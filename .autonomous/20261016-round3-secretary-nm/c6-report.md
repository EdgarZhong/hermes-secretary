# C6 Scheduler 投递交回（2026-10-17）

状态：**本域实现与开发证据已交回，等待主会话 review 和 C9 正式 caller 接线。未提交、未 stage、未建分支、未启动模型。** 个人 Provider 线自上次交回后保持停写。

## 1. 条款

- 冻结 d19018 白板 A3/A7/K1–K5/N5；07 §0–3／§6–7／§8.6／§8.9／§8.14：独立 Scheduler、当前定义接纳、SCHEDULED ATTENTION、instant／busy deferred、24h 最终投递 notice。
- 继承02 §3.9–3.12／§5.6和04 §5.3的 owner、lease、原生 ingress、单 durable batch carrier、真实请求携带且成功响应 ACK、失败重试与原生 timestamp；不继承 Notebook ownership／类型／local开关联动。

## 2. 实际变更

- `secretary/reminders.py`：去掉 Notebook 当前条目和 local Noting gate；使用 C3 精确 generation／sequence／lease 重验；atomic busy→pending消费C3现成事务；英文正文；最终 instant notice；durable witness 改为证明原生 row＋既有 receipt，不依赖今天的可变排期。新增 instant prepare 回调，仅在 native txn 更新 private batch，commit 后才同步 live。
- `secretary/reminder_request.py`：prepare 只估压力；真正 native append 的 prepare_rows 内重读 pending／当前定义，剔除撤销项、刷新内容及投递方式，单条批量 carrier 同事务绑定全部真实 occurrences。失败不发布 live；丢失提交返回／重开DB后复用已绑定 carrier，不重复新建。压缩 pass 不materialize；已compact退休的carrier沿原机制terminated。ACK需两阶段实际携带证明和成功响应标记，按实际True结果计数。Scheduler关闭只阻新接纳，已admit的carrier仍可ACK。
- `secretary/schedules.py`：default_enablement直接使用C4 `scheduler_settings_for_db(db)`，去除重复parser，保留profile。
- **主会话显式扩权** `hermes_state_messages.py::append_messages_batch`：新增可选 prepare_rows 原生事务接缝；不传时原生执行分支不变，保持guard／repair／insert／counter／snapshot责任。没有复制原生插入器、另建队列、锁或数据库。与C9-H的archive_and_compact分工不重叠。
- `tests/secretary/test_r3_delivery.py`：新增30个独立参数化场景；真实SessionDB／Scheduler／native append及CLI现有admission入口，受控响应／时钟／故障。
- `secretary/cli_reminders.py`、C3 schedule sibling／Schema、既有测试均未修改：其现有CLI lane直接持完整claim，已消费本包新机制。

## 3. 正式路径

`due scan / C3 claim` → `queue_pending_for_claim / native instant admission` → `prepare_pending_reminders` → native `append_messages_batch(prepare_rows, before_commit)` → native durable carrier＋C3 receipt bind → COMMIT后live publication → 实际provider request `verify_carried_reminders` → 成功非空response接缝 `acknowledge_carried_reminders`。

instant沿已有 `CLISecretaryClaim → dispatch_cli_reminder_input` 或Gateway现有slot gate；busy同事务转pending，不额外排未来Turn。正文含每项Schedule／Due／Delivery／Content和07完整授权提醒；原instant混批只附一次notice，纯deferred不读coverage。Due为原发生时间，instant timestamp为实际进入时间，deferred无timestamp marker。

## 4. 证据

日志与manifest：`.hermes-dev/round3-local-20261017-l0/L-B/c6/`。版本锚点C3已接4022c5b、C4已接723343c60f；共享最新HEAD、5文件hash和证据目录见 `manifest.json`。全域补丁（含untracked测试）见 `c6-review.patch`。

统一命令前缀 `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh`；PM Python3.14.7／macOS arm64／runner临时隔离，无真实服务或模型。没有大套或别的owner用例。

| 执行 | 结果／耗时 | 日志 |
|---|---|---|
| `tests/secretary/test_r3_scheduler.py` 首次全模块 | 47通过，1.1s | scheduler-initial.log |
| `tests/secretary/test_r3_delivery.py` 首次全模块 | 28通过，2.4s | delivery-initial.log |
| Delivery `-k 'disabled or materialized or response'` | 6通过，0.8s；新增disabled后已接纳carrier ACK＋受影响边界 | disable-repair.log |
| Scheduler `-k 'configuration or disabled_scanner'` | 8通过，0.4s；C4统一parser后 | scheduler-config-final.log |
| Delivery `-k 'lost_commit or native_prepare'` | 4通过，0.8s；重开DB恢复、native事务自动retry／guard顺序／rollback／opt-in原生路径 | native-callback-final.log |
| 指定5文件Ruff | 通过 | ruff.log |
| 冻结官方Measurer／compare，仅本包5路径对723343c基线 | 0 blocking／0 advisory，0.8s | health-final.log、health-scope.py |
| 本包git diff --check | 通过 | 命令输出 |

最终本域独立测试覆盖C3 47＋C6 30=77项；不是声称某次单命令运行77项。只在新修复后定向补测。native文件原2000行上限，通过同方法内表达折行收敛保持2000行，未改门禁。

