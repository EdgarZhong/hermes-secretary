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

## R3-F11 / F12 本地真实发现修复补充（2026-10-17）

### 1. 依据与真实反证

d19018 白板实际 A7 为删除Memo、N5 为主动性归Main、N6 为保持冻结前缀；本包机制要求由07 §3（89–114）、§8.1–8.2（1237–1264）及04 §4.4/C13（265–291）、§4.6（317–356）明确。未继承双profile/child压父。真实证据摘要：`real-model/native-boundary-interval-miss.json`、`force-user-tail-prefix-observation.json`；只读请求 body/摘要，未输出headers、root或凭据，未触碰round3。

F11：原生in-place复用旧assistant UID形成新summary，原`_noting_compaction_write`以“UID全库未见过”判新边界，真实发布后interval仍conversation_start；重压同UID summary也不能前进。F12：父最后一条是user，原生live repair与发送副本user merge将noting-task并入该user，违反逐消息前缀。受控新增RED分别复现两类同UID不前进、finish/五Turn父user被改写（4 FAIL）。新增多模态反证还发现父当前user数组的timestamp块只在发送时存在，child历史重放丢该块。

### 2. 实际变更

- `hermes_state_compression.py::_noting_compaction_write`：写前保存目标session物理水位，原生write成功后只接受该session新插入、active、summary行，且它仍是当前合法路径的最新边界。排除同事务其他session、未发布/no-op；异常原生write照常回滚，观察保持fail-open。
- `hermes_state_secretary_noting.py`：从Full foreground合法节点导出不透明 `compaction:<session_id>:<physical_row_id>` interval，`boundary_message_uid`仍为逻辑UID。初次seed/成功record同一格式；同物理发布重记幂等，同UID再次发布新行则新interval。getter已登记后直接返回，不因rewind重置，Force占用随真正新边界释放。
- `secretary/noting_child.py` / `agent/cache_parity.py`：只给持久Noting child绑定冻结父前缀长度。live repair只处理child后缀；发送drop/merge分段调用原生函数，不能跨父/child边界。首请求、工具循环与五Turn续跑共用此边界，无假assistant、provider adapter、独立Loop或父root/tools修改。
- timestamp补充：freeze私有副本仅对父`_persist_user_message_idx`对应、Anchor以内的user数组，复用该消息**已有非空FreshUserTimestampMarker**与正式prepend helper物化实际发送块。不读取普通timestamp来补造时间；历史图片、无现成标记、索引不匹配均不补。已物化的可信Parts不重复。原消息字典未改，不给无content字段的消息补None。
- `agent/agent_runtime_helpers.py`仅repair与drop/merge两个窄接缝、`agent/turn_request_assembly.py`只调用上述已有cache owner。未绑定冻结边界时继续原调用参数、原repair与send行为。超长runtime helpers仍3837行，与基线相同；只重排两段原docstring换行，未删指导或规则。
- 两处`test_r3_host_wiring.py`及一个`test_secretary_noting.py`旧内部断言改为逻辑boundary UID＋opaque interval/旧占用变化，不恢复旧alias、不删可靠性保障。

### 3. 正式路径与原子性

in-place `archive_and_compact`、rotation `publish_compression_child`均进入同一原生transcript写事务，在native成功发布与COMMIT之间更新现有Secretary interval表。物理summary行、合法路径、目标session三者同时匹配；竞争admission仍由SQLite原生写锁串行看到新interval，失败无新占用释放。没有新schema或迁移。

F12正式`run_noting_task`→同一持久child→原生`run_conversation`→live repair→request assembly/provider。测试先让原生Parent真实发出受控请求，逐消息比较所有child实际请求的root、tools与完整父数组；不是源码断言或镜像拼装。允许合法完成Framework追加父尾，但原父前缀逐项不变；child durable只保存自有后缀，来源UID不重复入库。

### 4. 最终验证与耗时

本包最终有效 **62 PASS**：新独立文件20（F11同UID两轮×2、no-op/外session/rollback3、rewind1、rotation1；F12五种前缀×finish/五Turn10、无marker/错index2、原生默认repair/send1）；旧正式host边界10；旧state占用1；默认sanitizer20＋cache parity11。其余已有C1–C10证据复用，不跑全组或大型门禁。

