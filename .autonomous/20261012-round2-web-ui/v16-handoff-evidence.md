# T5 · V1.6 移交证据适用性与最小补验清单

> Development 研究交回；不是独立 Verification / Validation，也不作门禁 PASS。
> 核对日期：2026-10-12。产品交付基线 `edd031f5518955a10a2c68210e1c65477d6f0991`；本轮文档冻结 `37ad76f5dfac02d4774d5e0faea55911b5fb8de9`；观察 HEAD `8e7ba807f8f4f827f947e5e4184f46173d80cfd2` 加合法进行中的工作区增量。源码/hash 是本次观察快照，不自动覆盖其后继续施工的版本。

## 1. 任务对应条款与结论

本次只核 V1.6 移交未闭合项和本轮后端实际变化影响。依据为旧轮 continuation-guide、validation 最终阶段（L282 起，CU03 剩余、CU05–08、CE01、VAL04）、verification 的 82cd557 收口、snapshot-index/baseline/final-delivery，以及本轮索引 C04、06 §4.6。已按派遣完整读现行 02 §1、§2.5–2.7、§3、§4.1–4.5、§5.6、§5.10–5.11、§6.1–6.6、§6.8–6.18、最终不变量，并补读 §5.12 Reminder / Persistence Target；04 §6/§7 未被覆盖的增量。

**结论：旧证据可分项复用，真实移交缺口仍未闭合。** C15/C16 施工和定向机制证据存在；C16 最新机制证据并非被其初次失败全盘否定。旧 82cd557 的 Verification PASS 只对应该历史产品；随后 VAL04 的真实 busy 反例保留。C15/C16 在 edd031 收尾后没有真实最终复验。当前工作区增加了观察、Pending、Usage、压缩取消与 idle-only 提交接缝，须补变化影响，不能拿旧整版 PASS 覆盖。

不重做 V1.6 自身全量 Verification，不机械复跑有效测试。第二轮自身两个完整独立门禁仍依本轮计划执行。Full 审计 UI 属 06 延后范围，不能为补 CU08 提前造接口。

## 2. 实际变更与只读核对产物

唯一正式新增文件为本报告；小型核对产物在 ignored `.hermes-dev/round2-evidence/v16-handoff/`：

| 产物 | 内容和用途 |
|---|---|
| `source-and-artifact-audit.json` | 当前关键源码 hash、与 edd031 相同与否；旧/新 manifest 的逐文件匹配；历史证据文件完整性 |
| `old-profile-summary.json` | 旧合成隔离 profile 的只读计数、条目类型、Snapshot/Anchor ID、Child 状态、Idle/local 状态；不包含对话长原文或 memo 正文 |

未改产品、其他报告、根文档、plan、runtime、配置或定时器；未 stage/commit；没有正式测试、服务操作、模型请求或外部持久化写入。SQLite 用 URI `mode=ro` + `query_only` 读取含 WAL 的逻辑状态，不导入产品模块。DB 和 WAL 读取前后 SHA256 不变。最初 immutable 只读探查不作为含 WAL 的最终状态依据，正式摘要已按 mode=ro 重新核对。

旧 profile `.hermes-dev/v1.6-validation/dashboard-final-4743943e` 当前仍是：6 Sessions / 157 messages / 5 Snapshots / 5 admissions / 5 Children，Children 全 completed，memo 0，memo archive 3；Schedule/pending Reminder/branch rows 均 0；现有 item 只有 2 decision、1 open_question。它是 History/Notebook/memo 证据可复用起点，**没有 CU05 Candidate 或 CU06–08 已执行数据**。未读取配置凭据、私人 Pi 库、用户生产 HOME 或 docs/archived；未干预 round2-runtime。

## 3. 正式路径和本轮变化影响

### 3.1 实际变化的边界

