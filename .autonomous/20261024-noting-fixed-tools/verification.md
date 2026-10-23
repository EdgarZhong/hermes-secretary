# Verification：20261024-noting-fixed-tools

## 1. 审查对象与结论概览

以下首段为初审原时点记录；当前结论以其后的“全新独立复审当前汇总”及第3节新矩阵为准。

审查者：独立 Verification（新上下文；不派生）。判据建立：2026-10-24。冻结基线 `56b7ebc01131ea4eaad0a4690c0bfbab048c2803`，授权追加 `3ce7517dc7c4e6dbdae7de1607032c8281ff0e24`；定位见同目录 snapshot-index.md、baseline.txt、user-request.md。待审 Core `4f503a22ca804b63717fda1104b6146420b525df`（产品与f841170一致）、Web `589df02706d3c6738789ff97fcb652a0bf76c398`。范围C01–C11；独立判据32条（初始28条＋交付闭包覆盖补录4条）；当前初审门禁不通过：32条中24符合、3有依据不适用、1违规、4证据不足。F01拒绝反馈契约违规及真实完整Idle/四工具/N46与最终收尾证据尚未齐备。生产部署尚未发生，本审查区分发布前符合性与发布后Validation。

**全新独立复审当前汇总（2026-10-24）：门禁通过。** 新审查者 `/root/fixed_tools_reverification`，先原文判据落盘后调查；待审 Core `1ea38ef16addaac2cb441029e38f07578d3738dd`、Web `589df02706d3c6738789ff97fcb652a0bf76c398`。本次C01–C11全范围11条全部符合（C08为发布前机制与能力符合性），无违规／必要证据不足；原F01拒绝回执和R01真实工具／Idle链路证据缺口均已关闭。N46实际长前缀、默认Task正常短链及单列显式Show控制分支均有真实原件和独立核验。初审32条及4f503a2时点事实完整保留，不与本次数量混计。生产部署没有发生；此PASS允许进入独立Validation，不代表最终用户验收或已上线，部署后真实运行／数据保护仍须核验。

## 2. 独立要求清单与覆盖

以下28条在读取实现、测试、动态看板或实现报告前独立建立。依据为指定版本用户原话、07（2026-10-24修订优先）、白板语义及06今日修订、部署SOP；索引只用于定位。07既有动态Schema口径由本轮用户明确替代，其它业务及原生不变量保留。C编号仅追溯授权，V编号是独立判据。弱细节处：可信身份的具体接线、旧pin构造边界、前缀wire作用域须据不变量反证，不能因规格未指定函数名而放过绕路。判据之后不依据实现降低。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| V01 | C01；需求1；07修订、§4.3/4.5 | 机制/全局Noting合格Main | 直接要求／必要保持：原Schema、description、参数及Provider转换保持；只改变注册位置 | 两canonical定义逐字段相等；无Provider转换改写 | §3 V01 |
| V02 | C01；07修订、§8.2 | 机制/工具发现 | 直接要求／必要保持：完整定义固定API顶层，禁止Tool Search折叠或消息级动态声明 | 实际Main/child请求顶层含两工具；messages[*].tools为空 | §3 V02 |
| V03 | C02；需求2；07§8.5 | 提示/Main | 直接要求／必要保持：Main明确两维护工具disabled且background Noting保留；其它能力保持 | 正式Root出现已确认英文句，原生其它工具可用 | §3 V03 |
| V04 | C02；需求3；07§8.11–12 | 提示/Noting | 直接要求／必要保持：任务作废父角色/策略并明确两工具enabled和仅四工具授权 | 初始/续Turn含权限控制及完整任务、工作视图 | §3 V04 |
| V05 | C03；需求4；07§8.12 | 机制/初始与续Turn | 直接要求／必要保持：不重复完整Schema；数据与指令分开；完整工作Notebook、时间和参数保持 | 初始及续Turn无callable_tool_schemas/重复定义，工作态含已有修改 | §3 V05 |
| V06 | C04；需求5；07修订、§3.1/4.5/5.1 | 权限/同步并发invoke间接调用 | 直接要求／必要保持：执行权来自真实运行时身份和绑定任务；模型内容或参数不能自授 | Main和其它child拒绝maintain/finish；Noting四工具外均拒绝，底层不能旁路 | §3 V06 |
| V07 | C04；07§4.5/5.1 | 身份/读取边界 | 直接要求／必要保持：Noting show取自身工作态；History只取绑定父；跨Profile/Conversation拒绝 | 不能借继承顶层Schema跨域或读父最新快照覆盖草稿 | §3 V07 |
| V08 | C05；需求6；07§3.1/8.2 | 缓存/构造到每个请求 | 直接要求／必要保持：父子Root/tools/冻结Active消息及缓存作用域结构一致，多模态保留；只追加任务控制 | 逐请求wire比对前缀；无child刷新MCP/Provider/记忆或重建Root | §3 V08 |
| V09 | C05；07修订、§12.3末段 | 生命周期/旧工具pin恢复 | 直接要求／必要保持：只在正常构造/恢复freeze前生效；旧缺维护工具pin补canonical，完整pin不改；旧Root/历史保留且sources如实 | 当前任务冻结后不热改；恢复工具pin来源及一次失效明确，无新恢复门槛 | §3 V09 |
| V10 | C05；07修订、§3.1/6.3 | 关闭/资格/兼容 | 直接要求／必要保持：全局关闭、非合格身份保原生；local参与开关不改变Main工具前缀；History/Scheduler独立 | 开关/身份矩阵通过，非Noting其它原能力无退化 | §3 V10 |
| V11 | 保留07§3.1–3.2/4.5；白板K6/N1 | 结束/并发 | 直接要求／必要保持：finish最后单独调用；混合批整批拒绝；结束锁固定视图；原生Turn返回后Commit Gate提交 | 同步并发混合无副作用；结束后写拒绝、重复finish幂等；文本done不能正常结束 | §3 V11 |
| V12 | 保留07§3.1–3.2/8.13 | 预算/失败/释放 | 直接要求／必要保持：最多五Turn、不自行压缩；预算/overflow可保存合法完整状态但标forced/overflow；一般错误可无快照 | normal/forced/overflow/API异常/取消行为与资源释放不变，不能forced冒称正常 | §3 V12 |
| V13 | 保留07§3.1/8.13/11.1；白板N3/P3 | 持久/并发/历史状态 | 直接要求／必要保持：原子校验参与/Anchor/版本/来源，旧Anchor不得回退pointer；仅新生效结果通知且追加时复核 | 提交与通知有效性接线、关闭/rewind/fork/旧结果晚到不被新工具面绕过 | §3 V13 |
| V14 | 保留07§8.1；白板P2 | Idle/其它触发 | 直接要求／必要保持：Idle需相应Noting正常提交才full compaction，Framework在压缩后；其它压缩/Force原机制保持 | 失败/forced/overflow不触发Idle压缩；已有任务复用按运行/正常/失败分别处理 | §3 V14 |
| V15 | 保留07§4.1–4.4；白板C1–9/L/E/N | Notebook保留语义 | 直接要求／必要保持：原文为事实源、稳定ID/版本、来源合法、Candidate二选一/结算、用户认可范围不变 | 无改Schema/内容语义；真实任务合法Notebook与Snapshot，不能凭新注册扩大写入范围 | §3 V15 |
| V16 | C06；需求7–8 | 真实模型/隔离 | 直接要求／必要保持：Alex独立Home/runtime/DB、仓库外cwd；实际kimi-for-coding；保Persona/业务Prompt，仅授权提示增量 | 隔离创建/配置指纹/实际Provider模型wire与生产无写入证据可复核 | §3 V16 |
| V17 | C07；需求8–9 | 实际用户链路/模型行为 | 直接要求／必要保持：小阈值只限隔离；自然Main行为误调用率与受控拒绝分开统计；任务正常finish及用户工作完成 | 真实Main→Noting→合法Snapshot→压缩/Framework代表链路；错误被Harness拦截后纠正 | §3 V17 |
| V18 | C07；需求8–9 | 真实工具协议 | 直接要求／必要保持：无重复Schema时真实Noting仍能实际调用四工具；不以声明/受控mock当实测 | 四工具真实执行记录和正常finish；如单轨未用齐须另取真实代表记录 | §3 V18 |
| V19 | C11；追加需求；07修订 | 真实长上下文 | 直接要求／必要保持：超过原N38的N46代表点，报告该模型真实Usage；不先压短；任务转换后固定工具可用正常完成 | 实际kimi-for-coding长Main/Noting wire、Usage、工具回执及正常提交证据 | §3 V19 |
| V20 | C08；需求10；06§1.4第271行 | 今日修补/微信 | 直接要求／必要保持：active中每条完整正式Assistant及时按序投递；redirect未发半截合并同通知，已发不重复，无Thinking外发 | 完整消息/工具前正文/redirect半截/空正文/纠正后回复及上下文事实保留证据 | §3 V20 |
| V21 | C08/C10；06§1.4第273–279行 | 今日修补/前端消息 | 直接要求／必要保持：来源包裹/Thinking/Timeline保留；failed_turn只由实际诊断行元数据分类，无turn_terminal合成兜底；slash/真实正文保持 | 正式后端元数据→前端分类→渲染接线；旧无类型不猜，真实部分回复不误分 | §3 V21 |
| V22 | C08；06§1.4第277行 | 今日修补/Heartbeat | 直接要求／必要保持：仅完整user heartbeat包装分类，原文/身份不变；默认折叠、标题图标陶土橙主题、展开保内timestamp | 前端真实组件和分类边界；不处理HEARTBEAT_OVER或添加行为 | §3 V22 |
| V23 | C08；06§1.4第281–283行 | 今日修补/审批 | 直接要求／必要保持：移动/桌面主题排版改善；Patch replace仅已有唯一owner待处理参数预览，文本转义，可空new删除；无新增接口/权限 | 当前owner配对、缺参/歧义回退、非Patch/Clarify保持；真实组件手机/桌面证据 | §3 V23 |
| V24 | C08；需求10；06§1.2第195行 | 交付范围/APK | 直接要求／必要保持：599d114后端/589df02前端同批交付；既有0.1.4竖屏APK不自动装用户手机 | 目标版本含今日修补，前端产物绑定；APK范围不被扩大 | §3 V24 |
| V25 | C08；部署SOP§0/2/6/8 | 发布能力与实际部署分层 | 直接要求／必要保持：先固定Core/UI/dist/PM-lock/配置/SOUL指纹、可恢复快照；活动工作结束才停唯一后端升级；失败保数据可回滚 | 发布脚本/操作计划可审；生产实际版本与保护收据由部署后Validation核，不以本地代签 | §3 V25 |
| V26 | C09；需求11 | 流程/模型/显示/门禁 | 直接要求／必要保持：Sol子Agent不Astra、不再派生；仅自建隐藏IAB；冻结十检查及等级不改变 | 编排模型/工具操作/规则diff与有效检查证据，未验范围如实标注 | §3 V26 |
| V27 | C10；需求8/12；07修订 | 禁止范围/数据保护 | 直接要求／必要保持：不动生产历史排期绑定、不重跑旧失败、不恢复47错误时间；不带隔离配置/库/凭据/Persona/raw wire入Git或生产 | 变更范围及测试/部署输入无上述内容；保密证据仅ignored目录 | §3 V27 |
| V28 | C08；需求10及仓库流程 | 交付/提交push | 直接要求／必要保持：生效范围变更统一提交干净push，部署版本精确绑定，旧今日修补不得漏发 | Git ancestry/dirty/远端绑定与发布包闭包一致；部署实际另由Validation核 | §3 V28 |

