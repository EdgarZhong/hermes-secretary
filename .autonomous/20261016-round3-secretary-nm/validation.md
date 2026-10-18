# Validation：20261016-round3-secretary-nm

## 1. 结果概览

本文件由主会话依据 R3-017、R3-024～027 制定；执行者为全新、无主会话上下文的 GPT-6.1 Sol / high。用户已明确推迟静态 Verification，优先执行真实使用功能 Validation。当前状态：**2026-10-18 首轮真实使用实测已完成，Validation NOT PASS**。实测13:45:39–14:07:02（Asia/Shanghai），完整走完P01–P07及两个真实600秒测试日窗口；首轮曾发现个人自动归档/自动Recall及模型行为失败；当前接入复验已通过的范围和仍未关闭的VP-02见下方最新记录。不是第三轮整体交付通过。执行者填充实测版本、时间、证据与结论，不修改判据迎合实现。发现遗漏的适用场景先记录并通知主会话补入，不自行缩减。

**最新定向复验（14:27:42–14:30:30，Asia/Shanghai）：VP-01本次真实首批→suffix链通过。** 仅原考研Conversation两个短普通Turn；真实自动补归档首批22条获receipt，随后同Thread/同space追加一对用户/助手消息到24条，receipt长度22→24、旧前缀/ID/正文不变，全部服务端role/正文可与该Conversation原记录对应；关闭页面后仍24条，无重复。main未发新模型消息、receipt仍0。VP-04前包三个样本有效，本包只随行观察无新异常；**整体仍NOT PASS，VP-02未关闭，VP-03/05观察保留**。首次/第一次复验失败均保留，详情见§5.2。

**第一次定向复验（14:16:53–14:19:54，Asia/Shanghai）：** 仅VP-01/VP-04，既有考研Conversation两Turn＋既有主助手一Turn；未重跑提醒、F16或suite。5秒预算下三个正式用户`api_content`均无Recall unavailable，考研第二Turn含本次合成Memory的真实指针，**VP-04本次样本通过**；但自动Thread首批仍失败，出现4条`RuntimeError`未确认日志、receipt与服务端Thread均0，**VP-01仍不通过，suffix/同ID计数链未能执行**。整体Validation继续NOT PASS，首次失败不改写；详细证据见§5.1。

**2026-10-18 执行覆盖说明：** 下文原 V01～V15 保留机制覆盖，不再沿用旧 round3-only、fixture-only、禁止真实 NM 写入或必须先通过 Verification 的阶段限制。新建主助手/考研助手本机隔离 Profile，接真实 NM；Default 严格只读，包括自动 Thread 同步；“考研复习” Space 及获授权新测试 Space 可写。原 round3 服务与已有有效专项证据保留，不重复全量。产品版本/配置/正式入口在准备完成后记录。SOUL 依据用户指定身份文档与待补文档编写，私人全文不进公开报告。

**需求资料已到／现行执行约束：** 用户下载文档《Hermes Secretary 场景、个人需求、长期愿景与产品设计原则》（2026-10-18）为使用预期依据，原文与SHA在ignored `validation-personal-20261018/inputs/`；结合`~/.pi/SYSTEM.md`形成两份测试SOUL。长期愿景不扩为本次实现清单：不加正式跨助手委托、完整记忆治理或长期统计基准。**两个Profile均开启Noting**，Scheduler开启；主助手自动归档关闭、考研助手开启，分别验证独立Notebook。测试Persona/配置可调并记录前后版本；框架内硬编码Prompt不改，第一轮后仅给建议。真实Provider用DeepSeek，K3未测；结论分客观产品事实、配置问题、模型行为局限与未覆盖，模型自述/建议不可单独作证。

**本阶段优先功能链（主会话制定；实际结果见第3、4节）：**

| 编号 | 输入与操作 | 必须观察到的结果 |
|---|---|---|
| P01 | 两个新 Profile 分别启动真实模型、检索带独特标识的资料 | 实际加载各自 SOUL/配置/Space；工具取证区分两者，不以自称身份代替证据；Default 全程无写入 |
| P02 | 考研助手接收简短测试事实、纠正和未完成事项，经正式入口整理、提出持久化建议；分别暂缓与明确批准 | 暂缓不写；批准后真实目标写入有收据；Noting 先结算已覆盖来源，后处理 Candidate；未覆盖事项保留。串联 V04/V08/F16，不演复习剧情 |
| P03 | 新会话/冷恢复读取 P02 的真实结果，再查询原始依据 | 召回实际 NM 记录、必要时精读；正确区分事实/推断与旧/新版本；跨压缩原文通过正式 History 入口恢复 |
| P04 | 明确告知10分钟代表测试中的一天；要求主助手每10分钟至少一次 Reminder，查询考研 Space 在该测试日内的记录 | 真实600秒排期到期后，模型确实读取授权 Space、准确汇总有记录/无记录/读取失败，不读取考研 Profile；报告同时记录真实时间和测试日窗口，不等待现实一天、不把排期存在冒充实际执行 |
| P05 | 测试会话释放后观察生命周期，再恢复并检查排期/记忆归属 | 自有 Runtime/poller 回收，宿主保留必要调度；不出现其他 Profile 的历史/记忆/排期串用；复用已接收的 round3 冷态基础证据，仅补双 Profile/NM 新增链 |
| P06 | 主助手接收明确“只是分享、不安排任务”的自然交流，再接收一项明确跟进约定；考研助手接收已确认方法及待定推测 | 区分闲聊/情绪与任务，不把推测存成用户事实；已接受责任经过Noting/压缩仍可接续，不靠每轮重述。结合实际排期/Notebook变化判断，不仅看回复口吻 |
| P07 | 两助手回答相同的简短使用体验问题，并核对各自完整工具轨迹 | 直接据自身实际可见行为回答，不查仓库/另一Profile、不调查Harness；同题行为与各自职责相关。DeepSeek自述有误时记录差异，以轨迹为准，不按其建议直接改产品 |

