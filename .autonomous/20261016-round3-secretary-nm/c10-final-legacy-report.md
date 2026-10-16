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
