# Hermes Secretary 当前状态

## 自主口径收敛 · 待用户追认

- **Agent自主收敛／待追认：混合压缩载体的读取。** 原空白：一个native UID可同时承载压缩摘要与真人消息，而用户要求辅助开关能读取Compression且Get Meta仍仅四字段。决定：默认保留原真人视图；显式辅助允许同UID的system摘要视图，Get Meta／Search按语义部分分别返回，anchored Read允许现有roles参数选部分，默认锚点优先原非压缩部分；同UID同role的system内容合并为一个视图；不造UID、不放开Full／隐藏内容。理由：使明确要求在native混合载体下可操作。影响：Read新增可选roles适用位置，同UID可有不同语义投影。已实现，201项History接受测试及56项原生路径通过；独立Verification／Validation已通过，已上线；不改变Message Identity或Notebook新证据准入。
- **Agent自主收敛／待追认：Candidate同Task来源形式切换。** 原空白：旧合法direct→refs操作与新旧Task节点不可删约束如何同时成立。决定：仅尚未提交且唯一节点属于本Task时，允许显式清空当前工作槽并切为合法refs；任何旧Task直接节点仍禁止删改。理由：继承原来源二选一操作并保持旧节点约束。影响：当前Task工作态边界，无迁移／旧节点特权。已实现，正式工具／恢复／原子失败98项通过；独立Verification／Validation已通过，已上线。

## 2026-10-27 · 增量同步与免刷新恢复（第二迭代执行中）

**当前完成条件（U22／U23）：** 持续自主执行；第一轮之后Verification与Validation各最多再两次正式全轮复审／复验，第三轮内完成两仓main集成、正式Alex上线和原签名0.1.9 APK交付。次数上限不豁免缺陷或证据缺口，不开第四轮。用户U24已明确将Verification改回本地，第二轮集成锁定后派全新上下文6.1 sol/high全范围独立审查；开发定向测试／主会话亲审不冒充独立门禁。生产模型和真实微信测试外发不在授权内。

唯一计划／索引在[本轮目录](.autonomous/20261027-incremental-sync/plan.md)。原始需求U01–U29、缓存D01–D18、表现S01–S20和操作P01–P11已落档。保持原产品／视觉／操作资格，主目标仍是500条消息与完整已取详情缓存、游标同步、SPA／APK无需刷新恢复，不为填缓存预读或重新发起写操作。

