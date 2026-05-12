"""Tests for `pre_load_check` — PR #649-shaped admission entrypoint."""

from __future__ import annotations

from owlmlx import pre_load_check
from owlmlx.nonresident_model_admission_policy import (
    NonResidentModelAdmissionPolicy,
    build_nonresident_model_admission_policy,
)


def test_returns_admission_policy_instance() -> None:
    result = pre_load_check("some-model")
    assert isinstance(result, NonResidentModelAdmissionPolicy)


def test_matches_underlying_builder_for_same_inputs() -> None:
    a = pre_load_check("model-a")
    b = build_nonresident_model_admission_policy(model_id="model-a")
    assert a.decision == b.decision
    assert a.reason_code == b.reason_code
    assert a.confidence == b.confidence


def test_unknown_or_missing_runtime_signals_returns_one_of_the_four_outcomes() -> None:
    result = pre_load_check("model-x")
    # PR #649's contract: every check produces one of four decisions.
    assert result.decision in {"admit_and_load", "defer", "reject", "unknown"}


def test_passes_request_context_class_through() -> None:
    result = pre_load_check("model-a", request_context_class="standard")
    assert result.inputs.get("request_context_class") == "standard"


def test_passes_known_loadable_through() -> None:
    result = pre_load_check(
        "model-a",
        known_loadable_model_ids=("model-a", "model-b"),
    )
    assert "model-a" in tuple(result.inputs.get("known_loadable_model_ids", ()))


def test_exposed_from_owlmlx_top_namespace() -> None:
    import owlmlx
    assert hasattr(owlmlx, "pre_load_check")
    assert owlmlx.pre_load_check is pre_load_check
