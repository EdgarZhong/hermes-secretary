# 本轮实施计划：20261024-noting-maintenance-v2

## 目标与依据
冻结依据snapshot-index.md与baseline.txt（初始冻结文档提交a4faa767e6）；07顶部v2 §0–9明确本轮全部需求与验收。源码基线5ea0f7fbaa，工作树/Users/edgar/code/hermes-secretary-noting-v2，分支codex/noting-maintenance-v2；主仓其它dirty已保存ignored补丁并原地保留，未混入冻结。
优先级：先闭合六工具→真实维护→Snapshot→Framework→后续Main，再覆盖compaction触发矩阵。完成需主会话亲审、相关回归、真实Kimi长前缀/隔离Alex端到端、独立Verification及Validation、质量检查、干净提交和正式云端部署验证。

## 覆盖与任务
| 要求/口径编号 | 任务和正式路径 | 实现负责人及白名单 | 依赖和接口 | 验证方法 | 用户场景 | 完成条件 |
|---|---|---|---|---|---|---|
| R03/R04/R06/R07/R08 | A Notebook模型／Schema／存储与只读投影 | Sol A：secretary/notebook_contract.py、notebook_model.py、notebook_store.py、notebook_render.py、notebook_items.py、noting_contract.py、可增notebook_evidence.py；hermes_state_secretary_notebook.py；tests/secretary/test_r3_notebook.py、test_notebook*.py及新test_notebook_maintenance_v2*.py | 出口NOTEBOOK_CREATE_SCHEMA/UPDATE_SCHEMA/ARCHIVE_SCHEMA；working create可选schedule_suggestion，内部update仍可用changes映射；返回entry顶层建议单对象；投影可选db/conversation_ref参数，B负责正式调用传参 | 真实SQLite版本/引用/失败原子性、field/type/perms/新旧数据读取；时间优先级及readonly；关系原子清理 | S1创建更新归档；S2关键文件/证据时间；S3建议持久与关系 | 生产旧不可变Snapshot/聊天不迁移、不清空；旧字段在投影/新输入正确处理 |
| R01/R02/R05/R08/R09/R12/R13 | B 正式六工具权限、Prompt、Schedule→Framework | Sol B：model_tools.py、toolsets.py；agent/inline_tool_executors.py、tool_executor.py、system_prompt.py、secretary_prompt.py；tools/secretary_dispatch.py、notebook_tool.py、registry.py、tool_search.py；secretary/noting_child.py、noting_tools.py、noting_surface.py、noting_prompts.py、noting_recovery*.py、noting_notifications.py、framework_messages.py；新权限/Prompt/Framework测试以及相应既有非A/C测试 | A提供三Schema；B将wire扁平参数适配内部update。完整API父工具表不按Noting重建；Show投影带A所需db/ref。C仅负责noting_compact，双方不交叉 | 同步并发invoke/间接强制越权拒绝；Task/control/continuation、父子真实wire前缀；Framework末尾条件及非触发 | S4 Main拒四工具；S5 Noting只六；S6建议→后续Main考虑Scheduler；S7已外写范围退出 | 移除旧maintain执行入口，不重复Schema；用真实runner/DB覆盖结束预算与恢复 |
| R10/R11 | C compaction真实触发与无默认尾部策略 | Sol C：agent/context_compressor.py、conversation_compression*.py、turn_context_compaction.py、turn_preflight.py、context_compaction_request*.py、compression_facade.py、必要run_agent.py压缩签名小接线；secretary/noting_compact.py；tests/agent/test_context*、test_conversation_compression*及对应secretary compaction/idle/force测试，新test_noting_tail_policy*.py | 不改B的noting_child／capability模块。按本次attempt策略，不永久修改共享compressor；分类真实阈值vs其它；显式partial优先保留。新增policy sibling承接机制，防超标单元膨胀 | 真实engine摘要输入/输出、durable/live/request一致、用户和tool组及新消息；成功/失败/noop/取消、off/非Main/阈值/partial | S8 Idle正常/强制；S9手动/阈值/partial；S10活动输入与并发消息保真 | 历史旧tail先纳入摘要，提交前回插同策略；原生及失败路径零越界 |
| R01–R15 | D 主会话集成／亲审／真实端到端 | root独占根三文档、07与本轮.autonomous、ignored证据、ops记录及必要微小接线；不并行编辑实现者白名单 | A/B接口先闭合；C策略独立；分包不自行提交。集成后针对真实变更补测试，不重复有效大套 | Kimi Coding隔离Alex Profile，cwd在Git root外，N46代表历史超过原N38；真实Main→Noting维护→正常Finish/提交→Idle compaction→Framework→后续Main，记录wire/Usage/调用错误及拦截 | S11跨压缩上下文接续与建议；S12旧数据/部署保护 | 两门禁前亲审全部diff，检查凭据及无生产数据写入 |
| R14 | V 独立Verification→独立Validation→交付部署 | 全新Sol/high、fork_turns=none，分别仅报告与ignored证据 | Verification先只用冻结规格提判据落盘，再查实现；通过后Validation先交场景计划供root过目再实际入口验收 | 复用同版本必要证据，不以脚本模型代替真实API/用户结果，不复跑无关大套 | 全部适用S1–S12 | 无范围内违规/证据不足/未执行；root delivery-evidence-review后授权云部署并验真 |

