# Section : Immobilier (prix m² / loyer)

Le marché immobilier comme proxy de solvabilité et de valeur patrimoniale des
clients (un patrimoine élevé = capacité à financer le maintien à domicile).

## Données disponibles (clés RÉELLES — chercher par metric_id dans `metrics.by_id`)

- `real_estate_price_house_m2` : prix maisons (EUR/m²)
- `real_estate_price_apartment_m2` : prix appartements (EUR/m²)
- `rental_price_m2` : loyer moyen (EUR/m²/mois)
- `real_estate_avg_transaction` : transaction moyenne (EUR)
- `real_estate_price_growth_5y` : croissance des prix sur 5 ans (%)
- `real_estate_premium_zone_share` : part de zones premium (%)
- `houses_vs_apartments_share` : part de maisons vs appartements (%)
- `avg_house_surface` : surface moyenne maison (m²)

## Règles ABSOLUES anti-invention

- Ces metric_id sont les SEULS valides. Absent → "n.d.".
- La plupart de ces métriques sont grade "C"/"D" (baselines) → badge
  `<span class="badge-estimation">estimation</span>` (classe du template)
  OBLIGATOIRE sur chaque card concernée. C'est le différenciateur honnêteté de Stella.
- Aucun calcul (pas de rendement locatif, pas de prix moyen combiné).

## Layout attendu

1. **Ligne de 4 KPI cards "Prix"** :
   - `real_estate_price_house_m2` + "€/m²" + "Maisons" — `fa-house`
   - `real_estate_price_apartment_m2` + "€/m²" + "Appartements" — `fa-building`
   - `rental_price_m2` + "€/m²/mois" + "Loyer moyen" — `fa-key`
   - `real_estate_avg_transaction` + "€" + "Transaction moyenne" — `fa-file-signature`

2. **Ligne de 3 indicateurs de structure** (cards plus petites) :
   - `real_estate_price_growth_5y` + "%" + "Croissance 5 ans" — `fa-arrow-trend-up`
     (texte vert si positif)
   - `real_estate_premium_zone_share` + "%" + "Zones premium" — `fa-gem`
   - `houses_vs_apartments_share` + "%" + "Part de maisons" — `fa-house-chimney`

3. **Strategic box** (bas) :
   - 2 phrases sur ce que le marché immobilier local implique pour le
     positionnement de l'agence (patrimoine des seniors, quartiers cibles),
     en citant uniquement des valeurs affichées
   - Icône `fa-house-circle-check`

## Règles

- Pas de Chart.js
- Classes : `kpi-row`, `kpi-card`, `kpi-icon`, `kpi-value`, `kpi-label`,
  `strategic-box`, `strat-icon`, `section-accent-bar`
