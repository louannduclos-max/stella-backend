# Section : Profil démographique <!-- v2 : tokens 4096 + Chart.js -->

## Données disponibles

- `demographics_pie` : {"labels": ["60 ans et +", "Moins de 60 ans"], "values": [X, 100-X]}
  - Valeurs pré-calculées — recopier sans recalculer
- `metrics` : objet `{count, items, by_id}` — chercher par `metric_id` EXACT dans `by_id` :
  - `population_total` : population de la zone (habitants)
  - `seniors_60_plus_share` : part des 60 ans et + (%)
  - `seniors_75_plus_share` : part des 75 ans et + (%)
  - `single_senior_households` : ménages seniors vivant seuls (ménages)
  - `dependency_ratio_apa` : taux de dépendance APA
  - `population_growth_5y` : croissance de population sur 5 ans (%)

**RÈGLE** : ces metric_id sont les SEULS valides pour cette section. Un id absent
du JSON → ne pas afficher la card (jamais de valeur voisine ni d'id inventé,
il n'existe PAS de `median_age` dans les données).

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
