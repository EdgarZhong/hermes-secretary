# Hermes Secretary V1.5 — 实施权威规格

> **2026-10-09 用户补充授权及纠偏：** 本轮索引C05–C13（C12/D01仍未定稿）：Noting每次请求保留完整冻结父快照前缀，包括root、原工具列表/Schema与到Anchor的消息，不改写头部。在`<noting-task>`及后续新增的系统提示/控制消息中追加当前可用History/Notebook工具列表和完整Schema，强调以此为准；特殊profile另含compact_parent，实际dispatch按Noting白名单限制。此前“从首请求改实际顶层Schema、撤销父工具前缀parity”是Agent理解偏差，现撤销。机制停留在Hermes中间层上下文复用，模型继承、API/provider直接使用Hermes原生，不新增独立模型路由、provider改造或App Server Noting执行器。本轮真实运行选择仍为DeepSeek官方Anthropic/deepseek-flash思考模式；缓存观察使用Hermes自身日志或抓包。原始附件保留在d5acc冻结树，以下正文按最新用户澄清同步。

> **规格状态：** 既有定案契约继续有效；§4.5 D01外部Agent runtime继承边界按C12仅记录待论证问题，未定稿，等待用户重新论证。实施与最终验收仍暂停；本文不代表代码已经修改或通过验收。
> **实施对象：** `EdgarZhong/hermes-secretary`，承接 V1 首轮实现。  
> **规格角色：** V1.5 的最高优先级**增量修订规格**，不是独立替代 V1 的全量重写。  
> **原始依据：** `docs/01-personal-hermes-v1-first-fork-iteration.md`（下称 **V1-01**）、`docs/02-noting-system-specification.md`（下称 **V1-02**）、`.autonomous/20261007-v1-first-implementation/` 的冻结与审查记录、`.autonomous/20261008-v1.5-adjustment-and-acceptance/index.md`，以及本轮用户已定案的修订口径。

---

## 1. 规格定位、继承关系与实施边界

### 1.1 目标与基本原则

V1.5 只完成 V1 首轮实现后的必要调整、已确认缺口修复和最终验收，不启动第二轮 Personal UI 产品化。实施应以真实现行代码为对象，沿用 Hermes 原生 Session / Conversation lifecycle、System Prompt tiers、Gateway Agent cache、Slash、Compaction、工具注册与权限机制，不搭建平行子系统。

规范性用语：**必须 / 不得**为强制要求；**应**为默认实现要求，偏离需要明确证据；**可以**为允许但非必需。本轮没有授权的新特性不得凭实现便利自行加入。

### 1.2 V1 → V1.5 全范围继承、扩展、修订对照表

本表是后续**所有章节的强制对应索引**。每一项实施、测试、代码审查与验收，必须能回溯到此表、相应 V1 条款和本轮定案；未列为变更的 V1 机制继续有效。若 V1-01、V1-02 与本文件冲突，以本文件**明确修订的范围**为准；未修订部分以 V1-02 的详细约束为准。对 V1-01/V1-02 的同步修订不得追改首轮历史冻结证据。

| 编号 | 能力或契约 | V1 对应 | V1.5 性质 | 具体继承／变更边界 | 本文位置 |
|---|---|---|---|---|---|
| M01 | Hermes-first / additive-first / 非目标 | V1-01 §1、§4、§7；V1-02 §1.8、§3.1 | **继承** | 只复用／增量修改现有运行与持久化路径；不扩张 Personal 范围 | §1.1、§1.5、§7 |
| M02 | Conversation Ref、Locator、Message Identity | V1-01 §2.1；V1-02 §1.1–§1.6 | **继承** | 身份定义、alias 冲突、路由与所有权不重设计 | §2.1、§7 |
| M03 | Runtime 资格及辅助 Agent 隔离 | V1-01 §2.3；V1-02 §1.9、§3.5、§5.7 | **修订／澄清** | 主会话两种只读能力精确门禁；其他类型不因本轮获得新注入 | §2.2、§3.1 |
| M04 | Active Foreground | V1-02 §2.1 | **修订／精确化** | 以实际 provider-request 的有效上下文为准，明确实时视图边界 | §2.3 |
| M05 | History Foreground | V1-02 §2.2 | **扩展／精确化** | 保留真实消息事件与跨 Compaction 原文，排除派生 scaffold／无效路径；与 Active、Full 严格区分 | §2.4 |
| M06 | Full Foreground | V1-02 §2.4、§2.6–§2.7；首轮审查 R015 | **实质修订** | 首节点为 Context Prelude；其余为与 Message Identity 一一对应的逻辑消息节点，唯复合 Compaction carrier 允许双投影；关闭首轮缺口 | §1.3、§2.5 |
| M07 | History Search 语义与基础操作 | V1-01 §2.2；V1-02 §2.3、§6.4 | **继承＋修订** | 继续只读当前 Conversation、支持 search/read；**废止**“与 read 一样由模板/配置选择暴露”的旧策略 | §2.6 |
| M08 | History Search 默认暴露与 Stable Guidance | V1-02 §1.9、§2.3；旧 Secretary Prompt | **新增／替换** | 所有用户主会话默认、不可配置且不受 Noting 开关影响；新增独立两句 Guidance | §2.2、§3.2、附录 A |
| M09 | Notebook 四区十类型／字段／状态图 | V1-01 §2.3；V1-02 §2.5 | **完全继承** | 不改类型、字段、状态流转、分类含义，不增独立 section 字段 | §4.1 |
| M10 | Snapshot、Pointer、Anchor、分支与回退 | V1-02 §2.6–§2.7、§3.1–§3.4 | **继承** | 不可变完整 Snapshot、原子 pointer 与 provenance 仍按 V1 | §4.1、§7 |
| M11 | Main `notebook_show` 与只读权限 | V1-02 §3.5、§5.7 | **修订** | 只按主会话资格 + **全局** `noting.enabled` 注入，与局部开关完全解耦 | §3.1–§3.4、§4.2 |
| M12 | `/notebook` 与局部 Noting Slash | V1-01 §2.3；V1-02 §3.6 | **修订** | `/notebook` 仅展示；`/noting on|off` 仅改变后台参与并持久化反馈；旧 `/notebook on|off` 退出 | §4.2–§4.3 |
| M13 | Noting 两层启用、Idle/Force、准入与阈值 | V1-02 §4 全章 | **继承＋门禁澄清** | Trigger／Force 机制不变；局部开关只管后台行为，不管 Notebook 读取 | §4.3、§4.4 |
| M14 | Noting Worker 生命周期、缓存前缀、工具权限 | V1-02 §5.1–§5.5、§5.7–§5.11 | **继承＋澄清** | 完整父root/tools/消息前缀始终冻结；新工具列表/Schema只追加在task及后续新系统提示中并声明优先；dispatch受限，模型/API/provider沿用原生 | §4.4 |
| M15 | Noting Task 的 Candidate 清理与 Schedule 认知 | V1-02 §2.5、§3.7、§3.8、§5.6 | **最小扩展** | 补充按主会话进展修订／归档 Candidate 与 in-Conversation Schedule 边界 | §4.4 |
| M16 | Notebook Schedule 的归属、Registry、scanner | V1-01 §2.5；V1-02 §3.8–§3.10 | **继承** | Schedule 不跨 Conversation、不创建 Hermes Cron Job；运行与持久化机制不重设计 | §5.1、§5.3 |
| M17 | Schedule 时间表达式工具描述 | V1-02 §3.7–§3.8；现有 `notebook_mutate` | **扩展** | 在 `expression` Schema 中写明复用的五类 Hermes Cron 时间表达式，**不是**简单写“与 Cron 相同” | §5.2、附录 B |
| M18 | System/User Reminder、时间戳与包装 | V1-01 §2.5–§2.6；V1-02 §3.11–§3.12、§5.6 | **继承** | 被动／主动投递、busy 回退、ACK、retry、role/user/timestamp 不重设计 | §5.3 |
| M19 | Stable Prompt 增量模块 | V1-02 §3.5；首轮 `SECRETARY_GUIDANCE` | **替换** | 删除未授权的混合模块，分别引入 History 与 Secretary Work/Notebook 两个 Stable 模块 | §1.4、§3.2、附录 A |
| M20 | 全局配置热切换与缓存一致性 | V1-02 §4.1–§4.3、§5.11；Hermes 原生 Prompt cache | **新增实施契约** | 下一次主会话 Pre-message Context 立即一致生效；允许主动损失缓存；不自造缓存架构 | §3.4–§3.5 |
| M21 | Persistence Candidate 的审核、批准和写入 | V1-02 §2.5；V1 首轮 `/propose-persistence` | **澄清＋修订** | Candidate 仅线索；提案和用户明确批准后才可执行；讨论／修订不视为批准 | §6 全章、附录 C |
| M22 | `/propose-persistence` 证据召回方式 | V1 首轮 Slash；V1-02 §2.3、§2.5 | **修订** | 不再自动拼贴预检索 Source Evidence；由主模型使用 History Search 主动深查 | §6.1–§6.3 |
| M23 | Dashboard、共享 Slash、验收渠道 | V1-01 §4–§6；V1-02 §6.19；首轮报告 | **继承＋补齐** | 官方 Dashboard 仅作端到端用户验收；不做 Personal UI 产品化 | §7.3 |
| M24 | 独立 Verification / Validation、回归门禁 | V1-01 §6；V1-02 §6；首轮 Verification | **扩展** | 覆盖本轮变化、旧缺口和 V1 未改契约，不能复用旧通过声明替代新验收 | §7 全章 |
| M25 | Foreground 术语、Prelude 与节点映射 | V1-02 §1.1、§1.6、§2.1–§2.4；首轮审查 R014–R015 | **继承＋精确化／修订** | 继承 Conversation/Message Identity；精确定义 Pre-message Context、Context Prelude 与 Full 首节点；锁定普通节点 1:1 Message Identity 和复合 Compaction 特例 | §1.3、§2.5、§7.2 |

