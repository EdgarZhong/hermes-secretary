# Verification：20261024-web-recovery（首轮独立审查）

## 1. 审查对象与结论概览
审查者：独立 Verification 子 Agent（gpt-6.1-sol；无主会话历史上下文，不派生）；2026-10-24。索引 `.autonomous/20261024-web-recovery/snapshot-index.md`，基线 `baseline.txt`。冻结主仓 `ba83d2b430e3448461dd7feb9f1acd8fc94c6cc9`、Web `9fd115d3b016bb51a8a78dd1724684fd1890665c`；待审主仓 `1ca5d68581e0fa09d824a95ac2682e8afaf158fd`、Web `c4f2f6dca05a81d88fe1ca1e75d90dc9b0e182a7`。

**门禁不通过：20组独立判据完整覆盖，14组符合、6组违规（G03/G10/G13/G14/G15/G16）；4个范围内阻断 V01–V04，未关闭。** 各组的相关子条件全部纳入，分组数量不代表缩减原R1–R10。核心后端有界读、D0/S/D1、原子cut与前端staging主路径已落实，但可见失败边界、菜单读取登记、缓存更新与冷开实际DOM交接仍有可复现偏离。不能进入“Verification已通过”的声明。

先依据冻结原文落第2节，再读取编码指导、实现及证据；只写本报告和ignored证据，无产品代码改动、提交、部署、模型、设备或浏览器操作。审查后段主会话并行整改已改变Web工作树测试/呈现文件，本报告结论固定于上述候选；晚挂载反证从git show固定候选源码，仅改import定位。用户冻结后C17明确豁免本轮真实APK验收：仍核R8机制、单测与APK资源/签名，真实WebView未验不伪称通过；Web实际验收仍由后续独立Validation完成。

## 2. 独立要求清单与覆盖
判据建立：2026-10-24；先仅阅读冻结索引、基线及 backend `ba83d2b430e3448461dd7feb9f1acd8fc94c6cc9` 的 06 §0.4、§1.2 现行替代、§1.3、§1.4（R1–R10）、§1.13、08 §1/§3；尚未读取产品实现、动态计划和实现报告。下表为独立起点，不以实现反推规格；无未决产品解释。分组不豁免子条件。判据建立后仅按用户明确补充C17调整G20实际APK验收适用性（豁免／未验），R8机制、Web实测与其余判据原样保持；不迁就实现。除 G19 流程约束外均为直接要求；“正式接线/失败不得假成功”为其必要推导。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| G01 | 06 §0.4/§1.3/§1.4：薄客户端、列表与当前Conversation完整重读 | 行为/数据边界，Web/APK | 服务端为真值；不建第二历史库，不减少请求，不全库正文扫描/批量激活；导航不创建/取消Turn，沿真实lineage | 初次/重连真实读取同覆盖；旧画面只是过渡；正式写受理与消息投影保持 | 矩阵G01 |
| G02 | R1：唯一page-recovery owner/代次/结果 | 机制/取消/并发 | document、真实WS connection、epoch、recovery和demand身份明确；ok/error/cancelled/retained不混淆 | Controller唯一协调器；owner/连接过时不能提交；同连接触发合并dirty，正常delta不重启 | 矩阵G02 |
| G03 | R1/R5：失败恢复与ready | 行为/失败 | 当前需求全部成功、证明有效、React提交/anchor完成才ready；背景另记；失败不作idle或unknown真值 | 初次失败仍可重试；前台1/2/5秒、隐藏/离线暂停；404只读确认后退New Chat清缓存；不自动重放写 | 矩阵G03 |
| G04 | R2：有界REST及activate可选扩展 | API/兼容 | 任意合法anchor、latest200/max500、冲突400；coverage含身份/边界/digest；receipt仅本轮REST；最多2窗口/详情12行分批 | REST/RPC共用纯读helper；版本宣告才发新参数；老接口保持，降级不冒称新版ready | 矩阵G04 |
| G05 | R3.1：真实SQLite事务与有界payload | 指定机制/历史 | 同一conn显式只读BEGIN解析owner/spine/代表与范围；事务后投影，无写索引回填；深anchor不全正文物化 | 真实SQLite SQL/深anchor/多lineage UID退役证据；不是mock或串新conn假快照 | 矩阵G05 |
| G06 | R3.2–7：D0/S/D1证明和锁 | 指定机制/竞争 | attach后目标history_lock有界250ms；DB/replay不嵌套；D0旧区间D1相同，D1完整tail；破坏改写view_changed，增量断层coverage_gap | 有界重试（后端一次/前端两次），真实独立连接/进程正式writer覆盖append/replacement/rewind/compression/delete；不得追静止或阻塞Turn | 矩阵G06 |
| G07 | R3.5–8：活动Turn/输出/失效 | 机制/owner/运行态 | 持久输出按身份与D1对账，退役UID不复活；未持久输出须当前租约/起点；外部owner无relay不得idle/ready；writer与sessions.changed触发当前历史重读 | 完整snapshot+正式relay与持续delta/下一Turn/外部lease证据；具体writer接线，rewind_count签名；无mtime全表轮询 | 矩阵G07 |
| G08 | R2/R3：原子replay cut和有限suffix | 机制/顺序/资源 | events/latest/truncated/epoch同锁；有限B逐seq补齐，B后继续；新epoch/runtime丢旧cursor；观察副作用与projection去重独立 | ring截断/缺口/held补齐/4096帧8MiB超限明确失败；不丢帧报ready、不重复通知/toast | 矩阵G08 |
| G09 | R4：viewport覆盖与稳定分页 | 行为/覆盖 | 真实可见首尾anchor/offset及展开facet决定需求；深anchor直定位，已加载≠本轮验证；首次tail固定后续分页，不拼新旧offset | Load earlier同helper；邻接/重叠证据；离屏解除阻塞，进入旧页局部校验而不冻全页；未验证≠删除 | 矩阵G09 |
| G10 | R5：全资源登记及正式入口 | 接线/所有页面 | initialize/select/gateway.ready/online/visibility/Android同入口；Profile/配置、可见侧栏旧页、title、cards/stream、胶囊、Pending/审批、Secretary/Schedules/Compaction和已开详情全覆盖 | 可见需求必需/后台分离；组件不以mount唯一取数；staging详情12行批次不等React发布；漏登记负对照阻断ready | 矩阵G10 |
| G11 | R5/08 §1/§3：Files/owner隔离 | 边界/Files与跨Profile | Files固定Profile/root/path/preview；root/list/文本/媒体实际资源都真实重读；不污染聊天cwd/恢复/附件/配置；第三方渲染失败不能ready | 同ID跨Profile、route/迟到REST/IDB、Files返回与深链接均owner正确；错误不换Profile，New Chat唯一选择Profile | 矩阵G11 |
| G12 | R6：缓存schema/白名单/身份 | 存储边界 | 独立IDB secretary-display-v1，canonical origin+profile+stored route，列表owner roster；首次只精确已确认owner | Timeline持久cards≤200+额外有界窗；不含折叠正文/runtime/seq/审批/pending/草稿流/Notebook/Schedules/令牌/Blob/整响应 | 矩阵G12 |
| G13 | R6：容量/失效/写入资格 | 存储/失败 | 2MiB/会话、16MiB/10会话、列表500/1MiB、7天TTL/LRU；超大正文跳窗不截断；坏schema/quota降内存 | 迟到IDB不盖真值；成功对账展示后闲时≤1Hz写；失败保留不续成功时间；404/owner消失删除，rewind/压缩替换，认证失败清document敏感投影 | 矩阵G13 |
| G14 | R4/R7：单次不可变展示交接 | 机制/可见提交 | state业务实时，visible/staged不共可变binding；一次commitId；对齐窗口真实边界且内容/身份/facet/timestamp判前缀 | React layout同帧恢复anchor、不清空/remount；深窗与tail间明确gap，未验中间页不冒充路径；ready在anchor完成后 | 矩阵G14 |
| G15 | R7：滚动衔接 | 表现/交互 | 公共前缀覆盖当前所见则约240ms ease-out去真实tail，禁止instant/ResizeObserver抢位；delta增长不续期 | 深anchor保留DOM/offset、无位移不动；用户wheel/touch/键盘/拖滚立即取消不重播；降动效受控定位，真破坏可重定位 | 矩阵G15 |
| G16 | §1.13/R7：Usage/Context有效值与动画 | 表现/统计/兼容 | 同owner/统计view有效值保留（零合法），unknown不虚构；模型/provider/rewind不兼容失效；当前规范展示签名才触发 | 首次/同值/切view/切owner不闪；约120+480ms/600ms合并不续闪；降动效静态；不改open/尺寸/滚动；不缓存运行态 | 矩阵G16 |
| G17 | R8/§1.2替代：JS/Native身份闭环 | 平台机制 | hello仅身份，recover同入口，ready当前document/nativeRecovery/recovery/demand且先recovering；health仅存活连接 | onPageStarted使旧document无效，普通网页零行为；旧包/旧connected不能解除deadline；可信origin+mainframe维持 | 矩阵G17 |
| G18 | R8：5秒/退避与保护 | Android生命周期/失败边界 | 真前台单调5秒固定窗口、onResume/online合并不续期；4.9秒有效ready成功，5秒超时赢；冷启动不额外刷 | 无JS独立watchdog，reload后10/15/20/30并每document恢复；认证/附件不打断；通知目标owner恢复后确认，协议不配明确降级 | 矩阵G18 |
| G19 | R9：范围/模型/健康 | 工程约束/本轮 | 全6.1无Astra、不派生；模块拆分不增加旧facade健康超标；保留既有视觉及通知/发送语义 | 差异范围与冻结检查阈值核对，禁止部署/真实模型；已有健康超标不得扩大 | 矩阵G19 |
| G20 | R10：同版机制证据及平台边界 | 验证/完成条件 | 全表竞争、分页、详情、owner、失败、动画、APK机制均需匹配版本证据；Robolectric不能代实际WebView；APK资源内置匹配 | 审查证据底座/负例有效性；不重复大套；真实用户结果交独立Validation，构建/签名另核不冒称实机通过 | 矩阵G20 |

## 3. 逐条实现证据
路径以主仓根为默认，`web:`为 `/Users/edgar/code/hermes-secretary-web/`。证据根E=`.hermes-dev/web-recovery-20261024/`，所有“符合”仅指Verification已查机制；真实用户平台效果不由单测代签。第2节为每行原文→不变量依据。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| G01 | web:controller initialize/select/handleBroadcast→ControllerPageRecovery；REST messages与native resume/activate；sourceTimeline原消息投影 | 亲读初次/同epoch恢复调用、只当前正文/摘要列表、只读404前置、旧发送/编辑/lineage路径差异；正式Controller real DTO测试核每轮请求，导航无写重放 | web:controller.ts:488–525/706–769/863–868；controller-page-recovery.ts:373–445；E/frontend/accepted-tests.log | 符合；保留薄客户端/分页/真实owner基本边界；可见资源完整性缺口单列G10 | 未调用模型、未验用户页面；不把摘要读取当其他正文恢复 |
| G02 | web:Controller唯一ControllerPageRecovery→PageRecovery；owner/connection/current→resourceKey→read结果→commit | 亲读generation/cancel/dirty合并；测试旧owner/路径晚到、同连接online dirty、撤除慢需求、delta签名不增代次、局部读取失败重试 | web:page-recovery.ts:17–247；recovery-demand.ts；E/frontend/review-fixes.log | 符合；协调器显式区分ok/error/cancelled，旧轮不能commit，正常流不重启 | 具体reader漏报失败仍见V01，非协调器将错误吞掉 |
| G03 | PageRecovery.run required结果→reconcile→commit→layout ack；Controller readUsage→UsageViews.sessionView | 正式Controller冷开后部分usage_detail＋补充summary503反证：result=true/committed，usageError=503、retained=true；旧完整RPC失败用例能拒绝但未覆盖该部分成功路径 | web:usage-view.ts:65–103；controller-page-recovery.ts:313–317；E/verification/counterexamples.log第一项 | **违规V01**；当前可见字段依赖失败仍误作ok，无重试资格 | 合法empty/zero/unknown、404与初次1/2/5重试其余分支已核；不把合法unknown判失败 |
| G04 | sessions.py GET recovery分支→read_view/project_view；session.activate→recovery_view.activate/parse_request | 亲读默认200/max500、任意UID/row、offset/detail冲突400、owner receipt/版本、最多两窗/12详情及前端批次；旧无参数分支保留；native fixture为正式route/handler产生 | sessions.py:791–895；tui_gateway/recovery_view.py:21–50/319–343；E/backend/recovery-final.log；backend/generate_fixture.py；两仓fixture字节相等 | 符合；可选能力宣告后用新封套，旧后端明确错误不冒称v1ready | 受控runtime元信息/无模型；非所有可选字段等同DB共事务 |
| G05 | read_view→_snapshot同conn→lineage/_display_sql/_read_window/_details→事务外project_view | 亲读显式事务入口、SQL身份去重/UID退役/branch隔离/逻辑order、深anchor只单行anchor＋选定payload；真实1400行转换计数、独立conn追加仍旧快照、多lineage和多模态投影 | hermes_state_recovery_view.py:49–277；hermes_state_timeline._snapshot；tests/hermes_cli/test_recovery_view.py；E/backend/recovery-final.log/read-timing.json | 符合；无GET写库或无界Python正文物化 | 旧缺display_identity的兼容SQL可能扫描内容计算身份，未拉全正文入Python；一次DB36.8ms/投影117.6ms非SLA |
| G06 | activate attach锁释放→_capture history250ms→D0→snapshot S→D1 proofs→锁外投影比较→有限suffix | 亲读无DB/replay嵌套、全局resume不包读/投影；真实跨进程正式replace/rewind/compression/delete、独立连接append、持续改写有限失败/大append gap、锁可获取断言 | tui_gateway/recovery_view.py:85–164/247–298；tests/tui_gateway/test_recovery_view.py:97–211/298–414；E/backend/recovery-final.log/activate-final.log | 符合；相容证明非两个Promise，后端一次/前端两次立即重试后失败；不等Turn终结 | snapshot回调在D0/S间插入真实writer控制时序，未用手改内存冒称跨进程 |
| G07 | _turn_proof/_clean_snapshot；正式writer→通知文件/rewind_count→watcher sessions.changed→当前协调器 | 亲读UID/真实row/tool occurrence及租约holder/currentTurn依据；实际lease交接、缺完整snapshot/idle未知输出拒绝；持久工具parent/live result与异常terminal对账；writer通知四类路径 | recovery_view.py:137–244；hermes_state_history_notifications.py；messages.py:844–871；secretary_foreground.py:220–243；change_watcher.py:126/200；E/backend/recovery-final.log/targeted-tests.log | 符合；无来源旧尾不复活，外部relay不可证时明确runtime_unavailable；同数编辑失效不靠任意mtime轮询正文 | 外部owner无输出时不保证成功，但正确拒绝；不声称真实模型/外部进程运行完整Turn已验 |
| G08 | events.since→read_replay_cut同锁；Controller observeControl/event→replaying hold→installCut→独立projection游标 | 亲读snapshot S/有限B逐seq校验、held>B连续补入、epoch/runtime拒绝、4096帧/8MiB超限失败；并发stamp锁外decode核虚水位；正式Controller suffix/held重复及request.cancel即时移除 | event_replay.py:133–145；methods_session.py:2190；web:controller.ts:1150–1223；controller-page-recovery.ts:136–155/473–501；E/backend/targeted-tests.log；E/frontend/accepted-tests.log | 符合；未用latest_seq跳过缺失，观察副作用与staging不互相跳帧 | 缺口可失败；不以ring唯一恢复活动输出；controlled事件不代表真实供应商 |
| G09 | useTimelineReading需求→readWindows最新/深anchor→HistoryWindows→App真实gap按钮→loadEarlier | 亲读首尾/offset/facet登记、深anchor直取、有界background、verified代次、邻接/重叠冲突重读、gap非message；深窗口＋tail不下载间隔，1000+行真实后端和helper冲突测试 | web:history-coverage.ts:12–64；controller-page-recovery.ts:278–289/343–372/458–471/528–544；App.tsx:141–144；E/frontend/review-fixes.log | 符合；覆盖与加载状态分开，offscreen不挡当前屏；失去anchor仅正式anchor_not_found才重定位 | 动画/子树真实呈现另见G14/G15；普通分页不保证所有独立资源同一物理瞬间 |
| G10 | recovery-resources注册→Controller读Profiles/列表/usage/pending/secretary/schedules/compaction/facets/capabilities；App各需求effect | 亲读必需/后台，staging详情12批次无需React effect；缺Files登记负例拒ready。但实际App打开Model dialog后无capabilities需求；config.get reasoning独立effect吞错；model/catalog/profile展示字段未统一stage | web:recovery-resources.ts；controller-page-recovery.ts:299–357；App.tsx:383–386/440–466/469–487/580–587；E/verification/app-registration.log | **违规V01/V03**；当前菜单被算后台，缺共同失败/交接边界，不是单纯测试不足 | 其余资源正式路径已查；菜单关闭应解除必需，而非永远阻塞 |
| G11 | App Files→files-current固定FILES_PROFILE→default-cwd/list/read-text/authorizedFile→真实renderer状态→layout ack | 亲读root/path/preview精确key、取消reject、owner路由、返回聊天、新会话cwd分离；文件列表保留、renderer失败、换path取消测试；Profile选择仅New Chat | web:Files.tsx:46–76/159–223；FileViewerPreview.tsx；core/files.ts；profiles.ts:85–93；E/presentation/frontend-final.log；E/frontend/review-fixes-integration.log | 符合；目录/文本/媒体资源都重取，未用旧ObjectURL算成功、未借当前聊天Profile | 第三方renderer返回点受控，真实文件用户呈现由Validation；不声称设备媒体已验 |
| G12 | DisplayCache conversation/sidebarCandidate→独立IDB→displayRows/displayCapsules/displaySidebar | 亲读canonical HTTPS origin（APK真实HTTPS同源拦截资源）、profile+stored route+roster白名单；200行及附件引用；工具/Thinking正文和运行态剔除；跨owner/迟到IDB测试 | web:display-cache.ts:4–125/178–214；ControllerPageRecovery:211–229；PackagedWebViewClient.kt；E/frontend/review-fixes.log/accepted-tests.log | 符合；无第二历史库、runtime/seq/审批/Blob/Notebook等持久化；首次owner未确认不借default | 只允许URL/原生确认owner候选，缓存不授权；持久真值仍重读 |
| G13 | cache容量/TTL/LRU/queued flush；PageRecovery ready回调→putConversation | 容量2MiB/16MiB/10、sidebar500/1MiB、7天/坏schema/quota降内存、oversize跳窗、404/认证失效均亲读/测试；但正式session.usage更新展示111，flush缓存仍0 | web:display-cache.ts:127–253；controller-page-recovery.ts:84–89/519–525；E/verification/counterexamples.log第二项；E/frontend/review-fixes.log | **违规V02**；正常成功更新无缓存写路，保存值落后“上次成功展示值” | TTL不被失败retained刷新仍须修复时保持；非要求每delta或任意publish写缓存 |
| G14 | business state→cloneDisplay visible/retained/staged→commitId→RenderStore→hook/Files layout ack | 亲读深拷贝防binding泄露、立即安全控制覆盖、单次commit；mutability/anchor ack/Files布局测试通过。但晚挂载候选固定源码反证ack=1后仍top0；菜单字段亦未统一stage | web:controller-page-recovery.ts:41–46/179–208/513–526；render-store.ts；chat-presentation.tsx:239–298；E/verification/late-mount-candidate.log | **违规V03/V04**；父级commit/ack不能证明实际子树展示及定位完成 | 不要求等待240ms动画完成；要求初始定位事实和后继DOM不破坏既有following |
| G15 | timeline layout anchor→handoff240ms→动态tail；用户输入cancel；reduced一次定位 | 暖前缀/ResizeObserver/增长不续期、wheel含嵌套/touch/key/pointer、unknown不当破坏及降动效测试和源码已核；冷开消息子树晚挂载后旧候选只监听属性，300ms top0/tail1000 | web:chat-presentation.tsx:151–299/300–386；E/presentation/frontend-final.log；E/frontend/review-fixes-integration.log；E/verification/late-mount-candidate.log | **违规V04**；当前可见提交后不能稳定落真实末尾 | 反证jsdom控制真实hook DOM挂载；主会话隐藏IAB同现象是独立线索，未将其口述代独立证据 |
| G16 | native usage/context→App字段→规范显示签名→useValueUpdateHighlight＋CSS；成功数据cache | 亲读Session/Latest与zero/unknown retained及模型/provider/rewind兼容；首次hasData、相同值/owner/view/open、600ms合并和120+480/reduced静态测试。但补读失败误ready及普通成功值不缓存 | web:App.tsx:375–435；indicators.tsx:16–35/90–127；usage-counters.ts；E/frontend/accepted-tests.log/unknown-final.log；E/presentation/capsule-baseline-review.log；V01/V02反证 | **违规V01/V02**；展示/高亮本身有证，完整胶囊恢复与缓存链未满足 | 不将零/unknown误判失败；不按引用/observed_at闪，不推算新token |
| G17 | JS hello/native recover→同start→recovery state；MainActivity可信mainframe→parser→ForegroundRefresh | 亲读同document/nativeID/recovery/demand先recovering后ready、onPageStarted失效、网页零行为、health仅存活、navigation target确认；JS桥与parser负例 | web:api/android-health.ts:13–85；MainActivity.kt:80–95/129–135；AndroidBridgeState.kt:13–76；ForegroundRefresh.kt:100–135；E/presentation/android-final.log/三份XML | 符合；协议身份及接线齐全，旧connected/旧包不作成功 | 上层PageRecovery可因V01/V03/V04错误ready，原生正确校验不抵消上层缺陷 |
| G18 | 真onStop/onResume→固定5s→dispatch/health→reload10/15/20/30；activityResults/external page/mailbox | 亲读monotonic deadline不因owner/online续期，4.9成功/5秒超时优先、cold/watchdog/无JS、认证暂停和附件保护、通知目标跨刷新；40项真实MainActivity Robolectric/URI测试 | ForegroundRefresh.kt:45–99/113–218；MainActivity.kt；AndroidBridgeState.kt；E/presentation/android-final.log与XML | 符合；R8机制及原生回归有证，未更改通知内容/通道/保活/竖屏 | **真实WebView/后台前台/相机/认证/通知UI未验；C17用户豁免，不把Robolectric写真机通过** |
| G19 | 两仓candidate差异→新sibling/薄facade；冻结十检查/health；读取既有AGENTS与三核心分工 | 亲读无规则/阈值文件改动；health 15Python文件0阻断0advisory，旧facade自身超标指标未增；Web controller2556→约2491，新函数/文件阈值核适用范围；全6.1不派生，无模型/生产 | E/backend/staged-ten-checks.log/health-ruff-final.log；两仓git diff freeze..candidate；reports及本报告独立执行边界 | 符合；未放宽冻结规则，不把外部catalog旧失败当本轮新失败 | Pythonhealth不假称量测TS复杂度；TS新增模块和变更函数已静态核规模/嵌套，未新增超标facade |
| G20 | R10矩阵→真实SQLite/native/replay证据→Controller真实DTO→组件/Native→构建包 | 复用最终backend32、replay/watcher/投影回归；前端246及后续3文件33/45、原生40；fixture SHA一致；source-manifest24项及review6项无mismatch；APK439资源0 mismatch、v2签名有效，6a125e95… | E/verification/version-audit.json；frontend accepted-tests/build、review-fixes；backend recovery/targeted/staged；presentation Android XML；apk-manifest.json/apk-signature.log | 符合（证据方法/适用性）；旧报告未被当新代码自证，四项反证能暴露被既有测试漏掉的错误 | 原presentation manifest的5个共享模块随后变更由frontend同版manifest与定向接线补证覆盖；真实Web结果属Validation；C17豁免实际APK，候选包仍不能等同最终修复版包 |

