# Hermes Secretary 项目主看板

## 自主口径收敛 · 待用户追认

暂无未经授权的待追认产品扩展。本轮用户已整体审定白板，并授权自主收敛完整 Noting Prompt 与工具细节；下列是依授权形成的具体决定，不冒称逐字段由用户亲自选择。尚未实施。

## 第三轮自主实现 · 文档基线（2026-10-16，收敛完成、提交后暂停）

- **本次用户指令**：“开始第三轮自主实现，执行 ask and align”。ask-and-align已完成，正在提交双仓库文档基线；随后按用户要求暂停，未编制正式实施计划或修改产品代码。
- **承接既有确认**：Secretary 改版＋独立个人 NM 接入共同纳入本轮；界面改版后置。已确认的 finish 独立调用、deferred 原投递机制、Scheduler 24 小时空档提示与生效 pointer 控制完成通知继续适用，不重复视为本次新增确认。
- **已确认 A01／R3-002**：并发 Noting 保持现状。已有 Snapshot A，B 未提交时 C 启动，C 可以 A 为起点独立整理，不要求继承 B 的未提交成果；按有效边界选择生效结果，B 后续不生效本身不是缺陷。用户明确认为这一点不构成大碍；保留该设计边界，不新增串行、合并或重跑机制，不以缺少 B→C 成果继承阻断验收。生效 pointer 控制完成通知仍须按已确认契约落实。
- **已确认 R3-003**：用户要求从云端拉取个人Provider仓库；已克隆`EdgarZhong/hermes-nmem-provider`到并列目录`/Users/edgar/code/hermes-nmem-provider`，分支`main`，HEAD `f9733fcb`，clone后工作区干净。已有个人Provider、CLI helper与测试，旧PHASE3的History设计已由新版07替代；个人现行设计已纳入该仓库nowledge-mem-hermes/docs/PHASE3.md上半部§1–7，下半部仅作历史。未安装／部署Provider、未更改运行配置、未写NM服务。
- **已确认 R3-004／本次停止点**：用户要求完成ask-and-align、建立文档基线后先暂停。继续必要调查、收敛和冻结提交；随后仅记录基线并暂停，不撰写交付或交接文档，不编制实施计划、不启动代码实现／运行部署，等待用户恢复。
- **已确认交付环境（R3-005／R3-009）**：明确Hermes正式运行／部署在云端后，用户再次确认“本轮本地隔离验收；以后部署云端”。正式部署不属本轮完成条件；本地验收不冒称云端部署已验证。本次仍只建立文档基线后暂停。Provider旧报告只覆盖其记录版本的模拟客户端／本地HTTP服务，不代表本轮实际环境验证。
- **已确认 R3-006／CLI测试边界**：通用`nmem` CLI编辑／管理不重复验收；此前捆绑Memory／Thread写入测试Space提议未获授权，不据此创建Space或写NM。自有Metadata小脚本与Provider Thread归档的接线验证须与通用CLI功能测试区分。
- **最新用户决定 R3-008／R3-009**：Hermes provenance必须写入NM Memory；撤销此前取消`metadata.hermes_provenance`的短暂决定。以一个小脚本调用官方CLI创建Memory、读取真实返回ID、再仅补写Metadata，复用运行主机同一NM端点／密钥／远程配置；不复刻官方CLI，也不沿用旧helper直接HTTP创建／编辑正文的体系。正式部署目标为云端。尚未实施，未调用NM写入。
- **已确认 R3-010／小脚本验证边界**：用户明确省去provenance小脚本的严格验证，不为它设置独立验收门禁或真实NM测试写入；后续实施仅做基本静态／调用检查，实际联通问题留待云端部署时调整。这不取消强制保存provenance，也不豁免公开Secretary与Provider其他适用要求。Provider自动Thread归档的真实服务写入仍未获授权；本次不写NM。
- **依据入口**：[本轮索引](.autonomous/20261016-round3-secretary-nm/snapshot-index.md)。公开白板／07、旧规格明确保留范围及个人PHASE3现行§1–7均已核对；下载个人稿不再作为平行权威。自动Thread归档的真实NM测试写入未授权，需要时在恢复阶段另行收敛。
- **工作区保护**：启动读取时后端 HEAD 为 `a51fd99abc783f245ab855526a10862f2c89656a`；已有修改为核心文档、01／02／04／05／06／07、白板及归档移动。它们是此前准备成果，不冒称本次实现。本次纳入文档冻结，未改前端、产品代码、配置、运行库或NM服务。
- **检查与停止**：文档差异检查通过，07的9个JSON块可解析，白板43个ID／73张卡片唯一、内部锚点有效，38处本地链接存在；Provider现行JSON及旧PHASE3原文保留检查通过；未运行产品测试，未启动Verification或Validation。基线提交后仅记录双仓库哈希并暂停等待用户恢复；用户明确不撰写交付或交接文档；恢复第一步为writing-plans。第二轮历史结论不作为本轮通过证据。

