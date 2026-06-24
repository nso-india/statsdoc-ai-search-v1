from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import Chat
from user_management.permissions import IsStaffUser

from .models import ResponseFeedback
from .response_serializers import (
    ResponseFeedbackCreateSerializer,
    ResponseFeedbackSerializer,
    ResponseFeedbackSummarySerializer,
)
from .query_utils import get_response_feedback_list_queryset, paginate_queryset
from .utils import build_response_feedback_context


class ResponseFeedbackCreateView(APIView):
    """Submit or update thumbs up/down on a specific assistant answer."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ResponseFeedbackCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message = serializer.context["message"]
        chat = serializer.context["chat"]
        validated = serializer.validated_data
        snapshots = build_response_feedback_context(message)

        feedback, _created = ResponseFeedback.objects.update_or_create(
            user=request.user,
            message=message,
            defaults={
                "chat": chat,
                "rating": validated["rating"],
                "category": validated.get("category", ""),
                "details": validated.get("details", ""),
                "user_question": snapshots["user_question"],
                "assistant_response": snapshots["assistant_response"],
            },
        )

        return Response(
            ResponseFeedbackSerializer(feedback).data,
            status=status.HTTP_201_CREATED,
        )


class ResponseFeedbackChatSummaryView(APIView):
    """List current user's feedback ratings for all messages in a chat."""

    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):
        chat = get_object_or_404(Chat, pk=chat_id)
        if not (
            request.user.is_staff
            or request.user.is_superuser
            or chat.user_id == request.user.id
        ):
            return Response(status=status.HTTP_404_NOT_FOUND)

        queryset = ResponseFeedback.objects.filter(
            user=request.user,
            chat=chat,
        ).select_related("message")

        return Response(
            ResponseFeedbackSummarySerializer(queryset, many=True).data
        )


class ResponseFeedbackListView(APIView):
    """Staff-only list of all response feedback for review."""

    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        queryset = get_response_feedback_list_queryset(request.query_params)
        page = paginate_queryset(queryset, request.query_params)
        serializer = ResponseFeedbackSerializer(
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
