import logging
from dataclasses import dataclass

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class MospiPortalResult:
    success: bool
    portal_id: int | None = None
    error: str = ""


def format_feedback_for_portal(feedback) -> str:
    parts = [f"Subject: {feedback.subject}", f"Message: {feedback.message}"]
    if feedback.page_url:
        parts.append(f"Page: {feedback.page_url}")
    if feedback.category and feedback.category != "general":
        parts.append(f"Category: {feedback.category}")
    attachment_count = feedback.attachments.count()
    if attachment_count:
        parts.append(
            f"Attachments: {attachment_count} file(s) stored in StatsDoc admin reports"
        )
    return "\n\n".join(parts)


def submit_feedback_to_mospi_portal(feedback, *, force=False) -> MospiPortalResult:
    """Forward a local feedback row to the MoSPI DI Lab central portal."""
    if not getattr(settings, "MOSPI_PORTAL_ENABLED", True):
        return MospiPortalResult(success=False, error="MoSPI portal sync disabled")

    if feedback.mospi_portal_synced_at and not force:
        return MospiPortalResult(success=True, portal_id=feedback.mospi_portal_id)

    url = settings.MOSPI_PORTAL_FEEDBACK_URL
    payload = {
        "name": feedback.name[:150],
        "email": feedback.email,
        "feedback": format_feedback_for_portal(feedback),
        "data_source": settings.MOSPI_PORTAL_DATA_SOURCE,
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=20,
            verify=getattr(settings, "MOSPI_PORTAL_VERIFY_SSL", True),
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        logger.exception("MoSPI portal feedback sync failed for %s", feedback.id)
        return MospiPortalResult(success=False, error=str(exc))

    portal_response = data.get("response") if isinstance(data, dict) else None
    portal_id = None
    if isinstance(portal_response, dict):
        portal_id = portal_response.get("id")

    feedback.mospi_portal_id = portal_id
    feedback.mospi_portal_synced_at = timezone.now()
    feedback.mospi_portal_sync_error = ""
    feedback.save(
        update_fields=[
            "mospi_portal_id",
            "mospi_portal_synced_at",
            "mospi_portal_sync_error",
        ]
    )

    logger.info(
        "Synced feedback %s to MoSPI portal (portal_id=%s)",
        feedback.id,
        portal_id,
    )
    return MospiPortalResult(success=True, portal_id=portal_id)


def record_mospi_portal_sync_failure(feedback, error_message: str):
    feedback.mospi_portal_sync_error = (error_message or "")[:500]
    feedback.save(update_fields=["mospi_portal_sync_error"])
