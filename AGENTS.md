# Agent Guide For `owlmlx`

This repository is the source-of-truth home for the `owlmlx` runtime line.

## Read Order

If a task does not specify a narrower entry point, read in this order:

1. `README.md`
2. `AGENTS.md`
3. `docs/source-of-truth/master-outline.md`
4. `docs/source-of-truth/product-definition.md`
5. `docs/source-of-truth/system-architecture.md`
6. `docs/source-of-truth/repository-boundaries.md`
7. `docs/source-of-truth/runtime-capability-matrix.md`
8. `docs/source-of-truth/runtime-contracts.md`
9. `docs/source-of-truth/runtime-status-schema.md`
10. `docs/source-of-truth/runtime-governance.md`
11. `docs/source-of-truth/hazardous-operations.md`
12. `docs/source-of-truth/rename-strategy.md`
13. `docs/source-of-truth/contract-mapping.md`
14. `docs/source-of-truth/extraction-inventory.md`
15. `docs/source-of-truth/autonomous-loop-discipline.md`
16. `docs/source-of-truth/roadmap.md`

## Non-Negotiable Project Truth

- `owlmlx` is our own runtime.
- `oMLX`, `vMLX`, and similar projects are reference inputs, not identity
  sources.
- `owlmlx` exists to replace `oMLX`, not to become a permanent patch stack on
  top of it.
- the current desktop product shell repository, historically referred to as
  `local-llm-platform`, sits above `owlmlx`.
- `Kimi` is a first validated specimen on the `large-weight runtime path`, not
  the permanent name of that path.
- `owlmlx` reuses open-source runtime mechanisms freely. Self-owned does not
  mean full rewrite. What is owned is identity, principles, governance, truth
  contracts, and path semantics.

## Writing Rules

- Keep capability labels honest: `supported`, `partial`, `experimental`, or
  `not in scope`
- Do not describe future generalization as current fact
- Do not collapse runtime truth and desktop product truth into one layer
- Do not describe `owlmlx` as "just a fork" or "just a wrapper"
- When borrowing ideas from external runtimes, rewrite them as `owlmlx`
  architecture, not as borrowed branding
- Follow the autonomous loop discipline when iterating on source-of-truth
  (see `autonomous-loop-discipline.md`)
- Respect the adoption model: borrowed code enters as `partial` or
  `experimental`, never automatically as `supported`

## Boundary Discipline

This repository owns:

- Runtime identity
- Runtime architecture
- Runtime capability labels
- Runtime path definitions
- Runtime extraction and packaging plans

This repository does not own:

- Desktop UI source of truth
- Dashboard-first product narratives
- Generic platform orchestration truth unrelated to runtime internals

## Current Working Assumption

The repository has completed source-of-truth bootstrap mode and now operates as
an executable early runtime.

The immediate goal is no longer boundary freeze or specimen-first progress. It
is:

- replacement-grade stability alignment versus `oMLX` / `vMLX`

The immediate question is:

- which replacement-grade stability gap most limits `owlmlx` next, and what is
  the next executable runtime-owned closure round

## Anti-regression rule (Stage 1, 2026-05-11)

After Stage 1 archived 151 spec-as-code modules (cache_stream_*,
cache_pre_claim_*, multi_model_governance_*, etc.) the following module
patterns are **prohibited**:

**Do not create new modules matching these naming patterns:**

- `*_exactness.py`
- `*_carrier.py`
- `*_marker.py`
- `*_harness.py`
- `*_feasibility.py`
- `*_rung.py`
- `*_seam.py`
- `*_charter.py`
- `*_manifest.py` (when serving as in-tree spec, not as runtime artifact metadata)
- `*_evidence.py` (when not consumed by a real runtime decision)
- `*_ledger.py` (when not consumed by a real runtime decision)

**Module-as-spec is forbidden.** A module's reason for existence must be
that some other module in `owlmlx/runtime/` *reads its dataclass fields
or calls its functions*. Files whose entire body is a frozen dataclass
plus a builder that returns hardcoded status strings are documentation,
not code. Put documentation in `docs/`.

**PR-level check before merging any new `.py` in `owlmlx/`:**

```bash
# 1. Does at least one file in owlmlx/runtime/ import this module?
grep -rE "from \.+(\.\.)?<module> import" owlmlx/runtime/

# 2. Does it have any module-level function or method body, not just
#    builder() returning frozen dataclass with literal strings?

# 3. Are its dataclass fields read by name (`.field_name`) anywhere
#    outside the module itself, customer_runtime_evidence, and tests?
```

If 1+3 are NO, the module belongs in `docs/source-of-truth/` as a markdown
contract, not in the package as Python code.

This rule exists because Stage 1 archived 151 modules / 31K LOC that
followed the dataclass+builder+hardcoded-strings pattern with no
runtime consumer reading the fields, AND because LLM-assisted PRs make
the marginal cost of adding such modules approximately zero. Without
this explicit ban, the pattern regrows.
