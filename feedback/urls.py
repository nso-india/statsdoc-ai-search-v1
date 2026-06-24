from django.urls import path

from .export_views import FeedbackExportView, FeedbackReportMetaView
from .attachment_views import FeedbackAttachmentDownloadView
from . import views
from .response_views import (
    ResponseFeedbackChatSummaryView,
    ResponseFeedbackCreateView,
    ResponseFeedbackListView,
)

app_name = "feedback"

urlpatterns = [
    path("", views.FeedbackCreateView.as_view(), name="feedback-create"),
    path("list/", views.FeedbackListView.as_view(), name="feedback-list"),
    path("reports/meta/", FeedbackReportMetaView.as_view(), name="feedback-reports-meta"),
    path("reports/export/", FeedbackExportView.as_view(), name="feedback-reports-export"),
    path(
        "attachments/<uuid:attachment_id>/download/",
        FeedbackAttachmentDownloadView.as_view(),
        name="attachment-download",
    ),
    path("response/", ResponseFeedbackCreateView.as_view(), name="response-feedback-create"),
    path(
        "response/chat/<int:chat_id>/",
        ResponseFeedbackChatSummaryView.as_view(),
        name="response-feedback-chat-summary",
    ),
    path(
        "response/list/",
        ResponseFeedbackListView.as_view(),
        name="response-feedback-list",
    ),
]