## 当前状态与编排
| 目标/任务 | 机制实现 | 正式接线 | 针对性验证 | 用户结果 | 当前负责人和下一步 |
|---|---|---|---|---|---|
| A | 已实现并亲审 | 已接入正式路径 | 相关机制证据通过 | 待真实端到端 | notebook_data Sol/high |
| B | 已实现并亲审 | 已接入正式路径 | 相关机制证据通过 | 待真实端到端 | tools_prompt Sol/high |
| C | 已实现并亲审 | 已接入正式路径 | 相关机制证据通过 | 待真实端到端 | compaction_policy Sol/high |
| D | short首周期正常完成，第二周期因F02停止 | 正式原生链路 | 28请求（27完整HTTP200） | 第二周期／N46未完成 | root亲审；Sol最小续测准备 |

同一工作树不交叉改文件；测试均经HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh，.venv为与原PM lock一致的只读复用解释器，不改依赖。A/B共享接口如上，需额外文件先与root协调。子Agent不修改根文档、plan或相互文件、不派生、不提交，不访问生产或收费模型；各自完整交回一次报告，常规细节写ignored证据，禁止流水账。
部署仅root：按docs/cloud-deployment-sop.md首尔布局，保护三库/配置/绑定/排期/静态资产，先自然空闲与活动检查，备份，再切正式已审提交/重启/读回；不把测试Profile、合成数据或临时阈值带到生产，不自动回盖DB。

## 缺陷与整改
| 问题编号 | 要求与触发条件 | 当前事实与影响 | 优先级及理由 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|
| PRE-01 | 并行源目录存在其它任务文档dirty | 已独立工作树仅拷本轮定稿/规则/CLAUDE条目，保护其它dirty | 已解决，避免提交污染 | root | 保存前置补丁/新树gitdiff确认 | 关闭 |
| PRE-02 | 冻结CLAUDE尾部空行 | diffcheck提示新EOF空行，冻结提交已完成；已在后续计划更新去除 | 文档格式，不是运行缺陷 | root | 当前diffcheck通过 | 关闭 |
| F04 | 更新／抽入其它历史事实时，该entry须保留足以支持所记内容的来源 | c5真实F04四条均补新progress，但matter新增“12箱”未引原采购单；采购action及最终Main能正确找到该原单，不能代签matter自身direct来源。事实正确、来源覆盖不完整 | P2，真实语义／证据时间索引质量；不增加NL硬门禁 | root对齐，Sol实现／真实取证 | 获批最小Task来源句实际注入后，同类新增数量由该entry自己的UID/ranges支持，保旧事实/进度及完整原生链；不得手修产物 | 待用户批准冻结Prompt单句；独立Verifier已确认问题及细化方向 |

