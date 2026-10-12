# Validation：20261011-v1.6-implementation

## 1. 结果概览

验收者：独立 `validation_final`；日期2026-10-11开始，2026-10-12恢复。Snapshot Index为同目录 `snapshot-index.md`，初始冻结 `fc2668310bff783dde0d6f1cee01b8de99a43cb9`，C03–C09补充见 `baseline.txt`；新增C10/C11冻结及小投影产品提交 `551ca53ba4f33441781304a761d92aac27a94d3c`，尚待与UI修补统一升级；C12 History输出去重冻结 `9fa27767e8ae15ec72cfec96be106dfc0931ed55`，未放行新模型请求。待验产品 `ce2fa6f4760709275ae9ea87050a5d3996c092c8`，官方入口 `http://127.0.0.1:53345`。

已完整阅读 autonomous-run／real-user-acceptance、根AGENTS／README／CLAUDE、冻结CLAUDE施工清单、索引及现行01／02／04原文。02 V1.6修订及§5.12 Target优先04相应旧条款，未修订契约继承。docs06未冻结讨论与私人Pi库不纳依据、不读取。Verification PASS是进入条件，不代替用户结果。

**计划已由主会话完整过目并放行；正在执行，门禁未关闭。** U01跨压缩原文旅程已完成；U02局部开关后台／模型读取已取得真实结果，但长human Notebook折叠不可展开。已发现VAL01即时Finish缺席、VAL02长Notebook不可展开；其它旅程尚未完成。覆盖macOS本地官方Dashboard＋DeepSeek真实Main/Noting；不宣称其它平台、正式云部署或提供商缓存命中率。

## 2. 环境与准备

- 唯一隔离profile：`.hermes-dev/v1.6-validation/dashboard-final-4743943e`；PID62527／port53345。官方PM `.venv` Python3.14.7、现有前端构建；DeepSeek官方 `deepseek-flash` 思考模式Chat Completions，原生Hermes调用；凭据仅该profile ignored `.env`，不输出／不入tracked，不换provider。
- readiness：`.hermes-dev/v1.6-evidence/dashboard-final-prep/readiness.json`，health/home200、commit正确、初始0session/0message，只是准备证据。初始Noting global on／Idle2秒。
- 实际CHAT surface为官方 `node ui-tui/dist/entry.js` → `python -m tui_gateway.entry`，source=tui。首次连接曾有build CalledProcessError，后来使用已有构建；不能据首次错误称后来的Main为CLI fallback。过程树证据 `validation-final/runtime-processes.json`，原Main物理session `20261011_231755_2fc826`、ConversationRef `conv_fde00abd17fd4ae09d9349c583083ba9`，执行时浏览器tab1侧栏30 msgs tui；暖关闭后36 msgs。另PTY未操作／未停止，`runtime-session-association.txt` 记录全部实际Main输入／完成均ui_session09576192→上述physical session。69591启动23:17:54.464与Main创建23:17:55对应；65202在23:12:16已启动。日志无PID直接join，时间关联不能冒作直接进程身份字段。
- 2026-10-12恢复现场（只读一次，无新模型／配置／产品操作）：global noting=false／Idle2仍已保存；PID62527 Dashboard仍运行，原65199/65202及69590/69591均退出；Main physical session与两个Noting均ended，原数据保留。中断后原IAB browser2/tab1不可用，浏览器清单无本轮Dashboard；未新建连接，不将缺失页面称当前UI ready。证据 `resume-C12-state.json`／`resume-C12-observation.json`。等待root新构建、同profile重启与正式门禁放行再从原session恢复。
- CUA官方Dashboard；子Agent不支持visible=true，按文档创建后台IAB tab，首页显示官方导航与fresh状态。只有合成输入，Memory/Rule批准写入只限该profile；不接触真实HOME、其它Dashboard、Pi源／迁移库。
- 写白名单仅原报告、ignored `.hermes-dev/v1.6-evidence/validation-final/` 及上述profile正式产品数据／合法配置。产品代码只读、不提交。
- global优先Dashboard CONFIG；缺入口则原生配置入口并记录用户流程边界。Cold stop/start由root协调该PID／profile并保数据及启动参数。memo场景必要时临时加长Idle避免后台先消费，之后恢复；不改due_at、不插Snapshot／Registry、不伪工具／provider。
- 浏览器DOM／截图及真实输入输出是用户结果；Full现有只读接口／profile DB／日志仅补观察。证据放ignored目录。
- 复用 `verification-final/verification.final-manifest.json`、native-compaction-fix最终handoff和三API组，先核版本／源码影响；只支持受控竞态、强制关闭、overflow、External等机制边界，不冒同commit、不替代本次用户旅程，不重复全量／昂贵API补探。

