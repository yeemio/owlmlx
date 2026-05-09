# Python Environment Unification — Research

> Status: research deliverable (not a contract yet)
> Updated: 2026-05-07
> Scope: owlmlx repo + adjacent runtime-probes; local truth, with CI implications

## 1. Question

How do we collapse the project's de-facto multi-venv state into one **single,
machine-readable, auditable** Python environment baseline that local dev,
subprocess MLX execution, and (future) CI all agree on?

This is not "pick a Python version". The blocking problem is that **three
independent sources of truth currently disagree** about which interpreter is
safe to use for `mlx_lm`, and none of them is canonical.

## 2. Verified facts on this host (2026-05-07)

### 2.1 Venvs that exist under `owlmlx/`

| Path | Python | `mlx-lm` | `mlx` | Created | Role per current docs |
|---|---|---|---|---|---|
| `.venv/` | 3.11.15 | none (empty pip set) | none | Apr 11 | none — historical, abandoned |
| `.runtime1-mlx/` | 3.14.3 | 0.31.2 | 0.31.1 | Apr 11 | "verified clean baseline" |
| `.runtime2-mlx/` | 3.14.3 | 0.31.2 | 0.31.1 | Apr 13 | unstated; identical to runtime1 |
| `.runtime-deepseek-v4-mlx/` | 3.14.3 | editable `/tmp/deepseek-v4-mlx-pr` | 0.31.2 | May 5 | DeepSeek adapter probe |

Plus the project-external `/Users/yeemio/AI/llm-infra/.venv` (quarantined) and
`/opt/homebrew/bin/python3` (no `mlx_lm`).

### 2.2 Three sources of truth, three different answers

| Source | Asserts safe | Asserts unsafe |
|---|---|---|
| `docs/source-of-truth/runtime1-environment-diagnostics.md` | `.runtime1-mlx` | `.venv`, `llm-infra` |
| `~/.owlmlx/mlx-verified-python.json` (registry, written by `register_verified_mlx_baseline.py`) | only `runtime-probes/omlx-probe/.venv` | — |
| `~/.owlmlx/mlx-unsafe-python.json` (quarantine) | — | **`.runtime1-mlx`**, **`.runtime2-mlx`**, `.venv`, `llm-infra` |
| `owlmlx/runtime/mlx_environment.py:331-335` (hardcoded probe list) | enumerates `.runtime1-mlx`, `.runtime2-mlx` as candidates | hardcodes `_KNOWN_UNSAFE_EXECUTABLE_SUFFIXES` for `.venv`, `llm-infra` |

**The contradiction:** docs and source code call `.runtime1-mlx` the verified
baseline. The on-disk quarantine says it has aborted during Metal init under
both `default_metal` and `force_cpu`. The verified-baseline registry doesn't
mention it at all and instead points at a different venv entirely
(`runtime-probes/omlx-probe/.venv`).

This contradiction is the actual unification debt. Any future "single-env"
proposal that doesn't first reconcile this will inherit it.

### 2.3 Spec artifacts that exist but nothing reads

- `pyproject.toml` declares `requires-python = ">=3.10"` and an optional
  `runtime` extra with `mlx>=0.22.0`, `mlx-lm>=0.22.0`. **No script installs
  this extra.** `bootstrap_runtime1_env.sh` runs `pip install` against the
  same version pins by hand, bypassing the extra.
- `uv.lock` exists, revision 3, last edited Apr 23. **No script runs
  `uv sync`.** The lock is a fossil of one resolution; the actual venvs were
  built ad-hoc with `pip` and have already drifted from it (e.g.
  `.runtime-deepseek-v4-mlx` has `mlx==0.31.2`, `uvicorn==0.46.0`; the others
  have `mlx==0.31.1`, `uvicorn==0.44.0`).

### 2.4 What the hardcoded `_KNOWN_UNSAFE_EXECUTABLE_SUFFIXES` actually is

```python
_KNOWN_UNSAFE_EXECUTABLE_SUFFIXES: tuple[str, ...] = (
    "/AI/llm-infra/.venv/bin/python",
    "/AI/gitrep/owlmlx/.venv/bin/python",
)
```

This is a per-machine fact baked into `owlmlx/runtime/mlx_environment.py`. It
duplicates information that already lives in `~/.owlmlx/mlx-unsafe-python.json`
and would be wrong on any other host.

## 3. The decision space

There are exactly three viable shapes. Listing all three so the trade-offs are
explicit.

### Option A — `pyproject.toml` + `uv.lock` is the only truth

One `.venv`, populated by `uv sync --extra runtime`. Delete every
`.runtime*-mlx` directory. Hardcoded path tables in `mlx_environment.py` go
away. Subprocess code resolves the interpreter as `{repo}/.venv/bin/python`.

- Pros: matches modern Python convention, machine-portable, CI-friendly,
  one artifact to audit.
- Cons: ignores that on macOS Metal, "the package set resolves" and "the
  interpreter can survive `import mlx_lm`" are independent facts. A perfectly
  valid `uv.lock` can produce a venv that aborts at Metal init. Pyproject
  cannot express host-level facts.

### Option B — On-disk registry is the only truth

