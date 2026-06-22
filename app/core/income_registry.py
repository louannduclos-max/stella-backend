"""Référentiel revenus & habitat.
FR : INSEE Filosofi (revenus médians communes) + recensement (statut occupation, typologie).
ES : INE Atlas de Distribución de la Renta de los Hogares (renta media municipal).
Valeurs agrégées par département / comunidad. À actualiser annuellement.
"""

# Revenu médian par UC par département FR (EUR/an) - INSEE Filosofi 2021-2022
FR_MEDIAN_INCOME_BY_DEPT = {
    "01": 24200, "02": 21100, "03": 21500, "04": 22300, "05": 22600, "06": 23100,
    "07": 22300, "08": 21100, "09": 21000, "10": 22200, "11": 21500, "12": 22600,
    "13": 22500, "14": 22500, "15": 22000, "16": 22000, "17": 22300, "18": 21800,
    "19": 22000, "21": 23300, "22": 22600, "23": 21100, "24": 21900, "25": 23000,
    "26": 22500, "27": 22600, "28": 22800, "29": 22800, "2A": 22500, "2B": 21500,
    "30": 21200, "31": 23400, "32": 22000, "33": 23100, "34": 21800, "35": 23500,
    "36": 21800, "37": 22800, "38": 23800, "39": 22900, "40": 22300, "41": 22500,
    "42": 22200, "43": 22000, "44": 23700, "45": 22900, "46": 22000, "47": 21500,
    "48": 21800, "49": 22500, "50": 22300, "51": 22800, "52": 22000, "53": 22800,
    "54": 22600, "55": 21800, "56": 22900, "57": 22800, "58": 21800, "59": 21800,
    "60": 23400, "61": 22000, "62": 21300, "63": 22600, "64": 23300, "65": 22000,
    "66": 21000, "67": 23500, "68": 23400, "69": 24100, "70": 22500, "71": 22500,
    "72": 22300, "73": 24000, "74": 25800, "75": 30900, "76": 22500, "77": 25400,
    "78": 28200, "79": 22000, "80": 21800, "81": 22300, "82": 21500, "83": 22600,
    "84": 21900, "85": 22600, "86": 22200, "87": 21800, "88": 22000, "89": 22200,
    "90": 22500, "91": 26000, "92": 30600, "93": 19400, "94": 24800, "95": 24600,
}
FR_MEDIAN_INCOME_DEFAULT = 22500

# Part ménages imposables par département (%) - INSEE 2022
FR_TAXABLE_HOUSEHOLDS_BY_DEPT = {
    "75": 68.5, "92": 65.5, "78": 62.5, "91": 58.5, "74": 60.5,
    "69": 56.5, "31": 55.5, "44": 55.0, "33": 55.0, "67": 54.5,
    "13": 52.5, "59": 50.5, "62": 47.0, "93": 42.5,
}
FR_TAXABLE_DEFAULT = 52.0

# Part propriétaires occupants par département (%) - INSEE recensement 2020
FR_HOME_OWNERSHIP_BY_DEPT = {
    "75": 33.5, "92": 49.5, "93": 41.5, "94": 47.5, "95": 56.0,
    "13": 54.5, "69": 50.5, "59": 56.5, "44": 60.5, "33": 56.0,
    "56": 70.0, "29": 68.5, "22": 71.0, "35": 60.5,
}
FR_HOME_OWNERSHIP_DEFAULT = 58.0


# Renta media por hogar - INE Atlas de Distribución (EUR/an)
ES_MEDIAN_INCOME_BY_REGION = {
    "Madrid": 38500, "Cataluña": 36200, "País Vasco": 41800,
    "Navarra": 39500, "Aragón": 33500, "La Rioja": 33000,
    "Comunidad Valenciana": 30500, "Valencia": 30500, "Cantabria": 32500,
    "Asturias": 32000, "Castilla y León": 30500, "Galicia": 29500,
    "Baleares": 33500, "Castilla-La Mancha": 28000, "Murcia": 27500,
    "Andalucía": 27000, "Canarias": 26500, "Extremadura": 24500,
    "Ceuta": 28500, "Melilla": 28000,
}
ES_MEDIAN_INCOME_DEFAULT = 30000

ES_HOME_OWNERSHIP_BY_REGION = {
    "Madrid": 73.0, "Cataluña": 70.5, "País Vasco": 78.5,
    "Navarra": 79.0, "Aragón": 78.0, "La Rioja": 78.5,
    "Comunidad Valenciana": 78.5, "Valencia": 78.5, "Cantabria": 79.5,
    "Asturias": 77.0, "Castilla y León": 80.5, "Galicia": 79.0,
    "Baleares": 70.0, "Castilla-La Mancha": 82.0, "Murcia": 79.0,
    "Andalucía": 76.5, "Canarias": 71.5, "Extremadura": 81.0,
    "Ceuta": 72.0, "Melilla": 70.5,
}
ES_HOME_OWNERSHIP_DEFAULT = 76.5

ES_TAXABLE_BY_REGION = {
    "Madrid": 68.0, "Cataluña": 64.5, "País Vasco": 70.0,
    "Comunidad Valenciana": 56.0, "Valencia": 56.0,
    "Andalucía": 51.5, "Galicia": 54.0, "Castilla y León": 55.0,
    "Castilla-La Mancha": 51.0, "Extremadura": 48.5,
}
ES_TAXABLE_DEFAULT = 56.0
