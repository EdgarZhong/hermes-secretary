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


---

# 独立 Validation 收尾复验计划：82cd557（2026-10-12）

## 1. 结果概览

验收者：全新独立 `validation_closeout`，无主会话上下文；只读准备于2026-10-12完成。依据为本轮 `snapshot-index.md`、`baseline.txt` 及冻结提交 `31b1f7570562c447c3ac8d37e423d4fc4989b3bb` 的完整01／02／04，已完整读取两Skill、根AGENTS／README／CLAUDE和旧报告。现行02 V1.6修订及§5.12 Target优先04相应旧文；未修订V1/V1.5全范围有效。plan仅作线索。待验产品为 `82cd557aafad97a57d58d07db93fe53f35956990`；官方入口 `http://127.0.0.1:53345`。本段追加保留前文六节、旧版本结论和失败事实，不把修补提交自动写成通过。

**阶段：主会话已正式核准计划，当前82cd557整版Verification PASS已root接收并明确放行。实际首次官方CHAT恢复失败，新增VAL03；尚无Main输入/模型请求/配置变更，已关闭自身页面避免重复自动构建，等待root处理入口缺口。门禁未关闭。** 准备阶段没有浏览器、PTY、配置更改、模型请求或数据库写入。本次覆盖官方Dashboard CHAT／共享Slash输入→真实DeepSeek Main/Noting→用户可读结果及后续使用；macOS本地隔离实例，不冒称云部署或其它平台。

## 2. 环境与准备

- 当前唯一本轮隔离profile：`/Users/edgar/code/hermes-secretary/.hermes-dev/v1.6-validation/dashboard-final-4743943e`。已只读 `.hermes-dev/v1.6-evidence/dashboard-final-prep/upgrade-readiness.json`：PID35729、health.commit=82cd557、首页/health200、bundle SHA256 `3fdf6116f506a757f7567b1653e759985e07a33c8930860589e5d56350770140`。保库升级前后3 sessions／79 messages／2 Snapshots，配置凭据hash不变，scope为Cold upgrade/readiness且无UI或模型请求；这只是起点，不是cold用户行为通过。
- 原合成父Conversation为 `conv_fde00abd17fd4ae09d9349c583083ba9`，physical Session `20261011_231755_2fc826`；青松-731蓝→绿、更正与35项长原文末标“全文末标-霜叶927”、已完成一次原生压缩、两个Snapshot及历史失败是合法中间态。当前globalfalse、local偏好on、memo空、Idle2。不得重建库。先经Dashboard恢复原会话，核实际归属；原CHAT是官方 `ui-tui`→`tui_gateway`，具体本次连接以现场观察记录，不从旧build失败推断fallback。
- 运行使用官方PM工作区 `.venv`、现有lock和官方DeepSeek `deepseek-flash` 思考模式Chat Completions。凭据只允许profile授权.env，不显示、复制到证据或入Git；不切换API/provider、不接Codex Proxy/App Server，不操作另一Dashboard。
- 实际授权只在主会话放行后生效：官方CHAT/共享Slash、Dashboard CONFIG或其缺口下的原生合法配置入口；仅该隔离profile内合成产品数据；真实Memory工具写入须在已提案后，经场景里的明确批准且只写一项合成内容。禁止NM、真实HOME、私人Pi、docs06、.playwright旁支、产品源码修改和提交。新增证据白名单 `.hermes-dev/v1.6-evidence/validation-closeout/`，报告只追加本文件。Cold由root核无活动Main/Noting/compaction后保库协调，验收者不重启。
- 可在memo操作前临时将Idle调长，避免Main刚结束即被消费；随后恢复短Idle，记录原值、保存入口和恢复结果。Schedule必须由真实Noting依对话证据创建；真实钟表等待，绝不改due_at、直接插Registry/Snapshot、手造provider/工具成功或驱动内部tick。
- UI页面、终端timeline、共享Slash返回、模型实际工具使用与用户后续操作为主证据；模型结果白名单核验可补读真实durable工具结果、运行日志或Full。只读DB使用read_only，Full读取不得驱动后台；不把DB计数、helper成功或原始JSON单独当作人类可读/即时可见通过。
- 旧证据复用范围：U01原始输入、真实keyword/regex/role、精确read、压缩及后续查源旅程保存于 `validation-final/U01/`，新版只补C12输出与真实Main继续使用；local旧实测及warm-off证据仍保其ce2fa6f版本，本次以新增开关路径核新版用户行为。ce2fa6f→82cd557的变更清单已读：History/Notebook投影、Framework展示和C13压缩边界改变，原Source-of-Truth/History路径、Notebook store、memo、reminders/schedules、Full投影未变；不能据此直接跳过VAL01/02或新版投影。
- 昂贵／受控边界复用须逐项核实际artifact、hash、路径影响及当前Verification判断：`verification-final/verification.final-manifest.json`、`child-memo/` memo并发与失败保留、既有Reminder ACK/compaction拒投/崩溃重投、`native-compaction-fix/real-native-handoff.json`三真实特殊分支及原wire/cache证据、`force-notice-boundary/`正式C13。55e92真实forced/overflow后新Turn曾live/DB不等的失败保留，只复用其独立成立的结构调用、publication/下一wire与cache事实，后续边界必须引用已修正式证据，不能把旧失败整体称PASS。C13改变原生compress，所以只支持未受影响的旧结论，并核当前专项关闭证据；本次不重新灌高token或重复大测试。

## 3. 用户目标与场景覆盖

