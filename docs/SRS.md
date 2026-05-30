# Software Requirements Specification (SRS)

## 1. Introduction

### 1.1 Purpose
This document defines functional and non-functional requirements for the Christianity-focused AI assistant. The system provides safe, grounded theological responses, scripture retrieval, and Christian-themed image generation.

### 1.2 Scope
The product is a web-based assistant that:
- Answers Christian theology questions
- Retrieves scripture deterministically from API.Bible
- Rejects adversarial or out-of-scope requests
- Generates Christian-themed images with safety filtering
- Persists conversation sessions and supports session history

### 1.3 Intended Users
- Christians seeking scriptural guidance
- Users exploring Christian theology
- Developers/operators maintaining the system

### 1.4 Definitions
- **Supervisor**: Node that classifies intent and routes requests
- **Verse Finder**: Node that retrieves Bible content via API.Bible/ChromaDB
- **Output Assembler**: Node that composes final response with quote guardrail
- **Guardrail**: Validator ensuring quoted text matches retrieved scripture

## 2. Overall Description

### 2.1 Product Perspective
The application is a FastAPI server with a LangGraph multi-agent backend and Bootstrap/Jinja UI.

### 2.2 User Needs
- Accurate scripture references without hallucinated text
- Pastoral, understandable answers
- Safe handling of harmful or manipulative prompts
- Lightweight chat experience with session continuity

### 2.3 Constraints
- Requires valid `OPENROUTER_API_KEY` and `API_BIBLE_KEY`
- Depends on external APIs (OpenRouter, API.Bible, DuckDuckGo search)
- Python 3.13+ runtime

## 3. Functional Requirements

### FR-1 Conversation Handling
The system shall accept user messages from the web UI and return AI responses.

### FR-2 Intent Routing
The system shall classify user intent into `qa`, `image`, `web_search`, `adversarial`, or `out_of_scope`.

### FR-3 Adversarial Rejection
The system shall reject requests that manipulate scripture or promote violence/hate.

### FR-4 Scope Enforcement
The system shall reject non-Christian or unrelated secular requests.

### FR-5 Deterministic Scripture Retrieval
The system shall retrieve verse content from API.Bible instead of generating verse text from model memory.

### FR-6 Reference Parsing
The system shall parse explicit verse references (e.g., John 3:16) and detect invalid references.

### FR-7 Topic Search
The system shall support semantic topic-to-verse retrieval via ChromaDB and fallback keyword search.

### FR-8 Not-Found Handling
If a verse cannot be found, the system shall return a clear corrective message.

### FR-9 Output Guardrail
The system shall validate quoted verse text against retrieved payload and redact unverifiable text after retry limits.

### FR-10 Denomination Context
The system shall track denomination context (`general`, `catholic`, `protestant`, `orthodox`) in session state.

### FR-11 Controversial Topic Formatting
For controversial topics, the system shall structure responses with denomination perspectives where relevant.

### FR-12 Christian Image Generation
The system shall sanitize image prompts and generate Christian-themed images using configured image model.

### FR-13 Session Persistence
The system shall persist multi-turn state using SQLite checkpoints.

### FR-14 Session Management APIs
The system shall provide endpoints to reset session, list sessions, and fetch chat history.

## 4. External Interface Requirements

### 4.1 User Interface
- Browser UI served at `/`
- Message input, chat history display, session sidebar, image rendering

### 4.2 API Interface
- `POST /chat`
- `POST /reset`
- `GET /sessions`
- `GET /chat/history`
- `POST /session/{session_id}`

### 4.3 Software Interfaces
- OpenRouter chat completions API
- API.Bible REST endpoints
- DuckDuckGo search via `ddgs`
- ChromaDB EphemeralClient

## 5. Non-Functional Requirements

### NFR-1 Accuracy and Trust
Scripture quotations must be source-grounded and validated.

### NFR-2 Safety
Unsafe/adversarial requests must be blocked.

### NFR-3 Availability
If dependencies fail, system shall return graceful error messages.

### NFR-4 Maintainability
Prompt logic, graph wiring, tools, and validators shall remain modular.

### NFR-5 Observability
System shall log startup, routing decisions, retrieval counts, and major failures.

### NFR-6 Performance
Typical request path should remain responsive for interactive chat usage; external API latency is expected.

## 6. Assumptions and Dependencies

- API keys are provisioned securely in environment variables.
- Internet connectivity is available to required APIs.
- Default Bible ID points to a valid translation in API.Bible.

## 7. Risks

- Upstream API outages or rate limits
- Prompt-classification errors causing misrouting
- Incomplete web results for time-sensitive queries

## 8. Acceptance Criteria

- User can chat via UI and receive responses.
- Explicit verse requests return grounded references or clear not-found response.
- Adversarial prompts are rejected.
- Image requests return image payload when provider succeeds.
- Session listing/history/reset work from UI.
