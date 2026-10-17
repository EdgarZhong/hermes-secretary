# C10-H 旧 runtime/config 测试收口与真实模型执行方案

状态：本包完成，停止写入，待主会话亲自 review。五个获授旧测试文件及一个后续明确授权的生产窄修已落盘；无 stage、commit、再派生或分支切换。真实模型及产品服务 **尚未启动**，等待主会话完成 C9-S review 并明确 start。

## 1. 对应条款与保留保障

依据冻结 `d19018a7ba3e38ae01f76aa57821b55cbc15ff58`：07 §3/6.3/8.1/11.1、白板 N/P/D；继承 02 §4.6–4.9/5.1–5.5、04 §4.4–4.7 的真实 Main 资格、Profile 隔离、原生阈值/失败/来源、持久 child 及提交边界。02 §4.5 第 1268 行的单 deadline 参与决定经主会话核实仍适用，本包据此修复实际回归。

- 保留精确 64K/66K/128K、1.20 原生余量公式、strict capability 边界与已解析 compressor 测量，不新增 token 估算。
- 新嵌套 Noting Idle 默认关闭；旧 key 不翻译执行。坏配置只关闭所属功能；真实 Main 的 `conversation_history` 与独立 Scheduler 继续存在。global/local off 不改原生压缩配置。
- 真实 Main 结束计时、自然 daemon、off/on slash、stale deadline 不删替代周期、终结 off 事件不复活、重启/同 Anchor 并发、child registry 生命周期均保留。
- Force 占用依据同事务 admission 的压缩区间，不依据 child/Snapshot 成功释放；四入口共用；只有真实成功 native boundary 推进区间。
- 既有 External native transport 的成功 RPC receipt、拒绝/取消/超时/失败保持真实机制；本组使用已有 `FakeClient`，未启动 App Server 进程。D01 继续按实际请求来源，不能因 API mode 猜测拒绝；其有效矩阵由已接收 C7/C9-H 证据映射保留，不重复运行。

## 2. 实际变更与退出保障映射

| 文件 | 变更及保留保障 |
|---|---|
| `tests/secretary/test_noting_policy.py` | 换新嵌套配置/扁平 dataclass 参数，保留 global/local、Idle 时间、原生阈值和测量；删除退出的两 profile 选择用例 |
| `tests/secretary/test_noting_config_contract.py` | 正式 Main construction/request 改 `conversation_history`；坏配置自身 Notebook 关闭、History/Scheduler 保留；校验错误使用实际 hint；保留冷能力构造、LM Studio 不激活、配置失效、日志顺序和原配置不改 |
| `tests/secretary/test_noting_codex_receipt.py` | 不再 import 退出的 child compact 工具或其旧测试；使用正式父 `request_context_compaction`，保留真实 native fence/receipt/FakeClient RPC 完成及失败条件 |
| `tests/secretary/test_noting_deadline_event.py` | 在本文件建立独立真实 AIAgent/SessionDB/daemon 夹具，开启显式 Idle 时间+长度；实际 Main response 提供真实格式 usage；保留一次 local 决定；新增 Idle 升级 Force 后关闭仍准入、Commit Gate 拒绝场景；关闭事件用完成 Event 等待而非短负向 sleep |
| `tests/hermes_state/test_secretary_noting.py` | schema 断言换新 interval 表、退出 Memo 表；四 kind 正向场景；Snapshot-only Force 成功断言换成 child/Snapshot 不释放占用及真实 native 成功推进；保留 SQLite 并发、身份、registry、restart、durable Idle |
| `secretary/noting_runtime.py` | **仅后续获授权 `_freeze_and_admit` / `_idle_decision` 窄修**：成功 claim 的 Idle 显式传参与已决定，避免二次读取 local；其他入口和 Commit Gate 保持检查 |

未改任何私有 `_harness`、C4/C5/C9-S/正式 host 文件、规则、锁、核心文档、规格或 validation.md。

