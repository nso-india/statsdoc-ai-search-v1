from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@database_sync_to_async
def get_user_from_jwt(token_key):
    """Get user from JWT token instead of Django Token"""
    if not token_key:
        logger.warning("No token provided in WebSocket connection")
        return AnonymousUser()
    
    try:
        logger.info(f"Attempting to validate JWT token: {token_key[:20]}...")
        # Validate JWT token
        token = AccessToken(token_key)
        user_id = token['user_id']
        logger.info(f"Token validated successfully, user_id: {user_id}")
        user = User.objects.get(id=user_id)
        logger.info(f"User found: {user.username}")
        return user
    except (InvalidToken, TokenError) as e:
        logger.error(f"JWT token validation failed: {e}")
        return AnonymousUser()
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
        return AnonymousUser()
    except Exception as e:
        logger.error(f"Unexpected error during JWT validation: {e}")
        return AnonymousUser()

class TokenAuthMiddleware:
    """
    Custom middleware for JWT token authentication in WebSocket connections.
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        """
        ASGI application that authenticates WebSocket connections using JWT tokens.
        """
        # Parse query string for token
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        token_key = query_params.get("token", [None])[0]
        
        logger.info(f"WebSocket connection attempt with query string: {query_string}")

        # Use JWT authentication instead of Django Token
        scope['user'] = await get_user_from_jwt(token_key)
        
        # Call the inner application
        return await self.inner(scope, receive, send)

# Helper function to stack the middleware
def TokenAuthMiddlewareStack(inner):
    """
    Helper function to create a middleware stack with JWT authentication.
    """
    from channels.auth import AuthMiddlewareStack
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))
