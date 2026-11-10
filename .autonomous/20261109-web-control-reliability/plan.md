# 实施计划 · 20261109-web-control-reliability

## 1. 目标与依据

依据snapshot-index.md与baseline.txt（12e2b45）；产品起点BE main b4ed135、FE cd5d12f，集成V4候选b232后BE为2e91189。先复核旧故障，再沿同一原生运行实例实现完整Web控制，最后main联合发布／确认V4实际生效。root已完成旧故障首轮复核，尚未解决项不冒称完成。

优先完成纵向链：App输入→正式RPC原子受理→真实runtime/Pending/维护→流式／回执／控制结果。稳定operation、owner、commit fence先于展示。沿现有Session、原生lease、Pending和队列持久事实，不建新通用gate、writer、调度器或对话存储。旧默认接口保持，Web capability opt-in；首选既有prompt.submit增加input_policy=web_controlled，名称可在正式协议交接时沿现有类型风格收口。

完成条件（按用户2026-11-10执行方式纠正）：U01–U15正式接线和针对性证据、root认真审查与实际故障复验通过；main实际服务／静态／APK版本及原签名一致；V4自然运行可核；范围内缺陷清空。无ADB真实手机的现场边界明确，不伪称完成运营商归因。

## 2. 覆盖与任务表

| 任务 | 要求与依据 | owner／白名单 | 依赖与接口 | 验证／完成判据 |
|---|---|---|---|---|
| B1 后端完整控制 | U02–U08/U10；白板K1–K8、N0–N4、P1–P5、D6/D8；07顶部21–39、87–128，§3约680–715、§6 1641–1771、§8.1 1826–1845、§8.13–8.15 1999–2091；02身份、3.11–3.12、5.4–5.11，04原生边界／cache，08全篇，06最新合同 | backend_control；tui_gateway既有Session/owner、prompt、Pending、recovery、通知／scheduler_host、interrupt、web_read及contracts和对应siblings；agent/pending_steer、turn_context、compression_read/partial/observation及registration接缝；必要active_sessions元数据与gateway/run_busy claim接缝；对应tests。禁止改算法公式、Prompt、锁仲裁、原生schema、部署或核心文档 | 已集成V4；交F1原子受理能力、control快照、可查询输入receipt、maintenance快照／delta。先交可实际接线的协议和状态转换表作为一次完整里程碑，之后整包交回。维护Stop按本轮E01仅取消维护、保留已受理输入 | 真RPC＋nativeLoop＋SQLite，受控外部Provider；覆盖启动／冷建／结束／idle竞态／各内部来源／维护提交取消／Force／双窗口／tip／跨Profile／重启／ACK丢／真正Gateway及旧wechat误判。V4冷HB零API时已受理真人不丢、不改source绕guard；真人观察一次、无假blocked_send，原claim退款和Reminder ACK保持 |
| F1 前端故障与控制 | U01–U09/U12；06顶部、C1–C8、11/8折叠及恢复／局部更新／维护合同；07相关维护／Force／Heartbeat | frontend_control；独立FE src/api、src/core/controller及siblings、timeline-folding、ChatComposer与压缩展示、相关测试和正式生成协议；必要既有Android诊断白名单兼容，不改Gradle／依赖／版本／签名／根文档 | 先修折叠并审seq覆盖，后按B1正式协议接实际Controller/App；不以mock-only代替接线，不busy后自动retry | 同页未知→已证边界恢复旧组，active展开／用户展开保持；各phase Enter/button/Stop、查询回执、ACK未知／owner切换、维护部分摘要恢复；正常事件零整页恢复。seq必须核真实作用域，不能把合法全局跳号误判缺口；C2 Unknown/typed回归。UI仅自建隐藏IAB |
| A1 V4整合 | U10；算法V4 C01–C23、D1–D4与保留V3合同 | root；merge／文档／微小跨包接线，算法公式不委派控制权子Agent | b232已合入2e91189，27模块与原验收SHA一致；控制输入与adaptive接缝待联验 | 复用32文件556机制和独立23场景同版证据；补控制输入×冷HBguard／当前配置／首读许可／维护提交取消。线上只读核配置和自然request/decision，不制造生产模型测试 |
| V/Va 两独立门禁 | U01–U12全部适用条款 | 各全新无上文独立Agent，产品只读，分别report与ignored证据 | 集成收敛及root亲审后，先Verification，阻断清零再Validation | 按冻结原文先建矩阵；实际产品入口与隔离数据；同版证据复用，必要反证真实运行 |
| R 联合发布 | U08/U10–U12 | root；main合并、0.1.14版本、构建／部署与运维记录 | 门禁通过，稳定源码，原签名，服务安全空闲 | 原生main发布器、实际资源清单manifest/HTTP、APK签名/ZIP/ELF/资源、双端ID；保最近两套三库；无ADB实机不冒称实导，脚本和格式仍交付 |

