# Section : Analyse géographique

## Données disponibles

- `metrics` : métriques géographiques — chercher :
  - `zone_area_km2` : superficie de la zone (km²)
  - `population_density` : densité de population (hab/km²)
  - `mobility_index` : indice de mobilité
  - `coverage_radius_km` : rayon de couverture opérationnel
- `microzones` : {count, items: [{name, population, priority}]} ou null
- Study `geo_scope` : city, department, region (dans les données de contexte)

## Layout attendu

1. **Ligne de 3 KPI cards** :
   - Superficie de la zone — icône `fa-map`
   - Densité population — icône `fa-people-group`
   - Rayon de couverture — icône `fa-location-dot`

2. **Tableau des microzones** (si `microzones` présent et non vide) :
   - Titre : "Découpage par microzone"
   - Colonnes : Zone | Population | Priorité
   - Badge priorité : high=rouge, medium=orange, low=gris
   - Max 8 microzones

3. **Strategic box** :
   - 2 phrases sur les enjeux géographiques pour le déploiement
   - Citer superficie et densité
   - Icône `fa-map-location-dot`

## Règles

- Si ni métriques géo ni microzones : afficher "Données géographiques non disponibles"
- Classes : `kpi-row`, `kpi-card`, `comp-table`, `strategic-box`, `section-accent-bar`