| 工作包 | 当前实际状态／交接 |
|---|---|
| 原独立修复及主体增量机制 | 已提交／push，尚未按本轮发布；历史记录与证据见reports/integration.md |
| U18 Steer／U19 Approval／冷Slash目录竞态 | 前端1a906ae及后续类型／复杂度修补已提交；正式中间态／App反例通过，待当前集成浏览器复验 |
| F03/F04缓存 | 前端0ea002e已亲审提交：完整详情字段保留，窗口／详情／已核验前缀合计500身份预算，证明失效时仅退役selector；95项及真实IDB证据，见reports/r2-cache.md |
| F05/F06后端增量 | 后端918efda已亲审提交：同源Thinking合法尾追加、正式CAS实际改文提交后通知；132项及末次22项定向证据，见reports/r2-backend-sync.md；实际App接收待联调 |
| F01/F02前端恢复 | 已整包交回并亲审，166项＋末次14项通过；复杂度窄拆分完成且无增长，前端8313cf2已提交；见reports/r2-frontend-recovery.md |
| F08微信逐消息发送 | 已亲审提交后端a5018ff；final持久UID后立即沿既有FIFO投递、尾部成功回执去重；150项及最后47项影响复测，不真实外发；见reports/r2-weixin.md |
| U20／F07／E02联合Noting | 后端27c74b094f已亲审提交／push，root提出的C-R1–R4四处接线补修全部纳入，末次5文件46项及42文件十检查通过；普通手动／Idle／原生auto并发联合触发取消、已提交保留，Force仅Turn结束不可取消并封区间，特殊替代审计透明跳过，Note独立四时点检查后原FM推送；正式独立门禁待统一执行 |
| E01/E03与动态体验 | D07原表漏标客户端范围已在06顶部勘误，仅约束已有入口的Desktop；Web/APK不新增索引UI，E03交独立Verifier核对；root准备同夹具流量／时序／必要读取证据；已有旧候选隐藏IAB记录只按旧版本引用，不当作当前候选通过 |
| 第二次整轮门禁 | 第二轮独立Verification在de45/11353b8调查中，已发现R2-V01：native普通error/no_change被误联取消Noting。root方案获审查者按原N01/N02认可，隔离remediation工作区实施，不改正在审查的源；完整调查继续，第三轮统一复审才可关闭。Validation62计划含U29已准备，正式执行仍未开始 |
| U25冷启动视口 | 用户已确认新document首次真实历史提交后一次立刻到底，加载期用户滚动不阻止；cold_start_viewport已交回，root审查正式commit/ack接线后接收并提交ba7decd；5文件115项、types与冻结健康通过，同页规则保持 |
| Main notebook_show线上反馈 | 用户转述Main自述无工具且只限Noting，既定只读Main资格不变；只读核线上3426持久工具表有Show且同会话23:42实际调用成功；争议请求wire缺失，缺工具未确证。新候选17项正式Main工具接线通过；用户明确停止深挖旧逻辑，继续以新链路实际注入／读取为准，未改Prompt或扩大旧版追查 |
| Noting误恢复补修 | root已亲审接收：独立Secretary token、可信child独立history token、原生sessions.changed完整scope与FE437b9aa正式owner消费；原生租约释放／两处改文／两处recovery reservation均准确通知，Main／未知仍global。专项21、watcher26、历史9、manual18、FE12及十检查通过；保真实断线与Main历史authority，待统一独立门禁 |
| U29真机视觉反馈 | 用户已确认起手正常，但要求圈旋转放慢、阈值补明显高光／光晕；FE6628a2e已提交：旋转540→240度、等待700→1300ms、阈值主题高光／光晕；32项与types通过，root隐藏IAB浅深主题／回拖已核，不改已正常手势时序／行程／区域，新视觉真机反馈待 |
| U28真机触摸起手失败 | 用户e545实测标题栏完全无圆盘；root确认子lost capture冒泡误cancel，FE d1a53cf已亲审提交，31项及正式wrapper/StrictMode/types/健康通过。已交付`/Users/edgar/Downloads/Hermes-Secretary-0.1.9-preview-d1a53cf-arm64.apk`：32123717字节、SHAfb651a0bbeae025776016d58fa594b68aa2f0fb16faeaf88aa6b3983ef564a2d，439资源/原签名/ZIP/16KB/1009已核；用户随后明确反馈“之前你给我的第2次APK已经可以正常下拉刷新了”，d1a53cf预览实际顶栏起手故障已获真机关闭；其余场景不据此代签 |
| U26顶栏手动刷新预览 | 用户新明确体验变更：APK only，页面／背景静止，Chrome式圆背板橙圈阻尼与cap；root已先交付隐藏IAB真实原型截图，CDP真实mouse验证cap/松手一次reload/正文不起手/浅深主题；03a9689已接正式APK packaged native入口、普通Web关闭，25组件＋83整合项、types/health通过；无真机touch，后继d1a53cf预览已交付，最终包待当前修补后重建 |
| C-R5／C-R6 显式恢复Note资格 | root已完整亲审接收：Snapshot同事务来源／operation证明、branch去父关联、原生恢复lease受理接手及终态补检查；7文件源码SHA与62项／十检查证据逐一匹配，待统一独立门禁，不作为正式V已通过 |
| U27 APK引导失败同页恢复 | 原生自动reload已取消；冷启bootstrap传输失败/暂时服务错误仍落静态重试页，未进入SPA，root指定最小APK专属deferred-bootstrap接缝已亲审提交FEe545359；native13/前端35/types/健康通过，认证／默认Web保持。bc02旧APK严格核验保留，e545新包已严格核验并按用户明确要求交付预览，正式全轮验收尚未完成 |
| 发布／APK | 用户2026-10-29明确要APK先看，已交付`/Users/edgar/Downloads/Hermes-Secretary-0.1.9-preview-e545359-arm64.apk`预览：32123801字节，SHA41a193804d481a87bb2f28956c3b18659a88c8c0bc5204893ad9d52447e4d5e2，原证书/0.1.9(1009)/439资源/ZIP/16KB及交付副本已核；未冒称后端已发布或正式验收通过。U23最终发布授权保持；0.1.9元数据cb4c769已提交，8313cf2候选APK已构建并通过原签名／0.1.9(1009)／ZIP／16KB及439内置资源一致性核验，尚未最终交付／上线。生产只读基线后端3426c0f，Web系统服务和Gateway用户服务active；正式前端0947ed5保持 |

