"""F-4 #1b: grammar through the OpenAI surface, real model, end-to-end.

The route unit tests (test_server_routes_openai.py) prove the plumbing with a
FakeBackend; F-4.2a's backend smoke proves backend→child→grammar produces valid
JSON with a real model. This probe closes the last seam: a real model behind the
full OpenAI /v1/chat/completions route via FastAPI TestClient (in-process, no
uvicorn), driven with an OpenAI ``response_format`` json_schema.

control (no response_format) vs treatment (response_format json_schema), same
prompt. Expect treatment to return valid schema-conformant JSON.

Probe (scripts/), not a committed unit test: loads a ~14GB model via the real
subprocess backend.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from owlmlx.runtime.kernel import RuntimeKernel
from owlmlx.runtime.mlx_lm_subprocess_backend import MlxLmSubprocessBackend
from owlmlx.runtime.server import create_app

MODEL_DIR = "/Users/yeemio/AI/Agent/models/Qwen3.6-27B-4bit"
MODEL_ID = "qwen3.6-27b-4bit"

SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string", "maxLength": 120},
        "category": {"type": "string", "enum": ["bugfix", "feature", "docs", "test"]},
        "priority": {"type": "integer"},
        "requires_review": {"type": "boolean"},
    },
    "required": ["task_id", "category", "priority", "requires_review"],
    "additionalProperties": False,
}

PROMPT = (
    "Return JSON only. Schema: task_id string, category one of "
    "[bugfix,feature,docs,test], priority integer, requires_review boolean. "
    'Use task_id "F4-OAI-001" and category "bugfix".'
)


def _last_json_block(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    return text[start : end + 1] if start != -1 and end != -1 else text


def main() -> int:
    if not Path(MODEL_DIR).is_dir():
        print(f"model dir absent: {MODEL_DIR}")
        return 3

    backend = MlxLmSubprocessBackend(model_path_resolver=lambda _m: MODEL_DIR)
    kernel = RuntimeKernel(backend)
    print(f"loading {MODEL_ID} …", flush=True)
    loaded = kernel.load_model(MODEL_ID, memory_gb=14.0)
    if not loaded.ok:
        print(f"load failed: {loaded}")
        return 4
    client = TestClient(create_app(kernel))

    base = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 128,
        "temperature": 0.3,
    }

    try:
        print("control (no response_format) …", flush=True)
        r_ctrl = client.post("/v1/chat/completions", json=base)
        ctrl_text = r_ctrl.json()["choices"][0]["message"]["content"]
        ctrl_ok = _parses(_last_json_block(ctrl_text))
        print(f"  control parses: {ctrl_ok} :: {ctrl_text[:120]!r}", flush=True)

        print("treatment (response_format json_schema) …", flush=True)
        r_tx = client.post(
            "/v1/chat/completions",
            json={
                **base,
                "response_format": {"type": "json_schema", "json_schema": {"schema": SCHEMA}},
            },
        )
        tx_text = r_tx.json()["choices"][0]["message"]["content"]
        tx_json = _last_json_block(tx_text)
        tx_ok = _parses(tx_json)
        schema_ok = tx_ok and _schema_conformant(json.loads(tx_json))
        print(f"  treatment parses: {tx_ok} schema_ok: {schema_ok} :: {tx_text[:160]!r}", flush=True)
    finally:
        kernel.unload_model(MODEL_ID)

    passed = bool(schema_ok)
    print(f"VERDICT: {'PASS' if passed else 'FAIL'} (grammar via OpenAI /v1/chat/completions)", flush=True)
    return 0 if passed else 5


def _parses(text: str) -> bool:
    try:
        json.loads(text)
        return True
    except Exception:  # noqa: BLE001
        return False


def _schema_conformant(obj: object) -> bool:
    if not isinstance(obj, dict):
        return False
    keys = {"task_id", "category", "priority", "requires_review"}
    return (
        set(obj) == keys
        and isinstance(obj.get("task_id"), str)
        and obj.get("category") in {"bugfix", "feature", "docs", "test"}
        and isinstance(obj.get("priority"), int)
        and isinstance(obj.get("requires_review"), bool)
    )


if __name__ == "__main__":
    raise SystemExit(main())
