from openai import AsyncOpenAI, AsyncAzureOpenAI
from app.core.config import settings
from typing import List

class VectorService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        
        if self.provider == "azure":
            # 1. Embedding Client
            self.embedding_client = AsyncAzureOpenAI(
                api_key=settings.AZURE_OPENAI_EMBEDDING_API_KEY,
                api_version=settings.AZURE_OPENAI_EMBEDDING_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_EMBEDDING_ENDPOINT
            )
            self.embedding_model_name = settings.AZURE_EMBEDDING_DEPLOYMENT_NAME

            # 2. Chat Client
            self.chat_client = AsyncAzureOpenAI(
                api_key=settings.AZURE_OPENAI_CHAT_API_KEY,
                api_version=settings.AZURE_OPENAI_CHAT_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_CHAT_ENDPOINT
            )
            self.chat_model_name = settings.AZURE_CHAT_DEPLOYMENT_NAME
        else:
            # Default to Standard OpenAI (One client for both)
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.embedding_client = self.client
            self.chat_client = self.client
            
            self.embedding_model_name = "text-embedding-3-small"
            self.chat_model_name = settings.OPENAI_MODEL_NAME

    async def generate_answer(self, messages: List[dict]) -> str:
        """
        Generates a chat completion.
        """
        try:
            response = await self.chat_client.chat.completions.create(
                model=self.chat_model_name,
                messages=messages,
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating answer with {self.provider}: {e}")
            raise e

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a 1536-dimensional embedding using the configured provider.
        """
        try:
            cleaned_text = text.replace("\n", " ")
            
            response = await self.embedding_client.embeddings.create(
                input=[cleaned_text],
                model=self.embedding_model_name
            )
            
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding with {self.provider}: {e}")
            raise e

vector_service = VectorService()
