# owlmlx Release Floor 7/7 Seal Review And Commit

> Date: 2026-04-28
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Executor: single seal reviewer / committer
> Goal: verify the staged release-floor closeout set and produce one clean seal commit if honest

## 1. Role

You are the release-floor seal reviewer and committer for `owlmlx`.

This is not a new implementation round. Do not add runtime features. Do not
continue phase45 narrowing. Do not rerun expensive live comparative evidence or
external customer HTTP probes unless the archived evidence is missing or
internally inconsistent.

Your job is to review the staged release-floor work, confirm the `7 / 7`
release-floor ledger state is honest, ensure no unrelated dirty work is pulled
into the commit, and then commit the staged set if it passes.

## 2. Current Expected Truth

The expected staged truth is:

- `release-readiness-backlog.md` shows all release floors `3.1` through `3.7`
  closed.
- `release-readiness-execution-plan.md` shows `7 / 7` release-floor items
  closed.
- floor `3.6` closed via OwlOps-boundary external runtime-truth consumer
  evidence.
- floor `3.7` closed via runtime-owned public-surface freeze.
- the closeout handoff exists:
  `files/execution-prompts/owlmlx/owlmlx-release-floor-3-6B-3-7B-final-closeout-ledger-sync-handoff.md`
- `7 / 7 closed` is not a release-ready / parity / replacement /
  production-grade claim. The banned vocabulary discipline remains in force.

## 3. Non-Negotiable Boundaries

- Work only in `/Users/yeemio/AI/gitrep/owlmlx`.
- Do not edit OwlOps, OwlCoda, `/Users/yeemio/AI/Agent`, desktop UI, or any
  external repo.
- Do not use `git add -A`.
- Do not use destructive git commands.
- Do not revert unrelated dirty files.
- Do not amend an existing commit.
- Do not include unstaged overlays by accident.
- If a file is `MM` or `AM`, inspect staged and unstaged hunks separately
  before deciding whether the staged snapshot is safe to commit.
- If staged content is mixed with unrelated work that cannot be separated
  safely, stop with `needs_fix` and list the exact files.

## 4. Required Status Audit

Run and record:

```bash
git status --short
git diff --cached --stat
git diff --cached --name-only
git diff --check
```

Then inspect these specifically:

```bash
rg -n "7 / 7|3\\.6 external customer evidence|3\\.7 public surface|owlmlx_release_floor_3_6B_3_7B_final_closeout_closed" \
  docs/source-of-truth/release-readiness-backlog.md \
  docs/source-of-truth/release-readiness-execution-plan.md \
  files/execution-prompts/owlmlx/owlmlx-release-floor-3-6B-3-7B-final-closeout-ledger-sync-handoff.md

rg -n "release-ready|release_ready|parity|equivalent|replaces|replacement|production-ready|production_ready|production-grade|production_grade|superior|wins|beats|matches" \
  docs/source-of-truth/release-readiness-backlog.md \
  docs/source-of-truth/release-readiness-execution-plan.md \
  docs/source-of-truth/public-surface.md \
  files/execution-prompts/owlmlx/owlmlx-release-floor-3-6B-3-7B-final-closeout-ledger-sync-handoff.md
```

The banned-word grep may return negative / forbidden-claim / vocabulary
references. That is allowed. It must not reveal a positive current claim.

## 5. Required Evidence Checks

Confirm these staged or tracked paths exist:

- `docs/source-of-truth/public-surface.md`
- `tests/test_public_surface_contract.py`
- `docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
- `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/external-run-notes.md`
- `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.stdout.json`
- `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.stderr.txt`
- `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.exit-status`
- `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/live-ledger.jsonl`
- `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/http-latest.txt`
- `files/evidence/owlmlx/comparative-evidence/20260428T004500Z/http-history.txt`

Confirm:

- the 3.6 external probe exit status is `0`
- the 3.6 stderr file is empty
- the 3.6 stdout capture includes successful `/v1/runtime/status` and
  `/healthz` HTTP responses
- the 3.5 fresh comparative evidence contains a measured record, not merely
  the earlier invalid / inconclusive evidence
- `public-surface.md` explicitly keeps unlisted surfaces internal by default

## 6. Required Tests

Run this minimum seal matrix:

```bash
pytest -q tests/test_customer_runtime_evidence.py
pytest -q tests/test_public_surface_contract.py
pytest -q tests/test_runtime_comparative_evidence_measured_runner.py
pytest -q tests/test_runtime_server.py -k "comparative_evidence or public_surface or runtime_status"
python3 -m py_compile \
  owlmlx/customer_runtime_evidence.py \
  scripts/runtime_customer_runtime_evidence.py \
  owlmlx/runtime/server.py \
  owlmlx/comparative_evidence_runner.py
git diff --check
```

If the `runtime_server.py -k` selector collects fewer tests than expected, do
not treat that as failure by itself; report the collected/pass count and confirm
the dedicated public-surface and comparative-evidence tests passed.

Do not rerun:

- the heavy same-host measured comparative run
- the OwlOps external HTTP probe
- long phase45 cache suites

unless the archived evidence is missing or contradictory.

## 7. Staged Snapshot Decision

Before committing, answer:

1. Does the staged diff close release floors `3.6` and `3.7` without claiming
   release readiness?
2. Does the staged diff preserve `3.5` measured evidence as the closeout-grade
   comparative record and keep earlier invalid / inconclusive evidence as
   honest trail only?
3. Does the staged diff include the 3.6 external customer evidence artifacts?
4. Does the staged diff include the 3.7 public-surface doc and validation test?
5. Are there any unstaged hunks in `MM` / `AM` files that would make the staged
   commit misleading?
6. Are any unrelated dirty files accidentally staged?

If any answer is negative, do not commit. Return `needs_fix` with exact file
paths and the smallest safe next step.

## 8. Commit Rule

If all checks pass, create exactly one commit from the current index.

Suggested commit message:

```text
owlmlx: seal release-floor readiness at 7 of 7
```

Do not amend. Do not squash into earlier commits. Do not push unless explicitly
asked.

After committing, run:

```bash
git status --short
git log -1 --oneline
```

It is acceptable for unrelated pre-existing dirty files to remain after the
commit. Report them only as residual dirty scope; do not clean them.

## 9. Final Report Format

Return:

```text
verdict: committed | needs_fix | blocked
commit: <short sha and subject, if committed>
release_floor_state: 7/7 closed | not closed
tests:
  - <command>: <result>
staged_scope:
  - <high-level groups committed>
residual_dirty:
  - <short statement; do not list every unrelated file unless it blocks>
blocking_findings:
  - <only if needs_fix/blocked>
non_blocking_notes:
  - <optional>
```

Hard wording rule: do not write that `owlmlx` is release-ready, parity,
replacement-grade, production-grade, superior, wins, beats, equivalent, or
matches `oMLX` / `vMLX`. The correct statement is only that the
release-readiness backlog floors are closed and the project may move to the
technical-preview signoff lane.

