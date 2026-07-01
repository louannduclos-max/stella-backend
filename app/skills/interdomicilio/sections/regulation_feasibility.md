# Section : Réglementation & faisabilité

Le cadre réglementaire SAP/SAAD et les conditions économiques d'entrée.

## Données disponibles (clés RÉELLES — chercher par metric_id dans `metrics.by_id`)

Cadre réglementaire :
- `saad_authorization_required` : autorisation SAAD requise (bool ou flag)
- `regulatory_barrier_level` : niveau de barrière réglementaire (indice)
- `regulated_saad_rate` : tarif SAAD réglementé (EUR/h)
- `avg_hourly_price_care` : prix horaire moyen du marché libre (EUR/h)
- `public_aid_coverage` : couverture des aides publiques (indice ou %)
- `apa_hourly_rate` : tarif horaire APA (EUR/h)

Conditions d'entrée :
- `estimated_initial_investment` : investissement initial estimé (EUR)
- `estimated_monthly_fixed_costs` : coûts fixes mensuels estimés (EUR)
- `franchise_entry_fee` : droit d'entrée franchise (EUR)

`funding_scale.type/year/source` : référence du barème (pour la mention de bas de slide)

## Règles ABSOLUES anti-invention

- Ces clés sont les SEULES valides. Absent → "n.d.".
- Badge estimation : `<span class="badge-estimation">estimation</span>`
  (classe du template) si `fallback_used` true ou grade "C"/"D".
- NE PAS calculer d'écart tarif réglementé vs marché — afficher les deux valeurs
  côte à côte, le lecteur voit l'écart.
- Ne pas qualifier juridiquement ("légal/illégal") — rester factuel.

## Layout attendu

1. **Bloc "Cadre réglementaire"** (2 colonnes) :
   - Colonne gauche — carte statut : icône `fa-scale-balanced` + titre
     "Régime SAAD" + ligne "Autorisation requise : {saad_authorization_required
     → Oui/Non/n.d.}" + ligne "Barrière réglementaire : {regulatory_barrier_level}"
   - Colonne droite — carte tarifs (3 lignes libellé/valeur) :
     "Tarif SAAD réglementé : {regulated_saad_rate} €/h" ·
     "Prix marché libre : {avg_hourly_price_care} €/h" ·
     "Tarif horaire APA : {apa_hourly_rate} €/h"

2. **Ligne de 3 KPI cards "Conditions d'entrée"** :
   - `estimated_initial_investment` + "€" + "Investissement initial" — `fa-coins`
   - `franchise_entry_fee` + "€" + "Droit d'entrée franchise" — `fa-handshake`
   - `estimated_monthly_fixed_costs` + "€/mois" + "Coûts fixes" — `fa-file-invoice`

3. **Strategic box** (bas) :
   - 2 phrases sur la faisabilité réglementaire et l'effort d'entrée, chiffres
     affichés uniquement
   - Icône `fa-clipboard-check`
   - Dessous, petit texte muted : "Barème {funding_scale.type} {funding_scale.year}
     — source {funding_scale.source}" (si funding_scale présent)

## Règles

- Pas de Chart.js
- Classes : `kpi-row`, `kpi-card`, `comp-table`, `strategic-box`, `strat-icon`,
  `section-accent-bar`
