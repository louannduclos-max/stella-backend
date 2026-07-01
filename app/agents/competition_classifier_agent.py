"""
Competition Classifier Agent — Sprint 12.

PRINCIPE MIX CODE/AGENT :
  Le CODE collecte des FAITS (Places : nom, adresse, note, types).
  L'AGENT ajoute de la COMPRÉHENSION (domaine, direct/indirect) UNIQUEMENT
  sur les acteurs que le code a collectés.

  L'agent NE PEUT PAS :
    - Ajouter un concurrent
    - Modifier une note ou un nombre d'avis
    - Inventer un domaine (incertain → "n.d.")

  L'agent PEUT :
    - Déduire is_direct depuis le nom + types Google
    - Déduire le domaine d'expertise (court, max 40 chars)

Entrée  : liste de dicts {"name": str, "types": str|None} — noms sanitisés
Sortie  : dict {name: {"is_direct": bool, "domain": str}}
Fallback: {} si l'appel Gemini échoue → le code garde la classification par défaut
"""
from __future__ import annotations

import json
import logging
import os

import httpx

logger = logging.getLogger(__name__)

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)
_GEMINI_TIMEOUT_S = 45

_SYSTEM = """
Tu es un analyste du marché des services à la personne (aide à domicile).
Tu reçois une liste d'entreprises RÉELLES collectées via Google Places
(nom + types Google). Pour CHAQUE entreprise de la liste, tu détermines :

1. is_direct (booléen) :
   - true si l'entreprise fait de l'AIDE À DOMICILE POUR SENIORS / personnes
     dépendantes (même métier que la marque analysée).
   - false si métier proche mais différent (ménage seul, garde d'enfants,
     jardinage, soins infirmiers médicaux purs, résidence senior...).

2. domain (texte court, max 40 caractères) : le domaine d'expertise déduit
   du nom et des types Google.
   Exemples : "Aide à domicile senior", "Ménage / repassage",
              "Garde d'enfants", "Soins infirmiers", "Services mixtes SAP".
   Si tu ne peux PAS déduire avec confiance → "n.d.". Ne devine jamais.

RÈGLES ABSOLUES :
- Tu ne classes QUE les entreprises fournies. Tu n'en ajoutes AUCUNE.
- Tu ne modifies aucune donnée factuelle (note, avis, nom).
- Tu ne inventes pas de domaine. Incertain = "n.d.".
- Tu retournes UNIQUEMENT du JSON valide, une entrée par entreprise fournie,
  identifiée par son name exact (tel que fourni dans la liste).

Format de sortie STRICT (rien d'autre) :
{"classifications": [
  {"name": "<name exact fourni>", "is_direct": true, "domain": "Aide à domicile senior"},
  {"name": "<name exact fourni>", "is_direct": false, "domain": "Ménage / repassage"}
]}
"""


class CompetitionClassifierAgent:

    def classify(
        self,
        competitors: list[dict],
        brand_context: str = "aide à domicile senior",
    ) -> dict[str, dict]:
        """
        Classifie une liste de concurrents bruts (faits Places).

        Args:
            competitors : liste de dicts {"name": str, "types": str|None}
                          Les noms doivent être sanitisés avant l'appel.
            brand_context : description courte de la marque analysée.

        Returns:
            dict {name: {"is_direct": bool, "domain": str}}
            Retourne {} si l'appel Gemini échoue → le code garde les valeurs par défaut.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("[ClassifierAgent] GEMINI_API_KEY absente — pas de classification")
            return {}
        if not competitors:
            return {}

        # On envoie UNIQUEMENT nom + types (factuel, pas d'adresse ni de note)
        payload_list = [
            {
                "name": c.get("name", ""),
                "types": c.get("types") or c.get("category") or "",
            }
            for c in competitors
            if c.get("name")
        ]

        prompt = (
            f"Marque analysée : {brand_context}\n\n"
            "Entreprises réelles à classer (ne pas en ajouter, ne pas en retirer) :\n"
            f"{json.dumps(payload_list, ensure_ascii=False, indent=2)}\n\n"
            "Classe chaque entreprise (is_direct + domain)."
        )

        url = f"{_GEMINI_URL}?key={api_key}"
        body = {
            "system_instruction": {"parts": [{"text": _SYSTEM}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                # Sprint 14c — 2048 était trop court pour 30 acteurs ET les
                # tokens de thinking de gemini-2.5 se décomptaient du budget
                # → JSON tronqué → json.loads KO → fallback {} silencieux
                # → TOUS les domaines en "n.d." (constaté sur l'étude Lyon).
                "maxOutputTokens": 6144,
            },
        }
        if "2.5" in (GEMINI_MODEL or ""):
            body["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}

        try:
            resp = httpx.post(url, json=body, timeout=_GEMINI_TIMEOUT_S)
            logger.warning(
                "[ClassifierAgent] HTTP %s model=%s n=%d",
                resp.status_code, GEMINI_MODEL, len(payload_list),
            )
            resp.raise_for_status()

            raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            # Retirer les éventuelles fences markdown
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            if raw.endswith("```"):
                raw = raw[:-3]

            # Parse défensif : si le JSON est coupé, récupérer jusqu'au dernier
            # objet complet plutôt que tout perdre.
            raw = raw.strip()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                last = raw.rfind("}")
                candidate = raw[: last + 1]
                # refermer la structure {"classifications": [ ... ]}
                if not candidate.rstrip().endswith("]}"):
                    candidate = candidate + "]}"
                data = json.loads(candidate)
            result = {}
            for cls in data.get("classifications", []):
                name = cls.get("name", "")
                if name:
                    result[name] = {
                        "is_direct": bool(cls.get("is_direct", False)),
                        "domain": cls.get("domain") or "n.d.",
                    }
            logger.warning(
                "[ClassifierAgent] %d classifiés sur %d fournis",
                len(result), len(payload_list),
            )
            return result

        except Exception as exc:
            logger.warning(
                "[ClassifierAgent] échec → classification par défaut : %s", exc
            )
            return {}


competition_classifier_agent = CompetitionClassifierAgent()
