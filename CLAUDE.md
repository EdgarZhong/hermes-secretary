# V1.5 云端恢复实施与接续看板

## 自主口径收敛 · 待用户追认（下次用户交互优先报告）

> 本区域是项目 `AGENTS.md` 强制要求的显眼交接看板。规格空白的必要局部收敛可自主实施，但必须即刻登记，注明“Agent 自主收敛／待追认”；下次向用户询问、汇报或交接必须优先主动报告。不得冒充用户授权；普通编码细节不必上报；不构成事前审批门禁，也不涉及 Codex 全局规则。

| ID | 规格空白、Agent 的最小收敛及理由 | 影响范围与实施状态 | 用户确认 |
|---|---|---|---|
| — | **暂无新产生的待追认自主收敛**。本轮静态 review 只补齐现行规格已明确的 continuation wrapper 与 terminal 参数契约，不改变产品语义 | 云端代码已实施；待本地运行门禁 | 不适用 |

## 当前状态与恢复条件

2026-10-09 用户已明确恢复 V1.5 编码授权：由当前云端主会话直接在 GitHub main 完成可远程完成的编码、静态核对与自主实现过程文档，并提交可由本地 Coding Agent 直接续接的版本；无需 subagent。此前暂停状态到 70c772180d1bb2aaf8bba8d27a8a64f7c2fabb12 为止，现已解除。D01、两个 Profile 的五 Turn 终止／强制提交及 Snapshot 结束审计均已定稿，不得重新设计。真实 DeepSeek、Dashboard 用户验收及必须独立执行的 Verification/Validation 若云端条件不具备，必须保留为本地接续门禁，不得伪装通过。


- 历史暂停轮次权威索引：[index.md](.autonomous/20261009-v1.5-implementation/index.md)，C05–C17继续作为定稿规格来源。当前恢复实施轮次权威索引：[index.md](.autonomous/20261009-v1.5-cloud-resume/index.md)，snapshot-index.md 同正文；本轮基线固定为 70c772180d1bb2aaf8bba8d27a8a64f7c2fabb12。
- 最新规格：[04](docs/04-hermes-secretary-v1.5-implementation-spec.md)；未修订契约沿用[02](docs/02-noting-system-specification.md)。原附件原样保留于 d5acc2cc27c6053ff198448fa3502bd8dd47e415 历史树，不追改首轮报告。
- 原代码起点：main / 41f7057a28f8e9bf2fc6c8fb769748d9f2534012；产品承接 7533173ca315d6308b121d313f0dd281777c8604。
- 原文档冻结：d5acc2cc27c6053ff198448fa3502bd8dd47e415；计划基线：5dc152f0dfa4086134a79e6366bfbcc1d615784a。暂停代码快照：b0f260afe1a4e09f86725d800b109939953e45b2，完整哈希见baseline.txt；C11文档纠偏提交4f940cda0d，后续C12只增加待论证问题和调查交接。暂停快照保存当时的普通实现及文档，不代表当前全部口径或最终发布版本。
- 环境：macOS，官方PM工作区 .venv Python3.14.7，现有pyproject/uv.lock未修改。测试与未来运行状态仅限ignored .hermes-dev隔离目录。

## 最新口径与云端实现状态