**落实规则：** 后续每项工作至少标注一条 `Mxx` 和对应 V1 条款；若出现表中没有的功能需求，先归类为 V1 既有契约还是 V1.5 新增变更，不得悄然变成代码要求。

### 1.3 术语表与 Foreground 节点不变量（M02、M04–M06、M20、M25）

以下术语在全文及其实施、工具、接口、审计与验收中具有统一含义。既有 V1 身份模型沿用 V1-02 §1.1、§1.6；其中 Full Foreground 的具体结构由 V1.5 §2.5 修订。

| 术语 | 精确定义与区别 |
|---|---|
| **Conversation** | 与用户持续交互的一条语义上连续的对话路径；一次 Compaction 或物理 Session rotation 不会自动创建新 Conversation。Branch/Fork、Reset/New 按 Hermes 的边界规则产生新 Conversation。**Conversation ≠ physical Session**。 |
| **Conversation Ref** | 该逻辑 Conversation 稳定且不透明的 Secretary owner identity；不得用当前 Session ID、Channel 路由键取代。 |
| **Message Identity** | **`(conversation_ref, message_uid)`**，当前 Conversation 路径中一条逻辑 Message 的规范身份。它不是物理数据库行 ID `message_id`；物理复制、压缩续接与跨分支同名 UID 均不能取代该二元身份。 |
| **Pre-message Context** | 为一次合格 Main Conversation 的模型请求，**在对话消息序列之前准备的有效上下文与其组装边界**，包括本次实际采用的 root System Prompt 和可调用 Tool Schemas／工具面。V1.5 的全局开关同步必须在下一次主 Turn 的这一构建边界、且在首次模型请求发出前完成。它是运行时请求构建概念，**不是**额外 Conversation Message、独立的数据库节点，也不等同于 System Prompt 三层中的 `context` tier。 |
| **Context Prelude（Prelude）** | **Full Foreground 的唯一首节点**，提供从 Hermes 真实运行与恢复来源读取的、当前**最新有效** root System Prompt 及 Tool Schemas 的审计投影。它对应 Pre-message Context 中需要固定审计的 Prompt／Tool Surface，但**不是**逐次请求内容的全量副本，也不维护每次重建的历史版本。Prelude 不属于 Messages，不具有 Message Identity。 |
| **Active Foreground** | 当前主模型请求实际使用的有效运行上下文；与 Full 的审计视图不同，不是简单地从数据库重组 Messages。 |
| **History Foreground** | 当前有效 Conversation 路径上的真实历史原文检索视图；跨 Compaction 保留源消息，去掉不属于真实消息原文的 Compaction scaffolding，不包含 Prelude、Notebook 审计投影。 |
| **Full Foreground** | **有序结构：`[Context Prelude, Message Node 1, Message Node 2, …]`**。首节点之后只排列沿当前有效 Conversation 路径的逻辑消息节点；Compaction 交接消息仍属消息节点，Anchor、Snapshot 等只作为其关联审计信息，不另伪造成消息。 |
| **Full Message Node** | 除下述复合 Compaction 例外外，**每个有效的 Message Identity 对应且仅对应一个 Full 消息节点，每个普通 Full 消息节点也只对应一个 Message Identity**；映射不是以物理 `messages` 表行或 `message_id` 为依据。 |
| **复合 Compaction Carrier（唯一节点映射例外）** | 当**同一条具备一个 Message Identity 的复合消息**同时承载 Compaction handoff／boundary 与应保留的真实用户消息内容时，Full 可从它投影出**两个相邻、不同语义的消息节点**：Compaction 节点和用户消息节点。两者仍引用**同一个原始 Message Identity**，以投影种类区分，**不创造第二个 UID／Message Identity**。若不存在可保留的真实用户消息部分，则无须双投影。 |
| **Noting Anchor / Notebook Snapshot annotation** | Anchor 以既有 Message Identity 锚定到 Full 的对应普通消息节点；Snapshot 和 Noting provenance 按 V1 规则附着并可审计。二者**不是**替代消息身份的新 Message Node，也不改变 Full 的消息节点映射。 |

