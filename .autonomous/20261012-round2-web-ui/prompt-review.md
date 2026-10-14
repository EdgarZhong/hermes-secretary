# Prompt 调优：独立审阅提案

**本文件为用户已审定的完整前后对照；正在应用并做定向检查。** 按语义清晰、保留已有语义的标准写，不设长度不得增加的硬约束。

| 你的原话 | 提案落点 |
|---|---|
| “要让提醒/日程真的建起来，就把它写进 memo”（DS 指出的缺口） | Main 主动唤醒、Memo 段、Memo 工具描述明确登记路径 |
| “它只是主 agent 留给 noting task 的指示”；“你能不能做最小修改？” | 统一表达后台整理指示通道，不改变 Memo 身份、来源或消费 |
| “二加 n 的结构”；“除了 secretary task 之外，还有什么类似的东西” | 正文尾部两句健康原则＋各类明确完成态规则；不实施硬门禁 |
| “只改排期……由代码处理自动的调整状态” | 明确有效改期由代码重新激活，不要求模型另改 status |
| “调整的应该是提示消息头部，对于忠实记录的强调。不用额外强调时间” | 只加强原头部第一句；不加过去时间判断句或任务时间戳 |
| “最新一个timestamp……这条消息产生时的真实当前时间” | Main 一句通用时间规则；Reminder 正文另列原定触发时间 |
| “精确到秒以后的东西……通通删掉” | 新生成的模型可见时间去掉小数秒、保留时区 |

## 主动唤醒：明确使用 Memo

改动前：

> When later action is needed, you wake yourself up with a Reminder at a time you choose yourself.

中文直译：当需要之后采取行动时，你在自己选定的时间通过 Reminder 唤醒自己。

改动后：

> When later action is needed, use `noting_memo` to instruct background Noting to register a Reminder that will wake you up at a time you choose.

中文直译：当需要之后采取行动时，使用 noting_memo 指示后台 Noting 注册一个 Reminder，在你选定的时间唤醒你。

## Main 的 Memo 段：统一后台整理指示通道

改动前：

> **Noting Memo and routing.** `noting_memo` exists so you can still tell background Noting what the next consolidation must cover: one tool with add/replace/delete/list; write a brief one-sentence memo when the user asks you to keep something for later consolidation or you spot something the next pass must not miss; the current memo is carried into the next Noting Task as context. While any memo is non-empty, background Noting stays on for this Conversation. Semantic routing: in-Conversation reminders and schedules are owned entirely by the Notebook — never satisfy them through Hermes Cron; keep cron for explicitly requested Hermes-wide scheduled management or standalone recurring agent dispatches.

中文直译：Noting Memo 与路由。noting_memo 让你仍然可以告诉后台 Noting 下一次整理必须覆盖什么：一个工具，具有 add／replace／delete／list；当用户让你保留某事以便之后整理，或你发现下次处理不能遗漏的事时，写一条简短的一句话 Memo；当前 Memo 作为上下文带入下一次 Noting Task。只要任何 Memo 非空，本会话的后台 Noting 就保持开启。语义路由：会话内提醒和日程完全属于 Notebook——绝不能用 Hermes Cron 来满足它们；Cron 仅用于用户明确要求的 Hermes 全局排期管理或独立的周期性 Agent 派遣。

改动后：

> **Noting Memo and routing.** `noting_memo` is your channel for telling background Noting what the Notebook must contain: one tool with add/replace/delete/list. Whenever you believe a matter must be included in the Notebook at the next background consolidation, write a brief memo; background Noting will ensure that matter is included. For reminders or schedules, include the intended action and requested time; background Noting handles registration. The current memo is carried into the next Noting Task as context. While any memo is non-empty, background Noting stays on for this Conversation. Semantic routing: in-Conversation reminders and schedules are owned entirely by the Notebook — never satisfy them through Hermes Cron; keep cron for explicitly requested Hermes-wide scheduled management or standalone recurring agent dispatches.

中文直译：Noting Memo 与路由。noting_memo 是你告诉后台 Noting，Notebook 必须包含什么的通道：一个工具，具有 add／replace／delete／list。任何时候，当你认为某件事必须在下一次后台整理时纳入 Notebook，就写一条简短便签；后台 Noting 会确保所指事项被纳入。对于提醒或日程，写明要做的事和请求的时间；后台 Noting 负责注册。当前 Memo 作为上下文带入下一次 Noting Task。只要任何 Memo 非空，本会话的后台 Noting 就保持开启。语义路由：会话内提醒和日程完全属于 Notebook——绝不能用 Hermes Cron 来满足它们；Cron 仅用于用户明确要求的 Hermes 全局排期管理或独立的周期性 Agent 派遣。

