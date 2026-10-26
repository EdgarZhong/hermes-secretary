# Verification：20261027-noting-provenance-history

## 1. 审查对象与结论概览

审查者：全新独立Verification Agent `verification_final`；时间2026-10-27。Snapshot Index：本目录`snapshot-index.md`；`baseline.txt`为`02d55fdb45b4fb7c883fb477f4469912f4707f70`；唯一待审产品版本`3426c0fc9579dc0589fd0a831741b535aee71ca2`。范围为索引C01–C20对应的跨区间保真、Task来源链、Evidence time、History/Prompt及本轮适用保留契约。

**结论：本轮本地Verification门禁通过，可进入独立Validation。** 全轮38项：37符合、1有依据本地不适用（V36生产执行交接），无范围内未关闭违规或必要证据缺口；旧初审误清理I-V01已修复并用原独立反证关闭。生产上线/单目标数据转换与独立Validation均未由本报告执行，不预判通过，不声明用户总体目标完成。

进入条件：当前HEAD等于唯一待审commit，产品工作树无未提交差异；判据阶段先读根规则、两个Skill、Snapshot Index和冻结规格，动态CLAUDE/计划/代码/测试/旧报告延后到第2节落盘后；第2节原判据保持。此前4032f44初审及其原反证完整保留`reports/verification-initial.md`等原文件，当前全范围复审不改写历史结论。本次仅报告/verification-final-*白名单写入，产品、测试、规格只读。


**证据归档说明（2026-10-27）：** 为保留原始证据并遵守冻结的no-tmp约束，两次审查的6份非Markdown证据已按原字节移至ignored `.hermes-dev/noting-chain-20261027/review-evidence/`。原路径→现存路径、字节数及SHA-256见同目录`verification-evidence-archive-map.json`；逐文件归档前后哈希一致。报告中的证据引用已指向现存位置；历史执行命令、日志及脚本内部的当时路径原样保留，仅表示当时执行事实，本次未重新审查、测试或运行证据脚本。判据、原反证断言及历史结论不变。

## 2. 独立要求清单与覆盖