## 取舍、快照与续接
- 初始base5ea0f7fbaa，文档冻结a4faa767e6，自动push origin同名分支成功；baseline.txt已记录完整SHA，后续纳入阶段提交。
- 不改规则冻结、检查阈值或等级；禁止假OS、绕过模型路由/正式DB/核心Loop，不给Noting Scheduler权限。源码复用正常，若生产旧Notebook payload需兼容，沿既有读写/不可变版本接缝最小处理，不重建正式库、不批量迁移或写原生表。
- 显示保护：只允许自己创建的隐藏IAB（iab visible:false），禁止外部浏览器/桌面/用户页面及open/open_in_codex；不能后台验就记未验，不回退可见方式。
- 独立Verification初审完成且不通过（F01/F02），需修后全新独立全轮复审；Validation与交付尚未执行。后续提交由root统一，不以push等同部署。

### 执行期接口协调（不改变产品规格）
- A追加test_r3_notebook_time_projection.py，迁移旧工具及只读时间场景；B追加cache_parity.py仅普通delegate名单接线；C追加test_compression_last_assistant_anchor.py将旧tail断言明确限定Noting关闭的原生回归。三个文件所有权不交叉。
- 不新增first_evidence_time展示字段；证据投影和既有实质计龄语义分别保持，未知时间不造日期。
- 云只读确认183f1a5运行、工作树干净、双服务active；本轮后端发布不替换双SPA，仅核原完整集合/SHA。发布保护脚本本地SQLite备份/活动lease拒绝/双服务独立启动自检通过，尚未切生产。

### 主会话集成亲审与验证（待独立门禁）
- 亲审A/B/C实际差异和正式调用者：三工具→Store→不可变版本→Snapshot、权限各seam、完整父工具面/Task、关系清理收据恢复、只读时间所有产品入口、条件Framework与非触发边界、真实阈值分类/摘要输入/候选回插/publication/失败回滚。
- Root补CLI slash、Proposal、Web read所属DB参数，A跨表面9项通过。亲审反例揭露synthetic user时间优先级，A复用原生is_user_originated_turn修正，17项定向通过；不新增字段/来源授权门禁。
- A基包7文件243通过；B权限58、Prompt/surface/framework59、生命周期修后96等有效分区通过（范围重叠不相加）；C新完整链路44、Force18、原生压缩器302及owner/source集复用。完整日志分别在ignored .hermes-dev/{notebook-data-v2,tools-prompt-v2,compaction-policy-v2}/report.md。
- Root共享seam 5文件首跑117通过/2旧fixture失败；未改基线同2失败复现。旧Web read Idle fixture缺现行nested配置与threshold_tokens，B仅补测试配置，原断言全部保留，12项通过，故四个未改成功分区证据无需复跑。
- 真实Kimi短链28请求：27完整HTTP200，1人工终止无完整响应；第一轮正常提交／Idle压缩／Framework／Main实际Schedule登记及完整部分结算有效，第二轮清建议8次失败后停止。N46仍0真实请求。报告在ignored E2E目录，保留全部失败；dry失败不可当Provider故障。
- Root发布脚本只改后端，保护静态/三库/配置/绑定，离线备份/lease/双服务启动自检通过；未改云端运行态。当前生产183f1a5双服务active。

### 5ee2a94 初审整改与续测
- F01／P2：正式Instant carrier无display_kind，需在Notebook取时按既有持久回执、精确owner／UID／原文证明排除真人优先级。A已只改notebook_evidence.py和v2测试，26项＋独立真实Admission反例1项通过，root亲审接收，待新独立复审；不改原文、metadata、来源权限或计龄。
- F02／P1：Kimi wire的Moonshot sanitize移除nullable，违背既定null清除。Sol探针首个误加tool_choice与thinking冲突HTTP400，root明确追加仅移除此参数的纠正探针HTTP200并准确返回null，原失败完整保留；已实现窄可信官方Coding路由保留nullable，其他Moonshot／聚合保持。不改canonical Schema／Prompt／empty-string validator。最终111项通过，相关transport57／cap58实现不再改变复用有效证据，冻结10检查通过，root亲审接收。两探针按short计入总70。
- Sol D只准备从停止状态只读克隆续测，重建Main正常边界，不恢复旧child旧工具freeze，不重付首个成功周期；新HEAD锁定后root再授权收费。预算当前30／70，short30／45，long0／25；续测最多15请求。
- Verification初审版本5ee2a94：23条15符合／5违规（F01/F02牵连）／3证据不足；两缺陷修复后由全新Sol独立全轮复审，未通过不启动Validation。无生产上线动作。

