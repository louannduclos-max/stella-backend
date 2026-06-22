import httpx

STAT_BASE = "https://api.francetravail.io/partenaire/stats-offres-demandes-emploi/v1"


class FranceTravailClient:
    """Stub France Travail (ex-Pôle Emploi). API stats publique nécessite OAuth client_credentials.
    En V1 sans clé : on retourne None, le collecteur applique baseline + confidence dégradée.
    À brancher V2 avec credentials partenaires."""

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    def fetch_local_employment(self, code_insee: str | None) -> dict | None:
        if not code_insee:
            return None
        return None


france_travail = FranceTravailClient()
