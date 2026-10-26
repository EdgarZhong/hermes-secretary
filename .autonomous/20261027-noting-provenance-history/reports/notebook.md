# Notebook 来源链实现交回报告（已交回，待主会话 review）

## 1. 对应条款与边界

- 冻结基线：`02d55fdb45b4fb7c883fb477f4469912f4707f70`，分支 `codex/noting-provenance-history-20261027`。执行包 N，C04–C08／C20；配合 C02–C03 的每次真实编辑来源要求。
- 依据：07 顶部 2026-10-26／27 全部最新确认；v2 §2–5 与模型身份修订；白板 C1–C9、K6、U1–U2、N1、Persistence／结算；02 身份、不可变 item／Snapshot、合法来源与 fork／rewind；04 持久 child、冻结前缀及多 Turn 接缝。新语义覆盖旧平铺来源和可写范围。
- 本包未改核心文档、计划、History 实现／分类器、Noting Prompt、原生 compressor、生产库、锁或依赖；未提交、push、部署。主会话已授权最小扩展 `noting_tools.py`／`noting_child.py` Task owner 传递及 `noting_recovery_sources.py` 恢复接缝。

## 2. 实际变更

1. 直接消息来源唯一事实改为 `provenance: UID[][]`；本 Task 输入仍是 `source_message_uids: UID[]`。普通 fields 按键合并，提交的普通数组／对象整体替换，省略保留。
2. 每条目每 Task 仅尾部一个槽；后续调用、native Turn 和原 admission 恢复覆盖该槽。下一 Task 真编辑追加；属性无变化不分配节点／版本；来源单独编辑、缺来源、非法／重复／不在当前路径的来源原子拒绝。
3. `provenance_tasks` 持久记录节点 owner，`write_task_id` 记录每个版本实际维护 Task。runner 显式传 `str(admission_id)`；非 runner 独立 Store 实例才默认 UUID，不根据 child/session 字符串猜归属。两字段均不进入普通人类／模型 Notebook 投影，模型另隐藏 version_id。
4. 旧节点、派生时间与 source basis 的完整前缀受不可变版本和 Snapshot 门禁保护。历史 off-path 节点可原样继承，新增节点必须再次过当前合法路径，不能用旧节点授权新来源。
5. Evidence time 每个直接节点持久一个 `{start_time,end_time}` 或 `null`。组内真人消息优先，单用户单点、多用户最早／最晚范围；无真人取最近 Assistant；否则组内消息范围。只用原消息 timestamp；未知保留 null 槽位，不写 now、不因读取刷新旧时间。来源身份先经共享 `enrich_message_source` 只读补全，再按 `semantic_role` 判断；Instant 精确 receipt 识别集中在共享 owner，已删除 Notebook 私有重复 SQL。展示统一用 Profile 时区，真正同一时刻可读为字符串。
6. Candidate refs 型不建立直接链，沿当前引用的来源条目派生时间；与直接 UID 链仍互斥。工具 Schema 移除 source_time_ranges；原范围写入口即使显式空数组也拒绝，evidence_time 不可写。现有只读旧字段规范化边界没有扩成新结构迁移层。
7. archive 和 ordinary relations 自动清理保留已有链与时间，不强造 UID、不改既定生命周期／结算／引用保护；批量版本写入仍同一事务。恢复还保留被归档条目的最终不可变版本，防止原 archive 结果被内部恢复丢掉审计引用。
8. 模型回执已隐藏 version_id，恢复因此改用可信 admission owner、entry_id、完整可读成功回执匹配原不可变版本；非空初始状态匹配原 Snapshot。多个不同原版本／初始 Snapshot 均能匹配时明确拒绝，不猜版本、不重放维护。

## 3. 正式路径与持久形状

正式调用：`run_noting_task` → `initialize_notebook_work(task_id=str(admission_id))` → typed Notebook tools → `NotebookStore` → `NotebookWorkingState` → `_insert_version_conn` → INSERT-only item → Snapshot commit gate／pointer；继续／恢复仍走同一 Store 和正式 runner。

