# Noting 长时间运行与持久化只读调查

## 范围与结论

用户现场要求只读调查最新 Main 写入 Memo 后的后台 Noting，区分仍在执行、已完成但 UI 未刷新、失败及持久化异常。本报告依据 2026-10-13 11:34–11:38（Asia/Shanghai）的已取得证据整理；落文档时未重新查询模型或数据库。

**结论：两个 Noting 均已自然完成。旧任务长耗时直接来自首轮 DeepSeek 流持续 388.84 秒后传输中断、Hermes 原生重试；未发现数据库提交卡死。** 首轮有效回复之前约 410 秒，之后约 36 秒完成工具处理与提交。UI 未由本调查者独立操作，不能将后端正常结束直接写成 UI 已正确刷新。

调查全程未停止任务、force dispatch、重启服务、修改配置或数据库、发送模型请求。只读数据库使用 SQLite URI `mode=ro`，仅访问下述隔离 profile；原生 RPC 仅调用只读状态、会话列表和事件回放。落文档仅修改本报告，不改产品源码、核心文档或规格。

## 身份与权威入口

| 对象 | 精确身份 |
|---|---|
| 隔离 profile home | `/Users/edgar/code/hermes-secretary/.hermes-dev/round2-runtime` |
| 本 profile DB | `.hermes-dev/round2-runtime/state.db` |
| 原生服务 | `http://127.0.0.1:53445`，当前产品 checkout `494de9a739f6bf0ccd898037d98a3e5b79215dba` |
| Web 开发服务 | `http://127.0.0.1:5173` |
| Main stored session | `20261013_111430_4c8d85` |
| Main 标题 | 检查文件上传内容可见性 |
| Main live runtime | `e66fc3a9` |
| Conversation | `conv_3390f70fe5064b2882930f7eb9945837` |
| Memo 后旧任务 | admission17，child `noting_8db1d9fe34254b60`，Anchor `b665f65c7a5b49bb8d3a14cbcd756f5b` |
| 后续 Main Turn 后新任务 | admission18，child `noting_dd4d751a5a6249e1`，Anchor `7fc11233f47d442094bcc7251769cc27` |

实际 Main 由 `session.list` 与 SQLite `sessions.source=desktop / parent_session_id=NULL` 交叉确认。用户提出新开最新会话后，本次没有依赖旧测试会话名称推断身份：真实 Main 的 row250 在 11:27:44.689 请求“往 memo 里随便写个东西，让后台去整理 notebook”，row251/252 在 11:27:48.779 完成 `noting_memo.add`，可准确对应本次问题。Noting 子会话均为 `source=subagent` 且指向上述 Parent，未将最新子会话误认 Main。

审查规格入口：

