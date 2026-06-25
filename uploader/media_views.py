"""
Views for serving protected media files
"""
import os
import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import Http404, HttpResponse
from django.utils.http import content_disposition_header
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import authentication_classes

from .file_response_utils import build_file_download_response


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def serve_protected_media(request, file_path):
    """
    Serve media files only to authenticated users.
    Uses FileResponse by default; optional X-Accel-Redirect when nginx is configured.
    """
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)

    media_root = Path(settings.MEDIA_ROOT).resolve()
    requested_path = Path(full_path).resolve()

    if not str(requested_path).startswith(str(media_root)):
        raise Http404("Invalid file path")

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise Http404("File not found")

    content_type, _ = mimetypes.guess_type(full_path)
    if not content_type:
        content_type = "application/octet-stream"

    filename = os.path.basename(full_path)
    use_x_accel = getattr(settings, "USE_X_ACCEL_REDIRECT", False)

    if use_x_accel:
        response = HttpResponse()
        response["X-Accel-Redirect"] = f"/protected-media/{file_path}"
        response["Content-Type"] = content_type
        response.headers["Content-Disposition"] = content_disposition_header(
            as_attachment=False,
            filename=filename,
        )
        return response

    return build_file_download_response(full_path, download_name=filename, inline=True)