判据覆盖反查补录（实现调查初期）：原第2节V24对冻结需求10指定的599d114／589df02闭包只列合并交付，未逐项展开标题、wire、时间与Context。现保留V01–V28全部原判据，依原需求的精确交付范围及06既有事实契约补V29–V32；这是覆盖细化，不以实现解释替代用户目标或降低判据。V21–V23为06既有保留回归，未要求重新制作旧UI项目或重复昂贵验收。V06拒绝反馈同时继承07§7.2固定code/message/next_action，无权限扩大。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| V29 | C08；冻结需求10精确绑定599d114；运维记录2026-10-23已审修补口径 | 今日闭包/Kimi wire | 直接要求／必要保持：只对可信官方Kimi Chat URL更名输出字段；非可信URL/其它Provider/override优先级/fallback保持 | Main/aux SDK真实序列化只有一个输出字段，内部预算及其它协议不变 | §3 V29 |
| V30 | C08；冻结需求10之599d114标题修补；06原生title控制契约 | 今日闭包/标题 | 直接要求／必要保持：K3与带Provider前缀变体沿原生温度省略、oneshot及标题写回，不改其它模型默认 | 实际RPC→原生aux→SDK→session.title→DB/info及自动标题，失败保旧值 | §3 V30 |
| V31 | C08/C10；冻结需求10之599d114；06§1.4时间事实契约 | 今日闭包/timestamp | 直接要求／必要保持：压缩复制保持原消息authoring time和UID；新摘要/新输出仍是新时间，不恢复生产47旧行 | 原地/covered/rotation及full/cards/details/resume均保持，UID优先、显式时间不改、错误回滚 | §3 V31 |
| V32 | C08；冻结需求10精确绑定589df02；06§1.13/1.14 Context事实契约 | 今日闭包/Context显示 | 直接要求／必要保持：压缩完成只取当前owner正式Context，不以临时unavailable清掉旧有效值；显式invalidated仍清除；迟到不能覆盖新值 | 正式CompactionViews→ContextAfterCompaction→controller；并发/切换/重连/字段部分返回回归 | §3 V32 |

### 全新独立复审判据（2026-10-24）

