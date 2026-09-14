# Artifact-Driven Stage Gates

The workflow does not advance merely because a stage produced text. It advances when its required Artifact Contracts are valid and its evidence requirements are satisfied.

| Gate | Required artifact | Minimum checks |
|---|---|---|
| Analysis Gate | ProblemMap | tasks mapped; inputs/outputs identified; assumptions/open questions recorded |
| Data Gate | DataProfile | assets profiled; quality risks recorded; gate decision is not FAIL |
| Model Gate | ModelPlan + ModelSpec | candidate rationale; assumptions; equations; constraints; validation plan |
| Compute Gate | RunManifest + ResultBundle | input/model/code provenance; run identity; outputs recorded |
| Verification Gate | VerificationReport | checks executed or explicitly marked NOT_RUN; critical failures absent |
| Writing Gate | PaperEvidence | material claims have evidence references |
| Final Gate | all above | end-to-end lineage is complete and no blocking gate remains |

## Blocking rules

A gate must fail when:

- a required artifact is missing;
- the artifact violates its schema;
- a required upstream reference cannot be resolved;
- a material result has no input/model/code provenance;
- a model choice has no documented rationale when alternatives are plausible;
- a required comparison or validation is claimed but evidence is absent;
- a critical verification check is `FAIL`;
- a paper claim has no supporting evidence reference.

Warnings may be carried forward only when explicitly recorded and judged non-blocking.

## Validation levels

The gate system should distinguish:

- **schema validity**: structure and field-level constraints;
- **semantic validity**: content is internally coherent;
- **lineage validity**: references point to real upstream artifacts;
- **evidence validity**: claims and model choices have supporting evidence;
- **reproducibility validity**: a run can be reconstructed from recorded inputs/configuration/code.

The current implementation begins with schema-level smoke tests. Semantic, lineage, and reproducibility validators are subsequent layers and must not be falsely reported as complete.
