"""
Vertex AI client wrapper for Gemini models using the modern google-genai SDK.
Handles authentication, model initialization, and grounding configuration.
"""
import os
import logging
import asyncio
from typing import Optional, Dict, Any, List, AsyncGenerator
from google import genai
from google.genai import types

from config import settings

import random
from functools import wraps
import inspect

logger = logging.getLogger(__name__)


def with_retry(max_retries: int = 3, base_delay: float = 2.0, max_delay: float = 30.0):
    """Decorator for exponential backoff retry logic. Supports both async functions and async generators."""
    def decorator(func):
        if inspect.isasyncgenfunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                retries = 0
                while True:
                    try:
                        async for item in func(*args, **kwargs):
                            yield item
                        return
                    except Exception as e:
                        is_rate_limit = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
                        if not is_rate_limit or retries >= max_retries:
                            logger.error(f"Streaming execution failed after {retries} retries: {e}")
                            raise e
                        
                        retries += 1
                        delay = min(base_delay * (2 ** (retries - 1)) + random.uniform(0, 1), max_delay)
                        logger.warning(f"Rate limit hit in stream (429). Retrying in {delay:.2f}s (Attempt {retries}/{max_retries}). Error: {e}")
                        await asyncio.sleep(delay)
            return wrapper
        else:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                retries = 0
                while True:
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        is_rate_limit = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
                        if not is_rate_limit or retries >= max_retries:
                            logger.error(f"Execution failed after {retries} retries: {e}")
                            raise e
                        
                        retries += 1
                        delay = min(base_delay * (2 ** (retries - 1)) + random.uniform(0, 1), max_delay)
                        logger.warning(f"Rate limit hit (429). Retrying in {delay:.2f}s (Attempt {retries}/{max_retries}). Error: {e}")
                        await asyncio.sleep(delay)
            return wrapper
    return decorator


class VertexAIClient:
    """Wrapper for Vertex AI Gemini models with grounding support using google-genai SDK."""
    
    def __init__(self):
        self.project_id = settings.gcp_project_id
        self.location = settings.gcp_location
        self.model_name = settings.gemini_model
        self.initialized = False
        self.client: Optional[genai.Client] = None
    
    def initialize(self):
        """Initialize the Gen AI Client."""
        if self.initialized:
            return
        
        try:
            # Set credentials path for the SDK to pick up if needed
            if settings.credentials_path.exists():
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(settings.credentials_path)
            
            # Initialize Gen AI Client in Vertex AI mode
            self.client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location
            )
            
            self.initialized = True
            logger.info(f"Gen AI Client initialized: project={self.project_id}, location={self.location}, model={self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gen AI Client: {e}")
            raise
    
    @with_retry(max_retries=5, base_delay=5.0)
    async def generate_with_grounding(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        use_grounding: bool = True,
        extra_config: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate content with optional Google Search grounding.
        """
        if not self.initialized:
            self.initialize()
        
        # Prepare configuration
        tools = []
        if use_grounding:
            tools.append(types.Tool(google_search=types.GoogleSearch()))
            
        config_params = {
            "temperature": temperature or settings.gemini_temperature,
            "max_output_tokens": max_output_tokens or settings.gemini_max_output_tokens,
            "tools": tools if tools else None,
            "thinking_config": types.ThinkingConfig(
                include_thoughts=settings.include_thoughts,
            ) if "gemini-3" in self.model_name.lower() or "thinking" in self.model_name.lower() else None
        }
        
        if extra_config:
            config_params.update(extra_config)
            
        config = types.GenerateContentConfig(**config_params)
        
        target_model = model_name or self.model_name
        logger.info(f"Generating content with model: {target_model} (grounding={use_grounding})")
        
        try:
            # Generate content using native async client
            response = await self.client.aio.models.generate_content(
                model=target_model,
                contents=prompt,
                config=config
            )
            
            # Extract response data
            result = {
                "text": "",
                "thought": "",
                "grounding_metadata": None,
                "citations": []
            }
            
            if response.candidates:
                candidate = response.candidates[0]
                # Extract text and thoughts from parts
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if part.thought:
                            result["thought"] += part.text
                        elif part.text:
                            result["text"] += part.text
                elif getattr(candidate, 'text', None):
                    result["text"] = candidate.text
                
                # Extract grounding metadata
                if candidate.grounding_metadata:
                    gm = candidate.grounding_metadata
                    result["grounding_metadata"] = {
                        "web_search_queries": getattr(gm, 'web_search_queries', []),
                        "grounding_attributions": []
                    }
                    
                    # Map grounding chunks to citations
                    if gm.grounding_chunks:
                        for chunk in gm.grounding_chunks:
                            if chunk.web:
                                citation = {
                                    "title": chunk.web.title,
                                    "uri": chunk.web.uri
                                }
                                result["citations"].append(citation)
                                result["grounding_metadata"]["grounding_attributions"].append(citation)
            
            logger.info(f"Successfully generated response: text_len={len(result['text'])}, thought_len={len(result['thought'])}, citations={len(result['citations'])}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise
    
    @with_retry(max_retries=5, base_delay=5.0)
    async def generate_streaming(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        use_grounding: bool = True,
        extra_config: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate content with streaming.
        """
        if not self.initialized:
            self.initialize()
            
        # Prepare configuration
        tools = []
        if use_grounding:
            tools.append(types.Tool(google_search=types.GoogleSearch()))
            
        config_params = {
            "temperature": temperature or settings.gemini_temperature,
            "max_output_tokens": max_output_tokens or settings.gemini_max_output_tokens,
            "tools": tools if tools else None,
            "thinking_config": types.ThinkingConfig(
                include_thoughts=settings.include_thoughts,
            ) if "gemini-3" in self.model_name.lower() or "thinking" in self.model_name.lower() else None
        }
        
        if extra_config:
            config_params.update(extra_config)
            
        config = types.GenerateContentConfig(**config_params)
        
        logger.info(f"Starting streaming generation: model={self.model_name}, grounding={use_grounding}")
        
        try:
            # Use the native async streaming interface
            stream = await self.client.aio.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            chunk_count = 0
            # For streaming responses, we iterate over segments using async iterator
            async for block in stream:
                chunk_count += 1
                logger.debug(f"Raw stream block {chunk_count}: {getattr(block, '__dict__', block)}")
                if not block.candidates:
                    logger.debug(f"Stream block {chunk_count} has no candidates")
                    continue
                    
                candidate = block.candidates[0]
                
                # Process parts in current chunk
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if part.thought:
                            logger.debug(f"Stream block {chunk_count}: yielding thought ({len(part.text)} chars)")
                            yield {"type": "thought", "text": part.text}
                        elif part.text:
                            logger.debug(f"Stream block {chunk_count}: yielding text ({len(part.text)} chars)")
                            yield {"type": "text", "text": part.text}
                
                # Extract grounding metadata if present
                if candidate.grounding_metadata:
                    gm = candidate.grounding_metadata
                    citations = []
                    if gm.grounding_chunks:
                        for chunk_data in gm.grounding_chunks:
                            if chunk_data.web:
                                citations.append({
                                    "title": chunk_data.web.title,
                                    "uri": chunk_data.web.uri
                                })
                    if citations:
                        logger.debug(f"Stream block {chunk_count}: yielding {len(citations)} citations")
                        yield {"type": "citations", "data": citations}
            
            logger.info(f"Streaming generation completed successfully after {chunk_count} blocks")
                        
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            raise


# Global Vertex AI client instance
vertex_client = VertexAIClient()
