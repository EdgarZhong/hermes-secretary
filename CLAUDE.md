# Hermes Secretary 当前状态

## 自主口径收敛 · 待用户追认

暂无。

## 当前阶段

2026-10-25：正常Turn完成后恢复误拒及Thinking跨Turn错位均已修复、亲审、验证并上线；按用户追加要求移除两条顶部同步／重试横幅，隐藏聊天区右侧滚动条而保留滚动能力。生产后端main为`2b6d5ec`，网页为`d644d4a`，联合发布及只读核验通过。Alex置顶会话已原生noting off，空闲整理／相连压缩暂停，不自动恢复；其它会话／Profile及Scheduler／Heartbeat保持。后端在现有main签出`/Users/edgar/code/hermes-secretary-web-release`，前端源码在`../hermes-secretary-web`的main；不开新worktree、不启自主套件。主仓原有presentation报告dirty保留。

通用规则只查[AGENTS](AGENTS.md)，稳定事实／规格索引只查[README](README.md)，历史操作与回退只查[运维记录](docs/operations-log.md)。已结束的Agent编排与逐次发布流水不作为当前任务。

## 当前交付与运行版本

| 项目 | 已核结果 |
|---|---|
| 后端 | `2b6d5ec655135caaca141f68b5853e80ecb84283`已提交／自动push，云端检出main，双服务实际同版本且active、微信connected；后继纯文档提交不改变运行版本 |
| 前端 | `d644d4a08854b6a7cc5fb1b77f99fb9ef02d525e`已提交／自动push并上线，439静态逐SHA及HTTP入口资源核验通过；0.1.4回退结束。顶部同步横幅移除，聊天滚动条隐藏，Thinking按正式消息身份归属；浏览器需刷新一次载入 |
| Android | 已交付0.1.7／1007未改，仍内置原f3eb130；本次仅Web修复／发布，未重打APK，不能宣称内置前端与当前网页一致；实际生命周期未验 |
| Noting／压缩 | 跨进程活动证明覆盖子任务、多Turn、Notebook提交、父压缩及Framework实际结算；独立压缩fence不提前报idle，不新增Main准入锁 |
| Context | 旧热runtime不能覆盖新压缩读数，冷热读取共用有效边界并计入Framework增量；生产正式恢复后两API及重复读取同为55,716／262,144（21%），真实Chrome自动恢复一致、未刷新 |
| 数据保护 | 历史、Notebook、排期、配置、绑定及Dashboard发布前后对账通过；保留最近两套完整三库，旧6个备份文件已清理，运行库及同步ZIP保持 |
| 已有会话设置 | 用户本次要求暂停Alex置顶会话空闲整理／压缩：原生noting off已完成，local_enabled=false／next_idle absent／task idle；只改目标Conversation参与开关，不自动恢复。Alex全局Idle延迟500秒／阈值96K保持；旧Pi041排期暂停及Heartbeat清除保持 |

本轮第二次Idle触发符合机制：Main在18:20:06结束时输入114739，500秒后启动Noting；18:35:49正常提交后压缩，18:43:46完成26→1，随后Framework追加。18:59–19:01又有真实Main请求，因此当前有效Context不是仅摘要时的30970。详细时间线、失败尝试和证据仅见运维记录。

## 唯一任务看板

| 工作 | 状态 |
|---|---|
| 本次恢复／Thinking／界面修复 | 联合上线收据verified；REST最新200、正式Socket恢复complete=true、入口无两条横幅、439资源与目标包一致；用户当前Main运行亦能正常恢复。置顶local_enabled=false／next_idle absent读回保持。未代刷新用户页，不把接口验证冒称用户浏览器使用已验 |
| 后端实现、集成亲审、定向验证 | 已完成；正式接线与跨进程、owner、过期、异常和结算边界已覆盖 |
| 上一轮前后端联合部署与线上核验 | 原版本证据按历史时点保留；本次回退已结束，当前版本以上线表为准 |
| 原0.1.7重新打包 | 原包及签名／439资源核验保留；本次未重打APK，与当前回退网页不同 |
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
