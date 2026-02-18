"""
Fact extraction agent using Gemini to identify verifiable claims.
Implements intelligent claim detection with context awareness.
"""
import logging
from typing import List, Dict, Optional, Callable, Any
import asyncio
import json
import re

from utils.vertex_client import vertex_client
from core.thinking_refiner import ThinkingRefiner

logger = logging.getLogger(__name__)


class ExtractionAgent:
    """Agent for extracting factual claims from text."""
    
    def __init__(self):
        self.vertex_client = vertex_client
    
    async def extract_claims(self, text: str, session_id: str = "default", progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """
        Extract verifiable factual claims from text.
        """
        logger.info(f"Extracting claims from text ({len(text)} chars)")
        
        # Initialize Thinking Refiner for professional updates
        refiner = None
        if progress_callback:
            refiner = ThinkingRefiner(
                session_id=session_id,
                claim_id="extraction_thinking", # Virtual ID for the extraction phase
                progress_callback=progress_callback
            )
        
        prompt = f"""You are a professional fact-checker. Analyze the following article and extract EVERY individual verifiable factual claim.

Typical articles contain 5-15 distinct claims. Extract each one separately.

Article text:
\"\"\"
{text}
\"\"\"

Return your response AS ONLY A VALID JSON ARRAY. 
Each object in the array MUST have this structure:
{{
    "claim": "The specific factual statement",
    "verbatim": "The EXACT line or sentence from the article (must be verbatim)",
    "context": "Surrounding context from the original text",
    "type": "statistical|historical|scientific|attribution|general",
    "is_quote": true|false,
    "confidence": 0.0-1.0
}}

IMPORTANT: 
- The "verbatim" field MUST BE AN EXACT SUBSTRTING from the article.
- Return ONLY the JSON array. Don't add text before or after.
"""

        try:
            full_text = ""
            all_thoughts = ""
            max_tokens = 8192
            
            chunk_count = 0
            async for chunk in self.vertex_client.generate_streaming(
                prompt=prompt,
                temperature=0.1,
                max_output_tokens=max_tokens,
                use_grounding=False,
                extra_config={"response_mime_type": "application/json"}
            ):
                chunk_count += 1
                if chunk['type'] == 'thought':
                    logger.debug(f"Extraction chunk {chunk_count}: Received thought ({len(chunk['text'])} chars)")
                    all_thoughts += chunk['text']
                    # Route thoughts through refiner if available
                    if refiner:
                        await refiner.add_raw_thought(chunk['text'])
                    
                if chunk['type'] == 'text':
                    logger.debug(f"Extraction chunk {chunk_count}: Received text content ({len(chunk['text'])} chars)")
                    full_text += chunk['text']
            
            logger.info(f"Extraction streaming loop finished after {chunk_count} chunks. full_text_len={len(full_text)}")
            
            # Flush refiner at end
            if refiner:
                 await refiner.flush()
            
            # Combine text and thoughts for extraction search if text is empty
            # Sometimes models put the results in the wrong part
            combined_search_area = full_text.strip()
            if not combined_search_area and all_thoughts:
                logger.warning("Empty text response, but found thoughts. Searching thoughts for JSON.")
                combined_search_area = all_thoughts.strip()
            
            # Find JSON boundaries
            start_idx = combined_search_area.find('[')
            end_idx = combined_search_area.rfind(']')
            
            if start_idx != -1 and end_idx != -1:
                json_text = combined_search_area[start_idx:end_idx + 1]
            else:
                json_text = combined_search_area
            
            try:
                claims = json.loads(json_text)
            except json.JSONDecodeError:
                # Cleanup attempt
                cleaned = re.sub(r',\s*([\]}])', r'\1', json_text)
                cleaned = re.sub(r'//.*', '', cleaned) # Remove comments if any
                claims = json.loads(cleaned)
            
            if not isinstance(claims, list):
                raise ValueError(f"Extracted JSON is not a list: {type(claims)}")
            
            # Ensure each claim has required fields
            for i, claim in enumerate(claims):
                claim["id"] = f"claim_{i+1}"
                if "verbatim" not in claim:
                    claim["verbatim"] = claim.get("claim", "")
                # Ensure verbatim is actually in the text (basic check)
                if claim["verbatim"] not in text:
                    # Attempt simple fix: check if it's a whitespace issue
                    trimmed = claim["verbatim"].strip()
                    if trimmed in text:
                        claim["verbatim"] = trimmed
            
            logger.info(f"Successfully extracted {len(claims)} claims:")
            for i, claim in enumerate(claims):
                logger.info(f"  Claim {i+1}: {claim.get('claim')}")
                logger.info(f"  Verbatim: {claim.get('verbatim')}")
            
            # Also log full JSON for deep cross-checking
            logger.debug(f"Full Extracted Claims JSON: {json.dumps(claims, indent=2)}")
            return claims
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            logger.error(f"Text Response Head: {full_text[:200]}")
            logger.error(f"Thoughts Response Head: {all_thoughts[:200]}")
            
            # Smart fallback: split by sentences and take first 3 as separate potential claims
            sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
            fallback_claims = []
            for i in range(min(3, len(sentences))):
                fallback_claims.append({
                    "id": f"claim_fb_{i+1}",
                    "claim": sentences[i] + ".",
                    "verbatim": sentences[i] + ".",
                    "context": sentences[i],
                    "type": "general",
                    "is_quote": False,
                    "confidence": 0.5
                })
            
            return fallback_claims if fallback_claims else [{
                "id": "claim_fallback",
                "claim": text[:200] + "...",
                "verbatim": text[:100],
                "context": text[:500],
                "type": "general",
                "is_quote": False,
                "confidence": 0.3
            }]
    
    async def refine_claims(self, claims: List[Dict], user_feedback: str) -> List[Dict[str, Any]]:
        # Same as before but with JSON mode
        prompt = f"Update these claims based on feedback: {user_feedback}\n\nClaims: {json.dumps(claims)}"
        try:
            resp = await self.vertex_client.generate_with_grounding(
                prompt=prompt,
                extra_config={"response_mime_type": "application/json"}
            )
            text_resp = resp["text"].strip()
            s = text_resp.find('[')
            e = text_resp.rfind(']')
            if s != -1 and e != -1:
                return json.loads(text_resp[s:e+1])
            return json.loads(text_resp)
        except:
            return claims

extraction_agent = ExtractionAgent()
