# Hermes Secretary 项目主看板

## 自主口径收敛 · 待用户追认

**暂无待追认项。** 来源先结算、Candidate最后处理及控制Prompt体量仍沿用户R3-019既有要求；本次Verification没有新增产品语义、修改权威规格或降低门禁。

**已由用户确认并落地（2026-10-17）：** Schedule Table 的 `timezone` 字段属原规格空白（07 §6.1 只列字段名、未定格式）。实测实现按 `kind` 取两个来源：`once` 从 `run_at` 的 ISO 偏移反推得 `UTC+08:00`，`interval`/`cron` 取进程本地时区得系统缩写 `CST`；即使配置 `timezone: Asia/Shanghai`，`once` 仍是 `UTC+08:00`，属结构性不一致而非缺配置。用户确认采用「条目归属时区」口径：三种 `kind` 统一取 `hermes_time` 当前生效时区，配置了 IANA 时区返回其名称，未配置时返回 `UTC±HH:MM` 固定偏移，不再从 `run_at` 反推。影响范围：模型 `list`/`create`/`update` 返回的 Schedule 条目与 Web `ScheduleEntry.timezone`。**是否已实施：是。** 改于 `secretary/scheduler_time.py::schedule_timezone`，同步 07 §6.1；新增 2 项 kind 无关性测试，`tests/secretary/test_r3_scheduler.py` 49 项通过；不计入本轮 Verification 结论。


## 已完成代码修复 · 冷态 Reminder 与 Files Profile（2026-10-18）

**用户指令：** 拉取远端最新提交，根据最新文档修复两个 bug。依据为 [08](docs/08-profile-scheduler-files-clarification.md)；修复范围是常驻 serve 对冷态 Instant Reminder 的自动恢复投递，以及固定 Files Profile 与请求目录归属。既有其他审查问题不纳入本次关闭声明。

**同步与基线：** 两仓 fetch 后均已是远端最新且开始时工作区干净；主仓 `65dbb54e806263814547e5b3602b658f08ed717e`（origin/main），UI `4808500b458f10539115946ca6fb34905c15b6fc`（origin/secretary）。PM `.venv` Python 3.14.7，`uv.lock` blob `2b9135989931cc4ef8a696c9f7371671fe03190e`；不修改环境或锁文件，不为基线重跑全量。既有历史失败与未验证平台保持原记录。

**分工：** `files_profile_fix`（GPT-6.1/high）负责独立 UI 的 Files/导航和后端 `web_routers/files.py` 及定向测试；`cold_scheduler_fix`（GPT-6.1/high）负责常驻宿主 scanner、原生恢复/提醒接缝及相关测试；均不再派生、不提交。主会话维护根文档、复核机制和证据、处理最小集成修补。两个修改范围不交叉。

**完成条件：** 冷态测试先确认 Runtime/Session poller 不存在，再从常驻宿主接缝触发原生恢复及 Main；覆盖 Profile owner、配置关闭、deferred 不唤醒、busy 转 deferred、claim/失败重试及回收。Files 的 root/list/read/media/download 固定同 owner，返回保留聊天 Profile/Conversation，创建/附件不受影响；后端本地目录按请求 Profile 读取。真实 Provider/浏览器现场与受控测试分别报告，不把受控 Provider 输出当真实模型验收。

**当前状态：** 两项实现及证据均已由主会话集中 review 接收，相关回归通过；UI 已提交同步 `524e479`，后端与本记录同一提交同步。未重启用户运行后端，未部署。无新增待追认产品口径。

**Files 验证：** 后端真实隔离 Profile 配置的 RED 显示 `other` 错返 default 目录，修复后 `tests/hermes_cli/test_web_server_files.py` 22 PASS、ruff PASS；校验请求切换不改进程 HERMES_HOME/cwd，缺失 Profile 返回 404。前端 RED 复现入口借聊天 cwd 和返回丢 Profile；修复后相关有效并集194 PASS（Profile UI 14、Profile Controller 13、其他 Files 导航相关 Controller 157、Files 专项10），包含固定root/list/text/media/download、错误不fallback、history/刷新/新标签、首发cwd/Profile/草稿/附件归属；`npm run typecheck` PASS。主会话 `npm run build` PASS（Vite 14.35秒，包体积提示不阻断）；两仓 diff whitespace 检查通过；Files 后端补充 health/no-tmp 2文件0 blocking/0 advisory。未做真实SSH文件访问或浏览器实机验收，不重复全量测试。

**冷态 Scheduler 实现：** `tui_gateway/scheduler_host.py` 常驻宿主扫描，启动即扫描、每轮后约5秒；原生受管理 Profile 枚举加实际启动 Home，按真实 Home 去重，仅打开已有数据库。先验证本地 Main 路由再 claim，消息渠道路由保留给原 owner；deferred 只持久 pending。Instant 沿 `_Resume` 定位／压缩续接／guard／deferred hydration／原生 Agent build 恢复，再使用既有 `_secretary_deliver_claim` 原子接纳；不触发恢复时的自动续跑。内部 background 复用并发 winner 时不重绑客户端 transport，新 Runtime 使用原生 detached/reaper。`web_server` lifespan 启停扫描，恢复中收到停止请求则释放 claim，不新启 Turn；未增加公开 API 或改动数据库 schema。

**冷态验证：** 新增 `tests/tui_gateway/test_cold_scheduler_host.py` 有效并集19 PASS，包含无客户端、无Runtime/轮询器的真实宿主入口、实际回收后再唤醒、B Profile及named launch/default隔离、busy、暂停/删除/关闭竞争、失败构建释放与重试、迟到once/周期推进、claim竞争、messaging防错投、并发浏览器transport、压缩续接及恢复中shutdown。真实 SessionDB/AIAgent/消息见证及deferred自然Turn响应ACK；Provider响应受控，不是外部真实模型验收。相关6文件76 PASS（58秒），完整范围及日志见 `.hermes-dev/cold-scheduler-fix-20261018/handoff.md`；专项初始17项20.8秒，后续仅复测变化路径和新增2项。4个冷态文件 ruff/health/no-tmp 0 blocking/0 advisory；有效证据复用，不重复全量。首次RED为新增模块缺失的收集错误，不冒称旧版端到端反证。

**实际限制：** 未执行真实外部Provider调用、用户现场关闭浏览器后的端到端验收、真实SSH文件访问或跨平台验证；未重启运行后端，不能宣称现场已加载修复。README补充08稳定入口及Files/冷态宿主实现事实；AGENTS通用规则保持不变，顶部待追认区域已恢复到顶部。

## 已完成 · Compaction 恢复指引对齐 History 与前端完成通知（2026-10-17）

**用户确认口径：** 压缩摘要的恢复指引与 `HISTORY_SEARCH_GUIDANCE` 同资格，只看合格 Main（`_secretary_main_read_eligible`），不额外要求 Noting 全局开关；`## Context Recovery` 改为“上一次压缩掉的 N 条消息（区间时间）；`conversation_history` 可检索自本 Conversation 第一条消息以来全部消息（会话起始时间）”，不出现 Session ID / `session_search` / 工具 Schema，迭代摘要替换旧 footer。`compression.protect_first_n` 产品默认改为 0（用户自用 Secretary 也吃产品默认，不单独覆盖 profile）。前端成功 compact 后弹 `Compact completed` 通知并整句高亮；degraded/aborted 仍显示原生 receipt。

**实现（后端）：** `agent/context_compressor.py`（Secretary footer、区间/会话起始时间、`_replace_summary_section`、anchor index 文案）；`agent/context_compressor_summary.py`（记录会话起始 timestamp）；`agent/conversation_compression.py`（按 `main_read_surface_enabled` 注入 `_secretary_history_recovery`）；`secretary/noting_surface.py`（新 helper，`apply_main_read_surface` 复用）；`agent/agent_init.py`、`hermes_cli/config_defaults.py`、`hermes_cli/config.py`（默认 0）。**前端：** `native-notices.ts`（`strong`）、`controller.ts`（`noticeStrong` 透传）、`compaction-read.ts`（成功通知）、`App.tsx`（整句高亮）及测试。

