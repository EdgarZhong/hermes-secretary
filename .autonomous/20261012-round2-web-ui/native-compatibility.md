# 第二轮 Native Compatibility Audit（研究准备）

> 2026-10-12；审计工作区 `/Users/edgar/code/hermes-secretary`。HEAD `6c3659bdf8032becc048a43650302e8c390921bd`，产品基线 `edd031f551`。本文是 Development 研究交回，不是独立 Verification，也不声称接口已实测或门禁通过。产品源码只读，无服务启动、真实模型请求、profile 操作、产品修改、测试新增或提交。
>
> 所有 **A 候选均未实现、未经 Main review、方法名未定案**。本文不授权额外产品行为。权威顺序：现行 02 含 V1.6 修订 →04 未覆盖增量→01；06 明确 Web 增量优先，保留旧客户端行为。

主会话协调更新：本轮已冻结 `37ad76f5dfac02d4774d5e0faea55911b5fb8de9`，计划快照 `9127c5d7f70eec2af2daf566079fd0251531f45e`；产品仍 `edd031f551`。06/01/02/04已一级只读。前端已开始已有原生路径、视觉限 `src/design/**`；本文的后端候选供Main集中审核后派遣，不以审计准备状态阻挡已启动的前端。文首HEAD是开始调查时的读取版本，收尾版本与源码漂移检查见本地 `audit-closeout.json`。

## 1. 结论和研究边界

现有 Dashboard REST + TUI Gateway 已覆盖会话、历史分页、附件、普通 Prompt/Stop/Rewind、模型与推理、Slash 和 Files 的主要接线。无需 BFF、新对话 API、客户端数据库或新的 Agent Loop。最重要的真实缺口是：

1. `_pending_steer` 是一个合并字符串，现有 ACK、`inflight.corrections/correction_offsets` 都不是可撤回 occurrence 清单；消费与 Gateway `running` 的终结没有共享原子边界。
2. `session.interrupt` 是硬 Stop，清普通 queued Prompt 并增加其 generation；没有“冻结尚未消费 Steer→停止→一次 follow-up 实际准入”操作，无法以两客户端 RPC 代替。
3. 每次原生压缩已有 `CompressionCommitFence`、attempt generation 与取消探针；缺的是安全的小型 RPC 和初始状态读取。应复用 fence，绝不能通过 Turn hard interrupt 伪造取消。
4. 人类 `/notebook` 的现有命令路径确实写两条 feedback 到 DB/live history；新增只读路径必须避开该 adapter，同时复用 renderer，保留旧路径。
5. `session.usage`/`message.complete.usage` 是累计快照；`_last_turn_usage` 又是最后一模型调用，二者都不是完整 Latest Turn。真实 cache counters 和 Turn 计数需窄投影，缺历史来源时返回 unavailable。
6. Secretary 没有消费者可直接调用的 Noting 状态/Memo/Idle due 只读接口，也没有足够的任务状态失效事件。可添加一份 owner-aware 只读投影和同 WS 的小事件，勿新增调度器。

附带重要原生事实：REST display projector 会隐藏纯 compaction handoff，但保留 raw `content`；Gateway projected history 不保留 `message_uid` 且不提供完整工具结果，不能替代 REST 历史。原生 Framework 使用 `display_kind=process_complete`，不能仅凭 kind 区分 Secretary 载体。初始/重连压缩状态与 occurrence 状态也不能从文本或 offsets 猜。

只读证据：[source-manifest.json](../../.hermes-dev/round2-evidence/native-audit/source-manifest.json)、[source-proofs.txt](../../.hermes-dev/round2-evidence/native-audit/source-proofs.txt)。50 个实际读取源文件 SHA256、21 组带行号关键原文。所有证据为源码不变量或确定性可调度反例，**未执行反例程序、网络/集成测试、跨平台测试或浏览器验收**。

已读：根 AGENTS/CLAUDE、第二轮 snapshot-index、06 全文；02 §1 L15–280、§2.6–2.7 L586–640、§3.1/3.5–3.6 L643–870、§4.1–4.5/C16 L1085–1206、§5.6 L1540–1741、§5.9 实际标题 L1780 起（补读 L1756–1820）、§6.11/6.12 L2340–2395。没有读 archived、私人 Pi 库或既有运行 DB。

## 2. Correction 真 owner、消费和 Finalizer

### 2.1 原生接线与锁

| 层/实际符号 | 真实所有权与行为 | 证据 |
|---|---|---|
| `agent/agent_init.py` `_RUNTIME_FACTORIES` | `_pending_steer=None`、`_pending_steer_lock=threading.Lock`；另有 `_pending_redirect_lock`，不是同一锁 | L494–501 |
| `agent/interrupt_control.py::InterruptControlMixin.steer` | 仅校验非空，锁住 Agent steer 槽，`existing + "\n" + cleaned`；不校验 active Turn/终结 epoch | L269–281 |
| 同文件 `_drain_pending_steer` | 同 steer 锁下读字符串、清为 None；无 occurrence、消费 receipt、持久行身份 | L367 起 |
| `tui_gateway/methods_session_interrupt.py::_correction_method/_apply_correction` | 外层查 session；`running` 在 Agent 锁外判断；调用 `agent.steer` 后才在 `history_lock` 记录 inflight correction | L73–126 |
| 同文件压缩分支 | `_session_compression_in_flight` 时 `_enqueue_prompt`，结果仍 `{status:"queued",text}`；这是普通后续 Prompt，不是 Agent steer 槽 | L109–118 |
| `tui_gateway/session_history.py::_record_inflight_correction` | 追加 text 与已流 assistant 字符偏移；从不在消费时删除；仅恢复 UI 分段用途 | L413–424 |
| `agent/turn_iteration_prep.py::prepare_iteration` | pre-API 先 `_drain_pending_steer`；`_inject_steer_after_newest_tool_result` 负责真实 user-row 插入；无合适 slot 会 requeue | L180–188；同文件 L274–302 |
| `agent/agent_runtime_helpers.py::apply_pending_steer_to_tool_results` | tool batch 后 drain；有 tool tail 才追加 `steer_user_row`，下一正常 flush 持久；无 tool 重新放回槽 | L3758–3798 |
| `agent/prompt_builder.py::steer_user_row` | 原生 user role、`display_kind="steer"` 和模型侧 out-of-band marker；只是一行合并内容 | L592–601 |
| `agent/turn_finalizer.py::finalize_turn` | 最后 drain→`result.pending_steer`→`clear_interrupt`；真实返回到宿主前即清槽 | L740–752 |
| `tui_gateway/prompt_turn.py::_run_post_turn_followups` | Gateway 已释放 `running` 后，把 leftover 放普通 queue，再 `_drain_queued_prompt`；其他 queued 内容按既有 priority 排队 | L438–459 |
| `tui_gateway/session_auto_continue.py::_drain_queued_prompt` | `_session_turn_admission`（retirement + history RLock）claim，generation 防取消；进一步原生 `run` 生命周期 | L455–491 |

