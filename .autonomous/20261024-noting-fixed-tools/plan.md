# 本轮实施计划：20261024-noting-fixed-tools

## 目标与依据

以snapshot-index.md和baseline.txt定位冻结用户需求／07及白板／编码指导。核心纵向路径：合格Main正常构造或恢复→完整固定两Schema且Main禁用提示→可信白名单拒绝非法维护→Idle或原生联合入口冻结父prefix→Noting仅四工具、任务无重复Schema→正常finish／Commit Gate→按已有时序压缩及Framework→Main继续使用。今日既有微信／标题／wire／时间／Web修补一起上线。

完成条件：所有适用C01–C11落实；Schema canonical SHA不变；正式机制／失败及跨协议回归；Alex隔离真实kimi-for-coding轨迹及Main自然误调计数／确定性拒绝分开取证；两个独立门禁通过；本地生效改动提交推送，实际云后端／Web版本和保护数据核验成功。无生产旧行恢复或旧任务重跑。

## 覆盖与任务

| 要求/口径编号 | 任务和正式路径 | 实现负责人及白名单 | 依赖和接口 | 验证方法 | 用户场景 | 完成条件 |
|---|---|---|---|---|---|---|
| C01,C04,C05 | T1 顶层注册与身份权限：Main surface／registry→原生validator／sync／concurrent／invoke；child冻结工具与四名字 | fixed_tools_runtime；secretary/noting_surface.py、tools/secretary_dispatch.py、secretary/noting_child.py、agent/cache_parity.py、agent/tool_executor.py、agent/turn_tool_validation.py、tools/tool_search.py（仅固定工具direct接线）；tests/secretary/test_noting_surface.py、tests/secretary/test_noting_child.py、tests/agent/test_secretary_noting_dispatch.py、tests/agent/test_secretary_main_execution_dispatch.py及新tests/secretary/test_fixed_noting_permissions.py | 不改noting_contract.py；不改Prompt／任务builder／wire接缝（T2 owner）。若需扩白名单先与root协调 | 正式Loop＋真实DB受控SDK；所有两工具Main拒绝、四工具外Noting拒绝、直接invoke／混合finish／普通子Agent／开关组合；拒绝前无副作用 | S1 Main普通工作与误调；S2 Noting正常维护；S3越权拒绝后恢复 | 原定义完整顶层且不折叠，执行权与advertise分开，父子tools不变、child仅四工具；本包测试通过 |
| C02,C03,C05 | T2 Prompt与任务去重Schema：Main Notebook指导、Noting authority／control／continuation→builder→所有协议请求 | fixed_tools_prompt；agent/system_prompt.py、secretary/noting_prompts.py、secretary/noting_tools.py、secretary/noting_request.py、agent/chat_completion_helpers.py、agent/turn_request_assembly.py、agent/iteration_summary_messages.py（仅退出dynamic glue并复用原生normalizer）、secretary/noting_recovery.py（仅显式恢复freeze前补旧pin缺失canonical定义并标来源）；tests/secretary/test_noting_dynamic_tools.py、test_noting_dynamic_fallback.py、test_noting_request_protocol.py、test_noting_recovery.py、test_r3_child.py（仅去重复Schema断言）及新test_fixed_noting_request.py | 依T1接口；现有_bound_store／维护逻辑不改；Schema／description只读；三核心／规格root独占 | 正式native SDK序列化含父多模态、续Turn、fallback、恢复；无messages[*].tools和callable_tool_schemas；各次root/tools/frozen消息相同；Main提示与任务权限准确 | S2正常无重复Schema工具可用；S4续跑／fallback／冷恢复 | 初始及续Turn去Schema，旧动态接缝退出，前缀归一化仍沿原生；不改Provider协议、预算和结束条件 |
| C06,C07,C11 | T3 隔离Alex真实端到端与模型行为：正式CLI／RPC／AIAgent／Idle Timer／Noting／原生Compaction／DB／Framework | fixed_tools_e2e；产品只读，仅.hermes-dev/noting-fixed-tools-20261024/e2e/及仓库外独立Home/runtime/workspace；可读Alex冷副本配置／Persona和凭据但不改源，不启动真实MCP外发 | 先交完整准备方案（配置差异、公开入口、请求预算、数据保护）；T1/T2主会话接收后root通知才发模型 | 实际kimi-for-coding High，Alex完整业务Prompt／Persona保留，父子实际wire哈希；自然Main样本与明确越权样本分开；四工具实际调用／finish快照／压缩后Framework／后续恢复 | S1–S5 从普通对话经Idle正常整理压缩到后续检索／使用；S6拒绝和纠错；S8真实N46长前缀任务切换 | 正常任务完成，真实调用与合法持久化，不以forced冒成功；可复用接口证据留受限raw和脱敏receipt |
| C08,C10 | T4 今日修补复核与联合发布：已审599d114、UI589df02＋本轮新实现→主机空闲／快照／固定版本→单后端及双SPA→实际健康与保护数据核对 | root；三核心、07／白板、ops、本轮plan与最终交付；云部署仅正式首尔SOP范围 | Verification通过且Validation本地用户链路通过、放行部署；部署后补S7关闭最终Validation，实际代码／dist／PM绑定固定；不重建锁、不发生产模型测试／渠道消息 | 复用已审包有效证据；交叉影响定向回归；部署前后配置/SOUL及历史／排期／绑定指纹、服务版本、静态集合／SHA／API／WS／微信连接 | S7 正式服务带全部修补上线，用户状态保持 | 生效版本与目标一致，无码／环境漂移，隔离值未进入生产；回滚点保留 |
| C09 | T5 独立Verification与Validation、最终目标判定 | 全新Sol/high、fork_turns=none独立两Agent；分别仅verification.md／validation.md及指定证据；root最终delivery | 集成收敛后按轮一次派遣；Verification先独立判据落盘，全部阻断关闭才Validation；Val计划先过目 | 符合性矩阵＋公开入口用户验收，复用同版本真实模型取证但不只复跑测试；不得降判据 | 全范围S1–S7 | 两门禁全适用项通过，无违规／不足／未执行；final-delivery按六节模板 |

