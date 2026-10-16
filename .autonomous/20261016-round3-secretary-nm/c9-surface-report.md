# C9-S 工具面、正式 dispatch 与投递 caller 交回

状态：本域 Development 与定向证据完成，待主会话亲自 review；停止本域源码与共享 fixture 写入。未 stage、commit、切分支或派生；未运行真实模型、NM 或产品服务。本报告不代替独立门禁。

## 1. 条款

冻结 `SPEC=d19018a7ba3e38ae01f76aa57821b55cbc15ff58`；起点 `92fddf82f280f79a73db8ecba5d454ae7a437e1a`。07 §0–3、§4.3–4.5、§5–7、§8.2–8.14、§9.1/9.3；白板 K1–K6/P6/C7–C9/N5/N6。按计划继承 02 §1.1–1.6/2.1–2.2/2.4/2.6–2.7/3.9–3.12 与 04 §2.1–2.6/3.1–3.5/5.3 的身份、原生同步和可靠投递边界，06 仅原生客户端。旧 Memo、special、Notebook 排期与旧 History 工具面退出。

## 2. 实际变更与 manifest

共 **16 个生产文件、7 个测试文件**；完整 SHA256、交回 HEAD、patch/log hash 见 `.hermes-dev/round3-local-20261017-l0/L-C/c9-surface/manifest.json`，差异快照为同目录 `c9-surface.patch`。共享仓其余 owner 变更未纳入本包；本报告另为获授权单文件。

| 路径 | 本包内容 |
|---|---|
| `secretary/noting_surface.py` | Main 三资格同步；History 常有，Notebook 全局 gate，Scheduler 独立 gate；重建已有 native bridge 的私有 catalog，冷热恢复检查四块实际指导，local 不重建 |
| `agent/inline_tool_executors.py` | 四工具和 Main Scheduler 的真实 inline 分发；删除旧 handlers；direct 退休名明确拒绝 |
| `agent/tool_executor.py` | 同步、并发、分段完整批次 guard；原生共同执行点带可信 catalog scope；Noting 单结果/aggregate 反馈身份来自 runtime |
| `agent/turn_tool_validation.py` | 原始完整批次在 fuzzy repair/未知项过滤前经过同一 C5 guard；保持原生配对结果与 continue。等价合并旧 None/string 判断保持冻结 complexity |
| `agent/conversation_loop.py` | 仅 `_invalid_tool_name_error_content` 对退休名返回结构化 legacy 错误；其余未知/合法混批及原生三次纠错不变 |
| `agent/agent_runtime_helpers.py` | 仅 `invoke_tool` registry 分支用同一 scoped dispatcher；`repair_tool_call` 拒绝退休名及其原生大小写/分隔符形式，不 fuzzy 执行新工具。文件保持3837行 |
| `model_tools.py` | 新 Agent-loop 工具集合、bridge 私有 capability filter、历史名非执行错误 |
| `toolsets.py` | 新 History/Scheduler/Noting 注册索引；原生 session_search 保留 |
| `tools/registry.py` | registry direct 退休名也明确非执行拒绝 |
| `tools/secretary_dispatch.py`（新增） | 新 Scheduler/maintain/finish 注册、统一退休错误、可信 ContextVar catalog scope、两处 native 批次拒绝适配；Noting 写工具只由任务 suffix 提供，不向 Main catalog 发布 |
| `tools/notebook_tool.py` | 直接消费 C1 完整 Snapshot envelope，空 Snapshot 成功，传 owner profile；共用 C5 新 schema |
| `tools/noting_memo_tool.py` | 退出注册与旧 DB mutation，只保留非执行拒绝 |
| `tools/tool_result_storage.py` | 可选可信 `noting=True`，host 留存及预览诚实说明；先缩 History 邻域，单消息仍大则剩余不可读，不建议 read_file/terminal/execute_code；原生预算和其它 runtime 文案不变 |
| `agent/session_persistence.py` | 仅 `_db_flush_write` 同时传 C6 prepare_rows/before_commit，成功后 confirm、再同步 markers |
| `gateway/secretary_reminders.py` | Scheduler 独立配置；保持 Main route/source/profile 与原生 runtime resolver；退出 Noting Force-window 冷能力阻断；generation/sequence 贯穿 ingress、重验和 busy conversion |
| `gateway/run_agent_cache.py` | parsed Noting/Scheduler enabled 分别进入原生 cache signature，字符串 false 等非法值不当 truthy |
| `tests/secretary/test_r3_wiring.py`（新增） | 当前29场景，见下表 |
| `tests/secretary/test_noting_surface.py` | 新 History 名称与默认 Idle off；保留构造、Turn、冷热恢复、分支/旋转/reset、prompt/schema字节与Prelude断言 |
| `tests/secretary/test_noting_hosts.py` | 消费 C10-A 新 fixture，显式 Idle 配置与真实 native source/usage；独立 Scheduler gate |
| `tests/agent/test_secretary_noting_dispatch.py` | 可信 child 标识、单 Noting runtime 与退休 compact 明确错误 |
| `tests/gateway/test_secretary_reminders.py` | 独立 Schedule 建立、profile 精确归属、完整 claim、冷原生 route、暂停/重领、Noting off仍投递 |
| `tests/tui_gateway/test_secretary_reminders.py` | 独立 Schedule；pending 到实际响应前不冒称 done；原生 poll/admission 和 cold真实Turn |
| `tests/secretary/reminder_runtime.py` | 保持两个公共函数签名；独立 Scheduler 建立原始 registry row，native prepare+bind+COMMIT后confirm。已停写，交 C10-B 消费 |

