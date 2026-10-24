# Verification：20261024-noting-maintenance-v2 全轮独立复审

## 1. 审查对象与结论概览

审查者：全新独立 Agent `/root/noting_v2_reverification`，未参与实现，不派生 Agent。日期：2026-10-24。

冻结依据：Snapshot Index `.autonomous/20261024-noting-maintenance-v2/snapshot-index.md`，`baseline.txt` 指向 `a4faa767e6b7c1d01ec688a083c71576d58638a5`。权威原文均使用该冻结树；07 顶部 2026-10-24 最终 v2 §0–9 优先，白板语义和 02→04 未被替代增量→01、06、08 未覆盖不变量继承。冻结副本位于 `.hermes-dev/noting-v2-reverification/frozen/`，没有修改权威规格。

范围：R01–R15、O01 全部及它们依赖的正式接线、身份／来源、不可变快照、失败与原生边界。本报告为全轮复审，初审保持历史版本。本报告写入授权替代 Skill 默认的 verification.md 路径；六节模板及全部表列保持。

审查代码版本：HEAD `5ee2a94d97f57a001d3ad748dc2b5b2189068a9b` 加 F01/F02 当前修补工作树；产品证据指纹在本报告 §3 及 `evidence-version-audit.json`。F03 发现后 root 将另行安排修复及全新独立最终复审，本报告不冒称最终待部署 SHA。当前结论：**Verification 门禁不通过**：新增 F03 未关闭，正式模型第二轮及 N46 证据不足。完整矩阵 36 行：28 符合、3 违规、5 证据不足、0 不适用；统计以 §3 为准。不以已有测试计数、实现报告或前审结论作为要求来源。

## 2. 独立要求清单与覆盖

判据建立于 2026-10-24，在读取任何产品代码、测试、实现报告、CLAUDE 或旧 verification 之前落盘。本节仅依据冻结规格原文。阅读覆盖：07 全文（历史四工具／maintain Schema 的已替换内容不重新生效）；白板完整正文及脚本内七类型／生命周期／完整场景数据；02 的身份、Foreground、来源、事务、timer、Force、child、载体、失败、接线与历史替换说明；04 的未替代增量及历史边界；01 愿景／边界；06 客户端／API兼容和真实载体契约（新 UI 工作不纳入）；08 Profile／宿主／渠道不变量（个人工具及 UI 新需求不扩大本轮）。未读取归档目录。索引与版本仅用于定位，流程要求不反向构成产品要求。

