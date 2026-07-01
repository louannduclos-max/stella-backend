# HANDOFF MANAGER — Stella V2.1
**Date :** 1er juillet 2026 — mise à jour Sprint Data-Depth
**Rédigé par :** Claude Cowork

---

## ✅ E2E SPRINT 6 — BORDEAUX VALIDÉ (1er juillet 2026)

### Fix principal : bouton "Lancer la génération" caché sur études pending

**Commit :** `4edb754` — `front/src/routes/_authenticated/app.studies.$id.tsx` ligne 193

```ts
// AVANT (bug)
const isGenerating = status === "pending" || status === "processing";
// APRÈS (fix)
const isGenerating = status === "processing";
```

**Pourquoi :** Le flow "Nouvelle version" crée l'étude avec `generation_status: "pending"` sans appeler Render. Le bouton "🚀 Lancer la génération" était invisible car `isGenerating=true` cachait le bouton `canLaunch`. Fix : `isGenerating` ne couvre plus que `"processing"` (Render actif). Le bouton apparaît maintenant sur `pending`, `draft`, et `failed`.

**Déployé :** CF Pages `stellav1front.pages.dev` ✅

### Résultats E2E Bordeaux

| Étape | Résultat |
|-------|----------|
| Wizard — Interdomicilio / Bordeaux / Étude de Faisabilité | ✅ |
| "Nouvelle version" → étude `pending` créée | ✅ |
| Bouton "🚀 Lancer la génération" visible (fix Sprint 6) | ✅ |
| Toast "🚀 Génération lancée (~5-10 min, ~0.25 €)" | ✅ |
| Render POST /generate-study → 200 OK | ✅ |
| Pipeline 5 phases (~34s : 00:17:49 → 00:18:23) | ✅ |
| PPTX généré — 76 155 octets (74 Ko) | ✅ |
| Supabase Storage `deliverables/{id}/etude.pptx` | ✅ |
| Webhook CF Pages → `generation_status = "done"` | ✅ |
| Supabase Realtime push → UI rafraîchie | ✅ |
| Bouton téléchargement PPTX actif | ✅ |

**Étude test Sprint 6 :** ID `18f460c9-245b-4443-aa65-23eb2032089c`
**URL :** https://stellav1front.pages.dev/app/studies/18f460c9-245b-4443-aa65-23eb2032089c

### Anomalie Gemini constatée

```
[gemini_analyst] parsing réponse échoué : Unterminated string starting at: line 2 column 24 (char 25)
[gemini_analyst] Gemini n'a pas répondu — fallback template
```

Le modèle répond (pas de 404 → `gemini-2.0-flash` potentiellement de nouveau disponible), mais la réponse JSON est tronquée. Slides narratifs = template fallback. PPTX généré correctement malgré cela.

---

## ✅ E2E LIVRÉ — ÉTUDE GÉNÉRÉE + PPTX TÉLÉCHARGÉ

L'étude **Interdomicilio — Paris v1** a été générée avec succès et le PPTX est disponible.

| Étape | Résultat |
|-------|----------|
| Wizard (6 étapes) | ✅ Paris · Interdomicilio |
| Backend pipeline (5 phases) | ✅ Render FastAPI |
| PPTX généré et uploadé | ✅ 67 Ko dans Supabase storage |
| Supabase `generation_status` = "done" | ✅ |
| CF Pages génération-webhook | ✅ déployé (fix Sprint 3) |
| Téléchargement PPTX côté utilisateur | ✅ confirmé |

**Étude test :** ID `7f4d7d0e-6f10-49a5-a154-06888be5097c`
**URL :** https://stellav1front.pages.dev/app/studies/7f4d7d0e-6f10-49a5-a154-06888be5097c

---

## ✅ E2E SPRINT 5 — ÉTUDE LYON GÉNÉRÉE + PPTX TÉLÉCHARGÉ (30 juin 2026)

