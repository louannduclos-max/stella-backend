# Section : Verdict et recommandation

## Données disponibles

- `verdict` : "GO" | "GO_CONDITIONAL" | "NO_GO" | null
- `score_composite` : float 0-100 ou null
- `scores_radar` : {"labels": [...], "values": [...]} (pré-calculé)
  - labels : noms des dimensions d'analyse
  - values : scores arrondis (entiers 0-100)

**RÈGLE** : `scores_radar.values` sont pré-calculés — recopier sans arrondir ni recalculer.

## Layout attendu

1. **Bandeau verdict** (pleine largeur, hauteur réduite) :
   - "GO" → fond `#16A34A` + icône `fa-circle-check` + "Faisabilité confirmée"
   - "GO_CONDITIONAL" → fond `#EA580C` + icône `fa-triangle-exclamation` + "Faisabilité conditionnelle"
   - "NO_GO" → fond `#DC2626` + icône `fa-circle-xmark` + "Faisabilité insuffisante"

2. **Ligne 2 colonnes** :

   **Colonne gauche (50%)** — Radar Chart.js :
   - `type: 'radar'`
   - `data.labels` : `scores_radar.labels`
   - `data.datasets[0].data` : `scores_radar.values`
   - Couleurs : borderColor `#0095D9`, backgroundColor `rgba(0,149,217,0.2)`
   - Options : `scales.r.min=0, max=100`, pointRadius 4, légende masquée
   - Titre sous le canvas : "Scores par dimension"

   **Colonne droite (50%)** — Score composite + analyse :
   - Grand cercle avec score : `score_composite` en chiffre + "/100"
   - Couleur du cercle selon score : ≥70 vert, 40-69 orange, <40 rouge
   - Liste des 3 dimensions les plus fortes (valeurs les plus hautes dans `scores_radar`)
   - Liste des 2 dimensions à renforcer (valeurs les plus basses)
   - NE PAS calculer : lire depuis `scores_radar.values` et classer

3. **Strategic box** (pleine largeur bas) :
   - 2 phrases de recommandation finale
   - Citer score composite et verdict
   - Icône `fa-flag-checkered`

## Règles

- Script Chart.js autorisé (graphique radar)
- Canvas ID unique : `radarChart`
- Si `scores_radar` null ou vide : remplacer le radar par un placeholder texte
- Classes : `section-accent-bar`, `strategic-box`
