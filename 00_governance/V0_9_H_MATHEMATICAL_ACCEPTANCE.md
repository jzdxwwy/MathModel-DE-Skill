# V0.9-H Mathematical Acceptance

## 1. Goal

V0.9-H upgrades V0.9-G from evidence-presence verification to schema-oriented mathematical acceptance.

Pipeline:

```text
ModelSpec + DataProfile + ResultBundle + Rule Registry
                ↓
      Mathematical Acceptance Rules
                ↓
          Rule Evaluator
                ↓
       VerificationReport
                ↓
              Gate
```

## 2. Core principles

1. Evidence-first: missing evidence is `NOT_RUN`, never silently treated as PASS.
2. Fail-closed: explicit mathematical contradictions or invalid ranges produce `FAIL`.
3. Traceability: checks refer to metrics, outputs, bindings, or artifacts actually present in the run.
4. Non-invasive: verification never changes numerical results.
5. Schema-oriented: acceptance checks have stable IDs/categories and can be extended without rewriting the orchestration layer.

## 3. Current acceptance families

- Regression: finite metrics, R² range, validation/CV binding, leakage-check binding.
- Classification: finite/range-valid accuracy and F1, CV binding, class-distribution evidence.
- Time series: chronological split, future-leakage check, forecast horizon.
- Optimization: feasibility, finite objective, explicit constraints, optimality evidence.
- Network: path continuity evidence, finite distance, edge legality, weight consistency.
- Stochastic: repetition count, confidence interval evidence, explicit random seed.

## 4. Acceptance semantics

`PASS` means the supplied evidence satisfies the registered check.
`NOT_RUN` means the system does not have sufficient evidence to decide.
`FAIL` means supplied evidence contradicts a mathematical invariant or required acceptance condition.

The final gate is:

- any `FAIL` → `FAIL`
- otherwise any `NOT_RUN`/`WARN` → `PASS_WITH_WARNINGS`
- otherwise → `PASS`

## 5. Boundary

V0.9-H is not a symbolic theorem prover. It validates explicit numerical invariants and evidence contracts. Deeper proof obligations, automatic recomputation from raw data, figure-to-number reconciliation, and paper-number lineage are future extensions.

## 6. Next stage

V0.9-I should focus on evidence materialization and independent recomputation: derive acceptance evidence directly from ResultBundle/data artifacts where safe, rather than relying only on binding metadata.