| Étape | Résultat |
|-------|----------|
| Wizard — Interdomicilio / Lyon / Étude de Faisabilité | ✅ |
| Pipeline Sprint 5 (layout_engine_5_0 → validate_slide_objects → QAAgent) | ✅ |
| PPTX généré | ✅ 72 Ko |
| Durée pipeline | ~27s (07:11:13 → 07:11:40) |
| Progress steps | 5%→20%→50%→75%→90%→100% |
| Téléchargement PPTX | ✅ confirmé |

**Étude test Sprint 5 :** ID `371196f9-4513-4aff-90fc-4358b3624c61`

---

## ÉTAT DES SERVICES

| Service | URL | Statut |
|---------|-----|--------|
| Backend Render | `stella-backend-mtap.onrender.com` | ✅ LIVE |
| Frontend CF Pages | `stellav1front.pages.dev` | ✅ LIVE |
| Supabase cowork (front DB) | `utwjfsomblhupghbgvgv` | ✅ |
| Supabase louann-duclos (backend DB) | `exacjvbgtrejbjtttcsz` | ✅ |

---

## CE QUI A ÉTÉ RÉPARÉ AUJOURD'HUI

### 1. Clé Supabase Render (critique)
Le backend Render utilisait une ancienne clé désactivée le 23 juin pour le projet `exacjvbgtrejbjtttcsz`.
→ **Fix :** Nouvelle Secret key collée dans Render → Environment → `SUPABASE_SERVICE_ROLE_KEY`.

### 2. CF Pages jamais déployé depuis Sprint 3
3 fichiers TS étaient tronqués dans le working tree (`generate-study.functions.ts`, `supabase-browser.ts`, `wizard.functions.ts`) → TypeScript échouait au build → CF Pages restait sur l'ancienne version sans l'endpoint `/api/public/generation-webhook`.
→ **Fix :** Restauration depuis git + push `push_force_cfpages.bat` → CF Pages déployé.

### 3. CF Pages env vars manquantes
`GENERATION_WEBHOOK_SECRET` et `SUPABASE_SERVICE_ROLE_KEY` (projet cowork) n'étaient pas configurés sur CF Pages.
→ **Fix :** Ajoutés manuellement dans le dashboard CF Pages.

> ⚠️ **Important : les deux projets Supabase ont des clés différentes**
> - Render `SUPABASE_SERVICE_ROLE_KEY` = secret key du projet `exacjvbgtrejbjtttcsz` (louann-duclos)
> - CF Pages `SUPABASE_SERVICE_ROLE_KEY` = secret key du projet `utwjfsomblhupghbgvgv` (cowork)

### 4. Bug `date` non sérialisable (slide_builder_agent.py)
Le JSON encoder plantait sur les objets Python `date` dans les données d'étude → tous les slides tombaient en fallback layout_engine.
→ **Fix :** Ajout d'un `_DateEncoder(json.JSONEncoder)` dans `slide_builder_agent.py`.

### 5. Gemini model obsolète (session précédente)
`gemini-1.5-flash` n'existe plus sur l'API v1beta.
→ **Fix :** Mis à jour vers `gemini-2.0-flash` dans `narrative_agent.py` et `gemini_analyst.py`.

### 6. Logs `notify_front` invisibles
Les callbacks Render → CF Pages passaient par `logger.warning/debug` qui ne s'affiche pas dans les logs Render sans handler.
→ **Fix :** Remplacé par `print(flush=True)` dans `progress_notifier.py`.

---

## SEUL POINT RESTANT : APERÇU SLIDES

La page étude affiche **"Chargement de l'aperçu…"** en boucle car `StudyResultView` utilise pdf.js pour afficher les slides, mais le backend ne génère que du PPTX (pas de PDF).

**Fix déjà codé + poussé** : `push_fix_preview.bat` (commit dans `stellav1front`) remplace le spinner infini par un message clair "Aperçu PDF non disponible — Téléchargez le PPTX ci-dessous".

**Pour ajouter un vrai aperçu slides à l'avenir :**
- Option A (rapide) : LibreOffice headless sur Render pour convertir PPTX → PDF → envoyer `file_pdf` dans le callback
- Option B (qualité) : Générer des PNG slide-by-slide avec python-pptx + Pillow

