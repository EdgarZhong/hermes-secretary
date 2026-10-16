# C10-T 六旧测试收口及 F10/F13 回修

状态：**DEVELOPMENT_READY_FOR_REVIEW**；六旧文件及F10/F13已收口，F11指定owner修复后最后定向节点通过。本域停止写入。未stage/commit/派生，未启动产品、真实模型、round3或NM。主会话亲自review后统一提交；不是独立门禁报告。

## 1. 条款与范围

依据冻结d19018白板A3/A7/N5/N6和07 §3（89–114）、§4.5（868–904）、§6.3（1136–1159）、§8.1/8.2（1237–1265）、§8.10（1319–1330）。继承04 §3（170–264）的真实Main及原生Prompt边界、§4.5 D01（294–316）实际请求来源和External只拒Noting/不拒压缩/suppression；02 §3.6（848–897）slash原生反馈/local独立/原文时间，以及04 §4.2实际248–257的人类视图不展示Snapshot/Anchor。新版类型、字段和Idle配置优先。执行前恢复根规则/CLAUDE、executing-plans、自主交接节、index/baseline/plan；旧报告只用于接口定位。

原白名单六文件中修改4个：`test_external_notice_v16.py`、`test_force_notice_compaction.py`、`tests/hermes_cli/test_noting_config.py`、`test_secretary_commands.py`。`test_timestamp_origin.py`、`test_usage_noting_isolation.py`原样保留并复用首轮通过证据。后续精确扩权F13只改`secretary/notebook_render.py::render_notebook`两行审计输出及`tests/secretary/test_notebook_render.py::test_human_and_model_views_are_complete_and_exclude_termination_audit`一个函数。

F10生产补线由root亲自实施：`secretary/noting_runtime.py::_dispatch_joint_decision`消费prepare时已解析ref，不在decision后重读owner；本子任务仅复测、记录hash/health。F11生产修复由local_environment独占，未修改其文件。F09已另交并由root提交43a38089e4，不混作本包实现。

## 2. 逐函数旧语义处置

没有删除测试、skip/xfail或恢复旧执行alias。

| 文件／函数 | 旧假设与替代覆盖 |
|---|---|
| external_notice `runtime/prepare` | Idle默认开、旧idle_delay_seconds退役；显式新idle.enabled/delay/threshold，沿native last_real_prompt_tokens读数。所有D01前置拒绝/owner/fence/队列/并发/suppression断言保留 |
| `test_external_trigger_glue_dual_writes_notice_without_noting_work[cold-catchup]` | cold新runtime须有原生measurement才能到达Idle长度gate，补实际测量接缝的受控读数；不越过gate或假称无测量也触发 |
| `test_real_idle_timer_external_rejection_publishes_once` | 现行nested Idle配置显式开启，保留真实daemon timer与at-most-once通知 |
| `test_actual_native_fallback_removes_only_queued_external_notice` | 去掉已退出Memo清空文案，仅作另一个合法producer的合成正文，仍核Native实际dispatch只撤External通知、不撤其他producer及真实UID |
| force_notice `runtime` | 配置改新Idle-off，DB放同一个home/config所属profile，保留真实native压缩/事务/lease/Foreground；日志转本轮ignored目录 |
| `_force` | 从固定“一生只有1个admission”改每次真实Force恰增加1个；适配同runtime先发生合法manual联合整理，不允许重复接纳 |
| `test_no_force_paths_keep_native_compression_and_capture_dormant` | 07要求普通手动压缩联合Noting，故保留manual admission并断言非Force通知/捕获；local off不新增admission，nonMain仍拒绝；再次真正Force前追加并持久化真实新Main输入，尊重既有Anchor去重；统一现行skip:not_main返回 |
| `test_next_interval_formal_force_producer_is_not_retired_by_old_attempt` | 保留下一成功区间必须可再Force；新增真实DB状态与Full summary UID观察，发现F11而未删断言/手工推进interval；后按owner确认改为boundary_message_uid匹配逻辑summary UID且opaque interval较prior变化，不强加interval等于UID的内部假设 |
| force_notice其他producer保留用例 | Memo完成文案替换为中性合成producer；依旧逐UID核成功退休Force、真实历史保留、其他正文不丢、失败/no-op不退休及同Turn续跑 |
| noting_config defaults/file/malformed | 旧3键退役，新Idle默认关/500/null、proposal12000/60、Scheduler独立默认开；修诊断标题大小写断言并保留parser失败关闭与Scheduler不受牵连 |
| `test_retired_noting_keys_fail_closed_with_explicit_replacement`（新增3参数） | 每个旧键都必须明确报removed和新位置；不能静默当alias或只改成永远off |
| secretary_commands `state` | Task-bound Store绑定真实Anchor，现行candidate及完整fields、真实来源、finish_noting审计字典提交；用另一真实assistant UID作为coverage，避免把条目正文应保留的source UID误当不可展示的envelope审计ID |
| `test_actual_invalid_capability_on_is_visible_and_does_not_write_local` | 现行坏Noting配置整体失败关闭；原生idle冲突时on/off/Notebook明确unavailable，不改local/config；能力阈值失败仍能off/读空Snapshot |
| `test_notebook_local_off_retains_human_snapshot_and_candidates` | 现行四数组板块和可读profile时间；保留不展示snapshot/anchor、显式具体内容/目标批准、local不影响读取/提案/工具和原config不变 |
| `test_usage_null_pointer_no_candidates_and_pre_turn_local_state` | 无Snapshot仍明确无Snapshot；已提交空Snapshot按07共用Proposal指令交Main诚实说明无材料，不沿旧候选专用短路返回 |
| `test_proposal_reads_only_candidate_leads_and_preserves_source_identity` | 07提案沿完整current Snapshot envelope与candidate条目，保留准确provenance与禁止slash读取原文/外部写入；不恢复memory_candidate/旧独立候选DTO |
| notebook_render授权单函数 | 人类仍含完整条目/source_time_range/来源，不含Snapshot/coverage头部审计ID；模型show独立保留精确snapshot_id和coverage；不禁止正文中的“source”文字 |