<details>
<summary>10-16冻结前的文档准备历史记录</summary>

以下“未提交／准备／下一阶段”是当时记录；实际状态以上方本轮文档基线及暂停交接为准。

## 10-16 文档重整（已完成，未实施）

- **授权与基线**：白板D7/D8先改为授权自主收敛，再将当前仓库保存为 `a51fd99abc783f245ab855526a10862f2c89656a`，已推送origin/main且基线工作区干净。包含此前已有显示身份修复和文档，不代表本轮重新验证；浏览器临时日志本地忽略、未提交。
- **07与白板互补**：白板保留已审语义：三板块七类型、属性含义、用户认可范围、7天/72小时具体处理、候选原位引用、两阶段退出、完整Noting顺序、联合触发与Framework注入。07重写为术语、简化转向/理论、History管理、工具Schema/反馈、英文定案、架构接线和实施路径；不再复制白板机制章节。
- **自主收敛的接口**：用户补充确认Noting保留四工具：conversation_history（父Conversation）、notebook_show、notebook_maintain、finish_noting。show按调用者身份返回视图：Main读已提交有效快照，Noting读本任务当前完整工作视图（含未提交修改）；runtime输入/续Turn仍提供视图，修改返回完整单条。07、白板与英文工具提示已同步；尚未实施。稳定entry_id与version_id分离；update属性合并、数组整值替换，参数/类型契约写进模型可见Schema。字数只有软指导，12,000字符/60条只用于提交后提案提示。
- **自主收敛的运行细节**：finish返回end_requested，保持原生Turn返回后提交；去掉with_compaction和compact_parent。Force需补同事务区间admission判据，不能只靠同Anchor/已提交快照防重复。Scheduler独立配置/状态/投递，与Notebook pointer无副作用；用户至少一个instant仍只用提示流程。
- **History具体化**：公开Search/Read、默认当前/Main显式同profile跨域/Noting父域；内部原生FTS候选适配固定路由并处理gap/offset，返回真实诊断，消息时间不冒充Session时间，保留合法inactive fork。候选扫描初值min(10000,max(1000,20×limit))，内部批200；不新增公开cursor。超大Read按真实工具能力反馈，不诱导Noting读文件。旧工具执行入口退出、历史记录保留，恢复时错误明确指向新工具。
- **英文提示文**：Main角色/Notebook/History/Scheduler/时间、原生Search与Cron窄覆写、Proposal、完整Noting、工具声明/续跑、完成/超限/失败和Reminder均在07定案；白板原逐字草案改为对应入口，避免两份Prompt漂移。
- **个人边界**：下载来源稿中公共History吸收进07；个人NM独立为 `/Users/edgar/Downloads/Hermes-Personal-NM-Memory-Integration.md`，原合并稿加拆分提示。Provider/Recall/归档/Metadata/治理仅个人要求，不进入公开Secretary。未访问或写入NM、未修改Provider。
- **旧文档处置**：01/02/04/06保留并加适用边界；05成本证据保持。两份旧Notebook提案及06早期API讨论移入docs/archived并修正入口，旧待审状态不作为现行要求。AGENTS只补文档权威边界，README更新稳定入口。
- **检查范围**：已完成代码接缝与文档交叉审阅；JSON、HTML、链接与一致性检查已完成：9个JSON块可解析（含5个工具Schema），英文提示块无中文混入，73张白板卡片和43个ID唯一，HTML闭合、内部锚点和本轮文档本地链接有效，差异格式检查通过。未改任何运行实现、实际Prompt、Schema、配置、数据库，未运行产品测试或部署。重整结果留在工作区供阅读，未另行提交；改版施工须另按用户安排启动。

## 第三轮实施前准备（2026-10-16）

