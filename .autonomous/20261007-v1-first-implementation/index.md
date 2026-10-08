# Snapshot Index：20261007-v1-first-implementation

本文件按用户指定命名为 `index.md`，承担自主套件的 Snapshot Index 职责；不另建重复索引。Ask and Align 已完成；冻结文档提交的完整哈希写入同目录 `baseline.txt`。任务看板与动态编排仅在根 `CLAUDE.md` 维护。

## 审查依据索引

| 输入类别 | 实际仓库文件路径或本文件位置 | 修改等级 |
|---|---|---|
| 用户需求 | `docs/01-personal-hermes-v1-first-fork-iteration.md` | 二级 |
| 权威规格 | `docs/02-noting-system-specification.md` | 一级：用户明确要求本轮不再修改 02 |
| 编码指导 | `AGENTS.md` | 二级；已冻结规则不得由 Agent 自行变更 |
| 会话确认口径 | 本文件“口径与决策” | 二级 |

本索引自身为二级；用户明确授权在本索引持续记录本轮收敛口径。一级文件本轮不可修改；二级文件须有用户明确授权才可修改。会话确认口径补充或收敛现行规格的本轮适用范围，必须与相关原文共同阅读；不能因为补充未写进 02 而漏实现或漏审。

## 口径与决策

下表只记录本轮由用户明确确认或授权的产品与验收口径；引用的既有规格仅提供依据，不视为本次问答产生的新要求。通用规则按 `AGENTS.md`、执行状态按 `CLAUDE.md` 查阅。保留已有口径编号，移出的条目不重编号。

