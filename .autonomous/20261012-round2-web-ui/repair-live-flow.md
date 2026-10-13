# 真实消息顺序、流式、Usage 与 Steer 消费调查

2026-10-13，Development `live_order_stream_usage`。C58 调查阶段报告已由 Main 集中读取，随后明确恢复 R06–R10，并追加 R02 原生取消状态及 R13 human-only Notebook 固定位置。**当前前端机制已完整交回，待 Main review、统一 native 契约生成/运行版本和真实 DeepSeek/IAB 实测；本报告不是验收通过声明。**下方保留先前调查与第一组证据，最新实施与七字段交回见文末。

## 范围与版本

- 依据：现行 06 §1.4–1.5、§1.6、§1.9、§1.13 与 §4.5；02 §1.6 Message Identity、§1.7 source of truth。遵循实际 source 顺序及 `(conversation_ref, message_uid)`，不按文字、工具名或时间戳猜排序。
- 前端 `/Users/edgar/code/hermes-secretary-web`，HEAD `21aad02c2d0ebe8ff377ec8fd19b2b84ba1d4296` 加现有未提交集成修改。本 Agent 只修改 `src/core/controller.ts` 与 `src/core/controller.test.ts`；`projection.ts` 只读。保留 Main 的 initialize 幂等、同 owner HMR 以及附件展示/工具卡接线。
- 后端 `/Users/edgar/code/hermes-secretary`，HEAD `494de9a739f6bf0ccd898037d98a3e5b79215dba` 加现有工作树。真实库 `.hermes-dev/round2-runtime/state.db` 只读；未写配置/数据库、未重启 53445/5173、未发送模型请求、未操作用户浏览器。
- 本报告为本 Agent 唯一过程文档；未改核心看板或权威规格，未提交、构建或运行全量测试。

## 真实来源证据

stored Conversation `20261013_111430_4c8d85` 对应 runtime `e66fc3a9`。SQLite 查询只读取 `id/role/timestamp/message_uid/display_kind/display_order` 等来源字段，内容摘录仅辨别原生 carrier，不用于排序。

| row | 原生类别 / UID | 事实 |
|---|---|---|
| 255 | Assistant / `b665f65c7a5b49bb8d3a14cbcd756f5b` | 前一回复，timestamp `1791862072.4981` |
| 257 | 普通 User / `835fdc69578a45858ab0feb907d1ca7a` | 下一普通 Send，timestamp `1791862354.10412`，真实持久顺序在 255 后 |
| 258 | Assistant / `183d70bff9bb4711ad74db0305ff4907` | 工具调用前 reasoning 370 字符 |
| 259 | Tool / `7ee64c140ae0407ab1fc360dfc502e6e` | sleep 工具结果 |
| 260 | User，`display_kind=steer` / `22b12a41a70c4726b3a3d8f98e438985` | 真实合并 Steer 原位插入，`display_order=260`，在工具 259 后、Assistant 261 前 |
| 261 | Assistant / `7fc11233f47d442094bcc7251769cc27` | 最终回复，`display_order=261`；timestamp 比 260 早约 1ms，证明不能按时间重排 |

只读 native `session.active_list` → `session.events.since(last_seen=0)`，来源为现有 53445 `/api/ws`。认证仅使用 native bootstrap 内存值，未打印或保存 token。返回 replay 已截断，最高 seq `9693`：

- `steer.consumed` seq `9202`：`message_uid=22b12a41a70c4726b3a3d8f98e438985`。现行事件没有真实 combined message 或插入前驱元数据。
- `message.complete` seq `9682`：`status=complete`，`persisted_turn={row_ids:[257,258,259,260,261], complete:false, user_row_id:257, final_assistant_row_id:261}`。
- replay 截断，因此**没有**前一普通 Turn 的完整 delta/complete 证据，不能将当前 partial receipt 直接判为 A 的唯一现场根因。

Main 已取得同一真实凭据的本地证据入口：`.hermes-dev/round2-evidence/main-final-integration/repair-native-complete-receipts.json`（ignored），`truncated=true`、512 events、seq9682 `text_length=349`。以上字段与本 Agent 只读观察一致；Main 判定当前 A/Framework 更新重复位于实际 partial receipt 路径，后续应以此来源复现并修复，不再重拉，不凭正文去重。