“直接”指原文直接要求；“推导”指为实现原文明示目标／机制所必需；薄弱处保留重点核查，不因未规定函数名而弱化。后续若修正判据，必须在第 6 节保留原文依据与理由。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| R01a | 07 v2 §0、§3、§6；固定六工具完整顶层 | 机制；eligible Main＋Noting | 直接：History/Show/Create/Update/Archive/Finish 是完整 API 顶层定义，父可另有 Main 工具；声明不授执行权 | 实际序列化 tools 含完整六定义、不 defer；无 messages[*].tools、动态注册或 Task/续Turn重复 Schema；当前面无 maintain alias | §3 R01a |
| R01b | 07 v2 §0、§3、§6；07 §3.1、§8.2；04 §4.4 C13 | 机制；任务全生命周期 | 直接：父实际 root/tools/冻结 Active 前缀在每次 child 请求完整一致；新配置只在合法父构造/恢复边界生效 | 首请求、工具循环、重试、续Turn及父并发活动均不重建/热改冻结前缀；多模态结构保留；真实请求证据区别字节 parity 与缓存命中 | §3 R01b |
| R02a | 07 v2 §0、§3 | 权限；Main/普通子Agent | 直接：Main 拒绝三个维护工具和 Finish；History/Show 沿其权限可读；普通子Agent不因继承 Schema 获写权 | 同步、并发、invoke、wrapper/间接调用按可信 runtime 身份拒绝，拒绝无副作用；参数／正文自称 Noting 不改变权限 | §3 R02a |
| R02b | 07 v2 §0、§3、§6 | 权限；Noting | 直接：Noting 精确六工具、绑定父 Conversation；Scheduler/Cron/文件/外部写/委派均无权 | 全部正式 dispatch 与间接调用都不能绕过六工具白名单；跨域读被拒绝；Task、当前 control、续Turn 权限与 Main 四禁用提示同步 | §3 R02b |
| R03a | 07 v2 §3；07 §4.4/§4.5 未替代部分 | 接口；create/update/archive | 直接：同名参数同层；update 无 action/changes；一次一条；archive 有具体 reason | canonical Schema、实际 handler、错误 next_action 一致；update 仅 entry_id 时拒绝；未知/多余/只读字段不静默丢弃，不出现笼统 mixed-action | §3 R03a |
| R03b | 07 v2 §3；白板 C6/K6；02 §3.3a | 状态；所有维护 | 直接：稳定 entry_id、固定 entry_type；真实变化新 version，无变化不造版本/刷新时间 | fields 按键合并，文字替换、数组全替、对象全替；省略保持，null 清可选单值、[] 清数组，清后仍合法；旧 Snapshot 固定旧版本 | §3 R03b |
| R03c | 07 v2 §3；07 §4.4/§4.5；白板 K6/N4 | 原子性；失败/并发/结束 | 直接：验证整体再发布，失败不改变 working；Finish 最后独立且只请求结束 | finish 混批执行前整批拒绝；成功 end_requested 后锁定工作态，后续写拒绝、重复 Finish 不变；runner 原生 Turn 返回后 Commit Gate 发布 | §3 R03c |
| R04a | 07 v2 §2；白板 C1/C7/C8 | 模型/validator；七类＋Candidate | 直接：七类必填按新表；status/关系/来源仍 entry 顶层，不造未知事实补必填 | matter completion_condition；action owner/completion_condition；situation subjects；gap situation_ref/missing_information/impact；question description；insight certainty；decision scope。Schema 和 handler 必填/可空一致 | §3 R04a |
| R04b | 07 v2 §2、§6.1 | 边界；内容字段/材料 | 直接：删除 external_refs、不增 schedule_refs/history/details 或独立材料字段；精选文件引用只在 description | 当前可写 Schema/validator/投影无 external_refs 残留；路径不计软长度指导、不列全部文件、不仅因文件新建情景；provenance 不被路径替代 | §3 R04b |
| R05a | 07 v2 §1、§2、§6.1/§6.2 | Prompt/内容；初始/续Turn | 直接：完整用途和 description 指导，通常1–3短句/约150中文字符或80英文词，软长度，无未知摘要比较 | 实际构建文本逐字落实已定稿段；稳定对象更新保留必要历史意义/纠正/条件及其来源，另一对象另建；无硬门禁/截断/凑字 | §3 R05a |
| R05b | 07 v2 §6/§6.2；白板 N1/N2/C7/L7 | Prompt/内容；完整任务 | 直接：七步顺序，对齐→更新→补建→结算→过滤/候选→Schedule缺口→检查Finish；第三步七类写作与第五步七类过滤各自独立 | 运行 Prompt 保持两表；每种类型准入、归因、七天/72h和出口齐全；不把 AI 未采纳建议变用户认识/决定，不以无任务删有用情景 | §3 R05b |
| R06a | 07 v2 §5 | 派生时间；所有模型投影 | 直接：只读 evidence_time 位于来源信息区、不在 fields 或 editable 输入 | runtime 从可信 provenance 派生：仅range直接复用；UID有user仅user起止；无user有assistant最近assistant；均无取全部消息范围；UID+range优先UID、原range保留；unknown不填现在；refs Candidate 不造直接证据时间 | §3 R06a |
| R06b | 07 v2 §5；白板 L2/T4；07 §4.1 | 生命周期时间；普通/gap | 直接：组来源时间不无条件代替首次实质证据；7天/72小时仅处理点 | matter/action 用 last_progress_time、question 用 last_discussion_time、gap 首次识别/created_at；情景/认识/决定首次实质证据不因新增来源、复制/改写/压缩刷新；各视图/回执保持同语义 | §3 R06b |
| R07a | 07 v2 §3/§6.3 | 引用/归档；relations | 直接：创建/更新保基本引用检查；普通入向 relations 随归档同次解除 | 未知/归档目标、自指、重复kind+ID拒绝；archive 原子更新目标及受影响条目版本并回执说明；不级联归档、不改业务状态、不删正文/来源、不新图门禁 | §3 R07a |
| R07b | 07 v2 §3/§6.3；白板 C8/C6 | 引用/归档；gap/Candidate | 直接：gap situation_ref 和 Candidate notebook_refs 仍保护 | 未处理保护引用时整个 archive 拒绝，不能先清普通关系再失败；修复引用后才成功；不发布悬空引用 | §3 R07b |
| R08a | 07 v2 §4 | 数据；所有entry含Candidate | 直接：entry 顶层零或一 schedule_suggestion 单对象，仅 content/schedule 两字符串 | 不混 fields、不数组化、不拆额外条目装多项；update 整体替换/null清除；普通自然语言字符串成功，创建/更新/提交均不做日期/CRON/时区或可执行性语法校验 | §3 R08a |
| R08b | 07 v2 §4/§6.1 | Prompt/语义；每次Noting | 直接：必查父未来请求、已接受责任、Main承诺与登记证据；有缺口补，无缺口不造 | 实际 Prompt 完整定稿：content 自包含背景/对象/行动/条件、不受description软长度，不依赖见上文；schedule保实际一次/周期意图、不造时间；advice不等于注册；Noting无Scheduler权 | §3 R08b |
| R09 | 07 v2 §4/§7；07 §8.13 | Framework/Main；实际注入含建议时 | 直接：仅当前注入有效 Notebook 含建议，Framework最底部附三句定稿 Main 文案 | 无建议不附；提示位于其它可选尾部之后；不强制照抄/立即登记/再检查，不新队列/Turn/微信发送；建议不能变新授权 | §3 R09 |
| R10a | 07 v2 §7 | Compaction；Noting on/eligible Main | 直接：按真实原因分支；原生阈值自动保默认tail，其余取消默认tail；显式/compress here N原生指定tail | 自动阈值、Force后真阈值、普通手动、Idle、overflow/recovery等分别接线；不以force=False或auto宽标签替真实原因；off/非Main全部原生 | §3 R10a |
| R10b | 07 v2 §7/§9 | 压缩区间；no-tail路径 | 直接：取消tail从摘要输入选择开始，所有被覆盖旧tail进入摘要；recency/min_messages/旧user-assistant回插一并处理 | 模型请求/live/durable一致；未总结旧tail不直接删除；新区间用户/Framework/合法steer/未闭合工具链保真；失败/取消/no-op/提交失败保原上下文与History/Timeline原文 | §3 R10b |
| R11a | 07 v2 §7；07 §8.1；白板 P2/D6 | Idle机制；新增/已有Noting | 直接：相应Noting正常Finish且提交→父durable full compaction→Framework | 新任务、已有运行中、已有正常提交都按真实状态处理；failed/forced/overflow/External不可整理均不得Idle full；无新child不绕过也不永久跳过；压缩失败不回滚合法Snapshot | §3 R11a |
| R11b | 07 v2 §7；07 §3.1/§3.2/§8.1 | 结束/失败；各trigger | 直接：forced/overflow仍尝试合法全量Snapshot且通知非正常；一般API失败可无新快照；非Idle不新增等待/成功门槛 | 五Turn/原生调用或迭代预算/处理过overflow正确区分；有效Snapshot与正常完成不等同；真实失败不冒成功/新Snapshot；普通手动/阈值并行不阻塞原生必须压缩 | §3 R11b |
| R12 | 07 v2 §1/§6/§8；白板 E1/E2/C6/F1/F2 | 内容/结算；外部Memory/Rule/Skill | 直接：获批后实际成功覆盖范围退出，不因仍有用保余额；部分成功保真正剩余范围 | 先来源后Candidate，按真实批准/版本/工具结果结算；未覆盖新变化/未完责任/其它未完成提案所需范围保留；失败/未知不结算、不查目标保管、不回流已结算内容、不新增归档召回 | §3 R12 |
| R13 | 07 v2 §6.4 | Prompt；第4步最小修改 | 直接：只将指定短语换为“scope left unsettled by the confirmed writes…” | 除工具拆名必要调整外原段四项保护、失败/未知、来源先Candidate后保持；不多处新增强硬清退，不以一般有用性覆盖成功结算，也不无条件删除整条 | §3 R13 |
| R14 | 07 v2 §0/§9；冻结索引R14 | 工程交付；本轮 | 直接：范围内自主实施/独立双门禁及真实证据；确认后提交部署 | 审查对象、检查、实际版本和日志可对应；保护其它任务/凭据/生产；未完成/未测如实记；本复审不授权提交/push/部署，也不因流程报告替产品证据 | §3 R14 |
| R15a | 07 v2 §9、冻结索引R15、07顶部 v2后追加授权段 | 真实模型/版本证据；Alex隔离Kimi | 直接：实际kimi-for-coding，隔离Alex Persona/系统背景，真实长前缀超过历史N38代表点(N46)，记录实际Usage | Main→Noting→压缩→Framework→后续Main真实代表链路；父子逐请求root/tools/Active核对；任务切换后固定工具真实调用；不能缩短前缀冒充长样本；误调及Harness拒绝如实统计 | §3 R15a |
| R15b | 07 v2 §9；白板 C7/L7/E1；冻结索引R15 | 真实内容质量；多次整理压缩 | 直接：工作进展、偏好/身份/情绪/关系、开放讨论/未采纳方案、纠正及有用历史；外部成功/部分成功/剩余保留/不回流 | 真模型结果能由Notebook解释发生过什么和当前怎样，细节再History；HTTP成功/Finish或单次正常样本不足；授权实际分支与机制测试证据不能互相冒充 | §3 R15b |
| O01 | 冻结索引O01；07 v2 §0/§8；06顶部替换边界 | 范围边界；全差异 | 直接：不做Web恢复/Android/标题/Provider协议切换/上游Issue/个人Provider改造，不改生产迁移策略 | diff无越界产品行为、无第二Loop/数据库/调度器/API hierarchy；生产数据和个人凭据不入Git；UI/个人并行任务仅保存，不混为本轮已验 | §3 O01 |
| I01 | 02 §1/§2.6–2.7/§3.1–3.4；04 §1.3/§2；07 §3.1 | 继承；身份/事务 | 直接：Conversation跨压缩不换身份；new/reset/fork新身份；合法Anchor/来源/权限/版本同事务；晚旧Anchor不回退pointer | 本轮新增字段/归档/压缩不破坏 owner、不可变快照、fork继承绑定、rewind有效路径、原子pointer；同任务working不被父新Snapshot覆盖 | §3 I01 |
| I02 | 07 §4.1/§4.5/§8.12–8.13；白板 N3；02 §5.6 | 继承；模型投影/通知 | 直接：完整Notebook＋可读coverage，隐藏Snapshot/Anchor审计；pointer改变才通知且追加时原子复核 | Show/初始/续Turn/维护回执/Framework共合法投影；有效结果整本注入不截断；旧排队结果丢弃；busy/fence安全tail-only，live/durable同写，非触发不外发 | §3 I02 |
| I03 | 07 §3.1/§8.1；04 §4.5；02 §4.5–4.8/§5.4 | 继承；联合准入/生命周期 | 直接：D01所有入口先实际来源；Force区间admission一次且失败/rewind不解；Idle单deadline；持久child资源释放 | Native沿原生；External freeze/admission前拒绝且保通知抑制；unknown不新拒；区间内换Anchor不重复；成功压缩才新区间；无自动崩溃恢复、新调度器或复制父transcript | §3 I03 |
| I04 | 07 §4.1/§5；白板 C3/C6/C8/C9 | 继承；来源/Candidate | 直接：普通条目有合法UID或range；Candidate refs+mapped types或exact UID二选一且range=null；refs稳定 | 拒绝混源、重复、外域、无效来源/引用、Candidate引用Candidate；gap映射situation，反向引用派生；fork旧来源不为新断言兜底，来源不因新Schema放宽 | §3 I04 |
| I05 | 07 §5/§8.4/§8.10；04 §2/§3；06 §1.12/§2.7 | 继承；History/Proposal/人类读 | 直接：History独立于两开关，Main同Profile显式跨域，Noting父域；原文不换摘要；Proposal非批准，human-only /notebook不污染模型 | 六工具改动保既有合法History查询/同源分页/错误边界；当前Proposal来源/批准/标签链完整；新tool schema不使非Main获能力；浏览器临时读不持久/不触发 | §3 I05 |
| I06 | 07 §6.2–6.4/§8.14；02 §3.10–3.12/§5.6；08 §1–2 | 继承；Scheduler/Reminder/Profile | 直接：Scheduler独立Main；无Notebook状态联动；claim/witness/ACK及busy→deferred和冷宿主保留 | Schedule建议不创建/改排期，不得影响due/owner；所用Profile绑定正确；Framework无借旧微信adapter发送；本轮相关改动未破坏延迟一次/重试/ACK/重启既有机制 | §3 I06 |
| I07 | 07 §8.13；白板 L1/L6/L9 | 继承；容量/建议尾部 | 直接：Unicode正文>12000或条目>60仅追加共用Proposal；不阻提交/删源/另开整理 | 同一有效Snapshot计量、通知包装不计；Main考虑建议句仍在Framework最底；来源/Candidate完整保留；失败无新Snapshot不伪造成功或容量结果 | §3 I07 |
| I08 | 07 v2 §7；04 §3.4–3.5；02 §4.3；06 §0.4–0.5；08 §1 | 继承；原生/配置兼容 | 直接：全球关闭/非Main原生；local仅参与；API增量兼容/目标Profile；原生Prompt和Provider所有权 | 开关组合冷/热恢复Prompt/tools/dispatch一致；local不改cache prefix；压缩tail策略仅适用范围生效；无凭据/个人配置、生产迁移、Provider适配或全局环境变量副作用 | §3 I08 |

