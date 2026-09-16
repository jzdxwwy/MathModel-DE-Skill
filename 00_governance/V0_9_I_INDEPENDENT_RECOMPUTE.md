# V0.9-I：Independent Recompute & Evidence Materialization

## 1. Goal

V0.9-H checks mathematical invariants and evidence presence. V0.9-I adds an independent recomputation layer so reported numerical values are not trusted merely because they appear in a ResultBundle.

## 2. Core chain

`ResultBundle → Raw Evidence → Independent Recompute → Reported-vs-Recomputed Comparison → VerificationReport → Gate`

## 3. Evidence-first policy

- Raw evidence is required for independent recomputation.
- Missing raw evidence is `NOT_RUN`, never `PASS`.
- Length mismatch or non-finite raw values are `FAIL` when the requested recomputation is otherwise applicable.
- A mismatch between reported and independently recomputed values is `FAIL`.
- Recomputed values never overwrite the original ResultBundle.

## 4. V0.9-I adapters

### Regression

When `y_true` and `y_pred` are available, independently recompute:

- MAE
- RMSE
- R²

Compare against the corresponding ResultBundle metrics using explicit absolute/relative tolerances.

### Classification

When `y_true` and `y_pred` are available, independently recompute accuracy and compare it with the reported metric.

## 5. Traceability

The recomputation checks must retain the distinction between:

- reported value
- independently recomputed value
- tolerance
- decision

This allows later PaperEvidence to reference a verified numerical result instead of copying a number without provenance.

## 6. Boundary

V0.9-I does not yet independently recompute every model family. Unsupported model families remain `NOT_RUN` rather than being treated as verified.

## 7. Next

Extend independent recomputation to optimization objective/constraint values, shortest-path distance, Monte Carlo interval consistency, sensitivity perturbation response, and figure/result consistency. Then add regression fixtures and execute the test suite in a real runtime environment.
