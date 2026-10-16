# Hermes Secretary 项目主看板

## 10-16 文档重整（进行中）

用户已审定整份白板，D7 完整 Noting 提示文与 D8 工具细节授权自主收敛。先提交当前仓库现状为重写基线；此次包含此前已存在的显示身份修复与文档变化，不把它们当成本轮新增实现或已重新验证。浏览器临时日志仅本地保存并忽略。接下来重写 07：与白板互补，补齐英文提示、工具 Schema／反馈、Conversation History、架构接线与实施路径；个人 NM 接入独立成文，整理旧文档。授权范围为文档设计，不修改运行实现。

- **10-16 Main Prompt 收紧与 Notebook 工具写法（用户明确）**：K5 Scheduler System Prompt 压成三句话、一个段落，参考现行 Main／Cron 提示的语义分流写法：会话内提醒归 Scheduler，独立定时任务归 Cron；保留即时登记、instant／deferred 与默认至少一个有效 instant 的要求，详细流程留在工具说明，不重复注入。K6 的 changes 按属性提交修改，fields 按键合并，数组直接提交更新后的完整数组，未提供属性保持；补充示例。用户澄清字数和表达仅有提示词软指导，不设写作预算或代码硬限制；已逐类型、逐参数写明一句话总述、简洁属性与完整引用要求，未设置长度数值、maxLength 或截断。白板／07／Noting Prompt 同步；具体文案待审，运行实现未改。

- **10-16 第三章定稿、研讨准入与 Scheduler 删除（用户明确）**：第三章整体七类型方案通过，包括类型语义、各类型属性／状态与 Candidates 组织；D2 转为已确认，具体工具接口仍归 D8。研讨只收用户自己提出或明确认可的内容；读用户回应前后文逐项划定认可范围，不能将模糊确认扩到整段 AI 输出。用户实质尝试回答但未有答案可保留具体未决问题；无人回应、用户关闭或错误的 AI 提问不新建，Noting 不追加问题。Scheduler 对外动作统一为 `delete／删除`，与保留定义的 pause 区分；业务取消与排期删除分别表述。已同步白板 C7／类型详情／N2、K3／K5、D2／D8 与 07；未修改运行工具。

- **10-16 N3 消息结构与 N6 Prompt 补全（用户明确）**：Noting 成功提交后，runtime 将完成通知与本次完整 Notebook 现状正文放入同一条 Framework Message，直接注入 Main 上下文；超限时在该消息末尾追加计数、上限及共用 Persistence Proposal 指令。不能仅通知或发快照 ID 后再要求 Main 读取；完整快照来自提交结果，原始历史仍按需回读。N3 输出结构已确认，D7 只保留失败处理及具体 Prompt 文案待审。已参考 `secretary/noting_child.py` 现行任务指令，为 N6 补全历史仅作证据、父 Main 角色／工具语义与当前 Noting 任务切换、追加授权 Schema、忠实转录与禁止补写、用户认可范围及工具结束要求；不恢复旧 Memo／排期职责。白板与 07 同步，本次仅设计，运行 Prompt、代码和数据未改。 文档检查通过：HTML 闭合、73 张卡片与 ID 唯一、14 章及本地链接有效；四份 Prompt 在 HTML 与 07 中一致，批注存储键保留。未运行产品测试、未提交新版。

- **10-16 N1 审定与 Main 按需回读（用户明确）**：N1 的完整任务输入、六步执行顺序及完成条件已审定。Main 使用 Notebook 时先结合当前任务读相关索引；当前信息足够就继续工作，只有缺少影响判断的具体细节时才沿 provenance 定向 Read／必要时先 Search。快照到达不触发全量历史恢复，依据足够即停止扩展。白板 N1／N0／P6／D7 与 07 §8.11／§9.4 同步；P6 给出 Main 稳定提示草案。N1 从待审项移除，N3 输出结构随后明确，D7 保留失败处理及具体 Prompt 文案；未修改运行 Prompt 或代码。

- **10-16 结算只读取 Conversation 分发轨迹（用户再次明确，E1／E2 批注）**：Noting 的分发证据来自任务冻结父上下文中的对话／工具轨迹，以及 conversation_history 可读的同一 Conversation 过往压缩区间历史。确认获批内容已成功分发即可结算；不使用文件或目标系统工具检查目标是否真正接收、保存了什么或保管质量。E1 改为定位批准与分发→补读缺少历史→按轨迹确认范围→移除已分发部分→修正引用并在结束说明记录结果，删除“内容已由目标承接”的暗示；E2 保留真实分发成功口径。已同步 F1、完整 Noting Prompt 及 07 §2.2／§8.9–8.12；仅文档，未实施。

- **10-16 白板第 07 章整体通过（用户明确）**：用户确认本章方案，包括逐类型处理动作、语义路由及时间参数。普通条目按各类型既定时间依据采用 **7 天**，缺失警示 **72 小时**；达到条件后在下一次完整 Noting 同次执行精简与去留判断。既定 12,000 字符／60 条的整理后提案提示机制保持。白板 L7／L2／L9、类型详情、D5 与 07 §8.5–8.8 已同步为确认；D7 不再待审这些动作；随后 N1 输入、顺序和完成条件亦获审定，N3 输出结构随后明确，剩余失败处理及具体 Prompt 文案待审。该通过指白板第 07 章，不将其他章节或运行实现写成已获授权。

