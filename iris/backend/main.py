import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from agents import FALLBACK, SEATS, run_check

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("iris.api")

app = FastAPI(title="IRIS", version="1.1")

origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

FRONTEND = Path(__file__).resolve().parent.parent / "index.html"


class CheckIn(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


@app.get("/", include_in_schema=False)
def frontend():
    """Serve the self-contained frontend from the same origin as the API."""
    return FileResponse(FRONTEND)


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "version": app.version,
        "seats": SEATS,
        "fallback": FALLBACK or None,
        "providers": {
            "meta": bool(os.getenv("MODEL_API_KEY") or os.getenv("META_API_KEY")),
            "gemini": bool(os.getenv("GEMINI_API_KEY")),
            "ollama": True,
        },
    }


@app.post("/api/check")
async def check(body: CheckIn):
    question = body.question.strip()
    if len(question) < 3:
        raise HTTPException(status_code=422, detail="Question must contain at least 3 non-whitespace characters.")

    async def stream():
        try:
            async for event in run_check(question):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception:
            # Keep stack traces in server logs; never send internal exception details to browsers.
            logger.exception("Unhandled error while processing an IRIS check")
            yield f"data: {json.dumps({'type': 'error', 'error': 'An internal server error interrupted this check.'})}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
