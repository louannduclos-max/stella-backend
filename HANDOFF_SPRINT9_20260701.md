# HANDOFF SPRINT 9 — Collecte concurrentielle + HTML génératif production-ready
**Date :** 1er juillet 2026
**Rédigé par :** Claude Cowork

---

## OBJECTIF DU SPRINT

Rendre l'infrastructure HTML génératif "production-ready" avant de généraliser aux 15 slides.
8 chantiers : collecte Places fiable, sécurité injection, QA renforcé, résilience pipeline,
cache Gemini, multi-pays, iframe sécurisé.

**Règle du sprint :** Ne jamais passer à l'étape suivante sans la preuve de l'étape courante.

---

## CE QUI A ÉTÉ FAIT

### A.1 — Probe dual-API Google Places ✅

**Fichier modifié :** `app/api/routes/agents.py`

Endpoint `GET /agents/debug/places-probe?query=...` — teste maintenant **deux APIs en parallèle** :

| API | Endpoint | Cas attendu |
|-----|----------|-------------|
| Legacy Text Search | `maps.googleapis.com/maps/api/place/textsearch/json` | `REQUEST_DENIED` si clé provisionnée New seulement |
| New Places API | `places.googleapis.com/v1/places:searchText` | `count > 0` — cas attendu après rotation de clé |

Retourne une `recommendation` automatique :
- `NEW_API_OK` → activer `GOOGLE_PLACES_API_NEW=true` sur Render
- `LEGACY_OK` → bug dans collector (keyword/radius), pas dans l'API
- `BOTH_FAIL` → activer "Places API (New)" dans Google Cloud Console

**Test :**
```
GET https://stella-backend-mtap.onrender.com/agents/debug/places-probe?query=aide+a+domicile+Bordeaux
```

---

### A.2 — Collector New Places API ✅ (prêt, activation après probe)

**Fichier modifié :** `app/services/external/google_places_api.py`

Deux clients disponibles, bascule via flag Render :

```python
# Legacy (défaut) — inchangé
USE_NEW_PLACES_API = os.environ.get("GOOGLE_PLACES_API_NEW", "false").lower() == "true"
google_places = GooglePlacesClient()       # Nearby Search
google_places_new = GooglePlacesNewClient()  # Text Search + pagination
```

`GooglePlacesNewClient` — 4 pièges documentés dans le code :

| Piège | Implémentation |
|-------|---------------|
| **Facturation** | Field mask verrouillé : `displayName,formattedAddress,rating,userRatingCount,types,nextPageToken`. Ne jamais ajouter `reviews`/`editorialSummary` (Atmosphere tier = +cher). |
| **Schéma** | `displayName.text` (pas `name`), `formattedAddress` (pas `vicinity`), `userRatingCount` (pas `user_ratings_total`) → normalisés en legacy keys pour compatibilité |
| **Pagination** | Body reconstruit complet à chaque page (pas juste pageToken injecté) + `sleep(3)` obligatoire |
| **Clé API** | Recommandation : clé dédiée New API séparée de la Legacy |

Max 3 pages × 20 résultats = 60 acteurs par ville. Requêtes pays-conscientes FR/ES via `_competition_queries(city, country)`.

**Fichier modifié :** `app/services/collectors/competition.py`
- `_fetch_live()` accepte maintenant `city=` en plus de `lat/lon`
- Bascule `USE_NEW_PLACES_API` → New API ou Legacy selon flag
- Source title distinct dans logs : `"Google Places API (New) - Text Search acteurs SAP"` vs Legacy
- `source_id="google_places_new"` sur les objets `Competitor` (traçabilité)
- Note métrique distingue : New API = `count_30=count_15` (pas de rayon)

**Activation :**
1. Lancer le probe → `new_places_api.count > 0`
2. Ajouter `GOOGLE_PLACES_API_NEW=true` sur Render dashboard
3. Manual Deploy → tester une étude Bordeaux → vérifier `competitors_top` ≥ 5 acteurs réels

---

### B — Sanitisation injection de prompt ✅

**Fichier créé :** `app/agents/sanitize.py`

```python
sanitize_external_text(value, max_len=120)
    # Retire : { } [ ] < > ` " ' \
    # Retire : patterns injection LLM (ignore, disregard, system:, assistant:, ...)
    # Tronque à max_len

sanitize_competitors_for_prompt(competitors: list[dict])
    # Sanitise name, address, category de chaque concurrent
