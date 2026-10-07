# 首轮自主实现：当前阶段与任务同步

## 当前目标与阶段

截至 2026-10-07，**Ask and Align、文档基线冻结与实施规划已完成；首批 T1/T2A/T3A 实现已交回并全部经主会话 review 接收，后续任务按依赖序列继续派遣，整体目标未完成**。Codex 主会话因额度耗尽中断后，用户于当日晚将本轮托管给 Kimi 主会话继续自主执行（不再暂停；停止判定与交付按套件执行）；后续实现子 Agent 显式使用 kimi-code/kimi-for-coding。目标仍是在 `main` 完成现行 01 / 02 定义的公开 Hermes Secretary V1 完整链路，并少量调优通用 System Prompt。

两任主会话均已完整阅读根 `AGENTS.md`、`README.md`、现行 01 / 02（02 共 1,978 行）及自主套件全部七份技能。三份核心文档与本轮索引已一并提交为冻结基线 `5346cd094b6a1bb6c6d9ce69e83b3a1570cf46bd`，完整哈希存本轮 `baseline.txt`；实施计划见本轮 `plan.md`。

本轮编号为 `20261007-v1-first-implementation`。会话确认口径的权威入口为 [.autonomous/20261007-v1-first-implementation/index.md](.autonomous/20261007-v1-first-implementation/index.md)，按用户指定命名，承担自主套件的 Snapshot Index 职责；02 本轮保持原文不变。

稳定项目事实与入口见 `README.md`；通用规则与协作约束见 `AGENTS.md`。本文件只维护本轮动态状态，不保留已结束的建仓流水账。

## 本轮范围与完成目标

| 能力面 | 本轮目标 | 主要依据 |
|---|---|---|
| Conversation Identity | durable opaque Conversation Ref、可信 alias reconciliation、压缩延续保持身份、branch/reset 隔离、冲突与路由 ownership fail closed | 02 §1、§6.2–6.3、§6.13 |
| Foreground / History Search | 区分 Active / History / Full Foreground；跨压缩读取真实有效历史，排除 rewrite superseded 路径；主会话与 Noting 复用同一 search/read 能力，独立于 Noting 开关 | 02 §2.1–2.4、§6.4、§6.14 |
| Notebook | 四区十类型、完整 immutable Snapshot、原子 current pointer、Noting-only semantic mutation、主 Assistant 只读、人类 Notebook slash 控制与查看、rewind/edit/branch reconciliation | 02 §2.5–2.7、§3.1–3.7、§6.11、§6.18 |
| Noting | 两层 enable gate、Idle / Force、规定阈值公式、DB-backed same-Anchor admission、不同 Anchor 可并发、persistent one-shot child、Parent cache parity、两种 profile、受限 dispatch、commit-time Anchor validation | 02 §4–5、§6.6–6.7、§6.15–6.16 |
| Schedule / Reminder | Notebook-owned durable registry、due claim 与重启恢复、被动 Reminder request-time 注入与成功响应 ACK、主动 Reminder 复用 Gateway admission、busy 转被动提醒 | 02 §3.8–3.12、§6.8–6.10、§6.17 |
| 时间标记、回退与正式接线 | source-event timestamp、三种完整 `role=user` wrapper；关闭 Noting 的原生回退；身份、权限、并发、失败与重启路径证据；Slash 命令及必要的既有入口接线 | 02 §4.3、§5.6、§6，加本轮 Frontend / API 排除口径及索引 A24 的有限补充 |
| Persistence 提议 Slash 命令 | `/propose-persistence` 无结构化参数，可跟普通 user message；主 Assistant 核对当前 Notebook persistence 候选与原文依据，只输出提议；后续自然语言批准 / 修改 / 否决，没有批准 UI | 本轮索引 A06–A07、A14–A15、A17、A19；补充 02 §2.5 |
| 通用 System Prompt 调优 | 主会话自行选择少量通用文本调优，不引入额外机制 | 本轮用户明确授权，作为 02 之外的补充范围 |
| E2E 验收入口 | 前端、后端在本机 localhost 运行；官方 Dashboard Web UI 目标为零专属补丁，通过共享 Slash 链路自然提供命令；仅查证 consumer 缺口后补薄兼容层。Codex 内置浏览器验收，Personal UI 与产品化 API 留第二轮 | 本轮索引 A24–A26；macOS 实测边界按 A20 |

