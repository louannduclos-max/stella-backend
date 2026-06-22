import httpx


class IMSERSOClient:
    """Stub IMSERSO - Estadísticas SAAD / Ley de Dependencia.
    Données disponibles via datos.gob.es et publications mensuelles IMSERSO.
    V1 : pas de live; référentiel local utilisé."""

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    def fetch_saad_region(self, region: str | None) -> dict | None:
        if not region:
            return None
        return None


imserso_api = IMSERSOClient()
