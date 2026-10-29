# 主会话集成审查与实际联调（进行中）

## 第二次迭代接收与发布准备（2026-10-28，尚未最终验收）

- F03/F04缓存包已亲审，前端`0ea002e`提交／推送；字段分组复用核同UID/物理行/role/revision，最新原生前缀参与同一500身份预算，触及淘汰的完整selector撤销证明而不伪改receipt。95项证据对应实现者记录的精确source；极端无sync详情恢复交A-FE薄接线，尚待最终App联调，不提前宣称全包用户路径闭合。
- F05/F06后端已亲审，`918efda22c`提交／推送；严格Thinking前缀验证保留旧行/窗口/detail证明，只接合法尾追加；CAS通知比较准确候选行在事务前后的原生owned digest，commit返回后才写原通知信号。已核writer只写owned列、legacy content-only repair，no-op/回滚/拒绝UPDATE/并发winner不假通知；正式watcher132项及最后22项按报告边界复用，实际页面消费仍待Z。
- root Steer/Approval/Slash修补前端`1a906ae`，复杂度等价抽取`f94fc07`、类型细化`12a2b90`；10个正式中间态/App用例、Approval相关57项与typecheck通过。全量Timeline旧7失败在原91ad隔离副本亦同7失败，未改断言冒称关闭。冻结TypeScript测量对新增/改动root函数无新增超标，Controller总行数低于原2550。
- 前端0.1.9发布元数据`cb4c769`：package/lock/Tauri/Cargo自包版本统一，不改依赖版本和签名。最终APK尚未构建或交付，等最终候选固定后构建并核资源同一性。
- 正式机仅做只读盘点：`ssh alex`，仓库main `3426c0fc9579dc0589fd0a831741b535aee71ca2`，git status无dirty输出。实际Web为system `hermes-secretary.service` active，Gateway为user `hermes-gateway.service` active；最初试查user hermes-web为不存在/非实际unit，未据此误判线上故障。未重启、未写运行库。

### E03索引客户端追溯（供最终独立复审判断）

D07的原生Timeline索引对应主仓`apps/desktop/src/components/assistant-ui/thread/timeline-index.ts`、`use-timeline-history.ts`及`timeline.tsx`的ThreadTimeline/TimelineRail，使用原生timeline分页入口；它不是独立Web的Load earlier正文分页。初冻前端c39086c的App已只有原history/live Timeline与Load earlier，未调用原生timeline索引；当前Android reply focus也明确只匹配已加载消息、best-effort定位，不伪装全索引跳转。

用户本轮明确“无产品和体验上的变更”，D07以“原有索引”描述可复用能力，未授权给独立Web新增Desktop索引UI。上述固定基线与正式Desktop路径是客户端范围依据，不以当前代码缺入口独自推导N/A。保留供云端复审核对06表述与适用范围；主会话未擅自新增UI、删除D07要求或自签E03关闭。

下文保留第一迭代各时点原始记录，不将历史“待验／工具禁用”视作当前最终状态；最终覆盖以新候选Validation及本节后续补证为准。

本报告尚非整轮通过结论。前后端产品收尾代码已完成并亲审；精确载入版本见ignored integration/runtime.json及各实现报告SHA。仅自己的隐藏IAB，真实App／Controller、真实SQLite、正式REST和native activate／replay／WS。Usage／Pending／配置／压缩状态响应为受控依赖，无生产模型或外发。

## 已完成亲审

- B1：实际DB／Profile／Conversation／selector绑定的短期fingerprint缓存；D0／S／D1及原生cut仍正式接线；详情revision变化不能靠cards matched跳过；手动维护保真实busy，仍核冲突租约／残留输出。
- F1：同IDB条目原子保存消息、完整详情、游标与版本；按UID统一最多500，详情不是新消息；旧owner／迟到结果无展示权限；Usage／Pending并行于历史、仍保原操作门禁。主会话发现的终态Context失败不重试和unknown订阅永久观察已按明确方案定向修复，合法unavailable／历史补读／详情共享收尾已亲审，最终IAB复验待完成。
- Android免刷新6ba37b4、Toast main 810aca3／功能分支03ef6d5已亲审；旧Signal Aborted／Notebook／键盘／微信main修复按各报告接收。未部署、未真机安装或微信真实试发。

