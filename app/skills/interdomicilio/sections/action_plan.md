# Section : Plan d'action

## Données disponibles

`action_plan` : liste d'actions, chaque item :
- `title` : titre de l'action
- `description` : description courte
- `priority` : "high" | "medium" | "low"
- `timeline` : délai estimé (ex. "J+30", "3 mois", "Immédiat")
- `category` : catégorie (ex. "Commercial", "RH", "Financier", "Réglementaire")
- `estimated_cost` : coût estimé (string, peut être null)

Si `action_plan` est null ou vide : générer 3 actions génériques adaptées au contexte
(projet SAP, zone géographique de l'étude).

## Layout attendu

1. **En-tête** : "Prochaines étapes recommandées" avec badge compteur (N actions)

2. **Liste d'actions** (max 6) :

   Chaque action = carte horizontale :
   - **Badge priorité** à gauche :
     - "high" → rouge `#DC2626` + "Priorité haute"
     - "medium" → orange `#EA580C` + "Priorité moyenne"
     - "low" → gris `#6B7280` + "Priorité basse"
   - **Titre** en Montserrat 600, couleur `#1F2937`
   - **Description** en Open Sans, gris `#6B7280`
   - **Timeline** badge bleu clair à droite : icône `fa-clock` + délai
   - **Catégorie** badge discret en bas à droite
   - Fond blanc, bordure gauche 3px couleur priorité, border-radius 6px, padding 0.75rem

3. Si `estimated_cost` présent : afficher sous la description en italic gris

## Règles

- Max 6 actions affichées (les N premières si plus)
- Trier : high → medium → low si non déjà trié
- Ne pas inventer d'actions si `action_plan` est null — afficher "Plan d'action non disponible"
  (EXCEPTION à la règle générale : ce champ peut être absent si l'étude est récente)
- Pas de Chart.js
- Classes : `section-accent-bar`
