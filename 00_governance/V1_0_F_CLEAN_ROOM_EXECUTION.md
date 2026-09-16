# V1.0-F Clean-Room Execution / Environment Adapter

## Goal
V1.0-F upgrades V1.0-E from environment closure metadata to an explicit execution-adapter boundary.

## Architecture
`EnvironmentClosure → EnvironmentAdapterContract → Trusted Host Adapter → Isolated Execution → Observed EnvironmentClosure → CleanRoomGate → ReproducibilityGate`

## Hard constraints
1. The Skill must not execute arbitrary shell commands from a model-generated contract.
2. An adapter describes a controlled execution capability; it does not imply that isolation actually occurred.
3. `HOST`, `VENV`, `CONDA`, `DOCKER`, `GITHUB_ACTIONS`, and `CUSTOM` are adapter kinds, not claims that the corresponding runtime is available.
4. A real clean-room PASS requires observed rebuild evidence from a trusted host/adapter.
5. Missing rebuild evidence is `NOT_RUN`; missing evidence must never become `PASS`.
6. Environment mismatch is `FAIL` and must identify the mismatched closure fields.
7. Reference/Frozen ResultBundle remains immutable.
8. Network and arbitrary shell execution remain disabled by default.

## Scope of this implementation
The repository now provides a safe declarative adapter protocol and a Clean-Room Evidence Gate. It intentionally does not pretend to create Docker/Conda/venv environments inside GitHub file operations.

## Future trusted-host implementation
A host may implement an adapter that materializes a dependency lock, creates an isolated environment, executes only registered tools, captures the observed environment, and returns the rebuild artifact. That host evidence can then be evaluated by the repository gates.
