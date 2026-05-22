from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import AIServiceException
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise AIServiceException("OpenAI API key not configured")
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client
