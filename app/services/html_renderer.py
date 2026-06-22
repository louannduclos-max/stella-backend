from app.api.schemas.common import Study
from app.core.brand_profiles import get_brand_profile
from app.services.master_json_builder import master_json_builder


# Palette par défaut (charte O2)
DEFAULT_PALETTE = {
    "primary": "#0066CC",
    "primary_dark": "#003D7A",
    "text": "#2C2C2C",
    "accent": "#00CC66",
    "alert": "#FF3333",
    "warn": "#FF9900",
}
DEFAULT_FONT = "Arial, Helvetica, sans-serif"
GREY_LIGHT = "#F0F0F0"

VERDICT_LABELS = {
    "GO": "OUI - GO",
    "GO_CONDITIONAL": "OUI SOUS CONDITIONS",
    "NO_GO": "NO-GO",
}


def _fmt(value, unit=None):
    if isinstance(value, bool):
        txt = "Oui" if value else "Non"
    elif isinstance(value, (int, float)):
        if isinstance(value, float) and not float(value).is_integer():
            txt = f"{value:,.1f}".replace(",", " ").replace(".", ",")
        else:
            txt = f"{int(value):,}".replace(",", " ")
    else:
        txt = str(value)
    return f"{txt} {unit}" if unit and unit != "bool" else txt


