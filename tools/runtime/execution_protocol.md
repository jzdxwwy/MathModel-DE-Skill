# V0.6 Model-Executable Runtime Protocol

## Purpose

This protocol defines the boundary between a host large model and MathModel-DE-Skill.
It is provider-neutral: Claude Code, Codex, API-based GPT clients, local models, or another harness may implement the `ModelAdapter` contract.

## Runtime responsibilities

1. Load `SKILL.md` and the requested Stage Skill.
2. Create and persist `TaskContext`.
3. Expose available tools through `ToolRegistry`.
4. Ask the model to reason/plan for the current stage.
5. Execute the authoritative stage bridge that creates real artifacts.
6. Run the stage Gate.
7. Persist status and provenance.
8. Continue or stop according to Gate status.

## Model responsibilities

The model is responsible for interpretation, planning, model selection, explanation, and requesting appropriate tools. It must not claim that a file, numerical result, figure, validation result, or paper section exists unless the runtime has materialized and registered the corresponding artifact.

## Artifact rule

Natural-language model output is advisory. Files registered in `TaskContext` and accepted by Gates are authoritative.

## Failure rule

A model failure, missing artifact, failed Gate, or tool error blocks downstream stages. The runtime must not silently convert a failure into PASS.

## Minimal host integration

Implement:

```python
class MyModelAdapter:
    def invoke(self, request):
        # send request.instruction + request.context to your model
        # return ModelResponse(status="ok", output={...})
        ...
```

Then construct `RuntimeOrchestrator(repo_root, model_adapter, tool_registry)` and call `run()` with the stage definitions.

## V0.6 boundary

V0.6 establishes the execution protocol and runtime plumbing. It does not yet claim automatic parsing of every CUMCM attachment or automatic generation of a competition-ready paper. Those capabilities belong to later versions.
