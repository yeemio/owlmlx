"""Contract tests for the speculative_execution_status surface.

F-1.2 block: §4.11.1 spec-disabled stub shape, kernel's top-level
diagnostic placement, contract.diagnostic_sections registration, live
read of GEMMA4_MTP_CAPABILITY_LABEL.

F-1.3 block: kernel observe_speculative_runner_{load,generate,unload}
APIs; §4.11.2 active-runner shape; counter accumulation via floor(mean
* rounds); rejected_tokens stays null; crash-keeps-method semantics;
FallbackEntry lifetime per §4.8.

Source: docs/architect/design/F-1-spec.md §4.11.1 / §4.11.2 / §5.1 / §5.2.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from owlmlx.host_pressure import host_pressure_not_sampled_snapshot
from owlmlx.runtime.backends import FakeBackend
from owlmlx.runtime.kernel import RuntimeKernel
from owlmlx.runtime.server import create_app


F1_SURFACE = "owlmlx.speculative_execution_status"
F1_VERSION = "v1"
F1_ROUTE = "/v1/runtime/speculative-execution-status"

EXPECTED_DAY_ONE_METHOD_NAMES = (
    "native_mtp",
    "assistant_drafter",
    "draft_model",
    "eagle",
    "ngram",
)


def _fresh_client() -> tuple[TestClient, RuntimeKernel]:
    """Fresh kernel + FakeBackend with no model loaded.

    No load_model() call — the §4.11.1 default applies whether or not a
    model is loaded (spec is orthogonal to model presence).
    """
    backend = FakeBackend()
    kernel = RuntimeKernel(
        backend,
        host_pressure_sampler=host_pressure_not_sampled_snapshot,
    )
    return TestClient(create_app(kernel)), kernel


# ---------------------------------------------------------------------------
# §4.11.1 verbatim shape (every field present, exact vocabulary values)
# ---------------------------------------------------------------------------


def test_route_returns_spec_disabled_default_shape() -> None:
    client, _kernel = _fresh_client()

    response = client.get(F1_ROUTE)

    assert response.status_code == 200
    payload = response.json()
    assert payload["surface"] == F1_SURFACE
    assert payload["version"] == F1_VERSION
    assert payload["method"] is None
    assert payload["capability_label"] == "disabled"
    assert payload["runner_status"] == "unloaded"
    assert payload["missing_reason"] == "spec_explicitly_disabled"
    assert isinstance(payload["available_methods"], list)
    assert len(payload["available_methods"]) == 5


def test_route_required_keys_are_exactly_seven() -> None:
    """The §4.11.1 shape lists exactly these seven keys at top level."""
    client, _kernel = _fresh_client()

    payload = client.get(F1_ROUTE).json()

    assert set(payload.keys()) == {
        "surface",
        "version",
        "method",
        "capability_label",
        "runner_status",
        "missing_reason",
        "available_methods",
    }


def test_available_methods_day_one_vocabulary() -> None:
    client, _kernel = _fresh_client()

    payload = client.get(F1_ROUTE).json()

    method_names = tuple(entry["method"] for entry in payload["available_methods"])
    assert method_names == EXPECTED_DAY_ONE_METHOD_NAMES


def test_available_methods_each_entry_shape() -> None:
    """Every MethodEntry has exactly {method, status, notes} keys."""
    client, _kernel = _fresh_client()

    payload = client.get(F1_ROUTE).json()

    for entry in payload["available_methods"]:
        assert set(entry.keys()) == {"method", "status", "notes"}
        assert isinstance(entry["method"], str)
        assert isinstance(entry["status"], str)
        assert entry["notes"] is None or isinstance(entry["notes"], str)


def test_available_methods_default_statuses() -> None:
    """All methods default to not_implemented except assistant_drafter."""
    client, _kernel = _fresh_client()

    payload = client.get(F1_ROUTE).json()

    by_name = {entry["method"]: entry for entry in payload["available_methods"]}
    assert by_name["native_mtp"]["status"] == "not_implemented"
    # assistant_drafter status defaults to the module constant ("experimental")
    assert by_name["assistant_drafter"]["status"] == "experimental"
    assert by_name["draft_model"]["status"] == "not_implemented"
    assert by_name["eagle"]["status"] == "not_implemented"
    assert by_name["ngram"]["status"] == "not_implemented"


def test_native_mtp_default_notes_match_d3_link() -> None:
    client, _kernel = _fresh_client()

    payload = client.get(F1_ROUTE).json()
    by_name = {entry["method"]: entry for entry in payload["available_methods"]}

    assert "D3" in by_name["native_mtp"]["notes"]
    assert "deferred_cli_per_request" in by_name["assistant_drafter"]["notes"]
    assert by_name["draft_model"]["notes"] is None
    assert by_name["eagle"]["notes"] is None
    assert "F-2" in by_name["ngram"]["notes"]


# ---------------------------------------------------------------------------
# Kernel-level placement + contract.diagnostic_sections registration
# ---------------------------------------------------------------------------


def test_status_dict_top_level_key_present() -> None:
    """speculative_execution_status is a top-level key (peer of reclaim_barrier).

    Per §4.1 rationale: NOT nested under backend.detail.
    """
    _client, kernel = _fresh_client()

    status = kernel.status_dict()
    assert "speculative_execution_status" in status
    # Must NOT be under backend.detail
    backend_detail = status.get("backend", {}).get("detail", {})
    assert "speculative_execution_status" not in backend_detail


def test_status_dict_payload_matches_route_payload() -> None:
    """status_dict()['speculative_execution_status'] equals route response.

    Per §5.1: 'status_dict() produces the same payload'.
    """
    client, kernel = _fresh_client()

    route_payload = client.get(F1_ROUTE).json()
    kernel_payload = kernel.status_dict()["speculative_execution_status"]

    assert route_payload == kernel_payload


def test_diagnostic_sections_lists_speculative_execution_status() -> None:
    """contract.diagnostic_sections registers the new section name.

    Per §5.1: 'status_dict()["contract"]["diagnostic_sections"] contains
    the string "speculative_execution_status" after F-1.2 lands'.
    """
    _client, kernel = _fresh_client()

    sections = kernel.status_dict()["contract"]["diagnostic_sections"]
    assert "speculative_execution_status" in sections


# ---------------------------------------------------------------------------
# Live read of GEMMA4_MTP_CAPABILITY_LABEL (monkeypatch verification)
# ---------------------------------------------------------------------------


def test_assistant_drafter_status_is_read_live_from_module_constant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Per §5.1: 'changing the constant in a test fixture and re-querying
    the endpoint MUST reflect the change in
    available_methods[method=assistant_drafter].status'.
    """
    monkeypatch.setattr(
        "owlmlx.gemma4_mtp_drafter.GEMMA4_MTP_CAPABILITY_LABEL",
        "partial",
    )

    client, _kernel = _fresh_client()
    payload = client.get(F1_ROUTE).json()

    by_name = {entry["method"]: entry for entry in payload["available_methods"]}
    assert by_name["assistant_drafter"]["status"] == "partial"