本表由全新独立审查者 `/root/fixed_tools_reverification` 在读取代码、测试、动态看板、实现自评及旧审查结论之前形成并落盘。依据为初始冻结 `56b7ebc01131ea4eaad0a4690c0bfbab048c2803` 的用户需求、白板 K1/K6/N1–N4/P1–P6、07 的 2026-10-24 修订及保留契约、06 今日修补契约、部署 SOP §0/2/8，以及授权追加 `3ce7517dc7c4e6dbdae7de1607032c8281ff0e24` 的长上下文和恢复兼容要求。索引只用于定位；未以主会话的实现说明构建判据。以下 C01–C11 为本次全范围复审判据，不覆盖上方历史判据。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| C01 | 用户需求 §已确认方案1、4、6；07 顶部修订、§3.1/8.2 | 机制；合格 Main／全局 Noting 开启；非适用保持原生 | 直接要求：两维护工具的完整 Schema、description、Provider 转换不改，只改变注册层级；完整顶层声明不能被 Tool Search 折叠；首次增加工具面允许旧缓存一次失效 | 与冻结原 canonical 逐字段比对；正式请求的顶层 tools 含完整定义；无 messages[*].tools 或消息级动态注册；关闭／非 eligible 路径没有新增行为 | 本次证据矩阵 C01 |
| C02 | 用户需求2–5；07 §8.5/8.11 | Prompt；初始 Main 和 Noting 身份切换 | 直接要求：Main 明确禁用两工具；Noting 作废父 system／角色／规则／工具策略／任务／完成条件，并明确启用两工具、严格四工具；Main 其它能力保持 | 真实完整构建 Prompt 中出现已定英文；任务及后续控制消息当前身份清楚；不得借固定声明授予 Main 执行权 | 本次证据矩阵 C02 |
| C03 | 用户需求4、9；07 修订、§3.1/8.11/8.12；白板 K6/N6 | 数据与机制；初始任务、同 child 所有续 Turn | 直接要求：任务不重复完整四 Schema，仅使用 API tools；保留完整工作 Notebook、时间、任务参数和必要权限指导；同 Turn 成功修改可通过单条结果跟踪 | 初始与续 Turn 正式消息都不含重复 Schema或动态声明；完整当前工作视图可见，续 Turn 含已成功修改；不能删掉工作数据来缩短输入 | 本次证据矩阵 C03 |
| C04 | 用户需求5；07 修订、§3.2/4.5/5.1/7.2；白板 K1/K6 | 权限与状态；同步、并发、invoke、间接执行；普通子 Agent | 直接要求：可信运行身份及绑定工作态授予权限；Noting 仅四工具且 History 限父域；Main 和其它子 Agent 拒绝两维护工具。必要推导：不能用正文、参数、继承 Schema 或调用包装绕过；错误不改变状态、不泄露域外存在性 | 从正式入口追踪并取得拒绝证据；覆盖伪装、错误绑定、并发混批和间接路径；有效四工具保持可用；finish 与其它工具同批整批拒绝，end_requested 后不可再写 | 本次证据矩阵 C04 |
| C05 | 用户需求6–7；07 §3.1/8.2；追加版本 §12.3；白板 P3 | 前缀与生命周期；新构造、冷/热恢复、旧任务显式恢复 | 直接要求：从实际父 Active 结构冻结，Root、完整 tools、消息及缓存作用域逐请求继承，冻结后只追加任务／控制数据；旧 pin 缺定义仅在重建父运行态 freeze 前补 canonical，完整 pin 不变，保历史原记录并报告 sources | 检查父子真实 wire/结构、续 Turn 和多模态；不从历史重拼普通父前缀、不对子临时补工具、不刷新 root/MCP/Provider；旧 pin 恢复定向证据显示补齐时点、来源及一次缓存变化诚实 | 本次证据矩阵 C05 |
| C06 | 用户需求7–8；07 本轮修订；部署 SOP §0/1/3 | 环境、模型与隔离；Alex 本地完整链路 | 直接要求：实际 kimi-for-coding，Alex 原 Persona／业务 Prompt 保持，仅新增授权权限提示；允许仅隔离副本调低阈值／延迟；Home、runtime、DB、cwd 与生产隔离 | 环境与 Prompt 指纹、实际 Provider/model、隔离路径和配置差异可核；正式 CLI/RPC/原生 runner 完整接线，不用减 Prompt／假模型代签；无生产排期、外发或外部持久写入 | 本次证据矩阵 C06 |
| C07 | 用户需求8–9；07 §3.1/4.5/8.1/8.13；白板 N1–N4/P2 | 模型行为、正常结束、提交及用户结果；短样本 | 直接要求：自然 Main 误调频率与确定性拒绝分别报告；不重复 Schema 的 Noting 实际能用四工具并正常 finish。必要推导：finish 成功只请求结束，原生 Turn 返回后 Commit Gate 发布合法完整 Snapshot；forced 不能冒称正常；Idle 正常提交→父 full compaction→Framework | 真实模型短链路有工具回执、finish_noting、合法 Snapshot、完整 Framework 与用户任务完成；错误调用被 Harness 拒绝且可纠正；保预算／失败／释放和有效 pointer 投递边界；未实际调用的四工具分支不得仅凭声明声称实测 | 本次证据矩阵 C07 |
| C08 | 用户需求10及“之前今天修复一块部署”；06 §1.2.1 微信正文/Redirect、Heartbeat及 Android 竖屏；部署 SOP §0/2/6/8 | 联合交付；后端599d114修补、前端589df02与本次实现 | 直接要求：审查今日修补随最终产物纳入提交、push及云发布闭包；升级保护原数据／配置／排期／绑定，APK不自动安装。必要推导：部署能力、固定源码/产物/PM锁、可恢复备份、空闲停启、回滚方案须先可核；实际部署结果由部署后 Validation 核 | 静态确认两端修补完整接入最终版本，已有同版本机制证据可信；发布前具备执行能力与保护计划。记录“具备部署条件”与“已经部署验真”的边界，不用未来动作判已完成，也不要求本审查者写生产 | 本次证据矩阵 C08 |
| C09 | 用户需求11；冻结 AGENTS 与自主套件流程 | 过程约束；全部子 Agent、检查与界面操作 | 直接要求：Sol 系/high、不使用 Astra、不再派生；固定十检查及阈值不降；只自建隐藏 IAB 无显示／焦点变化；先独立 Verification 后独立 Validation | 核本轮配置/记录、检查入口和结果版本；不以改门禁获得通过；没有合规 UI 手段则如实未验；不能把 Verification 代替用户验收 | 本次证据矩阵 C09 |
| C10 | 用户需求12；07 本轮修订；06 微信/来源最终确认；部署 SOP §3/8 | 范围与数据安全；生产、恢复、公开仓库 | 直接要求：不恢复旧47错误时间、不实际重放旧生产失败 Noting、不更改其它 Provider 路由／Thinking／Timeline／来源包裹；凭据/Persona/历史/raw wire 不入 Git；隔离配置不带生产 | review 全部变更与待跟踪文件，核敏感证据 ignored/受限、生产改动计划精确；历史来源/模型原文保持，今日必要修补没有扩大语义或数据权限 | 本次证据矩阵 C10 |
| C11 | 授权追加 user-request 最末节；追加版07顶部修订 | 真实长上下文；实际 kimi-for-coding、超过原N38 | 直接要求：已有 N46 长代表点、记录该模型实际 Usage；父 Main→Noting 切换后固定工具仍有效且正常结束；不得先压短再声称长样本 | 核完整请求/响应与父子 wire，证明实际输入长度超过原N38、无任务重复 Schema、无切换前自动压短、工具成功与正常 finish/合法 Snapshot；短成功、K3校准或受控 SDK 均不能替代 | 本次证据矩阵 C11 |

薄弱处说明：C04 的“间接路径”、C05 的“正常恢复边界”、C08 的“部署闭包”没有规定唯一函数或脚本；审查仍以权限不可绕过、freeze 前完成工具面、数据保护和真实运行绑定为必要不变量，不降低为 helper 测试或准备文件存在。C07 对正常完成与 forced、Snapshot发布及Idle压缩先后已有明确规定，不属可自行改变的工程空白。本表形成后才进入实现调查。

## 3. 逐条实现证据

