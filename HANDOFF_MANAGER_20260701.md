# HANDOFF MANAGER — Stella V2.1
**Date :** 1er juillet 2026 — mise à jour Sprint 9
**Rédigé par :** Claude Cowork

---

## CE QUI A ÉTÉ FAIT AUJOURD'HUI

### Sprint 6 — Fix `isGenerating` (commit `4edb754`) ✅

**Fichier :** `front/src/routes/_authenticated/app.studies.$id.tsx` ligne 193

Le bouton "Lancer la generation" etait invisible sur les etudes `pending` creees via "Nouvelle version". Fix : `isGenerating` couvre uniquement `"processing"`. **Deploye CF Pages.**

---

### Sprint Data-Depth — Enrichissement manifest (commit `c534183`) ✅

5 chantiers backend — aucun endpoint casse.

| Chantier | Apport manifest |
|----------|-----------------|
| Benchmark national | `metrics[*].national_benchmark`, `benchmark_interpretation` |
| Concurrents nommes | `competitors_top` (<=10), `competitors_total_count` |
| Bareme APA + market sizing | `funding_scale` (4 GIR CNSA 2026), `market_sizing` |
| Manifest | 4 nouvelles cles top-level |
| QA | BENCH_001, FUND_001 |

---

### Sprint 8 — Chemin B : Infrastructure HTML generatif ✅

**Livre :**
- Fix Gemini complet (`GEMINI_MODEL` env var, `maxOutputTokens` 4096, `_safe_parse_json()` defensif)
- `HTMLSlideAgent` + QA HTML + skill Interdomicilio (colors, base template, sections/competition.md)
- Endpoint `GET /agents/debug/html-slide?study_id=...`
- Bug `json.dumps` date non serialisable corrige (`default=str`)
- Env var `GEMINI_MODEL=gemini-2.5-flash` ajoutee sur Render

---

### Sprint 9 — Collecte concurrentielle + HTML production-ready ✅

**Objectif :** Fermer les failles de securite et resilience avant d'activer le Chemin B en production.

#### A — Probe dual-API + Collector New Places API

`GET /agents/debug/places-probe` teste maintenant **Legacy textsearch** ET **New Places API** et retourne une recommandation automatique.

Le collector supporte les deux APIs via flag `GOOGLE_PLACES_API_NEW` :
- `false` (defaut) : Legacy Nearby Search — inchange
- `true` : New Places API avec pagination correcte (sleep 3s entre pages, max 60 resultats)

#### B — Sanitisation injection de prompt

`app/agents/sanitize.py` (nouveau) : nettoie tous les noms Places avant injection dans le prompt Gemini. Protection contre les etablissements nommes avec des patterns d'injection.

#### C — QA HTML renforce (3 checks vs 1 en v2)

`qa_html_agent.py` reecrit — 3 verifications :
- Nombres dans le texte visible
- **Donnees Chart.js** `data: [...]` dans les blocs `<script>` (faille v2 comblee)
- **Red-flags** : superlatifs non sources ("leader du marche", "le meilleur", etc.)

#### D — Resilience pipeline (ThreadPoolExecutor + circuit breaker)

`slides_5_0_builder.py` — Chemin B activable via `USE_HTML_SLIDE_AGENT=true` :
- `ThreadPoolExecutor` (sync-safe, pas asyncio) pour paralleliser les appels Gemini
- Circuit breaker partage par etude : 3 echecs Gemini -> fallback total immediat
- Le deterministe PPTX est TOUJOURS construit -> 15 slides garanties meme si Gemini tombe

#### E — Cache slide HTML

`app/services/slide_cache.py` (nouveau) : cle SHA256 canonique stable + stockage Supabase.
0 appel Gemini si la meme slide est regeneree a l'identique.
**Table a creer** sur Supabase backend (`exacjvbgtrejbjtttcsz`).

---

## E2E SPRINT 6 — BORDEAUX VALIDE

**Etude :** `18f460c9-245b-4443-aa65-23eb2032089c`

| Etape | Resultat |
|-------|----------|
| Wizard Interdomicilio / Bordeaux | OK |
| Bouton "Lancer" visible (fix Sprint 6) | OK |
| Pipeline 5 phases (~34s) | OK |
| PPTX 74 Ko genere + telechargeable | OK |

---

## E2E SPRINT DATA-DEPTH — BORDEAUX V4 VALIDE

**Etude :** `65585b75-b51d-4cf8-a5e9-dd734f898f3d`

Pipeline complet + PPTX 74 Ko — les 4 chantiers Data-Depth ont tourne sans erreur.

---

## ETAT DES SERVICES

| Service | URL | Statut |
|---------|-----|--------|
| Backend Render | `stella-backend-mtap.onrender.com` | En deploy — Sprint 9 |
| Frontend CF Pages | `stellav1front.pages.dev` | LIVE — commit `4edb754` |
| Supabase cowork (front) | projet `utwjfsomblhupghbgvgv` | OK |
| Supabase louann-duclos (back) | projet `exacjvbgtrejbjtttcsz` | OK |

