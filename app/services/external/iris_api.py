import httpx


class IRISClient:
    """Stub INSEE IRIS - sous-zones communales FR.
    V2: API geo.api.gouv.fr + open data INSEE pour shapes & population par IRIS.
    V1: génération déterministe via population & densité."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def fetch_iris_for_commune(self, code_insee: str | None):
        if not code_insee:
            return None
        return None


class SeccionesCensalesClient:
    """Stub INE secciones censales - sous-zones municipales ES.
    V2: INE API JSON + Atlas Renta par sección.
    V1: génération déterministe."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def fetch_secciones_for_municipio(self, municipio_code: str | None):
        if not municipio_code:
            return None
        return None


iris_api = IRISClient()
secciones_api = SeccionesCensalesClient()
