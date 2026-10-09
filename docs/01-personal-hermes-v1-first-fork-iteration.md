# Hermes Secretary V1：首次 Fork 实施总纲

> **状态：** V1 核心实施总纲，已纳入 1.5 轮用户确认的补充调整
> **用途：** 定义本轮 Fork 的目标、边界、能力关系、实施顺序与验收口径；不替代具体实现规格。  
> **权威实现规格：** V1 继承契约见 `02-noting-system-specification.md`；V1.5 明确修订范围以 `04-hermes-secretary-v1.5-implementation-spec.md` 为最高优先级增量规格。未修订部分仍以 02 为准。
> **后续路线材料：** 03 保存在仓库外，本轮不纳入考量，也不作为实现依赖或验收依据。

---

# 1. 本轮目标与实施原则

Hermes Secretary V1 的第一次 Fork，不是把 Hermes 重写成另一套 Harness，而是在 Hermes 现有 Session、Gateway、Compaction、tool/runtime、state persistence 等机制之上，补齐一组长期个人对话真正缺失的基础能力：

- 为用户语义上的 Conversation 建立稳定身份；
- 让主 Conversation 可以可靠检索自己跨 Compaction 的真实历史；
- 为每条直接与用户交流的主 Conversation 提供跨 Compaction 持续存在的结构化 Notebook；
- 通过后台 Noting 持续维护 Notebook，而不是让主 Assistant 在聊天过程中随手写状态；
- 为 Notebook entry 提供 Conversation 内的 Schedule、Reminder 与后续跟进能力；
- 保持这些改造尽可能 additive，并在 Noting 不生效时最大限度恢复 Hermes 自己的已知行为。

本轮遵循以下原则。

## 1.1 Hermes-first

Hermes 已经拥有的机制优先复用，不建立平行实现：

- physical Session 与 transcript persistence 继续由 Hermes 管理；
- Turn 继续使用 Hermes `run_conversation()` lifecycle；
- message identity 建立在 Hermes `message_uid` 上；
- compression、branch、reset 等 Conversation boundary 继续以 Hermes 当前语义为准；
- Gateway ingress / busy admission 继续使用 Hermes 现有路径；
- Parent compaction 继续交给 Hermes native compaction lifecycle；
- Schedule 的时间表达解析与 next-run 计算可复用 Hermes Cron 的通用代码。

Secretary 只新增 Hermes 原生模型中确实缺失的身份、状态和控制层。

## 1.2 Additive-first

首轮持久化采用对现有 `state.db` 的增量扩展：

- 新增 Secretary-owned tables；
- 不修改 Hermes 现有 tables 的字段、主键、外键或既有语义；
- 不把 Secretary ownership 塞进 `sessions`、`messages`、`conversation_generations`、`gateway_routing` 等现有表。

Core patch 只允许出现在已经确认的接线点。能通过现有 lifecycle、projection、Gateway admission 或公共 helper 接入的，不新增第二套核心路径。

## 1.3 Conversation 是 source of truth

Raw Conversation transcript 始终是事实来源。

Notebook 是从 Conversation 派生出来的 working state，而不是 Conversation summary、长期记忆库或新的事实权威层。主 Assistant 先通过当前 Conversation Foreground 立即理解和执行用户意图；Noting 随后把需要长期维持在该 Conversation 内的工作状态整理进 Notebook。

## 1.4 先完成 Secretary core，再接个人私有能力

本轮仓库实施只处理 Hermes Secretary 的通用核心能力。

以下个人化能力不进入本轮 Core Fork：

- Nowledge Mem / 其他个人长期记忆 Provider；
- pre-turn Recall / memory candidate prefetch；
- 个人 System Prompt / Character / Persona 注入；
- Hermes Conversation → 外部长记忆系统的同步；
- Memory Governance / Dreaming / 定期核查；
- Hermes+ / 额外 RSI 机制；
- Remote Mac capability node、VFS、统一远程 CLI/MCP gateway。

这些能力可以在个人插件、私有分支或后续阶段接入，但不得反向污染本轮 Secretary core 的抽象。

---

# 2. 首轮必须完成的能力面

本轮不是若干互不相关的小功能，而是一条由 Conversation identity 向上建立的完整链路。

## 2.1 Conversation Identity Foundation

Hermes 的 physical `session_id` 不能直接承担 Secretary 的长期 Conversation ownership。V1 因此新增稳定的 `Conversation Ref` 与 Conversation Identity Registry。

核心关系是：

```text
Conversation -> physical Session : one-to-many
physical Session -> Conversation : single-valued
```

`Conversation Ref` 是 Secretary-owned、durable、opaque 的一级身份。Hermes 的 compression lineage root、declared `(source, session_key, generation)` conversation identity 等都只是 locator / alias，而不是 Conversation Ref 本身。

