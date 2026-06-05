# tests/test_runtime_comparative_evidence_multi_turn.py
import hashlib
import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "runtime_comparative_evidence",
    Path(__file__).parents[1] / "scripts" / "runtime_comparative_evidence.py",
)
op = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(op)


def test_prompt_set_hash_is_deterministic_sha256(tmp_path):
    f = tmp_path / "ps.json"
    f.write_text('{"turns":["a"]}', encoding="utf-8")
    h = op._prompt_set_hash(str(f))
    assert h == "sha256:" + hashlib.sha256(b'{"turns":["a"]}').hexdigest()
