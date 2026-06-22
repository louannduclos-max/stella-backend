import httpx

BASE_URL = "https://geo.api.gouv.fr"


class GeoApiGouvClient:
    """Client API Découpage administratif (geo.api.gouv.fr) - officiel data.gouv.fr."""

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    def resolve_commune(self, city: str, postal_code: str | None = None) -> dict | None:
        params = {
            "nom": city,
            "fields": "code,nom,codesPostaux,population,surface,codeDepartement,codeRegion,centre",
            "boost": "population",
            "limit": 5,
        }
        if postal_code:
            params["codePostal"] = postal_code
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.get(f"{BASE_URL}/communes", params=params)
                r.raise_for_status()
                data = r.json()
        except Exception:
            return None
        if not data:
            return None
        return data[0]


geo_api_gouv = GeoApiGouvClient()
