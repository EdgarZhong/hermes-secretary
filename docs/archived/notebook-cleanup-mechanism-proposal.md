# Notebook 完成事项清理机制设计提案

> **已归档／2026-10-16：** 本文保留历史研讨，旧方案及“待审”状态不再是当前施工要求。新 Notebook 语义以[已审白板](../notebook-ontology-whiteboard.html)为准，实施契约以[07](../07-scheduler-notebook-noting-compaction-redesign.md)为准；UI现行事实见[06](../06-Hermes-Secretary-Web-UI-V1-Spec.md)。归档不改写原轮次验收结论。

> **历史设计提案／未实施／不改变现行契约。** 2026-10-16 按用户要求移除原 07 编号，保留本文讨论，不升格为规格。当前职责重设计入口为 [新 07](../07-scheduler-notebook-noting-compaction-redesign.md)。旧轮次材料中的“docs/07 清理提案”指本文，不指新 07。
>
> 本文只论述功能、状态与实现候选方案，不授权任何清理硬门禁、工具、Prompt、产品或测试变更。既有 C84 状态与 Schedule 同步修复和本文的新清理机制必须分开。以下“建议”“候选”“若采用”均不是用户已批准的产品规则。

## 1. 目的、问题与范围

Notebook 是 Conversation 的派生工作状态，不是完成工作流水账。一个事项已经确认完成后，可以留一个 Noting Task 的观察窗口；后续维护应明确决定继续跟进还是移出 Notebook，不能靠每次复制旧状态无限积压。这里的“处理”是有真实状态结果的重新排期或归档，不是模型口头说已检查。

最小设计方向是：**已提交 Snapshot 提供跨 Task 事实，同一个 Notebook owner 同步产生完整条目版本及提交计划，唯一正式发布事务保证 Notebook、pointer、Schedule Registry 与既有 Memo 消费一致。** 不将条件复制到 scanner、Reminder ACK、Main 请求、UI 或多个下游工具中。

须先区别两种保证：

- **安全性**：某次成功的正常收尾／发布不能把本次应处理的旧完成事项原样带过去。代码可以凭确定事实保证。
- **最终进展**：未来一定有 Noting Task，且它一定获取足够依据、完成处理。关闭功能、进程崩溃、持续 overflow、无后续 Trigger 都可能阻止进展，本文方案不能宣称无条件保证。软 Prompt 也不能保证。

非目标：不替代原文事实源、Hermes Cron、Main admission 或 Compaction；不引入取消任务工具、清理工具、新调度器、平行 Agent Loop、自动重试工作流、模型纪律台账或数据库迁移；不静默自动归档、伪造下一次时间、迫使未完成工作结束。Main 仍只读 Notebook；Memo 仍只作为给 Noting 的指示，不是 Notebook 条目或 provenance。

## 2. 用户需求逐字对账与权威边界

| 用户原话（逐字保留） | 本文对应处理 |
|---|---|
| 「清理门禁，先不加了」 | 本文未实施，所有候选硬约束待审核 |
| 「这些单独成文档，不实施」 | 独立专项提案；不改工具、Prompt、产品与测试 |
| 「还有没有其他的类似的情况和状态流转？有没有其他类似条目？到达某个状态之后，下一次一定要处理，不允许积压。我们使用清理门禁来保证这一点，这就是清理门禁的作用。以及清理门禁该如何实现？最小节线改造点在哪里？逻辑机制是什么？」 | §4 十类型矩阵，§5 跨 Task 定义，§6–8 最小接线与强制收尾权衡 |
| 「用正向代码机制，保证不变量平凡成立，如条件判断点归同一处，能寻找同步的地方，就尽量同步。而不是在下游无脑追加门禁检查，或者设置散落在各处的判断条件与复杂 if else 逻辑」 | 一个 owner、统一处置判定、不可变提交计划；多入口只转交同一机制 |
| 「逻辑机制结构性的让不变量成立，而不是靠纪律和门禁去逼近。」 | 不依赖模型填写 processed／声明完成；从实际版本、lineage、Snapshot 与 Registry 形成证明 |
| 「禁止扩大工具实现范围，比如单独做一个取消任务的工具。」 | 完全复用 manage/archive、edit/status、schedule/update 与两个既有 terminal 工具；无新工具 |
| 「首先，不是完成态（status）的，应该置为完成，或者是直接注册下一次（schedule）对于已是完成状态的，根据本轮 noting 依据，决定是重新注册 schedule，还是直接归档。」 | 工作事项本轮确认结束或继续排期；下一 Task 初始已完成事项才进入处置候选；不将字面 done 强套所有类型 |
| 「实际上是先经过了一轮，标记为结束，下一轮才可清理。」 | 不将同 Child continuation 算下一轮；本 Task 新完成与 baseline 已完成分开 |
| 「Memo 自己的清理只和快照有关」 | §7/8 保持原 Snapshot 事务消费，不增加逐条模型使用声明或清理义务 |
| 「你还得考虑，如果上下文或者是他人的论述打满了，Notebook Task 强制结束了怎么办？尚未通过的经理门禁，怎么移流到下一轮处理？这个都是问题，清理门禁比想象中复杂，所以我不让不让你在想清楚之前就直接动手」 | §8 专门对照五 Turn、overflow、失败／崩溃与跨 Task 承接，明确不能同时满足的政策选择 |

