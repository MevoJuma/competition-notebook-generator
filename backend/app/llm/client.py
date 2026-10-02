import json
import logging
from typing import Type, TypeVar
from pydantic import BaseModel
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger("app.llm.client")
T = TypeVar('T', bound=BaseModel)

class LLMClient:
    def __init__(self):
        # We handle missing API keys gracefully so tests don't crash
        api_key = getattr(settings, "OPENAI_API_KEY", "dummy_key")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = getattr(settings, "LLM_MODEL_NAME", "gpt-4-turbo-preview")

    async def generate_structured(self, prompt: str, response_model: Type[T]) -> T:
        """Generates a structured response using OpenAI JSON mode."""
        try:
            schema = response_model.model_json_schema()
            system_prompt = (
                f"You are a Kaggle Grandmaster AI. Return your response purely as a JSON object "
                f"matching this schema: {json.dumps(schema)}"
            )
            
            response = await self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            content = response.choices[0].message.content
            return response_model.model_validate_json(content)
        except Exception as e:
            logger.error(f"LLM Generation failed: {e}")
            raise

llm_client = LLMClient()