完整内部 entry 必含：

```text
entry_id, version_id, entry_type, fields, done, relations,
provenance, provenance_tasks, write_task_id, evidence_time,
created_at, updated_at, last_processed_at, archived
```

仅 `schedule_suggestion` 可选。直接条目三条链长度一致，Task owner 字符串非空且条目内不重复；每组 UID 非空、组内不重复，允许跨 Task 复用 UID。refs Candidate 的三条持久链均空，write_task_id 仍为该版本实际维护 Task。

`secretary_notebook_item.payload_json` 不含 entry_id、version_id、archived，分别从 lineage_id、id、archived 列恢复，其余全部保存；没有新表／schema 迁移。`source_basis_id` 如存在，必须是同 lineage、属于本 Conversation 或可继承、已被 Snapshot 引用的版本，并且其所有来源节点与时间为新版本完整不变前缀。

只读验证入口：`secretary.notebook_store.validate_snapshot_state_conn(db,conn,ref,payload)`（要求精确不可变版本）；审计读取 `db.notebook_snapshot_audit[_conn]`；普通完整投影 `show_notebook`／`readable_notebook_state`；原始单组派生 `derive_evidence_time(db,conn,ref,uids)`。原始派生不代替合法路径写入门禁。

所有展示入口通过共用投影：维护成功回执、Working Show、初始／续 Turn control、Main Show、Framework、slash／Web 文本、Persistence proposal；无 version_id 的模型投影和有人类审计身份的 API 各自保持。

## 4. 验证与原始日志

环境：本机 macOS，官方 PM 共用 `.venv`，Python 3.14.7、pytest 9.1.1；虚构隔离临时 SessionDB，无生产／网络模型请求。命令均经 `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh ...`。日志在 ignored `.hermes-dev/noting-chain-20261027/`；实现未提交，版本标识为上述冻结基线加本报告列明工作区差异。

- `notebook-fourth.log`：17 个 Notebook／原生 child／恢复相关文件 547 项通过，26.4 秒。之后仅恢复保留最终 archive、Schema 文本／分类反例及对应测试继续收敛。
- `recovery-final.log`：来源链新增及恢复 3 文件 49 项通过，15.3 秒，含非空初始 Notebook、真实失败 child／恢复原 admission、同槽覆盖、下一 Task 追加、歧义／错误拒绝、重启与源时间。
- `schema-final.log`：Schema 与 native child 2 文件 127 项通过，13.1 秒。
- `notebook-final.log`：17 文件 549 项通过、1 项旧断言失败；该失败只期待恢复内部移除 archive final row，已按保留不可变审计引用修正为当前可见条目仍仅保留项、内部另保留 archived final row；`recovery-archive-closed.log` 已定向复测 2 文件 25 项通过，14.9 秒。
- `quality-final.log`：独立临时 Git index 仅收本包 25 文件，对冻结基线执行 `scripts/check --staged --base <冻结哈希> --only ruff,health`，两项通过，health 0 blocking／0 advisory。未改真实 index，不运行全仓测试；最终 `quality-closed.log` 已再次以 25 个本包文件检查 ruff／health，通过，0 blocking／0 advisory，1.8 秒。`git diff --check` 本包范围通过。
- `semantic-before.log`：真实 DB 新增 4 例，旧派生 1 过／3 失败，证明 framework origin 的 user 及 assistant 系统载体错误取得高优先级。
- `semantic-after.log`：仅改 shared `semantic_role` 后，新 4 例通过，但旧 5 个真人保护反例失败；保留原断言，已定位并交接共享来源 owner。
- `semantic-closed.log`：共享可信来源补全和 Notebook 接线收敛后，2 文件 99 项全部通过，6.5 秒，包含原 5 个真人保护、新 4 个辅助优先级及真实 Instant admission／fork／foreign。H 包的共享分类实现与其额外测试由 History Agent 独立交回。

