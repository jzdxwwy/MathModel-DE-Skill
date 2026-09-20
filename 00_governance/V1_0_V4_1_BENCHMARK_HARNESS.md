# V1.0-V4.1 Benchmark Harness

## Purpose

V4.1 begins benchmark integration without solving the historical problem. The
harness validates whether required historical attachments are actually
available and records SHA256 for present inputs.

The existing 2024E benchmark specification explicitly requires the original
historical attachments for formal execution and forbids replacing missing data
with guessed data.

## Scope

V4.1 adds:
- BenchmarkInputManifest;
- BenchmarkRun readiness artifact;
- deterministic SHA256 capture for present files;
- fail-closed blocking when required attachments are missing;
- synthetic smoke tests for the harness.

It does not:
- hard-code 2024E field names into generic Skill modules;
- import a historical answer;
- invent missing data;
- execute Q1-Q4;
- claim benchmark completion.

## Acceptance

A benchmark is READY only when every required attachment is present and
hashable.

Missing required inputs produce:
- BenchmarkRun.status = BLOCKED;
- B01_INPUT_READINESS = BLOCKED;
- gate_decision = NOT_RUN.

This is intentional: missing data is an input-readiness condition, not a model
result.

## Next

V4.2 will connect the real 2024E attachments to the generic ingestion/DataProfile
pipeline. No question-specific column names should be added to generic runtime
components.
