from app.api.schemas.common import Study
from app.core.brand_profiles import get_brand_profile
from app.services.css_vars_builder import build_css_vars
from app.services.frontend_bindings_builder import build_frontend_component_map
from app.services.lovable_config import build_lovable_config
from app.services.master_json_builder import master_json_builder
from app.services.playlist_builder import build_playlist_manifest


class FrontendManifestBuilder:
    def build_shell(
        self,
        *,
        brand_slug: str | None = None,
        country: str | None = None,
        city: str | None = None,
        business_model: str | None = None,
        study_id: str | None = None,
    ) -> dict:
        profile = get_brand_profile(brand_slug) if brand_slug else get_brand_profile("o2")
        resolved_slug = profile["slug"] if profile else brand_slug
        return {
            "version": "1.0.0",
            "manifest_type": "frontend_manifest",
            "consumption_mode": "single_request",
            "brand_profile": profile,
            "theme": {
                "brand_slug": resolved_slug,
                "css": build_css_vars(resolved_slug),
                "font_family": (profile or {}).get("font_family"),
                "palette": (profile or {}).get("palette"),
            },
            "renderer": {
                "component_map": build_frontend_component_map(),
                "playlist": build_playlist_manifest(
                    brand_slug=resolved_slug,
                    study_id=study_id,
                    country=country,
                    city=city,
                    business_model=business_model,
                ),
            },
            "lovable_config": build_lovable_config(
                business_model=business_model,
                brand_slug=resolved_slug,
            ),
            "bootstrap": {
                "strategy": "fetch once then render locally",
                "slide_order_source": "renderer.playlist.slides",
                "component_resolver": "renderer.component_map.items",
                "theme_source": "theme.css.variables",
            },
        }

    def build_for_study(self, study: Study, brand_slug: str | None = None) -> dict:
        resolved_slug = brand_slug
        if not resolved_slug and study.business_context.brand_name:
            candidate = study.business_context.brand_name.lower().split()[0]
            if get_brand_profile(candidate):
                resolved_slug = candidate

        shell = self.build_shell(
            brand_slug=resolved_slug,
            study_id=study.study_id,
            country=study.geo_scope.country,
            city=study.geo_scope.city,
            business_model=study.business_context.business_model,
        )
        master_json = master_json_builder.build(study)
        shell.update(
            {
                "study_id": study.study_id,
                "resolved_brand_slug": resolved_slug,
                "study_data": master_json,
                "assets": {
                    "preview_html": f"/studies/{study.study_id}/preview-html?brand_slug={resolved_slug or ''}",
                    "preview_html_export": f"/studies/{study.study_id}/preview-html/export?brand_slug={resolved_slug or ''}",
                    "master_json_export": f"/studies/{study.study_id}/master-json/export",
                },
            }
        )
        return shell


frontend_manifest_builder = FrontendManifestBuilder()
