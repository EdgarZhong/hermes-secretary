# Hermes Secretary 当前状态

## 自主口径收敛 · 待用户追认

暂无。

## 当前阶段

2026-10-26用户明确Composer闪动发生于移动端网页版，并追问推流不可见是否真正修复。已说明并纠正上轮只交APK、漏掉网页发布的交付缺口：故意阻塞历史／Pending时正式App推流即时可见的744ac30现已从main静态原子上线，receipt=verified，439文件与实际HTTP入口CJ6XWfgz的JS／CSS逐SHA一致；后端fd57123、Web PID3874452／Gateway PID3874455前后不变，双服务active／微信connected，配置／Dashboard不变，无数据库写入、服务重启或生产模型测试。手机已打开页面需刷新一次载入新JS，不把部署当成已代操作手机验收。Composer另项继续按移动端网页输入／浏览器路径调查，不能用桌面窄窗口冒称真机通过。alex旧入口连接失败未执行生产命令，随后按SOP使用首尔入口成功；证据ignored frontend-018-20261026/release。

2026-10-26本轮前端修复已提交／自动push `744ac30`，0.1.8／1008签名APK已构建、完整校验并交付Downloads；上轮漏掉的网页发布已于本次追加完成，现为744ac30。已修复idle／前缀兼容重连仍回底及旧20秒计时抢位，active或已证视口脱离前缀才回底；持续连接手动等待独立保留20秒。正常发送的受理后history-invalidated与运行通知均会冻结旧Timeline而Stop实时变化，是推流被挡住的已复现机制；现同owner／runtime／epoch／连接已核验时，新事件沿原reducer连续呈现，历史／详情／有限cut暂存至统一reconcile，保留完整重读。断线、换owner／epoch、鉴权或cut失败撤销连续性，无新协议／推流框架。271项集成、86项恢复和12项APK校验通过（范围重叠）；隐藏IAB已实际验证慢历史／Pending下User／Thinking／工具／正文及时可见，active期间完成commit、无重发。Controller保持2550行。

**未关闭：Composer满高输入闪动。** 正式App／Controller、200行历史／220显示节点，桌面与390×844下长草稿键入／合成语音增量均未复现；idle Timeline零DOM变更／零scrollTo，active正文沿原容器增量更新，暂停delta只保持active输入也无位移。不凭推测替换field-sizing或宣称已修，用户已明确客户端为移动端网页版，继续按实际移动浏览器输入／布局路径定位，不把桌面窄窗口等同真机验收。0.1.7本机原件及交付副本ZIP／签名核验通过，手机报损坏根因未证实；新构建流程增加CRC、签名／版本／ABI、ZIP／ELF16KB对齐、439资源逐SHA及原子交付副本校验，失败撤销默认旧成功收据。无连接ADB设备，实际安装／生命周期未验；不能由产物核签代替真机结论。细节及SHA在operations与ignored `.hermes-dev/frontend-018-20261026/`，其它后端并行dirty保留。

2026-10-26用户明确要求重新构建并交付Android 0.1.7 APK：以当前已上线前端c29b457的精确dist打包，复用原签名及0.1.7／1007；已构建并核签，439资源逐SHA同线上；安装包已放Downloads，版本0.1.7／1007、arm64／Android8+，未做真机安装测试；不操作生产服务或用户页面。

2026-10-26最新前端c29b457已上线：按用户再次明确的两层分开交付，document内存视图保视口／阅读／展开和临时显示，有可用内存直接展示、不走持久快照展示读取；持久缓存承担刷新／冷启。修复持久Steer误拒整页正文、隐藏详情参与处理、冷读取作废及侧栏全表读取；Controller保持2550行。冷缓存主体193、最终分层200相关测试通过（重叠不相加），类型／构建／独立复核通过。root最终Cnx隐藏IAB：断WS＋API延迟4s刷新，命中200正文／壳、10.5ms取值，导航644.3ms已有246节点且只读；网络恢复无需reload自动接管。之后同页切回首帧246节点、视口57510.5保持、持久展示读取0。439静态／HTTP SHA verified，服务PID及后端fd57123保持，无数据库写入或生产模型测试；0a4eabf候选未单独上线。旧胶囊-only条目需一次正常载入后建立正文缓存，不伪造无正文的旧快照。