- **10-16 交付边界与结算判据（用户连续两条批注明确）**：Secretary 将映射后的 Notebook 标签与 provenance 作为可交付材料提供给目标即完成该部分职责。目标是否支持、保存或使用这些信息、结算后如何恢复细节，由目标自行决定；个人 NM 的配置不成为公开 Secretary 要求。Noting 只依据用户批准范围和现有对话中的实际写入结果结算，不审计目标内部数据或以缺少标签／provenance 支持为理由否定成功写入。已同步白板 A5／C9／F1／E1／E2／L3／P6、07 §2.2–2.3／§8.9–8.12 与两份相关指令草案；本次仅文档，未改运行实现。

- **10-16 整理后超限主动提案（用户最新确认，覆盖仅限手动提案与旧容量建议）**：删除 L5 到期额外触发压缩建议及分区预算／百分比整理目标；每次 Noting 仍完整执行。有效快照提交后，由 runtime 统计 Notebook 字符数与独立条目数，任一超限就在完成 Framework Message 附上与 /propose-persistence 共用的指令，让 Main 直接提出可审批草稿。实际写入仍必须用户明确批准，提示词与流程保持门禁。用户授权先采用估计值：**12,000 字符／60 个现行条目，任一严格超过**；计入三板块、Candidates 与来源，后续按体验调参。白板 L1／新 L9／L6、07 §8.6–8.9／§9.4 和完整 Noting Prompt 同步；本次只改方案，运行命令指令、Framework 与代码未改。文档检查：HTML 标签、73 个卡片编号与锚点有效；Noting、Main Scheduler、Persistence 三份指令在白板与 07 中分别一致；批注存储键保留，未运行产品测试。

- **10-16 防积压表的对象与语义分支（用户进一步明确）**：保留进入条件、处理时机、本次处理、退出条件等表头；按条目类型直接写清什么信息满足何种条件、具体精简／保留／归档／聚合什么、去往哪里，通用章节展开执行方法，不能代替每类对象的动作选择。白板表格、类型详情、07 §8.5 与 Noting Prompt 已同步；逐类型分支与 7 天／72 小时后来已随白板第 07 章整体通过。文档检查确认 HTML 标签、73 个卡片编号与锚点有效，两份完整 Prompt 分别与 07 一致；未运行产品测试。精简与候选可同时作用于同一条目，源正文继续原位保留；未改运行实现、未提交。

- **10-16 更新、防积压处理与具体 AI 指令（用户连续澄清）**：审计与更新负责条目的时效和正确性；过滤与候选阶段负责防止积压。处理表明确写“处理时机”和具体动作，精简与保留／归档／候选判断在同一次完成，不拆成 7 天／14 天两阶段。用户要求写入项目规则的是“机制中如何指示 AI 行动必须具体”，已写入 AGENTS；已撤回误写的统一机制设计模板。白板／07／Noting Prompt 已同步职责边界；7 天、72 小时后来已随第 07 章通过。将含糊“复核”拆回内容更新、去留判断与按具体缺失事实读取原文；按具体缺失事实取证的动作后来已随第 07 章通过，未实施。

- **10-16 Notebook Maintain 工具重审（名称与问题由用户提出，具体方案待审）**：用户指定 notebook_maintain，要求重审去掉 Schedule 后是否仍需分层，并吸收 Noting Memo 补丁与 Notebook 状态／Schedule 耦合两项教训。白板 K6 与 07 §9.5 提出两个 Notebook 工具（show／maintain），连同 conversation_history、finish_noting 共四个 Noting 授权工具；maintain 仅 create／update／archive，状态与内容同次更新。新增待审设计包括稳定 entry_id＋不可变 version_id、单条增量返回、结构校验与证据驱动状态修正。既有独立所有权方向明确落为取消双向状态副作用；Main 在业务变化时判断并调用 Scheduler，Noting 读取正常证据。已同步两份 Prompt、K7、A7 与 D8；仅设计，未实施。

- **10-16 Conversation History 工具更名与设计对齐（用户明确）**：已读取下载目录 2026-10-16 独立设计稿的 History 契约及提示指导，白板 K1／P6／N6 与 07 §9.5／§8.12 改为 conversation_history。Main 默认当前 Conversation，可显式选择同 Profile 内获授权用户 Conversation；Noting 仅绑定父 Conversation，实际 dispatch 拒绝跨会话。Search 定位命中原文邻域，Read 沿 (conversation_ref, message_uid) 读原文及邻近消息；原生 session_search 保留物理执行记录职责。仅纳入 History 设计，不导入 NM 专属语义；参数拼写等仍沿来源稿标为建议，未改运行实现或旧数据，不安排数据迁移。

- **10-16 C5／C6 审阅确认**：删除旧标签到新结构的映射，旧分类已废弃，不纳入新规格，也不安排已有数据迁移；其工作场景转为 Main／Noting Prompt 的简短行为示例。用户认可 C6：候选采用聚合引用，源正文原位保留并随新证据更新；Noting 同步复核关联候选，Main 提案前回读，实质变更重新取得对应批准，结算只处理真实成功覆盖部分。白板 C6 已标为确认，07 §5.2／§8.8 及两份 Prompt 已同步。当前仅设计修订，未修改运行 Prompt、代码或数据。

- **10-16 O3 信息流展示修订（用户确认）**：卡片顺序直接表达单条信息的生命周期，同时作为机制章节入口；步骤 1–5 与章节 05–09 分开标注，主图以箭头串联，持续维护、直接归档及原文直达候选作为明确分支展示，不把生命周期缩为脚注。已同步白板与 07 §5.5；本次不改变业务语义或运行实现。

