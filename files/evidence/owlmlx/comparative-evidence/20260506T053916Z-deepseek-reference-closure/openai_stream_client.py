#!/usr/bin/env python3
"""Minimal OpenAI-compatible streaming client for comparative evidence runs."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def _choice_text(obj: dict[str, object]) -> str:
    choices = obj.get("choices")
    if not isinstance(choices, list) or not choices:
        text = obj.get("text")
        return text if isinstance(text, str) else ""
    choice = choices[0]
    if not isinstance(choice, dict):
        return ""
    delta = choice.get("delta")
    if isinstance(delta, dict):
        for key in ("content", "reasoning_content", "reasoning"):
            content = delta.get(key)
            if isinstance(content, str):
                return content
    message = choice.get("message")
    if isinstance(message, dict):
        for key in ("content", "reasoning_content", "reasoning"):
            content = message.get(key)
            if isinstance(content, str):
                return content
    text = choice.get("text")
    return text if isinstance(text, str) else ""


def _print_json_response(raw: bytes) -> None:
    payload = json.loads(raw.decode("utf-8", errors="replace"))
    text = _choice_text(payload)
    if text:
        print(text, flush=True)


def _print_sse_response(response) -> None:
    for raw_line in response:
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            return
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            continue
        text = _choice_text(payload)
        if text:
            print(text, flush=True)


def _post_json(url: str, payload: dict[str, object] | None = None) -> None:
    data = b"" if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=900) as response:
        response.read()


def _preload_if_requested(base_url: str, model: str) -> None:
    mode = os.environ.get("OPENAI_STREAM_CLIENT_PRELOAD_MODE", "").strip()
    if mode == "owlmlx_v1_load":
        memory_gb = float(os.environ.get("OPENAI_STREAM_CLIENT_MEMORY_GB", "80"))
        _post_json(
            base_url.rstrip("/") + "/v1/load",
            {"model_id": model, "memory_gb": memory_gb},
        )


def _unload_if_requested(base_url: str, model: str) -> None:
    mode = os.environ.get("OPENAI_STREAM_CLIENT_UNLOAD_MODE", "").strip()
    if mode == "owlmlx_v1_unload":
        _post_json(base_url.rstrip("/") + "/v1/unload", {"model_id": model})
    elif mode == "omlx_v1_model_unload":
        _post_json(base_url.rstrip("/") + f"/v1/models/{model}/unload")


def main() -> int:
    if len(sys.argv) != 6:
        print(
            "usage: openai_stream_client.py BASE_URL MODEL PROMPT MAX_TOKENS TEMPERATURE",
            file=sys.stderr,
        )
        return 2
    base_url, model, prompt, max_tokens, temperature = sys.argv[1:]
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": int(max_tokens),
        "temperature": float(temperature),
        "stream": True,
    }
    request = urllib.request.Request(
        base_url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        _preload_if_requested(base_url, model)
        with urllib.request.urlopen(request, timeout=900) as response:
            content_type = response.headers.get("content-type", "")
            if "text/event-stream" in content_type:
                _print_sse_response(response)
            else:
                _print_json_response(response.read())
        _unload_if_requested(base_url, model)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code}: {body}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
