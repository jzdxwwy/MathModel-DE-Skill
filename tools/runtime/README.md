# Model-Executable Runtime · V0.6-C

V0.6-C turns the V0.6 provider-neutral runtime contract into an executable real-LLM boundary while preserving the separation between host, model adapter, workflow orchestration, tools and artifacts.

## Components

- `model_adapter.py` — provider-neutral model contract.
- `llm_config.py` — environment-only provider configuration; never stores secrets.
- `providers/openai_compatible.py` — standard-library HTTP adapter for OpenAI-compatible chat-completions endpoints.
- `host_adapter.py` — normalized external host request/response contract.
- `real_host.py` — real LLM host that connects the provider adapter to the Runtime.
- `skill_loader.py` — loads Master Skill and Stage Skills.
- `task_context.py` — persistent task state, artifacts and stage status.
- `tool_registry.py` — executable tool discovery/invocation contract.
- `orchestrator.py` — stage execution, model request, model-output persistence and Gate.
- `entrypoint.py` — CLI with `--host demo|real`.
- `V0_6_C_REAL_LLM.md` — configuration and usage.

## Execution model

```text
CLI / external host
       ↓ HostRequest
RealLLMHostAdapter
       ↓ ModelAdapter
OpenAI-compatible endpoint
       ↓ ModelResponse
RuntimeOrchestrator
       ├── SkillLoader
       ├── ToolRegistry
       ├── TaskContext
       └── Stage + Gate
              ↓
        verified filesystem artifacts
```

The LLM may reason and return structured output, but filesystem artifacts accepted by the runtime and Gates remain authoritative. Stage model outputs are persisted into the task context so later stages can trace what the model actually returned.

## Configuration

```text
MATHMODEL_LLM_PROVIDER=openai-compatible
MATHMODEL_LLM_BASE_URL=https://<provider>/v1
MATHMODEL_LLM_API_KEY=<secret>
MATHMODEL_LLM_MODEL=<model-name>
MATHMODEL_LLM_TIMEOUT=120
```

Run:

```bash
python -m tools.runtime.entrypoint --host real --problem problem.pdf --attachments ./attachments --out final_output
```

The default `--host demo` remains deterministic and offline.

## Current limitation

V0.6-C proves real model invocation and output persistence for the first three runtime stages. It does **not** yet claim full CUMCM automation. Real attachment ingestion, structured artifact synthesis, tool dispatch, numerical computation, verification, and paper generation are subsequent production stages.
