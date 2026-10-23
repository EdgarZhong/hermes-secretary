# Verification：20261024-noting-fixed-tools

## 1. 审查对象与结论概览

审查者：独立 Verification（新上下文；不派生）。判据建立：2026-10-24。冻结基线 `56b7ebc01131ea4eaad0a4690c0bfbab048c2803`，授权追加 `3ce7517dc7c4e6dbdae7de1607032c8281ff0e24`；定位见同目录 snapshot-index.md、baseline.txt、user-request.md。待审 Core `4f503a22ca804b63717fda1104b6146420b525df`（产品与f841170一致）、Web `589df02706d3c6738789ff97fcb652a0bf76c398`。范围C01–C11；独立判据32条（初始28条＋交付闭包覆盖补录4条）；当前初审门禁不通过：32条中24符合、3有依据不适用、1违规、4证据不足。F01拒绝反馈契约违规及真实完整Idle/四工具/N46与最终收尾证据尚未齐备。生产部署尚未发生，本审查区分发布前符合性与发布后Validation。

## 2. 独立要求清单与覆盖

以下28条在读取实现、测试、动态看板或实现报告前独立建立。依据为指定版本用户原话、07（2026-10-24修订优先）、白板语义及06今日修订、部署SOP；索引只用于定位。07既有动态Schema口径由本轮用户明确替代，其它业务及原生不变量保留。C编号仅追溯授权，V编号是独立判据。弱细节处：可信身份的具体接线、旧pin构造边界、前缀wire作用域须据不变量反证，不能因规格未指定函数名而放过绕路。判据之后不依据实现降低。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| V01 | C01；需求1；07修订、§4.3/4.5 | 机制/全局Noting合格Main | 直接要求／必要保持：原Schema、description、参数及Provider转换保持；只改变注册位置 | 两canonical定义逐字段相等；无Provider转换改写 | §3 V01 |
| V02 | C01；07修订、§8.2 | 机制/工具发现 | 直接要求／必要保持：完整定义固定API顶层，禁止Tool Search折叠或消息级动态声明 | 实际Main/child请求顶层含两工具；messages[*].tools为空 | §3 V02 |
| V03 | C02；需求2；07§8.5 | 提示/Main | 直接要求／必要保持：Main明确两维护工具disabled且background Noting保留；其它能力保持 | 正式Root出现已确认英文句，原生其它工具可用 | §3 V03 |
| V04 | C02；需求3；07§8.11–12 | 提示/Noting | 直接要求／必要保持：任务作废父角色/策略并明确两工具enabled和仅四工具授权 | 初始/续Turn含权限控制及完整任务、工作视图 | §3 V04 |
| V05 | C03；需求4；07§8.12 | 机制/初始与续Turn | 直接要求／必要保持：不重复完整Schema；数据与指令分开；完整工作Notebook、时间和参数保持 | 初始及续Turn无callable_tool_schemas/重复定义，工作态含已有修改 | §3 V05 |
| V06 | C04；需求5；07修订、§3.1/4.5/5.1 | 权限/同步并发invoke间接调用 | 直接要求／必要保持：执行权来自真实运行时身份和绑定任务；模型内容或参数不能自授 | Main和其它child拒绝maintain/finish；Noting四工具外均拒绝，底层不能旁路 | §3 V06 |
| V07 | C04；07§4.5/5.1 | 身份/读取边界 | 直接要求／必要保持：Noting show取自身工作态；History只取绑定父；跨Profile/Conversation拒绝 | 不能借继承顶层Schema跨域或读父最新快照覆盖草稿 | §3 V07 |
| V08 | C05；需求6；07§3.1/8.2 | 缓存/构造到每个请求 | 直接要求／必要保持：父子Root/tools/冻结Active消息及缓存作用域结构一致，多模态保留；只追加任务控制 | 逐请求wire比对前缀；无child刷新MCP/Provider/记忆或重建Root | §3 V08 |
| V09 | C05；07修订、§12.3末段 | 生命周期/旧工具pin恢复 | 直接要求／必要保持：只在正常构造/恢复freeze前生效；旧缺维护工具pin补canonical，完整pin不改；旧Root/历史保留且sources如实 | 当前任务冻结后不热改；恢复工具pin来源及一次失效明确，无新恢复门槛 | §3 V09 |
| V10 | C05；07修订、§3.1/6.3 | 关闭/资格/兼容 | 直接要求／必要保持：全局关闭、非合格身份保原生；local参与开关不改变Main工具前缀；History/Scheduler独立 | 开关/身份矩阵通过，非Noting其它原能力无退化 | §3 V10 |
| V11 | 保留07§3.1–3.2/4.5；白板K6/N1 | 结束/并发 | 直接要求／必要保持：finish最后单独调用；混合批整批拒绝；结束锁固定视图；原生Turn返回后Commit Gate提交 | 同步并发混合无副作用；结束后写拒绝、重复finish幂等；文本done不能正常结束 | §3 V11 |
| V12 | 保留07§3.1–3.2/8.13 | 预算/失败/释放 | 直接要求／必要保持：最多五Turn、不自行压缩；预算/overflow可保存合法完整状态但标forced/overflow；一般错误可无快照 | normal/forced/overflow/API异常/取消行为与资源释放不变，不能forced冒称正常 | §3 V12 |
| V13 | 保留07§3.1/8.13/11.1；白板N3/P3 | 持久/并发/历史状态 | 直接要求／必要保持：原子校验参与/Anchor/版本/来源，旧Anchor不得回退pointer；仅新生效结果通知且追加时复核 | 提交与通知有效性接线、关闭/rewind/fork/旧结果晚到不被新工具面绕过 | §3 V13 |
| V14 | 保留07§8.1；白板P2 | Idle/其它触发 | 直接要求／必要保持：Idle需相应Noting正常提交才full compaction，Framework在压缩后；其它压缩/Force原机制保持 | 失败/forced/overflow不触发Idle压缩；已有任务复用按运行/正常/失败分别处理 | §3 V14 |
| V15 | 保留07§4.1–4.4；白板C1–9/L/E/N | Notebook保留语义 | 直接要求／必要保持：原文为事实源、稳定ID/版本、来源合法、Candidate二选一/结算、用户认可范围不变 | 无改Schema/内容语义；真实任务合法Notebook与Snapshot，不能凭新注册扩大写入范围 | §3 V15 |
| V16 | C06；需求7–8 | 真实模型/隔离 | 直接要求／必要保持：Alex独立Home/runtime/DB、仓库外cwd；实际kimi-for-coding；保Persona/业务Prompt，仅授权提示增量 | 隔离创建/配置指纹/实际Provider模型wire与生产无写入证据可复核 | §3 V16 |
| V17 | C07；需求8–9 | 实际用户链路/模型行为 | 直接要求／必要保持：小阈值只限隔离；自然Main行为误调用率与受控拒绝分开统计；任务正常finish及用户工作完成 | 真实Main→Noting→合法Snapshot→压缩/Framework代表链路；错误被Harness拦截后纠正 | §3 V17 |
| V18 | C07；需求8–9 | 真实工具协议 | 直接要求／必要保持：无重复Schema时真实Noting仍能实际调用四工具；不以声明/受控mock当实测 | 四工具真实执行记录和正常finish；如单轨未用齐须另取真实代表记录 | §3 V18 |
| V19 | C11；追加需求；07修订 | 真实长上下文 | 直接要求／必要保持：超过原N38的N46代表点，报告该模型真实Usage；不先压短；任务转换后固定工具可用正常完成 | 实际kimi-for-coding长Main/Noting wire、Usage、工具回执及正常提交证据 | §3 V19 |
| V20 | C08；需求10；06§1.4第271行 | 今日修补/微信 | 直接要求／必要保持：active中每条完整正式Assistant及时按序投递；redirect未发半截合并同通知，已发不重复，无Thinking外发 | 完整消息/工具前正文/redirect半截/空正文/纠正后回复及上下文事实保留证据 | §3 V20 |
| V21 | C08/C10；06§1.4第273–279行 | 今日修补/前端消息 | 直接要求／必要保持：来源包裹/Thinking/Timeline保留；failed_turn只由实际诊断行元数据分类，无turn_terminal合成兜底；slash/真实正文保持 | 正式后端元数据→前端分类→渲染接线；旧无类型不猜，真实部分回复不误分 | §3 V21 |
| V22 | C08；06§1.4第277行 | 今日修补/Heartbeat | 直接要求／必要保持：仅完整user heartbeat包装分类，原文/身份不变；默认折叠、标题图标陶土橙主题、展开保内timestamp | 前端真实组件和分类边界；不处理HEARTBEAT_OVER或添加行为 | §3 V22 |
| V23 | C08；06§1.4第281–283行 | 今日修补/审批 | 直接要求／必要保持：移动/桌面主题排版改善；Patch replace仅已有唯一owner待处理参数预览，文本转义，可空new删除；无新增接口/权限 | 当前owner配对、缺参/歧义回退、非Patch/Clarify保持；真实组件手机/桌面证据 | §3 V23 |
| V24 | C08；需求10；06§1.2第195行 | 交付范围/APK | 直接要求／必要保持：599d114后端/589df02前端同批交付；既有0.1.4竖屏APK不自动装用户手机 | 目标版本含今日修补，前端产物绑定；APK范围不被扩大 | §3 V24 |
| V25 | C08；部署SOP§0/2/6/8 | 发布能力与实际部署分层 | 直接要求／必要保持：先固定Core/UI/dist/PM-lock/配置/SOUL指纹、可恢复快照；活动工作结束才停唯一后端升级；失败保数据可回滚 | 发布脚本/操作计划可审；生产实际版本与保护收据由部署后Validation核，不以本地代签 | §3 V25 |
| V26 | C09；需求11 | 流程/模型/显示/门禁 | 直接要求／必要保持：Sol子Agent不Astra、不再派生；仅自建隐藏IAB；冻结十检查及等级不改变 | 编排模型/工具操作/规则diff与有效检查证据，未验范围如实标注 | §3 V26 |
| V27 | C10；需求8/12；07修订 | 禁止范围/数据保护 | 直接要求／必要保持：不动生产历史排期绑定、不重跑旧失败、不恢复47错误时间；不带隔离配置/库/凭据/Persona/raw wire入Git或生产 | 变更范围及测试/部署输入无上述内容；保密证据仅ignored目录 | §3 V27 |
| V28 | C08；需求10及仓库流程 | 交付/提交push | 直接要求／必要保持：生效范围变更统一提交干净push，部署版本精确绑定，旧今日修补不得漏发 | Git ancestry/dirty/远端绑定与发布包闭包一致；部署实际另由Validation核 | §3 V28 |