判据建立于2026-10-27，先于实现调查落盘。依据为冻结基线的完整07、白板语义，以及索引指定02、04、01、06适用保留部分；最新07顶部覆盖旧来源数组／time_range、物理role及工具hash。此阶段只读取规格原文与定位索引，未读取代码、测试、实现报告、旧审查或动态看板。以下必要推导只用于恢复既定目标，不新增产品权限。接线细节薄弱处以“薄弱”标记，后续必须核真实路径。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| V01 | 07顶部链结构／C04 | 数据；全部直接来源 | 直接要求：精确UID二维链，内组去重；不接受时间范围，不加跨Task全链去重 | 非空合法来源，旧模型输入退出，允许不同Task复用同UID | §3 V01 |
| V02 | 07顶部编辑粒度／C05 | 机制；同Task跨调用及Turn | 每条目每Task至多一个槽；后调用替换本Task组，旧Task节点不改删 | 多调用／续Turn仍同槽，后Task追加一次，未编辑不追加 | §3 V02 |
| V03 | 07顶部覆盖式调用／C05 | 机制；所有真实编辑 | 属性修改与完整本Task来源组同传；不能分开编辑伪造来源节点 | 缺任一侧拒绝且零副作用；fields按键合并、数组替换 | §3 V03 |
| V04 | 07原样保留、§3更新规则／C02 | 行为；无实质改变 | 沉默、Reminder、助手提示、无明确推迟不能重写；无真实属性变化不刷新来源／版本／时间 | 同值成功no-op且全部保持；新Task重复来源不造进展 | §3 V04 |
| V05 | 02§1.6、§2.7；07§3.1身份与引用 | 安全；fork/rewind/继承来源；薄弱 | 每条旧来源的继承依据绑定其准确版本；不能借另一条合法来源或废路径撑新断言 | 当前新来源逐项合法；旧链不可改；fork共享版本不可串写 | §3 V05 |
| V06 | 07 Candidate顶部、白板C3/C6/C9 | 数据；Candidate两模式 | 直接链或refs＋映射source_types二选一，不混传，不取消refs与反向派生 | 创建／更新／模式切换及引用保护一致；无重复源正文要求 | §3 V06 |
| V07 | 07 Evidence time链／C07 | 数据；直接来源 | evidence_time与二维来源内组逐槽对应，更新只重算本Task槽，不重算旧槽 | 节点数量及顺序匹配，持久恢复后仍一致，只读拒写 | §3 V07 |
| V08 | 07派生口径／时间含义／C08 | 行为；来源消息 | 真实user优先；单条时刻、多条min/max；否则最近assistant；再否则组时间范围 | 使用原消息timestamp，正文“昨天”不解析成事件时间，不使用处理时间 | §3 V08 |
| V09 | 07未知、Candidate refs派生 | 数据；未知/间接来源；薄弱 | 取不到不造现在且不丢槽；refs沿合法源链派生，不伪造直接UID | unknown保位、refs聚合可解释，显示时区及可读精度保持 | §3 V09 |
| V10 | 07 History统一范围／C13–14 | 安全；所有模式 | 默认只真人user/assistant；aux开关顶层默认false；roles/kinds不绕过；可信来源先分类 | Search/Read邻域及锚点/Get Meta一致；system不靠正文猜真人 | §3 V10 |
| V11 | 07 Get Meta每条输出／C10 | API；当前/跨域 | 每条严格UID、timestamp、语义role、content四字段，跨域归属放外层 | 不增第五字段，短正文不重叠，头尾各100字符 | §3 V11 |
| V12 | 07 Get Meta正文清理／C11 | 行为；预览；薄弱 | 仅项目注入timestamp/包装先清理再截；用户自写日期/HTML及原持久正文保留 | 同形用户内容仍保留；辅助来源只清可信包装；不影响原timestamp | §3 V12 |
| V13 | 07 include就是Search／C09 | 搜索；Get Meta | 主参数时间段，include和角色可选；复用既有FTS/CJK/LIKE/OR语义，不建新检索器 | 无关键词可列；有include与Search同语义及诊断，不退成字面contains | §3 V13 |
| V14 | 07消息覆盖／超大窗口／C17 | API；Get Meta完整性；薄弱 | 过滤后全返回；超容量明确缩小范围，不能silent partial成功 | 辅助过滤不吃默认20；容量内完整，超限／候选耗尽明确失败 | §3 V14 |
| V15 | 07统一时间边界／C16 | 行为；全部timestamp查询过滤 | 消息自身时间双端闭区间，单端亦含；不是Session开始时间 | Search/Read/Get Meta端点及时区转换一致 | §3 V15 |
| V16 | 07顶层cross_conversation／§5／C12 | 安全；所有模式 | 当前域默认，Main仅同Profile真实用户路径显式跨域，Noting仅父 | 模式不能改开关意义，跨域不给新权限，不创建绑定写副作用 | §3 V16 |
| V17 | 07 Search工具内容／C15 | API；工具消息 | 仅显式aux纳入，参数/结果各头100尾100，不hash、不混同批call | 同次call真实配对，缺源不编；普通正文Search仍真实命中窗口 | §3 V17 |
| V18 | 07 Read工具及§5.3分页 | API；精读/长工具正文 | 选定工具可完整参数及结果；同源有界窗口逐页重验owner，不无界输出 | call_id配对、分页可复原、超限不诱导越权文件工具 | §3 V18 |
| V19 | 02§2；04§2；07§5.2/5.5 | 机制；历史/隐藏/分支 | History只是真实合法可见原文，排除失效/Prelude/不可见注入；inactive合法fork保留 | Search与Read同路径；压缩保身份，不扫描复制全库，检索故障不伪空 | §3 V19 |
| V20 | 07 Prompt审阅收缩／C18 | Prompt/模型 | 最新父区间主依据、早期仅必要追溯，真人第一assistant第二；Get Meta默认取UID，细节Read、定位Search | 真实构建文本有准则且无区间术语教学，实际代表行为不是机械遍历 | §3 V20 |
| V21 | 07稍后处理／C03、§4 | 行为/权限 | 未明推迟正文/done保持，Schedule缺口可单独建议且不造时刻或实际排期 | schedule-only编辑配完整本Task来源，Noting不能scheduler | §3 V21 |
| V22 | 白板N1/L/E；07顶部第5/6/8/10块 | Prompt/生命周期 | 双类条目/槽位说明集中，去重复；清退/结算及原finish结束语义不改 | 新Task及control/continuation一致；不加语义硬门禁或改变退出规则 | §3 V22 |
| V23 | 07 v2§0/3、§8.2 | 权限/接线 | 六工具固定顶层；Main四写拒绝，Noting仅六；同步/并发/invoke等一致 | 可信身份、拒绝零副作用、旧alias退出，固定工具不是执行授权 | §3 V23 |
| V24 | 07§3.1/§4.5/§8.1；02§5 | 生命周期 | finish独立整批预检、请求后锁工作态；原生Turn返回才Commit Gate；forced/overflow仍合法提交 | 混批无执行、结束后写拒绝；真失败/关闭不伪成功，资源释放 | §3 V24 |
| V25 | 07 v2§3/§6.3；白板K6 | 数据/原子性 | 稳定ID、新版本只真实变更；单条输入合并、引用/relations归档原子，无长文硬限制 | 失败无working副作用；可选清除及必填、done只读元数据约束保留 | §3 V25 |
| V26 | 02§2.6–2.7/§3.3–3.4；07§3.1 | 持久化/并发 | 完整Snapshot与pointer同事务；Anchor/enable/source/版本再校验；晚旧结果不回退 | 并发、rewind/fork、重启读取及失效Anchor放弃均守约 | §3 V26 |
| V27 | 07§3.1/§8.2；02§5.5 | cache/多模态 | 准入冻结真实父root/tools/messages，所有循环/重试/续Turn同前缀，后缀累积 | 不从History拼父，不在子中补工具，不刷新MCP/记忆，实际请求可核 | §3 V27 |
| V28 | 02§5.2–5.4；04§4.5–4.6 | 原生/运行/关闭 | 持久独立child、原生模型继承与Profile；最多5Turn，无child auto compact；不自动重启恢复 | D01只已证External拒绝、未知保原生；关闭/失败/资源隔离 | §3 V28 |
| V29 | 04§3.4–3.5；07工具Schema边界 | 开关/热冷恢复 | 全局关闭非eligible原生、History独立；工具面在父合法构造恢复同步，冻结运行中不热改 | 新schema正常恢复可达、local off不改root；Main/Noting开关组合 | §3 V29 |
| V30 | 07 v2§7、§8.1；白板P | 保留compaction契约 | 原生阈值保tail、其它去默认tail、here N保显式；Idle正常提交后压缩后通知 | 失败保上下文/新尾；Force区间去重、External与预算/异常不错误Idle | §3 V30 |
| V31 | 07§6/§8.14；02提醒保留条款 | 保留Scheduler/Reminder | Notebook与Scheduler独立，建议不副作用；claim/ACK/retry、busy deferred和Profile owner保持 | 本轮改变不破坏状态/时间/载体/ACK，失败不声称成功 | §3 V31 |
| V32 | 07§8.13；白板N3 | 保留通知 | 仅生效pointer准备、追加重验，完整Notebook同Framework；不触发Turn/外发渠道 | 无旧排队正文后插、失败诚实、runtime同写及阈值Proposal保持 | §3 V32 |
| V33 | 07身份投影修订；06§1.12/2.6–2.7；根AGENTS | 投影/兼容 | 模型不泄snapshot/version/anchor但entry可操作；人类/API旧字段兼容；slash人类只读 | Show/回执/初始续Turn/Framework一致；不修改旧持久事实 | §3 V33 |
| V34 | 根AGENTS Prompt验证；07§9.3及最新顶部 | 证据 | 机制测试与真实模型各覆盖合适边界，当前版本可追溯；不以HTTP/Finish代内容正确 | 检查真实构建完整Prompt、原生工具协议/行为/prefix及差异影响，明确未测 | §3 V34 |
| V35 | 01§1/3–4；02§1.8/3.1；根AGENTS | 架构/平台 | 只state.db自有表、原生入口、profile-aware、增量兼容，无新执行器/检索库/个人依赖 | 差异及目标平台证据不引新规则、环境/lock不改，非启用不受影响 | §3 V35 |
| V36 | Snapshot C01；07旧数据范围 | 发布交接；本地不执行 | 只核Alex一个真实置顶目标一次转换；不通用迁移，不改聊天/模型/Schedule/其他会话 | 本地工具/步骤可审核；上线目标/备份/版本/服务/data真实性由main发布核验 | §3 V36 |
| V37 | 07§12固定工具兼容及热恢复 | 调试保留路径 | 从持久旧材料恢复原生任务，freeze前补当前固定工具而非子中动态补；旧记录不改 | 新契约恢复来源槽位/工作态正确，原接口身份幂等/结果诚实 | §3 V37 |
| V38 | 根AGENTS文档/冻结规则；01§1.2 | 约束 | 文档职责、规格/常量一致；冻结检查不增减放宽，不凭旧失败误称新回归或全过 | diff/规则入口/证据版本核验；基线失败保留明确限制 | §3 V38 |

