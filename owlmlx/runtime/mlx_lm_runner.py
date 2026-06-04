"""Persistent child-process runner for mlx-lm execution.

This module is executed in an isolated Python process. It is the only place in
owlmlx runtime where ``mlx_lm`` is imported for real execution. The parent
runtime communicates through stdin/stdout JSON lines so Metal/Objective-C
crashes cannot terminate the parent process.
"""

from __future__ import annotations

import json
import gc
import os
import sys
import time
from collections.abc import Callable
from contextlib import redirect_stdout
from typing import Any


_SAMPLER_PARAM_NAMES = (
    "temp",
    "top_p",
    "min_p",
    "min_tokens_to_keep",
    "top_k",
    "xtc_probability",
    "xtc_threshold",
    "xtc_special_tokens",
)

_PREFILL_CHUNK_TOKENS_PARAM = "prefill_chunk_tokens"
_PREFILL_CHUNK_TOKENS_ENV = "OWLMLX_PREFILL_CHUNK_TOKENS"
_PREFILL_PROGRESS_EVENTS_PARAM = "prefill_progress_events"


def _positive_int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


def _safe_usage_token_count(tokenizer: Any, text: str, *, is_prompt: bool) -> int | None:
    """Best-effort non-stream usage token count; never raises into generation.

    The prompt count is bos-aware (avoid double-counting BOS); the completion
    count uses no special tokens. ``mlx_lm.generate`` returns only text on the
    non-stream path, so this re-encode is the count source there (the stream path
    stays exact).
    """
    try:
        if is_prompt:
            bos = getattr(tokenizer, "bos_token", None)
            add_special = bos is None or not str(text).startswith(str(bos))
        else:
            add_special = False
        try:
            return len(tokenizer.encode(text, add_special_tokens=add_special))
        except TypeError:
            return len(tokenizer.encode(text))
    except Exception:
        return None


def _stop_strings_from_params(params: dict[str, Any]) -> tuple[str, ...]:
    raw_stop = params.get("stop")
    if raw_stop is None:
        return ()
    if isinstance(raw_stop, str):
        candidates = (raw_stop,)
    elif isinstance(raw_stop, list):
        candidates = tuple(item for item in raw_stop if isinstance(item, str))
    else:
        return ()
    return tuple(dict.fromkeys(item for item in candidates if item))


def _chat_template_kwargs_from_params(params: dict[str, Any]) -> dict[str, Any]:
    raw_kwargs = params.get("chat_template_kwargs")
    if not isinstance(raw_kwargs, dict):
        return {}
    return {
        str(key): value
        for key, value in raw_kwargs.items()
        if isinstance(key, str) and key
    }


def _truncate_at_stop_strings(
    text: str,
    stop_strings: tuple[str, ...],
) -> tuple[str, bool]:
    if not stop_strings:
        return text, False
    earliest: int | None = None
    for marker in stop_strings:
        index = text.find(marker)
        if index >= 0:
            earliest = index if earliest is None else min(earliest, index)
    if earliest is None:
        return text, False
    return text[:earliest], True


class _StopStringStreamFilter:
    def __init__(self, stop_strings: tuple[str, ...]) -> None:
        self.stop_strings = stop_strings
        self.max_marker_len = max((len(marker) for marker in stop_strings), default=0)
        self.buffer = ""
        self.stopped = False

    def feed(self, text: str) -> tuple[str, bool]:
        if self.stopped or not text:
            return "", self.stopped
        if not self.stop_strings:
            return text, False

        self.buffer += text
        truncated, found = _truncate_at_stop_strings(self.buffer, self.stop_strings)
        if found:
            self.stopped = True
            self.buffer = ""
            return truncated, True

        retain = max(self.max_marker_len - 1, 0)
        if retain == 0 or len(self.buffer) <= retain:
            return "", False
        emit = self.buffer[:-retain]
        self.buffer = self.buffer[-retain:]
        return emit, False

    def flush(self) -> str:
        if self.stopped or not self.buffer:
            return ""
        text = self.buffer
        self.buffer = ""
        return text