## 3. 正式路径与产品修复

六文件覆盖真实AIAgent请求/实际dispatch来源记录、daemon Idle、Framework原生持久与live队列、native in-place/rotation压缩、原始UID/时间、多模态/可信synthetic来源、child独立usage以及CLI `process_command`→持久反馈→下一真实请求。Provider只在受控模型边界返回，无真实模型/外网请求。

F10：真实`try_admit_force`返回External拒绝后切owner，通知必须不能跨Conversation；root将已有ref贯穿publisher。6个精确有效节点列于manifest；原race及Native恢复、并发suppression、队列失效、同runtime往返均保留。

F13：`render_notebook`仅删除Snapshot/coverage anchor两行，保留Created at和完整entries。`show_notebook`模型envelope及Framework实现均未改；三个定向节点通过，模型source range/immutable Snapshot和Framework完整正文保障未放宽。

## 4. 执行证据与有效并集

统一公共PM/canonical runner：`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh <本次指定文件> -q --tb=short --show-capture=no`；只有CLI最终取证使用`-v`，隔离home/DB均沿runner。没有direct pytest或大门禁。

| 日志 | 真实结果／处置 |
|---|---|
| baseline.log | 六文件87场景：60 PASS、17 FAIL、10 setup ERROR。runner估算~51及summary17不能替代真实含setup统计 |
| fixture-repair.log | config新14 PASS、CLI4 PASS/10 setup ERROR（审计metadata fixture仍旧）、External26 PASS/1 FAIL（cold缺usage） |
| diagnostic.log | cold补measurement后1 PASS；暴露F13、F11两生产反例；另一noForce负例继续补当前joint contract |
| remaining.log | CLI13 PASS；Force16 PASS/1 FAIL（现行skip:not_main正文）、已知F11/F13暂未选择；不是宣称全通过 |
| f10-f13.log | F10精确6 PASS、noForce新契约1 PASS、Framework1 PASS；F13剩coverage与entry source重名的fixture混淆1 FAIL，已分开真实UID |
| f13-final.log | 原F13失败、独立human/model投影、Framework完整正文共3 PASS |
| cli-final.log | shared state fixture最后版本14 PASS |
| f11-final.log / f11-final.xml | F11 owner完整交回后仅下一成功区间、in-place/rotation及no-op四个Force节点PASS；opaque interval较prior推进、boundary逻辑UID正确，实际下一Force可admit、新notice保留 |
| collection-only.log | 仅通过canonical runner收集精确node inventory，未执行test；runner将0已执行测试视非绿，退出1为预期，不列作PASS |

