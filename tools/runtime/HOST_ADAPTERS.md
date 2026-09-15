# V0.6-B Host Adapter + Executable Entry Point

## Purpose

V0.6-B defines the boundary between an external LLM host and MathModel-DE-Skill Runtime.
The host supplies a normalized `HostRequest`; the Runtime owns task context, Skill loading,
stage execution, artifact state and workflow completion.

## CLI entry point

From the repository root:

```bash
python -m tools.runtime.run --problem problem.pdf --attachments ./attachments --out final_output
```

A deterministic demo host is used by default. It does **not** solve the supplied problem;
it proves that the host/runtime boundary and task lifecycle are executable.

## Host integration contract

A real host should implement:

```python
class HostAdapter:
    def run(self, request: HostRequest) -> HostResponse:
        ...
```

The host is responsible for translating its provider-specific model interface into the
provider-neutral runtime contract. Provider SDKs must not leak into the Workflow Engine,
Artifact Contracts, or Stage Skills.

## Model integration contract

Inside the host/runtime boundary, `ModelAdapter.invoke(ModelRequest)` is the model-level
contract. The model receives:

- task id
- current stage
- stage instruction
- problem input
- known artifacts
- stage status
- loaded Skill bundle
- registered tool descriptions

The model response is advisory. Runtime stages remain authoritative for filesystem
artifacts and Gates.

## Intended next integration

1. Add a provider-specific adapter outside the core Runtime.
2. Replace demo model callbacks with a real LLM invocation.
3. Connect Stage executors to real problem/attachment ingestion.
4. Preserve Artifact Contracts and Gate semantics unchanged.
