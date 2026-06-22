"""
Catalogue des profils entreprise consommé par Lovable.

Chaque profil porte:
- identité (slug, nom, pays, modèle business par défaut)
- charte graphique (couleurs hex, font)
- services par défaut
- KPI prioritaires à pousser dans l'UI Lovable
- concurrents directs à matcher (détection brand_presence_flag)
- positionnement et pricing par défaut

Lovable peut récupérer la liste via /config/brand-profiles
et un profil précis via /config/brand-profiles/{slug}.
"""

BRAND_PROFILES = {
    # ============= FR =============
    "o2": {
        "slug": "o2",
        "brand_name": "O2 Care Services",
        "country": "FR",
        "business_model_default": "franchise",
        "positioning_default": "premium",
        "palette": {
            "primary": "#0066CC",
            "primary_dark": "#003D7A",
            "text": "#2C2C2C",
            "accent": "#00CC66",
            "alert": "#FF3333",
            "warn": "#FF9900",
        },
        "font_family": "Arial, Helvetica, sans-serif",
        "default_services": ["menage", "seniors", "garde_enfants", "jardinage", "handicap"],
        "target_segments_default": ["seniors", "familles", "actifs_premium"],
        "pricing_default_eur_hour": {"cleaning": 28.0, "care": 32.0},
        "priority_kpis": [
            "population_total", "seniors_60_plus_share", "seniors_75_plus_share",
            "single_senior_households", "median_income", "taxable_households_share",
            "real_estate_price_house_m2", "rental_price_m2",
            "competitor_count_15min", "franchise_brand_count", "brand_presence_flag",
            "apa_hourly_rate", "regulatory_barrier_level",
            "premium_neighborhoods_count",
        ],
        "direct_competitors": ["o2", "shiva", "apef", "vitalliance", "destia", "age d'or", "petits-fils", "domaliance"],
        "associations_to_track": ["admr", "una", "adpad", "tout a dom"],
        "lovable_flags": {
            "show_company_costs": False,
            "show_franchise_entry_fee": False,
            "show_royalties": False,
        },
    },
    "shiva": {
        "slug": "shiva",
        "brand_name": "Shiva",
        "country": "FR",
        "business_model_default": "mandataire",
        "positioning_default": "premium",
        "palette": {
            "primary": "#8B0000",
            "primary_dark": "#5A0000",
            "text": "#2C2C2C",
            "accent": "#D4AF37",
            "alert": "#FF3333",
            "warn": "#FF9900",
        },
        "font_family": "Georgia, 'Times New Roman', serif",
        "default_services": ["menage", "repassage"],
        "target_segments_default": ["actifs_premium", "familles"],
        "pricing_default_eur_hour": {"cleaning": 30.0, "care": 0.0},
        "priority_kpis": [
            "population_total", "median_income", "taxable_households_share",
            "real_estate_price_house_m2", "real_estate_premium_zone_share",
            "competitor_count_15min", "premium_neighborhoods_count",
        ],
        "direct_competitors": ["o2", "shiva", "wecasa", "yoojo"],
        "associations_to_track": [],
        "lovable_flags": {
            "show_company_costs": False,
            "show_franchise_entry_fee": False,
            "show_royalties": False,
        },
    },
    "apef": {
        "slug": "apef",
        "brand_name": "APEF Services",
        "country": "FR",
        "business_model_default": "franchise",
        "positioning_default": "milieu_gamme",
        "palette": {
            "primary": "#E30613",
            "primary_dark": "#A00410",
            "text": "#2C2C2C",
            "accent": "#FFCC00",
            "alert": "#FF3333",
            "warn": "#FF9900",
        },
        "font_family": "Arial, Helvetica, sans-serif",
        "default_services": ["menage", "seniors", "garde_enfants", "jardinage"],
        "target_segments_default": ["familles", "seniors"],
        "pricing_default_eur_hour": {"cleaning": 24.0, "care": 28.0},
        "priority_kpis": [
            "population_total", "seniors_60_plus_share", "median_income",
            "competitor_count_15min", "franchise_brand_count", "brand_presence_flag",
            "apa_hourly_rate",
        ],
        "direct_competitors": ["o2", "apef", "vitalliance", "destia"],
        "associations_to_track": ["admr"],
        "lovable_flags": {
            "show_company_costs": False,
            "show_franchise_entry_fee": False,
            "show_royalties": False,
        },
    },
    "vitalliance": {
        "slug": "vitalliance",
        "brand_name": "Vitalliance",
        "country": "FR",
        "business_model_default": "prestataire",
        "positioning_default": "premium_dependance",
        "palette": {
            "primary": "#7AB800",
            "primary_dark": "#4F7900",
            "text": "#2C2C2C",
            "accent": "#003D7A",
            "alert": "#FF3333",
            "warn": "#FF9900",
        },
        "font_family": "Arial, Helvetica, sans-serif",
        "default_services": ["dependance", "handicap", "seniors"],
        "target_segments_default": ["seniors_dependants", "personnes_handicapees"],
        "pricing_default_eur_hour": {"cleaning": 0.0, "care": 34.0},
        "priority_kpis": [
            "seniors_75_plus_share", "dependency_ratio_apa", "single_senior_households",
            "apa_hourly_rate", "regulated_saad_rate", "regulatory_barrier_level",
            "public_aid_coverage", "competitor_count_15min",
        ],
        "direct_competitors": ["vitalliance", "petits-fils", "age d'or", "destia"],
        "associations_to_track": ["admr", "una"],
        "lovable_flags": {
            "show_company_costs": False,
            "show_franchise_entry_fee": False,
            "show_royalties": False,
        },
    },

    # ============= ES =============
    "interdomicilio": {
        "slug": "interdomicilio",
        "brand_name": "Interdomicilio",
        "country": "ES",
        "business_model_default": "franchise",
        "positioning_default": "premium",
        "palette": {
            "primary": "#0095D9",
            "primary_dark": "#00608A",
            "text": "#2C2C2C",
            "accent": "#FFCC00",
            "alert": "#FF3333",
            "warn": "#FF9900",
        },
        "font_family": "Arial, Helvetica, sans-serif",
        "default_services": ["limpieza", "mayores", "cuidado_ninos", "ayuda_domicilio"],
        "target_segments_default": ["mayores", "familias"],
        "pricing_default_eur_hour": {"cleaning": 16.0, "care": 19.0},
        "priority_kpis": [
            "population_total", "seniors_60_plus_share", "single_senior_households",
            "median_income", "real_estate_price_house_m2", "rental_price_m2",
            "competitor_count_15min", "franchise_brand_count", "brand_presence_flag",
            "regulated_saad_rate", "regulatory_barrier_level",
        ],
        "direct_competitors": ["interdomicilio", "eulen", "clece", "serhogarsystem", "sergesa"],
        "associations_to_track": ["cruz roja", "caritas"],
        "lovable_flags": {
            "show_company_costs": False,
            "show_franchise_entry_fee": False,
            "show_royalties": False,
        },
    },
    "eulen": {
        "slug": "eulen",
        "brand_name": "Eulen Servicios Sociosanitarios",
        "country": "ES",
        "business_model_default": "prestataire",
        "positioning_default": "milieu_gamme",
        "palette": {
            "primary": "#003366",
            "primary_dark": "#001A33",
            "text": "#2C2C2C",
            "accent": "#FFB300",
            "alert": "#FF3333",
            "warn": "#FF9900",
        },
        "font_family": "Arial, Helvetica, sans-serif",
        "default_services": ["mayores", "limpieza", "dependencia"],
        "target_segments_default": ["mayores", "dependientes"],
        "pricing_default_eur_hour": {"cleaning": 15.0, "care": 18.0},
        "priority_kpis": [
            "population_total", "seniors_60_plus_share", "dependency_ratio_apa",
            "regulated_saad_rate", "public_aid_coverage",
            "competitor_count_15min", "franchise_brand_count",
        ],
        "direct_competitors": ["eulen", "clece", "interdomicilio"],
        "associations_to_track": ["cruz roja"],
        "lovable_flags": {
            "show_company_costs": False,
            "show_franchise_entry_fee": False,
            "show_royalties": False,
        },
    },
}


