import httpx


class PricingScraperClient:
    """Stub scraping pricing concurrents (O2, Shiva, Apef, Interdomicilio, Eulen, Clece...).
    Implémentation V2 via Playwright + cache 24h.
    V1 : pas de live; référentiel local utilisé."""

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    def fetch_local_pricing(self, country: str, code_insee: str | None) -> dict | None:
        return None


pricing_scraper = PricingScraperClient()
