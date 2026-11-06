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
| D | 原件/特征调查中 | CLI复用decide | 待案例冻结 | 未验 | /root/adaptive_audit；先完整数据/案例里程碑，主会话过目后候选可运行 |
| P | 设计已审、实现中 | 旧decide接口保持 | 待D冻结后候选运行 | 未验 | /root/empirical_policy；经验同源风险/费用，不跑未冻结案例 |
| W | 原生接缝已核、实现中 | 采集/导入owner | 待 | 未验 | /root/empirical_wiring；按共享schema，正常运行可持续更新 |
| I | 依据已冻结 | 未集成 | 尚未 | 未验 | root统筹 |

共享接口初稿：同Secretary事件表kind=maintenance_sample，component=compaction/noting，at/available_at、model_identity/model_contract、operation_id、outcome、context_before/after、duration_seconds、block_seconds、usage四token桶、source/proof、verified。缺测保持None；费用由当前倍率从raw usage计价。Compaction与Noting真实有关联才称同操作完整账单；历史分项分布组合标条件模拟。最终字段由P/W共同明确记录，不变用户语义；D使用同schema导出，W提供显式本地可测导入路径。P不增独立调度器/路由，D不复制策略。

**P/W已对齐接口：** `joint_operation_id`仅真实admission关联时出现；start_at/at=end/available_at=end（运行直接观测，回溯证据另标可知性）；model_identity/contract是组件实际模型，parent_model_key关联父；usage互斥四桶，input_tokens为fresh且显式input_semantics=fresh，与旧request.total区别。usage_complete仅dispatch/结算相符且全桶已知；duration_scope=component_execution；Compact block_scope=native_compaction_registration，Noting block_seconds=0/background_not_main_block。无效context_after<=0为None；proof有界dict。W提供normalize_sample/import_samples给D；P优先真实joint，历史边际组合仅条件模拟。

**W额外接缝（root已读并批准）：** agent/compression_facade.py只围既有调用ContextVar关联并跨worker传递；agent/auxiliary_hooks.py物理回执数值旁路；agent/usage_read.py绑定Noting子任务数值观测。observer-only/fail-open，不注册全局hook、不保存正文，不改变关闭路径。streaming首回执不能冒完整usage；超时/取消迟到回执不跨operation/owner。

## 缺陷与整改
| ID | 要求/触发 | 事实/影响 | 优先级 | owner | 关闭条件 | 状态 |
|---|---|---|---|---|---|---|
| G1 | R6/R7真实策略验收 | 旧历史仅预测分数、合成正例90K/600秒不对应线上 | P0 | D/root | 案例预期冻结＋真实逐时策略/闭环及人工判定 | 开放 |
| G2 | R3/R4维护经验建模 | usage_complete=false与native注册范围导致费用/时长不学习 | P0 | W/P | 经验组件与正式后继采集均接入；新样本改变估计 | 开放 |
| G3 | R1/R2/R4同源预测 | 无足够阶段工程及独立风险门持续否决 | P0 | P | 可解释特征作用、同源经验风险费用、实际反例关闭 | 开放 |
| G4 | R5/R7长期延后 | 六小时反复拒绝且无真实整段验收 | P0 | P/D | 真实有收益机会可执行，过早/频繁维护反例保护 | 开放 |

## 取舍、快照与续接
24fe50ff为冻结依据（含本会话已写调查/确认）；baseline.txt此后纳入。README/AGENTS已在基线树无需空改。原Huawei目录未跟踪不碰。现有main工作树只含本会话文档修改，故原目录切开发分支，不另建worktree。hook与原件一致，冻结提交已推同名功能分支。仅标准库数值算法及本地隔离测试，无新付费模型需求。阶段报告不称上线或实测节费。gate报告待独立角色创建，不预填PASS。

**root工程设计接收：** P使用多尺度真人/背景特征、可知历史片段/有证据quiet锚点、条件剩余空档与回归后工作，32条共同需求路径×最多12维护情景；风险与费用同源，15%/30秒/短离开与频度限制保留。共同比较窗口取历史支持长度、最多24h，另报6h/24h敏感性；不能只扩大窗口凑正例，须核共同终点/剩余责任。完整失败/慢样本、右删失、未知覆盖均保留，历史采样归一化有来源及消融。该数学实现为本轮授权范围内Agent工程取舍，非用户逐项亲定。

**新增只读证据：** root仅SSH取数值，gpt-noting-20261102-source.json、gpt-compaction-source.json、compression-boundaries-source.json在本轮ignored目录。GPT Noting32请求2.279M等价/1702秒来自778492首prompt规模；Compact11/2、11/4原生attempt218/292秒，native粗估749494→45997及430886→46745。GPT compact费用未留独立账单。11/6新compact在原16:09截点之后，不倒灌此前训练，仅后验留出。原始来源SHA保留，D须审可知性及代理范围。
