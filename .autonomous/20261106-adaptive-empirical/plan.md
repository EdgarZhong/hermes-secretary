# 本轮实施计划：20261106-adaptive-empirical

## 目标与依据
依据snapshot-index.md与baseline.txt、算法稿V2 U1–U3/R1–R10。先数据与人的经验案例，后算法、回放、亲审及两门禁。核心是历史数值→可解释特征/经验样本→正式decide→m/T/δ→实际可执行历史模拟→逐段经验判断。禁止上线/合main/生产写/生产模型。

## 覆盖与任务
| 要求 | 任务和正式路径 | 负责人及白名单 | 依赖和接口 | 验证 | 场景 | 完成条件 |
|---|---|---|---|---|---|---|
| R1/R2/R6/R7 | D 数据来源、阶段/特征分析、真实案例先固定；后历史策略CLI | historical_replay：scripts/adaptive_empirical_replay.py、secretary/adaptive_empirical_replay*.py、tests/secretary/test_adaptive_empirical_replay*.py；本轮ignored数据/报告 | 只读旧numeric、historical-input、当前774event包；读取正式decide，不复制算法 | 原件SHA/来源/knowability/预期先落盘；真实旧/新回放，迟到信息、策略分歧后的状态 | 上升→平台→再上升，长闲后台自增，短暂停顿，失败/无读取补充分支 | 预期先于结果，有全段动作/执行/拒因/漏机会证据，不伪称因果收益 |
| R1–R5/R7 | P 经验特征、采样与策略重写 | empirical_policy：secretary/adaptive_policy.py、adaptive_forecast.py、adaptive_features.py、adaptive_cost.py、adaptive_rollout.py、adaptive_risk.py、adaptive_empirical*.py（不含replay）；相关新test_adaptive_empirical_policy.py/既有对应测试 | 等D先固定真实经验案例；与W协商sample schema；不拥有runtime/import | 经验特征对照、同源风险费用、真实包与正式入口测试、旧原生保护 | 平台有收益机会、活跃/短离开不抢、维护真实慢失败、缺证不虚构 | 不能靠固定昂贵/廉价假设或换标签过关 |
| R3/R4/R8 | W 正式观测、历史样本导入/读取闭环 | empirical_wiring：secretary/adaptive_runtime.py、adaptive_store.py、adaptive_import.py、adaptive_bootstrap.py、adaptive_samples.py；必要agent/context_compaction*及secretary/noting_native_link.py/noting_child.py/noting_completion.py/noting_task_lifecycle.py（先核精确接缝）；scripts/adaptive_empirical_import.py；tests/secretary/test_adaptive_empirical_wiring.py | 输出maintenance_sample数值事件；完整费用/阻挡/缩减各自证据及unknown，沿现有store owner，不生产调用 | 真实隔离SessionDB/正式生命周期，关闭/失败/重启/隔离，导入幂等原子失败 | 下一次自然维护样本可更新估计；离线样本可同owner显式导入 | 正常路径可持续学习，不只离线shadow有效 |
| 全部 | I 设计定案、亲审接线/证据、核心文档、阶段提交、门禁 | root：根三文档/本轮文档/微小集成；tests或代码重修交原owner | D经验表先核并锁SHA；P/W先接口协商后并行，D后段回放等P集成 | 亲审实际diff；同版证据复用；冻结十检查统一一次 | 全范围 | 两独立门禁及主会话经验判断通过才交付 |

## 当前状态与编排
| 任务 | 机制实现 | 正式接线 | 针对性验证 | 用户结果 | 当前安排 |
|---|---|---|---|---|---|
| D | 原件/特征与经验表已亲审接收，CLI实现中 | CLI复用decide | 9真实/3补充案例已冻结 | 候选尚未验 | /root/adaptive_audit；允许P/D运行候选后整段回放 |
| P | 整包交回，root亲审正式路径/消融/时序修正及跨合同work-end | decide→经验特征/维护场景→同源evaluate；原接口保持 | 最新6文件89项；特征增轴对照与历史可知性证据；真实规模单次约0.5–0.6秒 | D连续旅程与费用敏感性待判 | /root/empirical_policy已交回；无上线 |
| W | 10文件修订包已交回，root亲审接收G7整改 | 原生Compact/Noting采集及显式导入→snapshot→估计 | 首包13项、既有63项；轮转/干扰10项、partial1项、读取失败1项 | 整轮门禁未验 | /root/empirical_wiring已交回；待集成检查/门禁 |
| I | 依据已冻结 | 未集成 | 尚未 | 未验 | root统筹 |

