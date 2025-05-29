import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import API_PREFIX
from app.routers import document
from app.database import init_db
from app.models.document import DocumentDB 
import os
print("SYSTEM PATH:", os.environ["PATH"])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Document Q&A with RAG",
    description="API for document upload and question answering using RAG",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        init_db()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise


# Include routers
app.include_router(document.router, prefix=API_PREFIX)


@app.get("/")
async def root():
    """API health check endpoint."""
    return {"status": "ok", "message": "Document Q&A API is running"}


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "api_prefix": API_PREFIX,
        "database": "connected"
    }