退出能力的保障归位：旧 `idle_task_profile / NOTING_WITH_COMPACTION` 选择由现行单 `NOTING` profile 替代；C5 `test_exact_four_schema_surface_is_independent_copy` 已证明旧 profile 明确拒绝，本包又定向复核 C7 `test_idle_requires_actual_length_and_has_one_runtime_profile`。旧 `compact_parent` 子工具不恢复 alias，父原生请求 receipt 保障留本组，legacy 工具明确失败由 C9-S 的正式 dispatch 证据承担。旧 Snapshot-only Force 判据已由本域新真实 DB 测试和 C7 区间/rewind 既有证据替代。

## 3. 发现的真实回归、修复与正式路径

首轮旧 deadline 夹具使用已删除 key，按现行配置与真实 usage 修正后，原有效的两项断言仍失败：

1. local on 的 deadline 在同一次 Idle 准入读 local 两次；
2. deadline 已决定 on，freeze 接缝把 local 关闭后，admission 被第二次检查拒绝。

原因是 `db.noting_idle_claim_event` 已在原事件写事务作唯一 local 决定，随后 `_freeze_and_admit` 又无条件检查。主会话核对 02 §4.5 的用户既有单次决定契约，明确授权最小修复；未把这两项改成接受新行为。

现在正式路径为：真实 `run_conversation` → Main 结束 → daemon deadline → `noting_idle_claim_event` 原子决定 local → `_idle_decision` 校验实际长度/D01/能力并冻结 → `_freeze_and_admit(... participation_decided=True)` → child spawn → parent native request。该显式参数仅来自成功 claim 的 Idle，包括达到 Force 线而使用 Force kind 的情形；普通 Force/manual/auto 默认 False，仍在 admission 事务读 local。child 真正提交时的独立 gate 未改，关闭后抛精确 `NotingChildError("local_disabled")`、无 Snapshot。

deadline 测试保留真实 Main loop、usage 更新、原生 SessionDB、slash 与 daemon。受控边界仅为模型返回、child spawn 和父 native request I/O；它不冒称实际摘要模型或 child runner 已再次测试。真实 native 发布的区间更新测试走 `archive_and_compact`，不手工设“成功”状态。

## 4. 验证命令、结果与版本

统一前缀：

```bash
HERMES_PYTHON="$PWD/.venv/bin/python" HERMES_TEST_FILE_RETRIES=0 scripts/run_tests.sh
```

五旧组当前 **62 个独立场景**均有有效 PASS：policy 20、config 15、receipt 9、deadline 5、state 13。因获批生产 Idle 修复，额外授权复测旧 runtime 中 **4 个相关节点**，共 66 个不同节点有有效证据。没有运行完整 runtime/timers/joint/host_wiring 或新 C4 组。

| 日志 | runner 参数（省略前缀） | 实际结果 |
|---|---|---|
| `baseline-tests.log` | 五旧文件全部 `-q` | 16 PASS/12 FAIL，另 2 文件 collection ERROR；3.9 秒。错误包括退出的两 profile/child compact import；不把 runner 的 failed 汇总当 collection 成功 |
| `repair-tests.log` | 五旧文件全部 `-q` | 58 PASS/3 FAIL；5.0 秒。所有本文件夹具/契约改写后首次运行；2 个真实单次决定回归，1 个错误 message/hint 字段的旧断言 |
| `config-final-tests.log` | `tests/secretary/test_noting_config_contract.py -q -k 'global_or_local_off'` | 3 PASS；2.2 秒，仅复测实际配置失败及相同参数分支 |
| `idle-regression-tests.log` | `tests/secretary/test_noting_deadline_event.py tests/secretary/test_noting_runtime.py -q -k 'actual_off_slash or only_deadline or idle_admits_after_the_delay or idle_requires_actual_length or idle_above_force_reserve or local_off_deadline'` | 6 PASS/2 FAIL；3.1 秒。修复后一次 local/admission 断言已通过；余 2 为新旧 Commit Gate 异常类型不一致，按 C5 实际精确错误修正 |
| `idle-commit-tests.log` | `tests/secretary/test_noting_deadline_event.py -q -k 'only_deadline'` | 2 PASS；2.0 秒，普通 Idle/升级 Force 均只读一次，关闭后禁止提交 |

