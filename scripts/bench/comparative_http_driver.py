#!/usr/bin/env python3
"""Uniform HTTP wrapper driver for the comparative-evidence runner.

One subprocess invocation = one runner attempt. Hits a runtime's warm
OpenAI-compatible /v1/chat/completions server (owlmlx :8066, oMLX :8063, vMLX).
The runner measures this process's wall-clock + first-token (stdout) and the
server's RSS (via the runner config's external_listener_ports/external_pid_file).

Modes:
  single     : one user prompt, one request.
  multi-turn : a sequence from --prompt-set; accumulate assistant replies into
               history each turn. With --session-id (owlmlx only), every request
               carries x-owlmlx-session-id so the runtime can reuse cached prefix.

stdout contract for the runner:
  - each turn's assistant text is printed as it arrives (first non-empty chunk =>
    first-token latency of the first turn)
  - a final line `{"generated_tokens": N}` (sum of completion_tokens across turns)
    => use tokens_method=json_field:generated_tokens in the runner config.

scripts/ (not owlmlx/) per the AGENTS module-as-spec rule: bench driver, no
runtime consumer, no capability promotion.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request


def load_prompt_set(path: str) -> tuple[str, list[str]]:
    payload = json.loads(open(path, encoding="utf-8").read())
    system = str(payload.get("system", ""))
    turns = [str(t) for t in payload.get("turns", [])]
    return system, turns


def build_messages(*, system: str, history: list[dict], user_turn: str) -> list[dict]:
    msgs: list[dict] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(history)
    msgs.append({"role": "user", "content": user_turn})
    return msgs


def format_output(*, turn_texts: list[str], total_tokens: int) -> str:
    lines = list(turn_texts)
    lines.append(json.dumps({"generated_tokens": int(total_tokens)}))
    return "\n".join(lines) + "\n"


def post_chat(
    *, base_url: str, model: str, messages: list[dict], max_tokens: int,
    temperature: float, session_id: str | None,
) -> tuple[str, int]:
    body = {
        "model": model, "messages": messages,
        "max_tokens": max_tokens, "temperature": temperature, "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    if session_id:
        headers["x-owlmlx-session-id"] = session_id
    req = urllib.request.Request(
        base_url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(body).encode(), headers=headers, method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read())
    content = data["choices"][0]["message"].get("content") or ""
    usage = data.get("usage") or {}
    completion = int(usage.get("completion_tokens", 0))
    return content, completion


def run(args: argparse.Namespace) -> int:
    if args.mode == "single":
        system, turns = ("", [args.prompt])
    else:
        system, turns = load_prompt_set(args.prompt_set)

    history: list[dict] = []
    turn_texts: list[str] = []
    total_tokens = 0
    for user_turn in turns:
        messages = build_messages(system=system, history=history, user_turn=user_turn)
        content, completion = post_chat(
            base_url=args.base_url, model=args.model, messages=messages,
            max_tokens=int(args.max_tokens), temperature=float(args.temperature),
            session_id=args.session_id,
        )
        # Print immediately so the runner's first-token timer fires on turn 1.
        print(content, flush=True)
        turn_texts.append(content)
        total_tokens += completion
        history.append({"role": "user", "content": user_turn})
        history.append({"role": "assistant", "content": content})

    sys.stdout.write(json.dumps({"generated_tokens": total_tokens}) + "\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["single", "multi-turn"], required=True)
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--prompt", default="")
    ap.add_argument("--prompt-set", default="")
    ap.add_argument("--max-tokens", type=int, default=128)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--session-id", default=None)
    return run(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