本表为4f503a2初审事实，F01修补及T3真实执行材料尚待交回；每行解释见第2节，代码与证据用于验证事实，不反写判据。证据相对前缀为`.hermes-dev/noting-fixed-tools-20261024/`，另有显式旧包路径。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| V01 | secretary/noting_contract.py；noting_surface._read_schema；Moonshot/Anthropic转换owner未改 | 冻结→待审git diff为空；canonical SHA与用户冻结二值一致；真实SDK fixed_permissions检查每字段 | schema-before-sha256.json；root-integration.log；verification/independent-hash-check.json | 符合：原定义和转换未改 | 顶层列表新增会使旧工具前缀一次变化，未声称旧缓存字节相同 |
| V02 | apply_main_read_surface→filter_tool_definitions→tool_search.main_tool_is_direct→request assembly | 正式AIAgent/SDK受控HTTP验证Main与child四工具完整顶层；显式defer仍不能折叠；noting_request旧动态函数已删且无引用 | runtime/final-permissions.log；prompt/final-requests-tests.log；root-integration.log | 符合：完整固定顶层，messages无tools声明 | 实际模型wire待V16–19核 |
| V03 | agent/system_prompt.NOTEBOOK_GUIDANCE→turn_context→synchronize_main_read_prompt | 原文禁用句逐字加入；global on/off/local与冷root恢复测试；旧Root一次重建后warm请求保持 | tests/secretary/test_fixed_noting_request.py；prompt/final-requests-tests.log | 符合：准确禁用且不改其它Main段落 | 当前合格Main/全局门禁，非全局默认注入 |
| V04 | noting_prompts.DEFAULT_NOTING_TASK_INSTRUCTION/CURRENT_NOTING_CONTROL/CONTINUATION→runner | 三段与07修订逐字相等；父system/角色/规则/策略/任务/完成条件作废；原六步任务其余逐字保留 | prompt/receipt.json；tests/secretary/test_fixed_noting_request.py | 符合：身份切换与四工具授权准确 | 此项证明Prompt接线，执行另见V06 |
| V05 | noting_tools.noting_tool_control_message→_working_control→_run_child_turns | 仅删callable_tool_schemas；完整working_notebook与task_parameters/current_time/evidence_coverage保留；真实Loop两Turn检验先前修改仍在 | prompt/final-requests-tests.log；tests/secretary/test_noting_dynamic_tools.py | 符合：初始/续Turn无重复定义且工作态完整 | History返回正文中的历史Schema属于证据，不是新增注册 |
| V06 | turn_tool_validation.secretary_validation_refusal→parser→sync/concurrent→resolve_invoke_tool_executor→scoped_registry_dispatch→_bound_store | Main/普通child拒绝两维护；Noting白名单仅四，解包前拒绝tool_call/tool_search、拼写修复前后拒绝、prechecked invoke仍守卫；真实Loop/DB无写；但拒绝回执缺固定字段 | tests/secretary/test_fixed_noting_permissions.py；runtime/final-permissions.log；verification/permission-error-contract.log | 违规：F01权限有效但07§7.2回执不符合；独立1 failed反证 | 待主会话提案修补全部入口，不能用有效拒绝掩盖错误契约 |
| V07 | noting_tools._bound_store/notebook_work_show；tools/session_history_tool；_bind_child_identity | Store须真实锁对象及父ref相等；show工作态不能选scope；History绑定父DB/ref；现有全局Main跨域不授予child | runtime/runtime-tests-1.log；runtime/runtime-tests-2.log；tests/secretary/test_noting_child.py | 符合：旧可信绑定保留，四工具执行仍归父域 | 未扩大跨Profile授权；不把Schema字段当权限 |
| V08 | freeze_parent_active_prefix/freeze_parent_runtime→cache_parity→assemble_api_request/iteration_summary | 父运行态先freeze，tools/root深拷贝、cache scope及frozen前缀保留；正常/summary/retry/延迟启动/多模态、OpenAI及Anthropic SDK有针对性证据 | prompt/final-requests-tests.log；prompt/third-tests.log中cache_parity11与summary4已通过文件；tests/secretary/test_noting_dynamic_tools.py | 符合：机制与受控SDK逐请求前缀一致 | 真实kimi字节/结构另待V16–19；prefill/multimodal只用受控SDK取证 |
| V09 | start_recovery._prepare_fixed_recovery_tools→parent_factory→freeze_parent_runtime→run_noting_task | 只补缺失canonical；完整pin不变；sources.tools注明补齐及非旧wire字节相同；旧failed row/root/suffix保留，幂等key/租约/资源释放沿原生 | tests/secretary/test_noting_recovery.py；prompt/final-recovery-tests.log；root-integration.log | 符合：freeze前恢复适配，无新恢复门槛 | 未重跑生产任务，重启状态interrupted不自动恢复 |
| V10 | noting_surface.notebook_read_enabled/apply_main_read_surface→Main资格；local开关与noting_trigger_gate分开 | global off去两定义、History仍有；local off不改Root/tools；sideagent/aux/branch/reset/compaction cold/warm已在surface33与固定测试核 | runtime/runtime-tests-1.log；tests/secretary/test_noting_surface.py；root-integration.log | 符合：原生能力及独立开关保持 | 原生其它Provider行为只按变更影响核，不重复全量 |
| V11 | secretary_dispatch.reject_noting_mixed_finish/secretary_validation_refusal→guard_noting_tool_batch→finish_noting/store.lock→runner | 完整批预检早于repair/执行；正常end_requested固定状态、后写state_conflict、重复finish保首reason；原生Turn返回才_commit_when_complete | runtime/final-permissions.log；tests/secretary/test_fixed_noting_permissions.py；noting_tools.py:115 | 符合：finish单独与状态冻结保持 | 不得将end_requested当committed；真实结束待V17–19 |
| V12 | _run_child_turns/_force_task_close/_commit_when_complete→finally close | 五Turn/50 iteration、context overflow兜底；一般API失败无新Snapshot；非正常终止不伪报finish；DB/clients/admission/强引用在finally释放 | runtime/runtime-tests-2.log child38；prompt/third-tests.log r3_child54有效文件；root-idle-integration.log | 符合：保留结束/预算/失败/释放机制 | 历史第三次整命令含fixture失败不算全绿；只复用已通过文件及最终修正文件 |
| V13 | commit_noting_snapshot→db._execute_write→notebook_commit_snapshot_result_conn→pointer重选→publish_noting_completion→append-time predicate | 同事务核开关/anchor/合法state/来源版本并插完整Snapshot；pointer_changed false不通知；实际追加在framework→persist→DB锁核仍current；未改fork/rewind ownership | secretary/noting_child.py:513；hermes_state_secretary_notebook.py:235；framework_messages.py:333；runtime child38与surface33 | 符合：新工具面仍落原子门禁，未绕过pointer | 全量fork/rewind并非本轮重做；相关owner未改且表/契约保持 |
| V14 | Idle timer→prepare_joint_noting→existing admission/child→normal commit callback→request_context_compaction wait→Framework | 正常finish+Snapshot才callback；已有running等、正常已完成压缩、失败/forced不压缩；relevance check区间及owner；native completion事件而非admission才释放通知 | tests/secretary/test_idle_noting_commit_order.py；test_idle_noting_reuse.py；root-idle-integration.log 43通过；旧repair-review-20261023-idle-integration.log含native36 | 符合：Idle成功前置与其它compaction独立性落实 | 自动/手动/Force原机制保持；一般API失败可无新Snapshot |
| V15 | NotebookStore/notebook_items/noting_contract→maintain→Commit Gate；完整Noting六步Prompt | 定义、Notebook语义校验及原六步内容未改；读/写/finish实际SDK与DB受控链可得合法完整Snapshot，无外部Memory写 | schema diff为空；runtime/final-permissions.log；prompt/final-requests-tests.log；noting_prompts.py | 符合：本轮保留内容语义，Schema与owner未被改写 | 不据受控单样本声称模型每次均正确萃取全部七类；真实任务质量另核 |
| V16 | T3 prepare._make_agent→原生Profile/provider→独立Home/runtime/DB/cwd | 已核准备脚本及source前后指纹；实际run-short-20261024-011441仓库外全新Home/runtime/cwd/DB，SOUL指纹相等，真实wire业务请求kimi-for-coding/high；仅隔离差异，禁MCP/微信，无源DB复制 | e2e/preparation.json；e2e/prepare.py；e2e/run-short-20261024-011441/manifest.json；verification/short-independent-audit.json | 符合：隔离与实际短请求已核；长样本另列V19 | 源cwd本机不存在，未编造线上workspace AGENTS；外部MCP禁用不声称线上工具全复刻 |
| V17 | 正式Main→Idle timer→Noting→native compaction→Framework→Main | 首短8HTTP200，5自然Main/5Turn零维护误调，Noting1Turn正常finish空Snapshot、Framework1；独立从实际wire重算root/tools/Active及最后Main前缀均相等；但4→4手动压缩no-op引structural_backoff，Idle仅尝试未压缩成功 | e2e/short-stage-report.md；run-short-20261024-011441/audited-receipt.json；verification/short-independent-audit.json；V06/V11–14机制证据 | 证据不足：短链缺实际Idle父压缩与跨压缩Notebook承接；自然小样本已如实统计 | 自然0误调不能替代确定性拒绝；forced不能代正常 |
| V18 | 四工具原生dispatch→真实Provider模型结果→工具回执 | 受控真实Loop四工具均可执行；真实短Noting只调用finish_noting一次，History/Show/Maintain均未用；不把schemas存在当已实用 | runtime/final-permissions.log；e2e待交回 | 证据不足：缺真实四工具覆盖及正常完成材料 | 若自然轨迹没用齐，需明确真实覆盖缺口，不能伪造或受控冒充 |
| V19 | kimi-for-coding长Main→manual compaction前freeze→Noting | N46准备存在且计划实际Usage/wire、不先缩短；尚缺实际长请求及结束审计 | e2e/long-history-n46.json；e2e/preparation.md | 证据不足：C11实际长样本未交回 | 不能套K3旧Usage或拿短请求代签 |
| V20 | TurnRunner capture/message callback→GatewayStreamConsumer FIFO→Weixin adapter；redirect receipt→checkpoint→FIFO | 完整UID消息按序；capture与投递分离；writer/turn fencing；同文不同UID分别发、final按成功UID+payload去重；半截清洗后合并同redirect通知，不进模型回复 | weixin-message-final-integrated.log 56通过；weixin-message-explicit-streaming.log 31通过；verification/independent-hash-check.json全部15文件一致 | 符合：微信原生链路受控SDK/adapter整链证据支持 | 未真实向微信发送；外部不确定结果仍最佳努力，不承诺exactly-once |
| V21 | 原Framework/来源/Thinking/Timeline owner；589df02无此类生产改动 | 来源包裹候选已撤回，git diff闭包只有Context与时间测试/APK；06第279行失败卡保持既有元数据分类，无新增后端/前端消息机制 | 599d114/589df02 diff；docs/operations-log.md撤回记录；projection.ts:339 | 有依据的不适用：既有完整失败卡UI重验不属本轮新增范围；本轮未改该机制 | 保留约束已查变更未触及，不将早期全UI项目并入新施工；今日微信输出仍按V20核 |
| V22 | 既有projection完整user heartbeat识别与既有卡片 | 589df02未改该产品；原user完整wrapper分类仍在，来源角色/内容不变；未新增HEARTBEAT_OVER处理 | projection.ts:344；589df02生产diff | 有依据的不适用：既有Heartbeat视觉全验不属本轮新增范围 | 保留回归仅审无行为改动；不冒称本次重新UI验收 |
| V23 | 既有approval/patch preview组件 | 599d114/589df02未改审批或Clarify，未增加后端接口/权限/choice；原生批准机制不受固定Noting工具权限变更 | 双仓固定diff闭包 | 有依据的不适用：旧审批弹窗/截图项目不在本轮新增范围 | 未重新UI截图，未据源码冒称旧视觉验收重新通过 |
| V24 | Core git ancestry＋Web589df02→439 dist；Android Manifest/MainActivity | 当前Core包含599d114；Web固定589df02且clean；dist源commit/439files绑定；APK0.1.4 hash独立重算相等，portrait/1004/nondebug签名收据 | verification/release-static-receipt.json；frontend-manifest.json；android-apk-20261023/package-verification-0.1.4.json | 符合：今日修补在候选闭包，APK已有竖屏包 | 没有安装用户手机；本轮Web新构建与既有APK分别追溯，不等同手机真机测试 |
| V25 | 发布计划T4→首尔正式SOP→preflight；生产部署尚未执行 | 亲读发布脚本：精确目标祖先/HEAD/锁与pm复用、保护表指纹、活动租约/Noting拒绝、停两专属服务后SQLite备份、ff-only、Linux原子目录交换与分别finally启服、失败保新数据不盲回滚；dist439独立解包集合/SHA全等；preflight旧e9de406 | plan.md T4；cloud-preflight.json；release/deploy.py/remote_release.py/PREPARE.md/selfcheck-receipt.json；verification/release-package-independent-audit.json；部署SOP§0/2/6/8 | 符合：发布能力及保护计划可审；生产实际验真交部署后Validation | 不是已部署完成结论；生产版本/配置/数据/服务实际差异必须后续验真 |
| V26 | 本轮委派记录与冻结检查入口、实际工具使用 | 独立审查未派生/未UI/未收费API；本轮scripts/check与lock/规则入口diff为空；root staged frozen10全部通过0/0；实现报告Sol/high | root-staged-check.log；verification/independent-hash-check.json；plan.md编排 | 符合：当前所审流程证据未见改门禁或显示边界 | 不从子Agent自报推断未记录外部行为；只读审计可得范围 |
| V27 | 双仓tracked diff及T3隔离脚本/发布输入 | 本轮只改受授权代码/文档/测试，private Persona/raw wire/credential/DB不入tracked；恢复调试只改构造兼容，未调用生产重跑；源文件只读保护 | git diff范围；e2e/preparation.json/prepare.py；cloud-preflight.json | 符合：当前实施及准备未越数据边界 | 生产保护最终值在部署后Validation；不预签未来操作 |
| V28 | core upstream4f503a2；Web upstream589df02；当前报告/修复尚在推进 | 原生闭包已commit且当前upstream一致，祖先599d114在；既有两untracked稿保留；F01修复和本审查未提交，发布未发生 | verification/release-static-receipt.json | 证据不足：最终生效修补提交push和部署闭环尚未收尾 | 不能把祖先已push当整轮最终clean/已部署；留后续收尾核 |
| V29 | utils.is_official_kimi_chat_url/normalize_kimi_chat_output_overrides→Main _max_tokens_param→chat kwargs；aux build/402retry | 可信https精确host/path/443无userinfo/query/fragment；copy-on-write override/extra_body保优先级；其它Provider与Responses/Anthropic保持；旧生产6文件SHA一致，本轮58 wire通过 | tests/agent/test_kimi_output_tokens_wire.py；root-integration.log 58；kimi-output-wire-20261023/files.sha256；utils.py:757 | 符合：仅确认端点输出字段兼容，内部预算和fallback未改 | 不声称仅改字段解决N38动态声明400；旧动态39用例已被本轮替代 |
| V30 | auxiliary_client._is_kimi_model→_build_call_kwargs→llm.oneshot→session.title/info→DB；自动title prologue | K3/k3-*/provider前缀走原生温度省略；真实RPC/aux/SDK受控HTTP与真实SessionDB验证生成非持久、确认写回、自动标题回调；失败保旧名 | tests/tui_gateway/test_ai_title_native.py；apk-title-20261023/title-native-final.log 5通过；temperature-regression.log 4通过 | 符合：标题兼容/写回正式链路完整 | 无真实Kimi标题质量评估；本轮不在线改名 |
| V31 | hermes_state_messages._carry_parent_timestamps→archive_and_compact/covered/publish_compression_child→full/cards/details/resume | UID优先且同文反序不会串时间；未知UID不借时间，显式timestamp保留；active归档前补time、异常恢复调用方；所有投影真DB检查 | timeline-timestamps-20261023/receipt.json哈希3项全一致；backend-tests.log 104；tests/hermes_state/test_compaction_timestamps.py | 符合：新压缩复制继承源时间，不恢复生产旧行 | 旧47错误历史修复不属授权，本轮没有迁移 |
| V32 | CompactionViews.readContext→ContextAfterCompaction.read/observe→controller | unavailable不删pending/不invalidate旧值；显式context_invalidated处理；token/owner/lifecycle/revision拒绝迟到；已观察字段不被旧read覆盖；正式controller相关测试 | Web src/core/compaction-view.ts/context-after-compaction.ts/controller-context-compaction.test.ts；frontend-manifest/build；frontend-context-test.log当前589df02正式controller50通过；frontend-context-receipt.json；verification/context-independent-hash-check.json四项全真 | 符合：正式controller50项覆盖保留值/迟到/owner/显式失效，源码与日志哈希已核 | 本轮不是新造Context cache；不以单纯build当并发恢复测试通过 |

