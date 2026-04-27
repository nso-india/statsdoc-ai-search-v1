from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from django.http import FileResponse, Http404
import os
import mimetypes
from django.conf import settings

from .models import UploadedFile, Comment, KnowledgeBase
from .serializers import (
    UploadedFileSerializer,
    UserProfileSerializer,
    DocLingJSONSerializer,
    CommentSerializer,
    KnowledgeBaseSerializer,
)
from user_management.permissions import IsStaffUser

from .tasks import process_reviewed_file


class FileUploadView(generics.ListCreateAPIView):
    """
    File upload view.
    GET: List files (any authenticated user)
    POST: Upload files - Admin only.
    """
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsStaffUser()]
        return [IsAuthenticated()]

    queryset = UploadedFile.objects.all()
    serializer_class = UploadedFileSerializer

    def get_queryset(self):
        """
        Filter uploaded files by knowledge_base query parameter if provided.
        Also use select_related to optimize database queries.
        """
        queryset = UploadedFile.objects.select_related('knowledge_base', 'chat').all()
        
        # Filter by knowledge_base if provided in query params
        knowledge_base_id = self.request.query_params.get('knowledge_base')
        if knowledge_base_id:
            queryset = queryset.filter(knowledge_base_id=knowledge_base_id)
        
        # Order by most recent first
        return queryset.order_by('-uploaded_at')

    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist("file")  # "file" must match the form field name
        other_info = request.data.get("other_info", {})
        knowledge_base_id = request.data.get("knowledge_base_id")

        results = []
        errors = []

        for file in files:
            data = {
                "file": file, 
                "other_info": other_info
            }
            
            # Add knowledge_base_id if provided
            if knowledge_base_id:
                data["knowledge_base_id"] = knowledge_base_id
            
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                serializer.save()
                results.append(serializer.data)
            else:
                errors.append(serializer.errors)

        if errors:
            return Response(
                {"success": results, "errors": errors},
                status=status.HTTP_207_MULTI_STATUS,
            )
        return Response(results, status=status.HTTP_201_CREATED)