判据覆盖反查补录（实现调查初期）：原第2节V24对冻结需求10指定的599d114／589df02闭包只列合并交付，未逐项展开标题、wire、时间与Context。现保留V01–V28全部原判据，依原需求的精确交付范围及06既有事实契约补V29–V32；这是覆盖细化，不以实现解释替代用户目标或降低判据。V21–V23为06既有保留回归，未要求重新制作旧UI项目或重复昂贵验收。V06拒绝反馈同时继承07§7.2固定code/message/next_action，无权限扩大。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| V29 | C08；冻结需求10精确绑定599d114；运维记录2026-10-23已审修补口径 | 今日闭包/Kimi wire | 直接要求／必要保持：只对可信官方Kimi Chat URL更名输出字段；非可信URL/其它Provider/override优先级/fallback保持 | Main/aux SDK真实序列化只有一个输出字段，内部预算及其它协议不变 | §3 V29 |
| V30 | C08；冻结需求10之599d114标题修补；06原生title控制契约 | 今日闭包/标题 | 直接要求／必要保持：K3与带Provider前缀变体沿原生温度省略、oneshot及标题写回，不改其它模型默认 | 实际RPC→原生aux→SDK→session.title→DB/info及自动标题，失败保旧值 | §3 V30 |
| V31 | C08/C10；冻结需求10之599d114；06§1.4时间事实契约 | 今日闭包/timestamp | 直接要求／必要保持：压缩复制保持原消息authoring time和UID；新摘要/新输出仍是新时间，不恢复生产47旧行 | 原地/covered/rotation及full/cards/details/resume均保持，UID优先、显式时间不改、错误回滚 | §3 V31 |
| V32 | C08；冻结需求10精确绑定589df02；06§1.13/1.14 Context事实契约 | 今日闭包/Context显示 | 直接要求／必要保持：压缩完成只取当前owner正式Context，不以临时unavailable清掉旧有效值；显式invalidated仍清除；迟到不能覆盖新值 | 正式CompactionViews→ContextAfterCompaction→controller；并发/切换/重连/字段部分返回回归 | §3 V32 |

