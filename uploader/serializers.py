from rest_framework import serializers
from .models import UploadedFile, Comment, KnowledgeBase
from .tasks import process_uploaded_file
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import os
import mimetypes

User = get_user_model()


class StrictFieldValidationMixin:
    """Mixin to reject unexpected fields in serializers"""
    
    def to_internal_value(self, data):
        """Override to validate that only expected fields are provided"""
        if isinstance(data, dict):
            # Get allowed field names
            allowed_fields = set(self.fields.keys())
            provided_fields = set(data.keys())
            
            # Check for unexpected fields
            unexpected_fields = provided_fields - allowed_fields
            if unexpected_fields:
                raise serializers.ValidationError({
                    'detail': f'Unexpected parameters: {", ".join(sorted(unexpected_fields))}',
                    'rejected_fields': sorted(list(unexpected_fields))
                })
        
        return super().to_internal_value(data)


# Allowed file extensions and MIME types for security
ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.csv', '.json', '.xml', '.html', '.htm',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
    '.zip', '.tar', '.gz'
}

ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain',
    'text/csv',
    'application/json',
    'text/xml',
    'application/xml',
    'text/html',
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/bmp',
    'image/tiff',
    'application/zip',
    'application/x-tar',
    'application/gzip',
}

def validate_file_upload(file):
    """
    Validate file uploads to prevent double extension and malicious file uploads.
    
    Args:
        file: The uploaded file object
        
    Raises:
        ValidationError: If the file fails validation
    """
    # Get the original filename
    filename = file.name
    
    # Check for null bytes (path traversal attempt)
    if '\x00' in filename:
        raise ValidationError("Invalid file name: null bytes detected")
    
    # Check for path traversal patterns
    if '..' in filename or '/' in filename or '\\' in filename:
        raise ValidationError("Invalid file name: path traversal attempt detected")
    
    # Convert filename to lowercase for case-insensitive comparison
    filename_lower = filename.lower()
    
    # Extract all extensions from the filename (handle double extensions)
    parts = filename_lower.split('.')
    if len(parts) < 2:
        raise ValidationError("File must have an extension")
    
    # Get the actual extension (last part)
    actual_extension = '.' + parts[-1]
    
    # Check if the actual extension is allowed
    if actual_extension not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type '{actual_extension}' is not allowed. "
            f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    
    # Check for double extensions (e.g., file.pdf.exe)
    if len(parts) > 2:
        # Check if any intermediate part looks like an extension
        for part in parts[1:-1]:
            if len(part) <= 4:  # Typical extension length
                potential_ext = '.' + part
                # If it looks like a dangerous extension, reject
                dangerous_exts = {'.exe', '.bat', '.cmd', '.sh', '.php', '.jsp', '.asp', '.js'}
                if potential_ext in dangerous_exts:
                    raise ValidationError(
                        f"Double extension detected: {filename}. This is not allowed for security reasons."
                    )
    
    # Validate MIME type
    try:
        content_type = file.content_type
        if content_type and content_type not in ALLOWED_MIME_TYPES:
            # Also check against guessed MIME type from filename
            guessed_type, _ = mimetypes.guess_type(filename)
            if not guessed_type or guessed_type not in ALLOWED_MIME_TYPES:
                raise ValidationError(
                    f"MIME type '{content_type}' is not allowed"
                )
    except AttributeError:
        # If content_type is not available, rely on extension validation
        pass
    
    # Check file size (limit to 100MB)
    max_size = 100 * 1024 * 1024  # 100MB in bytes
    if file.size > max_size:
        raise ValidationError(f"File size exceeds maximum allowed size of 100MB")
    
    return True


class KnowledgeBaseSerializer(StrictFieldValidationMixin, serializers.ModelSerializer):
    """
    Serializer for KnowledgeBase model
    """
    files_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = KnowledgeBase
        fields = ("id", "name", "description", "created_at", "updated_at", "files_count")
        read_only_fields = ("id", "created_at", "updated_at")

    def get_files_count(self, obj):
        """Return the number of files in this knowledge base"""
        return obj.files.count()


class UploadedFileSerializer(StrictFieldValidationMixin, serializers.ModelSerializer):
    file_name = serializers.CharField(source="file.name", read_only=True)
    file_url = serializers.SerializerMethodField(read_only=True)
    other_info = serializers.JSONField(required=False)
    knowledge_base_id = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = UploadedFile
        fields = ("id", "file", "file_name", "file_url", "uploaded_at", "other_info", "status", "knowledge_base_id", "knowledge_base")
        read_only_fields = ("id", "uploaded_at", "status", "knowledge_base", "file_url")
    
    def get_file_url(self, obj):
        """Return the URL of the uploaded file"""
        if obj.file:
            return obj.file.url
        return None

    def validate_file(self, file):
        """
        Validate the uploaded file before processing.
        """
        validate_file_upload(file)
        return file
    
    def create(self, validated_data):
        file = validated_data.get("file")
        file_name = file.name
        knowledge_base_id = validated_data.pop("knowledge_base_id", None)
        
        # Set the file name to the file field
        validated_data["file_name"] = file_name
        validated_data["other_info"] = validated_data.get("other_info", {})
        
        # Set knowledge_base if provided
        if knowledge_base_id:
            from .models import KnowledgeBase
            try:
                knowledge_base = KnowledgeBase.objects.get(id=knowledge_base_id)
                validated_data["knowledge_base"] = knowledge_base
            except KnowledgeBase.DoesNotExist:
                pass  # If knowledge base doesn't exist, continue without it
        
        # Call the Celery task to process the file
        file = super().create(validated_data)
        kb_id = validated_data.get('knowledge_base').id if validated_data.get('knowledge_base') else None
        process_uploaded_file.delay(file.id, knowledge_base_id=kb_id)
        print(f"File name: {file_name}")
        return file


class UserProfileSerializer(StrictFieldValidationMixin, serializers.ModelSerializer):
    """
    A simple serializer for viewing user profile information.
    Only includes username and email.
    """

    class Meta:
        model = User
        fields = ("username", "email")


class DocLingJSONSerializer(StrictFieldValidationMixin, serializers.ModelSerializer):
    """
    Serializer for returning DocLing JSON data from uploaded files
    """

    class Meta:
        model = UploadedFile
        fields = ("id", "file_name", "docling_json")
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        docling_json = data.get("docling_json")
        # Ensure 'pages' property exists
        if docling_json is not None and "pages" not in docling_json:
            # Try to create pages from texts array if available
            if (
                isinstance(docling_json.get("texts"), list)
                and len(docling_json["texts"]) > 0
            ):
                docling_json["pages"] = {
                    str(i + 1): text for i, text in enumerate(docling_json["texts"])
                }
            elif docling_json.get("body") is not None:
                docling_json["pages"] = {"1": docling_json["body"]}
            else:
                docling_json["pages"] = {}
        data["docling_json"] = docling_json
        return data


class CommentSerializer(StrictFieldValidationMixin, serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = (
            "id",
            "comment",
            "comment_type",
            "target_ref",
            "source_ref",
            "created_at",
            "status",
        )
        read_only_fields = ("id", "created_at", "status")
