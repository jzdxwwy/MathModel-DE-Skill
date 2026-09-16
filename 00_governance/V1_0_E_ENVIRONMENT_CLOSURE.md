# V1.0-E Environment Closure / Clean-Room Rebuild

## 1. Purpose

V1.0-E extends V1.0-D from controlled rebuild to **environment-closed rebuild evidence**. A reproducibility claim must distinguish:

1. the recorded environment is complete;
2. the rebuild environment matches the recorded environment;
3. an actual isolated clean-room execution was performed.

Metadata alone proves neither isolation nor execution.

## 2. Closure contents

`EnvironmentClosure` records Python implementation/version, OS and architecture, declared package versions, registered tool code references/hashes, source-file hashes, complete input hashes, model/spec references, and execution policy. A deterministic SHA256 fingerprint is computed over canonical JSON excluding the fingerprint field itself.

## 3. Gate semantics

- missing reference closure → `NOT_RUN`
- incomplete closure → `NOT_RUN`
- self-inconsistent fingerprint → `FAIL`
- missing rebuild closure → `NOT_RUN`
- explicit environment mismatch → `FAIL`
- complete matching closures → `PASS`

`NOT_RUN` never becomes `PASS`.

## 4. Clean-room boundary

The environment module does not launch Docker, Conda, venv, shell, or arbitrary commands. A trusted Host/EnvironmentAdapter may later materialize an isolated environment and capture a `REBUILD_OBSERVED` closure. V1.0-E therefore supplies the evidence contract without pretending that GitHub source metadata is execution evidence.

## 5. Final Submission Gate

V1.0-E adds `F8_ENVIRONMENT_CLOSURE` to the Final Submission Gate and requires it by default. The gate still relies on V1.0-C for numerical reproducibility comparison.

## 6. Immutability

The reference ResultBundle and reference EnvironmentClosure are evidence artifacts. A rebuild must use a fresh run directory and may not edit the frozen reference to make the environment gate pass.

## 7. Future extension

A future EnvironmentAdapter may provide container image digests, lockfiles, OS image hashes, dependency closure, clean-room execution logs, and network/shell isolation evidence. Those stronger claims must be represented explicitly rather than inferred from this schema.
