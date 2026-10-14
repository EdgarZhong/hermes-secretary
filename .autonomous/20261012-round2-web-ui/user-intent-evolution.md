# 第二轮独立用户口径演进审计

> 本报告是用户意图及规格文字审计，不是 Verification，也不是正式 Validation 材料或实现通过证明。产品、代码、根文档和规格全程只读；仅保存过滤后的历史消息证据与本报告。正式 Validation 材料、执行指示和最终判据由 Root 亲自编制。

## 1. 依据与证据边界

- 直接历史来源：Codex `read_thread`，会话 `01a13593-93e1-7ba2-8f1b-6ab9095e8f5a`，实际标题「启动第二轮 Verification」。三页分页已经读至 `hasMore=false`；不输出或保存工具执行日志，仅保留 userMessage 与 agentMessage。合计143条用户消息（含异步问题答复）、243条必要对话消息。
- 原话证据：`.hermes-dev/round2-verification/user-intent-evolution/read-thread-messages.json`。下文 `Tn-Um` 指该文件的 `ref`；保留对应 turnId、userMessage.id、完整 content 和当时 Agent 对话。T 是按返回的历史时序编号，并非消息产生的独立时间戳，不能用 turn.startedAt 冒充每条原话的准确时间。
- 找到既有未完成提取资料：`.hermes-dev/user-intent-evolution-evidence/{extract.py,message-index.jsonl,source-manifest.json}`。未找到既有最终报告。原提取器只读三段 JSONL 的明文 response_item，不能据此假定加密字段或最新尾部已完整；本次以 read_thread 的可读完整消息作为直接证据。没有输出密文或尝试解密。
- 文档版本：后端 HEAD `cb05c0671c2c7e1e995e0f3b7d1c24ac216d3d5c`；02 SHA256 `ffe712722b3a9443c359e66e929daeae21989d04259d954e9354c7e06bea57db`（2584行）；06 SHA256 `8a13fe1f92b292de95665195c49b57a98fd94293046ba903de088430d3f689b7`（662行）。根 AGENTS、CLAUDE、Snapshot Index 与 README 索引已查阅。
- **本次恢复主会话最新覆盖**：Root 转交的当前用户指令要求 Astra 主会话亲自写正式 Validation 材料和指示，GPT-6.1执行；真实 Validation 先行，Verification最后静态审查，不再将当前阶段称为临时／开发态 Validation。本条是恢复会话的新指令来源，**不伪装成上述历史会话的原话**。历史中 T23-U5/U8 的“开发态、跳过 Verification”授权仍如实保留为前阶段，当前执行以新指令覆盖。

## 2. 实际工作与还原方法

先按用户消息时序找到问题触发场景，再核对紧邻的 Agent 解释、异步问题及答复；用户后续纠正优先覆盖早期解释，Agent安排、DS建议或观察事实不当成用户新授权。将“检查是否支持”“只改提案”“确认应用”“撤回实施”分别标记，不把调查请求自动变成产品扩展许可。随后只对02／06文字及当前索引做覆盖、冲突和弱表述对照，不读实现来反推用户意图，不做测试、模型、浏览器、服务操作或提交。

### 原话 → 时序 → 覆盖／取代关系 → 当前口径