无需改 `secretary/noting_hosts.py` 生产逻辑、`tools/budget_config.py`、`hermes_state_secretary_schema.py` 或 `hermes_state.py`。没有修改 C6、C7、C8 Notebook/Framework 或 C9-H 生命周期实现。

## 3. 正式路径与遗漏图

```text
native construct / Turn / cold restore
  → apply_main_read_surface → 三资格 + 私有 tools/catalog
  → synchronize_main_read_prompt → native builder / root persistence

native provider tool batch
  → validate_tool_calls 原始整批 guard（过滤/修名前）
  → 原生 sequential / concurrent / segmented 整批 guard
  → 共同 authorization / direct invoke scope
  → conversation_history / Main snapshot show / child working show / maintain / finish / Scheduler

Gateway due tick
  → owner profile + Scheduler policy + native route resolver
  → C3 claim(generation, sequence, token, due)
  → 原生 ingress busy→C6 deferred；idle→原生 slot admission 重验
  → _db_flush_write → native prepare_rows → repair/insert → before_commit bind
  → COMMIT → confirm live → 实际 request carriage → C9-H 非空响应事实 → C6 ACK
```

| 要求 | 位置 / 证据 | 尚未覆盖 |
|---|---|---|
| 注册/catalog/同步/并发/inline一致 | registry/schema、两种成功四工具、actual catalog、direct/真实Turn legacy | 无本域已知代码缺口 |
| 混合 finish 零副作用 | 三 executor + 原始真实Turn含 unknown/退休edit/maintain | 不只依赖helper；实际Loop已证 |
| Main三能力、local、冷热 | surface33 + wiring冷/热Scheduler、catalog关闭负例、native auxiliary session_search | 原生真实模型后续由唯一运行owner执行 |
| Gateway Noting off及完整claim | Gateway30，metadata generation/sequence与durable消费 | 其它owner旧投递测试由C10-B收口 |
| native persistence | actual `_db_flush_write` 成功最终重算、事务拒绝无live/无消费 | unknown COMMIT恢复沿C6既有证据，本包不重复跑 |
| 预算与退休 | 单/aggregate helper与实际dispatch、native文案保持、真实Turn不fuzzy执行 | 未启动独立门禁，不声称全面用户验收 |

## 4. 执行证据

环境：官方 PM `.venv` Python3.14.7/macOS arm64，锁与依赖不变。所有 tests 均经 `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh ...`，runner 临时隔离状态；无真实模型、NM、服务或用户 profile。以下结果按有效运行并集覆盖 **112 个独立场景**，没有为汇总再全跑一遍：