## 3. 逐条实现证据

以下每行与第2节同编号合读，形成“冻结原文→必要不变量→实际路径→适用输入→方法→观察→判定”链。证据键在表后列出具体日志及版本；函数名为当前3426c0f可复查位置。所有“符合”仅指本轮变更及适用保留路径，不代表旧轮全部问题已修。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| V01 | `run_noting_task→initialize_notebook_work→notebook_create/update→NotebookStore→NotebookWorkingState._apply_sources/_validate_sources`；`noting_contract`声明 | 亲读Schema及路由；真实DB `test_real_edits_require_valid_complete_slot_and_refuse_atomically`拒绝范围、整链手写、重复/空/非法UID；`test_same_task_updates_restore_slot_then_next_task_appends`跨Task同UID可复用 | F：provenance_arrays32；L同文件32 | 符合：模型写一维当前槽，持久/读二维，旧写范围不作为alias保留 | 不恢复旧生产结构；V36单独转换 |
| V02 | runner以`task_id=str(admission_id)`传入Store；`_apply_sources`仅替换本owner尾槽；`_working_state/_restore_entry`恢复原admission | DB多调用/恢复同槽及下一Task追加；native continuation沿同child；`test_nonempty_initial_and_successful_receipt_restore_task_owner_then_resume`核同owner；现有item JSON不变 | F：provenance_arrays32、task_recovery4、noting_history_tuning_prompt3；L | 符合：Task不是工具调用，也不是native Turn；可信owner参与实际持久状态 | 默认UUID仅独立内部Store；正式runner不依赖该默认 |
| V03 | `NotebookWorkingState.update`验证属性→`_apply_sources`→全簿验证→`_persist`；`_insert_version_conn`写事务再验 | 缺来源/属性、非法UID等场景深比较working与item rows；只传来源拒绝，fields只合并键，普通数组替换 | F：provenance_arrays、maintenance_v2；L | 符合：真实编辑与当前完整来源槽同传，拒绝无副作用 | refs型Candidate沿其替代来源，非强迫其混传直接UID |
| V04 | `update`先比较实际entry，no-op不分配item；Prompt第2步及description指导 | `test_noop_does_not_create_task_node_or_version_and_fields_merge`核版本/时间/全态；真实第二Task只有助手提示，Notebook1==Notebook2；普通无关条目第一Task也相等 | F；M、A的`second_task_identical_payload`及entry3无变更 | 符合：同值输入不造来源节点/版本；实际模型代表样本守原样 | 内容支持属于模型判断，不新增自然语言硬门禁；不能保证任意模型均遵循 |
| V05 | `source_basis_conn→provenance_prefix→require_item_owner`；`_source_validator_conn`新组；commit exact_version核验 | rewind旧链保留/新非法来源拒绝、fork共享原item但分支改动隔离；提交前rewind使新组失效则原子拒绝；source_basis绑定同lineage已提交版本 | F：provenance_arrays的rewind/fork/commit、foundation26/lifecycle30；L | 符合：继承许可仅覆盖准确旧前缀，新组仍查当前路径 | 旧来源可off-path继承，不等于重新授权旧证据支撑新断言 |
| V06 | `validate_candidate_provenance/validate_references/public_state`；`_apply_sources`及item提交引用检查 | refs派生、标签映射、混传/空来源/candidate引用拒绝；当前唯一未提交槽direct↔refs往返；已提交同owner清槽也拒绝且旧item不改 | F：candidate_source_contract52、settlement10、provenance_arrays32、task_recovery4；L | 符合：两模式互斥、refs及反向派生保留；当前草稿形态转换未删除旧Task节点 | 工程细化待用户追认；不是批准或外部写入权限，§6单列 |
| V07 | `_apply_sources→_insert_version_conn→derive_evidence_time`，persist `evidence_time`；`evidence_time`读旧槽 | 多组时间与provenance长度/顺序一致；同Task替换只改尾槽；旧time在读及消息timestamp后来变化时均不刷新；工具写evidence_time拒绝 | F：provenance_arrays、r3_notebook_time_projection9；L | 符合：来源/时间同一写事务持久，旧节点只读 | refs型时间是现行源链派生，与直接链逐槽表达区分 |
| V08 | `notebook_evidence._message_points→enrich_message_source→semantic_role` | users优先单点/多点minmax、无user最近assistant、否则全部引用消息minmax；正文日期冲突和系统user/assistant假冒优先级反例；原timestamp重启保持 | F：provenance_arrays的priority/original/restart/semantic_system；L | 符合：原消息时间而非叙述事件/维护时间 | “最近assistant”按合法消息轨迹的最后一个，非Noting当前时钟 |
| V09 | `_message_points`未知返回None；`_referenced_time`拼源条目数组；render可读Profile时间 | `test_unknown_time_keeps_slot_and_is_not_recomputed_on_read`核null保位；refs更新跟随当前源槽、无直接provenance；可读点/段且无now兜底 | F：provenance_arrays32、render4、r3_time9；L | 符合：未知不丢节点、refs不伪造直接来源 | 展示解析失败按既有best-effort边界返回，不新增提交门槛 |
| V10 | registry/inline→`conversation_history→_arguments/_eligible_row→HistoryPaths.rows` | 三模式和锚点邻域统一aux门控；roles/kinds/旧tool switches反例不能绕；共享分类在先，包装清理在后 | F：source_modes47；P：当前source_modes53；L53 | 符合：默认真人/assistant，显式aux才允许tools/system | 只改变模型History公共语义role，不回写物理role |
| V11 | `_candidate_public(mode=get_meta)→cleaned_preview→head_tail` | ≥20/200全部返回、201报错；四字段精确集合；≤200原文不重复、长文头100尾100；跨域外层分组 | F/P/L：source_modes；compression_parts30 | 符合：每条严格四字段；mixed UID按语义部分计容量 | UTF码点预算，不承诺整条原文已读 |
| V12 | `cleaned_preview→_cleaned_content/_strip_stamp`；trusted steer/compaction/system wrapper分支 | 亲读3426修复：额外Gateway纯文本剥离已撤回；原独立CLI粘贴反证不改断言重跑1过；6个CLI/weixin×user/steer/native frame保护例、HTML/日期、真实trusted包装、原DB不变/Read原文均过 | P107及SHA；R1过0.7s；L source_modes53；A | 符合：仅项目timestamp/可信HTML外壳清理后截取，用户纯文本来源头保留；初审I-V01关闭 | 不再把普通字符串Gateway JSON头当可证明框架包装；规格未要求清这种纯文本 |
| V13 | `_get_meta`有include用原`HistoryCandidateStream`，无include用`TimeCandidateStream`；Search同stream | 无关键词时间主查询；参数化同Search query匹配；CJK/布尔/短语等既有路由、非法query、stale index及读取失败按诊断报错 | F/P/L：source_modes；F r3_history82 | 符合：不以独立contains替换include语义，无新索引库 | mixed投影只用既有literal fallback核可见部分，并诚实保留边界 |
| V14 | `_collect_search`读取至多一条额外合法结果；`_get_meta`overflow/incomplete抛明确错误 | 200完整/201不带部分messages，候选budget耗尽即使零合法结果也incomplete_window；index/source无法验完整亦拒绝；aux过滤不沿20默认截 | F/P/L：source_modes、compression_parts容量；`_get_meta`源码 | 符合：成功仅完整已验证窗口，不能silent漏条 | 200计语义parts；无界请求可以明确要求缩小，不承诺跨任意规模完成 |
| V15 | `_time_bound`；TimeCandidate SQL `>= <=`；`_eligible_row`所有模式双端；原Search候选时间 | Get Meta边界单点、Search/Read单端与双端；compression辅助part端点与原timestamp；精读锚点拒绝时间选择避免筛掉锚点 | F/P/L source_modes/compression_parts；F r3_history | 符合：闭区间筛消息时间，无Session-start替代 | 精读anchor依其原路径身份，不接受混用时间过滤 |
| V16 | `owning_history_db/resolve_history_scope_conn→require_current_owner→memberships`；Noting真实children/admission查询 | Main显式跨同DB真实用户Conversation、fork多membership；Noting跨域/错ref/错DB、普通辅助runtime拒绝；无绑定修复或写入；每页再授权 | F/P/L source_modes/compression_parts/paging；F identity8/foundation26 | 符合：开关独立不变义，模型Ref不是授权 | 无跨Profile搜索；不新增全库正文扫描 |
| V17 | `_project_content→ToolInvocations`按assistant batch+call_id配对；Search `preview=True→head_tail` | 多call乱序/同ID重复/边界/隐藏结果缺源反例；参数/结果各200预算、不hash；完整Read选择同call；普通assistant正文仍excerpt cap | P107；F r3_history82；L | 符合：无相邻猜配和同批串参，缺失值诚实None | 缺失工具来源不编造；assistant有实际正文时仍是assistant语义部分 |
| V18 | `_read→_read_public_row→_project_content`；`content_offset`单锚0/0 canonical JSON分页 | 双值长工具参数/结果完整拼回；Unicode/结构内容码点分页；每页作用域/rewind重新验证；结果预算及oversize指导不诱导文件越权 | P：paging23/source_modes53/compression_parts30；L同分支 | 符合：选定工具完整可达，同时保持有界输出 | 一次不保证巨型正文全部进入模型；同identity+role选择续页 |
| V19 | `HistoryPaths.rows/parts`与`get_history_auxiliary_foreground_conn→_foreground_winners→native split` | 正式archive_and_compact的pure/mixed/double、fork inactive源、rewind、hidden/model_only/human_only/Prelude；同UID同role coalesce后精读/分页一致；default API行为未改 | F/P/L compression_parts30；F foundation/lifecycle；H | 符合：辅助只补明确允许系统part，非Full直接外放；新Notebook来源仍走原History gate | 旧Prelude15项在基线同失败，未冒称全Foreground套件全过 |
| V20 | `HISTORY_SEARCH_GUIDANCE`实际Main构建；`DEFAULT_NOTING_TASK_INSTRUCTION`经runner包装 | Main开/关Noting均实际请求有模式/权限指导；初始/continuation携完整Task/control；真实两Task都Get Meta取得UID，不重读细节、无非白名单工具 | F：history_tuning3/r20；M及A | 符合：最新区间主依据、有限必要历史、优先真人、旧证据不新进展的已定指导已到达实际请求 | 真实样本只代表两Task，不等于所有未来任务自然选择同策略 |
| V21 | Prompt第2与Schedule步骤；typed `notebook_update→_apply_sources`；suggestion validator仅语义对象 | M第一Task税表fields/done保持，仅建议+新来源/time/version；已有真实Scheduler登记取书条目完全不变；受控建议框架4项无实际排期副作用 | M/A；F schedule_suggestion_framework4/schedule_status3；L prompt3 | 符合：建议独立变化且不造具体推迟，不代表登记；Noting无Scheduler执行权限 | 真实已有排期由正式SchedulerStore及可见回复给证据，不通过删断言掩盖fixture缺口 |
| V22 | `noting_prompts`第2/TOOL USE/Candidate来源及保留第4/第5/第7；CURRENT_CONTROL/CONTINUATION | 对冻结基线diff：生命周期/结算段、finish及control/continuation不变；只更新本轮已确认来源及保真说明；native初始/两Turn+真实样本 | F：history_tuning3、r20、finish_exit22、settlement10；M | 符合：同任务槽位集中、不重教区间术语、旧清退及结束语义保持 | 本轮不重开完整旧内容/长上下文效果实验；原有契约回归按受影响范围审 |
| V23 | `noting_surface.apply_main_read_surface`完整六定义；`noting_dispatch_block`、`tools.secretary_dispatch`、inline与executor | fixed permissions86、fixed request7含Main四写/Noting其它工具、invoke/并发/顺序正式拒绝；旧alias退出；当前Schema缺省与handler一致 | F及L fixed_request7；M请求tools/实际calls | 符合：声明不等于授权，可信身份在执行点继续拦截 | 不是依靠模型没误调来证明权限，强制负例独立存在 |
| V24 | `guard_noting_tool_batch→finish_noting→store.freeze→_run_child_turns→_commit_when_complete` | 混批整批拒绝、finish后写拒绝/重复finish幂等；原生Turn返回才commit；forced/overflow合法状态提交、一般失败不新Snapshot、resource close | F：finish_exit22/noting_child38/r3_child56；RPC3；L | 符合：本轮Task owner增量未改原结束门槛，真实失败不伪正常 | 旧固定请求数失败不自动解读为产品finish回归；RPC已更新到终止契约 |
| V25 | WorkingState create/update/archive全簿draft；`_insert_versions`同事务关系清理；item INSERT-only | maintenance71、done120、source_contract52、settlement10；非法字段/null类型、引用归档、relation清理失败回滚、no-op；真实item旧row逐字不变 | F；L provenance_arrays/task_recovery | 符合：稳定ID/不可变版本、既有done与类型字段、原子失败保持，不设写作硬长度 | archive机械引用清理保留旧来源，不强加新UID；不是改清退产品语义 |
| V26 | `commit_noting_snapshot→notebook_commit_snapshot_result_conn→validate_snapshot_state_conn→snapshot_item_ids_conn→_notebook_reselect_pointer_conn` | 逐项精确版本/owner/source复核、Anchor/enable gate；旧晚结果pointer不回退、rewind失效放弃、fork共享旧Snapshot隔离 | F：foundation26/lifecycle30/notebook arrays/store/r3_notebook120；L | 符合：完整Snapshot及pointer同一写事务，不以完成时间代覆盖 | 允许不同任务各自冻结基线，07§11.1明确不要求B草稿继承给C |
| V27 | `freeze_parent_active_prefix/build_noting_child→apply_cache_parity_from_parent→_continuation_history`；request audit | 亲读无父热刷新；受控native多Turn及工具循环全前缀/多模态；M独立重算6wire工具1SHA、root1SHA，两个Task分别3/2消息前缀各全请求一致 | F：fixed_request7/r3_child56/dynamic_tools19/history_tuning3；M/A；L | 符合：冻结父root/tools/Active，当前工具在父恢复边界同步，子中不临时补表 | 字节一致不是命中证据；真实Usage另有cache_read，不保证所有Provider命中；旧基线请求计数问题保留 |
| V28 | build child独立DB/session/profile；runner≤5Turn、close/lifecycle；原D01 `noting_trigger_gate`接缝 | 当前差异只加admission Task owner，模型/route/cache helper不改；native child/失败释放、恢复原Profile/环境、权限测试；真实native k3.1-pro/high | F：noting_child38/r3_child56/recovery22/permissions86；M；L | 符合：无新执行器/Provider适配；原生关闭与失败资源契约保留 | 不自动重启旧child；显式RPC恢复不是自动恢复或生产重放授权 |
| V29 | `apply_main_read_surface/_refresh_noting_definitions`→native prompt同步；child直接return不刷新 | 旧pin恢复canonical六表，global Main Noting开/关/history常有，local off不重建root；真实请求构建7项与debug3项到后续断言均过 | F：fixed_request7/permissions86；RPC3；L | 符合：Schema/提示/dispatch在合法父边界一致，冻结后不热改 | 当前表更新会一次损失旧tools cache，恢复来源明确记载不声称旧wire相同 |
| V30 | 原`noting_runtime`共同admission、`_publish_after_idle_completion`及父native压缩；本轮Foreground只读增量 | 亲审diff无compaction策略/Force/Idle参数变更；新辅助投影使用真实native archive_and_compact/double/fork/rewind；旧29集合中的joint/visibility失败为基线原文件 | F/L/H；源码关键不变量；F lifecycle/r3_child | 符合：本轮不改既有触发/保tail/Idle正常提交时序；新增读取未夺原native owner | 不宣称旧Joint/Prelude所有断言已修或此轮重验全部历史能力 |
| V31 | typed建议仅Notebook写；原SchedulerStore/due/claim/ACK消息路径未改；分类只读exact receipt | 确认代码差异无Schedule状态机/ACK写；schedule_status3/suggestion4、Foundation/lifecycle及真实已有排期保持；receipt三模式/foreign相同UID及fork反例 | F/P/L；M；H基线crash8 | 符合：来源分类未消费/确认提醒，不把建议/条目变化联动到Schedule | 既有跨进程Instant busy/crash夹具问题不冒称修好，范围外保留 |
| V32 | `commit_result.pointer_changed→publish_noting_completion→notebook_snapshot_if_current_conn`和安全追加锁 | 亲追runner发布只新pointer；Main owner切换不发；Framework19、source维度Snapshot回归及RPC当前尾部/队列断言通过；render完整新链 | F r3_framework19/noting_child/recovery；RPC3；源码 | 符合：新链完整进入现有Framework，旧排队通知仍重验，失败/forced语义诚实 | 不承诺Framework重启必达；不自动Turn/外发渠道 |
| V33 | `public_state→readable_notebook_entry/state→model_notebook_data/view`；show/tool/control/Framework共投影 | owner元数据全普通投影隐藏，模型version隐藏entry_id保；model audit3/version3、local_uids61、render4、Framework19与native请求断言；人类/API audit保内部版本 | F；L；源码diff | 符合：模型/人类/API身份边界保持；新provenance按已确认契约替换旧来源形状 | 未施工UI/APK；slash人类瞬态路径未改变，不拿Framework完整注入扩大slash语义 |
| V34 | 实际Main `_make_agent→AIAgent→run_noting_task→typed handler→SQLite`，受控native与既有真实API证据分层 | 独立解析真实wire/工具轨迹/前后Notebook；两Task6HTTP200、正常finish及source/time保持；8文件后继差异按分支审，当前机制和Linux补齐；不额外调用模型 | M/A；F/P/L/R；见§4 | 符合：当前代表核心链路有真实模型证据，新增互斥/Compression/修复由当前机制反证支撑 | 两Task均1Turn；未把真实样本冒称覆盖Candidate转换、Compression辅助、竞态、任意Provider/长上下文 |
| V35 | 变更集中原Notebook/History/Prompt siblings；native SessionDB与Profile路径，`TimeCandidateStream`只metadata | diff无原schema/ownership/依赖锁/新模型执行器；PM解释器官方runner；Linux完整18394 Git blobs匹配3426、真实Linux7文件132过 | L/A；F/P；diff | 符合：原生机制复用、state.db自有状态、增量接口；真实目标平台而非OS伪造 | 生产repo/venv/config未动；无macOS UI/Android真机声明 |
| V36 | 私有一次性manifest固定目标/51item/8Snapshot；事务内精确旧hash→仅来源JSON替换→正式validator→比较其他表/schema | 亲读私有脚本：固定manifest SHA、目标Ref/Session/pointer、精确51row、原消息proof，BEGIN IMMEDIATE，失败rollback，触发器原DDL恢复；副本演练报告与收据 | C；主会话release preflight/dryrun收据 | 有依据的不适用：生产apply/上线不属于本地只读Verification执行；本地转换方案已具可审核证据，交main发布核验 | 生产未上线/未转换；必须后续核main、服务、真实目标、其他对象/备份，不提前判C01完成 |
| V37 | `reconstruct_noting→_base_snapshot/_working_state/_restore_entry/_restore_archive→_prepare_fixed_recovery_tools→原runner` | 成功模型回执按admission owner+可读body唯一匹配原不可变版本，歧义/foreign task拒绝；非空起始/归档/当前槽转换后恢复；RPC3核幂等/原记录/排期环境/lease尾部 | F recovery22/task_recovery4；RPC3；L | 符合：不重放维护，不新建专门快照；freeze前补工具如实记cache变化，结束语义未改 | 不授权实际重放旧生产任务；旧失败重建范围外问题不据接口通过宣称全部关闭 |
| V38 | 根三文档/07增量、产品diff与冻结检查入口；测试原文/日志版本 | README稳定入口、CLAUDE动态待追认、07明确工程实施事实；check10项ok；diff-check通过；独立解析29基线失败原8文件逐字未变；当前V01 SHA匹配 | Q/A/H；F/P/L及§6 | 符合：未增删放宽冻结规则、环境/lock未改；基线问题与本轮通过分开记录 | 未称全Secretary分区全绿；报告和文档本身仍需main最终接收、更新交付状态 |

