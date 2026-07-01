# Section : Quartiers, rues & routes

Le découpage opérationnel de la zone : où s'implanter, où intervenir, comment
circuler.

## Données disponibles (clés RÉELLES)

- `microzones` : objet OU `null` :
  - `neighborhoods` : liste de `{name, population, seniors_60_plus_share,
    median_income, premium_flag, premium_score, confidence_grade}`
  - `streets` : liste de `{name, street_type, priority, target_segment}`
  - `transit_lines` : liste de `{name, mode, frequency_peak}`
  - `traffic_axes` : liste de `{name, axis_type, rush_hour_penalty_min}`
- `metrics.by_id` : `neighborhood_count`, `premium_neighborhoods_count`,
  `transit_lines_count`, `travel_time_spread`

## Règles ABSOLUES anti-invention

- Si `microzones` null ou `neighborhoods` vide : strategic-box
  "Données de découpage géographique non disponibles pour cette zone." et RIEN d'autre.
- Recopier population / part 60+ / revenus tels quels. Aucun total recalculé.
- Les quartiers sont souvent grade "C" (estimés par baseline) : afficher la
  mention "Sous-zones estimées (baseline INSEE + multiplicateurs) — grade C"
  en petit texte muted sous le tableau.

## Layout attendu

1. **Ligne de 3 KPI cards** :
   - `neighborhood_count` + "Quartiers identifiés" — `fa-map`
   - `premium_neighborhoods_count` + "Quartiers premium" — `fa-gem`
   - `travel_time_spread` + "min" + "Amplitude de trajet" — `fa-route`

2. **Tableau des quartiers** (`comp-table`, max 6 lignes) :
   - Colonnes : Quartier | Population | Part 60+ | Revenu médian | Profil
   - Profil : badge "Premium" (fond accent `#FFCC00`, texte `#1F2937`) si
     `premium_flag` true, sinon "Standard" (gris)
   - Trier : premium d'abord (ordre du JSON sinon)

3. **Bandeau mobilité** (flex, 2 groupes côte à côte) :
   - Groupe "Transports" : une chip par ligne de `transit_lines` (max 6) :
     icône selon `mode` (`fa-train-subway` metro, `fa-bus` bus, `fa-train-tram`
     tram) + `name` + `frequency_peak`
   - Groupe "Axes routiers" : une chip par axe de `traffic_axes` (max 3) :
     `fa-road` + `name` + "+{rush_hour_penalty_min} min en pointe"

4. **Strategic box** (bas) :
   - 2 phrases : quartiers à prioriser pour l'implantation et implications
     mobilité pour les tournées d'intervenants — chiffres affichés uniquement
   - Icône `fa-map-location-dot`

## Règles

- Pas de Chart.js
- Classes : `kpi-row`, `kpi-card`, `comp-table`, `strategic-box`, `strat-icon`,
  `section-accent-bar`
