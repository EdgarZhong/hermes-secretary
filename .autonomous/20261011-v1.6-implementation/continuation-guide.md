# V1.6 接续实施与工作交接指导

本文给接手主 Agent 使用，尤其面向需要明确步骤的小模型。用户于2026-10-12要求暂停当前自主推进、形成详细指导，交接后继续完成V1.6。当前目标未完成；本文是执行指导，不是新产品规格，也不是验收通过声明。

仓库：/Users/edgar/code/hermes-secretary。分支：main。本文记录的产品／C13冻结基准HEAD：31b1f7570562c447c3ac8d37e423d4fc4989b3bb。后来仅提交交接文档时，HEAD可能继续前移；必须以文件hash及产品差异判断，不能把文档提交当产品变化。

来源与定稿：本文由原主会话在用户2026-10-12暂停指令后起草；该会话于最后一次事实更新（同日12:35）落盘后被中断，此后由接手会话只读复核全部锚点并补全定稿，期间未执行任何实施、测试、构建或提交。事实如有出入，以pause-handoff、锁定criteria及实际源码hash为准，不以本文文字为准。

## 0. 接手后先做的事

1. 先完整读根AGENTS.md、CLAUDE.md，不能只读本文。CLAUDE顶部“自主口径收敛 · 待用户追认”目前暂无。
2. 读本轮snapshot-index.md、baseline.txt、plan.md；读本文直到末尾，随后按各阶段阅读原规格及技能。
3. 核对git status、HEAD、分支及现存Agent／进程。不reset、不clean、不全树restore、不重建验收库。
4. 恢复C13原工作，先读实现者的pause-handoff.md。若尚未生成或不完整，对照本文和实际源码／日志补齐事实；不得凭本文替它宣称全部通过。
5. 只有用户明确授权接续之后才恢复自主目标。本文生成时目标工具状态为paused；不能由Agent擅自把paused改成active。用户在新会话明确要求按本文继续，即恢复授权。目标工具不可用时以根看板记录实际状态，不影响已授权任务的实施。
6. 按本文A→B→C→D→E→F的顺序执行。每次写代码或运行命令前用中文说明意图；每阶段结束更新根CLAUDE和已有plan，不建立第二套动态看板。
7. 接手期间不要再恢复原Codex会话或另开Agent写同一工作区：两个活动主会话会双写冲突。如确需并行，按§3.3文件归属严格划分，且根三文档同一时间只由一个会话维护。

第一轮安全只读命令：

~~~bash
cd /Users/edgar/code/hermes-secretary
git status --short
git branch --show-current
git rev-parse HEAD
git diff --stat
git diff --check
~~~

不要打印.env、完整进程环境、令牌、配置中的秘密；只读来源和hash足以核对。所有正式Python测试都通过scripts/run_tests.sh；直接pytest不符合项目规则。

交接定稿时（2026-10-12）的只读复核基线，用于确认“从暂停到现在无漂移”：

- 工作区C13六文件SHA256与pause-source-hashes.json逐项一致；五产品聚合6daf1fad…、含测试六文件f688d3c6…均未变。
- HEAD仍为31b1f757，docs/02无未提交差异，§A1所列行号即当前行号。
- criteria.json SHA256＝18b9e352…、criteria.md＝2d277ddc…，与§C1一致；proposal-review.json载七项C13-PR条件，VD081未关闭。
- ui-tui/dist/entry.js SHA256＝3fdf6116…，与§D1一致。
- Dashboard：PID62527仍在127.0.0.1:53345监听，argv与§4.2表格一致。
- §A7两条-k模式对应测试文件中实际存在的5个参数化用例（persisted in_place×2＋inheritance routes×3）。
- 根CLAUDE与本轮plan／final-delivery最后更新于暂停前（11:22），其“当前接续”止于核心1/1通过、剩余待完成；暂停后的准确剩余状态以本文§A5及pause-handoff第4／5节为准。进入§B时按其第4步更新根CLAUDE，此前不要把根CLAUDE的旧表述当成比本文更新的状态。

接手时重跑上面命令并与本清单对照；任一项不符，先停下查漂移来源（谁改的、何时改的、是否合法），不盲目续做。

## 1. 最终目标与禁止偏离的边界

完成公开Hermes Secretary V1.6及未修订V1/V1.5契约，关闭范围内问题，通过当前交付版本的独立Verification与真实用户Validation，完成主会话证据复核、最终文档和本地提交。不push，不部署。

实际顺序：实施及正式接线 → 主会话review／集成 → 全范围独立Verification → 真实用户Validation → 主会话最终判定。失败则修复并按套件重新独立复审，不能用一份旧PASS覆盖后来的产品变更。

必须保持：

- Hermes-first。Noting只请求父压缩；执行、成功结果发布、active Turn协调及Continuation归父原生机制。
- “不启用即原生”：从未启用／非eligible／Aux路径不得因Secretary改造而变行为。不能为了测试变绿调整原生模型层、provider、路由、工具协议或root结构。
- Notebook为派生状态；原对话为事实源；Main只读Notebook，Noting写。Agent无item生命周期查表／找回工具；系统内部可取当前Snapshot引用的正文，归档项不可见、不可恢复。
- 父root、工具列表／完整Schema／消息冻结前缀在Noting所有后续请求保持；新权限与工具声明只追加到task后缀，执行权限仍白名单。不独立实现一套Agent Loop或provider适配。
- state.db只加Secretary自有表，不改原表ownership。开发结构变更不用迁移；当前C13无schema变更，无需重建已有验收库。
- 已持久化的历史原文不能为上下文清理而删除。
- 所有状态、任务、线程及子进程显式绑定所属profile，不硬编码真实~/.hermes。
- 不新增通用调度器、admission gate、epoch／revision／pending协议、API hierarchy。
- Idle trigger沿事件注册定时器：Turn结束arm，开始cancel，一周期一次；不能退回全局每5秒扫一次。host tick／reaper已有其他职责不代表可以承担替代Idle语义。
- 保持十项冻结检查及原阈值。文档长度不做门禁。新函数CC≤20、行数≤300、嵌套≤6、文件≤2000；原已超标单元自身超标指标不能增。
- 范围内失败或证据不足不能写“风险可接受”代替关闭；无统计数据不能估算剩余缺陷概率。

## 2. 权威依据与阅读顺序

| 文件 | 用途／优先级 |
|---|---|
| 根AGENTS.md | 用户规则、边界、环境、正式测试、协作规则 |
| 根CLAUDE.md | 当前任务和进度；历史记录不是当前PASS |
| 根README.md | 稳定入口及开发环境，不承载动态看板 |
| docs/01-personal-hermes-v1-first-fork-iteration.md | 公开首轮目标、边界和完成定义 |
| docs/02-noting-system-specification.md | 现行权威；V1.6定案及§5.12 Target优先 |
| docs/04-hermes-secretary-v1.5-implementation-spec.md | 未被02修订的增量契约；尤其§7.3六类真实用户旅程 |
| 本轮snapshot-index.md | 四类依据入口、C01–C13用户确认表 |
| 本轮baseline.txt | 初始冻结及后续用户授权增量的完整提交hash |
| 本轮plan.md | 任务、整改及关闭条件 |
| 本轮verification.md／validation.md | 各自独立门禁报告，保留原失败和版本历史 |
| 本轮final-delivery.md | 主会话当前判定；现为未完成快照，最终要重写为真实结论 |

本轮目录均为.autonomous/20261011-v1.6-implementation/。

主会话适用技能在/Users/edgar/.agents/skills/。已使用autonomous-run套件，后续阶段行动前重读相应SKILL.md；新接手主会话按autonomous-run阅读契约完整读七套件：

- autonomous-run
- ask-and-align
- writing-plans
- executing-plans
- spec-implementation-review
- real-user-acceptance
- delivery-evidence-review

