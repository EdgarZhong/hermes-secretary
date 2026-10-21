# Hermes Secretary 当前状态


**托管集成更新（2026-10-21）：** 后端产品快照`3b48cf0`、Web`bf279b2`已提交推送。最终前端68份1038项通过、1跳过；实际隐藏IAB复验详情加载后同UID Thinking保持手动展开及正文、19帧顺序／中途Heartbeat唯一卡、八次重排阅读锚偏移不变。修补包含Context引用稳定保护（80张静态卡不因纯文本帧重绘）。新版439文件dist构建成功，0.1.3/1003最终签名APK已完成，32,048,497bytes、SHA5c9cabe4…6f98b，实际439文件与新dist一致；旧ad7e484包只保留为中间候选。第三次全新独立Verification为19条17符合／0违规／2不足，F03/F04关闭；本轮受限交付，正式Validation未启动。真实Android视口／Insets／IME和实际通知响铃／横幅仍缺证据，未声明全验收或上线。详细看板见本轮plan，生产未部署。

## 自主口径收敛 · 待用户追认

暂无。Android恢复退避已获用户明确确认：10／15／20／30秒；生命周期回前台立即刷新并清空退避，再从10秒开始。此前45秒、分钟级长退避及5秒单次刷新方案均已废弃。UI-CAM-01已获用户确认，拍照压缩保留当前实现。2026-10-21本轮用户明确确认：升级APK迁移至新的响铃＋横幅通知通道，并尽量保留用户主动静音设置；已实施并完成原生定向测试，真机响铃／横幅未验。

## 当前阶段

**2026-10-21 手机多故障修复收尾：** 采用Sol/high分包、主会话亲审集成。用户已放弃旧置顶Kimi工具调查与恢复，不重开、不动其历史／排期。用户最终明确Android逻辑视口380 CSS px、等比显示，覆盖390；通知升级迁移新响铃／横幅通道并保留可识别主动静音，launcher保完整logo／深纸背景。全部前端修补后统一dist与0.1.3/1003签名APK。只准备上线，不自动部署或向生产发测试消息。隐藏IAB现已恢复，只在自有隐藏页补组件实际呈现，不绕过显示保护；真Android运行与完整App验收仍未完成。

| 当前任务 | 当前状态／完成条件 |
|---|---|
| MOBILE-RENDER-02 | UID位置优先旧尾锚、同Turn后缀续接、工具occurrence／详情、DOM身份锚／程序scroll反馈与底部O(history)测量修复已实现。真实512帧＋200cards旧失败／新通过。浏览器新增F04后已修同身份手动展开的live→history交接，保真正完成折叠／scope及phase隔离／实际正文，并保护Context稳定引用。68份1038过1跳、稳定浏览器上述场景通过；F04第三次独立复审已关闭；设备未验 |
| SUBMISSION-RECOVERY-03 | 可选ID沿原生writer落真实行，同Profile／Conversation只读核回执；晚ACK／unknown／后续草稿与rewind不复活处理已实现并亲审。45项后端、5项前端及既有4项恢复有效；worker仅进程内真实入口，新连接非OS重启 |
| HEARTBEAT-CARD-02 | 真实落库observer即时卡片、源UID去重，不按Thinking造卡；追加emit前异常恢复／入环后不重复修补，17相关／最终7Heartbeat与10检查过，独立复审已关F03；真实浏览器中途唯一卡通过 |
| WEIXIN-REBIND-03 | Gateway沿目标native身份初始化，入口peer key只投递；旧身份／历史／Notebook／排期及新绑定保持。7份111项与10检查过，主审接收；生产只读无需修库，真实入站仍待明确部署后正常用户消息 |
| AUX-TITLE-02 | 实际SDK区分私有参数，18最终重叠定向及较早360相关通过；真实Kimi k3-256k/OpenAI SDK单请求2.49秒标题成功，无生产Conversation写；线上仍旧代码 |
| ANDROID-RECOVERY-02 | v2 HIGH／主动静音迁移、恢复退避、原生380视口／Insets／图标safe zone与资源已实现。70原生过，实际资源mask亲审；最终同签名0.1.3/1003已统一打包。真WebView／键盘／vivo launcher／声音横幅未验，不冒称全绿 |
| 独立门禁与交付 | 原始及第二次报告保留；F03关闭，第二次新增F04已修，第三位全新fork-none已审最终bf279b2，19条17符合／0违规／2不足。Android真实证据F01/F02仍阻断，正式Validation前置尚未通过，未启动，不把主会话组件补证冒充独立验收 |
| KIMI-TOOLS-02 | 用户关闭，不自动重开；原会话／历史／排期未改，保留原调查时点，不宣称精确模型根因 |

