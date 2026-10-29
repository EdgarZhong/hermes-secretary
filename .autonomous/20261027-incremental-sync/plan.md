# 实施计划：20261027-incremental-sync

## 第二次迭代（2026-10-28，用户已授权纳入U20）

**当前阻塞补修（2026-10-29）：** Noting开始／提交／结束复用全局history wake，导致空owner sessions.changed误触发当前Chat／Usage恢复；Socket仍连接时，暂不可用响应可误撤销原操作资格。root指定独立Secretary跨进程wake、可信Noting child独立history wake，保留Main／未知原history失效；native sessions.changed只增可选完整变更会话scope，能证明当前物理会话未变才不启动其恢复，未知／真实历史改写保持原恢复。原生事件与API默认兼容，不以隐藏提示或强ready代替修复。C-R5/C-R6已亲审接收，62项及冻结检查复用。

**U22自主目标及轮次上限：** 已按用户明确要求创建自主目标，持续推进。第一轮后Verification、Validation各最多再两次正式全轮复审／复验，对应第二、第三轮；所有包的反例、开发测试、主会话review和集成先闭合再统一送审，不按包开启门禁。用户U24已将Verification改回本地；先前云端安排仅为历史。第三轮为最终允许轮次，上限不作为带缺陷通过或放宽阈值的理由；仍有缺口则明确未完成，不开启第四轮。

**U23最终发布完成条件：** 用户最新明确授权最终正式上线及0.1.9 APK打包交付，覆盖本计划及旧报告中的“未授权部署”历史限制。最终候选通过后合入两仓main、按既有cloud-deployment-sop/operations-log发布Alex（ssh alex），云端保持main，核实际后端版本及前端资源/健康/配置与三库保护；准备可用回滚点并最多保留两套有效三库历史备份。APK按现有签名与架构构建0.1.9，核versionName/versionCode递增、签名/ZIP/资源SHA/包哈希并按既有交付入口交付。无真机时如实记机制/包核验边界，不假称实机通过。生产模型调用及真实微信测试外发仍未获授权。

**U24最新门禁调整：** 用户明确Verification改回本地，覆盖此前停本地／交云端的当前执行安排。待本轮全部集成及两仓SHA固定后，派全新fork-none 6.1 sol/high独立Verifier，先从指定版本规格建立全范围判据，再调查代码及历史云端发现；不是逐包审查。第二轮Validation计划已建立，按集成／门禁就绪继续；不消耗第三轮去重复未集成片段。旧报告与停Verifier历史保留原时点，最终完成条件和三轮上限不变。

原轮未交付，继续同一索引／计划与两仓同名分支。整改输入原文保存在`reports/cloud-remediation-plan-20261028.md`，原待审BE44eb0be4c3／FE91ad72f；8项根因、3类证据事项保留原编号，报告所述27条违规／43条静态符合／4条证据不足不直接变成当前版本结论。原始Verification已由用户补入Downloads，逐字复制`reports/cloud-verification-20261027.md`并核SHA3546c0e1138804f25a4e24fcc8ca5d9f3dd1486399445b9300135a0f2b5b24bf；§6内嵌反例原样保留，额外附件未冒称已取得。

U20最新用户业务契约优先：云端计划C包及旧IDLE判据中“先Noting再压缩、任务等待FM结算”的旧时序被替换。保留F07真实Gateway维护资源保护和E02开关／跨due证据目标，改按并发独立提交、联合取消、Note独立推送选择与任务及时终态验收。冻结质量检查、原前端D/S/P、主按钮权限与全部未冲突条款保持。

| 包／根因 | 主会话指定机制与正式路径 | 唯一修改范围／依赖 | 必要证据／用户旅程 |
|---|---|---|---|
| A-FE：F01/F02 | loadEarlier并入现有owner、恢复代次、认证撤销及连接资格；完成前后均核资格。仅确证anchor_not_found退役selector／复用证明，建立合法必要窗口；不吞网络／owner错误 | controller-page-recovery/page-recovery及认证接线；先由root收敛现有Steer／Slash接线，缓存文件归B | A01–A03及Z01/Z05：迟到成功／失败不复活旧历史，RPC失效锚点同document有限收敛 |
| A-BE：F05/F06 | D0/S/D1保持旧身份／内容／revision，允许同source最新Thinking有合法尾追加；旧行变更／删除／换源仍拒绝。正式writer实际CAS改文提交后通知，no-op／回滚不通知 | tui_gateway/recovery_view、hermes_state_messages及必要change_watcher；不改U20生命周期或D finalizer | A04–A06：RESTcursor→sync v1 activate，正式SQLite writer→watcher；最终由Z接实际App |
| B-CACHE：F03/F04 | 同UID／物理代表／详情revision的Thinking子集更新保留已取完整字段。统一窗口／详情／已核验前缀的最近500身份预算，淘汰最旧，损坏配对的selector证明退役，绝不改造服务端receipt | history-coverage/history-sync/display-cache及必要详情前缀sibling；禁止改大Controller，窄接口root接入 | B01–B04：窗口外完整详情→Thinking更新→真实IDB冷读；500+1新前缀／同UID落库不双计 |
| C-U20：F07/E02及U20 | 主会话先设计完整接线；普通三入口同时触发／联合取消；已提交保留；替代审计不可消费；Force仅Turn结束、不可取消及封区间；四时点检查有效来源快照，经原FM推送。Gateway维护保护覆盖普通回收，及时释放终态 | secretary/noting及框架／自有状态表、native compaction接缝、Gateway cache；与D共享run_turn_runner仅由root协调；不加通用scheduler/mailbox | C01–C04按新时序重写；U20全部成功顺序／取消／替代／Force／重启／注入去重；真实DB与正式native loop，外部模型结果受控 |
| D-WX：F08 | 普通final完成输出变换和原生消息身份后，进入既有完整消息callback/FIFO；不能等micro-compaction/finalizer结束；尾部按UID及成功事实去重 | agent/turn_final_response、必要turn_finalizer、gateway/run_turn_runner及专属tests；不改Gateway cache或U20触发owner | D01–D03：正式Loop屏障阻塞收尾时已交adapter；不同UID同文不漏、同UID不重、失败不伪成功 |
| Z：E01/E03、U18/U19及全轮 | root亲审所有接线；先核D07规格对象对应客户端；原版本证据分层复用；同200长正文夹具核请求依赖／全轮传输／动态就绪。保全部既有异常闪现修复 | root独占大型集成夹具、索引／计划与云端版本prompt；U18/U19/Slash现有未提交diff先关闭 | Z01–Z07及27条违规映射；真机／外发缺口如实保留；不只凭终态截图称零闪 |