## 3. 逐条实现证据

证据简称：**A243** 为 `.hermes-dev/notebook-data-v2/final-suite.log` 中243项有效机制分区；只复用当前产品指纹匹配项。**A26** 为 `instant-receipt-final.log` 的26项，另 `instant-independent-repro-after.log` 为正式 Admission 原反例1项通过。**B121** 为 `.hermes-dev/noting-maintenance-v2/b-mechanism-version-tests.log`对应5文件121项，before/after两份17源码指纹已独立核同当前树；**B58/B59/B96** 分别指 tools-prompt-v2 报告定位的58权限、59请求/Prompt/Framework、96生命周期有效分区，范围重叠不加总。**C44/C18/C302** 分别为 `.hermes-dev/compaction-policy-v2/targeted-final.log`、`force-final.log`、`native-regression.log` 对应范围。**F02-111** 为 nullable-probe/tests-final.log 的两个变化测试文件111项，115项未改transport/cap回归复用初次日志。日志原红色尝试保留，不称整批均绿。

所有复用证据先核产品版本/底座/断言；逐文件 hash 复算记录 `.hermes-dev/noting-v2-reverification/evidence-version-audit.json`。A最终11项有2项被F01新2项替代，C有1项只少EOF空行已独立复算等价；B17前后匹配，F02六项匹配。各“符合”为当前已读候选源码的条款判定，最终SHA仍需映射，门禁不因此提前通过。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| R01a | Main apply_main_read_surface→_read_schema/filter_tool_definitions→tool_search direct→原生build/SDK | canonical六定义、实际SDK工具目录检查；F02官方Coding nullable修补再经出站清理/SDK保持；旧maintain仅retired拒绝 | B121、F02-111、probe actual wire | 符合：完整固定六工具；Task无Schema；F02机制修补已证 | 正式新E2E仍待R15 |
| R01b | freeze_parent_active_prefix/freeze_parent_runtime→apply_cache_parity_from_parent→build_noting_child→_run_child_turns/_continuation_history | 读真实父前缀冻结、FrozenParentPrefix身份、多模态结构clone、child own suffix；实际first/tool/续Turn与父活动路径受控SDK对账 | B121/B59；tests/secretary/test_fixed_noting_request.py、test_r3_child.py；旧short frozen-parent-wire | 符合：冻结后root/tools/Active不热改；真实缓存数据另记 | 长前缀新真实证据待补，不把字节相等冒称缓存收益 |
| R02a | turn_tool_validation secretary_validation_refusal→tool_executor权限guard→inline；_invoke_tool→resolve_invoke_tool_executor；model_tools/registry scoped_dispatch_refusal | Main四写/finish强制负例、混批保合法History、raw/scoped registry和参数自称身份；child绑定store再次检查 | B121中permissions58；test_fixed_noting_permissions | 符合：可信runtime判定，非Noting拒绝且不写Snapshot | 受控SDK和真实SQLite机制；自然模型未误调不作权限证明 |
| R02b | noting_child NOTING_ALLOWED_TOOL_NAMES/_bind_child_identity/noting_dispatch_block；全部dispatch共用拒绝；History绑定_parent_ref | Noting六工具外terminal/scheduler/bridge/delegate等强拒，间接工具不能转授；普通delegate去除权限 | B121/B58；noting_child.py:46、75；tools/secretary_dispatch.py:38、154 | 符合：完整广告数组与执行白名单分离，继承Schema不授权 | 未改变History本身现有范围 |
| R03a | noting_contract三Schema→inline handlers→noting_tools._mutation_args→Store.create/update/archive | 同字段同层、update无wrapper、未知字段拒绝，旧名明确retired；独立null反证发现Create单type字段被None默认接纳 | A243/B58；独立runtime-schema.log | 违规（F03）：status:null与relations:null违反Schema而被成功创建 | 其余flatten路径成立；等待F03修复证据 |
| R03b | NotebookWorkingState.create/update/_persist→Store._insert_version_conn→insert_item_conn→Snapshot固定version列表 | 真实SQLite稳定lineage/id、变化新version、no-op不刷新；fields键合并、数组整换、nullable对象清除 | A243及test_notebook_maintenance_v2.py:72–147；notebook_model.py:202–292、notebook_items.py | 符合：未用全局最新版本改旧Snapshot，运行元数据不能编辑 | 非法top null另列F03，不作合法调用的缺陷 |
| R03c | noting_tools.guard_noting_tool_batch/finish_noting→Store.freeze；runner._run_child_turns→_commit_when_complete→commit_noting_snapshot | Finish完整批次前拒、end_requested锁同owner，重复finish首结果；原生Turn结束再同事务提交；故障与并发固定态 | B58/B96；noting_tools.py:154–195；noting_child.py:808–920 | 违规（F03关联）：本项一般非法调用零副作用不全满足；Finish/事务机制符合 | 不把end_requested冒充提交；F03修复后需复核 |
| R04a | noting_contract七类fields Schema→notebook_contract REQUIRED_FIELDS/OPTIONAL_FIELDS/validate_fields→WorkingState._validate_state | 八类型最小合法实例及新增可选项/非法字段/空required验证；Schema与数据模型必填表对齐；但Create显式null不一致 | A243/A新v2最小类型；独立runtime-schema.log | 违规（F03关联）：七类必填正确，Create顶层字段nullable契约不一致 | 不是要求模型填虚构未知；F03修后关闭 |
| R04b | notebook_contract COMMON_FIELDS/validate_fields；notebook_items.canonical_notebook_payload/item_entry；notebook_render.readable_notebook_entry；Task description段 | external_refs/evidence_time可写fields撤出；旧不可变行只读兼容投影不写回；文件仅精选description、无新材料槽 | A243；notebook_contract.py:34、155；noting_prompts.py DESCRIPTION GUIDANCE | 符合：新输入严格拒绝退役字段，历史版本未迁移，文件路径指导仅一处 | 软长度为模型指导，不作解析/截断 |
| R05a | noting_prompts DEFAULT_NOTING_TASK_INSTRUCTION/CONTROL/CONTINUATION→runner initial/working control | 与冻结§6.1定稿逐段核；完整description为同段集中指导，更新稳定对象/必要历史/来源；Main用途同步 | noting_prompts.py:3–25；system_prompt.py NOTEBOOK_GUIDANCE；B59 | 符合：完整指导及软长度，未要求比较未知摘要，无maxLength门禁 | 真实内容质量另见R15b |
| R05b | Task COMPLETE THIS TASK IN ORDER→runner task suffix/每次续Turn的完整工作簿 | 七步、第三步七写作指导、第五步七生命周期分支独立；用户认可/AI备选/未知/gap/候选来源审批原约束逐段核对 | noting_prompts.py:27–85；B59；冻结07§6.2/白板C7、L7 | 符合：未以写作表取代过滤表，7天/72小时和出口未弱化 | 运行模型是否按全部内容场景工作仍须R15b |
| R06a | readable_notebook_entry/state→notebook_evidence.evidence_time/_referenced_time；正式Show/维护回执/control/Framework传db/ref/state | 四级取时、UID优先range、unknown不造；F01正式Instant receipt精确物理row owner+UID+body排除真人优先，branch与真人wrapper/steer对照；不改来源授权 | A243中旧时间分区＋A26最终＋初审真实Admission反例1；instant-receipt-sha256两文件匹配 | 符合：F01机制已关闭；候选refs沿来源链，返回时间模型可见且输入只读 | 新模型链是否触达全部时间分支不替代机制反证 |
| R06b | NotebookWorkingState时间owner与fields last_progress_time/last_discussion_time；Task第2/5步；evidence_time仅派生显示 | create保created_at，update/noop不重置first；processing_note只last_processed；模型指导不让重读/改写更新实质龄；gap用created识别时间 | A243/26；notebook_model.py:202–290；noting_prompts.py第2/5步 | 符合：来源组时间不替代所有类型计龄字段，期限非自动删除 | 来源支持断言真实性仍是模型语义职责 |
| R07a | WorkingState.archive→draft relations cleanup→validate full state→Store._insert_versions单write事务→insert_item_conn | 普通入向关系同事务移除并新version，result updated_entries/relations_removed_from；失败注入回滚working/全部item，历史offpath继承仅精确清关系claim | A243/v2 archive原子与失败用例；notebook_model.py:293–346；notebook_store.py:175–181 | 符合：不级联状态/归档、不增图检测、正文来源不变 | 自写in-memory fallback不代表正式SQLite；正式Store batch已检查 |
| R07b | archive outgoing_references→protected gap/Candidate referrers在写前整体拒绝→validate_references | 混有普通关系和protected refs时先检查无持久副作用；模型先修gap/Candidate再archive；recovery读取updated_entries精确版本不重放 | A243；test_notebook_maintenance_v2.py:284–326；noting_recovery_sources._working_state | 符合：没有半归档半清关系或悬空来源 | 不把普通relations自动清理扩展到Candidate来源 |
| R08a | 三Schema schedule_suggestion anyOf(object,null)→validate_schedule_suggestion→WorkingState create/update→immutable payload | 所有类型包括Candidate一对象；content/schedule非空字符串，无parser；整对象替换/nullclear/noop；非法形状零item | A243；F02官方SDK111；notebook_contract.py:192；noting_contract.py三Schema | 符合：建议层无CRON/时区可执行性校验，F02修补如实表达null | 正式真实第二轮清除待R15，不用探针代签 |
| R08b | Task第6步 Identify missing Schedule registrations→entry建议→Snapshot | 定稿语义完整、必查未来要求/责任/承诺和登记证据；content自包含背景/对象/动作/条件且不套description长度；无Scheduler调用权 | noting_prompts.py:第6步；B58/B59；旧short首轮建议 | 证据不足：指定机制/Prompt符合，正式真实第二轮建议清除链路仍待R15 | 无新队列/额外条目策略；未将时间语法当注册 |
| R09 | Framework append事务prepare_completion→completion_body→完整Notebook/Proposal尾部→SCHEDULE_SUGGESTION_INSTRUCTION | 实际有效snapshot含建议才追加，最后三句逐字一致；有Proposal也在最后，无建议/clear省略；无Turn/外发 | test_schedule_suggestion_framework_v2四项；noting_notifications.py:18–47；framework_messages.py:167 | 符合：从实际注入payload条件判断，无强制立即登记或照抄 | 后续Main真实登记/清除另见R15 |
| R10a | 原生turn-start/pre-api/post-tool→native_threshold_trigger；manual compress_now；_run_summary_phase→select_no_default_tail→ContextVar scope | 三个实际阈值seam和provider_overflow/engine_maintenance分支受控内置engine验证；force/auto宽标签不决定；explicit here tail、off/非Main/child原生 | C44最终、C原生302有效复用；tail_policy.py:12–30；turn_preflight.py:156、325 | 符合：attempt局部、不改共享配置，原生阈值保尾，其余取消默认tail | 用户配置自定义第三方engine非本轮改造，不宣称其实测 |
| R10b | ContextCompressor._compress_window/prune/_augment_summary_lean→prepare_candidate_anchors→_commit_compaction→publish_native_commit完整DB读取 | 旧tail实际在summary input，停old user/reply回插；pending多输入/图片/steer/unread toolowner保留；并发水位外user in-place/rotation与live/durable/下一Main一致；failure/cancel/noop/commit/lease/growth原文保留 | C44/C18及ownership/source有效分区；test_noting_tail_policy_v2.py；publication.py:73 | 符合：取消recency/head/min floor不吞未处理输入；无进展不清尾，History原文仍在 | 合并handoff包含待答请求保守no-op，不承诺一定压缩成功 |
| R11a | noting_runtime prepare_joint_noting(trigger=idle)→reuse_noting_for_idle/normal_noting_snapshot_conn→_publish_after_idle_completion→idle_compaction_after_commit→native durable request→Framework | 新正常child及in-place/rotation真实内置摘要；已有运行等待/正常commit复用；failed/forced/overflow/External拒Idle；owner关联与压缩完成而非admission才发布 | C新Idle2/C旧Idle19+reuse24有效；noting_child.py:159–222；noting_compact.py:23–63 | 符合：相应正常提交是Idle专有前提，durable后Framework，压缩失败不回滚Snapshot | 真实新long/续短待R15，不当已执行 |
| R11b | _run_child_turns→_force_task_close→Commit Gate；_NotingFailureNotice→publish_noting_failure；非Idle prepare_joint_noting平行spawn | 原生迭代预算/五Turn/overflow合法state commit；forced/context_overflow completion明确非正常；一般API错误无新Snapshot；child finally关闭DB/registry/admission | B96/C19/C24；noting_child.py:791–927；noting_notifications.py:22–29、50 | 符合：合法快照和正常完成分离，非Idle不新增成功等待门槛 | harness人工SIGTERM不是产品forced或资源正常释放证据 |
| R12 | Task第3防回流、第4结算、第5过滤→实际真实Noting三维护工具→Store | 检查提案→批准→真实结果/版本/覆盖，来源先于Candidate；完全退出、部分只留未结算范围；不查目标保管、不以有用豁免、不重建已结算 | noting_prompts第3–5步；旧short snapshot/events/semantic audit（5ee同Prompt/Store hash） | 证据不足：指定Prompt/机制符合、已有short完整/部分结算有效；后续多轮防回流尚未完成 | 预置合成成功写轨迹为模型输入，不冒充实际外部写入 |
| R13 | Task第4步 settle actual writes | 与冻结父Prompt diff逐字核：工具拆名外仅替换批准短语，既有四保护/失败未知/顺序仍在；其它写作仅提醒结算规则适用 | noting_prompts.py第4步；冻结07v2§6.4；git diff baseline | 符合：只保scope left unsettled及理解剩余范围上下文，未多处强硬清退 | 不改仓库通用规则为模型正文 |
| R14 | 独立工作树/冻结/亲审/阶段源码hash/限定测试→本复审→后续Validation/Delivery | 冻结索引/基线存在、无权威规格改；主会话A/B/C亲审与独立初审/本复审；最终SHA/门禁/部署未完成 | 本轮plan/旧verification、质量log、evidence-version-audit.json | 证据不足：完整交付尚未收敛，不能以阶段commit/测试数替门禁 | 提交/部署不由本审查者执行；当前未授权我碰生产 |
| R15a | 隔离Alex _make_agent→真实Kimi Main→Idle Noting→原生压缩→Framework→后续Main；N46 | 旧short首周期真实链路/前缀/usage有效，F02第二周期失败；官方nullable探针200仅能力；本轮新short/N46尚未交接 | e2e/run-short-20261024-150156/；nullable-probe/corrected；e2e-report.md | 证据不足：N46未执行、最终新版本代表链路未完成 | dry/HTTP200/Finish不代替长上下文真实结构化调用 |
| R15b | Task语义输入→真实Notebook→多次压缩后的Main Notebook/History与Schedule | 首short有工作纠正、身份/偏好/情绪/关系、未采纳备选及外写完整/部分结算；缺第二周期清除/多次Main接续和新长样本 | 旧short snapshot/framework/registered-schedules及semantic audit；后续待交接 | 证据不足：已成功部分保留，不能替未完成真实内容链 | 未实际外写目标或投递Reminder，不拿合成轨迹冒充真实写入 |
| O01 | baseline→当前产品diff；所有源owner/依赖/规则入口 | 只有Notebook工具/Prompt、只读时间、tail policy和F02必要原生schema修补；未改Web恢复/Android/标题/个人Provider/迁移/调度器/新Loop | git diff --stat/production diff；冻结质量10checks；uv.lock原样 | 符合：Provider协议与模型路由未切换，nullable仅既有transport兼容修补；本审查未触生产/云/凭据 | 不对生产既有独立Reminder缺口下本轮修复要求 |
| I01 | Conversation/Foreground既有owner→NotebookStore._source_checks/_inherited_sources→validate_snapshot_state_conn→notebook_commit_snapshot_result_conn→pointer reselect/fork | 完整state/immutable item精确版本、source license、anchor有效/local/global/版本同事务；按coverage排序非完成时间；fork共享只读版本，late旧结果不回退 | A243/B96；notebook_store.py:17–73、101–181；hermes_state_secretary_notebook.py:151–300 | 符合：拆工具/归档和新字段沿现有事务，独立working不跟父pointer热换 | 同Conversation并发任务不保证互为内容超集，按冻结07§11.1不要求合并 |
| I02 | readable/model_notebook_view→初始/control/维护/Show；runner commit_result→publish_noting_completion→append_runtime_row.prepare/record_carrier同write事务 | 模型隐藏snapshot/base/anchor审计、局部UID、真实coverage；pointerChanged才queue、追加同事务再核；busy/fence tail-only、失败回滚live、不外发 | B121/B59及r3_framework19；notebook_render.py:14–126；framework_messages.py:130–216、330–357 | 符合：完整Notebook非delta/ID；原API默认审计字段保留，旧通知被新pointer取代整条丢弃 | Framework内存队列不承诺重启必达；不新增持久通知队列 |
| I03 | D01 actual dispatch记录→noting_runtime四入口gate→_freeze_and_admit同事务区间占用→spawn持久child→finally释放 | 真实来源external在freeze/admit前拒，unknown不新增拒；Force区间占用换anchor/失败/rewind不解；Idle单deadline/catch-up、已有任务成功证明；资源owner Profile | C18/C24/B96及r3_wiring52有效；noting_runtime.py:208–310、380–451、583–712；noting_child finally | 符合：沿既有owner、不新Loop/调度/任务自动恢复；非Idle原生必须压缩不受阻 | 仅复用同版本适用机制分区，未把所有历史302套重复运行 |
| I04 | canonical_source_fields/validate_candidate_provenance/validate_references→Store当前路径与source_basis→Snapshot校验 | refs/source_types或确切UID二选一、range null；普通合法range；gap映射situation、candidate_refs派生、无Candidate套Candidate；offpath只同claim源继承 | A243/B96 provenance/source visibility；notebook_contract.py:129–144、205–303；items.source_basis_conn | 符合：新Schema未放宽来源权限；archive cleanup仅移除辅助关系可继承原源 | 时间显示Unknown不能反过来拒绝原本合法来源 |
| I05 | Main surface History独立gate→session_history_tool可信绑定/模式与分页；Proposal slash常量→Main；human-only Notebook既有路径 | 本轮History Schema不改，维护投影局部UID保全局identity；Proposal无source预拼、明确批准；human-only标记过滤既有；Noting权限不跨父域 | B121/B96/旧source visibility；cli_secretary_commands.py diff、notebook_tool.py；06边界 | 符合：History能力、原文与合法路径未随Noting/Scheduler撤销，普通子Agent无新注入 | 新UI恢复等不在本轮增量验收，不把旧UI测试全量复跑 |
| I06 | 独立Scheduler/claim/Reminder materialize/witness/ACK既有链路；Noting schema/dispatch拒scheduler；Frame runtime-only发布 | diff未改due/ACK/route，建议只payload/正文无Schedule副作用；owning DB传入、框架不经旧adapter发送；保现有busy→deferred契约 | B58/r3_wiring52、framework boundaries有效分区；noting_notifications/framework_messages；08 owner | 符合（本轮变更隔离）：无Notebook状态驱动Schedule或新跨Profile路由 | 生产既有desktop来源微信busy缺口为本轮排除的独立已知问题，不冒称已修/重验 |
| I07 | completion_body(snapshot)→render_notebook同body len/各section count→strict >阈值→同条Proposal→可选建议末尾 | Unicode码点len(body)及当前entries，>12000或>60仅提示；无截断/删除/额外Noting；无建议时无advice | test_r3_framework容量边界＋test_schedule_suggestion_framework_v2；notifications.py:18–47 | 符合：Proposal审批和pending来源保持，失败无新快照不伪造成功计数 | 不将阈值当持久写入授权或自动触发新Main |
| I08 | apply_main_read_surface/synchronize_main_read_prompt原生边界；tail policy global eligible/child排除；API可选参数默认 | Noting/Scheduler开关独立，local不改root/tools；全球off/非Main原生tail；三新内部可选参数默认旧行为；Profile传db，不改env/依赖/原生schemaowner | B59/config41、C44/302有效；quality log；source diff | 符合：允许合法构造切换一次工具前缀，但冻结child不热变，原生路由/Prompt tiers保留 | F02官方nullable改变仅恢复canonical契约，不声明其它Moonshot支持null |