| 路径 / 当前变化 | 影响的旧结论与适用性 | 下一步最小证据 |
|---|---|---|
| `secretary/noting_runtime.py`、`hermes_state_secretary_noting.py` 与 edd031 相同 | C16 Main start/end、global lifecycle gate、统一 event claim、off 消耗、on 准入、expected-period 原子性未被本轮改写；82cd 旧 Idle 结论被 C16 覆盖，不继续当最终证据 | 复用 C16 定向机制；真实 C16/VAL04 + cold 旅程仍必需 |
| `secretary/noting_timers.py` 新失效通知与 `idle_timer_observation` | timer arm/cancel/fire 原机制未重写。只读观察不 attach/recover；UI local-off 显示 `next_idle.absent` 是后台有效性呈现，不代表取消了真实 timer，也不能用它证明 C16 timer 仍运行 | reads 已有 21 timer 回归可复用；实际 off 到点用合法自然时钟及状态/无 Child 取证，不仅看 Orb |
| `secretary/noting_child.py` 真实 registry start/finish 与成功 commit 后通知 | Child dispatch/冻结前缀/五 Turn/terminal/commit Gate 主体不变；Finish 时间 formatter 未被此轮改写；observer 位于原锁/事务返回之后 | reads 真实 Child Loop 证据复用；新 Web running→finish/Notebook 重读与时间显示取证，不重灌旧特殊高 token 分支 |
| `hermes_state_secretary_notebook.py` memo/local/commit wrapper 成功返回后 observer | 原 conn/SQL/schema/事务/消费身份未改；Archive、精确 memo 消费和 pointer/Schedule reconcile 历史结构证据仍适用 | 新 Web 只读前后无写、事件按 owner 重读与正式新链路由 T4/第二轮验收覆盖；旧 memo 四操作不重做 |
| `agent/turn_api_call.py`、`turn_usage.py`、`turn_context.py` / `turn_finalizer.py` 与 `prompt_turn.py` 的 usage 委托 | observe 在 Reminder verify 后，真实 dispatch/返回/异常仍原生，Child 被 `_main` 排除；冷 Session usage unknown 不等于 Notebook 冷恢复失败。改变了同一 Main/Tool-loop/终结接缝，旧 response/ACK 不能无条件冒称当前 runtime 已验 | usage 23 项有效机制结果复用；CU07 在下一真实 request 携带 deferred 并成功 ACK 的旅程补当前边界 |
| Pending owner：`interrupt_control.py`、`agent_runtime_helpers.py`、`turn_iteration_prep.py`、`turn_context.py`、`turn_finalizer.py`、`prompt_turn.py`、`session_lifecycle.py` | legacy 无新 owner 保原路径；opt-in 下插入/停止/尾部 handoff 正式接缝变化，可能触及 active Main 时序、Framework busy 尾部及第二 Turn。不改 Notebook/Reminder 存储本体 | Pending 109 项已接收机制证据复用；VAL04 busy 无旧 Idle、CU07 无额外 instant Turn；若在这些场景顺带用 Web correction，记录真实 epoch/Turn 和尾部事实，不扩为旧轮全组合重测 |
| `agent/compression_facade.py` 新 observation / cancel 在原 registration/fence；fallback 继承 cancel | 原生压缩发布/Continuation/C13 retirement 主体未改。新取消是当前用户入口，不能只靠旧 C09/C13 PASS 证明此入口；read owner 已取得真实 DB/facade/Noting admitted→Snapshot→cancel 的定向证据 | 复用 reads 19 个压缩机制用例和既有 C13 正式原生证据；本轮 T3 压缩 UI 取消场景覆盖，不再做旧特殊模型全分支 |
| `tui_gateway/methods_prompt.py` 新 idle-only 提交委托 / images | 当前仍施工。Web 新 Send 入口，旧 prompt.submit 委托至新 sibling；真实 Reminder 入站仍走 `session_notifications._secretary_deliver_claim` 的既有 `_session_turn_admission`→`_run_prompt_submit`，不走 Web submit_idle。共享 Turn 执行和收尾有影响 | 等 T3c 完整交回及 Main review。CU06/07 实际 Reminder entry 和第二轮 old-client compatibility 都要有当前版本证据；本报告不提前判新 sibling 通过 |
| `secretary/web_read.py` / `web_events.py`、`methods_web_read.py`、全局 config 成功写后通知 | 新只读接口和失效 hint，未建立调度器/存储。`secretary.notebook_read` 是新 Web transient 人类入口；旧裸 `/notebook` 的普通持久反馈证据不等于新瞬时读已验 | 新 Web `/notebook` + Secretary UI 按 T4 已明确入口取证；本报告只补 C15/只读 owner 与旧数据复用边界 |

历史 source hash 任意变化不一律废弃整套证据：按上述真正改变的接缝和语义判断。当前关键 identity/Foreground/item/store/reminders/History 原始数据源和 native branch/undo 本体与 edd031 相同；C15 只改输出表示的旧时间结论必须补新表示，原文连续性和身份结论保留。

### 3.2 应走的实际入口