共享接口初稿：同Secretary事件表kind=maintenance_sample，component=compaction/noting，at/available_at、model_identity/model_contract、operation_id、outcome、context_before/after、duration_seconds、block_seconds、usage四token桶、source/proof、verified。缺测保持None；费用由当前倍率从raw usage计价。Compaction与Noting真实有关联才称同操作完整账单；历史分项分布组合标条件模拟。最终字段由P/W共同明确记录，不变用户语义；D使用同schema导出，W提供显式本地可测导入路径。P不增独立调度器/路由，D不复制策略。

**P/W已对齐接口：** `joint_operation_id`仅真实admission关联时出现；start_at/at=end/available_at=end（运行直接观测，回溯证据另标可知性）；model_identity/contract是组件实际模型，parent_model_key关联父；usage互斥四桶，input_tokens为fresh且显式input_semantics=fresh，与旧request.total区别。usage_complete仅dispatch/结算相符且全桶已知；duration_scope=component_execution；Compact block_scope=native_compaction_registration，Noting block_seconds=0/background_not_main_block。无效context_after<=0为None；proof有界dict。W提供normalize_sample/import_samples给D；P优先真实joint，历史边际组合仅条件模拟。

**W额外接缝（root已读并批准）：** agent/compression_facade.py只围既有调用ContextVar关联并跨worker传递；agent/auxiliary_hooks.py物理回执数值旁路；agent/usage_read.py绑定Noting子任务数值观测。observer-only/fail-open，不注册全局hook、不保存正文，不改变关闭路径。streaming首回执不能冒完整usage；超时/取消迟到回执不跨operation/owner。

**G7轮转接缝补充（root完整读后批准）：** `agent/context_compaction_request_publication.py`的`publish_native_commit`现有成功分支可增加fail-open只读observer，沿本次ContextVar collector冻结原生commit的old→new及现成已落盘边界，finished验证仍是本次合法发布。不得更改publication marker／cache prefix／请求状态／持久提交，不新增身份或admission门禁；scope外不新增状态。真实compress_context＋SessionDB轮转验证，仅summary外部边界受控。

## 缺陷与整改
| ID | 要求/触发 | 事实/影响 | 优先级 | owner | 关闭条件 | 状态 |
|---|---|---|---|---|---|---|
| G1 | R6/R7真实策略验收 | 旧历史仅预测分数、合成正例90K/600秒不对应线上 | P0 | D/root | 案例预期冻结＋真实逐时策略/闭环及人工判定 | 开放 |
| G2 | R3/R4维护经验建模 | usage_complete=false与native注册范围导致费用/时长不学习 | P0 | W/P | 经验组件与正式后继采集均接入；新样本改变估计 | 开放 |
| G3 | R1/R2/R4同源预测 | 无足够阶段工程及独立风险门持续否决 | P0 | P | 可解释特征作用、同源经验风险费用、实际反例关闭 | 开放 |
| G4 | R5/R7长期延后 | 六小时反复拒绝且无真实整段验收 | P0 | P/D | 真实有收益机会可执行，过早/频繁维护反例保护 | 开放 |
| G5 | R3–R6共同外部需求 | E06无真实用户操作却随机抽中explicit_interrupt，虚构Stop使重复维护；首版保留 | P1 | P/D | 明确用户取消随共同真实动作，内部失败继续采样，取消费用/未知/截尾不删除 | 整改中 |
| G6 | R1/R4/R5亲审 | 增长轴作用、恢复费用未知敏感性及模拟越原生容量阈值需闭环 | P1 | P | 特征作用/消融、费用来源与压力对照、共同容量责任边界证据 | 整改中 |
| G7 | R3/R8正常Session轮转 | _sample_parent_matches严格旧session相等，正常压缩轮转后会提前return，丢after和state_refresh；首包测试未覆 | P1 | W | 本次commit observer+持久路径见证；真实compress_context/SessionDB轮转、分支/后继/rewind/runtime替换及读取失败证据在wiring/rotation-* | 实现关闭，root已亲审；待独立门禁 |
| G8 | R1/R3/R6特征可知时间 | excluded裸区间参与origin向量，若仅结束后回填／导入可知则可能提前暴露维护缺口 | P1 | P | 原生feature_exclusion_events保可知时间，裸tuple仅成熟label；end1000/known1500不改500/1200特征、已知start300可改500，见policy/knowability-tests.log | 实现关闭，root已亲审；待独立门禁 |
| G9 | R5/R6/R7连续经验判断 | v4 E06/E08已执行维护；E03/E07各自短截点费用负差，需区分结算截断与过早维护；不能独立片段重置旧大context冒连续行为 | P1 | D/root | 保原9段/预期/负结果；补E01→既有取证终点连续旅程、阶段投影及E03/E07共同终点对照；主会话逐段判定 | 补证中 |
| G10 | R2/R8工作结束保护跨模型 | root实测E03的user end=1793765542.519，价格合同过滤后last_user_work_end却1793722340.320；v4 12:38:59维护距实际12:12:23结束仅26m36s | P1 | P/D | 同owner已知真人工作结束时间跨合同保留，工作量/费用仍分层；P最新89项含跨合同/迟到/外来历史隔离；D重验相应片段 | 机制关闭，真实回放补验中 |
| Q1 | R9统一质量检查 | 首次十检查8项通过；本轮health HX011在轮转测试分派 | P2 | W/root | handler映射等价整改，6场景原断言保留并通过；root-health-recheck.log为0阻断/0提示 | 已关闭 |