证据位置与版本：

- **F**：`.hermes-dev/noting-chain-20261027/final-integration-tests.log`，主会话执行，4032f44产品，官方PM `.venv`/原lock、官方runner、macOS，40文件1094过0败，87.2秒，10 workers，一次集成收敛检查。本次亲读完整文件清单及逐文件结果。3426相对4032仅产品`tools/conversation_history_projection.py`撤回额外Gateway纯文本清理，另新增6个source_modes保护例和文档，不影响其它F路径。
- **P**：`.hermes-dev/noting-chain-20261027/review-evidence/history-v01-{tests-final.log,version.sha256,full-check.log}`，实现端最终修复版本：source_modes53、compression_parts30、paging23、原独立反证1，共4文件107过0败8.6秒10 workers；独立重算源码/测试/原反证三个SHA全部匹配3426工作树。`full-check.log`10检查通过。源SHA及日志SHA收在A；不是复用修复前通过数冒称修复已验。
- **R**：本复审者执行，`.hermes-dev/noting-chain-20261027/review-evidence/verification-final-counterexample.log`，`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh .autonomous/20261027-noting-provenance-history/reports/verification-preview-counterexample.py`；原反证源码及断言完全未改，1文件1过0败0.7秒。没有重复大套、昂贵模型或服务操作。
- **L**：`.hermes-dev/noting-chain-20261027/release/{linux-final-tests.log,linux-final-source-verification.json,linux-final-manifest.json,v01-final.patch,linux-env-build.log}`。main在Linux隔离目录、原lock构建独立官方PM dev/test环境，7文件132过0败53.7秒j2；本复审独立比对manifest全部18,394个blob/OID与3426 Git tree精确一致，patch SHA也匹配。remote验证收据all_match=true，35个PowerShell仅按仓库.gitattributes声明CRLF在核Git OID时规范化，工作文件保声明EOL；并非改规则或伪造OS。初始4032 archive7文件126过56秒仅历史中间证据，最终当前版用L132；未操作生产repo/venv/config/service。
- **M**：`reports/model-evidence.md`及私有`.hermes-dev/noting-chain-20261027/e2e/live/{result.json,wire-01…06.json,child-1/2-construction.json,child-1/2-transcript.json,outcome-1/2.json,seed.json,notebook-1/2.json,existing-book-schedule.json}`。实际k3.1-pro/kimi-coding原生chat_completions、高推理，库外cwd、虚构隔离Profile；两Task6HTTP200、无非白名单调用，构造same_root/same_tools均true。原Alex config/.env/SOUL/auth逐SHA保持，未用生产消息/渠道。失败旧别名及缺登记证据样本仍原样保留；不拿其等同正确生产型号或删除失败。实际cache_read Task1=72192、Task2=36608；没有实际账单，不宣称免费或总成本收益。
- **A**：`.hermes-dev/noting-chain-20261027/review-evidence/verification-final-audit.py`与`.hermes-dev/noting-chain-20261027/review-evidence/verification-final-evidence-audit.json`，本复审只读解析。独立重算6wire tools/root各仅一SHA；两Task分别3/2个父前缀消息全请求相同；工具轨迹GetMeta→update→update→finish及GetMeta→finish；第二Taskpayload全等，税表fields无修改/取书无修改。17个受测源码SHA对当前8个不同，详见§4，明确模型证据适用边界。亦核P源码/日志SHA、L清单与原始29失败集合。
- **H**：`.hermes-dev/noting-chain-20261027/{integration-tests.log,nonshape-frozen-baseline.log,baseline-failure-comparison.json,rpc-final-surface.log}`和`review-evidence/history-compression-{prelude-baseline.log,baseline-compare.json}`。首次87文件1703过105败保留；74个来源契约适配与2个RPC旧底座已闭合。当前29项8文件同冻结基线失败集合，本复审从原日志独立解析并比对：baseline29均在current初始105集合、JSON对应完全一致；这8个测试文件与冻结基线字节相同。另Prelude15个旧失败与基线同集合，原测试文件未改。RPC规范结束/固定工具底座更新后1文件3过6秒，完整走到下游断言；不是产品结束机制修改。
- **C**：`reports/conversion.md`与私有`.hermes-dev/noting-chain-20261027/production/{convert_notebook_once.py,conversion-manifest.json,mechanism-fingerprints.json,dryrun-result.json,rehearsal-result.json,execution-receipt.json}`（若收据按既有同目录命名以报告原路径定位）。报告记录51版本/8Snapshot/31独立节点/累计55节点、180 UID引用、81不同UID；副本完整apply+关闭重开验证、事务故障回滚、重复执行拒绝、其他表/schema指纹保持。只读核脚本不等于生产执行，未复制真实正文/UID进本报告。
- **Q**：P十检查日志、`git diff --check 02d55fdb 3426c0fc`无输出；产品diff未改`uv.lock`/pyproject/检查器/CI/AGENTS。root当前CLAUDE已读（判据落盘后），两项Agent收敛仍标待追认，未冒充用户确认。

