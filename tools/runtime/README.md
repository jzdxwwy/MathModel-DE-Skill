# Model-Executable Runtime · V0.6

V0.6 turns MathModel-DE-Skill from a workflow definition into a provider-neutral runtime contract that a host large model can execute.

## Components

- `model_adapter.py` — model/provider boundary.
- `skill_loader.py` — loads Master Skill and Stage Skills.
- `task_context.py` — persistent task state, artifacts and stage status.
- `tool_registry.py` — executable tool discovery/invocation contract.
- `orchestrator.py` — stage execution, model request, artifact bridge and Gate.
- `execution_protocol.md` — host integration rules.
- `demo_runtime.py` — minimal executable demonstration with a fake model.

## Execution model

```text
Host Model
   ↓
ModelAdapter
   ↓
RuntimeOrchestrator
   ├── SkillLoader
   ├── ToolRegistry
   ├── TaskContext
   └── Stage + Gate
          ↓
      Artifacts
```

The model can reason and request actions, but filesystem artifacts accepted by the runtime and Gates remain authoritative.

## Host integration

A compatible host only needs to implement `ModelAdapter.invoke(request)` and provide stage definitions. No vendor SDK is required by the runtime itself.

## Current limitation

This is V0.6 plumbing. The next production step is to connect the runtime to real input ingestion and real Stage implementations so a CUMCM problem statement and attachment directory can become `ProblemSpec` and `DataProfile` automatically.
