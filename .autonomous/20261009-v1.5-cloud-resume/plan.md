# V1.5 Cloud Resume Implementation Plan

## 目标与边界

从 70c772 基线直接实现已定稿的 M26–M28 及 C11 全生命周期纠偏，不扩大到新 Provider、独立模型路由、个人 UI、云部署或其它 V1 机制重构。

## 批次

### P1 — D01 实际执行来源
- 在 native/ACP generic 实际调用内层记录 `native|external`，仅合格 Main 生效。
- Codex App Server 在真实 `_codex_session.run_turn` 前记录 external；若随后 fallback 到 generic native，后者覆盖为 native。
- Main Turn 完成时用现有 `patch_session_model_config` 合并 `_secretary_last_main_execution`；无真实请求不覆盖。
- Force Trigger 过阈值后、freeze/admission 前读取内存值；Idle 触发成立后、freeze/admission 前读取持久值；只 external 拒绝。

### P2 — Noting 五 Turn、工具后缀与终止
- 删除首响应后修改 `child.tools` 的旧偏差，记录每次实际 request tools parity。
- 为 task 与每次 continuation 追加 Profile 对应合法工具列表及完整 Schema 文本，不改 frozen Parent 顶层 schemas。
- 普通 Profile 增加 `finish_noting(reason)` inline tool；特殊 Profile 仅 `compact_parent()`。
- 两个 Profile 均最多 5 个完整 Turn；文本完成不算终止。超限设 forced；特殊 Profile 由框架直接调用既有 native parent compaction，然后不增加第六 Turn。
- 无 Notebook mutation 时也从现有 NotebookStore 读取当前完整状态，保证 forced/正常 no-op 可走原 Commit Gate。

### P3 — Snapshot termination 审计
- `secretary_notebook_snapshots` 增 `termination_json`，init 时兼容迁移；不修改 Hermes 原生表。
- commit API 接受内部 termination；branch 复制；新增 audit-only reader。
- `notebook_current`、`notebook_show`、Slash 普通投影保持原 shape，不泄露 termination/reason。
- Noting commit 必须带当前结束类型。

### P4 — 测试与交接
- 补 D01、五 Turn/工具 parity/forced、termination migration/visibility/branch 测试。
- 云端由于无仓库工作树执行环境，至少做逐文件语法/接口静态核对和 Git diff review；任何无法真实执行的 pytest/DeepSeek/Dashboard 明确留为本地门禁。
- 更新本轮 verification/validation/final-delivery 与根 CLAUDE，使本地 Coding Agent 可直接从待办门禁接续。