- Root已接受最小续测计划resume-plan.md；准备0请求正式child wire通过，只读克隆源DB不变，新Main正常边界生成新child、不复用旧freeze，在线仍须验证真实Idle。F01/F02修补提交锁定后才收费；新的独立Verification已先基于冻结原文落判据，全轮复审进行中。

- F03／P2（全新独立复审新增）：Create显式status:null／relations:null被内部None默认吞掉，真实invoke反例2失败。root提案在wire _mutation_args按canonical单一非nullable type拒绝显式null，Store内部Python默认不改，省略／[]／合法nullable保持；Verifier已确认方向符合R03/R04（原Schema落实，不改产品语义）。B限定noting_tools.py增7行与原权限测试补例，invoke+Loop零副作用及正例138项通过、独立反例2项通过；root亲审接收，真实收费继续等待最终修补SHA。

### 833真实续测与当前讨论
- resume13请求=Main1／Noting11／summary1，全部有HTTP200、12完整。真实null update1成功，Finish9次为1接受+8幂等重复；之后自然正常返回、提交snap_4f20592f24c14665830fb3a6882ba220。审计者停止判断过早，SIGTERM截断已开始摘要，durable=false、第二Framework无，不能记成结束机制确定缺陷。原错误解释及更正均保留resume-report.md／stopped-audit-corrected.json。当前总43／short43／long0，无活收费进程，N46未执行。
- 用户追问工具设计与Finish为何后续请求；root提案只补工具轮合法Finish后的原生Turn收尾，随后仍runner Commit Gate，不改六工具Schema、Prompt、身份、混批、forced/overflow及提交条件；正在由独立Verifier评审是否属原契约接线细化，尚未实施。
- F04（真实语义来源缺口）：旧short entry1/2/3新增进度未补新UID，range=null，原UID原文不支持新增断言；白板I2/第二步来源指导/R06有效时间/R15内容证据受影响。D只读审833快照，不收费；旧证据保留。若需要Prompt第二步一句明确新来源，先向用户对齐，不以语义硬门禁或人工改输出遮盖。

### 当前独立研讨与实施边界
- 原契约评审：Verifier已依据R03/R11与07§4.5认可Finish后原生收尾提案为既有两阶段提交接线细化（不是新增完成条件），条件是不在handler内commit、不伪造模型final、不绕过native finalization/owner/cancel。B已接限定实现包：可信首Finish结果持久→原生Loop结束→空输出正常finalize→runner Commit Gate，覆盖预算最后调用及失败/原生回归；Prompt／Schema不改。
- F04已由D与Verifier分别只读确认833仍缺来源，另含entry4容量更新遗漏新消息。两份审计都保留原坏样本。root已向用户提交第二步单句before/after及异步确认，**尚未获答，不能实施Prompt改动**。未添加语义硬门禁或人工修模型结果。
- 第三次独立复审833：16项14符合／1违规（F04）／1证据不足（E00），F01/F02/F03关闭；报告verification-final.md。后继收尾实现及任何获批Prompt补充完成后，另派全新独立审查者按新冻结依据全轮复审，再进入Validation。

