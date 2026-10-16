# C5 Development 交回（2026-10-17）

## 范围与条款

本域停止写入，待主会话 review；无 stage/commit、无真实模型或产品服务启动。开发运行记录为共享集成工作区的 HEAD 加本报告列出的未提交文件，精确源码哈希见 ignored `L-A/c5/c5-manifest.json`。不把本报告当作 C8/C9 整链完成或独立门禁通过。

| 文件 | 作用／条款 |
|---|---|
| `secretary/noting_child.py` | 07 §3.1/3.2、§8.11/8.12；继承02持久child／冻结prefix、04五Turn／overflow／Turn后提交。去Memo/special/child压父；同步捕获base，Commit Gate返回C1同事务receipt，资源仍按原生命周期关闭 |
| `secretary/noting_tools.py` | 07 §4.4/4.5、§7：四工具、整批finish预检、同task锁下freeze、首次reason幂等、task-local show、小结果与结构化错误 |
| `secretary/noting_contract.py` | 07 §4.3/4.5完整function对象逐字结构提取，运行时不读取规格文件；无长度限制 |
| `secretary/noting_prompts.py` | 07 §8.11/8.12英文正文逐字提取；六步、逐类型处置、用户认可、来源、部分结算及外部权限边界完整保留 |
| `secretary/notebook_store.py` | 主会话批准的C1最小补丁：未传base读取current，显式None为空，给ID仅hydrate该immutable snapshot，并验证存在及Conversation归属；不改pointer接口 |
| `tests/secretary/test_r3_notebook.py` | 增加3个base冻结／异步父pointer更新／错误owner与不存在Snapshot场景 |
| `tests/secretary/test_r3_child.py` | 34项：四工具、guard负例、small-result/own-working-view、finish锁与幂等、原生持久child两请求/五Turn、失败/overflow、local-off提交拒绝、multimodal、skip-memory |

白板覆盖C1–C9/K6/L0–L9/E1–E2/N0–N6/P1–P6中本域要求；无新产品口径。固定Prompt与Schema来自现行07，与冻结文档同源；不继承旧Memo、十类型、Schedule intent或compact_parent执行alias。

## 精确接口与接线责任

- `guard_noting_tool_batch(agent, tool_names) -> None | dict`：`tool_names` 是完整原生批次按序解析的function names；C9必须在同步/并发执行任何调用前调用一次。含finish且多于1调用时返回标准 `invalid_argument`，C9为每项返回同error、整批零执行；非Noting返回None。这里只提供前置guard，不伪称它已接入全局executor。
- `notebook_maintain(child, args)`、`notebook_work_show(child, args)`、`finish_noting(child, args)` 返回JSON字符串。Main无mutation授权；没有绑定store/相同task lock/父Conversation则拒绝。maintain调用C1 `store.maintain`，不回整簿；show返回C1 working envelope。
- finish在 `store.lock` 下freeze，保存固定内部state与首次termination；返回 `{success:true,status:end_requested}`，无commit receipt。后续maintain返回state_conflict；重复合法finish保留首次reason/result，show/History只读仍可用。
- `noting_tool_schemas(profile='NOTING')` 返回新的四个完整Schema副本。`noting_tool_control_message(profile='NOTING', *, notebook_state=None, conversation_ref=None, coverage=None, base_snapshot_id=None, current_time=None)` 附冻结英文控制文本及独立JSON数据；C9仅追加suffix，不能改父tools/root。
- `spawn_noting_task(parent, admission, *, instruction=None, parent_active_messages=None, owning_profile=None) -> threading.Thread` 未改调用签名；线程启动前同步捕获prefix、runtime/root/tools、admitted_at、base_snapshot_id，然后worker消费这些冻结值。C7先admit，在原有父锁内调用spawn，再执行原生父压缩；不等child。`run_noting_task` 删除memo_entries，新增可选 `frozen_work={'base_snapshot_id': ...}`，其余签名沿用。
- `freeze_notebook_start(db, conversation_ref) -> {'base_snapshot_id': str|None}`；`NotebookStore(..., base_snapshot_id=<省略>|None|str)` 三态区分。隐式或显式base的owner与来源仍由C1校验，不引入继承新草稿或合并任务。
- `commit_noting_snapshot(...) -> dict` 使用 `notebook_commit_snapshot_result_conn`，在同一写事务内重检Noting gate并提交；结果不另查pointer。`NotingTaskOutcome` 新增 `commit_result`（C1完整四键dict）及 `termination`，既有snapshot_id/committed保留。
- C8成功接缝：`framework_messages.publish_noting_completion(parent, commit_result, *, termination, summary)`。只在本次 `pointer_changed` 才调用；C8实际追加时仍须原pointer/原owner同锁同事务校验。forced/overflow summary注明未完成限制。
- C8失败接缝：`framework_messages.publish_noting_failure(parent, *, conversation_ref, specific_reason)`。当前任务没有提交Snapshot的真实失败/提交拒绝使用；失败notice对象绑定原DB/Conversation并只尝试一次。关闭导致的正常abandoned与无pointer变化的成功旧Snapshot不伪报系统失败。C8未接入时仅记录发布缺口，不反转已提交事实。

## 验证与次数

统一使用 `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh`，无直接pytest，无真实网络/模型。模型返回与请求overflow仅作为受控I/O边界；原生 AIAgent、child Session、SessionDB、工具finish、runner、Snapshot事务和close保持真实。

| 次数 | 范围 | 结果／总耗时 |
|---|---|---|
| 1 | `tests/secretary/test_r3_notebook.py` + `tests/secretary/test_r3_child.py` | 93+33=126通过；5.87秒 |
| 2 | 仅C5文件；加入真实非空tools前缀比较、失败Framework适配及local-off提交场景后 | 34通过；5.63秒；未重复C1 |
| 1次检查 | `.venv/bin/python scripts/check --only ruff,health --base HEAD` | ruff通过；health只有C7定时器测试F841阻断，已交其owner；C5本域无阻断 |

证据目录：`.hermes-dev/round3-local-20261017-l0/L-A/c5/`，包括 first-run.log/json、child-followup.log/json、checks.log、c5-manifest.json。首次观察HEAD `723343c60f65e6942f7a26113455cff53292c6cb`；第二次 `ba6266f314dbeddc01a4066110ed5138df683efd`，测试中本域源码没有修改。精确当前源码哈希由manifest补充，后续集成变更仅定向复测实际受影响路径。

## 缺口、旧测试处置与建议

1. C9尚需真实注册四工具handler与两种batch执行入口调用guard；本域guard测试证明前置拒绝返回及无状态副作用，不能替代C9正式batch零写场景。
2. C8两通知函数尚待实现；因此本域只证明提交receipt/notice适配边界，不宣称完整Notebook Framework或pointer排队竞争已验证。
3. 真实DeepSeek结构化四工具可调用性与缓存请求证据，留唯一真实运行owner在用户指定round3隔离profile验证；本次没有真实缓存命中/效果证据。单元测试仍用canonical runner临时隔离。
4. 原 `test_noting_child.py`、`test_noting_compaction_cancel_completion.py`、`test_noting_busy_idle.py`、`test_notebook_model.py`、`test_notebook_store.py`、`test_notebook_v16.py` 等含旧三工具/special/Memo假设，未为了兼容而恢复alias，也未运行这些旧组；由C9/C10按07保留持久child/prefix/失败资源、替换旧产品语义，避免把合法旧测试整批视为无效。
5. 无C1功能失败；只按主会话批准补base捕获能力及3场景。C7通知接口已发送，C9/C8签名已获主会话同意。请主会话review并阶段提交；我停止本域写入。