## noting_memo 工具描述

改动前：

> Maintain this Conversation's Noting Memo with add, replace, delete, or list. Write a brief one-sentence memo for what the next background consolidation must cover; a non-empty memo keeps local Noting on and does not trigger a run.

中文直译：使用 add、replace、delete 或 list 维护本会话的 Noting Memo。为下一次后台整理必须覆盖的内容写一条简短的一句话 Memo；非空 Memo 保持本地 Noting 开启，不触发运行。

改动后：

> Maintain this Conversation's Noting Memo with add, replace, delete, or list. Write a brief memo whenever a matter must be included in the Notebook at the next background Noting Task; background Noting ensures its inclusion. For reminders or schedules, include the intended action and requested time for background Noting to register. A non-empty memo keeps local Noting on; it does not trigger a run.

中文直译：使用 add、replace、delete 或 list 维护本会话的 Noting Memo。任何时候，当某件事必须在下一次后台 Noting Task 中纳入 Notebook，就写一条简短便签；后台 Noting 会确保其被纳入。对于提醒或日程，写明要做的事和请求的时间，交由后台 Noting 注册。非空 Memo 保持本地 Noting 开启；它不触发运行。

## Main 的时间标记说明

拟加入位置：`agent/system_prompt.py` 的 `SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE`，紧接现有 Notebook／Schedule 总述段（末句为 `...delivered reminders.`）之后、`**Noting Memo and routing.**` 段之前，作为独立的一句话。用户已审定，可应用。开发阶段通过原生同步更新已有会话 Prompt；缓存失效并重建属于本次调优的正常结果。

改动前：

原文无此段。

中文直译：目前 Main guidance 中没有这段明确说明。

改动后：

> Time system: only the latest `<timestamp>` marks the real current time when its message arrives; other time fields carry their respective scheduling semantics and do not represent the current time.

中文直译：时间系统：只有最新的 timestamp 标记表示那条消息抵达时的当前真实时间；其他时间字段各自承载其调度语义，不代表当前真实时间。

## Noting Task：头部忠实性与尾部健康维护

位置说明：现行维护段在工具说明后、Notebook Schedules／完整历史与工具权威说明之前，**不是固定指令正文尾部**。提案仅加强头部第一句；保留中间起始状态／核对／终止控制句；将健康维护整理为“2＋N”，移到 `DEFAULT_NOTING_TASK_INSTRUCTION` 正文末尾（`the list and complete schemas below are authoritative.` 之后）。动态工具／Notebook／Memo 的现有追加机制不改。没有新任务时间戳或额外时间判断句。

**头部完整首段，修改前：**
> Maintain the Notebook from the frozen Conversation. The Parent Assistant never maintains the Notebook itself: anything it flags as must-not-miss reaches you as a Noting Memo appended to this instruction — when a memo is present, every memo item must be covered by the resulting Notebook: treat each memo as a requirement to consolidate, not text to paste, and ground its entries in the conversation evidence exactly like anything else you write.
中文直译：根据冻结的 Conversation 维护 Notebook。Parent Assistant 从不亲自维护 Notebook：它标记为不能遗漏的内容，会作为 Noting Memo 追加到本指令中传给你——存在 Memo 时，每条便签所指事项都必须由最终 Notebook 覆盖：将每条 Memo 当作需要整合的要求，而不是直接粘贴的文本；为其形成的 Notebook 条目亦与任何其他写入一样，以对话证据为依据。

**头部完整首段，修改后：**
> Maintain the Notebook faithfully from the frozen Parent Conversation, preserving the original meaning and intent. The Parent Assistant never maintains the Notebook itself: anything it flags as must-not-miss reaches you as a Noting Memo appended to this instruction — when a memo is present, every memo item must be covered by the resulting Notebook: treat each memo as a requirement to consolidate, not text to paste, and ground its entries in the conversation evidence exactly like anything else you write.
中文直译：根据冻结的 Parent Conversation 忠实维护 Notebook，保留原本含义和意图。Parent Assistant 从不亲自维护 Notebook：它标记为不能遗漏的内容，会作为 Noting Memo 追加到本指令中传给你——存在 Memo 时，每条便签所指事项都必须由最终 Notebook 覆盖：将每条 Memo 当作需要整合的要求，而不是直接粘贴的文本；为其形成的 Notebook 条目亦与任何其他写入一样，以对话证据为依据。