**Conversation级Heartbeat已完成并上线（2026-10-21）：** 后端`ed94619da8`、固定前端`0b8843f`已联合上线；按目标Profile全局Noting分支，稳定Conversation自有状态、独立设置/暂停/恢复/清除，UI runtime后台唤醒，压缩共享，新建/reset/fork独立，关闭原生。156项有效定向、冻结10检查、独立负例与4个真实K3/High样本通过；正式serve关页/回收后自然61.9秒执行、148.6秒停机跨两due合一次、暂停/清除跨重启不复活已实测。首次成功回执遗留原生进程限制文字被主会话发现，旧门禁结论更正；已修补并经新独立36判据/18场景前置复审和实际WS en/zh输出复验。Alex原置顶Conversation已正式设7200秒/空prompt/active/count0；补发版只读核定义全字段、revision1及19:58:09到期锚点保持，未提前模型触发。两独立角色已补审最终三收据，Verification36条全部符合、Validation18项全通过，范围内整改清空；交付见`.autonomous/20261021-conversation-heartbeat/final-delivery.md`，持续目标完成归档。439文件及三库保护数据/配置/微信绑定对账一致，双SPA正常、Web/Gateway active且微信connected，NRestarts0。禁止Astra，全部子Agent sol/high；无新产品口径待追认。

**Heartbeat前端卡片已联合上线（2026-10-21，用户已确认浅／暗色效果）：** 仅将后端原生`role=user`且完整`<heartbeat>…</heartbeat>`包装的消息展示为独立卡片；原消息角色／原文／UID不变，普通文本、Assistant回复及其它消息行为保持，`HEARTBEAT_OVER`不参与运行判断。复用Reminder／Framework结构与阅读宽度，陶土橙浅底／深色棕底、HeartPulse图标、固定标题`Heartbeat`、默认折叠；展开保留内层timestamp／Additional prompt，不加普通User操作／附件／外时间。后端模板与UI唤醒实现由现有Heartbeat任务负责，本轮不覆盖其改动。主会话亲审并以真实后端模板、正式TimelineMessages在隐藏IAB验证360×792／1280×800，暗色计算配色为预期值且无横向溢出；截图在`/Users/edgar/.codex/visualizations/2026/10/21/01a15d70-fbb7-7190-b233-211cd9270a42/heartbeat-dark-mobile.jpg`、`heartbeat-dark-desktop.jpg`、`heartbeat-dark-expanded.jpg`。用户随后授权测试／构建／前端提交推送，部署交由后端统一处理；暂存18文件，仅含本轮timeline／approval／Patch／Heartbeat，不带此前Android变更。精确暂存树`f8de8c4d4f0f5a525dfb57ac9c27de8fc3b54fe8`隔离验证：60份917项通过／1项跳过，TypeScript与生产构建通过；mock构建亦通过；Web提交`0b8843f`已推送并通过`ls-remote`核对`origin/secretary`，现已随Heartbeat联合部署。此次暂存已清空，工作区只保留此前Android任务改动。生产包与日志在Web仓ignored`node_modules/.cache/hs-timeline-check/`；首尔439文件逐字节SHA一致，未重打APK。

**Patch replace审批diff已联合上线（2026-10-21，仅前端范围）：** 用户授权“对于patch工具的审批，根据replace工具参数补上diff渲染”，限定“不额外加后端东西”。已从App当前Profile／Conversation／runtime和queued／running真实工具节点向审批组件接入参数，按`path/old_string/new_string/replace_all`展示完整路径、红色Before／绿色After拟替换片段，空new_string表示删除；原文换行／React转义保持，文案不承诺原生模糊匹配是exact。优先已有明确调用身份，否则仅依原生`<write to …>`／`<patch> (plugin approval rule)`目标与唯一待处理工具关联；兼容protected_instruction_file仅basename对完整路径，同名并发／write_file竞争／旧Turn／其它owner／参数不全均不猜，原选项仍可用。仅replace，不扩V4A、write_file或读文件重建完整文件；不新增后端字段、接口或RPC，不混入上轮failed_turn改动，不改审批／Clarify语义。参数总片段超过65536字符或1000行时不造截断预览，保留审批。审批包59项定向与mock24项、typecheck通过，主会话改文案后相关21项及最终生产build通过；亲审App正式接线／回归，隐藏IAB 360×792与1280×800预览无横向溢出、44px按钮保持。本地真实组件截图在`/Users/edgar/.codex/visualizations/2026/10/21/01a15d70-fbb7-7190-b233-211cd9270a42/patch-approval-mobile.jpg`与`patch-approval-desktop.jpg`。前端已纳入`0b8843f`并推送`origin/secretary`；已随Heartbeat部署，未重打APK。