覆盖的真实机制包括：同 Task 多次覆盖、续 Turn／恢复同槽、下一 Task 追加、跨 Task 重复 UID、no-op／false 等价非法类型、完整来源同传、失败零副作用、readonly 时间、组内三优先级／未知槽／原始时间／重启、Candidate refs 派生／互斥、保护引用与批量关系清理回滚、Snapshot 精确版本／提交失败／晚结果 pointer、不在当前路径的旧组继承及新组拒绝、fork 分支隔离、native 全前缀与实际工具回执恢复。

## 5. 缺口与完成边界

本包已知范围内实现／测试缺口已关闭。最后 review 发现的来源分类差异保留了改前反例、纯替换后回归失败和共享修复后的 99 项通过证据：没有把真人自行输入包装降级成系统来源，也没有让 metadata 标注的 user／assistant 辅助载体占取证时间优先级。共享分类代码由 H 包负责，本包只接共用正式入口；没有改原生 compressor、没有改保护断言。

上述 17 文件回归与随后受影响文件定向复测按有效同版本范围复用，没有把先前一次 549 过／1 失败的全包执行冒称完整通过；唯一恢复 archive 断言经 `recovery-archive-closed.log` 的 25 项补测关闭，最终来源集成经 `semantic-closed.log` 的 99 项关闭。其余未变机制证据继续有效。

真实模型、独立 Verification／Validation、Linux／正式机及一次性人工目标数据转换归主会话，单元／受控模型 I/O 证据不代替这些门禁。没有执行 UI；没有动用户显示状态。

## 6. 接口影响

- Store／WorkingState 新增可选可信 task_id；initialize 新增同名可选参数；正常 runner 始终显式传原 admission_id，恢复不用新的 recovery child session 当 owner。
- 模型写参数保持 source_message_uids 一维；读来源名改为 provenance 二维。禁止写入范围、完整链、内部 owner 或 evidence_time。
- main/human 普通投影不暴露 owner 元数据；模型 entry_id 稳定、version_id 隐藏；审计仍可读精确不可变版本。
- 一次性生产转换须由主会话按明确授权手工准备新持久形状；本包没有迁移程序。旧时间范围无法凭当前来源组直接保留为可写来源，必须按精确 UID 补齐，未知证据时间使用 null，不能填当前时间。

## 7. 建议后续动作

由主会话亲自 review 本包及共享来源分类接线，复用上述有效存储／native 机制证据，再跑真实两 Task 模型样本及两个独立门禁。生产转换脚本只作用获授权唯一置顶 Conversation，核验所有版本／Snapshot 引用、所有非来源字段和其它对象指纹。

## 本包文件清单

产品：`secretary/notebook_contract.py`、`notebook_evidence.py`、`notebook_items.py`、`notebook_model.py`、`notebook_render.py`、`notebook_store.py`，以及 `secretary/noting_contract.py`、`noting_tools.py`、`noting_child.py`（唯一构造调用参数）、`noting_recovery_sources.py`。底层 SessionDB Snapshot／pointer schema 和提交算法原接线足够，本包没有修改 `hermes_state_secretary_notebook.py`。

测试：`test_notebook_provenance_arrays.py` 改为新链／UID-only 契约，新增 `test_notebook_task_recovery.py`；其余 Notebook 专项及 `test_r3_child.py`、`test_noting_recovery.py` 只更新受影响的显式来源输入／链形状、补保留 archive final row 的内部恢复断言。`test_notebook_model.py`／`test_notebook_coverage_projection.py` 未改，作为既有回归执行。未修改其它实现包 dirty 文件。

## 集成回归补充（主会话追加委派，已整包交回）