def list_brand_profiles(country: str | None = None) -> list[dict]:
    items = list(BRAND_PROFILES.values())
    if country:
        items = [b for b in items if b["country"] == country.upper()]
    return items


def get_brand_profile(slug: str) -> dict | None:
    return BRAND_PROFILES.get(slug.lower())


def merge_brand_profile(slug: str | None, override: dict | None) -> dict:
    """
    Fusionne le profil statique (BRAND_PROFILES) avec un override inline envoyé par le front.
    Le front passe company_branding + company_study_presets depuis Supabase.

    Priorité : override > statique > défaut vide.

    override attendu (format Supabase company_branding + presets) :
    {
      "primary_color": "#0095D9",
      "secondary_color": "#FFCC00",
      "accent_color": "#...",
      "logo_primary_url": "https://...",
      "brand_style": "premium",
      "default_kpis": [...],
      "default_activity_families": [...],
      "default_target_publics": [...],
      "default_risks": [...],
      "guidance": {...},
      "positioning": "...",       ← depuis companies.positioning
    }
    """
    base: dict = {}
    if slug:
        static = BRAND_PROFILES.get(slug.lower())
        if static:
            import copy
            base = copy.deepcopy(static)

    if not override:
        return base

    # Fusion palette depuis Supabase company_branding
    palette = base.setdefault("palette", {})
    if override.get("primary_color"):
        palette["primary"] = override["primary_color"]
    if override.get("secondary_color"):
        palette["secondary"] = override["secondary_color"]
    if override.get("accent_color"):
        palette["accent"] = override["accent_color"]
    if override.get("background_color"):
        palette["background"] = override["background_color"]

    # Logo
    if override.get("logo_primary_url"):
        base["logo_primary_url"] = override["logo_primary_url"]

    # KPIs prioritaires depuis company_study_presets.default_kpis
    if override.get("default_kpis"):
        kpis = override["default_kpis"]
        if isinstance(kpis, list):
            # Supporte [{code: "...", label: "..."}, ...] ou ["code1", "code2"]
            base["priority_kpis"] = [
                k["code"] if isinstance(k, dict) else str(k)
                for k in kpis
            ]

    # Activités par défaut
    if override.get("default_activity_families"):
        base["default_services"] = [
            a["activity_code"] if isinstance(a, dict) else str(a)
            for a in override["default_activity_families"]
        ]

    # Segments cibles
    if override.get("default_target_publics"):
        base["target_segments_default"] = [
            t["public_code"] if isinstance(t, dict) else str(t)
            for t in override["default_target_publics"]
        ]

    # Positionnement
    if override.get("positioning"):
        base["positioning_default"] = override["positioning"]

    # Guidance (notes libres)
    if override.get("guidance"):
        base["guidance"] = override["guidance"]

    return base
