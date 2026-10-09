# V1.5 本地接续实施与门禁看板

## 自主口径收敛 · 待用户追认（下次用户交互优先报告）

> 本区域是项目 `AGENTS.md` 强制要求的显眼交接看板。规格空白的必要局部收敛可自主实施，但必须即刻登记，注明“Agent 自主收敛／待追认”；下次向用户询问、汇报或交接必须优先主动报告。不得冒充用户授权；普通编码细节不必上报；不构成事前审批门禁，也不涉及 Codex 全局规则。

| ID | 规格空白、Agent 的最小收敛及理由 | 影响范围与实施状态 | 用户确认 |
|---|---|---|---|
| P01（归类纠正） | **补齐现行规格，不属于新增自主口径**：`DEFAULT_NOTING_TASK_INSTRUCTION` 追加的 Active Foreground＋Notebook、按需 History、及时 terminal 四句，逐字来自已提交的现行 04 §4.4（HEAD 中行 245–249，M15/M27）。此前旁路看板误将其归类为未经确认的 Prompt 调优；本会话核对原文后纠正。此前用户“预览期间先保留”的记录保留，不扩写为新授权 | 产品代码与实际 sent task 断言未提交；独立 Verification V-001 指出漏实现，当前按冻结要求补齐 | 不需要新产品口径追认；如用户另行要求更改指导，按新修订处理 |

## 当前状态与恢复条件

2026-10-10 额度交接节点：用户提醒本轮可能无法实施完。5 小时额度已用 94%、周额度已用 79%（查询时点）；不再扩大场景或重开整轮检查。R08 默认真实 OpenAI 链路已完成：`openai-resume/default-368d1880`，12.97 秒、8 次 HTTP 全部 200，实际 `/chat/completions`、deepseek-flash、thinking enabled。真实 Main 承诺→Noting notebook_show／notebook_mutate／notebook_show／finish_noting→Snapshot→Main 真实 notebook_show 读回闭合；1 Child Turn，termination=finish_noting。5 条 Child 请求冻结 root/tools/messages 前缀一致，cache-hit tokens 为 4096/6656/6912/7424/7552（不是专属父缓存命中率），16 个产品源开始/结束 hash 一致。主会话已亲自核对探针、原始请求、真实读回与 Snapshot audit；最终离线报告随后补齐，不追加调用。

主会话已 review 并接收 d01_fix 最小接线：既有 middleware 后 Main scope、最终 provider invocation 通知、实际 root/tools Prelude 投影、ACP prompt write/flush；全 transport registry 已删除。`d01-fix/native-execute-targeted.log` 48 passed（5.5s）、projection 3 passed（1.8s）、ruff/health 0 blocking/0 advisory；不重复大型测试。该边界确认进入 Hermes native execute；人工非法 SDK 参数本地拒绝压力仍是明确限制，不宣称 HTTP 已发出，更不视为正常 DeepSeek 故障。当前拟保存本地阶段提交，不 push。H6 初审仍 FAIL，新的独立复审尚未执行；H7 Dashboard 仍 PENDING，由用户另一旁路体验，本会话未操作。下一次接续：以阶段提交和本地证据为输入，让 verification_recheck 全范围复审，失败只定向修复；H6 PASS 后再协调独立 H7，不重复已有效的大型运行。

2026-10-10 用户明确要求「把 DeepSeek Provider 换成 OpenAI 格式再测一遍，跑通真实链路」（R08）。本会话据此执行隔离真实重测：Hermes 原生 OpenAI Chat Completions，base URL `https://api.deepseek.com`，`deepseek-flash` 思考模式；不改旁路 Dashboard。native_evidence 仅在 ignored `openai-resume/` 证据及 `v1.5-openai-resume/` runtime 准备并执行默认 Main→Noting→Snapshot→Main 读回，开始/结束核对代码 hash；待实际结果后更新。d01_fix 按调查结论收回未接收的全 transport registry 候选，回到已有 provider 最终 execute 接缝的窄通知，保留 facade 兼容；不因人工非法 SDK 参数扩大底层改造。该异常压力边界与已复现 interrupt/preflight/Prelude 缺陷分开报告。