完成定义：上述能力通过真实正式入口形成可用闭环，满足 01 的 Definition of Done 与 02 的适用条款；独立 Verification、Validation 均关闭范围内缺陷与必要证据缺口，由主会话核验并交付。Helper、阶段提交或局部测试通过不等于整轮完成。

## 口径收敛状态

- 本轮范围按上表和 01 / 02 查阅；少量 Prompt 调优授权、Frontend / API 排除范围、Persistence 提议与自然语言批准边界见索引 A02、A05–A07。Development 精确阅读分派及提问、文档冻结规则归根 `AGENTS.md`，不再混入产品口径问答表。
- 02 原文不变；索引补充与收敛本轮适用口径，不再安排“同步修改 02”。旧稿和仓库外 03 不作为本轮依据。
- 已冻结通用规则继续按根 `AGENTS.md` 执行；后续确认口径写索引，本文件只维护任务状态与必要摘要。
- 主会话错误提出的“按 Anchor 新旧淘汰迟到任务结果”方案已撤回，不作为实施要求；索引仅保留用户明确澄清的 pointer 口径 A10。
- 用户已澄清 pointer 的选择依据，见索引 A10：按当前 Full Foreground 的最新有效 Snapshot Anchor 选择，不按完成 / 提交时间；较早 Anchor 的迟到合法 Snapshot 可以提交，但不能使 current 倒退。该口径需纳入 persistence 实现、rewind reconciliation 与并发验收。
- 真实模型验收选择已确认，见索引 A11–A12：本机 Codex Proxy、GPT6 Luna、High，仅用于必要实际测试，Hermes 不参与编码。用户要求准确模型 ID 与 Proxy 接线到实际配置时再核实；尚未调查或写入运行配置。
- `propose persistence` 的 global-on / local-off 行为已确认，见索引 A14：仍可提议已有候选，不触发或重启 Noting，缺少 Snapshot / 候选时明确提示。
- global-off 行为已确认，见索引 A15：全局 `noting.enabled=false` 时，`propose persistence` 不可用。
- 旧 Background Self-Improvement Review 开关明确删除，见索引 A16：同步清理其独立启用通路与对应设置 / 帮助入口，Noting 关闭不恢复旧 Review；保留并抽取 02 要求复用的 cache-parity helper。
- Slash 正式拼写已确定为 `/propose-persistence`，见索引 A17。
- 命令调用形式已确认，见 A19：无结构化参数的普通 Prompt-trigger Slash，可在命令后跟自然语言 user message；正式接线复用既有主 Conversation 路径。
- 平台验收边界已确认，见 A20：本机 macOS 实测，Linux / Windows 如实记录未验证范围，保留既有跨平台实现约束。
- 验收入口与方法已确认，见 A24–A25：官方 Dashboard Web UI 最小专属改造作为首轮 E2E acceptance surface，通过 Codex 内置浏览器操作，不使用 Computer Use；Personal UI 选择和产品化留到第二轮。A05 的 Frontend 排除范围据此有限补充，具体必要接线经调查后纳入计划。
- 最终云端运行、通过 Web UI 使用属于用户此前已确定的部署口径；开发测试期间前端、后端均在本机 localhost 运行，内置浏览器访问本地 Web UI。两者已分别写入根 `README.md` 的架构与开发环境说明，不把最终部署形态当开发测试环境要求。
- 旧 Review 清理范围进一步确认，见 A22：删除 `/refine` 及其旧 Review 接线，保留另一项独立工作审查功能 `/review`。
- Force 固定边界单位已确认，见 A23：K＝1,000 tokens，三个整数分别为 64,000 / 66,000 / 128,000；公式与两种 capability failure 原样遵循 02。
- 两轮边界进一步明确，见 A26：首轮 Core correctness＋shared slash surface＋官方 Dashboard E2E；优先零 Dashboard-specific patch，仅有实际 consumer 缺口时补兼容层。结构化 Notebook / Snapshot / Noting / Full Foreground / Schedule API 及产品面板留第二轮。

