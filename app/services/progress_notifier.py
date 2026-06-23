"""
Service partagé de notification de progression vers le frontend.
Extrait de webhook.py pour être utilisable depuis le pipeline (run_study.py)
sans import circulaire.
"""
from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)


def notify_front(
    study_id: str,
    status: str,
    *,
    progress: int | None = None,
    phase: int | None = None,
    phase_total: int = 5,
    phase_label: str | None = None,
    progress_label: str | None = None,
    eta_seconds: int | None = None,
    pptx_bytes: bytes | None = None,
    error_message: str | None = None,
) -> None:
    from app.core.config import get_settings
    settings = get_settings()
    url = settings.front_webhook_url
    secret = settings.generation_webhook_secret
    if not url or not secret:
        logger.debug("[progress-notifier] FRONT_WEBHOOK_URL ou GENERATION_WEBHOOK_SECRET non configuré — skip")
        return
    try:
        import httpx
        files: dict = {"study_id": (None, study_id), "status": (None, status)}
        if progress is not None:
            files["progress"] = (None, str(max(0, min(100, progress))))
        if eta_seconds is not None:
            files["eta_seconds"] = (None, str(max(0, eta_seconds)))
        if phase is not None:
            files["phase"] = (None, str(phase))
            files["phase_total"] = (None, str(phase_total))
        if phase_label:
            files["phase_label"] = (None, phase_label[:500])
        if progress_label:
            files["progress_label"] = (None, progress_label[:500])
        if status in ("error", "failed") and error_message:
            files["error_message"] = (None, error_message[:2000])
        if pptx_bytes:
            files["file_pptx"] = (f"{study_id}.pptx", io.BytesIO(pptx_bytes), "application/vnd.openxmlformats-officedocument.presentationml.presentation")
        resp = httpx.post(url, headers={"Authorization": f"Bearer {secret}"}, files=files, timeout=30.0)
        if resp.status_code >= 400:
            logger.warning("[progress-notifier] HTTP %s pour study_id=%s status=%s", resp.status_code, study_id, status)
        else:
            logger.debug("[progress-notifier] OK %s study_id=%s status=%s progress=%s", resp.status_code, study_id, status, progress)
    except Exception as exc:
        logger.exception("[progress-notifier] échec notification pour study_id=%s : %s", study_id, exc)
