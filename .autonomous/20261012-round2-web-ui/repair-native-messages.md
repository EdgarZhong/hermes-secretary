# 原生消息观测接缝修复（R07 / R10）

2026-10-13，Development `repair_native_message_projection`；后端 HEAD `494de9a739f6bf0ccd898037d98a3e5b79215dba`，保留既有未提交修改。只改 Main 授权原生插入/完成事件及对应测试，不提交、不重启、不修改运行 profile/DB、不自行调用模型，不派生 Agent。仍停 Verification 前。

## 来源和方案

- 已读 executing-plans 全文、autonomous-run 子 Agent 消息与返回契约、根 AGENTS/CLAUDE C58、轮次索引/基线/计划和 repair-live-flow。依据 02 §1.6/§1.7/§2.1/§2.7、06 §1.4/§1.9/§4.5；消息身份由原生 owner 维护，不按正文/时间猜身份。
- 复用 Main 现场证据：stored `20261013_111430_4c8d85`、runtime `e66fc3a9`；seq9682 `persisted_turn.row_ids=[257,258,259,260,261]`、`complete=false`。尾部含普通 User257 与 Steer260，原判据要求尾部恰一 User，故**至少这一条件确定为 false**；不冒称其它 prefix/compaction 条件已从现场复原。
- R10 原 `append_claimed_batch` 同原生锁生成真实 combined User、stamp UID、原位插入并消费；`steer.consumed` 只 UID，DB 尚未 flush。将发布这条刚插入的真实消息与实际 index 前驱/有界当前 Turn 身份元数据。`display_content` 取同批原生作者文本，不改模型 content；timestamp 仅原行已有才给。旧字符串 Steer 路径不变。
- R07 原 `persisted_turn.complete` 的单 User、prefix、compaction、全部持久化及 final 判据全部保留。将增量发布 actual source 身份映射及明确边界，不携带历史正文、父 prefix 或图片 Base64；前端 owner 按正式来源原子交接，不由后端清理未知 stream。
- 白名单：`agent/pending_steer.py`、`tui_gateway/prompt_turn.py`、`tui_gateway/contracts/{pending,events}.py`、`tests/agent/test_pending_steer.py`、`tests/tui_gateway/test_pending_native_turn.py`；Main 后续明确补充 `tests/tui_gateway/test_submit_time_user_row.py` 的 receipt 行为例。生成合同由 Main 统一。

## 七项交回

### 1. 对应条款

R07/R10；02 §1.6 的 `(conversation_ref,message_uid)`、§1.7 原文事实源、§2.1 实际 live context、§2.7 压缩/rewind 身份边界；06 §1.4 真顺序/时间/单 Timeline、§1.9 同原生消费点合并一 User、§4.5 真 source/持久行而非 RPC ACK。保留原生 owner、原生 flush 和 Loop，不改模型/provider、执行或持久 schema。

### 2. 实际变更

- `pending_steer.py` 增量 observer helpers 仅读原字典；仅新 Steer row 由既有插入点 stamp UID。消费在同 `_pending_steer_lock` 捕获真实 row 与前驱、native 原 user 起到**实际 insertion index 前驱**止的身份索引；不假定永远尾部。事件额外 `message.display_content` 来源为同批实际作者文本，`content` 保留原 native steer marker；原消息无 timestamp 时不造时间。
- `prompt_turn.py::_invoke_agent` 按当前 st.history/压缩 count 绑定可选 source observer，finally 清理/恢复原回调；只用于 pending Web 观察，不进入请求/缓存前缀。完成事件额外 source 索引由结果 actual suffix 读取。原 `persisted_turn.complete` 的全部条件不变，包括单 User、未压缩、原 prefix、全部已 flush、结构选择 final 后原 body 复核；真实 Steer 的尾部仍 false。
- 可选观察异常明确省略 source 元数据，不影响原生插入/消费/原 completion receipt；不伪造 green boundary。

### 3. 正式路径与字段

`prompt.submit → _invoke_agent → AIAgent.run_conversation → append_claimed_batch（包括 pre-API 非尾 index）→ steer.consumed`；原 `_pending_publish` 透传，因此无新增 API/Loop。消费事件在真实插入完成后通知，无需提前 flush SQLite。

`AIAgent native flush → st.result.messages → _persisted_turn_receipt → message.complete`；完成观察地址只在 `_db_persisted` marker 且正 row_id 时发布。未 flush 仍可有真 UID，但不带 row_id。

