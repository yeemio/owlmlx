# owlmlx Python Environment Unification — Research Prompt

## 你是谁

你是 `owlmlx` 的环境治理研究者。这不是一个能力开发轮（runtime / backend / capability），是一个**专门研究课题**：把项目本机 / dev / CI 的 Python 环境统一到一个**可复现、可机读、可审计**的基线。

研究产物会被主线复用，但研究本身**不动主线代码**，**不改 phase45 active seam**，**不改 native MLX backend adapter**。

## 背景：本机当前现状（实测，2026-05-07）

本机存在的 Python 解释器（多套并存，未统一）：

- `/usr/bin/python3` → 3.9.6（Apple 系统，受系统保护，不能装包）
- `/Library/Developer/CommandLineTools/.../python3.9` → 3.9.6（Xcode CLT）
- `/Applications/Xcode.app/.../python3.9` → 3.9.6（Xcode）
- `/opt/homebrew/bin/python3.10` → 3.10.20（brew `python@3.10`）
- `/opt/homebrew/bin/python3.11` → 3.11.15（brew `python@3.11`）
- `/opt/homebrew/bin/python3.14` → 3.14.3（brew `python@3.14`，**默认 `python3`**）
- `~/.local/share/uv/python/cpython-3.13.12-...` → 3.13.12（uv 自下载）

项目内现状：

- `.venv/` 已存在，pin 在 `python@3.11`（3.11.15）
- `uv.lock` 已存在但 untracked（`requires-python = ">=3.10"`）
- `pyproject.toml` 声明 `requires-python = ">=3.10"`、optional `runtime` extra
  含 `mlx>=0.22.0` + `mlx-lm>=0.22.0`
- 项目同时装了 `uv` (`~/.local/bin/uv`) 和 `poetry` (`/opt/homebrew/bin/poetry`)，
  但实际 lock 用的是 uv
- 默认 shell 命令 `python3 -m pytest` 走的是 brew **3.14**，**不是** .venv 的
  3.11——存在隐式漂移
- `mlx-lm 0.31.3` 是 `py3-none-any` wheel，3.10/3.11 dry-run 装得上，3.14 被
  PEP 668 拦（brew 标记 externally-managed）；`mlx` 的二进制 wheel 是否对所有
  目标 Python 都有可用 ABI **未实测**

## 研究问题

1. **本机层**：项目工作 Python 应该锁在 3.11 还是别的版本？依据是什么（mlx /
   mlx-lm wheel 兼容性、上游模型代码兼容性、社区常见 CI 选择）？
2. **项目层**：是否把 `.python-version` / `uv.lock` 收进 git？怎么收？这两个
   文件是否会和 `pyproject.toml` 的 `requires-python` 产生张力，张力如何
   消除？
3. **dev 体感**：开发者本机 `python3 -m pytest` 应该 fail-loud（强制要求走
   `uv run` / `.venv/bin/python`），还是允许默认 PATH 但有显式 warn？两种
   方案的 trade-off？
4. **CI 层**：CI lane 用什么 Python？多 lane 还是单 lane？是否需要额外一条
   `runtime` extra 装得上的 lane（mlx + mlx-lm）以支持 native MLX backend
   lifecycle smoke 与未来的 batching / KV cache 测试？
5. **下游契约**：`requires-python = ">=3.10"` 是给下游用户的兼容声明，应不应
   改？如果改，是否影响 owlmlx 作为可被外部安装的 runtime 的形象？
6. **工具选择**：项目同时有 uv 和 poetry，是否应明确弃用其中之一？依据是
   什么？是否需要在 `docs/source-of-truth` 里写清"工具选定"以避免后续混乱？
7. **平台扩展面**：未来如果加 Linux x86 / Linux arm64 CI lane（例如外部审计
   要求 cross-platform 复现），3.11 是否仍是合适锚定版本？mlx wheel 是
   Apple Silicon-only，Linux lane 是否只跑 owlmlx 的非 native 部分（subprocess
   backend、cache 调度证据等）？

## 研究**不**做的事（硬规则）

- **不**改任何运行时代码（`owlmlx/runtime/`、`owlmlx/cache_*`、subprocess
  backend、native backend）
- **不**改 phase45 active seam / sentinel chain / capability matrix
- **不**改 `pyproject.toml` 的 `requires-python` 声明，除非研究结论明确建议
  改并给出 trade-off
- **不**删除任何已有 Python（系统 3.9 / brew 3.10 / 3.11 / 3.14 都不动）
- **不**强行卸载 poetry / uv，先研究再决定
- **不**把研究结论直接落地到 main——研究产物是一份**建议文档**，落地由
  主线另开 round 决定

## 研究**要**输出的产物

落到 `docs/source-of-truth/python-environment-research.md`，**只写文档**，不
改代码。包含：