## 4. 核心目标及验证方法审查

1. **核心目标及指定机制**：当前Conversation有限范围真实重读→正式activate封套→D0/S/D1＋有限cut连续suffix→前端staging→可见commit/布局ack的主干存在。后端证明没有退化为并行两个Promise、DB全局revision或等待Turn停止；数据库/relay证据不可证时明确失败，未伪造idle。当前完成度受V01/V03/V04影响，不能声称整页成功边界正确。
2. **正式接线和覆盖**：初次/select/gateway.ready/online/visibility/Android均有统一入口，owner/连接取消和正常delta副作用独立。R5资源大部到位，Files真实renderer与staging details无React死锁；可见配置菜单/独立reasoning读遗漏是V03，不以“已有后台请求”弱化当前展示依赖。普通Usage更新走真实事件与reader，却缺缓存写路为V02。
3. **失败/取消/边界**：针对同版代码独立加入3个最小反证文件，实际4个范围内问题均可重现。部分usage成功+补读503、有效usage更新后缓存、实际App打开菜单登记、真实hook晚挂载分别覆盖错误实现仍通过旧测试的空白；没有复制协调器/投影实现，没有用源码字符串断言代行为验证。冷挂载反证固定候选源码，控制的仅为DOM几何及挂载时序。
4. **有效证据及版本**：既有机制测试预期可追R1–R10，真实SQLite/FastAPI handler/native replay没有绕过待测算法；受控runtime/网络/renderer返回与真实用户边界已区分。主仓日志计数未重复累计；Web246与后续定向33/45是不同版本/范围，不累加总通过率。E/verification/version-audit.json确认正式DTO字节一致、frontend24及后修6文件SHA匹配。presentation旧共享模块5处SHA差异被后续frontend证据覆盖，并未靠typecheck冒称行为通过。
5. **表现层证据限制**：暖恢复动画与胶囊高亮的jsdom测试有价值，但同步子树不能证明冷开DOM实际就绪。晚挂载反证在当前整改工作树曾通过（late-mount.log），该结果**作废为候选证明**；重新从候选Git源码固定后失败（late-mount-candidate.log），故不混版关闭。新版本由全新审查者完整复审，真实Web由Validation验收。
6. **平台与包**：原生40项是Robolectric/API35机制证据，非真实WebView。主会话签名包清单记录候选前端commit、439个内置资源0差异、APK SHA256 `6a125e9573e0b337abed7630d99bbd84c3a4c90354cde95f086696f5236a9b99`、v2签名有效。真实APK安装/生命周期按C17用户豁免/未验；后续修复重新打包后需重新核资源和版本。
7. **工程健康**：冻结检查规则/阈值未改，十检查和同冻结health结果可复用。未运行无关大套、未执行真实模型/浏览器/设备/生产操作。优先先修V01/V03/V04可见成功边界，再补V02成功字段持久化与其失败TTL/owner边界；全部范围内项通过新独立复审后才能认为Verification通过。

## 5. 发现、整改优先级与范围外项
| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| V01 / P1 | G03/G10，usage-view.ts:81–89；controller-page-recovery.ts:313–317 | 已有有效Session读数→新usage_detail仅部分字段成功→补充summary GET 503。正式Controller仍startRecovery=true/committed，usageError=503，usageSessionRetained=true，总数保留旧0；可布局ack为ready | 当前可见字段所需补充读取失败却被当ok，违R1/R5“保留展示不能转ok／吞错不能ready”，APK亦可能错误解除deadline | 保留字段仍可展示，但required读取必须显式失败或具备本轮合法unknown证据；同正式Controller反例应false且自动重试，补充GET恢复后才ready | 未关闭；反证counterexamples.log第一项 |
| V02 / P2 | G13/G16，controller-page-recovery.ts:84–89/519–525；controller-event-effects.ts:17–23 | cold成功并布局ack缓存0；正式session.usage事件触发成功readUsage→界面111；flush后缓存仍0 | 只有整页commit写Conversation，普通有效更新未保存最新展示值，不符合§1.13缓存上次成功值及新值接管后更新缓存；刷新可退回旧数 | 正常同owner有效Usage/Context显示更新也应白名单合并写；不得缓存失败retained或运行态。事件→界面→缓存反例闭环通过，覆盖Context及TTL不被失败续期 | 未关闭；反证counterexamples.log第二项 |

| V03 / P2 | G10，App.tsx:469–487/580–587；controller-page-recovery.ts:330–333 | 实际App点击Model触发真实dialog后，pageRecovery.getDemand()无capabilities；Conversation页capabilities仅在demand.capabilities为真时required，故菜单仍被当后台，慢／失败不阻断当前菜单的ready。useReasoningCurrent的config.get也独立于登记表并吞错 | R5“当前实际展示配置/已打开菜单”漏登记；组件已有读取没有共同成功/失败边界，online同连接恢复也不触发该config effect | 模型/推理菜单当前展示的真实读取须纳入可见需求，关菜单解除阻塞；初次/同epoch重连/online、失败重试及慢隐藏菜单均验证。实际App打开菜单登记反例通过，并证明ready确实等待而非只补布尔值 | 未关闭；app-registration.log（1项按规格失败，dialog=true，capabilities缺失） |

| V04 / P1 | G14/G15，c4f2f6d chat-presentation.tsx:239–298 | 恢复commit先于实际消息子树挂载，父级已ack且无位移。随后消息DOM到达、视口尺寸不变，候选MutationObserver只看aria-expanded，未跟踪childList；300ms后scrollTop仍0，真实tail1000 | 冷开可停在latest窗口起点而非真实末尾；ready不能证明本轮实际展示/定位完成。旧暖恢复测试同步挂载所有节点，无法捕获 | 实际消息子树就绪及布局交接需有真实证据；保持既有following及人工阅读规则，冷开/暖恢复/局部commit/动画中局部需求不抢位。候选固定源码反例及正式App晚挂载/冷开实测通过后关闭 | 未关闭；late-mount-candidate.log（ack=1、top=0、target=1000） |

范围外项：既有wire catalog孤立review.summary失败有冻结树复现（backend/frozen-catalog.log），非本轮新回归；不据此放宽本轮健康或接口标准。冷开晚挂载现象另经本审查者以候选固定源码复现为V04，不以主会话口述代替证据。

## 6. 修复与独立复审

本报告为首轮独立全范围审查，未收到退回补审，未替新候选复审；V01–V04均未关闭。主会话并行修复/测试工作树不属于本报告的通过对象，不能将其结果覆盖上述候选失败。

| 研讨/复审项 | 原判据与发现 | 主会话提案及理由 | Verification评审/是否改规格 | 实现版本与关闭证据 |
|---|---|---|---|---|
| V01 | G03/G10：当前可见Session补读失败却committed，保留展示不能转ok | 按当前必需scope分成功/失败；Session补读失败拒ready并重试，合法unknown可成功；Latest不被另一隐藏scope失败额外阻塞 | 满足原R1/R5方向；需正式Controller反证、隐藏scope及自动重试关闭；**未改规格** | 旧候选仍失败；待新版本/新独立复审 |
| V02 | G13/G16：正式session.usage显示111、缓存0 | 同owner有效Usage/Context展示变更经白名单合并capsules，保持已验证Timeline；不从任意publish或retained刷新TTL | 满足§1.13/R6方向；需事件→展示→缓存、Context、TTL、owner负例；**未改规格** | 旧候选仍失败；待新版本/新独立复审 |
| V03 | G10/G14：模型菜单真实dialog却未登记、reasoning effect吞错 | App受控modelOpen/reasoningOpen登记需求；独立config.get转真实协调reader，保owner/runtime/可选语义；关闭解除阻塞，菜单展示字段纳可见交接 | 满足R5方向，不能只加布尔值或保留effect吞错；需实际App开关/慢失败/online同连接及共同commit证据；**未改规格** | 旧候选仍失败；待新版本/新独立复审 |
| V04 | G14/G15：候选父级ack后晚挂载子树top0/tail1000 | 主会话正在调查冷开/局部commit/消息子树挂载并追加回归；本审查者未参与实现设计 | 关闭须基于实际DOM/定位及原人工阅读和动画约束，不以新工作树单测通过跳过全新复审；**未改规格** | E/verification/late-mount-candidate.log保留失败；新候选未审 |
| C17适用性补充 | R10原要求真实APK平台验证 | 用户明确豁免本轮实际APK验收，保Web实测、原生单测及未验声明 | 仅按用户授权改适用完成条件；R8及Web范围不变，原判据建立记录保留 | snapshot-index末尾C17；本报告未操作设备 |

供final-delivery.md及主会话最终汇报的实质收敛：当前可见数据失败与合法unknown/retained必须分离；普通成功胶囊更新应写展示缓存；菜单配置也属于当前可见依赖；真实消息子树挂载是交接/定位证据的一部分。上述是冻结规格原有要求的工程落实，不是新增产品语义。当前门禁**不通过**，主会话安排整改并由全新独立审查者重新提取全轮判据、全范围复审及复核四项失败。

# Verification v2：20261024-web-recovery

## 1. 审查对象与结论概览

独立审查者：verification_v2（gpt-6.1-sol），2026-10-24。待审主仓 `dd9a4c57dd7c182ad8497f9538e115bbab3131b0`，Web `474a934f617faceeacfc670974fc72f559033276`。冻结原文版本 `ba83d2b430e3448461dd7feb9f1acd8fc94c6cc9`，索引 `.autonomous/20261024-web-recovery/snapshot-index.md` C01–C16；唯一冻结后产品验收变更 C17 豁免实际 APK 运行，保留机制、原生单测、构建签名资源核验。**门禁不通过：44项完整覆盖，40符合、4违规（V03/V05/V28/V32），0证据不足；新范围内阻断N01未关闭，不能进入Validation。** 建立下节时未读实现、测试、旧审查、动态看板；旧四项及REV-10修复已独立核对，后继配置事件交错新增N01。

## 2. 独立要求清单与覆盖

判据于 2026-10-24 仅依冻结 06 §0.4、§1.2 现行替代、§1.3、§1.4（含1.4.1 R1–R10）、§1.13；08 的 Profile/Files 保留条款及索引 C01–C17 建立。直接要求记 D，必要推导记 N；未指定代码接缝不降低机制要求。第3节同号逐行核查。以下原始独立判据保留，不以随后实现形状改写。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| V01 | 06 §0.4/C01/C10：薄客户端白名单 | D约束，全部页面 | 服务端事实源；展示缓存可丢弃，不是响应镜像或同步库 | 无持久runtime/游标/审批/Pending/Notebook；缓存不减少请求，不恢复写操作 | 第3节V01 |
| V02 | R1：唯一协调器及owner | D机制，全部恢复入口 | 单一Controller实例；页面/组件登记，不各自整页循环；Files owner独立 | origin/profile/screen/storedId精确；document/connection/recovery/demand分工正确 | 第3节V02 |
| V03 | R1：结果类型及失败边界 | D机制，所有reader | ok/error/cancelled明确；空和unknown合法，retained不等于成功 | fulfilled/空值/旧值不满足ready；404与不可用Profile明确处理 | 第3节V03 |
| V04 | R1/R5：重试合并和取消 | D机制，网络/可见性/owner | 失败1/2/5秒自动重试；隐藏/离线暂停；同owner连接并发合并+dirty | 初次失败无validated仍重试；再次断线/epoch/owner取消旧提交；delta不重启恢复 | 第3节V04 |
| V05 | R1/R7/C04：可见ready | D行为，全页 | 当前需求成功、历史流证明、React提交及anchor定位才ready；background另记 | 不等隐藏读取或动画结束，不用connected当ready；安全/业务观察持续 | 第3节V05 |
| V06 | R2：有界REST新参数及兼容 | D接口，消息读取 | 任意仍展示消息anchor；默认200最多500；不混offset/detail | 冲突400；每轮完整cards；旧响应/调用语义保持；不新增schema/BFF | 第3节V06 |
| V07 | R2：coverage证明 | D机制，历史窗口 | owner/tip/lineage/window/digest，SHA256只含规范展示及顺序 | 前后界/逻辑坐标真实；临时URL/请求时间排除；detail另证；仅内存 | 第3节V07 |
| V08 | R2：能力协商与封套 | D接口，activate/resume | 宣告v1才发送；receipt来自本轮REST；最多2窗口×500，detail12分批 | matched服务端重读确认，不符整窗替换；老后端明确降级不能交付通过 | 第3节V08 |
| V09 | R2/R3：原子replay cut | D机制，events.since | events/latest_seq/truncated/epoch同锁复制，锁外解码 | 并发stamp不能虚抬水位；旧契约/open_requests规则保持 | 第3节V09 |
| V10 | R3.1：同conn短只读事务 | D机制，DB helper | 一个BEGIN内解析owner/spine/代表身份/边界/payload，结束后投影 | 无串调新conn假快照；旧只读GET不补索引/写身份；深历史不全正文物化 | 第3节V10 |
| V11 | R3.2–3：D0/S/D1与有界失败 | D机制，activate完整路径 | 先attach，目标history锁；D0→S→D1；原区间/lineage/rewind/lease变更拒绝 | 后端至多一次重做，前端两次立即重试后退避；delta无需静止 | 第3节V11 |
| V12 | R3.4：追加与覆盖间隔 | D机制，持续写入 | 普通append由D1当前完整tail补齐；无法证明连续须coverage_gap | 不靠去重猜覆盖，不为隐藏间隔全量下载 | 第3节V12 |
| V13 | R3.5：快照持久身份/活动租约 | D机制，active/idle/外部接管 | 持久代表以D1为准；退役UID不复活；未持久输出需当前Turn正式租约/起点 | active缺完整快照不能纯文字回退；外部owner无relay返回runtime_unavailable | 第3节V13 |
| V14 | R3.6：有限后缀与staging | D机制，ring/流式 | S至有限B逐序无缺口；B后接正常流；不得用latest跳帧 | epoch/runtime/seq排序去重；ring截断换完整快照；持续delta有限完成 | 第3节V14 |
| V15 | R3.7：锁序和等待边界 | D机制，性能/并发 | history→DB结束→replay结束→DB结束，无嵌套；history最多250ms | 不持锁网络/图片/投影/等待事件；真实独立conn/跨进程及计时证据 | 第3节V15 |
| V16 | R3.8：正式writer失效链 | D/N机制，rewind/edit/delete/compression | session.info/Framework/complete/sessions.changed均登记；同数替换不漏 | 列正式writer到广播路径；watcher含rewind签名；不靠任意mtime轮询历史 | 第3节V16 |
| V17 | R3尾段：控制与投影分离 | D机制，恢复中事件 | observeControl与reduceProjection独立seq；真实受理/撤销/通知观察不停 | 副作用不重复；held≤4096/8MiB，超限明确缺口换快照，不能丢帧ready | 第3节V17 |
| V18 | R4：视口/facet需求 | D机制，Timeline/Disclosure | 实际DOM首尾身份+offset；视口内展开source需求不依赖新projection发布 | 滚动展开收起离屏改变需求；staging详情无需先发布React | 第3节V18 |
| V19 | R4：cold/latest及深anchor | D行为，历史恢复 | cold仍latest200；暖anchor有界定位，不offset逐页追赶 | 无缓存不假空；超时不是已删除；只有真值缺anchor才刷新感 | 第3节V19 |
| V20 | R4：分页与本轮覆盖 | D机制，多页 | 稳定逻辑相邻选择；首最新页尾界冻结；loaded与validated分开 | Load earlier同helper；插删冲突整页重读；隐藏旧页不挡屏，进入屏局部校验 | 第3节V20 |
| V21 | R4/C06：对齐公共前缀 | D机制，交接 | 从同真实左边界比较身份、可见内容/状态/timestamp/facet | 起点不同不得直接index0比较；未展开正文不比较；仅局部结论 | 第3节V21 |
| V22 | R4：深anchor到tail间隔 | D行为，非邻窗 | 保留明确非message分页间隔；挂载中间未验证页先转间隔 | 不画假邻接/假正文；保anchor再动画；不强读全部历史；ready不等隐藏准备 | 第3节V22 |
| V23 | R5：统一入口/route404 | D接线，initialize/select/ready/online/visibility/Android | 同一startRecovery；初次失败不豁免；只读存在性校验先于resume | 已删locator退New Chat且删缓存；New Chat/Files不任意绑定runtime | 第3节V23 |
| V24 | R5：Profile/cwd/侧栏/标题 | D接线，多Profile | 每轮roster重读；New Chat cwd依赖；侧栏可见范围与标题本轮有效 | 隐藏页不阻塞；跨Profile独立结果；已加载可见旧页不被first-page删掉 | 第3节V24 |
| V25 | R5：Usage/Context/秘书/排期/压缩 | D接线，显示与展开 | 当前可见字段为需求，另视图/隐藏详情后台；共享响应不伪拆成功 | 每轮真实读；失败与unknown区分；模型失效正确；可见面板不遗漏 | 第3节V25 |
| V26 | R5：Pending/审批/受理 | D接线，业务安全 | 不缓存；恢复撤销失效动作；受理状态只读核实 | 不旧审批可操作、不重发；既有owner事务导航不改归属 | 第3节V26 |
| V27 | R5：Files重读 | D接线，root/list/preview | 固定owner，root/list及当前实际展示资源纳代次 | 文本取新文本、二进制实际重取；渲染失败明确失败；旧ObjectURL非成功 | 第3节V27 |
| V28 | R5尾段：登记表扩展契约 | D机制，新增reader | 资源均登记安排/必需/覆盖；初始重连与失效接线齐全 | 故意漏登记应观察未满足；allSettled不是ready证明 | 第3节V28 |
| V29 | R6：缓存身份/介质 | D约束，IDB | 独立secretary-display-v1；schema+canonical origin+profile+route；侧栏roster | 确认owner前只精确候选；不default猜owner；drafts库保持 | 第3节V29 |
| V30 | R6：缓存白名单/容量 | D约束，存储 | Timeline≤200已持久cards+可选额外窗；折叠正文/Blob/runtime等禁存 | 2MiB/16MiB/10会话/500侧栏1MiB/7天TTL/LRU；大正文跳窗不截断 | 第3节V30 |
| V31 | R6：缓存竞态/失败/失效 | D机制，IDB与认证 | 真值提交后迟到IDB不能覆盖；仅已成功对账展示写入，≤1次/秒idle | 配额/损坏降内存不阻网；404/owner删；rewind替窗不merge复活；认证停展示清document | 第3节V31 |
| V32 | R7：不可变单次交接 | D机制，visible/staged/RenderStore | Controller实时业务与visible/staged隔离；一次commitId不可变快照 | 无共享mutable binding泄漏；RenderStore仅合帧；即时错误安全状态覆盖 | 第3节V32 |
| V33 | R7：anchor/滚动动画 | D行为，恢复提交 | 同帧layout恢复offset、同Timeline/owner无remount；公共前缀约240ms至真实tail | following/ResizeObserver不抢位；delta继续、时长不续；输入即取消；降动效定位 | 第3节V33 |
| V34 | R7/§1.13：胶囊有效值动画 | D行为，Usage/Context | 比较实际显示规范签名；初次/同值/owner切换/视图切换不伪闪 | 120ms亮480ms淡600ms合并；独立selected/open、尺寸稳定、无Timeline滚动 | 第3节V34 |
| V35 | R8：桥身份和协议 | D机制，JS/Native | 可信origin主frame；hello不成功；document/nativeRecovery/recovery/demand匹配 | onPageStarted旧doc失效；recover调统一入口；health仅存活连接；无Android零行为 | 第3节V35 |
| V36 | R8：5秒与退避 | D机制，前台/network/watchdog | 真实回前台单调固定5秒，等hello也不续；同轮onResume/online合并 | 4.9ready+健康可取消；5秒先超时赢；connected不解除；10/15/20/30及新前台重置 | 第3节V36 |
| V37 | R8：冷启动/认证/附件/通知 | D约束，原生保护 | 首冷不额外刷新；无JS独立恢复；认证不注入/打断；Activity结果保护 | 通知目标跨reload保留，目标owner恢复回执才清；旧协议明确降级 | 第3节V37 |
| V38 | R10/C17：构建/证据边界 | D交付，Web与APK | Web实测+原生单测；实际APK用户豁免且未验，不能冒通过 | type/build与定向测试同候选；内置资源签名APK资源SHA匹配；不启动模拟器 | 第3节V38 |
| V39 | §1.3/§1.4：既有历史语义保留 | D约束，正式发送/选会话/投影 | 导航不新建/取消Turn；真实消息/UID/lineage；临时命令不持久 | owner不混，user committed不重复，thinking/tool/terminal真实状态，无合成历史 | 第3节V39 |
| V40 | §1.3/C02/C07：侧栏过渡 | D行为，多Profile | 列表快照原地更新、不清空/闪烁；首次请求前不假空 | 不缓存running等实时事实；分组/Pin/现视觉保留；不批量正文/activate | 第3节V40 |
| V41 | §1.13：统计保留语义 | D行为，Usage/Context | 同owner/视图新有效值才覆盖，零有效；Latest completed；缺字段不清可信旧值 | 无本地推算新token/比例；不兼容model/provider/rewind失效；冷估计不因append/compact误废 | 第3节V41 |
| V42 | 08 §1/§3/C11：Profile/Files隔离 | D约束，所有owner操作 | Profile仅New Chat选择；既有Conversation不可迁移；Files固定配置集中 | root/list/预览/下载一致固定Profile；不污染cwd/附件/config；Back恢复原身份 | 第3节V42 |
| V43 | R9/C12–C16：实施与验证约束 | D流程，整轮 | 全6.1、不派生、主会话review；仅隔离本地无真实模型/生产；保留他人dirty | 证据路径匹配候选；冻结检查不放宽；commit/push结果准确；UI只隐藏自建IAB | 第3节V43 |
| V44 | R10：关键矩阵覆盖 | D证据，全范围 | 原子cut、真实跨连接/进程writer、持续delta/新Turn/lease、深anchor及失败须各有证据 | 用真实适用机制证据，不用mock/helper/字符串替正式接线；缺必要证据阻断 | 第3节V44 |

