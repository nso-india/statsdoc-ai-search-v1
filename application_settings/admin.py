from django.contrib import admin
from .models import Config


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ('namespace', 'modified_data_summary')
    list_filter = ('namespace',)
    search_fields = ('namespace',)
    readonly_fields = ('namespace',)  # Prevent editing namespace from admin

    @admin.display(description="Data Summary")
    def modified_data_summary(self, obj):
        """Display a summary of the data field."""
        if obj.data:
            keys = list(obj.data.keys())
            if len(keys) <= 3:
                return str(keys)
            return f"{keys[:3]} ... ({len(keys)} keys)"
        return "Empty"