## 4. 核心目标及验证方法审查

**指定工具机制已经形成正式链路。** Main 构造/恢复在原生边界同步完整六工具 → Tool Search 的 direct 例外 → 实际原生请求/SDK 序列化；parent prefix 从真实 Active 冻结，child 原生持久 Session 只追加自己的任务/控制/工具后缀，循环与 continuation 不刷新 root/tools/Active。Main 的四工具拒绝、Noting 精确六工具授权同时覆盖真实 loop、同步/并发、invoke、scoped/raw registry/bridge。测试不是仅调用孤立 helper：受控 SDK 返回 tool_calls，真实 AIAgent 解析/执行并落 SQLite。自然模型未误调并非权限证据，强制负例才证明拒绝。

**Notebook 成功操作和发布是两阶段。** 三个 flat 工具到真实 Store/WorkingState/不可变 item 版本，逐次成功结果不代表已发布；Finish 混批执行前整批拒绝，end_requested 在相同任务锁固定状态，runner 等原生 Turn 返回才执行 Commit Gate。完整来源/版本/Anchor/参与状态在同一事务重验，Snapshot 固定版本、coverage 排序选 pointer；新 pointer 才准备完成通知，真正追加时在同一写事务再核 pointer 并发布 live/durable。ordinary relations 自动清理沿一次写事务插入全部相关版本，protected gap/Candidate 阻止时没有半清理；恢复使用精确成功收据不重放写入。新增 F03 说明仅有 Schema 正向断言、合法 helper 测试仍可能漏掉正式参数校验缺口：错误的实现可以把非法 null 猜成默认值并通过原58项权限测试。独立反证已证明这一点，不能因原大部分机制通过而忽略。