主会话首次 Secretary 分区＋History 集成原日志 `integration-tests.log` 最终是 87 文件、1703 通过／105 失败（217.6 秒）；这是集成发现记录，不能与本包原定向通过混同。新增白名单仅扩展受本轮来源契约影响的 Secretary 测试，未改产品、Schema、Prompt、History 或当前真实模型运行。

已修正的旧夹具／断言：Candidate 矩阵和结算的平铺 sources／可写 ranges、直接来源 proposal 材料改分组链、真实编辑显式同传 UID、History 回读工具结果显式 include_auxiliary、RPC 失败 child 夹具按原 admission 绑定 owner 并写规范 typed update／模型投影回执；Framework、业务状态与独立 Scheduler、Schedule 建议、权限测试补显式 UID。保留生命周期／已批准覆盖与未完成责任／原子拒绝／原冻结父前缀等验收要求。

- `integration-fixtures-first.log`：6 文件 59 通过／2 失败，19.3 秒。Candidate provenance（17）、settlement lifecycle（10）、provenance wire（7）、source visibility（5）、dynamic tools（19）已过；RPC 恢复继续升级夹具后进入下列复测。
- `integration-fixtures-second.log`：7 文件 202 通过／3 失败，64.5 秒。r3_framework（19）、schedule status（3）、schedule suggestion（4）、fixed permissions（86）、noting child（38）通过。Candidate source contract 51 通过／1 真实转换边界失败；RPC 恢复已成功进入并提交，余 2 项旧 finish 后额外模型请求计数期待失败。

待主会话裁定的真实边界：同 Task 新建 direct Candidate 后显式 `source_message_uids=[]` 并切换 refs，当前产品仍保留该 Task 唯一 direct 节点而拒绝切换。旧 Task 节点不可删除，但这个场景没有旧 Task 节点；测试 `test_candidate_source_contract.py::test_direct_candidate_requires_complete_source_clear_before_switch_to_refs[messages]` 已保留。建议只允许清除尚未提交的本 Task 唯一 direct 槽后切 refs，已有旧 Task direct 节点仍不可删。尚未改产品或把拒绝改为测试通过。

非来源形状失败已独立复现于 `integration-nonshape-diagnosis.log`（4 文件、23 通过／13 失败；其中 crash 子进程耗时另列原日志）：

- dynamic fallback 3 项：实测 primary→fallback→primary（finish 已是末调用），旧期待末尾再一次 primary。
- request protocol selector 1 项：实测 3 请求，旧期待 4；同类计数还影响 compaction visibility／boundary prefix，以及当前 RPC recovery 的 2 项。
- Force notice 1 项：实际观察到两条相同且都满足旧队列已失效／fence 存在／active summary 成立的记录；旧期待只调用一次 loader。
- active reminder crash 8 项：预期 SIGKILL 实际子进程正常 return 0；TUI 明确报测试 lambda 不接受新增 image_paths，gateway 尚需单独诊断。同样的 lambda 签名落后还影响 timestamp_origin 两项。另 r3_joint compact 返回 False、boundary prefix current_interrupted 无预期 marker 均不含本轮 Notebook 源写入。

上述非 shape 断言未修改，已向主会话提交具体路径与原始证据，需基线核实／独立处理，不可当作新链夹具升级直接放行。

### 集成收尾结论与补充验证

主会话已授权并冻结工程细节：只允许当前尚未提交 Task 的唯一 direct 槽随显式 `source_message_uids=[]` 与合法 refs/source_types 切换为 refs；有任何旧 Task direct 节点不允许删除。产品最小变更在 `notebook_model.py`、`notebook_contract.py`、`notebook_items.py`、`notebook_store.py`，不改 schema 或持久形状。WorkingState 检查显式清槽，正式 source_basis 和 INSERT 点再次依据可信 Task owner 与 Snapshot 引用事实校验；已提交版本即使复用同 owner 也不能清除。不可变旧 item 仍保持原 JSON，当前槽可转 refs、再次转 direct，并在原 admission 恢复后继续维护同槽。

