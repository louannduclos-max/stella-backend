import httpx

BASE_URL = "https://servicios.ine.es/wstempus/jsstat/ES"


class INEApiClient:
    """Client API JSON INE (Espagne). Doc: https://www.ine.es/dyngs/DAB/index.htm?cid=1099"""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def fetch_population(self, municipio_code: str | None) -> dict | None:
        if not municipio_code:
            return None
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.get(f"{BASE_URL}/DATOS_TABLA/2852", params={"nult": 1})
                r.raise_for_status()
                return {"raw": r.json(), "municipio_code": municipio_code}
        except Exception:
            return None


ine_api = INEApiClient()