| 本地日志（f11-f12/） | 结果 | runner wall秒 |
|---|---:|---:|
| red | 0P/4F；根因RED | 1.9 |
| green-first | 2P/2F；F11绿，测试旧写死root需改实际请求比较 | 2.2 |
| expanded | 3P/9F；实际多模态marker差异＋合法Framework/false字段夹具假设 | 4.6 |
| expanded-fixed | 13P | 4.4 |
| prefix-timestamp-final | 13P；新增历史图片/assistant尾/无marker/rotation | 6.5 |
| prefix-final | 最终受影响12个F12节点PASS | 7.5 |
| host-boundary-regression | 10P | 4.1 |
| state-boundary-regression | 1P | 0.7 |
| native-parity-regression | 31P | 85.3 |

共9次canonical runner调用，累计各runner wall 117.2秒（最后四组并行，该值不是端到端串行耗时）。改动/实际失败后定向复测；最后helper字典结构保留调整只重测12个F12节点，F11无关8个新节点复用已有效证据。长耗时来自旧cache-parity文件85.3秒，已过，不重复。

九路径锁定Ruff PASS，官方未改的Measurer/compare/apply_allows/verdict相对`4739b54896040be66c37c194d6b75dac2b675d97`为 **0 blocking / 0 advisory**，diff-check PASS（1.19秒）。最终固定实现前base的全范围十类门禁仍未执行；不据scoped结果宣称全项目绿。

### 5. 缺口与证据边界

本包无已知未关闭的受控机制失败。真实DeepSeek对user→user独立后缀的接受、真实Force首长user、再次压缩后新interval以及实际请求/cache观察，由c4唯一owner按原失败序列复测；本包没有真实模型结论。C10-T owner已另交`c10-t/f11-final.log`四个Force边界PASS（下一interval、in-place/rotation、no-op），本包未重复执行该文件/节点。F09/F10与最终regression-plan已归其他owner，未碰。

### 6. 文件与接口 manifest

九路径：`agent/agent_runtime_helpers.py`、`agent/cache_parity.py`、`agent/turn_request_assembly.py`、`hermes_state_compression.py`、`hermes_state_secretary_noting.py`、`secretary/noting_child.py`、新增`tests/secretary/test_r3_boundary_prefix_regression.py`、`tests/secretary/test_r3_host_wiring.py`、`tests/hermes_state/test_secretary_noting.py`。没有新的公开产品接口；原生drop/merge增加内部可选`preserve_prefix_count=0`，默认native签名参数使用保持；interval消费者必须视其为opaque，不再等同逻辑UID。

全部SHA256/锁指纹、版本、最终命令、精确node选择、运行次数与日志hash：`.hermes-dev/round3-local-20261017-l0/f11-f12/manifest.json`；已有源码diff为`final.patch`，新独立测试完整快照`new-test-source.py`；健康脚本/完整测量为`check_scoped.py`、`scoped-checks.json`、`checks.log`。HEAD只是集成背景，本包尚未提交，不把HEAD冒称已含修复。

### 7. 后续与停止

本包停止全部生产/测试写入，交主会话review/集成，随后c4定向真实复测F11/F12。没有stage/commit、派生、真实NM、round3操作或大型检查。最终回归静态准备已转c4，不再写该文档与目录。

## F12 review 回修：父 replay cleanup 只冻结一次

1. **条款与反证**：同04 C13／07 §3每次请求的完整父前缀合同。主会话指出`build_api_messages`在每个child Turn用child新clock清理整个父prefix。新增真实原生Parent→持久child反证证实：已合法清理的旧read-only interrupted历史及父本Turn刚返回的interrupted工具结果被再次删去，使静态长度越界；跨Turn/后台交接的新clock将父原请求合成确认文案改为EXPIRED。没有执行危险动作；read_file仅在正式`model_tools.handle_function_call`返回边界提供合成结果。

2. **相对上次review的变更**：仅`agent/cache_parity.py`、`agent/turn_context.py::build_api_messages`、`secretary/noting_child.py::freeze_parent_active_prefix`、同一新测试文件。首次同步freeze沿父现成`_persist_user_message_idx`切历史，复用现成`_current_turn_timestamp`只canonicalize历史一次，当前父Turn不提前清理；无现成clock不补造时间。原始索引在human_only过滤前保留，完成原生历史清理后再过滤，按清理后的长度绑定child边界。`FrozenParentPrefix`仅内部list结构副本标记，spawn→后台再次freeze只复制，不读取父已变化clock/index；普通list及该内部类型都仍逐条检查Anchor，提交gate未绕过。

