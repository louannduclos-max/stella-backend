"""
Narrative Agent — remplit uniquement les slots texte d'un slide déjà positionné.
Le layout (positions pixel) vient du layout_engine, jamais du LLM.

Principe de séparation :
- layout_engine_5_0 / slide_builder_agent → positions des objets
- NarrativeAgent → contenu texte des objets qui ont fill_with_narrative=True

Utilise GEMINI_API_KEY (Google AI Studio, gratuit) — même clé que gemini_analyst.
Fallback silencieux si la clé est absente ou si l'API échoue.
"""
import json
import logging
import os
import re

import httpx

logger = logging.getLogger(__name__)

# Modèle configurable via env var GEMINI_MODEL — partagé avec gemini_analyst
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

NARRATIVE_SYSTEM_PROMPT = """
Tu es un rédacteur d'études de faisabilité franchise. Tu reçois :
1. Une liste de slots texte à remplir (nom du slot + contrainte max_chars + rôle)
2. Les données du manifest (source de vérité, données réelles)
3. La langue cible

Règles absolues :
- Utilise UNIQUEMENT des données présentes dans le manifest.
- Chaque phrase narrative cite au moins un chiffre du manifest.
- Bullets SWOT : 1 fait chiffré + son implication business, max 15 mots par bullet.
- Si une donnée manque : laisser le slot vide (""), ne jamais inventer.
- Retourner UNIQUEMENT du JSON valide, sans markdown, sans bloc ```json```.

Format de sortie strict :
{ "slot_id_1": "texte rempli", "slot_id_2": "texte rempli", ... }
"""


def _safe_parse_json(raw: str) -> dict | None:
    """
    Parse JSON de façon défensive :
    1. Retire les fences markdown (```json ... ```)
    2. Tente json.loads normal
    3. Si échec, tente jusqu'au dernier } valide (réponse tronquée)
    4. Retourne None si tout échoue — jamais de crash
    """
    txt = raw.strip()
    txt = re.sub(r"^```json\s*", "", txt)
    txt = re.sub(r"^```\s*", "", txt)
    txt = re.sub(r"\s*```$", "", txt)
    txt = txt.strip()
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        last = txt.rfind("}")
        if last > 0:
            try:
                return json.loads(txt[: last + 1])
            except json.JSONDecodeError:
                pass
    return None


class NarrativeAgent:

    def fill_text_slots(
        self,
        slide_objects: list[dict],
        manifest: dict,
        language: str = "fr",
    ) -> list[dict]:
        """
        Remplit les slots texte d'une liste d'objets déjà positionnés.
        Ne touche jamais aux positions (left/top/width/height).

        Un objet est éligible si :
        - data_object_type == "textbox"
        - fill_with_narrative == True

        Si GEMINI_API_KEY est absente ou si l'API échoue : retourne les objets
        sans modification (les textes statiques du layout_engine restent inchangés).
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.debug("[NarrativeAgent] GEMINI_API_KEY absente — fallback template")
            return slide_objects

        # Identifier les slots texte narratifs à remplir
        text_slots = [
            {
                "slot_id": obj["id"],
                "max_chars": obj.get("max_chars", 300),
                "role": obj.get("narrative_role", "analysis"),
            }
            for obj in slide_objects
            if obj.get("data_object_type") == "textbox"
            and obj.get("fill_with_narrative") is True
        ]

        if not text_slots:
            return slide_objects

        # Tronquer le manifest pour éviter un prompt trop long (6000 chars)
        manifest_excerpt = json.dumps(manifest, ensure_ascii=False)[:6000]

        user_prompt = (
            f"Langue : {language}\n"
            f"Slots à remplir : {json.dumps(text_slots, ensure_ascii=False)}\n"
            f"Manifest : {manifest_excerpt}"
        )

        try:
            r = httpx.post(
                f"{_GEMINI_URL}?key={api_key}",
                json={
                    "system_instruction": {
                        "parts": [{"text": NARRATIVE_SYSTEM_PROMPT}]
                    },
                    "contents": [{"parts": [{"text": user_prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 4096,
                    },
                },
                timeout=30,
            )
            logger.warning("[NarrativeAgent] HTTP %s model=%s", r.status_code, GEMINI_MODEL)
            r.raise_for_status()

            raw = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            logger.warning("[NarrativeAgent] BODY (300 premiers car.) : %s", raw[:300])

            filled = _safe_parse_json(raw)
            if filled is None:
                logger.warning("[NarrativeAgent] _safe_parse_json échoué — réponse brute : %s", raw[:200])
                return slide_objects

            # Injecter dans les objets sans toucher aux positions
            for obj in slide_objects:
                if obj.get("id") in filled:
                    obj["text"] = str(filled[obj["id"]])[: obj.get("max_chars", 500)]

            logger.info(
                "[NarrativeAgent] %d slots remplis sur %d attendus",
                len([k for k in filled if filled[k]]),
                len(text_slots),
            )

        except Exception as exc:
            logger.warning("[NarrativeAgent] Fallback texte statique : %s", exc)
            # Ne rien modifier — les textes générés par layout_engine restent

        return slide_objects


narrative_agent = NarrativeAgent()
