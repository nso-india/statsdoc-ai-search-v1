import os

from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from uploader.file_response_utils import build_file_download_response

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
                status=status.HTTP_401_UNAUTHORIZED,
            )

        file_path = attachment.file.path
        if not os.path.isfile(file_path):
            raise Http404("File not found")

        return build_file_download_response(
            file_path,
            download_name=attachment.original_filename,
            inline=True,
        )

    def _has_access(self, request, attachment_id):
        access_token = (request.query_params.get("access") or "").strip()
        if access_token:
            try:
                return verify_feedback_attachment_access(attachment_id, access_token)
            except (BadSignature, SignatureExpired):
                return False

        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.is_staff)
