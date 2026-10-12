# R2-F14 Cold Parent Active Context 恢复：实施与阶段交回

本阶段是 Development 修复；Main 已集中审查准入四文件设计，随后准入原生 eager claim/build owner 复用及 session_notifications 最小 busy 观察。§1–7 保留原调查与候选设计，**被 §8 的实施修订替代之处不再作为当前方案**。基线为后端 `5ccc619723f39690f11d29ca4b9182d2c6d9d543`；文档冻结 `37ad76f5dfac02d4774d5e0faea55911b5fb8de9`。执行技能及 autonomous-run 子 Agent 阶段交接契约已读；根 AGENTS/CLAUDE、本轮索引/基线/计划已恢复。遵循 R2-C10 同一 owner/恢复提交点；按 Main 最新 R2-C24，机制修复与真实补验继续，独立门禁等视觉 worktree 交回后才开始。

## 1. 对应条款与已核实失败

必读 02：§1 L14–257；§2.1–2.7 L260–645；§4.1–4.10 L1091–1330；§5.1–5.5 L1404–1541；§6.1–6.6 L2221–2301；§6.11–6.16 L2364–2451；Final L2514–2553。按标题额外补读 §4.10 后半 L1331–1344、§5.1 L1392–1403，避免派遣行数未包含完整标题内容。全局关闭/非 eligible 原生不变；local off 只在共同 deadline handler 决策；真实 Conversation Ref/UID/profile、原生 Active、冻结 prefix、同 Anchor admission 和失败不提交 Snapshot 不改变。

H04-A 是真实已正常结束 Main 的合法 cold catchup，非模型/计时器猜测：

| 已存证事实 | 值 |
|---|---|
| owning Conversation | `conv_9d02b19595f34da1b80cad2596f51b6d` |
| stored Session / resumed runtime | `20261012_214809_c5cb3e` / `48c1f787` |
| Main finished / deadline | `1791812895.436746` / `1791812925.436746` |
| event claim / admission | `1791812930.502721` / admission 3，`1791812930.505279` |
| Anchor UID | `78b2c6ab6a4b49ab99d1387d8aeb352b` |
| resume ACK | message_count=2，running=false，status=idle |
| 最终事实 | event有trigger_produced_at、一个admission；无该Conversation Snapshot/child；freeze_parent_active_prefix抛Active unavailable |

源证据为 `.hermes-dev/round2-evidence/v16-live/H04-A-cold-failure.json`、`H04-A-pending-period.json`、`H04-A-resume.json`、`H04-A-catchup-final.json`。仅阅读报告文件，没有访问53445/53446进程或运行数据库，没有读取凭据。admission 的 child/profile 未建立是预派遣失败结果；named profile为null本身不能推定错profile，该隔离home并不是已命名用户profile。

## 2. 准确根因与正式调用链

1. `methods_session._resume_eager` L948–1006 先 `ctx.restore()`，经 `SessionDB.get_resume_conversations` 与 `canonicalize_replay_history` 得到正确的模型历史；构造 fresh AIAgent后交 `_init_session`。冷/延迟路径经 `_resume_cold` / `_resume_deferred`、`server._schedule_resume_hydration` L2950，最终也构造 fresh Agent。
2. 原生 `hermes_state_messages.get_resume_conversations` L1664–1687 已清楚区分：模型为**当前 tip 的 active rows**（保summary、api_content、reasoning、UID、时间与born-durable标记）；display为跨有效lineage的历史。当前恢复数据源完全可复用，不能另读 Full/History 生成Noting prefix。
3. AIAgent初始化 `_session_messages=[]` / `_cached_system_prompt=None`（`agent/agent_init.py` L549/559）；工具是当前构造时的定义（L1066）。host只保存 `session["history"]`，没有把它发布为 Parent 的实际 Active；也没有完成已存 root/tool pin 的原生恢复。
4. `server._init_session` L2743–2773 注册Agent/host history，随后启动服务。deferred由 `_start_agent_build` L1136–1221 → `_attach_built_agent` L1082 → `_announce_built_agent` L1102 → `_start_session_services` L1061。服务启动 poller第一轮即可能到 `session_notifications._maybe_fire_tui_noting_idle` L355 → `maybe_run_idle_noting` L602 → `attach_idle_timer` L90 → `_run_idle_event_locked` L638 → 原 `try_admit_idle` → `spawn_noting_task` L718。
5. 原 timer handler正确领取单次 event/admission；`noting_child.freeze_parent_active_prefix` L141 只接受真正Parent `_session_messages`，因此失败。`spawn_noting_task`捕获预冻结失败，`finish_child_admission(...status="failed")`，不造child、不提交Snapshot；这一失败关闭行为应保留。
6. root/tools还有独立缺口：真正Main `build_turn_context` L1148–1156 才调用原生 `_restore_or_build_system_prompt`，恢复stored prompt、pin tools、plugin/static prefix，并同步当前Main read surface。仅复制history会让 `apply_cache_parity_from_parent` L93继承None root/未恢复的tools，不能构成完整修复。

