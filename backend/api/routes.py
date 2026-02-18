"""
API routes for the fact-checker service.
Defines REST endpoints for text analysis, claim verification, and session management.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
from pathlib import Path
import tempfile

from core.orchestration_service import orchestration_service
from core.session_manager import session_manager
from utils.pdf_processor import pdf_processor

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class VerifySingleRequest(BaseModel):
    """Request model for single claim verification."""
    claim: str = Field(..., description="The factual claim to verify")
    session_id: Optional[str] = Field(None, description="Optional session ID")


class AnalyzeTextRequest(BaseModel):
    """Request model for bulk text analysis."""
    text: str = Field(..., description="Text to analyze for factual claims")
    session_id: Optional[str] = Field(None, description="Optional session ID")


class ConfirmClaimsRequest(BaseModel):
    """Request model for confirming extracted claims."""
    session_id: str = Field(..., description="Session ID")
    confirmed_claims: List[dict] = Field(..., description="User-confirmed claims to verify")


class SessionResponse(BaseModel):
    """Response model for session information."""
    session_id: str
    status: str
    created_at: str
    last_activity: str
    extracted_claims_count: int
    confirmed_claims_count: int
    verification_results_count: int


# Endpoints

@router.post("/create-session")
async def create_session():
    """Create a new verification session."""
    try:
        session_id = session_manager.create_session()
        session = session_manager.get_session(session_id)
        
        return {
            "session_id": session_id,
            "status": "created",
            "message": "Session created successfully"
        }
    
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-single")
async def verify_single_claim(request: VerifySingleRequest):
    """
    Verify a single factual claim.
    
    This endpoint provides immediate verification without the extraction phase.
    Results are streamed via WebSocket to the session.
    """
    try:
        # Create or recover session
        session_id = session_manager.create_session(request.session_id)
        
        # Verify claim
        result = await orchestration_service.verify_single_claim(
            claim_text=request.claim,
            session_id=session_id
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in single claim verification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-text")
async def analyze_text(request: AnalyzeTextRequest):
    """
    Analyze text and extract factual claims.
    
    This is Phase 1 of the bulk analysis workflow.
    Returns extracted claims for user confirmation.
    """
    try:
        # Create or recover session
        session_id = session_manager.create_session(request.session_id)
        
        # Extract claims
        result = await orchestration_service.process_text_extraction(
            text=request.text,
            session_id=session_id
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in text analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm-claims")
async def confirm_claims(request: ConfirmClaimsRequest):
    """
    Submit confirmed claims for verification.
    
    This is Phase 2 of the bulk analysis workflow.
    Verifies user-confirmed claims in parallel with streaming results.
    """
    try:
        # Get session
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Verify claims
        result = await orchestration_service.process_verification(
            confirmed_claims=request.confirmed_claims,
            session_id=request.session_id
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in claim verification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session information and status."""
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    try:
        # Clean up expired sessions first
        session_manager.cleanup_expired_sessions()
        
        sessions = session_manager.get_all_sessions()
        return {
            "sessions": sessions,
            "total": len(sessions)
        }
    
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_manager.delete_session(session_id)
        
        return {
            "message": "Session deleted successfully",
            "session_id": session_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: Optional[str] = None
):
    """
    Upload and extract text from a PDF file.
    
    Returns extracted text which can then be analyzed for claims.
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Create or recover session
        session_id = session_manager.create_session(session_id)
        session = session_manager.get_session(session_id) # Guaranteed to exist now
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = Path(temp_file.name)
        
        try:
            # Extract text
            extracted_text = pdf_processor.extract_text(temp_path)
            
            if not extracted_text:
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract text from PDF. The file may be image-based or corrupted."
                )
            
            # Store in session
            session.text = extracted_text
            session.metadata["pdf_filename"] = file.filename
            
            return {
                "session_id": session_id,
                "filename": file.filename,
                "extracted_text": extracted_text,
                "text_length": len(extracted_text),
                "message": "PDF text extracted successfully"
            }
        
        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for the API."""
    return {
        "status": "healthy",
        "service": "fact-checker-api"
    }
