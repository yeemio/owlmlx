# owlmlx Peer Reference Vendor Provenance Audit Handoff

> Date: 2026-05-05
> Executor: B
> Outcome label:
> `owlmlx_peer_reference_vendor_provenance_audit_closed`
> Repo: `/Users/yeemio/AI/gitrep/owlmlx`

## 1. What Closed

The provenance audit for the two current
`vendor_candidate_requires_license_review` items is closed as an audit result:

- oMLX sampler/RNG safety primitive: `not_yet`, use as rewrite/test input first
- vMLX DeepSeek V4 JANGTQ / DSV4 loader references: `not_yet`, use only as
  experimental adapter research or explicit ecosystem dependency input

No code was vendored. No runtime code was modified. No model load was run.

## 2. Files Changed

- `docs/source-of-truth/peer-reference-vendor-provenance-audit.md`
- `docs/source-of-truth/master-outline.md`
- `files/execution-prompts/owlmlx/owlmlx-peer-reference-vendor-provenance-audit-handoff.md`

## 3. Source Versions Inspected

- oMLX local probe:
  `/Users/yeemio/AI/gitrep/runtime-probes/omlx-probe` at
  `d3c328f6d0a1dd4641808d75ccc5d08af6a71898`
- oMLX fresh raw primary snapshot:
  `bac678ec72c97e497d05c3c6d637fa54f1b3d7e3`
- vMLX local probe:
  `/Users/yeemio/AI/gitrep/runtime-probes/vmlx-probe` at
  `9fe1bb7e8a99c9d5cd8718d61f798a13e222fcfe`
- vMLX fresh raw primary snapshot:
  `3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69`
- PyPI package metadata:
  `jang==2.5.21`

Fresh source files and the downloaded wheel were stored under
`/tmp/owlmlx-peer-reference-audit-20260505` for this audit. External
repositories were not edited.

## 4. Allowed To Reference Next

Next owlmlx-owned work may reference:

- oMLX sampler/RNG behavior as a test oracle
- direct `mlx-lm` sampler behavior as the first comparison point
- vMLX/JANG DSV4 registration, stop-token, cache, and sidecar concepts as
  experimental DeepSeek adapter research
- `jang` package metadata as a dependency/provenance input

## 5. Still Forbidden Or Blocked

Still blocked:

- copying oMLX sampler code without local reproduction, attribution, and tests
- copying vMLX DSV4 loader or broad JANG loader code into owlmlx
- relying on JANG/JANGQ model artifacts without explicit artifact-license and
  `jang_config.json` provenance
- upgrading DeepSeek V4 from the experimental adapter lane
- making stronger readiness or comparative claims from this audit

## 6. Verification

Required checks to run:

- whitespace/error diff check for the whole worktree diff
- archived-prompt forbidden-current-claim scan against the audit doc and this
  handoff

Expected result:

- `git diff --check` passes
- the forbidden-claim scan returns no hits in the two lane-owned output files
