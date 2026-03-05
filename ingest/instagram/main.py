"""Instagram webhook listener service for VOSS CRM."""

import logging

from fastapi import FastAPI

from webhook import router as webhook_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="VOSS Instagram Listener", version="1.0.0")

app.include_router(webhook_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