class HtmlRenderer:
    def render(self, study: Study, brand_slug: str | None = None) -> str:
        data = master_json_builder.build(study)
        s = data["study"]
        geo = s["geo_scope"]
        biz = s["business_context"]
        country = s["country"]
        verdict = s.get("verdict") or "N/A"

        # Résolution profil entreprise : explicite -> slug brand_name -> défaut
        profile = None
        if brand_slug:
            profile = get_brand_profile(brand_slug)
        if not profile and biz.get("brand_name"):
            profile = get_brand_profile(biz["brand_name"].lower().split()[0])

        palette = (profile or {}).get("palette") or DEFAULT_PALETTE
        font_family = (profile or {}).get("font_family") or DEFAULT_FONT
        O2_BLUE = palette["primary"]
        O2_BLUE_DARK = palette["primary_dark"]
        GREY_DARK = palette["text"]
        GREEN_POS = palette.get("accent", "#00CC66")
        RED_ALERT = palette.get("alert", "#FF3333")
        ORANGE_WARN = palette.get("warn", "#FF9900")
        HIGHLIGHT = "#E6F2FF"
        VERDICT_COLORS_LOCAL = {
            "GO": GREEN_POS,
            "GO_CONDITIONAL": ORANGE_WARN,
            "NO_GO": RED_ALERT,
        }
        verdict_color = VERDICT_COLORS_LOCAL.get(verdict, GREY_DARK)
        verdict_label = VERDICT_LABELS.get(verdict, verdict)
        brand_display = (profile or {}).get("brand_name") or biz.get("brand_name", "")

        metrics_by_id = data["metrics"]["by_id"]

        def m(mid):
            return metrics_by_id.get(mid)

        def mv(mid, default="—"):
            mm = m(mid)
            return _fmt(mm["value"], mm.get("unit")) if mm else default

        brand_flag = m("brand_presence_flag")
        franchise_count = m("franchise_brand_count")
        own_alert = ""
        if brand_flag and str(brand_flag["value"]).lower() in {"true", "1"}:
            own_alert = (
                f"<div class='box-alert'>⚠️ <b>ALERTE CRITIQUE</b> — Présence d'un grand réseau "
                f"({biz['brand_name']} ou concurrent direct) détectée sur le périmètre. "
                f"Obstacle territorial probable.</div>"
            )

        # Synthèse KPI (section 2)
        synth_rows = [
            ("Population totale", mv("population_total")),
            ("Seniors 60+", mv("seniors_60_plus_share")),
            ("Revenu médian", mv("median_income")),
            ("Prix m² maison", mv("real_estate_price_house_m2")),
            ("Résidences secondaires", mv("secondary_residences_share")),
            ("Concurrents 15 min", mv("competitor_count_15min")),
            ("Franchises présentes", mv("franchise_brand_count")),
            ("Tarif APA/SAAD local", mv("apa_hourly_rate")),
            ("Verdict", verdict_label),
        ]
        synth_html = "".join(
            f"<tr><td>{label}</td><td><b>{value}</b></td></tr>" for label, value in synth_rows
        )

        # Sources (section 3)
        src_rows = "".join(
            f"<tr><td>{src['theme_id']}</td><td>{src['publisher'] or src['title']}</td>"
            f"<td>{src['freshness_level']}</td></tr>"
            for src in data["sources"]["items"][:10]
        )

        # Démographie (section 4)
        demo_ids = [
            "population_total", "population_growth_5y", "density_population",
            "seniors_60_plus_share", "seniors_75_plus_share",
            "households_with_children_share", "single_senior_households",
            "dependency_ratio_apa", "working_age_women_share",
        ]
        demo_rows = "".join(
            f"<tr><td>{m(mid)['label']}</td><td><b>{_fmt(m(mid)['value'], m(mid).get('unit'))}</b></td>"
            f"<td><span class='conf c-{m(mid)['confidence_grade']}'>{m(mid)['confidence_grade']}</span></td></tr>"
            for mid in demo_ids if m(mid)
        )

        # Emploi & RH (section 5)
        emp_ids = ["unemployment_rate", "care_worker_pool", "jobseekers_service_sector", "working_age_women_share"]
        emp_rows = "".join(
            f"<tr><td>{m(mid)['label']}</td><td><b>{_fmt(m(mid)['value'], m(mid).get('unit'))}</b></td>"
            f"<td><span class='conf c-{m(mid)['confidence_grade']}'>{m(mid)['confidence_grade']}</span></td></tr>"
            for mid in emp_ids if m(mid)
        )
        mob_ids = ["car_dependency_share", "rush_hour_penalty", "travel_time_spread", "parking_constraint_index"]
        mob_rows = "".join(
            f"<tr><td>{m(mid)['label']}</td><td><b>{_fmt(m(mid)['value'], m(mid).get('unit'))}</b></td></tr>"
            for mid in mob_ids if m(mid)
        )

        # Économie & habitat (section 6)
        econ_ids = [
            "median_income", "taxable_households_share",
            "real_estate_price_house_m2", "real_estate_price_apartment_m2",
            "rental_price_m2", "real_estate_price_growth_5y",
            "houses_vs_apartments_share", "avg_house_surface",
            "home_ownership_share", "tenants_share", "secondary_residences_share",
            "real_estate_premium_zone_share",
        ]
        econ_rows = "".join(
            f"<tr><td>{m(mid)['label']}</td><td><b>{_fmt(m(mid)['value'], m(mid).get('unit'))}</b></td>"
            f"<td><span class='conf c-{m(mid)['confidence_grade']}'>{m(mid)['confidence_grade']}</span></td></tr>"
            for mid in econ_ids if m(mid)
        )

        # Tourisme (section 7)
        tour_ids = ["tourism_overnight_stays", "tourism_seasonality_index", "seasonal_revenue_multiplier", "secondary_residences_share"]
        tour_rows = "".join(
            f"<tr><td>{m(mid)['label']}</td><td><b>{_fmt(m(mid)['value'], m(mid).get('unit'))}</b></td></tr>"
            for mid in tour_ids if m(mid)
        )

        # Concurrence (section 8)
        comp_ids = [
            "competitor_count_15min", "competitor_count_30min",
            "franchise_brand_count", "association_competitor_count",
            "ccas_presence_flag", "recent_openings_2y",
            "top_competitor_density",
        ]
        comp_rows = "".join(
            f"<tr><td>{m(mid)['label']}</td><td><b>{_fmt(m(mid)['value'], m(mid).get('unit'))}</b></td>"
            f"<td><span class='conf c-{m(mid)['confidence_grade']}'>{m(mid)['confidence_grade']}</span></td></tr>"
            for mid in comp_ids if m(mid)
        )

        # Pricing
        price_ids = ["avg_hourly_price_cleaning", "avg_hourly_price_care", "regulated_saad_rate"]
        price_rows = "".join(
            f"<tr><td>{m(mid)['label']}</td><td><b>{_fmt(m(mid)['value'], m(mid).get('unit'))}</b></td></tr>"
            for mid in price_ids if m(mid)
        )

        # Réglementation (section 9)
        reg_ids = ["regulatory_barrier_level", "saad_authorization_required", "public_aid_coverage", "apa_hourly_rate"]
        reg_rows = "".join(
            f"<tr><td>{m(mid)['label']}</td><td><b>{_fmt(m(mid)['value'], m(mid).get('unit'))}</b></td></tr>"
            for mid in reg_ids if m(mid)
        )

        # Microzones
        micro = data.get("microzones") or {}
        neighborhoods = micro.get("neighborhoods", [])[:12]
        neigh_rows = "".join(
            f"<tr><td>{n.get('name','')}</td><td>{n.get('density_profile','')}</td>"
            f"<td>{n.get('premium_score',0)}/100</td>"
            f"<td>{'⭐ premium' if n.get('is_premium') else '—'}</td></tr>"
            for n in neighborhoods
        )

        # Scores (utilisés en synthèse exécutive)
        score_rows = "".join(
            f"<tr><td>{sc['label']}</td><td><b>{sc['value']:.0f}</b>/100</td>"
            f"<td>{sc['weight']}</td>"
            f"<td><span class='conf c-{sc['confidence_grade']}'>{sc['confidence_grade']}</span></td></tr>"
            for sc in data["scores"]["items"]
        )

        # SWOT (section 10)
        def swot_li(items):
            return "".join(f"<li>{x}</li>" for x in items)

        strengths = [
            f"Population {mv('population_total')} - marché local solide",
            f"Seniors 60+ : {mv('seniors_60_plus_share')} - cœur cible SAP",
            f"Revenu médian {mv('median_income')} - solvabilité",
            f"Vivier RH : {mv('care_worker_pool')} profils mobilisables",
            f"Marque {biz['brand_name']} (modèle {biz['business_model']})",
        ]
        weaknesses = [
            f"Concurrents 15 min : {mv('competitor_count_15min')}",
            f"Franchises présentes : {mv('franchise_brand_count')}",
            "Tarifs > associations (CCAS/ADMR)",
            f"Dépendance auto : {mv('car_dependency_share')}",
        ]
        opportunities = [
            f"Résidences secondaires {mv('secondary_residences_share')} - niche premium",
            f"Silver économie : {mv('dependency_ratio_apa')} bénéficiaires APA estimés",
            f"Quartiers premium identifiés : {mv('premium_neighborhoods_count')}",
            "Diversification seniors / familles monoparentales",
        ]
        threats = [
            "Saisonnalité (haute saison vs basse saison)",
            f"Barrière réglementaire : {mv('regulatory_barrier_level')}",
            "Concurrence employeurs saisonniers",
            f"Ouvertures récentes 2 ans : {mv('recent_openings_2y')}",
        ]

        # Plan d'action
        action_rows = """
        <tr><td><b>CRITIQUE</b></td><td>Validation territoriale réseau</td><td>S1-S2</td><td>Confirmer zone disponible / exclusivité.</td></tr>
        <tr><td><b>CRITIQUE</b></td><td>Étude microzones premium</td><td>S2-S3</td><td>Quartiers premium déjà identifiés.</td></tr>
        <tr><td>HAUTE</td><td>Sourcing RH ciblé</td><td>M1</td><td>Mères isolées, écoles, CCAS, associations.</td></tr>
        <tr><td>HAUTE</td><td>Solutions mobilité</td><td>M1-M2</td><td>Pool véhicules, sectorisation 5-10 km.</td></tr>
        <tr><td>MOYENNE</td><td>Pricing local</td><td>M2</td><td>Positionnement vs concurrents et tarif SAAD.</td></tr>
        <tr><td>MOYENNE</td><td>Plan B alternatives</td><td>M2</td><td>Si blocage, étudier enseigne alternative.</td></tr>
        <tr><td>BASSE</td><td>Autorisation SAAD</td><td>M3</td><td>Dossier anticipé selon décision GO.</td></tr>
        """

        # CSS dynamique selon palette brand + asymétrie Diapositive 5.0
        css = f"""
        *{{box-sizing:border-box;}}
        html,body{{margin:0;padding:0;font-family:{font_family};color:{GREY_DARK};
                   background:#e2e8f0;}}
        .page{{width:210mm;min-height:297mm;background:#fff;margin:8mm auto;padding:20mm;
               box-shadow:0 6px 18px rgba(0,0,0,.15);position:relative;line-height:1.4;
               font-size:11pt;text-align:justify;}}
        h1{{font-size:24pt;font-weight:bold;color:{O2_BLUE};margin:0 0 4pt 0;text-align:left;}}
        h2{{font-size:18pt;font-weight:bold;color:{O2_BLUE_DARK};margin:18pt 0 8pt 0;
            padding:6pt 0 4pt 0;border-bottom:3px solid {O2_BLUE};text-align:left;}}
        h3{{font-size:14pt;font-weight:bold;color:{GREY_DARK};margin:12pt 0 6pt 0;text-align:left;}}
        p{{margin:6pt 0;}}
        ul{{margin:6pt 0 6pt 18pt;padding:0;}}
        li{{margin:3pt 0;}}
        table{{width:100%;border-collapse:collapse;font-size:10pt;margin:6pt 0 10pt 0;
               border:2px solid {O2_BLUE};}}
        th{{background:{O2_BLUE};color:#fff;font-weight:bold;padding:8px 10px;text-align:left;
            border:1px solid #CCC;}}
        td{{padding:6px 8px;border:1px solid #CCC;vertical-align:top;}}
        tbody tr:nth-child(even) td{{background:{GREY_LIGHT};}}
        tr.hl td{{background:{HIGHLIGHT};}}
        .conf{{display:inline-block;padding:1px 6px;border-radius:3px;font-size:9pt;
               font-weight:bold;color:#fff;}}
        .c-A{{background:{GREEN_POS};}} .c-B{{background:#22a85a;}}
        .c-C{{background:{ORANGE_WARN};}} .c-D{{background:#f97316;}}
        .c-E{{background:{RED_ALERT};}}
        .box-alert{{background:#FFE6E6;border-left:5px solid {RED_ALERT};padding:10pt 12pt;
                     margin:8pt 0;font-weight:bold;}}
        .box-info{{background:{HIGHLIGHT};border-left:5px solid {O2_BLUE};padding:10pt 12pt;
                    margin:8pt 0;}}
        .box-pos{{background:#E6FFED;border-left:5px solid {GREEN_POS};padding:10pt 12pt;
                   margin:8pt 0;}}
        .box-warn{{background:#FFF4E6;border-left:5px solid {ORANGE_WARN};padding:10pt 12pt;
                    margin:8pt 0;}}
        .verdict{{display:inline-block;padding:8px 18px;border-radius:6px;color:#fff;
                   font-weight:bold;font-size:14pt;background:{verdict_color};}}
        .swot{{display:grid;grid-template-columns:1fr 1fr;gap:10pt;}}
        .swot .q{{padding:10pt 12pt;border-radius:6px;}}
        .swot .forces{{background:#E6FFED;border:1px solid {GREEN_POS};}}
        .swot .forces h3{{color:{GREEN_POS};margin-top:0;}}
        .swot .faiblesses{{background:#FFE6E6;border:1px solid {RED_ALERT};}}
        .swot .faiblesses h3{{color:{RED_ALERT};margin-top:0;}}
        .swot .opportunites{{background:{HIGHLIGHT};border:1px solid {O2_BLUE};}}
        .swot .opportunites h3{{color:{O2_BLUE};margin-top:0;}}
        .swot .menaces{{background:#FFF4E6;border:1px solid {ORANGE_WARN};}}
        .swot .menaces h3{{color:{ORANGE_WARN};margin-top:0;}}
        .cover-asym{{display:grid;grid-template-columns:70% 30%;gap:14mm;height:100%;align-items:start;
                     padding-top:30mm;}}
        .cover-left{{border-left:6px solid {O2_BLUE};padding-left:14pt;}}
        .cover-eyebrow{{font-size:11pt;font-weight:bold;letter-spacing:2pt;text-transform:uppercase;
                        color:{O2_BLUE_DARK};margin-bottom:14pt;}}
        .cover-mega{{font-family:{font_family};font-size:72pt;font-weight:900;line-height:1;
                     color:{O2_BLUE};margin:0;letter-spacing:-2pt;}}
        .cover-sub{{font-size:14pt;color:{GREY_DARK};margin-top:10pt;}}
        .cover-brand{{font-size:18pt;font-weight:bold;color:{O2_BLUE_DARK};margin-top:18pt;
                      padding-top:8pt;border-top:2px solid {O2_BLUE};display:inline-block;}}
        .cover-right{{display:flex;flex-direction:column;gap:14pt;}}
        .cover-stamp{{background:{O2_BLUE};color:#fff;border-radius:10pt;padding:14pt;
                      text-align:center;}}
        .cover-stamp-label{{font-size:10pt;text-transform:uppercase;letter-spacing:1pt;opacity:.85;}}
        .cover-stamp-value{{font-size:54pt;font-weight:900;line-height:1;margin-top:4pt;}}
        .cover-stamp-out{{font-size:11pt;opacity:.85;}}
        .cover-meta{{display:flex;flex-direction:column;gap:8pt;font-size:10pt;
                     background:{GREY_LIGHT};border-radius:8pt;padding:12pt;}}
        .cover-meta b{{color:{O2_BLUE_DARK};}}
        .footer{{position:absolute;bottom:10mm;left:20mm;right:20mm;font-size:9pt;color:#888;
                  border-top:1px solid #CCC;padding-top:4pt;display:flex;justify-content:space-between;}}
        @media print{{
          body{{background:#fff;}}
          .page{{box-shadow:none;margin:0;page-break-after:always;}}
        }}
        """

        return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<title>Étude SAP — {geo['city']} ({country}) — Stella</title>
