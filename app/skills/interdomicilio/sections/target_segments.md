# Section : Seniors & segments cibles

Qui sont les clients potentiels de l'agence, segment par segment.

## Données disponibles (clés RÉELLES — chercher par metric_id dans `metrics.by_id`)

- `seniors_60_plus_share` : part des 60 ans et + (%)
- `seniors_75_plus_share` : part des 75 ans et + (%)
- `single_senior_households` : ménages seniors vivant seuls (ménages)
- `dependency_ratio_apa` : personnes en situation de dépendance APA (personnes)
- `households_with_children_share` : ménages avec enfants (%)
- `premium_customer_potential` : potentiel clientèle premium (indice ou %)
- `market_sizing` : `{seniors_75_plus, estimated_dependent,
  addressable_private_market, disclaimer}` ou null

## Règles ABSOLUES anti-invention

- Ces clés sont les SEULES valides. Absent → "n.d.".
- Badge "estimation" (fond `#FFF7ED`, texte `#EA580C`, 10px) si `fallback_used`
  true ou grade "C"/"D" sur la métrique.
- Aucun calcul de taille de segment (pas de % × population).

## Layout attendu

1. **3 cartes segment** (flex, gap 16px, hauteur égale) :

   **Carte "Seniors en autonomie"** (bordure haute 4px primary `#0095D9`) :
   - Icône `fa-person-walking` dans un `icon-circle`
   - Chiffres : `seniors_60_plus_share`% de 60+ · `single_senior_households`
     ménages seniors seuls
   - Ligne besoin : "Ménage, courses, compagnie" (offre métier, pas une donnée)

   **Carte "Seniors en dépendance"** (bordure haute 4px `#00608A`) :
   - Icône `fa-hand-holding-heart`
   - Chiffres : `seniors_75_plus_share`% de 75+ · `dependency_ratio_apa`
     personnes en dépendance APA · si `market_sizing` présent :
     `addressable_private_market` clients privés potentiels
   - Ligne besoin : "Aide à domicile, soins d'accompagnement, APA"

   **Carte "Familles & premium"** (bordure haute 4px accent `#FFCC00`) :
   - Icône `fa-people-roof`
   - Chiffres : `households_with_children_share`% ménages avec enfants ·
     `premium_customer_potential` (avec badge estimation si grade C/D)
   - Ligne besoin : "Garde d'enfants, ménage premium, jardinage"

2. **Strategic box** (bas) :
   - 2 phrases : quel segment prioriser au lancement et pourquoi, en citant
     uniquement des chiffres affichés dans les cartes
   - Icône `fa-bullseye`
   - Si `market_sizing` affiché : recopier son `disclaimer` en petit texte muted
     sous la box

## Règles

- Pas de Chart.js
- Classes : `kpi-card`, `icon-circle`, `strategic-box`, `strat-icon`, `section-accent-bar`
