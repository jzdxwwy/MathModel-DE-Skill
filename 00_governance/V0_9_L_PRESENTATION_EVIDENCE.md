# V0.9-L — Figure / Table / Equation Evidence Binding

## Goal
Prevent figures, tables and equations in the final paper from becoming detached from the verified numerical result.

## Contract
Every publishable presentation object must explicitly bind:

`source_refs → result_refs → verification_refs → lineage_refs`

The binding is explicit. The system must not infer a missing source, result or verification relationship from filenames, captions or model names.

## Presentation objects
- Figure: plotted visual derived from verified result data.
- Table: reported numerical/structured values derived from verified result data.
- Equation: model/formula representation tied to the accepted ModelSpec and its evidence chain.

## Gate
`PASS` requires:
1. VerificationReport gate is `PASS`.
2. ResultBundle is `VALIDATED` or `FROZEN`.
3. Every presentation object has source, result, verification and lineage references.
4. Every lineage reference resolves to an existing lineage node/reference.

Any missing or unresolved binding is `FAIL`.

## Important boundary
V0.9-L verifies provenance and binding consistency. It does not yet compare pixels, OCR every table cell, or symbolically prove that a rendered equation is algebraically equivalent to ModelSpec. Those capabilities belong to later versions.

## Next
V0.9-M will strengthen rendered-artifact consistency: table values vs ResultBundle, figure data manifests vs ResultBundle, and equation references vs ModelSpec.
