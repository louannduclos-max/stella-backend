# Section : Faisabilité financière et financement

## Données disponibles (clés RÉELLES — ne rien chercher d'autre)

`funding_scale` (peut être null) :
- `type` : type de barème (ex. "APA")
- `source` : source officielle (ex. "CNSA / DGCS")
- `year` : année du barème (int)
- `scale_rows` : liste de `{gir, label, apa_ceiling_eur_month, coverage_note}`
  (4 lignes GIR 1 → GIR 4)
- `participation` : `{no_participation_below_eur, max_participation_above_eur, note}`

`market_sizing` (peut être null) :
- `seniors_75_plus` : effectif des 75 ans et + (int)
- `estimated_dependent` : personnes en perte d'autonomie estimées (int)
- `addressable_private_market` : clients privés potentiels (int)
- `hypotheses` : `{dependency_rate_among_75plus, dependency_rate_source,
  private_sad_preference_rate, private_sad_preference_source}`
- `disclaimer` : phrase de mise en garde méthodologique

## Règles ABSOLUES anti-invention

- **AUCUN calcul** : pas de CA (ni annuel ni mensuel), pas de montant moyen,
  pas de reste à charge, pas de multiplication clients × prix. Ces valeurs
  n'existent pas dans les données → ne PAS les afficher du tout.
- Recopier les montants du barème au centime tel quel (2 080,33 — jamais arrondi).
- Si `funding_scale` null ET `market_sizing` null : "Données financières non
  disponibles pour ce pays."

## Layout attendu

1. **Ligne de 3 KPI cards** (uniquement depuis `market_sizing`, sinon "n.d.") :
   - `seniors_75_plus` + label "Seniors 75 ans et +" — icône `fa-person-cane`
   - `estimated_dependent` + label "En perte d'autonomie (est.)" — icône `fa-hand-holding-heart`
   - `addressable_private_market` + label "Clients privés potentiels" — icône `fa-users`

2. **Tableau barème** (si `funding_scale.scale_rows` présent) :
   - Titre : "Barème {type} — {year} ({source})"
   - Colonnes : GIR | Profil | Plafond mensuel
   - Lignes : recopier `gir`, `label`, `apa_ceiling_eur_month` formaté "X XXX,XX €"
   - En-tête fond primaire `#0095D9`, texte blanc

3. **Encart participation** (si `funding_scale.participation` présent) :
   - "0 % de participation sous {no_participation_below_eur} € de revenus mensuels ;
     90 % au-delà de {max_participation_above_eur} €" + la `note` en italique

4. **Ligne hypothèses** (petit texte muted, obligatoire si `market_sizing` affiché) :
   - Recopier `hypotheses.dependency_rate_source` et le `disclaimer` —
     la transparence des hypothèses fait partie du produit, ne jamais la masquer.

5. **Strategic box** :
   - 2 phrases sur la solvabilisation du marché par le barème (sans chiffre inventé)
   - Icône `fa-sack-dollar`

## Classes

`kpi-row`, `kpi-card`, `comp-table`, `strategic-box`, `section-accent-bar`