| 目标编号及冻结依据 | 完整场景编号 | 场景类型与起点 | 数据/顺序选择依据 | 当前执行结果 |
|---|---|---|---|---|
| CG01 原文连续、紧凑结果仍可查全文；01§2.1–2.2/§6、02§2.2–2.3/§6.14、C12、04§7.3(1) | CU01（续U01） | 保留旧真实压缩史→新版search→精确read→Main辨别更正 | >800字符长源、keyword/regex/role与全文末标；不重复已通过准备 | 计划；新版未执行 |
| CG02 开关可理解、立即一致、Cold不丢状态；02§3.5–3.6/§4.1–4.3/§6.18、04§3.4–3.5/§7.3(2)(3) | CU02、CU03 | Cold globaloff→warmon；localoff/on；warm globaloff/on→root coldon | global工具资格与local后台门禁独立；当前升级是合法coldoff起点 | 计划；VAL02原复验未执行 |
| CG03 memo四操作、安全消费与完成可见；02§3.5/§5.6/§6.17、C03–C05 | CU04（续U04） | 空memo/localoff→Main维护→非空off拒绝→Idle真实Noting→完成通知→重读 | 简单两条memo覆盖add/list/replace/delete/重排、auto-on及消费；并发另复用受控 | 计划；VAL01原复验未执行 |
| CG04 候选自主查证、修订与批准分开、完成才归档；02§2.5/§3.7/§5.12-5.1、04§6/§7.3(4) | CU05（续U05） | 真实Notingcandidate→proposal→更正修订→只批准一项Memory→真正执行→后续归档 | 先笼统偏好后限定“仅纸鹤”，有反证；未批准与执行成功是不同观察节点 | 计划；未执行 |
| CG05 真实Schedule同Conversation到期、无Cron；02§3.8–3.12/§5.6/§6.17、04§7.3(5) | CU06、CU07（续U06/U07） | 真实Noting建once→idle instant；deferred批量→自然请求；off跨due/on；instant跨真实busy | R提醒与O观察会话；两deferred同due、一次性、忙后下一请求，真实时钟 | 计划；未执行 |
| CG06 审计可信、branch隔离、合法rewrite有效路径；02§2.4/§2.6–2.7/§3.3a/§6.11–6.14、04§2.5/§7.3(6) | CU08（续U08） | 真实产物→只读Full→/branch→分支新决定→/undo→更正新输入→回父查看 | 分支及undo只修改合成数据；普通UID映射/Prelude/Anchor与用户更正后查源 | 计划；未执行 |
| CG07 完整继承的运行/权限/原生回退边界；01§6、02§1/§3–§6、04 M01–M28/§7.2；C07–C09/C13 | CE01（证据复用审查）＋CU01–08实际衔接 | 正式同源机制与真实模型证据→核版本影响→本次最终用户结果 | identity冲突、并发/取消/崩溃、force阈值/External、五Turn/overflow、ACK/重投、compound仅机制可稳定构造 | 待当前Verification及artifact复核；不充当UI场景替代 |

从连续原文、读取/关闭/恢复、便签维护、候选修改/批准、到期交错、跨Conversation及分支撤改枚举完整旅程，不机械穷举所有输入组合。五种时间表达和不可稳定发生的竞态由已有效正式机制证据覆盖；典型提醒选择显式延迟once与带时区绝对once，防裸duration误判。Memory一项代表获批已有持久化能力；Rule/Skill类型/schema及禁止越权由全范围Verification和机制证据覆盖，不写个人规则或文件。非确定性整理按意图/限定范围/真实效果判定，不要求特定文案或条目计数。

执行顺序：CU03 coldoff起点→globalon→CU01及C10/C11→CU02 long/localoff→CU04及VAL01→CU05→CU06/CU07→CU08→CU03 warmoff/on与root coldon→最终证据闭合。共享准备有完整实际历史；需要缩减或改序必须记录理由，范围内未完成不能改为NA。

## 4. 详细场景与执行结果

### CU01 旧原文在新版紧凑History结果中继续可用（C12）

- 意图/依据：找回真正旧事实、更正及完整长原文；02§2.3 L289–349/§5.12-3.1，04§7.3(1)。版本82cd557；合法起点为U01已真实压缩的原父Conversation，不重新创建原文。
- 输入：“请亲自用session_history关键词查青松-731，再用regex和user过滤核最初蓝色与后续绿色；查到35项长原文后用结果的conversation_ref和message_uid组成message_identity精确read，指出全文末标及第35项。以原文为准。”
- 操作：CHAT恢复父→输入→观察真实工具调用及回答→补读实际tool result；需要的read由Main自行发，不由验收者预贴源文本。
- 预期：成功envelope只success/conversation_ref/messages/count，结果Ref单份；row只message_uid/timestamp/role/content（search长行允许truncated）；无physical message_id/重复Identity；精确read返回35项与末标、正确蓝→绿，同Ref持续，源正文中原有标识符不被改写。原U01跨compact连续性的有效旧事实保留，新响应补足输出投影和后续使用。
- 实际/状态/效果/证据/时间：未执行；拟 `validation-closeout/CU01/`。偏差无。

### CU02 人类长Notebook、AI六键与localoff/on（C10/C11、VAL02）

- 意图/依据：读取实际当前工作状态，暂停后台后仍可用；02§3.5 L764–780/§3.6/§4.3/§6.18，04§7.3(2)(3)。版本82cd557，旧515chars Snapshot可复现VAL02。
- 输入与步骤：globalon恢复后 `/notebook`，滚动/真实键盘阅读全四区和字段；请求Main亲自notebook_show，并根据anchor_message_uid以当前History Ref精确read该源行；空memo时 `/noting off`→自然输入“纸鹤验收新增待决：是否需要页眉，先只读现有Notebook和原文，不添memo”→等超过短Idle→再次 `/notebook`；随后 `/noting on`，下一自然Turn说明“页眉暂不采用”，等Idle真实整理→再读。
- 预期：人类完整长文可阅读，含Created at、不露Anchor/pointer/termination且Slash历史可再读；不能用折叠标题/DB替代。真实show外层仅success/notebook；notebook恰六键user/assistant/consultation/persistence/last_update_time/anchor_message_uid（四区内容完整、归档缺席），时间等实际当前commit、裸UID能查真实源；不泄露Snapshot/ref/Identity/trigger/profile/审计。localoff反馈持久/模型可见、root/tools字节不变，Notebook/History可读，超过Idle无Child/Snapshot/Reminder；on保旧状态并按新意图整理。若Main自行加memoauto-on，则明确该输入没达成localoff窗口，按实际记录并报root，不伪称后台停用。
- 实际/状态/效果/证据/时间：未执行；拟 `validation-closeout/CU02/`。VAL02旧失败保留，本次须真实同长/更长正文和后续使用通过；偏差无。

