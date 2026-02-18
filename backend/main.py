"""
Main FastAPI application entry point for the fact-checker service.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import settings
from api.routes import router as api_router
from websocket_app.websocket_handler import connection_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Fact-Checker API Service")
    
    # Validate GCP setup
    if not settings.validate_gcp_setup():
        logger.warning(
            "GCP credentials not configured. "
            "Please set GCP_PROJECT_ID and place service account key in /key folder."
        )
    else:
        logger.info(f"GCP Project: {settings.gcp_project_id}")
        logger.info(f"Credentials: {settings.credentials_path}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Fact-Checker API Service")


# Create FastAPI application
app = FastAPI(
    title="Fact-Checker API",
    description="Agentic fact-checking tool for editorial workflows",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Fact-Checker API",
        "version": "1.0.0",
        "status": "running",
        "gcp_configured": settings.validate_gcp_setup()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "gcp_configured": settings.validate_gcp_setup()
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time updates."""
    await connection_manager.connect(websocket, session_id)
    logger.info(f"WebSocket connected for session: {session_id}")
    
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            logger.debug(f"Received from client {session_id}: {data}")
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, session_id)
        logger.info(f"WebSocket disconnected for session: {session_id}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info"
    )