## 4. 核心目标及验证方法审查

**本地实现门禁通过。** 第2节38项全部覆盖，37项符合，V36生产执行部分有依据不适用于本地只读门禁；无本轮范围内未关闭违规或必要证据缺口。独立Validation、生产上线与单目标转换尚未在本报告执行，不能据此宣称用户目标完成。

三条核心纵向路径已按入口追踪：

1. Notebook：正式runner用原admission给可信Task owner，typed工具在task锁下先做完整draft验证，再在DB写事务校验来源/继承准确前缀并插入不可变item；源与只读时间一并提交。finish只固定状态，native Turn返回后既有Commit Gate再验Anchor/local enable/version/source，插完整Snapshot及重选pointer原子完成。no-op不产生节点，多个调用/Turn/恢复占同槽，后Task一次追加。恢复根据既有原Snapshot及真实成功工具回执匹配owned不可变item，歧义拒绝、原失败记录保留；未新增恢复快照或重放写入。
2. History：正式registry/inline复用同handler，实际Agent owner/运行Noting children绑定及只读事务确定范围，原生候选搜索和合法Foreground membership再验证。新增TimeCandidateStream只枚举metadata；语义role/辅助开关先过滤，Meta再可信清理+固定头尾；超过200或未证完整报错。工具参数结果按call_id和实际assistant batch配对，不以相邻猜测；精读同源分页每次授权。Compression辅助读取从同一原生合法winner/native split补可见part，未将Full Prelude/审计/hidden带进模型。
3. Prompt与实际模型：正式Main构建、Noting初始/continuation的全Task/control、固定六工具与父多模态前缀均由当前native机制测试核查。真实k3.1-pro样本实际调用Get Meta取得UID，第一Task更新采购仍保原条件、税表只补建议、已有排期条目不改；第二Task仅Assistant提示且整簿完全不变。独立重算wire而非只信result.ok或模型自述；各Task只有1Turn，续Turn/竞态/恢复由当前正式机制证据补，不声称真实模型自然覆盖这些分支。