本轮不单独重测官方 CLI CRUD 或给 provenance 小脚本新增严格门禁；P02 的真实写入用于证明 Harness 完整业务链。正式执行前先确认插件 Default 禁写机制，并收到用户待补身份文档；不以 prompt 约定冒充自动同步已禁写。报告须区分机制错误、模型未遵循提示、环境错误及未覆盖项，失败后只补相关链。短时排期及测试数据清理只限本轮创建对象；每日任务保留或清理状态在交回时明确，不误删用户既有任务。

### 实测消息前缀与时间尺度（R3-028）

执行子 Agent 向两个 Hermes 主模型发送的**每条用户消息**均须添加以下前缀（包括追问、纠正、批准与恢复后消息），不能只在首条告知；测试正文接在前缀之后。这是被测主模型的角色边界，不禁止外围测试执行者按计划收集日志与证据。

> 【部署前实测说明】这是 Hermes Secretary 实际部署前的真实场景功能测试，你正在配合测试。时间尺度收缩：现实每10分钟代表测试中的一天；本测试的“每天”按每10分钟执行，“今天”指本条消息注明的测试日时间窗口。你不是开发者，你是测试官：仅作为 Hermes 的主模型，遵守上下文赋予你的人格与职责，模拟真实为用户服务的场景。不访问当前 Hermes 工作区之外的文件，不查看代码仓库，不研究所处 Harness 背后的代码机制。以当前可见上下文为唯一行动指导；禁止调查或建议 Harness 代码机制，只站在用户助手角度汇报工作体验，并如实直接回答提问，不去调研代码库。按既有授权访问 NM：主助手只读 Default 和“考研复习” Space；考研助手可操作自己的“考研复习” Space，不读取另一 Hermes Profile。

前缀后明确填入本轮固定起点T0、当前测试日编号及真实起止时间（带时区）；第n日为 `[T0+(n-1)*600秒,T0+n*600秒)`。时间收缩只用于本测试的需求与Schedule，不修改系统时钟、数据库时间或Harness内部24小时规则。让模型创建的提醒正文也携带10分钟时间尺度和授权Space，实际到期使用当前真实时间判定窗口，不能固定沿用登记当天。测试前缀不塞入应调用哪些工具或预期结算答案；这些由既有Harness/Persona指导，外围执行者观察。原生slash操作通过正式命令入口执行，不给slash前加文字导致失效，也不将其伪称为发给模型的普通用户消息。

以下为原计划的机制覆盖与历史环境描述；与上述新授权冲突的阶段限制不再适用，不能作为执行阻断依据。

依据：本轮 snapshot-index.md、baseline.txt；公开冻结 d19018a7ba3e38ae01f76aa57821b55cbc15ff58 的白板全文（含 types/scenarios）和 07；旧 01/02/04/06 仅继承索引明确保留条款；个人 Provider 97078118287bcd41ba8b02aa5a3a108c5026f7af 的 PHASE3 现行 §1–7。R3-016～018补充执行授权、模型与 round3 profile。待验双仓 SHA、Verification 版本、公开操作入口由主会话集成收敛后填写。

范围是本地公开核心及独立个人 Provider fixture 接线；UI 改版、正式云端部署、真实 NM Memory/Thread/Space 写入不在本轮授权内。provenance 小脚本只复核已有基本模拟调用证据，不重复严格验收或官方 CLI 通用测试。

## 2. 环境与准备

### 2026-10-18 本次实际环境（覆盖下方历史环境限制）

- 本次在新双 Profile 与真实 NM 上执行；主仓 `4e21f787595571cad8efe36fa725fef1f8b2636f`、UI `7f0fea60463c6731f8e04a00db923d28b80ade19` 加各自既有 dirty，个人插件仓 `6d7ab899f31ed21697a8554cf4c7e24e8b9c0c5c` 加已安装修补。不是冻结版本全量结论；版本、安装副本、配置及 dirty 指纹见 ignored `evidence/validation/run-info.json` 与环境 manifest。
- 正式入口：真实 IAB `http://127.0.0.1:5174`，独立后端 `127.0.0.1:53446`。真实 Hermes 原生 custom/chat_completions/DeepSeek Flash，推理 medium；未用 K3、App Server 或 Proxy。
- main-assistant/exam-assistant 的实际持久 system prompt 均包含对应 SOUL，证据 `actual-soul-loading.json`；两者均启用 Noting/Scheduler。主助手 `default/archive_enabled=false`，考研助手 `space/archive_enabled=true`。Default 的手动访问依 SOUL/逐条前缀约束，原生终端没有 OS 沙箱，不宣称不可绕过的只读权限。
- T0=`2026-10-18T13:45:39.216+08:00`；第1日 `[13:45:39.216,13:55:39.216)`，第2日 `[13:55:39.216,14:05:39.216)`（Asia/Shanghai）。每条普通用户输入均附固定前缀、实际测试日与合成素材说明；原生 slash 走正式命令入口。没有更改系统/内部时钟、SQL写状态、内部 helper 伪造结果或重复 suite。
- 首轮已开始后，用户新增联合 Idle 配置：双 Profile `noting.idle.enabled=true/threshold_tokens=100000/delay_seconds=5`，原生独立 Idle Compaction 按互斥契约关闭，模型 context 仍262144。环境 Agent 在两 Turn idle 后安全重启自有后端至 PID55982；既有 Conversation/排期保留，之后继续。配置生效证据 `idle-100k-5s-configuration.json`；不把累计 usage 当上下文阈值。
- 完整原始轨迹、真实 NM 结果、只读 DB 快照与观察脚本均在 `.hermes-dev/validation-personal-20261018/evidence/validation/`，仅本地 ignored 保留；正文只记录合成资料与脱敏结论。Default 私人检索正文不进入本报告。环境准备阶段的 Bundle 403 已由正式 CLI Bundle 修补关闭，不掩盖本次运行中独立的 Thread 归档失败。


