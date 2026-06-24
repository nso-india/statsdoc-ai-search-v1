import logging



from django.conf import settings



from user_management.utils import MOSPIEmailService



from .models import FeedbackAttachment



logger = logging.getLogger(__name__)


def build_media_absolute_url(relative_url, request=None):
    """Build a clickable URL for files stored under MEDIA_URL."""
    if request:
        return request.build_absolute_uri(relative_url)
    base = getattr(settings, "PUBLIC_BACKEND_URL", "").strip()
    if base:
        return f"{base.rstrip('/')}{relative_url}"
    if getattr(settings, "DEBUG", False):
        return f"http://localhost:8000{relative_url}"
    return relative_url


def build_feedback_attachment_download_url(attachment, request=None, signed=False):
    """Return staff download URL for a feedback attachment."""
    from django.urls import reverse

    from .attachment_views import sign_feedback_attachment_id

    path = reverse(
        "feedback:attachment-download",
        kwargs={"attachment_id": attachment.id},
    )
    if signed:
        token = sign_feedback_attachment_id(attachment.id)
        path = f"{path}?access={token}"
    return build_media_absolute_url(path, request)


def get_feedback_notify_recipients():

    """MoSPI team inbox for new feedback notifications."""

    raw = getattr(settings, "FEEDBACK_NOTIFY_EMAILS", "")

    if raw:

        return [e.strip() for e in raw.split(",") if e.strip()]

    return ["di.lab@mospi.gov.in"]





def save_feedback_attachments(feedback, files):

    """Persist validated screenshot files for a feedback submission."""

    created = []

    for uploaded in files:

        attachment = FeedbackAttachment.objects.create(

            feedback=feedback,

            file=uploaded,

            original_filename=uploaded.name,

            content_type=(uploaded.content_type or "").split(";")[0].strip().lower(),

            file_size=uploaded.size,

        )

        created.append(attachment)

    return created





def send_feedback_notification(feedback, request=None) -> bool:

    """

    Notify the MoSPI team when feedback is submitted.

    Uses MOSPI SMTP API; returns False if email is not configured (submission still saved).

    """

    recipients = get_feedback_notify_recipients()

    subject = f"[StatsDoc Feedback] {feedback.subject}"

    body = (

        f"<p><strong>New feedback received</strong></p>"

        f"<p><strong>From:</strong> {feedback.name} &lt;{feedback.email}&gt;</p>"

        f"<p><strong>Subject:</strong> {feedback.subject}</p>"

        f"<p><strong>Message:</strong></p><p>{feedback.message}</p>"

        f"<p><strong>Page:</strong> {feedback.page_url or '—'}</p>"

        f"<p><strong>Submission ID:</strong> {feedback.id}</p>"

    )



    attachments = list(feedback.attachments.all())

    if attachments:

        body += "<p><strong>Screenshots:</strong></p><ul>"

        for attachment in attachments:

            if request:

                url = request.build_absolute_uri(attachment.file.url)

            else:

                url = attachment.file.url

            body += (

                f"<li><a href=\"{url}\">{attachment.original_filename}</a> "

                f"({attachment.file_size} bytes)</li>"

            )

        body += "</ul>"



    service = MOSPIEmailService()

    sent = service.send_email(recipients, subject, body)

    if not sent:

        logger.info(

            "Feedback %s saved; notification email not sent (SMTP not configured).",

            feedback.id,

        )

    return sent


def extract_message_text(content) -> str:
    """Best-effort plain text from a chat Message.content field."""
    import json

    if content is None:
        return ""

    if isinstance(content, dict):
        parsed = content
    else:
        text = str(content)
        if text.strip().startswith("{"):
            try:
                parsed = json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return text[:2000]
        else:
            return text[:2000]

    if not isinstance(parsed, dict):
        return str(parsed)[:2000]

    if parsed.get("response"):
        return str(parsed["response"])[:2000]

    inner = parsed.get("content")
    if isinstance(inner, dict):
        return str(inner.get("response") or inner.get("content") or "")[:2000]
    if isinstance(inner, str):
        return inner[:2000]

    return str(parsed)[:2000]


def get_preceding_user_question(message):
    """Return the user message immediately before this assistant message."""
    from chat.models import Message

    return (
        Message.objects.filter(
            chat=message.chat,
            role="user",
            created_at__lte=message.created_at,
        )
        .exclude(pk=message.pk)
        .order_by("-created_at")
        .first()
    )


def build_response_feedback_context(message):
    """Capture question/answer snapshots for admin review."""
    question_msg = get_preceding_user_question(message)
    return {
        "user_question": extract_message_text(question_msg.content) if question_msg else "",
        "assistant_response": extract_message_text(message.content),
    }