# C7 父 runtime 联合触发与压缩区间交回

状态：本域 Development 实现、定向测试和自审完成，待主会话 review 与 C9 正式接线；停止写入。未提交、未 stage、未切分支、未派生。C4 文件保持已交回状态；未运行真实模型或个人服务。

## 1. 条款与机制

冻结依据 `d19018a7ba3e38ae01f76aa57821b55cbc15ff58`：07 §0–3、§4.5、§7、§8.1–2/8.11–13、§11/11.1；白板 N0–N6/P1–P5/D6–D8；继承 02 §4.6–4.9、§5.1–5.5/5.10–5.11 的原生测量、完整冻结、资源与提交；04 §4.4–4.7 的 D01/持久 child/五 Turn。

- 四入口共用 `prepare_joint_noting`：真实 Main/owner/profile → 配置/local/capability → 原生测量/Idle 双条件 → 最近实际 Main 来源 D01 → Anchor → 同一 admission 事务 → C5 同步冻结父 prefix/runtime/base → 后台 child。
- Force 的压缩区间写在既有 admission `compression_interval_id`。当前成功 native boundary 身份存于 Secretary 自有 `secretary_noting_compaction_state`；它只是最后已发布 native boundary 的身份指针，不是第二任务状态机或调度器。首次按真实当前 Full Foreground 的最近 compaction 初始化；之后仅显式成功压缩 hook 更新，rewind 不重选它。
- 同一 admission 事务检查本区间是否已有 `kind=force` 并插入新 admission，所有四入口均复用；新 Anchor、child 成功/失败/取消、释放和 rewind 不删除占用。只有新成功 boundary 允许新区间整理；重复观察同 UID 幂等。
- Idle 默认关闭；开启后 Main 期限与真实 native usage 必须同时达标。达到 Force 空间线时使用 Force kind/占用，保持安全线优先。周期只消费一次，新 Main Turn 取消/重臂，辅助活动不改 Main 时间。关闭配置后既有到期事件终结清理，不复活旧期限。
- `NotingDecision.compaction_due` 单独保留 Idle 双条件已经成立的事实，Noting 的 External 拒绝、Anchor 不可冻结、admission 错误或 spawn 失败不抹掉该事实；父 native compaction 继续请求。manual/auto 的原生 callback 无条件执行，native 异常原样传播。
- D01 不依据 model/provider/api_mode 猜来源；only `external` 拒绝 Noting。Idle 在时间和长度条件成立后、freeze/admission 前判来源；未知/native 保持旧行为。
- Force 接纳与 External 拒绝沿原 Framework producer，保留既有文案/suppression。原有 `agent/compression_force_notice.py` 成功提交后退休机制保留，未将接纳 receipt 当成功边界。

## 2. 变更白名单

修改 6 个既有文件，新增 1 个测试文件：

| 文件 | 变更 |
|---|---|
| `secretary/noting_runtime.py` | 新联合入口/结果、四 kind、Idle 双条件、D01、一次同步 spawn、父压缩继续、成功边界 hook；删除 `idle_task_profile` 与旧配置字段消费者 |
| `secretary/noting_timers.py` | Idle 开关关闭时不初始化 timer，终结既有到期状态；保留 daemon、弱 owner、同 period 恢复、Main start 取消与 owner 锁 |
| `secretary/noting_compact.py` | 删除子工具 Schema、special dispatch 与结束状态；仅父 runtime 的 `request_parent_compaction` 原生适配 |
| `hermes_state_secretary_noting.py` | 四 admission kind、interval 字段/索引、成功 native boundary 身份、同事务 Force 占用；child finish 不清 occupancy |
| `tests/secretary/test_noting_runtime.py` | 现行配置/单 profile/长度门槛/Force 区间；保留真实身份、生命周期、capability、失败、持久 D01、重启断言 |
| `tests/secretary/test_noting_timers.py` | 更新新配置与长度用量，实际 daemon/恢复/关闭/External/once-only/框架 flush；负向路径用 callback Event 等待，移除短负向 wait |
| `tests/secretary/test_r3_joint.py` | 新事务竞争、四入口、释放/rewind/跨 boundary rewind、成功 boundary、新区间无需等待旧 child、失败压缩/关闭/External/父 prefix 等测试 |

`noting_capability.py`、`noting_admission_receipt.py` 读取并复用，未修改。不改 C4/C5/Framework/正式 agent caller、根文档、plan、规格、规则或锁文件。

## 3. 正式路径与接线边界

