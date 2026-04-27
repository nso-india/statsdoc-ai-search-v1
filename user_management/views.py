from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.paginator import Paginator
from django.utils.crypto import get_random_string
from django.utils import timezone
from .serializers import (
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer,
    BulkUserCreateSerializer,
    UserSignupSerializer,
    EmailVerificationSerializer,
    ResendEmailVerificationSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)
from .permissions import IsStaffUser
from .utils import send_verification_email, send_welcome_email

User = get_user_model()


class UserSignupView(APIView):
    """User signup with email verification"""

    permission_classes = []  # Allow unauthenticated access

    def post(self, request):
        """Create a new user account"""
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.save()

                # Send verification email
                if send_verification_email(user, request):
                    return Response(
                        {
                            "message": (
                                "Account created successfully. Please check your "
                                "email to verify your account."
                            ),
                            "email": user.email,
                        },
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        {
                            "message": (
                                "Account created but failed to send verification "
                                "email. Please contact support."
                            ),
                            "email": user.email,
                        },
                        status=status.HTTP_201_CREATED,
                    )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    """Verify user email address"""

    permission_classes = []  # Allow unauthenticated access

    def post(self, request):
        """Verify email with token"""
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]

            # Activate user and mark email as verified
            user.is_active = True
            user.is_email_verified = True
            user.email_verification_token = None
            user.email_verification_sent_at = None
            user.save()

            # Send welcome email
            send_welcome_email(user)

            return Response(
                {
                    "message": (
                        "Email verified successfully. You can now log in to "
                        "your account."
                    ),
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendEmailVerificationView(APIView):
    """Resend email verification"""

    permission_classes = []  # Allow unauthenticated access

    def post(self, request):
        """Resend verification email"""
        serializer = ResendEmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            user = User.objects.get(email=email)

            # Generate new verification token
            user.email_verification_token = get_random_string(50)
            user.email_verification_sent_at = timezone.now()
            user.save()

            # Send verification email
            if send_verification_email(user, request):
                return Response(
                    {
                        "message": "Verification email sent successfully.",
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "error": (
                            "Failed to send verification email. Please try "
                            "again later."
                        ),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListCreateView(APIView):
    """
    GET: List all users (staff only)
    POST: Create a new user (staff only)
    """
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        """List all users with pagination and filtering"""
        # Get query parameters for filtering and pagination
        search = request.GET.get('search', '')
        is_active_filter = request.GET.get('is_active', None)
        page = request.GET.get('page', 1)
        page_size = min(int(request.GET.get('page_size', 20)), 100)

        # Build queryset with filters
        users = User.objects.all().order_by('-date_joined')

        if search:
            users = users.filter(
                username__icontains=search
            ) | users.filter(
                email__icontains=search
            ) | users.filter(
                first_name__icontains=search
            ) | users.filter(
                last_name__icontains=search
            )

        if is_active_filter is not None:
            is_active = is_active_filter.lower() == 'true'
            users = users.filter(is_active=is_active)

        # Paginate results
        paginator = Paginator(users, page_size)
        try:
            page_obj = paginator.page(page)
        except Exception:
            page_obj = paginator.page(1)

        serializer = UserSerializer(page_obj.object_list, many=True)

        return Response({
            'users': serializer.data,
            'pagination': {
                'page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })

    def post(self, request):
        """Create a new user"""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.save()
                return Response(
                    UserSerializer(user).data,
                    status=status.HTTP_201_CREATED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    """
    GET: Retrieve user details (staff only)
    PUT: Update user (staff only)
    DELETE: Delete user (staff only)
    """
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get_object(self, user_id):
        """Get user object or return 404"""
        return get_object_or_404(User, id=user_id)

    def check_user_permissions(self, request, user):
        """Check if the current user can modify the target user"""
        # Prevent staff from deleting themselves
        if request.method == 'DELETE' and user == request.user:
            return Response(
                {'error': 'Cannot delete your own account.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prevent staff from modifying superuser accounts
        if user.is_superuser and not request.user.is_superuser:
            return Response(
                {'error': 'Cannot modify superuser accounts.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return None

    def get(self, request, user_id):
        """Retrieve user details"""
        user = self.get_object(user_id)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request, user_id):
        """Update user information"""
        user = self.get_object(user_id)
        permission_error = self.check_user_permissions(request, user)
        if permission_error:
            return permission_error

        serializer = UserUpdateSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id):
        """Delete user"""
        user = self.get_object(user_id)
        permission_error = self.check_user_permissions(request, user)
        if permission_error:
            return permission_error

        username = user.username
        user.delete()
        return Response(
            {'message': f'User "{username}" has been deleted successfully.'},
            status=status.HTTP_200_OK
        )


class UserActivateView(APIView):
    """Activate a user account (staff only)"""
    permission_classes = [IsAuthenticated, IsStaffUser]

    def post(self, request, user_id):
        """Activate user account"""
        user = get_object_or_404(User, id=user_id)

        if user.is_active:
            return Response(
                {'message': f'User "{user.username}" is already active.'},
                status=status.HTTP_200_OK
            )

        user.is_active = True
        user.save()

        return Response(
            {
                'message': f'User "{user.username}" has been activated.',
                'user': UserSerializer(user).data
            },
            status=status.HTTP_200_OK
        )


class UserDeactivateView(APIView):
    """Deactivate a user account (staff only)"""
    permission_classes = [IsAuthenticated, IsStaffUser]

    def post(self, request, user_id):
        """Deactivate user account"""
        user = get_object_or_404(User, id=user_id)

        # Prevent staff from deactivating themselves
        if user == request.user:
            return Response(
                {'error': 'Cannot deactivate your own account.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prevent staff from deactivating superuser accounts
        if user.is_superuser and not request.user.is_superuser:
            return Response(
                {'error': 'Cannot deactivate superuser accounts.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not user.is_active:
            return Response(
                {'message': f'User "{user.username}" is already inactive.'},
                status=status.HTTP_200_OK
            )

        user.is_active = False
        user.save()

        return Response(
            {
                'message': f'User "{user.username}" has been deactivated.',
                'user': UserSerializer(user).data
            },
            status=status.HTTP_200_OK
        )


class UserChangePasswordView(APIView):
    """Change password for a user (staff only)"""
    permission_classes = [IsAuthenticated, IsStaffUser]

    def post(self, request, user_id):
        """Change user password"""
        user = get_object_or_404(User, id=user_id)

        # Prevent staff from changing superuser passwords
        if user.is_superuser and not request.user.is_superuser:
            return Response(
                {'error': 'Cannot change superuser passwords.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                {
                    'message': (f'Password changed successfully for '
                                f'"{user.username}".')
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    """Request a password reset link. Returns 200 for privacy regardless of email existence."""
    permission_classes = []  # Allow unauthenticated access

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get('email')

        try:
            user = User.objects.get(email=email)

            # Generate token and timestamp
            user.password_reset_token = get_random_string(64)
            user.password_reset_sent_at = timezone.now()
            user.save()

            # Build reset URL
            from django.conf import settings as _settings
            host = request.get_host() if request else getattr(_settings, 'DOMAIN', 'localhost:8000')
            protocol = 'https' if not _settings.DEBUG else 'http'
            reset_url = f"{protocol}://{host}/reset-password?email={user.email}&token={user.password_reset_token}"

            # Send email via MOSPI API (log failures but don't reveal to caller)
            try:
                from .utils import send_password_reset_email_mospi
                send_password_reset_email_mospi(user, reset_url)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to send password reset email to {user.email}: {e}")
        except User.DoesNotExist:
            # Silent success for non-existent email
            pass

        return Response({"message": "If an account with this email exists, you will receive reset instructions."}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """Reset a user's password using a token"""
    permission_classes = []  # Allow unauthenticated access

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        new_password = serializer.validated_data['new_password']

        user.set_password(new_password)
        user.password_reset_token = None
        user.password_reset_sent_at = None
        user.save()

        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)


class UserStatsView(APIView):
    """Get user statistics (staff only)"""
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        """Get user statistics"""
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = User.objects.filter(is_active=False).count()
        staff_users = User.objects.filter(is_staff=True).count()
        superuser_count = User.objects.filter(is_superuser=True).count()

        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'staff_users': staff_users,
            'superuser_count': superuser_count,
        })


class UserRoleCheckView(APIView):
    """Check current user's role and permissions"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user's role information"""
        user = request.user
        
        # Determine user role - only 3 basic constants
        if user.is_superuser:
            role = 'SUPERADMIN'
            access_level = 3
        elif user.is_staff:
            role = 'STAFF'
            access_level = 2
        else:
            role = 'USER'
            access_level = 1
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'role': role,
            'access_level': access_level,
            'is_active': user.is_active
        })


class BulkUserCreateView(APIView):
    """Bulk create users from CSV/Excel file upload (staff only)"""
    permission_classes = [IsAuthenticated, IsStaffUser]

    def post(self, request):
        """Create multiple users from uploaded file"""
        serializer = BulkUserCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )

        file = serializer.validated_data['file']

        try:
            # Parse file data
            users_data = serializer.parse_file_data(file)

            if not users_data:
                return Response(
                    {'error': 'No user data found in file'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate users data
            valid_users, errors = serializer.validate_users_data(users_data)

            # Create users that passed validation
            created_users = []
            creation_errors = []

            with transaction.atomic():
                for user_data in valid_users:
                    try:
                        user_serializer = UserCreateSerializer(data=user_data)
                        if user_serializer.is_valid():
                            user = user_serializer.save()
                            created_users.append(UserSerializer(user).data)
                        else:
                            creation_errors.append({
                                'username': user_data.get('username', 'Unknown'),
                                'error': user_serializer.errors
                            })
                    except Exception as e:
                        creation_errors.append({
                            'username': user_data.get('username', 'Unknown'),
                            'error': str(e)
                        })

            response_data = {
                'summary': {
                    'total_in_file': len(users_data),
                    'validation_passed': len(valid_users),
                    'successfully_created': len(created_users),
                    'validation_errors': len(errors),
                    'creation_errors': len(creation_errors)
                },
                'created_users': created_users,
                'validation_errors': errors,
                'creation_errors': creation_errors
            }

            if created_users:
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {'error': f'Failed to process file: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkUserTemplateView(APIView):
    """Download template for bulk user creation (staff only)"""
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        """Return CSV template for bulk user creation"""
        from django.http import HttpResponse
        import csv

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="user_template.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'username', 'email', 'password', 'first_name', 
            'last_name', 'is_active'
        ])
        writer.writerow([
            'john_doe', 'john@example.com', 'password123', 'John', 
            'Doe', 'TRUE'
        ])
        writer.writerow([
            'jane_smith', 'jane@example.com', 'password456', 'Jane', 
            'Smith', 'TRUE'
        ])

        return response