## 3. 逐条实现证据

本表为4f503a2初审事实，F01修补及T3真实执行材料尚待交回；每行解释见第2节，代码与证据用于验证事实，不反写判据。证据相对前缀为`.hermes-dev/noting-fixed-tools-20261024/`，另有显式旧包路径。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| V01 | secretary/noting_contract.py；noting_surface._read_schema；Moonshot/Anthropic转换owner未改 | 冻结→待审git diff为空；canonical SHA与用户冻结二值一致；真实SDK fixed_permissions检查每字段 | schema-before-sha256.json；root-integration.log；verification/independent-hash-check.json | 符合：原定义和转换未改 | 顶层列表新增会使旧工具前缀一次变化，未声称旧缓存字节相同 |
| V02 | apply_main_read_surface→filter_tool_definitions→tool_search.main_tool_is_direct→request assembly | 正式AIAgent/SDK受控HTTP验证Main与child四工具完整顶层；显式defer仍不能折叠；noting_request旧动态函数已删且无引用 | runtime/final-permissions.log；prompt/final-requests-tests.log；root-integration.log | 符合：完整固定顶层，messages无tools声明 | 实际模型wire待V16–19核 |
| V03 | agent/system_prompt.NOTEBOOK_GUIDANCE→turn_context→synchronize_main_read_prompt | 原文禁用句逐字加入；global on/off/local与冷root恢复测试；旧Root一次重建后warm请求保持 | tests/secretary/test_fixed_noting_request.py；prompt/final-requests-tests.log | 符合：准确禁用且不改其它Main段落 | 当前合格Main/全局门禁，非全局默认注入 |
| V04 | noting_prompts.DEFAULT_NOTING_TASK_INSTRUCTION/CURRENT_NOTING_CONTROL/CONTINUATION→runner | 三段与07修订逐字相等；父system/角色/规则/策略/任务/完成条件作废；原六步任务其余逐字保留 | prompt/receipt.json；tests/secretary/test_fixed_noting_request.py | 符合：身份切换与四工具授权准确 | 此项证明Prompt接线，执行另见V06 |
| V05 | noting_tools.noting_tool_control_message→_working_control→_run_child_turns | 仅删callable_tool_schemas；完整working_notebook与task_parameters/current_time/evidence_coverage保留；真实Loop两Turn检验先前修改仍在 | prompt/final-requests-tests.log；tests/secretary/test_noting_dynamic_tools.py | 符合：初始/续Turn无重复定义且工作态完整 | History返回正文中的历史Schema属于证据，不是新增注册 |
| V06 | turn_tool_validation.secretary_validation_refusal→parser→sync/concurrent→resolve_invoke_tool_executor→scoped_registry_dispatch→_bound_store | Main/普通child拒绝两维护；Noting白名单仅四，解包前拒绝tool_call/tool_search、拼写修复前后拒绝、prechecked invoke仍守卫；真实Loop/DB无写；但拒绝回执缺固定字段 | tests/secretary/test_fixed_noting_permissions.py；runtime/final-permissions.log；verification/permission-error-contract.log | 违规：F01权限有效但07§7.2回执不符合；独立1 failed反证 | 待主会话提案修补全部入口，不能用有效拒绝掩盖错误契约 |
| V07 | noting_tools._bound_store/notebook_work_show；tools/session_history_tool；_bind_child_identity | Store须真实锁对象及父ref相等；show工作态不能选scope；History绑定父DB/ref；现有全局Main跨域不授予child | runtime/runtime-tests-1.log；runtime/runtime-tests-2.log；tests/secretary/test_noting_child.py | 符合：旧可信绑定保留，四工具执行仍归父域 | 未扩大跨Profile授权；不把Schema字段当权限 |
| V08 | freeze_parent_active_prefix/freeze_parent_runtime→cache_parity→assemble_api_request/iteration_summary | 父运行态先freeze，tools/root深拷贝、cache scope及frozen前缀保留；正常/summary/retry/延迟启动/多模态、OpenAI及Anthropic SDK有针对性证据 | prompt/final-requests-tests.log；prompt/third-tests.log中cache_parity11与summary4已通过文件；tests/secretary/test_noting_dynamic_tools.py | 符合：机制与受控SDK逐请求前缀一致 | 真实kimi字节/结构另待V16–19；prefill/multimodal只用受控SDK取证 |
| V09 | start_recovery._prepare_fixed_recovery_tools→parent_factory→freeze_parent_runtime→run_noting_task | 只补缺失canonical；完整pin不变；sources.tools注明补齐及非旧wire字节相同；旧failed row/root/suffix保留，幂等key/租约/资源释放沿原生 | tests/secretary/test_noting_recovery.py；prompt/final-recovery-tests.log；root-integration.log | 符合：freeze前恢复适配，无新恢复门槛 | 未重跑生产任务，重启状态interrupted不自动恢复 |
| V10 | noting_surface.notebook_read_enabled/apply_main_read_surface→Main资格；local开关与noting_trigger_gate分开 | global off去两定义、History仍有；local off不改Root/tools；sideagent/aux/branch/reset/compaction cold/warm已在surface33与固定测试核 | runtime/runtime-tests-1.log；tests/secretary/test_noting_surface.py；root-integration.log | 符合：原生能力及独立开关保持 | 原生其它Provider行为只按变更影响核，不重复全量 |
| V11 | secretary_dispatch.reject_noting_mixed_finish/secretary_validation_refusal→guard_noting_tool_batch→finish_noting/store.lock→runner | 完整批预检早于repair/执行；正常end_requested固定状态、后写state_conflict、重复finish保首reason；原生Turn返回才_commit_when_complete | runtime/final-permissions.log；tests/secretary/test_fixed_noting_permissions.py；noting_tools.py:115 | 符合：finish单独与状态冻结保持 | 不得将end_requested当committed；真实结束待V17–19 |
| V12 | _run_child_turns/_force_task_close/_commit_when_complete→finally close | 五Turn/50 iteration、context overflow兜底；一般API失败无新Snapshot；非正常终止不伪报finish；DB/clients/admission/强引用在finally释放 | runtime/runtime-tests-2.log child38；prompt/third-tests.log r3_child54有效文件；root-idle-integration.log | 符合：保留结束/预算/失败/释放机制 | 历史第三次整命令含fixture失败不算全绿；只复用已通过文件及最终修正文件 |
| V13 | commit_noting_snapshot→db._execute_write→notebook_commit_snapshot_result_conn→pointer重选→publish_noting_completion→append-time predicate | 同事务核开关/anchor/合法state/来源版本并插完整Snapshot；pointer_changed false不通知；实际追加在framework→persist→DB锁核仍current；未改fork/rewind ownership | secretary/noting_child.py:513；hermes_state_secretary_notebook.py:235；framework_messages.py:333；runtime child38与surface33 | 符合：新工具面仍落原子门禁，未绕过pointer | 全量fork/rewind并非本轮重做；相关owner未改且表/契约保持 |
| V14 | Idle timer→prepare_joint_noting→existing admission/child→normal commit callback→request_context_compaction wait→Framework | 正常finish+Snapshot才callback；已有running等、正常已完成压缩、失败/forced不压缩；relevance check区间及owner；native completion事件而非admission才释放通知 | tests/secretary/test_idle_noting_commit_order.py；test_idle_noting_reuse.py；root-idle-integration.log 43通过；旧repair-review-20261023-idle-integration.log含native36 | 符合：Idle成功前置与其它compaction独立性落实 | 自动/手动/Force原机制保持；一般API失败可无新Snapshot |
| V15 | NotebookStore/notebook_items/noting_contract→maintain→Commit Gate；完整Noting六步Prompt | 定义、Notebook语义校验及原六步内容未改；读/写/finish实际SDK与DB受控链可得合法完整Snapshot，无外部Memory写 | schema diff为空；runtime/final-permissions.log；prompt/final-requests-tests.log；noting_prompts.py | 符合：本轮保留内容语义，Schema与owner未被改写 | 不据受控单样本声称模型每次均正确萃取全部七类；真实任务质量另核 |
| V16 | T3 prepare._make_agent→原生Profile/provider→独立Home/runtime/DB/cwd | 已核准备脚本及source前后指纹；实际run-short-20261024-011441仓库外全新Home/runtime/cwd/DB，SOUL指纹相等，真实wire业务请求kimi-for-coding/high；仅隔离差异，禁MCP/微信，无源DB复制 | e2e/preparation.json；e2e/prepare.py；e2e/run-short-20261024-011441/manifest.json；verification/short-independent-audit.json | 符合：隔离与实际短请求已核；长样本另列V19 | 源cwd本机不存在，未编造线上workspace AGENTS；外部MCP禁用不声称线上工具全复刻 |
| V17 | 正式Main→Idle timer→Noting→native compaction→Framework→Main | 首短8HTTP200，5自然Main/5Turn零维护误调，Noting1Turn正常finish空Snapshot、Framework1；独立从实际wire重算root/tools/Active及最后Main前缀均相等；但4→4手动压缩no-op引structural_backoff，Idle仅尝试未压缩成功 | e2e/short-stage-report.md；run-short-20261024-011441/audited-receipt.json；verification/short-independent-audit.json；V06/V11–14机制证据 | 证据不足：短链缺实际Idle父压缩与跨压缩Notebook承接；自然小样本已如实统计 | 自然0误调不能替代确定性拒绝；forced不能代正常 |
| V18 | 四工具原生dispatch→真实Provider模型结果→工具回执 | 受控真实Loop四工具均可执行；真实短Noting只调用finish_noting一次，History/Show/Maintain均未用；不把schemas存在当已实用 | runtime/final-permissions.log；e2e待交回 | 证据不足：缺真实四工具覆盖及正常完成材料 | 若自然轨迹没用齐，需明确真实覆盖缺口，不能伪造或受控冒充 |
| V19 | kimi-for-coding长Main→manual compaction前freeze→Noting | N46准备存在且计划实际Usage/wire、不先缩短；尚缺实际长请求及结束审计 | e2e/long-history-n46.json；e2e/preparation.md | 证据不足：C11实际长样本未交回 | 不能套K3旧Usage或拿短请求代签 |
| V20 | TurnRunner capture/message callback→GatewayStreamConsumer FIFO→Weixin adapter；redirect receipt→checkpoint→FIFO | 完整UID消息按序；capture与投递分离；writer/turn fencing；同文不同UID分别发、final按成功UID+payload去重；半截清洗后合并同redirect通知，不进模型回复 | weixin-message-final-integrated.log 56通过；weixin-message-explicit-streaming.log 31通过；verification/independent-hash-check.json全部15文件一致 | 符合：微信原生链路受控SDK/adapter整链证据支持 | 未真实向微信发送；外部不确定结果仍最佳努力，不承诺exactly-once |
| V21 | 原Framework/来源/Thinking/Timeline owner；589df02无此类生产改动 | 来源包裹候选已撤回，git diff闭包只有Context与时间测试/APK；06第279行失败卡保持既有元数据分类，无新增后端/前端消息机制 | 599d114/589df02 diff；docs/operations-log.md撤回记录；projection.ts:339 | 有依据的不适用：既有完整失败卡UI重验不属本轮新增范围；本轮未改该机制 | 保留约束已查变更未触及，不将早期全UI项目并入新施工；今日微信输出仍按V20核 |
| V22 | 既有projection完整user heartbeat识别与既有卡片 | 589df02未改该产品；原user完整wrapper分类仍在，来源角色/内容不变；未新增HEARTBEAT_OVER处理 | projection.ts:344；589df02生产diff | 有依据的不适用：既有Heartbeat视觉全验不属本轮新增范围 | 保留回归仅审无行为改动；不冒称本次重新UI验收 |
| V23 | 既有approval/patch preview组件 | 599d114/589df02未改审批或Clarify，未增加后端接口/权限/choice；原生批准机制不受固定Noting工具权限变更 | 双仓固定diff闭包 | 有依据的不适用：旧审批弹窗/截图项目不在本轮新增范围 | 未重新UI截图，未据源码冒称旧视觉验收重新通过 |
| V24 | Core git ancestry＋Web589df02→439 dist；Android Manifest/MainActivity | 当前Core包含599d114；Web固定589df02且clean；dist源commit/439files绑定；APK0.1.4 hash独立重算相等，portrait/1004/nondebug签名收据 | verification/release-static-receipt.json；frontend-manifest.json；android-apk-20261023/package-verification-0.1.4.json | 符合：今日修补在候选闭包，APK已有竖屏包 | 没有安装用户手机；本轮Web新构建与既有APK分别追溯，不等同手机真机测试 |
| V25 | 发布计划T4→首尔正式SOP→preflight；生产部署尚未执行 | 亲读发布脚本：精确目标祖先/HEAD/锁与pm复用、保护表指纹、活动租约/Noting拒绝、停两专属服务后SQLite备份、ff-only、Linux原子目录交换与分别finally启服、失败保新数据不盲回滚；dist439独立解包集合/SHA全等；preflight旧e9de406 | plan.md T4；cloud-preflight.json；release/deploy.py/remote_release.py/PREPARE.md/selfcheck-receipt.json；verification/release-package-independent-audit.json；部署SOP§0/2/6/8 | 符合：发布能力及保护计划可审；生产实际验真交部署后Validation | 不是已部署完成结论；生产版本/配置/数据/服务实际差异必须后续验真 |
| V26 | 本轮委派记录与冻结检查入口、实际工具使用 | 独立审查未派生/未UI/未收费API；本轮scripts/check与lock/规则入口diff为空；root staged frozen10全部通过0/0；实现报告Sol/high | root-staged-check.log；verification/independent-hash-check.json；plan.md编排 | 符合：当前所审流程证据未见改门禁或显示边界 | 不从子Agent自报推断未记录外部行为；只读审计可得范围 |
| V27 | 双仓tracked diff及T3隔离脚本/发布输入 | 本轮只改受授权代码/文档/测试，private Persona/raw wire/credential/DB不入tracked；恢复调试只改构造兼容，未调用生产重跑；源文件只读保护 | git diff范围；e2e/preparation.json/prepare.py；cloud-preflight.json | 符合：当前实施及准备未越数据边界 | 生产保护最终值在部署后Validation；不预签未来操作 |
| V28 | core upstream4f503a2；Web upstream589df02；当前报告/修复尚在推进 | 原生闭包已commit且当前upstream一致，祖先599d114在；既有两untracked稿保留；F01修复和本审查未提交，发布未发生 | verification/release-static-receipt.json | 证据不足：最终生效修补提交push和部署闭环尚未收尾 | 不能把祖先已push当整轮最终clean/已部署；留后续收尾核 |
| V29 | utils.is_official_kimi_chat_url/normalize_kimi_chat_output_overrides→Main _max_tokens_param→chat kwargs；aux build/402retry | 可信https精确host/path/443无userinfo/query/fragment；copy-on-write override/extra_body保优先级；其它Provider与Responses/Anthropic保持；旧生产6文件SHA一致，本轮58 wire通过 | tests/agent/test_kimi_output_tokens_wire.py；root-integration.log 58；kimi-output-wire-20261023/files.sha256；utils.py:757 | 符合：仅确认端点输出字段兼容，内部预算和fallback未改 | 不声称仅改字段解决N38动态声明400；旧动态39用例已被本轮替代 |
| V30 | auxiliary_client._is_kimi_model→_build_call_kwargs→llm.oneshot→session.title/info→DB；自动title prologue | K3/k3-*/provider前缀走原生温度省略；真实RPC/aux/SDK受控HTTP与真实SessionDB验证生成非持久、确认写回、自动标题回调；失败保旧名 | tests/tui_gateway/test_ai_title_native.py；apk-title-20261023/title-native-final.log 5通过；temperature-regression.log 4通过 | 符合：标题兼容/写回正式链路完整 | 无真实Kimi标题质量评估；本轮不在线改名 |
| V31 | hermes_state_messages._carry_parent_timestamps→archive_and_compact/covered/publish_compression_child→full/cards/details/resume | UID优先且同文反序不会串时间；未知UID不借时间，显式timestamp保留；active归档前补time、异常恢复调用方；所有投影真DB检查 | timeline-timestamps-20261023/receipt.json哈希3项全一致；backend-tests.log 104；tests/hermes_state/test_compaction_timestamps.py | 符合：新压缩复制继承源时间，不恢复生产旧行 | 旧47错误历史修复不属授权，本轮没有迁移 |
| V32 | CompactionViews.readContext→ContextAfterCompaction.read/observe→controller | unavailable不删pending/不invalidate旧值；显式context_invalidated处理；token/owner/lifecycle/revision拒绝迟到；已观察字段不被旧read覆盖；正式controller相关测试 | Web src/core/compaction-view.ts/context-after-compaction.ts/controller-context-compaction.test.ts；frontend-manifest/build；frontend-context-test.log当前589df02正式controller50通过；frontend-context-receipt.json；verification/context-independent-hash-check.json四项全真 | 符合：正式controller50项覆盖保留值/迟到/owner/显式失效，源码与日志哈希已核 | 本轮不是新造Context cache；不以单纯build当并发恢复测试通过 |

