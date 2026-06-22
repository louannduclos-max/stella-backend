"""Référentiel transports en commun (TC) FR + ES.
Indice de desserte par densité et profil urbain.
Lignes types, fréquences, compatibilité horaires SAP (7h-9h, 18h-20h).
"""

# Profil TC par niveau de densité - indices types
TRANSIT_PROFILE_BY_DENSITY = {
    "very_urban": {
        "lines_count": 12, "frequency_peak_min": 5, "frequency_offpeak_min": 12,
        "modes": ["metro", "bus", "tram"], "coverage_pct": 95, "sap_compatibility": True,
    },
    "urban": {
        "lines_count": 8, "frequency_peak_min": 10, "frequency_offpeak_min": 20,
        "modes": ["bus", "tram"], "coverage_pct": 80, "sap_compatibility": True,
    },
    "periurban": {
        "lines_count": 4, "frequency_peak_min": 20, "frequency_offpeak_min": 40,
        "modes": ["bus"], "coverage_pct": 55, "sap_compatibility": False,
    },
    "rural": {
        "lines_count": 2, "frequency_peak_min": 45, "frequency_offpeak_min": 90,
        "modes": ["bus"], "coverage_pct": 25, "sap_compatibility": False,
    },
}

# Villes FR à desserte TC élargie (top 60+ pôles urbains)
HIGH_TRANSIT_CITIES_FR = {
    "Paris": 100, "Lyon": 92, "Marseille": 80, "Toulouse": 78,
    "Nice": 75, "Nantes": 82, "Strasbourg": 85, "Bordeaux": 80,
    "Lille": 85, "Rennes": 78, "Montpellier": 76, "Grenoble": 80,
    "Saint-Étienne": 70, "Le Havre": 65, "Reims": 65, "Toulon": 60,
    "Aix-en-Provence": 68, "Brest": 60, "Le Mans": 60, "Amiens": 60,
    "Tours": 65, "Limoges": 55, "Clermont-Ferrand": 65, "Villeurbanne": 88,
    "Besançon": 65, "Orléans": 65, "Metz": 65, "Mulhouse": 62,
    "Caen": 65, "Nancy": 65, "Argenteuil": 75, "Montreuil": 85,
    "Roubaix": 75, "Tourcoing": 72, "Dunkerque": 55, "Avignon": 55,
    "Poitiers": 55, "Versailles": 78, "Courbevoie": 88, "Nanterre": 88,
    "Vitry-sur-Seine": 80, "Créteil": 82, "Pau": 55, "Asnières-sur-Seine": 85,
    "Rouen": 70, "Boulogne-Billancourt": 92, "Colombes": 80, "Saint-Denis": 88,
    "Aubervilliers": 85, "Champigny-sur-Marne": 72, "Saint-Maur-des-Fossés": 75,
    "Issy-les-Moulineaux": 88, "Levallois-Perret": 92, "Cannes": 60, "Antibes": 55,
    "La Rochelle": 55, "Calais": 50, "Mérignac": 70, "Chambéry": 60,
    "Annecy": 60, "Bourges": 50, "Quimper": 50, "Lorient": 55,
    "Vannes": 55, "Auray": 35, "Saint-Brieuc": 50, "Niort": 50,
    "Valence": 55, "Béziers": 55, "Perpignan": 55, "Bayonne": 55,
    "Biarritz": 55, "Saint-Nazaire": 55, "Cherbourg": 50, "Évreux": 50,
}

