# F1／F2／F3／I1 整包交回

状态：主会话已集成至474cd4f；最新N05认证整改包已完成，待主会话亲审、统一候选及同版本独立复审。下文保留各验证时点，本Agent未自行stage／commit／push，未部署、未调用真实模型、未操作浏览器／设备。依据为baseline.txt冻结06 R1/R4–R7/R9及R2/R3接口，保持08 Profile与Files归属。

## 条款与实际变更

- R1/R5：PageRecovery是Controller唯一恢复owner，冷开/select/gateway.ready/online/前台/Native均进入同一入口；初次失败独立按1/2/5秒重试。owner、connection、recovery及需求身份隔离；ReadResult明确ok/error/cancelled，合法空／zero／原生unknown有成功语义，真实错误不能由保留数据或Promise结束消除。
- R4：HistoryWindows按真实coverage索引有界latest/anchor窗口、明确gap和本轮验证状态；普通翻页用anchor并核邻接与重叠字段，冲突自动发起当前owner恢复。暖恢复不沿offset追赶深anchor，未展示旧页独立有界后台重读。未知alias不借空集证明前缀，当前live及持久工具facet复用展示层同一签名核对。
- R6：独立IndexedDB secretary-display-v1，精确origin/profile/route，冷开缓存与网络并行；侧栏在精确已确认Profile候选边界内可先于roster显示。白名单、200行、2MiB/16MiB/10会话、侧栏500/1MiB、7天TTL、LRU、空闲合并写及schema/quota/corrupt降级。只保存持久展示身份/正文/附件引用、胶囊/列表摘要，剔除运行态、权限、temporary、工具/Thinking折叠正文、Blob/binary及未知嵌套；过大或不完整窗口跳过。网络成功且布局ack后才缓存本轮事实，旧IDB不能覆盖真值，失败保留计数不刷新成功时间。
- R7：保留业务state，以隔离的不可变display视图冻结/提交；可见资源成功与有限S/B cut连续对账后单次commit，React anchor布局ack后ready；后台慢不阻塞。需求撤除可唤醒等待，依赖变化重求集合；正常delta不递增恢复/需求代次。恢复后展开走local commit、不重冻全页。观察副作用和投影游标分别去重，hold有4096帧/8MiB上限、缺口明确失败。
- R8/I1：App接阅读hook、visible/facet、侧栏、胶囊、Secretary/Schedules和Files登记；Android使用唯一documentId，ready只取本轮布局ack；通知导航等待目标owner的实际ready后才完成/聚焦。胶囊签名限实际展示字段，首次真值与合法unknown明确建基线。
- 认证：正式bootstrap 401/403经Gateway专用回调进Controller，取消/停旧socket并清本document敏感展示，禁止旧缓存重现；原生roster再次成功才重新允许。普通断网/503不当成登出；现有前端无独立logout入口。

## 正式路径与接口

Controller.startRecovery → ControllerPageRecovery → recovery-resources登记表 → 领域RPC/REST → 本轮完整REST receipt → 正式session.activate recovery_view → 真实D1窗口完整替换/匹配＋snapshot S/连续suffix至B＋held后继 → staging → display commit → App/reading/Files layout ack → Native ready及展示缓存。既有发送/编辑/审批不自动重放。已回收runtime沿已验证stored locator重新resume。Profiles只New Chat可选；Files继续固定FILES_PROFILE，未借Files默认cwd给聊天。

主体逻辑落page-recovery/history-coverage/display-cache/controller-page-recovery/controller-event-effects等sibling；controller.ts从基线2556行降至2491行附近，未增加既有文件长度超标。详情公开方法保留既有取消兼容；可见恢复使用独立严格adapter，不从其fulfilled推导成功。共享接口最终说明见frontend-contract.md及presentation-contract.md。

## 验证证据

