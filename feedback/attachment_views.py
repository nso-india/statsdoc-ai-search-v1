import mimetypes
import os

from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.http import FileResponse, Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import FeedbackAttachment

ATTACHMENT_SIGN_SALT = "feedback-attachment-download"
ATTACHMENT_SIGN_MAX_AGE = 60 * 60 * 24 * 7  # 7 days for Excel export links


def sign_feedback_attachment_id(attachment_id):
    return TimestampSigner(salt=ATTACHMENT_SIGN_SALT).sign(str(attachment_id))


def verify_feedback_attachment_access(attachment_id, access_token):
    unsigned = TimestampSigner(salt=ATTACHMENT_SIGN_SALT).unsign(
        access_token, max_age=ATTACHMENT_SIGN_MAX_AGE
    )
    return unsigned == str(attachment_id)


class FeedbackAttachmentDownloadView(APIView):
    """Staff JWT or signed export link download for feedback attachments."""

    authentication_classes = [JWTAuthentication]
    permission_classes = []

    def get(self, request, attachment_id):
        try:
            attachment = FeedbackAttachment.objects.get(pk=attachment_id)
        except FeedbackAttachment.DoesNotExist as exc:
            raise Http404("Attachment not found") from exc

        if not self._has_access(request, attachment.id):
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=403,
            )

        file_path = attachment.file.path
        if not os.path.isfile(file_path):
            raise Http404("File not found")

        content_type = attachment.content_type or mimetypes.guess_type(file_path)[0]
        if not content_type:
            content_type = "application/octet-stream"

        response = FileResponse(open(file_path, "rb"), content_type=content_type)
        response["Content-Disposition"] = (
            f'inline; filename="{attachment.original_filename}"'
        )
        return response

    def _has_access(self, request, attachment_id):
        access_token = (request.query_params.get("access") or "").strip()
        if access_token:
            try:
                return verify_feedback_attachment_access(attachment_id, access_token)
            except (BadSignature, SignatureExpired):
                return False

        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.is_staff)
