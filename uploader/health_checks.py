# myapp/health_checks.py
from health_check.backends import BaseHealthCheckBackend
from health_check.exceptions import HealthCheckException
import requests

from django.conf import settings


class DoclingHealthCheck(BaseHealthCheckBackend):
    def check_status(self):
        try:
            response = requests.get(f"{settings.DOCLING_URL}/health", timeout=3)
            if response.status_code != 200:
                raise HealthCheckException(f"Docling returned {response.status_code}")
        except Exception as e:
            raise HealthCheckException(f"Docling error: {str(e)}")


class QdrantHealthCheck(BaseHealthCheckBackend):
    def check_status(self):
        try:
            response = requests.get(settings.QDRANT_URL, timeout=3)
            if response.status_code != 200:
                raise HealthCheckException(f"Qdrant returned {response.status_code}")
        except Exception as e:
            raise HealthCheckException(f"Qdrant error: {str(e)}")