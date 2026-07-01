# Section : Analyse SWOT

## Données disponibles

`scores` : liste de {score_id, label, value, weight, interpretation}
- Valeur positive élevée → force / opportunité
- Valeur faible → faiblesse / menace
- `interpretation` : phrase d'interprétation fournie

**RÈGLE** : Ne JAMAIS inventer de bullets SWOT. Utiliser uniquement les `interpretation` du manifest.
Les scores sont déjà calculés — ne pas recalculer.

## Layout attendu

Grille 2x2 (`display: grid; grid-template-columns: 1fr 1fr; gap: 1rem`) :

**Case FORCES** (vert `#16A34A` / fond `#F0FDF4`) :
- Titre : "Forces" + icône `fa-plus-circle`
- Bullets : scores avec value ≥ 60, utiliser leur `interpretation`
- Max 3 bullets
- Si aucun score ≥ 60 : "Aucune force significative identifiée"

**Case FAIBLESSES** (rouge `#DC2626` / fond `#FEF2F2`) :
- Titre : "Faiblesses" + icône `fa-minus-circle`
- Bullets : scores avec value < 40, utiliser leur `interpretation`
- Max 3 bullets
- Si aucun score < 40 : "Aucune faiblesse majeure identifiée"

**Case OPPORTUNITÉS** (bleu `#0095D9` / fond `#E6F4FB`) :
- Titre : "Opportunités" + icône `fa-arrow-trend-up`
- Bullets : scores avec value entre 50-70 avec interprétation positive de marché
- Ou : les 2-3 meilleurs scores non utilisés en Forces
- Max 3 bullets

**Case MENACES** (orange `#EA580C` / fond `#FFF7ED`) :
- Titre : "Menaces" + icône `fa-triangle-exclamation`
- Bullets : scores avec value entre 30-50 ou interpretation négative de marché
- Ou : les 2-3 moins bons scores non utilisés en Faiblesses
- Max 3 bullets

## Règles

- **Source unique** : `scores[*].interpretation` — jamais de texte inventé
- Si `interpretation` est vide pour un score : sauter ce score
- Si `scores` vide ou null : afficher un message "Analyse SWOT non disponible"
- Chaque case : border-radius 8px, padding 1rem, border-left 4px solid couleur
- Pas de Chart.js
- Classes : `section-accent-bar`