- 已有 Force 三处测量调用继续通过 `maybe_admit_force_from_pressure → prepare_joint_noting`；没有另建计数器。
- 已有 `note_main_turn_started/finished → daemon timer/_run_idle_event → prepare_joint_noting → C5.spawn_noting_task → request_parent_compaction` 已接新逻辑；C5 已确认 spawn 在线程启动前完成 prefix/runtime/base 冻结，C7 不等待 child 完成。
- DB 使用现有 SessionDB mixin 与 schema initializer，新增仅 Secretary-owned 表/字段；开发新隔离库，无迁移。
- manual/auto 的正式 native 接缝仍由 C9 唯一 owner 接入；本报告提供可调用实现和准确替换表，不以局部 callback 测试宣称这些实际 agent 路径已完成。

## 4. 测试、版本与证据

环境：macOS arm64，官方 PM `.venv` Python 3.14.7；canonical runner，`HERMES_TEST_FILE_RETRIES=0`，临时 HOME/HERMES_HOME，真实 SessionDB/native compressor/Foreground/rewind；仅 child/model 调用边界受控，无真实模型/NM。

唯一测试所有权：新增 `test_r3_joint.py`（26 参数展开场景），获主会话确认的旧 `test_noting_runtime.py`（17），`test_noting_timers.py`（20），共 **63 个独立场景全部有 PASS 证据**。

基础命令：

```bash
HERMES_PYTHON="$PWD/.venv/bin/python" HERMES_TEST_FILE_RETRIES=0 scripts/run_tests.sh tests/secretary/test_r3_joint.py tests/secretary/test_noting_runtime.py tests/secretary/test_noting_timers.py -q
```

执行历史（没有反复全量）：

1. 首次本域三文件：53 PASS、3 FAIL，6.5 秒。失败为全局关闭期限清理缺口，以及两个不符合新实际用量条件的夹具（native 零用量响应不覆盖上次真实值；恢复 owner 未提供已解析用量）。
2. 修产品清理与测试输入后，仅 timer 文件：20 PASS，4.2 秒。
3. 新增 External 两 transport × Force/Idle，以及 freeze/spawn 失败仍 native compact：`test_r3_joint.py -k 'external_execution_fact or idle_native_compaction'`，6 PASS，0.9 秒。
4. 引入显式 `compaction_due` 后只复测实际受影响 Idle/lifecycle 路径，加跨 boundary rewind 新例：三文件 `-k 'idle or timer or deadline or native_off_turn_end or framework_queue or main_start or auxiliary_turn or attach_recovers or external_idle or restart_retains or resumed_owner or same_anchor_idle or rewind_across'`，34 PASS，4.3 秒。其他有效 Force/manual/auto 事务证据复用。

最终 Ruff 对 9 个本域文件通过；官方 `scripts.code_health` 未改动的 Measurer/compare/apply_allows/verdict 引擎按 7 个 C7 changed 文件限定范围、与 HEAD 比较：0 blocking、0 advisory。没有 stage，未运行 `scripts/check --staged` 的空检查；整体保留检查留主会话统一门禁。`git diff --check` 通过。

版本/依赖 SHA256、dirty patch hash、HEAD、执行历史：`.hermes-dev/round3-local-20261017-l0/L-A/c7/manifest.json`。同目录 `first-tests.log`、`timers-repair-tests.log`、`joint-failure-tests.log`、`idle-final-tests.log`、`health.log`、`c7.patch`。没有把工作区 HEAD 冒称包含未提交 C7；新的测试文件另用 SHA256 固定。

## 5. 公开接口与上下游契约

```python
NotingAdmission(admission_id, conversation_ref, anchor_message_uid, kind, profile,
                task_profile, compression_interval_id="")
NotingDecision(action, reason="", admission=None, compaction_due=False)
prepare_joint_noting(parent, *, trigger, measurement=None, messages=None,
                     now=None, expected_period=None) -> NotingDecision
run_joint_cycle(parent, *, trigger, native_compact, measurement=None, messages=None,
                now=None, expected_period=None) -> (NotingDecision, native_result)
note_successful_compaction(parent, *, committed: bool) -> bool
request_parent_compaction(parent, *, threshold_tokens=None) -> native_result
```