## 4. 核心目标及验证方法审查

核心机制从正式AIAgent构造/恢复到provider顶层tools，经validator、完整批预检、同步/并发parser、inline/registry和真实绑定Store贯通，权限不由模型参数或正文决定。固定Schema与Main执行名分开，Noting工具定义继承父冻结数组但执行名精确四个。初始/续Turn仍附完整工作Notebook，动态注册已退出正常及summary接缝；缓存归一化继续区分父前缀/子后缀，恢复旧pin只在freeze前补齐且来源明确。

反证问题已检查：tool_call/tool_search先解包会否绕过（原名先拒绝）；拼写repair会否提权（前后策略校验）；pre_tool_block_checked会否旁路（inline仍检查）；已有Store能否给普通child写权（marker/lock/ref共同检查）；local开关会否变工具prefix（不会）；旧pin缺Schema会否加恢复门槛（不会）；文本done/forced会否冒正常finish（不会）；晚Anchor/排队通知会否回退（Commit Gate与实际追加pointer复核保持）。发现F01说明测试虽能证明拒绝，不足以证明07完整错误契约；独立负对照实际失败，能识别这类错误实现。

已有测试底座主要只控制SDK I/O，实际Loop、SDK JSON、DB、admission、Store、Commit Gate及后台线程运行；部分失败矩阵故意控制child返回类型，这可验证父状态机，但不冒称真实模型错误频率。正式SDK多协议/多模态检验证明结构保留，不代表实际Anthropic在线可用。本轮真实Kimi由单owner负责，当前未交回，不使用受控轨迹替代。旧包证据按文件哈希复核复用，Kimi旧dynamic测试已变更不沿用其39通过，而用本轮新32/116集成接续；无无关大套重跑。