| 字段 | 正式语义 |
|---|---|
| `steer.consumed.message` | 实际一条 User `{role,content,display_kind:'steer',message_uid,display_content}`；同锁源快照，不随后续 flush markers 变化 |
| `steer.consumed.after_message_uid` / `predecessor` | 实际 normalized insertion index-1 的原生身份；不存在/未知时 null，不为前驱 mint UID |
| `steer.consumed.source_messages` | actual 原 user→前驱的有序身份元数据，不含刚插入 Steer 或插入点之后已有 Assistant |
| `persisted_turn.source_messages` | actual 当前结果 user suffix，有序元数据；不发正文/历史 prefix/图片 Base64 |
| `source_boundary` | `{user_message_uid,after_message_uid,prefix_unchanged,compression_unchanged,all_rows_committed}`；原边界未知则无此项；consumed 另给 `insertion_at_tail` 真 bool |
| `NativeSourceMessage` | `{message_uid:str|null,role,has_content,has_reasoning,row_id?,display_kind?,tool_call_id?,tool_call_uid?,tool_calls?:[{id,tool_call_uid?}]}`；UID 与 per-occurrence 工具 UID 仅读原 native 字段 |

已与前端 `live_order_stream_usage` 收敛：3个 source 边界事实全 true、全部真 UID/row 在 REST 同序可见、final address 具备时才交接该 start→complete 封存范围；消费仅 `insertion_at_tail=true` 时可整体交接此前封存 stream。非尾或边界失败走准确 source 局部映射，无法证明则保 unknown；不得按正文/时间/工具名猜配或清未持久 stream。**这是前端接线约定，不冒称前端已经完成/实测。**

### 4. 验证结果

本机 macOS，PM `.venv`，isolated tmp profile/真实 SQLite/正式 Gateway RPC/AIAgent Loop；外部 provider 响应与第二次请求屏障受控。测试 fixture 明确拒绝 socket.connect/connect_ex，无真实模型流量，也未触碰用户运行 profile。

第一包命令：

```bash
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/agent/test_pending_steer.py tests/tui_gateway/test_pending_native_turn.py tests/tui_gateway/test_submit_time_user_row.py -k 'consumed_projection or legacy_dormant or claim_is or withdraw_and_real or pre_api_claim or rpc_consume_withdraw or consumed_event or true_tool_insertion or completion_receipt or completion_source_boundary' -q
```

3文件 11 passed / 0 failed，runner 8.4s；agent6、receipt2、native3。随后 review 发现可选观察异常可能 veto 原插入，隔离异常并新增一例，按实际影响定向复测：

```bash
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/agent/test_pending_steer.py tests/tui_gateway/test_pending_native_turn.py tests/tui_gateway/test_submit_time_user_row.py -k 'consumed_projection or rpc_consume_withdraw or consumed_event or true_tool_insertion or completion_receipt or completion_source_boundary' -q
```

3文件 8 passed / 0 failed，runner 3.6s；agent3、receipt2、native3。最终 8 当前包＋首包4条未受异常隔离影响的 dormant/claim/withdraw/pre-API 对照，共12 distinct；不把两次通过相加成19。名称过滤其余 deselected 不是失败，不声明三文件全例通过。

取得证据：

- 正式第二次 provider 请求屏障期间，consumed 已携真实 combined User/真 UID、前驱 UID/row/工具 call；Steer 此时确实不在 SQLite，仍可被 Web 准确展示。最终 flush 后同 UID/content/display_kind 与 DB 相同，事件快照没有后加 persistence markers。
- 同 Turn 两 accepted Steer 合并一 User；withdrawn claim 不被插入；竞争只有一赢家。旧字符串路径 dormant 仍保持原行为。
- 实际中间 index 插入只发布前驱前缀且 `insertion_at_tail=false`，保原 prefix/后续 Assistant；未知前驱不 mint UID、不改变旧 prefix；观察异常仍真插入/consumed，无 fake source。
- 最终 Steer receipt 仍 `complete=false`，独立 source facts 为 true，source UID/row 按顺序逐项等真实 DB；旧完全 receipt 的地址/complete 不变。压缩、未 flush marker、重排 prefix、重定向 user cursor、缺 anchor/stale transcript 反例保持 false/缺凭据。
- 最后 Ruff 7文件通过；`.venv/bin/python scripts/check --only health --base HEAD` 对7文件、基线494de9a739f6：0 blocking/0 advisory；`git diff --check` 通过。检查各两次，第二次因异常隔离源码变化；未运行 full suite/build/大型门禁。