以上路径属于原会话环境。若接手运行时不同（如AutoClaw等），按同名skill在当前环境定位（例如skill://autonomous-run）；确实读不到同名套件时，以根AGENTS、本指导各阶段门禁与验收原文、冻结01／02／04为准继续执行，不得因环境差异降低门禁、省略独立审查或改用自定流程。

依据文档不能由实现者随意修改来迁就代码。必要局部工程空白按根AGENTS授权自主收敛；若改变用户预期，立即登记根CLAUDE顶部待追认区域，并在下一次交互优先汇报。用户明确语义不能自主改。

不读取docs/archived，不从旧规格猜测。docs/06-ui-read-api-discussion.md、README中对应未提交索引是另一项讨论，未纳V1.6冻结依据。

### 2.1 本轮最容易做错的用户确认

| 编号 | 必须保留的语义 |
|---|---|
| C02 | 禁Agent查item历史／找回；不是禁止系统内部按当前Snapshot ids读取 |
| C03 | Noting dispatch后新增／替换memo保留；用简单正向行身份及同事务消费，不建复杂revision协议 |
| C04/C05 | Finish只一条正常系统英文，说明已处理memo已清空；不是宣布所有memo清空 |
| C06 | Verifier先无干扰仅规格建判据；主Agent提方案，Verifier依据判据评审；研讨进报告、delivery和最终汇报 |
| C07 | 最近实际Main执行源External拒绝Noting时，Force／Idle／catch-up都有对应Framework提示；不是按provider或模型名猜External |
| C08 | Noting只触发父原生压缩，不自己读取父DB拼tail／判断active／重造Continuation |
| C09 | 原生compact请求成功准入后，后续取消／失败不撤Snapshot提交机会和合法Finish；仍过原Anchor／enablement Gate |
| C10/C11 | Main notebook_show结果只success/notebook；notebook六键为四区＋last_update_time＋裸anchor_message_uid。内部Snapshot审计及Noting工作态不变 |
| C12 | session_history成功结果只一份conversation_ref；row单message_uid／timestamp／role／content，search原truncated保留；read原输入兼容，不加裸UID selector |
| C13 | Force dispatch通知只属于当前compaction区间；父成功commit后旧通知在所有active继承渠道及busy队列都过期；原历史保留；cancel／fail／noop不过期 |

精确Finish正文：

~~~text
Background: notebook updated at <snapshot commit time>. Processed memo entries have been cleared.
~~~

精确Force正文：

~~~text
临近上下文上限，notebook 更新任务已派发。建议尽早压缩，并在此提示：compaction 时将本消息之后的内容重点保留。
~~~

正文不是生命周期识别条件。C13必须正向producer身份，不能用中文字符串搜索删除普通消息。

## 3. 交接时已完成什么、还剩什么

### 3.1 产品与阶段版本

| 版本／工作 | 状态 |
|---|---|
| 初始冻结fc2668310bff783dde0d6f1cee01b8de99a43cb9 | 原始依据；增量见baseline |
| ce2fa6f4760709275ae9ea87050a5d3996c092c8 | 旧全129 Verification通过，后来的C10–C13／显示修补不由它自动覆盖 |
| 551ca53ba4f33441781304a761d92aac27a94d3c | C10/C11 Notebook精简产品已提交；13项定向证据 |
| 9fa27767e8ae15ec72cfec96be106dfc0931ed55 | C12输出口径冻结 |
| fb8fb696d5a3048ab07fa6ef68c034eec7542503 | C13初始生命周期口径冻结 |
| bc9cd6d7a16700618410cd41dbb21a4bf4e5de6b | C12＋VAL01/VAL02实现已root接收并提交 |
| 31b1f7570562c447c3ac8d37e423d4fc4989b3bb | C13同active Turn queued通知迟到边界澄清冻结 |
| 工作区C13六文件 | 未提交、未root最终接收、未当前独立关闭 |

基础能力已经实现集成：INSERT-only item版本、Snapshot ordered ids、lineage、三Noting工具、永久archive、secretary_task显式delivery_mode、Prompt Targets、memo消费、真实Turn事件Idle timer、Reminder batch/ACK、Framework双写／宿主显示、Anchor、overflow以及History原文查源。不要重新实施整套V1.6。

### 3.2 仍需完成的顺序

- A：恢复并收尾C13当前六文件，完成必要定向证据、主会话正式接线review。
- B：本地产品阶段集成提交，明确源hash／测试适用性，不能stage旁支。
- C：新独立Verifier已建98条全范围判据，恢复其阶段B实现调查；全部范围内阻断关闭。
- D：保留现有验收库、Cold升级同隔离Dashboard，核来源与产物。
- E：全新独立Validator，完整重核范围并实际补完／复验用户旅程；既有证据按源码影响复用。
- F：主会话delivery-evidence-review，两个当前版门禁与整改均关闭后，最终文档及本地提交。

开发只剩一个已知核心修补，不代表实际Validation基本做完。目前U01主体做完、U02/U03部分，U04–U08尚未闭环。

### 3.3 当前未提交文件的归属

C13产品／测试六文件：

~~~text
agent/compression_force_notice.py                 新文件
agent/conversation_compression.py                 已修改
agent/context_compressor_summary.py               已修改
secretary/framework_messages.py                   已修改
secretary/noting_runtime.py                       已修改
tests/secretary/test_force_notice_compaction.py    新文件
~~~

本轮根看板／内部报告有未提交状态更新：

~~~text
CLAUDE.md
.autonomous/20261011-v1.6-implementation/baseline.txt
.autonomous/20261011-v1.6-implementation/plan.md
.autonomous/20261011-v1.6-implementation/verification.md
.autonomous/20261011-v1.6-implementation/validation.md
.autonomous/20261011-v1.6-implementation/final-delivery.md
~~~

另任务：README.md中的docs06索引、docs/06-ui-read-api-discussion.md和.playwright-mcp/。不要覆盖、清理、顺手stage。不得git add .或git add -A。

## 4. 环境、状态库和恢复入口

### 4.1 开发环境

- 官方PM构建的工作区.venv，Python3.14.7。
- 官方uv.lock原SHA256：2bc4db483e9cba927cd7147f9ccbb09635f85bb3f1f36d6e9d51d06b65d1c67e。
- 不裸pip／uv修改PM环境，不重解析锁文件，不为一个import失败重装全套。
- Main／Noting真实运行：DeepSeek官方deepseek-flash思考模式，Chat Completions。凭据仅获授权profile的ignored.env。
- 不Codex App Server／Codex Proxy、不fallback到它们、不改另一个Dashboard配置。
- 所有测试状态／basetemp在仓库ignored.hermes-dev。正式验收库不能在测试中复用。

相关命令模板，实际恢复后按变化选择，不要求全部重复：

~~~bash
mkdir -p .hermes-dev/v1.6-evidence/resume-c13/home
HERMES_HOME="$PWD/.hermes-dev/v1.6-evidence/resume-c13/home" HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/secretary/test_force_notice_compaction.py -j 1 --basetemp="$PWD/.hermes-dev/v1.6-evidence/resume-c13/basetemp"
~~~

已有测试首层fixture禁止httpx同步／异步HTTP，并控制摘要／provider返回，运行真实Main Loop、SessionDB和压缩器。接手必须保持哨兵；若增加流式等分支，拦实际传输接缝而不是假设某个patch能盖所有通道。受控provider不是实际模型调用。

### 4.2 官方验收实例