- **用户已确认：第三轮实施范围**：第三轮自主实现聚焦Secretary改版＋个人NM接入，两条工作线都须纳入计划与验收；不是仅整理这两类文档。个人NM沿独立个人分支／Provider仓库，不进入公开Secretary依赖。界面修改整体后置，Web／Orb／Memo面板／人类Notebook卡片／Settings展示及对应UI读投影不作为本轮实施或完成条件；不据旧07接线清单扩张前端范围。当前仍为正式冻结前准备，代码实施尚未启动。
- **用户已确认：finish与deferred**：沿现有Noting工具执行机制确保finish_noting不与其他工具同批提交；deferred投递逻辑保留原有批量carrier、durable materialization、请求携带与ACK，不重做调度／投递。07已同步。

- **用户已确认：Scheduler未来24小时空档提示**：取消此前固定list检查点／先建后删等步骤指导，AI自行负责管理。每次scheduler工具结果返回，以及每次instant reminder实际投递时，按当前Conversation完整Table检查未来24小时有无可触发instant；排除本次投递发生。没有则在工具结果notice或本次Reminder正文附一句提示，不独立发Framework、不自动补建／拒绝操作。状态未知不当没有；周期后续发生可计入，busy转deferred随最终投递重算。已同步白板K5与07 §6.4／Schema／英文Main Prompt／Reminder及返回策略，尚未改实现。

- **用户已确认：完成通知跟随生效pointer**：Noting提交后只有使当前有效Snapshot指针切换到自己的结果才准备完成通知；未生效旧结果不发。排队消息实际追加前仍须匹配当前pointer，被更新则整条丢弃（含完整正文与Proposal）；比对和追加沿原事务／锁形成一致判定。完成时间保持完成时间，不改派发时间。已同步07 §8.13与白板N3；原Agent“旧结果仍发并标落后”方案撤销。尚未改代码。
- **并发任务工作状态继承（第三轮 ask-and-align 已确认保持现状）**：同Conversation不同Anchor可重叠，各任务读取启动时已提交Snapshot后私有编辑，提交不自动合并其他任务。用户接受C在B未提交时以A为起点；B未被后续有效结果继承本身不构成缺陷，不新增串行／合并／重跑要求。pointer投递规则继续独立落实，详见07 §11.1与本轮索引R3-002。

- **本次范围**：整理三份核心文档、逐章标明旧口径、从第三轮实现者视角审读白板与07；准备审读已完成；本次尚未启动代码实现、运行环境重建或模型验收。
- **依据顺序**：先白板已审语义＋07完整契约，再继承旧规格明确保留部分。01／02／04／06的历史“冻结”“不得改Prompt”等措辞不扩大到第三轮；旧类型、Memo、Notebook排期、旧History面、双profile与compact_parent不进入新施工。
- **仓库实况（本次读取）**：后端 HEAD `a51fd99abc783f245ab855526a10862f2c89656a`，该基线已包含此前后端流式身份修复；当前后端工作区改动为文档。前端 HEAD `9e3566c83633d0456b12e14028b9de77aa58e607`，仍有用户既有未提交修改和 ISSUES.md，本次只读、未改前端。第三轮冻结前须单独记录并保护这些已有变更，不能把它们算作第三轮实现。
- **已有证据边界**：第二轮局部测试／真实运行只对其记录版本有效，整轮无最终PASS；不能将10-15的293项局部通过扩写为全量通过，也不能将较早共同失败的计数直接当当前基线。本次未重跑产品测试。旧端口、PID和live配置只作为历史记录，不保证进程仍运行。
- **审读结果**：三份核心文档已调整第三轮阅读顺序与当前／历史边界；01／02／04／05／06逐章增加替换／保留标识，尤其旧Frozen／Target、Memo、Notebook排期、三工具残句和旧验收项。原正文及旧验收事实保留，不将新设计倒写成旧轮次实现。
- **修正的实施缺口**：07的K5已按用户新决定改为24小时空档提示、pointer变更触发完成通知并在实际安全追加时剔除已失效消息、已结算内容禁止因重读再建、entry/version范围证据、deferred单carrier多项ACK、D01全部入口、Force／External通知继承；Idle读取投影／客户端删除Memo等界面工作已按用户新指令后置。
- **完成控制（finish单独调用已获用户确认，其余为授权内细化，未实施）**：finish混合批次在dispatch前整批拒绝；end_requested后沿原任务锁固定草稿并拒绝继续写，原生Turn返回后Commit Gate才提交。termination保留finish_noting／forced／context_overflow三值，删除compact_parent。上述是已审显式结束／有界兜底与D8授权的落实，不新增工具权限、主会话gate或用户审批机制，不冒称用户逐字段亲选。
- **准备检查**：两名独立只读审读者检查新旧规格与实际接缝，主会话逐项接收修订并复审。文档差异、链接、代码块和Schema一致性检查通过：9个JSON块可解析、73张白板卡片身份不重复，128处章节级适用标识未进入提示文／代码块，另为05历史台账增加整篇边界。非第三轮Verification／Validation，未运行产品测试、改代码／配置、重启／部署或提交。
- **下一阶段**：审读结果见07 §11；第三轮已进入ask-and-align，并发Noting工作状态继承已确认保持现状。收敛其余执行边界后冻结新的Snapshot Index与baseline.txt，再编制计划、实施及开展两项独立门禁，不复用第二轮结论冒充第三轮证据。

