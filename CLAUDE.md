# 首轮自主实现：当前阶段与任务同步

## 当前目标与阶段

截至 2026-10-08，**用户已按 A29 恢复首轮完整目标；Codex 主会话已从 Kimi 提交的 `2ba9b34193` 完成进展复核，进入增量修复与后续实现。整体目标未完成**。工作区恢复时干净；T1/T2A/T3A 与 T2B/T3B/T3C/T4 的已交回实现和有效证据保留，不重新派遣这些任务。F1/F2/F3/T5 已完整交回并 review 接收，P15 工具面与正式 main 归属证据已关闭；T6 已提交。当前创建全轮集成快照，随后执行一次扩大回归及独立 Verification / Validation。原目标仍是在 `main` 完成现行 01 / 02 定义的公开 Hermes Secretary V1 完整链路，并少量调优通用 System Prompt。

两任主会话均已完整阅读根 `AGENTS.md`、`README.md`、现行 01 / 02（02 共 1,978 行）及自主套件全部七份技能。三份核心文档与本轮索引已一并提交为冻结基线 `5346cd094b6a1bb6c6d9ce69e83b3a1570cf46bd`，完整哈希存本轮 `baseline.txt`；实施计划见本轮 `plan.md`；停止判定简报见本轮 `final-delivery.md`。

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
- 真实模型验收选择已确认，见索引 A11–A12：本机 Codex Proxy、GPT6 Luna、High，仅用于必要实际测试，Hermes 不参与编码。用户要求准确模型 ID 与 Proxy 接线到实际配置时再核实；2026-10-08 开始核实模型 ID 与隔离配置，详见下方环境记录。
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
- 剩余执行层口径授权已确认，见 A27：规格未尽之处由主会话自行合理收敛、逐项记录依据并最终统一汇报；不变更已冻结一级 / 二级依据的明确要求。集成期收敛（取舍 S3）记录于 `plan.md`。
- A28 记录此前第二批交回后的暂停边界；用户已在 2026-10-08 按 A29 明确恢复，继续增量修复、T5/T6 和独立门禁。历史暂停简报保留来源，不能作为当前停止授权。

## 后续接线调查与环境工作

当前没有影响冻结的待确认问题；以下属于实施规划及按用户要求留待后续的环境工作，尚未调查的细节不作为已冻结行为：

| 议题 | 来源 / 影响 | 当前状态 |
|---|---|---|
| 官方 Dashboard Web UI 共享 Slash consumer | A24–A26 已确定本地入口、方法及零补丁目标 | 只读调查完成：现有 send union/completion/rendering可复用；需注册原生命令和TUI pending-input集合，未发现React缺口 |
| 本机 Codex Proxy 与隔离环境接线 | 模型选择、High 与实际测试用途已确认 | `/v1/models` 已核实 `gpt-6-luna-high`；loopback endpoint `http://127.0.0.1:9879/v1`，真实连通请求已成功；隔离验收配置位于 `.hermes-dev/acceptance/config.yaml`，凭据只在忽略路径 |

其他问题先查现行文档与实现；A27 起剩余执行层口径由主会话自行收敛并记录于 plan.md 与 final-delivery.md（批次边界见 A28），仅影响冻结依据解释或范围变更的事项才提交用户。本轮口径已收敛，文档基线提交一并纳入三份核心文档与索引。

## 首轮任务看板