最终`npm run typecheck`通过，`npm run build`通过（Vite保留既有>500kB chunk提示）。最终17文件246项Vitest通过：本轮协调器/缓存/coverage/侧栏/正式Controller，加既有state/mobile/usage/details恢复及App/Files/阅读/JS桥/Bootstrap相关回归。覆盖撤除慢依赖、同资源换路径迟到、跨owner、旧IDB、冷缓存等待、同epoch完整重请求、有限持续delta与控制取消、matched/replacement/incomplete、合法空/零/unknown与真实失败、初次失败重试、dirty重读、commit后新需求local ack、工具-only/展开facet破坏、未知alias、深anchor gap、已加载侧栏页保留、runtime回收、认证401/403与断网区别、隐藏计数同值不闪、首次context数据不闪。

输入历史/封套来自后端真实SQLite＋正式REST/RPC fixture，前端`src/core/fixtures/page-recovery-native.json`与后端最终fixture SHA256完全一致；其他资源在正式Controller读取边界控制RPC响应、网络顺序与故障，未替换待测协调/投影机制。

ignored证据：`.hermes-dev/web-recovery-20261024/frontend/accepted-tests.log`、`accepted-build.log`、`auth-final.log`、`unknown-final.log`及`source-manifest.json`。早期失败和修复日志保留，不冒充最终结果。展示/Native独立包证据见presentation.md，不累加重叠计数。

## 缺口与边界

本包未运行实际浏览器UI、真实APK生命周期、设备、生产、真实模型或无关全量测试；jsdom/controlled RPC不代表实际平台用户验收。原生打包与独立Verification/Validation仍由主会话依本轮计划执行，未以本包测试替代门禁。旧后端能力缺失保留兼容读取与明确错误，绝不冒称v1一致恢复ready。

## 接口影响与下一步

仅增可选v1类型/参数、Gateway认证失败订阅、PageRecoveryPort及展示props；旧调用保持。Controller/App最终接线由本包完成。主会话亲读实际diff与上下游、确认本包和presentation/backend接口后统一快照；随后执行独立门禁。若后续代码修复，按source-manifest定位影响并定向补证。本包没有待跨包决定的产品歧义。

## 主会话亲审后定向修补（2026-10-24）

- R4/R7可见交接改为按实际展示窗口的左边界与有序连续前缀核对。定位同时使用节点kind、工具occurrence或持久别名；同一行产生的thinking/message不再混选。A/B重排为B/A、窗口中插入新节点均为已证变化，真正尾部append保持相容；缺少/歧义身份仍是未验证。共享展示签名继续覆盖已展开facet。
- R1恢复后局部required读取失败在已committed画面上公开error并按1/2/5秒自动重试，失败/cancelled结果不会复用为已完成请求；成功后产生可布局ack的local commit。不重新retain或启动全页冻结；撤除依赖、owner取消、隐藏/断网停止旧重试，正式online/前台入口仍按统一恢复执行。
- R6侧栏两个缓存读入口（精确roster及已确认Profile候选）与写入共用摘要白名单，旧/损坏条目额外running、runtime_id、status、turn_started_at、pending不能进入显示；访问不刷新真实successAt。

本次只改history-coverage/page-recovery/display-cache及各自测试，未改兄弟呈现/原生代码。定向机制3文件33项通过；受影响Controller正式adapter、阅读交接、Files回归3文件45项通过；同版本typecheck及git diff --check通过。此前17文件246项与build结果仍按原验证时点保留，未重复运行无关大套。

新增ignored证据为frontend/review-fixes.log、review-fixes-integration.log及review-fixes-source-manifest.json；source-manifest.json仅更新本次6文件SHA256，其余版本保持先前记录。没有stage／commit／push，没有浏览器、设备或部署操作。

## 独立审查及真实冷开整改包（c4f2f6d之后，2026-10-24）

本包对应Verification原判据G03/G10/G13/G15/G16与V01–V03，及主会话隐藏IAB冷开阻断；不自行关闭独立门禁。

### 根因与正式修补