</details>

<details>
<summary>第二轮与10-15历史记录（保留证据，不作为第三轮施工指令）</summary>

下列“当前／未提交／运行入口／本次”均是记录形成时的历史措辞；实际代码版本以上方第三轮准备状态为准。历史工具、Memo与排期语义不再授权新实现；前端既有修改与用户当时的操作要求仍需保护。

2026-10-14 第二轮收尾后用户拍板口径（新会话交接必读）：

- **Rewind active 禁用（用户拍板，实施中）**：Turn active 时直接禁用编辑入口，不做 active 编辑事务；V-R2-02 按此口径收敛，不再是待修复杂事务。
- **模型行为路径问题降级关闭**：FV-F05（tool_call/terminal/schedule_cancel 误用）、PDF 漏读/临时 PNG 定性为“白名单挡得住即可”，不追 Prompt/语义层修复。
- **Prompt 历史结论与新议题**：10-14 当时 Prompt 议题关闭；10-15 Main M2／M3 已审定，仅文档 Target 未实施。用户要求回退 02 的 Noting 调优增量，相关文案及提醒结构设计独立保存在 `docs/archived/noting-message-and-reminder-contract-proposal.md`（原 08）；该历史Prompt议题已由10-16白板审定与07英文定案覆盖；运行实现仍未改变。
- **10-14 流式体感历史结论**：当时用户确认响应速度跟得上、未观察到明显上限；10-15 真实录屏暴露动态投影重复、缺段和滚动异常，已重新打开修复，不能以静态结果正确判定流式过程正确。
- **附件实测缺口**：新名 RPC（file.upload_chunk/upload_abort/attachment_info）前端已接线（aacb6e9），仅缺新路径端到端实测——按用户口径仅记录为风险点，不补跑。
- **10-14 修复记录（已完成未提交，以下三项均前端，用户指示不提交）**：① TeX 数学公式渲染（remark-math + rehype-katex + katex，含 realText 第二渲染路径）；② 工具卡片运行期问题族（tool.complete 不再 push Unknown 影子卡改为就地更新；applyTool 退化吸收唯一 constructing 占位卡；旧路径 tool.start 只吸收一张同名构建卡修并行误删）；③ active 态 Reply 禁用入口（liveActive 穿透 memo 链）。tsc/build 通过；440 测试 431 过，9 挂与基线完全一致（8 个 presentation 既有 + 1 个 Usage 既有）。

### 第二轮报告的历史差异说明

以下文档的部分或全部内容已过时，引用前必须核对当时证据版本（后端 `d276ea8b60`、前端 `9e3566c83`）：

| 文档 | 过时内容 | 当前事实 |
|---|---|---|
| `verification.md`（首轮 Verification，10-13） | V-R2-05“assistant-ui 只作外壳”；V-R2-01“前端未接线”；“不通过”整体结论 | aacb6e9 已完成 assistant-ui 深度集成；前端已接新名 RPC；“不通过”针对 c55120f/002f7a2，未复审 |
| `repair-attachment-rpc.md` | “前端未接线，V-R2-01 尚未整体关闭” | 前端 aacb6e9 已接线；仅缺实测（风险点） |
| `plan.md` | V-R2-01~04“待初审集中安排”状态表 | 已被后续实施覆盖 |
| `repair-timeline-latency.md` | V-R2 系列整改方案表 | 框架深度集成已完成；工具卡片运行期归并修复中 |
| `validation.md`（10-14 收尾） | 初始版本引用 BE ea2ab/FE 833ef | 当时 d276ea8b60/9e3566c83；其缺陷记录与未覆盖清单仍有效 |
| `final-delivery.md` | “云端复查未回”交接时点表述 | 以本看板为准 |
| 各 owner 报告（frontend-report、native-compatibility、repair-*、clarify-ui-implementation 等） | 反映各自提交时点状态 | 引用须核版本，不作现状依据 |
| `user-intent-evolution.md` | 历史口径审计 | 仅作历史导航，非现状依据 |

