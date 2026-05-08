# owlmlx Python Environment — Research (NOT main-line landing)

> Status: research-grade, 2026-05-08
> Scope: snapshot + recommendation only; this document does not change code,
> does not add `.python-version`, does not stage `uv.lock`, does not modify
> `pyproject.toml`. Landing decisions belong to a separate
> `python-environment-unification-landing` round.

## 0. TL;DR

- **Recommended pinned Python: `3.11.15`** (already in `.venv/`, fully
  exercised; mlx + mlx-lm + transformers + dependent runtime stack already
  resolved and installed against this interpreter)
- **Recommended toolchain: `uv` only**, deprecate `poetry` (poetry is
  installed but not used; `uv.lock` already exists)
- **Recommended lifecycle smoke entry**: `.venv/bin/python` directly or
  `uv run pytest` — **not** the default shell `python3` (which is brew 3.14
  and PEP668-blocked)
- **Recommended for landing round**: stage `uv.lock`, add `.python-version`
  pinned to `3.11`, write a minimal `docs/source-of-truth/python-environment.md`
  developer-facing doc, and add a fail-loud helper that warns when tests are
  run outside `.venv`. Do not change `pyproject.toml`'s
  `requires-python = ">=3.10"` declaration (it is the downstream-user
  compatibility contract, not a development constraint).
- **Lifecycle smoke can proceed in parallel** without waiting for the
  landing round. The lifecycle-smoke prompt's step 1 already says "do not
  change owlmlx requires-python" — the only adjustment needed is for the
  smoke executor to use `.venv/bin/python` rather than default `python3`,
  and to cite this research as the basis for the provisional pin.

## 1. Factual Snapshot (实测, 2026-05-08)

### 1.1 Interpreters present on this machine

| Label        | Path                                                                  | Version  | Arch  | PEP668 (externally-managed)            |
|--------------|-----------------------------------------------------------------------|----------|-------|-----------------------------------------|
| system       | `/usr/bin/python3`                                                    | 3.9.6    | arm64 | n/a (Apple system, do not write)        |
| xcode-clt    | `/Library/Developer/CommandLineTools/usr/bin/python3.9`               | 3.9.6    | arm64 | n/a (Apple, do not write)               |
| brew-3.10    | `/opt/homebrew/bin/python3.10`                                        | 3.10.20  | arm64 | yes (brew marks externally-managed)     |
| brew-3.11    | `/opt/homebrew/bin/python3.11`                                        | 3.11.15  | arm64 | yes                                     |
| brew-3.14    | `/opt/homebrew/bin/python3.14`                                        | 3.14.3   | arm64 | yes — confirmed by direct `pip install` |
| uv-3.13      | `~/.local/share/uv/python/cpython-3.13-macos-aarch64-none/bin/python3.13` | 3.13.12 | arm64 | n/a (uv-managed, isolated)              |

The default shell `python3` symlinks to brew 3.14, which is **PEP668-blocked
for direct `pip install`** — confirmed by:

```
$ /opt/homebrew/bin/python3.14 -m pip install --dry-run "mlx>=0.22.0"
error: externally-managed-environment
hint: See PEP 668 for the detailed specification.
```

### 1.2 Project venv

- Location: `.venv/` (created 2026-04-11 by **uv 0.10.10**)
- Pinned interpreter: `/opt/homebrew/opt/python@3.11/bin/python3.11`
  (3.11.15)
- `include-system-site-packages = false` — fully isolated
- `pip` is not installed inside the venv (uv idiom — uv manages
  installation directly)
- owlmlx itself is installed in **editable mode**
  (`_editable_impl_owlmlx.pth` points back to repo root)

### 1.3 uv.lock state (untracked in git)

- `version = 1`, `revision = 3`
- `requires-python = ">=3.10"`
- Resolution markers: `python_full_version >= '3.11'` /
  `python_full_version < '3.11'` (i.e. resolver split forks at the 3.11
  boundary)
- Key resolved versions: mlx 0.31.2, mlx-lm 0.31.3, mlx-metal 0.31.2,
  numpy 2.2.6 + 2.4.4 (forked), pytest 9.0.3, fastapi 0.136.0, uvicorn
  0.46.0