## 3. 用户目标与场景覆盖

| 目标编号及冻结依据 | 完整场景编号 | 场景类型与起点 | 数据/顺序选择依据 | 当前执行结果 |
|---|---|---|---|---|
| G01长期原文连续性；01§2.1–2.2、02§2.2–2.3、04§7.3(1) | U01 | fresh→原文／更正→原生压缩→查源 | 辨识事实＋>800字长文本，search截断后精准read | 用户目标通过；Finish另记VAL01 |
| G02开关可理解且状态可恢复；02§3.5–3.6／§4.1–4.3、04§7.3(2)(3) | U02、U03 | 已有Snapshot→localoff/on；warmglobaloff/on→cold | global资格切换与local后台开关行为不同，分别判断 | local及warmoff实际符合；human VAL02／Cold未完 |
| G03memo进入下一整理且Main不越权；02§3.5／§5.6–5.7、C03–C05 | U04 | localoff空memo→维护→非空off→Idle | 四操作／编号／auto-on／消费／同Anchor通知；并发保留复用受控证据 | 未执行 |
| G04候选需查证、可修订、显式批准才执行；02§2.5／§3.7、04§6／§7.3(4) | U05 | 真实Notingcandidate→propose→修订→批准→归档 | 合成偏好含后续更正；批准只一项Memory或Rule | 未执行 |
| G05Notebook同Conversation提醒；02§3.8–3.12／§5.6／§6.17、04§7.3(5) | U06、U07 | 真实Schedule→idle；另一due→真实Mainbusy→后续请求 | 一次性／两个deferred批量／instant两入口；另Conversation隔离 | 未执行 |
| G06可信Full与边界；02§2.4／§2.6–2.7／§3.3a、04§2.5／§7.3(6) | U08 | 真实产物→Full只读→产品branch/rewrite | Prelude普通UID／compound唯一特例／Anchor；入口阻挡记缺口 | 未执行 |

从主流程、修改／批准、停用／恢复、压缩后继续、到期交错、跨Conversation隔离枚举八条完整旅程，不做机械交叉乘积。模型输出按意图和实际效果判断，不以计数或DB成功代替。强制终结、取消／崩溃、受控并发及五类时间表达的机制证据复用已审查版本；不可把本次未完成的用户路径改为不适用。

## 4. 详细场景与执行结果

### U01 跨压缩查原文

- 意图／要求：准确找回长期对话原始约定；04§7.3(1)、02§2.3／§6.14。
- 产品／起点／输入：ce2fa6f、fresh CHAT；合成“纸鹤验收”，辨识码“青松-731”；先约定蓝，后改绿；另>800字合成原文末尾“全文末标-霜叶927”。
- 步骤：建立Main→要求History关键词、regex／role查当前历史→等真实Noting→原生 `/compress` 或已有同等入口→继续要求History找原始事实与更正，长命中按UID精准read全文。保存真实工具结果、Main响应及后续读取。
- 预期：History默认存在，压缩前原文和后续更正均能找；search长行有截断、timestamp／UID，read含全文末标；Ref稳定、Notebook后续可读，Main不以摘要替代原文。
- 实际／状态／后续：2026-10-11 23:17起执行四个真实Main输入。先蓝后绿，关键词与regex查旧原文；search截断至第14项，按Ref＋UID `d6b7df680aa044d4b8e0ac54f63bd609` 精准read得到35项及全文末标。真实Idle Noting产生两决策Snapshot（23:20:55），human短Notebook显示Created at且不泄露Anchor。官方 `/compress` 成功24→11消息；后续Main自己search/read原长消息，准确区分旧蓝／最终绿，找回全部35项及末标，并真实show Notebook／list空memo。Main没有拿摘要代原文；同Ref／物理session持续。证据 `U01/input1–4.txt`、`current-history.dom.txt/.png`、`compressed.dom.txt/.png`、`after-compaction-main.dom.txt/.png`及只读状态。G01旧ce2fa6f用户目标通过；Finish即时呈现另记VAL01，未以Snapshot成功替代此通知。C12定向补验预期（已读9fa277提交02 §2.3 L314–325、§5.12 L1990）：升级后亲自search既有青松长原文，成功result层仅一次conversation_ref且保success/messages/count；行仅message_uid/timestamp/role/content，长search保既有truncated。Main由top ref＋row UID构Message Identity精准read取得全部35项／末标；read不暴露physical message_id或重复message_identity，原输入兼容不改。观察实际工具返回及真实Main完整原文使用，不重跑已完成跨compact整套，不修改源正文中的合法标识符。