<style>{css}</style></head>
<body>

<!-- 1. PAGE DE COUVERTURE - asymétrie 70/30 -->
<section class="page">
  <div class="cover-asym">
    <div class="cover-left">
      <div class="cover-eyebrow">ÉTUDE DE MARCHÉ & FAISABILITÉ SAP</div>
      <div class="cover-mega">{geo['city']}</div>
      <div class="cover-sub">{geo.get('region') or ''} · {country} · {s['study_date']}</div>
      <div class="cover-brand">{brand_display}</div>
      <div style="margin-top:24pt;"><span class="verdict">{verdict_label}</span></div>
    </div>
    <div class="cover-right">
      <div class="cover-stamp">
        <div class="cover-stamp-label">Score global</div>
        <div class="cover-stamp-value">{sum(sc['value'] * sc['weight'] for sc in data['scores']['items']) / 100:.0f}</div>
        <div class="cover-stamp-out">/ 100</div>
      </div>
      <div class="cover-meta">
        <div><b>Modèle</b><br>{biz['business_model']}</div>
        <div><b>Positionnement</b><br>{biz['positioning_mode']}</div>
        <div><b>Périmètre</b><br>{', '.join(geo.get('postal_codes') or []) or 'commune'}</div>
      </div>
    </div>
  </div>
  <div class="footer"><span>Stella · {s['study_id']}</span><span>1 / 10</span></div>