## 3. 当前状态与编排

**当前状态：** root已完成D38和诊断两包实际代码/正式接线/失败路径/测试调整及25源指纹审查；FE655ecf5已提交推送，正构建0.1.14/1014。419项D38相关回归、62项诊断前端、native Schema8/受影响1与Provider6复用及root六浏览器日志案例按各自范围有效。原白屏修复后实际IAB待最终dist；通过后直接main联合发布并核V4自然事实。没有宣布已上线。

**执行方式纠正（用户明确）：** 挂目标、持续推进与恢复子Agent并非授权完整自主实现流程；用户要求保留认真审查、灵活执行。停止新的整轮门禁/模板轮转，采用必要代码审查、针对性测试、实际反例复验和发布核对。既有V6固定79的58项54符合/2违规/2后继不足及原D38红保留历史，不强改绿；后继以真实修复/复验事实关闭当前问题，不再要求新一轮全套报告。

**21:18当前执行事实：** B1正式Lock／D18包已由root亲审；D20排序包已接收，49传输／52身份回放／4stdio证据有效，root核hook、Tee、旧子类和健康端credit接线。root两行旧字符串queue兼容修正获3项绿；protocol另两失败在未改12e同源基线复现（`root-protocol-baseline-two.log`），不算本轮新回归。F1 R5（37源清单15bcb…）285项／type／health及真实网络lost-ACK链已交；root实IAB终态Stop通过，D24异步owner反例补验中。新joint lab使用当前B1＋D20及修正后的真实streaming返回探针，frontend_control_resume独占联调动作，补维护／API返回至terminal连续链；root不并发操纵。apk_release_prepare仅五版本文件及ignored构建证据，待最终源冻结后打0.1.14。尚未独立双门禁、main合并或发布；旧表的调查描述保留为发现时点，当前状态以本段和后续闭合证据为准。

用户恢复目标后新增U13前置顺序：先完成连接／控制层真实连续Turn联调，取得Socket、seq、native身份、recovery_view及控制快照证据并修复该层已证缺陷，再亲审Timeline必要结构调整。B1准备真实WebServer/WS/nativeLoop＋受控外部Provider/barrier，F1先诊断Gateway→ControllerPageRecovery，root亲查生产只读元数据。已做R4折叠候选保留但不当作整体通过；静态历史、独立单Turn及JSDOM理想顺序不足以证明连续使用稳定。

连接／控制前置检查按既有U条款展开，不是新增产品语义或独立门禁：

| 观察边界 | 应证明的不变量 | 当前证据／缺口 |
|---|---|---|
| Socket→事件接收 | 同runtime/epoch事件覆盖有序；真断线与页面恢复区分；健康流式不主动误断 | 旧有界Fanout同源证据；root18:47线上40事件seq39123–39162连续；连续Turn隔离实测待补 |
| 原生Turn→控制通知 | 同一真实生命周期的身份／开始／结束一致，不误开新轮，不让旧终态或清理覆盖下一轮 | 启动通知重复与running释放后的清理窗口正在正式同源探针验证，不静态定案 |
| 控制RPC→原生owner | 正式Lock下启动／活动／维护／收尾均及时受理或精确拒绝；Stop／撤回只作用原目标，无复活输入 | D18红→绿待root整包审；D19正式Lock整改前的RLock证据不证明这条 |
| REST窗口＋WS恢复cut | 活动期可在有限一致cut交接；普通局部变化不反复整页恢复，不等Turn结束才获得可用控制与实时输出 | root5次active＋8次idle正式读取完整；真正连续边界及客户端commit状态仍待实测 |
| ACK／失败／重连 | 已受理输入可查且不自动重放；未知保持诚实，新显式用户动作有控制；旧owner回调不覆盖新状态 | 原B1/F1反例与窄修已交，正式Lock和真实网络联验后再接收 |

前置已证缺陷闭合后，才扩Timeline渲染结构：同一消息单份显示、流式连续、旧折叠和用户选择稳定、正确spinner、稳定阅读锚点；用同一连续链验证，不用静态历史替代。

| 目标 | 机制 | 正式接线 | 针对性证据 | 用户结果 |
|---|---|---|---|---|
| 0.1.12/13连接／Thinking／Enter修复 | 已有 | 已发布 | 有同版证据 | 不能证明全部历史断连已归因 |
| 折叠边界 | fallback永久保留已有候选修复，最新活动Turn全展开反证仍待闭合 | F1追加实际App交接 | root组件反例及用户最新现场 | 已证历史组在Steer／新Turn交接始终保折叠，当前Turn展开 |
| 内部运行完整控制 | B1首版／正式接口已交 | F1已接实际App，补回归中 | 初版机制与App定向测试，待整包亲审 | 0.1.13仍不合新合同，新候选未发布 |
| V4 R4 | 已合隔离分支 | 新控制待联验 | 27模块源相同、旧证据有效 | 尚未线上生效 |
| 联合发布 | 未开始 | 未开始 | 未开始 | 线上仍9270933/cd5d12f/0.1.13 |

