# Section : Cartographie concurrentielle (vue synthétique)

## Données disponibles

- `competitors_top` : liste des concurrents (max 10), chaque item :
  - `name` : nom de l'acteur
  - `is_direct_competitor` : bool
  - `rating` : float ou null
  - `review_count` : int ou null
  - `address` : adresse complète
  - `source_id` : "google_places_new" ou "google_places_legacy"
- `competitors_total_count` : nombre total identifiés
- `competition_avg_rating` : moyenne des notes (pré-calculée) ou null

**RÈGLE** : `competition_avg_rating` est pré-calculé — ne pas recalculer depuis `competitors_top`.

## Layout attendu (identique à competition mais avec badge source)

1. **Ligne de 3 KPI cards** :
   - Acteurs totaux (`competitors_total_count`)
   - Concurrents directs (compter `is_direct_competitor=true` dans `competitors_top`)
   - Note moyenne (`competition_avg_rating`, 1 décimale, "n.d." si null)
   - Icônes : `fa-store`, `fa-users`, `fa-star`

2. **Tableau des concurrents** (`comp-table`) :
   - Colonnes : Nom | Type | Note ★ | Avis | Statut
   - Ligne directe : classe `is-direct` + badge "Direct" jaune `#FFCC00`
   - Note : "★ 4.5" ou "n.d." si null
   - Avis : nombre entre parenthèses ou omis si null
   - Si `competitors_total_count > 10` : sous-titre "10 principaux sur N identifiés"

3. **Strategic box** :
   - Analyser : pression concurrentielle (nombre directs vs. indirects), niveau qualitatif (note moyenne)
   - Citer les chiffres du manifest — jamais inventés
   - Icône `fa-map-location-dot`

## Règles

- Si `competitors_top` vide : afficher "Aucun concurrent identifié dans la zone" dans le tableau
- Ne jamais inventer de noms, notes ou adresses
- Classes : `kpi-row`, `kpi-card`, `comp-table`, `is-direct`, `badge-direct`, `badge-indirect`, `strategic-box`