## 3. 逐条实现证据

路径以主仓根为默认；`web:` 指 `/Users/edgar/code/hermes-secretary-web/`。E=`.hermes-dev/web-recovery-20261024/`。本节每行承接第2节同号原文及独立不变量，构成原文→判据→路径→条件→方法→观察→判定链。`F`=E/frontend/review-final-tests.log（12文件223项）；`B`=E/backend/rev10-final-tests.log（39项）；`P`=E/presentation/frontend-final.log（96项原包，受影响阅读/胶囊由后续证据覆盖）；`A`=E/presentation/android-final.log及三个XML（40项）；`N`=E/verification-v2/menu-overlap.log。指纹核对及复用边界见第4节，计数不相加。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| V01 | web:Controller.startRecovery→ControllerPageRecovery.installResources/readCache/commit→DisplayCache.displayRows/displayCapsules | 亲读全持久化白名单、恢复每轮读和投影；F缓存有/无均完整请求、临时/运行态剔除 | web:controller-page-recovery.ts:202–239/309–391/577–597；display-cache.ts:4–126；F | 符合；缓存仅展示，没有持久游标、Notebook、审批或写重放 | 既有drafts另库保持；不把胶囊估计当runtime |
| V02 | Controller唯一pageRecoveryOwner→PageRecovery.owner/context/resourceKey/connection/cancel | 亲读document/connection/recovery/demand代次、canonical owner及Files资源key；F跨owner/迟到URL/A→B→A反例 | web:controller.ts:172–175；page-recovery.ts:17–155；Files.tsx:163–222；F | 符合此项身份结构；owner过时不得commit，delta不增代次 | 同owner配置后继事件失效遗漏由V03/V28单列N01 |
| V03 | PageRecovery.read/results→requirements；UsageViews.readResult→usage adapter；menuStages→commit | 空/zero/unknown/404/cancelled/503正式Controller用例已核；独立N反证菜单旧成功未失效而覆盖新值 | web:page-recovery.ts:142–186；usage-view.ts:71–129；controller-page-recovery.ts:159–165/329–345/519–524/577–582；F、N | **违规N01**；结果类型存在，但已知过时配置结果仍保ok及commit资格 | Session补读失败原缺陷已修；不是把合法unknown当失败 |
| V04 | PageRecovery.startRecovery/run/scheduleRetry/readLocalRequirements；adapter lifecycle | F验证cold失败无gateway事件自动重试，local失败1/2/5、撤需求、隐藏/离线与同连接dirty；源码核owner/epoch取消 | web:page-recovery.ts:112–250；controller-page-recovery.ts:107–119/159–178；F | 符合；前台失败可重试、隐藏/断网不继续定时、触发合并不反复abort | N01为配置失效资源集合遗漏，不是否存在重试机制 |
| V05 | PageRecovery.run→commit→Chat/Files/New Chat layout ack→ready；backgroundSettled独立 | F正式App6场景及Files layout、慢隐藏需求；N中旧配置回盖后ready=true | web:page-recovery.ts:185–211；App.tsx:687/705–707；chat-presentation.tsx:239–300；Files.tsx:224–236；F、P、N | **违规N01**；基础屏与anchor就绪机制成立，但可见菜单已知过时仍宣布ready | 不要求等240ms动画结束；真实Web用户效果交Validation |
| V06 | GET /api/sessions/{id}/messages recovery分支→_get_recovery_messages→selector/read_view | 核任意UID/row anchor、200/500、offset/order/detail冲突400及旧分支；真实REST8用例 | hermes_cli/web_routers/sessions.py:791–895；hermes_state_recovery_view.py:25–48；E/backend/recovery-final.log | 符合；可选参数兼容、每次完整cards且只当前选中Conversation | 旧offset仍旧客户端使用；无新增DB schema |
| V07 | read_view._read_window→project_view→digest；HistoryWindows.accept/replace | 核真实逻辑界/前后邻居、cards SHA256、独立detail_digest；真实DTO两仓一致，F owner/receipt非法拒绝 | hermes_state_recovery_view.py:126–277；web:history-coverage.ts:12–64；B、F | 符合；范围及展示摘要来源于本轮真实读，非缓存自行确认 | coverage只内存；临时媒体URL不作为同步游标 |
| V08 | resume/live payload宣告→attachConversation→readConversation→activate.parse_request/activate_payload | 核宣告v1才新参数、REST receipt、2窗/500及12详情；matched重读/整窗替换；legacy明确一致恢复不可用 | tui_gateway/methods_session.py:694/867；server.py:3047；recovery_view.py:21–50/319–387；web:controller-page-recovery.ts:410–470；B、F | 符合；老后端降级没有伪称v1 ready，新封套不负责额外runtime创建 | first attach仍只选中Conversation，不批量绑定 |
| V09 | session.events.since→event_replay.read_replay_cut | 源码核同锁复制events/latest/truncated/epoch且锁外解码；真实并发stamp负对照测试 | tui_gateway/event_replay.py:133–145；methods_session.py:2190附近；E/backend/targeted-tests.log，test_tui_gateway_event_replay.py新增并发用例 | 符合；不存在数组旧cut配新水位 | open_requests仍独立request snapshot，不宣称DB共事务 |
| V10 | read_view→hermes_state_timeline._snapshot→_lineage/_display_sql/_read_window/_details | 核一个conn BEGIN/ROLLBACK、SQL代表与UID退役、branch排除；真实深1400行仅5payload，latest200，第二conn期间快照不变 | hermes_state_recovery_view.py:52–235；hermes_state_timeline.py:40–49；tests/hermes_cli/test_recovery_view.py；E/backend/recovery-final.log | 符合；无串新conn、GET写索引或Python全正文物化 | 旧缺display_identity可在SQLite算身份；身份扫描非全部正文下载 |
| V11 | session.activate→activate attach→_capture D0/S/D1→_same_history→activate_payload重试 | B真实独立进程正式replace/rewind/compression/delete；同数改写、重复破坏两次有限失败；前端3次尝试即两次立即重试 | tui_gateway/recovery_view.py:107–185/319–387；web:controller-page-recovery.ts:426–455；B | 符合；证明实际区间而非两个Promise，不等待Turn静止 | 持续破坏改写可明确失败，不能保证5秒成功 |
| V12 | _capture D1最新页＋proofs→_coverage→整窗响应；HistoryWindows gap | B独立conn append、超窗append gap；深anchor/tail相隔1100行有界；F gap与邻接 | tui_gateway/recovery_view.py:137–150/288–298；tests/tui_gateway/test_recovery_view.py:97–115/403–414/451–463；F、B | 符合；普通尾追加由D1补齐，不连续明确coverage_gap，不假装读全间隔 | 未展示间隔本来不要求无缝正文 |
| V13 | _turn_context/_native_source/_turn_proof/_prove_source→_clean_snapshot→D1身份 | B核当前agent/Turn token/lease、跨Profile同ID、非user source、rewind/retire、换Turn/lease、tool occurrence；真实native SSE活动恢复及结束idle证据 | tui_gateway/recovery_view.py:85–105/176–286；B；E/backend/rev10-native-stream-probe.json、rev10-settled-proof.json | 符合；普通Web原生source与Reminder source分支有正式证明；缺完整snapshot/外部relay明确拒绝 | loopback合成SSE，外部模型0；无relay时正确拒绝，不声称外部owner完整成功 |
| V14 | snapshot S→read_replay_cut B→Controller.installCut→suffix/held→正常event | B持续真实stamp线程仍running时有限complete，ring换完整snapshot、新epoch拒绝；F suffix/held逐序与重复 | tui_gateway/recovery_view.py:301–317；web:controller-page-recovery.ts:491–517；test_recovery_view.py:191–209/465–502；F、B | 符合；逐seq证明至有限B，未凭latest跳帧，后继流不每delta读REST | 真缺口可失败；不是以ring替完整当前Turn快照 |
| V15 | activate attach锁后_capture history锁250ms→D0释放→S释放→D1释放→project_view | B实锁检查投影时history/replay/global resume/DB事务均释放；锁超时；真实独立进程writer；一次DB36.8ms投影117.6ms | tui_gateway/recovery_view.py:107–165/301–307/359–387；test_recovery_view.py:211/416–441；E/backend/read-timing.json，B | 符合；没有DB/replay嵌套和投影长持锁，不以等待模型完成收敛 | 单次本机计时是边界证据，非性能SLA |
| V16 | 正式writer→通知/Session签名→change_watcher sessions.changed→Controller.start | 核rewind计数、replace/set_user及secretary_set_user_content成功通知、delete行集合、compression/Framework/complete；通知真实db_path、跨进程与失败不阻写测试 | hermes_state_messages.py:844–871/1824–1851；hermes_state_secretary_foreground.py:220–243；history_notifications.py；change_watcher.py:129/203–208；web:controller-event-effects.ts；E/backend/targeted-tests.log、B | 符合；同数改写有失效入口，当前会话合并重读，不扫其他正文 | best-effort通知不是revision证明；直接SQL非正式写接口 |
| V17 | Controller.event→observeControl→held→reduceProjection；adapter.observeControl/holdSize/installCut | 源码核双游标与4096/8MiB；F request.cancel即时撤、有限suffix重复去重及overflow拒绝；提交受理/通知观察未暂停 | web:controller.ts:1150–1230；controller-page-recovery.ts:133–158/491–517；F、E/frontend/accepted-tests.log | 符合；业务观察前进不跳staging帧，超限不丢帧ready | 后继session.info配置失效另列N01；不把控制观察等同投影已应用 |
| V18 | actual App useTimelineReading→reportDemand visible aliases/facets→readFacets staging | 核DOM实际首尾及offset、展开source identities；P视口/tool-only/离屏用例及F正式App；details12一批不等React发布 | web:chat-presentation.tsx:90–200/309–330；controller-page-recovery.ts:367–408；P、F | 符合；展开/收起/滚动需求独立于新projection发布，不制造effect死锁 | 已展开但离屏可后台，进入视口才需本轮验证 |
| V19 | readWindows latest200→anchorSelector→任意anchor GET | 核warm直接anchor不用offset追赶；cold缓存/空仍真实latest；404 anchor_not_found才anchorMissing | web:controller-page-recovery.ts:478–490；history-coverage.ts:65–73；F、E/backend/recovery-final.log | 符合；超时/未知不等于anchor删除，无缓存不假空 | 旧未验证alias保持未知而不伪造前缀破坏 |
| V20 | HistoryWindows loaded/verified/invalidate/view→loadEarlier anchor helper | 核稳定页尾/邻接与重叠冲突、1000旧行后台恢复不挡屏、滚入新需求局部读；F coverage/page-key用例 | web:history-coverage.ts:12–64；controller-page-recovery.ts:207–210/375–386/599–629；F、E/frontend/review-fixes.log | 符合；新恢复不拼新旧offset，加载过与本轮验证分开 | 冲突发当前owner完整窗口恢复，不接收旧页覆盖 |
| V21 | visibleWindowCompatibility→sourceTimeline/combineToolCards→shared signature | 核真实左边界、kind/UID/tool occurrence、timestamp/可见facet签名；F重排A/B→B/A拒绝、同UID thinking/message不混、append相容 | web:history-coverage.ts:94–124；components/presentation-signature.ts；F | 符合；有序局部前缀，缺失/歧义身份不借空集证明 | 不宣称整个Conversation前缀已验证；未展开正文不参与 |
| V22 | HistoryWindows.view.gaps→App gap按钮→reading handoff | F深anchor+tail显式非message gap；核只保本轮验证窗，中间未知页不假正文，保anchor DOM再滚 | web:history-coverage.ts:37–62；controller-page-recovery.ts:450–462；App.tsx:141–144；F、B | 符合；无需为动画下载全部历史，正常相邻不添gap | 实际滚动视觉交Validation；机制不伪造持久消息 |
| V23 | initialize/select/gateway.ready/online/visibility/Native→startRecovery | F formal Controller cold/reconnect/runtime reclaimed/404；亲读先REST metadata再resume，Files/New Chat afterBinding无任意runtime | web:controller.ts:488–525/706–772/1341；controller-page-recovery.ts:107–120/410–425；F | 符合；初始化失败仍重试，已删路由退New Chat清缓存且无resume | 不自动重放发送/编辑/审批 |
| V24 | installResources.roster/sessions/defaultCwd→SessionList.refresh→metadata title protection | 每轮roster；多owner并发独立保页，strict错误；New Chat cwd；current title revision防旧回盖；F SessionList旧页重读 | web:controller-page-recovery.ts:252–278/309–325/346–353/471–476；session-list.ts:15–77；F、E/frontend/accepted-tests.log | 符合；可见侧栏已加载范围不被first page截掉；隐藏请求不阻可见 | 不逐会话正文/激活；无关cwd不挡已有Conversation |
| V25 | installResources usage/pending/secretary/schedules/compaction→领域reader | 核UsageReadFacts必需scope、context_unknown与失败区分、秘书/排期共享响应、staging详情；F相关失败/隐藏/零未知，原生数据保持 | web:controller-page-recovery.ts:326–367；usage-view.ts:71–129；controller.ts:1806–1857/1896–1923；F | 符合此项统计/秘书/排期/压缩数据覆盖；缺失不伪造成功 | 实际配置菜单后继失效缺陷单列V28；不拿此结论代所有resource完整 |
| V26 | retain清请求/Pending→ServerRequests request snapshot→readPending→owned业务事务 | 核恢复中旧审批不可操作、request.cancel即时撤；F通知目标/受理/cancel；旧编辑/发送相关回归 | web:controller-page-recovery.ts:202–220/510–514；controller.ts:1963–2020；server-requests.ts；F、E/frontend/accepted-tests.log | 符合；不从缓存造审批/Pending，导航不迁已受理owner，未增写重放 | 原生控制RPC保持；不是以旧缓存提供授权 |
| V27 | App Files→files-current read root/list/read-text/authorizedFile→staged renderer→layout ack | P正式组件每轮固定Profile读root/list、当前文本/媒体文件；renderer失败拒ready，换path取消旧stage | web:Files.tsx:46–76/159–236；FileViewerPreview.tsx recovery回调；E/presentation/frontend-final.log | 符合；旧ObjectURL不作新读、真实renderer成功才accept | 第三方渲染依赖边界受控；真实媒体用户效果交Validation |
| V28 | recovery-resources→Controller installResources→App配置/侧栏/胶囊/Timeline/Files demands | 核初始/重连登记、漏Files reader负对照阻断；新增Model/Thinking实际App登记已补；但N证明session.info后资源未失效 | web:recovery-resources.ts；controller-page-recovery.ts:159–165/309–391；App.tsx:443–450；F、N | **违规N01**；当前可见菜单的已知配置失效没有进入其reader代次/暂存资格，登记不等于完整恢复 | 初始与普通online/menu开关路径已修，不据此掩盖后继事件 |
| V29 | DisplayCache.keyFor/sidebarKey/sidebarCandidate→readCache exact owner | 核独立DB/schema/canonical scheme-host-port；profile+stored route、明确roster；F跨origin/profile/late IDB；drafts无变更 | web:display-cache.ts:4–16/127–150/192–217；controller-page-recovery.ts:223–246；F | 符合；未确认owner不借default，WebView正式HTTPS origin不是本地文件path | 缓存不绕认证；Profile候选只限明确URL身份 |
| V30 | displayRows/displayMetadata/displayCapsules/displaySidebar→queue/flush | F持久tool/Thinking折叠正文及binary/Blob/runtime过滤、oversize跳窗口；200/2MiB/16MiB/10/500/1MiB/7天/LRU源码核 | web:display-cache.ts:4–126/159–171/196–253；F | 符合；不截断正文伪完整，工具外侧与已持久terminal projection字段按白名单 | 保存真实历史终态展示不是恢复运行态；无认证token/附件二进制 |
| V31 | readCache current→commit/ready cache；observeUsage/observeContext→acknowledgeDisplay→白名单merge | F真值先到后IDB不盖；普通成功usage/context更新入cache、失败retained不续TTL、late foreign owner/认证清理；损坏/quota降级 | web:controller-page-recovery.ts:223–251/541–597；display-cache.ts:159–253；F | 符合；本轮已成功展示后缓存，404删、rewind替窗、不merge旧消息 | 旧V02完成该路径修复；缓存写不参与ready与原生5秒 |
| V32 | present/cloneDisplay/retain→menuStages→commit→RenderStore | F可变business binding不泄露已发布view、REST/WS两顺序保旧统一commit；N证明commit重新套旧menuStages | web:controller-page-recovery.ts:41–46/179–220/519–524/577–597；render-store.ts；F、N | **违规N01**；数据深拷贝与单提交存在，但旧暂存已知失效后仍覆盖新business配置，不满足连贯交接 | 非要求所有独立资源同一物理瞬间；要求不能回盖已知更新 |
| V33 | actual Timeline reading owner→anchor layout→handoff240ms→input cancel/Mutation/ResizeObserver | 当前hook阅读43项+F正式App6项核cold/cache/warm local motion/输入；源码核晚子树children、动态tail和不续期、reduced定位 | web:chat-presentation.tsx:155–330；E/presentation/cold-handoff-fix-final.log、F | 符合；旧V04停窗口起点原因已修，同recovery local不夺motion/following，后续DOM可落tail | jsdom真实组件，几何受控；独立浏览器画面验收仍待Validation |
| V34 | App实际规范displaySignature/hasData→useValueUpdateHighlight→theme.css | F及当前胶囊测试核首次无数据、合法unknown/zero、同值、切owner/view/open、600ms burst、reduced；源码120+480及尺寸样式保持 | web:App.tsx:380–415；design/indicators.tsx:16–33/90–97/121–127；theme.css:649–658；F | 符合；实际值变化才闪，选中/展开状态与动画独立，不引Timeline滚动 | 手动view切换建新基线，不把observed_at或对象引用当变化 |
| V35 | Android JS hello/recover/state/health→MainActivity可信bridge→ForegroundRefresh | A和JS桥测试核文档/native/recovery/demand匹配、旧包/iframe普通网页零行为，hello不等于ready；源码主frame+origin保护 | web:api/android-health.ts；AndroidBridgeState.kt:9–113；MainActivity.kt:85–95/130–134；A、E/presentation/frontend-final.log | 符合；health只连接/存活，新协议ready来自协调器layout | 不代表真实WebView运行验收；C17未验 |
| V36 | ForegroundRefresh.stopped/resumed/startRecovery/recoveryState/reload/checkHealth | A核4.9秒ready、5秒connected不解除、deadline先到优先、online/resume合并、无JS、10/15/20/30、新前台重置 | web:ForegroundRefresh.kt:42–137/192–217；A三个XML | 符合；单调固定5秒，不因hello/owner延长，reload后每文档须恢复 | Robolectric API35，无实际设备/系统挂起保证 |
| V37 | ForegroundRefresh.pageStarted/external/ActivityResults→MainActivity NavigationMailbox→target ack | A冷启动无额外reload、认证恢复、ActivityResultRegistry URI、相机/文件保护、通知target跨reload；F目标owner layout后确认 | web:ForegroundRefresh.kt:42–81/141–182；AndroidBridgeState.kt:130–150；MainActivity.kt；A、F | 符合；认证不注入/打断，附件返回保护，通知不因当前别的页ready先清 | JS/native旧版明确降级日志；实际认证/设备流程按C17未验 |
| V38 | npm build→npm android:build→签名release APK→439资源核验 | 独立核APK bytes/SHA与manifest相同；已签v2证书有效，前端474a934绑定；A指纹匹配；F/build日志有效 | E/apk-final-manifest.json、apk-final-signature.log、android-build-final.log；E/verification-v2/version-audit.json；E/frontend/review-final-build.log | 符合Verification阶段的构建/机制证据要求；C17实际APK运行有依据豁免/未验 | Web实际验收仍是后续独立Validation，当前门禁失败尚不能交付或部署 |
| V39 | Controller.select/ensureBinding/submit既有事务→sourceTimeline/reconcileLiveHistory→真实消息身份 | 亲读恢复差异不改写消息/UID/持久lineage；F原state/mobile/presentation及user committed/工具/终态回归 | web:controller.ts:706–779/1000–1060/1150–1230；session-recovery.ts；projection.ts；F、E/frontend/accepted-tests.log；B | 符合；导航不新建Turn或取消他处Turn；临时命令仅内存无cache | 外部模型未调用；无合成历史的新分支 |
| V40 | retained sidebar cache→SessionList.refresh→App分组/Pin原组件 | F exact-owner cache先roster、侧栏旧页重读、读侧runtime字段过滤；核没有清空列表与改Pin/分组设计 | web:controller-page-recovery.ts:229–236/312–325；session-list.ts；display-cache.ts:123–126；App侧栏既有组件；F、P | 符合；首次未完成不假空，摘要不提供Turn/管理操作真值 | UI视觉保持的源码证据；实际不闪与原地效果交Validation |
| V41 | UsageViews/usage-counters→App Usage/Context规范值→cache compatibleCapsules | F旧usage source/view与app capsules用例；核字段零/未知保留、Latest completed、model/rewind失效和cold native estimate；本次不增本地token统计 | web:usage-view.ts:30–129；usage-counters.ts；display-cache.ts:111–119；App.tsx:380–415；F | 符合；失败不清旧可信值也不当新事实，不从cache推新百分比 | Context真实统计仍来自原生现有接口；不新增专用API |
| V42 | ProfileEnvironment/New Chat选择→Controller.select/openConversation→filesNavigationState/FILES_PROFILE | 核Profile只New Chat，原Conversation不可迁；固定default集中、root/list/preview/download同owner；Files返回完整chat owner | web:profiles.ts:85–93；core/files.ts；Files.tsx:36–76/163–223；controller.ts:706–779；E/presentation/frontend-final.log、F | 符合；固定Files不污染新会话cwd/附件/config，固定不可用真实错误不fallback | 不扩跨Profile Agent读取权限或Workspace产品 |
| V43 | R9分包sibling/两仓candidate diff/主会话review/冻结检查 | 核源码范围、facade controller2556→2501、后端15文件health0/0；十检查原规则通过；本审查无UI/模型/生产/提交 | E/review-staged-ten-checks.log；reports三包；两仓git diff冻结→候选；本审查version-audit | 符合；未借证据复用放宽规则，C17唯一验收范围变化 | push核同沿主会话已有记录；本审查不网络重复核远端 |
| V44 | R10矩阵→B/F/P/A测试底座＋native SSE＋本次N反证 | 核每类竞态确实走正式handler/Controller，真实DB跨进程/独立conn、持续delta/lease/新Turn、深窗、Files/failed与动画均有适用证据 | 第4节证据目录；tests/tui_gateway/test_recovery_view.py:97–524；F；E/backend/rev10-native-stream-probe.json；N | 符合审查方法与范围覆盖；反证能暴露现有绿测漏掉N01，不以实现者自评作通过 | 结果包括失败而非宣称全通过；真实Web结果仍待Validation，APK用户豁免 |

## 4. 核心目标及验证方法审查

