from django.contrib import admin

from .models import UploadedFile, ExtractedTableMapping, Comment, KnowledgeBase


# Register your models here.
@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "created_at", "updated_at")
    search_fields = ("name", "description")
    list_filter = ("created_at", "updated_at")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ("id", "file", "uploaded_at")
    search_fields = ("file",)
    list_filter = ("uploaded_at",)
    ordering = ("-uploaded_at",)
    date_hierarchy = "uploaded_at"


@admin.register(ExtractedTableMapping)
class ExtractedTableMappingAdmin(admin.ModelAdmin):
    list_display = ("id", "file", "table_name", "caption_text")
    search_fields = ("file__file_name", "table_name", "caption_text")
    list_filter = ("file",)
    ordering = ("-id",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "file", "comment_type", "created_at")
    search_fields = ("file__file_name", "comment")
    list_filter = ("comment_type", "status", "created_at")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
