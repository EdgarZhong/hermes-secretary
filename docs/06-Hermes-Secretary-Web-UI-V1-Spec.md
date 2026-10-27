# Hermes Secretary Web UI V1 — Product, Native Interface & Implementation Specification

## 2026-10-27 · 客户端缓存、增量同步与表现层契约

本节是本轮设计与后续验收的对照表，稳定编号用于区分设计遗漏和编码偏离。实施／验证状态只在CLAUDE及本轮报告中记录。本节优先于下文旧轮次“不以缓存减少请求／每次完整传输／不存详情／APK五秒强制重载”的冲突描述，其余产品语义保持；不得以旧技术实现反向否决本节。用户要求先查清恢复慢的原因，在main修独立问题，再在前后端同名分支实施，跳过Ask and Align；main独立修复豁免严格双门禁，新机制完成后完整Verification与Validation。主会话设计、集成、验收审查；子Agent6.1 sol只按方案实施。

### C0 · 术语、归属与容量

- **展示缓存**仅提供连续画面，不证明连接、运行状态、审批权限或写入成功。**同步缓存**是完整数据与其服务端游标／版本的原子配对，只能向服务端提出增量请求，不能自行宣布已恢复。
- 所有Conversation缓存以canonical server origin＋真实Profile＋稳定Conversation／路由归属隔离；runtime、epoch、连接轮次只用于当前有效性判定。切owner不能借用旧owner展示、详情或游标。认证失败立即撤销展示和动作资格，失效正在进行的读写缓存任务。
- **Timeline每Conversation最多缓存最近500条真实消息，按后端逻辑顺序和消息身份计数**，不按卡片数、工具组数、Thinking段数计数。已请求／完整收到的详情附着原消息，不另计名额。重复窗口同UID只占一条；原消息淘汰时连同详情、相关版本一起淘汰。默认首屏仍200条，Show More仍原分页；不为填满缓存预读500条。用户正在阅读的更早分页属于当前页面展示数据，仍可按需请求，不写入超过最近500条的可复用缓存。
- 已完整取得的Thinking／工具参数／结果不因收起UI而丢弃；“不折叠掉数据”不改变原视觉折叠规则。尚未展开、未取得的旧详情继续懒请求。请求中断、缺片或仅收到部分的旧详情不写持久缓存；不能把部分内容标记为完整。
- 最新Turn的Thinking是主动同步例外：每次当前Conversation的历史同步／恢复都取得其最近500条消息缓存范围内的详情，包括运行中截至本次有限切点的完整前缀，并更新缓存。普通图片下载、侧栏、Files或无关RPC不额外触发Thinking读取。收到的后续流式片段先沿原生事件在内存显示；只有完整快照确认的前缀或明确完整的消息才能写持久缓存。没有可证明身份或完整前缀时保留内存，不伪造完整缓存。
- 不为每条Thinking建立独立游标、轮询或事件日志。历史窗口游标负责整体差异；详情的消息身份与内容版本负责有效性；活动Turn沿原生snapshot／seq／epoch恢复。尚未落库的最新Thinking前缀只作为该原生消息的过渡展示，不伪造持久消息行、不授予running／完成事实；原生落库后按同一UID合并，不额外占一条。无完整原生身份／切点则不落盘。
- 容量按消息计数，不能截断正文或详情来伪造完整缓存。保留跨Conversation最多10个／7天淘汰；不沿用旧2MiB单窗口限制导致详情自动被裁掉。浏览器配额不足则按旧Conversation／旧消息淘汰并重试，仍失败降级内存；不阻断在线使用、不把存储失败当数据同步成功。Blob、图片二进制、认证凭据不进历史缓存。

### C1 · 数据缓存与同步矩阵

“展示新值”均要求owner、请求轮次、身份及适用版本有效；被取消／过时响应没有提交资格。表中持久缓存不保存可执行权限。

| ID／对象 | 内存／持久缓存什么 | 何时展示缓存 | 何时展示最新数据 | 同步时机与方式 | 不变量与失败表现 |
|---|---|---|---|---|---|
| D01 Timeline正文／卡片外侧 | 同消息身份、逻辑顺序、原展示正文／时间／卡片状态及详情版本；最近500条。持久缓存包含已完成的同消息详情 | 冷开在确认owner后取精确缓存；暖切回首帧取该owner内存；断线／恢复期间保当前画面 | 当前所见窗口与原生Turn切点完成一致对账后一次交接；后续实时更新不等待整页REST | 初始、重连、回前台、当前历史失效用窗口游标；无缓存／游标失效只读必要窗口；分页按原入口按需读取 | 不清空再绘制；不拼回已删／rewind行；不把缓存当恢复完成；不全库扫描 |
| D02 已取得的旧Thinking详情 | 完整已收到的reasoning显示数据，归原消息及详情版本；内存与持久均保留，即使UI已折叠 | 原消息显示且详情已缓存时直接可用，展开无需先清空／重取 | 同消息详情版本未变直接复用；变更时可见已展开详情主动更新，不可见详情撤销旧有效资格、再展开才读 | 跟随窗口游标获得详情版本；仅版本变化且当前需要／缓存缺失时按需拉取 | 旧网络半截不持久化；不改变流式时展开、完成后自动收起、用户手动展开的行为 |
| D03 未取得的旧Thinking详情 | 只保真实卡片壳／未取标记，不缓存假空正文 | 卡片按既有折叠状态显示 | 用户展开后得到完整正文，提交为同消息详情并缓存 | 用户展开触发原详情读取；恢复时只有当前实际展开可见的缺失详情需要拉取 | 不为后台补齐而请求所有Thinking；加载／失败／真实空结果保持区别 |
| D04 最近一个Turn的Thinking（已完成或运行中） | 已完成正文；运行中仅经原生完整快照核验到有限切点的前缀，含同消息身份和“前缀／完整”标记，不持久化原始事件队列 | 冷开／断线可显示已核验前缀作为旧画面；不据此推断仍在运行或已完成 | 当前Turn的快照＋有序后续事件接管；转持久消息按UID合并 | 每次该Conversation历史同步／恢复主动拉取最新Turn详情，或直接复用本次完整state_snapshot；后续用原生实时事件；无单Thinking游标 | 新Turn开始使“最新”资格转移；旧半截没有完整确认不得升级持久详情；完成、取消、失败沿真实终态，不伪造成功 |
| D05 工具参数／结果、折叠终态输出详情 | 用户曾展开且完整收到的字段／身份／版本，与原消息一体缓存，不额外计条数 | 同消息详情缓存有效时立即显示；关闭展开面板不删缓存 | 服务端确认版本不变沿用；变更则当前展开需要的详情拉取并替换 | 版本由历史增量校验；未展开从不预取；展开／当前可见恢复按既有最多12行批次读取 | 不混淆工具生成中、运行中、完成、失败、取消；失败半截不持久缓存 |
| D06 历史附件／图片 | 消息中的既有授权引用、文件名／类型等；不存Blob／二进制／短期认证令牌 | 先显示原消息附件壳；已加载资源遵守浏览器原缓存 | 当前视口需要时通过原授权资源入口显示 | 按视口／显式打开加载；引用变化随历史增量；资源失败独立重试 | 不因重连下载所有图片，不把过期引用当永久资源，不阻塞无关正文 |
| D07 Timeline索引／跳转 | 原有索引内存与选择状态；不额外持久化全历史索引 | 已有同owner索引可作过渡 | 当前索引读取成功后更新，跳转目标按后端身份定位 | 复用原生timeline分页游标；展开索引／跳转按需请求；重连仅恢复当前使用范围 | 不用索引批量拉全部正文；不改变跳转和阅读位置语义 |
| D08 Conversation侧栏 | 持久摘要：id／profile／标题／pin／归档／分组及已读分页覆盖；不存可执行runtime状态 | 冷开／断线／暖切换沿原缓存展示 | 当前摘要分页成功后局部更新；实时active观察单独合并 | 原列表分页拉取＋既有sessions.changed失效；不新造全局列表游标；隐藏时不扩正文读取 | 同名不同Profile不混；不把后台列表失败冻结已恢复聊天；置顶／删除等不自动重放 |
| D09 标题／当前Conversation元数据 | 同owner最近有效显示值；动作仍取服务端 | 恢复期间保标题等原显示 | 当前元数据或更新事件有效后更新 | 每次恢复有界summary读取；事件与本地写回执按现有版本防倒退 | 当前owner元数据404才确认不存在；子资源404不能删会话或跳New Chat |
| D10 Usage Session／Latest | 持久展示数值、原统计scope／来源和兼容字段；不存运行权限 | 原视图保最近有效值，unknown／临时失败不清掉有效值 | 该统计视图本次有效结果局部接管，零值是真值 | 每次恢复原生usage_detail拉取，与历史正文并行；持久计数fallback尽量复用本轮已取得的summary，事件沿原失效规则 | 不因读取Usage锁住已核验正文；原切视图／高亮语义保持；失败在既有恢复单行重试 |
| D11 Context／Compaction胶囊 | 持久兼容的估算／窗口与展示值；compacting等运行状态仅内存 | 保同模型／Provider兼容的已知值 | 原生有效Context／Compaction状态到达后局部更新 | 每次恢复原生RPC拉取，可与历史并行；模型变化按既有失效规则处理 | 不把unknown误当0；模型变更不沿用不兼容值；只在原正式Turn结束条件高亮 |
| D12 Notebook Orb／Noting状态 | 同owner内存最后有效状态；不新增持久Notebook实体缓存 | 断线／重连／临时读取失败保原图标，不能闪unknown；首次无值不造idle | 本次secretary.state或有效既有状态事件到达后更新 | 每次恢复按既有轻量state拉取／事件失效，独立于历史正文；无新游标 | 网络状态不覆盖业务图标；真实task_state unknown／关闭／失败按原语义；完成动画不因恢复重复触发 |
| D13 Notebook展开面板／Schedules | 同owner当前面板内存；不新增持久实体缓存 | 已打开面板恢复期间保旧内容和展开层级 | 面板所需最新state／列表成功后局部更新 | 未展开不取明细；已展开重连主动拉取；沿既有Secretary／Schedule事件失效 | 不重开用户已关面板，不制造整板隐藏／重动画，不让未展开排期阻塞聊天 |
| D14 Pending／审批／发送受理 | 当前事务及原owner内存；不从展示缓存恢复权限，不持久化旧审批／pending快照 | 原输入和未确定提交状态按现有机制保留；不把旧审批伪装可操作 | 当前正式snapshot／receipt恢复后更新可操作性 | 每次恢复读原Pending／open_requests／receipt；实时事件沿原机制 | 不自动重发Send／Steer／编辑／审批；不丢已受理消息；失败不冒称未受理或成功 |
| D15 活动Turn正文／Thinking／工具实时输出 | 原生当前运行内存；仅D04明确允许的核验前缀进入消息展示缓存，不存原始事件流／运行权限 | 恢复前保已见画面；活动性未知不伪造idle／running | 完整state_snapshot＋连续seq后缀对账后接真实事件，正常流式立即显示 | 复用原生epoch／seq／session.events.since和现有完整快照；epoch变更或ring缺口重取当前快照 | 恢复不等Turn结束，不逐帧等REST；不能漏字／重复；合法Gateway活动Turn不因无Web流而报异常 |
| D16 Profile／模型／Thinking菜单／默认cwd | 原既有内存；不新增权限配置持久缓存 | 旧菜单展示不能越过原生当前owner校验；草稿选择保持 | 当前实际打开／New Chat需要的配置读取成功后更新 | Profile每轮读取；菜单按打开需求拉取；默认cwd仅New Chat需要；关闭菜单不为恢复重复请求 | 不扩大设置权限、不用别的Profile配置、不改变模型选择产品行为 |
| D17 草稿／附件／编辑意图 | 沿原草稿存储及事务机制，与展示历史缓存分离 | 恢复／断线持续保留输入、附件和编辑意图 | 用户操作或真实受理回执更新；后台同步不得覆盖用户新输入 | 原owner本地读取／写入，必要receipt只读核实；无历史游标 | 不以恢复重载清草稿，不重放写操作、不误清未受理内容 |
| D18 Files目录／预览 | 沿当前Files固定owner内存；不新增文件正文持久缓存 | 保当前路径、已打开预览、原画面 | 当前目录／预览所需读取成功后更新 | 初始与重连复用现有目录／预览拉取，未打开文件不取 | 不随聊天Profile换错owner；二进制仍原授权读取；失败局部可见，不整页刷新 |

### C2 · 恢复状态与表现层转换矩阵

| ID／转换 | 数据与控制边界 | Timeline／图标／输入的表现 | 何时结束／继续 |
|---|---|---|---|
| S01 冷启动，无缓存 | 校验owner并读首屏、配置、当前状态；无旧权限 | 沿原加载外观；不造历史、idle图标或旧审批 | 本轮所见窗口和Turn对账成功后显示；附属项独立收敛 |
| S02 冷启动，有缓存 | 精确owner候选只供显示；随后主动增量校验 | 先显示可用旧正文／已取详情／胶囊，首屏与折叠规则保持；不显示旧可执行状态 | 服务端差异＋切点核验后一次交接 |
| S03 正常连接→断线 | 旧网络轮次失效，保留用户意图；实时权限沿原失效 | 正文／阅读位置／展开／输入保留；Notebook原图标保留；Composer原单行Connecting | 网络恢复触发同页恢复，不reload |
| S04 断线→Socket连上 | connected只证明通道，不能宣布已恢复 | 缓存画面保持；Composer沿原Restoring项；不闪unknown、不弹AbortError | 当前所见历史与实时状态核验，实际附属项继续各自恢复 |
| S05 暖恢复／同epoch | 缓存游标提出变化请求，实时事件持续有序接收 | 不清空、不重新挂载、不跳走；不因后台小更新反复夺阅读位置 | 有限切点达成即接管，不等待Turn结束 |
| S06 服务重启／异epoch | 丢弃旧运行权限和事件水位，保留可校验历史缓存；失效历史游标补必要窗口 | 保旧画面直到新切点；不冒用旧流式running，不重发任何操作 | 原生resume／快照／窗口对账后接管；仍不reload |
| S07 请求取消／切owner／旧轮次迟到 | 取消不是业务失败；旧数据无提交资格 | 不弹协议错误，不让旧owner覆盖新页；新owner首帧按其缓存／加载显示 | 新owner独立完成；迟到IDB／网络结果丢弃 |
| S08 必要读取失败／断续弱网 | 本轮未满足；按现有退避重试，无完整成功回执 | 保画面、输入和Notebook图标；Composer现有Retrying；不把旧值改unknown或0 | 在线自动重试，后台／离线暂停；不触发网页／APK刷新 |
| S09 附属读取慢或失败 | Chat已核验可独立可用；附属项仍未完成 | 正文继续实时，Usage／侧栏／Notebook面板保各自旧展示；原单行提示具体未就绪项 | 局部重试完成后仅更新其区域；无全页冻结 |
| S10 当前可见恢复提交 | 历史／详情／有限流切点已对账，React完成本次布局 | 原前缀相容且idle保阅读锚点；真正重连确认active沿原有限滚向末尾；无位移不造动画 | 布局提交即就绪，不等缓存写盘、后台窗口或动画结束 |
| S11 正常连接中历史失效 | 当前会话新增、跨渠道完成或真实编辑触发增量；原连续流权限保持 | 持续呈现新流，后台同步不重新锁整个页面／不重启恢复动画 | 新窗口核验后并入原呈现；旧数据与新事件去重 |
| S12 用户展开／收起详情 | 已完整缓存且版本有效直接用；否则只取所需详情 | 保原卡片loading／错误／空内容表现；收起不删数据、不触发新网络；不改变默认展开规则 | 完整响应与版本有效才缓存；断线半截不写盘 |
| S13 最新Turn开始／完成／取消 | 最新Thinking主动恢复资格随真实Turn身份移动；终态沿原source与UID | 运行中Thinking原展开／流式；完成后原自动收起；不因缓存命中改状态或动画 | 已完整内容与消息身份合并；旧不完整段不冒充完整详情 |
| S14 Rewind／编辑／压缩／删除行 | 服务端新顺序及详情版本权威；移除被退役消息及关联详情／前缀 | 沿原编辑／压缩／定位语义；不复活旧缓存，不把同UID新内容混旧详情 | 对账后原子替换当前需要范围，再更新缓存 |
| S15 当前Conversation不存在／Profile不可用 | 必须由对应元数据／roster权威确认；撤销目标缓存及动作 | 原地址明确说明并给原返回入口；不静默跳New Chat、不循环刷新 | 等用户选择其它目标；不是“连接已恢复”伪成功 |
| S16 认证失效／登录恢复 | 撤销敏感展示资格及旧请求；沿既有认证流程 | 不展示未授权缓存，不刷新打断认证页 | 鉴权恢复后重新确认owner并走同页恢复 |
| S17 APK回前台／网络恢复 | Native仅发同页恢复信号；不再以5秒／退避deadline调用reload | 保当前页面、草稿、键盘／附件返回状态；恢复接近完成时不被打断 | JS恢复持续收敛；不把无心跳误判业务成功。系统杀进程后属于自然冷启，不是软件主动重载 |
| S18 存储损坏／配额／缓存缺失 | 丢弃不可验证缓存／游标，退回所需窗口读取；不改变服务端 | 正常在线／加载表现，不能因缓存不可用拒绝聊天或丢草稿 | 同页恢复完成后尽力重建缓存；完整消息不截断 |

### C2a · 表现层与操作资格的固定对照

本表中的“正文可见”与“页面可操作”是不同状态。只优化数据取得方式，不改`PageRecovery.availability`、`composerActionPolicy`及已有事务回执的产品判定；D10／S09所称“不锁正文”只指继续阅读与流式呈现，不表示提前放行写操作。

| ID／表现对象 | 原有判定与转换 | 本轮必须保持的表现／禁止的隐性变更 |
|---|---|---|
| P01 正文与可见详情 | `readyForDisplay`来自必要历史／切点及布局提交；缓存只提供此前画面 | 同owner不清空；详情命中直接用；不因缓存写盘、隐藏分页、未打开菜单迟延正文交接 |
| P02 Composer恢复提示 | 断线为`Connecting to Hermes…`；连上后按真实waiting显示`Restoring {对象}…`／`Retrying {对象}…` | 仍固定20px单行、省略号；多项每3秒轮换。chat／usage等名称保持，不伪装只有Chat和Usage、不隐藏真实失败、不增加Toast或横幅 |
| P03 Send／Steer／Stop主按钮 | 原`composerActionPolicy`读取连接且`availability.ready`、draftReady、pendingKnown、activityKnown、pendingBusy、uncertainSteer及真实运行状态 | 不用缓存替代任一权限；正文先恢复但必要附属项未就绪时仍沿原按钮禁用规则；连续在线的普通后台刷新沿原continuity资格，不反复锁定 |
| P04 输入、草稿与附件 | 输入可编辑性仍由draftReady等原条件决定；受理不明优先保留事务 | 恢复不覆盖新输入、不清附件、不自动提交；原未知受理反馈仍在恢复提示结束后按既有优先级显示 |
| P05 Notebook图标／球 | 业务task_state与全局开关决定；网络连接不是业务状态 | 同owner保最后有效业务图标；真实unknown仍unknown；开关关闭仍关闭，完成动画不重复，切owner不借用旧状态 |
| P06 Thinking／工具卡片展开 | 原流式展开、终态默认收起、用户主动展开的状态及身份归并规则 | 缓存完整详情不等于强制展开；收起不丢数据；同消息补全文字不重置用户展开选择；读取失败与真实空正文区分 |
| P07 Usage／Context | 原视图选择、来源兼容、unknown／零值语义与终态高亮规则 | 缓存不制造已完成Turn、不补造0；真零覆盖旧数值；局部成功只更新对应胶囊，不重播高亮 |
| P08 视口与滚动 | 继续沿现有前缀相容、active恢复、手动阅读与布局锚点规则 | 不因增量替换整树／重复执行无位移scroll；用户分页仍能读早期消息，500上限不裁当前阅读页 |
| P09 审批／Pending／错误 | 原服务端当前snapshot与真实回执授予动作；取消／过期请求无提交资格 | 不从缓存复活审批、Stop或重发资格；只消除无异常的Signal Aborted闪现，真实网络／服务端失败仍按原恢复重试或动作反馈呈现 |
| P10 APK生命周期与键盘 | 原通知导航、拍照／附件返回、IME Insets和网页document归属继续使用 | 不以恢复超时重载文档；不切焦点／清草稿；键盘尺寸真实变化同回调重绘，保主题与动画进度，不改布局设计 |

查责方式：按D项核对数据来源、S项核对触发与转换、P项核对可见结果；三者一致但结果不符合用户意图属于设计缺口，实际行为偏离任一表项属于实现缺陷。后续修订保留编号并明确改动理由与授权来源，不倒改历史验收结论。

### C3 · 最小机制边界与测试判据

1. 复用Desktop原生`session.events.since(last_seen)`、epoch、完整`state_snapshot`与现有恢复封套。它们恢复实时输出；原生timeline游标只分页索引，不足以证明持久正文的编辑／删除，因此历史差异只在现有messages／activate接口新增可选字段，不改变旧调用默认。
2. 历史窗口游标绑定server/profile/Conversation、selector和投影版本；服务端只保有界短期行版本清单，不建立持久事件日志或新数据库。有效游标返回变化行和当前权威顺序／删除事实；无游标／过期／重启返回该必要窗口快照，不能依赖前端盲目append。至少覆盖原位改文、同UID换代表行、rewind、压缩、跨渠道写入及删除。
3. 已取详情需同消息版本确认。旧详情完整且版本未变时，不因新cards投影不含详情而删除。最新Turn Thinking主动详情与活动快照须有真实身份、有限边界和完整性标记；内容字段只用现有用户可见投影，不引入隐藏模型原文。
4. 同一恢复轮次共享元数据／binding读取；Usage、Context等仅需binding的读取不等待历史正文。隐藏菜单和非可见旧分页不得无条件争抢网络；用户打开时仍取得最新数据。已显示旧分页在实际变为需求时校验，不以500缓存上限裁掉用户当前页面。
5. 补齐无reload场景：同／异epoch、活动Turn、断线新增／改写／删除、游标失效、缓存损坏／空／容量淘汰、详情已取／未取／半截、最新Thinking前缀、切owner迟到、失败后自动重试、Files和菜单、APK超5秒仍完成、原生通知导航／附件返回。对照记录200条长正文的完整／无变化／少量追加传输字节与请求数，不能只用时间或测试总数宣称性能完成。
6. 独立main修复亦纳入最终回归：取消请求不弹异常但真失败仍可见；Notebook不闪unknown；键盘resize无空白帧；微信会话内Slash及逐完整Assistant Message即时投递。真实Android／微信外部发送不可用时明确证据边界，不能冒称已实机验证。


<!-- 以下前言保留原轮次时点；本轮增量契约优先关系见本文顶部。 -->

> **改版阅读边界（2026-10-16）：** 本文保留现有Web UI与原生客户端架构基线。用户已确认第三轮自主实现聚焦Secretary改版与个人NM接入，界面修改整体后置；Memo控件、Orb／Idle倒计时、Notebook人类卡片、Settings及UI读取DTO的调整不作为本轮实施／验收条件。下方局部标识仅说明旧语义已被白板＋07替换或继续继承，不构成第三轮UI施工清单；后续界面改版另行安排。

> **历史冻结范围：** 下行“this round”“remain frozen”等只指第二轮，不约束第三轮已授权的改版。局部过时标识优先于对应旧正文；不修改第二轮验收历史。

> **Status:** Frozen normative specification for Round 2 (2026-10-12). This round MUST NOT revise its authoritative specifications; implementation and acceptance status belong to the root CLAUDE.md and round reports. **Authorized exceptions (2026-10-13):** §1.6 Composer keyboard binding (Enter submits content only; Escape carries the cancel-type primary actions), with §1.10 aligned; and §1.7 attachment budget (all attachments in the current draft together MUST NOT exceed 500 MB), explicitly confirmed by the user. Subsequent explicit user-confirmed amendments, including the 2026-10-14 corrections, are recorded in the Round 2 Snapshot Index. Unrelated clauses remain frozen.
> **Date:** 2026-10-12
> **Target:** `EdgarZhong/hermes-secretary` native Hermes/Secretary backend plus a separate browser-native Secretary UI repository.
> **Authority:** The user's final decisions in the two 2026-10-12 UI discussions and subsequent clarification take precedence over superseded UI proposals. For inherited Secretary Core semantics, effective `docs/02-noting-system-specification.md`, including its confirmed V1.6 revisions, takes precedence over corresponding older clauses in `docs/04-hermes-secretary-v1.5-implementation-spec.md`; retain 04's increments not superseded by current 02, then inherit applicable 01 requirements not covered by those increments. This specification is authoritative for its **expressly identified, user-approved Web UI increments**, which require compatible additive changes. Actual deployed behavior is established by source and tests, not by any historical design discussion.
> **Document organization:** Exactly six top-level numbered divisions at the `##` level, numbered **0–5**. Division 0 is the mandatory terminology/architecture preamble; divisions 1–5 are the five delivery sections. All subsidiary headings are `###` or `####`, with at most 20 sibling headings per parent.

**Normative vocabulary.** **MUST / MUST NOT** state non-negotiable V1 requirements; **SHOULD** is a strong implementation preference that may be varied only if the stronger architectural or functional invariant is still satisfied. **Existing** means grounded in the inspected fork; **Proposed additive** means a required outcome for which a new native interface may be necessary; **Verify** means the current implementation/DTO/transport or end-to-end guarantee is not yet established. A proposed name never silently becomes an existing API.

---

## 0. Terminology, Specification Authority & Architecture Invariants

### 0.1. Canonical terminology

> **第三轮适用性：** 表中Memo及Notebook-owned Schedule的术语已过时；Conversation／Session／Message Identity、原生客户端与真实消息载体继续继承。第三轮Scheduler与Notebook的定义以07术语表为准。

Use Hermes/Secretary's actual names first. UI-only terms are allowed only when they denote actual presentation behavior that has no corresponding native primitive.