**覆盖及结论：44项逐条覆盖，40符合、4违规（V03/V05/V28/V32），0证据不足，0整项不适用。四条违规对应同一范围内新阻断N01，不能进入Validation。** V38中的实际APK运行子场景按C17有依据豁免且未验，R8与构建资源要求仍核；不得把这个子场景豁免误计为整个原生条款通过实机。

核心纵向路径已落实：页面统一入口→真实roster/metadata→本轮REST有界窗口→能力协商activate封套D0/S/D1→有限S/B及held后缀→独立staging→可见commit→React anchor/Files layout→ready。它没有退化成“REST与WS各等一次”，也不要求事件静止或Turn结束。恢复缓存只撑展示，页面需求而非全历史决定阻塞；读取失败与合法unknown有区分。当前缺口集中在同owner恢复中的**后继配置事件**：菜单资源已经成功暂存后发生session.info，history等资源失效却不失效capabilities/reasoning；旧menuStages context仍current，统一commit反而把已读到的新菜单覆盖。这是正式数据流/失效接线问题，不是只缺一个测试，也不是规格缺少函数名。

证据版本审查：

- `E/verification-v2/version-audit.json`独立核主仓dd9a4c5、Web474a934。frontend最新post-verification的23项及source-manifest26项全部匹配；REV-10 manifest产品/测试/原生依赖全部匹配，只有动态plan文字变化。早期presentation总manifest与cold-handoff manifest包含历史revision，列出差异后按变更影响复用：原生Kotlin/JS桥、Files/renderer未变；chat-presentation及胶囊改动以当前hook/indicator指纹和最新F223/阅读43定向证据覆盖，不拿旧96项冒充新全量。早期page-recovery两项差异也由当前F覆盖。
- `F`为当前12文件223项，`review-final-build.log`含tsc与Vite成功，已核失败预期来源于冻结契约；正式App联合测试实际使用App＋Controller＋PageRecovery＋reading，非只测孤立hook。DOM几何与RPC/renderer依赖受控，未替换协调器或投影；它不能证明真实浏览器视觉，因此后续Validation仍必需。
- 后端当前B39包含真实SQLite、独立进程正式replace/rewind/compression/delete、独立连接append、持续真实native stamp与有限suffix、ring截断、新epoch、lease/Turn切换和普通Web source负例。受控snapshot回调只选择并发时点，writer及DB事实真实。既有其他源码未变，可复用`targeted-tests.log`的replay17/watcher2/cards46/timeline6/通知4/生成一致1及对应正式接线；不重叠累加。`rev10-native-regression.log`的35项覆盖既有终态和inflight路径。
- `rev10-native-stream-probe.json`及`rev10-settled-proof.json`是正式Dashboard WS/REST＋native Turn＋真实SQLite，唯一loopback SSE请求，running恢复complete、同runtime、正文精确、唯一assistant落库、结束idle无未持久尾巴。审查读取其harness代码/拒绝边界及manifest：仅本轮合成模型、特定标记、固定loopback地址、0外部模型调用；该证据补普通Web活动来源，不冒称真实供应商或Web用户结果。
- A40的三个Robolectric类对应当前Kotlin源码，覆盖5秒身份/退避/无JS、ActivityResults及通知邮箱。实际APK按C17未运行。独立核当前APK32,081,185字节、SHA256 `9e2339c0e840381ee3da862894b404b9464e61be1fa336a99c63bb370a5304f5` 与manifest一致；签名v2有效，439资源逐字节核验有当前构建记录，绑定Web474a934。
- 本审查没有复跑上述有效大套。仅为新反证建立`menu-overlap.test.ts`。原活动源码尚等于候选时先复现；尾段复核发现主会话已修改工作树，立即将固定474a934源码git archive展开到本证据目录，使用当前projection游标下一序号再次复现同一失败。中间工作树试跑不用于原候选结论；前两次证据目录依赖解析失败无测试运行，不计通过。`counterexample-version.json`核四个关键被测归档源码与固定候选SHA一致，避免把后续修复混入审查。旧测试同时绿的错误实现仍能通过，原因是只测菜单打开、普通online、失败和隐藏撤除，没有在同轮已暂存后插入后继session.info。

未做UI、外部模型、生产、设备/模拟器、提交或部署。没有把主会话自评当独立判据。必要真浏览器用户结果属于下一门禁，不以本报告代签。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| N01 / P1 | V03/V05/V28/V32；06 R1/R5/R7；web:controller-page-recovery.ts:159–165/329–345/519–524/577–582 | Model菜单打开；恢复时capabilities旧结果先暂存，Pending延迟；期间正式session.info把model改为fresh-model且旁路capabilitiesForBinding已成功取得fresh；该事件只invalidate conversation/usage/pending/secretary/schedules/compaction/facets/sessions，未使capabilities/reasoning旧context失资格；释放Pending后commit重新套old。N观测ready=true、binding.model=fresh-model、可见providers[0].slug=old，fresh断言失败 | 当前可见配置与已确认后继事实不相容仍ready，用户可见菜单被倒退，APK可收到假成功。不是全局物理瞬间一致性要求，而是明确新事实被已知过时结果回盖 | 主会话提案使session.info当前owner受影响capabilities/reasoning及menuStage同代失效；验证Pending延迟期间Model/Thinking变化、旧响应迟到、失败重试、关闭/切owner不泄漏，核旁路serial/stage；新候选全新独立全范围复审 | **未关闭；阻断进入Validation** |

N01完整安全复现：E/verification-v2/menu-overlap.test.ts、menu-overlap.log、counterexample-version.json。只使用隔离fixture与真实后端DTO，事件进正式Controller.event；控制依赖返回时序，不改产品。先明确观察business models为fresh，再释放Pending，最终old，不把“新读未完成”误报成bug。

范围外历史项：旧wire catalog孤立`review.summary`失败有冻结树正式runner复现（E/backend/frozen-catalog.log），非本轮新增，不放宽门禁或宣称全仓全绿。旧README/CLAUDE混用“当前已发布”和“整体集成未完成”的动态措辞仅由主会话在最终交付同步；本审查不扩改其它文档。

## 6. 修复与独立复审

这是全新gpt-6.1-sol独立全轮复审；先仅冻结规格建立44项第2节并向主会话完整交回，之后才读指导、实现和旧报告。旧六节保持完整，未以本次结论覆盖旧候选失败历史。未发生退回补审。待审对象始终dd9a4c5／474a934；后续工作树或修复版不属于本次通过对象。

| 研讨/复审项 | 原判据与发现 | 主会话提案及理由 | Verification评审/是否改规格 | 实现版本与关闭证据 |
|---|---|---|---|---|
| 旧V01 | 当前Session补读503被fulfilled/retained当ok | UsageReadFacts分detail/session、当前scope失败阻断，Latest隐藏scope不挡 | 核当前reader正式接线与F定向失败→1秒自动恢复、合法unknown。原缺陷关闭；不代表N01旧菜单也正确失效；**未改规格** | 474a934；controller-page-recovery.test.ts:184–205；F |
| 旧V02 | 正常Usage/Context成功展示未写cache | 同owner成功事实，经展示资格确认白名单合并，保已验证Timeline；失败不续TTL | 核observeUsage/observeContext/acknowledgeDisplay与F正常更新、TTL、外owner、local commit交错；原缺陷关闭；**未改规格** | 474a934；controller-page-recovery.test.ts:207–235/254；F |
| 旧V03 | 实际Model/Thinking未登记、独立effect吞错 | 受控open登记唯一协调reader，菜单字段stage，关闭释放依赖 | 实际App6项及formal Controller证明原始打开/online/失败路径已修；原缺陷关闭，但全范围新增N01证明后继事件失效仍缺；**未改规格** | 474a934；App.tsx:443–450；app-page-recovery.test.tsx:133–181；F |
| 旧V04 / REV-09 | 冷开晚DOM挂载/局部commit取消滚尾 | 同recovery local保motion与following，观察childList/characterData，cold无阅读位置先定位 | 亲读当前hook及当前F正式App cold/cache/warm+manual反例；当前hook43项可复用，修复影响覆盖，原缺陷关闭；真实用户画面仍交Validation；**未改规格** | 474a934；chat-presentation.tsx:239–330；F及cold-handoff-fix-final.log |
| REV-10 | 普通Web活动Turn只具原生_terminal_source，旧封套仅认Reminder source事件 | 受控history capture取当前agent/Turn token/lease，验证真实DB/source row/UID/lineage与D1 | 亲读_native_source与_turn_proof及39项负例；原生loopback SSE running恢复与idle收敛有效，关闭该机制缺口；**未改规格** | dd9a4c5；B及rev10-native-stream-probe.json、rev10-settled-proof.json |
| 新N01 | 恢复已stage旧菜单后session.info变化，新business菜单成功却被旧stage回盖 | 主会话亲读反证后接受；提案把capabilities/reasoning纳当前owner session.info失效集合，使menuStage旧context立即失资格；required重取fresh后统一commit，核本地写和held event及旁路串号，不每delta重读 | 依据既有R1过时资格、R5当前展示读取及R7统一交接认可方向；需上节反例与失败/迟到关闭证据；不参与迁就实现的判据改写；**未改规格** | 原候选N失败，**未关闭**。主会话将另安排修复及全新独立全范围复审 |
| C17 | R10原有实际APK生命周期 | 用户唯一冻结后变更豁免本轮实际APK验收，保Web实测/原生单测/构建签名资源 | 仅子场景豁免/未验，不降低R8，不启动模拟器；原始判据保留变更依据 | snapshot-index末尾C17；当前APK资源/SHA/签名证据有效 |

供final-delivery及用户汇报摘要：旧四项与REV-10的修复在当前候选有机制证据；新N01是独立全范围复审发现的配置后继事件与暂存资格遗漏，主会话已接受并提出既有授权内方案，未改冻结产品定义。**最终门禁不通过；44项40符合/4违规，范围内N01未关闭，不能进入Validation或宣称本轮完成。**

---

# Verification v3：20261024-web-recovery

## 1. 审查对象与结论概览

独立新审查者：verification_v3（gpt-6.1-sol/high，不派生）。判据建立于2026-10-24；先完整阅读autonomous-run及spec-implementation-review，仅阅读冻结原文、索引的规格定位与当前C17后建立本节和第2节；未提前读取实现、测试、旧审查或动态看板。主仓候选`aed15db4d7175fdbf4b1ba6a4dece351255ce6cc`；Web候选`833d456e8c8a71f0388e902ac19dda7e5586eda8`。冻结依据：主仓`ba83d2b430e3448461dd7feb9f1acd8fc94c6cc9`的06 §0.4、§1.2现行替代、§1.3、§1.4（R1–R10）、§1.13；08仅Profile与Files保持条款；同版本snapshot-index C01–C16。当前索引C17唯一新增完成条件：实际APK运行验收用户豁免，须明确未验；R8机制、原生单测及APK构建签名资源匹配不豁免。报告仅追加，历史v1/v2不改写。基线与其它指导将在判据落盘后读取。

进入条件：集成候选冻结，产品只读；不操作UI、真实模型、生产、设备或提交。总体结论：全范围审查完成，门禁不通过。41条中36符合、5违规，对应N02/N03/N04三项范围内阻断；不进入Validation。

## 2. 独立要求清单与覆盖

本表为先于实现调查的独立起点。类型中的“直接”是冻结原文直接要求，“推导”是保证该要求不可绕过的必要条件；具体命名仅在规格已指定时引用。当前无未决产品解释；工程细节薄弱处均保留为必须从正式路径证明的对象，不因函数名缺失而豁免。后续修改须保留本版及规格理由。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| V3-01 | 06 §0.4、§1.4目标；C01/09/10 | 直接；架构、全部页 | 服务端权威；展示缓存不是响应镜像、可写历史、事件库或同步引擎，不重放写操作 | 仅限定展示快照；runtime/游标/运行事实不持久化；无新BFF/DB schema/全库扫描 | §3同编号 |
| V3-02 | 06 §1.2现行替代、§1.3；08 §1/§3；C11 | 直接；导航与owner | 三屏及原生浏览历史、Files返回身份保持；Profile只在New Chat选择；已有Conversation不改归属；冷恢复校验存在与权限 | 打开/返回/刷新/深链保留真实Profile与locator、草稿；不因导航新建/打断Turn，不以固定Files owner污染聊天 | §3同编号 |
| V3-03 | 06 §1.3、§1.4；C02 | 直接；历史/侧栏 | 只读当前Conversation所需分页，不读取其它正文或批量runtime；新聊天首发才恰好创建一次 | 正式入口有有界读取与只读存在校验；保留压缩连续性、分支边界、旧cwd可发现、真实列表事实 | §3同编号 |
| V3-04 | 06 §1.3侧栏、R5/R6；C05/07 | 直接；全部Profile侧栏 | 冷开先缓存、结果原地更新，未完成不冒充空；owner页独立保留；当前标题不能被旧列表回滚 | 可见已加载页完整登记；隐侧栏后台；不单首屏删掉屏内旧页；保留分组/Pin/拖动视觉 | §3同编号 |
| V3-05 | 06 §1.4统一交接；R1/R7；C03/04 | 直接；全部恢复入口；接线细节重点 | 唯一恢复owner；读本轮可见依赖且历史/事件证明完成后一次不可变commit；不等Turn结束/所有后台 | initialize/select/gateway.ready/online/visibility/Android同入口，缓存/connected/Promise fulfilled不能ready | §3同编号 |
| V3-06 | R1 owner/代次 | 直接；跨owner、连接、文档 | serverOrigin/profile/screen/storedId、document/connection/epoch/recovery/demand各有规定寿命；同epoch新连接仍不同 | 过时结果无提交资格；取消/owner切换不转移后台受理事务；normal delta不重开整页恢复 | §3同编号 |
| V3-07 | R1结果/失败/重试；C05 | 直接；失败与合法空 | ReadResult明确owner/recovery/request/status；retained非ok，取消非空成功；空/unknown/404有合法语义 | 初次失败也可重试；前台1/2/5秒封顶、隐藏/离线暂停；同owner同连接合并dirty，不能不停abort | §3同编号 |
| V3-08 | R1/R4/R5；C05 | 直接；需求动态变化 | demand随viewport/facet/owner真实变化；旧需求撤销、仍有效结果保留；恢复后局部读取不整页冻结 | 当前渲染依赖本轮全成功且React提交/锚点完成才ready；backgroundSettled独立 | §3同编号 |
| V3-09 | R2范围REST | 直接；兼容接口 | 可选recovery_view围绕任意展示消息；默认200上限500；不与旧offset/detail混用 | 400冲突、完整窗口、coverage身份/边界/顺序及规范SHA256；折叠详情独立digest；旧调用不变 | §3同编号 |
| V3-10 | R2 activate能力与封套 | 直接；协商与初次绑定 | capability宣告后发新参数；本轮完整REST receipt；最多2窗口≤500、详情12行批次，超出有界分批 | matched仅服务端重读证明，否则整窗口替换；owner/epoch/cut/state/details/complete可核验；旧后端明确降级非新版通过 | §3同编号 |
| V3-11 | R2原子replay cut | 直接；并发ring | events/latest_seq/truncated/epoch同一replay锁切点；锁外解码 | 并发stamp不能产生虚水位，既有字段/seq/epoch/ring上限兼容 | §3同编号 |
| V3-12 | R3.1 单conn事务与SQL | 直接；SQLite、深历史/lineage | 一个显式只读BEGIN同conn读owner/spine/代表/边界/payload，结束后投影；旧库不迁移 | 复用UID退役与分支排除、display_identity顺序；多段先算身份再有界payload，无全正文物化 | §3同编号 |
| V3-13 | R3.2/7 D0/S/D1锁序 | 直接；并发机制 | attach后只目标history_lock；短D0→释放DB→S replay→释放→短D1；不与全局resume、网络/图片/序列化嵌套 | 250ms有界history锁；不写锁/接管模型；独立DB连接/跨进程正式writer证明、短事务与投影分时 | §3同编号 |
| V3-14 | R3.3/4破坏性变更与append | 直接；rewind/replacement/delete/compact | D0已有区间字段/代表/顺序/lineage/rewind或Turn owner失效不得交接；普通append可有限完成 | view_changed有界重试（后端1/前端2）；追加超窗口coverage_gap；不可去重猜无漏行，不等待delta静止 | §3同编号 |
| V3-15 | R3.5快照与Turn归属 | 直接；活动/终态/外部lease | 持久快照节点与D1真实UID/row/tool occurrence核对；窗口外有界存在查询；未持久尾有正式当前Turn租约/起点 | retired/rewind不复活；外部接管无正式输出返runtime_unavailable；active不纯assistant文字退化为完整快照 | §3同编号 |
| V3-16 | R3.6/收尾事件/held | 直接；同epoch/新epoch/ring缺口 | S→有限B逐序证明后缀，B后帧继续正常；new epoch/runtime旧结果丢弃；held超4096/8MiB显式缺口 | 真实snapshot+suffix无漏重；不凭latest_seq跳帧；ring缺口重立快照；不会等待Turn结束 | §3同编号 |
| V3-17 | R3.8及observeControl/reduceProjection | 直接；事件/副作用/失效；接线细节重点 | 控制观察与投影应用独立去重；安全事实即时处理；全部正式历史失效接协调器 | session.info/Framework/complete/sessions.changed触发合并当前历史；rewind_count及正式rewind/edit/delete/compression writer广播有路径；不重toast/写入 | §3同编号 |
| V3-18 | R4视口/展开需求 | 直接；Timeline/Disclosure | 登记实际第一/末持久别名及offset、屏内已展开facet source；不依赖新projection先发布 | 视口外展开可后台，进入前校验；staging详情可读；收起/离屏不阻塞，失败可重试 | §3同编号 |
| V3-19 | R4有界定位/分页 | 直接；深anchor、加载更多 | 冷开仍latest200；暖anchor不在tail另读有界窗口；冻结tail界，稳定身份相邻分页 | 不offset追深anchor；旧/新offset不直接拼；邻接/重叠证明，冲突整页重读；未证anchor不等已删除 | §3同编号 |
| V3-20 | R4覆盖状态/显式间隔 | 直接；加载1000但只看一屏 | “曾加载”与“本轮已验证”区分；旧页不阻塞当前，可见前局部校验 | 深anchor与tail非邻接有非message间隔；未验证挂载中间页转间隔，保anchorDOM/offset，不全历史回读 | §3同编号 |
| V3-21 | R4前缀窗口比较；C06 | 直接；视觉衔接 | 对齐真实左边界与身份后比较有界窗口，判等含正文/状态/时间/已展facet；非只ID | 前缀覆盖当前屏才连续衔接；未证不当破坏；真正rewind/替换可重定位；结论非整库前缀 | §3同编号 |
| V3-22 | R5 profiles/cwd/metadata | 直接；全部页 | 每轮roster及当前owner有效性；New Chat默认cwd读取；当前聊天不等无关cwd | 失败保展示不授创建权限；当前标题metadata依赖；初始未validated仍恢复；404清缓存退New Chat且不resume | §3同编号 |
| V3-23 | R5 usage/pending/Secretary | 直接；胶囊、Composer、Orb/面板 | 当前字段/展开面板需本轮读；另一统计/未展排期后台；共享响应不能伪造部分成功 | Pending/审批/发送受理不缓存；恢复撤销旧可操作状态；Secretary/Schedules/Compaction按当前需求重读，错误非idle | §3同编号 |
| V3-24 | R5详情与Files；08 §3 | 直接；当前文件展示 | staging详情12行真实source；Files固定owner root/list/preview实际资源本轮读取 | 不靠mount/旧URL满足恢复；文本新文本、二进制授权资源重取；第三方渲染失败明确，不污染附件/配置owner | §3同编号 |
| V3-25 | R5登记扩展契约；C03 | 直接/推导；新增reader | 新读取同时接初始与重连，登记安排/必需/覆盖；不以allSettled结束即ready | 正式路径可故意漏登记反证未满足；读失败/取消/owner迟到不能ready | §3同编号 |
| V3-26 | R6键/库/owner | 直接；IDB过渡缓存 | 独立secretary-display-v1不改draft；schema+canonical server origin+profile+route，侧栏roster明确 | 初次未确认owner仅精确URL/确认profile候选；WebView文件origin不误作server；不default填充 | §3同编号 |
| V3-27 | R6白名单 | 直接；缓存payload | timeline最新≤200持久cards和可选额外有界窗不存位置/折叠详情；sidebar≤摘要，无运行字段；胶囊仅展示与兼容元信息 | 禁runtime/seq/审批/Pending/发送/临时/流稿/Notebook/Schedules/auth/Blob/图片/API全响应；不得由缓存推算新统计 | §3同编号 |
| V3-28 | R6容量/降级 | 直接；存储异常 | 单2MiB/总16MiB/10会话、sidebar500/1MiB、TTL7天、LRU；schema结构/过期丢弃 | 超大单条跳窗口不假截断；quota/private/损坏降内存不阻网；缺缓存非空历史 | §3同编号 |
| V3-29 | R6写入/失效/安全 | 直接；迟到/退出/404/rewind | 真值提交挡迟IDB；仅成功对账展示数据空闲合并≤1Hz；retained不刷新成功时间 | 404/owner消失删除；rewind/compact整窗替换不旧窗merge复活；模型失配失效Context；认证失败清document敏感投影 | §3同编号 |
| V3-30 | R7 visible/staged隔离 | 直接；React/RenderStore | Controller实时业务与不可变visible/staged分开；唯一commitId发布，RenderStore不判一致性 | 无共享可变binding深泄漏；安全禁用覆盖；组件状态不越过可见提交屏障 | §3同编号 |
| V3-31 | R7 Timeline handoff | 直接；动画/人工阅读 | 同帧layout恢复anchor/offset、不remount/清空；240ms ease-out至真实tail，暂停instant/ResizeObserver抢位 | delta增长不续期且终点真实末尾；用户wheel/touch/key/拖立即取消且不重播；降动效受控定位；ready不等动画/缓存/后台 | §3同编号 |
| V3-32 | R7及§1.13胶囊动画 | 直接；所有有效数值更新 | 规范可见签名含视图/数值unknown/估算/窗口；首次/同值/owner切换/用户切视图不闪 | 有效变化120ms亮+480淡，600ms合并不无限重置；不改selected/open/尺寸/Timeline位置；降动效短静态 | §3同编号 |
| V3-33 | §1.13统计/失效语义 | 直接；Session/Latest/Context | 原生可信含零；未知不清已有合法同scope值，未获数不捏造；Latest只最近完成Turn；New Chat无胶囊 | exact counters/cache比率；无独立计数/新API；cold同Session原生估算可用，已知模型/provider变更/rewind失效，普通append/compact不误失效 | §3同编号 |
| V3-34 | R8 JS协议/网页零行为 | 直接；JS/Native边界 | trusted origin+mainframe、hello document、recover事件同入口、state匹配document/native/recovery/demand；health只存活 | ready来自本轮React提交而非connected；当前轮先recovering后ready，旧包忽略；无HermesAndroid零行为 | §3同编号 |
| V3-35 | R8 deadline与退避 | 直接；前台/online/冷启/无JS | 真回前台单调固定5s；等hello不延时，重复resume/online合并；owner不延长 | 4.9s对应ready且health可免reload，超时先赢；fallback10/15/20/30每document真恢复；真回前台重置；冷启不额外reload | §3同编号 |
| V3-36 | R8保护/通知目标/降级 | 直接；认证/附件/通知 | 三方认证不注入/重载；Activity result不抢断；原生目标跨reload保留 | 当前文档ready不提前清通知目标，目标owner恢复才ACK；版本不匹配明确降级非新能力 | §3同编号 |
| V3-37 | R9/C12–16、R10构建 | 直接；过程/资源 | 6.1/high、不Astra不派生；保他人dirty/视觉，原阈值不放宽；本地隔离无真实模型生产 | 检查现候选和证据版本；前端build、原生单测；APK正式构建签名及内置资源SHA匹配候选 | §3同编号 |
| V3-38 | R10场景矩阵；C13/14/15/C17 | 直接；验证与豁免 | 全范围机制证据、Web实际结果仍必需；实际APK运行唯一豁免且明示未验，不启动模拟器 | 真实SQLite/并发/正式writer反证与正式前后DTO；不以helper/源码字符串/历史日志冒充当前；Web UI由后续Validation独立核验 | §3同编号 |
| V3-39 | §1.4继承消息投影/样式/时间 | 直接；历史与实时表现保持 | 真实行/原生wrapper/display_kind，单Timeline；普通user时间戳只UI去除、Reminder展开保留；临时slash只内存原边界 | 保持Thinking流/自动折叠、tool默认折叠真实状态、Framework/Reminder/compaction/完成通知各身份；不合成terminal提示，不猜正文种类 | §3同编号 |
| V3-40 | §1.4继承活动Turn与用户视觉 | 直接；Web/后台Instant/首次/重连/完成后 | 保完整carrier/Thinking/tool/assistant及全局列表状态，不逐会话activate；保64px底、阅读不抢底、人工样式/Pin/Profile图标 | 不用非持久取消文本覆写输出；System/Compaction宽度、Heartbeat、failed_turn、slash原语义；approval/patch预览与native choices不变 | §3同编号 |
| V3-41 | 08 §1/§3；C11 | 直接；Profile/files隔离保持 | Profile Home/config/db/history独立，Files固定单点profile，不随sticky/current变化；default-cwd在请求作用域解析 | root/list/preview/download同owner、真实失败不切换；聊天cwd/模型/附件/受理事务不被Files重归属；不修改全局HOME/cwd | §3同编号 |