### CU03 全局warm/cold切换与恢复

- 意图/依据：用户配置后下一Turn立即一致，重启不恢复陈旧权限；02§4.1/§6.18，04§3.4–3.5/§7.3(2)。版本82cd557，起点保库cold升级后的globalfalse、原Session。
- 步骤/输入：先恢复旧Session，CHAT“查纸鹤最初颜色与更正，说明这次能否读取Notebook”，观察History及globaloff不可用反馈；Dashboard CONFIG保存true→同Session下一Turn真实show/History；在其它场景结束且memo空后CONFIG true→false→下一Turn同样查源，再false→true→下一Turnshow；安全空闲交root保库coldon重启，恢复同Conversation，再输入show/History并读 `/notebook`。不重建Session来掩盖热更新。
- 预期：false无Notebook指导/schema/show/memo/dispatch，History工具及精确两句指导保留；true同步恢复且局部偏好、原文/Snapshot不丢。每次实际provider request/Prelude来源核指导与最终schemas一致；cold恢复不复活旧prompt/pinned tools、不在启动时偷发模型。人类globaloff `/notebook`及proposal拒绝可理解。upgrade readiness本身只cold起点，实际请求才决定coldoff是否通过。
- 实际/状态/效果/证据/时间：未执行；拟 `validation-closeout/CU03/`。原warmoff旧证据保留其版本，本次新增路径闭合，root cold协调待放行；偏差无。

### CU04 memo四操作→自动开启→真实整理→即时Finish（VAL01）

- 意图/依据：Main告诉后台下一次必须整理什么，安全消费且及时知晓完成；02§3.5 L782–804/§5.6 L1657–1698、C03–C05。版本82cd557；globaltrue、空memo/localoff、临时长Idle。
- 输入：请Main亲自依序add“纸鹤封面保持绿色”、add“纸鹤目录待确认”、list、replace第二条“纸鹤封面不要目录”、delete第一条、list；这些合成意图同时写明，并禁止Main直接Notebook mutation。操作可同Turn，但每个真实工具结果均核。
- 步骤：先off→Main四操作→核auto-enable、list编号及反馈→立刻 `/noting off` 非空拒绝→确认memo仍在/无因memo独立触发的Task→恢复Idle2并发自然Turn使下一正常Idle发生→持续观察timeline不再输入→真实Noting完成→ `/notebook` 和Main list/show复读→空memo off/on，reload历史核单条通知持久。
- 预期：index1起连续，add created/content/index与auto-enable反馈；replace/delete前内容+完整Markdowncurrent list；非空off不生效且解释；memo只下次Trigger上下文、Noting覆盖剩余“不要目录”意图。commit同Anchor消费/归档，list精确“No memo after last noting”，memo不混进show。Finish在无Turn时commit后即用户timeline可见（记录观察时刻），正文精确正常英文含实际commit时间和processed memo句；单条、raw wrapper/timestamp/audit隐藏、不会自激启动Turn或重复Noting，刷新继续可读。并发新增/替换/失败保留的不可稳定时序按CE01有效正式证据补，不用本次简单消费冒充。
- 实际/状态/效果/证据/时间：未执行；拟 `validation-closeout/CU04/`；VAL01旧“commit后35秒无通知”原失败必须保留，不能以新DB成功关闭；偏差无。

### CU05 真实candidate→查原文/反证→只提案→修订→显式批准Memory→归档

- 意图/依据：从长期线索形成经用户控制的准确持久化结果；02§2.5/§3.7/§5.12-5.1、04§6/§7.3(4)。版本82cd557，原合成父会话。
- 输入/步骤：先说“纸鹤汇报先考虑英文，把可能长期有用的偏好记为待审候选，尚不批准”；之后明确更正“仅纸鹤验收项目使用中文短段，其它项目未决定；记候选，不写Memory”。真实Noting后人类Notebook看candidate及来源；`/propose-persistence 请亲自查原始来源、上下文和后续纠正，只提案`；再“草稿进一步限定到纸鹤验收项目，我只是修改，仍未批准执行”。最后才“明确批准通过现有Memory工具执行刚才限定纸鹤验收项目的这一条合成Memory，只有这一条，仅当前隔离profile”。
- 预期/观察：Main亲自session_history按来源read并查后续更正，提案准确限定、解释证据/不确定；Slash不预拼Source Evidence。proposal和修订均无Memory/Rule/Skill工具写入，candidate仍在（可被修订，不因谈过归档）。批准后真实既有Memory调用成功、可再读/后续使用且只授权项；失败不冒成功。后续真实Noting确认已执行才archive，human/show/后续Child不再见候选，无restore或生命周期回收入口；审计可补追踪不可代替用户看到卸下。检查批准本身不是Notebook归档条件，实际工具结果是结案依据。
- 实际/状态/效果/证据/时间：未执行；拟 `validation-closeout/CU05/`。Memory仅合成隔离profile，不写NM或个人Rule/Skill；偏差无。

### CU06 真实时钟的idleinstant／deferred批量／localoff恢复／Conversation隔离

