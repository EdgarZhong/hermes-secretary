# C8 Framework 通知交回（2026-10-17）

本域 Development 完成并停止写入，待主会话 review；未 stage/commit/再派生，未运行真实模型、启动产品服务或写NM。源码与依赖精确哈希见 ignored `L-A/c8/manifest.json`；共享HEAD不冒称已包含未提交C8。

## 条款与修改

依据07 §3.1/3.2、§7、§8.10/8.13、§11.1，白板N3/L1/L6/L9/P2；继承02 Snapshot/pointer、原生安全尾部append/busy/fence/live-durable/at-most-once/不启动Turn，04审计与业务payload分离。

| 文件 | 实际变化 |
|---|---|
| `secretary/framework_messages.py` | 沿现有内存队列保留snapshot_id/termination/summary，增加C5约定的完成/失败入口；snapshot通知在原生append事务prepare_rows内验证当前pointer并准备正文、before_commit中再次验证owner/pointer且追加同一live行；失效整条丢弃；原生失败撤销本次live行。通用Force/External producer及suppression/retirement保留 |
| `secretary/noting_notifications.py` | 只负责已提交Snapshot的消息正文与计数：复用C1 `render_notebook`完整正文；Python len统计Unicode码点，现行四数组长度统计独立entry；严格超过现行C4阈值才追加其唯一Proposal常量。failure/forced/overflow分开 |
| `tests/secretary/test_r3_framework.py` | 17场景，真实NotebookStore/SessionDB/原生append/queue/并发锁；覆盖完整正文、乱序、排队丢弃、已追加后推进、竞争、回滚、threshold、fence、独立开关和失败 |
| `tests/secretary/test_framework_message_boundaries.py` | 主会话批准的旧本域维护：现行Idle配置、实际mock API usage、原生compaction受控边界、Force interval occupied新断言和原清理假对象修正；保留原生repair/wire/durable/身份/timeline/冷恢复/多producer行为断言 |

未修改 `hermes_state_secretary_notebook.py`：C1的 `notebook_snapshot_if_current_conn` 已足够。仅消费C6的 `append_messages_batch(..., prepare_rows=...)`，没有触碰其文件。C5主review另授权 `noting_tools.py` 当前时间改 `isoformat(timespec='seconds')`，并在既有单节点补microsecond==0断言；两者已停止写入并由主会话随C5提交。

## 接口、正文与开关

- `publish_noting_completion(parent, commit_result, *, termination, summary) -> bool`：与C5签名一致。receipt只有 `pointer_changed is True`、snapshot_id==effective_snapshot_id时才能准备；读取实际提交Snapshot验证audit后渲染，不从提交后查询推测本次是否生效。False代表未接受，True表示已按原队列机制接受尝试，不承诺已投递／重启必达。
- `publish_noting_failure(parent, *, conversation_ref, specific_reason) -> bool`：07原英文无新Snapshot回执，不附Notebook/Proposal，不伪报成功。
- `append_runtime_row` 新可选 `snapshot_id/termination/summary` 仅内部snapshot生产者使用；缺省通用路径保持原行为，不传prepare_rows。既有Reminder调用者可原样调用。
- 成功通知正文依07模板包含Conversation/Snapshot/coverage/termination/summary与C1完整Notebook renderer输出；正文的Created at来自Snapshot提交时间。仅该Notebook正文计字符，通知头/Framework外壳/Proposal不计；引用不重复算entry。默认12000/60及自定义阈值均是严格大于。forced/overflow正文明确可能有未完成职责，不误用无Snapshot文案。
- `_runtime_valid` 只判断实际合格Main与原DB/Conversation/live列表，删除对Reminder/Scheduler injection资格的耦合。Noting完成/失败与External Framework不因Scheduler关闭而消失；各producer自身准入规则不被绕过。关Noting后已经持久化的Framework在冷恢复仍按原生事实读取。

## 锁与事务顺序

