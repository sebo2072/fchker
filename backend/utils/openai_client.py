"""
OpenAI client wrapper for fast refinement tasks.
Uses the modern OpenAI Responses API with streaming support.
"""
import logging
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from openai import AsyncOpenAI
from config import settings

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Wrapper for OpenAI API using the modern Responses interface with streaming support."""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model_name = settings.openai_refiner_model
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            if not self.api_key:
                logger.error("OpenAI API key not configured")
                raise ValueError("OPENAI_API_KEY is missing from configuration")
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def generate_refined_update(self, prompt: str) -> str:
        """
        Generate a refined update using the OpenAI Responses API (non-streaming).
        """
        try:
            response = await self.client.responses.create(
                model=self.model_name,
                input=prompt
            )
            
            # Extract content from nested Responses API structure
            if hasattr(response, 'output') and isinstance(response.output, list):
                for item in response.output:
                    if getattr(item, 'type', None) == 'message' and hasattr(item, 'content'):
                        if isinstance(item.content, list):
                            for part in item.content:
                                if getattr(part, 'type', None) == 'output_text':
                                    return part.text
                        elif hasattr(item.content, 'text'):
                            return item.content.text

            return str(response)

        except Exception as e:
            logger.error(f"OpenAI refinement failed: {e}")
            raise

    async def stream_refined_update(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Stream a refined update using the OpenAI Responses API.
        Yields text deltas as they arrive.
        """
        try:
            stream = await self.client.responses.create(
                model=self.model_name,
                input=prompt,
                stream=True
            )
            async for chunk in stream:
                # The Responses API uses specific event types for streaming
                chunk_type = getattr(chunk, 'type', None)
                
                # Path 1: Targeted delta extraction for newer Responses API events
                if chunk_type == 'response.output_text.delta':
                    if hasattr(chunk, 'delta') and chunk.delta:
                        yield chunk.delta
                
                # Path 2: Handle reasoning items if needed in future (currently skipping reasoning)
                # elif chunk_type == 'response.output_reasoning.delta':
                #     pass

                # Path 3: Generic fallback for other SDK versions/structures
                if hasattr(chunk, 'output') and isinstance(chunk.output, list):
                    for item in chunk.output:
                        if hasattr(item, 'delta'):
                            delta = item.delta
                            if hasattr(delta, 'text'):
                                yield delta.text
                            elif isinstance(delta, str):
                                yield delta

                # Path 4: Standard ChatCompletion delta fallback
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        yield delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming refinement failed: {e}")

# Global instance
openai_client = OpenAIClient()