- **10-16 Scheduler 独立控制（用户最新确认）**：Scheduler 作为独立工具组注册、单独控制，控制权与维护职责归 Main，不再和 Noting 开关绑定；该项由 D8 待审建议转为已确认。Scheduler 负责将内容按时投递回所属 Conversation，Cron 负责独立 Session 定时执行任务；共享 Hermes 时间语义，分别维护控制面。Noting 保持会话内渐进式状态／索引维护与会话外候选／交接结算两项职责。已同步 K7／K8、Main Prompt 与 07；具体字段仍待审，未实施。

- **10-16 工具控制面与 Scheduler（用户新增确认，已纳入本轮待审设计）**：Scheduler 直接提供给 Main，与 Notebook 语义标签解耦；投递内容的业务语义由 Main 决定，工具只区分 instant／deferred 两种投递方式。排期沿用 Hermes Cron 时间控制语义，继续按 Conversation 隔离，到期直接投递所属 Main；Main 通过 scheduler list 理解和维护当前 Conversation 的 Schedule Table。默认自主运行要求：除非用户明确要求关闭，Main 至少保持一个有效 instant reminder；暂只由 System Prompt 与流程约束，不增加代码层兜底、不自动补建。白板 04／K1–K8 与 07 §9.1、§9.5 已写明动作、字段、Table、投递、Main Prompt、Notebook／History 权限与结束控制；接口及开关细节仍待 D8 审定，未授权运行实现。

- **10-16 白板机制目录与删除 Noting memo（用户最新确认，已同步白板与 07）**：索引建立与依据新对话证据审计、更新现有索引必须分开论述；信息流总览同时作为具体机制章节入口，统一卡片样式，先机制后完整场景并更新场景。Persistence 的提案、用户审批、实际分发是由用户 `/propose-persistence` 启动的连续过程，合为一个机制与独立章节；该条“仅用户命令启动”已被后续整理后超限主动提案决定覆盖；实际写入仍须用户明确批准。新版彻底删除 Noting memo，不保留 Main→Memo→Noting 的动作出口或替代便签通道；动作归正式 Main／Scheduler／Persistence 流程，Noting 从对话证据维护 Notebook。白板会议批注是设计审阅界面，与被删除的产品机制无关。当前仅修改白板与 07 设计，现行运行实现尚未变更。

- **10-16 两阶段清退与双重职责（用户新增确认，O3 批注；已同步完整待审方案）**：Notebook／Noting 一方面为 Conversation 提供渐进式上下文状态管理，以工作状态、索引与 provenance 支持多次 compaction 后恢复重要细节；另一方面构成本 Conversation 信息通往 Memory／Skill／Rule 等持久化目标的提案起点、用户批准门禁与分发流程。在候选处理点，Noting 按各板块语义／时间／容量规则过滤：不再需要且无持久化价值的条目直接归档退出，其余映射、聚合成候选并保留原位源正文；D4 已确认。Main 提案、取得明确批准并实际写入后，后续 Noting 核对已 dispatch 的结果，在结算处理点移除对应源条目和候选。直接归档不建立空候选、不另建短期恢复通道；尚待审批的候选积压治理仍后置。两阶段是条目生命周期处理点，不是两种 Noting 任务。用户进一步明确：一次 Noting Task 必须承担全部工作，包括最初索引建立；白板必须给出完整任务流程、执行顺序、输入输出、失败处理及重新调优后的 System Message Prompt 草案，不能后置成空白。当前 v2.2 将 O3 改为五项机制章节目录：索引建立、证据审计维护、过滤候选、命令启动的 Persistence、分发后结算；每项说明 owner、输入输出与独立章节。N0–N6 给出单任务六步草案（先审计，再建立），包含完整 Noting Prompt。工具控制面及 Main Scheduler Prompt 纳入 K1–K8；场景移至机制之后并按本版重写。新版未提交，未修改运行 Prompt、产品代码或真实记忆。

- **10-16 Notebook 白板重写（文档已收敛为完整待审方案，未实施）**：用户要求先提交旧白板，再收敛分类、属性、Noting 维护标准、容量与每类型“何时执行”的进退机制。旧 HTML 快照已提交并自动推送 origin/main：69f9b1ab411e95ccd19559bdb102337e00717674，该提交只含白板。当前原白板已重写为正式方案 v2.2，共 14 章；07 §1.3／§5.5／§8／§9 同步；新版留在工作区供审阅。C4 分类与属性设计指导已认可；第三章七类型及属性／状态随后获整体确认，第 07 章处理参数亦已通过；工具接口仍待审。入口见 README；不改变 02 现行运行契约。

- **Notebook 最新归属与职责（用户已确认）**：采用“Conversation 内部记忆／会话外记忆体系”区分；会话内记忆可以长期存在，也不等于用户全部短期记忆。公开 Secretary 维护当前 Conversation 的工作状态、历史细节索引及跨 compaction 连续性，Persistence 负责获批交接流程。Hermes 原生记忆或用户选择的 Memory Provider 承接后自行治理；NM 只是用户个人 Provider，不引入其专属语义、接口和治理要求。个人情况、关系、经历、认识都可提议保存，Memory 不套用 Skill／Rule 的普适可复用标准。Secretary 的统筹定位及“让用户忘记 Session 管理”的愿景保持；用户不承担日常分类、归档和压缩交接。