| 口径编号 | 用户明确确认或授权的内容 | 依据与适用边界 | 用户消息定位与授权来源 |
|---|---|---|---|
| A02 | 通用 System Prompt 由主会话自行做少量调优，不引入额外机制；该项是 02 之外的补充范围 | 用户明确授权自主选择少量通用文本；不引入个人 Persona / Character、个人规则或新的运行机制 | 2026-10-07 用户“你先看着调优，改一点，但是，不引入额外机制……02文档没有提 system prompt” |
| A05 | 本轮不做 Frontend / API 增量，除 Slash 命令及必要的既有路径接线之外 | 收敛 01 的最小接口工作及 02 §6.19 的 Open 范围：不增加专用 Notebook 面板、新公开 API / RPC / DTO / event contract；仍需正式 Slash 路径可用 | 2026-10-07 用户“本轮不做 front end API……除了 slash 命令之外” |
| A06 | 本轮追加名称为 `propose persistence` 的 Slash 功能，由主 Assistant 读取当前 Notebook 的 persistence 区，核对候选与原文依据，整理 Memory / Rule / Skill 持久化提议供用户审阅；命令本身只 propose，不执行持久化 | 用户确认了主会话提出的完整行为方案；复用 02 §2.5 的三类候选、canonical Message Identity provenance 及主 Assistant 审查原则，Noting 不执行 Memory / Rule / Skill 写入 | 2026-10-07 主会话提出“读取当前 Notebook……核对候选及原文依据……整理……建议……命令本身只提出方案”；用户随后“对，我就是这个意思……就像你说的那样……强调的是，propose persistence” |
| A07 | 提议后的批准、修改或否决由用户后续自然语言控制；没有批准 UI。用户明确批准后，主 Assistant 通过已有能力执行获批的持久化行动 | 命令触发不等于批准；不新增确认按钮、批准面板或独立审批机制；沿用 02 的 explicit user approval 与主 Assistant 只读 Notebook 边界 | 2026-10-07 用户确认上述方案并明确“批准没有一个 UI 交互，后续用户用自然语言控制就行” |
| A10 | current Notebook pointer 由当前 Full Foreground 视图下最新的 Anchor 决定，不按任务完成或 Snapshot 提交时间决定 | 结合 02 §2.7、§3.3–3.4、§4.8、§5.10：选择有效路径上最新 Anchor 对应的已提交 Snapshot；较早 Anchor 仍有效则可提交，但 pointer 不倒退；原子事务、rewind 重选及无有效 Snapshot 时为 null 属于原有规格要求 | 2026-10-07 用户“指针指向谁？……它是由 for foreground 视图下最新的那个 anchor 锚点决定的” |
| A11 | 本轮真实模型验收使用本机 Codex Proxy，GPT6 Luna、High 思考强度；实际配置前核实准确模型 ID | 用户指定 provider / 模型 / 强度；配置调查时机见 `CLAUDE.md`。Parent / Noting 的模型、provider、reasoning parity 仍按 02，不是新问答要求 | 2026-10-07 用户“使用本机 Codex Proxy,GPT6Luna，加 High，思考强度……实际配置的时候，先去看清楚模型ID” |
| A12 | 本机 Codex Proxy / GPT6 Luna 仅用于必要的实际测试；禁止 Hermes 自己参与编码 | Hermes 作为被测产品，不作为代码实现者；实现与测试代码由 Codex 主会话和 Development 子 Agent 完成 | 2026-10-07 用户“只用于必要的实际测试,禁止 Hermes 自己参与编码” |
| A14 | 全局 Noting 开启、当前 Conversation 已 `/notebook off` 时，`propose persistence` 仍可读取已保存的 persistence 候选并生成提议；不触发 Noting，不重新开启它；没有 Snapshot 或候选时明确提示 | 与裸 `/notebook` 的 local-off 已存状态查看原则一致；命令不恢复 main Assistant 的常驻 Notebook 工具权限，不修改 Notebook，批准仍通过后续自然语言 | 2026-10-07 主会话针对 global-on / local-off 提出上述方案，用户明确回复“同意” |
| A15 | 全局 `noting.enabled=false` 时，`propose persistence` 不可用；不能绕过全局开关读取已有候选并启动提议 | 与 02 的 `/notebook` 全局开关一致；与 A14 的 global-on / local-off 场景区分 | 2026-10-07 主会话询问 global-off 可用性，用户明确回复“不可以用” |
| A16 | Hermes Secretary 移除旧 Background Self-Improvement Review 的开关及独立启用入口，旧自动 Review 不再作为可选产品功能存在；不能只设为默认关闭或简单改名。Noting 在产品生态位上完整替代它 | 用户进一步明确 02 §5.1 的 fork-wide 替代边界；清理对应配置定义、实际启用接线及设置 / 帮助入口，防止旧开关继续有效。Noting 全局或局部关闭均不恢复旧 Review。02 §5.2–5.3 要求保留并抽取的纯 cache-parity machinery 继续复用，不能将底层 helper 一并误删。清理旧设置入口不属于新增 Frontend / API 能力 | 2026-10-07 用户“Secretary里面不再设有那个 Background Self Improvement Review 的那个开关，删掉它……Noting机制在生态位上已经彻底替换掉了那个东西” |
| A17 | Persistence 提议 Slash 命令的正式拼写为 `/propose-persistence`，使用短横线连接，采用一个完整命令 token | 用户明确选择短横线形式，替代主会话先前建议的 `/propose persistence`；索引此前的名称 `propose persistence` 均指此功能 | 2026-10-07 用户“中间不能断吧？能用空格吗？还是用短横线连接一下吧？” |
| A19 | `/propose-persistence` 是正常的 Prompt-trigger Slash 命令，无结构化参数；命令后可跟普通自然语言 user message，该消息用于补充本次意图，与特定提议 Prompt 一同进入正常主 Conversation 执行 | 复用既有 Prompt Slash 触发方式，不新增参数筛选子命令、独立工作流或 Agent loop；后续文本不能被误当成结构化参数而拒绝或丢弃。具体候选审查 / 提议行为按 A06，批准仍按 A07 | 2026-10-07 用户“slash命令后边可以跟正常的user message……正常的那种触发……特定prompt用的slash命令。无参数” |
| A20 | 本轮实际验收在当前 macOS 主机执行；Linux / Windows 记录具体未验证范围，不声明已实测通过；实现继续遵守现有跨平台约束 | 用户选择当前主机实测，明确其他平台的证据边界；不通过伪造 OS 冒充平台覆盖 | 2026-10-07 异步提问“本轮实际验收覆盖哪些操作系统？”；用户选择“macOS 实测，其他平台记录未验证范围” |
| A22 | 删除手动触发旧 Memory / Skills Background Review 的 `/refine` 命令及其启用入口；保留独立审查代码 / 文档 / 工作结果的 `/review` | 实际 CLI / Gateway / TUI `/refine` 均调用旧 `_spawn_background_review`，须一并清理，防止绕过 A16 的产品替代边界；`/review` 调用独立 review engine，不属于该旧功能 | 2026-10-07 异步提问附现有路径区分与建议；用户选择“删除 /refine，保留独立审查 /review” |
| A23 | 02 Force 公式中的 K 统一为 1,000 tokens：64K＝64,000，66K＝66,000，128K＝128,000 | 本次只确认单位。原公式、严格比较关系、两种 capability failure、128K 不作为 clamp，以及消费 Hermes 已解析上下文参数均按 02 原有规格执行 | 2026-10-07 异步提问明确单位；用户选择“K＝1,000 tokens” |
| A24 | 第一轮使用官方 Dashboard Web UI，做最小专属改造作为 E2E acceptance surface；Personal UI 的选择和产品化改造推迟到第二轮 | 用户明确 Dashboard 指 Web UI；对 A05 作有限补充，允许验收必需的官方 Web UI 最小改造，具体接线范围经现有实现调查后纳入规划。既有云端运行、Web UI 使用的部署口径见根 `README.md` | 2026-10-07 用户“第一轮用官方 Dashboard 做最小专属改造的 E2E acceptance surface……”；随后澄清“Dashboard指的是那个Web UI……部署形式最终就是云端运行，走Web UI……早就敲定的” |
| A25 | 开发期间前端、后端均在本机 localhost 运行；首轮通过 Codex 内置浏览器访问本地官方 Dashboard Web UI 进行实际验收，不使用 Computer Use | 开发测试与最终云端部署分别处理；按用户指定方式安排独立 Validation，浏览器入口与真实操作证据在实施及验收阶段落实 | 2026-10-07 用户“验收方法，用内置浏览器即可，不需要 Computer Use”；随后明确“那是部署口径，不是……开发……测试口径。开发的时候都在本地local host……不管是前端还是后端” |
| A26 | 第一轮以 Core correctness＋共享 Slash surface＋官方 Dashboard E2E 验收为边界，目标为零 Dashboard-specific patch：新增 Hermes Slash 命令通过现有 catalog、complete.slash、slash.exec / command.dispatch 自然获得补全、执行和文本结果；仅在查证 consumer whitelist / rendering gap 后补薄兼容层 | 不预先改 Web React，不为 UI 提前设计 API，不让未来 Personal UI 反向约束后端架构。Notebook structured / Snapshot history / Noting status-event / Full Foreground audit / Schedule presentation API 与产品面板留第二轮；首轮核心验收仍完整覆盖 01 / 02 及本表补充 | 2026-10-07 用户明确共享 Slash 链路、两种前端补丁情形及两轮边界，并强调“第1种为目标”“第一轮用官方Dashboard做零/最小专属改造的E2E acceptance surface” |
| A27 | 本轮剩余未冻结的规格口径由主会话自行合理收敛，不再逐项请示；每项自主收敛记录依据与理由，最终随交付统一向用户汇报 | 适用于规格未尽善尽美之处的执行层判断；不得变更已冻结一级 / 二级依据的明确要求；自主收敛记录写入 plan.md 取舍节与 final-delivery.md | 2026-10-07 用户“我知道规格肯定不是尽善尽美，剩余口径你自行合理收敛，最后统一向我汇报就行” |
| A28 | 第二批 T2B/T3B/T3C/T4 交回、主会话完成 review 与集中接线后，本轮先暂停；不再继续 T5/T6、独立门禁与后续实现 | 用户明确本轮边界；后续任务与两个独立门禁留待恢复；不改变既有冻结要求与完成定义 | 2026-10-07 用户“本轮subagent返回，你完成验收与接线之后，就先到此为止,不再继续往后” |
| A29 | 恢复首轮完整目标并继续自主实现；先从 Kimi 已提交的基线复核进展，避免重复已委派的任务，必要时更新计划并将具体修复交给子 Agent | 本次授权解除 A28 的暂停边界；原冻结范围、两门禁与完成定义继续有效。恢复审查代码基线为 `2ba9b34193`，保留原始文档冻结基线 | 2026-10-08 用户“继续自主实现……先完成进展复核……不要重复派遣已经由kimi委派过的subagent任务……直接从基线开始审……把具体修复交回给subagent……恢复目标……晚上你自主执行” |
| A30 | 允许必要的真实模型调用测试，使用本机 Codex Proxy / GPT6 Luna | 再次确认 A11–A12 的测试授权；High、配置前核实模型 ID、Hermes 不参与编码的既有约束继续有效 | 2026-10-08 用户“允许真实模型调用做测试，codexproxy，GPT，6Luna” |
| A31 | 继续自主实现，直到完成本轮既定目标 | 额度中断后恢复原 F1/F3/T5 子 Agent；原冻结范围与两个独立门禁继续有效，不重复已交回任务 | 2026-10-08 用户“现在继续自主实现，直到完成本轮既定目标” |

明确排除：除共享 Slash 及经查证必要的 Dashboard 薄兼容补丁之外的 Frontend / API 增量、批准 UI、Personal UI 选型与产品化（A05、A07、A24、A26）；第二轮 API 与面板边界按 A26。其余既有排除范围直接按 01 与根 `AGENTS.md` 查阅，不作为本次新增问答口径。

未决事项：当前没有影响冻结的待确认问题，用户已授权进入下一阶段。验收入口、方法及两轮边界按 A24–A26 确定，平台覆盖按 A20、模型选择与用途按 A11–A12。共享 Slash consumer 调查与实际模型配置时机见 `CLAUDE.md`；调查中出现新的范围或产品歧义按既有对齐规则处理。冻结时按 `AGENTS.md` 将本轮核心文档变更与索引一并提交。
