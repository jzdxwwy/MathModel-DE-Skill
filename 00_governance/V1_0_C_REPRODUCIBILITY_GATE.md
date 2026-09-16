# V1.0-C Reproducibility Gate

## 1. Purpose

V1.0-C verifies that a frozen modeling result can be independently rebuilt from the recorded evidence contract. It moves the Skill from traceability to reproducibility.

## 2. Core chain

`Frozen ResultBundle → Rebuild Contract → Independent Rebuild → Rebuilt ResultBundle → Deterministic Comparison → Reproducibility Gate`

## 3. Rules

1. No rebuild evidence means `NOT_RUN`.
2. A supplied rebuild directory without a ResultBundle is `FAIL`.
3. The original ResultBundle is immutable and is never overwritten by the rebuild.
4. Model identity, output names, output values, units and metrics are compared deterministically.
5. Numeric comparison uses explicit `atol` and `rtol`; defaults are `1e-8` and `1e-6`.
6. Missing or changed required source artifacts fail the source-hash check.
7. A PASS means the supplied independent rebuild matches the frozen result under the declared contract; it does not claim that arbitrary hidden code or an external environment is reproducible.
8. No LLM judgment can convert `NOT_RUN` into `PASS`.

## 4. Current scope

V1.0-C supplies a deterministic evidence gate and comparison engine. It does not execute arbitrary project code itself. An execution host must explicitly produce the rebuild run directory.

## 5. Future extension

Later releases may add containerized environment capture, dependency lock verification, clean-room rebuild, dataset hash closure and full command replay. These are separate checks and must remain evidence-first.