原生可复用函数是 `agent.conversation_loop._restore_or_build_system_prompt` L767–907、其 `_restore_pinned_tools` L720、`secretary.noting_surface.apply_main_read_surface` / `synchronize_main_read_prompt`。不改这些函数，不自行拼root/schema，不调用run_conversation来伪造Main。

## 3. 建议的最小恢复机制（候选，未实现）

在TUI Gateway原生的 **cold Agent准备→正式attach/服务启动** 阶段恢复它的完整有效上下文；Noting只消费已经完成原生恢复的Parent，原 admission/spawn/freeze/timer都不变。

新增一个普通 sibling，例如 `tui_gateway/session_agent_context.py::prepare_resumed_parent_context(agent, model_history)`：

- 唯一适用分支：owning-profile global Noting已启用、真实eligible Main、有已由原生resume加载的非空模型历史，且新Agent尚未运行Main。global off、辅助child、fresh空Session原路直接返回，不提前构建root，不新增DB/timer/background行为。**不查询local participation，不自行拒绝external/unknown来源**；这些仍归原共同handler。
- 在原建Agent的完整 profile runtime scope 与 session/cwd context内，以原生canonical replay history为输入，调用原生恢复root/tool pin的函数，并沿原Pre-message read surface顺序同步有效root/schema；不加请求、不生成Turn/UID、不记Main-start/end、不改变due_at。
- 结果成为该真实Parent的 `_session_messages`，以及native已恢复的cached root/tools；host的模型history与Parent Active引用/内容一致。保留UID/timestamp/api_content/summary/持久标记；不混display prefix、archive History或Full annotations。持久恢复保持native born-durable markers与已有flush baseline；原root恢复若stage了新的surface控制note，不能将该新note误标已持久。close/后续Main不能重落旧rows。
- 临时恢复副本属于未发布的Agent准备结果，不是Noting冻结prefix或另一个cache；冻结仍只由现有 `freeze_parent_active_prefix` 在实际admission执行。

**两条入口只做薄调用**：

- Eager：`methods_session._resume_eager` 在 `_make_agent_in_context` 已构造Agent之后、**进入 `_session_resume_lock` 之前**完成恢复；保持profile/session/cwd scope。此后沿原双检查：并发winner存在就close未发布loser并复用winner，否则_init_session启动服务。不能在_init_session/服务中做耗时root恢复，因为eager此时已持resume lock。
- Deferred/cold/omit/defer-history：`server._start_agent_build::_build` 在 `_await_resume_history` 成功及 `_make_agent` 返回之后、clear build context/attach之前完成恢复；随后 `_attach_built_agent` 的原publication点安装正确Active并发布agent，才启动原服务。不把新恢复放进poller/spawn或追加一堆ready gates。

**history并发提交**：当前record可在Agent构造期间被合法Rewind/关闭/另一client更新。准备时在既有history_lock短暂取model history及history_version，然后锁外执行可能耗时的原生root/tool恢复；最终在既有attach提交点用同一history owner核对版本与record identity。若版本已变，重取当前原生history完成恢复后再publish；不能把过期Active覆盖新host history。使用现有history_version/record identity，不增加持久epoch、额外gate或调度器。最终锁顺序沿现有短提交顺序（history→sessions，eager已有resume→publication）；不持history反向取得resume，不持sessions/history锁等provider或native恢复IO。实现时以真实屏障确认这个顺序，若实际native回调接缝要求更小调整，先回报具体位置。

已结束off事件继续不可恢复；已failed admission3不重试、不清记录、不新表/flag。修复后真实复验需要由原测试者新建合法正常Main idle period，绝不重复消耗当前失败事件来遮蔽失败。

## 4. 准确候选白名单与为何需要额外server接缝

