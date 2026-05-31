# owlmlx Python Environment — Developer Workflow

> Status: authoritative
> Updated: 2026-05-08
> Audience: contributors. For the rationale behind these choices see
> `python-environment-research.md`.

## TL;DR

> **Update (2026-05-09, `90cefa5e`)**: `uv.lock` has since been committed
> (it is now tracked in git). The "deliberately does not stage it yet" /
> "follow-up operator action" wording throughout this doc predates that
> commit and is retained as the as-authored 2026-05-08 record.

- Project Python is **3.11.15**, pinned via `.python-version`
- Toolchain is **uv**; `uv.lock` is the lock file and is now committed
  (`90cefa5e`); the original landing-slice wording below ("does not stage
  it yet") predates that commit
- All commands run **inside `.venv/`** — either via `uv run …` or
  `.venv/bin/python …`
- The default shell `python3` on Apple Silicon machines often points to a
  different Python (brew 3.14, system 3.9, etc.) and is **not** the
  project Python. `pytest` will emit a loud `UserWarning` if run outside
  `.venv`.

## Setup From A Fresh Clone

```bash
# 1. Install uv if not present
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Sync the project (creates .venv, installs lock, includes editable owlmlx)
uv sync --extra runtime

# 3. Verify
.venv/bin/python --version           # → Python 3.11.15
.venv/bin/python -c "import mlx_lm"   # → no error
```

`uv sync --extra runtime` is what installs `mlx`, `mlx-lm`, transformers,
and the rest of the optional `runtime` dependencies. Until the follow-up
landing slice stages `uv.lock`, this command may create or refresh a local
lock file; do not treat that local lock as committed project truth yet.
Without `--extra runtime`, only the base `owlmlx` package is installed and
any test that imports `mlx_lm` will gracefully skip.

## Daily Workflow

| Task                      | Command                                                              |
|---------------------------|----------------------------------------------------------------------|
| Run all tests             | `uv run pytest`                                                      |
| Run a focused test file   | `uv run pytest tests/test_mlx_native_backend.py -q`                  |
| Run a script              | `uv run python scripts/runtime_dominant_gap_reselection.py`          |
| Open a Python REPL        | `uv run python`                                                      |
| Add a dependency          | `uv add <package>` (writes to `pyproject.toml` and `uv.lock`)        |
| Refresh after pulling     | `uv sync --extra runtime`                                            |

`uv run` ensures `.venv/` is in sync with the local uv environment before
each invocation. After the follow-up landing slice stages `uv.lock`, it
will also enforce the committed lock. If you prefer not to type `uv run`
every time, activate the venv:

```bash
source .venv/bin/activate
# now `python` is .venv/bin/python until you `deactivate`
```

## Why Not `python3 -m pytest`?

The default shell `python3` on this machine is brew **3.14**, not the
project's 3.11. Tests that don't `import mlx_lm` will pass anyway, but
the moment a test imports the runtime extra it will fail with `ModuleNotFoundError`
because mlx-lm is not installed in the system Python (and PEP 668
prevents installing it there).

`conftest.py` at repo root emits a loud `UserWarning` at pytest config
time when `sys.executable` is not under `.venv/`. This makes the drift
visible without breaking workflows for contributors who knowingly run on
a different interpreter.

## Project Pin vs Downstream Compatibility Pin

- `pyproject.toml` declares `requires-python = ">=3.10"` — this is the
  **downstream-user compatibility contract**. Anyone installing owlmlx as
  a library should be able to use Python 3.10+.
- `.python-version` declares `3.11` — this is the **development pin**.
  Contributors get a deterministic interpreter; lock resolution is stable.

These two are not in conflict. The development pin is stricter than the
downstream contract, which is the correct relationship.

## When Local `uv.lock` And `.venv/` Drift

Symptom: `.venv/lib/python3.11/site-packages/mlx-X.Y.Z.dist-info`'s
version disagrees with `grep '^version' uv.lock` near the `mlx` package
entry.

Fix:

```bash
uv sync --extra runtime
```

This is non-destructive: it brings `.venv` to the local lock state, no
manual uninstall needed. The follow-up environment landing part is expected
to run this intentionally and stage `uv.lock` only after the operator
accepts the resulting dependency refresh.

## CI Lane (Recommendation, Not Yet Wired)

A single CI lane is currently sufficient:

- **`native-runtime`**: Python 3.11.15, `uv sync --extra runtime`,
  `uv run pytest`

The lifecycle smoke test
(`tests/test_mlx_native_backend_real_smoke.py`) is **opt-in only** via
`OWLMLX_NATIVE_SMOKE_MODEL_PATH`. CI default does not invoke it. To
exercise it, the lane operator must:

1. ensure a small mlx-community quantized model is in
   `~/.cache/huggingface/hub/`
2. set `OWLMLX_NATIVE_SMOKE_MODEL_PATH=<that-model-id>`
3. set `OWLMLX_NATIVE_SMOKE_MAX_TOKENS=8` (or higher) to cap generation
4. `uv run pytest tests/test_mlx_native_backend_real_smoke.py -q -s`

A real-model smoke run is what gates the capability matrix promotion of
KV cache handle / decode_step / per-step finish_reason / cancellation
rows from `partial` to `supported`.

## What This Doc Does Not Do

- does not change `pyproject.toml`'s `requires-python`
- does not change project source code
- does not configure CI (CI lane spec is recommendation, not file)
- does not auto-run `uv sync` — that is an operator action
- does not stage `uv.lock`; that is reserved for the follow-up operator
  action after `uv sync --extra runtime` *(historical: `uv.lock` has since
  been committed in `90cefa5e` — see the TL;DR update banner)*
