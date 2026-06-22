from rest_framework import serializers



from user_management.serializers import StrictFieldValidationMixin



from .constants import CATEGORY_GENERAL

from .models import Feedback, FeedbackAttachment





class FeedbackAttachmentSerializer(serializers.ModelSerializer):

    url = serializers.SerializerMethodField()



    class Meta:

        model = FeedbackAttachment

        fields = [

            "id",

            "original_filename",

            "content_type",

            "file_size",

            "url",

            "created_at",

        ]

        read_only_fields = fields



    def get_url(self, obj):

        request = self.context.get("request")

        if request:

            return request.build_absolute_uri(obj.file.url)

        return obj.file.url





class FeedbackCreateSerializer(StrictFieldValidationMixin, serializers.ModelSerializer):

    """Public serializer for submitting feedback (simple form — no category field)."""



    website = serializers.CharField(required=False, allow_blank=True, write_only=True)



    class Meta:

        model = Feedback

        fields = [

            "name",

            "email",

            "subject",

            "message",

            "page_url",

            "website",

        ]



    def validate_subject(self, value):

        value = value.strip()

        if not value:

            raise serializers.ValidationError("Subject is required.")

        if len(value) > 200:

            raise serializers.ValidationError("Subject must be 200 characters or fewer.")

        return value



    def validate_message(self, value):

        value = value.strip()

        if not value:

            raise serializers.ValidationError("Message is required.")

        if len(value) > 2000:

            raise serializers.ValidationError("Message must be 2000 characters or fewer.")

        return value

    def to_internal_value(self, data):
        # Files are handled via request.FILES in the view.
        if hasattr(data, "copy"):
            data = data.copy()
            if hasattr(data, "_mutable"):
                data._mutable = True
            data.pop("attachments", None)
        elif isinstance(data, dict):
            data = {key: value for key, value in data.items() if key != "attachments"}
        return super().to_internal_value(data)

    def validate(self, attrs):

        if attrs.get("website", "").strip():

            raise serializers.ValidationError({"detail": "Invalid submission."})



        request = self.context.get("request")

        user = getattr(request, "user", None)

        if user and user.is_authenticated:

            attrs["name"] = user.get_full_name() or user.email.split("@")[0]

            attrs["email"] = user.email

        else:

            attrs["name"] = attrs.get("name", "").strip()

            attrs["email"] = attrs.get("email", "").strip().lower()

            if not attrs["name"]:

                raise serializers.ValidationError({"name": "Name is required."})

            if not attrs["email"]:

                raise serializers.ValidationError({"email": "Email is required."})



        attrs.pop("website", None)

        return attrs



    def create(self, validated_data):

        request = self.context.get("request")

        user = getattr(request, "user", None)

        if user and user.is_authenticated:

            validated_data["user"] = user

        validated_data["category"] = CATEGORY_GENERAL

        return Feedback.objects.create(**validated_data)





class FeedbackSerializer(serializers.ModelSerializer):

    """Staff read serializer."""



    attachments = FeedbackAttachmentSerializer(many=True, read_only=True)



    class Meta:

        model = Feedback

        fields = [

            "id",

            "user",

            "name",

            "email",

            "category",

            "subject",

            "message",

            "page_url",

            "status",

            "attachments",

            "created_at",

            "updated_at",

        ]

        read_only_fields = fields