最终有效nodes及依赖hash见ignored `c10-t/manifest.json`；最终有效并集**92节点：六旧文件90＋相关human/model投影1＋Framework完整正文1**。F11修后只复4个Force节点，通过；时间16／usage1／config14与其余未受影响节点复用有效证据，没有凑整重跑。静态Ruff PASS；冻结health引擎限定本域及root F10：0 blocking/0 advisory；diff-check PASS。

## 5. 缺口及边界

F11初始反证见`diagnostic.log`：成功native压缩已出现真实Full summary UID，但Noting interval仍conversation_start，下一Force错误被occupied拒绝。local_environment修复后于完整交回信号后定向四节点PASS；`force-notice-boundary/next-interval.json`现为修后正向观察（同路径旧文件已被该次更新，不将其冒充保留的初始负例）。断言按opaque身份契约检查boundary_message_uid和interval变化，实际下一Force必须接纳；没有手工推进状态、删保障或恢复旧机制。当前本包无未关闭失败。

无真实模型、产品profile、NM、云端部署或独立门禁结论。C11-P继续等待round3独占start；其额外临时工具收窄将依主会话新指令在start前实施并纳同一备份/双hash恢复，本包不读改配置。

## 6. 接口与版本

本包不改工具/配置/parser/Loop接口。F13 `render_notebook(snapshot, *, profile_home=None)`签名不变，仅人类正文少两行审计头；root F10 `_dispatch_joint_decision(parent,decision,messages,expected_conversation_ref)`只在已有prepare caller传当前已解析ref，不新建权限来源。

起点e2fd9081；F09后增量检查基准43a38089e4，最终取证HEAD 4739b54896040be66c37c194d6b75dac2b675d97。本包代码仍未提交，manifest记录准确HEAD、六个本包修改路径＋root F10依赖hash、未修改的两基线测试hash、patch和日志hash。后继若公共继续提交，不以HEAD单独冒称包含本包差异。

## 7. 下一步

F11已完成最后定向复测，92有效node并集与精确文件/证据hash齐备。集中交root亲自review，本Agent已停止本包全部白名单写入；root统一提交/自动同步。继续等待C11-P正式start，不自行启产品或模型。


## 8. 最终回归修复（27 个非压缩失败／错误，2026-10-17）

### 8.1 条款与本包边界

首轮固定公共版本 `323c64dacba1190c16bacc69bbe5e76db6f43529`；直接复用 `final-regression/failure-triage.{md,json}` 与 loop/state/gateway 原始日志的 RED：23 FAIL＋4 setup ERROR，不为造 RED 重跑。依据冻结 d19018：07 §2、§3.1、§4.1–4.5、§5、§8.2/8.4/8.8、§9.1；白板 K1/K6/P3/N3；旧02身份、Foreground、跨压缩／rewind／fork §1–3.4及slash §3.6；04 Main History §3及child-parent权限 C13 §4.4/4.6。生产只读，不碰 compaction/ACP/V51 时间投影 owner。

### 8.2 变更及原节点保障

没有恢复退休执行名、删除主体断言或 skip/xfail。原生 no-DB Agent 本来不具备 Main 资格，不能只替换字符串后假设必有 History：native no-tools 用例直接断言真实空 catalog；Main reasoning 用例建立隔离真实 SQLite owner 后用既有 runtime surface 接缝授予 History，再实际执行原生 loop、两次 API、空 content、sidecar 和重放断言。它仍是原测试的返回 row／请求重放范围，`_persist_session` 沿原夹具受控，不将其夸大为新取得真实持久库写入证据。

Snapshot 两共享夹具仅给真实既存 Anchor 的合法空 Snapshot 补 `finish_noting` 非空 reason 审计；branch、rewrite、rollback、schema reopen 全部原断言保留。Gateway 夹具沿现行 task-bound Store＋真实 source UID＋candidate 完整字段＋合法 termination 发布；不再用旧 rule_candidate。History 改用 actual Agent、canonical ref/UID、合法 running Noting admission/child；Search 使用现行 FTS，明确拒绝 regex 参数而不恢复 regex。