1. 外层现有 `_secretary_framework_lock` 序列化busy/队列/Turn标记；持有原 `_session_persist_lock`，先flush既有live tail，冻结flush后的实际physical session。
2. 原生 `append_messages_batch` 取得SessionDB writer lock与BEGIN IMMEDIATE，先执行原生compression/turn-lease guards；C8 `prepare_rows` 用同conn确认当前pointer，读该immutable正文/audit，构造本次私有row，不发布live。
3. 原生repair/insert/reconcile后，`before_commit` 同conn再次核对原DB/Conversation/list identity、真实session binding和pointer；在仍持DB写锁时追加同一个live row。Snapshot commit只有DB锁，不回取host锁，顺序不反转。
4. 原生COMMIT返回后同步persisted markers并走原display sink。native回滚／重试最终失败时，在释放外层host锁前移除本次live对象；队列沿原逻辑一次性取出，持久失败不自行重试。已被取代的snapshot内部异常只丢弃整条含Proposal消息。

并发测试设置屏障：A在pointer检查事务内时B不能提交；A原生COMMIT返回后，刻意阻挡A的外层后续代码，B提交一完成便同时观察到A的durable行和live行，证明live追加不落在B pointer更新之后。B在A排队期间先生效的场景则整条丢A；A已追加后B生效的场景保留正常两条推进。rewind重选pointer自身不制造通知。

## 验证与证据复用

只有canonical runner；`HERMES_TEST_FILE_RETRIES=0`。真实SessionDB、NotebookStore、native transcript repair/append、AIAgent Main/child与原生status sink保持；模型transport、父compaction请求结果及竞态屏障为受控边界，无真实模型/NM。新旧Framework共 **59个独立场景全部取得PASS**；C5时间精度另1节点通过。未重跑C1/C5既有组。

| 运行 | 实际范围与结果 | 总耗时 |
|---|---|---|
| 1 | 两个Framework文件首次：新15 PASS/1失败；旧22 PASS/20失败，另1 teardown错误。新失败是assistant被误作原生rewind目标；旧失败为已退出配置／缺usage及清理假对象 | 22.32s |
| 2 | 修夹具后仅失败相关节点：新rewind1 PASS，旧24 PASS/2失败；剩余2项为新Force区间占用与旧Idle重复spawn断言冲突 | 15.90s |
| 3 | 仅Force2修订、新增fence1与加强live竞争1：4 PASS | 2.31s |
| 4 | 公共夹具变更影响的旧文件其余16节点：16 PASS；不复跑上轮26节点 | 4.64s |
| 时间小修 | `test_r3_child.py -k test_control_encodes_full_schema_and_working_data_separately`：1 PASS | 单文件0.61s |
| 检查 | `scripts/check --only ruff,health --base HEAD`，夹具调整前/后两次均通过；最终0 blocking/0 advisory；diff-check通过 | 0.98s / 1.79s |

测试修复只改变输入与按07退出的旧产品预期，没有降低规则、加skip/xfail、盲目重试或改锁。第一次新C8其他15项有效证据直接复用；新rewind与fence补证、竞争加强后复测各自节点。

证据：`.hermes-dev/round3-local-20261017-l0/L-A/c8/` 下first-run、fixture-repair、final-targeted、fixture-complement的log/json；checks/checks-final；time-precision.json；manifest.json。首轮HEAD `92fddf82f280f79a73db8ecba5d454ae7a437e1a`，最终哈希以manifest为准。

## 调用者、限制与下一步

- C5 `_commit_when_complete` 和失败notice对象已按相同签名调用两入口；旧Framework的真实spawn/finish测试同时覆盖该接线，未改C5其余代码。
- C7 Force/External producer、mark_framework_turn/flush及原fence waiter沿用；Force成功compaction退休的最终native挂载仍由C9收口，不由C8改父压缩。
- C9仍负责四工具正式dispatch与全部Main native生命周期。C8不是独立Verification/Validation，也没有DeepSeek结构化工具／真实缓存命中／真实NM证据。
- 无新增持久通知队列、数据库schema、跨重启保证或新唤醒；目前进程崩溃可丢失尚未追加的通知，沿冻结契约如实保留。

C8完成后停止本域写入，交主会话review集成。