**失败提示卡片与审批排版已联合上线（2026-10-21，按后续联合部署授权）：** 后端只在API等待取消和预算summary取消的明确诊断生成分支，为原本就会落库的工具尾收尾消息标记`display_kind=failed_turn`；无正文／整轮状态匹配，不新增原本不存在的状态行，不误标模型回复／部分回答／工具。Web按该类型展示原文卡片，复用原中断卡片外观与Assistant阅读宽度，不加System或其它前缀、无Assistant操作栏；取消`turn_terminal`额外派生的中断／失败提示卡，真实正文、Thinking、工具恢复／去重／rewind保留。slash的`temporary`／`command`表现和生命周期保持。Compaction全宽与加载历史入口对齐且保留样式，加载入口不改。approval说明与完整命令分区，长路径等宽换行；手机按钮纵向、桌面两列，44px触控高度，原生choice／顺序／授权范围／关闭与Clarify行为保持。本轮三子Agent包已由主会话亲审接收，保留已有Android等未提交修改；前端已纳入`0b8843f`并推送`origin/secretary`；后端failed_turn来源标记已随`f32d70f703`提交并部署；历史原文未迁移，未重打APK。

**本轮验证与限制：** Timeline等10份定向238项；审批请求30项及mock24项；后端核心4份38项、网关用量／中断14项通过，后端冻结10检查通过（health 0 blocking／0 advisory），最终前端typecheck／生产build通过。后端额外两组已有问题已在未改HEAD `2990444dc6be`隔离副本复现：`test_secretary_slash.py`6项fixture初始化缺`anchor_message_uid`；`test_failed_turn_retention.py`18过、1项异常回执未发预期complete。未放宽门禁、不声称全部测试全绿；后端证据ignored`.hermes-dev/failed-turn-20261021/`。主会话自建隐藏IAB检查实际TimelineMessages：仅真实failed_turn行显示无前缀卡，metadata不额外造卡，partial／slash仍为正文；审批360×792和1280×800均无命令横向溢出、四choice完整、按钮44px，打开聚焦弹窗而非批准按钮。截图为本地mock真实组件，未执行样例命令；在`/Users/edgar/.codex/visualizations/2026/10/21/01a15d70-fbb7-7190-b233-211cd9270a42/`保存`approval-mobile.jpg`、`approval-desktop.jpg`、`failed-turn-final.jpg`。

**此前诊断纠偏与旧历史边界：** 首尔Alex实库截图两类额外文字都已持久化，并非slash临时输出：15:57:35的id=10412已有failed_turn，16:00:42的id=10422取消诊断未标类型；user id=10411／10419另有turn_terminal才造成额外卡。此前单归因为非持久实时回执的判断不完整，现已同时处理新诊断的来源标记与前端卡片。旧无标记历史行本轮不猜测分类、不自动迁移，仍按普通正文；当前已按后续授权部署，新诊断来源标记与前端分类生效，旧无标记历史保持。

**两项Conversation调试入口已上线（2026-10-21 15:35）：** 用户要求将按Conversation清空系统提示词缓存、失败Noting热恢复一并实现并上线；清理目标为Alex置顶会话，清后只等下次active原生重建，不主动离线重建／模型Turn。缓存清理须覆盖持久root与旧tools固定副本及对应内存；历史／排期不改。用户进一步明确：Noting恢复不新增专门持久快照，利用已有原文、压缩边界、子任务记录等重建失败当时Active Foreground与Notebook工作态，沿原生runner／Commit Gate及当前timeline尾部Framework发布；不以没有专门快照或缺少逐字wire为拒绝条件，不额外加门禁；穷尽现有原文／版本／子任务记录恢复，实际缺项具体报告，不用当前父上下文替代。

`conversation.context_cache_clear`、`secretary.noting_recover`及状态查询RPC已随`c21b1d5b9c`部署；Alex置顶Conversation通过正式RPC清空root／工具pin，等下次正常active原生重建。三条实际本地HTTP接线通过（缓存下一Turn、冷态恢复尾部发布、已有Main队列），冻结10检查通过；定向分组及两项既有测试失败详见operations-log。本次未主动执行生产模型请求／Noting重跑，历史、排期、其它Profile缓存保持；Web／Gateway在线、微信connected。稳定接口见07 §12，证据在ignored `.hermes-dev/conversation-debug-20261021/`。

**Alex百炼模型目录已排除（2026-10-21 13:44）：** 用户要求排除语音阿里云Key自动带入选择器的全部百炼模型列表，保留独立Kimi／DeepSeek／GPT。仅Alex设置model_catalog.excluded_providers为alibaba、alibaba-cn及Coding Plan／Token Plan的国际／中国共六slug。前端同一model.options RPC核实Alex百炼3组194条消失，Kimi11／DeepSeek2模型集合保持，study GPT14与默认DeepSeek2保持，当前Provider／模型未切换；语音Key、其它Profile配置和认证文件指纹不变。页面已有目录需重新加载；未控制用户页面，未作视觉验收，无代码／服务重启／模型请求。备份与收据见operations-log。