**Env vars Render :** `GEMINI_MODEL=gemini-2.5-flash` presente.
**A ajouter apres probe :** `GOOGLE_PLACES_API_NEW=true` si New API repond.

---

## BUGS RESOLUS CETTE SESSION

| Bug | Sprint | Statut |
|-----|--------|--------|
| Bouton "Lancer" invisible sur etudes pending | 6 | OK |
| Gemini `maxOutputTokens` trop bas (1024) | 8 | OK |
| Parsing JSON Gemini non defensif | 8 | OK |
| `lstrip("```json")` buggy dans `narrative_agent.py` | 8 | OK |
| `json.dumps` plante sur `date` (`qa_html_agent.py`) | 8 | OK |
| QA ne verifiait pas les donnees Chart.js | 9 | OK |
| Cle de cache instable (Pydantic/dates) | 9 | OK |
| Pas de sanitisation des noms Places -> injection prompt | 9 | OK |
| Circuit breaker local jamais declenche | 9 | OK |

---

## ACTIONS MANUELLES EN ATTENTE

### Immediates
- [ ] Supprimer `.git\index.lock` si present + pusher le fix Places spec (2 fichiers) :
  ```bat
  del "D:\claude\stella\stella V2.1\.git\index.lock"
  cd "D:\claude\stella\stella V2.1"
  git add app/services/external/google_places_api.py app/services/collectors/competition.py
  git commit -m "fix(places-new): pagination body rebuild + source_id traceability"
  git push
  ```
  Puis Manual Deploy sur Render.
- [ ] `GET /agents/debug/places-probe?query=aide+a+domicile+Bordeaux`
  - `NEW_API_OK` -> ajouter `GOOGLE_PLACES_API_NEW=true` sur Render + redeploy
  - `LEGACY_OK` -> ne rien changer
- [ ] Creer table Supabase backend (`exacjvbgtrejbjtttcsz`) :
  ```sql
  CREATE TABLE IF NOT EXISTS slide_html_cache (
    key TEXT PRIMARY KEY,
    html TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
  );
  ```
- [ ] Retester `GET /agents/debug/html-slide?study_id=18f460c9-245b-4443-aa65-23eb2032089c`

---

## BACKLOG PRIORISE

### Immediat
- [ ] Probe Places -> decision API -> si New : activer + test Bordeaux avec concurrents reels
- [ ] Table Supabase `slide_html_cache`
- [ ] Test slide HTML concurrence (QA passe ?)

### Sprint 10 — Generalisation HTML (si slide competition validee)
- [ ] `sections/executive_summary.md` + test + valider
- [ ] `sections/benchmark_comparison.md` + test + valider
- [ ] Repeter pour les 13 sections restantes (une par une)
- [ ] Frontend : iframe `sandbox="allow-scripts"` (sans `allow-same-origin`)
- [ ] Activer `USE_HTML_SLIDE_AGENT=true` quand >= 10 sections validees

### Court terme (independant du Chemin B)
- [ ] Slides Data-Depth : brancher `competitors_top`, `funding_scale`, `market_sizing` dans `layout_engine_5_0.py`
- [ ] NarrativeAgent (`SLIDE_BUILDER_USE_AGENT=true`) apres golden check OK
- [ ] Bareme ES (SAAD) dans `funding_scales.py` avant Interdomicilio Espagne
- [ ] Frontend : retirer `borderLeft` dans `KpiListRenderer` + `HighlightBoxRenderer`

### Annuel (maintenance)
- [ ] Mettre a jour `BENCHMARKS_YEAR` + valeurs `national_benchmarks.py` (INSEE / France Travail / DVF)
- [ ] Reverifier montants APA `funding_scales.py` au 1er janvier (circulaire CNSA)

---

## RAPPELS OPERATIONNELS

**Render :** Toujours Manual Deploy apres push backend. Cold start ~50s apres 15 min d'inactivite.

**Deux flows de creation d'etude :**

| Flow | Appelle Render | Status initial |
|------|----------------|----------------|
| Wizard (6 etapes) | OUI | `pending` -> Render demarre |
| "Nouvelle version" | NON | `pending` -> bouton Lancer requis |

**Deux projets Supabase distincts :**
- Render -> `exacjvbgtrejbjtttcsz` (louann-duclos)
- CF Pages -> `utwjfsomblhupghbgvgv` (cowork)

**Flags HTML actifs sur Render :**

| Variable | Valeur actuelle | Effet |
|----------|-----------------|-------|
| `GEMINI_MODEL` | `gemini-2.5-flash` | Modele Gemini |
| `SLIDE_BUILDER_USE_AGENT` | absent/false | NarrativeAgent desactive |
| `USE_HTML_SLIDE_AGENT` | absent/false | Chemin B desactive — test via endpoint debug uniquement |
| `GOOGLE_PLACES_API_NEW` | absent/false | Legacy Nearby Search actif |

**Ne jamais activer `USE_HTML_SLIDE_AGENT=true` avant validation section par section.**

**`SKILL_VERSION` dans `slide_cache.py`** : bumper a chaque modification de `base_slide.html` ou `sections/*.md`.