3. **正式接缝**：native Parent `run_conversation`真实请求捕获→同步freeze→持久child runner→`build_api_messages`只canonicalize冻结边界后的child自有历史。未绑定时helper仍调用原`canonicalize_replay_history(messages[:split], now=now)+messages[split:]`等价路径，同clock/阈值，原生cleanup保持；没有全局关闭清理。原父live/durable、root/tools均不改；父实际已清理的历史不会被“原样保留坏历史”重新带回。

4. **新增验证**：`replay-red-native.log`4 FAIL为有效原生RED；`replay-green.log`四反例PASS，每个持久child五Turn逐请求比对完整实际父数组及tools，并确认父durable原文不改。`replay-prefix-regression.log`14 PASS＝前版受影响F12十二节点＋普通/内部类型不可绕Anchor两节点；`native-replay-regression.log`六PASS验证原生默认发送/恢复清理及60秒clock行为。未重跑F11/62全组、31项cache/sanitizer。原62按影响复用，加六个新边界和六个原生cleanup场景，最终有效覆盖 **74 PASS**。

| 本次日志 | 结果 | runner wall秒 |
|---|---:|---:|
| replay-red | 4F，stub误写到不存在的facade；非根因证据 | 1.5 |
| replay-red-native | 4F，有效RED | 3.1 |
| replay-green | 4P | 3.0 |
| replay-prefix-regression | 14P | 6.8 |
| native-replay-regression | 6P | 0.5 |

本次5次canonical runner，累计14.9秒；连同上次为14次/132.1秒各runner wall之和。四变化路径锁定Ruff PASS、冻结scoped health **0 blocking/0 advisory**、diff-check PASS，0.574秒。完整门禁仍未启动。

5. **缺口**：本次受控反例已关闭；真实DeepSeek接受与缓存命中仍由c4原owner复测，不把受控Loop当成真实模型结论。F11两个prod未再写，C10-T92项与其四Force节点不重复。

6. **最终hash与增量**：`f11-f12/manifest.json`的`replay_review.final_sha256`给出四个最终完整SHA256，`unchanged_f11`两项均true。相对上次review的完整四文件增量为`replay-review-delta.patch`（SHA256 `b705e9069fb8acf9c07cebf75532260a344ad5a7bb7fa0204731745ed1b9e0b6`）。已用初次base＋初次patch重建上次源文件并逐一核对所有旧manifest hash，不是凭当前HEAD推测增量。第一次review证据保留为`manifest-before-replay-review.json`、`before-replay-review.patch`、`before-replay-review-test.py`；最终全patch/新测试完整源已更新，检查为`replay_check_scoped.py`、`replay-scoped-checks.json`、`replay-checks.log`。

7. **停止**：四路径生产/测试已停止写入，无stage/commit、派生、round3/真实模型或大型检查。交root按独立增量一次review并集成，之后原真实owner按原失败序列复测。最终regression文档与目录仍归c4，本owner不再写。


## F12 review 追加回修：Anchor 早于当前未持久化 user

1. **条款与真实接缝**：沿用04 C13／07 §3每请求冻结父前缀合同。普通Main输入在`turn_context`先append user并登记索引，`run_turn_start_compaction`的preflight Force早于1229的正式user持久化；`reminders.persist_active_before_compaction`仅提前持久Active Reminder。正式admission从DB最新合法Full Foreground取Anchor，没有保证Anchor晚于当前user。故旧assistant Anchor合法，不能把截断后越界的current直接解释为原生“无current”。

2. **实际变更**：相对已review并集成的`eff3235f6bc1ee53b5d29b5210ad397024959df6`，仅改`agent/cache_parity.py`与`secretary/noting_child.py`窄freeze接口。内部helper新增必传`source_length`，先验证父current属于完整source，再以`min(current,len(truncated_prefix))`确定历史清理边界。完整source索引None／末尾／越界仍split0；FrozenParentPrefix后台handoff仍不重读父index/clock。没有改变admission、原生Loop、阈值或父live/durable。