## A：新 Send 出现在上一 Assistant 前

已查接缝：

- 前端 `src/App.tsx:437–460` 直接拼接 `[projected history, ...live.nodes, temporary]`。没有独立的 completed-live 历史位置锚点；未退的旧 live 永远位于所有历史后面。
- `src/core/controller.ts:993–1037` 的 `finishHistory` 在完成后刷新历史，先按 `persisted_turn.row_ids` 找对应 persisted rows。只有完整凭据且所有行可见，才整批退掉当前完成节点；partial 通过正文/reasoning/工具 ID 比对局部匹配。
- 凭据缺失时 `stored=[]`，旧 live 无法退出；随后新的 Send 刷新 history，将新真实 User 放在旧 live Assistant 之前。这是可从源码推导的明确失败路径，**尚未取得该现场上一 Turn 凭据缺失的反证/证明**。
- `performHistoryRead` 在 `controller.ts:689–690` 先 publish history，`finishHistory` 随后单独 publish 已退 live，存在过渡期重复和先后位置变化。

调查阶段建议：在一个 source-owner 提交点原子交换 history/live，并用真实 native message UID、source 边界和真实持久化凭据退 live；完成时保存被封存的节点范围，不能把下一 Turn 一并退掉。缺失/partial 凭据要保留 unknown，不可靠内容猜身份，也不可按 timestamp 重排序。**该路径随后已实施，见文末当前交回。**

## B：Thinking 滞后，Turn 结束后全量瞬现

- `projection.ts:297–437` 的 `reduceEvent/appendStreamText` 同步追加 native delta；没有 timer 字播或固定限速。未发现主动播放积压的实现。
- 已证明确实存在恢复积压：原 `controller.recover` 把 `replayHeld` 的放行放在 `ensureBinding + REST refreshHistory` 之后，因此 replay 已恢复 cursor 时，新实时 delta 仍被慢网络读挡住。
- 已落第一组修改：`controller.ts:1040–1097` 在 replay 应用/判定结束后的 `finally` 立刻释放 hold；随后完成 binding/history 查询。事件 seq 去重保持原路径，失败仍释放 hold，不添加播放 timer。
- 用户现场持续连接时的慢输出是否由此造成，**未证明**。App 历史 Markdown/长附件重渲染也可能贡献主线程延迟；Main 正在处理展示与 memo 接线，这不是本 Agent 已验证的唯一根因。
- replay 截断时仍遵守原历史恢复路径，不能把截断 replay 宣称完整来源。真实下一次流式需同时记录 native seq 到达、controller 可见文本与 UI 更新时间，区分网络/恢复扣留和渲染开销。

## C：active 期间保留上次已完成 Usage

- 原生 `agent/usage_read.py:55–76` 只替换 `owner.active`；`owner.latest` 保留上一完成 Turn。`main_usage_detail:274–296` 返回上一 `latest_completed_turn`，但 Session Total 会合入 active 未知桶，计数可变成 null；并非每次都能作为稳定已完成显示替换。
- 原前端 `controller.readUsage` 无条件替换可见 detail，故 active 期间原生 unknown 会清掉已有数字。
- 已落修改 `controller.ts:1465–1493`：本会话有已显示快照时，active 中的普通读取不替换它；`message.complete` 正式读取传 `completed=true` 更新。没有自行估算计数，也没有写 localStorage 或跨 Conversation 缓存。
- `select` 的同 exact profile+route 保留 detail（`controller.ts:456/483`），切 route 清掉；读取回包继续校验 exact key、runtime、serial，防止串会话。
- 限制：页面首次进入正在运行的 Conversation，没有本地既有显示快照时只能显示实际 native detail，不能从生命周期总量反推上一完成数。真实 completed→active→completed 页面数值仍需 Main 实测。

## D：断连保留会话、历史、草稿和内存

- 当前 `controller.ts:338–352` 的断连 callback 只改变 connection 和 live active/status；保留 live.nodes、history、sessions、draft。原全空现场根因由 Main 查为 HMR owner 重建，本 Agent 未重新实现持久缓存。
- 本 Agent 增加断连 owner 行为测试：真实 `Gateway.setState('disconnected')` callback 后三类数据与 live.nodes 引用保持，草稿仍可编辑，active 改为 unknown。
- Composer 断连提示和发送按钮禁用归 Main；本测试**不**声称验证了视觉/按钮状态。