| 项 | 暂停时事实 |
|---|---|
| 地址 | http://127.0.0.1:53345 |
| 服务器 | PID62527；接手重新验证，不能盲信PID未复用 |
| profile | /Users/edgar/code/hermes-secretary/.hermes-dev/v1.6-validation/dashboard-final-4743943e |
| 运行产品 | 旧ce2fa6f，尚未升级 |
| 数据 | 3 sessions／79 messages／2 notebook Snapshots |
| 配置 | global noting=false，Idle2秒，local偏好on，memo空 |
| 活动 | 原Main及两个Noting已结束；原两对PTY退出；无当前模型请求 |
| Main physical session | 20261011_231755_2fc826 |
| Conversation ref | conv_fde00abd17fd4ae09d9349c583083ba9 |
| 浏览器 | 原IAB browser2/tab1已失效，不能直接接着点旧句柄 |
| 实际surface | 官方Dashboard CHAT → node ui-tui/dist/entry.js → python -m tui_gateway.entry；不是CLI fallback |

暂停只暂停开发，不要求删除实例／验收数据。不要把服务器health200说成UI或用户验收通过。恢复一次合法CHAT连接，核对应Conversation归属，避免多开PTY导致owner／会话误判。

### 4.3 严禁混入测试或清理的私人Pi库

~~~text
/Users/edgar/code/hermes-secretary/.hermes-dev/chat-migration/pi-personal-history-20261011T143110Z/profile/state.db
~~~

这是用户授权的正式格式私人迁移库，已完成，暂放一边。48 Conversation分支、5986DB消息行；有完整原件／归档／来源映射。它含真实私人聊天，不是随时可删测试库；不读取到Validator、不接Dashboard、不重建、不删除、不入Git、不跑Noting。

## A. 收尾C13：具体实施指导

### A1. 先恢复依据、当前源码及证据

必读原文，以31b1f757版本行号定位；修改文档后要重新核行号，不仅看数字：

| 02章节 | 此版本行范围／目的 |
|---|---|
| §2.2／§2.3／§2.4 | L273–356，History原文、逻辑身份、Full不能损坏 |
| §2.6 | L575起，Anchor／Finish标记及后续活动边界 |
| §5.6 Framework Message | L1642–1698，核心C13在L1669，同Turn迟到队列也必须过期 |
| §5.9／§5.10 | L1774–1827，原生父压缩职责、请求准入与Snapshot提交区分 |
| §5.12 | L1844起，冻结Prompt及工具面不能顺手改 |
| §6.11／§6.12 | L2358起，正式压缩及恢复验收条款 |

研究／研讨材料：

~~~text
.hermes-dev/v1.6-evidence/force-notice-boundary/proposal.md
.hermes-dev/v1.6-evidence/force-notice-boundary/proposal-source.json
.hermes-dev/v1.6-evidence/verification-delivery/proposal-review.json
.hermes-dev/v1.6-evidence/force-notice-boundary/pause-handoff.md
~~~

最后一个由原timers在暂停时交回；其状态必须与实际文件对照。proposal已经root接受、独立Verifier按原判据接受方向；七项实现关闭条件尚未正式审查。不能把提案接受当成产品PASS。

### A2. 需要实现的结果

原问题有两个入口：

1. 已落盘Force可被原压缩器留在protected head／tail／verbatim／摘要／最新user replay；root已用真实compress复现60→10仍旧UID／正文在。
2. active Main Turn中Force先排queue，父中途压缩成功后Continuation仍同一run_conversation；Turn结束才flush旧queue，把已过期通知写入新区间。Conversation ref／Turn id不变不能代表区间未变。

仅删除已落盘消息无法修第二个问题。只在Turn结束判断／只读compression_count也不成立。

成功判定分两层，严禁混淆：

| 场景 | 成功条件 | 后果 |
|---|---|---|
| C09 Noting任务terminal | 原生compact请求按既有契约成功准入（或已有inflight／无需压缩条件成功） | 可以过Snapshot Commit Gate；后续取消不撤合法Snapshot／Finish |
| C13 Force区间到期 | 父这一次真实数据库compaction事务已经成功提交 | 旧Force active／queued过期；后续loader失败也不能把旧通知写回新区间 |

### A3. 当前方案及实际接线

- Force实际生产处：secretary/noting_runtime.py::maybe_admit_force_from_pressure，增加内部display_metadata.noting_force_dispatch=true以及原publisher的_producer=force_dispatch。
- 正式producer调用点在agent/turn_context.py和agent/turn_preflight.py的Main压力检查；必须证明它们与本次capture→commit的线程／安全消费窗口匹配，不能只说“有Turn lease”。
- secretary/framework_messages.py沿原锁capture同parent／ref旧Force queue对象身份，只retire这些对象；不同ref／DB／新通知／Finish／External不清。
- agent/compression_force_notice.py为原生单attempt工作plan、正向身份筛选、过滤副本、摘要当次重点、精确carry和成功退队专责sibling；不是第二压缩器。
- agent/conversation_compression.py::_run_summary_phase在adopt grown parent后capture，原始messages保留作为rollback／coverage，工作副本不含已识别旧Force。
- 同模块compress_context中的候选比较用filtered baseline；通知减少一行不能冒充“成功压缩”；失败／cancel／noop返回原输入。
- 同模块_commit_compaction／_publish_rotated_compaction在archive_and_compact或publish_compression_child真实返回下一语句retire；fence仍在，早于update_system_prompt、rebind及loader。
- 只有Force plan且DB成功后再出错，沿原native request failclosed阻止旧上下文发wire；无Force路径不新增失败处理。
- context_compressor_summary.py将后段真实材料只作为本次aux summary focus。旧Force正文不作为素材，临时指引不写回Parent summary／root／Framework。
- in-place通过原carried_messages精确行身份保留合法tail；Force支路tail_count=0，verbatim rejoin不能又加回原N造成邻行误supersede。
- coverage／watermark保完整原original／verbatim含旧Force，原文继续History；候选Active不再带旧Force。

注意原_candidate_rejected函数完整职责已经移到新sibling，并以原模块同名import保留接缝；内部按运行时从原模块import动态依赖，避免测试patch错位置与循环import。不要为了减少行数再拆无关核心职责。

### A4. 当前白名单

只改上述六个产品／测试文件。原派遣另允许必要tests/agent/test_context_compaction_request.py，但当前未改。不要顺手改DB、Snapshot／Reminder／Registry、provider、Dashboard后端、toolsets、全局规则或docs06。若真实反例证明现有DB接口无法保障语义，先记录具体断点并由主会话向独立Verifier提最小方案，评审后再扩边界。

### A5. 已有证据与尚需确认的地方

根会话已完整读实现者pause-handoff并核当前源码。五产品聚合SHA256为6daf1fad3ad003b5b7944b1ddc13c81df65fa2fb41014cadf2affee42cfc4889；含测试六文件为f688d3c6a3e33d6117fa14d9d694762393003945f6dd8f3389647f1b4911499b。完整pause-source-hashes.json、pause-final.patch及pause-source/字节快照保留。各日志计数有重叠，不累加成总测试数。旧日志未逐run采集sourcehash，当前manifest不能倒填为当时证据；已知时间顺序仅支持对应适用性判断。产品最后改于11:21:54，测试最后改于11:24:08（2026-10-12 +08）：