**Alex／study工具配置已同步（2026-10-21 13:40）：** 用户要求关闭Alex的vision_analyze、不再顶层注入，并把这套工具配置原样复制给study。两者均agent.disabled_toolsets=[vision]；原生工具选择／折叠配置沿相同默认，kimi-tools与playwright完整定义复制、保持enabled和lazy。两Profile正式只读组装均26顶层，Web/TUI5个／微信4个原生折叠；延迟MCP未连接初始化，不计入此独立组装数量，加载后沿原生Tool Search折叠。模型／认证／Noting和Scheduler开关、其它配置与历史／排期保护表指纹保持，未重启服务或发模型请求。后续原生刷新／新Agent生效；备份和收据见operations-log。

**Main工具顶层声明已部署（2026-10-21 13:32）：** 用户确认Scheduler／Notebook Show按各自独立能力开关完整进入API顶层`tools`、退出折叠目录；Scheduler仅受scheduler开关，Notebook沿既有全局Noting读取门禁，当前Conversation的Noting参与不控制二者。`f7d93351ca`已部署Web／Gateway；部署时正式Profile配置独立组装核实两入口均27个顶层工具（后续按用户要求关闭Vision后为26），原生折叠Web/TUI5个／微信4个，差异仅desktop_project。303项相关测试通过，1项Noting全局活动任务计数失败在未改基线同样复现；冻结10检查通过。隔离K3样本：重复旧历史的Scheduler正确，新上下文Notebook正确，重复旧Notebook历史时有一次复述旧结果未调用，指定tool_choice对照400；不声称模型行为全通过。三库历史／排期／待投递／绑定全行SHA及配置保持，无主会话测试消息、排期写入或自动回退。07§8.2、运维记录已同步；证据ignored`.hermes-dev/main-direct-tools-20261021/`。

**Android APK 0.1.2 自动恢复已交付（2026-10-21）：** 按用户最终口径，首次打开正常加载，锁屏／后台回前台立即原生reload并清空退避；此后WS未恢复按10／15／20／30秒重载，封顶30秒，connected即停止。无JS／明确初始化错误走原生兜底，正常慢历史不误刷；仅权限／焦点pause和原生附件结果返回、第三方认证页保护；通知目标跨刷新保留、Active重新观察、去重不清。前端／相关92项、原生52项及最终release构建通过，正式包headless Chromium验收：后台／解锁回前台重建JS且路由保留，短断3.487秒自行重连不刷新，持续故障11.550秒观察新页并12.166秒恢复；360×792。交付ignored`.hermes-dev/android-apk-20261021/Hermes-Secretary-0.1.2-arm64.apk`，32155481字节、版本1002、SHA256 `b8b044fef12fe2424a5adf31a909e42a6074821ae2166c7f7c5a99b6b57faafb`，原签名，可覆盖升级。未发生产模型消息／部署或提交；真实手机节电与长期运行未验。证据与实现详见运维记录。

**Scheduler schema最小修复已部署（2026-10-21 12:57）：** 用户确认修复并部署，明确不动主会话历史和已有排期。`fba851b2ef`只为Kimi转换层无属性定义、未显式限制额外字段的泛型object补`additionalProperties:true`；保留required、明确关闭对象及类型字典约束。181项相关回归与冻结10检查通过，修复后三次隔离K3-256k／High查询／重复历史／创建均正确；部署后正式传输层再验重复历史查询正确。Web／Gateway实际同提交、微信connected、自动重启0；Alex10258条消息、20排期、13pending Reminder及三库全部历史／绑定前后全行SHA一致，配置指纹保持。未向主会话发测试消息、未改排期或回盖DB。原调查表明API schema触发Kimi兼容性问题；10:27与12:30均为Chat，上午成功不能被解释为协议切换。首次暴露的确切原因缺原始请求证据，Notebook首调／大快照不是必要条件。备份、两次临时校验脚本问题与最终收据见operations-log；证据ignored`.hermes-dev/scheduler-tool-investigation-20261021/`。

**Android APK 0.1.1 图标更新已交付（2026-10-21）：** 复用原logo、现有主题dark paper #232120居中组合，普通／圆形自适应启动图标及5档密度资源已接线；版本0.1.1／1001，沿用0.1.0签名支持覆盖升级。交付件ignored`.hermes-dev/android-apk-20261021/Hermes-Secretary-0.1.1-arm64.apk`，32155961字节，SHA256 `2d8a6926c3dfe00fd5362d3b4f3e45d6ba934921a737e7e6bc793d67bec99242`。release构建、22项图标资源接线／20张PNG可见RGBA一致、签名／非debug及16KB对齐核验通过；439前端资源中438与0.1.0逐字节一致，另一份仅构建时间变化。本次未重启模拟器或重测网络／通知，不新增真机验收结论，细节见运维记录。

