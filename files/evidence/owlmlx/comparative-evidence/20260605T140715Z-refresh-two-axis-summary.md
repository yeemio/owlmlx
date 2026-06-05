# Comparative Evidence Refresh Two-Axis Summary

Date: 2026-06-05

Host class: `Mac17,6-arm64-macOS-26.4.1-128GB`

Model: `gemma-4-31B-it-4bit`

Reference runtime: `oMLX` on `127.0.0.1:8063`

owlmlx runtime: isolated benchmark-only native server on `127.0.0.1:8067`.
This server used the current checkout plus an in-process visibility registry
extension for `gemma-4-31B-it-4bit`; the normal `127.0.0.1:8066` model
visibility was not changed.

## Verdict

Two measured records were produced:

| Workload | owlmlx completed / failed | oMLX completed / failed | owlmlx TPS | oMLX TPS | owlmlx TTFT ms | oMLX TTFT ms | owlmlx wall ms | oMLX wall ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `single_prompt_short` | 5 / 0 | 5 / 0 | 9.6570 | 24.5576 | 1060.3388 | 5205.5068 | 1067.1697 | 5212.4238 |
| `multi_prompt_serial` | 5 / 0 | 5 / 0 | 20.5102 | 22.4831 | 1833.9661 | 22765.7077 | 11807.3667 | 22772.9772 |

Interpretation:

- On the short single-prompt axis, oMLX recorded higher decode throughput.
- On the multi-turn serial axis, owlmlx recorded much lower first-token latency
  and lower mean wall-clock time, while decode throughput was close to oMLX.
- This is a single-host point measurement, not a capability promotion and not a
  general replacement claim.

## Evidence Pointers

- Short prompt measured record:
  `files/evidence/owlmlx/comparative-evidence/20260605T140335Z-refresh-short-omlx-gemma4bit-8067/manifest.json`
- Multi-turn serial measured record:
  `files/evidence/owlmlx/comparative-evidence/20260605T140422Z-refresh-serial-omlx-gemma4bit-8067/manifest.json`
- Ledger:
  `data/comparative-evidence-ledger.jsonl`

## Rejected Warmup Record

An earlier warmup run at
`files/evidence/owlmlx/comparative-evidence/20260605T135821Z-refresh-short-omlx-gemma4bit/manifest.json`
is intentionally not included in the two-axis comparison. It used the normal
`127.0.0.1:8066` owlmlx server, whose default visibility contract did not expose
`gemma-4-31B-it-4bit`; owlmlx returned HTTP 404 for all five attempts. That row
is a configuration/visibility mismatch record, not a performance measurement.

## Startup Notes

oMLX was not installed in a local venv, so it was launched from the local
`/Users/yeemio/AI/gitrep/omlx-upstream` checkout with the owlmlx `.venv`
interpreter after adding the missing runtime dependencies to that venv.

The benchmark-only owlmlx server was launched separately from the normal
`:8066` server to avoid changing the normal visibility surface while still
making the 16G 4-bit Gemma artifact visible to the comparative runner.