- 冷开／缓存刷新：正式App＋Controller＋PageRecovery＋阅读hook反例证明完整commit后首DOM/Secretary需求产生local commit，旧hook无条件取消正在滚尾的handoff并从尚未定位的DOM反推following=false。presentation包独占修hook：同恢复轮的local commit保留合法motion及原240ms期限，人工输入仍取消，晚挂消息子树可重定位。其变更与证据归presentation.md，本包记录正式联合版本。另缓存改变viewport首身份后，旧context可把resolved undefined放进新selectionKey共享Promise表，afterBinding有效reader反复复用形成微任务循环；adapter现拒绝旧context发起共享读，取消／失败的共享结果撤除。相同联合fixture与act等待不改，修后通过。
- V01：UsageViews新增UsageReadFacts，明确scope/runtime/epoch/serial及detail/session各自ok/error/cancelled，原始fresh事实与保留展示分开。当前Session所需summary补读失败会使required reader失败并按1/2/5自动重读，不能靠detail fulfilled或旧总数ready；Latest只读取本scope所需明细，不等待隐藏Session补读。成功响应的合法unknown保持ok。旧readUsage兼容调用保持逐字段保留展示；恢复只消费显式读事实。
- V02：正式session.usage／成功Context读取把可证当前owner/epoch/代次的原始成功事实送入adapter。原恢复轮已布局ack时，核对已发布render projection；App另提供layout确认。新恢复／新可见需求仍须其当前ready；验证过的窗口从缓存原样保留，仅通过原白名单合并capsules，串行写防并发覆盖。失败retained、隐藏失败scope、旧owner／旧代次不写、不续successAt。纯local菜单commit不使正在合并的同owner成功统计失效；认证／切owner／完整恢复仍取消旧写。
- V03：实际受控Model/Thinking开关向唯一协调器登记capabilities/reasoning需求。model.options、commands.catalog与config.get均走带owner/runtime和覆盖代次的reader；删除独立吞错的useReasoningCurrent effect。菜单读成功暂存，当前可见所需配置齐备后随同一local/full commit接管；旧配置可继续展示，局部错误在App显示并自动重试。关闭慢菜单解除required等待，同连接online重新请求；native成功返回无value是合法unknown。显示字段纳入隔离projection，禁止谁先到就盖住当前菜单。
- 覆盖键A→B→A反例修前确实复用旧A慢请求；PageRecovery现仅对覆盖身份变化的资源推进代次，即使字符串回到A也不能恢复旧request资格。正常同身份stream签名变化仍不触发读取／代次。

### 当前证据与边界

最终受影响12文件223项Vitest通过；包括实际App6项（无缓存cold、冷缓存等待真实请求后刷新、兼容warm动画中新visible proof、人工取消后local不重播、真实Model开关／同连接恢复／慢隐藏、Thinking初读／失败自动重试／online）、正式Controller V01/V02反例、隐藏scope、Context成功、失败TTL／迟到owner、菜单联合提交，以及缓存合并途中local commit。Coordinator另有覆盖键循环反证的修前失败和修后成功。旧原包246项、此前33／45项保持各自时点，不累加为本次计数。

最终npm run build（含tsc -b）成功，git diff --check通过；Vite保留既有大chunk提示。controller.ts当前约2501行，仍低于冻结基线2556行；逻辑继续放sibling。未改presentation独占文件、后端封套DTO、drafts、依赖或Android文件。

证据：ignored frontend/review-final-tests.log、review-final-build.log；修前handoff-reproduction.log、coverage-cycle-before.log保留。post-verification-source-manifest.json记录本包10文件及实际受影响呈现／测试版本，source-manifest.json同步本包文件SHA256。主会话自行隐藏IAB已另复核1200行真实末尾（top28950、1199可见），本包未操作页面，此结果不替代独立Validation。后端普通Turn新修与APK豁免由主会话另行编排；本报告不扩作后端／APK通过证据。

下一步：主会话亲读本包接口、状态／失败／旧结果路径后统一新候选，交独立V2复审V01–V03及原全范围；本Agent没有stage／commit／push或部署动作。