| Term | Precise meaning | V1 implementation rule |
|---|---|---|
| **Hermes Desktop** | The existing Electron application, renderer, shared client code, and native API integration | Primary reference for feature coverage, session recovery, message projection, transport wiring, and API use; **not** an implementation to wholesale port. |
| **Dashboard REST** | Existing FastAPI HTTP routes, including `/api/sessions/*`, `/api/fs/*`, and `/api/files/*` | Frontend calls the relevant existing endpoints directly; no newly invented server-side UI adapter. |
| **TUI Gateway** | `tui_gateway/*`, with WebSocket JSON-RPC exposed at `/api/ws` | Hosts session-scoped runtime control, prompt submission, stream/event fanout and native attach methods. |
| **Messaging `gateway/`** | Hermes's messaging-channel integration layer | **Not** a synonym for TUI Gateway or Dashboard REST; no dependency on a messaging chat transport for primary browser chat. |
| **Agent Core** | Python Agent execution, tool calls, context/compaction, and runtime-owned state | Backend-owned; UI never instantiates, serializes, or owns Agent instances. |
| **Conversation** | One logically continuous user-facing path, including valid compression continuations; branches/new/reset are distinct | The view must preserve user continuity while correctly respecting native boundaries. |
| **`conversation_ref`** | Secretary's durable logical Conversation identity defined in 02 | Authoritative for Secretary Notebook/Noting/Memo ownership; the browser does not mint or duplicate the registry. |
| **Stored Session ID / `session_key`** | Durable Hermes Session locator (and its compression lineage) used for list, REST history, and resume | Used as the stable UI route/lookup address where supported; must not be confused with `conversation_ref`. |
| **Runtime Session ID / `session_id`** | Ephemeral TUI Gateway `_sessions` key used by session-scoped RPCs | Client keeps only a transient mapping from stored locator to this ID; invalidates/rebuilds after transport/backend changes. |
| **Message Identity** | `(conversation_ref, message_uid)` as specified in 02 | Must be respected whenever native UIDs exist; never substitute a physical DB row ID as a universally stable semantic identity. |
| **Timeline** | The chronological UI containing real stored messages, live projections, and visibly pending-but-not-yet-stored steer bubbles | Presentational surface, **not** a new authoritative transcript store. |
| **Turn** | One Hermes `run_conversation()` driving execution, possibly with multiple model/tool calls | Usage and controls must not equate one assistant bubble, model call, or tool call with one Turn. |
| **Steer / `session.steer`** | Native correction injection into a running Turn, not a new persisted user Turn at acceptance time | Browser text-only active-turn submission uses this existing mechanism. |
| **Pending Steer** | A server-accepted Steer not yet consumed at its legitimate native insertion point | May have separate temporary UI bubbles; exact withdraw/consume truth must come from backend. |
| **Withdraw** | Remove exactly one still-unconsumed pending Steer and recover its text | Not deletion of an already-persisted message; cannot succeed once consumed. |
| **Interrupt** | Stop the current Turn **and** atomically promote its remaining pending Steers into one follow-up Prompt | Different from plain Stop; never submits unsubmitted Composer content. |
| **Cancel Send** | Cancel one in-progress pre-acceptance send/upload transaction, restoring its captured local draft | Different from stopping an Agent Turn or canceling a Compaction. |
| **Rewind + Edit** | Frontend Reply action followed by confirmed native history truncation and resubmission | Not a threaded reply, filesystem rollback, or separate message-edit database. |
| **Compaction** | Hermes's actual context compression and possible physical Session rotation | Display true history content and true status; never insert a fabricated compression notice. |
| **Framework Message** | Secretary runtime-produced durable user-role message, typically `<framework-message>` | A real message in the Timeline with its own visual treatment. |
| **Instant Reminder** | Secretary active user-reminder delivery, typically `<instant-reminder>` | A real user-role message in the Timeline with a distinct reminder treatment. |
| **Deferred Reminder** | Secretary passive in-request reminder, typically `<deferred-reminder>` | Display where it is actually part of the durable/displayable native projection; never invent one merely from a pending schedule. |
| **Secretary Orb / Memo Stick** | Conversation-only, read-only UI projections of actual Noting state and current Memo | Not a secondary scheduler, task initiator, or Notebook editor. |
| **Full Foreground** | 02/04's logical audit view with Context Prelude, message nodes and Anchor/Snapshot annotations | **Deferred UI**; ordinary chat history is not to be mislabeled or implemented as Full Foreground. |

**Terminology retired from earlier discussions:** `Attach Notice` as a synthetic API object; `Photo Attach` as a universal backend operation; `PDF Attach` for ordinary file-PDF transfer; `Gateway` used ambiguously; `Reply` as a second thread; a separate `In-flight Queue` card/zone; speculative `/stash` name for the actual `/notebook` command; and a new “Conversation Web API” just to map stored IDs to runtime IDs. They MUST NOT appear as new domain types or backend requirements.

### 0.2. Relationship to 01/02/04 and historical 06

> **第三轮适用性：** 以下优先级描述的是第二轮。第三轮先白板＋07，再继承旧规格明确保留部分；旧规格中的Target不得反向覆盖新版。浏览器/notebook只读临时结果的差异仍保留。

| Source | Retained authority | Deliberate Web UI boundary/revision |
|---|---|---|
| `01-personal-hermes-v1-first-fork-iteration.md` | Hermes-first, additive-first, Conversation truth | The Web UI is a later, independently scoped delivery; it does not reopen the original first-fork implementation. |
| `02-noting-system-specification.md` | Current Core contract, including confirmed V1.6 revisions: `conversation_ref`, `message_uid`, Notebook, Noting, Reminder carriers, Compaction, Schedule | Current 02's confirmed revisions take precedence over corresponding older 04 clauses. UI displays these facts and uses existing backend owner resolution; it does not replicate Core rules. |
| `04-hermes-secretary-v1.5-implementation-spec.md` | V1.5 increments not superseded by current 02, including applicable Full Foreground and Core clauses | Inherit only still-effective increments, then applicable 01 requirements they do not cover. Full audit projection remains deferred as a UI feature. |
| Original `06-ui-read-api-discussion` | Early Web UI scope, read-only files, Orb/Memo, future audit requirements | A superseded discussion record, **not** an API schema, a current integration map, or authorization to implement. |
| `UI选型评估` and `恢复UI讨论` conversations | The user's later confirmed product interactions | Adopt the **latest user decision** when a conversation contradicts an earlier proposal, especially for Steer, Attach, Timeline, Slash, Compaction and Orb. |
| Subsequent architecture/UX decisions | Direct REST+WS, Desktop-first wiring, thin client, scoped engineering/design roles, Timeline timestamps, Files navigation | These are the final V1 decisions and override earlier assistant-imposed architectural constraints. |

For any inherited 02/04 reference below, apply the same precedence: current 02, including confirmed V1.6 revisions, then still-effective 04 increments, then inherited 01. This 06 supersedes the historical UI discussion for Web V1; its explicit Web increments remain authoritative.

**Explicit Core/UI conflict:** the inherited 02 text permits bare `/notebook` render output to participate in ordinary persisted transcript/context semantics. V1 now requires **human-only transient rendering without a durable message or model-context insertion**. This is a deliberate, limited new behavioral requirement; the implementing lead MUST locate the current command dispatch/persistence seam and provide a compatible, minimally invasive browser-facing path. It MUST NOT claim this behavior already exists or silently rewrite other CLI/TUI semantics.

### 0.3. Authoritative C/S architecture

```text
Browser-native Hermes Secretary UI
  React + assistant-ui + shadcn/ui + Tailwind
  UI rendering, bounded ephemeral state, transient stored-ID/runtime-ID mapping
        |                           |
        | HTTPS (existing REST)     | WSS (existing /api/ws, JSON-RPC + events)
        v                           v
  Hermes Dashboard REST         Hermes TUI Gateway
  SessionDB history, files      session.create/resume/activate,
  media, metadata, config       prompt.submit, steer, interrupt, stream
        \                           /
         \--- native Hermes/Secretary backend ---/
                     Agent Core + state.db + filesystem
```

The diagram is a **logical ownership** diagram, not a deployment promise that all browser cross-origin/auth scenarios already work. Browser authentication, URL resolution, hosting, WSS and file access MUST be validated against real routes and policies. A hosting reverse proxy required by deployment is infrastructure, **not** an invented BFF, alternate transcript API or Agent lifecycle owner.

Round 2 uses a separate **local frontend repository beside this backend workspace**, `hermes-secretary-web`. Necessary backend increments stay in this `hermes-secretary` workspace; all process plans, coordination records and acceptance evidence stay here as well. Subsequent user authorization enables automatic push after commits in both repositories. This code synchronization does not authorize cloud deployment or Memory Provider work.

### 0.4. Thin client and local-persistence allowlist

> **第三轮适用性：** 薄客户端与持久化边界保留；表中Memo实体退出，Schedule从Notebook中独立，权威owner仍在Secretary服务端。

| State | Authoritative owner | Browser treatment |
|---|---|---|
| Session list, stored transcript, titles, pinned/archived metadata, Lineage | Hermes SessionDB | Fetch on demand; 2026-10-24允许下文限定的过渡展示快照，不建立可写镜像或第二历史库；恢复仍完整重读页面所需范围。 |
| `conversation_ref`, Notebook, Memo, Noting task/schedules | Secretary Core `state.db`/runtime | Read via native or minimally additive read interfaces; never client-derive truth. |
| Agent Turn lifecycle, Pending Steers, execution progress, usage, Compaction | TUI Gateway / Agent Core | Live in-memory projection from actual RPC/event/REST facts; refresh/reconnect resynchronizes. 仅Usage／Context已取得的展示数值可按2026-10-24边界缓存，不包含运行事实。 |
| Stored Session ID → Runtime ID map, event high-water marks, inflight render state | Browser working memory | Minimal transient Map/state; not persisted; recreated with existing `session.resume`/`session.activate`. |
| Unsubmitted text, selected photos/files and their Blobs, New Chat draft | Browser local persistence | Allowed, scoped by draft/Conversation and recoverable across same-browser reloads (IndexedDB for binary where appropriate). |
| Last route, Files return target, explicitly chosen presentation preferences | Browser local persistence / URL history | Allowed, sparse and device-local; validation against server on restore. 滚动位置／阅读锚点依2026-10-15确认只留内存。 |
| Existing config such as `terminal.cwd`, actual active model/effort | Hermes native config/session | Display source of truth from native API; a *not-yet-applied user selection* may be local draft only. |

The implementation MUST NOT introduce a general persisted API-response cache, client SessionDB replica, client-held Notebook records, client-managed turn ledger, independent unread watermarks, or background synchronization to make those local copies agree with the server. **2026-10-24明确例外：** Timeline、Conversation侧栏、UsageSummary／ContextIndicator可保存按owner隔离、容量有界、可丢弃的展示快照；白名单和失效规则见§1.4.1，不保存整份API响应，不跳过本轮真实读取，不恢复runtime、审批、Pending或事件游标。该例外替代旧的全面禁止展示持久缓存口径，其余薄客户端限制保留。Small **in-memory** render buffers and pending UI state are inevitable; use no more than required. Losing browser storage may lose **unsubmitted** data and local presentation preferences, but MUST NOT destroy already accepted server data.

### 0.5. Additive compatibility and data provenance

1. All existing native REST/RPC methods MUST keep their names, required/optional input shapes, response shapes, errors and semantics. The V1 UI adapts to them; it does not standardize them by rewriting backend contracts.
2. Backend changes are restricted to concrete missing V1 atomic operations, source-truth read projections, or necessary event visibility at existing native seams. New behavior MUST be scoped and tested without side effects on unrelated clients.
3. UI-specific projection fields MUST NOT replace or rewrite real messages, `message_uid`, timestamps, attachments, `conversation_ref`, persisted Session lineage or model context.
4. An API call's *acknowledgment* and a Turn's *completion* are distinct. A websocket disconnect does not prove that a submitted Prompt was rejected.
5. Read-only navigation, Files browsing, Noting/Memo/Notebook inspection and route restoration MUST NOT start a new Turn, mutate Notebook/Memo or consume a Reminder.
6. A missing/uncertain backend fact is represented as loading/unknown/error, **never as guessed success, false idle, an inferred consumption, or a fabricated historical row**.

### 0.6. Engineering and delegation authority

> **第三轮适用性：** 本节角色与编排属于第二轮历史安排，第三轮以新计划与AGENTS为准；不据此指定旧Agent或扩大文档冻结。

**Main/Integration is GPT-6 Astra high**, accountable for technical direction, complete requirement coverage, delegation, review and integration. **Development is GPT-6.1 Sol high**, responsible for concrete frontend/backend implementation and relevant tests within assigned boundaries. Independent **Verification is Astra high**, independent **Validation is Astra medium**, and the independent **visual designer is Astra medium**. Technical accountability does not make the Main agent the sole code implementer. The visual designer is scoped to a cohesive design system, responsive visuals, tokens and styling, with **no authority to design new product interactions** or change button conditions, navigation, data semantics or Agent controls. See division 4 for boundaries and acceptance.

### 0.7. Confirmed deployment topology and dual-SPA routing (2026-10-17)

> **User-confirmed deployment shape.** One private hostname, one Cloudflare Access gate, one backend process serving both the Secretary SPA and the native Hermes Dashboard. This is a deployment decision, not a new API or a second product surface.

The following constraints are normative for the private cloud deployment:

1. **Single public entry.** The only public address is one private hostname protected by Cloudflare Access with an email allowlist. Cloudflare Tunnel reaches the backend host; a loopback-only reverse proxy rewrites the request `Host` to `127.0.0.1` and removes `Origin` before forwarding to Hermes. The Hermes backend and the reverse proxy MUST bind `127.0.0.1` only. No browser cross-origin configuration, second API hostname, or CORS policy is part of this deployment.
2. **Two SPAs, one origin.** `/` serves the Secretary SPA from `HERMES_WEB_DIST`. `/dashboard` serves the native Hermes Dashboard SPA from `HERMES_DASHBOARD_WEB_DIST` (prefix `HERMES_DASHBOARD_PREFIX`, default `/dashboard`). Both are same-origin with the API and MUST acquire the injected `window.__HERMES_SESSION_TOKEN__` from their own served `index.html`.
3. **One shared API and one backend process.** `/api/*` and `/api/ws` are shared by both SPAs. Requests under `/dashboard/api/*` MUST be rewritten to `/api/*` before routing, for both HTTP and WebSocket upgrades, so the native SPA can use `__HERMES_BASE_PATH__ = /dashboard` without a second API surface. Both SPAs MUST be mounted in the same Hermes process. A second backend process, multiple workers, or replicas are forbidden for this deployment: `_sessions` is process memory, and Scheduler/Noting background owners would duplicate or diverge.
4. **Authentication boundary.** Cloudflare Access is the only user-visible authentication layer. The backend session token remains an automatically injected machine credential, not a second interactive login. `dashboard.public_url` MUST NOT be configured for this deployment because it engages the dashboard OAuth gate; `--insecure` does not bypass authentication and MUST NOT be relied upon.
5. **Docker is allowed only with host identity.** If the backend runs in a container, the reverse proxy and the backend MUST share the host network namespace (or an equivalent arrangement) so WebSocket upgrades still present a `127.0.0.1` peer; a separate bridge network would be rejected by the loopback peer check.
6. **Stale runtime sessions are a normal reconnect case.** A backend restart, idle TTL, or eviction invalidates the in-memory runtime session. Session-scoped `config.set` for `model` / `reasoning` answers `4001`; the Web UI MUST resume the stored session and retry that operation once. Recovery is silent on success and surfaces the real error on failure. The backend stale-session guard MUST NOT be removed or weakened.
7. **No default change when the second SPA is absent.** When `HERMES_DASHBOARD_WEB_DIST` is unset, the server MUST behave exactly as before: no `/dashboard` mount and no path-rewrite middleware.

The stable operator entry points are `HERMES_WEB_DIST`, `HERMES_DASHBOARD_WEB_DIST`, and `HERMES_DASHBOARD_PREFIX`; their operator-facing summary lives in the repository README.

### 0.8. Development opt-out for model code-skew guards (user-confirmed 2026-10-17)

The user approved a configuration switch for the native model-operation code-skew protection (including RPC error `5098`). This is an implementation requirement, not a claim that the switch already exists.

- **Default compatibility.** The protection remains enabled by default. Existing installations without the new setting retain the original behavior and error handling.
- **Scope.** An explicit development opt-out bypasses only the model-operation skew guards. Keep raw revision detection, its cron consumers and backend retirement/watchdog behavior intact. Do not make `detect_code_skew()` return a fabricated no-skew result to implement the switch.
- **Configuration ownership.** Use the existing configuration system, not a new environment variable or frontend setting. The policy belongs to the backend process; requests or Sessions from different Profiles in that process must not change it. The implementation must document the chosen key and activation/restart behavior.
- **Preserved boundaries.** No database/schema, frontend protocol or Session ownership changes. Preserve the independent stale-runtime `4001` guard, authentication, model/provider validation and existing quality checks.
- **Actual limitation.** Opting out permits model operations despite revision drift; it does not hot-reload Python modules or guarantee compatibility between loaded and on-disk code. Genuine import/runtime failures still surface and may require a restart.

Implementation and evidence status remain in root `CLAUDE.md`. Tests must cover the default/enabled path, the explicit opt-out through the actual model ingress points, consistent process policy across Profiles, and unchanged raw detection/other consumers.

---

## 1. Product Design, User Interactions & V1 Boundaries

### 1.1. Experience, scope and visual authority

V1 is an English-language, responsive, chat-first Secretary, accessible from desktop and mobile browsers at a private deployment. It provides conversations, native execution visibility, attachments, session/turn control, a read-only Files viewer and restrained Secretary/Noting visibility. It is **not** a general-purpose assistant platform, an IDE, an Electron port, or a replacement for the existing administrative Dashboard.

- Use `assistant-ui` as the interaction/component foundation and `shadcn/ui` + Tailwind for the application design system. Browser-native semantics and accessibility take priority over bespoke render tricks.
- No speaker portraits/avatars in user/assistant message bubbles; preserve visual differentiation through layout and reusable tokens/components.
- The visual AI owns colors, fonts, radii, spacing, elevations, motion quality and responsive finish within the fixed product semantics. Do not name other libraries as required style dependencies or prescribe ornamental treatments not approved by the user.
- App identity/favicon/New Chat brand asset slots MUST use supplied project assets when available; absent assets receive a tasteful design-system placeholder without inventing new product branding or a hard dependency on an asset not yet provided.

### 1.2. Pages, navigation and browser history

Exactly **three main screen states** exist: **New Chat**, **Conversation**, **Files** (file list and preview are Files substates). The mobile sidebar/drawer exposes New Chat, Conversation list and Files; the **sidebar control remains at the mobile top-left** on every main screen.

| Screen | Mobile top-left | Navigation bar top-right | Main behavior |
|---|---|---|---|
| New Chat | Sidebar button | **No** `Back to Chat` | Welcome/initial composer; no backend Session merely from navigation. |
| Conversation | Sidebar button | **No** `Back to Chat` | Existing conversation, timeline, composer, conditional Secretary Orb. |
| Files list | Sidebar button | **`Back to Chat`** | Browse the configured default directory read-only. |
| Files preview | Sidebar button | **`Back to Chat`** | Read-only preview; Files internal path/breadcrumb navigation. |

- Desktop Files also puts `Back to Chat` **at the right of the Files navigation bar**, not the left; New Chat and Conversation never display it. The visual AI determines styling, not the location or conditions.
- **`Back to Chat` is a deliberate exit action, not `history.back()`**: it always returns directly to the chat state closest before entry into Files (existing Conversation or unsent New Chat), regardless of folder depth or preview depth. It restores the chat draft and reading position. With no valid preceding chat target (e.g. direct deep link), it opens New Chat. It must not create/resume/interrupt a Turn solely to navigate.
- Browser Back/Forward controls and platform-provided swipe-back gestures **must work natively** through real browser history. Files subroutes (directory and preview) participate in history; no application-level swipe gesture simulator or history-hijacking interception may replace system behavior.
- From Files, internal breadcrumbs/back-to-folder navigate the file hierarchy; they are **not** a substitute for the Files-level `Back to Chat`. Preserve native keyboard focus and standard link behavior.
- Refresh/revisit restores the last shown route (New Chat, Conversation, Files list, or Files preview), selected conversation, relevant preview path and reading position, plus local drafts. Verify the target still exists and is authorized; if not, fall back safely without changing backend state.

**用户确认 Android APK（2026-10-21）：** 使用 Tauri 2，前端构建资源内置 APK，业务仍连接现有线上 Hermes 服务并沿用认证；不把纯线上网页壳当作内置前端交付。重新打开恢复上次关闭时的 Conversation，复用现有本地路由及 Profile 归属和服务端有效性校验，不另建对话缓存。底部暂不增加安全区；顶部按真实系统状态栏／刘海尺寸避让，菜单、侧栏和通知不得与状态栏重叠。用户明确授权本任务启动并操作 Android 模拟器验收；先将原始分辨率与 density 调成整数倍率，实际验收 CSS 视口为 **360×792**，以 APK WebView 的实测尺寸为准，不能只用系统逻辑屏幕尺寸代替。打包及验收不包含生产服务配置或认证策略变更。

**用户2026-10-21追加确认：** 顶部安全区不能为零，但状态栏下方的菜单／标题留白应比首次24px预览更紧凑。Android保留真实状态栏／刘海避让，将该区域下方间距由12px缩为4px、顶栏内容高度由64px缩为56px；普通浏览器外观保持原样。360×792浏览器预览标识的状态栏只用于视觉核对，不进入APK产品页面。

**2026-10-24适用性说明：** 上段“不另建对话缓存”由§0.4、§1.4的限定展示快照例外替代；仍不建立第二Conversation库。下方2026-10-21“返回前台立即刷新、connected即停止重载”记录旧版行为与当时口径；新目标为§1.4.1的先保留页面恢复、5秒内本轮可见依赖及Socket／Turn就绪则不重载，超时原生兜底。后续10／15／20／30秒退避、首次正常加载及认证／附件／通知保护继续保留。此替代不改写旧版交付和验收事实，新方案尚未实施。

用户随后对上述收紧预览确认“看起来不错”，采用该Android视觉。24px仅为当前模拟器状态栏实测，正式壳使用设备实时Insets，不把其它设备强制设为24px。最终补充确认：标题保持靠左，只保证在状态栏下方的56px内容带垂直居中，Android上下间距统一4px；此适配只对APK生效，普通网页不启用，显式Mock预览除外。

**用户确认图标更新（2026-10-21，0.1.1）：** APK启动图标复用已有Hermes Secretary logo，居中放在现有主题色卡的深色背景上；不另行重设计logo。用户随后反馈launcher前景被过度放大裁切；后续修复须按adaptive icon前景安全区和普通图标实际mask核对，保持logo可辨、不过小、不露四周白边；背景沿深纸色填满，不修改logo内容。

**用户确认自动恢复（2026-10-21，后续版本）：** APK在原生生命周期确认进入后台后，返回前台显式重载WebView网页和JS，不仅依赖前端重连；系统冻结无法精确判定。用户进一步要求考虑移动弱网、缺少刷新按钮时必须自动恢复，不能停在失效页面。短暂WS断线保留现有重连，持续失败／前台JS无健康响应由原生兜底并限制频率；不为短断快速循环刷新。不清Cookie／本地草稿与路由，通知目标跨刷新保留，第三方认证与原生附件交互不得被恢复刷新打断。**用户随后澄清：** 首次WS断线先尝试现有代码恢复，几次／几秒短时间内仍无法恢复时触发原生刷新；不能因刷新退避再等一分钟或更久。此口径覆盖先前Agent提出的45秒及分钟级退避方案。返回前台立即刷新，无JS／未就绪错误页也应有独立原生恢复能力，不能因为只允许一次刷新而永久停住。**最终追加确认：** 首次打开是正常加载，不额外重复刷新；解锁回前台及从后台回前台均立即原生重载，并将旧的退避计时和进度全部清空。此后监测WS是否实际connected；首次给10秒，未恢复则原生重载并重新计时，随后15秒、20秒、30秒，封顶30秒继续尝试；连接恢复停止该轮自动重载。再次切回前台始终立即重载并从10秒重新开始，不承接旧退避剩余时间。此最终口径覆盖前述分钟级及5秒单次刷新方案。JS持续响应且WS已连接的正常慢历史加载不判失败；明确初始化报错或JS无响应使用原生恢复兜底。

**用户2026-10-21逻辑视口澄清：** 手机整页显示更多内容须由Android壳提供更大的实际逻辑视口并按手机屏幕等比显示；不采用前端按断点缩放整页的方案。用户最后明确选择380，采用380 CSS px作为手机竖屏目标（覆盖此前390建议），保持等比；横屏／大屏须避免因硬塞380反向放大，键盘弹出不改变缩放基准。后续须实测WebView的`window.innerWidth`与比例，以及Insets／键盘避让。最终APK等全部修复验证后统一准备。

#### Android 原生通知与临时后台保护（用户最终确认，2026-10-21）

**APK方向（用户确认，2026-10-23）：** Android壳固定竖屏，不随设备旋转自动切换横屏；合并Manifest及Activity运行时方向保持一致。普通网页沿原响应式行为，不由本条锁定方向。实际安装包和真机验证状态只记根CLAUDE及运维记录。

- **范围以现有观察能力为准。** 复用已有`session.active_list`、`sessions.changed`、`state.sessions[].running`及`gateway.ready`，识别现有列表监控范围内跨Conversation、跨Profile的Active Turn；不只看当前`state.live.active`，不要求由APK发起。全局运行监控不等于所有会话完整正文推流，不发现／监听原客户端不能观察的外部Turn。
- **保持现有资源边界。** 不批量`session.resume`／`session.activate`，不取消`releaseInactiveViews()`，不破坏弱网优化、历史懒加载和Conversation切换。不改后端API契约、Gateway接线或WebSocket协议，不加全局查询、额外轮询、新推流、独立WS、FCM／Firebase或通知服务器。
- **临时保活。** 至少一个被现有全局状态观察到的Active Turn时启用；各Turn结束逐一更新，全部结束后解除。尽可能保持同一WebView、JS和已有WS短暂后台运行，不另建Conversation／Agent Runtime状态。原生前台服务只提高存活概率，遵守后台启动限制、权限和系统时限；拒权、系统暂停／回收或强制结束不影响云端Turn。无长期驻留、进程重启自启、离线通知、补发或后台发现。
- **完成依据。** Active→Idle只触发核验，不直接等同正常完成；用已有只读事件回放核实当前连续连接期间的正常完成，再按需读取既有只读Session History及必要详情，确认最终可见Assistant行实际持久化。不得用侧栏preview替代最终回复，缺失／截断／不可靠证据时放弃通知。Thinking、Tool Call、Compaction、Noting、中间正文、失败、取消不触发。Profile＋Stored Session ID区分owner，真实Turn／Message身份去重。
- **断线边界。** 断线、状态未知、epoch变化使未完成核验失效；重连后观察到Idle不能推断刚刚完成或补发旧通知。重复事件、异步旧结果和重放不得重复通知。系统终止后不要求继续通知或补发。
- **通知呈现。** 仅APK在后台且确实收到所跟踪Turn正常完成时发送Android本地通知；前台不发。标题固定“您的助理有一条消息”；正文直接取对应最终Assistant回复开头，适当去Markdown／多余换行并截断，无LLM摘要。不同Conversation完成可分别通知。
- **通知通道升级（用户确认，2026-10-21）。** APK覆盖升级迁移到新的响铃＋横幅通道，使用HIGH等级和系统默认提示音，尽量保留用户主动静音／关闭设置；不能以同名通道重新注册冒称旧等级已经提高。Android旧版本无法完整识别主动设置时须如实保留实现与验收限制。
- **点击和权限。** 处理Android通知权限，拒绝不得破坏对话。点击打开正确Profile的Conversation，尽可能定位该Assistant回复；冷启动保留通知目标、沿用认证，不向登录页注入业务内容。桥接只允许APK可信页面主frame，不向普通网页、第三方页或iframe开放原生通知能力；最小去重仅进程内，及时清理原生资源。
- **验收。** 覆盖APK发起及电脑发起但APK已观察到的Turn；查看B时A完成；多个并发分别通知且最后解除保活；跨Profile同ID；前台抑制；断线／重连／重复事件；点击正确归属；观察范围外不扩接线；系统暂停／回收不保证通知、不影响云端执行。真实实机／模型与隔离测试证据分别记录，不把模拟或未验场景写成通过。最终交付前端资源内置、已签名且可直接在手机安装的APK。