2026-10-10 用户质询 SDK 参数报错来源。主会话核对确认：`verification-local/test_sdk_local_rejection.py` 刻意注入 `invalid_middleware_argument=True`，故触发 SDK 本地拒绝；正常 Main/Noting 没有该字段，已取得的真实 DeepSeek 请求没有该类参数错误。此反例只针对派发事实的异常边界，不是正常调用故障，不能据此声称需要修 SDK 参数或扩大 provider/model 改造。此前汇报未区分人工压力测试与真实故障，现纠正。d01_fix 当前全 transport 方法观察 wrapper / 全局注册与引用计数只是未接收候选；已要求按现行 04 §4.5 Hermes middleware 后真正 provider execute 内层的既定接缝评估最小修复，分别报告真实 interrupt/preflight/Prelude 缺陷和人工异常测试，核查既有 MoA/custom/facade 行为保留。用户此前要求主会话停下汇报、子 Agent 不停；本次仅调查此质询并更新记录，不代表恢复整轮推进。

2026-10-09 用户指令「拉取最新提交，然后根据现状继续1.5轮自主实现」已恢复本地全流程执行。工作区原为干净 main / b24c558f15，fetch 后快进到 origin/main / c4b45bdf9bcc6bdedfb63897ae289c281a0c41ce（18 个提交）。沿用现有 `.autonomous/20261009-v1.5-cloud-resume/` 轮次及冻结依据，不重开轮次、不重新设计 D01/M27/M28。V1.5 整体仍未完成，独立 Verification/Validation 尚未通过。本地阶段提交沿用自主套件授权；不 push、不部署。

本地准备与当前编排：官方 PM `.venv` Python 3.14.7、既有锁文件不变；隔离状态仅在 ignored `.hermes-dev/`。主会话负责全局 review、接线集成与交付。真实 Native DeepSeek 取证已由上一轮本地会话用隔离探针脚本实际跑通两轮（见下）。H6/H7 各由新独立 Agent 执行。

最新定向与扩大运行证据：c4b45bdf9b 上三文件 **55 passed / 0 failed（17.4s）**（`local-resume-initial.log`）；四个 agent/cache/turn 文件 **28 passed / 0 failed（6.8s）**（`local-resume-agent.log`）；7e9e99df54 上冻结检查 **10 checks ok**、health 0 blocking/0 advisory（`local-resume-checks.log`）。7e9e99df54＋V-001 指令修复的 43 文件扩大回归 **673 passed / 11 failed（80.1s）**（`local-resume-selected.log`、路径清单 `local-resume-selected-paths.txt`）。4 个失败文件为 Schedule atomicity(1)、notebook tool(2)、Noting config contract(5)、Noting hosts(3)。初步归因是旧 Main 读门禁预期、host mock 缺 `finish_noting` 导致续 Turn 耗尽、Reminder fixture 未绑定有效 runtime；并非日志中占位 provider 名称证明凭据缺失。四文件定向修正后 **33 passed / 3 failed（8.4s）**（`local-resume-failed-retest.log`）；剩余三个配置 case 证实既有修正指导未输出，主会话在正式 `noting_trigger_gate` 补既有 guidance、未改拒绝逻辑/阈值。随后 config contract＋runtime 两文件 **32 passed / 0 failed（4.8s）**（`local-resume-config-feedback.log`），原 11 个失败已定向关闭。另加强local off仍读完整已有Snapshot，`local-resume-local-off-read.log` 3项通过。D01/Prelude修复交回后，主会话review新增真实SDK本地参数拒绝反证，发现记录仍早于HTTP派发；已退回继续整改，暂缓阶段提交与新独立复审。H5尚未关闭。另新增实际Noting child的瞬时SDK连接错误→原生重试→工具循环→正常Snapshot用例，首次漏import导致1fail/旧25pass（`local-resume-retry-prefix.log`），修正后只复测该用例 **1 passed（4.3s）**（`local-resume-retry-prefix-retest.log`），逐次冻结root/tools/messages及task时间戳不变；这是canonical失败路径回归，非真实DeepSeek retry观测。主会话修复六文件ruff/health零阻断/提示（`local-resume-repair-checks.log`），最终新增用例相关ruff/health也通过（`local-resume-retry-repair-checks.log`）。此前误选 3964 文件的大范围运行已中止，不作为通过证据；一次解释器软链接解析错误引发 PM bootstrap 已中止，后改用工作区解释器路径完成上述 43 文件运行，锁文件未变。