1. **冻结父前缀始终存在（C05）**：同一个Noting Task每次实际模型请求、工具循环和continuation均保留触发时冻结的Parent root与截至Anchor的Active消息序列；只能累加Noting自有后缀，不能换成实时Parent历史。父前缀不复制到child持久转录。
2. **工具变更只追加在后缀（C06/C11）**：完整冻结父快照前缀包括root、头部原工具列表/Schema、到Anchor消息，首请求及以后均不改写。在`<noting-task>`及后续新增系统提示/控制消息中重新给出session_history、notebook_show、notebook_mutate列表与完整Schema，强调以此为准；特殊NOTING_WITH_COMPACTION另有compact_parent。沿用Hermes控制消息机制，不新增第二root；dispatch始终受Noting白名单限制。**云端代码已移除首响应后扩 child.tools 的旧行为；每次请求保持冻结 Parent 顶层 tools，合法工具与完整 Schema 只在 task/continuation 后缀声明；真实 provider 请求一致性仍待本地取证。**
3. **本轮运行选择与原生边界（C07/C09/C11）**：模型继承、API/provider直接沿用Hermes原生；不新增Secretary独立模型路由、provider适配或App Server Noting执行器。本轮Main、Noting及后续真实验收选择DeepSeek官方Anthropic接口 https://api.deepseek.com/anthropic，deepseek-flash思考模式；不使用Codex App Server或Codex Proxy，不自动fallback到它们。用户授权从 /Users/edgar/code/Ebbinghaus-v2/.env.personal.local 读取DEEPSEEK_API_KEY。仅确认该变量非空，**未复制凭据、未验证有效性、未切换runtime配置、未调用DeepSeek**。密钥只能进入隔离配置或正常秘密读取，不进Git/报告。
4. **缓存证据（C08）**：使用Hermes自己的真实request/response日志或获授权抓包逐次查冻结前缀和provider缓存读取tokens；字节一致、缓存命中量和效果分别报告。**当前没有这条真实Noting缓存核验结果**；Codex App Server日志不得作为证据。
5. **停止边界更新**：C10 是历史暂停口径；用户本轮 R01/R02 已明确恢复云端编码和过程文档更新。云端可完成的实现已继续，真实运行与独立验收仍留本地。
6. **权威正文加强（C13）**：现行02 §5.5/§5.11/§6.16和04 §4.4同步明确首次、工具循环、重试、continuation全部保留完整父前缀；tool列表/完整Schema只在后缀声明，dispatch独立受限。云端实现已按此纠偏，实际 provider 请求和 cache-read 仍须本地验证。
7. **D01 定稿（C14；覆盖C12旧“未定稿”）**：仅记录最后实际 Main 模型请求 native/external，实际 dispatch 更新内存 `_secretary_last_main_execution`，Main Turn 完成通过现有 patch_session_model_config 持久化同值。Force 读即时内存，Idle/Cold Resume 读同一持久值；无模型请求不清空；仅确认 external 才拒绝并使用既定框架提示，native 原 Noting/cache_parity；不以 api_mode 模拟 ACP、模型路由比较或缓存 TTL 作新的准入条件。
8. **五 Turn 双 Profile（C15）**：普通 NOTING 新 finish_noting(reason) 正常结束；NOTING_WITH_COMPACTION 保留 compact_parent() 成功正常结束；两者同 Child 最多五 Turn，初始任务优先当前 Active＋Notebook，跨历史按需查。到上限两者均强制收尾并经原 Commit Gate 尝试 Snapshot；特殊由框架直接请求原生父压缩。
9. **Snapshot 结束审计（C16）**：新增 metadata termination，三型 finish_noting(reason)、compact_parent、forced；特殊超限 fallback 压缩成功仍 forced；日常 notebook_show、/notebook 和 Main AI 不得见。
10. **自主收敛治理（C17）**：项目 AGENTS 允许局部最小自主收敛继续实施，但必须即刻登记本页顶部待追认看板、下次用户交互首先报告；不得修改用户已确认规格。

## 理解偏差的时间定位与纠正（2026-10-09，静态核对，非验收）

用户在暂停期间先要求检查模型继承，随后明确C11：不改头部Schema，工具列表/完整Schema追加在task及后续新系统提示消息，模型/API/provider直接用Hermes原生，中间层负责上下文复用。此前调查中“从首请求收窄顶层tools”和“新增独立Noting模型路由”的建议均已撤下，不作为后续任务或已确认口径。

