from app.api.schemas.common import Study
from app.core.enums import ConfidenceGrade, FreshnessLevel, GeoLevel, SourceType
from app.core.score_config import DEFAULT_METRIC_BASELINES
from app.services.collectors.base import BaseCollector


class BusinessCaseCollector(BaseCollector):
    theme_id = "business_case"
    supported_countries = {"FR", "ES"}

    def collect(self, study: Study):
        country = study.country
        if country not in self.supported_countries:
            return [], []

        src = self._new_source(
            country=country,
            title="Stella - Référentiel business case interne",
            url="https://internal.stella/business-case",
            publisher="Stella",
            source_type=SourceType.CORPORATE,
            authority_level=2,
            freshness=FreshnessLevel.QUARTERLY,
            coverage=GeoLevel.COUNTRY,
            confidence=ConfidenceGrade.C,
        )
        business_model = (study.business_context.business_model or "").lower()
        include_franchise_buyin = business_model == "franchise"

        sources = [src]
        sids = [src.source_id]

        metrics = [
            self._new_metric("estimated_initial_investment", "Investissement initial",
                DEFAULT_METRIC_BASELINES["estimated_initial_investment"], "EUR", "latest",
                GeoLevel.MUNICIPALITY, sids, ConfidenceGrade.C, fallback=True),
            self._new_metric("estimated_monthly_fixed_costs", "Charges fixes mensuelles",
                DEFAULT_METRIC_BASELINES["estimated_monthly_fixed_costs"], "EUR/mois", "latest",
                GeoLevel.MUNICIPALITY, sids, ConfidenceGrade.C, fallback=True),
            self._new_metric("recurring_revenue_share_potential", "Part CA récurrent",
                DEFAULT_METRIC_BASELINES["recurring_revenue_share_potential"], "%", "latest",
                GeoLevel.MUNICIPALITY, sids, ConfidenceGrade.D, fallback=True),
            self._new_metric("premium_customer_potential", "Potentiel premium",
                DEFAULT_METRIC_BASELINES["premium_customer_potential"], "indice", "latest",
                GeoLevel.MUNICIPALITY, sids, ConfidenceGrade.D, fallback=True),
        ]

        if include_franchise_buyin:
            src_franchise = self._new_source(
                country=country,
                title="Observatoire de la Franchise / O2",
                url="https://www.observatoiredelafranchise.fr/",
                publisher="Observatoire Franchise",
                source_type=SourceType.CORPORATE,
                authority_level=2,
                freshness=FreshnessLevel.ANNUAL,
                coverage=GeoLevel.COUNTRY,
                confidence=ConfidenceGrade.C,
            )
            metrics.append(
                self._new_metric("franchise_entry_fee", "Droit d'entrée franchise",
                    DEFAULT_METRIC_BASELINES["franchise_entry_fee"], "EUR", "latest",
                    GeoLevel.COUNTRY, [src_franchise.source_id], ConfidenceGrade.C, fallback=True)
            )
            sources.append(src_franchise)

        return metrics, sources