“当前 queue owner”准确答案：**Agent steer 槽**负责正在执行的 correction，**Gateway session 普通 Prompt queue**负责非 steerable/compressing/后续 Turn；inflight 只是 UI resume 快照。不能在 Web 侧或 RPC handler 再建立独立 pending correction 队列来绕过 Agent。

### 2.2 可复核反例/不变量（A admission 依据）

- **S01 occurrence 不可恢复**：依次 `steer("a")`、`steer("b")` 后槽值是 `a\nb`；一次 `steer("a\nb")` 槽值也完全相同。同文重复更无法按内容区分。仅有字符串状态不可能决定“撤回第二个 occurrence”；offsets 记录不随 drain 更新，不能修补此信息损失。
- **S02 ACK 不等于 pending**：Agent tool/pre-API drain 后已插入 user row，Gateway `inflight.corrections` 仍保留全部原 corrections。快照里出现 correction 不能证明仍可撤回。反过来 compressing 分支返回 queued，却没有进入 Agent 槽，客户端若当 Pending Steer 会错误理解插入时点。
- **S03 late acceptance/Finalizer 窗口**：finalizer drain 空槽→RPC 外层看到 `running=True`→Agent `steer` 返回 True→finalizer 返回→Gateway 完成清 inflight、释放 running→result 没有 pending_steer。已 ACK 的 correction 留在 Agent 槽却没有本次 follow-up；下一不相关 Turn 的 drain 可能接收到它。这是两个真实锁域的可调度交错，不是宣称已实际跑出的一次故障。
- **S04 requeue 顺序风险**：`_requeue_pending_steer` 把已在槽中的新字符串放前、旧已 drain 字符串放后。若 drain→无 slot→requeue 之间又有 enqueue，得到 newer→older。新 occurrence 实现必须按 accepted order 恢复原批次，不能沿用文本拼接当排序权威。
- **S05 ACK/记录竞态**：Agent `steer` 已成功但 `history_lock` 未获取时可已被 native drain；因此 RPC 记录后的所谓 pending 不能依据“刚刚 ACK”推断仍 pending，必须原子/明确返回当前状态或 ID transition。

### 2.3 最小候选（未实施）

保留唯一 `_pending_steer` owner，把其内部数据表达改为可保存 accepted occurrence/order 的**同一 buffer**，legacy `steer(text)` 仍返回原 bool、旧 RPC 原结果/错误均不变。新调用在此 owner 分配 opaque ID，不能另有 RPC 层权威列表再与字符串同步。以该 buffer 锁结合真实 Turn epoch/closing 状态实现 enqueue/withdraw/drain，epoch 由原生 Turn 起止驱动。

必须覆盖三处 drain、redirect 降级为 steer、失败 requeue、hard-cancel 清槽、finalizer leftover；临时 drain 批次不能在合法插入前无故标 consumed，插入成功才转 consumed。若 batch 无合法 slot，恢复同一 ID/order 为 pending。consume 的 row UID/物理 row association 在正常 flush receipt 上补齐；允许先事件给 exact ID set 后 REST refetch，但不得声称还没落盘的一行已持久。需要显式让终结窗口中 enqueue 与 finalizer handoff 只有一个 winner。

旧客户端仍走相同拼接文本语义；新 occurrence 日志只需 live bounded terminal receipts，不新建 durable pending 表。兼容性的难点是旧调用可以与新调用混合：它们必须共用队列，legacy 无新 ACK 字段；新快照不得冒充旧客户端尚未产生的精确 operation receipt。Main 决定内部 representation、锁顺序和 terminal receipt 保留上限后方可实施。

## 3. Atomic Interrupt→next Prompt

### 3.1 当前保证不足

`tui_gateway/methods_session_interrupt.py::session.interrupt`→`session_lifecycle._interrupt_session_turn`：history lock 下设置 `_turn_cancel_requested=True`，清 `queued_prompt/queued_prompts`、增加 `_queued_prompt_generation`；然后 hard interrupt Agent、退 crash marker。返回 `{status:"interrupted"}` **没有等待当前 Turn 彻底退场，也没有 follow-up 准入**。manual compression active 时只保留压缩 busy，Stop 不取消它。Agent hard interrupt 设置 Turn/工具/子 Agent 的中断，还会取消 native compaction request；它不是 compaction-only cancellation。

`clear_interrupt(hard_cancel=True)` 可清未消费 steer；真实 `agent/turn_recovery.py::abort_turn_on_interrupt` L1370–1388 正在调用该分支并直接返回 interrupted result，不提供pending receipt。`finalize_turn` 普通 `clear_interrupt()` 又保留 accepted steer，当前 Stop 与不同退出路径不可当“剩余 pending 自动一定跟随”的协议。`_run_post_turn_followups` 在 release running 之后另行 enqueue/drain；`prompt.submit` 忙碌会 steer/redirect/queue，甚至另一个 client 可先 claim 下一 Turn。

**I01 两 RPC 反例时序**：客户端读 offsets/pending 文本→原生 drain 消费其中一个→客户端 Stop→客户端把旧文本 join 发 prompt.submit：已消费 occurrence 重复。**I02**：finalizer 已把 leftover 入 queue→Stop 清 queue/generation→客户端下一 submit 超时/另一个 client 先准入：无法判定自己的 follow-up 是否真实接受，更不能安全补发。**I03**：压缩旋转 current stored tip，客户端旧 Session/文本没有参与一次 native owner claim，无法证明一次性/正确 tip。

### 3.2 最小候选（未实施）

新增专门 RPC，复用真实 session admission/history lock + Agent buffer owner 锁，冻结仍 pending exact IDs 为 handoff-reserved，原子阻止其继续 native consume/withdraw/自然 finalizer 重投。之后调用真实 stop；**不持 history/buffer 锁等待 provider/tool thread**；原生 finalizer/settlement 完成后由既有 `_run_post_turn_followups/_drain_queued_prompt` 或等价原生 dispatch 接缝一次性接管 reserved batch，以当前 stored tip 正常生成一个 user Prompt。不能调用旧 Stop 把 reserved batch 清掉，也不能误带现有 queued Prompt、attached_images、unsent Composer。

`attached_images` 默认由 `_admit_prompt_turn` 消费（L143–145），pending-only handoff 必须显式传 `image_paths=[]`，保留其他 client 已 stage 的图像。新 reserve 不改变旧 queued envelopes 的所有权；新 operation 的优先级/一次 claim 只用于这一停止交接，不能替代通用 admission gate。新方法应能在 old Turn 未退场时返回机器状态 `handoff_pending`，随后通过 operation query/event 返回**真实** followup_accepted；不可把 hard-interrupt ACK 当完成。若 RPC选择等待实际准入，则超时必须保留 queryable operation ID，不能 false success。

新 operation receipt 必须关联 Turn epoch/runtime owner、exact pending IDs、新 driving user row/Turn receipt、current stored tip；相同 retry operation ID只能观测同一结果。错误前恢复 pending或明确 terminal rejection，绝不把已接受文本丢到不可查状态。core finalizer 与 Gateway settlement 的 atomic boundary 是实施重点，不能仅增加 handler。