真实 Native DeepSeek 证据（`.hermes-dev/evidence/v1.5/native-resume/`）：两个普通场景 `ordinary-5f6e157c`、`ordinary-de24213f` 已取得默认 task 正常结束、同 Child 两 Turn continuation 与 Snapshot 的真实请求证据，12 条 Noting 请求的 neutral/wire 冻结 root、tools、messages prefix 全部一致，响应有 provider `cache_read_input_tokens`；逐次 `matrix.md` / `audit.json` 已落盘。特殊场景 `special-324a2386` 另有 Parent 原生 manual compaction 的实际 handoff、7 条 Noting 请求完整冻结前缀一致与正常 `termination=compact_parent`；该工具本次返回 already_below_threshold，不能说它又执行了一次压缩。额外五 Turn探针中模型第二Turn主动正常finish，未取得真实forced，保留 `ordinary-0a2c3c5d`；其中单条gzip SSE usage采集缺失，不能推断缺失值。停止无必要追加真实调用，五Turn强制路径由已有正式行为回归补证并明确provider未观测边界。完整七项 `native-resume/return-report.md` 与三份主体矩阵已由主会话核对采集脚本、实际请求/响应与Snapshot接线后接收；共34次HTTP（26Noting＋7Main＋1summary），主体19条完整。新派发修复仅改变观察接缝、不改payload或Noting冻结机制，已有真实请求按这个边界复用；最终C08判定仍交独立审查，不把缓存读tokens推算为专属父缓存命中率。

`verification.md` 已交回六节初审，115 条（V1 68＋M28＋C13＋R6），对7e9e99df54最终判定87符合/17不足/9违规/2有依据不适用，初审不通过；多个违规条款归并为三个产品缺陷，报告正在登记本地整改和新证据，不能用工作区修补偷换初审对象。修复后依套件派全新独立审查者全范围复审。当前已证实 V-001（初始 task 指导遗漏，主会话补齐）、V-002（请求发出前误覆盖 D01 最近 Main 来源）、V-003（execution middleware 改写实际 root 后 Prelude 仍捕获旧值）；后两项由 d01_fix 在实际派发接缝定向修复。三个 Agent 中断后已恢复：d01_fix 实现、native_evidence 整理真实取证、verification 独立全范围审查；原修改白名单与无派生边界不变。H6 未通过，`validation.md` 维持 PENDING。d01_fix首版九文件修复已完整交回，主会话逐文件review并取得下列证据，但后续真实SDK反证要求继续修补，不能称缺陷关闭：Main请求ContextVar scope经现有worker继承，最终SDK invocation/ACP prompt写入后更新D01并捕获实际middleware后Prelude；本地准备失败/中断/短路不覆盖，aux不污染，actual错误仍记录。17新增＋两个反证 **19 passed**（3.4s，`d01-fix/tests-final.log`）；七文件相关 **170 passed**（12.6s，`tests-regression.log`）。review另发现Bedrock实际`toolSpec`未投影，补入既有Foreground sibling纯helper，两个反例由失败转通过；定向四文件 **171 passed / 8 skipped**（3.3s，`bedrock-after.log`，跳过仅既有boto3/botocore可选测试），旧格式兼容 **3 passed**（1.4s，`projection-compat.log`）；九文件ruff/health零阻断/提示（`bedrock-checks.log`）。不累加重叠测试计数，不把standin测试称真实服务派发。主会话新增真实OpenAI SDK＋HTTPX standin反例 `verification-local/test_sdk_local_rejection.py`，canonical日志 `sdk-local-rejection.log` **0pass/1fail（1.7s）**：SDK在本地拒绝非法middleware参数、HTTP transport零调用，source却改native。已要求d01_fix把事实通知推进到SDK完成本地准备后的真实transport执行观察点，排查Anthropic enter/Bedrock参数验证同类路径，不用TypeError回滚猜测实际派发。首版接线并未改变provider参数/路由、cache-parity、规则/阈值、公共工具或状态结构。2026-10-09 用户明确 Dashboard 实际体验在另一旁路进行，本会话暂不操作该入口；不因此自动算 H7 通过。