- 所有真实产品运行、DeepSeek 模型复测及本验收统一使用仓内 `round3` 隔离 profile：`.hermes-dev/round3-runtime/profiles/round3`。启动包装器为 `.hermes-dev/round3-local-20261017-l0/run-native.py`；它只在内存读获授权本地密钥，不打印密钥，不接 App Server/Proxy。
- 官方 PM `.venv`、现有锁不变；macOS arm64。模型走 Hermes 原生 custom / chat_completions / DeepSeek。执行时记录实际模型、API、推理设置和请求/响应证据，不以配置存在冒充联通。
- 使用原生 CLI 或既有 TUI Gateway RPC：创建/恢复/输入、slash、压缩、rewind/fork；无须启用后置的新 UI。执行者写明实际入口与可重复命令。若不能通过这些入口完成必要用户操作，记录阻断，不能直接调用内部 helper 冒充端到端结果。
- 各场景使用 round3 中不同 Conversation；有状态依赖时继续同一 Conversation。需要干净状态时先保留脱敏证据，再使用新 Conversation 或重建测试库，不连接用户真实状态。后台任务、RPC和子进程均绑定 round3。
- 个人 Provider 的网络只指向本机隔离 HTTP fixture，服务记录与 ACK 供观察；不得连接真实 NM。其端到端接线可使用同一 round3 profile 的受控配置阶段，执行后恢复公共配置，避免污染公共模型证据。若已有效开发证据覆盖真实 host→fixture 链路，引用同版本证据，明确它不证明真实 NM 服务可用。
- 证据集中于 ignored `.hermes-dev/round3-runtime/evidence/validation/`，只在报告保留摘要/路径/版本/时间。不输出密钥和完整私人上下文。数据库只含本轮合成数据。
- 本验收不重跑大型 suite。并发时序、强制 overflow、External 模拟等机制证据可引用同版本开发报告；模型行为、结构化工具可调用性、用户恢复结果须有实际产品入口证据。

## 3. 用户目标与场景覆盖

### 当前 P01–P07 首轮结果（已执行）

| 场景 | 已观察结果 | 当前结论/剩余 |
|---|---|---|
| P01 | 双 SOUL 实际加载；主助手读取授权两 Space，未观察到Default写入；双Notebook均真实提交 | 身份/实际访问边界通过；首轮接入失败保留，自动归档§5.2及Recall§5.1本次定向样本已通过，仍不外推长期可靠性 |
| P02 | 暂缓/只改措辞时 Memory 为0；限定批准后真实创建1条；Noting先成功归档源#1，后归档Candidate#5，未完参数页/未认可猜测保留 | 部分失败：批准/真实写入/F16主链通过；provenance传递、提案回查/内容标签行为缺口未关闭（VP-02） |
| P03 | 新会话真实读取NM记录；同Conversation跨成功压缩读回原文；明确跨同Profile后找回最早确认/修订 | 主链通过；首次新会话未主动找其他Conversation，NM记录没有可用来源链接，用户多补一句后才恢复历史 |
| P04 | 第1日cold、第2日warm均真实到期/真实读取考研Space，正确区分1条新增与次日0新增；续建次日提醒 | 到期/读取/时间窗链通过；第二日无新增且无需参与仍可见汇报，安静性偏差见VP-05；不是现实24h证据 |
| P05 | 全部自有页面关闭后runtime/lease归零，首个到期由宿主恢复同Conversation/Profile；第2次使用同一warm runtime | 通过：正式删除唯一未来排期，最终自有runtime/poller/lease/pending全归零，服务与测试资料保留 |
| P06 | 闲聊未新建排期/行动；青禾跨Noting、压缩、冷恢复仍待确认；方法修订与参数页未完区分正确 | 已观察主链通过，不外推长期24小时/几个月表现 |
| P07 | 双助手已回答同题体验；未查仓库/另一Profile；自述按实际命令核对 | 可观察身份/直接回答通过；考研自述把默认unit_type说成显式设置（VP-03），不能全信，不外推K3 |


| 目标编号及冻结依据 | 完整场景编号 | 场景类型与起点 | 数据/顺序选择依据 | 当前执行结果 |
|---|---|---|---|---|
| G01 Main 三能力独立，07 §3/6.3/8.2，04 §3 | V01 | 新建、warm与cold恢复 | noting/scheduler四组合；local参与独立 | 未执行 |
| G02 持续对话原文取证，07 §5/8.4/8.8 | V02 | 同Conversation跨压缩→读取 | 中文短词、精确身份、邻域、时间与真实纠正 | 未执行 |
| G03 跨Conversation授权取证，07 §5 | V03 | new/fork/rewind后搜索 | 默认当前与显式跨域；合法fork源、失效父路径 | 未执行 |
| G04 Notebook语义整理，白板C/L/E与07 §4/8.11 | V04 | 真实多Turn材料→手动联合整理 | 七类型、candidate、用户认可与AI建议区分 | 未执行 |
| G05 持久child与前缀，07 §3.2/8.11–12，04 §4.4/4.6 | V05 | 真实child工具循环和续跑 | 四工具结构调用、父多模态、5Turn/overflow | 未执行 |
| G06 四入口、D01与原生压缩，07 §8.1/11.1，04 §4.5 | V06 | auto/manual/Force/Idle | 同区间去重、成功边界、External拒Noting | 未执行 |
| G07 Snapshot发布与恢复，07 §3.1/8.13 | V07 | 合法异步完成与pointer变化 | 晚到/忙碌/压缩fence；完整正文、无额外Turn | 未执行 |
| G08 提案与批准边界，白板L/F与07 §8.10/8.13 | V08 | /propose-persistence及超限通知 | 等于/超过、延期/纠正、部分成功不全结算 | 未执行 |
| G09 自主登记与独立排期，07 §6/8.6/8.9 | V09 | 用户未来需求→Schedule Table | instant/deferred、中文意图、Cron分流 | 未执行 |
| G10 提醒可达与ACK，07 §6.2/8.14，02 §3.10–12 | V10 | 到期idle/busy、多条deferred | 同批载体、失败重试、实际携带响应、迟到 | 未执行 |
| G11 修改撤销与恢复，07 §6.2/8.14 | V11 | pending后更新/暂停/删除→恢复 | 接纳前撤销与接纳后在途、重启、24h notice | 未执行 |
| G12 通用原生不变量与旧面退出，07 §7/9.1 | V12 | 辅助runtime、关闭、历史旧工具 | 无新权限、legacy明确失败、预算真实反馈 | 未执行 |
| G13 个人Bundle与Recall，PHASE3 §2–3/6 | V13 | Main/cold/compaction与fixture | 稳定root、短CJK、离线无旧指针、恶意标题 | 未执行 |
| G14 completed归档，PHASE3 §2/5 | V14 | Main/Cron成功失败、续接/rewind | host完成gate、脱敏、ACK suffix、分歧停止 | 未执行 |
| G15 窄provenance接线，PHASE3 §4.1及R3-010 | V15 | 已有基本模拟调用证据 | 官方CLI真ID→仅补Metadata；partial不重建 | 未执行 |

