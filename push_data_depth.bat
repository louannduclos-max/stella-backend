@echo off
cd /d "%~dp0"
del /f /q .git\index.lock 2>nul

git add ^
  app/api/schemas/common.py ^
  app/services/collectors/competition.py ^
  app/pipelines/run_study.py ^
  app/services/master_json_builder.py ^
  app/services/qa_engine.py ^
  app/core/national_benchmarks.py ^
  app/core/funding_scales.py ^
  app/services/benchmark_engine.py ^
  app/services/market_sizing_engine.py

git commit -m "feat(data-depth): benchmark national, concurrents nommes, bareme APA, market sizing

Chantier 1 - Benchmark national par metrique
- app/core/national_benchmarks.py : table de reference versionnee (source + year)
- app/services/benchmark_engine.py : enrich_metrics() avec interpretation relative
- app/api/schemas/common.py : Metric + 4 champs benchmark (national_benchmark, source, year, interpretation)
- app/pipelines/run_study.py : branchement apres Phase 2 collecte

Chantier 2 - Liste concurrentielle nommee
- app/api/schemas/common.py : schema Competitor
- app/services/collectors/competition.py : build_competitors_from_places() avec dedup par nom, tri directs/note
- Study.competitors alimente depuis Google Places live15 si disponible

Chantier 3 - Bareme financement APA + market sizing
- app/core/funding_scales.py : bareme APA 2026 CNSA (4 GIR + participation), extensible par pays
- app/services/market_sizing_engine.py : estimation deterministe marche prive adressable
- app/api/schemas/common.py : schema FundingScale, Study.funding_scale

Chantier 4 - Manifest enrichi
- app/services/master_json_builder.py : competitors_top, competitors_total_count, funding_scale, market_sizing

Chantier 6 - QA
- app/services/qa_engine.py : BENCH_001 (benchmark sans source), FUND_001 (bareme mauvais pays)

Garde-fous : None si pays sans bareme, None si donnees insuffisantes, hypotheses toujours exposees"

git push origin main
echo.
echo Push termine. Aller sur Render dashboard et cliquer Manual Deploy.
pause