## N01 菜单恢复交错整改交回（基于474a934，2026-10-24）

1. **对应条款。** R1要求已失效读取／成功证明不得满足当前ready，R5要求当前实际Model/Thinking菜单读取加入统一owner，R7要求完整可见交接。原V2反例的根因是session.info仅失效历史等资源，capabilities/reasoning已有成功结果及menuStages context仍合法；旧stage在新旁路响应之后随恢复commit回盖，出现ready=true但旧菜单。冻结规格及产品语义未改。

2. **实际变更。** 已知model/provider/reasoning_effort/reasoning_effort_wire变化在业务观察时进入configuration-changed，单次invalidate同时推进capabilities/reasoning与其余必要资源的覆盖代次，并推进既有capabilitySerial。旧stage保留但context立即无资格，不靠最后清stage遮盖问题；仍required的菜单必须取得变更后的真实读取成功结果才可同一commit。恢复中capabilitiesForBinding只记录scope，不另发可覆盖展示的旁路；已有恢复owner时公开loadCapabilities也委托同一入口，未建立恢复owner时的原调用保留，旧legacy串号仍拒迟到结果。当前owner成功且不需confirmation的本地config.set同样失效；普通delta不触发配置重读。

3. **正式路径。** session.info → observeControl按seq去重并比较已知配置字段 → startRecovery(configuration-changed) → adapter原子invalidate菜单成功证明＋旧串号 → 同一PageRecovery合并运行重新求required → 新capabilities/config.get暂存 → 完整/current local commit → 原App/reading布局ack。业务观察在held入队之前执行，投影重放不重复失效。成功setSessionConfig及当前owner显式Retry capabilities也复用此路径；旧owner结果没有当前展示资格。

4. **验证。** 修前两个正式Controller反例（Model与Thinking）均失败在旧context仍current，见ignored frontend/n01-before.log。最终5文件113项通过（n01-final-tests.log）：其中10项N01 Controller场景覆盖旧成功stage、变更后请求失败不ready和自动重试、实际held帧、本地配置写与正在恢复合并、关闭／切owner后的迟到结果、普通delta无新增菜单读、legacy旧串号；实际App新增2项用真实Model/Thinking开关和最终DOM验证重叠恢复，释放Pending之前不提前采用fresh菜单，之后必须fresh并ready。相关既有配置owner／Usage／恢复路径一并通过。npm run typecheck及git diff --check通过；controller.ts当前2512行，低于冻结2556行。精确版本见n01-source-manifest.json；source-manifest.json仅更新本次4文件。

5. **缺口与边界。** 依授权未重跑无关大套、build、浏览器、APK、模型或部署；此前223项及build只代表其原时点，本次不冒充当前打包／真实用户验收。受控依赖只位于正式RPC响应/时序屏障，协调器、Controller、held处理与实际App/reading均为正式实现。独立N01与全范围门禁是否关闭由主会话及审查者判定。

6. **接口影响。** 仅新增内部reason configuration-changed；未改公共DTO、PageRecovery API、组件props、presentation源码或其它文件。loadCapabilities在已有恢复owner时归同一协调器，config写返回与confirmation语义保留；不新增恢复循环，不沿每delta重读。

7. **建议后续。** 主会话亲读两个产品源码差异及上下游后统一新候选，用当前manifest交独立同版本复审；尤其核旧stage资格、新required失败与held/local顺序。原V2反例中旁路中途写入raw fresh的现象现被收敛，正式判据应核新读取证明与最终可见commit。未stage／commit／push，无待产品决策项。


## N02/N03 缓存写入与 Context 兼容失效整改（基于833d456，2026-10-24）

1. **条款与根因。** 已复读executing-plans、autonomous-run子Agent阅读／消息契约、本轮index/baseline/plan及冻结06 R5/R6/R7、§1.13。N02原sessions reader在真实读取完成后直接putSidebar，Pending仍延迟、旧render尚未交接时已经续缓存；N03只清业务Context，冻结的retained/visible仍显示旧模型10%。本包保留原产品规格与R6容量、TTL、LRU及白名单原则，不新增恢复owner或恢复循环。

