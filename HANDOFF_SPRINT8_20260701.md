# HANDOFF SPRINT 8 — Chemin B : Bascule HTML génératif
**Date :** 1er juillet 2026
**Commit :** À compléter après push_sprint8.bat
**Rédigé par :** Claude Cowork

---

## OBJECTIF DU SPRINT

Prouver que le HTML génératif fonctionne sur UNE slide riche (concurrence) avant d'engager les 15 slides. Le layout_engine PPTX reste le chemin principal — ce sprint est un test isolé via endpoint debug.

**Règle :** Rien ne se fait sur Gemini tant que Gemini n'est pas fiable. C'est pourquoi l'étape 1 (fix Gemini) était bloquante.

---

## CE QUI A ÉTÉ FAIT

### Étape 1 — Fix Gemini (bloquant) ✅

**Fichiers modifiés :**
- `app/services/gemini_analyst.py`
- `app/agents/narrative_agent.py`
- `app/agents/slide_builder_agent.py`

**Changements :**

| Problème | Avant | Après |
|----------|-------|-------|
| Modèle hardcodé | `gemini-2.0-flash` / `gemini-2.5-flash` | `GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")` |
| `maxOutputTokens` trop bas | 1024 (gemini_analyst) / 2000 (narrative) | 4096 partout |
| Parsing naïf | `json.loads(text)` crash si fence markdown | `_safe_parse_json()` : retire fences, tente jusqu'au dernier `}` valide |
| `lstrip("```json")` buggy (narrative_agent) | Strip caractères individuels | Remplacé par `re.sub()` correct |
| Diagnostic absent | Aucun log de la réponse brute | `logger.warning("[gemini] HTTP %s" + body 500 car.)` |

**Env var à ajouter sur Render :** `GEMINI_MODEL=gemini-2.5-flash`

**`_safe_parse_json()` (implémenté dans les deux fichiers) :**
```python
def _safe_parse_json(raw: str) -> dict | None:
    txt = raw.strip()
    txt = re.sub(r"^```json\s*", "", txt)
    txt = re.sub(r"^```\s*", "", txt)
    txt = re.sub(r"\s*```$", "", txt)
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        last = txt.rfind("}")
        if last > 0:
            try:
                return json.loads(txt[: last + 1])
            except json.JSONDecodeError:
                pass
    return None
```

### Étape 2 — Fix timeout wizard ✅ (déjà fait Sprint 6)

`front/src/lib/wizard-submit.server.ts` ligne 423 : `AbortSignal.timeout(60000)` — déjà à 60s.

### Étape 3 — Golden check étendu ✅

`tests/golden_check.py` — ajout de `_check_data_depth(study)` :
- Au moins une métrique avec `national_benchmark` non nul
- `study.competitors` non vide
- `study.funding_scale` présent pour une étude FR

**À lancer (après deploy Render) :**
```bash
python tests/golden_check.py --save 18f460c9-245b-4443-aa65-23eb2032089c
python tests/golden_check.py
```

### Étape 4 — Slide concurrence HTML (test décisif) ✅ (code livré)

**Fichiers créés :**

| Fichier | Rôle |
|---------|------|
| `app/skills/interdomicilio/skill.json` | Charte marque : couleurs #0095D9, polices Montserrat/Open Sans, CDN |
| `app/skills/interdomicilio/base_slide.html` | Squelette header/footer/CSS : kpi-row, comp-table, strategic-box, badges |
| `app/skills/interdomicilio/sections/competition.md` | Instructions layout tableau concurrentiel |
| `app/agents/html_slide_agent.py` | `HTMLSlideAgent.generate_main_content()` + `assemble_slide()` |
| `app/agents/qa_html_agent.py` | `validate_html()` — trace chaque nombre HTML dans le manifest |
| `app/api/routes/agents.py` | `GET /agents/debug/html-slide?study_id=...` |

**Endpoint de test :**
```
GET https://stella-backend-mtap.onrender.com/agents/debug/html-slide?study_id=18f460c9-245b-4443-aa65-23eb2032089c
```
- Si QA passe → retourne le HTML brut (ouvrir dans navigateur)
- Si QA échoue → retourne JSON `{qa_failed: true, untraceable_numbers: [...]}`

**Architecture `HTMLSlideAgent` :**
```
Manifest (section_data)
    │
    ▼
_build_prompt(instructions .md + données + classes CSS)
    │
    ▼
