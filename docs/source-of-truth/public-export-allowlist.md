# owlmlx Public Export Allowlist and Ignore Policy

> Status: authoritative
> Created: 2026-05-10
> Scope: which files and directories are safe to export to a public repository
> as-is; which require sanitization; which must be excluded

## 1. Purpose

This document defines the export boundary for `owlmlx` when publishing to a
public repository. It addresses two concerns:

1. **Content safety** — files containing private absolute paths (e.g.,
   `/Users/yeemio/AI/gitrep/runtime-probes/...`) or host-specific configuration
   that must not appear in public git history
2. **Surface discipline** — `public-surface.md` defines what is *supported*;
   this document defines what is *safe to ship* in a public repo

These two concerns are not the same. An `internal` surface may be safe to ship
(it just isn't supported); a `supported` surface may still require sanitization
if it embeds private paths.

## 2. Safe to Export As-Is

The following are safe to include in a public repository without modification:

### 2.1 Runtime source code

- `owlmlx/` — all Python source modules
- `tests/` — all test files
- `conftest.py`
- `pyproject.toml`
- `.python-version`
- `scripts/` — all operator scripts

### 2.2 Core documentation

- `README.md`
- `AGENTS.md`
- `docs/source-of-truth/*.md` — **except** the files listed in §3 below
- `docs/handoff/*.md`

### 2.3 Evidence structure (safe to export; data may be sparse on a fresh clone)

- `files/evidence/owlmlx/comparative-evidence/` — schema-valid JSONL artifacts
- `files/evidence/owlmlx/model-release-candidates/` — schema-valid JSONL artifacts
- `files/evidence/owlmlx/external-customer-evidence/` — schema-valid JSONL artifacts
- `files/execution-prompts/owlmlx/` — coordinator prompt files

### 2.4 Supporting directories

- `docs/source-of-truth/gemma4-mtp-drafter/` — benchmark data, no private paths

## 3. Requires Sanitization Before Export

The following files contain private absolute paths or host-specific references
that must be replaced or annotated before appearing in a public repository:

### 3.1 `docs/source-of-truth/reference-runtime-comparison-matrix.md`

Section 2 ("Comparison Inputs") previously listed probe input files under
private paths. **This sanitization is already applied as of 2026-05-10:**
the three paths now read:

```
<runtime-probes repo>/2026-04-16-mlx-omlx-vmlx-baseline-investigation.md
<runtime-probes repo>/omlx-probe/README.md
<runtime-probes repo>/vmlx-probe/README.md
```

No further action required for this file. The factual content (TPS numbers,
verdicts, honest labels) is safe to export.

### 3.2 Evidence JSONL files with private `artifact_path`

Evidence JSONL files currently contain private absolute paths in `artifact_path`
fields pointing to local model weight directories. As of 2026-05-10, the
affected files include all ledgers under
`files/evidence/owlmlx/model-release-candidates/` and
`files/evidence/owlmlx/runtime-test-runs/audit-ledger.jsonl`.

These paths point to local model directories (e.g., MLX weights under a
personal AI directory). They are not credentials or secrets, but they expose
the operator's home directory path.

**Required action before public export:** strip or replace `artifact_path`
field values that begin with `/Users/` in all affected JSONL files. Replace
with the basename or a relative path placeholder.

Scan command to verify:
```bash
grep -r '/Users/' files/evidence/ --include='*.jsonl' -l
```

The schema requires `artifact_path` to be a non-empty string when present;
relative paths satisfy this.

### 3.3 Docs with incidental private paths in examples

Several `docs/source-of-truth/*.md` files contain private absolute paths in
example commands, hardware spec references, or evidence pointers. Most are
internal surfaces and do not need to be in the public export at all.

For any doc listed in `public-surface.md` §6 that is exported: replace any
literal home-directory path with `<local-path>` before committing to the
public repo. Internal docs not listed in `public-surface.md` §6 may be
excluded from the public export entirely.

## 4. Must Not Be Exported

The following directories and files must not appear in a public repository:

### 4.1 Phase45 internal exactness artifacts

The `phase45-*.md` family under `docs/source-of-truth/` is listed as internal
in `public-surface.md` §8. These files contain correctness-level seam detail
that is not part of the public surface. Export only if intentionally promoting
internal truth to public (requires a `public-surface.md` update first).

Current list of explicitly internal doc families:
- `docs/source-of-truth/phase45-*.md` (all files matching this pattern)
- `docs/source-of-truth/owlmlx-release-floor-*.md` (handoff docs for floor
  closure coordination; internal process truth)

### 4.2 Private session data

- Any file with a path component containing the operator's home directory
  literal (e.g., `/Users/yeemio/`)
- `.env` files or any file matching `*.env`
- Any credential, token, or API key file

### 4.3 Build artifacts and caches

Standard `.gitignore` exclusions apply:
- `.venv/`
- `__pycache__/`
- `*.pyc`, `*.pyo`
- `dist/`, `build/`, `*.egg-info/`
- `.pytest_cache/`
- `*.swp`, `.DS_Store`

## 5. `.gitignore` Policy for Public Repo

At minimum, the public repository's `.gitignore` must cover:

```
.venv/
__pycache__/
*.pyc
*.pyo
dist/
build/
*.egg-info/
.pytest_cache/
.DS_Store
*.swp
.env
*.env
```

Phase45 internal docs should remain in the repo but do not need to be gitignored
(they are internal by label, not by exclusion from git). If intentional exclusion
is desired, they can be listed explicitly.

## 6. Pre-Export Checklist

Before pushing to a public remote:

1. Confirm `reference-runtime-comparison-matrix.md` §2 has no private absolute
   paths (see §3.1 above)
2. Scan `files/evidence/**/*.jsonl` for `/Users/` prefix in any field value:
   ```bash
   grep -r '/Users/' files/evidence/ --include='*.jsonl' -l
   ```
3. Confirm no `.env` file exists at any depth:
   ```bash
   find . -name '*.env' -not -path './.venv/*'
   ```
4. Run `uv run pytest` — must pass (currently `1419 passed, 3 skipped` baseline)
5. Confirm README first screen communicates developer-preview label

## 7. Update Rule

This document is updated when:

- a new file category is identified that requires sanitization
- a previously private path is resolved to a safe relative form
- new evidence directories are added to `files/evidence/`
- the `public-surface.md` internal-surface list changes in a way that affects
  export classification

Schedule pressure is not an update reason.