**结构不变量：** Full 的第一个节点必须是 Prelude，之后必须是 Message Nodes；普通 Message Nodes 与规范 **Message Identity 一一对应**，不与物理 Messages／`message_id` 一一对应。**只有复合 Compaction Carrier 双投影是允许同一 Message Identity 对应两个 Message Nodes 的特例**。重复持久化行、压缩续接复制或 Branch 来源引用均不得无故生成第二个普通 Full 节点。

### 1.4 先回退未经授权的 Prompt 修改

首轮自主实验擅自引入的 `agent/system_prompt.py::SECRETARY_GUIDANCE` 把 History Search、Notebook 与 Persistence 审批混写，并以 `session_history` 是否可用触发整段指导。**该改动没有经过对应的语义论证与权威规格授权，必须先精确回退，再按 §3 和附录 A 重建。**

回退只针对该次未经授权的增量，包括引用与注入判断；不得回退 Hermes 原生 `stable/context/volatile` 拼接、其他已授权的 Secretary 功能或无关上游改动。以当前 Git 代码和首轮冻结提交比对定位具体 diff，保留可审计记录；不得因“即将重写”而跳过回退核查。

### 1.5 禁止性扩张

不得新增 Secretary 独立 Agent Cache Manager、第二套 Prompt Builder、统一缓存失效框架、第二套历史数据库／索引、Cron 执行框架、Notebook 专属审批 UI、MCP Hub、Personal Character 或外部 NM 集成。未经本次确认的固定三工具 MCP 桥接方案不纳入强制目标。仅在已有 Hermes 主代码中作必要的窄接线。

---

## 2. Foreground、Conversation History 与 History Search

### 2.1 原生身份基础（继承 M02）

`Conversation Ref`、`Message Identity = (conversation_ref, message_uid)`、compression continuation、branch/fork、rewind/edit、Anchor 归属与 Session route resolver 均沿用 V1-02 §1、§2.6–§2.7。**物理 Session 不等于逻辑 Conversation**；历史、Notebook 与 Schedule 不得以当前 Session ID 冒充长期 owner。所有三类 Foreground 必须遵循同一有效 Conversation 路径和身份判定。

### 2.2 用户主会话资格与 History Search 默认可用性（修订 M03、M08）

**合格 Main Agent**：直接承接用户真实对话的 Main Conversation 执行者；资格应通过 Hermes 真实 runtime ownership／入口判定，而不是仅凭工具列表或是否存在某个 `session_id` 猜测。

- 所有合格 Main Agent **默认拥有** `session_history` Tool Schema 与 `HISTORY_SEARCH_GUIDANCE`，不可由普通 Agent 模板、工具集配置或 `noting.enabled` 移除；不另设 Secretary 可配置开关。
- 普通 Subagent、Background Agent、Cron、Dreaming、Skill refinement 等**不因 V1.5 新增**任何 History Guidance 或 Notebook Guidance、`notebook_show` 等主会话能力，也不因主会话开关切换重建其 Prompt／工具面。不得把其已有合法工具配置无关地重写。
- **专用 Noting Worker 例外仅在 V1 既有维护职责内**：继续按V1-02 §5.7使用已获授权的父Conversation历史读取工具和受限分发；不把自己认定为新的用户主Conversation，不获得新的独立主会话注入资格。完整冻结Parent root、原工具列表/Schema、到Anchor消息在每次请求、工具循环及continuation始终保留；Noting当前可用History/Notebook工具列表和完整Schema只追加在task及后续新增系统提示/控制消息中并声明以此为准，特殊profile另含compact_parent。实际dispatch受白名单限制；冻结前缀不构成新的主会话授权，不改写其头部。
- `session_search` 仍负责**不同 Conversation** 之间的检索。它与 `session_history` 是两个独立工具，不能互作替代或混用名称。

### 2.3 Active Foreground（修订／精确化 M04）

Active 是**模型本次请求实际收到的活跃上下文**，基于 Hermes 原生 provider-neutral request/context（有效 root System Prompt、Compaction handoff／摘要、存活 tail、当前消息与请求期注入），而非数据库按历史行拼接的近似版。当前 tool schemas 与请求上下文是执行态事实，不要求另建持久状态。

用于请求重现、Noting Parent prefix 冻结及缓存一致性诊断。继承 V1 Noting 对 Parent 实际运行前缀的 freeze 约束，不通过重新扫描全部 history 伪造 Active。

### 2.4 History Foreground（扩展／精确化 M05）

History 是沿**当前有效 Conversation 路径**整理的真实消息事件流，可供 `session_history` 检索与阅读：

- 包含真实 User、Assistant、Tool，以及真实存在且属于 Conversation 消息流的 System 事件（如有）；消息原文、时间、角色和 canonical identity 以真实持久来源为准。
- 跨 in-place／rotating Compaction 继续到已归档原始消息，包含 V1 规定的合法 compacted source rows；按 `message_uid`／身份去重。
- 排除 rewind/edit/undo 失效路径；剔除**作为上下文构造物而非真实会话消息**的 root System Prompt、Compaction scaffold、临时衔接指令和 Full 审计标注。
- 不以 Notebook 快照、模型总结或派生文本替代实际原文；历史的事实权威性高于 Notebook。

若 Hermes 某种 source 事件本来就不持久化，不得为使 History 看似齐全而杜撰记录。`History Foreground` 不直接提供跨 Conversation 搜索。

### 2.5 Full Foreground（实质修订 M06、M25）

Full 是当前 Conversation 的**完整可审计有序结构**，规范节点形态为：

```text
Full Foreground
├── [0] Context Prelude                    # 唯一首节点；无 Message Identity
├── [1] Message Node                     # 对应一个 Message Identity
├── [2] Message Node                     # 对应下一个 Message Identity
└── ...                                  # 复合 Compaction Carrier 特例见下文
```

它由以下两类节点构成：

1. **Context Prelude（首节点）：** 当前可确证的**最新有效 root System Prompt**与**当前有效 Tool Schemas／工具面**。应读取 Hermes 真实的当前／已持久化执行来源（含必要的恢复路径），不是根据配置猜测或重新生成一个“看起来相同”的版本。Prelude 反映最新有效值，**不维护历史每一版 Prompt／工具 Schema 时间序列**；Prelude 不具有 Message Identity。
2. **Conversation Message Nodes（其余节点）：** 沿当前有效 Conversation 路径，按逻辑顺序投影的真实 Message，包含属于消息内容的 Compaction boundary／handoff、普通消息以及与相应消息关联的 Noting Anchor、Notebook Snapshot 审计注释。**普通节点与 `Message Identity = (conversation_ref, message_uid)` 一一对应**，不得以物理 `message_id` 建立一一对应关系。

**唯一映射特例：** 若一条复合 Compaction Carrier 同时包含 Compaction handoff 和可保留的真实用户输入，则由**同一个 Message Identity**生成两个相邻的 Full 消息节点（Compaction 投影与真实用户消息投影）。二者须可按投影类型区分，保留同一来源身份，不重复创造逻辑 Message 或 provenance。该特例之外，相同 Message Identity 在当前有效路径中**不得**产生第二个普通节点。Anchor 和 Snapshot 为消息节点的关联审计数据，并非额外的独立消息节点。