## E：Steer 消费后立即显露真实合并 User

- 原生 `agent/pending_steer.py:305–325` 的 `append_claimed_batch` 在同 lock/claim owner 生成 combined row、stamp message UID、原位插入 model messages、将 pending 状态改 consumed，然后发 `steer.consumed`；**该处没有持久化 row**。
- `tui_gateway/methods_pending.py:8–12` 透传该事件。当前 payload 只有 `turn_id/pending_ids/message_uid`。
- 前端 `controller.ts:965–978` 已在 consumed 调用 `refreshHistory`，但 REST 来源是 SQLite，读取早于这条 row 持久化；当前刷新得不到真实 User。Pending snapshot 已显示 consumed，临时泡消失，而真实泡缺席，直到最终完成刷新才出现。
- 真实 seq9202 与 row260 UID 完全一致，最终原位正确；问题在即时来源接线，而非最终重排序。

建议最小 native 增量（**Main 已认可字段方向，尚未实施**）：同原生 insertion owner 发布 `payload.message` 为刚插入的真实 combined row（role/content/display_kind/message_uid），并发布 `after_message_uid` 为真实原位前驱或等价、能准确表达该插入点的 source 边界。timestamp 只携带原行已有的真实记录，不制造 browser 时间。前端只投影这一个真实 UID 对应 User，在 durable history 后按同 UID 原子交接。不能用 pending 草稿本地拼接多泡、猜时间或猜工具边界。若插入前驱在 live 中缺 UID，还需 native 真实 source 映射或完整有界 source 前缀；仅补 UID、前驱但前端仍无法定位，不算完整接线。

Conversations 列表当前主要在 Send/完成时回拉；consumed 的列表刷新可随实际 source 发布一起接，但只回拉 SQLite 列表无法使尚未持久化的 row 自动出现。Main 需确认列表的稳定展示来源和更新点。已有真实 User 增长动画 hook 由 Main 复核接入，不在 controller 伪造合成消息触发动画。

## 第一组最小测试证据

前端上述 HEAD + 当时工作树，2026-10-13 11:40 本机：

```text
npm test -- src/core/controller.test.ts -t 'releases recovered live|keeps observed Usage|preserves conversation/history/draft'
3 passed / 57 skipped，1 test file passed，Vitest 4.1.11，282ms
```

精确用例位置（当前源文件）：

- `controller.test.ts:441`：replay 已恢复但 binding promise 未结束时，新 reasoning delta 立即进入 visible live。
- `controller.test.ts:463`：active native null counters 不清旧 Usage；真正 message.complete 更新；离开 Conversation 不串 detail。
- `controller.test.ts:497`：断连保留 sessions/history/draft/live.nodes，并允许继续编辑。

57 skipped 是本次名称过滤范围，不是功能测试失败；既有 63 contracts + 15 附件证据未复跑。未跑 typecheck/fullbuild/fullsuite；未运行新的真实流式/Usage/Steer/断网浏览器场景。Main 集中读报告后需给下一次修复的 source 字段、owner 及白名单，再组织必要真实 DeepSeek 场景；仍停 Verification 前。

## 当前完整交回（2026-10-13 12:26；12:36 健康微重构与类型修正）

### 1. 对应条款和最新授权

06 §1.4–1.5 的 source 顺序、真实 streaming、重连去重；§1.9 的同 insertion point 单个真实 User 与 Pending 转移；§1.13 的原生 Usage；02 §1.6 的 Message Identity、§1.7 的事实源。R06–R10 为本次主体；Main 追加 R02 固定原生取消包装状态、R13 `/notebook` 输出固定在**发起命令时**的 Conversation 序列边界，刷新可消失，不进入 durable/model history。

已读 executing-plans 全文、autonomous-run 子 Agent 阶段交接、本轮 baseline/snapshot/plan/current CLAUDE 和派遣条款。遵守白名单、健康阈值和不重跑有效证据；不改权威文档、核心看板、后端代码、配置或运行状态，不提交/构建/重启/派门禁。

### 2. 实际变更

