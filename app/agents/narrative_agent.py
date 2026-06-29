"""
Narrative Agent — remplit uniquement les slots texte d'un slide déjà positionné.
Le layout (positions pixel) vient du layout_engine, jamais du LLM.

Principe de séparation :
- layout_engine_5_0 / slide_builder_agent → positions des objets
- NarrativeAgent → contenu texte des objets qui ont fill_with_narrative=True

Chaque slot de type textbox avec fill_with_narrative=True est soumis au LLM.
Le LLM ne touche jamais aux coordonnées (left/top/width/height).
"""
import json
import logging
import os

import httpx

logger = logging.getLogger(__name__)

VERTEX_REGION = "europe-west1"
VERTEX_PROJECT = os.environ.get("GCP_PROJECT_ID", "ouicare-stella-prod")
VERTEX_MODEL = "gemini-2.0-flash"

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

        Si Vertex est indisponible : retourne les objets sans modification
        (les textes statiques générés par le layout_engine restent inchangés).
        """
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
            import google.auth
            import google.auth.transport.requests

            # Support credentials JSON inline (Option A Render)
            creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            if creds_json and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                import tempfile
                tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
                tmp.write(creds_json)
                tmp.close()
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name
                logger.debug("[NarrativeAgent] Credentials écrits depuis GOOGLE_APPLICATION_CREDENTIALS_JSON")

            creds, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            creds.refresh(google.auth.transport.requests.Request())

            endpoint = (
                f"https://{VERTEX_REGION}-aiplatform.googleapis.com/v1/"
                f"projects/{VERTEX_PROJECT}/locations/{VERTEX_REGION}/"
                f"publishers/google/models/{VERTEX_MODEL}:generateContent"
            )

            r = httpx.post(
                endpoint,
                json={
                    "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                    "systemInstruction": {
                        "parts": [{"text": NARRATIVE_SYSTEM_PROMPT}]
                    },
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 2000,
                    },
                },
                headers={"Authorization": f"Bearer {creds.token}"},
                timeout=30,
            )
            r.raise_for_status()

            raw = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            # Nettoyer éventuels blocs markdown
            raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            filled: dict = json.loads(raw)

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