术语按现行产品校正：上述“经理门禁”按清理门禁理解，“Notebook Task”对应 Noting Task；秘书事项类型是 `secretary_task`，完成状态是 `done`。不创造 `secondary` 类型、通用 completed 状态或新的公开条目状态。

现行需求依据为 [02](../02-noting-system-specification.md) §1.7–1.9、§2.5–2.7、§3.1–3.4/3.7–3.12、§4.3、§5.4–5.5/5.8–5.10/5.12、§6.12–6.13/6.17；[04](../04-hermes-secretary-v1.5-implementation-spec.md) 的 M27／§4.6 等未被后续覆盖增量。派遣时对应行范围分别为 198–257、357–647、650–763、856–1092、1142–1163、1464–1545、1759–1836、1852–2223、2377–2412、2456–2478，已以章节名核对。

根 AGENTS 约束协作与原生兼容；README 提供稳定索引；CLAUDE 记录本次动态授权与最新 Memo 澄清。第二轮 snapshot-index、plan、baseline 只定位轮次输入；`repair-secretary-task-contract.md` §8/9 只作为实现调查／证据入口，不能作为新需求权威，旧稿的 Memo 扩展建议不能覆盖上述最新澄清。本文不改 02 §5.12 Frozen／Target 文本。

## 3. 状态与执行证据不能混为一谈

| 事实 | 能证明什么 | 不能证明什么 |
|---|---|---|
| Notebook `secretary_task.done`／`user_commitment.done` | Noting 已将该工作事项记为语义完成 | 执行程序自动验证了实际工作；旧 Schedule 可再次投递 |
| `failed` | 一次工作失败的语义结论 | 事情已解决、用户已放弃、可以自动删掉 |
| `dropped`／`cancelled`／撤回 | 某项义务或意图结束／取消 | 等同实际执行成功；必须先伪造 done |
| `watchpoint.resolved`／`open_question.resolved` | 观察／问题得到结论 | 结论以后不再有用；watchpoint 到期自然就 resolved |
| `user_reminder.delivered` | 条目被 Noting 记为提醒语义完成 | 任一周期 occurrence 的 ACK 就完成整个提醒计划 |
| Registry `state=done` | 该排期的一次运行／一次性调度已 terminal | 对应任务、承诺或观察的语义工作完成 |
| pending Reminder `delivered`／Provider 成功后的 ACK | 某次提醒已实际携带并取得成功响应 | 被提醒的工作已完成；用户已遵守承诺 |
| `formulating_insight.validated` | 洞见得到确认 | 这个有效知识应被清理 |
| `decision.superseded/revoked`、insight `superseded/rejected` | 原知识被替代、撤销或否定 | 撤销／反证信息已无防止误用的价值 |
| candidate 提案／用户批准 | 可以讨论／获准执行对应持久化行动 | 外部 Memory／Rule／Skill 写入成功 |
| candidate 实际执行完成、明确拒绝／撤回的原文证据 | 现行规范允许 Noting 归档该 candidate | 存在一个可由代码盲判的 candidate.done 状态 |

机器清理范围应由已经提交的确定状态推导。正文语义、实际执行成败、取消、知识价值和 candidate 外部操作的判断仍需 Noting 根据原文完成，不能为了硬约束给每类对象制造不存在的状态。

## 4. 十种条目的候选状态流转与保留矩阵

以下“下个 Task 必处理”均为**待审建议**，目前未实施。建议先以两类明确工作完成态为最窄范围；其余逐类审核，不能把“终态”统一等同“必须归档”。

