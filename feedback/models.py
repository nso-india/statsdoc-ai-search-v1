import os
import uuid

from django.conf import settings
from django.db import models

from .constants import (
    CATEGORY_GENERAL,
    FEEDBACK_CATEGORIES,
    FEEDBACK_STATUSES,
    RESPONSE_FEEDBACK_CATEGORIES,
    RESPONSE_FEEDBACK_RATINGS,
    STATUS_NEW,
)


def feedback_attachment_upload_to(instance, filename):
    from django.utils import timezone

    ext = os.path.splitext(filename)[1].lower()
    date_path = timezone.now().strftime("%Y/%m")
    return f"feedback_attachments/{date_path}/{uuid.uuid4().hex}{ext}"

class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedback_submissions",
    )
    name = models.CharField(max_length=150)
    email = models.EmailField()
    category = models.CharField(
        max_length=20,
        choices=FEEDBACK_CATEGORIES,
        default=CATEGORY_GENERAL,
    )
    subject = models.CharField(max_length=200)
    message = models.TextField()
    page_url = models.URLField(max_length=500, blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=FEEDBACK_STATUSES,
        default=STATUS_NEW,
    )
    mospi_portal_id = models.IntegerField(null=True, blank=True)
    mospi_portal_synced_at = models.DateTimeField(null=True, blank=True)
    mospi_portal_sync_error = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Feedback"
        verbose_name_plural = "Feedback submissions"

    def __str__(self):
        return f"{self.subject} ({self.email})"


class FeedbackAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to=feedback_attachment_upload_to)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True, default="")
    file_size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Feedback attachment"
        verbose_name_plural = "Feedback attachments"

    def __str__(self):
        return self.original_filename


class ResponseFeedback(models.Model):
    """Question-specific feedback on an assistant chat answer (thumbs up/down)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="response_feedback",
    )
    message = models.ForeignKey(
        "chat.Message",
        on_delete=models.CASCADE,
        related_name="response_feedback",
    )
    chat = models.ForeignKey(
        "chat.Chat",
        on_delete=models.CASCADE,
        related_name="response_feedback",
    )
    rating = models.CharField(max_length=10, choices=RESPONSE_FEEDBACK_RATINGS)
    category = models.CharField(
        max_length=30,
        choices=RESPONSE_FEEDBACK_CATEGORIES,
        blank=True,
        default="",
    )
    details = models.TextField(blank=True, default="")
    user_question = models.TextField(blank=True, default="")
    assistant_response = models.TextField(blank=True, default="")
    mospi_quickreview_synced_at = models.DateTimeField(null=True, blank=True)
    mospi_quickreview_sync_error = models.CharField(
        max_length=500, blank=True, default=""
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Response feedback"
        verbose_name_plural = "Response feedback"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "message"],
                name="unique_response_feedback_per_user_message",
            )
        ]

    def __str__(self):
        return f"{self.rating} on message {self.message_id} by {self.user_id}"