**Noting成本与阈值建模（2026-10-21）：** 用户最新确认按每个Conversation真实轨迹估计阈值，统一“是否提前整理”和“何时提前整理”，阈值为唯一决策变量、长期总费用为优化目标；不再单独估计开关，候选必须含“不提前整理／原生接管”（数学上T=∞），全局资格与Force／原生安全线保持，尚未实现或改配置。统计上下文增长用冷启动批次之间实际prompt差，不累计usage；频率需区分冷启动次数和同批热续聊，固定每冷启动增长时提高日历频率只加快回本、不必然改变最优token阈值。前版每Turn恒冷／每次30K／不同时间窗口不能互相替代。用户纠正固定历史比较为昨晚手动Compact约21:38、假设Noting当晚热父成功、比较到今天最新使用；已补齐服务器纯数字日志并与本地145主API账本逐类对齐，期间18Turn／46API至13:05，8cold-first。Notebook提前出现及无整理路线移除Notebook均计差额；中央不整理约35.02元、整理正常15.92＋一次热Noting4.75＋Compact代估2.19＝22.85元，净约12.17元；参数情景净10.29～12.40元，异常两Turn不计缩短收益仍约6.50～8.14元。API反事实预算、非订阅账单；Compact本次无完整独立usage、Notebook为代理分词、冷热／请求／输出路径保持是假设，非长期最优证明。此前混合窗口建议暂关的费用依据撤回，不据本次手动事件宣布自动Idle长期最优。未改线上开关／阈值／delay，自适应仅讨论。证据本机ignored`.hermes-dev/noting-cost-probability-20261021/lastnight-fixed-scenario.py/json`及独立复核，方法限制见运维记录。

本轮已形成[自适应阈值初稿](docs/adaptive-noting-threshold-proposal.md)，README已索引；用户明确简化公式有定性分析／调优／算法设计价值，§6.1保留回本式及平方根式，仅解释方向，不作实际求解器。基于12严格／14修正cold批次、全部热API、共同工作量的条件预测，经济性建议保留Idle提前整理、初始建议96K＝98304（候选低谷80～96K）；中央每100批次80／96／128K／∞约305／314／349／459元，96K比80K贵约3%但少约24%维护。15种参数情景仅为假设敏感性，单维护样本、native/provider映射、异步状态及质量不足以证明长期最优。只完成方案与本地分析，未实现自适应／改配置；线上仍131072、delay500秒。脚本及参数见ignored`batch-threshold-forecast.py/json`，完整收据见运维记录。

**Android APK 已交付（2026-10-21）：** Tauri 2、内置前端、已签名release，Android8.0+／arm64，0.1.0／1000，35.6MiB；ignored交付件`.hermes-dev/android-apk-20261021/Hermes-Secretary-0.1.0-arm64.apk`，SHA256 `1135911a0ee04beb0a4d16fd9e6ce442ce3f998a356cd8a7088cf9f1447c08dc`。跨Profile全局Active状态复用、完成receipt＋精确History行核验、后台原生通知／点击导航和临时WebView保护已接线；普通网页不启用，无后端协议或生产部署变更。真实已登录API200／99–111ms、WS101／gateway.ready2.209s、TLS1.3；模拟器360×792、重启登录保留与Conversation恢复、原流光恢复已验。通知54项、定位／阅读18项、原生26项及主题脚本7场景通过，隔离Android并发通知／保活释放／点击验收通过；未做生产真实Turn通知、真机及长期后台验收。用户最后确认黑边无需重测；模拟器物理2400与显示2376差异导致上下各12px黑边，已关闭准备调整但尚未改物理配置，按用户要求停止重测。详细实施、签名、调试镜像限制和证据见运维记录。

**生产旧失败 Noting 已补回（2026-10-21 11:53）：** 用户确认今天用工作量较少的一次性脚本，热调试入口只入下方看板。服务器恢复失败当刻251条父前缀／旧root／25工具，冻结原Anchor与空Notebook工作态，调用已部署原生K3-256k／High／Chat runner及Commit Gate，无裸SQL写入／monkey patch／代码发布或服务重启。337.83秒、1Turn、11请求；maintain20次中15成功／5校验失败后修正，finish1次，提交15条目`snap_7b7f6972049c4053a9ab064fd5f1d2a4`；Framework单行追加当前timeline末尾，正式REST读回一致。原会话行及模型元数据、旧失败child原文、全部排期与既有绑定原样，原admission3由原生流程重绑定新child，旧登记受限备份保留。执行后Web空闲、Gateway活动0、租约0、微信connected；13条正文来源为旧Anchor之前时间范围、2Candidate沿Notebook refs，不冒称逐UID或逐事实质量全验。用量非缓存输入155668＋缓存1529600＋输出8959＝1694227，费用未知。原失败与脚本校验误用按时点留存，详情见operations-log。

**study Provider配置已完成（2026-10-21）：** ChatGPT subscription已通过原生`openai-codex`独立授权；用户确认主模型GPT-6 Sol／High，普通子Agent与后台delegate_task通过`delegation.model`使用GPT-6.1 Sol并继承High，Noting继续跟随主模型。正式Profile作用域与委派runtime解析通过，两个模型各1次真实请求成功（各38 tokens、无重试、不写Conversation历史）；未另启动完整前台／后台委派任务或Noting。凭据0600只留study运行Home，Alex配置及其它原配置保持，未重启服务或改源码。首次auth add漏存及原生登录绕行、证据与回滚记录在operations-log。

