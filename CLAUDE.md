# Hermes Secretary 主看板

## 自主口径收敛 · 待用户追认

> 本区域按 AGENTS.md 永久维护。无待追认收敛时注明"暂无"。

| ID | 规格空白、收敛及理由 | 状态 | 用户确认 |
|---|---|---|---|
| — | **暂无待追认收敛。** 历史三项已闭环：P01（task instruction 四句系现行 04 §4.4 漏实现的补齐，非新口径）；P02（memo 非空 ⇒ Noting 保持开启，off 仅空 memo 时生效）已确认；P03（memo 触发来源记录名）前提被用户否定，已撤销——memo 不是触发源 | 已闭环 | 2026-10-11 |

## 当前状态

- **C10／C11小修补已完成，待整版复审／真实模型补验**：只改notebook_render正向投影和Main工具外层notebook／description；正文四区＋last_update_time＋anchor_message_uid精确白名单，无Schema／存储迁移，Noting工作态、人类renderer、内部审计不变。相关三文件13/13（1.3秒），future内部字段不泄露／深拷贝／current时间Anchor同值／localoff与null及gate／永久归档通过；四项相关冻结检查ok（health摘要94 files vs3417313ab1f9，0阻断0提示，不冒称只扫描5文件）。证据notebook-ai-view-{manifest.json,tests.log,checks.log}。UI两个修补由timers施工，测试profile仍停新请求，等稳定提交统一升级。

- **用户确认C10／C11，立即修订AI Notebook视图**：Main notebook_show按最新C10／C11只返回四区完整正文＋last_update_time（当前提交created_at原值）＋anchor_message_uid（裸UID可供History查源），移除其余Snapshot envelope身份／Identity／Trigger／Profile／审计；正向白名单投影，内部审计及Noting工作态不变。已同步02 §3.5／§5.12及本轮索引；这是真正用户新增产品修订，不是Agent自主口径。Validator已停新请求：globalfalse、memo空、Main ready、两Child ended，允许同profile升级／Cold，不重建。
- **VAL02（待最小提案）**：真实TUI /notebook 515字符正文折叠为摘要，AX／箭头坐标点击均无法展开；不能用DB可读替用户完整可读。timers只读核既有Slash→消息折叠／PTY鼠标接缝；不引入docs06新UI。

- **验收Surface更正**：启动日志曾有ui-tui构建失败，但现场Dashboard62527子树两对实际进程均为node ui-tui/dist/entry.js→python -m tui_gateway.entry，session source=tui，隔离HOME正确。不能从先前构建错误推断当前fallback CLI；用户汇报已主动纠正，Validation保留原失败记录。主会话打开体验页可能存在第二PTY连接，验收核对自身Conversation归属、不操作其他连接。

- **Validation首发现VAL01（待调查）**：真实官方Dashboard PTY/TUI Main→Idle Noting已提交Snapshot并消费memo，History有正确Finish行；至提交后35秒聊天终端仍无timeline通知。双写成功不能证明02 §5.6要求的用户即时可见。timers正在只读调查原TUI及CLI通知接缝／全host影响并交最小提案；独立Validation继续其余旅程，此项未通过，整体不能交付。未修改产品或新加机制。

- **独立 Verification 已通过（ce2fa6f）**：129条判据为127符合、0违规、0证据不足、2仅Verification阶段不适用（AF122真实用户验收、AF123最终交付，后续仍必须完成）。VFR01–04及旧VF01–03已关闭。原规格先行判据、主会话提案／Verifier评审和各版本失败证据保留于 `.autonomous/20261011-v1.6-implementation/verification.md`；root已复核全129矩阵、当前版本映射及关键正式路径证据，接受进入Validation。
- **官方隔离 Dashboard 已启动**：产品提交 `ce2fa6f4760709275ae9ea87050a5d3996c092c8`，唯一本轮正式实例PID62527，入口 http://127.0.0.1:53345，profile `.hermes-dev/v1.6-validation/dashboard-final-4743943e`。首页与health均200，启动时0会话／0消息；readiness不是用户验收。显示dirty仅文档变更，产品源码hash一致。启动证据 `.hermes-dev/v1.6-evidence/dashboard-final-prep/readiness.json`。
- **独立 Validation 已放行执行**：全新无主会话上下文 `validation_final` 已完整读冻结依据并制定八场景覆盖04 §7.3六旅程；root已完整过目计划与§7.3原文，正式放行通过实际Dashboard输入→真实DeepSeek Main/Noting结果验收。产品只读、不派生；报告 `.autonomous/20261011-v1.6-implementation/validation.md`；Cold重启由root按已保存同profile、无活动任务后协调，不重建数据。最终Verification报告SHA256 `7b5bd97444f75a13ad74f273f0ede9622590613f9a0010014cb9959bdd770fa3`及manifest全artifact hash已root核对。当前未宣布用户验收或本轮完成，后续仍须真实场景关闭和最终证据复核／交付。
- **Pi正式格式库已完成，按用户要求暂存**：48分支Conversation、5986消息行；独立库 `.hermes-dev/chat-migration/pi-personal-history-20261011T143110Z/profile/state.db`，源与归档hash、身份／时间／工具关联、完整性已核。真实私人历史不接验收实例，不参与测试库重建或删除。
- **UI／只读API另行讨论**：docs06及README索引的待提交修改保持独立；没有进入V1.6冻结规格或产品施工，不作为本轮验收依据。

## 本轮接续历史（保留各时间点事实，不代表当前门禁状态）