| 文件 / 数量 | 有效日志 |
|---|---|
| surface33 | `repair.log`；catalog相关变化后 `direct-catalog-final.log`5例定向保持 |
| dispatch9 | `surface-dispatch.log` |
| Gateway30、TUI6 | `repair.log`29/6；新 Noting-off `final-failures.log`1 |
| hosts5 | `catalog-hosts.log`4；`child-host-repair.log`1 |
| 新wiring29 | `repair.log`11；`catalog-hosts.log`新增预算/legacy8；`child-host-repair.log`2；`direct-catalog-final.log`catalog1及legacy更新；`native-validation-final.log`原始批次3与旧名1；`legacy-normalized.log`保留原例+新增大小写/分隔符1；`final-failures.log`rollback1；`native-session-search.log`native auxiliary1 |

`repair.log`79场景12.7秒；后续均为新增或实际受影响路径的定向执行。初次失败日志保留：旧名、Idle默认、旧fixture profile=NULL、pending误断言及无registry/字段的测试构造均已修正；不能把首次失败计为通过。

官方冻结 `Measurer/compare/apply_allows` 对本包路径与起点的 scoped health：`health-final.log` **0 blocking/0 advisory**；`ruff-final.log`通过；`diff-check.log`为空通过。没有调整门禁、豁免、阈值或全仓检查范围。manifest 固定本包源码与证据hash。

## 5. 缺口与边界

- 本包没有真实模型/产品运行、完整 Python suite 或独立 Verification/Validation；这些由主会话统一安排。C3/C5/C6/C7原已通过组未重复执行。
- C9-H actual response ACK、completed/failed归档、precompaction与native成功boundary由其已交报告提供；本包消费正式入口，不冒称亲测全部H实现。
- C10-B正在消费已停写的共享 `reminder_runtime.py`，继续旧Scheduler/投递测试；延期 Web读DTO与UI没有复活旧结构。
- `tools/session_history_tool.py::SESSION_HISTORY_SCHEMA` 是C2保留的源码导入兼容常量，值的name已为conversation_history；不注册或执行旧名。本包没有为它恢复旧工具。
- 公共核心没有个人Provider安装依赖、NM特判或凭据；个人线保持停写。

## 6. 精确接口与生命周期

- `active_delivery_prepare_callback(db,batch_msgs,batch_rows)` 与既有 bind callback由 `_db_flush_write` 构造；prepare可随原生SQLite重试重复，修改私有待写row；bind在同txn查当前claim/route并绑定真实UID。失败不confirm、不发布live；成功COMMIT后confirm最终TrustedUserInput，再原生markers。
- Gateway event metadata必须携带 `conversation_ref, schedule_id, claim_token, generation, sequence, next_run_at`；`source_timestamp`保留实际进入时刻，不能代替due。`_event_claim`、busy和最终slot admission均保留原值，不重算generation/sequence。
- 冷Scheduler只消费已证明的profile/source/generation/current tip和Hermes `_resolve_session_agent_runtime`；不创建SDK/冷Agent、不要求Noting/Force阈值，也不新增Main gate。
- `secretary_surface_scope(agent)` / `scoped_registry_dispatch(agent,*args,**kwargs)` 只绑定当前runtime资格到目录副本，退出即reset ContextVar；共享native cache/schema不修改。
- `maybe_persist_tool_result(..., *, noting=False)`、`enforce_turn_budget(..., *, noting=False)` 新参数由可信child+唯一NOTING标识传入；未传的原生预算路径保持。
- Gateway profile过滤严格匹配registry.profile；测试home须原生可识别为default root或`.../profiles/<name>`，不能创建NULL profile后假定default扫描会接纳。

## 7. 下一步

主会话亲自review本包23路径与manifest；更新根CLAUDE接收状态后统一提交。接收后C10-B继续其独占旧测试；最终仅由统一owner执行round3真实产品/模型和独立门禁。无需C9-S再派生或重复已有效测试。
