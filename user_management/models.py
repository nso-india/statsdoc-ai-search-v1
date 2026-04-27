from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Extended User model with additional signup fields"""

    USER_TYPE_CHOICES = [
        ("individual", "Individual"),
        ("company", "Company"),
    ]

    # Override email field to make it required
    email = models.EmailField(unique=True)

    # Additional fields for signup
    phone = models.CharField(max_length=20, blank=True, null=True)
    user_type = models.CharField(
        max_length=10, choices=USER_TYPE_CHOICES, default="individual"
    )
    organization_name = models.CharField(max_length=255, blank=True, null=True)

    # Email verification fields
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)

    # Password reset fields
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_sent_at = models.DateTimeField(blank=True, null=True)

    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(blank=True, null=True)
    last_failed_login = models.DateTimeField(blank=True, null=True)

    # Override username requirement
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "auth_user"  # Keep using the same table

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Auto-generate username from email if not provided
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