**只读时间 F01 的当前机制证据成立。** 原生 Instant 没有 display_kind，不能仅按 role=user 或通用分类 helper 认真人。当前仅在时间投影内以精确物理 source row 的原 owner、UID、body 与既有 pending receipt 证明 Instant；不依据 wrapper 文本，也不查当前 Schedule 是否仍启用。真实 Admission/SQLite 证据覆盖 Assistant 回退、真人优先、单 Instant fallback、暂停/删除后、合法 branch、外域相同 UID/body、真人逐字 wrapper 与 typed steer、unknown 时间、只读无副作用。最终两个文件指纹匹配 26 项和原独立反例1项，满足原判据。时间模型输入仍不可写，来源许可链没有放宽。

**压缩从选区开始改变，非事后删尾。** 真实阈值入口标识与 provider overflow/maintenance 分开，Force 不替后续真实原因决策；attempt-local ContextVar 在摘要执行后 finally 恢复，未改共享 compressor 配置。取消默认 tail 时把旧 tail 纳入真实内置摘要输入，禁旧 user/reply 回插及原文 user 段，保留全部尚未回答输入/图片/合法 steer/unread tool owner。成功通过既有 lease/fence/DB commit 后读取实际 durable 状态并 overlay runtime，保水位外新消息；失败/取消/无进展/租约/增长拒绝均保原文。Idle 精确正常提交后才请求 durable full compaction，再发 Framework；已有运行/已提交任务复用、forced/overflow/API失败及 External 的非成功路径覆盖，非 Idle 保并行且不拦必须压缩。已审 C44/18 与原生302的有效分区，source audit 只存在EOF空行等价差异；未复跑302。第三方自定义 engine/外部远端压缩没有被本轮增量改造，不冒称它们有新实测。

