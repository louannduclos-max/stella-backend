# Section : Cartographie concurrentielle

## Layout attendu

1. **Ligne de 3 KPI cards** (en haut, avant le tableau) :
   - Nombre total d'acteurs identifiés (`competitors_total_count`)
   - Nombre de concurrents directs (comptage depuis `competitors_top` où `is_direct_competitor=true`)
   - Note moyenne des acteurs (moyenne des `rating` non nuls, 1 décimale)
   - Icônes : `fa-store` pour acteurs, `fa-users` pour directs, `fa-star` pour note moyenne

2. **Tableau des concurrents principaux** (`competitors_top`) :
   - En-tête sur fond couleur primaire (#0095D9), texte blanc, Montserrat 700
   - Colonnes : **Nom** | **Type** | **Note ★** | **Avis** | **Statut**
   - Lignes alternées (blanc / highlight_bg)
   - Concurrents directs (`is_direct_competitor=true`) : classe CSS `is-direct` + badge "Direct" accent jaune
   - Note : afficher `★ 4.5` + le nombre d'avis entre parenthèses si disponibles. Si `rating` absent : `n.d.`
   - Statut : badge "Direct" (#FFCC00, texte brun) ou badge "Indirect" (gris clair)
   - Si `competitors_top` contient plus de concurrents que `competitors_total_count > 10` : afficher en sous-titre du tableau "N principaux sur M identifiés"

3. **Strategic box** (en bas du tableau) :
   - 2-3 phrases d'analyse de la pression concurrentielle
   - Citant obligatoirement : nombre total d'acteurs, nombre de directs, note moyenne
   - Icône `fa-lightbulb` en début, couleur primaire
   - Ton analytique et professionnel

## Règles

- **Ne jamais inventer** un nom, une note ou un nombre absent du manifest
- Si `rating` est `null` ou absent : afficher `n.d.` — jamais `0` ni `—`
- Si `review_count` est absent : ne pas afficher la colonne avis pour cette ligne
- Les colonnes **Type** et **Avis** peuvent être omises si toutes les valeurs sont nulles
- Limiter à 10 lignes max dans le tableau (les données sont déjà filtrées en `competitors_top`)
- Utiliser les classes CSS du `base_slide.html` : `kpi-row`, `kpi-card`, `comp-table`, `is-direct`, `badge-direct`, `strategic-box`
- Pas de `<script>` Chart.js sur cette slide (tableau pur HTML)
