import httpx

BASE_REPORT = "https://www.idealista.com/sala-de-prensa/informes-precio-vivienda/"


class IdealistaApiClient:
    """Stub Idealista. API privée (OAuth, accès payant) — non branchée en V1.
    Utilisé comme placeholder; valeurs réelles via accès partenaire à brancher en V2."""

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    def fetch_price_m2(self, city: str, province: str | None = None) -> dict | None:
        return None


idealista_api = IdealistaApiClient()