| 日志／观察文件（都在force-notice-boundary/） | 记录 |
|---|---|
| tests-first.log | 首批1通过／2失败，保留原失败 |
| tests-persisted.log | 2失败，为in-place／rotation返回值预期调整阶段；不是当前最终PASS |
| tests-routes.log | 定向9通过，继承／失败代表路径 |
| tests-priority.log | 2通过／1失败；误把原样保留的tail要求进aux focus |
| tests-priority-fixed.log | 更正摘要素材预期后1通过；保留首失败 |
| tests-commit-boundary.log（11:22:53） | 最终产品后2通过／1失败；两个通过是next_interval与expired_verbatim，loader首例在下一Main二次观察fence已释放时误取attr失败 |
| tests-loader-fixed.log（11:24:11） | test-only修正后loader＋next_interval 2/2；第二loader调用来自下一Main，不能当重复commit；expired_verbatim不在此次重跑 |
| tests-native-regression.log | 两文件18通过，原native request及delivery适用回归 |
| check-mid.log／check-before-regression.log | ruff／health两相关检查ok，6文件0阻断／0提示；不是十检查全套 |
| same-turn-observation.json | 真实Main run_conversation两wire；pressure Force准入；实际DB压缩；第二wirequeue空 |
| commit-before-loader-observation.json | 实际DB成功，loader报错，旧queue已退；先观测fence在，下一Main重试时fence已释放；live结果未成功发布 |
| metrics-before.json／metrics-after.json | 健康自身基线／阶段结果；最终修补后需要确认是否仍对应当前源码 |

最新新增测试的准确状态：

~~~text
test_next_interval_formal_force_producer_is_not_retired_by_old_attempt
    最后产品之后通过两次；第二次是test-only更正后的版本，不累加。
test_expired_verbatim_force_preserves_adjacent_human_history_exactly
    最后产品之后在tests-commit-boundary.log通过；后来测试文件另例更正，
    该例正文及产品未变，未再重跑，不应强行当未执行。
test_real_db_success_expires_queue_before_native_publication_loader_failure
    test-only更正后通过；真实DB成功、旧queue消失、第一次fence仍在，
    第二次下一Main入口fence已释放且沿原failclosed拒旧wire。
~~~

当前明确剩余事项：

1. 最后retire／carry变化之后，persisted in-place／rotation及protected-head／verbatim／latest-inflight代表routes仍需必要窄复测；旧9/9不直接倒灌。exactcarry邻行专门用例已有最终产品PASS，不为报告接收再重复。
2. noForce globaloff／Aux专门新对照尚未添加；现有最终native选中18/18有部分证据，需结合实际接线核PR07覆盖。普通同文伪metadata目前只有noop反例，成功压缩不误删可取一个必要对照；避免机械模式乘积。
3. capture→commit生产者闭集仍需root检查三个正式Main pressure seam及同步安全点；没有证据就不能靠Turn lease猜测。
4. 最后test-only修改之后未再跑ruff／health；恢复时最终stage相关冻结检查即可。C13完整root review／阶段提交／当前独立Gate及实际UI仍未执行。

这些是续接任务，不是要求把当前所有用例重新跑一遍。最后修改和日志的准确先后以pause-handoff第4节为准；日志缺当时hash限制必须保留。

### A6. 必须交回的七项及review判据

实现者交回：对应条款、实际变更、正式路径、验证结果、缺口、接口影响、建议下一步。日志要附命令、控制点、源码hash、观察边界、首次失败及修复理由。root亲自review，不能只复跑它测试。

独立方案评审七条件必须逐项准备证据：

1. 正向真实producer＋Framework形状＋逻辑UID／owner。普通同文user／伪标记／其它producer不能被误删；没有新模型输出字段或迁移。
2. 真实DB提交成功关口之后、fence释放前、loader前退队。DB后失败不能恢复旧wire；DB前失败／取消／noop／anti-growth／拒绝保原输入及queue。
3. capture覆盖所有受支持正式Force生产路径；同TurnContinuation／Turnend无旧通知；下一新区间Force及其它queue不误清；reset／branch／别owner不受影响。
4. protected head／tail／verbatim／摘要／replay代表渠道不续带；真实in-place及rotation History原UID／正文保存；合法foreign tail／邻行身份不损；never-appended不造audit／pending。
5. filtered no-progress不能把删除通知冒充成功；原生当前上下文／Continuation协调保持，Noting没有读库重建父。
6. 真实后段材料优先只用于单次aux summary，排队通知不伪造位置；旧正文和临时指引不被持久化回Parent。
7. 无Force原生行为保持，已有Force后关闭仍到期；Aux／未启用不新进路径，Snapshot／Finish／External和冻结Child prefix保持原契约。

不是每个位置与每个模式都跑笛卡尔积。用各渠道代表＋关键交错取得真实机制证据，静态核查剩余适用接缝。若机制缺失，即使某项测试通过也不能接收。

### A7. 推荐复测范围及停止扩大规则

先核现有日志／hash。只补最后产品变化影响的persisted及inheritance代表路径；loader／nextinterval／exactcarry专门观察与最终产品相符，勿重复。可先选以下5个参数化例，保首次结果、禁自动重试；如接手又改产品，按影响再定：

~~~bash
mkdir -p .hermes-dev/v1.6-evidence/resume-c13/home
HERMES_HOME="$PWD/.hermes-dev/v1.6-evidence/resume-c13/home" \
HERMES_PYTHON="$PWD/.venv/bin/python" \
scripts/run_tests.sh tests/secretary/test_force_notice_compaction.py -j 1 --file-retries 0 \
-k 'persisted_force_native_compaction or native_force_inheritance_routes' \
--basetemp="$PWD/.hermes-dev/v1.6-evidence/resume-c13/targeted-temp"
~~~

补noForce／普通同文成功对照时，仍从真实正式Loop／DB／压缩入口取得结果，不写源码字符串断言，不控制掉待验机制。NoForce主原生回归18项和主要sameTurn核心1/1的既有证据按实际源码影响复用；若新改动确影响sameTurn再定向补，不固定重跑。

每个新run在开跑前保存实际六文件hash、命令及隔离profile；完成后确认源hash未变、记录结果／耗时／日志定位。不要重复1574项扩大检查或真实29次API取证只为了接收报告。

A完成条件：当前产品源码与有效证据对应，七项handoff齐，root已核正式接线及边界，无已知范围内代码缺陷留在施工态。此时仅可进入B，不能宣布整版完成。

## B. 主会话集成与本地阶段提交

1. 确认实现者停止写共享文件，核所有返回源hash。
2. 读六文件差异及真实上下游，重点DB-success退队关口、当前Main安全消费者、后续loaderfail／Turnend、Full／History carry。
3. 将未证项转plan整改，不从实现者自评复制“已关闭”。主会话review记录放ignored证据目录。
4. 更新根CLAUDE当前状态、plan的C13／C12／VAL项阶段状态、final-delivery的未完成说明。不要改独立门禁矩阵结论。
5. 显式stage本轮六文件及本轮必要文档，保留README／docs06／.playwright旁支。
6. 使用官方检查入口核实际stage。相关检查可先选择footguns／lazy-deps／ruff／health；冻结十检查不放宽。此前大型检查只按源码影响复用；若必须新增一次阶段检查，记执行者／版本／范围／次数／耗时，不无条件又开全套。
7. git diff --cached --stat／--check／--name-only及完整差异核秘密／个人化／旁支。
8. 本地commit描述实际修补，注明定向证据及尚未当前门禁。把完整commit传给Verifier，不只短hash。

显式stage示意，执行前核是否有新必要文件：

~~~bash
git add -- \
  agent/compression_force_notice.py \
  agent/conversation_compression.py \
  agent/context_compressor_summary.py \
  secretary/framework_messages.py \
  secretary/noting_runtime.py \
  tests/secretary/test_force_notice_compaction.py
.venv/bin/python scripts/check --staged --only footguns,lazy-deps,ruff,health
git diff --cached --stat
git diff --cached --check
~~~

文档按实际归属另外显式stage（本轮实际更新过的根CLAUDE、plan／final-delivery等内部报告，以及本指导continuation-guide.md），不把此示意盲复制成全文件提交。commit授权已包含在本轮自主授权，无需再次问常规本地提交。实现子Agent默认不提交。

## C. 当前全范围独立Verification

### C1. 已有独立起点可继续使用

