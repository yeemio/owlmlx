# owlmlx Cache Manager — Scaffold Landing Round (C-1)

## 你是谁

你是 `owlmlx` 主线执行者。

native MLX backend 已完成 B-1 / B-1.1 / B-1.2 证据链：本机
Qwen3.6-35B-A3B 已 admitted，adapter real lifecycle evidence 已收集；
是否 `partial → supported` 留给后续 promotion-gate round。当前
`native-mlx-backend-capability-matrix.md §7 Recommended Next Round` 把
后续杠杆指向了**七条线之外**的 scaffold 地基：

> **Line 5 — Cache / scheduler depth (`behind`)**: begins with
> `cache_manager.py` scaffold (C-1)

本轮就是 C-1：在 `owlmlx/` 包里**新增** `cache_manager.py` ownership
domain，并把它和 `cache_truth.py`、`mlx_lm.models.cache`、141 个现有
`cache_*.py` 模块的边界**写实**。

本轮是 **scaffold-grade landing**，不是 feature implementation。

## 本轮唯一目标

落地 KV cache lifetime 的**所有权域**（ownership domain），让后续轮
（eviction policy / prefix reuse / cross-request keying）有一个 frozen
contract 可以扩展。

scaffold 仅暴露 **single-request semantics**：每次 `acquire_for_request`
直接调用 `mlx_lm.models.cache.make_prompt_cache(model)`，产生**全新**的
upstream cache object，不查任何之前的 handle，不 emit 任何 reuse / hit /
eviction event。

## 本轮**不**做的事（硬规则）

1. **不**改 `owlmlx/runtime/mlx_native_backend.py` —— scaffold 不接进
   adapter；wiring 是后续轮的事
2. **不**改 `owlmlx/cache_truth.py` —— legacy oMLX SSD/hot-cache schema 域
3. **不**改 141 个现有 `cache_*.py` 中的任何一个 —— pre-claim contract /
   evidence / closure rung 的边界保持不变
4. **不**改 `owlmlx/runtime/server.py`、`owlmlx/serving.py`、
   `pyproject.toml`、`uv.lock`、`.python-version`、`conftest.py`、
   `README.md`、任何已有 test 文件
5. **不**改 `docs/source-of-truth/native-mlx-backend-capability-matrix.md`
   —— scaffold 不促升任何行
6. **不**实现 eviction policy（`LRUPromptCache.trim_to`）
7. **不**实现 prefix reuse（`PromptTrie.search`）
8. **不**实现 cross-request handle keying
9. **不**新增 dependency；只用 stdlib + 已有 mlx_lm 模块引用形状
10. **不**接 serving path —— scaffold 完全独立
11. **不**跑 pytest —— 测试要在 fake mlx_lm 注入下能通过，但本轮不验证
12. **不**做 `git add` —— operator stages
13. **不**用 evidence-language calibration 禁止的措辞（"is supported" /
    "is loadable" / "production-ready" / "complete"）—— 严格降格成
    "scaffold contract" / "extension point" / "not yet bound to runtime
    path" / "single-request semantics enforced"

## Subagent A research（fact base，不要重新验证）

以下事实作为本轮 fact base，**不要**通过 pytest / loads 重新验证：

- `owlmlx/cache_truth.py` (270 lines) 是 legacy oMLX SSD/hot-cache
  schema —— `CacheProfile`、`CacheFlags`、`TurboQuantCacheSafety`。**与
  KV cache 零重叠**。`cache_manager.py` 是独立 ownership domain
- `mlx_lm 0.31.2` cache surface 在
  `.venv/lib/python3.11/site-packages/mlx_lm/models/cache.py`：
  - top-level：`make_prompt_cache(model, max_kv_size=None) -> List[Any]`、
    `save_prompt_cache`、`load_prompt_cache`、`can_trim_prompt_cache`、
    `trim_prompt_cache`
  - cache types：`KVCache`、`RotatingKVCache`、`QuantizedKVCache`、
    `ConcatenateKVCache`、`ChunkedKVCache`、`ArraysCache`、`BatchKVCache`、
    `BatchRotatingKVCache`、`CacheList`、`TokenBuffer`
  - prefix-reuse：`PromptTrie` (1498-1586) + `LRUPromptCache(max_size=10,
    max_bytes=1<<63)` (1589-1729) —— 已经是接近完整的 eviction 引擎
- 现有 native binding：`owlmlx/runtime/mlx_native_backend.py` 第 207-240
  行有 `_make_fresh_prompt_cache(mlx_lm, session)`，per-request 单一
  cache。**本轮不动它**
