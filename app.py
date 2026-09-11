import logging
import os
import threading
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.config import (
    PORT,
    REFRESH_SECONDS,
    WEB_DIR,
)

from app.services.chat_service import process_chat_message
from app.tfwm_client import tfwm_client
from app.json_safe import make_json_safe


logging.basicConfig(
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Birmingham Smart Public Transport Assistant",
    version="1.0.0",
    description=(
        "Context-aware public transport assistant using "
        "TfWM GTFS/GTFS-RT data and ML ETA prediction."
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


def background_refresh():
    """
    Periodically refresh TfWM GTFS-RT data.

    The server keeps credentials private.
    """

    while True:

        try:
            if tfwm_client.configured:

                result = tfwm_client.refresh_all()

                logger.info(
                    "TfWM refresh: vehicles=%s trip_updates=%s",
                    result.get("vehicle_records"),
                    result.get("trip_update_records"),
                )

            else:

                logger.warning(
                    "TfWM credentials are not configured. "
                    "Live refresh skipped."
                )

        except Exception as exc:

            logger.exception(
                "Background TfWM refresh failed: %s",
                exc,
            )

        time.sleep(REFRESH_SECONDS)


@app.on_event("startup")
def startup_event():

    # Initial refresh
    if tfwm_client.configured:

        try:
            tfwm_client.refresh_all()

        except Exception as exc:

            logger.warning(
                "Initial TfWM refresh failed: %s",
                exc,
            )

    thread = threading.Thread(
        target=background_refresh,
        daemon=True,
    )

    thread.start()


@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "Birmingham Smart Public Transport Assistant",
        "version": "1.0.0",
        "tfwm_configured": tfwm_client.configured,
        "vehicle_records": len(
            tfwm_client.vehicle_positions
        ),
        "trip_update_records": len(
            tfwm_client.trip_updates
        ),
        "refresh_seconds": REFRESH_SECONDS,
    }


@app.get("/")
def home():

    index_file = WEB_DIR / "index.html"

    if not index_file.exists():

        return JSONResponse(
            {
                "service": (
                    "Birmingham Smart Public "
                    "Transport Assistant"
                ),
                "status": "running",
            }
        )

    return FileResponse(index_file)


@app.post("/chat")
def chat(request: ChatRequest):

    try:

        result = process_chat_message(
            request.message
        )

        return make_json_safe(result)

    except Exception as exc:

        logger.exception(
            "Chat request failed"
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "reply": (
                    "Sorry, something went wrong "
                    "while processing your request."
                ),
                "error": str(exc),
            },
        )


@app.get("/api")
def api_info():

    return {
        "name": (
            "Birmingham Smart Public "
            "Transport Assistant"
        ),
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "frontend": "/",
        },
    }


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
    )