| 类型 | 现行状态与 Schedule | 下一 Task 必处理候选 | 可用处置结果／应保留原因 |
|---|---|---|---|
| `user_commitment` | `pending→in_progress→done`；活动态可 `dropped`；Schedule 可选 | 建议仅 baseline `done` 纳最窄范围 | 有新跟进依据则现有 schedule_update 同步转 `pending`，或 archive；未完成的用户义务不能强制结束。`dropped` 单列，不冒称履约成功 |
| `user_reminder` | `active→delivered/cancelled`；Schedule 可选；instant | 单次提醒 baseline `delivered` 可候选，须先确认它表示整体提醒结束 | 重新排期同步转 `active` 或 archive；周期 occurrence 送达不是条目 delivered。`cancelled` 走取消处理，不伪造完成 |
| `secretary_task` | `pending→running→done`；活动态可 `failed/dropped`；所有状态 Schedule 非空且 mode 显式 | 建议 baseline `done` 纳最窄范围 | schedule_update 同步转 `pending` 且重新 arm，或 archive。失败可需要重试／分析，dropped 是放弃；两者不自动纳 done 清理。真正取消直接 archive，无新取消工具 |
| `watchpoint` | `watching→resolved/dropped`；`until` 对应单次 Schedule | baseline `resolved` 可候选，需确认观察已经结案 | 新 until／schedule_update 同步转 `watching`，或 archive；到 until 只产生提醒，不能自动判 resolved。仍在观察者保留 |
| `decision` | `active→superseded/revoked`；无 Schedule | 不建议纳第一批强制清理 | active 是当前有效决策，应保留；被替代／撤销信息可能仍防止误用，仅在原文证明已无工作价值时归档。不许要求重新排期 |
| `open_question` | `open→resolved/dropped`；无 Schedule | baseline `resolved` 可列“审查后归档”候选，尚未批准 | resolved 后答案可能需保留或在已有 decision／insight 中维护；不能设 re-schedule 二选一。现行无 resolved→open，若新问题产生按原文新建，不擅改状态图 |
| `formulating_insight` | `forming→validated/rejected/superseded`；无 Schedule | 不建议按 validated 清理；后两态仅审查候选 | validated 是有效知识，应保留；反证、否定和替代缘由可能仍有价值。不能强制另建条目或排期作为逃生条件 |
| `memory_candidate` | 无定义的 status graph；必须合法 provenance；无 Schedule | 保持现行证据驱动归档，不建议纳代码两轮硬约束 | 实际持久化完成、明确拒绝／撤回后归档；提案、批准、修改均不等执行。未执行候选应保留 |
| `rule_candidate` | 同上 | 同上 | 规则实施成功与讨论／批准分离；Noting 无 Rule 外写权限 |
| `skill_candidate` | 同上 | 同上 | Skill 真正创建／修改成功与计划分离；不得虚构 candidate.done 或执行台账 |

`failed/dropped/cancelled` 是否要求在下一 Task 处理，是另一套结束意图政策，不能由 done 清理顺手扩大。重复到期、提醒 ACK、运行超时属于运行层已有职责；不能借“类似条目”纳入整个 Notebook 的 TTL 或清空政策。

对“不在完成态的应标完成或注册下一次”的解释限于本次讨论的工作事项：已证实结束才沿合法图设置对应完成态，仍需跟进才排期。不能将未完成承诺强制 done，或把有效 decision、validated insight、待执行 candidate 强制转换成工作完成态。

## 5. 怎样识别本 Task、下一 Task 与完成观察窗口

### 5.1 固定真实开始基线

建议在 `NotebookStore.load()` 首次创建 task-local 工作状态时，**同一 read context** 获取实际 current Snapshot 身份、包含归档版本的完整 item 引用与实际行。固定只读基线：所属 profile/DB、`conversation_ref`、baseline `snapshot_id`（无 Snapshot 则 null）、每条 baseline lineage 的确切版本／type／status／archived／Schedule。集合只从有真实 Snapshot 引用的 immutable item 推导；孤立 draft row 不算已发生的一轮。

稳定事项键为内部 `(conversation_ref, lineage_id)`。`entry_id` 同时是 agent-visible 版本 handle，每次 edit/status/schedule/archive 都变，不能用于累计义务。lineage 不向模型公开，也不由模型传入；branch 可共享不可变 item 行，但 key 必须带 branch 自己的 Conversation Ref，不能把父 Conversation 的义务带过去。

基线只建立一次。`notebook_show`、继续 Turn、重试模型请求、更换 handle、重复 edit、提交理由或 reload helper 不能重置它。若未来保留 Store 的 reload 能力，应把“初次基线”与“重新载入工作体”分开，正式 Noting 路径不能偷偷重建 baseline；不改冻结 Parent prefix 来同步较新 Notebook。

### 5.2 两轮含义

| 情况 | 判定 |
|---|---|
| Task A 从 active 开始，本次把 lineage X 标 done | X 是本 Task 新完成，获得观察窗口；若 A 成功提交，后续读取该 Snapshot 的 Task 才承担旧完成处置 |
| A 的第 2–5 个 continuation Turn | 仍是同一 Task，不算下一轮；基线、prefix、memo 输入保持 |
| Task B 实际加载 A 的已提交 done 版本 | X 进入 B 的 baseline 已完成集合，必须按获批准政策处置 |
| A 尚未提交，B 已先加载旧 active Snapshot | B 未见 A 的 done，不凭 admission 序号、时间或更大 item id虚构清理义务 |
| B 失败，Task C 又加载同一 done Snapshot | 义务仍在 C 的 baseline；不需要 B 成功生成中间 Snapshot 才叫“下一次尝试” |
| compaction／cold resume | Conversation Ref 与有效 Snapshot 不变；新的 Task 从它建立基线，不以物理 session 更换清掉义务 |
| rewind／edit 回到更早路径 | 使用该路径实际有效 current Snapshot；被撤掉的完成事实不能继续强制清理。当前 Child Anchor 失效仍放弃整个结果 |
| branch／fork | 新 Ref 从分支点有效 Snapshot 独立建立基线；继承已完成条目在分支首个维护 Task 中属于 baseline 已完成，父子处置不互相修改 |
| archive 后又需要同一事项 | 按原文创建新 lineage；没有 restore。不能无依据重建同内容以规避处置 |

