from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Language(models.Model):
    """Model to store supported languages for chat responses"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True, help_text="Language code (e.g., 'en', 'hi', 'kn')")
    name = models.CharField(max_length=100, help_text="Language name (e.g., 'English', 'Hindi', 'Kannada')")
    is_active = models.BooleanField(default=True, help_text="Whether this language is available for selection")
    display_order = models.IntegerField(default=0, help_text="Order in which to display in dropdown (lower = first)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Language'
        verbose_name_plural = 'Languages'

    def __str__(self):
        return self.name


class Chat(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chats"
    )
    title = models.CharField(max_length=100)
    knowledge_base = models.ForeignKey(
        "uploader.KnowledgeBase",
        on_delete=models.SET_NULL,
        related_name="chats",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['knowledge_base', '-created_at']),
        ]

    def get_room_group_name(self):
        return f"chat_{self.id}"

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class Message(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=['chat', 'created_at']),
        ]

    def __str__(self):
        return f"{self.chat.title} - {self.role}: {self.content[:50]}..."