**F02 的传输修补满足原契约，但不能用探针替真实闭环。** canonical object/null 与 optional text 的契约和 Prompt 没有改，官方 Coding 路由通过既有原生 transport 按可信 https/host/path 校验保留 nullable，旧 Moonshot/聚合/伪造 URL 保持原修补。两构造路径、stream/nonstream、SDK wire、真实 fallback binder、新旧修补和输入不突变均有111最终及115未改分区；6个源码指纹匹配。真实首探针400是指定 tool_choice 与 thinking 冲突，纠正只移除该参数后200且返回准确 null；没有执行返回工具。这可关闭传输机制缺陷，尚不能证明第二轮真实 Noting 成功清建议、正常提交、再次压缩和后续 Main 接续。

**模型内容证据与机制证据分开。** 旧5ee短链第一周期真实覆盖工作纠正、偏好/身份/情绪/关系、未采纳讨论材料、完整和部分外写结算、Schedule建议→Framework→Main实际登记；已直接读 snapshot、termination、live/durable 与正式Schedule行，首 Idle 确为 Snapshot→durable压缩→Framework。外写成功是明确标注的合成 Conversation 轨迹，实际外部副作用0，不冒称真写 Rules。第二周期原8次清建议失败保留；N46真请求0。最终多轮不回流、完整建议清除及超过N38实际请求仍缺，R08b/R12/R15a/R15b不能据静态Prompt或HTTP200判通过。真实用户 Validation 尚未启动。