- **VFR04完整交回已root接收并提交ce2fa6f，待独立关闭**：root读完整四文件变更、正式staging→本Turn资格重算→repair→实际wire/DB/Idle freeze及aux调用，独立核12Main原始双marker各1、4开启场景真实freeze含两UID、2aux资格false/Freshtrue原merge、1Trusted Noting无Fresh；四文件sourcehash一致。96/96（14.9秒）＋定向aux2/2（2.2秒）与原Noting1例证据按分批版本记录、不累加重叠，ruff/health四文件0/0，原超标3839行及函数指标不增。聚合`998e9d82269cdd802489ab75412035ad7d86512c036db340bad0ccb370a8400c`；handoff/root-review在native-compaction-fix/main-input-boundaries-*。首HTTP401和测试底座失败保留，最终aux禁止出网。未宣布整版/门禁通过，已提交`ce2fa6f4760709275ae9ea87050a5d3996c092c8`，独立Verifier已恢复全129影响闭合。
- **用户再次授权继续（2026-10-11）**：已恢复timers收尾VFR04；产品两文件修补在工作区，尚未root接收/提交。既有Main/Framework/repair 96/96证据按源码适用性保留；aux首轮delegate/Noting通过、background因测试未拦流式边界意外发出一次OpenRouter请求且HTTP401（无有效模型响应），真实失败保留，不能说首轮0外部HTTP。仅修测试既有disable_streaming及HTTP禁止哨兵并定向补证，不扩大真实API或重复大套件。收尾后root review→独立全129闭合→正式Dashboard Validation；Pi正式库保留暂存，docs06讨论及README索引修改不并入V1.6产品/冻结依据。
- **当前独立门禁计数（414d37）**：Verifier报告125符合、1违规（AF105，对应新VFR04）、1不足（AF120完成定义）、2阶段不适用（AF122/123仍须后续Validation/交付）。原Framework VFR03已核源码及六正式观察关闭，新连续真实user时间戳缺口按原判据另列、不静默豁免。VFR04研讨与关闭证据将进入原报告及最终交付。
- **UI/只读API独立讨论（2026-10-11）**：口径与技术提案集中于 `docs/06-ui-read-api-discussion.md`，尚未冻结或开始产品施工。用户要求保留V1.6冻结依据，本次误写02 §3.5/§6.19与轮次索引C10–C12已撤回。新文档收录Full Foreground消息列及Anchor/Snapshot、当前Notebook/Memo、关闭后人类仍可读、Framework/Reminder稳定识别；状态复用现有WS。悬浮球仅任务执行时亮起，静息可点开详情；后端提供预计触发时间、前端计算倒计时，不逐秒推送，不设手动触发。不改变主线缺陷、门禁状态及历史审查结论。
- **Pi独立正式迁移库已完成并暂存**：48个独立分支Conversation、5986消息行（4234唯一源消息，含分支公共前缀副本）；43源/4370entry完整存档和消息字段、History身份、时间、图片/思考、工具关联对账通过，8唯一未完成toolcall（10路径副本）如实保留。1条无内部timestamp采用该entry真实时间并注明。root只读重开核48/5986/18自有表、integrity ok/FK0，完整报告与DB hash已核；0API/0Noting/0Snapshot/0Dashboard，源未改、所有连接已关闭。库` .hermes-dev/chat-migration/pi-personal-history-20261011T143110Z/profile/state.db`及同父级`migration-report.json`仅本地ignored保留；真实私人历史不参与测试库重建/删除，不阻塞主线。
- **414d37复审发现连续真实input时间戳缺口**：原Framework VFR03已独立核六真实观察/源码并确认关闭，正式报告更新中。另两native-off实际Main捕获旧1700000400 marker一次、新1700000500零次；旧merge丢api_content且保旧fresh witness，新源timestamp虽变仍重放旧marker。旧2/2只断言原merge，不能证明时间戳完整。root已按02 §5.6及localoff base timestamp契约提议保护现有FreshUserTimestampMarker真实提交行的live合并边界，保原API副本归一及非真实提交普通字典原行为；Verifier已按原AF105接受资格细化：只读既有本Turn Main eligibility＋Fresh witness，Framework独立形状保护保持，不依Noting开关、不放宽判据、不假造时钟/状态/schema。timers已受派实施四文件白名单与正式Main/aux正反证据。调查`native-compaction-fix/native-off-marker-investigation.md`，尚未修补/闭环，Dashboard仍未启动。
- **VFR03修补已在414d37独立关闭（原交回证据保留）**：仅两产品文件识别正式Framework行形状，并在原live user merge双侧保护；原API副本归一、plain native及正文lookalike保持原路径。root完整阅读交回、实际接线及六方向Main→DB→下一Idle真实冻结观察，核源码hash一致；新增正式路径11/11（6.4秒）、既有repair71/71，四文件ruff/health0/0，超标原文件行数/函数指标不增，未API/未重复测试。冷恢复local/global off、三producer连续、纯native反例已覆盖。四文件聚合`4b5d815e9ab020d0330d296de9cedae3b9dc47e1f838712be9b1cec1a077bda7`；证据`native-compaction-fix/framework-boundaries-handoff.md`及`framework-boundaries-root-review.json`。已集成提交414d37并由独立Verifier关闭此缺陷；新VFR04另列，门禁尚未通过。
- **最新接续与体验准备（2026-10-11）**：用户已确认来源是 **Pi**，并明确迁成一份 **Hermes Secretary 正式格式数据库，建好后先放一边**。chat_migration已恢复，只读发现实际 Pi 存储并按真实格式迁入ignored `.hermes-dev/chat-migration/`独立profile；保留原件、消息与分支来源，不接入本轮Dashboard、不运行Noting、不提交私聊。此独立迁移库按用户明确授权含真实私人历史，属于本次任务对“全部运行库仅测试数据”的特定例外，必须保留，不参与测试库重建或清理。主线当前一个已知实体缺陷VFR04：连续真实输入合并丢第二条timestamp；原Framework边界VFR03已在414d37独立关闭。VFR04最小真实提交边界方案已由Verifier评审接受，timers正在实施。其后仍须root review/提交、独立Verification关闭、官方Dashboard Validation和最终交付。
- **当前产品与证据**：当前已提交产品`ce2fa6f4760709275ae9ea87050a5d3996c092c8`，VFR03已独立关闭，VFR04等待独立复审；真实模型证据对应`55e92f170eeb293f7dd78f93e5ea5b340fee0464`；三真实特殊profile观测完成（normal7/forced10/overflow5，共22HTTP200，另旧失败7累计29/30），2530项源hash起止一致、所有probe/worker退出、凭据扫描通过。三组压缩publication瞬间live/DB完整UID-content-order一致和Finish各1；normal实际sameTurn下一wire、forced/overflow实际newTurn wire均使用压缩prefix。后两组newTurn结束live6/DB7，Finish旧UID内容被合入新user，原证据如实标失败/差异，不判最终全一致。root已读取完整handoff及三组summary/source-end；正式wire/前缀关键对应已核验，后续Framework合并差异仍阻断。证据`native-compaction-fix/real-native-handoff.json`。
- **VFR02研讨及实施**：独立Verifier按AF061/062/066/068/070/073确认：读取故障发生在Idle claim之前，导致已fire/pop的周期被后续hostattach重复触发。root提案existingtry_admit_idle接惰性measurement_reader，在原gate/still-idle/durableclaim/External拒绝后读取；真实故障走原_guarded trigger_error且周期已消费，合法None保持原语义，local闭包仅传同次measurement给compact阈值。不新增表/gate/state/revision；Verifier已接受方向及关闭证据。稳定窗口已解除，timers受派双文件修补及真实timer故障多attach读1/FG0、新Main新周期恢复、gate/External正反证据；后续已在87228独立关闭，详见下条当前门禁状态。此前R7 test断言trigger None不构成exactly-one故障路径证据，明确更正保留历史。
- **迁移子任务准备已完成**：chat_migration建议原生`SessionDB.import_sessions`，合成10项（2会话9消息）原文/角色/时间/metadata/UID/toolpair、实际History Search/identity精读、Dashboard显示函数、resume loader/timeline通过，0API/0Snapshot。仅ignored独立测试profile，真实源未读取/迁移、浏览器和模型继续未验证。源system/tool、缺pair/时间/重复显示须按实际来源处理，不伪造外部工具结果/当前root。继续loader会按原生协议合并连续Assistant，durable/display仍逐行保留，不当成原文丢失。证据`.hermes-dev/chat-migration/synthetic/result.json`；来源已由用户确认为Pi，同一子Agent已恢复实际迁移；正式格式库建好后暂存。
- **VFR02已root接收，VFR03仍开放**：两文件惰性reader/原claim顺序修补及21timer＋5直接接口（不累加旧覆盖）通过，ruff/health0/0，双文件hash`73921afb43c9fdf91d77ab17fbb919af06453b6331006d1c688db7cf6e5a9f61`，未API，已在87228独立关闭。正式Verifier确认VFR03为live原列表改写非wire副本：原repair合并Finish与newuser，保Finish UID/noting_run_output并吸收newUID、丢new timestamp，违反AF105/107并关联AF013/109。root提案仅按正式Framework行既有wrapper/display事实保护native live合并边界，所有producer覆盖，纯native零变，provider副本沿原协议；Verifier已接受方向，最小修补已落实，正式路径验证尚未完整交回，不重跑三API证明同一边界。研讨须进入正式报告/交付。
- **历史独立门禁状态（87228；最新414d37见顶部）**：Verifier已按全129条第一轮覆盖后整理最新证据，122符合、4违规（AF013/105/107/109同属唯一实体VFR03）、1证据不足（AF120完成定义）、2阶段不适用（AF122/123后续Validation/交付，整体仍须完成）。VFR02已独立核两个源码hash/manifest/实际timer底座和21＋5日志后关闭；旧VF01/02/03已全范围之后复核，三真实压缩publication及后续wire证据可按源码影响复用，不冒称55e92为872同commit。报告保留旧初审及规格先行129原判据，根`verification.md`已追加六节版本/讨论，当前尚未通过。VFR03 root提案已评审接受，timers最小helper＋live merge条件正在实现；API副本归一已有原native路径，无需新增provider机制。后续同审查者核修复影响与最新129，不重复全量测试。
- **V1.5 产品口径已收口，实施与验收尚未闭环（2026-10-11）**：本轮全部纠偏口径已并入 02 权威规格——新增 **§5.12 全量 prompt 冻结清单**（按代码归属逐条收录，Frozen/Target 双态，施工逐字对照）、**§3.3a 条目生命周期表**、archive 卸下语义、三工具拆分、secretary_task 改名＋delivery_mode、context_overflow、定时器机制、投递 ACK/M4 规则、anchor 判定（noting_run_output 标记）、History Search 截断规则。**V1.6 实际启动提交为 `fa51561601`，文档冻结提交为 `fc2668310b`**；此前 `ec4fc58057` 为口径整理过程中的历史提交，完整 docs 提交链见 git log。
- **V1.6 自主实现已启动**（用户 2026-10-11 最新指令：“开始，1.6轮自主实现”，替代此前待启动及不走自主流程的安排）。轮次 `.autonomous/20261011-v1.6-implementation/`；已冻结现行规格并进入分组实施；随后主会话集成、独立 Verification 与官方 Dashboard Validation。启动提交 `fa51561601`，启动时工作区干净；实现阶段快照已提交，新增C07已集成，尚未最终验收。
- **本轮确认 C02**：item 表限制针对 Agent 直接查生命周期历史和找回条目；内部可以按当前 Snapshot 引用 id 取正文，归档项仍不可见、不可恢复。用户原话“是，原意就是禁止 Agent 查表和找回”，已同步 02 §3.3a。
- 历史轮次索引（细节与流水在各索引与 git 历史中，本看板不复述）：V1 首轮 `.autonomous/20261007-v1-first-implementation/`；V1.5 文档准备 `20261008-v1.5-adjustment-and-acceptance/`；V1.5 实施与云端接续 `20261009-v1.5-implementation/`、`20261009-v1.5-cloud-resume/`。
- 既有验证边界（V1.5 遗留，V1.6 收尾时重跑）：独立 Verification 未通过（含机制形状/时间语义检查项缺口）；官方 Dashboard Validation 未做（用户旁路体验）。
- 运行口径：Main/Noting 真实运行 DeepSeek 官方接口（OpenAI Chat Completions 格式已取证）；不使用 Codex App Server / Codex Proxy；测试一律隔离 `HERMES_HOME`，不触碰真实用户状态。
- 上下文开销：基线与 Secretary 增量实测记录在 [docs/05-context-cost-ledger.md](docs/05-context-cost-ledger.md)（tiktoken o200k_base；主会话增量现行 775 / V1.6 目标 1,419，占完整 profile 基线 2.9% / 5.4%）。

