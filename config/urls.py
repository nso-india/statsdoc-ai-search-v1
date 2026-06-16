from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "Mospi Administration"
admin.site.site_title = "Mospi Administration"
admin.site.index_title = "Site administration"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("uploader.urls")),
    path('health/', include('health_check.urls')),
    path("", include("vanna_adapter.urls")),  # Include vanna_adapter URLs
    path("", include("user_management.urls")),  # Include user_management URLs
    path("api/chat/", include("chat.urls")),  # Include chat URLs
    path("api/settings/", include("application_settings.urls")),  # Include application_settings URLs
    path("api/feedback/", include("feedback.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
