"""
Orchestration service managing the fact-checking workflow.
Coordinates claim extraction, user confirmation, and verification.
"""
import logging
from typing import List, Dict, Optional
import asyncio

from agents.extraction_agent import extraction_agent
from agents.verification_agent import verification_agent
from core.session_manager import session_manager
from websocket_app.websocket_handler import connection_manager

logger = logging.getLogger(__name__)


class OrchestrationService:
    """Main orchestration service for fact-checking workflows."""
    
    def __init__(self):
        self.extraction_agent = extraction_agent
        self.verification_agent = verification_agent
        self.session_manager = session_manager
        self.connection_manager = connection_manager
    
    async def process_text_extraction(
        self,
        text: str,
        session_id: str
    ) -> Dict:
        """
        Phase 1: Extract claims from text and await user confirmation.
        Supports 750-word chunked sprints for large texts.
        """
        logger.info(f"Processing text extraction for session {session_id}")
        
        # Get or create session
        session = self.session_manager.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Invalid session ID: {session_id}")
            
        # Check word count for chunking
        words = text.split()
        max_words = 750
        
        current_chunk_text = text
        remaining_text = ""
        
        if len(words) > max_words:
            logger.info(f"Large text detected ({len(words)} words). Slicing first {max_words} words.")
            current_chunk_text = " ".join(words[:max_words])
            remaining_text = " ".join(words[max_words:])
            
            # Store remaining text for next sprint
            session.remaining_text = remaining_text
            
            await self.connection_manager.broadcast_status(
                session_id,
                "extracting",
                {"message": f"Processing first {max_words} words. Remaining {len(words) - max_words} words will follow in the next sprint."}
            )
        else:
            session.remaining_text = ""
        
        # Update session
        session.text = text
        session.status = "extracting"
        
        # Notify frontend
        await self.connection_manager.broadcast_status(
            session_id,
            "extracting",
            {"message": "Extracting claims from text..."}
        )
        
        try:
            # Create progress callback for extraction
            async def progress_callback(update: Dict):
                await self.connection_manager.broadcast_thinking_update(session_id, update)
                
            # Extract claims from the CURRENT chunk
            claims = await self.extraction_agent.extract_claims(current_chunk_text, progress_callback)
            
            # Store in session
            session.extracted_claims = claims
            session.status = "awaiting_confirmation"
            
            # Send claims to frontend
            await self.connection_manager.broadcast_claim_extraction(session_id, claims)
            
            logger.info(f"Extracted {len(claims)} claims for session {session_id}")
            
            return {
                "status": "awaiting_confirmation",
                "session_id": session_id,
                "claims": claims,
                "message": "Please review and confirm the claims to verify"
            }
            
        except Exception as e:
            logger.error(f"Error in claim extraction: {e}")
            session.status = "error"
            await self.connection_manager.broadcast_error(session_id, str(e))
            raise
    
    async def process_verification(
        self,
        confirmed_claims: List[Dict],
        session_id: str
    ) -> Dict:
        """
        Phase 2: Verify confirmed claims with non-blocking background task.
        
        Args:
            confirmed_claims: List of user-confirmed claims to verify
            session_id: Session identifier
        
        Returns:
            Immediate acknowledgment that verification has started
        """
        logger.info(f"Initiating background verification for session {session_id} ({len(confirmed_claims)} claims)")
        
        # Get session
        session = self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Invalid session ID: {session_id}")
        
        # Update session status
        session.confirmed_claims = confirmed_claims
        session.status = "verifying"
        session.verification_results = [] # Clear previous results
        
        # Notify frontend
        await self.connection_manager.broadcast_status(
            session_id,
            "verifying",
            {
                "message": f"Verifying {len(confirmed_claims)} claims...",
                "total_claims": len(confirmed_claims)
            }
        )
        
        # Start verification loop in background
        asyncio.create_task(self._run_verification_loop(session_id, confirmed_claims))
        
        return {
            "status": "verifying",
            "session_id": session_id,
            "message": f"Verification of {len(confirmed_claims)} claims started in background"
        }

    async def _run_verification_loop(self, session_id: str, confirmed_claims: List[Dict]):
        """Background task to verify claims and stream results."""
        try:
            session = self.session_manager.get_session(session_id)
            if not session:
                logger.error(f"Session {session_id} lost during background verification")
                return

            # Progress callback for thinking process
            async def progress_callback(update: Dict):
                await self.connection_manager.broadcast_thinking_update(session_id, update)
            
            # Process claims sequentially one by one to prevent 429 errors
            results = []
            for i, claim in enumerate(confirmed_claims):
                # Add a small delay between claims to avoid grounding burst limits
                if i > 0:
                    logger.info(f"Cooldown delay for 1.5s before claim {i+1}...")
                    await asyncio.sleep(1.5)
                try:
                    logger.info(f"Session {session_id}: Starting verification {i+1}/{len(confirmed_claims)}")
                    result = await self.verification_agent.verify_claim(claim, session_id, progress_callback)
                    results.append(result)
                    
                    # Update session in-memory list
                    session.verification_results.append(result)
                    
                    # Stream individual result
                    await self.connection_manager.broadcast_verification_result(session_id, result)
                    
                except Exception as e:
                    logger.error(f"Error verifying individual claim {i+1} for session {session_id}: {e}")
            
            # Final session update
            session.status = "completed"
            
            # Final summary notification
            summary = self._generate_summary(results)
            await self.connection_manager.broadcast_status(
                session_id,
                "completed",
                {
                    "message": "All verifications completed",
                    "total_verified": len(results),
                    "results_summary": summary
                }
            )
            
            logger.info(f"Finished all background verifications for session {session_id}")
            
        except Exception as e:
            logger.error(f"Critical error in background verification loop for session {session_id}: {e}")
            await self.connection_manager.broadcast_error(session_id, f"Verification process failed: {str(e)}")
    
    async def verify_single_claim(
        self,
        claim_text: str,
        session_id: str
    ) -> Dict:
        """
        Single-claim verification mode (no extraction phase).
        
        Args:
            claim_text: The claim to verify
            session_id: Session identifier
        
        Returns:
            Verification result
        """
        logger.info(f"Single claim verification for session {session_id}")
        
        # Get session
        session = self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Invalid session ID: {session_id}")
        
        session.status = "verifying"
        
        # Create claim object
        claim = {
            "id": "single_claim",
            "claim": claim_text,
            "context": "",
            "type": "general",
            "is_quote": False,
            "confidence": 1.0
        }
        
        # Progress callback
        async def progress_callback(update: Dict):
            await self.connection_manager.broadcast_thinking_update(session_id, update)
        
        # Verify claim
        result = await self.verification_agent.verify_claim(claim, session_id, progress_callback)
        
        # Send result
        await self.connection_manager.broadcast_verification_result(session_id, result)
        
        session.verification_results = [result]
        session.status = "completed"
        
        return {
            "status": "completed",
            "session_id": session_id,
            "result": result
        }
    
    def _generate_summary(self, results: List[Dict]) -> Dict:
        """Generate summary statistics from verification results."""
        if not results:
            return {}
        
        status_counts = {}
        total_confidence = 0
        
        for result in results:
            status = result.get("status", "UNVERIFIED")
            status_counts[status] = status_counts.get(status, 0) + 1
            total_confidence += result.get("confidence", 0)
        
        return {
            "total_claims": len(results),
            "status_breakdown": status_counts,
            "average_confidence": total_confidence / len(results) if results else 0
        }


# Global orchestration service instance
orchestration_service = OrchestrationService()