## V1.6 施工清单（依据现行 02；prompt 逐字对照 §5.12）

**A. 存储与工具**
1. `secretary_notebook_item` 生命周期表迁移（§3.3a）：snapshot payload 改存**有序 item id 列表**（无 FK、纯逻辑引用）；item 行 **INSERT-only**，edit/status/schedule 变更插新行并**继承 lineage_id**（create 开新 lineage）；id 为**自增十进制**（对外字符串），行 id＝agent 可见 entry_id＝版本 id；不可变由结构保证，历史演进可完全重放。
2. `notebook_mutate` 拆三工具（§5.12-3.6）：`notebook_manage`（create/archive）／`notebook_edit`（edit/status）／`notebook_schedule`（schedule_update/schedule_cancel，**无 schedule_create**——新条目的 Schedule 在 create 时经 `watchpoint.until` 或 `expression` 子参数设置）；状态机逐类型写死在 `notebook_edit` 的 status description（与 §2.5 一致，persistence 三类禁止 status）。
3. `agent_task` → `secretary_task` 改名（§2.5）：schema 枚举、required fields、status 描述、guidance 段③、提醒模板（`Secretary task due: {task}`）、§3.8/§6.17 同步；其 Schedule 加**显式必填** `delivery_mode`（instant/deferred，仅此类型；instant 到点可拉 turn，deferred 不拉）。
4. archive 卸下语义（§3.7）：archived 条目所有 agent 面过滤、下轮不可见；**无 restore、无任何找回通路**；归档行存 item 表、仅审计视图可见。返回契约（§3.7）：成功 `{"success": true, "entry": <完整条目含新 id>}`＋四分区 state；**任何内容变更都换 id**（旧 id 即刻失效，误用报 unknown-entry 点名）；失败 `success:false`＋可诊断报错。报错可诊断化（§5.12-6）：`Unknown semantic fields for {type}: {违规}; allowed: {允许}`、`Illegal status transition for {type} from {current}: legal targets {…}`。

