@echo off
cd /d "%~dp0"
del /f /q .git\index.lock 2>nul

git add ^
  app/api/routes/agents.py ^
  app/agents/sanitize.py ^
  app/agents/qa_html_agent.py ^
  app/services/slides_5_0_builder.py ^
  app/services/slide_cache.py ^
  app/services/external/google_places_api.py ^
  app/services/collectors/competition.py

git commit -m "feat(sprint9): Places dual-API + sanitize + QA v3 + resilience + cache

A.1 - Probe dual-API Places
- agents.py : GET /agents/debug/places-probe teste Legacy textsearch
  ET New Places API, retourne recommandation automatique
  (new_places_api.count > 0 → GOOGLE_PLACES_API_NEW=true)

A.2 - Collector New Places API (pret, active via GOOGLE_PLACES_API_NEW=true)
- google_places_api.py : GooglePlacesNewClient avec textQuery + pagination
  correcte (sleep(3) entre pages, max 3 pages = 60 resultats)
  Requetes localisees par pays (FR/ES)
- competition.py : bascule USE_NEW_PLACES_API → New API si flag actif
  Sinon Legacy Nearby Search (defaut inchange)

B - Securite : injection de prompt via noms Places
- app/agents/sanitize.py (NOUVEAU) : sanitize_external_text() retire
  les caracteres JSON/HTML ({} [] <> ` '') et patterns injection LLM
  sanitize_competitors_for_prompt() applique sur name/address/category
- agents.py debug/html-slide : sanitise competitors avant passage au LLM

C - QA renforce v3 (3 failles v2 comblee)
- app/agents/qa_html_agent.py REWRITE :
  1. Chiffres dans texte visible (herite Sprint 8)
  2. Donnees Chart.js dans data:[...] (faille v2 : graphiques non verifies)
  3. Heuristique red-flags : superlatifs non sources (leader, meilleur, etc.)
  Honnete sur les limites : QA reduit le risque, ne l'annule pas

D - Resilience pipeline (ThreadPoolExecutor, pas asyncio)
- slides_5_0_builder.py :
  USE_HTML_SLIDE_AGENT=true → ThreadPoolExecutor parallele les appels Gemini
  Circuit breaker thread-safe partage par etude (3 echecs → fallback total)
  _generate_one_html() : breaker + cache lookup + Gemini + QA + assemble
  _prepare_section_data() : donnees par section (sanitisees pour competition)
  Le deterministe PPTX est TOUJOURS construit → 15 slides garanties

E - Cache slide HTML
- app/services/slide_cache.py (NOUVEAU) :
  slide_cache_key() : SHA256 canonique (sort_keys + default=str + SKILL_VERSION)
  cache_get/cache_set : Supabase table slide_html_cache
  SKILL_VERSION=1.0.0 : bumper a chaque changement de skill

ACTIONS MANUELLES RENDER :
1. Manual Deploy apres ce push
2. GET https://stella-backend-mtap.onrender.com/agents/debug/places-probe?query=aide+a+domicile+Bordeaux
   → Si new_places_api.count > 0 : ajouter GOOGLE_PLACES_API_NEW=true
   → Si legacy_textsearch.count > 0 : laisser defaut (ne pas changer)
3. Creer table Supabase (backend : exacjvbgtrejbjtttcsz) :
   CREATE TABLE IF NOT EXISTS slide_html_cache (
     key TEXT PRIMARY KEY,
     html TEXT NOT NULL,
     created_at TIMESTAMPTZ DEFAULT now()
   );
4. USE_HTML_SLIDE_AGENT reste false — tester via /agents/debug/html-slide d'abord

NE PAS FAIRE :
- Ne pas activer USE_HTML_SLIDE_AGENT=true avant validation section par section
- Ne pas ajouter allow-same-origin sur iframe (XSS)
- Ne pas hardcoder la France pour Interdomicilio Espagne"

git push origin main
echo.
echo Push Sprint 9 termine.
echo.
echo === ACTIONS MANUELLES ===
echo 1. Render : Manual Deploy
echo 2. Tester : GET /agents/debug/places-probe?query=aide+a+domicile+Bordeaux
echo    → new_places_api.count ^> 0 → ajouter GOOGLE_PLACES_API_NEW=true sur Render
echo    → legacy_textsearch.count ^> 0 → ne rien changer
echo 3. Supabase backend (exacjvbgtrejbjtttcsz) : creer table slide_html_cache
echo    CREATE TABLE IF NOT EXISTS slide_html_cache (key TEXT PRIMARY KEY, html TEXT NOT NULL, created_at TIMESTAMPTZ DEFAULT now());
echo 4. Re-tester : GET /agents/debug/html-slide?study_id=18f460c9-245b-4443-aa65-23eb2032089c
echo.
pause
