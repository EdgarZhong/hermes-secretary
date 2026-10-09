# V1.5 暂停基线与接续看板

## 自主口径收敛 · 待用户追认（下次用户交互优先报告）

> 本区域是项目 `AGENTS.md` 强制要求的显眼交接看板。规格空白的必要局部收敛可自主实施，但必须即刻登记，注明“Agent 自主收敛／待追认”；下次向用户询问、汇报或交接必须优先主动报告。不得冒充用户授权；普通编码细节不必上报；不构成事前审批门禁，也不涉及 Codex 全局规则。

| ID | 规格空白、Agent 的最小收敛及理由 | 影响范围与实施状态 | 用户确认 |
|---|---|---|---|
| — | **暂无新产生的待追认自主收敛**。历史“超限不提交”和“首响应后更改顶层工具”是用户已否定的实现偏差，属于下方整改项，**不得视为待追认决定** | 本次仅更新规格与交接，未执行代码修复 | 不适用 |

## 当前状态与恢复条件

2026-10-09 用户此前暂停所有代码修改与继续验收。**此后明确单独授权 GitHub main 上一次 V1.5 全范围文档新提交，不授权恢复编码、真实模型调用、测试或验收。** D01、两个 Profile 的五 Turn 终止／强制提交及 Snapshot 结束审计均已由用户定稿，不能再让 Coding Agent 自选准入、另设路由或把强制结束改成不提交。V1.5 代码实施／独立验收依然 **paused / 未完成**。


- 本轮权威索引：[index.md](.autonomous/20261009-v1.5-implementation/index.md)，snapshot-index.md为同正文链接；C05–C17是最新用户口径；C11纠正工具Schema承载位置，C12授权待论证记录和静态核对，C13明确授权加强现行02/04的完整生命周期表述。
- 最新规格：[04](docs/04-hermes-secretary-v1.5-implementation-spec.md)；未修订契约沿用[02](docs/02-noting-system-specification.md)。原附件原样保留于 d5acc2cc27c6053ff198448fa3502bd8dd47e415 历史树，不追改首轮报告。
- 原代码起点：main / 41f7057a28f8e9bf2fc6c8fb769748d9f2534012；产品承接 7533173ca315d6308b121d313f0dd281777c8604。
- 原文档冻结：d5acc2cc27c6053ff198448fa3502bd8dd47e415；计划基线：5dc152f0dfa4086134a79e6366bfbcc1d615784a。暂停代码快照：b0f260afe1a4e09f86725d800b109939953e45b2，完整哈希见baseline.txt；C11文档纠偏提交4f940cda0d，后续C12只增加待论证问题和调查交接。暂停快照保存当时的普通实现及文档，不代表当前全部口径或最终发布版本。
- 环境：macOS，官方PM工作区 .venv Python3.14.7，现有pyproject/uv.lock未修改。测试与未来运行状态仅限ignored .hermes-dev隔离目录。

## 最新口径与代码实际差距

1. **冻结父前缀始终存在（C05）**：同一个Noting Task每次实际模型请求、工具循环和continuation均保留触发时冻结的Parent root与截至Anchor的Active消息序列；只能累加Noting自有后缀，不能换成实时Parent历史。父前缀不复制到child持久转录。
2. **工具变更只追加在后缀（C06/C11）**：完整冻结父快照前缀包括root、头部原工具列表/Schema、到Anchor消息，首请求及以后均不改写。在`<noting-task>`及后续新增系统提示/控制消息中重新给出session_history、notebook_show、notebook_mutate列表与完整Schema，强调以此为准；特殊NOTING_WITH_COMPACTION另有compact_parent。沿用Hermes控制消息机制，不新增第二root；dispatch始终受Noting白名单限制。**当前代码仍在首次响应后扩child.tools，未实现完整前缀始终冻结及后缀工具声明，保持暂停，不宣称已修。**
3. **本轮运行选择与原生边界（C07/C09/C11）**：模型继承、API/provider直接沿用Hermes原生；不新增Secretary独立模型路由、provider适配或App Server Noting执行器。本轮Main、Noting及后续真实验收选择DeepSeek官方Anthropic接口 https://api.deepseek.com/anthropic，deepseek-flash思考模式；不使用Codex App Server或Codex Proxy，不自动fallback到它们。用户授权从 /Users/edgar/code/Ebbinghaus-v2/.env.personal.local 读取DEEPSEEK_API_KEY。仅确认该变量非空，**未复制凭据、未验证有效性、未切换runtime配置、未调用DeepSeek**。密钥只能进入隔离配置或正常秘密读取，不进Git/报告。
4. **缓存证据（C08）**：使用Hermes自己的真实request/response日志或获授权抓包逐次查冻结前缀和provider缓存读取tokens；字节一致、缓存命中量和效果分别报告。**当前没有这条真实Noting缓存核验结果**；Codex App Server日志不得作为证据。
5. **停止边界（C10）**：本次仅文档、撤销偏离和本地现状快照；全部后续实施/验收保持暂停。
6. **权威正文加强（C13）**：现行02 §5.5/§5.11/§6.16和04 §4.4同步明确首次、工具循环、重试、continuation全部保留完整父前缀；tool列表/完整Schema只在后缀声明，dispatch独立受限。后续fork-tag处理不授权改头部；禁止只验首请求或把后续扩头部工具写成预期。仅文档落实，代码问题仍待修。
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

