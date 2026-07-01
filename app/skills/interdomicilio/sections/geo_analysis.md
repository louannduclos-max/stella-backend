# Section : Analyse géographique

## Données disponibles

- `metrics` : tableau de métriques — chercher UNIQUEMENT par `metric_id` exact :
  - `zone_area_km2` : superficie de la zone (km²)
  - `population_density` : densité de population (hab/km²)
  - `mobility_index` : indice de mobilité
  - `coverage_radius_km` : rayon de couverture opérationnel
- `microzones` : objet `{count, items: [{name, population, priority}]}` OU `null`

## Règles ABSOLUES anti-invention

- **INTERDICTION ABSOLUE** d'inventer ou d'estimer des valeurs numériques.
- N'utiliser QUE les valeurs littéralement présentes dans le JSON fourni.
- Si `zone_area_km2` n'est pas dans les metrics : afficher `n.d.` (ne pas calculer, ne pas estimer).
- Si `population_density` n'est pas dans les metrics : afficher `n.d.`.
- Si `microzones` est `null` ou absent : **NE PAS générer de tableau de microzones**. Afficher à la place une `strategic-box` avec le texte "Données de découpage géographique non disponibles pour cette zone."
- Si `microzones.items` est vide : idem, ne pas générer de tableau.
- Dans la `strategic-box` finale : ne citer superficie et densité QUE si ces valeurs sont présentes dans les metrics. Sinon, parler des enjeux géographiques en termes généraux sans inventer de chiffres.

## Layout attendu

1. **Ligne de 3 KPI cards** (valeurs issues UNIQUEMENT des metrics) :
   - Superficie de la zone — icône `fa-map` — valeur `zone_area_km2` ou `n.d.`
   - Densité population — icône `fa-people-group` — valeur `population_density` ou `n.d.`
   - Rayon de couverture — icône `fa-location-dot` — valeur `coverage_radius_km` ou `n.d.`

2. **Tableau des microzones** UNIQUEMENT si `microzones` est non-null ET `microzones.items` non vide :
   - Titre : "Découpage par microzone"
   - Colonnes : Zone | Population | Priorité
   - Badge priorité : high=rouge, medium=orange, low=gris
   - Max 8 microzones

3. **Strategic box** si microzones null :
   - "Données de découpage géographique non disponibles pour cette zone."
   - Icône `fa-map-location-dot`

4. **Strategic box** synthèse finale :
   - 2 phrases sur les enjeux géographiques pour le déploiement (sans inventer de chiffres si absents)
   - Icône `fa-map-location-dot`

## Classes CSS

`kpi-row`, `kpi-card`, `kpi-icon`, `kpi-value`, `kpi-label`, `comp-table`, `strategic-box`, `strat-icon`, `section-accent-bar`
