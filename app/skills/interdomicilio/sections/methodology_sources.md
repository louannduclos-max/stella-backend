# Section : Méthodologie & sources

La slide qui matérialise le différenciateur Stella : chaque valeur de l'étude
est tracée vers une source identifiée et graduée. C'est la slide de confiance.

## Données disponibles (clés RÉELLES)

- `sources` : objet `{count, items}` — `items` = liste de :
  - `title` : nom de la source
  - `publisher` : éditeur (ex. "INSEE", "Google Places", "CNSA")
  - `confidence_grade` : "A" | "B" | "C" | "D"
  - `theme_id` : thème couvert (demography, income_housing, competition, ...)
  - `source_type` : "official_national" | "commercial" | "semi_official" | ...

## Règles ABSOLUES anti-invention

- Recopier `title` et `publisher` verbatim. Ne JAMAIS ajouter une source.
- Ne pas inventer de dates de publication ni de méthodologie non fournie.
- `sources.count` est le seul comptage autorisé.

## Layout attendu

1. **Bandeau d'intro** (strategic-box en HAUT de slide, icône `fa-shield-check`) :
   - "Chaque donnée de cette étude est tracée : {count} sources identifiées,
     chacune graduée de A (source officielle directe) à D (baseline nationale)."

2. **Légende des grades** (ligne de 4 chips) :
   - A — "Officielle directe" (fond `#F0FDF4`, texte `#16A34A`)
   - B — "Fiable / dérivée" (fond `#E6F4FB`, texte `#0095D9`)
   - C — "Estimation locale" (fond `#FFF7ED`, texte `#EA580C`)
   - D — "Baseline nationale" (fond `#FEF2F2`, texte `#DC2626`)

3. **Tableau des sources** (`comp-table`, max 10 lignes) :
   - Colonnes : Source | Éditeur | Thème | Grade
   - Trier : grade A d'abord, puis B, C, D
   - Colonne Grade : badge coloré (mêmes couleurs que la légende)
   - Si plus de 10 sources : sous-titre "10 principales sur {count}"
   - Thème : traduire les theme_id en français lisible (demography → Démographie,
     income_housing → Revenus & habitat, competition → Concurrence,
     real_estate → Immobilier, employment → Emploi, regulation → Réglementation)

4. **Pied de slide** (petit texte muted) :
   - "Données absentes affichées « n.d. » — Stella n'extrapole jamais une valeur
     manquante."

## Règles

- Pas de Chart.js
- Classes : `comp-table`, `strategic-box`, `strat-icon`, `section-accent-bar`
