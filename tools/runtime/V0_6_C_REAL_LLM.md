# V0.6-C Real LLM Host

## Purpose

V0.6-C replaces the deterministic model callback with a real LLM invocation while keeping the Runtime contract unchanged.

```text
CLI / external host
        ↓ HostRequest
RealLLMHostAdapter
        ↓ ModelAdapter
OpenAI-compatible HTTP endpoint
        ↓ ModelResponse
RuntimeOrchestrator
        ↓
TaskContext + stage artifacts
```

## Configuration

Set environment variables; never commit credentials:

```text
MATHMODEL_LLM_PROVIDER=openai-compatible
MATHMODEL_LLM_BASE_URL=https://<provider>/v1
MATHMODEL_LLM_API_KEY=<secret>
MATHMODEL_LLM_MODEL=<model-name>
MATHMODEL_LLM_TIMEOUT=120
```

`MATHMODEL_LLM_BASE_URL` may also point directly to `/chat/completions`.

## Run

```bash
python -m tools.runtime.entrypoint \
  --host real \
  --problem problem.pdf \
  --attachments ./attachments \
  --out final_output
```

The default `--host demo` remains offline and deterministic.

## Current scope

V0.6-C proves the real model boundary and persists stage model outputs. It currently executes the first three runtime stages: `00-start`, `01-analysis`, and `02-data`.

It does **not** yet claim full CUMCM problem solving. Tool dispatch, structured artifact generation, real computation, verification, and paper generation remain later stages.

## Security / reproducibility

- API keys are read only from environment variables.
- Diagnostic configuration output reports only whether a key is configured.
- No credentials are written to task manifests.
- Tests should mock HTTP; no network call is required for the test suite.