已验证：Noting global/local off下排期正常；claim/prepare后pause/delete/reschedule无落库；内容/模式修改后只用当前正文；carrier先提交后的在途标记与晚ACK不复活定义；两项batch一条durable row且逐项ACK；无carriage／失败响应不ACK；bind失败完全rollback；unknown COMMIT重开DB后复用同UID；compaction fence／退休；原instant final notice在实际表变更后重算、混批仅一次、纯deferred无coverage入口、unknown诚实投递；instant stale witness拒绝；CLI busy不排新Turn／idle走既有lane；prepare_rows原生guard后执行、真实SQLite busy自动retry幂等、chunk拒绝、无callback原行为。

## 5. 缺口与边界

- **C9未接线，不能宣称最终产品已完成。** 下面caller表是必接清单，不是孤立helper验收代替正式产品。
- `agent/turn_api_call.py` 两处 `answer is not None` 会把 `{}` 等空返回标为responded，C9-H需改为非空成功证据；本包只能消费该受信flag，不窥探SDK/provider细节。
- 旧测试明确需C10收口：`tests/secretary/test_cli_reminders.py`、`test_active_reminder_persistence.py`、`test_active_reminder_admission.py`、共享`reminder_runtime.py`依赖已退出schedule_sync_conn／Notebook user_reminder／local-off冻结／旧正文。未修改、未运行、未加skip／旧alias。
- 运行时正在由C7／C9改版；真实模型／完整host入口留唯一owner在round3隔离profile验证，本包无模型或额外profile。
- 无真实网络、NM、部署、用户状态修改。代码没有改Scheduler/Notebook数据归属，不自动建后续排期。

## 6. 精确接口、事务与C9替换表

| 正式caller | 必要替换／保留 |
|---|---|
| `agent/session_persistence.py::_db_flush_write`（C9-S） | 引入 `active_delivery_prepare_callback(db,batch_msgs,batch_rows)`；与现有 `active_delivery_batch_callback` 一并构造；`append_messages_batch(...prepare_rows=prepare, before_commit=callback)`（None可省略）；保持COMMIT成功后既有 `confirm_active_delivery_batch(batch_msgs)`，再sync_flushed_message_markers。prepare仅改batch row／process witness，confirm才把最终TrustedUserInput同步live；失败不得调用confirm。 |
| `gateway/secretary_reminders.py::_prime_owner_runtime`（C9-S） | 保留真实Main、当前route/profile、已有cache／cold runtime资格；排期设置改C4 scheduler_settings_for_db，去掉noting enabled／notebook_local_enabled阻断，不把Scheduler关连到Noting。 |
| `_deliver_active_claim` metadata、`_event_claim`、`convert_busy_reminder_event`（C9-S） | 在原claim的owner/schedule_id/token/next_run_at之外贯穿 `generation`、`sequence`。`schedule_current_claim_conn`必须同时比较这些，缺字段会失败关闭；不能只持token来重新解释新定义。 |
| Gateway旧独立due tick入口／CLI既有REPL与busy monitor（C9） | 扫描调用C3 `scan_and_claim_due(...is_enabled=default_enablement(db))`；native busy调用convert_claim_to_pending，idle调用admit_active_reminder。不加新Main gate／未来Turn队列。CLI现有直接传完整claim已正确。 |
| `agent/turn_request_assembly.py`／`agent/turn_api_call.py`（C9-H） | 保持prepare在compaction判定前、materialize在build_api_messages前；最终传输kwargs再次verify；仅非空成功response之后ACK。prepare与materialize不得被Noting gate包住。 |

`append_messages_batch(..., *, before_commit=None, prepare_rows=None)`：真实native guard之后、repair/insert之前调用 `prepare_rows(conn, session_id, messages)`，原位改私有list，返回值忽略；可清空list进行零insert，开头原本空list仍原生直接返回0；任一callback与chunk_rows同用报ValueError。回调可能随SQLite重试重复执行，必须幂等、不自行commit、不修改live。C6无有效项抛内部_NoPendingReminders使事务rollback；成功后才publish。C8另消费该通用接缝，本包没改Framework。

`active_delivery_prepare_callback(db,batch_msgs,batch_rows)->callable|None` 和既有 `active_delivery_batch_callback(...)`：同一对batch/live在同一native事务建立正文与receipt；`confirm_active_delivery_batch(batch_msgs)`仅成功COMMIT后。`ActiveReminderAdmission.durable`复核native row与持久receipt，pause/delete后仍有效，不用可变registry复原过期定义。

`prepare_pending_reminders(agent,messages)->rough_tokens`；`materialize_pending_reminders(agent,messages)->occurrence_count`；`verify_carried_reminders(agent,actual_api_messages)->bool`；`acknowledge_carried_reminders(agent)->actual_ack_count`。ACK要求 `_secretary_reminder_carriage_verified` 与 `_secretary_reminder_provider_responded`；prepare每次清旧flag，carrier构造不授ACK。owner由db/session只读binding证明，无模型参数。

锁顺序：native持有 `_session_persist_lock` → flush既有tail → DB native写事务／guard → prepare/read/render → insert → bind → COMMIT → 同persist lock发布live。C3 CRUD使用同DB写锁，control先提交则旧witness失效，carrier先提交则在途，不另加锁。所有配置、时间和后台调用绑定所属db profile。

## 7. 下一步

主会话亲自review上述5文件＋新测试；C9-S接 caller表，C9-H接真实成功response／request顺序；以后仅按新增接线取得定向证据，不重跑本包有效77项。C10更新指定旧测试。最终跨模块／模型／独立门禁仍由主会话统一安排。
