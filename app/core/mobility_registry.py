"""Référentiel mobilité & opérations.
FR : INSEE mobilité domicile-travail (% voiture) + indicateurs urbains.
ES : INE Encuesta de Movilidad + indicadores urbanos.
Valeurs agrégées par département / comunidad. À actualiser annuellement.
"""

# Part actifs en voiture pour trajet domicile-travail (%) - INSEE mobilité 2020
FR_CAR_DEPENDENCY_BY_DEPT = {
    "75": 12.5, "92": 38.5, "93": 45.0, "94": 42.5, "95": 58.5,
    "78": 60.0, "91": 65.0, "77": 70.0,
    "13": 70.0, "06": 65.5, "83": 78.0, "84": 76.0,
    "69": 60.5, "31": 65.5, "33": 65.0, "44": 68.0,
    "59": 67.0, "67": 65.0, "34": 70.5, "35": 65.0,
    "56": 78.5, "29": 78.0, "22": 80.5, "85": 80.0,
    "73": 76.0, "74": 75.0, "65": 78.0, "66": 73.5,
    "2A": 76.0, "2B": 76.0,
}
FR_CAR_DEPENDENCY_DEFAULT = 74.0

# Pénalité moyenne heures de pointe (min) par typologie département
FR_RUSH_HOUR_PENALTY_BY_DEPT = {
    "75": 18, "92": 16, "93": 15, "94": 15, "95": 14,
    "78": 13, "91": 13, "77": 12,
    "13": 14, "06": 12, "83": 10, "69": 13,
    "31": 11, "33": 11, "44": 10, "59": 11, "67": 10,
    "34": 9, "35": 9, "56": 6, "29": 6, "22": 5,
    "85": 5, "44": 9, "73": 8, "74": 9, "2A": 6, "2B": 6,
}
FR_RUSH_HOUR_PENALTY_DEFAULT = 7

# Indice contrainte stationnement (0-100, plus haut = plus contraignant)
FR_PARKING_BY_DEPT = {
    "75": 85, "92": 70, "93": 60, "94": 65, "69": 70,
    "13": 70, "06": 72, "31": 60, "33": 60, "44": 58,
    "59": 55, "67": 60, "34": 58, "35": 50,
    "56": 35, "29": 35, "22": 30, "85": 30,
    "2A": 50, "2B": 50, "73": 50, "74": 55,
}
FR_PARKING_DEFAULT = 45


# Comunidades autónomas ES - mobilité voiture (INE / Ministerio de Transportes)
ES_CAR_DEPENDENCY_BY_REGION = {
    "Madrid":                  45.0,
    "Cataluña":                52.0,
    "Andalucía":               68.0,
    "Valencia":                65.0,
    "Comunidad Valenciana":    65.0,
    "País Vasco":              48.0,
    "Galicia":                 70.0,
    "Castilla y León":         72.0,
    "Castilla-La Mancha":      75.0,
    "Aragón":                  68.0,
    "Murcia":                  72.0,
    "Asturias":                65.0,
    "Navarra":                 68.0,
    "Extremadura":             75.0,
    "Cantabria":               66.0,
    "La Rioja":                70.0,
    "Baleares":                65.0,
    "Canarias":                70.0,
    "Ceuta":                   55.0,
    "Melilla":                 55.0,
}
ES_CAR_DEPENDENCY_DEFAULT = 65.0

ES_RUSH_HOUR_PENALTY_BY_REGION = {
    "Madrid": 16, "Cataluña": 14, "País Vasco": 12,
    "Valencia": 10, "Comunidad Valenciana": 10,
    "Andalucía": 10, "Baleares": 11, "Canarias": 12,
    "Galicia": 7, "Asturias": 7, "Cantabria": 6,
}
ES_RUSH_HOUR_PENALTY_DEFAULT = 8

ES_PARKING_BY_REGION = {
    "Madrid": 82, "Cataluña": 72, "País Vasco": 68,
    "Valencia": 62, "Comunidad Valenciana": 62,
    "Andalucía": 58, "Baleares": 65, "Canarias": 62,
    "Galicia": 50, "Asturias": 50, "Cantabria": 48,
    "Navarra": 55, "Aragón": 55,
}
ES_PARKING_DEFAULT = 50

# Dispersion temps de trajet par densité (min)
TRAVEL_TIME_SPREAD_BY_DENSITY = {
    "very_urban":  18,
    "urban":       22,
    "periurban":   28,
    "rural":       35,
}