| 任务 | 状态 | 完成条件 / 依赖 |
|---|---|---|
| Ask and Align | 已完成 | 四项输入核对完成；用户确认进入下一阶段，无影响冻结的未决问题 |
| Snapshot Index 与冻结基线 | 已完成 | 冻结提交 `5346cd094b6a1bb6c6d9ce69e83b3a1570cf46bd`，三份核心文档与索引同批提交，完整哈希已写 `baseline.txt` |
| 实施计划与精确阅读分派 | 已完成 | 本轮 `plan.md` 记录 R01–R22 覆盖、任务、S01–S22 场景、接口/依赖/白名单/精确02阅读范围；T2/T3 拆分、接口锁定、A27/A28 与取舍 S1–S3 已补记 |
| Identity / Foreground / History foundation | F1 增量修复已交回、review 接收并接线 | birth、branch/reset、rewrite/pointer、Full audit、raw版本保护与路由ownership已有正式证据；待全轮独立审查 |
| Notebook persistence / semantic control | T2A/T2B 已接收并接线 | immutable Snapshot、原子 pointer（A10）、local 开关、branch 独立 Notebook、rewind 重选、commit reconcile 成立；shared Slash 已由 T5 接线，待 Dashboard 用户结果 |
| Persistence 提议 Slash 命令 | T5 已交回、review 接收并接线 | 正常主Turn Prompt-trigger、尾随文本、自然语言批准及开关边界；79项定向证据，待实际Dashboard验收 |
| Noting Trigger / runtime | F3 与 P15 完整交回并 review 接收 | child 正式执行、受限语义工具、Snapshot、原生 admission receipt、CLI/messaging/TUI Idle 与 Force 已有正负证据；实际 Proxy 流式链路成功 |
| Schedule / Reminder | F2 增量修复已 review 接收并接线 | pointer/registry 与 pending claim 同事务、迟到 Snapshot/rewind/null/branch、stale/expired/cross-owner 与 off-on 均有证据；待全轮门禁 |
| 跨模块集成与少量 Prompt 调优 | 增量修复与接线中；T6 少量文本已实现、75项定向通过 | wrapper、关闭回退、并发与失败路径须在修复接线后确认；T6 无新机制 |
| 官方 Dashboard Web UI E2E acceptance surface | 官方 TUI/Web 已构建；shared Slash 已接，验收待 Verification | 共享 Slash 命令自然可用；优先零 Dashboard 补丁，必要才补薄兼容层；本地内置浏览器验收 |
| 独立 Verification | 待启动（增量修复与 T5/T6 收敛后） | 集成收敛后全新审查者按冻结依据核对机制、正式路径和证据；关闭范围内阻断 |
| 独立 Validation | 待启动（增量修复与 T5/T6 收敛后） | Verification 通过后，另一全新验收者通过产品入口执行适用用户场景 |
| 主会话交付判定 | 自主目标已恢复，待最终核验 | `final-delivery.md` 记录当前证据、停止原因与恢复条件，不声明整轮完成 |

## 当前编排与风险

- 三项只读接线研究已完成并纳入计划。首批 T1/T2A/T3A（Codex 派遣，gpt-6.1-sol / high）接收于 `cd79cf6c46`。Codex 额度耗尽后 Kimi 主会话接手；第二批 T2B/T3B/T3C/T4 曾以 wrong-model 中断、经用户修复绑定后 resume 原四个 Agent（deepseek/deepseek-flash），全部交回并接收。Kimi 主会话集中接线（MRO/schema/turn hooks/notebook commit reconcile/rewind/branch/force seam/TUI Idle poll/工具面）后，三轮回定向复测全绿；测试适配（7 文件手动 mixin 子类改普通 SessionDB；`session_history` 登记 CONFIGURABLE + `_RECENTLY_SHIPPED_TOOLSETS`）已随修复提交。
- 三份根核心文档与本轮索引已在冻结提交中一并纳入；后续文档变化为获用户授权的RTK透明使用一句规则、A27/A28 授权、`baseline.txt`、`plan.md`和动态状态。01 / 02 正文和锁文件未改。
- 基线没有02要求的`session_history`模型工具的缺口已由 T1 关闭：当前 Conversation History Foreground search/read 已新增并正式接线（并登记为可配置 toolset，saved list 经 `_RECENTLY_SHIPPED_TOOLSETS` 回填）。
- Parity 抽取的实施设计按 02 §5.3：`/btw` 现有调用点与 detached constructor 不改；原 constructor 内部调用纯 parity helper，Noting 的独立 persistent constructor 也复用该 helper。不是将原 constructor 加 flags 改成通用工厂；该设计写入计划，不追加为用户问答口径。
- 已接收的恢复期缺口：F1补birth/rewrite/branch/raw版本与host ownership；F2补current registry/pending事务；F3首次报告补正式child、mutation、Force/Idle及安全receipt；T5接共享Slash并清旧surface，T6稳定文本已提交。P15主工具面/基础History 46项定向证据与六项归属边界证据通过；实现已收敛，统一提交后进入两个独立门禁。

