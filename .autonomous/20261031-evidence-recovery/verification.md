# Verification：20261031-evidence-recovery

## 1. 审查对象与结论概览

审查者：全新无父实现上下文的独立 Verification Agent；2026-10-31。先复制本 Skill 的原模板，先仅读权威规格并完成第2节落盘，再读取 AGENTS、CLAUDE、实现及报告；未修改产品、测试、检查器或规则，未运行真实模型、UI或生产操作。

- Snapshot Index：`.autonomous/20261031-evidence-recovery/snapshot-index.md`；基线：同目录 `baseline.txt` 的 `8b31d986dca870c8656dde2b69826ad65dc24e65`，追加授权冻结 `67d0fab44e`。待审产品：`a51a0bf17fff5ccea52ae9faebc880dd200a457e`。正式发布产品为 `bf28ab565ae322965e3b8eb0797486e1d0cdbac7`，a51a0bf至bf28全差异仅文档/门禁报告；本地收尾 `913084338b76d9188e60dc5b10c7c15bb1cfb633` 继续仅文档变更，不代表再次生产部署。原本轮工作树已删除，报告及证据迁回 `/Users/edgar/code/hermes-secretary`。
- 范围：07顶部2026-10-31 A/B及增量接口，§12.3已授权manual调试入口；来源链、UID授权、派生时间、Candidate、全模型投影、原子Snapshot、Main只读与缓存不变量；白板C3/C6/C7/K6/N1/N3。E10包括本仓全部旧工作树保全/合净/原目录main。其它独立重设计不重验。
- 当前结论：**Verification最终通过。** 第3节19项全部符合，0项违规、0项证据不足、0项不适用。初审时V18/V19的最终动作尚未发生，曾只作安全计划审查；现已按实际收据与本地现状补核，VF-FINAL-01/02/03全部关闭。独立Validation结论由其报告负责，最终交付由主会话判定。
- 授权归属：自主执行套件为Agent自行选择，不能倒称用户最初要求自主实现；用户最新明确按已展开原计划完成再上线，部署与收尾仍依真实授权及收据核验。
- 有效复用证据逐文件匹配：D1八产品文件、D2六产品/测试文件及lock/PM环境、D3七文件，共23指纹全部相同，独立记录于 `.hermes-dev/evidence-recovery-20261031/verification/static-review.json`。没有把实现阶段HEAD单独当成已包含dirty产品的证明。

