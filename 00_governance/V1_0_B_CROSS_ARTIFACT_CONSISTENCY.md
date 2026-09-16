# V1.0-B Cross-Artifact Consistency Gate

## 1. Purpose

V1.0-B closes the gap between separately valid artifacts. A ResultBundle,
PaperEvidence, PresentationDataManifest, RenderManifest and SubmissionManifest
may each look valid while referring to different claims, figures, runs or
files. V1.0-B checks that these artifacts form one coherent evidence chain.

## 2. Required closure

```text
PaperManifest
   ↓ claim_refs
PaperEvidence
   ↓ figure/table/equation refs
PresentationDataManifest
   ↓ result_ref
ResultBundle
   ↓
VerificationReport

PresentationDataManifest
   ↓ evidence_id
RenderManifest

SubmissionManifest
   ↓ paths + SHA256
actual delivery artifacts
```

## 3. Checks

- B01: every PaperManifest claim reference resolves to PaperEvidence.
- B02: every PaperEvidence claim is represented by PaperManifest.
- B03: figure/table/equation references resolve to PresentationDataManifest.
- B04: presentation bindings point to a VALIDATED/FROZEN ResultBundle.
- B05: presentation evidence closes into the RenderManifest.
- B06: PaperManifest presentation references resolve to presentation evidence.
- B07: SubmissionManifest artifact paths exist and their SHA256 values match.
- B08: run_id is consistent across run artifacts.

## 4. Decision

- Any FAIL → `FAIL`.
- No FAIL but any `NOT_RUN` → `NOT_RUN`.
- All checks PASS → `PASS`.

## 5. Non-goals

V1.0-B does not inspect PDF/Word pixels, perform OCR, prove full symbolic
equivalence, recompute numerical results, or infer missing references. It is
a closure gate, not a replacement for domain verification or V1.0-C
reproducibility execution.

## 6. Final Submission Gate integration

`tools/verification/final_submission_gate.py` invokes V1.0-B as `F6_CROSS_ARTIFACT`
by default. Therefore a final PASS now requires cross-artifact closure in
addition to the earlier V1.0 checks.
