"""
API Routers Package

Contains all FastAPI router modules for different API endpoints.
"""

from .document import router as document_router

# List of all available routers
__all__ = [
    "document_router",
]

# You can add more routers here as they're created
# from .query import router as query_router
# from .user import router as user_router