| 原始精确节点 | 现行断言保障 | 结果 |
|---|---|---|
| `tests/agent/test_reasoning_only_stop_persistence.py::test_main_history_planning_reasoning_continues_and_preserves_sidecar` | 实际 SQLite Main owner 授予 canonical History；原生 loop 两次 API，空 content／reasoning+api_content sidecar 与下一请求逐字重放均执行。 | PASS |
| `tests/agent/test_reasoning_only_stop_persistence.py::test_promoted_reasoning_is_returned_but_persisted_row_keeps_content_empty` | 无 SessionDB 的 native/no-tools 路径保持；一次 API 返回 reasoning，assistant content 空，sidecar 与下一 Turn 重放均执行。 | PASS |
| `tests/agent/test_run_agent.py::TestBuildSystemPrompt::test_skills_prompt_derives_available_toolsets_from_loaded_tools` | 从真实加载的四个工具推导 web/skills 能力，不为无 owner 的 native Agent 伪造 Main History。 | PASS |
| `tests/agent/test_run_agent.py::TestTaskCompletionGuidance::test_no_tools_no_injection` | 无 owner、无工具时 task-completion guidance 不注入；断言真实空 catalog，不手工清空工具掩盖资格。 | PASS |
| `tests/agent/test_run_agent.py::TestToolUseEnforcementConfig::test_no_tools_never_injects` | 无 owner、无工具时 tool-use enforcement 不注入；真实原生 no-tools gate。 | PASS |
| `tests/hermes_state/test_secretary_foundation.py::test_carried_tail_rewind_and_anchor_same_transaction` | 同 UID carried tail 用 canonical identity 读回原文；真实 rewind 同事务移除 b，并保留 a／排除 summary Anchor。 | PASS |
| `tests/hermes_state/test_secretary_foundation.py::test_history_crosses_compression_uid_twins_and_real_tip` | 原生压缩及真实有效 tip 跨 Session 原文；两个同文不同 UID 命中不合并；FTS phrase/AND、角色、时间与 read 邻域。 | PASS |
| `tests/hermes_state/test_secretary_foundation.py::test_registry_inline_executor_and_noting_parent_scope` | 真实注册和 inline 执行；Main 跨 ref 默认拒绝；合法 running admission+child 仅读 parent；cross=true 仍不得读外域。 | PASS |
| `tests/hermes_state/test_secretary_lifecycle.py::test_branch_own_native_rewrite_does_not_revive_inherited_path[clear]` | 合法空 Snapshot/audit 后执行 branch 自身 clear/replace/rewind；旧 inherited path 不复活、parent 原文与 Snapshot 不变、再分支正确。 | PASS |
| `tests/hermes_state/test_secretary_lifecycle.py::test_branch_own_native_rewrite_does_not_revive_inherited_path[replace]` | 合法空 Snapshot/audit 后执行 branch 自身 clear/replace/rewind；旧 inherited path 不复活、parent 原文与 Snapshot 不变、再分支正确。 | PASS |
| `tests/hermes_state/test_secretary_lifecycle.py::test_branch_own_native_rewrite_does_not_revive_inherited_path[rewind]` | 合法空 Snapshot/audit 后执行 branch 自身 clear/replace/rewind；旧 inherited path 不复活、parent 原文与 Snapshot 不变、再分支正确。 | PASS |
| `tests/hermes_state/test_secretary_lifecycle.py::test_branch_partial_rewind_keeps_prefix_snapshot_audit_and_rebranches` | 保留前缀 a 的真实 Snapshot/audit，撤销 b，当前 pointer/Anchor/再分支均退回合法 a。 | PASS |
| `tests/hermes_state/test_secretary_lifecycle.py::test_full_annotations_are_consumable_but_never_messages_or_history` | 合法空 Snapshot 的 noting_anchor/notebook_snapshot 审计在 Full 可读，History 不混入 audit。 | PASS |
| `tests/hermes_state/test_secretary_lifecycle.py::test_native_mutation_pointer_failure_rolls_back_transcript_and_counter[clear]` | 合法 Snapshot 后让 pointer reconcile 真正抛错；rewind/replace/clear 原文、rewind_count 和 pointer 全回滚。 | PASS |
| `tests/hermes_state/test_secretary_lifecycle.py::test_native_mutation_pointer_failure_rolls_back_transcript_and_counter[replace]` | 合法 Snapshot 后让 pointer reconcile 真正抛错；rewind/replace/clear 原文、rewind_count 和 pointer 全回滚。 | PASS |
| `tests/hermes_state/test_secretary_lifecycle.py::test_native_mutation_pointer_failure_rolls_back_transcript_and_counter[rewind]` | 合法 Snapshot 后让 pointer reconcile 真正抛错；rewind/replace/clear 原文、rewind_count 和 pointer 全回滚。 | PASS |
| `tests/hermes_state/test_secretary_migration_lineage.py::test_legacy_branch_freeze_backfill_is_idempotent_and_atomic` | 保留既有 partial-schema/backfill 回归；真实 trigger 故障全事务回滚，重试幂等且不把 parent 后续消息重冻结。 | PASS |
| `tests/hermes_state/test_secretary_migration_lineage.py::test_native_branch_rotations_keep_ref_notebook_and_frozen_path[False-False]` | global/local 四组合均执行真实原生 rotation/native create/Agent 恢复；ref、Snapshot、local、冻结原文稳定，delegate/reset 不混 owner。 | PASS |
| `tests/hermes_state/test_secretary_migration_lineage.py::test_native_branch_rotations_keep_ref_notebook_and_frozen_path[False-True]` | global/local 四组合均执行真实原生 rotation/native create/Agent 恢复；ref、Snapshot、local、冻结原文稳定，delegate/reset 不混 owner。 | PASS |
| `tests/hermes_state/test_secretary_migration_lineage.py::test_native_branch_rotations_keep_ref_notebook_and_frozen_path[True-False]` | global/local 四组合均执行真实原生 rotation/native create/Agent 恢复；ref、Snapshot、local、冻结原文稳定，delegate/reset 不混 owner。 | PASS |
| `tests/hermes_state/test_secretary_migration_lineage.py::test_native_branch_rotations_keep_ref_notebook_and_frozen_path[True-True]` | global/local 四组合均执行真实原生 rotation/native create/Agent 恢复；ref、Snapshot、local、冻结原文稳定，delegate/reset 不混 owner。 | PASS |
| `tests/hermes_state/test_secretary_migration_lineage.py::test_partial_secretary_schema_upgrade_reopens_without_refreezing` | 保留真实 drop-table/reopen 两次的历史兼容回归；不重新冻结后来原文，Snapshot 与 ref 不变。 | PASS |
| `tests/hermes_state/test_secretary_migration_lineage.py::test_settled_open_with_real_branch_performs_no_writes_while_writer_is_held` | 真实 SQLite BEGIN IMMEDIATE 持 writer 时重开 settled DB；SQL trace 零写，frozen branch 原文可读。 | PASS |
| `tests/gateway/test_secretary_slash.py::test_canonical_prompt_keeps_original_identity_and_tail` | 真实 Gateway canonical dispatch：local off 反馈持久化；proposal 保留自然尾文/source/message identity、不预拼原文。 | PASS |
| `tests/gateway/test_secretary_slash.py::test_existing_plan_learn_and_review_routes_remain_canonical` | 既有 plan/learn/review canonical 路由保留，refine 退役不复活。 | PASS |
| `tests/gateway/test_secretary_slash.py::test_feedback_stays_with_command_conversation_if_route_moves` | 真实 dispatch 路由切换时反馈及 local 开关仍写原 Conversation，新 owner 未修改。 | PASS |
| `tests/gateway/test_secretary_slash.py::test_global_off_returns_unavailable_without_turn_rewrite` | owner profile 全局关闭时明确 unavailable，原 Turn 不改写。 | PASS |

