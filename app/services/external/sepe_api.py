import httpx

OPENDATA_BASE = "https://datos.gob.es/apidata/catalog/dataset"


class SEPEClient:
    """Stub SEPE (Servicio Público de Empleo Estatal).
    Données disponibles via datos.gob.es / fichiers mensuels.
    V1 : pas de live; baseline appliquée; sources cataloguées."""

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    def fetch_local_paro(self, municipio_code: str | None) -> dict | None:
        if not municipio_code:
            return None
        return None


sepe_api = SEPEClient()