- `owlmlx/` 下 141 个 `cache_*.py` 文件 —— 没有一个 own KV-cache
  lifetime。**本轮不动它们**
- `owlmlx/cache_residency_evidence.py:19-28` 声明 5 个 residency 计数器：
  `entries`、`resident_bytes`、`reuse_events`、`hit_count`、
  `eviction_events`。scaffold 必须以 zero-baseline read-only 计数器形式
  暴露这 5 项，让现有 residency_evidence / closure_rung 消费者在真实
  实现 land 之前就不 break

## 本轮**要**做的事（5 个 deliverable）

### Deliverable 1：`owlmlx/cache_manager.py`（新增）

scaffold module。content shape：

- module docstring：明示 ownership statement（own 什么、不 own 什么、
  与 `cache_truth.py` / `mlx_lm.models.cache` 的边界）；明示
  "single-request semantics enforced; cross-request reuse intentionally
  absent in scaffold"
- frozen dataclass `CacheManagerCounters`：5 字段（match
  `cache_residency_evidence.py`），全部默认 0；`to_dict()` method
- frozen dataclass `CachedRequestHandle`：`model_id: str`、
  `cache_object_id: int`、`created_at: float`、
  `cross_request_reuse_claimed: bool = False`
- class `CacheManager`：
  - `__init__(self)` —— 空 per-model registry + zero counters
  - `acquire_for_request(self, *, model_id: str, mlx_lm_module, model)
    -> CachedRequestHandle` —— 调用
    `mlx_lm_module.models.cache.make_prompt_cache(model)`（用与
    `_resolve_make_prompt_cache` 一致的 defensive attribute walk），
    记录 handle，`entries` += 1，返回 handle。**不**按 prefix key，
    **不**查之前的 handle
  - `release_for_request(self, handle)` —— drop reference，**不**改
    counter（release 在 single-request mode 下是 incidental）
  - `counters(self) -> CacheManagerCounters` —— frozen snapshot
  - `status_dict(self) -> dict` —— 给 runtime status 的 payload shape
- 显式 "future extension point" 注释（注释而已，**不**写 method stub）：
  - (a) eviction policy（reference `LRUPromptCache.trim_to`）
  - (b) prefix reuse（reference `PromptTrie.search`）
  - (c) cross-request handle keying

module top docstring 必须为：

```python
"""owlmlx KV cache manager scaffold.

Owns the in-process, per-request KV cache lifetime for the native MLX
backend. Distinct from ``cache_truth.py`` (legacy oMLX SSD/hot-cache
schema). Distinct from the upstream ``mlx_lm.models.cache`` primitives
(which provide ``make_prompt_cache``, ``KVCache``, ``LRUPromptCache``).

Scaffold-grade. The current binding enforces single-request semantics:
each ``acquire_for_request`` produces a fresh upstream cache object via
``mlx_lm.models.cache.make_prompt_cache``; cross-request prefix reuse,
LRU eviction, and residency tracking beyond a zero-baseline counter
ledger are explicit extension points, not implementations. See
``docs/source-of-truth/cache-manager-architecture.md``.

This module is NOT wired into ``MlxNativeBackend`` in this scaffold
round. Wiring is a follow-up round and requires a §1a-style promotion
walkthrough on the native MLX backend capability matrix.
"""
```

### Deliverable 2：`docs/source-of-truth/cache-manager-architecture.md`（新增）

architecture doc，~1200-1800 词。Sections：

1. Status / scope / authorship line（Status: authoritative, Updated:
   2026-05-08）
2. Why this module exists —— 与 `cache_truth.py` 的区分；cite 七条线
   评估 Line 5 (`behind`)
3. Ownership boundaries —— 表格：cache_manager 拥有什么 vs
   `cache_truth.py` 拥有什么 vs `mlx_lm.models.cache` 提供什么 vs
   现有 141 个 `cache_*.py` 已覆盖什么。明示 pre-claim files
   (`cache_pre_claim_admission_contract.py:53-58`) 禁止从 staging seam
   碰 cache，cache_manager 尊重该约束
4. Scaffold contract —— public API 和 invariants
5. Single-request semantics —— 明示且 intentional —— 为什么 scaffold
   不做 cross-request reuse（即使 `LRUPromptCache` 触手可及）
6. Counter contract —— 5 计数器 zero-baseline ledger；
   `cache_residency_evidence.py` 消费者怎么 query