- 第二轮用户旅程：最终重建的 Web + 真 REST/WS + 原生 Main/Noting + 已配置 DeepSeek；`/noting` 和 `/propose-persistence` 走现有 `command.execute` / `methods_secretary._cmd_secretary`，proposal 返回原生 `type=send` 后由正常 Main 执行。不能手工调用 child/trigger/tick 代替用户路径。
- Web 人类 Notebook：`secretary.notebook_read` 复用 renderer，瞬时只读；模型 Notebook：真实 `notebook_show`；History：真实 `session_history` search/read。两者时间源均核现有存储 instant。
- Reminder：原生 notifications poller→`scan_and_claim_due`→`_secretary_deliver_claim`→原 `_session_turn_admission`；idle instant `admit_active_reminder`→`_run_prompt_submit`；busy 转 pending；下一真实 Main request before-build→durable 单 batch→实际 carrier response ACK。
- Persistence：现有本地 `memory` 工具写所属隔离 profile 的 `memories`；不是 Nowledge Mem，也不引入 Memory Provider。若原生写审批返回 staged，须完成其合法批准并证明实际写入，不能以 staged/模型口头成功冒充执行成功。
- branch/undo：真实 native `session.branch`/共享 Slash，以及用户可达 `/undo` 或本轮既定 Rewind/Edit 正式路径；后者若仍未接通，记录入口阻挡，不改库伪造 rewrite。Full 只可复用既有内部只读诊断及真实 Prelude/Anchor 事实作辅助，不能新增 Full UI/API。用户主要结果从 History、Notebook、父/分支恢复判断。

## 4. 验证结果与真实证据复用表

### 4.1 完整性、观察版本和限制

- `verification-final/verification.final-manifest.json` 是 **ce2fa6f**，其 7/7 artifact hash 匹配；不是 edd031 全版 PASS。
- `verification-closeout/final-manifest.json` 是 **82cd557**，11/11 artifact hash 匹配；正式历史结论 73 组、72 符合、1 后续阶段 NA。C15/C16 授权和 VAL04 在其后，不能据此清掉移交缺口。
- `validation-closeout/stage-manifest.json` 是 **82cd557**，57/57 evidence hash 匹配；CU01/02 和 CU03/04 有效子结果保留，CU03 剩余及 CU05–08 未执行、VAL04 失败仍保留。
- `root-closeout/implementation-end-manifest.json` 是 **edd031**；71/71 source hash 全部与该 Git 树匹配，当前工作区 69/71 相同，仅 Child/timers observer 不同。`readable-times/source-manifest.json` 63/63 同 edd031，当前 62/63 相同，仅 Child observer 不同。
- 82cd 的 66 源码清单当前 48/66 匹配，18 个变化混含后续 C15/C16 和本轮接缝，不能凭 18 个变化报整套失效。完整逐文件当前 hash 和 equals_edd031 在 ignored audit 中。
- 第二轮 reads manifest 12/12 当前匹配；usage final manifest 15/15（含规格/锁）匹配；Pending manifest 10/13，三个已释放给 usage/Main 的 `turn_context.py`、`turn_finalizer.py`、`prompt_turn.py` 后续修改。按现行 usage manifest 和本表审这些薄增量，不能拿 Pending 原 hash 宣称这三文件完全没变。

下表路径均以 `.hermes-dev/v1.6-evidence/` 为前缀，第二轮路径明确写出。测试日志均为既有结果，本次运行正式测试次数为 **0**。

