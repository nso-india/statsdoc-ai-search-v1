from django.apps import AppConfig


class UserManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_management'
    verbose_name = 'User Management'
    
    def ready(self):
        """
        Import signals and perform any app initialization here
        """
        pass
