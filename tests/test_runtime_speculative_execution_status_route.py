"""F-1.2 contract tests for the speculative_execution_status surface.

These tests pin down the §4.11.1 spec-disabled stub shape, the kernel's
top-level diagnostic placement, the contract.diagnostic_sections registration,
and the live read of GEMMA4_MTP_CAPABILITY_LABEL.

Source: docs/architect/design/F-1-spec.md §4.11.1 + §5.1.
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