| 候选文件/位置 | 仅允许职责 |
|---|---|
| 新 `tui_gateway/session_agent_context.py` | 上述native Parent恢复准备，唯一global/eligibility分支；普通qualified helper，不增加RPC/module registry |
| `tui_gateway/methods_session.py::_resume_eager`（必要时 `_make_agent_in_context` 的薄参数/上下文保留） | lock外恢复，原双检查/close/transfer顺序；不改外部DTO或其它resume路由 |
| `tui_gateway/server.py::_start_agent_build::_build`、`_attach_built_agent` | deferred准备与native attach提交；必要的identity/history_version校验及失败close；不改server注册/catalog、模型解析、认证、services业务或其它server功能 |
| 新 `tests/tui_gateway/test_cold_noting_resume.py` | 独立正式RPC→真实SQLite/Agent/child机制测试及屏障 |
| 本报告 / ignored `cold-resume-fix/**` | 机制与证据；根看板/计划仍由Main维护 |

**server.py必须追加精确授权**：当前仓库不存在现成session_agent模块，build/attach owner就在server上述函数，原分派候选 `session_agent*.py`不能代替真实接线点。不需要产品修改 `secretary/noting_hosts.py`、noting_runtime、noting_timers或noting_child；不修改agent core、prefix规则、前端、生命周期或共享契约。若Main愿将两处薄调用亲自接线，可由Main拥有server，但最终机制须与新helper/测试同一版本review。

## 5. 恢复失败与并发边界

- 原生root/tool/history恢复失败，不发布一个伪ready Parent给background consumers；沿既有eager5000或deferred agent_error/error+agent_ready完成，关闭未发布Agent、正确释放/保留dedicated DB handle。没有Idle event claim/admission/Snapshot；尚未处理的真实deadline保持原事实，后续合法native恢复仍由同handler处理。已领取事件/失败任务不因此复活。
- 并发resume沿原profile-aware stored target/tip double-check，loser的恢复不能覆盖winner或启动另一poller/timer。close/reap时若record identity已失效，丢弃并close prepared Agent，既有ready/error避免等待者悬挂。
- Warm live reuse不重新恢复/刷新已有root/tools/messages；Rewind/压缩后以native当前tip/active history为准，不能读ancestor display当Active。运行中Parent及已冻结child prefix不由此helper刷新。
- C16 local on/off只在统一event handler选择；global关闭/非eligible不执行helper。已有timer lock/DB unique admission继续是event与Anchor的权威；恢复不产生第二admission owner。
- Main真正启动/compaction与catchup交错按原native Turn + conversation_timer_lock/period竞争。验证必须包含真实Main抢先启动、late构造/重写、close/reap与两个resume；如果发现原native host running claim到Agent.run_conversation之间另有影响此次合法freeze的实际竞态，单独带正式反例回报，不暗中扩大为通用调度器修复。
- late MCP/原生工具pin、旧saved-root缺失或stale-runtime按原native恢复处理，记录必要恢复变化；不承诺从没有来源的DB字段捏造旧schema。当前全局改变在native恢复/Pre-message边界同步，旧child仍保持已冻prefix。

## 6. 准入后定向机制证据计划

使用canonical runner、仓库ignored隔离home/SessionDB、真实server.handle_request与AIAgent/Noting Child Loop，只控制外部SDK/provider返回、native模型元数据/MCP发现、clock/scheduler等待或时序屏障。禁止源码镜像断言。首先取得当前版本的正式cold失败反例（不是手工造parent对象假前缀），再验证同输入修复。

1. 真正Main正常结束形成原生命周期idle facts，关闭/移除旧runtime后跨due，分别eager/default cold/defer_history/omit model-history恢复；恢复本身Main provider调用0，单次event/admission、实际child、有效Snapshot与同ref/Anchor。到点off事件结束，之后on/再次cold不补。
2. root/tool pin与native恢复后的Active实值：UID、timestamps、api_content/reasoning、多轮tool结果、compaction summary/tip与存档display区分。对实际child第一/后续请求的完整冻结prefix做比较；新task suffix落child，Parent后续Main/compaction不能改变已冻结prefix。
3. 原生不同profile/cwd/同stored key隔离；global off与非eligible负对照：无提前root恢复、无新增timer/admission/Notebook写，旧resume DTO/历史/普通发送/close语义保留。local off仍恢复合法timer但由共同handler唯一决定。
4. controlled屏障：耗时Agent/root准备时另一个resume先胜、history_version变化/合法Rewind、close/reap；不持反序锁、不覆盖winner、不重复服务；真实Main先启动取消旧period。DB/native-root恢复失败明确build失败、无event消费或Snapshot；late结果不发布到已移除record。
5. 健康/ruff只任务文件与必要官方ratchet；不全套检查、不机械重跑旧T3a/T3c/Usage证据。真实DeepSeek cold复验归独占53446的原v16_gap_evidence，须Main集成commit后协调执行；本Agent不操作运行实例。