**8个受测源码后继差异的适用性。** A逐文件SHA独立核对：`agent/system_prompt.py`、`notebook_evidence.py`、`notebook_render.py`、`noting_contract.py`、`noting_child.py`、`noting_tools.py`、`noting_prompts.py`、`noting_recovery_sources.py`、`conversation_history_time.py`与模型受测源码相同；8个不同为`hermes_state_message_provenance.py`、`hermes_state_conversation_history.py`、`tools/session_history_tool.py`、`tools/conversation_history_projection.py`以及`notebook_contract/items/model/store.py`。前4个后继补可信receipt/legacy heartbeat与Compression parts、相应role/selector说明和预览处理，后4个补当前唯一未提交direct Candidate槽的refs切换限制；当前最后修复又撤回额外Gateway纯文本清理。真实样本都是普通真人/assistant、直接来源事项，无Candidate、Compression UID、legacy wrapper或粘贴Gateway头；其实际核心分支和获批Prompt/六工具写契约未变。其差异分支已由F/P/L的真实DB/native路径及R旧反证覆盖，故复用M的代表链路行为与原生工具协议证据有依据。不能把M称为3426全源码同字节实测，也不能声称工具说明新增文本已经过同一次真实模型请求。

**薄弱规格不是免验理由。** Task槽位没有指定实现函数，但owner必须跨Turn/恢复保持；实际admission owner参与持久状态，不能用每调用append代替。系统含Compression的方向明确，即使native一UID复合承载，也必须让其可显式读且不丢真人；当前parts/role选择、同role合并和容量计数满足此方向，不以旧anchored禁止roles条文否定新能力。Candidate当前草稿换形态可以工程细化，但已提交/旧Task节点绝不能删，DB写入点再次读取Snapshot引用事实保证。预览纯文本清理没有可信证明时必须保留，不能用猜平台替来源证明；本次旧反证实际证明了错误实现会通过此前1094项，修复后原断言通过才关闭。

