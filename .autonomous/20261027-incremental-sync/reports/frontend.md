# F1 前端缓存、增量恢复及压缩故障修复交接

状态：实施完成，待主会话 review／集成及全轮独立门禁。本子 Agent 未提交、未部署，未调用生产模型或真实微信发送，也未操作任何浏览器／桌面页面。

## 1. 任务对应条款

- 冻结依据：本轮 snapshot-index、baseline、plan“主会话冻结的工程接口”1–8；06 顶部 C0–C3、D01–D18、S01–S18、P01–P10；保留 §0.4／0.5／1.3／1.4／1.4.1／1.6 的非冲突语义。
- 本包实现 D01–D05、D09–D11、D14–D16 所涉机制，保留其余数据归属和按需入口；覆盖缓存冷暖启动、有限切点、详情展开、旧 owner／旧代次、失败重试与容量边界。未修改 PageRecovery.availability 或 composerActionPolicy。
- 主会话追加 U13：同 owner 当前原生压缩状态穿过历史保留画面；压缩状态读取与慢 Context 解耦；旧 operation 响应不能覆盖新 operation，终态同页刷新 Chat／Usage／Context。
- 主会话追加 U14：仅 session.compress 默认不设客户端固定完成期限；普通 RPC 与显式期限保留；断线／显式期限产生的 IndeterminateError 不误作失败 Toast、不重发、不清草稿；真实 RpcError 保留。
- U15 Toast 外观修复不在本子包，未改视觉样式或 Android 文件。

## 2. 实际变更

- 新增 history-sync sibling，集中校验 cursor／base_cursor、selector、权威 order、每行 revision、消息身份和窗口范围。增量按完整 order 重建，明确移除删除／rewind 行；同 UID 换物理代表行不借旧详情。selector 使用固定字段生成的规范键，兼容 Python／JS 对象字段顺序差异。
- HistoryWindows 复用原有窗口 owner 和本轮 verified 标记。完整详情只在同身份且 revision 相符时复用，跨窗口重叠按已确认 revision 比较；未核窗口不标成本轮已核。
- DisplayCache schema 升为 2，在同一个 Conversation IDB 条目内原子存消息、窗口 receipt／cursor／revision、完整已取详情与已核前缀。旧 schema 展示数据不能提出 delta。移除单窗口 2MiB／全局 16MiB 的数据丢弃截断；仍保最多 10 Conversation、7 天 TTL，quota 时逐旧 Conversation 淘汰并重试，失败保内存且不阻塞在线读取。
- 最近 500 预算按真实消息身份统一计算，覆盖窗口、最新 Thinking 候选、历史详情提示及未落库前缀。早期阅读页继续保在页面内存；超范围窗口不重新持久化。不为填满 500 主动读取正文。
- 完整 Thinking／工具参数／结果沿消息保存；未展开旧详情仍按原最多 12 行懒读。详情请求使用 history_sync opt-in，迟到版本不符不会错误标记完整。已不属于最新 Turn、位于当前窗口之外的已取 Thinking 作为同消息详情提示保留，只有后续窗口证明相同 revision 才能复用；提示本身不授予覆盖或展示资格。
- 最新 Thinking bundle 与同一个窗口 cursor 一起合并，支持普通 reasoning 字段及原生 interrupted/error terminal wrapper；未展开工具详情不被主动补齐。活动未落库 Thinking 只保存完整原生 snapshot 确认的、带 UID／Turn／Conversation／epoch／切点的类型化前缀；后到片段只在内存，缓存不包含原始事件或运行权限。
- 已有可核缓存可直接带 receipt＋cursor 到 activate，不先 REST 重传 200 正文；异常／过期 cursor 由后端必要快照回退。IDB 阻塞超过 100ms 则本轮继续在线读取，迟到缓存仍须经 owner／代次校验。
- 元数据／binding／roster 按 owner＋恢复轮次共享，不随 viewport 重建。Usage／Context／Pending 仅等共享 binding，并行于慢历史。共享 binding 的元数据先进入当前业务 owner，保留原恢复门禁，防止早到 Pending 因 binding 尚未展示而被丢弃。安装正式 cut 推进现有 activityVersions，早发晚返 Pending 须重新读取，不能降级当前活动状态。
- Usage fallback 复用本轮已确认 summary，旧调用默认行为保留；修复并行 Context 下旧 binding identity 再次覆盖较新观察的问题。隐藏菜单不请求；earlierPages 不再无条件后台重传，当前实际可见 anchor 仍核验。
- 压缩读取统一经过 CompactionViews，PageRecovery 不再另有裸 compaction_state 读取。已确认状态立即穿过 retained 画面；原状态读取不等待 Context／历史补读，完成补读有独立在途标记并沿原 700ms 观察 owner 重试，不阻挡新 operation 状态。手动开始使旧读取 revision 失效，终态／取消／失败沿原完整读取链收敛。
- Gateway 的 compress pending timer 改为可选；连接活跃时大于 11 分钟仍保留同一请求并接受真实回执。未知回执返回 indeterminate 给命令保留路径，并继续既有原生观察；只观察到别的 operation 终态不会清本次草稿或发本次成功确认。普通 30 秒 RPC、显式期限及确定失败不变。
- Controller 仅薄接线，最终仍 2550 行；未修改 Android、核心三文档、规格或 plan，原 .DS_Store 保留未纳入。

