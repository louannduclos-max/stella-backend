import httpx


class FilosofiClient:
    """Stub INSEE Filosofi - revenus disponibles localisés (open data).
    Jeu de données annuel data.insee.fr / data.gouv.fr (revenu médian par commune).
    V1 : pas de live; référentiel local utilisé."""

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    def fetch_commune_income(self, code_insee: str | None) -> dict | None:
        if not code_insee:
            return None
        return None


filosofi_api = FilosofiClient()
