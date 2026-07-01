# Section : Analyse géographique

## Données disponibles

- `metrics` : objet `{count, items, by_id}` — chercher UNIQUEMENT par `metric_id` exact
  dans `items` (ou `by_id`) :
  - `density_population` : densité de population (hab/km²)
  - `travel_time_spread` : amplitude des temps de trajet dans la zone (min)
  - `transit_lines_count` : nombre de lignes de transport en commun
  - `neighborhood_count` : nombre de quartiers identifiés
- `microzones` : objet `{neighborhoods, streets, traffic_axes, transit_lines}` OU `null`.
  - `neighborhoods` : liste de `{name, population, seniors_60_plus_share, median_income,
    premium_flag, confidence_grade}`
  - `transit_lines` : liste de `{name, mode, frequency_peak}`

## Règles ABSOLUES anti-invention

- **INTERDICTION ABSOLUE** d'inventer ou d'estimer des valeurs numériques.
- N'utiliser QUE les valeurs littéralement présentes dans le JSON fourni.
- Si un `metric_id` listé ci-dessus n'est pas dans les metrics : afficher `n.d.`
  (ne pas calculer, ne pas estimer, ne pas remplacer par une autre métrique).
- Si `microzones` est `null` ou absent, OU si `microzones.neighborhoods` est vide :
  **NE PAS générer de tableau de quartiers**. Afficher à la place une `strategic-box`
  avec le texte "Données de découpage géographique non disponibles pour cette zone."
- Recopier les nombres tels quels (population, part 60+, revenu) — jamais de
  moyenne, somme ou pourcentage recalculé.

## Layout attendu

1. **Ligne de 3 KPI cards** (valeurs issues UNIQUEMENT des metrics) :
   - Densité population — icône `fa-people-group` — valeur `density_population` + "hab/km²" ou `n.d.`
   - Amplitude trajets — icône `fa-route` — valeur `travel_time_spread` + "min" ou `n.d.`
   - Lignes TC — icône `fa-train-tram` — valeur `transit_lines_count` ou `n.d.`

2. **Tableau des quartiers** UNIQUEMENT si `microzones.neighborhoods` non vide :
   - Titre : "Découpage par quartier"
   - Colonnes : Quartier | Population | Part 60+ | Profil
   - Colonne Profil : badge "Premium" (fond accent) si `premium_flag` true, sinon "Standard" (gris)
   - Max 6 quartiers, ordre du JSON
   - Sous le tableau, une ligne en petit texte muted si les quartiers ont
     `confidence_grade` "C" : "Sous-zones estimées (baseline INSEE + multiplicateurs) — grade C"

3. **Strategic box** synthèse finale :
   - 2 phrases sur les enjeux géographiques pour le déploiement (couverture, temps de
     trajet, desserte TC), sans citer de chiffre absent des données
   - Icône `fa-map-location-dot`

## Classes CSS

`kpi-row`, `kpi-card`, `kpi-icon`, `kpi-value`, `kpi-label`, `comp-table`, `strategic-box`, `strat-icon`, `section-accent-bar`