| 要求 / 历史已证明部分 | 精确证据与观察版本 | 当前可复用范围 / 需补部分 |
|---|---|---|
| History 跨压缩、keyword/regex/user、长行截断与精准全文 | `validation-final/U01/` 真实旧旅程；`validation-closeout/CU03/cold-off-C12-proof.json`、`cold-off-completed.{dom.txt,png}`（82cd）；C12 单 Ref/单 UID 四字段真实结果 | 保原文连续/身份/精准查源和当前 source 准备。C15 `row.timestamp` 从 epoch 变可读后，只补代表真实 result 与原 instant 相等，不重建 35 项旧长源 |
| Notebook 六键、裸 Anchor 可精准查源、人类 515 字长文、local-off 阅读 | `validation-closeout/CU02/show-six-key-proof.json`、`show-anchor-*`、`long-notebook-original.{dom.txt,png}`、`local-off-human.*`（82cd） | 六键/权限/正文/Anchor 事实复用；旧 numeric last_update_time/Created-at 不是 C15 成功。新 Web transient 与当前时间显示须补；不机械重做旧全文准备 |
| local-off 窗口 root/schema 不变、无后台 | `CU02/local-off-proof.json`、`local-off-after-idle30.json`（82cd；观察相隔 154.374s） | 正常读门禁/schema/历史 Snapshot 不删除可复用；旧未处理 deadline 机制被 C16 修订，不用旧“off 无后台”推导 off timer 被取消或 on 不补 |
| memo 四操作、auto-enable 反馈、连续编号、非空 off 拒绝 | `CU04/memo-six-actual-results.json`、`memo-six-completed.*`、`nonempty-off-rejected.*`（82cd） | 操作结果与数据身份复用；auto-enable 是已观测事实，但同 Main 内旧 Idle 准入失败保留，不能当 VAL04 关闭 |
| 同任务 memo 冻结消费、替换/删除保留、下一自然30秒消费 | `CU04/after-finish-state.json`、`memo-natural-timer-proof.json`、`post-consumption-*`（82cd）；`child-memo/` 正式机制及 `verification-closeout/coverage.final.json` 对应 memo 行 | 第二个自然 timer 30.0s、lateness约6.3ms，Snapshot/同 Anchor archive 与空 memo事实有效。只复用消费不变量，不把第一 busy Trigger 算合法；新 observer 不改变消费 SQL |
| VAL01 单条英文 Finish、即时用户可见、后续不自激；VAL02 长文 | `CU04/instant-finish.*`、`natural30-finish.*`、`post-consumption-completed.*`，`CU02/long-notebook-original.*`（82cd） | 原用户可见缺陷已真实关闭。保结果及首次失败。C15 时间字符串与新 Web Timeline 呈现是实际变化，需要补新 UI 结果；不重跑旧通知版本旅程 |
| C16 统一 deadline、off只改偏好、off事件消耗不补、on一次、busy取消旧周期 | `idle-busy-fix/c16-minimal-tests.log`（48 pass/1 fail）；`c16-failed-final.log`（原失败单项1 pass）；`c16-affected.log`（15 pass）；最终 source 对应 edd031 | 不同用例 48+1+15=64；失败 fixture 原先在 Main Force preflight 后继续把 local 读数当 Idle读数，最终测试只在真实 Mainend 后开始观察，保两份失败日志。实际 Main/SessionDB/daemon/claim 是生产，provider 返回和 spawn 受控；不是真实 DeepSeek/cold 验收。runtime/DB claim 当前同 edd031；timer observer 由 reads 21 legacy timer 回归补影响 |
| VAL04 实际 busy 反例（不是通过） | `CU04/VAL04-busy-idle-finding.json`（82cd）：Main driving1791796722.572049→旧Idle admit6727.605147→Mainfinal6737.116671 | 原反例完整保留。C16修复不能仅靠 normal-on 自然 timer成功关闭；必须真实 localoff→跨due→busy Main memoauto-on 无旧准入→Mainend 新周期复验 |
| Reminder ACK/失败/drop/compaction拒投/重启、原生 busy gate、Schedule once/offon 机制 | `integration-group-0.log`…`integration-group-3.log`；`verification-closeout/coverage.final.json` E15/E16与相关行；真实测试名 `test_v16_delivery.py`、`test_active_reminder_admission.py`、`test_active_reminder_crash.py`、`test_active_reminder_persistence.py`、`test_schedules.py` | 旧正式机制可复用，当前提醒/调度状态本体及 admission 原代码没被改；C15 due_at 表示和本轮 Main dispatch/收尾增量需 CU06/07 当前真实用户结果。0 Schedule的旧库绝不作为实际提醒通过 |
| Persistence proposal不预贴源、只提案/批准/实际执行分离、archive权限/不可恢复 | `verification-closeout/coverage.final.json` proposal/item行；原生 `cli_secretary_commands.py::propose_persistence_command`、item/store源码与 edd031相同 | 机制/权限可复用；CU05没有任何实际用户写入旅程证据，必须执行剩余代表 Memory 全链。无 Candidate 的旧库不能跳过真实准备 |
| branch/undo有效源/Ref/Anchor重绑、pointer与Schedule reconcile、Full唯一Prelude/compound | `verification-closeout/coverage.final.json` E02/E03/E24；`validation-final/U08/post-compress-full.json` 已有真实Full辅助观察；对应 native branch/rewrite/Foreground代码同 edd031 | 同源机制可复用；真实 branch/undo用户旅程尚未执行。既有 Full 内部证据仅辅助来源核对，新 Full审计UI延期，无新增接口义务 |
| cache/Child terminal/forced/overflow/父原生压缩/C13 | `verification-closeout/{native-wire-independent,special-wire-independent}.json`；`native-compaction-fix/real-native-handoff.json`；`force-notice-boundary/same-turn-observation.json` 等正式C13证据 | 旧19真实 wire/prefix/cache事实保留，旧55e92 forced/overflow newMain live/DB失败不能整条称PASS。本轮 Child observer/usage排除/原fence取消已有新的受控正式机制证据；不重新灌高token重做全特殊分支 |
| 本轮观察/取消/只读与旧 timer影响 | `.hermes-dev/round2-evidence/reads/{formal-and-error-tests.log,queue-preservation.log,child-final.log,final-targeted.log,source-manifest.json}` | 53不同用例：27自身读/压缩＋1Child＋4legacy fence＋21legacy timers，当前12hash匹配；不是实际53445/Web用户已验 |
| 本轮 Main dispatch/usage、Child/压缩计数隔离 | `.hermes-dev/round2-evidence/usage/{final-tests.log,final-source-manifest.json}`；usage-implementation报告 | 23不同用例、4文件、11.8s；当前15hash匹配，异常/原生fallback/cold unknown/真Noting隔离有效。未专门替代 CU07的真实 Reminder response ACK |
| 本轮 Pending原生/关闭/rotation机制 | `.hermes-dev/round2-evidence/pending/{final-owner-lock-tests.log,last-integrated.log,final-regression-first.log,concurrent-operation.log,activation-race.log,source-manifest.json}` | 109不同用例已由Main接收，原日志失败保留；3生命周期文件后有usage薄接线，须按影响与新manifest核，不为接收而重跑109 |