这层身份随后统一成为以下状态的 ownership key：

- Notebook；
- Notebook Snapshot；
- Anchor；
- Conversation-local Noting enable state；
- Notebook Schedule；
- pending Reminder delivery；
- Noting admission / same-Anchor dedupe。

这样当前只使用普通 Session 的 Conversation，未来再接入 Hermes Channel / `session_key` 时，不需要迁移 Notebook 或 Schedule，也不会改变既有 Conversation Ref。

完整 resolver、alias reconciliation、conflict handling 与 runtime route resolution 见 02。

## 2.2 History Search：独立于 Noting 的基础能力

V1.5 已替代此前“与 read 一样由普通配置和模板选择暴露”的策略：所有直接与用户交流的合格 Main 默认且不可配置地拥有 `session_history` 与独立 History Guidance，不受全局或局部 Noting 控制。它检索当前未压缩历史及跨 Compaction 原文。辅助 Agent 不因本轮获得新的主会话注入，保留其既有合法工具配置；专用 Noting Worker 保持 V1 的受限父历史读取契约。详见 V1.5 §2.2、§2.6、§3。

它始终读取 **History Foreground**：

- 跨同一 Conversation 的 compression continuation；
- 保留真实历史；
- 去掉 compaction scaffolding；
- 排除 rewind/edit 后已 supersede 的路径；
- 返回可用于 provenance 的 canonical Message Identity。

已有 History Search 工具契约继续有效，包括 search/read、keyword/regex、role filter、bounded history/time-range read，以及围绕 Message Identity 的前后读取。

History Search 的主会话默认暴露与专用 Stable Guidance 独立于 Noting 开关；工具与身份权限遵循 V1.5 §2.2、§2.6、§3。

## 2.3 Session Notebook

只有直接与用户交流的 main Conversation 拥有 Notebook / Noting System；每条这样的 Conversation 恰好拥有一份 current Notebook working state。Cron Task、Dreaming、Skill 打磨、通用 Subagent 等后台或辅助 runtime 不参与该系统，全局配置 on/off 均不改变这一资格边界，其工具列表绝不出现 notebook_show。专用 Noting Runtime 仅维护所属主 Conversation 的 Notebook，不为自己创建独立 Notebook。

Notebook 使用四区十类型：

```text
user
├── user_commitment
└── user_reminder

assistant
├── agent_task
└── watchpoint

consultation
├── decision
├── open_question
└── formulating_insight

persistence
├── memory_candidate
├── rule_candidate
└── skill_candidate
```

Notebook 不是 mutable master JSON。每次成功 Noting 提交完整 immutable Snapshot，再原子移动 current pointer。

主 Assistant：

- 在直接与用户交流的主会话资格成立且全局 noting.enabled=true 时获得只读 notebook_show；局部 Noting on/off 不影响该工具的暴露或已有 Notebook 的读取；
- `notebook_show` 返回完整结构化 Notebook JSON；
- 永远不获得 Notebook mutation tools。

人类通过 Slash Command 使用：

```text
/notebook
/noting on
/noting off
```

裸 `/notebook` 面向人类展示 current Notebook 的可读投影，并显示该 Snapshot 的 timestamp；结果沿用正常 Hermes 历史语义，AI 也能看到。/noting on、/noting off 只控制当前主 Conversation 的后台 Noting 参与状态，不改变主 Assistant 工具 schema。Conversation-local `/noting off` 不删除已有 Notebook；当全局 Noting 仍开启时，裸 `/notebook` 仍可查看已有 Snapshot，pointer 为空则明确报错。

## 2.4 Noting

Noting 是本轮最主要的后台行为扩展。

它接管原 Background Self-Improvement Review 的产品生态位，但不会简单把旧 Background Review 原样改名。旧实现中有价值的 cache-parity machinery 应抽取为通用 helper；旧的自动 memory/skill review 产品行为在 Secretary 模式下停止运行。

Noting 负责：

```text
Conversation
→ periodic / forced inspection
→ understand current state
→ update Notebook working state
→ commit immutable Snapshot
```

V1 只有两个 Trigger：

- Idle Trigger；
- Force Trigger。

V1 只有两个 Runtime Profile：

- `NOTING`；
- `NOTING_WITH_COMPACTION`。

Noting 使用 persistent Hermes child Session + 始终保留的冻结Parent root/消息前缀 + 从noting-task起收窄的真实Noting工具面。它是 process-lifetime one-shot task；进程中断后不恢复，未完成的任务不能移动 Notebook pointer。

主 Conversation 后续活动不会自动取消一个已经成功 admit 的 Noting Task。最终安全门是 commit 时重新验证 frozen Anchor 是否仍然位于当前 Full Foreground。

Trigger、Force threshold、admission、same-Anchor dedupe、compaction interaction、persistent child lifecycle 与 cache-parity 细节全部见 02。