“本轮刚 done 下一轮才可清理”若要成为强制机器规则，还涉及 archive 的原有语义，见 §9。不能只在 finish 检查：若新 done 已在本 Task 提前 archive，最终状态中已看不到它，单看 baseline 完成集合抓不住这个窗口。

## 6. 正向机制：一个 owner 生成完整处置与提交计划

### 6.1 结构与不变量

建议把清理判定归入既有 NotebookStore 的 task-local 生命周期，复用现有 WorkingState、immutable items 和 Child RLock。可以增加一个小型内部 sibling 承载纯判定，**它是 Store 的实现细节，不是第二 owner、工具或持久账本**。

owner 从固定基线和当前完整工作体生成一个不可变的内部提交计划，包含候选完整 payload／确切版本、适用义务和实际处置、原有 termination、冻结 Memo 输入等。模型只操作已有语义工具，不提交“已审查”bool、processed 列表、取消原因标记或 baseline。

不变量由以下结构保证：

1. **同一次语义写入产生完整合法版本。** 重新排期的 expression/mode 校验与必要 status 联动先同步完成，再 INSERT 一个版本。C84 已沿此方向实现；不先写 schedule、再要求模型补 status。
2. **义务从 immutable 基线推导，不可被 handle 变化重置。** 当前每个 lineage 只能是归档终版本，或有可用后续排期的活动版本；无关 edit／status 后又回 done 不构成处置。
3. **唯一准备动作证明可正常结束。** 两个 terminal 工具和 forced/overflow 转交同一个 owner；入口不各自维护状态名单和复杂 if/else。
4. **准备后固定工作体。** 在 Child 现有 RLock 内捕获版本并暂止新的语义写入，避免 terminal 预检通过后另一个调用改回非法状态；这是同一个 task 内的提交生命周期，不是新的公开条目状态或数据库 schema。失败则由同 owner恢复可写阶段，不能留“已结束”假标记。
5. **事务只能消费真实准备的版本。** 最终统一 commit 验证 profile/ref、基线引用和确切版本；验证与 Snapshot/pointer/Registry/Memo 写入在同一 conn，由异常回滚。不存在“检查过所以跳过提交校验”的捷径。

软提示可帮助模型选处置；不会证明 actual rearm、合法 archive 或真实下一次。把失败诊断追加在既有工具结果／新控制 suffix 可在将来审定 Prompt 后帮助恢复，但不能当不变量的实现。

### 6.2 可接受的继续工作结果

对最窄范围的 baseline done，继续工作必须是该 lineage 的当前正式版本：未 archived、处于对应活动态、有合法未取消的 Schedule／该类型正确的 delivery mode，并通过既有 rearm 机制取得有效的下一次投递意图。仅保留旧 canonical_schedule 字段不够；同 canonical 也不能因 Registry runtime.done 而假成功。

C84 已在同事务由真实旧／新有效 Snapshot 的 terminal→active 版本推导 reactivation，保持同 lineage schedule identity。清理设计应复用该机制，不能另造 reactivated 持久 flag 或重复 occurrence 授权。

“下一次”是否必须晚于提交时刻仍须审核。现行 one-shot 允许 overdue，关闭后再开启也允许过期一次投递；不得全局改成未来时间。候选政策：仅清理中的继续跟进要求新的未来 horizon，或允许已到期但尚未消费的一次合法投递。工作体预检使用统一计算计划，事务以实际 now 复核；不拿尚未提交的工作体去要求 current Registry 已提前出现。

若严格要求“commit 瞬间 next_run_at>now”，短延迟可能在准备到 commit 之间过期；这必须产生可诊断的重新排期要求，不能自动替用户加时间。真实 occurrence 在 commit 后正常被 scanner claim／送达，也不能让随后的只读观察误判那次 commit 未激活。

### 6.3 归档与 ID 变化

归档必须沿现有 `archive` INSERT 同 lineage、`archived=1` 的终版本，Snapshot 仍引用它，ordinary view 过滤。直接删除 payload id、创建替代 lineage、只把 status 改 done、只改字段和空操作，均不等归档。

同一 Task 中新 done 的观察窗口可由 owner在 archive 写入前，依据 baseline 与当前版本判定；不需要每一步记“做过什么”的模型台账。可是仅凭 archive 的现行 entry_id 参数不能机器判明“完成清理”还是“真实取消”，须按 §9 决策，不能添加一个取消工具逃避这项语义问题。

## 7. 最小正式接线与原子发布

下面位置为 2026-10-14 只读观察版本，函数名用于稳定定位。未来若批准，仅在既有接缝增量接线，不改原生循环、模型路由或权限。