### 1.4 .venv vs uv.lock drift (already observable)

| Package    | uv.lock pins | `.venv` actually installed |
|------------|--------------|----------------------------|
| mlx        | 0.31.2       | **0.31.1**                 |
| mlx-lm     | 0.31.3       | **0.31.2**                 |
| mlx-metal  | 0.31.2       | **0.31.1**                 |

The `.venv` was created and populated before the lock file was bumped, and
no `uv sync` has rerun against the latest lock. This is one concrete
example of why the project needs an environment hygiene policy: lock and
venv should not silently diverge.

### 1.5 mlx_lm public surface that lifecycle smoke depends on (实测 against `.venv`)

```python
>>> from mlx_lm import load, generate, stream_generate, batch_generate  # all present
>>> from mlx_lm.models.cache import make_prompt_cache  # present — KV cache handle entry point
>>> from mlx_lm.sample_utils import make_sampler  # present — sampler injection entry point
```

Every mlx_lm entry point that the native-MLX-backend capability matrix lists
as `experimental` for "supported in upstream public API" is **actually
present** in the currently-installed `.venv` mlx-lm 0.31.2. The
matrix's `experimental` rating reflects "owlmlx has not yet bound it" —
not "upstream does not provide it."

### 1.6 Default shell command behavior

- `python3 -m pytest tests/...` runs against **brew 3.14**, not `.venv` 3.11
- All prior rounds in this conversation that ran `python3 -m pytest` used
  3.14 — the test files only pass because they don't `import mlx_lm` (or
  use fake-injection)
- This is a silent drift between "what runs locally" and "what the project
  is actually pinned to"

## 2. mlx / mlx-lm Wheel Compatibility Matrix (实测 dry-run)

| Python | mlx wheel filename                                                | mlx-lm wheel              | Verdict                                   |
|--------|-------------------------------------------------------------------|---------------------------|-------------------------------------------|
| 3.10   | `mlx-0.31.2-cp310-cp310-macosx_26_0_arm64.whl`                    | `mlx_lm-0.31.3-py3-none-any.whl` | wheel exists, install OK in venv          |
| 3.11   | `mlx-0.31.2-cp311-cp311-macosx_26_0_arm64.whl`                    | `mlx_lm-0.31.3-py3-none-any.whl` | wheel exists, **already in `.venv`**      |
| 3.13   | uv-managed but no project venv attached                           | (same)                    | wheel availability not yet probed        |
| 3.14   | `mlx-0.31.2-cp314-cp314-macosx_26_0_arm64.whl`                    | `mlx_lm-0.31.3-py3-none-any.whl` | wheel exists; PEP668 blocks direct install |

Surprise finding: **mlx 0.31.2 has a cp314 wheel for macOS 26 arm64 already
published**. The earlier assumption that 3.14 was "too new for mlx" was
wrong — the constraint was PEP668, not wheel availability.

mlx-lm itself is `py3-none-any` (pure Python), so any 3.10+ Python that has
mlx works.

The full mlx-lm dependency closure (one-shot): mlx, mlx-metal, numpy,
transformers (>=5.0.0), tokenizers, safetensors, sentencepiece, protobuf,
pyyaml, jinja2, huggingface-hub (>=1.5.0), httpx, hf-xet, regex, typer,
tqdm, packaging, filelock, fsspec. Several of these (transformers 5.x,
tokenizers 0.22+, huggingface-hub 1.x) have moved to versions that
themselves require Python >= 3.10. **3.9 paths cannot run mlx-lm 0.31.x.**

## 3. Recommendation

### 3.1 Pin Python to 3.11.15

Reasons (in order of weight):

1. **Already in `.venv` and exercised** — switching cost is zero
2. **All required wheels exist and are installable** — confirmed by dry-run
   for all of mlx, mlx-lm, transitive deps
3. **uv.lock resolution boundary is exactly 3.11** (`>= '3.11'` /
   `< '3.11'` markers) — this is the version uv has actually solved
   against most recently