macOS arm64，官方 PM `.venv` Python 3.14.7，runner 临时隔离 HOME/HERMES_HOME；无真实模型请求。6 本域文件 Ruff PASS；官方未修改 `scripts.code_health` 引擎限定该 6 文件对 HEAD 检查，0 blocking/0 advisory；`git diff --check` PASS。

证据：`.hermes-dev/round3-local-20261017-l0/L-D/c10-runtime/` 下全部日志、`ruff-final.log`、`health.log`、`manifest.json`、`c10-runtime.patch`。最终取证 HEAD `1aedf2de9f8c4ed10b9646d07afc0d462bad131d`；manifest 固定未提交六文件及依赖哈希，patch SHA256 `b4d535bf8b78f309cf357ced8dd53d4bc004315d5c5f44ce80e9066cdb78b9d8`。HEAD 本身不包含本包 patch。

中途按主会话 C9-H review 授权短暂回修 response gate，并已独立更新其报告/manifest；仅该包 23 响应/实际 carriage 场景复测通过，之后再次停止 C9-H 文件写入，不计入本包 66 个节点。

## 5. 缺口与边界

- 本包不是独立 Verification/Validation，也没有填写 validation.md。跨平台、真实模型、缓存命中和实际 Scheduler 到期尚无本包运行证据。
- C9-S 尚由主会话 review；真实模型只在主会话确认稳定待测提交并发出 start 后启动。届时遇到产品缺陷先提交精确路径/输入/日志给主会话，生产修复重新分配，不边改多包代码边混淆模型证据版本。
- D01 源事实、Force rewind 占用、完整 child 权限及五 Turn、多个渠道投递等有效新组证据按 C4/C5/C6/C7/C9 报告引用；本包不重跑，不将其记成额外新覆盖。

## 6. 精确接口影响

仅内部 helper 增加参数，无公开配置/数据库接口变更：

```python
_freeze_and_admit(db, conversation_ref, *, kind, frozen_identity=None,
                  participation_decided=False) -> NotingDecision
```

`participation_decided=True` 必须来自 `_idle_decision` 中成功的原子 `noting_idle_claim_event`；不是全局关闭绕过开关，不免除身份、Anchor、区间、来源、能力或 Commit Gate。没有新增表/线程/调度器/状态机。其余入口省略参数，默认保持原准入事务 gate。

## 7. 真实模型执行方案与后续动作（待 start）

拟由本 Agent 作为唯一 Development 真实模型 owner，避免多进程同时操作 round3。先固定主会话接收后的 SHA、依赖哈希和 round3 非敏感配置摘要；使用现有官方 PM `.venv`，只用原生 DeepSeek `custom/chat_completions`。统一启动包装器：

```bash
.venv/bin/python .hermes-dev/round3-local-20261017-l0/run-native.py .venv/bin/python -m hermes_cli.main
.venv/bin/python .hermes-dev/round3-local-20261017-l0/run-native.py .venv/bin/python -u -m tui_gateway.entry
```

包装器固定 `.hermes-dev/round3-runtime/profiles/round3`，只在子进程内存装载既有本地 DeepSeek key；不复制/输出凭据，不加载个人 Provider、不连真实 NM、不启动 App Server/Proxy，不改旧 Dashboard。RPC 显式 `profile:"round3"`；所有真实合成数据进入该 profile，不另起 L0 产品库。ignored 操作脚本只负责 JSON-RPC 驱动和证据记录，不替换 Agent loop、存储、模型返回或调度器。

拟按以下代表链路顺序执行，取证成功后复用同一对话和原生真实状态；不提前声称覆盖 validation.md 全部 15 组：

