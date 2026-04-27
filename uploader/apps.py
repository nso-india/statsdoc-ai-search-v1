# filepath: /home/edubild/izhaar/mospi_backend/uploader/apps.py
from django.apps import AppConfig
from health_check.plugins import plugin_dir
from .health_checks import DoclingHealthCheck, QdrantHealthCheck


class UploaderConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "uploader"

    def ready(self):
        plugin_dir.register(DoclingHealthCheck)
        plugin_dir.register(QdrantHealthCheck)