- `controller.ts:693–701`：REST 页完整读取成功后，一次 publish 同时更新 history、退已证明的 live、交接临时输出锚；删除原 `finishHistory` 的正文/reasoning/工具 ID 猜配和独立第二次 live publish。
- `projection.ts:469–576`：按 `message.start` 的本地 turn 范围封存节点，接消费前缀/完成 suffix 的 native source checkpoint。完整旧 receipt 或真实 boundary/ordered UID/row 证明成立才退整段；partial 的 source facts 可交接 UI，但不改 native `complete=false`。结束与下一 Turn 范围隔离，迟到旧读取不能退新节点。
- `bindSourceNodes` 仅在原 prefix/压缩边界可靠、UID 全部真实、native kind/role/tool occurrence 与封存流段严格一一对应时绑定来源；数量/顺序不匹配或 unknown UID 不推断。已知 final row 地址、同 UID 来源按 exact identity 局部退，不按内容匹配。
- `projection.ts:507–530`、`controller.ts:874–914`：消费事件采用 native combined message 和真实 predecessor/after UID，当次 publish 同时移除对应 Pending、显示一个真实 User、更新该会话列表 preview。DB 未 flush 时保留真实事件行；后续同 UID 历史接手，重复消费事件幂等。已在 durable history 中的旧消费事件不会拿当前新 Turn 建 checkpoint。
- non-tail 消费按唯一真实 predecessor 插入，`insertion_at_tail=false` 不允许整批退消费后的 streamed 内容。不用工具名或时间排序。
- `projectTimelineNodes(history, live, temporary=[])` 按真实 UID/节点边界合成唯一 Timeline；unknown 身份保留在完成事件当时已观察的真实历史边界，下一 User 不会绕到它前面。unknown 状态不能凭同样文字冒充已完成去重。
- 第一组 B/C 改动保留：replay cursor 处理完即放行，不等待慢 binding/REST；active 保已显示原生 Usage，完成刷新，不持久化第二份历史/计数。D 断连保数据测试保留。
- `composerActionPolicy` 新增 optional `connected`：只有显式 false 禁 Send/Steer 和 Enter，兼容既有未传值的调用；本地 Cancel Send 仍可用，草稿编辑状态不受影响。
- `toolResultState` 精确识别 `tool_executor.py:980/1537` 的完整 `[Tool execution cancelled — <name> was abandoned: ...]` / `was skipped. ...` 包装及 native cancelled/interrupted metadata，显示 interrupted；普通正文含 cancellation 单词不误判。
- `readNotebook:1448–1465` 在发 RPC 前捕捉真实 UI sequence boundary；在途边界留在同 Controller 的短期内存，native 交接更新 exact anchor，RPC 返回按原边界显露，finally 释放。`temporary:1943` 不制造时间、不持久化；idle、final stream、reasoning→durable 锚都有正式反例。
- 仅按 Main 要求在 HMR 保留区补 `Object.setPrototypeOf(controller.gateway, Gateway.prototype)`；API 重连机制属于另一 owner，本 Agent 不改 client.ts。

### 3. 正式路径

`Gateway.onEvent → Controller.event → reduceEvent/native source checkpoint → reconcileLiveHistory → 一次 publish(live/binding/temporary/Pending)`；`refreshHistory → performHistoryRead → 同 owner source 证明 → 一次 publish(history/live/temporary)`。

`readNotebook → 请求发起边界 → native 事件/REST 更新在途 exact anchor → temporary human-only result`。临时输出不含 source message 身份、不入 DB/model context，刷新/新 Controller 时为空。

Main 已确认 App 接入 `projectTimelineNodes` 第三参数、history projection 独立 memo，并保 Rewind cut/hiding；ChatComposer 已传 `connected: state.connection === 'connected'`。这些 App/组件薄接线由 Main 修改和审查，不属于本 Agent 改动白名单。

### 4. 验证与当前源码版本

前端 HEAD 仍 `21aad02c2d0ebe8ff377ec8fd19b2b84ba1d4296` 加未提交集成修改。执行方本 Agent；受控依赖仅 HTTP/RPC 返回和 promise 屏障，实际 Controller/Event/REST commit/投影运行，不读取源码断言、不镜像待测机制。

