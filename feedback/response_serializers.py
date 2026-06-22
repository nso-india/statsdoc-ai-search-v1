from rest_framework import serializers

from chat.models import Message
from user_management.serializers import StrictFieldValidationMixin

from .constants import (
    MAX_RESPONSE_FEEDBACK_DETAILS_LENGTH,
    RATING_DOWN,
    RATING_UP,
    RESPONSE_FEEDBACK_CATEGORIES,
    RESPONSE_FEEDBACK_CATEGORY_VALUES,
    RESPONSE_FEEDBACK_RATINGS,
)
from .models import ResponseFeedback


class ResponseFeedbackCreateSerializer(StrictFieldValidationMixin, serializers.Serializer):
    message_id = serializers.IntegerField()
    rating = serializers.ChoiceField(choices=[RATING_UP, RATING_DOWN])
    category = serializers.CharField(required=False, allow_blank=True, default="")
    details = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_details(self, value):
        value = (value or "").strip()
        if len(value) > MAX_RESPONSE_FEEDBACK_DETAILS_LENGTH:
            raise serializers.ValidationError(
                f"Details must be {MAX_RESPONSE_FEEDBACK_DETAILS_LENGTH} characters or fewer."
            )
        return value

    def validate(self, attrs):
        rating = attrs["rating"]
        category = (attrs.get("category") or "").strip()
        details = (attrs.get("details") or "").strip()

        if rating == RATING_DOWN and not category:
            raise serializers.ValidationError(
                {"category": "Please select a reason for your feedback."}
            )

        if category and category not in RESPONSE_FEEDBACK_CATEGORY_VALUES:
            raise serializers.ValidationError({"category": "Invalid feedback category."})

        if rating == RATING_UP:
            category = ""
            details = ""

        attrs["category"] = category
        attrs["details"] = details
        return attrs

    def validate_message_id(self, value):
        request = self.context["request"]
        try:
            message = Message.objects.select_related("chat").get(pk=value)
        except Message.DoesNotExist as exc:
            raise serializers.ValidationError("Message not found.") from exc

        if message.role != "assistant":
            raise serializers.ValidationError(
                "Feedback can only be submitted on assistant responses."
            )

        chat = message.chat
        user = request.user
        if not (user.is_staff or user.is_superuser or chat.user_id == user.id):
            raise serializers.ValidationError(
                "You do not have permission to rate this message."
            )

        self.context["message"] = message
        self.context["chat"] = chat
        return value


class ResponseFeedbackSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField(source="message.id", read_only=True)
    chat_id = serializers.IntegerField(source="chat.id", read_only=True)
    category_label = serializers.SerializerMethodField()

    class Meta:
        model = ResponseFeedback
        fields = [
            "id",
            "message_id",
            "chat_id",
            "rating",
            "category",
            "category_label",
            "details",
            "user_question",
            "assistant_response",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_category_label(self, obj):
        if not obj.category:
            return ""
        return dict(RESPONSE_FEEDBACK_CATEGORIES).get(obj.category, obj.category)


class ResponseFeedbackSummarySerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField(source="message.id", read_only=True)

    class Meta:
        model = ResponseFeedback
        fields = ["message_id", "rating", "category", "updated_at"]
        read_only_fields = fields