4. **3.11 is well past `mlx-lm`'s minimum (3.10)** and well before EOL
   (Oct 2027) — at least 18 months of stable runway
5. **3.14 has wheels but is more aggressive about deprecation warnings** —
   already observed on this machine: `mlx`'s SWIG bindings emit
   `DeprecationWarning: builtin type SwigPyPacked has no __module__
   attribute` on import. Tolerable on 3.11, may become an error on 3.14
6. **3.10 is two versions behind and approaches EOL faster** — not
   forward-looking
7. **3.13 is also viable** — but no project venv exists for 3.13, and
   migration cost is non-zero

### 3.2 Toolchain: uv only

- `uv 0.10.10` already manages `.venv/`
- `uv.lock` already exists
- `poetry` is installed (`/opt/homebrew/bin/poetry`) but no `poetry.lock`
  exists — keeping it installed but unused is dead weight
- Recommendation: deprecate `poetry` from project documentation. Do not
  uninstall it from the user's brew formulae unless they want to clean
  globally.

### 3.3 What goes into git

| Artifact            | Recommendation         | Rationale                                                  |
|---------------------|------------------------|-------------------------------------------------------------|
| `uv.lock`           | **stage and commit**   | Lockfile is the contract; CI and dev should agree           |
| `.python-version`   | **add and commit**     | Lets uv / pyenv / IDEs auto-pick 3.11; avoids shell drift   |
| `.venv/`            | already in `.gitignore`| Standard                                                    |
| `pyproject.toml`    | **do not change**      | `requires-python = ">=3.10"` is the downstream contract     |

The `requires-python` value in `pyproject.toml` is a **compatibility
declaration for downstream users who install owlmlx as a library** — it
says "this package will run on Python 3.10+". It is intentionally permissive.
The development pin (3.11) is a separate, stricter constraint encoded in
`.python-version` and `uv.lock`. These two files do not contradict
`pyproject.toml`; they refine it.

### 3.4 Dev command convention

Two acceptable patterns:

1. **`uv run <cmd>`** — uv ensures `.venv` is in sync before running
   (recommended; one syntax for all)
2. **`.venv/bin/python -m <cmd>`** — direct, no uv overhead, but the
   developer must remember to `uv sync` when lock changes

Prohibited (or fail-loud warned):

- bare `python3 -m pytest` — silently runs against brew 3.14, which is
  PEP668-blocked and lacks runtime extras

A simple `conftest.py`-level check can detect mismatch: if
`sys.executable` is not under `.venv/`, emit a loud pytest warning
"running outside .venv; native lifecycle tests will skip". This makes the
drift visible without breaking workflows.

### 3.5 CI lane design

One CI lane is sufficient for the current main line:

- **`native-runtime`** lane: Python 3.11.15, `uv sync --extra runtime`,
  runs full test suite including native-MLX lifecycle smoke

Future considerations (out of scope for landing round):

- a **`compatibility-3.10`** lane that runs the non-runtime tests on 3.10 to
  prove `requires-python = ">=3.10"` declaration still holds
- a **`linux-arm64-subprocess-only`** lane for cross-platform proof of the
  subprocess backend (mlx is Apple Silicon-only; Linux can only exercise
  non-mlx parts of owlmlx)

These additional lanes are research, not landing scope.

### 3.6 Relationship to lifecycle smoke round

Lifecycle smoke (`owlmlx-native-mlx-backend-lifecycle-smoke-and-kv-cache-handle-owned.md`)
can run **in parallel** with this research's landing. Concrete impact on
that round:

- step 1 ("CI lane preparation"): use 3.11; this is now backed by evidence
- step 2 ("real model lifecycle smoke"): can use existing `.venv` directly;
  mlx-lm 0.31.2 + mlx 0.31.1 are already installed, no new install needed
  for the smoke itself
- step 3 ("KV cache handle to first-class"): `make_prompt_cache` and
  `make_sampler` are confirmed present in upstream public API; binding can
  proceed