上述是预计证据，不是已经运行或通过的测试。源证据hash、调查源码hash及恢复链路摘要在ignored evidence目录。

## 7. 接口影响、未实施项与建议下一步

没有新增RPC/DTO、事件、表、持久retry/capability flag或Root/schema格式，原session.resume/newPrompt协议继续沿用。新增效果只是在globally-enabled eligible冷Parent第一次被后台使用前完成正式native Active恢复，使已经合法存在的catchup事件能按同一pipeline执行。

以上为原只读里程碑结论，Main 随后已准入实施；最终状态、源版本与剩余动作见 §8–9。


## 8. 准入后的最终机制及设计修订

### 8.1 唯一 build owner 与合法 Parent publication

- 实际新增 `session_agent_context.py` sibling，facade 使用 `method_ctx.rebind(..., globals())` 读取正式 server 装配后的真实函数与参数；没有新增 RPC、module registry 或独立服务。
- **替代 §3 原 eager preclaim 准备设计**：原生 eager 先构造真实 Agent，用已有 `is_main_conversation_agent` / `settings_for_db(agent._session_db)` 证明 eligible/global on。仅该新增分支调用现有 `ctx.record/claim`；winner 通过内部 `prepared_agent` 参数交原 `_start_agent_build` 唯一 `agent_build_lock/agent_build_started` owner。根恢复在 claim 后、build profile/session/cwd scope 内、history/sessions/resume 锁外执行。同步 eager 锁外等原 `agent_ready`，失败返回原 resume 5000；从不返回假 idle 成功。
- ctor loser 沿原 reuse；未采用 prepared 实例只 close 借用的 Agent，ctx reader 仍供当前 reuse/finally 使用。builder 真正接管后才撤销 `ctx.owns_db`；已有 builder 抢先则 prepared 实例不转移 DB。profile dedicated ref 成功由原 `_finish_agent_build/_transfer_db_to_agent` 转交；失败/abandoned 在 native finally 释放一次。shutdown/close 后 identity 失效，late Agent 关闭且不继续 wire/announce。共享 launch DB 从不转移或关闭。
- deferred/default/omit/defer-history 经同原 owner、同 native canonical history hydration。helper 在 constructor 后恢复 Main read surface、原 `_restore_or_build_system_prompt`（含原 tool pin）并同步 native prompt；不调用模型，不产生 Main Turn/UID/时间、不改 deadline。
- **替代 §3 无限 history_version 重试设想**：native root 恢复只读用于stage的 history；`stage_surface_switch_note` 只修改 Agent-side `_surface_switch_note`，不修改 host history。DB root/tool pin 可能写入，因此不重复重跑有副作用的恢复。原 attach 在 `history_lock → sessions_lock` 下确认同一 record，并安装**最新** host history 引用为 Parent `_session_messages`；rewind 空列表也保持同一引用。root 已完成恢复后才 publication/services/ready。没有新持久 flag 或 prefix cache。
- 持久恢复保留所有 born-durable marker/UID/API字段；flush scan 起点 0、scan snapshot None，由原持久标记扫描确定哪些尾行应写，避免把未落库尾行假标持久。close 的真实 DB row 比较确认恢复的旧 rows 不重复写。原恢复函数吞掉 DB read 错误并采用 native fallback 的政策保留；只在准备实际 raise 时走 native build failure。
- global off、非 eligible、空历史仍走原 eager/init 或原 build/attach；旧参数、错误及结果保留。为了不增加两个原超限文件的行数，将原 eager/build body 原样移 sibling 后加最小分支，server 3661→3581、methods_session 2320→2264。

### 8.2 正式 Main claim 与 cold catchup 竞争

