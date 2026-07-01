from datetime import UTC, datetime
from uuid import uuid4

from app.api.schemas.common import Study
from app.api.schemas.studies import StudyCreateRequest
from app.core.constants import DEFAULT_VERSION
from app.core.enums import StudyStatus
from app.services.geo_normalizer import geo_normalizer


class StudyFactory:
    def build(self, payload: StudyCreateRequest) -> Study:
        now = datetime.now(UTC)
        # Si un external_study_id est fourni (UUID Supabase), on l'utilise directement
        # pour que le polling front fonctionne avec le même identifiant.
        study_id = payload.external_study_id or f"std_{uuid4().hex[:12]}"

        # Résolution du tenant_id : payload > brand_name.lower() > défaut
        brand_slug = (payload.business_context.brand_name or "").strip().lower().split()[0] if payload.business_context.brand_name else ""
        tenant_id = payload.tenant_id or brand_slug or "interdomicilio"

        return Study(
            study_id=study_id,
            version=DEFAULT_VERSION,
            status=StudyStatus.DRAFT,
            country=payload.country.upper(),
            language=payload.language,
            study_type=payload.study_type,
            study_date=payload.study_date,
            tenant_id=tenant_id,
            company_id=payload.company_id,
            brand_profile_override=payload.brand_profile_override,
            wizard_selections=payload.wizard_selections,
            geo_scope=geo_normalizer.normalize(
                city=payload.city,
                country=payload.country,
                region=payload.region,
                postal_codes=payload.postal_codes,
            ),
            business_context=payload.business_context,
            created_at=now,
            updated_at=now,
        )


study_factory = StudyFactory()
