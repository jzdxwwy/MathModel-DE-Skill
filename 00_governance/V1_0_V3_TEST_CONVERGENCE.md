# V1.0-V3 Test Convergence

## Purpose

V1.0-V3 does not add another evidence gate. It converts the V1.0-V2 publication-core fixture into an executable regression baseline and closes defects revealed by real test execution.

## Test layers

1. Integration tests: canonical run topology and Final Submission Gate.
2. Verification tests: individual evidence/gate contracts.
3. Full regression: all pytest tests in the repository.
4. Mutation regression: intentionally modify a canonical artifact and require a blocking FAIL.

## Required mutation cases

- ResultBundle output value
- UnifiedExecutionEvidence result_bundle_hash
- PaperEvidence structured observation
- PresentationDataManifest declared value
- ModelSpec model_id
- PaperManifest reference
- SubmissionManifest SHA256

A mutation must not be repaired by changing the reference ResultBundle or selecting another evidence source.

## CI boundary

GitHub Actions is the repository execution path for V1.0-V3. If the connector cannot observe a workflow run, that is an execution-observability limitation; it must not be reported as a passing test.

## Release rule

No statement that the V1.0-V3 suite passes is allowed until an actual pytest/CI result is observed. Static inspection and test-file creation are not test execution.

## Exit criteria

V1.0-V3 closes when:

- integration tests execute successfully;
- verification regression tests execute successfully;
- mutation cases fail as intended;
- fixture artifacts validate against their declared schemas where schemas exist;
- no newly introduced test relies on fabricated external execution evidence;
- remaining NOT_RUN states are explicitly attributable to unavailable trusted-host/clean-room execution.

V1.0-V4 may then begin D/E benchmark integration.

## V3.3 Schema/Runtime/Mutation Convergence

V3.3 focuses on three-way contract convergence:

1. Schema contract — canonical source artifacts and generated evidence are validated against their JSON Schemas.
2. Runtime contract — Final Submission Gate output shape is validated in memory against final-submission-gate.schema.json.
3. Mutation contract — intentional mutations must fail at the gate that owns the affected evidence.

Current mutation coverage includes:
- ResultBundle output value → F22
- UnifiedExecutionEvidence result hash → F22
- PresentationDataManifest value → F23
- ModelSpec model identity → F21
- PaperEvidence numeric observation → F20
- PaperManifest claim reference → F23
- removal of canonical UnifiedExecutionEvidence → F22
- SubmissionManifest artifact SHA256 → F6

CI now runs integration tests, verification tests, and the full pytest regression suite.

Important: adding these tests does not mean they have passed. A release claim requires an observed CI/test result.
