from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from feedback.export_views import FeedbackReportMetaView
from feedback.response_serializers import ResponseFeedbackSerializer
from feedback.serializers import FeedbackSerializer
from user_management.permissions import IsStaffUser

from .export import build_all_reports_workbook, build_single_report_workbook
from .queries import REPORT_CATALOG, get_report_slug, run_report_query
from .validators import validate_date_params


class ReportCatalogView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        return Response({"reports": REPORT_CATALOG})


class ReportMetaView(FeedbackReportMetaView):
    """Filter options for admin reports UI (includes feedback filters)."""

    def get(self, request):
        response = super().get(request)
        data = dict(response.data)
        data["reports"] = REPORT_CATALOG
        return Response(data)


class ReportDetailView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request, slug):
        if not get_report_slug(slug):
            return Response({"detail": "Report not found."}, status=status.HTTP_404_NOT_FOUND)

        date_error = validate_date_params(request.query_params)
        if date_error:
            return Response({"detail": date_error}, status=status.HTTP_400_BAD_REQUEST)

        handler = run_report_query(slug, request.query_params)
        if not handler:
            return Response({"detail": "Report not found."}, status=status.HTTP_404_NOT_FOUND)

        data = handler(request.query_params)

        if slug == "form_feedback":
            data["results"] = FeedbackSerializer(
                data["results"], many=True, context={"request": request}
            ).data
        elif slug == "response_feedback":
            data["results"] = ResponseFeedbackSerializer(data["results"], many=True).data

        return Response(data)


class ReportExportView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request, slug=None):
        params = request.query_params
        date_error = validate_date_params(params)
        if date_error:
            return Response({"detail": date_error}, status=status.HTTP_400_BAD_REQUEST)

        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")

        if slug:
            if not get_report_slug(slug):
                return Response({"detail": "Report not found."}, status=status.HTTP_404_NOT_FOUND)
            buffer = build_single_report_workbook(slug, params, request=request)
            filename = f"{slug}_report_{timestamp}.xlsx"
        else:
            buffer = build_all_reports_workbook(params, request=request)
            filename = f"admin_reports_{timestamp}.xlsx"

        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
