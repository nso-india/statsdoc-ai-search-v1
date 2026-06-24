from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from user_management.permissions import IsStaffUser

from .constants import FEEDBACK_CATEGORIES, RESPONSE_FEEDBACK_CATEGORIES
from .export_utils import build_feedback_workbook
from .query_utils import get_rating_choices, get_status_choices


class FeedbackExportView(APIView):
    """Staff-only Excel export for feedback reports."""

    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        buffer, form_count, response_count = build_feedback_workbook(request.query_params, request=request)
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        filename = f"feedback_report_{timestamp}.xlsx"

        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["X-Feedback-Form-Count"] = str(form_count)
        response["X-Feedback-Response-Count"] = str(response_count)
        return response


class FeedbackReportMetaView(APIView):
    """Filter options for the admin feedback reports UI."""

    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        return Response(
            {
                "form_statuses": get_status_choices(),
                "form_categories": [
                    {"value": value, "label": label}
                    for value, label in FEEDBACK_CATEGORIES
                ],
                "response_ratings": get_rating_choices(),
                "response_categories": [
                    {"value": value, "label": label}
                    for value, label in RESPONSE_FEEDBACK_CATEGORIES
                ],
            }
        )