- **Candidates 双来源与正文原位保留（用户最终确认，覆盖旧搬家方案）**：三板块准备清退的内容先过滤；无当前用途且无持久化价值的直接归档，值得持久化的再映射与聚合；Candidate 保持简约 description，新增 Notebook 现行条目引用，保留 Messages provenance，并继续允许直接从原文提炼候选。可混合来源，可合并则合并；源条目留在原板块，不二次转写正文。用户明确批准且实际写入确认后，处理源条目与 Candidate 的移除。批准要求用提示词和流程保证，不新增专用代码门禁；积压治理、每日集中提案和强制超限政策后置。已分发内容退出后由目标体系召回；直接归档内容不继续作为可召回记忆保留。不新增旧 Snapshot／已退出 Notebook 的找回通道；来源原文仍是证据。

- **类型标签及缺失警示（用户最终确认）**：Notebook 第二板块允许情景与专门缺失警示并列，警示关联情景。清退前先查补足或失效证据：已补足的答案、导致失效的已知变化补入情景；旧警示不再作为当前缺口呈现，仍未知只保留理解所必需的最少部分。进入候选阶段与对应情景合并，统一 situation 标签，独立 implicit_gap 标签不继续深入目标记忆；来源引用仍可追溯原警示。其他 Notebook 来源类型经 Candidate、获批提案一路保留到目标记忆。用户研讨的问题、认识、决定须有用户表达或明确认可来源，模型缺口或猜测不混入。早期“第二板块仅一标签”“Candidate 与源正文互斥”均已被这一最终设计覆盖。

- **联合机制与完成注入（用户已确认）**：Noting 总开关开启联合机制，普通路径同时触发并行执行；Force 因较大空间需求提前 Noting，后续 compaction 与其对应，不重复启动。Idle 子开关只在总开后可用，由空闲延迟与上下文规模双阈值自动发起联合流程，以利用热缓存；保持与原生“空闲回归后自动 compact”互斥。总开关闭走原生，现有快照获取机制不变。Noting 提交有效快照并结束后，结束通知与本次快照一起通过 Framework Message 注入 Main；compaction 不等待，用户接受连续工作时晚到新的区间。覆盖此前“随 Compact Message 同步携带本次快照”的设想。正式 payload、并发与失败接线未实施。

- **提醒职责与主动性（用户已确认，具体 Prompt 已纳入本版待审）**：需要未来可靠提起的事项由 Main 当场登记，运行时负责 instant／deferred 投递；新 Notebook 不继承 Noting 补充提醒注册机制，缺失警示不产生 Schedule。Main System Prompt 默认至少维持一个有效 instant reminder，除非用户明确要求关闭；K5 已提出检查、补位、替换与失败处理草稿，控制面见 K1–K8。暂不以代码保证，本轮不新建实际提醒。

- **设计依据与文档地位**：本轮研究包含 Palantir Ontology、分类／协作理论及 coding agent 初始化、维护、加载实践，来源保留于白板／07。用户提供的独立稿中 Conversation History 设计已按本次明确要求纳入目标方案；NM 部分仅作研究输入，未授权运行接入或改造。新 07 是重设计入口；原 07 清理提案与原 08 文案／提醒提案已去编号为两个 proposal 文件，保留历史讨论、不覆盖现行规格。当前仅文档／白板工作；未改产品配置、数据库、活动 Notebook 或 NM，未运行模型实验或产品测试。 本次已核对 HTML 标签闭合、14 章目录／面板顺序、卡片编号、唯一 ID 及本地链接，均无问题；白板与 07 的完整 Noting Prompt、Main Scheduler Prompt 正文一致。浏览器已加载 v2.2，实际显示五项机制目录与 K8 Scheduler／Cron 对照；截图 `.hermes-dev/notebook-whiteboard-v2.2.png`。原批注存储键保持；新版尚未提交，未运行产品测试或模型实验。

- **10-15 Noting 成本分析（仅分析）**：用户确认初始 50K、压缩回约 70K、窗口 256K；单次增量 30K／50K／80K，只比较窗口放得下的完整 6／4／2 次使用，不计之后原生压缩。比较完全不开 Noting、每次 Noting+阈值 compact、仅阈值 Noting+compact；冻结前缀计费，Force 纳入 500 秒组。推导、数据来源、K3 单价及估计限制见 `docs/05-context-cost-ledger.md`「2026-10-15 Round Two Noting 成本模型」。当前样本价格换算模型无严格省钱 p，不代表 K3 实测或长期使用结论；未改运行配置／代码、未运行测试。

## 自主口径收敛 · 待用户追认

> 本区域按 AGENTS.md 永久维护；无待追认收敛时注明“暂无”。

**10-16 Notebook 正式方案待拍板（Agent 提案，未实施）**：D2 已随第三章整体通过，七类型的属性、行动状态与候选组织按本版定稿；D3 已按用户授权采用 12,000 字符／60 条的整理后提案提示上限；D5 已随第 07 章通过，7 天／72 小时及逐类型动作与语义路由已确认；N1 的输入、六步顺序及完成条件已审定；N3 的同条消息完整快照注入与超限 Proposal 尾部已确认；D7 仅待审失败处理、完整 Noting Prompt 与 Main Notebook 按需读取提示文案；D8 为 notebook_maintain 三动作、增量返回、稳定条目身份／不可变版本及状态校验范围；按属性更新、数组全值替换和字数仅用软指导已明确，具体字段文案仍待审；Scheduler 字段与 Table、独立控制配置、统一 finish_noting，以及 Main 检查／补位／业务变化流程；delete 删除名称与语义已确认。除已确认的 D2／第三章、已采用的 D3 初始上限、已通过的 D5／第 07 章、N1 及 N3 输出结构外，上述方案细节待审；未增加 runtime 读取过滤、独立 Noting 定时器或自动删除。超限提示已纳入本版；长期积压处置后置，不承诺审批停滞时占用始终低于提示线。详情集中于白板第 13 章及 07 §8.14，其余未审定方案不能写成用户已确认。D4 的过滤时直接归档已获用户确认，已移出待拍板项。