当前全新无父历史的verification_delivery已经完成阶段A：只读指定冻结01／02／04，建立98条判据并落盘。初始及C13澄清变更都有保留记录；尚未调查施工产品、没有当前PASS。

~~~text
.hermes-dev/v1.6-evidence/verification-delivery/criteria.json
.hermes-dev/v1.6-evidence/verification-delivery/criteria.md
.hermes-dev/v1.6-evidence/verification-delivery/criteria.lock.json
.hermes-dev/v1.6-evidence/verification-delivery/hashmanifest.json
.hermes-dev/v1.6-evidence/verification-delivery/criteria.initial.20261012T023510Z.json
.hermes-dev/v1.6-evidence/verification-delivery/proposal-review.json
.hermes-dev/v1.6-evidence/verification-delivery/root-evidence-index.json
~~~

锁定98条criteria.json SHA256：
18b9e352d23934e460479043be48cd8a9f3d44e267bb0e2834475d359ad2c3b0

criteria.md SHA256：
2d277ddcb905440a5b07f59a107c3406606e24f979b7d327a92e7e3b3659370c

旧129条和新98条组织粒度不同，不机械要求数量相同。必须核全范围覆盖；不能少读旧契约／关闭行为。旧ce2fa6f报告是证据参考，不是新判据来源。

如果该Agent仍可恢复，直接followup进入阶段B；不要再对每一碎片spawn verifier。如果Agent无法恢复，另建fork_turns=none按仅规格先建判据重做完整新审查，不能让接手主Agent自己审核自己。

可恢复性说明：verification_delivery、timers、validation_final都是被中断原Codex会话内的子Agent；在全新会话（尤其换运行时）接手时通常不可直接followup，即按“无法恢复”分支执行。新Verifier仅规格重建判据后，必须与已锁定98条（含C13覆盖，SHA256见上）逐条交叉核对：新增判据注明规格来源；锁定集已覆盖而新集缺失的要求，回到规格原文确认后补入，不能静默缩水；两集组织粒度不同按映射说明，不按数量机械对齐。锁定criteria是核对参照与覆盖底线，不是降低独立性的捷径，也不必逐字照抄。

### C2. 阶段B委派内容模板

~~~text
目标：调查并审查完整V1.6及未修订V1/V1.5契约，待审产品为<完整commit>。
依据：本轮snapshot-index／baseline定位的冻结01／02／04，初始fb8fb696原文＋31b1f757 C13段override；已锁定98条独立判据保持。
已完成阶段A，仅规格判据；现在放行阶段B读根AGENTS／README、当前完整产品、正式接线和证据。root提案／旧报告只能用于核事实，不反向降低判据。
产品只读。写白名单：本轮verification.md，ignored verification-delivery证据。六节及全矩阵保留原历史，追加本次调查／复审；不重写旧失败为PASS。
证据入口：root-evidence-index.json＋新C13handoff／rootreview／最终source manifest；逐项评估源码适用性。
不派生、不修改产品、不运行模型/API、不重启Dashboard。有效大检查和真实API按版本影响复用，不重复昂贵取证。必要安全定向反证可以取得真实DB／Loop证据，使用官方runner、隔离HOME和HTTP禁止哨兵。
从正式入口检查机制、权限、数据、失败、模式、关闭、profile隔离以及方向明确但接线未完全写出的要求。98条全范围之后复核旧VF/VFR与新C10–13、VAL显示修补及其影响，不只验C13。
发现先落原判据＋事实＋差异＋影响。root提方案，审查者依据已锁定判据评审。必要关闭证据逐项列，不迁就代码。
返回当前commit覆盖统计、具体源码／证据、未关闭项、研讨与六节报告定位。
~~~

默认按根AGENTS用gpt-6.1-sol／high、fork_turns=none；用户明确指定其它模型时按用户。子Agent不再派生。接手小模型可以做主会话，但门禁必须独立；工具环境若没有独立Agent能力，不能伪称同一上下文审查为独立，需准备完整审查包交给可独立执行的会话，实际门禁未执行前不宣布完成。

### C3. 可复用的关键证据

| 证据 | 可支持的范围／限制 |
|---|---|
| history-output/handoff.json | C12四文件、39/39、四相关检查，Main／Noting共用handler，DB真实read／截断／隔离 |
| notebook-ai-view-manifest.json | C10/C11正向六键投影、13/13、null／gates／归档／deepcopy；不是新真实模型输出 |
| framework-visibility/handoff.md | VAL01/02正式CLI／TUI／Gateway与长Slash渲染；47回归、30UI、tsc，原失败保留 |
| integrated-output-ui-root-review.json | root集成接收，不是独立PASS |
| framework-visibility/official-build-manifest.json | 官方产物构建，不是UI验收 |
| verification-final/verification.final-manifest.json | ce2fa6f旧129全范围调查及各证据版本映射 |
| native-compaction-fix/real-native-handoff.json | 55e92版本真实normal／forced／overflow，实际publication及下次wire；按C13无Force路径适用性核对 |
| 原verification.md | 全范围旧VF／VFR发现、root提案／Verifier评审及关闭链；不是新规格来源 |
| 原validation.md及validation-final/ | 旧ce实际用户结果与两个真实UI失败；当前未闭环 |

证据均在.hermes-dev/v1.6-evidence/，正式报告在本轮目录。root-evidence-index只locator；其中sha256_at_index是当时hash，持续维护报告可变，不能因报告变化抹原记录或说旧hash就是新报告。

大范围已1574通过／1macOS文件系统跳过、十冻结检查ok，适用源版本见旧manifest。macOS证据不宣称Linux／Windows实测；跨平台未覆盖按规则记录，不伪造sys.platform。

真实DeepSeek特殊三组22 HTTP200在55e92（normal7／forced10／overflow5），原失败7次保留，原专门取证累计29/30。这是那一项probe的账本，不是后续真实用户Validation的全局30次上限。不要因误读上限删用户场景；也不要为无变化重复三组昂贵API。

### C4. Verification通过条件与发现处理

逐条符合或有依据不适用；无违规、无证据不足。阶段不适用的用户验收／最终交付要求仍由后续完成，不是整体豁免。

报告必须六节：对象／概览、独立要求与覆盖、逐条实现证据矩阵、核心目标和方法、发现／优先级／范围外、修复复审。每条论证链包含原文→不变量／判据→正式路径→条件→方法→观察→结论。

若发现代码问题：先记plan，root调查提出最小方案→Verifier按原判据评审→授权内实施修补→定向证据→全新独立全轮复审。不能审一个碎片就派一次Gate，不降低规则阈值。实质工程研讨同步final-delivery和最终用户汇报。

root亲自接收全范围报告、核核心结论与适用hash，缺项退回补审。只有当前产品全范围阻断关闭才进入D／E。

## D. 保库升级官方Dashboard

### D1. 已构建产物，不必再盲构建

官方构建：node scripts/build/tui.mjs，源版本bc9cd6d7a16700618410cd41dbb21a4bf4e5de6b。

~~~text
ui-tui/dist/entry.js
SHA256 3fdf6116f506a757f7567b1653e759985e07a33c8930860589e5d56350770140

ui-tui/src/app/createGatewayEventHandler.ts
SHA256 570b3752a0feca93b4b3dd1e377a439e2a30abb8aaacadbc28b30e3c3ace69e8

ui-tui/src/app/createSlashHandler.ts
SHA256 83c7922e1ee591513c58440f23031dcb6725d432ca145dab907fcca75a8ddf7e
~~~

manifest／log：framework-visibility/official-build-manifest.json及official-build.log。C13当前只Python，不改变这些TUI源码；恢复时核hash一致即可复用build。若真正改TUI，再用官方builder，不npm install重装，不改lock，不拿source-alias test说官方build已成功。

### D2. 使用现有保库升级脚本