### 2026-10-15 产品记录（历史时点，不是第三轮状态）

- **10-15 ISSUE-013 失败归因与流式回归修复（已完成，未提交）**：用户要求逐项说明此前 11 个失败，先判定本次修改引入的回归，再修复流式相关问题。主会话在 ignored `.hermes-dev/flow-regression-audit-20261015/before` 建隔离副本，仅撤销本聊天上一轮生产代码修改、保留此前其他未提交实现，测试保持相同；未在正式热更新工作区回滚补丁。基线重建的生产文件哈希已核对，比较与完整日志见该目录 `manifest.json`、`comparison.json`、`before-report.json`、`current-report.json`。
  - **归因证据**：相同 49 项，补丁前 35 过／14 失败，首次流式修复后 38 过／11 失败；原 11 项全部共同失败，新增回归 **0**。额外修复前失败的 3 项是新增 paired 正文／推理合并及终态拒绝草稿测试。此前未实测的“既有”判断现已有隔离对照证据，不再只靠代码推断。
  - **原 11 项明细**：① legacy 103 帧缺身份链路出现构建占位＋真实调用两卡，属真实缺陷，已修；② 同一 Assistant 重复 generating 被旧断言视为独立调用，断言过时，同时补修无调用段 commit 时影子 phase 残留；③ 正常 commit 后调用 UID／活跃退休，④ no-history，⑤ empty-history-calls，⑥ hidden-history，⑦ invalid-history-calls，⑧ incomplete-history-calls，⑨ other-uid，⑩ other-scope，八项都混淆了“调用身份已证明”和“结果已证明”，已按现行 06 补强测试，仍禁止凭未证明结果标完成；⑪ Usage fixture 缺 stored_session_id／正式计数字段，补合法 DTO 与 REST 回退 fixture，生产身份校验不变。
  - **实际修复**：未识别构建通知只代表一个阶段，旧链路仅收敛同 Turn 连续尾部无身份 phase；有身份时严格按 scope／Conversation／Turn／Assistant owner 收敛并更新，真实 UID 到达后替换自己的 phase，其他 owner 和真实调用不受影响。新增先见红用例发现 provider ID 复用会碰撞前端节点 ID，已改为以原生 occurrence UID 分配独立新槽位；后端 `mint_uid()` 为 UUID4 fresh durable identity。乱序完成分别更新真实结果，不按名称猜身份。Astra/high 已基于主会话交付证据进行方案逻辑 review，UID 前提由主会话核实。
  - **扩大接线检查**：另发现 4 项在隔离补丁前也失败：3 项按结果到达顺序而非冻结调用段顺序排序的旧断言；1 项 Notebook 用例的活跃节点应为空断言过时，移除遮挡后暴露真实锚点偏移。已保留活跃槽位，并在调用临时命令时保存生成阶段的 Assistant UID 边界，防止占位升级后被未来 tool result 重锚。此为浏览器临时边界标量，不改原文、数据库或后端队列。原始历史 fixture 未修改，不跳过测试、不放松校验。
  - **最终验证**：相关 10 文件 **293 过／0 失败**，3.37s；覆盖原 11 项、额外 4 项、调用 UID／结果乱序、跨 Turn 隔离、正式 Controller／Timeline、Notebook 顺序、Usage 来源、原生 writer/DB fixtures 及按帧合并／Steer 收据。类型检查、两仓差异格式检查通过。主会话按本轮初始快照亲自 review，独立增量见 `followup.patch`；最终报告 `final-regression-report.json`，归因摘要 `summary.json`。本轮未重跑模型联调；此前速度联调结果按其原版本保留，不能冒称本轮重新测量。未提交，保留其他未提交工作。

- **10-15 Notebook 文档拆分（已完成／全部未实施）**：用户要求撤回 02 中本轮 Noting Message 相关改动，将现有提案独立成文。已将 Noting 压缩稿、类型语义澄清、提醒来源／不可变字段及 Schema JSON Patch、token 统计和未来案例迁至 `docs/archived/noting-message-and-reminder-contract-proposal.md`（当时编号 08）；明确已确认设计与待审文案，均不覆盖 02 现行契约。02 §2.5 恢复本轮前版本，删除 §5.12.0 与提醒 Schema 3.6a 增量；现行 Noting／continuation／工具 Schema 原文保持不变。只在 02 §5.12 entry 1.2 Target 写入用户已审定 Main M2／M3 两行，M1 不进入 Main。README 已补独立提案入口；02 中另一讨论的 §1.7 索引目的、§3.8 Schedule 待议澄清及其他未提交工作保留。原 08（现无编号文案提案）第 4 节保持迁移时压缩正文（原版粗估 998／草案 1358，增 360），未静默合入尚待定稿的精简建议。仅文档整理，未改代码、运行 Schema、配置或活动 Notebook，未运行模型／测试／构建，未重启／提交。