- 意图/依据：提醒只回所属对话，不派Cron；02§3.8–3.12/§5.6/§6.17、04§7.3(5)。版本82cd557，官方新合成提醒Conversation R及观察Conversation O，记录各自Ref/Session。时间输入按配置Asia/Shanghai及实际时钟生成，留足真实Noting完成余量。
- 步骤：R中输入“请两分钟后提醒检查纸鹤文件，仅当前对话，不用Cron；让背景Noting设置一次性Schedule”；观察Main通过memo，真实Noting create user_reminder expression `in 2m`，humanNotebook确认Schedule后等待到due，R idle自启Main、O无提醒。另一次输入创建同带时区绝对due的两条deferred事项：“我承诺校验封面”和secretary_task“到时跟进验收结果，明确deferred，不自行执行”；确认真实NotebookSchedule后等待到期，期间不发R请求，应无Turn/无deferreddurable行；随后自然发“当前到期事项有哪些”→保存批量timeline及Main响应。再建未来once“off恢复标记”，待Snapshot/空memo后 `/noting off`，跨due观察无投递， `/noting on` 后恢复一次，并继续自然问/刷新确认不重复。
- 预期：idleinstant真实 `<instant-reminder>` durable role=user和entry timestamp、同R真实新Turn提醒文件。deferred不自启，到真实请求前一条durable carrier批量 `以下提醒已到期。`+两个entries JSON，schedule变实际due_at，无timestamp、timeline隐藏wrapper，Main正确回应两事项且ACK后再问不重投。off保意图、不fire；on overdueonce至多一次恢复。O实际查看不含R提醒；官方Cron页无新job，无cron_新独立Session，无模型自行执行secretary_task。提醒产生/再读均完整结果，不用只读Registry替UI。
- 实际/状态/效果/证据/时间：未执行；拟 `validation-closeout/CU06/`；真实钟表，不改due_at；偏差无。

### CU07 真实busyinstant→同Turn下一请求deferred→ACK不重复

- 意图/依据：忙时提醒不丢且不排第二Turn；02§3.12/§5.6/§6.17、04§7.3(5)。版本82cd557，R、真实Noting已建立未来once“蓝图-忙碌提醒”；due时刻由真实Schedule可读确认。
- 步骤：due前经CHAT明确要求Main亲自用既有terminal执行不读写外部文件的短暂sleep（按剩余真实秒数选能跨due的时长），随后工具返回后继续回答；观察busy窗口和due→保存下一真实模型请求、deferredtimeline及回答→Turn结束再自然问“是否还有同一蓝图提醒”→刷新。不从验收者shell调用sleep伪造Mainbusy；不预造pending，不另排瞬时Turn。
- 预期：原生busygate把instant转pendingdeferred，下一真实request携带，Main回应标记；role=user deferred无timestamp、单timeline事件，ACK后不重复due，不在Turn结束再启第二个instantTurn，R仍可继续。机制ACK失败/compaction拒投/崩溃重投按CE01复用，成功后续自然请求是本次可观察不重投证据。首尝试如忙窗口未覆盖或工具未合法执行，记录真实偏差与未完成，不自动重复昂贵构造，交root决定后续。
- 实际/状态/效果/证据/时间：未执行；拟 `validation-closeout/CU07/`；偏差无。

### CU08 Full最新实际来源、branch/undo后用户意图可继续

- 意图/依据：审计真实有效上下文、分支不串数据、撤销后只读有效原文；02§2.4/§2.6–2.7/§3.3a/§6.11–6.14、04§2.5/§7.3(6)。版本82cd557，先用前述真实Snapshot/Anchor及原U01压缩产物。
- 步骤：从现有只读Full入口读取/保存实际Prelude和节点，重复读前后确认不启动Turn/后台；官方CHAT `/branch 纸鹤收尾分支`→分支 `/notebook`/Main show核继承→输入“分支页眉改用银色，父会话不变”，真实Noting后看分支更新→官方 `/undo` 撤回该最后用户交换，按UI合法prefill/新输入“撤销银色，改为分支页眉白色”；MainHistory核失效银色路径不返回，再等真实整理核Notebook pointer落有效Anchor及白色意图；通过Dashboard恢复父会话看原Notebook/History未被分支改动。必要时新会话入口核新Ref但不破坏原父。
- 预期：唯一首Prelude无Message Identity，root/tools来自最新真实provider_neutral_request或可信恢复，缺失须诚实不猜；普通节点每Identity唯一，compaction/Snapshot/Anchor位置与实际产物相符，Finish不推进Anchor，日常无termination。branch新Ref、继承内容/Anchor重绑且隔离；undo按原生语义删除失效路径、pointer退至有效Snapshot，后续输入能继续并不会复活被archive候选。Full读取无副作用。复合carrier若本次压缩没有保用户双部分，明确本次未观察，复用已核正式同源相邻双投影证据且核当前Full文件hash/影响；不改成NA、不为复合例灌昂贵压缩。`/undo`是只读代码已确认的合法用户历史操作，不使用文件checkpoint `/rewind` 或直接DB更改。公开入口阻挡则记范围内未完成/失败而非伪造操作。
- 实际/状态/效果/证据/时间：未执行；拟 `validation-closeout/CU08/`；偏差无。

### CE01 必要机制/真实模型证据的适用性闭合

- 用户目标：确保上述典型旅程的权限、身份、后台生命周期、失败恢复与原生回退有全范围证据；依据01§6、02§6及04 M01–M28/§7.2、C07–C09/C13。
- 操作/预期：只读当前Verification逐项矩阵和artifact，核版本、manifest、源码影响与支持边界；身份alias/conflict、atomicSnapshot、item INSERT-only/归档无恢复、禁止工具、memo并发与失败、exactly-oneIdle/Force、External拒绝、两Profile真实terminal/五Turn/context_overflow、父原生adoption/cancel、Reminder ACK/compaction拒投/重启、compound、C13成功区间过期/取消失败不误清/同文lookalike保留，均须有当前有效证据。C13 `same-turn-observation.json`与commit-before-loader等是正式Main/DB受控机制而非真实Dashboard模型，本次不得混称UI观察。被当前改动破坏或缺证者报root定向补证；不重跑有效大检查，不以机制通过代CU实际用户结果。
- 实际/状态/证据/时间：准备已读相关路径与real-native-handoff保留失败，最终适用性待Verification当前报告；未关闭，拟 `validation-closeout/evidence-reuse.json`；偏差无。