关键边界：

- Full ≠ Active：Full 负责历史／状态审计，不声称等于本次 API 请求。Full ≠ History：Full 额外保留 Compaction 和 Notebook 审计信息，不作为 `session_history` 的检索源。
- root Prompt 与 Tool Schema 放在**同一个最新有效 Context Prelude** 语义层，不夹成伪造的 User/Assistant 消息；展示或 API 投影应明确其来源和捕获／有效性。
- **Pre-message Context 是运行时请求前置上下文的构建边界，Context Prelude 是 Full 中对其有效 Prompt／Tool Surface 的最新审计投影**；二者不可混同，也不可将 Prompt 的 `context` tier 当作任一术语的同义词。
- V1 首轮 Verification 指出的 root System Prompt provenance 缺口必须通过原生实际来源关闭，同时补全 Tool Schema 审计；若无法可靠获取，应明确记录缺失及原因，不输出推测值。
- Compaction、Resume、Cold/Warm、Branch、Rewind/Edit 下，事件和 Prelude 必须指向该 Conversation **当前有效路径与当前有效执行状态**，不得混入旧分支或已失效内容。仅审计当前有效 Prompt/Tools，不另外建立 Snapshot 版本史或通用审计存储层。
- Full 的构建／读取本身不触发 Noting、Schedule 或新 Turn；沿用 V1 Anchor／Snapshot 原子性和有效性检查。

### 2.6 `session_history` 契约与来源检索（继承＋修订 M07）

保留现有 `session_history` read-only 操作及已有参数兼容性：`search` 的 keyword／regex、角色过滤、界限，`read` 的定位与前后文、时间范围，返回原始 `content`、`role`、`timestamp`、物理 `message_id` 与 canonical `message_identity`／`message_uid`。对真实存在的 Conversation 内 `role=system` 消息，必须允许查询／读取，并在已有 `roles` 枚举中最小兼容扩展 `system`；这不授权读取 root System Prompt 或 Full Prelude。由 Runtime 注入 owner；模型不能自行选择其他 Conversation Ref。

为 §6 的自主回溯流程，必须确保 Candidate 的 `(conversation_ref, message_uid)` 可以**可靠定位到该条历史原文**，并允许模型继续搜索邻近及其他相关消息。若现有按 `message_id` 读取的参数不足，应在**同一现有工具**上作最小兼容性扩展或提供既有稳定解析路径；不得让 Slash 代搜、拼贴原文来掩盖定位缺口。明确测试来源缺失、路径无效、错误 identity、跨压缩重复、后续推翻证据的情况。

`HISTORY_SEARCH_GUIDANCE` 使用附录 A.1 的**精确两句英文定稿**，按 §3 的 Stable 注入机制处理。

---

## 3. Main Agent System Prompt 与 Tool Surface

### 3.1 注入资格与两个独立能力组（M03、M08、M11）

| Runtime／条件 | `session_history` + History Guidance | `notebook_show` + Secretary Work and Notebook Guidance |
|---|---|---|
| 用户 Main，`noting.enabled=true` | **必须存在** | **必须存在** |
| 用户 Main，`noting.enabled=false` | **必须存在** | **必须缺席** |
| 用户 Main，global=true，局部 `/noting off` | **必须存在** | **必须存在**（Notebook 继续只读） |
| Cron／Dreaming／普通 Subagent／后台辅助 Runtime | **不作新的主会话注入** | **不得因该配置暴露** |
| 专用 Noting Worker | **保持 V1 的受限父对话读取契约** | **保持 V1 的 Noting 专用工具／dispatch 契约，不独立应用主会话门禁** |

`noting.enabled` 只控制第二组主会话 Prompt＋工具暴露以及 V1 已有后台全局门禁，不控制 History Search。Conversation-local `/noting on|off` 只控制 V1 后台任务／Schedule 参与，**不改变两组主工具 Schema、Stable Prompt 或缓存生命周期**。

### 3.2 Stable 模块与原生结构（M08、M19）

在 Hermes `build_system_prompt_parts` 的 **stable** tier，保留原始 Identity、Help、行为指导、Skills 与 Coding posture 组织。增加**两个彼此独立的模块**：

- `HISTORY_SEARCH_GUIDANCE`：所有合格用户 Main；两句定稿见附录 A.1。说明本 Conversation 跨 Compaction 原文检索，以及与 `session_search` 的跨对话优先级。
- `SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE`：仅合格用户 Main **且全局 `noting.enabled=true`**；英文定稿见附录 A.2。Notebook 四区十类型仅心智模型说明，不重写其数据字段规格。

两者与各自工具 Schema 的资格条件绑定。不得以“`session_history` 可用”作为 Notebook Guidance 的注入条件，也不得在 `session_search` 的原生 Guidance 上直接改写一段混合说明。删除未经授权的 `SECRETARY_GUIDANCE`，不得重复注入。附录文本是实施内容，不得因措辞重构自行新增任务权限。

### 3.3 Tool Schema 的绑定与隔离（M07、M11）

- Main History 工具统一复用现有 `session_history` Schema／handler；主会话默认暴露不能因用户选择 toolsets／模板或已恢复的陈旧 pinned tools 而意外消失。
- Main Notebook 工具只暴露**只读** `notebook_show`，返回 current Snapshot 完整结构化 JSON；不向主 Agent 提供 `notebook_mutate` 或 Schedule Mutation 权限。
- 启用、禁用时必须同时调整**向模型发送的 Tool Schemas**、`valid_tool_names`、真实 dispatch 权限，不得只删视觉列表或只改变 Prompt 文本。
- 原生工具注入／工具列表排序尽可能稳定；在未切换全局状态时，不因每 Turn 的 Secretary gate 制造无意义 schema 字节变化。

### 3.4 全局配置切换的立即生效边界（M20）

用户修改 `noting.enabled` 后，**下一次合格 Main Conversation 的 Pre-message Context 构建**必须读取最新有效配置并使两项 Notebook 相关内容同步生效：

1. stable tier 中 Notebook Guidance 有／无；
2. provider request 中 `notebook_show` Tool Schema 有／无，dispatch 与之匹配。

**不等 Compaction、不要求新建或重开 Conversation、不等待 Gateway cache 自然过期。** 对已经发给模型、正在进行的请求不倒灌变更。修改全局配置视为用户主动接受此次失去 Prompt Prefix Cache 命中的成本，**一致性优先**。

Conversation-local `/noting on|off` 仅写入当前 Conversation 的后台参与状态，并产生正常持久化的用户可见、模型可见 Slash 反馈；不得使 Main Prompt／Tool Schema 重建、Agent 重建或缓存失效。

### 3.5 原生 Prompt Cache、Warm 与 Cold（M20）

复用 Hermes 原生 Gateway Agent cache／配置签名、Session Prompt 持久化／恢复、Prompt invalidation 与工具刷新机制，不另建 Secretary cache manager。

