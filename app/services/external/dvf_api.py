import httpx

BASE_URL = "https://api.cquest.org/dvf"


class DVFApiClient:
    """Client agrégateur DVF public (api.cquest.org/dvf) - prix m² par commune INSEE."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def fetch_commune_stats(self, code_insee: str) -> dict | None:
        params = {"code_commune": code_insee}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.get(BASE_URL, params=params)
                r.raise_for_status()
                payload = r.json()
        except Exception:
            return None
        return self._summarize(payload)

    def _summarize(self, payload: dict) -> dict | None:
        if not payload or "resultats" not in payload:
            return None
        rows = payload.get("resultats") or []
        houses, apartments, all_prices = [], [], []
        for row in rows:
            try:
                surface = float(row.get("surface_reelle_bati") or 0)
                value = float(row.get("valeur_fonciere") or 0)
                if surface <= 0 or value <= 0:
                    continue
                price_m2 = value / surface
                if not (200 < price_m2 < 30000):
                    continue
                local_type = (row.get("type_local") or "").lower()
                if "maison" in local_type:
                    houses.append(price_m2)
                elif "appartement" in local_type:
                    apartments.append(price_m2)
                all_prices.append(price_m2)
            except Exception:
                continue
        if not all_prices:
            return None
        return {
            "median_price_m2": self._median(all_prices),
            "house_price_m2": self._median(houses) if houses else None,
            "apartment_price_m2": self._median(apartments) if apartments else None,
            "transactions_count": len(all_prices),
        }

    def _median(self, values: list[float]) -> float:
        s = sorted(values)
        n = len(s)
        if n == 0:
            return 0.0
        m = n // 2
        if n % 2:
            return round(s[m], 1)
        return round((s[m - 1] + s[m]) / 2, 1)


dvf_api = DVFApiClient()