## 实际IAB证据

证据根：前端`.archive/incremental-sync-20261027/integration/`，原始JSON和PNG不入Git。

| 场景 | 实际观察 | 证据／边界 |
|---|---|---|
| 200条长消息，同页断线期间追加并修改一行 | 同document恢复为新的200条窗口，草稿12字保持；新末条是外部修改正文；当前完整就绪、无通知 | root-append-state／requests；recovery封套18403 bytes、delta1行，REST仅摘要及侧栏，无正文全量 |
| 同页无变化再重连 | 同document就绪、草稿保持；delta0正文 | root-unchanged-state／requests；恢复封套17656 bytes，不含TLS／压缩，不冒称生产时延 |
| native手动维护运行中重连 | 原生_manual_compress_turn提供running／maintenance，正式activate成功；原Context环及Compacting可见；重连同document继续active并恢复就绪 | root-compact-active.json/png、root-compact-reconnected.json；压缩状态RPC受控、非真实模型摘要 |
| 结束且Context首次读取故障 | 同document退出active、Context由2000收敛为500、页面就绪、通知为空、草稿保留 | root-compact-finished.json/png；原生维护退出，摘要／计数受控 |
| epoch／cursor丢失 | 同document恢复并保草稿；必要snapshot回退成功 | root-epoch-state／requests；模拟epoch变化不是重启真实生产服务；发现重复全量见下表 |

首次开发服务重启后Vite自动热更新替换了夹具页，因此该次epoch观察作废；后续已在ignored专用Vite配置关闭HMR，再建立独立document完成压缩和epoch旅程。正常恢复旅程内没有主动reload。

## 主会话发现与待关闭项

| 问题 | 反例 | 已指定方案／状态 |
|---|---|---|
| F1终态Context一次失败后永不重读、unknown永久轮询 | 正式Controller新增反例改前失败，见frontend报告followup | 分离Context成功标记与history完成；unknown只退观察，不假确认命令；已实现，合法unavailable终态补验中 |
| 已finished压缩后的epoch恢复重复全量 | root-epoch-requests：两个并行snapshot各598805 bytes／200行，总RPC约1.20MB | 当前同owner历史在途读取先settle取得新cursor，再沿原强制终态对账；不得只跳过终态刷新。F1已实现并亲审，最终IAB复验待执行 |
| 首次展开旧Thinking重复详情读 | root-detail-requests：同row6两次REST各4740 bytes | 无staged画面时共享原HistoryDetails读取owner；staged隔离／版本核验保留。F1已实现并亲审，最终IAB复验待执行 |
| 历史typed来源不可判定 | B1正式反例可见同类typed既是Turn又可仅通知 | 用户U17已确认旧模糊片段懒取、新Turn最小内部source标记；B1已实现并亲审，候选862326c0a7 |
| Idle旧owner迟到host tick抢回绑定 | root审当前maybe_run_idle_noting路径 | 曾绑定但被替换的实例在attach/tick前拒绝，真实新Main边界保持；已亲审关闭；main 0a5d09cdcf，同补丁已接入增量 |

| Idle旧completion清理撞新native复用 | _end_completion提前读取pending后才等待Framework，可能清掉随后reserve的同handle | 在同一ACTIVE临界区reserve；Framework→ACTIVE重新核验并原子关闭；已亲审原子交接及71＋3项定向证据；main 0a5d09cdcf，Linux待验 |

最终版本须定向重验上述修复并核SHA，之后执行全轮独立Verification及Validation。本报告不把当前部分结果冒称交付完成。

## 恢复执行后的候选与环境边界

