import httpx

BASE_URL = "https://servicios.ine.es/wstempus/js/ES"


class INEGeoClient:
    """Résolution municipios ES via API JSON INE."""

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    def resolve_municipio(self, city: str, province: str | None = None) -> dict | None:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.get(f"{BASE_URL}/MUNICIPIOS")
                r.raise_for_status()
                data = r.json()
        except Exception:
            return None
        if not isinstance(data, list):
            return None
        needle = city.strip().lower()
        for item in data:
            name = (item.get("Nombre") or "").lower()
            if name == needle:
                return item
        for item in data:
            name = (item.get("Nombre") or "").lower()
            if needle in name:
                return item
        return None


ine_geo = INEGeoClient()
