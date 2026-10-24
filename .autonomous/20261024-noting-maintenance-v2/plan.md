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
