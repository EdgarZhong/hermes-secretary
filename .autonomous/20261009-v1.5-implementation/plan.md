# 本轮实施计划：20261009-v1.5-implementation

## 2026-10-09 V1.5 授权文档修订（不新增 V1.6）

本轮获用户明确授权，仅把已定稿的 C14–C17 写入现行 01／02／04 与项目AGENTS／CLAUDE／README／索引／计划，并在 GitHub main 提交一次文档改动。D01 唯一 Native/External 最近实际请求来源标记（Force 内存、Idle/Resume 现有 model_config）；两 Profile 各自正常结束工具、最多5 Turn、超限仍提交有效 Snapshot 与特殊框架原生父压缩；Snapshot termination 三态只供审计。维持 C05/C11 父前缀与 Child 持久化/独立 dispatch 职责边界。项目 AGENTS 允许必要自主收敛不断工，但强制 CLAUDE 顶部看板和下次用户交互优先汇报，不改 Codex 全局规则。**尚未授权恢复编码、模型测试或独立验收。**

## 目标与依据

依据 index.md（snapshot-index.md 为同文件链接）及 baseline.txt 冻结树中的 01、02、04、AGENTS 与会话授权。目标为 V1.5 增量、V1 未改要求、首轮 Full provenance 缺口全部落实，经独立 Verification 和官方 Dashboard 真实模型 Validation 关闭。先精确回退混合 Prompt，再使主对话→History/Notebook→Noting→Snapshot→Reminder/Proposal 的纵向路径完整。公开 main、本机隔离状态、官方 PM 3.14.7、现有锁文件；只在本轮范围内本地提交，不部署云端或触碰生产状态。

## 覆盖与任务

| 要求/口径编号 | 任务和正式路径 | 实现负责人及白名单 | 依赖和接口 | 验证方法 | 用户场景 | 完成条件 |
|---|---|---|---|---|---|---|
| M01/M19、04 §1.4、V1 原生 tiers | T0 精确回退未授权 SECRETARY_GUIDANCE，再加入附录 A 两独立模块 | Prompt Agent；agent/system_prompt.py | Git 对照 5346cd→7533173 仅 8 行增量；先完成回退并留证再进入重建 | Git diff 留证、native tiers 回归 | S01 主对话指导 | 未改原生模块，无混合残留，精确英文 |
| M02/M04–M08/M25、02 §1/§2/§6.2/§6.4/§6.11 | T1 Full/History：native DB→有效路径→Prelude+逻辑节点；History identity read | Foreground Agent；hermes_state_secretary_foreground.py、hermes_state_secretary_identity.py、hermes_state_secretary_schema.py、hermes_state.py（仅 facade/schema 必要接线）、hermes_state_sessions.py（仅原生 current context 窄接线）、tools/session_history_tool.py；对应 tests/hermes_state/Secretary 与 tests/tools/test_session_history* | 与 T2 约定 capture_secretary_prelude API：实际 root Prompt+tools+source/session，不创建版本史；所有 Full 消费者跳过 Prelude | SQLite 真路径 rotating/inplace/branch后压缩/rewind/edit、system/source identity 失败/越界/重复、Anchor/Snapshot/Force 不变量 | S02 跨压缩召回；S06 Full 审计 | 真实最新来源、唯一 Prelude、身份一一映射、复合唯一特例、History 无 scaffold |
| M03/M08/M11/M19/M20、02 §1.9/§3.5/§4.1–4.3/§5.7/§6.6 | T2 Main 资格→最新所属 profile config→tools+dispatch+Stable 同步→native Prompt restore/cache→真实 request | Prompt Agent；agent/system_prompt.py、agent/turn_context.py、agent/agent_init*、agent/session_persistence.py、agent/conversation_loop.py（仅 capture 调用接缝）、secretary/noting_surface.py、secretary/noting_runtime.py（仅资格和 read gate）、tools/notebook_tool.py、gateway/agent_cache*、gateway/run_agent*.py（仅 cache/config 窄接线）、相应 tests/agent/ 与 tests/secretary/test_noting_surface.py | T0 先行；T1 Prelude API 后接线；T3 local toggle 不重建 | 实际 provider-neutral request 正反切换、Warm/Cold/pinned/Compaction、auxiliary 构造/继承/刷新、dispatch 与 schema 配对 | S01/S03 全局切换；S04 局部关闭 | History 必有；Notebook 仅 Main+global；local 不动字节；旧 Prompt/Schema 无泄漏 |
| M09/M10/M12–M18/M21/M22/M23、02 §2.5–§3.12/§4/§5/§6.8–6.10/§6.18 | T3 共享 Slash→Noting local state；Candidate/Schedule两句+获授权工具面变更指示；five-form schema；Proposal main 自主搜证 | Workflow Agent；hermes_cli/cli_secretary_commands.py、hermes_cli/commands.py、hermes_cli/cli_commands_mixin.py、gateway/slash_commands_secretary.py、gateway/slash_commands.py（仅共享分派）、tui_gateway/methods_secretary.py、tui_gateway/methods_slash.py（仅共享分派）、secretary/noting_child.py（原两句保留；C11后缀工具列表/Schema与完整父前缀冻结尚待恢复实现）、secretary/noting_tools.py（expression）、apps/desktop/src/lib/desktop-slash-registry.json（生成同步）、对应 tests/cli/tests/gateway/Secretary/tests/tui_gateway/Secretary/tests/secretary/notebook_render/noting_child | T1 identity read、T2 门禁；其余 inherited Scheduler/Reminder 不重设计；共享 catalog 优先 | Slash 正式入口持久可见、local schema 字节不变、附加要求/候选 identity/无 source 拼贴、Schedule 五类与 timezone、审批负例 | S04 局部；S05 提案审批；S07 Reminder | 旧入口不生效；提案自主检索、修改不批准、明确批准范围执行；Candidate 结案归档 |
| M01–M25、C01–C04、V1 全继承 | T4 主会话 review/接线/文档及针对性证据 | 主会话；根三文档/plan、必要微小集成修补；深入实现重新委派 | 三实现报告七项必答；白名单冲突先协调；主会话拥有共享 plan/CLAUDE | 读实际返回及上下游，定向补集成证据，真实模型正式路径 | S01–S07 完整旅程 | 所有范围内缺口关闭、提交可回退、证据匹配版本 |
| M24、04 §7.2–§7.4、02 §6 | T5 独立 Verification + 一次必要扩大本地回归 | 全新 fork_turns=none reviewer；产品只读，verification.md 和独立证据白名单 | T4 收敛提交；独立重新提取全部要求；主会话统一安排检查/回归范围和执行方 | 独立矩阵反证；保留十类检查；按实际影响 Secretary/Agent/Gateway/Slash/State 完整相关分区，不无差别全套 | S01–S07 覆盖机制 | 无违规/证据不足；平台限制有依据；大型执行记录版本/范围/次数/耗时 |
| M21–M25、04 §7.3、继承公开验收入口 | T6 官方 Dashboard+localhost Gateway+真实 Main/Noting 模型用户验收 | 另一全新 fork_turns=none validator；产品只读，validation.md/隔离 runtime/证据 | T5 通过；先写独立场景供主会话过目；内置浏览器，不 Computer Use | 用户输入到响应；跨 Compaction/source、全局/局部切换、Proposal 反证与批准、真实 Candidate 归档、Schedule idle/busy、Full 来源 | S01–S07 | 适用场景全部通过/有依据不适用；构建/CLI/mock 不代替 |
| 所有完成标准 | T7 delivery-evidence-review 最终判定 | 主会话；final-delivery.md、CLAUDE/README | 两门禁关闭、整改清空、不产生新缺口、证据对应当前交付 | 原始要求反查实现/两门禁/用户结果 | 用户复核交付记录 | 完成目标才标 complete；未关闭持续修复 |

