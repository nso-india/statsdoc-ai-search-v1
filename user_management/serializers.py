from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.contrib.auth import get_user_model
import pandas as pd
import io

User = get_user_model()


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


class UserSignupSerializer(StrictFieldValidationMixin, serializers.ModelSerializer):
    """Serializer for user signup"""

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "user_type",
            "organization_name",
            "password",
        ]

    def validate_email(self, value):
        """Check if email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_organization_name(self, value):
        """Validate organization name for company type users"""
        user_type = self.initial_data.get("user_type")
        if user_type == "company" and not value:
            raise serializers.ValidationError(
                "Organization name is required for company accounts."
            )
        return value

    def create(self, validated_data):
        """Create user with hashed password and email verification token"""
        
        password = validated_data.pop("password")

        # Set username to email
        validated_data["username"] = validated_data["email"]
        # User inactive until email verified
        validated_data["is_active"] = False
        validated_data["email_verification_token"] = get_random_string(50)
        validated_data["email_verification_sent_at"] = timezone.now()

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class EmailVerificationSerializer(StrictFieldValidationMixin, serializers.Serializer):
    """Serializer for email verification"""

    email = serializers.EmailField()
    token = serializers.CharField(max_length=50)

    def validate(self, attrs):
        """Validate email and token combination"""
        try:
            user = User.objects.get(
                email=attrs["email"],
                email_verification_token=attrs["token"],
                is_active=False,
            )

            # Check if token is expired (24 hours)
            from django.conf import settings

            expiry_hours = getattr(
                settings, "EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS", 24
            )
            if user.email_verification_sent_at:
                expiry_time = user.email_verification_sent_at + timezone.timedelta(
                    hours=expiry_hours
                )
                if timezone.now() > expiry_time:
                    raise serializers.ValidationError("Verification token has expired.")

            attrs["user"] = user
            return attrs
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid verification token or email.")


class ResendEmailVerificationSerializer(StrictFieldValidationMixin, serializers.Serializer):
    """Serializer for resending email verification"""

    email = serializers.EmailField()

    def validate_email(self, value):
        """Check if email exists and needs verification"""
        try:
            user = User.objects.get(email=value)
            if user.is_email_verified and user.is_active:
                raise serializers.ValidationError("Email is already verified.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "No account found with this email address."
            )


class UserCreateSerializer(StrictFieldValidationMixin, serializers.ModelSerializer):
    """Serializer for creating new users"""

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "user_type",
            "organization_name",
            "password",
            "is_active",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "is_active": {"default": True},
        }

    def validate_organization_name(self, value):
        """Validate organization name for company type users"""
        user_type = self.initial_data.get("user_type")
        if user_type == "company" and not value:
            raise serializers.ValidationError(
                "Organization name is required for company accounts."
            )
        return value

    def create(self, validated_data):
        """Create user with hashed password"""
        password = validated_data.pop("password")
        
        # Set username to email if not provided
        if not validated_data.get("username"):
            validated_data["username"] = validated_data["email"]
            
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class BulkUserCreateSerializer(StrictFieldValidationMixin, serializers.Serializer):
    """Serializer for bulk user creation from file upload"""

    file = serializers.FileField()

    def validate_file(self, value):
        """Validate uploaded file format"""
        if not value.name.endswith((".csv", ".xlsx", ".xls")):
            raise serializers.ValidationError("Only CSV and Excel files are supported.")
        return value

    def parse_file_data(self, file):
        """Parse uploaded file and return user data"""
        try:
            if file.name.endswith(".csv"):
                df = pd.read_csv(io.StringIO(file.read().decode("utf-8")))
            else:  # Excel files
                df = pd.read_excel(file)

            # Convert column names to lowercase for consistency
            df.columns = df.columns.str.lower().str.strip()

            # Required columns
            required_columns = ["username", "email", "password"]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                raise serializers.ValidationError(
                    f"Missing required columns: {', '.join(missing_columns)}"
                )

            # Optional columns with defaults
            if "first_name" not in df.columns:
                df["first_name"] = ""
            if "last_name" not in df.columns:
                df["last_name"] = ""
            if "is_active" not in df.columns:
                df["is_active"] = True

            # Convert DataFrame to list of dictionaries
            users_data = []
            for index, row in df.iterrows():
                user_data = {
                    "username": str(row["username"]).strip(),
                    "email": str(row["email"]).strip(),
                    "password": str(row["password"]).strip(),
                    "first_name": (
                        str(row["first_name"]).strip()
                        if pd.notna(row["first_name"])
                        else ""
                    ),
                    "last_name": (
                        str(row["last_name"]).strip()
                        if pd.notna(row["last_name"])
                        else ""
                    ),
                    "is_active": (
                        bool(row["is_active"]) if pd.notna(row["is_active"]) else True
                    ),
                }
                users_data.append(user_data)

            return users_data

        except Exception as e:
            raise serializers.ValidationError(f"Error parsing file: {str(e)}")

    def validate_users_data(self, users_data):
        """Validate each user data and return validation results"""
        valid_users = []
        errors = []

        for index, user_data in enumerate(users_data):
            try:
                # Check for duplicate usernames and emails in the file
                usernames_in_file = [u["username"] for u in users_data]
                emails_in_file = [u["email"] for u in users_data]

                if usernames_in_file.count(user_data["username"]) > 1:
                    errors.append(
                        {
                            "row": index
                            + 2,  # +2 because index starts at 0 and we skip header
                            "error": f"Duplicate username '{user_data['username']}' in file",
                        }
                    )
                    continue

                if emails_in_file.count(user_data["email"]) > 1:
                    errors.append(
                        {
                            "row": index + 2,
                            "error": f"Duplicate email '{user_data['email']}' in file",
                        }
                    )
                    continue

                # Check if username or email already exists in database
                if User.objects.filter(username=user_data["username"]).exists():
                    errors.append(
                        {
                            "row": index + 2,
                            "error": f"Username '{user_data['username']}' already exists",
                        }
                    )
                    continue

                if User.objects.filter(email=user_data["email"]).exists():
                    errors.append(
                        {
                            "row": index + 2,
                            "error": f"Email '{user_data['email']}' already exists",
                        }
                    )
                    continue

                # Validate using UserCreateSerializer
                serializer = UserCreateSerializer(data=user_data)
                if serializer.is_valid():
                    valid_users.append(user_data)
                else:
                    error_messages = []
                    for field, field_errors in serializer.errors.items():
                        error_messages.extend(
                            [f"{field}: {error}" for error in field_errors]
                        )
                    errors.append(
                        {"row": index + 2, "error": "; ".join(error_messages)}
                    )

            except Exception as e:
                errors.append(
                    {"row": index + 2, "error": f"Validation error: {str(e)}"}
                )

        return valid_users, errors


class UserSerializer(StrictFieldValidationMixin, serializers.ModelSerializer):
    """Serializer for user display and updates"""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "user_type",
            "organization_name",

            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "date_joined", "last_login", "is_superuser"]


class UserUpdateSerializer(StrictFieldValidationMixin, serializers.ModelSerializer):
    """Serializer for updating user information"""

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "phone", "user_type", "organization_name", "is_active"]


    def validate_username(self, value):
        """Check if username is unique for update"""
        user = self.instance
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        """Check if email is unique for update"""
        user = self.instance
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("This email is already taken.")
        return value

    def validate_organization_name(self, value):
        """Validate organization name for company type users"""
        user_type = self.initial_data.get("user_type", self.instance.user_type)
        if user_type == "company" and not value:
            raise serializers.ValidationError(
                "Organization name is required for company accounts."
            )
        return value


class PasswordChangeSerializer(StrictFieldValidationMixin, serializers.Serializer):
    """Serializer for changing user password"""

    new_password = serializers.CharField(
        validators=[validate_password], style={"input_type": "password"}
    )


class ForgotPasswordSerializer(StrictFieldValidationMixin, serializers.Serializer):
    """Serializer for requesting a password reset link

    For privacy we accept any well-formed email and let the view silently
    handle sending reset instructions if the account exists.
    """

    email = serializers.EmailField()

    def validate_email(self, value):
        # Do not disclose whether email exists; accept valid email format
        return value


class ResetPasswordSerializer(StrictFieldValidationMixin, serializers.Serializer):
    """Serializer for resetting the password using a token"""

    email = serializers.EmailField()
    token = serializers.CharField(max_length=100)
    new_password = serializers.CharField(validators=[validate_password], style={"input_type": "password"})

    def validate(self, attrs):
        # Validate user and token
        try:
            user = User.objects.get(email=attrs["email"], password_reset_token=attrs["token"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": "Invalid token or email."})

        # Check token expiry (1 hour)
        if user.password_reset_sent_at:
            expiry_time = user.password_reset_sent_at + timezone.timedelta(hours=1)
            if timezone.now() > expiry_time:
                raise serializers.ValidationError({"detail": "Password reset token has expired."})

        attrs["user"] = user
        return attrs
