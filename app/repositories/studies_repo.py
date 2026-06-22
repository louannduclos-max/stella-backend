import json
import os
import threading
from pathlib import Path
from typing import Dict

from app.api.schemas.common import Study


class StudiesRepository:
    def __init__(self, storage_dir: str | None = None) -> None:
        self._store: Dict[str, Study] = {}
        self._lock = threading.RLock()
        env_path = os.environ.get("STELLA_STORAGE_DIR")
        resolved = storage_dir or env_path or "storage/studies"
        self._dir = Path(resolved)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._load_all()

    def _file(self, study_id: str) -> Path:
        return self._dir / f"{study_id}.json"

    def _load_all(self) -> None:
        for path in self._dir.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                study = Study.model_validate(payload)
                self._store[study.study_id] = study
            except Exception:
                continue

    def _persist(self, study: Study) -> None:
        path = self._file(study.study_id)
        payload = study.model_dump(mode="json")
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def save(self, study: Study) -> Study:
        with self._lock:
            self._store[study.study_id] = study
            try:
                self._persist(study)
            except Exception:
                pass
            return study

    def get(self, study_id: str) -> Study | None:
        with self._lock:
            if study_id in self._store:
                return self._store[study_id]
            path = self._file(study_id)
            if path.exists():
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    study = Study.model_validate(payload)
                    self._store[study_id] = study
                    return study
                except Exception:
                    return None
            return None

    def all(self, tenant_id: str | None = None) -> list[Study]:
        """Retourne toutes les études. Si tenant_id fourni, filtre par filiale."""
        with self._lock:
            studies = list(self._store.values())
            if tenant_id:
                studies = [s for s in studies if s.tenant_id == tenant_id]
            return studies


studies_repo = StudiesRepository()
