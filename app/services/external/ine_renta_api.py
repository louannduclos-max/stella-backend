import httpx


class INERentaClient:
    """Stub INE Atlas de Distribución de la Renta de los Hogares.
    Renta media municipal disponible via INE API JSON.
    V1 : pas de live; référentiel local utilisé."""

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    def fetch_municipio_renta(self, municipio_code: str | None) -> dict | None:
        if not municipio_code:
            return None
        return None


ine_renta_api = INERentaClient()