检查范围说明：root统一检查执行于暂存31文件，日志`root-quality-check.log`；唯一剩余no-tmp指向未修改的`.autonomous/20261031-evidence-recovery/validation.md:20`，HEAD与冻结24fe50ff的blob均`35daf5563d97496728892feb281ba89f5a7eb724`。保留历史报告和冻结规则，不冒称十项整体通过；这是既有范围外失败，不是本轮新增豁免。质量检查后仅等价改测试并定向复测health。

## 取舍、快照与续接
24fe50ff为冻结依据（含本会话已写调查/确认）；baseline.txt此后纳入。README/AGENTS已在基线树无需空改。原Huawei目录未跟踪不碰。现有main工作树只含本会话文档修改，故原目录切开发分支，不另建worktree。hook与原件一致，冻结提交已推同名功能分支。仅标准库数值算法及本地隔离测试，无新付费模型需求。阶段报告不称上线或实测节费。gate报告待独立角色创建，不预填PASS。

**root工程设计接收：** P使用多尺度真人/背景特征、可知历史片段/有证据quiet锚点、条件剩余空档与回归后工作，32条共同需求路径×最多12维护情景；风险与费用同源，15%/30秒/短离开与频度限制保留。共同比较窗口取历史支持长度、最多24h，另报6h/24h敏感性；不能只扩大窗口凑正例，须核共同终点/剩余责任。完整失败/慢样本、右删失、未知覆盖均保留，历史采样归一化有来源及消融。该数学实现为本轮授权范围内Agent工程取舍，非用户逐项亲定。

**新增只读证据：** root仅SSH取数值，gpt-noting-20261102-source.json、gpt-compaction-source.json、compression-boundaries-source.json在本轮ignored目录。GPT Noting32请求2.279M等价/1702秒来自778492首prompt规模；Compact11/2、11/4原生attempt218/292秒，native粗估749494→45997及430886→46745。GPT compact费用未留独立账单。11/6新compact在原16:09截点之后，不倒灌此前训练，仅后验留出。原始来源SHA保留，D须审可知性及代理范围。

**经验里程碑已在候选运行0次时亲审冻结：** root完整读D三文并与先前逐事件取证核对，接受E01–E09/M01–M03。`experience-cases.json` SHA256 `449d078fdba53e7765306aa7649a5183daaccbe878fd4553ce0e9a0a33cd448a`；data-analysis.md `3fbf0ea3bc30d9f34f8d739818d7d0df9d123dbbc5a2f8f0c652d9164e420b31`。9份原件由input-manifest冻结。E06约21h及E08约46h为主要有收益机会验收，基础经验情景全程不维护须整改；高成本/慢尾部敏感性可拒绝，不能调整基础成本凑PASS。E03 173K/5h仅1HB、E09平台只作条件判断，不一概强压。E01/E02/E04/E07保护活跃/短返；E05背景不能冒真人。E01跨epoch初态用新epoch67817，旧464730不得混入。M02原basis指旧缺done，新telemetry已证cancel/failed须在后续覆盖，resolved不能双算失败。43组件当前投影SHA948c25b5ed6b61b9b46773e32483b55908b9070db030a43bd3ffa15720fbd86d，接口规范化可形成新投影但原件与经验预期不可按结果改。
