# yourapp/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/pdf_update/$', consumers.JsonUpdateConsumer.as_asgi()),
]