def _prepare_generation_params(params: dict[str, Any]) -> dict[str, Any]:
    """Adapt API-facing sampling params to the installed ``mlx_lm`` API.

    Current ``mlx_lm.generate`` forwards unknown keyword arguments to
    ``generate_step``. OpenAI-compatible callers send ``temperature`` and
    ``top_p``, while this mlx-lm version expects those to be wrapped in a
    sampler callable.
    """

    prepared = dict(params)
    prepared.pop("stop", None)
    prepared.pop("chat_template_kwargs", None)
    # Grammar is handled child-side via a logits_processor (see
    # _maybe_add_grammar_processor); it must never leak to mlx_lm as an
    # unknown generate_step kwarg.
    prepared.pop("grammar", None)
    prepared.pop(_PREFILL_PROGRESS_EVENTS_PARAM, None)
    raw_prefill_chunk_tokens = prepared.pop(_PREFILL_CHUNK_TOKENS_PARAM, None)
    if raw_prefill_chunk_tokens is None and "prefill_step_size" not in prepared:
        raw_prefill_chunk_tokens = os.environ.get(_PREFILL_CHUNK_TOKENS_ENV)
    if raw_prefill_chunk_tokens is not None:
        prefill_step_size = _positive_int_or_none(raw_prefill_chunk_tokens)
        if prefill_step_size is not None:
            prepared["prefill_step_size"] = prefill_step_size
    sampler_kwargs: dict[str, Any] = {}

    if "temperature" in prepared:
        sampler_kwargs["temp"] = prepared.pop("temperature")
    if "temp" in prepared:
        sampler_kwargs["temp"] = prepared.pop("temp")

    for name in _SAMPLER_PARAM_NAMES:
        if name in prepared:
            sampler_kwargs[name] = prepared.pop(name)

    if sampler_kwargs:
        from mlx_lm.sample_utils import make_sampler  # noqa: PLC0415

        prepared["sampler"] = make_sampler(**sampler_kwargs)

    return prepared


class GrammarCompileError(ValueError):
    """Raised child-side when a grammar spec cannot be compiled."""


# Cap on consecutive whitespace tokens in JSON-schema grammars. Prevents the
# unbounded-newline loop some models fall into after "{" when whitespace is
# unconstrained. Overridable per request via grammar_spec["max_whitespace_cnt"].
DEFAULT_GRAMMAR_MAX_WHITESPACE = 16


def _resolve_hf_tokenizer_for_xgrammar(tokenizer: Any) -> Any:
    """Return the transformers tokenizer xgrammar's from_huggingface accepts.

    xgrammar wants a ``transformers.PreTrainedTokenizerBase``. Two cases:

    * A raw HF tokenizer (e.g. ``Qwen2Tokenizer``) already IS that base — use it
      directly. Do NOT unwrap its ``._tokenizer``; that is the inner Rust
      ``tokenizers.Tokenizer`` which xgrammar rejects.
    * mlx-lm's ``TokenizerWrapper`` is NOT a base; its ``._tokenizer`` is the
      real HF tokenizer — unwrap one level.
    """
    try:
        from transformers import PreTrainedTokenizerBase  # noqa: PLC0415

        if isinstance(tokenizer, PreTrainedTokenizerBase):
            return tokenizer
    except ImportError:
        pass
    inner = getattr(tokenizer, "_tokenizer", None)
    if inner is not None:
        return inner
    return tokenizer