并行仅B1与F1，仓库和白名单隔离；root负责实际diff／上下游审查、协议协调、证据覆盖与集成。子Agent禁止派生、禁止提交、禁止流水账；仅真阻断、必须root决策或约定完整协议里程碑发消息，整包完成一次交回。UI只允许自建hidden IAB visible:false，不操作桌面／用户页／外部浏览器。root无独立全局工作则等待，不按文件数监工。

## 4. 缺陷与整改、取舍与快照

| ID | 缺口与证据 | owner／状态／关闭标准 |
|---|---|---|
| D01 | activeStart fallback0被错误retained：idle2fold→active未知0→已证仍0→同状态remount1。FE .archive/control-recheck-20261109/fold-probe.*。用户最新再次确认active时所有旧折叠消失，疑似Steer接续但不排除其它入口 | F1已有knownness候选，追加真实Controller→App普通Steer／Interrupt接续／自然followup／native ID先于checkpoint／Unknown交接反例；保已证结束历史与用户选择，不误折当前Turn，不靠remount |
| D02 | 实际App idle-only rejection仍确认4009保草稿，启动／维护／终态拒非Gateway输入 | B1/F1待修，一次显式请求原子受理与对应结果 |
| D03 | 4→6→5探针可能丢5，当前controller只拒旧seq未验证覆盖，需核真实scope | F1调查；真实缺口则诊断／统一恢复，不误判合法过滤，不以Socket有流量冒称数据连续 |
| D04 | accepted=false／本地phase拒绝诊断不足 | B1/F1沿新协议补最小枚举，复用脱敏桥，不记录正文 |
| D05 | 维护Stop后waiting输入去向 | 用户已后继明确确认“取消维护，继续处理已接收的消息”；原E01工程收敛现获追认。B1/F1实现和竞态验证中 |
| D06 | root亲读Controller.cancelCompaction发现refresh省略捕获的profile；ACK等待中切Profile后readCompaction默认借当前Profile；cancelNativeCompaction异常分支未按operation明确查询 | F1已接收；取消ACK丢／Profile切换／同runtime ID跨Profile实际入口反例，保原操作身份、不重放取消 |
| D07 | B1接口里程碑亲审：先入queue后写durable witness，ensure False／DB throw未清envelope，可能5071 accepted:false后仍执行；持久成功后的通知失败亦须区别受理结果 | B1整改；正式drain验证拒绝零副作用、已受理可查、同operation零重复；连同idle native晚期4009只能由真Gateway证明 |
| D08 | B1里程碑删除scheduler_host的Gateway来源筛选，而Gateway仍独立claim，可能使既有通道Reminder宿主／出站语义取决于扫描竞争 | B1核查并保原路由边界；历史source不作为Web输入拒绝依据，不等于可任意接管投递；必要方案须root先亲审 |
| D09 | 重启受理见证保留，但首版input_state只列RAM queue、operation_status不带原输入，需证明冷启可恢复文本／附件与显式再操作 | B1/F1接口整改；不能只显示中断却找不到输入，未知已执行不得冒称未执行 |
| D10 | Turn内auto compaction期间接收的文本不能仅留maintenance队列直到整Turn结束；第一个安全边界应为压缩发布后当前native Pending再次可用 | B1闭合阶段转换；正式auto compaction→下一API反例，不把Idle或假flag测试冒充；附件沿原下一Turn完整输入 |
| D11 | Stop等待compression commit fence期间可能跨Turn；仅RPC前比turn_id不足，锁外abort请求／线程／child传播亦可能命中新Turn | B1在原interrupt owner增可选身份fence，真实barrier＋新Turn接管验证；旧默认和hard_interrupt兼容语义保持，拒绝不得有清队列／cancel／信号副作用 |
| D12 | root亲审StopReceipts发现unknown仅按runtime/epoch/页面存，旧T1未知会吞掉用户对新T2显式Stop；旧启动target为空时可能一直只查询，旧query还可能覆盖新目标状态 | F1整改；按精确目标/动作世代隔离，允许新已证目标的新显式Stop，同目标未知不自动重放；实际Controller/App及交错查询反例 |
| D13 | U02现有审批/澄清恢复补查：3种内部source同epoch重连后q0选择丢为stages={}，Confirm disabled；当前retain直接requests=[]导致 | F1正式反例approval-recovery-counterexample.log；窄修ControllerPageRecovery/ServerRequests同owner同epoch草稿保留及needsCheck。须当前open_requests对账才允许确认；owner/epoch/认证/请求payload变化及已结束不复活 |
| D14 | CompactionViews与CompactionUpdates两个读取owner都publish完整phase；旧A终态/changed读取可能覆盖普通读取已证的新B活动状态；同op确认取消后旧unknown notice亦需清理 | F1统一当前operation/phase提交owner和cut，exact旧操作查询不得覆盖新；两个读交错的Controller反例，普通delta零RPC保持 |
| D15 | E01维护Stop保queue后，waiting消息只有展示、没有显式撤回，会使误发等待输入无法阻止 | B1/F1补现有Prompt operation撤回，沿原queue/Pending/witness，不取消维护、不影响其它输入；consume竞态、已消费too_late、未知ACK只读恢复 |
| D16 | 新controlled 5071明确accepted:false仍被前端一概视为5xxx未知事务，保草稿但阻塞后续输入 | B1保证false无执行残留，F1区分明确拒绝与真实未知；同code有/无受理事实两支实际入口验证，旧端仍保守 |
| D17 | controlled提交事件/input_changed只查询phase unknown；RPC ACK迟迟不settle时，已收到精确受理见证仍submitting挡后续输入 | F1按同owner/op事件或input_state见证立即只读query并退役已接收事务；ACK一直pending仍可第二次输入，迟到ACK不改新草稿/重复执行 |
| D18 | root亲审等待queue drain摘head后、generation复核前的Stop窗口：旧恢复分支可能把已Stop输入重新放回queue，再被poller执行 | B1优先真实barrier反例；明确Main Stop不得复活已claim输入，保其它原生generation变化恢复语义；红→绿与receipt／零后继Provider证据待交 |
| D19 | B1真实网络harness准备发现候选重复获取history锁；测试live fixture为RLock，正式_init_session为Lock，掩盖idle claim／active通知／Stop cleanup死锁。root已亲读确认idle嵌套锁接缝 | B1发布阻断整改：保正式Lock，沿原owner拆已持锁段、通知移锁外、cleanup只持一次；受影响旧RLock证据不能证明正式链路，必须正式构造＋有界RPC反例重验。未上线，不能归因用户线上现场 |
| D20 | 线上同源原生流＋真实Steer并发：_native_write已stamp/replay后，Fanout锁外serialize被超越；健康Peer收到5,6,8,7,9(source7)，replay仍有序完整，无断线也破坏live事件合同 | root亲审接收原报告／反例，stream_control_diagnosis续派正式排序修复，F1承接真实乱序trace核客户端影响；旧健康传输测试没有覆盖stamp→enqueue窗口，必须红→绿及真实WS/多端/慢端回归 |
| D21 | root实际隐藏IAB New Chat Enter，controlled prompt.submit携client_submission_id被正式schema拒收，原mock未拦非法字段 | root已窄修prompt-submit新分支剔除旧字段，原operation_id/legacy submit_idle保持；真实IAB已Send/Steer/Interrupt/Stop走通，F1补正式契约回归与指纹 |
| D22 | 同次真实IAB，Stop后后端running=false/native_active_turn=null/phase=idle，网页Receiving response及侧栏Running消失，但主按钮仍Stop | F1接续已取得无input_changed终态的红→绿，补实际IAB同页复验与状态owner审查；不能只改按钮标签 |
| D23 | 20:42用户真实输入已durable受理，约127ms后WS1005关闭；20:44重连，截图仍unknown且离线点取消再报错；原生submission_status可证明accepted | F1接续核legacy/controlled原ID自动查询、离线cancel/check、同／新runtime重连事务与对应通知退休；不重发、不假撤销，关闭诱因仍未知 |
| D24 | root亲审R5 inspectSubmission：refreshHistory前检查owner，但await后到草稿迁移／select未再检查；慢读期间用户切owner可能被旧检查导航回来 | F1定向实际Controller反例；若复现按原owner／generation覆盖异步边界，保原事务后台受理查询，不借屏蔽所有错误或禁止切页规避 |
| D25 | root真实隐藏IAB受控last-delta时Enter Steer，待消费custody witness被正式history提前画成普通You，同时Pending显示同输入两份，当前Assistant被挪到该早写row之后；terminal/followup后早写行才消失 | stream_order_resume改BE正式display可见谓词及session_history内存投影同owner；SQL计数/分页/coverage/turn_start一致排除明确Web queued custody，保durable receipt/原始active/原生队列和legacy语义。先正式read/recovery红→绿再联合实UI |
| D26 | F1真实联合Gateway/Controller＋TimelineMessages：同epoch重连后Idle维护→两同文waiting→按op撤回其一→Stop维护保另一→新Turn流式，三次DOM提交历史folds=[]、终态恢复；当时连接ready且身份/控制正确 | F1/BE已共同定位completedMark恰为已withdraw的第一条waiting custody UID；owner/runtime/epoch未变，删除该错误前沿后retained/completed均失效。先修D25正式投影并重跑原真实链，暂不新增FE下游补丁；若仍失效再修通用owner。严格逐DOM提交断言保红证据 |
| D27 | root实际隐藏IAB Stop后Thinking从正文前移动到后；原始row7 turn_terminal保reasoning residual，row8同Assistant UID仅正文。F1已核terminal-history把所有residual锚到suffix尾，且先retire已见live | F1按真实source/native UID、typed facet及已见顺序修既有terminal-history／projection；保正文/工具残留与冷恢复缺证明的诚实fallback，不按文本或时间猜顺序，补真实链反例及跨Turn回归 |
| D28 | close_origin_audit在原Gateway＋正式Controller注册链复现：同步state观察者异常穿透endConnection，连接已退役而retry未安装；ready后置heartbeat/Promise也受观察者影响。无20:42自然throw记录，不称现场关闭原因 | close_origin_audit实现唯一连接owner先提交ready/退休/重试，再隔离通知；F1接明确delivery failure到既有恢复。健康Socket不因渲染失败关闭，任何意外关闭统一恢复；4100固定对端原因仅诊断不决定重连。界面/原生测试及陌生关闭原因、回调重入、旧owner、自然WS恢复交叉验证 |
| D29 | 过期viewport读取遗留无owner replaying，终态连续帧已到却被held；另查到consumed Pending半提交、Secretary首次读取通知遗漏 | root结构方案经Verification第6节接受。F1五产品接缝修正，最终15文件510绿/1原可选wire未启；E1–E4完整绿。root真实IAB八Turn原路径及HB/Reminder/Steer/Stop通过，同connection1/recovery2、cursor189、八唯一Assistant/无held或Receiving、reading anchor与manual choice保持（root-final-ui/fixed-ui-verification.json）。完整旧App52红已分类，18文件583通过；其中D30 Scheduler期待后被fresh复查确认为旧规格回退，单列D33修正，不抵销D29有效证据。 |
| D30 | 52项旧App逐项分类；root曾按10/26旧Scheduler条款调整App四处 | 历史583绿和Orb零预取证据保留；fresh复查确认该期待违反11/8用户确认，转D33整改，不能作为当前合规证据。 |
| D31 | lease首通知早于exact owner metadata约28ms，身份成功公布后缺后继hint，source未写期间页面停合法unavailable | root已亲审接收锁外/真变化后原history hint；39正式测试＋真实App/WS/native8Turn→两Gateway强制窗口绿，source/row不变下约2.3秒自动gateway/samecut uncommitted，同Socket/round/runtime与fold保持、后续Web Send/Stop通过。原红保留、无FE修改。完整证据d31-research/implementation-report.md；待fresh全轮Verification/Validation，不把分区绿冒整轮通过。 |
| D32 | 活动Main+附件的controlledAction返回Steer，公开Controller.steer绕过原附件资格，Enter可能上传提交未准备附件；违反06§1.8及本轮保留附件限制 | 已实施并root亲审，FE71340be；30正式App附件用例、真实App/native四组合及两上传竞态、root IAB两个组合均通过，3源指纹一致；无Main维护/E01保持。等待fresh独立复审关闭，见FE d32-d33/report.md。 |
| D33 | D30 root按10/26旧合同回退11/8明确Orb立即异步预取及二级先准备几何后展开要求 | 已实施并root亲审，FE71340be；恢复Orb预取、一级准备/失败Retry、目标就绪再动画，正式App含running/慢/失败/owner/降动效通过，root IAB预取及43帧正常双向过渡通过。root旧依据错误及原证据保留；等待fresh独立复审关闭。 |
| D34 | 正式/resume或/sessions跨Profile列表选B row后仅select(id)，默认仍A；唯一ID错误404，同ID可显示错误Conversation | root提案复用现有openConversation(match)统一侧栏选择owner，独立v3按U07/W19接受；F1窄修及真实Controller/REST/activate B归属、同ID/草稿隔离/零创建发送中断等反例。保持命令匹配规则，不新设Profile门禁。完整App又暴露原A canonical draft maps过早退休，须保活到命令有效结算，并挡acceptedEdit已退休boundary的迟到回写；root提案和v3评审见verification§6。原profile红及38绿4草稿红均保留。现FE75e989a五文件已root亲审，8完整205绿/无skip，原source不写重放、B绑定/草稿、A剩余附件及模型选择、精确boundary/最后清退均有正式App证据；固定71340be报告仍违规，当前等待fresh全轮复审。 |
| D35 | /notebook等待中真实Rewind受理退休旧boundary，用户输入新草稿后旧结果外层consume()无资格参数，实际截掉新/notebook前缀 | frontend_finish将消费boundary设必填，所有异步成功路径统一精确资格；保正常跨owner原草稿结算/失败保留。V4实际App反例原红、其它消费路径及真实退休/正常回归须关闭；当前未修，技术阻断。 |
| D36 | /model及/reasoning原A config.set ACK迟到，切other后ensureBinding仅传原stored ID，实际resume/activate other的同ID错误范围 | frontend_finish按原Profile/stored/runtime/key/epoch/recovery/活boundary约束回执补读，显式原Profile；不回滚已成功设置或重发。两原App反例、ABA/epoch/正常成功/失败隔离验证后root亲审；当前未修，技术阻断。 |