检查冻结入口、lock、Provider Schema转换与canonical文件无变。微信发送证据为真实SDK流/原生Turn/consumer/实际adapter模拟发送，支持正式接线与顺序，未发送真实微信；标题证据为原生RPC与持久化、SDK受控响应，不声称模型标题质量。UI范围按固定589df02交付闭包审查；旧完整Heartbeat/失败卡/审批设计不扩大为重做验收，保留约束通过变更反查。生产实际部署/数据保护由部署后Validation核，不以本地报告代签。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| F01/P2 | V06；07§7.2；tools/secretary_dispatch.py:130、147；agent/inline_tool_executors.py:346；agent/tool_executor.py:751 | Loop拒绝缺next_action；直接invoke与executor只返回error字符串；本地原生invoke反证1 failed | 权限有效但新固定权限工具的拒绝回执违反固定错误契约，影响模型一致纠错，阻断本门禁 | 主会话提出最小统一标准拒绝方案；核同步/并发/Loop/invoke/registry，拒绝前无效果且带scope_denied/message/next_action | 已证实，待提案与修复 |

## 6. 修复与独立复审

初始审查：F01原判据为V06及07§7.2。反证使用官方runner、受控SDK/真实Loop与DB，Main实际_invoke_tool返回字符串error，预期契约测试失败，日志位于.hermes-dev/noting-fixed-tools-20261024/verification/permission-error-contract.log；无模型收费请求、生产写。已向主会话集中交回，待其提案。无退回补审历史。