| 原话证据 | 当时场景与意图演进 | 当前仍适用口径 |
|---|---|---|
| T1-U1：“开始第二轮的verification”；T1-U6：“首轮之后…派遣6.1sol解决…你做验收” | 用户开启独立审查后实际使用产品并反馈，要求主会话统筹和验收 | 历史启动事实；当前阶段流程由恢复会话最新授权覆盖 |
| T1-U4/U5：“我同意现有…数字选取”；答复“首次200条，每次更多200条” | 8轮／32条是操作回执保留，不是聊天历史；用户关心当前状态可恢复，并另选历史分页数量 | 两个窗口不能混为一个；聊天首次200、追加200，按后台消息包括工具调用／结果计数 |
| T1-U7/U9 → T2-U1/U2：“我实际上早就stop了…只是消息记录还在慢慢往出走” | 早期“Esc和Stop按钮失效”表象被用户本人修正为Timeline展示滞后；第一次Interrupt、后两次Stop | 核验真实停止与显示进度，两者分开；不能继续把用户三次操作概括为三次Interrupt失败。Ctrl/Cmd+Z草稿问题未被撤回 |
| T2-U3/U5，T3-U2/U3，T6-U6/U7：“中层或者地基的替换”“不是让他停手…继续干活” | 要先研究assistant-ui真实收益，再整改；语音“停手”纠正为保留已调视觉 | 成熟框架中层复用，保持用户视觉；不能把研究当暂停全部整改或许可自由重做UI |
| T2-U6：“turn active和turn结束…刷新…闪动” | 实际5173侧栏反复刷新 | 优化闪动，维持真实列表与已批准视觉 |
| T2-U9：“数据正常获取到了…不论turn是否运行” → T23-U4/U6/U7：“按位置增量更新”“不是…前端数据持久化” | 从取消活动态显示门禁，进一步收敛为各字段独立保值 | 同一事实范围内新有效值替换对应字段；缺失、unknown、失败或Turn变化不清空已有内存值；不建持久化缓存 |
| T3-U4/U5：“一个slash命令作为一个文本框…Tab补全”“不是set命令” | 候选命令和description拆框导致宽度够仍换行 | Slash Tab补全、命令与说明统一文字流换行 |
| T3-U6/U7 → T3-U8：“总而言之…不允许它的schedule为空” | secretary_task被Noting写成工作日志；早期问答限定未完成任务，随后扩大为所有状态 | secretary_task表达未来工作，始终有有效非空Schedule及明确instant/deferred；取消整条归档，不留空Schedule任务 |
| T3-U8/U9：“thinking…正常流式…reminder没有第一时间推送” | WS保持时模型已开始，真实Instant节点等到Turn结束才出现 | 真实Reminder应及时按原生位置展示；保持源消息和顺序，不造前端占位提醒 |
| T3-U10/U11，T24-U1 | 先有纯视觉worktree；最新另有Clarify独立UI工作树 | 两者不是一个合并许可；Clarify等用户通知才合并 |
| T3-U12/U13：“AI总结重命名”；答复“Hermes原生” | 语音“HarmonyOS”经用户答复明确为Hermes | 只调查原生AI总结命名能力；不等于授权新命名服务或改变手动改名 |
| T3-U14，T12-U2/U3 → T13-U1：“算了，不要文案了” | 原Mock侧栏分隔／日期分组／Appearance效果丢失；后一次要求局部文案又明确撤回 | 保已批准分隔、胶囊收缩及真实日期分组；撤回该局部文案恢复，非全站文案删除 |
| T4-U1 → T18-U1：“一点不增加…不是硬约束…以写好为标准” | 先希望局部精简，后来反对为长度而破坏语义；多次要求完整前后英中对照 | 语义清晰、保未修订语义为准；不是Prompt零增长硬门禁；审阅资料保完整前后英文及紧邻中文直译 |
| T5-U1：“我们有专门的watch point类型” | 提案总述混淆secretary_task和watchpoint | 分开类型职责，secretary_task新增Schedule约束不能自动套到所有Notebook类型 |
| T6-U1/U2/U3 → T10-U1/U2：“清理门禁，先不加了…单独成文档，不实施” | 曾提提交硬门禁，随后因forced／overflow承接复杂而撤回实施 | 不实施硬清理门禁；仅尾部软提示与独立设计提案。Schedule／状态耦合由代码所有者同步，非要求模型分两步记住 |
| T7-U1：“它只是主agent留给noting task的指示…Memo自己的清理只和快照有关” | Agent扩写Memo导致指示被当条目／provenance | 保Memo语义、快照消费、证据规则；Memo不是事实证据，不把便签文字直接粘为Notebook条目 |
| T9-U1：“禁止扩大工具实现范围…单独做一个取消任务的工具” | 限制任务修复的扩展冲动 | 复用现工具和正式接缝，不新增取消／清理工具或平行调度层 |
| T10-U3/U5/U6，T18-U3/U4 | 大输出导致卡顿，用户要求自查、避免后续内存问题与重复劳动 | 轻量取证、复用有效证据、及时交接；不能凭当前一次进程快照证明历史无泄漏或归咎用户进程 |
| T10-U7/U8：“Reminder默认折叠…timestamp不需要…消除” | 纠正普通User消息时间标记隐藏规则被误套到Reminder | Reminder默认折叠，展开保原内部timestamp；不额外包装或strip |
| T10-U9：“每次commit自动push” | 云端有人协作 | 两仓提交后自动同步当前upstream；不由此推导自动合并或发布许可 |
| T14-U1：“noting delay…回2秒钟”；U2–U5查失败 | 用户最近旧Notebook违反新Schedule校验造成Noting失败，接受旧库理解 | 运行round2 delay=2秒；不是产品默认改动，也不自动授权迁移、清库、静默修条目 |
| T15-U1/U12：“没有…原生前端API…不要再接线” | 系统失败要可见，强调复用已有API | 使用原生notice横幅入口；无原生能力时不新造API，失败不变成成功Framework或完成高亮 |
| T15-U2/U4/U6 | DS回答列多个原因，用户明确时间余量另议、撤回内部术语渗漏 | DS建议不是用户事实；只解决Reminder→Memo→后台Noting桥接歧义，不扩成“禁止Notebook词汇” |
| T15-U7/U10/U11：“允许这5秒…过期…不要被丢掉” | 讨论迟到的一次性Instant及提交后扫描 | 保原定时间，允许现有5秒扫描补投；不新增立即触发旁路，不让Noting根据任务起始时间决定要不要注册 |
| T15-U8 → T22-U4：“时间系统…一句话” | 原提案过度绑定单次Reminder | 最新timestamp只代表最新消息抵达真实时间；其他时间字段各有调度含义，不代表当前时间；Instant原定时间单独表达 |
| T15-U14/U17/U18 | 滚动条丑、Context压缩表现不符、常规notice长期积累 | 侧栏可滚动但不显示该滚动条；Context环原地loading，压缩面板仅Cancel；错误notice手动关闭，其他10秒消失 |
| T16-U2：“精确到秒以后的…通通删掉” | AI上下文暴露小数秒无价值 | 对外可读绝对时间秒精度，不改变内部计时／存储精度，不加新时钟 |
| T18-U2/U3：“所有触发路径…消息及时…状态…context” | 特殊Noting、手动、自动压缩完成显示疑点 | 所有真实触发路径分别观察触发、过程、完成；不得用“已调用compact_parent”或Finish早读替代Parent最终完成事实 |
| T21-U1、T22-U2/U3：“通过memo告诉…后台…不是自己直接安排” | Root Prompt用了有歧义的“arrange Reminder”，Memo定义分裂 | Main经noting_memo传意图，后台Noting注册；任何认为下次Notebook必须包含事项均记便签，降低Main分神／研究Notebook机制 |
| T22-U5–U8/U10/U12/U13 | 忠实头部、尾部2+N；人类/notebook已经不进模型；最后“已审定…可以应用” | 应用批准稿：头部忠实原意、尾部两句共性加各类型规则；无任务开始timestamp／额外过期判断／硬清理门禁；删除Target历史/notebook告诫，保Frozen历史原文 |
| T22-U9/U14–U17 | Usage胶囊指标不符、已有计数能算却空白、Information残留 | 胶囊仅Total Tokens和Cache Hit Rate；ratio按06源语义计算；移除Information及专属popup |
| T22-U18–U23：“如果做不到…暂缓”“不要再造API” → T23-U4 | 冷Context／Turns／Latest数据来源不足，随后用户指出活跃多Turn也没计数 | 冷无可靠原生来源可以暂缓；**不能用冷缺失解释活跃会话已有原生计数不接线**；新有效值优先显示并保值 |
| T22-U25/U26：“以底边为基准” | 修桌面底距时担心再次破坏New Chat一致性 | New Chat和Conversation Composer同底边，内容向上扩；桌面底距与移动一致，两个胶囊同约束 |
| T22-U27：“现在是开发台…缓存失效…必然” | Agent主动保护旧Prompt造成额外修补 | 本轮批准Prompt开发生效可原生重建缓存；不是废除一般运行期prefix保护 |
| T22-U28–U30、T23-U1 | 指定本次独立审计职责 | 原话与当时情景还原意图，再检查规格需否更新；不得揣测，也不是Verification |
| T23-U3/U5/U8/U9/U10 | 用户否定隔离profile／端口取证，授权真实模型检验驾驭 | 统一round2+5173；真实发消息观察模型轨迹，带指定前缀；正式阶段次序依恢复会话最新授权覆盖旧开发态称谓 |
| T24-U1–U3 | 要主会话随时响应，Clarify另开worktree | Main抓全局、派遣与交付，不陷具体实现；Clarify先隔离，用户通知才合并 |

