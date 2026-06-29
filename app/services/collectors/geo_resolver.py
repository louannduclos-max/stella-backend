"""
Résout la zone géographique réelle d'une commune :
- Commune → EPCI (intercommunalité)
- Commune → département
- Population EPCI via geo.api.gouv.fr
"""
import logging
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)

GEO_API = "https://geo.api.gouv.fr"


def resolve_geo_zone(city: str, postal_code: str | None = None) -> Dict[str, Any]:
    """
    Retourne les infos de zone élargie pour une commune.
    Retourne un dict vide si la commune n'est pas trouvée ou si l'API est indisponible.
    """
    try:
        params: Dict[str, Any] = {
            "nom": city,
            "fields": "nom,code,codesPostaux,population,epci,departement",
            "limit": 1,
        }
        if postal_code:
            params["codePostal"] = postal_code

        r = httpx.get(f"{GEO_API}/communes", params=params, timeout=10)
        r.raise_for_status()
        communes = r.json()
        if not communes:
            logger.warning("[geo_resolver] Commune non trouvée : %s %s", city, postal_code)
            return {}

        commune = communes[0]
        result: Dict[str, Any] = {
            "commune_nom": commune.get("nom"),
            "commune_code": commune.get("code"),
            "commune_population": commune.get("population"),
            "departement_code": commune.get("departement", {}).get("code"),
            "departement_nom": commune.get("departement", {}).get("nom"),
        }

        # Résoudre l'EPCI (intercommunalité)
        epci = commune.get("epci")
        if epci:
            result["epci_code"] = epci.get("code")
            result["epci_nom"] = epci.get("nom")

            r2 = httpx.get(
                f"{GEO_API}/epcis/{epci['code']}/communes",
                params={"fields": "population"},
                timeout=10,
            )
            if r2.status_code == 200:
                members = r2.json()
                result["epci_population"] = sum(
                    m.get("population", 0) for m in members if m.get("population")
                )
                result["epci_nb_communes"] = len(members)
            else:
                logger.warning(
                    "[geo_resolver] EPCI %s : membres non récupérés (%d)",
                    epci["code"],
                    r2.status_code,
                )

        logger.info(
            "[geo_resolver] %s → code=%s, epci=%s (pop. %s)",
            city,
            result.get("commune_code"),
            result.get("epci_nom"),
            result.get("epci_population"),
        )
        return result

    except httpx.TimeoutException:
        logger.warning("[geo_resolver] Timeout API pour '%s'", city)
        return {}
    except Exception as exc:
        logger.error("[geo_resolver] Erreur pour '%s' : %s", city, exc)
        return {}