- `candidate-current-slot-first.log`：原来源继承／原子性及 Candidate 模式 3 文件 103 项通过，31.9 秒。
- `candidate-current-slot-final.log`：4 文件 98 项通过，27.3 秒；包含新增 Store 往返、显式原 Task 恢复再转 direct、旧 Task／旧加当前双节点／已提交后复用同 owner 拒绝且零副作用，及原结算 10 项与 Candidate 来源矩阵 52 项。
- `integration-quality.log`：本包及新增测试共 37 文件对冻结基线 ruff／health 均通过，0 blocking／0 advisory，3.0 秒；本包 `git diff --check` 通过。

当前新增产品失败与本轮来源契约适配失败已关闭；首次集成中的 74 项属于本轮契约升级／上述一个真实转换边界，相关文件已逐包定向复测。旧 range-only／mixed 正向场景按新契约改为 UID-only 正向或明确拒绝已退休范围的反向场景，未把新来源语义改回旧行为。原 105 失败中其余 31 项为下表可重复的冻结基线同名失败，没有改产品或原断言放行。

| 文件 | 当前集成失败数 | 冻结基线复现 | 结论及证据 |
|---|---:|---:|---|
| test_noting_dynamic_fallback.py | 3 | 3 | 同末尾 finish 额外请求计数 |
| test_force_notice_compaction.py | 1 | 1 | 同重复 loader 观察 |
| test_noting_request_protocol.py | 1 | 1 | 同请求计数 |
| test_active_reminder_crash.py | 8 | 8 | 同 SIGKILL 未触发／TUI lambda image_paths 签名 |
| test_timestamp_origin.py | 2 | 2 | 同 lambda image_paths 签名 |
| test_r3_joint.py | 2 | 2 | 同 compact 返回 False |
| test_r3_compaction_visibility.py | 6 | 6 | 同 finish 额外请求计数 |
| test_r3_boundary_prefix_regression.py | 6 | 6 | 5 个 finish 计数＋1 个 current_interrupted marker |
| test_conversation_debug_integration.py | 2 | 2 | 同名但不同阻断层：冻结版先卡缺 version，当前规范夹具恢复／提交已成功，仍卡原末尾额外请求计数；未断言后续未执行检查通过 |

冻结树 冻结临时基线树（精确路径见ignored `.hermes-dev/noting-chain-20261027/review-evidence/baseline-environment.json`） 版本 `02d55fdb45b4fb7c883fb477f4469912f4707f70`，沿官方 PM venv／官方 runner；未编辑基线产品或测试。`nonshape-frozen-baseline.log`：8 文件 88 通过／29 失败，53.6 秒；这 29 项与当前原集成同名失败集合完全相同。`rpc-frozen-baseline.log`：1 文件 1 通过／2 失败，11.4 秒（pytest 4.17 秒），明确保留更早缺 version 原因。逐项集合比较见 `baseline-failure-comparison.json`。这些旧失败单列交给主会话，不扩大本轮产品修复；当前不是整分区零失败声明。

新增测试修改白名单共 12 文件：candidate_provenance、candidate_settlement_lifecycle、candidate_source_contract、conversation_debug_integration、noting_source_visibility、noting_dynamic_tools、noting_provenance_wire、r3_framework、schedule_status_lifecycle、schedule_suggestion_framework_v2、fixed_noting_permissions、noting_child；原 Task／source 本包另补 5 个来源槽／恢复测试。没有修改非 shape 的 8 个旧失败文件或其断言。

### 74 项本轮契约修正的逐文件定位与最终定向命令