## 当前状态与编排

| 目标/任务 | 机制实现 | 正式接线 | 针对性验证 | 用户结果 | 当前负责人和下一步 |
|---|---|---|---|---|---|
| T1 | 已实现并亲审 | 正式Loop／执行器／invoke已核 | 权限32、surface33、child38等通过 | 待真实模型 | root接收；真实样本待T3 |
| T2 | 已实现并亲审 | native normalizer／SDK／恢复已核 | 请求32、恢复20等通过 | 待真实模型 | root接收；真实样本待T3 |
| T3 | 准备方案已接收 | Alex隔离原生入口 | 零请求准备通过 | 待真实模型 | 批准50HTTP上限（短28／长22含内部重试），固定受测版本后开跑 |
| T4 | 旧包已审 | 当前未部署 | 有效证据复用 | 待上线 | root核部署环境与产物；先只读 |
| T5 | 未开始 | 未开始 | 未开始 | 未开始 | 集成后统一安排 |

T1、T2、T3白名单不相交；共享变更串行交root。不用worktree，不让子Agent提交／push／部署或派生。每包只在真阻塞／跨包接口决定／预定整包交回时发消息，不流水账；产品UI仅自建隐藏IAB，禁止用户已有页面／桌面／显示／焦点变化。

主会话亲审每包要求覆盖、指定机制、正式接线、失败状态与证据；不以复跑代review。真实调用由T3单一owner，先准备初始预算（建议Main约3–5Turn＋一轮正常Idle维护与压缩，最多30HTTP尝试作为初始成本控制；非产品限制），不足则根因复盘／记录后由root决定，不自行反复试错。两门禁复用同版本证据，必要反证仍从真实入口。

## 缺陷与整改

| 问题编号 | 要求与触发条件 | 当前事实与影响 | 优先级及理由 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|
| F01 | C01–C05原实现动态声明与重复Schema | 已知旧实现非本轮目标；固定prefix新增工具须同步权限与Prompt，不能只移tools | P1核心 | T1＋T2 | 全纵向路径／父子wire等价与硬拒绝、无重复Schema | 机制关闭，待真实模型及门禁 |

## 取舍、快照与续接

- 冻结基线见baseline.txt：保留本轮user-request、索引、已更新07／白板及CLAUDE；README／AGENTS未改但在基线树内。
- 两份原有未跟踪docs调查／算法稿不属本轮，保留不提交；前端589df02当前干净。产品Schema canonical SHA见索引／ignored before收据，禁止修改。
- 角色提示及去Schema依据用户最后确认，不继续讨论已否决的description修改或重复Schema；不改Main／Noting其它业务任务、Snapshot／Idle成功前置、预算／强制结束或来源显示。
- 测试Home与cwd必须仓库外，隔离运行不可接生产Gateway／排期／MCP写工具；凭据只留受限副本／内存，raw wire及Persona只留ignored0600文件。
- 本轮开始前代码71533a05ae；今日已审修补599d11467c／Web589df02。发布前Verification与Validation本地链路未通过不部署；部署后补真实生产只读核验，再关闭全轮Validation；全部授权范围包括安全正常停服务／版本与dist更新／启动验真，不包括改用户模型、线上测试阈值、历史修复或旧Noting重跑。

- 2026-10-24 root接口收敛：T1获tools/tool_search.py单点direct集合扩展，T2获turn_request_assembly.py／iteration_summary_messages.py动态glue退出；均属满足冻结机制的必要接线，非Schema／产品权限变更。旧恢复原材料fallback保留，不能因新Task去Schema加拒绝门槛。

- 用户追加C11：真实kimi-for-coding必须验证超过N38的长前缀，选已有N46点；不先压缩，记录实际Usage而非K3推算。T3准备时给扩展成本方案，仍需root接收实现后才统一开跑。

- root接收T1/T2：亲审顶层注册／ToolSearch direct／validator修复前拒绝／sync与concurrent／invoke guard、原生normalizer、初始续Turn去Schema与旧恢复边界；Schema owner无改。集成4文件116通过（初次命令中的不存在idle路径未被runner发现，已改用实际两文件另跑，不把遗漏记通过）。新恢复旧pin的一次tools前缀变化已明示来源。阶段提交仅机制检查，不宣称真实模型或部署验收。

- root补齐README稳定架构及AGENTS缓存原则，去旧动态声明表述，来源为已批准C01/C03/C05，未改变检查规则／阈值。Idle两文件43通过，Web dist439files绑定589df02，tar/manifest保ignored。