| 当前交付范围 | 机制实现 | 正式接线 | 针对性验证 | 用户结果 |
|---|---|---|---|---|
| T1 Identity/Foreground/History | 已实现，F1增量review接收 | birth/rewrite/branch/route正式接线完成；基础工具面P15收尾 | F1最新lifecycle30通过，相关事务反证和检查通过 | 未验收 |
| T2A语义模型/renderer | 已实现、review接收 | 模型/renderer＋T5 shared Slash 已接 | 两文件119通过；定向37通过 | 未验收 |
| T3A纯parity抽取 | 已实现、review接收 | 原 constructor 复用 helper；`/btw` 入口未改 | 四文件35通过；定向8通过；Ruff/health通过 | 未验收 |
| T2B/T3B/T3C/T4 | 已实现、review接收、集中接线完成 | MRO/schema/turn hooks/commit reconcile/rewind/branch/force seam/TUI Idle/工具面 | run1 31文件1033通过；run2/run3 修复后全绿（详见下） | 未验收 |

## 恢复后的复核与修复编排

恢复审查基线：`2ba9b34193`；原始文档冻结仍为 `5346cd094b`，01/02 未变。已核对第二批实际 DB、child、request、host 接线及任务证据摘要；测试全绿仅在既有覆盖范围内有效，以下正式链路缺口仍须关闭。

| 增量任务 | 状态 / 修改边界 | 完成条件 |
|---|---|---|
| F1 身份与历史生命周期 | `fix_identity_lifecycle` 完整交回，主会话 review 接收；待统一提交 | 原生 birth、即时 branch freeze、rewrite/clone/exclusions/pointer 同事务、Full audit 与 Gateway live ownership 已有正式证据；主会话 reset hook 也已实测 |
| F2 Notebook/Schedule 一致性 | `fix_notebook_schedule` 完整交回，主会话 review 接收；待统一集成提交 | current pointer 与 registry 同事务；迟到/rewind/null/branch、半写 rollback、stale/expired/cross-owner claim 及 local-off 已有定向证据；接口保持、失效 queue 返回 None |
| F3 Noting 正式执行 | 原 Agent 完整交回，P15 与归属边界已 review 接收；待统一提交 | 真实 Agent/SDK 工具面与基础 History、同 Turn 稳定、branch/resume/reset/压缩续接 main 归属有证据；原 runtime/实际模型/原生 receipt/host seam 证据保留 |
| T5 shared surface | 完整交回，主会话 review 接收；三份薄 patch 已串行应用 | shared catalog/dispatch/exec/send、CLI/Gateway及remote host已接；79项定向通过；零 Dashboard React/API patch |
| T6 通用 Prompt | 已随 `035c4ed` 提交，75项定向通过 | 少量稳定 guidance，无新机制或会话中 root prompt 重建 |

主会话按完整返回集中 review；无必要全局工作时等待，不检查零碎文件增长。独立门禁仅在全轮集成收敛后派遣。

- A31 续接：账号额度曾使原 F1/F3/T5 中断，用户再次要求继续直至本轮目标完成；现已恢复这三个原 Agent 的断点，不新增重复任务。F1/F2/F3/T5 已完整接收，复核 P15 后统一提交；没有重派已完成任务。

