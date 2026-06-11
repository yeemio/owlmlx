"""C1: gemma4 tool parser attach for vlm-loaded sessions (R1 Phase-2 spec §2)."""
from __future__ import annotations

from owlmlx.runtime.mlx_native_backend import (
    _attach_gemma_vlm_tool_parser,
    _parse_native_tool_calls,
)


class _BareTokenizer:
    """Mimics an mlx_vlm processor: no tool_parser attributes at all."""


def test_attach_installs_parser_and_markers_for_gemma4() -> None:
    tok = _BareTokenizer()
    attached = _attach_gemma_vlm_tool_parser(tok, model_id="gemma-4-12B-it")
    assert attached is True
    assert callable(tok.tool_parser)
    assert tok.tool_call_start == "<|tool_call>"
    assert tok.tool_call_end == "<tool_call|>"


def test_attached_parser_feeds_parse_native_tool_calls() -> None:
    tok = _BareTokenizer()
    _attach_gemma_vlm_tool_parser(tok, model_id="gemma-4-12B-it")
    text = (
        'before <|tool_call>call:write{content:<|"|>x<|"|>,'
        'path:<|"|>a.js<|"|>}<tool_call|> after'
    )
    tools = [{"type": "function", "function": {
        "name": "write", "description": "w",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"]}}}]
    parsed = _parse_native_tool_calls(tok, text, tools=tools)
    assert parsed.tool_calls, f"expected tool_calls, detail={parsed.detail}"
    assert parsed.tool_calls[0]["function"]["name"] == "write"
    assert not parsed.detail.get("tool_parser_missing")


def test_attach_skips_non_gemma_models() -> None:
    tok = _BareTokenizer()
    attached = _attach_gemma_vlm_tool_parser(tok, model_id="Qwen3.6-27B")
    assert attached is False
    assert not hasattr(tok, "tool_parser")


def test_attach_preserves_existing_parser() -> None:
    tok = _BareTokenizer()
    sentinel = lambda text, tools=None: []  # noqa: E731
    tok.tool_parser = sentinel
    attached = _attach_gemma_vlm_tool_parser(tok, model_id="gemma-4-12B-it")
    assert attached is False
    assert tok.tool_parser is sentinel