### 用户追加来源模型方向（尚未完整冻结，相关实现等待）
- 用户直接要求evidence_time数组（点/段），source_time_ranges数组与Message IDs可混传；Prompt建议同一证据只选一种表达，代码不作覆盖去重或重叠门禁。必须保留新／旧事实实际来源，数组本身不自动修复漏来源。
- 用户已确认IDs→evidence_time：每条真实用户消息各列一个时间戳；没有用户时取最近Assistant，再无则列全部来源时间。显式时间段独立加入数组，不被IDs覆盖。Candidate直接来源是否同样支持时间段数组与IDs混传尚待回答，notebook_refs模式及权限不扩大。新规格需同步07/索引与新冻结基线，再派数据／工具Prompt包，旧证据保留其版本。
- 最终模型样本/新独立双门禁/部署应针对最终来源设计及Finish接缝，不以833旧坏样本冒充新通过。费用仍43，未再请求API。

### Finish原生收尾包主会话接收
- root已亲审noting_completion、tool round、finalizer、原生interrupt上下游及12文件差异，核对报告源码Git blob完全一致；合法durable单独Finish→原生break/finalize→原runner一次Commit Gate，无伪造final。Main/关闭/普通child、非法与混批仍原路径；最后预算合法Finish正常，持久化/owner/commit失败不冒称成功。
- root亲审暴露clear前取消窗口并要求先反例；真实hard interrupt反例旧版会误提交，修补后在既有clear_interrupt锁内before_clear观察并更新result，原生继续负责全部清理、返回bool，默认None兼容原调用。三个取消屏障、四个正常正例及60项原生相邻回归通过，最终12文件冻结10检查0blocking/0advisory。有效源码hash及原失败在.hermes-dev/tools-prompt-v2/finish-report.md，未为review重跑有效大套。
- 阶段接收不等同全轮通过；真实收费43保持，来源数组新规格、F04自然行为新证据、N46、全新独立双门禁及部署仍未完成。

### 已确认来源数组增量的实施边界
- 07顶部及v2§3/§5/§6第二步、索引R06/R16已同步已确认部分：七内容类型source_time_ranges完整数组与IDs混传；evidence_time数组点／段及每条真实用户取时算法；软指导同一处证据择一。未知空数组不造时间，沿原合法域逐来源校验；旧单范围仅读兼容规范化，不改不可变原件；当前API不列旧字段别名。
- Candidate直接来源扩展仍待用户回答，现保原限制，只读refs链时间改数组；不把未答当批准。此独立选择不阻止通用数据与Schema更新，但最终收费、双门禁与发布前需收口。未获批准的“新增断言补新来源”候选句仍不实施，以用户此次明确软指导为界。
- A接通用数据／Schema／projection与旧数据兼容；B接正常Main／恢复边界Schema刷新、Task软指导及正式wire测试；文件白名单不交叉，root负责文档／亲审和必要微小接线。新模型最终验证与N46待全部产品锁版，不重跑旧复杂失败流程。
- Root亲审F04最小前态计划：全新隔离DB四条真实旧事实支持的prepared entry→自然新progress→默认Task→真实Idle/Finish/提交/durable压缩/Framework→后续Main Show/History，不能给模型UID/修源提示、不人工改输出；新断言必须由实际来源支持，数量/责任/未完义务保持。D仅获离线数组审计适配及最终dry准备，尚未授权发送。Root批准内部总70不变、short55/long15的配额重分配；已用43计数不改，F04单轮cap12，N46 cap15，SDK max_retries0、不自动转移未用配额。此决定不是新收费启动，待最终SHA锁定再逐链授权。
- Root零网络独立核N46材料：只从原kimi-k3-prefix-boundary-20261023/run_experiment.py AST取compact/history_unit函数，在无模型调用下重建46组；与当前long-history-n46.json全184条逐结构完全相等。证据.hermes-dev/noting-maintenance-v2/n46-fixture-generator-audit.json含原生成器及fixture SHA，不只依赖N标签。真实wire未缩短及Provider Usage仍须在线取证，不能以该离线核对替代。
- B发现Candidate旧Prompt要求“keep source_time_range null”与新Schema数组不符；root已批准仅同步为“keep source_time_ranges empty”，保原IDs/refs二择一及全部权限，不是Candidate来源范围扩展，也不借此改未批准F04候选句。当前Task中同一字段名/空值语义与新Schema必须一致。