并行按4个总槽位安排：第一组B-CACHE、A-BE、D-WX可独立，root收敛前端旧diff并设计C-U20；下一组A-FE、C-U20按实际空槽及文件依赖推进，不要求报告建议五路同时运行。具体方案由root先冻结；子Agent仅6.1 sol/high实施，不派生、不流水账，只整包完成或真阻塞交回。

全范围复审仍由用户云端执行，本地Verifier保持停止；最终送审固定新的完整BE/FE SHA，带可访问且脱敏的原始证据附件。Validation复用不受影响证据，改动范围在新候选复验，独立报告未完成不冒称通过。不因新增U20抹去F01–F08/E01–E03，或把旧IDLE时序直接照抄回产品。

### C-U20正式接线设计（主会话2026-10-28指定，实施前依据）

1. **身份与正式事实。** 保留Profile／Conversation／原生成功压缩边界／不透明operation_id／admission／child／snapshot独立身份。取消关联绑定具体native compression fence的正式operation_id，禁止按同Conversation所有任务泛取消，禁止解析holder字符串。复用现有Secretary自有admission/children/presence和compaction_state；必要持久字段仅加自有表，开发隔离库重建，不做生产迁移，不创建通用调度器或新Loop。普通同Anchor取消后可重新准入，历史审计保留，不能原UNIQUE使取消永久占位；Force本区间占用仍保留到真实成功压缩。
2. **普通三入口。** 原生压缩通过自身安全／lease边界后，在现有pre-summary接缝冻结准确完整父前缀并准入Noting；Idle删除after_normal_commit的等待，改用同一原生request路径并行，不造第二压缩执行器。native fence取消／失败收尾关联该未提交普通Noting；同一正式cancel/commit竞争用Secretary任务提交资格的一次事务确定，已提交不撤销。安全锁不跨模型/网络。未启用／非eligible／External保既有原生分支。
3. **替代。** 新普通任务或Force准入时，先原子撤销旧未提交非Force任务的有效提交资格；工具工作锁冻结已有完整工作态，以`superseded`专属结束审计保存，不调用finish_noting模型工具、不新增模型请求、不提升pointer、不作为新task基础。然后从上一完整有效快照冻结新工作视图。旧API/工具晚返回不得继续改视图或恢复有效提交；native interrupt用于停止旧执行，不持任务锁等待网络。特殊审计结果在pointer选择、Main show、Noting初始化、branch继承、注入及debug recovery等模型消费路径统一排除；人类审计保留。普通Compact取消则丢未提交稿，与替代审计区分，不把其伪装成可消费forced/context_overflow结果。
4. **Force。** 移除turn_preflight两处Force发起，以及Idle中把超线改派Force的旁路；只保真正Main Turn结束的统一hook。读取原生已解决窗口／阈值及包含Turn尾的占用，不新增估算器或改公式。短时确认当前真实owner／本次Turn已结束、冻结前缀、持久准入与带稳定身份的原生FM提示同边界落实；线程启动失败有明确失败状态且提示不冒称仍执行，重复hook不多发。不修改通用FM投递机制；Force不得被Compact取消或替代，直到成功压缩才解除该区间后续Noting禁用；真实失败／进程死亡明确终态，不伪装用户取消或永远running。
5. **快照提交与注入拆开。** 正常任务以自己的有效提交资格和合法来源／完整工作视图提交，不等待父runtime空闲、压缩完成、通知或句柄存活。child完成立即写终态并释放资源，不再用NotingTaskLifecycle.carrier留运行owner等待FM。提交后只唤醒统一Note资格检查。快照选择复用Full Foreground合法anchor位置与真实成功边界，跳superseded审计；不能取全库最大created_at或只看全局current pointer。当前区间自己的Note不得注入本区间。选中最近来源的对应任务尚未结束时，等待该最新来源结果或其明确失败终态，不为旧无效任务等待；更老任务已在替代路径失效，无须等所有历史任务。
6. **四处统一检查。** Noting提交、native压缩成功发布、父runtime恢复／合法attach、下一模型请求前调用同一幂等selector；新建snapshot或成功边界只有提交后唤醒。通过既有publish_framework_message推送，通用busy等待和Turn间隙接入保持，不新增mailbox或turn内注入。原append_runtime_row仅接受global current snapshot的guard须改为Note专属、同事务重新选中验证，避免较新区间快照遮住应注入的上区间结果。实际FM row与对应目标边界／snapshot回执同事务，重复检查／排队／重启不重发；append失败未算成功，旧runtime/旧目标边界不得乱写，跨更后继区间按当前合法路径重新选取。必要回执只在Secretary自有状态中保存，不另建通用消息队列。
7. **F07/E02维护保护。** 当前仍需父原始前缀／原生压缩资源的准确维护依赖接入Gateway TTL/LRU/pressure选择和实际soft release；检查与释放在既有owner锁下有确定先后，无先检查后清空漏洞。终态不被FM等待拖延；必要FM责任由既有父owner机制处理，不靠保持已结束child。explicit close/替换使旧回调失效，失效任务及时收尾；开关跨due终结与暂不可用owner保due的原有区别保持。
8. **开发期反例矩阵。** 真实SQLite/native Loop验证Noting先／Compact先、commit与cancel双屏障、取消后同Anchor重试、旧工作态特殊结束且新任务从完整快照开始、迟到工具/模型回调零有效提交、Force仅Turn结束／重复hook一次提示／取消Compact不杀Force／成功边界解封、不同Profile/owner、注入反序／两次压缩／排队后被替代／append失败重试／重启任务终态。F07使用真正Gateway cache三种普通回收，E02用实际开关及跨due，不用DB伪父前缀或AST孤立helper代替正式路径。

