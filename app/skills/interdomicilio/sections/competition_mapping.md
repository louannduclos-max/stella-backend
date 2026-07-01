# Section : Cartographie concurrentielle

## Données disponibles

`competition_table` (pré-calculé — recopier tel quel, NE PAS recalculer) :
- `count_total` : nombre total d'acteurs collectés
- `count_direct` : nombre de concurrents directs
- `avg_rating` : note moyenne des acteurs (float ou null)
- `directs` : liste des concurrents directs (max 8), chacun avec :
  - `name` : nom de l'acteur
  - `domain` : domaine d'expertise déduit (ex: "Aide à domicile senior") ou "n.d."
  - `rating` : note Google (float ou null)
  - `stars` : chaîne d'étoiles pré-calculée (ex: "★★★★☆") ou null
  - `reviews` : nombre d'avis (int ou null)
- `indirects` : liste des concurrents indirects (max 6), même structure

## Layout attendu

### 1. Ligne de 3 KPI cards

- Acteurs identifiés → `competition_table.count_total` — icône `fa-store`
- Concurrents directs → `competition_table.count_direct` — icône `fa-users`
- Note moyenne → `competition_table.avg_rating` (1 décimale) ou "n.d." — icône `fa-star`

### 2. Tableau des concurrents (comp-table)

Colonnes : **Nom** | **Domaine d'expertise** | **Note** | **Statut**

- Afficher TOUJOURS les concurrents `directs` en premier (class `is-direct` sur leur ligne),
  puis les `indirects`.
- Colonne **Note** : afficher `rating` en gras, et `stars` en dessous en plus petit
  (classe `rating-stars`). Si `rating` null → "n.d.", pas d'étoiles.
- Colonne **Statut** :
  - Directs → badge "Direct" classe `badge-direct`
  - Indirects → badge "Indirect" classe `badge-indirect`
- Colonne **Domaine** : recopier `domain` tel quel. Si "n.d." → italique grisé.
- Si `count_total > 14` : ajouter sous-titre "14 principaux sur N identifiés".

### 3. Strategic box

- Citer `count_direct` et `count_total` (réels, jamais inventés)
- Citer `avg_rating` si non null
- Analyser la pression concurrentielle (directs vs. indirects) et le niveau qualitatif
- Icône `fa-map-location-dot`

## Cas edge

- `count_total = 0` : afficher "Aucun acteur identifié dans la zone" dans le tableau.
  Strategic box : "marché peu dense ou collecte à approfondir."
- Tous les `domain` à "n.d." : on peut masquer la colonne Domaine pour alléger.

## Règles ABSOLUES

- Recopier `name`, `domain`, `rating`, `stars`, `reviews` verbatim.
- NE JAMAIS recalculer les étoiles — elles sont dans `stars`, pré-calculées.
- NE JAMAIS recalculer `avg_rating` — il est dans `competition_table.avg_rating`.
- NE JAMAIS ajouter un concurrent absent de `competition_table`.
- NE JAMAIS inventer un domaine si "n.d." est fourni.

## Classes CSS

`kpi-row`, `kpi-card`, `kpi-icon`, `kpi-value`, `kpi-label`,
`comp-table`, `is-direct`, `badge-direct`, `badge-indirect`,
`rating-stars`, `strategic-box`, `strat-icon`, `section-accent-bar`