### 1.3. Session list, New Chat and chat selection

| Operation | Required behavior | Forbidden shortcut |
|---|---|---|
| Enter New Chat | Show clean unsent route and scoped draft; no backend Session | Creating an empty `session.create` on page mount. |
| First Send | Create exactly one backend Session via native RPC; then stage attachments and submit as prescribed | Eager create / duplicate create on concurrent button/Enter. |
| Open stored Conversation | Fetch authoritative history by stored locator; bind runtime only when needed for live actions/state | Reuse an unrelated runtime ID or force a new Conversation. |
| Switch conversations | Change selected route, hydrate destination; keep other running Turns owned by Hermes | Cancel previous Turn just because view changes. |
| Lineage/Compaction | Present one continuous user-semantic Conversation across valid compression edges, respecting branch/new boundaries | Treat every compression child as a separate new chat; merge branches. |
| Session with different historical cwd | Keep discoverable in the list according to native filters and real accessibility | Silently hide historical sessions to make the default-cwd story appear uniform. |

Conversation list, title, ordering, archival/pin affordances (only if included by the approved design and native capability) use actual REST results. Do not add management controls just because Desktop has them. Empty/loading/error and a lost/deleted session are explicit, recoverable UI states.

**用户2026-10-25确认：** 已删除Conversation应从最新权威列表移除。旧缓存、旧链接或已打开页面遇到该Conversation确实不存在时，保留当前定位并显示明确不存在／已删除错误和返回入口，禁止静默重定向New Chat。历史、详情、锚点等子读取失败或404不能等同Conversation不存在；当前owner的精确元数据读取才用于判断存在性，子读取失败按页面恢复契约保留过渡内容并恢复读取。后端使用已选Profile的实际数据库归属，不因导入会话遗留的`profile_name`标签误拒正常存在会话，不新增跨库查找或修改用户历史。

**用户2026-10-25最新变更：Gateway运行中可访问，结束主动更新。** 微信等Gateway Turn在其他进程运行时，Web仍必须允许读取同一Profile／Conversation已成功取得的持久历史，不得因当前Web进程没有Gateway实时输出快照而整页空白。用户进一步明确这属于正常状态，不得报恢复错误／降为只读／只显示旧缓存。须基于同owner的真实native外部Turn lease和稳定有界REST读取，正常交接已持久历史与本地WS切点，保留其他功能；允许没有Gateway未持久输出的实时流，显式区分该输出流可用性，不伪造idle、完整Gateway实时输出或成功完成。当前WebSocket持续连接时，Gateway Turn结束后服务端必须及时主动通知并驱动当前Web UI自动读取／显示新增持久历史，无需用户手动刷新。**此要求替代此前接受不主动推送的约定，以本次为准。** 复用既有原生完成／租约释放点、同Profile失效信号和`sessions.changed`连接，按当前页面有界范围重读，不广播全库历史、不新建独立WS、不发送模型消息凑恢复。此变更不扩大Android正常完成通知资格，历史更新信号不能冒充正常完成回执。

**用户2026-10-24确认：Conversation侧栏展示缓存。** 页面冷启动、刷新后及断线期间，先展示上次成功获取的Conversation列表快照，不必等请求或Socket就绪；保持跨Profile列表及各行真实owner归属。网络恢复仍完整读取列表，结果到达后原地更新并更新缓存，不做Timeline式衔接动画，也不先清空列表造成闪烁。缓存只承担过渡展示，不作为置顶、归档、删除或Turn运行状态的实时事实，不改变后端权威及既有列表分页语义；首次请求未完成不能仅因缓存缺失就显示“No conversations yet”。与下方Timeline及底部两个卡片共用展示缓存边界，尚未实施。

**2026-10-19 recovery implementation:** merge repeated list invalidations per owner, publish each Profile's successful page without waiting for another Profile, and cancel obsolete downloads. Optional `summary=true` on the existing session list/detail reads omits heavy provenance/configuration blobs; default callers retain their complete existing response. Current Conversation titles may use the owning native binding's `info.title` and authoritative title events/rename responses while the list is unavailable; stale list results cannot roll them back. Missing stored locators must still be verified read-only before a potentially restoring resume.

**User-confirmed sidebar restoration (2026-10-13, R2-C80):** Retain the approved Mock's Sidebar separators, including between Files and the theme controls. Organize real Sessions by their actual update time into mutually exclusive Today, Yesterday, previous 7 days, previous 30 days, and older groups. Restore the real-page presentation; do not substitute a single generic Conversations section for the approved grouping. Missing native timestamps must not be invented. Turn activation or completion must not cause whole-list flashing. Keep the list scrollable while hiding the visible scrollbar, and preserve the approved Mock separators and compact theme-control layout.

**User-confirmed Pin interaction (2026-10-17).** Place a Pin section between New Conversation and Today; hide it when empty and no drag approaches it. Long-pressing a Conversation lifts its card while temporarily retaining its original slot. Dragging upward toward New Conversation opens/expands the Pin area and reserves a drop slot; releasing there pins the Conversation. Multiple pinned cards can be reordered using the same long-press drag gesture. Pinned Conversations belong to that section instead of being duplicated in date groups. This explicitly replaces the old activity-only ordering/custom-drag exclusion in §2.6. The user has assigned implementation of Pin presentation/dragging to another Agent; this bug-fix task must preserve its concurrent changes.

### 1.4. Timeline, streaming, message kinds and timestamps

**用户2026-10-26明确：重连与持续连接的滚动行为分开。** 断线重连完成后，只有正式恢复确认 Turn active（接入当前流式输出），或证实当前视口已不在未变化的公共前缀内，才回到底部；idle 且前缀兼容时保留原消息锚点及屏内位置，即使没有新历史也不得滚动，Disconnected 消失及附属读取／迟到回调均不是回底触发。未知前缀不能当作已变化。此条覆盖下方旧“前缀兼容即快速滚到末尾”的宽泛描述。持续连接时沿既有用户滚动规则：离开底部立即暂停跟随，每次手动滚动重新计时；停止操作20秒后仅当 Turn 仍 active 才回底恢复跟随，到期 idle 则始终保留位置，不在随后自动 Turn 开始时补触发。用户主动回到底部立即恢复，用户 Send 被正式接受仍回底；恢复行为不能与普通手动等待计时混用。Composer 达到最大自适应高度后的内部输入／滚动不得导致 Timeline 闪动；保持连接时正式用户消息、Thinking、工具和模型流式输出须及时呈现，不能只有 Stop 状态并等 Turn 结束才交接。

**用户2026-10-26现场补充：** Composer满高输入引发Timeline闪动发生于Android Chrome移动端网页版；软键盘本身没有移动，屏幕上的区域划分稳定。不能把该问题改述成键盘升降或Composer／Timeline区域高度抖动，也不能以桌面窄窗口几何稳定宣布真实移动端绘制问题关闭。

**用户2026-10-24追加：渲染驱动的统一恢复提交点。** 冷启动／刷新及重连恢复期间，保留现有／缓存画面，REST与Socket在后台恢复；不能各自先到就单独替换对应可见投影，也不能等全部历史读取完毕才开始对账。同步条件由当前实际展示内容及维持其身份／顺序／正确性所需的数据依赖决定：前端须跟踪当前可见Timeline范围、已展开内容和其他当前呈现组件所依赖资源的本轮就绪情况，而不是仅查看某个整页Promise或Socket connected。该依赖集的历史／读取结果就绪，且Socket／活动Turn恢复至可确认边界并完成历史／事件对账后，一次提交连贯的可见投影，再执行已确认的前缀滚动衔接和卡片数据变化动画。单纯等待两个Promise完成不能代替一致性校验；具体边界及对账机制须依据现有消息身份、epoch和事件恢复契约设计，不凭请求完成时刻假定服务端原子快照。

当前不展示的已安排读取可异步完成，不阻塞本次可见交接；更早历史、未展开详情仍沿既有按需语义，不因此全量下载。滚动、展开、切换页面／owner时重新确定展示依赖并校验就绪，过时结果不得满足新依赖；不能因隐藏内容慢而冻结当前可见界面。恢复期间Socket新事件继续有序接收／暂存和对账，避免丢失、重复及旧历史覆盖新输出；恢复边界不要求等待Turn结束或等待事件流永久静止，统一提交后恢复正常流式呈现，不给后续每次delta增加REST屏障。可见恢复完成与后台读取全部完成分开定义；APK5秒恢复成功条件对应当前可见依赖和Socket／Turn恢复就绪，未展示内容的慢请求不单独触发整页重载。本条细化并替代下文“请求返回即接管／全部读取完成”的宽泛表述；普通恢复之外的正常卡片更新仍按各自有效数据变化轻量动画。当前只确认交接语义，具体机制尚未实现。

**用户2026-10-24澄清“全量快照”的读取范围：** 采用当前页面所需状态快照；Conversation正文及会话状态只读取页面上当前打开的Conversation，不下载其他Conversation正文或逐一激活其runtime。即使是当前Conversation，也不要求下载全部历史，只读当前页面需要的分页范围，早期历史与折叠详情保持按需加载。Conversation侧栏独立读取列表摘要，不等同于读取列表中每个会话的正文。通用恢复原则要求上述范围内该重读的资源完整覆盖，不扩大数据下载范围。

**2026-10-15 用户确认底部留白：** Conversation Timeline 底部 padding 与 scroll-padding-bottom 统一为用户最终指定的 **64px**，避开 Secretary 悬浮球并保留正文间隙；替代此前试调的 52px，不改既有滚动跟随规则。

A Conversation has **one** Timeline. It includes the original ordered persisted messages, the live assistant stream and temporary pending-steer *visual* bubbles as a distinct non-persisted tail projection. No extra composer-level Queue card, separate In-flight panel or second transcript is permitted.

**用户2026-10-19确认：历史分层加载。** 保持当前首屏200条及已有分页语义；先读取普通可见正文、Thinking/工具卡外侧的真实名称、状态与身份，折叠正文、工具参数和结果随后受控分批补齐，用户展开优先。未加载、读取失败与真实空正文必须区分，失败可显式重试；切换会话取消失效详情请求，不抢占当前会话读取。不合成历史；原“只保留内存、不新增持久缓存”限制由下方2026-10-24确认的过渡展示缓存边界补充替代。

**用户2026-10-24确认：本地缓存仅作过渡展示。** 页面冷启动、刷新页面后、断线期间，以及历史请求与网络连接恢复就绪之前，先展示本地保存的快照，避免加载空窗；范围包含Timeline、Conversation侧栏列表以及底部UsageSummary／ContextIndicator两个卡片。不做复杂双端状态同步，不以缓存减少请求，不改成基于缓存的增量历史请求。每次仍按既有完整历史读取流程获取服务端内容，保留既有首屏／分页契约；服务端内容返回后接管展示并更新缓存，不能用旧快照复活已删除或rewind掉的消息。缓存按服务端和真实Profile／Conversation归属隔离，不能借其他owner的旧数据填充当前页面。Turn active时，Socket重连握手后还须通过正式状态恢复／事件回放对齐当前流式输出；缓存不是运行状态、事件游标或历史事实源，不得把旧快照当作已经恢复完成。此处确认产品边界，不代表缓存已实现；缓存载荷、容量和交接机制的正式技术方案见§1.4.1，仍待实施与验证。

**用户2026-10-25明确：Conversation切换的首帧。** 从一个Conversation离开后切回，第一帧就应显示该owner离开时已有的正文及阅读位置，不能先显示空Timeline／只有Load earlier messages，再等草稿、本地缓存或服务端返回才补正文。此要求对idle及active Turn相同；缓存的首要目的是避免空窗。暖切换保留内存内该owner的展示与阅读锚点，不扩为持久化滚动位置；快速滚动仅负责缓存状态到本轮真实状态的衔接，不能以最终动画存在代替首帧连续。仍按原契约完整读取、隔离owner、失效旧轮次及按真实结果处理rewind／删除；从未有可用展示缓存的会话不伪造正文。

**用户2026-10-26明确区分两层。** 同一document的内存视图负责视口显示状态、阅读位置、展开及临时展示的保留和快速切换；已有可用的同owner内存视图时，直接展示它，不走持久缓存的展示读取路径。持久缓存是跨document生命周期的本地快照，用于刷新／冷启动后先显示内容；只有缺少可用内存视图时才作为该过渡来源。真实已确认空会话的内存视图与尚无画面的空loading必须区分，不能借旧磁盘内容复活空会话。两层都不替代后台完整恢复或提供动作权限；服务端真值确认后，仍沿既有契约更新持久快照。不能把内存切换加速当成持久缓存冷启验收，也不能把两层统一称为已完成缓存交付。

**用户2026-10-24追加确认：缓存到真实 Timeline 的视觉衔接。** 真实历史到达后，比较缓存展示与真实Timeline的最长公共前缀；比较仅用于视觉衔接，不改变全量读取或引入双端同步。若当前缓存视口显示的内容处于未变化的公共前缀内，接入真实内容时保留该视口的消息锚点与屏内位置；按2026-10-26最新口径，重连确认active才快速衔接至真实Timeline末尾，idle保留位置；禁止先清空再重绘、瞬间跳到底部或以重新挂载制造刷新感。前缀判等须包含消息身份与实际展示内容，不能只凭ID相同就认定未变化。若当前所见内容不在公共前缀内（例如另一客户端已经rewind），允许按真实结果重新呈现及定位，不要求伪造连续衔接。无位移则无需制造滚动；Turn active时仍沿正式恢复接入当前流式输出，不能为动画推迟或遗漏真实状态更新。动画的内部技术默认与实现计划见§1.4.1，尚未实施。

**用户2026-10-24进一步确认：完整重请求属于Web UI通用恢复机制。** 网页与APK断线重连后均重新执行当前页面所需的完整服务端读取，覆盖初次刷新会获取的有效数据；不得仅连上Socket、补事件或因旧内存／binding存在而跳过应重读的数据。完整重请求不改变已有历史分页和详情按需加载范围，也不全库扫描所有会话。恢复完成须覆盖本轮请求结果及Socket／活动Turn状态恢复，不能仅以connected或旧缓存就绪作成功依据。保留已有页面和阅读位置，按上方前缀契约交接。APK回前台另有新的5秒恢复窗口要求：先保留页面，窗口内本轮网络读取及Socket／Turn恢复完成则不重载，超时由原生兜底；本条替代§1.2中旧的回前台立即刷新口径，不给普通网页新增5秒强制重载。前端缓存及交接逻辑共用于网页／APK；APK前端资源内置，须重打包安装后生效。当前仅确认机制与调查，尚未实施。

**架构原则与扩展契约（用户2026-10-24确认）。** 目的在于减少用户手动刷新或APK自动整页重载：任何页面打开／冷启动及断线重连，在网络可用、读取成功后都应自动收敛到服务端最新状态。初始读取与重连恢复必须共享完整的页面数据覆盖；新增请求必须同时接入两条路径，不能留下仅组件mount或整页刷新才重读的数据。范围包括当前页面依赖的Profile／配置、侧栏列表、会话历史、Usage／Context、Secretary／Schedules／Pending／Compaction及当前已打开的Files目录／预览、详情等既有按需读取；不因此提前展开或下载尚未需要的内容。恢复须有本轮owner及完成／失败边界，不能把发起请求、吞掉异常、旧结果或Socket connected当作全部成功；切换页面／Profile、再次断线及服务epoch变化使对应旧结果失效。读取与活动Turn恢复协调，不能丢失／重复新到输出，不自动重放发送或其他写操作。新增读取的验证须覆盖无整页重载的重连后数据更新及失败恢复；通用约束同时记入AGENTS，不依赖某轮任务看板提醒。此为实施契约，现状不因文档确认而自动视为符合。

实现采用已有`GET /api/sessions/{id}/messages`的可选`view=cards`；每条真实消息用`deferred_details`标记省略的折叠字段，普通可见正文与UID/row ID/顺序保持。详情用同一路径的`detail_row_ids`（最多12个真实row ID）返回原完整投影，只允许当前已验证compression spine中仍可展示的行；过时详情不能复活rewind行或覆盖另一会话。默认不传参数时原响应完整。`display_tool_status`仅携带从原结果计算的已有卡片状态，不从缺少正文推断成功。

本端及跨客户端的普通user消息以成功持久化点的真实row为依据：Web idle回执可选`accepted_user`与可重放`message.user_committed`事件同形，含`stored_session_id`及`message`（真实`row_id`、`message_uid`、role、content、timestamp和可选display字段）。接收后可立即呈现，不等待Thinking、整页历史或Turn结束；按正式身份去重。没有真实持久化依据不发该字段/事件，旧客户端/后端保留既有行为，原生`prompt.submit`行为不变；已接受后辅助历史读取失败不得变成发送失败或自动重发。

| Rendered source | Timeline semantics | Default rendering |
|---|---|---|
| Real ordinary User Message | One actual persisted user message with original content/metadata | User bubble, no avatar; native timestamp marker stripped only from UI presentation. |
| Real Assistant Message | Native persistent message / streaming continuation | Assistant content without avatar; rich text, code, accessible links. |
| Thinking | Model thinking stream, subject to actual available event segments | **Expanded while actively streaming**; auto-collapsed on completion; user can toggle. |
| Tool Call | Native tool call/arguments, activity and result | **Collapsed by default**, including during execution; show a visible working status, expandable parameters/results. |
| Framework Message | Genuine durable `<framework-message>` carrier | **Distinct message visual form within the Timeline**, not a toast, sidebar status or generic Assistant claim. |
| Process completion notification | Native `display_kind=process_complete`, excluding Noting Framework carriers | Independent notification card using the Framework Message theme; exact title **process complete**; collapsed by default, expandable to show the complete report. |
| Async delegation completion notification | Native `display_kind=async_delegation_complete` | Independent notification card using the Framework Message theme; exact title **async delegation complete**; collapsed by default, expandable to show the complete report. |
| Instant Reminder | Genuine `<instant-reminder>` user-role carrier | Distinct Reminder treatment, collapsed by default; not misattributed to a typed user message. |
| Deferred Reminder | Real native `<deferred-reminder>` message when actually projected in visible history | Collapsed by default, distinct from instant reminders; never fabricate one for a merely scheduled/pending occurrence. |
| Compaction | Real native summary/handoff carrier as projected by backend | In correct historical position, **collapsed by default**, full original available on expansion. |
| Pending Steer | Server-accepted, still-unconsumed correction | Separate provisional User-shaped bubbles at visual tail; no timestamp implying persistence. |
| Human-only `/notebook` result | Slash result intended for human viewing only | Temporary **Assistant-styled** result in the Conversation Timeline, anchored at the sequence boundary when the command is invoked; later messages follow it. Keep this display only in browser working memory; reload clears it. Until that memory is reset, preserve its invocation-time Timeline position across later messages and history updates; do not relocate it to the tail merely because an anchor was reconciled. Render the public human output as readable sections, entry states, fields and schedules; do not show internal Anchor metadata. No durable message identity or next-model-history insertion. |

**2026-10-15 用户确认完成回报的前端身份：** 上述两类通知按后端 `display_kind` 分类，前端使用独立通知 kind 和 system 角色，不能仅换皮后仍识别为 User Message；不使用用户气泡、用户消息动作栏、Reply／编辑入口或用户附件解析。原生 source 的 `role=user`、正文、UID 及数据库记录保持原样用于历史定位，不改变模型输入。Framework／Reminder 的既有包装优先识别，`display_metadata.noting_run_output=true` 不转换为进程完成通知，Noting Framework Message 的标题、主题及折叠行为保持不变。不以英文正文或 `display_text` 猜通知类型，固定标题不以任务摘要替代。

**2026-10-15 用户确认 `/notebook` 时间标签：** 前端临时 Notebook 卡片的时间标签使用 `Updated at`。时间值继续来自当前有效 Snapshot 在原生人类输出中的 `Created at`，仅调整界面文案，不修改后端响应字段、存储或时间语义。

**2026-10-15 用户确认 Thinking 展示保持现状：** 继续流式展示后端实际提供的推理文本或推理摘要，不因 GPT 等模型原始思维链不透明而隐藏其可见摘要或替换为「该模型思维链不可见」等固定文案。此前固定文案要求（前端 ISSUE-009）已由用户取消，不为该需求新增加密识别或接口。保留流式时展开、完成后自动折叠及用户手动展开的既有交互；内容仅以实际可用事件为准，不保证上游持续提供摘要。该取消不影响打断状态、缺段、状态闪烁等既有缺陷修复。

**2026-10-15 用户确认 GPT Subscription 路径与摘要分段：** GPT Subscription 指 Hermes 的 `openai-codex` Provider，使用 ChatGPT／Codex OAuth 订阅认证，经 `codex_responses` 模式调用 Responses API。摘要请求、接收、流式传输与段落分隔直接复用 Hermes：推理开启时请求 `summary: "auto"`，上游摘要增量经既有回调和 `reasoning.delta` 进入前端 Thinking；Responses 摘要的 `summary_index` 变化时由 Hermes 插入 `\n\n`。前端按收到的文本顺序拼接并正常渲染 Markdown，保留已有空行，无需额外补换行，不按每次回调强行分段（回调可能只是一个摘要段的文本碎片）。此结论限定上述 Responses 路径，不泛化至所有第三方兼容接口；源码依据见 [Provider 路由](../hermes_cli/runtime_provider.py)、[摘要请求](../agent/transports/codex.py)、[摘要流与分段](../agent/codex_runtime.py)。本次核对未发起真实订阅请求，不作为运行验收通过证据。

**Timeline time presentation contract:** Human-friendly date/time labels appear **only as Timeline reading aids** and **outside every message bubble**. They need not precede each message. The visual AI chooses ergonomic grouping, density, reveal timing, relative-vs-absolute style and placement; no per-message prefix rule is imposed. `<timestamp>ISO...</timestamp>` in ordinary native user-message content MUST be hidden from rendered text without modifying source data; grouped/merged Steers do not cause artificial timestamp rows. **2026-10-14 user clarification:** Reminder carriers remain collapsed by default; their inner timestamp is preserved on expansion, with no additional wrapper or timestamp-stripping treatment.

Message ordering, Compaction lineage, framework carriers, UIDs and stream insertion are backend facts. Do not infer message kind from English content text; identify authoritative native wrappers/projection metadata. Use event/source timestamps accurately, format locally, and avoid manufacturing message creation times for temporary UI nodes. Long histories initially load 200 backend messages and load 200 more per Show More History action, counting native tool-call/result rows; they remain scroll-anchored; a reader examining older messages MUST NOT be forcibly jumped to the bottom by new live content. Streaming content expands **before** the Pending Steer tail. Streaming presentation must follow real native progress without an artificial playback speed cap or a growing backlog of already-completed output. Reuse the mature interaction/rendering foundation while preserving the user-approved custom visual layer. With a live WebSocket connection, a materialized Instant Reminder must become visible at its native position promptly, without waiting for the resulting Turn to finish or allowing later Thinking to appear while that triggering row is still withheld.

**2026-10-18 user-confirmed background-Turn observability:** Whether a Turn is initiated by the Web UI or by a background Instant Reminder, opening the Web UI at any point MUST recover its true running/terminal state and complete available Timeline, including the triggering carrier, provided Thinking/reasoning, tool calls and their current/results states, and assistant output. Already connected viewers, first attachment during execution, reconnects and opening after completion are distinct required cases. Restore a consistent current-Turn view and then continue live events without gaps, duplicates or Profile-owner confusion; a bounded replay ring alone is insufficient when its earlier events have expired. Global Conversation state must initialize on connection and update for background work without opening or activating every Conversation. Reuse the existing session lifecycle, history/output projection, replay and global broadcast mechanisms; do not introduce a separate event store, scheduler or WebSocket service. Quiet follow-up does not authorize suppression of execution facts. This paragraph records the required behavior, not a claim that implementation or deployment validation is complete.

**2026-10-18 user-confirmed presentation baseline:** The user has completed the UIUX polish. Final state/recovery wiring MUST preserve the user's latest layout, styling, animations, Profile icons, Pin/drag interactions and scrolling behavior. Reuse existing presentation components for necessary status visibility; do not redesign the interface or overwrite/inadvertently include the user's unrelated changes.

**2026-10-21 用户确认 Timeline 中断与宽度：** 中断回执中的非持久取消说明不作为 Assistant 正文新增或覆盖输出；保留实际输出的正文、Thinking、工具状态以及已有 `turn_terminal` 历史投影位置。System 卡片左右边缘与 Assistant 阅读区对齐，`System ·` 标签与短正文同行；长正文仍可自然换行，不截断。Compaction 卡片左右边缘与加载历史按钮对齐，比 Assistant 阅读区更宽，仅调整宽度，保留既有底色、边框、图标、圆角和折叠交互。加载历史入口保持现状。

**2026-10-23 用户确认微信正文与Redirect：** 保留原生Redirect及hidden空占位，不改变Thinking留存或Timeline排序／渲染机制。微信Turn active中每条完整正式Assistant Message应及时投递，包括工具前正文，不等待Turn结束后仅发送final尾段。Redirect取消正式正文生成时，已收到且尚未外发的半截正式正文合并进对应同一条Redirected通知；已发送正文不重复，完整消息、合并通知、纠正后回复保持实际顺序。无正式正文时保留既有通知与空占位，不把Thinking当正文发送。模型上下文及持久化继续使用原生事实，不把渠道通知文案写成模型回复。

**同日用户最终确认来源包裹保持：** 用户取消此前提出的前端来源包裹显示适配，保留上游Gateway JSON来源说明、现有追加逻辑及Web显示；不新增剥离适配，不改模型可见来源／数据库原文。本项目正常微信输入的XML仍仅进模型`api_content`，持久`content`保持用户正文，沿现有路径不变。

**同日用户补充的分类边界：** 失败／中断提示卡片化仅针对具备明确失败／中断提示身份的消息，不把“后端生成的内容”整体视为状态卡片。slash命令返回继续遵循现有临时输出契约（含`temporary`／`command`的样式、生命周期和位置），不转换；模型实际回复及中断前真实部分回答保持正文表现。不得仅因整个Turn为interrupted或正文包含诊断用语就改变消息类型。

**同日用户确认Heartbeat卡片：** 用户已确认浅色／暗色实际效果，沿下述样式落实。最新收敛仅调整这一条Heartbeat消息的卡片展示，其它消息与行为保持；不增加结束标记处理。对后端原生`role=user`且完整`<heartbeat>…</heartbeat>`包装的消息使用独立Heartbeat表现类型；source角色、原文及UID不变，前端不合成消息。沿Reminder／Framework同类卡片结构与阅读宽度，默认折叠、外部固定标题`Heartbeat`，使用心电波形图标与低饱和陶土橙色线／浅底，兼顾暗色主题；展开保留内层timestamp和原始正文／Additional prompt，仅隐藏外层heartbeat包装。不显示普通用户Reply／编辑、附件或额外外部时间标签。普通文本提及、Assistant引用和无包装的旧原生英文模板不猜测分类；`HEARTBEAT_OVER`不触发额外静默、调度或过滤行为。后端模板及全局Noting分支／UI唤醒契约见07 §8.15。