```

**Appliqué dans :** `app/api/routes/agents.py` (endpoint `debug/html-slide`) et `slides_5_0_builder.py` (`_prepare_section_data()` pour la section competition).

**Principe :** Le manifest Supabase garde les valeurs brutes (pour traçabilité QA). Seul ce qui va dans le PROMPT est sanitisé. Les champs numériques (rating, reviews_count) ne sont pas touchés.

---

### C — QA renforcé v3 ✅

**Fichier réécrit :** `app/agents/qa_html_agent.py`

Trois vérifications (vs une seule en v2) :

| Check | Cible | Faille v2 comblée |
|-------|-------|-------------------|
| `texte:` | Nombres dans le texte visible (hors CSS) | Non (déjà présent) |
| `chart:` | Données `data: [...]` dans les blocs `<script>` Chart.js | OUI — graphiques non vérifiés |
| `claim:` | Superlatifs non sourcés ("leader du marché", "le meilleur", etc.) | OUI — claims inventés |

**Note d'honnêteté** : ce QA est heuristique. Il réduit le risque d'hallucination, ne l'annule pas. Ne pas le présenter comme une preuve absolue.

Signature inchangée : `validate_html(html, manifest) -> tuple[bool, list[str]]`

---

### D — Résilience pipeline (ThreadPoolExecutor + circuit breaker) ✅

**Fichier modifié :** `app/services/slides_5_0_builder.py`

**POURQUOI ThreadPoolExecutor et PAS asyncio :**
Le pipeline Stella est synchrone (FastAPI sync, collectors httpx sync). Injecter de l'async casserait tout. ThreadPoolExecutor est le seul choix compatible.

**Circuit breaker thread-safe (faille v2 corrigée) :**
```python
class _Breaker:
    # Partage entre les threads via self.lock (threading.Lock)
    # 3 échecs Gemini consécutifs → is_open=True
    # Toutes les slides restantes → fallback immédiat (pas d'attente N×timeout)
```
Le breaker est stocké dans `_breakers[study_id]` (dict module-level, protégé par `_breakers_lock`). Partagé par étude, pas par slide.

**`_prepare_section_data(study, section_id, manifest)` :**
Prépare uniquement les données pertinentes pour chaque section. Sanitise les concurrents. Ne passe jamais le manifest complet au LLM.

**Sections mappées :** `competition`, `executive_summary`, `benchmark_comparison`, `funding_feasibility`. Les autres reçoivent les 8 premières métriques brutes (à compléter sprint par sprint).

**INVARIANT garanti :** Le déterministe PPTX est TOUJOURS construit. `html_content=None` → renderer frontend utilise le PPTX. 15 slides garanties même si Gemini tombe.

**Env vars :**

| Variable | Valeur | Effet |
|----------|--------|-------|
| `USE_HTML_SLIDE_AGENT` | `false` (défaut) | Chemin déterministe seul |
| `USE_HTML_SLIDE_AGENT` | `true` | Chemin B actif (HTML génératif) |
| `HTML_AGENT_PARALLELISM` | `5` (défaut) | Threads parallèles Gemini |

---

### E — Cache slide HTML ✅

**Fichier créé :** `app/services/slide_cache.py`

```python
SKILL_VERSION = "1.0.0"  # Bumper à chaque changement de skill

slide_cache_key(section_id, section_data) -> str
    # SHA256 canonique (sort_keys=True, default=str, ensure_ascii=True)
    # Préfixe SKILL_VERSION → invalide cache si skill change
    # Retourne "slide_html:{20_chars_hex}"