本次修复依据：559598b的暖切换验收未覆盖冷刷新，root已承认交付判断错误。旧版真实缓存读取约0.5ms却只有944bytes胶囊，284ms只见LoadEarlier、2344ms网络才有正文；200条历史中的2条原生持久Steer导致整页拒绝。当前已按原始主线“保住画面→后台完整恢复→连贯接管”修复，正文／卡片壳与折叠详情分离；不丢真实Steer、不用隐藏按钮或空白占位假装命中、不跳过完整恢复或授予缓存操作权限。证据与实际运维见本轮operations条目及ignored cold-cache-first-paint-20261026目录。

前版559598b的Working末尾位置修复及对应证据保留，随当前c29b457继续生效；历史版本与测试范围见运维记录，不把旧暖态验收延伸为本轮冷刷达标。

2026-10-26紧急恢复已上线：置顶会话在Skill Create Constructing期间先不可见，23:42显式Stop后仍空白；已确认持久turn_terminal存在但恢复层未对账已中断输出，非Compact补丁引入。通用恢复补丁`fd57123`已亲审、定向验证、冻结10检查、提交／push及main发布，Web／Gateway同版本且active。按用户明确选择等后台自动Noting／压缩自然结束（00:07:20），未中断任务；正式目标200条正文、activate complete=true／idle，root独立隐藏IAB已见正文及可编辑输入、正确模型／推理，Context19%。前端后继静态发布已完成，版本与证据见上文。Stop之前Constructing等待的更细原因继续只读取证，不能把已修的Stop后恢复遗漏当作前者根因。

2026-10-25追加当前工作：用户要求从调试接口立即补跑一次最近原生Compact未伴随的置顶会话Noting；已读回23:28目标local_enabled=true／task idle（主会话未改该开关），现有RPC只有失败恢复，正在以原生manual接缝补最小单次入口，由`context_after_compaction`实现／测试，主会话发布并调用，不能把旧失败child冒充本次整理，不额外Compact或改自动配置。Context高亮新口径已确认：数值实时更新，只有正式Turn结束时单次高亮，工具／流式／缓存／重连更新不高亮；由前端实现Agent和独立review继续落实。隐藏IAB已对root恢复，Thinking及工具内层A→B→A真实位置保持补验通过，活动连续性尚在验证。

2026-10-25当前优先：用户明确停止主会话其它工作并研究置顶会话Compact等10分钟失败，已只读核实22:17摘要到22:27达600秒总上限，300/598秒仍有流式进展，无本次提交；22:28原文续跑完成，80–81%为真实占用。用户随后明确授权立即修复并部署：保留思考与原生带保尾路径，总时限改1000秒；超时或长度／窗口截断只要已经取得非空摘要，采用已收到内容完成原生压缩，并在摘要末尾追加系统notice说明不完整，不因截断直接判失败；无返回内容不伪造摘要，显式Stop仍尊重停止。`context_after_compaction`负责正式流式部分结果到原生提交链路及测试，主会话已完成亲审、默认／Alex配置、冻结检查、main提交及发布；Compact后端93d3b71已线上verified，沿用d644d4a网页，未混入未验前端变更。前端首帧／展开详情由`conversation_first_frame`独立收口，禁止触碰用户页面；若隐藏IAB不可用则记真实验收缺口。

2026-10-25追加：用户实测所有Conversation切换会短暂首屏空白，随后才加载及快速滚动，明确不符合缓存避免空窗的首要目标。当前正在修复同owner暖切换的正文、阅读位置及恢复交接；用户确认“从哪里离开，回到哪里”，快速滚动只用于缓存画面衔接实时画面。前端子Agent `conversation_first_frame`负责正式Controller／阅读hook及定向反例，主会话负责规格、亲审、实际隐藏IAB与最终判定；尚未完成或发布。另核实此前置顶会话`noting off`关闭了全部触发方式，较“暂停空闲触发”范围更大；不能将现有实现耦合说成用户要求，不自动恢复，也不擅改整个Alex Profile，待明确纠正范围。