**测试方法及依据。** 新正反例预期均能回到第2节冻结条款：UID-only、同Task、closed interval、严格四字段、语义role/aux、来源保真及明确完整性。大部分测试用真实隔离SessionDB、registry/typed handlers、native archive_and_compact和原生child loop；受控SDK只替外部响应，不替待验owner/状态机/数据库/工具拒绝。实际构建Prompt精确文案断言用于已审文本到运行时的接线，不是源码字符串自证。未重复大型套件；仅因旧缺陷修复定向重跑原独立1项，当前107项及Linux132项证据按SHA/版本复用。F的1094过不等于全分区全绿，旧基线29与Prelude15不自动豁免新回归，已另按变更路径及新机制审查。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| 初审I-V01（P2，旧报告称V01；与本报告条款V01无关） | V12；`conversation_history_projection._cleaned_content`旧`_strip_gateway_origin` | 4032真人CLI正文含原生timestamp＋用户粘贴的Gateway纯文本来源头时，旧清理误删用户正文；原独立反证曾失败 | 违反“只清本项目注入timestamp/HTML、保留用户原文”，初审阻断属实 | 3426删除该额外纯文本剥离；原反证SHA/断言未改，复审者官方runner1过；新增6保护例及trusted包装/Compression/权限回归107过，Linux当前132过 | 已关闭；无同类新范围内缺陷 |
| 发布交接C01（非代码缺陷） | V36；一次性脚本及main发布流程 | 尚未生产apply/上线/正式服务验真；本地副本演练与精确目标约束已可审核 | 不阻断本地只读Verification；仍是用户总体完成条件，不能提前声称完成 | main在独立Validation通过后按既有授权核main版本/自然空闲/两套三库备份/精确目标与源proof，事务转换后验其他表/schema、服务及实际读取 | 待main执行与发布核验，不预判结果 |

