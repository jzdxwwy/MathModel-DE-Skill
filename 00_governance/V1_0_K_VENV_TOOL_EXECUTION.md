# V1.0-K Venv Tool Execution

## Goal
V1.0-K is the first stage that executes a registered modeling tool in the target Python venv rather than in the parent Runtime process.

## Execution chain
VenvToolExecutionContract -> input hash verification -> host-resolved fixed module -> venv Python -> approved ToolRegistry id -> ResultBundle -> execution log -> VenvToolExecutionEvidence -> VenvToolExecutionGate.

## Fixed entrypoint
The executor invokes one fixed Python module with shell=False and explicit argv. The model may select only a registered tool id and payload path. It cannot provide Python source, shell syntax, arbitrary import code, or a command string.

## Result contract
The entrypoint materializes a ResultBundle inside the independent execution directory. The reference ResultBundle is never overwritten.

## Evidence
Evidence binds run_id, adapter_id, tool, interpreter, isolation_id, input hashes, dependency lock hash, observed environment fingerprint, ResultBundle hash and execution log hash.

## Security boundary
Network and shell are disabled by contract. Python venv is process/package isolation, not an OS/container security boundary. A stronger clean-room boundary still requires a trusted container or VM adapter.

## Limitation
The first implementation uses the repository fixed module entrypoint and default registered tools. A production trusted host should provide an explicit allowlisted module resolver and avoid relying on a caller-supplied import path.

## Next
V1.0-L should connect K execution evidence to the existing ExecutionEvidence and Reproducibility gates, and should eliminate duplicate ResultBundle construction where possible.
