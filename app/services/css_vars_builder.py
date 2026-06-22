from app.core.brand_profiles import get_brand_profile, merge_brand_profile


DEFAULT_PALETTE = {
    "primary": "#0066CC",
    "primary_dark": "#003D7A",
    "text": "#2C2C2C",
    "accent": "#00CC66",
    "alert": "#FF3333",
    "warn": "#FF9900",
}
DEFAULT_FONT = "Arial, Helvetica, sans-serif"


def _palette_to_variables(palette: dict, font: str, brand_name: str, slug: str | None) -> dict:
    return {
        "slug": slug,
        "brand_name": brand_name,
        "variables": {
            "--stella-primary": palette.get("primary", DEFAULT_PALETTE["primary"]),
            "--stella-primary-dark": palette.get("primary_dark", DEFAULT_PALETTE["primary_dark"]),
            "--stella-text": palette.get("text", DEFAULT_PALETTE["text"]),
            "--stella-accent": palette.get("accent", DEFAULT_PALETTE["accent"]),
            "--stella-alert": palette.get("alert", DEFAULT_PALETTE["alert"]),
            "--stella-warn": palette.get("warn", DEFAULT_PALETTE["warn"]),
            "--stella-highlight": palette.get("background", "#E6F2FF"),
            "--stella-grey-light": "#F0F0F0",
            "--stella-font": font,
        },
    }


def build_css_vars(slug: str | None) -> dict:
    profile = get_brand_profile(slug) if slug else None
    palette = (profile or {}).get("palette") or DEFAULT_PALETTE
    font = (profile or {}).get("font_family") or DEFAULT_FONT
    brand_name = (profile or {}).get("brand_name") or "Default"
    return _palette_to_variables(palette, font, brand_name, slug)


def build_css_vars_for_study(slug: str | None, brand_profile_override: dict | None) -> dict:
    """
    Construit les CSS vars en fusionnant le registre statique (slug) avec
    l'override inline du front (company_branding + presets Supabase).
    Utilisé dans la réponse slides_5_0 pour auto-injection côté front.
    """
    profile = merge_brand_profile(slug, brand_profile_override)
    palette = profile.get("palette") or DEFAULT_PALETTE
    font = profile.get("font_family") or DEFAULT_FONT
    brand_name = profile.get("brand_name") or slug or "Default"
    return _palette_to_variables(palette, font, brand_name, slug)


def build_css_string(slug: str | None) -> str:
    data = build_css_vars(slug)
    lines = [f"  {k}: {v};" for k, v in data["variables"].items()]
    return (
        f"/* Stella CSS variables - brand: {data['brand_name']} */\n"
        ":root {\n" + "\n".join(lines) + "\n}\n"
    )


def build_css_string_for_study(slug: str | None, brand_profile_override: dict | None) -> str:
    data = build_css_vars_for_study(slug, brand_profile_override)
    lines = [f"  {k}: {v};" for k, v in data["variables"].items()]
    return (
        f"/* Stella CSS variables - brand: {data['brand_name']} */\n"
        ":root {\n" + "\n".join(lines) + "\n}\n"
    )
