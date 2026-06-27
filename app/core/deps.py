from openai import AsyncOpenAI
from typing import AsyncGenerator
from app.core.config import settings

async_opnerouter_client = AsyncOpenAI(
    base_url=settings.OPENROUTER_BASE_URL,
    api_key=settings.OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": settings.APP_REFERER,
        "X-OpenRouter-Title": settings.APP_TITLE,
    }
)

async def get_llm_client() -> AsyncGenerator[AsyncOpenAI, None]:
    yield async_opnerouter_client