from app.api.schemas.common import GeoScope
from app.core.constants import DEFAULT_RADIUS_MINUTES
from app.core.enums import GeoLevel


class GeoNormalizer:
    """Sprint 0 normalizer: deterministic placeholder to be replaced by real FR/ES adapters."""

    def normalize(
        self,
        city: str,
        country: str,
        region: str | None = None,
        postal_codes: list[str] | None = None,
    ) -> GeoScope:
        country_map = {
            "FR": "France",
            "ES": "Spain",
        }
        return GeoScope(
            city=city.strip(),
            country=country_map.get(country.upper(), country.upper()),
            region=region,
            province=region,
            municipality_code=None,
            postal_codes=postal_codes or [],
            geo_level_primary=GeoLevel.MUNICIPALITY,
            comparison_scopes=[GeoLevel.PROVINCE, GeoLevel.COUNTRY],
            radius_minutes=DEFAULT_RADIUS_MINUTES,
        )


geo_normalizer = GeoNormalizer()
