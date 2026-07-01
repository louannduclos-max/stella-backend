# Section : Faisabilité financière et financement

## Données disponibles

`funding_scale` (peut être null) :
- `apa_coverage_rate` : taux de couverture APA (%)
- `monthly_apa_amount_avg` : montant moyen mensuel APA (€)
- `hourly_rate_ceiling` : plafond horaire APA (€/h)
- `client_copay_rate` : taux de participation client moyen (%)
- `thresholds` : [{label, gir, hours_per_month, monthly_amount}, ...] (barème GIR)
- `source_year` : année du barème

`market_sizing` (peut être null) :
- `total_addressable_population` : population éligible estimée
- `apa_eligible_count` : bénéficiaires APA estimés
- `annual_revenue_estimate` : CA annuel estimable (€)
- `monthly_revenue_estimate` : CA mensuel estimable (€)
- `methodology_note` : note méthodologique

## Layout attendu

1. **Ligne de 3 KPI cards** :
   - Taux de couverture APA (%) — icône `fa-shield-halved`
   - Montant mensuel APA moyen (€) — icône `fa-euro-sign`
   - CA annuel estimable (€) — icône `fa-chart-line`
   - Valeur "n.d." si champ absent

2. **Tableau barème APA** (si `funding_scale.thresholds` présent) :
   - Titre : "Barème APA — {source_year}"
   - Colonnes : GIR | Heures/mois | Montant mensuel
   - En-tête fond primaire `#0095D9`, texte blanc
   - 4 lignes max (GIR 1 à 4)

3. **Encart marché adressable** (si `market_sizing` présent) :
   - `total_addressable_population` personnes éligibles estimées
   - `apa_eligible_count` bénéficiaires APA probables
   - Note méthodologique en italique gris si `methodology_note` présent

4. **Strategic box** :
   - 2 phrases sur la viabilité financière
   - Citer le CA annuel estimable et le taux APA
   - Icône `fa-sack-dollar`

## Règles

- Si `funding_scale` null ET `market_sizing` null : afficher "Données financières non disponibles"
- Ne jamais calculer — toutes les valeurs viennent du manifest
- Classes : `kpi-row`, `kpi-card`, `comp-table`, `strategic-box`, `section-accent-bar`