V4当前复核关闭D29/D31/D32/D33/D34；上表的阶段“待复审”属于当时交回记录，当前未关闭产品项为D35/D36。报告106条98符合/4违规/4后继缺证，不以已绑定APK字节代合格产品。

D35/D36后继工程收敛：原三红扩至六红（title迟到展示、AI-title退休后仍写、已开始activate后ABA覆盖model）；统一boundary守消费／展示／后继写。设置ACK有效后沿既有configuration-changed，不裸ensureBinding；后继局部方案又证deferred model无session.info时Model仍旧，原红单独保留不回填75e。root扩白名单到controller-page-recovery的start/bound，配置成功失效既有bindingReads，由compaction reader共享一次metadata/activate与Context权威确认，Promise身份与原context相交防旧读提交；不新增resource／owner或history读取，普通reasoning同一次确认。V4两轮方案评审与条件见verification§6，FE仍须实际App正常成功、菜单关闭、deferred idle/running、新setting／ABA／epoch／失败Retry及原完整路径证据，不能只spy恢复调用。无阈值／产品语义变化。

D36菜单后继：实际Reasoning点击证setter后再裸ensureBinding，迟到切B仍读A、同owner ABA旧Toast；Model菜单也重复。root批准ChatSelectors两个菜单移除独立绑定并守旧close/error/busy/确认收尾；Controller.setSessionConfig及原reasoningPick沿同一对象/纯owner资格，保两种event/ACK次序正常一次反馈、较新选择和失败隔离。可在既有profiles.ts共享纯helper，不新增全局状态/计数/队列；原4001合法原A runtime后继须可继续，不能靠初始runtime硬相等一概拒绝。V4方向评审见§6；原menu-owner/menu-ABA及deferred方案红均保留，后继完整验证未完成。相关manual compaction/incremental fixture22红已合法收口两文件144绿，不替代最终整包。

