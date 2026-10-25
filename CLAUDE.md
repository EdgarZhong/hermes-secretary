# Hermes Secretary 当前状态

## 自主口径收敛 · 待用户追认

暂无。

## 当前阶段

2026-10-25：跨进程Noting状态／通知、压缩后Context与前端0.1.7联合发布已完成；随后按用户要求规整核心文档。后端在现有main签出`/Users/edgar/code/hermes-secretary-web-release`实施，前端在`../hermes-secretary-web`的main；本轮不开新worktree、不启自主套件。主仓原有presentation报告dirty保留，未纳入提交。

通用规则只查[AGENTS](AGENTS.md)，稳定事实／规格索引只查[README](README.md)，历史操作与回退只查[运维记录](docs/operations-log.md)。已结束的Agent编排与逐次发布流水不作为当前任务。

## 当前交付与运行版本

| 项目 | 已核结果 |
|---|---|
| 后端 | 本轮代码已提交并推送main；云端检出main，Web／Gateway实际运行`7bc57298be9fa4ee24de97f70d13c5b9c4a7de4c`，双服务active、微信connected |
| 前端 | `f3eb13024f3bbfd501db1e7f7391aaf7fdd3e304`，439静态逐SHA核验；正文宽度、恢复重试／缓存／离线体验修复已发布 |
| Android | 原证书0.1.7／1007已重新封包，439内置网页与联合发布一致；新包与SHA见运维记录，实际APK生命周期沿用户C17豁免未实测 |
| Noting／压缩 | 跨进程活动证明覆盖子任务、多Turn、Notebook提交、父压缩及Framework实际结算；独立压缩fence不提前报idle，不新增Main准入锁 |
| Context | 旧热runtime不能覆盖新压缩读数，冷热读取共用有效边界并计入Framework增量；生产正式恢复后两API及重复读取同为55,716／262,144（21%），真实Chrome自动恢复一致、未刷新 |
| 数据保护 | 历史、Notebook、排期、配置、绑定及Dashboard发布前后对账通过；保留最近两套完整三库，旧6个备份文件已清理，运行库及同步ZIP保持 |
| 已有会话设置 | Alex Idle延迟500秒／阈值96K（98,304）；旧Pi041会话全部Scheduler已暂停，Heartbeat原已清除，不自动恢复 |

本轮第二次Idle触发符合机制：Main在18:20:06结束时输入114739，500秒后启动Noting；18:35:49正常提交后压缩，18:43:46完成26→1，随后Framework追加。18:59–19:01又有真实Main请求，因此当前有效Context不是仅摘要时的30970。详细时间线、失败尝试和证据仅见运维记录。

## 唯一任务看板

| 工作 | 状态 |
|---|---|
| 后端实现、集成亲审、定向验证 | 已完成；正式接线与跨进程、owner、过期、异常和结算边界已覆盖 |
| 前后端联合部署与线上核验 | 已完成；收据verified，REST／Socket恢复、Context两路一致、真实页面回落均已核 |
| 0.1.7重新打包及生产一致性 | 已完成；原包保留，新包已复核签名／版本／439资源 |
| 核心文档整理 | 已收敛为稳定入口／通用规则／当前看板；历史原文和报告保留，详见运维记录 |

当前没有待启动的实现Agent或新增自主目标。云端后续只发布main；分支完成后及时合回main，规则见AGENTS。

## 验证摘要与边界

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
