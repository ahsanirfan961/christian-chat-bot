# Software Design Specification (SDS)

## 1. System Overview

The system is composed of a FastAPI web server and a LangGraph workflow. Requests are routed through specialized nodes that enforce safety, scripture-grounding, and response quality.

## 2. High-Level Components

### 2.1 Web Layer (`main.py`)
- Initializes resources in FastAPI lifespan:
  - ChromaDB collection (`init_chromadb`)
  - SQLite checkpointer (`AsyncSqliteSaver`)
  - Compiled LangGraph
- Serves static assets and Jinja template
- Exposes chat/session endpoints

### 2.2 Agent Graph (`agent/graph.py`)
- Entry node: `supervisor`
- Conditional routes:
  - `supervisor -> verse_finder | image_gen | web_search | END`
  - `verse_finder -> output_assembler`
  - `web_search -> output_assembler`
  - `image_gen -> END`
  - `output_assembler -> output_assembler (retry) | END`

### 2.3 Node Implementations (`agent/nodes.py`)
- `supervisor_node`: intent classification + metadata extraction
- `verse_finder_node`: deterministic scripture retrieval (API.Bible + ChromaDB)
- `image_gen_node`: safe prompt transformation + image generation
- `web_search_node`: DuckDuckGo context retrieval
- `output_assembler_node`: final response synthesis + quote validation/retry

### 2.4 Tooling Layer (`agent/tools.py`)
- Verse reference parsing
- API.Bible passage retrieval and keyword search
- ChromaDB initialization and semantic search

### 2.5 Validation Layer (`agent/validators.py`)
- Extract quoted text from model output
- Normalize and compare quotes to retrieved corpus
- Redact unverifiable quotes

## 3. Data Design

### 3.1 Agent State Schema (`agent/state.py`)
- `messages`
- `next_node`
- `denomination`
- `is_controversial`
- `image_url`
- `retrieved_verses`
- `web_context`
- `retry_count`

### 3.2 Persistence
- SQLite database files:
  - `checkpoints.db` (runtime sessions)
  - `eval_checkpoints.db` (test runner)

### 3.3 Seed Data
- Topic-to-verse seed list in `agent/seed_data.py` loaded into ChromaDB collection `bible_topics`.

## 4. Processing Flows

### 4.1 QA Flow
1. User sends message
2. Supervisor classifies `qa`
3. Verse Finder retrieves verse candidates
4. Output Assembler composes answer
5. Guardrail validates quotes; retries up to 2 times if needed

### 4.2 Image Flow
1. Supervisor classifies `image`
2. Image node sanitizes prompt
3. OpenRouter image model invoked
4. Response and `image_url` returned

### 4.3 Web Search Flow
1. Supervisor classifies `web_search`
2. Web Search node fetches context snippets
3. Output Assembler integrates context in final answer

### 4.4 Rejection Flow
1. Supervisor classifies `adversarial` or `out_of_scope`
2. Static rejection message returned, graph ends

## 5. API Design Summary

See `docs/api.md` for endpoint contract details. Core endpoint behavior:
- `/chat` invokes compiled graph with session thread ID from cookie.
- Session endpoints manage and expose stored thread history.

## 6. Error Handling

- Graph readiness failures return HTTP 503
- Runtime exceptions in chat/history/session listing return HTTP 500 JSON errors
- Verse retrieval failures produce user-facing not-found guidance
- Image failures return fallback message with no image URL

## 7. Security and Safety Design

- Input guardrail at supervisor level
- Quote-validation guardrail in output assembler
- Prompt sanitation for generated images
- Session cookie stored as HTTP-only

## 8. Configuration

Environment variables:
- `OPENROUTER_API_KEY`
- `API_BIBLE_KEY`
- `DEFAULT_BIBLE_ID` (default: `de4e12af7f28f599-02`)

## 9. Design Trade-offs

- Strong grounding and safety are prioritized over broad open-domain scope.
- External APIs provide quality capability but introduce network dependency risk.
- Ephemeral ChromaDB keeps deployment simple, but requires reseeding each startup.