## 3. 正式文档位置与覆盖矩阵

这里核对文档表达，不宣称实现存在或通过。行号属于上文SHA版本。

| 主题／原话 | 现行02／06位置 | 核对结论与最小修订建议 |
|---|---|---|
| secretary_task未来工作、任何状态非空Schedule、取消归档（T3-U6–U8） | 02 §2.5 assistant，433–435行 | 已覆盖，不重新把约束缩窄为未完成状态 |
| 状态／Schedule自动耦合（T6-U2/U3） | 02 §3.9，958行 | 已覆盖；不能退成模型另调status |
| Memo不是provenance、主只读（T7-U1；T21-U1；T22-U3） | 02 §5.12 Main Target，约1916–1918行；Noting Target1931–1954行；§3.5/3.6 | 批准Target已明确Memo桥接及忠实依据，原Memo语义保留；无需重写成Memo自身为证据 |
| 头部忠实、尾部2+N、无硬门禁（T22-U6–U13） | 02 §5.12，1931–1954行 | 已覆盖。Frozen仍含历史/notebook旧文是历史对照，不能误判为仍须执行 |
| 迟到Instant／5秒扫描／原定时间（T15-U7/U10/U11） | 02 §3.10，960–984行；§5.6 Instant，约1643–1648行 | **明确冲突**：仍称“the Reminder's due moment coincides with it”。原定时间可能早于抵达，不能相等。删除相等断言，写明timestamp是实际抵达，原定due时间单独保留；§3.10补用户接受现5秒扫描、过去一次性due不得只因迟到丢弃、不加立即旁路 |
| 时间秒精度（T16-U2） | 02 §5.6，1548／1584行 | 已有可读带时区ISO，但没有明确对外不暴露小数秒。补秒精度、内部存储／计时保持；不改timestamp仅用户输入／Instant可生产的边界 |
| 时间系统一句话（T22-U4） | 02 §5.12，1916行 | 已覆盖；无需添加Noting任务起始timestamp或过期决策句 |
| /notebook仅人类（T22-U5） | 06 §1.12，267行；02 Target1931行 | Web模型／DB界限与删除Target旧告诫已覆盖；不能扩大到所有slash结果均临时 |
| Usage胶囊两项、ratio、移除Info、冷暂缓（T22-U9/U14–U23） | 06 §1.13，271／275–289行 | 已覆盖两项／Info／来源限制。Cache Write不单列显示与Total包含其可信消耗不矛盾 |
| 有效值按字段增量保留（T23-U4/U6/U7） | 06 §0.4 89–96行、§0.5 105行、§1.13 285–289行 | **需加强**：现“缺失显示unknown”可被误用成每次清空。补同一Session、相应统计视图内已有有效值不被缺失／unknown／请求失败覆盖；仅新有效值替换对应字段，只内存不持久化。首次无值仍unknown，不能用另一会话值填补 |
| Context压缩环／唯一Cancel／完成及时（T15-U17/U18；T18-U2/U3） | 06 §1.14 293–299行；02 §5.9 1816行 | 表现已覆盖，但“完成后应显示”时效偏弱。补手动、原生自动、Noting with compaction各真实路径在完成时无需刷新及时协调原生历史／状态；不存在摘要时不能造卡。Noting提交不等Parent最终压缩，不能用Noting finish替代Parent完成 |
| Instant节点晚到（T3-U8/U9） | 06 §1.4 166–170行、§3.2消息投影约520行 | 真节点身份覆盖，但缺明确实时性。补WS连接有效时原生Instant行进入Timeline不等Turn结束，并按其真实顺序在后续Thinking前可见，不造占位／不换存储owner |
| Streaming滞后、框架复用、保视觉（T2-U1–U5；T6-U6/U7） | 06 §1.0约119行、§1.4/1.5、§4.2视觉边界 | 复用与边界有，仍可加强不人为限速播放离线动画／不积累过时展示队列；规定成熟中层复用不覆盖已批准视觉 |
| Ctrl/Cmd+Z、Stop真实结果（T1-U7 → T2-U1/U2） | 06 §1.6 190–191行、§1.9 | 基本键位已覆盖；不再把历史纠正前的Stop表象写成当前确定缺陷。实际复测仍需覆盖工具执行态键位与进度 |
| 侧栏闪动、隐藏滚动条、Mock视觉（T2-U6；T3-U14；T15-U14） | 06 §1.3 154行 | Mock分隔／日期分组已覆盖；未明确Turn状态变化不整栏闪动、保持可滚动但隐藏可见滚动条，建议两句局部补充 |
| 历史200/200（T1-U5） | 06 §1.4 175行仅写分页；轮次索引C67已有 | 用户明确数量应进入稳定交互条款；说明按后台消息计数，非200对问答或200Turn |
| Reminder折叠／内部timestamp（T10-U7） | 06 §1.4 173行 | 已覆盖，不再strip |
| notice条件与10秒（T15-U1/U12/U18） | 06 §1.15 315–317行 | 已覆盖；error与普通notice寿命分开，真实错误不造成功提示 |
| 同底边（T22-U25/U26） | 06 §1.6 188行 | 已覆盖，桌面修补须保New Chat一致 |
| round2+5173、真实模型前缀、最终门禁次序 | 06 §0.6／§4.6、CLAUDE／索引 | 运行profile／端口与当前轮次执行次序写CLAUDE／索引；不能把阶段授权反写成永远取消独立门禁。恢复会话最新真实Validation先行及末尾静态Verification覆盖T23旧阶段表述 |
| Clarify独立worktree／等用户合并（T24-U1） | 06 §1.5 181行只有原生clarify请求状态 | 有现成工具请求状态边界，具体Clarify交互仍需该隔离分支明确原生契约后编制。独立分支与合并等待写动态看板，不能以概括句冒充完整Clarify UI规格 |
| 远端自动push（T10-U9） | 06 §0.3 82行仍“does not publish…to a remote” | **明确过时**：用户后续已授权两个仓提交push，当前规则／索引已记。删除旧绝对不传远端断言，保不授权云部署／Memory Provider，不把push等同部署 |

