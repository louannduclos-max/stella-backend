"""Référentiel seniors / dépendance.
FR : CNSA - bénéficiaires APA par département (taux pour 1000 hab 75+).
ES : IMSERSO - SAAD Ley de Dependencia (taux bénéficiaires pour 1000 hab 65+).
Valeurs publiques agrégées 2023-2024. À actualiser annuellement.
"""

# Taux bénéficiaires APA pour 1000 habitants 75+ par département FR
# Source: CNSA - Aide à l'autonomie des personnes âgées (open data)
FR_APA_RATE_PER_1000_75PLUS = {
    "01": 195, "02": 205, "03": 220, "04": 215, "05": 200, "06": 175,
    "07": 210, "08": 215, "09": 220, "10": 200, "11": 215, "12": 225,
    "13": 200, "14": 195, "15": 230, "16": 215, "17": 200, "18": 220,
    "19": 230, "21": 200, "22": 195, "23": 235, "24": 220, "25": 195,
    "26": 200, "27": 195, "28": 200, "29": 190, "2A": 210, "2B": 215,
    "30": 210, "31": 190, "32": 220, "33": 195, "34": 200, "35": 185,
    "36": 230, "37": 200, "38": 195, "39": 210, "40": 205, "41": 210,
    "42": 210, "43": 220, "44": 185, "45": 205, "46": 220, "47": 215,
    "48": 230, "49": 195, "50": 200, "51": 200, "52": 215, "53": 195,
    "54": 200, "55": 215, "56": 195, "57": 210, "58": 225, "59": 215,
    "60": 200, "61": 215, "62": 220, "63": 205, "64": 195, "65": 215,
    "66": 210, "67": 200, "68": 200, "69": 185, "70": 215, "71": 215,
    "72": 205, "73": 195, "74": 175, "75": 165, "76": 200, "77": 185,
    "78": 170, "79": 215, "80": 215, "81": 215, "82": 210, "83": 195,
    "84": 200, "85": 200, "86": 215, "87": 225, "88": 215, "89": 215,
    "90": 200, "91": 175, "92": 170, "93": 195, "94": 180, "95": 180,
}
FR_APA_RATE_DEFAULT = 205

# Part ménages seniors seuls (%) par département - estimation INSEE
FR_SINGLE_SENIOR_SHARE_BY_DEPT = {
    "75": 18.5, "92": 14.5, "93": 13.0, "94": 14.0, "95": 12.5,
    "13": 13.8, "69": 14.2, "44": 12.5, "33": 13.5, "31": 13.2,
    "59": 13.8, "67": 13.0, "06": 15.2, "34": 13.5,
}
FR_SINGLE_SENIOR_SHARE_DEFAULT = 13.5


# Taux bénéficiaires SAAD pour 1000 hab 65+ par comunidad autónoma ES
# Source: IMSERSO - Estadísticas SAAD / Ley de Dependencia
ES_SAAD_BENEFICIARIES_BY_REGION = {
    "Madrid": {"rate_per_1000_65plus": 95, "single_senior_share": 22.5},
    "Cataluña": {"rate_per_1000_65plus": 110, "single_senior_share": 23.0},
    "Andalucía": {"rate_per_1000_65plus": 135, "single_senior_share": 19.5},
    "Valencia": {"rate_per_1000_65plus": 105, "single_senior_share": 21.0},
    "Comunidad Valenciana": {"rate_per_1000_65plus": 105, "single_senior_share": 21.0},
    "País Vasco": {"rate_per_1000_65plus": 130, "single_senior_share": 24.5},
    "Galicia": {"rate_per_1000_65plus": 120, "single_senior_share": 25.0},
    "Castilla y León": {"rate_per_1000_65plus": 145, "single_senior_share": 26.5},
    "Castilla-La Mancha": {"rate_per_1000_65plus": 140, "single_senior_share": 22.0},
    "Aragón": {"rate_per_1000_65plus": 125, "single_senior_share": 25.0},
    "Murcia": {"rate_per_1000_65plus": 100, "single_senior_share": 19.5},
    "Asturias": {"rate_per_1000_65plus": 130, "single_senior_share": 27.5},
    "Navarra": {"rate_per_1000_65plus": 120, "single_senior_share": 23.5},
    "Extremadura": {"rate_per_1000_65plus": 145, "single_senior_share": 22.5},
    "Cantabria": {"rate_per_1000_65plus": 125, "single_senior_share": 24.0},
    "La Rioja": {"rate_per_1000_65plus": 130, "single_senior_share": 23.0},
    "Baleares": {"rate_per_1000_65plus": 100, "single_senior_share": 21.5},
    "Canarias": {"rate_per_1000_65plus": 90, "single_senior_share": 19.0},
    "Ceuta": {"rate_per_1000_65plus": 85, "single_senior_share": 18.5},
    "Melilla": {"rate_per_1000_65plus": 85, "single_senior_share": 18.5},
}
ES_SAAD_DEFAULT = {"rate_per_1000_65plus": 115, "single_senior_share": 22.0}