## 2. 独立要求清单与覆盖
判据于2026-10-31独立建立；依据待审a51a0bf工作树的07顶部A/B、§12.3及索引指定保留条款、白板C3/C6/C7/K6/N1/N3。此前未读代码、测试、看板或实现报告。V14明确标记工程接线较薄处；索引仅定位及确定授权范围。以下初始判据永久保留，后续修订另记第6节。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| V01 | 07:13–28 A定稿与EN | 行为/Prompt | 描述只概括本组消息；补充entry description，忠实保留主体、接受、限定及变化，禁止跨组/泛标签/复制当前态。语义遵守不能由校验器保证。 | 运行Noting Task须含逐字定稿EN与完整来源指导；不额外硬截断。 | 第3节 V01 |
| V02 | 07:11、17–18、109–112 | 机制/写入 | source_description与完整source_message_uids共同构成本Task槽；同Task覆盖，后Task追加，旧Task不可改删，组内去重不加跨Task唯一。 | 真DB创建/同Task多次编辑/后Task/继承校验；描述与UID不可分离错位。 | 第3节 V02 |
| V03 | 07:11 | 边界/模型与可信Python | 模型新建/实质修改非空直接UID必须提供非空描述，拒绝无副作用；可信Python省略保持兼容未知。 | 检查schema、同步/并发/间接dispatch及正式runner调用；缺失/空白/错误类型拒绝，兼容调用可用。 | 第3节 V03 |
| V04 | 07:11、20 | 历史兼容 | 旧来源描述只读规范为null，原记录不回写、不猜造、不重跑；继承比较采用兼容表示。 | 旧组读取/更新/提交/恢复正式路径可用，旧快照字节不变；未知不冒充空组。 | 第3节 V04 |
| V05 | 07:11、19；白板K6/N1/N3 | 投影/机制 | 描述/UID/时间逐槽一致，覆盖Main/Noting Show、初始/续Turn、Framework、工具回执及持久快照。 | 追全模型投影及返回路径；真DB有效Snapshot与各投影核对。 | 第3节 V05 |
| V06 | 07:18、123–125 | 保留/时间 | 证据时间仅由对应UID原timestamp及原优先级派生；未知不回填当前时间，描述不能影响时间。 | 真实用户优先、无用户取最近assistant、其它范围/未知；同Task只重算本槽、旧槽不刷新。 | 第3节 V06 |
| V07 | 07:11、19、134；白板C3/C6 | Candidate | 直接与refs严格二选一；refs沿现行源条目，不制造空描述；直接转refs仅本Task唯一未提交槽。 | 直接/refs创建更新、混用拒绝、已提交直接组保护及引用源更新链核查。 | 第3节 V07 |
| V08 | 07:11、109–112；白板K6 | no-op | 实际无修改update保持no-op，不为补来源描述续期/造版本；真实变化须本Task来源。 | 比较实际属性及来源处理顺序；无修改与描述单独补充均不造版本，真实修改沿稳定身份出版本。 | 第3节 V08 |
| V09 | 07:30–46 B定稿EN | 行为/Prompt | 依赖本Conversation既往表述/选择/原因/承诺/修正即MUST落实原文，即使简单紧急熟悉；不依赖历史即时任务不强迫查。 | 实际Main History与Notebook指导统一定稿，无主观足够即可跳过的竞争句。 | 第3节 V09 |
| V10 | 07:30–46 B定稿EN | 行为/工具顺序 | 先相关Notebook组；原文已可见且足够免重复Read；否则优先相关引用Read，缺失/无法定位/重要缺口才Meta/Search；足够即停，不猜补。 | 正式构造文本和受控SDK历史分支、失败分支证明工具可用与输出未知；不宣称模型必然服从。 | 第3节 V10 |
| V11 | 07:240、655–668；白板K6/N1/N3 | 保留/权限与原子性 | Main只读；Noting可信身份六工具；来源需当前合法授权及继承绑定；成功finish后runner原子验证提交完整Snapshot，不发布草稿。 | 核正式dispatch/runner/Commit Gate及失败、旧来源继承、授权拒绝；全局关闭/非eligible原生不变。 | 第3节 V11 |
| V12 | 07:659、1810–1822、2155–2157 | 保留/缓存 | 父root/tools/Active冻结共享；运行中不热改工具/root；新版本仅正常构造/恢复边界生效，定向失效只清prompt/tools pin不改历史数据。 | 核实际序列化/受控SDK前缀及缓存失效入口；busy拒绝、无额外模型、无Notebook重写。 | 第3节 V12 |
| V13 | 07:2165–2178 manual start/state | 接口/权限 | 认证WS RPC，必填profile/conversation/request；同键幂等，state只查询、不存在not_found；生成TS与OpenRPC一致；不进模型工具表。 | 从RPC dispatch追目标Profile及请求身份、重复/异Profile、非法参数及state零启动。 | 第3节 V13 |
| V14 | 07:2175 manual边界 | 机制/薄弱接线 | 新manual整理基于目标Profile当前原生Main resume/context及完整工具freeze，复用manual admission/child/Commit Gate/通知；不借失败child/独立执行器。 | 追原生parent构造至child提交与发布；真DB/受控SDK正式链，生命周期资源关闭。 | 第3节 V14 |
| V15 | 07:2175 manual边界 | 边界/并发失败 | 不额外Compact、不改自动参与/Idle配置；沿能力参与门禁；忙不抢Main租约、不绕压缩锁；重启/失败/取消/替代如实状态。 | busy/lock/off/External/profile等分支与原生租约；持久状态恢复不重跑。 | 第3节 V15 |
| V16 | 07:2172–2175 manual回执 | 提交见证 | committed/snapshot_id必须来自实际child提交；queued/模型结束不等于提交；cancelled/superseded审计不能作有效Snapshot。 | child持久model_config/recovery/admission/有效Snapshot对账，失联旧记录只报告事实。 | 第3节 V16 |
| V17 | 07:7–9、19–20、2175 | 范围/授权 | 只两项及已授权manual遗留接收；不重做其它生命周期/UI/Provider，不启动生产Noting，不新增真实模型条件。 | diff范围、执行证据与外部动作记录；受控SDK不可冒称未来模型遵守。 | 第3节 V17 |
| V18 | 索引E10/E08；07:7 | 收尾事实/最终补核 | 所有本仓worktree盘点、整合在授权范围内独立改动、保留证据后清理，排除其它仓库/镜像/个人隔离，原目录最新main。 | 先审盘点与保全方案不把计划作事实；最终需删除/分支/main收据补核。 | 第3节 V18 |
| V19 | 索引E03/E08/E09；07:7–9 | 发布事实/最终补核 | 授权正式Alex上线，保护配置/业务/凭据，正常边界采用新Prompt/Schema；备份保留最近两套。 | 先核发布计划与范围；最终需实际SHA/只读验真/目标缓存失效/备份清理收据，不由计划判完成。 | 第3节 V19 |

