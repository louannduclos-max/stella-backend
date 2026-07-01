# Section : Emploi & vivier RH

Le recrutement d'intervenants est LE facteur limitant d'une agence SAP —
cette slide évalue le vivier local.

## Données disponibles (clés RÉELLES — chercher par metric_id dans `metrics.by_id`)

- `care_worker_pool` : vivier d'intervenants aide à domicile (personnes)
- `jobseekers_service_sector` : demandeurs d'emploi du secteur services (personnes)
- `unemployment_rate` : taux de chômage local (%)
- `working_age_women_share` : part des femmes en âge de travailler (%)
- Chaque métrique porte `confidence_grade` ("A"-"D") et `fallback_used` (bool)

## Règles ABSOLUES anti-invention

- Ces 4 metric_id sont les SEULS valides. Absent → "n.d.".
- **Badge honnêteté obligatoire** : si `fallback_used` est true OU grade "C"/"D",
  afficher un petit badge "estimation" (fond `#FFF7ED`, texte `#EA580C`, 10px)
  dans le coin de la card. La transparence fait partie du produit.
- Aucun calcul (pas de ratio candidats/poste, pas de projection).

## Layout attendu

1. **Ligne de 4 KPI cards** :
   - `care_worker_pool` + "Vivier intervenants SAP" — `fa-hand-holding-heart`
   - `jobseekers_service_sector` + "Demandeurs d'emploi services" — `fa-user-clock`
   - `unemployment_rate` + "%" + "Taux de chômage" — `fa-briefcase`
   - `working_age_women_share` + "%" + "Femmes en âge de travailler" — `fa-people-group`

2. **Encart lecture stratégique** (2 colonnes égales) :
   - Colonne "Atouts recrutement" (`fa-circle-plus`, vert) : 2 bullets qualitatifs
     s'appuyant UNIQUEMENT sur les valeurs affichées (ex. chômage au-dessus de la
     moyenne = vivier disponible)
   - Colonne "Points de vigilance" (`fa-triangle-exclamation`, orange) : 2 bullets
     (ex. tension sur les métiers du care, concurrence sur les profils qualifiés —
     formulations génériques métier autorisées SANS chiffre)

3. **Strategic box** (pleine largeur, bas) :
   - 2 phrases : capacité de la zone à staffer une agence, en citant
     `care_worker_pool` et `unemployment_rate`
   - Icône `fa-users-gear`

## Règles

- Pas de Chart.js
- Classes : `kpi-row`, `kpi-card`, `kpi-icon`, `kpi-value`, `kpi-label`,
  `strategic-box`, `strat-icon`, `section-accent-bar`
