# C9-H 正式 host 生命周期接线交回

状态：本域 Development、定向证据与自审完成，待主会话亲自 review；停止写入。无 stage、commit、分支切换或再派生；未调用真实模型、NM 或启动产品服务。本报告不宣称 C9-S、C10、真实运行或独立门禁完成。

## 1. 条款与实现机制

权威规格：冻结 `d19018a7ba3e38ae01f76aa57821b55cbc15ff58`；07 §0–3、§4.5、§7、§8.1–2/8.11–13、§9.1/9.3、§11 至末尾；白板 N0–N6/P1–P5/D6–D8。继承 02 §4.6–4.9/5.1–5.5/5.10–5.11 的原生资源、测量、完整前缀与提交，以及 04 §4.4–4.7 的 D01/持久 child/五 Turn；06 仅原生客户端边界。个人 PHASE3 仅提供通用 completed/failed 语义，公开实现没有个人或 NM 依赖。

- 普通 manual/auto 在实际 native summary 接缝统一调用 C7 `prepare_joint_noting`，在父 Active 改写前同步 freeze/admit/spawn，随后原生摘要与提交继续，不等 child。Noting 关闭、拒绝、freeze/spawn 错误均不取消原生压缩。
- Idle 的既有 parent native request 使用内部 `noting_joint_idle` 标记；此路径已在 C7 prepare 一次，共同 hook 不重复 spawn。不保留退出的 child compact 工具或旧 trigger alias。
- 原生成功发布事务将真正新 summary 的 UID 交给 C7 interval owner。同一个 SQLite write transaction 同时发布 in-place/rotation transcript 和新的压缩区间；另一连接的 Force admission 只能在事务发布后读到新区间。receipt、失败、no-op 不更新区间。
- 关闭或无资格的原生会话不新建 Noting interval 状态；已有 interval 则继续观察真实成功 native 进展，保证重新开启后不沿用旧 Force 占用。native 写入异常和返回行为保持原样；Secretary 观察异常仅记录日志，不能把它变成原生失败。
- 两条 provider 调用路径使用现有 transport 的 response shape 校验和 normalization：非空白文本或至少一个有名称的非空工具调用，才确立成功响应事实；工具参数是否有效由原生后续执行处理，不影响模型已经收到载体的事实。`None`、`{}`、空白、空壳工具调用、failed/cancelled/error 状态和传输异常不确认 Reminder。最终 kwargs 的 carriage 校验与 C6 durable ACK 继续共用原入口。
- 通用 external-memory sync 仅在 `completed && !failed && !interrupted` 且正文非空时执行 sync 与 queue；finalizer 和既有 External runtime caller 传真实完成状态，没有 NM 特判。

## 2. 准确变更白名单

共 8 个生产文件、2 个旧测试文件，新增 1 个测试文件。

| 文件 | 本域变更 |
|---|---|
| `agent/context_compaction_request.py` | 共同 pre-summary helper；Idle 内部 trigger 更换 |
| `agent/conversation_compression.py` | native summary 与既有 External compact 实际派发前调用同一 helper；传播内部 trigger |
| `hermes_state_compression.py` | `_noting_compaction_write` 事务内观察 helper，接 `publish_compression_child` |
| `hermes_state_messages.py` | 仅获批 `archive_and_compact` 窄符号，局部 apply_patch 包装实际 write transaction；未碰 C6 `append_messages_batch` |
| `agent/turn_api_call.py` | 两路 provider 成功非空响应判定，保留实际 final-kwargs verify 与 ACK 位置 |
| `run_agent.py` | 仅 `_sync_external_memory_for_turn` 增加 completed/failed 参数与统一 gate |
| `agent/turn_finalizer.py` | 既有 sync 调用传真实 completed/failed |
| `agent/codex_runtime.py` | 获批既有 `_finish_codex_turn` sync 调用传真实 completed/failed；执行和路由不改 |
| `tests/agent/test_context_compaction_request.py` | 离线模型元数据/child I/O 夹具，现行内部 trigger；保留原生租约、提交、跨会话请求测试 |
| `tests/agent/test_web_compaction_control.py` | 嵌套配置、父 request 接口、现行 Snapshot termination/result；保留取消/timeout/竞态断言 |
| `tests/secretary/test_r3_host_wiring.py` | 新增 45 个参数展开场景，覆盖以下正式路径 |

原白名单中的 `turn_context.py`、`turn_preflight.py`、`conversation_compression_manual.py`、`tui_gateway/session_compression.py` 无需修改：原调用均汇聚公共 native 压缩接缝，避免多处 spawn。只读核对 `turn_request_assembly.py` 与 `conversation_loop.py` 后，确认 prepare/materialize/build/verify 顺序已有正式接线，无需新增变更。

`conversation_compression.py` 仍为 4498 行，与当前 HEAD 相同；`hermes_state_messages.py` 仍为 2000 行，与当前 HEAD 相同。仅压缩原有重复说明抵消所需接缝，不调整规则/阈值/豁免。

## 3. 正式 caller 路径证据

