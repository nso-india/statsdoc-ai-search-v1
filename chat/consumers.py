import json
import logging
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, Message
from .utils import get_llm_response
from uploader.models import KnowledgeBase

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close()
            return

        # Store the authenticated user as an instance variable
        self.user = user
        
        # Initialize knowledge_base_id to None
        self.knowledge_base_id = None

        try:
            chat_id = self.scope['url_route']['kwargs'].get('chat_id')
            
            # Extract knowledge_base_id from query string
            query_string = self.scope.get('query_string', b'').decode('utf-8')
            query_params = parse_qs(query_string)
            knowledge_base_id_str = query_params.get('knowledge_base_id', [None])[0]
            if knowledge_base_id_str:
                try:
                    knowledge_base_id = int(knowledge_base_id_str)
                    logger.info(f"Knowledge Base ID from query string: {knowledge_base_id}")
                    # Store for later use in receive()
                    self.knowledge_base_id = knowledge_base_id
                except (ValueError, TypeError):
                    knowledge_base_id = None
                    logger.warning(f"Invalid knowledge_base_id in query string: {knowledge_base_id_str}")
            else:
                knowledge_base_id = None
                logger.info("No knowledge_base_id in query string")
            
            # Only get/create chat if chat_id is provided (existing chat)
            # For new chats, wait until first message is sent in receive()
            if chat_id:
                self.chat = await self.get_or_create_chat(chat_id, knowledge_base_id=knowledge_base_id)
                self.room_group_name = self.chat.get_room_group_name()

                # Join room group
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )

                await self.accept()

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': {
                            'id': self.chat.id,
                            'title': self.chat.title,
                            'user': self.user.username
                        }
                    }
                )

                # Check if there are any files being processed and send loading if needed
                has_active_processing = await self.check_active_file_processing()
                if has_active_processing:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'loading_message',
                            'loading': True
                        }
                    )
            else:
                # New chat - just accept connection, don't create chat yet
                # Chat will be created when first message is sent
                await self.accept()
                logger.info("WebSocket connected for new chat, waiting for first message")
                
        except ValueError as e:
            # Close connection if daily chat limit is reached during connect
            await self.close(code=4000, reason=str(e))
            return
    async def disconnect(self, close_code):
        # Leave room group only if it was set
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            if text_data_json.get("edit_message_id"):
                await self.handle_edit_message(text_data_json)
                return

            message_content = text_data_json['message']
            chat_id = text_data_json.get('chat_id')
            language_id = text_data_json.get('language_id', None)

            try:
                chat = await self.get_or_create_chat(chat_id, message_content, knowledge_base_id=self.knowledge_base_id)
            except ValueError as e:
                # Send error message for daily chat limit
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': str(e)
                }))
                return
            
            # If this is a new chat (no room group yet), set it up
            if not hasattr(self, 'room_group_name'):
                self.room_group_name = chat.get_room_group_name()
                # Join room group
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                logger.info(f"New chat created via receive(), joined room group: {self.room_group_name}")

            # Save user message with validation
            try:
                user_message = await self.save_message(chat, 'user', message_content)
            except ValueError as e:
                # Send error message for validation failures
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': str(e)
                }))
                return

            # Send user message to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': user_message.id,
                        'role': 'user',
                        'content': message_content,
                        'timestamp': user_message.created_at.isoformat(),
                        'chat_id': chat.id
                    }
                }
            )

            # Send loading message
            await self.send_loading_message(chat, True)

            response = await get_llm_response(chat, user_message, language_id)

            # Create complete response structure for database storage
            complete_response = {
                'content': response
            }

            # Save assistant message with complete JSON structure
            assistant_message = await self.save_message(chat, 'assistant', json.dumps(complete_response))

            # Send loading stop
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'loading_message',
                    'loading': False
                }
            )

            # Send assistant message to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': assistant_message.id,
                        'role': 'assistant',
                        'content': response,
                        'timestamp': assistant_message.created_at.isoformat(),
                        'chat_id': chat.id
                    }
                }
            )

        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': f'Error processing message: {str(e)}'
            }))

    async def handle_edit_message(self, data):
        """Edit a prior user prompt and regenerate the assistant response."""
        message_content = (data.get("message") or "").strip()
        chat_id = data.get("chat_id")
        language_id = data.get("language_id")
        edit_message_id = data.get("edit_message_id")

        if not message_content:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Message cannot be empty.",
            }))
            return

        try:
            chat = await self.get_or_create_chat(
                chat_id,
                None,
                knowledge_base_id=self.knowledge_base_id,
            )
        except ValueError as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": str(e),
            }))
            return

        if not hasattr(self, "room_group_name"):
            self.room_group_name = chat.get_room_group_name()
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name,
            )

        try:
            user_message = await self.edit_user_message(
                chat,
                edit_message_id,
                message_content,
            )
        except ValueError as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": str(e),
            }))
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": user_message.id,
                    "role": "user",
                    "content": message_content,
                    "timestamp": user_message.created_at.isoformat(),
                    "chat_id": chat.id,
                },
            },
        )

        await self.send_loading_message(chat, True)

        try:
            response = await get_llm_response(chat, user_message, language_id)
            complete_response = {"content": response}
            assistant_message = await self.save_message(
                chat,
                "assistant",
                json.dumps(complete_response),
            )
        except Exception as e:
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "loading_message", "loading": False},
            )
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Error processing message: {str(e)}",
            }))
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "loading_message", "loading": False},
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": assistant_message.id,
                    "role": "assistant",
                    "content": response,
                    "timestamp": assistant_message.created_at.isoformat(),
                    "chat_id": chat.id,
                },
            },
        )

    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message
        }))

    async def loading_message(self, event):
        # Send loading status to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'loading',
            'loading': event['loading']
        }))

    @database_sync_to_async
    def get_or_create_chat(self, chat_id=None, message_content=None, knowledge_base_id=None):
        # self.user is guaranteed to exist because we check it in connect()
        if chat_id:
            try:
                chat = Chat.objects.get(id=chat_id, user=self.user)
                return chat
            except Chat.DoesNotExist:
                pass

        # Check daily chat limit before creating new chat
        from django.utils import timezone
        from application_settings.utils import ConfigManager, validate_daily_chats
        
        today = timezone.now().date()
        daily_chats = Chat.objects.filter(
            user=self.user,
            created_at__date=today
        ).count()
        
        daily_limit = ConfigManager.get_chats_per_day()
        if not validate_daily_chats(daily_chats + 1):
            raise ValueError(
                f'Daily chat limit of {daily_limit} reached. '
                f'You have already created {daily_chats} chats today.'
            )

        # Get knowledge_base if provided
        knowledge_base = None
        if knowledge_base_id:
            try:
                knowledge_base = KnowledgeBase.objects.get(id=knowledge_base_id)
                logger.info(f"Found knowledge base: {knowledge_base.name} (ID: {knowledge_base_id})")
            except KnowledgeBase.DoesNotExist:
                logger.warning(f"Knowledge base with ID {knowledge_base_id} not found")
                pass  # Continue without knowledge base if not found

        # Create new chat with title from first few characters
        if message_content:
            title = message_content[:50] + "..." if len(message_content) > 50 else message_content
        else:
            title = "New Chat"
        chat = Chat.objects.create(
            user=self.user, 
            title=title,
            knowledge_base=knowledge_base
        )
        logger.info(f"Created new chat {chat.id} with knowledge_base: {knowledge_base.name if knowledge_base else 'None'}")
        return chat

    @database_sync_to_async
    def save_message(self, chat, role, content):
        # Only validate question limits for user messages
        if role == 'user':
            from application_settings.utils import ConfigManager, validate_questions_count
            
            # Count existing user messages in this chat
            current_questions = Message.objects.filter(chat=chat, role='user').count()
            questions_limit = ConfigManager.get_questions_per_chat()
            
            if not validate_questions_count(current_questions + 1):  # +1 for current question
                raise ValueError(
                    f'Questions per chat limit of {questions_limit} reached. '
                    f'This chat already has {current_questions} questions.'
                )
        
        return Message.objects.create(
            chat=chat,
            role=role,
            content=content
        )

    @database_sync_to_async
    def edit_user_message(self, chat, message_id, new_content):
        try:
            message = Message.objects.select_related("chat").get(
                id=message_id,
                chat=chat,
                chat__user=self.user,
                role="user",
            )
        except Message.DoesNotExist as exc:
            raise ValueError("Message not found or cannot be edited.") from exc

        Message.objects.filter(chat=chat, created_at__gt=message.created_at).delete()
        message.content = new_content
        message.save(update_fields=["content"])
        return message

    @database_sync_to_async
    def check_active_file_processing(self):
        from uploader.models import UploadedFile
        from uploader.constants import PENDING, IN_PROGRESS
        return UploadedFile.objects.filter(
            chat=self.chat,
            status__in=[PENDING, IN_PROGRESS]
        ).exists()

    async def send_loading_message(self, chat, loading):
        await self.channel_layer.group_send(
            chat.get_room_group_name(),
            {
                'type': 'loading_message',
                'loading': loading
            }
        )

    @staticmethod
    async def send_message(chat, message, message_type):
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            chat.get_room_group_name(),
            {
                'type': message_type,
                'message': message
            }
        )

    @staticmethod
    async def send_loading_message(chat, loading):
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            chat.get_room_group_name(),
            {
                'type': 'loading_message',
                'loading': loading
            }
        )
