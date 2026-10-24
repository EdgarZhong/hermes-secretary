# F1／F2／F3／I1 整包交回

状态：初包已由主会话集成为c4f2f6d候选；本Agent追加整改包已完成并待新候选独立复审。下文保留各验证时点，本Agent未自行stage／commit／push，未部署、未调用真实模型、未操作浏览器／设备。依据为baseline.txt冻结06 R1/R4–R7/R9及R2/R3接口，保持08 Profile与Files归属。

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
