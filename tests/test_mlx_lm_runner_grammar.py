"""F-4.2a grammar plumbing tests (child runner side).

These cover the wiring contract for grammar-constrained decoding:
  * grammar spec is stripped from the mlx_lm kwargs (never leaks as an
    unknown generate_step kwarg);
  * a logits_processor is added only when a grammar spec is present
    (backward compatibility: absent grammar => byte-for-byte today's params);
  * the child-side builder produces a processor that actually masks logits
    (real xgrammar; skipped when xgrammar or a local tokenizer is absent).

Design ref: docs/architect/design/F-4-2-grammar-constrained-baseline-spec.md
"""

from __future__ import annotations

import os
import sys
import types

import pytest

from owlmlx.runtime.mlx_lm_runner import (
    _prepare_generation_params,
)


def _install_fake_sampler(monkeypatch):  # type: ignore[no-untyped-def]
    mlx_lm_module = types.ModuleType("mlx_lm")
    sample_utils_module = types.ModuleType("mlx_lm.sample_utils")

    def make_sampler(**kwargs):  # type: ignore[no-untyped-def]
        def sampler(*args, **inner_kwargs):  # type: ignore[no-untyped-def]
            return None

        return sampler

    sample_utils_module.make_sampler = make_sampler  # type: ignore[attr-defined]
    mlx_lm_module.sample_utils = sample_utils_module  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "mlx_lm", mlx_lm_module)
    monkeypatch.setitem(sys.modules, "mlx_lm.sample_utils", sample_utils_module)


# --- Cycle 1: grammar must not leak into mlx_lm kwargs -----------------------


def test_prepare_generation_params_strips_grammar_field() -> None:
    prepared = _prepare_generation_params(
        {"max_tokens": 4, "grammar": {"kind": "json_schema", "schema": {}}}
    )

    assert "grammar" not in prepared
    assert prepared["max_tokens"] == 4


def test_prepare_generation_params_without_grammar_is_unchanged() -> None:
    prepared = _prepare_generation_params({"max_tokens": 4})

    assert prepared == {"max_tokens": 4}
    assert "logits_processors" not in prepared


# --- Cycle 2: wiring grammar spec -> logits_processor ------------------------


def test_maybe_add_grammar_processor_is_noop_without_grammar() -> None:
    from owlmlx.runtime.mlx_lm_runner import _maybe_add_grammar_processor

    generation_params = {"max_tokens": 4}
    result = _maybe_add_grammar_processor(
        generation_params, params={"max_tokens": 4}, tokenizer=object()
    )

    assert "logits_processors" not in result


def test_maybe_add_grammar_processor_appends_processor_when_present(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import owlmlx.runtime.mlx_lm_runner as runner

    sentinel = object()

    def fake_builder(tokenizer, grammar_spec):  # type: ignore[no-untyped-def]
        return sentinel

    monkeypatch.setattr(runner, "_build_grammar_logits_processor", fake_builder)

    generation_params: dict = {"max_tokens": 4}
    result = runner._maybe_add_grammar_processor(
        generation_params,
        params={"grammar": {"kind": "json_schema", "schema": {}}},
        tokenizer=object(),
    )

    assert result["logits_processors"] == [sentinel]


def test_maybe_add_grammar_processor_preserves_existing_processors(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import owlmlx.runtime.mlx_lm_runner as runner

    sentinel = object()
    existing = object()
    monkeypatch.setattr(
        runner, "_build_grammar_logits_processor", lambda t, g: sentinel
    )

    result = runner._maybe_add_grammar_processor(
        {"logits_processors": [existing]},
        params={"grammar": {"kind": "json_schema", "schema": {}}},
        tokenizer=object(),
    )

    assert result["logits_processors"] == [existing, sentinel]


# --- Cycle 3: real builder masks logits (xgrammar + tokenizer) ---------------

_TOKENIZER_DIR = os.environ.get(
    "OWLMLX_F4_TEST_TOKENIZER", "/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B-4bit"
)


def _load_real_tokenizer():  # type: ignore[no-untyped-def]
    pytest.importorskip("xgrammar")
    pytest.importorskip("mlx.core")
    if not os.path.isdir(_TOKENIZER_DIR):
        pytest.skip(f"tokenizer dir not present: {_TOKENIZER_DIR}")
    transformers = pytest.importorskip("transformers")
    return transformers.AutoTokenizer.from_pretrained(_TOKENIZER_DIR)


def test_build_grammar_processor_masks_logits_for_json_schema() -> None:
    import mlx.core as mx

    from owlmlx.runtime.mlx_lm_runner import _build_grammar_logits_processor

    hf_tok = _load_real_tokenizer()
    schema = {
        "type": "object",
        "properties": {"task_id": {"type": "string"}},
        "required": ["task_id"],
        "additionalProperties": False,
    }
    processor = _build_grammar_logits_processor(
        hf_tok, {"kind": "json_schema", "schema": schema}
    )

    # First call: prompt-tail token (offset only, accepts nothing).
    vocab = 248320
    logits0 = mx.zeros((1, vocab))
    tokens0 = mx.array([7])  # a lone prompt-tail token
    out0 = processor(tokens0, logits0)

    # The very next step must be masked: a JSON object can only start with a
    # small set of tokens, so the mask sets most positions to -inf.
    masked = mx.isneginf(out0).sum().item()
    allowed = vocab - masked
    assert masked > 0, "grammar applied no mask"
    assert allowed >= 1, "grammar masked every token"
    assert allowed < vocab, "grammar left all tokens allowed (no constraint)"


# --- Cycle 5: backend forwards grammar through to the child as a param -------


def test_backend_stream_generate_forwards_grammar_in_params(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """The subprocess backend must pass a `grammar` kwarg through to the child
    runner inside `params`. The backend itself is grammar-agnostic (kwargs ->
    params), and this guards against a future kwargs filter silently dropping
    grammar. No subprocess is spawned; the session + exchange are stubbed.
    """
    from owlmlx.runtime import MlxLmSubprocessBackend

    backend = MlxLmSubprocessBackend()
    captured: dict = {}

    monkeypatch.setattr(
        backend, "_ensure_session", lambda model_id, reason_prefix="": (object(), None)
    )

    def fake_exchange(session, payload):  # type: ignore[no-untyped-def]
        captured["payload"] = payload
        return iter(())

    monkeypatch.setattr(backend, "_stream_exchange", fake_exchange)

    grammar = {"kind": "json_schema", "schema": {"type": "object"}}
    list(
        backend.stream_generate(
            "some-model", "hello", grammar=grammar, temperature=0.3
        )
    )

    assert captured["payload"]["params"]["grammar"] == grammar
    assert captured["payload"]["params"]["temperature"] == 0.3