## 2.5 Notebook Schedule 与 Reminder Delivery

Schedule 是 **Notebook-owned、in-Conversation scheduling capability**，属于 Noting / Notebook 的附属能力。

它不是 Hermes Cron Job，也不是 Hermes Cron 的替代品。Secretary 自己持久化 ConversationScheduleRegistry 与 mutable due state；Hermes Cron 只在适合时提供时间表达解析和 next-run calculation 等通用能力。

V1 有两种 delivery semantics。

### Passive System Reminder

用于：

- `user_commitment`；
- `agent_task`；
- `watchpoint`；
- 已冻结的内部 passive reminder 场景。

Schedule 到期后只进入 durable pending 状态，不主动创建 main Turn。下一次 eligible main LLM request 拉取并注入 `<system-reminder>...</system-reminder>`。

### Active User Reminder

用于 `user_reminder`。

Schedule 到期后，通过现有 Hermes Gateway ingress/admission 路径尝试以 synthetic `role=user` 输入重新进入原 Conversation：

- Conversation idle：启动新的 main Turn；
- Conversation busy：不排一个额外未来 Turn，而是在现有 busy gate 转成 pending System Reminder。

Schedule registry、due scanner、restart behavior、claim/idempotency 与两条 delivery wiring 的完整规格见 02。

## 2.6 Message Timestamp / Synthetic Wrapper Contract

本轮还统一 Conversation 内需要显式时间语义的消息格式。

真实用户消息在真实 content 前附加既定 HTML-style timestamp marker，不包裹全文。

Secretary synthetic input 使用完整 wrapper，当前冻结的 wrapper 至少包括：

```text
<noting-task>...</noting-task>
<system-reminder>...</system-reminder>
<user-reminder>...</user-reminder>
```

这些 synthetic carrier 均使用 Hermes/provider-neutral 的 `role=user`。Timestamp 位于 wrapper 内第一行，随后才是真实 synthetic content。

准确格式、timestamp source 与持久化/注入位置见 02。

---

# 3. Enablement 与 Hermes-native 回退边界

Noting 的实际启用状态由两层共同决定：

```text
effective_noting_enabled
=
global noting.enabled
AND
Conversation-local Noting enabled
```

Conversation-local 状态持久化在 Secretary 自己的 state 中。

当某条 Conversation 的 Noting effective disabled 时：

- 不运行 Idle / Force Noting；
- 不启动 Noting child；
- 不执行 Notebook mutation；
- Notebook Schedule 不参与 due processing；
- 不产生 Noting-owned Reminder delivery；
- 后台行为门禁不改变主 Assistant 的 Notebook 只读工具面；notebook_show 只由主会话资格和全局配置决定。

History Search 不受影响。

在全局 Noting 开启但当前主 Conversation 局部 Noting 关闭时，人类 /notebook 和 AI notebook_show 都仍可读取已有 Snapshot。后台 Noting、Schedule 和 Reminder 的有效门禁继续按 02；读取权限不再使用这个局部门禁。

除此之外，Secretary 不应为该 Conversation 引入新的行为差异。与 Hermes 全局配置存在的少数已知冲突，只在相关 Noting 能力启用时按 02 的规则处理。

---

# 4. 持久化与改造边界

本轮所有 Secretary durable state 进入现有 `state.db`，采用新增表，不建立 JSON sidecar 或第二个数据库作为 Notebook 真值。

概念上至少包括：

```text
Conversation Identity Registry
Conversation-local Noting state
current Notebook pointer
immutable Notebook Snapshots
Notebook Schedule runtime state
必要的 Noting admission / delivery state
```

具体 table/column 名称由实现按 Hermes repository convention 确定。

关键不变量：

- 不修改 Hermes 现有 tables 的 schema/ownership；
- Snapshot 是 immutable complete state，不是 diff；
- current pointer 与新 Snapshot commit 原子更新；
- Schedule mutable runtime state 与 immutable Snapshot 分离；
- Snapshot、Schedule、Reminder ownership 全部基于 `conversation_ref`；
- physical Session 只用于 runtime execution/routing，不作为 Notebook ownership。

Frontend / API 的更大范围增量 contract 仍保持 Open。本轮只实现核心功能真正需要的最小接口；不重新设计 Hermes API hierarchy，不重做 UI framework。

---

# 5. 建议实施顺序

实现应按依赖关系推进，而不是先做 UI 或先做零散 Trigger。

## Phase 1 — Identity 与 History foundation

先完成：

1. Conversation Ref / Identity Registry；
2. current Session → Conversation Ref resolver；
3. Channel/session-key locator 的兼容路径；
4. History Foreground；
5. History Search 全部既有契约；
6. branch/reset/compression identity tests。

这一阶段完成后，Secretary 已经拥有稳定的 Conversation ownership 与可靠历史读取能力。

