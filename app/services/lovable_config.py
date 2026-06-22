from app.core.brand_profiles import get_brand_profile
from app.core.constants import DEFAULT_VERSION
from app.core.kpi_catalog import KPI_CATALOG


# Tous les coûts liés à l'achat franchise = optionnels, NON cochés par défaut
FRANCHISE_PURCHASE_COST_METRICS = [
    "franchise_entry_fee",
    "franchise_royalty_rate",
]

# Coûts entreprise généraux = optionnels, NON cochés par défaut
COMPANY_COST_METRICS = [
    "estimated_initial_investment",
    "estimated_monthly_fixed_costs",
]


def build_lovable_config(
    business_model: str | None = None,
    study_id: str | None = None,
    brand_slug: str | None = None,
) -> dict:
    profile = get_brand_profile(brand_slug) if brand_slug else None
    if profile and not business_model:
        business_model = profile.get("business_model_default")
    normalized_model = (business_model or "").strip().lower()
    is_franchise = normalized_model == "franchise"

    metrics = []
    for item in KPI_CATALOG:
        metric_id = item["metric_id"]
        is_franchise_cost = bool(item.get("franchise_purchase_cost", False))
        excluded = bool(item.get("exclude_from_lovable", False))

        # Coûts achat franchise : disponibles uniquement si modèle franchise,
        # toujours optionnels, jamais cochés par défaut.
        if is_franchise_cost and not is_franchise:
            excluded = True

        optional = bool(item.get("lovable_optional", False)) or is_franchise_cost
        default_visible = (
            False
            if (is_franchise_cost or excluded)
            else bool(item.get("lovable_default_visible", True))
        )

        metrics.append(
            {
                "metric_id": metric_id,
                "label": item["label"],
                "theme_id": item["theme_id"],
                "priority": item["priority"],
                "lovable_optional": optional,
                "lovable_default_visible": default_visible,
                "exclude_from_lovable": excluded,
                "deprecated": bool(item.get("deprecated", False)),
                "franchise_purchase_cost": is_franchise_cost,
            }
        )

    optional_groups = [
        {
            "group_id": "company_costs",
            "label": "Coûts entreprise (général)",
            "default_visible": False,
            "optional": True,
            "metric_ids": COMPANY_COST_METRICS,
        },
        {
            "group_id": "franchise_purchase",
            "label": "Coûts achat franchise (droits, redevances)",
            "default_visible": False,
            "optional": True,
            "available": is_franchise,
            "metric_ids": [
                mid for mid in FRANCHISE_PURCHASE_COST_METRICS
                if any(m["metric_id"] == mid and not m["exclude_from_lovable"] for m in metrics)
            ],
        },
    ]

    palette = profile.get("palette") if profile else None
    font_family = profile.get("font_family") if profile else None
    priority_kpis = profile.get("priority_kpis") if profile else None

    return {
        "name": "lovable_display_config",
        "version": DEFAULT_VERSION,
        "study_id": study_id,
        "business_model": business_model,
        "brand_profile": profile,
        "payload": {
            "optional_groups": optional_groups,
            "metrics": metrics,
            "priority_kpis": priority_kpis,
            "palette": palette,
            "font_family": font_family,
        },
    }