| 正式位置 | 当前事实 | 候选最小改造职责 |
|---|---|---|
| `secretary/noting_tools.py:380 initialize_notebook_work` → `secretary/notebook_store.py:39/54 NotebookStore/load` | 从 current Snapshot 建 Task 工作体，初始化 RLock；Store 可 reload | 同一个 owner首次原子捕获 baseline；固定 task 生命周期，禁止下一次 show／continuation 重置 |
| `secretary/notebook_model.py:290 archive`、`:295 transition_status`、`:319 _apply_schedule_update`；`notebook_store.py:110–119` facade | archive/status 插完整新版本；Schedule 校验与活动态同步已接 C84 | 封装同 owner 的窗口／版本判定；沿既有 Schedule 更新完成继续工作，不新增反向 manual status 图 |
| `secretary/noting_tools.py:439 finish_noting` | 目前只校验 reason 后设置 terminal 标记 | 转交统一准备动作；拒绝时返回既有 success=false/error，列当前 entry id/type、baseline/current status、缺项；通过后才标正常结束 |
| `secretary/noting_compact.py:62 compact_parent_from_child` | 验证 Parent/profile/gate 后调用原生 Parent 压缩；成功标 terminal | 先由同 owner准备固定工作体，发现已知欠项先返回；通过后才请求 Parent 外部 side effect。不加 finish_noting第二终止条件 |
| `secretary/noting_child.py:537 _force_task_close`、`:614 _commit_when_complete` | M27／overflow 强制结束；随后统一尝试 Snapshot | 仅按 §8 已审核政策转交同 owner；不各自复制清理集合，不增加第六 Turn |
| `secretary/noting_child.py:389 commit_noting_snapshot`、`hermes_state_secretary_notebook.py:227 notebook_commit_snapshot_conn` | 当前一个写事务验证 Anchor/条目，INSERT Snapshot，consume memo，再 reselect pointer | 内部传受信基线／计划，在同 conn 验版本与义务后再写；任何失败回滚全部四层，不让直接 Store.commit成为绕行入口 |
| `hermes_state_secretary_notebook.py:181 _notebook_reselect_pointer_conn` → `secretary/schedules.py:143 reconcile_payload`／`:103 _schedule_reactivated` → `hermes_state_secretary_schedule.py:113 schedule_sync_conn` | 按当前有效 Anchor选 Snapshot；同事务同步真实选中状态，C84基于旧有效状态推导 rearm | 复用这条唯一正式发布链；事务验证实际 selected Snapshot 对应 Registry，不能对 candidate payload作假想验证后冒称已经生效 |

准备时复用 Child RLock 固定工作体；**不持 SQLite write conn／新全局锁等待 Parent 原生压缩**。Parent 请求在准备之后、最终 SQLite 提交之前执行；成功后最终事务再验证仍合法的 Anchor、enablement、版本和计划。正常 finish 没有 Parent side effect，也无需立即提交 Snapshot 来取代既有 framework owner。

Parent 压缩与 SQLite Notebook 发布不是一个跨系统事务：预检只能保证“已知清理欠项不先请求 Parent”；Parent 已成功准入后发生 rewind、关闭或数据库故障，Notebook 仍可拒绝，已准入压缩不能回滚，也不能因此伪造 Snapshot 成功。Parent 原生 Auto Compaction 不属于这个 owner，继续按原生机制执行。

late Anchor Task 仍遵循现行排序：旧合法 Anchor 可保存审计 Snapshot，却不能覆盖较新有效 pointer。Registry 必须反映真正 selected Snapshot，不能让旧 Task 把自己的 schedule重新投递。对旧 candidate 的处置证明和当前生效结果须分别报告；不能要求它的 item 必然出现在当前 Registry，也不能把较新 Snapshot 的未处理旧 done说成这次已清理。任何新“拒绝旧合法审计 Snapshot”政策均需明确修订，不能借提交机制悄悄改变现行晚完成语义。

Memo 按现有 `secretary/noting_memo.py:98 consume_memo_conn`：只在 Snapshot 同事务消费本 Task冻结且仍存在的 memo_id，期间新加／replace 的新身份保留；同 Anchor审计归档。没有 Snapshot 或事务回滚就不消费。**不增加模型声明用了哪条 Memo、做了什么、将 Memo 转 Notebook 或将它作为 provenance 的要求。** Memo 不作为清理义务的持久队列。

## 8. 五 Turn、overflow、异常强制结束与下一 Task 承接

### 8.1 现行 M27 不允许偷偷改变

现行 02 §5.8/5.9 与 04 M27/§4.6：最多五完整 Turn；terminal 未成功时框架仍尝试提交当前合法 Notebook（可为原 Snapshot或初始空四区）；special框架仍请求原生 Parent compaction，即使被拒也不单因此丢弃 Snapshot。context_overflow 无进一步 Turn，按同样流程尝试 Snapshot并在成功后发布 Finish Notice。真正失败／中断、崩溃、invalid Anchor、无效 Notebook 和写入失败继续不提交；Child永不跨进程续跑。

