# V1.5 Cloud Resume Implementation Plan

## 目标与边界

从 70c772 基线直接实现已定稿的 M26–M28 及 C11 全生命周期纠偏，不扩大到新 Provider、独立模型路由、个人 UI、云部署或其它 V1 机制重构。

## 批次

### P1 — D01 实际执行来源 — 云端代码已实施
- 在 native/ACP generic 实际调用内层记录 `native|external`，仅合格 Main 生效。
- Codex App Server 在真实 `_codex_session.run_turn` 前记录 external；若随后 fallback 到 generic native，后者覆盖为 native。
- Main Turn 完成时用现有 `patch_session_model_config` 合并 `_secretary_last_main_execution`；无真实请求不覆盖。
- Force Trigger 过阈值后、freeze/admission 前读取内存值；Idle 触发成立后、freeze/admission 前读取持久值；只 external 拒绝。

### P2 — Noting 五 Turn、工具后缀与终止 — 云端代码已实施
- 删除首响应后修改 `child.tools` 的旧偏差，记录每次实际 request tools parity。
- 为 task 与每次 continuation 追加 Profile 对应合法工具列表及完整 Schema 文本，不改 frozen Parent 顶层 schemas。
- 普通 Profile 增加 `finish_noting(reason)` inline tool；特殊 Profile 仅 `compact_parent()`。
- 两个 Profile 均最多 5 个完整 Turn；文本完成不算终止。超限设 forced；特殊 Profile 由框架直接调用既有 native parent compaction，然后不增加第六 Turn。
- 无 Notebook mutation 时也从现有 NotebookStore 读取当前完整状态，保证 forced/正常 no-op 可走原 Commit Gate。

### P3 — Snapshot termination 审计 — 云端代码已实施
- `secretary_notebook_snapshots` 增 `termination_json`，init 时兼容迁移；不修改 Hermes 原生表。
- commit API 接受内部 termination；branch 复制；新增 audit-only reader。
- `notebook_current`、`notebook_show`、Slash 普通投影保持原 shape，不泄露 termination/reason。
- Noting commit 必须带当前结束类型。

### P4 — 测试与交接 — 云端静态收口完成，运行门禁待本地
- 补 D01、五 Turn/工具 parity/forced、termination migration/visibility/branch 测试。
- 云端由于无仓库工作树执行环境，至少做逐文件语法/接口静态核对和 Git diff review；任何无法真实执行的 pytest/DeepSeek/Dashboard 明确留为本地门禁。
- 更新本轮 verification/validation/final-delivery 与根 CLAUDE，使本地 Coding Agent 可直接从待办门禁接续。


## 实施落点与静态复核

- P1：`agent/turn_api_call.py` 与 `agent/codex_runtime.py` 只在真实派发前记录执行来源；`secretary/noting_runtime.py` 负责内存/现有 session model_config 同一事实、Force/Idle 门禁。后续修补保证 External Idle 不先进入 parent-compaction 分支，同 Turn rotation 不丢 D01 事实。
- P2：`secretary/noting_tools.py` 不再在首响应后扩顶层 `child.tools`；完整可用工具 Schema 进入 Noting 后缀控制消息。普通/特殊 Profile 分别以 finish_noting(reason)/compact_parent() 正常结束；同一 Child 五 Turn 上限，超限 forced。Continuation 继续使用 `<noting-task>` synthetic carrier 且保持 admission source timestamp。
- P3：`secretary_notebook_snapshots.termination_json` 为 Secretary-owned 可迁移审计列；普通投影不含 termination；audit reader 单独暴露；branch 复制；老 Snapshot 为 null。
- 静态 review 另关闭两个明确契约缺口：finish_noting 拒绝额外参数，compact_parent 拒绝任何参数；均有定向测试断言。
- GitHub 连接器环境没有可执行工作树，因此本轮没有运行 tests/check。代码层结论仅为“实现已写入并完成静态接收”，不能替代 H6/H7。

## 本地执行顺序（拉取最新 main 后直接继续）

1. 先运行最小受影响集：
   `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/secretary/test_noting_runtime.py tests/secretary/test_noting_child.py tests/hermes_state/test_secretary_notebook.py`。
2. 按实际改动补跑相关 agent/cache-parity/turn 生命周期测试，并运行冻结的 ruff/health 等相关检查；不要通过改规则、阈值或豁免让结果变绿。
3. 更新本轮 `verification.md`，执行 H6 独立 Verification；只有通过后进入真实模型/用户验收。
4. 使用既定 DeepSeek 官方 Anthropic / deepseek-flash 原生 Hermes 路径，取得真实 prefix/cache-read 证据，再执行官方 Dashboard H7 Validation。
5. H6/H7 均通过后更新 `final-delivery.md`、`CLAUDE.md`、README，才标记整体完成。


## 2026-10-09 本地接续

依据 R06 沿用本轮基线和计划。当前产品 c4b45bdf9b，首批三文件定向55项通过（17.4秒），日志见根 CLAUDE。主会话接收云端变更并取得接线证据；native_evidence 只读产品准备 Native DeepSeek 脚本与隔离运行条件。相关 Agent/cache 定向回归后安排一次影响范围内扩大回归和10类检查，独立 Verification 重新提取全范围要求；真实 Native请求/缓存证据与官方 Dashboard Validation 分别记录，不用历史 Codex结果代替。
