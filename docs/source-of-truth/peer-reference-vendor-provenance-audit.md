# owlmlx Peer Reference Vendor Provenance Audit

> Status: authoritative audit
> Updated: 2026-05-05
> Scope: provenance and license review for the two
> `vendor_candidate_requires_license_review` items identified by
> `peer-reference-mechanism-audit-for-model-profiles.md`.

## 1. Outcome

Outcome label:
`owlmlx_peer_reference_vendor_provenance_audit_closed`.

This audit closes the narrow provenance question for the current vendor
candidates. It does not vendor code, approve code import, modify runtime code,
edit external repositories, or run model loads.

The immediate implementation rule is:

- prefer owlmlx-owned rewrites and direct ecosystem dependency use
- do not copy peer-runtime code until a later legal/provenance gate records the
  exact source file, source commit or package, license text, attribution notice,
  local need, and isolated tests
- keep DeepSeek V4 / DSV4 work in the experimental adapter lane only

## 2. Sources Inspected

Primary source snapshots were read-only. The existing local probes were used
where present, and fresh raw primary files plus package metadata were fetched
into `/tmp/owlmlx-peer-reference-audit-20260505` because the local probes did
not contain every candidate file named by the prior mechanism audit.

| Source | Version or commit inspected | Files inspected | License observed |
|---|---:|---|---|
| oMLX local probe | `d3c328f6d0a1dd4641808d75ccc5d08af6a71898` | `pyproject.toml`, `LICENSE` | Apache-2.0 |
| oMLX fresh primary raw snapshot | `bac678ec72c97e497d05c3c6d637fa54f1b3d7e3` | `pyproject.toml`, `LICENSE`, `omlx/utils/sampling.py` | Apache-2.0 and file SPDX `Apache-2.0` |
| vMLX local probe | `9fe1bb7e8a99c9d5cd8718d61f798a13e222fcfe` | `pyproject.toml`, `LICENSE`, `vmlx_engine/utils/jang_loader.py`, local JANG references | Apache-2.0 |
| vMLX fresh primary raw snapshot | `3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69` | `pyproject.toml`, `LICENSE`, `vmlx_engine/loaders/load_jangtq_dsv4.py`, `vmlx_engine/utils/tokenizer.py`, `vmlx_engine/utils/jang_loader.py` | Apache-2.0 and file SPDX `Apache-2.0` |
| PyPI `jang` wheel | `jang==2.5.21` | `jang-2.5.21.dist-info/METADATA`, `jang_tools/load_jangtq.py`, `jang_tools/dsv4/mlx_model.py` | metadata says Apache-2.0 |

Network note:

- `git clone` of the peer repositories failed twice due GitHub TLS/empty-reply
  errors, so fresh source files were fetched by raw primary URLs instead.
- `git ls-remote` succeeded for oMLX `HEAD`; vMLX `HEAD` was resolved through
  the GitHub commits API.

## 3. Candidate Matrix