**同日最终确认的失败提示展示（覆盖前述保留派生提示卡的口径）：** 对实际消息行的`display_kind=failed_turn`复用原`Turn interrupted`派生卡片外观，与Assistant阅读区对齐，只显示该行原文，不加`System ·`或其它标题／前缀。后端仅在明确生成取消诊断的分支为其落库消息设置既有`failed_turn`类型，不能以正文匹配或整个Turn中断为由标记模型回复。取消从`turn_terminal`额外派生`Turn interrupted`／`Turn failed`提示卡，即使没有独立提示行也不兜底合成；元数据用于真实部分输出、Thinking、工具的恢复、状态和去重功能保持。旧历史无类型行不自动猜测或迁移，slash返回完全保持现状。

**同日用户要求审批弹窗排版修订：** 在保留现有主题和审批交互语义的前提下，改善移动端approval提权弹窗的信息层次、长命令／路径排版、文字与按钮布局，同时兼容桌面端；以实际前端组件分别提供移动端和桌面端截图。`once`／`deny`等原生choice及授权范围、关闭行为不变，不改变Clarify问答交互。

**同日用户确认Patch replace审批diff：** 仅前端复用已接收的当前工具调用参数，为Patch replace模式提供审批前拟修改片段的差异渲染：路径、old_string、new_string及replace_all；新字符串为空时按删除展示。不得为此新增后端接口／diff字段，不将预览冒充执行后真实diff或完整文件。不扩大到V4A或write_file。审批只展示能与当前owner／当前待处理调用唯一对应的参数，不拿Terminal或其它调用参数猜测；缺少完整参数或存在歧义时保持原审批、选项与流程，不额外阻断审批。模型参数按文本转义显示，保留原文；非Patch审批及Clarify表现不变。

**用户2026-10-26追加确认：统一连接／恢复状态。** 先调查当前恢复回归，再设计状态提示，不得无证据归因于网络。聊天页所有连接、初始恢复、读取重试状态统一放入 Composer 底部原 Hermes disconnected 的位置；移除页面其它位置的同类网络状态横幅。该位置是单一固定高度、宽度随 Composer 的单行状态区，任一时刻只能显示一条，状态改变原地替换，不堆叠 Notice、不拼接两条、不换行。Socket 握手成功不能冒充页面恢复完成：须如实表达当前是否可用、是否需要等待及等待对象，覆盖当前页面必要数据与活动 Turn／流式恢复；不得静默功能失效，也不倾倒协议／内部错误。正常后台读取不反复打扰、不把已可用正文重新冻结。Noting 缺失优先查实际回归，不以额外缓存掩盖。用户已确认三种可见模板：`Connecting to Hermes…`、`Restoring {对象}…`、`Retrying {对象}…`。对象使用有限短名称（如history、live updates、Noting、settings），不暴露接口名／原始异常。超宽省略号截断；多个实际等待对象可每3秒轮换一个，已完成立即退出轮换。仅慢不报错，确实失败且自动重试时才用Retrying；恢复过程不经顶部Error／横幅／Toast。全部满足本轮恢复条件后隐藏，不额外弹Connected。实现及验证状态见CLAUDE。 用户进一步确认：恢复期间状态行持续存在；恢复提示消失即承诺当前页面应恢复的数据／实时状态已到位且合法操作可用。Composer 主按钮因恢复而不可操作的判定与该提示同源，不允许提示消失后仍静默缺功能或被恢复门禁拦住。恢复过程中已取得的正文可提前展示，草稿输入保留；正常连接下后台刷新不反复重新锁定主按钮，不扩大到隐藏功能预取或每次操作重新完整恢复。 HTTP／REST读取与Socket握手、可独立进行的状态恢复保持并行，只对真实数据依赖等待；界面状态不是请求串行步骤。复用现有单一恢复owner／结果／提交机制，集中派生恢复提示与操作就绪，禁止另建重复状态机或在组件／动作处散落追加防御门禁。

**用户2026-10-26追加确认：Noting显示与弱网读取。** 先完成当前恢复状态修复及验证，再优化Noting。悬浮球的显示资格只由当前Profile的全局Noting开关决定，与实时连接状态解耦；已确认全局开启后，断线／重连、会话参与开关、任务是否运行或详情读取失败均不使球消失。当前Profile开关尚未确认时不能以Socket connected冒充已恢复。Noting状态保持实时，不新增持久缓存；数据只按实际可见范围获取，悬浮球只取必要状态，展开后才取对应详情，收起后不为隐藏内容持续重复读取，减少弱网下对实时输出带宽的争抢。此条覆盖此前把完整Secretary状态都作为默认展示读取／持久缓存的冲突口径；运行状态与完成信号保持真实，不以减少读取丢失变化或伪造idle。实现状态见CLAUDE。

**用户2026-10-26追加确认：排期列表有界返回。** 结束超过24小时的排期，后端不返回条目细节，只返回已隐藏数量；前端在列表底部显示简短英文摘要。过滤在后端查询阶段执行，不先把细节传到前端。已删除排期不返回，也不计入隐藏数量；暂停与未结束排期保留。采用现有真实结束时间，超过24小时才隐藏，恰好24小时仍展示；不能证明结束时间的旧数据不误隐藏。轻量状态提供排期计数，完整可见列表只在用户展开时读取；既有Scheduler写操作和模型工具列表语义不变。

**2026-10-25用户追加界面要求：** 移除页面顶部灰色`Syncing conversation…`及黄色`Conversation updates unavailable. Retrying…`同步／重试横幅，后台自动恢复、状态验证及重试继续执行；不由隐藏提示假称恢复成功。真实会话不存在、Profile不可用及操作／连接失败按各自已有就地反馈处理，不恢复这两条顶层横幅。聊天时间线保留滚轮、触摸及键盘滚动能力，但隐藏右侧可见原生滚动条，不为它保留固定gutter；侧栏既有隐藏滚动条规则保持。

#### 1.4.1. 页面恢复、过渡展示缓存与统一交接实施方案（2026-10-24）

**本节为6.1恢复机制的产品契约，执行版本、发布状态、独立报告的覆盖及交付边界以根CLAUDE和运维记录为准；历史final-delivery.md仅对应当时交付，不代表后续修补仍未上线。** 动态进度与最终结论以根CLAUDE及本轮`.autonomous/20261024-web-recovery/`为准。以下未来语气保留定稿时的计划语义，不表示当前尚未启动；原冻结方案可从`ba83d2b`读取。本节由独立Astra方案审查后形成，此后不再调用Astra。产品定义沿§1.3、§1.4及§1.13，不改变5秒硬兜底、滚向真实末尾或完整重读范围。结构、参数、容量、锁序、分包为内部技术决定，不冒称用户逐项指定；原代码基线为前端`f3a03ce32c0dd1e96719da210716caa2c1c7b8d4`。

**用户2026-10-25补充确认的交互文案：** 产品界面统一英文、短句、易理解和观察；用户访问目标确实无效／不存在时明确报错；持续网络／读取故障也须在对应区域解释原因和重试状态，不能完全隐藏。连接恢复、暂时读取失败等软件内部状态自动恢复，保留内容、输入与操作意图，必要时只显示轻量更新／等待状态；不弹协议错误、不因临时状态拒绝操作、静默跳转或增加用户门禁。用户创作的正文、会话标题和Profile名称保持原文。

**用户2026-10-25确认的体验修复口径（覆盖本节冲突处）：** 历史与Socket／当前Turn必须仍取得相容证明后统一接管；Usage、侧栏、其他Profile列表等附属读取失败只影响其局部展示，不把已核验正文一同冻结或强制整页刷新。附属读继续按同owner／当前轮次自动重试，失败不得冒充新真值；缓存保留已显示的同统计视图有效值，unknown或失败不反写覆盖。错误后的滚动／侧栏等需求变化不能取消后续自动恢复。真正冷启动／断线重连保留原衔接契约，普通失效通知／其他会话变化不得因此抢走用户阅读位置或恢复自动跟随。Conversation明确不存在、Profile明确不可用应在原路由解释并提供用户选择入口，不静默跳New Chat；已正常呈现此类终态时APK停止恢复重载。明确离线时保留当前页面等网络恢复，不循环重载；JS心跳真正挂死的兜底和正常5秒恢复窗口保留。范围由Web会话主导修复、验证、前端部署及0.1.7交付，不自动扩大成后端改造。

**目标和非目标。** 页面打开、刷新、初次失败后恢复、连接重建、APK回前台均经过同一个恢复入口；保留可读旧画面，重读当前需求，取得可证明相容的历史／事件投影后交接。浏览器不新增自动整页重载。不会建立通用增量同步协议、持久事件日志、客户端SessionDB、BFF、新Conversation生命周期或全库扫描；不回放写操作，不为这轮工作重写通知或发送受理机制。服务端各独立资源不承诺同一物理瞬间的全局事务；这里的“一致”是owner相同、历史覆盖可证明、Turn输出无缺口／重复、失效与新事件有序收敛。

**实际基线。** Controller已有历史完整重读、binding、epoch、回放和UID对账；`session.activate`已有`state_snapshot`，快照和seq共用replay lock。RenderStore只是渲染合帧。REST页未携范围证明，`events.since`的数组与latest_seq分开取锁，部分reader吞错，Files和展开状态在组件内部，APK以connected取消deadline；这些不能直接组合成新恢复完成条件。复用原投影、typed output身份、提交受理、详情批次和阅读owner；增量补齐下列接缝。

**R1 · 单一恢复owner与结果契约。** 新增前端`core/page-recovery.ts`，Controller持有唯一实例；页面／组件登记需求，不各自创建整页恢复循环。

- `pageOwner = { serverOrigin, profile, screen, storedId? }`；Conversation的storedId为当前路由locator，另存服务端确认的`conversation_ref`／compression tip映射，不以runtime ID作缓存主键。Files的resource owner固定`FILES_PROFILE + root + path + preview`，与聊天Profile分离。
- `documentId`在每次JS文档启动生成，仅内存；`connectionId`在每次真实WS建立时递增，即使同epoch也不同；`epoch`沿现协议。`recoveryId`在启动／重新恢复时递增，兼作请求取消与提交代次。`demandVersion`仅在当前展示依赖实际变化时递增。资源请求只另有自己的requestId，不再增加平行的全页代次。
- `ReadResult<T> = { owner, recoveryId, requestId, coverage?, status: 'ok'|'error'|'cancelled', value?, error? }`；合法空数组、合法unknown数值、已确认404／不可用Profile分别是带明确语义的ok结果或路由失效结果，不以truthy判断。失败后保留的展示数据独立标记`retained`，不能转成ok；取消不能以resolve空值满足依赖。既有公共reader签名可保留，由内部adapter提供该结果，禁止从Promise fulfilled反推成功。
- 状态为`retained → reading → reconciling → committed`，失败为`retryable-error`，owner／连接过时为`cancelled`。读取中保留画面，业务控制状态可以更新为unknown／不可操作；错误不自动当idle。网络可用且上次可见读取失败时自动重试，前台按1／2／5秒封顶重试，断网或隐藏时暂停；新恢复触发立即尝试，不依赖下一次gateway.ready。相同owner／同连接的并发触发合并为一次运行和一个dirty标志，不能不停abort重启。
- owner切换、再次断线、epoch变化取消不适用请求和本轮提交资格；仍需保留的后台事务由既有发送／审批owner继续管理。正常delta不递增recoveryId。恢复完成后的滚动／展开是局部需求读取，不把整页退回冻结状态；恢复提交前的需求变化重新求当前集合，保留仍有效结果。
- `readyForDisplay`只在当前需求全部成功、历史／流恢复证明有效并完成React该次提交后成立；`backgroundSettled`另记，不参与APK5秒成功条件。写操作回执、审批撤销、断线失效和通知观察继续同步处理，不能通过暂停真实事件消费保持画面。

**R2 · 选定的最小后端增量：有界范围读＋既有activate恢复封套。** 不采用“REST／WS各等一次”方案，也不新增服务端长期快照库或DB schema。增加纯读sibling `hermes_state_recovery_view.py`、`tui_gateway/recovery_view.py`；既有REST与RPC薄接线共用前者。

| 接口增量（均可选，旧调用完全保持） | 精确定义 |
|---|---|
| `GET /api/sessions/{id}/messages`的`recovery_view=1`、`anchor_uid`／`anchor_row_id`、`before`、`after` | recovery页可围绕任意仍可展示的消息定位，不能照搬现有仅human prompt的`/messages/around`。默认仍latest 200、单页最多500；不与旧offset或detail参数混用，冲突返回400。每次回完整所选cards窗口，不接受缓存版本来省略正文。 |
| 同响应新增`coverage` | `{version:1, profile, requested_id, tip_id, lineage, window, digest}`；window含首／尾逻辑身份、前驱／后继、是否真实首／尾、逻辑顺序坐标、实际返回范围。digest为规范cards展示字段及身份／顺序的SHA256，排除临时URL、请求时间；折叠正文不进入cards digest，已展开字段另有detail digest。coverage只在本轮内存有效。 |
| `session.activate`可选`recovery_view` | `{version:1, stored_id, profile, windows:[{selector, receipt}], details:[row identity…]}`。selector为latest或有界anchor范围，receipt必须来自本轮已完成的完整REST读取；默认最多两个窗口（当前视口窗口、最新页），单窗口≤500，detail沿12行批次。超出时分有界需求批次，不静默裁掉可见行。 |
| activate响应新增`recovery_view` | 返回owner、epoch、stream cut、各窗口`matched`或该窗口**完整替换**cards、所需详情与范围证明、当前运行状态及`state_snapshot`、`complete`／明确失败原因。matched只表示服务端本次重读与receipt一致，不能由前端缓存自行确认；不匹配返回整个所需窗口，不发送行增删补丁。 |
| `session.events.since` | 内部新增原子`read_replay_cut`helper，一次replay lock复制`events / latest_seq / truncated / epoch`的同一切点；锁外解码。原方法名、参数和原返回字段保持。open_requests仍按既有request snapshot规则对账，不谎称与DB共事务。 |

能力由普通`session.resume/activate`响应的可选`recovery_view_version:1`宣告，`LiveSessionSnapshot`同步增该字段；收到后才发送新参数，封套内仍校验version。老后端继续现有读／回放和错误提示，不声称完成新版一致恢复，也不把兼容降级视为本轮交付通过。恢复封套是现有activate已有messages／state_snapshot读能力的有界扩展，不负责创建runtime；第一次只沿现有只读存在校验→resume／activate取得当前唯一binding，不批量绑定其他Conversation。

**R3 · 历史读事务与封套的证明算法。** 选用“有限切点＋有界重读校验”，不引入所有writer必须维护的新revision。`history_version`仅是运行态辅助证据，`rewind_count`只覆盖rewind，二者都不能冒充所有历史变化版本。

1. 纯读helper在**一个显式SQLite只读BEGIN事务、同一conn**内解析真实owner、compression spine、逻辑代表行、范围边界及所需正文；finally结束事务后才做图片引用、Markdown／cards投影。不能串调各自借新conn的`get_messages`来假装同一快照；沿`hermes_state_timeline._snapshot`的短事务模式。SQL复用现有UID退役、display_identity／首次逻辑顺序、active／compacted及branch排除语义；多段lineage先在SQL计算必要身份，再只取窗口payload，不沿当前多段`SELECT *`物化全部正文。旧只读库不得为GET补索引或回填身份。
2. activate恢复helper先完成既有attach，再只持有目标session的`history_lock`，不持有全局resume lock跑DB读取。第一次短读D0确定本轮所需窗口、当前尾界、lineage／rewind计数、相关代表行字段摘要，以及当前Turn的持久起点／实际租约owner核对材料。D0释放DB事务后，在replay lock内复制完整输出快照和切点S，随后释放replay lock。第二次独立短读D1重新核对D0已覆盖区间，并取得**当前完整最新窗口**、可见anchor窗口和已展开详情。所有数据均有界；普通append不要求最后seq停止增长。
3. D0与D1中原有区间的逻辑顺序、代表身份或实际展示字段变化，lineage／rewind发生变化，或当前活动Turn归属失效，均不得交接；返回`view_changed`，前端重读受影响的完整窗口后重试。后端每次封套最多重做一次，前端同轮最多两次立即重试，随后进入可重试错误／既有退避，不能在锁内无限循环到Turn结束。正常文本delta不改持久窗口，不触发该重试。
4. D1相对D0的普通尾部追加不使整轮失败：D1完整最新窗口提供持久真值，S之前的输出来自完整快照，S之后继续从同一绑定的真实事件流接入。若短读间新增量超过本次最新窗口，且与仍需展示的D0窗口不能证明覆盖连续，则返回明确`coverage_gap`并重读所需窗口；不能靠去重猜测没有漏行。未展示间隔依R4保留缺口，不要求为了封套读取全部间隔。
5. 快照中已持久化的节点按UID／真实row／tool occurrence与D1对账：D1有代表行时以该行的已展示字段为准；已退役／rewind的UID不得作为live尾巴复活。对快照涉及、但不在所选窗口内的持久身份只做有界分批存在性／归属查询，不拉正文。未持久化输出只能属于被本次锁内运行态与D1正式Turn租约／起点共同确认的当前Turn；依2026-10-25最新变更，外部owner已接管且本runtime没有其输出流时，只要同owner真实native外部Turn租约可确认且D0/D1稳定，就走正常的持久历史＋本地WS恢复，封套可选`live_output_available=false`明确不含Gateway输出流；不报错／不降只读／不借旧Turn输出。租约有效性及owner以选定数据库快照为准，holder仅作不透明身份比较，不解析PID／渠道／命名格式来决定资格。本地active缺正式输出快照、租约归属冲突或事实不相容等真实失败仍拒绝完整交接。快照缺失仅在原生已确认idle且没有未对账输出时允许；active不得以`inflight.assistant`纯文字回退声称完整。
6. D0、S、D1不是“DB与WS共用一个原子事务”。证明是：D0原有展示区间在D1仍相同，D1补足当前所需持久尾部；S输出的持久部分与D1身份相容，未持久部分有当前Turn依据；S之后的帧完整保留。D1之后新发生的变化属于后继更新，不要求无限追逐。由原子replay cut取得至有限水位B的连续后缀，按`(epoch,runtime,seq)`排序去重后在staging对账，B后的已到帧紧接提交正常处理。不可凭latest_seq跳过尚未收到的帧。
7. 锁序固定为`目标history_lock → 短DB read事务（结束） → replay lock（结束） → 短DB read事务（结束）`，DB和replay lock**不嵌套**；不持锁做网络、图片读取／转换、投影序列化或等待下一事件。不取得SQLite写锁，不阻塞／接管模型请求；目标history lock采用有界等待，拿不到返回可重试状态，不终止Turn。测试须用真实双连接／跨进程写入覆盖D0/S/D1之间的rewind、追加与压缩，不以单进程锁测试代替。
8. 已有`session.info`／Framework／complete等当前历史失效入口全部接入协调器。`sessions.changed`除侧栏外，也对当前Conversation登记一次合并历史重读；不因此读其他正文。补`change_watcher`的`rewind_count`签名，覆盖相同消息数量的undo／replacement；正式原生对当前消息内容的更新若没有现成失效通知，在该writer完成点复用现有变更广播，禁止只因DB任意表mtime变化就轮询全部历史。实现包必须列出本轮涉及的rewind／edit／delete／compression正式writer到失效入口的接线证据；外部直接SQL不作为受支持实时写接口。

该算法在正常持续delta时能取得有限边界；破坏性改写持续发生时可以报告未恢复并重试，不能为了“必须5秒成功”接纳未证明数据。ring截断先用完整快照替换起点，再原子取后缀；缺口可由held帧补齐但必须逐序证明。新epoch、runtime替换、旧document／旧recovery结果全部丢弃；严禁旧cursor跨epoch继续使用。回放期间后继事件仅在投影staging暂存，安全／业务观察仍执行；恢复的副作用去重，不重复toast、完成通知或写入。

入口拆为`observeControl(event)`与无副作用`reduceProjection(event, target)`：前者按已接收seq去重，后者按目标投影已应用seq去重，不能因为业务观察已经前进就跳过staging尚未覆盖的事件。held队列默认上限4096帧／8MiB，超限作明确恢复缺口，取更新完整快照重新建立起点；不得丢帧后报ready。目标history lock单次等待上限250ms，失败释放并交普通重试；DB短事务与大正文投影分别计时，以验收证据核实未长时间卡住Turn writer。

**R4 · 可见需求、覆盖窗口与分页。** `core/history-coverage.ts`管理有序窗口及明确间隔；它是当前页面读结果索引，不是另一个持久历史库。`useTimelineReading`向协调器报告实际视口内第一／最后节点的持久别名和屏内offset；各Disclosure登记已展开的facet及其source identities。只登记DOM里实际可见的详情；已展开但远离视口的正文可以后台重读，进入视口前再校验。read demand来源不依赖新projection已经发布。

- 冷启动从缓存最新窗口或空loading开始，仍请求latest 200；没有缓存不显示已确认空会话。暖恢复按当前阅读anchor有界定位，anchor不在latest 200时另读anchor窗口，不从offset=0逐页追赶到老位置。真值明确找不到anchor才允许刷新感；超时／未验证不等同anchor已删除。
- 每页完整读取，默认200、上限500；按稳定逻辑顺序／身份选择相邻范围，首次最新页后冻结该页尾界用于后续分页。不能把新页offset与旧页offset直接拼接。返回的前驱／后继与已知重叠行用于校验邻接，冲突重读受影响整页；新append只扩展末端，rewind／代表替换按R3失效。旧offset接口继续服务旧客户端，前端新恢复路径使用有界anchor选择，普通“Load earlier messages”接同一helper。
- 保留“加载过”与“本轮已验证”两种覆盖状态；已加载但不可见的旧页后台恢复，不挡当前屏。滚动使未验证页进入视口时，该局部保持旧画面／明确更新中，完成相同owner下的局部对账再采用；不能称旧页已验证，也不能让后台旧页覆盖当前页。收起／离屏解除对应阻塞需求，已经发出的有用请求可后台完成。
- 比较对象是**对齐的展示快照窗口**：取恢复前当前屏及必要相邻节点组成有界窗口，冷缓存窗口最多200行；以真实左边界和逻辑身份对齐后，对该窗口从左到右求最长公共前缀。窗口起点不同先定位同一边界，不能直接数组第0项比较。判等包括可见正文、卡片名称／状态、timestamp和当前已展示facet；未展开正文不参与。恢复期间保留内存中已确认的窗口边界，不持久化滚动位置。该局部结论不宣称整个Conversation前缀已验证。
- 动画终点是本次提交采用的**最新持久窗口＋已对齐live尾部**。深处anchor窗口与最新窗口不相邻时保留明确的分页间隔控制，复用“Load earlier messages”样式／加载语义；间隔不是timeline message，不伪造相邻历史、不把未读取内容画成旧正文，也不自动填满两窗口之间所有历史。动画路径只遍历当前挂载且本轮已验证的窗口与明确的分页间隔；尚未验证的已挂载中间页先转为该分页间隔，保留anchor所在DOM及offset，再开始动画。因而无需下载全部历史来滚向真实末尾。正常相邻页面不新增间隔。
- 当前屏真值已提交后，动画准备与非可见页恢复不影响APK ready；动画需要的挂载区间尚未完成就先保持已恢复的锚点画面，准备好再执行一次，不假报动画已完成。用户主动滚动／展开时以新需求为准；不能在等待时把整页业务重新冻结。

**R5 · 读取登记表与组件接线。** 新增`core/recovery-resources.ts`只集中reader登记和依赖规则，领域读取仍在原模块。`initialize/select/gateway.ready/online/visibility/Android恢复事件`调用同一`startRecovery(reason)`；初始化是否成功、是否已有validatedRoutes均不作为重试资格。route不存在时按正式404退到New Chat并清相应展示缓存，不能resume一个已删除locator。

| 资源／正式owner | 可见提交依赖 | 后台／按需及接线 |
|---|---|---|
| Profile roster／当前Profile有效性 | 当前所有页的owner校验；新聊天Profile菜单实际展示数据 | `profiles.ts`每轮重读；失败保留展示不赋予创建权限。默认cwd在New Chat配置／发送依赖中重读；当前聊天不为无关默认cwd阻塞。 |
| 侧栏摘要／真实标题 | 侧栏可见时其已显示列表范围；当前标题以当前owner有效metadata为依赖 | 跨Profile并发页保留，每个owner独立结果；隐藏侧栏请求后台，展开时读取其本轮必要页。不逐个加载会话正文或runtime。不能用一次first-page替换删掉屏内已加载更早列表页。 |
| 当前Conversation cards／活动状态／stream | 始终是该Conversation当前可见范围依赖 | R2–R4；其余曾加载页后台。没有打开Conversation的New Chat／Files不绑定任意历史runtime。 |
| UsageSummary／ContextIndicator | 当前显示的胶囊字段及已展开详情 | 胶囊显示Session或Latest Turn对应字段；另一视图可后台。沿usage原生失效／retained语义，context_unknown是真值，读取失败不是unknown真值。模型／provider变化先处理兼容失效。 |
| Pending／审批／发送受理事实 | 当前Composer、Pending气泡、审批面板所需状态与可用动作 | 不从缓存恢复；恢复中撤销失效的可操作状态，既有准确受理状态检查只读执行，不自动重发。未打开详情后台。 |
| Secretary／Schedules／Compaction | 当前Orb状态、已打开面板／排期列表及Context压缩状态所需字段 | 未展开排期正文不阻塞；仍按既有范围后台请求。结构上共享一个响应时可以等该响应，不能为了“拆小”伪造部分字段已成功。 |
| Thinking／tool详情 | 当前视口内已展开facet的所有source rows | 组件把展开身份登记给协调器，HistoryDetails可针对staging cards加载，12行一批；取消／被替换记录明确结果。无需先把staging节点发布给React来触发effect。 |
| Files root／directory／preview | Files页当前root和目录，预览打开时其metadata与实际呈现文件 | root、列表、preview effect纳入恢复代次；固定FILES_PROFILE。文本预览需读新文本；二进制预览按现有授权文件路径重取实际展示资源，隐藏文件不下载；第三方预览渲染失败明确失败，不能用旧ObjectURL算新读取。 |

外观组件的open状态／viewport报告只决定依赖，不直接写恢复完成。所有资源均在本轮开始登记是否已安排、是否当前必需、结果覆盖；不能把`Promise.allSettled`全部结束当ready。新增reader必须在此登记初始／重连入口和失效边界，相关测试应能故意漏掉登记并观察恢复未满足，而非仅检查源码字符串。

**R6 · 持久展示快照。** 新增`core/display-cache.ts`，使用独立IndexedDB `secretary-display-v1`，不修改现有drafts库。键为`[schemaVersion, canonical server origin, profile, stored route id]`；侧栏键另以server origin与明确owner roster命名，各行保留profile。origin包含scheme／host／有效port，不取WebView文件路径作server identity。首次真实owner确认前只读精确URL／已确认Profile匹配的候选，未能确认owner时不借default Profile填充。