### 全新独立复审证据矩阵（Core 1ea38ef／Web 589df02）

下表按本次第2节独立 C01–C11 判据逐条核验，保留上表 V01–V32 初审时点记录。`reverification/`均指 ignored `.hermes-dev/noting-fixed-tools-20261024/reverification/`；真实模型原件位于同级 `e2e/`，不写入 Git。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| C01 | AIAgent构造／turn_context.prepare→noting_surface.apply_main_read_surface→registry filter→Tool Search direct→build_api_kwargs→Chat SDK；两canonical来自noting_contract | 独立重算canonical SHA与before字典逐字段相等；Provider运输转换文件无改；固定工具直出而Main执行名排除维护工具；真实Main及所有长child顶层28工具相等、无messages.tools | secretary/noting_surface.py:78；tools/secretary_dispatch.py:43；tools/tool_search.py:149；reverification/independent-binding-audit.json、independent-model-audit.json；固定权限47通过 | 符合：注册层级改变，原Schema／description／转换保持；正常构造边界生效 | 不把新增工具面与旧缓存字节相等混同；关闭／非Main路径由正式surface测试覆盖 |
| C02 | system_prompt.NOTEBOOK_GUIDANCE→Main root；noting_prompts.DEFAULT_NOTING_TASK_INSTRUCTION＋CURRENT_NOTING_CONTROL→run_noting_task／continuation | 四段常量逐字存在授权追加版07；独立核长样本真实Root包含原Alex SOUL及Main禁用句，child任务启用两工具、作废父策略并限四工具；受控正式Main gate/冷恢复/两Turn SDK测试有效 | agent/system_prompt.py:40；secretary/noting_prompts.py；tests/secretary/test_fixed_noting_request.py；prompt/final-requests-tests.log；reverification/independent-binding-audit.json | 符合：模型可见当前权限明确，原业务Prompt保留 | Prompt声明不授予执行权，执行硬约束另核C04 |
| C03 | noting_tools.noting_tool_control_message→run_noting_task.initial_instruction／_working_control→_run_child_turns续Turn；turn_request_assembly／iteration_summary_messages使用原生cache normalizer | control数据保完整working_notebook、7天/72h、时间及可读coverage，移除callable_tool_schemas；真实长7请求无动态声明/重复schema；正式两Turn多模态SDK、恢复与summary用例通过且源码/日志SHA一致 | secretary/noting_tools.py:171；secretary/noting_child.py:661/684/814；agent/turn_request_assembly.py:177；prompt/receipt.json、final-requests-tests.log、final-recovery-tests.log | 符合：初始／续Turn去重复定义，同时保工作数据及原生前缀归一化 | 真实长样本只有一个原生Noting Turn；续Turn与多模态结论来自真实SDK受控I/O机制证据 |
| C04 | validator完整批预检→repair前后policy→sync/concurrent parse（包装解包前）→共同dispatch gate→inline invoke（含prechecked）／scoped_registry_dispatch→_bound_store；History可信父域绑定 | 亲读每入口；标准scope_denied含message/next_action；Main合法混批保History执行，Noting跨名单整批拒绝；finish混批无效果，end_requested锁定；47权限＋9原生dispatch有效。原初审失败的直接invoke反证在当前HEAD独立重跑1通过 | tools/secretary_dispatch.py:98/116/147；agent/tool_executor.py:464/660/737；agent/turn_tool_validation.py:72；secretary/noting_tools.py:33/115/141；permission-errors/version.json及日志；reverification/permission-error-contract.log | 符合：原F01（计划F02）关闭；权限不来自模型自称／参数／继承定义，错误回执契约已齐 | 非Noting其它工具、通用scope/plugin/未知名及finish混批错误格式保持；自然零误调不代替确定性拒绝 |
| C05 | freeze_parent_runtime→apply_cache_parity_from_parent→freeze_parent_active_prefix→child构造／每次装配；恢复start_recovery._prepare_fixed_recovery_tools→parent_factory→freeze | 独立对照实际Main wire与4个长child wire全部父前缀及tools相等；完整N46结构保留。旧pin测试核缺两定义只在freeze前补、完整pin不变、sources明确非旧wire字节等价、原失败行/root/history未改；受控跨协议/多模态/续Turn证据按SHA接收 | agent/cache_parity.py:84/111；secretary/noting_child.py:400/415；secretary/noting_recovery.py:24/68；tests/secretary/test_noting_recovery.py；prompt/final-recovery-tests.log；reverification/independent-model-audit.json | 符合：冻结后不重建工具/root或改父消息，恢复边界补齐而非对子热补 | 未实际恢复旧生产任务；新运行的旧缓存一次变化已记录，不声称所有协议在线实测 |
| C06 | tui_gateway._make_agent→AIAgent原生Provider→正式Loop／DB／timer／spawn；独立Home/runtime/cwd | preparation与执行脚本已亲读：SOUL逐字保留，config仅隔离模型别名/阈值/延迟/本地cwd等差异；安全审计限隔离写入及Kimi推理。独立核真实Root含原SOUL、长样本source SHA皆当前、实际model=kimi-for-coding/high，全部raw受限 | e2e/prepare.py、execute.py、preparation.json；run-long-20261024-012630/；reverification/independent-model-audit.json | 符合：实际Alex隔离原生运行，未缩减业务Prompt伪造低成本，生产源未修改 | MCP/微信禁用用于隔离，未冒称生产外部工具全复刻；最大上下文262144只是原配置pin／family默认，非端点最大窗口实证 |
| C07 | 正式Main→Idle timer→真实Noting四工具→finish→Commit Gate→父native compaction→Framework→Main继续；失败／预算／pointer owner保留 | 默认短013830真实16HTTP200，History2、maintain15次（9参数拒绝后6成功）、finish1；正常Snapshot→Idle实际持久compaction→Framework→Main正确承接。显式控制短020652另8HTTP200，真实同child History1／Maintain3／Show1／Finish1全部成功；一条原生steer持久在tool结果后，Show读working中entry3/1新版本且父Snapshot未变，随后正常提交和Idle压缩／Framework，资源释放。SQLite独立核publication→Framework行序66<70、89<93 | e2e/run-short-20261024-013830/、run-short-20261024-020652/；reverification/independent-model-audit.json、show-completion-audit.json、native-framework-db-order.json；43Idle机制证据 | 符合：默认任务完整链路及显式Show可达／当前工作态／正常结束均已真实闭包，R01关闭 | 默认短9参数拒绝如实保留，不私定容忍率；显式Show是单列受控指令分支，不回填默认Task自然使用。额度截断旧样本不算成功；正式用户验收仍由独立Validation负责 |
| C08 | Core祖先599d114修补＋固定工具1ea38ef；UI589df02→439dist；发布deploy.py dry/preflight/stage/apply→remote_release.preflight/backup/exchange/start/verify | 全文审发布脚本、独立tar439文件集合/逐SHA及bundle/目标/锁一致；Core和UI upstream均等目标。微信15文件、时间3文件、Context源码/50项日志指纹全真；标题5/温度4、Kimi wire58、Idle43及APK0.1.4原证据按实际同版本复用；已核首尔旧e9de406及正常unit只读预检、完整三库快照及保护表/配置/绑定指纹方案 | reverification/independent-binding-audit.json；frontend-context-receipt.json；release/dry-run-receipt.json、selfcheck-receipt.json、deploy.py、remote_release.py；cloud-preflight.json；ops今日入口 | 符合（发布前符合性）：联合修补完整纳入候选和安全发布路径，具备可审产物/恢复条件 | 当前没有部署；独立Validation须在本地链路通过后部署，再核真正Web/Gateway目标、保护数据、439静态及Dashboard；不安装用户手机、不以准备态代签生产 |
| C09 | 本轮Sol/high委派与独立门禁；冻结十检查→相关暂存／临时index；本审查工具边界 | 本审查全新上下文、先原文判据后实现且不派生；未UI/收费API/SSH/生产写。冻结检查入口/锁/阈值diff为空，六文件最新十检查health0/0、前集成十检查有效；当前仅复跑原失败反证1项 | permission-errors/checks.json；root-permission-staged-check.log；root-staged-check.log；reverification/independent-binding-audit.json | 符合（本阶段）：无降门禁／改模型／显示边界；保留独立Validation顺序 | 真实用户验收及部署后核验尚在后续阶段，本报告不代签；没有重复大套 |
| C10 | 双仓完整差异→隔离输入／执行审计→发布上传精确5文件、三库/配置备份与保护指纹；恢复仅构造兼容 | tracked差异没有凭据/Persona/历史/raw；ignored证据受限，UI clean，原两份untracked稿保留；微信来源包裹/Thinking/Timeline机制未扩大，时间修补只对新压缩复制生效；未调用生产旧恢复、未外发或改生产模型阈值 | git diff 599d114..1ea38ef及599d114/589df02闭包；e2e/execute.py；release/remote_release.py；reverification/independent-binding-audit.json | 符合：范围和数据权限保持，无旧47行恢复或生产重放 | 根文档／ops正在由root收尾，不将其dirty误当未经提交产品源码；生产实际保护指纹由部署后Validation核 |
| C11 | N46184条合法历史→真实Main→manual joint冻结→真实Noting→maintain/finish→Snapshot/Framework | 独立解析每份raw wire/response：1Main140765 input、首Noting143828 input；46组184条逐字段完整，4child均无先压短，父前缀/工具一致；7HTTP200，maintain8与finish1全成功；1Turn正常提交、pointer_changed、Framework1、资源关闭 | e2e/run-long-20261024-012630/{wire-*.json,response-*.jsonl,events.jsonl,result.json,snapshot-audit.json}；reverification/independent-model-audit.json | 符合：实际kimi-for-coding超过原N38代表点，固定声明切换后工具有效且正常完成 | 1原生探针thinking disabled单列，不计High业务；长样本History/Show0不虚称四工具齐；不推测最大窗口／普遍成功率或实际费用 |