</section>

<!-- 2. SYNTHÈSE EXÉCUTIVE -->
<section class="page">
  <h1>Synthèse exécutive</h1>
  {own_alert}
  <h3>Territoire</h3>
  <p>{geo['city']} ({country}), {geo.get('region') or ''}.
     Périmètre : {", ".join(geo.get('postal_codes') or []) or 'commune'}.
     Modèle : <b>{biz['business_model']}</b>. Positionnement : <b>{biz['positioning_mode']}</b>.</p>

  <h3>Opportunité démographique</h3>
  <p>Population {mv('population_total')}. Seniors 60+ : <b>{mv('seniors_60_plus_share')}</b>.
     Revenu médian <b>{mv('median_income')}</b>. Résidences secondaires : {mv('secondary_residences_share')}.</p>

  <h3>Défi concurrence</h3>
  <p>Concurrents à 15 min : <b>{mv('competitor_count_15min')}</b>.
     Franchises présentes : {mv('franchise_brand_count')}. Associations : {mv('association_competitor_count')}.</p>

  <h3>Tableau KPI synthétique</h3>
  <table><thead><tr><th>Indicateur</th><th>Valeur</th></tr></thead><tbody>{synth_html}</tbody></table>

  <div class="box-info"><b>Verdict :</b> {verdict_label}.</div>
  <div class="footer"><span>Stella · Synthèse</span><span>2 / 10</span></div>