前后端实施目录分别为`/Users/edgar/code/hermes-secretary-incremental-sync`与`/Users/edgar/code/hermes-secretary-web`，同名`codex/incremental-sync-20261027`分支。C、原恢复包及U25/U26均已亲审提交；两仓main历史已按SOP纳入候选（BE2dc4398／FEbc02d01），合并产品tree零增量，不触碰其它main工作区dirty。validation_round2已补完并过目56场景，release_preflight及27项本地发布保护演练已完成。隐藏IAB已恢复；root开发联调确认正式CAS改文→watcher→App同document自动delta更新1条，草稿保留，不把该开发证据冒称独立验收通过。子Agent6.1 sol/high、不再派生、不流水账；主会话负责方案、亲审、接线、正式门禁与发布。

保护原main工作区的Noting调试／生成协议／07／presentation等他人dirty。新状态表必须兼容正式旧库，仅加Secretary自有伴随表／读取视图，不重建生产数据库。冻结检查不增删放宽；no-tmp旧报告七处仅加既有允许的历史取证说明，原行原结论保留，原字节与SHA已在ignored存档；单项扫描通过，未改检查规则／阈值／baseline；de45版本已统一执行冻结十项且70文件health 0／0，后继整改须按影响补查。旧Timeline七项失败在原91ad同样存在，不能据此替代部署基线或当前用户体验判断。Android完整生命周期与真实微信送达未完整实测；用户已确认d1顶栏起手正常，不能扩大为新视觉及全部生命周期通过；包校验／受控adapter不冒称实机或真实外发。

U20详口径见07顶部及plan接线设计；旧“先Noting再压缩／FM结算后才终态”已被替换。U17旧模糊片段保持懒取，新Turn沿原生source精确主动取Thinking，不设逐Thinking游标。用户确认与原始云端报告保留索引，不改写旧审查时点结论。界面验收只许自建隐藏IAB，不动用户浏览器／桌面。

## 2026-10-27 · Noting来源链／History调优（已上线）

用户已确认全部语义和精简Prompt，并明确“开始改吧。改完，测好，上线”。轮次`.autonomous/20261027-noting-provenance-history/`，工作区`/Users/edgar/code/hermes-secretary-noting-chain`，分支`codex/noting-provenance-history-20261027`，基于main `d1de4db49b`；为隔离旧目录及main调试dirty新建，原修改保持。

范围：Get Meta、统一语义role／默认辅助消息排除、闭区间、工具参数及结果展示；每条目每Task一个不可改旧节点的来源链、runtime只读对应Evidence time；已审Noting／History Prompt。独立History／Notebook／Prompt实现包，主会话亲审集成、真实模型证据、独立Verification→Validation通过后已统一部署。仅人工转换Alex仍用的唯一置顶Conversation的Notebook，保留消息、排期、绑定、其它Profile／Conversation和前端；不建通用迁移层。正式机`ssh alex`，上线沿既有SOP／发布工具，备份最多两套三库。