接续工作只修Hermes中间层的完整冻结父前缀、追加工具声明与受限dispatch；不更换上游模型/API/provider机制。缓存观察仍按C08使用Hermes自身日志/响应或抓包，不以源代码推断冒充真实命中。当前没有新增模型调用、测试或验收。

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

## 详细接续任务看板（全部暂停，需用户恢复）

| 顺序/任务 | 范围、负责人和修改边界 | 依赖与实施步骤 | 完成与验证条件 |
|---|---|---|---|
| P0 D01 已定稿的最小接线 | 待恢复的 Main Runtime/Noting Agent；04 §4.5 是用户权威实现方案 | 实际请求派发时记录 native/external 单一事实，Force 即时读取、Idle/Resume 持久读取；仅 external 拒绝，native 沿用缓存与 Child；不新建路由快照或 Provider 层 | 当前未实施；含ACP伪装、Codex App Server、fallback、无新请求以及无副作用验收；不允许重新论证门禁设计 |
| H0 恢复依据与状态 | 主会话；根CLAUDE及接续轮次索引/计划 | 先接收P0用户修订并确认恢复范围；读取AGENTS/CLAUDE/index/baseline/01/02/04和自主套件，核对暂停快照、工作区与锁文件。C11纠正C06顶层Schema误解：完整父快照不改，新工具列表/Schema只在后缀；模型/API/provider沿用原生，不恢复T2b或独立模型路由建议 | 现行要求与保留代码差距明确，原生下层边界锁定，派遣行号重新核对，无未授权范围变化 |
| H1 Noting后缀工具声明与权限 | 新实现Agent gpt-6.1-sol/high；secretary/noting_child.py、noting_tools.py及必要中间层控制消息接缝；对应tests/secretary/test_noting_child.py、tests/agent/test_cache_parity.py；根文档主会话负责 | 在task及后续新增系统提示/控制消息中重新给出当前工具列表与完整Schema，明确以此为准；普通session_history/notebook_show/notebook_mutate；普通Profile另finish_noting(reason)，special仅以compact_parent正常结案。移除首次响应后扩顶层child.tools的旧行为，完整继承父头部工具Schema；真实dispatch始终白名单 | 原工具头部/root不变；新增Schema全部位于child后缀；task/tool loop/continuation声明持续有效；拒绝fs/Web/Memory/Skill/Cron/delegation执行。不重设计原生Loop或provider层 |
| H2 全生命周期完整父前缀 | H1同Agent或非重叠独立Agent；既有freeze/child循环及测试，深入范围先明确白名单 | 确认Parent root、原头部工具Schema、到Anchor消息在首次、多个tool request、同child continuation均不变；Parent并发追加、global切换、压缩不刷新冻结前缀；新增工具指示只在后缀，child仅持久后缀 | Hermes中间层实际组装内容与冻结源比较，逐次完整prefix一致；不改下层API/provider去满足。Anchor/commit原规则有效，child不自行压缩，不只核对第一次 |
| H3 本轮DeepSeek原生运行配置 | 主会话环境配置；只读Ebbinghaus-v2获授权环境文件，凭据仅本地隔离运行状态 | 使用Hermes已有配置/adapter选择官方Anthropic endpoint、deepseek-flash思考模式，凭据不输出；核对native resolved上下文/Force阈值与有效配置。本任务不开发独立Noting模型路由、provider适配、API改造或App Server执行器 | 原生Hermes Main/Noting有效模型继承与本轮已选配置一致；只在恢复后记录实际结果。遇原生能力缺口如实报告，不擅自扩大实现范围 |
| H4 Hermes缓存观察 | 主会话统一取证；沿既有Hermes日志/响应接缝，证据integration/cache/ | H1–H3后通过原生Hermes真实路径观察Main→Noting：首次、工具请求、continuation、Parent并发，记录完整父前缀指纹、后缀工具列表/Schema、原生返回的缓存统计；不改provider缓存策略或新增日志/缓存管理器 | 我方中间层冻结/追加机制逐次成立；真实命中另按原生响应记录，0或不可见如实报告。屏蔽认证头，只观察隔离Hermes流量，不用Codex日志 |
| H2b 有界结案与审计 | 待恢复 Noting/State 实现 Agent；Noting Child/Tools/Session Snapshot/日常读投影 | 两Profile最多五Turn，正常结束各自工具，超限强制有效Snapshot提交，特殊框架直接调用父原生Compaction；审计termination仅内部可见 | 不以终止工具缺失当Snapshot拒绝条件；旧Snapshot/Branch兼容、真实工具调用、权限与原Commit Gate回归 |
| H5 接收集成与定向证据 | 主会话亲自review、微小接线；深入修复重新分派 | 接收七项报告、正式请求/权限/状态/失败与上下游；同时对本次Foreground兼容字段清理做必要定向复测，然后按DeepSeek重新验证global on↔off、local schema稳定、Warm/Cold/pinned、Full latestsource。更新README稳定事实、CLAUDE状态，创建明确待审提交 | 新口径代码与文档一致；未改V1未修订机制；凭据/个人内容不进Git；版本与证据匹配，不用反复复跑已有tests代替review |
| H6 一次必要扩大回归+独立Verification | 全新fork_turns=none reviewer；产品只读，仅verification.md与证据；主会话统一安排测试执行方 | H5收敛后按冻结输入独立重新提取V1未改要求+M01–M28+C05–C17及用户后续已定稿修订；统一一次10类检查及实际影响的Secretary/Agent/State/Gateway/CLI/TUI/History分区、必要共享catalog验证；不无差别重测无关能力 | 六节完整矩阵与原文→路径→条件→方法→观察→判定闭环，无违规/证据不足；macOS边界明确。已知失败与新回归区分；修复仅定向复测，不能关闭规则让结果变绿 |
| H7 官方Dashboard独立Validation | 另一个全新fork_turns=none validator；产品只读，validation.md与隔离runtime/证据 | H6通过后先写场景供主会话过目，再用官方Dashboard+localhost native gateway+真实DeepSeek Main/Noting操作：跨compaction查原文、global/local/cold、真实Candidate自主搜证/后续更正、修订不写、明确批准限定写、Noting归档、Schedule idle/busy、Full Prelude/身份/Anchor审计 | 全部适用用户场景真实输入到输出通过，保留失败序列；构建/CLI/mock不替代，平台未测不冒称；无个人UI/新API/云部署 |
| H8 交付判定 | 主会话delivery-evidence-review；根状态及新轮次final-delivery | 两独立门禁关闭、范围内整改清空、最新版本无新增必要缺口；对照本轮暂停历史与新轮次原始要求 | 才能标goal complete并交付实际commit/证据；未关闭继续修复，不以阶段测试通过替代整体完成 |