</section>

<!-- 3. MÉTHODOLOGIE -->
<section class="page">
  <h1>Méthodologie</h1>
  <p>Étude générée par le moteur Stella. Collecte multi-sources : démographie, emploi, immobilier,
     concurrence locale, réglementation, mobilité, tourisme, pricing.</p>
  <h3>Sources principales</h3>
  <table><thead><tr><th>Domaine</th><th>Source</th><th>Fraîcheur</th></tr></thead>
  <tbody>{src_rows}</tbody></table>
  <div class="box-info">Chaque KPI est annoté d'un grade de confiance A→E.
     Les valeurs marquées <i>fallback</i> sont à raffermir par branchement API réel.</div>
  <h3>Scoreboard ({data['scores']['count']} sous-scores)</h3>
  <table><thead><tr><th>Sous-score</th><th>Valeur</th><th>Poids</th><th>Conf.</th></tr></thead>
  <tbody>{score_rows}</tbody></table>
  <div class="footer"><span>Stella · Méthodologie</span><span>3 / 10</span></div>
</section>

<!-- 4. ANALYSE DÉMOGRAPHIQUE -->
<section class="page">
  <h1>Analyse démographique</h1>
  <p>Profil territoire : {geo['city']} ({country}). Cible SAP prioritaire : 60+, familles monoparentales,
     résidences secondaires.</p>
  <table><thead><tr><th>KPI</th><th>Valeur</th><th>Conf.</th></tr></thead>
  <tbody>{demo_rows}</tbody></table>
  <div class="box-info"><b>Encadré seniors :</b> {mv('seniors_60_plus_share')} de 60+. Cœur de cible SAP.</div>
  <ul>
    <li>Ménages avec enfants : {mv('households_with_children_share')}</li>
    <li>Femmes 25-54 ans : {mv('working_age_women_share')}</li>
    <li>Ménages seniors seuls : {mv('single_senior_households')}</li>
    <li>Bénéficiaires APA estimés : {mv('dependency_ratio_apa')}</li>
  </ul>
  <div class="footer"><span>Stella · Démographie</span><span>4 / 10</span></div>