| Candidate | Peer/reference repo | Source inspected | Files/modules inspected | License observed | NOTICE / attribution requirements | Transitive dependency concerns | Model asset or quantization artifact concerns | Can code be vendored now | Exact blocker | Recommended route |
|---|---|---:|---|---|---|---|---|---|---|---|
| oMLX sampler/RNG safety primitive | oMLX peer reference runtime | `bac678ec72c97e497d05c3c6d637fa54f1b3d7e3` fresh raw snapshot, plus local probe `d3c328f6d0a1dd4641808d75ccc5d08af6a71898` for repo metadata | `omlx/utils/sampling.py`, `pyproject.toml`, `LICENSE` | Apache-2.0; sampler file has SPDX `Apache-2.0`; package metadata also declares Apache-2.0 | If copied later, preserve Apache-2.0 license text, file SPDX, source commit, file path, modification notice, and any NOTICE file if one appears in a later reviewed source package | The file states it is an mx.compile-free reimplementation of `mlx_lm.sample_utils.make_sampler`; the inspected oMLX snapshot pins `mlx-lm` to `ed1fca4cef15a824c5f1702c80f70b4cffc8e4dd`, so a later gate must verify whether the copied shape is derived only from Apache-licensed oMLX code or also needs MIT `mlx-lm` attribution | None for model assets; this is sampler/runtime logic only | `not_yet` | owlmlx has not reproduced the exact RNG-state failure locally in this lane, and no lane-owned attribution/NOTICE bundle or focused tests exist for imported sampler code | `rewrite` first; `vendor_after_review` only if owlmlx reproduces the failure and a later legal/provenance gate records attribution and tests |
| vMLX DeepSeek V4 JANGTQ / DSV4 loader references | vMLX peer reference runtime plus `jang` package metadata | vMLX `3ae0b234cc1e4d2a0870ed36683afcf8ba0f6d69`; `jang==2.5.21`; local vMLX probe `9fe1bb7e8a99c9d5cd8718d61f798a13e222fcfe` for repo metadata | `vmlx_engine/loaders/load_jangtq_dsv4.py`, `vmlx_engine/utils/tokenizer.py`, `vmlx_engine/utils/jang_loader.py`, `jang_tools/load_jangtq.py`, `jang_tools/dsv4/mlx_model.py`, `pyproject.toml`, `LICENSE`, wheel `METADATA` | vMLX is Apache-2.0; DSV4 loader file has SPDX `Apache-2.0`; PyPI `jang` metadata says Apache-2.0 | If copied later, preserve Apache-2.0 license text, file SPDX, source commit or package version, file path, modification notice, and explicit attribution for vMLX and JANG/JANGQ code paths | vMLX `pyproject.toml` now makes `jang>=2.5.15` a hard dependency for JANG / MXTQ / JANGTQ runtime; `jang==2.5.21` depends on `safetensors`, `numpy`, `tqdm`, `huggingface_hub`, and `jinja2`, with optional MLX/VLM/Torch extras. The vMLX loader delegates to `jang_tools.load_jangtq.load_jangtq_model` and imports `jang_tools.dsv4`, `jang_tools.turboquant`, and DSV4 model/cache code | DSV4 use depends on JANGTQ-stamped model bundles, `jang_config.json`, packed safetensors shards, sidecar cache files such as `jangtq_stacked.safetensors` / `jangtq_stacked.json`, and upstream model/license terms. Those artifact terms were not closed by this code audit | `not_yet` | the candidate is not self-contained vMLX code; it depends on JANG package internals, DSV4 model code, TurboQuant kernels, sidecar artifact semantics, and model-asset terms that require a dedicated adapter/provenance gate | `ecosystem_use_only` for `jang` as a package where acceptable; otherwise `rewrite` an owlmlx-owned DeepSeek adapter. Do not copy vMLX/JANG loader code without a later dedicated gate |

## 4. Allowed Reference Mechanisms

The following mechanisms are allowed to inform the next owlmlx-owned work:

- sampler/RNG drift tests using direct `mlx-lm` and owlmlx wrapper paths
- sampler API shape, only as behavior to test or re-express in owlmlx-owned
  code
- DSV4 model-type registration as a concept
- DSV4 stop-token, chat, reasoning, and cache-caution metadata as experimental
  adapter inputs
- JANG package use as an explicit ecosystem dependency candidate, provided the
  lane records package version, dependency set, and artifact terms
- DeepSeek V4 sidecar/cache manifest ideas as experimental pressure-lane
  research, not as a mainline capability label

## 5. Still Forbidden Or Blocked

The following remain blocked after this audit:

- copying `omlx/utils/sampling.py` into owlmlx without local need,
  attribution, and tests
- copying `vmlx_engine/loaders/load_jangtq_dsv4.py` or broad
  `vmlx_engine/utils/jang_loader.py` code into owlmlx
- importing JANG/JANGQ model-bundle assumptions without recording the model
  artifact license and `jang_config.json` provenance
- promoting DeepSeek V4 / DSV4 behavior into the mainline model matrix
- treating oMLX, vMLX, or vllm-mlx as upstream identity sources
- making any stronger readiness or comparative claim from this audit

## 6. Next Implementation Rule

The next runtime-owned closure round may reference:

- oMLX sampler behavior as a test oracle for a narrow RNG/sampler-drift
  investigation
- vMLX/JANG DSV4 mechanisms as experimental DeepSeek adapter research
- `jang` package metadata as a dependency/provenance input

It must not vendor peer-runtime code. If direct code import becomes necessary,
open a new gate whose output includes source commit/package version, license,
NOTICE handling, attribution text, local reproduction evidence, and focused
tests before any import.
