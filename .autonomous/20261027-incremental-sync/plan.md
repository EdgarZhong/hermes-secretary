# 实施计划：20261027-incremental-sync

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
- B1／F1：已派遣实施；A1已交回且主会话亲审，82项原生测试通过，无真机证据。main修复完成并冻结后并行，源码范围不交叉。任何契约真阻塞向主会话整点报告；不发流水账、不再派生。
- 主会话已查恢复链串行、无条件隐藏读取、warm旧分页更多及APK5秒deadline。正式数据量证据待I1。
- 主会话亲审接线，独立门禁按整轮执行，不逐包派Verifier。

## 缺陷、取舍与快照

- 保护后端main已存在Noting调试／07／生成协议／presentation报告dirty，原始旧工作区全部不动。前端.DS_Store不入Git。
- 无生产部署／发送权限；无真机时不称Android最终体验通过。已有前端基线失败按旧轮记录，若触及必须定向辨明，不能改断言掩盖。
- 冻结检查沿根AGENTS，不增删／放宽阈值；大型检查集成收敛后统一一次，失败修复定向复测。
- 报告位置reports/，完整日志在ignored .hermes-dev/incremental-sync-20261027或前端.archive/incremental-sync-20261027；子Agent不提交。

- B1工程细化（2026-10-27，主会话决策）：现有DB无独立详情版本列，跨首屏Thinking候选同一行可能含工具参数；为保证完整revision检测原位修改，允许服务端短读该候选的完整原生字段，锁外算hash，仅传Thinking字段。这不改变客户端懒加载或缓存白名单；需反例证明同一行工具参数变更改变revision但不出现在latest_thinking响应。未新增schema或锁内投影。

- U13追加：compact原生active状态须立即穿过历史保留画面，Context不等待Chat／Usage；压缩busy与生成Turn恢复证明需区分，完成／取消／失败／断线均沿现有生命周期安全收敛。主会话先查明并设计，再交B1／F1实施及反例；无生产写操作。

- U14工程方案：仅session.compress默认取消客户端固定完成期限，保普通RPC30秒与显式deadline；socket断开仍释放pending为IndeterminateError。压缩入口专门将未决交原生观察，不报确定失败、不重发、不清未确认草稿；真实错误保留。U15修复Toast父滚动容器裁切阴影，主会话定案为把阴影绘制置于裁切后层级，保既有几何/滚动/交互；main隔离修复后并入功能分支，实际截图验边缘。

## U16 · Idle父owner生命周期包（主会话设计）

采用最窄保留现有父实例方案，不新增冷恢复扫描器：在noting_timers现有记录绑定准确weak owner、原生compaction epoch与原period；查询维护依赖须同时核对这些事实和当前有效开关／周期。timer firing到同步冻结/已受理completion之间连续交接保护；用现有_NotingCompletion的准确parent/admission及notified/closed生命周期覆盖child、父压缩和发布，不另建任务账本。普通orphan和TTL/LRU共享维护依赖predicate，沿原生周期重新检查；这是有界活跃维护工作，cap沿已有live-work豁免，不能无条件永久保活或忙等。

显式关闭/替换仍沿原生close边界。复用context_compaction_request原生owner epoch及_session_persist_lock，使close与准备阶段同步身份核验/冻结具有确定先后；cancel timer只取消准确旧owner，不影响同DB/ref新owner，不改durable due/period/trigger。避免sessions_lock、conversation_timer_lock、registry、persist、Framework锁反向嵌套；回收predicate在sessions_lock内只能短时读准确注册事实，不在此读DB/等待网络。准备检查必须在claim/admission之前，不用空列表return掩盖消费后失败。若valid parent真无可冻结上下文，保留未消费周期供合法attach，不循环重试或重建Agent。

白名单：secretary/noting_timers.py、noting_scope.py、noting_runtime.py、noting_child.py、noting_compact.py；tui_gateway/session_lifecycle.py、session_reaper.py；run_agent.py仅既有close接缝；必要独立小sibling；对应tests。禁止改schema/Prompt/预算/阈值/Provider/新scheduler/生成协议；不改增量包文件。Main/开关关闭/非eligible原生行为保持；不修改失败记录，不发真实模型/微信。报告的真实后台Heartbeat→native orphan→Idle复现必须改前失败修后正常，覆盖精确owner/period/跨Profile/回收冻结并发/显式关闭/新owner旧回调/成功Noting→真实假摘要压缩commit→Framework/失败释放。官方runner；Linux定向验证由主会话集成安排。实现整包交回、主会话亲审后先main，再并入增量分支，统一双门禁。
