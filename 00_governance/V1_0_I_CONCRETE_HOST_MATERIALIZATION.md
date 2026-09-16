# V1.0-I Concrete Host Materialization

## 1. Goal

V1.0-I converts the V1.0-G/H declarative trusted-host boundary into the first concrete execution artifact: a freshly created Python `venv`.

The stage is intentionally split into two concerns:

`DependencyLockManifest → VenvMaterializationContract → Trusted Host Adapter → Fresh venv → VenvMaterializationEvidence`

It does **not** yet claim that locked packages were installed or that a modeling tool was executed inside the new environment.

## 2. Security boundary

The core Skill must not execute model-generated shell commands. The V1.0-I adapter therefore:

- uses Python's standard-library `venv.EnvBuilder`;
- creates only a fresh target that did not exist before the run;
- does not call pip, conda, docker, or a shell;
- requires `allow_network=false` and `allow_shell=false`;
- records the materialized interpreter and its SHA256;
- carries the exact DependencyLock fingerprint into the evidence.

A real OS/container sandbox is still the responsibility of the trusted host. Python `venv` is Python-environment isolation, not a security container.

## 3. Freshness rule

The target directory must be a child of the run output directory and must not exist before materialization. Reusing an existing environment is a hard failure.

## 4. Evidence rule

`VenvMaterializationEvidence` is produced only after the interpreter exists. The materialization gate requires:

- status `MATERIALIZED`;
- `fresh=true`;
- network and shell disabled;
- isolation required;
- a dependency-lock hash;
- an existing interpreter;
- interpreter SHA256.

Missing evidence is `NOT_RUN`; contradictory evidence is `FAIL`.

## 5. What remains for V1.0-J

V1.0-I intentionally stops before dependency installation and cross-process tool execution. The next stage should add a host-owned, fixed-argv package installation mechanism against the locked dependency manifest, followed by observed package inventory and then execution through an approved entrypoint. It must not become an arbitrary command runner.