## 3. 正式路径与版本

前端工作区 `/Users/edgar/code/hermes-secretary-web`，分支 `codex/incremental-sync-20261027`；冻结前端 `c39086c1879cd46370bdc8f4e3d98a3c290aecc3`，工作区现有 HEAD `6ba37b4453a0adb69eaa9e5117c5b2351ab381b2`（本子包为未提交 diff）。后端参考工作区 `/Users/edgar/code/hermes-secretary-incremental-sync`，原冻结 `cf5742c70b26e0dc954eabcb4b07c232c5231013`。

正式入口：Controller.startRecovery → ControllerPageRecovery／HistoryWindows → REST readRecoveryHistory 或带 sync_version 的 session.activate → 原 envelope／snapshot／有序事件对账 → 原表现层提交 → DisplayCache 原子写。用户展开仍走 Controller.hydrateDetails → HistoryDetails → 原精确 row 详情入口。压缩仍走 command-actions → Controller.compact → runManualCompaction／CompactionViews → 原 Gateway RPC／恢复资源。

22 个变更 TS 文件的精确 SHA256、HEAD、冻结度量输出都在证据目录 source-sha256.json／ts-measures.json／baseline-measures.json／health-result.json，便于主会话与门禁复用。未改生成协议。

## 4. 验证结果与证据

证据根目录：`/Users/edgar/code/hermes-secretary-web/.archive/incremental-sync-20261027/frontend-incremental/`。