## 5. 问题、修复与复验

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| VAL01（原失败保留） | 旧官方CHAT Main→Idle2→Snapshot于23:20:55提交→23:21:30仍无timeline | Finish真实durable存在但用户未即时看见；原 `validation-final/U01/after-noting-no-notice` | 修补已集成不等于通过；本次CU04未执行 | bc9cd6d7a1，当前82cd557 | 等放行：Idle完成即时timeline＋单UID持久＋下一Turn/reload；busy尾部受影响随CU07/证据复核 |
| VAL02（原失败保留） | 旧localon→真实Noting→/notebook 515chars→AX/可见箭头均不展开 | 应完整人类可读，实际只有折叠标题；原 `validation-final/U02/local-on-fold-*` | 修补已集成不等于通过；本次CU02未执行 | bc9cd6d7a1，当前82cd557 | 等放行：同515chars或更长Notebook真实全阅读、localoff继续读、reload/后续使用 |
| — | 本次仅只读准备 | 无新增产品失败；未操作不得称通过 | 全部本次场景待执行/证据核对 | 不适用：尚未出现新问题 | 有新失败时追加完整输入/时序/版本/证据，不删旧记录 |

发现范围内差异按原判据报root研讨，验收者不修改产品或放宽要求。若同原因重复三次仍未解决停止重复尝试、做根因复盘；修后需新独立全轮复审与相应原用户场景复验，不只查失败编号。

## 6. 验收结论与推荐复核

本次计划已从完整冻结要求独立导出。CG01复用旧跨压缩合法历史但新版C12未验；CG02 cold/warm/六键及VAL02未验；CG03 memo四操作与VAL01未验；CG04 proposal/修订/实际批准写入/归档未验；CG05真实Schedule的idle/busy/deferred批量/off恢复/Conversation隔离未验；CG06Full/branch/undo仍未验；CG07当前正式证据适用性尚待独立Verification报告和artifact闭合。**Validation门禁未关闭，当前只有计划与合法准备，不能声明本轮完成。**

推荐主会话核准上述CU01–08顺序、CE01证据边界及安全Cold协作后，待Verification通过明确放行。执行后用户复核主路径为：官方Dashboard恢复纸鹤→原文search/read与六键show→完整长/notebook→memo维护与即时Finish→候选查源、修改和明确批准→R同对话真实到期与busy恢复→分支撤改→回父确认→root cold恢复。每步实际输入、工具结果、timeline/截图、持久后续读及版本证据写入本次目录；最终目标判定由root负责。


### 收尾执行首次观察（2026-10-12，CU03／VAL03）

当前Verification 73组、72符合、0违规、0不足、1阶段责任不适用，已由root接收并正式放行。执行首次用户路径：IAB3/tab1打开官方53345→Dismiss metrics notice→CHAT→点击旧36msgs纸鹤合成会话（URL resume=20261011_231755_2fc826）→terminal空白、“Chat connection interrupted. Reconnecting...”→官方Reconnect chat语义点击一次仍同样提示。未输入模型或修改配置。只读upgrade-server日志确认chat WS在PTy argv解析前调用官方source TUI build，`scripts/build/tui.mjs`的productOutput拒绝仓库内隔离profile的`cache/scratch/hermes-tui-…/tui`：要求“Output must be outside source or in a supported generated destination”。真实入口不可用，已有bundle/hash与HTTP200 readiness不能代替。

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| VAL03 | 如上首次CHAT恢复原Session→官方重连一次→仍空白 | 预期可恢复原合成Conversation发coldoff Main；实际source build输出校验异常，CHAT连接中断。`validation-closeout/CU03/initial-reconnect.*`、`after-official-reconnect.*`、`startup-build-failure.log`、`VAL03-startup-failure.json` | 官方用户入口阻挡，已报root；自身tab已关闭防自动重复；CU03及依赖旅程尚未执行，不改NA | 待root处理；验收者产品只读未修 | 正式入口恢复后同profile/Session首次coldoff原序列复验，随后按核准计划继续 |

CG01–CG07本次仍未闭合，VAL01/VAL02原失败继续保留，VAL03新增范围内入口缺口。推荐主会话先处理正式启动/构建路径边界，验收者不回退其它UI/CLI或绕正式入口；恢复后补当前runtime/版本及实际输入输出。Validation未通过。


### 正式预构建入口恢复与初步结果（CU01／CU02／CU03，2026-10-12 17:10–17:15）

root采用原生HERMES_TUI_DIR显式预构建入口保库重启为PID68046（配置globalfalse，3/79/2与配置凭据hash不变）；HEAD dff417d2为文档提交，产品仍82cd557同源。验收者IAB3/tab2重新经CHAT→原36msgs纸鹤恢复，正式进程Node68713 `ui-tui/dist/entry.js`→Python68714 `tui_gateway.entry`，所属HERMES_HOME/PYTHON/TUI_DIR正确，证据CU03/runtime-processes.json。VAL03原入口已可用，首次失败保留；不改build guard、不CLI fallback。

首真实coldoff Main亲自keyword/regex-user/read三工具调用，准确蓝→绿、取得35项全文/末标。实际成功Historyenvelope四键success/conversation_ref/messages/count；全部searchrow四键加既有truncated，readrow四键，无重复ref/Identity或物理地址；原长源search截断、精确read含第35项与全文末标。实际Prelude来自provider_neutral_request，History工具/指导在、Notebook/Memo工具及Notebook指导均缺席。CU01新版C12通过，CU03coldoff通过；旧U01跨压缩史合法复用。证据CU03/cold-off-input.txt、cold-off-completed DOM/PNG、cold-off-state.json、cold-off-C12-proof.json。

CONFIG独立tab3保持聊天warm连接，正式保存globaltrue与临时Idle120（原2），为旧长Notebook/memo防消费；这是临时顺序调整，不更改产品规格。真实 `/notebook`同旧515charsSnapshot完整呈现Created at 1791732286.999451、四区、绿色/无目录决策与页脚open question，无Anchor/pointer/termination，CU02/long-notebook-original DOM/PNG；VAL02原同长状态初步复验通过，后续localoff/再读仍继续。已发真正Main show+Anchor查源请求，尚待结果。

用户新增C14验收授权由root传达：可临时调合法现有配置加快真实链路；自然Idle基准30秒，memo必要时可更长，全部验完恢复初始2秒。必须真实Main结束→timerarm→真实时间→Noting，不允许直接trigger/tick/任务函数、伪busy/时钟或DBdue写入。当前120临时窗口在便签操作后恢复30；运行时所有配置仅隔离profile、官方入口、记录前后值。


