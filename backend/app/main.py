"""FastAPI entry point for the Multi-Agent Code Helper integration backend.

Provides the secure API facade between the React frontend and the Google ADK runtime.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import ALLOWED_ORIGINS, BACKEND_HOST, BACKEND_PORT
from .adk_client import ADKClient
from .session_service import SessionService
from .routes import health, sessions, chat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("code_helper_backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize and teardown client resources."""
    if not hasattr(app.state, "adk_client") or app.state.adk_client is None:
        logger.info("Initializing ADK Client and Session Service...")
        adk_client = ADKClient()
        session_service = SessionService(adk_client=adk_client)
        app.state.adk_client = adk_client
        app.state.session_service = session_service
    yield
    logger.info("Closing ADK Client connection...")
    if hasattr(app.state, "adk_client") and app.state.adk_client:
        await app.state.adk_client.close()


app = FastAPI(
    title="Multi-Agent Code Helper API",
    description="Integration backend facade between React frontend and Google ADK Multi-Agent runtime",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes under /api
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])


@app.get("/")
async def root():
    """Root info endpoint."""
    return JSONResponse({
        "name": "Multi-Agent Code Helper API",
        "status": "online",
        "health": "/api/health",
        "docs": "/docs",
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=BACKEND_HOST, port=BACKEND_PORT, reload=True)
