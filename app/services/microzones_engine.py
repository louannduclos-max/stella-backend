from uuid import uuid4

from app.api.schemas.common import Study
from app.api.schemas.microzones import (
    MicroZonesSnapshot,
    Neighborhood,
    Street,
    TrafficAxis,
    TransitLine,
)
from app.core.enums import ConfidenceGrade
from app.core.income_registry import (
    ES_MEDIAN_INCOME_BY_REGION,
    ES_MEDIAN_INCOME_DEFAULT,
    FR_MEDIAN_INCOME_BY_DEPT,
    FR_MEDIAN_INCOME_DEFAULT,
)
from app.core.transit_registry import (
    HIGH_TRANSIT_CITIES_ES,
    HIGH_TRANSIT_CITIES_FR,
    TRANSIT_PROFILE_BY_DENSITY,
    coverage_label,
    coverage_label_es,
)


PREMIUM_PRICE_M2_THRESHOLD = 4000
PREMIUM_RENT_M2_THRESHOLD = 16


class MicroZonesEngine:
    def build_snapshot(self, study: Study) -> MicroZonesSnapshot:
        city = study.geo_scope.city
        country = study.country
        density_level = self._density_level(study)
        base_income = self._base_income(study)
        base_price_m2 = self._base_price_m2(study)
        base_rent_m2 = self._base_rent_m2(study)
        population = self._lookup_population(study)

        neighborhoods = self._build_neighborhoods(city, country, density_level, base_income, base_price_m2, base_rent_m2, population)
        streets = self._build_streets(neighborhoods)
        axes = self._build_traffic_axes(density_level)
        lines = self._build_transit_lines(city, country, density_level)

        return MicroZonesSnapshot(
            neighborhoods=neighborhoods,
            streets=streets,
            traffic_axes=axes,
            transit_lines=lines,
        )

    def _build_neighborhoods(self, city, country, density_level, base_income, base_price_m2, base_rent_m2, population):
        profile = self._neighborhood_profile(density_level)
        out: list[Neighborhood] = []
        for idx, (name, share, income_mult, price_mult, rent_mult) in enumerate(profile):
            pop = int(population * share)
            income = round(base_income * income_mult)
            price_m2 = round(base_price_m2 * price_mult)
            rent_m2 = round(base_rent_m2 * rent_mult, 1)
            n = Neighborhood(
                neighborhood_id=f"nbh_{uuid4().hex[:8]}",
                name=f"{name} ({city})",
                code=f"IRIS_{idx+1:03}" if country == "FR" else f"SEC_{idx+1:03}",
                population=pop,
                seniors_60_plus_share=self._seniors_share_for_zone(name),
                median_income=income,
                real_estate_price_m2=price_m2,
                rental_price_m2=rent_m2,
                confidence_grade=ConfidenceGrade.C,
                notes=f"Sous-zone {name} - estimée via baseline INSEE/INE + multiplicateurs.",
            )
            n.premium_flag = self._is_premium(n)
            n.premium_score = self._compute_premium_score(n, base_price_m2, base_rent_m2, base_income)
            out.append(n)
        return out

    def _neighborhood_profile(self, density_level: str):
        if density_level == "very_urban":
            return [
                ("Centre historique", 0.18, 1.10, 1.30, 1.25),
                ("Quartier d'affaires", 0.15, 1.20, 1.40, 1.35),
                ("Quartier résidentiel premium", 0.12, 1.35, 1.55, 1.40),
                ("Quartier mixte", 0.20, 1.00, 1.00, 1.00),
                ("Quartier populaire", 0.20, 0.75, 0.65, 0.80),
                ("Périphérie", 0.15, 0.85, 0.75, 0.85),
            ]
        if density_level == "urban":
            return [
                ("Centre-ville", 0.20, 1.10, 1.25, 1.20),
                ("Quartier résidentiel premium", 0.12, 1.30, 1.45, 1.30),
                ("Pavillonnaire familial", 0.20, 1.05, 1.05, 1.00),
                ("Zone mixte", 0.18, 1.00, 0.95, 0.95),
                ("Quartier populaire", 0.15, 0.80, 0.70, 0.80),
                ("Périphérie", 0.15, 0.90, 0.85, 0.85),
            ]
        if density_level == "periurban":
            return [
                ("Bourg centre", 0.25, 1.05, 1.15, 1.10),
                ("Lotissement récent", 0.20, 1.20, 1.20, 1.10),
                ("Pavillonnaire ancien", 0.20, 1.00, 1.00, 0.95),
                ("Zone artisanale", 0.10, 0.85, 0.75, 0.80),
                ("Hameaux résidentiels", 0.15, 1.10, 1.05, 0.95),
                ("Zone rurale proche", 0.10, 0.95, 0.85, 0.85),
            ]
        return [
            ("Bourg principal", 0.35, 1.05, 1.10, 1.05),
            ("Hameaux", 0.30, 0.95, 0.90, 0.90),
            ("Zone agricole", 0.20, 0.90, 0.80, 0.85),
            ("Résidences secondaires", 0.15, 1.15, 1.15, 1.05),
        ]

    def _seniors_share_for_zone(self, name: str) -> float:
        n = name.lower()
        if "résidentiel" in n or "premium" in n or "hameaux" in n or "secondaires" in n:
            return 34.0
        if "populaire" in n or "affaires" in n or "artisanale" in n:
            return 22.0
        if "lotissement" in n or "familial" in n:
            return 21.0
        return 28.0

    def _build_streets(self, neighborhoods):
        streets = []
        for n in neighborhoods[:5]:
            streets.append(Street(
                street_id=f"str_{uuid4().hex[:8]}",
                name=f"Axe principal {n.name}",
                neighborhood_id=n.neighborhood_id,
                street_type="avenue" if n.premium_flag else "rue",
                target_segment="seniors + premium" if n.premium_flag else "mix",
                priority="P0" if n.premium_flag else "P1",
                avg_real_estate_price_m2=n.real_estate_price_m2,
                notes=("Rue à forte densité cible premium." if n.premium_flag
                       else "Rue de circulation usuelle."),
            ))
        return streets

    def _build_traffic_axes(self, density_level: str):
        if density_level == "very_urban":
            return [
                TrafficAxis(axis_id=f"ax_{uuid4().hex[:8]}", name="Boulevard central", axis_type="structurant",
                            daily_traffic=60000, rush_hour_penalty_min=18, notes="Très chargé en heures de pointe."),
                TrafficAxis(axis_id=f"ax_{uuid4().hex[:8]}", name="Périphérique", axis_type="contournement",
                            daily_traffic=120000, rush_hour_penalty_min=22, notes="Saturation matin/soir."),
                TrafficAxis(axis_id=f"ax_{uuid4().hex[:8]}", name="Axe secondaire", axis_type="distribution",
                            daily_traffic=25000, rush_hour_penalty_min=10, notes="Bon report TC possible."),
            ]
        if density_level == "urban":
            return [
                TrafficAxis(axis_id=f"ax_{uuid4().hex[:8]}", name="Boulevard urbain", axis_type="structurant",
                            daily_traffic=30000, rush_hour_penalty_min=12, notes="Charge modérée."),
                TrafficAxis(axis_id=f"ax_{uuid4().hex[:8]}", name="Voie de contournement", axis_type="contournement",
                            daily_traffic=22000, rush_hour_penalty_min=8, notes="Permet de gagner du temps."),
            ]
        if density_level == "periurban":
            return [
                TrafficAxis(axis_id=f"ax_{uuid4().hex[:8]}", name="RN/RD principale", axis_type="structurant",
                            daily_traffic=18000, rush_hour_penalty_min=7, notes="Saturation aux entrées de ville."),
                TrafficAxis(axis_id=f"ax_{uuid4().hex[:8]}", name="Route secondaire", axis_type="distribution",
                            daily_traffic=8000, rush_hour_penalty_min=3, notes="Fluide hors pointe."),
            ]
        return [
            TrafficAxis(axis_id=f"ax_{uuid4().hex[:8]}", name="RD départementale", axis_type="structurant",
                        daily_traffic=6000, rush_hour_penalty_min=2, notes="Faible trafic."),
        ]

    def _build_transit_lines(self, city: str, country: str, density_level: str):
        profile = TRANSIT_PROFILE_BY_DENSITY[density_level]
        coverage_override = HIGH_TRANSIT_CITIES_FR.get(city) if country == "FR" else HIGH_TRANSIT_CITIES_ES.get(city)
        coverage = coverage_override if coverage_override is not None else profile["coverage_pct"]
        lines_count = profile["lines_count"] + (3 if coverage_override and coverage_override >= 85 else 0)
        modes = profile["modes"]
        label = coverage_label(coverage) if country == "FR" else coverage_label_es(coverage)

        out = []
        for idx in range(min(lines_count, 6)):
            mode = modes[idx % len(modes)]
            is_priority = idx < max(2, len(modes))
            freq = profile["frequency_peak_min"] if is_priority else profile["frequency_offpeak_min"]
            out.append(TransitLine(
                line_id=f"tl_{uuid4().hex[:8]}",
                name=f"Ligne {mode.upper()} {idx+1}",
                mode=mode,
                frequency_peak=f"{freq} min",
                compatibility_sap_hours=(freq <= 15),
                notes=(f"Desserte {label} - couverture territoire {coverage}%." if is_priority
                       else f"Ligne secondaire - fréquence {freq} min."),
            ))
        return out

    def _density_level(self, study: Study) -> str:
        density = None
        for m in study.metrics:
            if m.metric_id == "density_population":
                try:
                    density = float(m.value)
                except (TypeError, ValueError):
                    density = None
                break
        if density is None:
            return "periurban"
        if density >= 4000:
            return "very_urban"
        if density >= 1500:
            return "urban"
        if density >= 300:
            return "periurban"
        return "rural"

    def _base_income(self, study: Study) -> float:
        for m in study.metrics:
            if m.metric_id == "median_income":
                try:
                    return float(m.value)
                except (TypeError, ValueError):
                    pass
        if study.country == "FR":
            return FR_MEDIAN_INCOME_DEFAULT
        region = (study.geo_scope.region or "").strip()
        return ES_MEDIAN_INCOME_BY_REGION.get(region, ES_MEDIAN_INCOME_DEFAULT)

    def _base_price_m2(self, study: Study) -> float:
        for m in study.metrics:
            if m.metric_id == "real_estate_price_house_m2":
                try:
                    return float(m.value)
                except (TypeError, ValueError):
                    pass
        return 3200.0

    def _base_rent_m2(self, study: Study) -> float:
        for m in study.metrics:
            if m.metric_id == "rental_price_m2":
                try:
                    return float(m.value)
                except (TypeError, ValueError):
                    pass
        return 13.5

    def _lookup_population(self, study: Study) -> int:
        for m in study.metrics:
            if m.metric_id == "population_total":
                try:
                    return int(m.value)
                except (TypeError, ValueError):
                    return 50000
        return 50000

    def _is_premium(self, n: Neighborhood) -> bool:
        if n.real_estate_price_m2 and n.real_estate_price_m2 >= PREMIUM_PRICE_M2_THRESHOLD:
            return True
        if n.rental_price_m2 and n.rental_price_m2 >= PREMIUM_RENT_M2_THRESHOLD:
            return True
        return False

    def _compute_premium_score(self, n: Neighborhood, base_price, base_rent, base_income) -> float:
        score = 0.0
        if n.real_estate_price_m2 and base_price:
            score += min(50, (n.real_estate_price_m2 / base_price) * 30)
        if n.rental_price_m2 and base_rent:
            score += min(30, (n.rental_price_m2 / base_rent) * 25)
        if n.median_income and base_income:
            score += min(20, (n.median_income / base_income) * 15)
        return round(min(score, 100), 1)


microzones_engine = MicroZonesEngine()