</section>

<!-- 5. EMPLOI / RH / MOBILITÉ -->
<section class="page">
  <h1>Emploi, chômage & RH · Mobilité</h1>
  <h3>KPI emploi</h3>
  <table><thead><tr><th>Indicateur</th><th>Valeur</th><th>Conf.</th></tr></thead>
  <tbody>{emp_rows}</tbody></table>
  <h3>Mobilité & opérations</h3>
  <table><thead><tr><th>Indicateur</th><th>Valeur</th></tr></thead>
  <tbody>{mob_rows}</tbody></table>
  <div class="box-alert">🚨 Dépendance auto {mv('car_dependency_share')} · pénalité heure de pointe
     {mv('rush_hour_penalty')} · dispersion trajet {mv('travel_time_spread')}.</div>
  <ul>
    <li>Cibler mères isolées (écoles, associations, CCAS)</li>
    <li>Pool véhicules de service · sectorisation 5-10 km</li>
    <li>Flexibilité horaire 8h30-16h30</li>
    <li>Formation interne (ADVF / DEAES)</li>
    <li>Rémunération > SMIC + primes</li>
  </ul>
  <div class="footer"><span>Stella · Emploi & Mobilité</span><span>5 / 10</span></div>
</section>

<!-- 6. ÉCONOMIE & HABITAT -->
<section class="page">
  <h1>Analyse économique & habitat</h1>
  <table><thead><tr><th>Indicateur</th><th>Valeur</th><th>Conf.</th></tr></thead>
  <tbody>{econ_rows}</tbody></table>
  <div class="box-info">Solvabilité : revenu médian {mv('median_income')} · imposables
     {mv('taxable_households_share')} · résidences secondaires {mv('secondary_residences_share')}.</div>
  <div class="footer"><span>Stella · Économie & Habitat</span><span>6 / 10</span></div>
