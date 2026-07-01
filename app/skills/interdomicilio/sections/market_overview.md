# Section : Vue d'ensemble du marché

## Données disponibles

- `metrics` : métriques de marché — chercher par metric_id :
  - `market_size_estimate` : taille du marché local (€/an)
  - `potential_clients_count` : nombre de clients potentiels
  - `competition_density` : densité concurrentielle (acteurs/km²)
  - `avg_basket_size` ou `monthly_revenue_per_client` : panier moyen
  - `market_growth_rate` : taux de croissance annuel
- `market_sizing` : {annual_revenue_estimate, total_addressable_population}
- `competitors_total_count` : nombre d'acteurs identifiés

## Layout attendu

1. **Ligne de 4 KPI cards** (métriques marché clés) :
   - CA marché estimé — icône `fa-chart-line`
   - Clients potentiels — icône `fa-users`
   - Acteurs en place — icône `fa-store`
   - Panier moyen — icône `fa-euro-sign`
   - "n.d." si métrique absente

2. **Encart synthèse marché** (style strategic-box étendu) :
   - 3 phrases sur la taille et le dynamisme du marché
   - Citer CA estimé, nombre de clients potentiels, densité concurrentielle
   - Icône `fa-globe`, couleur primaire

3. **Barre de jauge** (si `competition_density` présent) :
   - Label : "Densité concurrentielle"
   - Barre CSS (pas Chart.js) : width proportionnelle à la valeur (max = 5 acteurs/km²)
   - Couleurs : <1 = vert, 1-3 = orange, >3 = rouge

## Règles

- N'afficher que les métriques effectivement présentes
- Ne jamais inventer de valeurs de marché
- Classes : `kpi-row`, `kpi-card`, `strategic-box`, `section-accent-bar`