- [02 §3.2–3.4：局部状态、不可变 Snapshot 与原子 pointer](../../docs/02-noting-system-specification.md#32-conversation-local-noting-state)。
- [02 §4.5：原生 Idle Timer](../../docs/02-noting-system-specification.md#45-idle-trigger)、[§4.8：同 Anchor admission 与不同 Anchor 并发](../../docs/02-noting-system-specification.md#48-trigger-admission-and-anchor-freeze)。
- [02 §5.4：持久 child、强 owner 与一次性 lifecycle](../../docs/02-noting-system-specification.md#54-persistent-noting-child-ownership-and-one-shot-lifecycle)。
- [04 §4.5–4.7：执行来源、终止工具与终止审计增量](../../docs/04-hermes-secretary-v1.5-implementation-spec.md#45-d01最近一次实际-main-模型请求的执行来源门禁m26定稿)。
- [06 §1.15：只读 Orb、真实执行/完成状态](../../docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#115-secretary-orb-noting-status-and-memo-stick)、[§2.6：Secretary human-only read contracts](../../docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#26-secretary-human-only-read-contracts)。

## 时间线（均为 2026-10-13，UTC+08:00）

| 时间 | 事实与证据 |
|---|---|
| 11:27:44.689 | Main row250：用户要求写 Memo，让后台整理 Notebook。 |
| 11:27:48.779 | `noting_memo.add` 完成；`memo_id=1`、index1，真实 Main tool result 为 row252。 |
| 11:27:54.534／.550 | admission17 admitted／旧 child 开始，持久化初始 Noting task wrapper row256。 |
| 11:27:54.566 | 旧任务创建原生 `chat_completion_stream_request` 客户端，进入 DeepSeek 首轮流式调用。 |
| 11:32:34.113 | 用户又向同一 Main 提交一分钟命令行休眠请求，启动新的 Main Turn；不取消既有 Noting child。 |
| 11:33:41.235 | 新 Main Turn 结束，当前原生 Idle deadline 计算为结束后 15 秒。 |
| 11:33:56.235／.241 | `due_at`／`trigger_produced_at`；admission18 于 .253 admitted，新 child 于 .327 开始。 |
| 11:34:13.447 | 新 child 首个 assistant 工具调用 row263／`session_history`，下一行真实 tool result row264。 |
| 11:34:23.401 | 旧任务首轮流中断，`RemoteProtocolError`，原生 `Stream drop on attempt 1/3 — retrying`。 |
| 11:34:24.416 | 旧任务重建 stream 客户端进行原生重试。 |
| 11:34:44.627／.629 | 旧任务第一轮有效 API 回复完成／assistant row271 持久化；距任务开始约 410.08 秒。 |
| 11:34:52.176 | 新任务 `finish_noting` tool result row278 成功。 |
| 11:34:55.892 | 新任务 Snapshot 提交，同时消费、归档实际处理的 Memo。 |
| 11:34:55.896／.901／.904 | 新任务向 Main 持久化完成载体 row280／admission completed／child ended。总耗时约 59.65 秒。 |
| 11:35:17.651 | 旧任务 `finish_noting` tool result row288 成功。 |
| 11:35:20.334 | 旧任务 Snapshot 提交；较早 Anchor 的晚完成不倒退 pointer。 |
| 11:35:20.340／.346／.351 | 旧任务向 Main 持久化完成载体 row290／admission completed／child ended。总耗时约 445.81 秒（7 分 25.8 秒）。 |
| 11:35:49.608 | 原生 `secretary.state` 返回 idle、tasks 空、memo_count0，profile_home 精确匹配隔离 profile。 |

当前 ignored profile 的 `noting.idle_delay_seconds=15` 与 `model.supports_vision=true` 已只读核对；本次没有修改它们。上表新周期的原生持久事实为：`last_turn_finished_at=1791862421.2346141`、`due_at=1791862436.2346141`、`trigger_produced_at=1791862436.240582`，deadline 精确为结束加 15 秒。旧任务在配置调整前已 admission，不能用当前 15 秒配置倒改其历史周期。两个不同 Anchor 的并发本身符合 02 §4.8，不是重复派发同一 Anchor。

## 长耗时的直接证据与边界

[原生 agent.log](../../.hermes-dev/round2-runtime/logs/agent.log) 第 **1120 行**与同 profile `logs/errors.log` 保存旧任务流中断事件：

| 字段 | 已观察值 |
|---|---|
| provider／model | custom／deepseek-flash，原生请求流 |
| HTTP status | 200 |
| 首 chunk 延迟 | `ttfb=0.95s` |
| 累计流时间 | `elapsed=388.84s` |
| 已接收数据 | `chunks=3872`、`bytes=171034` |
| 正常结束标记 | `finish_reason_seen=False` |
| 异常 | `RemoteProtocolError: peer closed connection without sending complete message body (incomplete chunked read)` |
| 原生处理 | `Stream drop on attempt 1/3 — retrying` |

日志第 **1129 行**记录随后第一轮有效 API response：`API call #1`、`latency=410.1s`。第 **1150 行**记录最终 Turn 正常结束，`reason=text_response(finish_reason=stop)`、`api_calls=7/50`。两任务均最终记录 7 次有效 API 调用、14 条 child transcript，并有正常 `agent_close` 日志。

这证明旧任务此前持续接收 provider 数据，之后发生传输中断并重试，不能把“数据库尚无 assistant row”或“api_call_count 仍为 0”理解为后台未执行或 owner 已丢失。未完成流的中间数据不等同持久化完成的 assistant 消息。日志无法继续区分 DeepSeek 服务内部、具体网络链路或代理为何在该时点中断；不能把这一层未确定的原因写成已确认故障。

## Snapshot、Memo 与 pointer

| 持久化事实 | 结果 |
|---|---|
| 新任务 Snapshot | `snap_d6fad34bf545407b9670b8cf399ba745`，Anchor `7fc11233f47d442094bcc7251769cc27`，11:34:55.892090 提交，termination type 为 `finish_noting`。 |
| Memo 消费 | `secretary_noting_memo_archive.archive_id=1`，`entry_count=1`，snapshot 指向上述新任务 Snapshot；`archived_at` 与 Snapshot `created_at` 同为 1791862495.89209。当前有效 Memo 空。 |
| 旧任务 Snapshot | `snap_532cc34884f64259be4dcf8d035c0d5c`，Anchor `b665f65c7a5b49bb8d3a14cbcd756f5b`，11:35:20.334359 提交，termination type 为 `finish_noting`。 |
| current pointer | 仍为 `snap_d6fad34bf545407b9670b8cf399ba745`，对应较新 Anchor；较早 Anchor 晚结束没有将 pointer 倒退。 |
| 终态 | 两条 `secretary_noting_children` 为 completed 且有 `finished_at`；两条 native sessions 有 `ended_at`／`end_reason=agent_close`。 |
| Main 完成通知 | row280／290 分别于 11:34:55.896210／11:35:20.339503 正常持久化。 |

原子机制由 [hermes_state_secretary_notebook.py](../../hermes_state_secretary_notebook.py) 的 `notebook_commit_snapshot_conn` 复核：同一写事务执行 Snapshot INSERT、`consume_memo_conn` 和 `_notebook_reselect_pointer_conn`；pointer 依 Anchor 路径位置选择最新有效 Snapshot。实际数据与此机制一致，不是仅凭一列 status 推断提交成功。

## live owner、完成事件及 UI 边界

原生 `secretary.state` 的读取入口与投影见 [methods_web_read.py](../../tui_gateway/methods_web_read.py)、[web_read.py](../../secretary/web_read.py)。其 active 判断读取拥有本 profile DB 与 Conversation 的 `_ACTIVE_NOTING_TASKS`，不存在 live owner 而 DB 仍为 running 时会返回 unknown；并非直接将数据库 running 映射为 active。本次 11:35:49.607585 的真实 RPC 返回：

- `availability=available`、`global_enabled=true`、`local_enabled=true`。
- `task_state=idle`、`tasks=[]`、`memo_count=0`。
- `next_idle.state=absent`，该周期已产出 Trigger，没有杜撰下一次 countdown。
- `profile=default`，`profile_home=/Users/edgar/code/hermes-secretary/.hermes-dev/round2-runtime`。

`session.active_list` 确认 Main runtime `e66fc3a9` 为 idle。该 runtime 的 `session.events.since` 真实回放包含：

| seq | 正式事件 |
|---|---|
| 9687 | `secretary.changed / task_started` |
| 9688 | `secretary.changed / notebook_changed` |
| 9690 | `secretary.changed / task_finished` |
| 9691 | `secretary.changed / notebook_changed` |
| 9693 | `secretary.changed / task_finished` |

所有列出的事件均携带正确 profile_home、Conversation 和 runtime ID。回放 `latest_seq=9693`，`count=512`，`truncated=true`；只能证明缓存内列出的完成事件已正式发布，不能宣称回放覆盖任务开始以来全部事件。

完成发布由 [noting_child.py](../../secretary/noting_child.py) 的 finally 路径执行 `finish_child_admission`、unregister（发出 `task_finished`）、child.close；[methods_web_read.py](../../tui_gateway/methods_web_read.py) 将 owning invalidation 发到真实 runtime 与全局 WS peers。前端 `/Users/edgar/code/hermes-secretary-web/src/core/controller.ts:897` 对 `secretary.changed` 核 profile／Conversation 后调用 `readSecretary`，全局 `task_finished` 驱动 completion revision。

本调查没有操作浏览器，以避免与 Main 的 UI 操作冲突。**后端当前 idle、完成事件已发布，不等同已独立证明某个 UI owner 收到了事件并正确刷新。** 若 Main 现场在 11:35:20 后仍观察到 active，应核该 UI owner 的 Secretary read、route/profile 归属与错误状态；本报告不将假设写成已确认 UI 缺陷。

## 最小处理建议与交接

当前不需要修改数据库、timer、后台完成条件或停止任务；原生流重试已成功，两个任务及持久化链路已结束。若需继续缩短慢响应，需另行审查 provider 流与等待诊断的授权范围，不能以本次异常擅自改变 Hermes 的请求、超时或重试机制。

Main 可用本报告与已存在日志集中 review，并现场核当前 Orb/Memo 显示；只在实际 UI 仍异常时补对应读状态证据。此为开发期只读调查，不是独立 Verification／Validation，不补写整轮验收通过。

## 最新Secretary task与Schedule核查（R2-C61–C63）

用户指定同一会话「检查文件上传内容可见性」。Main只读state.db `secretary_notebook_item.id=12/conversation_ref=conv_3390f70fe5064b2882930f7eb9945837`：type=secretary_task、status=pending、payload无schedule，内容为待同意后的原生视觉配置验证。全profile `secretary_schedule_registry=0`、`secretary_pending_reminders=0`。因此当前pending是任务状态，不是已到期pending Reminder；没有注入故障证据。用户已纠正可能误读，不新增schedule/force dispatch/改Notebook；精确来源记录保存在ignored `main-final-integration/repair-reminder-source-proof.json`。首次查询误用entry_id（表实际id）报错，随后按真实schema成功，不把该查询失败当产品故障。

## Main 最终集成接收

2026-10-13：Main集中亲审正式路径与改动并接收相应owner证据，最终前端c55120f、visual fc18614、原生产品4443aa7。用户自测整改的实际关闭范围、测试失败/修复留痕、真实DeepSeek/IAB及未验证边界统一见final-delivery「当前整改关闭证据」和根CLAUDE；本报告上方“待实测”是交回时观察，不覆盖该最新接收。最终冻结前端health0/0及build/types通过；两独立门禁未执行，不称整轮验收。