2026-10-14 第二轮收尾后用户拍板口径（新会话交接必读）：

- **Rewind active 禁用（用户拍板，实施中）**：Turn active 时直接禁用编辑入口，不做 active 编辑事务；V-R2-02 按此口径收敛，不再是待修复杂事务。
- **模型行为路径问题降级关闭**：FV-F05（tool_call/terminal/schedule_cancel 误用）、PDF 漏读/临时 PNG 定性为“白名单挡得住即可”，不追 Prompt/语义层修复。
- **Prompt 历史结论与新议题**：10-14 当时 Prompt 议题关闭；10-15 Main M2／M3 已审定，仅文档 Target 未实施。用户要求回退 02 的 Noting 调优增量，相关文案及提醒结构设计独立保存在 `docs/noting-message-and-reminder-contract-proposal.md`（原 08）；Noting Message 仍待审，设计确认不代表授权实施。
- **10-14 流式体感历史结论**：当时用户确认响应速度跟得上、未观察到明显上限；10-15 真实录屏暴露动态投影重复、缺段和滚动异常，已重新打开修复，不能以静态结果正确判定流式过程正确。
- **附件实测缺口**：新名 RPC（file.upload_chunk/upload_abort/attachment_info）前端已接线（aacb6e9），仅缺新路径端到端实测——按用户口径仅记录为风险点，不补跑。
- **10-14 修复记录（已完成未提交，以下三项均前端，用户指示不提交）**：① TeX 数学公式渲染（remark-math + rehype-katex + katex，含 realText 第二渲染路径）；② 工具卡片运行期问题族（tool.complete 不再 push Unknown 影子卡改为就地更新；applyTool 退化吸收唯一 constructing 占位卡；旧路径 tool.start 只吸收一张同名构建卡修并行误删）；③ active 态 Reply 禁用入口（liveActive 穿透 memo 链）。tsc/build 通过；440 测试 431 过，9 挂与基线完全一致（8 个 presentation 既有 + 1 个 Usage 既有）。

## 过时文档警示（严格标注，不能反映当前状态）

以下文档的部分或全部内容已过时，引用前必须核对当前正式版本（后端 `d276ea8b60`、前端 `9e3566c83`）：

| 文档 | 过时内容 | 当前事实 |
|---|---|---|
| `verification.md`（首轮 Verification，10-13） | V-R2-05“assistant-ui 只作外壳”；V-R2-01“前端未接线”；“不通过”整体结论 | aacb6e9 已完成 assistant-ui 深度集成；前端已接新名 RPC；“不通过”针对 c55120f/002f7a2，未复审 |
| `repair-attachment-rpc.md` | “前端未接线，V-R2-01 尚未整体关闭” | 前端 aacb6e9 已接线；仅缺实测（风险点） |
| `plan.md` | V-R2-01~04“待初审集中安排”状态表 | 已被后续实施覆盖 |
| `repair-timeline-latency.md` | V-R2 系列整改方案表 | 框架深度集成已完成；工具卡片运行期归并修复中 |
| `validation.md`（10-14 收尾） | 初始版本引用 BE ea2ab/FE 833ef | 当前正式 d276ea8b60/9e3566c83；其缺陷记录与未覆盖清单仍有效 |
| `final-delivery.md` | “云端复查未回”交接时点表述 | 以本看板为准 |
| 各 owner 报告（frontend-report、native-compatibility、repair-*、clarify-ui-implementation 等） | 反映各自提交时点状态 | 引用须核版本，不作现状依据 |
| `user-intent-evolution.md` | 历史口径审计 | 仅作历史导航，非现状依据 |

## 当前产品级状态（2026-10-15）

