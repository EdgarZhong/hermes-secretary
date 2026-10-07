# 首轮实施计划：20261007-v1-first-implementation

## 目标与依据

审查入口为本目录 `index.md`；冻结提交 `5346cd094b6a1bb6c6d9ce69e83b3a1570cf46bd` 见 `baseline.txt`。依据是现行 01、02、根 `AGENTS.md` 与索引中的用户确认口径。本文是执行设计，不增加产品要求或公开 API；内部接口名称可由实现者按现有风格调整，跨任务调整先向主会话报告。

核心优先级：先贯通真实主 Conversation → durable Identity → 正确 Foreground / History → Notebook Snapshot → 正常 Slash 可观察结果，再贯通 Idle / Force child、Schedule 与 Reminder。所有规定机制、关闭回退、并发、失败和重启边界都是完成条件；不能以 isolated helper 或阶段提交宣称完成。

开发运行与验收均为本机 macOS localhost 前端与后端，隔离 `HERMES_HOME`、官方 PM `.venv` 和锁文件；实际模型仅必要测试使用本机 Codex Proxy / GPT6 Luna / High，配置阶段核实真实 ID。Hermes 不参与编码。验收使用 Codex 内置浏览器访问官方 Dashboard，目标零 Dashboard 专属补丁；Personal UI、产品化 API 与面板留第二轮，不部署云端或接个人渠道。

主会话获授权做本轮本地阶段提交。实现子 Agent 不提交，不修改核心文档/规格/计划，不再派生；主会话维护全局看板、review、接线集成和证据。根 `CLAUDE.md` 是唯一动态看板，本文记录覆盖、任务契约与整改依据。

## 覆盖与任务

