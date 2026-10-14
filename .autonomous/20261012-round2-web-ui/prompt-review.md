# Prompt 调优：独立审阅提案

**本文件只含本次待审内容，未实施。** 按语义清晰、保留已有语义的标准写，不设长度不得增加的硬约束。

| 你的原话 | 提案落点 |
|---|---|
| “要让提醒/日程真的建起来，就把它写进 memo”（DS 指出的缺口） | Main 主动唤醒、Memo 段、Memo 工具描述明确登记路径 |
| “它只是主 agent 留给 noting task 的指示”；“你能不能做最小修改？” | 原 Memo 段只插入桥接句，不改变 Memo 身份、来源或消费 |
| “先把清理门禁作为软提示放到这一部分” | 只在整体维护段写两轮完成处理；不实施硬门禁 |
| “只改排期……由代码处理自动的调整状态” | 明确有效改期由代码重新激活，不要求模型另改 status |
| “忠实的为主会话记录 noting……尽量不引入额外的自我判断” | 过去的一次性时间也忠实登记，不自行舍弃或改期 |
| “最新一个timestamp……这条消息产生时的真实当前时间” | Main 明确真实时间；Reminder 正文另列原定触发时间 |
| “精确到秒以后的东西……通通删掉” | 新生成的模型可见时间去掉小数秒、保留时区 |

## 主动唤醒：明确使用 Memo

改动前：

> When later action is needed, you wake yourself up with a Reminder at a time you choose yourself.

中文直译：当需要之后采取行动时，你在自己选定的时间通过 Reminder 唤醒自己。

改动后：

> When later action is needed, you wake yourself up with a Reminder at a time you choose yourself. Arrange this Reminder through `noting_memo`.

中文直译：当需要之后采取行动时，你在自己选定的时间通过 Reminder 唤醒自己。通过 noting_memo 安排这个 Reminder。

## Main 的 Memo 段：只补提醒登记路径

改动前：

> **Noting Memo and routing.** `noting_memo` exists so you can still tell background Noting what the next consolidation must cover: one tool with add/replace/delete/list; write a brief one-sentence memo when the user asks you to keep something for later consolidation or you spot something the next pass must not miss; the current memo is carried into the next Noting Task as context. While any memo is non-empty, background Noting stays on for this Conversation. Semantic routing: in-Conversation reminders and schedules are owned entirely by the Notebook — never satisfy them through Hermes Cron; keep cron for explicitly requested Hermes-wide scheduled management or standalone recurring agent dispatches.

中文直译：Noting Memo 与路由。noting_memo 让你仍然可以告诉后台 Noting 下一次整理必须覆盖什么：一个工具，具有 add／replace／delete／list；当用户让你保留某事以便之后整理，或你发现下次处理不能遗漏的事时，写一条简短的一句话 Memo；当前 Memo 作为上下文带入下一次 Noting Task。只要任何 Memo 非空，本会话的后台 Noting 就保持开启。语义路由：会话内提醒和日程完全属于 Notebook——绝不能用 Hermes Cron 来满足它们；Cron 仅用于用户明确要求的 Hermes 全局排期管理或独立的周期性 Agent 派遣。

改动后：

> **Noting Memo and routing.** `noting_memo` exists so you can still tell background Noting what the next consolidation must cover: one tool with add/replace/delete/list; write a brief one-sentence memo when the user asks you to keep something for later consolidation or you spot something the next pass must not miss; the current memo is carried into the next Noting Task as context. For an in-Conversation reminder or schedule, write the intended action and requested time in a brief memo; background Noting registers it in the Notebook. While any memo is non-empty, background Noting stays on for this Conversation. Semantic routing: in-Conversation reminders and schedules are owned entirely by the Notebook — never satisfy them through Hermes Cron; keep cron for explicitly requested Hermes-wide scheduled management or standalone recurring agent dispatches.

中文直译：Noting Memo 与路由。noting_memo 让你仍然可以告诉后台 Noting 下一次整理必须覆盖什么：一个工具，具有 add／replace／delete／list；当用户让你保留某事以便之后整理，或你发现下次处理不能遗漏的事时，写一条简短的一句话 Memo；当前 Memo 作为上下文带入下一次 Noting Task。对于会话内提醒或日程，在一条简短 Memo 中写明要做的事和请求的时间；后台 Noting 将其登记到 Notebook。只要任何 Memo 非空，本会话的后台 Noting 就保持开启。语义路由：会话内提醒和日程完全属于 Notebook——绝不能用 Hermes Cron 来满足它们；Cron 仅用于用户明确要求的 Hermes 全局排期管理或独立的周期性 Agent 派遣。

## noting_memo 工具描述

改动前：

> Maintain this Conversation's Noting Memo with add, replace, delete, or list. Write a brief one-sentence memo for what the next background consolidation must cover; a non-empty memo keeps local Noting on and does not trigger a run.

中文直译：使用 add、replace、delete 或 list 维护本会话的 Noting Memo。为下一次后台整理必须覆盖的内容写一条简短的一句话 Memo；非空 Memo 保持本地 Noting 开启，不触发运行。

改动后：

> Maintain this Conversation's Noting Memo with add, replace, delete, or list. For a reminder or schedule, write its action and requested time in one brief sentence for background Noting to register in the Notebook. Also note other matters the next consolidation must cover. A non-empty memo keeps local Noting on; it does not trigger a run.