| 次数/触发原因 | 精确选择 | 结果 |
|---|---|---|
| 第一组，旧有效证据 | `npm test -- src/core/controller.test.ts -t 'releases recovered live\|keeps observed Usage\|preserves conversation/history/draft'` | 3 PASS / 57 skipped，282ms |
| 初次接线，新增和实际受影响旧流段 | `npm test -- src/core/controller.test.ts src/core/contracts.test.ts -t 'native source ownership\|blocks disconnected Send\|exact native cancelled\|releases recovered live\|keeps observed Usage\|preserves conversation/history/draft\|independent native stream segments\|native spinner versus reasoning identity\|formal native stream spinner lifecycle\|does not complete a Turn'` | 14 PASS / 115 skipped，620ms |
| findLastIndex 兼容修正、non-tail/幂等增强后的相关包 | `npm test -- src/core/controller.test.ts src/core/contracts.test.ts -t 'native source ownership\|exact native cancelled\|formal native stream spinner lifecycle\|does not complete a Turn'` | 8 PASS / 122 skipped，642ms |
| R13 发起时边界和延迟回包，增强同一原用例 | `npm test -- src/core/controller.test.ts -t 'keeps human-only Notebook output'` | 1 PASS / 64 skipped，360ms |
| 冻结 2,000 行约束，将同 5 例移到既有 contracts 并精确加独立 fixture；非新增覆盖 | `npm test -- src/core/contracts.test.ts -t 'native source ownership'` | **最终位置 5 PASS / 65 skipped，624ms** |

各包重叠，**不相加为总通过数**。首次 typecheck 命中本 Agent `findLastIndex` 编译目标兼容错误，已改兼容实现；第二次只命中 Main ChatDialogs 两处 useEffect 重复 import，Main 修复后报告一次集成 typecheck PASS。最后 Notebook/测试组织小改后按 Main 要求不再重复 typecheck，由 Main 最后 build 包含 types。最终 `git diff --check` PASS；未做 fullbuild/fullsuite/真实模型/IAB。

当前最终 source SHA-256：

| 文件 | SHA-256 |
|---|---|
| `src/core/controller.ts` | `4c3efeeb877b36a8bdac4d83ac433b636c7e175fd4d4b0e6ec559ba14ccf9bcd` |
| `src/core/projection.ts` | `fca837c05db5f32e50fd1d0e60e50d9e8c2f1e3f07be0e97159b8e86c2b2d879` |
| `src/core/controller.test.ts` | `0902c5278d0320395e535c5a94a0de497256448deea061a7014226c98b32f7b0` |
| `src/core/contracts.test.ts` | `1a924717ad51449047af655965a24f96319c39c739ec94096d7c3a90b74d0220` |

controller 最新 1,970 行、controller.test 1,937 行、contracts.test 798 行；未改阈值或新建并行测试文件。正式来源反例当前在 `contracts.test.ts:581–798`：消费早于 DB flush → partial completion → Framework →实际下一 Send；迟到旧完成读取与新 Turn；non-tail 原位插入保后续流；partial/no source 不凭相同文字猜 UID；Notebook idle/延迟回包/final stream/reasoning→durable 固定锚。

### 5. 缺口与实际限制

- 尚未取得本次实际 DeepSeek/IAB 的 R07–10/R13 现场通过证据。B 在持续连接时的体感速率仍须实际 event/controller/UI 观察；本 Agent 只证明 replay 不扣到慢 REST，没有模拟限速或宣称性能问题唯一根因。
- old replay 截断、unknown UID、压缩/prefix 改变、来源形状无法严格对齐时，未证明的 live 保 unknown；不会从正文猜身份或整段删除。旧服务/旧 singleton 中已丢来源的历史现场不能由新字段反向伪造证明。
- 新 source field 依赖原生 owner 的准确 actual suffix/prefix 和 boundary。需 Main 核 native 代码/契约生成、服务实际版本，并按真实新 Turn 验证；本 Agent 没有操作运行中的服务器。
- Reconnect/API attempt 与旧热更新 Gateway 字段兼容由 API owner/Main 检查，本 Agent 的测试采用当前类的新 Controller；不冒称用户主 tab9 的全部旧实例重连分支已验证。
- source 槽严格绑定失败时临时输出仍保原已知历史 fallback boundary，不制造精确 reasoning UID；真实中途 `/notebook` 应检查原生实际段形状和锚交接。