场景是完整用户目标的分组，不表示每组只有一次调用。所有正式人／模型可见绝对时间均检查秒精度及明确时区，包括Notebook工具／Proposal／Framework、Scheduler嵌套canonical时间和Recall日期；内部精度、用户表达原文与纯日期不因此改写。实际执行记录须区分表内行为不同的分支；等价数据可复用，不得用一个成功样例代表所有失败与恢复分支。异常时序优先引用正式路径受控证据，用户观察与恢复仍记录实际结果。没有真实服务授权的个人线限制必须保留。

## 4. 详细场景与执行结果

### 2026-10-18 首轮实际旅程（P01–P07，已完成）

| 实际顺序与入口 | 输入/起点 | 预期 | 实际观察与证据 | 判定边界 |
|---|---|---|---|---|
| 双Profile首轮，IAB普通输入 | 主助手每天跟进考研Space；考研助手已确认方法A、未核对页B、未认可猜测、方法修订C | 区分角色/Space/权限与事实、未完、猜测 | 主助手实际登记第1日Instant；考研助手真实检索space，明确暂缓写入。`first-responses.json`、`after-safe-restart.json`，实际SOUL见`actual-soul-loading.json` | 不能用身份自述代替加载证据；Default原文只留ignored |
| 主助手纯分享及青禾约定 | 不安排任务/建议；青禾下次由用户告知，先待确认、不另设提醒 | 闲聊不任务化，责任不伪完成 | 无新Schedule；Notebook把青禾保留为situation/gap，闲聊未造action。压缩/冷恢复后仍答待确认，拒绝编结果；授权NM语义近似结果未被当作代号证据 | P06主链有效；没有几个月/现实24小时证据 |
| 两Profile正式`/compact`与`/notebook` | 主助手3轮，考研助手3轮 | Main压缩与Noting各自记真实结果，来源可见 | 主助手13:48:32压缩committed、13:48:35 Notebook提交7条；考研助手13:48:29压缩would_grow拒绝、原文未删，但13:48:57 Noting独立提交。保留第一次拒绝，不冒称成功 | `first-noting-pending.json`与原生日志；首考研压缩未成功是有效保护，不是凭计划通过 |
| 考研`/propose-persistence`→只改措辞 | 仅为草稿；把边界改边界情形但不批准 | 不写Memory，提案可审批 | 原生提案列正文、space、source entry/version及标签；只改措辞后仍未写。外围正式CLI读回space Memory总数0，`nm-before-approval.json`。本次Main未在提案时用History回读原话，且没有把decision映射为输出内容标签 | 暂缓边界通过；原文核对/标签行为存在缺口 |
| 明确批准单条合成方法卡→实际NM | 仅正文含合成测试说明、space精确ID；参数页/粗心猜测不批准 | 真实创建、限定范围、准确报告结果与来源 | 原生terminal执行官方CLI m add，真实返回created；外围show核对相同ID/Space/正文/两个获准标签，`nm-actual-memory.json`。本次绕过已安装provenance接线，命令没有传Hermes Conversation/Message/entry来源，返回source=cli；自述也承认来源仅留在Conversation | 写入主链通过；不能将成功Memory ID冒充来源元数据已传递 |
| 成功写入后考研正式`/compact`、第二Noting | 原来源decision#1及Candidate#5，未核对参数页/未认可猜测 | 先处理已覆盖来源，再关闭Candidate；未覆盖保留 | 13:51:29原生压缩committed。child真实History读写入轨迹；先修引用，#1首次归档因#4入向引用被正式拒绝，模型修引用后成功归档#1，再归档#5。当前#2保留未核对页/#3 gap/#4未认可限定/#6 conversation指导；#1v13、#5v14为archived。`f16-observation.json`、`post-write-noting.json` | **现行F16本样本通过**，有真实写入/先后顺序/未覆盖保留；无partial/unknown写入的新实测，不外推全部分支 |
| 原考研Conversation跨成功压缩回查 | 问最初与批准版的差别、参数页状态 | 正式History查原话，区分修订与未完 | 实际History读回原始用户消息，分别呈现13:46确认、13:48修订、13:49只改措辞、13:50批准；参数页仍未核对，不等于不成立 | P03历史主链通过；不以模型说“读过”代替实际tool轨迹 |
| 考研新Conversation长期召回→明确同Profile跨对话 | 先问现有版本/历史未知；后明确原讨论在同一考研助手另一对话 | 读NM实际结果，不编旧版；需要时找原始History | 首轮实际NM检索/精读返回本次创建记录，保留合成身份，诚实说明NM无旧版/Thread；未主动跨Conversation。用户补充实际位置后，正式History cross_search/read恢复原确认/修订/批准；一处参数错误后修正，未绕权限。没有读Default或另一Profile | P03通过并记录用户仍需补一句的负担；NM来源缺失不能由跨对话搜回覆盖掉 |
| 双助手同题体验 | “实际完成了哪些事，还有什么不确定/未完成，不调查代码” | 直接据可见工作回答，可与轨迹核对 | 主助手给登记/第一次核对/NM读取盲区/青禾未确认，未查仓库；考研助手给写入/回读/History和来源未落字段。考研自述把默认unit_type=context说成自己显式设置，实际命令没有该参数 | P07按实际行为观察有效；自述不是事实源，不用于K3结论 |
| 首日冷态真实到期 | 页面全部关闭；13:55:06正式active_list空、两owner lease空；OS采样无自有poller但宿主scheduler保留 | 无用户新消息也能恢复正确Profile/Conversation，实际读取NM | 13:55:30到期，约13:55:33 durable Instant admitted，唯一carrier；新runtime88520b78绑定主助手原Conversation。真实模型读space Memory/Thread/Library，正确识别13:50:08新增1条，不把无Thread推成未学习，并建次日14:05:20提醒；结束后runtime再次回收。`before-first-due.json`、`threads-all-cold-before-due.txt`、`first-due-completed.json`、`durable-watch.jsonl` | P04第1窗口与P05冷恢复通过；Instant沿admitted语义，ACK空不误报失败 |
| 第2日warm真实到期 | 主助手页面重新打开并完成青禾/体验问答后保持订阅；14:04:31同一runtime27f9d3d4 idle、lease有效；考研不再写新资料 | 实际读取当天新记录，不把第一日旧记录当第二日进展；无需参与时保持适度安静 | 14:05:20到期，14:05:21.495 durable Instant admitted，唯一carrier且claim_attempts=1；模型真实list Memories/Threads/Library，正确保留第1日唯一记录、判断本日0新增，不推断未学习，建第三日14:15:20。却仍输出“记录不足”的可见汇报，见VP-05。`before-second-due.json`、`second-due-completed.json` | 两次均由真实时钟到期，无手工触发；是600秒测试日里的逐日one-shot续排，不是固定600秒周期排期；只覆盖实际读取前的记录，不冒称读取未来窗口尾部 |
| 正式结束与清理 | 14:05:56用户结束测试，仅取消本轮本Conversation的未来跟进、保留完成项/资料，不改NM | 取消第三日future，不再续排，释放自有资源 | Main正式scheduler list→delete→list确认第三日排期已删，已完成两条保留；所有自有IAB页关闭。14:07:02 active_list空，双Profile active/turn lease空，无未来Schedule、无pending reminder，两个Instant均delivered且各claim一次；OS采样只留常驻宿主scheduler，无自有poller。只读watcher已终止，后端health正常，未停共享/新服务 | `final.json`、`threads-final.txt`、`cleanup.json`；新Profiles/Conversation/Notebook/1条合成Memory保留供用户复核，未碰原round3 |

