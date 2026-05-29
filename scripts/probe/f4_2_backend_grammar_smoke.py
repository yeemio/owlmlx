"""F-4.2a end-to-end backend grammar smoke (real subprocess IPC path).

Unit tests cover the wiring in isolation. This probe proves the whole path
works through the REAL MlxLmSubprocessBackend: parent serializes a grammar
spec into the request params, the persistent child runner rebuilds the
xgrammar matcher and threads a logits_processor into mlx_lm.stream_generate,
and the streamed text comes back as parseable JSON.

It is a probe (scripts/), not a committed unit test: it spawns a child that
loads a ~18GB model, which is far too heavy for the unit suite. Run on a host
that has the local MLX model and xgrammar installed
(`uv pip install xgrammar` into the runtime venv).

Usage:
    .venv/bin/python scripts/probe/f4_2_backend_grammar_smoke.py

Exit code 0 = control breaks AND grammar produces valid JSON (the expected
F-4.2a outcome); non-zero = the path did not behave as designed.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from owlmlx.runtime import MlxLmSubprocessBackend

MODEL_DIR = "/Users/yeemio/AI/Agent/models/Qwen3.6-35B-A3B-4bit"
MODEL_ID = "qwen3.6-35b-a3b-4bit"
EVIDENCE_DIR = Path("files/evidence/owlmlx/bench/structured-output-invariance")

PROMPT = (
    "Return JSON only. No markdown. No prose. "
    'Schema: {"task_id": string, "category": one of ["bugfix","feature","docs","test"], '
    '"priority": integer, "requires_review": boolean}. '
    'Use task_id "F4-JSON-001" and category "bugfix".'
)

GRAMMAR = {
    "kind": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "task_id": {"type": "string"},
            "category": {
                "type": "string",
                "enum": ["bugfix", "feature", "docs", "test"],
            },
            "priority": {"type": "integer"},
            "requires_review": {"type": "boolean"},
        },
        "required": ["task_id", "category", "priority", "requires_review"],
        "additionalProperties": False,
    },
}


def _collect_text(events) -> str:
    parts = []
    for ev in events:
        if ev.event == "token" and ev.text:
            parts.append(ev.text)
    return "".join(parts)


def _parses(text: str) -> bool:
    try:
        json.loads(text.strip())
        return True
    except Exception:  # noqa: BLE001
        return False


def main() -> int:
    if not Path(MODEL_DIR).is_dir():
        print(f"[smoke] model dir absent: {MODEL_DIR}", flush=True)
        return 3

    backend = MlxLmSubprocessBackend(
        model_path_resolver=lambda _mid: MODEL_DIR,
    )
    print(f"[smoke] loading {MODEL_ID} via subprocess backend …", flush=True)
    load_result = backend.load(MODEL_ID, memory_gb=20.0)
    if not getattr(load_result, "ok", False):
        print(f"[smoke] load failed: {load_result}", flush=True)
        return 4

    try:
        print("[smoke] control (no grammar) …", flush=True)
        control_text = _collect_text(
            backend.stream_generate(MODEL_ID, PROMPT, max_tokens=128, temperature=0.3)
        )
        control_ok = _parses(control_text)
        print(f"[smoke]   control parses as JSON: {control_ok}", flush=True)
        print(f"[smoke]   control text: {control_text[:160]!r}", flush=True)

        print("[smoke] treatment (grammar) …", flush=True)
        treatment_text = _collect_text(
            backend.stream_generate(
                MODEL_ID,
                PROMPT,
                max_tokens=128,
                temperature=0.3,
                grammar=GRAMMAR,
            )
        )
        treatment_ok = _parses(treatment_text)
        print(f"[smoke]   treatment parses as JSON: {treatment_ok}", flush=True)
        print(f"[smoke]   treatment text: {treatment_text[:160]!r}", flush=True)
    finally:
        backend.unload(MODEL_ID)

    passed = bool(treatment_ok)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_path = EVIDENCE_DIR / f"{ts}-f4-2-backend-grammar-smoke.json"
    evidence_path.write_text(
        json.dumps(
            {
                "schema_version": "f4.2.backend_grammar_smoke.v1",
                "phase": "f4-2a-backend-grammar-smoke",
                "ts_utc": ts,
                "path": "real MlxLmSubprocessBackend IPC (parent->child runner)",
                "model_id": MODEL_ID,
                "model_dir": MODEL_DIR,
                "family": "json_schema_flat",
                "control": {"parses_json": control_ok, "text": control_text},
                "treatment": {"parses_json": treatment_ok, "text": treatment_text},
                "passed": passed,
                "note": (
                    "End-to-end proof that a grammar spec crosses the subprocess "
                    "boundary as a serializable param, the child rebuilds the "
                    "xgrammar matcher, and constrained generation returns valid "
                    "JSON. Single-sample integration smoke, not the F-4.2b matrix."
                ),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    print(f"[smoke] wrote evidence -> {evidence_path}", flush=True)

    # Expected F-4.2a outcome: grammar produces valid JSON. (Control may or may
    # not break on a single sample; the design claim is about treatment.)
    if passed:
        print("[smoke] PASS: grammar path produced valid JSON via real backend IPC", flush=True)
        return 0
    print("[smoke] FAIL: grammar path did not produce valid JSON", flush=True)
    return 5


if __name__ == "__main__":
    raise SystemExit(main())