本地范围内新增整改：无。建议下一优先级为独立Validation，再按用户授权发布并单目标转换；最终收敛由main按套件判定，不用本报告代替Validation或发布结果。

范围外/历史问题：H列29项8文件与Prelude15项冻结基线失败保留，不冒称已修。跨进程Instant busy、旧日期/旧Noting重放、UI/APK、Provider/Persona、NM和其他服务迁移不在本轮扩修范围。本复审没有新增独立范围外发现，没有更改原测试来使它们通过。

## 6. 修复与独立复审

审查者为全新`verification_final`，唯一对象3426c0fc9579dc0589fd0a831741b535aee71ca2。重新建立38项全轮判据并先落盘，再读取实现、动态CLAUDE、初审及证据；不是只复测旧问题。第2节条款未为当前实现增删或放宽。随后补核冻结白板HTML中脚本承载的七类型详情和完整场景文本，它们重复静态白板/07已覆盖的语义；未导致判据变化，也未用代码建议反推要求。初审稿保留`reports/verification-initial.md`，未覆盖其当时不通过结论。没有本报告被main以缺列/缺证退回的记录。

关键研讨链及本次独立评审：

| 事项 | 原判据/初步发现与薄弱处 | main提案及理由 | 本复审依据原判据的评审与关闭证据 | 规格/确认/最终交接 |
|---|---|---|---|---|
| mixed UID Compression读取 | V10/V11/V16/V19：辅助可读system含Compression，但native一UID可有摘要与原消息，Get Meta只能四字段 | 保默认原非压缩部分；显式aux按语义parts返回、anchored roles选system；同UID同role system合并，不新造UID | 忠于明确方向，已有roles作selector使内容可操作；同一parts owner用于Search/Meta/Read/容量/分页，native pure/mixed/double/fork/rewind、hidden隔离及不扩大Notebook新证据gate经当前F/P/L核实；不降低默认或权限判据 | 不新增产品范围，工程接口细化；CLAUDE/07仍标Agent自主收敛待用户追认，审查认可不冒称用户已选 |
| Candidate本Task唯一未提交direct→refs | V02/V05/V06：同Task槽可覆写、旧Task链不可删、来源二选一；未提交当前槽如何切形态薄弱 | 仅显式清当前UID数组且唯一槽属于本Task/未被Snapshot引用，才切合法refs；其它拒绝 | 草稿换形态不删旧Task，WorkingState先筛，source_basis/INSERT用真实Snapshot引用及owner二次校验；往返/恢复/旧Task/旧加新/复用已提交owner拒绝且无副作用，旧不可变row保持，F/L覆盖 | 无审批/结束/来源权限扩张；工程细化仍待用户追认，不伪造用户确认 |
| I-V01误删用户纯文本头 | V12：只清可信项目timestamp/HTML，不泛删用户同形内容；初审原反证实证失败 | 调查producer后确认steer/platform不能证明该JSON头注入；撤回额外Gateway纯文本清理，不新增无依据持久标记或猜测层 | 冻结07未要求删除Gateway纯文本JSON头，撤回恢复原保真边界；亲读修复、原反证源码未改且本复审1过、6新保护例/107回归/132 Linux及源码SHA闭合。真实trusted包装仍清，Read/DB原文保持 | 未变更产品规格；3426修复关闭，应在final-delivery及用户汇报说明误清原因和撤回依据 |
| RPC测试底座 | V24/V27/V37：finish是最后独立工具，父子固定完整工具表 | 原固定额外请求计数改为实际finish响应序号后无更多请求；补全旧terminal-only夹具到真实固定六定义 | 亲读diff和3项正式RPC日志，冻结tools仍逐字比实际表；完整后续Snapshot/原failed记录/当前Main tail/Schedule/Profile/lease断言到达并通过，未改产品finish语义 | 夹具忠于已有契约，非放宽结束条件；不将其它29旧计数/夹具问题一并说已修 |

实质收敛供final-delivery.md及用户最终汇报摘要：前两项Agent工程细化的影响与待追认状态；I-V01撤回无可信来源证明的纯文本剥离以保留用户原文；真实模型样本和当前后继差异的覆盖边界；历史29+15基线失败未修；生产转换与发布尚待执行。

最终判定：**3426c0f本轮本地Verification门禁通过，可进入独立Validation。** 37符合＋1有依据本地不适用，共38项；范围内未关闭违规0、必要证据不足0、新增整改0。不得将本结论作为独立Validation通过、生产上线成功或C01转换完成的证明。本次未修改产品/测试/规格/环境/lock，未提交/推送、未派生、未联网模型、未操作生产/服务/UI；显示保护全程保持。