覆盖汇总：41条独立判据，覆盖所有指定章节及R1–R10、C01–C17（C17仅实际APK运行完成条件）。第3节须逐条同编号填写，不删列；当前尚无实现判定，不把41条待查统计成通过。

## 3. 逐条实现证据

下表逐行承接第2节同编号的冻结原文、适用条件及独立判据，形成“原文→独立不变量→正式路径→检查输入/方法→观察→判定”的完整链。路径默认主仓；`web:`为`/Users/edgar/code/hermes-secretary-web/`；`E`为主仓`.hermes-dev/web-recovery-20261024/`。证据简写：`B`=backend/rev10-final-tests.log（39项）；`F`=frontend/review-final-tests.log（223项，后继修改按N适用替代）；`N`=frontend/n01-final-tests.log（5文件113项）；`P`=presentation/frontend-final.log（96项原包，按源码影响复用）及cold-handoff-fix-final.log（43项）；`A`=presentation/android-final.log及三份XML（22+13+5=40项）；`V3`=verification-v3/。这些计数重叠，不相加。指纹与构建核验见第4节。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| V3-01 | web:Controller.pageRecoveryOwner→ControllerPageRecovery→DisplayCache；REST/RPC使用原native seams | 读全部新增产品文件及冻结→候选差异；核只读有界DTO/展示白名单、既有drafts独立；F缓存有无均真实读取 | web:controller.ts:172–175/487–527；display-cache.ts:4–126；F；version-audit.json | 符合；无BFF、客户端SessionDB/事件库、新schema或写重放 | 已受理事务仍走原生owner；展示写入时点单列V3-29 |
| V3-02 | web:Controller.select/openConversation→profileRouteUrl/filesNavigationState；App New Chat Profile入口 | 核三屏、push/popstate及显式Back；真实Profile只在new选择；先GET summary校验再resume；F/P/profile/files回归 | web:controller.ts:706–779；core/files.ts；profiles.ts；App.tsx；P/F | 符合；导航未变成创建/取消Turn，Files返回保profile+route+草稿，已有对象不迁移 | 本轮非新增导航产品；原阅读位置仍只内存 |
| V3-03 | selected→attachConversation→GET summary→resume/activate→readWindows；SessionList单独摘要 | 静态追当前stored route唯一binding；B任意anchor/压缩branch；F缺404不resume、回收runtime重新resume、只当前正文 | controller-page-recovery.ts:279–306/410–498；tests/hermes_cli/test_recovery_view.py；B/F | 符合；不批量绑定侧栏会话；New Chat/Files不读任意历史，首发仍原newCreate单事务 | 无真实模型调用；保持既有cwd发现过滤 |
| V3-04 | retain/readCache→SessionList.refresh→renderStore retained/commit→App Sidebar | 核缓存未完成loading及列表不先清空；refresh保各Profile已加载offset、摘要页重读；读侧过滤运行字段；F session-list及P原样式回归 | web:session-list.ts:17–76；controller-page-recovery.ts:217–239/314–327；display-cache.ts:123–126；F/P | 符合列表过渡/owner/分页行为；Pin/日期分组/主题布局未改，真实标题有revision保护 | 当前可见写缓存过早是V3-29/N02，不把该行行为符合扩为R6全通过 |
| V3-05 | initialize/select/gateway.ready/online/visibility/Android→startRecovery→resources→reconcile→commit→React ack | 核唯一owner主干及本轮资源；F/N全页门/菜单门；独立V3实际App增加合法历史图片引用，首download503后online其余读取成功 | web:controller.ts:487–527/715–778/1348–1353；controller-page-recovery.ts；V3/attachment.test.tsx、attachment.log | **违规N04**；主干一次commit成立，但当前展示图片读取根本未进入需求，错误图片仍在而ready=true | 不是要求等全部历史/所有附件；反例只对当前挂载且IntersectionObserver已确认可见的图片 |
| V3-06 | PageRecovery.owner/context/resourceKey/connection/cancel；Controller changingOwner/epoch | 核document UUID、每次connected connection++、recovery/demand寿命与resourceVersions；F跨owner迟到/A→B→A | web:page-recovery.ts:17–155；recovery-demand.ts；controller-page-recovery.ts:179–185；F/N | 符合身份结构与取消；delta不推进恢复代次，owner切换不重新归属受理事务 | 缺失reader不是代次结构失效；独立计入N04 |
| V3-07 | PageRecovery.read/results/run/scheduleRetry/localFailure→UsageReadFacts | F空/zero/unknown与503/cancelled对照、初次与local自动1/2/5、隐藏/离线暂停、并发dirty；N菜单失败与关闭反例 | web:page-recovery.ts:142–250；usage-view.ts:71–129；controller-page-recovery.ts:329–345；F/N | 符合已登记reader结果契约；retained/fulfilled不被直接当ok，初次无validated也可重试 | 图片错误未登记属于V3-25/N04，不误称该错误已被结果结构处理 |
| V3-08 | setDemand→requirements/readLocalRequirements→commit demandVersion→acknowledgeCommit | F撤除慢需求、new facet、A→B→A、commit→layout前需求变更；V3正式App可见图片下载失败不影响ready | web:page-recovery.ts:67–99/185–250；V3/attachment.log | **违规N04**；已登记需求动态机制成立，但实际图片依赖/失败未报告，当前需求集合不完整 | backgroundSettled独立、不等待动画的设计符合；N04不能靠扩大到所有离屏图片来关闭 |
| V3-09 | GET messages recovery_view→_get_recovery_messages→selector/read_view/project_view | 亲读参数校验；真实REST8含任意assistant深anchor、200/500、offset/order/detail冲突400、legacy形状 | hermes_cli/web_routers/sessions.py:791–895；hermes_state_recovery_view.py:25–48/126–180；E/backend/recovery-final.log | 符合；每次完整cards、有owner/tip/lineage/首尾邻居/逻辑坐标/SHA256，折叠正文另digest | cards采用原投影；媒体网络资源就绪另属前端N04 |
| V3-10 | resume/live optional capability→attachConversation→activate.parse_request/activate_payload→HistoryWindows.replace | 核v1能力协商、当轮receipt、2窗≤500与detail12；B正式handler/pydantic、F native DTO matched/replacement/incomplete/legacy | tui_gateway/recovery_view.py:21–50/319–387；methods_session.py:694/867；server.py:3047；web:controller-page-recovery.ts:410–480；B/F | 符合；matched是服务端重读，失败返回明确reason，旧后端明确提示未完成v1 | 超12详情沿readFacets批次，非静默删除当前可见详情；旧客户端形状兼容 |
| V3-11 | session.events.since→read_replay_cut | 同replay锁复制events/latest/truncated/epoch、锁外thaw；并发stamp实际测试能暴露旧水位分锁问题 | tui_gateway/event_replay.py:133–145；methods_session.py:2190附近；E/backend/targeted-tests.log；tests/tui_gateway/test_tui_gateway_event_replay.py | 符合；cut无虚水位，保持原seq/epoch/ring及open_requests独立规则 | 不宣称open_requests与DB同事务 |
| V3-12 | read_view→hermes_state_timeline._snapshot→_lineage/_display_sql/_read_window/_details | 读同conn BEGIN/ROLLBACK及SQL CTE；真实1400行deep只5payload、NULL旧identity只读、branch/UID退役、第二conn追加不混快照 | hermes_state_recovery_view.py:52–235；hermes_state_timeline.py:40–49；tests/hermes_cli/test_recovery_view.py:37–148；E/backend/recovery-final.log | 符合；payload仅所选窗口，旧GET不补schema/索引，不用串接新conn伪快照 | SQL仍需身份计算；不等于数据库不扫描身份列 |
| V3-13 | activate先attach→_capture目标history250ms→D0结束→snapshot S→D1结束→project_view | B检查history/global resume/replay/DB均在投影前释放，真实跨进程正式writer；read-timing 1200行read36.77ms/projection117.64ms | tui_gateway/recovery_view.py:107–165/301–307/359–387；test_recovery_view.py:117–149/211–222/416–441；E/backend/read-timing.json；B | 符合；无DB/replay嵌套/写锁/模型接管，无全局resume持锁读DB，等待有界 | 本机一次计时用于证明边界分离，不承诺所有设备固定性能 |
| V3-14 | _proofs/_same_history/_coverage→activate_payload两次→frontend readConversation三次 | B独立进程replace/rewind/compression/delete、同数内容替换、重复破坏有限失败、独立连接append/超窗gap | tui_gateway/recovery_view.py:58–62/168–185/288–298/319–354；web:controller-page-recovery.ts:426–455；B | 符合；原区间/lineage/rewind变更拒绝，普通append允许，gap不猜连续，两次前端立即重试后退避 | 破坏性变化持续时可明确未恢复；不能为5秒接纳未证事实 |
| V3-15 | _turn_context/_native_source/_turn_proof/_prove_source/_clean_snapshot→D1 identity | B原生source路径/用户row/同ID异Profile/租约/换Turn、退休UID/tool occurrence、idle旧输出反例；正式native SSE恢复活动及idle | tui_gateway/recovery_view.py:85–105/176–286；B；E/backend/rev10-native-stream-probe.json、rev10-settled-proof.json | 符合；持久以D1真实代表，未持久需当前Turn起点/holder；外部无relay/runtime缺snapshot明确拒绝不报idle | loopback SSE不是真实供应商；外部owner无输出时只证明安全失败，不谎称完整恢复 |
| V3-16 | native snapshot S→atomic cut B→installCut逐seq suffix/held→event正常流 | B持续真实stamp线程不等Turn结束、ring截断新快照、新epoch；F suffix/held重放、重复seq与错误缺口 | tui_gateway/recovery_view.py:301–317；web:controller-page-recovery.ts:499–534；test_recovery_view.py:191–209/465–502；B/F | 符合；只追有限B，B后紧接，4096/8MiB超限显式失败；不凭latest跳帧 | 正常持续delta无每帧REST屏障；破坏变更另走失效重读 |
| V3-17 | Controller.observeControl先于held→sessionEventEffects；reduceProjection独立cursor；broadcast→startRecovery | 核安全request.cancel/受理/Pending观察即时，projection replay不跳；列正式writer：replace/secretary_set_user_content通知文件，rewind_count签名、delete/count/compact签名→sessions.changed；B通知跨进程/Profile/失败测试 | web:controller.ts:1156–1271/1300–1355；controller-event-effects.ts；hermes_state_messages.py:844–872；secretary_foreground.py:220–244；history_notifications.py；change_watcher.py:126–210；B/F/N | 符合；完整失效链、控制/投影独立去重、没有DB任意mtime全历史轮询 | 通知是best effort唤醒而非history revision；业务副作用不随projection重放 |
| V3-18 | useTimelineReading.reportDemand→DOM可见alias/signature/facet source→facets.readFacets | 读二分视口定位、只可见展开required、同owner staging rows详情12批、不依赖React新projection发布；P/F工具only/展开/收起/离屏反例 | web:chat-presentation.tsx:151–197；presentation-signature.ts；controller-page-recovery.ts:367–407；P/F | 符合Timeline/facet需求登记；不把整页历史或所有展开离屏正文当阻塞 | 图片是另一组件网络reader，未包含在facet详情中，已单列N04 |
| V3-19 | readWindows latest200＋anchorSelector；loadEarlier→anchor before200 after0→HistoryWindows | 核无offset追赶深anchor、首tail界保留、真实notfound才anchorMissing；真实深1100/1400及F stable邻接/重叠冲突 | web:controller-page-recovery.ts:488–498/614–632；history-coverage.ts:12–64；B/F | 符合；默认200，单次201含重叠anchor等于新增200；冲突触发整窗恢复，未证不当已删除 | 旧offset API仍服务旧调用 |
| V3-20 | HistoryWindows.invalidate/verified/view→index.clear替换本轮窗→App gaps | F深anchor+tail非邻接明确gap、旧loaded与本轮verified分开；background earlier不挡required，视口进入走selected覆盖 | web:history-coverage.ts:31–56；controller-page-recovery.ts:215–220/374–385/449–470；App.tsx:138–147；B/F | 符合；只发布已验证当前窗，中间旧页转非message Load earlier间隔，保anchor而不读满全部历史 | 后台准备不决定APK ready；gap不是合成消息 |
| V3-21 | DOM shared signature→visibleWindowCompatibility→reconcile.prefix→reading handoff | 核对齐左界/真实kind+UID或tool occurrence，连续有序LCP；F reorder A/B、正文、同UID thinking/message、expanded facet、unknown反例 | web:history-coverage.ts:67–124；presentation-signature.ts；controller-page-recovery.ts:535–545；F | 符合；判等含实际可见内容/时间/状态/展开字段，未知保持anchor而非假破坏 | 仅当前有界窗结论，非全Conversation前缀证明 |
| V3-22 | roster→profiles.list/config launch→selected summary；New Chat defaultCwd reader | F初次/同epoch、Profile不可用/404/old owner；读roster每轮，失败不授权create；metadata/title revision保护 | web:controller-page-recovery.ts:253–306/389–393/410–426/483–487；F/N；profiles.ts | 符合；初始未validated仍重试、先只读校验存在再resume；当前聊天不等无关cwd | roster若owner消失退New Chat并删条目；不借default猜owner |
| V3-23 | usage/pending/secretary/schedules/compaction resources→领域strict adapters→App需求 | F V01补读503/合法unknown/隐藏scope、V03菜单及Orb/Schedules；读原生pending/compaction/context、撤旧requests/pending | web:controller-page-recovery.ts:329–355/206–220；usage-view.ts:71–129；App.tsx:383–386/844–848；F/N | 符合这些已登记资源范围及结果；另一统计/隐藏排期不阻塞当前，失败不当idle，已受理写只读核实 | 已知不兼容Context的retained画面缺口另V3-29/33；不重复充当通过证明 |
| V3-24 | Files.register files-current→fixed root/list/previewFile→authorizedFile→hidden renderer stage→layout ack；facets strict读取 | P/F Files定向包括实际文本重读、二进制File重取、renderer loading/error、route替换cancel；核旧URL不算新读 | web:Files.tsx:46–76/163–236；FileViewerPreview.tsx；controller-page-recovery.ts:396–407；P/F | 符合Files与Thinking/tool详情接线；固定FILES_PROFILE不随chat/sticky；错误明确，stage不提前可见 | renderer依赖为受控替身，真实浏览器支持交Validation；不把此结论扩给HistoryImage |
| V3-25 | recovery-resources完整表→Controller/App组件reader；历史图片App.historicalAttachments→HistoryImage | 全组件API读取搜索反查；正式App历史user引用在viewport首download503，online后REST/WS全部恢复；同url/scope组件保留 | web:recovery-resources.ts；App.tsx:942–965；HistoryImage.tsx:4–57；V3/attachment.test.tsx、attachment.log | **违规N04**；图片fetch只mount effect，started=true后断observer，recovery没有端口/登记/失败/重试；online后ready=true、imageRequests=1、failed=true、rendered=false | 使用真实App+Controller+PageRecovery+阅读hook；仅网络/DOM几何受控，不替换待测机制；首次可见图片已实际请求，不是隐藏资源 |
| V3-26 | DisplayCache DB/keyFor/canonicalOrigin/sidebarKey/sidebarCandidate→readCache | 亲读独立库、精确origin/profile/stored路由、roster候选；F缓存跨owner/schema和首次roster前精确候选；APK可信origin为同HTTPS | web:display-cache.ts:4–15/121–136/200–218；controller-page-recovery.ts:222–239；F；Android PackagedWebViewClient | 符合；不拿runtime/WebView本地文件origin/default猜owner，不改drafts库 | 后续已知模型兼容失效缺口是V3-29/33，不否定键隔离本身 |
| V3-27 | displayRows/displayMetadata/displayCapsules/displaySidebar白名单 | F data/blob/token/嵌套图片binary拒绝、tool/Thinking正文去除、temporary/command/steer不缓存；读侧也同过滤 | web:display-cache.ts:16–126；display-cache.test.ts；F | 符合payload白名单；≤200持久cards/可选额外窗，不保存阅读位置，sidebar运行字段及capsules运行态剔除 | 完整正文过大跳窗不截成假正文；原native终态元数据仅展示字段 |
| V3-28 | DisplayCache.valid/queue/flush/LRU/TTL→memory fallback | F真实fake-IDB transaction quota/error、损坏schema/rows/capsules、TTL7日/10条、超2MiB窗口独立胶囊；源码核总16MiB/sidebar500/1MiB及空闲≤1Hz | web:display-cache.ts:4–11/138–253；display-cache.test.ts；F | 符合容量与不可用降级；不存在缓存不等空历史，存储错误不拦网络 | 不引入offline一致性保证；pagehide仅尽力flush |
| V3-29 | reader→cache.putSidebar；retained.visible→present.live；readCache/commit/acknowledgeDisplay | V3 Pending门延迟观测新sidebar put调用发生在旧画面/reading；已知模型变更business context_invalidated而render10%；F其它404/迟IDB/认证/失败TTL | web:controller-page-recovery.ts:186–239/326/572–612；V3/lifecycle.test.ts、lifecycle.log；F | **违规N02/N03**；侧栏写调用未等已展示；已知不兼容Context被retained复盖。其余迟IDB/404/认证及失败TTL已有约束 | N02不冒称IDB最终新值；N03只要求已知失效窄覆盖，不提前发布fresh REST。见§6原文研讨依据 |
| V3-30 | cloneDisplay→retained/visible/staged→commit→RenderStore.publish | 源码核structuredClone、不把binding共享到visible；F在business binding直接mutation后已发布snapshot不变，菜单stage current资格；N修复旧成功stage | web:controller-page-recovery.ts:43–52/186–205/601–612；render-store.ts；F/N | 符合不可变隔离与一次commit结构，RenderStore仅合帧；N01已按配置资源代次在held前失效 | 正确隔离结构仍可能保留应失效Context，具体语义缺陷单列N03，不掩盖 |
| V3-31 | useTimelineReading layout→anchor placement→240ms handoff→normal following | 亲读pendingAnchor同帧定位、local不cancel合法motion、晚挂MutationObserver；P43及F实际App冷无/有缓存、growing tail/人工取消/降动效 | web:chat-presentation.tsx:151–334；recovery-handoff.test.tsx；app-page-recovery.test.tsx；P/F/N | 符合；无remount/instant抢位，真实delta不续时长，输入即取消不重播；layout后ready不等动画 | jsdom几何受控，真实连续视觉/末尾由后续Validation；当前N04使总体ready不完整 |
| V3-32 | UsageSummary/ContextIndicator→useValueUpdateHighlight→theme.css | P原包+baseline7项、当前43中胶囊签名；F实际App胶囊回归；读规范显示数字/unknown/视图/展开字段、首次hasData建基线 | web:indicators.tsx:16–34/90–101/126–143；theme.css末10行；P/F | 符合；同值/首次/owner/视图不闪，600ms内不重启，120ms亮480淡，降动效静态短亮不改selected/布局 | Context不兼容值是否还应显示由N03阻断，不把动画机制当统计正确性 |
| V3-33 | UsageViews/usage-counters→App Utilities→retained render/cache compatibleCapsules | F原生来源/zero/unknown/Latest completed/cold估计；独立model_changed事件反证business已清旧数而render仍10% | web:usage-view.ts:30–129；usage-counters.ts；App.tsx:359–435；controller-page-recovery.ts:201–204/231；V3/lifecycle.log | **违规N03**；known model change按§1.13应省略旧数字直到可信新观察，retained不能反向延续已知错误百分比 | 普通断网/append/compaction及未知identity仍保合法旧估计；不要求以未知清数或新增API |
| V3-34 | AndroidBridgeTrust/parser→MainActivity.receivePacket→ForegroundRefresh；JS bridge→same recovery owner | A40/JS桥测试；亲读trusted HTTPS主frame/document/native/recovery/demand、hello非完成、health只存活；无HermesAndroid零行为 | web:api/android-health.ts；AndroidBridgeState.kt:6–113；MainActivity.kt:75–145；A/P | 符合桥协议身份/入口机制；当前包拒绝旧doc/native与无匹配recovering的ready | 网页依赖集合缺N04可产生上游假ready，已在V3-05阻断，非Native校验绕过 |
| V3-35 | ForegroundRefresh.resumed/startRecovery/hello/recoveryState/reload/checkHealth | A22覆盖4.9s ready+health、5s超时先赢、connected不解除、重复/online合并、无JS、10/15/20/30、新前台重置 | web:ForegroundRefresh.kt:42–137/192–217；E/presentation/ForegroundRefreshTest.xml；A | 符合单调固定5秒与有界退避；等hello或owner切换不续期，冷启无额外前台reload | Robolectric非实际WebView；C17实际APK明确未验 |
| V3-36 | external page/ActivityResults→MainActivity→NavigationMailbox→JS navigate→target layout ack | A认证/相机文件结果/通知mailbox及HermesBootstrap；F等待目标owner layout不提前完成导航；读旧协议降级日志 | web:ForegroundRefresh.kt:42–81/141–182；AndroidBridgeState.kt:130–150；MainActivity.kt；controller-page-recovery.ts:129–140；A/F | 符合认证/附件保护和通知目标保持，不因另一页ready清目标；旧能力明确降级 | 不外推真机通知/摄像头/登录实际通过；R8机制与C17边界分开 |
| V3-37 | 冻结候选diff→三包sibling→十检查→npm build/android build→签名APK | 核6.1任务记录/无子派生、本地isolated/fake SSE；source/manifest匹配；APK32,081,553字节、439资源逐SHA一致、签名v2有效 | E/review-staged-ten-checks.log；reports三包；apk-v3-manifest.json/signature.log/android-build-v3.log；V3/version-audit.json | 符合过程/构建范围要求；controller2512<原2556，新sibling不放宽health阈值；未混他人dirty或生产部署 | 无法由日志证明所有历史行为，但本次无UI/模型/设备/提交；push不替代验收 |
| V3-38 | R10→B/F/P/A及native SSE证据；本审查V3三定向反例 | 核真实SQLite跨进程writer、native stamp/lease/深窗、真实前后DTO同SHA，正式Controller/App控响应时序；APK当前SHA及资源独立核 | 第4节证据审计；V3/version-audit.json/counterexample-version.json；B/F/N/A；V3两日志 | 符合审查/构建证据入口与方法；没有以全绿套件掩盖当前三个失败，实际APK子场景按C17有依据豁免且未验 | 本行不是能力全通过；Web用户结果仍须独立Validation，当前门禁失败不能进入 |
| V3-39 | Controller native送/编/审批→sourceTimeline/reconcileLiveHistory→MessageSlot/Disclosure | 读恢复差异未改源role/content/UID或终态typing；P/F现native投影/temporary命令/Thinking/tool/用户committed回归；B cards46/timeline6 | web:projection.ts（未改）/App.tsx:138–350；session-recovery.ts；E/backend/targeted-tests.log；F/P | 符合继承消息/时间语义；真实wrapper/display_kind分类、不从英文猜类型，临时slash只内存原锚点、不派生terminal提示 | 真实供应商summary分段未改；不需为本轮恢复调用真实模型 |
| V3-40 | native background触发→typed snapshot/replay/global active_list→Timeline/App既有布局 | B正式SSE/native lease活动及结束证据、旧inflight14+terminal21；P阅读/完成卡/approval呈现回归；差异核保Heartbeat/failed_turn/patch preview、64px/Pin/Profile视觉 | E/backend/rev10-native-regression.log、native-stream-probe.json/settled-proof.json；web:App.tsx/projection.ts；P/F | 符合本轮继承语义保持；恢复不等Turn完结、不压制carrier/Thinking/tools，不导航cancel他处Turn | 未宣称所有渠道/设备再次实际验收；变更只恢复接线而未改其原生契约 |
| V3-41 | ProfileEnvironment/Controller.select→FILES_PROFILE→root/list/preview/download；backend default-cwd | 核fixed default单点、无随机first/sticky fallback；P/F不同chat owner/return/deeplink/错误；原请求profile配置作用域未改 | web:core/files.ts；profiles.ts；Files.tsx:36–76/163–236；controller.ts:715–779；主仓fs default-cwd原路径；P/F | 符合08保留隔离；Files不改变聊天/附件/配置/受理owner，不改全局HOME/cwd | 非新增Workspace产品或跨Profile Agent检索权限 |