### U02 局部停后台仍可读

- 意图／要求：04§7.3(3)、02§3.6／§4.3／§6.18。
- 产品／起点／输入：ce2fa6f，U01已有真实Snapshot、空memo；`/notebook`→`/noting off`→“纸鹤新增待确认：封面是否需要目录，请读Notebook和查原文”→`/noting on`。
- 步骤：保存原Snapshot及实际root/tools；off后真实Main、等超过Idle、reload读Slash及Notebook；确认无后台／Schedule处理；on后自然Main、Idle，重读新增事项。
- 预期：human显示Created at，无Anchor／pointer／termination；off反馈持久且模型可见，AI Notebook与History仍读、root/tools字节不因local变；off不启动Noting／提醒，on后保旧状态并整理新增事项。
- 实际／后续／证据／时间：23:22–23:25，localoff后真实Main仍能读Notebook和原文，超过Idle没有新增Noting、Snapshot或admission；两次真实provider_neutral_request的root／工具逐字相等（root SHA256 `03527a62ec46a87e2922b6a3c9933a852c57c105d85171185272474009b2688c`）。localon后Main添加页脚open question memo，真实Idle Noting保旧决策并写入新open question，memo消费归档。证据 `U02/input-on.txt`、`local-off-after-main.json`、`local-switch-comparison.json`、`local-on-restored.json`、`local-off-notebook.dom.txt/.png`。后台关闭／恢复及AI可读通过；恢复后 `/notebook` 515chars只显示折叠标题，AX点击与屏幕箭头点击无展开，human后续使用受VAL02阻挡，该完整场景未通过。

### U03 全局热切换与Cold

- 意图／要求：04§7.3(2)／§3.4–3.5。
- 产品／起点／输入：ce2fa6f、U02同Conversation；globaltrue→false→true，各阶段“查纸鹤最初约定，并说明这次Notebook能力”。
- 步骤：正式配置false，不新建Conversation发Main，记录实际root/tools；root协调cold重启，恢复同Conversation再发Main；true后warmMain，再cold恢复发Main；on时humanNotebook读取。
- 预期：off下Notebook指导／show／memo同步缺席，History指导／工具仍在；on同步恢复，cold不复活旧prompt／pinned tools；local偏好、Snapshot、历史不丢，之后能读。
- 实际／后续／证据／时间：23:31 CONFIG明确保存globalfalse；同Conversation真实Main调用History正确核蓝→绿，实际Full Prelude root无Notebook指导／schema无notebook_show及noting_memo，History指导／工具保留。human `/notebook` 明确“Notebook unavailable: global Noting configuration is disabled or unreadable.”。证据 `U03/global-off-config.dom.txt/.png`、`warm-off-input.txt`、`warm-off-main.dom.txt/.png`、`global-off-slash.dom.txt/.png`、`warm-off-proof.json`及`warm-off-completed.json`。warmoff通过；coldoff／warmon／coldon未执行。新增C10/C11定向预期（已完整读551ca53提交02 §3.5 L764–780、§5.12 L1994–2002、§6.18 L2477及索引C10/C11）：升级后同Conversation亲自调用notebook_show，真实返回仅success/notebook，notebook内为user／assistant／consultation／persistence四区、last_update_time及裸anchor_message_uid；不有Snapshot/ref/identity/trigger/profile/created_at/termination外层审计；时间等当前Snapshot提交值，UID可History查源，human仍不显示Anchor。以真实工具结果、Main后续使用及只读同Snapshot补证判断，不以helper测试代替。收到C10/C11后已交root升级，同profile保持globalfalse／Idle2／local偏好on但全局停用、memo空、Mainready、两Notingended、无compaction；停止新模型请求。

