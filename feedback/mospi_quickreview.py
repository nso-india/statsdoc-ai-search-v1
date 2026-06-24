import logging
from dataclasses import dataclass

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

MAX_QUICKREVIEW_PROMPT_LENGTH = 2000


@dataclass
class MospiQuickreviewResult:
    success: bool
    error: str = ""


def build_quickreview_payload(feedback) -> dict:
    """Map a local ResponseFeedback row to the MoSPI quickreview API body."""
    prompt = (feedback.user_question or "").strip()
    if len(prompt) > MAX_QUICKREVIEW_PROMPT_LENGTH:
        prompt = prompt[:MAX_QUICKREVIEW_PROMPT_LENGTH]

    return {
        "category": (feedback.category or "").strip(),
        "details": (feedback.details or "").strip(),
        "message_id": str(feedback.message_id),
        "rating": feedback.rating,
        "session_id": str(feedback.chat_id),
        "prompt": prompt,
        "product": getattr(settings, "MOSPI_PORTAL_PRODUCT", "statsdoc"),
    }


def submit_response_feedback_to_mospi_quickreview(
    feedback, *, force=False
) -> MospiQuickreviewResult:
    """Forward a thumbs up/down rating to the MoSPI DI Lab quickreview API."""
    if not getattr(settings, "MOSPI_PORTAL_ENABLED", True):
        return MospiQuickreviewResult(success=False, error="MoSPI portal sync disabled")

    if feedback.mospi_quickreview_synced_at and not force:
        return MospiQuickreviewResult(success=True)

    url = settings.MOSPI_QUICKREVIEW_URL
    payload = build_quickreview_payload(feedback)

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=20,
            verify=getattr(settings, "MOSPI_PORTAL_VERIFY_SSL", True),
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.exception(
            "MoSPI quickreview sync failed for response feedback %s", feedback.id
        )
        return MospiQuickreviewResult(success=False, error=str(exc))

    feedback.mospi_quickreview_synced_at = timezone.now()
    feedback.mospi_quickreview_sync_error = ""
    feedback.save(
        update_fields=[
            "mospi_quickreview_synced_at",
            "mospi_quickreview_sync_error",
        ]
    )

    logger.info(
        "Synced response feedback %s (message_id=%s) to MoSPI quickreview",
        feedback.id,
        feedback.message_id,
    )
    return MospiQuickreviewResult(success=True)


def record_mospi_quickreview_sync_failure(feedback, error_message: str):
    feedback.mospi_quickreview_sync_error = (error_message or "")[:500]
    feedback.save(update_fields=["mospi_quickreview_sync_error"])