## 4. 核心目标及验证方法审查

**全范围41条：36符合、5违规（V3-05/08/25/29/33）、0证据不足、0整项不适用；五条违规对应3个独立范围内阻断N02/N03/N04。门禁不通过，不能进入Validation。** C17仅使实际APK运行子场景用户豁免/未验；R8单测机制与构建签名资源仍适用并已核。主会话不能把3个失败被大量绿测覆盖或APK已构建写成整轮完成。

核心机制主干确实落实：统一恢复owner→roster及只读存在校验→当前Conversation的完整有界REST receipt→原生activate D0/S/D1→完整当前Turn snapshot和有限S/B/held连续后缀→隔离staging→可见commit→React anchor/Files layout→ready。它不是REST/WS各等一次，不等Turn或全部历史结束，不将cache当cursor。多Profile/Files、错误/取消/unknown、深anchor与间隔、可见展开详情及原生5秒生命周期均有正式路径。当前核心目标尚未收敛：真实可见图片reader可永远停在首次503，整页却ready；过渡快照写入/失效的两处窄边界还不符合原文。

反证问题与观察：

1. 当前有一项可见读取失败，而其它已登记资源都成功，是否仍可ready？正式App图片反证确认会。原测试只证明HistoryImage靠近视口fetch一次、换scope取消及非图片失败，恰好允许错误实现在同URL恢复时永远不重试；F/N没有把这个组件与恢复owner接起来。
2. 同owner完整恢复尚未提交，已成功读的可见侧栏是否被作为“已展示”写缓存？正式Controller反证确认reader已调用putSidebar，visible仍旧列表。原cache TTL测试聚焦Usage失败/迟到owner，不能覆盖该写调用时点。
3. 已知model change后原生已明确Context失效，保留画面是否会把旧percentage再盖回来？正式事件进入Controller后business为model_changed而render仍10%。这不是fresh REST慢导致暂时未知，而是已经观察的失效事实被表现层覆盖；保持整幅旧画面不能取消§1.13明确失效语义。其余Timeline/Usage/anchor仍可保留。

证据版本与复用：

- 本审查开始及反证结束均为主仓`aed15db4`/Web`833d456e`；`V3/counterexample-version.json`8个关键产品文件工作树与指定Git候选SHA全部一致，Web工作树无产品dirty。主仓plan/AGENTS/CLAUDE/07及其它文档dirty保留；不作为本轮产品变更。
- `V3/version-audit.json`独立校验frontend/source-manifest26/26、N01 manifest11/11、post-verification13/13匹配。早期review-fixes中PageRecovery/test两项后续变化，由当前F及N覆盖；presentation最早manifest26项只有17相同，明确按影响复用：Kotlin/JS桥/Files/preview/signature/theme等未改，indicator由baseline修补证据，reading由current cold-handoff43及正式F/App/N覆盖，不把旧96项改称833d全套新跑。
- backend REV-10 manifest产品/测试/原生依赖10项匹配，仅动态plan文字已变；B39对应当前recovery_view。按原文读测试实际底座：正式session.activate handler/pydantic、真实SQLite、独立进程正式replace/rewind/archive_and_compact/delete、独立连接append、真实native stamp线程和租约/Turn切换。受控snapshot wrapper仅选并发时点，不用fake SQL或内存数值冒充正式writer。其它未改接口可复用replay17/watcher2/cards46/timeline6/通知4/生成契约1等原日志，不累加总数。
- 真实loopback SSE证据经正式Dashboard WS/REST→native Turn→真实SQLite，在仍running时恢复同runtime/精确正文/complete，最终唯一assistant持久化、idle无未知尾。manifest与源码已核；不冒称外部供应商或真实浏览器用户结果，不新发请求。A三XML核22+13+5=40、零失败/跳过，对应当前Kotlin源码。
- 独立核当前APK32,081,553字节，SHA256`d58e4979ace29015f70f75540752d2502feffb0a3dd5fb753fffae46c97cb509`，解包439个assets/secretary文件与当前dist逐字节SHA一致，mismatch=[]；android-build-v3含tsc+Vite及正式APK完成，apk-v3-signature记录同包有效v2签名、公钥未改。C17明确没有运行APK/设备/模拟器，不拿40个Robolectric或签名替代实际WebView。
- 本次只新增V3定向探针；两生命周期断言及一正式App图片断言均失败，详见日志。N02早期读取IDB仍旧值的探查不能证明写时点符合，最终断言针对正式putSidebar调用、精确记录区别；没有把初次探查绿例算最终通过。图片HTTP/native字段是明确受控输入，真实App、Controller、PageRecovery、projection、HistoryImage和阅读hook均未mock；没有改产品来造失败。

未复跑无关大套、未操作UI/生产/设备、未调用真实模型、未提交或部署。后续真实Web结果由另一个独立Validation验证；当前三个阻断未修前不得开始该门禁。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| N02 / P2 | V3-29；R6“写入仅取本轮已成功对账并展示”；web:controller-page-recovery.ts:314–326 | Sidebar可见，foreground恢复新列表HTTP成功、Pending门延迟；phase=reading/visible Real title，而reader已putSidebar(New sidebar title)。V3/lifecycle.log正式调用断言失败 | 将尚未完成可见交接的数据当已展示快照写入，绕开限定成功/失效边界；范围内明确机制偏离，不能用缓存可丢弃豁免 | 主会话已提pending成功事实→对应commit/layout与published rows匹配后写；补未ready无写、ready写、失败TTL/失效resource/迟到owner、隐藏晚到独立成功 | 主会话接受阻断，方案原则通过；固定候选仍未修，不关闭 |
| N03 / P1 | V3-29/33；R5模型/provider先失效、R6不能错误百分比、§1.13 known model/rewind omit number；web:controller-page-recovery.ts:186–204/231 | 同owner可信session.info模型改新，business context_invalidated=model_changed；retain冻结仍返回旧Context10%。V3/lifecycle.log原生事件正式路径断言失败 | 明确不兼容的旧统计仍可见，已观察原生失效被旧画面逆盖；不是未知字段、普通断线允许保留的估算 | 主会话窄覆盖已知失效，不提前泄漏fresh REST；补model/provider/rewind门延迟、冷cache identity后确认不符、迟IDB/旧usage不复活、合法估计保持 | 主会话接受并提方案，原则通过；当前未修，不关闭 |
| N04 / P1 | V3-05/08/25；§1.4通用完整恢复及R1/R5；web:App.tsx:942–965→HistoryImage.tsx:13–52；recovery-resources无图片 | 实际App挂载的历史图片靠近viewport正式GET503，组件started=true并断开observer。随后online走当前完整恢复，仍相同scope/url/key；ready=true、GET仅1次、failed=true、没有img。V3/attachment.log | 网络恢复后用户仍必须重载页面才可重试；可见资源失败未进入本轮就绪边界，APK也可误获ready。不因reader既有未修改而从本轮全覆盖豁免 | 主会话提出同唯一协调器的图片需求/reader方案；需当前实际可见图片本轮完整重取、错误/取消不ready、同URL自动重试；离屏/未需要不阻塞/不全量下载、跨owner/迟到取消、保持同Timeline与锚点，不靠remount或新循环 | 新发现，待主会话提案与实施；范围内阻断 |

范围外：旧wire catalog的孤立`review.summary`失败已有冻结树同runner复现，非本轮新增，不据此扩全仓修复或声称全仓测试全绿。未发现需新产品权限或改变冻结范围的事项。当前发现均在原恢复/展示契约内，工程细化无须用户补写函数名。

## 6. 修复与独立复审

全新v3独立审查：两必读Skill完整阅读，先仅依据冻结原文及C17建立41条判据并落盘、按约交回里程碑，再读当前指导/README/CLAUDE/index/baseline/plan、实现、证据及旧报告。第2节原始判据未改。没有用v1/v2旧问题清单代替全范围审查，没有退回补审或偷换候选。

旧问题关闭复核：原V01 Session补读503通过UsageReadFacts当前scope严格成功结果，不从detail fulfilled或旧数ready；原V02正常成功Usage/Context按owner/epoch/current、published signature白名单合并缓存，失败不续TTL；原V03 Model/Thinking真实受控开关登记、无mount-only reasoning旁路；原V04/REV-09同恢复local commit不取消motion，晚DOM可放末尾；REV-10原native source+DB/UID/lease证明真实普通Web Turn。源码与当前证据按影响独立检查，均可关闭原问题，不因此豁免N02/N03/N04。

N01旧阻断独立复核：业务observeControl在held入队前比较已知model/provider/reasoning字段，configuration-changed单次失效capabilities/reasoning及旧capabilitySerial；menuStages保留也无current资格；read中capabilitiesForBinding不另发旁路，显式成功config写同入口。N113含Model/Thinking旧stage、变更后失败不ready/自动重试、held帧、本地写、关闭/切owner迟到、普通delta不增菜单读、legacy串号；真实App最后DOM联调。11个manifest源码全部匹配833d456。**N01在本候选按原R1/R5/R7证据关闭**；这是配置成功证明失效已修，不等于Context表现失效N03也已修。

| 研讨/复审项 | 原判据与发现 | 主会话提案及理由 | Verification评审/是否改规格 | 实现版本与关闭证据 |
|---|---|---|---|---|
| N02 | 第2节V3-29；R6只成功对账且展示数据写，正式reader先put | 撤reader写，精确roster/rows/context作为pending事实；可见commit+layout ready且published rows匹配后写，owner/recovery/resource过时取消；隐藏慢读独立成功不挡ready | 符合原文方向。关闭需同owner资源重取使旧成功资格失效、失败不续TTL、隐藏晚到有效独立窗口；未改规格 | 仍833d456未修；lifecycle反例失败，待实现后全新独立全范围复审 |
| N03 | 第2节V3-29/33；先记“立即”解释疑点，再回原文研讨，business已失效而retained逆盖 | 主会话回读§1.13明确known change/rewind省略旧数；已知不兼容为原生即时事实，只窄叠加Context失效，保其余画面/anchor，fresh REST仍commit；冷cache留identity供真实binding确认 | 根据R5“先处理兼容失效”+R6错误百分比+§1.13原文，确认原判据已要求此失效，不是新增产品“立即更新”规则。方案原则符合；旧IDB/usage不得复活，未知identity不能清合法估计 | 当前未修。反例仅观察reading中过渡值，不拿受控后返回旧数冒充最终fresh真值；无迁就实现降低判据 |
| N04 | 第2节V3-05/08/25；完整页面依赖含当前可见组件读取，新增/修改读取共享初始重连；实际App GET503后online不重试 | 主会话接受反证：App传唯一pageRecovery及scope，图片按真实viewport登记依赖/覆盖，同URL每轮真实授权GET且验证可呈现；结果stage到统一/local commit，失败沿原1/2/5重试，离屏撤阻塞、owner/迟到/对象URL有界清理；不remount、不加整页循环、不批量读隐藏图 | 原则符合已冻结R1/R4/R5/R7，不改变产品规格；关闭条件见下方N04研讨续接，方案认可不是实现通过 | 固定833d456反证仍失败、N04仍未关闭；本次仅研讨，不重跑/不改产品；新候选另全新独立全范围复审 |

**N04研讨续接（2026-10-24，仅方案评审）：** 主会话为提案方，Verification依已冻结第2节V3-05/08/25及06 §1.4通用恢复、R1当前可见ready、R4需求/覆盖、R5初始与重连同登记、R7统一交接评审，结论为方案原则符合。真正完成需要实现及如下证据，不能以“方案已认可”关闭缺陷：

1. **唯一owner与真实可见需求：** App只传既有恢复port/scope；图片不另起整页循环。当前viewport中待显示图片在首次状态尚未判定时不得因空登记被误认为ready；注册/取消、解码回调及React layout交错不能出现本轮ready先成立再补发现必需资源的假成功。需求/资源覆盖由真实server/profile/Conversation、图片URL及恢复/连接资格约束；同URL不能借上一轮Blob或failed/fulfilled结果满足本轮。
2. **读范围和生命周期：** 外部授权图片引用每次初始/重连/online均真实读取，并验证实际可呈现；已有内联data-image回退保持原生正文的展示语义，不额外引入API或伪造授权GET。临近预取可保留，但登记表在整轮“安排所有reader”时不得顺带下载从未需要的全部隐藏图片；当前可见依赖才阻塞，离屏/关闭撤阻塞，仍有用的已发读取可后台结束。已验证同轮结果允许按其有效覆盖复用，不随正常delta/重复IO事件无意义重读或推进整页代次。
3. **统一采用与错误边界：** 成功授权响应和解码只是staging成功事实，新图按同一full/local commit及相应layout采用；慢图片不能独自提前覆盖已保留画面，保留旧图也不能当本轮ok。网络503、非图片/解码失败、取消及过时结果有明确状态，当前required失败阻断ready并沿原1/2/5自动重试；不可只在下一online或用户重新挂载时重试。普通已完成恢复后的滚入/展开需求走局部读取，不把全页退回冻结；owner/再次断线/epoch变化取消旧资格。
4. **对象URL与原视觉：** 旧可读图/占位保持，不用remount Timeline/消息/图片作为恢复捷径，不破坏阅读anchor/原滚动或用户手势。每个候选及已展示ObjectURL有明确内存owner，只有被替代/取消/退出的对应URL才释放；新旧请求、迟到解码、卸载交错均不泄漏或误释放正在展示的新图。图片Blob/ObjectURL不进入R6持久缓存。
5. **必要关闭证据：** 沿实际App→Controller→PageRecovery→HistoryImage补首次503→同URLonline成功、无online的自动retry成功、同URL已成功后的重连真实重取；同时证明HTTP/解码门未放行前ready=false，新图到统一/local commit才采用。补离屏慢图不挡/不批量请求、实际滚入新增依赖、同URL不同scope/owner及旧请求/解码迟到、新旧URL清理、非图片与解码失败不ready，保持原内联回退/有界预取。测试应控制网络/解码与几何边界，保留正式App和恢复/图片机制；源指纹绑定新候选。新候选仍需全新独立全范围复审，之后才做独立真实Web Validation。

本次未运行任何测试、未读取/修改新候选产品，也未重判原反例；原候选36符合/5违规、N02/N03/N04三个阻断及C17边界原样保留。主会话仅扩大HistoryImage与App附件props接线的实现白名单不改变产品范围；如实施实际需要修改其它共享接缝，应按既有协作白名单协调，不以此评审自行授予无界改动。

供最终交付摘要的实质收敛：N02明确“成功读取”与“已展示快照写入”不可混同；N03明确旧画面保持不覆盖已确认Context不兼容失效；N04要求恢复覆盖当前实际图片组件读取而非只覆盖文本cards与折叠facet。均为冻结方向内工程收敛，不需改原规格。主会话应同步plan/CLAUDE并在最终汇报说明；当前三项全部未关闭。

最终门禁结论：**不通过**。主仓`aed15db4d7175fdbf4b1ba6a4dece351255ce6cc`／Web`833d456e8c8a71f0388e902ac19dda7e5586eda8`的全范围审查完成，36/41符合、5/41违规，三个范围内阻断；实际APK按C17豁免/未验。不可进入Validation或宣称本轮完成；产品尚未改动，需主会话安排实现后由全新审查者重新提取全范围判据复审。

# Verification v4：20261024-web-recovery

## 1. 审查对象与结论概览

审查者：全新独立 gpt-6.1-sol / high，未继承主会话实现解释，不派生。判据建立日期：2026-10-24。冻结原文：主仓 ba83d2b430e3448461dd7feb9f1acd8fc94c6cc9 的06 §0.4、§1.2现行替代、§1.3、§1.4（含R1–R10）、§1.13，以及08仅Profile／Files保持条款；该版本snapshot-index C01–C16仅定位，当前索引C17是唯一完成条件变更。候选：主仓06dc95c168dbeb0f8cb5fead0f597173176b073d；Web474cd4f61d6fe7b29917cdd07fb3f4f647401265。本轮索引及baseline：.autonomous/20261024-web-recovery/。本节与第2节首次落盘前仅阅读上述冻结原文、模板及两个必读Skill，未读实现、测试、旧报告、动态看板。历史报告追加前字节数及SHA由工具输出留存，未修改历史。结论：全范围43条审查完成，42符合／1违规（V4-32/N05）／0证据不足／0整项不适用；门禁不通过，不进入Validation。实际APK运行按C17本轮豁免／未验，Web实测、原生机制／单测、签名与内置资源不豁免。

## 2. 独立要求清单与覆盖