## 后续接线调查与环境工作

当前没有影响冻结的待确认问题；以下属于实施规划及按用户要求留待后续的环境工作，尚未调查的细节不作为已冻结行为：

| 议题 | 来源 / 影响 | 当前状态 |
|---|---|---|
| 官方 Dashboard Web UI 共享 Slash consumer | A24–A26 已确定本地入口、方法及零补丁目标 | 只读调查完成：现有 send union/completion/rendering可复用；需注册原生命令和TUI pending-input集合，未发现React缺口 |
| 本机 Codex Proxy 与隔离环境接线 | 模型选择与测试用途已确认；须核实准确模型 ID、High 配置及实际入口 | 按用户要求留到实际配置时调查 |

其他问题先查现行文档与实现；只把仍影响产品行为、范围或完成判据的歧义提交用户。每次询问一个关键问题并提供建议，回答后立即更新本轮 `index.md`。本轮口径已收敛，文档基线提交一并纳入三份核心文档与索引。

## 首轮任务看板

| 任务 | 状态 | 完成条件 / 依赖 |
|---|---|---|
| Ask and Align | 已完成 | 四项输入核对完成；用户确认进入下一阶段，无影响冻结的未决问题 |
| Snapshot Index 与冻结基线 | 已完成 | 冻结提交 `5346cd094b6a1bb6c6d9ce69e83b3a1570cf46bd`，三份核心文档与索引同批提交，完整哈希已写 `baseline.txt` |
| 实施计划与精确阅读分派 | 已完成 | 本轮 `plan.md` 记录 R01–R22 覆盖、T1–T8任务、S01–S22场景、接口/依赖/白名单/精确02阅读范围 |
| Identity / Foreground / History foundation | `dev_foundation` 实施中 | 身份边界、真实历史读取与正式工具接线成立 |
| Notebook persistence / semantic control | T2A语义模型与renderer已交回、主会话review接收；T2B未启动 | immutable Snapshot、原子 pointer、权限与 slash、路径变更 reconciliation 尚未实现 |
| Persistence 提议 Slash 命令 | 口径已确认，待实施 | 按索引中的正式拼写、Prompt-trigger、自然语言批准及开关边界接入正式 Slash 路径，不修改 02 |
| Noting Trigger / runtime | T3A纯helper抽取已交回、主会话review接收；runtime未启动 | admission、阈值、child、受限工具与 commit gate 待实现；旧 Background Review 开关与 `/refine` 尚未移除 |
| Schedule / Reminder | 待实施 | due scan、持久状态、request injection / ACK、Gateway busy fallback 成立 |
| 跨模块集成与少量 Prompt 调优 | 待实施 | wrapper、关闭回退、并发与失败路径及 Slash 接线完成；Frontend 范围限于 A24 授权的官方 Dashboard 最小验收改造 |
| 官方 Dashboard Web UI E2E acceptance surface | 入口与方法已确认，待调查与实施 | 共享 Slash 命令自然可用；优先零 Dashboard 补丁，必要才补薄兼容层；本地内置浏览器验收 |
| 独立 Verification | 待启动 | 集成收敛后全新审查者按冻结依据核对机制、正式路径和证据；关闭范围内阻断 |
| 独立 Validation | 待启动 | Verification 通过后，另一全新验收者通过产品入口执行适用用户场景 |
| 主会话交付判定 | 正在整理阶段暂停简报 | `final-delivery.md`记录当前证据、未完成项与恢复条件，不声明整轮完成 |

## 当前编排与风险

