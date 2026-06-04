# R4 Phase-1 Pilot Closeout — owlmlx-only OwlCoda Controlled Smoke

> Status: **R4 Phase-1 closeout (controlled pilot PASSED — promotes nothing)**
> Date: 2026-06-04
> Evidence commit: `da6f35e3` (origin/main); pilot ran against owlmlx `9014775e`
> Spec: [`../architect/design/R4-ops-cutover-spec.md`](../architect/design/R4-ops-cutover-spec.md) · Plan: `R4-ops-cutover-plan.md` · Runbook: `R4-ops-cutover-runbook.md`
> Re-baseline context: [`runtime13-replacement-rebaseline-verdict.md`](runtime13-replacement-rebaseline-verdict.md) §5 (R4)

---

## §1 What passed

One **controlled, non-default** agentic loop —
`OwlCoda 0.15.0 → owlmlx :8066 (owlmlx-only) → Qwen3.6-35B-A3B → Bash tool → final answer` —
ran live and the R4 harness (`scripts/replacement/r4_ops_cutover_pilot.py`) emitted
`verdict: passed`. Evidence (under `files/evidence/owlmlx/replacement/r4-ops-cutover/`):

- pilot verdict: `20260604T080213Z-pilot-passed-conv-1780560067760-d35frq.json`
- readiness verdict: `20260604T080052Z-readiness-readiness_passed-Qwen3.6-35B-A3B.json`
- operator capture + correlated logs: `live-logs/20260604T080009Z-r4-owlcoda-pilot-correlated/`

Gates met (each independently recorded):

- **Readiness**: healthz 200; `Qwen3.6-35B-A3B` visible in `/v1/openai/models` + visibility contract; tool lane live (1 forced tool_call); monitor reachable.
- **Tool lane — 4 independent sub-gates**: `tool_call_emitted` / `tool_call_executed` / `tool_result_roundtrip` / `final_answer_after_tool` = all `true`.
- **`fallback_used=false` (double-proof)**: consumer config snapshot points at owlmlx `:8066`; consumer outbound has no `:8009`; owlmlx-side **inbound coverage** proven via the static pilot `x-request-id` correlating two `/v1/chat/completions 200` in the request-lifecycle log.
- **Watermark health gate**: no RED this session (`healthy_serving`) — recorded as "this session only", explicitly NOT a stability claim.

## §2 What this does NOT establish (bounds — verbatim honesty)

- **Not** a default cutover — OwlCoda/OwlCC committed defaults still point at `:8009` / `:11434`; this used a non-default pilot profile.
- **Not** sustained stability — one session, not a soak (→ R4 Phase B).
- **Not** non-Qwen parity — `Qwen3.6-35B-A3B` + the existing **experimental, Qwen-only** tool lane only.
- **No capability promotion**; Session KV / prefix cache stay `experimental`; the §1a Promotion Gate is unchanged.
- Replacement verdict stays **`not yet replaceable`**.

## §3 Blocker / gap status delta (vs runtime13)

- **Blocker ④ (ops-level replacement)**: ⛔ open → **◐** — first controlled owlmlx-only customer pilot PASSED (`da6f35e3`). Still open for the **default flip** and **sustained soak**.
- **Gap 5 (`customer_runtime_evidence`)**: ⛔ open → **◐** — past the zero-evidence `early_formal_runtime` floor for a single controlled session; **not** production-sustained evidence.

(runtime13 §3/§4 bodies are point-in-time 2026-06-03; this closeout is the current status for blocker ④ / gap 5.)

## §4 Narrowed remaining critical path

- **R4 Phase B** — sustained owlmlx-only soak + formal default flip (OwlCoda owlmlx-gate / OwlCC `routerUrl` repoint) + remove the `:8009` fallback on the default path.
- **R1** — tool-calling / source-first parity **beyond Qwen-only** experimental (the pilot validated Qwen only). [blocker ①]
- **R2** — production control-plane last-mile closure. [blocker ②]

## §5 Verification & scope

- `uv run pytest tests/test_r4_ops_cutover_pilot.py -q` → `24 passed` (harness logic).
- Pilot ran against owlmlx `9014775e` (incl. the 2026-06-04 serving fixes F1–F4 + subprocess), so those fixes were exercised **live** in the loop (no crash; tool loop + final answer produced).
- Temp `:8066` / `:8029` stopped after the run; the user's live `:8019` untouched; pre-existing dirty files untouched.
- This is **ops-evidence capture**, not a §1a capability promotion. Cross-repo touch was read-only / pilot-config only; no OwlCoda/OwlCC repo file committed here.
