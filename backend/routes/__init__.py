"""Package routes — endpoints FastAPI de l'API."""

from backend.routes.analyze import router as analyze_router
from backend.routes.upload import router as upload_router
from backend.routes.chat import router as chat_router
from backend.routes.report import router as report_router

__all__ = [
    "analyze_router",
    "upload_router",
    "chat_router",
    "report_router",
]