C15 其它既有呈现结果可复用：`readable-times/last-interface-tests.log` 78 pass；`final-native-tools.log` 79 pass/1平台skip；`final-native-schedules.log` 101 pass；`final-small-tests.log` 42 pass；`desktop-restored-tests.log` 2文件19 pass；相关 Web/TUI/shared 定向与类型检查原日志保留。`final-secretary-tests.log` 初次 History ISO断言失败已在 final-small 中复验；`baseline-current.json` / `baseline-frozen.json` 中旧 Child fixture `unknown_system_message` 和既有SDK归档限制仍须保留，不能写整版全部检查通过。Desktop 完整 suite/typecheck缺依赖、跨平台未验证不属于本次小报告新完成项。

## 5. 缺口：可直接执行的最小用户场景

以下是 Main 编排 T5 与后续独立 Validation 的输入；不是本研究 Agent 运行授权。每项均需最终产品 commit/两仓产物、profile/Session/Ref、实际入口与真实时钟、预期/实际/证据边界。时间是预算估算，不保证模型耗时。所有输入用合成唯一标记；主会话协调安全 cold，不更改 due、不调用内部 Trigger/tick、不伪造 busy。用户 C14 已允许隔离 profile 的现有配置暂调 Idle30秒，验后恢复原值；不是代码默认值改动。

### H01 · C15 跨实际面代表取证（可合并 H02–H08）

- 原要求：02 §5.6 C15/§3.5/§3.6/§5.12 Target；实际 AI/human 全部绝对时间带 timezone、保存原instant/source/field/权限；carrier不新增timestamp marker。
- 操作：旧源直接真实 session_history search→precise read，show当前Notebook；新 Web `/notebook` 人类输出；H02 Finish、H06/H07 Schedule due/deferred body 和 instant入场timestamp；Orb observed_at / next_idle、Timeline实际绝对时间。若某旧系统面本轮未变化，复用既有定向呈现证据，不泛开整版Desktop验收。
- 最小判据：AI row.timestamp、last_update_time、task/control可见Schedule、human Created at、Finishcommittime、Reminderdue/entry等均可读带offset；把输出parse回与原同source epoch比较（保存精度），使用owning-profile时区。多个profile owner不串；internal lease/epoch/duration仍数值。旧数字时间截图不能代替本项；自然正文中的数字日期不重写。
- 前置/等待：Main从最终源码重建/重启自己的目标服务；旧source可复用，不重新生成长文；本项自身约2–4次代表Main请求，主要等待合并在其他旅程。
- 新测试/修复：真实AI/UI补验必需；formatter现有hash匹配，尚无本次静态发现要求修源码。新Web时间展示若失败，定向修呈现后只复验失败面。

### H02 · C16 local-off真正到点终结、on分支一次

