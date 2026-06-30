"""
QA Agent — vérifie le contenu produit par NarrativeAgent avant publication.
Volontairement déterministe (pas de LLM) : rapide, gratuit, prévisible.
Si un slot échoue la vérification, on revient au contenu déterministe
pour CE slot uniquement — jamais toute la slide.
"""
import logging
import re

logger = logging.getLogger(__name__)


def _extract_numbers(text: str) -> list[str]:
    """Extrait les nombres d'un texte (gère les formats FR : 1 234,5)."""
    return re.findall(r"\d[\d\s]*[.,]?\d*", text or "")


def _manifest_contains(manifest: dict, number_str: str) -> bool:
    """Vérifie qu'un nombre cité existe quelque part dans le manifest."""
    cleaned = number_str.replace(" ", "").replace(",", ".")
    manifest_str = str(manifest)
    return cleaned in manifest_str.replace(" ", "").replace(",", ".")


class QAAgent:

    def validate_and_merge(
        self,
        agent_objects: list[dict],
        deterministic_objects: list[dict],
        manifest: dict,
    ) -> list[dict]:
        """
        Compare objet par objet (même id). Garde le contenu agent
        UNIQUEMENT s'il passe toutes les vérifications. Sinon,
        revert vers le contenu déterministe pour cet objet précis.
        """
        det_by_id = {o["id"]: o for o in deterministic_objects}
        result = []

        for agent_obj in agent_objects:
            obj_id = agent_obj.get("id")
            det_obj = det_by_id.get(obj_id)

            if not agent_obj.get("fill_with_narrative"):
                # Objet non concerné par l'agent (positions/KPIs déterministes)
                result.append(agent_obj)
                continue

            text = agent_obj.get("text", "") or ""
            max_chars = agent_obj.get("max_chars", 500)

            # Check 1 : non vide
            if not text.strip():
                logger.info("[QA] %s : texte vide → revert déterministe", obj_id)
                result.append(det_obj or agent_obj)
                continue

            # Check 2 : respecte la limite de caractères (tolérance légère)
            if len(text) > max_chars + 20:
                logger.info("[QA] %s : dépasse max_chars (%d > %d) → revert", obj_id, len(text), max_chars)
                result.append(det_obj or agent_obj)
                continue

            # Check 3 : chaque nombre cité (≥ 2 chiffres) existe dans le manifest
            numbers = _extract_numbers(text)
            unverifiable = [
                n for n in numbers
                if len(n.strip()) >= 2 and not _manifest_contains(manifest, n)
            ]
            if unverifiable:
                logger.info("[QA] %s : chiffres non tracés %s → revert", obj_id, unverifiable)
                result.append(det_obj or agent_obj)
                continue

            # Toutes les vérifications passent
            agent_obj["source"] = "agent"
            result.append(agent_obj)

        return result


qa_agent = QAAgent()