### U04 Memo与Finish

- 意图／要求：02§3.5／§5.6、C03–C05。
- 产品／起点／输入：ce2fa6f、空memo/localoff；合法配置暂加Idle；请Main亲自调用memo add“纸鹤最终为绿”、add“封面目录待确认”、list、replace第二条为“封面不要目录”、delete第一条、list，本Turn同时明确这些合成决策。
- 步骤：核四操作反馈及重排→非空 `/noting off`→恢复短Idle发自然Turn→真实Noting→读Notebook/memo、刷新Finish时间线→空memooff/on。
- 预期：add自动on，编号1起连续；replace/delete返回前内容＋完整Markdown列表；非空off拒绝解释；memo不是Trigger，下次Idle才整理，Notebook反映决策，memo空态精确；archive与Snapshot同Anchor；Finish统一英文单条、刷新持久，无timestamp／raw wrapper／日常termination，无自激重复Noting。
- 实际／后续／证据／时间：未执行，`validation-final/U04/`。并发新增／替换保留仅复用受控证据。结论未执行；偏差无。

### U05 候选→提案→修订→批准→归档

- 意图／要求：04§7.3(4)／§6、02§2.5／§3.7。
- 产品／起点／输入：ce2fa6f；合成“纸鹤喜欢英文汇报”，后更正“仅纸鹤用中文短段，其它项目未决定；形成候选，尚不批准”。真实Noting后 `/propose-persistence 请查原始来源及后续纠正，只提案`；修订“进一步限定纸鹤，仍未批准”；最后“明确批准执行刚才限定纸鹤的这一条Memory，只有这一条，仅当前隔离profile”。
- 步骤：humanNotebook见candidate与来源→Main自己History查source、上下文／纠正→提案后查无写入→修订后再次查无写入且candidate在→批准后核真正持久化工具及再读结果→后续Noting归档→刷新继续询问限定范围。
- 预期：查证原文及反证，Slash不拼源Evidence，候选不是权威；讨论不写，批准后仅那项实际成功且可再用；批准本身不是完成归档，执行确认后才卸下，agent面无恢复。
- 实际／后续／证据／时间：未执行，`validation-final/U05/`；结论未执行；偏差无，禁止NM／其它profile。

### U06 Idle／批量／off-on提醒

- 意图／要求：04§7.3(5)、02§3.8–3.12／§5.6。
- 产品／起点／输入：ce2fa6f，新合成Conversation R和观察Conversation O；请Main经memo/真实Noting建once `in 2m` user_reminder“检查纸鹤文件”，两个同绝对due的deferred承诺“校验封面”／secretary_task“检查验收结果”显式deferred。
- 步骤：先见真实NotebookSchedule再计时；deferred到期idle不应自启，自然Main“当前到期事项”→批量输出；instant到期idle同R自启Main，O无提醒；另一未来once先off跨due再on，核保意图至多一次；官方Cron页与只读诊断无新Job／CronSession；再读提醒历史。
- 预期：deferred真实请求前单durable行、JSON due_at无timestamp，Main回应两事项；instant真实timestamp且同R新Turn；off不fire/on一次恢复，无串Conversation／Cron Agent，持久后仍能读。
- 实际／后续／证据／时间：未执行，`validation-final/U06/`；结论未执行，偏差无；真实钟表，不改due／insertregistry。

### U07 Busy instant转deferred

- 意图／要求：04§7.3(5)、02§3.12／§5.6。
- 产品／起点／输入：ce2fa6f，R真实Noting建短期once“蓝图-忙碌提醒”；due前要求Main亲自以既有合法terminal短暂sleep保持Turn跨due，不读写外部文件，随后工具后续请求并回答。
- 步骤：确认真实Schedule与未来due→UI发真实Main见busy→到期→保存后续模型请求／输出→Turn结束自然问是否提醒→刷新历史。
- 预期：busy原gate转deferred，下一真实请求模型看到并回应蓝图，无第二个排队instantTurn／重复due；timeline可见、wrapper隐藏、无timestamp；ACK后不无控制重投，Conversation可继续。
- 实际／后续／证据／时间：未执行，`validation-final/U07/`；结论未执行；偏差无。若实际忙窗口未覆盖，记录首尝试未完成，不自动重复；受控busy证据不能替代本次用户结果。