- 最终相关集合 16 文件 **454 项通过**，7.16 秒：final-current-scope.log。覆盖正式 Controller、真实 fake-indexeddb 事务、实际 App／Composer／阅读交接、原生输出 snapshot、受控 REST／RPC、Usage、Pending、Context／压缩、移动恢复和菜单。最后仅缓存白名单收敛再定向 3 文件 **59 项通过**：cache-whitelist-final.log；并重跑 typecheck 与构建。
- typecheck-final.log：通过。build-final.log：Vite 正式构建通过，5.83 秒；仅既有大 chunk 提示，未改其阈值。
- 冻结 ts_units.mjs 相对 c39086c 的 22 个变更 TS 文件度量无新增／增长超标：health-result.json。Controller 文件仍 2550 行；git diff --check 通过。未改质量规则、豁免或等级。
- 新正式 Controller 场景包含：无缓存／冷缓存／暖恢复、无变化、追加、权威删除／rewind、游标过期快照、600 条当前阅读数据与最近 500 复用边界、旧详情 0 预取、首次展开后冷开复用、详情 revision 飞行中变化、最新 Thinking、只存完整活动 snapshot 前缀、早 Pending 与切点竞态、慢历史／慢 Context 时压缩立即可见、旧终态不覆盖新 operation。
- 压缩回执场景：真实 Gateway＋fakeSocket 连续等待 **720000ms** 后仍只发一次 compress 并接收成功；普通 30000ms 与显式 100ms deadline 保留；断连 pending 清理／不重发；正式 Controller／command 的未知结果保命令、无失败 Toast、重连后原生终态刷新；真实 RpcError 仍反馈。见 compress-unknown-fixed.log 之前保留了旧断言失败；最终结果以 final-current-scope.log 为准。
- 真实基线负对照：从 c39086c git archive 创建 ignored 隔离源码副本，运行相同正式 Controller 场景，4 项均在目标断言失败：重复全量历史（2 次而非 1 次）、最新 Thinking 缺失、慢恢复遮住 active compaction、Pending 仍等待慢历史。见 negative-control.log；不是源码字符串断言。基线旧规则未修改，隔离 runner 仅用于让 archive 内测试可被 Vitest 发现。
- 受控数据量：200 条长消息完整 REST 响应 **2,631,101 bytes**；无变化恢复 envelope **16,857 bytes／0 正文行**；少量追加 **16,946 bytes／1 正文行**。冷缓存＋追加＋rewind＋失效游标 5 次对账期间 REST history 总计仍 1 次；失效游标由 RPC 必要快照回 80 行。完整原始值在 transport.json／transport-final.log。版本 hash 用 SHA256，未把正文当版本串。
- 保留了中间失败和修复日志；本轮没有通过改源码断言、改门禁或泛化忽略错误来制造通过。

## 5. 缺口与边界

- 本包没有启动隐藏 IAB 或实际 Android WebView；真实 App 证据是 React／jsdom 加正式 Controller，不能称真实浏览器画面／原生生命周期验收。Android 包、通知／附件返回及 U15 由对应实现／主会话集成验收。
- 新 REST／RPC 的前端完整链路使用受控服务依赖；已核对 B1 当前 Python wire，包括 matched、字段名、selector 及 latest Thinking wrapper，但没有声称真实 Python HTTP／WS 到此前端的最终联调通过。该项留给 I1 与全轮两个独立门禁。
- 传输字节为受控真实 Response／envelope 序列化大小，未含压缩、TLS 或移动网络耗时；不能替代正式后端及真实弱网的 I1 指标。
- 非本包白名单内容、原有 .DS_Store 和 Android／Toast 工作均未代为提交。没有生产部署、真实微信或生产模型验证。

## 6. 接口影响

- API 仅新增可选 HistorySync 类型、sync_version／cursor 请求字段与详情 opt-in，沿原 messages／activate／snapshot／seq 使用；无独立事件同步系统。
- readRecoveryHistory 的 cursor 参数、UsageViews／Controller.readUsageFacts 的 summary 参数均可选且默认保原调用。
- DisplayCache schema 2 隔离旧记录；缓存从不恢复 binding、pending、approval、active 或可执行权限。旧后端依原能力失败路径处理，不伪装完成新一致恢复。
- session.compress 默认无固定客户端完成 deadline 是 U14 的限定行为；普通方法及显式 timeout 不变。未知返回 status=indeterminate 只用于本地人工命令 retain，不更改服务端 wire。

## 7. 建议后续动作

主会话亲审本包实际 diff、B1 的 matched／delta 与 latest Thinking 字段接线，特别复核同一 IDB 条目预算、共享 binding 的时序和 CompactionViews 生命周期；再整合 Android／U15，进行真实前后端 I1 和独立 Verification → Validation。使用 source-sha256.json 核对有效证据版本；若集成仅改接线或修缺陷，定向补测相应路径。当前没有需要产品决定的阻塞，本包未自行提交。

## 8. 主会话亲审后的压缩生命周期收尾（2026-10-27）

