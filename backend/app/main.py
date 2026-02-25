import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, companies, contacts, deals, email_draft, follow_ups, interactions
from app.routers import dashboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting CRM backend (env={settings.app_env})")

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
        except Exception:
            pass
        try:
            from app.scheduler import stop_scheduler
            stop_scheduler()
        except Exception:
            pass


app = FastAPI(title="Voss CRM", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(contacts.router)
app.include_router(companies.router)
app.include_router(deals.router)
app.include_router(interactions.router)
app.include_router(follow_ups.router)
app.include_router(dashboard.router)
app.include_router(email_draft.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