### CU02／CU04真实结果及计时交错（2026-10-12 17:14–17:22）

CU02真实show外层success/notebook、内层六键四区+last_update_time+anchor_message_uid，值分别1791732286.999451与dd280e18f8394826938ee1729fd529b8，和实际Snapshot同值；Main自己session_history精确read Anchor原Assistant页脚确认，warmon Prelude Guidance/show/memo同步恢复，证据show-anchor-completed DOM/PNG、show-anchor-state.json、show-six-key-proof.json。随后空memo `/noting off` 用户可见且持久；CONFIG正式将120→30，在新localoff Main输入前保存。Main仍实际show+History、/notebook完整515chars。等跨30实际deadline后snapshot2/sessions3不增；两读数间154.37秒，root/tools逐字相同、Snapshot同一，见local-off-after-idle30.json/local-off-proof.json、local-off-main及human DOM/PNG。不是在120配置下只等30。

CU04官方CONFIG30→120暂延，Main六真实noting_memo调用按指定顺序完成：add绿色index1并auto-enabled、add目录待确认index2、Markdownlist、replace2“不要目录”返回replaced+完整list、delete1绿色返回deleted+重排index1、最终list1“不要目录”。非空/noting off真实拒绝，明确Background Noting stays on while memo non-empty。然后CONFIG120→30在自然Main启动前保存，真实无工具短Main结束后实际idle_state end=1791796803.361171/due=1791796833.361171/trigger=1791796833.367473，差30秒、lateness0.006302秒；admit6833.381725→commit6849.945511，memo“纸鹤封面不要目录”同Anchor ce0e2f…归档/消费，当前active空。没有直接arm/trigger/tick/DBdue修改；自然30输入与工具反馈、CONFIG及Finish均有DOM/PNG，state及proof在CU04/。真实Finish在现有timeline完整显示标准英文、无wrapper/timestamp，首次观测无需刷新/追加输入；随后第二Task也显示单条自身通知。VAL01用户可见链路初步复验通过，待后续持久再读。

同时保留真实计划偏差而不静默：第一Idle Task在六memo Main回合中admit1791796727.605147，冻结到UID04a9e92f…并拿前两条memo；期间Mainreplace/delete，第一Task commit6803.469644但没有错误消费替换后条目，未新增archive；下一自然30秒Task才消费新一条。两不同Anchor/两Snapshot/各一Finish，不能把第一Finish冒作新自然Main的30秒结果。第一Task的准入是否源于合法catch-up或busy Idle边界疑点已立即报root研判，保留全部时序，不以memoauto-on解释成memoTrigger；并发消费不变量本次真实成立，但Trigger合法性结论等待调查。当前已发消费后Main list/show复读请求，其它旅程仍待执行。


### VAL04：localoff Main内memo自动on后，旧Idle catch-up在真实Main仍忙时准入（已确认）

本次额度恢复只读核PID68046仍运行、官方Node68713→Python68714仍所属同profile，配置globaltrue/Idle30，当前6sessions/5Snapshots/memo空；HEAD相对82cd557仅根/轮次文档变化。消费后真实Main已list返回精确空态并show正确Notebook，期间自然30秒还产生自身一份Snapshot/Finish，属于新Main独立idle周期而非Finish自激。

先前第一Task时序现已核清，不是合法post-end Idle：真实同一memo Main driving user于1791796722.572049进入，六串联真实工具运行；第1add auto-on6724.690250、第2add tool UID04a9e92f…于6726.711425，Idle admission6727.605147，后续list tool6728.425066、replace6730.757147、delete6732.301656、list6733.706476，最终Main回答6737.116671。Idle准入在同Main结束之前约9.51秒，冻结第二个工具结果Anchor，因而真实busy，不从memo位置或单DB计数猜测。旧持久Idle记录还指向先前on-state Mainend6464.779992/due6584.779992；localoff时新Mainstart被gate取消计时但未更新这份旧记录，memoauto-on后host catch-up读取旧闲置事实并准入，缺少真实Main仍忙校验。只读代码证实 `_record_main_turn_event` 在off gate前不记录本次start；TUI poll及attach仅看旧persistedidle，无当前Mainbusy拒绝。

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| VAL04 | 原on Mainend并持久deadline→localoff→deadline过去→仍off的真实Main里依次add两memo（第1auto-on）→当前Main尚有list/replace/delete/read与最终回答→hosttick Idle准入 | 02§4.5要求真实Main结束后的idle期、新Main取消/重排且fire回查still-idle；§3.5 memo不是Trigger。实际旧deadline catch-up在真正busy Main内准入，admit6727.605147早于该Mainfinal6737.116671。`CU04/VAL04-busy-idle-finding.json`含完整真实消息/时间/UID、原旧Idle状态、admission/Snapshot及只读接线；旧6操作DOM/PNG与after-finish-state保留 | 范围内Idle时序缺陷确认，需root修产品；后续尚未执行，不降判据。第一Task的有效状态/并发memo保留及第二自然30timer事实仍保留，不冒整场景PASS | 未修，产品82cd557 | 修后须原序列localoff→真实Mainadd auto-on→busy工具循环不得旧Idle准入；Mainend→真实新30秒→唯一自然Idle并完整memo消费/即时Finish；相关coldcatch-up与原off路径影响须核 |

证据已经足够构成正式用户路径反例，无需重复昂贵模型构造。当前停止新的模型输入，产品只读、保持profile数据；按授权仅将实际缺陷与所需修复动作交root。CU05–08仍未执行，Validation未通过，VAL01/02已有复验事实不因本次缺陷删去。


---

# 收尾阶段报告：VAL04 阻断与安全交接（2026-10-12）

## 1. 结果概览

独立验收者 `validation_closeout`；完整冻结依据31b1f757的01/02/04及本轮索引，C14操作补充冻结40d3c992d1。待验产品源码82cd557不变，后续HEAD仅文档提交，已只读核差异。主会话完整核准CU01–08/CE01计划并接收当前整版Verification PASS后，验收者实际经官方Dashboard＋真实DeepSeek Main/Noting执行。中断后按落盘状态恢复，未重跑有效用户链路。

