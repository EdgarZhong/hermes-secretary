# C10-A · History 首次运行与 Notebook/child 旧测试收口

Development 本包完成，停止写入，待主会话 review。未 stage/commit、切分支或派生；没有真实模型、NM、部署、UI 或用户状态操作。共享工作区的其它 owner 差异完整保留。

## 1. 对应条款

冻结基线 `d19018a7ba3e38ae01f76aa57821b55cbc15ff58`，07 unchanged：§0–3、§4（重点839–907）、§5、§7、§8.10–13；白板 A2/A4/A5/C1–C9/I1/I2/U1/U2/T2–T5/L0–L9/E1/E2/P6/K1History。保留旧02/04中的身份与合法路径、原文来源、Snapshot/pointer原子性、持久child/cache prefix、资源释放；不恢复旧类型、Memo、双profile或child压父。

范围按plan C2/C5/C10及主会话追加白名单；C5/C7/C8报告已有有效证据复用，不重复这些新测试组。

## 2. 实际源码变更

仅三个生产文件：

| 文件 | 最小改动／原因 |
|---|---|
| `tools/session_history_tool.py` | `_search` 候选成员验证抽为 `_candidate_public`，保留 route、投影fallback、partial、预算及错误传播。原 nesting=7，现 `_search` nesting=5；不改原生 session_search。 |
| `hermes_state_conversation_history.py` | 可见合法路径出现缺失/空白/非字符串 UID 时返回 source_unavailable；原先候选无法匹配后会伪报 `success/count=0/partial=false`。旧 damaged-metadata 反证触发并验证修复。 |
| `secretary/notebook_render.py` | 获主会话批准，仅公开 Snapshot `created_at` 经 `format_timestamp(..., profile_home=...)`；不暴露 epoch，不改内部浮点、entry或source ISO精度。 |

未改 `hermes_state_search.py`、候选流、锁/依赖/门禁、C5/C7/C8源码或C9 wiring。

## 3. 正式路径与测试处置

实际执行注册/inline `conversation_history` →真实owner/path→原生候选流与SQLite；Notebook使用真实Store/commit/rewind/branch；child使用真实AIAgent/native loop/工具dispatch/持久Session/registry/commit/close，仅provider返回和必要时序受控。原生父压缩的receipt、cooldown、lock、cancel保留，测试直接调用正式native request，不恢复child压父alias。