| 项 | 白名单／限制 |
|---|---|
| Timeline | 最新最多200条已持久化cards的身份、顺序、展示正文／timestamp／卡片外侧字段和附件引用；普通文本完整保存，折叠工具参数／结果／Thinking正文不持久化。可存一个当前可见的额外有界窗口，但不保存阅读位置；冷开默认最新窗口。 |
| 侧栏 | 已成功读到的列表页摘要：真实owner/id、标题、preview、分组时间、pinned／archived展示字段及页覆盖；没有runtime_id/running/status/turn_started_at。管理操作仍向服务端校验，不以旧置顶／归档事实作写成功依据。 |
| 胶囊 | Session Total／Latest Turn已经取得的展示数值、零值／unknown、原统计scope、context估算／失效语义、兼容所需model/provider及来源；不保存active／compacting、完整usage事件或恢复游标。 |
| 明确禁止 | runtime/binding、seq、approval、pending、发送事务、临时command／temporary／steer节点、未持久化流式草稿、Notebook／Schedules实体、认证令牌、附件Blob、图片二进制或整个API响应。 |

这里的临时Steer指尚未消费／尚未持久化的视觉载体；已由原生writer落库、带真实消息来源身份的Steer用户行属于持久历史，应保留其可见正文与顺序，不能只因`display_kind=steer`就拒绝整页缓存。白名单过滤先于复制、容量计算及序列化；折叠Thinking／工具正文及未展示字段不参与该处理。

容量默认单Conversation 2MiB、总16MiB、最多10个Conversation，侧栏最多500条／1MiB；7天TTL，LRU淘汰，访问时间写入合并。单条正文过大不截断成假完整快照：跳过该Timeline窗口缓存，胶囊／侧栏仍可独立保存。schema不符、结构校验失败或过期条目直接丢弃；quota／私密模式／损坏均降级内存，不阻断网络恢复。不存在缓存不等于空历史。

读取为启动并行过渡，只要真值已提交就不能让迟到IDB覆盖它。写入仅取本轮已成功对账并展示的白名单数据，后台窗口独立成功才更新对应缓存；合并至一次空闲写入，最多每秒一次，pagehide只尽力flush。不从恢复失败后保留的数值刷新“最后成功时间”。服务端404／明确owner消失时删相应条目；rewind／压缩以本轮真值替换原窗口，已删除消息不得从另一个旧窗口merge回来；模型／上下文不兼容时按原失效规则丢弃Context部分，不能延续错误百分比。退出／认证失败时停止展示敏感缓存并清本document投影；缓存无法授权访问或绕过登录。

**R7 · 单次表现层交接与动画。** `Controller.state`仍是实时业务状态；新增明确的`visibleView`与`stagedView`，由协调器发布一次带`commitId`的不可变展示快照。RenderStore消费该展示快照并保留原流式合帧能力，不承担一致性判断。禁止把同一个可变binding对象同时放进staging与visible，避免无publish的深层变更泄漏。连接／错误／安全禁用等即时控制状态单独覆盖，不把过渡画面包装成可操作旧审批。

连续连接的同owner／runtime／epoch／connection已经完成正式cut核验时，普通运行通知及发送受理后的历史失效仍完整重读，但新事件沿既有Controller reducer继续呈现在当前画面，并沿原缓冲保存本轮切点之后事件；新的历史／详情／cut仅暂存，到当前可见依赖就绪后再统一安装／对账。不能让slow Pending等阻塞已核验实时消息，也不能让staging历史或REST胶囊数值借实时事件提前泄漏。连续性证明在断线、owner／runtime／epoch替换、鉴权失败或cut错误时撤销；首次加载／真正重连没有该证明，仍保留过渡画面并等待正式恢复。不跳过读取、不等待Turn结束，不新增第二条reducer或独立推流框架。

首次New Chat的当前Send收到真实成功受理后，可使用刚创建的正式binding、目标Profile／Conversation、runtime、epoch及connection建立仅交给紧接着目标owner的受理交接证明，使真实后到消息沿同一reducer立即呈现；不伪造lastCommit或持久消息。仅status=streaming不合成User正文，仍等实际持久User回执／事件；拒绝／未知受理不建立证明，其它导航／断线／epoch／权限或cut失效撤销。冷恢复在必要历史／有限cut／可见详情核验后正常提交正文，不能等待未显示的Pending请求或Turn结束。Pending仍完整读取并独立失败退避重试；未确认时相关操作保持禁用；已显示Pending occurrences的恢复仍属于本轮展示屏障，不能借“辅助请求”省略。



- 交接前从现阅读owner取anchor与offset；提交后layout effect在同一帧先恢复该anchor的屏内位置，不清空、不换Conversation key、不重新mount Timeline。按2026-10-26口径，重连且最长公共前缀覆盖当前所见时，idle保留锚点并撤销旧恢复计时；只有确认active才进入`handoff-scroll`模式，暂停原`following → instant`及ResizeObserver抢位，用同一reading owner执行约240ms ease-out滚向提交后的尾部，结束后恢复跟随。无位移不动画；已证前缀破坏则可直接重定位末尾，未知前缀且idle保留位置。持续连接的普通失效与局部可见性提交不重新夺取阅读owner，用户手动滚动沿独立20秒规则。
- 动画目标以本次提交尾部为有限起点；期间真实delta继续呈现并更新尾部几何，动画总时长不续期，结束落在当时真实末尾，不等Turn结束。用户wheel／touch／键盘／拖滚动条立即取消本次自动动画并交还既有人工阅读规则，不在用户手势结束后重播旧交接。`prefers-reduced-motion`用一次受控定位替代运动，仅属可访问性降动效，不取消数据交接或最终末尾目标。
- Usage／Context比较**当前实际呈现值的规范签名**，包含视图、数字／unknown、估算标识、窗口与实际显示字段，不比较对象引用、observed_at或请求完成次数。首次无旧数据建立基线不闪；同值不闪；Usage实际有效变化背景高亮一次约120ms、约480ms淡回；600ms内连续变化合并、不重置无限闪烁。Context高亮时机按2026-10-25追加口径，仅由当前owner新的正式Turn结束事实触发一次，不能由数值变化、请求返回或恢复交接直接触发。切owner重建基线，不把另一会话当旧值；用户切Session／Latest视图不伪装成后端数据更新。动画独立于真实selected/open状态，不改尺寸、不触发Timeline滚动，降动效时只保留短暂静态高亮。
- 可见恢复ready在该次展示commit与anchor定位完成后回报；无需等240ms动画、缓存写入或背景所有请求完成。
- 阅读owner仅在目标／滚动范围或浏览器实际位置变化时写原生scroll；记录requested与实际可达actual，程序滚动回执按actual识别。整数scrollHeight／clientHeight对应的底部被浏览器钳制到小数时，同一目标／范围／actual不变不得重复写scrollTo；真实内容增长、锚点变化与用户操作仍正常处理。仅保留document内状态，不新增持久视口缓存。

**R8 · APK JS／Native闭环。** 保留可信origin＋主frame检查和现有health心跳，只扩展packet parser与原生ForegroundRefresh；网页没有HermesAndroid时该层零行为。

| 方向／包 | 字段与动作 |
|---|---|
| JS→Native `recovery-hello` | `{documentId, protocol:1}`；onPageStarted使旧document失效，Native接受当前可信页hello后记身份。不是恢复成功。 |
| Native→JS `hermes:android-recover` | `{documentId, nativeRecoveryId, reason:'foreground'|'network'|'watchdog'}`；由evaluateJavascript派发。JS入口调用同一startRecovery，不只重新connect。 |
| JS→Native `recovery-state` | `{documentId,nativeRecoveryId,recoveryId,demandVersion,state:'recovering'|'ready'|'failed'}`；ready必须来自R1/R7当前页面完成。Native只接收当前document＋nativeRecoveryId，旧包忽略；当前轮先recovering后ready，旧connected不得解除deadline。 |
| JS→Native `health` | 保留connection并增documentId／最近recoveryId，只证JS存活与连接；不证本轮页面读取完成。 |

原生确认真正从后台回前台且不是受保护的Activity result返回时，用单调uptime启动`nativeRecoveryId++`和**固定5秒deadline**，保留页面，投递恢复事件。若JS尚未hello则等待其hello后投递，但deadline仍从回前台开始；无响应到期照常兜底。重复onResume／online合并同一未完成原生轮次，不重置5秒；owner切换只改变JS需求版本，不能借此无限延长原生deadline。deadline前收到对应ready且心跳有效才取消重载，5秒后先到的超时判定赢，旧页ready不能撤回已经执行的reload。

`online`不再调用立即reload：可信前台有JS时发起／合并同一恢复窗口，WS未断但REST失效也能恢复。首次正常冷启动不额外走回前台5秒重载，沿正常加载和既有无响应看门狗；初始化失败依可见恢复结果，不把吞错视作ready。兜底reload后依旧10／15／20／30秒封顶重试，每个新document必须完成对应恢复而非只connected；原生看门狗保持无JS独立能力。再次真实回前台重新开始5秒窗口及后续退避，不承接上次剩余时间。

第三方认证页不注入恢复事件／业务数据，不自动重载打断登录；回到可信页后正常hello／恢复。拍照／文件选择的activityResults保护原样保留，返回后续读可发生但不以5秒抢断附件处理。通知目标继续由原生navigation保存，当前文档ready不等于已完成目标Conversation恢复；派发目标路由后由该owner的恢复完成回执确认，不能提前清目标。升级APK才取得新前端与协议；JS／Native版本不匹配保留旧能力明确降级，不能宣传新恢复已交付。

**R9 · 实施工作包与集成顺序（本节只规划，不派发执行）。** **用户最新模型约束：本方案交回后不再调用Astra；后续代码改造统一由`gpt-6.1-sol`执行，允许委派subagent，主会话负责复核／协调，不安排任何Astra实施或后续评审。** 默认high，子Agent不再派生；此条覆盖06中旧轮次的固定Astra分工，仅对本次后续工作适用，不改旧验收事实。表内路径以主仓为默认；`web:`表示独立`hermes-secretary-web`根。每包只改其白名单，公共Controller／App最终接线由集成包独占；确需超白名单先向主会话说明具体依赖，不顺手扩写其它能力。新模块用于分离现有超大facade，不增加其健康超标指标。

| 包／依赖 | 修改白名单与接口产出 | 完成判据及定向验证 |
|---|---|---|
| B1 范围读／无依赖 | 新`hermes_state_recovery_view.py`；`hermes_state_messages.py`只抽取可复用纯读接缝；`hermes_cli/web_routers/sessions.py`可选参数接线；`tests/hermes_cli/test_recovery_view.py`（新）／`test_history_cards.py` | 单conn事务、任意anchor、multi-lineage代表与UID退役、窗口证明、详情边界；旧接口响应不变。用真实SQLite证明深anchor不加载全正文、跨页插删不漏行；纯mock SQL不够。 |
| B2 原子事件切点／无依赖 | `tui_gateway/event_replay.py`、`tui_gateway/methods_session.py`对应events.since接线、`tui_gateway/contracts/sessions.py`对应返回契约；`tests/tui_gateway/test_tui_gateway_event_replay.py` | events/latest/truncated同锁切点，真实并发stamp测试；原seq／epoch与ring上限不变。 |
| B3 恢复封套／B1、B2 | 新`tui_gateway/recovery_view.py`；`tui_gateway/server.py`／`tui_gateway/methods_session.py`仅activate helper调用；`tui_gateway/contracts/sessions.py`可选字段；`tui_gateway/change_watcher.py`既有签名；新`tests/tui_gateway/test_recovery_view.py`／已有`tests/tui_gateway/test_inflight_output_recovery.py` | D0/S/D1、锁序、跨进程rewind／压缩、租约交接、ring缺口、持续delta有限完成；成功和失败DTO交F1。补已有writer通知时精确列实际缺少的writer文件，经主会话review后才加入白名单。 |
| F1 协调器与数据接口／B1–B3契约可先用真实DTO fixture | `web:src/core/page-recovery.ts`、`web:src/core/history-coverage.ts`、`web:src/core/recovery-resources.ts`（新）；`web:src/api/types.ts`／`web:src/api/client.ts`读取接口；各新模块同名test | 结果结构、取消、需求版本、有限cut、staging提交及无缓存成功捷径；把后端真实输出固定fixture用于接线测试，不能只造理想DTO。 |
| F2 展示缓存／F1类型 | `web:src/core/display-cache.ts`及test（新），只读取现drafts实现，不改drafts库 | fake-indexeddb测试owner、schema、TTL、quota、容量、旧IDB晚到、模型兼容、无runtime／临时节点；真实UI冷开再验。 |
| F3 reader适配／F1类型 | `web:src/core/profiles.ts`、`web:src/core/session-list.ts`、`web:src/core/usage-view.ts`、`web:src/core/history-details.ts`及对应test；Secretary等Controller内reader仅产出补丁说明交I1 | 初始／重连同覆盖，结果不吞错冒充成功；history详情能读staging而非依赖React effect；侧栏可见旧页恢复正确。 |
| F4 UI需求与动画／F1类型、F2接口 | `web:src/components/chat-presentation.tsx`、`web:src/components/Files.tsx`、`web:src/design/indicators.tsx`、`web:src/design/theme.css`（设计层只修改UsageSummary／ContextIndicator样式及动画）；`web:src/components/timeline-reading.test.tsx`、`web:src/components/presentation.integration.test.tsx`、`web:src/components/files-profile.test.tsx`及新恢复交接测试 | viewport／facet登记、可见窗口及分页间隔、无remount、anchor连续、人工输入、降动效、同值不闪；App调用点由I1接。 |
| A1 APK闭环／F1恢复结果协议 | `web:src/api/android-health.ts`及test；Android路径均在`web:src-tauri/gen/android/app/src/`：`main/java/com/edgarzhong/hermessecretary/ForegroundRefresh.kt`、`main/java/com/edgarzhong/hermessecretary/AndroidBridgeState.kt`中的AndroidPacket parser、`main/java/com/edgarzhong/hermessecretary/MainActivity.kt`、`test/java/com/edgarzhong/hermessecretary/ForegroundRefreshTest.kt`、`test/java/com/edgarzhong/hermessecretary/AndroidBridgeStateTest.kt` | generation闭环、4.9秒ready／5秒失败、online／onResume合并、旧包、无JS、认证／附件／通知目标；不改通知内容、通道或保活策略。 |
| I1 GPT-6.1代码集成／B1–A1 | `web:src/core/controller.ts`、`web:src/core/session-recovery.ts`、`web:src/core/render-store.ts`、`web:src/core/projection.ts`必要对账接缝、`web:src/App.tsx`、对应controller恢复测试；代码由`gpt-6.1-sol`执行，主会话亲审／协调，主仓README／AGENTS／CLAUDE由主会话独占 | initialize/select/gateway.ready/readers/Files/Android正式接线；旧发送受理／通知／编辑流程无回归。完成新状态机和矩阵证据才更新实现状态；不以包测试通过替代亲审。 |

可并行的是B1与B2、F2与F3及A1协议实现；B3与B2共用`methods_session.py/contracts/sessions.py`必须顺序集成，不能同时编辑。F4与I1不同时修改App，所有样式改动保留用户现视觉。B3后先完成前后端真实DTO对接，再合F2／F3、F4、A1，最后I1整体审查及隐藏UI／原生验收。仅到未来获准实施时才创建任务／分工；本方案不授权提交、push或部署。

**R10 · 验收矩阵与可执行验证入口。** 下列全部为待执行；现有测试报告仅证明原版本，不能填充新能力结果。

**本轮后续明确授权C17：用户在可审签名APK之后豁免实际APK验收，仅完成Web实测与原生单测，并明确APK实际运行未验边界。** 不启动模拟器，不以Robolectric冒称实际WebView验收；R8产品机制、APK构建／签名／资源匹配和Web实际验收要求保持。下表为冻结验收判据，执行结果按本轮报告记录，不将定稿时的“待执行”当成当前动态状态。

| 场景 | 应验证的行为／证据 |
|---|---|
| REST先／后到、同epoch重连、初次cold | 同一可见commit；没先清空／各自覆盖；每轮真实请求都发生 |
| 复制events后并发stamp、ring截断、快照后真缺口、新epoch | 原子cut无虚水位，逐序补齐／有限失败；新epoch不接旧游标 |
| D0/S/D1间append、同数replacement、跨进程rewind／压缩／delete | 无旧节点复活、无假相容；用真实独立DB连接／进程及正式writer，不用手改内存假装跨进程 |
| 活动Turn持续delta、结束后立即新Turn、外部lease接管 | 不等待Turn结束；snapshot＋suffix无重复／丢失；缺正式relay证据不报idle或ready |
| 旧anchor在很深历史、缓存起点变化、多页插删 | 有界定位，稳定覆盖证明；不得无界回读，不能把未验证当前缀破坏 |
| 已加载1000行但只看最新屏，隐藏详情／Profile页很慢 | 可见交接和APK ready不等全量；隐藏旧页重新进入视口有独立就绪校验 |
| 展开详情后断线；恢复中展开／收起／滚动 | staging详情可加载、无等React死锁，旧需求撤除，新需求不被旧结果满足 |
| 深anchor与tail不相邻、交接动画中增长／用户输入 | 明确分页间隔，无旧未验证正文冒充通路；无instant抢位，输入取消，最终末尾正确 |
| 跨Profile同ID、route切换、旧IDB／REST晚到、Files固定owner | 无越owner展示／缓存污染；列表不绑定所有runtime；Files root/preview确实重读 |
| reader失败／取消／合法空／unknown／404；初次未validated | 不误报ready；错误可自动重试，404不恢复不存在Conversation |
| Usage同值、实际变化、连续更新、模型切换、降动效 | 只对有效展示变化高亮，旧值不当新真值，布局和timeline位置不动 |
| APK4.9秒ready、5秒超时、旧document/nativeId、online先到 | 按当前轮次解除或兜底，无connected捷径、不无限续期；后续10/15/20/30保持 |
| APK冷启动、无JS、认证、拍照附件、通知目标跨刷新 | 首次不额外刷新，受保护流程不被打断，真实目标owner恢复后才完成导航 |

前端在独立仓库执行（新增文件创建后才运行对应命令）：

```bash
npm run test -- src/core/page-recovery.test.ts src/core/history-coverage.test.ts src/core/display-cache.test.ts src/core/controller-state-recovery.test.ts src/core/controller-mobile-recovery.test.ts
npm run test -- src/core/controller-profiles.test.ts src/core/session-list.test.ts src/core/history-details.test.ts src/core/controller-usage-view.test.ts src/core/controller-usage-source.test.ts src/api/android-health.test.ts
npm run test -- src/components/timeline-reading.test.tsx src/components/presentation.integration.test.tsx src/components/files-profile.test.tsx src/components/recovery-handoff.test.tsx
npm run typecheck
npm run build
```

主仓使用既有项目虚拟环境与隔离测试库，不直接pytest；新增集成测试须默认禁真实模型与外部网络：

```bash
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/hermes_cli/test_recovery_view.py tests/hermes_cli/test_history_cards.py tests/hermes_cli/test_session_timeline.py tests/tui_gateway/test_recovery_view.py tests/tui_gateway/test_tui_gateway_event_replay.py tests/tui_gateway/test_inflight_output_recovery.py
.venv/bin/python scripts/check --staged --only footguns,shebangs,no-tmp,config-writers,os-marker-fakes,case-collisions,lazy-deps,profile-archives,ruff,health
```

冻结检查在未来有对应staged候选时运行；不为跑命令暂存他人dirty、不放宽规则／阈值、不重复跑无关大套。Android在已安装项目所需JDK／SDK／NDK的环境、前端build成功后，从独立仓库执行：

```bash
cd src-tauri/gen/android
./gradlew :app:testDebugUnitTest --tests 'com.edgarzhong.hermessecretary.ForegroundRefreshTest' --tests 'com.edgarzhong.hermessecretary.AndroidBridgeStateTest' --tests 'com.edgarzhong.hermessecretary.HermesBootstrapTest'
```

JS／原生单测不能证明实际WebView生命周期与画面连续。后续验收只使用自建隐藏IAB连接隔离本地服务／合成真实协议fixture：记录请求次数、owner、recoveryId、commitId、cut、coverage、各资源完成／失败与滚动anchor offset；断网后用正式写入口改变隔离数据，再恢复网络核对。不得调用真实模型，不能操作用户现有页。需真实APK验证后台→前台、杀死JS／WS、通知目标、相机附件及5秒reload计数，保存版本／安装包资源SHA与原生日志；若当前显示保护或授权不允许操作模拟器／真机，明确该部分未验，不以Robolectric替代。最终重打包沿`npm run android:build`，签名／资源匹配核验后才称APK包含新能力；打包与安装／部署权限分开处理。

### 1.5. Tool rendering, Markdown and errors

**视口信息不持久化（2026-10-15 用户确认）：** 滚动位置、手动控制状态和恢复计时只存在页面内存；不读写 localStorage 等持久存储。每次刷新页面回到 Timeline 底部并恢复默认跟随。

**2026-10-15 滚动补充澄清（覆盖此前恢复跟随的含糊描述）：** Timeline 默认随内容高度向下增长而被动跟随底部，持续显示最新内容；用户 Send 被接受后回底并开始被动跟随。用户主动 Timeline 滚动（向上或向下）离开底部后立即退出跟随，之后流式追加不得推动视口，按用户选定的高度位置阅读；用户主动回到底部时立即恢复跟随；停止手动滚动控制 20 秒后，若当时 Turn 仍在流式输出，则自动回底恢复被动跟随；期间再次手动滚动重新计时，触摸拖动与惯性滚动结束后计时。若到期时 Turn 已结束则保留位置。用户主动回到底部之外，仅用户 Send 被后端接受会立即触发程序回底；不得监听所有 Turn 启动统一回底，Reminder 等自动触发的新 Turn 不改变阅读位置。首次只加载 200 条后台消息；更早历史仅通过上方按钮每次加载 200 条，不做自动分页。向前加载完成后，补偿顶部新增高度并锚定原可见内容在视口中的位置，不能跳顶、跳底、闪动或错位。

**2026-10-19 用户确认底部恢复跟随：** 用户手动滚动后暂停自动跟随；若用户随后主动滚回 Timeline 底部，立即恢复跟随新的流式输出，不再等待原手动阅读暂停计时结束。仍在底部以上阅读时保持原阅读位置与既有暂停恢复规则；不能把程序性滚动或内容增长误认成用户主动回到底部。该补充覆盖此前“动过 Timeline 后即使回到底部仍继续暂停”的含糊口径。

**2026-10-15 用户录屏确认补充：** 每次真实工具调用在动态 Timeline 中只有一张卡，构建、运行和完成在同一卡片原位更新。**并行 N 次调用必须展示 N 张独立卡片，不得将整组并行调用合并成一张卡。识别到完整工具调用段时，全部调用卡即按后端真实顺序出现在 Timeline；各卡身份和位置顺序始终稳定，即使 start/complete 到达顺序不同，也仅及时更新各自的真实状态，不重排、不追加替代卡。** 每段 Thinking 和每次调用独立收尾，不以整个 Turn 结束作为统一纠正点。动态内容转为静态历史时，条目数量、顺序与内容保持连续，不得靠结束后的历史重渲染消除重复或补出此前漏显的段。处于底部跟随状态时，内容增长、卡片折叠及历史对账不得自行中断跟随；用户主动上滚阅读时保持其阅读位置。用户新 Send 被原生接受后回到底部、恢复跟随；手动滚动暂停与 20 秒恢复条件遵循上述最终澄清。

**2026-10-15 结束瞬间连续性补充：** Turn 从 active 转为完成及随后的后台历史刷新期间，当前内容与视口必须连续，不得短暂跳回旧 Turn 再恢复。历史消息的操作栏在 active/idle 切换时保持占位高度稳定；已有被动跟随与分页锚定不能因后台历史请求而暂停。仍遵守用户手动滚动所有权，不把 Turn 完成新增为强制回底触发。

**2026-10-21顺序／阅读修复契约：** 已结束Turn的流式Thinking／工具恢复须按真实消息UID／row与调用occurrence归属定位；已有真实持久位置时，完成回执的旧尾部锚点不得覆盖它。详情懒加载补齐只能原位替换对应facet，不能把同Turn剩余片段推到全局尾部；工具parent在分页外而result在页内时，仍按真实result位置显示唯一卡。阅读锚点除DOM仍连接外还须核对当前消息身份，防React复用到其它条目；程序放置产生的scroll事件不成为新的用户滚动请求。后台Heartbeat等自发Turn沿既有20秒／active规则，不新增强制回底条件。

**2026-10-21提交受理恢复实现契约：** Web每次实际Send携可选`client_submission_id`，后端沿原生提交writer将其作为持久用户行的展示metadata保存，不进入模型消息。`message.user_committed`及直接受理回执可携同标识；`prompt.submission_status(session_id, profile?, client_submission_id)`只读核验目标Profile／Conversation内的精确受理事实，返回`accepted`及实际回执或`unknown`。未知不是未提交证明，不能据此自动重发；相同正文、running或其它会话事件都不能代替关联。晚到ACK不能重复消费草稿，后续草稿保留。退休／rewind行可证明历史上已受理，但客户端只刷新权威历史，不因回执插回退休行。省略ID的原生及旧客户端行为保持。

**Heartbeat即时展示：** 沿原生用户行持久回调发布已落库Heartbeat原文与身份，前端现有完整`<heartbeat>`用户消息分类生成卡片；不等Turn结束，不以Thinking正文、status文案或`HEARTBEAT_OVER`推断／伪造卡片，重复事件与历史按UID合并。


- Assistant text supports Markdown and code blocks with normal text selection/copy. Render links safely; regular `http(s)` links may open, but assistant local paths/`file://` URLs remain plain text in V1, not automatically resolved into Files.
- Tool cards retain activity/identity while token deltas arrive, including incremental tool-call argument construction when native events expose them; secure sensitive payloads using existing redaction/authorization rules, not invented client heuristics.
- Tool state distinguishes constructing, running, complete, failed, interrupted, unknown and an explicit user-required approval/clarify request where native APIs expose it. A spinner alone is not evidence of a healthy model loop.
- Completion of one tool or assistant block is not completion of the whole Turn; controls reconcile with backend status and actual terminal events.
- A disconnected or stale feed displays a recoverable status; on reconnect, native replay plus REST history is reconciled instead of appending duplicated fragments.

**2026-10-15 流式速度联调修订：** 纯正文／推理增量及其原生身份配对投影（`message.output_delta` 的对应 `native_type`）必须共享同一按帧渲染合并策略，不能由每条身份事件打穿合并并造成已完成内容持续积压。仅合并中间画面，原生事件、文本、顺序、身份及控制状态仍逐条同步处理；interim 边界、控制与终态立即发布最新完整投影并取消过期待绘制帧。真实终态竞争仍由后端拒绝，前端明确说明本轮已结束、Steer 未被接受、草稿已保留，不自动转成普通 Prompt。

**用户2026-10-26确认：Working转圈位置。** 活动回复的Working／流式等待转圈统一放在当前已呈现正文、Thinking及工具卡片之后，不留在某条较早回复气泡里、夹在正文与后续活动卡片之间。只调整呈现位置，不改变原生消息／卡片顺序或将转圈作为Turn活动与操作权限证明。

**用户2026-10-26确认：冷刷新缓存性能。** 刷新后的首帧同样必须尽快显示同owner已缓存的可见正文／卡片外壳，不能仅以暖切换瞬时显示作为刷新验收。持久展示缓存不需要Thinking正文、工具参数或结果，不为这些折叠详情做读出、解析或复制；已有页面的document内存阅读状态仍沿既有契约保留。缓存读取、采纳、首次可见绘制分别计时，不能把网络读取完成当缓存命中，也不能以隐藏Load earlier按钮或空白占位掩盖无正文；完整后台恢复及动作权限证明保持。