~~~text
.hermes-dev/v1.6-evidence/dashboard-final-prep/restart_preserving_profile.py
~~~

这是root已准备但未执行的协调脚本，先读它再执行。不要复用start_final_dashboard.py；后者fresh库guard，不应删已有库绕过。

前置检查：

- 当前产品已提交且Verification通过，产品源码无dirty。
- 原profileglobalfalse已保存；没有活动Main／Noting／compaction，原PTY退出。
- 当前端口owner／PID／创建时点／HERMES_HOME／argv实际匹配，不能盲kill62527。
- 对.env／config只hash，不打印凭据；counts与原3／79／2可对账。如有合法后续差异先查来源，不删库强归零。
- buildartifact及源hash适用。
- 脚本只SIGTERM确认本profile的server／子树，官方gracecleanup；若未停，检查实际owner，不SIGKILL其他进程。

按实际完整commit和实际PID运行：

~~~bash
.venv/bin/python   .hermes-dev/v1.6-evidence/dashboard-final-prep/restart_preserving_profile.py   <待验完整commit> <已核实的旧Dashboard_PID>
~~~

尖括号是需要先填值的占位符，不直接执行。脚本会校验HEAD，停止旧server，保count及配置hash，启动：

~~~bash
HERMES_HOME="/Users/edgar/code/hermes-secretary/.hermes-dev/v1.6-validation/dashboard-final-4743943e" .venv/bin/python -m hermes_cli.main dashboard --host 127.0.0.1 --port 53345 --isolated --skip-build --no-open
~~~

此手工命令只说明实际入口；正常优先用协调脚本，避免重复启动。启动环境不继承乱七八糟的APIkey，由原profile正式加载.env。

脚本产物：upgrade-readiness.json、upgrade-source-hashes.json、upgrade-server-<commit前10位>.log。核health.body.commit／home200／count／配置hash一致。readiness不等UI／模型验收。

PID已变或旧server不在时：先只读确认原profile无活动worker、端口free；保同库／配置，用同官方入口启动并记录前后manifest。不要硬改script guard放过未知owner；若调整协调脚本，只是本地证据工具，不改产品启动机制。

## E. 完成真实用户Validation

### E1. 派全新独立Validator，计划先审后执行

旧validation_final已完成安全交接，原报告有真实U01/U02/U03及失败事实。由于随后产品修补，正式当前版验收由全新fork_turns=none第三方执行；别让实现者／主会话自己扮“独立Validator”。

默认gpt-6.1-sol／high，用户模型指定优先。无派生、只读产品，只写原validation.md追加本次六节及ignored独立证据目录。实际操作仅指定验收profile及合成数据，配置修改／Memory批准也仅该profile。与新Verifier分开，不能继承主会话讨论历史。

委派模板：

~~~text
完成当前<完整commit>全部适用公开V1.6真实用户验收。
先完整读autonomous-run／real-user-acceptance、本轮索引／冻结01/02/04／根AGENTS和稳定README。plan场景只是线索，自行从原需求重核全范围。
官方唯一获授权profile／URL／原Main与Conversation见交接；产品只读、无私人Pi、无真实HOME、无其它Dashboard。
先按模板在原validation.md追加本次六节计划，列目标、起点／历史、输入、步骤、预期、实际观察、证据及状态；root过目后再操作。
复用旧有效用户准备和同版本适用机制／模型证据；说明源码影响，保留旧失败。旧U01主体不用重新构造全部长原文／压缩旅程，新C12输出和C10/C11必须看实际模型工具返回。VAL01/02必须原用户场景实际复验，不能DB替UI。
未完成Memo／Persistence／Reminder／Cold／Full及branch旅程保留，不能改NA省略。
实际模型仍官方DeepSeek deepseek-flash思考。只经实际Dashboard CHAT合法输入与工具流程，Schedule由真实Noting产生，钟表真实流逝，不能改due／插Registry／伪tool。
Cold重启由root协调，同库同profile保存，不重建。Full／DB／日志只补诊断，用户呈现仍亲眼操作观察。
无产品修补、无提交、无其它Agent。发现记root，原场景及影响链条复验；不无控制重复随机模型尝试。
返回当前来源hash、全部目标场景覆盖、原失败复验、输入输出／持久结果证据及六节结论。
~~~

root先完整读新计划并对04 §7.3六旅程及02范围查漏，过目不降低预期，放行再执行。本文八场景为已有合法覆盖线索，不强迫新验收者以主会话解释重写预期。

### E2. 浏览器操作与结果证据

用当前环境提供的合法浏览器工具，按其首调用／文档要求初始化；当前tab失效需要重新获取或建唯一页。不能shell启动自动浏览器、读取私密浏览器状态或靠Playwright旁支绕环境约束。

接入后核URL、CONFIG、CHAT及具体Main Conversation；恢复原session，不误新建并把另session结果当旧历史。会话列表用户可见名称／ID按实际入口选；实际officialsession.resume也可研究，但验收应沿公开用户流程。

保存合成输入txt、真实DOM／截图、实际工具结果／provider_neutral_request、按只读capture脚本补Full／History／Notebook。不要只记“模型回答成功”而没调用正确工具。

只读辅助脚本：

~~~bash
HERMES_HOME="$PWD/.hermes-dev/v1.6-validation/dashboard-final-4743943e" .venv/bin/python .hermes-dev/v1.6-evidence/validation-final/capture_state.py resume-current-version.json
~~~

该脚本hardcoded指定合法profile、SessionDB(read_only=True)，不驱动产品。输出含该profile完整合成资料，仅ignored，不能入Git。capture不能替代UI和实际请求观测。

### E3. U01补C12：真实History输出及精确read

起点：原纸鹤合成Conversation，有“青松-731”，先蓝后绿、35项长原文末标“全文末标-霜叶927”；原长消息UID d6b7df680aa044d4b8e0ac54f63bd609。

已完成：旧版本关键词／regex→search截断→精确read全文→原生compress24→11→下一Main找回旧／更正及末标。不要重复这整条昂贵准备。

在新版本发实际用户请求，让Main自己session_history.search既有长原文并read全文。观察工具真实结果：

- outer成功result只一份conversation_ref。
- row只message_uid／timestamp／role／content，search截断保truncated；没有重复message_identity或物理message_id。
- Main从top ref＋row UID组成原Message Identity进行read；没有新裸UID读参数。
- read见全35项和末标；原始正文内若本来有UID字样，不删正文来伪造“字段不重复”。
- 原蓝／最新绿准确，未用压缩摘要代原文，隔离与原权限不变。

该请求可同时真实调用notebook_show覆盖E4，但每项必须观察。

### E4. U02／U03：C10/C11、VAL02与开关／Cold

原Notebook长515字符；VAL02是human只显示折叠标题，无法操作展开。新版本在已有长状态执行/notebook：

- 所有正文完整可读，无必须依赖不可用鼠标折叠才能看内容。
- Created at正常，human不泄露Anchor／Snapshotpointer／termination；reload／cold仍可读。
- localoff依既有产品口径AI Notebook与History仍可读，后台无新Noting／Schedule处理；local切换不改Main root／tools。
- 非globaloff情况下Main真正调用notebook_show：outer仅success/notebook；notebook精确四区user／assistant／consultation／persistence＋last_update_time＋anchor_message_uid。
- last_update_time等当前Snapshot原created_at值，anchor裸UID等对应当前值并能合法History查源；不显示Snapshotid／ref／Identity／trigger／profile／audit／created_at外层包装。
- 没有Snapshot时保持原null契约，不能造空对象新语义；不为复验删已有状态。

U03待完：已有warmglobaloff真实通过，保存false，原请求root和工具无Notebook／memo，History仍在。root同profile升级本身可供coldoff准备，但必须cold恢复后真实Main确认工具面，再warmon→真实Main→coldon→真实Main。每阶段核实际root、schema、dispatch资格与提示同步，不只CONFIG开关显示。

