"""
Slide Builder Agent
Reçoit : données du manifest + section_id
Fait : choisit le bon template, remplit les slots via LLM (Vertex Gemini)
Retourne : objets positionnés prêts pour le renderer PPTX/HTML

Règle absolue : ne crée pas de positions, ne sort pas du template.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "slides"
VERTEX_REGION = "europe-west1"
VERTEX_PROJECT = os.environ.get("GCP_PROJECT_ID", "ouicare-stella-prod")
VERTEX_MODEL = "gemini-2.0-flash"

# Mapping section → template
SECTION_TEMPLATE_MAP = {
    "cover":                    "cover",
    "executive_summary":        "kpi_analysis",
    "market_scorecard":         "kpi_analysis",
    "demographics":             "kpi_analysis",
    "target_segments":          "kpi_analysis",
    "employment_talent":        "kpi_analysis",
    "income_housing":           "kpi_analysis",
    "real_estate":              "kpi_analysis",
    "microzones":               "kpi_analysis",
    "competition_mapping":      "competition",
    "regulation_feasibility":   "kpi_analysis",
    "swot":                     "swot",
    "verdict":                  "verdict",
    "action_plan":              "kpi_analysis",
    "methodology_sources":      "kpi_analysis",
}

SLOT_FILLER_PROMPT = """
Tu es un rédacteur d'études de faisabilité franchise. Tu reçois :
1. Les données d'une étude locale (manifest)
2. Un template de slide avec des slots nommés et leurs contraintes
3. Le type de section à rendre

Règles absolues :
- Tu remplis UNIQUEMENT les slots définis dans le template.
- Tu utilises UNIQUEMENT des données présentes dans le manifest fourni.
- Si une donnée est absente : tu laisses le slot vide ou tu indiques
  "Donnée non disponible" — tu n'inventes jamais.
- Tu respectes les limites max_chars de chaque slot.
- Pour les slots "narrative" et "bullets" : tu argumentes avec des chiffres
  du manifest. Chaque phrase cite une donnée. Pas de généralités.
- Pour les slots SWOT : chaque bullet = 1 fait chiffré + son implication
  business (max 15 mots par bullet).
- Tu retournes UNIQUEMENT du JSON valide, sans markdown ni explication.

Format de sortie :
{
  "template_id": "<id du template>",
  "slots_filled": {
    "nom_du_slot": "valeur remplie",
    "kpi_1": {"label": "...", "value": "...", "unit": "...", "fallback": false},
    "q1_forces": {"score": "74/100", "bullets": ["bullet 1", "bullet 2", "bullet 3"]}
  },
  "slots_empty": ["liste des slots non remplis faute de données"]
}
"""


class SlideBuilderAgent:

    def __init__(self):
        self._templates: Dict[str, Dict] = {}
        self._load_templates()

    def _load_templates(self):
        if not TEMPLATES_DIR.exists():
            logger.warning("[SlideBuilderAgent] Dossier templates introuvable : %s", TEMPLATES_DIR)
            return
        for f in TEMPLATES_DIR.glob("template_*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                self._templates[data["template_id"]] = data
            except Exception as e:
                logger.error("[SlideBuilderAgent] Erreur chargement template %s : %s", f, e)
        logger.info("[SlideBuilderAgent] %d templates chargés", len(self._templates))

    def _get_template(self, section_id: str) -> Dict:
        template_id = SECTION_TEMPLATE_MAP.get(section_id, "kpi_analysis")
        tmpl = self._templates.get(template_id)
        if not tmpl:
            # Fallback absolu sur kpi_analysis
            tmpl = self._templates.get("kpi_analysis")
        if not tmpl:
            raise RuntimeError(f"Aucun template disponible pour section '{section_id}'")
        return tmpl

    def _call_vertex(self, prompt: str) -> str:
        """Appelle Vertex AI Gemini. Lève une exception si indisponible."""
        try:
            import google.auth
            import google.auth.transport.requests

            # Option A — credentials JSON inline via variable d'env Render
            # Permet d'éviter de monter un fichier de clé sur le filesystem.
            creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            if creds_json and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                import json as _json
                import tempfile
                tmp = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False
                )
                tmp.write(creds_json)
                tmp.close()
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name
                logger.debug("[SlideBuilderAgent] Credentials écrits depuis GOOGLE_APPLICATION_CREDENTIALS_JSON")

            creds, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            creds.refresh(google.auth.transport.requests.Request())
        except Exception as e:
            raise RuntimeError(f"google.auth non disponible : {e}") from e

        endpoint = (
            f"https://{VERTEX_REGION}-aiplatform.googleapis.com/v1/"
            f"projects/{VERTEX_PROJECT}/locations/{VERTEX_REGION}/"
            f"publishers/google/models/{VERTEX_MODEL}:generateContent"
        )
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": SLOT_FILLER_PROMPT}]},
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 3000,
                "responseMimeType": "application/json",
            },
        }
        r = httpx.post(
            endpoint,
            json=payload,
            headers={"Authorization": f"Bearer {creds.token}"},
            timeout=45,
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]

    def build_slide(
        self,
        section_id: str,
        manifest_data: Dict[str, Any],
        tenant_id: str,
        language: str = "fr",
    ) -> Dict[str, Any]:
        """
        Point d'entrée principal.
        Retourne un dict compatible avec le renderer existant (objects + metadata).
        """
        template = self._get_template(section_id)

        prompt = f"""
Section : {section_id}
Langue : {language}
Tenant : {tenant_id}

Template à utiliser :
{json.dumps(template, ensure_ascii=False, indent=2)}