D36联调契约：14文件630绿后补原生真实Context.model得两持续Retry红，分版本保留。root选择原生快照提供3optional事实model_switch_pending/context_model/context_provider，覆盖冷开/重连/连续pending，避免仅记ACK旧值的局部补丁。backend_control白名单session_usage统一纯投影、server两info facade、methods_session._resume_live_unpersisted/_cwd_info、model_switch._lazy_info_route、contracts/common、对应正式tests及官方生成的apps/shared两合同文件；不改原模型写/应用/数据库/依赖。frontend_finish在已准配置/Context接缝接入，额外仅controller-event-effects.sessionInfoRecoveryReason纳入3字段真实变化；不变/省略不假变更。已证pending源对应但目标不兼容或身份未知保退休/unknown并成功读；完整身份匹配才恢复数值，真实源矛盾继续错；原630与新红不互相覆盖。V4讨论见§6，两个包仍待root亲审、新完整审查和Validation。

D37：V5按06 §0.7第6条从正式App复现/model、/reasoning遇4001仅1写/0恢复，两原红保持。root方案与V5评审为共享Controller.setSessionConfig/writeOwnedSessionConfig和命令boundary，合法fresh回调仅原操作继承；第二次失败真实可见/保稿，confirm_required保稿/原native提示，不假已应用；unknown/非4001不重放。reasoning原显示词与effort别名按原优先级仅规范本地echo，raw写不变。

