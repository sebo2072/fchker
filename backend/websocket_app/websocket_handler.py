"""
WebSocket connection manager for real-time updates.
Handles connection lifecycle, session-based broadcasting, and message streaming.
"""
from fastapi import WebSocket
from typing import Dict, List
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time communication."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        
        self.active_connections[session_id].append(websocket)
        logger.info(f"WebSocket connected: session={session_id}, total={len(self.active_connections[session_id])}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
                logger.info(f"WebSocket disconnected: session={session_id}")
            
            # Clean up empty session lists
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
    
    async def send_message(self, session_id: str, message: dict):
        """Send a message to all connections for a session."""
        if session_id not in self.active_connections:
            logger.warning(f"No active connections for session: {session_id}")
            return
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        disconnected = []
        for connection in self.active_connections[session_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn, session_id)
    
    async def broadcast_thinking_update(self, session_id: str, thinking_data: dict):
        """Stream thinking process update to frontend."""
        message = {
            "type": "thinking_update",
            "data": thinking_data
        }
        await self.send_message(session_id, message)
    
    async def broadcast_verification_result(self, session_id: str, result: dict):
        """Send verification result to frontend."""
        message = {
            "type": "verification_result",
            "data": result
        }
        await self.send_message(session_id, message)
    
    async def broadcast_claim_extraction(self, session_id: str, claims: List[dict]):
        """Send extracted claims to frontend."""
        message = {
            "type": "claims_extracted",
            "data": {"claims": claims}
        }
        await self.send_message(session_id, message)
    
    async def broadcast_error(self, session_id: str, error: str):
        """Send error message to frontend."""
        message = {
            "type": "error",
            "data": {"error": error}
        }
        await self.send_message(session_id, message)
    
    async def broadcast_status(self, session_id: str, status: str, details: dict = None):
        """Send status update to frontend."""
        message = {
            "type": "status",
            "data": {
                "status": status,
                "details": details or {}
            }
        }
        await self.send_message(session_id, message)


# Global connection manager instance
connection_manager = ConnectionManager()
