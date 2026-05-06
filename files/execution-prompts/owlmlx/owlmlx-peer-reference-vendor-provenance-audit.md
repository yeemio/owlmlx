# owlmlx Peer Reference Vendor Provenance Audit

> Coordinator: owlmlx
> Date: 2026-05-05
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`
> Outcome label: choose one of
> `owlmlx_peer_reference_vendor_provenance_audit_closed` or
> `owlmlx_peer_reference_vendor_provenance_audit_still_blocked`

## 1. Goal

Close the narrow legal/provenance question for the only two current
`vendor_candidate_requires_license_review` items from the peer-reference
mechanism audit:

1. oMLX sampler/RNG safety primitive
2. vMLX DeepSeek V4 JANGTQ/DSV4 loader references

This is an audit-only lane. Do not implement or vendor code.

## 2. Required Reading

Read first:

1. `AGENTS.md`
2. `docs/source-of-truth/peer-reference-mechanism-audit-for-model-profiles.md`
3. `docs/source-of-truth/model-release-candidate-program.md`
4. `docs/source-of-truth/release-readiness-execution-plan.md`

Then inspect primary source snapshots:

- oMLX repository license / pyproject / candidate sampler file
- vMLX repository license / pyproject / DSV4 loader and routing files
- any JANG/JANGQ/JANGTQ dependency metadata referenced by the vMLX DSV4 path

Use local read-only clones if present under:

- `/tmp/owlmlx-peer-reference-audit-20260505`
- `/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe`
- `/Users/yeemio/AI/gitrep/runtime-probes/vmlx-probe`

If these are missing or stale, re-fetch/read primary sources read-only. Do not
edit external repos.

## 3. Hard Boundaries

- Do not vendor code.
- Do not modify runtime code.
- Do not modify external repos.
- Do not run model loads.
- Do not claim any code is approved for import unless license/provenance is
  actually sufficient.
- Keep `oMLX`, `vMLX`, and `vllm-mlx` described as peer reference runtimes.
- Keep `mlx-lm` described as ecosystem dependency/substrate.

## 4. Required Output

Create:

- `docs/source-of-truth/peer-reference-vendor-provenance-audit.md`
- `files/execution-prompts/owlmlx/owlmlx-peer-reference-vendor-provenance-audit-handoff.md`

Update `docs/source-of-truth/master-outline.md` if the new truth document is
added.

## 5. Audit Matrix

For each candidate, answer:

- candidate name
- peer/reference repo
- source commit or package version inspected
- files/modules inspected
- license observed
- NOTICE / attribution requirements
- transitive dependency concerns
- model asset or quantization artifact concerns
- can code be vendored now: `yes`, `no`, or `not_yet`
- if `not_yet`, exact blocker
- recommended route: `rewrite`, `vendor_after_review`, `do_not_adopt`,
  or `ecosystem_use_only`

## 6. Verification

Run:

```bash
git diff --check
rg -n "release-ready|production-grade|parity|equivalent|replacement|beats|wins" \
  docs/source-of-truth/peer-reference-vendor-provenance-audit.md \
  files/execution-prompts/owlmlx/owlmlx-peer-reference-vendor-provenance-audit-handoff.md
```

If hits occur only in forbidden-claim sections, record as non-blocking. Fix any
positive current claim.

## 7. Final Report

Return:

- outcome label
- files changed
- source commits/versions inspected
- verdict for oMLX sampler candidate
- verdict for vMLX DSV4 candidate
- blockers if any
- recommended next implementation rule