## 当前状态与编排

动态任务状态唯一记录在根 CLAUDE.md；本计划仅描述机制、接口和证据，不另建并行动态看板。

并行分组：T1、T2、T3 共享工作区白名单不重叠；T2 先执行 T0。T1 负责 DB native context 最新值/API，T2 负责实际请求 capture 和所有 Prelude 消费者中的非 DB 调用适配；若同文件需求出现，先回报由主会话协调。T3 不修改 read gate / root Prompt，只依赖公共配置/身份函数。实现 Agent 不改根文档、plan 或权威依据，不自行提交、不派生；报告及证据落各自 `.hermes-dev/evidence/v1.5/{foreground,prompt,workflow}/`。主会话接收后集中 review，不重复跑实现者有效测试。

独立门禁在整轮集成收敛后派遣；旧报告仅对照，不取代重新提取。扩大测试由主会话统一一次安排，可与 Verification 独立核查并行；失败仅复测受影响项，不重复全套。

## 缺陷与整改

| 问题编号 | 要求与触发条件 | 当前事实与影响 | 优先级及理由 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|
| F01 | Full root/Tools Prelude、R015 | 首轮 Full 无 root provenance，工具审计新增要求 | P1 必须机制 | T1/T2 | 真实最新请求源及恢复，Anchor/History 不污染 | 主会话 review 中 |
| F02 | next Pre-message Context 同步 | 起点先读取 cached Prompt 后更新工具 gate；有陈旧配对风险 | P1 首请求一致性 | T2 | Warm/Cold/global on↔off 实际 request 对照 | 主会话 review 中 |
| F03 | Branch 后继续压缩有效路径 | T1 initial-targeted.log 真实反证：in-place顺序 early,tail,new-boundary；rotating continuation被 inherited fork marker过滤，遗漏boundary | P1 身份/状态安全 | T1 | 修正Secretary路径/tail重定位并复测，保留native边界和Anchor/Snapshot/Force契约 | 真实反例已修复并定向复验，待独立核查 |