冻结02d55fdb，产品3426c0f已合入origin/main并在正式Alex保持main上线；两服务实际版本、只读RPC、目标Notebook与保护数据／配置／绑定／静态均已验真。独立Verification38判据通过（37符合、1本地生产不适用）；Validation17适用场景及独立10旅程通过；40文件1094项、保真修复107项、最终Linux132项及十检查通过。旧29项／8文件和Prelude15项冻结基线失败保留，不称分区全绿。真实k3.1-pro/high两Task6请求代表样本通过，8个后继源码差异分支由当前正式机制补证。

唯一目标转换完成：51历史item、8Snapshot／pointer不变，31独立条目×Task节点在版本内累计55次，180UID引用／81不同UID，162可见投影；生产重开只读验证通过。两套完整三库已逐库核SHA／integrity／FK，研究副本两文件清退；运行库及同步包不动。具体发布／恢复事实只记operations-log；[最终交付](.autonomous/20261027-noting-provenance-history/final-delivery.md)含范围、独立报告、工程细化与限制。本轮无未完成项／新阻塞；原main和旧目录他人dirty未纳入，未做UI／APK或生产模型测试。

## 2026-10-26 · Scheduler二级切换卡顿与0.1.8重建

用户明确卡顿发生在一级面板点击Tag切换Scheduler二级，不是打开球；要求修复、重建0.1.8暂不交付。前端0947ed5已提交／自动push：移除层级及异步尺寸更新触发整板隐藏360ms的玻璃动画，层级改为立即可见可操作的140ms轻量位移；球展开／关闭动画保持，数据到达不重启导航过渡，按需读取与恢复owner不变。旧APK及SHA已移出Mac和云端Alex工作同步区，Downloads原副本及云端同步区外副本保留。

验证：改前Tag导航透明／不可点击反例失败，修后通过；4文件112项、typecheck及冻结TypeScript度量通过。隐藏IAB390×844真实App受控排期延迟3秒，仅1次读取，切换约30ms可见；648采样帧里透明／不可点击／ghost均0。5秒未决请求期间可返回一级，迟到结果不重开；原球展开／关闭回归通过。无Android真机，不把IAB性能当作真机验收。

新0.1.8／1008已重建：本地ignored `.archive/qa018/apk-staging/Hermes-Secretary-0.1.8-0947ed5-arm64.apk`，32,106,601字节，SHA256 `1ffb96ff4476fdb261d01c8d1170f61c02e3eeacb17cd4ffde82085758f7b463`，原证书、v2签名／ZIP CRC／16KB对齐及439前端资源通过；仅本地暂存，未发送或复制至用户同步区。网页已沿先前授权只更新静态0947ed5，439文件和HTTP资源核验通过；后端6ef9459及Web／Gateway PID保持、微信connected。

## 前轮完成情况（2026-10-26）

**2026-10-26最新授权：用户已允许前后端上线，SSH `alex`为正式首尔43.128.131.30／ubuntu；由主会话独立接完迁移会话未完成的飞书notifier MCP（Alex、study均启用），发布本轮代码并恢复Hermes云端正常运行。同步修订全局服务器规则、补齐运维记录；第一台实验用首尔机废弃、准备回收，不再作为生产源。原迁移期间禁止上线约束已被本次授权替代。**

