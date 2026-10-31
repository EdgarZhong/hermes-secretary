# 问题报告：Idle Noting 压缩中断导致 Framework 消息与任务状态悬空

- 日期：2026-10-28（Asia/Shanghai）
- 影响会话：Alex 置顶 `20261021_200341_2ce088` / `conv_a497994968694fe180ad6e4523afe9f2`
- 性质：状态机缺口。Notebook 快照已提交、无数据丢失；Framework 消息未注入；Noting 任务行未收尾
- 本次触发：00:06:41 人为重启 Web 服务打断压缩。进程崩溃、压缩失败等同类中断会落到同一状态

## 时间线

| 时间 | 事件 |
|---|---|
| 10-27 23:56:54 | Idle Noting 触发并准入：admission 15，子会话 `noting_a4b9dd8efa244234`，anchor `5129e4f2…`，interval `compaction:20261021_200341_2ce088:12392` |
| 10-28 00:01:44.929 | 子会话 `finish_noting` 成功，Turn 以 `noting_finished` 结束 |
| 00:01:45.114 | 快照 `snap_bfa709db4926481a8de389213f09c35a` 落库（trigger=idle，termination=`finish_noting`） |
| 00:01:45.504 | 父会话上下文压缩启动：63 条消息、约 123,427 tokens、k3.1-pro，摘要请求已发出 |
| 00:06:41 | Web 服务重启（PID 652199 → 828565），压缩线程随进程消失；无 `context compression done`、无该次 attempt telemetry，active 消息仍为 63 条 |
| 00:07:29 | 用户新 Turn 开始，日志 `Pruned 1 stale active session lease(s)`；压缩租约被当作 stale 清理，Turn 于 00:09:15 正常结束 |
| 00:07:40 前 | 父会话 00:00–00:07:40 区间只有 1 条消息（用户 00:07:29 那条），**没有 Framework 消息** |
| 00:10:54 | 子任务 presence 租约到期 |
| 00:22:32 | `secretary_noting_children` admission 15 仍为 `running`、`finished_at=NULL` |

## 关键事实

1. 快照先提交、压缩后启动，顺序符合设计（`idle_compaction_after_commit`：压缩完成前不投递 Framework）。
2. 压缩未提交：`archive_and_compact` 在事务内校验压缩租约，进程死亡后无提交、无部分归档。
3. Framework 未注入：`framework_messages` 侧没有任何该 interval 的投递记录，父会话消息流也没有对应消息。
4. 任务行悬空：`noting_child_finish` 只在子任务线程退出路径上 best-effort 写入；线程被杀后没有任何终态写入。
5. 读模型表现：`web_read._tasks` 取 `running_tasks()` 得到该行，但 `task_is_live()` 因租约过期返回 false，于是前端状态落到 `unknown`；该行不会被回收，状态不会自愈。

## 缺口

1. **Framework 注入是内联单点**：排在压缩 durable 之后，压缩未完成就没有任何投递路径；"防被压缩吞掉"的约束与"必须投递"之间没有持久待投记录作为缓冲。
2. **没有中止终态**：压缩被中断/被顶掉/失败时，interval 没有 aborted 标记，任务没有 failed/aborted 终态可写。
3. **没有对账**：`status='running'` 的行不与租约存活、进程身份核对，死任务永远显示为未收尾。
4. **读模型只有 unknown 兜底**：`running` 行 + 无活租约 = `unknown`，这是保守降级，但缺少收敛路径后变成永久状态。
5. **任务终态依赖 Framework**：`completed` 写在 Framework 之后，Framework 悬空会连带任务状态悬空。
6. **force 占位与尝试结果不匹配**：`_freeze_and_admit` 先查 `noting_force_occupied_conn`，只按 interval 匹配 `kind='force'` 的 admission，不检查子任务状态或是否成功；interval 只有成功压缩才推进。因此一次 force 尝试即使在提交前被杀（00:28:08 触发，00:31:19 被杀，发生在 00:29:59 放宽到 512000 之前），占位仍长期保留，之后 manual/idle/force 全部被判 `force_interval_occupied` 跳过，直到有一次成功压缩推进 interval 或人工清掉该行。

## 影响

- 用户侧：Noting 已产生并注入，但看不到 Framework 消息；会话的 Noting 状态长期显示 `unknown`。
- 系统侧：该 interval 无压缩提交、无 Framework、无终态；后续没有自动重试或补偿，只能等下一次 Noting 覆盖新 anchor。

## 本轮处置（仅记录事实，不含修复方案）

- 00:23:36 曾误将全局 `noting.enabled` 置为 false（备份 `alex-noting-off-20261027T162335Z`），导致悬浮球入口消失；00:24:50 已恢复 `noting.enabled=true`，并将 `noting.idle.enabled` 置为 false（备份 `alex-noting-idle-only-20261027T162449Z`）。
- 00:28:08 发生 **force** 触发（admission 16，anchor `ee00fd57…`），不经过 idle 开关；00:31:19 重启 Web 与 Gateway，该任务在提交前被杀，无快照（anchor `ee00fd57…` 无对应 snapshot 行）。
- 00:29:59 `model.context_length` 262144 → 512000（供应商元数据 context=1048576）；备份 `alex-ctx500k-20261027T162958Z`，读回 512000。
- 00:31:52 将 admission 15、16 两行由 `running` 直接收敛为 `failed`（`finished_at` 写入同一事务），会话内 `running` 行归零；这是人工对账，不是正式终态写入路径。
- 00:39:54 用户手动 Compact（110 条、约 246,574 tokens），联合 Noting 因 force 占位被判 `force_interval_occupied` 跳过；日志只留 `Noting trigger attempt kind=manual`，无新 admission。
- 00:43:29 重启 Web 取消该次压缩：无 `context compression done`，active 消息仍 110 条，interval 仍 `compaction:…:12392`（未推进）。
- 00:43:39 删除 admission 16 及其 `failed` 子行（该 anchor 无 snapshot），`force_occupied=0`；interval 未动，admission 15（idle）保留。
- 当前配置：`noting.enabled=true`、`noting.idle.enabled=false`、`noting.idle.delay_seconds=500`、`noting.idle.threshold_tokens=98304`、`compression.threshold=0.8`、`compression.idle_compact_after_seconds=0`、`model.context_length=512000`。
- 未改代码；00:06:41 与 00:31:19 两次重启分别用于终止压缩与使上下文配置生效。

## 新记录的要求（未实现，未提方案）

- 用户要求：若中途取消压缩（无论自动 Compact 还是手动 Compact），对应的 Noting 应一并取消，而不是留下已提交/未收尾的任务。

## 复查入口

- `state.db`：`secretary_notebook_snapshots`、`secretary_noting_children`、`secretary_noting_task_leases`、`session_turn_leases`、`secretary_noting_idle_state`、`secretary_noting_compaction_state`
- 日志：`~/.hermes/profiles/alex/logs/agent.log`（00:01:45 启动、无 done；00:07:29 prune 与 Turn 开始）
