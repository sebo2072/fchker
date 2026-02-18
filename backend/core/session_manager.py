"""
Session manager for tracking active verification sessions.
Maintains session state, user confirmations, and results.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


class Session:
    """Represents a verification session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.text: Optional[str] = None
        self.extracted_claims: List[dict] = []
        self.confirmed_claims: List[dict] = []
        self.verification_results: List[dict] = []
        self.status: str = "created"  # created, extracting, awaiting_confirmation, verifying, completed
        self.remaining_text: str = "" # To support 750-word chunked sprints
        self.metadata: dict = {}
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired."""
        expiry_time = self.last_activity + timedelta(minutes=timeout_minutes)
        return datetime.utcnow() > expiry_time
    
    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "status": self.status,
            "extracted_claims_count": len(self.extracted_claims),
            "confirmed_claims_count": len(self.confirmed_claims),
            "verification_results_count": len(self.verification_results),
            "metadata": self.metadata
        }


class SessionManager:
    """Manages verification sessions."""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session and return its ID."""
        if session_id:
            if session_id in self.sessions:
                logger.info(f"Returning existing session: {session_id}")
                return session_id
            new_id = session_id
        else:
            new_id = str(uuid.uuid4())
            
        self.sessions[new_id] = Session(new_id)
        logger.info(f"Created/Recovered session: {new_id}")
        return new_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        session = self.sessions.get(session_id)
        if session:
            session.update_activity()
        return session
    
    def delete_session(self, session_id: str):
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
    
    def cleanup_expired_sessions(self, timeout_minutes: int = 30):
        """Remove expired sessions."""
        expired = [
            sid for sid, session in self.sessions.items()
            if session.is_expired(timeout_minutes)
        ]
        
        for session_id in expired:
            self.delete_session(session_id)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    def get_all_sessions(self) -> List[dict]:
        """Get all active sessions."""
        return [session.to_dict() for session in self.sessions.values()]


# Global session manager instance
session_manager = SessionManager()