如果新义务把“原本合法但旧 done 未处理”的工作状态判为不能发布，就改变了 M27 的有效状态条件；若连 special fallback 压缩也拒绝，又改变了其兜底行为。**二者都是待用户审核的产品政策，现行机制保持。**

### 8.2 两个互斥方向与第三种高成本需求

| 待审方向 | 到五 Turn／overflow仍有 baseline欠项 | 怎样带到下一 Task | 得到／失去的保证 |
|---|---|---|---|
| A：严格“不发布仍有欠项的结果” | 统一 owner仍执行提交尝试但诊断拒绝，不 INSERT Snapshot、pointer/Registry/Memo不变；special已知拒绝不先发 fallback压缩；不加 Turn | 旧 current Snapshot中 done不变，后续既有 Trigger创建新 Child时再次自然成为 baseline义务；进程重启也保留 | 任何新发布结果都不带该欠项；但本 Task新维护成果，包括新标 done而尚未提交的事实，不能保留为 Notebook事实。须修订 M27／overflow及 special fallback |
| B：保留 M27强制有效 Snapshot优先，正常结束须处置 | forced／overflow沿既有合法工作状态原子提交，允许旧 done留在其中；normal finish/compact仍不能冒称完整处置 | 未处置条目仍以 done保存在新 Snapshot，下一 Task重新从真实 baseline识别；新 done也已保存。termination forced/context_overflow是现有审计事实，不等清理完成 | 保留跨压缩维护成果和既有 fallback；**不能声称“下个 Task一定处理完、强制路径不许积压”**。这是显式允许 carry-forward例外，不能伪称硬保证 |
| C：既不许 dirty Snapshot，又必须保留准确的部分维护成果与清理欠项 | 需要区别已发布 Notebook和未发布可靠 draft，或独立义务持久记录 | 现有 immutable item孤立行无 Task所属/完整顺序/完成资格，不能可靠恢复；必须新增受信 draft引用或其他真正持久契约 | 会扩大到持久草稿／恢复边界，触及 one-shot不续跑与额外状态成本；本文不建议默认采用，也不实施新表／ledger |

建议明日先选安全性还是强制保存优先，再定范围。**本文不替用户选定 A 或 B。** 严格 A不能包装成“仍完整保留本轮工作”；B不能包装成“硬门禁始终成立”。若要求 C，必须先说明为何需要保留未发布精确状态，再单独审定最小持久结构，不能把一个 `processed`标记或孤立 item视为足够。

### 8.3 各种中止的具体后果

| 情况 | Snapshot／pointer／Registry／Memo | 下一 Task含义 |
|---|---|---|
| 第1–4 Turn terminal预检失败 | 继续同 Child维护，工作体不丢；没有提前正式发布或 Memo消费 | continuation不是下一 Task；同 baseline欠项持续 |
| 第5 Turn缺项／context_overflow | 按获审 A或B处理；不追加第六 Turn，不自动归档或排期 | A重新读旧 Snapshot；B读强制新 Snapshot，欠项仍是 done；不能用 termination清掉义务 |
| 工具错误但 Turn可继续 | 既有success=false诊断；状态写入失败原子不变 | 不是自动允许结束理由 |
| 真实失败／中断 Turn或Child崩溃 | 现行不提交；pointer/Registry/Memo保持；已INSERT孤立 item只审计，不推断成功 | 新 Child从实际 committed Snapshot重新开始；不resume崩溃 Child，不以更大item id逃逸 |
| 提交时 Anchor离开路径／Noting关闭 | 放弃结果，不消费 Memo或挪 pointer；无新的清理后台工作 | rewind后重新读当前有效路径；关闭期间不承诺下一 Task何时来 |
| SQLite写失败／Registry reconcile失败／未知 COMMIT结果 | 必须沿既有事务错误与恢复事实判断，不能返回假成功或盲目再次发布；已确定rollback保四层不变 | 后续以数据库实际 current Snapshot为基线；不是模型声称成功的版本 |
| Task未提交但Parent已获准压缩 | Parent原生结果独立保留；Notebook/Memo仍按真实提交结果 | 不恢复Child；后续既有Trigger在实际原生context与current Snapshot上继续 |

采用 A时，baseline已经 done的欠项会自动存续，无需新增持久义务表。**本 Task才认出的结束事实**若最终失败，事实原文仍在History，但 Notebook不能保留未提交状态；后续 Noting需再次依据原文判断，本文不保证一定重做出同一语义结果。只有明确需要精确保存这部分失败 draft时才涉及 C，不能偷用 Memo做任务结果账本。

采用 B时，每次正常结束的处置证明仍从 Snapshot-derived baseline和实际结果形成；forced结果并非正常处置证明。若下一 Task又overflow，可能再次carry-forward，因此无“最多一轮积压”保证。把 forced条目的开始时间重置、换id、只新增 audit文字或宣称已检查都不能将它变为已履行。