---

## ARCHITECTURE PIPELINE COMPLET

```
[Browser User]
    │ clic "🚀 Lancer la génération"
    ▼
[CF Pages — stellav1front.pages.dev]  (TanStack Start SSR)
    │ POST /generate-study (Bearer WEBHOOK_SECRET)
    ▼
[Render FastAPI — stella-backend-mtap.onrender.com]
    │ pipeline 5 phases (~30s)
    │   Phase 1: Consolidation + geo
    │   Phase 2: Métriques marché
    │   Phase 3: Concurrence Google Places
    │   Phase 4: Scoring + SWOT
    │   Phase 5: QA + Gemini narratifs
    │ build_pptx_for_study() → 72 Ko
    │ notify_front(status="done", pptx_bytes=...)
    ▼
[CF Pages /api/public/generation-webhook]
    │ upload PPTX → Supabase Storage bucket "deliverables"
    │ INSERT study_deliverables (type="pptx")
    │ UPDATE studies SET generation_status="done", status="active"
    ▼
[Browser User] ← Supabase Realtime push
    PPTX téléchargeable ✅
```

---

## REPOS GIT

| Repo | Branche | Dernier commit significatif |
|------|---------|----------------------------|
| `louannduclos-max/stella-backend` | main | `fix: date encoder + gemini-2.0-flash + print diagnostics` |
| `louannduclos-max/stellav1front` | main | `fix: apercu PDF - ne plus bloquer sur Chargement si pas de PDF` |

---

## ENV VARS RENDER (stella-backend)

| Variable | Valeur / Note |
|----------|---------------|
| `SUPABASE_URL` | `https://exacjvbgtrejbjtttcsz.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Secret key projet `exacjvbgtrejbjtttcsz` ✅ mis à jour |
| `GOOGLE_PLACES_API_KEY` | GCP projet `stella-market-studies` |
| `GEMINI_API_KEY` | Google AI Studio (gratuit) |
| `WEBHOOK_SECRET` | Auth front→backend |
| `FRONT_WEBHOOK_URL` | `https://stellav1front.pages.dev/api/public/generation-webhook` |
| `GENERATION_WEBHOOK_SECRET` | Auth callback backend→front |
| `SLIDE_BUILDER_USE_AGENT` | `false` (layout_engine only) — voir section Sprint 5 |

---

## ENV VARS CF PAGES (stellav1front)

| Variable | Valeur / Note |
|----------|---------------|
| `SUPABASE_URL` | `https://utwjfsomblhupghbgvgv.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Secret key projet `utwjfsomblhupghbgvgv` ✅ mis à jour |
| `SUPABASE_PUBLISHABLE_KEY` | Publishable key projet `utwjfsomblhupghbgvgv` |
| `RENDER_BACKEND_URL` | `https://stella-backend-mtap.onrender.com` |
| `WEBHOOK_SECRET` | Même valeur que Render |
| `GENERATION_WEBHOOK_SECRET` | Même valeur que Render ✅ ajouté aujourd'hui |

---

## RÈGLES DE SÉCURITÉ — IMMUABLES

1. Aucune clé dans le code — uniquement env vars Render / CF Pages dashboard
2. `SUPABASE_SERVICE_ROLE_KEY` jamais dans le code front ni dans git
3. `GOOGLE_PLACES_API_KEY` backend uniquement
4. Jamais committer `.env` ou `.env.production`
5. Ne pas casser d'endpoint existant sans test

---

## SPRINT 5 — Consolidation architecture (30 juin 2026)

### Chantiers livrés