1. **正式入口与开关**：CLI 新会话完成一次实际 DeepSeek 回复；TUI stdio `session.create → prompt.submit` 创建后续样本，观察 `gateway.ready`、请求完成事件与真实物理 Session/Conversation Ref。用原生 slash/RPC `/noting off/on`、`/notebook`、`/propose-persistence`，以及原生配置切换检查三能力独立和 warm/cold 恢复。保持 provider 路由不变。
2. **连续材料与手动整理**：真实输入探访安排、委派、情景缺口、用户问题/认识/决定、被否决建议及后续纠正等合成材料；`session.compress` 或 CLI `/compress` 启动联合路径，观察父压缩无需等待 child、Noting 实际工具调用、Snapshot/audit 与完整 Framework 正文。再次输入纠正/完成/部分结算，检查 entry 身份和版本。
3. **工具协议与 prefix/usage**：保留实际 parent/child provider 请求、结构化 tool_calls/原生 dispatch 结果和 usage；优先使用既有 request dump/日志机制，仅提取 request body、去除 headers，不输出凭据。逐项比较冻结 root、工具 Schema、消息 content blocks 及每次 suffix，记录 cache usage 原值；字节一致不冒称 cache hit。若自然任务没有调用全部四工具，另安排使用同一真实模型/原生持久 child 的受控任务指令探针明确调用 show/History/maintain/finish；该补充标为开发协议机制证据，不冒充 CLI 用户验收。混批/overflow/五 Turn 的确定性机制继续引用已有正式路径证据，不用模型随机性重造竞态。
4. **跨压缩原文与 Proposal**：压缩前后要求模型用 `conversation_history` 找回“青鹭/截止周五→纠正周六”的原文及邻域，检查身份和排除控制消息；合法 Candidate 经 slash 生成提案，展示来源及版本，延迟/措辞修改不当批准；不写入真实外部目标。降低该隔离 profile 的 Proposal 阈值时记录配置与后续恢复，不改生产阈值。
5. **四入口代表链路**：manual 已在第 2 步取得；配置合法原生窗口/阈值后，通过真实长输入和实际 provider usage 将压力落在 Force/auto 区间，观察占用、实际成功压缩和新 boundary。Idle 显式开启短 delay 与合法实际 token threshold，通过 Main 结束后自然等待/新 Main 取消验证，绝不手工伪造 usage 或成功 receipt。若实际 API 容量/返回不足以覆盖，诚实记录，另保留同版本受控机制证据；不修改模型路由/适配来强行通过。
6. **Scheduler 实际到期**：让 Main 实际结构调用 `scheduler` 登记短时 deferred/instant、list/update/pause/delete；保持 Noting 关闭时再次登记以证明独立。通过同 TUI host 等待到期：idle instant 的 Main 唤起、busy 降为 pending、两条 deferred 在下一实际请求形成一 carrier 并 ACK；记录真实 Table/receipt/carrier 与完成事件，重启同 profile 读取持久排期和 Snapshot。必要失败时序引用 C6/C9-H 真实 DB/provider seam 证据，不伪造网络失败来污染正式样本。

所有输入、JSON-RPC 请求/事件、模型实际结构调用、usage、数据库身份与脱敏请求 body 写入新的 ignored real-model 证据子目录，报告列版本、控制边界、观察到的事实与缺口。启动前不执行上述命令或修改 round3 运行配置；主会话 review 本包及 C9-S 后确定实际待测 SHA 并发出 start。独立 Validation 保持另外执行者和报告职责。


## F14 最终回归剩余压缩六节点：原生夹具与ACP隔离依赖

1. **依据与范围**：以`ac7032be96114016bc26d1fa8825c4ba04b925f4`为回修起点，复用最终回归`compaction.log`／`failure-triage.json`六个精确失败，不重跑29文件／136文件。遵守未启用即原生及官方PM／现锁依赖契约，不修改压缩production或放宽断言。

