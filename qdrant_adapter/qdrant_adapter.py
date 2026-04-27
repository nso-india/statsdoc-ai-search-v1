from qdrant_client import QdrantClient
from django.conf import settings


def init_connection() -> QdrantClient:
    """
    Initialize the Qdrant client connection using settings from Django.
    """
    if not settings.QDRANT_URL or not settings.QDRANT_API_KEY:
        raise ValueError("Qdrant URL and API Key must be set in Django settings.")
    qdrant_client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )
    qdrant_client.set_model(settings.QDRANT_EMBEDDING_MODEL, cuda=settings.QDRANT_GPU_ENABLED, cache_dir=settings.QDRANT_CACHE_DIR)
    return qdrant_client
