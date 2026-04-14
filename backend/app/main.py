import logging
from time import perf_counter
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.limiter import limiter
from app.routers import auth, companies, contacts, deals, email_draft, follow_ups, interactions, notifications, social
from app.routers import dashboard

# Structured JSON logging in production, standard logging in development
if settings.app_env == "production":
    from pythonjsonlogger import json as json_log

    handler = logging.StreamHandler()
    handler.setFormatter(
        json_log.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    )
    logging.root.handlers = [handler]
    logging.root.setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting CRM backend (env={settings.app_env})")

    if settings.app_env == "production":
        settings.validate_production()

    if settings.telegram_enabled:
        try:
            from app.services.telegram_service import get_telegram_app
            await get_telegram_app()
            logger.info("Telegram bot started")
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")

        try:
            from app.scheduler import start_scheduler
            start_scheduler()
            logger.info("Scheduler started")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")

    yield

    # Shutdown
    if settings.telegram_enabled:
        try:
            from app.services.telegram_service import stop_telegram_app
            await stop_telegram_app()
        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}")
        try:
            from app.scheduler import stop_scheduler
            stop_scheduler()
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")


app = FastAPI(title="Voss CRM", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _add_security_headers(response):
    """Add security headers to a response object."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.app_env == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Combined middleware: request logging, error handling, security headers.

    Must be a single middleware because BaseHTTPMiddleware re-raises exceptions
    through call_next() — a separate @app.exception_handler(Exception) never
    sees them. Catching here ensures unhandled errors always return JSON 500.
    """
    start = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((perf_counter() - start) * 1000, 1)
        logger.error(
            f"{request.method} {request.url.path} -> 500 ({duration_ms}ms)\n"
            f"{traceback.format_exc()}"
        )
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
        _add_security_headers(response)
        return response

    duration_ms = round((perf_counter() - start) * 1000, 1)
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)"
    )
    _add_security_headers(response)
    return response


app.include_router(auth.router)
app.include_router(contacts.router)
app.include_router(companies.router)
app.include_router(deals.router)
app.include_router(interactions.router)
app.include_router(follow_ups.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(email_draft.router)
app.include_router(social.router)


@app.get("/api/health")
async def health():
    result = {"status": "ok", "env": settings.app_env}
    try:
        from app.sheets import get_spreadsheet
        get_spreadsheet()
        result["google_sheets"] = "connected"
    except Exception as e:
        logger.error(f"Health check — Google Sheets error: {e}")
        result["status"] = "degraded"
        result["google_sheets"] = "unavailable"
    return result