2. **实际查因与修改**：`test_in_place_compaction.py`四失败的原始日志显示额外Noting失败Framework，导致same-session／flagoff行数及rotation-preflush次数变化、anti-growth原文比对多一条通知。`test_in_place_persist_marker.py`最初仅知5!=4，本包先在原失败节点补失败诊断，实际读出额外active行正文为NOTING RESULT、metadata含`noting_run_output:true`，不是compact dict重复写入。两文件各自`_make_agent`在所属临时DB目录写`noting.enabled:false`，使纯原生夹具明确关闭后台Notebook任务；保留全部原生active／inactive行数、FTS、same-session／rotation、anti-growth、marker、两次persist及零重复断言；只为原行数断言添加失败时tail正文／metadata诊断。没有删除、skip、xfail、alias或生产绕路。

3. **ACP正式环境**：原失败`test_conversation_compression_manual.py::test_every_surface_honours_preview_without_compressing[acp]`缺`acp`导入。官方`pyproject.toml:415`已声明extra `acp=agent-client-protocol==0.9.0`，现有uv.lock同版本；不是新增依赖／锁变化。获root协调授权后，以官方`pm.build_env`在ignored `compaction-repair/acp-env`创建独立Python3.14.7，groups dev/test＋extra acp，不使用裸pip/uv、无resolve、不动共享.venv。canonical runner显式选择该环境，仅运行ACP原参数。版本／source／准确PM命令／锁hash见`acp-environment.json`；共享.venv仍不能导入acp。环境构建成功日志保留，未单独计时构建过程。

4. **验证**：`persist-red.log`1F（整行列表被pytest截断，1.9秒）；`persist-red-detail.log`1F（精确tail与metadata反证，2.0秒）；修复后`native-green.log`9P＝五原native失败＋同构造helper四邻近节点（5.9秒runner wall）；`acp-green.log`1P（1.3秒，21个其余manual参数复用原有效证据）。共4次runner／累计11.1秒，最终本包**10 PASS**，六原失败均关闭；micro-compact独立helper未改，原1P复用。环境切换仅ACP单点，其它命令仍工作区.venv。

5. **缺口**：本包未发现需改压缩production的缺陷。Noting本身的开启／失败通知由既有C5–C9及真实模型证据覆盖，本包不以关闭Noting的native夹具冒称覆盖其开启行为。原manual文件无源码修改；此包只弥补ACP可选依赖的规范环境证据。

6. **manifest与检查**：测试改动仅两个in-place文件；精确六旧节点、所有命令／次数／日志hash、三旧文件最终hash、独立环境范围见`final-regression/compaction-repair/manifest.json`，最小两文件patch为该目录`final.patch`。与F15一起执行四变化路径Ruff、冻结scoped health（相对ac703）及diff-check，全部通过，**0 blocking／0 advisory**，0.419秒；不重复保留10类大型检查。

7. **停止／后续**：F14停止写入，交root集中review／统一集成；全范围门禁判定与其它owner旧夹具修复不在本包完成声明内。不stage／commit，不派生，不操作round3或模型；独立ACP环境留作ignored证据，后继可复用，不替换共享环境。

## F15 Scheduler run_at 可读时间投影

1. **条款**：冻结d19018的02 §5.6行1635–1637，07 §6.1行1054–1124、§6.2行1125–1135、§6.3行1136–1156；白板Scheduler独立语义。公开canonical规则及原expression保留，所有面向人／模型的绝对时刻为有zone秒精度，存储／推进精度不变。

2. **实际修改**：production仅`secretary/scheduler_table.py::schedule_public_conn`两行：已从DB JSON解码并validate的局部canonical副本若有run_at，调用既有`render_source_timestamp(...,profile_home=...)`（原生format_timestamp）生成可读值。不改DB canonical、expression、next_run_at、解析器、周期算法、claim／ACK、generation／sequence、Scheduler开关或Notebook状态。

