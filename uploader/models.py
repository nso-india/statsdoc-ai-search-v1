from django.db import models

from .constants import (
    FILE_STATUS,
    PENDING,
    COMMENT_TYPES,
    COMMENT_STATUS,
    COMMENT_PENDING,
)
from chat.models import Chat


class KnowledgeBase(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Knowledge Base"
        verbose_name_plural = "Knowledge Bases"
        ordering = ["-created_at"]


class UploadedFile(models.Model):
    file = models.FileField(upload_to="uploads/")
    file_name = models.TextField()
    status = models.CharField(
        max_length=255,
        choices=FILE_STATUS,
        default=PENDING,
    )
    chat = models.ForeignKey(
        Chat, on_delete=models.CASCADE, related_name="uploaded_files",
        null=True,
        blank=True
    )
    knowledge_base = models.ForeignKey(
        KnowledgeBase, 
        on_delete=models.CASCADE, 
        related_name="files",
        null=True,
        blank=True
    )
    docling_json = models.JSONField(null=True, blank=True)
    reviewed = models.BooleanField(default=False)
    other_info = models.JSONField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name

    class Meta:
        verbose_name = "Uploaded File"
        verbose_name_plural = "Uploaded Files"
        ordering = ["-uploaded_at"]


class Comment(models.Model):
    file = models.ForeignKey(
        UploadedFile, on_delete=models.CASCADE, related_name="comments"
    )
    comment = models.TextField()
    existing_text = models.TextField(null=True, blank=True)
    comment_type = models.CharField(
        max_length=20, choices=COMMENT_TYPES, default="EDIT"
    )
    target_ref = models.TextField(null=True, blank=True)
    source_ref = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=COMMENT_STATUS,
        default=COMMENT_PENDING,
    )


class ExtractedTableMapping(models.Model):
    file = models.ForeignKey(
        UploadedFile, on_delete=models.CASCADE, related_name="extracted_tables"
    )
    table_name = models.TextField()
    caption_text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Table {self.table_name} from {self.file.file_name}"

    class Meta:
        verbose_name = "Extracted Table Mapping"
        verbose_name_plural = "Extracted Table Mappings"
        ordering = ["-created_at"]