## 3. 逐条实现证据

证据路径未特别说明时均位于 `.hermes-dev/evidence-recovery-20261031/`；代码路径相对本仓。逐行适用条件与必要不变量见第2节，以下不给新含义替换原判据。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| V01 | noting_prompts.py:3–69 DEFAULT_NOTING_TASK_INSTRUCTION → noting_child.py:run_noting_task → 初始wrapper及后续原生Turn | 逐字比较07 A英文与运行文本；审真实SDK序列化初始/续Turn及拒绝scheduler后show/finish；描述规则只写本组、归属、接受和不确定性，不加字符截断。 | prompt/tests-prompt-final.log（8通过）；prompt/pytest-final/test_noting_exact_description_0/noting-initial-continuation-requests.json；verification/static-review.json | 符合：A原文完整进入真实Task一次，后续保留；原Noting按需Get Meta策略保持。 | 证明提示交付及能力边界；E12取消模型采样，不声称每次模型必然忠实概括。 |
| V02 | noting_tools.py:54 initialize_notebook_work → NotebookStore → notebook_model.py:96 _apply_sources/236 create/277 update → notebook_items.py:116 source_basis_conn/149 insert_item_conn | 真SQLite同Task覆盖完整UID/描述/派生时间、跨Task追加；已提交节点重用Task ID及篡改描述反例被拒。transition前缀同时比Task/UID/描述/时间，committed禁止尾槽替换。 | data/targeted-final.log（151通过）；test_notebook_evidence_descriptions.py:42,181；notebook_contract.py:217–240 | 符合：一Task一槽、旧节点不变；描述不能以相同UID冒用历史继承，持久INSERT-only。 | 审查了正常与恶意继承、重启；无生产原记录写入。 |
| V03 | 固定noting_contract.py:279/631 Schema → noting_tools.py:_mutation_args/_notebook_mutation → strict NotebookStore → _apply_sources | 模型绑定require_source_description=True，参数不可通过schema关闭；None/空/空白/非字符串/缺UID及非法UID拒绝；SQLite真实insert后注入故障核事务回滚；可信Python默认False可省略。 | data/targeted-final.log；test_notebook_evidence_descriptions.py:75–125；data/targeted-third.log中fixed_noting_permissions完整86通过 | 符合：模型新/实改direct必填，拒绝零副作用；schema可选兼容refs与可信旧调用，不把可选误作免校验。 | 六工具同步/并发/invoke权限复用未改guard，结合当前strict正式绑定；不是独立helper证明。 |
| V04 | notebook_contract.py:136 canonical_notebook_entry → notebook_items.py:canonical_notebook_payload/item_entry → Store构造/Show；noting_recovery_sources.py:_visible_entry/_base_snapshot | 缺字段旧INSERT-only JSON通过只读canonical给等长null；读取/提交/后Task追加及历史control恢复均保持旧raw；继承比较也canonical；追加三生产Profile mode=ro/query_only零写只读核验：Alex190历史item里132个UID链item的204组归null，58个更早非链item及17Snapshot保持。 | data/targeted-final.log；test_notebook_evidence_descriptions.py:159,296；noting_recovery_sources.py:56,207；release/{readonly-compat.json,readonly_compat.py}；verification/final-receipt-audit.json | 符合：旧组可用且显式未知，不猜补、不回写、不自动重跑或转换。 | 生产核验只读输出计数/哈希；更早非链审计项不冒称被迁移到新来源链；当前有效Notebook另由正式RPC读取成功。 |
| V05 | notebook_render.py:27 readable_notebook_entry/47 state/119 show/149 _render_entry → tools/notebook_tool.py；noting_tools.py:_encoded/控制消息；noting_child.py:_working_control → framework_messages/Note既有接缝 | 真工具Create→Update回执/working Show/control/Commit→Main Show和render全部保描述；真实原生Noting循环提交后，通过后续合法压缩边界实际投递Framework核UID和描述。 | data/targeted-final.log；test_notebook_evidence_descriptions.py:137,272；data/targeted-fourth.log中noting_provenance_wire7及r3_notebook_time_projection9通过 | 符合：新数组随完整条目和各模型输出，runtime内部Task/version标识仍按原投影隐藏。 | refs Candidate本身无direct数组；其现行源条目在完整Notebook内可读，继承原refs时间展示语义。 |
| V06 | notebook_store.py:_derive_time/_insert_version_conn → notebook_evidence.py:derive_evidence_time/_message_points → 原UID来源路径/semantic_role | 源码确认仅UID与原timestamp进入时间派生；正文2099日期不改100时刻；用户优先、assistant最近及未知沿既有测试；新槽写事务复核、旧槽保持。 | data/targeted-final.log；data/targeted-fourth.log中provenance_arrays32/provenance23；test_notebook_evidence_descriptions.py:42,237 | 符合：描述没有成为时间或来源授权输入，时间逐槽原样派生/保留。 | 保留现行UID语义消息分类，不扩大任意正文日期推断。 |
| V07 | notebook_model.py:_apply_sources/validate_fields → notebook_contract.py:validate_candidate_provenance/validate_references → Store/Show | direct/refs两来源创建、混传拒绝、同Task唯一未提交direct显式清空转refs；已提交/旧Task节点禁止清除；源条目更新后refs读取当前源内容，refs描述槽保持[]。 | data/candidate-final.log（62通过）；data/targeted-final.log；test_notebook_evidence_descriptions.py:214；notebook_contract.py:validate_provenance_transition | 符合：新描述未引入第三来源形态或空证据组，也未扩大已上线同Task切换例外。 | 覆盖全部Candidate目标与既有settlement回归；未重验其它独立生命周期设计。 |
| V08 | notebook_model.py:277 update先合并普通属性 → 校验 → entry==old no-op → 实改_persist | 属性未变化且不带来源直接返回不造版本；带来源则先验证但实际无改仍不造版本；仅source_description/UID无普通属性拒绝。 | data/targeted-final.log；test_notebook_evidence_descriptions.py:83；notebook_model.py:309–328 | 符合：不能借补描述单独续期或造来源，真实变化和支持组同时提交。 | 无改时允许省略描述是明确本轮契约，只因不会创建/修订组。 |
| V09 | agent/system_prompt.py:34 MAIN_EVIDENCE_RECOVERY_GUIDANCE → HISTORY_SEARCH_GUIDANCE → builder _guidance_parts → AIAgent.run_conversation请求 | 独立逐字匹配B三段；完整root含项目context、Skill/MEMORY/USER、时间及runtime footer；Notebook旧主观足够句已原位删去并指向统一指导；资格/off分支均核。 | prompt/tests-prompt-final.log；prompt/pytest-final/test_full_main_prompt_and_cold0/{main-full-request,main-restored-request}.json；verification/static-review.json | 符合：历史依赖触发MUST，不以简单/紧急/熟悉绕过；即时无历史依赖未新增强迫调用条件。 | 真实builder/SDK构造，受控响应；不推导自然模型服从率。 |
| V10 | 同V09实际完整Main root；conversation_history固定顶层声明及原生工具dispatch保持 | B准确规定visible且充分可用、相关组先Read、references缺失/不能定位/重要缺口才Meta/Search、充分即停/未知不猜。原权限及读取结果回归核路径；没有旧主观充分竞争句。 | prompt/tests-prompt-final.log；prompt/tests-footer.log（10通过）；data/targeted-third.log权限86；实际wire同V09 | 符合：正式可见指导、工具和失败处理未被弱化；无法恢复的语义要求明确保留未知。 | SDK脚本不能证明模型自然选择顺序；E12授权下本轮以构造/正式机制为判定范围，独立Validation另走用户入口。 |
| V11 | noting_child.py:73 noting_dispatch_block → tools/secretary_dispatch.py:scoped_dispatch_refusal；_notebook_mutation；run_noting_task → _commit_when_complete → commit_notebook_state → hermes_state_secretary_notebook.py:255 | Main四写工具、Noting其它工具在同步/并发/invoke/Loop拒绝；实际finish正常收束后同事务核参与、anchor、精确不可变版本、来源与Snapshot/pointer；新数组加入精确继承，不跳过原gate。 | data/targeted-third.log权限86及wiring52完整文件；data/targeted-final.log；notebook_items.py:215 snapshot_item_ids_conn；noting_child.py:642–660 | 符合：Main只读、Noting独占写、Snapshot原子性与失败不发布草稿保持，关闭/非eligible边界由现行guard保留。 | 只核本轮影响及适用原生回归；不是宣称重做全部历史生命周期验收。 |
| V12 | noting_surface.py:apply_main_read_surface/synchronize_main_read_prompt → conversation_loop正常restore/build；cache_parity及freeze_parent_active_prefix → Noting请求；context_cache_clear原RPC | 完整父工具表/Root/Active在Noting初始/续Turn逐项一致；恢复旧root在正常Main边界重建一次并记录toolset_change，warm复用不改原消息；定向缓存失效契约未变。 | prompt/tests-prompt-final.log；prompt/tests-protocol.log（4通过）；prompt/tests-adjacent-final.log（11通过）；test_evidence_recovery_prompt.py:52–138,179–224 | 符合：无中途刷新工具或root，无新增Provider/执行器；新版Schema随正常构造恢复刷新。 | 生产两服务正常重启已采用新代码并退役旧热runtime；持久Root/tools沿既有正常构造/恢复自动同步，此机制已在隔离真链验证；本轮没有生产模型请求，不冒称已实测某次生产Main重建。 |
| V13 | server.handle_request认证后 → methods_noting_recovery.py:_noting_start/state profile_scoped → debug_noting_rpc；contracts.NotingStartParams/Result →正式TS/OpenRPC生成 | 参数必填/空白/最长128/extra拒绝；target/foreign Profile真DB隔离；同键幂等/异键竞争；state未存在not_found且SDK0调用；生成逐字校验通过。 | manual-debug/final-current.log（34新manual＋6恢复＋1生成＝41通过）；tests/tui_gateway/test_manual_noting_debug.py:70,96,142,151,535 | 符合：已认证后台RPC沿既有注册/目标Profile边界，不进入模型工具表；只新增start到_LONG_HANDLERS。 | 认证外层未改，独立Validation实际入口另核；catalog旧review.summary孤立事件另记范围外。 |
| V14 | noting_debug.py:_parent/_prepare_parent/_dispatch → scheduler_host.resume_session(exact_session=True) → _sess原生builder → prepare_joint_noting(manual,operation_id) → freeze/admission/spawn → 原生child工具/Commit Gate/Note | 真冷builder及暖原生parent；目标Profile与当前route一致检查；短Main lease下同步正常cache/root/tools，实际history冻结；真实child写Notebook与提交；后续原生压缩才投Note，无独立执行器。 | manual-debug/final-current.log；tests/tui_gateway/test_manual_noting_debug.py:157,454,558；noting_runtime.py:552–654；noting_child.py:run_noting_task | 符合：薄弱接线要求已落实到原生正式路径，准备动作没有当完成；完整工具freeze与正式child提交均实跑。 | provider响应受控，原生resume/构造/DB/工具/提交/发布未替换；不操作生产manual。 |
| V15 | noting_debug.py:_start/_renew/_dispatch/_receipt → 原生session_turn_leases、compression lock、能力/参与、task presence | busy/压缩锁4010不抢占；准备中锁变化/过期继任不派child；CAS不复活旧租约、定时续租后回收；off/能力/Force保持；取消/替代/启动/执行/存储故障与注册presence窗口实跑。 | manual-debug/final-current.log；tests/tui_gateway/test_manual_noting_debug.py:106,203,290,320,329,348,361,378,431,481,535；noting_debug.py:129–219 | 符合：没有额外Compact/配置修改/自动重跑；重启无活任务返回interrupted，不把running字段当活跃证明；finally回收持有租约。 | 针对性并发故障测试而非长时间压力测试；实际child不占Main模型Turn，短准备租约为原生owner复用。 |
| V16 | noting_debug.py:_request_admission/_child_receipt/_receipt → noting_child持久child → hermes_state_secretary_noting.py:196 noting_record_child_snapshot_conn | 提交见证在原Snapshot写事务内以admission/child/Conversation/anchor/kind绑定；回执只接受该child model_config witness；queued与模型结束无witness均false；cancelled/superseded无commit，audit末写失败仍按operation找已接纳child。 | manual-debug/final-current.log；tests/tui_gateway/test_manual_noting_debug.py:70,244,290,329,481；hermes_state_secretary_noting.py:196–212 | 符合：committed不是排队/文本完成或任意当前Snapshot推断，取消/替代审计不冒充有效提交。 | 保留既有非关键association失败时“不凭空声称已提交”的保守观察语义。 |
| V17 | baseline..a51a0bf完整diff；当前07/index授权；产品仅Notebook十文件与manual窄包及测试/文档整合 | 审未增加新模型路由/Provider、UI改版/独立生命周期变更；原来源旧组不转换；本Agent0真实模型/生产/UI调用。E12替换旧采样条件，历史3样本原件不作为全覆盖依据。 | git diff 8b31d986..a51a0bf；data.md/prompt.md/manual-debug.md及上述匹配日志；snapshot-index E10/E11/E12 | 符合：本轮范围按授权收敛，独立旧文档/历史报告整合不当新功能验收。 | 新增长期文档的产品结论保持历史时点；最终公开范围与凭据/数据保护由主会话提交/发布复核。 |
| V18 | worktree-audit.md → dirty/分支/证据保全 → archive-receipt → old-cleanup → finalize_worktrees → cleanup-final；本Agent复核原根Git及逐manifest SHA | 5旧树与本轮树均已删除；只剩原目录main，补核开始时clean且HEAD/main/origin-main=9130843。13旧本地功能分支清理，3非ancestor补丁等价已保bundle并verify；仅main/hermes-upstream保留，stash相同。独立重算5旧树82385文件、本轮20274文件及原根14 dirty原件SHA，46软链文本和目录均无差异；原Python实体SHA保持。 | worktree-audit.md；cleanup-final.json；`.hermes-dev/worktree-retained-20261031/`的archive/old-cleanup/final-cleanup-receipt、各evidence-manifest、原根dirty-manifest及refs bundle；verification/final-receipt-audit.json | 符合：已核实际归档/删除/分支/原目录main，VF-FINAL-02关闭；没有把祖先关系当dirty已合或把计划当完成。 | 归档中历史pytest便捷软链保持原文本，未跟随旧绝对链误删原环境；本报告补写会产生范围内文档dirty，交主会话提交，clean事实对应补核前及收据时点。 |
| V19 | 已授权main发布执行器 → 空闲预检复检/停服/三库backup/main快进/重启 → receipt verified → 认证WS/HTTP只读验真 → 两套备份校验/旧备份清退 | 2026-10-31T10:09:58+08正式Alex bf28ab5；Web/Gateway实际同SHA且active/running、微信connected。receipt前后三库保护表、配置、绑定、Secretary及Dashboard静态五组逐对象exact相同。正式Notebook50789字节可读新描述字段、内部Task隐藏；新noting_state返回not_found且0 start，6HTTP资源核SHA。两套完整三库SHA/integrity/FK均通过，删除旧备份sidecar等9文件212004864字节，运行库/同步包保持。Linux111/0及精确QA/环境/锁绑定已关闭。 | release/{receipt.json,postrelease-readonly.json,backup-retention.json,readonly-compat.json,linux-tests-valid.log,linux-environment.txt}；docs/operations-log.md顶部；verification/final-receipt-audit.json | 符合：实际SHA/健康/正式读验/数据保护/备份收尾齐备，VF-FINAL-03关闭；正常构造/恢复采用新Prompt/tools，未热改飞行前缀或重写旧组。 | 生产测试模型、manual Noting启动及测试外发均0；不以本轮读验声称自然模型服从或生产Main请求已跑过。线上bf28与本地913文档HEAD区分，不把本地后继SHA当线上版本。 |

