from django.urls import path
from . import views

app_name = 'application_settings'

urlpatterns = [
    # List all configurations
    path('configs/', views.ConfigListView.as_view(), name='list_configs'),

    # Get/Update specific namespace configuration
    path('configs/<str:namespace>/', views.NamespaceConfigView.as_view(), name='namespace_config'),

    # Reset specific namespace to defaults
    path('configs/<str:namespace>/reset/', views.NamespaceResetView.as_view(), name='reset_namespace'),

    # Reset all namespaces to defaults
    path('configs/reset/', views.NamespaceResetView.as_view(), name='reset_all_namespaces'),
]