- the smoke round still does not need to touch `.python-version`,
  `uv.lock`, or `pyproject.toml` — those are landing-round work

## 4. Migration Path (for a future landing round, not now)

Each step is independently revertable.

| Step | Action | Revert cost |
|------|--------|-------------|
| 1 | `git add .python-version` (file content: `3.11`) | trivial |
| 2 | `git add uv.lock` | trivial |
| 3 | `uv sync --extra runtime` to refresh `.venv` to lock | run `uv sync` again with old lock |
| 4 | Add `docs/source-of-truth/python-environment.md` (developer-facing) | doc-only |
| 5 | Add `conftest.py` warning when tests run outside `.venv` | revert one file |
| 6 | Update README dev section | doc-only |
| 7 | Add CI lane spec (file location TBD by landing round) | doc-only until CI is wired |

No step requires changing `pyproject.toml`. No step affects `owlmlx/`
runtime code.

## 5. Risks & Open Questions

### 5.1 Already-known
- **`.venv` lags `uv.lock` by one patch** (mlx 0.31.1 vs 0.31.2). Landing
  round must `uv sync` to align before tests are trusted as authoritative.
- `pip` is not in `.venv` (uv idiom). Any tool that shells out to `pip`
  directly will fail. Landing round should document `uv pip ...` as the
  install path.
- `transformers 5.x` and `tokenizers 0.22+` change rapidly. Lock-pinning
  is essential; floating `>=5.0.0` would break repeatability.
- `mlx`'s SWIG-derived classes emit DeprecationWarnings on Python 3.11
  already; on 3.14 these may turn into errors. This is an upstream-mlx
  issue and is one reason to **not** chase 3.14 right now.

### 5.2 Not yet probed (deferred to lifecycle smoke or follow-up research)
- whether `mlx_lm` 0.31.2 (in venv) and 0.31.3 (in lock) have any
  meaningfully different cache / sampler API (likely a patch-level no-op,
  but unverified)
- whether `mlx_lm.models.cache.make_prompt_cache` accepts being threaded
  back into `stream_generate` in 0.31.2 — needed for the lifecycle smoke
  KV cache handle round (probable yes; not yet smoke-tested)
- whether `uv` itself should be pinned via `pyproject.toml`'s
  `[tool.uv]` block — out of research scope
- Linux-side feasibility (subprocess-backend only); not on critical path

### 5.3 No predefined conclusion (per research prompt's anti-bias clause)
- if a future probe shows mlx-lm 0.31.x has broken on 3.11 in some way,
  this recommendation should flip to 3.13 (next-best uv-managed option
  with wheels)
- if uv tooling is ever blocked on a CI provider, fallback is
  `python3.11 -m venv .venv && pip install -e .[runtime]` — slower but
  works without uv

## 6. What This Research Does Not Do

- does not modify `owlmlx/` runtime code
- does not change `pyproject.toml`'s `requires-python`
- does not stage `uv.lock`
- does not add `.python-version`
- does not modify CI configuration
- does not change phase45 active seam, native-MLX backend adapter, or
  capability matrix
- does not promote any capability matrix row from `experimental` to
  `supported`
- does not block lifecycle smoke from proceeding in parallel

The landing of any of the above is the explicit scope of a separate
**`python-environment-unification-landing`** round, which is recommended
to follow this research only after the lifecycle smoke round has
independently proved the recommended Python actually carries a real-model
lifecycle.

## 7. Recommended Next Round (Landing)

`python-environment-unification-landing`:

- stage `uv.lock`
- add `.python-version` (content: `3.11`)
- add `docs/source-of-truth/python-environment.md` (developer-facing, not
  research)
- add minimal `conftest.py` venv-mismatch warning
- update README dev section
- run `uv sync --extra runtime` to align venv to lock
- re-run focused regression sweep on `.venv/bin/python` to confirm parity
  with previously-passed tests on default `python3`
- explicitly does **not** change `pyproject.toml`
- explicitly does **not** modify `owlmlx/` code
- explicitly does **not** create CI configuration files (CI is a separate
  follow-up that depends on knowing which CI provider, which is not yet
  decided)