D37实施又证fresh已安装、第二ACK未返时真实beginEdit/输入触发旧bound缓存，activate旧runtime4001，UI卡在Rewind确认前；根与V5认可集中binding安装点失效旧bound/selection/在途结果，既有当前可见有限对账、legacy不重复承担，初次/同runtime不自退、后台A不扰B。原runtime-cache-red稳定WIP源两红2.42s；后继需真正走完accepted Rewind再放旧ACK，不把前置卡住称为后置已验。fresh谱系/epoch合法失败边界不人为复活。root原生隐藏IAB的pending模型＋强制4107＋同doc恢复/草稿/Steer接续证据在root-d35-d36-ui，绑定0d6，不能关闭D37。

**后继事实（用户追问关闭与抽象提示）：** 用户明确20:42同页面发送后没有关闭页面操作。closed不是server主动关闭的同义；该1005来自原ASGI WebSocketDisconnect而非日志默认值，RFC定义需与实际服务栈确认；close_origin_audit只读调查主动关闭入口/重连调度/观察者异常隔离，不改F1产品。20:44有重新接入不等于同页自动恢复成功。unknown提示由项目Web初始27c5cb4已有，原身份受理查询ad7e484/9fabcdd于10/21加入，非Hermes原生错误，非本轮新增。用户批评抽象红错与失去控制，F1将沿已授权自动查询语义改为明确待确认状态，确认后自动退休；不新增盲重放或常驻门禁。