本节是后续增量交回；保留以上原时点报告与全部旧证据，当前这 5 个文件以 `lifecycle-followup/source-sha256.json` 为准。未修改 CSS、Android、主文档、其它功能或权限判定，未提交／部署、未使用浏览器或派生 Agent。

### 对应要求与反例

依据主会话本次明确交接、冻结 06 C/S/P 与 U13／U14，先在正式 Controller 行为测试确认缺陷：

- `lifecycle-followup/before.log`：终态 Context 首次读取失败后不重试；unknown 后可靠 idle 没有触发完整数据补读；unknown 后首次即其它 operation finished 仍每 700ms 重读。3 个目标反例均失败，另 3 个 operation／epoch／Profile 退休反例原已通过，保留原保护。
- `lifecycle-followup/recheck-before.log`：同一 native operation 在 unknown 请求之前已经完成过对账，unknown 后再读仍错误复用旧 Context（46189，预期 60000）。这是观察订阅与请求结果分开后必须补齐的新观察轮次，先复现再修复。

### 实际机制与正式接线

1. `ContextAfterCompaction.read` 显式返回 complete／incomplete／superseded。失败／无有效 native 字段是未完成；owner 或请求已退休是 superseded；只有当前有效读取成功后才允许标 Context 生命周期完成。已有较新 native Context 观察继续保护字段，不被晚结果覆盖。
2. `CompactionViews` 分别维护已成功的 Context 生命周期与原 complete 回调生命周期；同生命周期每种读最多一个在途请求。Context 失败不阻塞 native active 状态或历史补读，沿原单一 700ms 观察重新核对状态并定向重读 Context；历史已经成功则不反复重读历史。两项结束后立即停止该轮观察。新 operation 可立即接管状态和自己的 Context，旧请求晚到没有提交资格。
3. `readNativeCompaction` 增可选 contextCurrent predicate；Controller 用现有 contextVersion 薄接线，失效 Context owner 不能以一次 fulfilled 冒充成功。Controller 当前 2549 行，未增长超标指标。
4. unknown 专属 watch 只是一项观察订阅，不是本次 compress 结果证明。当前 owner 新取得的可靠 idle／finished／cancelled 会释放该订阅；active 则继续观察至终态。订阅释放后，必要的当前状态／历史／Context 补读仍可独立完成，失败继续原观察重试；全部满足后停止，不永久轮询。
5. unknown 到来建立一次新的内部对账轮次，原生 operation_id／active／state 保持不变，避免复用请求之前已完成的数据补读，或接纳此前在途读的过时完成标记。其它 operation 的终态只能更新当前真实状态，始终不清 unknown 草稿、不发本次成功 Toast、不重发 compress。
6. owner／epoch／选择退休时清理未知订阅与原计时器；迟到 Context／complete 回调不能覆盖新 owner／operation。正常回执、普通 RPC 期限、显式期限、真实 RpcError 和原 UI／操作资格保持。

正式路径仍为 command-actions → Controller.compact／readCompaction → readNativeCompaction → CompactionViews → ContextAfterCompaction／原 history＋usage 补读，无第二恢复状态机或新增定时器。

### 验证与版本证据

证据目录：`/Users/edgar/code/hermes-secretary-web/.archive/incremental-sync-20261027/frontend-incremental/lifecycle-followup/`。

- 当前定向相关 8 文件 **316 项通过**：current-related-final.log；包含真实 Gateway fakeSocket、正式 Controller／人工命令、实际 App 恢复呈现、Usage 与冷启动交接。
- 压缩专项全部 **61 项通过**：after-final.log。新增覆盖失败一次再成功且历史只补读一次、慢 Context 单在途、新 operation 不被旧结果覆盖、失败后 operation／epoch／Profile 退休、unknown 首次 idle／其它 operation finished、active 后完成、断连换 epoch 后终态及停止轮询、同 operation 的旧完成标记不可代替 unknown 后新对账。
- typecheck-final.log 通过；build-final.log 正式构建通过（5.86 秒，仅原有 chunk 提示）；冻结 ts_units 对本次 5 文件相对 c39086c 无新增／增长超标，见 health-result.json／measure-current.json／measure-baseline.json；git diff --check 通过。
- 精确 HEAD 与本次 5 文件 SHA256：source-sha256.json。以上原 454 项与基线反例日志均保持原样，不混写成新版本全仓验证。

