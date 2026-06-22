"""Référentiel tourisme & saisonnalité.
FR : DGE / CRT régionaux - nuitées hôtelières + AirBnB + taxe séjour.
ES : INE / Turespaña - pernoctaciones hoteleras + viajeros.
Valeurs agrégées par région / comunidad. Niveau régional appliqué à la commune
sauf si typologie touristique connue (côte, montagne, ville).
"""

# Profil tourisme par région FR (CRT - nuitées annuelles total millions)
FR_TOURISM_BY_REGION = {
    "Île-de-France":          {"overnight_stays_per_capita": 8.5, "seasonality_index": 1.3, "revenue_multiplier": 1.2},
    "Provence-Alpes-Côte d'Azur": {"overnight_stays_per_capita": 27.0, "seasonality_index": 2.5, "revenue_multiplier": 1.8},
    "Auvergne-Rhône-Alpes":   {"overnight_stays_per_capita": 18.0, "seasonality_index": 2.2, "revenue_multiplier": 1.6},
    "Occitanie":              {"overnight_stays_per_capita": 22.0, "seasonality_index": 2.4, "revenue_multiplier": 1.7},
    "Nouvelle-Aquitaine":     {"overnight_stays_per_capita": 18.5, "seasonality_index": 2.3, "revenue_multiplier": 1.7},
    "Bretagne":               {"overnight_stays_per_capita": 30.0, "seasonality_index": 2.8, "revenue_multiplier": 1.9},
    "Pays de la Loire":       {"overnight_stays_per_capita": 14.0, "seasonality_index": 2.0, "revenue_multiplier": 1.5},
    "Normandie":              {"overnight_stays_per_capita": 13.0, "seasonality_index": 1.9, "revenue_multiplier": 1.4},
    "Hauts-de-France":        {"overnight_stays_per_capita": 7.0,  "seasonality_index": 1.4, "revenue_multiplier": 1.2},
    "Grand Est":              {"overnight_stays_per_capita": 9.0,  "seasonality_index": 1.5, "revenue_multiplier": 1.3},
    "Bourgogne-Franche-Comté":{"overnight_stays_per_capita": 10.0, "seasonality_index": 1.6, "revenue_multiplier": 1.3},
    "Centre-Val de Loire":    {"overnight_stays_per_capita": 9.5,  "seasonality_index": 1.7, "revenue_multiplier": 1.3},
    "Corse":                  {"overnight_stays_per_capita": 80.0, "seasonality_index": 4.5, "revenue_multiplier": 2.2},
}
FR_TOURISM_DEFAULT = {"overnight_stays_per_capita": 12.0, "seasonality_index": 1.8, "revenue_multiplier": 1.5}

# Codes département à fort profil touristique (override sur la région)
FR_HIGH_TOURISM_DEPTS = {
    "06": 2.0, "83": 2.0, "2A": 2.5, "2B": 2.5, "33": 1.8, "85": 1.8,
    "29": 1.8, "56": 1.8, "22": 1.7, "73": 2.2, "74": 2.2, "65": 2.0,
    "66": 2.0, "34": 1.8, "17": 1.8, "50": 1.7, "62": 1.7, "84": 1.6,
}


# Comunidades autónomas ES - INE EOH 2023 (pernoctaciones)
ES_TOURISM_BY_REGION = {
    "Madrid":                 {"overnight_stays_per_capita": 6.5,  "seasonality_index": 1.4, "revenue_multiplier": 1.2},
    "Cataluña":               {"overnight_stays_per_capita": 9.5,  "seasonality_index": 2.2, "revenue_multiplier": 1.6},
    "Andalucía":              {"overnight_stays_per_capita": 7.0,  "seasonality_index": 2.0, "revenue_multiplier": 1.6},
    "Valencia":               {"overnight_stays_per_capita": 7.5,  "seasonality_index": 2.2, "revenue_multiplier": 1.7},
    "Comunidad Valenciana":   {"overnight_stays_per_capita": 7.5,  "seasonality_index": 2.2, "revenue_multiplier": 1.7},
    "Baleares":               {"overnight_stays_per_capita": 60.0, "seasonality_index": 4.5, "revenue_multiplier": 2.4},
    "Canarias":               {"overnight_stays_per_capita": 45.0, "seasonality_index": 1.6, "revenue_multiplier": 2.0},
    "País Vasco":             {"overnight_stays_per_capita": 4.5,  "seasonality_index": 1.7, "revenue_multiplier": 1.4},
    "Galicia":                {"overnight_stays_per_capita": 4.0,  "seasonality_index": 2.0, "revenue_multiplier": 1.5},
    "Castilla y León":        {"overnight_stays_per_capita": 4.5,  "seasonality_index": 1.8, "revenue_multiplier": 1.4},
    "Castilla-La Mancha":     {"overnight_stays_per_capita": 3.0,  "seasonality_index": 1.6, "revenue_multiplier": 1.3},
    "Aragón":                 {"overnight_stays_per_capita": 5.0,  "seasonality_index": 1.9, "revenue_multiplier": 1.5},
    "Murcia":                 {"overnight_stays_per_capita": 4.5,  "seasonality_index": 2.1, "revenue_multiplier": 1.6},
    "Asturias":               {"overnight_stays_per_capita": 5.0,  "seasonality_index": 2.2, "revenue_multiplier": 1.6},
    "Navarra":                {"overnight_stays_per_capita": 4.0,  "seasonality_index": 1.7, "revenue_multiplier": 1.4},
    "Extremadura":            {"overnight_stays_per_capita": 3.5,  "seasonality_index": 1.7, "revenue_multiplier": 1.4},
    "Cantabria":              {"overnight_stays_per_capita": 5.5,  "seasonality_index": 2.3, "revenue_multiplier": 1.6},
    "La Rioja":               {"overnight_stays_per_capita": 3.5,  "seasonality_index": 1.7, "revenue_multiplier": 1.4},
    "Ceuta":                  {"overnight_stays_per_capita": 2.5,  "seasonality_index": 1.5, "revenue_multiplier": 1.3},
    "Melilla":                {"overnight_stays_per_capita": 2.5,  "seasonality_index": 1.5, "revenue_multiplier": 1.3},
}
ES_TOURISM_DEFAULT = {"overnight_stays_per_capita": 6.0, "seasonality_index": 1.8, "revenue_multiplier": 1.5}