### 1.6. Composer contents, layout and keyboard

The Composer is a responsive, rounded multiline input with the approved controls: **Attach**, **Model**, **Reasoning**, and one state-dependent circular primary action (**Send / Steer / Stop / Interrupt / Cancel Send**). The visual AI may arrange the fixed controls ergonomically but may not remove, re-label semantically or replace their actions with unapproved flows.
- **Bottom anchor (user-reaffirmed 2026-10-14):** New Chat and Conversation share the same Composer bottom-edge anchor. Content growth expands upward; changing between these screens does not move the Composer. Desktop Composer and the two bottom capsules use the same bottom-spacing arrangement as mobile.

- **Enter submits content only (user-confirmed 2026-10-13).** Enter fires **Send** while idle, or **Steer** while a Turn is active with Composer content, and **nothing else**: with an empty Composer and no attachments, Enter performs **no** action and MUST NOT fire **Stop**, **Interrupt** or **Cancel Send**, and MUST NOT consume still-pending corrections. Shift+Enter inserts a newline; IME composition must never accidentally send. **Escape is the binding for cancel-type actions**: it triggers the correct cancellable action for the current state — **Cancel Send**, **Stop** or **Interrupt** — with sane modal priority and safeguards when a modal confirmation is active.
- Editor text can be undone via native Cmd/Ctrl+Z; ordinary text undo does **not** retract submitted messages, revert Rewind history, recover withdrawn Steers after consumption, undo attachments, or roll back filesystem actions.
- A draft belongs to an exact Conversation route or the independent current New Chat draft. Text and selected binary attachments must survive reload/revisit within the same browser where storage is available. Do not leak a draft across Conversations.
- A model/reasoning selector reflects backend-capable options and true current settings. A Composer pick not yet applied is local input state; an applied change must go through native Hermes configuration/session methods, never be hidden in localStorage as a competing active-model fact.
- During a send/upload transaction, prevent another Enter or Send while the transaction's acceptance is unresolved, regardless of additional typing; do not opportunistically submit those new characters.

### 1.7. Attach entry points and local selection

| Entry | UI contract | Native submit path |
|---|---|---|
| **Files** | Choose ordinary files, including ordinary PDF; show a small chip/icon and name | `file.attach` with bytes (`data_url`) → authoritative `ref_text` (`@file:...`) included in real submitted Prompt. |
| **Photos & Media** | Select images/media supported by native image routing; preview thumbnail | `image.attach_bytes` or verified equivalent native Image Attachment, bound to same runtime Session as Prompt. |
| **Take Photo** | Invoke mobile capture; one photo per capture, returning as an image attachment | Same image path as Photos & Media, not a fake ordinary-file `@file:` conversion. |
| Paste / drop | Add compatible selected content into Composer, preserve occurrence identity | Same type-specific native path when actually sending. |

**Transfer timing:** Selecting/pasting/dropping an attachment MUST NOT immediately upload to Hermes. Save it locally with the draft, check type/size at selection, and only transfer after the user issues Send. Duplicate visible filenames are allowed; distinct local occurrence IDs and the native server-generated paths/references distinguish them. Do not rename in the Composer or assume a filename is a unique identity. **User-confirmed attachment budget (2026-10-13): all attachments in the current draft together MUST NOT exceed 500 MB (500,000,000 bytes).** Selection, paste and drop MUST account for attachments already present, including duplicate-name occurrences; removing an attachment releases its contribution to that budget. Enforce the combined budget before admitting selected content into the draft. This is an aggregate limit, not a 500 MB allowance per file. Verify the complete actual upload and native submission path at this limit, including browser memory and websocket/API transport behavior; an ACK alone is not evidence of Agent readability. Do not retain the provisional 16 MiB per-file cap.

On historical messages: ordinary file attachments show only file type/name with an extension-derived icon; historical attachment chips are **not** click-to-preview, and no backend read-link reconstruction is required. Existing displayed image content may be restored only from real native history/projection, never from guessed local blob paths. PDF `pdf.attach` is not the default ordinary PDF mechanism (it renders pages into images, a different semantic action).

**2026-10-19 user-confirmed display correction:** User bubbles MUST hide Hermes-generated `<memory-context>` recall blocks and their System note; keep the underlying native/model content unchanged. Restore native persisted `[Image attached at: <path>]` / `[screenshot]` carriers as authenticated, profile-owned image thumbnails with bounded width and height, using their real recorded paths. Keep ordinary user text and quoted/code examples intact. Handle both live multimodal input and refreshed flattened history, without depending on base64 image parts surviving persistence.

**2026-10-19 user-confirmed core note wording:** New native recall wrappers state the sentence directly, with no `System note` label: `The following is recalled memory context, possibly relevant, not user input. This is the agent's persistent memory.` Remove the previous authoritative-data and all-responses instructions. Existing persisted API content is replayed unchanged; rendering and output sanitization remain compatible with every historical wrapper (labeled authoritative/informational forms and the earlier two-sentence note).

**2026-10-19 capture behavior, settings accepted by the user on 2026-10-20:** Compress photos locally from **Take Photo** before upload, with a maximum long edge of 2560 and JPEG quality 0.85; do not upscale, preserve the original when already small or when encoding increases its size, and fall back to the original with feedback on failure. Selection/processing performs no network upload before Send. Other attachment entry points retain their original bytes.

### 1.8. Primary action: normative decision table

Input assumptions: `draftText` is trimmed for meaningful send eligibility while preserving original edited content; `attachments` counts any selected file/photo; `pendingSteers` counts **server-authoritatively unconsumed** corrections; `turnActive` is based on actual live backend status, not merely a local spinner. “Send transaction” covers initial upload and unresolved submission admission.

| Priority / condition | Main action label / icon semantics | Exact result |
|---|---|---|
| Sending/attaching/submitting, before confirmed admission | **Cancel Send** (`X` or cancellation affordance) | Abort remaining client-side transfer, do not start an unaccepted Prompt, restore captured text+attachments snapshot. |
| Idle + no meaningful text and no attachment | **Send disabled** | No RPC or navigation. |
| Idle + meaningful text or attachments | **Send** (up arrow) | Resolve/create proper runtime, stage all attachments, only then invoke `prompt.submit`. |
| Turn Active + nonempty **text only** | **Steer** (arrow pointing left into a vertical bar) | Call native `session.steer` and show accepted pending correction provisionally. Repeating is supported. |
| Turn Active + empty draft + no Pending | **Stop** (square) | Stop only current running Turn. |
| Turn Active + any attachment + no Pending | **Stop** (square) | Stop current Turn; leave unsubmitted text/files/photos staged in Composer. |
| Turn Active + empty draft + one or more Pending | **Interrupt** (square, semantic action changed) | Atomically stop Turn and promote exactly the remaining Pending corrections to one next Prompt. |
| Turn Active + any attachment + one or more Pending | **Interrupt** (square, semantic action changed) | Same pending-only atomic handoff; never submits Composer attachments or text. |

Buttons MUST be driven by this precedence so a user can prepare attachments during a running Turn without accidentally sending them as Steer. Attach is **never disabled solely because a Turn is active**. No implicit redirect, generic queued Prompt fallback or silent attachment drop is permitted. A text-only Steer rejection is represented as a rejection/recoverable draft, not silently converted into a new Turn or routed to a different Session.

### 1.9. Pending Steer visualization and consumption

**Accepted Steer:** move the corresponding text from Composer into a User-shaped provisional bubble at the Timeline tail; additional accepted Steers form separate provisional bubbles and gently push older pending items upward. These are **not yet persisted User Messages**, even though they share the visual form. New Thinking, Tool, and Assistant stream content is inserted ahead of that provisional tail; the pending bubbles stay at the bottom until there is an actual native insertion point.

**Withdraw:** each **still-unconsumed** pending occurrence exposes an undo/withdraw icon (not a generic delete `X`). Successful withdrawal removes exactly that occurrence and **overwrites** the Composer text with its text; if editing/Rewind presentation state is open, retire incompatible edit state as specified by the confirmed product behavior. If the backend says “already consumed” or cannot prove pending status, do not claim a successful withdrawal or locally erase an actual message.

**Consumption:** all corrections consumed at the **same native insertion point** produce one real persisted User Message, with the backend's combined text and original ordering. Remove the consumed provisional bubbles and render that **single** real message at the actual insertion point. Do not preserve one historical bubble per original Steer or construct multiple timestamps for the batch. If a Turn finishes before pending corrections were inserted, the native Finalizer must carry the remaining combined text into exactly one follow-up Prompt (subject to the authoritative backend state). That behavior must be proved and, if native semantics lack withdrawal/exact pending identity, minimally extended in the native backend.

**Race rules:** acceptance, withdrawal, insertion, interrupt, natural finish, refresh and disconnection may coincide. The client uses authoritative receipt/consumption state, not estimated tool-call boundaries. A rejected/error/no-response steer must not be optimistically shown as securely accepted forever. Recovered pending state must not be reconstructed from the mere presence of `inflight_turn.correction_offsets`: that value is not proof of which occurrences remain withdrawable.

### 1.10. Stop, Interrupt and Cancel Send are distinct

- **Stop** requests native Turn interruption with no pending correction handoff; unsubmitted Composer content remains untouched.
- **Interrupt** requests native Turn interruption **and** atomic consumption of exactly the still-pending corrections as **one new Prompt**; pending text does not become a local draft and is not combined with the Composer's unsent contents.
- **Cancel Send** is a pre-acceptance *client transaction* control, not `session.interrupt`. It cancels any remaining uploads and prevents a not-yet-admitted `prompt.submit`; on successful cancellation restores the original snapshot of both selected attachments and text, **overwriting even draft changes made since the send began**.
- Uploads may already have produced server-side paths when canceled; V1 does not guarantee cleanup of those residual staged bytes. Such residues must never be submitted as a Turn after cancellation.
- If `prompt.submit` may already have been accepted, cancellation cannot pretend to undo it. The UI must reconcile the real server outcome and show an unambiguous submitted/unknown/rejected state; never blind-resubmit or fire a new prompt as a compensation.
- Escape follows the available cancel-type current action (**Cancel Send**, **Stop** or **Interrupt**) with sane modal priority; while a Send transaction is in progress Enter is blocked, and while a user is composing an IME sequence Enter/Escape must respect IME conventions.

### 1.11. Rewind + Edit: user-visible transaction

1. Offer **Reply** on eligible **persisted User Message** bubbles only; it is a rewind/edit action, not threaded replies and not an “Edit message in place” feature.
2. On entry, save the current draft snapshot; temporarily hide the selected User Message **and all subsequent Timeline nodes** in the foreground display; prefill Composer with that User Message's editable text and recoverable existing attachment references. Overwrite the visible draft.
3. Show a Composer `X` exit affordance for this **temporary edit mode** (distinct from Pending Steer Withdraw and Cancel Send). Exit restores the entire original Timeline and the saved pre-Rewind draft without modifying the backend.
4. User-confirmed 2026-10-13: **Send opens one confirmation dialog with a red Rewind and send button**. The two deliberate actions are Send and confirming that single dialog; do not add a second confirmation stage or another confirmation dialog. Cancellation keeps the edit and its recoverable draft. After confirmation, issue the existing Hermes `prompt.submit` truncation/rewind parameters with the correct durable persisted target. Follow Desktop's native rewind submit and busy/interrupt handling; never treat a busy truncation as an ordinary queued/steered prompt.
5. After successful backend truncation, the new history becomes authoritative. On rejection, restore a safe recoverable state; never hide source rows permanently on the assumption that the cut happened.
6. Refresh while the Rewind transaction is uncommitted MUST **not** auto-run truncation; any surviving editor text becomes an ordinary draft without armed destructive metadata or concealed history.
7. Rewind changes the actual Hermes transcript path; it does **not** reverse filesystem side effects or reclaim earlier file uploads. Cmd/Ctrl+Z does not roll back a committed Rewind and only provides native text-editor undo.

### 1.12. Slash catalog, command dispatch and human-only `/notebook`

> **第三轮适用性：** 保留共享catalog与浏览器临时只读结果；新版四分区正文为work／situations／discussion／candidates，旧栏目不继承。/noting不再控制Scheduler或受Memo阻止；Proposal英文指令见07 §8.10。

| Class | Examples | Mandatory Web behavior |
|---|---|---|
| Navigation | `/new`, `/reset` where genuinely registered, `/sessions`, `/resume` | UI navigation/session selection, with the **actual** command's semantics validated. Never invoke terminal interactive selection inside the browser. |
| Session/user controls | `/model`, `/reasoning`, `/compact`/`/compress`, `/stop` where genuinely supported | Use established UI controls or dedicated native RPC; synchronize actual model/effort/compression state. Do not submit command text as ordinary Prompt by accident. |
| Session title | `/title`, `/title <name>` | Read or set the current Conversation title. A live Conversation writes through the native `session.title` RPC; a stored row falls back to `PATCH /api/sessions/{id}`. The native answer is the only adopted title; the existing `RenamingText` animation plays on the real change. `/title --ai` is not a mode; use `/ai-title`. |
| AI title (Web-local) | `/ai-title` | Web command-router command (no native registry entry) that asks the existing `llm.oneshot` RPC with the `conversation_title` template to name the current Main's model-visible context, then applies the result through the same `session.title`/PATCH write. It is advertised locally in Web completions, not by the native catalog. AI proposes; the command writes. Failure leaves the existing title untouched and surfaces the native error. |
| Human-facing results | `/help`, `/status`, `/usage`, `/notebook`, `/noting` where supported | Render native results appropriately; `/notebook` is a **transient read-only Assistant-style chat result** without new model context or durable transcript row. |
| Dynamic commands | Skills, Bundles, plugins from native completion/catalog | Discover native availability; expose only those executable via correct browser/native dispatch, not a hardcoded stale catalog. |
| Terminal-only / test-specific | `/mouse`, `/redraw`, `/density`, `/theme`, `/logs`, `/clear` or others **where proven TUI-only** | Exclude or intercept at the Web command router, without deleting commands from shared Hermes registry. |

**User-confirmed title split (2026-10-17; context scope superseded 2026-10-24).** `/title` remains the native read/set entry: `/title <name>` sets the given title and bare `/title` reads the current title. AI naming is a separate Web-local `/ai-title` command; it is not a `--ai` flag on `/title`, and it is not a native registry command. The Web command router advertises it locally, while official clients keep their native `/title` semantics. It invokes the existing `llm.oneshot` RPC and then applies the generated title through the same native write. A failed generation or rejected write leaves the existing title untouched and surfaces the native error.

**用户确认取材范围（2026-10-24）：** `/ai-title`依据当前Main实际可见上下文命名，包括当前压缩摘要、Notebook及最近对话；不再从浏览器cards／live选择最早User＋末8条、逐条截前1200字符，不按屏幕滚动位置取样。Web只提交`template: conversation_title`及当前绑定session／profile，命名Prompt及上下文快照由后端负责，沿用当前Main模型。最近经微信运行的同一Conversation也必须识别真实上下文owner，不能将过期Web Agent或未补详情的浏览器历史冒充当前Main。无法取得可靠完整快照时明确失败，不静默回退到开场／限长摘录。标题任务只读、不继续原业务、工具执行硬拒绝，不改变父Main的Prompt、工具面、历史、Notebook或排期；原生首Turn自动标题的取材不因此改变。生成期间切换Conversation／Profile不得把旧结果写入新目标；空白浏览器历史本身不阻止后端命名。完整上下文命名沿用Main推理设置，总输出预算至少8192 tokens（包含推理）；旧客户端携带的256 tokens不再限制该新任务，标题正文仍要求简短。

**用户确认忙时行为（2026-10-24）：** Main运行（包括另一入口持有同Conversation的Turn lease）或压缩期间，`/ai-title`不触发模型生成，提示稍后空闲重试；不等待、不排队、不使用旧上下文回退，现有标题保留。

**User-confirmed slash completion (2026-10-13, R2-C76):** Composer supports Tab completion for slash commands. Each completion candidate presents the command and description in one text flow with unified wrapping, rather than separate text containers that wrap independently. Commands must not wrap prematurely while the candidate has sufficient available width.

Slash completions and execution are separate: a suggestion MUST NOT imply a command can execute in this UI when only a terminal handler exists. Typing a literal command, clicking a suggestion, selecting a model pill and using a matching keyboard shortcut must converge on one underlying action. `/notebook` is human read-only, shows the currently effective Snapshot/explicit “none” state and its proper timestamp **as required by 02** within the temporary result, but does not show Anchor/pointer IDs, create a Turn, consume Memo, mutate Notebook, or persist the human display as model-visible history. Other valid slash results follow their native result and persistence contracts, not an indiscriminate `/notebook` special-case extension.

### 1.13. Usage cards and context indicator

**User-confirmed compact pill (2026-10-14):** The collapsed pill shows only Total Tokens and Cache Hit Rate. Total includes trustworthy input, cache-read, cache-write and output consumption; absent required source fields remain unknown. Cache Hit Rate uses known input/cache-read counters independently of whether total is available. Remove the Information icon and its dedicated popup. Saved native Session counters may be shown while idle; do not invent missing completed Turn counts or Latest Turn receipts, and defer cold Context recovery if existing native APIs cannot provide a trustworthy occupancy. No new API is authorized.

Under/near the Composer, show a restrained usage component with two equal-size views, **Session Total** and **Latest Turn**, not badges on each assistant bubble or an aggressive cost dashboard. Switching views MUST NOT change the container's dimensions or jitter the chat input.

| Metric | Session Total | Latest Turn |
|---|---|---|
| Input tokens | Native trustworthy total | Native completed Turn result |
| Cache Read tokens | Native trustworthy total | Native completed Turn result |
| Output tokens | Native trustworthy total | Native completed Turn result |
| Cache Hit Rate | `cache_read / (input + cache_read)` **only if the source counters have that exact meaning**; otherwise native trustworthy ratio | Same constraint using Latest Turn counters |
| Turns | Real Session Turn count | Not an extra session count |
| Model Calls | Not a replacement for Turns | Number of provider/model calls in that actual Turn |
| Cache Write | Not displayed | Not displayed |

**User-confirmed visibility (2026-10-13, R2-C73):** Once usage data for the selected actual Session has been successfully fetched, show it regardless of whether a Turn is running or idle. Turn activity MUST NOT suppress successful Session usage data. Latest Turn retains its completed-Turn meaning; fields for which no valid value has been obtained remain unknown. New Chat remains excluded under R2-C16.

**用户2026-10-25确认：Context只在Turn结束时高亮。** Context数值持续及时更新，不为动画延迟或批量结算；同一Turn中Constructing、工具串／并行衔接、Thinking、首个delta前及其他流式／读取更新都不高亮。仅当前owner新的正式Turn结束事实触发一次；异常断线不构成Turn结束，历史恢复／事件重放不能重复播放结束动画，切owner不能借用另一会话的结束事实。此条替代上轮Context“任意有效数值变化都可高亮”的规则，不改变原统计来源及读取契约。

**User-confirmed incremental updates (2026-10-14):** For each field in both bottom capsules and their expanded views, update only when a new valid native value is obtained for the same Session and corresponding statistical view; zero is valid. Missing fields, unknown results, failed reads and Turn-state changes do not clear a previously valid in-memory value. Values never obtained remain unknown. The former memory-only restriction is superseded only by the user-confirmed transitional display cache below; retention must not leak across Sessions or incompatible views.

**用户2026-10-26追加：** Composer下方Usage与Context两个胶囊继续压低卡片高度，主要减少上下留白，保持文字大小及胶囊轮廓。当前实现高度32→26px、上下内边距4→2px，所在底栏36→30px；不改展开详情的排版。

**用户2026-10-24确认：底部两个卡片缓存与通用数据更新动画。** UsageSummary（Session Total／Latest Turn对应统计）及ContextIndicator均保存已成功取得的展示数据，页面冷启动、刷新后及断线期间先显示同一owner的上次值；新值返回后原地接管并更新缓存。UsageSummary的轻量动画以实际展示数据变化为触发条件，重复请求返回同值不触发。ContextIndicator的触发时机由2026-10-25追加确认替代：实时更新数据，但仅在正式Turn结束时单次高亮；缓存交接、恢复请求、工具衔接及Turn内流式更新均不触发高亮。动画采用用户进一步指定的轻微选中态高亮：胶囊背景短暂亮起一次后柔和淡回，不改变实际选中／展开状态，不连续闪烁。须让用户能察觉“数据更新了”但不抢夺注意力，连续变化合并提示，避免逐帧／逐事件闪动。保持卡片位置和尺寸稳定，不先清空数值，不触发Timeline滚动；具体时长、强度和合并节奏按§1.4.1的内部技术默认实施并验证。保持原统计视图、零值及未知字段语义，不由缓存推算新的token或百分比；缓存不跳过usage／Context读取，也不能恢复旧的active／compacting状态或作为整轮恢复完成依据。真实模型／上下文不兼容时沿原失效规则处理，不能以缓存延续错误统计。

Session Total SHOULD refresh as real native model-call/turn usage updates are available; Latest Turn switches to the most recently **completed** Turn, not the latest arbitrary assistant text segment. Missing/incompatible counters with no previously valid value are shown as unavailable/unknown, **not** obtained by dubious subtraction of lifetime aggregates. Cost presentation should not direct attention away from the conversation.

The adjacent Context control is a compact percentage ring, with an expanded detailed numerical usage/max view. Do not invent a category breakdown bar when authoritative categories do not exist. Context and Session Total numbers refer to the backend's real state and source; no independent local token accounting is authoritative.

**Runtime presence is not product state (user-confirmed 2026-10-17).** Binding, cold start, runtime recycling and “no live agent yet” are implementation details, not states the Chat UI may expose. Consequences:

- No control may render a sentence derived from a missing binding — in particular the Reasoning panel MUST NOT show an “Effective on this route” line, and the Context/Usage capsules MUST NOT say “Unknown” or “no active runtime”.
- **User clarification (2026-10-17): previous readings are allowed as cold-start estimates.** After a cold start or a recycled runtime, restore usable Context and Session Total readouts from the same Session’s persisted native readings rather than requiring an exact live measurement. Reusing the previous value as an estimate is explicitly authorized: Context can use its persisted usage anchor, while Session Total can use the existing native persisted Session counters or the previous trustworthy value for that statistical view. These are usable estimates until superseded by valid live readings; do not reject them merely because no live runtime measurement exists. If there is no trustworthy previous value, omit the number rather than label it unknown. The expanded Context panel states, in one short sentence, that the value appears after the next model response (“Shows after the next model response.”) instead of printing placeholders. This clarification permits estimates; it does not relax Session/profile ownership or the following known-model-mismatch rules.
- **User clarification (2026-10-17, cold restart follow-up): cold Context estimates become invalid only after a model switch or rewind.** Restore the same Session’s persisted native usage record across backend restart and runtime rebinding; ordinary append, compaction, and derived Framework messages must not by themselves suppress this authorized estimate. Keep the model’s exact native usage-anchor validation separate from the cold UI estimate. Compare the native model identity and rewind generation; an anchor persisted before model identity was recorded has no opinion and may still restore. A known model change or rewind omits the number until a new trustworthy observation is available. This is Hermes’s native usage anchor, independent of the Notebook coverage anchor.
- Restoring must reuse an existing native read path. Do not add a dedicated API for this; if no existing read carries the persisted anchor, stop and escalate instead of inventing one.
- A value restored this way is replaced by live numbers as soon as a real runtime reports them; frontend persistence is limited to the transitional display snapshots authorized above on 2026-10-24, with no cross-Session leakage.

**Additive API compatibility:** Reuse `session.resume` / `session.info.usage` and `session.context_breakdown`; no new endpoint or required request field. The optional `context_available` distinguishes unavailable legacy numeric placeholders, while optional `context_invalidated` and `context_invalidation_reason` (`model_changed` / `rewind`) explicitly retire an existing Context readout. Absent hints retain legacy compatibility. Original required breakdown fields and native exact anchor behavior remain unchanged; auxiliary display persistence is best-effort.

### 1.14. Compaction presence, cancellation and authentic history

During actual manual or automatic Compaction, the existing Context percentage ring **morphs in place** to a same-size animated loading ring; its normal percentage caption becomes **`Compacting`**. The expanded subview substitutes a **Cancel Compaction** action for the normal “used / limit” numbers while cancellation is meaningful. There is no extra Compaction status strip or second permanent control.

Cancel Compaction requests cancellation of **only** the active compression work, not the enclosing Turn, queued user actions, or the current legitimate transcript. If already committing or committed, the system reports that cancellation is no longer possible or complete; it must not leave a half-published context or fabricate a rollback. On actual completion/cancel/error, revert the Context indicator from reliable native state.

**User-confirmed command cleanup (2026-10-17):** After a submitted `/compact` or `/compress` completes successfully, clear that submitted slash command from the Composer through the existing draft owner/version mechanism. Preserve any newer draft typed while the command was running. A timeout or disconnect is an indeterminate result, not proof of compression failure or success; do not clear the draft or repeat compression merely from that transport error.

The post-compaction Timeline must display the **original native compaction summary/handoff** where it actually belongs, collapsed by default and expandable to its real content. On actual completion of manual, native automatic, or Noting-requested Parent compaction, reconcile the native Timeline and Context state promptly without requiring page reload or Turn completion. Noting task completion is not proof of Parent compaction completion; absent native textual handoff must not produce a synthetic summary. Native edge cases include a separate summary row, a composite carrier retaining real user text, Session rotation, no textual handoff and archived/compacted ancestors. The renderer follows the real projection; no synthetic “compression occurred” message, duplicated user identity or guessed marker is allowed. Full Foreground's audit node semantics from 02/04 do not become an excuse to build a V1 Full audit view.

### 1.15. Secretary Orb, Noting status and Memo Stick

> **第三轮适用性：** Memo计数、二级Memo面板和相关读取全部删除；Orb真实任务状态、失败提示与只读边界保留。**用户2026-10-17确认：现有Orb表现无误，不再需要Idle倒计时。** 本节旧Idle倒计时要求已由此替换，不据旧表恢复倒计时或重做已确认的表现。**2026-10-18补充：真实运行中任务的正计时不属于Idle倒计时，按下方状态计时口径显示。**

**Visibility is governed by the GLOBAL Noting switch and route, not by conversation-local eligibility:** show Orb only on an **existing Conversation** page while the global switch is on. A conversation-local `/noting off` does **not** hide it. When global Noting is off, hide the Orb (rather than displaying a disabled orb). Never show it on New Chat or Files.

| View/state | Product behavior |
|---|---|
| Orb idle | Calm, unobtrusive, even when local Noting is off; no task-running claim. |
| Orb active | Lights only while a real Noting Task is executing; never from a mere countdown or “enabled” flag. |
| Orb finish | A short completion highlight then back to idle, from real task completion. |
| First-level Status | Compact, **read-only** actual status. While a real Noting Task is active, show its positive elapsed clock from the runtime-owned start; otherwise show no Idle countdown. Current Orb presentation is user-approved. Memo count/contents are retired by the above Round 3 amendment. |
| Memo second level | Replaces first-level Status body with a header and the full ordered **current effective Memo** plus collapse control; no Status-body remnants and no edit controls. |
| No valid next trigger | Show no invented countdown; a 0-second local clock never asserts Noting started. |
| Local `/noting off` | Preserve orb when global switch on, but render true local/not-running status; current Memo remains human-readable subject to authorized native reads. |