### 接口、缺口与后续

仅内部 Context read 返回值增显式结果、readNativeCompaction 可选 contextCurrent predicate 及既有 owner 生命周期实现改变；服务端 wire、UI、按钮资格和 compress 提交次数不变。没有新增产品待决定项或实质阻塞。没有浏览器、真机或生产联调证据新增，仍由主会话 I1／独立门禁覆盖；建议亲审这 5 个文件的生命周期差异，并按 source-sha256.json 接收本次修补。

## 9. I1 复审收尾：权威 unavailable、压缩补读串行交接及单一详情 owner

本节合并主会话随后追加的三项收尾，全部已完成，未提交／部署，未操作浏览器。只改获授权的 Context、Controller／PageRecovery 接线与对应行为测试；未改 CSS、Android、主文档或协议。

### 9.1 权威“不提供 Context”与真正读取失败

已核实际原生 DTO：`tui_gateway/contracts/sessions.py` 的 SessionContextBreakdownResult、`tui_gateway/session_usage.py` 的 `_cold_context_breakdown`／`_replace_stale_context_breakdown`。原生 unknown 通过 `context_available:false` 表达，并可能带 required 的 0 占位数值。当前严格 DTO 没有 `context_unknown` 字段，因此不将孤立 `{context_unknown:true}` 当作一个合法原生 breakdown；没有扩展 wire 或宽泛接受假 unknown。

- `ContextAfterCompaction.read` 现在将明确且类型合法的 unavailable 当作本轮 complete，沿现有合并路径表达 unknown，不复制 0 占位数值。
- 已有兼容数值在 Controller 原 Context owner 保留；首次无值只保明确 unavailable 标记，仍显示原未知外观，不制造 0。明确 context_invalidated 仍正常退休旧数值。
- PageRecovery 安装有限 cut 时保留本轮已经合并好的 unavailable 事实；旧代码整段排除 context_available:false，导致首次无值的明确 unknown 又被丢掉。
- RPC reject、空对象、不受 DTO 支持的孤立 unknown 字段、错误类型和 null／array／boolean 等畸形结果仍 incomplete 并按原观察重试。后续正常页面恢复获得数值后可原地更新。
- 行为负对照 `i1-followup/unavailable-before.log` 复现合法 unavailable 不停止轮询／首次无值缺明确 unknown；当前正式 Controller 反例覆盖保旧值、无旧值不造 0、停止轮询、畸形仍重试及下一轮正常恢复得到 42%。

### 9.2 压缩终态历史补读复用正在建立的新 cursor

主会话 I1 提供了重启 epoch 后两次并行全正文恢复的真实证据。本包在 PageRecovery 增加仅供压缩补读使用的窄方法 `historyAfterCompaction`：只等待当前同 owner／当前恢复轮次和 selection 的 conversationRead，等待的是该有限读取，不是 PageRecovery round 或 Usage／Context。读取成功或失败 settle 后重新检查当前读取与 valid；然后仍走原强制 refreshHistory。无匹配在途读取／非当前 owner 保原路径；旧 owner 的后续读取不会触发新页面恢复。

- 不跳过 terminal complete，不将当前未完成读取当作终态已对账，不泛化改变其它写后 force 行为。
- 第一份窗口及新 cursor 建立后，必要的终态补读用新 cursor；读取失败仍沿原路径补必要快照，不死锁。
- `i1-followup/overlap-before.log` 在冷启动与异 epoch 的正式 Controller＋真实 Gateway pending/frame 处理器夹具复现了并行两次恢复。
- 当前 actual Gateway＋受控 REST／RPC（非生产模型）结果：