- **V1首轮已有实现偏差**：提交`6a75369c11`的`secretary/noting_tools.py::after_noting_response`首次响应后向`child.tools`添加NOTEBOOK_MUTATE_SCHEMA/特殊compact_parent并标suffix_diverged；V1.5起点`41f7057a28`保留同机制。首轮冻结`5346cd094b`的02 §5.2要求exact Parent advertised tool surface、§5.7允许父tools保持byte-identical并由窄dispatch限制。因此“只首次请求保留工具头部、以后修改”的问题早于本次V1.5澄清；本次未运行请求或测试，不声称已修。
- **V1.5实施范围偏差**：主会话将上游可选App Server存在误当成必须补兼容的任务，派生T2b并作兼容改动；用户未授权。已按C07/C10撤销，与上一条前缀问题分别记录。
- **后续解释/文档偏差**：用户提出C06工具变更指示时，主会话误写为“从首请求修改顶层tools Schema、撤销父工具parity”，在暂停基线`b0f260afe1`入文档；刚才模型兼容性答复沿用该误解并提出独立路由。C11现明确纠正；该错误解释不能冒充用户决定。
- **规格与审查责任**：原规格并未授权首响应后改写工具头部。旧实现把修改`child.tools`标记为suffix_diverged，混淆“追加child消息后缀”与“修改请求前部工具定义”；`record_noting_request`也只记录首请求工具parity，不能证明全生命周期一致。主会话审查未关闭这一矛盾，后来还误写成用户授权。恢复后的H1/H2须按原规格完整前缀与C11纠正，不能用供应商层解释合理化实现偏差；实际缓存命中损失尚未实测，不虚报数值。
- **仍成立的静态事实**：child由独立AIAgent/Session/DB handle运行，模型及api_mode等当前经parent_cache_parity_kwargs继承；若Main是codex_app_server，现有run_conversation按该模式进入外部Turn分支。这只描述现有代码，不授权为Noting增加App Server兼容或下层路由。本轮继续原生Hermes实施边界、已选DeepSeek运行配置与暂停状态。

云端已完成 Hermes 中间层的完整冻结父前缀、后缀工具声明、受限 dispatch、D01、五 Turn 与 termination 实现；没有更换上游模型/API/provider机制。缓存观察仍按 C08 使用 Hermes 自身日志/响应或抓包，不以源代码推断冒充真实命中。当前没有真实 DeepSeek 调用、可执行测试、独立 Verification 或 Dashboard Validation。

## 原始V1/V1.5规格核对结论与交接依据（C12）

本次检查的是本争议涉及的Noting热缓存、工具前缀与外部runtime边界，不是全篇规格正确性或独立验收声明。读取首轮baseline.txt确认V1原始冻结为`5346cd094b6a1bb6c6d9ce69e83b3a1570cf46bd`；读取V1.5原始`d5acc2cc27c6053ff198448fa3502bd8dd47e415`树，04文件SHA256为`3e7dd22ecd196527136a9051809f93e2ff177535cc70da622519ef397df85bbe`，与原附件记录一致。以这些历史树判断原稿，不拿Agent后来修改的工作区文字反证用户。

| 依据与原始位置 | 实际要求/事实 | 本次结论 |
|---|---|---|
| V1总纲01 §2.4、V1权威02 §5.2/§5.5/§5.7（5346cd） | 01要求Parent cache-parity prefix+narrow Noting tool surface并把细节交给02；02要求exact Parent advertised tool surface，图中列Parent exact tools[]，实际执行由窄dispatch限制 | 原规格未授权为了Noting修改头部工具Schema；01总纲的narrow不能脱离02解释成必须删改头部 |
| V1权威02 §5.10/§5.11/§6.16（5346cd） | child持续使用冻结Prefix/Anchor；§5.11两处明确强调first request热缓存复用和后续suffix不破坏Parent缓存，§6.16未逐次列出完整工具前缀一致性验收 | 目标和前缀机制明确，但后续请求缓存表述、逐次验收约束写得不够完整；不能声称原稿逐字写了“每次请求”或没有任何可补强处，也不能据此把头部变化解释为获授权suffix |
| V1.5原始04 §1.2 M14、§2.2/§2.3、§4.4、§7.2（d5acc） | M14继承V1缓存前缀与权限，不重做runtime；沿冻结Parent prefix；§4.4只追加Candidate/Schedule两句，保留现有工具使用顺序；真实cache未观测不得冒称优化 | 没有撤销父工具前缀一致性、没有新增Noting头部Schema修改许可。对既有工具顺序的保留不等于批准修改顶层tools；原稿也未单独补齐V1的后续缓存表述和外部runtime边界 |
| V1实施6a75369c11及保留代码 | after_noting_response首次响应后扩child.tools；turn_api_call调用该函数；turn_request_assembly随后直接使用agent.tools构建请求 | 实施把头部变化误当suffix，违反既有缓存前缀机制；不是刚才才产生，也不是原规格要求。V1.5保留了该问题 |
| 当前tests/secretary/test_noting_child.py::test_real_spawn_runs_semantic_tool_to_snapshot_and_close | 断言calls[0].tools等父列表，calls[1].tools新增notebook_mutate；record_noting_request只审计首次请求 | 测试将偏差当预期，并未验证全部请求的完整父前缀；测试通过不能证明原机制满足。当前只读核对，未运行测试或测量实际cache损失 |
| b0f260afe1暂停文档及后续答复 | Agent把C06误写成首请求改顶层Schema，继而提出独立Noting模型路由 | 后续工作区权威文档确实曾被Agent错误解释污染；4f940cda0d已纠正，与原用户规格问题分别归责 |
| 原V1/V1.5外部Agent runtime边界 | 原稿规定Hermes child和Parent runtime/prefix parity，没有明确外部整Turn执行器的完整上下文交接及支持范围 | **历史调查结论**：当时D01未定稿；用户后续已将其定案为最近实际请求来源门禁（04 §4.5），不增加模型路由或缓存准入。该历史缺口仍不能合理化顶层工具改写 |