## 4. 核心目标及验证方法审查

1. **独立判据与正式机制。** 第2节19项在读取实现/报告/看板之前写出；权威原文→必要不变量→正式入口→适用条件→方法→观测→判定的链路逐行在第2/3节对应。没有因规格未给函数名而放过manual父构造/租约/实际提交。V14的方向明确而接线薄处，以现有原生Main/resume、freeze/admission、真实child、Commit Gate及现行Note资格全链核验；没有用孤立helper或准备成功代替提交。
2. **数据增量与历史兼容。** 模型工具strict在可信初始化处绑定，而不是让模型自己传旗标；字段可选只服务refs和Python旧调用。UID、描述及时间在同一条不可变版本内，继承前缀比较包括描述；已提交末槽的替换权被显式收紧。旧字段缺失只读映射null，Snapshot仍精确匹配不可变版本。反证包括旧描述篡改、复用Task ID、source-only更新、非法UID、null/空白/非文本、错位数组、真实insert后SQLite失败；相应旧raw/pointer/工作态不变证据有效。
3. **Prompt与全部模型投影。** 两段英文定稿逐字出现在运行源及真实SDK构造中；Main完整Root实际产物含project context、Skill、MEMORY/USER、时间/footer及其余工具指导，没有旧主观“足够”竞争句。Noting父system/角色/规则/工具政策/任务/完成条件明确作废，当前Task和续Turn仍限六工具；描述、UID、时间经控制消息、Show、单条回执、真实Snapshot与Framework贯通。Main回查序列是模型指导，不新增强制代码检索或改变无历史依赖即时任务；E12明确取消后续真实模型，不以脚本模型选择证明自然服从，也不要求再采样才通过。
4. **证据底座与版本。** D1真DB、D2真实AIAgent/原生builder/OpenAI SDK JSON序列化（MockTransport仅控provider响应）、D3真RPC handler/Profile DB/冷暖builder/child/工具/原生压缩与Note均保留产品机制。固定权限86项含同步、并发、invoke、正式Loop及间接registry，而非只测函数。逐文件23指纹全部一致；uv.lock与共享PM pyvenv一致。基于相同机制有效证据复用，没有复跑大型套件。审查新增测试的assert来自本轮A/B/接口及保留机制，自动为旧fixture加描述不替代专属缺描述拒绝测试。
5. **测试失效与负对照。** 当前R3整文件12项失败，在冻结基线原代码/测试准确复现：9项旧同区间立即FM预期与3项旧registration/owner接口；当前适用44项通过。测试调整将实际Framework推迟到合法后继压缩边界，没有为旧oracle改现行生命周期。contract catalog的review.summary orphan在集成前HEAD独立源码复现；生成逐字校验已通过。不能据中间第三轮20失败或第四轮人工中止日志宣称全绿；只取报告列明完整文件有效片段/最终替代日志。
6. **平台与风险范围。** macOS为真实arm64、Python3.14.7，Linux不能由其替代。首轮Linux没有进入测试：生产venv缺pytest触发环境准备，fresh PM锁解析因resvg-py无publish time中断；保留失败，后继复用既有官方PM test环境的真实Linux结果已核：`release/linux-tests-valid.log`为7文件111通过/0失败、97.4秒，覆盖描述23、Prompt8、UID wire7、来源数组32、manual34、恢复6及生成1。`release/linux-environment.txt`记录实际QA HEAD为a51a0bf、tracked状态空、Python3.14.7、pytest9.1.1，新旧源码uv.lock均为2bc4db483e9cba927cd7147f9ccbb09635f85bb3f1f36d6e9d51d06b65d1c67e；未重跑或修改锁。没有桌面/浏览器/UI请求，本轮无前端改版不以UI缺失阻断；无生产manual调用或外发。
7. **规则与资源保护。** diff未修改冻结检查规则、阈值或等级，最终staged十检查日志为0 blocking/0 advisory；不关闭项目门禁。收尾计划先保全完整证据和dirty，保原目录共享venv及解释器实体；拒绝整树clean/reset及跨仓/镜像/个人隔离误并。最终执行已按收据补核：归档文件与软链逐manifest重核、原根Git/本地refs/bundle/Python实查均符合，未用计划代替完成。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| VF-FINAL-01 | V19；release/linux-tests.log、linux-tests-valid.log、linux-environment.txt | 首次setup失败保留；有效Linux后继7文件111通过/0失败、97.4秒，canonical runner实际执行。实际QA a51a0bf tracked干净，Python3.14.7/pytest9.1.1，新旧uv.lock同SHA。 | 已取得真实目标平台及精确身份/环境/锁绑定，未见范围内回归；原setup失败不当产品通过证据。 | 复用日志与环境原输出，未重跑测试、改锁或生产环境；第4节列精确覆盖。 | 已关闭（2026-10-31独立补核）。 |
| VF-FINAL-02 | V18；cleanup-final及retained收据/manifest | 最终只剩原根main、补核前clean，HEAD/main/origin-main=9130843；5旧树+本轮树均不存在，13本地旧功能分支已处理，bundle/stash/Python保持；102673普通文件逐SHA及46软链无差异。 | 原最终事实缺口已补齐，没有产品变更或降低原判据。 | 原件、归档、bundle与本地Git现状独立核验记录见verification/final-receipt-audit.json。 | 已关闭（2026-10-31最终事实补核）。 |
| VF-FINAL-03 | V19；release最终收据 | 正式bf28 receipt verified，两实际服务同版/健康；三库保护/配置/绑定/双静态exact；正式认证只读RPC及6HTTP资源通过；两套三库备份有效，旧9文件清退完成。 | 已由实际结果补齐发布缺口；受控测试与线上只读观测的边界继续保留。 | receipt/postrelease-readonly/backup-retention/readonly-compat与本Agent逐对象比较，产品a51至bf28无代码差异。 | 已关闭（2026-10-31最终事实补核）。 |
| VF-BASE-01 | 范围外既有测试债 | R3旧oracle12项与catalog review.summary孤立事件在既有基线复现。 | 无本轮新增产品偏离；不把它们冒签通过，不通过降低门禁消除失败。 | 主会话将测试债登记计划，后续独立维护按现行机制更新；本轮相关正式路径证据见第3节。 | 范围外保留，不阻断本轮产品改动。 |