### 1. 当前事实表（factual snapshot）
- 所有解释器位置 + 版本 + 来源 + 是否能装包
- `.venv` 当前 pin、`uv.lock` 解到的所有依赖版本（关键的：mlx、mlx-lm、
  pytest、fastapi 等）
- 默认 shell `python3` 走哪一个，与项目期望差距

### 2. mlx / mlx-lm wheel 兼容性矩阵
- 在 3.10 / 3.11 / 3.12 / 3.13 / 3.14 各跑一次
  `pip install --dry-run --no-deps mlx mlx-lm`，记录是否有可用 wheel、wheel
  名字（`-cp31x-` 还是 `-py3-none-any-`）
- 在能装上的版本里实跑一次 `python -c "import mlx_lm; mlx_lm.load(...)"`
  最小烟，记录是否真能 load 一个最小公开模型（如 `mlx-community/Qwen2.5-0.5B-...`）
- 记录 mlx 上游 GitHub 当前明确支持的 Python 版本（如果 README / setup.py
  声明）

### 3. 推荐统一方案
- 单一推荐 Python（含理由：wheel 可用性、上游测试覆盖、社区 CI 默认、
  3.14 / 3.13 距 EOL 距离）
- 工具链选择（uv vs poetry vs pip+venv）+ 理由
- `.python-version` / `uv.lock` 是否进 git
- dev 命令规范（`uv run pytest` vs `.venv/bin/pytest` vs 全局 alias）
- CI lane 设计（单 lane / 多 lane / runtime extra lane）
- 跟 `requires-python` 声明的关系（开发约束 ≠ 下游兼容声明）

### 4. 迁移路径
- 当前状态 → 推荐方案的最小改动清单
- 每一步是否破坏现有 dirty tree / 现有 staged 主线工作
- 每一步可以 revert 的程度

### 5. 风险与未决
- 还没实测但可能成为 blocker 的事（mlx 在某 Python 版本的 ABI 漂移、
  PEP 668 在 brew 升级后的行为变化、Linux 跨平台 CI 的 mlx 问题）
- 下一轮如果按推荐方案落地，需要哪些独立 round（建议：
  `python-environment-unification-landing` round）

### 6. 不预设结论
- 如果研究发现 3.11 不是最佳选择（例如 mlx 0.31+ 已经只支持 3.12+），
  如实推荐 3.12，不为了"已经在 .venv 里"将就
- 如果研究发现 uv 在某些场景反而成为障碍（例如 CI 环境拉不到 uv），
  如实给出 fallback 路径

## 最小入口

1. `/Users/yeemio/AI/gitrep/owlmlx/pyproject.toml`
2. `/Users/yeemio/AI/gitrep/owlmlx/uv.lock`（untracked，但 inspect 用）
3. `/Users/yeemio/AI/gitrep/owlmlx/.venv/`（inspect bin/python symlink，
   不要写）
4. mlx 与 mlx-lm 上游 GitHub 的 README / setup.py / CI 配置
5. 公开渠道关于 Apple Silicon Python 选择的当前最佳实践

## 第一组命令

```
# 实测每个 Python 能不能装 mlx + mlx-lm
for py in /opt/homebrew/bin/python3.10 /opt/homebrew/bin/python3.11 /opt/homebrew/bin/python3.14; do
  echo "=== $py ==="
  "$py" --version
  "$py" -m pip install --dry-run --no-deps "mlx>=0.22.0" "mlx-lm>=0.22.0" 2>&1 | tail -3
done

# 看 .venv 里到底装了什么
.venv/bin/python -c "import sys; print(sys.executable, sys.version)"

# uv 当前管理的 Python 列表
uv python list --only-installed

# uv.lock 头部解析的 markers
head -10 uv.lock
```

## 交付格式

请按下面顺序输出：

1. 一句最终结论：建议锁定哪个 Python 版本作为项目主线
2. mlx / mlx-lm wheel 兼容性矩阵（实测，不靠回忆）
3. 推荐工具链（uv / poetry / pip）+ 理由
4. `.python-version` / `uv.lock` 是否进 git 的建议
5. CI lane 推荐设计
6. 与 `pyproject.toml` `requires-python` 的关系处理
7. 迁移路径（按 round 拆，每 round 可独立 revert）
8. 风险与未决事项列表
9. 一份草稿版的 `docs/source-of-truth/python-environment-research.md`
   （research-grade，不是 final main-line doc）

## 守则提醒

- 这是研究 round，不是落地 round
- 不动主线代码、不动主线文档、不动 phase45 / native backend / capability
  matrix
- 产物只是研究文档；落地由主线另开 round 决定
- 实测 > 回忆——所有兼容性结论必须有命令证据
- 如果实测发现项目当前 .venv 选择（3.11）就是最优，**如实给出，不强行
  推荐换**
- 不预设结论，不提前给主线工作（lifecycle smoke、KV cache、batching）
  让路或挡路