已按用户指定顺序完成统一恢复修复与b33e428阶段APK核验，再完成Noting按需优化。悬浮球仅由当前Profile全局开关决定，与连接状态解耦；未展开排期不取详情，概览用轻量计数，同owner突发失效合并为一个在途请求加一次最新读取，未生效的旧读不消费完成通知。不新增持久缓存。后端查询排除结束严格超过24小时的排期，仅返回hidden_count；删除不返回／不计数，暂停保留，原生模型工具完整列表不变。用户新增胶囊压高已落实：Usage／Context从32降至26px，字体／胶囊圆角不变，底栏36降至30px。最终0.1.8／20c9267已构建并完成交付副本完整性核验，已随本轮在正式Alex上线。用户明确追加修复Compaction message末尾的Conversation start：只取该Conversation的History Foreground第一条timestamp，禁止用内存最早时间或本次压缩区间代替，禁止另猜起点。已删除_summarize_window的内存min(timestamp)，Compaction footer直接读取get_history_foreground(current_session)[0].timestamp；真实数据库反例改前3失败、改后3通过，7文件201项相关测试与10项冻结检查通过。已上线；不改写生产历史／旧摘要。

统一恢复状态本地实现完成：PageRecovery复用原有owner、轮次、读取结果与提交点，派生当前可见依赖的availability；Composer单行提示、主按钮恢复资格及Android恢复／导航回执同源。只有Connecting to Hermes…、Restoring {对象}…、Retrying {对象}…三模板，固定20px单行、随Composer宽度、省略号、多个真实等待对象3秒轮换。移除聊天页其它自动恢复横幅／Toast；草稿保留可编辑，真实写操作及未确认回执反馈保留。已恢复同owner的普通后台刷新不重新锁定操作；隐藏预取不进入完整恢复资格。REST读取增加30秒可取消超时，失败交给既有owner自动重试。

已定位的静默恢复缺陷：Socket connected、Profiles读取成功与页面完整恢复原来各自决定提示，Secretary又错误等待历史／流恢复，导致提示消失但球未出现。现Secretary独立按当前stored owner读取，读失败与secretary.changed刷新均沿恢复owner重试。另一个后端根因：原生压缩后的完成回执来源仍visible，但active=0；恢复层误拒并返回runtime_unavailable。只放行exact UID／row／role且visible并active或compacted的已完成来源，rewind／删除／不匹配仍拒绝。此前只读取证与本地原生链路反例均可复现，不归因于网络。

通用规则见[AGENTS](AGENTS.md)，稳定入口见[README](README.md)，逐次部署／故障历史见[运维记录](docs/operations-log.md)。历史CLAUDE可由f812c1d等已提交时点读取，不把旧阶段的“当前／正在”继续作为任务编排。

本轮发布及迁移收尾已完成：Alex、study飞书MCP握手均仅notify，未发通知；Hermes恢复正常运行。旧实验首尔机废弃、待回收，未销毁实例。全局服务器规则已精简。具体版本、验证、备份与限制统一见[运维记录顶部](docs/operations-log.md)。20c9267旧APK原已交付并核SHA，用户本轮要求后已移出两端Alex工作同步区，新构建暂不交付。

## 当前交付与运行版本

| 项目 | 已核结果 |
|---|---|
| 本轮本地代码 | 新候选后端de45e33262与前端11353b8已提交／push，产品源冻结；第二轮独立Verification已进入实现审查。尚未发布，本地候选不等同下行线上版本 |
| 后端线上最后核验版本 | 3426c0fc9579dc0589fd0a831741b535aee71ca2；正式Alex的Web／Gateway实际版本、RPC和目标Notebook已核，微信connected |
| 前端线上最后核验版本 | 0947ed5f25fe9d412e25ab6ab6248aefcd64c55e；Scheduler即时切换已上线，439静态逐SHA及HTTP入口资源验证通过 |
| 已交付APK | 最新为0.1.9／1009预览d1a53cf（Downloads preview-d1a53cf-arm64.apk），用户已确认顶栏能正常下拉；32,123,717字节、SHA fb651a0bbeae025776016d58fa594b68aa2f0fb16faeaf88aa6b3983ef564a2d。最终候选437b9aa已构建严格校验，尚未交付；原正式0.1.8／20c9267保留，不混作最新预览 |
| 运行设置 | 历史noting off不代表当前值；最后已核local_enabled=true，默认／Alex压缩总时限1000秒及Idle500秒／96K保持。本轮只追加授权飞书MCP配置／官方PM mcp依赖，不改模型或调用生产模型 |
| 保留他人工作 | presentation报告、手动Noting调试入口／协议生成、07等原dirty保持，不纳入本轮恢复补丁提交 |