**证据有效性与执行范围。** 先独立建立本报告 §2 再读任何实现/测试/旧结论；现有测试预期回溯冻结原文，检查底座是否绕过待验机制。hash复算独立写入 evidence-version-audit.json：A旧11项中的2项由F01最终2项替代；C8/9精确，1项仅末尾换行等价；B前后17项全部匹配；F02六项全部匹配。只重跑了有明确新疑点的两项 F03 反证，项目 runner 报2 failed（预期拒绝但实际成功），不写产品源码、不提交、不触生产/云/凭据/收费模型、不操作可见UI。既有初审/大型测试结果只按适用版本与路径复用，不加总重叠计数、不把红色尝试抹掉。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| F01（初审） | R06a；notebook_evidence.py:24–98 | 原生无display_kind Instant被误认为真人优先；当前改为既有durable receipt精确物理row owner/UID/body证明 | 原算法偏离；当前机制及反例证据已满足原判据 | 已核26项＋原独立真实Admission反例1项、最终2源码SHA；保真人wrapper/typedsteer/branch/fallback及来源许可 | **本次机制复核关闭**；不改历史初审失败 |
| F02（初审） | R01a/R03/R08a；moonshot_schema.py / transports/chat_completions.py | 原真实Coding wire删除nullable；当前官方Coding精确路由恢复canonical null，旧路由默认不变 | 原第二Noting反复失败；传输修补机制成立，正式模型闭环仍有E00 | 六文件SHA、111最终＋115未改分区、真实200/null能力探针已核；正式第二轮清建议及长链由E00补 | **传输机制已证，真实闭环待补**；不以探针代整体关闭 |
| F03（本次新增） | R03a/R03c/R04a；noting_tools.py:68–104→notebook_model.py create | 真实可信child._invoke_tool收到status:null或relations:null，canonical拒绝，handler却各success:true/changed:true并分配entry/version | **P2阻断**；拆工具后放宽非法参数校验、静默把null猜为默认/[]，破坏Schema/handler一致与零副作用 | root已提正式wire按canonical单一type拒显式null，保Store内部默认及合法nullable。须有最终SHA正式invoke和loop负例，具体field/invalid_argument，working及item数量不变；省略/[]/合法null正例 | **违规，待修复/全新独立复审**；原独立反证2 failed保留 |
| E00（初审续留） | R08b/R12/R15a/R15b | 首short第一周期有效；第二周期清除8次失败后停止；新short及真实N46尚未交接 | 必要真实接口/内容结果不足，阻断本轮整体通过 | 最终产品版本真实第二周期→清建议→正常提交/压缩/Framework→后续Main与History，N46真实长前缀及Usage/逐请求parity，完整/部分结算后多轮不回流；保失败/误调 | **证据不足**；由root安排最终新独立审查者核验 |
| V-VERSION | R14/全范围 | 当前审查为5ee＋F01/F02修补工作树；F03需另修，最终阶段SHA未固定 | 不能把当前候选审查冒称最终已验部署版本 | root锁定最终SHA、提供各修补/同版本证据，新独立全轮复审后Validation | **未完成**，非产品缺陷 |