交接结论：**头部Schema变化由实施、错误测试预期及审查造成；原用户规格未要求这样做。原稿存在可补强表述和外部runtime边界未定义，不能夸称全无问题；这些缺口不构成擅自改变热缓存机制的授权。** 已确认的C05/C11继续有效。D01现已由用户定稿；代码实施和验收仍暂停，本次只获文档提交授权。

## 已保留的实现、接收与证据

| 分区 | 保留事实 | 已取得证据与边界 |
|---|---|---|
| T0/T2普通provider | 精确回退首轮混合SECRETARY_GUIDANCE；独立A1/A2、Main资格、global/local读门禁、Warm/Cold/pinned同步、正式dispatch及actual request capture | Prompt报告 .hermes-dev/evidence/v1.5/prompt/return-report.md；定向101/89/23/3项通过，有重叠不可相加；11文件ruff/health通过。主会话review已接管，未宣称全轮完成 |
| T1 Foreground/History | 唯一latest Prelude、actual root与native cached root隔离、canonical identity read、真实System History、Full消费者；branch压缩与carried/late Force反例窄修 | foreground/report.md；清理前最终7文件106项通过、11文件ruff/health通过；本次撤销Codex partial字段及专项测试后未复测，历史计数不能作为暂停版本的新结果；反例日志保留。主会话已核对核心机制，独立门禁未开始 |
| T3 Slash/Proposal/Schedule | /notebook展示、/noting局部反馈、共享CLI/Gateway/TUI/compute-host接线；提案不预拼源原文、附录C自主搜证；Candidate/Schedule两句与expression五类 | workflow/report.md；52个不同定向tests通过；主会话集中review。真实Candidate→搜证→修订→批准→归档未验收 |
| 主会话微小集成修补 | Gateway命令与反馈捕获同一Session，防路由变化写到新Conversation | workflow/route-move-before-fix.log真实失败；after-fix整文件4项通过；没有扩大路由框架 |
| 历史真实模型核验 | Codex Proxy/gpt-6-luna-high/chat_completions五lane实际请求完成：global_on/local_off/global_off/cold_off/global_on_again；Full来源一致 | integration/real-main.log/json/audit.txt仅证明当时provider及工作区；不能证明DeepSeek已通过，也不是Dashboard验收或Noting缓存命中证据 |

所有本轮证据在ignored .hermes-dev/evidence/v1.5/中，不包含于提交；跨版本只按实际变更范围复用，不复跑有效结果充当review。

## 已消除的偏离影响