必须在**捕获本 Turn 使用的 `active_system_prompt` 和最终 Tool Schemas 之前**完成门禁／配置一致性决策。现有代码若先读取 cached Prompt 再调用 Secretary Tool gate，实施时必须改正顺序：绝不允许“一边旧 Stable 指导，一边新 Tool Schema”进入模型请求。

对于 Warm Agent，旧 Prompt cache 和旧 Tool Schema 都必须被同步更新；对于 Cold Resume，不能因 persisted root Prompt、pinned tools、静态 prefix 重建而恢复已被全局设置撤销的 Notebook 能力。尽可能沿用 Hermes 既有 signature/config epoch 路径；若 `noting.enabled` 尚未计入相关原生配置缓存失效判定，作最小必要接线。

三层 Prompt 的其它正常行为不变：**stable/context/volatile 是有序前缀分层，不是每 Turn 各自定时刷新**；仅在约定重建边界更新，不因为局部 Slash 触发自造刷新。System Prompt 的当前有效值须与 §2.5 的 Full Prelude 可审计来源保持一致。

---

## 4. Notebook、Slash 与 Background Noting 的最小调整

### 4.1 Notebook 语义模型：**V1 原样继承**（M09、M10）

四区十类型**完全不变**：

```text
user           → user_commitment, user_reminder
assistant      → agent_task, watchpoint
consultation   → decision, open_question, formulating_insight
persistence    → memory_candidate, rule_candidate, skill_candidate
```

字段、required/optional、状态转移、Archive/Restore、来源 identity、不可变完整 Snapshot、原子 pointer、Schedule 允许附着的类型以及 Rewind/Branch 重绑等，**全部直接适用 V1-02 §2.5–§2.7、§3.1–§3.4**。本章不得借 1.5 重新设计模型，也不新增第十一种类型或 Candidate 的状态图。

### 4.2 Slash 命令修订（M12）

- `/notebook`：仅进行**人类可读的 current Notebook 查看**，显示 Snapshot 创建时间；pointer 为空明确报告；不展示 Anchor／Pointer ID。仍按 Hermes 正常 Slash 历史／可见性机制持久化，**用户和模型均能看到**。
- `/noting on`、`/noting off`：取代旧 `/notebook on|off`，仅持久化该 Conversation 的**后台 Noting 参与**布尔值，通过 Hermes 原生 Slash 通道输出简短、用户可见／模型可见的 enable/disable 反馈。不另建特殊消息 role、display_kind 或“仅 UI 可见”的旁路。
- 局部 `/noting off` **不禁止** `/notebook`、`notebook_show` 读取最后有效 Snapshot（前提 global=true），也不删除 Snapshot／Schedule intent／审计记录。
- `noting.enabled=false` 时既有 global-level Noting 服务入口关闭语义按 V1 有效约束处理；切换前已持久化的局部偏好不得丢失。不得把旧命令保留为未经批准的新别名。

### 4.3 局部开关只控制 Background Noting（M11–M13）

继续使用 V1 的 `effective_noting_enabled = global noting.enabled AND conversation-local noting_enabled` 决定 Idle／Force Noting、专用 child、Notebook mutations、Schedule due 和 Reminder 产生／投递的后台行为。局部 off 不改变主会话工具或 Stable 指导。

V1 的两种 Trigger、Force 公式／阈值、同 Anchor 准入、`NOTING`／`NOTING_WITH_COMPACTION`、原生 Compaction 交互、Commit gate、process-lifetime child 及权限白名单继续有效，不因 1.5 重写。

### 4.4 Noting Task 指导：**只增必要句子**（M14、M15）

保留现有`secretary/noting_child.py::DEFAULT_NOTING_TASK_INSTRUCTION`的结构、`NOTING_WITH_COMPACTION`约定、原始消息与`/notebook` rendering的区别；**不得整体替换或重新设计驱动Prompt**。对Candidate与Schedule语义只追加以下两句（合适地接入原英文段落）；另按C06/C11在`<noting-task>`及后续新增的系统提示/控制消息中重新给出当前可用History/Notebook工具列表和完整Schema（特殊profile另含compact_parent），明确“以此工具列表和Schema为准，取代此前工具可用性说明”。完整冻结父快照前缀包括root、原工具列表/Schema、到Anchor的消息，始终原样携带；不得在首请求或后续请求改写头部tools/schema。实际dispatch独立限制Noting白名单。模型继承、API/provider直接使用Hermes原生；中间层只保证上下文复用，不新增独立路由或provider改造。原“首次响应后扩顶层工具”的使用顺序不能覆盖这一纠偏契约：

> Keep Persistence Candidates aligned with developments in the Parent Conversation: create or revise them as needed, and archive candidates once their persistence actions are confirmed completed, or the user has rejected or withdrawn them; a proposal or approval alone is not completion.

> Notebook Schedules belong only to the Parent Conversation and deliver in-Conversation reminders; they are not Hermes Cron jobs or delegated agent tasks.

第一句要求 Noting 随父 Conversation 的**实际进展**维护 Candidate，结案采用既有 `archive` 语义而不是物理删除。未确认执行成功、未明确拒绝或撤回的候选不得因“已经讨论过”而归档。第二句只补必要的 Schedule 边界，不重复五种时间表达式（由 §5.2 的 Tool Schema 承担）。

主 Agent **没有** Notebook mutation 能力；Noting Worker **没有** Memory／Rule／Skill 外部持久化权限。两者原 V1 权限隔离保持不变。

**完整生命周期的强制澄清（C13，与V1-02 §5.5/§5.11/§6.16一致）：**

- **目的与冻结源：** Noting通过在父请求的冻结前缀之后追加自身内容来复用热缓存。在准入时冻结父会话实际有效的root、原工具列表/完整Schema及顺序、截至Anchor的Active消息；不是数据库History拼接，也不是后续父会话的最新版本。
- **每次请求不变量：** 首请求、每次工具循环、重试、同child continuation均为“同一份完整父前缀＋累积Noting后缀”。首个工具响应、父会话新Turn/压缩、全局配置变化均不授权刷新已冻结task的前缀。不得以“suffix divergence”为名往头部tools加工具、删工具、改定义或改顺序。
- **声明与执行分离：** 初始task给出当前完整可用工具列表及完整Schema（名称、描述、参数定义），强调取代此前工具可用性说明；每当追加新的系统提示/任务驱动控制消息时，再给一遍。已追加的声明随后缀保留，不回写此前消息，不重建root。实际执行从task起按Noting白名单限制；冻结父前缀仍列有某工具不等于Noting有权执行它。消息载体沿用V1-02 §5.6。
- **改造边界与证据：** 只在Hermes中间层保证上述上下文复用，模型继承、API/provider与推理沿用原生。接续验证逐次比较实际组装的完整前缀、后缀声明及dispatch负例；不能只验第一请求，更不能把第二次新增头部Schema写成正确测试预期。真实缓存读取另由Hermes自身日志/响应观察，不用字节一致冒充已测命中。

§4.5 D01仍为未定稿的外部Agent runtime问题；本澄清不对其支持范围、缺失快照处置或模型配置作决定。

### 4.5 待论证的规格问题：外部 Agent runtime 的继承边界（未定稿）

