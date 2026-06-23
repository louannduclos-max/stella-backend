from __future__ import annotations
import logging, os
from supabase import create_client, Client
from app.api.schemas.common import Study

logger = logging.getLogger(__name__)

_SUPABASE_URL = os.environ.get("SUPABASE_URL") or "https://utwjfsomblhupghbgvgv.supabase.co"
_SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0d2pmc29tYmxodXBnaGJndmd2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MjExNTMxNSwiZXhwIjoyMDk3NjkxMzE1fQ.EwLQ1XeK3yUYh8Ld_CGeDQTA2ptfuKTzc_Phkcpfbak"
_TABLE = "study_generated_data"

class StudiesRepository:
    def __init__(self) -> None:
        self._client: Client = create_client(_SUPABASE_URL, _SUPABASE_KEY)

    def save(self, study: Study) -> Study:
        row = {"study_id": str(study.study_id), "tenant_id": study.tenant_id, "status": str(getattr(study.status, "value", study.status)), "country": study.country, "data": study.model_dump(mode="json")}
        try:
            self._client.table(_TABLE).upsert(row, on_conflict="study_id").execute()
        except Exception:
            logger.exception("[studies_repo] save failed study_id=%s", study.study_id)
            raise
        return study

    def get(self, study_id: str, tenant_id: str | None = None) -> Study | None:
        try:
            q = self._client.table(_TABLE).select("data").eq("study_id", str(study_id))
            if tenant_id:
                q = q.eq("tenant_id", tenant_id)
            res = q.limit(1).execute()
            if not res.data:
                return None
            return Study.model_validate(res.data[0]["data"])
        except Exception:
            logger.exception("[studies_repo] get failed study_id=%s", study_id)
            return None

    def all(self, tenant_id: str | None = None) -> list[Study]:
        try:
            q = self._client.table(_TABLE).select("data")
            if tenant_id:
                q = q.eq("tenant_id", tenant_id)
            res = q.order("created_at", desc=True).execute()
            studies = []
            for row in res.data:
                try:
                    studies.append(Study.model_validate(row["data"]))
                except Exception:
                    logger.warning("[studies_repo] row invalide ignore: %s", row.get("study_id"))
            return studies
        except Exception:
            logger.exception("[studies_repo] all() failed")
            return []

studies_repo = StudiesRepository()
