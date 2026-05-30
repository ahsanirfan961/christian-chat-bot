# API Reference

Base URL: `http://localhost:8000`

## `GET /`
Serves chat UI HTML.

## `POST /chat`
Invokes the LangGraph workflow for a user message.

### Form Fields
- `message` (required, string)

### Success Response (`200`)
```json
{
  "response": "string",
  "image_url": "string",
  "denomination": "general|catholic|protestant|orthodox"
}
```

### Error Responses
- `503`: `{"error": "Server not ready"}`
- `500`: `{"error": "An error occurred: ..."}`

## `POST /reset`
Resets current user session.

### Success Response (`200`)
```json
{
  "status": "ok",
  "session_id": "uuid"
}
```

## `GET /sessions`
Returns available non-eval sessions from checkpoints.

### Success Response (`200`)
```json
{
  "sessions": [
    {"id": "thread-id", "title": "first message preview"}
  ]
}
```

## `GET /chat/history`
Returns message history for current session cookie.

### Success Response (`200`)
```json
{
  "messages": [
    {"role": "user|ai", "content": "...", "image_url": "optional"}
  ],
  "denomination": "general|catholic|protestant|orthodox"
}
```

## `POST /session/{session_id}`
Switches the active session cookie to an existing thread.

### Success Response (`200`)
```json
{
  "status": "ok",
  "session_id": "thread-id"
}
```