def _build_grammar_logits_processor(tokenizer: Any, grammar_spec: dict[str, Any]) -> Any:
    """Build an mlx ``logits_processor`` that constrains decoding to a grammar.

    Runs child-side: the xgrammar matcher holds a non-serializable C++ state and
    cannot cross the parent/child IPC boundary, so the parent ships the
    serializable ``grammar_spec`` (a JSON schema or a structural-tag envelope)
    and the matcher is reconstructed here.

    ``grammar_spec`` shape::

        {"kind": "json_schema", "schema": {...}}
        {"kind": "structural_tag", "schema": {...}, "begin": "</thinking>", "end": ""}

    The xgrammar matcher is compiled lazily on the first processor call, using
    ``logits.shape[-1]`` as the authoritative vocab size — that is the model's
    real logits dimension, which can exceed the tokenizer's nominal vocab (e.g.
    Qwen3.6 pads to 248320 vs a 248077-token tokenizer); using the tokenizer
    size would make the bitmask fail to broadcast against the logits.

    Verified behaviour (see scripts/probe/f4_grammar_feasibility.py and
    f4_grammar_per_family_verify.py):
      * mlx-lm hands the prompt-tail token to the first processor call, so the
        first call records the offset and accepts nothing;
      * later calls accept the newly generated tokens, then mask the next step.
    """
    import json as _json  # noqa: PLC0415

    import mlx.core as mx  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415
    import xgrammar as xgr  # noqa: PLC0415

    hf_tok = _resolve_hf_tokenizer_for_xgrammar(tokenizer)
    kind = str(grammar_spec.get("kind") or "json_schema")
    schema = grammar_spec.get("schema")

    state: dict[str, Any] = {
        "matcher": None,
        "bitmask": None,
        "vocab_size": None,
        "last_seen_len": -1,
    }

    def _ensure_compiled(vocab_size: int) -> None:
        try:
            tokenizer_info = xgr.TokenizerInfo.from_huggingface(
                hf_tok, vocab_size=vocab_size
            )
            compiler = xgr.GrammarCompiler(tokenizer_info)
            if kind == "json_schema":
                # Cap consecutive whitespace. With xgrammar's default
                # any_whitespace=True an unconstrained model (observed on
                # gemma-4-31b at temp 0) can emit an unbounded run of newlines
                # after "{" and never reach a key, burning max_tokens into a
                # whitespace loop. A small cap still allows pretty-printing.
                max_ws = int(grammar_spec.get("max_whitespace_cnt") or DEFAULT_GRAMMAR_MAX_WHITESPACE)
                compiled = compiler.compile_json_schema(
                    _json.dumps(schema), max_whitespace_cnt=max_ws
                )
            elif kind == "structural_tag":
                begin = str(grammar_spec.get("begin") or "")
                end = str(grammar_spec.get("end") or "")
                item = xgr.StructuralTagItem(
                    begin=begin, schema=_json.dumps(schema), end=end
                )
                compiled = compiler.compile_structural_tag([item], [begin])
            elif kind == "ebnf":
                ebnf = str(grammar_spec.get("ebnf") or "")
                compiled = compiler.compile_grammar(xgr.Grammar.from_ebnf(ebnf))
            else:
                raise GrammarCompileError(f"unknown grammar kind: {kind!r}")
        except GrammarCompileError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise GrammarCompileError(
                f"grammar_compile_failed: {type(exc).__name__}: {exc}"
            ) from exc
        state["matcher"] = xgr.GrammarMatcher(compiled)
        state["bitmask"] = xgr.allocate_token_bitmask(1, vocab_size)
        state["vocab_size"] = vocab_size

    def processor(tokens: Any, logits: Any) -> Any:
        vocab_size = int(logits.shape[-1])
        if state["matcher"] is None:
            _ensure_compiled(vocab_size)
        matcher = state["matcher"]
        cur_len = int(tokens.shape[0])
        if state["last_seen_len"] < 0:
            # First call carries the prompt-tail token, not a generation.
            state["last_seen_len"] = cur_len
        elif cur_len > state["last_seen_len"]:
            new_ids = tokens[state["last_seen_len"] : cur_len].tolist()
            for tok_id in new_ids:
                if matcher.is_terminated():
                    break
                if not matcher.accept_token(int(tok_id)):
                    state["last_seen_len"] = cur_len
                    return logits
            state["last_seen_len"] = cur_len

        if matcher.is_terminated():
            return logits

        bitmask = state["bitmask"]
        matcher.fill_next_token_bitmask(bitmask)
        flat_bytes = bitmask.numpy().view(np.uint8).reshape(-1)
        allowed = np.unpackbits(flat_bytes, bitorder="little")[:vocab_size]
        allowed_mx = mx.array(allowed.astype(np.bool_)).reshape((1, vocab_size))
        neg_inf = mx.full(logits.shape, -mx.inf, dtype=logits.dtype)
        return mx.where(allowed_mx, logits, neg_inf)

    return processor


def _maybe_add_grammar_processor(
    generation_params: dict[str, Any],
    params: dict[str, Any],
    tokenizer: Any,
) -> dict[str, Any]:
    """Append a grammar logits_processor to ``generation_params`` if requested.

    No-op when ``params`` carries no ``grammar`` spec, preserving today's
    behavior byte-for-byte. Mutates and returns ``generation_params``.
    """
    grammar_spec = params.get("grammar")
    if not grammar_spec:
        return generation_params
    processor = _build_grammar_logits_processor(tokenizer, grammar_spec)
    processors = list(generation_params.get("logits_processors") or [])
    processors.append(processor)
    generation_params["logits_processors"] = processors
    return generation_params


