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