### 5. 缺口与边界

- 没有自行重启服务/改 profile/DB/commit/模型实测，当前 53445/5173 未保证加载新源；Main 在稳定窗口统一核对。
- 本 owner **不声明**真正浏览器 immediate bubble/涨入、连续 Send 位置、Framework 更新后无重复、replay 截断或真实 DeepSeek 流式已闭合；由前端 owner 集成和 Main 实测。
- source 没有直接把每个 delta 标上 durable UID；它提供原生 ordered 索引和准确边界，前端不能把它误读成按正文任意配对或任意清 stream 的许可。压缩边界 false 不能整体 retire。
- 未验证跨平台/完整 callback 组合；沿任务受影响正式入口及既有证据复用。不改 V1.6 Notebook/Noting/Framework ownership。

### 6. 接口影响

`events.py` 的 source 类型与 `pending.py` 的真实消息类型都是既有事件的 **optional** 增量；followup accepted 原 event 仍 `{turn_id,pending_ids,message_uid:null}`，旧 sender 不需新字段。关闭/旧字符串路径无执行语义改变，新的 metadata 不送模型、不改历史/工具 Schema。合同生成文件未修改，需 Main 统一 `scripts/gen_gateway_contracts.py`；生成一致性测试在此前不应冒称通过。

### 7. 建议后续动作

Main 亲读7文件变更及原生插入/flush/callback 上下游 → 统一生成合同 → 前端按 source owner 原子交接并保未知 → review后统一稳定服务版本 → 真浏览器连续 Turn、工具后批量 Steer、Framework 更新、压缩 false 边界及真实 DeepSeek 流式复验。保持 C58 停 Verification 前。无需重跑 BE-PENDING109、BE-SUBMIT旧大包或整套 V1.6；如字段接线变化只定向补受影响例。

最终源 SHA256（HEAD494de9a＋本工作区；不是新 commit）：

| 文件 | SHA256 |
|---|---|
| `agent/pending_steer.py` | `ee0df2b7229f33deb647413f3d1fea06fe8c8eacad0b260e1633cf99f1cf6dec` |
| `tui_gateway/prompt_turn.py` | `c77e62972bdfad55436b2629158ad20d1d02617c047afbce98605cea5e5b5feb` |
| `tui_gateway/contracts/pending.py` | `13ba6a7e815c6838bf22dd614ab7b1092e55098ae557d7408dca61cbb4289324` |
| `tui_gateway/contracts/events.py` | `143da864d882cae28ec10ae2c8a39ca84d5b69289612a45c3a8547be59b130bc` |
| `tests/agent/test_pending_steer.py` | `896856bd4587e712b55f1ea9ef69b1e858ca970ce322cd2511060b6a7de8fb03` |
| `tests/tui_gateway/test_pending_native_turn.py` | `55e9d569e00a421dcbb9df206fbd64139ec89e244603fb1d67ae2e4c67c010e3` |
| `tests/tui_gateway/test_submit_time_user_row.py` | `69be89df7fdbbbb82a0151b7c555220f4bd64852621a6eab26762884b77465e3` |

## R06 追加：原生重启后同 Gateway owner 更新 bootstrap 令牌

2026-10-13 后续明确派遣。原生七文件已由 Main review/集成于 `4443aa7`（含生成合同），本次没有再改后端源。Main 实际 stop/start53445 后 test tab12仍保有草稿/历史但 disconnected；原 Gateway retry 一直使用页面启动时的旧令牌，原生 token 轮换后认证拒绝。此为 Main 实况输入，本 owner 未自行操作浏览器或服务。

### 七项交回

