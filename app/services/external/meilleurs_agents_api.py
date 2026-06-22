import httpx


class MeilleursAgentsClient:
    """Stub MeilleursAgents. API privée payante - non branchée en V1.
    Lecture publique (HTML) possible mais fragile et non recommandée pour V1.
    À remplacer V2 par un partenariat data ou un fournisseur DVF-enrichi."""

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    def fetch_rental_price_m2(self, city: str, code_insee: str | None = None) -> dict | None:
        return None


meilleurs_agents = MeilleursAgentsClient()