## 4. 仍适用反馈场景输入清单

以下只提供用户反馈、触发情景与原意，供Root亲自编制正式Validation材料及判据；不作为已经执行的测试记录，也不替代正式冻结范围。真实入口统一用户round2 profile与5173，禁止另建profile／端口。Clarify合并前仅列依赖。

| 编号 | 反馈场景与用户意图 | 原话 |
|---|---|---|
| F01 | 空Composer光标在框内、Turn工具执行中：Esc与按钮的真实Stop行为，区分Interrupt三次历史操作；显示进度必须跟上实际终态 | T1-U7/U8/U9，T2-U1/U2 |
| F02 | 草稿连续文字编辑时Cmd/Ctrl+Z有独立文本撤销；不撤已发消息或文件系统副作用 | T1-U7 |
| F03 | 连续大量Thinking／工具参数／Assistant输出，保持真实进度；Stop后不再缓慢播放陈旧动画；成熟框架复用保视觉 | T2-U1/U3–U5，T3-U9，T6-U6/U7 |
| F04 | active→结束及后台更新时侧栏不整栏闪动；原Mock分隔、theme胶囊、真实日期分组保持 | T2-U6，T3-U14，T12-U2，T13-U1 |
| F05 | Conversation列表可正常滚动但不显示用户厌恶的滚动条；本次撤回的局部文案不再加回 | T15-U14，T13-U1 |
| F06 | Slash候选宽度足够时不提前断行，command与description统一文字流；Tab补全各种slash | T3-U4/U5 |
| F07 | 实际会话Usage在active、刚结束、idle均呈已成功取到的数据；New Chat继续无两统计卡 | T2-U9，T23-U4（New Chat边界继承06） |
| F08 | Session／Last Turn各字段取得一个有效值后，缺失／失败／unknown不清空；再获得有效值才替换对应位置；两胶囊与展开面板同逻辑；内存保留不持久化、不串会话／视图 | T23-U4/U6/U7 |
| F09 | 活跃会话完成数个真实Turn后总Turns及Latest Turn有原生来源即接线显示，不拿模型calls／消息数代替Turn | T22-U22/U23，T23-U4 |
| F10 | 胶囊仅Total Tokens＋Cache Hit Rate；有效input/cache-read能计算ratio时直接显示；无Information图标或专属popup | T22-U9/U14–U17 |
| F11 | Context正常占比、Total／Latest真实性；冷来源缺失可暂缓，不补造API或猜比率；已有有效内存值保留 | T22-U18–U21，T23-U4 |
| F12 | New Chat→Conversation、短草稿→多行草稿及桌面／移动底距：Composer保持同底边向上长，两胶囊对应位置稳定 | T22-U25/U26 |
| F13 | Instant注册于空闲会话后自动唤起：真实Reminder节点及时出现，后续Thinking／内容不先行而Reminder等Turn完才显示；WS不刷新场景 | T3-U8/U9 |
| F14 | 注册已经过去的一次性Instant：保原定时间，既有5秒扫描补投，不新增立即旁路；timestamp指抵达真实时间，不等原定due；忙时原生转Deferred，不自造新规则 | T15-U7/U10/U11及紧邻原生解释 |
| F15 | Instant／Deferred／Framework都是真实Timeline节点；Reminder默认折叠且展开保内部timestamp，无额外包装 | T10-U7；现行06 |
| F16 | Main接受未来工作通过Memo让Noting建有instant/deferred明确模式的Schedule；完成工作不创建流水账秘书任务；不能用虚构排期包装日志 | T3-U6–U8 |
| F17 | secretary_task取消整条归档、不能Schedule置空留task；改期状态联动代码处理，含done后的真实重新激活；不是模型另调status才能生效 | T3-U8，T6-U2/U3 |
| F18 | Main当前判断某事必须进入下一次Notebook时记Memo；提醒／日程桥接不使Main研究代码、直接写Notebook或用Cron替代；Memo不是provenance、快照消费不改 | T7-U1，T21-U1，T22-U3 |
| F19 | Noting忠实原会话意图：头部只强化忠实性，不加起始timestamp或过期时间判断；尾部2+N覆盖完成态；新done保下一轮，原done重新激活或归档；硬清理门禁保持未实施 | T10-U1，T22-U6–U13 |
| F20 | 人类/notebook可读展示不进入Main、Noting、后续Summary模型事实路径，不因旧展示被重复整理成新条目 | T22-U5 |
| F21 | 对外AI／人类绝对时间有时区并到秒，Instant原定时间与抵达time分开，内部计时不受显示精度改变 | T16-U2，T15-U8，T22-U4 |
| F22 | 普通Noting运行delay2秒：真实倒计时／active／有效完成Framework／finish高亮对应实际事实；失败时真实notice，没有成功假象；旧非法Notebook不静默迁移或放宽校验 | T14-U1–U5，T15-U1/U12 |
| F23 | 开启Noting with compaction时真实触发；原生自动／手动／特殊Noting三路径分别看Context原地loading、popup仅Cancel、Parent最终完成摘要不刷新及时出现；would_grow／无摘要不造卡；Noting Finish不等Parent完成 | T15-U17/U18，T18-U2/U3 |
| F24 | notice堆叠与替换／clear：系统错误通过原生横幅且保到手关，普通notice10秒消失；不新造API | T15-U1/U12/U18 |
| F25 | Show More History前首次200后台消息，追加每次200；断线长时间后手动刷新恢复真实当前状态，不因操作回执窗口误删聊天记录 | T1-U3–U5 |
| F26 | 原生AI总结会话命名能力调查与真实呈现，和手动重命名区分；此项只有能力调查授权，不预先创立新实现 | T3-U12/U13 |
| F27 | Clarify／ask-user工具实际交互缺口：独立UI worktree推进，Root先明确该分支与正式验收之间依赖；用户通知前不合并回当前正式5173 | T24-U1 |