- **10-15 ISSUE-013 失败归因与流式回归修复（已完成，未提交）**：用户要求逐项说明此前 11 个失败，先判定本次修改引入的回归，再修复流式相关问题。主会话在 ignored `.hermes-dev/flow-regression-audit-20261015/before` 建隔离副本，仅撤销本聊天上一轮生产代码修改、保留此前其他未提交实现，测试保持相同；未在正式热更新工作区回滚补丁。基线重建的生产文件哈希已核对，比较与完整日志见该目录 `manifest.json`、`comparison.json`、`before-report.json`、`current-report.json`。
  - **归因证据**：相同 49 项，补丁前 35 过／14 失败，首次流式修复后 38 过／11 失败；原 11 项全部共同失败，新增回归 **0**。额外修复前失败的 3 项是新增 paired 正文／推理合并及终态拒绝草稿测试。此前未实测的“既有”判断现已有隔离对照证据，不再只靠代码推断。
  - **原 11 项明细**：① legacy 103 帧缺身份链路出现构建占位＋真实调用两卡，属真实缺陷，已修；② 同一 Assistant 重复 generating 被旧断言视为独立调用，断言过时，同时补修无调用段 commit 时影子 phase 残留；③ 正常 commit 后调用 UID／活跃退休，④ no-history，⑤ empty-history-calls，⑥ hidden-history，⑦ invalid-history-calls，⑧ incomplete-history-calls，⑨ other-uid，⑩ other-scope，八项都混淆了“调用身份已证明”和“结果已证明”，已按现行 06 补强测试，仍禁止凭未证明结果标完成；⑪ Usage fixture 缺 stored_session_id／正式计数字段，补合法 DTO 与 REST 回退 fixture，生产身份校验不变。
  - **实际修复**：未识别构建通知只代表一个阶段，旧链路仅收敛同 Turn 连续尾部无身份 phase；有身份时严格按 scope／Conversation／Turn／Assistant owner 收敛并更新，真实 UID 到达后替换自己的 phase，其他 owner 和真实调用不受影响。新增先见红用例发现 provider ID 复用会碰撞前端节点 ID，已改为以原生 occurrence UID 分配独立新槽位；后端 `mint_uid()` 为 UUID4 fresh durable identity。乱序完成分别更新真实结果，不按名称猜身份。Astra/high 已基于主会话交付证据进行方案逻辑 review，UID 前提由主会话核实。
  - **扩大接线检查**：另发现 4 项在隔离补丁前也失败：3 项按结果到达顺序而非冻结调用段顺序排序的旧断言；1 项 Notebook 用例的活跃节点应为空断言过时，移除遮挡后暴露真实锚点偏移。已保留活跃槽位，并在调用临时命令时保存生成阶段的 Assistant UID 边界，防止占位升级后被未来 tool result 重锚。此为浏览器临时边界标量，不改原文、数据库或后端队列。原始历史 fixture 未修改，不跳过测试、不放松校验。
  - **最终验证**：相关 10 文件 **293 过／0 失败**，3.37s；覆盖原 11 项、额外 4 项、调用 UID／结果乱序、跨 Turn 隔离、正式 Controller／Timeline、Notebook 顺序、Usage 来源、原生 writer/DB fixtures 及按帧合并／Steer 收据。类型检查、两仓差异格式检查通过。主会话按本轮初始快照亲自 review，独立增量见 `followup.patch`；最终报告 `final-regression-report.json`，归因摘要 `summary.json`。本轮未重跑模型联调；此前速度联调结果按其原版本保留，不能冒称本轮重新测量。未提交，保留其他未提交工作。

- **10-15 Notebook 文档拆分（已完成／全部未实施）**：用户要求撤回 02 中本轮 Noting Message 相关改动，将现有提案独立成文。已将 Noting 压缩稿、类型语义澄清、提醒来源／不可变字段及 Schema JSON Patch、token 统计和未来案例迁至 `docs/noting-message-and-reminder-contract-proposal.md`（当时编号 08）；明确已确认设计与待审文案，均不覆盖 02 现行契约。02 §2.5 恢复本轮前版本，删除 §5.12.0 与提醒 Schema 3.6a 增量；现行 Noting／continuation／工具 Schema 原文保持不变。只在 02 §5.12 entry 1.2 Target 写入用户已审定 Main M2／M3 两行，M1 不进入 Main。README 已补独立提案入口；02 中另一讨论的 §1.7 索引目的、§3.8 Schedule 待议澄清及其他未提交工作保留。原 08（现无编号文案提案）第 4 节保持迁移时压缩正文（原版粗估 998／草案 1358，增 360），未静默合入尚待定稿的精简建议。仅文档整理，未改代码、运行 Schema、配置或活动 Notebook，未运行模型／测试／构建，未重启／提交。

- **10-15 Steer 延迟／terminal_conflict（ISSUE-013，修复并完成真实联调，未提交）**：用户要求对照模型输出与前端流式速度，主会话在原故障聊天、原 53445／5173、同 round2 profile 实测。根因是新增 `message.output_delta` 身份配对事件未纳入 RenderStore 按帧合并，每条配对立即 flush，打穿 legacy delta 的合并并饿死事件消费／输入；没有证据把网络认定为主因。纯正文／推理 identity delta 现与 legacy 一起合并画面，权威状态仍逐条同步处理，interim／控制／终态立即发布。用户要求 Astra/high 研讨；已直接交付完整上下文、禁止其探索取证，完成两轮讨论并由主会话 review：保持最小调度修复，不增队列、固定节流或拆 Composer；真实结束竞争仍拒绝且保留草稿，提示改为清楚的结束原因。
  - **真实证据**：修复前 200 行表格约 5,307 字符，后端 17:41:43.459 结束，前端至 17:42:13.638 仍消费旧 delta、动作 Stop，积压至少 30 秒；其后为加载修复主动刷新，未测得基线最终排空耗时。最长事件循环停顿 7.612 秒。修复后同 200 行／约 5,304 字符，后端 17:43:00.719 结束，测试客户端 17:43:00.942 处理结束事件、17:43:01.033 绘制检查已为 Send（约 314ms）；另一客户端约 209ms。实际 Steer 17:42:58.993 发出、17:42:59.065 accepted/pending（72ms），按原生无工具插入点的正常规则进入一个 followup，页面最终显示 `FLOW_STEER_RECEIVED`、空闲 Send、草稿清空。证据仅代表本次样本，不承诺所有机器／长度的绝对上限。
  - **修改／验证**：前端 `core/render-store.ts` 集中纯渲染事件分类，`core/controller.ts` 接入及结束拒绝提示；`verification-fixes.test.tsx` 补完整身份配对的正文／推理、同步状态、控制／终态清除待排帧、拒绝草稿保留及无 Prompt fallback。`native-output.ts` 一处可选链修复既有 TypeScript 空值收窄报错，无行为变化。最终定向回归 15 过／0 失败（含真实 native writer/DB fixture 11 项）；最终版本类型检查与两仓差异格式检查均通过。此前扩大相关 3 文件检查为 48 项 37 过／11 失败（纯 native-output 投影 10、Usage identity 1），不宣称全绿，也未将未实测的历史归因写成确定基线；完整输出 `.hermes-dev/flow-related-tests.json`。原始无正文计时 `.hermes-dev/flow-timing.jsonl`，摘要 `.hermes-dev/flow-timing-summary.json`；临时探针及 Vite 中间件已移除。保留两仓其他未提交修改，后端未修改／重启，未提交。