**移动端重复登录续查已落实（2026-10-21 10:44）：** 用户确认跳到Authelia登录页，要求每天访问至少一个月免重复登录，并表示可能漏勾“记住我”。线上普通登录原为12h、记住我1M；同手机UA昨22:21完成双因素、今10:26再次302，12h期限与本次现象高度一致，但无当次勾选状态，不冒称唯一根因。现已将普通／记住我均设31d，保留5d空闲期；原生二次认证规则、Cookie域和密钥未改。隔离同版本真实认证已核两种登录Cookie／Redis TTL、认证及Redis重启保留；生产仅重启Authelia，Redis未重启、有效键保留，公网HTML302／JSON401及health200通过。失效旧登录需重新认证，新登录才取得新期限；手机新登录及31天长期使用未实测。详细证据与回滚见[运维记录](docs/operations-log.md)。

**移动端阶段一与Noting联合交付已上线（2026-10-21 01:30）：** 未开worktree，三个实现包与并行Noting会话已亲审并集成；首尔Web／Gateway实际运行`0bdddfc133`，Secretary前端`1d1b1a7`的439文件SHA通过，Caddy2.11.7已加载限定gzip／私有哈希静态缓存。真实同200行cards 863366B→212094B，实际Caddy gzip54696B；唯一图转换成功／fallback0，引用实际可下载。隐藏IAB经SSH回环观察静置详情0／图片0，展开单卡1次6783B，进入视口单次488384B图片成功解码；公网只验Authelia入口，未冒称登录后或蜂窝验收。纯图片持久受理／同row UID原子认领及失败路径已完成定向测试，未加生产Turn。Noting真实K3/High在1Turn、6HTTP200中正常维护并正式提交3条Snapshot；保留首版400及harness额外校验误用证据。用户C08简化部署后Validation、C09禁止自动回退已落实；切换后空闲检查短暂未通过，保留新版正常运行并续完Caddy，无回退或回盖DB。部署后原Alex10161／host2行内容身份、全部排期和微信绑定保持；既有7条Instant中最近2026-10-21 10:00，Scheduler线程／微信connected／发送工具及原生冷恢复路由已核。未提前触发提醒或测试发送，不把未来触达写成已发生。完整范围、有效证据与限制见[本轮交付](.autonomous/20261021-mobile-phase1/final-delivery.md)及[运维记录](docs/operations-log.md)。持续目标已完成；阶段二及手机蜂窝短实验不在本轮实施。

**K3-256k最小Anthropic验证已完成（2026-10-21）：** 用户明确授权“小贝子”使用实际`k3-256k`补验证；严格3次真实请求、无重试，High、原生Coding Anthropic端点。正式顶层注册1/1成功且参数完整；末尾system.tools携OpenAI schema及Anthropic schema各0/1，模型均表示未提供维护工具。主会话亲审脚本并独立核验实际wire／响应哈希、精确模型ID和父前缀不变；不为review复跑。总输入含缓存1,665、输出510，合计2,175 tokens，实际费用未知。与便宜模型方向一致，但只证明所测两种写法未生效，不推为官方或所有Anthropic动态机制均不支持。仅本地隔离虚构内容，无Chat重测／长会话／SSH／生产数据，不改实现／配置／部署；证据见[运维记录](docs/operations-log.md)及ignored`k3-256k-summary.json`。

**前轮便宜模型隔离验证已交回（2026-10-21）：** “小贝子”12次Coding `kimi-for-coding`／High验证中，Anthropic末尾两种动态封装0/4，顶层注册2/2；Chat动态2/2参数完整，不外推K3的Anthropic能力。历史上“不切协议”讨论限制已由最新用户授权覆盖；当前进入原生Chat配置及Noting接缝实施，实验原文与边界见[运维记录](docs/operations-log.md)。

**Noting模型对照调查已完成（2026-10-21）：** 按用户要求直接复制本地同步DB，用本地代码／独立Profile及数据库跑DeepSeek；原wrapper／root恢复，实际发送父历史250条，投影差异如实保留。`deepseek-flash`／High在87.07秒、8次API、1个Turn内完成，27次maintain中23成功／4字段校验失败，正常finish并提交19条目；无History调用，总token1,193,633。原Kimi50次History已记录7,913,013 tokens，另有未入账总结用量。主会话亲审正式接线、请求工具哈希、usage及副本Snapshot；Kimi10个虚构内容对照支持正文schema与正式／动态工具声明的兼容差异，动态system.tools仅已实测Chat接口。用户确认理解独立结构化声明及缓存边界，未要求改生产Anthropic接口；未改Prompt／工具面／模型配置或部署。接到用户限制后未再访问云端或复制云端材料；完整范围、差异、证据与结论边界见[运维记录](docs/operations-log.md)。