- 三项只读接线研究已完成，结论已由主会话核对并纳入计划：Foundation、Noting、Schedule / Reminder / shared Slash / Dashboard。首批三个 Development 已派遣：`dev_foundation`（T1 DB/Foreground/History tool与正式接线），`dev_notebook_model`（T2A仅 `secretary/notebook*` 模型/renderer），`dev_parity`（T3A仅 `agent/cache_parity*` 与原constructor内部）。均为 `gpt-6.1-sol` / `high`、无主会话历史，不派生、不提交、不运行Hermes模型。未建worktree，修改白名单互不相交；返回后主会话review，不提前派独立门禁。
- 三份根核心文档与本轮索引已在冻结提交中一并纳入；后续文档变化为获用户授权的RTK透明使用一句规则、`baseline.txt`、`plan.md`和动态状态。01 / 02 正文和锁文件未改。
- 已查证基线没有02要求的`session_history`模型工具，UI同名module与跨会话`session_search`不等价。T1须新增当前Conversation History Foreground search/read并正式接线。
- 文档基线已冻结；以本轮索引定位补充口径，保持 02 原文不变。官方 Dashboard 验收目标为零专属补丁，规划阶段调查共享 Slash consumer；模型 ID 与隔离环境接线按用户要求在实际配置阶段核实。
- Parity 抽取的实施设计按 02 §5.3：`/btw` 现有调用点与 detached constructor 默认不改；原 constructor 内部调用纯 parity helper，Noting 的独立 persistent constructor 也复用该 helper。不是将原 constructor 加 flags 改成通用工厂；该设计写入计划，不追加为用户问答口径。

| 当前交付范围 | 机制实现 | 正式接线 | 针对性验证 | 用户结果 |
|---|---|---|---|---|
| T1 Identity/Foreground/History | 开发中 | 开发中，待review | 尚未交回 | 未验收 |
| T2A语义模型/renderer | 已实现、主会话review接收 | 纯模型/renderer；DB/runtime/slash未接 | 两文件119通过；最后Schedule边界修改后定向37通过 | 未验收 |
| T3A纯parity抽取 | 已实现、主会话review接收 | 原detached constructor内部复用helper；`/btw`入口未改 | 四文件35通过；补充真实request assembly后定向8通过；Ruff/health通过 | 未验收 |
| T3其余/T4/T5/T6 | 待实施 | 待实施 | 未执行 | 未验收 |

## 起点与验证摘要

- 本轮起点：`main`，提交 `ef1f0e909c7f8b438a2121aa9d9d07b0f7697eb6`；进入对齐前工作区干净。冻结检查基线按 `AGENTS.md` 的官方提交 `d02f211858ab202d6d4d34ea59774591a5f14cbd`。
- 已有环境：官方 PM 工作区 `.venv`，Python 3.14.7，已纳入 `dev` / `test` groups；初始化记录确认官方依赖定义与锁文件未改。测试使用隔离状态及 canonical runner。
- 沿用已有证据：初始化阶段本地保留检查执行一次，10 项通过；GitHub Actions 已关闭。这些证据不证明 Secretary 功能或完整 Python suite 通过。
- 本轮文档基线及计划阶段：01 / 02 原文未改，差异检查通过；计划/RTK授权指导阶段快照 `56d5adee6d057afa35cd5cae99a5f12e66371b2a`，初始冻结哈希保留在 `baseline.txt`。尚未运行完整suite或两个独立门禁。
- T2A：canonical runner两文件119通过（0.9秒）；最后Schedule校验修改后定向一文件37通过（0.5秒）。证据：`.hermes-dev/evidence/t2a/notebook-tests.log`、`schedule-review-tests.log`。主会话阅读实际模型、renderer、测试与日志后接收；仅证明语义和输出边界，不证明持久化或产品闭环。
- T3A：canonical runner四文件35通过（6.4秒）；补充真实request assembly后新测试文件8通过（4.7秒）；独立临时Git index上的Ruff/health三文件通过（0.6秒）。证据：`.hermes-dev/evidence/t3a/parity-tests.log`、`request-parity-tests.log`、`parity-checks.log`。主会话核对helper、原constructor、真实请求与持久化隔离测试后接收；尚无Noting生产runtime。
- 大型检查执行方、版本、范围、次数、耗时与结果待实际执行后记录；当前平台及真实模型覆盖尚未验收，不声明跨平台通过。