### Candidate来源边界后续用户确认（替换上段临时保留限制）
- 用户已明确：二选一只发生在直接对话证据与notebook_refs间接引用之间；直接内部IDs／时间段数组可单独或混用。07及索引R16/R17立即更新，前次“keep ranges empty”只属回答前临时实现记录，须移除最终限制及其Prompt；不改两模式互斥、标签映射、目标、审批、实际写入结算。
- A负责validator/Schema/直接来源与refs相关数组用例；B负责Task对应句及其原五文件Candidate脚本/断言迁移，两者白名单不交叉。需测仅IDs、仅多段、混传、refs保持、模式切换完整清理、直接+refs混用拒绝及无来源拒绝零副作用。保旧仅IDs日志为历史，不以它签新契约。
- 来源范围现已完整收口，仍不得提前收费或部署；A/B最终整包后root亲审/锁版，再依最终版本做F04/N46、全新独立Verification与Validation。

### 来源数组整包主会话亲审
- root已亲读A七份产品及正式Store/item/source-basis/投影调用链、Candidate最终validator与正反例，11文件SHA256 manifest逐一与现树一致。规范化仅作用读/内部兼容，当前API不保单范围alias；逐来源域与事务重核、精确version/继承资格、Noop/稳定ID及旧immutable字节保持。时间点不合宽段，显式range独立保留；F01可信Instant证明和Profile时区路径保留。
- A最终Candidate相关15项、此前投影55项及七类型相关分区证据按源码影响有效复用；原171/216及中间临时Candidate证据保原时点，不冒称最终全量复跑。相邻12文件原152pass/45fail已由root交B处理5份旧脚本/期望，真实失败保留，等待最终B包。
- root已亲读B三份产品及旧pin→native恢复→Main apply→当前canonical pin→新Noting freeze上下游、恢复新audit及SDK测试，确认只更新变化的同名六定义、保其它工具顺序/字节；原生记录真实toolset cache break并best-effort pin，不热改已冻child，不Task再注Schema。最后Candidate措辞/测试迁移仍待B最终整包和依赖hash核对。
- B最终5d包已交回并root亲审接收：Prompt仅追加用户明确软指导并准确改Candidate direct/ref二选一，未改未批F04补新来源句；五份旧测试保实体/生命周期/失败原子与旧immutable兼容，最后Finish改读durable回执且验证所有call/result严格交错。最终Candidate两文件70项、两种真实SDK混传2项及负例28定向（重叠不加总）通过；非Candidate68项及原有效81/4/33按影响复用。A/B共21文件SHA256与现树逐一一致，实际依赖canonical/renderer稳定，不为review复跑有效大套。
- 当前A/B集成无已知机制缺口；来源软指导自然模型能否修正F04仍未证，N46及独立双门禁/部署仍未完成。root统一stage质量检查及阶段锁版后，D先最终零请求dry，再按明确授权收费F04；成功并亲审内容后才授权N46。
- Root整包实际stage相对初始源码5ea检查73文件，冻结10全部通过，health0blocking/0advisory，日志.hermes-dev/noting-maintenance-v2/source-arrays-integrated-checks.log。功能锁版c5f57b2552f7618e890fabeefb2fbfdc68eb9e7c已提交自动push、clean/upstream一致；不等同模型质量或发布通过。D仅获最终F04/N46零请求正式dry，尚未--run授权。新Sol/high/forknone独立noting_v2_verification_v4已派，先只读5d最终规格独立判据落盘，再查全R01–R17/O01实现与有效证据；历史报告保留，第四审追加同verification.md。Validation未启动。
- c5最终两个dry通过，root独立逐组786源码hash与关键wire/隔离字段核实，N46精确原生成器184消息未缩；ledger43不变。报告.hermes-dev/noting-maintenance-v2/e2e/final-c5-dry-report.md、proof.json。Root现仅授权F04一次收费（--scenario short --provenance-short --run，cap12/short55/total70），成功并亲审后另授权N46，不能自启后者；必须先核来源支持再付后续调用，保正常Finish后摘要完整推进，防误杀已提交阶段。V4独立29判据已落盘，完成其它静态/机制调查暂未核实新代码缺陷，等待当前真实证据后终局。
- root针对c5完成一次云端只读preflight：183f1a5仍运行、双服务active、Gateway/微信connected、Web/Gateway活动0，工作树/依赖/三库无有效writer/compaction/Noting，配置/绑定/双静态与数据保护哈希已取得；production_model_requests=0、cloud_runtime_writes=0。回执.hermes-dev/noting-maintenance-v2/release/preflight-receipt.json，未stage/apply/stop/重启或改库。正式发布前仍须重复当时预检，不把当前空闲当将来保证。
- c5 F04真实一次8请求正常结束，累计51；6个Noting工具结果均成功，无参数错误，合法Finish后Noting额外请求0。四条均补真实新progress；正常Snapshot→durable Idle full摘要→Framework→最终Main真实Show/History全完成，源Alex不变。root及独立V4分别亲读原Snapshot/childcalls/SQLite/原文，确认F04现收窄为matter新增12箱缺原采购单789edcb7来源，另一采购action已有该源、最终Main也准确History回读，但不自动补matter引用。raw .hermes-dev/noting-maintenance-v2/e2e/run-provenance-short-20261024-171957/，未人工改数据。
- V4已依据白板I2/v2步骤2认可“保留仍需内容来源并补新增/变化断言来源”为原义务最小细化，不得读全History或盲堆旧source；新实证需该entry自身source可支持新数量等、保原生整链。root已向用户展示原因及精确英文候选句，异步询问仅改Task第二步一句；冻结Prompt未答不改。D不启动任何后续收费/N46，实际运行已自然退出，尚不具备终局门禁或发布条件。
- V4当前c5完整审查已终结为27符合/1违规/1证据不足，独立六节与原始c5-short-independent-audit.json已交回root接收；修后按套件另派全新审查者，不要求原研讨审查者代签后继PASS。Validation仍未启动。root按delivery-evidence-review复核并将当前未完成/输入依赖/恢复步骤写final-delivery.md，goal保持active，不冒称用户暂停或目标完成。
- D离线Request-ID观察hook6组通过，0新网络，ledger51/policy70/55/15不变。root澄清旧c5原send本来已捕获白名单头，8个实际http_response仅content-type，两个Request-ID头未提供；新hook只是显式null，不回填旧事件，也不改变请求/重试/预算。后续同前态fresh F04计划只准备，未批准新Prompt/配额/run。