本轮未发现需要产品修复的范围内缺陷；没有建议为通过测试改生命周期、扩大模型权限或增添真实模型条件。

## 6. 修复与独立复审

初审产品门禁通过，审查者与待审产品见第1节；主会话明确接收产品/最终事实阶段区分，独立Validation可接续，Linux及发布/清理必须在最终交付前补核。本次没有实现修复，不是针对旧问题的局部复测。第2节初始19判据未为容纳实现降低，未修改产品规格。完整范围与薄弱接线均按第3/4节核查。

关键研讨链：初步产品调查未发现阻断 → 主会话告知Linux首轮非零 → 审查者独立读取原日志，确认未进入测试/PM解析失败 → 主会话提议复用既有官方PM test环境与同锁，在隔离QA按canonical runner补证 → Verification认可该方法不改产品/生产/依赖锁且能补真实目标证据，后继实际日志及环境原件已逐项核实并关闭VF-FINAL-01。没有把环境准备失败解释为产品成功，也没有要求新增真实模型。

尚未发生报告退回补审；无产品工程语义取舍需用户追认。供final-delivery及最终用户摘要：受控SDK/正式工具/真DB/原生child链证明提示被正确构造及机制可用，不能证明模型未来必然遵守；旧组描述保持未知不回填；manual能力上线不等于已获授权生产补跑；发布和所有工作树清理已按实际收据补核关闭，历史计划/初审结论保留其时点。

