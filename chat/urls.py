from django.urls import path
from .views import (
    ChatListCreateAPIView, 
    MessageListAPIView, 
    ChatDeleteAPIView, 
    ChatFileUploadAPIView, 
    DeleteChatFileAPIView,
    LanguageListView,
    AnalyticsDashboardView
)

app_name = 'chat'

urlpatterns = [
    path('languages/', LanguageListView.as_view(), name='language-list'),
    path('chats/', ChatListCreateAPIView.as_view(), name='chat-list-create'),
    path('chats/<int:chat_id>/messages/', MessageListAPIView.as_view(), name='message-list'),
    path('chats/<int:chat_id>/delete/', ChatDeleteAPIView.as_view(), name='chat-delete'),
    path('chats/upload/', ChatFileUploadAPIView.as_view(), name='chat-file-upload'),
    path('chats/<int:chat_id>/<int:file_id>/delete/', DeleteChatFileAPIView.as_view(), name='chat-file-delete'),
    
    # Analytics endpoints
    path('analytics/dashboard/', AnalyticsDashboardView.as_view(), name='analytics-dashboard'),
]