| 旧文件（目录以行内路径为准） | 现行处置与有效保障 | 本包独立PASS场景 |
|---|---|---:|
| `tests/secretary/test_r3_history.py` | C2首次实际执行，69全过；抽取后69复证，坏UID校验后只定向16条路径/成员/作用域反证 | 69 |
| `tests/tools/test_session_history_identity.py` | 真实注册与inline实际Agent；反复压缩后规范Identity/原文、Main/Noting父域、私有feedback不可见、物理ID退役、锚点模式拒filter | 8 |
| `tests/tools/test_session_history_truncation.py` | 约800字符字面命中片段＋完整Read、每行预算、坏UID/时间失败关闭；去掉读取旧文档Schema的镜像测试，改实际模式冲突调用 | 8 |
| `tests/secretary/test_notebook_store.py` | 冻结Anchor/明确termination、幂等commit、拒绝原子性、候选真实来源、单profile、分支、offpath同claim行政维护、新source提交重验 | 8 |
| `tests/secretary/test_notebook_provenance.py` | 保留rewind后禁止新引用、task load/insert/commit三时点重验、不可借用basis/owner/lineage、伪造版本拒绝、旧并发base独立、compaction原文、分支重绑和回滚。旧offpath任意改正文改成processing_note同claim维护；相同source无变化不制造版本 | 23 |
| `tests/secretary/test_notebook_model.py` | 旧十类型状态图/排期退出；保留跨owner即使validator宽松仍拒绝、完整state深拷贝/非法section拒绝，新增旧类型不可创建/恢复。现八类型全部字段/状态/refs/no-op等复用C1 93条中的对应保障 | 10 |
| `tests/secretary/test_notebook_v16.py` | 保留实际版本链、归档内部终版/不可变SQL、并发task版本、branch不改parent、range/字段原子拒绝、完整body gate/overflow audit。旧secretary_task排期与三工具退出；新工作态/四工具复用C1/C5 | 4 |
| `tests/secretary/test_notebook_render.py` | 完整payload/ID/coverage可读、无Snapshot明确null、无archive/audit污染、深拷贝、源时间不改与四section空Snapshot | 4 |
| `tests/secretary/test_readable_times.py` | 三时区真实DB→Main show/slash/History/Reminder同一秒精度；精确存储及过滤边界不变，其余时间格式保障保留 | 10 |
| `tests/secretary/test_noting_child.py` | 保留原生persistent child、suffix-only、多模态/隐藏feedback、prefix/root/tools每请求及重试稳定、同步freeze、五Turn、语义权限、构造/线程/provider/状态/commit失败与资源/owner清理；坏base在分配child前拒绝。special/Schedule子工具退出改显式禁止；不删failure保障。live/durable比较公共字段并另验native持久化标记 | 38 |
| `tests/secretary/test_noting_busy_idle.py` | 真实Main busy/ingress/daemon/end timer/local/global重新开启/owner切换保留；使用显式Idle开启＋实测usage。仅Memo自动开启分支退出；观察器返回用Event同步，消除spawn回调先到的竞态 | 6 |
| `tests/secretary/test_noting_compact.py` | 十项native低阈值、cooldown、durable lock非admission、receipt及summary尚未结束、错误typed result、安全拒绝；直接正式native request。原child binding工具断言被四工具退役负例替代 | 10 |
| `tests/secretary/test_noting_compaction_cancel_completion.py` | 父native receipt后cancel，独立child仍合法finish/commit，完整成功消息live/durable一次且ID相同 | 1 |
| `tests/secretary/test_child_memo_v16.py` | 旧Memo增删/消费/归档持久化退出；保留实际组装overflow零provider、Main不受child guard影响、原parent切换/排队后切换、真实Idle/Force system Anchor不被通知推进、真实archive工具→内部完整commit；增加退役Memo不能自动开启/写入 | 9 |
| `tests/hermes_state/test_secretary_notebook.py` | 原十三项Snapshot insert-only、out-of-order pointer、并发、rollback、rewind/null、branch独立、local重开及termination audit保留；新提交无termination明确拒绝 | 13 |
| `tests/hermes_state/test_secretary_notebook_schedule_atomicity.py` | 原Notebook-owned schedule_sync要求退出。改十二项真实独立Table反证：late commit/rewind/null/branch/Noting-off不改Table，pointer失败回滚、缺Schedule schema仍可提交，六类非法完整state无副作用 | 12 |

合计 **233 个独立参数展开场景**均有PASS证据，来自相应最终分组/定向结果，未声称某次单命令运行233。被替换的148个原测试函数及其原参数装饰器、保留/退役与替代保障映射见ignored `old-test-disposition.json`；不是skip/xfail。

等价保障复用：C1 `test_r3_notebook.py` 93、C5 `test_r3_child.py` 34；C7 63；C8新/旧Framework证据（owner变更事务rollback、晚结果丢弃、busy/fence、至多一次、strict阈值）。C3 Scheduler 47及C6 Delivery 30见 `c6-report.md`，替代旧Notebook-owned schedule状态、native时间表达式、在途ACK等要求；本包未重跑。

## 4. 验证与耗时

环境：官方PM `.venv` Python3.14.7，macOS arm64；canonical runner临时隔离，非真实round3产品运行。前缀统一：

```bash
HERMES_PYTHON="$PWD/.venv/bin/python" HERMES_TEST_FILE_RETRIES=0 scripts/run_tests.sh <本包准确文件或-k> -q
```