上一发布（2026-10-25）：正常Turn完成后恢复误拒及Thinking跨Turn错位均已修复、亲审、验证并上线；按用户追加要求移除两条顶部同步／重试横幅，隐藏聊天区右侧滚动条而保留滚动能力。生产后端main为`2b6d5ec`，网页为`d644d4a`，联合发布及只读核验通过。Alex置顶会话已原生noting off，空闲整理／相连压缩暂停，不自动恢复；其它会话／Profile及Scheduler／Heartbeat保持。后端在现有main签出`/Users/edgar/code/hermes-secretary-web-release`，前端源码在`../hermes-secretary-web`的main；不开新worktree、不启自主套件。主仓原有presentation报告dirty保留。

通用规则只查[AGENTS](AGENTS.md)，稳定事实／规格索引只查[README](README.md)，历史操作与回退只查[运维记录](docs/operations-log.md)。已结束的Agent编排与逐次发布流水不作为当前任务。

## 当前交付与运行版本

| 项目 | 已核结果 |
|---|---|
| 后端 | `fd5712351512e99e8d828f9263d3756eb6f0adac`已提交／自动push并上线，云端检出main，双服务实际同版本且active、微信connected；追加中断终态输出对账，默认／Alex总时限1000秒及partial摘要提交保持。后继纯文档提交不改变运行版本 |
| 前端 | `744ac30ff3194c29b06dd7bce552e8904749f5f4`已提交／自动push并上线，入口CJ6XWfgz／439静态及HTTP SHA通过；修复idle重连抢位与恢复阻塞实时消息，原内存／持久缓存分层、Context终态高亮和Working位置保持。Composer移动端网页闪动尚未复现关闭 |
| Android | 当前已交付0.1.8／1008，内置744ac30，Downloads/Hermes-Secretary-0.1.8-744ac30-arm64.apk；原证书／release／arm64／minSDK26、完整ZIP CRC、ZIP／ELF16KB、439资源同最终dist及交付副本SHA全部通过；网页已同步上线744ac30。真机安装／生命周期未验；用户报告旧0.1.7损坏原因仍未确定 |
| Noting／压缩 | 跨进程活动证明覆盖子任务、多Turn、Notebook提交、父压缩及Framework实际结算；独立压缩fence不提前报idle，不新增Main准入锁 |
| Context | 旧热runtime不得覆盖有效压缩边界；本次22:17尝试未提交、80–81%为原文真实占用，非刷新缺陷。22:47另一次旧版尝试22:56已成功，不能冒称新修复效果；当前不为此修改Context逻辑 |
| 数据保护 | 历史、Notebook、排期、配置、绑定及Dashboard发布前后对账通过；保留最近两套完整三库，旧6个备份文件已清理，运行库及同步ZIP保持 |
| 已有会话设置 | 先前noting off的历史回执保留；23:28已只读发现local_enabled=true，主会话未执行恢复开关，不再把历史false当当前事实。随后23:51自动Idle Noting运行并于00:07完成后续压缩；本轮未额外触发重复Noting。用户要求的单次调试RPC本地已完成，尚未发布／调用。Alex全局Idle延迟500秒／阈值96K保持 |

本轮第二次Idle触发符合机制：Main在18:20:06结束时输入114739，500秒后启动Noting；18:35:49正常提交后压缩，18:43:46完成26→1，随后Framework追加。18:59–19:01又有真实Main请求，因此当前有效Context不是仅摘要时的30970。详细时间线、失败尝试和证据仅见运维记录。

## 唯一任务看板