- 撤销T2b及Codex Noting协议研究，不再作为本轮实现依赖或验收阻断。
- agent/codex_runtime.py、agent/transports/codex_app_server.py、codex_app_server_session.py、hermes_tools_mcp_server.py已恢复5dc152f前本轮未改版本；tests/agent/test_codex_secretary_transport.py已移除。另撤销Foreground仅为Codex RPC增加的partial_context参数/字段/返回投影及专门Codex Prelude测试；通用missing/source审计保留。只撤销本轮误加兼容改动，不删除既有上游可选实现。
- 本地备份仅在 .hermes-dev/evidence/v1.5/retired-codex/t2b-uncommitted.patch 与兼容测试副本，供审计，不是接续任务。
- 9139原隔离Dashboard目前无监听，先前exec句柄已不存在；不启动新服务、不继续用户场景。内置浏览器仅完成运行库准备，未执行本轮Dashboard验收。
- 三实现Agent目前无继续执行任务；此前prompt/workflow因usage限制中断，不把T2b未交回内容称为完成。

## 详细接续任务看板（云端编码已收口；从本地门禁继续）

| 顺序 | 状态 | 本地接续动作 | 关闭条件 |
|---|---|---|---|
| H0/P0–P3 云端实现 | **已写入 main，静态 review 完成** | 不重新设计 D01/M27/M28；仅在运行证据发现真实缺陷时做定向修复 | D01、冻结前缀/后缀 Schema、双 Profile 5 Turn、forced Snapshot、termination 审计代码与现行规格一致 |
| H5 定向运行证据 | **待本地** | 先跑 `tests/secretary/test_noting_runtime.py`、`tests/secretary/test_noting_child.py`、`tests/hermes_state/test_secretary_notebook.py`，再补实际受影响的 agent/cache-parity/turn 生命周期测试与冻结检查 | 最新 head 的相关测试/检查无新增失败；失败只定向修复并复测 |
| H6 独立 Verification | **待本地，未通过** | 独立重新提取 V1 未改要求 + M01–M28 + C05–C17/R01–R05；核对正式接线、负例、证据与平台边界 | `verification.md` 六节矩阵闭环，无未关闭违规/证据不足 |
| H3/H4 Native DeepSeek 与缓存证据 | **待本地，未执行** | 使用既定 DeepSeek 官方 Anthropic / deepseek-flash 原生 Hermes 路径；核对首次、工具循环、continuation、Parent 并发的完整父前缀与 provider cache-read | 不改 provider/cache 层；真实请求证据证明中间层契约，命中量按实际记录 |
| H7 官方 Dashboard Validation | **待 H6 后本地执行** | localhost native gateway + 官方 Dashboard，以真实用户输入覆盖跨 compaction、开关、Noting、Proposal、Schedule/Reminder 与审计边界 | 用户场景全部通过或有明确不适用依据；CLI/mock 不替代 |
| H8 最终交付 | **未关闭** | 两门禁通过后更新本轮 final-delivery、根 CLAUDE/README | 才允许标 V1.5 overall complete |

当前云端实现提交链从 `a84ce76769` 开始；核心代码/测试包括 `aefd94b6f0`、`0edf956211`、`c5a4405fab`、`db88b6ce48`、`27d4463472`、`0fb3e8cf96`、`32349fc25f`、`2a58d3e49e`。后续文档提交只更新交接事实，不改变产品规格。

## 已知验证边界

- GitHub 连接器可读写仓库但当前会话没有可执行仓库工作树；因此本轮**没有实际运行** Python tests、ruff、health 或其它冻结检查。新增 tests 是待执行回归，不是已通过证据。
- 独立 Verification 与 Validation 均未启动；网页端当前没有本流程要求的独立 fork/subagent 条件，必须由本地 Coding Agent 接续。
- DeepSeek 未调用，真实 provider cache-read / cache hit 未测；完整父前缀的静态代码路径已核对，但不能代替真实请求证据。
- Dashboard 未启动，真实用户输入到模型输出未验收。
- 历史测试/审查结果只作为旧版本证据，不能自动覆盖本轮最新 head。
- 平台历史主要为 macOS；Linux/Windows 未实测，不得冒称跨平台验证完成。
- 本轮未产生“Agent 自主收敛／待追认”的产品行为决定。

