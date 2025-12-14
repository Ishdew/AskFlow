from openai import AsyncOpenAI, AsyncAzureOpenAI
from app.core.config import settings
from typing import List

class VectorService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        
        if self.provider == "azure":
            self.client = AsyncAzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            # In Azure, the "model" parameter in client calls is usually the deployment name
            self.embedding_model_name = settings.AZURE_EMBEDDING_DEPLOYMENT_NAME
        else:
            # Default to Standard OpenAI
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.embedding_model_name = "text-embedding-3-small"

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a 1536-dimensional embedding using the configured provider.
        """
        try:
            cleaned_text = text.replace("\n", " ")
            
            response = await self.client.embeddings.create(
                input=[cleaned_text],
                model=self.embedding_model_name
            )
            
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding with {self.provider}: {e}")
            raise e

vector_service = VectorService()
