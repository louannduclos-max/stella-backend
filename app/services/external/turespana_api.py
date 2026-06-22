import httpx


class TurespanaClient:
    """Stub Turespaña / INE EOH (Encuesta de Ocupación Hotelera).
    Données publiques : pernoctaciones, viajeros, ocupación mensuel par comunidad.
    V1 : pas de live; référentiel régional utilisé."""

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    def fetch_tourism_region(self, region: str | None) -> dict | None:
        if not region:
            return None
        return None


turespana_api = TurespanaClient()