class FileReview(APIView):
    """
    API view for reviewing files.
    """
    authentication_classes = [JWTAuthentication]

    def post(self, request, file_id):
        # file_id now comes from the URL parameter
        if not file_id:
            return Response(
                {"detail": "File ID is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            file_obj = UploadedFile.objects.get(pk=file_id)
        except UploadedFile.DoesNotExist:
            return Response(
                {"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND
            )

        file_obj.reviewed = True
        file_obj.save()

        process_reviewed_file.delay(file_id)

        return Response(
            {"detail": "File reviewed successfully."}, status=status.HTTP_200_OK
        )


class ProfileView(APIView):
    """
    API view for retrieving the current user's profile information.
    Returns only the username and email fields.
    """

    authentication_classes = [JWTAuthentication]

    def get(self, request):
        """Get the current user's profile information"""
        # The user is already authenticated via JWT, so request.user is available
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RawFileView(APIView):
    """
    API view for retrieving the raw, unprocessed file content.
    Returns the actual file content.
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request, pk):
        try:
            file_obj = UploadedFile.objects.get(pk=pk)
        except UploadedFile.DoesNotExist:
            raise Http404("File not found")

        # Check if file exists on disk
        if not file_obj.file or not os.path.exists(file_obj.file.path):
            return Response(
                {"detail": "File does not exist on disk."},
                status=status.HTTP_404_NOT_FOUND,
            )

        content_type, _ = mimetypes.guess_type(file_obj.file.path)
        if not content_type:
            content_type = "application/octet-stream"

        response = FileResponse(
            open(file_obj.file.path, "rb"), content_type=content_type
        )

        filename = os.path.basename(file_obj.file.name)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response


class ProcessedFileView(APIView):
    """
    API view for retrieving the file after Docling processing.
    Returns the processed file data in a structured format.
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request, pk):
        try:
            file_obj = UploadedFile.objects.get(pk=pk)
        except UploadedFile.DoesNotExist:
            raise Http404("File not found")

        if not file_obj.docling_json:
            return Response(
                {"detail": "File has not been processed yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "id": file_obj.id,
            "file_name": file_obj.file_name,
            "uploaded_at": file_obj.uploaded_at,
            "status": file_obj.status,
            "docling_data": file_obj.docling_json
        })


class DocLingJSONView(APIView):
    """
    API view for retrieving DocLing JSON data for a specific file by ID
    """

    authentication_classes = [JWTAuthentication]

    def get(self, request, file_id):
        """
        Retrieve DocLing JSON data for a file with the given ID
        """
        try:
            file = UploadedFile.objects.get(id=file_id)
            serializer = DocLingJSONSerializer(file)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UploadedFile.DoesNotExist:
            return Response(
                {"detail": "File not found"}, status=status.HTTP_404_NOT_FOUND
            )


class AICommentsView(APIView):
    """
    API view for retrieving AI-generated comments for a specific file
    """

    authentication_classes = [JWTAuthentication]
    serializer_class = CommentSerializer

    def get(self, request, **kwargs):
        """
        Retrieve AI comments for a file with the given ID
        """
        file_id = kwargs.get("file_id")
        try:
            file = UploadedFile.objects.get(id=file_id)
            comments = Comment.objects.filter(file=file)

            serializer = self.serializer_class(comments, many=True)
            final_data = {
                "file_id": file_id,
                "file_name": file.file_name,
                "comments": serializer.data
            }
            return Response(final_data, status=status.HTTP_200_OK)
        except UploadedFile.DoesNotExist:
            return Response(
                {"detail": "File not found"}, status=status.HTTP_404_NOT_FOUND
            )


class KnowledgeBaseView(generics.ListCreateAPIView):
    """
    API view for creating and listing knowledge bases.
    GET: List all knowledge bases (any authenticated user)
    POST: Create a new knowledge base (staff/admin only)
    """
    authentication_classes = [JWTAuthentication]
    queryset = KnowledgeBase.objects.all()
    serializer_class = KnowledgeBaseSerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsStaffUser()]
        return [IsAuthenticated()]


class KnowledgeBaseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a specific knowledge base.
    GET: Retrieve a knowledge base by ID (any authenticated user)
    PUT/PATCH: Update a knowledge base (staff/admin only)
    DELETE: Delete a knowledge base (staff/admin only)
    """
    authentication_classes = [JWTAuthentication]
    queryset = KnowledgeBase.objects.all()
    serializer_class = KnowledgeBaseSerializer
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated(), IsStaffUser()]
        return [IsAuthenticated()]


class FileDeleteView(APIView):
    """
    API view for deleting individual files from knowledge base.
    Deletes both the file record and its associated Qdrant vectors.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsStaffUser]

    def delete(self, request, file_id):
        try:
            file_obj = UploadedFile.objects.get(pk=file_id)
        except UploadedFile.DoesNotExist:
            return Response(
                {"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Delete Qdrant vectors associated with this file
        try:
            from qdrant_adapter.qdrant_adapter import init_connection
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue
            from django.conf import settings

            qdrant_client = init_connection()
            
            # Delete all points where file_id matches
            qdrant_client.delete(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points_selector=Filter(
                    must=[FieldCondition(key="file_id", match=MatchValue(value=file_id))]
                )
            )
            print(f"Deleted Qdrant vectors for file {file_id}")
        except Exception as e:
            print(f"Error deleting Qdrant vectors for file {file_id}: {e}")
            # Continue with file deletion even if Qdrant deletion fails

        # Delete the file record (this will also delete the physical file due to FileField behavior)
        file_name = file_obj.file_name
        file_obj.delete()

        return Response(
            {"detail": f"File '{file_name}' and its vectors deleted successfully."},
            status=status.HTTP_200_OK
        )


class TranscribeAudioView(APIView):
    """Server-side transcription proxy for audio files.

    - Accepts multipart form data with a `file` field (audio blob)
    - Optional `language` form field for Whisper
    - Requires JWT authentication (keeps transcription API key on server)
    - Returns JSON with `text` or `transcription` field

    Notes: Uses a Whisper-compatible client if available and expects a transcription API key
    to be set in the environment or Django settings.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Log whether an Authorization header is present and whether the request is authenticated
        auth_present = bool(request.META.get("HTTP_AUTHORIZATION"))
        print(f"TranscribeAudioView: Authorization header present={auth_present}")
        is_auth = getattr(request.user, "is_authenticated", False)
        print(f"TranscribeAudioView: request.user.is_authenticated={is_auth}")

        if not is_auth:
            # Explicitly return 401 for unauthenticated requests
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        audio = request.FILES.get("file")
        if not audio:
            return Response({"error": "Missing file"}, status=status.HTTP_400_BAD_REQUEST)

        # Basic safety checks
        max_size_bytes = 25 * 1024 * 1024  # 25 MB limit
        if audio.size > max_size_bytes:
            return Response({"error": "File too large"}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        language = request.data.get("language")
        model = request.data.get("model", "whisper-1")

        # Prefer an explicit transcription API key env var, else fall back to AI_COMMENTS_LLM_API_KEY
        transcription_api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "AI_COMMENTS_LLM_API_KEY", None)
        if not transcription_api_key:
            return Response({"error": "Whisper API key not configured on server"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".webm") as tmp:
            for chunk in audio.chunks():
                tmp.write(chunk)
            tmp.flush()

            try:
                text = ""

                # 1) Try modern OpenAI SDK (OpenAI client) which exposes audio.transcriptions.create
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=transcription_api_key)

                    if hasattr(client, "audio") and hasattr(client.audio, "transcriptions") and callable(getattr(client.audio.transcriptions, "create", None)):
                        with open(tmp.name, "rb") as f:
                            resp = client.audio.transcriptions.create(file=f, model=model, language=language)

                        text = getattr(resp, "text", None) or (resp.get("text") if isinstance(resp, dict) else None) or ""

                    # Some SDK variants may expose a different interface; try common alternatives
                    elif hasattr(client, "Audio") and callable(getattr(client.Audio, "transcribe", None)):
                        with open(tmp.name, "rb") as f:
                            resp = client.Audio.transcribe(model=model, file=f, response_format="json")
                        if isinstance(resp, dict):
                            text = resp.get("text") or resp.get("transcript") or ""
                        else:
                            text = getattr(resp, "text", None) or ""

                except Exception as client_exc:
                    # If this was an authentication error, return a clear 403 to the client
                    err_str = str(client_exc)
                    if '401' in err_str or 'Unauthorized' in err_str or getattr(client_exc, 'status', None) == 401 or getattr(client_exc, 'http_status', None) == 401:
                        print("Transcription error: Whisper API key unauthorized (401)")
                        return Response({"error": "Whisper API key unauthorized (401). Please check Whisper API key on server."}, status=status.HTTP_403_FORBIDDEN)

                    # 2) Fallback: try legacy openai package usage (openai.Audio.transcribe)
                    try:
                        import openai as openai_legacy
                        openai_legacy.api_key = transcription_api_key
                        with open(tmp.name, "rb") as f:
                            if hasattr(openai_legacy, "Audio") and callable(getattr(openai_legacy.Audio, "transcribe", None)):
                                resp = openai_legacy.Audio.transcribe(model=model, file=f, response_format="json")
                                if isinstance(resp, dict):
                                    text = resp.get("text") or resp.get("transcript") or ""
                                else:
                                    text = getattr(resp, "text", None) or ""
                            else:
                                # Not supported - raise to trigger REST fallback
                                raise client_exc
                    except Exception:
                        # 3) Final fallback: call the REST API directly
                        import requests
                        headers = {"Authorization": f"Bearer {transcription_api_key}"}
                        with open(tmp.name, "rb") as f:
                            files = {"file": (audio.name or "audio.webm", f)}
                            data = {"model": model}
                            if language:
                                data["language"] = language

                            r = requests.post("https://api.openai.com/v1/audio/transcriptions", headers=headers, files=files, data=data, timeout=120)

                        if r.status_code == 401:
                            print("Transcription error: 401 from Whisper REST API")
                            return Response({"error": "Whisper API key unauthorized (401). Please check Whisper API key on server."}, status=status.HTTP_403_FORBIDDEN)

                        r.raise_for_status()
                        resp_json = r.json()
                        text = resp_json.get("text") or resp_json.get("transcript") or ""

                return Response({"text": text}, status=status.HTTP_200_OK)

            except Exception as e:
                print(f"Transcription error: {e}")
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