中文直译：使用 add、replace、delete 或 list 维护本会话的 Noting Memo。对于提醒或日程，用一句简短的话写明要做的事和请求的时间，让后台 Noting 登记到 Notebook。也记下下一次整理必须覆盖的其他事项。非空 Memo 保持本地 Noting 开启；它不触发运行。

## Main 的时间标记说明

改动前：

原文无此段。

中文直译：目前 Main guidance 中没有这段明确说明。

改动后：

> The latest `<timestamp>` marks when that message was actually created, not when its reminder was scheduled to fire. An Instant Reminder states its scheduled time separately in the message body.

中文直译：最新的 timestamp 标记表示那条消息实际产生的时间，不是其中提醒计划触发的时间。Instant Reminder 在消息正文中另外写明其计划触发时间。

## Noting Task：维护软提示和忠实登记

修改前（当前完整维护段）：

```text
Use the appended Notebook; verify complete state with notebook_show after changes. End via terminal tool, not text alone. Keep all four sections current. Mark confirmed secretary_task completion done; next task, reschedule or archive tasks done at task start. Keep newly done until then. Historical /notebook is derived state, not fresh evidence; duplicate entries only for a new intent verified in independent original user evidence. Keep Persistence Candidates aligned with Parent: create/revise as needed; archive after confirmed persistence execution or user rejection/withdrawal; a proposal or approval alone is not completion.
```
中文直译：使用追加的 Notebook；修改后用 notebook_show 核对完整状态。通过终止工具结束，而不是仅有文本。保持全部四个分区与当前情况一致。将已确认完成的 secretary_task 标为 done；下一任务，对任务开始时已 done 的 task 重新排期或归档。新变为 done 的留到那时。历史 /notebook 是派生状态，不是新鲜证据；仅在独立原始用户证据验证了新意图时才复制条目。让 Persistence Candidates 与 Parent 一致：按需创建／修订；在持久化执行被确认完成，或用户拒绝／撤回后归档；仅有提案或批准不等于完成。

修改后（同一范围）：

```text
Treat the appended Notebook as the starting state; after changes, use notebook_show to verify the complete state. End through the terminal tool, not a text-only answer. Keep all four sections aligned with the Parent Conversation and clear completed items as described below. When secretary_task work is confirmed complete during this pass, mark it done and retain it until the next pass. For tasks already done in the starting Notebook, use this pass's conversation evidence to decide whether to register the next schedule or archive them. A valid schedule update reactivates the task automatically; do not separately reset its status. A historical /notebook rendering is already-existing derived Notebook state, not fresh user evidence: never duplicate its entries into new entries unless independent original user evidence establishes a new intent. Keep Persistence Candidates aligned with developments in the Parent Conversation: create or revise them as needed, and archive candidates once their persistence actions are confirmed completed, or the user has rejected or withdrawn them; a proposal or approval alone is not completion.
```
中文直译：将追加的 Notebook 视为起始状态；修改后使用 notebook_show 核对完整状态。通过终止工具结束，而不是仅有文本的回答。保持全部四个分区与 Parent Conversation 一致，并按下文清理已完成条目。若 secretary_task 的工作在本轮被确认完成，将其标为 done，并保留到下一轮。对于起始 Notebook 中已经 done 的任务，根据本轮对话证据决定登记下一次排期，还是归档。有效的排期更新会自动重新激活任务；不要另外重置其状态。历史 /notebook 呈现是已有派生 Notebook 状态，不是新鲜用户证据：除非独立原始用户证据确立新的意图，绝不要将其中条目复制成新条目。让 Persistence Candidates 与 Parent Conversation 的发展一致：按需创建或修订；在其持久化行动被确认完成，或用户已拒绝或撤回后归档；仅有提案或批准不等于完成。

对 Notebook Schedule 增补一句：

修改前：无此明确句子。

中文直译：当前任务指令没有明确说明过去的一次性时间仍须忠实登记。

修改后：

> Faithfully record the requested action and schedule, including a one-shot time already in the past; do not omit or move it merely because that time has passed.

中文直译：忠实记录所请求的行动和排期，包括已经过去的一次性时间；不要仅仅因为该时间已经过去而省略它或移动它。

## Instant Reminder：真实时间与原定时间分开

修改前（格式示例）：

```xml
<instant-reminder>
<timestamp>2026-10-14T09:36:00.123456+08:00</timestamp>
提醒：说你好
</instant-reminder>
```
中文直译：Instant Reminder；消息真实产生时间为 09:36:00（含小数秒）；提醒：说你好。

修改后（同一提醒的格式示例）：

```xml
<instant-reminder>
<timestamp>2026-10-14T09:36:00+08:00</timestamp>
Scheduled for: 2026-10-14T09:35:00+08:00
提醒：说你好
</instant-reminder>
```
中文直译：Instant Reminder；消息真实产生时间为 09:36:00；原定触发时间为 09:35:00；提醒：说你好。

## 秒精度与保留边界

时间格式提案：`2026-10-14T09:36:00.123456+08:00` → `2026-10-14T09:36:00+08:00`。内部计时和精确查询边界不降低精度；历史原文、当前 root 与冻结父快照不回写。现有系统提示的会话开始日期本身没有小数秒，不额外加入动态时钟。

保留现有四区十类、Main 只读、Persistence 批准边界、Memo 首段与 Snapshot 消费、完整历史审阅、原生工具权限和终止机制。此前已实施的 secretary_task 必填 Schedule／明确模式／取消直接 archive 及工具描述保持现状。本次不新增工具、硬清理门禁、Noting 时间窗口判断；过期 Instant 继续由现有约五秒扫描补投，不加立即触发旁路。