- 原要求：02 §4.3–4.5/C16，统一deadline读取当前开关，off不取消timer，off事件结束之后on/cold不补；on沿原准入一次，不散落gate。
- 起点：globaltrue、eligible、memo空、Native实际Main，合法Idle30；用真实Main形成周期，及时 `/noting off`。记录Mainend与自然due、off反馈持久；观察跨due时无admission/Child/Snapshot，period已消耗。再 `/noting on`，没有新真实Mainend的窗口中不补旧事件。观察至少一个poll周期，cold后再次确认旧事件不恢复（可合并H04）。
- 另一分支：下一真实Main形成新周期，在due前off→on；自然到点应1 admission/Child/Snapshot/Finish，后续poll/重连无同事件重投。新的Main只会生成新的周期，不能把它计作“补旧”。
- 实际入口：Web共享 `/noting` + 正常Send，真实daemon；只读状态/日志/DB作辅助，不能把 Orb absent 当timer不存在。
- 前置/等待：2个真实周期，约2×30秒+模型/Noting耗时；off必须空memo，否则命令会正常拒关；控制观察不输入新Main以免cancel/rearm。
- 新测试/修复：复用64 C16/21timer机制，不重跑；该真实旅程未执行，源码修复必要性未知，遇失败记录原时序并按影响修。

### H03 · VAL04 原合法 busy memoauto-on→Mainend后唯一新Idle

- 原要求：02 §3.5 memo非Trigger、§4.5真实Main生命周期、§5.10；旧VAL04不可抹除。
- 起点：Native Main已留on周期→localoff→真实时钟跨旧due→仍off的真实Main要求两次memoadd（第1auto-on），随后list/replace/delete/read与最后回答，或同意图真实工具链跨旧poll窗口。不能直接insert due/内部arm。最新C16下off事件应已结束，即使旧deadline无残留，也必须记录“自然消耗旧事件”，不能假造旧状态来复制旧bug。
- 判据：auto-on发生时Main仍busy，当前工具循环/最终回答前无旧Idle admission/Child；最终Mainend才有新due=end+30，自然到点唯一admission→Snapshot/memo消费→单Finish。后续自然读证明结果可用；四操作的契约不用再机械覆盖全套，重点是busy时序/Trigger来源。
- 实际入口：真实WebMain→`noting_memo`→原生工具循环，真实daemon与新版Timeline；同时涵盖当前Pending/usage共享Main接缝的未启用正常路径。
- 等待：跨旧due30秒+新周期30秒+2次模型链路/Noting；若模型没有按合法工具链制造busy窗口，记真实偏差，不冒PASS或无条件重做昂贵构造。
- 新测试/修复：必须真实原序列补验；若发现当前Pending/usage连接导致时序差异，再按失败接缝定向机制测试，现有64通过无需全量重跑。

### H04 · 合法cold：未处理事件恢复 / 已off处理不补 / global warm与coldon

- 原要求：02 §4.1–4.5、§6.18；04 §3.4–3.5/§7.2。区分仍合法未处理事件与已处理off事件。
- A：真实Main结束、globaltrue/localon、还未due，Main核无在途Noting/压缩后安全结束自己runtime/服务；真实时钟跨due，保同profile库冷启动/恢复同Conversation。若有效原生attach在发新Main之前可恢复，observe一次真实catch-up→Child；输入新Main会依法取消旧周期，不能那样声称catch-up通过。
- B：复用H02已经off到点消耗的周期；安全cold→localon不补。不要把“未启动runtime无Framework”误判为通知错误。
- C：复用CU03已过的coldglobaloff+warmon历史事实，补同一Conversation warm true→false→下一真实Turn→true→下一真实Turn，最后安全coldon恢复→show/History。false只有History指导/schema，trueNotebook同步恢复；局部偏好/旧Snapshot保留，启动不偷发Main请求。实际请求Prelude/tool bytes是事实源。
- 入口/前置：Main明确目标profile和合法原生profile启动法，重建正确bundle，验收者不自重启。旧官方prebuilt路径曾合法解决VAL03，不把旧bundle/readiness当新源码用户结果。无需新FullUI；用真实请求/只读内部诊断辅助。
- 等待：2次安全cold与一个自然跨due窗口，约1–3分钟+Main/Noting模型耗时；调度安排可合并H02 B。实际setup取决于Main最终目标实例，尚未知。
- 新测试/修复：cold真实行为未验；静态未见新的cold源码缺陷。若入口不能在新Main前合法attach，标未执行并由Main解决实际入口，不能直接调用内部catch-up。