1. **对应条款**：R06、用户已授权断连保会话/历史/草稿、可编辑及自动恢复；沿同源原生 bootstrap 和已有 `/api/ws` 认证，不新建 API、不绕过认证、不通过 reload恢复。
2. **实际变更**：仅前端 `src/api/client.ts` 与新 `src/api/client.test.ts`。首次 connect 复用已注入 bootstrap；连接结束后标记 fresh，重连通过同源 `fetch('/')`，`credentials=same-origin/cache=no-store/redirect=error`，DOMParser读取 inline script 中精确 `window.__HERMES_SESSION_TOKEN__=<JSON字符串>;`。仅接受一个非空字符串 literal，不执行 HTML/JS/eval、不打印/保存令牌。成功且仍为当前尝试才更新现有 window 内存值，使原 REST/auth header同步当前token。
3. **正式路径/机制**：`Gateway.connect → openConnection → freshBootstrapToken → existing /api/ws → gateway.ready`。同 owner 共用一个 connect Promise；每尝试持有 abort、20秒包含bootstrap/handshake超时、socket/heartbeat。唯一 `endConnection` 清理当前尝试、reject未完成connect、将在途RPC结论保持 Indeterminate，1.5秒原节奏重试；stop取消fetch/timeout/socket/retry。旧socket和晚fetch回包按真实 attempt owner拒绝，不能关闭新连接/覆写token/建重复socket。不清Controller历史/草稿/listeners、不盲重发原prompt。
4. **验证结果**：`npm test -- src/api/client.test.ts`，Vitest4.1.11，7/7通过，463ms（测试20ms）；7场景为首次bootstrap+singleflight、原生重启token/REST/listener/不重发unknown prompt/旧socket反例、bootstrapHTTP失败继续重试、不接受表达式/多赋值且script不执行、stop中止refresh并结算connect/晚回包、hang20秒后可恢复单尝试、未open socket的stop/error/close不重复重试。FakeWebSocket/fetch作为外部依赖，实际 `Gateway` 生产实现运行，非镜像实现。仅这两个文件定向`tsc --noEmit --target ES2022 --module ESNext --moduleResolution Bundler --lib ES2022,DOM,DOM.Iterable --strict --skipLibCheck src/env.d.ts src/api/client.ts src/api/client.test.ts`通过，`git diff --check`通过；未fulltest/build。
5. **缺口**：未操作主用户tab9或测试tab12，未重启/commit/model/后端源修改。真实IAB保页、原生token轮换后自动恢复、draft/history保留需Main复验；测试只证明Gateway传输/认证恢复与unknown不重发，不冒称完整Controller/UI通过。
6. **接口影响**：公开 `Gateway/rest/scoped`调用入口不变，令牌仅已有window内存位置，不新增缓存/存储/registry。Main提示当前HMR保留旧Gateway instance，class新prototype需由Main/flow owner在已有controller HMR接缝更新；本owner未触碰controller或为了HMR新建全局owner。Main可在独立testtab第一次reload加载新client，后续原生重启观察必须无需reload；主tab不刷新。
7. **建议后续**：Main亲读两个文件/原nativebootstrap精确赋值并按既有HMR接缝集成 → 独立测试页加载新client → 同Gateway owner真实断开/重连证明fresh native token、状态与草稿保留 → 本地阶段交接，继续停Verification前。已有controller断连保状态证据复用，不无差别重跑核心包。

| 文件（前端HEAD21aad02＋合法未提交工作区） | SHA256 |
|---|---|
| `src/api/client.ts` | `45224b1a85110fe222037c6e32a4327274fa733451bacf9b5ab7a49fb7921bb4` |
| `src/api/client.test.ts` | `9f505b9cbd90af2d73f559201821f523ef7155bbc195642cc127b511fd2bc967` |

## Main 接收（2026-10-13）

Main集中读取七文件差异、实际append/flush/callback上下游与报告/反例，接收owner12distinct与Ruff/health结果。新增metadata只在正式观察路径读取，不改变原native insertion/consume/complete判据；未知边界保留unknown。合同生成后生成一致性1pass，catalog既有review.summary孤立事件1fail保留，未改规则。九文件原生产品快照提交4443aa7；运行前确认Main/压缩/Noting均idle，真实停止旧服务时IAB保Conversations/history/草稿、可继续编辑、Send禁用、仅Composer持续提示，随后按同profile/runtime启动新服务。重连与新真实Turn证据尚待补。

## Main 最终集成接收

2026-10-13：Main集中亲审正式路径与改动并接收相应owner证据，最终前端c55120f、visual fc18614、原生产品4443aa7。用户自测整改的实际关闭范围、测试失败/修复留痕、真实DeepSeek/IAB及未验证边界统一见final-delivery「当前整改关闭证据」和根CLAUDE；本报告上方“待实测”是交回时观察，不覆盖该最新接收。最终冻结前端health0/0及build/types通过；两独立门禁未执行，不称整轮验收。
