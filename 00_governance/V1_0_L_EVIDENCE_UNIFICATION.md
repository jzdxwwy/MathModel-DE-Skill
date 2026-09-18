# V1.0-L Evidence Unification + Reproducibility Closure

## Goal
K created a valid venv execution path, but its evidence was parallel to the older G/H/C paths. L establishes one canonical execution evidence record and connects the K ResultBundle to the existing deterministic reproducibility comparison.

## Canonical chain
K ResultBundle + K Execution Log + K/G/H evidence
-> UnifiedExecutionEvidence
-> EvidenceUnificationGate
-> V1.0-C compare_result_bundles
-> ReproducibilityClosureReport.

## Rules
1. L does not execute code.
2. L does not recompute model outputs.
3. L does not edit ResultBundle.
4. Hashes are recomputed from actual files.
5. Source evidence is preserved and referenced.
6. Reproducibility uses V1.0-C tolerances: atol=1e-8, rtol=1e-6.
7. PASS means supplied reference and rebuild ResultBundles match under the declared comparison contract; it does not prove hidden infrastructure equivalence.

## Canonicalization
UnifiedExecutionEvidence is the presentation-independent canonical record. G/H/K evidence remains raw historical evidence, while downstream logic should consume the unified record.

## Security
No shell, network, package installation, model-generated code, or arbitrary import is introduced by L.

## Next
V1.0-M should standardize run-directory topology and make UnifiedExecutionEvidence the single execution evidence reference for PaperEvidence, SubmissionManifest and Final Submission Gate.
