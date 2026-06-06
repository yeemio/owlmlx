# R2 — Control-Plane Operator Runbook

> design-grade · companion to [`R2-control-plane-closure-spec.md`](R2-control-plane-closure-spec.md) · **promotes nothing**, verification tooling only.
> cutover 前/中，操作员用 owlmlx **现有**控制面 endpoint 验证：(A) 消费者契约闭合、(B) 控制面生命周期可操作。**不翻默认、不去 `:8009`、不晋级任何 capability。**

---

## 0. 三态 verdict

| verdict | 含义 | 退出码 |
|---|---|---|
| `passed` | 全部契约/生命周期步骤通过 | 0 |
| `contract_gap_found` | 至少一个消费者契约不闭合（**诚实落盘的 gap，非崩溃**） | 2 |
| `rehearsal_failed` | 至少一个 operability 步骤失败 | 2 |

---

## 1. 消费者契约 conformance（只读 —— 可直接打 live `:8066`，零风险）

```bash
.venv/bin/python scripts/replacement/r2_control_plane_conformance.py probe-contracts \
  --base-url http://127.0.0.1:8066 \
  --out files/evidence/owlmlx/replacement/r2-control-plane/<ts>-r2-conformance.json
```

只发 GET，不改任何运行态。每契约断言 owlmlx 响应含**消费者实际解析**的字段：

| 契约 | endpoint | 消费者读取的字段 | owlmlx 期望响应 | 来源 |
|---|---|---|---|---|
| `owlcc_preflight_healthz` | `GET /healthz` | HTTP<400; `ok`,`readiness` | `{ok,readiness,active_model_id,model_count,...}` | owlcc/src/preflight.ts:36,57 |
| `owlcc_preflight_v1_models` | `GET /v1/models` | `data[].id` | **status-dict，无 `data[]`** → **gap** | owlcc/src/preflight.ts:119-120 |
| `owlcc_resolution_openai_models` | `GET /v1/openai/models` | `data[].id` | `{object:"list",data:[{id,...}]}` → pass | （OwlCC 的 resolution 面）|
| `owlcoda_gate_openai_models` | `GET /v1/openai/models` | `data[].id` | `{object:"list",data:[{id,...}]}` → pass | owlcoda/src/runtime-probe.ts:61-66 |
| `owlcoda_gate_model_visibility` | `GET /v1/runtime/model-visibility` | `rule`,`contract_version`,`formal_surface.endpoint`,`diagnostic_surface.endpoint`,`loaded_inventory_surface.{endpoint,semantic_role}`,`gate.{owner,kind,models_root}`,`visible_model_ids`,`blocked_model_ids`,`entries[].{model_id,visible,block_reason}` | 全部存在 → pass | owlcoda/src/runtime-probe.ts:93-154; admin/src/api/types.ts:43-63 |
| `owlcoda_gate_loaded_inventory` | `GET /v1/models` | `inventory.entries[].model_id`,`inventory.model_count`,`visibility_contract.loaded_inventory_surface.semantic_role` | 全部存在 → pass | owlcoda/src/runtime-probe.ts:68-84 |
| `owlcoda_gate_runtime_status` | `GET /v1/runtime/status` | `health.readiness`,`backend.healthy`,`inventory.entries[].model_id`,`inventory.model_count`,`backend.loaded_models[].model_id` | probe 报告**实际** owlmlx status 形状；缺字段=诚实 gap | owlcoda/src/runtime-probe.ts:231-245 |

---

## 2. 冻结的 last-mile 契约 —— 模型可用性面

R2 把以下语义定死（cutover 必须遵循）：

- **`GET /v1/openai/models` = 可用性真相**（OpenAI list，`data[].id`，仅 visible 模型）。
- **`GET /v1/models` = 仅已加载**（status-dict：`inventory.entries[].model_id`、`inventory.model_count`、`visibility_contract.loaded_inventory_surface.semantic_role`；**无 `data[]`**）。
- **`GET /v1/runtime/model-visibility` = 诊断面**（visible/technical_preview/blocked + per-model gate reason）。
- **OwlCoda** owlmlx-gate 已**正确**按此读取（`owlcoda/src/runtime-probe.ts`：把 `/v1/openai/models` 当可用性、`/v1/models` 当 loaded-inventory）。
- **OwlCC** preflight 当前读 `GET /v1/models` → `data[].id`（`owlcc/src/preflight.ts:119-120`）。把 `routerUrl` repoint 到 owlmlx 后，owlmlx 的 `/v1/models` 没有 `data[]`，preflight 会找不到模型。
  - **➜ OwlCC 的 R2 cutover 前置：preflight 必须改读 `GET /v1/openai/models` 取可用性。** 这是 `contract_gap_found` 的解法，不是 owlmlx 缺陷（owlmlx 已在 `/v1/openai/models` 提供该 shape）。

---

## 3. 控制面 operability 演练（**bench only** —— 改运行态，吃机器成本）

⚠️ 该命令会 load/evict/restart 真实模型 → **必须在隔离 bench server 上跑，绝不碰默认 daemon `:8066`**。脚本有双重护栏（缺 `--i-understand-bench-only` 或 base-url 命中 8066 端口 → REFUSED/exit 3）。

```bash
# 1) 另起一个隔离 bench server（非 :8066），例如 :8067，按需挂 RC ledger 暴露所需模型
# 2) 跑演练（用最小够用的已注册模型，降成本）
.venv/bin/python scripts/replacement/r2_control_plane_operability.py rehearse \
  --base-url http://127.0.0.1:<bench-port> \
  --model-a <small-model> --model-b <small-model-2> \
  --i-understand-bench-only \
  --out files/evidence/owlmlx/replacement/r2-control-plane/<ts>-r2-operability.json
```

**成本**：每个 `--model-*` 是一次真实加载（GB 级、分钟级）+ eviction + restart。跑前先 surface 成本 + run-now-vs-defer。

演练步骤与断言：`load`（`/healthz`+`/v1/runtime/status` 反映 active/readiness）→ `model_switch`（status 反映新 active）→ `evict`（`/v1/runtime/memory-pressure-eviction` 返回 `selected_victim` + status 反映）→ `restart`（`/v1/runtime/recovery-supervisor-contract` + status 反映）→ `watermark`（`/v1/runtime/memory-watermark` level 全程在已知集合内）。

> 演练只证「现有控制面在状态变迁时报告正确」**一次受控**结论；**不**是 sustained 稳定性（那是 R4 Phase B soak），watermark 仅 per-session health gate。

---

## 4. 读 evidence

证据落 `files/evidence/owlmlx/replacement/r2-control-plane/`：conformance（per-contract verdict + 实际响应摘要）、operability（per-step + lifecycle verdict + bench recipe）、复现（cmd·env·commit·baseURL·model·endpoints）。**诚实**：verdict 仅表 conformance / 受控 operability 已验证，**非** parity/equivalent/replacement-complete。
