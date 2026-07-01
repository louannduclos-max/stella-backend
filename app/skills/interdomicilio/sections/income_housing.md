# Section : Économie, revenus & habitat

Solvabilité des ménages + structure de l'habitat = capacité à payer des
prestations à domicile et facilité d'intervention.

## Données disponibles (clés RÉELLES — chercher par metric_id dans `metrics.by_id`)

Revenus / solvabilité :
- `median_income` : revenu médian (EUR/an)
- `avg_hourly_price_care` : prix horaire moyen du marché care (EUR/h)
- `taxable_households_share` : part de ménages imposables (%)

Habitat :
- `home_ownership_share` : part de propriétaires (%)
- `tenants_share` : part de locataires (%)
- `real_estate_price_house_m2` : prix maisons (EUR/m²)
- `real_estate_price_apartment_m2` : prix appartements (EUR/m²)
- `rental_price_m2` : loyer moyen (EUR/m²/mois)

Chaque métrique porte `confidence_grade` et `fallback_used`.

## Règles ABSOLUES anti-invention

- Ces metric_id sont les SEULS valides. Absent → "n.d.".
- **Badge "estimation"** (fond `#FFF7ED`, texte `#EA580C`, 10px) sur toute card
  dont la métrique a `fallback_used` true ou grade "C"/"D".
- Aucun calcul (pas de budget mensuel, pas de pouvoir d'achat dérivé).

## Layout attendu

1. **Ligne de 3 KPI cards "Solvabilité"** :
   - `median_income` + "€/an" + "Revenu médian" — `fa-euro-sign`
   - `taxable_households_share` + "%" + "Ménages imposables" — `fa-receipt`
   - `avg_hourly_price_care` + "€/h" + "Prix horaire marché" — `fa-clock`

2. **Bloc habitat en 2 colonnes** :
   - Colonne gauche — "Occupation" : 2 barres horizontales CSS pures (pas de
     Chart.js) : Propriétaires `home_ownership_share`% (fond primary) et
     Locataires `tenants_share`% (fond primary_dark), largeur = valeur en %,
     étiquette valeur au bout de la barre
   - Colonne droite — "Marché immobilier" : 3 lignes libellé/valeur :
     Maisons `real_estate_price_house_m2` €/m² · Appartements
     `real_estate_price_apartment_m2` €/m² · Loyer `rental_price_m2` €/m²/mois

3. **Strategic box** (bas) :
   - 2 phrases sur la solvabilité locale pour des services à la personne,
     citant `median_income` (et son positionnement si évident, sans le calculer)
   - Icône `fa-house-circle-check`

## Règles

- Pas de Chart.js (barres CSS uniquement)
- Classes : `kpi-row`, `kpi-card`, `kpi-icon`, `kpi-value`, `kpi-label`,
  `strategic-box`, `strat-icon`, `section-accent-bar`