3. **正式路径证据**：新增测试启用真实Parent preflight，控制原生测量返回140K、已解析window200K/auto150K；真实Force policy/admission/sync freeze全部执行。在正式worker调度边界延迟后台运行，断言DB头仍为旧Anchor、新user尚未入库。Parent实际provider请求将历史合成确认改为EXPIRED；旧实现child实际请求仍发原文，取得有效RED。修后在父已改index/clock时执行原worker，五Turn child每请求完整前缀均等于父实际请求截至Anchor，最终成功Snapshot。无真实危险动作，provider返回为受控依赖。

4. **验证与次数**：仅同一新独立测试文件新增四节点及受影响六节点。`anchor-red.log`初轮4F（旧Anchor一项为真实反证；三个无current项因取样停在transport清理前而比较了持久字段，非产品失败）；修正测试取样使用原生transport sanitizer后，`anchor-red-native.log`为**1F/3P**有效RED；生产窄修后`anchor-green.log`为**10P**（新增4＋原四replay模式及两Anchor身份节点）。三个无current反证覆盖None、完整source末尾和完整source越界，走原生`build_api_messages`＋transport清理与真实持久child请求对比。3次canonical runner，runner wall分别3.1／2.9／5.4秒，共11.4秒。既有74项证据按影响复用，新有效并集78；未复跑F11／C10-T／旧74全集。三变化路径Ruff PASS，冻结scoped health相对eff3235为**0 blocking/0 advisory**，diff-check PASS；完整十类门禁未启动。

5. **缺口**：本次正式preflight反例与无current／后台handoff边界均已关闭。真实DeepSeek复测仍由c4原owner执行；本包没有真实模型或cache命中结论。

6. **接口及manifest**：只新增内部`freeze_parent_replay_prefix(..., *, source_length, already_frozen=False)`参数，唯一正式freeze caller传完整source长度；公开产品接口不变。三路径最终hash、精确命令／选择器／日志hash／检查计时见ignored `f11-f12/manifest.json`的`anchor_review`；相对eff3235的完整三路径增量为`anchor-review-delta.patch`。上次manifest保存在`manifest-before-anchor-review.json`，避免覆盖上一轮review历史。

7. **停止与后续**：生产／测试停止写入，交root集中review／统一集成，再由c4按真实失败序列复测。不stage／commit，不派生、不操作round3、不写最终regression目录或启动大型检查。


## Verification V51：Notebook 时间只在可读输出投影为秒

1. **条款／原因**：冻结d19018的02 §5.6（1635–1637）要求所有面向人／模型的绝对时间为带时区秒精度，内部存储及计时精度不变；07 §4.1–4.5的条目时间／不可变版本／no-op／provenance，§8.10–8.13的提案、task/control及Framework；白板C4／T4／L2／N3继续区分真实证据年龄与处理时间。真实Store调用默认`_now`序列化机制产生微秒，正式maintain、working show、Main show、slash、Proposal、Framework及child控制正文原先直接暴露。有效RED为7 FAIL／1 PASS，没有更改内部clock来掩盖问题。

2. **实际变更／文件**：相对`323c64dacba1190c16bacc69bbe5e76db6f43529`，production仅`secretary/notebook_render.py`统一可读entry/state投影、`secretary/noting_tools.py`输出接缝、`hermes_cli/cli_secretary_commands.py`的Proposal payload。统一复用`hermes_time.format_timestamp`，只处理entry的created_at／updated_at／last_processed_at、fields内EVIDENCE_TIMES三字段及source_time_range起止；现成control current_time也经相同秒投影。保留null／未知、字段名、ID、关系、原始来源、自然语言description／time_context。没有改notebook_model._now、NotebookStore、public_state、原生时间helper、contract、hydrate、commit、source_basis、父prefix或旧History。

3. **正式路径**：真实SessionDB＋NotebookStore→notebook_maintain单条返回／notebook_work_show整视图；Store commit→Main notebook_show／共享notebook_command（CLI／TUI／Gateway复用）／propose_persistence_command。Framework既有noting_notifications.completion_body→render_notebook自动采用统一投影，真实publish_noting_completion在原生事务追加durable＋live同条完整Snapshot及超限Proposal；无需修改通知owner。真实原生Parent→持久child五Turn捕获实际provider请求，逐次检查初始及continuation control的完整working_notebook。provider返回受控文本，不执行真实模型或危险动作。