2. **实际变更。** sessions严格读取精确roster、各Profile列表及活动事实，成功后只暂存白名单摘要与ReadContext。复用当前ready/layout-ack接缝，核owner、资源覆盖代次和published snapshot摘要签名后才putSidebar；隐藏慢侧栏不挡ready，晚到独立成功必须仍具当前proof且已发布才写。同owner重新失效会使旧stage context立即无资格；失败、retained或旧owner不续时间。整轮Timeline/胶囊pending cache也核当前Context/Usage成功证明及已发布投影签名，防ack间隙失效或更新的旧stage写入。

3. **正式 Context 路径。** session.info／原生显式context_invalidated在业务观察、进入held队列之前撤销当前Context代次；已知模型或精确provider失配立即窄覆盖retained/visible中的Context，保history对象、Timeline、其它Usage与锚点，当前required Context必须重新读。绑定初次确认也比较已显示缓存的model/provider身份；缓存先到时把身份保留在内存供稍后确认，绑定先到时过滤并清除不兼容缓存部分。旧snapshot、IDB、RPC和旧seq不能复活退役数值；新可信数字仍暂存至当前full/local commit。正常append、compaction、身份缺失、网络失败及原生unavailable占位继续保合法同owner估计；Thinking变化不算Context失配。原生通用路由标签custom（以及unknown/auto）不作为精确provider冲突证明，明确provider-A→provider-B会失效，与原已有通用标签兼容语义一致。

4. **缓存机制与证据。** DisplayCache.retireContext只移除Context部分，保Timeline/Usage及原successAt；guard和可选身份比较防旧清理删新证明。IDB读回在await之后按同key内存修订核对，包含新条目已经flush、queued已清空的时序；晚到旧读不得回滚新成功／失效。正常成功Context缓存合并同时携带当前已知兼容身份；缺字段或unavailable导致的保留估计不当成新成功写入。修前两项正式Controller反例均失败，见ignored frontend/n02-n03-before.log（提前putSidebar和仍显示10%）；最终三文件108项通过，见n02-n03-final-tests.log。新增21项（正式Controller 15项、Usage/Context 1项、缓存5项）覆盖：Pending＋ack屏障、隐藏慢侧栏／独立晚到／owner撤除、同owner重取旧stage失效、失败TTL、冻结model/provider窄失效、冷缓存先到／晚到绑定确认、完整required读与正常压缩Context读迟到、真实有限Socket cut后的旧seq、held rewind、合法missing/unknown/unavailable估计、普通断网、Context-only退休及IDB晚到（含flush后）。npm run typecheck和git diff --check通过；controller.ts为2518行，仍低于冻结2556行。源版本及证据散列见n02-n03-source-manifest.json，source-manifest.json仅更新本包7文件。

5. **缺口与边界。** 本次只跑获授权的三个相关机制／正式Controller测试文件与typecheck；没有重复无关大套、build、App联合测试、浏览器、APK、模型或部署。App/HistoryImage/presentation及app-page-recovery.test.tsx的工作区变更归N04，本包未修改；不以旧绿或兄弟证据冒充当前整候选门禁。额外修订记录是document内防旧IDB结果回滚的身份元数据，不写入缓存或扩大持久化容量。独立N02/N03是否关闭由主会话及Verification按原判据确认。

6. **接口影响。** 无公共DTO、PageRecovery API或组件props变化；仅adapter内部Context代次／窄退役接缝、统一摘要白名单复用和DisplayCache内部retireContext（可选current/兼容身份guard）。Controller事件控制路径先做明确失效，正常Context补读捕获同代次后才能采用；原scope、合法unknown/available和业务通知语义保持。未改App、presentation、后端、drafts、依赖或Android。