| # | Fichier(s) | Ce qui change |
|---|-----------|---------------|
| 0 | Render env var | `SLIDE_BUILDER_USE_AGENT=false` — rollback déterministe pur |
| 1 | `slides_5_0_builder.py` | Chemin unique : layout_engine → schema → [NarrativeAgent optionnel] → [QAAgent]. `slide_builder_agent` retiré du chemin actif (fichier conservé) |
| 2 | `app/schemas/slide_objects.py` (nouveau) | Schéma Pydantic unique + `validate_slide_objects()` branché dans export_pptx.py |
| 3 | `app/agents/qa_agent.py` (nouveau) | QA déterministe slot par slot : revert si texte vide, trop long, ou chiffre non tracé dans le manifest |
| 4 | `layout_engine_5_0.py` | Slot `analysis-narrative` (fill_with_narrative=True) dans Sidebar-Analysis — rempli par NarrativeAgent si actif, invisible sinon |
| 5 | `layout_engine_5_0.py` | `slide-separator` supprimé — trait sous titre = signature visuelle IA |
| 6 | `export_pptx.py` + `slide_data_builder_5_0.py` | Graphiques natifs PPTX éditables : camembert seniors (slide démographie), barres scores (slide SWOT). Données depuis métriques réelles uniquement |
| 7 | `tests/golden_check.py` (nouveau) | Test non-régression : slides vides, SWOT sans bullets, nombres mal formatés, débordements canvas |

### Pour activer le NarrativeAgent (pas encore fait)

1. `python tests/golden_check.py --save 371196f9-4513-4aff-90fc-4358b3624c61` (crée la fixture)
2. `python tests/golden_check.py` (doit passer en mode false)
3. Mettre `SLIDE_BUILDER_USE_AGENT=true` sur Render → Manual Deploy
4. Relancer une étude → vérifier golden check toujours OK

### Note frontend (prochain sprint)

Dans `StellaSlide5_0.tsx`, retirer les `borderLeft: "3px solid ..."` dans `KpiListRenderer` et `HighlightBoxRenderer`. Remplacer par `background: var(--stella-highlight)` sans bordure latérale.

---

## ✅ E2E SPRINT DATA-DEPTH — BORDEAUX V4 VALIDÉ (1er juillet 2026)

**Commit :** `c534183` — backend Render déployé ✅
**Étude test :** ID `65585b75-b51d-4cf8-a5e9-dd734f898f3d` (Interdomicilio — Bordeaux v4)

### Logs Render confirmant l'exécution des chantiers

```
10:45:37  POST /generate-study HTTP/1.1  200 OK
10:46:00  [benchmark] Références nationales périmées (BENCHMARKS_YEAR < 2026-1) — à revérifier
10:46:00  progress=50                              ← Phase 3 + enrichissement Data-Depth OK
10:46:05  [gemini_analyst] parsing réponse échoué → fallback template  ← Bug 2, connu
10:46:12  status=done  progress=100
```

| Étape | Résultat |
|-------|----------|
| Pipeline complet (~37s) | ✅ |
| `benchmark_engine.enrich_metrics()` exécuté (log stale warning) | ✅ |
| `build_competitors_from_places()` — concurrents Places | ✅ |
| `get_funding_scale("FR")` — barème APA 2026 | ✅ |
| `market_sizing_engine.estimate()` | ✅ |
| 4 nouvelles clés manifest (`competitors_top`, `competitors_total_count`, `funding_scale`, `market_sizing`) | ✅ |
| PPTX généré — 74 Ko | ✅ |
| Téléchargement PPTX actif | ✅ |

> **Note :** Le log `[benchmark] Références nationales périmées` est le comportement **attendu** — `BENCHMARKS_YEAR=2024` et `2026-2024=2 > 1`. Il signale que les valeurs INSEE/DREES doivent être mises à jour pour 2025/2026.

---

## ✅ SPRINT DATA-DEPTH — LIVRÉ (1er juillet 2026)

**Commit :** `c534183` — backend Render déployé ✅

### Ce qui a été ajouté au pipeline