**B. Prompt 落码**（§5.12 冻结版；**分支注入**：仅全局 Noting 开启的 eligible main conversation，其它会话/平台保持原生原文；prompt 字节稳定、幂等）
5. guidance 六段（§5.12-1.2）：身份首段（秘书心智：不亲自下场、指派督办、用户视角验收、主动沟通；两例）＋段序（Persistence Candidates 前移）＋④⑤合并段＋memo/routing 尾段。
6. task instruction 全文替换＋continuation 新文案（background-task 口径）＋`<noting-tools>` 追加**当前 Notebook 状态**（首条与每次 continuation）。
7. cron 三处（§5.12-7）：主描述（独立定时 agent、与主会话无关；仅显式要求全局管理/免验收重复任务时用；会话内 schedule 归 Notebook）、schedule 字段（删 "remind me in N minutes" 诱导＋加边界句）、`_LOCAL_CRON_DELIVERY_NOTE` 追加反诱导段。

**C. 机制**
8. `noting_memo` 工具（§3.5）：operation 四值（add/replace/delete/list）；index 从 1、delete/replace 后重排；add 返回 `created: 内容, index=N`；replace/delete 返回 `replaced:`/`deleted:`＋完整 current memo；list 为 Markdown 有序列表、空态 `No memo after last noting`；**memo 非空 ⇒ Noting 保持开启**，`/noting off` 仅空 memo 生效；memo **不触发** Noting，随下次 Trigger 的 task 后缀进 child 上下文；commit 时仅消费该任务拿到且仍未替换/删除的条目并**随同一 Anchor 归档**，期间新增/替换内容保留（C03）。
9. Idle Trigger 定时器化（§4.5）：turn 结束 arm（due_at=finished+delay、registry+锁+daemon）；新 turn 取消重排；到点回查持久状态后**只产生一个 Trigger**；session cap 排序键改 `(持有待触发定时器, last_active)`——**排最后、非绝对豁免**；`idle_candidates` 仅作 catch-up 兜底，不得周期性合成 Trigger。
10. Reminder 投递改造（§5.6）：deferred 活跃时落 durable 行，多条到期**一次批量注入**（`以下提醒已到期。`＋JSON，schedule→due_at）；instant＝用户消息提交带 timestamp；**两步 ACK**（预登记→装配校验→成功响应才清 pending；失败保持 pending 重投，幂等键不阻止重落行）；**compaction pass 拒投**（识别本次装配为压缩则拒绝、保持 pending、下次装配重试）；**去掉每请求读库**。
11. Framework Message（§5.6/§2.6）：runtime 内部双写（活列表＋落库同一行）；Force 准入即发"已派发"句、finish 发统一 `Background: notebook updated at <time>. Processed memo entries have been cleared.`（C04/C05）；D01 External拒绝通知覆盖Force/Idle/catch-up（C07）。Finish Notice 写 `display_metadata["noting_run_output"]=true` ⇒ **不推进 anchor**（anchor＝最后一条无该标记的行；其它一切行照旧推进；不用 kind 白名单）。
12. `context_overflow` 强制收尾（§5.8）：请求装不下时与五 Turn 同款——Commit Gate 照走、Finish Notice 照发、termination 记第四型 `context_overflow`；禁止无 Snapshot 丢弃。
13. History Search（§2.3/§2.5）：结果行必附 entry timestamp＋message_uid；candidate provenance 支持 `source_message_identities` 或 `source_time_range`（不强调优先）；**search 单行超 ~800 字符就地截断标记，无强制全文参数；全文唯一通道＝read＋message_uid 精确取**。

**D. 收尾门禁**
14. 独立 Verification 全范围复审（含机制形状/时间语义逐行核验）。
15. 官方 Dashboard Validation（用户旁路体验）。

## 施工硬约束

- **不启用即原生**（AGENTS.md）：功能未启用场景与原生行为完全一致，新机制一律分支/旁路接入。
- 冻结父前缀（root/tools/messages）不动；prompt 文本逐字稳定、分支注入。
- Secretary 持久化只增自有表，不改 Hermes 原有表。
- **开发阶段不做数据迁移**（AGENTS.md）：持久化结构变更直接重建库；所有库在仓库内、全是测试数据。
- 测试走 `scripts/run_tests.sh`（隔离 `HERMES_HOME`），检查 `python scripts/check`；不为建基线预跑大型检查。

## 环境

官方 PM 工作区 `.venv`（Python 3.14.7），现有锁文件不变；运行状态仅 ignored `.hermes-dev/`；不 push 除非用户要求。

## V1.6 实施记录与历史证据（最新编排见顶部）

- **修复交回及root review**：首批native主体已交回（21文件），完整请求25/25＋原native并发48/48，随后receipt取消6项及tool专项1/1，ruff/health21文件零问题，全部worker结束；计数与版本分开保留、不累加。root亲自核对request/commit publication/Loop消费者/取消与host边界，发现lease先绑定旧rotating Session、同UID语义变化sidecar、CLI旧history flush的窄接缝需补核，已交timers定向整改；不提前收产品快照或跑API。C09新独立AF129已仅新规格建立，原128不改，逐字补入正式报告；SHA`04f8bae0c0d50350f5911477ce5e6d303f0aef93d0ae28d81e20b59516570aba`。

- **用户确认C09已立即落规格**：compact_parent按原生成功契约触发后，父压缩后来取消/失败不撤销Noting terminal成功；照常尝试原Snapshot Gate，合法commit后照常写Finish Framework Message。实际压缩context仅成功commit才采纳，与Snapshot/通知提交独立；未准入不能冒称正常terminal成功、Anchor/enablement仍保留。02 §5.9及本轮索引已同步，独立Verifier须先仅新规格补判据再查实现。

- **再一次额度恢复接续（用户明确“额度已恢复，继续”）**：timers从首批14/14后的claimed-timeout/reset/cancel/sidecar/tool验证恢复，native_evidence仅本地适配，网络权限中断后本地工具可用。当前原生接线工作区仍未提交、未root集中review；真实API补证仍0，native_evidence已完成正式五接缝观测适配并等待最终commit。root已准备ignored最终Dashboard单实例starter但未启动；不得把实现途中通过数或准备记录写为门禁通过。

- **新全范围Verification阶段A完成**：全新`verification_final`（fork none）只读36f8冻结01/02/04，独立128条（121直接／2必要推导／5未决解释）、19能力域、M01–M28全覆盖及27薄弱接线重点；尚未调查实现/旧报告/动态看板。root已复核覆盖并将六节原始报告逐字附入正式verification.md，旧139条与固定fba初审保留；原始criteria SHA256 `1ce545ee77cb45ee4c0fba9201671b7500733c6348f219bab30c66f1827459b3`，证据`verification-final/manifest.phase-a.json`。等待最终修复commit及真实补证后阶段B；不作通过声明。

- **隔离Dashboard旧实例已关闭**：接续修复期间以PID/create_time/完整argv/HERMES_HOME核对所有权后，对63881发送SIGTERM并确认退出；本轮官方Dashboard当前0实例，不留旧schema／旧代码混合运行。新profile仍只准备未启动，Verification通过后用最终版启动单实例；证据`dashboard-final-prep/old-server-stop.json`。此前53345就绪记录仅为历史环境准备，不冒充当前运行或验收。

