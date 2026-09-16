# V0.9-J：Independent Recompute Expansion & Evidence Lineage

## 1. Goal

V0.9-J extends V0.9-I independent recomputation and establishes a deterministic Evidence Lineage graph. The purpose is to make numerical conclusions traceable from source evidence through computation and verification.

## 2. Core chain

`Raw Input → DataProfile → ModelSpec → RunManifest → ResultBundle → Independent Recompute → VerificationReport → PaperEvidence`

Figures are attached to this chain only when their data reference is explicitly available.

## 3. Independent recomputation coverage

Current adapters:

- regression: MAE, RMSE, R²
- classification: Accuracy
- optimization: objective-value consistency when independently evaluable evidence is present
- shortest path: path-edge weight sum vs reported distance
- Monte Carlo: sample mean and 95% interval when raw samples and interval evidence are present
- sensitivity: aligned finite perturbation/response evidence checks

Unsupported families remain `NOT_RUN`.

## 4. Evidence Lineage

`EvidenceLineage` is a graph artifact with typed nodes and typed edges.

Node kinds:

`input | data | model | run | result | verification | paper_evidence | figure`

Relations:

`derived_from | computed_by | verified_by | visualized_as | cited_by`

The lineage builder only records relationships supported by explicit references. It must not invent a data source, model dependency, figure origin, or paper citation.

## 5. Gate semantics

Independent recomputation participates in the same Verification Gate:

- recomputation mismatch → `FAIL`
- invalid raw evidence → `FAIL`
- missing raw evidence → `NOT_RUN`
- verified comparison → `PASS`

A model cannot obtain a PASS merely because it reports a plausible number.

## 6. Boundary

V0.9-J does not yet provide automatic PaperEvidence generation or full figure lineage. Those are subsequent stages. It also does not claim that all mathematical model families are independently recomputed.

## 7. Next

V0.9-K should formalize `PaperEvidence` as a first-class artifact and enforce that every key numerical claim, table cell, and figure data series has a valid lineage path ending in a verified ResultBundle.