当前所有具体 ID、完整指令/结果/时间和来源动作顺序保留在ignored证据；以上是使用结果及可复现序列，不是实现者解释。业务旅程没有降低100000阈值或灌入无意义文本；UI实际Context最高约16%×262144，且实际admission均为manual，未达到100000。自动Idle阈值触发分支未覆盖，双Profile手动联合链已实际观察。15条不同普通用户消息均带完整前缀/真实窗口/合成声明；物理压缩保留副本按UID去重，不按DB行数误计额外输入。


所有场景执行前统一记录：双仓 SHA、round3 配置摘要、起点 Conversation Ref/物理 Session、历史准备来源。执行后逐项追加实际输入/完整操作/输出和状态/证据时间路径/结论及偏差。以下为主会话批准的输入与预期，当前全部未执行。

### V01 三能力开关与恢复
通过原生配置和会话入口依次操作 noting/scheduler 四组合；同一 warm Conversation 下一Turn请求观察Schema、Prompt与dispatch，再cold恢复；用 `/noting off`、`/notebook`、`/noting on`检查局部参与。预期：合格Main始终History；Notebook只按global；Scheduler独立；local不重建root、不取消Schedule；坏配置只关对应功能并具体说明修法，旧key明确报错不迁移。与原生idle compaction互斥按现行契约反馈。辅助runtime不从此获得Main权限。

### V02 跨压缩原文与身份
用户依次说“项目代号是青鹭，截止周五”“纠正：截止周六，尚未承诺今晚提交”；完成真实压缩后要求查证原话与纠正，使用返回的Message Identity继续read邻域。预期跨压缩原文可读，锚点必达，身份不是物理row/session；时间边界按消息时间，中文短词可搜，空结果与不完整/错误区分。不得读Prelude或把压缩scaffold当原话。大结果的Noting反馈引用V12机制证据。

### V03 跨域与路径变化
创建第二Conversation放置独特合成短语；当前默认search不得泄漏它，显式cross_search才可定位。对第一Conversation执行真实fork并在父侧rewind/edit，沿fork读合法继承源，再在父侧查询失效段。预期fork拥有新ref但保留合法原文；无效父路径排除；辅助/未知目标不泄露存在性；new/reset不承袭旧Conversation身份。

### V04 真实模型整理语义
输入一组连贯合成材料：周末探访安排及一个已委派行动；亲属处境与尚缺的具体信息；用户提出的一个问题、一条带“可能”的认识和明确决定；一个AI建议明确被用户否决。经正式manual联合入口启动Noting，观察实际四工具调用与提交。预期七类型按需要而非凑数建立，gap附情景、不编动机/结论；AI建议不写成用户确认；来源完整、candidate聚合引用不搬走源。继续输入纠正、完成证据和部分交接，再整理，检查稳定entry与版本、no-op不续期、数组替换及归档引用无悬空。真实非确定性语义按证据支持范围判断，不要求模型逐字复现测试文案。

### V05 child执行、结束与缓存前缀
用正式父runtime启动持久Noting child，保留模型真实请求序列，至少覆盖工具循环及同child续Turn。父消息包含一个可由原生路径承载的合成图片块；对比每次请求root/tools/messages完整冻结前缀，后缀完整声明四工具；验证模型能结构化调用新工具并实际dispatch。继承schema中的父工具不授执行权。finish与其他工具混批必须整批拒执行；独立finish成功后冻结工作态，原生Turn返回才提交。五Turn/overflow强制有效提交、失败/中断不提交可引用同版本正式runner证据。实际cache-hit仅按provider响应/log记录，字节相同不冒称缓存命中。

### V06 联合触发与区间
在round3配置合法窗口/阈值，分别经原生手动、自动压力、Force及Idle触发。观察冻结在压缩之前，父压缩无需等待child；Force占用后同区间换Anchor、结束/失败/rewind不再启动，真实成功压缩新区间才可新启动。Idle要同时满足Main空闲delay与实际token，新Main Turn取消等待。External来源真实派发标记的受控证据覆盖所有入口：只拒Noting，无freeze/admission副作用且通知抑制正确；原生必要压缩、History/Scheduler仍工作。native/unknown不新增拒绝。失败/no-op压缩不退休Force notice。

