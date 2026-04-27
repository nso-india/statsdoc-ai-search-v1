"""
Utility functions for accessing and managing configuration settings.
"""
from .models import Config


class ConfigManager:
    """Utility class for managing configuration settings."""

    @staticmethod
    def get_chat_settings():
        """Get chat configuration settings with defaults."""
        defaults = {
            'file_size_limit_mb': 20,
            'questions_per_chat': 10,
            'chats_per_day': 50
        }
        return Config.get_namespace('chat', defaults)

    @staticmethod
    def get_file_size_limit():
        """Get file size limit in MB."""
        settings = ConfigManager.get_chat_settings()
        return settings.get('file_size_limit_mb', 20)

    @staticmethod
    def get_questions_per_chat():
        """Get maximum questions per chat."""
        settings = ConfigManager.get_chat_settings()
        return settings.get('questions_per_chat', 10)

    @staticmethod
    def get_chats_per_day():
        """Get maximum chats per day."""
        settings = ConfigManager.get_chat_settings()
        return settings.get('chats_per_day', 50)

    @staticmethod
    def update_chat_settings(**kwargs):
        """Update chat configuration settings."""
        return Config.update_namespace('chat', kwargs)

    @staticmethod
    def reset_chat_settings():
        """Reset chat settings to defaults."""
        defaults = {
            'file_size_limit_mb': 20,
            'questions_per_chat': 10,
            'chats_per_day': 50
        }
        return Config.set_namespace('chat', defaults)


def get_setting(namespace, key, default=None):
    """Get a specific setting value from a namespace."""
    data = Config.get_namespace(namespace, {})
    return data.get(key, default)


def update_setting(namespace, key, value):
    """Update a specific setting value in a namespace."""
    return Config.update_namespace(namespace, {key: value})


def validate_file_size(file_size_mb):
    """Validate file size against configured limit."""
    limit = ConfigManager.get_file_size_limit()
    return file_size_mb <= limit


def validate_questions_count(count, chat_id=None):
    """Validate number of questions in a chat."""
    limit = ConfigManager.get_questions_per_chat()
    return count <= limit


def validate_daily_chats(count, user_id=None):
    """Validate daily chat count for a user."""
    limit = ConfigManager.get_chats_per_day()
    return count <= limit


# Backward compatibility aliases
get_chat_file_size_limit = ConfigManager.get_file_size_limit
get_chat_questions_limit = ConfigManager.get_questions_per_chat
get_chat_daily_limit = ConfigManager.get_chats_per_day