**语音体验第二步已上线并验收（2026-10-20）：** 首尔已上线`532cadb4d8`，显式启用`gateway.stt.echo_transcripts_with_reply`；转录保留到模型首条实际回复合并投递，成功ACK才消费，interim／final／错误及队列分支已覆盖，不污染模型assistant历史。Alex上传改为16kHz单声道AAC64kbps，原始SILK保留；341KB→49KB，压缩样本5.03秒／6.07秒、转录与旧结果一致，网络波动不作固定延迟承诺。188个不同相关场景的分组证据有效，完整冻结10检查通过。原绑定、既有10155条Alex消息、adapter／Key及study配置保持。新微信语音已入库且assistant历史无回显头；用户已明确确认“已收到合并回复，没有独立通知”，真实显示验收通过；运维与回滚见operations-log。

**首轮已完成 · Gateway语音与缓存同步（2026-10-20）：** 首尔已部署`b0c9252`，包含Noting修复`02964de`及严格的`Voice message transcript: <转录结果>`前缀。Alex复用原生STT Command Provider、SILK解码和原有Key，调用`paraformer-v2`非实时文件API；私有阿里临时链接48小时失效获用户接受，原生媒体缓存24小时龄期清理，转录message正常入库。真实新微信语音已转录，Alex回复由用户确认收到，临时文件清理通过；33项相关回归、57项适配离线测试和冻结10检查通过。配置只改Alex，原绑定及既有10153条消息保持；study／host配置不变。Profile Home已是8文件白名单，两Profile缓存探针实测均不回Mac，快照只有3数据库，无须改同步策略。13.45秒预检的主要耗时为上传6.12秒和结果下载3.39秒，真实新消息入库到Alex生成回复另约30.75秒，不混算为ASR耗时；首轮未实施音频压缩。详见运维记录和ignored `.hermes-dev/gateway-voice-20261020/`。stuck技能已按用户要求改为完整报告直接贴用户、默认不派子Agent；移动端网络调查独立保留。

**Noting预算窄修复已上线（2026-10-20晚用户确认）：** Noting原生每Turn迭代预算耗尽时，经既有Commit Gate保存合法工作态，所有触发来源共用，与`force`触发无关；末次调用已成功finish时保留显式结束。无模型／Prompt／预算变更。13个新增边界场景通过，所在测试文件54项通过，冻结10检查通过；相关5文件首次156通过／2失败，两项均在原版复现（旧Snapshot ID正文断言、旧文件活动任务计数污染），不冒称全绿。`02964de`已随`b0c9252`部署，未重跑线上预算耗尽场景、未恢复旧失败任务。21:38:15–21:51:31旧生产任务达到50次上限后failed、无Snapshot为部署前事实；口径已同步07，原证据在`.hermes-dev/pinned-mobile-20261020/`。

**当前调查交接已完成：** 用户要求调查者只取证／梳理现状，网页版GPT（Astra／Extra）提方案；新增明确要求报告与必要留存一起ZIP交付。报告覆盖全部22组反馈，见[手机Web／微信调查](docs/mobile-web-investigation-20261020.md)。服务器17:58—22:42:59日志原件9份／11.67MB已固定、SHA256复核通过，另22:57在线一致性DB备份186.51MB仅留服务器；手机两轮22:21及22:35起的CDP／UI事件已保存。实测蜂窝cards68.199／56.090／64.684秒，主要在响应头后的正文传输；稳定Wi-Fi0.404秒，WS可同时低延迟。纯图片即时用户回执缺口正式链路离线复现；本次唯一授权代点26字符纯文字Send气泡成功，不代表文字历史问题关闭。早场手机包、认证具体失效原因、灰Send内部条件及桌面滚动仍有缺口。Ignored证据与ZIP在`.hermes-dev/pinned-mobile-20261020/`；敏感原件只留服务器，ZIP白名单脱敏。ADB观察与转发已结束，未关用户页、未部署或改线上配置。此前未验证气泡／渲染候选已保存并撤出源码，不混入交付方案；Noting独立本地修复状态见上段。

**2026-10-20用户确认：部署基本告一段落，第一版可以正常使用。** 本轮文档／仓库整理及追加微信修复已完成，17:58部署首尔；后续按新任务推进，不自动重开旧挂账。