| 工作 | 状态 |
|---|---|
| 0.1.8重连阅读／实时流与APK | 744ac30已提交／push，APK完整校验交付；本次追加网页发布verified，未重启服务。Composer闪动完整App桌面／移动尺寸未复现，用户已明确为移动端网页版，继续定位，不宣称本轮全部问题关闭 |
| 冷刷新持久缓存／同页内存分层 | 已上线c29b457；合法Steer正文完整保留、隐藏字段不读解析、冷IDB候选不被同owner恢复代次废弃、侧栏候选有界。最终200相关项及独立审通过；Cnx真实断网冷刷、无reload恢复与同页暖返回0持久展示读取已验；旧条目须首次正常载入建立正文，不承诺导航或渲染零耗时 |
| 置顶会话Stop后空白／不可控 | 已恢复并发布fd57123；正式200正文、Socket complete=true／idle及隐藏IAB实际显示和输入可用。中断源／输出精确对账，原生文件49项及最后19项定向通过（重叠不相加），其余4关联文件89项通过，冻结10检查通过；原反例与首次测试预期错误保留 |
| Conversation切换首帧缓存／阅读位置 | 暖态成果随当前c29b457保持；436相关项及类型／构建通过，271c真实暖首帧／Thinking展开、D5抽取后暖首帧均通过。Pending owner等价抽取后Controller2550行（原基线2553），新sibling95行，147定向通过，独立接线审查通过；最终Working复审通过，439静态已verified |
| 前端活动Turn显示状态系统性抖动 | 始于559598b，随当前c29b457保持：同owner连续活动／Pending保留、断线禁用Stop、当前受理／NewChat桥接、Context实时但正式结束一次高亮。271c真实两Turn并行工具／首stored帧／6.3秒断线及D5等价接线／暖首帧证据承接，DOND新增Working实际位置已验；0生产模型测试 |
| 原生Compact超时／截断已有摘要保留 | 实现及主会话亲审完成：10文件187项、补日志后31项定向及冻结10检查通过；覆盖lean／legacy保尾、超时／length／窗口error部分摘要、无第二模型请求、晚线程不回退durable／Context／成功回执。1000秒默认／Alex配置已读回；main后端93d3b71已verified，网页沿用d644d4a，最新历史／Notebook／配置／绑定／Dashboard及439静态保护通过 |
| 本次Context未更新判断复核 | 已查正式API与真实提交边界：该次Compact未成功，续跑使用原文，80–81%与服务端一致；用户已确认可能误判，仅检查，不为此改Context逻辑 |
| 置顶Noting关闭范围复核 | 已确认会话参与开关挡住所有Noting，Idle子开关为Profile级；用户反对被说成两者联动要求，当前未再变更运行设置，纠正方案待明确 |
| 本次恢复／Thinking／界面修复 | 联合上线收据verified；REST最新200、正式Socket恢复complete=true、入口无两条横幅、439资源与目标包一致；用户当前Main运行亦能正常恢复。置顶local_enabled=false／next_idle absent读回保持。未代刷新用户页，不把接口验证冒称用户浏览器使用已验 |
| 后端实现、集成亲审、定向验证 | 已完成；正式接线与跨进程、owner、过期、异常和结算边界已覆盖 |
| 上一轮前后端联合部署与线上核验 | 原版本证据按历史时点保留；本次回退已结束，当前版本以上线表为准 |
| 0.1.7重新打包 | c29b457新APK已构建／核签，439资源与当前网页一致，原包保留；本次未安装到真机，证据见android-017-c29b457-20261026 |
| 核心文档整理 | 已收敛为稳定入口／通用规则／当前看板；历史原文和报告保留，详见运维记录 |

两个子Agent整包均已亲审；主会话负责整合、实际隐藏页、最终构建与发布。复用已有发布器，活动预检拒绝时不切换，等待自然空闲后完成联合发布，保最新数据库；未触发生产模型测试。当前范围收口，保护presentation dirty；云端只发布main，规则见AGENTS。

## 验证摘要与边界

Thinking问题在原0.1.7同样存在，本次才修复：历史末条延迟reasoning不能作为新Thinking的owner，统一以source／native消息UID判断，并保真正延迟facet补齐。Controller反例先败（Thinking索引2、最新用户4）后过；普通连续Turn、carry及已提交新user对照、own／foreign／unbound owner共85项定向及typecheck通过。首次较宽测试另有5项既有失败，保留原日志，不称全仓绿。追加横幅／CSS后及Thinking整合后，136项恢复／阅读回归与最终build通过；隐藏IAB实际右侧无可见条，滚动仍有效。证据`.hermes-dev/turn-completion-recovery-20261025/thinking-*.txt`、`frontend-final-*.log`和`ui/no-scrollbar*.png`；原85项与136项有交叉，不加总。