## 前轮交付事实索引（本轮唯一任务看板见顶部）

| 工作 | 状态与完成边界 |
|---|---|
| Noting来源链／History Get Meta | 3426c0f已合入main并上线；双独立门禁通过，唯一目标转换及RPC／保护数据终验通过，详本轮交付报告 |
| Composer统一恢复契约 | 本地实现与正式App链路已验，已提交／自动push前端b33e428，等价抽取217项及复杂度检查通过；已部署正式Alex |
| 压缩后完成回执恢复误拒 | 本地正式入口及原生链路105项通过；补充中断／失败压缩路径7项通过，10项冻结检查通过；已提交／自动push后端98a707e，已部署正式Alex |
| 0.1.8重新构建 | 20c9267最终APK已构建并核验，唯一新文件名与SHA／verification sidecar已生成；无真机不声称安装验证 |
| Noting弱网按需读取／显示解耦 | 已提交／自动push前端20c9267、后端4b04546；本地实现及主会话隐藏IAB已验：未展开0次、展开1次、关闭／重连无额外列表读；底部隐藏摘要、全局开关控制球、断线球保留；不新增持久缓存 |
| Compaction末尾Conversation start | 已按用户再次明确的Foreground第一条修复，真实DB连续三轮原地压缩／Session轮转／冷恢复稳定；非单调时间与foreign owner反例覆盖。7文件201项及10项冻结检查通过，已提交／自动push后端453401d，已部署正式Alex |
| 重连阅读／流式漏显 | 388839c已交付：idle前缀兼容保视口；active或已证前缀失配才回底；连续连接手动20秒规则独立。旧恢复冻结挡住已到达消息的机制、首次NewChat／冷active慢Pending路径已补齐。本轮回归继续验证 |
| Composer满高闪动 | 小数scrollTop钳制导致的无效重复scrollTo已修：原90次含30次无位移，修后105次均有实际位移。未修改键盘／布局；Android Chrome真机绘制尚未验，不把桌面窄窗口等同问题全部关闭 |
| 既有工具展开状态 | construction→UID admission展开保持测试在未修改388839c隔离副本同样失败，已留证；本轮不改断言掩盖，不与流式可见修复混为一谈 |
| 已有成果 | 冷刷新正文缓存／暖态阅读保持、Thinking身份修复、Context终态单次高亮、Stop后持久终态恢复、Compact部分摘要提交均沿既有已发布成果保持；历史逐项证据见operations |
| 手动Noting调试入口 | 别的工作已有本地dirty，尚未发布／调用；本轮不混入或额外触发Noting |

## 验证摘要与边界

- Compaction start修复：真实DB反例改前3项失败，旧代码将Conversation的9月21日起点写成内存后段9月22日。改后3文件96项及4文件105项通过，合计7文件201项；原地压缩／Session轮转各连续三轮，重开DB／重建compressor，末尾始终等于同Conversation History Foreground第一条timestamp。另测后续行时间更早、外部Conversation更早、旧RAM字段与确定性摘要路径，均不改变权威起点。10项冻结检查通过，证据见ignored `frontend-018-20261026/conversation-start/`。