**User-confirmed Scheduler navigation responsiveness (2026-10-26):** Clicking the first-level Schedule Tag switches to the second-level Schedule Table immediately, independently of request completion. Loading and data updates stay inside the already visible, interactive panel; they must not veil the whole panel or restart its navigation transition. Preserve the orb's own open/close morph and visible-only schedule reads; do not add hidden prefetch or persistent caches to mask the delay.

**User-confirmed running clock (2026-10-18):** while a real Noting Task is active, the first-level Status shows `Task Running` and its positive elapsed time (`HH:MM:SS`) from the runtime-owned task start (`secretary_noting_children.registered_at`). It is hidden for idle, unknown and finished, and is never inferred from page load, first observed transition or a local refetch. This is not the retired Idle countdown; it adds no status polling and does not change the read-only boundary. Older backends that do not provide the start hide the clock rather than inventing one.

Use native status/task read with initial fetch on entry, refetch after Conversation change and reconnect, and existing owning Gateway event path for changes. Do not render an Idle countdown or introduce polling for it. The running clock's one-second presentation tick is not status polling. Orb and Status remain entirely read-only: no Run Now, Stop, Noting toggle, Notebook mutation or background control surface.

**User-confirmed system error notices (2026-10-14, R2-C106):** Consume the existing native `notification.show` / `notification.clear` events through the existing notice stack, retaining the actual owner, text, severity and keyed replacement/clear semantics. Noting failures use the Parent's native notice callback; they do not create a successful Finish Framework Message or completion highlight. Preserve real failure/commit/trigger behavior; error presentation is not a retry, Notebook repair or new API contract.

**Completion evidence.** `task_finished` is a lifecycle invalidation, not proof of success. Use the existing `notebook_changed` hint's optional `completion_snapshot_id`, emitted only when the commit transaction made that result the current pointer, and confirm it against the owning `secretary.state` response's optional `current_snapshot_id` before highlighting. Reads without a success hint (including cold reads or rewind invalidation), failed reads, non-winning results, duplicates and another selected owner do not manufacture success. Missing optional fields from an older backend suppress this extra highlight without breaking status reads. Keep the user-approved Orb presentation unchanged.

**User-confirmed notice lifetime (2026-10-17, replaces the 2026-10-14 ten-second value):** Error notices remain until manually dismissed. All ordinary notices automatically disappear after **5 seconds**, including native notices and local thinking-effort feedback, through the same notice lifetime owner. Notices can stack; native clear/replacement must not prematurely erase an earlier error occurrence. This uses the existing notice entry and adds no API.

### 1.16. Files viewer, scope and error states

Files is a read-only directory browser and previewer, rooted at the **default cwd returned by the Hermes backend**; no workspace switcher or project manager is in V1. Native `terminal.cwd` is configurable by Hermes, not by a new Secretary Files settings page. Directory listing, bounded text preview, supported media preview and download use existing authorized REST, with genuine response MIME/size/permission limits. The pane does not silently invoke editing, delete, write, rename or standalone “upload into folder.” Chat attachment staging remains independent and is an intentional existing *send* write operation.

Opening Files does not change the runtime Session cwd. Opening a historical Conversation with a different stored cwd does not automatically rewrite it or hide it; the backend's new/create/resume policies must be audited against the user requirement that **new** V1 sessions take the configured default cwd. If uniformity for a resumed historical session is desired, it requires explicit product authorization, not silent workspace mutation.

File list and preview have loading, empty, not found, permission denied, unsupported preview and oversized file states. Browser navigation/deep-link routes should not leak unauthorized host paths or credentials. Exiting via the Files top-right `Back to Chat` returns directly to prior chat/draft without breaking native browser history or resetting an unrelated active Turn.

---
## 2. V1-Only Additive API Contracts & Native Compatibility

### 2.1. Delta admission: no duplicate API layer

> **第三轮适用性：** N/F/A/D评估与原生复用保留；表中Memo能力删除，Notebook／Schedule按新owner和07接线，不额外保留旧读取入口。

**Every V1 requirement first receives one of four dispositions:** **N** = reuse existing native REST/RPC/Event unchanged; **F** = implement only in thin frontend UI/orchestration; **A** = add a minimal native method, read projection, or event at a proven missing seam; **D** = deferred and MUST NOT be implemented for V1. A user-visible action is not sufficient justification for a new backend method. The engineering team MUST record a file-level source audit and a failing invariant/test before creating any **A** item; Main/Integration reviews the evidence.

| Capability | Default disposition | Contract judgment |
|---|---|---|
| Session create/resume/activate and transient stored/runtime mapping | **N + F** | Existing Desktop pattern already implements this via RPC and in-memory mapping; **no new Conversation mapping API**. |
| Session list, stored history, lineage, basic files, default cwd, real model config | **N** | Call existing Dashboard REST and TUI Gateway directly. |
| Timeline grouping, bubble placement, human-friendly timestamps, sidebar/history, scroll/drafts | **F** | Presentation logic only; no new server storage. |
| Basic prompt, image and file attachments | **N + F** | Keep Hermes's distinct attachment calls and exact runtime binding. |
| Pending Steer independent identity, authoritative withdrawal/consumption | **A if existing implementation truly insufficient** | Current `session.steer` result alone does not establish independently withdrawable still-unconsumed occurrences. |
| Interrupt + exact remaining Pending as one next Prompt | **A if native path lacks atomic handoff** | Sequential `session.interrupt` then `prompt.submit` is not a safe approximation. |
| Cancel just Compaction, not Turn | **A if native cancellation hook not available at API boundary** | May require a small core cancellation probe/hook with generation checks. |
| Secretary Noting/Idle timer/current Memo and `/notebook` human read | **N where present, else smallest A** | Do not invent an entire Notebook REST hierarchy or dedicated second event socket. |
| Authentic compaction carrier, stable message kind, tool-argument visibility and trustworthy Latest Turn usage | **N where possible, else narrow projection A** | Add read/event fields only after proving the relevant existing projection cannot express the fact. |
| Full Foreground/Snapshot auditing, rich file-link preview, user-run Noting controls | **D** | No preemptive schema, endpoint or UI scaffolding. |

**Compatibility rule:** A proposed **A** method MUST have a new name rather than changing an existing method's parameters, response shape, acceptance semantics or errors. New event types/read-only projections may be added without changing existing fields. Exact implementation symbols for proposed deltas are **intentionally not asserted to exist**: the lead must publish the audited final method-name manifest before merging. The following sections freeze **semantics, schema obligations and atomicity**, not imaginary upstream method spellings.

### 2.2. Pending Steer: acceptance and authoritative identity

**Gap:** Native `session.steer` accepts text and may answer `{status:"queued",text}` for a running Agent, but this response does not itself prove that a specific, separately identifiable text occurrence remains withdrawable. `inflight_turn` correction offsets alone are not a pending inventory. The V1 UI requires exact occurrence-level withdrawal and a reliable ack/consume transition.

**Required native additive operation (logical name: `SteerSubmitPending`, method spelling finalized after source audit):**

| Contract item | Requirement |
|---|---|
| Input | Current **runtime** `session_id`, nonblank text, session/profile ownership through existing transport scope; optional client operation ID for retry deduplication only if the native backend can honor it atomically. |
| Admission | Reuse the actual native steer/correction queue and Turn fence; **do not** build a second correction queue or a parallel chat loop. |
| Accepted result | `{accepted:true, pending_id:<opaque>, state:"pending", ...}` or an equivalent explicit durable-enough authoritative receipt scoped to the live Session/Turn. The occurrence ID is stable until consumed/withdrawn/turn-retired; no browser-generated ID is an authority. |
| Rejected/non-steer result | Distinguish inactive Turn, compression-specific native queueing, invalid session, rejected payload, and terminal conflict. No silent redirect or ordinary Prompt fallback. |
| Consumption | Backend emits or exposes `pending_id` to insertion-point transition and the actual persisted User Message/row relationship (or exact consumed ID set), with **one** combined message for a shared insertion point. |
| Recovery | A read/snapshot path returns authoritative still-pending occurrences for the exact active runtime/Turn; reconnect must not infer their existence from stale client chips. |
| Lifetime | Pending identity need not become a new SessionDB entity; consumption persists through the **normal** Hermes message pathway, and no independent client persistence is needed. |

**Minimality choice:** The lead may implement one atomic enqueue-with-receipt handler and one pending snapshot rather than retrofit the existing `session.steer` response. The product does not require the illustrative `pending_id` field spelling, only its exact meaning and the absence of ambiguity. If the current Agent's correction queue is internally merged before it can retain occurrence boundaries, use the smallest in-core pending occurrence bookkeeping necessary **at that queue's real owner**, not client indexing of a concatenated string.

### 2.3. Pending Steer: Withdraw and consumption races

**Required native additive operation (logical name: `WithdrawPendingSteer`):**

| Situation | Atomic server result | UI consequence |
|---|---|---|
| Occurrence still pending | Remove that exact occurrence from the true pending buffer, return `withdrawn` with its original text | Delete only the provisional bubble; **overwrite** Composer text. |
| Already consumed | Report `already_consumed` (prefer actual persisted message/link if available) | Convert to/retain real history projection; **do not** restore Composer text. |
| Already withdrawn | Report idempotent already-withdrawn or a verifiable terminal rejection | Do not restore the same text twice. |
| Unknown/wrong Session/Turn | Explicit error, no mutation | Surface uncertainty; refresh pending snapshot. |
| Concurrent natural completion/Interrupt | Exactly one transition wins under the same authoritative queue/turn lock | No phantom withdrawn bubble and no duplicate follow-up Prompt. |

Consumption must remove the corresponding pending identifiers **as a single authoritative transition** at the actual insertion point. Temporary UI insertion occurs only after a successful acceptance receipt; provisional bubbles are cleared only by matching consumption/withdrawal/final handoff, not by elapsed time, a random event gap, or the user changing routes.

**Acceptance invariants:** `accepted_ids = pending_ids ∪ consumed_ids ∪ withdrawn_ids ∪ otherwise_terminally_rejected_ids` for a completed operation epoch, with each occurrence in exactly one terminal disposition; no acknowledged correction is silently lost; no consumed correction is still withdrawable; persisted combined text preserves the accepted order of all actually consumed occurrences.

### 2.4. Atomic Interrupt-and-submit of remaining Pending

**Required native operation (logical name: `InterruptAndSubmitPending`, not an alias for `session.interrupt`):**

1. Identify the exact live Session and active Turn under its existing owner/admission/turn lock; acquire an atomic barrier against native consumption, withdrawal, Finalizer queue drain and mid-Turn rotation.
2. Determine which accepted Pending Steers are **still unconsumed at that barrier**; do not read from the Composer, browser LocalStorage, speculative UI list or old correction offsets.
3. Interrupt/cancel the current Turn using its native shutdown semantics; ensure it cannot consume those selected corrections afterward.
4. Atomically reserve/consume those still-pending corrections **once**, in accepted order; admit exactly **one follow-up Prompt** using the existing native prompt admission/persistence/turn lifecycle (including the current stored-session tip after Compaction).
5. Return a machine-readable outcome that distinguishes `(interrupted, followup_accepted)`, `nothing_pending`, `already_transitioned`, `not_active`, `rejected` and genuine **indeterminate** acceptance. Return or make queryable the accepted new Turn/session identity. Do not emit success before actual backend admission.
6. On partial failure, preserve recoverable authoritative state or an explicit terminal error; prevent a second Finalizer or retry from dispatching the same text again. Native queue generation/lease changes must be accounted for.

It is **forbidden** to implement this as `await session.interrupt(...); await prompt.submit({text: locallyJoinedPending})`. That sequence loses atomic ownership of the buffer and races consumption, backend auto-continue, session rotation and other attached clients. A separate additive method is permitted because the required invariant genuinely crosses native atomic state boundaries.

### 2.5. Cancel Compaction without stopping the enclosing Turn

**Logical operation `CancelActiveCompaction` (method to be selected after inspecting existing native cancel hooks):**

| Item | Contract |
|---|---|
| Target | Runtime `session_id`; identify the active compression operation/generation, if any. |
| Allowed phase | While cancellation can prevent publication of the compression result; do not promise undo after an irrevocable commit. |
| Effect | Request cooperative cancellation of **only** active compression; preserve enclosing Turn, unrelated Pending Steers, committed history and normal Agent operation. |
| Race | A successful commit and a cancellation cannot both be published for the same generation; any canceled output must be discarded rather than overwriting newer history. |
| Response | Explicit outcome: canceled / cancellation requested / already finished / too late to cancel / no active compaction / error. |
| Events | Status returns from `compressing` to a true backend state; actual Session/Context/Usage updates drive the ring. |

The lead first audits `session.compress`, native compression lock/commit fences, cancellation tokens and any isolated compute-host variant. It may add a small Core hook only if such a safe cancellation edge is absent. **Never** rewire or weaken `session.interrupt` to simulate this product operation. A button in the UI is insufficient proof the cancellation semantics work.

### 2.6. Secretary human-only read contracts

> **第三轮适用性：** CurrentMemoRead整项删除。HumanNotebookRead改为新版work／situations／discussion／candidates四区；NotingPresenceRead与NextIdleRead采用新开关、联合流程与双阈值。真实归属、只读、沿既有传输与禁止浏览器伪造倒计时继续保留。

Secretary read APIs MUST preserve 02's actual `conversation_ref` ownership. First inspect current Core tools/status data and identify only missing consumer-safe projections. No read may initiate a Turn, trigger Idle/Force Noting, mutate Snapshot pointers, consume Memo or acknowledge a Reminder.

| Logical read | Required source data | Minimum return/behavior |
|---|---|---|
| `NotingPresenceRead` | Effective global config, target Conversation's local Noting participation and real running-task ownership | Explicit global on/off and local participation, actual task state (including unknown), task identity/status and real start instant where available, no inference from a stale DB `running` row. |
| `NotingNextIdleRead` (retired UI requirement, user-confirmed 2026-10-17) | Existing native data may remain available | No Orb countdown is required or rendered; do not remove native fields solely for this UI decision. |
| `CurrentMemoRead` | Current effective Memo in Secretary-owned state.db | Ordered current entries and count, including an explicit empty result; read-only even when local Noting is off, subject to authorized global behavior. |
| `HumanNotebookRead` | Current effective Notebook pointer and Snapshot | Read-only rendered four-section content (or true no-Snapshot result) and Snapshot `created_at`; no Anchor/pointer ID by default; never a normal persisted chat row. |
| `GlobalNotingConfigRead` | Existing native config read | Enough to decide Orb visibility without adding a duplicate browser-maintained setting. |
| `ScheduleTableRead` | Current Conversation's formal Scheduler Schedule Table (`secretary_schedule_registry`, projected by `schedule_public_conn`) | Read-only rows with id, content, expression, canonical schedule, timezone, delivery mode, state, next due, pending count and last delivery; an unbound Conversation returns explicit `unavailable` with an empty table. Never synthesize a due time or a scheduled occurrence client-side. |

The engineering team may expose these through the **existing** REST/read paths or new small TUI Gateway RPCs as technically appropriate; do not force every read through WS or wrap existing REST endpoints in redundant RPCs. All results use correct profile/Conversation owner resolution; fetching status for Conversation A must not paint B after a rapid route change. Changes SHOULD travel on existing owning WS transport as small events/invalidation hints, followed by refetch when necessary. Do **not** add a dedicated Noting WebSocket or fast periodic status polling merely for the countdown.

**Browser state boundary (user-confirmed 2026-10-17, Pin amendment above takes precedence).** The Web UI is not a second store for native facts: session titles, pin membership and the Schedule Table are read from the backend and rendered from that answer. A rename is one native write — `session.title` for a live Conversation, `PATCH /api/sessions/{id}` for a stored row — and a pin is one native `PATCH /api/sessions/{id}`; the response is the only adopted membership value; no optimistic copy, browser mirror, replay queue or two-way sync layer exists. The later Pin interaction explicitly authorizes manual drag ordering, replacing the prior activity-only/custom-drag prohibition. The Agent implementing Pin must document its ordering persistence mechanism and distinguish presentation order from native pin membership; this bug-fix task does not choose or implement that mechanism. The Schedule Table is refetched on Conversation open, on Secretary invalidation hints and on panel expansion; schedule mutations emit no dedicated invalidation yet.

### 2.7. Special `/notebook` result contract and inherited Core behavior

> **第三轮适用性：** 临时人类结果、不持久化、不注入模型及客户端边界保留；four-section指07新四区，不指旧标签结构；不把后台Framework完整Snapshot注入误写为slash也要注入。

The new human view has a **different persistence intent** from the inherited 02 slash path. In a browser-client command invocation:

- Use one minimal read-only operation or a scoped native command execution mode whose output goes **only to the requesting UI**; no normal `message_uid`, transcript row, model-history injection, faux Assistant Turn, Snapshot mutation or Memo consumption.
- Present the response as a temporary Assistant-style chat result so it visually aligns with other command results; the display type is UI-only, with a local occurrence ID for rendering **not** a server Message Identity.
- Keep each ephemeral result only in browser working memory. Reload clears these results; do not persist or restore them through SessionDB or browser storage. The last real chat state comes from REST.
- Before that memory reset, preserve each result at the Timeline sequence boundary of its invocation, including after later messages, live/history reconciliation and compaction updates. Its relative position must remain correct; refreshing away a misplaced card is not a fix.
- Existing TUI/CLI semantics MUST remain compatible unless a separately approved Core-level change is absolutely necessary. The implementation review must identify the actual slash dispatch → output persistence path to enforce the difference, not hide a persisted row via CSS.
- The currently effective Snapshot's existence, four-section text and creation time remain grounded in 02/04; do not invent an empty Snapshot when no pointer exists.

### 2.8. Conditional display projections: strict evidence gate

These items are **not automatically additional API work**. Before making a change, prove the mismatch using the native server event/REST output and Desktop's already-working projection.

| Need | Prefer existing | Add only if proven missing |
|---|---|---|
| True Compaction message | REST `GET /api/sessions/{id}/messages?include_compacted=true`, existing display projector and compaction helper | Narrow server-side `display_*` projection for a real carrier, preserving message identity and full raw content. |
| Tool argument deltas | Existing TUI Gateway streamed `event` frames and Desktop event reducers | Correctly scoped incremental tool-call ID + argument delta if the backend cannot expose it, preserving sensitive content policy. |
| Message kind | Native `role`/display metadata and Secretary’s explicit `<framework-message>`, `<instant-reminder>`, `<deferred-reminder>` carrier semantics | Minimal safe kind projection if wrapper-based classification of actual messages is ambiguous or visually destructive. |
| Usage | `session.usage`, real turn/model-complete events and stored metadata | Read-only Latest Turn/source counters or model-call count where existing data is insufficient; **never** generate per-message estimates. |
| Real Noting presence | Existing Noting runtime metadata, config and true task events | Minimal read/event delta only for missing authority, not a UI polling database. |
| Default cwd vs live Session cwd | `/api/fs/default-cwd`, `session.info`, original cwd resolver | Fix only a demonstrated V1 behavior inconsistency at the correct native seam, not by falsifying UI paths. |

### 2.9. Additive interface correctness checklist

Every accepted delta requires a completed mini-contract before merge: **owner**, source file, reason native reuse fails, input constraints, stable IDs, response/terminal statuses, errors, timeout/unknown-acceptance rules, thread/lock ownership, native event projection, durable-vs-ephemeral boundary, existing-client compatibility, and tests. Use the source file's naming conventions when selecting method names. Existing RPC names and DTOs remain untouched. No other new backend features may be introduced under the label “V1 convenience.”

### 2.10. Model and reasoning-effort capability projection (decided 2026-10-17)

**一句话决策。** 思考强度的候选档位必须由后端解析后下发；前端只渲染后端给出的集合，拿不到就显示“未声明”，不再用固定常量冒充真实能力。

**为什么需要。** 现状有三处脱节：

- 前端把 `minimal … ultra` 七档写死（`apps/shared/src/reasoning-effort.ts` 与 Web 的 `src/core/reasoning.ts` 是同源复制）；后端从不告诉任何客户端“这条路由支持哪些档位”。
- 后端其实已经维护了十几张厂商档位表（ChatGPT 订阅、Kimi Code、xAI、TokenHub 等，见 `agent/reasoning_effort.py`），OpenRouter / Nous 的聚合目录里也有 `supported_efforts`。但这些表只在“构造请求”时被用掉，没有任何一处序列化给客户端。
- 结果是：`ultra` 在多数路由上必然被钳成 `max`；`none`（关闭思考）在自定义端点永远不出现；未设置时界面同时显示 `medium` 与 `Unknown`。

**增量内容。** 在既有 `model.options` 响应的 `providers[].capabilities[<model>]` 上增加两个字段，不新增 RPC：

| 字段 | 类型 | 含义 |
|---|---|---|
| `supported_efforts` | `list[str] \| None` | 该 `(provider, model)` 已声明的思考档位；`None` 表示没有上游声明 |
| `supported_efforts_source` | `"config" \| "provider" \| "catalog" \| None` | 上述集合的来源 |

**解析顺序（后端一个函数，按序回退）。**

1. 用户配置 `model_overrides.<provider>.<model>.supported_efforts`。自定义端点（DeepSeek 直连）走这条；`_default` 可给目录未知的模型兜底。
2. 厂商代码表（`codex_supported_efforts`、`kimi_supported_efforts` 等既有常量）。
3. 聚合器目录（OpenRouter / Nous 的 `supported_efforts`，仅缓存态）。
4. 都没有 → `None`。

**前端必须区分的三态。**

| 状态 | 渲染 |
|---|---|
| `supported_efforts` 有值 | 只显示这些档位 |
| `None` | 显示现有兼容全集，并标注“该路由未声明，厂商可能再收窄” |
| 字段缺失（旧后端） | 回退兼容全集，不报错 |

**明确不做。** 不改任何发送路径（`clamp_effort`、`route_supported_efforts`、`agent/transports/*` 全部不动），不改未设置时的实际发送值；不新增 RPC 方法；不改 `binding.info`；不改现有字段语义；不为任何厂商新增档位知识——集合只能来自配置、厂商代码或聚合器目录。

**兼容性红线。** `model.options` 的结果由 `contracts/registry.py` 依 `ModelCapabilities` 强校验（`extra="forbid"`）。新增字段必须同时进入契约模型并重新生成 `gateway-contract.generated.ts` / `.openrpc.json`；漏做会让 Desktop、TUI 与 Web **同时**收到校验失败。同步完成后新增字段是可选、只读的，不读它的客户端行为完全不变。

**已知边界。** Codex app-server 上的 `ultra` 可能少报一格，因为解析时拿不到会话的 `api_mode`；聚合器目录为缓存态，冷启动返回 `None`，界面落到兼容全集且不阻塞。

**验收。** 后端覆盖三种来源各一个用例与 `None` 回退，且契约生成物字节一致；前端三态各一个渲染用例，选择器只信任该字段或兼容全集；Desktop / TUI 的既有字段与数值零变化。

**实现落点（2026-10-17，已交付）。**

- `agent/models_dev.py`：`ModelCapabilities.supported_efforts` 字段；`declared_supported_efforts()` 读 `model_overrides`（显式优先，`_default` 仅在目录不认识该模型时兜底）；`model_overrides.supported_efforts` 进入 canonical key space。
- `agent/reasoning_effort.py`：`declared_provider_efforts(provider, model)`，覆盖 ChatGPT 订阅 / Codex、Kimi Coding、xAI 三家已声明的表；其余 provider 返回 `None`。
- `hermes_cli/inventory.py`：`_declared_efforts()` 按 `config > provider > catalog` 回退，`_apply_capabilities` 仅在确有声明时写入两个键。
- 契约与生成物：`ModelCapabilities` 加两字段，`scripts/gen_gateway_contracts.py` 已重跑。
- Web：`src/core/reasoning.ts` 三态返回（`source` / `undeclared`），`ReasoningSelector` 对未声明路由显示提示；其余客户端不读该字段，行为不变。
- 实测：`openai-codex` → `none/low/medium/high/xhigh/max`；`kimi-for-coding:k3` → `low/high/max`；`custom:deepseek-flash`（未声明）→ 不出现该字段；带 `model_overrides` 声明时来源标 `config`。`ModelOptionsResult` 与 `ModelOptionProvider` 均可通过校验。

---

### 2.11. New Chat Profile selection and Conversation icons (user-confirmed 2026-10-17)

This decision replaces the earlier proposal to place Profile entries inside the Model selector.

- **Placement and content.** Only the home / New Chat screen exposes a separate Profile dropdown. It is independent of the Model selector; each Profile option shows its name only, without a model, description, system prompt preview or other secondary metadata. Existing Conversation screens do not expose a control that pretends to change that Session's Profile in place.
- **Native ownership.** Read the available Profile roster through Hermes' existing native API. Selecting a Profile changes the New Chat environment before Session creation, including its model/provider defaults, SOUL/system instructions, memory, tools and native state ownership. The eventual `session.create` and all subsequent operations use that Profile. Existing Sessions remain owned by their original Profile; no transcript migration, copy of another Profile's prompt into the current Session, or second profile state store is introduced.
- **Sidebar visibility (user clarification 2026-10-18).** The sidebar shows existing Conversations across all available Profiles. The home Profile selector controls the New Chat environment; it is not a Conversation-list filter, and changing it must not hide another Profile's Conversations. Opening a row restores that row's original native owner.
- **Draft and transition boundaries.** Preserve separate draft ownership per Profile with the existing draft mechanism. Profile-scoped model/effort choices and staged paths must not leak into another Profile's first send. A pending Send/session creation must not have its owner changed by the dropdown. Load native defaults/capabilities for the selected Profile, and do not publish a late response for the previous Profile into the new selection.
- **Workspace reuse.** Profiles may configure the same `terminal.cwd` to share project files; this does not merge their Session stores, memory or instructions.
- **Conversation row icons.** The icon to the left of each sidebar Conversation is determined by that row's owning Profile. Conversations of the same Profile use the same icon; the configured Profiles use distinguishable icons. Keep a centralized, hardcoded Profile-name-to-icon mapping in the frontend source, as the user requested. Do not add a config field, persistence layer or icon-setting UI. Render the Profile's icon using the existing icon system without adding text metadata to the Profile options.

The native Profile roster, Session ownership and existing APIs remain authoritative. The frontend mapping is presentation data, not a replacement Profile registry. A newly configured Profile needs an entry in that source mapping to receive its own icon; an unmapped name uses a generic fallback. Implementation and evidence status remain in root `CLAUDE.md`.

## 3. Native Integration — Verified Wiring & Implementation Handoff

**Purpose and limit.** This division records the native behavior and code seams **actually investigated** in the fork, and the product obligations they support. It is **not** a substitute for the implementation lead's current-commit audit or a prescriptive reimplementation of Hermes Desktop. GPT-6 Astra owns subsequent code-level design, exact DTO validation, module boundaries, and implementation choices. If an interface named here behaves differently at implementation time, test the deployed code and record the discrepancy; do not silently rewrite the user-facing contract of divisions 1–2.

### 3.1. Verified transport and authority map

