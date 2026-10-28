# Verification：20261027-incremental-sync · 云端独立静态审查

## 1. 审查对象与结论概览

**结论：本次 Verification 不通过。** 固定候选共有 **8 项已确认实现不符合、3 类待补证事项**。74条独立判据中，43条在本报告限定的静态范围内符合，27条受已确认缺陷阻断，4条证据不足；同一根因影响多条要求，只登记一次缺陷。静态符合不代表真实浏览器、Android、微信或完整产品回归已通过。

本报告可作为 `.autonomous/20261027-incremental-sync/verification.md` 的本次外部独立审查记录。审查日期为2026-10-27；结论只对应下列两个完整commit，不随分支HEAD移动。

| 对象 | 完整待审版本 | 身份核验 |
|---|---|---|
| 后端 hermes-secretary | [`44eb0be4c3a2c7e9f13157740514fd40bd83aa50`](https://github.com/EdgarZhong/hermes-secretary/commit/44eb0be4c3a2c7e9f13157740514fd40bd83aa50) | Git commit与tree对象已核；tree为00683fe00dd3e6ca482b9baa27d0336eb5fc3283 |
| 前端 hermes-still-chat | [`91ad72f3898be4e6d98461f69566a76b54595290`](https://github.com/EdgarZhong/hermes-still-chat/commit/91ad72f3898be4e6d98461f69566a76b54595290) | Git commit与tree对象已核；tree为1b55f08a3da9734d2f035434ef28117315925d0f |
| 共同分支 | codex/incremental-sync-20261027 | 只作背景信息；所有源证据均固定完整SHA |

主审已复核三个独立分工的关键发现，并检查从正式入口到最终消费方的接线。范围包含初冻前并入的微信、Idle、取消/Notebook、Android免reload、键盘和Toast修复；没有只审初冻后的diff，也没有扩展为07全部Notebook/Scheduler功能验收。后端44eb0be已经包含测试夹具收尾；旧报告中的862326c、旧待修目录问题或阶段暂停状态均不替代本次最终对象及用户新授权。

### 1.1 发现速览

| 编号 | 优先级/性质 | 结论 |
|---|---|---|
| F01 | P1 / 确实缺陷 | 已取消的更早分页仍可写回；401清空后历史重新进入可见状态 |
| F02 | P1 / 确实缺陷 | 已删除的缓存阅读锚点在恢复重试中持续复用 |
| F03 | P2 / 确实缺陷 | 同版本最新Thinking片段覆盖已完整取得的工具详情 |
| F04 | P2 / 确实缺陷 | 缓存占满500身份时丢弃最新已核验Thinking前缀 |
| F05 | P2 / 确实缺陷 | 普通尾部追加Thinking被误判为破坏性历史变化 |
| F06 | P2 / 确实缺陷 | 同计数原生CAS改文完成后缺少历史失效通知 |
| F07 | P1 / 确实缺陷 | Gateway缓存TTL/LRU/pressure未保护Idle依赖的真实父对象 |
| F08 | P1 / 确实缺陷 | 微信普通stop的最后一条完整Assistant消息仍等待Turn收尾 |
| E01 | P1 / 证据不足 | 最终版本性能与关键集成回归的原始记录未随审查包提供 |
| E02 | P2 / 证据不足 | Idle关闭开关、父会话被回收、再次开启/attach的组合未完成闭环证明 |
| E03 | P2 / 证据不足 | D07原生Timeline索引要求与正式WebUI入口的适用范围尚未对应 |

P1表示应优先处理的授权展示、恢复收敛或原生生命周期/发送时点问题；P2表示随后的必要契约修正。**P2并不表示可以带着问题宣布本轮通过。** E类是待补证，不等于已确认场景失败。

### 1.2 实际完成的工作及证据等级

| 证据层 | 本次取得/执行 | 可以支持的结论 |
|---|---|---|
| 固定源码/规格 | 108份后端、81份前端已取文件，共189份；全部重算Git blob与指定对象一致；关键路径、相关测试及已有报告静态审阅。 | 版本身份和已列正式路径的实现事实；不等于189份文件每一行都做了无遗漏的全仓审计。 |
| 本轮已执行的隔离反例 | 原始TypeScript方法隔离执行：分页取消/401、缓存anchor、详情退化、500前缀；原始Python AST：有限切点谓词、Gateway回收及普通final尾分支。 | 指定输入下的源码逻辑结果；HTTP、线程调度、host等依赖采用小型受控适配，不是整产品端到端复现。 |
| 仓内测试源码 | 阅读pytest/Vitest/Robolectric等实际fixture、调用层和断言，包括正式REST/RPC、真实SQLite与受控模型设计。 | 测试设计与覆盖能否排除错误实现；不声称本轮运行通过这些测试。 |
| 既有实施/集成报告 | 读取backend/frontend/integration的汇总、场景与原件路径；未取得ignored目录的日志、网络JSON、图片和runtime SHA清单。 | 仅能确认报告作过何种声明及其自述边界；不能提升为主审独立实测。 |
| 真实外部环境 | 未启动产品/本地Verification或Validation，未操作生产DB、生产模型、Android设备、真实微信发送或部署。 | 这些环境下的用户结果本轮未验证。用户另行进行的本地Validation不被本报告替代或暂停。 |

## 2. 独立要求清单与覆盖

判据v1建立于 **2026-10-27T21:20:52+08:00**。主审先读取上传的云端审查prompt、project内`autonomous-run`及其专业依据、`spec-implementation-review`及Verification模板，再读原口径、指定版本规格/索引，形成下表；之后才读取AGENTS、实现、测试和已有报告。三个并行审查者也各自先冻结要求再读实现。

判据原件`criteria-initial.md`的SHA-256为 `9254987ec94712baf4cce9b722725e3c18f856a2abf40cf77f790782c36e85be`，最终重新核验未变。本次没有根据实现者自评或发现的代码形状放宽要求。

解释优先级：用户原引文/本次授权 → 06顶部2026-10-27新契约C0、D、S、P、C3 → 触及的既有产品语义 → 07 §8.1新增Idle生命周期要求。旧“每次全量”、仅200缓存、2MiB裁剪、5秒恢复deadline reload等与新约定冲突部分有依据地不适用，不作为新版本违规依据。手动点击Retry和系统杀进程后的自然冷启也不等同于禁止的主动恢复reload。

权威规格与任务索引：

- [BE:docs/06-Hermes-Secretary-Web-UI-V1-Spec.md:1-93](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#L1-L93)。
- [BE:docs/06-Hermes-Secretary-Web-UI-V1-Spec.md:451-464](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#L451-L464)（保留的D0/S/D1、有限切点与writer失效要求）。
- [BE:docs/07-scheduler-notebook-noting-compaction-redesign.md:1700-1716](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/docs/07-scheduler-notebook-noting-compaction-redesign.md#L1700-L1716)。
- [BE:.autonomous/20261027-incremental-sync/snapshot-index.md:1-36](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/snapshot-index.md#L1-L36)。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| C0.1 | 06:L9 展示与同步真值分离；**展示缓存**仅提供连续画面，不证明连接、运行状态、审批权限或写入成功。**同步缓存**是完整数据与其服务端游标／版本的原子配对，只能向服务端提出增量请求，不能自行宣布已恢复。 | 机制/约束；直接要求 | 展示不授予权限；同步状态与游标/版本原子绑定 | 追踪hydrate到正文发布与动作判定，断网/失败不得假ready | §3 C0.1 |
| C0.2 | 06:L10 owner与认证隔离；所有Conversation缓存以canonical server origin＋真实Profile＋稳定Conversation／路由归属隔离；runtime、epoch、连接轮次只用于当前有效性判定。切owner不能借用旧owner展示、详情或游标。认证失败立即撤销展示和动作资格，失效正在进行的读写缓存任务。 | 机制/约束；直接要求 | canonical origin、真实Profile、稳定Conversation隔离；代次仅判有效性 | 切owner/认证失败/迟到IDB与网络响应均失去提交资格 | §3 C0.2 |
| C0.3 | 06:L11 500真实消息边界；**Timeline每Conversation最多缓存最近500条真实消息，按后端逻辑顺序和消息身份计数**，不按卡片数、工具组数、Thinking段数计数。已请求／完整收到的详情附着原消息，不另计名额。重复窗口同UID只占一条；原消息淘汰时连同详情、相关版本一起淘汰。默认首屏仍200条，Show More仍原分页；不为填满缓存预读500条。用户正在阅读的更早分页属于当前页面展示数据，仍可按需请求，不写入超过最近500条的可复用缓存。 | 机制/约束；直接要求 | 按服务端逻辑顺序和消息身份计数，详情同槽，默认200不预读500 | 重复UID、工具组、前缀转持久、超过500及更早当前阅读页均保持边界 | §3 C0.3 |
| C0.4 | 06:L12 完整详情与懒取；已完整取得的Thinking／工具参数／结果不因收起UI而丢弃；“不折叠掉数据”不改变原视觉折叠规则。尚未展开、未取得的旧详情继续懒请求。请求中断、缺片或仅收到部分的旧详情不写持久缓存；不能把部分内容标记为完整。 | 机制/约束；直接要求 | 完整详情保留，视觉折叠不变，未取旧详情懒取，旧半截不持久 | 版本相同复用、变化失效；失败/空/未取不能混同 | §3 C0.4 |
| C0.5 | 06:L13 最新Turn主动Thinking；最新Turn的Thinking是主动同步例外：每次当前Conversation的历史同步／恢复都取得其最近500条消息缓存范围内的详情，包括运行中截至本次有限切点的完整前缀，并更新缓存。普通图片下载、侧栏、Files或无关RPC不额外触发Thinking读取。收到的后续流式片段先沿原生事件在内存显示；只有完整快照确认的前缀或明确完整的消息才能写持久缓存。没有可证明身份或完整前缀时保留内存，不伪造完整缓存。2026-10-27用户明确兼容口径：旧的系统触发片段缺少真实Turn来源证据、不能区分启动Turn与仅插入通知时，保持详情懒取，不从更早Turn扩大主动读取范围；新Turn在原生构建／持久化接缝保存最小内部来源标记，精确主动取Thinking。 | 机制/约束；直接要求 | 每次历史同步取真实最新Turn的范围内详情及核验有限前缀；旧模糊系统片段不猜 | 完整身份和有限快照证明，后续流只在内存，U17新来源精确、旧来源懒取 | §3 C0.5 |
| C0.6 | 06:L14 原生事件及前缀归并；不为每条Thinking建立独立游标、轮询或事件日志。历史窗口游标负责整体差异；详情的消息身份与内容版本负责有效性；活动Turn沿原生snapshot／seq／epoch恢复。尚未落库的最新Thinking前缀只作为该原生消息的过渡展示，不伪造持久消息行、不授予running／完成事实；原生落库后按同一UID合并，不额外占一条。无完整原生身份／切点则不落盘。 | 机制/约束；直接要求 | 没有每Thinking游标/轮询/日志；沿窗口游标、seq/epoch/snapshot；落库同UID | 过渡前缀不伪造持久行或运行权限；落库合并不重复计条 | §3 C0.6 |
| C0.7 | 06:L15 存储容量与降级；容量按消息计数，不能截断正文或详情来伪造完整缓存。保留跨Conversation最多10个／7天淘汰；不沿用旧2MiB单窗口限制导致详情自动被裁掉。浏览器配额不足则按旧Conversation／旧消息淘汰并重试，仍失败降级内存；不阻断在线使用、不把存储失败当数据同步成功。Blob、图片二进制、认证凭据不进历史缓存。 | 机制/约束；直接要求 | 最多10会话/7天；完整正文不截断，quota淘汰重试再内存；不保存凭据/二进制 | 核查序列化白名单、损坏、quota恢复，不以存储成功替代网络同步 | §3 C0.7 |
| D01 | 06:L23 D01 Timeline正文／卡片外侧；缓存：同消息身份、逻辑顺序、原展示正文／时间／卡片状态及详情版本；最近500条。持久缓存包含已完成的同消息详情；展示缓存：冷开在确认owner后取精确缓存；暖切回首帧取该owner内存；断线／恢复期间保当前画面；展示最新：当前所见窗口与原生Turn切点完成一致对账后一次交接；后续实时更新不等待整页REST | 数据/时点/归属；直接要求 | 不清空再绘制；不拼回已删／rewind行；不把缓存当恢复完成；不全库扫描 | 初始、重连、回前台、当前历史失效用窗口游标；无缓存／游标失效只读必要窗口；分页按原入口按需读取；须同时满足该行展示条件与失败表现 | §3 D01 |
| D02 | 06:L24 D02 已取得的旧Thinking详情；缓存：完整已收到的reasoning显示数据，归原消息及详情版本；内存与持久均保留，即使UI已折叠；展示缓存：原消息显示且详情已缓存时直接可用，展开无需先清空／重取；展示最新：同消息详情版本未变直接复用；变更时可见已展开详情主动更新，不可见详情撤销旧有效资格、再展开才读 | 数据/时点/归属；直接要求 | 旧网络半截不持久化；不改变流式时展开、完成后自动收起、用户手动展开的行为 | 跟随窗口游标获得详情版本；仅版本变化且当前需要／缓存缺失时按需拉取；须同时满足该行展示条件与失败表现 | §3 D02 |
| D03 | 06:L25 D03 未取得的旧Thinking详情；缓存：只保真实卡片壳／未取标记，不缓存假空正文；展示缓存：卡片按既有折叠状态显示；展示最新：用户展开后得到完整正文，提交为同消息详情并缓存 | 数据/时点/归属；直接要求 | 不为后台补齐而请求所有Thinking；加载／失败／真实空结果保持区别 | 用户展开触发原详情读取；恢复时只有当前实际展开可见的缺失详情需要拉取；须同时满足该行展示条件与失败表现 | §3 D03 |
| D04 | 06:L26 D04 最近一个Turn的Thinking（已完成或运行中）；缓存：已完成正文；运行中仅经原生完整快照核验到有限切点的前缀，含同消息身份和“前缀／完整”标记，不持久化原始事件队列；展示缓存：冷开／断线可显示已核验前缀作为旧画面；不据此推断仍在运行或已完成；展示最新：当前Turn的快照＋有序后续事件接管；转持久消息按UID合并 | 数据/时点/归属；直接要求 | 新Turn开始使“最新”资格转移；旧半截没有完整确认不得升级持久详情；完成、取消、失败沿真实终态，不伪造成功 | 每次该Conversation历史同步／恢复主动拉取可证明的最新Turn详情，或直接复用本次完整state_snapshot；旧的模糊系统触发片段保持懒取，新Turn以内部来源标记精确定位；后续用原生实时事件；无单Thinking游标；须同时满足该行展示条件与失败表现 | §3 D04 |
| D05 | 06:L27 D05 工具参数／结果、折叠终态输出详情；缓存：用户曾展开且完整收到的字段／身份／版本，与原消息一体缓存，不额外计条数；展示缓存：同消息详情缓存有效时立即显示；关闭展开面板不删缓存；展示最新：服务端确认版本不变沿用；变更则当前展开需要的详情拉取并替换 | 数据/时点/归属；直接要求 | 不混淆工具生成中、运行中、完成、失败、取消；失败半截不持久缓存 | 版本由历史增量校验；未展开从不预取；展开／当前可见恢复按既有最多12行批次读取；须同时满足该行展示条件与失败表现 | §3 D05 |
| D06 | 06:L28 D06 历史附件／图片；缓存：消息中的既有授权引用、文件名／类型等；不存Blob／二进制／短期认证令牌；展示缓存：先显示原消息附件壳；已加载资源遵守浏览器原缓存；展示最新：当前视口需要时通过原授权资源入口显示 | 数据/时点/归属；直接要求 | 不因重连下载所有图片，不把过期引用当永久资源，不阻塞无关正文 | 按视口／显式打开加载；引用变化随历史增量；资源失败独立重试；须同时满足该行展示条件与失败表现 | §3 D06 |
| D07 | 06:L29 D07 Timeline索引／跳转；缓存：原有索引内存与选择状态；不额外持久化全历史索引；展示缓存：已有同owner索引可作过渡；展示最新：当前索引读取成功后更新，跳转目标按后端身份定位 | 数据/时点/归属；直接要求 | 不用索引批量拉全部正文；不改变跳转和阅读位置语义 | 复用原生timeline分页游标；展开索引／跳转按需请求；重连仅恢复当前使用范围；须同时满足该行展示条件与失败表现 | §3 D07 |
| D08 | 06:L30 D08 Conversation侧栏；缓存：持久摘要：id／profile／标题／pin／归档／分组及已读分页覆盖；不存可执行runtime状态；展示缓存：冷开／断线／暖切换沿原缓存展示；展示最新：当前摘要分页成功后局部更新；实时active观察单独合并 | 数据/时点/归属；直接要求 | 同名不同Profile不混；不把后台列表失败冻结已恢复聊天；置顶／删除等不自动重放 | 原列表分页拉取＋既有sessions.changed失效；不新造全局列表游标；隐藏时不扩正文读取；须同时满足该行展示条件与失败表现 | §3 D08 |
| D09 | 06:L31 D09 标题／当前Conversation元数据；缓存：同owner最近有效显示值；动作仍取服务端；展示缓存：恢复期间保标题等原显示；展示最新：当前元数据或更新事件有效后更新 | 数据/时点/归属；直接要求 | 当前owner元数据404才确认不存在；子资源404不能删会话或跳New Chat | 每次恢复有界summary读取；事件与本地写回执按现有版本防倒退；须同时满足该行展示条件与失败表现 | §3 D09 |
| D10 | 06:L32 D10 Usage Session／Latest；缓存：持久展示数值、原统计scope／来源和兼容字段；不存运行权限；展示缓存：原视图保最近有效值，unknown／临时失败不清掉有效值；展示最新：该统计视图本次有效结果局部接管，零值是真值 | 数据/时点/归属；直接要求 | 不因读取Usage锁住已核验正文；原切视图／高亮语义保持；失败在既有恢复单行重试 | 每次恢复原生usage_detail拉取，与历史正文并行；持久计数fallback尽量复用本轮已取得的summary，事件沿原失效规则；须同时满足该行展示条件与失败表现 | §3 D10 |
| D11 | 06:L33 D11 Context／Compaction胶囊；缓存：持久兼容的估算／窗口与展示值；compacting等运行状态仅内存；展示缓存：保同模型／Provider兼容的已知值；展示最新：原生有效Context／Compaction状态到达后局部更新 | 数据/时点/归属；直接要求 | 不把unknown误当0；模型变更不沿用不兼容值；只在原正式Turn结束条件高亮 | 每次恢复原生RPC拉取，可与历史并行；模型变化按既有失效规则处理；须同时满足该行展示条件与失败表现 | §3 D11 |
| D12 | 06:L34 D12 Notebook Orb／Noting状态；缓存：同owner内存最后有效状态；不新增持久Notebook实体缓存；展示缓存：断线／重连／临时读取失败保原图标，不能闪unknown；首次无值不造idle；展示最新：本次secretary.state或有效既有状态事件到达后更新 | 数据/时点/归属；直接要求 | 网络状态不覆盖业务图标；真实task_state unknown／关闭／失败按原语义；完成动画不因恢复重复触发 | 每次恢复按既有轻量state拉取／事件失效，独立于历史正文；无新游标；须同时满足该行展示条件与失败表现 | §3 D12 |
| D13 | 06:L35 D13 Notebook展开面板／Schedules；缓存：同owner当前面板内存；不新增持久实体缓存；展示缓存：已打开面板恢复期间保旧内容和展开层级；展示最新：面板所需最新state／列表成功后局部更新 | 数据/时点/归属；直接要求 | 不重开用户已关面板，不制造整板隐藏／重动画，不让未展开排期阻塞聊天 | 未展开不取明细；已展开重连主动拉取；沿既有Secretary／Schedule事件失效；须同时满足该行展示条件与失败表现 | §3 D13 |
| D14 | 06:L36 D14 Pending／审批／发送受理；缓存：当前事务及原owner内存；不从展示缓存恢复权限，不持久化旧审批／pending快照；展示缓存：原输入和未确定提交状态按现有机制保留；不把旧审批伪装可操作；展示最新：当前正式snapshot／receipt恢复后更新可操作性 | 数据/时点/归属；直接要求 | 不自动重发Send／Steer／编辑／审批；不丢已受理消息；失败不冒称未受理或成功 | 每次恢复读原Pending／open_requests／receipt；实时事件沿原机制；须同时满足该行展示条件与失败表现 | §3 D14 |
| D15 | 06:L37 D15 活动Turn正文／Thinking／工具实时输出；缓存：原生当前运行内存；仅D04明确允许的核验前缀进入消息展示缓存，不存原始事件流／运行权限；展示缓存：恢复前保已见画面；活动性未知不伪造idle／running；展示最新：完整state_snapshot＋连续seq后缀对账后接真实事件，正常流式立即显示 | 数据/时点/归属；直接要求 | 恢复不等Turn结束，不逐帧等REST；不能漏字／重复；合法Gateway活动Turn不因无Web流而报异常 | 复用原生epoch／seq／session.events.since和现有完整快照；epoch变更或ring缺口重取当前快照；须同时满足该行展示条件与失败表现 | §3 D15 |
| D16 | 06:L38 D16 Profile／模型／Thinking菜单／默认cwd；缓存：原既有内存；不新增权限配置持久缓存；展示缓存：旧菜单展示不能越过原生当前owner校验；草稿选择保持；展示最新：当前实际打开／New Chat需要的配置读取成功后更新 | 数据/时点/归属；直接要求 | 不扩大设置权限、不用别的Profile配置、不改变模型选择产品行为 | Profile每轮读取；菜单按打开需求拉取；默认cwd仅New Chat需要；关闭菜单不为恢复重复请求；须同时满足该行展示条件与失败表现 | §3 D16 |
| D17 | 06:L39 D17 草稿／附件／编辑意图；缓存：沿原草稿存储及事务机制，与展示历史缓存分离；展示缓存：恢复／断线持续保留输入、附件和编辑意图；展示最新：用户操作或真实受理回执更新；后台同步不得覆盖用户新输入 | 数据/时点/归属；直接要求 | 不以恢复重载清草稿，不重放写操作、不误清未受理内容 | 原owner本地读取／写入，必要receipt只读核实；无历史游标；须同时满足该行展示条件与失败表现 | §3 D17 |
| D18 | 06:L40 D18 Files目录／预览；缓存：沿当前Files固定owner内存；不新增文件正文持久缓存；展示缓存：保当前路径、已打开预览、原画面；展示最新：当前目录／预览所需读取成功后更新 | 数据/时点/归属；直接要求 | 不随聊天Profile换错owner；二进制仍原授权读取；失败局部可见，不整页刷新 | 初始与重连复用现有目录／预览拉取，未打开文件不取；须同时满足该行展示条件与失败表现 | §3 D18 |
| S01 | 06:L46 S01 冷启动，无缓存；校验owner并读首屏、配置、当前状态；无旧权限 | 转换/并发/失败；直接要求 | 沿原加载外观；不造历史、idle图标或旧审批 | 本轮所见窗口和Turn对账成功后显示；附属项独立收敛；必须覆盖触发前后及迟到结果 | §3 S01 |
| S02 | 06:L47 S02 冷启动，有缓存；精确owner候选只供显示；随后主动增量校验 | 转换/并发/失败；直接要求 | 先显示可用旧正文／已取详情／胶囊，首屏与折叠规则保持；不显示旧可执行状态 | 服务端差异＋切点核验后一次交接；必须覆盖触发前后及迟到结果 | §3 S02 |
| S03 | 06:L48 S03 正常连接→断线；旧网络轮次失效，保留用户意图；实时权限沿原失效 | 转换/并发/失败；直接要求 | 正文／阅读位置／展开／输入保留；Notebook原图标保留；Composer原单行Connecting | 网络恢复触发同页恢复，不reload；必须覆盖触发前后及迟到结果 | §3 S03 |
| S04 | 06:L49 S04 断线→Socket连上；connected只证明通道，不能宣布已恢复 | 转换/并发/失败；直接要求 | 缓存画面保持；Composer沿原Restoring项；不闪unknown、不弹AbortError | 当前所见历史与实时状态核验，实际附属项继续各自恢复；必须覆盖触发前后及迟到结果 | §3 S04 |
| S05 | 06:L50 S05 暖恢复／同epoch；缓存游标提出变化请求，实时事件持续有序接收 | 转换/并发/失败；直接要求 | 不清空、不重新挂载、不跳走；不因后台小更新反复夺阅读位置 | 有限切点达成即接管，不等待Turn结束；必须覆盖触发前后及迟到结果 | §3 S05 |
| S06 | 06:L51 S06 服务重启／异epoch；丢弃旧运行权限和事件水位，保留可校验历史缓存；失效历史游标补必要窗口 | 转换/并发/失败；直接要求 | 保旧画面直到新切点；不冒用旧流式running，不重发任何操作 | 原生resume／快照／窗口对账后接管；仍不reload；必须覆盖触发前后及迟到结果 | §3 S06 |
| S07 | 06:L52 S07 请求取消／切owner／旧轮次迟到；取消不是业务失败；旧数据无提交资格 | 转换/并发/失败；直接要求 | 不弹协议错误，不让旧owner覆盖新页；新owner首帧按其缓存／加载显示 | 新owner独立完成；迟到IDB／网络结果丢弃；必须覆盖触发前后及迟到结果 | §3 S07 |
| S08 | 06:L53 S08 必要读取失败／断续弱网；本轮未满足；按现有退避重试，无完整成功回执 | 转换/并发/失败；直接要求 | 保画面、输入和Notebook图标；Composer现有Retrying；不把旧值改unknown或0 | 在线自动重试，后台／离线暂停；不触发网页／APK刷新；必须覆盖触发前后及迟到结果 | §3 S08 |
| S09 | 06:L54 S09 附属读取慢或失败；Chat已核验可独立可用；附属项仍未完成 | 转换/并发/失败；直接要求 | 正文继续实时，Usage／侧栏／Notebook面板保各自旧展示；原单行提示具体未就绪项 | 局部重试完成后仅更新其区域；无全页冻结；必须覆盖触发前后及迟到结果 | §3 S09 |
| S10 | 06:L55 S10 当前可见恢复提交；历史／详情／有限流切点已对账，React完成本次布局 | 转换/并发/失败；直接要求 | 原前缀相容且idle保阅读锚点；真正重连确认active沿原有限滚向末尾；无位移不造动画 | 布局提交即就绪，不等缓存写盘、后台窗口或动画结束；必须覆盖触发前后及迟到结果 | §3 S10 |
| S11 | 06:L56 S11 正常连接中历史失效；当前会话新增、跨渠道完成或真实编辑触发增量；原连续流权限保持 | 转换/并发/失败；直接要求 | 持续呈现新流，后台同步不重新锁整个页面／不重启恢复动画 | 新窗口核验后并入原呈现；旧数据与新事件去重；必须覆盖触发前后及迟到结果 | §3 S11 |
| S12 | 06:L57 S12 用户展开／收起详情；已完整缓存且版本有效直接用；否则只取所需详情 | 转换/并发/失败；直接要求 | 保原卡片loading／错误／空内容表现；收起不删数据、不触发新网络；不改变默认展开规则 | 完整响应与版本有效才缓存；断线半截不写盘；必须覆盖触发前后及迟到结果 | §3 S12 |
| S13 | 06:L58 S13 最新Turn开始／完成／取消；最新Thinking主动恢复资格随真实Turn身份移动；终态沿原source与UID | 转换/并发/失败；直接要求 | 运行中Thinking原展开／流式；完成后原自动收起；不因缓存命中改状态或动画 | 已完整内容与消息身份合并；旧不完整段不冒充完整详情；必须覆盖触发前后及迟到结果 | §3 S13 |
| S14 | 06:L59 S14 Rewind／编辑／压缩／删除行；服务端新顺序及详情版本权威；移除被退役消息及关联详情／前缀 | 转换/并发/失败；直接要求 | 沿原编辑／压缩／定位语义；不复活旧缓存，不把同UID新内容混旧详情 | 对账后原子替换当前需要范围，再更新缓存；必须覆盖触发前后及迟到结果 | §3 S14 |
| S15 | 06:L60 S15 当前Conversation不存在／Profile不可用；必须由对应元数据／roster权威确认；撤销目标缓存及动作 | 转换/并发/失败；直接要求 | 原地址明确说明并给原返回入口；不静默跳New Chat、不循环刷新 | 等用户选择其它目标；不是“连接已恢复”伪成功；必须覆盖触发前后及迟到结果 | §3 S15 |
| S16 | 06:L61 S16 认证失效／登录恢复；撤销敏感展示资格及旧请求；沿既有认证流程 | 转换/并发/失败；直接要求 | 不展示未授权缓存，不刷新打断认证页 | 鉴权恢复后重新确认owner并走同页恢复；必须覆盖触发前后及迟到结果 | §3 S16 |
| S17 | 06:L62 S17 APK回前台／网络恢复；Native仅发同页恢复信号；不再以5秒／退避deadline调用reload | 转换/并发/失败；直接要求 | 保当前页面、草稿、键盘／附件返回状态；恢复接近完成时不被打断 | JS恢复持续收敛；不把无心跳误判业务成功。系统杀进程后属于自然冷启，不是软件主动重载；必须覆盖触发前后及迟到结果 | §3 S17 |
| S18 | 06:L63 S18 存储损坏／配额／缓存缺失；丢弃不可验证缓存／游标，退回所需窗口读取；不改变服务端 | 转换/并发/失败；直接要求 | 正常在线／加载表现，不能因缓存不可用拒绝聊天或丢草稿 | 同页恢复完成后尽力重建缓存；完整消息不截断；必须覆盖触发前后及迟到结果 | §3 S18 |
| P01 | 06:L73 P01 正文与可见详情；`readyForDisplay`来自必要历史／切点及布局提交；缓存只提供此前画面 | 表现/权限；直接要求 | 同owner不清空；详情命中直接用；不因缓存写盘、隐藏分页、未打开菜单迟延正文交接 | 追踪控制状态与实际UI消费，静态可判与动态画面分别记录 | §3 P01 |
| P02 | 06:L74 P02 Composer恢复提示；断线为`Connecting to Hermes…`；连上后按真实waiting显示`Restoring {对象}…`／`Retrying {对象}…` | 表现/权限；直接要求 | 仍固定20px单行、省略号；多项每3秒轮换。chat／usage等名称保持，不伪装只有Chat和Usage、不隐藏真实失败、不增加Toast或横幅 | 追踪控制状态与实际UI消费，静态可判与动态画面分别记录 | §3 P02 |
| P03 | 06:L75 P03 Send／Steer／Stop主按钮；原`composerActionPolicy`读取连接且`availability.ready`、draftReady、pendingKnown、activityKnown、pendingBusy、uncertainSteer及真实运行状态 | 表现/权限；直接要求 | 不用缓存替代任一权限；正文先恢复但必要附属项未就绪时仍沿原按钮禁用规则；连续在线的普通后台刷新沿原continuity资格，不反复锁定 | 追踪控制状态与实际UI消费，静态可判与动态画面分别记录 | §3 P03 |
| P04 | 06:L76 P04 输入、草稿与附件；输入可编辑性仍由draftReady等原条件决定；受理不明优先保留事务 | 表现/权限；直接要求 | 恢复不覆盖新输入、不清附件、不自动提交；原未知受理反馈仍在恢复提示结束后按既有优先级显示 | 追踪控制状态与实际UI消费，静态可判与动态画面分别记录 | §3 P04 |
| P05 | 06:L77 P05 Notebook图标／球；业务task_state与全局开关决定；网络连接不是业务状态 | 表现/权限；直接要求 | 同owner保最后有效业务图标；真实unknown仍unknown；开关关闭仍关闭，完成动画不重复，切owner不借用旧状态 | 追踪控制状态与实际UI消费，静态可判与动态画面分别记录 | §3 P05 |
| P06 | 06:L78 P06 Thinking／工具卡片展开；原流式展开、终态默认收起、用户主动展开的状态及身份归并规则 | 表现/权限；直接要求 | 缓存完整详情不等于强制展开；收起不丢数据；同消息补全文字不重置用户展开选择；读取失败与真实空正文区分 | 追踪控制状态与实际UI消费，静态可判与动态画面分别记录 | §3 P06 |
| P07 | 06:L79 P07 Usage／Context；原视图选择、来源兼容、unknown／零值语义与终态高亮规则；原生确认active的压缩使用原loading环及Compacting | 表现/权限；直接要求 | 缓存不制造已完成Turn、不补造0；真零覆盖旧数值；同owner确认的压缩状态不被历史保留画面遮住，也不等待Chat／Usage恢复。终态按原生状态退出压缩显示并读取最新Context，旧请求不得覆盖新生命周期；局部成功只更新对应胶囊，不重播高亮 | 追踪控制状态与实际UI消费，静态可判与动态画面分别记录 | §3 P07 |
| P08 | 06:L80 P08 视口与滚动；继续沿现有前缀相容、active恢复、手动阅读与布局锚点规则 | 表现/权限；直接要求 | 不因增量替换整树／重复执行无位移scroll；用户分页仍能读早期消息，500上限不裁当前阅读页 | 追踪控制状态与实际UI消费，静态可判与动态画面分别记录 | §3 P08 |
| P09 | 06:L81 P09 审批／Pending／错误；原服务端当前snapshot与真实回执授予动作；取消／过期请求无提交资格 | 表现/权限；直接要求 | 不从缓存复活审批、Stop或重发资格；只消除无异常的Signal Aborted闪现；Compact回执等待超时／断连属于未决，不能当确定失败报错或自动重发；已确认成功按原成功反馈，确定失败仍反馈，未决保原草稿并继续读取原生状态。Toast阴影不得被外层裁成直角灰底，位置／尺寸／关闭／堆叠保持。真实网络／服务端失败仍按原恢复重试或动作反馈呈现 | 追踪控制状态与实际UI消费，静态可判与动态画面分别记录 | §3 P09 |
| P10 | 06:L82 P10 APK生命周期与键盘；原通知导航、拍照／附件返回、IME Insets和网页document归属继续使用 | 表现/权限；直接要求 | 不以恢复超时重载文档；不切焦点／清草稿；键盘尺寸真实变化同回调重绘，保主题与动画进度，不改布局设计 | 追踪控制状态与实际UI消费，静态可判与动态画面分别记录 | §3 P10 |
| C3.1 | 06:L88 复用Desktop原生`session.events.since(last_seen)`、epoch、完整`state_snapshot`与现有恢复封套。它们恢复实时输出；原生timeline游标只分页索引，不足以证明持久正文的编辑／删除，因此历史差异只在现有messages／activate接口新增可选字段，不改变旧调用默认。 | 机制/兼容/证据；直接要求 | 不能以替代机制、孤立helper或构建成功弱化本条 | 核验正式接线、输入边界、证据版本和真实性；缺少必要证据独立判证据不足 | §3 C3.1 |
| C3.2 | 06:L89 历史窗口游标绑定server/profile/Conversation、selector和投影版本；服务端只保有界短期行版本清单，不建立持久事件日志或新数据库。有效游标返回变化行和当前权威顺序／删除事实；无游标／过期／重启返回该必要窗口快照，不能依赖前端盲目append。至少覆盖原位改文、同UID换代表行、rewind、压缩、跨渠道写入及删除。 | 机制/兼容/证据；直接要求 | 不能以替代机制、孤立helper或构建成功弱化本条 | 核验正式接线、输入边界、证据版本和真实性；缺少必要证据独立判证据不足 | §3 C3.2 |
| C3.3 | 06:L90 已取详情需同消息版本确认。旧详情完整且版本未变时，不因新cards投影不含详情而删除。最新Turn Thinking主动详情与活动快照须有真实身份、有限边界和完整性标记；内容字段只用现有用户可见投影，不引入隐藏模型原文。 | 机制/兼容/证据；直接要求 | 不能以替代机制、孤立helper或构建成功弱化本条 | 核验正式接线、输入边界、证据版本和真实性；缺少必要证据独立判证据不足 | §3 C3.3 |
| C3.4 | 06:L91 同一恢复轮次共享元数据／binding读取；Usage、Context等仅需binding的读取不等待历史正文。隐藏菜单和非可见旧分页不得无条件争抢网络；用户打开时仍取得最新数据。已显示旧分页在实际变为需求时校验，不以500缓存上限裁掉用户当前页面。 | 机制/兼容/证据；直接要求 | 不能以替代机制、孤立helper或构建成功弱化本条 | 核验正式接线、输入边界、证据版本和真实性；缺少必要证据独立判证据不足 | §3 C3.4 |
| C3.5 | 06:L92 补齐无reload场景：同／异epoch、活动Turn、断线新增／改写／删除、游标失效、缓存损坏／空／容量淘汰、详情已取／未取／半截、最新Thinking前缀、切owner迟到、失败后自动重试、Files和菜单、APK超5秒仍完成、原生通知导航／附件返回。对照记录200条长正文的完整／无变化／少量追加传输字节与请求数，不能只用时间或测试总数宣称性能完成。 | 机制/兼容/证据；直接要求 | 不能以替代机制、孤立helper或构建成功弱化本条 | 核验正式接线、输入边界、证据版本和真实性；缺少必要证据独立判证据不足 | §3 C3.5 |
| C3.6 | 06:L93 独立main修复亦纳入最终回归：取消请求不弹异常但真失败仍可见；Notebook不闪unknown；键盘resize无空白帧；微信会话内Slash及逐完整Assistant Message即时投递。真实Android／微信外部发送不可用时明确证据边界，不能冒称已实机验证。 | 机制/兼容/证据；直接要求 | 不能以替代机制、孤立helper或构建成功弱化本条 | 核验正式接线、输入边界、证据版本和真实性；缺少必要证据独立判证据不足 | §3 C3.6 |
| CP.1 | 06:L65 U13；§1.14:L767–775 | 生命周期；直接要求 | 压缩busy可合法恢复；Context及时Compacting，终态Chat/Usage/Context自动收敛 | 压缩start/progress/complete/cancel/failure与断线覆盖，不能按普通Turn证明永久拒绝 | §3 CP.1 |
| CP.2 | 06:L65 U14；P09:L81；§1.14:L773 | 未决事务；直接要求 | 活连接不按11分钟丢回执；显式/普通读期限保持；断连不误报成功或失败、不自动重发 | 请求身份、迟到响应、操作生命周期不得串用；确定失败仍反馈，新草稿受owner/version保护 | §3 CP.2 |
| U01 | 上传prompt原始引文；索引U01；06:L5 | 目标/调查证据；直接要求 | 查明恢复比刷新慢的具体原因，轮播提示不证明串行 | 将路径依赖、重复请求和传输量区分；仅可见证据支持结论 | §3 U01 |
| WX.1 | 上传prompt微信Slash引文；索引U11；C3.6:L93 | 跨入口保持；直接要求 | 可禁会话管理，保会话内交互，并沿原授权/busy路径 | 检查微信正式入口的分类、允许项及拦截顺序，不能误送成普通Prompt | §3 WX.1 |
| WX.2 | 上传prompt逐Assistant Message即时发送引文；索引U11；C3.6:L93 | 事件时点/频次；直接要求 | 每条完整Assistant Message产生即交给发送，不等Turn结束/人工缓冲 | 追踪原生消息完成回调、UID和发送队列；允许网络耗时但不引入Turn结束门槛 | §3 WX.2 |
| IDLE.1 | 07 §8.1:L1702–1716，重点L1706；精确依赖保护 | 生命周期/并发；直接要求及必要推导 | 实际DB/Conversation/父对象/owner epoch/period一致，timer存在不够 | 普通orphan/TTL/LRU各正式回收路径均检查精确依赖 | §3 IDLE.1 |
| IDLE.2 | 07 §8.1:L1702–1716，重点L1706；保护整个联合流程 | 生命周期/并发；直接要求及必要推导 | 覆盖Noting正常提交→父压缩→Framework发布；有界存续/取消/终态释放 | 任务预算与强引用/租约边界贯通，无提前释放或永久保活 | §3 IDLE.2 |
| IDLE.3 | 07 §8.1:L1702–1716，重点L1706；失效owner禁止副作用 | 生命周期/并发；直接要求及必要推导 | close/退休/替换回调在消费period和admission前失效，不冻结close空前缀 | 检查显式关闭、删除/归档、替换及并发顺序 | §3 IDLE.3 |
| IDLE.4 | 07 §8.1:L1702–1716，重点L1706；冻结和关闭顺序 | 生命周期/并发；直接要求及必要推导 | 同步冻结与close有确定先后；锁不跨模型网络等待 | 沿所有入口/锁序检查竞态与锁生命周期 | §3 IDLE.4 |
| IDLE.5 | 07 §8.1:L1702–1716，重点L1706；未消费due保留 | 生命周期/并发；直接要求及必要推导 | owner失效保原due/period可合法attach，不重置已失败admission/触发标志 | 检查timer回调、attach恢复与失败路径，不产生补跑或无界重试 | §3 IDLE.5 |
| IDLE.6 | 07 §8.1:L1702–1716，重点L1706；开关关闭终结 | 生命周期/并发；直接要求及必要推导 | global/local关闭走原claim terminal cleanup，清period，不freeze/起child | 重新开启不补跑，不把关闭混同owner暂不可用 | §3 IDLE.6 |
| IDLE.7 | 07 §8.1:L1702–1716，重点L1706；原父前缀与原调度 | 生命周期/并发；直接要求及必要推导 | 不能用DB历史替代父真实冻结前缀，不另建调度器 | 正式freeze来源和timer/owner路径一致 | §3 IDLE.7 |
| IDLE.8 | 07 §8.1:L1702–1716，重点L1706；正常提交后才能Idle压缩 | 生命周期/并发；直接要求及必要推导 | 只在对应Noting正常提交后full compaction；其它原生/手动压缩保持 | 错误、取消、预算耗尽不能触发Idle full compaction；Framework顺序正确 | §3 IDLE.8 |
| G01 | 用户指定最终两SHA；上传prompt精确版本及范围 | 审查边界 | 仅后端44eb0be、前端91ad72f的完整对象；独立main修复亦覆盖 | 固定ref/blob身份、完整性、main修复落在最终树的路径证据可回查 | §3 G01 |
| G02 | 上传prompt首段/输出；索引U02/U03/U12与授权边界 | 过程/不适用范围 | 本任务为外部静态Verification；不修改产品/部署/生产DB/真实模型或发送 | 不续跑本地Validation；动态未验不可冒称通过；main历史豁免不豁免最终回归 | §3 G02 |

## 3. 逐条实现证据

下表中的BE与FE分别固定到§1两仓完整SHA；链接均带对应源码行号。每条要求均给出正式入口/关键路径、核查方法、实际证据及边界。**“符合（静态范围）”只表示该机制在所列路径中成立，不给未执行的设备/网络/像素结果签通过。** 违规行的确切反例和最小关闭条件集中在§5；证据不足行不可视为通过。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| C0.1 | DisplayCache → readCache/retain → 原生恢复切点 → PageRecovery提交与布局确认；动作读取availability。 | 缓存白名单排除运行/审批权限；cache导入窗口标为未核验；只有有效连接、owner、恢复代次与布局确认才能完成本轮。 | [FE:src/core/display-cache.ts:54-68](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L54-L68)<br>[FE:src/core/controller-page-recovery.ts:361-446](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L361-L446)<br>[FE:src/core/page-recovery.ts:79-101](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L79-L101)<br>[FE:src/core/page-recovery.ts:253-304](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L253-L304) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| C0.2 | Show More → Controller.refreshHistory(older) → loadEarlier → HistoryWindows.accept → commitHistoryView → App/Chat。 | 追踪正常读的credentials/Abort保护与分页支路差异；直接执行原始分页、取消、401清理及发布方法的隔离反例。 | [FE:src/core/controller.ts:897-903](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L897-L903)<br>[FE:src/core/controller-page-recovery.ts:467-487](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L467-L487)<br>[FE:src/core/controller-page-recovery.ts:1145-1162](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L1145-L1162)<br>[FE:src/core/page-recovery.ts:181-187](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L181-L187)<br>[FE:src/App.tsx:665-685](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/App.tsx#L665-L685)<br>[FE:src/App.tsx:800-804](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/App.tsx#L800-L804) | 违规：已确认缺陷 F01 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 反例使用内存延迟HTTP、原源码方法和轻量host；证明状态写回及实际UI消费路径，未声称真实浏览器复现或越过服务端鉴权。 |
| C0.3 | 完整原生snapshot → snapshotThinking → commit.pendingCache → DisplayCache.putConversation/prefixValue；落库以native UID归并。 | 核验epoch/seq/Turn/Conversation/message UID和完整前缀标记；500边界反例检查最新前缀是否得到持久保留。 | [FE:src/core/history-thinking-prefix.ts:10-25](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-thinking-prefix.ts#L10-L25)<br>[FE:src/core/controller-page-recovery.ts:904-938](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L904-L938)<br>[FE:src/core/controller-page-recovery.ts:1117-1126](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L1117-L1126)<br>[FE:src/core/display-cache.ts:297-303](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L297-L303)<br>[FE:src/core/display-cache.ts:371-386](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L371-L386) | 违规：已确认缺陷 F04 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 仅有完整来源身份的前缀适用；不要求将无法证明的原始流片段写盘。最新Turn定位另见后端证据。 |
| C0.4 | cards/详情接口 → HistoryDetails → HistoryWindows.accept/cachedDetails → DisplayCache → 同版本重开。 | 核验完整详情与cards壳、同revision复用和按需12行批次；检查latestThinking facet进入独立details map时是否覆盖既得完整工具字段。 | [FE:src/core/history-sync.ts:10-20](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L10-L20)<br>[FE:src/core/history-coverage.ts:28-71](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-coverage.ts#L28-L71)<br>[FE:src/core/display-cache.ts:118-155](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L118-L155)<br>[FE:src/core/history-details.ts:1-113](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-details.ts#L1-L113) | 违规：已确认缺陷 F03 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 源码逻辑反例证明特定窗口迁移下的工具详情退化；未将所有Thinking或仍在当前窗口的完整字段统称丢失。 |
| C0.5 | 完整原生snapshot → snapshotThinking → commit.pendingCache → DisplayCache.putConversation/prefixValue；落库以native UID归并。 | 核验epoch/seq/Turn/Conversation/message UID和完整前缀标记；500边界反例检查最新前缀是否得到持久保留。 | [FE:src/core/history-thinking-prefix.ts:10-25](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-thinking-prefix.ts#L10-L25)<br>[FE:src/core/controller-page-recovery.ts:904-938](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L904-L938)<br>[FE:src/core/controller-page-recovery.ts:1117-1126](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L1117-L1126)<br>[FE:src/core/display-cache.ts:297-303](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L297-L303)<br>[FE:src/core/display-cache.ts:371-386](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L371-L386)<br>[BE:hermes_state_history_sync.py:77-181](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_history_sync.py#L77-L181)<br>[BE:agent/turn_source.py:11-56](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_source.py#L11-L56)<br>[BE:agent/turn_context.py:674-723](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_context.py#L674-L723) | 违规：已确认缺陷 F04 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 仅有完整来源身份的前缀适用；不要求将无法证明的原始流片段写盘。最新Turn定位另见后端证据。 |
| C0.6 | 完整原生snapshot → snapshotThinking → commit.pendingCache → DisplayCache.putConversation/prefixValue；落库以native UID归并。 | 核验epoch/seq/Turn/Conversation/message UID和完整前缀标记；500边界反例检查最新前缀是否得到持久保留。 | [FE:src/core/history-thinking-prefix.ts:10-25](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-thinking-prefix.ts#L10-L25)<br>[FE:src/core/controller-page-recovery.ts:904-938](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L904-L938)<br>[FE:src/core/controller-page-recovery.ts:1117-1126](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L1117-L1126)<br>[FE:src/core/display-cache.ts:297-303](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L297-L303)<br>[FE:src/core/display-cache.ts:371-386](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L371-L386) | 符合（静态范围）：snapshotThinking只取当前native UID/Turn/Conversation的未落库Thinking；complete/epoch/seq先核验，展示status重置unknown，不新增原始事件日志或每Thinking轮询；落库沿UID对账。满500时最新前缀保留缺口计F04，不否定上述身份隔离机制。 | 仅有完整来源身份的前缀适用；不要求将无法证明的原始流片段写盘。最新Turn定位另见后端证据。 |
| C0.7 | DisplayCache读写、白名单校验、TTL/LRU和IDB事务/配额降级。 | canonical owner键；7天/10会话；完整数据与cursor一起存储；不按旧2MiB截正文。写失败删除最旧会话并重试，耗尽后转内存，取消中止在途事务。 | [FE:src/core/display-cache.ts:8-38](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L8-L38)<br>[FE:src/core/display-cache.ts:268-343](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L268-L343)<br>[FE:src/core/display-cache.ts:445-503](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L445-L503) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| D01 | 当前Conversation恢复 → 有界历史窗口读 → activate恢复封套 → D0/S/D1证明 → 前端连续seq后缀与保留画面交接。 | 检查缓存仅显示、窗口权威顺序、删除/代表行变化及实时切点；以原始_same_history谓词反例检查普通Thinking尾部追加。 | [BE:tui_gateway/recovery_view.py:193-263](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L193-L263)<br>[BE:tui_gateway/recovery_view.py:515-576](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L515-L576)<br>[FE:src/core/history-sync.ts:23-56](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L23-L56)<br>[FE:src/core/controller-page-recovery.ts:804-938](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L804-L938) | 违规：已确认缺陷 F02、F03、F05 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 反例限于持久Thinking普通追加；不推断每次恢复必失败，也不把正常破坏性改写的拒绝交接列为缺陷。 |
| D02 | cards/详情接口 → HistoryDetails → HistoryWindows.accept/cachedDetails → DisplayCache → 同版本重开。 | 核验完整详情与cards壳、同revision复用和按需12行批次；检查latestThinking facet进入独立details map时是否覆盖既得完整工具字段。 | [FE:src/core/history-sync.ts:10-20](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L10-L20)<br>[FE:src/core/history-coverage.ts:28-71](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-coverage.ts#L28-L71)<br>[FE:src/core/display-cache.ts:118-155](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L118-L155)<br>[FE:src/core/history-details.ts:1-113](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-details.ts#L1-L113) | 符合（静态范围）：同版本已取得Thinking经retainDetails/thinkingFields保留；折叠不删除已取reasoning。F03已确认的是同消息的完整工具/终态字段被Thinking-only facet降级，未据此泛称Thinking正文也丢失。 | 源码逻辑反例证明特定窗口迁移下的工具详情退化；未将所有Thinking或仍在当前窗口的完整字段统称丢失。 |
| D03 | cards/详情接口 → HistoryDetails → HistoryWindows.accept/cachedDetails → DisplayCache → 同版本重开。 | 核验完整详情与cards壳、同revision复用和按需12行批次；检查latestThinking facet进入独立details map时是否覆盖既得完整工具字段。 | [FE:src/core/history-sync.ts:10-20](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L10-L20)<br>[FE:src/core/history-coverage.ts:28-71](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-coverage.ts#L28-L71)<br>[FE:src/core/display-cache.ts:118-155](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L118-L155)<br>[FE:src/core/history-details.ts:1-113](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-details.ts#L1-L113) | 符合（静态范围）：未取旧Thinking只保壳与deferred标记，展开/当前可见缺片才按需读；完整响应才消除deferred。真实空、失败与未取未被合为同一成功值。 | 源码逻辑反例证明特定窗口迁移下的工具详情退化；未将所有Thinking或仍在当前窗口的完整字段统称丢失。 |
| D04 | 完整原生snapshot → snapshotThinking → commit.pendingCache → DisplayCache.putConversation/prefixValue；落库以native UID归并。 | 核验epoch/seq/Turn/Conversation/message UID和完整前缀标记；500边界反例检查最新前缀是否得到持久保留。 | [FE:src/core/history-thinking-prefix.ts:10-25](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-thinking-prefix.ts#L10-L25)<br>[FE:src/core/controller-page-recovery.ts:904-938](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L904-L938)<br>[FE:src/core/controller-page-recovery.ts:1117-1126](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L1117-L1126)<br>[FE:src/core/display-cache.ts:297-303](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L297-L303)<br>[FE:src/core/display-cache.ts:371-386](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L371-L386)<br>[BE:hermes_state_history_sync.py:77-181](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_history_sync.py#L77-L181)<br>[BE:agent/turn_source.py:11-56](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_source.py#L11-L56) | 违规：已确认缺陷 F04 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 仅有完整来源身份的前缀适用；不要求将无法证明的原始流片段写盘。最新Turn定位另见后端证据。 |
| D05 | cards/详情接口 → HistoryDetails → HistoryWindows.accept/cachedDetails → DisplayCache → 同版本重开。 | 核验完整详情与cards壳、同revision复用和按需12行批次；检查latestThinking facet进入独立details map时是否覆盖既得完整工具字段。 | [FE:src/core/history-sync.ts:10-20](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L10-L20)<br>[FE:src/core/history-coverage.ts:28-71](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-coverage.ts#L28-L71)<br>[FE:src/core/display-cache.ts:118-155](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L118-L155)<br>[FE:src/core/history-details.ts:1-113](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-details.ts#L1-L113) | 违规：已确认缺陷 F03 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 源码逻辑反例证明特定窗口迁移下的工具详情退化；未将所有Thinking或仍在当前窗口的完整字段统称丢失。 |
| D06 | 历史附件引用投影 → Timeline实际附件/图片组件 → 原授权资源路径。 | 持久缓存仅保授权引用/文件元数据；data/blob/二进制/令牌字段被排除；恢复没有全量图片预下载入口。 | [FE:src/core/display-cache.ts:18-38](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L18-L38)<br>[FE:src/core/display-cache.ts:133-155](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L133-L155)<br>[FE:src/core/controller-page-recovery.ts:618-721](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L618-L721) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 确认缓存与恢复调度边界；实际图片网络、浏览器资源缓存及第三方预览器未运行。 |
| D07 | 正式App→design/layout.Timeline滚动容器；Android通知定位→同owner已加载消息UID/row匹配→reveal。原生索引展开入口的适用范围未有权威对应。 | 补查App实际渲染、design导出/容器、sessions API与通知定位消费链；确认摘要分页不是消息索引，不把已加载节点定位包装成完整索引跳转。 | [FE:src/App.tsx:451-474](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/App.tsx#L451-L474)<br>[FE:src/App.tsx:578-637](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/App.tsx#L578-L637)<br>[FE:src/design/layout.tsx:86-115](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/design/layout.tsx#L86-L115)<br>[FE:src/api/sessions.ts:4-19](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/api/sessions.ts#L4-L19)<br>[FE:src/components/android-reply-focus.ts:8-35](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/components/android-reply-focus.ts#L8-L35)<br>[FE:src/components/chat-presentation.tsx:463-477](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/components/chat-presentation.tsx#L463-L477)<br>[FE:src/core/display-cache.ts:305-327](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L305-L327) | 证据不足：E03：无新增全索引持久缓存/无借索引cursor证明正文可静态确认；本WebUI没有原生索引展开/分页的暴露入口。D07文字明确存在该对象，但尚无规格或用户授权说明它仅约束另一原生客户端，不能只因实现未提供而判不适用，也未直接判新增功能缺失。 | 此项是规格对象到正式入口的适用范围证据缺口，不是已确认第九项代码缺陷；普通阅读anchor恢复问题仍由F02单列。 |
| D08 | SessionList分页 → profiles/loaded-page proof → 恢复commit局部合并 → sidebar持久摘要。 | 列表以profile+id归属；只持久标题/分组/分页等摘要，active另读；未完成的Profile分页保旧显示，已证明空页可清旧值。 | [FE:src/core/session-list.ts:1-103](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/session-list.ts#L1-L103)<br>[FE:src/core/display-cache.ts:201-205](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L201-L205)<br>[FE:src/core/display-cache.ts:388-421](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L388-L421)<br>[FE:src/core/controller-page-recovery.ts:1095-1106](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L1095-L1106) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| D09 | profiles roster → 当前Conversation metadata → attach共享binding → 当前owner清理或标题更新。 | 只有当前summary元数据404才认定会话不存在；roster权威否定Profile才撤销；不把子资源404当会话删除、不跳New Chat。异步元数据遵守本轮和更新版本。 | [FE:src/core/controller-page-recovery.ts:489-522](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L489-L522)<br>[FE:src/core/controller-page-recovery.ts:760-802](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L760-L802) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 正式metadata/roster路径可静态确认；分页迟到绕过敏感展示撤销另见F01，不能据本条正向路径否定该缺陷。 |
| D10 | 每轮共享binding → usage_detail及summary fallback → Usage视图观察与独立提交。 | usage读不等待history；保留最后有效scope/来源；unknown不清零，真零可覆盖；所选视图按实际需求恢复。 | [FE:src/core/controller-page-recovery.ts:543-578](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L543-L578)<br>[FE:src/core/controller-page-recovery.ts:648-654](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L648-L654)<br>[FE:src/core/display-cache.ts:164-184](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L164-L184)<br>[FE:src/core/controller.ts:1990-1996](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L1990-L1996)<br>[FE:src/App.tsx:350-425](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/App.tsx#L350-L425) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| D11 | 原生compaction/context RPC → CompactionView生命周期与Context observation → present保留画面 → Context胶囊。 | 合法手动压缩busy有独立证明；同owner active状态越过保留历史画面及时展示；终态后history/usage/context各自收敛，未知不造0，旧生命周期结果无权覆盖新压缩。 | [BE:tui_gateway/recovery_view.py:150-162](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L150-L162)<br>[BE:tui_gateway/recovery_view.py:266-277](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L266-L277)<br>[FE:src/core/controller-page-recovery.ts:317-359](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L317-L359)<br>[FE:src/core/controller-page-recovery.ts:660-679](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L660-L679)<br>[FE:src/core/compaction-read.ts:65-83](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/compaction-read.ts#L65-L83)<br>[FE:src/core/compaction-view.ts:1-187](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/compaction-view.ts#L1-L187)<br>[FE:src/design/indicators.tsx:123-165](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/design/indicators.tsx#L123-L165) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 关键机制静态成立；最终浏览器重测原始结果未入审查包，不能宣称所有压缩失败/取消/慢请求组合已动态通过。 |
| D12 | 同owner secretary.state/event → 单飞观察/Controller.refreshSecretary → Notebook图标与completion提示。 | 网络失败只记录secretaryError，保已有状态；真unknown仍显示unknown；完成提示以实际owner与snapshot身份去重，恢复不会凭缓存制造完成。 | [FE:src/core/controller-page-recovery.ts:580-602](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L580-L602)<br>[FE:src/core/controller.ts:1892-1918](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L1892-L1918)<br>[FE:src/core/secretary-completion.ts:1-42](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/secretary-completion.ts#L1-L42) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| D13 | Notebook/Schedules打开需求 → 既有轻量state/列表 → 当前需求的局部更新。 | 只为已打开面板读取schedules；错误保旧内容，按serial/current丢弃迟到结果；关闭面板不因恢复重开。 | [FE:src/core/controller-page-recovery.ts:604-616](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L604-L616)<br>[FE:src/core/controller-page-recovery.ts:655-659](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L655-L659)<br>[FE:src/core/controller.ts:1925-1945](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L1925-L1945) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| D14 | 原生binding/request snapshot/receipt → Pending恢复 → PageRecovery.availability → composerActionPolicy。 | 展示缓存不恢复审批/Stop/发送资格；必要附属项未就绪仍按原按钮门禁；连续在线的后台局部刷新可保原continuity资格，不把正文ready误作全权限。 | [FE:src/core/page-recovery.ts:79-101](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L79-L101)<br>[FE:src/core/controller-pending.ts:1-100](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-pending.ts#L1-L100)<br>[FE:src/core/server-requests.ts:1-150](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/server-requests.ts#L1-L150)<br>[FE:src/components/ChatComposer.tsx:217-261](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/components/ChatComposer.tsx#L217-L261) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| D15 | 当前Conversation恢复 → 有界历史窗口读 → activate恢复封套 → D0/S/D1证明 → 前端连续seq后缀与保留画面交接。 | 检查缓存仅显示、窗口权威顺序、删除/代表行变化及实时切点；以原始_same_history谓词反例检查普通Thinking尾部追加。 | [BE:tui_gateway/recovery_view.py:193-263](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L193-L263)<br>[BE:tui_gateway/recovery_view.py:515-576](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L515-L576)<br>[FE:src/core/history-sync.ts:23-56](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L23-L56)<br>[FE:src/core/controller-page-recovery.ts:804-938](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L804-L938) | 违规：已确认缺陷 F05 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 反例限于持久Thinking普通追加；不推断每次恢复必失败，也不把正常破坏性改写的拒绝交接列为缺陷。 |
| D16 | roster每轮共享读；打开菜单/New Chat需求 → model/thinking/cwd当前owner读取。 | 菜单仅按当前需求发请求；默认cwd限New Chat；关闭菜单不无条件抢历史网络，stage提交检查本轮current。 | [FE:src/core/controller-page-recovery.ts:489-522](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L489-L522)<br>[FE:src/core/controller-page-recovery.ts:681-716](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L681-L716)<br>[FE:src/core/controller-page-recovery.ts:1091-1094](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L1091-L1094) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| D17 | 原草稿scope/事务 → Draft读取版本 → 命令 captured owner/revision → 真实受理后consume。 | 恢复保留新输入、附件和未定提交；稳定Conversation scope采用版本保护；后台草稿或旧Compact结果不能清掉更新的输入。 | [FE:src/core/controller.ts:809-820](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L809-L820)<br>[FE:src/core/controller.ts:1947-1961](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L1947-L1961)<br>[FE:src/core/command-actions.ts:93-108](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/command-actions.ts#L93-L108)<br>[FE:src/core/command-actions.ts:185-204](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/command-actions.ts#L185-L204) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| D18 | Files固定owner → 注册files-current恢复资源 → 目录/preview读取 → renderer布局确认。 | 当前路径和已打开预览参与局部恢复；有Abort/current保护，二进制沿原授权入口；仅实际打开文件读取，不新加正文持久缓存。 | [FE:src/components/Files.tsx:46-103](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/components/Files.tsx#L46-L103)<br>[FE:src/components/Files.tsx:165-229](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/components/Files.tsx#L165-L229)<br>[FE:src/components/Files.tsx:267-274](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/components/Files.tsx#L267-L274) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 代码接线可确认；第三方PDF/文档预览器实际渲染和授权下载未在本轮运行。 |
| S01 | 无缓存冷开 → 当前owner/roster/metadata → 原生binding/窗口/状态 → 布局提交。 | 无缓存走必要200首屏；未证明的Conversation不造idle或审批；只有当前未提交New Chat可建立idle。 | [FE:src/core/controller-page-recovery.ts:489-578](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L489-L578)<br>[FE:src/core/controller-page-recovery.ts:760-864](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L760-L864)<br>[FE:src/core/controller-page-recovery.ts:1083-1090](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L1083-L1090)<br>[FE:src/core/page-recovery.ts:253-304](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L253-L304) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| S02 | 当前Conversation恢复 → 有界历史窗口读 → activate恢复封套 → D0/S/D1证明 → 前端连续seq后缀与保留画面交接。 | 检查缓存仅显示、窗口权威顺序、删除/代表行变化及实时切点；以原始_same_history谓词反例检查普通Thinking尾部追加。 | [BE:tui_gateway/recovery_view.py:193-263](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L193-L263)<br>[BE:tui_gateway/recovery_view.py:515-576](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L515-L576)<br>[FE:src/core/history-sync.ts:23-56](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L23-L56)<br>[FE:src/core/controller-page-recovery.ts:804-938](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L804-L938) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 反例限于持久Thinking普通追加；不推断每次恢复必失败，也不把正常破坏性改写的拒绝交接列为缺陷。 |
| S03 | socket状态/前台信号 → 取消旧轮次、retain旧画面 → 同页恢复/分资源退避。 | 原生connected不等于恢复成功；保留输入和Notebook旧状态；1/2/5秒退避且离线/后台暂停，没有业务deadline reload。分页支路取消例外见F01。 | [FE:src/core/controller.ts:514-534](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L514-L534)<br>[FE:src/core/controller-page-recovery.ts:135-145](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L135-L145)<br>[FE:src/core/controller-page-recovery.ts:361-388](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L361-L388)<br>[FE:src/core/page-recovery.ts:305-333](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L305-L333) | 违规：已确认缺陷 F01 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| S04 | socket状态/前台信号 → 取消旧轮次、retain旧画面 → 同页恢复/分资源退避。 | 原生connected不等于恢复成功；保留输入和Notebook旧状态；1/2/5秒退避且离线/后台暂停，没有业务deadline reload。分页支路取消例外见F01。 | [FE:src/core/controller.ts:514-534](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L514-L534)<br>[FE:src/core/controller-page-recovery.ts:135-145](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L135-L145)<br>[FE:src/core/controller-page-recovery.ts:361-388](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L361-L388)<br>[FE:src/core/page-recovery.ts:305-333](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L305-L333) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| S05 | 当前Conversation恢复 → 有界历史窗口读 → activate恢复封套 → D0/S/D1证明 → 前端连续seq后缀与保留画面交接。 | 检查缓存仅显示、窗口权威顺序、删除/代表行变化及实时切点；以原始_same_history谓词反例检查普通Thinking尾部追加。 | [BE:tui_gateway/recovery_view.py:193-263](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L193-L263)<br>[BE:tui_gateway/recovery_view.py:515-576](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L515-L576)<br>[FE:src/core/history-sync.ts:23-56](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L23-L56)<br>[FE:src/core/controller-page-recovery.ts:804-938](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L804-L938) | 违规：已确认缺陷 F02、F05 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 反例限于持久Thinking普通追加；不推断每次恢复必失败，也不把正常破坏性改写的拒绝交接列为缺陷。 |
| S06 | epoch变化 → 保留展示、撤销旧运行水位 → 原生resume/snapshot+有界历史重新证明。 | 切点验epoch/runtime/连续seq；失效历史cursor回快照，不复用旧执行权限、不自动重发。 | [FE:src/core/controller-page-recovery.ts:869-938](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L869-L938)<br>[FE:src/core/session-recovery.ts:1-170](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/session-recovery.ts#L1-L170)<br>[FE:src/api/client.ts:202-245](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/api/client.ts#L202-L245) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| S07 | Show More → Controller.refreshHistory(older) → loadEarlier → HistoryWindows.accept → commitHistoryView → App/Chat。 | 追踪正常读的credentials/Abort保护与分页支路差异；直接执行原始分页、取消、401清理及发布方法的隔离反例。 | [FE:src/core/controller.ts:897-903](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L897-L903)<br>[FE:src/core/controller-page-recovery.ts:467-487](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L467-L487)<br>[FE:src/core/controller-page-recovery.ts:1145-1162](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L1145-L1162)<br>[FE:src/core/page-recovery.ts:181-187](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L181-L187)<br>[FE:src/App.tsx:665-685](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/App.tsx#L665-L685)<br>[FE:src/App.tsx:800-804](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/App.tsx#L800-L804) | 违规：已确认缺陷 F01 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 反例使用内存延迟HTTP、原源码方法和轻量host；证明状态写回及实际UI消费路径，未声称真实浏览器复现或越过服务端鉴权。 |
| S08 | socket状态/前台信号 → 取消旧轮次、retain旧画面 → 同页恢复/分资源退避。 | 原生connected不等于恢复成功；保留输入和Notebook旧状态；1/2/5秒退避且离线/后台暂停，没有业务deadline reload。分页支路取消例外见F01。 | [FE:src/core/controller.ts:514-534](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L514-L534)<br>[FE:src/core/controller-page-recovery.ts:135-145](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L135-L145)<br>[FE:src/core/controller-page-recovery.ts:361-388](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L361-L388)<br>[FE:src/core/page-recovery.ts:305-333](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L305-L333) | 违规：已确认缺陷 F02 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| S09 | 共享roster/metadata/binding → history与Usage/Context/Pending等并行 → local resource提交与重试。 | 实际读由resource.required决定；正文交接只等待所需核心，附属局部失败不冻结已核验正文；按钮仍按availability，非可见分页/菜单无条件读已去除。 | [FE:src/core/controller-page-recovery.ts:543-578](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L543-L578)<br>[FE:src/core/controller-page-recovery.ts:618-721](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L618-L721)<br>[FE:src/core/page-recovery.ts:253-298](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L253-L298)<br>[FE:src/core/page-recovery-availability.test.ts:26-120](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery-availability.test.ts#L26-L120) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| S10 | 可见签名/anchor与历史窗口 → recovery commit → React布局ack → 原滚动策略。 | 按消息身份和可见投影有序前缀判断相容，不仅看集合；实际布局确认后ready；持久500边界不直接截当前阅读页。 | [FE:src/core/history-coverage.ts:81-101](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-coverage.ts#L81-L101)<br>[FE:src/core/history-coverage.ts:113-170](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-coverage.ts#L113-L170)<br>[FE:src/core/page-recovery.ts:300-304](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L300-L304)<br>[FE:src/core/controller-page-recovery.ts:939-955](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L939-L955) | 违规：已确认缺陷 F02 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 可静态检查选择器与ack；真实浏览器滚动、DOM连续帧与无位移动画未实测，已删除anchor分支另列发现。 |
| S11 | 正式持久writer → watcher/sessions.changed → 当前会话失效 → 窗口sync权威order/revision替换。 | 游标本身能表达同UID换代表、改文、删除与rewind；另检查writer完成点是否真正发出当前页失效，不能用主动REST重读测试替代通知链。 | [BE:hermes_state_history_sync.py:1-242](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_history_sync.py#L1-L242)<br>[BE:hermes_state_messages.py:382-392](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_messages.py#L382-L392)<br>[BE:hermes_state_messages.py:463-503](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_messages.py#L463-L503)<br>[BE:tui_gateway/change_watcher.py:125-205](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/change_watcher.py#L125-L205)<br>[FE:src/core/history-sync.ts:23-56](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L23-L56) | 违规：已确认缺陷 F06 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 同计数修正缺通知的结论限定正式原生writer；不把外部任意SQL定义为必须实时支持。 |
| S12 | cards/详情接口 → HistoryDetails → HistoryWindows.accept/cachedDetails → DisplayCache → 同版本重开。 | 核验完整详情与cards壳、同revision复用和按需12行批次；检查latestThinking facet进入独立details map时是否覆盖既得完整工具字段。 | [FE:src/core/history-sync.ts:10-20](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L10-L20)<br>[FE:src/core/history-coverage.ts:28-71](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-coverage.ts#L28-L71)<br>[FE:src/core/display-cache.ts:118-155](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L118-L155)<br>[FE:src/core/history-details.ts:1-113](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-details.ts#L1-L113) | 违规：已确认缺陷 F03 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 源码逻辑反例证明特定窗口迁移下的工具详情退化；未将所有Thinking或仍在当前窗口的完整字段统称丢失。 |
| S13 | 完整原生snapshot → snapshotThinking → commit.pendingCache → DisplayCache.putConversation/prefixValue；落库以native UID归并。 | 核验epoch/seq/Turn/Conversation/message UID和完整前缀标记；500边界反例检查最新前缀是否得到持久保留。 | [FE:src/core/history-thinking-prefix.ts:10-25](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-thinking-prefix.ts#L10-L25)<br>[FE:src/core/controller-page-recovery.ts:904-938](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L904-L938)<br>[FE:src/core/controller-page-recovery.ts:1117-1126](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L1117-L1126)<br>[FE:src/core/display-cache.ts:297-303](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L297-L303)<br>[FE:src/core/display-cache.ts:371-386](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L371-L386) | 违规：已确认缺陷 F04 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 仅有完整来源身份的前缀适用；不要求将无法证明的原始流片段写盘。最新Turn定位另见后端证据。 |
| S14 | 正式持久writer → watcher/sessions.changed → 当前会话失效 → 窗口sync权威order/revision替换。 | 游标本身能表达同UID换代表、改文、删除与rewind；另检查writer完成点是否真正发出当前页失效，不能用主动REST重读测试替代通知链。 | [BE:hermes_state_history_sync.py:1-242](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_history_sync.py#L1-L242)<br>[BE:hermes_state_messages.py:382-392](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_messages.py#L382-L392)<br>[BE:hermes_state_messages.py:463-503](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_messages.py#L463-L503)<br>[BE:tui_gateway/change_watcher.py:125-205](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/change_watcher.py#L125-L205)<br>[FE:src/core/history-sync.ts:23-56](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L23-L56) | 违规：已确认缺陷 F02、F06 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 同计数修正缺通知的结论限定正式原生writer；不把外部任意SQL定义为必须实时支持。 |
| S15 | profiles roster → 当前Conversation metadata → attach共享binding → 当前owner清理或标题更新。 | 只有当前summary元数据404才认定会话不存在；roster权威否定Profile才撤销；不把子资源404当会话删除、不跳New Chat。异步元数据遵守本轮和更新版本。 | [FE:src/core/controller-page-recovery.ts:489-522](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L489-L522)<br>[FE:src/core/controller-page-recovery.ts:760-802](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L760-L802) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 正式metadata/roster路径可静态确认；分页迟到绕过敏感展示撤销另见F01，不能据本条正向路径否定该缺陷。 |
| S16 | Show More → Controller.refreshHistory(older) → loadEarlier → HistoryWindows.accept → commitHistoryView → App/Chat。 | 追踪正常读的credentials/Abort保护与分页支路差异；直接执行原始分页、取消、401清理及发布方法的隔离反例。 | [FE:src/core/controller.ts:897-903](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L897-L903)<br>[FE:src/core/controller-page-recovery.ts:467-487](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L467-L487)<br>[FE:src/core/controller-page-recovery.ts:1145-1162](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L1145-L1162)<br>[FE:src/core/page-recovery.ts:181-187](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L181-L187)<br>[FE:src/App.tsx:665-685](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/App.tsx#L665-L685)<br>[FE:src/App.tsx:800-804](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/App.tsx#L800-L804) | 违规：已确认缺陷 F01 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 反例使用内存延迟HTTP、原源码方法和轻量host；证明状态写回及实际UI消费路径，未声称真实浏览器复现或越过服务端鉴权。 |
| S17 | Android前台/网络/心跳 → JS恢复信号；IME Insets → canvas同回调重绘。 | 检查Native主入口、ForegroundRefresh及视口/背景canvas；超时不再调用WebView reload，尺寸变化时同步应用draw，保留动画相位和主题。 | [FE:src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/ForegroundRefresh.kt:37-161](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/ForegroundRefresh.kt#L37-L161)<br>[FE:src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/MainActivity.kt:152-201](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/MainActivity.kt#L152-L201)<br>[FE:src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/MainActivity.kt:215-242](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/MainActivity.kt#L215-L242)<br>[FE:src/design/ambient-backdrop.tsx:116-165](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/design/ambient-backdrop.tsx#L116-L165)<br>[FE:src/core/controller-page-recovery.ts:135-183](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L135-L183) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 只读真实接线和JVM/组件测试源码；未连接真机，未声称IME收起无空白帧、拍照返回或通知导航实机通过。 |
| S18 | DisplayCache读写、白名单校验、TTL/LRU和IDB事务/配额降级。 | canonical owner键；7天/10会话；完整数据与cursor一起存储；不按旧2MiB截正文。写失败删除最旧会话并重试，耗尽后转内存，取消中止在途事务。 | [FE:src/core/display-cache.ts:8-38](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L8-L38)<br>[FE:src/core/display-cache.ts:268-343](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L268-L343)<br>[FE:src/core/display-cache.ts:445-503](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L445-L503) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| P01 | DisplayCache → readCache/retain → 原生恢复切点 → PageRecovery提交与布局确认；动作读取availability。 | 缓存白名单排除运行/审批权限；cache导入窗口标为未核验；只有有效连接、owner、恢复代次与布局确认才能完成本轮。 | [FE:src/core/display-cache.ts:54-68](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L54-L68)<br>[FE:src/core/controller-page-recovery.ts:361-446](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L361-L446)<br>[FE:src/core/page-recovery.ts:79-101](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L79-L101)<br>[FE:src/core/page-recovery.ts:253-304](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L253-L304) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| P02 | PageRecovery各resource状态 → RecoveryIndicator → Composer原20px单行。 | Connecting/Restoring/Retrying文字对应真实waiting/error；多项3秒轮换，省略号与原区域保留，非新Toast替代恢复状态。 | [FE:src/components/RecoveryIndicator.tsx:1-40](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/components/RecoveryIndicator.tsx#L1-L40)<br>[FE:src/components/ChatComposer.tsx:406-411](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/components/ChatComposer.tsx#L406-L411)<br>[FE:src/design/theme.css:228](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/design/theme.css#L228) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 静态状态与样式检查；没有真实帧/截图测量。 |
| P03 | 原生binding/request snapshot/receipt → Pending恢复 → PageRecovery.availability → composerActionPolicy。 | 展示缓存不恢复审批/Stop/发送资格；必要附属项未就绪仍按原按钮门禁；连续在线的后台局部刷新可保原continuity资格，不把正文ready误作全权限。 | [FE:src/core/page-recovery.ts:79-101](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L79-L101)<br>[FE:src/core/controller-pending.ts:1-100](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-pending.ts#L1-L100)<br>[FE:src/core/server-requests.ts:1-150](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/server-requests.ts#L1-L150)<br>[FE:src/components/ChatComposer.tsx:217-261](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/components/ChatComposer.tsx#L217-L261) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| P04 | 原草稿scope/事务 → Draft读取版本 → 命令 captured owner/revision → 真实受理后consume。 | 恢复保留新输入、附件和未定提交；稳定Conversation scope采用版本保护；后台草稿或旧Compact结果不能清掉更新的输入。 | [FE:src/core/controller.ts:809-820](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L809-L820)<br>[FE:src/core/controller.ts:1947-1961](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L1947-L1961)<br>[FE:src/core/command-actions.ts:93-108](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/command-actions.ts#L93-L108)<br>[FE:src/core/command-actions.ts:185-204](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/command-actions.ts#L185-L204) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| P05 | 同owner secretary.state/event → 单飞观察/Controller.refreshSecretary → Notebook图标与completion提示。 | 网络失败只记录secretaryError，保已有状态；真unknown仍显示unknown；完成提示以实际owner与snapshot身份去重，恢复不会凭缓存制造完成。 | [FE:src/core/controller-page-recovery.ts:580-602](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L580-L602)<br>[FE:src/core/controller.ts:1892-1918](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L1892-L1918)<br>[FE:src/core/secretary-completion.ts:1-42](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/secretary-completion.ts#L1-L42) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| P06 | cards/详情接口 → HistoryDetails → HistoryWindows.accept/cachedDetails → DisplayCache → 同版本重开。 | 核验完整详情与cards壳、同revision复用和按需12行批次；检查latestThinking facet进入独立details map时是否覆盖既得完整工具字段。 | [FE:src/core/history-sync.ts:10-20](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L10-L20)<br>[FE:src/core/history-coverage.ts:28-71](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-coverage.ts#L28-L71)<br>[FE:src/core/display-cache.ts:118-155](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L118-L155)<br>[FE:src/core/history-details.ts:1-113](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-details.ts#L1-L113) | 违规：已确认缺陷 F03 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 源码逻辑反例证明特定窗口迁移下的工具详情退化；未将所有Thinking或仍在当前窗口的完整字段统称丢失。 |
| P07 | 原生compaction/context RPC → CompactionView生命周期与Context observation → present保留画面 → Context胶囊。 | 合法手动压缩busy有独立证明；同owner active状态越过保留历史画面及时展示；终态后history/usage/context各自收敛，未知不造0，旧生命周期结果无权覆盖新压缩。 | [BE:tui_gateway/recovery_view.py:150-162](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L150-L162)<br>[BE:tui_gateway/recovery_view.py:266-277](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L266-L277)<br>[FE:src/core/controller-page-recovery.ts:317-359](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L317-L359)<br>[FE:src/core/controller-page-recovery.ts:660-679](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L660-L679)<br>[FE:src/core/compaction-read.ts:65-83](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/compaction-read.ts#L65-L83)<br>[FE:src/core/compaction-view.ts:1-187](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/compaction-view.ts#L1-L187)<br>[FE:src/design/indicators.tsx:123-165](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/design/indicators.tsx#L123-L165) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 关键机制静态成立；最终浏览器重测原始结果未入审查包，不能宣称所有压缩失败/取消/慢请求组合已动态通过。 |
| P08 | 可见签名/anchor与历史窗口 → recovery commit → React布局ack → 原滚动策略。 | 按消息身份和可见投影有序前缀判断相容，不仅看集合；实际布局确认后ready；持久500边界不直接截当前阅读页。 | [FE:src/core/history-coverage.ts:81-101](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-coverage.ts#L81-L101)<br>[FE:src/core/history-coverage.ts:113-170](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-coverage.ts#L113-L170)<br>[FE:src/core/page-recovery.ts:300-304](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L300-L304)<br>[FE:src/core/controller-page-recovery.ts:939-955](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L939-L955) | 违规：已确认缺陷 F02 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 可静态检查选择器与ack；真实浏览器滚动、DOM连续帧与无位移动画未实测，已删除anchor分支另列发现。 |
| P09 | session.compress请求 → receipt/Indeterminate区分 → 原生compaction观察 → captured命令草稿消费；原Toast外框。 | 仅compress默认无30秒/11分钟期限，显式timeout和普通RPC期限保留；断连拒绝为未决、无重发，不误发失败/成功，确定错误仍提示。原Toast裁剪修复另由独立生命周期审查。 | [FE:src/api/client.ts:202-245](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/api/client.ts#L202-L245)<br>[FE:src/core/compaction-read.ts:27-55](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/compaction-read.ts#L27-L55)<br>[FE:src/core/controller.ts:2034-2064](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L2034-L2064)<br>[FE:src/core/command-actions.ts:93-108](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/command-actions.ts#L93-L108)<br>[FE:src/api/client.test.ts:72-108](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/api/client.test.ts#L72-L108)<br>[FE:src/design/toasts.tsx:18-55](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/design/toasts.tsx#L18-L55)<br>[FE:src/design/theme.css:50-63](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/design/theme.css#L50-L63) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 测试代码含超过旧期限和断连用例但本轮未跑；真实长期连接、Toast画面没有本轮运行证据。 |
| P10 | Android前台/网络/心跳 → JS恢复信号；IME Insets → canvas同回调重绘。 | 检查Native主入口、ForegroundRefresh及视口/背景canvas；超时不再调用WebView reload，尺寸变化时同步应用draw，保留动画相位和主题。 | [FE:src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/ForegroundRefresh.kt:37-161](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/ForegroundRefresh.kt#L37-L161)<br>[FE:src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/MainActivity.kt:152-201](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/MainActivity.kt#L152-L201)<br>[FE:src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/MainActivity.kt:215-242](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/MainActivity.kt#L215-L242)<br>[FE:src/design/ambient-backdrop.tsx:116-165](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/design/ambient-backdrop.tsx#L116-L165)<br>[FE:src/core/controller-page-recovery.ts:135-183](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L135-L183) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 只读真实接线和JVM/组件测试源码；未连接真机，未声称IME收起无空白帧、拍照返回或通知导航实机通过。 |
| C3.1 | 旧messages/activate默认调用与显式history_sync/recovery_view opt-in → 原生epoch/snapshot/events.since。 | 新增协议仅通过可选参数进入；旧默认完整读不被隐式改成delta；原生replay cut和历史窗口证明承担不同职责。 | [BE:tui_gateway/recovery_view.py:551-585](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L551-L585)<br>[FE:src/api/client.ts:307-321](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/api/client.ts#L307-L321)<br>[FE:src/core/controller-page-recovery.ts:804-938](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L804-L938)<br>[BE:hermes_cli/web_routers/sessions.py:788-910](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_cli/web_routers/sessions.py#L788-L910)<br>[BE:tui_gateway/methods_session.py:1047-1052](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/methods_session.py#L1047-L1052)<br>[BE:tui_gateway/contracts/sessions.py:222-233](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/contracts/sessions.py#L222-L233) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| C3.2 | 正式持久writer → watcher/sessions.changed → 当前会话失效 → 窗口sync权威order/revision替换。 | 游标本身能表达同UID换代表、改文、删除与rewind；另检查writer完成点是否真正发出当前页失效，不能用主动REST重读测试替代通知链。 | [BE:hermes_state_history_sync.py:18-21](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_history_sync.py#L18-L21)<br>[BE:hermes_state_history_sync.py:184-242](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_history_sync.py#L184-L242)<br>[BE:hermes_state_recovery_view.py:98-193](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_recovery_view.py#L98-L193)<br>[FE:src/core/history-sync.ts:23-56](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L23-L56) | 符合（静态范围）：对已实际发出的同步请求，游标按server/DB、Profile、Conversation、selector、版本绑定，返回权威order与详情revision；128项/1小时有界指纹，重启/失效回必要快照。正式writer通知缺口单列F06，不能由本算法正向结论抵销。 | 同计数修正缺通知的结论限定正式原生writer；不把外部任意SQL定义为必须实时支持。 |
| C3.3 | cards/详情接口 → HistoryDetails → HistoryWindows.accept/cachedDetails → DisplayCache → 同版本重开。 | 核验完整详情与cards壳、同revision复用和按需12行批次；检查latestThinking facet进入独立details map时是否覆盖既得完整工具字段。 | [FE:src/core/history-sync.ts:10-20](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L10-L20)<br>[FE:src/core/history-coverage.ts:28-71](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-coverage.ts#L28-L71)<br>[FE:src/core/display-cache.ts:118-155](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L118-L155)<br>[FE:src/core/history-details.ts:1-113](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-details.ts#L1-L113) | 违规：已确认缺陷 F03 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 源码逻辑反例证明特定窗口迁移下的工具详情退化；未将所有Thinking或仍在当前窗口的完整字段统称丢失。 |
| C3.4 | 共享roster/metadata/binding → history与Usage/Context/Pending等并行 → local resource提交与重试。 | 实际读由resource.required决定；正文交接只等待所需核心，附属局部失败不冻结已核验正文；按钮仍按availability，非可见分页/菜单无条件读已去除。 | [FE:src/core/controller-page-recovery.ts:543-578](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L543-L578)<br>[FE:src/core/controller-page-recovery.ts:618-721](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L618-L721)<br>[FE:src/core/page-recovery.ts:253-298](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L253-L298)<br>[FE:src/core/page-recovery-availability.test.ts:26-120](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery-availability.test.ts#L26-L120) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 本轮为静态路径审查；仓内测试仅阅读，未作为本轮执行通过。 |
| C3.5 | 最终规格要求 → 仓内测试设计/已有backend、frontend、integration报告 → 原始证据可核验性检查。 | 区分源码、已执行隔离谓词、仓内测试源码、实现者自报和缺失原始记录；不以测试总数或截图描述代替最终SHA逐场景/传输证据。 | [BE:.autonomous/20261027-incremental-sync/reports/backend.md:70-105](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/reports/backend.md#L70-L105)<br>[BE:.autonomous/20261027-incremental-sync/reports/frontend.md:1-140](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/reports/frontend.md#L1-L140)<br>[BE:.autonomous/20261027-incremental-sync/reports/integration.md:1-43](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/reports/integration.md#L1-L43) | 证据不足：E01：缺可独立核验的最终对象传输/请求原始记录及最后收尾的浏览器集成结果。测试源码和执行摘要不能代替该证据。 | 被忽略的原始JSON/日志/截图不在指定Git对象中，未取得；本轮没有重启本地Verification/Validation、生产模型、真实微信或真机。 |
| C3.6 | 最终规格要求 → 仓内测试设计/已有backend、frontend、integration报告 → 原始证据可核验性检查。 | 区分源码、已执行隔离谓词、仓内测试源码、实现者自报和缺失原始记录；不以测试总数或截图描述代替最终SHA逐场景/传输证据。 | [BE:.autonomous/20261027-incremental-sync/reports/backend.md:70-105](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/reports/backend.md#L70-L105)<br>[BE:.autonomous/20261027-incremental-sync/reports/frontend.md:1-140](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/reports/frontend.md#L1-L140)<br>[BE:.autonomous/20261027-incremental-sync/reports/integration.md:1-43](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/reports/integration.md#L1-L43) | 违规：已确认缺陷 F08 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 被忽略的原始JSON/日志/截图不在指定Git对象中，未取得；本轮没有重启本地Verification/Validation、生产模型、真实微信或真机。 |
| CP.1 | 原生compaction/context RPC → CompactionView生命周期与Context observation → present保留画面 → Context胶囊。 | 合法手动压缩busy有独立证明；同owner active状态越过保留历史画面及时展示；终态后history/usage/context各自收敛，未知不造0，旧生命周期结果无权覆盖新压缩。 | [BE:tui_gateway/recovery_view.py:150-162](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L150-L162)<br>[BE:tui_gateway/recovery_view.py:266-277](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L266-L277)<br>[FE:src/core/controller-page-recovery.ts:317-359](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L317-L359)<br>[FE:src/core/controller-page-recovery.ts:660-679](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L660-L679)<br>[FE:src/core/compaction-read.ts:65-83](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/compaction-read.ts#L65-L83)<br>[FE:src/core/compaction-view.ts:1-187](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/compaction-view.ts#L1-L187)<br>[FE:src/design/indicators.tsx:123-165](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/design/indicators.tsx#L123-L165) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 关键机制静态成立；最终浏览器重测原始结果未入审查包，不能宣称所有压缩失败/取消/慢请求组合已动态通过。 |
| CP.2 | session.compress请求 → receipt/Indeterminate区分 → 原生compaction观察 → captured命令草稿消费；原Toast外框。 | 仅compress默认无30秒/11分钟期限，显式timeout和普通RPC期限保留；断连拒绝为未决、无重发，不误发失败/成功，确定错误仍提示。原Toast裁剪修复另由独立生命周期审查。 | [FE:src/api/client.ts:202-245](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/api/client.ts#L202-L245)<br>[FE:src/core/compaction-read.ts:27-55](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/compaction-read.ts#L27-L55)<br>[FE:src/core/controller.ts:2034-2064](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L2034-L2064)<br>[FE:src/core/command-actions.ts:93-108](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/command-actions.ts#L93-L108)<br>[FE:src/api/client.test.ts:72-108](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/api/client.test.ts#L72-L108) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 测试代码含超过旧期限和断连用例但本轮未跑；真实长期连接、Toast画面没有本轮运行证据。 |
| U01 | 最终规格要求 → 仓内测试设计/已有backend、frontend、integration报告 → 原始证据可核验性检查。 | 区分源码、已执行隔离谓词、仓内测试源码、实现者自报和缺失原始记录；不以测试总数或截图描述代替最终SHA逐场景/传输证据。 | [BE:.autonomous/20261027-incremental-sync/reports/backend.md:70-105](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/reports/backend.md#L70-L105)<br>[BE:.autonomous/20261027-incremental-sync/reports/frontend.md:1-140](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/reports/frontend.md#L1-L140)<br>[BE:.autonomous/20261027-incremental-sync/reports/integration.md:1-43](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/reports/integration.md#L1-L43) | 证据不足：路径依赖、重复全量/详情请求与新并行接线已有可追踪依据；E01缺原始同对象字节/总请求与版本证据，不能量化宣称“恢复已更快”或根因全部关闭。 | 被忽略的原始JSON/日志/截图不在指定Git对象中，未取得；本轮没有重启本地Verification/Validation、生产模型、真实微信或真机。 |
| WX.1 | 微信适配器 → Slash分类/原授权busy路由；原生完整Assistant Message → callback/FIFO → consumer/final收尾。 | 会话管理与会话内交互分开；同时核验工具前消息和普通stop最终消息时点，不以两条interim通过代表每条消息即时。 | [BE:gateway/weixin_commands.py:9-33](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/weixin_commands.py#L9-L33)<br>[BE:gateway/run_inbound.py:1280-1306](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_inbound.py#L1280-L1306)<br>[BE:gateway/run_inbound.py:592-614](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_inbound.py#L592-L614)<br>[BE:gateway/run_inbound.py:814-860](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_inbound.py#L814-L860) | 符合（静态范围）：会话管理及其别名在原控制修改前拒绝；其余会话内交互仍走原授权、pending和busy处理，未全面禁用Slash。 | 静态完整生产链与局部源码反证；无真实微信发送授权，未发送消息。 |
| WX.2 | 微信适配器 → Slash分类/原授权busy路由；原生完整Assistant Message → callback/FIFO → consumer/final收尾。 | 会话管理与会话内交互分开；同时核验工具前消息和普通stop最终消息时点，不以两条interim通过代表每条消息即时。 | [BE:gateway/run_turn_runner.py:1917-1937](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_turn_runner.py#L1917-L1937)<br>[BE:agent/turn_final_response.py:344-376](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_final_response.py#L344-L376)<br>[BE:agent/turn_finalizer.py:632-654](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_finalizer.py#L632-L654)<br>[BE:gateway/run_turn_runner.py:923-1002](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_turn_runner.py#L923-L1002)<br>[BE:gateway/run_turn_runner.py:1243-1257](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_turn_runner.py#L1243-L1257)<br>[BE:gateway/stream_consumer_messages.py:29-50](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/stream_consumer_messages.py#L29-L50) | 违规：已确认缺陷 F08 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 静态完整生产链与局部源码反证；无真实微信发送授权，未发送消息。 |
| IDLE.1 | Main Turn结束 → 原Idle period/timer → 精确owner检查和短锁freeze → Noting提交 → 父压缩 → Framework；并检查所有host回收。 | 核验DB/Conversation/parent对象/owner epoch/period、close失效、due保留、开关终结及joint completion；TUI路径与Gateway缓存TTL/LRU/pressure分别审查。 | [BE:agent/turn_facade.py:223-228](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_facade.py#L223-L228)<br>[BE:secretary/noting_timers.py:30-77](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L30-L77)<br>[BE:secretary/noting_timers.py:113-164](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L113-L164)<br>[BE:run_agent.py:938-979](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/run_agent.py#L938-L979)<br>[BE:gateway/run_agent_cache.py:910-930](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L910-L930)<br>[BE:gateway/run_agent_cache.py:1051-1112](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L1051-L1112) | 违规：已确认缺陷 F07 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 不使用生产个案或模型运行；源码所有权/锁序与局部隔离事实可核验，整个真实模型联合流程未运行。 |
| IDLE.2 | Main Turn结束 → 原Idle period/timer → 精确owner检查和短锁freeze → Noting提交 → 父压缩 → Framework；并检查所有host回收。 | 核验DB/Conversation/parent对象/owner epoch/period、close失效、due保留、开关终结及joint completion；TUI路径与Gateway缓存TTL/LRU/pressure分别审查。 | [BE:agent/turn_facade.py:223-228](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_facade.py#L223-L228)<br>[BE:secretary/noting_timers.py:30-77](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L30-L77)<br>[BE:secretary/noting_timers.py:113-164](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L113-L164)<br>[BE:run_agent.py:938-979](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/run_agent.py#L938-L979)<br>[BE:gateway/run_agent_cache.py:910-930](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L910-L930)<br>[BE:gateway/run_agent_cache.py:1051-1112](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L1051-L1112) | 违规：已确认缺陷 F07 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 不使用生产个案或模型运行；源码所有权/锁序与局部隔离事实可核验，整个真实模型联合流程未运行。 |
| IDLE.3 | Main Turn结束 → 原Idle period/timer → 精确owner检查和短锁freeze → Noting提交 → 父压缩 → Framework；并检查所有host回收。 | 核验DB/Conversation/parent对象/owner epoch/period、close失效、due保留、开关终结及joint completion；TUI路径与Gateway缓存TTL/LRU/pressure分别审查。 | [BE:agent/turn_facade.py:223-228](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_facade.py#L223-L228)<br>[BE:secretary/noting_timers.py:30-77](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L30-L77)<br>[BE:secretary/noting_timers.py:113-164](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L113-L164)<br>[BE:run_agent.py:938-979](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/run_agent.py#L938-L979)<br>[BE:gateway/run_agent_cache.py:910-930](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L910-L930)<br>[BE:gateway/run_agent_cache.py:1051-1112](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L1051-L1112)<br>[BE:secretary/noting_runtime.py:586-627](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_runtime.py#L586-L627)<br>[BE:secretary/noting_child.py:289-310](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_child.py#L289-L310)<br>[BE:secretary/noting_child.py:385-432](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_child.py#L385-L432)<br>[BE:secretary/noting_compact.py:21-51](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_compact.py#L21-L51) | 违规：已确认缺陷 F07 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 不使用生产个案或模型运行；源码所有权/锁序与局部隔离事实可核验，整个真实模型联合流程未运行。 |
| IDLE.4 | Main Turn结束 → 原Idle period/timer → 精确owner检查和短锁freeze → Noting提交 → 父压缩 → Framework；并检查所有host回收。 | 核验DB/Conversation/parent对象/owner epoch/period、close失效、due保留、开关终结及joint completion；TUI路径与Gateway缓存TTL/LRU/pressure分别审查。 | [BE:agent/turn_facade.py:223-228](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_facade.py#L223-L228)<br>[BE:secretary/noting_timers.py:30-77](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L30-L77)<br>[BE:secretary/noting_timers.py:113-164](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L113-L164)<br>[BE:run_agent.py:938-979](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/run_agent.py#L938-L979)<br>[BE:gateway/run_agent_cache.py:910-930](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L910-L930)<br>[BE:gateway/run_agent_cache.py:1051-1112](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L1051-L1112)<br>[BE:secretary/noting_runtime.py:586-627](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_runtime.py#L586-L627)<br>[BE:secretary/noting_child.py:289-310](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_child.py#L289-L310)<br>[BE:secretary/noting_child.py:385-432](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_child.py#L385-L432)<br>[BE:secretary/noting_compact.py:21-51](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_compact.py#L21-L51) | 违规：已确认缺陷 F07 未关闭；正式触发、影响限定与最小关闭条件见§5。表中正向机制不能抵销该条完整契约的失败。 | 不使用生产个案或模型运行；源码所有权/锁序与局部隔离事实可核验，整个真实模型联合流程未运行。 |
| IDLE.5 | Main Turn结束 → 原Idle period/timer → 精确owner检查和短锁freeze → Noting提交 → 父压缩 → Framework；并检查所有host回收。 | 核验DB/Conversation/parent对象/owner epoch/period、close失效、due保留、开关终结及joint completion；TUI路径与Gateway缓存TTL/LRU/pressure分别审查。 | [BE:agent/turn_facade.py:223-228](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_facade.py#L223-L228)<br>[BE:secretary/noting_timers.py:30-77](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L30-L77)<br>[BE:secretary/noting_timers.py:113-164](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L113-L164)<br>[BE:run_agent.py:938-979](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/run_agent.py#L938-L979)<br>[BE:gateway/run_agent_cache.py:910-930](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L910-L930)<br>[BE:gateway/run_agent_cache.py:1051-1112](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L1051-L1112)<br>[BE:secretary/noting_runtime.py:586-627](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_runtime.py#L586-L627)<br>[BE:secretary/noting_child.py:289-310](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_child.py#L289-L310)<br>[BE:secretary/noting_child.py:385-432](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_child.py#L385-L432)<br>[BE:secretary/noting_compact.py:21-51](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_compact.py#L21-L51)<br>[BE:secretary/noting_runtime.py:754-781](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_runtime.py#L754-L781)<br>[BE:hermes_state_secretary_noting.py:319-345](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_secretary_noting.py#L319-L345) | 符合（静态范围）：失效owner或无真实prefix在claim前拒绝，未消费DB period/due不重置；新合法attach沿原due恢复，不重置trigger_produced。Gateway因回收丧失真实parent的及时性缺陷仍由F07阻断。 | 不使用生产个案或模型运行；源码所有权/锁序与局部隔离事实可核验，整个真实模型联合流程未运行。 |
| IDLE.6 | Main Turn结束 → 原Idle period/timer → 精确owner检查和短锁freeze → Noting提交 → 父压缩 → Framework；并检查所有host回收。 | 核验DB/Conversation/parent对象/owner epoch/period、close失效、due保留、开关终结及joint completion；TUI路径与Gateway缓存TTL/LRU/pressure分别审查。 | [BE:agent/turn_facade.py:223-228](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_facade.py#L223-L228)<br>[BE:secretary/noting_timers.py:30-77](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L30-L77)<br>[BE:secretary/noting_timers.py:113-164](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L113-L164)<br>[BE:run_agent.py:938-979](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/run_agent.py#L938-L979)<br>[BE:gateway/run_agent_cache.py:910-930](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L910-L930)<br>[BE:gateway/run_agent_cache.py:1051-1112](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L1051-L1112)<br>[BE:secretary/noting_runtime.py:586-627](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_runtime.py#L586-L627)<br>[BE:secretary/noting_child.py:289-310](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_child.py#L289-L310)<br>[BE:secretary/noting_child.py:385-432](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_child.py#L385-L432)<br>[BE:secretary/noting_compact.py:21-51](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_compact.py#L21-L51) | 证据不足：E02：有效owner在due直接看到关闭会terminal清退；关闭使父回收、timer取消，再跨due重开/attach的组合没有完整不补跑证明，尚不判确实缺陷。 | 不使用生产个案或模型运行；源码所有权/锁序与局部隔离事实可核验，整个真实模型联合流程未运行。 |
| IDLE.7 | Main Turn结束 → 原Idle period/timer → 精确owner检查和短锁freeze → Noting提交 → 父压缩 → Framework；并检查所有host回收。 | 核验DB/Conversation/parent对象/owner epoch/period、close失效、due保留、开关终结及joint completion；TUI路径与Gateway缓存TTL/LRU/pressure分别审查。 | [BE:agent/turn_facade.py:223-228](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_facade.py#L223-L228)<br>[BE:secretary/noting_timers.py:30-77](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L30-L77)<br>[BE:secretary/noting_timers.py:113-164](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L113-L164)<br>[BE:run_agent.py:938-979](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/run_agent.py#L938-L979)<br>[BE:gateway/run_agent_cache.py:910-930](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L910-L930)<br>[BE:gateway/run_agent_cache.py:1051-1112](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L1051-L1112)<br>[BE:secretary/noting_runtime.py:586-627](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_runtime.py#L586-L627)<br>[BE:secretary/noting_child.py:289-310](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_child.py#L289-L310)<br>[BE:secretary/noting_child.py:385-432](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_child.py#L385-L432)<br>[BE:secretary/noting_compact.py:21-51](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_compact.py#L21-L51) | 符合（静态范围）：freeze仍只取父实际_session_messages或已核验冻结prefix，空prefix在claim前拒绝；没有以DB历史代填或另建scheduler。 | 不使用生产个案或模型运行；源码所有权/锁序与局部隔离事实可核验，整个真实模型联合流程未运行。 |
| IDLE.8 | Main Turn结束 → 原Idle period/timer → 精确owner检查和短锁freeze → Noting提交 → 父压缩 → Framework；并检查所有host回收。 | 核验DB/Conversation/parent对象/owner epoch/period、close失效、due保留、开关终结及joint completion；TUI路径与Gateway缓存TTL/LRU/pressure分别审查。 | [BE:agent/turn_facade.py:223-228](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_facade.py#L223-L228)<br>[BE:secretary/noting_timers.py:30-77](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L30-L77)<br>[BE:secretary/noting_timers.py:113-164](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L113-L164)<br>[BE:run_agent.py:938-979](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/run_agent.py#L938-L979)<br>[BE:gateway/run_agent_cache.py:910-930](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L910-L930)<br>[BE:gateway/run_agent_cache.py:1051-1112](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L1051-L1112)<br>[BE:secretary/noting_runtime.py:586-627](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_runtime.py#L586-L627)<br>[BE:secretary/noting_child.py:289-310](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_child.py#L289-L310)<br>[BE:secretary/noting_child.py:385-432](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_child.py#L385-L432)<br>[BE:secretary/noting_compact.py:21-51](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_compact.py#L21-L51) | 符合（静态范围）：outcome.committed且finish_noting正常提交才走after_normal_commit；请求核验同admission/snapshot/owner并在父压缩后发布Framework，失败/取消不被冒充正常Idle提交。 | 不使用生产个案或模型运行；源码所有权/锁序与局部隔离事实可核验，整个真实模型联合流程未运行。 |
| G01 | GitHub固定commit/tree/blob → 固定文本快照 → 审查所触完整入口，含初冻前独立main修复。 | 核对两仓完整SHA、Git commit对象与逐文件blob；引用固定SHA而非main/动态分支；下载快照不是一次成功git clone的冒称。 | [BE:.autonomous/20261027-incremental-sync/snapshot-index.md:1-36](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/snapshot-index.md#L1-L36)<br>[BE:.autonomous/20261027-incremental-sync/baseline.txt:1-18](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/baseline.txt#L1-L18) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 仅宣称已取且实际阅读/检索文件的身份完整性；不宣称逐行审查两仓所有不相关代码。 |
| G02 | 用户云端prompt → project两项review skill → 先判据后实现 → 并行独立静态审查 → 主审复核报告。 | 74条判据v1在读代码/AGENTS/测试/报告前冻结；不改产品、不部署、不生产发送；没有把现有实现报告当验收标准，也未续跑本地Validation。 | [BE:.autonomous/20261027-incremental-sync/snapshot-index.md:14-36](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/snapshot-index.md#L14-L36) | 符合（静态范围）：在已核查正式路径中满足本条机制；不扩展为实机或所有竞态验证通过。 | 旧阶段文档的“先停后续阶段”安排由用户本次明确授权顺序覆盖；本报告不对另行进行的本地Validation下通过结论。 |

## 4. 核心目标及验证方法审查

### 4.1 增量、完整性与恢复时点

后端的主要机制确已接上正式入口：messages/activate新增可选sync参数，原Desktop默认调用保留；游标是按实际DB/server、Profile、稳定Conversation、selector和投影版本隔离的短期指纹，最多128项、1小时，服务重启失效后回必要窗口。响应同时给当前权威顺序、变化行及完整可见详情版本；前端据order重建，避免把删除/代表行替换误当append。这个方向可静态确认。
[BE:hermes_state_history_sync.py:18-21](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_history_sync.py#L18-L21)<br>[BE:hermes_state_history_sync.py:184-242](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_history_sync.py#L184-L242)<br>[FE:src/core/history-sync.ts:23-56](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L23-L56)

原生实时恢复仍沿完整snapshot、epoch和seq；前端逐序核对有限后缀及held帧，不能凭latest_seq跳过缺失事件。D0、S、D1是有界重读证明，不能要求普通持久追加停止才交接。F05正是在这个边界上把新增Thinking误当旧内容改变；F02则使本可识别的已退役阅读锚点失去正常回退机会。这些问题不能用增加重试次数或把旧缓存宣布ready关闭。
[BE:tui_gateway/recovery_view.py:193-263](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L193-L263)<br>[BE:tui_gateway/recovery_view.py:515-560](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L515-L560)<br>[FE:src/core/controller-page-recovery.ts:820-938](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L820-L938)

U17的新旧来源区分有实际落实：新Turn在真实staging/持久化接缝记录最小UID与Turn身份；旧typed系统片段若缺足够来源证据，返回无法证明而保留懒取，不从更早Turn扩大主动范围。最新Thinking-only投影与普通完整工具详情是不同字段集合；F03正是前端合并它们时损失已有字段。F04则表明500身份上限本身未超额，但容量决策丢掉最新完整前缀，仍不满足“最近500”的保留方向。
[BE:agent/turn_source.py:11-56](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_source.py#L11-L56)<br>[BE:hermes_state_history_sync.py:77-181](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_history_sync.py#L77-L181)<br>[FE:src/core/history-coverage.ts:28-71](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-coverage.ts#L28-L71)<br>[FE:src/core/display-cache.ts:297-303](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L297-L303)

### 4.2 展示可以先恢复，动作资格仍必须有当前证据

同一轮共享roster、metadata和binding，Usage、Context、Pending等只等binding后即可与正文并行。PageRecovery区分核心交接与local resource，保留原按钮availability、draftReady、pendingKnown、activityKnown等条件；连续在线的局部刷新可以保持原continuity资格。这解释了“正文不被附属项拖住”与“动作仍有门禁”可以同时成立，不能把恢复提示轮播本身当成串行网络证据。
[FE:src/core/controller-page-recovery.ts:543-578](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L543-L578)<br>[FE:src/core/controller-page-recovery.ts:618-721](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L618-L721)<br>[FE:src/core/page-recovery.ts:79-101](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L79-L101)<br>[FE:src/core/page-recovery.ts:253-298](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L253-L298)<br>[FE:src/components/ChatComposer.tsx:217-261](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/components/ChatComposer.tsx#L217-L261)

取消/credentials/owner保护在通常读入口存在，但分页提前走loadEarlier，绕过了这些统一资格；单看旧performHistoryRead有AbortController或clearSensitive会清空状态，无法排除F01。必须追到commitHistoryView、publish/present及App真正如何消费history。实际UI不以displayAuthorized阻止Chat显示，因此本报告将401之后重新出现历史列为确认缺陷，同时明确没有证明执行权限或服务端鉴权被恢复。
[FE:src/core/controller.ts:897-903](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L897-L903)<br>[FE:src/core/controller.ts:942-1027](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L942-L1027)<br>[FE:src/core/controller-page-recovery.ts:1145-1162](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L1145-L1162)<br>[FE:src/App.tsx:665-685](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/App.tsx#L665-L685)<br>[FE:src/App.tsx:800-804](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/App.tsx#L800-L804)

### 4.3 压缩、Notebook及原UI修复的正向结论

合法手动压缩以真实maintenance状态恢复，不要求伪造普通Turn source；保留历史画面时仍直接采用当前compaction状态，Context环与Compacting不等Chat/Usage完成。终态按自己的操作生命周期核对，history、usage、context分别收敛；unknown/unavailable不制造零值。session.compress的默认等待不再沿旧固定期限丢弃仍可能到达的回执，断连按未决处理而不重发；真实成功、确定失败和新草稿版本继续区分。这些路径静态符合，最终浏览器失败注入结果仍受E01证据边界限制。
[BE:tui_gateway/recovery_view.py:150-162](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L150-L162)<br>[FE:src/core/controller-page-recovery.ts:317-359](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L317-L359)<br>[FE:src/core/controller-page-recovery.ts:660-679](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L660-L679)<br>[FE:src/api/client.ts:202-245](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/api/client.ts#L202-L245)<br>[FE:src/core/compaction-read.ts:27-83](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/compaction-read.ts#L27-L83)

Notebook同owner读取失败保最后有效业务状态，恢复不会因网络状态闪成unknown；真实业务unknown仍保留。Android Native恢复发同document信号，没有业务deadline重载；键盘引发的canvas真实resize在同一回调draw且保留动画相位/主题。Toast阴影从卡片移到滚动容器合成后，位置、宽度、圆角和关闭/堆叠逻辑保留。上述机制不能替代真机GPU帧、相机返回或Toast像素证据；本报告未宣称这些用户画面已实测通过。
[FE:src/core/controller.ts:1892-1918](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L1892-L1918)<br>[FE:src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/ForegroundRefresh.kt:37-161](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/ForegroundRefresh.kt#L37-L161)<br>[FE:src/design/ambient-backdrop.tsx:116-165](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/design/ambient-backdrop.tsx#L116-L165)<br>[FE:src/design/theme.css:50-63](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/design/theme.css#L50-L63)

### 4.4 微信与Idle必须审到每条消息、每个宿主

微信Slash分类已区分会话管理与会话内交互，工具前完整消息也经UID/FIFO直接投递。但普通stop最终消息另走finalizer，现有测试是在等待native完成之后断言最后一条到达，允许F08通过。应在最终消息已append/flush、微压缩或cleanup仍阻塞时检查真正发送入口，不能只看Turn结束后的总消息数。
[BE:gateway/weixin_commands.py:9-33](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/weixin_commands.py#L9-L33)<br>[BE:gateway/run_turn_runner.py:1243-1257](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_turn_runner.py#L1243-L1257)<br>[BE:agent/turn_final_response.py:344-376](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_final_response.py#L344-L376)<br>[BE:tests/gateway/test_weixin_message_delivery.py:85-106](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tests/gateway/test_weixin_message_delivery.py#L85-L106)<br>[BE:tests/gateway/test_weixin_message_delivery.py:134-176](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tests/gateway/test_weixin_message_delivery.py#L134-L176)

Idle共享owner/epoch/period与completion机制，以及TUI orphan/TTL/LRU保护，均有正式接线。Gateway却持有同一Main AIAgent并从自己的cache poll Idle，其回收只检查Main是否running。强引用只能防对象被GC，不能防soft release清空同对象的真实prefix或释放其资源。F07因此是宿主接线遗漏；不能以TUI测试通过、timer存在或空prefix会fail-closed代替“有效依赖被保护”。关闭开关与父被回收后的再次attach组合仍按E02保留未决，没有贸然判定已经发生错误补跑。
[BE:secretary/noting_timers.py:30-77](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L30-L77)<br>[BE:secretary/noting_child.py:120-193](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_child.py#L120-L193)<br>[BE:secretary/noting_hosts.py:39-58](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_hosts.py#L39-L58)<br>[BE:gateway/run_agent_cache.py:910-930](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L910-L930)<br>[BE:gateway/run_agent_cache.py:1051-1112](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L1051-L1112)

### 4.5 性能数字与运行证据的口径

可见报告列了不同夹具/不同层次的数字。下表**只复述已有报告声明，不是本轮重新测量**，各行不能混成一组或用于推导整页恢复的统一降幅。

| 来源/口径 | 完整/无变化/少量追加 | 本次证据判断 |
|---|---|---|
| backend报告；200条正式REST结果重新序列化的UTF-8 JSON | 6,873,547 / 16,205 / 16,757 bytes；每个单REST case记1次 | 测试源码可审；wire原始数据、fixture及运行SHA不可读；不等于整轮恢复请求总数。 |
| frontend报告；受控transport夹具 | 2,631,101 / 16,857 / 16,946 bytes | 另一夹具/控制层，不能与backend数据拼接；原始transport记录未取得。 |
| integration报告；恢复activate封套 | 无变化17,656 bytes；追加18,403 bytes；另曾发现两份各598,805 bytes的epoch snapshot | 旧IAB报告有具体场景与后续修复说明；最终单snapshot/单detail/unavailable观察停止三项浏览器复验在该文档中仍待执行。 |

[BE:.autonomous/20261027-incremental-sync/reports/backend.md:88-98](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/reports/backend.md#L88-L98)<br>[BE:.autonomous/20261027-incremental-sync/reports/frontend.md:1-157](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/reports/frontend.md#L1-L157)<br>[BE:.autonomous/20261027-incremental-sync/reports/integration.md:13-43](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/reports/integration.md#L13-L43)


静态证据支持三个有针对性的性能方向：减少长正文重复传输、复用binding/summary并放开附属并行、消除特定终态恢复/详情路径重复请求。但原始量化证据不足，且F02/F05会引入额外恢复重试，不能在当前候选上宣称“恢复已比刷新快”或“性能完成”。补证先取已有同版本记录，修复后仅扩充能排除上述错误实现的必要场景。

### 4.6 现有测试为何不能排除本次问题

| 错误实现 | 现有覆盖仍可通过的原因 | 必要的针对性关闭观察 |
|---|---|---|
| F01 迟到分页 | 一般恢复读和owner切换有资格测试，不等于older分页支路被取消。 | 在真正loadEarlier在途时401/断线，检查最终App历史和旧index发布。 |
| F02 失效cached anchor | REST404回退被覆盖，RPC完整失败封套走另一分支。 | 从缓存anchor发activate，后端返回anchor_not_found，下一轮应换合法需求并收敛。 |
| F03/F04 缓存丢字段/前缀 | 当前窗口详情复用、小于500前缀成功均不能证明跨窗口及满额淘汰。 | 窗口移出仍在500的完整工具记录；两个200窗口+100详情再加入最新完整prefix。 |
| F05 普通追加拒绝 | 旧append测试不启sync_version且新增行无reasoning；旧字段改写测试只验证拒绝。 | 真实新版封套的D0/S/D1之间追加带reasoning行，同时保留破坏性改写负对照。 |
| F06 写后无失效 | 主动重读REST证明delta可识别；CAS测试证明DB已改，均没有等待watcher驱动当前页。 | 无另一次append/Turn结算的正式writer完成→广播→前端请求全链。 |
| F07 Gateway维护回收 | TUI回收及completion registry测试不经过Gateway cache。 | 真正Gateway同一parent在等待/Noting/压缩/Framework阶段被各回收机制扫描。 |
| F08 final仍等Turn尾 | 现有测试前两条在Turn活跃时断言，最后一条通过先await native的finish helper检查。 | finalizer阻塞期间断言最后一条已交adapter，解锁后不重复。 |

[FE:src/core/history-sync.test.ts:36-145](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.test.ts#L36-L145)<br>[FE:src/core/controller-page-recovery.test.ts:1218-1252](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.test.ts#L1218-L1252)<br>[BE:tests/tui_gateway/test_recovery_view.py:115-180](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tests/tui_gateway/test_recovery_view.py#L115-L180)<br>[BE:tests/hermes_state/test_unaddressed_rewrite_identity.py:43-71](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tests/hermes_state/test_unaddressed_rewrite_identity.py#L43-L71)<br>[BE:tests/tui_gateway/test_idle_noting_owner.py:183-231](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tests/tui_gateway/test_idle_noting_owner.py#L183-L231)<br>[BE:tests/gateway/test_weixin_message_delivery.py:85-176](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tests/gateway/test_weixin_message_delivery.py#L85-L176)

## 5. 发现、整改优先级与范围外项

下面8项F为确认的不符合，3项E为待补证。每个问题均保留原条款，不通过改写规格关闭。根因与时点由主审复核，隔离反例的执行范围在每项中明确。

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| F01 / P1 / 确实缺陷 | C0.2、S03、S07、S16<br>[FE:src/core/controller-page-recovery.ts:1145-1162](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L1145-L1162)<br>[FE:src/core/page-recovery.ts:181-187](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/page-recovery.ts#L181-L187)<br>[FE:src/core/controller-page-recovery.ts:467-487](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L467-L487)<br>[FE:src/core/controller.ts:1024-1027](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller.ts#L1024-L1027)<br>[FE:src/App.tsx:665-685](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/App.tsx#L665-L685)<br>[FE:src/App.tsx:800-804](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/App.tsx#L800-L804) | 当前会话点Show More，HTTP尚未返回；随后断线或另一当前请求触发401清理。loadEarlier仅捕获owner和recoveryId，未传恢复AbortSignal、未检查credentials或connection；cancel不递增recoveryId。迟到成功响应仍通过检查，沿捕获的旧HistoryWindows进入commitHistoryView。 | 违背取消后无提交资格和认证失效立即撤销展示的要求。401反例中历史先清空为0行，随后重新变成201行，displayAuthorized仍false；App并不以该标志阻止Chat渲染。此处证明的是失效展示重新出现，不宣称服务端鉴权被绕过、写动作恢复或旧数据重新落盘。 | 将分页纳入同一owner/document/connection/恢复代次及credentials提交资格，并可取消网络；清理后旧index引用也不得发布。关闭证据至少包含正在分页时断线、401、切owner后旧成功/失败响应迟到；核对实际App不重现内容、不产生无异常取消Toast，且合法分页保持原行为。 | 未修复；固定两SHA初审确认 |
| F02 / P1 / 确实缺陷 | D01、S05、S08、S10、S14、P08<br>[FE:src/core/controller-page-recovery.ts:820-867](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L820-L867)<br>[FE:src/core/controller-page-recovery.ts:880-902](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L880-L902)<br>[BE:hermes_state_recovery_view.py:145-170](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_recovery_view.py#L145-L170)<br>[BE:tui_gateway/recovery_view.py:551-576](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L551-L576) | 用户正在看已缓存的旧anchor窗口；断线期间该anchor被删除或rewind退役。readWindows直接复用cachedAnchor，后端activate正常返回complete:false/reason=anchor_not_found。该分支被封装为RecoveryAuthorityError；conversationFailure只撤销控制，不清失效anchor，也不采用REST404分支已有的latest回退。 | 在owner和阅读需求不变时，后续恢复轮次继续发送同一失效selector，无法靠现有退避自行收敛。隔离执行两轮实际readConversation得到相同错误、相同selectors、0次REST重取，旧anchor仍在。没有将任意anchor失败误判成会话不存在。 | 在正式activate的anchor_not_found结果上使该阅读锚点失效，按既有“锚点确已不存在”语义建立必要最新窗口或新的合法覆盖；保留owner错误、真实暂时读失败的严格保护。用真实删除/rewind后的cached-anchor恢复验证同document可完成、已退役行不复活、滚动/动作资格正确；不能只增加重试次数。 | 未修复；固定两SHA初审确认 |
| F03 / P2 / 确实缺陷 | C0.4、D01、D05、S12、P06、C3.3<br>[FE:src/core/history-coverage.ts:28-71](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-coverage.ts#L28-L71)<br>[FE:src/core/history-sync.ts:10-20](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L10-L20)<br>[BE:hermes_state_history_sync.py:145-181](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_history_sync.py#L145-L181)<br>[FE:src/core/controller-page-recovery.ts:839-841](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L839-L841)<br>[FE:src/core/controller-page-recovery.ts:1122-1140](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L1122-L1140) | 某消息已取得完整Thinking及工具参数，详情版本为r；之后它离开当前窗口，但仍在最近500范围及真实最新Turn中。新的latest_thinking bundle合法地只携Thinking字段。HistoryWindows.accept无条件details.set，并把tool_arguments/tool_result/terminal_outputs标成deferred，覆盖该消息此前完整记录；当前窗口不含该行时cachedDetails无法从显示行补回。 | 同UID、同版本、并未淘汰的完整工具字段退化为未取得，后续重开需重新请求；离线时不能立即使用已取得详情。违反已完整取得详情保留与cards缺字段不得删详情。Thinking本身在反例中保留；仍在当前窗口的完整消息可能补回，未扩大为所有详情都会丢失。 | 将Thinking作为同消息、同版本的字段更新合并，保留既得完整工具/终态字段；代表或版本变化时再失效。关闭证据要跨“已取详情→窗口移出但仍在500→同版本主动Thinking→缓存写读→再次展开”，断言完整工具参数/结果未丢且不再请求；另保留版本变化失效和半截不持久化。 | 未修复；固定两SHA初审确认 |
| F04 / P2 / 确实缺陷 | C0.3、C0.5、D04、S13<br>[FE:src/core/display-cache.ts:297-303](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L297-L303)<br>[FE:src/core/display-cache.ts:371-386](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/display-cache.ts#L371-L386)<br>[FE:src/core/history-sync.ts:94-121](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/history-sync.ts#L94-L121)<br>[FE:src/core/controller-page-recovery.ts:904-920](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L904-L920)<br>[FE:src/core/controller-page-recovery.ts:1122-1126](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L1122-L1126) | 正式可达缓存形状为latest200＋anchor200＋范围内已取详情100，共500个真实消息身份。原生完整snapshot又提供一个尚未落库的新message UID的完整Thinking前缀。prefixValue先加该UID，发现总数501便直接返回undefined，没有为最新前缀淘汰最旧缓存消息。 | 最新且具完整来源/切点证明的前缀未被缓存，冷开/断线无法沿本条契约保留它。上限没有越界，但淘汰方向违反“最近500”和最新Turn主动前缀要求。问题不是要求所有前缀都不计身份；如果它代表第501条原生消息，应一致淘汰最旧消息及详情，而非丢最新。 | 建立按真实逻辑顺序/身份统一的窗口、详情和前缀容量决策，优先保留最近消息；淘汰不能破坏数据/游标原子配对，也不裁用户当前阅读页。以500边界＋完整原生前缀＋后续同UID落库验证恰好500、旧消息一致淘汰、prefix保留及落库不双计；无完整证明的前缀仍不落盘。 | 未修复；固定两SHA初审确认 |
| F05 / P2 / 确实缺陷 | D01、D15、S05；06 R3.4、C3有限切点目标<br>[BE:tui_gateway/recovery_view.py:193-263](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L193-L263)<br>[BE:tui_gateway/recovery_view.py:515-560](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/recovery_view.py#L515-L560)<br>[FE:src/core/controller-page-recovery.ts:825-835](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/core/controller-page-recovery.ts#L825-L835)<br>[BE:docs/06-Hermes-Secretary-Web-UI-V1-Spec.md:453-458](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#L453-L458) | 新版UI使用sync_version=1；D0与D1之间同owner、同Turn source、旧窗口顺序/身份/版本均未变，只新追加一条带Thinking的Assistant消息。_same_history末尾要求整个latest_thinking bundle完全相等，新增order/rows/revisions使其返回false。 | 本应由D1权威尾部和原生snapshot/cut承接的普通追加变成view_changed；一次触发多一轮读，两次后端尝试都遇追加则该封套complete:false，前端也耗尽有限重试时转退避。违反普通尾追加不使整轮失败；不声称必然永久卡住或所有文本delta触发该问题。 | 只严格核D0已有Thinking身份、顺序和内容版本，允许D1新增由权威尾部证明承接；保留旧Thinking原位改写/删除/Turn换代拒绝。至少以正式REST游标→sync_version=1 activate、第二连接或进程在每次D0/S/D1之间追加带reasoning行验证可完成，并以旧字段改写作负对照。 | 未修复；固定两SHA初审确认 |
| F06 / P2 / 确实缺陷 | S11、S14；06 R3.8<br>[BE:hermes_state_messages.py:382-392](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_messages.py#L382-L392)<br>[BE:hermes_state_messages.py:463-503](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/hermes_state_messages.py#L463-L503)<br>[BE:agent/transcript_repair.py:149-179](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/transcript_repair.py#L149-L179)<br>[BE:agent/transcript_repair.py:211-233](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/transcript_repair.py#L211-L233)<br>[BE:tui_gateway/change_watcher.py:125-205](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tui_gateway/change_watcher.py#L125-L205)<br>[BE:tests/hermes_state/test_unaddressed_rewrite_identity.py:43-71](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tests/hermes_state/test_unaddressed_rewrite_identity.py#L43-L71) | 正式支持的可写replay携message_uid与CAS版本，修改原正文/Thinking后通过append_messages_batch更新原行，inserted=0。完成点未发既有history通知；没有另外的append、rewind或Turn结算时，sessions被监视字段和.history-changed均不变。 | watcher虽观察到DB/WAL mtime并重算，最终sessions摘要仍相等，当前页不发增量请求，旧正文/详情可能保留到另一个独立失效发生。delta比较能力本身正确，也不能弥补触发缺口。范围是支持的原生writer，不是外部任意SQL。 | 在真实CAS内容改写成功完成点接既有变更通知，no-op flush不广播，不以任意DB mtime轮询全部历史。关闭证据应从第二连接正式可写replay改文，经writer→watcher→当前会话恢复，证明无额外append/新Turn也触发一次更新；若认为已有调用方补足，须给同完成点完整接线与该前提证据。 | 未修复；固定两SHA初审确认 |
| F07 / P1 / 确实缺陷 | IDLE.1、IDLE.2、IDLE.3、IDLE.4；07 §8.1 L1706<br>[BE:gateway/run_turn_runner.py:1124-1140](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_turn_runner.py#L1124-L1140)<br>[BE:gateway/run_turn_runner.py:1178-1186](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_turn_runner.py#L1178-L1186)<br>[BE:agent/turn_facade.py:223-228](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_facade.py#L223-L228)<br>[BE:secretary/noting_hosts.py:39-58](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_hosts.py#L39-L58)<br>[BE:gateway/run_agent_cache.py:910-930](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L910-L930)<br>[BE:gateway/run_agent_cache.py:960-1045](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L960-L1045)<br>[BE:gateway/run_agent_cache.py:1051-1112](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_agent_cache.py#L1051-L1112)<br>[BE:run_agent.py:938-979](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/run_agent.py#L938-L979) | Gateway正式Main agent进入同一_agent_cache，Turn结束后原Idle timer已arm，而Main running slot已释放。Gateway LRU/TTL和压力候选只排除正在跑主Turn等条件，没有holds_maintenance检查；soft release移除cache并清_session_messages，且不退休该Idle owner/epoch/timer。 | 待触发或联合维护中的真实父对象及其原生前缀可被回收。仅weakref时父对象可消失；仍有完成handle/worker等强引用时对象未退休但prefix已空，后续冻结可能拒绝为空，维护流程也可能被释放客户端/child打断。TUI orphan/TTL/LRU已有保护不能替代Gateway正式入口；违反“整个联合流程不因普通回收失去真实父会话”。 | 把精确DB/Conversation/父对象/epoch/period及联合completion资格接入Gateway所有普通回收路径，并协调资格判断与释放的竞态，避免只改一个LRU helper；短锁不得覆盖模型等待。关闭证据需正式Gateway cache对等待期、Noting运行、已提交后父压缩、Framework完成前各阶段施加TTL/LRU/pressure，证明真实prefix和parent保留，终态后正常释放；close/替换仍立即失效。 | 未修复；固定两SHA初审确认 |
| F08 / P1 / 确实缺陷 | WX.2、C3.6；用户U11逐完整消息即时发送原文<br>[BE:agent/turn_final_response.py:344-376](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_final_response.py#L344-L376)<br>[BE:agent/turn_finalizer.py:618-654](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/turn_finalizer.py#L618-L654)<br>[BE:agent/micro_compaction.py:117-136](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/micro_compaction.py#L117-L136)<br>[BE:agent/micro_compaction.py:262-267](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/agent/micro_compaction.py#L262-L267)<br>[BE:gateway/run_turn_runner.py:1921-1937](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/gateway/run_turn_runner.py#L1921-L1937) | 工具前完整Assistant消息通过interim callback进入FIFO即时发送；普通stop最终消息在输出transform后已append并flush，但finish_text_response没有调用该完整消息callback，直接break。最终发送仍在run_conversation返回后的finish_stream_consumer/Turn尾路径。 | 只要收尾较慢，已产生并持久化的最终Assistant消息仍等资源清理、微压缩或后续hook；例如micro开启、有可摘要exchange且aux摘要慢，代码会同步等待模型调用后才到发送。符合“interim及时”不等于符合“每条完整消息及时”，与原口径直接冲突。 | 在原生最终Assistant消息内容及UID稳定的完成接缝进入同一有序完整消息发送通道，并以UID防止Turn末尾重发；继续保留真实发送失败及变换语义。关闭需阻塞finalizer/微压缩，在其完成前断言最后一条已交发送；覆盖有工具/无工具、重复同文不同UID、单条失败及终态去重，不必做真实微信外发。 | 未修复；固定两SHA初审确认 |
| E01 / P1 / 证据不足 | C3.5；U01的量化关闭部分<br>[BE:.autonomous/20261027-incremental-sync/reports/backend.md:88-120](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/reports/backend.md#L88-L120)<br>[BE:.autonomous/20261027-incremental-sync/reports/frontend.md:1-157](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/reports/frontend.md#L1-L157)<br>[BE:.autonomous/20261027-incremental-sync/reports/integration.md:13-43](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/.autonomous/20261027-incremental-sync/reports/integration.md#L13-L43) | Git中可见实现者汇总及测试源码，原始wire-bytes/请求记录/runtime或snapshot SHA清单/JSON/PNG在ignored目录，本会话没有原件；集成报告还明确最终epoch单snapshot、详情单请求、unavailable停止观察的浏览器复验当时尚未执行。 | 不能独立核200条长正文的同对象full/unchanged/append字节和完整请求数，也不能将旧版本局部IAB结果当最终两SHA的全部回归。原始证据缺失是证据边界，不等于数字虚假或测试失败；本次代码缺陷本身已足以阻断。 | 优先补交已有原始记录及实际载入源码SHA、测量口径/参数/fixture；分清REST单响应重新序列化字节、activate封套和整轮网络总数。对最后收尾改动提供明确对应最终候选的定向浏览器结果；本报告列出的修复再做最小机制回归。无需为补静态审查材料重跑无关全套。 | 待补证；不宣称对应运行场景失败 |
| E02 / P2 / 证据不足 | IDLE.6<br>[BE:tests/tui_gateway/test_idle_noting_owner.py:204-231](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/tests/tui_gateway/test_idle_noting_owner.py#L204-L231)<br>[BE:secretary/noting_timers.py:38-64](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/secretary/noting_timers.py#L38-L64)<br>[BE:run_agent.py:951-962](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/run_agent.py#L951-L962) | 正常deadline入口有switch-off终结路径，但已有invalid-boundary测试对global/local/idle关闭后reap仍断言旧period保留；没有覆盖关开之间父对象被回收，随后合法新owner attach的完整序列。 | 现有材料不足以证明“关闭走terminal cleanup并清原period、再次开启不补跑”；这与暂时owner失效应保due的语义必须区分。未把单个测试断言直接升级为已确认生产补跑缺陷。 | 提供真实原生开关变更→普通回收→重新开启→合法attach的隔离证据：关闭按规定终结原period，整个关闭阶段不freeze/起child，再开启不补跑旧period；另对owner暂不可用保due作对照。若已有完整正式路径与证据，提交即可复评。 | 待补证；尚不能判符合或确实违规 |
| E03 / P2 / 证据不足 | D07<br>[BE:docs/06-Hermes-Secretary-Web-UI-V1-Spec.md:29](https://github.com/EdgarZhong/hermes-secretary/blob/44eb0be4c3a2c7e9f13157740514fd40bd83aa50/docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#L29)<br>[FE:src/App.tsx:451-474](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/App.tsx#L451-L474)<br>[FE:src/App.tsx:578-637](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/App.tsx#L578-L637)<br>[FE:src/design/layout.tsx:86-115](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/design/layout.tsx#L86-L115)<br>[FE:src/api/sessions.ts:4-19](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/api/sessions.ts#L4-L19)<br>[FE:src/components/android-reply-focus.ts:8-35](https://github.com/EdgarZhong/hermes-still-chat/blob/91ad72f3898be4e6d98461f69566a76b54595290/src/components/android-reply-focus.ts#L8-L35) | 最后补查确认正式Timeline是已有history/live的滚动容器，Load earlier是正文分页；sessions API是Conversation摘要分页。可达的Android通知跳转仅匹配同owner已加载消息；没有暴露D07所说的原生索引展开/索引cursor分页入口。 | 能证明没有新增全索引持久化或拿索引cursor代替正文差异，但不能据此宣称D07的全部索引同步/跳转要求通过。当前材料也不足以证明本轮删除了原有索引功能，故没有将其升级为已证实现缺陷。 | 给出D07所指原有索引的正式入口及其客户端范围。如果该行仅约束原生Desktop而不在本WebUI暴露，应提供对应规格或授权依据后登记不适用；如果它确属本轮WebUI要求，则补足实现与按需索引/身份跳转证据。不能单凭当前实现没有该功能修改验收范围。 | 待规格到入口对应依据；不计作第九项缺陷 |

### 5.1 F01｜已取消的更早分页仍可写回；401清空后历史重新进入可见状态

**证据方法：** 直接执行固定源码原始loadEarlier、PageRecovery.cancel、authenticationFailure/clearSensitive、commitHistoryView/publish/present，HTTP只由内存延迟Promise提供；结果见§6.4。主审另核App最终渲染消费链。

**边界与排除项：** 没有运行真实浏览器或真实认证服务；跨不同owner已被现有owner比较挡住，不把该正向保护说成不存在。


### 5.2 F02｜已删除的缓存阅读锚点在恢复重试中持续复用

**证据方法：** 前端两轮原始readConversation/readWindows/validateEnvelope/conversationFailure隔离执行；返回值采用已核后端正式_failure封套形状，见§6.4。

**边界与排除项：** 没有运行实际退避计时器、DOM或数据库删除；循环持续的结论来自不改变selector的正式控制流，条件是没有用户改换阅读目标或其它独立状态改变。


### 5.3 F03｜同版本最新Thinking片段覆盖已完整取得的工具详情

**证据方法：** 原始HistoryWindows/retainDetails源码执行：before含known full arguments，retained及reopened均不再有tool_calls，revision保持r200，见§6.4。后端真实Thinking-only投影已交叉确认。

**边界与排除项：** 未执行真实IDB/浏览器；反例证明内存详情记录及再次采纳已退化，后续持久化路径的后果由正式白名单代码确认。


### 5.4 F04｜缓存占满500身份时丢弃最新已核验Thinking前缀

**证据方法：** 实际snapshotThinking、HistoryWindows.cachedDetails和DisplayCache.putConversation/peek隔离执行；500时prefix=false，仅去掉一条最旧详情后prefix=true，见§6.4。

**边界与排除项：** 未用不合法500首屏替代产品路径；使用两个各200窗口和100条既得详情。没有测真实IDB配额或设备容量。


### 5.5 F05｜普通尾部追加Thinking被误判为破坏性历史变化

**证据方法：** 直接AST抽取固定blob93ee8ef00b07bb6f407e7f5e619bb93fea17eb2d的_same_history；相同旧区间下无sync接受true，启sync只追加Thinking接受false。封套失败是已核调用点的确定控制流后果。

**边界与排除项：** 只实际运行纯谓词；未运行完整RPC、模型或数据库并发。旧append测试没有sync_version=1且无reasoning，不能排除此反例。


### 5.6 F06｜同计数原生CAS改文完成后缺少历史失效通知

**证据方法：** 静态核原生CAS UPDATE、计数条件、事务commit、Secretary reconcile和watcher摘要；现有正式writer测试证明这种输入被支持，但本轮未运行该测试。

**边界与排除项：** 不宣称所有编辑路径缺通知：replace_messages、rewind、显式set_user_content及Turn租约释放各有既有通知。未动态观察跨进程或浏览器。


### 5.7 F07｜Gateway缓存TTL/LRU/pressure未保护Idle依赖的真实父对象

**证据方法：** 完整正式对象链经主审复核；AST执行真实LRU/TTL及soft-release方法，在maintenance_allowed=true、Main不running输入下均evicted=true、prefix=[]、epoch不变、closed=false。压力路径只静态核，不称已执行。

**边界与排除项：** probe的排队线程被同步适配以隔离选择/释放逻辑；未运行Gateway服务/数据库/模型。没有声称已观察到生产Notebook错误内容或全部场景必然起空child。


### 5.8 F08｜微信普通stop的最后一条完整Assistant消息仍等待Turn收尾

**证据方法：** 已核真实gateway callback/consumer上下游；对finish_text_response正常尾分支的原始AST执行只出现durable-final-flush，没有complete-message callback。实际等待点由finalizer→micro_compaction→call_llm→run_sync串行代码证明。

**边界与排除项：** 没有伪造不存在的AssistantMessageResultEvent类名；依据实际assistant dict/UID与原生callback。没有调用微信或模型，未把发送网络耗时本身列为缺陷。


### 5.9 E01｜最终版本性能与关键集成回归的原始记录未随审查包提供

**证据方法：** 只读Git中三个实现/集成报告及相关测试；原始记录未取得，没有把其汇总转写为主审实测。

**边界与排除项：** 用户已允许本地Validation另行推进；报告中的“当时未执行”不推断用户现在仍未执行。后续新提交证据可补审，当前未知。


### 5.10 E02｜Idle关闭开关、父会话被回收、再次开启/attach的组合未完成闭环证明

**证据方法：** 源码和测试断言静态对比；并行审查者及主审均保留未决，不为凑缺陷数作过强结论。

**边界与排除项：** 现有保period测试的due在未来3600秒；本报告不把到期前短暂关闭直接断言为必须立即删除。缺口是关闭期间父被回收、timer被取消、跨过原due后再重开/attach的完整组合。未运行该组合，也没有提出新产品语义或新的scheduler。


### 5.11 E03｜D07原生Timeline索引要求与正式WebUI入口的适用范围尚未对应

**证据方法：** 追加核查固定ref的design/index/layout/chat、api/sessions、android-reply-focus及App/controller接线；主审未接受仅以实现缺入口为由豁免明确规格条款。

**边界与排除项：** 这是适用范围/追溯证据不足，不要求用户现在新增未授权功能；当前Android best-effort定位本身未发现新缺陷。


### 5.12 有依据的不适用及未扩大的范围

- 新契约明确替代的旧全量传输、200条持久缓存、2MiB正文裁剪和5秒主动重载机制不再作为要求。原分页默认200及用户正在阅读的更早内容仍适用。
- 07只有本轮明确加入的§8.1 Idle生命周期范围，不扩大为全部Noting/Force/Scheduler重验；不将生产个案身份或生产数据库作为复现材料。
- 手动Retry、应用首次自然冷开与禁止的恢复deadline reload分开处理；未因代码中存在任何`reload`或`loadUrl`字符串便判违规。
- 真实Android画面、实际微信送达和真实模型摘要未执行且无新增外部操作授权。本报告把它们作为清楚的Validation边界，不为了“通过”擅自外发，也不把缺设备一律当已证代码缺陷。
- 最后测试夹具目录初始化已包含于指定后端44eb0be；未将旧文档的待办当作最终版本仍缺该修复。未运行其“4项clean-export通过”声明中的测试，因此只接收版本边界，不继承通过数量。

### 5.13 建议的关闭顺序

先处理F01的取消/认证提交资格与F02的失效anchor收敛，再处理F07的Gateway维护保护及F08的完整消息发送时点。随后关闭F03/F04的详情与最近500容量一致性、F05的有限切点普通追加、F06的原生writer失效接线。每项依§5对应最小机制回归提交新SHA及原始记录；E01优先补现有证据，E02补关闭/回收/重开完整序列，E03补D07规格对象到正式入口的适用范围依据。单纯增加重试、清空全部缓存、延长reload期限、主动重发Compact或用DB历史重建父prefix都不能作为关闭办法。

## 6. 修复与独立复审

### 6.1 本轮状态

本轮为固定候选的初次云端独立静态Verification，没有修改产品代码、规格或现有测试，没有提交修复、部署或改变用户本地Validation流程。创建内容仅为审查副本、独立判据、隔离反例及本报告。因此尚无“修复后复审通过”可登记；8项F和3类E均未关闭。

### 6.2 独立性及研讨记录

判据v1先于实现调查冻结，原件最终hash未变。并行分工分别审前端缓存/恢复、后端协议/原生writer、生命周期/独立main修复；主审负责横跨入口的动作资格、压缩、附属并行与最终裁决。

主审要求F01追到最终Chat可见消费，而不是只看map被写；F03确认后端Thinking-only投影合法且明确当前窗口可补回的排除条件；F04改用正式可达200+200+100容量输入并避免“所有prefix都不计名额”的错误解释；F05核旧区间稳定及普通新增边界；F06补查native notify_committed是否能补足历史广播；F07补齐同一parent建入cache、Main结束、回收、soft release不退休与强弱引用事实；F08核共享Assistant构建/UID、最终flush及微压缩同步等待，未臆造源码中不存在的事件类。E02始终保留证据不足，没有以推测列成第九项缺陷。

对后续修复，建议复审仍从同一74条要求出发，先验证每项根因及负对照，再对直接影响范围作必要回归。若用户确实改变语义，应单独记录新授权及判据版本；实现者的解释或自评不自动改变现有判据。

### 6.3 来源身份与可复核材料

GitHub固定ref读取后对189份本地原件重新计算Git blob，全部一致；保存环节若曾多出一个末尾LF，只在移除该字节后精确匹配目标blob时纠正，未更改产品语义。所有隔离反例记录的15项source SHA-256也与最终审查原件相符。工作区未成功克隆git，实际采用的是固定commit/tree/blob的文本快照；这里没有将其宣称为已执行仓库checkout或项目测试。

审查输入及证据文件SHA-256：

| 材料 | SHA-256 |
|---|---|
| cloud-static-review-prompt.md | f422d34e7a75a55604ed317fc1bf29859d4b4122dfc8b023c9531ce386158431 |
| 09-skills-clean.zip | 4ca879a00fe5d8d20849fe4040ab406e39b8733f852233b3f5faa30ca6b1bffb |
| criteria-initial.md | 9254987ec94712baf4cce9b722725e3c18f856a2abf40cf77f790782c36e85be |
| frontend_counterexamples.cjs | 3f07667d0c0f53b7e8204b3881014a5611d6d248a4e0057005617e74ccf7662b |
| frontend_counterexamples.json | b42e1bec5318f62306329e69d3634ed68583932bb3aa3d58bb7f6d6b7057acca |
| backend_append_predicate_probe.py | 7af63186446643e9d3f6ec58ad0da589bbd4c62fa66d8be8f32a941cf9cd8d76 |
| backend_append_predicate_probe.json | 49cbaa2280f8ed64218fe623a80206f561bc5fabab356634a2f9761a31d70e1e |
| lifecycle_logic_probe.py | 2e52a635cb0900bd9b4ce0dd75cbc8a4ff6ef47d70d93d353b59a4fe078c3a36 |
| lifecycle_logic_probe.json | 0e2bc8fab71d09918929998b83f4c404810eadd66452f2601e70f1f0607335d0 |


下表是已取得原件的身份清单。它证明引用版本一致，不宣称清单中所有无关行均经过逐行安全/性能审计；具体实际审查路径以§3和§5为准。

| 仓库 | 路径 | Git blob SHA-1 |
|---|---|---|
| BE | .autonomous/20261027-incremental-sync/baseline.txt | 2a101c2f363c453b02fd74e83d72082a92f3603c |
| BE | .autonomous/20261027-incremental-sync/plan.md | b29636d848865b9f3a8f8bc884941a61afbb0be3 |
| BE | .autonomous/20261027-incremental-sync/reports/backend.md | 607d588de2f9c81bd1cc71df4cfb88f49c3e52d9 |
| BE | .autonomous/20261027-incremental-sync/reports/frontend.md | c537bebe3c35a91ca14dbd1624e7eff68e340ae1 |
| BE | .autonomous/20261027-incremental-sync/reports/integration.md | 35feec4837d0c0656e40273149c54a8df81c4af2 |
| BE | .autonomous/20261027-incremental-sync/snapshot-index.md | a18613e573061ad7a631a7ef0cb907125af435db |
| BE | AGENTS.md | b34cb7888eac388d014bdf95e07ee193445c52bb |
| BE | agent/AGENTS.md | d76bfa6187e525770121280efac05b5aa49f276d |
| BE | agent/chat_completion_helpers.py | 6304685cfc149a78661b4ed547d3202c1bd360e7 |
| BE | agent/context_compaction_request.py | e9b3a9e40a912532a1322a8da1896e8435814bae |
| BE | agent/conversation_loop.py | 17349b073902516e20a84cf85e2b939d8a3690c3 |
| BE | agent/message_metadata.py | 531ea26a12865d9d837990fd0d205bc761a10229 |
| BE | agent/micro_compaction.py | 54c7cdcc4534321b01a10560eca0dbbd6815aabc |
| BE | agent/output_identity.py | 9d887d2c1a7802ddd74d2a5d0e9d8358bbb85292 |
| BE | agent/reasoning_params.py | 3749faa67e45bccabd12b418e35b04345099d305 |
| BE | agent/session_persistence.py | bfce0c687a1ef4ee5c8762f6a458d7cf0129cb46 |
| BE | agent/stream_delivery.py | 8ee13302f5c42dbd8b56c95c6922d68aa2d929cc |
| BE | agent/transcript_repair.py | d463c4606657da23f9d637f2e0f21778a6bdc5cb |
| BE | agent/turn_context.py | 2c5849a5abb3e205528bc284478e5fb2326a19a8 |
| BE | agent/turn_facade.py | 2acdb8201e103a9af8b7594df5ef7dc3f0d41704 |
| BE | agent/turn_final_response.py | b64ec35be22d8a8dbafa5b7a1d88cb1827680955 |
| BE | agent/turn_finalizer.py | 21770d4ba8033b491519b926042148edda0abb36 |
| BE | agent/turn_response_intake.py | eebd9d12debaef2d5b810dd7a2fc2f88775d960f |
| BE | agent/turn_source.py | 8d12330d597603766207707116604416e2e5ddea |
| BE | agent/turn_stop_gates.py | dc202a0103695362ec00eb497fb116e5a9abfa82 |
| BE | agent/turn_tool_round.py | 402f9b95013fe82a02766e2bcd84d33ba85de313 |
| BE | apps/desktop/src/api/sessions.ts | 8b759e957b3f25b8a7243188f553b07d161d5069 |
| BE | apps/desktop/src/app/session/hooks/use-session-actions/index.ts | 40bff29e2d03586412d5e06bdf7e5d7e75e77a2c |
| BE | docs/06-Hermes-Secretary-Web-UI-V1-Spec.md | 65a1f85d904ea3e3031faf4a2296c5dc9796a4c1 |
| BE | docs/07-scheduler-notebook-noting-compaction-redesign.md | fae8ccc2569b46db66fe66ae3779005c8e0436ed |
| BE | gateway/AGENTS.md | 785a5d8c0d132b5cf3fe9587d9b003506b301e7c |
| BE | gateway/platforms/base.py | 5330f14568851c158207c61fbfe88afbddd4e571 |
| BE | gateway/platforms/weixin.py | 5523874f5537bb114ff7804392c96cc1cc4f9a98 |
| BE | gateway/run.py | fc324480ad880322f690912d6d448c6f4744c4b4 |
| BE | gateway/run_agent_cache.py | 8301c7e6ffb048590ee2fedca6b8417b2f6ee81c |
| BE | gateway/run_busy.py | 4b0fe2da425bec6f34fdfafa3d5e68aebde47d92 |
| BE | gateway/run_inbound.py | 77fe5aadfbbca3c83c8e69820ba5638b8f8f418e |
| BE | gateway/run_inbound_consumer.py | 691e956599bb58d25053e826de6c529973925f58 |
| BE | gateway/run_turn.py | 88eb47838ab29e3f7fc8dd4f250abb3cf4f5c63f |
| BE | gateway/run_turn_first_response.py | e0d2227a3fb344ec6cda4e7eebd3c6be94d58c89 |
| BE | gateway/run_turn_runner.py | 9ad947458b0cdac710b52bb2dc4de147dc4914b4 |
| BE | gateway/run_watchers.py | 122829ff7190158920a874f14ba556f011c1adad |
| BE | gateway/secretary_reminders.py | 5c26037c9f866ba8cd61d7bb0fcd8591312fccff |
| BE | gateway/session_state.py | 61b95b50186cc9abf66b74d8769a97116f49bdc5 |
| BE | gateway/slash_commands.py | 55217e974f9fa3d16808a248bf82f7c38d235b92 |
| BE | gateway/stream_consumer.py | 35c98429b17431edea500e0cd6d648fafc128e90 |
| BE | gateway/stream_consumer_messages.py | c9710770ec3fa317d2d3d56c7b00c0528c0fbc52 |
| BE | gateway/weixin_commands.py | be70205978e8a196477283b7c691131801f85601 |
| BE | hermes_cli/commands.py | 1d4ae320d260d74a5989f9a432a6ac386336b7e5 |
| BE | hermes_cli/observability/shared_metrics_harness.py | efacbd994de58dee2923a51c0862737dfa927788 |
| BE | hermes_cli/web_history_cards.py | 7d87823c58af3faca6c83d29637b17761364b0b6 |
| BE | hermes_cli/web_routers/sessions.py | cab0bc7ead821615b8596beacbb2db48b78d9cff |
| BE | hermes_state.py | d7dc16a564a598e8be66866e6cb6821a36d285b2 |
| BE | hermes_state_compression.py | b0f42697eadf89cd5033b7caebfde22cd4c4f9f8 |
| BE | hermes_state_history_notifications.py | fff115d5f13630ef3d52452ee21097363513d768 |
| BE | hermes_state_history_sync.py | aa3b152f0b03677bf7f72cfd841d25c79df5fb5f |
| BE | hermes_state_message_provenance.py | dd0d19f79b0b58765c0f8c29d9aa272786b88811 |
| BE | hermes_state_messages.py | bf91398be3ce274f85d73d909c560774167f7d0e |
| BE | hermes_state_recovery_view.py | 486eb238d3590cacd497167129faca548062c554 |
| BE | hermes_state_rewind.py | a35be4f86b9bcc5ddced59d336fbd2554b3ae969 |
| BE | hermes_state_schema.py | de722c54d3c6e414d5d51b32b76439e9c5faaab8 |
| BE | hermes_state_secretary_foreground.py | 0c56b4f27817e7a39e636ccbc6c53c18bae410a4 |
| BE | hermes_state_secretary_identity.py | 2d5556f62dc78aeb9297deb422e2b76649b4a7e2 |
| BE | hermes_state_secretary_noting.py | f846f33e0e9b86385d77f9c5fca7c29fb5ea848e |
| BE | hermes_state_timeline.py | a305cd03e5fb7e4541cee07abaf0ceb88299bc63 |
| BE | hermes_state_turn_terminal.py | 4406011a82799a6a9c904a541e10043fd52580c4 |
| BE | hermes_state_wal.py | eb8b39e43db43ae676cfad7cdb4bef2b5bc9e385 |
| BE | run_agent.py | 088d601b6230bad463e7e7324a92ff4ccb016d14 |
| BE | secretary/framework_messages.py | d9d268e835e021b977ea1f090337dce576c8f35a |
| BE | secretary/heartbeat.py | 0a6d3849bc442fc13300784098da477c438d0d8d |
| BE | secretary/heartbeat_route.py | 0a484ce762a82721c7a8659259c30e61392f3dcf |
| BE | secretary/noting_child.py | 09ac2fec74223c73dc1df47c9d14f945fd8655aa |
| BE | secretary/noting_compact.py | 14e6330bdc85a5207fc8718c078a76e176afcc91 |
| BE | secretary/noting_hosts.py | 4c693871a324d621f3e53d57c493400856087f4a |
| BE | secretary/noting_runtime.py | 040c9127d5f2c48851f62edcbc05567a5d81b0f9 |
| BE | secretary/noting_scope.py | ea1b674a5889b45de16c88c673b811c5b01805ca |
| BE | secretary/noting_task_lifecycle.py | d31c7425e246c6b8ff3486d0d2ef7c6d0e70c70a |
| BE | secretary/noting_timers.py | 1783a6ad72b1c40d98e7530d4e31c9ff6e1d6f85 |
| BE | secretary/reminder_request.py | 529ac3395941be434fe9849bdba8dd0cf1037c8c |
| BE | secretary/reminders.py | 8a464c8d08388044a5c2659fd54bc047db650890 |
| BE | tests/agent/test_turn_source_persistence.py | 12d66718a6997ac6625410b46191bb9d01874fa0 |
| BE | tests/gateway/test_weixin_message_delivery.py | c8efb0e1a802951f6605122663ca8be1e2ec4ba1 |
| BE | tests/gateway/test_weixin_slash_refusal.py | e0470937fc3463b5bb03037a939164fad852649d |
| BE | tests/hermes_cli/test_history_sync.py | 13ef00eea56c0abe006c840bd236c72300070124 |
| BE | tests/hermes_cli/test_recovery_view.py | 9e3a1b866e0c9b37f11d480fd5363c6cea876fcf |
| BE | tests/hermes_state/test_unaddressed_rewrite_identity.py | e7e0e320bb6c844e4c5d6eb27dfe4bf5aa1026c9 |
| BE | tests/secretary/test_idle_noting_reuse.py | 772aff55e40b48e99a09467b749a0561dbafe797 |
| BE | tests/secretary/test_noting_runtime.py | e561a05eabcfe486bd7ce9591e488a7dd7385d59 |
| BE | tests/secretary/test_noting_timers.py | 4977f1be8d6bc723846452f28d96cc507bc301fc |
| BE | tests/tui_gateway/test_cold_noting_resume.py | be9d4c4abb6044a6549b5aa0afc680d035985d05 |
| BE | tests/tui_gateway/test_history_sync.py | 931af1ac135dc7fe5f02e76736fad0e621904325 |
| BE | tests/tui_gateway/test_idle_noting_owner.py | b4472c002c23a1e261ca231029667cd8123fd1fd |
| BE | tests/tui_gateway/test_manual_compress_recovery.py | 21a53311168972e61b4588de28e25ba97eacd267 |
| BE | tests/tui_gateway/test_recovery_view.py | b21ddaff93c59d77aa761fda96e29963c22724e1 |
| BE | tests/tui_gateway/test_tui_gateway_event_replay.py | cdcb09eac80574c4b06bcffe31cfbbf74e215028 |
| BE | tui_gateway/AGENTS.md | e56a4245e596bbf8a193a3aa8ef9ad225dea04e5 |
| BE | tui_gateway/change_watcher.py | c42f4a228c2215e0f41aaaf299021ac91538915b |
| BE | tui_gateway/contracts/sessions.py | d541460834be2f6dadca8de94d2d9aa3dbb43c2b |
| BE | tui_gateway/event_replay.py | 38e34d52f7c8a9cf2f02ba4eaf07c485deb7cfc9 |
| BE | tui_gateway/inflight_output.py | f19f609f2643649e4e34e066eee43b9e5ac93294 |
| BE | tui_gateway/methods_session.py | 2a8af8d297029174873b2d644c96d3b17590dc48 |
| BE | tui_gateway/output_identity.py | f1df2397acbd1abe3430665fef4032e1f09a4b17 |
| BE | tui_gateway/recovery_view.py | 93ee8ef00b07bb6f407e7f5e619bb93fea17eb2d |
| BE | tui_gateway/server.py | 6491cc5f0724ea25d53c814ff9119be39a852710 |
| BE | tui_gateway/session_lifecycle.py | c04cf0c7d3c1db5310959a8b29ec1b68727d0457 |
| BE | tui_gateway/session_notifications.py | 30749a06ed9ea051e3376d66d09f2babcf0577ea |
| BE | tui_gateway/session_reaper.py | 1d6c73a601563ad4e32c13b8b6bacabb6f0b7f0e |
| BE | tui_gateway/transport.py | 689f5614299c77f3f6a4c779176938b537a8cb4d |
| FE | AGENTS.md | 708f40eb120682607cd61de0d30a33b550a0447f |
| FE | package.json | 0698cbd38c1cc33def0797b922dbb5028ed1cd0c |
| FE | src/App.tsx | 9e57a2d7f43caa863153c712847b66156fcdf53a |
| FE | src/api/android-health.ts | b624600f8cf768f36eab568a2c8b233bbbe12c3f |
| FE | src/api/client.test.ts | 9321e177cc3b544d0e2c2dc65d4845a4a458d864 |
| FE | src/api/client.ts | 42705d0976c52d76e3c583d6e3dd4963e4b38db3 |
| FE | src/api/http-auth.ts | 66497f27e61696058c7d750d3f9fbea0e7a1e44a |
| FE | src/api/reads.ts | 2af01d41a58732ede016a4f963fe341221a75caa |
| FE | src/api/sessions.ts | 80c4f2763fa34770a05470ea141d3db1d83dd99d |
| FE | src/api/types.ts | 61f52c35a5241b9bd74b5ba72e11ddc8ffc2fb3f |
| FE | src/components/ChatComposer.tsx | f6ce00a4e17c400af73c029adfb1f4c67857f6d1 |
| FE | src/components/ChatSelectors.tsx | ad69c5f2758cae4d42b29f187ec40e952042aa67 |
| FE | src/components/Files.tsx | 67ba55d2c6b66ea242bc5001365b1b5a028b051f |
| FE | src/components/HistoryImage.tsx | 37bfb14e7562bfa8792eb08b3d4d82fab45acdff |
| FE | src/components/RecoveryIndicator.tsx | 6d82556c20158f2c573b9b897f86ccf829853af3 |
| FE | src/components/Timeline.tsx | 7621aa6ec382aeba192f14a8e89f98e8148cd587 |
| FE | src/components/android-reply-focus.ts | 42f9932d26a42864c897b6ca80a979028c652294 |
| FE | src/components/chat-presentation.tsx | 61e24fb1bf64f8d177ed6131255e205b2ba1cc62 |
| FE | src/components/files-profile.test.tsx | 44ee4ae43aa2dd461d65a1931ed49119b043acfd |
| FE | src/components/history-image-recovery.ts | a8f1f471932af75592e810c9920da31e0363fde4 |
| FE | src/components/presentation-signature.ts | af037758dc6c7c2290dda9ce0a9e9258919fa8f8 |
| FE | src/components/thinking-expansion.tsx | ed0b19b1d70586316b0b89b865bb9a8f3800d748 |
| FE | src/core/command-actions.ts | 5fcd729ad28aeb253aebbb435e20696210c06178 |
| FE | src/core/commands.ts | ee213d445ee128c7287e38255adaf7cbe8ed2c47 |
| FE | src/core/compaction-read.ts | 4b945acfa6eaaeede30cecdecbe2e1d34c6d9286 |
| FE | src/core/compaction-view.ts | e199427269af0b55ca164071f5407c7f85f3b3bf |
| FE | src/core/context-after-compaction.ts | b0cd278c0cb0590932536af6a4d3455283e5313e |
| FE | src/core/controller-context-compaction.test.ts | bddbbbdfba7596ae709f3f19bfe919f92909c420 |
| FE | src/core/controller-event-effects.ts | 82b0af2367867e9b2d16ba3383b0d932ac35e8fd |
| FE | src/core/controller-incremental-sync.test.ts | 4271dd38adcfd8f8e54a37c34001d268bcfdb806 |
| FE | src/core/controller-notebook-order.test.ts | 62379b0863bb5603d6a3b64107b020dc812abe55 |
| FE | src/core/controller-page-recovery.test.ts | 77ccb823de5de5c85ef7d2f431e35a9eabc52a84 |
| FE | src/core/controller-page-recovery.ts | 4ca6c1134f8ff6b9fc506edfde9a5339cce2dfb5 |
| FE | src/core/controller-pending.ts | 63a824f3b50a106a801121341202a91957d36306 |
| FE | src/core/controller-session-metadata.test.ts | c9c097556f02209c3b251ed3093b862d3b4c8651 |
| FE | src/core/controller-slow-history.test.ts | 0e5263c2aab8b44d325cbbdc7308c8a6e5d63dbc |
| FE | src/core/controller.ts | 4f4bbba72c855eb99add5e76cdb88f3e5b005915 |
| FE | src/core/display-cache.test.ts | 323dd602bc7def20dc1c4043dad8d9367e1ad68b |
| FE | src/core/display-cache.ts | b1267434b1cba82c5527a91b74659e5d0a6e37b9 |
| FE | src/core/history-coverage.test.ts | dee3121bcc5f0d8826f3b851c84dabe43b7aef81 |
| FE | src/core/history-coverage.ts | c98cac256b9bf13f7f4b38dddb807de1084cefc8 |
| FE | src/core/history-details.ts | d0e25724b9a7148b84c6eacc2a682a2d4b6a48a3 |
| FE | src/core/history-sync.fixtures.ts | 81cec8d2d8cde8489a804b7926850dd77a292f58 |
| FE | src/core/history-sync.test.ts | d29868f1cc2e0e4e54b0da8bec47a53963ffcdcb |
| FE | src/core/history-sync.ts | bc1e2c0c1583b6dc03581af396c923b174187523 |
| FE | src/core/history-thinking-prefix.ts | bfe7545f7e0a2507e87882f471ea884c19107497 |
| FE | src/core/native-compaction.ts | 97c80f588be32e0c2343676b3e5d2efa3e4935e1 |
| FE | src/core/native-output.ts | a9b9e163c2ebc3c34230984bc33d1ab41db1d63d |
| FE | src/core/page-recovery-availability.test.ts | aff9ee834579a4d80066e52f383988deb7f19494 |
| FE | src/core/page-recovery.ts | 086dc08e085f3925fa357457d9bc3be2445fc098 |
| FE | src/core/profiles.ts | dc8096734a211654f9495afea23303ea1a06328b |
| FE | src/core/projection.ts | e0cb8a37f4d65cfdd74b66d104d7a60e5aa83267 |
| FE | src/core/recovery-demand.ts | 8318286898757c66cb055b8e1630fa88e4770244 |
| FE | src/core/recovery-resources.ts | b11fa7e8af2997966e17200e9d5226b9355e2bae |
| FE | src/core/secretary-completion.ts | 7750301e25e7ff2455e349f925506976e742cd16 |
| FE | src/core/server-requests.ts | 946f1059e0bdd519387c00a57dda170de59f0c0e |
| FE | src/core/session-list.ts | 19d98730b198075b195fd89bda6f6b96d9cb38ce |
| FE | src/core/session-recovery.ts | c3074e8c65982fa21d812e29760398c9a14ad6fe |
| FE | src/core/terminal-history.ts | 576a0a7e18a5137209952e13bf26a35608c12c69 |
| FE | src/core/usage-counters.ts | 139521c97485ab9a8ef949ea1914d3443d03e624 |
| FE | src/core/usage-view.ts | 5415e79f056bb7cfc47ed7f639b660c85c7e69e0 |
| FE | src/design/ambient-backdrop.test.tsx | 1c85ed8a9c190044c828efd496c883b23a96c127 |
| FE | src/design/ambient-backdrop.tsx | df2b6e621486b623d34df8e352aa33c87c17e244 |
| FE | src/design/chat.tsx | 5f7e9974c8ec96248d4e38f45596d553b9a0c37a |
| FE | src/design/index.ts | 484b26b5edc2135a81a5b2893a06aa13c7f1bbbc |
| FE | src/design/indicators.tsx | e1520c48a24133a200b255bd1d838cee858b93d9 |
| FE | src/design/layout.tsx | 823152f04788a3242fd48b5328dfccfdce90053f |
| FE | src/design/theme.css | 5c7b6190672f9cf4d4adbd2a0b5a7c4ed63e3260 |
| FE | src/design/toasts.tsx | 5687eead3af41b6563343d0db914d427546d6afd |
| FE | src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/AndroidBridgeState.kt | 23c771c82d776e462cebdc88d74b05a0331bcdce |
| FE | src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/AndroidRunCoordinator.kt | 37ff030f06f5b291cca57b8b1593eaed246e8c7e |
| FE | src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/AndroidViewport.kt | 4a5f168e6ea051a258f95e6bd389f52b12120421 |
| FE | src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/ForegroundRefresh.kt | 664b8a6f4bcdbac5cdc8ab19a61f147f886fbe89 |
| FE | src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/HermesNotifications.kt | 7d6c1cfbc2c2828f771f2b3a10c1505c207fe0a4 |
| FE | src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/MainActivity.kt | 510abbf6ac23d2a12fb1c5da660afdf7a2564f54 |
| FE | src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/PackagedWebViewClient.kt | f2c53bacc72f3320789618cc0a656212fdf9598e |
| FE | src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/SystemBarTheme.kt | 9fc4a28a864f64c821c798a86dafac44bfa8bd48 |
| FE | src-tauri/gen/android/app/src/test/java/com/edgarzhong/hermessecretary/AndroidBridgeStateTest.kt | 90ceb9144671a5b69618a8b35431ba77bc8235e5 |
| FE | src-tauri/gen/android/app/src/test/java/com/edgarzhong/hermessecretary/AndroidViewportTest.kt | 2ee20ca24734458e2ed6ccacbb016ffbbf13a948 |
| FE | src-tauri/gen/android/app/src/test/java/com/edgarzhong/hermessecretary/ForegroundRefreshTest.kt | e39ff59da46eec6371cc2d9270d6b6fb74b4635e |
| FE | src-tauri/gen/android/app/src/test/java/com/edgarzhong/hermessecretary/HermesNotificationsTest.kt | 971c5efe58b89615b5b0ec46f34ca4b5b13bdc80 |

### 6.4 本轮隔离反例的实际输出

所有ID、正文、owner均为合成数据。前端直接执行固定源码方法，移除TypeScript类型并显式提供依赖；未运行App构造器/真实浏览器。Python只编译提取的真实AST纯分支，无应用导入、DB、模型或网络。下列JSON为本轮实际产物，不是建议性预期输出。


#### frontend_counterexamples.json

```json
{
  "method": "Original fixed-SHA methods evaluated as isolated logic; HTTP is deferred in-memory; no product/browser/server/model run.",
  "frontendCommit": "91ad72f3898be4e6d98461f69566a76b54595290",
  "sourceSha256": {
    "src/api/types.ts": "c8dc6f8d043fd8a15e927aae091ad0fb5372d4f89bdad456ec155fc09db193a1",
    "src/core/history-sync.ts": "300ec3bbec108264fcfbb6a03d8055a56d20402bd4b60b225de95525f639b9e3",
    "src/core/history-coverage.ts": "48f7549958e145f02ab4c48dd73c7b2f3e7e9d68dab30e9fbdd99c352df9265d",
    "src/core/history-thinking-prefix.ts": "fd8f3dc133d3b831c2a1c48a9aec75ff6cf58e71cb75a5e21e9e12380d24ac99",
    "src/core/display-cache.ts": "51451fef40b06f0e7e45517f7948236a0ba9807a1cf0375b8d1b8e03fd59b35d",
    "src/core/recovery-demand.ts": "cd9a8b49a69e7800c2a90ef3fcd9ace49fcc849e0f697acec22e50c869ac505a",
    "src/core/page-recovery.ts": "a0778792670667249e58605e6aa7f8fa759bcc342d2430a8e0500fdfbc10fd4e",
    "src/core/projection.ts": "e5db7130680095f7e57ed83fad7cb4d7ee5302083a1a3f764bd01f74549f6c29",
    "src/core/history-sync.fixtures.ts": "d4c9ab548a28bab70e7e78d01f4d739e79f6ae3ef075a44db59ba1fe45bea5d1",
    "src/api/http-auth.ts": "b645092c5d1e86af44cdbe07c38048359c7e828b646db1ad98af1badfda59099",
    "src/api/client.ts": "a5372d24d95f7fcf95c5ff3d8227f8ea156df12a454bbf9d1a9c9b4b3657431b",
    "src/core/controller-page-recovery.ts": "721a2f0cbf561bc20a5a572d206df1e02e565cc80beb5fd9b1cd25923e7beae3",
    "src/core/controller.ts": "3f9228c5c3e45125e1ef81a43c09f10bfa8c2660bc5d1b5e91507c0e71cfb783"
  },
  "results": {
    "latePaginationAfterDisconnect": {
      "afterCancellation": {
        "phase": "cancelled",
        "recoveryId": 7,
        "rowCount": 200,
        "firstRows": [
          2,
          3,
          4
        ],
        "displayAuthorized": null,
        "requestAborted": false
      },
      "afterResponse": {
        "phase": "cancelled",
        "recoveryId": 7,
        "rowCount": 201,
        "firstRows": [
          1,
          2,
          3
        ],
        "firstContent": "body1",
        "displayAuthorized": null,
        "cacheAuthorized": true
      }
    },
    "latePaginationAfterAuthenticationFailure": {
      "afterCancellation": {
        "phase": "cancelled",
        "recoveryId": 7,
        "rowCount": 0,
        "firstRows": [],
        "displayAuthorized": false,
        "requestAborted": false
      },
      "afterResponse": {
        "phase": "cancelled",
        "recoveryId": 7,
        "rowCount": 201,
        "firstRows": [
          1,
          2,
          3
        ],
        "firstContent": "body1",
        "displayAuthorized": false,
        "cacheAuthorized": false
      }
    },
    "retiredCachedAnchorRetriesUnchanged": {
      "calls": [
        {
          "method": "session.activate",
          "selectors": [
            {
              "kind": "anchor",
              "anchor_uid": "m201",
              "before": 100,
              "after": 99
            },
            {
              "kind": "latest",
              "limit": 200
            }
          ]
        },
        {
          "method": "session.activate",
          "selectors": [
            {
              "kind": "anchor",
              "anchor_uid": "m201",
              "before": 100,
              "after": 99
            },
            {
              "kind": "latest",
              "limit": 200
            }
          ]
        }
      ],
      "errors": [
        "Error: Recovery unavailable: anchor_not_found",
        "Error: Recovery unavailable: anchor_not_found"
      ],
      "restCalls": 0,
      "cachedAnchorStillAvailable": true,
      "liveStatus": "unknown",
      "boundary": "Two consecutive original readConversation calls simulate scheduled retry; actual timer, DOM and backend are not run."
    },
    "sameRevisionFullDetailOverwrittenByThinkingFacet": {
      "before": {
        "id": 200,
        "row_id": 200,
        "message_uid": "m200",
        "role": "assistant",
        "content": "body200",
        "detail_revision": "r200",
        "reasoning": "known full thinking",
        "deferred_details": [],
        "tool_calls": [
          {
            "id": "call",
            "function": {
              "name": "lookup",
              "arguments": "known full arguments"
            }
          }
        ]
      },
      "retained": {
        "id": 200,
        "row_id": 200,
        "message_uid": "m200",
        "role": "assistant",
        "reasoning": "known full thinking",
        "detail_revision": "r200",
        "deferred_details": [
          "tool_arguments",
          "tool_result",
          "terminal_outputs"
        ]
      },
      "reopened": {
        "id": 200,
        "row_id": 200,
        "message_uid": "m200",
        "role": "assistant",
        "content": "body200",
        "deferred_details": [
          "tool_arguments"
        ],
        "detail_revision": "r200",
        "reasoning": "known full thinking"
      }
    },
    "prefixWith500RealMessages": {
      "realMessages": 500,
      "windowSizes": [
        200,
        200
      ],
      "detailRecords": 100,
      "validPrefix": true,
      "persistedPrefixAccepted": false,
      "afterOneOldDetailEvicted": {
        "persistedPrefixAccepted": true
      }
    }
  }
}
```


#### backend_append_predicate_probe.json

```json
{
  "scope": "Pure _same_history predicate only; no end-to-end or UI execution",
  "source": "repos/hermes-secretary/tui_gateway/recovery_view.py",
  "source_blob_sha1": "93ee8ef00b07bb6f407e7f5e619bb93fea17eb2d",
  "source_lines": [
    253,
    263
  ],
  "scenario": "Same owner, source, lineage, old order/cards/details; only one new Thinking row appended after D0",
  "legacy_without_sync_latest_thinking_accepts": true,
  "sync_v1_with_latest_thinking_append_accepts": false,
  "d0": {
    "tip_id": "same-tip",
    "lineage": [
      "same-tip"
    ],
    "rewind": [
      [
        "same-tip",
        0
      ]
    ],
    "detail_digest": "no-expanded-details",
    "windows": [
      {
        "coverage": {
          "digest": "unchanged-cards-and-identities",
          "window": {
            "first": {
              "logical_order": 1
            },
            "returned": 2
          }
        },
        "detail_revisions": {
          "1": "source-revision",
          "2": "thinking-two-revision"
        }
      }
    ],
    "latest_thinking": {
      "source": {
        "row_id": 1,
        "message_uid": "native-source",
        "session_id": "same-tip"
      },
      "order": [
        2
      ],
      "rows": [
        {
          "id": 2,
          "message_uid": "assistant-two",
          "role": "assistant",
          "reasoning": "already committed thought"
        }
      ],
      "positions": {
        "2": 1
      },
      "revisions": {
        "2": "thinking-two-revision"
      }
    }
  },
  "d1": {
    "tip_id": "same-tip",
    "lineage": [
      "same-tip"
    ],
    "rewind": [
      [
        "same-tip",
        0
      ]
    ],
    "detail_digest": "no-expanded-details",
    "windows": [
      {
        "coverage": {
          "digest": "cards-with-appended-third-row",
          "window": {
            "first": {
              "logical_order": 1
            },
            "returned": 3
          }
        },
        "detail_revisions": {
          "1": "source-revision",
          "2": "thinking-two-revision",
          "3": "thinking-three-revision"
        }
      },
      {
        "coverage": {
          "digest": "unchanged-cards-and-identities",
          "window": {
            "first": {
              "logical_order": 1
            },
            "returned": 2
          }
        },
        "detail_revisions": {
          "1": "source-revision",
          "2": "thinking-two-revision"
        }
      }
    ],
    "latest_thinking": {
      "source": {
        "row_id": 1,
        "message_uid": "native-source",
        "session_id": "same-tip"
      },
      "order": [
        2,
        3
      ],
      "rows": [
        {
          "id": 2,
          "message_uid": "assistant-two",
          "role": "assistant",
          "reasoning": "already committed thought"
        },
        {
          "id": 3,
          "message_uid": "assistant-three",
          "role": "assistant",
          "reasoning": "newly appended thought"
        }
      ],
      "positions": {
        "2": 1,
        "3": 2
      },
      "revisions": {
        "2": "thinking-two-revision",
        "3": "thinking-three-revision"
      }
    }
  }
}
```


#### lifecycle_logic_probe.json

```json
{
  "backend_ref": "44eb0be4c3a2c7e9f13157740514fd40bd83aa50",
  "scope": "AST-extracted pure branch probes; no production app/DB/adapter/model invocation",
  "source_sha256": {
    "gateway/run_agent_cache.py": "5c2d7b8e18482cd4ce75e6d762543ecb9c3cbb4e7f8dc239fdffc60520e5d2ba",
    "agent/turn_final_response.py": "2e937817af2aa2e710593bfa52c6abdff11299031e4d4435aac7c11865d4579e"
  },
  "observations": [
    {
      "mode": "lru",
      "maintenance_allowed": true,
      "evicted": true,
      "prefix_after": [],
      "owner_epoch_unchanged": true,
      "parent_closed": false,
      "release_jobs": [
        "agent-cache-evict-idle-parent"
      ]
    },
    {
      "mode": "ttl",
      "maintenance_allowed": true,
      "evicted": true,
      "prefix_after": [],
      "owner_epoch_unchanged": true,
      "parent_closed": false,
      "release_jobs": [
        "agent-cache-idle-idle-parent"
      ]
    },
    {
      "mode": "normal-stop-tail",
      "verdict": "break",
      "messages": [
        {
          "role": "assistant",
          "message_uid": "last",
          "content": "complete final"
        }
      ],
      "events": [
        "durable-final-flush"
      ],
      "complete_message_callbacks": []
    }
  ]
}
```


### 6.5 隔离反例源码

下面保留反例原文，便于实现方核查适配边界。它们是Verification的分析材料，不是已加入产品仓库的测试，不代表端到端验证。重现时应把两仓放在`repos/hermes-secretary`、`repos/hermes-still-chat`并固定本报告SHA，将脚本放在同级`review_notes`；前端脚本需要支持`node:module.stripTypeScriptTypes`的Node版本，两个Python脚本仅用标准库。原项目测试未在本轮执行。


#### frontend_counterexamples.cjs

```javascript
/* Read-only Verification logic probes. No app, server, model, browser or network.
 * Execute unchanged methods read from the fixed-SHA snapshot. TypeScript is stripped
 * in memory, imports are supplied explicitly; constructors with application I/O are
 * bypassed. Only unrelated editor/usage/notification effects are inert adapters.
 */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { stripTypeScriptTypes } = require('node:module');
const { createHash } = require('node:crypto');
const root = path.resolve(__dirname, '../repos/hermes-still-chat');
const sources = {};
function moduleFrom(file, names, imports = {}, before = x => x) {
  const raw = fs.readFileSync(path.join(root, file), 'utf8');
  sources[file] = createHash('sha256').update(raw).digest('hex');
  let source = stripTypeScriptTypes(before(raw), { mode: 'transform' });
  source = source.replace(/^import\b[\s\S]*?;\s*$/gm, '')
    .replace(/^export\s*\{[^}]*\}\s*from\s*[^;]+;\s*$/gm, '')
    .replace(/\bexport\s+(?=(?:class|function|const|let|async)\b)/g, '');
  return new Function(...Object.keys(imports), source + '\nreturn {' + names.join(',') + '};')(...Object.values(imports));
}
global.location = { origin: 'https://example.test', href: 'https://example.test/chat/chat', protocol: 'https:' };
global.window = {};
const types = moduleFrom('src/api/types.ts', ['recoverySelectorKey']);
const sync = moduleFrom('src/core/history-sync.ts', ['reconcileSync', 'retainDetails', 'boundedSyncWindows', 'boundedHistoryDetails']);
// Supply the exact selector function to a second load (the first exports below
// do not invoke it until call time).
Object.assign(sync, moduleFrom('src/core/history-sync.ts', Object.keys(sync), types));
const coverage = moduleFrom('src/core/history-coverage.ts', ['HistoryWindows', 'messageIdentity', 'anchorSelector'], { ...types, ...sync });
const thinking = moduleFrom('src/core/history-thinking-prefix.ts', ['snapshotThinking', 'checkedThinkingPrefix']);
const cacheModule = moduleFrom('src/core/display-cache.ts', ['DisplayCache'], { ...coverage, ...sync, ...thinking });
const demand = moduleFrom('src/core/recovery-demand.ts', ['pageOwnerKey']);
const recovery = moduleFrom('src/core/page-recovery.ts', ['PageRecovery'], demand);
const projection = moduleFrom('src/core/projection.ts', ['emptyLive', 'reconcileLiveHistory']);
const fixture = moduleFrom('src/core/history-sync.fixtures.ts', ['page']);
const auth = moduleFrom('src/api/http-auth.ts', ['authenticatedFetch', 'revokeHttpCredentials', 'confirmHttpCredentials']);
const api = moduleFrom('src/api/client.ts', ['RpcError', 'readRecoveryHistory'], { ...types, ...auth });
const adapterModule = moduleFrom('src/core/controller-page-recovery.ts', ['ControllerPageRecovery'], {
  ...demand, ...recovery, ...coverage, ...sync, ...thinking, ...cacheModule, ...projection, ...api, ...auth,
  draftKey: (profile, id) => `${encodeURIComponent(profile)}:${id ?? 'new'}`,
  emptyDraft: () => ({ text: '', attachments: [] }),
});
const control = moduleFrom('src/core/controller.ts', ['Controller'], {
  ...projection,
  draftKey: (profile, id) => `${encodeURIComponent(profile)}:${id ?? 'new'}`,
}, text => text.slice(0, text.indexOf('const hotState =')));
const owner = { serverOrigin: location.origin, profile: 'default', storedId: 'chat', screen: 'conversation' };
const row = (id, extra = {}) => ({ id, row_id: id, message_uid: `m${id}`, role: 'assistant', content: `body${id}`, ...extra });
const results = {};

async function latePagination(mode) {
  const c = Object.create(control.Controller.prototype);
  const initialRows = Array.from({ length: 200 }, (_, i) => row(2 + i));
  let visible;
  Object.assign(c, {
    state: { version: 1, profile: 'default', route: { screen: 'conversation', id: 'chat' }, connection: 'connected',
      binding: { session_id: 'runtime', recovery_view_version: 1 }, history: { messages: initialRows, offset: 200, more: true, loading: false },
      live: projection.emptyLive(), temporary: [], sessions: [], notifications: [], requests: [], pending: [], models: {}, catalog: {} },
    listeners: new Set(), histories: new Map(), lives: new Map(), bindings: new Map(), replaying: new Set(), replayHeld: new Map(),
    secretaryReadSerial: 0, schedulesReadSerial: 0, capabilitySerial: 0, selectedGeneration: 0, metadataRevision: 0,
    gateway: { state: 'connected', stop() { this.state = 'disconnected'; } },
    // Preserve unchanged commitHistoryView and publish; only unrelated domain
    // reconciliation is inert because the scenario contains no live/steer nodes.
    reconcileLiveView(_key, live) { return { live, temporary: [] }; },
    invalidateDisplayReads() {},
    retainedRenderStore: { publish(value) { visible = value; }, getSnapshot() { return visible; } },
  });
  Object.defineProperty(c, 'profileEnvironment', { value: { resolved: true } });
  const page = new recovery.PageRecovery({ owner: () => owner, connected: () => c.gateway.state === 'connected', retain() {},
    reconcile: async () => {}, commit: () => true, documentId: 'probe-document' });
  page.state = { ...page.getSnapshot(), recoveryId: 7, phase: 'committed', readyForDisplay: true };
  const adapter = Object.create(adapterModule.ControllerPageRecovery.prototype);
  const index = new coverage.HistoryWindows();
  const initialPage = fixture.page(initialRows, 'latest', 1, 201);
  initialPage.coverage.window.predecessor = { row_id: 1, message_uid: 'm1', logical_order: 1, position: 0 };
  index.accept(initialPage, 'default', 'chat', 7);
  Object.assign(adapter, { host: c, page, cache: new cacheModule.DisplayCache(), windows: new Map([['default:chat', index]]),
    bindingReads: new Map(), metadataReads: new Map(), warmViews: new Map(), rosterReads: new Map(), conversationReads: new Map(),
    menuStages: new Map(), displayFacts: [], contextObservations: new Map(), heldBytes: new Map(), overflowed: new Set(),
    frozen: false, cacheAuthorized: true, cacheSerial: 0, contextRevision: 0 });
  c.retainedPageRecovery = adapter;
  c.histories.set(c.key(), c.state.history);
  c.publish();
  let finish;
  let requestedSignal;
  global.fetch = (_path, options) => { requestedSignal = options.signal; return new Promise(resolve => { finish = resolve; }); };
  auth.confirmHttpCredentials();
  const pending = adapter.loadEarlier();
  assert.equal(typeof finish, 'function');
  if (mode === 'auth') adapter.authenticationFailure(new api.RpcError('authentication lost', 401));
  else { c.gateway.state = 'disconnected'; adapter.connection('disconnected'); c.publish({ connection: 'disconnected' }); }
  const afterCancellation = { phase: page.getSnapshot().phase, recoveryId: page.getSnapshot().recoveryId,
    rowCount: visible.history.messages.length, firstRows: visible.history.messages.slice(0, 3).map(x => x.id), displayAuthorized: visible.displayAuthorized ?? null,
    requestAborted: requestedSignal.aborted };
  const response = fixture.page([row(1), row(2)], 'earlier', 0, 201);
  response.selector = { kind: 'anchor', anchor_uid: 'm2', before: 200, after: 0 };
  response.coverage.window.successor = { row_id: 3, message_uid: 'm3', logical_order: 3, position: 2 };
  finish(new Response(JSON.stringify(response)));
  await pending;
  const afterResponse = { phase: page.getSnapshot().phase, recoveryId: page.getSnapshot().recoveryId,
    rowCount: visible.history.messages.length, firstRows: visible.history.messages.slice(0, 3).map(x => x.id),
    firstContent: visible.history.messages[0]?.content,
    displayAuthorized: visible.displayAuthorized ?? null, cacheAuthorized: adapter.cacheAuthorized };
  assert.equal(afterResponse.phase, 'cancelled');
  assert.equal(afterResponse.rowCount, 201); assert.deepEqual(afterResponse.firstRows, [1, 2, 3]);
  if (mode === 'auth') assert.equal(afterResponse.displayAuthorized, false);
  return { afterCancellation, afterResponse };
}

async function retiredCachedAnchor() {
  const older = fixture.page(Array.from({ length: 200 }, (_, i) => row(101 + i)), 'old-anchor', 100, 600);
  older.selector = { kind: 'anchor', anchor_uid: 'm201', before: 100, after: 99 };
  const latest = fixture.page(Array.from({ length: 200 }, (_, i) => row(401 + i)), 'old-latest', 400, 600);
  const index = new coverage.HistoryWindows();
  index.accept(older, 'default', 'chat', 1); index.accept(latest, 'default', 'chat', 1);
  const binding = { session_id: 'runtime', recovery_view_version: 1 };
  const calls = [];
  const c = { state: { profile: 'default', route: { screen: 'conversation', id: 'chat' }, binding,
      history: { messages: [...older.messages, ...latest.messages] }, live: projection.emptyLive() },
    key: () => 'default:chat', metadataRevision: 0, bindings: new Map(), replaying: new Set(), lives: new Map(),
    serverRequests: { beginSnapshot: () => ({}), endSnapshot() {} },
    publish(patch) { Object.assign(this.state, patch); },
    gateway: { epoch: 'epoch', async request(method, params) {
      calls.push({ method, selectors: params.recovery_view.windows.map(window => window.selector) });
      // This is the exact failure shape returned by backend activate_payload
      // for a deleted/retired anchor, not an HTTP 404 and not a transport error.
      return { ...binding, recovery_view: { version: 1, owner: { profile: 'default', stored_id: 'chat', runtime_id: 'runtime' },
        epoch: 'epoch', complete: false, reason: 'anchor_not_found' } };
    } },
  };
  const adapter = Object.create(adapterModule.ControllerPageRecovery.prototype);
  Object.assign(adapter, { host: c, windows: new Map([['default:chat', index]]),
    page: { getDemand: () => ({ viewport: { first: 'uid:m201' } }) },
    readCache: async () => {}, bound: async () => binding });
  let restCalls = 0;
  global.fetch = () => { restCalls++; throw new Error('A fresh REST read was unexpectedly attempted'); };
  const errors = [];
  for (const recoveryId of [2, 3]) {
    const context = { owner, recoveryId, signal: new AbortController().signal, current: () => true };
    try { await adapter.readConversation(context); }
    catch (error) { errors.push(String(error)); }
  }
  assert.equal(errors.length, 2); assert.equal(restCalls, 0); assert.deepEqual(calls[0], calls[1]);
  assert.equal(index.loaded().some(window => window.selector.kind === 'anchor'), true);
  return { calls, errors, restCalls, cachedAnchorStillAvailable: true, liveStatus: c.state.live.status,
    boundary: 'Two consecutive original readConversation calls simulate scheduled retry; actual timer, DOM and backend are not run.' };
}

(async () => {
  results.latePaginationAfterDisconnect = await latePagination('disconnect');
  results.latePaginationAfterAuthenticationFailure = await latePagination('auth');
  results.retiredCachedAnchorRetriesUnchanged = await retiredCachedAnchor();

  // A full native message detail has been obtained in an older loaded window;
  // same-version latest Thinking outside the new selected windows is only a facet.
  const index = new coverage.HistoryWindows();
  const full = row(200, { detail_revision: 'r200', reasoning: 'known full thinking', deferred_details: [],
    tool_calls: [{ id: 'call', function: { name: 'lookup', arguments: 'known full arguments' } }] });
  const previous = fixture.page([full], 'old', 199, 600);
  previous.selector = { kind: 'anchor', anchor_uid: 'm200', before: 0, after: 0 };
  index.accept(previous, 'default', 'chat', 1);
  index.cachedDetails([full]);
  index.clear();
  const latest = fixture.page(Array.from({ length: 200 }, (_, i) => row(401 + i)), 'new', 400, 600);
  latest.sync.latest_thinking = { source: { id: 150, row_id: 150, message_uid: 'source', role: 'user' }, order: [200],
    rows: [{ id: 200, row_id: 200, message_uid: 'm200', role: 'assistant', reasoning: 'known full thinking' }],
    positions: { 200: 199 }, revisions: { 200: 'r200' } };
  index.accept(latest, 'default', 'chat', 2);
  const retained = index.cachedDetails().find(item => item.message.id === 200).message;
  const reopen = fixture.page([row(200, { deferred_details: ['reasoning', 'tool_arguments'] })], 'reopen', 199, 600);
  reopen.selector = previous.selector;
  const adopted = index.accept(reopen, 'default', 'chat', 2).messages[0];
  results.sameRevisionFullDetailOverwrittenByThinkingFacet = { before: full, retained, reopened: adopted };
  assert.equal(adopted.tool_calls, undefined);

  const native = projection.emptyLive(); native.active = true;
  native.nativeOutput = { state: 'open', messageUid: 'new-output', turnId: 'turn', conversationRef: 'conv' };
  native.nodes = [{ id: 'thinking', kind: 'thinking', role: 'assistant', text: 'complete prefix at seq 9',
    nativeMessageUid: 'new-output', nativeTurnId: 'turn', nativeConversationRef: 'conv' }];
  const prefix = thinking.snapshotThinking(native, 'epoch', 9);
  const cache = new cacheModule.DisplayCache();
  // Reachable formal cache shape: latest 200 + current anchor 200, with 100
  // complete details previously obtained in older windows, all inside recent 500.
  const anchor200 = fixture.page(Array.from({ length: 200 }, (_, i) => row(101 + i)), 'anchor200', 100, 500);
  anchor200.selector = { kind: 'anchor', anchor_uid: 'm201', before: 100, after: 99 };
  const latest200 = fixture.page(Array.from({ length: 200 }, (_, i) => row(301 + i)), 'latest200', 300, 500);
  const details100 = Array.from({ length: 100 }, (_, i) => ({ position: i, total: 500,
    message: row(i + 1, { detail_revision: `r${i + 1}`, reasoning: 'previously obtained complete Thinking', deferred_details: [] }) }));
  const cacheIndex = new coverage.HistoryWindows();
  cacheIndex.restoreDetails(details100);
  cacheIndex.accept(anchor200, 'default', 'chat', 8); cacheIndex.accept(latest200, 'default', 'chat', 8);
  const pages = cacheIndex.loaded().map(window => cacheIndex.page(window));
  const details = cacheIndex.cachedDetails();
  cache.putConversation(owner, { sync: pages, details, prefix });
  const stored = cache.peekConversation(owner);
  const realIdentities = new Set([...stored.sync.flatMap(page => page.messages), ...stored.details.map(detail => detail.message)].map(row => row.message_uid));
  results.prefixWith500RealMessages = { realMessages: realIdentities.size, windowSizes: stored.sync.map(page => page.messages.length),
    detailRecords: stored.details.length, validPrefix: !!prefix, persistedPrefixAccepted: !!stored.prefix };
  assert.equal(realIdentities.size, 500); assert.equal(stored.details.length, 100);
  assert.equal(results.prefixWith500RealMessages.persistedPrefixAccepted, false);
  cache.putConversation(owner, { sync: pages, details: details.slice(0, 99), prefix });
  results.prefixWith500RealMessages.afterOneOldDetailEvicted = { persistedPrefixAccepted: !!cache.peekConversation(owner).prefix };
  assert.equal(results.prefixWith500RealMessages.afterOneOldDetailEvicted.persistedPrefixAccepted, true);
  cache.cancelPending();
  const output = { method: 'Original fixed-SHA methods evaluated as isolated logic; HTTP is deferred in-memory; no product/browser/server/model run.',
    frontendCommit: '91ad72f3898be4e6d98461f69566a76b54595290', sourceSha256: sources, results };
  fs.writeFileSync(path.join(__dirname, 'frontend_counterexamples.json'), JSON.stringify(output, null, 2) + '\n');
  console.log(JSON.stringify(results, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });
```


#### backend_append_predicate_probe.py

```python
"""Isolated predicate probe: execute only _same_history extracted from reviewed source.
No application import, database, network, model, production process, or test suite.
"""
from pathlib import Path
import ast
import copy
import hashlib
import json

source = Path('repos/hermes-secretary/tui_gateway/recovery_view.py')
raw = source.read_bytes()
module = ast.parse(raw.decode())
node = next(item for item in module.body if isinstance(item, ast.FunctionDef) and item.name == '_same_history')
namespace = {}
exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), namespace)
check = namespace['_same_history']

original = {
    'coverage': {'digest': 'unchanged-cards-and-identities', 'window': {'first': {'logical_order': 1}, 'returned': 2}},
    'detail_revisions': {'1': 'source-revision', '2': 'thinking-two-revision'},
}
new_window = {
    'coverage': {'digest': 'cards-with-appended-third-row', 'window': {'first': {'logical_order': 1}, 'returned': 3}},
    'detail_revisions': {'1': 'source-revision', '2': 'thinking-two-revision', '3': 'thinking-three-revision'},
}
common = {'tip_id': 'same-tip', 'lineage': ['same-tip'], 'rewind': [('same-tip', 0)], 'detail_digest': 'no-expanded-details'}
d0 = {**copy.deepcopy(common), 'windows': [copy.deepcopy(original)]}
d1 = {**copy.deepcopy(common), 'windows': [copy.deepcopy(new_window), copy.deepcopy(original)]}
legacy = check(d0, d1, 1)
source_identity = {'row_id': 1, 'message_uid': 'native-source', 'session_id': 'same-tip'}
row2 = {'id': 2, 'message_uid': 'assistant-two', 'role': 'assistant', 'reasoning': 'already committed thought'}
row3 = {'id': 3, 'message_uid': 'assistant-three', 'role': 'assistant', 'reasoning': 'newly appended thought'}
d0['latest_thinking'] = {'source': source_identity, 'order': [2], 'rows': [row2], 'positions': {'2': 1}, 'revisions': {'2': 'thinking-two-revision'}}
d1['latest_thinking'] = {'source': source_identity, 'order': [2, 3], 'rows': [row2, row3], 'positions': {'2': 1, '3': 2}, 'revisions': {'2': 'thinking-two-revision', '3': 'thinking-three-revision'}}
opt_in = check(d0, d1, 1)
result = {
    'scope': 'Pure _same_history predicate only; no end-to-end or UI execution',
    'source': str(source),
    'source_blob_sha1': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(),
    'source_lines': [node.lineno, node.end_lineno],
    'scenario': 'Same owner, source, lineage, old order/cards/details; only one new Thinking row appended after D0',
    'legacy_without_sync_latest_thinking_accepts': legacy,
    'sync_v1_with_latest_thinking_append_accepts': opt_in,
    'd0': d0,
    'd1': d1,
}
Path('review_notes/backend_append_predicate_probe.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key not in ('d0', 'd1')}, ensure_ascii=False, indent=2))
```


#### lifecycle_logic_probe.py

```python
"""Read-only branch probes; AST-extract fixed-source functions, no project import/network/DB.

Fixtures model an idle Main whose exact maintenance qualification is already true.
This is not a production integration test; the report independently traces that wiring.
"""
import ast
import contextlib
import hashlib
import json
import logging
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / 'repos/hermes-secretary'


def source_tree(path):
    return ast.parse((BACK / path).read_text(), filename=path)


cache_tree = source_tree('gateway/run_agent_cache.py')
original = next(n for n in cache_tree.body if isinstance(n, ast.ClassDef) and n.name == 'GatewayAgentCacheMixin')
names = {'_enforce_agent_cache_cap', '_sweep_idle_cached_agents', '_commit_then_release_soft', '_release_evicted_agent_soft'}
members = [n for n in original.body if isinstance(n, ast.FunctionDef) and n.name in names]
helper = next(n for n in cache_tree.body if isinstance(n, ast.FunctionDef) and n.name == '_tuple_agent')
cls = ast.ClassDef(name='CacheProbe', bases=[], keywords=[], body=members, decorator_list=[])
env = dict(Any=Any, List=List, logger=logging.getLogger('probe'), suppress=contextlib.suppress,
           time=SimpleNamespace(time=lambda: 100.0))
exec(compile(ast.fix_missing_locations(ast.Module(body=[helper, cls], type_ignores=[])), '<fixed-source-extract>', 'exec'), env)
CacheProbe = env['CacheProbe']


class Fixture(CacheProbe):
    def _running_agent_ids(self): return set()
    def _agent_cache_cap(self): return 1
    def _agent_cache_idle_ttl(self): return 10.0
    def _commit_memory_before_soft_evict(self, agent, key): pass
    def _spawn_release_thread(self, callback, args, name, **kwargs):
        self.release_jobs.append(name)
        callback(*args)  # deterministic stand-in for daemon scheduling, not the worker implementation


def parent():
    result = SimpleNamespace(_last_activity_ts=0.0, _session_messages=[{'role':'assistant', 'message_uid':'m1', 'content':'body'}],
                             _db_flush_scan_prefix=['prefix'], _secretary_maintenance_allowed=True,
                             _secretary_parent_closed=False, _native_compaction_owner=object(), releases=0)
    result.release_clients = lambda: setattr(result, 'releases', result.releases + 1)
    return result


records = []
for mode in ('lru', 'ttl'):
    p, fresh = parent(), parent()
    fresh._last_activity_ts = 100.0
    epoch = p._native_compaction_owner
    f = Fixture()
    f.release_jobs = []
    f._agent_cache_lock = contextlib.nullcontext()
    f._agent_cache = OrderedDict([('idle-parent', (p, 'sig', 1, 'sid')), ('fresh', (fresh, 'sig', 1, 'sid2'))])
    f._enforce_agent_cache_cap() if mode == 'lru' else f._sweep_idle_cached_agents()
    observation = dict(mode=mode, maintenance_allowed=p._secretary_maintenance_allowed,
                       evicted='idle-parent' not in f._agent_cache, prefix_after=p._session_messages,
                       owner_epoch_unchanged=p._native_compaction_owner is epoch,
                       parent_closed=p._secretary_parent_closed, release_jobs=f.release_jobs)
    assert observation['evicted'] and observation['prefix_after'] == []
    assert observation['owner_epoch_unchanged'] and not observation['parent_closed']
    records.append(observation)

# Normal stop tail, copied verbatim as AST statements after the output-transform branch.
final_tree = source_tree('agent/turn_final_response.py')
final_function = next(n for n in final_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'finish_text_response')
tail = [n for n in final_function.body if n.lineno >= 360]
fn = ast.FunctionDef(name='normal_stop_tail', args=ast.arguments(posonlyargs=[], args=[ast.arg(arg=n) for n in
    ['agent', 'messages', 'final_msg', 'conversation_history', 'finish_reason', 'api_call_count']],
    vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]), body=tail, decorator_list=[])
sent, events = [], []
agent = SimpleNamespace(quiet_mode=True, _emit_interim_assistant_message=lambda m: sent.append(m),
                        _flush_messages_to_session_db=lambda *_: events.append('durable-final-flush'))
scope = dict(append_message=lambda rows, m: rows.append(m), logger=logging.getLogger('probe'), _verdict=lambda action: action)
exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), '<fixed-stop-tail>', 'exec'), scope)
message = {'role':'assistant', 'message_uid':'last', 'content':'complete final'}
rows = []
verdict = scope['normal_stop_tail'](agent, rows, message, [], 'stop', 1)
assert verdict == 'break' and rows == [message] and sent == []
records.append(dict(mode='normal-stop-tail', verdict=verdict, messages=rows, events=events, complete_message_callbacks=sent))

result = dict(backend_ref='44eb0be4c3a2c7e9f13157740514fd40bd83aa50',
              scope='AST-extracted pure branch probes; no production app/DB/adapter/model invocation',
              source_sha256={p:hashlib.sha256((BACK/p).read_bytes()).hexdigest() for p in
                ['gateway/run_agent_cache.py','agent/turn_final_response.py']}, observations=records)
print(json.dumps(result, ensure_ascii=False, indent=2))
```


### 6.6 门禁登记

**Verification：不通过；待修复F01–F08并补齐E01–E03对应证据后独立复审。Validation：本报告未执行、未代签，由用户已安排的流程另行记录。部署：本次未执行。**
