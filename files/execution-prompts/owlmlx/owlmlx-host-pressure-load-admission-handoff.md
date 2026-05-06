# owlmlx Host Pressure Load Admission Handoff

> Date: 2026-05-05
> Outcome: `owlmlx_host_pressure_load_admission_barrier_introduced`
> Scope: runtime-owned host-visible pressure sampling before model load; no
> private Metal allocator oracle, no automatic eviction, no legacy service
> shutdown.

## 1. Why This Round Exists

The Qwen3.6-35B-A3B live incident showed that a process can return from
ordinary RSS pressure while the runtime still needs a conservative first-OOM
prevention layer. The existing cooldown handles the post-OOM child-loss path.
This round adds the pre-load host-pressure gate.

## 2. What Landed

- New `owlmlx.host_pressure` module.
- `RuntimeKernel.load_model(...)` samples host pressure before model load.
- `host_pressure_block` rejects new loads before backend load starts.
- `/v1/runtime/status` exposes cached `host_pressure`; status reads do not
  shell out.
- `owlmlx.memory_pressure_contract` now reports `host_pressure_barrier` when
  the cached load-admission sample blocks new loads.

## 3. Honest Boundary

This is host-visible macOS pressure sampling from `memory_pressure` output. It
does not claim:

- private Metal allocator pressure visibility
- pressure-ranked model eviction
- automatic reclaim
- automatic restart or quarantine
- release-ready / parity / replacement status

## 4. Verification To Run

```bash
pytest -q tests/test_host_pressure.py tests/test_memory_pressure_contract.py
pytest -q tests/test_runtime_kernel.py -k "host_pressure or unload or restart or status_dict"
pytest -q tests/test_runtime_server.py -k "runtime_status or memory_pressure_contract"
python3 -m py_compile owlmlx/host_pressure.py owlmlx/runtime/kernel.py owlmlx/memory_pressure_contract.py
git diff --check -- owlmlx/host_pressure.py owlmlx/runtime/kernel.py owlmlx/memory_pressure_contract.py tests/test_host_pressure.py tests/test_runtime_kernel.py tests/test_memory_pressure_contract.py tests/test_runtime_server.py docs/source-of-truth/runtime-status-schema.md docs/source-of-truth/memory-pressure-contract.md files/execution-prompts/owlmlx/owlmlx-host-pressure-load-admission-handoff.md
```

## 5. Next Runtime Gap

If this lands cleanly, the next gap is not another status field. It is the
pre-load decision quality for large-model placement: combining model profile,
current host pressure, and known per-model peak RSS into an admission verdict
that OwlOps can compare across repeated records.