## 2026-10-28 · 恢复原自主轮与追加口径

原目标不变：500条消息及同条详情缓存、游标增量、SPA与APK免刷新恢复、D/S/P表现状态不回归，独立缺陷及最终动态验收闭合。原轮尚未交付，不另建替代看板或宣布验收完成。本地Verification继续依用户要求停止，云端静态审查prompt须更新到后继实际版本。

U20完整确认节已从原工作区07同步到本实施分支，保留本分支已有规格事实；尚未改U20产品代码。主会话先补正式接线／事务方案，再按明确白名单交6.1 sol实施，亲自集成。不能把规则重新开放为产品讨论，也不借此改变原前端缓存／状态契约。

优先序：完成现有前端Steer／Approval／Slash修补及定向验证；推进U20后端接线设计与实施；集成后复验受影响的压缩、Notebook、恢复用户路径并更新云端审查版本。已有同版本有效证据复用，无关大套不重跑。最终发布已获U23授权，生产模型调用或真实微信外发仍未授权。

U20验收必须覆盖普通手动／Idle／原生自动压缩并发触发与联合取消、已完整提交结果保留、旧在飞任务特殊finish审计且所有模型消费跳过、新任务继承完整快照、Force仅Turn结束触发且不可取消／封区间、成功压缩解封、Full Foreground有效快照独立注入与去重、重启不悬空；FM保持现有推送及Turn间隙接入机制。

## 目标与依据

依据snapshot-index.md、基线baseline.txt（冻结时填写）、06顶部C0–C3及D01–D18／S01–S18／P01–P10。已冻结cf5742c（前端c39086c），进入实施；baseline.txt记录精确版本。先main独立修复，再同名codex/incremental-sync-20261027前后端分支。核心优先：实际页面当前窗口增量→完整详情复用→同页实时恢复→请求并行／按需→APK不重载。完成要求是正式链路、针对性证据、独立Verification与Validation全部适用判据闭合，不以单测数量替代。

## 覆盖与任务表

| 包 | 条款／正式路径 | 负责人／白名单 | 依赖／验证／完成条件 |
|---|---|---|---|
| M0独立main修复 | U10、U11；真实取消、Notebook状态、IME绘制、微信命令及Assistant回调到发送 | 主会话及既有两实现Agent；仅已交付白名单 | 反例、真实入口行为、亲审；修复阶段豁免双门禁，最终仍回归 |
| B1后端增量 | U05–U08；REST messages与session.activate recovery_view→既有DB可见窗口投影→有界差异 | 后端实现Agent：hermes_state_recovery_view.py、hermes_state_history_sync.py新sibling、hermes_cli/web_routers/sessions.py、hermes_cli/web_history_cards.py、tui_gateway/recovery_view.py及对应tests | 不改schema／生成协议／原生事件层；真实SQLite覆盖无变化、追加、同UID换行／原位改写、rewind、压缩、删除、外部写、owner、过期；正式REST/RPC默认兼容 |
| F1前端缓存及接线 | D01–D18、S01–S18、P01–P09；正式Controller／PageRecovery→REST/RPC→IDB→React展示 | 前端实现Agent：src/api/client.ts、types.ts；src/core缓存／history-coverage／history-details／controller-page-recovery／page-recovery／usage-view及必要sibling与tests；Controller.ts只必要接线且不增长超标指标 | B1冻结wire契约；真IDB、当前Controller回归、受控网络事件；不得改视觉、按钮资格、已有折叠／阅读规则；所有当前页面读仍同页恢复 |
| A1原生免reload | S17、P10；MainActivity生命周期→ForegroundRefresh→原JS恢复／回执 | Android实现Agent：ForegroundRefresh.kt、必要MainActivity接线、相关原生tests；不改前端src | 5秒／30秒以上活跃恢复、离线重试、迟到回执／旧document、通知导航、附件返回，无自动reload；保原UI |
| I1集成审查与证据 | 全范围；正式前后端wire、实际App、长正文传输量 | 主会话，报告／微小接线修补 | 不复跑有效整套；集成变化定向测，200条长消息记录全量、无变化、少量追加字节与请求数；隐藏IAB真实App模拟网络，原生真实平台单测 |
| V1独立Verification | 全轮冻结要求→实现／接线／证据 | 全新sol/high fork none，只读代码，verification.md与证据 | 集成收敛后派遣，先原文建判据再看实现，复用同版本证据 |
| V2独立Validation | 全轮适用用户旅程 | 另一个全新sol/high fork none，validation.md与证据 | V1通过后真实入口；仅隐藏IAB；缺设备如实处理；主会话最终delivery审查 |