- **10-15 Steer 延迟／terminal_conflict（ISSUE-013，修复并完成真实联调，未提交）**：用户要求对照模型输出与前端流式速度，主会话在原故障聊天、原 53445／5173、同 round2 profile 实测。根因是新增 `message.output_delta` 身份配对事件未纳入 RenderStore 按帧合并，每条配对立即 flush，打穿 legacy delta 的合并并饿死事件消费／输入；没有证据把网络认定为主因。纯正文／推理 identity delta 现与 legacy 一起合并画面，权威状态仍逐条同步处理，interim／控制／终态立即发布。用户要求 Astra/high 研讨；已直接交付完整上下文、禁止其探索取证，完成两轮讨论并由主会话 review：保持最小调度修复，不增队列、固定节流或拆 Composer；真实结束竞争仍拒绝且保留草稿，提示改为清楚的结束原因。
  - **真实证据**：修复前 200 行表格约 5,307 字符，后端 17:41:43.459 结束，前端至 17:42:13.638 仍消费旧 delta、动作 Stop，积压至少 30 秒；其后为加载修复主动刷新，未测得基线最终排空耗时。最长事件循环停顿 7.612 秒。修复后同 200 行／约 5,304 字符，后端 17:43:00.719 结束，测试客户端 17:43:00.942 处理结束事件、17:43:01.033 绘制检查已为 Send（约 314ms）；另一客户端约 209ms。实际 Steer 17:42:58.993 发出、17:42:59.065 accepted/pending（72ms），按原生无工具插入点的正常规则进入一个 followup，页面最终显示 `FLOW_STEER_RECEIVED`、空闲 Send、草稿清空。证据仅代表本次样本，不承诺所有机器／长度的绝对上限。
  - **修改／验证**：前端 `core/render-store.ts` 集中纯渲染事件分类，`core/controller.ts` 接入及结束拒绝提示；`verification-fixes.test.tsx` 补完整身份配对的正文／推理、同步状态、控制／终态清除待排帧、拒绝草稿保留及无 Prompt fallback。`native-output.ts` 一处可选链修复既有 TypeScript 空值收窄报错，无行为变化。最终定向回归 15 过／0 失败（含真实 native writer/DB fixture 11 项）；最终版本类型检查与两仓差异格式检查均通过。此前扩大相关 3 文件检查为 48 项 37 过／11 失败（纯 native-output 投影 10、Usage identity 1），不宣称全绿，也未将未实测的历史归因写成确定基线；完整输出 `.hermes-dev/flow-related-tests.json`。原始无正文计时 `.hermes-dev/flow-timing.jsonl`，摘要 `.hermes-dev/flow-timing-summary.json`；临时探针及 Vite 中间件已移除。保留两仓其他未提交修改，后端未修改／重启，未提交。