### H05 · CU05 Persistence：查源→修订不写→批准实际Memory→归档

- 原要求：02 §2.5/§3.7/§5.12-5.1，04 §6/§7.3(4)；Candidate是线索，讨论/修订不是批准，批准也不是归档完成依据。
- 准备：所属隔离profile真实Main先笼统合成偏好、后限定“仅纸鹤验收项目使用中文短段，其它项目未决定，候选但不写Memory”；真实Noting产出Candidate/source。旧库没有Candidate，不能省略此准备。
- 操作：`/propose-persistence` 要求亲自查原始来源/上下文/后续更正，只提案；真实Main自行 `session_history` 原identity read + later correction search。用户再次修订限定范围，明确仍未批准。观察proposal和revision无Memory/Rule/Skill写工具、隔离memories无写；candidate仍effective。然后用户场景明确批准“只执行刚才限定纸鹤项目的这一项合成Memory，仅当前隔离profile”。观察真实memory成功及所属文件/工具后续读取；原生staged审批若存在先合法完成，不算已写。后续真实Noting识别实际执行成功再archive；human/show/下次Child看不到，审计仅辅助。
- 禁止：不调用Nowledge Mem，不写个人Rule/Skill，不由Main直接改Notebook，不仅批准就归档，不用模型口头“已保存”当证据。
- 入口/等待：正常Send、共享proposalSlash、原生 `memory`；约4–6Main请求 +2–3自然Idle/Noting周期（至少60–90秒timer预算）。Memory工具权限/原生approval现场确认，当前是否可执行未知，不能脑补成功。
- 新测试/修复：真实全链必需；proposal/store同edd031的有效机制继续复用。遇Source缺失必须诚实失败，不修改候选provenance或prefetch源来让场景变绿。

### H06 · CU06 Reminder idleinstant + deferred同due批量 + localoff/on

- 原要求：02 §3.8–3.12/§5.6/§6.17，04§7.3(5)；Schedule与Idle off事件恢复语义不同。
- 准备：R提醒Conversation、O观察Conversation；真实Main/memo→真实Noting创建 `user_reminder` 显式 `in 2m` once（relative从合法schedule创建瞬间算，保存实际due）。R idle自然到期原生admission启动1真实Main，O无该标记；无Cronjob/cron_新独立Session，不自主执行secretary_task。
- 批量：真实Noting创建两deferred条目（user_commitment + secretary_task明确delivery_mode=deferred），使用同一个有offset绝对due，给整理和创建留足时间。跨due不发R Main应只pending、无新Turn/无新durable deferred row；随后正常Send→1row `以下提醒已到期。` +两个entry JSON，schedule映射actual due_at可读，无timestamp marker；实际Main正确回应，response ACK后再次自然请求/刷新不重投。
- off/on：真实创建未来once，待Snapshot/memo空后off跨due无fire、Schedule意图保留；on恢复该overdueonce至多一次。它依法可补，**不要套H02 Idle“off处理后不补”**。
- 入口/等待：真实WebConversation/SharedSlash、原生poller与实际Main；3个due窗口（建议2分钟各，模型整理有余量）可与别的观察并行；总自然时钟约6分钟+模型耗时。仅C14配置调Idle，不能直接改Schedule due。
- 新测试/修复：用户链全未执行，机制保留旧结果；若发现批量/carry/ACK或当前submit/尾部缺陷，定向修受影响接缝后复验该分支。

### H07 · CU07 Reminder busyinstant→同Turn下一request deferred，含profile隔离

- 原要求：02 §1.5/§3.12/§5.6/§6.9/§6.17；busy不排未来第二instantTurn，目标profile/Ref可证明。
- 准备：R已真实创建将来once“蓝图-忙碌提醒”，确认实际due；到期前经真实Main亲自使用原有terminal执行不读写文件的短sleep跨due，随后tool返回继续回答。验收者shellsleep不能伪造Mainbusy。
- 判据：due时native busy gate转pending，下一真实request before-build携带单deferredrow，无timestamp、actualdue时间正确；成功response ACK，Main回应真实标记，Turnend不再启动instantTurn；后续自然问/刷新不重复。若模型未执行工具或busy窗口没有覆盖due，记录未执行/偏差，不冒PASS。
- 隔离：同profile O保持无R reminder；另一个Main授权的仓库内隔离profile观察没有R occurrence/消息/任务，owner必须不同真实home/DB，不用单个profile改展示名称来冒跨profile。不能读取私人库或生产profile。现有profile机制证据可复用，但当前实际运行隔离观察仍欠；第二profile合法启动/模型凭据由Main准备，不由本研究Agent复制配置。
- 等待：1个约2分钟due窗口 +真实Main工具sleep/后续请求；profile准备耗时未知。模型工具选择和sleep窗口是场景前置，非内部代码驱动时序。
- 新测试/修复：当前usage包dispatch、Pending收尾和新submit共享路径需此代表真实旅程；旧ACK失败/compaction拒投/SIGKILL机制不重做。若新接缝破坏ACK，再追加真实DB/正式Loop的定向反例。

