# HANDOFF MANAGER — Stella V2.1
**Date :** 29 juin 2026  
**Session :** Sprint 3 backend + fixes déploiement  
**Rédigé par :** Claude Cowork (session du jour)

---

## ÉTAT ACTUEL — TOUT EN PRODUCTION

| Composant | URL | Commit HEAD | Statut |
|-----------|-----|-------------|--------|
| Backend | stella-backend-mtap.onrender.com | `f3c0790` | ✅ LIVE |
| Frontend | stellav1front.pages.dev | `c53c56b` | ✅ LIVE |
| DB | Supabase `utwjfsomblhupghbgvgv` | — | ✅ OK |

---

## CE QUI A ÉTÉ FAIT CETTE SESSION

### 1. Sprint 3 backend (4 chantiers)
- **geo_resolver branché** dans `consolidation_engine.py` : enrichit `geo_scope.region` (nom EPCI), `municipality_code`, `province` (dept) avant les collectors. Silencieux si API indisponible.
- **Endpoint probe Places** `GET /agents/debug/places-probe` : teste 9 keywords SAP sur une ville, retourne count par keyword. Confirmé 69 résultats pour Auray.
- **Flag SLIDE_BUILDER_USE_AGENT** : `os.environ.get("SLIDE_BUILDER_USE_AGENT", "true")` dans `slides_5_0_builder.py`. Peut désactiver l'agent en prod sans redeploy.
- **NarrativeAgent** : remplit les slots `fill_with_narrative=True` dans les objets slide. N'écrit jamais les positions. Fallback silencieux si Gemini indisponible.

### 2. NarrativeAgent → GEMINI_API_KEY (gratuit)
- Réécrit pour utiliser `GEMINI_API_KEY` (Google AI Studio, déjà configuré sur Render) au lieu de Vertex AI (payant, service account GCP requis).
- Aucune config supplémentaire requise — fonctionne dès maintenant.

### 3. CORS fix
- `stellav1front.pages.dev` ajouté aux origines autorisées dans `config.py`.
- Regex : `r"https://.*\.(lovable\.app|lovableproject\.com|pages\.dev)$"`.

### 4. Google Places API
- Keywords SAP mis à jour avec ceux validés par la probe (69 résultats pour Auray vs 0 avant).
- L'API "Places API (legacy)" a été activée dans GCP Console projet `stella-market-studies`.

### 5. CF Pages build corrigé
- Problème : build command était `npm install` au lieu de `npm run build` → dist jamais généré.
- Fix : changé dans CF Pages dashboard Settings. `wrangler.jsonc` ne peut PAS contenir la clé `"build"` (Pages-only restriction, Workers-only feature).

---

## ARCHITECTURE COURANTE

```
[User Browser]
    ↓ HTTPS
[CF Pages — stellav1front.pages.dev]  ← TanStack Start SSR, React
    ↓ POST /generate-study (Bearer WEBHOOK_SECRET)
[Render Free — stella-backend-mtap.onrender.com]  ← FastAPI Python
    ↓
[Supabase — utwjfsomblhupghbgvgv]  ← PostgreSQL + Auth
    ↓
[APIs externes : geo.api.gouv.fr, Google Places, INSEE/Filosofi...]
    ↓
[Gemini API — generativelanguage.googleapis.com]  ← narrative + analyse
```

**⚠️ Render free tier** : spin-down après 15 min d'inactivité → cold start ~50s sur la première requête.

---

## REPOS GIT

| Repo | Branche | Dernier commit |
|------|---------|---------------|
| `louannduclos-max/stella-backend` | main | `f3c0790` NarrativeAgent → GEMINI_API_KEY |
| `louannduclos-max/stella-front` (ou équivalent) | main | `c53c56b` revert wrangler.jsonc |

---

## ENV VARS RENDER (stella-backend)

| Variable | Valeur | Note |
|----------|--------|------|
| `GOOGLE_PLACES_API_KEY` | *** | GCP projet `stella-market-studies` |
| `GEMINI_API_KEY` | *** | Google AI Studio, gratuit |
| `SUPABASE_URL` | *** | |
| `SUPABASE_SERVICE_ROLE_KEY` | *** | Backend only, jamais frontend |
| `WEBHOOK_SECRET` | *** | Auth front→backend |
| `FRONT_WEBHOOK_URL` | *** | Callback backend→front |
| `GENERATION_WEBHOOK_SECRET` | *** | Auth callback |
| `SLIDE_BUILDER_USE_AGENT` | `true` | Peut passer à `false` pour désactiver NarrativeAgent |