compute-host 分支当前 steer 没有可靠同 owner 通道，不可拿 parent Agent proxy 状态代替子进程。实施应复用 supervisor 控制/receipt 增量，或明确 unsupported；目标 localhost 的实际默认 isolation 配置仍需核对。本文未操作配置。

## 4. 只取消 Compaction：可复用的 fence 与 publication

`agent/compression_facade.py::CompressionMixin._compress_context` L274–334 为**每次**压缩注册 `CompressionCommitFence`，`_compression_commit_fence_lock`/stack保护 active 注册，成功/失败 only-own unregister。`agent/conversation_compression.py::CompressionCommitFence` L451–585：

- `begin_commit` 获取 fence lock并一直持有至 `finish_commit`；取消与 irreversible DB/session mutation有唯一 winner。
- `try_cancel_before_commit()` 非阻塞，True=已阻止未来 commit；None=commit 正持锁；False=已开始过 commit。`cancel_before_commit` 可能阻塞，不应在短 RPC里盲等。
- `is_cancelled` 在 summary dispatch、compressor取消探针和 commit gate读取；`_run_summary_dispatch` L2990–3052 将 fence probe传给 `aux_interrupt_protection`，late summary不能重新发布。
- compressor `_compression_attempt_generation`、cancel-check owner与注册 stack已经抵御旧 worker清理新 attempt；不要新增第二 generation/fence。
- `context_compaction_request.NativeCompactionRequest` 有 `publication_id`、owner/db/ref/current()`、admitted/completed、fence；其 `cancel()` 会先 revoke，再可能等 commit，不能无条件暴露为“取消成功”。Noting 已 valid commit/Snapshot不随父取消回滚，遵守02 §5.9。

`tui_gateway/session_compression.py::_manual_compress_turn` L227–245 busy覆盖完整过程，结束自动 drain ordinary queue；`_compress_session_history` L247–294用 history_version做 publish校验并原生 adoption。`session.compress` (`methods_session.py` L2093)在 `_LONG_HANDLERS` 中异步 pool执行（`server.py` L176–193），**不会因同 WS dispatch顺序阻止后续 cancel RPC**；无需另建 socket或 async compression job API。

**C01 缺口证明**：现有注册 API只有 session.compress/interrupt，没有 fence-only取消方法；旧 Stop在manual active时明确不 abort compression，普通 hard interrupt又会停 enclosing Turn/工具/native request。两者均不能满足06 §2.5。

候选新 RPC在注册锁下捕获实际 active fence/attempt handle，释放注册锁后仅对同 fence `try_cancel_before_commit`。True时回 `cancellation_requested`（发布已阻止，但 worker可仍 unwind）；None/False回 too_late，不 revoke一个已经提交的结果；无 active回 no_active。不要设置 `_interrupt_requested`、hard event、`_turn_cancel_requested`，不要清 Pending/ordinary queue。不在网络/summary期间持 history lock。成功后等原生 terminal status/usage恢复ring，不能按钮点击立即假 idle。

还需要 narrow **initial read**：原生 live snapshot的 running不区分manual压缩与Main；status.update replay可截断/epoch重启。新read应返回active operation/phase/cancelable从真实 fence/registration，不依据英文status文案。自动/手动/Noting请求、in-place/rotation、cancel/commit/fallback/timeout、late attempt与compute-host均须相关契约证据。

## 5. 实际 native DTO / 前端接线表

以下为**当前现有方法**，以对应 handler为运行权威，`tui_gateway/contracts/*`是审计读到的wire声明；Pydantic open optional并不证明producer每次真给值。所有 session-scoped RPC的 `session_id`默认是runtime；REST locator与resume输入是stored。`profile`可选但应以selected owner显式带入；不要把ambient选择在await后再次读。旧 `_sess_nowait`只按runtime dict取对象，不是新增profile ACL；新delta需核runtime/profile一致，不能改旧方法协议。

| API/输入 | 实际结果及接线要点 | 权威来源 |
|---|---|---|
| `session.create {profile?,cols?,source?,cwd?,cwd_explicit?,model?,provider?,reasoning_effort?,follow_profile_config?,idempotency_key?,…}` | `{session_id,stored_session_id,message_count,messages,info}`；deferred build；无seed时首次Prompt才DB落会话行。New Chat仅首Send调用且同retry key | `contracts/sessions.py` L126–176；`methods_session.py::session.create` L443 |
| `session.resume {session_id:stored,profile?,defer_history?,omit_messages?,lazy?,eager_build?,inline_images?}` | `LiveSessionSnapshot`含runtime session_id、stored_session_id/resumed/session_key、info/messages/message_count、running/status、inflight、queued、pending_approval、open_requests、hydrating/messages_omitted等条件字段；跟compression tip；同profile reuse live | `contracts/sessions.py` L70–98/L196–226；handler L1012–1044 |
| `session.activate {session_id:runtime,profile?,omit_messages?}` | 同snapshot；rebinding不关闭旧Session，stale 4001→按stored resume | 同文件；handler L1113起 |
| `session.active_list {profile?,current_session_id?}` | `{sessions:[{id:runtime,session_key,status,model,title,started_at,last_active,message_count,…}]}`；仅本进程；没有conversation_ref、Pending inventory | 同contracts L275–293 |
| `prompt.submit {session_id,text,profile?,…}` | `{status:streaming|queued|steered|redirected,user_row_id?,survivor_*?,turn_isolation?}`；有voice stop特例；无操作ID幂等，丢ACK后不可自动补发。busy会改路由，Web text-only active用steer专用路径 | `contracts/prompt_voice.py` L26–79；handler L693–830 |
| `prompt.submit` rewind | `confirm_truncate:true` + `truncate_before_row_id`优先，或native `message_id`/visible user ordinal；first-user empty另需`confirm_empty_truncate`；`rebind_survivor_row_ids`可返回映射；busy错误4009必须native interrupt+wait后完整cut重试 | `methods_prompt.py::_lock_in_submit_turn/_truncate_history_for_submit`；Desktop `rewind.ts::truncateSubmitParams/runRewindSubmit` |
| `session.steer {session_id,text,profile?}` | `{status:queued|rejected,text}`；blank 4002、不支持4010、session不存在4001；compressing queued不是Pending receipt | `methods_session_interrupt.py` L92–133 |
| `session.interrupt {session_id,profile?,expected_hosted_task_id?}` | `{status:interrupted|not_interrupted,interrupted?,turn_isolation?}`；不等Turn完成、无next Prompt保证 | 同文件 L33–70 |
| `session.compress {session_id,focus_topic?,profile?}` | compressed/aborted/pending、before/after、summary、messages、usage/info；lock-held `{compressed:false,lock_held:true,message}`；busy4009、failure5005；不能当前直接cancel | `methods_session.py` L2012–2130 |
| `session.events.since {session_id,last_seen?,profile?}` | `{events:[event.params],latest_seq,truncated,count,epoch,open_requests}`；512 events/4MiB每Session、64MiB进程/64Sessions。epoch改变/截断需REST+live重构 | `contracts/sessions.py` L699起；`event_replay.py` L24–41 |
| WS `event` | `{jsonrpc:"2.0",method:"event",params:{type,session_id,payload?,seq?}}`；无统一event timestamp/turn_id！只有某些payload携带时间。不能给临时节点杜撰持久时间 | `server.py::_event_frame` L696；event_replay |
| stream | message.start、message.delta `{text,rendered?}`、reasoning/thinking.delta、reasoning.available、message.interim `{text,already_streamed}`；message.complete `{text,status,usage?,persisted_turn?,reasoning?,error_surface?,partial?,response_*?,…}` | `contracts/events.py` L113–213；Desktop gateway-event/message-stream.ts |
| tool | tool.generating `{name}`只有状态；tool.start `{tool_id,name,args?,context?,args_text?,labels?}`；tool.complete `{tool_id,name,args?,result,result_text?,summary?,duration_s?,…}`；**没有incremental arguments delta** | `agent_callbacks.py` L164；`tool_progress.py` L276–302；`contracts/events.py` L263–308 |
| `file.attach {session_id,data_url?,path?,name?,profile?}` | `{attached,name,path,ref_path,ref_text,uploaded}`；ordinary PDF同路；把authoritative ref_text追加真实Prompt，不猜路径 | 当前`methods_prompt.py` L949–966；`contracts/prompt_voice.py` L165–184 |
| `file.upload_chunk {session_id,upload_id,offset,total_bytes,data_url,name?,profile?}`（V-R2-01整改新增） | 原六个附件字段加`upload_id/received_bytes/size_bytes?`；未完成`attached:false`且path/ref为空；末片才发布ref。单片≤4MiB、声明总量≤500000000；offset+payload精确重放幂等 | `methods_prompt.py`的同名注册入口→`prompt_attachments.py::_file_attachment_chunk`；契约`FileUploadChunkParams/Result` |
| `file.upload_abort {session_id,upload_id,profile?}`（V-R2-01整改新增） | 原六字段加`upload_id/received_bytes`；`attached:false`、path/ref为空；同runtime锁下仅清未完成临时文件，不撤销完整文件，不改变Turn/Pending、不启动冷Agent | `methods_prompt.py`→`_file_attachment_abort`；`FileUploadAbortParams/Result` |
| `file.attachment_info {session_id,path,profile?}`（V-R2-01整改新增） | 原六字段加真实`size_bytes`；`attached:false/uploaded:false`；只读session workspace与profile attachments/images根，不stage/copy/warm Agent；symlink/remote cwd边界沿现有helper | `methods_prompt.py`→`_file_attachment_metadata`；`FileAttachmentInfoParams/Result` |
| `image.attach_bytes {session_id,content_base64?|data?,filename?,ext?,profile?}` | `{attached,path,count,bytes?,name?,width?,height?,token_estimate?}`；魔术/后缀校验，同runtime `attached_images`留待submit | 同contracts L110–131；handler L887–917 |
| `image.detach {session_id,path,profile?}` | `{detached,count}`；只撤queue引用，不删文件；不能把Cancel Send当Turn Stop | handler L999–1012 |
| `session.usage {session_id,profile?}` | Usage累计`input/output/prompt/completion/total/calls`、context_*、cache_hit_pct?、avg_*?；**producer没填cache_read/cache_write，calls不是Turns**；read可能访问provider account limits，不宜每秒轮询 | `server.py::_get_usage` L2187–2240；`methods_session.py` L1405–1433 |
| `session.context_breakdown` | `{categories,context_max,context_percent,context_used,estimated_total,context_estimated,context_source,model,context_files}`；UI只需真实ring/数字不照搬category bar；可能build prompt，只在正确profile/session scope | `methods_session.py` L1436–1468 |
| `config.get {key,session_id?,profile?,cwd?}` | getter union：`key=full→{config}`，reasoning→value/display，provider→model/provider/providers；通过full读取noting全局；无新重复setting | `contracts/config_free_tier_control.py` L25–63；`methods_config.py` |
| `model.options {session_id?,profile?,explicit_only?,include_unconfigured?,refresh?}` | `{providers:[{slug,name,models,capabilities?,authenticated?,pricing?,…}],model,provider}`；capabilities含reasoning/can_disable_reasoning，**没有全部可用effort列表保证** | 同contracts L438–562；`methods_complete.py` |
| `config.set {key,value,session_id?,profile?,scope?,confirm_expensive_model?}` | `{key,value,warning?,confirm_required?,confirm_message?,scope?,deferred?,info?}`；reasoning有session/global/once，model原生setter按其existing行为；当前session.info含actual reasoning_effort及wire clamp | 同contracts L70–108；`methods_config_set.py`/model_switch |
| `complete.slash {text?,session_id?,profile?}` | `{items,replace_from?}`；items为completion，不是可执行证明 | `contracts/profiles_vault_complete_foreign_subagents.py` L50–67 |
| `commands.catalog {profile?}` | `{pairs,sub,canon,commands,categories,skills,skill_count,warning}`；commands meta有desktop/argument_mode；动态skills/quick/plugin | `contracts/tools_commands.py` L200–229 |
| `command.dispatch {name,arg?,session_id?,profile?}` | directive `{type:exec|alias|plugin|send|skill|prefill,output?|target?|message?|display?|notice?|…}`；send/skill必须按directive正常submit，exec按实际结果展示；不是所有terminal slash都有dispatch | 同contracts L247–280；`methods_tools.py`；shared/slash.ts |

REST DTO：

| 路径/输入 | 实际返回和限制 | 接线 |
|---|---|---|
| `/api/sessions?profile=&limit=&offset=&order=recent&archived=exclude&min_messages=0…` | `{sessions,total,limit,offset,storage}`；limit0–100，来源/cwd filters可选，compressed lineage projection、pin可额外backfill。GET有原生auto-archive维护副作用，非Notebook/Turn变更 | sessions.py L174–272；不要发cwd_prefix隐去历史不同cwd |
| `/api/sessions/{stored}?profile=` | 原始session字段加profile/is_default_profile、scheduler_owned条件字段；含真实cwd/累计token等 | sessions.py L563–585；不要full列表渲染敏感prompt/model config |
| `/api/sessions/{stored}/messages?profile=&limit=120&offset=0&order=latest&include_compacted=true&inline_images=true` | `{session_id:resolved_tip,profile,messages,pagination:{limit,offset,order,returned}}`；每页≤500；latest offset从最新向过去，返回页内部仍时间顺序；无total/has_more，完整页需继续查询直至短/空页 | sessions.py L724–767；Desktop api/sessions.ts:getLatest/OlderSessionMessages |
| REST message row | 实际SessionDB行含`id,session_id,role,content,timestamp,message_uid,tool_calls/tool_call_id,display_kind/display_metadata,…`；projector加display_content、hidden等但raw content保留。REST物理`id`可作rewind row target，绝非semantic Message UID | sessions projector L655–719；Gateway不同：`text,row_id`，不把二者混用 |
| `/api/fs/default-cwd?profile=` | `{cwd,branch}`；SSH使用profile backend；local `_fs_default_cwd`是serving config/PWD fallback | files.py L978–993；新session可以读取默认cwd后create `cwd/cwd_explicit:false`，不改历史cwd |
| `/api/fs/list?path=&profile=` | `{entries:[{name,path,isDirectory}],error?}`；ENOENT/ENOTDIR/EACCES可以是200+error，不能按200判成功 | files.py L758–785 |
| `/api/fs/read-text?path=&profile=` | `{binary,byteSize,language,mimeType,path,text,truncated}`；源64MiB、preview512KiB；binary不能当文本正常显示 | files.py L789–831 |
| `/api/fs/read-data-url?path=&profile=&session_id?` | `{dataUrl}`；真实MIME与cap；session_id这里是stored、校验ownership再解析相对path | files.py L901–927 |
| `/api/fs/download?path=&profile=&session_id?` | 流式响应、MIME与Content-Disposition；**legacy query-token allowlist不含fs/download**，使用authenticated fetch→Blob；不能直接加tokenURL假定可用 | files.py L930–958；web_server.py L473 |
| `/api/files/*`、`/api/media?path=` | managed policy与media roots独立；包含write/upload/mkdir/delete能力，V1 Files只调用read。`/api/files/download`可query-token；历史file chip不重建link | files.py L307–352/L598起；不能泛化成fs proxy |

附件限制原始审计实情：image25MiB、特殊pdf-render50MiB/25页；ordinary file.attach的实际stage函数**未见raw size cap**，WS uvicorn配置384MiB是frame ceiling，注释中的“256MiB raw attach cap”不能代替file.attach校验。R2-C30之后明确草稿全部附件合计500000000 bytes；已有实际500MB上传/模型读取证据见plan附件段，底层复用不再传大包。V-R2-01整改将分片与stat从旧`file.attach`移至上表新名，恢复旧方法精确参数/六字段结果、4015/5028及额外键4000；前端新名接线与代表完整链路仍待后续授权实施/补证。重名文件用原生独占allocation；原image/PDF-render限制不变，不声明500MB图片理解。

## 6. REST/WS 安全与前端实际复用

`web_server.py` L457–470 loopback HTTP接受`X-Hermes-Session-Token`或Bearer；gated模式依verified cookie/bearer session。loopback secret注入官方SPA，独立frontend origin**不会凭空获得token**，没有新公共token bootstrap接口。前端开发部署需Main确定如何复用官方authenticated入口或受控本地token交付；token不得进repo、log、localStorage business cache。仅同origin reverse proxy静态托管属于基础设施而非BFF，但本轮没有云端部署授权。

CORS在outermost，允许`http(s)://localhost|127.0.0.1`任意端口、methods/headers任意；**未开allow_credentials**，gated cookie不能据此承诺跨origin可用。WS校验Host/Origin hostname和bound/trusted hosts，不比较port；同host不同port本地可候选复用。`localhost`与`127.0.0.1`按现行accepted host规则核定，生产不同host不能自行放宽。gated WS可用30s单次ticket、`hermes-gateway-v1`+ticket subprotocol；legacy `?token`有效；不能使用server-only internal credential。`chat_ws.gateway_ws`调用同native `handle_ws`/dispatch，非PTY依赖。

JSON-RPC client需要处理请求/结果/事件/服务端请求（approval/clarify等）及heartbeat。Desktop `apps/shared`的`JsonRpcGatewayClient`是可复用参考；Desktop `api/client.ts`的大量`window.hermesDesktop.api`、Electron multiplex/connection registry不可直接搬进浏览器。**建议只移植/适配纯wire parser和少量纯reducer**，以直接fetch/WebSocket替换平台bridge。

文件授权细节：`hermes_cli/web_server_files.py::_fs_path` L35–74校验非空/NUL与解析路径，`_hosted_fs_read_guard` L209–220只在既有managed locked-root部署检查resolved path根界及敏感路径；未锁部署是现行auth权限内的host读，**不是default cwd天然形成server sandbox**。V1默认root/breadcrumb是F导航约束，不能宣称客户端路径限制等于权限控制，也不应本轮私自改原API的读权限。`fs_regular_file`/sensitive filename、locked-root symlink escape、SSH backend规则需后续真实security反例。data-url cap现为16MiB（web_server.py L892），text cap与WS cap不同。

| 参考模块 | 可复用行为 | 不照搬的边界 |
|---|---|---|
| `api/sessions.ts`、`store/transcript-tail.ts` | latest页、echo-order guard、older页chronology/offset、resolved tip | broad remote-owner backfill、持久tail cache、多backend探测不是V1需求 |
| `use-session-actions/index.ts`、`store/session-states.ts` | memory stored/runtime map、resume/activate/reclaim、single-flight恢复、REST预取+inflight | broadDesktop持久状态、new-chat mount建立runtime不符合06 |
| `use-prompt-actions/rewind.ts` | native durable target、busy interrupt等待、survivor row rebind、失败恢复 | 双确认/刷新取消armed状态为Web自己的F；不能提交synthetic renderer ID |
| `gateway-event/message-stream.ts`、`tools.ts`、`session-info.ts`、`lifecycle.ts` | start/interim/complete sealing、response_reused/transformed、tool_id、不跨session、reclaim | pet/preview/notifications/app settings副作用不迁入；pending tail独立投影 |
| `lib/chat-messages/hydration.ts` | assistant sidecars、tool pairing、machine notice投影 | 现行隐藏pure handoff、process_complete统归system，不满足06 distinct载体与compaction显示；保raw再按真实wrapper分型 |
| `store/compaction.ts`、gateway status reducer | per-session压缩flag、只真实resume/terminal清除 | status文本不是active operation generation、刷新需新authority read |
| `apps/shared/src/slash.ts` | parseCommand/parseCommandDispatch和multiline argument正确性 | shared catalog不是Browser完整执行矩阵；各terminal动作需有证据过滤 |

工具构造期目前仅name事件，完整参数到tool.start可显示。06要求“when native events expose”，据此当前**N+F，不自动 A tool-argument-delta**；若Main认为某种真实provider已有参数流应展现，再审具体底层streamer，不能凭按钮加全部provider新协议。

## 7. 逐项 N/F/A/D ledger

Owner统一：**Main/Integration负责technical closure；Development按白名单实施；visual角色仅样式**。以下状态均“源码研究已完成、真实接线待实施验证”，A项额外为“未实施候选待Main review”。N不等于已通过浏览器兼容。

| ID / V1能力 | 分类 | Native source /精确约束 | 证据/待闭环 |
|---|---|---|---|
| L01 REST auth/origin | N+F | web_server.py/token middleware/CORS；06 §0.3/0.5 | native localhost具备基础；独立SPA token获取/gated cookies实际未证，部署不能默认可用 |
| L02 WS auth/wire | N+F | web_server_chat.py::_ws_*；chat_ws→ws→dispatch；§3.1 | native多种credential；不能私自放宽origin/用internal，连接验收待 |
| L03 New Chat/first send | N+F | session.create idempotency + prompt.submit；§1.3 | 无导航时create；仅首Send；Prompt本身未知ACK不可补发 |
| L04 stored/runtime/profile mapping | N+F | resume/activate、session_home、Desktop memory map；§0.1/3.2 | 4001恢复、compression tip；全新delta显式owner核验，UI无registry |
| L05 session list/lineage/cwd | N+F | sessions GET list `cwd_prefix`可选、order recent、source filters；§1.3/1.16 | 不传default cwd过滤历史；compression children连续、branch分离 |
| L06 history/replay/pagination | N+F | REST messages/max500/include_ancestors/include_compacted + events.since；§1.4/3.3 | REST row identity；seq/epoch截断需重新fetch，不凭流补持久truth |
| L07 stream/reasoning/tool结果 | N+F | message/reasoning/tool.* + Desktop reducers；§1.4/1.5 | native tool.generating只有name；完整args在start；collapsed工具/active expanded thinking为F |
| L08 incremental tool args | N+F，条件A未准入 | 当前无id+args delta；§2.8 | 当实际可用才呈现；没有source证明必须改provider，不扩大基础要求 |
| L09 real message kinds/time | N+F | REST raw wrapper +display metadata；message_metadata.py；§1.4/02 §5.6 | process_complete不是Secretary kind；epoch只格式化于UI、不改源；不能假timestamp |
| L10 live Framework即时显示 | N+F | agent_callbacks::_agent_status_update kind framework +REST refetch；§1.4 | 已commit验证过的event可作invalidation，不直接复制text成无UID持久节点。收到后REST读取真实row。若延迟/页窗无法稳映射再提narrow A |
| L11 compaction authentic历史 | N+F优先，条件A | REST保存raw；native compaction classifier/split_user_originated_turn；§1.14 | Desktop隐藏纯handoff不能照搬。F识别真实carrier/full raw/composite仅一identity；无文本不造marker。如raw无法无歧义辨认，A只能新增read投影不改旧display字段 |
| L12 compression status/cancel | A | compression_facade注册/fence；§2.5 | 无active状态read/cancel RPC；复用现有fence；C01源码证明 |
| L13 file/image attachment | N+F；大传输/尺寸为最小A | file.attach/image.attach_bytes/image.detach；新增file.upload_chunk/file.upload_abort/file.attachment_info；§1.7/V-R2-01 | 原生同runtime/附件owner与锁、旧合同精确保留；新增依据为500MB整包base64超V8字符串/WS帧上限、旧附件ACK无size事实，见plan附件反例；新名完整接线待补 |
| L14 Cancel Send | F（N detach） | abort客户端剩余transfer/prompt；§1.10 | in-flight RPC不能假撤销；staged图像用detach清queue；留residual bytes允许；another-client stage消费竞态必须真实测试 |
| L15 Steer occurrence/withdraw/recovery | A | Agent唯一_pending_steer锁；§2.2–2.3 | S01–05；旧session.steer不可改shape、compression reject单独报告 |
| L16 Stop | N+F | session.interrupt native hard stop；§1.8/1.10 | 不发Composer；ACK后等terminal/status，不假idle |
| L17 Interrupt pending-only | A | 原生buffer→finalizer→Gateway followups；§2.4 | I01–03；reserve exact剩余，一次native admission，附图显式空 |
| L18 Rewind/Edit | N+F | prompt.submit truncation +Desktop rewind；§1.11 | 两确认、临时hide/restore、reload退armed，durable target；文件side-effect不回滚 |
| L19 model/reasoning | N+F | model.options/config.get/set/session.info；§1.6/1.12 | current/wire effort真实；未应用pick为draft，不硬编码全model可用efforts |
| L20 Session Total/context | N+条件A | usage/context +REST session token字段；§1.13 | totals/calls来源真实，但wire未给cache_read，Turn count缺精确契约；A新read不改旧usage |
| L21 Latest completed Turn | A | turn_usage最后call、prompt_turn cumulative completion；§1.13/2.8 | 两次provider call不等最后call、累计不等本Turn；最小runtime accumulator/read，cold无事实unknown，不杜撰差分 |
| L22 slash动态目录/dispatch | N+F | catalog/complete/dispatch/shared parser；§1.12 | 按动作N/F路由，不把terminal exec建议当可执行；noting on/off旧native保留 |
| L23 人类Notebook瞬时 | A | _cmd_secretary持久化冲突；§2.7 | 新只读路径复用renderer，不调用persist_secretary_feedback/history.extend，不新增Turn/identity |
| L24 global Orb visibility | N+F | config.get full→config.noting.enabled；§1.15 | true只Conversation，不用local gate隐去；config无法读unknown |
| L25 Noting task/Idle/memo read | A | active_noting_task registry、noting_idle_state、notebook_local_enabled、noting_memo_entries；§2.6 | 没有nativeconsumer接口/变化事件；DB running不等live，Idle0不等started；唯一WS失效事件refetch |
| L26 Files/default cwd | N+F，local named-profile默认cwd条件A | existing fs read/backend +session_workdir；§1.16 | SSH已profile；local fs default读取serving config，named-profile可能与create不同，不默认修、先目标actual配置证据；V1无writeUI |
| L27 routes/drafts/IME/scroll/visuals | F | 浏览器URL/history、IndexedDB text/blob allowlist；§1.2/1.6 | 无backend side-effects；四viewport/keyboard/camera真机证据边界保留 |
| L28 approvals/clarify/error | N+F | request.answer/approval.*、open_requests/replay；§1.5 | 服务端request正确answer，expired不假成功，safeMarkdown/link白名单 |
| L29 Full audit/historical snapshots/memo archives | D | 06 division5，现有Core仅保留 | 不新read hierarchy/UI/schema/导航 |
| L30 Files write/workspace switch/历史附件link/用户run Noting | D | 06 §1.15/1.16/division5 | 即使native有write方法也不暴露；Take Photo是V1 F而非D |

## 8. 候选 delta manifest（全部未实现，名字不是现有API）

兼容原则：新method、新event；不改旧method输入/输出/错误/acceptance语义。事件read projection按normal注册契约/生成types接线，consumer不能在接口未实现时hardcode成功。每个input的profile/runtime/Turn scope都由既有transport/Session owner证明，不接受browser提供conversation_ref当授权。

| 候选名（待Main选定） | 输入/结果候选最小形状 | owner、error、durability与事件 |
|---|---|---|
| `session.steer_pending` | `{session_id,text,operation_id?}`→`{accepted,pending_id,turn_id,state}`；拒绝inactive/compressing/closing/invalidpayload，禁止fallback Prompt | Agent buffer owner；operation_id只有原子dedupe实施后才支持。accepted_id可已消费故state必须真实；事件`steer.pending_changed`/`steer.consumed`候选；不持久pending |
| `session.steer_pending_snapshot` | `{session_id,turn_id?}`→`{turn_id,pending:[{id,text,order}],terminal_receipts?,observed_state}` | samebuffer lock；不是inflight offsets；unknown epoch明确错；refresh无需browser持久mirror |
| `session.steer_withdraw` | `{session_id,turn_id,pending_id}`→withdrawn(original text)/already_consumed(row UID?)/already_withdrawn/unknown | buffer consume同原子域；成功只有pending；同请求重复不重复恢复text；bounded terminal tombstone |
| `session.interrupt_pending` +同operation query | `{session_id,turn_id,operation_id}`→`{operation_id,state,selected_ids,followup?}`；状态interrupted+followup_accepted/nothing_pending/not_active/already_transitioned/rejected/indeterminate | queue/Turn owner，不局部join；followup带真实accepted receipt（可新turn ID与user row ID），sameepoch retry query；natural finalizer唯一claim；partial failure显式可恢复 |
| `session.compaction_state` | `{session_id}`→`{active,operation_id?,phase,cancelable,state}` | 真实registration/fence/host；非status文本。只read，无timer/压缩请求，恢复unknown诚实 |
| `session.compaction_cancel` | `{session_id,operation_id}`→requested/canceled/no_active/already_finished/too_late/error | same fence try_cancel。请求成功表示publication不可发生，worker未必退出；terminal原生status/event；旧session.interrupt不改 |
| `secretary.state`（REST或RPC择一） | stored locator+profile（RPC可runtime）→`{global_enabled,local_enabled,conversation_ref?,task_state,task_id?,next_idle_at?,observed_at,memo_count,memo_entries?}`；分memo read也可 | owning DB read-only + liveregistry同owner（profile/db/ref核）；status首层仅count，second才取完整current内容；absence/unknown区分；不得触发attach/tick/admission/consume |
| `secretary.notebook_read`（REST或RPC择一） | same owner locator→`{exists,output,created_at?}`（readablezone） | currentpointer+renderer；四区、人类created_at，不Anchor/pointer/审计；只请求UI收到，无transcript/messages/Turn |
| `secretary.changed`（候选event） | target runtime/profile可路由 +invalidation reason task_started/task_finished/memo_changed/idle_period/global_changed | 现有owning WS；thinhint后refetch、无专用socket，不能只监听Finish而漏running首次亮起；跨进程ownerunknown诚实 |
| `session.usage_detail`（候选read+completionhint） | `{session_id}`→`{session_total:{input,cache_read,output,turns?,…},latest_completed_turn:{input,cache_read,output,model_calls,completed_at?,turn_id?}|null,availability/source}` | reuse canonical call accounting，在native Main Turn范围累加、真实completion冻结。除非已有durable事实足够，不建立通用durableTurn ledger；cold oldlatest未知直接null。旧usage event原样 |

补充可直接复用的现有事实：`agent/turn_finalizer.py` L683–690 的真实result已包含 `api_calls=api_call_count`，这是本次native Turn计数；`prompt_turn._complete_turn_payload`未把它暴露给现有event。候选usage投影应优先转发此计数，无须再以工具/assistant行自行数调用；token/cache仍须在同一Turn范围累加canonical per-call usage，不能把名字叫 `_last_turn_usage` 的last-call字典当整Turn。`_user_turn_count`冷恢复会按prior user rows推导（turn_context.py L726–757），Steer本身也是user row，因而该字段在未建立明确计数契约前不直接当历史真实driving Turns。

Secretary只读必须避免隐藏写：`resolve_conversation_ref()`是read→若bindings不完整再write（identity.py L189–194），不能直接当纯read。优先复用`resolve_conversation_ref_conn(...,read_only=True)`及已知runtime ref；没有完整绑定返回unavailable/明确无既有状态，不mint registry。`notebook_current_conn`用已有current pointer读取，不主动reselect/reconcile，不ensure_session_db_row，不调用noting attach/idle tick。`notebook_command()`复用render语义但其`_current()`走potential resolver，新增read需从稳定只读snapshot输入直调renderer。Memo可用`noting_memo_entries_conn`（ordered）而不是`noting_memo(operation=list)`的工具授权/dispatch。

Noting task源：`secretary/noting_child.py::_ACTIVE_NOTING_TASKS/_ACTIVE_NOTING_LOCK` L98–125是真进程owner；child带`_secretary_parent_conversation_ref`和专属`_session_db`，必须两者匹配。`secretary_noting_children.status=running`本身不证明线程/owner活着。无liveowner而DB running残留应unknown/stale，不能Orbactive。Idle源：`noting_idle_state` +实际timerregistry，`last_turn_started/finished`、trigger_produced/due；正在Main、已处理/off的旧deadline不可当下一Trigger，local off显示没有有效执行估计而Orb仍存在；deadline不重新arm、不从UI零倒数推执行。

缓存语义：任何read/event/delta不改root/tools/schema/cacheprefix；消费新增User行只在原生append接缝；Notebook人类view不入model。Main/global-off/ineligible paths保持原有行为，改Corebuffer/fence必须同时有旧调用回归和未启用负对照。

## 9. 执行切分与建议白名单

不是施工授权；由Main review决定最终拆分。子Agent不再派生。Core correction和atomic handoff应由**同一个实现任务**负责，因其同owner/锁域/Finalizer紧耦合，强行并行会产生协议竞态。压缩与Secretary reads可在实际文件不交叉情况下并行。

| 建议任务 | 产品修改白名单候选 | 依赖/接口/完成判据 |
|---|---|---|
| T-Correction+Interrupt | `agent/interrupt_control.py`、`agent/agent_init.py`、必要steer sibling、`agent/agent_runtime_helpers.py`只steer helpers、`agent/turn_iteration_prep.py`只插入点、`agent/turn_finalizer.py`只leftover、`tui_gateway/methods_session_interrupt.py`、`tui_gateway/prompt_turn.py`只settlement/followup、`session_auto_continue.py`只nativehandoff、对应contracts/test | 先freeze occurrence/epoch DTO，再做core所有drain及reserved交接；S01–S05、I01–I03、消费/撤回/自然完成/Stop/关闭/rotation/失败、legacy各种调用回归；不得一并改compression/usage |
| T-Compression | `agent/compression_facade.py`只registration read/cancel seam、必要compression sibling、`tui_gateway`新小methods模块、compute_host control对应模块（若actual支持）、对应contracts/test | 不碰interrupt_control与prompt_turn，直接fence-only；manual/auto/Noting、lateworker、commit赛跑与外层Turn/pending保留；新status初始read；默认不开新增flag |
| T-Secretary human reads | `tui_gateway`新read module或`hermes_cli/web_routers`新read router（二选一）、`secretary`小projection module、`secretary/noting_child.py`只owned读取与生命周期event、`noting_timers.py`只read、`framework_messages.py`只invalidation、必要memo mutation observer、对应contracts/test | 不改currentcommand adapter语义；只读before/after DB/history/model/noTurn不变量、profile/ref混淆/rapidroute、DBstale与liveowner；memo ordered、off读取；补移交C15/C16真实场景留Validation |
| T-Usage projection | `agent/turn_usage.py`只nativecall观测、现有Turn start/finalizer的**委托接缝**、usage read sibling及新methods、对应contracts/test | 与T-Correction共享finalizer时由Main串行合入或预先约定一个小callback接缝，不能两Agent同文件并写；多call/retry/fallback/compaction不混计、cold unknown、canonicalcache语义 |
| T-Frontend technical | 新并列前端repo中的network、owner binding、routing、draft、history/live reducer、commands、controls | 已有N DTO可先做contract类型与F状态机；A capability未实现显示unsupported/loading；design仅接props与token不碰network/state transitions |
| T-Visual/designsystem | 新前端repo的semantictokens、presentationalprimitives/styles | Main先给固定状态/组件props；组件目录不与technical重叠；四viewport视觉/操作完整，设计师无UX扩权 |

共享后端入口 `tui_gateway/server.py` module注册、`contracts/__init__/registry`、event/type生成与前端接口包由Main统一接线，勿多个实现Agent同时编辑。不存在新service/profile/provider改造任务。保持facade+sibling，避免在已超标大文件继续长新函数；最小接缝不得演变通用control层。

实施前应明确且记录的工程收敛：新方法最终name/status enum、liveTurn epoch定义与tombstone上限、Main shutdown等待/超时query方式、compute-host适用实际配置、localhost独立SPA认证注入/同源方式、实际attachment限额。这些是有依据的候选技术方案；若影响用户预期/权限/完成条件，按根CLAUDE顶部待追认规则登记，不把本文当用户确认。

## 10. 移交后最小必要验证范围

原生回归/实际接线都还未执行。本研究不安排大型检查。后续采用canonical runner、仓库内隔离状态、零真实用户profile；实施者仅定向证据，Main按最终集成影响统一扩大一次并共享结果。

- Pending：同文重复、multiline碰撞、consume vs withdraw、无tool requeue order、finalizer lateACK、重连freshsnapshot、不同route/session/profile、legacy steer/redirect/Stop，global-off/aux不受新Web调用影响。
- Atomic handoff：native消费/withdraw/自然完成/Interrupt各交错、恰好一 followup、pending-only且images为空、无ack重试query、partialfailure/关闭/rotation/currenttip、原ordinaryqueue不误消耗。
- Compaction：fence cancel胜/commit胜、worker late结果不发布、正在Main不停止、manualqueue保留、Noting有效Snapshot不回滚、inplace/rotation、fallback/timeout、真实initialstate与terminalring。
- Read：Secretary所有before/after仅read、无ensure/registrywrite/feedbackmessage、noSnapshot真实、memo/currentoff、trueactivevsstalestatus、真实timerdue/invalidation、快速routeowner、C15/C16移交验收。
- Browser：REST+WS真实localhost连通/auth；pagedraw原文+Framework/Reminder/compaction完整可见；truncate恢复；未知submit不重发；真实DeepSeek图片与ordinary PDF/file可读；大小限制；四viewport；真实相机/软键盘/系统swipe专项后置证据不假通过。

本研究结束只新增本报告与ignored source证据；其余产品和状态只读。Main应集中审查本文后确定A最小manifest与后端实施白名单；前端可继续已启动的N/F路径，不能把未实现A候选写成已经存在的native能力。


## 11. Main review 接收与实施准入（2026-10-12）

主会话已集中阅读完整报告，亲自核对 interrupt_control 的唯一字符串/锁、prompt_turn Finalizer 后普通队列、compression_facade registration 与 CompressionCommitFence 原子发布、methods_secretary 的 feedback 持久化及 turn_usage/server 累计计数。S01–S05/I01–I03/C01 与只读/usage 原文是可复核源码反例，满足06增量证据准入；不冒称已执行竞态测试。L08 tool args 暂按 N+F：仅显示实际可得信息，不改provider。

批准按报告原生 owner 进行 A 实现，最终方法名称确定为：`session.steer_pending`、`session.steer_pending_snapshot`、`session.steer_withdraw`、`session.interrupt_pending`、`session.interrupt_pending_status`、`session.compaction_state`、`session.compaction_cancel`、`secretary.state`、`secretary.notebook_read`、`session.usage_detail`。精确DTO在各owner实施交回时补齐本manifest；前端不得以草拟shape宣称联调通过。全部为新方法；旧methods与旧events字段不改。新事件使用 `steer.pending_changed`、`steer.consumed`、`secretary.changed`；operation状态可在pending_changed触发后通过query读，usage完成后读新projection，不另立事件socket。

工程边界：Pending采用原生buffer内的occurrence表示与Turn边界，不在RPC层新建权威队列；未激活新增Web occurrence路径时保持原生逻辑；混用legacy调用时同一owner排序、旧返回形状不变。一个实现者负责Core+Gateway交接以消除跨owner接线缝隙。epoch/receipt保留上限是bounded内存工程机制，过期明确unknown不假定pending。Followup只在真实准入后success，超时/断线保留operation query，不把Stop ACK当完成。

Secretary只读采用两个新RPC；输入可用stored locator与明确profile，无需新runtime/ensure/attach即可查看现有Conversation。不以新read启动/重新arm Idle、创建identity或写反馈。实现者需定义精确输入/错误及只读证明后交回。真实状态事件只作invalidation，再按正确owner refetch。

已核隔离runtime为原生默认in-process（dashboard turn isolation默认False，未新增配置开关）；其他原生模式保留。实施者检查hosted分支，不能读parent代理来假定child状态；若需扩展按同native supervisor接缝报告边界。新功能目标环境必须全部可用，未覆盖环境明确留证。

认证复用原生HTML注入+header/WS token；实际loopback readiness已通过。开发Vite可转发原生bootstrap，最终构建优先由已有 `HERMES_WEB_DIST` 静态托管接缝注入，不新增token分发API或弱化origin。secret不写源码/报告/持久browser数据。


### Main 补充审计：R2-F08 空闲 Send 准入交错

前端调用 `session.activate` 确认空闲后，另一个客户端可先启动 Turn；现有 `methods_prompt.py` L755–775 根据实际 busy 进入 `_handle_busy_submit`，后者按原模式 queue/steer/redirect 并可能取走 staged images。`prompt.submit` 没有 expected-idle 参数，客户端 precheck 不构成原子保证。06 §1.8 禁止 Web 隐式 redirect/通用 queued fallback，因此必须关闭此交错，不能仅把真实 accepted disposition 显示出来便宣称合规。

Main 亲读 `methods_prompt.py::_lock_in_submit_turn`、实际 submit busy/claim 路径和 `session_lifecycle._session_turn_admission`，确认已有 retirement + history_lock 准入 owner 应继续复用；不得新增平行准入 gate/队列。批准最小 additive idle-only 提交入口，旧 prompt.submit 输入/返回/原生语义保留。实现必须同时审查 busy precheck→handler 与 idle break→原生 claim 的间隙；简单外层持 history_lock 调整个旧 handler 会跨原 session_resume_lock 锁序，不能未经证明照做。当前为源码反例准入，方法名/精确 DTO 和机制验证待专门开发交回；根 CLAUDE 已登记 Agent 自主收敛／待追认，不是已获用户确认。
