import logging
import mimetypes
import os

from django.http import FileResponse, Http404
from django.utils.http import content_disposition_header

logger = logging.getLogger(__name__)


def build_file_download_response(
    file_path,
    *,
    download_name=None,
    inline=True,
):
    """Return a FileResponse for an on-disk file with a safe Content-Disposition."""
    if not file_path or not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise Http404("File not found")

    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = "application/octet-stream"

    filename = download_name or os.path.basename(file_path)

    try:
        file_handle = open(file_path, "rb")
    except OSError:
        logger.exception("Unable to read file at %s", file_path)
        raise Http404("File not found") from None

    response = FileResponse(file_handle, content_type=content_type)
    response.headers["Content-Disposition"] = content_disposition_header(
        as_attachment=not inline,
        filename=filename,
    )
    return response
