# Operations Runbook

## 1. Startup Checks

- Confirm `.env` values are set
- Confirm dependencies installed
- Start server and check logs for:
  - ChromaDB initialized
  - SqliteSaver ready
  - LangGraph compiled

## 2. Health Verification

- Open `/` and send a normal theology prompt
- Send explicit verse prompt (e.g., `John 3:16`)
- Send adversarial rewrite prompt and verify rejection
- Send image request and verify image/fallback behavior

## 3. Common Failures

### Missing dependencies
Symptom: Import/module errors on startup or tests.
Action: Run `uv sync`.

### Missing API keys
Symptom: API call failures, empty/fallback responses.
Action: Validate `.env` keys and provider quotas.

### API.Bible unavailable
Symptom: verse retrieval fails, not-found/fallback responses increase.
Action: inspect network/API status, retry later.

### OpenRouter unavailable
Symptom: chat or image generation exceptions.
Action: inspect provider status and token limits.

## 4. Logs to Monitor

- Supervisor intent decisions
- Verse retrieval counts and not-found warnings
- Guardrail failures/retries
- Image generation success/failure
- Session listing/history exceptions

## 5. Data Management

- Runtime session DB: `checkpoints.db`
- Evaluation DB: `eval_checkpoints.db` (temporary)
- Regular backup strategy is recommended for long-lived deployments
