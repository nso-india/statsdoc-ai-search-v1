"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django BEFORE importing anything else
django.setup()

# Now safe to import after Django is initialized
from channels.routing import ProtocolTypeRouter, URLRouter
from uploader.middleware import TokenAuthMiddlewareStack
import uploader.routing
import chat.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddlewareStack(URLRouter(
        uploader.routing.websocket_urlpatterns +
        chat.routing.websocket_urlpatterns
    )),
})