def _bool_param(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _prefill_progress_requested(params: dict[str, Any]) -> bool:
    if _PREFILL_PROGRESS_EVENTS_PARAM in params:
        return _bool_param(params.get(_PREFILL_PROGRESS_EVENTS_PARAM))
    if _PREFILL_CHUNK_TOKENS_PARAM in params:
        return True
    return bool(os.environ.get(_PREFILL_CHUNK_TOKENS_ENV))


def _make_prefill_progress_callback(
    *,
    action: str,
    model_id: str,
    request_start: float,
    prompt_character_count: int,
    message_count: int | None = None,
    prefill_step_size: int | None = None,
) -> tuple[Callable[[Any, Any], None], dict[str, Any]]:
    state: dict[str, Any] = {"count": 0, "last": None}

    def callback(processed: Any, total: Any) -> None:
        processed_int = _positive_int_or_none(processed) or 0
        total_int = _positive_int_or_none(total) or 0
        state["count"] = int(state["count"]) + 1
        payload: dict[str, Any] = {
            "ok": True,
            "action": action,
            "event": "prefill_progress",
            "model_id": model_id,
            "pid": os.getpid(),
            "processed": processed_int,
            "total": total_int,
            "ratio": round(processed_int / total_int, 6) if total_int else None,
            "prefill_sequence": state["count"],
            "prompt_character_count": prompt_character_count,
            "timing": {
                "prefill_progress_elapsed_ms": _elapsed_ms(request_start),
            },
        }
        if message_count is not None:
            payload["message_count"] = message_count
        if prefill_step_size is not None:
            payload["prefill_step_size"] = prefill_step_size
        state["last"] = payload
        _emit(payload)

    return callback, state


def _prepare_tokenizer_config(config: dict[str, Any]) -> dict[str, Any]:
    """Adapt JSON-safe tokenizer config to ``transformers`` objects.

    Some experimental model adapters are known to the local ``mlx_lm`` fork but
    not to the installed ``transformers`` auto config mapping. The parent can
    pass a JSON-safe ``pretrained_config`` block to avoid AutoTokenizer falling
    back through an incompatible config path, without mutating the model files.
    """

    prepared = dict(config)
    pretrained_config = prepared.pop("pretrained_config", None)
    if isinstance(pretrained_config, dict):
        from transformers import PreTrainedConfig  # noqa: PLC0415

        config_obj = PreTrainedConfig()
        for key, value in pretrained_config.items():
            if isinstance(key, str) and key:
                setattr(config_obj, key, value)
        prepared["config"] = config_obj
    return prepared


def _fallback_prompt_from_messages(messages: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"{str(message.get('role') or 'user')}: {str(message.get('content') or '')}"
        for message in messages
    )


def _prompt_from_messages(
    tokenizer: Any,
    messages: list[dict[str, Any]],
    *,
    chat_template_kwargs: dict[str, Any] | None = None,
) -> str:
    template_kwargs = dict(chat_template_kwargs or {})
    if hasattr(tokenizer, "apply_chat_template"):
        return str(
            tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                **template_kwargs,
            )
        )
    return _fallback_prompt_from_messages(messages)


def _parse_request(line: str) -> dict[str, Any]:
    try:
        return json.loads(line or "{}")
    except Exception as exc:
        return {"_parse_error": str(exc)}