**阶段结果：Validation未通过，VAL04是新确认的范围内Idle时序缺陷，需修复并复验。** 已关闭原VAL03用户入口阻挡；CU01/C12、CU02六键/Anchor/人类长文/localoff读取、CU03coldoff/warmon，以及CU04 memo四操作/编号/auto-on/拒关/并发保留/自然30秒消费/Finish可见/空态后续使用取得有效实际证据。VAL01和VAL02用户可见问题在本版有真实关闭证据，原失败未删。CU03剩余切换/coldon、CU05–08及CE01最终复用核验未完成，不改为不适用。

## 2. 环境与准备

- 唯一隔离profile `.hermes-dev/v1.6-validation/dashboard-final-4743943e`，官方入口53345，Dashboard PID68046保留。有效执行进程为Node68713 `ui-tui/dist/entry.js`→Python68714 `tui_gateway.entry`，HERMES_HOME、工作区Python和原生HERMES_TUI_DIR归属已核；不CLI fallback。采用官方DeepSeek deepseek-flash思考模式Chat Completions，产品/provider/API/锁文件未修改，凭据不输出。
- 初始3sessions/79messages/2Snapshots保库升级，原纸鹤合成对话、真实压缩史和旧长Notebook复用。阶段交接6sessions/157messages/5Snapshots，memo0；五个Noting Child均status completed、durable ended。Notebook保持三条原工作状态。新增全部是获授权合成验收数据，未读私人Pi、docs06、其它profile或真实HOME。
- CONFIG合法变更顺序globalfalse→true，Idle2→120→30→120→30；120用于保留待复验长文/memo操作。现globaltrue/Idle30，初始Idle2待最终全部验收后恢复（C14），阶段修复交接保30；没有改schema/default/规则。config/model请求在合法边界使用，未倒灌在途请求。
- 真实30 timer证据：Mainend1791796803.361171、due6833.361171、trigger6833.367473、admit6833.381725、Snapshot6849.945511；未直接arm/trigger/tick/任务函数、修改due、伪时钟或busy。
- 主会话接收VAL04后授权安全关闭本次CHAT/PTY。只关闭本次tab2/chat及tab3/config；页面关闭后官方PTY仍驻留，按完整argv/profile/PID核验仅对 own Node68713/Python68714发送SIGTERM，二者均已退出；Dashboard68046不动、child tree空，Main/Noting/compaction无在途，允许root保库重启。证据 `safe-handoff-state.json`、`safe-handoff.json`、`own-chat-stop.json`。期间诊断脚本两次本地导入问题（脚本sys.path、hermes_yaml导入形式）修正仅ignored脚本，不是产品失败。

## 3. 用户目标与场景覆盖

| 目标编号及冻结依据 | 完整场景编号 | 场景类型与起点 | 数据/顺序选择依据 | 当前执行结果 |
|---|---|---|---|---|
| CG01；02§2.3/C12/04§7.3(1) | CU01 | 旧真实压缩史→新版keyword/regex/user→精确read→正确回答 | 35项长源/truncated/末标与蓝→绿更正，旧U01完整旅程合法复用 | 通过新版C12与后续原文使用 |
| CG02；02§3.5/§3.6/§4/04§7.3(2)(3) | CU02、CU03 | coldglobaloff→warmon→show/Anchor；localoff Main读与跨deadline无后台 | 同旧515charsSnapshot，现show六键/人类全读，真实root/schema前后相同 | 六键/Anchor/长文/localoff读取通过；普通空memooff/on、剩余warm/coldon未闭合 |
| CG03；02§3.5/§4.5/§5.6、C03–C05/C14 | CU04 | localoff→六memo操作→auto-on/拒关→真实自然30→消费/通知/复读 | 第一任务中途冻结两旧memo后replace/delete、下一任务仅消费新内容 | 便签/消费/通知结果通过；首次busy Idle准入VAL04失败，整体场景不能PASS |
| CG04；02§2.5/§3.7、04§6/§7.3(4) | CU05 | 真candidate→自主查反证→修订→批准真实Memory→归档 | 合成限定范围与原/更正证据 | 未执行：因VAL04待修复，保留原计划 |
| CG05；02§3.8–3.12/§5.6、04§7.3(5) | CU06、CU07 | 真Schedule→idleinstant/deferred批量/off恢复；busy下一request | R/O隔离、once与同due批量、真实Main终端sleep | 未执行：因VAL04待修复，禁止改due/伪busy |
| CG06；02§2.4/§2.7、04§2.5/§7.3(6) | CU08 | Full→branch→新意图→undo→更正→回父 | 合法共享Slash，只合成数据；compound按有效同源机制证据 | 本阶段仅已有真实Full补观察；branch/undo及最终审计未执行 |
| CG07；01§6、02§6、04M01–M28、C07–C09/C13 | CE01 | 有效机制与真实模型证据适用性→当前用户结果 | 不重复昂贵边界/大型检查，旧失败不整体冒PASS | 计划边界已核，最终artifact/hash闭合未完成；VAL04说明仍须补机制 |

这份阶段矩阵以实际执行结果替代当前结论；前文计划和旧版本记录作为历史保留。所有未完成仍是必要范围，不能以已通过小项或新缺陷为由降为NA。

## 4. 详细场景与执行结果