# Villes ES à desserte TC élargie (top 80+ municipios)
HIGH_TRANSIT_CITIES_ES = {
    # Grandes capitales métropolitaines
    "Madrid": 95, "Barcelona": 92, "Valencia": 80, "Sevilla": 75,
    "Zaragoza": 75, "Málaga": 70, "Murcia": 60, "Palma": 65,
    "Palma de Mallorca": 65, "Las Palmas": 65, "Las Palmas de Gran Canaria": 65,
    "Bilbao": 88, "Alicante": 65, "Córdoba": 60, "Valladolid": 65,
    "Vigo": 60, "Gijón": 65, "L'Hospitalet de Llobregat": 90,
    "Hospitalet de Llobregat": 90, "Vitoria-Gasteiz": 75, "Vitoria": 75,
    "A Coruña": 65, "La Coruña": 65, "Granada": 65, "Elche": 55, "Elx": 55,
    "Oviedo": 70, "Santa Cruz de Tenerife": 65, "Badalona": 88,
    "Cartagena": 50, "Terrassa": 75, "Jerez de la Frontera": 50,
    "Sabadell": 78, "Móstoles": 80, "Alcalá de Henares": 75,
    "Pamplona": 70, "Iruña": 70, "Fuenlabrada": 78, "Almería": 55,
    "Leganés": 80, "San Sebastián": 75, "Donostia": 75,
    "Donostia-San Sebastián": 75, "Getafe": 80, "Burgos": 60,
    "Santander": 65, "Castelló de la Plana": 60, "Castellón": 60,
    "Castellón de la Plana": 60, "Albacete": 55, "Alcorcón": 80,
    "Logroño": 60, "Badajoz": 55, "Salamanca": 60, "Huelva": 55,
    "Marbella": 55, "Lleida": 60, "Tarragona": 65, "Léon": 60, "León": 60,
    "Cádiz": 60, "Dos Hermanas": 55, "Mataró": 75, "Torrejón de Ardoz": 75,
    "Parla": 75, "Algeciras": 50, "Alcobendas": 80, "Reus": 60,
    "Ourense": 55, "Telde": 50, "Barakaldo": 80, "Lugo": 55,
    "Santiago de Compostela": 65, "Cáceres": 55, "Girona": 65, "Gerona": 65,
    "Lorca": 45, "Cornellà de Llobregat": 85, "Las Rozas": 70,
    "San Cristóbal de La Laguna": 55, "La Laguna": 55,
    "Coslada": 80, "Talavera de la Reina": 50, "El Ejido": 45,
    "Toledo": 60, "Pozuelo de Alarcón": 75, "Sant Cugat del Vallès": 75,
    "Sant Boi de Llobregat": 75, "Pontevedra": 60, "Guadalajara": 60,
    "Roquetas de Mar": 45, "Ávila": 55, "Mérida": 55, "Cuenca": 50,
    "Zamora": 50, "Soria": 50, "Segovia": 55, "Palencia": 55, "Huesca": 55,
    "Teruel": 50, "Ceuta": 60, "Melilla": 60, "Ferrol": 55,
    "Sant Adrià de Besòs": 85, "Esplugues de Llobregat": 85,
    "Gavà": 75, "Castelldefels": 70, "Viladecans": 75,
    "Manresa": 60, "Vic": 55, "Figueres": 55,
    "Benidorm": 60, "Torrevieja": 50, "Orihuela": 45,
    "Estepona": 50, "Fuengirola": 55, "Mijas": 50, "Vélez-Málaga": 50,
    "Torremolinos": 55, "Sanlúcar de Barrameda": 50, "El Puerto de Santa María": 55,
    "Chiclana de la Frontera": 50, "San Fernando": 55, "La Línea de la Concepción": 50,
    "Utrera": 45, "Mairena del Aljarafe": 55, "Alcalá de Guadaíra": 55,
    "Vilanova i la Geltrú": 60, "Vilafranca del Penedès": 55,
    "Granollers": 65, "Mollet del Vallès": 70, "Rubí": 70,
    "Sant Feliu de Llobregat": 75, "Cerdanyola del Vallès": 75,
    "Mejorada del Campo": 65, "Rivas-Vaciamadrid": 75,
    "San Sebastián de los Reyes": 75, "Tres Cantos": 72,
    "Majadahonda": 72, "Boadilla del Monte": 70, "Collado Villalba": 65,
    "Aranjuez": 60, "Arganda del Rey": 65,
    "Eivissa": 60, "Ibiza": 60, "Maó": 55, "Mahón": 55,
    "Manacor": 50, "Inca": 50, "Calvià": 55,
    "Arrecife": 50, "Adeje": 50, "Arona": 50,
    "Pucol": 50, "Sagunto": 55, "Sagunt": 55, "Paterna": 65,
    "Torrent": 60, "Mislata": 70, "Burjassot": 65, "Gandia": 55,
    "Alzira": 50, "Xàtiva": 50, "Játiva": 50, "Vinaròs": 50,
    "Benicarló": 50, "Elda": 50, "Petrer": 50, "Villena": 45,
    "Alcoy": 50, "Alcoi": 50, "Dénia": 50, "Calp": 50, "Calpe": 50,
    "Xàbia": 50, "Javea": 50, "Santa Pola": 50, "Crevillent": 45,
    "San Vicente del Raspeig": 60, "Sant Vicent del Raspeig": 60,
}


def coverage_label(pct: float) -> str:
    if pct >= 85:
        return "excellente"
    if pct >= 65:
        return "bonne"
    if pct >= 45:
        return "moyenne"
    if pct >= 25:
        return "médiocre"
    return "très faible"


def coverage_label_es(pct: float) -> str:
    if pct >= 85:
        return "excelente"
    if pct >= 65:
        return "buena"
    if pct >= 45:
        return "media"
    if pct >= 25:
        return "deficiente"
    return "muy baja"