### 主会话冻结的工程接口

1. 复用现有recovery_view版本1及Desktop的epoch／seq／events.since。REST新增可选history_sync=1、sync_cursor；仅在recovery_view=1或既有detail_row_ids请求生效。旧调用所有默认投影／错误／语义保持；新增字段不写生成协议，RPC现有dict可容纳。
2. RPC request.recovery_view新增可选sync_version=1；每个window可带cursor。旧receipt仍必须提供并核owner。每个返回window及REST recovery页面可选sync对象：version:1、cursor:string、mode:snapshot|delta、base_cursor?:string、order:number[]（完整权威物理row_id顺序）、revisions:Record<row_id,详情完整可见投影hash>。messages在snapshot为完整窗口、delta为新增／变化行。仅opt-in sync下，matched=true须整窗口含详情revision可复用；即使cards coverage相同但详情revision变化，也必须matched=false并携变化cards（delta）或完整cards（snapshot）；旧无opt-in行为保持。matched=false按sync模式恢复。完整返回行数看coverage.window.returned，不等于delta messages.length；有删除靠order排除，禁止append拼接。
3. 服务端cursor只是不透明随机定位符，绑定实际DB路径／Profile／requested Conversation／selector／投影版本。短期有界LRU（最多128窗口，每窗≤500身份，TTL1小时），只存身份hash与coverage，不存正文、不建DB／持久事件日志。REST与Gateway可在不同进程：cursor不认识须安全完整窗口回退；RPC精确matched receipt仍可给新cursor，不依赖两进程共享内存。并发访问加短锁，DB／history／replay锁外投影与hash，不扩大已有锁区。
4. cards保留旧外观；history_sync opt-in完整投影hash负责所有详情字段变化，详情请求同opt-in返回detail_revision。客户端不能把旧期望revision套在迟到新详情上。缓存用原生UID计消息、物理行定位详情，保存的消息+详情+版本+cursor在同一IDB条目原子写入；损坏／不完整配对不请求delta，回退必要快照。合并必须核owner、selector、base_cursor、顺序唯一、每行存在、coverage数量、版本、旧轮次资格。
5. 最新Turn由原生source身份优先；持久消息沿同SQLite快照及原生display_kind，排除Steer与不启动Turn的Framework Message，不以最后任意user行为边界，不猜文本或provider ID。最新Thinking只覆盖最近500条的缓存范围，不为凑500预读其它正文；如最新Turn跨首屏，仅把其范围内Thinking字段传给客户端。为保证该行完整详情revision一致，允许对确有Thinking的候选行在同一短DB快照取原生完整字段、锁外投影/hash；不得预取非Thinking行正文，不得把同一行未展开工具详情传入wire或缓存。可选sync.latest_thinking结构：source（原生source身份或null）、order（本次范围内权威row_id）、rows（变化的Thinking字段与原消息身份，不包含未展开工具详情）、positions（row_id→逻辑position）、revisions（row_id→完整详情revision）。该bundle与同一个window cursor一起差分，不能另造逐Thinking游标；snapshot模式传全bundle，delta模式只变化rows，order权威移除已不属最新Turn的主动补齐候选。详情仍可留在对应旧消息缓存。活动未落库Thinking只取既有完整state_snapshot验证的有限前缀，保存类型化展示字段和UID／source／epoch／切点，不能保存原始事件或伪造持久行／权限。无法证明原生身份只保内存。
6. 客户端复用DisplayCache同一个Conversation条目，schema升级隔离旧展示缓存与可用于同步的记录。500预算统一覆盖各窗口、已取详情、最新Thinking候选及未落库前缀，按原生消息身份去重；不独立给每窗口500，不截正文／详情。按服务端total／position淘汰最近500之外的复用内容；当前阅读早期页可留现有页面内存，但不重新持久化。默认首屏200与Show More保持；不为填满缓存主动读500。完整详情保留数据不改变UI折叠；旧未完整片段不得标完成。配额清理／失败只降级缓存，不影响在线主流程。
7. 暖／冷已有可核缓存时可直接把receipt+cursor带入activate，无须先REST重传200条；缓存缺失只取必要窗口。读绑定／元数据按owner+recovery round共享；与viewport变化解耦，但新可见窗口仍校验。Usage／Context／Pending只等绑定，不能等整个Chat封套；必须保原envelope／receipt权限边界；Pending现有generation／activityVersions与snapshot对账须防早发晚返覆盖，必要接线限controller-pending.ts并补受控反例。已完成同轮summary给Usage fallback复用，保旧调用默认。菜单只在New Chat或实际打开需要时读；去掉earlierPages无条件重传，实际可见历史仍核验。PageRecovery状态及composerActionPolicy产品行为不改。
8. Android删除业务恢复deadline的reload路径，保单一document／nativeRecoveryId对账、网络／前台信号、通知导航排队及附件返回保护。可持续同页恢复，不引入另一套刷新定时器；系统自然杀进程仍冷启。

