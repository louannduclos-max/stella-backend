# Section : Résumé exécutif

## Données disponibles

- `score_composite` : float (score global 0-100, peut être null)
- `verdict` : "GO" | "GO_CONDITIONALLY" | "NO_GO" | null
- `metrics` : liste de métriques — utiliser les 4 à 6 plus importantes :
  - Chercher : `market_size_estimate`, `potential_clients_count`, `competition_density`, `median_income`, `population_totale`, `taux_dependance`
- `market_sizing` : {annual_revenue_estimate, total_addressable_population, apa_eligible_count} ou null
- `funding_scale` : {apa_coverage_rate, monthly_apa_amount_avg, ...} ou null

## Layout attendu

1. **Bandeau verdict** (pleine largeur, en haut) :
   - "GO" → fond vert `#16A34A`, icône `fa-circle-check`
   - "GO_CONDITIONALLY" → fond orange `#EA580C`, icône `fa-triangle-exclamation`
   - "NO_GO" → fond rouge `#DC2626`, icône `fa-circle-xmark`
   - null → fond gris, "Verdict en cours d'analyse"
   - Score composite à droite du bandeau : grand chiffre blanc + "/100"

2. **Ligne de 4 KPI cards** (métriques clés) :
   - Choisir 4 métriques présentes dans `metrics` (les plus pertinentes)
   - Format : valeur (`kpi-value`) + label (`kpi-label`) + icône (`kpi-icon`)
   - Si `market_sizing` présent : inclure le CA annuel estimé comme 1ère card
   - Icônes suggérées : `fa-users`, `fa-euro-sign`, `fa-house`, `fa-chart-line`

3. **Strategic box** (en bas) :
   - 2-3 phrases de synthèse sur la faisabilité globale
   - Mentionner le verdict et le score composite
   - Icône `fa-bullseye`, couleur primaire

## Règles

- Afficher uniquement les métriques effectivement présentes (ne pas inventer)
- Si `score_composite` null : ne pas afficher le score, juste le verdict
- Si `verdict` null : bandeau gris neutre
- Classes : `kpi-row`, `kpi-card`, `strategic-box`, `section-accent-bar`
