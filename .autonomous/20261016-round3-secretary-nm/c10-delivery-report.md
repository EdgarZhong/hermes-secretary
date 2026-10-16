# C10-B · Scheduler／Reminder 旧保障收口

Development 本包完成，停止写入，待主会话 review。仅修改指定十个测试文件；无生产源码/shared helper修改，无stage/commit/分支/派生，无真实模型、NM、UI、部署或用户状态操作。

## 1. 条款

冻结 `d19018a7ba3e38ae01f76aa57821b55cbc15ff58`：07 §0–3、§6–7、§8.6/8.9/8.14；白板 A3/A7/K1–K5/N5。继承02 §3.9–3.12/5.6、04 §5.3的claim/lease/route、真实carrier、实际请求携带与成功响应后ACK、重启/原生timestamp。Notebook ownership、旧entry type/schedule_sync、Noting local开关控制排期的断言退出。

依据已读 C6报告（含C3 47＋C6 30有效证据）、C9-S `c9-surface-report.md` 的正式caller/nativeprepare合同。上述77项新测试未重复运行。

## 2. 实际变更

- 创建与控制fixture经真实 `SchedulerStore.create/update/pause/resume/delete`，claim带generation/sequence/token/due；不恢复sync/reconcile函数或alias。
- 请求/投递测试经真实Schedule claim→queue pending，替代无效或旧Notebook-shaped pending；新正文验证SCHEDULED ATTENTION／Schedule／Due／Delivery／Content，保持原生wrapper/时间、整批顺序与单carrier。
- ACK断言先证明无carrier不能ACK、只有携带无成功响应不能ACK，再沿既有native transaction实际绑定carrier。原生持久化、provider失败、middleware无response、lateACK/部分batch、重开DB保障保留。
- 关闭用例改独立scheduler.enabled；Noting global/local关闭改为排期继续的正例。删除Schedule现在确实移除row，旧receipt不能恢复；不为旧cancelled tombstone恢复实现。
- Gateway SIGKILL fixture按C9-S已确认的profile约定放入临时 `profiles/default`，修正registry.profile与scan='default'不匹配导致未进native append的假失败；未改Gateway生产代码。

## 3. 正式路径与旧用例处置

真实SessionDB/Scheduler控制、原生append的prepare/insert/before_commit/COMMIT、active witness、CLI既有serial lane、实际request assembly/provider受控返回均执行生产实现。SIGKILL subprocess在原生写事务前、inside及COMMIT后杀进程，再以全新进程重开同库/过期lease/执行host due scan，未用内存异常代替进程死亡。

| 文件 | 保留／替代保障 | 最终独立PASS |
|---|---|---:|
| `tests/secretary/test_reminders.py` | busy转换原子去重、周期继续、route/实际进入timestamp与原Due、stale route、ACK前carrier、内容不能虚构、finalize幂等、旧token/错误occurrence/缺generation拒绝、事务回滚、双发生重开与分别ACK、过期重claim、pause及Scheduler开关、跨Conversation token保护 | 16 |
| `tests/secretary/test_active_reminder_crash.py` | CLI/TUI/Gateway × native写前/事务内/提交后九边界，fresh host重扫恰好一条durable user row；TUI崩溃marker不因scheduler off或删除重放 | 11 |
| `tests/secretary/test_active_reminder_admission.py` | 最后admission重验Scheduler off/delete/改期/过期/reclaim、原生carrier后不能重claim、拒绝恢复相同Due新token、旧receipt不能撤回新owner、local off仍可写、route/occurrence匹配、no-op不撤销receipt、pause/resume后旧receipt失效、SQLite锁等待后lease过期 | 15 |
| `tests/secretary/test_active_reminder_persistence.py` | 定义控制先提交则native写前失败无SDK/compaction/ghost；普通turn原生不变；before COMMIT回滚、COMMIT返回丢失靠native row恢复；JSON无witness、chunk拒绝、原生turn lease被抢后禁止落库 | 10 |
| `tests/secretary/test_cli_reminders.py` | 正式idle lane、busy/pure deferred不排新Turn、Scheduler off/on原Due、poll后再gate、invoke失败、既有housekeeping/busy monitor、cold CLI真实chat trusted/untrusted wire/durable与timestamp | 10 |
| `tests/secretary/test_v16_delivery.py` | 两occurrences同一durable batch、context丢弃后复用原carrier、失败provider/重启、Framework owner/busy/fence/原生压缩rotation、owner在native写边界改变、Force producer owner、retirement、tail flush失败、实际携带的部分batch与成功响应条件 | 21 |
| `tests/secretary/test_schedules.py` | 独立Main建表、pause/resume/delete稳定身份、扫描资格/单claim、Noting与local关闭不控制排期、Scheduler off保留及on恢复原Due。旧Notebook reconcile/text projection/消失条目禁用退出 | 5 |
| `tests/secretary/test_schedule_status_lifecycle.py` | 旧十类型终态reschedule/reactivation/Memo耦合矩阵退出；现证业务完成、归档、Snapshot失败均不控制Schedule。Scheduler自身终态/已消费once/no-op及原子控制复用C3/C6 77，pointer rewind/branch不动Table复用C10-A 12 | 3 |
| `tests/agent/test_secretary_reminder_request.py` | 真实assembly→durable carrier→实际provider响应ACK、失败请求重试原carrier、child/aux不拉、Scheduler gate独立、原生wrapper bytes、middleware无provider响应不ACK | 6 |
| `tests/hermes_state/test_secretary_schedule_registry.py` | 两连接并发唯一winner、lease/release/reclaim、完成once重开不重放、pause/resume过期一次、done no-op不refire、周期跳过积压、bounded helper与once无recurrence、损坏canonical失败原子回滚/claim可释放、dedup/pull/实际carrier后ACK/reopen | 9 |

