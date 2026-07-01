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
   - Une ligne par score : label (Open Sans 600, 14px) puis barre horizontale
     CSS : conteneur gris clair `#F3F4F6` border-radius 999px hauteur 14px,
     remplissage `width: {value}%` avec couleur :
     value ≥ 60 → `#16A34A` / 40-59 → `#EA580C` / < 40 → `#DC2626`
   - Valeur "{value}/100" en 700 à droite de la barre

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
