# Section : Couverture

## Données disponibles (clés RÉELLES)

- `zone` : ville de l'étude (string) ; `brand_name` : marque ; `year` : année
- `verdict` : "GO" | "GO_CONDITIONAL" | "NO_GO" | null
- `score_composite` : float 0-100 ou null
- `competitors_total_count` : nombre d'acteurs identifiés (int)
- `metrics.by_id.population_total.value` : population de la zone
- `metrics.by_id.seniors_75_plus_share.value` : part des 75+ (%)

## Règles ABSOLUES

- Aucun chiffre hors de ceux listés. Absent → ne pas afficher l'élément.
- Ne pas réécrire le verdict en phrase marketing — le badge suffit.

## Layout attendu (slide d'ouverture — impact visuel maximal)

1. **Bloc titre central** (centré verticalement, ~55% de la hauteur) :
   - Sur-titre : "ÉTUDE DE FAISABILITÉ DE MARCHÉ" (lettres espacées,
     `letter-spacing:3px`, uppercase, text_muted, 14px)
   - Titre : `{zone}` en Montserrat 800, ~64px, couleur primary_dark
   - Sous-titre : "{brand_name} · Services à la personne · {year}"
     (Open Sans 600, 20px, text_muted)
   - Fine barre accent (`#FFCC00`, 4px × 80px) centrée entre sur-titre et titre

2. **Badge verdict central** (sous le bloc titre) :
   - Pastille arrondie (border-radius:999px, padding 10px 28px, texte blanc 700) :
     "GO" → fond `#16A34A` / "GO_CONDITIONAL" → `#EA580C` avec texte
     "GO CONDITIONNEL" / "NO_GO" → `#DC2626` avec texte "NO GO"
   - À droite de la pastille : score `{score_composite}` en 28px + "/100" en 14px
     (uniquement si non null)

3. **Bandeau 3 chips factuelles** (bas de slide, flex centré, gap 24px) :
   - `fa-users` population_total + "habitants"
   - `fa-person-cane` seniors_75_plus_share + "% de 75 ans et +"
   - `fa-store` competitors_total_count + "acteurs identifiés"
   - Style chip : fond `#F0F9FF`, bordure 1px `#0095D9`, border-radius 8px,
     padding 8px 16px, valeur en 700
   - Une valeur absente → omettre la chip (pas de "n.d." sur une couverture)

## Règles

- Pas de Chart.js, pas de tableau
- Classes : `section-accent-bar` + styles inline autorisés pour le centrage