**状态：仅记录问题，等待用户重新论证和修订，不属于新增定案契约，不授权实施、配置切换或验收。** 已确认的完整父前缀冻结、后缀工具声明及受限dispatch要求继续有效；不得用本项替代或放宽它们。

**D01：** 当Main由Hermes包装外部Agent runtime执行整个Turn时，Hermes持有的模型配置、root或历史镜像，是否等同于外部Agent实际请求的完整上下文？若外部执行器还加入自有指令、工具定义、内部消息或维护其权威会话，现有Noting的完整父快照与热缓存继承前提是否成立？V1/V1.5原稿没有明确规定这一组合的支持范围和交接契约。不能一概断言所有外部runtime均无内容可继承，也不能把模型名/历史镜像当作完整请求前缀。

用户后续论证需明确：

- 哪些Main运行形态纳入Noting支持范围；完整父快照由谁持有、提供，如何证明它与实际推理前缀一致。
- 只有部分上下文、没有完整快照或无法复用同一缓存时，产品应如何处理；是否接受不同缓存行为，以及用户是否需要显式选择。
- 外部Main场景的模型/执行入口继承应采用什么契约；现有Hermes原生能力是否足够，所需边界是什么。
- 此类边界如何验证，同时保持Main已有运行方式和用户已确认的中间层改造范围。

以上均为**未决问题**，不预设禁用Noting、冷启动、独立模型配置、额外capability failure、App Server桥接或provider改造等答案。Agent不得自行补成定稿或启动这些方案。待用户提供修订后，重新对齐相关01/02/04及接续索引，再确定实施范围；动态交接只在根CLAUDE维护。

---

## 5. Notebook Schedule、Schema 与 Reminder

### 5.1 In-Conversation 边界（M16）

Notebook Schedule 是**仅在所属 Conversation 内送达的提醒机制**，不是跨 Conversation Job，也不是 Hermes Cron 的隔离 Agent 运行任务。Notebook entry 是意图所有者；Registry、due 状态、claim／retry 仍归 Secretary 管理，不能创建 Hermes Cron Job、写 `jobs.json` 或启动 Cron 的独立 Session 来执行任务。

时间表达式解析、时区处理及 next-run 计算**复用 Hermes Cron 已存在的稳定基础函数**；复用语法／计算不意味着复用其执行或路由语义。有效 Schedule 类型只限 `user_commitment`、`user_reminder`、`agent_task`、`watchpoint`；`watchpoint.until` 必须一次性。其余六种 Notebook 类型不得安排 Schedule。

### 5.2 `notebook_mutate` Schedule 时间 Schema（扩展 M17）

对 **Noting Worker** 的 `NOTEBOOK_MUTATE_SCHEMA.parameters.properties.expression` 复制 Hermes 原生 `cronjob_manage.schedule` 的**五类时间表达能力说明**，但使用 Notebook-owned 的称谓与投递语义。不得只写“same as Cron”或“clone Cron schema”；不得复制 Cron 的 `prompt`、`deliver`、`model`、`skills`、`repeat`、`run` 等 Job 控制字段。

精确建议文案见**附录 B**，它须明确：

1. `30m`、`every 2h`、`every hour`：周期性间隔，非一次性；
2. `in 30m`、`in 2h`：延迟一次，优先用于“过 N 分钟提醒”；
3. `every monday 9am`、`weekdays at 9am`、`every day at 9am`：自然语言日／周循环；
4. `0 9 * * *`：Cron 表达式，仅复用时间语法；
5. `2026-11-01T09:00:00`：ISO 绝对时间一次性。

未明确时区的本地时间按 Hermes 的**当前配置时区**解析并正规化；禁止无凭据地使用服务器的隐含时区。既有业务方法继续通过 `parse_schedule()` 及 Notebook intent 校验，不新增另一套解析器。原生 Cron `repeat` 次数限制**未**进入 V1 Notebook Contract，本轮不擅自新增。

### 5.3 Schedule 生命周期与两类 Reminder：V1 继承（M16、M18）

Registry 根据 Notebook semantic mutation 原子注册、更新、取消／禁用 Schedule；局部 off 保留意图、冻结 due 处理，重新启用时一次性提醒至多投递一次，周期性不无限回放。scanner 继续走 Hermes 已有 ticker／housekeeping 的窄复用路径，保持跨重启可靠性与 claim 幂等。

- `user_commitment`、`agent_task`、`watchpoint`：**被动 System Reminder**，到期本身不生成主 Turn；在下一次合格 main LLM request 中按 V1 格式注入。
- `user_reminder`：**主动 User Reminder**，到期通过 Hermes 原生 ingress/admission 尝试在**同一 Conversation** 开始新 Main Turn；若主会话忙碌，在原生 busy gate 转成 pending System Reminder，不另排第二个未来 Turn。
- 继承 V1 的 timestamp wrapper、`role=user` synthetic carrier、ACK-after-success、at-least-once-safe retry、崩溃恢复和原生 Gateway routing；不得借 1.5 重新实现。

---

## 6. Persistence Proposal 与审批闭环

### 6.1 `/propose-persistence` 的职责边界（M21、M22）

该 Slash 在当前合格用户 Main Conversation 中启动**正常主 Turn**，不触发 Noting、不启动独立代理或新的审批 UI。读取 current Notebook 中**未归档**的 `memory_candidate`、`rule_candidate`、`skill_candidate`，给模型传递候选草案、类型、来源 `Message Identity` 以及原 Slash 额外自然语言参数。

**禁止** Slash 自动预读原始 Source Evidence、把源消息原文拼入 Prompt 或预设候选证据就是全貌。当前 V1 代码中 `propose_persistence_command` 的 `source_evidence` 预检索与 payload 拼装必须按此修订；自然语言用户附加要求保留，仍通过原生主 Turn 运行。

### 6.2 主模型自主检索与完整性核查（M22）

主模型从 Candidate 的来源 identity／线索出发，**亲自**用 `session_history` 找回原始来源消息，再自主扩展至相关上下文、关键词、前后讨论、用户后续更正、已执行结果或否定证据。来源 ID 不是完整证据集，Notebook 草案也不是原始事实；不得仅据引用的几条消息直接定论。

检索范围首先是**同一 Conversation**。跨对话的 `session_search` 使用原则按独立 `HISTORY_SEARCH_GUIDANCE`；不能拿跨对话结果代替对本 Conversation 原始证据的必要核查。未能找到可核验来源时，明确标记不确定／不予支持，不虚构证据。

### 6.3 提案、修改、批准与实际执行（M21）

`/propose-persistence` **仅授权形成提案**：基于查实的原始消息提出 Memory、Rule 或 Skill 的适当草案及理由，供用户审查、修改或拒绝。

- **候选不是指令**：Notebook 中出现 Candidate，不意味着可以写 Memory、Rule 或 Skill。
- **修改不等于授权**：用户讨论、补充、纠正或要求重写提案，不等于准许执行持久化。
- **双条件门槛**：必须**先向用户提出持久化提案**，并在其后收到用户对**实际执行**的明确授权，才可通过原有工具在批准范围内写入。一次批准不得扩张为批准其他候选。
- `Noting` 永远不直接写外部长记忆／规则／Skill；实际写入由合格主 Agent 使用已授权的现有能力承担。
- 已执行、拒绝、撤回的候选由后续后台 Noting 按 §4.4 追踪并归档，不由主 Agent 直接修改 Notebook。

