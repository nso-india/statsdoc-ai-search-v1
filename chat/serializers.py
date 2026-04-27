import json
from rest_framework import serializers
from .models import Chat, Message, Language


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


class LanguageSerializer(StrictFieldValidationMixin, serializers.ModelSerializer):
    """Serializer for Language model"""
    
    class Meta:
        model = Language
        fields = ['id', 'code', 'name', 'display_order']
        read_only_fields = ['id']


class MessageSerializer(StrictFieldValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_content(self, obj):
        return json.loads(obj.content) if obj.content else obj.content


class ChatListSerializer(StrictFieldValidationMixin, serializers.ModelSerializer):
    """Lightweight serializer for chat list view - only returns metadata"""
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'title', 'created_at', 'updated_at', 'message_count', 'knowledge_base']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()


class ChatSerializer(StrictFieldValidationMixin, serializers.ModelSerializer):
    """Full chat serializer with all messages - for detail view"""
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'title', 'created_at', 'updated_at', 'messages', 'message_count', 'last_message', 'knowledge_base']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return MessageSerializer(last_message).data
        return None
