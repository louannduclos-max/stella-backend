import httpx


class CNSAClient:
    """Stub CNSA - Aide à l'autonomie des personnes âgées (open data).
    Données disponibles via data.gouv.fr (jeux de données annuels APA).
    V1 : pas de live; référentiel local utilisé."""

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    def fetch_apa_dept(self, dept_code: str | None) -> dict | None:
        if not dept_code:
            return None
        return None


cnsa_api = CNSAClient()