| Chantier | Fichier(s) | Apport manifest |
|----------|-----------|-----------------|
| 1 — Benchmark national | `core/national_benchmarks.py` + `services/benchmark_engine.py` | `metrics[*].national_benchmark`, `benchmark_interpretation`, `benchmark_year` |
| 2 — Concurrents nommés | `collectors/competition.py` : `build_competitors_from_places()` | `competitors_top` (≤10), `competitors_total_count` |
| 3 — Barème APA | `core/funding_scales.py` + `services/market_sizing_engine.py` | `funding_scale` (4 GIR CNSA 2026), `market_sizing` |
| 4 — Manifest | `services/master_json_builder.py` | 4 nouvelles clés top-level |
| 6 — QA | `services/qa_engine.py` | BENCH_001 (benchmark sans source), FUND_001 (barème mauvais pays) |

### Garde-fous
- `None` si pays sans barème (pas de slide financement inventée)
- `None` si données insuffisantes pour market_sizing
- Hypothèses DREES toujours exposées dans `market_sizing.hypotheses`
- `benchmarks_are_stale()` : log warning si `BENCHMARKS_YEAR < année-1`
- Dédup concurrents par nom normalisé (Places peut renvoyer doublons)

### Références à mettre à jour annuellement
- `app/core/national_benchmarks.py` → `BENCHMARKS_YEAR` + valeurs
- `app/core/funding_scales.py` → `FUNDING_SCALE_YEAR_FR` + montants APA (circulaire CNSA 1er janvier)

---

## BUGS — ÉTAT SPRINT 6

### ✅ Bug 0 — RÉSOLU Sprint 6 — isGenerating masquait le bouton Lancer

**Commit :** `4edb754` | **Déployé :** CF Pages ✅
Voir section "E2E Sprint 6" ci-dessus.

### 🟡 Bug 1 — wizard-submit timeout trop court face au cold start Render

**Symptôme :** Étude bloquée en "En attente…" côté UI, état réel "failed" dans Supabase. Aucun log POST `/generate-study` dans Render.

**Cause :**
- Render Free Tier hiberne après ~15 min → cold start ~50s
- `wizard-submit.server.ts` ligne ~416 : `signal: AbortSignal.timeout(15000)` → AbortError avant que Render réponde
- Bouton "↻ Relancer" n'apparaît que sur `status === "failed"`, pas "pending"

**Contournement actuel :** Ouvrir `https://stella-backend-mtap.onrender.com/` dans le navigateur avant de lancer une étude depuis le wizard (réveille Render). Si l'étude passe en "failed" : hard-refresh → bouton Relancer.

**Fix à appliquer :** `front/src/lib/wizard-submit.server.ts` ligne ~416
```ts
signal: AbortSignal.timeout(60000)  // était 15000
```

### 🟡 Bug 2 — Gemini réponse JSON tronquée

**Log Render (Sprint 6, 1er juillet) :**
```
[gemini_analyst] parsing réponse échoué : Unterminated string starting at: line 2 column 24 (char 25)
[gemini_analyst] Gemini n'a pas répondu — fallback template
```

Note : le log Sprint 5 montrait un HTTP 404 ("model no longer available"). En Sprint 6 il n'y a plus de 404 — le modèle répond, mais le JSON est malformé. Peut indiquer `gemini-2.0-flash` de nouveau disponible, ou un autre modèle déjà configuré.

**Impact :** Slides narratifs = template générique. PPTX structure OK.

**Fix :** Investiguer la réponse brute Gemini. Si modèle toujours 404 : passer à `gemini-2.5-flash`. Si réponse tronquée : augmenter `max_tokens` ou parser plus défensivement dans `gemini_analyst.py`.

---

## BACKLOG

### Priorité haute
- [ ] **Fix gemini JSON parse** : logger la réponse brute pour diagnostiquer, puis corriger `gemini_analyst.py`
- [ ] **Fix wizard timeout** : 15s → 60s dans `wizard-submit.server.ts` + push frontend
- [ ] **Run golden check** : `python tests/golden_check.py --save 18f460c9-...` puis `python tests/golden_check.py`
- [ ] **Slides Data-Depth** : brancher `competitors_top`, `funding_scale`, `market_sizing` dans `layout_engine_5_0.py` (nouvelles sections `competition_mapping`, `funding_feasibility`, `benchmark_comparison`)