def test_assistant_drafter_label_change_does_not_affect_top_level_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Top-level capability_label remains 'disabled' until F-1.3 wires
    live runner state. The module constant only affects available_methods.
    """
    monkeypatch.setattr(
        "owlmlx.gemma4_mtp_drafter.GEMMA4_MTP_CAPABILITY_LABEL",
        "supported",
    )

    client, _kernel = _fresh_client()
    payload = client.get(F1_ROUTE).json()

    # F-1.2: no runner is wired in, so top-level stays disabled.
    assert payload["capability_label"] == "disabled"
    assert payload["method"] is None
    assert payload["runner_status"] == "unloaded"


# ---------------------------------------------------------------------------
# §5.1 invariants
# ---------------------------------------------------------------------------


def test_disabled_implies_method_null_invariant() -> None:
    """Per §4.6 invariant: capability_label=disabled ⇒ method is null."""
    client, _kernel = _fresh_client()

    payload = client.get(F1_ROUTE).json()
    if payload["capability_label"] == "disabled":
        assert payload["method"] is None


def test_runner_status_invariant_when_method_is_null() -> None:
    """Per §4.7 invariant: method=null ⇒ runner_status ∈
    {unloaded, deferred_cli_per_request, error}.
    Forbidden: method=null AND runner_status=loaded.
    """
    client, _kernel = _fresh_client()

    payload = client.get(F1_ROUTE).json()
    if payload["method"] is None:
        assert payload["runner_status"] in {
            "unloaded",
            "deferred_cli_per_request",
            "error",
        }
        assert payload["runner_status"] != "loaded"


def test_route_works_without_native_backend() -> None:
    """Per §5.1: 'when the runtime is started with no native backend, the
    route still returns the §4.11.1 payload (does not 503)'.
    """
    # FakeBackend is NOT a native backend; this is the canonical
    # non-native fixture.
    client, _kernel = _fresh_client()

    response = client.get(F1_ROUTE)

    assert response.status_code == 200
    payload = response.json()
    assert payload["surface"] == F1_SURFACE
    assert payload["method"] is None


# ===========================================================================
# F-1.3 block: observe_* APIs + §4.11.2 active shape
# ===========================================================================


def _synthetic_load_success(
    *,
    runtime_family: str = "mlx-vlm-mtp",
    capability_label: str = "experimental",
    load_mode: str = "deferred_cli_per_request",
    draft_model_path: str = "/Users/test/models/gemma-4-31B-it-assistant-bf16",
) -> dict:
    """Synthesize an MlxVlmMtpChildRunner._load success response.

    Matches the shape emitted at owlmlx/runtime/mlx_vlm_mtp_runner.py
    lines 207-219 when ok=True.
    """
    return {
        "ok": True,
        "action": "load",
        "model_id": "gemma-4-31B-it",
        "pid": 99999,
        "runtime_family": runtime_family,
        "capability_label": capability_label,
        "load_mode": load_mode,
        "draft_model_path": draft_model_path,
        "draft_block_size": 6,
        "pair": {"ok": True, "blockers": []},
        "toolchain": {"ok": True, "flags_missing": []},
    }


def _synthetic_load_failure(
    *,
    runtime_family: str = "mlx-vlm-mtp",
    error: str = "Gemma4 MTP target/draft pair is blocked",
    pair_ok: bool = False,
    toolchain_ok: bool = True,
) -> dict:
    return {
        "ok": False,
        "runtime_family": runtime_family,
        "capability_label": "experimental",
        "error": error,
        "pair": {"ok": pair_ok, "blockers": ["target_config_missing"] if not pair_ok else []},
        "toolchain": {"ok": toolchain_ok, "flags_missing": [] if toolchain_ok else ["--draft-model"]},
    }


def _synthetic_generate_success(
    *,
    runtime_family: str = "mlx-vlm-mtp",
    mean_accepted_tokens: float = 1.5,
    rounds: int = 8,
    include_summary: bool = True,
) -> dict:
    """Synthesize an MlxVlmMtpChildRunner._generate success response."""
    payload: dict = {
        "ok": True,
        "action": "generate",
        "runtime_family": runtime_family,
        "capability_label": "experimental",
        "returncode": 0,
        "text": "hello",
        "finish_reason": "stop",
        "generation_count": 1,
    }
    if include_summary:
        payload["speculative_summary"] = {
            "mean_accepted_tokens": mean_accepted_tokens,
            "rounds": rounds,
        }
    return payload


def _synthetic_generate_crash(
    *,
    runtime_family: str = "mlx-vlm-mtp",
    returncode: int = 1,
) -> dict:
    return {
        "ok": False,
        "action": "generate",
        "runtime_family": runtime_family,
        "capability_label": "experimental",
        "returncode": returncode,
        "stderr_excerpt": "fatal: drafter crashed",
    }


# ---- observe_load success -------------------------------------------------


def test_observe_load_success_transitions_to_active_shape() -> None:
    client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(_synthetic_load_success())

    payload = client.get(F1_ROUTE).json()
    assert payload["method"] == "assistant_drafter"
    assert payload["capability_label"] == "experimental"
    assert payload["runner_status"] == "deferred_cli_per_request"
    assert payload["drafter_id"] == "/Users/test/models/gemma-4-31B-it-assistant-bf16"
    assert payload["runner_started_at"] is not None
    # Counters start at 0; per §4.4 we omit zero-valued counters to match
    # the §4.11.1 minimality convention. They appear only after a
    # successful generate. (Implementation may emit explicit 0 instead;
    # adjust if so.)
    assert payload.get("accepted_tokens", 0) == 0
    assert payload.get("accepted_rounds", 0) == 0
    # rejected_tokens must be explicit null per §4.4 honesty rule
    assert payload["rejected_tokens"] is None
    # fallback cleared on successful load
    assert payload.get("fallback") is None
    # missing_reason cleared when method active
    assert payload.get("missing_reason") is None
    # cache_sharing per §4.9 day-one table
    assert payload["cache_sharing"] == {
        "reads_session_kv_cache": False,
        "writes_session_kv_cache": False,
        "shares_target_kv": False,
        "scope": "deferred_cli_per_request",
    }


def test_observe_load_success_keeps_available_methods_vocabulary() -> None:
    client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(_synthetic_load_success())

    payload = client.get(F1_ROUTE).json()
    method_names = tuple(entry["method"] for entry in payload["available_methods"])
    assert method_names == EXPECTED_DAY_ONE_METHOD_NAMES


# ---- observe_load failure -------------------------------------------------


def test_observe_load_failure_pair_blocked_sets_error_with_fallback() -> None:
    _client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(
        _synthetic_load_failure(pair_ok=False, toolchain_ok=True)
    )

    state = kernel.status_dict()["speculative_execution_status"]
    assert state["method"] is None
    assert state["capability_label"] == "disabled"
    assert state["runner_status"] == "error"
    assert state["missing_reason"] == "target_draft_pair_blocked"
    assert state["fallback"]["from_method"] == "assistant_drafter"
    assert state["fallback"]["to_method"] is None
    assert state["fallback"]["reason_code"] == "target_draft_pair_blocked"
    assert state["fallback"]["observed_at"] is not None
    assert state["fallback"]["transition_count"] == 1


def test_observe_load_failure_toolchain_missing_sets_specific_reason() -> None:
    _client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(
        _synthetic_load_failure(pair_ok=True, toolchain_ok=False)
    )

    state = kernel.status_dict()["speculative_execution_status"]
    assert state["missing_reason"] == "mlx_vlm_toolchain_missing"
    assert state["fallback"]["reason_code"] == "mlx_vlm_toolchain_missing"


def test_observe_load_failure_env_missing_falls_back_to_runner_load_failed() -> None:
    """Env var class failure uses the generic runner_load_failed code."""
    _client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load({
        "ok": False,
        "runtime_family": "mlx-vlm-mtp",
        "error": "OWLMLX_GEMMA4_MTP_DRAFT_MODEL is required",
        "capability_label": "experimental",
    })

    state = kernel.status_dict()["speculative_execution_status"]
    assert state["missing_reason"] == "runner_load_failed"
    assert state["fallback"]["reason_code"] == "runner_load_failed"


# ---- observe_generate counter accumulation --------------------------------


@pytest.mark.parametrize(
    "mean_accepted_tokens,rounds,expected_accepted_tokens,expected_accepted_rounds",
    [
        (1.5, 8, 12, 8),       # §5.2 worked example
        (1.7, 8, 13, 8),       # floor(13.6) = 13
        (2.0, 10, 20, 10),     # integer × integer
        (0.0, 8, 0, 8),        # zero acceptance, real rounds
    ],
)
def test_observe_generate_increments_counters_via_floor_formula(
    mean_accepted_tokens: float,
    rounds: int,
    expected_accepted_tokens: int,
    expected_accepted_rounds: int,
) -> None:
    _client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(_synthetic_load_success())
    kernel.observe_speculative_runner_generate(
        _synthetic_generate_success(
            mean_accepted_tokens=mean_accepted_tokens,
            rounds=rounds,
        )
    )

    state = kernel.status_dict()["speculative_execution_status"]
    assert state["accepted_tokens"] == expected_accepted_tokens
    assert state["accepted_rounds"] == expected_accepted_rounds


def test_observe_generate_counters_accumulate_across_calls() -> None:
    _client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(_synthetic_load_success())
    # Three calls: each 1.5 * 8 = +12 tokens, +8 rounds
    for _ in range(3):
        kernel.observe_speculative_runner_generate(
            _synthetic_generate_success(mean_accepted_tokens=1.5, rounds=8)
        )

    state = kernel.status_dict()["speculative_execution_status"]
    assert state["accepted_tokens"] == 36  # 3 * 12
    assert state["accepted_rounds"] == 24  # 3 * 8


def test_observe_generate_rejected_tokens_stays_null() -> None:
    """§4.4 honesty rule: rejected_tokens MUST stay null regardless of
    how many generates have occurred.
    """
    _client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(_synthetic_load_success())
    for _ in range(5):
        kernel.observe_speculative_runner_generate(_synthetic_generate_success())

    state = kernel.status_dict()["speculative_execution_status"]
    assert state["rejected_tokens"] is None


def test_observe_generate_advances_last_request_at() -> None:
    _client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(_synthetic_load_success())
    kernel.observe_speculative_runner_generate(_synthetic_generate_success())

    state = kernel.status_dict()["speculative_execution_status"]
    assert state["last_request_at"] is not None


def test_observe_generate_without_summary_does_not_increment_counters() -> None:
    """§8 honesty rule: returncode=0 + no parsable speculative_summary
    is 'ran without producing a summary'. last_request_at advances but
    counters do not.
    """
    _client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(_synthetic_load_success())
    kernel.observe_speculative_runner_generate(
        _synthetic_generate_success(include_summary=False)
    )

    state = kernel.status_dict()["speculative_execution_status"]
    assert state["accepted_tokens"] == 0
    assert state["accepted_rounds"] == 0
    assert state["last_request_at"] is not None  # last_request_at DOES advance
    assert state["runner_status"] == "deferred_cli_per_request"  # NOT error


# ---- observe_generate crash -----------------------------------------------


def test_observe_generate_crash_keeps_method_sets_error() -> None:
    """§5.2 / §8: returncode != 0 sets runner_status=error, populates
    missing_reason=runner_crash, populates fallback, AND keeps method
    non-null at last-loaded value.
    """
    _client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(_synthetic_load_success())
    kernel.observe_speculative_runner_generate(_synthetic_generate_crash())

    state = kernel.status_dict()["speculative_execution_status"]
    # Method preserved at last-loaded value (§5.2 + §8)
    assert state["method"] == "assistant_drafter"
    # capability_label stays at static method label, NOT downgraded (§4.6)
    assert state["capability_label"] == "experimental"
    # Runner is now broken
    assert state["runner_status"] == "error"
    assert state["missing_reason"] == "runner_crash"
    # Fallback records the transition
    assert state["fallback"]["from_method"] == "assistant_drafter"
    assert state["fallback"]["to_method"] is None
    assert state["fallback"]["reason_code"] == "runner_crash"
    assert state["fallback"]["observed_at"] is not None


# ---- observe_unload -------------------------------------------------------


def test_observe_unload_resets_to_spec_disabled_shape() -> None:
    _client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(_synthetic_load_success())
    kernel.observe_speculative_runner_generate(_synthetic_generate_success())
    kernel.observe_speculative_runner_unload()

    state = kernel.status_dict()["speculative_execution_status"]
    assert state["method"] is None
    assert state["capability_label"] == "disabled"
    assert state["runner_status"] == "unloaded"
    assert state["missing_reason"] == "spec_explicitly_disabled"
    # Counters cleared
    assert state.get("accepted_tokens", 0) == 0
    assert state.get("accepted_rounds", 0) == 0
    # Fallback cleared
    assert state.get("fallback") is None
    # Optional fields gone
    assert "drafter_id" not in state or state["drafter_id"] is None
    assert "runner_started_at" not in state or state["runner_started_at"] is None


# ---- §4.8 FallbackEntry lifetime rule --------------------------------------


def test_reload_after_crash_clears_prior_fallback() -> None:
    """§4.8 lifetime rule: a successful re-load that returns method to a
    non-null vocabulary value MUST set fallback = null.
    """
    _client, kernel = _fresh_client()
    # First load
    kernel.observe_speculative_runner_load(_synthetic_load_success())
    # Crash
    kernel.observe_speculative_runner_generate(_synthetic_generate_crash())
    state = kernel.status_dict()["speculative_execution_status"]
    assert state["fallback"] is not None  # crash populated fallback
    # Re-load
    kernel.observe_speculative_runner_load(_synthetic_load_success())

    state = kernel.status_dict()["speculative_execution_status"]
    assert state["method"] == "assistant_drafter"
    # Fallback cleared by successful re-load
    assert state.get("fallback") is None
    # Counters reset to 0
    assert state.get("accepted_tokens", 0) == 0
    assert state.get("accepted_rounds", 0) == 0


def test_repeated_load_failures_increment_transition_count() -> None:
    """transition_count tracks the number of fallback transitions
    observed since the current runner_started_at; resets on successful
    load (§4.8 lifetime rule).
    """
    _client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(_synthetic_load_failure(pair_ok=False))
    state = kernel.status_dict()["speculative_execution_status"]
    assert state["fallback"]["transition_count"] == 1

    kernel.observe_speculative_runner_load(_synthetic_load_failure(pair_ok=False))
    state = kernel.status_dict()["speculative_execution_status"]
    assert state["fallback"]["transition_count"] == 2


# ---- meta: no-live-caller fixture (§6.2 honesty) --------------------------


def test_kernel_without_any_observe_calls_stays_spec_disabled() -> None:
    """§6.2 integration-reality note: a kernel that has never had
    observe_speculative_runner_load invoked MUST keep the surface in the
    §4.11.1 spec-disabled shape. This is the empirical guard that F-1.3
    does NOT introduce a parent-side spawn site.
    """
    client, _kernel = _fresh_client()

    payload = client.get(F1_ROUTE).json()
    assert payload["method"] is None
    assert payload["capability_label"] == "disabled"
    assert payload["runner_status"] == "unloaded"
    assert payload["missing_reason"] == "spec_explicitly_disabled"


def test_observe_unknown_runtime_family_is_noop() -> None:
    """Unknown runtime_family does not transition state. Defensive
    against future runner additions that haven't been mapped yet.
    """
    client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load({
        "ok": True,
        "runtime_family": "some-future-unmapped-runtime",
        "capability_label": "experimental",
        "load_mode": "loaded",
    })

    # State unchanged from §4.11.1
    payload = client.get(F1_ROUTE).json()
    assert payload["method"] is None
    assert payload["capability_label"] == "disabled"
    assert payload["runner_status"] == "unloaded"


# ---- end-to-end via HTTP route --------------------------------------------


def test_route_returns_active_shape_after_observe_load() -> None:
    client, kernel = _fresh_client()
    kernel.observe_speculative_runner_load(_synthetic_load_success())

    response = client.get(F1_ROUTE)
    assert response.status_code == 200
    payload = response.json()
    assert payload["method"] == "assistant_drafter"
    assert payload["runner_status"] == "deferred_cli_per_request"
    assert "cache_sharing" in payload