新增正式反例位于 `cold-final-first.log`：root IO 被屏障暂停时真实 `prompt.submit` 成功，host running claim 和 durable user row 已成立；冷服务第一 poll 先于 `run_conversation` 启动，旧 deadline 被消费并 admission，freeze 报 Anchor 不在 Active。此失败不是旧 H04-A 的伪重试，亦不是假 Main hook。Main 亲读后准入仅 `session_notifications._maybe_fire_tui_noting_idle` 最小额外接缝。

最终新增 eligible/global-on 分支在**原 history owner**临界区读 running、原 `_compute_host_turn_id`、同 runtime/Agent identity；busy 即不交旧事件给 handler，idle 则同临界区调用原共同 handler完成 event/admission/freeze。判断与冻结提交同步，另一客户端不能在检查后夹入新的 native claim；没有另一个队列、准入 owner、持久标记或调度器。off/非 eligible 原调用不加锁、不改行为；local gate 仍全部归共同 handler。

锁核查与实际证据：history → conversation timer RLock；native child freeze/spawn 同步部分不回取 host history，后续 child 自己的 worker 不在该临界区执行。`compact_parent` 调原 request 的有界 admission receipt，使用 native persist/request/fence锁，status 回调只取 sessions lock，不回取 history；host poller 启动线程后原 `_start_session_services` 立即释放 sessions lock。曾用同步测试 poll 错持 sessions lock，造成原 status callback 阻塞/超时，保留 `lock-receipt.log`、`lock-stack.log`、`lock-wait-stacks.json`；改测试为真实异步 poll线程边界，不以改产品绕过失败。最终用真实 native lease/fence/commit 与受控 summary 返回验证该分支。

窗口覆盖 root IO 期间 submit、Agent 已 attach 但 ready 尚未 set 的 submit，两者旧 period admission=0；真实 Main 完成后产生的新合法 period 经持有的 Timer **原回调**执行一次并提交新 Anchor Snapshot。Timer/admission/freeze代码及原策略无修改。这不等于审查所有原生 warm/future timer 到 Loop start 的邻近时序；本阶段不扩展为通用调度器修复。

### 8.3 实际白名单与边界

| 文件 | 实际变更 |
|---|---|
| `tui_gateway/server.py` | `_start_agent_build` facade及prepared_agent薄参数；`_attach_built_agent` recovered分支；旧 attach body 原样 |
| `tui_gateway/methods_session.py` | `_resume_eager` facade；旧 body 移 sibling 保 late binding |
| 新 `tui_gateway/session_agent_context.py` | 上述恢复、原 owner 接管/关闭、最新 history publication、原 body |
| `tui_gateway/session_notifications.py` | Main追加准入的 `_maybe_fire_tui_noting_idle` 原 host busy观察 |
| 新 `tests/tui_gateway/test_cold_noting_resume.py` | 正式dispatch/真实Agent/SQLite/Loop/Child/compaction与时序屏障 |
| 本报告 / ignored evidence | 设计修订、失败和有效证据、manifest |

未触前端、pending、Usage三个生命周期文件、secretary timer/admission/freeze/core、registry/contracts、规格、根看板/plan。未stage/commit、未启动/重启服务、未访问53445/53446实际库或凭据、没有真实模型流量；socket connect/connect_ex 在测试中拒绝。

## 9. 七项阶段交回与证据复用

1. **对应条款**：§1/§2 Active身份、§4.5 C16单event、§4.8/4.10原 handler与Force覆盖、§5.1–5.5完整原生冻结prefix、§6接线/关闭及最终不变量。精确阅读校准见 §1。
2. **实际变更**：仅 §8.3 五源码/测试文件；原报告 preclaim恢复/version循环方案被 §8.1 明确替代。
3. **正式路径**：`server.handle_request(session.resume)` → 原 `_Resume` 原生history/claim → 原 build owner → native root/tools/read surface准备 → 原 attach publication → 原 services/poller → 原 timer handler/admission/freeze → 实际 Child Loop/Snapshot；eager真正等ready，profile在publication前完整绑定。
4. **验证结果**：见下表，完整失败不删除；通过数按不同用例及版本归属，不把多轮通过相加。当前最终源码/测试/report hash 与日志索引见 ignored `final-manifest.json`。最终工作区HEAD为188ccdb2566883b4605cd01f090146ac5b0ae8d1，任务起点仍5ccc619；期间Main的其他阶段提交未触本任务五文件，适用性由文件hash锁定。
5. **缺口**：开发机制不冒充真实模型或两个独立门禁；H04-A失败admission3永久保留、不重试遮蔽。真实cold复验由Main集成commit并统一restart后原T5 owner新建正常Main结束的合法period执行。涉及复杂 compaction summary/tip、压缩后分支、Rewind UID/API sidecar持久策略采用现有原生恢复/既有V1.6有效证据，本阶段未重复整套。
6. **接口影响**：无新RPC/DTO/事件/表；只有内部可选prepared_agent/recovered参数；旧普通用户路径保持原生，新增效果仅global-on eligible cold Parent正式准备与host已准入busy观察。
7. **建议后续**：Main集中源码review接收并阶段提交，提供待真实复验commit给T5；统一reload稳定版本批量补cold等剩余真实证据；按R2-C24停在Verification前，不提前宣称门禁或整轮完成。五文件已完成并释放，无待本Agent继续并写的共享接缝；请Mainreview接收后再commit/restart，当前没有运行实例加载本工作区代码。