- Noting／排期／紧凑胶囊收尾：前端22文件504项通过、6项跳过（5项已证旧失败＋1项可选原生wire夹具未配置）；typecheck及冻结TS复杂度检查通过。后台5文件73项通过（24h前／整点／之后、删除不计数、暂停保留、foreign owner隔离、SQL先过滤再投影、只读不改库、原生Scheduler语义），10项冻结检查通过。仅暂存本轮生成协议增量的隔离快照亦通过字节级重新生成检查。
- 扩大检查发现controller.test的4项旧失败，与此前工具展开1项一并保留；均在改前隔离快照复现。后端whole-wire目录检查的review.summary孤立契约同样在改前98a707e复现，未改断言或纳入本轮修复。测试中旧方法级夹具不启动PageRecovery，已隔离其刷新副作用；正式恢复owner／完成回执合并由完整native DTO测试覆盖。
- 390×844隐藏IAB实际App：胶囊各26px、上下padding2px、圆角999px、字体12px、底栏30px。关闭Noting详情不取排期，概览仍显示轻量计数；展开仅一次读取并显示4条隐藏摘要；关闭再失效／重连仍只有1次。断线球仍显示，Composer单行Connecting；恢复提示消失，球回到idle。

- 前端最终相关21文件483项通过、1项明确排除的已复现基线失败；typecheck通过。初次467项中465通过，旧Usage横幅断言按新合同更新；另补Android导航等待本地状态恢复测试，141项定向通过。等价复杂度抽取后217项通过，18个变更TS文件按主仓冻结度量／阈值检查无新增问题；Controller保持2550行。
- 后端正式恢复与原生结算2文件105项通过（46.2秒），包含改前失败的compacted回执、实际archive_and_compact和有／无Steer路径；随后新增中断／失败再压缩两条反例与夹具等价调整，7项定向通过；10项冻结检查通过，初次测试分支HX011已按表驱动修正，不改规则。不扩大为全仓通过。
- 主会话自己的隐藏IAB，390×844隔离真实App／Controller：实际Send后历史／Pending仍等待即可见User、Thinking、工具和流式正文；历史完成只剩Restoring live updates…；Pending返回后提示消失、球存在且Stop可用。失败Noting后台刷新只显示一条Retrying且不锁操作；断线与重连尚未恢复时同位置提示且主按钮等待；全部恢复后提示消失、草稿保留、Steer可用、零Toast。真实业务请求全部受控替身，无生产模型／用户页面操作。
- 0.1.7本地原件和副本核验通过，用户手机损坏根因未证实；后继APK产物核验不等同真机安装／生命周期通过。

## 保留事项（不自动立项）

| 事项 | 当前边界 |
|---|---|
| 跨进程busy Instant Reminder | desktop来源且Gateway持Main租约时，Instant可能另起Web运行而非转Deferred；10/24已确认，本轮未修。Deferred已验正常，未发现原文误外发 |
| 微信主动出站`prepare failed` | 既有失败与脚本exit 0误判风险仍独立保留；本轮connected不等于主动出站恢复，未试发 |
| 微信早期正文投递时序 | 18:18长正文已定位为刚生成即发送且拆成两段；更早正文是否积压尚缺逐消息发送身份回执，不将现有记录推断成已修 |
| Conversation时间／分页 | Compaction末尾Conversation start已本地修复并列入看板。旧第10项pagination反馈及47条历史时间副本仍未关闭；没有生产恢复写入授权 |
| 旧失败Noting内容重建 | 空工作态历史反例在原HEAD2122223复现；本轮只验证恢复入口生命周期，不冒称其内容重建已修 |

已关闭的拍照参数、首触Send、会话列表、补水流量及旧Kimi专项不重新挂账；Reminder语气、编排分流与触达白名单归模型行为调优，不变成开发任务。SOUL／workspace AGENTS不因文档整理改写。

## 证据入口

- 本轮恢复：ignored `.hermes-dev/frontend-018-20261026/`，前端ignored `.archive/qa018/status-evidence/`；最终日志会随收尾复制到同目录。
- 原388839c部署／APK：`release-388839c/apply.log`、`final-388839c.json`及Downloads交付旁SHA／verification收据；旧JSON的awaiting发布语句属于构建当时，实际上线结果以apply.log为准。
- 历史冻结／验收：[README索引](README.md#重要文档索引)及[运维记录](docs/operations-log.md)，不改写原报告时点。