3. **正式路径与反证**：新增`tests/secretary/test_r3_scheduler_time_projection.py`，真实SessionDB＋SchedulerStore的create→list→实际name update→同expression no-op四次正式操作均走统一出口。原生parser只在其现成clock依赖`cron.jobs._hermes_now`受控；显式带微秒ISO与相对`in 30m`均保留真实原生解析，分别覆盖UTC／Asia/Shanghai owner。RED四节点均明确run_at微秒654321／333333与已整秒next_due不一致。

4. **验证与副作用**：`v51-scheduler/red.log`4F（0.7秒）→`green.log`4P（0.7秒）；`affected-regression.log`既有CRUD／no-op不重解析且保claim／queued-once恢复／失败与末项删除notice四节点4P（0.4秒）。新例断言run_at与next_due_at具有zone、无小数且指向同一原瞬间的整秒；原display／expression及DBcanonical微秒、精确next_run不变。name更新只正常增加generation，不变sequence或next_run；no-op不重新解析相对表达、不更新任何定义行、不制造pending／Notebook。3次runner／累计1.8秒，最终本包**8 PASS**，未重复完整Scheduler或已有时间组。

5. **缺口**：无已知本包未关闭失败；不以本包定向证据替代独立Verification全范围复审或真实用户Validation。原生周期／due执行未改，继承既有有效证据，不为了可读投影重跑整组。

6. **接口／证据**：公开shape／字段不变，canonical_schedule.run_at展示为同一绝对时间的秒精度字符串；内部读取仍获得原始微秒canonical。准确SHA／命令／测试nodes／锁与scoped检查见`v51-scheduler/manifest.json`，最小production＋新测试完整patch在`v51-scheduler/final.patch`。此包不改`test_r3_scheduler.py`源码，只消费四个已明确影响节点；F14/F15合计定向有效并集18P，未开启第二次大型回归。

7. **停止**：F15停止production／测试写入，交rootreview并统一集成；无规则、规格、根文档、共享环境或其它production修改，无stage／commit／round3／模型运行。


### F15 root review 追加：canonical.display 绝对标签

1. **补漏来源／依据**：root review发现原生parser给显式ISO生成的`canonical.display`为`once at YYYY-MM-DD HH:MM`，仍属02 §5.6／V51规定的面向模型绝对时间；Astra已评审认可并记录verification.md §6.2。前一F15阶段只修run_at，且新测试把**公开绝对display等于原值**当成正确行为；该断言已撤销，不能据上阶段结果宣称最终display符合。历史“原display保持”仅继续适用于内部DBcanonical与相对标签，原expression始终保留。

2. **实际增量**：production仍只`secretary/scheduler_table.py`，在已validate的once局部canonical副本上，run_at投影后复用现成`hermes_time.readable_schedule_display`；只把`once at`绝对标签规范为有zone整秒。相对`once in 30m`由原生helper原样返回。没有改时间helper、原生parser、DBcanonical／原display、expression、due计算或投递状态。

3. **正式输出／断言**：仍用同四参数真实SessionDB＋SchedulerStore create/list/name update/no-op链；显式ISO公开display严格要求`once at 2030-04-06T12:30:00+05:30`，同时DB内原标签仍精确为`once at 2030-04-06 12:30`。两个owner timezone的相对标签要求`once in 30m`保持。实际name update的完整公开canonical必须等于create，no-op再等于update，故三个输出入口与无变化返回都覆盖；全部原DB精度／generation／sequence／pending／no-op不重解析断言保留。

4. **新增RED→GREEN与检查**：`display-red.log` **2F／2P**，仅显式ISO两个参数失败于缺秒和zone；`display-green.log` **4P**。新增2次canonical runner，wall分别0.7／0.6秒，累计1.3秒。只跑获授权四参数，没有重复F14或此前Scheduler四绿。本增量两路径Ruff PASS／冻结scoped health **0 blocking／0 advisory**／diff-check PASS，0.340秒。最终F15仍为8个有效独立节点，不能把同四参数重跑再计成新覆盖。

