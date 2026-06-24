from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from user_management.permissions import IsStaffUser

from .models import Feedback, FeedbackAttachment
from .serializers import (
    FeedbackAttachmentSerializer,
    FeedbackCreateSerializer,
    FeedbackSerializer,
)
from .utils import save_feedback_attachments, send_feedback_notification
from .mospi_portal import record_mospi_portal_sync_failure, submit_feedback_to_mospi_portal
from .query_utils import get_feedback_list_queryset, paginate_queryset
from .validators import validate_feedback_attachments


class FeedbackCreateView(APIView):
    """Submit feedback (anonymous or authenticated)."""

    permission_classes = []  # Anonymous allowed; JWT used when Bearer token is sent

    def post(self, request):
        attachment_files = request.FILES.getlist("attachments")
        try:
            validate_feedback_attachments(attachment_files)
        except ValidationError as exc:
            messages = getattr(exc, "messages", None) or [str(exc)]
            return Response(
                {"attachments": list(messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = FeedbackCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            feedback = serializer.save()
            created_attachments = save_feedback_attachments(feedback, attachment_files)

        send_feedback_notification(feedback, request=request)

        portal_result = submit_feedback_to_mospi_portal(feedback)
        if not portal_result.success:
            record_mospi_portal_sync_failure(feedback, portal_result.error)

        attachment_data = FeedbackAttachmentSerializer(
            created_attachments,
            many=True,
            context={"request": request},
        ).data

        return Response(
            {
                "id": str(feedback.id),
                "message": "Thank you for your feedback. We will review it shortly.",
                "attachments": attachment_data,
            },
            status=status.HTTP_201_CREATED,
        )


class FeedbackListView(APIView):
    """List feedback submissions (staff only)."""

    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        queryset = get_feedback_list_queryset(request.query_params)
        page = paginate_queryset(queryset, request.query_params)
        serializer = FeedbackSerializer(
            page["results"],
            many=True,
            context={"request": request},
        )
        return Response(
            {
                "count": page["count"],
                "page": page["page"],
                "page_size": page["page_size"],
                "results": serializer.data,
            }
        )
