# Section : Plan d'action

## Données disponibles (clés RÉELLES)

- `narratives` : objet contenant :
  - `action_30d` : action prioritaire à 30 jours (texte)
  - `action_60d` : action prioritaire à 60 jours (texte)
  - `action_90d` : action prioritaire à 90 jours (texte)
  - `opportunity_text` : 1-2 phrases sur l'opportunité du marché (texte)
- `verdict` : "GO" | "GO_CONDITIONAL" | "NO_GO" | null

## Règles ABSOLUES anti-invention

- Les 3 actions viennent EXCLUSIVEMENT de `narratives.action_30d/60d/90d` —
  recopier le texte tel quel, ne pas le réécrire, ne pas ajouter d'action.
- Si une action est absente/vide : ne pas afficher sa carte (pas de texte de
  remplacement inventé).
- Si les 3 sont absentes : afficher une `strategic-box` "Plan d'action non
  disponible pour cette étude."
- Aucun chiffre inventé (pas de coûts, pas de budgets, pas d'effectifs).

## Layout attendu

1. **En-tête** : "Feuille de route 30 / 60 / 90 jours"

2. **Timeline horizontale de 3 cartes** (flex, gap 16px, une carte par échéance) :
   - Carte 1 — badge circulaire "J+30" (fond primary `#0095D9`, texte blanc)
     + icône `fa-flag` + texte `action_30d`
   - Carte 2 — badge "J+60" (fond primary_dark `#00608A`) + icône `fa-users`
     + texte `action_60d`
   - Carte 3 — badge "J+90" (fond accent `#FFCC00`, texte `#1F2937`)
     + icône `fa-rocket` + texte `action_90d`
   - Chaque carte : fond blanc, bordure 1px `#E5E7EB`, border-radius 8px,
     padding 16px, le badge en haut, une fine barre de connexion visuelle entre
     les cartes (ligne grise horizontale derrière les badges)

3. **Strategic box** (bas de slide) :
   - Recopier `narratives.opportunity_text` si présent, sinon 1 phrase neutre
     de conclusion adaptée au `verdict` (sans chiffre).
   - Icône `fa-bullseye`

## Règles

- Pas de Chart.js
- Classes : `kpi-row`, `kpi-card`, `strategic-box`, `strat-icon`, `section-accent-bar`