### 8.3 路径及精确补丁

本包仅六个授权测试文件＋本报告追加；完整六路径源码 SHA256、原始 SHA256、补丁及证据指纹位于 ignored `final-regression/legacy-repair/{baseline.json,manifest.json,tests.patch}`。未修改 regression-plan、核心文档、其他报告、production、依赖、规则或其他 owner 文件。

| 测试路径 | 最终 SHA256 |
|---|---|
| `tests/agent/test_reasoning_only_stop_persistence.py` | `f4f906e94532e9db0e6b09d0baf3bb02d92263dbcd1966db3a555e6ee37d2633` |
| `tests/agent/test_run_agent.py` | `b554486d9832660063f77e626d6164d67b47364d2a25dfed896b3c7a4882d1c8` |
| `tests/gateway/test_secretary_slash.py` | `b6b1aa6ba6a5350eb2dfdcb89d1addc35d526837f8ba64e8597a6e2265193584` |
| `tests/hermes_state/test_secretary_foundation.py` | `a65af68498e2c757ef97dfa8b3c5cbf435209e782ae45cba2f552a44160e0683` |
| `tests/hermes_state/test_secretary_lifecycle.py` | `802b7c4ab6d1f41843bb0d9326d556707c0e9b8859b3289975c005ab94eaa353` |
| `tests/hermes_state/test_secretary_migration_lineage.py` | `104dcdc340b7da02acd62883e51f0df4c8ebf5fc2b4727e25f9abb8019795446` |