| 真实路径 | 证据与边界 |
|---|---|
| `compress_now → AIAgent._compress_context → _run_summary_phase → prepare_joint_noting → spawn_noting_task` | manual/auto × in-place/rotation 共 4 场景；保留真实 compressor、数据库、lease、native publish，仅摘要模型 I/O 与 child runner I/O 受控；冻结完整 prefix，单次 spawn |
| `C7 prepare idle → parent native compact(trigger=noting_joint_idle)` | Idle 双条件接纳后，实际 native pipeline 无第二次 freeze/spawn |
| `_run_summary_phase → _commit_compaction → archive_and_compact / publish_compression_child → _noting_compaction_write` | 从真实 Full 读新 boundary；事务内 hook 暂停时另一连接提交 Force，与证明覆盖/水位两支分别竞争，接纳看到实际新 UID |
| Noting off / child freeze 失败 / External D01 / native off | 前三者 native 继续；External 零 admission/child 且保留 suppression；native off 通过真实 `run_conversation` 不自动压缩或启动整理 |
| Force 通知与失败/no-op | 真实 Force admission 后实际成功 compact 才从 Active 退休，原数据库记录仍在；摘要失败、数据库发布失败、no-op 均保留原占用和通知，不假报成功 boundary |
| `Schedule claim → queue_pending_for_claim → run_conversation → assemble_api_request → native summary → materialize → provider final kwargs → ACK` | 真实 Schedule、pending、carrier、原生 append 与正式 loop；Noting 关闭时仍投递。断言 prepare 在摘要前，carrier 在摘要后落地；middleware 从最终 kwargs 移除 carrier 后，非空成功响应也不 ACK |
| `perform_api_call → streaming/nonstreaming provider → response gate → acknowledge_carried_reminders` | 20 个输出矩阵场景加传输失败；坏参数的具名工具响应仍 ACK，完全空壳不 ACK。I/O 受控，保留 native middleware/relay/normalizer。无实际 carrier 的矩阵只验证 ACK 调用 gate，上一行提供 durable ACK 端到端证据 |
| `finalize_turn → _sync_external_memory_for_turn` | 成功、failed 非空解释、interrupted 非空输出、预算耗尽未完成四分支；真实通用 helper + memory manager I/O spy；仅成功归档与预取 |
| 既有 External `_finish_codex_turn → _sync_external_memory_for_turn` | 成功/中断/error 三分支；通用 sync 真 flags；未启动 App Server 或改 provider 路由 |

## 4. 测试、命令与有效证据版本

环境：macOS arm64，官方 PM `.venv` Python 3.14.7；canonical runner 临时隔离 HOME/HERMES_HOME，无真实模型/NM。所有命令均以前缀执行：

```bash
HERMES_PYTHON="$PWD/.venv/bin/python" HERMES_TEST_FILE_RETRIES=0 scripts/run_tests.sh
```

**112 个独立场景均已有有效 PASS 证据**：新 host 45，旧 native request 36、Web compression control 19、memory sync 2、finalizer 10。主会话 review 后仅 provider response gate 改动，受影响矩阵与实际 carrier 路径已定向复测；其他未改机制证据复用，没有重复跑全量或 C1–C8 套件。

| 日志 | 精确 runner 参数（省略上述前缀） | 结果/耗时 |
|---|---|---|
| `first-tests.log` | `tests/secretary/test_r3_host_wiring.py tests/agent/test_memory_sync_interrupted.py tests/agent/test_turn_finalizer_final_response_persistence.py -q` | 旧归档 12 PASS，新 host 4 PASS/29 setup ERROR；12.2 秒。离线 guard 拦住初始化模型 metadata 探测，修正夹具。runner summary 把 setup errors 汇总成 0 failed，不能把该次当通过 |
| `second-tests.log` | `tests/secretary/test_r3_host_wiring.py tests/agent/test_context_compaction_request.py tests/agent/test_web_compaction_control.py -q` | 新 host 33 PASS、request 36 PASS、Web 6 PASS/13 FAIL；21.9 秒。Web 失败为旧 Snapshot 审计元数据/type |
| `third-tests.log` | `tests/secretary/test_r3_host_wiring.py tests/agent/test_web_compaction_control.py -q` | 53 PASS/4 FAIL；8.6 秒。Web 18 PASS/1 FAIL（旧 dict/string result 断言）；host 35 PASS/3 FAIL（新夹具缺 session_id、native off 必须从正式决策入口验证、DB 失败注入符号修正） |
| `failure-repair-tests.log` | `tests/secretary/test_r3_host_wiring.py tests/agent/test_web_compaction_control.py -q -k 'existing_external_runtime_sync or native_disabled or native_db_failure or snapshot_survives_cancellation'` | 5 PASS/1 FAIL；1.7 秒。余下 DB 失败测试应断言 native 保留原 transcript，不能要求既有 native 吞错路径抛异常 |
| `loop-tests.log` | `tests/secretary/test_r3_host_wiring.py -q -k 'native_db_failure or real_loop'` | 3 PASS；2.0 秒，修正 DB failure 断言并新增两个真实 loop/carriage 场景 |
| `notice-tests.log` | `tests/secretary/test_r3_host_wiring.py -q -k 'actual_native_commit or external_fact'` | 3 PASS；1.5 秒，新增 Force 成功/no-op、External 正式 manual 路径 |
| `response-review-tests.log` | `tests/secretary/test_r3_host_wiring.py -q -k 'formal_provider_call or provider_transport_failure or real_loop'` | 23 PASS；8.9 秒。主会话 review 纠正 ACK 判据后：坏参数但具名的实际工具响应算成功，参数业务校验交原生；新增两路空壳工具负例，20 个矩阵＋传输失败＋两个实际 carrier 场景定向复测；本次两个变更文件 Ruff、health 0/0 |