- **本次额度恢复接续（用户再次明确“额度已恢复继续推进”）**：原生两个边界反例已由主会话接收：真实存活 PID holder、正式 Framework writer 与两个 warm Agent，canonical 3/3（14.1s、0外部 API），证明旧 DB/live/tuple 不一致及无争用旧 history；尚非修复通过。证据 `.hermes-dev/v1.6-evidence/native-compaction-fix/counterexample-findings.md`。
- **VF02/VF03 整改进入实施**：root 提议、原 Verification 根据冻结判据有条件接受。父 native request sibling负责真实 receipt/fence、active安全消费者、idle完成态交接、reset/close/interrupt；Noting退为薄触发。完整实际提交结果由native commit/loader产生；请求压缩成功summary的既有metadata承载publication身份，native lease/loader接缝只对未采纳结果进行freshness交接，不新增pending/表/schema/全局gate，不普遍重载无request Main。后续普通压缩、foreign追加、branch/reset、跨进程无争用及未持久user/sidecar保护必须有关闭证据。active用原始custom参数、idle用上一可信参数；官方factory可信None、任意cold未知则诚实compact失败，不能拒绝普通Noting或废合法Snapshot。上述是C08工程收敛，不冒称新增用户确认。
- **当前分工**：timers已完成native修复及root review补交并停止修改；root集中核对接线、失败路径和最终22文件hash后提交为`ab209111ddc338cea203e983b80e20698497293d`。全新verification_final以先独立建立的128条及C09 AF129进入全范围实现调查；native_evidence已获准在该稳定版本上执行三分支真实补证，共享HTTP上限30、失败不自动重试。skill_evidence的五份套件修订已由root差异review接收并通过结构校验，直接用于正式门禁，不做试点。两正式门禁均尚未通过。

- **native最终补交已由root接收**：22文件聚合`018ddeb28f3d529ffe95a0d5a04f73019f443ccee4d384246f17119496dfa43d`，实际post-safety receipt、原生安全消费者、真实commit/loader发布、rotating lease的physical id/ContextVar交接、同UID sidecar正文校验、CLI pre-create/pre-flush settle及可信custom捕获接线均已核对。C09正式Child→Snapshot Gate→Finish在真实receipt后取消时仍成立；DB已成功commit但loader失败则父Loop传播异常，零后续旧wire/flush，不撤销Noting receipt。补交10/10、接缝9/9、settle5/5、失败3/3范围重叠不累加；ruff/health22文件0blocking/0advisory。真实DB/Loop/lease/fence保留，summary/provider边界受控，外部API0。原73/73与先前失败/修复日志保留其对应版本，不冒充最终版全量复跑；真实模型补证、两个门禁尚未完成。证据`native-compaction-fix/implementation-handoff.md`及`review-handoff-{source,manifest}.json`。

- **用户确认套件证据原则（2026-10-11）**：必要的机制集成测试应在开发、接线阶段主动完成，以正式路径和可控调度验证并发/取消/失败；Verification完整审查规格、正式接线与证据可信度，真实模型补证验证不可替代接口，Validation验证真实用户旅程，同版本有效证据复用。不得以零模型测试代替真实用户验收，也不得以“代表链路”为由省略规格明确要求的真实分支；不推测未测故障概率。本次更新既有自主实施套件，不新增试点、门禁或放宽冻结检查。
- 最终暂存集成的8项其余冻结检查通过（`native-compaction-fix/root-staged-checks.log`）；ruff/health复用最终22文件有效结果。root仅去掉新CLI sibling末尾空白行，暂存`diff --check`通过；交回hash对应格式修正前版本，提交树与后续真实probe源码hash对应修正后版本，未复跑行为测试。本次为修复阶段快照，VF01–03独立关闭、真实模型补证及Dashboard验收尚待完成。
- 套件证据分工修改仅五份既有SKILL.md（autonomous-run、executing-plans、spec-implementation-review、real-user-acceptance、delivery-evidence-review），未增模板/全局规则/产品条款。旧文、完整差异及五项结构校验结果位于`skill-evidence-tuning/20261011T103520Z/`；初次项目解释器缺PyYAML，改用已有mise Python/PyYAML，不安装依赖。校验只证明结构有效，实际效果由本轮门禁检验；规格先行和主会话提案／Verifier评审关系保留。
- **真实补证发现R7／root漏审更正**：`ab209111`第一组实际Idle admission选成普通NOTING（freeze用量8137、选择阈值1000），未调用compact_parent，已停止后两组，7个HTTP200不计特殊链路通过。root核对发现`noting_runtime`正式Idle回调仍import已删除的`noting_compact._reread_usage`，异常被捕获后measurement=None使profile错误降为ordinary。此前root只核直接admission与安全消费者，遗漏正式timer调用者，已明确更正并派timers最小修复及正式timer→measurement→profile正反集成证据；待旧probe全部worker结束及源hash闭合后才改产品。独立Verifier已获报并继续以自身判据核验；当前不得判修复版通过。原失败证据`native-compaction-fix/special-normal-c79168cd/`完整保留，共享HTTP预算仍按已用7计。
- R7失败probe已完成清理：SIGINT退出130，Child先完成、无native worker，真实finally写入summary/source-end，2530项产品Python/lock/规格hash起止一致、均ab209。9条wire中2条未发送（屏障及原生重试），只计7实际HTTP；INFO日志未记录DEBUG ImportError，单独只读import反证不伪称日志观察。已解除稳定窗口授权timers最小修复；真实取证等待新稳定commit和root另行授权，累计剩余23而非重置30。证据`special-normal-c79168cd/failure-handoff.json`。
- **R7修复已由root接线review接收，待独立关闭**：三文件仅原生usage公开共享、正式Idle调用去掉失效import/inner吞错、新正式timer行为证据，计算/阈值不变，不恢复Secretary压缩所有权。真实response usage→Main end→daemon timer→actual admission的8137/1000 special、500/合法未知0 ordinary、Force等号Snapshot compact-on/off及无Snapshot不得替代、读取故障error共8项，加5native定向回归，13/13（6.8s）；ruff/health三文件0/0。首负例两非法termination fixture先失败不计产品反例，修fixture后5个实际产品反例均成立，原日志保留。最终聚合`c7b38b5864d46941eaac03ac54b05c00ffeb9886d259c718419c98739cefe672`，所有workers结束，0真实API。root提案获Verifier AF068/AF065评审接受，但不能代替正式关闭；证据`native-compaction-fix/idle-usage-handoff.md`及source/manifest/log。
- 真实补证预算组织已获独立Verifier按AF084/087/088/090/091/109/121评审接受：完整Target另加显式隔离输入，normal以active同Turn压缩后的真实下一wire证明consumer/continuation，forced/overflow分别以新MainTurn证明入口freshness，三个分支各自保Snapshot/termination/Finish双视图。forced text-only五completeTurns仅构造框架兜底，不声称自然默认Task终结能力；不缩规格要求的真实分支、不手造guard/receipt/DB，不把sameTurn冒称newTurn。旧失败7累计，剩23预算仍需新提交后root授权，provider额外请求/原生retry如实计入。