## 4. 核心目标及验证方法审查

核心机制从正式AIAgent构造/恢复到provider顶层tools，经validator、完整批预检、同步/并发parser、inline/registry和真实绑定Store贯通，权限不由模型参数或正文决定。固定Schema与Main执行名分开，Noting工具定义继承父冻结数组但执行名精确四个。初始/续Turn仍附完整工作Notebook，动态注册已退出正常及summary接缝；缓存归一化继续区分父前缀/子后缀，恢复旧pin只在freeze前补齐且来源明确。

反证问题已检查：tool_call/tool_search先解包会否绕过（原名先拒绝）；拼写repair会否提权（前后策略校验）；pre_tool_block_checked会否旁路（inline仍检查）；已有Store能否给普通child写权（marker/lock/ref共同检查）；local开关会否变工具prefix（不会）；旧pin缺Schema会否加恢复门槛（不会）；文本done/forced会否冒正常finish（不会）；晚Anchor/排队通知会否回退（Commit Gate与实际追加pointer复核保持）。发现F01说明测试虽能证明拒绝，不足以证明07完整错误契约；独立负对照实际失败，能识别这类错误实现。

已有测试底座主要只控制SDK I/O，实际Loop、SDK JSON、DB、admission、Store、Commit Gate及后台线程运行；部分失败矩阵故意控制child返回类型，这可验证父状态机，但不冒称真实模型错误频率。正式SDK多协议/多模态检验证明结构保留，不代表实际Anthropic在线可用。本轮真实Kimi由单owner负责，当前未交回，不使用受控轨迹替代。旧包证据按文件哈希复核复用，Kimi旧dynamic测试已变更不沿用其39通过，而用本轮新32/116集成接续；无无关大套重跑。