独占旧归档两文件只运行一次，未修改。没有 direct pytest、skip/xfail、旧配置执行 alias 或放宽失败断言；所有退出假设均替换为已冻结契约。

本域 11 文件 Ruff PASS；官方未修改的 `scripts.code_health` Measurer/compare/apply_allows/verdict 引擎限定上述文件对 HEAD 做增量检查：**0 blocking、0 advisory**。新增测试后复检一次；`git diff --check` PASS。没有 stage，未用空 `--staged` 检查冒充验证。

证据目录：`.hermes-dev/round3-local-20261017-l0/L-C/c9-host/`；含全部测试日志、`ruff.log`、`health-final.log`、`manifest.json` 和 `c9-host.patch`。最终取证 HEAD `e200936b5c8f93e33f51625fd0b397a1d826a55f`；任务初始允许基线为 `ba6266f314dbeddc01a4066110ed5138df683efd`，期间主会话集成 C5/C7/C6。**本域实现仍为未提交 patch**，manifest 固定 11 文件 SHA256、依赖 SHA256、patch SHA256、命令和日志哈希，不能将 HEAD 单独冒称已包含 C9-H。

## 5. 精确接口与事务时机

```python
prepare_noting_for_native_compression(agent, messages, *, trigger=None,
                                     force=False, verbatim_tail=None) -> None
_noting_compaction_write(db, conn, session_id, messages, write,
                        *, owner_session_id=None) -> native_write_result
AIAgent._sync_external_memory_for_turn(
    self, *, original_user_message, final_response, interrupted,
    messages=None, completed=True, failed=False) -> None
```

- pre-summary helper 仅消费 native 已确定的实际 Active；partial manual 拼回 head+verbatim tail 后交 C7 freeze；普通 trigger 按 force 区分 manual/auto，内部 `noting_joint_idle` 是已准备标记。异常只日志，不阻断 native。无第二队列/调度器/token 估算。
- `_noting_compaction_write` 由既有 `_execute_transcript_write` 传入同一个 write connection，在 native 写入前只检测 incoming 是否存在真正新 summary，在实际 write 成功后读取真实 Full boundary、调用 `db.noting_record_compaction_conn(conn, ref)`，最后由原生 owner COMMIT。rotation 用 parent row 做资格检查、child session 解析同 Conversation；不采纳 receipt/model 提供的边界宣称。
- native `write()` 异常原样传播给原生外层；外层保留其原有错误处理/原 transcript 回退。Secretary 观察异常不能回滚成功 native。普通 transcript重写、携带已有 summary、no-op 都不据此创建新 boundary。
- sync 可选参数保留旧直接 caller 兼容；正式 finalizer 显式传真实 completed/failed，既有 External caller 用真实 interrupted/error。没有用“有展示文字”代替完成条件。
- provider response gate 为模块内 helper；现有 transport normalize/validate 是唯一解析源，不新增 provider hierarchy。C6 `verify_carried_reminders` 的真实 final kwargs 结果与本 gate 必须同时成立才 ACK。

## 6. 缺口与 C9-S/后续接缝

- C9-S 独占 toolsets/model_tools/noting_surface/dispatch、整批 finish guard、正式 hosts surface 和恢复边界；本包没有修改这些文件，也没有重复注册工具或启动第二 child。主会话需审查其与 C4 prompt flag/工具一致性证据。
- C6 `agent/session_persistence.py` caller、瞬时/延后投递原生 append 契约由其 owner 完成；本包仅消费并验证 actual loop 的 deferred carrier，不声称所有渠道、重启与 instant host 操作已全覆盖。
- 真实模型 prefix/cache、完整 Scheduler/Noting 多 host 实测、个人 Provider、统一大型门禁和独立 Verification/Validation 均无本包证据，由主会话统一安排。
- 后继 C10 配置/触发旧组准确清单已收到但**未执行/未修改**：`tests/secretary/test_noting_policy.py`、`test_noting_config_contract.py`、`test_noting_codex_receipt.py`、`test_noting_deadline_event.py`、`tests/hermes_state/test_secretary_noting.py`。不重跑 C7 runtime/timers/joint 三文件。

## 7. 交接与建议

主会话亲自 review 八个生产文件，特别核对两 DB publication 的同事务边界、共同 hook 的单次 freeze，以及失败 native 回退不改变既有行为；再按 manifest 接收未提交 patch。C9-S 继续其单写者文件，C10 收口上述旧组；已有 112 场景有效证据复用，仅集成实质改变相关接缝时定向复测。没有新增影响用户预期的自主规格收敛。
