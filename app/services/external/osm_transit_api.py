import httpx


class OSMTransitClient:
    """Stub OpenStreetMap Overpass - lignes TC par périmètre.
    V2: requête Overpass type=route route=bus|tram|subway|train autour des coords.
    V1: estimation déterministe via densité + référentiel."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def fetch_transit_lines(self, lat, lon, radius_m: int):
        if lat is None or lon is None:
            return None
        return None


osm_transit = OSMTransitClient()