**验证：** 后端 `tests/agent/test_lean_single_aux_call.py` 10 PASS、`tests/secretary/test_r3_config_prompt.py`＋`test_r3_wiring.py` 73 PASS、ruff 通过；前端 `controller-context-compaction.test.ts` 48 PASS、`tsc -b` 通过。

**文档：** 07 §5.2 第 9 条／§8.8／§9.1／§11.2、04 §3.2、02 §1 适用性、根 AGENTS「写 prompt」已同步。

**未完成／注意：** 后端未重启，代码与 `protect_first_n=0` 尚未在运行中的 runtime 生效；后端全量测试未跑；前端全量 vitest 未跑；自动（非手动）压缩完成目前仍不弹这条 notice；`tail_mode`/保尾逻辑未改。

## 已完成修复 · Round 3 Compact 与 Context 冷恢复（2026-10-17）

**用户授权：** 调查 Round 3「实测 conversation history 工具」的 `session.compress timed out; outcome is unknown`、Context 环没有显示转动的 Compacting、原生 compact message 未及时出现在 Timeline，并修复前后端问题；补充要求成功后清理 Composer 本次 slash 命令。等待期间新增草稿仍按现有草稿归属保护。

**现场已确认：** stored Session `20261017_202521_55c52c`；22:07:42.604 开始压缩，22:08:20.079 已 `committed`，耗时 37.474 秒，79→31 消息、粗估 168,459→41,914 tokens；数据库有 `_compressed_summary=1` 的真实 summary。前端 RPC 默认 30 秒超时，不能将其当作压缩失败。

**兼容约束（用户 2026-10-17 再次明确）：** 后端 API 只增可选字段/参数，旧前端及 Hermes 原生客户端通信不受影响；内部调用点保持旧默认逻辑。已同步根 AGENTS；本次精确 anchor 和冷估算分离、无新 API/必填 DTO/数据库 schema。

**用户追加（2026-10-17）：** 后端重启及 runtime 重新 bind 前，Context 必须允许读所属 Session 的原生 usage anchor 恢复估算；只有切换模型或 rewind 使冷估算失效。Notebook anchor 无关。已立即同步 06 §1.13，覆盖旧的 compaction/fingerprint 一概失效措辞。`cold_context_backend`（6.1/high，不再派生）独占后端冷估算读取及原生 usage-anchor 相关测试，主会话接线与最终 review；不放松模型精确计数路径，不新增用户消息或重新压缩真实会话。

**执行：** 主会话只读查后端与真实存储/投影，子 Agent `compact_frontend`（6.1/high，不再派生）修复前端 compaction owner、超时恢复、正式命令成功回收，集中交回后主会话 review。用户现有后端 History/来源及前端 sidebar/layout/theme dirty 原样保留；不重复压缩用户会话、不借 Noting 完成判断压缩成功。两子 Agent 已交回，主会话完成集中 review；代码与定向验证完成，用户要求尽快停止汇报，已停止后续操作。

**结果：** 前端压缩专用等待上限 660 秒（普通 RPC 仍 30 秒，显式 timeout 优先）；既有原生状态 owner 持续观察，完成后刷新真实历史与 Context；成功清理原 slash，保护新输入，失败/不确定/pending 不重发、不误清。真实原生 summary 已核对；原现场“环未转”的直接原因未完整复现，已关闭 first-idle、读取失败及迟到结果时序缺口，不能宣称重新做过真实 Compact。

**冷恢复：** 原生精确 `_usage_anchor` 保持原校验；可选 `_usage_context` 保存原生读数/压缩后估算，按 Session、model、原生 `rewind_count` 校验。首 resume ACK 在 history 延迟加载前即可读盘；Agent 已构建但无新读数继续保留估算。Provider 名称单独变化不清空；只有明确模型变化/rewind 清 Context，不清 Session Total。API 只增可选 `context_available`、`context_invalidated`、`context_invalidation_reason`，旧必填数值和错误码不变，OpenRPC required 清单零变更。原生 Context 计算与估算保存沿正式 rewind 的同一 history_lock 结算，已覆盖并发反证。

**验证：** 前端8个相关文件289 PASS；收窄Provider判据后6项邻域PASS（有效证据复用），新版 npm run build PASS（含TypeScript）。后端子Agent有效并集70 PASS/1环境FAIL（ACP缺acp依赖）；主会话正式binding5 PASS、只读resume7 PASS、账户usage1 PASS、原生选定resume/context/usage3 PASS、生成文件一致性1 PASS。事件目录另一失败为HEAD既有 `review.summary` scanner orphan，已核对发出点集合与HEAD相同。没有全量重跑，不把两项失败写成通过。子Agent5文件与主会话5集成文件ruff/health/no-tmp均PASS，实际index未改。三份核心文档及06已同步；两仓本次改动未commit/push，既有History与sidebar/layout/theme dirty保留。

**真实现场：** 确认Round3无活动Turn并用SQLite备份后，沿原run-native.py启动方式重启两次；首次通过正式session.context_breakdown读取并保存44,743/262,144 tokens（17%，local_estimate），再次重启后的session.resume首ACK在hydrating=true时即恢复同值，页面显示17%及~44,743。最终后端PID30230、端口53445；未发新消息/模型请求/再次Compact。证据及备份：`.hermes-dev/compact-cold-context-20261017/`（verify_runtime.py、native-reading.json、cold-restored.json、context-restored.png、integration-check.log、backend.log、before-restart.db）；原压缩只读回放为`.hermes-dev/compact-observe-events.json`、REST投影为`.hermes-dev/compact-observe-messages.json`。未进行旧原生客户端全端到端实机验收，兼容结论限于契约与相关原生路径回归。

## 已完成 · F01/F04 修复与 F16 真实模型复测（2026-10-17）

**用户指令（2026-10-17）：** 开始实测 F16，修 1、4；拿 F16 新结果和模型行为观察汇报，不擅自再次调优。复测复用 Round 3 Profile。**本轮未改提示词、未改场景输入、未做第二次调优。**

**F01（History 不可读来源仍可提交）· 已修复。** 根因在 `secretary/notebook_store.py::_source_checks_conn`：只用 `get_history_foreground_conn` 取路径，未套用 History 的可见性真值。修复为同一谓词：`model_visible_messages(...)` + `kind == "message"` + `display_kind != "hidden"` + role ∈ user/assistant/tool/system；身份与时间范围都只从该路径取。继承旧版本走原 `_inherited_sources_conn`，未改合法旧版本继承。新增 `tests/secretary/test_noting_source_visibility.py` 5 项（human_only/hidden × uid/range 的公开工具反证 4 项 + 可见来源正控 1 项）。**RED（未修源码）4 failed / 正控 PASS；GREEN 5 PASS。**

**F04（恢复未来排期被推进到下一次）· 已修复。** 根因 `secretary/scheduler_table.py::_participation`：resume 无条件把存储的 `next_run_at` 当 last-run 锚点交给 `schedule_advance_epoch`，未来时刻被当成已过去而跳到下一次。修复：`once` 仍从当前时刻重算；`cron`/`interval` 的存储 `next_run_at` 仍在未来时改用 `schedule_initial_next_run(now)`（与原生 `resume_job` 的未来分支一致），已过去时保留原跳过逻辑。`tests/secretary/test_r3_scheduler.py` 新增 3 项：cron 09:20 恢复保留当天 10:00（原次日）、interval 恢复按 now 重锚（不是 stored+interval）、已过时点仍推进到下一次。**RED 2 failed / 已过时点正控 PASS；GREEN 52 PASS。**

**相关回归（修复后）：** `test_r3_scheduler`、`test_r3_scheduler_time_projection`、`test_schedule_status_lifecycle`、`test_schedules`、`test_notebook_provenance`、`test_notebook_store`、`test_r3_notebook`、`test_r3_history` 共 **261 PASS**；`test_r3_delivery`、`test_web_read`、`test_secretary_read_profile_scope` 共 **41 PASS / 2 failed**；`test_noting_child`、`test_noting_surface`、`test_r3_child`、`test_r3_wiring` 共 **132 PASS / 6 failed**。上述 8 个失败在未修源码 `0dfa26a58d` 上逐字复现（`test_web_read` 2、`test_noting_surface` 4、`test_r3_child` 1、`test_noting_child` 1），非本次引入；未扩为全量重跑。`scripts/check --staged --only ruff,health,no-tmp` PASS（4 文件，0 blocking / 0 advisory）。