- `trigger/kind`：`force / idle / manual / auto_compaction`；唯一 `task_profile='NOTING'`。`measurement` 继续是 C4 的 `ContextMeasurement`，不估计 tokens；`messages` 是父实际 Active 消息。
- `prepare_joint_noting` 为 fail-safe Noting 增量；返回后 child 已同步冻结并在线程运行，不等待其结束；它不执行 manual/auto 的原生压缩。`run_joint_cycle` 额外保证 native callback 无条件执行，返回原 callback 结果，native 异常不吞。
- `maybe_admit_force_from_pressure(agent, measured_tokens, *, messages=None)` 签名与字符串结果保留，是新入口薄 facade。`try_admit_force` 删除旧 `force_snapshot_in_segment` 参数；不保留旧 Snapshot-only gate/执行 alias。`try_admit_idle` 签名保留，结果新增父 compaction due 事实。
- `db.noting_compaction_interval_conn(conn, ref)` 读/初始化已成功 boundary 身份，**不能在只读连接随意调用**；当前仅 admission write transaction 调用。
- `db.noting_force_occupied_conn(conn, ref, interval_id=None)`：传已获取 interval 避免重复读取；与 `noting_admit_conn` 在同一 write transaction 执行。
- `db.noting_record_compaction_conn(conn, ref)`：仅在 native boundary 已真正写入同一成功事务内调用；`db.noting_record_compaction(ref)` 是 post-commit 包装；同 UID 幂等。无新 boundary 不改变身份。
- `note_successful_compaction(..., committed=False)` 恒不更新；True 仍从真实当前 Full 读取边界，不接受模型/工具声明的 UID，不使用 receipt/no-op 作为成功事实。
- C5 spawn 准确签名不变：`spawn_noting_task(parent, admission, *, instruction=None, parent_active_messages=None, owning_profile=None) -> threading.Thread`。C5 不读取已删除的 `compaction_threshold_tokens`。

## 6. C9 唯一正式接线替换表与缺口

| 既有入口 | C9 应做的具体动作 | 防重复/成功边界 |
|---|---|---|
| `agent/turn_context.py`、`turn_preflight.py` 既有 Force 测量点 | 保留 `maybe_admit_force_from_pressure(..., messages=实际消息)`；其内部已统一 | 不再额外 direct spawn；已有三测量点共享同事务 interval 谓词 |
| 普通自动 native compaction | 在 native safety/fence/route 已确认、压缩修改实际 Active 前调用 `prepare_joint_noting(..., trigger='auto_compaction', messages=实际消息)` 一次 | 保留原生必须压缩，即使返回 skip/error；不要在 preflight 和 `_compress_context` 两层各启动一次 |
| `conversation_compression_manual.compress_now`、TUI/RPC手动入口 | 汇聚同一个 native pre-compression hook，用 `trigger='manual'`；传实际冻结消息 | 不在每个客户端额外 direct spawn，再由公共 hook重复启动 |
| Idle timer | 当前已通过 `prepare_joint_noting → request_parent_compaction` 完成一次 | `agent/context_compaction_request.py` 现固定 `trigger='noting_compact_parent'`，C9 改为父内部 `noting_joint_idle`/等价明确标记，在公共 native hook 识别“本次已准备”，不再第二次 prepare/spawn；不注册旧工具 alias |
| rotated成功持久化 | `agent/conversation_compression.py::_publish_rotated_compaction` 在 `publish_compression_child` 成功后调用成功边界 hook | 与现有 `retire_committed_force` 同成功范围，不能在 receipt 或正常函数入口调用 |
| in-place成功持久化 | `_commit_compaction` 的 `archive_and_compact` 成功后调用成功边界 hook | 与已有 `retire_committed_force` 同成功范围；失败/no-op不调用True |
| 更严格事务接线（可选） | 在实际成功 native DB publication事务内调用 `db.noting_record_compaction_conn`，替代post-commit包装 | 需要主会话明确授予 native DB sibling 单文件所有权；C7没有越权改 `hermes_state_messages.py`/`hermes_state_compression.py` |

**缺口真实保留：** manual/auto 正式 native caller、成功 boundary hook 的实际生产安装、Idle内部native触发标记替换，由 C9 接线；现有 Force notice 真实成功/失败 retirement 与完整 agent native fence/route 情景需要 C9 正式集成测试。C7 callback/DB机制证据不能冒充这些接线已验证。真实 DeepSeek、整体门禁、个人 Provider 无本任务证据。

## 7. 旧测试处置与后续建议

- 删除/重写旧两 profile 选择、special child compact、Snapshot-only Force 成功判据、不同 Anchor 任意重复 Force、旧 idle keys 等退出要求；没有保留执行 alias、skip/xfail 或放宽预算。
- 保留旧 runtime/timer 中实际 Main 资格、辅助隔离、Main start取消、owner恢复、profile、真实用量、capability、DB失败、D01持久化、无请求不覆盖、关闭期限、Framework flush 等有效断言。
- 其它旧 `test_noting_compact.py/test_noting_busy_idle.py/test_noting_hosts.py` 及正式调用测试不在本任务白名单，尚需 C9/收口 owner 按新 07 更新；不要以其旧 special profile 断言反向要求复活旧机制。
- 主会话 review 本域后将正式 caller/成功 hook 精确交给 C9；本域 63 场景的同版本有效结果复用，只有接线或共享依赖实质变化时定向复测。测试规则和公开/个人边界保持不变。
