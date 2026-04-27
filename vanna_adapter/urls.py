from django.urls import path

from .views import (
    QueryEnhancedView,
)

urlpatterns = [
    path("api/query-enhanced/", QueryEnhancedView.as_view(), name="query-enhanced-view"),
]
