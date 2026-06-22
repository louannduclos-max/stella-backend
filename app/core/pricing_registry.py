"""Référentiel pricing SAP local.
FR : grilles tarifaires concurrents O2 / Shiva / Apef / Vitalliance / Destia + tarif SAAD CD.
ES : grilles tarifaires Interdomicilio / Eulen / Clece + tarifa Ley Dependencia.
Valeurs publiques agrégées 2024-2025. À actualiser semestriellement.
"""

# Prix horaires moyens par département FR (EUR/h, avant crédit d'impôt)
# Source: relevés sites concurrents O2/Shiva/Apef/Vitalliance par grandes zones
FR_PRICING_BY_DEPT = {
    "75": {"cleaning": 32.5, "care": 36.5, "saad_regulated": 24.5},
    "92": {"cleaning": 31.5, "care": 35.5, "saad_regulated": 24.4},
    "93": {"cleaning": 28.5, "care": 32.5, "saad_regulated": 24.1},
    "94": {"cleaning": 30.0, "care": 34.0, "saad_regulated": 24.2},
    "95": {"cleaning": 29.0, "care": 33.0, "saad_regulated": 24.0},
    "78": {"cleaning": 30.5, "care": 34.5, "saad_regulated": 24.1},
    "91": {"cleaning": 29.5, "care": 33.5, "saad_regulated": 24.0},
    "77": {"cleaning": 28.5, "care": 32.5, "saad_regulated": 23.8},
    "06": {"cleaning": 28.5, "care": 32.5, "saad_regulated": 24.5},
    "13": {"cleaning": 26.5, "care": 30.5, "saad_regulated": 24.3},
    "83": {"cleaning": 27.5, "care": 31.5, "saad_regulated": 24.0},
    "69": {"cleaning": 27.0, "care": 31.5, "saad_regulated": 24.1},
    "31": {"cleaning": 25.5, "care": 30.0, "saad_regulated": 23.7},
    "33": {"cleaning": 26.0, "care": 30.5, "saad_regulated": 23.8},
    "44": {"cleaning": 25.5, "care": 30.0, "saad_regulated": 23.7},
    "59": {"cleaning": 24.5, "care": 28.5, "saad_regulated": 23.7},
    "67": {"cleaning": 25.5, "care": 30.0, "saad_regulated": 23.7},
    "34": {"cleaning": 24.5, "care": 29.0, "saad_regulated": 23.5},
    "35": {"cleaning": 25.0, "care": 29.5, "saad_regulated": 23.7},
    "56": {"cleaning": 24.5, "care": 29.0, "saad_regulated": 23.5},
    "29": {"cleaning": 24.0, "care": 28.5, "saad_regulated": 23.5},
    "22": {"cleaning": 23.5, "care": 28.0, "saad_regulated": 23.5},
    "74": {"cleaning": 28.5, "care": 32.5, "saad_regulated": 23.9},
    "73": {"cleaning": 27.0, "care": 31.0, "saad_regulated": 23.7},
    "2A": {"cleaning": 26.0, "care": 30.0, "saad_regulated": 24.0},
    "2B": {"cleaning": 26.0, "care": 30.0, "saad_regulated": 24.0},
}
FR_PRICING_DEFAULT = {"cleaning": 24.0, "care": 28.5, "saad_regulated": 23.5}

# Brand pricing benchmark FR (EUR/h, indicatif, avant crédit d'impôt)
FR_BRAND_PRICING = {
    "O2":          {"cleaning": 26.0, "care": 30.0},
    "Shiva":       {"cleaning": 28.0, "care": None},
    "Apef":        {"cleaning": 24.5, "care": 29.0},
    "Vitalliance": {"cleaning": None, "care": 30.5},
    "Destia":      {"cleaning": 25.0, "care": 29.5},
    "Age d'or":    {"cleaning": 25.5, "care": 30.0},
    "Petits-fils": {"cleaning": None, "care": 32.5},
}


# Tarifs horaires moyens par comunidad autónoma ES (EUR/h, avant deducciones)
# Source: relevés Interdomicilio / Eulen / Clece / Serhogarsystem
ES_PRICING_BY_REGION = {
    "Madrid":                  {"cleaning": 16.5, "care": 19.5, "saad_regulated": 16.5},
    "Cataluña":                {"cleaning": 17.0, "care": 20.0, "saad_regulated": 17.2},
    "Andalucía":               {"cleaning": 13.5, "care": 16.5, "saad_regulated": 14.8},
    "Valencia":                {"cleaning": 14.5, "care": 17.0, "saad_regulated": 15.2},
    "Comunidad Valenciana":    {"cleaning": 14.5, "care": 17.0, "saad_regulated": 15.2},
    "País Vasco":              {"cleaning": 17.5, "care": 21.0, "saad_regulated": 18.5},
    "Galicia":                 {"cleaning": 13.5, "care": 16.0, "saad_regulated": 14.5},
    "Castilla y León":         {"cleaning": 13.0, "care": 16.0, "saad_regulated": 14.3},
    "Castilla-La Mancha":      {"cleaning": 12.5, "care": 15.5, "saad_regulated": 14.0},
    "Aragón":                  {"cleaning": 13.5, "care": 16.5, "saad_regulated": 14.7},
    "Murcia":                  {"cleaning": 13.0, "care": 15.5, "saad_regulated": 14.2},
    "Asturias":                {"cleaning": 14.0, "care": 16.5, "saad_regulated": 15.0},
    "Navarra":                 {"cleaning": 16.0, "care": 19.0, "saad_regulated": 17.0},
    "Extremadura":             {"cleaning": 12.5, "care": 15.0, "saad_regulated": 13.8},
    "Cantabria":               {"cleaning": 14.0, "care": 16.5, "saad_regulated": 15.0},
    "La Rioja":                {"cleaning": 13.5, "care": 16.0, "saad_regulated": 14.5},
    "Baleares":                {"cleaning": 16.0, "care": 18.5, "saad_regulated": 16.0},
    "Canarias":                {"cleaning": 13.5, "care": 16.0, "saad_regulated": 14.5},
    "Ceuta":                   {"cleaning": 13.0, "care": 15.5, "saad_regulated": 14.0},
    "Melilla":                 {"cleaning": 13.0, "care": 15.5, "saad_regulated": 14.0},
}
ES_PRICING_DEFAULT = {"cleaning": 14.0, "care": 17.0, "saad_regulated": 15.0}

# Brand pricing benchmark ES (EUR/h, indicatif)
ES_BRAND_PRICING = {
    "Interdomicilio":   {"cleaning": 14.5, "care": 17.5},
    "Eulen":            {"cleaning": 16.0, "care": 19.0},
    "Clece":            {"cleaning": 15.5, "care": 18.5},
    "Serhogarsystem":   {"cleaning": 14.0, "care": 17.0},
    "Sergesa":          {"cleaning": 13.5, "care": 16.5},
}