---

## RÈGLES DE SÉCURITÉ — NE JAMAIS ENFREINDRE

1. **Aucune clé dans le code** — tout passe par les env vars Render
2. **`SUPABASE_SERVICE_ROLE_KEY` uniquement backend** — jamais dans le code front ni dans Supabase JS client
3. **`GOOGLE_PLACES_API_KEY` backend only** — jamais exposée au navigateur
4. **Ne jamais committer `.env`**
5. **Ne casser aucun endpoint existant** sans test préalable

---

## CE QUI RESTE À FAIRE (backlog)

### Court terme
- [ ] **Test end-to-end** : se connecter sur `stellav1front.pages.dev`, lancer une étude, vérifier progress bar → slides → PPTX téléchargeable
- [ ] **Vérifier logs Render** pendant une génération : chercher `[geo_resolver] EPCI:` et `[NarrativeAgent]` pour confirmer que les 2 pipelines sont actifs

### Moyen terme
- [ ] **Passer Cloud Run** : le Dockerfile est déjà dans le repo. Cloud Run = pas de cold start, meilleure fiabilité pour des vrais utilisateurs. Commande de deploy via `gcloud run deploy`.
- [ ] **RLS Supabase** : isoler les données par `company_id` (Sprint 4 Lot B était planifié — vérifier si implémenté ou stub)
- [ ] **Multi-tenant réel** : le `tenant_id` est dans les schémas mais la logique de routing par tenant dans les requêtes Supabase doit être auditée

### Long terme / Sprint 5 à planifier
- [ ] Authentification multi-company (plusieurs franchiseurs)
- [ ] Export PDF en plus du PPTX
- [ ] Dashboard analytics (études générées, conversion, etc.)

---

## APPRENTISSAGES OPÉRATIONNELS (pour le prochain Claude)

### Git sur Windows avec sandbox Linux
- Les `.bat` avec des espaces dans le chemin : utiliser **Parcourir...** dans Win+R — ajoute les guillemets automatiquement
- `index.lock` créé par le sandbox Linux : supprimer avec `del /f /q ".git\index.lock"` dans le bat, jamais depuis le sandbox
- Toujours mettre `if exist ".git\index.lock" del /f /q ".git\index.lock"` en première ligne de chaque bat de commit

### CF Pages
- La clé `"build"` dans `wrangler.jsonc` n'est **pas supportée** pour les projets Pages (Workers-only). Build command = Settings > Build > Build command dans le dashboard CF
- Le dashboard CF Pages utilise Shadow DOM → `document.body.innerText` toujours vide → utiliser les requêtes CF API avec `credentials: 'include'` depuis dash.cloudflare.com

### Google Places API
- Il faut activer "**Places API (legacy)**" (et non "Places API New") dans GCP Console
- Le projet GCP est `stella-market-studies` (pas `ouicare-stella-prod`)
- `google-auth-httpx` n'existe pas sur PyPI — utiliser seulement `google-auth>=2.28.0`

### Render
- Free tier ne déploie **pas automatiquement** sur push — toujours déclencher Manual Deploy via dashboard
- Service ID réel : `srv-d8t9a13eo5us73dejhv0` (projet `prj-d8t9a0v7f7vs73c0b570`)
- Cliquer Manual Deploy → "Deploy latest commit" depuis le dashboard Render

---

## FICHIERS CLÉS DU PROJET

```
stella V2.1/
├── app/
│   ├── agents/
│   │   ├── narrative_agent.py          ← NarrativeAgent (Gemini gratuit)
│   │   └── slide_builder_agent.py      ← SlideBuilderAgent (Vertex IA)
│   ├── api/routes/agents.py            ← Endpoints agents + probe Places
│   ├── core/config.py                  ← CORS origins + settings
│   ├── pipelines/run_study.py          ← Pipeline principal
│   ├── services/
│   │   ├── consolidation_engine.py     ← geo_resolver branché ici
│   │   ├── gemini_analyst.py           ← Analyse narrative (GEMINI_API_KEY)
│   │   ├── slides_5_0_builder.py       ← Builder slides + USE_AGENT flag
│   │   └── external/google_places_api.py ← Keywords SAP validés
│   └── services/collectors/geo_resolver.py ← EPCI / commune / dept
├── front/                              ← TanStack Start SSR
│   ├── src/
│   └── wrangler.jsonc                  ← CF Pages config (PAS de clé "build")
└── requirements.txt                    ← google-auth>=2.28.0 (pas google-auth-httpx)
```