### 真实模型发送必须使用的用户原话前缀

来源T23-U9。以下逐字保留，不能缩成“你是测试官”而丢掉禁止研究Harness的边界：

> 你不是开发者，你是测试官：仅作为 Hermes 的主模型，不访问当前hermes工作区外的东西，不要去看代码仓库的东西，不要研究你所处的 harness背后的代码机制。以你当前可见上下文为唯一行动指导。禁止对Harness 的代码机制做任何建议或者点评，只汇报你的工作体验。并如实的**直接回答**可能的提问，不要去调研代码库

T23-U10另明确允许任意Hermes模型调用、不担心额度，并演绎用户场景、观察行动轨迹是否符合预期。这是实际模型体验证据许可，不是取消电脑资源限制或要求并发重任务。

## 5. 缺口、意图疑点与禁止推断

- **应修规格文字**：迟到Instant的时间相等断言；秒精度；按字段内存增量保值；实时Reminder／压缩完成显示时效；Sidebar闪动／滚动条；200/200分页；远端发布旧限制。已同步的胶囊、Info、同底边、notice、2+N不重复重写。
- **当前新阶段来源差异**：原历史最后可读消息不是恢复会话最新用户指令。本报告将Root转交的最新阶段明确另列，保留可追溯性，不虚构新原话ref；正式材料由Root亲自登记本会话原始授权。
- **Clarify规格不足**：用户授权另开worktree修已有工具前端，但没有在这段历史决定输入控件形式、超时、拒绝／取消、继续条件等细节；不能从“clarify”一词补造交互。若相关分支已定义原生契约，由Root按新的实际来源编制，不擅自提前合并。
- **AI命名调查未等同产品修订**：原话只要查Hermes原生能力，报告不猜“必须立即实现AI改名”，也不默认废弃手动改名。
- **数据unknown不是任意旧值有效**：用户授权保同事实范围内最后已知值，不授权跨会话、不同统计视图串值，或把旧值伪装实时当前。有效0是值，不应因truthy判断清掉或拒绝；这一点属于保有效值的必要语义解释，不新增产品存储。
- **5秒是现有扫描间隔许可，不是所有端到端流程必然5秒完成保证**：忙态、投递条件和原生重试仍有原契约，不能据用户接受扫描间隔放宽丢失／ACK规则，也不能编造精确最大延迟。
- **“原生API做不到就暂缓”有范围**：当时针对冷Context／没有可靠完成回执的数据源；后续活跃会话Turns空白明确要求能获取即显示，不得通用化成所有Usage问题可不修。
- **“不要文案”是局部撤回**：覆盖T12-U3的Appearance局部标签，不删除原已批准New Chat欢迎文案、真实消息或无障碍名称。
- **Prompt批准与一般prefix保护不同**：开发期应用批准Prompt可以原生重建，不能回写成所有运行场景随意改prefix。
- **硬清理门禁撤回是明确约束**：设计07、forced／overflow承接讨论不能成为已获实现授权。2+N软提示的行为效果需真实观察，不能宣称硬机制保证已存在。
- **资源与历史输出风险**：历史两个审查Agent大输出卡顿，不能由一次当前ps定责或证明无泄漏；本次只保存消息，不转存全部tool日志，避免旧提取资料重读开销。