检查冻结入口、lock、Provider Schema转换与canonical文件无变。微信发送证据为真实SDK流/原生Turn/consumer/实际adapter模拟发送，支持正式接线与顺序，未发送真实微信；标题证据为原生RPC与持久化、SDK受控响应，不声称模型标题质量。UI范围按固定589df02交付闭包审查；旧完整Heartbeat/失败卡/审批设计不扩大为重做验收，保留约束通过变更反查。生产实际部署/数据保护由部署后Validation核，不以本地报告代签。

### 全新复审的机制与方法复核

本次全轮复审从第2节 C01–C11 出发，重新亲读完整固定工具差异、今日599d114生产修补、589df02前端差异、所有关键执行接线及发布脚本，没有把初审清单当唯一范围。主动核查的反例包括：名称repair是否把拼写误调变成授权、tool_call/search是否在解包前溜过、prechecked invoke是否绕过policy、Main合法混批是否被一并丢弃、Noting finish混批与结束后写是否有副作用、旧恢复pin是否被子运行临时重建、父压缩先完成是否改变child长前缀、发布期间用户新写入是否被“保护”逻辑覆盖。这些路径均由共同policy、可信绑定／锁、freeze前恢复、原子Commit Gate及只拒绝不覆盖的发布流程满足；未发现新的代码偏离。

权限错误契约使用原初审失败的相同独立反证在当前1ea38ef重跑，1 passed／0 failed，未发真实模型；这补证原F01关闭，而非复跑47项替代源码review。其余32请求、20恢复、47权限、9原dispatch、43Idle、Context50和今日微信／时间／标题／wire证据按当前源码及日志SHA复用，不累计重叠测试数字。旧Kimi包两个动态测试SHA不匹配是本轮有意替换，旧动态通过数不代签新固定声明。

长样本的判断直接来自实际wire及返回Usage，独立重算184条N46内容、真实父请求前缀和4次child请求相等，原Alex SOUL完整出现在root，真实工具回执和合法Snapshot相互一致。长阶段文字摘要曾称创建“工作指导Candidate”，但实际Snapshot是8条含decision、candidates为空；本审查以工具回执／Snapshot为事实，未将摘要误差转成新增产品缺陷或候选成果。长任务足以关闭C11，不足以关闭C07的真实四工具与Idle链路；补短准备种子和任何no-op均不算真实正常完成。

发布前审查确认固定bundle、439静态文件、既有PM/锁、首尔ubuntu两专属service、空闲/lease/Noting复核、停服后三库SQLite backup、配置/凭据0600备份、Linux renameat2原子目录交换、finally分别尝试重启及失败保留新写入／不自动回滚DB。C08的“符合”严格限发布前机制与能力；生产实际版本、服务与数据不在本次预签，必须后续Validation部署后核。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| F01/P2 | V06；07§7.2；tools/secretary_dispatch.py:130、147；agent/inline_tool_executors.py:346；agent/tool_executor.py:751 | Loop拒绝缺next_action；直接invoke与executor只返回error字符串；本地原生invoke反证1 failed | 权限有效但新固定权限工具的拒绝回执违反固定错误契约，影响模型一致纠错，阻断本门禁 | 主会话提出最小统一标准拒绝方案；核同步/并发/Loop/invoke/registry，拒绝前无效果且带scope_denied/message/next_action | 已证实，待提案与修复 |

### 全新复审当前发现

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| 原F01（计划F02） | C04；noting_dispatch_refusal及Loop/registry/inline/executor | 原初审拒绝有效但缺固定错误结构；1ea38ef同一policy builder已贯通全部入口，当前独立原反证1通过、47＋9同SHA证据有效 | 原违规已消除；没有放宽权限或错误契约 | 同版本路径源码、标准shape、零副作用、合法混批和拒绝后合法调用已核 | 本次复审关闭，初审事实保留 |
| R01 | C07；真实四工具覆盖中的notebook_show | 013830已证默认Task正常完整链路；020652显式原生steer分支进一步证同child四工具成功、Show working新版本、正常finish与Commit Gate／Idle压缩／Framework／释放 | 原必要真实分支缺口已补齐，没有改变产品Task／Schema／权限／完成条件；默认自然行为与显式请求分开报告 | 独立解析raw、只读SQLite核steer与publication顺序、Show-store-parent版本对照及正式提交全部满足 | 本次复审关闭；取证失败及内部预算修正原件保留 |

本次没有新增范围外产品项。UI视觉、手机实机安装及旧生产失败任务重放没有执行；均不由此扩入本轮施工。

## 6. 修复与独立复审

初始审查：F01原判据为V06及07§7.2。反证使用官方runner、受控SDK/真实Loop与DB，Main实际_invoke_tool返回字符串error，预期契约测试失败，日志位于.hermes-dev/noting-fixed-tools-20261024/verification/permission-error-contract.log；无模型收费请求、生产写。已向主会话集中交回，待其提案。无退回补审历史。

F01关键研讨链补记：主会话同意07§7.2偏离，提议在同一权限owner新增标准scope_denied回执builder，保留字符串诊断API；Loop/registry/inline/executor拒绝复用，post-hook诊断仍是字符串，不改其它plugin/通用scope/finish混批错误。Verification依据原V06认可方向，要求解析前tool_call/tool_search拒绝也覆盖、prechecked invoke不旁路、零副作用、合法混批/拒绝后合法调用继续。未改变规格；待实现版本与全部路径证据后关闭。该统一回执是需在final-delivery及最终汇报摘要的实质工程收敛，不能称原先已完全符合。

证据补齐：V32原缺口由主会话定向运行当前Web589df02的controller-context-compaction.test.ts关闭，50 passed/0 failed；Verification亲核三源码及日志SHA四项全真，未复跑无关前端套件。发布准备代码已亲读、439文件集合与tar SHA独立相等；未执行发布或任何云操作，不将准备态称生产通过。

初审整包交回（2026-10-24）：全范围V01–V32已逐行核查并有可回查判定；24符合、3有依据不适用（V21–V23旧完整UI项目不属本轮新增范围）、1违规（V06/F01）、4证据不足（V17/V18/V19/V28）。F01根因及主会话方案已评审但未收到修复版；此时无关闭证据，不将方案认可冒称缺陷关闭。F02–F04分别对应真实链路、明确长样本和最终收尾。按套件，修复后应由全新独立审查者重新建立全轮判据并核旧问题/影响；本次有效反证、源码核查与指纹材料可复用，不能只复跑问题清单。

### 全新独立复审记录

新审查者 `/root/fixed_tools_reverification`，Core `1ea38ef16addaac2cb441029e38f07578d3738dd`／Web `589df02706d3c6738789ff97fcb652a0bf76c398`。完整阅读两门禁相关Skill，先按冻结56b7ebc及授权追加3ce7517原始规格建立C01–C11并落盘第2节，再读代码／测试／CLAUDE／plan／历史报告。全轮覆盖矩阵见第3节新表；没有仅复测旧问题或使用主会话方案反建判据。

原F01（计划F02）研讨链仍沿初审保存：固定07§7.2 → 原错误结构反证失败 → 主会话提案由同一policy builder统一且保通用错误／诊断字符串 → 初审按原V06认可方向 → 1ea38ef实施 → 本次全新审查亲核全部接线与47＋9有效证据，再用原独立反证在当前HEAD取得1 passed，关闭。没有改变规格；此统一模型可见拒绝回执是最终汇报须摘要的工程收敛。

