# owlmlx Stabilization-2: MLX Environment Readiness Contract

> Status: authoritative
> Updated: 2026-04-13
> Scope: runtime-only MLX environment readiness and quarantine truth

## 1. Purpose

This document freezes the runtime-owned contract for answering one question:

**Can this machine safely provide a Python environment for `mlx_lm` subprocess
execution right now?**

This is not a control-plane question. It is not a dashboard question. It is not
a replacement verdict. It is a runtime readiness question that becomes critical
before large-weight work such as MiniMax-M2.7 conversion and first-load
validation.

## 2. Owned Contract

`owlmlx/runtime/mlx_environment.py` now owns a stable readiness contract:

- `build_mlx_environment_readiness(...)`
- `readiness_to_dict(...)`

Stable surface:

- `contract`
- `summary`
- `selection`
- `quarantine`

Diagnostic-only surface:

- `probes`

The serialized contract shape is:

```json
{
  "contract": {
    "surface": "owlmlx.mlx_environment",
    "version": "stabilization2"
  },
  "summary": {
    "readiness": "ready|blocked",
    "message": "...",
    "blocked_reason": "...|null",
    "include_known_candidates": false,
    "preferred_execution_mode": "default_metal|force_cpu",
    "candidate_count": 1
  },
  "selection": {
    "ok": true,
    "selected_label": "current|runtime1-mlx|...",
    "execution_mode": "default_metal|force_cpu",
    "python_executable": "/abs/path/to/python|null"
  },
  "quarantine": {
    "count": 0
  },
  "probes": [
    {
      "label": "current",
      "python_executable": "...",
      "usable": false,
      "returncode": 1,
      "message": "..."
    }
  ]
}
```

## 3. Semantics

- `summary.readiness = ready` means at least one candidate can safely import
  `mlx_lm` under subprocess probing for the requested execution mode.
- `summary.readiness = blocked` means no candidate in the requested scope is
  currently usable.
- `selection.ok` is a machine-readable duplicate of that verdict for consumers
  that only care whether a selection exists.
- `selection.execution_mode` is part of the stable identity. A Python path that
  is unsafe for `default_metal` is not automatically unsafe for `force_cpu`.
- `quarantine.count` is stable truth about remembered unsafe interpreters.
- `probes` remains diagnostic detail. Upper layers may display it, but must not
  treat every field there as a compatibility promise.

## 4. Scope Discipline

Default readiness stays conservative:

- it probes only the default safe candidate set
- when a verified MLX baseline has been explicitly registered and has not been
  quarantined, it is preferred ahead of the current interpreter
- it does not automatically walk broader local MLX-oriented virtualenvs
- broader diagnostics require explicit opt-in

This preserves the quarantine rule established during Runtime-1/2: known unsafe
interpreters must not be retried casually.

The preference rule is not a permanent promise that any previously-good
baseline stays healthy forever. If a baseline starts aborting during import
probe, quarantine truth overrides preference and it must stop being treated as a
default candidate.

Quarantine and verified-baseline registry are now keyed by:

- `python_executable`
- `execution_mode`

This prevents `default_metal` abort history from incorrectly suppressing a
separately usable `force_cpu` path on the same interpreter.

## 5. Operator Entry

`scripts/runtime_mlx_environment_readiness.py` is the operator-facing entry for
this contract.

`scripts/register_verified_mlx_baseline.py` is the operator-facing entry for
promoting one interpreter into the verified-baseline registry after a
successful probe.

Examples:

```bash
python3 scripts/runtime_mlx_environment_readiness.py
python3 scripts/runtime_mlx_environment_readiness.py --execution-mode force_cpu
python3 scripts/runtime_mlx_environment_readiness.py --include-known-venvs
python3 scripts/register_verified_mlx_baseline.py \
  --python /abs/path/to/python \
  --label runtime1-mlx-cpu \
  --execution-mode force_cpu
```

These scripts exist to make the contract usable before a later control-plane or
ops surface chooses to consume it.

## 6. What Stabilization-2 Proves

- MLX environment readiness is no longer hidden in ad-hoc smoke scripts.
- Quarantine state is now part of explicit runtime truth.
- Future MiniMax or other large-weight MLX work has a stable readiness gate.

## 7. What Stabilization-2 Does Not Prove

- that this machine is ready to load MiniMax-M2.7 today
- that a clean environment already exists on every operator machine
- that `owlmlx` should own environment creation or package installation
- that control-plane or dashboard surfaces must now expose this contract
- that a manual top-level shell success is automatically promotable to a
  runtime-owned verified baseline