**F16 真实模型复测（3 个 Conversation，复用现用 `round3` Profile）。** 证据目录 `.hermes-dev/f16-retest-20261017/`（`run_f16.py`、`inputs.json`、`analysis.json`、每 Conversation 的 baseline/settlement snapshot 与完整 child 工具序列、`rpc.jsonl`、`clarify.log`）。固定产品代码 `0dfa26a58d` + 上述 F01/F04 修改；现行 07 §8.11 Step4 提示词未改。每个 Conversation 都是同样的结算情景（两条已完成经验、一个未完资料册、一个租借经历 + 待审 Skill 草稿、一次精确批准的真实 memory 成功、一个后来变化），只替换合成内容 A/B/C，原因是同一 Profile 的 USER 记忆会让相同文本变成重复写入。

| Conversation | 完整派发来源的结算 | 部分派发来源 | Candidate | 结论 |
|---|---|---|---|---|
| A `conv_dce45273…` | Notebook 里没有该来源（Main 在 baseline 前已违规直接写 USER，见下），无法覆盖归档分支 | situation 14 改写为仅剩 Skill 待审基础，正确 | 16/18 先清 refs 再归档，17 保留 Skill，正确 | 归档分支不适用；已索引来源的结算正确 |
| B `conv_b3c7cda2…` | situation 29（食堂+南湾，均已随 F16B 派发）**未归档，正文原样保留并追加后来变化** | situation 30 保留整段经历正文，只加 processing_note | 33 已归档但 refs 仍为 `['28']`；32 正确收窄为 Skill | **F16 失败复现** |
| C `conv_ae2797a8…` | situation 41 **已归档**；situation 42 改写为只剩未批准保存的返程细节 | matter 43、situation 44 改写为仅剩未完成责任/待审 Skill | 46 先清 refs 再归档，47 保留 Skill，新增 54 承载未批准细节 | **F16 行为通过** |

**模型行为观察（只记录，未调优）：** (1) A、B、C 的 Main 都在 facts 阶段、用户明确“不批准任何写入”的情况下直接调用 `memory` 写了 USER 目标（A 18:36:33 一条；B 18:39:35 一条；C 18:41:59 一次批量三条），工具均返回 success；A、B 另各创建一条 Schedule（A `2026-10-19 19:00`、B `2026-10-18 10:00`），C 未排期；主动提醒属产品预期，不作为偏差。这是 Main 的指令遵循问题，与 Noting 的结算判断分开记录。(2) A 的 baseline 没有把两条已完成经验建成 Notebook 来源（已成功写入的内容未被重新索引），故 settlement 没有“完整派发正文”可清；C 的 baseline 仍建了 41/42，B 建了 29。(3) B 的 settlement 已识别出 F16B 真实成功、也更新了 Candidate，但仍把已派发正文留在 situation 29，并把 33 带 refs 归档；C 的同类判断则完整执行了“先来源正文、后 Candidate/refs”。(4) A 的 settle 子 Agent 首次 `conversation_history` 返回 `source_unavailable` 后自行改用可见读取，未重复失败调用。**结论：现行 Step4 文本能被执行，但真实模型在 3 次里只有 1 次完整执行；提示词不变的前提下，F16 仍不能判为已关闭。**

**当前 Profile 残留：** 上述 3 个测试 Conversation、其 USER 记忆追加（含 A/B 未经批准的写入）以及 2 条待触发 Schedule 仍在现用 `round3` Profile；未做 SQL 清理或二次写入。需要清理时由用户确认后按产品入口处理。

**2026-10-17 追加 · handoff 用词纠正：** 已把 Notebook/Candidate/Persistence 文本里把外部写入写成 handoff 的 10 处（4 个文件）改为 writes / proposal materials / approved write / dispatched；`docs/07`、`agent/system_prompt.py`、`hermes_cli/cli_secretary_commands.py`、`secretary/noting_prompts.py` 已同步，07 与运行时常量逐字一致。上下文/任务交接语义的 handoff 未动。

## WIP · 增量审查明确Bug修复（2026-10-17，Codex专职续修）

**用户决定（2026-10-17）：** 工作区保留已开始但未完成的增量审查 bug 修复；用户估计为 5 个、也可能只有 3 个，具体以 Codex 恢复后核对为准。这些 bug **不阻塞**当前开发，**不宣称已修复**。Codex 额度恢复后由 Codex 专职继续；其他 Agent 不接手这批 WIP，也不把现有改动当作完成。当前 WIP 的 3 项定向测试通过（`test_cold_usage.py` 2、`test_secretary_read_profile_scope.py` 1），仅证明当前检查点可运行，不证明 bug 已关闭。

**已落档的用户口径：** Pin 区在 New Conversation 与 Today 之间，空时隐藏；长按拖拽保留原占位，接近顶部展开 Pin 落点，松手置顶，已置顶项可同手势调序。**Pin 表现/拖拽由用户另外指定的 Agent 实施，本 WIP 不修改。** Orb 不再需要倒计时，现有表现已获用户确认；只修失败任务误报成功的事实判断，不重做 Orb。两项口径已同步 06 §1.3/§1.15/§2.6。

**当前 WIP 范围（未完成）：** 后端冷恢复改用所属 Profile 的 SessionDB 与当前 Session 模型（`tui_gateway/session_usage.py`、`test_cold_usage.py`，并从 `server.py` 移出旧 helper）；Secretary 读取按所属 Profile 绑定运行时时区（`methods_web_read.py`、`test_secretary_read_profile_scope.py`）；`inventory.py` 的可见 effort 声明整理与健康修补。**未包含：** 独立 UI 仓库的 F07/F09 等前端改动（其工作区原样保留，未提交）；其余审查项不在本 WIP。后续 Codex 继续时先核对实际剩余项，不按这里的估计数量直接判定。

## 已完成 · 5098模型代码漂移保护开发开关（2026-10-17）