Gemini API (temperature=0.4, maxOutputTokens=4096)
    │
    ▼
HTML brut (bloc <main> uniquement)
    │
    ▼
validate_html(html, manifest) — QA déterministe
    │
    ├── OK → assemble_slide() → HTML complet (header + footer + CSS)
    └── FAIL → JSON {untraceable_numbers: [...]}
```

---

## PREUVE ÉTAPE 1 — LOG RENDER

> ⚠️ À compléter après deploy + génération d'une étude.

Logs Render attendus après fix :
```
[gemini_analyst] HTTP 200 model=gemini-2.5-flash
[gemini_analyst] BODY (500 premiers car.) : {"verdict_narrative": "...", ...
[gemini_analyst] narratifs Gemini générés pour study=... city=...
```
(Plus de `fallback template` ni `parsing réponse échoué`)

**Coller ici le log Render réel après le premier test :**
```
[À COMPLÉTER]
```

---

## PREUVE ÉTAPE 4 — SLIDE CONCURRENCE HTML

> ⚠️ À compléter après test visuel.

**URL testée :**
```
GET .../agents/debug/html-slide?study_id=18f460c9-245b-4443-aa65-23eb2032089c
```

**Résultat QA :** [ OK / FAIL — à compléter ]
**Nombres non tracés :** [ liste ou "aucun" ]

**HTML généré (extrait ≤ 20 lignes) :**
```html
[À COMPLÉTER]
```

**Capture navigateur :** [À joindre]

---

## VARIABLES ENV RENDER — MISES À JOUR

| Variable | Valeur | Action |
|----------|--------|--------|
| `GEMINI_MODEL` | `gemini-2.5-flash` | **À AJOUTER** sur Render dashboard |
| `SLIDE_BUILDER_USE_AGENT` | absent / `false` | Laisser tel quel — test via endpoint debug uniquement |

---

## DÉCISION APRÈS LE TEST

### Si slide belle + QA passe → Chemin B validé
Sprint suivant : généraliser aux 15 sections.
- Skill complet Interdomicilio (15 sections .md)
- Pipeline : `USE_HTML_SLIDE_AGENT=true` → HTMLSlideAgent remplace layout_engine pour les sections concernées
- Frontend : iframe ou `<embed>` pour afficher le HTML dans l'UI
- Export : LibreOffice headless PPTX → HTML → PNG slides (ou export direct HTML → PDF)

### Si rendu décevant ou QA bloque trop → Ajuster avant de généraliser
- Affiner `base_slide.html` (CSS, layout)
- Affiner `sections/competition.md` (instructions plus précises)
- Tester un autre modèle ou temperature
- Ne pas engager 15 slides sur une base bancale

---

## CE QUI N'A PAS ÉTÉ FAIT (hors scope Sprint 8)

- Pipeline principal : `HTMLSlideAgent` N'EST PAS branché dans `run_study.py` — test isolé uniquement
- Slides Data-Depth : `competitors_top`, `funding_scale`, `market_sizing` pas encore dans `layout_engine_5_0.py`
- Barème ES (SAAD) : `funding_scales.py` pas encore implémenté pour Espagne
- NarrativeAgent (`SLIDE_BUILDER_USE_AGENT=true`) : toujours désactivé — attendre golden check

---

## BACKLOG MIS À JOUR

### Haute priorité
- [ ] **Lancer push_sprint8.bat** + Manual Deploy Render + ajouter `GEMINI_MODEL=gemini-2.5-flash`
- [ ] **Test visuel** : GET `/agents/debug/html-slide?study_id=18f460c9-...` → capture navigateur
- [ ] **Golden check** : `python tests/golden_check.py --save 18f460c9-... && python tests/golden_check.py`
- [ ] **Compléter ce handoff** avec logs Render + capture slide

### Si Chemin B validé
- [ ] Skill complet Interdomicilio (14 autres sections .md)
- [ ] Brancher HTMLSlideAgent dans `run_study.py` derrière flag `USE_HTML_SLIDE_AGENT`
- [ ] Frontend : affichage HTML dans iframe StudyResultView

### Court terme (indépendant)
- [ ] Slides Data-Depth : brancher dans `layout_engine_5_0.py` (sections `competition_mapping`, `funding_feasibility`, `benchmark_comparison`)
- [ ] Barème ES (SAAD) dans `funding_scales.py`
- [ ] Frontend : retirer `borderLeft` dans KpiListRenderer + HighlightBoxRenderer
