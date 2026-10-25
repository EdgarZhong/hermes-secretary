# Hermes Secretary 当前状态

## 自主口径收敛 · 待用户追认

暂无。

## 当前阶段

2026-10-25：正常Web Turn完成后的恢复误拒已在本地修复、亲审及验收。部署前已按要求停下汇报，**用户现已明确确认上线，并要求暂时关闭Alex置顶会话的空闲自动压缩和整理笔记**。正在通过原生会话参与开关关闭该目标后台Noting及相连Idle压缩，并准备main联合发布；其它会话／Profile及Scheduler／Heartbeat保持。当前线上仍为回退网页f3a03ce／后端7bc57298，实际切换后更新版本。后端在现有main签出`/Users/edgar/code/hermes-secretary-web-release`，前端源码仍在`../hermes-secretary-web`的main；不开新worktree、不启自主套件。主仓原有presentation报告dirty保留。

通用规则只查[AGENTS](AGENTS.md)，稳定事实／规格索引只查[README](README.md)，历史操作与回退只查[运维记录](docs/operations-log.md)。已结束的Agent编排与逐次发布流水不作为当前任务。

## 当前交付与运行版本

| 项目 | 已核结果 |
|---|---|
| 后端 | 本轮代码已提交并推送main；云端检出main，Web／Gateway实际运行`7bc57298be9fa4ee24de97f70d13c5b9c4a7de4c`，双服务active、微信connected |
| 前端 | 已紧急回退到`f3a03ce32c0dd1e96719da210716caa2c1c7b8d4`（0.1.4）；439静态逐SHA及HTTP入口资源核验通过，无服务重启。浏览器需刷新一次载入；源码main仍为f3eb130，未经新授权不得重新覆盖回退版 |
| Android | 已交付0.1.7／1007未改；内置f3eb130网页与本次回退后的生产网页已不同，不能再宣称二者一致。本次用户要求正常Web立即可用，未重打APK；实际生命周期未验 |
| Noting／压缩 | 跨进程活动证明覆盖子任务、多Turn、Notebook提交、父压缩及Framework实际结算；独立压缩fence不提前报idle，不新增Main准入锁 |
| Context | 旧热runtime不能覆盖新压缩读数，冷热读取共用有效边界并计入Framework增量；生产正式恢复后两API及重复读取同为55,716／262,144（21%），真实Chrome自动恢复一致、未刷新 |
| 数据保护 | 历史、Notebook、排期、配置、绑定及Dashboard发布前后对账通过；保留最近两套完整三库，旧6个备份文件已清理，运行库及同步ZIP保持 |
| 已有会话设置 | 用户本次要求暂停Alex置顶会话空闲整理／压缩：原生noting off已完成，local_enabled=false／next_idle absent／task idle；只改目标Conversation参与开关，不自动恢复。Alex全局Idle延迟500秒／阈值96K保持；旧Pi041排期暂停及Heartbeat清除保持 |

本轮第二次Idle触发符合机制：Main在18:20:06结束时输入114739，500秒后启动Noting；18:35:49正常提交后压缩，18:43:46完成26→1，随后Framework追加。18:59–19:01又有真实Main请求，因此当前有效Context不是仅摘要时的30970。详细时间线、失败尝试和证据仅见运维记录。

## 唯一任务看板

| 工作 | 状态 |
|---|---|
| 正常Turn完成后恢复失败／紧急回退 | 已验后端修复获用户上线确认；相关173项／最终专项31项、前端118项及冻结10检查通过。用户已确认两条同步／重试横幅都移除、后台自动恢复保留，并明确聊天区不显示右侧滚动条，滚动能力保留。前端最小修改及定向验证后联合发布，无需再次等待授权；另核最新版Thinking是否会错挂到上一条消息，按表现检查、不限定Steer机制 |
| 后端实现、集成亲审、定向验证 | 已完成；正式接线与跨进程、owner、过期、异常和结算边界已覆盖 |
| 上一轮前后端联合部署与线上核验 | 原版本证据保留；本次紧急回退后网页为f3a03ce，修复版尚未发布 |
| 原0.1.7重新打包 | 原包及签名／439资源核验保留；本次未重打APK，与当前回退网页不同 |
| 核心文档整理 | 已收敛为稳定入口／通用规则／当前看板；历史原文和报告保留，详见运维记录 |

后端子Agent整包已交回，主会话已亲审并等价整理专项测试条件表、完成最终代码检查及实际隐藏页面验收。用户已确认发布，按已验文件SHA提交／自动push并复用既有发布器，保护presentation dirty；不在生产触发模型测试、不打断活动Turn。云端只发布main，规则见AGENTS。

## 验证摘要与边界

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