本次联合发布云受限`release-20261024/20261025-turn-recovery-2b6d5ec/`，本地ignored同证据目录`release/`。正式旧会话REST／Socket及会话开关读回通过，生产模型测试0；439静态、历史／Notebook／排期／配置／绑定／Dashboard保护通过，备份按最近两套收尾。活动窗口拒绝及本地发布器默认cwd误用均保留，不冒充首次全成功；具体见运维记录。原冻结修复待确认和回退材料均保留历史时点，当前状态以上线表为准。

本次修复证据统一ignored`.hermes-dev/turn-completion-recovery-20261025/summary.json`，子Agent原生链路证据在`.hermes-dev/heartbeat-recovery-20261025/`。实际反例为后端idle／完整历史但恢复runtime_unavailable；漏查完成回执来源、带Steer后缀误依赖单用户complete，以及无正文／UID的队列交接混入display快照均已修。七文件最终173项通过；原pending容量夹具首次5秒等待超时，runner重试及独立定向复测通过，不称首次全绿。主会话等价测试重构后31项无重试通过／25.2秒；冻结10检查最终0 blocking／0 advisory，初次仅测试HX011已修。前端118项及typecheck通过，产品未改；439本地dist同f3eb130原manifest。隐藏IAB真实SSE模型替身完成5Turn，原故障复现、修复后自然carry、同document后端重启／断线／503自动重试、Thinking／草稿保留及外部追加收敛均已验；5user／6assistant含唯一外部追加、无重发。生产修复期操作0、真实供应商请求0；未跑全仓、未做APK真机，不将隔离验收冒称线上已修。

紧急回退复用原verified发布包与正式解包／renameat2工具，439文件与原manifest逐SHA一致；正式HTTP入口及JS／CSS资源SHA通过，Web PID前后3742575、无重启／无数据库写入／无模型测试请求。未代操作用户页面，不冒称刷新后实际使用已验；轻量收据及旧静态恢复点见运维记录。

Noting相关8文件102项、存储13项、Framework边界61项通过；新增真实恢复入口延后结算反例已通过。Context专项最终17项及冷读26项通过，另有原生联合链路26项及此前有效证据；范围重叠不加总。冻结10检查通过，health 0 blocking／0 advisory；未跑全仓，生产模型测试请求0。

真实浏览器查看仅为用户本次明确授权的只读核对，未导航、刷新、点击或切焦点；默认显示保护保持。历史全量失败与旧门禁结论仍按各自被测版本保留，不能由本轮定向通过改写。

## 保留事项（不自动立项）

| 事项 | 当前边界 |
|---|---|
| 跨进程busy Instant Reminder | desktop来源且Gateway持Main租约时，Instant可能另起Web运行而非转Deferred；10/24已确认，本轮未修。Deferred已验正常，未发现原文误外发 |
| 微信主动出站`prepare failed` | 既有失败与脚本exit 0误判风险仍独立保留；本轮connected不等于主动出站恢复，未试发 |
| 微信早期正文投递时序 | 18:18长正文已定位为刚生成即发送且拆成两段；更早正文是否积压尚缺逐消息发送身份回执，不将现有记录推断成已修 |
| Conversation时间／分页 | 起始时间漂移、旧第10项pagination元数据反馈未获关闭；生产47条历史副本时间错误尚未恢复、未获恢复写入授权，不扩大修复 |
| 旧失败Noting内容重建 | 空工作态历史反例在原HEAD2122223复现；本轮只验证恢复入口生命周期，不冒称其内容重建已修 |

已关闭的拍照参数、首触Send、会话列表、补水流量及旧Kimi专项不重新挂账；Reminder语气、编排分流与触达白名单归模型行为调优，不变成开发任务。SOUL／workspace AGENTS不因文档整理改写。

## 证据入口

- 本轮代码与发布：[运维记录](docs/operations-log.md)最新条目；原工作区ignored `.hermes-dev/noting-crossprocess-20261025/`。
- APK与前端证据：ignored `.hermes-dev/web-recovery-20261024/release-017/`及`performance/017-*`。
- 历史冻结／验收入口：[README索引](README.md#重要文档索引)；旧CLAUDE完整时点可由`git show 7bc5729:CLAUDE.md`恢复，不修改原报告。
