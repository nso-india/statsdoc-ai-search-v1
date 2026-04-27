from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    FileUploadView, 
    ProfileView,
    RawFileView,
    ProcessedFileView,
    DocLingJSONView,
    FileReview,
    AICommentsView,
    KnowledgeBaseView,
    KnowledgeBaseDetailView,
    TranscribeAudioView,
    FileDeleteView,
)
from .media_views import serve_protected_media

urlpatterns = [
    path("api/upload/", FileUploadView.as_view(), name="file-upload"),
    # Token endpoints removed - use /api/login/ from user_management instead
    path("api/profile/", ProfileView.as_view(), name="user-profile"),
    path("api/files/<int:id>/raw/", RawFileView.as_view(), name="raw-file-view"),
    path("api/files/<int:id>/processed/", ProcessedFileView.as_view(), name="processed-file-view"),
    path("api/files/<int:file_id>/docling-json/", DocLingJSONView.as_view(), name="file-docling-json"),
    path("api/files/<int:file_id>/approve-file/", FileReview.as_view(), name="file-approve"),
    path("api/files/<int:file_id>/ai-comments/", AICommentsView.as_view(), name="ai-comments"),
    path("api/files/<int:file_id>/delete/", FileDeleteView.as_view(), name="file-delete"),
    path("api/knowledge-bases/", KnowledgeBaseView.as_view(), name="knowledge-base-list-create"),
    path("api/knowledge-bases/<int:pk>/", KnowledgeBaseDetailView.as_view(), name="knowledge-base-detail"),
    # Transcription proxy endpoint (server-side) to avoid CORS and keep OpenAI key secure
    path("api/speech/transcribe/", TranscribeAudioView.as_view(), name="speech-transcribe"),
    # Protected media files - requires authentication
    path("media/<path:file_path>", serve_protected_media, name="protected-media"),
]