| F04 | Codex native loop 与继承Noting权限 | managed MCP目前只读，原生循环旁路task-local mutation/compact_parent且无dynamic-tool handler | P1 正式维护能力/权限不可冒称支持 | Prompt只读研究，主会话后续串行分派 | 原生协议可验证接线，不降级runtime/新bridge/第三失败条件 | C07撤销此可选通道目标，未修复、不再派遣 |

## 取舍、快照与续接

- 文档冻结 d5acc2cc27c6053ff198448fa3502bd8dd47e415，原附件 SHA256 3e7dd22ecd196527136a9051809f93e2ff177535cc70da622519ef397df85bbe；三核心文档和同步 01/02 已同批提交，AGENTS 仅入口变更。
- T0 对照原首轮基线 5346cd094b6a1bb6c6d9ce69e83b3a1570cf46bd..7533173，agent/system_prompt.py 仅 8 行混合增量；必须先回退核查再加入新模块。
- 历史04 §7.4 曾误写 M01–M24；现已统一 M01–M28，须覆盖 M25 Foreground 节点不变量以及 M26–M28 新定案；这属于现行规格对齐。
- 本轮保留首轮失败/跳过/macOS-only/未测真实缓存命中率边界，新的证据不得夸大；环境或工具阻塞如实记录并持续尝试范围内可行解决。

主会话必要白名单协调（实现边界，非规则变更）：T1 增 hermes_state_secretary_notebook.py / hermes_state_secretary_noting.py 的 Full 消费者 Prelude 适配；T2 增 agent/inline_tool_executors.py 的 notebook_show 实际 dispatch 与 secretary/noting_runtime.py 的 Full 迭代适配；T3 增 tui_gateway/methods_tools.py 的 Secretary dispatch/bypass 集合与 gateway/run_busy.py 的既有 idle allowlist，以及 tests/hermes_cli 的实际目录。各 Agent 仍不修改其他 Agent 的文件。

T3 定向测试发现 compute-host 共享路径：授权 tui_gateway/host_supervisor.py / tui_gateway/compute_host.py 仅既有Secretary路由集合纳入 slash.noting，沿用 slash.notebook 策略，不扩 busy/admission 机制。

T2 隔离补充：agent/cache_parity.py 非Noting fork构造时剔除本轮新增Main两个指导与Notebook工具，保留其他原生合法tool/cache/lifecycle；Noting专用fork必须保持完整父头部工具Schema及root/消息前缀；当前首次响应后扩child.tools的旧行为按C11待修，新的工具列表/完整Schema只追加在task及后续新增系统提示中，dispatch独立受限。依据04 §2.2/§3.1，不将主开关刷新传播至运行中的辅助runtime。

T2b 历史委派（已按C07撤销并恢复专属文件，不继续）：白名单 agent/codex_runtime.py、agent/transports/codex_app_server_session.py、codex_app_server.py、hermes_tools_mcp_server.py 与对应 Codex/MCP tests。接口复用 pre-message 冻结资格和 capture API missing_reason/partial_context；现有 managed MCP 传递所属 HERMES_HOME/Session/runtime资格，schema嵌套identity保真，Cold无法证明采用新developer时沿用native退休重建。T1允许 capture root/tools显式None，但必须reason，partial不得冒充完整来源。

2026-10-09授权修订C06–C09：取消T2b可选Codex接线与F04运行目标，保留本地未完成证据。此前“从首请求改写顶层工具Schema”的解释已按C11撤销：所有请求保留完整冻结父快照，包括头部工具Schema；新可用工具列表/完整Schema只追加在task及后续新系统提示中并声明以此为准，dispatch受限。模型/API/provider直接使用Hermes原生，只在中间层保证上下文复用，不增加独立路由。Main/Noting真实集成和Dashboard统一DeepSeek官方Anthropic/deepseek-flash思考模式；缓存从Hermes真实请求/响应逐次取证。新补充冻结提交覆盖01/02/04/index及根核心文档，原d5acc历史保留。

C10暂停：不继续代码修改、模型调用或验收。最新详细接续编排、修改边界、依赖和完成条件只在根CLAUDE的H0–H8看板，不在本计划另建动态看板。保留的普通实现与最新文档一起提交现状快照；本轮以暂停final-delivery交付，用户恢复时新建接续轮次。

C12历史交接更新：当时外部Agent runtime继承仅列为04 §4.5 D01待论证；后续C14已定稿为最近真实请求的Native/External唯一准入；不启动独立模型路由或外部执行器兼容。原V1/V1.5与实施的静态核对结论、P0已定稿接线和后续编排只在根CLAUDE；查实的头部Schema变化属于实施/测试预期/审查偏差，不能由这一规格缺口合理化。现行C05/C11保持有效，全部实施和验收继续暂停。