7. **下一步。** 请主会话亲读7文件正式diff及读→stage→commit/layout→白名单写、held/旧seq和身份失配上下游，结合N04统一新候选后交独立同版本复审。本Agent未stage、commit或push，无待产品决策项；当前验证不替代最终Validation。


## N05 正式 HTTP 认证清理整改（基于474cd4f，2026-10-24）

1. **对应条款与根因。** 已复读executing-plans、autonomous-run阅读／阶段交接契约、本轮index/baseline/plan，以及冻结06 R6与R1/R5失败边界；读取V4 §5/6的原判据与原三项正式反证。原问题是SessionList把HTTP 401字符串化，历史图片／authorizedFile包装普通Error，hidden错误也不进入required.failed，导致认证失效后旧history/sidebar/blob仍展示；原直接调用authenticationFailure的helper测试不能证明这条链。冻结规格未改。

2. **实际变更。** 全src正式fetch清单核实只有bootstrap、rest/patch、authorizedFile及HistoryImageReader四个传输点，现共用api/http-auth.ts薄接缝；仅mock fixture保留独立fetch。相同origin的/api明确401在body解析／领域包装前同步通知既有Controller；bootstrap明确认证403保留，普通Files 403是域错误，503／断网仍原retained和1/2/5重试。每次请求捕获document、当前凭据对象代次、取消signal及bootstrap attempt资格，通知携可复核current proof；旧token、同token但新bootstrap代次、取消请求和旧attempt不能清新身份。模块无恢复定时器、自动重发或认证协议；不猜redirect/TypeError，不记录URL、token、正文，不自行写cookie或制造token，token仍只由既有成功native bootstrap赋值。

3. **正式路径与清理顺序。** HTTP观察→current proof→撤销凭据资格→PageRecovery.cancel→静默撤销读取／待写proof、capability/secretary/schedule/draft代次→清document不可变展示和业务敏感字段、displayAuthorized=false→Gateway.stop。静默清理覆盖列表、历史／detail、Context、Usage、Pending及旧binding flight，取消过程不会额外发布旧敏感画面；晚到REST/RPC/IDB/menu/图片不能重新采用。当前成功roster还须其原始凭据proof有效，socket ready或旧roster成功都不能自行恢复cacheAuthorized；新凭据的真实当前Profile确认后才允许读展示缓存。主会话另批准的两处精确扩白名单已接：Files.tsx仅在displayAuthorized=false时清本地data/previewStages/accepted/等待者并卸载预览以释放其ObjectURL，普通cancelled断线不清；profiles.ts的既有load/loadDefault捕获同proof，防旧roster/cwd迟到resolved／发布。HistoryImage本体不改，reader只替换统一HTTP helper。

4. **针对性证据。** 当前9个相关文件134项通过（n05-final-related-tests.log），包含15项新增：传输观察2、旧bootstrap401/403两项、正式Controller visible/hidden sidebar与迟到proof三项、实际App同URL旧图片后401一项、真实Gateway＋Controller／挂载Files联合七项。联合fixture实际运行Gateway bootstrap DOMParser、WebSocket/RPC、Controller、PageRecovery、REST/authorizedFile与Files组件，只在HTTP响应、native RPC/事件和第三方viewer-ready边界供确定输入；没有替换认证／清理机制或手调helper充作正式链。证据覆盖：解析前清理、hidden包装不漏、取消先于stop、迟到cache/menu/roster/cwd/传统history/binding、跨真实bootstrap新凭据的旧无signal401、已取消401、bootstrap403、新socket ready但当前roster仍慢不能解锁；Files metadata/binary权限403保留、binary503不等新gateway.ready自动恢复、binary401清旧stage/URL且重新授权后仍等新二进制提交。另旧Profile目录owner定向1项通过（n05-profile-proof.log）。typecheck、git diff --check通过；Controller为2540行，低于冻结2556行。n05-source-manifest.json记录本包13文件及实际依赖、日志散列。