def _emit(payload: dict[str, Any]) -> None:
    sys.__stdout__.write(json.dumps(payload) + "\n")
    sys.__stdout__.flush()


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def main() -> int:
    current_model_id: str | None = None
    model: Any | None = None
    tokenizer: Any | None = None
    generation_count = 0

    for line in sys.stdin:
        request = _parse_request(line.strip())
        if "_parse_error" in request:
            _emit({"ok": False, "error": request["_parse_error"]})
            continue

        action = str(request.get("action") or "").strip().lower()
        model_id = request.get("model_id")
        prompt = request.get("prompt", "")
        messages = list(request.get("messages") or [])
        params = dict(request.get("params") or {})
        tokenizer_config = _prepare_tokenizer_config(
            dict(request.get("tokenizer_config") or {})
        )
        model_config = dict(request.get("model_config") or {})

        try:
            if action == "load":
                if not model_id:
                    _emit({"ok": False, "error": "model_id is required"})
                    continue
                if current_model_id and current_model_id != model_id:
                    _emit(
                        {
                            "ok": False,
                            "error": (
                                "runner already loaded a different model: "
                                f"{current_model_id}"
                            ),
                        }
                    )
                    continue

                import mlx_lm  # noqa: PLC0415

                with redirect_stdout(sys.stderr):
                    model, tokenizer = mlx_lm.load(
                        str(model_id),
                        tokenizer_config=tokenizer_config or None,
                        model_config=model_config or None,
                    )
                current_model_id = str(model_id)
                generation_count = 0
                _emit(
                    {
                        "ok": True,
                        "action": "load",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                    }
                )
                continue

            if action == "generate":
                if not current_model_id or model is None or tokenizer is None:
                    _emit({"ok": False, "error": "no model loaded"})
                    continue
                if model_id and str(model_id) != current_model_id:
                    _emit(
                        {
                            "ok": False,
                            "error": (
                                f"loaded model is {current_model_id}, "
                                f"not {model_id}"
                            ),
                        }
                    )
                    continue

                import mlx_lm  # noqa: PLC0415

                stop_strings = _stop_strings_from_params(params)
                generation_params = _maybe_add_grammar_processor(
                    _prepare_generation_params(params), params, tokenizer
                )
                with redirect_stdout(sys.stderr):
                    text = mlx_lm.generate(
                        model,
                        tokenizer,
                        prompt=str(prompt),
                        **generation_params,
                    )
                text, stop_hit = _truncate_at_stop_strings(str(text), stop_strings)
                generation_count += 1
                _emit(
                    {
                        "ok": True,
                        "action": "generate",
                        "model_id": current_model_id,
                        "text": text,
                        "finish_reason": "stop" if stop_hit else "stop",
                        "pid": os.getpid(),
                        "generation_count": generation_count,
                        "prompt_tokens": _safe_usage_token_count(
                            tokenizer, str(prompt), is_prompt=True
                        ),
                        "completion_tokens": _safe_usage_token_count(
                            tokenizer, text, is_prompt=False
                        ),
                    }
                )
                continue

            if action == "generate_batch":
                if not current_model_id or model is None or tokenizer is None:
                    _emit({"ok": False, "error": "no model loaded"})
                    continue
                if model_id and str(model_id) != current_model_id:
                    _emit(
                        {
                            "ok": False,
                            "error": (
                                f"loaded model is {current_model_id}, "
                                f"not {model_id}"
                            ),
                        }
                    )
                    continue

                import mlx_lm  # noqa: PLC0415

                requests = list(request.get("requests") or [])
                results: list[dict[str, Any]] = []
                with redirect_stdout(sys.stderr):
                    for item in requests:
                        payload = item if isinstance(item, dict) else {}
                        payload_params = dict(payload.get("params") or {})
                        stop_strings = _stop_strings_from_params(payload_params)
                        text = mlx_lm.generate(
                            model,
                            tokenizer,
                            prompt=str(payload.get("prompt", "")),
                            **_prepare_generation_params(
                                payload_params
                            ),
                        )
                        text, stop_hit = _truncate_at_stop_strings(
                            str(text),
                            stop_strings,
                        )
                        results.append(
                            {
                                "ok": True,
                                "text": text,
                                "finish_reason": "stop" if stop_hit else "stop",
                            }
                        )
                generation_count += 1
                _emit(
                    {
                        "ok": True,
                        "action": "generate_batch",
                        "model_id": current_model_id,
                        "results": results,
                        "batch_size": len(results),
                        "pid": os.getpid(),
                        "generation_count": generation_count,
                    }
                )
                continue

            if action == "generate_messages":
                if not current_model_id or model is None or tokenizer is None:
                    _emit({"ok": False, "error": "no model loaded"})
                    continue
                if model_id and str(model_id) != current_model_id:
                    _emit(
                        {
                            "ok": False,
                            "error": (
                                f"loaded model is {current_model_id}, "
                                f"not {model_id}"
                            ),
                        }
                    )
                    continue

                import mlx_lm  # noqa: PLC0415

                rendered_prompt = _prompt_from_messages(
                    tokenizer,
                    messages,
                    chat_template_kwargs=_chat_template_kwargs_from_params(params),
                )
                stop_strings = _stop_strings_from_params(params)
                generation_params = _maybe_add_grammar_processor(
                    _prepare_generation_params(params), params, tokenizer
                )
                with redirect_stdout(sys.stderr):
                    text = mlx_lm.generate(
                        model,
                        tokenizer,
                        prompt=rendered_prompt,
                        **generation_params,
                    )
                text, stop_hit = _truncate_at_stop_strings(str(text), stop_strings)
                generation_count += 1
                _emit(
                    {
                        "ok": True,
                        "action": "generate_messages",
                        "model_id": current_model_id,
                        "text": text,
                        "finish_reason": "stop" if stop_hit else "stop",
                        "pid": os.getpid(),
                        "generation_count": generation_count,
                        "message_count": len(messages),
                        "prompt_tokens": _safe_usage_token_count(
                            tokenizer, str(rendered_prompt), is_prompt=True
                        ),
                        "completion_tokens": _safe_usage_token_count(
                            tokenizer, text, is_prompt=False
                        ),
                    }
                )
                continue

            if action == "stream_generate":
                if not current_model_id or model is None or tokenizer is None:
                    _emit({"ok": False, "error": "no model loaded"})
                    continue
                if model_id and str(model_id) != current_model_id:
                    _emit(
                        {
                            "ok": False,
                            "error": (
                                f"loaded model is {current_model_id}, "
                                f"not {model_id}"
                            ),
                        }
                    )
                    continue

                import mlx_lm  # noqa: PLC0415

                request_start = time.perf_counter()
                prompt_render_start = time.perf_counter()
                rendered_prompt = str(prompt)
                prompt_render_ms = _elapsed_ms(prompt_render_start)
                sequence = 0
                prompt_tokens = None
                completion_tokens = 0
                finish_reason = "stop"
                stop_strings = _stop_strings_from_params(params)
                stop_filter = _StopStringStreamFilter(stop_strings)
                first_response_ms = None
                first_visible_token_ms = None
                generation_params = _maybe_add_grammar_processor(
                    _prepare_generation_params(params), params, tokenizer
                )
                prefill_progress_state: dict[str, Any] = {"count": 0, "last": None}
                if _prefill_progress_requested(params):
                    prefill_progress_callback, prefill_progress_state = (
                        _make_prefill_progress_callback(
                            action="stream_event",
                            model_id=current_model_id,
                            request_start=request_start,
                            prompt_character_count=len(rendered_prompt),
                            prefill_step_size=generation_params.get("prefill_step_size")
                            if isinstance(
                                generation_params.get("prefill_step_size"),
                                int,
                            )
                            else None,
                        )
                    )
                    generation_params["prompt_progress_callback"] = prefill_progress_callback
                with redirect_stdout(sys.stderr):
                    stream_call_start = time.perf_counter()
                    for response in mlx_lm.stream_generate(
                        model,
                        tokenizer,
                        prompt=rendered_prompt,
                        **generation_params,
                    ):
                        if first_response_ms is None:
                            first_response_ms = _elapsed_ms(request_start)
                        prompt_tokens = getattr(response, "prompt_tokens", prompt_tokens)
                        completion_tokens = int(
                            getattr(response, "generation_tokens", completion_tokens) or 0
                        )
                        finish_reason = str(
                            getattr(response, "finish_reason", finish_reason) or finish_reason
                        )
                        text, stop_hit = stop_filter.feed(
                            str(getattr(response, "text", "") or "")
                        )
                        if stop_hit:
                            finish_reason = "stop"
                        if not text and not stop_hit:
                            continue
                        if text:
                            if first_visible_token_ms is None:
                                first_visible_token_ms = _elapsed_ms(request_start)
                            sequence += 1
                            _emit(
                                {
                                    "ok": True,
                                    "action": "stream_event",
                                    "event": "token",
                                    "model_id": current_model_id,
                                    "text": text,
                                    "pid": os.getpid(),
                                    "sequence": sequence,
                                    "prompt_tokens": prompt_tokens,
                                    "completion_tokens": completion_tokens,
                                    "finish_reason": finish_reason,
                                    "timing": {
                                        "first_response_ms": first_response_ms,
                                        "first_visible_token_ms": first_visible_token_ms,
                                    },
                                }
                            )
                        if stop_hit:
                            break
                    tail = stop_filter.flush()
                    if tail:
                        if first_visible_token_ms is None:
                            first_visible_token_ms = _elapsed_ms(request_start)
                        sequence += 1
                        _emit(
                            {
                                "ok": True,
                                "action": "stream_event",
                                "event": "token",
                                "model_id": current_model_id,
                                "text": tail,
                                "pid": os.getpid(),
                                "sequence": sequence,
                                "prompt_tokens": prompt_tokens,
                                "completion_tokens": completion_tokens,
                                "finish_reason": finish_reason,
                                "timing": {
                                    "first_response_ms": first_response_ms,
                                    "first_visible_token_ms": first_visible_token_ms,
                                },
                            }
                        )
                generation_count += 1
                timing = {
                    "surface": "owlmlx.child_stream_timing",
                    "version": "v1",
                    "prompt_render_ms": prompt_render_ms,
                    "prompt_character_count": len(rendered_prompt),
                    "chat_template_applied": False,
                    "stream_call_start_ms": round(
                        (stream_call_start - request_start) * 1000,
                        3,
                    ),
                    "first_response_ms": first_response_ms,
                    "first_visible_token_ms": first_visible_token_ms,
                    "stream_wall_ms": _elapsed_ms(request_start),
                    "prefill_progress_event_count": prefill_progress_state["count"],
                    "prefill_step_size": generation_params.get("prefill_step_size"),
                }
                _emit(
                    {
                        "ok": True,
                        "runtime_owned_terminal_earlier_earlier_boundary": True,
                        "action": "stream_runtime_owned_terminal_earlier_earlier_boundary",
                        "terminal_action": "stream_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "runtime_owned_terminal_earlier_boundary": True,
                        "action": "stream_runtime_owned_terminal_earlier_boundary",
                        "terminal_action": "stream_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "runtime_owned_terminal_boundary": True,
                        "action": "stream_runtime_owned_terminal_boundary",
                        "terminal_action": "stream_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "runtime_owned_terminal_leading_discriminator": True,
                        "action": "stream_runtime_owned_terminal_leading_discriminator",
                        "terminal_action": "stream_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "runtime_owned_terminal_notice_discriminator": True,
                        "action": "stream_runtime_owned_terminal_notice_discriminator",
                        "terminal_action": "stream_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "terminal_notice_lead": True,
                        "action": "stream_terminal_notice_lead",
                        "terminal_action": "stream_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "terminal_notice": True,
                        "action": "stream_terminal_notice",
                        "terminal_action": "stream_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "action": "stream_done",
                        "event": "done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "generation_count": generation_count,
                        "sequence": sequence,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "finish_reason": finish_reason,
                        "timing": timing,
                    }
                )
                continue

            if action == "stream_generate_messages":
                if not current_model_id or model is None or tokenizer is None:
                    _emit({"ok": False, "error": "no model loaded"})
                    continue
                if model_id and str(model_id) != current_model_id:
                    _emit(
                        {
                            "ok": False,
                            "error": (
                                f"loaded model is {current_model_id}, "
                                f"not {model_id}"
                            ),
                        }
                    )
                    continue

                import mlx_lm  # noqa: PLC0415

                request_start = time.perf_counter()
                chat_template_kwargs = _chat_template_kwargs_from_params(params)
                prompt_render_start = time.perf_counter()
                rendered_prompt = _prompt_from_messages(
                    tokenizer,
                    messages,
                    chat_template_kwargs=chat_template_kwargs,
                )
                prompt_render_ms = _elapsed_ms(prompt_render_start)
                sequence = 0
                prompt_tokens = None
                completion_tokens = 0
                finish_reason = "stop"
                stop_strings = _stop_strings_from_params(params)
                stop_filter = _StopStringStreamFilter(stop_strings)
                first_response_ms = None
                first_visible_token_ms = None
                generation_params = _maybe_add_grammar_processor(
                    _prepare_generation_params(params), params, tokenizer
                )
                prefill_progress_state: dict[str, Any] = {"count": 0, "last": None}
                if _prefill_progress_requested(params):
                    prefill_progress_callback, prefill_progress_state = (
                        _make_prefill_progress_callback(
                            action="stream_message_event",
                            model_id=current_model_id,
                            request_start=request_start,
                            prompt_character_count=len(rendered_prompt),
                            message_count=len(messages),
                            prefill_step_size=generation_params.get("prefill_step_size")
                            if isinstance(
                                generation_params.get("prefill_step_size"),
                                int,
                            )
                            else None,
                        )
                    )
                    generation_params["prompt_progress_callback"] = prefill_progress_callback
                with redirect_stdout(sys.stderr):
                    stream_call_start = time.perf_counter()
                    for response in mlx_lm.stream_generate(
                        model,
                        tokenizer,
                        prompt=rendered_prompt,
                        **generation_params,
                    ):
                        if first_response_ms is None:
                            first_response_ms = _elapsed_ms(request_start)
                        prompt_tokens = getattr(response, "prompt_tokens", prompt_tokens)
                        completion_tokens = int(
                            getattr(response, "generation_tokens", completion_tokens) or 0
                        )
                        finish_reason = str(
                            getattr(response, "finish_reason", finish_reason) or finish_reason
                        )
                        text, stop_hit = stop_filter.feed(
                            str(getattr(response, "text", "") or "")
                        )
                        if stop_hit:
                            finish_reason = "stop"
                        if not text and not stop_hit:
                            continue
                        if text:
                            if first_visible_token_ms is None:
                                first_visible_token_ms = _elapsed_ms(request_start)
                            sequence += 1
                            _emit(
                                {
                                    "ok": True,
                                    "action": "stream_message_event",
                                    "event": "token",
                                    "model_id": current_model_id,
                                    "text": text,
                                    "pid": os.getpid(),
                                    "sequence": sequence,
                                    "prompt_tokens": prompt_tokens,
                                    "completion_tokens": completion_tokens,
                                    "finish_reason": finish_reason,
                                    "message_count": len(messages),
                                    "timing": {
                                        "first_response_ms": first_response_ms,
                                        "first_visible_token_ms": first_visible_token_ms,
                                    },
                                }
                            )
                        if stop_hit:
                            break
                    tail = stop_filter.flush()
                    if tail:
                        if first_visible_token_ms is None:
                            first_visible_token_ms = _elapsed_ms(request_start)
                        sequence += 1
                        _emit(
                            {
                                "ok": True,
                                "action": "stream_message_event",
                                "event": "token",
                                "model_id": current_model_id,
                                "text": tail,
                                "pid": os.getpid(),
                                "sequence": sequence,
                                "prompt_tokens": prompt_tokens,
                                "completion_tokens": completion_tokens,
                                "finish_reason": finish_reason,
                                "message_count": len(messages),
                                "timing": {
                                    "first_response_ms": first_response_ms,
                                    "first_visible_token_ms": first_visible_token_ms,
                                },
                            }
                        )
                generation_count += 1
                timing = {
                    "surface": "owlmlx.child_stream_timing",
                    "version": "v1",
                    "prompt_render_ms": prompt_render_ms,
                    "prompt_character_count": len(rendered_prompt),
                    "chat_template_applied": True,
                    "chat_template_kwarg_keys": sorted(chat_template_kwargs),
                    "stream_call_start_ms": round(
                        (stream_call_start - request_start) * 1000,
                        3,
                    ),
                    "first_response_ms": first_response_ms,
                    "first_visible_token_ms": first_visible_token_ms,
                    "stream_wall_ms": _elapsed_ms(request_start),
                    "prefill_progress_event_count": prefill_progress_state["count"],
                    "prefill_step_size": generation_params.get("prefill_step_size"),
                }
                _emit(
                    {
                        "ok": True,
                        "runtime_owned_terminal_earlier_earlier_boundary": True,
                        "action": "stream_runtime_owned_terminal_earlier_earlier_boundary",
                        "terminal_action": "stream_message_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                        "message_count": len(messages),
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "runtime_owned_terminal_earlier_boundary": True,
                        "action": "stream_runtime_owned_terminal_earlier_boundary",
                        "terminal_action": "stream_message_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                        "message_count": len(messages),
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "runtime_owned_terminal_boundary": True,
                        "action": "stream_runtime_owned_terminal_boundary",
                        "terminal_action": "stream_message_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                        "message_count": len(messages),
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "runtime_owned_terminal_leading_discriminator": True,
                        "action": "stream_runtime_owned_terminal_leading_discriminator",
                        "terminal_action": "stream_message_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                        "message_count": len(messages),
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "runtime_owned_terminal_notice_discriminator": True,
                        "action": "stream_runtime_owned_terminal_notice_discriminator",
                        "terminal_action": "stream_message_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                        "message_count": len(messages),
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "terminal_notice_lead": True,
                        "action": "stream_terminal_notice_lead",
                        "terminal_action": "stream_message_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                        "message_count": len(messages),
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "terminal_notice": True,
                        "action": "stream_terminal_notice",
                        "terminal_action": "stream_message_done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "sequence": sequence,
                        "message_count": len(messages),
                    }
                )
                _emit(
                    {
                        "ok": True,
                        "action": "stream_message_done",
                        "event": "done",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "generation_count": generation_count,
                        "sequence": sequence,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "finish_reason": finish_reason,
                        "message_count": len(messages),
                        "timing": timing,
                    }
                )
                continue

            if action == "unload":
                unloaded_model = current_model_id
                current_model_id = None
                model = None
                tokenizer = None
                generation_count = 0
                gc.collect()
                _emit(
                    {
                        "ok": True,
                        "action": "unload",
                        "model_id": unloaded_model,
                        "pid": os.getpid(),
                    }
                )
                continue

            if action == "ping":
                _emit(
                    {
                        "ok": True,
                        "action": "ping",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                        "generation_count": generation_count,
                    }
                )
                continue

            if action == "shutdown":
                _emit(
                    {
                        "ok": True,
                        "action": "shutdown",
                        "model_id": current_model_id,
                        "pid": os.getpid(),
                    }
                )
                return 0

            _emit({"ok": False, "error": f"unsupported action: {action or '<empty>'}"})
        except Exception as exc:
            _emit(
                {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
