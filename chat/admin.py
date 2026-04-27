from django.contrib import admin
from .models import Chat, Message, Language


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'display_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('display_order', 'name')
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'display_order')
        }),
    )


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['title', 'user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['chat', 'role', 'content_preview', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content', 'chat__title']
    readonly_fields = ['created_at']

    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'