| 场景 | 当前轮 REST 正文 | RPC 正文行序列 | 当前轮全正文次数 | 最终历史／Context |
|---|---:|---|---:|---|
| cold | 1 次 | 0、0 | 1 | 200 行／10% |
| epoch 重启、旧 cursor 失效 | 0 次 | 200、0 | 1 | 200 行／10% |
| 首份 snapshot RPC 失败后恢复 | 1 次必要回退 | 0（失败不生成正文） | 1 | 200 行／10% |

完整计数在 snapshot-cold.json／snapshot-epoch.json／snapshot-first-failure.json。另覆盖等待期间切到 New Chat，旧会话补读不能恢复或覆盖新页。真实 Python／SQLite 与隐藏 IAB 的最终复验仍由主会话 I1 执行，本夹具不冒称其替代证据。

### 9.3 当前展示详情共用 HistoryDetails

- PageRecovery 对当前 Controller history 的可见详情改走原 `HistoryDetails.prioritize`／接受点，与实际 disclosure 的在途请求共享；Controller.hydrateDetails 仅增加内部 NativeMessage[] 输入形式，旧 node 调用保持。
- await 后核当前 owner／请求代次、物理行＋UID＋role、完整状态及相应 revision。失败仍交既有恢复重试。
- 真正未交接的 stagedConversation 继续隔离读取，保持 context signal、身份及版本校验；途中 staging 退休不把旧页响应当新 staging 证明。
- 在原 ready／布局交接点尽力落盘完整详情，解决局部展开恢复时接受详情早于 ready 而漏掉及时缓存的问题。
- `detail-app-before.log`：真实 App 点击可见旧 Thinking，两个请求竞争，断言 1 实际 2。`detail-cache-before.log`：同样的正式 Controller 双 owner 反例。
- 当前真实 App 未展开 0 次，展开后延迟请求仍只有 1 次；正式 Controller＋真 IDB 覆盖展开、重连与冷开且 revision 不变，详情请求累计仍 1 次。原失败、切 owner、版本变化、隔离 staging 场景继续通过。

### 9.4 当前版本、验证及交接

新增证据根：`/Users/edgar/code/hermes-secretary-web/.archive/incremental-sync-20261027/frontend-incremental/i1-followup/`。旧报告／旧证据保持原样，本节涉及的 6 个文件以此目录 source-sha256.json 为准。

- 当前定向 **5 文件 244 项通过**，见 current-final.log；没有复跑 454 整套。
- typecheck-final.log 通过；build-final.log 正式构建通过，5.59 秒，仅原有 chunk 提示。
- 冻结度量对本次 6 文件无新增／增长超标，见 health-result.json、measure-current.json、measure-baseline.json；Controller 2550 行，未超过冻结基线。git diff --check 通过。
- 内部接口仅 hydrateDetails 的可选数组形式和压缩专用 promise 交接方法；没有新详情 transport 缓存、全局请求 owner、恢复状态机或定时器。PageRecovery availability、Composer 资格、UI 展开／loading 与权限判定保持。

无新产品待决项或实现阻塞。建议主会话按本节 SHA 接收这 6 文件，再重做 I1 epoch／详情请求计数；真实服务与隐藏 IAB 的最终结果继续由主会话记录。

## 10. 主会话最终代码接收（恢复执行后）

主会话已亲审第9节六文件实际路径及上下游，SHA256全部与交回证据一致。合法unavailable与读取失败分开，原有值保留；压缩终态仅等待同owner当前选择的有限历史promise，再沿原强制对账；当前展示详情共享HistoryDetails，staged仍隔离，owner／revision检查保留。接受代码包进入整轮审查。244项、typecheck、build及冻结度量仅按原证据范围复用。

最终真实Python／SQLite／HTTP／WS夹具已重启，但隐藏IAB新建被Work设置拒绝（Local browser use is disabled in Work settings），因此第9节三项最终浏览器复验仍未执行；已向用户提示开启本地浏览器，未回退其它显示方式，不将代码接收写成I1通过。