## 当前状态与编排

- M0：前端5cbef57与37a8e4c已亲审提交／push，未部署；微信包已亲审，main e1b124d已提交／push。
- B1／F1：实施及主会话代码审查已完成；A1已交回且主会话亲审，82项原生测试通过，无真机证据。main修复完成并冻结后并行，源码范围不交叉。任何契约真阻塞向主会话整点报告；不发流水账、不再派生。
- 主会话已查恢复链串行、无条件隐藏读取、warm旧分页更多及APK5秒deadline。正式数据量证据待I1。
- 主会话亲审接线，独立门禁按整轮执行，不逐包派Verifier。

## 缺陷、取舍与快照

- 保护后端main已存在Noting调试／07／生成协议／presentation报告dirty，原始旧工作区全部不动。前端.DS_Store不入Git。
- 最终部署按U23授权及既有SOP执行，无生产模型／真实微信测试外发权限；无真机时不称Android最终体验通过。已有前端基线失败按旧轮记录，若触及必须定向辨明，不能改断言掩盖。
- 冻结检查沿根AGENTS，不增删／放宽阈值；大型检查集成收敛后统一一次，失败修复定向复测。
- 报告位置reports/，完整日志在ignored .hermes-dev/incremental-sync-20261027或前端.archive/incremental-sync-20261027；子Agent不提交。

- B1工程细化（2026-10-27，主会话决策）：现有DB无独立详情版本列，跨首屏Thinking候选同一行可能含工具参数；为保证完整revision检测原位修改，允许服务端短读该候选的完整原生字段，锁外算hash，仅传Thinking字段。这不改变客户端懒加载或缓存白名单；需反例证明同一行工具参数变更改变revision但不出现在latest_thinking响应。未新增schema或锁内投影。

- U13追加：compact原生active状态须立即穿过历史保留画面，Context不等待Chat／Usage；压缩busy与生成Turn恢复证明需区分，完成／取消／失败／断线均沿现有生命周期安全收敛。主会话先查明并设计，再交B1／F1实施及反例；无生产写操作。

- U14工程方案：仅session.compress默认取消客户端固定完成期限，保普通RPC30秒与显式deadline；socket断开仍释放pending为IndeterminateError。压缩入口专门将未决交原生观察，不报确定失败、不重发、不清未确认草稿；真实错误保留。U15修复Toast父滚动容器裁切阴影，主会话定案为把阴影绘制置于裁切后层级，保既有几何/滚动/交互；main隔离修复后并入功能分支，实际截图验边缘。

## U16 · Idle父owner生命周期包（主会话设计）

采用最窄保留现有父实例方案，不新增冷恢复扫描器：在noting_timers现有记录绑定准确weak owner、原生compaction epoch与原period；查询维护依赖须同时核对这些事实和当前有效开关／周期。timer firing到同步冻结/已受理completion之间连续交接保护；用现有_NotingCompletion的准确parent/admission及notified/closed生命周期覆盖child、父压缩和发布，不另建任务账本。普通orphan和TTL/LRU共享维护依赖predicate，沿原生周期重新检查；这是有界活跃维护工作，cap沿已有live-work豁免，不能无条件永久保活或忙等。

显式关闭/替换仍沿原生close边界。复用context_compaction_request原生owner epoch及_session_persist_lock，使close与准备阶段同步身份核验/冻结具有确定先后；cancel timer只取消准确旧owner，不影响同DB/ref新owner，不改durable due/period/trigger。避免sessions_lock、conversation_timer_lock、registry、persist、Framework锁反向嵌套；回收predicate在sessions_lock内只能短时读准确注册事实，不在此读DB/等待网络。准备检查必须在claim/admission之前，不用空列表return掩盖消费后失败。若valid parent真无可冻结上下文，保留未消费周期供合法attach，不循环重试或重建Agent。这里的保留周期限定父owner关闭／epoch退休／替换等生命周期失效；global/local开关关闭仍沿既有claim的terminal cleanup清退未消费period，不freeze／admission／起child，不增加重新开启后的自动补跑。

白名单：secretary/noting_timers.py、noting_scope.py、noting_runtime.py、noting_child.py、noting_compact.py；tui_gateway/session_lifecycle.py、session_reaper.py；run_agent.py仅既有close接缝；必要独立小sibling；对应tests。禁止改schema/Prompt/预算/阈值/Provider/新scheduler/生成协议；不改增量包文件。Main/开关关闭/非eligible原生行为保持；不修改失败记录，不发真实模型/微信。报告的真实后台Heartbeat→native orphan→Idle复现必须改前失败修后正常，覆盖精确owner/period/跨Profile/回收冻结并发/显式关闭/新owner旧回调/成功Noting→真实假摘要压缩commit→Framework/失败释放。官方runner；Linux定向验证由主会话集成安排。实现整包交回、主会话亲审后先main，再并入增量分支，统一双门禁。