## 6. 接口影响

以上建议均不要求新增模型路由、provider、API层、client数据库、调度器或工具。统计保值是已有原生字段的前端内存投影策略；时间分离是既有timestamp与原定Schedule的语义纠正；notice复用原生notification事件；Timeline及时性须在原生消息／完成事件的现有接缝协调。Noting继续只写Notebook，Main只读并经Memo传指示；Parent最终Compaction所有权不转给Noting。改写动态阶段／worktree／运行profile的是CLAUDE和轮次索引，不把这些暂态安排写成永久产品架构。

## 7. 下一步与交回结论

1. Root亲自审阅本报告原话／情境／覆盖关系，采用最小规格修订；以02／06当前SHA版本为对照，若期间文档变化先核对行号及修订是否已落实。
2. Root亲自把F01–F27与原冻结范围、未闭合审查项、实际版本和入口依赖合成正式Validation材料及执行指示，再委派GPT-6.1执行真实Validation；当前次序依恢复会话新授权，末尾再做静态Verification。
3. Clarify单列隔离分支与等待用户合并的依赖，不绕过合并边界。
4. 正式结果区分通过、失败、无法覆盖及暂缓来源；复用有效证据不意味着可跳过用户新指定round2／5173真实复测。
5. 本研究已完成历史意图还原及现行02／06文字对照。没有修改规格／产品、运行测试或调用模型；没有提供实现通过或最终交付通过结论。