合计 **106 个独立参数展开场景**均有有效PASS证据，按最终分组与失败定向拼合，不声称单次运行106。完整原测试函数、原参数装饰器、保留或退役及替代保障定位存ignored `old-test-disposition.json`。没有skip/xfail；保留的是有效可靠性反证，退出的是旧产品控制关系。C8/C9-S已通过的其它文件未重复运行。

## 4. 验证与证据

官方PM `.venv` Python3.14.7，macOS arm64，canonical runner临时隔离（不启动真实round3产品profile）。统一命令前缀：

```bash
HERMES_PYTHON="$PWD/.venv/bin/python" HERMES_TEST_FILE_RETRIES=0 scripts/run_tests.sh <准确文件列表及-k> -q
```

证据目录 `.hermes-dev/round3-local-20261017-l0/L-A/c10-b/`。每个日志开头保存完整范围与filter；manifest含源码/锁/补丁及日志SHA256。

| 日志／范围 | 结果与runner wall |
|---|---|
| first-run.log：指定十文件首次 | 29 PASS/20 FAIL，另六文件collection因旧符号失败，29.0s |
| admission-native.log：admission/persistence/CLI/request/V1.6投递 | 56 PASS/6 FAIL，9.5s；其中request6、persistence10、V1.6 21已过 |
| service-crash.log：Reminder服务＋三Gateway与两off/delete crash | 20 PASS/1 FAIL，15.7s；失败是测试patch未对准现行finalize读取点 |
| admission-service-final.log：仅七个失败参数 | 7 PASS，1.0s |
| registry-lifecycle.log：三旧registry/lifecycle文件 | 16 PASS/1 FAIL，1.2s；旧once helper预期None，当前合法接口明确无recurrence报错 |
| final-two.log：helper once／partial batch ACK | 2 PASS，1.2s |
| crash-profile-final.log：共享home路径变化实际影响的六CLI/TUI SIGKILL | 6 PASS，18.6s |

共七次runner调用，按首次/实际失败/共享fixture影响定向，没有重开十文件全组；无C3/C6新组复跑。固定版本Ruff十文件通过；官方Measurer/compare/apply_allows/verdict引擎限定本十文件对HEAD：**0 blocking、0 advisory**。`git diff --check`通过。没有改检查器、阈值或空index检查。检查脚本及精确结果为 `check_scoped.py` / `checks.log` / `health-measurement.json`。

旧用例映射使用已记录 `dcd008f667e68183255d2d41076657a3ee1ac2a5` 树；共享交回HEAD及当前十文件SHA256见 `manifest.json`，不把HEAD冒称含未提交测试。

## 5. 缺口与生产问题

本包无剩余已知生产失败；没有生产修改请求。真实模型/cache与完整产品验收由唯一后继owner执行；本包受控provider不是其替代。SIGKILL仅当前macOS实际平台，未声称跨平台覆盖。

C9-S维护的Gateway/TUI/hosts/surface/dispatch测试文件未修改或重复运行；本包crash文件虽然使用host入口，仅验证独立的进程死亡/恢复边界。UI/DTO及正式部署继续后置。

## 6. 接口影响

无生产签名、Schema或返回形状变更。`tests/secretary/reminder_runtime.py` 只读消费，C9-S确认已停写；`arm_native_reminder` / `persist_native_carrier`维持其既有签名。跨旧测试引用 `test_active_reminder_admission.invalidate` / `test_reminders.materialize` 仅本包fixture，前者已改当前Scheduler控制；无平行产品实现。

partial request ACK先实际`verify_carried_reminders`，再观察无response ACK=0，最后以受控成功response事实ACK恰好被携带的批次；另外actual-provider seam测试保留真实非空响应/失败/middleware路径，未让测试构造正文授予ACK。

## 7. 建议后续动作

主会话review十个测试差异和旧例映射后集成，复用106场景证据；不为接收报告重跑本包。若C9正式接线再发生相关变动，仅复测实际影响边界。无新产品口径或待追认决定。