## U17 · 最新Thinking来源兼容（用户已确认）

旧的模糊片段保持懒取，新Turn精确主动取Thinking。B1旧“从最近可证明source保守多取”方案作废：最近可证明source之后出现无法判断是否启动Turn的typed行且无当前原生精确来源时，返回空latest_thinking，不主动补旧详情。新Turn在通用原生构建接缝合并display_metadata.turn_source，值仅为原生message_uid与turn_id；复用原持久化、必要准确行metadata补写与原lease guards，不改正文／schema／Provider wire／模型cache prefix。普通append通知／Steer／历史回放不生成标记。新标记优先于typed/queued的弱推断，实际active原生来源仍优先；冷恢复与跨渠道来源需按同快照身份验证。

扩展B1白名单仅agent/turn_context.py、必要小sibling agent/turn_source.py、确需的agent/session_persistence.py或既有DB metadata writer接缝及对应tests，不碰U16 owner包。原生写入失败为展示级best effort，不阻主Turn；测试覆盖真实typedTurn持久化到冷读、同型仅通知、旧模糊片段懒取、queued/Steer/Framework、异常标记与wire剥离。

## I1亲审整改追踪（2026-10-27）

| 项 | 负责人 | 完成条件与复验 | 当前状态 |
|---|---|---|---|
| 压缩终态Context读取失败重试、合法unknown不无限轮询 | F1 | 正式Controller失败后成功、合法unavailable结束本次读取且保旧值；隐藏IAB观察 | 代码已亲审；最终IAB复验受本地浏览器禁用阻断 |
| 已finished压缩后epoch恢复重复200条快照 | F1 | 同owner先等在途历史settle再强制终态对账；必要snapshot最多一次，其后delta；无死锁及owner越界 | 代码已亲审；最终IAB复验待执行，反例见integration报告 |
| 首次展开同一旧详情重复REST | F1 | 无staged共享HistoryDetails；真正staged仍隔离；实际App首次展开一次、完整缓存重连无需重取 | 代码已亲审；最终IAB复验待执行 |
| U17旧typed来源缺口 | B1 | 旧模糊lazy，新真Turn持久来源及冷恢复，Provider wire不变 | 已亲审关闭；U17正式Turn持久化／冷进程读取与wire回归通过 |
| U16旧completion清理撞新native复用 | U16 | reserve与关闭各自原子提交，Framework→ACTIVE锁序；两种barrier时序及压缩结束释放 | 已亲审关闭；main 0a5d09cdcf，同补丁接入增量，Linux163项已覆盖通过 |

全轮门禁尚未启动；上述问题关闭并完成主会话集成后统一派遣，不以局部通过代替整轮验收。

## 重启断点（2026-10-27）

前端91ad72f已提交push；backend产品862326c0a7、文档e26b8d1062。Linux163项（159＋4定向）完成，日志SHA与清理记录已亲核。为用户重启Codex暂停，Verification /root/verification_incremental 已中断，只复制模板，尚无判据／结论；重启恢复后先读本轮索引、baseline、plan、reports再继续。Validation未派遣。本地夹具5637/5638已停止。

| 新发现／缺口 | 负责人 | 完成条件 | 状态 |
|---|---|---|---|
| test_idle_noting_owner证据写盘依赖ignored目录已存在 | 主会话／U16 | 测试自行创建精确证据目录或用既有临时目录，保断言；干净隔离导出仅重验4项，修复按main先纳再集成 | 已关闭：main5fc54fc233／增量44eb0be4c3，干净导出4项通过 |
| I1最终三个浏览器复验 | 主会话 | 隐藏IAB工具恢复后，真实Python/SQLite/HTTP/WS同document核epoch仅一次snapshot、详情单请求且冷重开复用、合法unavailable停止轮询；保草稿与Context表现 | 工具报disabled与用户开启截图冲突，连接重置未解 |

## 用户最新执行调整

用户明确两仓提交后直接进Validation，停止本地Verification，由其自行把准确版本和原口径prompt交给云端AI结合skill静态审查。本地Verifier已中断，无通过结论。主会话继续独立Validation的计划审阅／实际验收与集成收尾，不把顺序调整冒称V1通过。重启后隐藏IAB已恢复；测试目录初始化修复已先main 5fc54fc233a0379321c13c22494923e06f302dad，四例干净导出通过，现纳入增量。

Validation已派全新fork-none sol/high `/root/validation_sync`，先独立从U01-U17与06/07范围提取完整用户场景并按技能模板落盘，主会话审阅计划后执行；本地静态Verifier `/root/verification_sync_resumed` 已中断。root已关闭自有测试页，避免同origin IDB/草稿后台写入干扰独立验收。服务8189/5199仍在隔离fixture运行，未部署。

主会话已审27项独立Validation计划并批准执行：优先组合验证200长正文冷暖加载/同页断线变化/详情复用/慢Usage/压缩及epoch；其余复用同版本有效证据，不重复大套。补充要求：新tab不等于无缓存，V01须准备自有fixture干净entry；动态过渡明确DOM rAF/MutationObserver采样或如实报告频率边界，不能从阶段截图推断零闪。计时区分缓存首显、正文切点、可操作和附属完成。真实Compact由用户动作入口验证，受控依赖仅准备/控制时序。缺设备/外发授权如实记录，不虚构通过。