cache_get(key) -> str | None   # Supabase table slide_html_cache
cache_set(key, html) -> None   # upsert silencieux en cas d'erreur
```

**Table Supabase à créer sur le backend (`exacjvbgtrejbjtttcsz`) :**
```sql
CREATE TABLE IF NOT EXISTS slide_html_cache (
  key TEXT PRIMARY KEY,
  html TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

**Faille v2 corrigée :** La clé v2 utilisait `json.dumps()` sans précautions → instable sur les objets Pydantic/dates. La clé v3 est stable et déterministe.

---

### G — Iframe sécurisé (XSS) — Décision documentée

**Frontend (`StellaSlide5_0.tsx`) — à implémenter quand `html_content` branché :**
```tsx
<iframe
  srcDoc={slide.html_content}
  sandbox="allow-scripts"   // PAS allow-same-origin
  referrerPolicy="no-referrer"
  style={{ width: 1280, height: 720, border: "none" }}
/>
```

**Pourquoi PAS `allow-same-origin` :** `allow-scripts` + `allow-same-origin` = accès DOM parent = XSS. Sans `allow-same-origin`, l'iframe est dans une origine opaque. Chart.js fonctionne dans une origine opaque.

---

## PREUVES À COMPLÉTER APRÈS DEPLOY

### Probe Places API
```
GET https://stella-backend-mtap.onrender.com/agents/debug/places-probe?query=aide+a+domicile+Bordeaux
```
Coller ici le résultat :
```json
[À COMPLÉTER]
```
Recommandation : `[ ]`

### Slide HTML concurrence (après probe + activ. éventuelle New API)
```
GET https://stella-backend-mtap.onrender.com/agents/debug/html-slide?study_id=18f460c9-245b-4443-aa65-23eb2032089c
```
Résultat QA : `[ OK / FAIL ]`
Issues : `[ liste ou "aucune" ]`

---

## ACTIONS MANUELLES RESTANTES

- [x] **Render : Manual Deploy** (sprint 9 pushé + live)
- [ ] **Supprimer `.git/index.lock`** si présent + pusher le fix Places spec :
  ```bat
  del "D:\claude\stella\stella V2.1\.git\index.lock"
  cd "D:\claude\stella\stella V2.1"
  git add app/services/external/google_places_api.py app/services/collectors/competition.py
  git commit -m "fix(places-new): pagination body rebuild + source_id traceability"
  git push
  ```
- [ ] **Probe Places** → GET `/agents/debug/places-probe?query=aide+a+domicile+Bordeaux`
  - Si `NEW_API_OK` → ajouter `GOOGLE_PLACES_API_NEW=true` + redeploy
  - Si `LEGACY_OK` → ne rien changer (bug collector ailleurs)
- [ ] **Créer table Supabase** `slide_html_cache` (SQL ci-dessus)
- [ ] **Retester** `/agents/debug/html-slide?study_id=18f460c9-...`

---

## CE QUI N'A PAS ÉTÉ FAIT (hors scope Sprint 9)

- **F — Slides HTML section par section** : `competition` seule est implémentée. Les 14 autres sections `.md` restent à créer (sprint suivant, dans l'ordre : `executive_summary`, `benchmark_comparison`, etc.)
- **`USE_HTML_SLIDE_AGENT=true`** : ne pas activer avant validation section par section
- **Frontend iframe** : pas encore câblé (`html_content` existe dans le payload mais le renderer l'ignore)
- **Barème ES (SAAD)** : `funding_scales.py` pas encore implémenté pour Espagne
- **Benchmarks INE (Espagne)** : `national_benchmarks.py` FR uniquement pour l'instant

---

## BACKLOG MIS À JOUR

### Immédiat (dépend du probe)
- [ ] Probe → décision API → si New : `GOOGLE_PLACES_API_NEW=true` + redeploy + test étude Bordeaux
- [ ] Créer table `slide_html_cache` Supabase backend

### Sprint 10 — Généralisation HTML (si probe OK + slide competition validée)
- [ ] `sections/executive_summary.md` → test → valider
- [ ] `sections/benchmark_comparison.md` → test → valider
- [ ] `sections/funding_feasibility.md` → test → valider
- [ ] Répéter pour les 11 sections restantes
- [ ] Activer `USE_HTML_SLIDE_AGENT=true` quand ≥ 10 sections validées
- [ ] Frontend : iframe `sandbox="allow-scripts"` dans `StellaSlide5_0.tsx`
- [ ] Bumper `SKILL_VERSION` dans `slide_cache.py` à chaque changement de skill

### Court terme (indépendant)
- [ ] Slides Data-Depth : brancher `competitors_top`, `funding_scale`, `market_sizing` dans `layout_engine_5_0.py`
- [ ] NarrativeAgent (`SLIDE_BUILDER_USE_AGENT=true`) après golden check OK
- [ ] Barème ES (SAAD) dans `funding_scales.py`
- [ ] Frontend : retirer `borderLeft` dans `KpiListRenderer` + `HighlightBoxRenderer`

---

## RAPPELS SÉCURITÉ (invariants)

- **Ne jamais** injecter un nom Places non sanitisé dans un prompt LLM
- **Ne jamais** mettre `allow-same-origin` sur l'iframe HTML slide
- **Ne pas** activer `USE_HTML_SLIDE_AGENT=true` avant validation section par section
- **Ne pas** présenter le QA comme une preuve absolue d'absence d'hallucination
- **Ne pas** hardcoder la France (Interdomicilio = Espagne)
- **Bumper `SKILL_VERSION`** à chaque modification de `base_slide.html` ou `sections/*.md`