范围外发现：无新增范围外缺陷。已知生产desktop来源微信busy Instant独立缺口由原任务跟踪；本轮没有改其claim/ingress路径，不将它伪称已修，也不扩大本轮到Web恢复/Android/标题/个人Provider/协议切换/生产迁移。没有读取归档目录、真实生产库或凭据。

## 6. 修复与独立复审

本次为 `/root/noting_v2_reverification` 的全新独立全轮复审，覆盖36行，未参与实现，禁止派生。先完整按冻结原文重建判据并落盘，再核当前正式代码、测试/证据和旧初审；没有沿旧问题清单代替全轮审查。§2原判据未修改、未降低，无产品规格变更；没有报告因缺行被退回的历史。

关键研讨链：

1. **F01原判据→修补复核。** 原判据R06a直接要求真实用户优先→无用户最近Assistant。初审真实Admission反例指出通用helper不能识别无类型Instant；root提既有持久回执精确owner/UID/body仅在时间投影内分类。独立读实际SQL与所有分支/测试并核最终2SHA后，确认branch用原物理owner、相同UID/body外域不借证，真人wrapper/typedsteer保持、unknown不造。26项及原独立反例1项有效，机制可关闭。没有改消息原文/metadata/History许可或计龄政策。
2. **F02原判据→修补机制与证据边界。** 原判据R03b/R08a规定null清除；初审真实wire与失败Noting证明Provider sanitize删除null。root方案只在已证官方Coding路由保留canonical nullable，其它旧repair/路由默认保持。独立核源码、可信URL helper应用、SDK/出站清理和fallback binder测试、6项SHA及真实探针响应，认可机制满足原契约。首400配置错误与纠正200/null都保留，实际工具未执行；新正式第二周期与长链未取到前不整体关闭F02/E00。
3. **本次F03发现→主会话提案→Verification评审。** 独立按R03a/R03c/R04a发现新Create `_mutation_args` 只查键/required，Store把显式None当省略。先在报告记录原判据/路径，再执行正式可信child invoke反证，两项预期拒绝而实际创建，日志 `runtime-schema.log`、测试 `test_runtime_schema.py`，均在本审查授权ignored目录。主会话提出在正式wire按canonical parameters.properties单一非nullable type拒显式null、保内部Store兼容，未传默认/[]/anyOf或type-array nullable仍走原validator。Verification按原判据认可这属于已有结构契约落实，要求正式invoke/loop精确错误和working/item零副作用正负对照；不代实现，不把认可方向当关闭。主会话将安排原实现者修补。
4. **最终门禁衔接。** root明确：由于本次新发现F03需要整改，套件要求另派全新独立审查者在最终修补提交后重新提完整判据、审全轮及旧问题，真实续短/N46也交新审查者核验。本次按已完成调查交回不通过，不等待付费E2E，也不由本审查者自审自己的整改建议后签最终PASS。

供 final-delivery.md / 用户最终汇报的实质摘要：F01应以正式Instant回执区分真实用户证据；F02恢复官方Coding对已批null清除的工具表达，首探针400与真实原第二轮失败不可隐去；F03是新拆Create丢失显式null拒绝，实际非法输入被创建，必须修复并取得正式路径零副作用证据。全部为已有目标/字段/机制细化，没有新增产品审批项、权限或结束条件。

本次门禁：**不通过**。36条中28符合、3违规（F03关联）、5证据不足，0不适用。F03及E00/V-VERSION均未关闭，不能进入Validation或宣称本轮完成。未提交/push/部署、未调用收费模型、未触生产或显示状态。

### 交回时的版本推进说明

本报告完整调查期间，root 已提交后继 `833277e804f82333a3e5be55e1c7386542e712a6` 并修补 F03。root交接称正式 invoke/loop及正例138项、原独立反例2项通过，冻结10检查63文件0/0，入口 `.hermes-dev/tools-prompt-v2/f03-report.md` 和 `.hermes-dev/noting-maintenance-v2/f03-quality.log`。此为后续审查输入，不追改本次 `runtime-schema.log` 的两项真实失败，不由主会话自评替本审查结论。本报告条款矩阵与统计仍对应 **5ee＋F01/F02、F03修前** 的已调查对象；833 的 F03 新差异及最终真实E2E由全新独立最终复审者核验。收尾只读捕获的当前HEAD/源码SHA在 `report-audit.json`，其中注明与失败时 `noting_tools.py` 的指纹差异，不把后来读到的新SHA当作旧失败执行时SHA。