4. **验证／次数**：新增`tests/secretary/test_r3_notebook_time_projection.py`八节点：六正式输出、内部版本／no-op／真实合法及非法来源、原生五Turn控制消息。显式带微秒Store clock、证据时间及同秒内精确source范围；输出为秒而immutable DB版本、原始snapshot_state／Store.show／public_state／提交再hydrate仍保持全部微秒，重复无修改不新建版本或刷新时间。描述中形似微秒时间的原文完整保留，非空／null处理时刻及未知证据不补造。

| 日志（ignored v51/） | 实际结果 | runner wall秒 |
|---|---:|---:|
| red.log | 7F／1P，有效正式输出RED | 1.7 |
| green.log | 5P／3F；三项为新测试JSON键序／内部state与持久payload结构取样错误，非产品时间失败 | 1.6 |
| green-final.log | 新V51八项全部PASS | 1.6 |
| affected-regression.log | 4P／3F；C5 handler/control、C8严格字符阈值通过；三失败为旧F13人类ID断言 | 0.7 |
| legacy-targeted.log | 两renderer节点＋三个timezone节点，5P | 0.6 |

共5次canonical runner，runner wall累计6.2秒；最终有效并集**17 PASS**（新增8＋相关旧4＋维护旧5），没有为收口重跑已有效8／4。早先对话把相关旧4口述为5，现以原始日志更正。六路径最终Ruff PASS、冻结scoped health **0 blocking／0 advisory**、diff-check PASS（最终检查0.404秒）；未重跑78／C10-T或任何大型组／完整门禁。

5. **旧例处置／缺口**：获root追加授权，仅维护`test_notebook_render.py`两实际受影响节点：可读source范围改秒预期，仍比较所有非时间字段完整性／ID／排除audit／原始对象不变／每个时间原瞬间截到秒；`test_readable_times.py`仅第46行更新已集成F13的人类view隐藏snapshot ID，保留source ID、三个profile时区、History精确查询、durable原值全部断言。未改变其它旧测试或共享fixture。没有已知本包未关闭机制失败；不把17项或scoped checks称为独立Verification通过，Astra旧SHA发现及全新全范围复审由root组织。

6. **接口／证据manifest**：`readable_notebook_entry/state`只加可选profile_home，可读JSON的结构不变；秒投影不回流内部working state或commit。六路径SHA256、固定base、spec／锁hash、五次精确命令与日志hash、scoped测量在`.hermes-dev/round3-local-20261017-l0/v51/manifest.json`；`final.patch`包含新测试在内的完整最小六路径增量，`new-test-source.py`为新增测试完整快照。无凭据或真实用户运行数据。

7. **停止／建议后续**：本包六源码／测试路径已停止写入，报告追加不改旧证据。root集中review并统一提交后安排全新全范围Verification复审；已通过大回归按实际影响复用，失败修复仅定向补证。本owner无stage／commit、派生、round3真实模型、核心文档或其它并行owner文件修改。


## F17 真实human_only Anchor在冻结交接后消失

1. **条款与真实缺陷**：以公共production `d033c5057df419fb7d7122cba3085105dd13d89e`为起点（启动时HEAD fd5ec46仅文档），沿07 §3完整冻结父prefix、§8.1手动joint、§8.11–12持久child，04 §4.4 C13／§4.6每请求cache parity及02身份／Anchor／Foreground／失败关闭保留合同。真实V23恢复F16链的admission12 manual，Anchor为压缩前正式/notebook的assistant反馈row502；c4只读确认display_metadata.human_only=true、observed=0。同步freeze找到该UID后模型投影过滤了它；后台run_noting_task再次按可见UID查找而失败，无child Session。原证据v23/runtime/recovery-anchor-metadata.json及recovery-admission12-traceback.log；原实测未独立dump同步prefix，不能冒称已有该内存证据。

