from app.core.enums import ConfidenceGrade, VerdictEnum


SCORE_CONFIG = {
    "market_attractiveness": {
        "label": "Attractivité marché",
        "weight": 25,
        "higher_is_better": True,
        "metrics": [
            {"metric_id": "population_total", "weight": 0.20},
            {"metric_id": "population_growth_5y", "weight": 0.10},
            {"metric_id": "seniors_60_plus_share", "weight": 0.20},
            {"metric_id": "households_with_children_share", "weight": 0.15},
            {"metric_id": "secondary_residences_share", "weight": 0.10},
            {"metric_id": "premium_neighborhoods_count", "weight": 0.15},
            {"metric_id": "real_estate_premium_zone_share", "weight": 0.10},
        ],
    },
    "rh_feasibility": {
        "label": "Faisabilité RH",
        "weight": 15,
        "higher_is_better": True,
        "metrics": [
            {"metric_id": "unemployment_rate", "weight": 0.30},
            {"metric_id": "care_worker_pool", "weight": 0.40},
            {"metric_id": "jobseekers_service_sector", "weight": 0.15},
            {"metric_id": "car_dependency_share", "weight": 0.15},
        ],
    },
    "competitive_pressure": {
        "label": "Pression concurrentielle",
        "weight": 15,
        "higher_is_better": False,
        "metrics": [
            {"metric_id": "competitor_count_15min", "weight": 0.35},
            {"metric_id": "top_competitor_density", "weight": 0.20},
            {"metric_id": "brand_presence_flag", "weight": 0.15},
            {"metric_id": "franchise_brand_count", "weight": 0.15},
            {"metric_id": "association_competitor_count", "weight": 0.10},
            {"metric_id": "recent_openings_2y", "weight": 0.05},
        ],
    },
    "regulatory_complexity": {
        "label": "Complexité réglementaire",
        "weight": 10,
        "higher_is_better": False,
        "metrics": [
            {"metric_id": "regulatory_barrier_level", "weight": 0.55},
            {"metric_id": "public_aid_coverage", "weight": 0.25},
            {"metric_id": "saad_authorization_required", "weight": 0.20},
        ],
    },
    "premium_potential": {
        "label": "Potentiel premium",
        "weight": 10,
        "higher_is_better": True,
        "metrics": [
            {"metric_id": "median_income", "weight": 0.20},
            {"metric_id": "taxable_households_share", "weight": 0.15},
            {"metric_id": "real_estate_price_house_m2", "weight": 0.20},
            {"metric_id": "real_estate_price_apartment_m2", "weight": 0.10},
            {"metric_id": "rental_price_m2", "weight": 0.15},
            {"metric_id": "real_estate_premium_zone_share", "weight": 0.10},
            {"metric_id": "premium_customer_potential", "weight": 0.10},
        ],
    },
    "recurring_revenue_potential": {
        "label": "Potentiel récurrent",
        "weight": 10,
        "higher_is_better": True,
        "metrics": [
            {"metric_id": "seniors_75_plus_share", "weight": 0.30},
            {"metric_id": "single_senior_households", "weight": 0.20},
            {"metric_id": "home_ownership_share", "weight": 0.15},
            {"metric_id": "dependency_ratio_apa", "weight": 0.15},
            {"metric_id": "recurring_revenue_share_potential", "weight": 0.20},
        ],
    },
    "execution_risk": {
        "label": "Risque d'exécution",
        "weight": 15,
        "higher_is_better": False,
        "metrics": [
            {"metric_id": "travel_time_spread", "weight": 0.25},
            {"metric_id": "parking_constraint_index", "weight": 0.10},
            {"metric_id": "rush_hour_penalty", "weight": 0.10},
            {"metric_id": "estimated_initial_investment", "weight": 0.25},
            {"metric_id": "estimated_monthly_fixed_costs", "weight": 0.20},
            {"metric_id": "main_traffic_axes", "weight": 0.10},
        ],
    },
}


VERDICT_RULES = {
    "go": {"min_score": 75, "max_blocking_failures": 0, "min_confidence": ConfidenceGrade.B},
    "go_conditional": {"min_score": 60, "max_blocking_failures": 2, "min_confidence": ConfidenceGrade.C},
    "no_go": {"min_score": 0, "max_blocking_failures": 99, "min_confidence": ConfidenceGrade.E},
}

VERDICT_MAPPING = {
    "go": VerdictEnum.GO,
    "go_conditional": VerdictEnum.GO_CONDITIONAL,
    "no_go": VerdictEnum.NO_GO,
}

CONFIDENCE_PENALTY = {
    ConfidenceGrade.A: 0,
    ConfidenceGrade.B: 2,
    ConfidenceGrade.C: 5,
    ConfidenceGrade.D: 10,
    ConfidenceGrade.E: 20,
}


DEFAULT_METRIC_BASELINES = {
    # demography
    "population_total": 50000,
    "population_growth_5y": 2.0,
    "density_population": 300,
    # segments
    "seniors_60_plus_share": 28.0,
    "seniors_75_plus_share": 12.0,
    "single_senior_households": 3000,
    "households_with_children_share": 28.0,
    "working_age_women_share": 19.0,
    "dependency_ratio_apa": 800,
    # employment
    "unemployment_rate": 8.0,
    "care_worker_pool": 600,
    "jobseekers_service_sector": 250,
    # income & housing
    "median_income": 23000,
    "taxable_households_share": 52.0,
    "home_ownership_share": 58.0,
    "tenants_share": 42.0,
    "secondary_residences_share": 8.0,
    "vacant_housing_share": 6.0,
    "houses_vs_apartments_share": 55.0,
    "avg_house_surface": 105,
    "avg_apartment_surface": 65,
    "avg_land_surface": 400,
    # real estate
    "real_estate_price_house_m2": 3200,
    "real_estate_price_apartment_m2": 3500,
    "real_estate_avg_transaction": 290000,
    "rental_price_m2": 13.5,
    "real_estate_price_growth_5y": 12.0,
    "real_estate_premium_zone_share": 25.0,
    # microzones
    "neighborhood_count": 8,
    "premium_neighborhoods_count": 2,
    "key_streets_count": 12,
    "main_traffic_axes": 3,
    "transit_lines_count": 4,
    # competition
    "competitor_count_15min": 12,
    "competitor_count_30min": 25,
    "top_competitor_density": 55,
    "brand_presence_flag": 1,
    "franchise_brand_count": 3,
    "association_competitor_count": 2,
    "ccas_presence_flag": 1,
    "recent_openings_2y": 2,
    # pricing
    "avg_hourly_price_cleaning": 24,
    "avg_hourly_price_care": 29,
    "regulated_saad_rate": 23.5,
    # operations
    "travel_time_spread": 24,
    "parking_constraint_index": 45,
    "car_dependency_share": 72.0,
    "rush_hour_penalty": 8,
    # tourism
    "tourism_overnight_stays": 250000,
    "tourism_seasonality_index": 1.8,
    "seasonal_revenue_multiplier": 1.5,
    # regulation
    "regulatory_barrier_level": 35,
    "public_aid_coverage": 60,
    "saad_authorization_required": 1,
    "apa_hourly_rate": 23.5,
    # business case
    "estimated_initial_investment": 45000,
    "estimated_monthly_fixed_costs": 12000,
    "recurring_revenue_share_potential": 58,
    "premium_customer_potential": 55,
    "franchise_entry_fee": 30000,
    "franchise_royalty_rate": 6.0,
}
