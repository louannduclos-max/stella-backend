# Section : Vue d'ensemble du marché

## Données disponibles (clés RÉELLES — ne rien chercher d'autre)

- `metrics` : objet `{count, items, by_id}` — chercher par `metric_id` exact dans `by_id` :
  - `population_total` (habitants)
  - `seniors_60_plus_share` (%) et `seniors_75_plus_share` (%)
  - `single_senior_households` (ménages)
  - `avg_hourly_price_care` (€/h — prix horaire moyen du marché)
- `market_sizing` : `{seniors_75_plus, estimated_dependent,
  addressable_private_market, hypotheses, disclaimer}` ou null
- `competitors_total_count` : nombre d'acteurs identifiés (int)

## Règles ABSOLUES anti-invention

- **AUCUN calcul** : pas de CA de marché, pas de panier moyen, pas de taux de
  croissance — ces valeurs n'existent pas dans les données. Ne pas afficher de
  card "CA marché".
- N'afficher que des valeurs littéralement présentes. Absent → "n.d.".

## Layout attendu

1. **Ligne de 4 KPI cards** :
   - `population_total` + label "Population de la zone" — icône `fa-city`
   - `market_sizing.addressable_private_market` + label "Clients privés potentiels"
     — icône `fa-users` (si market_sizing null → `single_senior_households` +
     label "Ménages seniors seuls")
   - `competitors_total_count` + label "Acteurs en place" — icône `fa-store`
   - `avg_hourly_price_care` + "€/h" + label "Prix horaire moyen" — icône `fa-euro-sign`

2. **Encart synthèse marché** (strategic-box étendue) :
   - PLEINE LARGEUR obligatoire : `display:block; width:100%` — ne JAMAIS placer
     cet encart dans une colonne flex étroite (bug constaté : texte rendu
     verticalement, un mot par ligne)
   - 3 phrases sur la taille et la structure du marché, en citant UNIQUEMENT
     des valeurs affichées dans les cards ci-dessus
   - Icône `fa-globe`, couleur primaire

3. **Ligne hypothèses** (si `market_sizing` affiché) : recopier le `disclaimer`
   en petit texte muted sous l'encart.

## Classes

`kpi-row`, `kpi-card`, `strategic-box`, `section-accent-bar`
