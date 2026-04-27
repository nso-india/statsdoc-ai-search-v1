"""
Views for serving protected media files
"""
import os
import mimetypes
from django.http import HttpResponse, Http404, FileResponse
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from pathlib import Path


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def serve_protected_media(request, file_path):
    """
    Serve media files only to authenticated users using X-Accel-Redirect
    """
    # Construct the full file path
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    
    # Security check: ensure the path is within MEDIA_ROOT
    media_root = Path(settings.MEDIA_ROOT).resolve()
    requested_path = Path(full_path).resolve()
    
    if not str(requested_path).startswith(str(media_root)):
        raise Http404("Invalid file path")
    
    # Check if file exists
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise Http404("File not found")
    
    # Use X-Accel-Redirect for efficient serving through nginx
    # This allows nginx to serve the file while Django handles authentication
    response = HttpResponse()
    response['X-Accel-Redirect'] = f'/protected-media/{file_path}'
    
    # Set content type
    content_type, _ = mimetypes.guess_type(full_path)
    if content_type:
        response['Content-Type'] = content_type
    
    # Set content disposition for downloads
    filename = os.path.basename(full_path)
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response