后端候选862326c0a7，前端候选91ad72f3898be4e6d98461f69566a76b54595290；最后六文件SHA与244项、typecheck、build和冻结度量证据一致，主会话已审上下游和owner／revision保护。当前已重启精确版本真实Python／SQLite／HTTP／WS隔离夹具，未调用模型或微信。隐藏IAB创建被工具拒绝：Local browser use is disabled in Work settings；用户随后截图证明开关已开启，重建连接仍同错，实际根因未知，不能据此断言用户关闭设置；未操作其它浏览器或用户页。最终epoch单snapshot、详情单请求及unavailable停止观察的实际浏览器复验尚未执行；上述旧反例保留，不以受控单测替代本项。独立Verification将核全部冻结要求及证据边界。

Linux7文件163项证据及16份日志／记录SHA已由主会话核对，全部相符；自建远程工作区已删除。复测时证据目录需预建，新增测试可移植性整改已登记plan，不改写既有产品路径测试结果。用户准备重启Codex，本地fixture服务5637/5638已正常停止；最后运行配置与SHA留在ignored runtime.json。

### 第二迭代已接收提交与重启后开发联调

- A-FE已亲审提交前端8313cf23714d47012a19fc2e0bee7d084933c851。捕获正式恢复取消/认证/连接资格；精确退役不存在anchor；无sync时只恢复详情提示、不造证明。复杂度窄拆分后readCachedDisplay CC17(原19)、readConversation21(原22)，14项及typecheck通过，未复跑有效166项。
- D-WX已亲审提交后端a5018ffd8206f54019f29f6bbb2c5edf641384bd；真实持久UID后投递，成功事实去重、排队不算成功，失败仍由既有FIFO/尾部兜底。报告r2-weixin.md记精确源码与150＋最后47项影响证据。未真实微信外发。
- root对部署版0947ed5与当前FE比较，ChatComposer.tsx、ChatSelectors.tsx、timeline.test.tsx字节无差异；七条旧组件夹具失败保留，不修改断言。原91ad隔离同样7失败记录已保留；该事实不代替真实页面验收。
- no-tmp七行旧Linux取证路径仅加历史说明marker；未删除/替换原行或历史结论，原字节SHA48821d41daf596c6c4395204073f9d4ab78970ceca6c7fe1ab40a03cb0b6e396在ignored historical-report-no-tmp备份；检查器/规则/阈值/baseline不变。指定报告扫描通过，未冒称全轮十项已统一执行。
- 重启后旧Agent和fixture进程均已确认停止，接续C-U20而非重做有效证据。隐藏IAB已从disabled恢复，重新启动8189/5199隔离服务，fixture运行时及源SHA在ignored integration/runtime.json。root隐藏tab2文档43687199-2dc4-4e7a-90b1-18088cf1414d，实际CAS改文200行保持、watcher自动更新App；恢复轮次1→2，delta1行/18312字节，正文REST0，草稿保留，零通知；raw state/requests/probe/png位于validation-round2/root-dev-native-cas.*。这是主会话开发联调，不是独立Validation通过。
- FE8313cf2的0.1.9候选APK已构建，1009/arm64/minSDK26/原证书/v2/16KB/ZIP/439内置资源核验通过，32120541字节，SHAac52bfb581fc1e94328a170e8447a151b95f0a4b530a3dd007e803b49f3f169e。初始后置校验调用旧系统Python缺file_digest；项目Python复核发现唯一dist/.DS_Store目录元数据，已原件备份ignored并仅从生成dist移除，public/用户原文件不改；随后严格资源一致性通过。原始构建和复核日志在FE ignored android-019-*.log及APK sidecar。尚未交付/真机/部署。

- root开发联调：隐藏窄屏390×844，CDP声明150ms/64KiB下载/32KiB上传；不把CDP设置等同WebSocket实际受限带宽或端到端性能改进。相同document43687199，断线期间正式append1行后同页恢复ready、最新200行包含新消息，draft14字符始终相同、无通知；delta1行18509字节，历史REST0，总REST3043/RPC20843（含附属读取/心跳）。存档root-dev-weak-*.json/png；DOM每帧/Mutation/100ms检查在窗口内记录12个变化观察，timeline不可见/空白0、Notebook unknown0、草稿变化0、alerts0；只证明这些采样边界，非Android真机绘制或逐像素零闪。
- 同窄屏实际输入框冷Slash /compact Send：1次session.compress，活动态Context: Compacting且hs-ring-spin=true；终态succeeded、ready、草稿清空、Context取到新250值、无Retrying/错误通知、同document。原始root-dev-slash-compact-{during,completed}.json/png。外部摘要依赖受控，原生maintenance接缝真实，不冒称U20全链已验。