- **额度恢复并接续（用户2026-10-11明确“额度已恢复继续推进”）**：恢复timers进行C08父原生request接线研究，先交方案再实现；恢复原Verification补存阶段B已核实发现、仅新规格先补C08判据后继续固定fba6ec53a7初审。当前HEAD606e251为C08文档冻结追踪，产品代码仍e5f2e70786。此前额度中断是历史状态，final-delivery中断记录保留，完成前重写交付判定。目标工具查询仍显示usageLimited（该状态不能由Agent手工恢复），不据此撤销用户本次接续授权；实际工具及子任务可执行性据实记录。
- 接续后原Verification固定fba初审已完整落盘：原136判据逐字保留，C08仅新规格补V137–139，共139；127符合、5违规、7不足，根因VF01/VF02及受影响接线证据缺口；报告不通过，不能进入Validation。已保存C07竞态评审接受依据、VF01basis方案待独立关闭、撤下Noting拼tail提案和C08父原生候选的有条件方向评审。主会话已集中复核核心事实及不足行，修复后仍需全新无上下文全轮审查，不能把当前版混入固定fba初审。
- 初审补充VF03后最新统计为**125符合、7违规、7不足**（仍139条）：旧Noting将完整cached root作为custom supplement传原生builder，无API真实反例root13054→20663字符；主会话已亲自读取反例与native调用链，接收为独立参数缺陷。修复将使用父原始custom参数，不能借此新增Prompt调优。V131已明确Verification→Validation顺序，未开始后续Validation仅影响整体交付，不能造成门禁循环。原生request完整方案及两个真实DB反例已交回，root提议经Verifier有条件评审后进入实施；本条统计仍对应固定fba初审，不提前关闭VF02/VF03。
- native_evidence子Agent仅准备新版真实取证观测脚本（ignored native-compaction-fix），实际API尚0，待收敛commit后再执行；计划覆盖active tool-loop/in-place、forced/rotating、overflow及每次压缩后的下一真实Main请求，保源码/hash稳定，不重跑旧40+24请求。官方Dashboard新隔离profile已准备为`.hermes-dev/v1.6-validation/dashboard-final-4743943e`，仅配置/凭据安全复制，尚无DB、无服务、无模型请求；正式通过Verification后启动当前版进行Validation。

- 冻结基线：`fc2668310b`（完整哈希见本轮 baseline.txt）；启动 `fa51561601`。计划见本轮 plan.md；三份核心文档和 C02 一并纳入冻结树。
- T1–T4 实现及局部修补已交回，T5 主会话集中 review 已完成，进入正式规格审查。预算正式入口／普通 System Anchor 已提供 50/50 集成定向证据；Framework 队列 owner、Force owner 与 branch 边界已交回；尚不能以子 Agent 测试代替主会话 review。白名单见 plan；子 Agent 不再派生、不提交。
- 用户明确讨论不暂停后台实施；2026-10-11 最新指令取消新 skill 单独试点，后续正式 Verification 直接使用，节省额度并抓紧推进。skill_trial 已停止，不续派试点；其执行曾返回额度限制，不计为审查证据。官方 Dashboard 隔离环境已就绪（localhost:53345，PID 63881；接管记录 `.hermes-dev/v1.6-evidence/dashboard-prep/launch.json`），首页与健康检查通过，尚未用户验收。真实 Native DeepSeek prefix/cache 取证已交回，最后 parent-compact 的八个关键源码哈希与当时集成版一致，新增C07再次改变noting_runtime；普通与 continuation 的 noting_runtime 哈希也不同。真实wire证据保留其观察版本及适用路径，不冒充当前整版全覆盖。Verification阶段A及固定fba6ec53a7阶段B初审已完成且未通过；Validation未启动，尚无全范围最终完成证据。
- PM Python 3.14.7；lock SHA256 `2bc4db483e9cba927cd7147f9ccbb09635f85bb3f1f36d6e9d51d06b65d1c67e`。未预跑大型检查；日志 `.hermes-dev/v1.6-evidence/`。既有失败和平台边界见当前状态。
- 隔离真实运行准备：全新 `.hermes-dev/v1.6-validation/`，DeepSeek 官方 Chat Completions／deepseek-flash，未复用旧库；凭据仅 ignored 本地 `.env`，未输出。官方 Dashboard 已有构建；尚未运行真实验收。
- T1 首次 Prelude 节点缺少 `is_compaction` 导致 13 失败，已修复；已提供局部 model/store/schedule/atomicity/branch 证据，主会话已复核接收。首次测试临时库在系统隔离临时目录，后续运行数据库使用仓库内分组专属basetemp；Prompt/Checkpoint纯文件测试改用runner默认临时目录以避免祖先Git根干扰，不更改runner规则。完整日志见 storage 证据目录。
- T2 初步接收：34/34、正式 host Child→Snapshot 5/5、补充 timer 9/9；主会话核对 timer/DB 原子周期消费/attach/cap 正式路径。R1（已有 Framework queue 遇结束前关闭）已修复并提供 3/3 定向证据；已纳入366181阶段提交。T3 已提供 compaction 拒投/下次重试、跨 host 崩溃恢复及旧 Reminder 回归证据，尾部持久化及owner检查已交回并经主会话复核。不同日志有重叠，不累加用例数。
- 主会话接线：原 `secretary_reconcile_session_conn` 的 Notebook pointer reconciliation 后调用 `reminder_settle_retired_conn`，只结算已有 carry 且源行已 compacted、同 UID 无 active 行的 pending occurrence。M4 未落行和普通请求丢行保持 pending；证据由 T3 的原生压缩/重投场景提供。
- 集成 review：主会话已阅读 Memo 不可变行身份及同事务消费、Child 当前 Notebook 后缀／原生请求预算 guard／Overflow Commit Gate、Framework 所属 ref 冻结与 native tail flush／append transaction、Force及Finish调用、普通System Anchor／Full audit／branch和cron bridge ContextVar路径；按已交回日志接收 R2 定向证据，不重复复跑。规格补充已提交 `8626dc30d5`，baseline保留初始提交并追加此授权版本。
- 正式 Verification 已派遣全新无上下文审查者，阶段A仅从 `8626dc30d5` 的01/02/04规格建立全范围判据，落盘后再提供实现快照与证据。用户取消的skill试点不恢复。集成阶段快照及一次必要扩大检查随后执行；Dashboard Validation须在Verification通过后进入。
- **用户托管目标已挂载**：完成本轮 V1.6 自主实现，含两独立门禁与 final-delivery；用户暂时离开不停止执行。阶段实现提交 `3661812638171ec9a83a8553fcd4a05f7924ed0b`，尚未最终验收。旧 Dashboard `9119`／PID 97007 已按用户授权 SIGTERM 并确认退出，仅保留本轮 `53345` 隔离实例；已重启为PID63881并确认health.commit=fba6ec53a7、首页/health 200、messages=0、配置凭据不变；仍只是环境准备。
- **统一检查已完成**：root 执行一次10项全集，首次 health 发现主循环 CC 23>原基线22与新测试fixture导入同名 F811；提取提醒装配 helper、使用pytest_plugins注册fixture后仅复测 ruff/health，两项通过；其余8项首次已通过，冻结规则未改。日志 `integration-checks.log`／`integration-checks-fix.log`。
- **一次扩大回归已完成**：128个相关文件，四组各自 canonical runner `-j 1`、独立仓库内basetemp，178.4秒；首次1563通过、9失败、3跳过，失败已定向闭环：ACP依赖缺失经官方PM用现有锁在ignored环境补齐；Prompt/Checkpoint纯文件用例的仓库内basetemp引入父级Git根，改用runner默认独立临时目录（这些用例不创建运行数据库）；schema旧表清单补上新增memo表。四个失败文件定向复测分别22/22、57/57+1skip、3/3、9/9，覆盖结果为1572通过、3跳过，不累加重叠用例。未重跑128文件或无关全仓库suite。证据 `integration-test-plan.json`、`integration-group-{0..3}.log`、`integration-{acp,prompt-fixture,checkpoint-fixture,schema}-fix.log`；首次启动参数解析失败未执行测试，已记录。
- SDK跳过补证：官方PM按现有锁新建独立bedrock测试环境（builder拒绝覆盖已有ACP环境，未改变该环境）；两个真实SDK模拟HTTP运输／Native来源用例2/2通过、无外网请求。扩大回归的有效覆盖更新为1574通过、1跳过，余项为macOS大小写不敏感文件系统上的互斥文件名用例；不宣称其他平台已覆盖。日志 `integration-bedrock-{environment-new,fix}.log`。
- C07正式规格补充提交 `3286b7d065`，baseline追加授权追踪；delivery已交回，主会话核对Force／Idle timer／cold attach拒绝的共同publisher、所属ref、busy/fence双写、实际Native派发重置以及仅撤未落盘External通知的路径。Verification阶段A补充已交回：原131判据逐字保留，新增V132–V136，合计136；原始和补充副本/hash均保留，当前C07已集成提交fba6ec53a7并进入阶段B，原判据及补充副本/hash保留不改。新增diff范围10项check通过（external-notice/integration-check.log），没有重跑128文件回归。

