from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Chat with specific ID and optional knowledge_base_id
    re_path(r'^ws/chat/(?P<chat_id>[^/]+)/(?P<knowledge_base_id>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
    # Chat with specific ID only
    re_path(r'^ws/chat/(?P<chat_id>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
    # Chat without ID (will create new chat, with optional knowledge_base_id query param)
    re_path(r'^ws/chat/$', consumers.ChatConsumer.as_asgi()),
]