2026-10-31 Linux独立补核：主会话提供有效目标日志与实际环境输出，审查者亲读并复核111/0及QA a51a0bf/干净tracked/Python3.14.7/pytest9.1.1/同锁SHA绑定，关闭VF-FINAL-01。产品门禁结论保持通过，未新增产品缺陷或改判据。此时VF-FINAL-02与03仍待实际清理/部署收据，生产只读兼容也未提供；以下最终补核记录其后发生的事实，不改写该时点。

2026-10-31 最终发布/清理补核：迁回原根后先读取当前AGENTS/CLAUDE/索引与所有最终收据，核a51→bf28全部差异仅文档/门禁报告，bf28→本地913也仅文档。独立重算旧树82385文件、本轮20274文件、原根14 dirty原件的完整SHA（共102673文件），46软链文本及目录存在性均匹配；原Python实体SHA e0466917…8360ee保持、refs bundle verify成功、stash保持、仅main/hermes-upstream及单原根工作树实查符合。该审计13.46秒，未运行产品测试或生产命令，原件见verification/final-receipt-audit.json。

亲读发布receipt及只读验真后，逐对象比较三库保护表、配置、绑定、Secretary/Dashboard双静态集合/哈希全相同；正式bf28双服务及微信健康、Notebook/新state只读RPC、6资源SHA、两套完整三库及旧9文件清退收据齐备。只读旧组核验以a51实际产品文件16项指纹匹配、mode=ro/query_only、total_changes=0为边界；190 item中132 UID链/204组null与58更早非链保持、17Snapshot不改，无补描述/转换/重跑。正常服务重启退役旧热runtime；下一正常Main构造恢复的Prompt/tools同步由已核隔离机制保证，本轮0生产模型不冒称已跑生产重建样本。关闭VF-FINAL-02/03，V18/V19由阶段不适用更新为符合，最终19/19符合、无未关闭范围内问题。主会话负责提交本报告的文档增量、独立Validation及最终交付声明。

授权陈述更正：套件执行是Agent自行选择，并非用户最初提出“自主实现”；用户当前已明确要求按既有展开计划完成再上线。此处只纠正流程归属，不更改已确认产品语义、E10/E11/E12边界或以历史描述制造新授权。