## U18用户新增动态反馈

部署版排队Steer在旧Turn结束后启动新Turn时短暂双显，仅第二条有Timeline时间，随后随流式合一。root定向调查carrier/native source/历史与pending提交，不按全局同文去重。/root/steer_handoff_repro 仅新增正式中间态行为反例、只读产品，回交真实根因后root先设计再实施。V28须逐中间帧/呈现核一条，不只看终态；版本原91ad72f尚未因此改产品。

## U19审批面板稳定性（用户明确追加）

同一待审批请求的Diff/写入目标/理由应同一面板，背景更新不自动换队列或退成少信息面板。root反例改前两项失败：receive重复id将其移尾；瞬态live工具节点消失即丢Diff。方案：保持现有请求位置；首次按原严格关联核验的Diff作为该请求的只读展示证据保留，以profile/conversation/runtime/request id/command/工具身份隔离；关键身份变化撤销，审批权限仍由ServerRequests原状态控制；Command与Diff同屏。新首帧仍严格匹配，不猜未取得Diff，不扩大批准范围。

额度中断：validation_sync、steer_handoff_repro、slash_catalog_fix均未整包交回，保已有日志/partial diff，root只按实际证据接收。当前本地Verifier保持停止，云端审查版本需在后继修复commit后更新。

### C-U20主会话亲审补修（2026-10-28，第二轮送审前）

| 项 | 亲审事实与指定窄修 | 当前状态 |
|---|---|---|
| C-R1 真正Main Turn边界 | 原turn_facade在native lease受理前标started、释放后才标finished，Force检查短锁不能证明真实相邻Turn边界；移现有观察至真实受理/释放边界，结束markfalse/占用/Force按既有Framework→persist原子接缝，不加Main admission gate，不锁跨模型。须以真实run_conversation+lease而非只直接hook证明 | 已关闭于27c74b094f：root已亲审真实lease边界及正式run_conversation反例 |
| C-R2 旧registry后续生命周期 | 统一views可读旧admission，但register/finish仅UPDATE新attempt表，旧合法调用可能退化，dead-task只扫描新表；按实际行所属表兼容，不按整数格式猜归属，不迁移旧库；初始化保全与后续依法终态分开 | 已关闭于27c74b094f：实际所属表分派及旧schema/running/expired lease/attach/旧API证据 |
| C-R3 Note幂等键 | 最新有效Snapshot可跨多次成功压缩仍无新版本；幂等应按目标边界，不能全局禁止同Snapshot在后继新区间再次注入。保每个目标interval一次，移除跨interval全局snapshot UNIQUE/拦截，原资格/队列重选/事务回执不变 | 已关闭于27c74b094f：真实连续边界／同Snapshot／重复检查事务证据 |
| C-R4 Note读取失败不得误报压缩失败 | adopt_native_publication属于原生成功commit后的Note展示增量，其资格读异常须日志隔离并返回；原生result/commit不被推翻、不吞原生异常、不伪receipt，后续检查可补偿 | 已关闭于27c74b094f：native成功后Note读取抛错不改原生结果，后继检查补偿 |

四项是统一门禁前主会话设计与接线审查，不计新的正式Verification/Validation轮次。原180＋3及十检查证据只按对应源码保留；追加改动按影响定向补证，不重复全量。

## U25／U26用户追加（第二轮门禁前纳入）

用户已确认冷启动新document首次真实可见历史提交后统一立刻到底，不受加载期用户滚动阻止；同页warm/reconnect保持。root方案复用PageRecovery document与commit/ack一次资格，useTimelineReading只在该提交instant到底，不能用组件mount猜新document。cold_start_viewport仅改page-recovery/types/chat-presentation及必要小sibling/测试，不碰App/layout或后端。

APK主动顶栏下拉先出浏览器原型。最新设计替换此前整页下移：页面/背景静止、圆背板橙环从顶部中央浮现、约200手指位移经阻尼映射固定80px指示器行程、40背板/24橙环按token、阈值全亮后release一次reload；正文起手/控件tap不劫持，取消/回退收回。header_pull_refresh_preview只新增隔离组件/CSS/测试及ignored原型，不改正式App/layout，root隐藏IAB截图/动态预览后再接APK。正式Web不自动开启。主会话亲审并接线；8313旧候选APK已核但不再当最终包，最终源SHA后重建。原三轮上限/范围内门禁与正式上线完成条件保持。

第二轮root集成接收：U25 ba7decd与U26 03a9689已纳入FEbc02d01，正式Android限定入口已接；两仓main历史纳入BE2dc4398／FEbc02d01，产品零合并增量。root已过目新增R47–56，完整Validation56项门禁前计划通过。接下来本地全新上下文完整Verification，不逐包审；APK按FEbc02d01构建中。


## U27再次明确：APK没有任何自动刷新依赖

用户原话及明确目标已落06顶部及索引。root已扫描正式原生/前端：ForegroundRefresh无reload，现仅冷启动loadUrl、真实认证redirect导航、用户按钮/顶栏手势reload；不过PackagedWebViewClient.appDocument的临时网络异常／5xx返回静态unavailable页，SPA尚未启动，所以不能同页自愈。此为主会话开发接线发现，独立Verifier仍处于仅规格判据阶段，不算正式门禁发现／新一轮。