5. **现有失败与边界。** 扩大检查的未修改controller-profiles.test.ts有五项失败（含旧ensureBinding初始化断言、旧cwd/模型采用假设和一个超时）；已在独立临时源树对原474cd4f逐项复现相同五项，见n05-expanded-profiles.log、n05-baseline-profiles.log及n05-profile-baseline-comparison.json（sameFailures=true），临时树已清理，未回滚共享源码、未修改预期消除失败。本包不冒称该旧文件全绿，认证相关旧roster/cwd及当前授权则有上述正式新反例。未跑无关大套/build，未操作UI／浏览器／模型／原生／部署，未stage/commit/push。viewer用既有ready合同替身，实际第三方渲染和真实用户效果不属于本次机制测试结论。主会话同期自行升0.1.5；本包未改版本／依赖／原生文件，测试启动标0.1.4，最终typecheck标0.1.5，认证源码未随版本小集成改变。

6. **接口影响。** 新增仅document内HTTP观察／凭据proof helper；rest/patch/RpcError、authorizedFile原返回与领域错误保持。AppState新增可选displayAuthorized（undefined保持既有调用），仅明确认证失败false、当前有效roster成功true，供Files区分普通断网和认证清理。PageRecovery状态机、恢复DTO、server/backend协议、样式、容量／TTL／LRU、drafts库不改；Controller内部invalidateDisplayReads只撤销读取与cache proof，不发送／重放写操作。新增源文件为api/http-auth.ts，新增测试为api/http-auth.test.ts和core/http-auth.integration.test.tsx。

7. **建议后续。** 请主会话亲读13文件、明确401的传输资格、静默清理顺序、重新授权proof及Files本地stage清理；版本0.1.5由主会话统一候选／构建后交全新独立同版本Verification，再决定Web Validation。原V4三项失败证据保留，本包通过不自行关闭门禁；无待产品决策项。既有五项Profile测试差异另有原候选对照，不夹带改行为或改断言。

## VAL-01／VAL-03／VAL-04 集中整改（基于0eef280，2026-10-24）

1. **条款与根因。** 按executing-plans及autonomous-run阅读／交接契约恢复本轮index、baseline、plan、Validation完整六节和Verification末尾原判据评审，依据冻结06 §1.3、R1/R5/R6/R7实施，未变更产品规格。VAL-01的正式initialize在Gateway.connect成功后才retain/readCache，WS阻断时已有IDB没有启动展示；VAL-03的retain撤去active，New Chat完整成功commit未建立该owner无Session／Turn的idle事实；VAL-04的正式GET未指定HTTP缓存策略，同URL可直接返回浏览器缓存，ObjectURL变化不能证明本轮实际重取。ENV-02夹具与EVID-01用户证据缺口不作为本包产品改动。

2. **实际变更。** 仅三个产品文件：ControllerPageRecovery.prepareDisplay在初始化订阅安装后、await connect前并行启动原白名单cache读取，保留同一owner的retained快照；后继retain复用已显示的retained，避免握手／开始整轮恢复时被旧空visible抹掉。无cache／坏／过期／不可用cache均维持Conversation loading，不伪造空历史。New Chat仅在当前统一commit、无binding／sending／创建或发送事务时建立自身emptyLive＋active=false/status=idle；移除select在必需读取成功前提前设idle的一行。统一HTTP helper对同源/api/ GET（含显式get）强制no-store，写请求、静态资源、跨源请求保持原cache选项。

3. **正式路径。** 实际App effect→Controller.initialize→安装原生命周期／认证订阅→prepareDisplay→原Gateway.connect→startRecovery→完整当前Profile roster、目录、model/config或Conversation REST／activate receipt／finite Socket cut→原可见commit／layout ack。cache只更新retained，不生成binding/runtime/Pending/approval、网络成功fact或ready；document内cacheSerial、owner、恢复代次、frozen及认证撤销仍约束结果，真实提交后迟到IDB无资格。New Chat idle在同一commit构造，不修改primaryAction或按钮；实际按钮／Enter继续原create→附件stage→prompt.submit_idle，既有draftReady、空内容、未确认owner、失败、离线、认证及并发事务门槛继续生效。HistoryImageReader与authorizedFile沿既有authenticatedFetch获得no-store，采用、decode、URL清理及401/403凭据proof无另一路径。