</section>

<!-- 7. TOURISME & SAISONNALITÉ -->
<section class="page">
  <h1>Tourisme & saisonnalité</h1>
  <table><thead><tr><th>Indicateur</th><th>Valeur</th></tr></thead>
  <tbody>{tour_rows}</tbody></table>
  <div class="box-info"><b>Haute saison :</b> demande accrue ménage/conciergerie · recrutement saisonnier renforcé.</div>
  <div class="box-warn"><b>Basse saison :</b> bascule sur seniors/familles (contrats annuels).</div>
  <ul>
    <li>Coefficient CA été/hiver : {mv('seasonal_revenue_multiplier')}</li>
    <li>Indice saisonnalité : {mv('tourism_seasonality_index')}</li>
    <li>Nuitées annuelles : {mv('tourism_overnight_stays')}</li>
  </ul>
  <div class="footer"><span>Stella · Tourisme</span><span>7 / 10</span></div>
</section>

<!-- 8. CONCURRENCE -->
<section class="page">
  <h1>Cartographie concurrentielle</h1>
  {own_alert}
  <p>Marché à analyser sur 15 et 30 min. Détection franchises + associations + CCAS.</p>
  <table><thead><tr><th>Indicateur</th><th>Valeur</th><th>Conf.</th></tr></thead>
  <tbody>{comp_rows}</tbody></table>
  <h3>Pricing local</h3>
  <table><thead><tr><th>Indicateur</th><th>Valeur</th></tr></thead>
  <tbody>{price_rows}</tbody></table>
  <h3>Microzones premium</h3>
  <table><thead><tr><th>Quartier</th><th>Densité</th><th>Score premium</th><th>Tag</th></tr></thead>
  <tbody>{neigh_rows or '<tr><td colspan=4>—</td></tr>'}</tbody></table>
  <div class="footer"><span>Stella · Concurrence</span><span>8 / 10</span></div>
</section>

<!-- 9. RÉGLEMENTATION & FRANCHISE -->
<section class="page">
  <h1>Cadre réglementaire</h1>
  <table><thead><tr><th>Indicateur</th><th>Valeur</th></tr></thead>
  <tbody>{reg_rows}</tbody></table>
  <ul>
    <li>Autorisation SAAD requise : {mv('saad_authorization_required')}</li>
    <li>Tarif APA/SAAD local : <b>{mv('apa_hourly_rate')}</b></li>
    <li>Couverture aides publiques : {mv('public_aid_coverage')}</li>
    <li>Barrière réglementaire : {mv('regulatory_barrier_level')}</li>
  </ul>
  <div class="box-info"><b>Mode {biz['business_model']} :</b> simplicité administrative client,
     continuité de service, crédit d'impôt 50% (FR).</div>
  <div class="footer"><span>Stella · Réglementation</span><span>9 / 10</span></div>
</section>

<!-- 10. SWOT, VERDICT & PLAN D'ACTION -->
<section class="page">
  <h1>SWOT · Verdict · Plan d'action</h1>
  <div class="swot">
    <div class="q forces"><h3>Forces</h3><ul>{swot_li(strengths)}</ul></div>
    <div class="q faiblesses"><h3>Faiblesses</h3><ul>{swot_li(weaknesses)}</ul></div>
    <div class="q opportunites"><h3>Opportunités</h3><ul>{swot_li(opportunities)}</ul></div>
    <div class="q menaces"><h3>Menaces</h3><ul>{swot_li(threats)}</ul></div>
  </div>

  <h3>Plan d'action</h3>
  <table><thead><tr><th>Priorité</th><th>Action</th><th>Timing</th><th>Détails</th></tr></thead>
  <tbody>{action_rows}</tbody></table>

  <div class="box-info"><b>VERDICT FINAL :</b> <span class="verdict">{verdict_label}</span>.
     Voies possibles : zones périphériques, rachat agence existante, ou enseigne alternative en cas de blocage.</div>
  <div class="footer"><span>Stella · Verdict · {data['generated_at']}</span><span>10 / 10</span></div>
</section>

</body></html>"""


html_renderer = HtmlRenderer()
