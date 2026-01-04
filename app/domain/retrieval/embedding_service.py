from abc import ABC, abstractmethod
from typing import List
import numpy as np
import asyncio
from app.core.config import settings
from app.observability.logging import logger

class EmbeddingService(ABC):
    @abstractmethod
    async def generate_embedding(self, text: str) -> np.ndarray:
        pass

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

class LocalEmbeddingService(EmbeddingService):
    def __init__(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Initializing Local Embedding Model", extra={"model": settings.EMBEDDING_MODEL_NAME})
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        except ImportError:
            logger.error("sentence-transformers not installed. Install it to use local embeddings.")
            raise

    async def generate_embedding(self, text: str) -> np.ndarray:
        return await asyncio.to_thread(self.model.encode, text, convert_to_numpy=True)

    async def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        return await asyncio.to_thread(self.model.encode, texts, convert_to_numpy=True)
    
    @property
    def dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()

class OpenAIEmbeddingService(EmbeddingService):
    def __init__(self):
        try:
            import openai
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is missing.")
            self.client = openai.OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
            self.model_name = settings.EMBEDDING_MODEL_NAME # "text-embedding-3-small"
            logger.info("Initialized OpenAI Embedding Service", extra={"model": self.model_name})
        except ImportError:
            logger.error("openai library not installed.")
            raise

    async def generate_embedding(self, text: str) -> np.ndarray:
        text = text.replace("\n", " ")
        # OpenAI Sync Client is used here, so offload it too to avoid blocking
        response = await asyncio.to_thread(
            self.client.embeddings.create, input=[text], model=self.model_name
        )
        return np.array(response.data[0].embedding, dtype=np.float32)

    async def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        # OpenAI has a batch limit, simplified here for demo
        safe_texts = [t.replace("\n", " ") for t in texts]
        response = await asyncio.to_thread(
            self.client.embeddings.create, input=safe_texts, model=self.model_name
        )
        return np.array([item.embedding for item in response.data], dtype=np.float32)

    @property
    def dimension(self) -> int:
        return 1536  # Standard for text-embedding-3-small

def get_embedding_service() -> EmbeddingService:
    provider = settings.EMBEDDING_PROVIDER.lower()
    if provider == "local":
        return LocalEmbeddingService()
    elif provider == "openai":
        return OpenAIEmbeddingService()
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")

# Singleton initialization could happen here if we want to preload
# embedding_service = get_embedding_service()