4. **验证与版本证据。** 修前正式App两项反例均失败（val-fixes-before.log：未ready时0张card、已就绪New Chat文本Send disabled）；修前有限HTTP缓存对照分别观察App图片错误true／绕过503（val-fixes-binary-before.log）及Files下载网络计数仍0（val-fixes-files-before-second.log；早期Files等待超时仅留诊断，不作为最终反证）。修后八个相关文件130项通过（val-fixes-final-related.log），新增19项：正式App.initialize文件16项、App图片／Files二进制缓存对照各1项、GET边界1项。实际Gateway保留bootstrap、Socket握手与RPC实现，只控制外部native响应／ready时序；没有mock/spy initialize、connect或request。已有IDB在WS未ready时Timeline、侧栏标题及已得Usage/Context即实际挂载，readyfalse、active未知、无任何RPC；WS释放而history仍延迟时保画面，最终完整请求／对账提交且订阅未见空闪。后增DOM明确断言与最终末尾几何只影响该文件，16项复验通过（val-fixes-final-app-dom.log）。覆盖连接拒绝、有／无／坏／过期／禁用cache、未知／不同Profile、不再有效的owner／IDB／认证、真值先到；New Chat导航、cold URL、必需菜单慢／失败后自动重试、空输入／离线／认证、连续Enter一次受理、真实file input附件顺序、实际Profile菜单选择other及Files返回后仍以other cwd创建。既有阅读交接、菜单覆盖、认证／403／503、隐藏读、图片decode及Files回归包含在相关八文件。typecheck、git diff --check通过；Controller仍2540行，未增长冻结facade指标。源SHA、完整依赖、日志散列及两次测试版本关系见ignored frontend/val-fixes-source-manifest.json。

5. **证据边界与缺口。** 测试运行正式App／Controller／Gateway／PageRecovery／reader，外部边界使用fake-indexeddb、受控WebSocket/HTTP、jsdom几何与rAF、Files第三方viewer-ready替身；附件用例仅为Node无法clone jsdom File补不可变Blob兼容，未替换产品clone／上传／受理实现。HTTP缓存模型在fetch依赖边界模拟已缓存响应，能揭露缺no-store时绕过网络；它不是实际浏览器HTTP缓存通过证据，参数断言亦不冒充用户验收。没有UI／浏览器／模型／APK构建或部署，未操作服务、数据库或原生，未重跑无关全套；真实WS阻断刷新、图片／Files实际GET及活动Turn完整用户旅程仍交下一候选独立Validation。EVID-01运动帧／人工取消／实际指标高亮用户证据、C17 APK豁免边界保留。原Validation未通过不由本包改写，门禁尚待主会话统一新候选复审。

6. **接口与范围。** 无公共恢复DTO、PageRecovery算法、组件props、后端／原生／版本／依赖／drafts库变化；App及presentation源码不改。仅adapter新增内部prepareDisplay，PageRecoveryHost复用既有profileSwitchBlocked只读事实；GET薄接缝自动覆盖现有binary两个reader及正式REST，N05的认证资格／清理顺序保留。新增测试app-initialize-recovery.test.tsx用新Controller替换App导出的测试实例以模拟新document，但initialize及所有正式机制均未替换。所有源码／测试在授权白名单内，无扩范围或待产品决策项。

7. **交回与后续。** 本包未stage／commit／push。请主会话亲审三个产品diff、缓存首显到正式retain／commit的资格、New Chat无Turn事实及统一GET传输策略，按manifest集成新候选并重建0.1.5 APK；之后全新独立V6及全范围Validation重点复验VAL-01／03／04完整用户链。此处130项是机制／正式接线证据，不自行关闭任何门禁。