## 附录A：对Root正式Validation材料的确实遗漏对照

已只读2026-10-14由Root编制的validation.md（82行、27组V/H），不修改该文件，不重新编制判据。大部分反馈已经对应V01–V19/H01–H08。以下建议只补进现有组，不扩大测试工程：

| 确实未显式覆盖的反馈 | 原话 | 建议放入既有场景 |
|---|---|---|
| 原生**普通自动Compaction**，与手动、Noting with compaction分开；三路径最终完成及即时Timeline／Context | T18-U2/U3 | V13/V14附普通自动路径；当前两行分别只有手动和特殊Noting，不能互相替代 |
| 普通notice **10秒**自行消失、error持续到手动关、堆叠／clear／同key新错误不被旧clear抹掉 | T15-U18，06 315–317行 | V16已写失败notice，但未写普通寿命和堆叠边界 |
| 侧栏active→结束不闪动、Mock分隔／真实日期分组、隐藏可见滚动条但仍可滚动、局部撤回文案不加回 | T2-U6，T3-U14，T15-U14，T13-U1 | V01/V03增加侧栏操作观察；当前矩阵无这些明确反馈 |
| Instant真实节点在WS连续连接时及时出现，不能等Turn结束才见，后续Thinking不先可见而原输入晚到 | T3-U8/U9 | H04＋V02增加Reminder自动唤起时序观察；当前H04单次触达未明确此缺陷时序 |
| 胶囊仅Total＋Hit、Information及其popup确实消失 | T22-U9/U17 | V11或V03附胶囊展开／收起；当前统计字段准确与底距并不能覆盖额外图标／指标残留 |
| secretary_task**所有状态**均保非空Schedule；取消任务整条archive，不能只取消Schedule留条目 | T3-U8 | H03明确生命周期输入；当前“状态与排期联动”未明说这两条不可替代要求 |
| 全部对外可读绝对时间无小数秒；timestamp仅最新抵达，原定调度时间分开 | T16-U2，T22-U4 | H04/V10/V16加时间呈现观察；当前H04分离二种时间，但未明确秒精度跨面 |
| 首次200后台消息／Show More每次200及聊天历史与8/32操作回执区分 | T1-U3–U5 | V01分页／恢复；当前历史连续性无用户明确数量 |
| 原生AI总结命名能力的调查结论 | T3-U12/U13 | V01记录原生能力是否存在／呈现。只有调查授权，若不可达不能为测试新增实现 |

Noting运行delay=2秒已在当前运行配置记录，V16自然Idle可记录实际解析值，不另建加速机制。Main/Noting真实体验与充分DeepSeek调用、统一profile、前缀、Clarify隔离合并边界，Root材料均已明确，无需重复添加。四视口当前材料已要求实际生效证明，不能用历史resize未生效冒充通过。

## 附录B：02／06精确原句与最小文字建议

下列是给Root的可审阅提案，未应用任何规格修改。凡原句过长仅定位**要替换的完整子句／完整句**，不要求整段重写。

1. **02:1644，明确冲突。** 原句：`the marker is the moment of entry, and the Reminder's due moment coincides with it.` 最小替换：
   > the marker is the actual moment of entry, which may be later than the Reminder's originally scheduled due time; the original due time is stated separately in the body.
   中文：标记是真实抵达时刻，可能晚于提醒原计划到期时间；原定时间在正文单独表达。保该段其余载体／wrapper规则。