本 Slash 的**精确英文驱动消息**见附录 C。其职责与 Stable 模块区分：Stable 只长期声明行为边界；Slash 负责一次提案任务中的完整搜证操作。

---

## 7. 工程实施、回归与最终验收

### 7.1 实施顺序与变更审计

建议按依赖顺序实施，每项记录 `Mxx`、V1 原条款、源码接缝、测试结果：

1. **冻结现状和差异**：确认当前代码提交、V1 首轮报告、现行 Hermes Prompt、工具 registry／Gateway 与 Slash；精确回退首轮未经授权的混合 `SECRETARY_GUIDANCE`（§1.4）。
2. **Foreground + History**：落实 Active/History/Full 的新视图、Context Prelude 最新 root Prompt／Tool Schemas、跨 Compaction source 定位与默认主会话暴露。
3. **Prompt／Tool gating**：加入两个正式 Stable Guidance，完成全局配置在 Pre-message Context 的工具／Prompt 一致性同步，以及 Warm／Cold Resume 缓存刷新。
4. **Slash 和 Noting**：调整 `/notebook`、`/noting on|off`、局部门禁；只补必要的 Noting Task 句子；更新 Persistence 候选归档规则。
5. **Schedule + Proposal**：复制五类时间表达 Schema、修订 `/propose-persistence` 的自主检索工作流；继续使用 V1 Schedule Runtime 和原生 Gateway 投递。
6. **全范围验证**：独立检查、DeepSeek官方Anthropic/deepseek-flash思考模式真实主模型测试、官方Dashboard端到端用户验收，出最终交付记录。

任何修改涉及 V1-01／V1-02 已经失效的文字时，应同步更新**现行有效文档**并标注替代口径；首轮历史 `baseline.txt` 和旧 Verification 不得改写为“当时符合新规格”。

### 7.2 必需测试与不变量矩阵

| 领域 | 必须通过的最小验收场景 | 对照 |
|---|---|---|
| 身份／原 V1 基础 | 普通继续、rotating／in-place Compaction、branch/reset、rewind/edit 下 Conversation Ref 与 Snapshot／Schedule owner 不漂移 | M02、M10 |
| Foreground | Active 基于真实请求；History 真实消息可跨 Compaction，去失效路径；Full 第一个节点为当前有效 Prompt + Tools Prelude，其余普通消息节点与 Message Identity 一一对应，复合 Compaction 双投影为唯一例外；Anchor／Notebook 附着正确 | M04–M06、M25 |
| History 工具 | main global on/off、local off 均有 `session_history` 和专用两句指导；关键词／regex／前后 read 正常；跨 Conversation 不越权；`session_search` 不冒充它 | M07–M08 |
| Agent 隔离 | Cron、Dreaming、普通 Subagent、Background 等全局 on/off 不被注入 main 指导／Notebook 工具；Noting worker 仍保留 V1 狭窄职责与权限 | M03、M11、M14 |
| Prompt／Tool 同步 | false→true、true→false；Cold Resume、Warm cached Agent、Compaction 前后；任何主请求中 Stable 指导与工具 Schema 一致，绝无陈旧 pinned tool 或旧 prompt | M19–M20 |
| 局部 Slash | `/noting off` 不改变 Prompt／Tool Schema、无 cache bust；`/notebook` 可读旧 Snapshot；Slash 反馈用户／模型可见且持久；旧命令不意外生效 | M11–M13 |
| Notebook | 四区十类型、状态图、provenance、archive、Snapshot 原子性与 Noting mutation 白名单沿用 V1 测试；局部 off 不删数据 | M09–M10、M15 |
| Noting | 两 Trigger／Child／Force／Anchor/Compaction 竞争继承原 V1；Candidate 实际完成／拒绝／撤回后归档，只有提议／批准不归档 | M13–M15 |
| Schedule | 五类 expression 解析、bare `30m` recurring vs `in 30m` once、时区、`watchpoint` only once；不产生 Cron Job、不跨 Conversation | M16–M17 |
| Reminder | 被动不启动 Turn；主动 idle 同 Conversation 新 Turn、busy 转被动；ACK、重复到期、防丢、重启、局部 off/on 继承 V1 | M18 |
| Proposal | Slash 不预检索／注入 source 原文；模型按 identity 自主查源并扩展关键词／后续更正；来源缺失 fail honestly；只提案、修改不批准、获批才执行且限批准范围 | M21–M22 |
| Hermes-native 回归 | 非主 Agent 原生行为、Skills、Cron、Gateway、Compaction、Tool Registry 与 native Prompt tiers 无无关退化 | M01、M23–M24 |

不得仅用单元测试的 mock 成功代替 Tool Schema 的**实际 provider request**一致性检查；不得只验证程序返回 OK 就宣称后续真实审批写入已发生。按C08必须从Hermes实际请求/响应日志或抓包核查Noting各次请求的父前缀与provider缓存读取token；字节一致不能替代命中证据，未测部分不得宣称优化。

### 7.3 官方 Dashboard 最终用户验收

沿用**仓库内官方 Dashboard 的最小必要聊天交互／Slash 支持**作为端到端验收 Surface；不另找 UI，也不在本轮开发个人 Web App。应以实际 localhost Gateway + 官方 Dashboard + 真实 Main Agent 完成至少：

1. 建立对话并验证默认 `session_history`；跨一次 Compaction 后找到压缩前原文。
2. 全局 Noting on：看到 Notebook 指导与 `notebook_show`；`/notebook` 人类可读、模型可见；全局 off：两者同步消失而 History Search 仍在；Cold Resume 后一致。
3. `/noting off`：可继续阅读 Notebook，但后台不触发，反馈持久；再次 on 按 V1 恢复。
4. 真正 Noting 产出 Candidate；`/propose-persistence` 自主检索源消息及相关上下文，用户修订意见不触发任何持久化写入；明确批准后才执行已授权项；后续 Noting 归档已结案 Candidate。
5. 测试至少一个当前 Conversation 的 Schedule Reminder，确认其不会跨 Conversation 或派遣独立 Cron Agent；保留 idle/busy 两条提醒通路的证据。
6. 使用 Full Foreground 审计 latest effective root Prompt／Tool Schema 与真实 Snapshot／Anchor；验证 Prelude 是唯一首节点、普通消息节点与 Message Identity 一一对应、复合 Compaction 双投影共用原始身份，且首轮 R015 缺口关闭。

若官方 Dashboard 无法表达已有共享 Slash 的最小验收动作，只作必要的薄兼容补丁；不得引入新的 API hierarchy、UI Framework 或完整 Personal UI 产品化。

### 7.4 Verification、Validation 与 Definition of Done

