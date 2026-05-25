"""Runtime-owned `speculative_execution_status` contract surface.

Implements F-1.2 (endpoint stub) + F-1.3 (live-state overlay from kernel
observe_* APIs) per docs/architect/design/F-1-spec.md.

F-1.2 path: a default kernel with no observe_* calls returns the §4.11.1
"spec explicitly disabled" payload from `build_speculative_execution_status_payload()`.

F-1.3 path: the kernel maintains a `_speculative_execution_state` dict and
passes it as `live_state` to `build_speculative_execution_status_payload()`,
which overlays the §4.11.2 active-runner fields. The kernel uses the helper
state machines `apply_load_event` / `apply_generate_event` / `apply_unload_event`
to transition state on each observed runner JSONL response.

Honest scope reminder (per spec §6.2): F-1.3 does NOT introduce a parent-side
spawn site for `MlxVlmMtpChildRunner`. The observe_* APIs above the build
function are written to consume synthetic / future-real runner response
shapes. They become useful the moment such a caller exists.

The `assistant_drafter` MethodEntry.status is read live from
`owlmlx.gemma4_mtp_drafter.GEMMA4_MTP_CAPABILITY_LABEL` via attribute access
at call time so tests / future capability promotions are reflected without a
process restart.
"""

from __future__ import annotations

import math
import time
from typing import Any

from owlmlx import gemma4_mtp_drafter as _drafter_module


SPECULATIVE_EXECUTION_STATUS_SURFACE = "owlmlx.speculative_execution_status"
SPECULATIVE_EXECUTION_STATUS_VERSION = "v1"


# ---------------------------------------------------------------------------
# Day-one vocabularies (locked at v1 per spec §4.5)
# ---------------------------------------------------------------------------


_DAY_ONE_METHOD_NAMES = (
    "native_mtp",
    "assistant_drafter",
    "draft_model",
    "eagle",
    "ngram",
)


_DAY_ONE_METHOD_NOTES: dict[str, str | None] = {
    "native_mtp": "DS4 MTP weights absent or stripped (see D3)",
    "assistant_drafter": "deferred_cli_per_request via mlx_vlm",
    "draft_model": None,
    "eagle": None,
    "ngram": "F-2 candidate",
}


_DAY_ONE_STATIC_STATUS: dict[str, str] = {
    "native_mtp": "not_implemented",
    # "assistant_drafter": <read live from module constant>
    "draft_model": "not_implemented",
    "eagle": "not_implemented",
    "ngram": "not_implemented",
}


# Map from runner-emitted `runtime_family` to the spec method it serves.
# Future methods (resident native MTP, EAGLE, etc.) extend this map without
# breaking the v1 contract.
_RUNTIME_FAMILY_TO_METHOD: dict[str, str] = {
    "mlx-vlm-mtp": "assistant_drafter",
}