### V07 完整Snapshot通知
通过合法后台整理并在父会话继续活动，观察完成时一条Framework含完整已提交payload及结束信息，不启动新Turn；忙碌时在Turn结束的durable tail出现，cold恢复仍可读取已落库正文。受控正式路径证据覆盖B先完成A晚到、A排队后B生效、pointer核对与append竞争、压缩fence；旧提交仅审计、不发过期正文或Proposal。rewind选pointer不凭空发完成通知，Scheduler不被重选改变。

### V08 提案与结算
以V04合法candidate调用 `/propose-persistence`，另以隔离配置降低提案阈值产生真实超限通知；边界等于不触发、大于才触发可引用计数机制证据。预期同一共用指令、完整正文，不要求用户再次下命令；Main按需读原文，展示内容/目标/labels/provenance/entry-version；仅提案不调用目标写入。用户输入“先推迟”“只修改措辞”不作为批准。后续使用合成正常Conversation轨迹记录明确批准及部分成功/失败，下一Noting只结算成功覆盖，不恢复旧内容、不因降计数捏造或删除来源。不执行真实NM写入。成功写入可沿已获授权的round3合成USER原生memory例外，或复用同版本真实正式轨迹；不得把测试文字声称“已保存”当作实际成功。逐项核对Candidate和source前后版本：全部成功且无保留理由的source退出；部分覆盖只移除成功部分，新增内容、未完责任及其他候选依赖继续保留。不以仅Candidate归档替代source结算。

### V09 Scheduler用户登记
用户要求“稍后提醒我检查探访安排”，模型应当立即调用Scheduler确认真实登记，不依赖Notebook或Memo；选择instant与deferred并列表查看。关闭Noting后继续操作；切到明确独立Cron任务意图检查正确分流与原生工具未被全局覆写。表为空或未来24小时缺instant时工具notice供模型判断，不自动由代码补排期；用户明确关闭自主follow-up时不强推提醒。

### V10 到期与请求ACK
短时合成instant在idle时唤起同Conversation，busy时转pending deferred而非排第二Turn。两条deferred在真实Main请求前形成一条durable carrier，正文每项schedule_id/due_at/mode/content，deferred无timestamp；instant只在实际entry写一次timestamp。模型成功响应实际携带的请求才ACK。受控provider失败/空响应/载体未携带的正式路径证据应证明不吞pending；恢复后一条原载体可成功结算，不重复持久化。迟到once仍可投递。

### V11 改定义、在途与重启
pending后通过工具更新content/mode、改期、pause/delete；下一实际materialize必须用当前合法定义，旧witness不得落库。已admitted carrier后pause/delete保留在途结果，late ACK不复活排期；周期resume不无限回放，once消费后不重播。重启round3 runtime后读取持久Table/pending继续合法投递。instant最终投递与busy降级最终注入重算24h全表，混批只附一次，unknown不假称无覆盖；不因Notebook rewind/fork自动复制或重绑排期。

### V12 原生边界与旧工具退出
通过正式注册/dispatch证据核对Main三能力、Noting四工具和辅助runtime；对历史旧名执行应返回明确legacy_tool_removed与新工具引导，历史不删除/重放。单结果spill和批次总裁剪分别在真实executor路径构造：Noting History反馈先缩窗口，单条仍超限明确无法继续，不提示无权工具；其他runtime原生提示/预算/落盘不变。无个人Provider安装时核心能加载与运行。

### V13 个人Bundle与Recall
仅本机HTTP fixture：Main首次构造、cold新runtime无有效root及compaction原生重建获取fresh稳定Bundle（无Working Memory）；cold resume仍有有效冻结root时沿用该root，连续Turn不每次重建root；有意义输入包括短CJK触发Memory Search指针（完整ID/标题/可得时间、不正文）。恶意标题编码为不可信数据。端点故障不得复用旧指针，保留不可用/Memory check短提示；History仍可用。Cron仅归档、Noting/其他辅助无独立Bundle/Recall网络；无模型工具Schema/第二同步插件。

### V14 completed归档与收据
公共真实host生命周期接本机fixture：completed且未failed/interrupted才sync；失败但有final_response不上传。跨压缩Main使用合法History及host批量egress脱敏；Cron仅自身合格正文。相同ACK前缀只上传suffix，失败不推进，重试可恢复；continuation同thread，new/fork分开。rewind/edit导致prefix差异返回reconciliation-required，不覆盖旧Thread/换ID。endpoint/Space隔离，无自动蒸馏或治理变更。引用开发46项时标明其真实SessionDB/MemoryManager与fixture范围；公共完成gate集成后受影响路径必须另有证据。

### V15 provenance小脚本
只审阅本轮P2基本模拟调用证据：参数数组调用官方CLI、解析真实ID、同配置仅补hermes_provenance并保留无关metadata；partial明确ID、修复不重新m add，unknown不猜ID。确认安装/skill指向新入口，其他管理回官方CLI。不重复真实NM写入、不把小脚本例外扩为整个Provider免验。

## 5. 问题、修复与复验