Données du manifest (source de vérité) :
{json.dumps(manifest_data, ensure_ascii=False, indent=2)}

Remplis les slots du template avec les données du manifest.
"""
        raw = self._call_vertex(prompt)
        # Nettoyer les balises markdown éventuelles
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[-1] if raw.count("```") >= 2 else raw
            raw = raw.lstrip("json").strip().rstrip("```").strip()
        filled = json.loads(raw)

        objects = self._slots_to_objects(template, filled.get("slots_filled", {}))

        return {
            "section_id": section_id,
            "template_id": template["template_id"],
            "layout": template["template_id"],
            "background": "dark" if section_id in {"cover", "verdict"} else "light",
            "canvas": template["canvas"],
            "safe_margin": template["safe_margin"],
            "objects": objects,
            "slots_empty": filled.get("slots_empty", []),
            "agent_generated": True,
        }

    def _slots_to_objects(
        self,
        template: Dict,
        slots_filled: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Convertit les slots remplis en objets positionnés absolus.
        Les positions viennent UNIQUEMENT du template (jamais de l'agent).
        """
        objects = []
        for slot_id, slot_def in template["slots"].items():
            value = slots_filled.get(slot_id)
            pos = slot_def["position"]
            style = slot_def.get("style", {})
            slot_type = slot_def["type"]

            base: Dict[str, Any] = {
                "id": f"{template['template_id']}-{slot_id}",
                "data_object": True,
                "data_object_type": "textbox",
                "left": pos["left"],
                "top": pos["top"],
                "width": pos["width"],
                "height": pos["height"],
                "style": style,
            }

            if slot_type == "shape" or not value:
                base["data_object_type"] = "shape"
                base["text"] = ""
                objects.append(base)
                continue

            if slot_type == "text":
                base["text"] = str(value)[: slot_def.get("max_chars", 500)]

            elif slot_type == "kpi_card" and isinstance(value, dict):
                base["data_object_type"] = "shape"
                base["children"] = [
                    {
                        "role": "label",
                        "text": str(value.get("label", "")),
                        "style": {
                            "font_size": 14,
                            "font_weight": 500,
                            "color": "var(--stella-text-muted)",
                            "text_transform": "uppercase",
                        },
                    },
                    {
                        "role": "value",
                        "text": str(value.get("value", "")),
                        "style": {
                            "font_size": 48,
                            "font_weight": 800,
                            "color": "var(--stella-primary)",
                        },
                    },
                ]
                if value.get("fallback"):
                    base["children"].append(
                        {
                            "role": "badge",
                            "text": "estimation",
                            "style": {"font_size": 11, "color": "var(--stella-warn)"},
                        }
                    )

            elif slot_type == "swot_quadrant" and isinstance(value, dict):
                base["data_object_type"] = "shape"
                bullets = value.get("bullets", [])
                base["children"] = [
                    {
                        "role": "label",
                        "text": slot_def.get("label", slot_id),
                        "style": {"font_size": 16, "font_weight": 700},
                    },
                    {
                        "role": "score",
                        "text": str(value.get("score", "")),
                        "style": {
                            "font_size": 28,
                            "font_weight": 800,
                            "color": "var(--stella-primary)",
                        },
                    },
                ] + [
                    {
                        "role": "bullet",
                        "text": f"• {b}",
                        "style": {"font_size": 14, "line_height": 1.5},
                    }
                    for b in bullets[:4]
                ]

            elif slot_type == "competitor_card" and isinstance(value, dict):
                base["data_object_type"] = "shape"
                items = value.get("items", [])
                base["children"] = [
                    {
                        "role": "title",
                        "text": str(value.get("title", "")),
                        "style": {"font_size": 16, "font_weight": 700},
                    },
                    {
                        "role": "count",
                        "text": str(value.get("count", "")),
                        "style": {"font_size": 40, "font_weight": 800},
                    },
                ] + [
                    {
                        "role": "item",
                        "text": f"• {item}",
                        "style": {"font_size": 14},
                    }
                    for item in items[: slot_def.get("max_items", 4)]
                ]

            elif slot_type == "highlight_box":
                base["data_object_type"] = "shape"
                base["children"] = [
                    {
                        "role": "text",
                        "text": str(value)[: slot_def.get("max_chars", 300)],
                        "style": style,
                    }
                ]

            elif slot_type == "bullet_list" and isinstance(value, list):
                base["data_object_type"] = "shape"
                base["children"] = [
                    {
                        "role": "bullet",
                        "text": f"✓ {item}",
                        "style": {"font_size": 15, "line_height": 1.6},
                    }
                    for item in value[: slot_def.get("max_items", 5)]
                ]

            elif slot_type == "score_bars" and isinstance(value, list):
                base["data_object_type"] = "shape"
                base["children"] = [
                    {
                        "role": "score_row",
                        "text": f"{item.get('label', '')} : {item.get('value', '')}",
                        "style": {"font_size": 15, "font_weight": 600},
                    }
                    for item in value
                ]

            elif slot_type == "score_bars_vertical" and isinstance(value, list):
                base["data_object_type"] = "shape"
                base["children"] = [
                    {
                        "role": "score_row",
                        "text": f"{item.get('label', '')} : {item.get('value', '')}",
                        "style": {"font_size": 15, "font_weight": 600},
                    }
                    for item in value
                ]

            elif slot_type in {"score_badge", "verdict_badge"}:
                base["data_object_type"] = "textbox"
                base["text"] = str(value)

            else:
                base["text"] = str(value) if value else ""

            objects.append(base)

        return objects


# Singleton — chargé une seule fois au démarrage de l'app
slide_builder_agent = SlideBuilderAgent()