### Court terme
- [ ] Activer NarrativeAgent (`SLIDE_BUILDER_USE_AGENT=true`) après golden check OK
- [ ] `html_renderer.py` : brancher `validate_slide_objects()` (mentionné spec Sprint 5, pas encore fait)
- [ ] Frontend : retirer `borderLeft: "3px solid ..."` dans `KpiListRenderer` + `HighlightBoxRenderer` (`StellaSlide5_0.tsx`)
- [ ] Barème ES (SAAD) dans `funding_scales.py` avant déploiement Interdomicilio Espagne
- [ ] Ajouter export PDF côté backend pour activer l'aperçu slides
- [ ] Supprimer les prints diagnostiques du code une fois le pipeline stable

### Moyen terme
- [ ] Migrer Render → Cloud Run (Dockerfile déjà présent) → pas de cold start
- [ ] RLS Supabase par `company_id` (multi-tenant réel)
- [ ] Dashboard analytics (coût par étude, temps de génération)

---

## APPRENTISSAGES OPÉRATIONNELS

### Deux projets Supabase distincts
- Backend (Render) → `exacjvbgtrejbjtttcsz` (louann-duclos)
- Frontend (CF Pages) → `utwjfsomblhupghbgvgv` (cowork)
- Chaque service a SA propre clé. Ne jamais croiser.

### Migration Supabase keys (23 juin 2026)
- Les anciennes JWT keys (`eyJ...`) sont désactivées. Nouvelles clés = `sb_publishable_...` / `sb_secret_...`
- Si une clé est rejetée → dashboard Supabase → Settings → API → re-copier la nouvelle clé

### CF Pages build failures silencieux
- Les fichiers TS tronqués ou corrompus dans le working tree ne bloquent pas `git push` mais font échouer le build TypeScript sur CF Pages sans message clair dans le dashboard
- Toujours vérifier avec `npx tsc --noEmit` avant de pousser

### Render Free Tier cold start
- Cold start ~50s après 15 min d'inactivité
- `wizard-submit.server.ts` a un timeout de **15s** → trop court → étude passe en "failed" silencieusement
- `generate-study.functions.ts` (bouton Relancer) a un timeout de **25s** → OK si backend déjà chaud
- Solution durable : migrer vers Cloud Run ou augmenter le timeout wizard à 60s

### UI Realtime peut manquer des événements Supabase
- Si la page étude est chargée pendant une transition d'état (pending→failed), la subscription WS peut rater l'UPDATE
- Hard-navigate (barre URL + Entrée) force un SSR re-fetch → fiable
- Navigation TanStack Router (links, router.push) = SPA → utilise le cache → peut afficher stale data

### SQL UPDATE "0 row" ≠ échec
- Supabase SQL Editor affiche "0 row" quand un UPDATE ne modifie aucune ligne parce que la valeur était déjà correcte
- Toujours faire un SELECT avant pour vérifier l'état réel avant de conclure à un problème

### Git + Windows + sandbox Linux
- Supprimer `.git/index.lock` avec bat Windows avant chaque push (`del /f /q`)
- Les fichiers restaurés via `git show HASH:path > file` reviennent en LF — warning CRLF ignorable

### Deux flows de création d'étude — comportement différent

| Flow | Crée l'étude | Appelle Render | Status initial |
|------|-------------|---------------|----------------|
| Wizard complet (6 étapes) | `wizard-submit.server.ts` | OUI (immédiat) | `pending` → Render démarre |
| "Nouvelle version" (dupliquer) | `createStudyVersion` | NON | `pending` → bouton Lancer requis |

Le bouton "🚀 Lancer la génération" est visible quand `canLaunch = !status || status === "draft" || status === "pending" || status === "failed"`. Ne jamais inclure `"pending"` dans `isGenerating` — cela masque le bouton sur les études issues du flow "Nouvelle version".

### Render deploy manuel recommandé
Ne pas attendre le déploiement automatique Render (peut prendre plusieurs minutes ou échouer silencieusement). Après chaque push backend : aller dans le dashboard Render → Manual Deploy → Deploy latest commit.
