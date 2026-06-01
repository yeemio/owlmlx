# OwlMLX F-3.1 Code-Grade Prompt: Resident MTP Feasibility Probe

> Created: 2026-06-01
> Goal: `owlmlx-f3-resident-mtp-feasibility`
> Parent spec:
> `docs/architect/design/F-3-resident-mtp-spec.md`

## Mission

Produce the F-3.1 feasibility verdict for Gemma4 resident MTP.

This is a prerequisite probe, not the F-3.2 resident backend and not the F-3.3
A/B benchmark. The round answers one question:

> Can the local isolated `mlx-vlm` runtime hold `gemma-4-31B-it` plus
> `gemma-4-31B-it-assistant-bf16` resident across multiple requests without
> reloading the model and without relying on unsupported trim?

## Required First Reads

1. `AGENTS.md`
2. `files/goals/owlmlx/f3-resident-mtp-feasibility-goal-contract.md`
3. `docs/architect/design/F-3-resident-mtp-spec.md`
4. `docs/source-of-truth/gemma4-mtp-drafter-probe-20260506.md`
5. `owlmlx/gemma4_mtp_drafter.py`
6. `owlmlx/runtime/mlx_vlm_mtp_runner.py`
7. `scripts/runtime_gemma4_mtp_drafter.py`
8. `tests/test_gemma4_mtp_drafter.py`
9. `tests/test_mlx_vlm_mtp_runner.py`

## Hard Rules

1. Do not start F-3.2 resident backend code-grade.
2. Do not count `MlxVlmMtpChildRunner` as resident if it shells out to
   `python -m mlx_vlm generate` for each request.
3. Do not edit `mlx-vlm`, vendor upstream, or change the F-1
   `speculative_execution_status` schema.
4. Do not touch Track 1 cache/memory files:
   `owlmlx/session_kv_cache.py`, `owlmlx/cache_manager.py`,
   `owlmlx/scheduler_admission.py`, `owlmlx/memory_pressure_eviction_policy.py`,
   or `owlmlx/memory_watermark.py`.
5. Keep `GEMMA4_MTP_CAPABILITY_LABEL` as `experimental`.
6. Leave unrelated dirty/untracked files untouched.

## Required Work

1. Verify the current upstream/local prerequisite state:
   - `mlx-lm #980` live issue state;
   - installed versions in the main env and isolated MTP probe env;
   - model/drafter directories.
2. Inspect the isolated `mlx-vlm` runtime for a programmatic API surface that
   can load a model once and generate multiple times.
3. If a true resident API exists, implement the smallest operator probe script
   that:
   - loads target + drafter once;
   - serves at least 3 sequential generate requests;
   - counts reloads explicitly;
   - records speculative summary on request 2+;
   - records whether trim was attempted;
   - emits `files/evidence/owlmlx/bench/f3-resident-mtp/<ts>-f3-1-resident-feasibility.jsonl`.
4. If no true resident API exists, emit a verdict ledger with
   `verdict=blocked_on_local_runtime` and evidence showing why the current
   runtime cannot satisfy F-3.1.
5. Update only F-3 docs/evidence needed to reflect the verdict.

## Verdict Values

Allowed verdicts:

- `resident_viable_append_only`
- `resident_viable_with_trim`
- `blocked_on_local_runtime`
- `blocked_on_980`
- `failed`

`resident_viable_*` unlocks a later F-3.2 round. Any blocked/failed verdict
keeps F-3 design-ready but code-grade-blocked.

## Suggested Commands

```bash
uv run pytest tests/test_gemma4_mtp_drafter.py tests/test_mlx_vlm_mtp_runner.py -q
uv run pytest tests/test_runtime_gemma4_mtp_resident_probe.py tests/test_gemma4_mtp_drafter.py tests/test_mlx_vlm_mtp_runner.py -q

uv run python scripts/runtime_gemma4_mtp_resident_probe.py inspect-api

/Users/yeemio/AI/gitrep/runtime-probes/mlx-vlm-mtp-probe-py311/.venv/bin/python - <<'PY'
import importlib.metadata as m
for name in ["mlx-vlm", "mlx-lm", "mlx"]:
    print(name, m.version(name))
PY

uv run python scripts/runtime_gemma4_mtp_resident_probe.py run-probe
```

Run the heavy Gemma4 probe only after the API-surface inspection proves it is
testing a real resident path rather than per-request CLI reload, and only when
no other memory-sensitive soak/evidence run is active on the host.

## Expected Outcome

The round ends with a narrow, evidence-backed F-3.1 verdict. It either unlocks
F-3.2 with a real resident primitive, or records exactly why the current local
runtime still cannot support resident Gemma4 MTP.
