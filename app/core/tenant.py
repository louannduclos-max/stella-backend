DEFAULT_TENANT = "interdomicilio"

def resolve_tenant(brand_slug=None, explicit=None):
    if explicit:
        return explicit.strip().lower()
    if brand_slug:
        return brand_slug.strip().lower().split()[0]
    return DEFAULT_TENANT
