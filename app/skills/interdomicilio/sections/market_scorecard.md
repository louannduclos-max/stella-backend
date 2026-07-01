# Section : Scorecard marché

Vue synthétique des 7 dimensions d'analyse — la slide "tableau de bord".

## Données disponibles (clés RÉELLES)

- `scores` : objet `{count, items, by_id}` — `items` = liste de
  `{score_id, label, value, weight, interpretation}` (7 dimensions, value 0-100)
- `score_composite` : float 0-100 ou null
- `verdict` : "GO" | "GO_CONDITIONAL" | "NO_GO" | null

## Règles ABSOLUES anti-invention

- Recopier `label` et `value` tels quels. AUCUN score recalculé, arrondi ou pondéré.
- Ne pas commenter un score au-delà de son label (pas d'analyse inventée par barre).
- ATTENTION sémantique : pour "Pression concurrentielle", "Complexité réglementaire"
  et "Risque d'exécution", un score BAS est DÉFAVORABLE au même titre que les autres
  (le moteur normalise déjà le sens : haut = favorable). Ne pas inverser.

## Layout attendu

1. **Colonne gauche (~62%) — les 7 barres** :
   Une ligne par score, en utilisant EXACTEMENT ce motif (classes du template) :
   ```html
   <div class="score-row">
     <span class="score-label">Potentiel récurrent</span>
     <div class="bar-track"><div class="bar-fill bar-orange" style="width:57%"></div></div>
     <span class="score-value">57/100</span>
   </div>
   ```
   Couleur de la barre : value ≥ 60 → `bar-green` / 40-59 → `bar-orange` /
   < 40 → `bar-red`. Le `width` du bar-fill = la valeur en %.

2. **Colonne droite (~38%) — synthèse** :
   - Grand cercle score composite : `score_composite` en 44px + "/100" en 14px,
     bordure 6px de la couleur du score (mêmes seuils que les barres)
   - Badge verdict sous le cercle (mêmes couleurs/textes que la slide verdict)
   - En dessous : mini-liste "Meilleure dimension" (label du score le plus haut)
     et "Dimension critique" (label du plus bas) — lus dans `items`, pas calculés
     au-delà du classement

3. **Strategic box** (pleine largeur, bas) :
   - 2 phrases de lecture globale citant le score composite et la dimension
     critique. Aucun chiffre hors des scores affichés.
   - Icône `fa-gauge-high`

## Règles

- Pas de Chart.js (barres CSS pures)
- Classes : `kpi-row`, `kpi-card`, `strategic-box`, `strat-icon`, `section-accent-bar`
