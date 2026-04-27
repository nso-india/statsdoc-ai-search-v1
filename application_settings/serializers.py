from rest_framework import serializers
from .models import Config


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


class ConfigSerializer(StrictFieldValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Config
        fields = ['namespace', 'data']
        read_only_fields = ['namespace']  # Namespace should not be changed via API

    def validate_data(self, value):
        """Validate that data is a dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Data must be a valid JSON object.")
        return value


class NamespaceConfigSerializer(StrictFieldValidationMixin, serializers.Serializer):
    """Serializer for updating specific namespace configuration."""
    config_data = serializers.JSONField()

    def __init__(self, *args, **kwargs):
        self.namespace = kwargs.pop('namespace', None)
        super().__init__(*args, **kwargs)

    def validate_config_data(self, value):
        """Validate that data is a dictionary and perform namespace-specific validation."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Data must be a valid JSON object.")
        
        # Perform namespace-specific validation
        if hasattr(self, 'context') and 'namespace' in self.context:
            namespace = self.context['namespace']
            self._validate_namespace_data(namespace, value)
        
        return value

    def _validate_namespace_data(self, namespace, data):
        """Perform validation specific to namespace."""
        if namespace == 'chat':
            self._validate_chat_data(data)

    def _validate_chat_data(self, data):
        """Validate chat namespace specific data."""
        errors = {}
        
        if 'file_size_limit_mb' in data:
            value = data['file_size_limit_mb']
            if not isinstance(value, int) or value < 1 or value > 100:
                errors['file_size_limit_mb'] = "File size limit must be between 1 and 100 MB."
        
        if 'questions_per_chat' in data:
            value = data['questions_per_chat']
            if not isinstance(value, int) or value < 1 or value > 100:
                errors['questions_per_chat'] = "Questions per chat must be between 1 and 100."
        
        if 'chats_per_day' in data:
            value = data['chats_per_day']
            if not isinstance(value, int) or value < 1 or value > 1000:
                errors['chats_per_day'] = "Chats per day must be between 1 and 1000."
        
        if errors:
            raise serializers.ValidationError(errors)