### U08 Full与会话边界

- 意图／要求：04§7.3(6)／§2.5、02§2.4／§2.6–2.7／§3.3a。
- 产品／起点／输入：ce2fa6f，U01–U07真实产物；现有Full只读入口；官方合法branch／rewrite操作仅合成数据。
- 步骤：核latest actual root/tools来源，唯一首Prelude无身份，普通UID1:1；实际compound若保用户部分，邻接双投影共原身份；Snapshot/Anchor附着、Finish不推进Anchor；重复读Full不触发后台／Turn。branch新owner且继承Notebook，改分支不影响父；产品支持rewind/edit则撤合成事项核失效历史及pointer。公开合法入口阻挡记缺口，不insertDB。
- 预期：无猜测root/tools，来源可查、日常无termination；branch隔离、rewrite只有效路径。若当前压缩无compound事实，明确未观察，引用正式同源证据并交root评审必要真实补场景，不静默NA。
- 实际／后续／证据／时间：本次官方 `/compress` 仅产生assistant单投影carrier；`U08/post-compress-full.json`初步观察latest Prelude来源为实际provider_neutral_request，root/tools有效，普通UID无重复，Snapshot附既有Anchor，Finish不推进Anchor；最终审计及用户branch/rewrite旅程仍未完成。root已按AF021原判据审阅已执行 `test_secretary_prelude_history` 的正式SessionDB/Full相邻双投影共Identity／annotation及重复compact／branch证据；允许compound机制项复用：`hermes_state_secretary_foreground.py` final SHA256 `eb9309d460270ee925fda3d7f10b782bc767839ab233b9b838adf966975eda69` 与87228一致，55e92→551ca53的Full／compaction_display／该测试无diff，C11不触及此路径。该项是对应版本正式机制证据，不是本轮UI产生或观察compound，未改成NA；交付前必须再核UI修补后hash。实际Full如与此矛盾按失败报root。官方TUI存在 `/branch`→session.branch合法入口，尚未操作；不用文件checkpoint rewind。当前结论未完成。

## 5. 问题、修复与复验

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| VAL01 | official CHAT首次Main决策→Idle2秒→Noting Snapshot commit 23:20:55→23:21:30仍idle | DB/History存在统一Finish `<framework-message>`，display_text与noting_run_output正确，但实际terminal timeline没有出现通知；`U01/after-noting-no-notice.dom.txt/.png`及`idle-observation.json` | 范围内Framework呈现接线缺口，root／timers正在调查；没有以DB替UI判通过 | 未修 | 待原场景即时呈现＋reload后读取复验 |
| VAL02 | localon→真实Main memo open question→Idle第二Snapshot→`/notebook` | human应可读Created at及四区；实际仅“▸ Notebook — 515 chars”，AX文本点击和屏幕可见箭头点击均无展开；`U02/local-on-fold-afterclick`、`local-on-fold-coordinate` DOM／PNG | human Notebook后续使用受阻，已报root；不以DB和模型show替human通过 | 未修 | 待同长Notebook原场景复验 |

范围内失败按原判据报root研讨，不自行修产品／降判据／删场景；保留首次失败，修后复验原场景及实际影响路径。

## 6. 验收结论与推荐复核

G01真实旅程通过；G02局部后台／AI读取结果符合但human后续读取阻挡，G03–G06未完成，门禁未关闭。已获root放行并执行，VAL01／VAL02待修复及原场景复验。C10/C11/C12已由root冻结；2026-10-12当前globalfalse配置保存、原Main/Noting均ended、原PTY和IAB页面已退出，数据未重建；等同profile升级与门禁放行，原ce2fa6f的Notebook show输出仅历史版本证据，升级后定向补验正文四区＋last_update_time＋裸anchor_message_uid，外层仅success/notebook，无其它内部审计。推荐复核：官方CHAT纸鹤合成对话→真实IdleNotebook→跨压缩查源→localoff仍读→propose修订／批准→同Conversation提醒→Full审计。执行后补实际入口、输入输出、持久产物及证据。本报告仅Validation，最终目标结束由root判定。