## 本轮产品边界确认与实施方案

- **C08 用户明确父压缩职责**：Noting 仅请求原生父压缩、自身Snapshot提交和Framework Message生产；active Turn协调、压缩结果发布与Compression Continuation由父原生运行时负责。已同步02 §5.9及轮次索引。此前Noting层读库拼tail/adoption方案未实施，现已撤下；VF02仍阻断。主会话正在核对原生接收结果及active Turn接线，具体最小方案尚未收敛，不把候选方案写成用户确认。
- C08原生调查（主会话，2026-10-11）：`turn_context.build_turn_context`复制传入history，运行Turn持有自己的messages；`turn_preflight`等原生调用方显式接收压缩tuple并更新flush baseline／重装请求，`turn_context_compaction._reanchor`更新当前user位置；压缩DB watermark保并发tail，rotating原子发布子Session，persist重试可采纳compression tip。但这些不自动替换运行中的Turn上下文；Noting worker局部tuple无人消费，单改`parent._session_messages`也会被旧Turn写回。Gateway hygiene同样显式adopt结果，未发现可直接调用且自动完成active Turn协调的现成异步入口。候选方向是父原生request在自身安全边界执行并消费结果，保留同Turn、同Conversation；空闲压缩与新Turn启动的竞态及receipt接线仍待研究，不是已收敛实现。
- **外部中断（2026-10-11T09:09:08Z）**：目标工具返回`usageLimited`，实现研究子Agent已报额度限制；正式审查报告仍只持久保存阶段A，阶段B已核实的VF01/VF02事实见本看板、plan及本地反例，不能称全范围审查完成。中断交接见本轮final-delivery.md；恢复后第一步收敛C08原生接线方案、修复VF02，补保存独立阶段B报告，再全新全范围复审及Dashboard Validation。此为额度中断，非用户暂停或目标完成。

- **C07 用户授权 External 拒绝通知**：最新指令要求最近实际请求来自External而使Noting被拒绝时追加Framework Message，并明确“不只是Idle”，交主会话自主收敛。覆盖Force、Idle与冷恢复catch-up，沿用所属Parent尾部双写／busy与fence队列；正文已同步02 §5.6。持续External在同一live runtime／Conversation只提示一次，实际Native请求重置提示抑制；开关、已有Notebook和D01门禁保持原契约。文案与内存通知抑制是用户明确委托的工程收敛，不冒充用户逐字确认。接线已实施并经主会话review；专项refs-final 27/27、关联队列回归60/60、Child兼容与Native竞态4/4、既有runtime17/17通过，日志有重叠不累加；ruff及health通过。正式Verification已仅读新规格补充5条判据，待调查实现。
- C07竞态提案（主会话提议，待Verification评审）：External拒绝判断到发布之间若已确认actual Native，文案所称latest External不再成立；发布前跳过过时通知。同Turn busy/fence排队后再实际Native则只撤掉当前ref仍排队的该类通知，保留其它Framework生产者与已落盘行。采用已有Framework锁与简单producer标记；hydration/config猜测不能当Native复位，不引入revision/路由状态/持久pending。此项属于用户委托范围内工程收敛，必须进入审查研讨与交付摘要，不能以主会话认可代替独立关闭。

- **C03 Memo 并发消费已确认**：用户确认未处理的新增/修改内容应保留，要求“用正向代码机制，保证不变量平凡成立”，尽量避免复杂 revision；已同步 02 §3.5 与轮次索引。
- **C04/C05 完成通知已确认**：用户认可简单行身份方案，并要求现有 Finish Framework Message 表达已处理便签已清空；C05 明确须转写为正常系统英文，正文为 `Background: notebook updated at <snapshot commit time>. Processed memo entries have been cleared.`，已同步 02 §5.6、§5.12 与轮次索引；接线与定向证据已交回，主会话已复核接收；正式门禁待审。Notebook 与已消费 memo 同事务提交后才发送该统一通知。
- 工程方案（主会话选择，不冒充用户逐项批准）：单 active 表增加不可复用的内部行主键，内容不可变；replace 删除旧行并插入新行，对外仍按连续 index 操作。dispatch 冻结行身份与内容；Snapshot commit 同事务仅归档/删除该任务实际拿到、且仍活跃的行，再重排显示 index。新增/替换行天然不在清理集合；失败不改 active，用户删除的内容不复活。实施与局部证据已交回，尚未通过全范围验收。