- 历史暂停轮次权威索引：[index.md](.autonomous/20261009-v1.5-implementation/index.md)，C05–C17继续作为定稿规格来源。当前恢复实施轮次权威索引：[index.md](.autonomous/20261009-v1.5-cloud-resume/index.md)，snapshot-index.md 同正文；本轮基线固定为 70c772180d1bb2aaf8bba8d27a8a64f7c2fabb12。
- 最新规格：[04](docs/04-hermes-secretary-v1.5-implementation-spec.md)；未修订契约沿用[02](docs/02-noting-system-specification.md)。原附件原样保留于 d5acc2cc27c6053ff198448fa3502bd8dd47e415 历史树，不追改首轮报告。
- 原代码起点：main / 41f7057a28f8e9bf2fc6c8fb769748d9f2534012；产品承接 7533173ca315d6308b121d313f0dd281777c8604。
- 原文档冻结：d5acc2cc27c6053ff198448fa3502bd8dd47e415；计划基线：5dc152f0dfa4086134a79e6366bfbcc1d615784a。暂停代码快照：b0f260afe1a4e09f86725d800b109939953e45b2，完整哈希见baseline.txt；C11文档纠偏提交4f940cda0d，后续C12只增加待论证问题和调查交接。暂停快照保存当时的普通实现及文档，不代表当前全部口径或最终发布版本。
- 环境：macOS，官方PM工作区 .venv Python3.14.7，现有pyproject/uv.lock未修改。测试与未来运行状态仅限ignored .hermes-dev隔离目录。

## 最新口径与云端实现状态

1. **冻结父前缀始终存在（C05）**：同一个Noting Task每次实际模型请求、工具循环和continuation均保留触发时冻结的Parent root与截至Anchor的Active消息序列；只能累加Noting自有后缀，不能换成实时Parent历史。父前缀不复制到child持久转录。
2. **工具变更只追加在后缀（C06/C11）**：完整冻结父快照前缀包括root、头部原工具列表/Schema、到Anchor消息，首请求及以后均不改写。在`<noting-task>`及后续新增系统提示/控制消息中重新给出session_history、notebook_show、notebook_mutate列表与完整Schema，强调以此为准；特殊NOTING_WITH_COMPACTION另有compact_parent。沿用Hermes控制消息机制，不新增第二root；dispatch始终受Noting白名单限制。**云端代码已移除首响应后扩 child.tools 的旧行为；每次请求保持冻结 Parent 顶层 tools，合法工具与完整 Schema 只在 task/continuation 后缀声明；真实 provider 请求一致性仍待本地取证。**
3. **本轮运行选择与原生边界（C07/C09/C11；R08）**：模型继承、API/provider 直接沿用 Hermes 原生；不新增 Secretary 独立模型路由、provider 适配或 App Server Noting 执行器。此前 DeepSeek 官方 Anthropic 接口真实证据保留；2026-10-10 用户明确要求改为官方 OpenAI Chat Completions 格式（`https://api.deepseek.com`）重测，仍用 deepseek-flash 思考模式，仅切换隔离测试 runtime。不使用 Codex App Server 或 Codex Proxy，不自动 fallback。用户授权从 /Users/edgar/code/Ebbinghaus-v2/.env.personal.local 读取 DEEPSEEK_API_KEY；本地此前已取得真实隔离请求，新格式结果见顶部。密钥只进入正常秘密读取或隔离配置，不进 Git/报告。
4. **缓存证据（C08）**：使用Hermes自己的真实request/response日志或获授权抓包逐次查冻结前缀和provider缓存读取tokens；字节一致、缓存命中量和效果分别报告。**当前已有逐次真实记录，完整门禁判定待独立审查**；Codex App Server日志不得作为证据。
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

云端已完成 Hermes 中间层的完整冻结父前缀、后缀工具声明、受限 dispatch、D01、五 Turn 与 termination 实现；没有更换上游模型/API/provider机制。缓存观察仍按 C08 使用 Hermes 自身日志/响应或抓包，不以源代码推断冒充真实命中。云端交接时没有真实调用或运行门禁；本地最新测试、DeepSeek 和独立审查状态见顶部，Dashboard Validation 未关闭。

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