- F2 接收证据：`.hermes-dev/evidence/f2/summary.md`、`manifest.json`。六文件 64 个不同测试有效通过；17 项纯 `2ba9` 基线负对照失败，branch 混合版本反证单独标明依赖。官方独立 index Ruff/health 通过，9文件0 blocking/0 advisory；没有为了接收报告复跑。branch Snapshot history 与 runtime 继承按 plan.md S5，local-off 在 DB transaction 内重查，global/profile 由 F3/host 负责。
- F1 接收证据：`.hermes-dev/evidence/f1/handoff.md`、`final-hashes.json`，18个任务文件及5个集成依赖。最新 lifecycle 30项通过；相关 run6–run12 按实际影响范围验证，SQLite写拒绝/stale CAS/branch自身 destructive 与 parent 独立性有反证。独立 index Ruff/health 0 blocking/0 advisory；未复跑有效证据。
- F3 首次完整报告：`.hermes-dev/evidence/f3/report.md`、`manifest.json`。正式流式 Parent暖请求1次+child同Turn6请求、12条suffix、completed/Snapshot/close；实际SDK kwargs边界prefix/tools规范JSON bytes相等、Parent tools不变。7响应报告10,532 tokens，无cache-hit细项。最终40项定向通过；原生app-server既有63项及新增9项通过。非流式Proxy空tool_calls真实失败保留。P15在主会话接收审查中发现，未宣布整项完成。
- T5 接收证据：`.hermes-dev/evidence/t5/summary.md`、`tree-manifest.json`。隔离真实源码树应用三薄patch后79项通过/0失败，官方Ruff/health 0 blocking/0 advisory；主会话已在同源码入口应用CLI MRO/refine删除、Gateway MRO和canonical短横线解析。remote帧桥覆盖目标profile/主Session/tail/busy语义，未冒称远端部署实测。Desktop Vitest因既有缺少plugin-babel未执行，静态registry两项Python通过。
- 主会话串行 fork-tag：`prompt_cache_scope` 使用 F3 `_secretary_noting_suffix_diverged` 信号，不伪造 compression_count；两相关文件32项通过（1.3秒），日志 `.hermes-dev/evidence/provider/fork-tag-tests.log`。
- 恢复阶段快照 `035c4ed`：授权与增量修复依据、官方 PM 前端准备、birth 薄接线及 T6 文本；三个在途修复未纳入该提交。根 staged Ruff/health 两项通过，health 0 blocking/0 advisory（6.1秒），日志 `.hermes-dev/evidence/provider/root-checks.log`。
- 真实调用已获 A30 再确认。F3 正式默认流式已完成 Parent→Noting→语义维护→Snapshot 链路，字段说明/Force Reminder 修补与完整报告已交回；非流式 Proxy HTTP200 返回空 content/无 tool_calls 的失败保留为环境负证据，不能计为成功。

## 起点与验证摘要

- 本轮起点：`main`，提交 `ef1f0e909c7f8b438a2121aa9d9d07b0f7697eb6`；进入对齐前工作区干净。冻结检查基线按 `AGENTS.md` 的官方提交 `d02f211858ab202d6d4d34ea59774591a5f14cbd`。
- 已有环境：官方 PM 工作区 `.venv`，Python 3.14.7，已纳入 `dev` / `test` groups；初始化记录确认官方依赖定义与锁文件未改。测试使用隔离状态及 canonical runner。
- 沿用已有证据：初始化阶段本地保留检查执行一次，10 项通过；GitHub Actions 已关闭。这些证据不证明 Secretary 功能或完整 Python suite 通过。
- 本轮文档基线及计划阶段：01 / 02 原文未改，差异检查通过；计划/RTK授权指导阶段快照 `56d5adee6d057afa35cd5cae99a5f12e66371b2a`，初始冻结哈希保留在 `baseline.txt`。尚未运行完整suite或两个独立门禁。
- T2A：canonical runner两文件119通过（0.9秒）；最后Schedule校验修改后定向一文件37通过（0.5秒）。证据：`.hermes-dev/evidence/t2a/`。仅证明语义和输出边界，不证明持久化或产品闭环。
- T3A：canonical runner四文件35通过（6.4秒）；补充真实request assembly后新测试文件8通过（4.7秒）；Ruff/health通过。证据：`.hermes-dev/evidence/t3a/`。T3B/T3C 增加 runtime，恢复复核发现正式 spawn/mutation 接线缺口，当前由 F3 修复。
- T1：canonical runner Foundation 16通过（3.4秒）；相关5文件89通过（4秒）；Ruff/diff/health定向通过。证据：`.hermes-dev/evidence/t1/summary.md`。
- T2B/T3B/T3C/T4（各 Agent 交回证据）：T2B 20新测试+353 邻域通过+指针鉴别力探针；T3B 59新测试+280/283 受影响（3 项改动前既存）+512 配置套件+223 邻域；T3C 29新测试+476 受影响+`tests/agent/` 全目录 10759 通过（34 项干净 HEAD 复现的既存失败）；T4 33新测试+231 受影响+57 交叉。证据：`.hermes-dev/evidence/{t2b,t3b,t3c,t4}/`。
- 集成定向复测（Kimi 主会话，2026-10-08 凌晨）：run1 31 文件 **1033 通过 / 2 失败 + 7 collection error**（tui toolset 断言 + 手动 mixin 子类与中央 MRO 冲突）；修复后 run2 9 文件 **775 通过 / 1 失败**；补 CONFIGURABLE 登记后 run3 2 文件 **719 通过 / 0 失败**；本地保留检查全集 **10 项全绿**（staged，health 0 blocking；FILE_LINES 棘轮以提取 `agent/agent_init_config.py` 与两处 facade 调用点回退修复）。run4 42 文件 **1178 通过 / 1 失败**（cache-parity byte 不变量回归：surface gate 曾在 request 期经 reminder 路径懒触发切换工具面——用仪表复现脚本定位，已改为**仅构造期**执行 + registry 直取）＋ 1 个 flaky；run5 42 文件 **1179 通过 / 0 失败**（flaky 重试通过）；随后 flake 根因修复（due scan 改在 claim 时刻断言，消除 `(now, now+1]` 微溢出窗口），定向复跑 **3×9/9 绿**。证据：`.hermes-dev/evidence/integration/run{1,2,3,4,5}.log`。
- 阶段快照：`cd79cf6c46`（T1/T2A/T3A）；`6432913cbe`（文档与授权）；随后一次集成批次提交（T2B/T3B/T3C/T4 + 接线 + 测试适配，哈希见 git log）。
- 大型检查执行方、版本、范围、次数、耗时与结果待实际执行后记录；当前平台及真实模型覆盖尚未验收，不声明跨平台通过。

