# Architecture Documentation

## 1. Runtime Topology

- **Frontend**: Jinja2 template + Bootstrap UI (`templates/index.html`, `static/style.css`)
- **Backend API**: FastAPI (`main.py`)
- **Agent Orchestration**: LangGraph (`agent/graph.py`)
- **Model Provider**: OpenRouter (`google/gemini-2.5-flash`, `google/gemini-2.5-flash-image`)
- **Scripture Source**: API.Bible
- **Vector Search**: ChromaDB ephemeral collection
- **Session Memory**: SQLite checkpointer

## 2. Request Lifecycle

1. Browser calls `POST /chat`
2. Server builds initial `AgentState`
3. Graph executes routed node path
4. Final AI message (and optional image URL) returned as JSON
5. State checkpoint persisted by thread ID (session cookie)

## 3. Safety Layers

- Supervisor-level adversarial and out-of-scope filtering
- Output quote verification against retrieved text
- Image prompt sanitation for policy-safe generation

## 4. Data Flow Notes

- Retrieval parameters passed internally via `[SEARCH_PARAMS]...[/SEARCH_PARAMS]` system messages
- Verse status passed via `[VERSE_STATUS]...[/VERSE_STATUS]`
- Guardrail retry instruction passed via `[GUARDRAIL_RETRY]`

## 5. Operational Dependencies

- Startup fails functionally without required keys/dependencies
- External API response quality and availability affect end-user reliability
