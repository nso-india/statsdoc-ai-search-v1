from django.urls import path

from .views import ReportCatalogView, ReportDetailView, ReportExportView, ReportMetaView

urlpatterns = [
    path("catalog/", ReportCatalogView.as_view(), name="report-catalog"),
    path("meta/", ReportMetaView.as_view(), name="report-meta"),
    path("export/", ReportExportView.as_view(), name="report-export-all"),
    path("<slug:slug>/", ReportDetailView.as_view(), name="report-detail"),
    path("<slug:slug>/export/", ReportExportView.as_view(), name="report-export"),
]