5. **缺口**：本次display反例关闭；公开／内部边界没有新增待确认产品扩展。仍不把定向测试当成全范围Verification复审通过。

6. **manifest与可review增量**：旧run_at阶段完整保存在`manifest-before-display-review.json`、`before-display-review.patch`及两个before-display源快照。当前`manifest.json`追加`display_review`，保留旧runs并更新最终完整hash；`display-review-delta.patch`仅含相对上次root review的production＋测试增量，`final.patch`为相对ac703的完整F15 patch。精确命令、日志、耗时、两路径检查与hash均落ignored，不覆盖旧日志。

7. **停止**：两源码／测试路径及报告停止写入，交root review／统一commit。F14已接收结果原样保留；无stage／commit、其它测试重跑、共享venv变更、round3／模型或大型检查。

## F19 hidden Anchor 压缩失效：提前收口（2026-10-17）

- 原真实d434ffd的admission15：raw21含human_only行643／644，摘要仅见19；归档却按raw末9行636–644撤掉尾部，而实际可见tail对应634–642。644无同UID有效替身，Full正确排除，child finish后被提交门禁abandoned。原生folded-away警告选中了隐藏/notebook回复，不是正常Main回复。原始state-after副本SHA与root提供值一致；只读调查见ignored `anchor-validity-repair/investigation.json`。
- production仅改`agent/conversation_compression.py`：Noting冻结先见raw，随后绑定可见压缩源和可见verbatim tail，摘要／candidate／reply／user后处理／held watermark／tail／coverage使用一致可见源；raw快照专用于回滚，当前Turn索引按投影重定位，拒绝／no-op比较可见源并返回原raw。hidden沿原生unseen clone保留，不改Snapshot gate、Foreground或pointer文件。文件物理行数回到原4498；最后仅删一空行，不影响已运行代码。
- 新`tests/secretary/test_r3_compaction_visibility.py`使用真实AIAgent、原生ContextCompressor／archive_and_compact／Noting worker与commit；仅summary／provider响应受控。末尾／中部／无hidden×full／here1六场景，含summary期间另写unseen输入、实际finish提交与下一Main API无泄露；另三项no-op／summary-failure／DB-failure原raw恢复。
- canonical runner依次：`red.log`初版6F（含两项错误地在wire读UID的测试观察错误）；修正观察后的`red-final.log` **3F／3P**，明确复现原abandoned及两中部hidden错误归档；初修`green.log`6P；补回滚检查`rejection-red.log`2F／1P；修正后`green-final.log` **9P**，runner wall依次3.9／4.6／5.5／2.2／6.9秒，共5次、23.1秒。命令统一显式工作区HERMES_PYTHON与RETRIES=0，经scripts/run_tests.sh选择该新文件；仅rejection-red加`-k rejected_visible`。不累计重复节点，不冒称真实模型。
- 用户要求额度前立即返回，现停止写入／运行。**未执行**Force旧节点、其它受影响原生邻域、Ruff／health／diff-check；未整理最终manifest／patch hash，未stage／commit、未动round3或源库、未新启模型或独立门禁。root需亲自review此当前patch与剩余证据缺口；本包不能宣称完整开发验收通过。


### F19 主会话单独补证（R3-022）

固定40f4ecceb772e6faaa98b99d95b8f4b0de5e31f0补齐原未执行邻域：canonical runner手动压缩选定节点9 PASS（含here N原生保留／轮换、未见输入、去重与中间空档），另一次无selector运行Force通知18 PASS与最后回复8 PASS，共35独立PASS，wall9.2＋6.3秒。首次跨文件带node selector实际只执行manual9，另两文件deselected，未误计通过；第二次只执行此前未运行的Force/reply。两日志与manifest在ignored solo-completion/，未重跑F19新9、F18的31或大型回归。生产未修改。统一新schema真实链正在同round3正式入口执行，尚不预判F16／F18／F19实测结果。