| 修正文件（tests/secretary/） | 首次集成本轮失败数 | 当前有效定向证据 |
|---|---:|---|
| test_candidate_provenance.py | 10 | integration-fixtures-first：17 通过 |
| test_candidate_settlement_lifecycle.py | 10 | candidate-current-slot-final：10 通过 |
| test_candidate_source_contract.py | 36 | candidate-current-slot-final：52 通过；退休 ranges 正向已替换为当前契约正／反向矩阵 |
| test_fixed_noting_permissions.py | 2 | integration-fixtures-second：86 通过 |
| test_noting_child.py | 1 | integration-fixtures-second：38 通过 |
| test_noting_dynamic_tools.py | 1 | integration-fixtures-first：19 通过 |
| test_noting_provenance_wire.py | 6 | integration-fixtures-first：7 通过 |
| test_noting_source_visibility.py | 2 | integration-fixtures-first：5 通过 |
| test_r3_framework.py | 4 | integration-fixtures-second：19 通过 |
| test_schedule_status_lifecycle.py | 1 | integration-fixtures-second：3 通过 |
| test_schedule_suggestion_framework_v2.py | 1 | integration-fixtures-second：4 通过 |
| 合计 | 74 | 有效证据按修正影响复用，不相加成一次完整测试执行 |

在本工作区执行的最终相关命令（各次完整 stdout/stderr 见上列日志）：

```bash
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/secretary/test_candidate_provenance.py tests/secretary/test_candidate_settlement_lifecycle.py tests/secretary/test_conversation_debug_integration.py tests/secretary/test_noting_source_visibility.py tests/secretary/test_noting_dynamic_tools.py tests/secretary/test_noting_provenance_wire.py --tb=short --show-capture=no
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/secretary/test_conversation_debug_integration.py tests/secretary/test_candidate_source_contract.py tests/secretary/test_r3_framework.py tests/secretary/test_schedule_status_lifecycle.py tests/secretary/test_schedule_suggestion_framework_v2.py tests/secretary/test_fixed_noting_permissions.py tests/secretary/test_noting_child.py --tb=short --show-capture=no
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/secretary/test_notebook_provenance_arrays.py tests/secretary/test_notebook_task_recovery.py tests/secretary/test_candidate_source_contract.py tests/secretary/test_candidate_settlement_lifecycle.py --tb=short --show-capture=no
```

冻结树基线命令：

```bash
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/secretary/test_noting_dynamic_fallback.py tests/secretary/test_force_notice_compaction.py tests/secretary/test_noting_request_protocol.py tests/secretary/test_active_reminder_crash.py tests/secretary/test_timestamp_origin.py tests/secretary/test_r3_joint.py tests/secretary/test_r3_compaction_visibility.py tests/secretary/test_r3_boundary_prefix_regression.py --tb=short --show-capture=no
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/secretary/test_conversation_debug_integration.py --tb=short --show-capture=no
```

主会话现有真实模型样本没有 Candidate 来源形态转换分支；本包已用受控 Provider 的真实 native child／SessionDB 正式路径覆盖此分支，不因此重复既有真实模型样本。产品文件已稳定，不再追加修改。


## 主会话最终RPC契约补证

此前2个RPC测试在旧finish额外请求计数处阻断。主会话按“finish为最终工具动作、完成后不再发模型请求”记录回环模型端实际finish响应所在请求序号，断言其后无请求，替代与现行终止语义相冲突的固定3／2次数；未改产品finish逻辑。进一步暴露历史夹具仅含terminal而不具现行固定六工具；补全真实已冻结工具表后仍逐字比较实际tools与该表，没有放宽冻结断言。

`rpc-terminal-contract.log`先为2过／1败，后者卡在夹具旧tools缺六定义；`rpc-final-surface.log`最终1文件3项全部通过（6.0秒），已到达并通过后续Snapshot精确工作态、原失败child及registry不变、当前Main并发tail保留、原Schedule／启动Profile／进程环境不变、Framework发布及重复RPC不增请求／不留lease。仅测试底座升级，无新增产品修复。原31项基线同名失败中的这2项现已关闭；当前保留29项／8文件原断言失败，不再把RPC列为当前缺口。原表与旧日志保留当时事实。