U13实现期诊断辅助`stream_control_diagnosis`已委派（gpt-6.1-sol/high、fork none、无派生），仅线上同源main12e工作区ignored探针；只读正式后端，调查OutputIdentity/消息持久与终态、连续内部Turn/recovery证明。不是独立Verification门禁，不改产品／根文档／生产，整包交回root。B1与F1仍为唯一对应实现owner。

该诊断已整包交回并由root亲审：4个实际native stream/SQLite/正式Session普通Lock探针；D20为明确缺陷，last chunk/finish/EOF/SQLite提交窗口5次完整恢复、普通Steer→真实到期HB链6次完整恢复为有限负结果。公共通知双start已观察、真实到期HB只一次；旧tail重叠样本没有破坏新native owner，不将它们直接定因。原件在main工作区ignored `.hermes-dev/stream-control-diagnosis-20261109/`。

root续派`stream_control_diagnosis`为D20实现owner（不是独立门禁）：集成worktree白名单`output_identity.py`、`transport.py`、`event_replay.py`及对应tests；追加`ws.py`仅WSTransport.write附近内部write_ordered接缝，和B1 ready字段有效隔离，不碰其它控制文件。沿已有Fanout/stdio输出锁、WS token锁统一prepare(编号/replay/inflight)＋serialize＋队列/任务准入；网络等待留锁外、announce/hosted hook留锁外，旧Transport兼容、不加无界queue/全局等待锁。新证据在ignored `.hermes-dev/stream-order-fix-20261109/`。不得改UID/epoch/coverage或靠FE丢帧掩盖；根亲审后与B1/F1整合。
| E01 | 15:05:43未知1006缺client_connection_id；旧13:41刷新前停顿无现场时序 | 历史证据边界，不强归网络／代码；后续依双端日志归因 |
| E02 | adb devices为空 | 不把包校验/IAB冒充真机，交付如实标安装／自然网络／实导限制 |

root复核证据：BE ignored .hermes-dev/control-recheck-20261109/，FE .archive/control-recheck-20261109/。旧有效证据：BE connection-reliability-20261109/final-review.md、steer-busy-20261109/review.md及FE对应.archive。设计参考BE .hermes-dev/internal-turn-control-20261109/design.md仅作源码线索，不替代冻结要求。V4原件在原算法工作区.hermes-dev/adaptive-v4-20261109/{final-report,review}.md与verification-index.json，27模块已核b232一致。

no-tmp旧历史报告、旧Timeline测试及Android TV lint缺口保持原时点，不关闭门禁；新代码影响证据时定向补证。官方PM .venv，Python只用HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh。最终大型检查由root在集成收敛并派独立门禁后统一一次，日常只相关分区／正式机制／竞态。

root基线反证：main12e2b45、相关6个test／实现blob与2e91189一致，官方runner仅执行hidden_row_receipt与gateway_enabled_branch两项，均失败（各1.31／1.02秒）；证据`baseline-two-failures-12e2b45.log`。允许B1窄修fake签名透传accept_metadata，并将“禁止查找adapter”改为证明“零实际handle_message／模型派发／claim”，保原durable内容、display_kind、fire_count与Profile断言；不改产品迁就fake，不隐藏原失败。生成完整性中的review.summary为旧基线项，本轮compaction_delta须真实literal emitter通过，不能造假的emit或改扫描规则。

B1白名单工程补充：root亲读后允许`agent/auxiliary_chat_stream.py`在现有compression capture作用域通知实际Chat摘要增量，observer在累积锁外且不影响原模型流／超时／进度语义；无capture保持原生。`tui_gateway/ws.py`、`entry.py`仅增可选能力声明。此为既有维护流式要求的必要接线，不扩大产品范围。Responses已有observer不得重复发布。