- root-dev-reading-* 是未完成开发观察：其间并行夹具源码扩展后隐藏页标题由自定义fixture变为正式Hermes Secretary，诊断panel消失、document更换，不能用该段证明或否定产品同页恢复/锚点保持。产品src未发现location.reload/assign等调用；隔离Vite虽hmr:false仍监视源码，现专用ignored配置再设watch:null，待夹具整包后重启并固定源；正式Validation须Page导航事件+documentId复核，无意reload使该场景无效而非预填通过。此前完成的CAS/weak/compact各自同document原始资料保留原结论边界。


## 第二轮集成封口与新增冷启／顶栏刷新（2026-10-28）

候选后端`2dc4398284bff5506dcf8f95b6507ff66ca71915`、前端`bc02d01d7e0eb8c9a35b6855dc984374cf6f1cee`；两仓main历史已按no-ff/no-commit及核心文档保护纳入，源产品相对合并前零变化。后端四文件十hunk逐段接线核对在r2-joint-noting末节，不因冲突恢复U20明确替换的旧串行等待。其它main工作区dirty未动。此为开发集成候选，不是独立门禁通过。

U25前端ba7decd：PageRecovery一次document资格只由首个真实Conversation commit的实际布局ack消费，local交接继承未消费标记；Timeline当次instant到底，不受加载期旧输入／触摸阻止；之后暖恢复与新人工阅读保持。root审正式owner/commit/ack与reconcile接线后接收，5文件115项、types和冻结健康证据见前端ignored cold-start-viewport/report.md及日志；浏览器真路径交独立R47–49。

U26先独立原型后正式接线03a9689，AppFrame只新增可选mainRef；AndroidHeaderRefresh限定top document＋native packaged标记＋既有HermesAndroid bridge，普通Web不启用。正式自动恢复不调用reload。组件仅在非交互topbar起手，阻尼cap、释放一次、回拖/cancel、正文/控件保护；监听主容器直属TopNav替换以恢复touch-action并取消旧手势，不监听流式正文子树。root发现mouse会选字，已窄修合格pointerdown的默认动作；未禁正文选字。

root自建隐藏IAB预览127.0.0.1:5209，390×844真实CDP mouse：半程图half-mobile.png、阈值armed-mobile.png（已向用户内嵌交付）、深色armed-dark-mobile.png；80px下降封顶后手指再多下拉200px，indicator仍top36/40高，header top0、canvas top-40均不变；释放页面真实reload一次，URL保持，预览计数0→1；正文起手phase idle、回拖未达收回计数仍1。原始cap-final.json/截图在前端ignored header-refresh-preview，旧armed.png/half.png为画幅未校准开发图不当正式证据。IAB不支持CDP touch，mouse不能冒称Android真实手指、WebView命中或真机手感；DOM25项也不冒充真触摸。

前端组件25项；root接线后App＋组件2文件83项通过，integration-tests.log；typecheck通过；正式冻结TS度量5文件0 blocking/0 advisory，integration-health.json及完整source SHA。U25独立115与U26整合83有复用文件，不合并宣传总测试数。原型源码/清单与现有主题保持，不修改全局字体/配色。

后端最终C42源码SHA及十检查有效证据、末次46项已核；发布保护脚本在最终schema上本地再演练27例全通过、零SSH/生产写/模型调用，脚本SHA08c010b4347796ba537b2c516adac16f0358bf791e2a6f2b54794166091f41a3。APK重建及正式部署尚未完成。第二轮独立Validation原46＋U25/U26十场景共56项已过目，待新本地Verifier整轮审查后执行，不按包开门禁。


## U27初始临时引导失败补齐（2026-10-29）