| Concern | Verified native entrance | Reference implementation / backend source | Boundary to preserve |
|---|---|---|---|
| Gateway transport | WebSocket `/api/ws`, JSON-RPC requests plus `event` notifications | `hermes_cli/web_routers/chat_ws.py` → `tui_gateway/ws.py` → `tui_gateway/server.py`; Desktop `apps/desktop/src/api/client.ts` | Browser is a **client**; Gateway owns runtime objects and dispatch. Deployment must prove browser-compatible auth, origin, WSS and REST access. |
| Stored session list/detail/history | Dashboard HTTP `/api/sessions`, `/api/sessions/{id}`, `/api/sessions/{id}/messages` | `hermes_cli/web_routers/sessions.py`; Desktop `apps/desktop/src/api/sessions.ts` | REST/SessionDB is the durable display-history source; it is not replaced by a second client repository. |
| New/recovered/live runtime | `session.create`, `session.resume`, `session.activate`, `session.active_list` | `tui_gateway/methods_session.py`; Desktop `apps/desktop/src/app/session/hooks/use-session-actions/index.ts` | Native lifecycle is server-owned; short-lived runtime addressing and UI route identity are different. |
| Prompt and control | `prompt.submit`, `session.steer`, `session.interrupt`, `session.compress` | `tui_gateway/methods_prompt.py`, `tui_gateway/methods_session_interrupt.py`, `tui_gateway/methods_session.py` | Existing signatures/semantics stay intact; only division 2's **proven** atomic gaps warrant additions. |
| Usage/context | `session.usage`, `session.context_breakdown` | `tui_gateway/methods_session.py`; actual model-call/turn events where available | Counters must retain their source meaning; no reconstructed false per-turn precision. |
| Slash and completion | `complete.slash`, native command-dispatch/Slash handlers | `tui_gateway/methods_complete.py`, `tui_gateway/methods_slash.py`, `tui_gateway/methods_secretary.py`, Gateway registered dispatch | Use the actual command registry/availability and Web-specific routing; never assume all terminal commands work in a browser. |
| Files/default cwd | `/api/fs/default-cwd`, `/api/fs/list`, `/api/fs/read-text`, `/api/fs/read-data-url`, `/api/fs/download` | `hermes_cli/web_routers/files.py`; Desktop `apps/desktop/src/lib/desktop-fs.ts` | Read-only Files is not a file-write tool; backend path policy and active terminal backend matter. |
| Other managed/media files | Existing `/api/files/*`, `/api/media*` routes | `hermes_cli/web_routers/files.py`; Desktop `apps/desktop/src/lib/media.ts` | Distinct native security/transfer semantics; do not blanket-substitute for `/api/fs/*` or attachments. |
| Attachments | `file.attach`, `image.attach_bytes`, `image.detach`; `pdf.attach` is a separate page-rendering operation | `tui_gateway/methods_prompt.py` | Type-specific semantics and the exact runtime `session_id` must be respected. |
| Event replay | `session.events.since`, Gateway event sequence and epoch | `tui_gateway/methods_session.py`, `tui_gateway/event_replay.py` | Replay is **bounded**; a truncated replay requires authoritative history/state resynchronization. |

The file paths identify the checked **2026-10-12 fork snapshot**, not a perpetual guarantee of identical line numbers or contracts. This table is the source-backed **reuse inventory**; it is intentionally not duplicated in division 2 as newly proposed API schemas.

### 3.2. Session continuity: Desktop's actual client/server pattern

- Desktop invokes `session.create`, `session.resume`, and `session.activate` through Gateway API requests; its renderer does **not** directly call the Python Agent Core. `session.create` yields both `session_id` (runtime) and `stored_session_id` (durable locator). `session.resume` accepts a stored locator and can reattach a live session or establish a fresh runtime ID.
- Desktop maintains **stored → runtime mapping in memory**; it intentionally does not trust persisted runtime IDs. It persists some presentation/connection hints, but Secretary V1 **does not inherit** the broad Desktop persistence system. References: `apps/desktop/src/app/session/hooks/use-session-actions/index.ts`, `apps/desktop/src/store/session-states.ts`, `apps/desktop/src/store/session.ts`.
- `session.activate` is a live-session rebinding point; on missing, recycled or mismatched runtime identity, the client falls back to verified stored-session resume. A single-flight approach for the same stored target is a proven Desktop pattern, not grounds to create a server Conversation API.
- The Secretary Core `conversation_ref` defined by 02 remains the owner of Notebook/Noting state; it is **not** the ephemeral Gateway runtime ID or a license to implement another browser-side Conversation Identity Registry. Correct lineage after compression must be resolved from Hermes's actual persisted facts.
- Merely opening a route may fetch REST history without creating a runtime; when actual execution/status binding is required, use existing native lifecycle RPCs. Never cancel another Conversation's turn on a route switch or re-submit a Prompt merely because the websocket reconnected.

### 3.3. History, live stream and reconciliation

| Input | Confirmed behavior | V1 use / constraint |
|---|---|---|
| `GET /api/sessions/{id}/messages` | Resolves the session's resumable tip; reads compression ancestors, supports `limit`, `offset`, `order`, `include_compacted`; returns a paginated display projection. | Authoritative old content, native message position, real Compaction; pages must preserve stable chronology and scroll anchoring. |
| `session.resume` / `session.activate` | Bind or rebind runtime, report session status and available live/in-flight information; Desktop can request omitted/deferred transcript. | Live control attachment, **not** an alternative permanent history store. |
| WebSocket `event` stream | Native session-scoped deltas/status; events include the runtime identity. | Paint live output and controls for the correct Conversation; keep the pending-steer visual tail separate from durable rows. |
| `session.events.since` | Bounded replay, `truncated` signal and a process `epoch`. | On reconnect, replay safely when possible; after truncation/restart refetch REST history and true runtime status. |

Desktop's existing REST-prefetch-plus-resume and transcript reconciliation is the main **behavioral reference**. GPT-6 Astra may simplify its implementation for a single backend, but MUST preserve the ordering, identity, no-double-send and no-false-completion invariants. Do not convert the browser into a second persisted transcript mirror.

### 3.4. Native action composition and established gaps

| Product action | Native building block already confirmed | Necessary boundary / gap |
|---|---|---|
| First Send | `session.create` → staged attachment RPCs if any → `prompt.submit` | Create once on first send, not on page entry; `prompt.submit` acceptance and Turn completion are separate. |
| Active-turn pure-text Steer | `session.steer` | Existing acceptance alone does not prove independently withdrawable pending occurrences or their exact later consumption; division 2 sets the **required outcome** without dictating an internal patch. |
| Stop with no pending | `session.interrupt` | Avoid submitting unsent Composer content. |
| Interrupt with pending | Native interrupt/turn machinery | Requires one authoritative interrupt-and-promote transition; **not** two client RPCs joined by local text. |
| Rewind + Edit | `prompt.submit` native truncation parameters and Desktop's prior rewind pattern | Verify the durable target and explicit user consent; do not substitute UI-only history deletion. |
| Manual Compaction | `session.compress`; backend status/rotation | Canceling compression **alone** is not equivalent to `session.interrupt`; the safe cancellation edge must be audited. |
| Native Slash | Verified completion and dispatch surfaces | Browser routes navigation/UI actions locally, uses proper native control for core commands, and filters only genuinely incompatible commands. |
| Human-only `/notebook` | Secretary notebook command/result path | **Approved behavior change:** current `tui_gateway/methods_secretary.py` persists `/notebook` feedback; V1 must instead return a transient human-only result with no persisted/message-context side effect, while preserving unaffected existing clients. |

These are implementation **handoff facts and requirements**, not a command to invent a particular API name, lock layout, worker abstraction, or frontend state-library architecture. The lead may use verified equivalent native calls where appropriate, with a recorded reason.

### 3.5. Attachments, filesystem and cwd facts

- `file.attach` accepts a gateway-visible path or `data_url` and returns `ref_text` with an `@file:` reference; the ordinary PDF path is the same. `image.attach_bytes` accepts base64 image data and registers an image on the correct runtime session. The actual prompt/agent perception must be tested, not inferred from a successful upload ACK.
- Native `pdf.attach` renders selected PDF pages as images; it is **not** the ordinary PDF attachment contract. `image.detach` exists, but cleanup semantics for canceled multi-file uploads must be proven; do not promise remote deletion where the native API does not provide it.
- `/api/fs/*` and `/api/files/*` are distinct REST families with their own path/security and transfer semantics. A read-only Files viewer uses authorized native read endpoints, not an unrestricted filesystem proxy. Any existing write endpoints remain outside this UI's Files surface.
- `terminal.cwd` is Hermes's configured default workspace. `GET /api/fs/default-cwd` exposes a Files-side default, while Gateway's session create/resume cwd resolution has additional session/profile/backend rules (`tui_gateway/session_workdir.py`, `tui_gateway/server.py`). **New** Secretary sessions must use the effective backend default; existing different-cwd history remains discoverable and must not be silently migrated.
- Browser binary uploads must respect the actual implementation's websocket framing, raw-size and memory limits. An unverified aspirational number is not a V1 compatibility guarantee.

### 3.6. Secretary and display facts that require care

- Existing Core authority: Notebook/Noting/Memo and `conversation_ref` follow current 02, including confirmed V1.6 revisions, then still-effective 04 increments under §0.2. This Web UI reads and presents them; it does not manufacture a second registry, mutable Notebook document, Trigger scanner or Reminder scheduler.
- Framework Messages, Instant Reminders and Deferred Reminders follow their **actual carrier and history** semantics. The UI renders each genuine surfaced message in the Timeline with a distinct treatment; it must not convert a due-but-unmaterialized schedule into a synthetic historical bubble.
- Original `/notebook` feedback persistence was found in `tui_gateway/methods_secretary.py`; this is the **source-proven conflict** with the approved browser-only temporary viewer. The remedy is intentionally left for GPT-6 Astra to design within division 2's compatibility rules.
- Tool deltas, Latest Turn usage, Compaction read projection and Noting status/events were discussed and partially inspected, but their **complete end-to-end consumer contracts were not proven** at the time of this specification. GPT-6 Astra MUST verify each against the current fork; do not treat a logical proposal in division 2 as an existing DTO or hardcode imaginary fields.

### 3.7. Audit and handoff ledger

For each V1 feature, the implementation lead records only the following compact ledger; a detailed per-function implementation plan is **not** part of this specification:

| Field | Meaning |
|---|---|
| **Native source** | Verified file and actual REST path / RPC / event, or `none` if genuinely absent. |
| **Classification** | Reuse unchanged **N** / frontend-only **F** / justified additive **A** / deferred **D**. |
| **User-visible invariant** | Reference to the normative clause in division 1 and, if applicable, division 2. |
| **Evidence** | Integration test, source proof, or counterexample explaining a required additive delta. |
| **Owner and status** | GPT-6 Astra owns technical closure; visual AI owns styling-only work. Track unverified items as such. |

The ledger is the handoff artifact for coding. It is **not** a second design document authorizing new product interactions or a reason to turn every backend method into a new wrapper.

---

## 4. Implementation Ownership, Design-System Engineering & Acceptance

### 4.1. Technical accountability, development and independent review

> **第三轮适用性：** 第二轮角色安排保留作历史记录，不作为第三轮人员／模型指定；第三轮以新编排为准。

Current-round user-authorized model assignments and gate order are recorded in the Snapshot Index; they do not waive either final gate.

**GPT-6 Astra high is Main/Integration and the accountable technical lead across frontend and backend; GPT-6.1 Sol high performs concrete Development.** Astra owns coverage, architecture decisions, delegation, review, integration and final defect closure; Sol implements assigned features, native integrations and tests, returning complete stage evidence for review. The specification does not prescribe their internal code structure, concurrency primitives or file-by-file patch sequence. Independent Verification uses **Astra high**; independent Validation uses **Astra medium**.

The independent **visual designer, Astra medium**, owns visual art direction, design-system specification and implementation, typography, color, spacing, composition, iconography, motion and responsive visual polish **within the frozen interactions**. It may build reusable styled/presentational components, but MUST NOT independently implement or revise Agent controls, network clients, Session state machines, event semantics or navigation behavior.

| Decision or work product | Accountable AI | Specialist role / limits |
|---|---|---|
| Source/code audit and implementation architecture | **Astra high Main/Integration** | Sol high performs scoped audits/development; visual designer receives stable component requirements. |
| REST/WS and Hermes Session/Core integration | **Astra high Main/Integration** | Sol high implements; visual designer does not touch API contracts. |
| Composer/Steer/Interrupt/Rewind/Slash state machines | **Astra high Main/Integration** | Sol high implements; visual designer styles specified states without new transitions. |
| Design tokens, reusable visual components and responsive polish | **Astra medium visual designer** for delivery; **Astra high Main/Integration** for integration/review | Visual permissions remain limited to 06's frozen interactions and accessibility requirements. |
| Automated tests, race/failure cases, native compatibility | **Sol high Development**, reviewed by **Astra high Main/Integration** | Visual designer may provide appearance fixtures; technical closure remains with Main. |
| Independent specification Verification | **Astra high independent reviewer** | Establish requirements from the frozen specifications, then review implementation and evidence. |
| Independent user Validation | **Astra medium independent validator** | Validate actual user input-to-output paths after Verification passes. |
| Final integration, defect triage and delivery evidence | **Astra high Main/Integration** | Review complete stage returns; Sol and visual designer fix defects within assigned scope. |

### 4.2. Design system as a production engineering deliverable

> **第三轮适用性：** 设计系统与组件治理保留；Memo相关组件退出，新版不因为本节列过Memo而继续实现。

The design system is **mandatory**, not a mood board or an optional last-mile styling pass. The visual AI establishes a coherent, reusable foundation using the approved React/assistant-ui/shadcn/Tailwind stack.

| System layer | Required discipline |
|---|---|
| **Tokens** | Central, semantic definitions for colors, typography, spacing, radii, shadows, elevation, motion and responsive rules; prefer semantic tokens over page-specific magic numbers. |
| **Components** | Shared primitives and composed visuals for top nav, sidebar, composer, action button, message kinds, tool/thinking disclosure, usage/context, popover, files list/preview and Secretary Orb/Memo. |
| **States** | Consistent hover, focus-visible, selected, active, pending, busy, disabled, unknown, error and reduced-motion variants without hiding required status. |
| **Responsive** | Desktop and mobile share a design language; keyboard insets, touch targets, safe-area handling and reading width are considered in visual delivery. |
| **Governance** | Any reused style change is made in the relevant token/component layer, with visual regression checks; no scattered literal colors, arbitrary one-off CSS overrides, duplicate design token values or page-local invented components where reusable semantics exist. |

Local implementation exceptions are permissible only when they represent a genuinely unique visual need, follow the token system, and are documented; they MUST NOT become an escape hatch to scatter unreviewed styling across screens. The system must remain maintainable after a different AI or human picks up the code.

### 4.3. Fixed product interactions; visual freedom only inside those bounds

- Division 1 controls **what an element does, when it exists, where behaviorally fixed controls appear, which action is enabled, and what errors mean**. The visual AI controls **how those facts are legible and aesthetically expressed**.
- The visual AI may decide Timeline time-label density, visual grouping and motion within the precise contract that times appear only outside bubbles. It may choose colors/typography for Framework Messages and both Reminder kinds, but MUST NOT reclassify, suppress, invent or relocate their real Timeline messages.
- The mobile Sidebar button remains **top-left** across New Chat/Conversation/Files; `Back to Chat` appears only on Files navigation bar **top-right** and has the fixed one-step return-to-chat semantic. This is not an optional visual rearrangement.
- One fixed Composer primary action follows the exact matrix in §1.8. The visual AI cannot add a secondary “Send Anyway,” a floating Queue, a separate Reminder inbox, an Orb `Run Now`, or a different Rewind flow.
- Questions about undefined styling can be resolved by the visual AI. Questions that would change interaction/product scope require explicit user approval, not an AI's unrecorded preference.

### 4.4. Sequencing without prescribing code architecture

> **第三轮适用性：** 本节是第二轮里程碑，不是第三轮实施计划；Memo相关里程碑退出，新切片见07 §9。

Implementation order is a **dependency guide**, not a file-by-file plan imposed on Astra:

| Milestone | Outcome and exit evidence |
|---|---|
| Native compatibility baseline | Proven REST/WS connectivity, identity map and current API status, plus a classified N/F/A/D ledger. |
| Foundational UI/design system | Shared tokens and components, three main routes and draft restoration without backend side effects. |
| Authentic conversation | Paginated history + live events + status reconstruction; true message kinds, times, Thinking/Tool presentation and Compaction history. |
| Submission/control | New Chat Send, type-specific attachments, Steer/Withdraw, Stop/Interrupt, Cancel Send, Rewind with real backend invariants. |
| Secretary/Files and utilities | Native Slash, Context/Usage, Orb/Memo, human-only Notebook, read-only Files and return navigation. |
| Hardening and final acceptance | Localhost in-app browser acceptance at all four required viewports (§4.6), reconnection/race and security/accessibility checks, relevant regression evidence; real-device keyboard/camera/system swipe-back checks remain later dedicated validation. |

Astra may reorder independent work and choose its preferred frontend engineering approach so long as every product and interface contract is met. Do not build future product infrastructure as a prerequisite to V1.

### 4.5. Normative acceptance matrix

A feature is not accepted because its button is present or its RPC returned 200. Use the backend's actual messages, persisted rows, usage and live state as validation evidence.

| Test focus | Required observable proof |
|---|---|
| Drafts and pages | New Chat navigation does not create a Session; same-browser text/binary drafts survive reload; Files right-top `Back to Chat` returns directly to previous chat; browser Back/Forward works naturally. Native system swipe-back remains required product behavior with real-device proof deferred under §4.6. |
| Identity and continuity | Stored→runtime mappings are memory-only and safely rebound; existing history loads by REST; true compression lineage appears as one Conversation; no cross-session stream bleed. |
| Streaming and history | True Thinking/tool parameter events appear as available; replay truncation refetches history; pending bubbles do not corrupt message ordering; no duplicated persisted assistant/user content. |
| Timeline semantics | Human-readable time appears only outside message bubbles; no per-message mandatory prefix; real Framework/Instant/Deferred Reminder carriers are distinct Timeline messages; no invented reminders or synthetic compaction markers. |
| Attachment success | Selected items remain local until Send; a real image is actually understood by the configured DeepSeek model (user confirms current V4.1Flash supports vision); verify actual configuration and request, without replacing the native provider or adding model routing. Ordinary file/PDF `@file:` is actually readable by Agent; duplicate filenames remain independent. Real-device camera invocation proof is deferred under §4.6, while Take Photo remains implemented. |
| Cancel Send | Before acceptance, cancellation restores the pre-send local text/binary snapshot; no duplicate turn; uncertain acceptance is reported rather than treated as a definite cancel. |
| Steer and Withdraw | Multiple pure-text steers accepted during an active turn; independent pending occurrences; consumed corrections cannot be withdrawn; successful withdrawal overwrites Composer; merged real user row in correct native position. |
| Stop and Interrupt | Stop has no unintended next prompt; with pending, Interrupt cuts the Turn and admits exactly one follow-up of **only** unconsumed pending content; attachments/unsent draft are not included. |
| Rewind | Two explicit confirmations, correct truncation target and replay, cancellation restores prior view; reload does not silently execute stale rewind; filesystem side effects remain untouched. |
| Usage and Compaction | Truthful Session Total/Latest Turn and Context data; Context ring becomes Compacting in place; cancel affects only compression; real handoff/summary displays correctly, including no-text and combined-carrier cases. |
| Secretary and Slash | `/notebook` human view is temporary and not present in DB/model context; current Memo is read-only and ordered; Orb visibility follows **global** switch; real running state and due time never guessed. |
| Read-only Files | Real backend default cwd, authorized list/preview/download, accurate errors; no unauthorized write/edit/renaming control; nondefault historical sessions are not arbitrarily hidden. |
| Security/robustness | Auth, origin, sensitive data, file read boundaries, Markdown rendering, browser IME/focus/keyboard, accessibility, large transcripts, native regression and compatibility pass within the declared local coverage. Four-viewports retain complete layouts and operations; real-device soft-keyboard checks are recorded separately under §4.6. |

### 4.6. Test layers and compatibility gate

> **第三轮适用性：** 第二轮证据与判定按原版本保留，不能替代第三轮两个独立门禁；新范围与证据由第三轮索引确定。

- **Unit/contract tests** confirm product state machines, visual component props, identity rules, slash routing, draft isolation, message-kind projections and mandatory API outcomes.
- **Gateway/Core regression tests** exercise only genuine additive behavior and prove unchanged clients can still call all existing methods with their original semantics; include crash, simultaneous correction consumption/withdraw, interrupt races and Compaction cancel/commit races where relevant.
- **Browser integration tests** use real REST+WS against the target fork, not UI mocks alone; include REST history paging, authentic message kind preservation, attachment-to-Agent readability, reconnection and uncertain Submit outcomes.
- **Required browser/visual acceptance** runs on local localhost through the in-app browser at desktop **1440×900** and **1024×768**, and mobile **390×844** and **320×568**. Every viewport MUST retain complete, usable layouts and operations, including the sidebar, Files return, Composer, Timeline, dialogs and Secretary views; small-screen usability is mandatory. The visual designer may own appearance fixtures; Main/Integration owns final behavior proof.
- **Later dedicated real-device validation** covers actual mobile soft keyboard, camera invocation and native system swipe-back. Their product capabilities remain required and implemented; browser viewport evidence MUST NOT be presented as proof of these device behaviors, nor does the deferred proof remove the features.
- **V1.6 handoff** is included in Round 2 acceptance: reuse valid historical evidence, supplement only transferred gaps and impacts of actual new changes, and do not repeat V1.6's own full Verification. Round 2 still requires its complete independent Verification and Validation gates.
- **No false green:** unavailable/unproven APIs are reported as blocked or incomplete; tests cannot pass by inventing DTOs, hardcoding counters, hiding legitimate messages or silently downgrading product rules.

### 4.7. Delivery checklist and change control

> **第三轮适用性：** 保留如实报告、兼容和薄客户端原则；Astra/Sol固定分工仅属第二轮，本轮角色按新计划。

The final implementation report MUST contain: (a) current source revision and changed files; (b) native-reuse versus additive-delta list with why each addition was needed; (c) verified client/backend contract results and existing-client compatibility; (d) test matrix with real evidence and known limitations; (e) design-system token/component governance checks; (f) proof of no new backend service, client business database or durable API history cache beyond the transitional display snapshots explicitly authorized on 2026-10-24; and (g) a concise list of unresolved items, if any, without declaring them complete.

**Change control:** no engineering, review or visual role may reinterpret a V1 product behavior, add an unrequested page/interaction, alter an existing native API or expand future scope without explicit user authorization. Astra leads technical decisions and Sol implements within assigned scope; neither may silently replace approved UX with a weaker behavior.

---

## 5. Planned Future Product Capabilities — Explicitly Out of V1

### 5.1. Full Foreground and provenance audit

The future UI is a **human-readable audit projection**, not a different chat history implementation. Retain 02/04's precise `Full Foreground` semantics: unique `Context Prelude`, ordered logical message nodes, authentic Compaction projection, and Anchor/Snapshot attachments. Message Identity is `(conversation_ref, message_uid)`; composite compaction may project adjacent logical nodes without inventing a second identity. The future viewer may expose source/version validity and audit anchors, but **none of its endpoints, database tables, message-node UI or navigation scaffolding is required in V1**.

### 5.2. Historical Notebook/Snapshot and advanced Memo views

> **第三轮适用性：** 旧Memo未来能力已取消，不再保留。Notebook历史审计仅为过去记录的未来设想，本次不实现已退出内容的短期检索通道。

Future screens may browse immutable Notebook Snapshot history, Anchor chronology, item lifecycle audit, archived Memo batches and richer human provenance. V1 has only the current effective Memo Stick and temporary human-readable `/notebook` result. Future read access may remain valid when Background Noting is disabled, subject to Hermes's authorized global policy; current V1 must not introduce editable Notebook surfaces or pretend archived data is an active Memo.

### 5.3. Rich Framework/Reminder and scheduler presentation

Future richer message cards may show provenance, delivery kind, timing, pending/consumed state and detailed schedule linkage. V1 already requires **distinct, real Framework Message / Instant Reminder / Deferred Reminder nodes in the ordinary Conversation Timeline**, not a generic notification overlay. Any future enhancements must preserve 02/04's actual carrier semantics and must not reconstruct due deliveries from guessed UI clocks.

### 5.4. Expanded workspace and file interactions

Future phases may add workspace switching, multi-root views, authenticated historical attachment preview/download, file editing, deliberate uploads into a selected folder, or richer artifact preview. These are **not** included in V1 Files; chat attachments use the separate native send pipeline. No unrequested filesystem write/management UI or workspace database is to be introduced prematurely.

### 5.5. Broader surfaces and advanced interactions

Native desktop/mobile applications, live voice/video interactions, advanced Dashboard controls, comprehensive branch-tree navigation, extended usage analytics and deeper multimodal presentation are future candidates, **not V1 prerequisites**. Browser camera attachment and mobile-responsive chat are already V1; they should not be confused with live camera/video streaming.

### 5.6. Future-scope change gate

Future goals remain recorded so omitting them from V1 is **not** a cancellation. However, V1 is complete only against the explicit requirements in divisions 0–4. No future-scope API method, audit storage, speculative DTO, hidden tab, preview scaffold or unused cross-client sync layer may be added “for later” without separate scope approval.

---

> **第三轮适用性：** 下文薄客户端、原生复用与真实交互原则保留；末句固定Astra／视觉AI职责是第二轮历史编排，第三轮按新计划，不由此指定人员／模型。

**Final normative invariant:** *The browser is a thin, reconstructible API client. Hermes/Secretary owns all committed conversation and runtime truth. The Web UI follows the confirmed user interactions exactly; source-grounded native reuse is preferred; exceptional backend changes are minimal and additive; the design system is centralized; GPT-6 Astra is responsible for integration and correctness, and the visual AI is responsible for styling without inventing product behavior.*


### 聊天背景表现层澄清（2026-10-19 用户确认）

- 仅表现层：New Chat 与 Conversation 共用完整聊天主面板背景，覆盖顶部、时间线及 Composer 下方，不能挂在 Welcome 局部容器内；不修改消息、路由或会话业务契约。
- 材质与运动：以高模糊、柔和低饱和度的磨砂漫射为主，采用连续火雾质感，以流淌为主、减少翻卷。拒绝几片渐变色带的移动、长条拉伸或锐利轮廓。两种聊天状态均持续且明显可见地流动；减少动态效果偏好下降低流速。
- 空间与切换：首页主要在画布中间、标题下方附近流淌；进入 Conversation 较快速向周边移位，再恢复常态流速。四周为主，允许偶尔漫入中心，无明确分界；返回首页反向聚拢，流动不断。保护文字、消息气泡及 Composer 的清晰度与操作。
- 色彩：参考现有 Warm Foundation / Cool Accents 色卡；明暗模式分别调校颜色、亮度、模糊和混合参数。暖陶／浅琥珀与雾蓝／灰绿交融，以实际视觉而非数值混合比例判断，暖色整体略占优势。冷暖倾向随时间平滑变化，一段时间偏暖、一段时间稍偏冷，不做整屏突然切色。