F1白名单工程补充：`src/App.tsx`和`src/core/command-actions.ts`的实际Chat／Composer／Timeline控制接线；不改无关布局。仅Controller修改不能覆盖真实Enter／主按钮，必须一并接入。维护可Send和可Stop独立，不能因存在草稿就消失取消入口。FE无README为既有事实，不新建平行文档。

完整控制权包含既有工具审批／用户确认响应：root要求补核内部Turn→晚进入／重连→合法响应和旧owner拒绝；允许F1在现有ServerRequests恢复owner接缝修已复现D13，不新增审批语义／权限。B1对应核同一Agent/Fanout/原生open_requests及正式响应，已有同版证据可复用。

Stop接口收口：旧`session.interrupt`默认保持；新Web可选`input_policy=web_controlled`，`operation_id`指维护目标、`turn_id`指Main目标，均不是本次Stop动作的幂等id。服务端在原owner边界按真实Main／维护状态判断，目标变化不停止后来的run；ACK未知只查原目标，不能以自然结束反推Stop成功。允许B1在`agent/interrupt_control.py`及原`turn_context.py`身份绑定点追加可选target fence，沿既有锁，禁止引入新gate／锁体系或在history/pending锁中等待commit。

上述“不重放”约束指故障恢复不能自动重发旧动作；新的用户显式Stop仍必须有真实停止能力，不能被旧unknown记录永久改成仅查询。当前目标fence与动作世代保护新的动作，旧ACK/query不得清除或覆盖它。自动恢复只读原目标，不把自然终态冒称Stop成功。

发布准备仅本地ignored目录`.hermes-dev/web-control-reliability-20261109/release/`：沿旧已审remote_release/retention原字节，独立stage-20261109-web-control-014；expected_old=9270933、新包0.1.14/1014，尚未运行prepare／上传／发布。发布时按实际manifest核资源集合，不以旧439数量代替内容验真；保新批次和013、核验后清退012旧数据库集合。

快照：12e2b45冻结；2e91189纳入V4、核心文档保护与27模块指纹核；25baafb计划、63bd98f编排更新。新控制首版实施中，尚未整包亲审或独立验收。生产模型／排期／数据／凭据不作测试；原算法dirty与Huawei目录保持。

D37工程接收（79ccd）：正式配置写共用原setter/helper；bindingInstalled统一旧bound/selection/在途资格交接、保自身合法source读取，有限cut后新runtime对账；reasoning仅本地echo规范化，raw RPC不变。root核真实accepted Rewind后的迟到ACK草稿与通知不变、旧读取退休、同runtime/初次/后台不自退及合法4001一次/第二失败/确认/unknown边界。14完整文件684通过、最终App149/类型/health有效，原两slash红及两cache红保留。该项等待V6独立关闭。

D38（V6新技术阻断）：06 C1/C2/U13原生合法通知夹在legacy/typed帧之间，single-slot配对被清除，第二reasoning chunk回滚/追加造成两个同ID Thinking。root与V6研讨见verification §5/6；front end按既有投影owner内精确贡献认领机制修复，不能status特判、后端禁交错、文本去重、增加REST等待/连接关闭。关闭需真实两chunk原红、child relay实际序列→正式Controller/App、多legacy迟到typed/重复/边界/epoch/Turn、终态归并及旧fold/阅读锚点；范围内仍未关闭。

D38正式接线补充：root亲读后准许reduceEvent新增可选内部epoch，Controller.reduceProjection传gateway.epoch，PageRecovery.installCut传已核等于当前epoch且context.current的snapshot.epoch；仅两个表达式，不增连接owner/协议。root真实隐藏IAB固定79ccd复现session.usage seq14插在legacy13/typed15之间，下一chunk令assistant-ui MessageRepository抛同ID异常、整页白屏；timeOrigin1794266267104.7不变/0WS close。原件ignored root-d38-ui/red-verification.json、red-console.json、red-page.jpg；本地受控Provider，全部gate已释放、tab9已关闭。此是D38影响补证，不代独立Validation。

D38诊断补齐：root发现React异步commit异常仅在console，原APK桥接未收录；V6按原U08/C5/C6接受固定render_failure/uncaught记录。apk_finish白名单main.tsx、api/connection-diagnostics.ts、api/client.ts仅当前attempt诊断接线、一个可选专责sibling/对应tests及Android DiagnosticSchema两文件；与D38投影修复不交叉。不保存异常正文/stack/componentStack/凭据；无当前attempt不得借退休diagnosticOwner；保React原报告恰好一次、桥接失败不改业务，不新增ErrorBoundary/reload/Socket动作。真实React异步异常/敏感排除/当前与退休切换/桥接失败/native严格schema需验证，现仅实施中；最终两包root统一亲审再commit/build，原V6固定FAIL不变。