root指定窄修：临时bootstrap传输失败／暂时服务错误时返回现有内置SPA和明确deferred bootstrap标记，无token／无伪授权；Gateway只在此APK专属初始提示下首尝试走现有freshBootstrapToken，原current/abort/凭据撤销/自动retry/可见恢复均复用，不做原生循环loadUrl/reload。正常200 bootstrap路径、300..399 Authelia自然导航、真实401/403撤权与默认Web无标记调用保持；Malformed/过大引导不当成网络成功。仅native PackagedWebViewClient+必要small sibling、Gateway最小接缝/types及定向native/TS测试可改。root review/接线，先反例再窄修；新源后更新候选/APK，第二轮实现调查才开始。


### C-R5主会话收尾发现（第二轮实现调查开始前）

真实RPC反例已证：当前区间保留tail UID的失败普通Noting显式恢复时，原failed admission不重新绑定（正确），但新Snapshot未关联来源区间，selector错误将其投回同一区间，实际FM与receipt均落库。superseded审计草稿恢复拒绝/未泄漏对照通过。原始证据见r2-joint-noting末节及ignored recovery-source-review；这不是正式Verifier发现，不能计新整轮。

root方案：仅recovery路径由runner传可信原admission，经commit同conn核Conversation/Anchor及有效来源；Snapshot现有termination_json在同一INSERT附内部noting_origin={admission_id,compression_interval_id}，与普通type/reason工具termination输入严格隔离。DB notebook_commit_snapshot_result_conn仅新增默认None内部参数/必要小helper，原默认行为保持；原失败Task/child/owner不复活、不改写。Note同一来源资格读取normal关联或新内部审计，旧recovery无审计时只读已有Session recovery audit+原admission事实核对，不迁移旧库、不改Full来源顺序/目标interval receipt一次机制。来源矛盾不能默默借资格。白名单noting_child/noting_notes/必要小sibling/hermes_state_secretary_notebook与相关回归；不新表/事件队列/gate/Prompt。真实同区间无FM、后继边界合法晚到一次、旧形状兼容与事务回滚补证，定向检查不复跑180。

用户已获e545359预览APK（Downloads preview文件，SHA41a193804d481a87bb2f28956c3b18659a88c8c0bc5204893ad9d52447e4d5e2），原签名/439资源/0.1.9及完整性全部通过；这是用户主动要看效果的预交付，不作门禁/上线已完成结论。Backend仍3426线上，后端C-R5及正式双门禁/部署尚未完。


### C-R6与U28（第二轮统一门禁前收口）

C-R6正式反例：最新来源显式recovery在SDK运行，但原admission仍failed；旧Note在Main间隙flush抢先落库，占后继区间唯一receipt。root设计同一Note资格纳入实际recovery在飞源，复用已有recovery native lease和可信审计，已提交Snapshot原子origin证明完成便解除pending，不等末尾model_config清理；queued前建立既有lease，失败/结束释放，终态唤醒同一资格检查，无新队列/通用FM变更/Main gate。明确跨进程极窄“lease已预留、Session尚未durable”竞争：重读仍无事实则沿既有NotingRecoveryError/4002如实busy拒绝，重用同request_id，不伪queued/另开任务/短轮询；成功受理后原幂等不变。此为未受理前真实预留状态的工程收敛，不新增错误码或权限。

U28是用户真机对原U26的失败反馈，原话及“完全没出现”已落索引，原APK e545严格校验只能证明包，不能覆盖手机触摸。root设计并由apk_header_pointer_capture实施正常h1 implicit→container explicit迁移的lost事件不能冒泡取消；只container自己的capture loss才取消，pointercancel仍取消。改前2反例失败，FE d1a53cf窄修+正式AppFrame/TopNav/AndroidHeaderRefresh/StrictMode正反例31项/types/冻结健康通过；没有扩大正文起手/改变阈值/移页面。新预览d1a53cf APK已按用户要看包交付Downloads，SHAfb651a0bbeae025776016d58fa594b68aa2f0fb16faeaf88aa6b3983ef564a2d，32123717字节，原签名/439资源/0.1.9(1009)/ZIP/16KB核验通过；修后手机尚未确认，不能宣称唯一根因/实机已通过。

独立Validation新增R57–R62六条已root逐项过目，计划共62场景/24目标，保原56；无正式执行。U28映射原R51/52/54历史失败，后继用户复验与当前版本正式场景分清。独立V的125判据仍已过目、实现调查尚未开始；C-R6整包完成及FE d1a版重锁后接续同一次第二轮。

**发布后数据保护补充检查：** 现有受限发布执行器严格要求启动前后messages及Secretary表相同（只容许新增空伴随表）。U20新runtime恢复可能合法补注旧最新Note并写FM／receipt；若该动作恰在发布启动后发生，不能改写收据为通过、关闭保护或自动回滚DB。保留原拒绝及现场，逐行只读比对三库发布备份与运行库，核是否仅为既定真实Note载体与同事务receipt及其必要计数；无法完整解释则保持未验并向前修。该检查是已授权自动注入的发布取证边界，不新增业务写授权。最终source／bundle尚未锁定，不提前apply。