下一 Task仅由既有Idle/Force/catch-up等合法Trigger产生；不为了清理欠项立即循环启动Child、不加scanner重试、不resume已失败Child。same Anchor去重仍适用，因此“保留义务”不等于“同 Anchor马上重试”；需要未来合法Trigger/Anchor。这个限制应明示，而不是靠新调度器掩盖。

## 9. 完成两轮规则与取消即时 archive 的边界

用户已明确：真正取消 secretary_task直接archive，不能schedule_cancel后留下空任务，取消前不需先标状态。现行archive也允许Noting在必要维护时移出条目；candidate执行完成、拒绝或撤回后按证据归档。不能把“仅明确完成可归档”扩成全Notebook禁止取消／撤回。

完成清理与取消的语义路径应区分：

- 工作完成：合法状态转换→本 Task Snapshot保留完成态→下一 Task决定继续排期或archive。
- 用户取消：原文意图立即生效于Main；Noting直接archive整条，保原Schedule意图于审计版本，不必伪造 done。

难点在于现行archive只收entry_id，没有可信的“此次为取消”机器标签。对 baseline active且未刚done的直接archive可以结构上保留原路径；对同 Task先done再archive，纯机器版本无法判断是清理过早还是后来取消。不能自行新增取消工具／model reason来当事实证明。

待审选项：①只把两轮窗口作为完成清理策略，保留现行archive一般权限，此时不能宣称代码完全禁止本 Task新done归档；②禁止本Task新done的所有archive，但会同时阻止此后发生的真实取消，需要用户明确接受；③依据可信原文证据区分例外，涉及新的证据绑定与语义判定契约，不能靠一个模型bool完成，必须单独审定。**目前不落实任一额外archive阻断。**

## 10. 必须保护的既有边界

- Main只读Notebook，Noting写入；只有专用Child白名单可调用既有维护工具，无新Audit／恢复／取消／清理工具；candidate实际外部持久化仍由Main获批后用现有能力完成。
- Raw History是事实源；candidate provenance只能为当前Conversation合法Message Identity或bounded time range；Memo不是来源。版本继承与branch重绑定保持现有精确body和source basis校验。
- Parent root、工具/schema与消息冻结prefix整个Task不变；仅Child后缀累积，continuation不刷新root／历史／工具头；不改Provider、API、推理或模型路由。
- global off、local off、non-eligible保持现行native／inert边界；清理不改Main admission、不阻断普通Main Turn、不启用Scanner新行为、不在关闭后后台偷偷清理。
- profile/DB归属从既有绑定获取；同Ref字符串出现在另一个profile不共享义务、Registry或Memo。tick／Child／RPC不得借启动profile替代目标profile。
- state.db只追加Secretary-owned结构，不改Hermes原表ownership/schema。候选 A/B可复用现有Snapshot/item/Registry，不默认新增表；若未来需要新结构，开发期重建仓库ignored测试库，不写migration、不清用户活动运行库。
- 不以终态统一清掉有效知识、待执行candidate或未完成义务，不按TTL清空Notebook；归档版本仍insert-only/audit-only，ordinary surfaces不可恢复。

## 11. 反例与未来验证计划（仅计划，未执行）

本文只有静态阅读和版本校核，没有运行测试、模型、浏览器、服务或构建。未来获用户批准后，按具体采用政策只做必要定向验证，沿 `scripts/run_tests.sh`、隔离profile/仓库内测试库，复用现有未受影响证据，不把C84测试当清理已验证。

| 反例／场景 | 应取得的机制／产品证据 |
|---|---|
| baseline done只改正文、换entry_id、同状态edit、status后又done、create同内容替代旧条目 | 原lineage义务仍未满足，诊断明确；没有processed bool逃逸 |
| 本Task新done在第2 continuation归档；下一真实Task归档 | 按获审窗口／取消政策分别处理；前者不被当作已经过一轮 |
| baseline done合法schedule_update，含同canonical、instant/deferred、watchpoint until | 状态+schedule同版本，实际选中Snapshot对应Registry可投递，不要求模型另call status |
| 非法expression/mode、过去one-shot、prepare后时钟越过due | 沿获审下一次时间政策诊断；失败无半成品版本／假重激活，不改变普通overdue语义 |
| Registry runtime.done／pending ACK delivered但Notebook仍running/active | 不判语义完成，不误清周期提醒；后续正常occurrence不重放 |
| 普通finish与special compact、准备中并发mutation | 单owner固定版本；缺项在Parent side effect之前返回；不持DB事务等待Parent，不留terminal假标记 |
| 五Turn、context_overflow、terminal错误、失败Turn、崩溃／重启 | A/B各自真实承接结果；原done不逃逸；新done未提交的限制如实；无第六Turn／自动retry |
| Snapshot/Registry/Memo消费各点故障 | 同事务回滚不挪pointer、不消费Memo、不发布假完成Notice；期间新增／replace Memo保留 |
| Parent compact成功后Anchor失效／关闭／写失败 | Notebook拒绝与原生压缩独立，不能假称跨系统rollback或Snapshot成功 |
| 晚Anchor完成、较新pointer、rewind回旧版本、branch继承、同Ref跨profile | Registry反映实际selected Snapshot；历史回选／branch不触发新rearm；义务与有效路径、Conversation/profile隔离 |
| decision.active、insight.validated、candidate只获批准、failed/dropped、直接取消archive | 保留语义差别；不扩范围；不将proposal当execution或强逼done |
| global/local off、non-eligible、native路径 | 原生未启用行为不变；无新admission/compaction/Reminder清理副作用 |