| 要求编号与依据 | 任务和正式路径 | 白名单 / 负责人 | 依赖与接口 | 验证方法 | 用户场景与完成条件 |
|---|---|---|---|---|---|
| R01：01 §2.1；02 §1、§6.2–6.3、§6.13 | T1 Identity：SessionDB → compression/declared locators → opaque durable Ref → trusted alias reconciliation | Foundation 实现 Agent；新增 `hermes_state_secretary_identity.py`、`hermes_state_secretary_foreground.py`、`hermes_state_secretary_schema.py`；下文列明正式薄接线 | 复用现有 DB、generation、compression tip；不把 latest generation 当旧 Session 的出生 generation；fallback 后增绑不换 Ref，冲突 fail closed | 实际 SessionDB 验证 rotating/in-place 稳定、reset/new/branch 隔离、fallback→declared、alias 冲突回滚、route ownership | S01 多 Turn/压缩仍同一 Conversation；S02 新会话及 branch 不串 ownership |
| R02：02 §2.1–2.4、§6.4、§6.14 | T1 Foreground/History：UID-based 有效路径 → 当前 Conversation search/read → main 与 Noting 同一工具 | T1；新增 `tools/session_history_tool.py` 及 inline executor/registry 薄接线 | Active/History/Full 分开；复用原文，不建第二 transcript；History 不依赖 Noting；summary carrier 保留真实 user 部分、剥离 scaffolding | keyword/regex/role/time/bounded/around-ID；跨压缩、UID twins、carried tail、rewrite superseded、compaction carrier | S03 历史检索在 Noting off 仍可用，返回 canonical provenance；不能以跨会话 `session_search` 替代 |
| R03：02 §2.6–2.7、§6.11 | T1/T2 + 主会话：成功 native rewind/edit/branch 后重建 path 和 Notebook reconciliation | T1 产 path 接口；T2 产 pointer/inherit；主会话串行接 core mutation/branch seams | branch 冻结源消息 row/UID 引用和顺序，不复制原文；继承 provenance 改为 branch Ref；parent 后续 rewind 不改变 branch 继承 | 正式 rewind/edit/branch 多入口、压缩前历史继承、parent 后改、in-flight stale Anchor | S04 rewind 后 pointer 重选或 null；branch 获独立 Ref/Notebook，主原文不改语义 |
| R04：02 §3.1、§6.1 | T1/T2/T4：Secretary-owned 新表通过既有 schema initialization 接入 | 各自新增 DB siblings；集中 schema/MRO 接线归主会话串行 | 同一 profile `state.db`；沿用 `_execute_write`、同事务 conn；不改 core table schema/ownership | 真实初始化/既有DB增量、事务失败回滚、并发写和 profile 隔离 | S05 升级/重启保留状态，没有 JSON sidecar 或第二 DB |
| R05：02 §2.5、§3.7、§5.7、§6.16 | T2 Notebook semantic model：四区十类型 → task-local mutation → complete state | Notebook 实现 Agent；新增 `secretary/notebook_model.py`、`secretary/notebook_render.py`、`hermes_state_secretary_notebook.py`、`tools/notebook_tool.py` 与对应测试 | 类型决定 section；required fields/status graph/provenance/合法Schedule intent；主 Assistant 只读、Noting 唯一 mutation；每次操作返回真实完整 entry/state | 十类型/status/required/provenance/archive/restore/edit/schedule、非法写入拒绝 | S06 人类意图立即进入 foreground，Noting 随后维护 Notebook；不执行 Memory/Skill 持久化 |
| R06：02 §3.3–3.4、§5.10；A10 | T2 immutable Snapshot / atomic pointer | T2；核心 schema/MRO 由主会话接 | 同 `_execute_write` 内 `_conn` 校验有效 Anchor、INSERT complete Snapshot、按 path 最新有效 Anchor 重选 pointer；不按 created_at | 中途失败、两 Anchor 逆序完成、rewind/commit race、invalid Anchor、insert-only | S07 旧 Anchor 合法迟到可提交而 pointer 不倒退，失败/未完成不产生 Snapshot |
| R07：02 §3.5–3.6、§6.18 | T2/T5 Notebook show 与 `/notebook[ on|off]` | T2 renderer/DB；T5 shared surface Agent，正式 registry/CLI/Gateway/TUI | global off 不可用；local off 人类仍可读已有；AI show gate；created_at 可见，Anchor/pointer ID 隐藏，null 明确提示；正常 transcript/display 行为 | 正式 catalog/completion/dispatch + live session + 两层开关；JSON/human rendering 区分 | S08 Web UI 补全、查看、开关，状态持久且不增 display_kind/role |
| R08：A06–A07、A14–A15、A17、A19 | T5 `/propose-persistence` → live target candidate/provenance → Prompt-trigger normal main Turn | T5；新增 Prompt/CLI/Gateway Slash sibling，复用现有 send directive | 无结构化参数，保留尾随 user text；只 propose；global off 不可用；local off 读取旧候选；后续自然语言批准，无批准 UI | live session/global/local/no Snapshot/no candidate/普通尾随文本；命令不触发Noting，不直接持久化 | S09 提议 Memory/Rule/Skill，核对原文，用户自然语言修改/否决/批准后已有能力执行 |
| R09：02 §4.1–4.5、§4.10、§6.6 | T3 Idle/global/local config：真实 main Turn start/end → per-Conversation timing → admission | Noting 实现 Agent；新增 `secretary/noting_policy.py`、`secretary/noting_runtime.py` 与 siblings；既有配置与turn seam薄接线 | only main Turn resets Idle；global AND local gate；所属 profile 显式绑定；原生 idle-compaction 冲突按02现行配置链处理 | 假 clock 只测时间不假 OS；真实 Turn hooks 排除child/delegate/hygiene；off inert | S10 无主 Turn 后 Idle admit；非主后台活动不重置，无新调度器 |
| R10：02 §4.6–4.9、§4.11–4.13；A23 | T3 Force：已有 measurement/已解析window-threshold → 精确公式 → DB admission → internal passive Reminder | T3 + T4；DB admission sibling 由 T3 实现并主会话安装 | K=1000；only `<64000` / `reserve>128000` capability failures；sameAnchor UNIQUE；不同Anchor并发；success 从forceSnapshot+boundary派生 | 三measurement seam实际调用、严格边界、无clamp、同Anchor并发一次、不同Anchor并发、最新boundary派生 | S11 压力在native compaction阈值前触发Force，保持Hermes计量/原压缩行为 |
| R11：02 §5.1–5.3；A16、A22 | T3A parity extraction / 旧产品移除 | Noting Agent；`agent/background_review.py` 等 helper；surface清理T5串行做 | `/btw` 保持现有调用入口与不持久化constructor；`build_cache_parity_fork()`内部复用抽出的pure helper，Noting独立持久化constructor复用同helper。helper不处理sessionID/DB/persistence/lifecycle，不将原constructor改成带模式flags的通用工厂；旧config/spawn/queue/cancel入口停用，`/review` 保留 | `/btw` persistence-detachment、parity与行为回归；旧Review不触发，旧switch/refine不再入口；兼容历史usage/write-origin不按同名误删 | S12 新生态位只有Noting，关闭时不恢复旧Review，既有btw方案继续有效 |
| R12：02 §5.4–5.5、§5.8、§5.11、§6.7、§6.16 | T3 persistent child：dedicated DB/profile → independent child ID → frozen Parent Active prefix + task suffix → strong owner → close | T3；delegate-style DB lifecycle、cache-parity helper、session persistence sibling 薄接线 | 不branchseed/共享Parent session；durable只childsuffix，首行user noting-task；same model/provider/reasoning/tools/prefix parity；不挂Parent中断链、不resume | prefix字节/schema/runtime一致；真实DB仅suffix；构造异常/close释放；Parent新Turn不取消；crash/incomplete不commit | S13 可审计child，强ownership，进程寿命内完成，重启不resume |
| R13：02 §5.7、§5.8、§6.16 | T3 narrow dispatch / same-child bounded continuation | T3；inline/invoke/sequential/concurrent execution seams | 可广告Parent tools parity，但actualdispatch仅History/Notebook；特殊profile多Turn同child，无autoCompaction；terminal failure不commit | filesystem/Web/Memory/Skills/delegation/connector等所有实际执行路径拒绝、concurrent scope传播；同childcontinuation | S14 Noting没有外部写能力，main没有Notebook mutation |
| R14：02 §5.9、§6.6 | T3 native `compact_parent` 薄接线 | T3；`agent/compression_facade.py` / native压缩 siblings / host现有maintenance seam | 重读usage；低于阈值、原生已inflight或已在lease/fence安全检查后admit才成功；不等待最终压缩完成、不force绕cooldown、不以线程启动当admitted | 真native admission成功/拒绝/lock holder/late failure/rotation；特殊顺序work→success→Anchor→commit | S15 Force特殊profile推动原生compaction；之后native失败不rollback有效Snapshot，无第二admission |
| R15：02 §3.8–3.10、§6.10、§6.17 | T4 Schedule registry → Notebook事务reconcile → profile-bound scan_due/atomic claim | Reminder 实现 Agent；新增 `hermes_state_secretary_schedule.py`、`secretary/schedules.py`、`secretary/reminders.py` 与对应测试 | usesRef/entryID；intent immutableSnapshot/runtime separate；parse_schedule/compute_next_run复用，非Cronjob；disabled不扫不删intent | concurrentclaim、dueoccurrence/重启、off→on overdue once、recurring不无限补backlog、staleintent | S16 commitment/task/watchpoint到期只pending，user_reminder主动，状态durable |
| R16：02 §3.11、§6.8、§6.17 | T4 + T3 request seam：repair后pending pull + neutraluserwrapper → accounting → provider → response-success ACK | T4 service；T3 request assembly / actualresponse接线，串行避免碰撞 | request-only不改durablehistory/prefix；ACK在模型成功响应不在装配；计量包括injectedwrapper，即usageanchor路径也算；failed/replay source timestamp不变 | failedrequest/retry、tool后nexteligible、成功ACK、重启pending、相邻usermerge完整wrapper | S17 用户下一eligible模型请求看到系统提醒，失败不会丢 |
| R17：02 §3.12、§6.3、§6.9、§6.17 | T4 active delivery → trustedroute → existing messaging/TUI ingress与busygate | T4；新增host Reminder siblings + `gateway/run_busy.py`/watchers及 `tui_gateway/session_notifications.py` 薄接线 | currenttip/generation/profile证明ownership；idle原生Turn，busy原子转pending不queue；Web默认attach与指定profile spawn均覆盖 | 两host idle/busy admission、route stale failclosed、pendingfallback、无cron_* session/第二Turn | S18 Web本地idle主动提醒；S19 busy下一request被动提醒，无FIFO未来Turn |
| R18：02 §5.6、§6.5、§6.17 | T3 timestamp/wrapper：sourceevent → 真user marker / synthetic首行wrapper → 正常持久/请求 | T3；`agent/message_metadata.py`、`turn_context.py` 与wrapper helper | 真user独立timestamp行，local off仍有效；三carrier role=user，源time稳定；multimodal/persistoverride/replay均覆盖 | actualdurable row与request、timeoffset、multimodal、replay、不出现新systemrole | S20 用户/任务/两提醒时间语义准确且不重复stamp |
| R19：02 §4.3、§4.12、§6.12 | T1/T2/T3/T4集成关闭回退 | 各实现者定向证据，主会话最终接线核对 | global/local gate贯穿trigger/child/tools/schedule/reminder；History/timestamp继续；notebook旧Snapshot人类可读；nativeHermes请求/压缩/admission回退 | globaloff与localoff真实formal链路，开关/restart/compaction，不只是helperunit | S21 开关边界完整，没有旧Review恢复或隐藏Noting行为 |
| R20：A02 | T6 少量通用System Prompt文本调优 | 主会话，现有native prompt composition所属 sibling | 不加机制/个人persona；不midconversation重建rootprompt；具体文本随最终核心行为核对 | diff/现有promptassembly与cache前缀证据 | S22 主Assistant理解原文/Notebook/persistence提议边界且不误写Notebook |
| R21：A05、A24–A26；02 §6.19适用收敛 | T5/T7 shared Slash→官方Dashboard E2E | T5 native registry/dispatch；T7独立验收，无React默认白名单 | catalog/completion/exec/dispatch自然获得；已查到TUI pending-input集合是shared执行缺口，不是Webrendering缺口；无新RPC/DTO/Notebook面板 | 真catalog/completion/send/output链路，WebPTY真实runtime；只证明consumer缺口才薄兼容 | S08/S09/S18/S19/S21在官方WebUI通过；目标0Dashboardpatch |
| R22：AGENTS、本轮适用01DoD与02§6/最终不变量 | T8独立Verification→Validation→主会话交付核验 | 全新fork_turns=none独立审查者；分别只写本轮报告/本地证据，主会话final-delivery | 交付commit明确；一次必要扩大检查由主会话安排，共享同版本证据；失败定向修复/复验；macOS实测，其他平台如实边界 | 冻结原文逐条提取+机制正式接线证据；另一人内置浏览器用户完整链路；禁止mockOS宣称跨平台 | 所有范围内阻断/证据缺口关闭，两门禁通过并当前版本支持完成声明 |