- 2026-10-08 真实测试授权再次确认：本机 Codex Proxy / GPT6 Luna，沿用 A11 的 High；Hermes 仅被测、不参与编码。正式 CLI 子命令入口为 `.venv/bin/python -m hermes_cli.main dashboard ...`；直接 `cli.py web --help` 曾误入无关对话并已结束，不作为验收证据。

- 恢复期模型连通证据：`.hermes-dev/evidence/provider/connectivity.json`，请求 `gpt-6-luna-high` / `reasoning_effort=high`，返回 `SECRETARY_PROVIDER_OK`；尚不证明产品功能。验收配置显式测试上下文窗口196,000 tokens，不冒充Proxy未公布的模型固有能力。

- 主会话增量接线：`run_agent.py::_ensure_db_session`成功create后调用 `initialize_conversation_identity(self,newly_created=True)`；F1将通过实际出生generation路径补接线证据。
- T6少量通用Prompt：`agent/system_prompt.py`稳定guidance层说明current history事实源、main只读Notebook、persistence候选经来源核对与明确批准；无新运行机制、不重建会话中root prompt。canonical runner两个相关文件75通过/0失败（9.4秒），日志`.hermes-dev/evidence/provider/prompt-tests.log`。
- 官方前端构建：主会话经 `source_build_env` / `prepare_launch_dependencies` / `build_source_tui` / `build_source_web`准备PM Node/Python/JS依赖并构建TUI和Web，成功。日志`.hermes-dev/evidence/provider/frontend-build.log`；未改前端源码/锁文件、未启动Dashboard用户验收。

- F3/P15 最终接收：真实 AIAgent／SDK 46项定向通过（15.2秒），branch/resume/reset/原生 rotation recovery 与冷启动续接的六项归属证据通过；DB Parent 指针不进入 Agent child 字段，未新增分类机制。当前 Ruff/health 89文件0 blocking/0 advisory（8.0秒），日志 `.hermes-dev/evidence/f3/p15_ownership_check.log`。
- 本轮集成收敛后的扩大回归由主会话执行一次，范围为 `tests/agent`、`tests/hermes_state`、`tests/secretary` 与16个受影响入口测试文件；冻结的十类检查全部保留。范围及计次保存 `.hermes-dev/evidence/final-local-ci/scope.json`，执行版本／耗时／结果待实际产生；独立审查共享证据，不重复跑大型检查。
