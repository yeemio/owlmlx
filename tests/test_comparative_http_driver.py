# tests/test_comparative_http_driver.py
import json
import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "comparative_http_driver",
    Path(__file__).parents[1] / "scripts" / "bench" / "comparative_http_driver.py",
)
driver = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(driver)


def test_load_prompt_set_returns_system_and_turns(tmp_path):
    p = tmp_path / "ps.json"
    p.write_text(json.dumps({"system": "sys", "turns": ["a", "b"]}), encoding="utf-8")
    system, turns = driver.load_prompt_set(str(p))
    assert system == "sys"
    assert turns == ["a", "b"]


def test_build_messages_accumulates_history():
    history = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "A"}]
    msgs = driver.build_messages(system="sys", history=history, user_turn="b")
    assert msgs[0] == {"role": "system", "content": "sys"}
    assert msgs[-1] == {"role": "user", "content": "b"}
    assert {"role": "assistant", "content": "A"} in msgs


def test_summarize_emits_total_tokens_line():
    out = driver.format_output(turn_texts=["hello", "world"], total_tokens=7)
    lines = out.strip().splitlines()
    assert lines[0] == "hello"
    assert json.loads(lines[-1]) == {"generated_tokens": 7}