### 任务契约、白名单与阅读分派

所有 Development 完整读根 `AGENTS.md`、`CLAUDE.md`、本计划、索引、baseline、`executing-plans/SKILL.md`及分派冻结原文。02固定1,978行；章节名与行数均基于冻结提交核对，文件不改。共同必读最终不变量1942–1978，分区文档只架构参考。相应测试文件可新增/修改，但不改runner/checker/门禁规则或安装依赖。

- **T1 Foundation**：02 §1–2（13–634）、§3.1（637–668）、§6.1–6.4（1666–1724）、§6.11/13/14（1813–1821、1841–1866），跨章 §3.3–3.4（681–730）、§4.8（1199–1218）、§5.10（1632–1650）。薄接线白名单 `hermes_state.py` MRO、`hermes_state_schema.py::_init_schema`、`agent/prompt_cache_scope.py`可信locator、`agent/inline_tool_executors.py`、`model_tools.py`、`toolsets.py`、`agent/agent_init.py`；与T3共享后者串行。若需新增具体原生lifecycle hook，报告主会话后交集中接线，不扩大白名单。
- **T2 Notebook**：02 §2.5–3.7（362–811）、§3.8–3.10（812–928，与T4intent接口）、§4.1–4.3（1027–1095）、§4.8（1199–1218）、§5.7（1522–1564）、§5.10（1632–1650）、§6.1（1670–1679）、§6.11–6.14（1813–1866）、§6.16/18（1878–1890、1906–1917）；索引A10/A14/A15。MRO/schema/rewind/branch薄接线由主会话基于返回接口集中完成。
- **T3 Noting**：02 §2.1–2.4（249–361）、§2.6–2.7（567–634）、§3.1–3.4（635–730）、§3.7（797–811）、§3.11（929–969）、§4–5全篇（1027–1665）、§6.5–6.8（1725–1783）、§6.12/15–17（1822–1840、1867–1905）；索引A11/A12/A16/A22/A23。正式接线白名单为 `agent/background_review.py`、`review_idle_queue.py`、`turn_facade.py`、`turn_finalizer.py`、`turn_context.py`、`turn_context_compaction.py`、`turn_preflight.py`、`turn_request_assembly.py`、`session_persistence.py`、`message_metadata.py`、tool execution/invoke siblings、native compression siblings、`hermes_cli/config_defaults.py`及既有config验证/hotreload。`agent/side_question.py` 默认不改，现有constructor签名与返回值继续有效。`run_agent.py` 仅由主会话按实际必要薄接线；旧surface清理由T5完成，避免共享改动。
- **T4 Schedule/Reminder**：02 §1.4–1.8（82–248）、§2.5–2.7（362–634）、§3.8–3.12（812–1026）、§4.1–4.3（1027–1095）、§4.13（1313–1319）、§5.6（1435–1521）、§6.3/8–12/17（1694–1710、1765–1840、1891–1905）。host薄接线白名单 `gateway/run_busy.py`、`run_watchers.py`及必要Reminder sibling、`tui_gateway/session_notifications.py`与新Reminder sibling；不改WebPTY/React/publiccontracts。requestassembly/responseACK由T3接，T4只提供service/receipt接口；schema/MRO由主会话接。
- **T5 shared Slash与旧surface清理**：02 §2.5（362–566）、§3.5–3.7（731–811）、§4.1–4.3（1027–1095）、§5.1–5.3（1320–1383）、§5.7（1522–1564）、§6.12/18–19（1822–1840、1906–1941；6.19按A26收敛）；索引A05–A07/A14–A17/A19/A22/A24–A26。白名单 `hermes_cli/commands.py`、`commands_platforms.py`、新增CLI/Gateway Slash/Prompt sibling、`hermes_cli/cli_commands_mixin.py`必要路由、`gateway/slash_commands_goals.py`、`run_busy.py` handler表、`tui_gateway/methods_tools.py`、`methods_slash.py`、`server.py` pending-input/旧callback、`compute_host.py`与host旧Review callback清理。旧`/refine`静态目录/帮助删除可按A16/A22精确清理；不是新增desktop功能。与T3/T4涉及同文件时串行。
- **T6/T7/T8**：主会话完整02已读；Prompt按A02少量文本；实际浏览器验收经完整Verification后由独立Validation进行。两个独立门禁各自完整读冻结四类依据，不能只读Development分区。报告/证据白名单在派遣时明确；不让审查者修改实现。