以下为只据冻结原文独立建立的起点；直接要求记“直”，由指定机制必然推出者记“推”。未以代码命名、测试预期解释规格。后续若修订必保留原判据与理由；当前无修订。表内核查位置均对应第3节同号行，尚待调查。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| V4-01 | 06 §0.4、R6；C01/C10 薄客户端 | 约束／全部 | 直：只有白名单展示快照，服务端仍为事实源 | 无第二历史库、runtime账本、通用响应缓存、后台双端同步；缓存不省真实请求 | 第3节01 |
| V4-02 | 08 §1/§3；R1/R5/R6 owner | 边界／跨Profile同ID、Files | 直：真实Profile／Conversation／server归属；推：晚到不得串owner | 发送／草稿／附件／恢复／配置owner稳定，Files固定单点且root/list/preview/download一致，不污染新聊天cwd及返回身份 | 第3节02 |
| V4-03 | 06 §1.2现行替代、§1.3 | 行为／三页面与选择 | 直：New Chat导航无创建，打开既有对象原生历史，切换不取消Turn | 浏览器路线／Files返回保留；404只读确认安全退回不resume不存在对象；不批量激活其他Conversation | 第3节03 |
| V4-04 | 06 §1.3、R5 | 行为／侧栏 | 直：缓存过渡、跨Profile分页保留、原地更新 | 每owner成功独立发布，当前可见旧页完整重读；不以first-page抹掉可见旧页；冷无缓存不误空，不闪全列表，不冒充实时运行状态 | 第3节04 |
| V4-05 | R1；§1.4统一恢复 | 机制／全部触发 | 直：Controller唯一协调器；启动／重连同覆盖 | initialize/select/gateway.ready/online/visibility/Android统一入口；初始失败或未validated仍可恢复；并发同owner同连接合并dirty，不反复abort | 第3节05 |
| V4-06 | R1代次与结果 | 机制／异步、取消 | 直：document/connection/epoch/recovery/demand各自生命周期 | owner/断线/epoch变更旧请求和提交失效；正常delta不重启；每资源ok/error/cancelled明确，合法空/unknown与失败retained分开 | 第3节06 |
| V4-07 | R1重试 | 行为／网络与失败 | 直：retryable-error不可假idle/ready | 网络可用前台1/2/5秒封顶自动重试，断网隐藏暂停，新触发立即尝试；失败不靠下次gateway.ready，写操作不自动重放 | 第3节07 |
| V4-08 | R1/R7 ready | 机制／当前可见提交 | 直：需求成功+历史流证明+React commit定位后ready | ready不由Promise fulfilled/connected/缓存或后台settled推断，需求变化重算，后台慢不阻塞；安全控制实时覆盖 | 第3节08 |
| V4-09 | R2 REST范围读 | 机制／原生接口兼容 | 直：既有messages可选recovery参数任意可展示anchor | latest200/≤500，anchor非仅human，before/after有界；与offset/detail冲突400；每次完整cards，无缓存版本省正文，旧调用不变 | 第3节09 |
| V4-10 | R2 coverage | 数据证明／窗口 | 直：owner/tip/lineage/边界/邻接/顺序/范围/digest | 展示字段及身份顺序SHA256，不混临时URL／请求时间，折叠详情另digest；只本轮内存有效 | 第3节10 |
| V4-11 | R2 activate封套 | 机制／有能力后端 | 直：本轮REST receipt且server重读matched或全窗口替换 | 默认≤2窗且每窗≤500，detail12批，不静默漏可见；返回owner/epoch/cut/state/complete失败；capability宣告后才发参数，旧后端明确降级不能称通过 | 第3节11 |
| V4-12 | R2 events.since | 机制／回放切点 | 直：events/latest/truncated/epoch同replay lock复制 | 不虚水位，锁外解码，字段兼容；open_requests不冒称DB共事务；并发stamp能验证原子性 | 第3节12 |
| V4-13 | R3.1 SQL短事务 | 机制／真实数据库 | 直：一个显式只读BEGIN同conn读owner/spine/代表/范围正文 | UID退役、首次逻辑序、active/compacted/branch语义保持；多lineage先身份后窗口payload，不全量SELECT *；读不写索引/回填；事务后投影 | 第3节13 |
| V4-14 | R3.2/7 D0/S/D1锁序 | 机制／恢复封套 | 直：attach后目标history_lock；DB→replay→DB不嵌套 | 无全局resume lock跑DB，history≤250ms等待，可重试不终止Turn；无锁内网络/图片/投影/等事件；短事务及大投影分别计时 | 第3节14 |
| V4-15 | R3.3/4相容证明 | 机制／并发持久修改 | 直：比较D0原区间身份/顺序/内容、lineage/rewind/Turn owner | rewind/replacement/delete/压缩返回view_changed；append容许D1最新完整窗口，无法证连续coverage_gap；后端最多重做1次、前端最多2次立即重试，其后退避 | 第3节15 |
| V4-16 | R3.5当前输出 | 机制／活动／idle／外部lease | 直：持久输出D1代表优先，退休UID不live复活 | 窗外只bounded身份归属查询；未持久输出必须当前Turn真实租约/起点支持；外部owner无正式快照runtime_unavailable沿relay重取，active不降级纯文字 | 第3节16 |
| V4-17 | R3.6/末段 finite suffix | 机制／流恢复、epoch、溢出 | 直：有限B逐seq完整后缀，S后不断流 | staging按epoch/runtime/seq去重；ring截断先完整snapshot；held≤4096帧/8MiB超限明确缺口重建；缺帧不跳cursor，epoch/runtime/文档旧结果丢弃 | 第3节17 |
| V4-18 | R3观察／投影拆分 | 机制／恢复中业务安全 | 直：observeControl与无副作用reduceProjection独立水位 | 观察先前进不跳过staging事件；审批撤销/受理/通知观察不暂停，无重复toast/通知/写 | 第3节18 |
| V4-19 | R3.8历史失效 | 机制／正式writer与广播 | 直：session.info/Framework/complete及sessions.changed均入协调器 | 当前历史合并重读不读其他正文；rewind_count签名捕获同数replacement；正式rewind/edit/delete/compression writer完成后有原生广播，无任意mtime全历史轮询 | 第3节19 |
| V4-20 | R4 viewport/facet需求 | 机制／滚动、展开 | 直：实际可见首尾持久别名/offset及facet source登记 | 需求不等新projection mount；离屏展开不阻塞，进入前校验；恢复前需求改动旧结果不满足新需求 | 第3节20 |
| V4-21 | R4 bounded分页/覆盖 | 机制／深anchor及更早历史 | 直：latest和深anchor分有界窗，不offset追赶 | 首尾邻接重叠校验，冻结页尾，冲突整页重读；普通Load earlier同helper；loaded与validated分开，旧隐藏页不挡当前屏也不覆盖新页 | 第3节21 |
| V4-22 | R4对齐公共前缀 | 行为／视觉连续判定，薄弱接线重点 | 直：真实左界与逻辑身份先对齐再比较实际可见内容 | 含正文/name/status/timestamp/已展示facet，折叠内容不参与；未验证/超时不得当anchor删除或前缀破坏 | 第3节22 |
| V4-23 | R4深anchor到tail | 行为／非相邻窗口 | 直：明确分页间隔不是消息且不填全历史 | 动画只跨已验证挂载窗口/间隔；先将未验证中间页转间隔保留anchor；准备慢可先ready，不假报动画完成，准备好只执行一次 | 第3节23 |
| V4-24 | R5 roster/配置 | 读取／当前owner权限 | 直：每轮重读roster及当前有效性；New Chat cwd依赖独立 | roster失败保展示不可创建；current chat不被无关default cwd卡住；标题真实metadata优先旧列表不回滚 | 第3节24 |
| V4-25 | R5 Usage/Context/安全状态 | 读取／胶囊、pending、审批、发送 | 直：实际呈现scope及详情是依赖；安全状态不缓存 | 另一scope后台，unknown合法非error；模型兼容先失效；恢复中旧审批不可操作，受理事实只读核查不重发 | 第3节25 |
| V4-26 | R5 Secretary/Schedules/Compaction | 读取／Orb及已开面板 | 直：当前显示所需字段本轮读取 | 折叠排期正文不阻塞；共响应不可伪分成功；相关配置/面板两入口完整，失败可恢复 | 第3节26 |
| V4-27 | R5详情 | 读取／可见Thinking/tool展开 | 直：所有可见facet source rows在staging可读 | 12行批，无等React死锁，取消/替换明确结果，失败区别空并可重试，过时不复活rewind | 第3节27 |
| V4-28 | R5 Files | 读取／root/list/text/media/第三方preview | 直：effect纳本轮代次，固定owner实读 | root/目录/metadata及呈现资源重取；不旧ObjectURL假新结果，第三方渲染失败明确；隐藏文件不下载；返回与深链接不串owner | 第3节28 |
| V4-29 | R5登记可扩展性 | 机制／所有reader | 直：资源登记已安排/当前必需/结果覆盖 | mount及reconnect同覆盖；漏登记使恢复未满足的行为证据，非源码字符串断言/allSettled成功替代 | 第3节29 |
| V4-30 | R6 DB/键/白名单 | 缓存／持久边界 | 直：独立secretary-display-v1，canonical服务origin+schema+profile+route | 不改drafts库，明确roster侧栏键；owner确认前精确候选不猜default；Timeline≤200+一可见窗，折叠正文不存；胶囊只展示统计；禁止项全部排除 | 第3节30 |
| V4-31 | R6容量/失效/降级 | 缓存／边界 | 直：2MiB/16MiB/10会话、侧栏500/1MiB、TTL7天/LRU | 巨正文跳过整窗不假截断；schema/损坏/过期丢弃；quota等降级不挡网络；无缓存不等空历史 | 第3节31 |
| V4-32 | R6写入/敏感性 | 缓存／异步与认证 | 直：已成功对账且展示后闲时合并≤1Hz，后台窗独立成功 | late IDB不盖真值，failed retained不刷新成功时间；404/owner消失删，rewind/压缩替换不旧窗merge复活；model/context失效；退出/认证失败停敏感展示清document投影 | 第3节32 |
| V4-33 | R7不可变单次交接 | 机制／React/RenderStore | 直：业务实时state与visible/staged隔离，一次commitId快照 | 不共享可变binding导致深层泄漏；RenderStore仅合帧；旧画面保留，Timeline无remount/no clear，commit后同帧anchor定位才ready | 第3节33 |
| V4-34 | R7滚动动画 | 表现／增长、输入、降动效 | 直：约240ms ease-out同reading owner，暂停instant/ResizeObserver抢位 | 当前anchor屏内位置保住后滚真实tail；delta继续，动画不续期末端最新；wheel/touch/key/拖取消不重播；无位移无动画，reduced-motion受控定位 | 第3节34 |
| V4-35 | R7/§1.13胶囊动画 | 表现／普通更新及恢复 | 直：实际展示规范签名，首次/同值/换owner/切scope不伪闪 | 有效变化120ms高亮480ms淡回，600ms内合并不无限闪；不变open/selected/尺寸，不滚Timeline；reduced-motion短静态高亮 | 第3节35 |
| V4-36 | §1.13统计语义 | 行为／Session/Latest/Context | 直：原生可信数值零有效，已知值增量保留，scope/owner隔离 | Latest为完成Turn不由差分编造，unknown不清旧有效值；冷Context可native估计，model/rewind失效而append/compaction不误失效，既有API读，不本地推token | 第3节36 |
| V4-37 | R8 packet/信任 | 原生／APK，Web零行为 | 直：可信origin+主frame，hello/health不等ready | document/nativeRecovery/recovery/demand身份校验；onPageStarted旧文档失效，先recovering后ready仅当前代；普通Web无HermesAndroid零副作用 | 第3节37 |
| V4-38 | R8 5秒/退避 | 原生／foreground/network/watchdog | 直：单调uptime固定5秒，重复resume/online合并不续期 | 等hello也不延长，ready且心跳有效才取消；超时已reload不可撤；connected不解除；冷首开正常，后10/15/20/30新document需ready，无JS独立兜底 | 第3节38 |
| V4-39 | R8保护与目标 | 原生／认证、附件、通知 | 直：认证页不注入重载，Activity result保护原样 | 返回可信页hello恢复；通知目标跨reload保留且对应目标owner恢复完成才确认，当前页ready不能清他owner目标 | 第3节39 |
| V4-40 | R9/C11–C16工程边界 | 约束／集成、保留能力 | 直：6.1实施门禁、不扩scope/后端服务/模型/生产 | 保留用户视觉/Pin/原生发送/编辑/认证/附件/通知；新模块分离facade不增加健康超标，现有规则阈值不放宽；提交push事实如实 | 第3节40 |
| V4-41 | R10机制证据 | 验证／后端、Web、native | 直：全列场景有匹配版本有效证据，可复用不重跑无关大套 | 原子并发、真实双连接/跨进程正式writer、持续delta/lease、深anchor/详情/失败/owner/动画/5秒均覆盖，测试底座不绕正式路径，Python项目venv/run_tests | 第3节41 |
| V4-42 | R10/C17产物与实测 | 完成条件／交付边界 | 直：Web实际结果+原生单测+内置签名资源匹配；实际APK本轮豁免 | 当前包签名及资源SHA与候选绑定；不启动模拟器；实际生命周期/相机/通知未验明确，Robolectric不冒称WebView实测，Web结果不豁免 | 第3节42 |
| V4-43 | §1.4继承消息/呈现 | 保持／历史及流 | 直：真实消息投影、现有包装分类/临时命令/分页/阅读规则 | 恢复不合成历史、不丢重复Thinking/tool/正文、真实中断元数据不造卡；200分页、底部64px、用户视觉及正常人工阅读保持 | 第3节43 |

## 3. 逐条实现证据

