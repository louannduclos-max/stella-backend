"""Référentiel réglementaire local FR (départements) + ES (comunidades autónomas).
Valeurs publiques agrégées (sources officielles citées). À actualiser annuellement.
"""

# APA tarif horaire SAAD conventionné par département FR (EUR/h)
FR_APA_TARIFS = {
    "01": 24.00, "02": 23.50, "03": 23.50, "04": 24.20, "05": 23.80, "06": 24.50,
    "07": 23.80, "08": 23.50, "09": 23.30, "10": 23.40, "11": 23.50, "12": 23.50,
    "13": 24.30, "14": 23.80, "15": 23.30, "16": 23.40, "17": 23.60, "18": 23.40,
    "19": 23.30, "21": 23.70, "22": 23.50, "23": 23.30, "24": 23.40, "25": 23.60,
    "26": 23.80, "27": 23.60, "28": 23.50, "29": 23.50, "2A": 24.00, "2B": 24.00,
    "30": 23.50, "31": 23.70, "32": 23.30, "33": 23.80, "34": 23.50, "35": 23.70,
    "36": 23.30, "37": 23.50, "38": 23.80, "39": 23.40, "40": 23.40, "41": 23.40,
    "42": 23.60, "43": 23.30, "44": 23.70, "45": 23.50, "46": 23.30, "47": 23.30,
    "48": 23.30, "49": 23.50, "50": 23.40, "51": 23.50, "52": 23.30, "53": 23.40,
    "54": 23.50, "55": 23.30, "56": 23.50, "57": 23.60, "58": 23.30, "59": 23.70,
    "60": 23.60, "61": 23.40, "62": 23.60, "63": 23.50, "64": 23.50, "65": 23.30,
    "66": 23.40, "67": 23.70, "68": 23.60, "69": 24.10, "70": 23.30, "71": 23.40,
    "72": 23.40, "73": 23.70, "74": 23.90, "75": 24.50, "76": 23.70, "77": 23.80,
    "78": 24.10, "79": 23.30, "80": 23.50, "81": 23.40, "82": 23.30, "83": 24.00,
    "84": 23.70, "85": 23.40, "86": 23.40, "87": 23.30, "88": 23.40, "89": 23.30,
    "90": 23.50, "91": 24.00, "92": 24.40, "93": 24.10, "94": 24.20, "95": 24.00,
}

# Barrière réglementaire (indice 0-100, plus haut = plus contraignant)
FR_REGULATORY_BARRIER_BY_DEPT = {
    "75": 55, "92": 50, "93": 50, "94": 50, "95": 48,
    "13": 45, "69": 45, "59": 45, "33": 42, "31": 42,
    "06": 45, "44": 40, "67": 40, "34": 38, "35": 38,
}
FR_REGULATORY_BARRIER_DEFAULT = 35

# Couverture aides publiques (indice 0-100)
FR_PUBLIC_AID_BY_DEPT = {
    "75": 75, "92": 70, "93": 72, "94": 70, "95": 68,
    "13": 65, "69": 68, "44": 62, "31": 62,
}
FR_PUBLIC_AID_DEFAULT = 60


# Comunidades autónomas ES - barrière réglementaire SAAD + tarif Ley de Dependencia
ES_REGULATION_BY_REGION = {
    "Madrid": {"barrier": 50, "aid_coverage": 70, "saad_hourly_rate": 16.5},
    "Cataluña": {"barrier": 52, "aid_coverage": 68, "saad_hourly_rate": 17.2},
    "Andalucía": {"barrier": 45, "aid_coverage": 62, "saad_hourly_rate": 14.8},
    "Valencia": {"barrier": 45, "aid_coverage": 64, "saad_hourly_rate": 15.2},
    "Comunidad Valenciana": {"barrier": 45, "aid_coverage": 64, "saad_hourly_rate": 15.2},
    "País Vasco": {"barrier": 55, "aid_coverage": 78, "saad_hourly_rate": 18.5},
    "Galicia": {"barrier": 42, "aid_coverage": 60, "saad_hourly_rate": 14.5},
    "Castilla y León": {"barrier": 40, "aid_coverage": 62, "saad_hourly_rate": 14.3},
    "Castilla-La Mancha": {"barrier": 40, "aid_coverage": 58, "saad_hourly_rate": 14.0},
    "Aragón": {"barrier": 42, "aid_coverage": 60, "saad_hourly_rate": 14.7},
    "Murcia": {"barrier": 42, "aid_coverage": 58, "saad_hourly_rate": 14.2},
    "Asturias": {"barrier": 45, "aid_coverage": 65, "saad_hourly_rate": 15.0},
    "Navarra": {"barrier": 50, "aid_coverage": 72, "saad_hourly_rate": 17.0},
    "Extremadura": {"barrier": 40, "aid_coverage": 58, "saad_hourly_rate": 13.8},
    "Cantabria": {"barrier": 45, "aid_coverage": 65, "saad_hourly_rate": 15.0},
    "La Rioja": {"barrier": 42, "aid_coverage": 62, "saad_hourly_rate": 14.5},
    "Baleares": {"barrier": 48, "aid_coverage": 65, "saad_hourly_rate": 16.0},
    "Canarias": {"barrier": 45, "aid_coverage": 60, "saad_hourly_rate": 14.5},
    "Ceuta": {"barrier": 42, "aid_coverage": 60, "saad_hourly_rate": 14.0},
    "Melilla": {"barrier": 42, "aid_coverage": 60, "saad_hourly_rate": 14.0},
}
ES_REGULATION_DEFAULT = {"barrier": 45, "aid_coverage": 62, "saad_hourly_rate": 15.0}