localoff和globaloff不同，不能拿一个代另一个。global切换允许规格规定cache损失；不要因想守cache拒切或错把local改工具面。

### E5. U04：memo四操作、自动开启、非空关闭拒绝、消费及VAL01

可先按正式配置临时加长Idle，让多操作不被后台提前消费；结束恢复短Idle并保存原值，不能改timer实现。

合成输入示例：Main亲自add“纸鹤最终为绿”、add“封面目录待确认”、list、replace第二条为“封面不要目录”、delete第一条、list。同时用户明确这几个决策，避免Noting误把它们当无依据memo。

逐项观察：

- add会自动localon；不是memo直接触发Noting。真实下一Idle事件才整理。
- 编号从1起连续；replace／delete返回修改前内容及完整Markdown列表，错误编号按原契约。
- memo非空时/noting off拒绝并解释；空时可以关闭。
- 后台真实Noting后Notebook反映最终决定；已处理memo消费、Snapshot同commit，dispatch后新加／替换的并发保留机制用现有有效受控证据，不为UI随机造并发。
- VAL01：提交后idle聊天timeline立即显示精确统一英文Finish，不需再发Main才出现、不起新Turn、raw wrapper隐藏；刷新／恢复持久同UID无重复。DB存在只是补证，必须UI见。
- Finish的时间来自Snapshot提交值，没有真正输入timestamp marker；只已处理memo清空，不宣称新memo也空。
- 下一普通Main自然携带该Finish／Notebook，不导致自激重复整理。

旧U01真实Finish UID e75549cf41254d038245fa661e08e040，旧anchor e12265e30b1c4c15b3ef9b38aa2cb120，23:20:55→23:21:30未显示的原失败保留。新修补在bc9cd6d7a1，原通知cold回显只能证明持久显示；还需新真实Idle完成后的即时通知证明live接线。

### E6. U05：真实Persistence候选、提案、修订、批准执行、卸下

不造item／Snapshot。通过真实Main谈合成偏好并等Noting生成persistence候选：

- 先“纸鹤喜欢英文汇报”。
- 后更正“仅纸鹤用中文短段，其它项目未决定；形成候选，尚不批准”。
- /propose-persistence 请查原始来源及后续纠正，只提案。
- 再修订限定范围，仍未批准。
- 最后明确批准执行该一条Memory，只限当前隔离profile。

必须看Main自己History查source及后续反证；Slash只触发指导，不能提前程序拼Evidence给Main。候选不能当权威；未批准讨论／修订不落长期Memory／Rule。最后真正持久化工具成功→同profile读回／后续可用；之后真实Noting才按执行完成卸下候选。批准本身不能当完成归档证据。

不使用Nowledge Mem，不写真实用户memory，不跨profile。若模型没有生成候选／调用工具，记录实际结果，分析它是否满足目标／是否请求仍不清；只做有依据的必要重试，不无限发同问题。

### E7. U06：真实Schedule、idle instant、deferred batch、关闭恢复、隔离

用新的合成Conversation R及观察Conversation O，不污染原来源旅程。

由真实Main信息／memo和真实Noting创建：

- once user_reminder，合法相对表达in 2m，内容“检查纸鹤文件”，按类型原instant语义。
- 两个同绝对due的deferred，user_commitment“校验封面”和secretary_task“检查验收结果”显式delivery_mode=deferred。

真实Notebook见Schedule后等真实钟表，不能修改due_at缩短／插Registry／强行tick／fakebusy。在合法创建阶段选择短期限可以；禁止事后改底层时间掩盖未触发。

观察：

- deferred到期idle不自行起Main；下一自然Main前单durable batch row，JSON带due_at、无timestamp marker，Main回应两条。
- instant到期idle在同R启Main，真实输入timestamp marker，O没有串提醒；不CronJob／Cron Agent／新CronSession。
- 用户看见提醒timeline，raw wrapper隐藏，History持久可读。
- 另一未来once在due前localoff，跨due后on，保原意图、合法恢复至多一次；off无投递／后台副作用。
- ACK以实际装配和成功响应为准；仅due／已排入list不算已交付。失败恢复的复杂时序复用已核机制证据，实际开关恢复旅程仍执行。

记录due／实际观察时间、Schedule来源版本／item、Conversation、输出与后续读取。等待不要每秒发请求，使用有界wait并保持进展交流。

### E8. U07：真实busy instant转deferred

真实Noting先建未来短期once“蓝图-忙碌提醒”。due前Main通过已有合法terminal短暂sleep（仅合成、无外部文件操作）让active Turn跨due，后续真实工具请求继续并回答。

必须实际观测busy覆盖due。若没覆盖，首尝试记为未覆盖而不是PASS；根据实际耗时调整合法下一次准备，只必要一次，不能改DB或用伪busy标志。

预期：

- 到期已有Mainbusy，原gate转deferred。
- 下一实际请求带提醒并回应；没有另排instant Turn。
- 单carrier durable／timeline可读，无timestamp marker、wrapper隐藏。
- ACK后不无控制重投；后续自然问／reload无重复，Conversation能继续。

受控busy／cancel边界的正式集成证据降低UI随机时序成本，但不能替代本次用户目标实际结果。

### E9. U08：Full审计及branch／rewrite合法边界

使用前面真实产物，现有Full只读接口／SessionDB官方方法补证；不实现docs06新UI。

核：

- 首Prelude唯一，来自latest actual provider_neutral_request的root／tools，无Message Identity，不能用现在config重算猜测过去请求。
- ordinary消息逻辑UID与原文一一对应；压缩carrier按真实投影，日常无termination审计噪声。
- Snapshot附实际Anchor，Finish noting_run_output不推进Anchor，其他ordinary合法事件不能因为kind／role被错排。
- 重复读Full无后台／Turn副作用。
- 官方/branch→session.branch是已确认合法入口；分支新Conversation owner，继承Notebook；改分支不影响父，History来源有效范围正确。
- 支持的rewind／edit／undo实际入口先确认，合成数据上操作并核失效历史／pointer；不能用任意文件checkpoint或直接DBupdate冒充用户入口。

compound双投影例外：本次旧UI原/compress只实际产生assistant单投影，不能写“UI已观察compound”。root已准许引用真实SessionDB／Full邻接双投影同Identity、annotation、重复compact／branch机制证据。生产hermes_state_secretary_foreground.py原SHA：
eb9309d460270ee925fda3d7f10b782bc767839ab233b9b838adf966975eda69
恢复时核当前同源及C13影响，保持“机制引用，UI未观察compound”的边界，不静默NA，不再为这个无变化分支写昂贵新driver。若真实Full与之矛盾立即记失败。

### E10. Validation关闭、失败修复及版本一致

每个适用目标／场景都有实际结果和证据，全通过或有依据不适用；无失败／未执行。不能拿“代码看起来对”“DB有值”“helper跑过”“已有模型22次”补未做的典型用户旅程。

如发生产品修补：保留原失败→转plan→主会话方案／独立评审→定向修复→新独立全范围Verification复审→新独立Validation重核全覆盖并复验原失败及影响路径。复用有效准备／未变路径，避免机械全流程重跑。不能只让原实现者修完说旧Gate仍PASS。

同原因连续三次修复未消除，停止重复尝试，根因复盘／换方法，报告事实；不能通过删断言／放宽规格／更改阈值收敛。

## F. 最终复核、文档、提交和交付

### F1. 四条件必须同时成立

1. plan范围内整改全关闭，每项当前版本证据可定位。
2. Verification完整矩阵无违规／不足，符合或有依据不适用。
3. Validation所有适用用户场景无失败／未执行，实际结果符合意图。
4. 最近完整修复＋全范围复审＋适用复验循环没有新整改项；再循环不会改变判定。