六测试文件 patch SHA256：`e69c6f2c5e92a01790d2757e29d0b097e2d0370a61ed27efb7abef23f72aa705`。交回时 HEAD `323c64dacba1190c16bacc69bbe5e76db6f43529`；工作区其他 owner 的生产与文档 dirty 保留，其精确观察依赖指纹另列 manifest，不归为本包改动。

### 8.4 执行证据与有效并集

统一官方 PM `.venv`，显式 `HERMES_PYTHON=/Users/edgar/code/hermes-secretary/.venv/bin/python`、`HERMES_TEST_FILE_RETRIES=0`，全部经 `scripts/run_tests.sh`。实际 argv／参数与时长见三个 invocation JSON；runner 将 node selector 转成函数 -k，本包参数全集与函数选择展开恰好相等，未选其他函数。

| 调用 | 选择／结果 |
|---|---|
| `green-first.log` | 原27＋下列两个受影响邻域：6文件29 PASS／0 FAIL／0 ERROR，runner wall 65.1秒 |
| `reasoning-final.log/xml` | Main reasoning 增加显式 DB finalizer 及退休名不在实际第二请求中的断言后，仅该1节点 PASS |
| `history-final.log/xml` | registry scope 增强具体 invalid_argument 字段，坏query/time邻域拆开具体错误字段后，仅该2节点 PASS |

有效并集 **29 精确节点＝原27＋受影响邻域2**；实际修后执行32次case，不把重复3次算新覆盖。首次并行调用共用 junit 路径被最后一个 per-file writer 覆盖，故 `green-first.xml` 仅7个 lineage 参数，**不是29项XML**；其余通过证据是原始 runner 逐文件数量＋精确选择表。最终两调用各有独立XML，不以缺失XML冒称未执行或重跑已通过组。

两个新增邻域只因实际改动选择：

- `test_bad_regex_and_time_fail_readonly`：共享 tool helper 从退休名 rejector 接回现行 handler，旧绿不能沿用；现在分别证明 regex 参数拒绝、畸形 FTS query、非法时间及消息数不变。
- `test_profile_database_isolation_and_formal_agent_initialization`：本文件正式 Agent 的 enabled_toolsets 迁至现行 History，须保留真实 identity 初始化及另一 profile 同 Session ID 不混库。

六路径 pinned Ruff PASS；六路径 `git diff --check` PASS。未重复全 test_run_agent、136文件、大门禁、Provider46/39、P2或其他既有效测试。

### 8.5 缺口／关闭情况

27原节点全部进入原主体并通过，无本包未关闭失败；没有需要扩权的新增生产反例。15个 Snapshot 初始错误和4个 Gateway setup 错误现在不再挡在主体前；reasoning 两节点实际执行1次／2次请求及下一请求重放，未只替旧名字符串求绿。schema backfill、持writer reopen、跨压缩 ownership 仍是有效回归，未以“开发不迁移”为由删掉。

本包不负责 ACP／5个压缩失败／V51 时间投影，不代替独立 Verification 或 Validation，不宣称整轮回归全绿。

### 8.6 接口

生产接口未改：`conversation_history(args, *, agent)`，anchored read 用 `{conversation_ref,message_uid}`；真实 Noting child 必须由 `noting_admit`＋`noting_child_register` 绑定 running task；`NotebookStore(..., anchor_message_uid=...)` 与 `commit(termination=...)` 按现行契约消费。两个低层合法空 Snapshot 夹具仅补现有 termination 参数。native no-owner 无 Main 自动工具；有真实 owner 的 Main 由既有 `apply_main_read_surface` 授予 History。

### 8.7 下一步

交 root 亲自 review 六测试路径、此追加报告及 manifest 后统一提交。本包已停止修改和测试，未 stage/commit、未安装依赖、未占 round3／启动真实模型／调用真实 NM。等待下一包正式个人授权与冻结后再开始，不提前处理 V51 candidate_index。