**用户已确认：** 增加现有配置系统中的开发开关；默认保持保护，显式关闭只绕过模型操作的版本漂移拦截，保留原始检测及其他使用方。策略为后端进程级，同进程不同Profile一致；不改前端/数据库，不削弱独立4001保护。权威需求已落[06 §0.8](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#08-development-opt-out-for-model-code-skew-guards-user-confirmed-2026-10-17)。

**状态：已实现；已按用户授权在 `round3` 启动 Profile 写入 `gateway.model_code_skew_guard: false` 并重启当前 `53445` serve 后端。** 配置键为 `gateway.model_code_skew_guard`（布尔，默认 `true`），用法与限制已写入[README](README.md#模型代码版本漂移保护开发开关)。集中策略入口在 `gateway/code_skew.py`：`record_boot_state()`/`resolve_model_guard_policy()` 在启动时读取一次启动 Profile 的 effective config 并锁定进程策略，`model_guard_skew()` 是三个模型入口共用的唯一接缝；`detect_code_skew()` 原语义未改，Cron 与后端退休/watchdog 仍直接使用它。启动接线位于 `gateway/run.py::start_gateway`、`hermes_cli/web_server.py::_lifespan`（dashboard/`hermes serve`）和 `tui_gateway/entry.py::main`。

**验证：** 三个原有测试文件定向 **47 PASS**（`test_code_skew.py` 33、`test_model_rpc_skew_guard.py` 7、`test_web_server_skew_exit.py` 7）；相关有效并集 **73 PASS / 1 平台 skip**（另含 `test_resource_limits.py` 启动顺序、`test_web_server_boot_handshake.py` lifespan、`test_web_server_launch_env_freeze.py`）。另在隔离 `HERMES_HOME` 实际执行 README 的 `hermes config set gateway.model_code_skew_guard false`：写入 `false`，启动解析返回 `False` 并记录关闭警告（未触碰用户配置）。证据覆盖：未配置/显式开启仍拦截、显式关闭后 Dashboard 两个模型路由与 gateway `/model` 实际路径继续执行、TUI `model.options`/`model.save_key` 继续执行、关闭后原始检测与 Cron/watchdog 仍工作、启动后切 Profile 或二次解析不改变策略。`scripts/check --staged --only ruff,health,no-tmp` PASS（health 0 blocking/0 advisory；已用等价压缩抵消 `run.py` 与 `config_defaults.py` 的超限增长）。**重启后现场（2026-10-17 18:11）：** 新进程 PID `14246`；`/api/health` 200 且 `commit=ffc3d4e4f5…`；`/api/config?include_defaults=false` 返回 `gateway.model_code_skew_guard=false`；启动日志明确记录 `model-operation code-skew guards are disabled`；`/api/model/options` 200。**真实漂移验证：** 提交 `74ae757904` 后后端 boot `ffc3d4e4f5` 与磁盘 HEAD 已分离，`/api/model/options` 仍 200（同等漂移在开关默认 `true` 时曾返回 503）。**未验证：** 真实模型调用、gateway/TUI 独立进程、其他平台。关闭保护不等于热更新；真实导入/运行错误仍会暴露。

## 第2次 Verification 后的增量审查与用户现场回归（2026-10-17）

**当前用户任务：** 审查第2次 Verification 后两仓功能打磨，识别用户需求是否落档、文档与实现/文档之间的冲突，以及潜在回归；不代替或改写第二次独立门禁结论。审查基线公开 `b6939f47e3ffdd81e507cc73a207e709fa0157d9`、UI `50cc8fd52dfe64a8f4afb4fe2d2cbbf8b8e5454e`，后续修复单独记录。定向反证及日志保存在 `.autonomous/20261016-round3-secretary-nm/evidence/post-verification-review/`；历史反证不因新授权改成新需求下的失败。

**本会话用户已确认，立即覆盖旧口径：**
- 冷启动允许沿用上次可信值作估算，目的是给用户可用读数，不能仅因不是当前精确测量就判缺陷或留空。06 §1.13已更正；此前“禁止估算”的审查判据撤回。实际Web Session Total还沿已有REST读取原生持久Session计数，不能仅凭live `usage_detail`未恢复就宣称整个界面未恢复。
- 普通提示统一 **5秒** 自动消失，错误仍手动关闭；06 §1.15已覆盖旧10秒，原生notice与本地思考档位toast共用已有 `NativeNotices.track` 计时owner。相关测试有效并集28项PASS（首26项＋修正旧4.6秒断言后的定向2项），不复跑其余已过节点。
- 用户要求缩短Scheduler说明；07 §8.14与运行时同步为26英文词（原42词），每条Reminder各带说明、整批仍一个durable carrier；2项相关投递/ACK测试PASS。
- 用户实测：Send后首段Thinking整个流式阶段缺失、Turn结束才出现；首个工具卡片开始时闪动。已授权修复并明确委派子Agent。`timeline_stream_regression`（GPT-6.1/high）独占UI投影/组件/RenderStore及对应测试，主会话避开其白名单；不得派生、重启后端或改用户Conversation。主会话处理其余审查、普通提示及文档，交回后集中review，不重复其有效测试。Timeline首包已review接收：仅App的呈现key保持及空白历史过滤，新7项逐帧组件测试；最终56项PASS、此前有效并集99项，整合typecheck一次PASS。真实replay未证明推理文本被吞，实际确认空白补卡与工具DOM重建。

**新增Chat UI需求（本会话用户确认）：** 原先“Profile放进Model selector”的提案已被用户替换：仅首页/New Chat显示独立Profile下拉，选项只显示名字，沿原生Profile整套切换，已存在Session归属不变。多个Profile可指向相同terminal.cwd共用Workspace。Conversation列表左侧icon按其所属Profile区分；图标用前端源码内固定映射表，不做配置或设置界面。已落06 §2.11，由同一子Agent以UI 01be26a为基线完成增量，主会话review接收并提交同步UI `0371c6c`；不得把旧提案保留为同时生效的交互。当前固定映射default→MessageSquare、round3→FlaskConical，未来新增Profile需补映射，未映射先用UserRound通用图标，不冒称每个未知Profile已有独占图标。真实只读观察确认名单及启动home唯一匹配round3；创建/发送/隔离为受控Controller→App链证据，未新发真实模型或真实Profile写入。

**Profile增量验证与接收：** 新增24项＋既有89项的有效并集113项PASS，共11次定向Vitest、两次对应不同实现版本的typecheck通过；最后定向8项，未再跑整组。主会话集中review后追加修复根URL显式Profile优先、last-route仅恢复同owner旧Conversation两处边界，各有RED→GREEN；不重复子Agent有效测试。公开合成日志/脱敏观察与哈希见专项报告§7及证据manifest。主仓库本次仅维护稳定入口、规格、看板和证据，AGENTS规则无需更改。UI提交排除用户同期Constructing文案/对应Timeline断言及新出现的置顶表现文件，保留其工作区内容，不宣称用户编辑中的UI工作区干净。

**同期协作（用户明确，2026-10-17）：** 用户会自行微调表现层；集成保留这些同期改动，不因小幅样式/呈现差异回滚或重做。主会话和子Agent继续核对功能、状态归属与接口，只有表现调整实际影响这些契约时才指出。

**检查现状：** 固定base a51fd99的ruff/no-tmp通过，health 158文件有13 blocking（其中5条证据脚本诊断与直接ruff/源码不一致，待排查），未放宽规则。详细专项审查见[post-verification-review.md](.autonomous/20261016-round3-secretary-nm/post-verification-review.md)。

**待收敛：** 跨会话配置4001重试错投在Profile增量中已按原route/profile/runtime owner窄修并取得RED→GREEN；历史反例保持原样，只关闭该受控路径。冷启动归属/模型真值错误、排期时区两端错配、置顶排序、AI起名输入及失败任务高亮共6项产品问题仍开放，另有上述代码健康阻断；仅估算本身及旧10秒寿命不再作为现行需求缺陷。原生事件与真实UI结果的边界分别记录，未凭模型自报通过认定完成。

## Web Chat `/title` + `/ai-title` 命令接线（2026-10-17）

**用户已确认语义（2026-10-17 更正）：** `/title <name>` 手动改名；空参 `/title` 查看当前标题；AI 起名改由独立的 `/ai-title` 专门处理。用户明确否决在同一个 `/title` 入口上用 `--ai` 承载两种模式；`/title --ai` 在 Web 上不再触发 AI，会给出用法错误并指向 `/ai-title`。`/ai-title` 是 **Web 本地命令**（无原生 catalog 条目），由 Web 命令路由本地广播；官方客户端 `/title` 语义不变。AI 只提议，命令执行写入；失败保留原标题并显示原生错误。

**实现：** Web 命令路由保留 `title` 浏览器控制（手动/读取）；新增 Web-local `ai-title`，在 Web 斜杠建议中单独注入，不冒充原生目录。live 会话走原生 `session.title` RPC 写入，stored row 回退 `PATCH /api/sessions/{id}`；AI 生成复用现有 `llm.oneshot`（不新增后端 RPC），标题变化由既有 `RenamingText` 在顶栏和选中侧栏播放动画。未改主仓库后端。

**验证（2026-10-17 复核）：** UI 仓库 `npm run typecheck` PASS；全量 `vitest run` 为 **504 PASS / 9 个既有失败**（`presentation.integration.test.tsx` 的 jsdom `el.scrollTo` 基线；在 clean HEAD 复跑同样 9 个失败，非本次引入）。

**改动文件：** UI 仓库 `src/core/conversation-title.ts`、`conversation-title.test.ts`、`controller.ts`、`commands.ts`、`command-actions.ts`、`App.tsx`、`controller.test.ts`、`controller-session-metadata.test.ts`、`contracts.test.ts`；主仓库 `docs/06-Hermes-Secretary-Web-UI-V1-Spec.md`、`CLAUDE.md`。已提交：UI `3f7f693`（含此前 `5d6121c`、`e15122d`、`c333bd7`），主仓库见本文件所在提交。

## 当前任务 · 部署拓扑 + 双 SPA + 4001 恢复（2026-10-17）

**用户已确认：** 单私有域名 + Cloudflare Access 唯一可见认证 + Cloudflare Tunnel + 本机 Caddy（Host 改写为 `127.0.0.1`、删除 `Origin`）+ 后端只 bind loopback；`/` 为 Secretary，`/dashboard` 为官方 Dashboard；同进程双 SPA、共享 `/api`/`/api/ws`；不做跨域、不做第二 API 域名。**规格已写入** [06 §0.7](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#07-confirmed-deployment-topology-and-dual-spa-routing-2026-10-17)，README 已补稳定部署入口。

**实现范围：**
- 后端：`mount_spa` 参数化并新增 `HERMES_DASHBOARD_WEB_DIST` / `HERMES_DASHBOARD_PREFIX`；`/dashboard/api/*` 在路由前重写为 `/api/*`（HTTP + WS）；未设置第二套 dist 时行为与原生完全一致。
- 前端：`controller.setSessionConfig` 在 4001 时 `ensureBinding`（resume stored session）后重试一次；成功静默，失败才提示；不删除后端 stale-session 保护。

**状态：已实现，定向验证通过；未做真实部署/手机端到端。** 后端正向：`mount_spa` 参数化，`HERMES_DASHBOARD_WEB_DIST`/`HERMES_DASHBOARD_PREFIX` 启用第二套 SPA，`_DashboardApiPrefixMiddleware` 将 `/dashboard/api/*`（HTTP+WS）重写为 `/api/*`；未设置新变量时不挂载、不加中间件。前端 `controller.setSessionConfig` 在 4001 时 resume stored session 并重试一次，成功静默。

**本次验证：** 后端新增 `tests/hermes_cli/test_dashboard_dual_spa_mount.py` 5 项 PASS（未启用保持原行为、`/dashboard` index/资源/CSS/API/WS、可配置前缀）；SPA 相关文件全量回归 **235 项 PASS**（`test_web_server.py` 202、`test_dashboard_auth_prefix.py` 26、`test_dashboard_initial_profile_bootstrap.py` 2、新增 5）。前端 `controller.test.ts` 73 项 PASS、`npm run typecheck` PASS、`npm run build` PASS。`scripts/check --staged --only ruff,health,no-tmp` PASS（health 0 blocking/0 advisory；两处 HX002 以部署路径注释豁免）。**未验证：** 真实 Cloudflare Tunnel/Access/手机浏览器、双 SPA 生产运行、后端重启现场。

**本次改动文件：** 主仓库 `hermes_cli/web_server_dashboard.py`、`tests/hermes_cli/test_dashboard_dual_spa_mount.py`、`docs/06-…md`、`README.md`、`CLAUDE.md`；UI 仓库 `src/core/controller.ts`、`src/components/ChatSelectors.tsx`、`src/core/controller.test.ts`。工作区另有既有未提交修改（`docs/07`、`scheduler_time.py`、`tests/secretary`、UI `design/layout.tsx`、`theme.css`），本次未触碰、未纳入提交。


## 第三轮第2次 Verification · 公开主仓库审查完成，不通过

**最新用户指令（2026-10-17）：** 继续在主仓库执行第三轮自主实现第2次verification，审出的内容直接写仓库，在main向前提交。实际仓库为 `EdgarZhong/hermes-secretary`。

**状态：`VERIFICATION_2_COMPLETE_NOT_PASS`。** 固定待审产品 `b40fa1ff2a771066b4da1d8978a7abe44327e530`；本次三个独立 `fork_turns=none` 审查者从原文提取要求，主会话亲审证据后完成87条细分要求及旧公共V01–V51/V52公开边界映射。全局正式报告：[verification.md](.autonomous/20261016-round3-secretary-nm/verification.md)；主会话交付判断：[final-delivery.md](.autonomous/20261016-round3-secretary-nm/final-delivery.md)。四项新不符合已在实际实现路径复现，另有F16及output-cap恢复证据缺口，Validation保持未启动。

| 当前问题 | 事实与影响 | 下一步/责任 |
|---|---|---|
| V2-F01 · P1 | History不可回读的human_only/hidden来源仍可经maintain和commit进入有效Snapshot，4组合全复现 | Notebook/History实现owner统一合法来源真值，保合法旧版本继承；原反例及实际影响邻域复证 |
| V2-F02 · P1 | 退休notebook_mutate被原生repair变为notebook_maintain，真实child写入并提交 | 工具dispatch owner在统一原始名称修复边界落实退休集合，保留历史原文 |
| V2-F03 · P1 | 配置ContextEngine后child第2/3请求可重写冻结父消息，任务仍提交 | 请求/child owner保护冻结段，保Main原生选择能力；逐请求tool/retry/continuation复证 |
| V2-F04 · P2 | 每日10:00在09:20恢复时被推进到次日10:00，正式list也错误 | Scheduler owner修未来next_run被当last_run推进的问题，保claim/撤销/ACK不变量 |
| V2-E01 / F16 · P1 | 40f4ecc新库真实链提交已成功，已交付来源正文仍未退出；b40fa1f具体改写Prompt无新行为关闭证据 | 原生round3固定修复SHA做一次完整来源结算链；保留首次结果、新变化/未完责任/其它候选依赖 |
| V2-E02 · P2 | 普通overflow会早停；output-cap豁免仍尝试child压缩，正式错误路由未实证 | runtime owner补该窄分支正式provider错误证据，再据实际结果修复 |

**本次执行证据：** 官方PM Python 3.14.7、Linux x86_64、原锁dev/test环境；四个canonical单文件runner、禁重试，共10独立用例，**3 PASS / 7 FAIL**，runner wall8.7秒。七个失败均保留为四项产品反证；另两次沙箱临时目录失败发生于收集前、0 tests，已分开记录。原始脚本、日志与哈希见 [evidence/verification2](.autonomous/20261016-round3-secretary-nm/evidence/verification2/README.md)。未修改产品或既有测试，没有运行新的真实模型、用户round3现场、NM、跨平台实机、UI或部署。

**旧问题复核：** 公共V51可读时间、F17交接、F18覆盖排序、F19可见压缩源/hidden Anchor及F20事件值的旧反例可按当前源码与具体旧证据关闭；首33回归失败/错误已有逐节点定向修复记录，六个修复测试源码哈希和锁亲核一致。F19较晚补35原生邻域与新schema真实链已读，较早final-delivery的“未执行”不再作为当前事实。完整旧全量结果仍是1766P/29F/4setupE/3平台skip，未改成“整套全绿”；忽略日志未在本次回放。以上不抵消本次新问题。

**main接续与范围：** 开始调查时main仅有c099c8c规划；期间并行提交已快进集成b40fa1f，并新增da68703/de810ba文档。已亲核两提交不改产品，保留其 [verification-2.md](.autonomous/20261016-round3-secretary-nm/verification-2.md) 静态历史，本次从最新main继续提交。公开产品审查与个人Provider V53–V60分开；个人线未在本次代签，不宣称整个第三轮交付完成。整改要求追加原 [plan.md](.autonomous/20261016-round3-secretary-nm/plan.md)，修复集成后需再次独立复审，通过后才启动Validation。

<details>
<summary>本次接续前的完整主看板原文（截至de810ba，历史状态）</summary>

# Hermes Secretary 项目主看板

## 第三轮第二次 Verification · GitHub 静态复核（2026-10-17）

**目标提交：** `b40fa1ff2a771066b4da1d8978a7abe44327e530`，本次依用户指令已从旧规划 `main=c099c8c` 非强推快进到该第三轮实现提交；`main` 前进是代码集成事实，**不代表通过Verification、Validation或发布**。本次报告与本段为后续文档提交，不改变审查所针对的产品SHA。

**审查文件：** [第二次 Verification 静态复核](.autonomous/20261016-round3-secretary-nm/verification-2.md)。状态：**NOT PASS / BLOCKED_EVIDENCE（独立全范围第二门禁 INCOMPLETE）**；仅经GitHub连接器静态回读代码、冻结条款与已有开发证据，未使用本机round3、未运行模型／测试／10类check，既有ignored原始日志未在本环境回放，也非项目指定 Astra/high 全量独立执行。

**需关闭的最高优先项：** V23/F16旧版真实反证及R3-022新库两child有效提交后仍保留已交付来源正文；最新b40的07/Noting Step4已明确`notebook_maintain`改写`fields.description`并先结算来源、后关Candidate，**但没有该SHA真实Main批准→Memory成功→Noting来源精简的成功轨迹**。开发报告称F18/F19及V51、首轮33失败/错误与两类检查已有定向修复证据；这些仍需按产品SHA/日志hash关联，不将原始失败或开发PASS改写为本次亲测结论。公共V01–V51剩余条款和个人V52–V60尚待符合项目要求的完整独立复审；Validation不启动。真实NM写入、UI改版、云端部署依旧不在本次授权范围。

**接续：** 按报告§5最小序列复用有效定向证据，唯一隔离round3正式复证F16同时观察F18/F19，然后由指定独立审查者给V01–V60正式二审门禁结论。保留首次`verification.md`及全部反证原记录，不为“绿色”重复大型回归或放宽规则。

## 自主口径收敛 · 待用户追认

**暂无。F16结算顺序已由用户明确调整（2026-10-17）：先处理该退出的来源正文，再关闭Candidate；提示词保持简短。** 已据此重写07 §8.11 Step4及运行时同段：修正阻塞归档的已结算引用时保留Candidate的描述和消息来源作为清单，先归档／精简来源，全部相关来源处理成功后再归档或更新Candidate；继续保护后来变化、未完责任、其他未完成提案所需内容。替换段落比上一版更短。先前“候选为空时再查”的补丁提案不采用。用户确认的是本次处理顺序与控制体量，不冒称逐字确认英文。已完成文本与接线一致性核对，待固定提交后真实round3复证；不启动第二次门禁，F16尚未关闭。原失败与原Astra评审仅代表历史版本。

**当前执行（2026-10-17，R3-022）：** 用户要求主会话一个人继续，把阶段推进至确实可启动第二次Verification；不派子Agent、不启动第二次复审。公开基线40f4ecceb772e6faaa98b99d95b8f4b0de5e31f0，工作区起点干净。当前补F19 Force／原生邻域，然后完整封存round3旧测试profile并新建同profile数据库，固定版本做统一真实链复证；不迁移旧库、不使用真实NM。F19补35邻域PASS；新schema真实链两child提交及pointer/反馈隔离通过，但F16仍仅来源注记未精简正文，首样本FAIL保留。Step4仅将来源动作明确到notebook_maintain重写fields.description，212词；待该新版本一次完整链复证。

提交前定向静态检查：固定base a51fd99abc783f245ab855526a10862f2c89656a，`ruff,health,no-tmp`三项PASS；health覆盖134文件，0 blocking／0 advisory，9.8秒。日志ignored pre-verification-final-check.log；没有重跑大型回归。

## 第三轮自主实现 · 本地托管恢复（2026-10-17）

- 用户已授权：拉取全部远端分支；据本地环境调整计划并完整完成第三轮，优先派遣 C4。Verification 前高并行委派，主会话抓全局、review、集成，不重复执行子 Agent 有效测试。积极使用原生 DeepSeek 真实模型，token 消耗不设限制。
- 门禁：Verification 全新 Astra / high；Validation 文档与场景由主会话直接制定，6.1 / high 独立执行。原计划只到 Develop 的停止限制已被本次完整托管覆盖。
- 远端全部分支已 fetch 完成（含 upstream）；未集成官方上游新代码。云端 C1/C2/C3 已亲自审读核心实现并分别接入 `0e150cbce8` / `b41c549d4c` / `4022c5b`；这表示源码接收，不表示整链通过。
- 工作区：公开核心 `codex/round3-local-completion`；初始后端干净。前端既有 dirty 保留、UI 后置。个人 Provider 独立仓库；真实 NM 写入与云端部署未授权。两仓 Actions 已读回关闭；提交自动同步不代表验收。
- 实测约定（用户最新明确）：真实产品运行、DeepSeek复测、最终验收统一采用 `round3` 隔离 profile（`.hermes-dev/round3-runtime/profiles/round3`；L0 `run-native.py` 已固定此路径）；所有数据库在仓库 ignored 目录。单元测试仍按 runner 创建临时隔离状态；本地 Provider fixture 不连接真实 NM。原 L0 目录仅保留环境准备和证据，不能继续作为另一个实测 profile。
- 环境：官方 PM `.venv` Python 3.14.7、macOS arm64、现有锁不变；隔离目录 `.hermes-dev/round3-local-20261017-l0/`。DeepSeek 原生 custom/chat_completions 公共真实复测已完整交回并由主会话接收，实际阶段版本为f304b42／eff3235／f66a8；既有 Dashboard 保留。详见本轮 `local-environment.md`。

| 包 | 当前 owner／状态 | 独占验证与待办 |
|---|---|---|
| C1/C2/C3 | 主会话已 review 并接收云端实现 | C1 93、C2 69、C3 47独立场景已有有效证据；C2 `_search` 嵌套由C10-A修复 |
| C4 | 主会话已review接收；c4-report.md | 38场景取得通过；ruff、C4增量health通过；不把全范围C2阻断写成通过 |
| C5 | 主会话已review接收；c5-report.md | C1 93场景、C5 34场景有通过证据；三Schema和三Prompt与07静态逐字一致；时间秒精度单节点由原owner补证 |
| C6 | 主会话已review接收；c6-report.md | C3 47、C6 30独立场景有通过证据；原生append_messages_batch事务prepare_rows，先持久化后live，实际携带与成功响应ACK；正式caller交C9-S |
| C7 | 主会话已review接收；c7-report.md | 63独立场景有通过证据；正式manual/auto与成功boundary接线交C9-H |
| C8 | 主会话已review接收；c8-report.md | 59场景有通过证据；pointer核验/durable/live同事务与既有锁，完整正文与严格超限Proposal；C5时间秒精度1节点通过 |
| C9-H | 主会话已review接收；c9-host-report.md | 正式pre-summary唯一联合准备、原生成功发布事务更新interval、非空成功响应ACK、completed/failed归档gate；112独立场景有通过证据。review修正工具args业务校验不属投递ACK，23项定向复测通过 |
| C9-S | 主会话已review接收；c9-surface-report.md | 23路径指纹一致，112独立场景有通过证据；原始整批guard、退休名不fuzzy、可信catalog scope、独立Scheduler及完整claim、原生持久化prepare接线。无真实模型结论 |
| C10-A | 主会话已review接收；c10-notebook-history-report.md | 233独立场景有通过证据；C2嵌套修复、坏UID来源不可用、Snapshot时间ISO；保留旧有效保障，退出接口有处置映射 |
| C10-H | 主会话已review接收；c10-runtime-report.md | 62旧组场景＋4受影响Idle节点有通过证据；恢复deadline唯一local决定，提交gate仍检查。公共真实DeepSeek复测已交回，证据见real-model-report.md |
| C10-B | 主会话已review接收；c10-delivery-report.md | 十个旧测试文件106独立场景PASS，含九个CLI/TUI/Gateway SIGKILL边界；无生产修改，旧Notebook耦合退出。F08/F11/F12已review接收；最终回归已统一执行一次；首33失败／错误均定向关闭 |
| C10-P | 主会话已review接收；个人8682ff8，c10-personal-report.md | 两旧测试39项PASS，canonical runner通过ignored源码链接避免错误包收集；无生产修改。正式host→本机fixture六场景已完成并review接收 |
| P1/P2/P3 | 主会话已review接收个人线并提交57d0abb854f4；personal-report.md | 46独立用例通过；真实SessionDB/MemoryManager+本地HTTP fixture，P2基本模拟通过；主会话已review，公共finalizer gate及历史旧测试已收口，真实host→fixture六场景已通过并review接收 |
| C10-T | 主会话已review接收；c10-final-legacy-report.md | 六旧文件及相关节点有效并集92 PASS；F10/F13、F11受影响旧组定向关闭；独立初审已完成，现修复复证 |
| C11-P | 主会话已review接收；personal-host-report.md | 原生host→loopback fixture六场景、临时工具收窄及完整配置/插件备份恢复；公共f66a8f80／个人8682ff85实测；12 completed Turns／14请求／24真实UID与ACK；配置和插件恢复，round3已释放 |
| L0 | 环境已交回；yaml问题是个人脚本旧导入，P3 owner修复 | 不跑产品测试；不改锁或裸装依赖 |
| 门禁 | verification_astra（全新Astra/high）已完成全范围初审；发现项已回到修复循环 | 初审固定公开323c64dacba1／个人e1af6cc45ffb；修复生产公开25241d8c83d0／个人5a2fe444042c；首审60项：56符合、2不符合、2证据不足，主会话已review接收；修后需全新独立全范围复审，Validation待通过 |
| F14 最终回归 | 首轮已完成；27个旧测试失败／错误已修复并由主会话review接收（含邻域共29）；压缩6原失败＋邻域共10已review接收；两失败检查已修复通过 | 1766 PASS／29 FAIL／4 setup ERROR／3平台skip；固定136文件等范围只执行一次，后续仅失败与影响路径定向复测 |
| F15 时间投影 | 公共六路径17项PASS，主会话已review接收；个人Recall8节点＋17子例已review接收；Scheduler run_at／绝对display共8项有效证据已review接收 | V51：仅人／模型可读Notebook投影为秒精度，覆盖工具、control、Main、slash、Proposal、Framework；内部精度不变 |
| F17 冻结交接 | local_environment修复20项PASS，主会话已review接收；r3_pointer_repair调查旧真实结果；新复证由r3_real_retest独占round3执行 | 原恢复链human_only Anchor在同步模型投影中被过滤；现用已验证Ref／UID交接，不重读父状态；admission13真实child完成并提交新Snapshot，完整六请求prefix已读；pointer问题已独立登记F18，不冒称通知整链通过 |
| F16 来源结算 | 主会话及Astra已评审具体Step4细化，c4已实施，F17修复后固定25241d8c83d0真实round3补证 | V23：候选13已归档但来源6仍保留成功写入的完整经验；细化后旧链仍错误跳过该来源，保持OPEN；R3-019短Prompt在d434ffd真实首样本仍先Candidate后source，source50未精简；且F19阻止提交，不能判好转；真实轨迹已确认把只读candidate_refs误当编辑入口；短句已明确Candidate.fields.notebook_refs，210词版真实首样本仍留成功正文；现212词明确fields.description待实测 |
| F18 coverage排序 | r3_pointer_repair完整修复31项PASS已由root review接收，待统一阶段提交 | 旧UID被压缩携带到更后物理位置，旧Snapshot误压新Snapshot；仅修排序真值源；fork同事务新增coverage_position保留父冻结顺序，保持Full展示与通知gate；开发阶段不迁移，真实库完整备份后重建 |
| F19 Anchor有效性 | r3_evidence_audit只读调查 | d434ffd真实admission15 finish后提交abandoned：human_only Anchor压缩后不在Full；同一summary输入与后续raw coverage/tail源集错配；统一可见压缩源，隐藏行走原生unseen保留，不放松commit gate；9项受控正式链PASS；Force/其他原生邻域未执行，真实复测未跑，阶段提交 |
| F20 结束事件 | root微小接线修补已验证 | 失败结束统一既有task_finished协议值，不更改outcome/提交事实；实际child失败＋wire验证RED1→GREEN1，待统一阶段提交 |

- 真实运行新发现 R3-F08：TUI Main streaming期间/noting反馈后，durable原文仍在但后续Active冻结缺输入／图片；修复已由主会话review接收：busy历史批次合并与cold human_only投影共28项PASS，ruff/health通过；eff3235真实busy图片六请求与cold回复／human_only隔离已通过，主会话接收。

- R3-F09真实Scheduler目录缺失已由主会话review接收单点catalog修复，正式TUI四开关及热关闭等6项PASS；eff3235真实bridge登记、投递与ACK已通过。C10-T六旧文件已收口，最终有效并集92项PASS；首轮60 PASS／17 FAIL／10 setup ERROR保留。R3-F10 External通知owner重读由主会话只补传现有ref，原失败及owner/suppression六项定向通过。F08b冷恢复human_only与正常回复合并已反证并修复；R3-F13原生/notebook误显Snapshot/anchor ID已修正，原CLI失败、human/model投影及Framework三项PASS。

- R3-F11／F12：真实原生成功压缩复用UID时漏记新interval；Force父尾为user时Noting任务被并入冻结消息。local_environment首包62项PASS；F11主会话review接收，C10-T另四项通过。F12首次review发现child时钟重做父历史清理，补四个真实native RED后回修；主会话已review接收累计74项有效证据并提交eff3235f6b；追加review确认preflight旧Anchor截断缺口，已补正式preflight RED并窄修，累计有效78项PASS；主会话接收；f66a8真实user尾七请求及两条五Turn链共31请求的完整前缀／root／tools一致，已核对真实forced提交与资源结束。

- eff3235真实定向复测首批：F08 busy图片+slash后child六请求前缀一致、F08b cold回复及human_only隔离；F09两deferred单carrier成功ACK、CRUD/instant idle；F11实际新boundary后Force再准入；F13 human/model视图区分已取得正证。忙碌instant已真实pending→下一Main单carrier→成功ACK；重启registry保持。F12及恢复已完整交回，11个child结束、未来排期零、配置原bytes恢复、原生host退出0。

- 公共真实模型开发证据已由主会话review接收，详见real-model-report.md；跨Turn两次受控probe真实执行五Turn forced，未取得“第二Turn正常finish”的特定模型形态；正常finish由自然链独立证明。受限合成USER成功不冒称多目标写失败；真实NM与部署仍未执行。C11-P已完整交回并review接收；round3配置hash恢复，插件恢复为原不存在，自有进程及lease归零。原生子进程退出码未独立记录，不宣称该码0；归档ACK完整。Verification首审已完成、整改进行中；c4统一最终回归已完成：136文件＋server84筛选函数（展开90项）＋Provider46项canonical＋冻结10类检查一次，12次调用、311.402秒，详见regression-plan.md §7。八类检查通过，no-tmp／health两项有窄修补；主会话不重复有效测试。

- 初审整改：V51输出投影修复不降低内部时间精度；V23真实来源结算样本存在缺口，已与Astra按冻结成功范围结算要求研讨，先核对实际Prompt分支，再通过round3正式Main批准→实际成功→Noting语义结算补证。不得用SQL删除、伪造写成功或硬编码删来源替代。首失败保留，新增成功证据须同时证明已交付覆盖移除及未交付内容／责任／其他候选依赖保护。

<details>
<summary>云端规划时点记录（历史，状态以上方本地托管为准）</summary>

## 第三轮自主实现 · Planning已编制，等待按任务分发

**当前阶段：** `PLANNING_DOCUMENTED`。本次完成计划撰写和仓库文档同步；没有派遣实现、启动产品、执行测试、写NM或部署。不能把本文中的待执行包当作正在后台运行的任务。

**最新用户指令（2026-10-16）：** 接手第三轮计划，覆盖整个Develop直到独立Verification／Validation之前；尽可能详细、减少子对话与主会话重复验证、增加并行度。随后明确：多个独立网页Chat各自通过GitHub连接器创建分支、一次或多次多文件提交和PR，由本规划会话处理PR；完成可完成的云端代码修改之后，再回本地实际运行、测试及修复编码阶段未识别的问题。测试后置，不取消；本次不直接启动编码。

**唯一计划：** [.autonomous/20261016-round3-secretary-nm/plan.md](.autonomous/20261016-round3-secretary-nm/plan.md)。

**确认索引：** [snapshot-index.md](.autonomous/20261016-round3-secretary-nm/snapshot-index.md)，新增R3-012～R3-015覆盖先前“文档基线后暂停”的阶段口径，既有产品约束不变。历史冻结哈希仍见[baseline.txt](.autonomous/20261016-round3-secretary-nm/baseline.txt)，不改成规划提交哈希。

### 基线、范围与禁止项

| 项目 | 当前事实 |
|---|---|
| Secretary源码起点 | `a51fd99abc783f245ab855526a10862f2c89656a`；改版前代码 |
| Secretary需求冻结 | `d19018a7ba3e38ae01f76aa57821b55cbc15ff58` |
| 规划开始读取的main | `dec457e2393dc3e7401449b19b068bf7c65e5a07`，仅追加冻结哈希记录 |
| Provider冻结main | `97078118287bcd41ba8b02aa5a3a108c5026f7af`，源码仍来自`f9733fcb31a0e6f468eabe6419cb76444fe16b30` |
| 公开需求 | 已审Notebook白板＋07；旧01/02/04/06仅明确保留段 |
| 个人需求 | 独立Provider仓库PHASE3现行§1–7；历史附录不作为本轮并列依据 |
| 本轮产品范围 | Secretary改版与独立NM接入；UI、Settings展示、Web DTO及云端部署后置 |
| 本次实际变更 | 计划、索引和当前看板；原看板逐字保留为不可变文本快照 |
| 当前运行／测试 | `NOT_RUN`，没有本轮产品通过证据；旧报告不作为新版本通过 |

两仓源码／配置／运行数据库未因本次规划改变。未读取用户本地当前dirty状态；旧路径、端口、PID和前端未提交记录都不能当作本次现场核验。回本地前必须保护实际已有变更，不reset/clean，不部署。

### 已确认且不得重新扩张的产品边界

- 并发Noting保持现状：已提交A、B未提交时C可从A独立整理；不要求C继承B，不新增串行／合并／重跑机制，不以缺少B→C成果继承阻断验收。pointer通知仍须正确。
- 完成通知只由本次提交使有效Snapshot pointer切换产生；实际追加前再同事务／锁判定，失效整条丢弃，含完整正文及Proposal；完成时间不替代coverage。
- Noting仅四工具；finish独立批次，成功后固定工作视图，原生Turn返回才提交。五Turn／overflow兜底保留，child不再请求父compaction。
- Scheduler独立于Notebook／Noting；deferred继续原批量carrier、durable materialization、真实携带与成功响应ACK；完整Table未来24小时空档notice沿工具返回／原instant最终投递提供，不自动补排期。
- 个人Memory必须保存Hermes provenance。窄脚本官方CLI创建→真实ID→仅补Metadata，复用同一运行主机配置；不恢复旧完整HTTP正文写入体系。小脚本仅基本检查，不严格验收、不重测官方CLI、不做真实测试写入。
- Provider自动Thread归档真实NM写入尚未授权。普通Hermes试跑也可能经sync hook写Thread，本地必须先用隔离fixture端点。不得创建Space、改个人记录或治理；正式部署另行安排。
- 不做旧数据／配置迁移；不删除旧消息调用历史；新执行面不保留旧名alias。不把旧UI要求拉回本轮；公开核心不能依赖个人Provider成功。

### 执行顺序与分支策略

```text
独立Chat代码与测试源码 → 本会话PR静态review/merge
→ CODE_INTEGRATED_UNRUN（双仓SHA，仍未运行）
→ 本地LOCAL_RUN/LOCAL_REPAIR（首次测试、接线运行、定向修复）
→ DEVELOP_READY_FOR_VERIFICATION → 停止
```

首次发包前由本会话建立两仓`round3/develop`，分别从含本计划的公开main和已核对Provider基线创建；当前尚未创建。任务各自`round3/<id>-<topic>`，PR base为本仓集成分支。本会话唯一合并者，执行对话不改main／集成分支、不合自己的PR。未经运行／独立门禁不作发布判断。

云端不安装、不运行、不lint/compile/typecheck、不启动模型和产品；可编写测试源码，统一NOT_RUN。静态发现的错误当场修。PR接收表示源码已审，不是测试／独立验证通过。后续本地保留canonical runner与冻结规则，不为每任务或每PR重复跑大套件。

### 当前任务看板（所有任务尚未派遣）

下表是唯一动态编排看板；plan中的任务卡保持静态。以后在本表填实际owner/branch/PR/head和状态，不新建分区看板。

| 任务 | 工作线 | 修改启动依赖 | 当前状态／实际PR |
|---|---|---|---|
| D0 | 两仓集成分支、运行触发设置、发包SHA | 用户开始分发 | 未执行 |
| C1 | Notebook模型／版本／Snapshot | D0 | 未派遣 |
| C2 | Conversation History／候选流 | D0 | 未派遣 |
| C3 | 独立Scheduler控制面 | D0 | 未派遣 |
| C4 | 配置／Main Prompt／Slash | D0 | 未派遣 |
| P1 | Provider资格／Bundle／Recall | D0 | 未派遣 |
| P2 | provenance窄脚本 | D0 | 未派遣 |
| C5 | child／四工具／结束续跑 | C1；合并前C2/C4 | 未派遣 |
| C6 | 投递／在途竞争／ACK | C3；合并前C4 | 未派遣 |
| C7 | 联合触发／Force区间 | C4；合并前C5 | 未派遣 |
| C8 | pointer／Framework／完整快照 | C1/C4 | 未派遣 |
| P3 | Thread归档／收据／个人接线代码 | P1；合并前P2 | 未派遣 |
| C9 | 公共正式dispatch／host接线 | C1～C8 | 未派遣 |
| C10 | 本会话源码收口／遗留测试调整 | C9/P3 | 未执行 |
| L0/L-A/L-B/L-C | 本地环境／分组首次运行 | CODE_INTEGRATED_UNRUN，回到本地 | 未执行 |
| LOCAL_REPAIR | 真实失败归因及定向修复 | 有实际失败证据 | 未执行 |
| Verification／Validation | 独立门禁 | Develop完成后另行启动 | 本次不进入 |

首批六个任务可并行；依赖满足就接力，不等整波结束。共享文件顺序交接：C1→C8的Snapshot事务、C3→C6的Schedule接纳、P1→P3的Provider归档。全局facade／dispatch由C9集中写。准确白名单、精读范围、实现步骤、后置测试与启动文本见plan，不在此重复。

### 本会话处理PR的责任

亲自读取完整patch和关键调用者；核对白名单、冻结契约、实际接口及未实现项；一次性交回具体修改意见。只因未运行不拒绝云端源码接收；有实质源码缺口／依赖未合并不能标完成。以expected_head_sha合并，确认真实merge结果后更新本看板；不把功能分支tree覆盖集成tree，不强推。后置本地证据有效时直接复用，不为主对话接收报告再跑测试。

### 启动前操作风险

1. Provider冻结看板记录Actions当时enabled；第一次代码push／PR前必须核对实际设置，确保不会违背用户测试后置。`[skip ci]`不保证所有触发事件均不运行，不能当唯一措施；本次不改Provider设置或工作流。
2. GitHub连接器能读写不表示拥有Hermes实际运行环境。云端只做内容和静态审查，不声称compile／测试通过。
3. 本轮源码更改较大，模块PR之间可能暂有待C9替换的旧调用点；待运行开发集成区不得当生产版本使用，C10必须在回本地前完成可静态识别的接线收口。
4. 真实NM服务写入授权与本地fixture证据分开记录；不能省略个人线，也不能把未授权写入变成自动执行。

### 历史原文与冻结事实保留

规划前完整根看板原文逐字保存在[CLAUDE.before-planning.txt](.autonomous/20261016-round3-secretary-nm/snapshots/CLAUDE.before-planning.txt)，其Git blob与`dec457e...:CLAUDE.md`相同。它是只读历史证据，不是第二动态看板；内含的相对路径按原仓库根解释。第二轮与10-15所有历史结论、未提交工作记录和报告版本未被改写；恢复第三轮以本页当前区域、plan和冻结索引为准，非必要不重读历史。

稳定产品入口仍由README维护，通用规则仍由AGENTS维护；本次没有改动两者或冻结白板／07／PHASE3，没有以规划状态改写“已实现”或“已验收”。

</details>

</details>