### H08 · CU08 branch/undo有效源与父隔离

- 原要求：02 §2.6–2.7/§3.3a/§6.11–6.14，04§2.5/§7.3(6)；Full用户UI延期不免除数据语义。
- 准备：已有合法父source/Snapshot/Anchor，不重建旧压缩长源。用户真实branch→新Ref、相同UID重绑、继承branch点有效Notebook；输入分支银色意图→真实Noting更新。合法undo撤回该最后交换→用户更正白色→Main自主History核银色失效不返回，Notebook pointer使用有效Anchor、后续Noting白色；回父恢复读原source/Notebook未污染。不可直接DBdelete或构造Snapshot替代branch/undo。
- 辅助：既有内部Full只读来源可核唯一首Prelude、真实provider-neutral root/tools、Anchor/Snapshot归属；无副作用。compound没有本次自然观察时仅复用已匹配正式同源机制，不为双投影灌昂贵压缩；不制造Full API/UI。
- 入口/等待：用户可达branch/undo或已落实的正式WebRewind/Edit链路，原生Session入口与History；约3–5Main请求+2自然Noting周期（至少60秒timer预算）。06未要求的新branch按钮不能临时添作Full审计产品；若Web未提供该原生操作，Main用合法既有官方入口完成继承V1.6场景，Web自己的Rewind链另按T3验收。
- 新测试/修复：旧identity/store/rewrite机制继续有效；真实旅程未执行。新Web入口或正式prompt claim重构导致失败则补对应定向证据，不重做旧轮全量identity矩阵。

## 6. 接口影响与风险

本报告没有新增产品接口。只引用已经存在/已授权开发的入口；new Full审计UI、Memory Provider、云部署和私人迁移不在范围。

主要取证风险：当前工作区仍可变、服务53445尚不能仅据readiness证明加载当前dirty源码；模型随机未构成busy/候选/同due输入；cold恢复前发送新Main依法消灭旧周期；memo非空拒off污染场景；把Scheduleoffon补投误套Idle不补；profile=''与named profile的native选择误绑owner；newWebNotebook瞬时读误用旧slash持久反馈作为证明；Memory原生staged审批被误算已写。这些须在场景输入/观察记录，不能“修判据”规避。

已知历史限制继续保留：旧Child fixture对照失败、既有SDK profile-archives命中、Desktop整版依赖缺失、非本机平台未测、旧forced/overflow失败。仅受影响路径需要补证，不因此启动旧轮全量复审或大套件。

## 7. 建议后续动作与交回

1. Main先review本报告和ignored逐文件audit，接收可复用证据边界；等待T3c完整交回，固定最终源码/前后端产物与服务版本。报告的hash不是未来版本凭证。
2. Main确定T5实际profile/入口：优先合法复用旧合成源准备；若最终Web只接round2-runtime，在授权运行环境中准备必要合成fixture，但不重构35项旧History或无故复制历史库。旧profile保持原样直到Main合法运行协调；本研究不为选profile自启动/复制库。
3. 开发与集成阶段按H02–H04取得关键真实timer/busy/cold证据；H01顺带取新时间表示。已有64/53/23/109机制结果不复跑。若实际失败才分派局部修复及定向机制复证。
4. 组织H05、H06–H07、H08连续用户旅程；按实际数据/时钟准备与等待，profile隔离由Main提前布置；新FullUI不创建。CU01/六键/长文/memo基础只复用，不作为从头场景。
5. 第二轮独立Verification/Validation接收本报告作实现调查输入，继续独立建立本轮判据与实际旅程；不得把本研究视为第三个门禁或T5已PASS。交付仍明确原失败、剩余未执行、目标版本和实际覆盖。

本次研究完成；V1.6真实补验未开始，范围内原未完项保持未完成。没有已确认的新源码缺陷，也没有通过静态核对关闭任何真实用户缺口。
