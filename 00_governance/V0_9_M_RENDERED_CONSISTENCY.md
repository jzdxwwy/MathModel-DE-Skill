# V0.9-M Rendered Artifact Consistency

## Goal

Turn the V0.9-L presentation evidence binding into a deterministic consistency gate.

```text
ResultBundle / ModelSpec
        ↓
PresentationDataManifest
        ↓
Rendered Consistency Verifier
        ↓
PresentationConsistencyReport
        ↓
Presentation Gate
```

## Rules

1. **Tables**: every material value declared in the presentation manifest must resolve to an authoritative ResultBundle output/metric and match within an explicit tolerance when a value is materialized.
2. **Figures**: plotted source bindings must resolve to ResultBundle evidence. The V0.9-M manifest is the authoritative pre-render data contract; pixel-level image inspection is out of scope.
3. **Equations**: equation references may bind to ModelSpec equation IDs. Normalized expression hashes can detect accidental text changes; this is not a symbolic-equivalence theorem prover.
4. **Missing or unresolved bindings** are failures for a claimed publishable presentation object.
5. The verifier never edits the ResultBundle to make a presentation pass.

## Deliberate scope boundary

V0.9-M validates deterministic source-data consistency before rendering. It does not perform OCR, pixel comparison, chart-image reverse engineering, or full symbolic equivalence checking.

## Testing status

Test fixtures were added, but pytest has not been executed in the current environment.
