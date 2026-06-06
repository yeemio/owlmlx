# R4 Phase B · B1 — Consumer Flip + Rollback Runbook

> design-grade · companion to [`R4-phaseB-b1-flip-readiness-spec.md`](R4-phaseB-b1-flip-readiness-spec.md) · **promotes nothing**.
> B1 = stage the **OwlCoda** default flip to **owlmlx-primary with `:8009` fallback RETAINED**. EXECUTION（改 config / OwlCC 代码）是 **gated step**，按本 runbook 手动做 —— owlmlx **不**自动改消费者仓/config。

---

## 0. 前提 + bounds
- B1 **≠** sustained（B2）· **≠** 去 `:8009`（B3）· **≠** replacement-complete。replacement verdict 仍 `not yet replaceable`。
- 只翻 **OwlCoda**（多后端 + 跨后端容灾 → owlmlx-primary + `:8009` 兜底，安全可逆）。**OwlCC repoint 推迟 B3**（single routerUrl 无内建兜底）。

## 1. 翻默认前：flip-readiness 门（owlmlx 侧）
```bash
.venv/bin/python scripts/replacement/r4_phaseb_b1_flip_readiness.py check \
  --base-url http://127.0.0.1:8066 --model-id <model> --owlmlx-commit <sha>
```
- `go`（exit 0）→ 继续；`no_go`（exit 1）→ **停**，artifact 列 blocking 项（OwlCoda-side 契约 gap 或 readiness 失败；OwlCC `/v1/models` gap **不**阻断）。
- **成本**：readiness 的 tool-lane check 会 `POST /v1/chat/completions` → **加载模型**（最小可加载 ~52G）。这一步吃机器 → 跑前 run-now-vs-defer。

## 2. OwlCC preflight 修法（gated · 消费者仓 `owlcc/src/preflight.ts`）
模型可用性探测从 `GET /v1/models`（读 `data[].id`）改为 `GET /v1/openai/models`（读 `data[].id`）—— owlmlx 在那里提供可用性真相（R2 冻结契约）。**仅改可用性 endpoint；`/healthz` 检查不动。** 这是解锁 future OwlCC repoint 的前置（repoint 本身 = B3）。

## 3. OwlCoda 翻默认（gated · 消费者 config，gitignored、环境相关）
- owlmlx-gate 设 owlmlx 为 **primary** backend；`:8009`/其它 backend **保留为 fallback**（OwlCoda 原生跨后端容灾）。
- **绝不删 `:8009` fallback**（删 = B3）。

## 4. 翻后采证 → assemble
operator 抓 `capture.json`：
```json
{"flip_readiness": { "verdict": "go" },
 "post_flip_capture": {
   "request_ids": ["..."],
   "owlmlx_inbound": {"served_request_ids": ["..."]},
   "consumer": {"fallback_count": 0, "outbound_hosts": ["127.0.0.1:8066"]}},
 "reproduction": {"session_id": "...", "owlmlx_commit": "..."}}
```
```bash
.venv/bin/python scripts/replacement/r4_phaseb_b1_flip_readiness.py assemble-flip-state --capture capture.json
```
- `fallback_used_count>0` = owlmlx 仍有缺口的**诚实信号**（喂 R1/诊断），不藏、不粉饰。
- `inbound_coverage_ok=true` = owlmlx 服务了本批全部 request-id。

## 5. 回滚
- revert OwlCoda config（owlmlx-gate 退回原默认）。
- OwlCC preflight 改法是纯增强（读对 endpoint），无需回滚。
- 全程可逆；`:8009` B1 不删，始终在。

## 6. bounds（诚实）
B1 = **flip staged + 初始真流量被 owlmlx 服务 + `:8009` fallback 保留**。**非** sustained（B2）/ **非** 去 `:8009`（B3）/ **非** replacement-complete。promotes nothing；§1a 不动；verdict 仍 not-yet。