- **CU01/C12、CU03coldoff**：17:10同原Session真实Main调用keyword“青松-731”、regex“青松-731|霜叶927”+user及message_identity read。三个真实工具成功result均只有success/conversation_ref/messages/count，rows四键±既有truncated；search长源截断、precise read含第35项和全文末标、Main准确最初蓝/最终绿。真实Prelude provider_neutral_request、History指导/工具存在，Notebook指导/show/memo缺席。`CU03/cold-off-{input,completed,state,C12-proof}`；旧U01跨压缩输入/输出/压缩史同源复用，不重新构造长源。
- **CU02/C10/C11与VAL02**：CONFIG独立tab保持原CHATwarm；真实show仅外层success/notebook和内层六键，time1791732286.999451/Anchor dd280e18…与同Snapshot值一致；Main自己History精准read Anchor原Assistant确认页脚。官方/notebook同515chars旧Snapshot全部正文可读，Created at及四区完整，无Anchor/pointer/termination，localoff后同样可读。`CU02/show-anchor-*`、`show-six-key-proof.json`、`long-notebook-original.*`、`local-off-human.*`。localoff新真实Main仍show/History；实际持久旧deadline6584.779992，off读数 at6677.486445已经跨过该deadline，且CONFIG已在新读Main前保存30；两读数154.37秒，sessions3/snapshots2不增、root/tools逐字相同。即使按旧120deadline判断也已跨过，而不是只证明短于有效deadline的窗口。`CU02/local-off-{input,main,after-idle30,proof}`。计划新增“页眉”事项未使用，本次改为无新事项只读，避免模型必须memoauto-on污染off观察，边界已记录。
- **CU04便签效果**：六真实串联调用add绿色→add目录待确认→list→replace2不要目录→delete1→list，逐项实际反馈完整，auto-on及连续编号符合；非空off拒绝解释持久。`CU04/memo-input.txt`、`memo-six-completed.*`、`memo-six-actual-results.json`、`nonempty-off-rejected.*`。原计划单任务简单消费被真实交错改变，未隐藏：第一Child拿旧两条memo后Main替换/删除，旧Taskcommit没有清掉替换后的新条目；第二自然30Task将新“不要目录”同Anchor ce0e2f…归档/清空；真实list精确“No memo after last noting”，show正确工作状态且memo不进入Notebook。`after-finish-state.json`、`memo-natural-timer-proof.json`及`post-consumption-*`。便签不变量有真实证据，但首TaskTrigger违规另记VAL04。
- **VAL01**：真实timeline出现各Task独立统一英文Finish，无raw wrapper/timestamp，不需追加输入/刷新才能看见；第一次commit后首次UI观察即存在，第二自然30Task亦显示自身单条。后续Main继续使用以及中断后的原页仍可读三条各独立Main/Task周期通知，没有Finish自激；通知时间均对应各Snapshot，不合并旧/新Task。`CU04/instant-finish.*`、`natural30-finish.*`、`post-consumption-completed.*`及原durable同UID通知。精确观测时刻上界以截图文件落盘mtime记录，不能把每次模型采样间隔冒作零延迟。当前通路用户可见缺口已复验关闭，范围内Trigger缺陷仍阻断总体。
- **VAL03**：原官方CHAT恢复入口在source TUI build输出目录校验前失败，首次DOM/PNG/日志保留；root仅使用既有HERMES_TUI_DIR原生prebuilt分支保库重启，未改guard/产品。验收者重新经同官方入口成功恢复原Session、真实Main查源、实际Node→Python归属正确，关闭该用户入口阻挡。详见原完整序列与`CU03/runtime-processes.json`。
- **VAL04**：完整序列、精确Input/Tool/Admission/结束时间和只读原因分析见上方问题节及`CU04/VAL04-busy-idle-finding.json`。没有重复模型复现、修改产品、伪造busy或内部调用。当前未输入CU05–08，保留最初核准的合法下一步输入。

## 5. 问题、修复与复验

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| VAL01 | 原Idle提交后35秒无timeline；当前实际Idle/交错Task完成→用户timeline→后续Main复读 | 新版真实通知标准英文、各Task单条、原页/后续可读，原失败保留 | 用户呈现缺口已关闭，整体受VAL04阻断 | bc9cd6d7a1并入82cd557 | CU04真实结果和post-consumption最终画面；新Idle修复后不得损坏通知 |
| VAL02 | 原515charsNotebook折叠不可展开；当前同Snapshot/notebook→完整四区→localoff再读 | 同515chars完整真实人类阅读、后续AI查源/再读，旧失败保留 | 人类读取阻挡已关闭 | bc9cd6d7a1并入82cd557 | CU02原长Snapshot及localoff真实截图/正文 |
| VAL03 | CHAT恢复→sourcebuild输出guard异常；rootprebuilt保库后同CHAT恢复 | 新入口真实Node→Python与profile匹配，Main实际完成查源 | 已关闭环境/启动入口阻挡，不改产品guard | 产品82cd557无改动、原生HERMES_TUI_DIR合法启动 | 同原Session复验通过；后续root cold沿用合法prebuilt |
| VAL04 | 旧on Mainidle未claim→localoff并经过旧due→新off Main add auto-on→同Main后续工具/回答未完→旧catch-up Idle准入 | admit6727.605147在同真实Main driving6722.572049/final6737.116671之间，冻结第二add tool；不符合02§4.5still-idle/新Turn取消重排，memo§3.5非Trigger。完整证据/源码定位见finding | 新确认范围内缺陷，root已接收并安排最小修复/新独立审查；当前未关闭 | 待修 | 原真实localoff→Mainaddauto-on→工具循环期间无旧Idle；end→自然30→单次整理/消费/即时Finish；核冷catch-up/localoff/globaloff、不得新增触发或放宽规则 |

只因本轮后续真实操作被缺陷阻断而留未执行，不新增产品NA或授权变更。旧计划、成功事实、失败与诊断原文均保留。

## 6. 验收结论与推荐复核

Validation门禁未关闭，当前阶段应交回修复。安全状态：Dashboard68046仍保留、child tree空、自己的68713/68714均已退出，globaltrue/Idle30/memo0、DB6sessions/157messages/5Snapshots，无在途Main/Noting/compaction。可以保库升级新修复版本，不重建合成数据、不删历史失败；最初Idle2须在最终所有场景完成后恢复。

恢复后的首要用户复核是VAL04原合法序列，不能只执行自然30成功分支。新独立Verification确认修复和全范围影响后，再从保留合成历史继续CU05–08、剩余warmglobal/coldon及CE01，不重复已经有效完成且源码路径未变的C12/六键/长Notebook准备。Cold始终root安全协调。阶段交付证据入口为本报告、本次目录`safe-handoff.json`和`CU04/VAL04-busy-idle-finding.json`；最终目标结束与交付判定由root负责。