2. **原生RED与方案review**：新增真实Main `run_conversation`的provider返回边界，用正式secretary_feedback_messages构造并原生append human_only反馈，再调用manual prepare_joint_noting→真实spawn→原生context worker。只在worker进入点用Event阻挡后续执行，捕获实际同步freeze返回结构；明确父源含Anchor而模型prefix不含它。`red.log`3F／1P：human_only场景与真实同样failed／child_session_id null，普通Anchor场景完成五请求；另确认原标记对象能被重绑至prefix内另一UID、空模型投影未同步拒绝。root review后认可按绑定身份修复，未更改Anchor定义或把hidden正文注入模型。

3. **实际机制／文件**：production仅`agent/cache_parity.py`与`secretary/noting_child.py`。FrozenParentPrefix新增只读anchor_identity（Conversation Ref＋UID）；裸构造对象无绑定。首次freeze仍从完整原source逐条匹配Anchor、私有clone、按父原index／clock清理历史并做模型可见投影，非空成功后才绑定身份及durable标记。空投影同步抛NotingChildError并沿原failed admission／notice路径退出，不启动child。正式spawn与后台run显式传原admission.conversation_ref；已有准确类型且绑定的对象只比较完整原身份并结构复制，不扫描可见UID，不再读取父current/index/clock／变化消息。错ref或同prefix内另UID直接拒绝。未绑定子类即使覆盖属性声称身份仍走原source完整校验；兼容未显式ref的首次调用只可复用父已存在bound Ref，父无Ref时仅返回匿名结构副本，不能形成匿名可信handoff。原始传入list、commit gate、失败清理、provider/root/tools与原生未绑定路径没有放宽。

4. **最终定向验证**：`green-final.log`9P，包括human_only／普通Anchor×父同ref变化／切新ref四条真实manual spawn/background/native五Turn链；逐请求比对真实Main已发送的完整父数组与tools，禁止human_only文本泄露，同步与worker复制身份始终原admission。父同ref但context/root/tools/index/clock变化仍正常commit；父切ref后仍发原前缀、不重绑，但按现行owner gate abandoned、无Snapshot，释放运行资源。其余五项为同prefix另UID／跨ref拒绝、空可见prefix同步failclosed、未绑定子类不可伪装／只读元数据、旧匿名调用只结构复制。`shared-freeze-regression.log`11P＝F12四replay模式＋两marker身份＋正式preflight旧Anchor七项，C5多模态复制／缺Anchor及合法overflow／failed／interrupted资源释放四项；F12每次冻结前缀合同保持，不全跑旧78。

| 本包日志 | 结果及用途 | runner wall秒 |
|---|---|---:|
| red.log | 3F／1P，有效正式handoff RED | 2.6 |
| green.log | 3P／2F；首测试误强求切ref后仍commit，实际旧owner gate按合同abandoned，不冒称新产品缺陷 | 3.0 |
| green-final.log | 新九项全部PASS；root认可同ref正常commit／跨ref保gate的拆分 | 4.6 |
| shared-freeze-regression.log | 共享冻结／多模态／失败资源11P | 4.5 |

共4次canonical runner，wall累计14.7秒，最终定向有效并集**20 PASS**（新9＋共享11）。三变化路径Ruff PASS／冻结scoped health相对d033 **0 blocking／0 advisory**／diff-check PASS，0.564秒；未重复旧78、大型回归或已通过时间组。

5. **缺口与真实复证**：本次是实际F17失败后的确定性身份交接修复，不是概率重试，也不删除／重写原失败admission或占用。原生模型可见性仍过滤human_only；原DB隐私行保持。没有本包未关闭的受控机制失败；真实模型原合法chain由c4在root集成后复证一次，本owner不碰round3，不把受控API返回称真实DeepSeek成功。

6. **接口／manifest**：freeze_parent_active_prefix新增内部可选keyword conversation_ref；正式spawn与run传同一admission Ref，外部四工具、admission身份定义与Snapshot／pointer接口不变。旧F12测试源码未改。精确三路径最终SHA、base、四次命令／nodes／日志hash及scope测量见ignored `f17/manifest.json`；`final.patch`包含新增test_r3_frozen_anchor_handoff.py的完整三路径增量，`real-origin.json`只记录脱敏metadata及原证据hash，没有凭据或完整root正文。

7. **停止与后续**：三源码／测试路径已停止写入，交root集中review／commit后再由c4独占真实复证。无stage／commit、派生、round3／真实模型、其它production／规格／根docs／规则／依赖变更。独立Verification／Validation判定由主会话组织，20P不代替最终全范围复审。