内部接口初稿：`SessionDB.resolve_conversation_ref(session_id, trusted_declared_locator=...)`、`get_history_foreground`、`get_full_foreground` 与显式同conn path/Anchor helper；Notebook提供task-local semantic state、完整Snapshot commit/local-enable/pointer/inheritance；Noting提供atomic sameAnchor admit、strong registry、Parent frozen-prefix与profile runner；Schedule提供事务intent reconcile、due claim、pending pull/response receipt ACK与active admission结果。所有内部服务显式接目标DB/profile，不能用launch profile或全局工具DB代替。

## 当前状态与编排

基线只证明文档冻结，尚无Secretary实现或真实模型证据。每个任务的**机制实现、正式接线、针对性验证、用户结果**四项状态及负责Agent在根 `CLAUDE.md` 维护，不在此建立第二看板。

执行序列：T1先行 → 主会话review/ref与path接口 → T2完整Notebook → T3/T4在独立siblings内并行 → 共享core接线串行 → T5 shared Slash与旧surface清理 → T6最终Prompt文本 → 集成收敛 → T8 Verification → 独立Validation（T7入口）→ 主会话交付判定。T3A纯parity抽取可以与T1并行，但不修改T1正在接线的初始化/core文件；T2 semantic model可提前独立准备，但正式DB/commit交付须等待T1接口。任何共享文件修改必须主会话明确切换ownership后进行。