真实模型代表链只在机制与Prompt范围明确获批后再验证：看它能否依据原文选择正确处置、理解诊断继续维护；模型偶然完成不代替不变量证明。当前33 distinct C84开发证据只说明已交回修复范围，本文不重复运行或冒称清理通过。

## 12. 只读观察版本与可核定位

观察时仓库HEAD为 `24510d1c7c3b8dfc95b6d0626be30f090561fa30`。C84产品变更仍在共享工作区未提交；不能只引用HEAD断言它含最新修复。既有manifest见 `.hermes-dev/round2-verification/secretary-task-contract/schedule-reactivation/source-manifest.json`，owned 使用 `working_sha256` 区分HEAD旧版本；以下是本文实际读取源文件的SHA-256，用于后续核对函数位置，**不是运行行为测试**。

| 源文件 | 本次观察SHA-256 |
|---|---|
| `docs/02-noting-system-specification.md` | `2bc4a8a5ce315b3b1028171dcb502c880925082a841840a637993d6fa2914b19` |
| `docs/04-hermes-secretary-v1.5-implementation-spec.md` | `74070e260a57450066db6ef070706b7cb2da3270447ba55a8e9a36f906aab445` |
| `secretary/notebook_store.py` | `bb68da8372d9ec57f3acb4a55a7c402bfc144a67520c329ac79b1879dd096dbb` |
| `secretary/notebook_model.py` | `c7bfe089fb59a7abcafb3714226b6f5796fbbecf59b4f6532c6e0101df602230` |
| `secretary/notebook_schedule.py` | `b0c6f99b1fe224f7c2c87b09853633025d5b2b291ded8b80dd0959eee160f2a2` |
| `secretary/notebook_items.py` | `abfa847ce6822a990ecfde9a32c5c2f4e8794e547974d4d22a77b47fe2d43b5d` |
| `secretary/schedules.py` | `ad670f32ef4c2431e96463600c39d98fbf0f0ca4156eb1ac5b5cb8330163848c` |
| `hermes_state_secretary_notebook.py` | `d809d42d5e87244b07e642e75a93622941e7e590f0bd4d3d6747d248bbd225a0` |
| `hermes_state_secretary_schedule.py` | `60732f6698c7321ccb1b15fcf42e28a936d642216e621450316bdcf8ed6094c8` |
| `secretary/noting_tools.py` | `3493d22d7a56d41cfe83ae2699fdfa00cf510fed9617ded738a590ae63f99fda` |
| `secretary/noting_compact.py` | `98b8a5ace323ecd5b0cf2b517b316b97c31ea46cfa4b24f82b508eb954998a01` |
| `secretary/noting_child.py` | `bb8708f769de2b2dbb41af53d625b70bb41d5b2199b52d774d1d567c82290b38` |
| `secretary/noting_memo.py` | `619e97821bd21c437811638a48b946e4f7b2954bf88897f1fae5ea9aab492ea7` |

C84五产品当前位置已具备：统一终态→活动初始态、同一item版本Schedule/status、旧有效Snapshot同conn传递、同lineage新版本terminal→active推导、Registry同canonical rearm。本文以实际源文件确认这些接线存在；未把报告里的历史“schedule_update不改status”当当前事实。source-manifest列出的测试与checks仍由Main复核接收，本文未重跑。

## 13. 明日需要审核的政策

1. 最窄强制处置范围是否仅 `secretary_task.done`／`user_commitment.done`；哪些扩展类型可纳入，哪些需要不同处置出口。
2. 五Turn／overflow选择A严格拒绝还是B保留强制Snapshot的显式carry-forward例外；是否确实需要C准确保存未提交draft。
3. 本Task新done不得archive的强度，以及同Task后来取消的例外；不添加取消工具如何保持现行archive权限。
4. “实际下一次”对未来性、已到期未消费one-shot的要求；不得改变现有普通overdue-once规则。
5. 对无Schedule类型是否只做证据审查建议；避免为保留有效知识强造新条目、状态或排期。

在上述口径获确认前，**本文硬机制及其拒绝式工具文案保持未实施**。本轮用户另行授权的整体维护软提示由Main独立实施并对账，不构成本文候选硬规则或M27政策的批准。批准后须先把新规则写入相应权威规格，明确M27／archive差异，再在同owner正式接缝实现与验证；不能用本文先行替换现行契约。