2. **02:984后，扫描与补投缺少明确已确认增量。** 原规则：`delivery failure does not silently discard the occurrence;`（982行）和`a successful one-shot is terminalized;`（983行）。其后追加：
   > Past one-shot Instant Reminders remain due and eligible for delivery; lateness alone must not discard them. The existing five-second due scan is acceptable; no immediate-delivery bypass is required. Noting faithfully records the intended action and schedule without a task-start timestamp or an additional time-window decision.
   中文：过去的一次性Instant仍到期可投，迟到本身不丢；接受现5秒扫描，不加立即旁路；Noting忠实登记，不加开始时间或窗口决策。时间窗口设计不能混入Prompt维护段。

3. **02:1548／1584，秒精度偏弱。** timestamp bullet原句：`- is exact ISO 8601 with a UTC offset;`。可替换为：
   > - is readable ISO 8601 with a UTC offset and second precision, without fractional seconds;
   在1548“对外所有绝对时间可读”段追加：
   > Human- and model-facing absolute-time renderings use second precision without fractional seconds; internal storage and timer precision are unchanged.
   这是展示精度修订，保时区／source／入上下文语义；不限制内部duration。

4. **06:285／287，保值。** 285原句子句：`unavailable counters remain unknown.`；287原句：`Missing/incompatible counters are shown as unavailable/unknown, **not** obtained by dubious subtraction of lifetime aggregates.`。最小把两处unknown限定“never obtained a valid value”，并在285后追加：
   > For each field in both bottom capsules and their expanded views, update only when a new valid native value is obtained for the same Session and corresponding statistical view; zero is valid. Missing fields, unknown results, failed reads and Turn-state changes do not clear a previously valid in-memory value. Values never obtained remain unknown. Retention is memory-only, never frontend persistence, and must not leak across Sessions or incompatible views.
   0.5:105的unknown规则保留，对unknown事实不猜；不能用它清空相同指标的已知最后值。

5. **06:297，完成时效。** 原句：`The post-compaction Timeline must display the **original native compaction summary/handoff** where it actually belongs, collapsed by default and expandable to its real content.`。在此句后追加：
   > On actual completion of manual, native automatic, or Noting-requested Parent compaction, reconcile the native Timeline and Context state promptly without requiring page reload or Turn completion. Noting task completion is not proof of Parent compaction completion; absent native textual handoff must not produce a synthetic summary.
   02 1816仍保持Noting提交不等Parent最终完成。无摘要不造卡。

6. **06:175，实时Reminder与分页。** 原句：`Long histories MUST be paginated and scroll-anchored;`。替换这一子句为：
   > Long histories initially load 200 backend messages and load 200 more per Show More History action, counting native tool-call/result rows; they remain scroll-anchored;
   同段末尾追加：
   > With a live WebSocket connection, a materialized Instant Reminder must become visible at its native position promptly, without waiting for the resulting Turn to finish or allowing later Thinking to appear while that triggering row is still withheld.
   这是即时显示真实行要求，不授权新占位消息或改变durable ownership。

7. **06:154，侧栏局部。** 原最后一句：`Missing native timestamps must not be invented.` 保留；后追加：
   > Turn activation or completion must not cause whole-list flashing. Keep the list scrollable while hiding the visible scrollbar, and preserve the approved Mock's separators and compact theme-control layout.
   已撤回局部文案不作为全站文字禁止；索引记录其撤回即可。

8. **06:175及119，流式时效。** 原句：`Streaming content expands **before** the Pending Steer tail.` 保留后追加：
   > Streaming presentation must follow real native progress without an artificial playback speed cap or a growing backlog of already-completed output. Reuse the mature interaction/rendering foundation while preserving the user's approved custom visual layer.
   不冻结未经测证的帧率或延迟阈值，不将逐字动画作为模型真实速度来源。

9. **06:82，已过时远端限制。** 原句：`This round does not publish the frontend repository to a remote or authorize cloud deployment or Memory Provider work.` 最小替换：
   > Subsequent user authorization enables automatic push after commits in both repositories. This code synchronization does not authorize cloud deployment or Memory Provider work.
   自动push SOP已在AGENTS，06不重复维护hook细节。

10. **当前正式Validation次序、模型、round2／5173与Clarify隔离合并**属于轮次授权增量，Root已在validation.md编制；更新CLAUDE／Snapshot Index并注明本会话来源即可。06:109、623和结尾仍写Astra分工及Verification→Validation一般要求，不应将本轮新顺序误作永久取消独立门禁；若Root判断需在06提醒，最小加“Current-round user-authorized model assignments and gate order are recorded in the Snapshot Index; they do not waive either final gate.”，不覆写旧轮历史。
