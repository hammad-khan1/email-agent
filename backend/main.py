"""
FastAPI application entry point for AI HR Email Automation Agent.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.core.config import settings
from backend.core.logger import setup_logger
from backend.database.database import init_db
from backend.scheduler.scheduler import start_scheduler, stop_scheduler
from backend.routes import (
    auth_routes,
    contact_routes,
    email_routes,
    template_routes,
    gmail_routes,
    ai_routes,
    report_routes,
    settings_routes,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    setup_logger()
    logger.info("Starting AI HR Email Automation Agent...")
    init_db()
    start_scheduler()
    yield
    logger.info("Shutting down...")
    stop_scheduler()


app = FastAPI(
    title="AI HR Email Automation Agent",
    description="Automate personalized HR emails with Gmail API and Gemini AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(auth_routes.router, prefix="/auth", tags=["Auth"])
app.include_router(contact_routes.router, prefix="/contacts", tags=["Contacts"])
app.include_router(email_routes.router, prefix="/emails", tags=["Emails"])
app.include_router(template_routes.router, prefix="/templates", tags=["Templates"])
app.include_router(gmail_routes.router, prefix="/gmail", tags=["Gmail"])
app.include_router(ai_routes.router, prefix="/ai", tags=["AI"])
app.include_router(report_routes.router, prefix="/reports", tags=["Reports"])
app.include_router(settings_routes.router, prefix="/settings", tags=["Settings"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "app": "AI HR Email Automation Agent", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
