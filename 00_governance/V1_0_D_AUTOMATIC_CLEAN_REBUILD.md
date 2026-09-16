# V1.0-D Automatic Clean Rebuild

## Goal
V1.0-D turns V1.0-C's manually supplied `rebuild_dir` into a controlled runtime capability: freeze a rebuild contract, verify inputs, execute only an approved registered tool, create a fresh rebuild run, and hand the resulting ResultBundle to V1.0-C.

## Contract
`artifacts/schemas/rebuild-contract.schema.json` records:
- reference `run_id`
- `model_id`
- registered `tool`
- exact input paths and SHA256 hashes
- parameters
- environment fingerprint
- expected ResultBundle identity
- explicit no-network/no-shell policy

The contract is evidence, not a license to invent missing inputs or commands.

## Execution boundary
`tools/runtime/rebuild_engine.py` is fail-closed:
1. validate contract identity and schema version;
2. reject arbitrary shell execution;
3. require the named tool to exist in `ToolRegistry`;
4. recompute every declared input SHA256 before execution;
5. create a new `rebuild-*` run directory;
6. invoke only the registered tool with the verified contract;
7. write a new ResultBundle and RebuildRunManifest;
8. never mutate the frozen/reference ResultBundle.

The engine does **not** execute arbitrary repository scripts, accept free-form shell commands, or silently repair a failed contract.

## Relationship to V1.0-C
V1.0-D produces the rebuild evidence consumed by V1.0-C. V1.0-C remains authoritative for numerical reproducibility comparison. A clean rebuild is not considered successful merely because the tool ran; its ResultBundle must still pass the V1.0-C comparison.

## Current limitation
The GitHub repository stores the contract and runtime implementation; actual Python execution requires a trusted host/runtime that supplies the existing ToolRegistry. Repository writes alone do not constitute a real rebuild execution.

## Acceptance
A future host integration should produce:
`Frozen Run → RebuildContract → hash verification → isolated rebuild run → ResultBundle → V1.0-C Reproducibility Gate → Cross-Artifact Consistency → Final Submission Gate`.

No evidence may be fabricated to convert `NOT_RUN` into `PASS`.