各行承接第2节同编号的冻结原文、独立不变量、适用条件及判据，构成“原文→判据→正式路径→方法/观察→判定”的逐条链。路径默认Web仓`/Users/edgar/code/hermes-secretary-web`，`B:`为主仓`/Users/edgar/code/hermes-secretary`；`E`为主仓`.hermes-dev/web-recovery-20261024/`。证据简写：`F`=frontend/review-final-tests.log（12文件223项）；`N`=frontend/n01-final-tests.log（5文件113项）；`Q`=frontend/n02-n03-final-tests.log（3文件108项）；`I`=integrated-v4-tests.log（4文件52项）；`P`=presentation/frontend-final.log、cold-handoff-fix-final.log及capsule-baseline-review.log；`A`=presentation/android-final.log及ForegroundRefreshTest/AndroidBridgeStateTest/HermesBootstrapTest.xml（22+13+5=40项）；`B`=backend/rev10-final-tests.log（39项）、targeted-tests.log与native-stream探测；`V4`=verification-v4/。计数存在重叠，不相加。版本/影响复用边界见第4节，不冒称上述套件全部在当前候选重新执行。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| V4-01 | Controller.pageRecoveryOwner→ControllerPageRecovery→DisplayCache；既有REST/WS native seams | 阅读两仓冻结至候选的产品差异及新增模块；查独立展示DB/白名单、每轮实读、原草稿库独立 | controller.ts:172–175/487–527；display-cache.ts:4–276；F/Q；V4/version-audit.json | 符合；无第二SessionDB、通用响应库、持久事件cursor、BFF或写重放 | 认证展示失效单列32，不能以此结构符合覆盖N05 |
| V4-02 | ProfileEnvironment→Controller.select/owned；core/files→Files→authorizedFile | 静态追Profile、draftKey、transaction owner和fixed FILES_PROFILE；F/P跨Profile同ID、迟到/返回/deep-link | profiles.ts:13–46/86–132；controller.ts:715–779；core/files.ts；Files.tsx:36–76/159–236 | 符合；固定Files default集中一处；root/list/preview/download同owner，聊天cwd/附件/模型配置不重归属 | 保持08授权边界，无新Workspace或跨Profile历史权 |
| V4-03 | initialize/select/openConversation→attachConversation→summary存在校验→resume/activate；Files Back | F正式404不resume、回收runtime重新resume、New Chat不创建；读真实push/popstate、首发newCreate/idempotency_key | controller.ts:487–527/715–815/1120–1166；controller-page-recovery.ts:424–455；F/P | 符合；仅当前Conversation绑定；导航不发Turn/取消旧Turn，404安全退New Chat | 原本浏览器原生Back/Forward及阅读内存契约保持，不作设备手势实测 |
| V4-04 | retain/readCache→SessionList.refresh/read→present/commit→Sidebar | read重读每owner已加载offset页、并发独立accept、旧画面loading不假空；F/P列表分页和保视觉；Q成功proof | session-list.ts:17–77；controller-page-recovery.ts:226–247/329–349/644–651；App.tsx:699–765；F/Q | 符合；不first-page清掉屏内旧页，不批量正文/activate，缓存去运行字段，标题revision保护，更新无整列表清空 | auth错误传播是32/N05，列表正常成功行为与缓存写时机本身已修 |
| V4-05 | initialize/select/gateway.ready/online/visibility/Android→start→PageRecovery.run | 逐入口读正式接线；F/N/I实际Controller/App；唯一Coordinator且同owner/connectiondirty合并 | controller.ts:487–527/715–779/1330–1358；controller-page-recovery.ts:117–129/176–186；page-recovery.ts:104–123；F/N/I | 符合；初次无validated亦恢复，不凭binding跳过，所有已登记资源安排，短触发不abort饥饿 | N05是已观察认证事实未清理，不能由主干统一推断所有错误已闭合 |
| V4-06 | PageOwner/pageOwnerKey→connection/context/resourceKey/cancel；Controller epoch/owner | F同epoch新连接、epoch换runtime、A→B→A与晚REST/IDB，读每资源version/current检查 | recovery-demand.ts:3–84；page-recovery.ts:61–155；controller-page-recovery.ts:187–198；F/Q/I | 符合；document仅内存、connection递增、recovery请求代次、demand仅实际依赖变化；正常delta不重启 | 已受理后台事务保原owner；对显式auth的失效漏接单列N05 |
| V4-07 | read/results→requirements/run→retryable-error/scheduleRetry/localFailure | F空数组/zero/unknown/取消、初次失败及局部1/2/5重试/离线隐藏；I图片503自动重试；失败结果不当ok | page-recovery.ts:139–250；usage-view.ts:71–129；HistoryImageReader.read；F/Q/I | 符合通常读取结果与自动重试；retained不使required成功，撤需求解除慢读 | auth不应作为通常503重试，32/N05独立阻断 |
| V4-08 | resources→reconcile→commitId→App/reading/Files layout→acknowledgeCommit→ready | F/I正式App冷/暖/迟mount/local commit、P读锚点、Q菜单/侧栏门、I图片门；亲读ready条件 | page-recovery.ts:158–215；controller-page-recovery.ts:560–568/680–699；App.tsx:685–707；Files.tsx:214–223；F/Q/I/P | 符合当前可见依赖与显示commit屏障；backgroundSettled单独，不等隐藏慢请求/Turn结束 | 普通隐藏失败不挡ready正确；认证失败的全document例外未接，32记违规 |
| V4-09 | B:GET messages→_get_recovery_messages→selector/read_view/project_view；readRecoveryHistory | 真FastAPI+SQLite latest1400仅转200、任意assistant深anchor仅5；400参数冲突、旧接口完整保持 | B:hermes_cli/web_routers/sessions.py:788–890；hermes_state_recovery_view.py:24–45；tests/hermes_cli/test_recovery_view.py:37–148；B | 符合；新路径完整cards、有界200/≤500，非human-only around，无缓存版本省正文 | 原旧REST默认500兼容；新恢复latest200 |
| V4-10 | read_view._read_window→project_view coverage/digest→HistoryWindows.accept/replace | 查first/last/邻居/order/position/returned/total，SHA256规范cards；REST/RPC真实fixture逐字节一致 | B:hermes_state_recovery_view.py:139–277；history-coverage.ts:12–58；V4/version-audit.json.fixturePair；B/F | 符合owner、lineage/tip、窗口证明与独立detail_digest；前端仅本轮内存索引 | 图片引用沿既有确定授权路径；digest不代替跨资源全局事务 |
| V4-11 | resume能力宣告→attachConversation→REST receipt→activate recovery_view→parse_request/activate_payload | 后端正式handler/契约测试、前端原生fixture；最多2窗≤500/detail≤12，matched服务端重读，否则全窗replace；legacy显式失败 | B:tui_gateway/recovery_view.py:22–51/327–387；server.py:3047；controller-page-recovery.ts:455–525；B/F | 符合；能力协商后发新参数，receipt源于本轮REST，不静默裁可见字段；更多facet通过后续12批处理 | legacy保旧能力，但不被当新版一致恢复交付通过 |
| V4-12 | B:session.events.since→event_replay.read_replay_cut | 读同锁复制bytes/events/latest/truncated/epoch、锁外解码；真实并发stamp及读间stamp测试，旧字段不删 | B:event_replay.py:133–143；methods_session.py:2193；test_tui_gateway_event_replay.py:192–325；B | 符合；事件与watermark同原子cut，无latest虚水位 | open_requests保持独立原生snapshot，未宣称DB共事务 |
| V4-13 | B:read_view→_snapshot同conn→lineage/display CTE/bounds/details/identity | 读真实只读BEGIN实现与SQL；第二连接append仍旧snapshot、multi-lineage/UID退役/branch/旧identity、深窗payload计数 | B:hermes_state_recovery_view.py:47–255；hermes_state_timeline._snapshot；test_recovery_view.py；B | 符合；先身份顺序后有界payload，不SELECT *物化全部历史；读不补索引/写身份，投影在事务后 | legacy身份回退可在SQL读取必要展示字段，非Python整库正文镜像 |
| V4-14 | B:activate attach→_capture history_lock→D0→snapshot S→D1→release→project | 真实history锁250ms timeout、DB/replay/global resume锁不嵌套断言；短读与投影计时独立 | B:tui_gateway/recovery_view.py:113–156/289–298/358–387；inflight_output.py:97–114；B；backend/read-timing.json | 符合；不拿写锁、网络/图片/投影在锁外，目标锁有界等待不终止Turn | read36.8ms/projection117.6ms为本机1200行样本，非SLA |
| V4-15 | B:_proofs/_same_history/_coverage→activate最多两次；前端attempt<3 | 真独立进程正式replace/rewind/压缩/delete与独立连接append；重复改写失败、append超窗coverage_gap；非单锁假竞态 | B:tui_gateway/recovery_view.py:60–64/159–169/278–322；tests/tui_gateway/test_recovery_view.py:97–163/403–414；controller-page-recovery.ts:465–485；B | 符合；旧区间字段/身份/顺序、lineage/rewind被破坏不得接受；正常append可有限完成 | 持续破坏可失败退避，不为5秒放松证明 |
| V4-16 | B:_native_source/_turn_context/_turn_proof/_clean_snapshot→D1身份/lease | B39活动真实source db/UID/row/holder、工具occurrence、稳定rewind/replace/delete旧idle尾；正式loopback SSE活动及终态probe | B:recovery_view.py:87–113/172–276；backend/rev10-native-stream-probe.json、rev10-settled-proof.json；B | 符合；D1持久代表优先，退休UID不复活；未持久输出有当前Turn租约/source；外部owner缺输出明确runtime_unavailable | 模型网络是本机合成SSE而非真实供应商；真实native gateway/DB/lease链未绕过 |
| V4-17 | snapshot+read_replay_cut→validateEnvelope/installCut→suffix/held→正常event | B ring截断/持续delta/epoch；F完整suffix/held逐序、溢出及新owner；查4096/8MiB上限 | controller-page-recovery.ts:165–173/526–558；B:recovery_view.py:300–318；F/B | 符合；先snapshot再有限B逐seq，B后held有序续接，不跳游标、不等流静止 | 真实缺口明确失败重建，不能以纯assistant回退 |
| V4-18 | Controller.event→observeControl→held；reduceProjection与cursor独立 | 查业务观察先执行、replayed不重复effects，staging仍重新reduce；F审批取消即时、held正常delta不漏、通知原去重 | controller.ts:1168–1236；controller-page-recovery.ts:148–163/526–558；controller-event-effects.ts；F/N/B | 符合；控制观察去重与投影水位分开，恢复中不暂停安全事件/受理/通知观察 | 非HTTP认证安全事实传播另N05，不能被此事件结构符合掩盖 |
| V4-19 | session.info/Framework/complete/sessions.changed→startRecovery→writer通知/watcher | 沿原正式writer逐项：rewind_count、replace/user edit通知、delete行集合、compression计数/lineage、事件；真实跨进程Profile信号测试 | controller-event-effects.ts；controller.ts:1168–1207/1302–1324；B:history_notifications.py；change_watcher.py:125–207；B/报告backend | 符合；当前历史合并重读，不全库正文或任意DBmtime轮询；同数替换不漏失效 | 外部裸SQL不属支持实时writer；best-effort信号不是一致性版本 |
| V4-20 | useTimelineReading.reportDemand→viewport/facet→PageRecovery.setDemand→reader key | P/F滚动/展开/收起/离屏与staging详情；I图片真实viewport unknown/visible/hidden，旧读代次current | chat-presentation.tsx:169–188/313–334；page-recovery.ts:61–79；controller-page-recovery.ts:405–423；HistoryImage.tsx:25–86；F/P/I | 符合；DOM旧画面可登记，无须新projection先mount；离屏撤阻塞、进入局部校验 | 几何测试受控，真实连续视觉留Validation |
| V4-21 | HistoryWindows loaded/verified/invalidate/view；readWindows深anchor；loadEarlier | B1400行深anchor、F/P多窗/邻接/重叠/旧页；查普通loadEarlier同recovery helper、按anchor before200 | history-coverage.ts:12–59；controller-page-recovery.ts:512–526/689–706；B/F/P | 符合；不offset追赶，不合新旧offset；旧隐藏窗后台验证且不回盖当前主投影 | loadEarlier以首窗口或显式gap边界的持久身份定位；不从offset=0下载深处间隔 |
| V4-22 | visibleWindowCompatibility→timelineSourceIdentities/timelineVisibleSignature→reconcile | F有序A/B重排、同UID正文/Thinking、tool aliases、expanded facet、左界变化；缺/歧义输出verified=false | history-coverage.ts:61–124；presentation-signature.ts；controller-page-recovery.ts:560–568；F/P | 符合；先边界身份对齐再有序可见签名，不仅ID；未证明不冒称已删除/前缀破坏 | 局部有界前缀结论不声称整个Conversation前缀证明 |
| V4-23 | index.clear→current verified view/gaps→TimelineMessages分页控制→reading handoff | 查非相邻窗显式gap、旧未验证中间页不进入新view；P/F深anchor/tail及local延迟motion证据 | controller-page-recovery.ts:478–490；history-coverage.ts:38–58；App.tsx:138–146；chat-presentation.tsx:252–310；F/P/I | 符合；gap非消息，保anchor DOM/offset，不填全历史，准备/局部提交不取消合法一次motion | ready不等非可见页/240ms运动；实际顺滑度仍独立Validation |
| V4-24 | profiles resource→roster/nativeLaunchProfile；defaultCwd→ProfileEnvironment；protectTitle | F roster失败/初次未validated/不可用Profile、New Chat配置、metadata及title revision；读实际路由权限 | controller-page-recovery.ts:268–301/321–325/392–396/424–454；profiles.ts；F/N | 符合；每轮校owner，失败不授创建权限；chat不等无关default cwd；旧标题不回滚新事件 | 普通读取失败事实保持；认证被字符串化的同类风险由N05整改要求覆盖 |
| V4-25 | usage resource→UsageReadFacts；pending resource→native snapshot；compaction→context | Q原生Session/Latest scope及HTTP失败/unknown/zero，F pending/approval即时，I实际胶囊/Context；读contextRevision与不兼容窄退役 | controller-page-recovery.ts:351–380/572–607；controller.ts:1914–1941；usage-view.ts；F/Q/I | 符合正常需求与安全运行态不缓存；另一scope后台，合法unknown非失败，已知不兼容先失效 | 各reader明确认证失败清document问题不在此行关闭，见32 |
| V4-26 | secretary/schedules/compaction registered→readSecretary/readSchedules→Secretary open需求 | 查Orb和panel字段、本轮shared响应真实成功/错误；F/N/P开关与慢面板撤需求 | controller-page-recovery.ts:359–380；controller.ts:1822–1875；App.tsx:841–849；F/P | 符合；可见字段本轮重读，未展开表正文不阻塞；不将shared响应伪拆成成功 | 本轮未改Scheduler产品/后台Noting契约，不扩审07并行任务 |
| V4-27 | facet rows→selected staging history→detail batches12→commitHistoryView | 查staging无React effect依赖、detail精确UID/row匹配、数量/未deferred校验；F/P失败/取消/过时rewind | controller-page-recovery.ts:405–423；HistoryDetails；F/P；B details bounded tests | 符合；真空与未加载/失败分开，可重试，旧详情不复活被替换行 | 正常交互原hydrateDetails保留；HTTP认证传播需纳N05全reader边界 |
| V4-28 | Files registered files-current→default-cwd→list/read-text/authorizedFile→preview stage/renderer→layout ack | P/F不同owner/text/blob/目录、renderer失败明确阻断、初读与online；查Files root/path/preview resource key与Abort、真实blob重取 | Files.tsx:46–76/159–223/259–270；FileViewerPreview.tsx；files-profile.test.tsx；file-viewer-recovery.test.tsx；P/F | 符合通常Files完整重读及失败ready边界，不旧ObjectURL当新结果，不下载隐藏文件 | binary认证401丢typed信息的静态路径同N05；本行不称认证安全全通过 |
| V4-29 | recoveryResourceRules/register→expect files-current；组件动态image/Files→same page owner | F故意漏files reader及重挂/代次；I真实App图片503、解码失败、同URL、自动重试/局部屏障及隐藏慢图 | recovery-resources.ts；page-recovery.ts:82–96；controller-page-recovery.ts:114/321–403；HistoryImage.tsx；F/Q/I | 符合需求登记扩展机制，非仅源码字符串/allSettled断言；图片N04已接正式入口 | 每个新增reader仍须明确认证事实处理，不能靠普通resource契约免除N05 |
| V4-30 | DisplayCache keyFor/sidebarKey→displayRows/displayCapsules/displaySidebar | Q fakeIDB、禁binary/runtime/审批/command/流草稿、旧side字段读过滤；核origin scheme/有效port与APK真实https origin | display-cache.ts:4–137/200–225；MainActivity.kt:112–139；Q/F；V4 audit | 符合独立DB、owner-key、白名单及≤200持久cards，未确认owner不借default | Inline image binary存在时跳过Timeline缓存，保胶囊；不缓存Blob |
| V4-31 | validate/get/queue/flush→TTL/LRU/容量→内存降级 | Q真fake-IDB transaction quota、损坏capsules/rows/schema/TTL7天/10条/超2MiB；源码核总16MiB与side500/1MiB | display-cache.ts:138–276；display-cache.test.ts；Q/F | 符合；超大整窗跳过无假截断，存储失败不挡网络，无缓存不假空 | 不承诺浏览器存储耐久或离线同步 |
| V4-32 | 成功proof→commit/layout/ackDisplay→cache；authenticationFailure→clearSensitive，但SessionList/图片HTTP绕过 | Q N02成功侧栏待layout、隐藏晚到、失败TTL/旧proof/owner；Q N03冷cache/迟IDB/旧RPC不复活。独立V4侧栏visible/hidden401与App图片401三反证失败 | controller-page-recovery.ts:100–106/249–263/644–699；session-list.ts:54–58；history-image-recovery.ts:57–58；api/files.ts:17；Q/I；V4/auth-counterexamples.log | **违规N05**；成功写入/Context/404/IDB分支已修，但HTTP明确401被普通Error或非required路径吞掉清理语义，敏感rows仍2且cacheAuthorized=true | 503保留是允许行为；仅明确认证401已反证，真实文件403须保持域错误，不能一律登出 |
| V4-33 | cloneDisplay/present/retain/commit→RenderStore→App layout | 亲读structuredClone与visible/source/staged隔离；F可变binding mutation不泄漏、N菜单proof invalidation、I图片新stage不借旧commit | controller-page-recovery.ts:43–52/203–247/680–699；render-store.ts；F/N/Q/I | 符合不可变展示/业务即时安全覆盖主干，单commitId发布，Timeline不重挂 | N05是未收到明确认证失效的安全清理，不因隔离结构正确而豁免 |
| V4-34 | useTimelineReading anchor/layout→handoff tick→输入cancel/late children observer | P43与F/I实际App冷有/无cache、暖motion/local、growing tail、人工取消/reduced；阅读source逐分支核 | chat-presentation.tsx:151–365；recovery-handoff.test.tsx；app-page-recovery.test.tsx；P/I/F | 符合约240ms有限时长到真实末尾，不被following/ResizeObserver抢位，用户取消不重播，layout后ready不等动画 | jsdom受控几何只能机制证明，真实视觉由下一门禁检查 |
| V4-35 | Utilities→UsageSummary/ContextIndicator→useValueUpdateHighlight→theme animation | 查规范实际显示字段签名、hasData首次baseline、owner/scope/open重建；P/I同值/连续/真实变化/降动效 | App.tsx:359–435；indicators.tsx:16–34/90–101/126–143；theme.css末10行；P/I | 符合120ms亮+480ms淡、600ms内合并；不变真实open/selected、布局/Timeline，不以observed_at或引用触发 | source/window/估算信息仅按实际展示字段变化参与，不以网络次数制造提示 |
| V4-36 | UsageViews/usage-counters→native saved anchor/API→Utilities→context retirement | Q/F native counters/zero/unknown/Latest完成Turn、cold估算；N03 model/provider/rewind窄退役及晚IDB/RPC/seq不复活、合法unknown保持 | usage-view.ts:30–129；usage-counters.ts；controller.ts:1237–1250/1914–1941；controller-page-recovery.ts:572–642；Q/I | 符合；不差分造统计，不新API；普通append/compact保合法估计，known model/rewind失效直至新可信读 | N03原问题独立闭合，未把所有运行缺字段当失效 |
| V4-37 | AndroidBridgeTrust/parser→MainActivity packet→ForegroundRefresh；JS bridge→same start | A40/JS桥，检查trusted https主frame/文档/native/recovery/demand；hello非ready/health仅存活；网页无bridge零行为 | api/android-health.ts；AndroidBridgeState.kt:6–91；MainActivity.kt:75–139；ForegroundRefresh.kt:97–139；A/P | 符合身份与信任机制；当前轮必须先recovering再对应ready；onPageStarted清旧document | C17实际WebView运行未验；原生不替代上游页面依赖正确性 |
| V4-38 | resumed/startRecovery/hello/recoveryState/checkHealth/reload | A22逐例4.9秒+心跳、5秒硬deadline、online/resume合并、无JS/旧包、10/15/20/30及新前台重置 | ForegroundRefresh.kt:42–137/192–217；ForegroundRefreshTest.xml；A | 符合单调固定5秒，等hello/owner切换不续期，connected不清deadline，超时先赢；首开不多reload | Robolectric证明native状态机，不冒称实际后台生命周期 |
| V4-39 | ActivityResults/外部auth→ForegroundRefresh；NavigationMailbox→JS target navigate→owner ready ack | A相机/file ActivityResult registry、external page、通知target/mailbox/HermesBootstrap；F等待目标React ack | ForegroundRefresh.kt:42–81/141–182；AndroidBridgeState.kt:130–150；MainActivity.kt:70–107；controller-page-recovery.ts:102–108/141–147；A/F | 符合保护与通知目标保持；当前页ready只允许派发，目标owner完成才清目标 | 未实际登录/摄像头/通知点击或设备验收，C17豁免明示 |
| V4-40 | frozen diff/分包报告→sibling集成→冻结十检查→build/push事实 | 读适用AGENTS/README/CLAUDE/index/baseline/plan及三包报告，核无生产/模型/设备操作，现有呈现/Pin/原生写入语义差异未改 | B/主仓AGENTS；reports三包；review-staged-ten-checks.log；V4/version-audit.json；两仓HEAD | 符合过程/范围与阈值保持；facade2518行低于原2556，新模块分离；他人dirty未纳本轮产品 | 普通继承回归不等于全部历史重验；身份认证语义当前N05另阻断 |
| V4-41 | R10矩阵→真实DB/native/replay→Controller/App协议fixture→原生单测 | 独立读测试底座和预期，核B真实跨进程writer、有限delta/lease、F有界/失败/demand/owner、Q/I影响补证、A时限。V4新反证暴露auth漏接 | 第4节版本审计；tests/hermes_cli/test_recovery_view.py、tests/tui_gateway/test_recovery_view.py；F/Q/I/P/A；V4/auth-counterexamples.log | 符合验证方法和范围覆盖职责；不把helper绿测或大量计数掩盖N05失败 | 本行评价证据方法，不声明所有能力通过；Web用户结果尚须独立Validation |
| V4-42 | npm android:build内置dist→signed APK→资源逐SHA；C17实际运行豁免 | 独立读取当前APK32086913字节、SHA256 027a411c…539254，unzip439个assets/secretary逐SHA与dist一致、无mismatch；签名v2日志与build | apk-v4-manifest.json、apk-v4-signature.log、android-build-v4.log；V4/version-audit.json | 符合本门禁构建及验收边界；真实APK仅用户明确豁免/未验，不启动模拟器；R8单测仍适用 | Web实际结果是后续Validation及最终交付条件，尚未完成、不由本行或构建冒称通过 |
| V4-43 | native messages→sourceTimeline/reconcileLiveHistory→MessageSlot/Disclosure/temporary；全局activity | 核恢复差异未改真实role/content/UID、原wrapper/display_kind/terminal规则、64px/Pin/approval/patch表现；B cards46/timeline6/inflight/terminal回归与F/P | projection.ts（本轮未改）；App.tsx:138–350；controller.ts；session-recovery.ts；B/F/P | 符合继承消息及呈现保持；无伪历史/terminal提示，Thinking/tool/Reminder/Framework/临时slash仍原语义，人工阅读不被正常delta强拉 | 无真实供应商调用/新模型摘要证明要求；实际视觉仍由下一门禁 |

## 4. 核心目标及验证方法审查

**全范围43条，42符合、1违规（V4-32/N05）、0证据不足、0整项不适用。门禁不通过，不进入Validation。** 实际APK运行子场景是C17用户明确豁免／未验；它不使R8机制、原生单测、签名资源或Web实际结果要求失效。Web实际操作属于随后独立Validation及最终交付，当前未宣告完成。

核心纵向路径已经正式落实：唯一恢复owner→roster/原生存在校验→当前Conversation有界REST完整receipt→activate D0/S/D1和native source/lease证明→完整输出snapshot与有限cut后缀/held逐序对账→不可变可见commit→React锚点/Files采用确认→ready。持续delta不要求结束；深anchor和tail可以分窗且有真实gap；隐藏旧页及未展开内容不阻塞当前。R5领域reader、Model/Thinking菜单、Files渲染、历史图片均已进入同一协调器。当前核心安全缺口是认证失败事实无法从部分正式HTTP路径抵达全document投影清理。

反证与测试依据审查：

1. 失败与合法unknown/zero的区分由R1/R5、§1.13直接要求。Q/F真实Controller `UsageReadFacts`、补充HTTP503、当前scope选择证明不是“Promise完成即成功”。图片503/解码失败正式App路径由I覆盖。缺失reader测试通过实际撤掉files-current观察未满足，不是源码字符串断言。
2. 历史一致性依据R2/R3，B通过真实FastAPI/SessionDB/handler，并在D0/S/D1选定时点驱动独立进程正式replace/rewind/archive_and_compact/delete、另一连接append。wrapper只控制并发时点，不假SQL/假内存writer。源码核DB/replay锁不嵌套与250ms等待，持续native stamp可有限返回；read/projection分别计时。当前native SSE证据使用正式Dashboard WS/REST/真实native Turn/SQLite/租约，只把供应商替为回环合成SSE，证据明确外部模型调用0。
3. 所有reader成功仍可能错误处理认证。V4依据原V4-32主动反问：明确401如果发生在SessionList包装或隐藏资源／图片blob路径，是否调用clearSensitive？三个实际反例均失败。可见side phase=retryable-error、隐藏side phase=committed、图片phase=retryable-error；三例retainedRows=2且cacheAuthorized=true，图片仍blob:attachment-1。隐藏side未模拟React ack，不能冒称其ready=true，但已观察该认证事实未取消恢复/缓存资格。此前直接调用authenticationFailure的绿测试只证明helper，未证明HTTP正式接线。重复一次探针仅为补精确状态日志，未扩无关套件。
4. Q/I已覆盖N02/N03/N04修复影响：侧栏必须精确成功proof与实际投影/layout相匹配才写，失败/旧resource不续TTL；已知不兼容Context窄失效且迟IDB/RPC/旧seq不能复活；图片当前viewport需求、同URL本轮授权GET+decode、成功stage经full/local commit采用，hidden慢不挡、owner/StrictMode及URL释放有机制证据。没有以旧缺陷清单代替本次全范围审查。

证据版本与复用：

- 本审查开始及独立反证均固定主仓06dc95c168dbeb0f8cb5fead0f597173176b073d／Web474cd4f61d6fe7b29917cdd07fb3f4f647401265，产品只读。E/V4/version-audit.json记录逐源码SHA、探针SHA与两仓HEAD；主仓产品仍dd9a4c5等价，文档/07/运维等他人dirty未改。历史报告前133452字节的SHA256仍6ccf49af8675d7f3f3e2773c9d4fb3e9488bc5fe44b1c6a884a035482e623b78，逐字节保留。
- integrated-v4 manifest24/24匹配，Q的modified+observed16/16匹配；图片早期manifest16项14同，改变的adapter/cache由Q及当前I52补集成。frontend/source-manifest27项25同，App及App测试由当前I代替；N01早期11项5同，未把N113整体冒称当前重跑，配置机制与后继adapter/controller修改按Q/I及源码差异核。post-verification13项10同，差异由Q补；P最早26项17同，Kotlin/JS桥/Files/preview/theme/signature未改可复用；reading/indicator后续manifest与P43、baseline及当前I补足影响。
- backend REV-10 manifest11项10同，唯一不符为动态plan文字；10项产品/测试/原生依赖匹配，B39有效。其余未改接口复用replay17、watcher2、cards46、timeline6、原inflight14及terminal21、通知4、生成契约精确一致1的各自日志，不合计总数。catalog孤立旧review.summary在冻结树同runner已复现，仍属范围外旧失败，不称全仓绿。
- A三XML测试数22/13/5、failures/errors/skipped均0；Kotlin/bridge源码与P manifest匹配，复用有效40项，不为审查重跑Gradle。APK独立读取32086913字节，SHA256 `027a411c5aeb1d0d44a93750a4da4274f95debc528438a17a448085c88539254`，439内置资源逐SHA匹配dist；签名日志v2有效、公钥指纹保持，build含tsc/Vite与正式Android构建。没有安装或运行APK。
- 本次只新增认证定向反证（2文件3项失败，另14个从底座拷来的非目标测试通过filter未运行），未复跑无关大套、未UI/生产/设备/模型/提交。真实用户画面连续、动画观感和Web断线结果仍需在门禁通过后独立Validation，不以jsdom几何或native单测替代。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| N05 / P1 | V4-32；冻结06 R6“退出／认证失败时停止展示敏感缓存并清本document投影”；session-list.ts:54–58、controller-page-recovery.ts:100–106/249–263；history-image-recovery.ts:57–58；api/files.ts:17 | 正式Controller冷读成功后online侧栏GET /api/sessions=401（sidebar可见／隐藏）；实际App已展示图片后同URL下一轮GET=401。三例均保两条敏感历史且cacheAuthorized=true；图片仍blob旧源。SessionList将RpcError字符串化，图片/authorizedFile转普通Error；隐藏错误不触发required失败回调 | 认证失效事实未抵达已有cancel/stop/clearSensitive；直接helper测试绿不能证明正式读路径。缓存及retained不能在明确认证失效后继续展示，范围内阻断 | 主会话统一传输观察提案见§6。关闭须正式visible/hidden侧栏、图片、Files blob401清敏感投影/取消proof且迟到不复活；503仍保留可重试，真实文件403不登出；旧token/已取消请求401晚到不清新身份 | 当前474cd4f已反证，未修；V4/auth-counterexamples.log 3失败；方案原则已认可，待新候选全新全范围复审 |

范围外：旧catalog `review.summary`孤立事件失败有冻结树同runner复现，保持历史，不扩为本轮整改。未发现需改变产品语义、权限、完成条件或重新冻结的其它事项。当前N05属于既有R6明确要求的接线遗漏，不能通过弱化“认证失败”原判据关闭。

## 6. 修复与独立复审

本审查全新独立v4，完整读两个必读Skill，先仅据冻结原文+C17建立43条判据并落盘，交回约定里程碑，后读适用指导/索引/baseline/plan/源码/证据/旧报告；第2节判据未变。报告六节与表列保留，旧三轮133452字节原样；本次未退回补审。产品在全范围审查期间冻结，未在原候选移动后偷用旧证据。

旧问题独立关闭复核：V01当前scope补读失败不假ready；V02普通有效Usage/Context成功事实可合并白名单缓存、失败不续TTL；V03/ N01实际Model/Thinking共享reader、配置观察早于held时失效旧proof、成功本地配置同入口；V04/REV-09晚mount及同轮local commit不抢滚尾；REV-10当前原生source/UID/lease证明真实普通Web Turn；这些正式路径与当前影响证据均已核，没有重开旧问题。

| 研讨/复审项 | 原判据与初步发现 | 主会话提案及理由 | Verification评审/是否改变规格 | 实现版本与关闭证据 |
|---|---|---|---|---|
| N02旧项 | 原v3 R6只成功对账且展示数据写；本次原V4-32保持 | 精确sidebar rows/roster/context成功proof，当前投影匹配且ready/layout后写，hidden晚到独立成功不挡ready，同owner重取作废旧proof | 原R6方向保持，无规格变化；独立读当前实现/失败TTL/迟到/同owner反例 | 474cd4f；adapter sidebarStage/acknowledgeDisplay，Q108及I52匹配版本，原N02关闭 |
| N03旧项 | 原v3 §1.13/R5/R6 known model/provider/rewind失效；本次原V4-25/32/36保持 | 已知失效窄覆盖Context，其余Timeline/anchor保留；fresh仍统一commit，冷cache身份确认及IDB/旧RPC/seq防复活 | 原判据保持，未知identity/普通append/compact不清合法估计；未增新产品失效规则 | 474cd4f；contextRevision/retireContext/UsageViews.observeIdentity/cache revision；Q108/I52及当前源码，原N03关闭 |
| N04旧项 | 原v3通用恢复组件reader；本次原V4-20/28/29保持 | App传唯一recovery及scope，真实viewport图片登记，授权GET+decode、stage经full/local commit采用，自动重试/hidden/owner/对象URL清理 | 与R1/R4/R5/R7一致，非新整页循环；不等所有图、不以remount恢复 | 474cd4f；HistoryImage+HistoryImageReader+App正式props；I52与当前图片源码匹配，原N04普通失败/重连/呈现机制关闭；其HTTP认证传播另记新N05 |
| N05本轮新项 | 原V4-32及R6；三条正式401反证失败后先落报告再反馈，未改判据迁就实现 | 主会话亲读后端鉴权/文件拒绝路径，提在现有HTTP传输观察点统一通知明确认证失效，Controller订阅后cancel/stop/clearSensitive，不依required失败/typed错误穿层；rest/authorizedFile/图片/其它正式读取共用薄helper，保业务错误，非新恢复循环 | 认可原R6内工程方向。明确同源API认证401触发；bootstrap403有明确认证来源可保留，真实files权限403是域错误不能一律logout。通知需带document/请求凭据代次资格，解析包装前处理，先失效恢复/待写proof；取消旧请求或旧token迟到不清新身份，旧IDB/RPC/图片不得复活；重新授权须新成功身份确认，旧roster迟到不能自解锁。无规格变更 | 当前474cd4f未修，N05不关闭。关闭要四类正式reader401、503/403对照、迟到新旧认证、缓存/RPC/image stage复活反例及新候选全新全范围Verification；认可提案不是实现通过 |

供final-delivery.md与主会话最终汇报的实质收敛：N02/N03/N04在本候选已由当前证据关闭；本轮全范围新发现N05，必须从正式HTTP认证事实传播到已有document清理，hidden与错误包装不能绕过，文件权限403须保持域语义。门禁不通过，完成报告后交主会话安排整改；不能直接进入Validation或把C17实际APK豁免扩成认证/ Web验收豁免。
