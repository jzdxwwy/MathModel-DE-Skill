# V1.0-J Locked Dependency Materialization

## 1. Goal

V1.0-J advances V1.0-I from “fresh venv exists” to “the declared dependency environment is installed and independently inventoried”.

The intended chain is:

DependencyLockManifest → DependencyMaterializationContract → Fresh venv → fixed-argv installer → local wheelhouse → EnvironmentInventory → DependencyMaterializationEvidence → DependencyMaterializationGate

## 2. Installation boundary

The installer is host-owned. It may invoke only fixed argument vectors:

- venv interpreter + `-m ensurepip --upgrade`;
- venv interpreter + `-m pip install ...`.

Both are invoked with `shell=False`. No model-generated command string is accepted.

The default policy is:

- network = false;
- shell = false;
- no interactive input;
- local wheelhouse required for non-empty package sets.

Thus J does not silently turn the Skill into an internet package installer.

## 3. Lock semantics

The locked package identity is `name + exact version`. Optional SHA256 package hashes can be enforced with pip's `--require-hashes`.

If `require_hashes=true`, every locked package must carry a SHA256 hash. If a package hash is absent under that policy, installation fails closed.

## 4. Observed inventory

After installation, the environment is inspected from the target interpreter using `importlib.metadata`. The inventory is sorted and fingerprinted.

The gate compares every locked package against the observed package inventory. A missing package or version mismatch is a hard failure.

This is stronger than trusting a lock file: the evidence comes from the environment that was actually materialized.

## 5. Deliberate limitation

V1.0-J does not yet execute a modeling ToolRegistry callable inside the venv. The current target is dependency closure only.

The next step should bind a registered modeling tool to a fixed host-owned module entrypoint, execute it with the venv interpreter, collect ResultBundle + execution log, and automatically feed that result into V1.0-C reproducibility.

## 6. Security rule

No arbitrary shell. No model-generated pip arguments. Package names and versions are validated before being placed into the fixed pip argv. Network remains disabled by schema contract.

Python venv is not a container-level security boundary; true OS/container isolation remains a trusted-host responsibility.
