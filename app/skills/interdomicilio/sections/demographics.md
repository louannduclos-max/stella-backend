# Section : Profil démographique

## Données disponibles

- `demographics_pie` : {"labels": ["60 ans et +", "Moins de 60 ans"], "values": [X, 100-X]}
  - Valeurs pré-calculées — recopier sans recalculer
- `metrics` : liste complète des métriques (filtrer par metric_id pour cette section)
  - `population_totale` ou `total_population` : population de la zone
  - `seniors_60_plus_share` : part des 60 ans et + (%)
  - `dependency_ratio` ou `taux_dependance` : taux de dépendance
  - `median_age` ou `age_median` : âge médian
  - `avg_household_size` : taille moyenne des ménages
  - `lone_elderly_share` : part des personnes âgées vivant seules

**RÈGLE** : N'afficher que les métriques effectivement présentes dans le manifest.

## Layout attendu

1. **Ligne de 2 colonnes** :

   **Colonne gauche (60% largeur)** — Graphique camembert :
   - Canvas Chart.js `type: 'doughnut'`
   - Données : `demographics_pie.values`, labels : `demographics_pie.labels`
   - Couleurs : `["#0095D9", "#E6F4FB"]` (bleu primaire / bleu clair)
   - Options : `cutout: '65%'`, légende en bas, tooltip avec "%"
   - Titre centré sous le canvas : "Répartition par âge"
   - Centre du donut : valeur `demographics_pie.values[0]`% en grand + "60 ans et +"

   **Colonne droite (40% largeur)** — KPI cards verticales :
   - 3 à 4 métriques démographiques clés (kpi-card empilées)
   - Icônes : `fa-users` population, `fa-person-cane` seniors, `fa-house-chimney-user` ménages, `fa-calendar` âge médian
   - Format : valeur en grand (`kpi-value`), label en dessous (`kpi-label`)

2. **Strategic box** (pleine largeur en bas) :
   - 2 phrases sur l'attractivité démographique pour les services SAP
   - Citer obligatoirement la part des 60+ et la population totale
   - Icône `fa-chart-pie`, couleur primaire

## Règles

- Si `demographics_pie` est null : afficher un placeholder "Données démographiques non disponibles" à la place du graphique
- Utiliser l'ID canvas unique `demoChart` pour Chart.js
- Script Chart.js dans un `<script>` après le `<main>` — autorisé ici (graphique)
- Classes : `kpi-row`, `kpi-card`, `strategic-box`, `section-accent-bar`