## Phase 2 — Notebook persistence 与 control

完成：

1. Conversation-local Noting state；
2. immutable Snapshot + current pointer；
3. 四区十类型 semantic model；
4. Noting-only semantic mutation tools；
5. main Assistant `notebook_show`；
6. `/notebook`、`/noting on`、`/noting off`；
7. branch/rewind/edit pointer reconciliation。

## Phase 3 — Noting runtime

完成：

1. cache-parity helper 抽取；
2. persistent Noting child；
3. `NOTING` / `NOTING_WITH_COMPACTION`；
4. Idle / Force Trigger；
5. Anchor freeze / same-Anchor admission；
6. `compact_parent`；
7. process-lifetime ownership、commit gate 与 failure handling。

## Phase 4 — Schedule / Reminder

完成：

1. ConversationScheduleRegistry；
2. Notebook semantic mutation → schedule register/update/cancel；
3. thin due scanner + restart recovery；
4. passive System Reminder request-time delivery；
5. active User Reminder → existing Gateway admission；
6. busy fallback；
7. claim/ACK/idempotency tests。

## Phase 5 — Integration hardening

最后处理：

- unified timestamp/wrapper contract；
- Noting-disabled Hermes-native regression tests；
- concurrent Trigger / Compaction / Rewind race tests；
- current Hermes upstream symbol/wiring revalidation；
- 最小 Frontend/API gap。

如实施顺序与 02 中的具体 correctness dependency 冲突，以 02 为准。

---

# 6. Definition of Done

首轮完成不是“代码大致跑起来”，而是以下能力形成完整闭环。

| 能力 | 最低验收结果 |
|---|---|
| Conversation Identity | 一个 Conversation 在 compression rotation、普通继续以及未来新增 declared session-key locator 时保持同一 Conversation Ref；branch/reset 创建新 Conversation；identity conflict fail closed。 |
| History Search | 合格 Main 默认拥有只读 session_history 及独立指导；当前未压缩历史与跨 Compaction 历史都可 search/read；Noting 开关不控制该能力；辅助 Agent 隔离遵循 V1.5。 |
| Notebook | 用户主 Conversation 有独立 current Notebook；Snapshot immutable；pointer 原子更新；主 Assistant 只读；branch/rewind/edit 后 ownership 与 pointer 正确；通用后台与 Subagent 不暴露 Notebook。 |
| Noting Enablement | global + Conversation-local 两层后台 gating 正确；局部开关不改变主会话工具 schema；global on 时人类 /notebook 与 AI notebook_show 仍能读取已有 Snapshot。 |
| Idle / Force Noting | 两个 Trigger 均按 02 规则运行；同 Anchor 不重复 admit；不同 Anchor 可以合法并发；Force 与 Hermes compaction 不互相替代。 |
| Noting Runtime | persistent child、cache parity、narrow dispatch、one-shot lifecycle、commit-time Anchor validation 均正确；失败/崩溃不提交 Snapshot。 |
| Schedule | Notebook-owned registry 持久化可靠；Noting disabled 时不 fire；restart 后恢复；不创建 Hermes Cron Job。 |
| System Reminder | due 后不启动 Turn；在下一 eligible main LLM request 注入；失败不丢；ACK/重试不造成无控制重复。 |
| User Reminder | idle 时通过现有 Gateway admission 启动 main Turn；busy 时在现有 busy gate 转为 pending System Reminder，而不是排第二个未来 Turn。 |
| Timestamp / Wrappers | real user timestamp 与 `<noting-task>` / `<system-reminder>` / `<user-reminder>` 的位置、role 和 persistence 行为符合 02。 |
| Hermes-native fallback | Noting effective disabled 时，除已定义的 Secretary capability absence / config conflict 外，主 Conversation 沿用 Hermes 自己的已知行为。 |
| Persistence | Secretary 只向 `state.db` 增加自己的 tables，不改 Hermes 现有 table schema/semantic ownership。 |

---

# 7. 本轮明确不做

以下内容不应在首轮实现过程中顺手扩张：

- 个人长期记忆 Provider / NM integration；
- 自动 Dreaming / Memory Governance；
- personal prompt / character system；
- Remote Mac / VFS / device capability network；
- Assistant / Character / Channel / Conversation Group 的完整产品模型；
- 为 Notebook Schedule 替代 Hermes Cron 或另造通用 job scheduler；
- 全新 API stack；
- 全量 Dashboard / Desktop / WebUI 重写；
- Noting task 的 crash-resume / distributed workflow engine；
- 主 Assistant 直接写 Notebook；
- Noting 访问 Web、filesystem、Memory、Skills 或外部数据源。

03 保存在仓库外，本轮不纳入考量。首轮实现只以本文和 `02-noting-system-specification.md` 为依据。
