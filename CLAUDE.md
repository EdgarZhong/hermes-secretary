# Hermes Secretary 当前状态

## 自主口径收敛 · 待用户追认

暂无。

## 当前阶段

**2026-10-26：用户正在迁移服务器，禁止自主上线、部署静态、更新／重启生产服务或为此操作迁移服务器。本轮仅本地代码、测试、Git同步及APK构建。用户明确本轮由主会话处理全部工作，已停止子Agent，不再委派。**

已按用户指定顺序完成统一恢复修复与b33e428阶段APK核验，再完成Noting按需优化。悬浮球仅由当前Profile全局开关决定，与连接状态解耦；未展开排期不取详情，概览用轻量计数，同owner突发失效合并为一个在途请求加一次最新读取，未生效的旧读不消费完成通知。不新增持久缓存。后端查询排除结束严格超过24小时的排期，仅返回hidden_count；删除不返回／不计数，暂停保留，原生模型工具完整列表不变。用户新增胶囊压高已落实：Usage／Context从32降至26px，字体／胶囊圆角不变，底栏36降至30px。最终0.1.8／20c9267已构建并完成交付副本完整性核验，全部尚未部署。用户明确追加修复Compaction message末尾的Conversation start：只取该Conversation的History Foreground第一条timestamp，禁止用内存最早时间或本次压缩区间代替，禁止另猜起点。已删除_summarize_window的内存min(timestamp)，Compaction footer直接读取get_history_foreground(current_session)[0].timestamp；真实数据库反例改前3失败、改后3通过，7文件201项相关测试与10项冻结检查通过。未部署，不改写生产历史／旧摘要。

统一恢复状态本地实现完成：PageRecovery复用原有owner、轮次、读取结果与提交点，派生当前可见依赖的availability；Composer单行提示、主按钮恢复资格及Android恢复／导航回执同源。只有Connecting to Hermes…、Restoring {对象}…、Retrying {对象}…三模板，固定20px单行、随Composer宽度、省略号、多个真实等待对象3秒轮换。移除聊天页其它自动恢复横幅／Toast；草稿保留可编辑，真实写操作及未确认回执反馈保留。已恢复同owner的普通后台刷新不重新锁定操作；隐藏预取不进入完整恢复资格。REST读取增加30秒可取消超时，失败交给既有owner自动重试。

已定位的静默恢复缺陷：Socket connected、Profiles读取成功与页面完整恢复原来各自决定提示，Secretary又错误等待历史／流恢复，导致提示消失但球未出现。现Secretary独立按当前stored owner读取，读失败与secretary.changed刷新均沿恢复owner重试。另一个后端根因：原生压缩后的完成回执来源仍visible，但active=0；恢复层误拒并返回runtime_unavailable。只放行exact UID／row／role且visible并active或compacted的已完成来源，rewind／删除／不匹配仍拒绝。此前只读取证与本地原生链路反例均可复现，不归因于网络。

通用规则见[AGENTS](AGENTS.md)，稳定入口见[README](README.md)，逐次部署／故障历史见[运维记录](docs/operations-log.md)。历史CLAUDE可由f812c1d等已提交时点读取，不把旧阶段的“当前／正在”继续作为任务编排。

## 当前交付与运行版本

| 项目 | 已核结果 |
|---|---|
| 后端线上最后核验版本 | fd5712351512e99e8d828f9263d3756eb6f0adac；当前压缩回执修复仅本地，迁移禁令之后未再访问服务器 |
| 前端线上最后核验版本 | 388839cda07d3a428ccfc924de85a504ee25cb77，439静态与HTTP入口index-Dhu8Zuse.js／index-D-MUF2u6.css验证通过；本轮统一状态尚未部署 |
| 已交付APK | 最新0.1.8／1008：`/Users/edgar/Downloads/Hermes-Secretary-0.1.8-20c9267-arm64.apk`，32,106,741字节，SHA256 `73d6ce39dd5e8fa7f05557f7b77db6424471bafba4850289bd6aa279dcab622a`；原证书、ZIP CRC／v2签名／16KB对齐、439内置资源及交付副本一致性通过。未真机安装；旧388839c文件保留，但非本轮最新包 |
| 运行设置 | 历史noting off不代表当前值；最后已核local_enabled=true，默认／Alex压缩总时限1000秒及Idle500秒／96K保持。本轮不改运行配置或调用生产模型 |
| 保留他人工作 | presentation报告、手动Noting调试入口／协议生成、07等原dirty保持，不纳入本轮恢复补丁提交 |

## 唯一任务看板

| 工作 | 状态与完成边界 |
|---|---|
| Composer统一恢复契约 | 本地实现与正式App链路已验，已提交／自动push前端b33e428，等价抽取217项及复杂度检查通过；未部署 |
| 压缩后完成回执恢复误拒 | 本地正式入口及原生链路105项通过；补充中断／失败压缩路径7项通过，10项冻结检查通过；已提交／自动push后端98a707e，未部署 |
| 0.1.8重新构建 | 20c9267最终APK已构建并核验，唯一新文件名与SHA／verification sidecar已生成；无真机不声称安装验证 |
| Noting弱网按需读取／显示解耦 | 已提交／自动push前端20c9267、后端4b04546；本地实现及主会话隐藏IAB已验：未展开0次、展开1次、关闭／重连无额外列表读；底部隐藏摘要、全局开关控制球、断线球保留；不新增持久缓存 |
| Compaction末尾Conversation start | 已按用户再次明确的Foreground第一条修复，真实DB连续三轮原地压缩／Session轮转／冷恢复稳定；非单调时间与foreign owner反例覆盖。7文件201项及10项冻结检查通过，待本地提交同步，未部署 |
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