**健康维护段：完整修改前／修改后**

整段替换并移到固定指令正文尾部；`Historical /notebook...` 及其重复条目告诫在修改后删除。下方修改前为现行原文，不代表保留这句。起始状态／核对／终止工具的控制句没有改动，不重复列出。

**修改前（完整健康维护内容）：**
> Keep all four sections current. Mark confirmed secretary_task completion done; next task, reschedule or archive tasks done at task start. Keep newly done until then. Historical /notebook is derived state, not fresh evidence; duplicate entries only for a new intent verified in independent original user evidence. Keep Persistence Candidates aligned with Parent: create/revise as needed; archive after confirmed persistence execution or user rejection/withdrawal; a proposal or approval alone is not completion.
中文直译：保持全部四个分区与当前情况一致。将已确认完成的 secretary_task 标为 done；下一任务，对任务开始时已 done 的 task 重新排期或归档。新变为 done 的留到那时。历史 /notebook 是派生状态，不是新鲜证据；仅在独立原始用户证据验证了新意图时才复制条目。让 Persistence Candidates 与 Parent 一致：按需创建／修订；在持久化执行被确认完成，或用户拒绝／撤回后归档；仅有提案或批准不等于完成。

**修改后（完整替换内容，整体移到正文尾部）：**
```text
Keep every Notebook entry aligned with the Parent Conversation's actual progress, and promptly mark completion when it is confirmed. Process entries already completed at the start of the Noting Task: reactivate them through an existing supported operation if follow-up is needed, or archive them; do not leave completed entries accumulating in the Notebook.
- secretary_task.done and user_commitment.done: keep entries newly marked done until the next Noting Task; for entries already done at the start, update the Schedule to reactivate them or archive them. Schedule updates restore the active status automatically.
- user_reminder.delivered: this means the reminder intention is complete, not merely that one recurring occurrence was delivered; register a new Schedule to reactivate it or archive it.
- watchpoint.resolved: register a new valid until/Schedule if further observation is needed, or archive it. Reaching until alone does not establish resolution.
- open_question.resolved: archive the resolved question. Create another question only for a new unresolved matter established by the Parent Conversation; do not invent a status rollback.
- Persistence Candidates: keep them aligned with Parent developments; create or revise as needed, and archive after confirmed persistence execution or user rejection/withdrawal. A proposal or approval alone is not completion.
```
中文直译：
让每个 Notebook 条目与 Parent Conversation 的实际进展一致，确认完成时及时标记完成。处理 Noting Task 起始时已完成的条目：若仍需跟进，通过现有支持的操作重新激活，否则归档；不要让完成条目在 Notebook 中积压。
- secretary_task.done 和 user_commitment.done：本轮新标为 done 的条目保留到下一次 Noting Task；起始时已 done 的条目，通过更新 Schedule 重新激活或归档。排期更新会自动恢复活动状态。
- user_reminder.delivered：这表示整个提醒意图已完成，不只是周期中的一次提醒已送达；登记新 Schedule 重新激活，或归档。
- watchpoint.resolved：若需继续观察，登记新的有效 until／Schedule，否则归档。仅到达 until 并不确立问题已解决。
- open_question.resolved：归档已解决的问题。只有 Parent Conversation 确立了新的未解决事项时才另建问题；不要虚构状态回退。
- Persistence Candidates：保持与 Parent 的发展一致；按需创建或修订，在持久化执行被确认完成，或用户拒绝／撤回后归档。仅有提案或批准不等于完成。

类型核对：其他明确完成态包括 user_commitment.done、user_reminder.delivered、watchpoint.resolved、open_question.resolved；Persistence Candidates 没有 status 图，沿用执行完成／拒绝／撤回的已有清理依据。decision.active 和 formulating_insight.validated 是仍有效的决定／见解，不因状态图没有后继就冒充“待清理的完成工作”；failed、dropped、cancelled、superseded 等不能冒充成功完成。此稿不改状态图，不新增重新激活手段，不实施硬门禁。

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