- **10-15 Timeline 底部留白（用户最终指定 64px，已修改未提交）**：底部 padding／scroll-padding-bottom 统一为 64px，替代此前试调的 52px。仅改前端样式，未改变跟随逻辑；同步 06 §1.4。差异格式检查，未运行测试／类型检查／构建或浏览器验收，待用户查看。
- **10-15 Notebook 时间标签（用户确认，已修改未提交）**：前端 `/notebook` 临时卡片将 `Created at` 改为 `Updated at`；时间值继续来自后端原生人类输出的 Snapshot `Created at`，不改原生响应字段、存储或时间语义。已同步 06 §1.4；未运行测试／类型检查／构建或浏览器验收。
- **10-15 后台／子 Agent 完成通知卡片（ISSUE-012，已实现待用户复测，未提交）**：按现有 `display_kind=process_complete`／`async_delegation_complete` 显示独立、默认折叠且可展开的通知卡片，主题复用 Framework Message，标题精确为 `process complete`／`async delegation complete`。前端赋予独立通知 kind 与 system 角色，不识别为 User Message，不使用用户动作栏／附件解析，不提供 Reply／编辑；后端 role、正文、数据库不改。Framework 包装和 `noting_run_output` 优先保留，Noting Framework Message 展示不变；工具归并仍按原生 source 输入边界分隔。历史／实时共享投影、正式组件及编辑入口已接线，同步 06 §1.4、README 与前端 ISSUES。已做源码 review 和差异格式检查；沿用用户亲自复测安排，未运行测试／类型检查／构建或浏览器验收，本次主会话直接实现、不提交。
- **10-15 Turn 结束跳变（ISSUE-011，已修改待用户复测）**：用户确认此前修复均正常生效，追加 `屏幕录制 2026-10-15 at 17.10.42.mp4`。主会话逐帧捕捉约 11.27–11.78 秒视口显示旧的 17:07 sleep 对比表，随后恢复当前回答。定位到 active 结束批量插回历史用户消息的 Reply 操作栏、累加列表高度，同时后台历史加载阻断滚动维护。已让用户消息操作栏始终保留占位（active 仍隐藏编辑按钮），并将加载等待限定于初次定位，后台刷新继续遵守原跟随/手动暂停/分页锚定所有权；active 切换也同步维护布局。仅改前端，用户继续录屏复测；未派 Agent、未运行测试/类型检查/构建或浏览器验收，未提交。
- **10-15 GPT Subscription 与摘要分段（用户确认）**：`openai-codex` Provider 使用 ChatGPT／Codex OAuth 订阅认证，走 `codex_responses`／Responses API；摘要请求、流式传输及 `summary_index` 变化时插入 `\n\n` 的分段直接复用 Hermes。前端顺序拼接并正常渲染 Markdown、保留原空行，无需额外补换行，不按每次回调强行分段。已同步 06 §1.4、前端 ISSUE-009；仅确认该 Responses 路径，不泛化至所有第三方接口。证据为源码核对，未发起真实订阅请求；本次仅更新文档，未修改代码、运行测试或提交。
- **10-15 列表标记缺失（ISSUE-010，用户已确认此前修复生效）**：用户报告无序/有序/多级列表仅有缩进无标记；确认 Tailwind preflight 清除 list-style 后主题未恢复。主会话直接在前端 `src/design/theme.css` 的 `.hs-prose` 范围恢复 disc/circle/square 与 decimal，保留原缩进、原生起始序号和子列表计数；公式已获用户确认正常，未改公式。按既有要求不派 Agent、不运行验收、不提交。
- **10-15 视口存储澄清（已确认）**：不持久化视口/滚动状态，每次刷新回到 Timeline 底部；已移除滚动 hook 的 localStorage 读写，手动暂停与 20 秒恢复计时仅保留页面内存。
- **10-15 滚动最终澄清／执行方式**：用户主动 Timeline scroll（不分方向）后暂停被动跟随；普通流式追加不推动视口，保持用户指定高度；手动控制结束 20 秒后且当前仍 active 时回底恢复；再次手动滚动重计时。只有用户 Send 被接受会立即回底，不能把 Reminder 等所有新 Turn 都作为回底触发。更早历史必须按钮加载，每次 200 条，插入后补偿新增高度并保持原可见内容锚定，禁止闪动错位。用户要求后续由主会话亲自操作，不再派 6.1；既有两位子 Agent 已交回，剩余修改由主会话直接完成。已同步 06 §1.5。
- **10-15 Thinking 展示口径（用户确认）**：保持现有推理文本／摘要流式展示，取消前端 ISSUE-009“加密思维链模型隐藏流式内容、改为固定文案”的要求；不因 GPT 原始思维链不透明而屏蔽上游可见摘要。保留流式时展开、完成后自动折叠及手动展开交互，不为该已取消需求新增加密识别或接口。已同步 06 §1.4、前端 ISSUES.md；其他 Thinking 打断、缺段和闪烁缺陷仍按既有任务修复。本次仅更新文档，未修改代码、运行测试或提交。
- **10-15 并行工具卡澄清（已确认，立即纳入实施）**：并行 N 个调用对应 N 张独立卡；识别完整工具段时按真实顺序全部展示，之后各卡按真实状态及时原位更新，身份和位置顺序稳定，不按开始/完成事件到达顺序重排。不是整组并行调用共用一张卡。已同步 06 §1.5。
- **10-15 录屏动态渲染修复（用户确认此前修复生效，结束跳变另见 ISSUE-011，未提交）**：用户提供 `屏幕录制 2026-10-15 at 16.33.25.mp4`，确认首次同一次工具调用出现 Success/Running 两卡，过程中四工具卡在 Turn 结束静态对账后恢复三卡，期间 Thinking 缺段/状态异常及跟随中断也存在。明确要求立即一起修复；保持一次真实调用一张卡原位更新、各段独立结束、动态到静态数量/顺序/内容连续。新 Send 被原生接受后回底恢复跟随；主动阅读历史不被后续输出拉走，按最新澄清实现手动控制结束 20 秒后、当时仍 active 才回底恢复，其他新 Turn 不触发立即回底。两位子 Agent 的动态投影/滚动 hook 初稿已交回，主会话亲自完成最终滚动口径、并行工具静态槽位、后端元数据与正式接线的修改和 review；**用户亲自使用相同方法复测，明确无需 Agent 验证，本次不跑模型、浏览器验收或测试，不提交**。
- **正式版本**：后端 `b4a20788c6`（main，已推 origin/main）；前端 `9e3566c83`（main = origin/secretary，工作区含未提交修复与新功能）。
- **运行入口**：后端 53445（round2 profile `.hermes-dev/round2-runtime`，PID 94335，10-15 本次已通过空闲检查及原生 retirement fence 后重启，加载完整工具段事件增量）；前端 5173（vite dev，`hermes-secretary-web` 仓库，热更新生效）。
- **10-15 配置变更（用户明确指示）**：`noting.idle_delay_seconds` 2→**500**；`noting.auto_trigger_compaction_after_noting.threshold_tokens`→**160000**（enabled 仍为 false，未触发特殊路径）。均已 live 生效。
- **10-15 新实现（用户明确要求的产品）**：① assistant 消息复制按钮（hover 显现；移动端/无 hover 单击消息区域 toggle 显现；复制该条正文原文 markdown 源；design/chat.tsx、App.tsx、design/theme.css）；② user message 内嵌 image 从文件图标改为实际预览图渲染（`App.tsx` HistoryImage 独立 img + `attachmentImageUrl` 走 `/api/fs/download` 授权加载内联 data URL 或 path 引用图；CSS `.hs-message-image` 上限 max-width/max-height 22rem 等比缩放）；③ display math 修复与口径（ISSUE-005/006）：多行 `$$` 块修复（`splitDisplayMathClosers` 拆行 + `foldMathMeta` 折叠 meta 并修补 `data.hChildren` 盖章副本）+ 公式块禁止换行改为滚动（`.katex-display` overflow + nowrap）。typecheck 通过，440 测试 431 过、9 挂与基线一致。
- **10-15 新问题登记**：前端仓库建 `ISSUES.md`，登记 ISSUE-001（工具卡片流式过程仍两张 success 卡，昨晚修复未覆盖 start×output 交叉路径）、ISSUE-002（compact 成功后误报 `session.compress timed out; outcome is unknown`）、ISSUE-003（Secretary Orb 展开面板有/无倒计时状态视觉不一致）、ISSUE-004（Thinking 打断显示 Unknown 而非 Interrupted，已定位 `finishOutputNode` 标 unknown 未区分打断）；ISSUE-005/006 已修复待用户确认。
- **整轮状态**：第二轮本地收尾完成；静态 Verification 交云端复查未回，整轮无最终 PASS。未覆盖边界以 validation.md §6 为准（该清单仍有效）：首次 200 分页、IME、最大上传实测、Settings/媒体播放、approval deny、Force 精确 selector、并发族。
- **产品缺口清单**：10-14 P1 = TeX 渲染 + 工具卡片运行期归并；P2 = active Reply 禁用；风险点 = 附件新路径实测。模型行为/Prompt 议题关闭；10-15 动态流式缺陷按上述录屏修复任务重新打开。


</details>

## 历史轮次入口

| 轮次 | 稳定入口 |
|---|---|
| V1 首轮 | `.autonomous/20261007-v1-first-implementation/final-delivery.md` |
| V1.5 | `.autonomous/20261008-v1.5-adjustment-and-acceptance/index.md` |
| V1.6 | `.autonomous/20261011-v1.6-implementation/continuation-guide.md` |
| 第二轮 | `.autonomous/20261012-round2-web-ui/snapshot-index.md`（口径）· `validation.md`（验收，版本见警示） |

改版前代码事实与旧轮次证据按各自版本理解；第三轮要求先读已审白板＋07，只继承旧规格明确保留的部分。05保留成本证据；旧Notebook提案与早期UI讨论已归档，不作为新施工要求。详见README索引。