F01关键研讨链补记：主会话同意07§7.2偏离，提议在同一权限owner新增标准scope_denied回执builder，保留字符串诊断API；Loop/registry/inline/executor拒绝复用，post-hook诊断仍是字符串，不改其它plugin/通用scope/finish混批错误。Verification依据原V06认可方向，要求解析前tool_call/tool_search拒绝也覆盖、prechecked invoke不旁路、零副作用、合法混批/拒绝后合法调用继续。未改变规格；待实现版本与全部路径证据后关闭。该统一回执是需在final-delivery及最终汇报摘要的实质工程收敛，不能称原先已完全符合。

证据补齐：V32原缺口由主会话定向运行当前Web589df02的controller-context-compaction.test.ts关闭，50 passed/0 failed；Verification亲核三源码及日志SHA四项全真，未复跑无关前端套件。发布准备代码已亲读、439文件集合与tar SHA独立相等；未执行发布或任何云操作，不将准备态称生产通过。

初审整包交回（2026-10-24）：全范围V01–V32已逐行核查并有可回查判定；24符合、3有依据不适用（V21–V23旧完整UI项目不属本轮新增范围）、1违规（V06/F01）、4证据不足（V17/V18/V19/V28）。F01根因及主会话方案已评审但未收到修复版；此时无关闭证据，不将方案认可冒称缺陷关闭。F02–F04分别对应真实链路、明确长样本和最终收尾。按套件，修复后应由全新独立审查者重新建立全轮判据并核旧问题/影响；本次有效反证、源码核查与指纹材料可复用，不能只复跑问题清单。