# Per-method cache sharing declarations (§4.9 day-one table). These are
# constants per method — F-1 never measures live cache state.
_CACHE_SHARING_BY_METHOD: dict[str, dict[str, Any]] = {
    "assistant_drafter": {
        "reads_session_kv_cache": False,
        "writes_session_kv_cache": False,
        "shares_target_kv": False,
        "scope": "deferred_cli_per_request",
    },
    "native_mtp": {
        "reads_session_kv_cache": False,
        "writes_session_kv_cache": False,
        "shares_target_kv": True,
        "scope": "in_process_resident",
    },
    "draft_model": {
        "reads_session_kv_cache": False,
        "writes_session_kv_cache": False,
        "shares_target_kv": True,
        "scope": "in_process_resident",
    },
    "eagle": {
        "reads_session_kv_cache": False,
        "writes_session_kv_cache": False,
        "shares_target_kv": True,
        "scope": "in_process_resident",
    },
    "ngram": {
        "reads_session_kv_cache": False,
        "writes_session_kv_cache": False,
        "shares_target_kv": False,
        "scope": "none",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return the current UTC instant in ISO 8601 with Z suffix.

    Extracted for monkeypatch-friendliness in tests and for parity with
    other owlmlx emitters.
    """
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _day_one_method_vocabulary() -> list[dict[str, Any]]:
    """Build the day-one `available_methods` list.

    The `assistant_drafter` status is read live from
    `GEMMA4_MTP_CAPABILITY_LABEL` (attribute access on the module object,
    not a bound import) so monkeypatching the constant in tests propagates
    without needing to reimport.
    """
    vocabulary: list[dict[str, Any]] = []
    for name in _DAY_ONE_METHOD_NAMES:
        if name == "assistant_drafter":
            status = _drafter_module.GEMMA4_MTP_CAPABILITY_LABEL
        else:
            status = _DAY_ONE_STATIC_STATUS[name]
        vocabulary.append(
            {
                "method": name,
                "status": status,
                "notes": _DAY_ONE_METHOD_NOTES[name],
            }
        )
    return vocabulary


def default_state() -> dict[str, Any]:
    """Return the kernel's default `_speculative_execution_state` dict.

    Used at kernel init and as the post-unload reset target. Matches the
    §4.11.1 spec-disabled default.
    """
    return {
        "method": None,
        "capability_label": "disabled",
        "runner_status": "unloaded",
        "missing_reason": "spec_explicitly_disabled",
        "drafter_id": None,
        "runner_started_at": None,
        "last_request_at": None,
        "accepted_tokens": 0,
        "accepted_rounds": 0,
        "fallback": None,
    }


# ---------------------------------------------------------------------------
# State transitions (pure functions; kernel methods are thin wrappers)
# ---------------------------------------------------------------------------


def _resolve_load_failure_reason(load_response: dict[str, Any]) -> str:
    """Pick the most specific §4.10 vocabulary value for a load failure."""
    toolchain = load_response.get("toolchain")
    if isinstance(toolchain, dict) and toolchain.get("ok") is False:
        return "mlx_vlm_toolchain_missing"
    pair = load_response.get("pair")
    if isinstance(pair, dict) and pair.get("ok") is False:
        return "target_draft_pair_blocked"
    return "runner_load_failed"


def apply_load_event(
    state: dict[str, Any],
    load_response: dict[str, Any],
) -> dict[str, Any]:
    """Return new state after an observe_load event.

    Unknown `runtime_family` is a no-op (returns state unchanged) per
    §4.5 vocabulary discipline + the test
    `test_observe_unknown_runtime_family_is_noop`.
    """
    family = load_response.get("runtime_family")
    if not isinstance(family, str):
        return state
    method = _RUNTIME_FAMILY_TO_METHOD.get(family)
    if method is None:
        return state

    new_state = dict(state)

    if load_response.get("ok"):
        # Successful load: §4.11.2 active shape, fallback cleared.
        new_state.update(
            {
                "method": method,
                "capability_label": load_response.get(
                    "capability_label",
                    "experimental",
                ),
                "runner_status": load_response.get("load_mode", "loaded"),
                "missing_reason": None,
                "drafter_id": load_response.get("draft_model_path"),
                "runner_started_at": _now_iso(),
                "last_request_at": None,
                "accepted_tokens": 0,
                "accepted_rounds": 0,
                "fallback": None,
            }
        )
        return new_state

    # Failed load: runner_status=error, fallback populated.
    reason_code = _resolve_load_failure_reason(load_response)
    prev_fallback = state.get("fallback")
    prev_count = (
        prev_fallback.get("transition_count", 0)
        if isinstance(prev_fallback, dict)
        else 0
    )
    new_state.update(
        {
            "method": None,
            "capability_label": "disabled",
            "runner_status": "error",
            "missing_reason": reason_code,
            "drafter_id": None,
            "runner_started_at": None,
            "last_request_at": None,
            "accepted_tokens": 0,
            "accepted_rounds": 0,
            "fallback": {
                "from_method": method,
                "to_method": None,
                "reason_code": reason_code,
                "observed_at": _now_iso(),
                "transition_count": prev_count + 1,
            },
        }
    )
    return new_state


def apply_generate_event(
    state: dict[str, Any],
    generate_response: dict[str, Any],
) -> dict[str, Any]:
    """Return new state after an observe_generate event.

    If kernel has no active method, this is a stray generate and the state
    is unchanged. If returncode != 0, a runner crash is recorded.
    """
    if state.get("method") is None:
        return state

    family = generate_response.get("runtime_family")
    if not isinstance(family, str):
        return state
    family_method = _RUNTIME_FAMILY_TO_METHOD.get(family)
    if family_method is None or family_method != state["method"]:
        # Stray generate from a different runner family — ignore.
        return state

    new_state = dict(state)
    returncode = generate_response.get("returncode")
    ok = bool(generate_response.get("ok"))

    if ok and returncode == 0:
        # Successful generate: advance last_request_at; increment counters
        # if a speculative_summary is parseable.
        new_state["last_request_at"] = _now_iso()
        summary = generate_response.get("speculative_summary")
        if isinstance(summary, dict):
            mean = summary.get("mean_accepted_tokens")
            rounds = summary.get("rounds")
            if isinstance(mean, (int, float)) and isinstance(rounds, int):
                new_state["accepted_tokens"] = state.get(
                    "accepted_tokens", 0
                ) + math.floor(float(mean) * rounds)
                new_state["accepted_rounds"] = state.get(
                    "accepted_rounds", 0
                ) + int(rounds)
        return new_state

    # Crash: keep method, set runner_status=error, populate fallback.
    prev_fallback = state.get("fallback")
    prev_count = (
        prev_fallback.get("transition_count", 0)
        if isinstance(prev_fallback, dict)
        else 0
    )
    new_state.update(
        {
            "runner_status": "error",
            "missing_reason": "runner_crash",
            "last_request_at": _now_iso(),
            "fallback": {
                "from_method": state["method"],
                "to_method": None,
                "reason_code": "runner_crash",
                "observed_at": _now_iso(),
                "transition_count": prev_count + 1,
            },
        }
    )
    return new_state


def apply_unload_event(_state: dict[str, Any]) -> dict[str, Any]:
    """Return the default state, regardless of prior state."""
    return default_state()


# ---------------------------------------------------------------------------
# Public build function
# ---------------------------------------------------------------------------


def build_speculative_execution_status_payload(
    live_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the §4.11.1 or §4.11.2 payload.

    When `live_state` is None or has `method=None` with no fallback / non-
    default missing_reason, the §4.11.1 spec-disabled shape is returned.
    When `live_state["method"]` is a non-null vocabulary value, the §4.11.2
    active-runner shape is returned with optional fields overlaid.

    F-1.3 honesty rules enforced:
    - `rejected_tokens` is always `None` when a method is active or last-
      active (§4.4 honesty rule).
    - `capability_label` reflects the method's static / load-reported label
      even when `runner_status=error` (§4.6 separation).
    """
    if live_state is None:
        live_state = default_state()

    method = live_state.get("method")
    payload: dict[str, Any] = {
        "surface": SPECULATIVE_EXECUTION_STATUS_SURFACE,
        "version": SPECULATIVE_EXECUTION_STATUS_VERSION,
        "method": method,
        "capability_label": live_state.get("capability_label", "disabled"),
        "runner_status": live_state.get("runner_status", "unloaded"),
        "available_methods": _day_one_method_vocabulary(),
    }

    missing_reason = live_state.get("missing_reason")
    if missing_reason:
        payload["missing_reason"] = missing_reason

    fallback = live_state.get("fallback")
    if fallback is not None:
        payload["fallback"] = fallback

    if method is not None:
        # §4.11.2 active-shape additions.
        drafter_id = live_state.get("drafter_id")
        if drafter_id is not None:
            payload["drafter_id"] = drafter_id

        runner_started_at = live_state.get("runner_started_at")
        if runner_started_at is not None:
            payload["runner_started_at"] = runner_started_at

        last_request_at = live_state.get("last_request_at")
        if last_request_at is not None:
            payload["last_request_at"] = last_request_at

        # Counters are part of the active-method lifecycle: when method is
        # non-null they are always present (possibly zero). Absence is
        # reserved for the spec-disabled / method=null path.
        payload["accepted_tokens"] = int(live_state.get("accepted_tokens", 0))
        payload["accepted_rounds"] = int(live_state.get("accepted_rounds", 0))

        # Explicit null for rejected_tokens conveys the §4.4 honesty rule
        # to consumers: "the runtime knows about this field but cannot
        # honestly populate it from current upstream output."
        payload["rejected_tokens"] = None

        cache_sharing = _CACHE_SHARING_BY_METHOD.get(method)
        if cache_sharing is not None:
            payload["cache_sharing"] = cache_sharing

    return payload
