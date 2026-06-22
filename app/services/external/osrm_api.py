import httpx


class OSRMClient:
    """Stub OSRM (Open Source Routing Machine).
    V2: calcul réel isochrones 15 min / 30 min via serveur OSRM public ou self-host.
    V1 : pas de live; estimation via densité + référentiel rush_hour."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def fetch_isochrone(self, lat: float, lon: float, minutes: int) -> dict | None:
        return None


osrm_api = OSRMClient()
