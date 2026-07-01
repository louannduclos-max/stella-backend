# Section : Résumé exécutif

## Données disponibles (clés RÉELLES — ne rien chercher d'autre)

- `score_composite` : float (score global 0-100, peut être null)
- `verdict` : "GO" | "GO_CONDITIONAL" | "NO_GO" | null
- `metrics` : objet `{count, items, by_id}` — chercher par `metric_id` exact dans `by_id` :
  - `population_total` (habitants), `seniors_75_plus_share` (%), `median_income` (EUR/an),
    `competitor_count_15min` (acteurs), `care_worker_pool`, `unemployment_rate` (%)
- `market_sizing` : `{seniors_75_plus, estimated_dependent, addressable_private_market,
  hypotheses, disclaimer}` ou null
  - `addressable_private_market` = nombre de clients privés potentiels (PAS un CA)
- `funding_scale` : `{type, source, year, scale_rows, participation}` ou null
  (barème APA — ne pas l'utiliser pour les KPI cards, il sert à la slide financement)
- `narratives.exec_summary` : paragraphe de synthèse pré-rédigé (peut être utilisé
  comme base de la strategic box)

## Règles ABSOLUES anti-invention

- **INTERDICTION ABSOLUE de calculer** : pas de CA estimé, pas de multiplication
  clients × prix, pas de moyenne de barème, pas de reste à charge. Aucune arithmétique.
- Afficher UNIQUEMENT des valeurs littéralement présentes dans le JSON.
- Une clé listée ci-dessus absente ou null → ne pas afficher la card correspondante.
- Ne jamais reformuler un nombre (pas d'arrondi, pas de "environ 270 000").

## Layout attendu

1. **Bandeau verdict** (OBLIGATOIRE, pleine largeur, PREMIER élément du main) —
   utiliser EXACTEMENT ce motif :
   ```html
   <div style="display:flex;align-items:center;justify-content:space-between;
               background:#DC2626;color:#fff;border-radius:8px;
               padding:12px 20px;margin-bottom:16px">
     <div style="font-weight:800;font-size:20px">
       <i class="fa-solid fa-circle-xmark"></i> NO GO
     </div>
     <div style="font-weight:800;font-size:26px">43.1<span style="font-size:13px">/100</span></div>
   </div>
   ```
   Adapter fond/icône/texte au verdict réel :
   - "GO" → fond `#16A34A`, `fa-circle-check`, texte "GO"
   - "GO_CONDITIONAL" → fond `#EA580C`, `fa-triangle-exclamation`, "GO CONDITIONNEL"
   - "NO_GO" → fond `#DC2626`, `fa-circle-xmark`, "NO GO"
   - null → fond `#6B7280`, "Verdict en cours d'analyse", sans score
   Le score affiché = `score_composite` réel (jamais 43.1 recopié de l'exemple
   si la valeur diffère).

2. **Ligne de 4 KPI cards** :
   - Card 1 : `market_sizing.addressable_private_market` + label "Clients privés potentiels"
     + icône `fa-users` (si market_sizing null → remplacer par `population_total`)
   - Card 2 : `seniors_75_plus_share` + "%" + label "Part des 75 ans et +" + `fa-person-cane`
   - Card 3 : `median_income` + "€/an" + label "Revenu médian" + `fa-euro-sign`
   - Card 4 : `competitor_count_15min` + label "Concurrents identifiés" + `fa-store`
   - Une valeur absente → "n.d." dans la card, jamais une valeur voisine.

3. **Strategic box** (en bas) :
   - 2-3 phrases de synthèse sur la faisabilité globale (base : `narratives.exec_summary`
     si présent). Mentionner le verdict et le score composite. Aucun chiffre nouveau.
   - Icône `fa-bullseye`, couleur primaire

## Classes

`kpi-row`, `kpi-card`, `kpi-icon`, `kpi-value`, `kpi-label`, `strategic-box`, `section-accent-bar`