主会话亲自核对返回的原文覆盖、机制/约束、接口、真实上下游、状态/失败路径与证据；不复跑有效测试。集成代码变化、失败修复或证据存疑才定向复验。缺口形成下节整改，不启动碎片级独立门禁。

进入Verification条件：范围内实现全部正式接线、定向证据完整、共享接口一致、已review并创建明确待审commit。由主会话指定唯一一次扩大测试的执行方/commit/范围，包括实际受影响Python suite、保留checks、受影响JS workspace/必要构建；日志进本地隔离证据目录，根CLAUDE记摘要/耗时/次数。Validation随后真实使用官方Dashboard localhost，通过内置浏览器执行S01–S22适用链路及验收者独立提取的其他场景；无法观测的机制用当前同版本证据核对，不用unit替代用户输入到输出。

## 缺陷与整改、取舍与快照

| 编号 | 现有事实 / 风险 | 对应任务与关闭证据 |
|---|---|---|
| P01 | 基线没有02要求的`session_history`模型工具；UI同名模块和跨会话召回不等价 | T1真实工具注册、当前Conversation-only search/read、main与Noting复用证据 |
| P02 | display历史按内容键去重；generation当前counter、compression siblings与branch只复制Active可能破坏身份/path | T1 UID/path/tip/generation证据；T1/T2原文引用型branch继承和parent后续rewrite独立性 |
| P03 | 现有cache-parity fork是detached，`/btw`仍复用；直接删或直接当persistent Noting均错误 | T3A purehelper抽取保留btw；T3 child transcript仅suffix/独立DB/strongowner及旧产品停止 |
| P04 | native压缩入口同步；线程启动或lock-skipped不能证明admitted | T3 lease/fence安全检查后的真实admission ACK、失败信号与特殊commit顺序证据 |
| P05 | Web默认profile attach现有内存TUI gateway；显式profile spawn独立TUI gateway，不是messaging adapter | T4两host既有ingress/admission、Web两profile路径idle/busy证据；不得只改messaging Gate就称Web闭环 |
| P06 | Prompt slash落isolated worker会丢正常主Turn；现有send union/completion无需React patch | T5 live handler+pending-input集合注册，真实tailtext/send/catalog/completion/output证据，0Webpatch目标 |
| P07 | 新request-onlyReminder成本可能被usage-anchor覆盖，提前ACK会丢失败请求提醒 | T3/T4正确accounting与success receipt ACK、fail/retry同source time证据 |

以上是基线缺口与必须防止的偏离，不是已发生实现缺陷。后续实际缺陷在本节追加要求、触发输入、版本/位置、负责人和关闭/复验证据；动态状态同步根CLAUDE，不擅自改要求或门禁。

初始可回退快照为冻结提交 `5346cd094b6a1bb6c6d9ce69e83b3a1570cf46bd`。后续主会话在review后的集成节点本地提交，准确声明已验证范围与剩余项；`baseline.txt`始终保留初始文档基线。索引/一级02不可随实现设计漂移；发现要求变更走授权流程，执行设计调整只影响本文与根CLAUDE。当前未运行模型、功能测试、完整suite或独立门禁，也未部署/发布。