### 等待Prompt决定期间的独立N46取证
- root复核发现N46工具可调用性及长前缀完整链可独立于单句来源提示继续；此前“先F04全部语义通过才N46”是root编排顺序，不是用户产品要求。为推进用户明确授权的>N38真实模型目标，现调整顺序，保F04未关闭及最终双门禁要求，不以此降低判据。
- 当前HEAD f287e94仅四文档变化，相对c5全部产品代码/测试及786受测源码均不变。D先以当前HEAD记录精确版本及同c5代码等价，最小零请求preflight后可按root明确授权仅一次N46 --scenario long --run，原46组184消息、真实Main→Noting→正常提交→manual native full压缩／Framework→后续Main；原序列由实际机制决定并分别审，不混作Idle成功门槛。不得因调序修改Prompt、模型、工具、validator或截短历史。
- 原收费policy70/short55/long15及已用51不变，N46硬cap15，无重复run、SDKmax_retries0，无自动再分配。F04修后以及最终文本对既有N46证据的适用性必须再评估，必要受影响长样本仍须补，不能提前豁免；当前N46只按实际版本和声明范围交付，不关闭F04或允许部署。

### N46同版真实取证已取得（独立补核中）

- 执行HEAD f287e94（产品与c5相同），实际run-long-20261024-174448完成；8个HTTP200，累计59（short51/long8，含probe2）。root亲核首Main prompt141662、Noting146064/149716/153726/155074，超过旧N38约131745校准量；不把校准量称旧服务端实测。
- root逐结构比对4个Noting请求：Root/tools/186条冻结Active完全相同，无messages.tools，仅max_completion_tokens=32000；独立证据.hermes-dev/noting-maintenance-v2/n46-root-wire-audit.json。正常Finish后无Noting追加请求；6条正常Snapshot及Framework和后Main答复存在，原184历史仍保留。该样本为manual非Idle，不替代既有Idle时序证据。
- D仍完成执行审计；原V4获派只补同产品长样本条款与内容质量，不签未来Prompt新版PASS。F04旧短样本来源缺口保持、单句提示仍待用户明确答复；Validation/部署未启动。