恢复实现时D01及生命周期/审计已定稿，只需用户另行明确恢复编码与验收授权，再按autonomous-run建立新的接续轮次索引，引用暂停代码快照、原始5346cd/d5acc和C05–C17，复核本表已查明偏差；不得重新发明D01模型路由方案，也不得自行补设产品准入条件。保留本轮暂停交付和历史结论，不追改为后来已通过。

## 已知验证边界

- 本轮独立Verification、Validation均未启动；唯一扩大检查尚未执行。恢复后按H6/H7统一安排，不先跑大型检查“建立基线”。
- 首轮7533173审查101条：98符合、2违规对应Full root provenance、1本机平台不适用；不是本轮通过声明。
- 首轮扩大suite在6a75369：13,318通过、117失败、109跳过，后续定向修复，未重跑整套；无全suite全绿结论。
- 平台只实测macOS，Linux/Windows未实测。真实cache hit未测，DeepSeek未调用。本次Foreground兼容字段清理未复测，隔离旧DB可能保留unused nullable列，新捕获采用显式列名不要求迁移；恢复后只定向核实。当前代码仍有首次响应后扩顶层Schema的旧机制，未满足C11完整前缀冻结和后缀工具声明，不能以旧测试绿代替H1/H2。
- 历史暂停轮次原本不 push；**本次已单独获授权把文档新提交写入 GitHub main**，不包含任何代码、运行、验收或密钥；自主编码目标继续暂停。