`~/.owlmlx/mlx-verified-python.json` and `mlx-unsafe-python.json` become
authoritative. Source code never hardcodes paths; `pyproject.toml` is just
documentation. Bootstrap registers the venv after a real probe.

- Pros: handles the host-fact dimension correctly. Already half-implemented.
- Cons: per-host. CI has to bootstrap its own registry every run. No way to
  share a known-good baseline across the team.

### Option C — Two-tier: spec + fact (recommended)

`pyproject.toml` is **intent**: pinned Python (`3.14`), pinned
`mlx>=0.31,<0.32`, locked via `uv.lock`. One canonical venv path —
`{repo}/.venv` — produced by `uv sync --extra runtime`.

`~/.owlmlx/*.json` is **runtime fact**: which interpreters on this host
actually survived an MLX import probe. The bootstrap step's *last* action is
to probe the freshly-built `.venv` and either write it into
`mlx-verified-python.json` (success) or refuse to mark the bootstrap
complete (failure).

`mlx_environment.py` discovers candidates in this order: registry first, then
the conventional `{repo}/.venv/bin/python`, then `sys.executable`. The
hardcoded `_KNOWN_UNSAFE_EXECUTABLE_SUFFIXES` table and the broader
`known_environment_candidates` enumeration both move into the registry.

- Pros: spec is portable (CI can use it), fact is honest (host abort risk is
  preserved). No path strings in source.
- Cons: two artifacts instead of one, and the bootstrap script becomes
  load-bearing — it is the bridge between them.

## 4. Recommendation

Adopt **C**, with the following concrete changes (research conclusion, not yet
a plan to execute):

1. **Pyproject corrections.** Bump `mlx`/`mlx-lm` lower bound to `0.31` (the
   actual working version; `0.22` is a lie about what works on Metal today).
   Add `requires-python = ">=3.14"` if 3.14 is the target — currently `>=3.10`
   misrepresents intent. Pin via a `.python-version` file checked into git.
2. **Single venv path.** Standardize on `{repo}/.venv` (drop the
   `.runtime1-mlx` / `.runtime2-mlx` cohabitation). The
   `runtime1` / `runtime2` distinction was operational mode, not interpreter
   identity, and conflating the two created the current confusion.
3. **Bootstrap rewrite.** `scripts/bootstrap_runtime1_env.sh` becomes a thin
   wrapper around `uv sync --extra runtime` followed by an explicit
   `register_verified_mlx_baseline` call against the new `.venv`. The script
   refuses to exit 0 unless the registry write succeeds.
4. **Source-code cleanup.** Delete `_KNOWN_UNSAFE_EXECUTABLE_SUFFIXES` and the
   hardcoded list inside `known_environment_candidates`. Both move to the
   on-disk JSON. The function reads from disk only.
5. **Registry truthing.** Before any of the above lands, do a one-time audit:
   re-probe each currently-installed venv against the *current* `mlx 0.31.x`
   (the abort that put `.runtime1-mlx` into quarantine happened before
   subsequent reinstalls; the quarantine entry may be stale). Reconcile
   the docs' "verified safe" claim against the quarantine file. One of the
   two is wrong; figure out which before unifying.
6. **Garbage collect.** After (1)–(5), the four legacy venv directories
   (`.venv`, `.runtime1-mlx`, `.runtime2-mlx`, `.runtime-deepseek-v4-mlx`)
   should be removable. The DeepSeek probe's editable install at
   `/tmp/deepseek-v4-mlx-pr` is by definition ephemeral and shouldn't anchor
   a tracked workflow — if it's still load-bearing, lift it into a real
   `[project.optional-dependencies].deepseek-probe` group.
7. **CI shape.** CI cannot import `mlx-metal` on Linux. Add a
   `[project.optional-dependencies].dev-nomlx` group (everything except
   `mlx*`). Mark MLX-touching tests with `@pytest.mark.requires_mlx` and
   skip-by-default in CI; nightly mac runner installs the full `runtime`
   extra and runs the lot. This is out-of-scope for the unification proper
   but is the constraint that disqualifies Option A in isolation.

## 5. Risks and open questions

- **Stale quarantine.** If `.runtime1-mlx` is actually safe today and the
  quarantine entry is just old, we've been silently skipping the right venv
  in operator diagnostics for weeks. This must be re-probed before any
  source-code cleanup.
- **Python 3.14 wheel availability.** Some pytest plugins / dev tools may
  not have 3.14 wheels yet. `uv lock` against the current pyproject will
  surface this; the answer may be "stay on 3.13 for now".
- **`uv.lock` revision drift.** The lock is from Apr 23; the venvs are
  newer. A `uv lock --upgrade` against the corrected pyproject will produce
  the new authoritative lock.
- **Cross-repo registries.** `register_verified_mlx_baseline.py` writes to
  `~/.owlmlx/`. Other repos under `gitrep/` (e.g. `runtime-probes/`) write
  to the same registry. This is correct (the registry is per-host, not
  per-repo) but should be documented — currently it is not.

## 6. Out of scope for this research

- The Phase-45 active seam, native MLX backend adapter ticketed FIFO, and
  any post-claim invariant testing. This research deliberately does not
  touch runtime code.
- The desktop product layer's environment story.
- Choosing between `uv` and `poetry` / `rye` / etc. — `uv` is already
  present and partially adopted; switching tools is a separate question.
