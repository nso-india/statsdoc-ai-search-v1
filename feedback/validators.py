import os

from django.core.exceptions import ValidationError

from .constants import (
    ALLOWED_FEEDBACK_ATTACHMENT_EXTENSIONS,
    ALLOWED_FEEDBACK_ATTACHMENT_MIME_TYPES,
    MAX_FEEDBACK_ATTACHMENT_SIZE_BYTES,
    MAX_FEEDBACK_ATTACHMENTS,
)


def validate_feedback_attachments(files):
    """
    Validate optional screenshot attachments for feedback submissions.
    Raises ValidationError with a message suitable for API responses.
    """
    if not files:
        return

    if len(files) > MAX_FEEDBACK_ATTACHMENTS:
        raise ValidationError(
            f"You can attach at most {MAX_FEEDBACK_ATTACHMENTS} screenshot(s)."
        )

    for uploaded in files:
        filename = uploaded.name or ""
        if "\x00" in filename or ".." in filename or "/" in filename or "\\" in filename:
            raise ValidationError("Invalid attachment filename.")

        filename_lower = filename.lower()
        ext = os.path.splitext(filename_lower)[1]
        if ext not in ALLOWED_FEEDBACK_ATTACHMENT_EXTENSIONS:
            raise ValidationError(
                "Only PNG, JPG, JPEG, and WEBP screenshots are allowed."
            )

        parts = filename_lower.split(".")
        if len(parts) > 2:
            raise ValidationError(
                f'Invalid filename "{filename}". Double extensions are not allowed.'
            )

        content_type = (uploaded.content_type or "").split(";")[0].strip().lower()
        if content_type and content_type not in ALLOWED_FEEDBACK_ATTACHMENT_MIME_TYPES:
            raise ValidationError(
                f'File type "{content_type}" is not allowed for feedback screenshots.'
            )

        if uploaded.size > MAX_FEEDBACK_ATTACHMENT_SIZE_BYTES:
            max_mb = MAX_FEEDBACK_ATTACHMENT_SIZE_BYTES / (1024 * 1024)
            raise ValidationError(
                f'"{filename}" exceeds the {max_mb:.0f} MB size limit per screenshot.'
            )
