"""
Verification agent using Gemini with Google Search Grounding.
Implements thinking process streaming and claim verification.
"""
import logging
from typing import Dict, Callable, Optional
import asyncio

from utils.vertex_client import vertex_client

logger = logging.getLogger(__name__)


class VerificationAgent:
    """Agent for verifying factual claims with grounding."""
    
    def __init__(self):
        self.vertex_client = vertex_client
    
    async def verify_claim(
        self,
        claim: Dict,
        session_id: str,
        progress_callback: Optional[Callable] = None,
        task_index: Optional[int] = None,
        total_tasks: Optional[int] = None
    ) -> Dict:
        """
        Verify a factual claim using Gemini with Google Search grounding.
        
        Args:
            claim: Claim dictionary with 'claim' text and metadata
            session_id: Session identifier for thinking refinement
            progress_callback: Optional callback for streaming thinking updates
        
        Returns:
            Verification result with status, confidence, evidence, and sources
        """
        from core.thinking_refiner import ThinkingRefiner
        
        claim_text = claim.get("claim", "")
        claim_id = claim.get("id", "unknown")
        
        logger.info(f"Verifying claim {claim_id}: {claim_text[:100]}...")
        
        # Initialize thinking refiner
        refiner = None
        if progress_callback:
            refiner = ThinkingRefiner(session_id, claim_id, progress_callback)
        
        # Send initial status
        if progress_callback:
            message = "Initializing verification parameters..."
            if task_index is not None:
                # Determine ordinal suffix (1st, 2nd, 3rd, 4th...)
                suffix = "th"
                if not 11 <= (task_index % 100) <= 13:
                    suffix = {1: "st", 2: "nd", 3: "rd"}.get(task_index % 10, "th")
                message = f"Starting up with the {task_index}{suffix} verification task."
                
            await progress_callback({
                "claim_id": claim_id,
                "phase": "ANALYZING",
                "message": message
            })
        
        prompt = f"""You are a professional fact-checker. Verify the following claim using real-time information from Google Search.

Claim to verify:
\"\"\"{claim_text}\"\"\"

Context: {claim.get('context', 'No additional context provided')}

Please provide:

1. **Thinking Process**: Explain your reasoning step-by-step
   - What sources are you looking for?
   - What evidence supports or contradicts the claim?
   - How reliable are the sources?

2. **Verification Status**: Choose ONE of:
   - VERIFIED: The claim is factually accurate based on reliable sources
   - PARTIALLY_VERIFIED: Parts of the claim are accurate, but some details are incorrect or unverified
   - UNVERIFIED: Cannot find sufficient evidence to verify the claim
   - DISPUTED: The claim is contradicted by reliable sources
   - FALSE: The claim is demonstrably false

3. **Confidence Score**: Rate your confidence (0.0 to 1.0)

4. **Evidence Summary**: Summarize the key evidence found

5. **Sources**: List the most relevant sources used (these will be automatically cited from Google Search grounding)

Format your response as follows:

## Thinking Process
[Your step-by-step reasoning]

## Verification Status
[VERIFIED|PARTIALLY_VERIFIED|UNVERIFIED|DISPUTED|FALSE]

## Confidence Score
[0.0-1.0]

## Evidence Summary
[Summary of evidence]

## Key Findings
- [Finding 1]
- [Finding 2]
- [Finding 3]
"""

        try:
            # Prepare for response accumulation
            full_text = ""
            full_thought = ""
            all_citations = []
            
            # Generate verification with streaming for real-time thinking
            async for chunk in self.vertex_client.generate_streaming(
                prompt=prompt,
                temperature=0.1,
                max_output_tokens=2048,
                use_grounding=True
            ):
                if chunk["type"] == "thought":
                    thought_text = chunk["text"]
                    full_thought += thought_text
                    
                    # Pass raw thought to refiner for real-time polishing
                    if refiner:
                        await refiner.add_raw_thought(thought_text)
                    elif progress_callback:
                        # Fallback to direct raw stream if no refiner
                        await progress_callback({
                            "claim_id": claim_id,
                            "phase": "ANALYZING",
                            "message": thought_text,
                            "is_native_thought": True
                        })
                elif chunk["type"] == "citations":
                    all_citations.extend(chunk["data"])
                else:
                    full_text += chunk["text"]
            
            # Flush refiner to capture last bit of thinking
            if refiner:
                await refiner.flush()
            
            # Send final processing phase update
            if progress_callback:
                await progress_callback({
                    "claim_id": claim_id,
                    "phase": "VALIDATING",
                    "message": "Synthesizing final verdict and confidence score..."
                })
            
            # Parse response text
            verification_result = self._parse_verification_response(
                full_text,
                all_citations
            )
            
            # Add native thought if available and better than parsed one
            if full_thought:
                verification_result["thinking_process"] = full_thought
            
            # Add claim metadata
            verification_result["claim_id"] = claim_id
            verification_result["claim_text"] = claim_text
            verification_result["claim_type"] = claim.get("type", "general")
            
            # Send completion update
            if progress_callback:
                await progress_callback({
                    "claim_id": claim_id,
                    "phase": "completed",
                    "message": f"Verification complete: {verification_result['status']}",
                    "is_final_thinking": True,
                    "result": verification_result
                })
            
            logger.info(f"Claim {claim_id} verified: {verification_result['status']}")
            return verification_result
            
        except Exception as e:
            logger.error(f"Error verifying claim {claim_id}: {e}")
            
            # Send error update
            if progress_callback:
                await progress_callback({
                    "claim_id": claim_id,
                    "phase": "error",
                    "message": f"Verification failed: {str(e)}"
                })
            
            raise
    
    def _parse_verification_response(self, response_text: str, citations: list) -> Dict:
        """Parse the verification response into structured data."""
        result = {
            "thinking_process": "",
            "status": "UNVERIFIED",
            "confidence": 0.5,
            "evidence_summary": "",
            "key_findings": [],
            "sources": citations,
            "raw_response": response_text
        }
        
        try:
            # Extract sections
            sections = response_text.split("##")
            
            for section in sections:
                section = section.strip()
                
                if section.startswith("Thinking Process"):
                    result["thinking_process"] = section.replace("Thinking Process", "").strip()
                
                elif section.startswith("Verification Status"):
                    status_text = section.replace("Verification Status", "").strip()
                    # Extract status keyword
                    for status in ["VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "DISPUTED", "FALSE"]:
                        if status in status_text.upper():
                            result["status"] = status
                            break
                
                elif section.startswith("Confidence Score"):
                    confidence_text = section.replace("Confidence Score", "").strip()
                    try:
                        # Extract first number found
                        import re
                        match = re.search(r'(\d+\.?\d*)', confidence_text)
                        if match:
                            result["confidence"] = float(match.group(1))
                            # Ensure it's between 0 and 1
                            if result["confidence"] > 1:
                                result["confidence"] = result["confidence"] / 100
                    except:
                        pass
                
                elif section.startswith("Evidence Summary"):
                    result["evidence_summary"] = section.replace("Evidence Summary", "").strip()
                
                elif section.startswith("Key Findings"):
                    findings_text = section.replace("Key Findings", "").strip()
                    # Extract bullet points
                    findings = [
                        line.strip().lstrip("-•*").strip()
                        for line in findings_text.split("\n")
                        if line.strip() and line.strip().startswith(("-", "•", "*"))
                    ]
                    result["key_findings"] = findings
            
        except Exception as e:
            logger.error(f"Error parsing verification response: {e}")
        
        return result


# Global verification agent instance
verification_agent = VerificationAgent()
