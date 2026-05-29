"""FastAPI server — serves the chat UI and handles agent invocations.

Lifespan manages:
  - AsyncSqliteSaver (persistent multi-turn memory)
  - ChromaDB collection (seeded topic data)
  - Compiled LangGraph
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent.graph import build_graph
from agent.tools import init_chromadb

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Global references (populated during lifespan)
# ──────────────────────────────────────────────────────────────────────
_app_state: dict[str, Any] = {}

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise shared resources on startup; clean up on shutdown."""
    logger.info("Starting Christianity AI Assistant ...")

    # 1. ChromaDB (in-memory, seeded with topic data)
    collection = init_chromadb()
    _app_state["chromadb_collection"] = collection
    logger.info("ChromaDB initialised")

    # 2. SqliteSaver for persistent checkpoints
    db_path = str(BASE_DIR / "checkpoints.db")
    async with AsyncSqliteSaver.from_conn_string(db_path) as saver:
        _app_state["saver"] = saver
        logger.info("SqliteSaver ready (%s)", db_path)

        # 3. Build & compile the LangGraph
        graph = build_graph(chromadb_collection=collection)
        compiled = graph.compile(checkpointer=saver)
        _app_state["graph"] = compiled
        logger.info("LangGraph compiled")

        yield  # ← app is running

    # Shutdown
    _app_state.clear()
    logger.info("Shut down complete.")


# ──────────────────────────────────────────────────────────────────────
# FastAPI app
# ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Christianity AI Assistant",
    description="Multi-agent theological Q&A with deterministic scripture grounding",
    version="1.0.0",
    lifespan=lifespan,
)

# Static files & templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ──────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, response: Response):
    """Serve the chat UI."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        response = templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"session_id": session_id},
        )
        response.set_cookie("session_id", session_id, httponly=True, max_age=86400 * 7)
        return response

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"session_id": session_id},
    )


@app.post("/chat")
async def chat(request: Request, message: str = Form(...)):
    """Handle a chat message — invoke the LangGraph and return the response."""
    session_id = request.cookies.get("session_id", str(uuid.uuid4()))

    graph = _app_state.get("graph")
    if graph is None:
        return JSONResponse(
            {"error": "Server not ready"}, status_code=503
        )

    logger.info("═══ NEW MESSAGE (session=%s) ═══", session_id[:8])
    logger.info("User: %s", message[:200])

    # Build initial state
    initial_state = {
        "messages": [HumanMessage(content=message)],
        "next_node": "",
        "denomination": "general",
        "is_controversial": False,
        "image_url": "",
        "retrieved_verses": [],
        "retry_count": 0,
    }

    config = {"configurable": {"thread_id": session_id}}

    try:
        result = await graph.ainvoke(initial_state, config=config)

        # Extract the last AI message
        ai_messages = [
            m for m in result.get("messages", [])
            if hasattr(m, "type") and m.type == "ai"
        ]

        response_text = ai_messages[-1].content if ai_messages else "I'm sorry, I couldn't generate a response."
        image_url = result.get("image_url", "")

        logger.info("Response: %s", response_text[:200])
        if image_url:
            logger.info("Image URL: present (%d chars)", len(image_url))

        return JSONResponse({
            "response": response_text,
            "image_url": image_url,
            "denomination": result.get("denomination", "general"),
        })

    except Exception as exc:
        logger.exception("Graph invocation failed")
        return JSONResponse(
            {"error": f"An error occurred: {str(exc)}"},
            status_code=500,
        )


@app.post("/reset")
async def reset_session(request: Request, response: Response):
    """Reset the user's session — starts a new conversation thread."""
    new_session = str(uuid.uuid4())
    resp = JSONResponse({"status": "ok", "session_id": new_session})
    resp.set_cookie("session_id", new_session, httponly=True, max_age=86400 * 7)
    return resp


# ──────────────────────────────────────────────────────────────────────
# Dev entrypoint
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
