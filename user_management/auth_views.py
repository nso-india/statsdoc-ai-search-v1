from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import status, serializers
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from rest_framework.throttling import AnonRateThrottle

User = get_user_model()


class LoginRateThrottle(AnonRateThrottle):
    """Rate limiting for login attempts"""
    rate = '10/hour'  # Maximum 10 login attempts per hour per IP


class SecureTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer with account lockout"""

    def validate(self, attrs):
        email = attrs.get(self.username_field)
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
            
            # Check if account is locked
            if user.account_locked_until:
                if timezone.now() < user.account_locked_until:
                    lockout_remaining = (user.account_locked_until - timezone.now()).seconds // 60
                    raise serializers.ValidationError({
                        'detail': f'Account is locked. Please try again in {lockout_remaining} minutes.',
                        'locked_until': user.account_locked_until
                    })
                else:
                    # Unlock account if lockout period has passed
                    user.failed_login_attempts = 0
                    user.account_locked_until = None
                    user.last_failed_login = None
                    user.save()

            # Verify the password
            if user.check_password(password):
                # Reset failed attempts on successful login
                if user.failed_login_attempts > 0:
                    user.failed_login_attempts = 0
                    user.account_locked_until = None
                    user.last_failed_login = None
                    user.save()

                # Generate tokens
                data = super().validate(attrs)
                return data
            else:
                # Increment failed login attempts
                user.failed_login_attempts += 1
                user.last_failed_login = timezone.now()

                # Lock account if threshold exceeded
                max_attempts = getattr(settings, 'ACCOUNT_LOCKOUT_ATTEMPTS', 5)
                if user.failed_login_attempts >= max_attempts:
                    lockout_duration = getattr(settings, 'ACCOUNT_LOCKOUT_DURATION', timezone.timedelta(minutes=30))
                    user.account_locked_until = timezone.now() + lockout_duration
                    user.save()
                    raise serializers.ValidationError({
                        'detail': f'Account locked due to {max_attempts} failed login attempts. Please try again in 30 minutes.'
                    })
                
                user.save()
                remaining_attempts = max_attempts - user.failed_login_attempts
                raise serializers.ValidationError({
                    'detail': f'Invalid credentials. {remaining_attempts} attempts remaining before account lockout.'
                })

        except User.DoesNotExist:
            # Don't reveal that the user doesn't exist
            raise serializers.ValidationError({
                'detail': 'Invalid credentials.'
            })


class SecureTokenObtainPairView(TokenObtainPairView):
    """Secure login endpoint with rate limiting and account lockout"""
    serializer_class = SecureTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        """Handle login with additional security checks"""
        # Check for unexpected parameters
        allowed_fields = {'email', 'password'}
        provided_fields = set(request.data.keys())
        unexpected_fields = provided_fields - allowed_fields
        
        if unexpected_fields:
            return Response(
                {
                    'detail': f'Unexpected parameters: {", ".join(sorted(unexpected_fields))}',
                    'rejected_fields': sorted(list(unexpected_fields))
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            # Log failed login attempt
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed login attempt from IP: {request.META.get('REMOTE_ADDR')}")
            return Response(
                serializer.errors if hasattr(serializer, 'errors') else {'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )

        return Response(serializer.validated_data, status=status.HTTP_200_OK)
