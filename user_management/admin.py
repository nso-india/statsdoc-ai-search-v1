from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

User = get_user_model()


class CustomUserAdmin(BaseUserAdmin):
    """Custom User Admin with enhanced functionality"""

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "user_type",
        "organization_name",
        "is_email_verified",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
    )
    list_filter = (
        "user_type",
        "is_email_verified",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
    )
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "organization_name",
    )
    ordering = ("-date_joined",)

    # Add custom fields to the admin form
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Additional Info",
            {
                "fields": (
                    "phone",
                    "user_type",
                    "organization_name",
                    "is_email_verified",
                )
            },
        ),
    )

    actions = ["activate_users", "deactivate_users", "verify_emails"]

    def activate_users(self, request, queryset):
        """Bulk activate users"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user(s) were successfully activated.")

    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        """Bulk deactivate users"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} user(s) were successfully deactivated.")

    deactivate_users.short_description = "Deactivate selected users"

    def verify_emails(self, request, queryset):
        """Bulk verify emails"""
        updated = queryset.update(is_email_verified=True, email_verification_token=None)
        self.message_user(
            request, f"{updated} user(s) email(s) were successfully verified."
        )

    verify_emails.short_description = "Verify selected user emails"


# Register our custom User admin
# Note: Since we're using a custom User model, Django automatically
# registers it, so we don't need to unregister the default User
admin.site.register(User, CustomUserAdmin)
