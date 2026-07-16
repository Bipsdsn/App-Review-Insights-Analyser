"""FastAPI server exposing pipeline outputs — deployable on Railway.

Read endpoints serve PII-free artifacts only. The run endpoint triggers
LLM spend, so it is protected by a RUN_TOKEN environment variable.

Start: uvicorn server:app --host 0.0.0.0 --port $PORT
"""

import json
import logging
import os
import threading
from pathlib import Path

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

log = logging.getLogger("server")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="App Review Insights API", version="1.0.0")

# CORS: allow the Vercel frontend. Override with FRONTEND_ORIGIN env var.
frontend_origin = os.environ.get("FRONTEND_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin] if frontend_origin != "*" else ["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_run_state = {"running": False, "last_error": None}


def _load_config() -> dict:
    with open(ROOT / "config.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config["reuse_legend"] = False
    config["dry_run"] = False
    return config


@app.get("/")
def health():
    return {"service": "app-review-insights", "status": "ok", "running": _run_state["running"]}


@app.get("/api/theme-counts")
def theme_counts():
    path = ROOT / "output" / "theme_counts.json"
    if not path.exists():
        raise HTTPException(404, "No run yet — trigger POST /api/run first")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/theme-legend", response_class=PlainTextResponse)
def theme_legend():
    path = ROOT / "output" / "theme_legend.md"
    if not path.exists():
        raise HTTPException(404, "No run yet")
    return path.read_text(encoding="utf-8")


@app.get("/api/note", response_class=PlainTextResponse)
def latest_note():
    notes = sorted((ROOT / "output").glob("weekly_note_*.md"))
    notes = [n for n in notes if ".FAILED" not in n.name]
    if not notes:
        raise HTTPException(404, "No note yet")
    return notes[-1].read_text(encoding="utf-8")


@app.get("/api/reviews")
def reviews(limit: int = 100):
    """PII-free themed reviews as JSON (capped)."""
    import pandas as pd

    path = ROOT / "data" / "reviews_themed.csv"
    if not path.exists():
        raise HTTPException(404, "No run yet")
    df = pd.read_csv(path).head(max(1, min(limit, 500)))
    return json.loads(df.to_json(orient="records"))


@app.get("/api/email-draft")
def email_draft():
    path = ROOT / "output" / "email_draft.eml"
    if not path.exists():
        raise HTTPException(404, "No draft yet")
    return FileResponse(path, media_type="message/rfc822", filename="email_draft.eml")


def _run_pipeline() -> None:
    from src import draft_email, generate_note, group_themes, import_reviews

    try:
        config = _load_config()
        for stage in (import_reviews, group_themes, generate_note, draft_email):
            stage.run(config)
        _run_state["last_error"] = None
    except Exception as exc:  # surfaced via /api/run-status
        log.error("pipeline run failed: %s", exc)
        _run_state["last_error"] = str(exc)
    finally:
        _run_state["running"] = False


@app.post("/api/run")
def trigger_run(background_tasks: BackgroundTasks, x_run_token: str = Header(default="")):
    """Trigger a full pipeline run (costs LLM quota — token protected)."""
    expected = os.environ.get("RUN_TOKEN")
    if not expected:
        raise HTTPException(503, "RUN_TOKEN not configured on server")
    if x_run_token != expected:
        raise HTTPException(401, "Invalid or missing X-Run-Token header")
    if _run_state["running"]:
        raise HTTPException(409, "A run is already in progress")
    _run_state["running"] = True
    background_tasks.add_task(_run_pipeline)
    return {"started": True, "note": "Poll /api/run-status for completion"}


@app.get("/api/run-status")
def run_status():
    return {"running": _run_state["running"], "last_error": _run_state["last_error"]}