- 首尔正式入口、双SPA、Alex / study Profile、NM / Ebbinghaus迁移及三条Mutagen同步已落地；旧部署等待、TCC阻塞与初始化过程不再是当前任务。
- 已上线后端功能基线 `ed94619da81547bcb9e27aab60b608b2310e6890`（含此前能力、Conversation级Heartbeat、配套failed_turn标记及持久成功提示）；前端 `0b8843fb87bf0ba109f7b744f4ae96faf09df597`；插件收尾 `f11a8db6c32e109bdc1de6c39c2920bcad14d617`已同步。后续纯文档提交不等于运行版本改变。
- Alex默认 `kimi-coding/k3-256k`／原生Chat及Coding `/v1`，窗口262144、thinking High；目标绑定Conversation当前tip同路由，Noting / Scheduler开启，联合Idle500秒／131072 tokens。已有Conversation保持自身模型配置；study默认`openai-codex/gpt-6-sol`／High，委派子Agent为`gpt-6.1-sol`并继承High，Noting跟随主模型；NM Thread目标仍继承考研Space，可选`thread_sync_space`能力保留。
- 微信绑定采用原生Gateway control socket与Conversation ref；Alex工具 `~/scripts/alex/weixin_bind.py`，调用方直接 `bind --self`。Kimi凭据已补到Alex自己的受限`.env`；多余Gateway凭据注入与用户副本已回滚，正常重启后连接及原绑定保持。独立K3请求HTTP200；未把它冒称新微信消息端到端验收。
- Prompt缓存清理已按当时授权完成，后续沿原生正常Turn懒构建，不追加离线重建。个人工具统一`~/scripts/`，只读保护、显式非空`--space`等规则见AGENTS／08。

## 本轮交付

| 工作 | 状态与完成条件 |
|---|---|
| 阶段一P1-01～06、08 | 已实现、亲审、定向测试及构建，联合部署；线上同窗字节与按需请求观察完成 |
| P1-07预算收尾 | 原02964de已部署，本轮未重复应用；新Noting包验证仍正常finish并提交 |
| Noting／Provider协作 | 并行会话本地整包接收，0bdddfc已上线；保留原生Provider，仅Alex默认与绑定tip切Chat／High |
| 后端提醒健康 | Web／Gateway active且自启、Linger=yes，0自动重启；7条Instant排期与绑定／工具保持，最近10月21日10:00；到点实际触达尚未发生 |
| 验证与限制 | 冻结10检查通过；真实回环历史／隐藏IAB请求行为有效。未做公网已登录／蜂窝长实验、生产发图Turn／微信测试发送；不冒称全量测试全绿 |

本轮按用户明确豁免不另跑严格两独立门禁；前端286定向与usage54（重叠）、后端投影26及兼容48、纯图受理34及受影响60、Noting dynamic39／summary4／fallback3的原版本证据由主会话亲审复用。冻结检查对初始50214cd基线，附包CDP工具的两项问题已等价拆分并核51事件输出一致，最终0 blocking／advisory。工作区先前手机调查文档dirty保留，不整树提交。运维详情只在operations-log。

## 调试事项看板

| 事项 | 用户确认的范围／启动条件 |
|---|---|
| KIMI-TOOLS-01 · 共同行为模式 | Kimi遇到工具声明／缓存上下文兼容异常后，可能反复误调或无法调用；工具Schema变更后须核对真实API工具面，清目标Conversation的旧Prompt／工具缓存，待下次active原生重建。 |
| NOTING-DEBUG-01 · 热态恢复调试入口 | 已实现并上线（`c21b1d5b9c`）；已有原文／边界／子任务记录恢复旧Active Foreground及Notebook工作态，无专门快照或额外恢复门槛，原生runner／Commit Gate及当前尾部Framework发布。调用、来源回执、幂等与状态见07 §12；本次未重复执行已补回的生产旧任务。 |

## 保留事项（不因本轮收尾自动立项）

| 事项 | 当前边界 / 下一步 |
|---|---|
| 详情接口 | 第10项pagination元数据漂移尚未得到用户关闭口径，暂保留；不主动扩大修复 |

侧栏旧“触摸／键盘均受影响”已纠偏，不再作已证实缺陷；手机重排后转宽屏的顺序同步仅静态观察，未UI复现，详情留运维记录，不自动立项。

用户已关闭／移出工程挂账：拍照参数接受；手机首触Send目前未见问题；会话列表关闭；补水总流量不构成问题；Reminder静默、编排分流句和主动核实／触达白名单属于模型行为调优，不再列开发待办。SOUL.md与workspace AGENTS.md可定初稿，不因本次整理改写它们。

入口识别口径已定：保留Hermes原生Gateway／其它Platform按消息来源轮换和切换时的notice注入；关闭System Prompt中当前Platform的身份注入（现代码已关闭），不再挂“稳定识别待定”。

## 证据与入口

- 通用规则只在 [AGENTS](AGENTS.md)，稳定规格索引在 [README](README.md)。操作、实际版本、备份与回滚统一 [运维记录](docs/operations-log.md)；执行步骤见 [部署SOP](docs/cloud-deployment-sop.md)。
- 固定v5产品意图复审及两门禁按其原版本保留：[Snapshot Index](.autonomous/20261018-product-intent-review/snapshot-index.md)。旧模型归因／Search完整性／Noting来源偏差为已接受的非阻断观察，不重开为新增开发。
- 不把未验证写成通过；历史全量存在失败，后续定向通过不等于全量全绿。原报告、固定证据、Git历史均保留，不将旧PID、Agent编排或过时等待条件带入下一轮。