长样本C11已关闭：actual kimi-for-coding Main140765／首Noting143828 input，7HTTP200，184条N46保留，8维护＋1独立finish，合法Snapshot与Framework及资源释放，独立后验`reverification/independent-model-audit.json`支撑。短补样`run-short-20261024-013228`14条准备历史的summary从约1096 tokens增至4111，原生would_grow／aborted正确拒绝，removed>0断言停止，未进Idle／Noting；这只属于如实保留的取证失败，不降低正常完成判据。主会话已安排在同总50HTTP预算内增加合法可缩准备历史补取证，判据／产品Task／Root／Schema／保护不变。

本段为补齐Show前的阶段记录：当时尚未形成最终PASS，R01仍开放。发布前保护与能力已符合，生产切换和真实运行验真留后续独立Validation闭包；本审查不提交、push、部署、发收费API或操作可见UI。最新门禁结论见本节末尾及第1节当前汇总。

发布能力补证：root随后实际执行仅只读`release/deploy.py preflight --target 1ea38ef...`。本审查亲读`release/preflight-receipt.json`及`root-preflight.log`：phase=preflight_passed，旧HEAD与Web/Gateway运行均e9de406，目标1ea38ef，两service active，Web活动0／Gateway活动0、微信connected，host/alex/study三库保护指纹、24配置指纹、Secretary439／Dashboard67文件已读，cloud_runtime_writes=0、production_model_requests=0。没有stage/apply/停启，故只补强C08发布前能力，不改变生产未上线结论；正式apply仍应重做瞬时空闲和指纹核验。

短链补证复核：`run-short-20261024-013830`完整16HTTP200，actual kimi-for-coding/high、原Alex SOUL／父子wire相等；raw response独立重建实际Noting History2、Maintain15（9次非法action参数被Harness拒绝、随后6次成功）、独立finish1。快照提交1792777334.725528→父压缩开始1792777334.727995→durable_commit_succeeded且completed 1792777370.139622→Framework发布1792777370.146303，后续Main正确承接已完成和未完责任；来源校验、pointer及资源关闭通过。此关闭R01中的History／Idle／正常完成／承接部分，仍保留notebook_show真实0的唯一缺口。已向root交回该事实供其提出补证方案，未以模拟四工具覆盖或原Schema出现就判实测齐全。

R01补证方法研讨：root提出保完整默认Noting Task／原Alex Root／tools／工作Notebook，仅在新任务合法后续control或未finish的原生continuation明确请求“inspect the complete current working Notebook, then continue the same task”；不改Schema、不强制tool_choice、不伪造工具结果、不复活已完成child。Verification依据原C07及用户要求“能否调用四工具”认可该方向：规格没有要求每个Noting工具都必须自然触发，不能新增“Show只能自然触发”的产品要求；自然误调频率针对Main，与确定性／明确请求的可达性试验分开即可。关闭仍需实际原生接缝、真实模型Loop→SDK→Store的Show成功及正常finish/Commit Gate；若声称Show读到本任务未提交修改，须有同child成功维护回执和对应entry/version。本评审不改判据／产品规格，也不将方案认可当分支已经通过，待T3实际证据。

R01实际接缝提案复核：T3给出从已验隔离DB只读backup到新Profile、恢复Main新进度→正常Idle全新child，首个真实维护成功且未finish时一次`AIAgent.steer`的完整方案。Verifier亲读`interrupt_control.py:276`、`tool_executor.py:1244`、`agent_runtime_helpers.py:3759`、`pending_steer.append_steer_row`及`prompt_builder.steer_user_row`：它沿正式新role=user/display_kind=steer持久追加，不改既有tool结果／父prefix，不是复活完成child。root将控制文案简化为只包含模型可见对象，去除内部commit/publish说明及版本比较任务；内部观察器继续核entry/version/父旧Snapshot。Verifier确认可执行该方法，仍待真实Show及正常完成后才关闭R01；没有产品规则或数值容忍率调整。

发布执行器保护补强定向复核：root在ignored `release/remote_release.py`的TABLES增加`secretary_notebook_item`、`secretary_notebook_snapshots`、`secretary_notebook_pointer`、`secretary_notebook_local_state`，名称与正式schema一致，沿同一只读事务全行类型保留排序SHA；三库完整SQLite backup、0600及失败不覆盖机制未变，selfcheck的动态表集亦包括这四表。`root-notebook-protection-selfcheck.log`／`root-notebook-protection-dry.log`通过，Verifier重算当前payload与新dry-run SHA一致、bundle/439静态/依赖绑定皆真。旧云preflight仍保留原时点，只能证明当时旧表集；正式stage/apply须按新脚本重新预检，实际四表不变由部署后Validation核。C08发布前结论保持，无产品或冻结检查变化。

Show补证取证事故（R01保持开放）：`run-short-20261024-015853` request11已真实Show，观察器及实际返回证明same child未end_requested、父Snapshot未变，读取5条新维护版本；request12的finish_noting仅接受为end_requested。此后原生收尾请求被进程内硬编码short40分类上限阻断，当时总计47/50；不是HTTP错误或模型权限问题，不足以证明原生Turn正常返回／Snapshot提交。root决定不热patch、不复活原child，让失败正常回收；原件保留为Show可达与结束请求事实，不能计Commit成功。root承认内部分类额度未预留收尾，提出将新测试护栏统一为总70／short63／long固定已用7、计数47不归零，只用全新隔离任务重做同一已审Show分支，并先做预算边界零请求自检。Verifier确认这是本地取证工程修正，不是用户预算或冻结十检查阈值调整，也不改变C07判据；当前仍等新样本真实正常完成后才关闭R01。

该旧样本随后完成失败回收，Verifier独立核`result.json`／原始事件：12HTTP均200，Show-before-finish及父Snapshot不变为真，finish回执仅end_requested，outcome.status=failed／committed=false／snapshot_id=null，snapshot_committed事件0，child_resources_released=true。独立收据`reverification/show-budget-failure-audit.json`。它作为真实失败边界的有效证据，支持“finish接受不等于提交、一般API错误不伪报快照、失败资源释放”；不计R01成功样本，不隐去额外成本。

**最终完整复审与R01关闭（2026-10-24）：** 全新受控样本`run-short-20261024-020652`使用同1ea38ef产品、原Alex SOUL及Root／tools／完整默认Task，正常Main新进度后由原生Idle创建全新admission／child。8HTTP200，真实同一child调用History1、Maintain3、Show1、Finish1，全部成功；只追加一次已评审显式steer，不回填默认Task自然统计。Verifier独立解析raw response工具名及Usage，并只读实际SQLite核一条持久steer位于tool结果之后；原有消息没有改写。Show实际`view_kind=working`，entry3和1的version／fields等于当时Store工作态，版本不同于父已提交Snapshot；Show发生在end_requested之前且父Snapshot不变。然后同任务正常单独finish、原生Turn返回、Commit Gate提交合法Snapshot／pointer_changed=true、child资源关闭。快照事件1792778896.4868789→父压缩开始1792778896.489551→durable完成1792778951.935446→Framework1792778951.942698；实际DB publication row89早于Framework row93。默认成功短013830同样独立核row66<70。对应`reverification/independent-model-audit.json`、`show-completion-audit.json`、`native-framework-db-order.json`。

截至本次取证，累计真实HTTP55（含已失败／准备探针与summary，不归零、不抹去），低于root修正后的内部70护栏；其中最后8次用于显式Show完整分支，没有追加长研究。默认短9参数拒绝、额度截断旧Show失败及长任务8创建0错误均原样保留；没有自行修改Schema／description／业务validator来换取通过，也不依据一次成功声称普遍零错或最大窗口实测。

全范围C01–C11当前11符合，0违规、0必要证据不足；原F01（计划F02）及R01均关闭，无新增范围内产品缺陷。发布前执行器Notebook四表保护补强已定向核，当前bundle／439静态／Schema／Prompt／机制证据指纹仍绑定待审Core1ea38ef与Web589df02。原初审完整32条和其失败反证、各阶段发现／提案／评审／版本／关闭证据均保留。**Verification门禁通过，进入独立Validation。** 最终用户结果、云端stage/apply/服务目标版本及数据前后不变仍由后续独立Validation和root最终判定；本PASS不代签尚未发生的生产部署。本审查只修改verification.md和获准ignored证据，独立重跑原反证1项，其它有效证据按SHA复用；没有收费API、生产写、SSH、可见UI、提交或push。
