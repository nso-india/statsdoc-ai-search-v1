from django.contrib import admin



from .models import Feedback, FeedbackAttachment, ResponseFeedback





class FeedbackAttachmentInline(admin.TabularInline):

    model = FeedbackAttachment

    extra = 0

    readonly_fields = ("id", "original_filename", "content_type", "file_size", "created_at", "file")

    fields = ("original_filename", "file", "content_type", "file_size", "created_at")

    can_delete = True





@admin.register(Feedback)

class FeedbackAdmin(admin.ModelAdmin):

    list_display = (

        "subject",

        "category",

        "status",

        "name",

        "email",

        "attachment_count",

        "created_at",

    )

    list_filter = ("status", "category", "created_at")

    search_fields = ("subject", "message", "name", "email")

    readonly_fields = ("id", "created_at", "updated_at")

    ordering = ("-created_at",)

    inlines = [FeedbackAttachmentInline]



    @admin.display(description="Screenshots")

    def attachment_count(self, obj):

        return obj.attachments.count()





@admin.register(FeedbackAttachment)

class FeedbackAttachmentAdmin(admin.ModelAdmin):

    list_display = ("original_filename", "feedback", "file_size", "created_at")

    search_fields = ("original_filename", "feedback__subject", "feedback__email")

    readonly_fields = ("id", "created_at")




@admin.register(ResponseFeedback)
class ResponseFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "rating",
        "category",
        "user",
        "chat",
        "message",
        "question_preview",
        "created_at",
    )
    list_filter = ("rating", "category", "created_at")
    search_fields = (
        "details",
        "user_question",
        "assistant_response",
        "user__email",
        "chat__title",
    )
    readonly_fields = (
        "id",
        "user",
        "message",
        "chat",
        "user_question",
        "assistant_response",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)

    @admin.display(description="Question")
    def question_preview(self, obj):
        text = obj.user_question or ""
        return text[:80] + "..." if len(text) > 80 else text