下表保留首轮问题与当时状态，最新定向复验以§5.1、§5.2为准，不把历史“未修”混作当前全部状态。

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| VP-01 | exam三个普通Turn及后续completed/压缩/关闭边界自动归档 | 原生日志反复`Personal NM Thread sync not acknowledged (MemHTTPError)`，本profile receipts表始终0；官方CLI threads读取0。Memory显式写入成功与Thread归档失败分开记账 | 个人接入/外部写路径失败，根因未由验收者查代码或改实现；不阻碍继续其它旅程 | 未修 | 未刷绿，原始失败保留；与准备阶段Bundle403分别记账 |
| VP-02 | P02批准后Main原生terminal直接m add，再m show | 创建内容/Space正确，但没走Hermes provenance接线、未传Conversation/Message/entry来源；提案也没有回读原文或携带decision内容标签。`actual-write.json`、`nm-actual-memory.json` | 模型执行/提示可见指导的行为缺口；目标端支持/保留元数据不是额外Secretary门禁，本处记录的是输入未传递 | 未修 | 原业务链已继续完成F16；不靠追加正确答案重跑 |
| VP-03 | P07考研助手自述 | 说unit_type=context由其命令参数设置；实际m add未传unit_type，先前还称系统默认。原始命令与自述可对照 | 模型自述不可靠的实际样本；不能据此改代码或推断K3表现 | 未修 | 以正式命令/回读结果为准 |
| VP-04 | 普通Turn的个人Provider自动Recall | 最终main/exam分别7/10条`Personal NM recall unavailable (TimeoutExpired)`；显式官方CLI检索和精读仍实际成功，记录见`provider-failures-final.json` | 自动召回存在运行/预算/环境退化，未由验收者查源码定因；手动成功不能证明自动路径通过 | 未修 | 保留首次和重复超时，继续合法用户旅程，未调参数刷绿 |
| VP-05 | 第二日真实Instant，到期读取0新增且无用户参与项 | 正确识别旧Memory不属于当天，但仍主动输出“记录不足/第三日已安排”；与先前自行确认的“只是记录不足也不主动打扰”纪律不一致，实际UI可见 | 模型主动性/通知行为偏差。用户原输入同时含“无记录就说明记录不足”，保留这处表达张力交主会话判断，不擅自改Prompt或新增硬门禁 | 未修 | 保留首轮真实输出；未追加答案诱导刷绿 |


### 5.1 VP-01 / VP-04 定向真实复验（首轮之后）

本包由root接收安装环境后放行，仅验证修补后的真实接入，不是新一轮全量门禁。实际入口为Chrome中的同一5174正式聊天页（本时段IAB不可用，未改产品入口）。保留原T0及完整前缀/当前第4测试日窗口，两条考研消息只回顾合成方法和未核对状态，主助手只读查询Default资料；未批准新Memory/新Reminder，也没有手动import、内部归档helper、SQL写状态或新增模型会话。

- 安装版本：个人client SHA256 `3246b0c571e39a67628f7675bbad66f74a0d9b1d085c80c63dd5ed7b86641b47`，provider SHA256 `4bcdc03ffb522056e837a4f209b0735b6853ad67f1210968f8ec9cb029916c2a`；自有backend PID79760。两Profile `recall_timeout=5`；main归档关闭、exam开启，其他Idle/模型/SOUL配置沿已核对环境。20项fixture结果仅为实现受控证据，不充当本次真实NM通过。
- 边界起点：14:16:53正式CLI只读考研Space Thread总数0；本地receipt0。日志用该时刻的行数切开，旧main7条/exam10条Timeout和exam16条归档失败全部保留，不与新时段混算。`vp01-vp04-retest-start.json`、`vp01-vp04-before.json`。

| 复验目标与正式操作 | 真实观察 | 结论与证据 |
|---|---|---|
| VP-01首批：既有考研Conversation普通Turn1，回顾已确认方法 | 真实模型正常完成；14:17:33.931 completed归档报`Thread sync not acknowledged (RuntimeError)`，本地receipt仍0，正式CLI目标space Thread仍0 | **失败**。`vp01-first-boundary.json`、`vp01-vp04-first-turn.json`。现有正式日志只给RuntimeError类别，没有HTTP状态/底层错误正文；不冒称本次已证明403/1010 |
| VP-01后续：同Conversation普通Turn2，确认参数页仍未知 | 第二Turn正常完成；14:18:13.360再次RuntimeError。页面关闭后正式生命周期又在14:19:24.753、14:19:27.095重试失败；共4条新警告，仍没有任何ACK或receipt | **仍失败**。首批未成功，故真正的已ACK前缀→suffix、同Thread ID及服务端消息数一致性均**未覆盖**，不能用“请求已发/模型答复成功”代签归档成功。`exam-assistant-vp01-vp04-retest.log`、`vp01-vp04-final-observations.json` |
| VP-04真实Main自动Recall：主助手1Turn、考研2Turn | 三条新用户记录的正式`api_content`均包含`<memory-context>`，没有旧`Automatic NM recall unavailable`文本；主助手与考研第1Turn明确“无自动指针，不代表不存在”，考研第2Turn实际含本次合成Memory完整ID、标题及创建时间的指针。新时段两个Profile均0条Recall错误/Timeout | **本次3个样本通过**。这是正式预取后的模型输入证据，不是手动CLI成功或模型自报。`vp01-vp04-observations.json`、`vp01-vp04-after-turns.json`；其中空结果只证明成功返回空，不能当作相关性/全量召回通过。样本不证明未来不再超过5秒，不抹去原2秒下失败 |
| main archive=false及授权边界 | 主助手新Turn工具轨迹均为CLI读取；无归档警告、无receipt、未观察到Default写入。考研未新建Memory，服务端最终仍为原1条合成记录；无新增提醒 | 本次观测通过；仍不把终端/SOUL约束称为服务端只读沙箱。`vp01-vp04-new-tool-calls.json`、`vp01-vp04-memory-final.json` |
| 资源回收与保留 | 两个自有Chrome页均关闭；14:19:54正式active_list空，双owner active/turn lease空、无未来Schedule；OS采样无自有poller，仅留宿主scheduler；backend health正常。没有启动watcher、停止服务或操作原round3 | 本包清理完成，Profile/Conversation/Notebook及原合成Memory/服务保留。`vp01-vp04-final.json`、`vp01-vp04-final-observations.json`、`vp01-vp04-threads-final.txt` |

本包完整原始证据仍只存ignored `evidence/validation/`。Thread失败目前可交回的最短归因事实为：**正式completed/结束hook→RuntimeError、4次、receipt0、目标Space Thread0、无底层HTTP状态**；验收者没有再试真实导入或研究产品实现以猜原因。VP-02保持原真实行为缺口，没有塞入正确答案重测；VP-05按root复核判为“原指令有张力、需澄清的体验观察”，不是已证明代码缺陷，原输出保持。

### 5.2 VP-01第二次定向真实复验：首批创建→同Thread后续suffix

