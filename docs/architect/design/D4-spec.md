# D4 · Design-Grade Spec

> **Gate**: Campaign D4 · DeepSeek V4 MTP clean pre-load rejection
> **Plan-grade source**: [`../01-mainline-roadmap.md`](../01-mainline-roadmap.md) Campaign D
> **Status**: passed · 2026-05-17
> **Prerequisite**: D3 inspection passed with
> `capability_conclusion=mtp_checkpoint_not_available`.
> **Non-goal**: this spec does not claim DeepSeek V4 MTP serving or supported
> DeepSeek serving.

## 1. Purpose

D4 closes the current DeepSeek MTP branch by proving the runtime rejects the
unavailable MTP path **before** any model load or child-process generation is
attempted.

```text
consume D3 checkpoint inspection
  -> see missingReason=mtp_weights_absent_or_stripped
  -> reject requested capability deepseek_v4_mtp
  -> probe 8066 health before / after
  -> record that runtime state did not change
```

D4 is a failure-isolation gate. It intentionally records a clean rejection, not
a generation result.

## 2. Scope

| Item | Requirement |
|---|---|
| Requested capability | `deepseek_v4_mtp` |
| Source evidence | D3 JSONL row under `files/evidence/owlmlx/deepseek-v4/d3-checkpoint-inspection/` |
| Reject reason | `mtp_weights_absent_or_stripped` |
| Runtime probe | `http://127.0.0.1:8066/healthz` before and after when supplied |
| Evidence | JSONL under `files/evidence/owlmlx/deepseek-v4/d4-preload-reject/` |
| Capability label | `experimental_only` |

Out of scope:

- no MTP load attempt
- no child process start
- no model visibility registration
- no `ds4.c` adoption
- no supported DeepSeek claim

## 3. Ledger Shape

Each row is one clean pre-load rejection record:

```yaml
schema_version: d4.preload_reject.v1
record_type: mtp_preload_reject
gate: D4
model_id: DeepSeek-V4-Flash-2bit-DQ
requested_capability: deepseek_v4_mtp
source_inspection:
  schema_version: d3.checkpoint_inspection.v1
  capability_conclusion: mtp_checkpoint_not_available
  missingReason: mtp_weights_absent_or_stripped
decision: rejected_pre_load
reason_code: mtp_weights_absent_or_stripped
load_attempted: false
child_process_started: false
default_model_surface_changed: false
runtime_health:
  before_fingerprint: object
  after_fingerprint: object
  stable: true
verdict: passed
```

## 4. Pass Criteria

```yaml
D4_clean_preload_reject:
  source_d3:
    capability_conclusion: mtp_checkpoint_not_available
    missingReason: mtp_weights_absent_or_stripped
  reject:
    decision: rejected_pre_load
    reason_code: mtp_weights_absent_or_stripped
    load_attempted: false
    child_process_started: false
    default_model_surface_changed: false
  health:
    if_runtime_health_url_supplied:
      observed_before: true
      observed_after: true
      stable_fingerprint: true
  overall_conclusion: passed
```

D4 fails if D3 presents candidate MTP weights, if health cannot be observed
when required, or if the before/after health fingerprint changes.

## 5. Current Evidence

```bash
uv run python scripts/bench/deepseek_v4_d1_repeatability.py mtp-preload-reject \
  --run-id 20260517T-d4-mtp-clean-preload-reject \
  --inspection-path files/evidence/owlmlx/deepseek-v4/d3-checkpoint-inspection/20260517T-d3-mtp-checkpoint-inspection.jsonl \
  --runtime-health-url http://127.0.0.1:8066/healthz
```

| File | Verdict | Key conclusion |
|---|---|---|
| `files/evidence/owlmlx/deepseek-v4/d4-preload-reject/20260517T-d4-mtp-clean-preload-reject.jsonl` | passed | `decision=rejected_pre_load`; `reason_code=mtp_weights_absent_or_stripped`; `load_attempted=false`; `child_process_started=false`; 8066 health stable before/after |

Current D4 boundary: current local artifact has no usable DeepSeek MTP path, and
owlmlx rejects that requested capability cleanly before load. DeepSeek V4
remains `experimental_only`.

## 6. Next Debug Slice

The current DeepSeek D1-D4 experimental lane is closed. A future D5 is useful
only if a new DeepSeek artifact or adapter fork changes the D3 checkpoint
inspection result.