## Verification 历史复盘与 skill 调优

- 用户要求沿 Git 文档历史主动识别 1.5→1.6 口径纠偏与漏审，不要求用户复述；讨论不暂停后台实现。
- 已核实：最早 `89a78c193e` 02 §4.5 已明确 main Turn 生命周期 timer；首轮/V1.5 报告 R050/V43 却只验证 elapsed，接受固定 5 秒轮询。历史 `1127da8731:CLAUDE.md` D02 记录 673 次尝试、672 次 same-anchor skip，是机制被替换后的真实症状；具体 registry/thread/cap 细节为后续细化，不能据此否定原 timer 要求。
- 已核实：首轮报告 R077 接受首响应后修改 child.tools，并称为 suffix-only divergence；历史 `14102ac85c:CLAUDE.md` 已承认头部与后缀被混淆、测试把偏差当预期，原规格没有授权该修改。
- 静态反证：V1.5 V39 只以外层 middleware 返回成功 ACK staged IDs；合法 middleware 删除载体或本地短路时，Provider 未收到提醒仍可能 ACK。V25 则接受额外 role=system Anchor 排除，旧普通逻辑消息定义未授权这一限制。两项为旧树源码反证，本次未新运行测试。
- 另需区分：历史 `1127da8731:CLAUDE.md` 明确记录 request-only System Reminder 是起草规格偏离用户一贯原意；这是审查输入/规格解释失真问题，不能仅以代码符合旧文档合理化。V-001/002/003 已被旧审查抓到，不冒充漏审；真正新增产品要求不倒推旧版本违规。
- **C06 已确认并更新 skill**：Verification先仅读规格建立判据并落盘，之后才读代码/测试/报告/看板；特别关注方向明确但接线与实现路径未详述的要求。主会话是提案方，Verification是依据规格与判据的评审方，授权内工程细化自行收敛推进。关键研讨及结论进入报告、final-delivery与最终汇报。全部原有审查职责保留，未修改冻结代码检查类别或阈值，历史报告不追改。
- 已修改三个全局 skill（spec-implementation-review、autonomous-run、delivery-evidence-review）与两个模板，格式校验全部通过；原件及差异证据位于 ignored `.hermes-dev/v1.6-evidence/skill-tuning/`。这只证明结构有效，实际审查效果仍待本轮独立门禁验证。

- 正式审查调查中的取证边界：Verifier指出04 §4.6/§7.2要求真实特殊Profile compact_parent结构调用、五Turn强制收尾与审计隔离；现有普通/continuation/父压缩wire不覆盖这些分支。root已提出补证方案并委派原取证Agent仅在ignored全新profile补实际DeepSeek链路，产品固定fba6ec53a7。context_overflow按budget guard零API→CommitGate证据评审，不能为HTTP绕过guard；warm/cold/global-off实际用户场景留Validation。此为必要证据补齐，尚未闭环，不作为通过结论。

- **正式发现VF01（未关闭）**：V036 来源有效路径约束被全历史Snapshot source UID通用允许集绕过；fba6ec5真实SessionDB反例确认，rewind移除b后新候选仍能引用旧b并成功commit。证据verification/provenance-observation.json与provenance-counterexample.log。root提案“具体旧item原来源保留／新输入严格当前History校验”已获Verifier方向评审接受；要求source edit及commit并发失效反例、旧来源正常维护与branch/compaction/并发旧base正例。storage正在设计修复，不新增revision或改产品来源语义；原初审固定fba6ec5继续，修复后全新独立全轮复审。

- VF01具体工程方案及评审：root提出INSERT-only item内部nullable source_basis_id，仅绑定same-lineage、合法owner/branch继承、source exact且真实Snapshot已引用的具体基线；create/显式source身份edit不继承，mutation与commit分别按当前History有效路径校验新来源；原version及未改来源的维护保留自身原引用。Verifier已依V036评审可实施，不属revision协议、不改变产品规格，尚未独立关闭；归属不可伪造/raw commit不绕、并发旧base/新source失效、branch/compaction/archived审计正反例仍须取证。为避免真实provider延迟import混版本，storage先准备测试，等T5当前固定版本probe结束后修改产品。新增内部column按开发规则fresh数据库，不做迁移；最终Dashboard将换fresh profile以加载新schema，旧证据库只读保留。

- T5追加真实补证已交回并经root集中review：固定fba6ec53a7的special-normal／ordinary-forced／special-forced／special-overflow四组，共40 HTTP200（26Child），两forced同Child五completeTurns且无模型terminal，special正常结构compact_parent及两特殊fallback均native admission后实际6→4；overflow最终装配guard330414>131072、Child零API。每组有效Snapshot、Finish父live/durable各1、actual notebook_show/Slash无审计字段；所有workers已结束，源hash起止相同。root从原transcript/wire/assembly核对工具名、前缀、Turn状态、guard和输出后接收此分支证据，不代替独立门禁。首specialforced提前Turn2正常结束未计forced；一条Child gzip采集用量解析不完整，Hermes runtime日志独立佐证cache，不补造；standalone AIAgent压缩后live发布同步留官方host Validation。证据native/terminal-evidence-accepted.json、terminal-source-start-end.json、terminal-attempt-ledger.json。storage已获准开始VF01产品修改，后续版本适用性须新Verifier复核。

- **正式发现VF02（未关闭）／root更正判断**：原special-normal/forced/overflow真实native压缩6→4后durable5/live7不是仅standalone harness边界；noting_compact worker只保存返回tuple，正式host没有消费该局部state，facade仅同步markers。Framework确等fence后双写，但仍向旧live列表。此前root暂列“留host Validation”不能作为放过接线缺口的依据，已更正。V099/V077阻断；root提议原生结果发布时点fence释放前adopt，仅本次已commit所属结果，保shared引用、sameDB/ref/live安全，不覆盖Main新tail/branch/reset/另一压缩；failed/cancel/blocked不fake、网络期间不持Main锁、不新增平行fence/pending。Verifier接受方向并要求三真实结束分支live=DB及下一Mainwire、rotation/新Turn/失败/reset竞态证据；timers正在设计最小接缝，与storage白名单不交叉。Snapshot先提交符合admission不等completion，不回滚已有有效Snapshot。

- VF01修复交回并经root接线review接收（独立关闭仍待新Verifier）：仅store/model/items三产品文件和test_notebook_provenance专项，新增internal source_basis_id不进item payload/schema；Child/工具/原DB CommitGate源码不改，该gate仍调用新同事务validator。root核对新create/显式identities edit关闭继承、动态History读取及INSERT重验、raw commit exact immutable版本和同事务来源重验、same-lineage/owner/Snapshot membership/basis exact、未变来源与range-only保留；无全历史UID许可。基础138/138、接线77/77（含专项28），ruff/health0/0；仅有效范围接收，不重复复跑。VF02仍未关闭，当前不进入Validation。证据provenance-fix/handoff.json、integration.log、checks-final.log。