交接结论：**头部Schema变化由实施、错误测试预期及审查造成；原用户规格未要求这样做。原稿存在可补强表述和外部runtime边界未定义，不能夸称全无问题；这些缺口不构成擅自改变热缓存机制的授权。** 已确认的C05/C11继续有效。这是 C12 时点的调查交接；D01 后续已定稿并恢复实施，当前运行与验收状态见顶部。

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
- 2026-10-09 23:10 按用户要求启动**隔离预览 Dashboard**：`HERMES_HOME=.hermes-dev/dashboard-preview`（真实 DeepSeek 凭据仅写入该 ignored profile 的 `config.yaml`，模式 600，未进 Git），命令 `.venv/bin/hermes dashboard --host 127.0.0.1 --port 9119 --isolated --no-open --skip-build`，入口 http://127.0.0.1:9119 ，后端 `/api/health` ok、`/api/config` 显示 `model=deepseek-flash`。此前 9139 旧隔离 Dashboard 已无监听。**本次仅为你查看产品的预览，不是 H7 Validation**，也不改变任何门禁状态。
- 三实现Agent目前无继续执行任务；此前prompt/workflow因usage限制中断，不把T2b未交回内容称为完成。

## 详细接续任务看板（云端编码已收口；从本地门禁继续）

| 顺序 | 状态 | 本地接续动作 | 关闭条件 |
|---|---|---|---|
| H0/P0–P3 云端实现 | **已写入 main，静态 review 完成** | 不重新设计 D01/M27/M28；仅在运行证据发现真实缺陷时做定向修复 | D01、冻结前缀/后缀 Schema、双 Profile 5 Turn、forced Snapshot、termination 审计代码与现行规格一致 |
| H5 定向运行证据 | **原11失败关闭；真实SDK本地拒绝反证未关闭，暂缓提交/复审** | 先跑 `tests/secretary/test_noting_runtime.py`、`tests/secretary/test_noting_child.py`、`tests/hermes_state/test_secretary_notebook.py`，再补实际受影响的 agent/cache-parity/turn 生命周期测试与冻结检查 | 最新 head 的相关测试/检查无新增失败；失败只定向修复并复测 |
| H6 独立 Verification | **审查恢复，未通过** | 独立重新提取 V1 未改要求 + M01–M28 + C05–C17/R01–R05；核对正式接线、负例、证据与平台边界 | `verification.md` 六节矩阵闭环，无未关闭违规/证据不足 |
| H3/H4 Native DeepSeek 与缓存证据 | **19条主体矩阵已接收；初审者已独立复核，最终判定待新复审** | 使用既定 DeepSeek 官方 Anthropic / deepseek-flash 原生 Hermes 路径；核对首次、工具循环、continuation、Parent 并发的完整父前缀与 provider cache-read | 不改 provider/cache 层；真实请求证据证明中间层契约，命中量按实际记录 |
| H7 官方 Dashboard Validation | **用户旁路实际体验；本会话暂不操作，未通过** | localhost native gateway + 官方 Dashboard，以真实用户输入覆盖跨 compaction、开关、Noting、Proposal、Schedule/Reminder 与审计边界 | 用户场景全部通过或有明确不适用依据；CLI/mock 不替代 |
| H8 最终交付 | **未关闭** | 两门禁通过后更新本轮 final-delivery、根 CLAUDE/README | 才允许标 V1.5 overall complete |

当前云端实现提交链从 `a84ce76769` 开始；核心代码/测试包括 `aefd94b6f0`、`0edf956211`、`c5a4405fab`、`db88b6ce48`、`27d4463472`、`0fb3e8cf96`、`32349fc25f`、`2a58d3e49e`。后续文档提交只更新交接事实，不改变产品规格。

## 已知验证边界（云端交接历史；本地新证据见顶部）

- GitHub 连接器可读写仓库但当前会话没有可执行仓库工作树；因此本轮**没有实际运行** Python tests、ruff、health 或其它冻结检查。新增 tests 是待执行回归，不是已通过证据。
- 独立 Verification 与 Validation 均未启动；网页端当前没有本流程要求的独立 fork/subagent 条件，必须由本地 Coding Agent 接续。
- DeepSeek 未调用，真实 provider cache-read / cache hit 未测；完整父前缀的静态代码路径已核对，但不能代替真实请求证据。
- Dashboard 未启动，真实用户输入到模型输出未验收。
- 历史测试/审查结果只作为旧版本证据，不能自动覆盖本轮最新 head。
- 平台历史主要为 macOS；Linux/Windows 未实测，不得冒称跨平台验证完成。
- 目前没有新增待追认的产品口径。P01 已核对为现行 04 §4.4 的漏实现修复；归类纠正与原旁路保留记录见顶部。
