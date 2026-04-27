from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate, Length
from datetime import timedelta

from uploader.models import UploadedFile, KnowledgeBase
from uploader.tasks import process_chat_uploaded_file
from .models import Chat, Message, Language
from .serializers import ChatSerializer, ChatListSerializer, MessageSerializer, LanguageSerializer
from user_management.permissions import IsStaffUser
from django.conf import settings
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from qdrant_adapter.qdrant_adapter import init_connection
from application_settings.utils import ConfigManager, validate_file_size, validate_daily_chats

User = get_user_model()


class LanguageListView(generics.ListAPIView):
    """API endpoint to list all active languages"""
    serializer_class = LanguageSerializer
    permission_classes = [AllowAny]  # No authentication required
    queryset = Language.objects.filter(is_active=True)


class ChatListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Use lightweight serializer for list, full serializer for create"""
        if self.request.method == 'GET':
            return ChatListSerializer
        return ChatSerializer

    def get_queryset(self):
        if IsStaffUser().has_permission(self.request, self) or self.request.user.is_superuser:
            required_user = self.request.query_params.get("user")
            if required_user:
                required_user = get_object_or_404(User, id=required_user)
                return Chat.objects.filter(user=required_user)
        return Chat.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Check daily chat limit
        today = timezone.now().date()
        daily_chats = Chat.objects.filter(
            user=self.request.user,
            created_at__date=today
        ).count()
        
        daily_limit = ConfigManager.get_chats_per_day()
        if not validate_daily_chats(daily_chats + 1):  # +1 for the current chat being created
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'non_field_errors': [
                    f'Daily chat limit of {daily_limit} reached. You have already created {daily_chats} chats today.'
                ]
            })
        
        serializer.save(user=self.request.user)


class MessageListAPIView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        chat_id = self.kwargs['chat_id']
        
        # If user is superuser, they can access any chat directly
        if self.request.user.is_superuser:
            chat = get_object_or_404(Chat, id=chat_id)
            return Message.objects.filter(chat=chat)
        
        # If user is staff, they can access chats with user parameter
        if IsStaffUser().has_permission(self.request, self):
            required_user = self.request.query_params.get("user")
            if required_user:
                required_user = get_object_or_404(User, id=required_user)
                chat = get_object_or_404(Chat, id=chat_id, user=required_user)
                return Message.objects.filter(chat=chat)
        
        # Regular users can only access their own chats
        chat = get_object_or_404(Chat, id=chat_id, user=self.request.user)
        return Message.objects.filter(chat=chat)


class ChatDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        chat_id = self.kwargs['chat_id']
        try:
            chat = Chat.objects.get(id=chat_id, user=request.user)
            chat.delete()

            qdrant_client = init_connection()
            qdrant_client.delete(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points_selector=Filter(must=[FieldCondition(key="chat_id", match=MatchValue(value=chat_id))])
            )

            return Response({'message': 'Chat deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Chat.DoesNotExist:
            return Response({'error': 'Chat not found'}, status=status.HTTP_404_NOT_FOUND)


class ChatFileUploadAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist('file')
        prompt = request.data.get('prompt', '')
        chat_id = request.data.get('chat_id', None)
        knowledge_base_id = request.data.get('knowledge_base_id', None)
        
        # Validate file sizes
        file_size_limit_mb = ConfigManager.get_file_size_limit()
        for file in files:
            file_size_mb = file.size / (1024 * 1024)  # Convert bytes to MB
            if not validate_file_size(file_size_mb):
                return Response({
                    'error': f'File "{file.name}" size ({file_size_mb:.2f}MB) '
                             f'exceeds the limit of {file_size_limit_mb}MB.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            chat = Chat.objects.get(id=chat_id, user=self.request.user)
        except Chat.DoesNotExist:
            # Check daily chat limit before creating new chat
            today = timezone.now().date()
            daily_chats = Chat.objects.filter(
                user=self.request.user,
                created_at__date=today
            ).count()
            
            daily_limit = ConfigManager.get_chats_per_day()
            if not validate_daily_chats(daily_chats + 1):
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'non_field_errors': [
                        f'Daily chat limit of {daily_limit} reached. '
                        f'You have already created {daily_chats} chats today.'
                    ]
                })
            
            title = prompt[:50] + "..." if len(prompt) > 50 else prompt
            
            # Get knowledge_base if provided
            knowledge_base = None
            if knowledge_base_id:
                try:
                    knowledge_base = KnowledgeBase.objects.get(id=knowledge_base_id)
                except KnowledgeBase.DoesNotExist:
                    return Response({
                        'error': f'Knowledge base with id {knowledge_base_id} not found.'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            chat = Chat.objects.create(
                user=self.request.user, 
                title=title,
                knowledge_base=knowledge_base
            )

        file_data = []
        for file in files:
            uploaded_file = UploadedFile.objects.create(
                chat=chat, 
                file=file,
                knowledge_base=chat.knowledge_base
            )
            data = {
                'id': uploaded_file.id,
                'file_name': uploaded_file.file.name,
                'file_url': uploaded_file.file.url
            }
            file_data.append(data)

        content = {
            'content': prompt,
            'files': file_data
        }
        user_message = Message.objects.create(
            chat=chat,
            content=content,
            role='user'
        )
        language_id = request.data.get('language_id', None)
        process_chat_uploaded_file.delay(
            [file['id'] for file in file_data],
            chat.id,
            user_message.id,
            language_id
        )
        return Response({
            'message': 'File uploaded and processing started.',
            'chat_id': chat.id
        }, status=status.HTTP_201_CREATED)


class DeleteChatFileAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        chat_id = self.kwargs['chat_id']
        file_id = self.kwargs['file_id']
        try:
            uploaded_file = UploadedFile.objects.get(id=file_id, chat__id=chat_id, chat__user=request.user)
            
            # Delete Qdrant vectors associated with this file
            try:
                qdrant_client = init_connection()
                
                # Delete all points where file_id matches
                qdrant_client.delete(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    points_selector=Filter(
                        must=[FieldCondition(key="file_id", match=MatchValue(value=file_id))]
                    )
                )
                print(f"Deleted Qdrant vectors for chat file {file_id}")
            except Exception as e:
                print(f"Error deleting Qdrant vectors for chat file {file_id}: {e}")
                # Continue with file deletion even if Qdrant deletion fails
            
            uploaded_file.delete()
            return Response({'message': 'File deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except UploadedFile.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)


class AnalyticsDashboardView(APIView):
    """
    Analytics dashboard endpoint for super_admin
    Provides:
    - Number of chats day wise
    - Knowledge base counts
    """
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        # Check if user is staff or superuser
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"detail": "You don't have permission to access analytics."},
                status=403
            )

        # Get query parameters for date range
        days = int(request.query_params.get('days', 30))  # Default last 30 days
        start_date = timezone.now() - timedelta(days=days)

        # 1. Chats per day
        chats_per_day = (
            Chat.objects.filter(created_at__gte=start_date)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        # 2. Knowledge base counts
        kb_counts = (
            KnowledgeBase.objects.annotate(
                chat_count=Count('chats')
            )
            .values('id', 'name', 'chat_count')
            .order_by('-chat_count')
        )

        return Response({
            'chats_per_day': list(chats_per_day),
            'knowledge_base_counts': list(kb_counts),
            'date_range_days': days
        })
