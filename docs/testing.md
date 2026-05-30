# Testing Guide

## 1. Current Test Approach

The project currently uses an evaluation-style automated runner instead of unit/integration suites.

- Runner: `eval/test_runner.py`
- Dataset: `eval/eval_dataset.json`
- Cases: 10 representative scenarios (QA, explicit citation, fake verse, adversarial, image, denomination, memory)

## 2. Test Command

Recommended command from project root:

```bash
uv run python eval/test_runner.py
```

Fallback when `uv` is unavailable (only if dependencies are installed in current Python environment):

```bash
python eval/test_runner.py
```

## 3. Prerequisites

Before running tests:
- Install dependencies (`uv sync`)
- Configure `.env` from `.env.example`
- Ensure valid keys for OpenRouter and API.Bible

## 4. What the Runner Verifies

For each test case, the runner checks:
- Required substrings present in final response
- Forbidden substrings absent
- Image URL exists when expected
- Rejection indicators appear for adversarial cases
- Multi-turn behavior works where follow-up query exists

## 5. Result Interpretation

Runner outputs:
- PASS/FAIL per case
- Failure reasons for each failed assertion
- Final summary (`passed/total`)

A passing run indicates end-to-end behavior is aligned with expected scenarios under current external API responses.

## 6. Known Limitations

- Results can vary due to LLM non-determinism and provider changes
- Requires live external APIs and network access
- No isolated unit tests for parsing, validation, or routing logic
- No CI matrix/lint/type-checking suite currently defined in project files

## 7. Recommended Future Expansion

- Add unit tests for:
  - `parse_verse_reference`
  - `validate_scripture_quotes`
  - Supervisor routing edge cases
- Add integration tests with mocked API.Bible/OpenRouter responses
- Add smoke tests for FastAPI endpoints
- Add CI workflow with deterministic checks and report artifacts
