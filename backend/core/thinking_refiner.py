"""
Thinking refinement service to transform raw model thoughts into professional structured updates.
Uses real-time streaming to provide a smooth, narrative-driven experience.
"""
import logging
from typing import Dict, Optional, Callable, List
import json
import asyncio

from utils.openai_client import openai_client

logger = logging.getLogger(__name__)

class ThinkingRefiner:
    """Refines raw model thinking into a professional technical narrative in real-time."""
    
    def __init__(self, session_id: str, claim_id: str, progress_callback: Callable):
        self.session_id = session_id
        self.claim_id = claim_id
        self.progress_callback = progress_callback
        self.buffer = ""
        self.buffer_limit = 500
        self.is_refining = False
        self.lock = asyncio.Lock()
        self.phase_counter = 1
        self.refinement_tasks: List[asyncio.Task] = []

    async def add_raw_thought(self, text: str):
        """Append raw thought chunk and refine if buffer limit reached."""
        async with self.lock:
            self.buffer += text
            
            # Check if we should trigger refinement (500+ chars)
            if len(self.buffer) >= self.buffer_limit and not self.is_refining:
                # Trigger background refinement without blocking the primary stream
                task = asyncio.create_task(self._trigger_refinement())
                self.refinement_tasks.append(task)

    async def flush(self):
        """Final refinement of remaining buffer and wait for tasks."""
        async with self.lock:
            if self.buffer:
                # For flush, we process whatever is left
                await self._trigger_refinement(force=True)
            
            # Wait for any pending background tasks
            if self.refinement_tasks:
                pending = [t for t in self.refinement_tasks if not t.done()]
                if pending:
                    await asyncio.wait(pending, timeout=10) # 10s safety timeout

    async def _trigger_refinement(self, force: bool = False):
        """Send buffer to fast agent for streaming narrative refinement."""
        if not self.buffer:
            return

        to_refine = ""
        
        if force:
            # Take everything
            to_refine = self.buffer
            self.buffer = ""
        else:
            # Intelligent chunking: find last sentence boundary
            # Look for . ! ? followed by space or end of string
            # We want the *last* valid split point to maximize chunk size
            # but keep it roughly within reason
            
            # Regex for sentence ending: [.!?] followed by whitespace
            import re
            
            # Search for sentence endings
            # We simply want to cut at the last punctuation mark that makes sense
            matches = list(re.finditer(r'[.!?]\s', self.buffer))
            
            if matches:
                last_match = matches[-1]
                cut_index = last_match.end()
                to_refine = self.buffer[:cut_index]
                self.buffer = self.buffer[cut_index:]
            else:
                # No sentence boundary found yet
                # If buffer is getting HUGE (> 2000 chars), force a cut to avoid stuck buffer
                if len(self.buffer) > 2000:
                   to_refine = self.buffer
                   self.buffer = ""
                else:
                    # Wait for more text to form a sentence
                    return
        
        if not to_refine.strip():
            return
            
        self.is_refining = True
        
        try:
            # Shift count for this "thought task"
            task_id = self.phase_counter
            self.phase_counter += 1
            
            # Narrative Refinement Prompt
            prompt = f"""You are a professional technical analyst and fact-checker. 
            Refine the following raw AI thinking process into a single, cohesive, professional narrative paragraph.
            
            Guidelines:
            - Output ONLY one logical paragraph.
            - Do NOT use bullet points, headers, or "Action/Headline" labels.
            - Focus on the intellectual progress: what is being searched, compared, or validated.
            - Maintain a technical, active voice like Claude or Antigravity.
            
            Raw Thinking to Synthesize:
            \"\"\"{to_refine}\"\"\"
            """
            
            logger.info(f"Triggering streaming refinement for task {task_id}")
            
            full_refined_paragraph = ""
            
            # Use the new streaming client
            async for delta in openai_client.stream_refined_update(prompt):
                if delta:
                    full_refined_paragraph += delta
                    # Broadcast delta for live-typing effect
                    await self.progress_callback({
                        "claim_id": self.claim_id,
                        "phase": f"PHASE {task_id}",
                        "message": full_refined_paragraph,
                        "is_refined": True,
                        "is_delta": True
                    })
            
            # Final refined update for this chunk
            await self.progress_callback({
                "claim_id": self.claim_id,
                "phase": f"PHASE {task_id}",
                "message": full_refined_paragraph,
                "is_refined": True,
                "is_streaming_complete": True
            })
            
        except Exception as e:
            logger.error(f"Thinking refinement failed for task {task_id}: {e}")
            # Fallback: Just send the raw chunk if refinement fails
            await self.progress_callback({
                "claim_id": self.claim_id,
                "phase": f"TASK {task_id}",
                "message": to_refine[:200] + "...",
                "is_raw_fallback": True
            })
        finally:
            self.is_refining = False