root依据用户再次明确的同页SPA目标查到：APK appDocument的初始网络IOException/408/429/5xx曾返回静态Retry页面，SPA没启动；ForegroundRefresh本身已无自动reload，不能仅删计时器就称冷启网络恢复完整。root设计后apk_cold_boot_recovery实施五文件，已亲审提交前端e545359（含MainActivity原构造兼容的可选network supplier、共用既有packaged renderer、可选BOOTSTRAP_PENDING初始提示）。Gateway仅pending=true+真实packaged DOM+top window时首尝试走现有freshBootstrapToken，之后仍同一Gateway/PageRecovery/document自动重试/读必要数据。正常200/30x自然认证导航、真实401/403/非法引导/本地资源失败及普通Web默认行为保留，无新reload/loadUrl或owner。

root指出首包hint缺JS侧平台限定，已窄修并以真实iframe及普通Web有hint反例补证。最终native13项源码不变复用，前端3文件35项、types及冻结TS健康通过；正式shouldInterceptRequest/AssetManager和真实Controller/PageRecovery分别证明两个接缝，不冒称真实AndroidWebView网络栈/物理手势。原始反例、完整报告及最终源码SHA在前端ignored apk-cold-boot-recovery/，client SHA60d7593d5774422f44b7622f53ac1346e576a08fc16f6b916b9c313c6cae4466；native SHA18ad2b3f7566386835397c5789675e10fa89e780a87afbf93ea9a3c2bc748b6a。

旧bc02d01 APK已构建严格通过（439内置文件、原证书、0.1.9/1009、ZIP及16KB），SHA da49cfe02bd8d5772603e9815ff1689efe73b20be8233c981d7ba4d0de0be178、32123673字节，作为旧候选保留；最终需e545359新dist/APK，正在重建，不用旧包冒签U27。

开发夹具在正式Validation前补基础设施：HMR关闭且watch:null；重载当前/chat或Files路由仍返回同一observer宿主、script使用绝对入口，保真实地址；被动DOM/rAF observer先装再首次React render并记appMountedAt，避免漏cache首显；新样本独立validation-round2/dom-samples.jsonl，不追加第一轮历史；JS '/' bootstrap直通实际隔离native HTTP，不能用Vite lastBootstrap旧值伪恢复。未改产品，不把未执行场景记通过。服务在更改期间已按PID停止，最终源/夹具重新freeze后再启动。


## U28用户真机预览反例与触摸接管窄修（2026-10-29）

用户对e545359预览实际反馈：标题栏下拉无响应，再往上是状态栏/系统控制中心；补答“完全没出现”。root没有据此要求用户改从状态栏起手，按原S19/P11缺陷处理。W3C Pointer Events §9.4与§4.1.3.2说明direct touch隐式capture及transfer次序；正式组件旧cancel监听所有冒泡lost，受控UA pending-capture时序在实际组件取得改前2失败，正常迁移会清掉pending container，标题低progress可能仍在上缘外，所以用户肉眼无圆盘与此相符，但不能证明手机唯一根因。

FE d1a53cfe35ae5173df48a550bc45048d64133598只增加lostCapture target===container判断，原pointercancel/控件/区域/cap/回拖保持。root亲审+31项受影响回归（含实际wrapper/ref/StrictMode和gating正反例）、types/冻结TS度量通过；原始证据前端ignored header-touch-capture/。隐藏IAB的CDP pointerType:pen未复现implicit迁移，不能把它冒称真实touch；IAB dispatchTouchEvent不支持，未回退桌面/外部浏览器。自建tab4已关闭/viewport reset。

d1a新APK按原构建签名重打，只有生成dist.DS_Store与包差异，精确保留该元数据后移除生成副本，439业务资源严格全匹配；用户原public/.DS_Store不动。原证书449b5f36...、0.1.9/1009、ZIP/16KB及交付副本全部通过；Downloads preview-d1a53cf-arm64.apk，32123717字节，SHAfb651a0bbeae025776016d58fa594b68aa2f0fb16faeaf88aa6b3983ef564a2d。是修正版预览，不冒称后端已发布/全门禁关闭；修后手机反馈仍待。旧e545预览与其包证据保留原版本失败事实。
