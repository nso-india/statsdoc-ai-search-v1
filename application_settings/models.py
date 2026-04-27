from django.db import models


class Config(models.Model):
    namespace = models.CharField(max_length=50, unique=True)
    data = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Configuration"
        verbose_name_plural = "Configurations"

    def __str__(self):
        return f"{self.namespace} config"

    @classmethod
    def get_namespace(cls, namespace, default=None):
        """Get configuration data for a namespace, creating it if it doesn't exist."""
        obj, _ = cls.objects.get_or_create(namespace=namespace, defaults={"data": default or {}})
        return obj.data

    @classmethod
    def update_namespace(cls, namespace, new_data: dict):
        """Update configuration data for a namespace."""
        obj, _ = cls.objects.get_or_create(namespace=namespace)
        obj.data.update(new_data)
        obj.save()
        return obj.data

    @classmethod
    def set_namespace(cls, namespace, data: dict):
        """Set configuration data for a namespace (replace existing data)."""
        obj, _ = cls.objects.get_or_create(namespace=namespace)
        obj.data = data
        obj.save()
        return obj.data