root接收创建分支修补并确认重装后执行：无ACK首批改为普通import，有ACK后仍沿checkpoint suffix。根因诊断及7项受控结果见本地`provider-thread-transport.md`§7，属于实现/诊断证据，不替代下面正式用户入口结果。已安装provider SHA256 `9bc6e21f08f8469810988bdc310e02d100573eae45bf4703612434db014c0ca7`；client仍`3246b0c571e39a67628f7675bbad66f74a0d9b1d085c80c63dd5ed7b86641b47`；backend PID91341，UI5174不变。

本包仅原考研Conversation两个普通真实Turn：A回顾已确认方法/未核对项，B再问参数页是否已有结果；均带完整固定T0、第5测试日真实窗口及合成说明，不要求模型操作Thread、不批准新Memory/Reminder。主助手没有模型Turn；没有手动import、调用归档helper、SQL写状态、新建Conversation、重测F16/提醒或suite。

| 顺序/正式入口 | 操作与实际结果 | 证据与判定 |
|---|---|---|
| 起点14:27:42 | 原考研Space Thread0、receipt0，保持前次安全失败状态；读取日志行数作为新时段边界 | `vp01-r2-start.json`、`vp01-r2-before.json` |
| A普通Turn→真实首批自动归档 | 14:28:00真实模型completed；14:28:02.591585本地正式receipt首次推进到22个fingerprint。官方CLI只读show返回1个新Thread，space精确ID为space，source=hermes，total_messages/message_count/实际数组长度均22 | **首批补归档通过**。`vp01-r2-first.json`、`vp01-r2-first-threads.json`、`vp01-r2-first-thread-show.json`；包含原历史与本次A用户/助手，非手动创建 |
| B普通Turn→同Thread后续suffix | 14:28:38.911真实模型completed；14:28:39.737367同receipt推进到24。服务端仍同一个Thread/同space，总数24，仅比前批新增user/assistant两条；前22条role/content/timestamp/服务端ID/order_index完全未变，receipt原22个fingerprint前缀也未变 | **后续增量结果通过**。`vp01-r2-second.json`、`vp01-r2-second-thread-show.json`；没有更换Thread、全量覆写或可见重复 |
| 正文/计数/身份独立核对 | 24条服务端role与正文逐项均能匹配该考研Conversation原始DB记录；service消息ID唯一、order_index连续0–23；A/B校验标记在user消息各出现一次。首批22=receipt22，后批24=receipt24，scope的Thread/space与服务端回读完全一致 | `vp01-r2-consistency.json`的14项只是真实记录一致性核对，**不是新增产品suite或替代真实入口**；没有抓取线上HTTP请求body，不以此宣称传输字节级证明 |
| 页面关闭后无重复与资源清理 | 关闭唯一自有Chrome页，14:30:30再读同Thread仍24条，全部消息对象与第二次读取一致；receipt仍24。两Profile active_list/active lease/turn lease空，无未来Schedule；OS无自有poller，仅常驻宿主scheduler，health正常 | `vp01-r2-final.json`、`vp01-r2-final-thread-show.json`、`vp01-r2-final-observations.json`、`vp01-r2-threads-final.txt`。服务/Profiles/原始资料保留，无自有watch进程 |
| 权限及邻域观察 | main未发模型消息、receipt仍0；两Profile本包无新归档错误/Recall错误；考研Space仍仅原1条合成Memory，无新提醒。VP-04既有3样本不重测，本包无异常仅作随行观察 | `main-assistant-vp01-r2.log`、`exam-assistant-vp01-r2.log`、`vp01-r2-log-summary.json`、`vp01-r2-memory-final.json` |

结论：**VP-01的本次真实普通Main首批补归档→同Thread后续增量→回收后不重复场景通过，原失败整改取得正式关闭证据。** Thread实际ID及完整数据只留ignored，两个Thread-show原始证据文件权限0600；公开报告不展开正文。未复测Cron/未知ACK/网络丢ACK/跨端点竞争等其它分支，不把此成功扩大为长期exactly-once或全轮通过。VP-02提案/来源传递行为缺口、VP-03自述偏差及VP-05待澄清体验观察保持。

## 6. 验收结论与推荐复核

**最新判定（第二次定向复验后）：Validation仍NOT PASS，剩余明确行为缺口为VP-02。** VP-01首批22条→同Thread后续24条、receipt/正文/身份与回收后不重复均取得真实证据；VP-04沿用5秒预算下三个正式Turn成功证据，不重跑。VP-02来源传递/提案查源缺口继续保留；VP-03为模型自述偏差，VP-05按root判断留作需澄清的体验观察。此结论不触发静态Verification，也不改写首轮和第一次复验的真实失败。

以下保留首轮交回时的结论，VP-01/VP-04最新状态以上述§5.1、§5.2及本段为准。


**首轮已执行完毕，Validation NOT PASS，建议继续处理VP-01/02/04后定向复验；本轮失败不抹去已取得的业务链证据。** 实际证明了两Profile独立Notebook、明确批准前不写、限定批准后的真实NM写入、来源先于Candidate结算且保留未覆盖事项、跨成功压缩/同Profile跨Conversation原文恢复、cold与warm两个真实窗口的主动NM跟进，以及正式取消/资源回收。个人Thread归档未成功、自动Recall反复超时；来源元数据/提案查源等模型行为还有缺口。VP-03/05是实际行为观察，不采信自述为产品事实，也不据此直接调框架Prompt。

建议用户复核：在5174打开本次主助手或考研助手Conversation，查看原生压缩/Framework/Notebook、两条已完成Schedule与无未来项；在考研Space查看唯一带合成素材前缀的Memory；对照ignored证据中的原始tool轨迹与归档/Recall警告。完整入口与ID见`run-info.json`、`final.json`，不需要在Default做任何写入。

保留范围：新双Profile、服务、Conversation、Notebook及合成NM资料均保留；本次future排期和自有Runtime/poller/lease/watch进程已清理。未测现实24小时/长期生活表现、K3、云端/手机部署、100000 token自动Idle触发；历史V01–V15仅复用适用机制证据，没有把未执行分支改成通过。静态Verification按用户要求推迟，历史NOT PASS保持；整轮完成与部署范围由主会话最终判断。
