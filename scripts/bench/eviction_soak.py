"""Eviction soak — Stage 4 placeholder.

Goal: replicate PR #649's verification claim ("50-round soak test 27B ↔ 35B:
zero memory accumulation, active memory locked at 33.1GB ± 0.0GB") as a
runnable bench, then run the same workload against oMLX and vMLX for a
comparative ledger entry.

This file is intentionally a stub. Stage 4 implements it. Until then it
exists to:

1. Reserve `scripts/bench/eviction_soak.py` as the canonical path so
   docs and the comparative-evidence ledger can reference it without
   churn.
2. Encode the design constraints in code shape, not just prose, so the
   contract for Stage 4 is unambiguous when work starts.

Design constraints
------------------

- **N model switches between two models of different size** — default
  N=50, as in PR #649. Smaller models surface signal faster on M-chip
  variants with less unified memory.
- **Record `mx.get_active_memory()` after every settle barrier** —
  the bench's verdict is "did active memory stay flat across N rounds"?
  not "did the model load succeed".
- **Output JSONL to `files/evidence/owlmlx/bench/eviction_soak/<timestamp>.jsonl`** —
  one line per round, fields:
    {"round": int, "switch": "A→B"|"B→A",
     "active_memory_gb_before": float,
     "active_memory_gb_after_load": float,
     "active_memory_gb_after_unload_settled": float,
     "settle_barrier_iterations": int,
     "settle_barrier_duration_ms": float,
     "watermark_before": "GREEN"|"YELLOW"|"RED"|"FATAL"|"UNKNOWN",
     "watermark_after": ...,
     "ok": bool, "drift_gb": float}
- **Drift criterion** — total reclaim drift across N rounds must be
  ≤ 0.5 GB. Above that, the run fails and the script exits non-zero.
- **Comparison mode** — `--runtime owlmlx|omlx|vmlx` switches the
  backend driver. Same workload across all three, same JSONL schema.
  PR #649's settle barrier is in oMLX main now (commit a34615e); vmlx
  has no equivalent — the comparison will surface that.

Out of scope for this script
----------------------------

- Multi-model > 2. The signal is the swap path, not a fan-out workload.
- Prompt diversity. Use a single fixed prompt; this isn't a quality
  bench, it's a memory accounting bench.
- Continuous batching. Each round is one full generation, then unload.

CLI shape (when implemented)
----------------------------

    python -m scripts.bench.eviction_soak \\
        --runtime owlmlx \\
        --model-a Qwen3.6-27B-MLX-4bit \\
        --model-b Qwen3.6-35B-A3B-MLX-4bit \\
        --rounds 50 \\
        --output files/evidence/owlmlx/bench/eviction_soak/

Stage 4 entry checklist
-----------------------

[ ] Implement the bench loop against owlmlx's runtime kernel.
[ ] Decide settle-barrier observability: trust kernel-reported settle
    iterations or measure independently from outside the kernel?
[ ] Wire `--runtime omlx` driver (cherry-pick the a34615e settle API).
[ ] Wire `--runtime vmlx` driver (no settle equivalent — measure
    accumulation directly).
[ ] First evidence ledger entry: `M5_Max_128GB_qwen27_qwen35_n50_<date>`.
"""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "scripts/bench/eviction_soak.py is a Stage 4 placeholder.\n"
        "See the module docstring for the design contract.",
        file=sys.stderr,
    )
    return 2  # EX_USAGE — explicit "not implemented yet" exit code


if __name__ == "__main__":
    raise SystemExit(main())