主会话亲自完整读delivery-evidence-review／索引／计划／两报告，逐项反查，不只统计PASS数量。

### F2. 源版本／环境／产物对账

- 待交付完整commit、最终产品源hash、构建artifact及实际运行manifest一致。
- Gate报告对应产品版本；后来的纯文档commit可注明同产品源，不必为文档重新模型验收。
- 若验证后代码又变，评估真正影响并按Gate流程补，不把新代码混进旧通过。
- 证据日志／输入／原失败保留ignored，不提交profile／DB／.env／私人Pi资料。
- macOS实测限制诚实保留，Linux／Windows没有实测，不冒跨平台全部通过。

### F3. 三核心文档与正式报告

- 根README只已落实稳定入口，必要本轮事实更新与docs06旁支分开；不能把别任务索引一起提交。
- 根AGENTS只通用规则，别把暂停／Agent名称／本轮状态写进去。
- 根CLAUDE顶部待追认区域保持，当前进度整合为最终已完成与实际限制；旧时点历史保留但标清不是当前状态。
- plan整改表当前关闭证据；verification／validation由对应独立Agent维护，root不能写假Gate结论。
- final-delivery按六节最终结论：目标状态、口径／授权、交付物、两Gate做了／没做什么、剩余／限制、用户复核路径。
- 有实质影响的工程研讨必须显眼进delivery及最终汇报：父原生压缩归属、Source具体item继承、Idle事件不是轮询、Frame／输入身份边界、C13真实DB成功区间退队等；区分用户确认与工程细化，不只列PASS。

本地最终提交前检查差异及秘密。最终答中文，直接给完成结论、主要修补／Gate证据、产物及Dashboard复核入口；不push／部署。

目标工具只在目标真实达成才complete。若用户再次暂停／外部额度中断，按实际情形更新final-delivery和恢复第一步，绝不因快没额度把未完成标complete。

## 5. 给接手小模型的执行纪律与常见误判

| 错误做法 | 正确处理 |
|---|---|
| 看到规范没写函数名就认为随便实现都行 | 恢复对象／事件／时点／频次／生命周期，不改变已指明的方向；薄弱处root提案、Verifier评审 |
| Idle用全局扫条件，重复触发靠下游去重 | 按Turn事件arm/cancel和一周期一次原native持久claim |
| Noting成功准入compact等同父最终commit | C09任务准入和C13父真实DB成功是两个不同关口 |
| 同Turn／同Ref说明Force通知仍有效 | 中途compaction成功已经新区间，Continuation不延寿 |
| 根据Force正文删行 | 正向producer、完整Framework形状、owner／UID限定 |
| 排队旧Force过期补一条audit记录 | never-appended通知不制造durable／pending／audit |
| 为清通知最终候选长度少一行就算压缩成功 | 与filtered baseline比较no-progress，cancel／fail保原输入 |
| Tail删Force后仍按原N保尾 | 精确carried行身份，coverage保原历史，rejoin不加回N |
| DB commit后loader失败退回旧context继续wire | 旧interval已退，原native failclosed，旧queue也必须已退 |
| 只跑受控Python脚本就算真实模型／用户验收 | 机制、模型接口、UI用户结果分别记录，适用真实旅程继续 |
| old129 PASS代替新增C10–13审查 | 独立98全范围当前版本调查及影响复核 |
| Notebook内部字段都透给模型方便debug | 正向六键白名单，内部审计留内部，UID只一份 |
| History输出精简时也改read输入 | 原输入／权限兼容，只正向投影输出 |
| 为跑test把整个项目／lock重装 | 官方PM .venv／原lock，定位实际环境问题 |
| 首assert错就抹失败日志 | 保存原失败，说明预期为何来自规格，定向复测 |
| root反复跑实现者有效suite验证它没撒谎 | root审正式路径／要求／证据适用性，必要才定向补证 |
| 看到后台进程旧PID就直接kill | 核profile／argv／create_time／子树，优雅停止所属实例 |
| 搞新UI帮助验收 | 现有公开入口验收；docs06另任务，不扩V1.6 |
| 规则／代码健康失败就调阈值 | 修实际实现，保冻结类别／阈值／等级 |
| 阶段提交或build成功就宣布交付 | 两当前版Gate与所有范围内整改关闭，再root最终判定 |

不要把小模型记忆不足转化成猜测。每次接续恢复本轮索引／计划／报告当前段和适用技能；只把当前必要材料分批读入上下文，完整证据存文件，用路径与hash传递。主会话必须全范围读规格，具体Development可按白名单精确章节分配。

## 6. 接续阶段完成检查表

~~~text
[ ] 用户明确授权恢复；根AGENTS／CLAUDE及本文已读
[ ] HEAD／dirty／进程／profile／旁支归属核清
[ ] C13 pause-handoff与当前源hash核清，没有把阶段日志当最终PASS
[ ] C13最终retire／carry受影响的persisted／inheritance及必要负对照证据补齐，已有最终PASS不重复
[ ] root亲自review正式接线、History、失败、NoForce及七项条件
[ ] C13产品本地集成提交，源码稳定、旁支未stage
[ ] 独立Verifier阶段B全范围调查，报告／矩阵完整，当前阻断关闭
[ ] 官方TUI产物适用，同profile保库升级并readiness对账
[ ] 新独立Validator全范围计划root过目放行
[ ] C12实际search→原identityread全文与末标
[ ] C10/C11实际notebook_show六键／时间／Anchor查源
[ ] VAL02原长Notebook实际完整可读、reload／cold可用
[ ] U03 warm／cold globaloff/on实际请求工具面
[ ] U04 memo四操作／auto-on／非空off拒绝／消费
[ ] VAL01新真实IdleFinish即时timeline及reload同UID
[ ] U05来源查证／提案修订不写／显式批准实际成功／候选归档
[ ] U06 idleinstant／deferredbatch／关闭恢复／Conversation隔离
[ ] U07真实busyinstant→deferred下一请求／无重复ACK
[ ] U08实际Full最终审计／合法branch及支持的rewrite边界
[ ] 必要修复后的新独立全范围复审／复验，无未闭环项
[ ] 当前产品源、Gate、运行及buildmanifest一致
[ ] root最终delivery-evidence-review与六节final-delivery
[ ] 根三文档职责／链接／状态无过时，秘密／私人数据不入Git
[ ] 本地最终提交、中文交付；只此时目标complete
~~~

本指导的现状以交接manifest、原timers的pause-handoff及根CLAUDE补充为准。恢复后的Agent须即时更新实际状态，不把本文件静态检查表当动态执行记录；动态看板仍只在根CLAUDE。


## 7. 完整恢复材料及迁移到其它执行环境

本指导适用于当前同一工作区的新主会话。C13产品还未提交，不能只复制本文或只git clone到HEAD就说继承了最新实现。

必须随交接保留：

- 本轮六份索引／计划／正式报告／交付文档及本指导。
- 工作区六个C13源文件，或pause-final.patch＋pause-source/真实字节快照；恢复后核pause-source-hashes.json。
- .hermes-dev/v1.6-evidence/下相关公开合成证据、独立criteria锁及proposal-review。
- 正式验收profile的合成state.db／配置与官方产物，保证用户旅程可以沿合法状态续做；凭据仍只本机获授权环境，不混入共享／tracked交接包。
- 根AGENTS／CLAUDE、当前权威01／02／04及对应冻结Git版本。

不得复制或分享私人Pi源／库、.env秘密、用户真实HOME或无关Dashboard状态。若只在本机切换小模型，无需复制或重建任何库。若换主机，先明确环境和凭据授权，实际平台变化不能冒称原macOS运行证据就是新平台实测。
