import httpx


class DGEClient:
    """Stub DGE (Direction Générale des Entreprises) / CRT régionaux.
    Données publiques : nuitées hôtelières, fréquentation, taxe séjour via data.gouv.fr.
    V1 : pas de live; référentiel régional utilisé."""

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    def fetch_tourism_region(self, region: str | None) -> dict | None:
        if not region:
            return None
        return None


dge_api = DGEClient()
