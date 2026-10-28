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