- 对**V1 全部仍有效**的要求及本文 `M01–M24` 逐项做独立 Verification；旧 101 项审查可作对照但不能替代对更新代码／新规格的复核。
- 必须包含首轮 Full Foreground root Prompt provenance 缺口及其新增工具面验证。独立审查不合格时不得进入“已通过最终验收”的结论。
- 独立 Verification 后进行**真正 Dashboard 用户输入到模型响应**的 Validation；编译成功、单测通过、CLI 冒烟或模拟请求都不等同于用户验收。
- 记录平台实测范围、模型及运行参数、Git commit、缓存行为、失败与限制。macOS 实测不得冒称 Linux/Windows 已验证；Prompt 字节 parity 不等于提供商实际缓存命中率。
- 最终交付至少包含：代码 diff 与 V1/V1.5 归属矩阵、测试／审查证据、Dashboard 验收结果、剩余风险／明确不适用项、现行规范同步记录。只有符合项具备证据，才标记完成。

---

## 附录 A. Stable Guidance 英文定稿（规范性）

### A.1 `HISTORY_SEARCH_GUIDANCE`（默认 Main；不受 Noting 控制）

```text
History Search retrieves original messages within the current Conversation, including across Compaction boundaries.

When recalling earlier information, use `session_history` first unless the user explicitly refers to another Conversation; if the information is not found here, use `session_search` to search across Conversations.
```

注意：此处 `session_search` 指向跨 Conversation 的既有独立工具；并不因此把不存在或被其他原生权限禁止的工具强行注入。若目标 Main 无法使用该工具，不能因文字指引而绕过工具权限。

### A.2 `SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE`（仅 Global Noting on 的 Main）

```text
## Secretary Work and Notebook Guidance

As a long-term personal assistant, you may serve as the user's secretary, maintaining continuity within the same Conversation across many interactions and context compactions.

The Notebook provides structured working state across compaction boundaries, preserving continuity in the user's affairs, ongoing work, shared decisions, and proposals for long-term memory and self-improvement.

The Notebook has four sections:
- **user** (`user_commitment`, `user_reminder`): the user's commitments and requested reminders.
- **assistant** (`agent_task`, `watchpoint`): tasks you have accepted and matters that require future attention.
- **consultation** (`decision`, `open_question`, `formulating_insight`): established decisions, unresolved questions, and developing insights.
- **persistence** (`memory_candidate`, `rule_candidate`, `skill_candidate`): proposals for durable memory, rules, and reusable skills.

The Notebook's Schedule capability provides in-Conversation reminders, delivered exclusively within the owning Conversation. Unlike Hermes Cron jobs, these reminders do not launch independent agents or execute autonomous tasks; they bring due matters back to the main Conversation for attention and follow-up.

Background Noting maintains the Notebook asynchronously after interactions become idle or at other defined triggers. Updates may lag behind the latest messages. The Conversation history remains the source of truth. As the main assistant, never maintain or modify the Notebook yourself. Instead, consult `notebook_show` when relevant and carry out your work using the Notebook, the user's latest instructions, and delivered reminders.

Persistence Candidates are only potential proposals recorded in the Notebook, not authorization to act. Never write them to Memory, Rules, or Skills without authorization. Persistence is permitted only after a proposal has been presented to the user and the user has explicitly authorized its execution.
```

此模块只定义稳定工作心智模型。审查候选时的自主搜证细节只放在附录 C 的 Slash 任务消息内，不混回 Stable。

---

## 附录 B. Notebook Schedule Tool Schema 时间字段（规范性）

只替换／扩写现有 `NOTEBOOK_MUTATE_SCHEMA.parameters.properties.expression`，**不引入 Cron Job schema 的其它字段**：

```python
"expression": {
    "type": "string",
    "description": (
        "Required for schedule_create and schedule_update. "
        "Time expression forms: "
        "(1) recurring interval — '30m', 'every 2h', 'every hour' "
        "(repeats indefinitely until cancelled); "
        "(2) explicit one-shot delay — 'in 30m', 'in 2h' "
        "(fires ONCE; use this for reminders after a duration, not a bare duration); "
        "(3) natural day/time — 'every monday 9am', 'weekdays at 9am', "
        "'every day at 9am' (recurring weekly/daily); "
        "(4) cron syntax — '0 9 * * *' (daily at 9am); "
        "(5) absolute one-shot — ISO timestamp '2026-11-01T09:00:00'. "
        "A bare duration like '30m' means recurring, while 'in 30m' means one-shot. "
        "Times without an explicit timezone use the configured Hermes timezone. "
        "This expression defines an in-Conversation Notebook reminder, "
        "NOT an independent Hermes Cron job."
    ),
},
```

---

## 附录 C. `/propose-persistence` 主模型指令英文定稿（规范性）

```text
Review the current Conversation's pending Notebook Persistence Candidates.

Treat the candidates and their Source Message Identities as leads, not authoritative or complete evidence. Use `session_history` to retrieve their original source messages, then independently examine the surrounding Conversation context. Do not assume the cited messages tell the whole story. Search further by relevant keywords, related discussions, later corrections, decisions, or outcomes whenever needed to establish a complete and accurate understanding.

Based on the verified Conversation history, prepare appropriate Memory, Rule, or Skill persistence proposals. Reconcile contradictions, identify outdated or unsupported candidates, and explain the evidence and rationale behind each proposal. Do not invent missing context.

This command authorizes proposals only. Present them for the user's review, revision, or approval. Do not write Memory, Rules, or Skills based on these proposals without explicit user authorization to perform the actual persistence actions. Requests to revise, refine, or discuss a proposal are not approval to execute it. Once explicitly approved, carry out only the authorized persistence actions using existing capabilities.
```

该消息作为原生 Slash 重写的主 Turn 指令；不得预先拼接 Source Evidence，也不得创建审批专用消息通道。工具及其它权限仍以实际 Main Runtime 为准。

---

## 最终裁决与不变量

1. **V1 无改动的语义继续有效**；尤其 Notebook 四区十类型、Conversation Identity、Snapshot、Trigger、Noting Child、Schedule Registry 与 Reminder 机制不得被 1.5 顺手重做。
2. **History Search 默认 Main 常开且不受 Noting 控制**；其 Stable Guidance 与 `session_history` 是一组独立的同步注入。
3. **Notebook Guidance 与 `notebook_show` 全局绑定**；只有用户 Main + `noting.enabled=true` 具备该组能力；局部 off 只停后台维护。
4. **全局切换在下一 Pre-message Context 生效**；允许缓存损失，不允许 Prompt/Tool 不一致。
5. **Notebook 只读 Main、后台 Noting 专属维护**；Prompt、Tool、Slash、Reminder 均不得越权。
6. **Schedule 严格 in-Conversation**；只借 Hermes Cron 的时间表达基础，不借其独立 Agent 执行机制。
7. **Persistence Candidate 是潜在候选，不是授权**；仅在正式提案后收到用户明确执行批准，才允许写入。Slash 自主深查原始证据，Noting 按真实进展归档结案项。
8. **未经规格授权的首轮 Prompt 改动先回退**；本文件、同步后的现行 V1 规范和可复核实施证据共同作为最终验收依据。