7. Extension points (not implemented) —— eviction policy / prefix reuse /
   cross-request keying —— 各自描述为后续轮责任，给出对应 upstream
   primitive
8. Promotion-gate coupling —— 明示：scaffold **不**促升任何 matrix
   行；后续 wiring + real-load evidence + §1a walkthrough 才能促升
9. What this doc does not claim —— list

### Deliverable 3：`tests/test_cache_manager.py`（新增）

5-8 个 test，**全部 fake mlx_lm 注入**（不要 import 真 mlx_lm）：

- `test_cache_manager_starts_with_zero_counters`
- `test_acquire_for_request_returns_handle_with_correct_model_id`
- `test_acquire_calls_make_prompt_cache_via_attribute_walk`
- `test_acquire_increments_entries_counter`
- `test_consecutive_acquires_produce_distinct_cache_object_ids`
- `test_release_drops_handle_reference_without_changing_counters`
- `test_status_dict_shape_matches_residency_evidence_consumer_expectation`
- `test_acquire_when_make_prompt_cache_attribute_missing_raises_clear_error`

参考 `tests/test_mlx_native_backend.py` 的 fake module pattern。测试
**不**依赖 optional `runtime` extra 安装，**不**导入真 mlx_lm。

### Deliverable 4：`files/execution-prompts/owlmlx/owlmlx-cache-manager-scaffold-landing.md`（新增）

本 prompt（authorize C-1 round 的本身）。

### Deliverable 5：`files/execution-prompts/owlmlx/coordinator-checkpoint-cache-manager-scaffold-landed.md`（新增）

本轮的 coordinator-checkpoint。Sections：

- Verdict
- What This Checkpoint Is
- What Is Now Frozen Exact
- Provenance（none —— scaffold not promotion）
- What This Checkpoint Closes
- What This Checkpoint Does Not Claim
- Test Counts
- Notable Implementation Choices
- Next Authorized Round

## 守则提醒

- **read-only outside the 5 deliverable paths** —— 严格执行
- **evidence-language calibration** —— 不写 "is supported" / "is
  loadable" / "production-ready" / "complete"；写 "scaffold contract" /
  "extension point" / "not yet bound to runtime path" /
  "single-request semantics enforced"
- **promotion gate respect** —— 不动
  `docs/source-of-truth/native-mlx-backend-capability-matrix.md`
- **no staging** —— 不跑 `git add`
- **executor phase no pytest run** —— 不把 scaffold 自测当 promotion
  证据；coordinator/reviewer 可以后置跑 focused pytest 做落地验证
- **no new dependencies** —— stdlib only
- **single-request semantics 不可妥协** —— 不引入 cross-request handle
  key、prefix lookup、eviction loop。这些是 doc 里的 extension point，
  不是本轮代码
- **edits 完成后跑 `git status --short`** —— 确认只有 5 个文件 new
  / modified

## 第一组命令

```bash
git status --short
ls owlmlx/cache_*.py | wc -l
ls owlmlx/cache_manager.py 2>&1 | head -2
grep -n "entries\|resident_bytes\|reuse_events\|hit_count\|eviction_events" \
  owlmlx/cache_residency_evidence.py | head -10
```

## 交付格式

完成后简报（< 200 词）：

- 5 个文件路径 + 一行描述
- `git status --short` 输出，证明 round-scope 干净
- 任何 caveat / discipline edge case 决策

## 下一轮候选（不在本轮范围）

- **C-1.1**（recommended after C-1）：`cache_manager.py` wiring round
  —— 把 scaffold 接进 `MlxNativeBackend`，走 §1a 风格 walkthrough。
  本轮**不**做
- **C-2**：multi-prompt randomized-load repeatability harness，闭
  Line 6（host-stable execution confidence）
- **C-3**：memory governance actuator 包 `mx.clear_cache` /
  `set_cache_limit`，闭 Line 3
- **C-4**：serving surface hardening（request-id middleware、
  per-request timeout、graceful shutdown drain、unified error envelope、
  `/metrics`），闭 Line 4
- **B-2**：sibling candidate admissibility（`Qwen3.6-27B`、
  `gemma-4-31B-it`），breadth not depth
- **B-4**：cooperative cancellation real-stream evidence

C-1 自身只 land ownership domain；后续真正闭 Line 5 还要 C-1.1
（wiring）+ 后续 eviction / prefix reuse / cross-request keying 的若干
轮。本轮 checkpoint 必须明示这一点。