### 9.1 已选回归包、结果与次数

所有命令用官方canonical runner、PM `.venv`（Darwin arm64 Python3.14.7）、仓库ignored basetemp，外部SDK/summary/metadata/MCP及Timer等待可控；真正RPC/native admission、SessionDB、Agent/root/pin、Child Loop、lease/fence/commit未替换。

| 证据 | 范围与结果/适用性 |
|---|---|
| `baseline3.log` | 基线5ccc619产品，真实Main自然结束→cold，单event/admission后Active空失败；1个有效正式失败反例。baseline-failure.log/baseline2.log是过早join launcher导致fixture失败，不能算产品反例 |
| `first-fix.log` | 原cold关键case1通过，仅早期实现，不代替最终版本 |
| `core2.log`/`core3.log` | 早期机制：修empty []引用真实缺陷；其它cwd/globalcfg/child FinishNotice同步测试边界失败保留；不作最终整包通过 |
| `selected-first.log` | 一次按影响选5文件：4个原恢复/DB ownership/live profile/failed retry文件21通过；新增包11通过4失败，整条命令不通过。这21项产品路径在后续没有相关语义修改，直接复用、不机械重跑 |
| `cold-final-first.log` | 12通过3失败，其中正式Main claim→catchup竞态有效；profile误要求registry全清零的取证缺陷保留 |
| `owner-final-first.log` | busy接缝后12通过4失败；Main旧event已不consume，新period因HeldTimer未送原回调而测试失败；profile检查仍错把原有generation引用当新增泄漏 |
| `boundary-second.log` | Main两窗口旧event保留+新period原callback/Snapshot2通过；profile2失败，仍保留 |
| `ref-trace.log` / `profile-final.log` | 引用来源追踪显示新增native acquire/release成对；保原warm baseline引用；修取证后profile采用/竞争builder2通过 |
| `lock-receipt.log` / `lock-stack.log` | 同步替换poll在_start_session_services持sessions锁等待receipt的测试边界失败，完整栈保留；不作为真实产品deadlock结论 |
| `real-poller-final.log` | 最终测试修复为真实异步context poll线程，重新选**全部新增cold17用例**验证新的正式调度边界：16通过、1失败（summary实际在native timeout worker运行，测试误认线程名）。整条命令失败，不写成17通过；这16个的fixture/断言与最终测试版本相同 |
| `lock-final.log` / `lock-publication-final.log` | compaction真实准入/commit成功；首次断言误用生成阶段summary私有flag，native加载使用不同标记，改查真实DB native publication与Parent同UID后该1项通过（2.2s）。最终产品源码不变；17个不同新增用例=上述16+此1，不重复相加其它版本 |
| `ruff-final.log` | official scripts/check --only ruff，1 check通过 |
| `owned-health-final.log` / `owned-health.json` | official Measurer/compare/apply_allows scoped五文件，0 blocking、1 advisory。提示HX012是原build裸thread体从server搬到sibling暴露；保原native build显式profile/session scope和原未启用thread行为，未新增allow、未放宽规则，不能写成0提示 |

运行履历全部留证：基线准备3次（有效反例1次），早期修复1次、核心小包3次（含syntax失败）、影响回归包1次、新cold包2次、竞争/profile定向3次、compaction锁分支4次（2次同步fixture超时、2次末端断言收口），异步poll修订后最终新增包1次。无大型检查；Pending109、Read53、Usage23、Submit既有分版本、原V1.6有效证据均未重跑。本阶段必要失败诊断复测与重复旧功能验收严格区分。
