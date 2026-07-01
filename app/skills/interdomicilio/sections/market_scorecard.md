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

2. **Structure GLOBALE imposée — 2 colonnes côte à côte** (la version empilée
   déborde du cadre 720px, constaté) :
   ```html
   <div style="display:flex;gap:36px;align-items:flex-start">
     <div style="flex:1.6"> <!-- les 7 score-row ici --> </div>
     <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:14px">
       <div style="width:150px;height:150px;border-radius:50%;
                   border:8px solid #DC2626;display:flex;flex-direction:column;
                   align-items:center;justify-content:center;
                   box-shadow:0 2px 10px rgba(15,23,42,.10)">
         <span style="font-family:Montserrat;font-size:40px;font-weight:800;color:#1F2937">43.1</span>
         <span style="font-size:13px;color:#6B7280">/100</span>
       </div>
       <span style="background:#DC2626;color:#fff;font-weight:800;
                    border-radius:999px;padding:8px 24px">NO GO</span>
       <!-- puis les 2 lignes Meilleure/Critique -->
     </div>
   </div>
   ```
   - Adapter la couleur de bordure du cercle et du badge au score/verdict réels
     (≥70 vert `#16A34A`, 40-69 orange `#EA580C`, <40 rouge `#DC2626` ; badge :
     mêmes règles que la slide verdict). Les valeurs 43.1/NO GO de l'exemple
     sont à REMPLACER par les valeurs réelles.
   - Sous le badge : "Meilleure dimension : {label du score le plus haut}" et
     "Dimension critique : {label du plus bas}" — lus dans `items`, pas calculés
     au-delà du classement

3. **Strategic box** (pleine largeur, bas) :
   - Base du texte : `narratives.verdict_narrative` (fourni) — recopier puis
     prolonger d'une phrase citant le score composite et la dimension critique.
     3-4 phrases au total. Aucun chiffre hors des scores affichés.
   - Icône `fa-gauge-high`

## Règles

- Pas de Chart.js (barres CSS pures)
- Classes : `kpi-row`, `kpi-card`, `strategic-box`, `strat-icon`, `section-accent-bar`