日志目录 `.hermes-dev/round3-local-20261017-l0/L-A/c10-a/`；每次日志开头保存完整文件列表及filter，manifest保存摘要和哈希。

| 执行日志／范围 | 结果与runner wall |
|---|---|
| first-run.log：初次14文件（含C2 69） | 103 PASS/109 FAIL，另3旧文件collection失败，22.2s；C2 69 PASS |
| extra-db-first.log：主会话追加两DB文件 | 2 PASS/24 FAIL，1.5s |
| history-store.log：History两旧文件/C2/Store/来源/DB | 119 PASS/10 FAIL，7.0s；C2抽取后69 PASS、DB13 PASS |
| lifecycle-display.log：九文件首次适配 | 85 PASS/15 FAIL，27.6s |
| history-provenance-retest.log：五受影响文件 | 48 PASS，3.8s |
| child-display-retest.log：三个失败文件 | 47 PASS/7 FAIL，24.0s；busy6及child34已过 |
| failure-time-final.log：4 child故障＋三时区 | 4 PASS/3 FAIL，2.2s；坏base1及三时区3已过 |
| failure-diff.log：仅body故障诊断-vv | 1 FAIL，1.4s；确认仅native内部row标记差异 |
| source-health-final.log：History16＋非法state6 | 22 PASS，1.4s |
| failure-final.log：仅剩三个child故障 | 3 PASS，1.8s |
| retained-native-final.log：补保留system Anchor×2/archive完整commit | 3 PASS，2.2s |

共11次canonical runner调用，包含首轮、诊断及失败定向复测；没有完整项目suite，没有C1/C5/C7/C8新组重复运行。初次观察HEAD `e200936b5c8f93e33f51625fd0b397a1d826a55f`，交回HEAD与18文件当前SHA256/锁hash/本包patch固定在 `manifest.json`，不把共享HEAD冒称已包含本包未提交代码。

固定版本Ruff检查18文件通过。调用官方未改动Measurer/compare/apply_allows/verdict限定同18文件对HEAD：**0 blocking、0 advisory**；`_search`和新helper均未超阈值。首次健康检查指出测试if/elif梯，被修为动作表；未调门禁。`git diff --check`通过。健康执行代码与精确测量见 `check_scoped.py`、`checks-final.log`、`health-measurement.json`；不是空index检查。

## 5. 缺口与边界

本包无剩余已知产品失败。完成范围是本地定向机制验证及旧例收口；真实DeepSeek工具协议/cache及完整host产品场景仍归后继owner在统一round3隔离profile执行，本报告不宣称真实模型或整体Develop验收通过。

`tests/secretary/test_web_read.py`、`test_web_read_child.py` 属明确延期DTO/UI，未更新、未运行，不为旧DTO恢复旧payload。未执行原生session_search全组，因公开handler/Schema/实现未改；C2已有原生候选路线保障有效。

## 6. 接口影响

无生产调用签名改变。公开Snapshot envelope的 `created_at` 现在为时区ISO字符串，C9-S `notebook_show`直接消费；DB仍float。`_candidate_public`为工具私有helper；History malformed UID使用既有 source_unavailable 错误形状。

`test_noting_child` 的 `db/stub_client/parent/make_agent/mock_response/_tool_response/_read_mutate_finish_responses` 公开fixture/helper名称及无参helper调用保持；已告知C9-S owner。响应helper现在是show→maintain matter→finish→text，合法source_time_range对应fixture原文1000/1001秒，无硬编码Conversation Ref。未写hosts/surface。

## 7. 建议后续动作

主会话集中review三个生产窄改及逐组退役映射后阶段集成，复用本包有效证据；C9只复测其实际接线变化。保留本报告与ignored manifest定位，不为接收报告再跑233条。本文不修改产品口径，不新增待追认决定。
