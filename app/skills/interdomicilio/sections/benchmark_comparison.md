# Section : Comparaison benchmark national

## Données disponibles

`benchmark_rows` (liste pré-calculée par slide_precompute.py) :
- `label` : libellé de la métrique
- `local` : valeur locale (string, déjà formatée)
- `national` : valeur nationale (string, déjà formatée)
- `unit` : unité (%, h/semaine, €/heure, etc.)
- `gap_display` : écart pré-calculé ex. "+12.3%" ou "-5.1%" ou "n.d."
- `direction` : "up" | "down" | "neutral"
- `interpretation` : phrase d'interprétation (peut être vide)

**RÈGLE ABSOLUE** : recopier `gap_display` verbatim. Ne jamais recalculer.

## Layout attendu

1. **Titre de section** : "Positionnement vs. marché national"

2. **Tableau de benchmark** (`comp-table`) :
   - En-tête 4 colonnes : Indicateur | Local | National | Écart
   - Colonne Écart :
     - direction "up" : texte vert `#16A34A` + icône `fa-arrow-trend-up`
     - direction "down" : texte rouge `#EA580C` + icône `fa-arrow-trend-down`
     - direction "neutral" : texte gris + icône `fa-minus`
   - Lignes alternées blanc / `#F0F9FF`
   - Valeur locale en **gras**
   - Si `gap_display` = "n.d." : cellule grisée, icône `fa-minus`

3. **Strategic box** (en bas) :
   - 2 phrases synthétisant les points forts et faibles vs. national
   - Citer le nombre de métriques supérieures et inférieures au national
   - Icône `fa-chart-bar`, couleur primaire `#0095D9`

## Règles

- Si `benchmark_rows` est vide ou null : afficher un message "Données benchmark non disponibles" dans la strategic box
- Ne JAMAIS recalculer les écarts — `gap_display` est la source de vérité
- Limiter à 8 lignes max dans le tableau
- Pas de Chart.js sur cette slide (tableau pur HTML)
- Utiliser classes : `comp-table`, `strategic-box`, `strat-icon`, `section-accent-bar`