- **10-15 Timeline 底部留白（用户最终指定 64px，已修改未提交）**：底部 padding／scroll-padding-bottom 统一为 64px，替代此前试调的 52px。仅改前端样式，未改变跟随逻辑；同步 06 §1.4。差异格式检查，未运行测试／类型检查／构建或浏览器验收，待用户查看。
- **10-15 Notebook 时间标签（用户确认，已修改未提交）**：前端 `/notebook` 临时卡片将 `Created at` 改为 `Updated at`；时间值继续来自后端原生人类输出的 Snapshot `Created at`，不改原生响应字段、存储或时间语义。已同步 06 §1.4；未运行测试／类型检查／构建或浏览器验收。
- **10-15 后台／子 Agent 完成通知卡片（ISSUE-012，已实现待用户复测，未提交）**：按现有 `display_kind=process_complete`／`async_delegation_complete` 显示独立、默认折叠且可展开的通知卡片，主题复用 Framework Message，标题精确为 `process complete`／`async delegation complete`。前端赋予独立通知 kind 与 system 角色，不识别为 User Message，不使用用户动作栏／附件解析，不提供 Reply／编辑；后端 role、正文、数据库不改。Framework 包装和 `noting_run_output` 优先保留，Noting Framework Message 展示不变；工具归并仍按原生 source 输入边界分隔。历史／实时共享投影、正式组件及编辑入口已接线，同步 06 §1.4、README 与前端 ISSUES。已做源码 review 和差异格式检查；沿用用户亲自复测安排，未运行测试／类型检查／构建或浏览器验收，本次主会话直接实现、不提交。
- **10-15 Turn 结束跳变（ISSUE-011，已修改待用户复测）**：用户确认此前修复均正常生效，追加 `屏幕录制 2026-10-15 at 17.10.42.mp4`。主会话逐帧捕捉约 11.27–11.78 秒视口显示旧的 17:07 sleep 对比表，随后恢复当前回答。定位到 active 结束批量插回历史用户消息的 Reply 操作栏、累加列表高度，同时后台历史加载阻断滚动维护。已让用户消息操作栏始终保留占位（active 仍隐藏编辑按钮），并将加载等待限定于初次定位，后台刷新继续遵守原跟随/手动暂停/分页锚定所有权；active 切换也同步维护布局。仅改前端，用户继续录屏复测；未派 Agent、未运行测试/类型检查/构建或浏览器验收，未提交。
- **10-15 GPT Subscription 与摘要分段（用户确认）**：`openai-codex` Provider 使用 ChatGPT／Codex OAuth 订阅认证，走 `codex_responses`／Responses API；摘要请求、流式传输及 `summary_index` 变化时插入 `\n\n` 的分段直接复用 Hermes。前端顺序拼接并正常渲染 Markdown、保留原空行，无需额外补换行，不按每次回调强行分段。已同步 06 §1.4、前端 ISSUE-009；仅确认该 Responses 路径，不泛化至所有第三方接口。证据为源码核对，未发起真实订阅请求；本次仅更新文档，未修改代码、运行测试或提交。
- **10-15 列表标记缺失（ISSUE-010，用户已确认此前修复生效）**：用户报告无序/有序/多级列表仅有缩进无标记；确认 Tailwind preflight 清除 list-style 后主题未恢复。主会话直接在前端 `src/design/theme.css` 的 `.hs-prose` 范围恢复 disc/circle/square 与 decimal，保留原缩进、原生起始序号和子列表计数；公式已获用户确认正常，未改公式。按既有要求不派 Agent、不运行验收、不提交。
- **10-15 视口存储澄清（已确认）**：不持久化视口/滚动状态，每次刷新回到 Timeline 底部；已移除滚动 hook 的 localStorage 读写，手动暂停与 20 秒恢复计时仅保留页面内存。
- **10-15 滚动最终澄清／执行方式**：用户主动 Timeline scroll（不分方向）后暂停被动跟随；普通流式追加不推动视口，保持用户指定高度；手动控制结束 20 秒后且当前仍 active 时回底恢复；再次手动滚动重计时。只有用户 Send 被接受会立即回底，不能把 Reminder 等所有新 Turn 都作为回底触发。更早历史必须按钮加载，每次 200 条，插入后补偿新增高度并保持原可见内容锚定，禁止闪动错位。用户要求后续由主会话亲自操作，不再派 6.1；既有两位子 Agent 已交回，剩余修改由主会话直接完成。已同步 06 §1.5。
- **10-15 Thinking 展示口径（用户确认）**：保持现有推理文本／摘要流式展示，取消前端 ISSUE-009“加密思维链模型隐藏流式内容、改为固定文案”的要求；不因 GPT 原始思维链不透明而屏蔽上游可见摘要。保留流式时展开、完成后自动折叠及手动展开交互，不为该已取消需求新增加密识别或接口。已同步 06 §1.4、前端 ISSUES.md；其他 Thinking 打断、缺段和闪烁缺陷仍按既有任务修复。本次仅更新文档，未修改代码、运行测试或提交。
- **10-15 并行工具卡澄清（已确认，立即纳入实施）**：并行 N 个调用对应 N 张独立卡；识别完整工具段时按真实顺序全部展示，之后各卡按真实状态及时原位更新，身份和位置顺序稳定，不按开始/完成事件到达顺序重排。不是整组并行调用共用一张卡。已同步 06 §1.5。
- **10-15 录屏动态渲染修复（用户确认此前修复生效，结束跳变另见 ISSUE-011，未提交）**：用户提供 `屏幕录制 2026-10-15 at 16.33.25.mp4`，确认首次同一次工具调用出现 Success/Running 两卡，过程中四工具卡在 Turn 结束静态对账后恢复三卡，期间 Thinking 缺段/状态异常及跟随中断也存在。明确要求立即一起修复；保持一次真实调用一张卡原位更新、各段独立结束、动态到静态数量/顺序/内容连续。新 Send 被原生接受后回底恢复跟随；主动阅读历史不被后续输出拉走，按最新澄清实现手动控制结束 20 秒后、当时仍 active 才回底恢复，其他新 Turn 不触发立即回底。两位子 Agent 的动态投影/滚动 hook 初稿已交回，主会话亲自完成最终滚动口径、并行工具静态槽位、后端元数据与正式接线的修改和 review；**用户亲自使用相同方法复测，明确无需 Agent 验证，本次不跑模型、浏览器验收或测试，不提交**。
- **正式版本**：后端 `b4a20788c6`（main，已推 origin/main）；前端 `9e3566c83`（main = origin/secretary，工作区含未提交修复与新功能）。
- **运行入口**：后端 53445（round2 profile `.hermes-dev/round2-runtime`，PID 94335，10-15 本次已通过空闲检查及原生 retirement fence 后重启，加载完整工具段事件增量）；前端 5173（vite dev，`hermes-secretary-web` 仓库，热更新生效）。
- **10-15 配置变更（用户明确指示）**：`noting.idle_delay_seconds` 2→**500**；`noting.auto_trigger_compaction_after_noting.threshold_tokens`→**160000**（enabled 仍为 false，未触发特殊路径）。均已 live 生效。
- **10-15 新实现（用户明确要求的产品）**：① assistant 消息复制按钮（hover 显现；移动端/无 hover 单击消息区域 toggle 显现；复制该条正文原文 markdown 源；design/chat.tsx、App.tsx、design/theme.css）；② user message 内嵌 image 从文件图标改为实际预览图渲染（`App.tsx` HistoryImage 独立 img + `attachmentImageUrl` 走 `/api/fs/download` 授权加载内联 data URL 或 path 引用图；CSS `.hs-message-image` 上限 max-width/max-height 22rem 等比缩放）；③ display math 修复与口径（ISSUE-005/006）：多行 `$$` 块修复（`splitDisplayMathClosers` 拆行 + `foldMathMeta` 折叠 meta 并修补 `data.hChildren` 盖章副本）+ 公式块禁止换行改为滚动（`.katex-display` overflow + nowrap）。typecheck 通过，440 测试 431 过、9 挂与基线一致。
- **10-15 新问题登记**：前端仓库建 `ISSUES.md`，登记 ISSUE-001（工具卡片流式过程仍两张 success 卡，昨晚修复未覆盖 start×output 交叉路径）、ISSUE-002（compact 成功后误报 `session.compress timed out; outcome is unknown`）、ISSUE-003（Secretary Orb 展开面板有/无倒计时状态视觉不一致）、ISSUE-004（Thinking 打断显示 Unknown 而非 Interrupted，已定位 `finishOutputNode` 标 unknown 未区分打断）；ISSUE-005/006 已修复待用户确认。
- **整轮状态**：第二轮本地收尾完成；静态 Verification 交云端复查未回，整轮无最终 PASS。未覆盖边界以 validation.md §6 为准（该清单仍有效）：首次 200 分页、IME、最大上传实测、Settings/媒体播放、approval deny、Force 精确 selector、并发族。
- **产品缺口清单**：10-14 P1 = TeX 渲染 + 工具卡片运行期归并；P2 = active Reply 禁用；风险点 = 附件新路径实测。模型行为/Prompt 议题关闭；10-15 动态流式缺陷按上述录屏修复任务重新打开。

## 历史轮次入口

| 轮次 | 稳定入口 |
|---|---|
| V1 首轮 | `.autonomous/20261007-v1-first-implementation/final-delivery.md` |
| V1.5 | `.autonomous/20261008-v1.5-adjustment-and-acceptance/index.md` |
| V1.6 | `.autonomous/20261011-v1.6-implementation/continuation-guide.md` |
| 第二轮 | `.autonomous/20261012-round2-web-ui/snapshot-index.md`（口径）· `validation.md`（验收，版本见警示） |

现行契约顺序：02（Noting 系统，含 V1.6/§5.12 Target）→ 04（增量）→ 01（继承）→ 06（Web UI V1，权威增量）。新 `docs/07-scheduler-notebook-noting-compaction-redesign.md` 是下一阶段重设计依据与规格设计入口，具体实现尚未冻结；05 为上下文成本台账。原 07 清理提案、原 08 文案／提醒提案已去编号为两个 `*-proposal.md`，只保留历史设计，不覆盖现行契约；详见 README 索引和新 07 历史编号对照。