### F05／N46独立内容反例（Prompt提案未实施）

- V4独立核实：action3/4正文断言“尚未开始／当前尚未开始”，唯一业务用户仅交代筹备启动与当前责任，未报告每项具体进度；原pending默认不构成正文零进度事实。依据原FAITHFUL EXTRACTION、白板U1及步骤7 unsupported status，P2内容偏离，不撤销N46长机制成功。
- root提案仅于FAITHFUL EXTRACTION既有禁止无依据添加事实句后追加：`Keep unreported progress unknown; a pending action does not establish that work has not started.` 不改status默认/Schema/validator，不加NL门禁或强制全History；原样本保留。V4评审方向后，冻结Prompt具体文字交用户决定；当前未改源。
- 后续必要证据：未报告进度的新自然行动不写确定未开始；明确已开始/未开始的受控正式提示分支保原提取语义，不以原pending默认遮蔽事实。最终新Prompt版仍须全新独立全轮复审；无自动新收费。

### 后续验收边界与待用户决定的精确文字

- F05候选措辞已细化为 `When the available evidence does not establish an action's progress, leave it unknown; pending does not mean the work has not started.`，强调全部现有证据，不能因最新消息未重述而清掉旧已知进展。V4按原判据认可方向，待新自然样本及最终fresh审查，不代用户批准。
- root已将F04来源句与本F05句合并一题，明确替代旧单句问题；用户答复“为什么要做这样的修补？前因后果也再发一下”，root已逐例解释，因此仍未批准。产品Prompt、Schema、状态默认及validator均保持c5，不再收费。
- E4-01原范围余项：最终同一Conversation的多次真实整理/压缩后内容连续性缺证。当前c5 short与f287 N46是两个不同Conversation的一次完整链，不能相加代签；旧833父摘要被审计中断且最终Task/来源面已变，也不能无保留复用为此证据。root接受V4边界，后续获批最终版须补同一隔离会话多周期链，核历史关键内容、已知进展不被清空、未知不造状态、新/旧来源、实际History细节找回及Framework；N46具体长机制证据保留有效。
- 费用累计59、无存活E2E、没有新run权；原policy70/55/15不自行扩大。后续所需配额由root按最终验证方案明确决定，不能因已有配额或宽泛自主授权让执行者自启。

### R18已批准，status简化仍在对齐

用户已明确同意F04/F05两处Prompt修改；07及索引R18立即落档。root已只读核现有条目status仅枚举校验/默认/展示及内容claim比较，无按这些细分值自动归档／推进提交；Noting任务运行status与Notebook条目status是不同对象。用户提出仅保留done，root建议所有条目含Candidate统一done布尔，默认false=未确证终结、true=确证终结而非成功；具体进度/原因语义记录、done不等archive、原审批/结算/权限保持、旧immutable只读兼容。具体方案已异步询问待答，不当已批准。先独立落实获批来源句，第二句等字段收口，避免过时pending文字；不新增收费。

### R19用户确认与本次实现分工

用户已明确采用统一done方案，R18两句Prompt及R19结构口径收口，07/索引已同步。下一步A负责数据/Schema/只读旧记录兼容及专属新测试；B负责两处获批Task、六工具/权限实际请求与旧测试迁移，A的新done测试不交叉；D在最终锁版后补真实同一Conversation多周期链、F04/F05及必要长前缀，执行前另明确配额，不自启。Root亲审集成/规则检查/阶段提交；V4只完成旧c5补证，之后新最终版必须全新独立全轮Verification再Validation。只改Notebook条目状态，不改运行任务/Scheduler状态，不引入状态语义硬门禁或自动归档。