### 6. 接口影响

使用原生 owner 新增的 optional `persisted_turn.source_messages/source_boundary` 和 `steer.consumed.message/after_message_uid/predecessor/source_messages/source_boundary`。既有 complete 保守语义、backend source 顺序、provider/model/loop 不变。

前端新公开接缝：`projectTimelineNodes(history: TimelineNode[], live: TimelineNode[], temporary: TimelineNode[] = []): TimelineNode[]`；`composerActionPolicy` readiness optional `connected?: boolean`。Main 已薄接入。Native consumed 尚无 durable row 地址时 UI 只展示真实事件行；Main 已收到应限制 Reply 于真实 durable row 的提醒。

### 7. 后续动作

Main 集中 review 本报告、前端 diff 及 native owner 报告；统一契约生成/必要稳定运行版本后，在其 IAB 窗口跑一个短真实 DeepSeek Turn，覆盖真实思考/工具/Steer 消费即时单 User、active Usage、完成/Framework 后不重复、下一 Send 顺序，以及读取期间消息变化后的 `/notebook` 位置。真实断连/恢复保稿、Composer 禁发送与状态提示由 Main 一并验。只复验实际受影响路径，不重发500 MB或复跑既有整套；继续停 Verification 前。

## 12:36 健康门禁微修正完整交回

1. **条款**：沿用以上 R06–10/R13 来源、单 owner 原子发布与冻结健康阈值；Main 基于 `bfecc9f` 检出新增 `performHistoryRead CC22`、`event CC26`，要求微重构，未授权改阈值/allowlist。
2. **实际修改**：仅生产 `controller.ts`。`performHistoryRead:641` 读取成功后委托 `commitHistoryView:708`；`event:857` 委托 `reconcileEventView:894`，两路径共享 `reconcileLiveView:713` 进行 source 退休及临时锚交接。新增条件由各准确 helper 承担，原行为和 owner 不变。`temporary:1949` 第三参数显式声明 `Pick<TimelineNode, 'afterNodeId' | 'afterMessageUid' | 'anchorFallbackUid'>`，解决可选 anchor 字段与默认参数推断 required 属性的 TS2345；纯类型修正。
3. **正式接线**：history 仍由 `commitHistoryView` 一次 publish `history/live/temporary`；event 仍在 Controller.event 一次 publish `view/binding/consumedView`。不增加中间 UI 发布、不变更 cursor/replay/UID 或 Pending 状态语义；没有新文件。
4. **验证**：`npm test -- src/core/contracts.test.ts -t 'native source ownership|keeps human-only Notebook output'`，5 PASS / 65 skipped，628ms；Notebook 屏障属于该 5 例，正则并集只运行一次，没有另计第六例。按 Main 新要求仅一次 `npm run typecheck`，**PASS**。`git diff --check` PASS。controller 1,970 行，最终 SHA 更新于上表；其他三文件 SHA 未变。
5. **缺口**：本 Agent 未执行最终 health 或 build，Main 统一检查；不以本次类型通过代替冻结 health 结果。Main 已报告取得真实 IAB 的像素、两个 Steer 消费即时、Usage 保值/完成更新及 source 顺序无重复证据，具体现场产物由 Main 在其索引登记；本 Agent 未重复现场验证。以上原缺口中相关 Main 现场项以其证据审收为准。
6. **接口影响**：helper 为 Controller 私有拆分；公开 `temporary` 的 optional anchor 字段语义不变，类型更准确；App/Native/API 无新增接口或运行语义变化。
7. **下一步**：Main 集中 review 此微差异、共享定向证据和最终 source SHA，再统一 frozen health/build。用户仍停 Verification 前；本 Agent停止进一步修改，等待明确修补指令。

## Main 最终集成接收

2026-10-13：Main集中亲审正式路径与改动并接收相应owner证据，最终前端c55120f、visual fc18614、原生产品4443aa7。用户自测整改的实际关闭范围、测试失败/修复留痕、真实DeepSeek/IAB及未验证边界统一见final-delivery「当前整改关闭证据」和根CLAUDE；本报告上方“待实测”是交回时观察，不覆盖该最新接收。最终冻结前端health0/0及build/types通过；两独立门禁未执行，不称整轮验收。
