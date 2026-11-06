# Verification：20261106-adaptive-empirical

## 1. 审查对象与结论概览

审查者：独立`verification_empirical_r1`；UTC 2026-11-06。本轮依据为Snapshot Index及`baseline.txt`所指`24fe50ffcf588e9846b1902b0ad0f6cf62520924`，待审产品与实际HEAD均为`1ae2b0f268eace9516de5f2633a089752e9f4e3c`。审查范围是U1–U3/R1–R10及指定继承执行/来源边界；没有重新导入旧公式、旧Idle串行或未确认愿景。

**Verification门禁不通过：31条符合，1条违规（S2/G17），0证据不足，0整条不适用。禁止进入Validation。** 条款内的UI视觉/付费模型/生产真实节费无本轮要求，不冒执行。本轮真实经验基础路径有有效成果，但正式V2零经验时仍可被固定维护先验驱动，未满足R3；不得以已有回放通过宣告全范围完成。

先仅读两个适用Skill、索引/版本和冻结原文，再于13:24:50 UTC落盘第2节；之后才读根AGENTS/CLAUDE/README、agent/tests指导、实现和证据。未派生、未改产品/测试/规则/用户资料、未生产/联网/模型/UI/提交。独立取证为原件/源码SHA审计、当前JSON一致性审计、两个固定历史时点的当前特征消融，以及1项按R3设计的缺维护经验负向测试（失败复现G17）；未重复大型套件或完整回放。

证据统一前缀：`E=.hermes-dev/adaptive-empirical-20261106/`（ignored本地）；§3短文件名均位于E，产品路径除agent/scripts/tests外均位于`secretary/`。完整数据留ignored，不复制个人原文或标识入本报告。独立证据：`E/verification-r1/criteria-initial.md`、`hash-audit.json`、`json-independent-audit.json`、`current-feature-counterevidence.json`、`test_missing_maintenance_evidence.py`、`missing-maintenance-evidence.log`。

## 2. 独立要求清单与覆盖
判据建立于 2026-11-06T13:24:50.560502+00:00。在此时点仅阅读两项Skill、Snapshot Index/baseline及冻结原文；未读取实现、测试、动态CLAUDE或实现报告。以V2 U1–U3/R1–R10为当前权威，继承117–232来源/导入/初始化/隔离及582–598 E1–E7；07只继承顶部10/28联合解耦、11/1取消及§8.15接口执行边界。旧被替代数学公式、旧Idle串行规定与未确认愿景不新增要求。直接要求与必要推导均在每行表述；工程路径薄弱项标记机制，不预定实现命名。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| U1 | V2 U1 | 目标/历史工程 | 先分析真实历史重要信息再联合决定m/T/δ；分析须影响策略而非挂名 | 历史分析、重要性及正式联合选择均有证据 | §3 U1 |
| U2 | V2 U2–U3 | 完成边界 | 真实历史经验逐段通过；预测分数、合成维护正例、工程测试不能替代 | 真实预登记片段、动作及错失机会逐段复核；失败继续整改 | §3 U2 |
| D1 | V2 R1；117–232来源约束 | 数据来源 | 真人/HB/Reminder/未知分离；墙钟与有效context epoch不以累计input替代 | 源标记可信；epoch/事件时间明确，未知不补造真人 | §3 D1 |
| D2 | V2 R1 | 特征 | 多尺度活动/增长、趋势/持续、距真人/任务结束、剩余空闲、时段、回归批次、后台责任、容量收益均须分析 | 每类有可用性和作用/消融证据；不只phase标签 | §3 D2 |
| D3 | V2 R2 | 判断顺序 | 先工作/短暂停顿，再可整理空档，再收益；不把后台增长当真人持续工作 | 正式选择可追溯上述条件；时段从历史学习，无任务语义不宣称任务结束 | §3 D3 |
| S1 | V2 R3/R6；117–232可知边界 | 机制/时点 | 每次决策只看当时已可知历史；训练成熟不泄漏未来 | 原发生/可知/导入时间同时门控；未来只用于事后评分 | §3 S1 |
| S2 | V2 R3 | 机制/稀疏估计薄弱处 | 回归时间/工作量/维护费用/阻挡/缩减/失败须有真实来源；不足可分层组件不能任意常量 | 分层/归一化可追溯，不删长耗时失败以造正例；跨模型行为保留 | §3 S2 |
| S3 | V2 R4 | 机制/同源路径 | 未来回归风险与费用同源经验路径/维护样本；独立保守概率不可永久否决机会 | 风险/成本共用来源并经真实经验验收，显式体验上限保持 | §3 S3 |
| C1 | V2 R4；07顶部10/28、11/1 | 成本/执行 | 普通Noting与Compact并发，Compact不等Noting；联合费用含失败取消恢复 | 计费全量，阻挡仅实际阻挡Main阶段；部分结果不冒成功 | §3 C1 |
| C2 | V2 R5 | 比较机制 | 同外部需求、同初态、同终点；策略自生HB/维护/context/cache | 沉没费用不追回、窗口外费用不藏；状态分歧后重算 | §3 C2 |
| C3 | V2 R5/R7 | 长期选择 | 长期平台不能无限延期；不能到期必压缩；选择拒绝理由/敏感性可解释 | 逐段动作及错失机会，真实高存量有益空档存在时执行 | §3 C3 |
| P1 | V2 R6 | 回放来源 | 原件SHA/来源/缺口冻结；先片段预期再候选结果 | 预登记及其时间/版本可核；不按结果调预期 | §3 P1 |
| P2 | V2 R6–R7 | 经验覆盖 | 上升/平台/短离开/长空闲后台增/回归/无读取/失败取消缺数据均覆盖 | 真实无样本明确机制补充，不能伪称真实；整段逐一判定 | §3 P2 |
| P3 | V2 R6 | 回放假设 | 排期/覆盖/初态不能恢复须披露并敏感性 | 动作分歧后按策略context/cache重算，不沿旧曲线 | §3 P3 |
| P4 | V2 R7 | 经验结果 | 密集工作短离开不抢；低存量无后读不无益整理；后台不假忙且不无限延期；回归新工作收敛 | 预登记定性期待与真实整段结果相符，无全程不维护免责 | §3 P4 |
| W1 | V2 R8 | 正式接线 | 沿adaptive owner/数值事件/显式导入/Main结束/原子三量；正常路径可获取更新估计 | 真实输入至事件至学习至决策至采纳链完整，不仅离线脚本 | §3 W1 |
| W2 | V2 R8；117–232配置 | 隔离/兼容 | 自有表/API可选增量/关闭非eligible原生/Profile Conversation隔离/缓存Force保护 | 无新路由执行器调度器UI；故障不阻断用户 | §3 W2 |
| H1 | 117–232模型与来源继承 | 模型身份 | provider+原生模型选项，窗口与运行合同解释样本；模型切换行为历史不丢 | 同名不同provider及900k独立；旧计划失效；费用迁移披露兼容 | §3 H1 |
| H2 | 117–232导入 | 显式历史导入 | 声明后一次事务有界冻结快照，幂等冲突拒绝，来源事件去重不复制正文 | 不隐式搬运，截止后源变化不流入；原始/可知/导入时间及缺口保留 | §3 H2 |
| H3 | 117–232初始化/隔离 | 历史运行态 | 导入仅训练不继承当前context/活动idle/cache/HB/计划；既有历史不强制重等 | 各来源不拼无人时段；无coverage不伪造；同Conversation轮转延续 | §3 H3 |
| H4 | 117–232容量 | 资源/历史 | 最多2048实时与2048导入事件、128成熟窗口/32收据等既有边界保留 | 索引有界读取，不扫描聊天全库；重启coverage断开，模型cache按合同失效 | §3 H4 |
| E1 | 冻结582–598 E1 | 执行 | 真实Main结束同一快照三量原子采纳；d=e+δ；到期只复核不重算 | 用户/HB/Reminder皆同接缝；结束后更新策略但不复活已消费周期 | §3 E1 |
| E2 | 冻结582–598 E2 | 执行 | HB b为实际成功交接开始/原始锚点；不变模式不计时，变模式due=b+H | 模式变不set重建、不改计数b；忙保due漏tick合一次、失败退款正确 | §3 E2 |
| E3 | 冻结582–598 E3 | 并发 | 不可重复受理点判优先；claim结算前不改revision；已开始不被策略抢占 | pause/clear/Stop保持；自动更新与claim/refund竞态有证据 | §3 E3 |
| E4 | 冻结582–598 E4 | 计划失效 | 每Conversation至多一个未受理计划绑定end/epoch/config/period；新输入Main等失效 | 扫描不延后；到期拒绝/失败本周期终止；HB/Reminder不算真人 | §3 E4 |
| E5 | 冻结582–598 E5 | 优先级 | 用户/Reminder/原生安全优先；同到期合法Idle优先HB，不靠线程先跑 | 正式串行接缝判定；单到期不为另一额外等待；已受理不抢 | §3 E5 |
| E6 | 冻结582–598 E6 | 维护后 | 维护不改HB锚点计数；结束先真实结果和排队工作，再采策略/原b due | 失败取消无伪压缩自查；到期合一次，不重新完整周期 | §3 E6 |
| E7 | 冻结582–598 E7 | 安全/恢复 | m仅两模式、T真实占用/∞不关Force、δ非负；合法owner且至多一次版本采纳受理 | 重启绝对due恢复，不证明匹配则丢计划；计算持久化失败不执行未采纳计划 | §3 E7 |
| B1 | 07顶部10/28、11/1；R4/R8 | 继承取消/Force | Compact取消对应未提交Noting一起取消，已提交保留；Force唯一提前独立且不可取消 | 正常联合并发及原生容量保护维持，不扩大本轮前端或Note演进改造 | §3 B1 |
| B2 | 07 §8.15 | 继承Heartbeat | 目标Profile全局Noting选择正式UI宿主原生Main；Conversation owner/持久锚点并发tick唯一 | 后台恢复不误投焦点；pause/clear不复活；用户优先与原生关闭不变 | §3 B2 |
| Q1 | V2 R9 | 验证/资源 | 有界事件采样，官方PM环境，真实规模单次耗时内存；接线学习关闭失败取消模型切换重启失效验证 | 质量冻结不放宽；证据版本/规模/单次与总时长清楚 | §3 Q1 |
| A1 | V2 R10/U3 | 权限/交付 | 本地分支不合main不部署不触生产模型；原件仅ignored；不承诺未证实际节费 | 差异/证据边界与未部署结论清楚；三核心职责保持 | §3 A1 |

起始判据保存在ignored verification-r1/criteria-initial.md；后续改变必须在本节追加原文依据及理由。

## 3. 逐条实现证据

以下每行沿用§2原文/必要不变量作为判据，给出实际路径、条件、方法/结果与边界。符合结论不以测试数为依据。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| U1 | adaptive_runtime.py:185 finish_turn→snapshot:142→adaptive_features.build_features:428→adaptive_forecast.predict:268→adaptive_policy.decide:497→adaptive_store.commit_plan:149 | 独立读正式入口与数据分析/特征来源；当前两时点消融确认年龄/增长/时段与quiet origins改变预测，最终三量沿同一decision采纳 | data-analysis.md；policy/candidate-feature-comparison.md；verification-r1/current-feature-counterevidence.json | 符合：不是只加诊断字段，历史特征参与轨迹和候选费用/风险选择 | 仅证明本轮数值与接线；不证明语义任务结束、模型最优或生产节费 |
| U2 | Replay.run→_plan→_start_maintenance→_finish_maintenance；adaptive_empirical_replay_report.audit_case | 独立核9原截止/连续/共同终点及压力JSON，核主会话逐段表；基础E06/E08各1次完成且净差+597664/+2628378，主动保留E03/E05/E07/E09短窗负差 | experience-cases.json；candidate-v11-real.json；root-experience-review.md；verification-r1/json-independent-audit.json | 符合：预登记真实行为已逐段审查；未用工程测试/合成正例代替经验验收；但S2发现正式缺数据阻断，不能据经验路径宣布全部完成 | 通过本Verification不代表Validation完成或用户逐条认可；压力负结果非全PASS盈利 |
| D1 | adaptive_runtime.origin:29、web_input/gateway_input；request_observed:272；adaptive_empirical_features.growth_by_source:97 | 查可信入口标记、未知回退和event source；增长仅相同epoch非负端点差；历史按原生入口证据分类，不从role=user猜真人 | tests/secretary/test_adaptive_runtime.py:47/61/82；tests/secretary/test_adaptive_history.py；data-analysis.md | 符合：真人/HB/Reminder/未知分离，墙钟/epoch与累计费用分开 | 端点归因不是逐token因果；unknown仍未知，旧数据完整性不扩大 |
| D2 | adaptive_empirical_features.state:13→signature；adaptive_forecast._transition_weights:195；adaptive_policy._candidates:429 | 向量实为17维：15m/1h/4h计数、年龄/quiet、趋势、时段、增长、背景及unknown；24h计数/phase持续仅分析，旧候选增轴对照保支持和反向结果；当前预测消融补证 | data-analysis.md；policy/handoff.md；policy/candidate-feature-comparison.*；verification-r1/current-feature-counterevidence.json | 符合：多尺度活动/增长、持续/趋势、机械结束、剩余空闲、时段、回归批次、背景责任与收益均有分析；候选未入模有对照理由 | 候选对照较早SHA只支持保留/不加轴的设计分析，不能当当前精确预测；当前两点消融不能证明普遍预测优越 |
| D3 | adaptive_policy._eligibility_reasons:221→_candidates→_evaluate_maintenance:274；features.last_user_work_end及current_activity_evidence | 先保当前观测/真人短离开与高真人增长，再检查可执行空档/已知Reminder冲突及碰撞等待，最后比较净费与末态责任；时段sin/cos由历史近邻作用，semantic_task_end=unknown | policy/cross-contract-work-end-tests.log；policy/e09-final-tests.log；candidate-v11-real.json | 符合：长Turn刚结束亦受1800保护，HB背景增长不重置真人年龄，无夜间无人硬编码 | 没有任务语义终结证据；phase是可观察活动近似，不代替任务语义 |
| S1 | adaptive_features.clean_events:23；adaptive_forecast.visible:17/_training_examples:107/outcome:60；adaptive_store.imported_history_conn:69 | at与available_at门控、imported_at额外门控；成熟完整窗口才成标签；裸excluded仅删失不回流过去特征；独立查所有当前JSON visible_event_max<=decision.at | policy/knowability-tests.log；tests/secretary/test_adaptive_empirical_policy.py:145/156/177/225；verification-r1/json-independent-audit.json | 符合：未发现未来事件进入决策；原生已知start可进入当前特征，后知end不提前进入 | 回放coverage是明示回溯条件，不声称恢复了历史每一版coverage；raw_coverage压力另列 |
| S2 | adaptive_policy._maintenance:55直接调用adaptive_cost.maintenance_profile:52；无经验scenario→旧显式prior fallback→_evaluate_maintenance→checked T | 真实有经验路径使用128 origin/32轨迹及完整组件，原件/贵失败样本保留；但独立负向测试给充足行为history、零maintenance事件，配置90K/600s/.18即可正式decide得business/T32768/δ0，cost/duration/retained样本全0；并非真实历史正例，而是合法缺数据反例 | root-empty-maintenance-prior-probe.json；verification-r1/test_missing_maintenance_evidence.py；verification-r1/missing-maintenance-evidence.log；adaptive_cost.py:52–109 | **违规：G17/P1。** V2 R3明确不能任意常量代替应有历史维护建模；正式V2未阻止compatibility explicit_prior驱动提前整理。稀疏不完整sample会拒绝，但完全无sample反而走旧prior，存在缺数据逃逸 | 不推翻v11有经验历史主路径结果；既有旧正文允许prior已被V2相关要求覆盖，不能当新正式路径豁免。必须修复并新全范围独立复审 |
| S3 | adaptive_policy._evaluate_maintenance:274→adaptive_rollout.evaluate/simulate_path；_risk_allowance | 费用/开始/碰撞/等待来自相同32需求路径×维护scenario，原Poisson conservative曲线不再作独立维护否决；15%/30s不变；取消反馈只按已证原因 | tests/secretary/test_adaptive_empirical_policy.py:118；policy/cancel-training-support.json；execution-audit-v11.json | 符合：维护风险与费用同源且真实机会基础情景实际执行；独立保守概率未永久否决 | 需求与组件池组合是条件模型，不是有足够同操作数据证明的相关联合分布；明确来源敏感性和无因果收益声明 |
| C1 | agent/compression_facade.py:297 _run→scope→auxiliary_hooks；noting_child.py:862/898；adaptive_samples.Collector；adaptive_empirical_maintenance._combine:104 | Compact原生执行不等待Noting；两组件费用相加，阻挡只Compact registration；dispatch/receipt不齐为unknown，paid lower bound保留；失败不缩context、真实Stop用付费截尾分支 | wiring/report.md；wiring/wiring-final.log；wiring/rotation-final-tests.log；tests/secretary/test_adaptive_empirical_policy.py:31/101；mechanical-failure-v11.json | 符合：费用与阻挡没有混成Noting总历时，成功/失败/取消有不同真实状态 | 未消费stream、硬杀无终态与SDK内部opaque retry不补完整账单；注册历时是实测段，不保证完整端到端用户租约上界 |
| C2 | adaptive_rollout.simulate_path；Replay._charge/_start_job/_start_maintenance；CLI.run固定对照 | 共同外部真人/Reminder、同初态/截止；HB由策略自生，context/cache/忙态随自己动作；初态跨epoch用新epoch67817，旧花费不回收；末期已受理工作/维护结算纳入 | candidate-v11-real.json；journey-e01-v11.json；continuation-e03-v11.json；tests/secretary/test_adaptive_empirical_replay.py:61/116/147/157 | 符合：对照不是把旧HB曲线直接套候选；没有将历史已付花费算收益或无证据越过容量 | 真人外部工作足迹增量是条件代理；未复原的suffix、最后tail/输出增量和busy假设明确，不能称账单复原 |
| C3 | adaptive_policy._comparison_scope:129/_checked_selection:414/_sensitivity:459；Replay全段 | 窗口按历史转移支持有界延伸而非年龄到期；checked整数T仅承诺该点可行；候选逐项拒因、6h/24h/整账单/恢复/unknown取消压力输出；真实E06/E08执行、重复维护边际独立对照 | policy/threshold-implementation.json；policy/threshold-final-tests.log；repeat-maintenance-v11.json；replay-review.md | 符合：没有长期平台永不维护或到期必维护；选择/拒绝与敏感性可检查 | 不证明T为全域最小/单调阈值，不证明每一片段事后盈利；终态冷读压力不是已兑现收益 |
| P1 | adaptive_empirical_replay_data.prepare:94；experience-cases.json→replay-input-final.json→CLI.run | 独立重算9原件SHA、75源码SHA、经验SHA449d078…448a；经验candidate_runs=0与主会话结果前冻结记录相符；首版预期及E01事实补正保留 | verification-r1/hash-audit.json；experience-cases.pre-review-v0.json；plan.md经验里程碑（只核冻结时序，不作判据） | 符合：原件/源版本及原预期可回查；后续未按结果改片段/费用/seed | 本审查不对个人原始来源作外部联网重采；复用已冻结数值及其来源证明 |
| P2 | experience-cases E01–E09/M01–M03；Replay.run/audit_case | 9段覆盖上升/短离开/平台/后台长闲/回归；真实无后读和可用Stop执行点缺失明确用机制补充；真实机械失败情景单列；未知终态不补成功 | experience-cases.json；replay-review.md；policy/cancel-origin-complete-audit.json；tests/secretary/test_adaptive_empirical_policy.py；tests/secretary/test_adaptive_empirical_replay.py | 符合：真实与声明机制分支没有混报；上升不抢、长闲执行、失败付费与不缩减均有证据 | M01/M02/M03是机制证据，不伪称9段里发生过无后读或Stop；本轮无新增真实模型要求 |
| P3 | Replay.__init__/_known_history/_snapshot/_charge/_finish_maintenance；coverage_at:135 | 读完整回放状态机及observer；observer只追加审计字段，CLI E02前置校验原动作/决定精确相同；维护后使用候选context/epoch，mode-only后state_refresh可见，不贴回历史大值 | observer-preflight-v11.json；execution-audit-v11.json；stage-change-v10-v11.json；verification-r1/json-independent-audit.json | 符合：完整状态分歧、共同终点、原coverage/known排期/初态相位都披露且有raw coverage/unknown Reminder/initial hot/来源对照 | 保留v10遗漏mode-only的负证据；不能以数值没变声称旧版本来已覆盖；真实排期改变的因果反事实不可证 |
| P4 | Replay.run实际actions/states→主会话逐段判断 | 独立核E01/E02/E04零维护；E07恢复后保1800且连续旅程继承94.8K→102.8K不重复压；E06/E08基础有益，E03/E05/E07/E09短截止亏损原样保留，E03共同终点与重复维护边际对照补责任 | verification-r1/json-independent-audit.json；root-experience-review.md；replay-review.md | 符合：原预期未要求每个平台/每个压力样本事后必盈利；主要有益机会通过，未出现后台冒真人或无限延期 | E07独立大context共同终点仍亏121905；E09短窗亏6776；当前模型/机械失败压力非全盈利，必须继续展示 |
| W1 | 真实入口标记→request_observed→Collector→state.db events/imports→snapshot→maintenance_profile→finish_turn→commit_plan | 审正式native Compact facade/aux relay及真实Noting Loop测试；显式导入后snapshot可读；native新费用收据确实改变maintenance estimate，非仅离线脚本 | tests/secretary/test_adaptive_empirical_wiring.py:76/122/287/306；wiring/wiring-final.log；wiring/integration-final-tests.log；wiring/rotation-final-tests.log | 符合：正常运行可采集和更新经验估计，真实同operation关联而非字串猜owner | 硬杀缺终态只留usage lower bound；正常运行自然积累需要本来发生维护，不为证明接线触生产模型 |
| W2 | adaptive_runtime._read_owner:42；adaptive_config.for_db；adaptive_samples.start/finish fail-open；native接缝最小旁路 | 只增Secretary侧数值状态/可选字段，旧API参数/返回及关闭分支维持；读owner Profile配置/DB/ref；异常日志后主流程继续；diff无新调度器/路由/UI/Prompt改造 | git diff baseline..product；wiring tests disabled/cross-owner/inflight；tests/secretary/test_adaptive_bootstrap.py:147 | 符合：native/Force与缓存前缀owner不变，新机制仅显式eligible adaptive分支；未见个人资料入Git | 新增imports无正文副本；未部署真实服务器和UI，数值修改不要求用UI或真实模型补证 |
| H1 | adaptive_model_config.parent_contract；adaptive_config.for_db；compatible_forecast_events:404；build_features.last_user_work_end | provider+完整原生选项身份；运行合同控制token工作量，行为结束时序跨合同保留；窗口改旧计划invalid；mixed turn不删半轮冒完整 | tests/secretary/test_adaptive_model_config.py；policy/cross-contract-work-end-tests.log；current-model-v11.json；current-model-whole-v11.json | 符合：模型切换不清空历史行为；费用/速度跨模型借用有标签和压力而非当本模型实测 | 继承完整原配置/metadata接线，本轮不建立第二选择器；同模型身份不证明完整reasoning/速度一致 |
| H2 | adaptive_import.preview/apply/_freeze:317/import_samples:393；adaptive_store.imported_history_conn:69 | 同事务容量/幂等冲突/来源proof，保原始/可知/导入时间；跨Profile拒绝，component_pool不冒目标亲历；同ID不同payload拒绝，原件只读 | tests/secretary/test_adaptive_empirical_wiring.py:142/172/183/287；wiring/wiring-final.log；tests/secretary/test_adaptive_import.py | 符合：普通Turn读取不隐式复制，导入后源变化不流入，冻结事件与收据由目标拥有 | 导入component pool只是显式声明数值证据池；不是凭SHA即可证明Conversation归属 |
| H3 | adaptive_learning._source:24/extend_features:69/extend_bootstrap:114；adaptive_bootstrap.read；snapshot | 来源独立/覆盖重叠减去/维护缺口删失；不跨来源拼静默；目标last_user/context/HB/plan不迁移；8成熟30m条件窗口能就绪且online原值分报 | tests/secretary/test_adaptive_bootstrap.py；tests/secretary/test_adaptive_learning.py；tests/secretary/test_adaptive_import.py:308；wiring/wiring-final.log；policy/cross-contract-work-end-tests.log | 符合：旧历史可用且不重等上线后8次/6h；导入不授当前执行静默资格；同Conversation轮转无需搬迁 | bootstrap grade是受限持久提交条件序列，不能冒完整在线coverage；新会话未有自己活动仍原生 |
| H4 | adaptive_store.history/event_conn；adaptive_import._freeze；forecast.training_examples/predict；adaptive_observation.touch | 每owner 2048当前+2048导入、32总收据、128窗口/32粒子/256path、最多12维护scenario有界；索引查询不扫正文；coverage原位更新且restart/gap断开 | source lines；tests/secretary/test_adaptive_bootstrap.py:343；tests/secretary/test_adaptive_observation.py；policy/import-window-tests.log；final-resource.json | 符合：事件/采样/状态容量有界，独立维护导入不被本地2048新请求挤掉 | 2048事件不是14天完整历史；SQLite文件/RSS/WAL总量不等于Python增量峰值 |
| E1 | noting_turn_boundary→noting_runtime._record_main_turn_event:328→finish_turn:185→commit_plan:149；runtime._maintenance:297 | Main结束e生成一份decision绑定period，m/T/δ同事务；due=e+δ；到期只读计划门槛不重算；maintenance finish仅adopt_mode不重挂Idle | tests/secretary/test_adaptive_store.py；tests/secretary/test_adaptive_integration.py；replay-mode-refresh-tests.log；execution-audit-v11.json | 符合：真实User/HB/Reminder Main共用正式结束接缝；维护后mode-only与新Idle计划分开 | 未知来源保unknown不伪真人；fallback保原生，维护mode-only计算出的T/δ未采纳 |
| E2 | heartbeat_store.claim/load/_effective_interval/_effective_anchor；adaptive_store.adopt_mode_conn:114/settle_claim_conn:128；Replay._schedule_hb | 采纳模式只改effective interval，不调用set、不改b/count；实际claim更新锚点，未启动失败refund；busy保due/coalesce；独立JSON核原anchor/actual HB的审计 | tests/secretary/test_adaptive_store.py；tests/secretary/test_adaptive_integration.py；execution-audit-v11.json；replay-mode-refresh-tests.log | 符合：不因普通Turn/维护重起整个周期；到期模式变化按原b重新算 | 真实后端claim由既有事务实现；回放是确定性执行模型，不能独证多进程DB竞争 |
| E3 | adaptive_store.adopt_mode_conn pending/settle_claim_conn；heartbeat_store.claim_is_current/refund/set_status；原生run_conversation admission | claim未结算时pending保存模式，revision不被自动改破；pause/clear令旧claim失效，refund只撤自己revision；已执行不被新策略取消 | tests/secretary/test_adaptive_store.py；tests/secretary/test_adaptive_integration.py；tests/secretary/test_conversation_heartbeat.py；wiring pending/late tests | 符合：自动模式更新不篡改用户操作或抢已开始动作，正式owner事务保持至多一次 | 本轮不新增通用admission，不承诺用户零等待；原生权限和输入排队继续 |
| E4 | user_arrived→invalidate_conn:138；turn_started；commit_plan；idle_settings/_idle_plan_valid；noting_timers._fire/attach | 单owner一计划，绑定end/epoch/config/path/period；新输入/新Main、窗口/config/owner/关闭失效；attach读绝对due不延长；到期消费后失败不自动重挂 | tests/secretary/test_adaptive_integration.py；tests/secretary/test_adaptive_policy_wiring.py；tests/secretary/test_adaptive_empirical_replay.py:124/192；wiring/rotation-final-tests.log | 符合：HB/Reminder的新Main会替换计划但不冒真人；旧timer不能借新计划执行 | 重启恢复无法证明匹配回原生并退休旧early due，不从restart重计合法绝对时刻 |
| E5 | heartbeat_store._adaptive_priority_held:187/_adaptive_idle_precedes:147→claim同事务；request_idle_joint原生lease；Replay._push | Reminder registry/native route/plan版本与C>=T同接缝判优先，用户持久队列/lease优先；同到期合法Idle先HB；单到期不额外靠近窗口；审1401个HB无ready external抢跑 | execution-audit-v11.json；tests/secretary/test_adaptive_integration.py；tests/secretary/test_adaptive_empirical_replay.py；source paths | 符合：未见timer线程抢跑充当产品优先级，原生容量保护不被policy T压制 | 回放不重建多线程调度本身；多宿主至多一次由原事务/claim继承与机制测试支持 |
| E6 | runtime._maintenance:297 settle→snapshot→decide→adopt_mode→state_refresh；Replay._finish_maintenance | 原耗费/结果先结算，mode-only不重挂；后续执行仍由原队列优先用户/Reminder，HB原b；26次维护对应26刷新，25后继可见+1终点无后继 | replay-mode-refresh-tests.log；execution-audit-v11.json；verification-r1/json-independent-audit.json；native partial测试 | 符合：维护不冒自查，不重置HB锚点；失败取消真实结算；刷新不产生新Idle，用户/Reminder仍先于后续HB执行 | 策略mode-only可在排队Main执行前计算，但不先执行动作/取消工作；Main结束再以新状态重算，受理优先级不被改 |
| E7 | validate_decision；commit_plan；idle_settings/_restore_native_idle；request_idle_joint owner lock；noting_timers attach | m两档/δ有限非负/T正式测量；∞通过None仅取消early Idle；Force检查仍在note_main_turn_finished；异常fail-open；旧owner/running/不匹配路径拒绝 | tests/secretary/test_adaptive_integration.py；tests/secretary/test_adaptive_policy_wiring.py；wiring/rotation-final-tests.log；policy/threshold-final-tests.log | 符合：非法未采纳计划不执行，绝对时钟重启和版本相关性保留；checked T用新分段缩减函数实际校验 | 原生容量所需费用不明时policy fallback，回放拒无证据越界，不声称证明溢出后费用最优 |
| B1 | request_idle_joint→noting_compact.request_parent_compaction→compression_facade；noting_joint/native link与Force end owner | diff只加数值observer，普通联合并发/取消原owner维持；已有有效Note不回滚，Force唯一提前独立不可随Compact cancel；不修改Notebook提交/注入契约 | 07适用原文；source diff；wiring/rotation-final-tests.log；tests/secretary/test_noting_child.py既有证据 | 符合：没有把旧Idle串行稿重新带回；新增采集不等待Noting、不开新整理执行器 | 本轮不重验全部Notebook/UI演进，因未变且不属数值改动范围；取消流式UI无改动不新增UI验收 |
| B2 | heartbeat_store owner/ref+heartbeat_route+既有UI宿主入口；adaptive模式只effective_interval旁路 | 目标DB/Profile/Conversation约束、paused/cleared不复活、同tick claim单次；模板和正式run_conversation/模型路由不变；后台来源仍明确HB | source diff；tests/secretary/test_conversation_heartbeat.py；tests/secretary/test_adaptive_integration.py | 符合：继承§8.15接口/执行边界，不按焦点/页面状态改owner，无独立HB Agent | 隐藏IAB/UI/真实模型在纯数值本轮有据不需要；本报告不声称验证了UI视觉或生产触达 |
| Q1 | bounded policy/forecast/scenarios/store；正式PM runner logs及冻结检查 | 核当前final-resource明确249历史/43组件，单次无trace0.185s、trace2.121s增峰1025839B；更大774+43旧阶段0.750s明确原SHA；矩阵408.459s不冒单次；health真实HX011已修并定向6场景+health零阻断 | final-resource.json；policy/work-end-resource.json；final-run-matrix-v11.json；root-quality-check.log；root-health-recheck.log；verification-r1/hash-audit.json | 符合：当前真实规模、资源边界与按影响复测已记录；规则未改/放宽。十检总命令有旧范围外no-tmp，未冒全绿 | 当前测量是本机单点Python增量，不是4096极限/RSS/生产延迟保证；旧no-tmp文件与基线逐字相同，详§5，不新增豁免 |
| A1 | git baseline..product / status；README稳定入口、CLAUDE阶段状态；ignored inputs/证据 | 无main合入/部署/模型/配置生产写操作；当前分支产品commit与75源码匹配，三核心职责在本轮差异内保持；报告全部标条件与未部署；既有私人未跟踪目录未触 | verification-r1/hash-audit.json；git diff --stat/代码差异；R10/U3、README/CLAUDE本轮修改 | 符合：本轮权限边界与数据归属保持；审查只写verification.md与ignored verification-r1 | 不证明工具之外没有任何其他人的独立活动；本审查没有commit/push，不将旧发布授权延伸本轮 |

## 4. 核心目标及验证方法审查

### 正式纵向路径与机制判断

可信Web/Gateway入口和原生HB/Reminder标记→Main真实dispatch/canonical usage→原生Main结束→按owner读取有界事件、显式冻结历史和当前context/合同→可知历史特征与成熟转移采样→32条需求路径及不超过12个维护场景→同源执行/费用/风险比较→checked整数T与m/δ同一事务采纳→既有Idle/Heartbeat受理→原生并发Compact/Noting→各自费用收据/实际结果→维护结算mode-only刷新→后续自然Main再次三量决策。该链中没有另造模型路由、调度器、正文库或UI。

指定机制没有被替换为孤立helper：Compact facade/aux relay在正式worker作用域带Collector；Noting实际Loop在原生dispatch及canonical入口记账；真实SessionDB中的新收据改变下一估计；native成功发布见证使同Conversation合法Session轮转能读取after，而branch/rewind/新runtime/后继压缩不能借旧owner结果。导入只追加目标拥有的训练快照，不给当前静默/锚点资格。

当前观察资格与完整本地预测小时区分：80秒内已存coverage尾只给当前资格，未存尾不扩训练/静默；有成熟bootstrap时不被重新等完整小时挡住，无bootstrap仍需真实local一小时。跨模型已知work end保留1800秒保护，工作token和费用仍按完整兼容合同。

### 主动反证与观察

| 反证问题 | 实际核查与结果 | 支持范围 |
|---|---|---|
| 特征是否只是phase标签？ | 当前17维静态调用与两个原固定时点纯数值消融：E02原30m回归34.375%，去年龄15.625%、去时段28.125%、仅Turn origin50%；E06原6.25%，去增长9.375%、仅Turn origin12.5%。 | 证明实际作用，不证明准确率普遍优越；旧24h/持续轴对照仅作候选分析，不冒当前精确数字。 |
| 零维护经验是否会退回任意固定先验驱动主动决策？ | **会，G17已独立复现。** 正式policy._maintenance不区分经验与compatibility prior；无样本时90K/600s/.18得到T32768/δ0。R3负向测试0.8秒runner失败，原断言与实际证据保留。 | 合法缺数据反例，阻断；不能以旧合成正例解释成真实经验验收。 |
| 后知维护/结束/coverage是否泄漏到过去？ | visible/clean/import三门控；origin裸excluded不读未来；当前全部JSON未见visible max超decision时刻；迟到信息测试验证end1000、known1500不改变500/1200特征。 | 原coverage逐版缺失仍只是声明重建条件；raw coverage压力E08无维护已展示。 |
| 风险是否另用保守公式永远否决？ | _evaluate_maintenance使用与cost同一次evaluate返回的started/collision/wait；无trajectory则不伪造第二分布；E06/E08已实际模拟执行。 | 组件与需求的组合仍是条件估计，不承诺经验相关联合分布充分。 |
| 动作分歧后是否继续贴历史大context？ | 读完整Replay；独立原JSON核失败正费用且context_after=context；连续E01旅程自己67817→两次维护→123878.5，回归阶段94778→102767.5不重新贴311K。 | 外部工作足迹/缓存命中曲线是代理，已披露。 |
| 三量阈值是否用旧线性割线冒可行？ | _checked_threshold按当前分段缩减/费用/风险/原生干预重新检查数值点；至多4完整probe，两中点，不承诺全局单调或最小。 | 只认证所选T点；实际受理仍核当前C>=T与版本。 |
| 长闲全程不维护或低context无益重复是否被掩盖？ | 基础E06/E08各1次有益维护；连续第二次边际对照至同终点少194337，原短窗亏损保留；无后读是声明机制分支。 | 不要求每个平台或每个压力样本事后盈利；没有基于次数本身判合理。 |
| 维护后是否漏掉正式学习/模式刷新？ | v10旧缺口保留；v11每次end均mode-only、T/δ忽略、pending空/anchor不变；26次刷新与25后继state可见+1终点例外。 | 不伪造新Main结束或重新消费Idle。 |
| 测试能否只靠替换整个被测逻辑通过？ | 主要估计/执行测试调用正式policy/rollout/Replay；Noting跑真实Loop；后补轮转跑真实compress_context/lease/publish，控制summary transport/无关异步Noting；owner干扰六场景不是源码字符串断言。 | 初版Compact测试控制整个执行边界，仅证明观测注册；真实轮转测试补足该弱点，均未称真实付费模型效果。 |

### 经验判断与负结果的独立复核

9例预期SHA与结果源版本相符。E01/E02/E04没有维护；E06约21h和E08约46h满足基础经验机会；E07保护、真实回归和自有context三项符合。E03短截止亏454485、E05亏23831、E07短截止亏849495且共同终点仍亏121905、E09亏6776完整保留。E03同初态延续既有共同终点才有+2277455；不能说5h已回本。E09没有被追加“每个平台必盈利”或自造0.52%容差，其首冷读前机会/1800保护与完整费用均可核。

当前模型E06亏46227，当前模型整账单E06不维护且比最佳固定多105735，机械失败E06亏1106461；这些是预先允许的高成本/失败敏感性，不是主要基础情景被换掉。E08同类压力仍有条件正差。raw coverage与unknown Reminder E08无维护是“无法证明当前资格/排期”边界，不拿逐点拒因替代基础长闲验收。真实9段没有可用Stop执行点，取消账单/排队释放通过机制补充，未伪装真实案例。

主会话逐段判断依据与冻结预期一致；本审查不把其自评当要求来源，独立读了原JSON/actions和状态机后才接收。本轮目标是条件历史上的行为与算法接线，冻结未要求每个预测/故障抽样都事后盈利或真实部署节费。

### 证据版本、执行方法及资源

独立重算：9/9原件SHA、75/75当前及冻结源码SHA一致，经验SHA=`449d078fdba53e7765306aa7649a5183daaccbe878fd4553ce0e9a0a33cd448a`。13项v11矩阵、最多3并行、墙钟408.459秒是D已运行证据，本审查未重跑。observer只在super返回后追加审计信息，前置CLI相同case精确对照其原决定、动作、费用；原生replay_runtime与policy分别记SHA。unknown Reminder v7的复用基于拒绝分支依赖未变和current_history_unknown=False的显式证明，不把所有旧结果冒v11。

测试日志均显式官方PM `.venv`/`HERMES_PYTHON`及`scripts/run_tests.sh`，模型transport受控且DB/Profile隔离。既有旧policy测试中expensive plateau等仍以零维护经验+显式prior期望提前整理，这些预期来自旧算法而不符合V2 R3；测试通过不能关闭G17。可复用的其他主要证据为最新policy/e09-final-tests（覆盖当前57机制及相关policy/forecast/learning/bootstrap）、replay-mode-refresh-tests（32场景）、wiring/rotation-final-tests、wiring/hx011-rotation-tests及原wiring导入/Loop分支。未将这些数字相加声称另一整套或通用全覆盖。旧特征消融SHA不匹配的精确数字不复用为当前；本审查追加当前两时点预测反证，源码未改。

当前资源取证是明确249历史+43组件的单次decide，无trace0.185113秒，trace2.121386秒、Python增量峰1,025,839字节；不当RSS、生产机延迟、极限4096事件或统计上界。更大774+43的旧阶段单次0.750秒/977496字节保原版本，仅作规模资料。14天、2048事件、SQLite高水位/WAL等限制未混淆。

## 5. 发现、整改优先级与范围外项

本次初审发现1项范围内违规G17（P1）并独立复现，阻断Validation；其余为必须随交付保留的边界及已核实范围外项，不据此放宽规则或宣布生产效果。

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| G17 / V-01 | S2；V2 R3；adaptive_policy.py:55 / adaptive_cost.py:52–109 | 无maintenance_sample也无完整legacy时，maintenance_profile从配置取固定cost/duration/retained，formal decide仍可产提前计划；独立用原声明fixture复现零maintenance事件→business/T32768/δ0。 | P1范围内阻断。缺数据合法入口用任意固定维护假设代历史；旧正例测试恰在期待此行为，无法暴露问题。 | 正式V2不允许无可用经验scenario的compatibility prior驱动提前整理或原生干预计价；诊断明确缺口，原生安全/Force不变，HB仍可独立估算。补缺样本/不完整/完整legacy/正常更新/原生容量与失败等定向证据，再新独立全范围复审。 | 开放；root提案方向通过独立评审，产品1ae2b0f尚未修复。 |
| V-B01 | R3/R5，empirical_maintenance | 同完整parent联合账单支持0；GPT Compact独立费用缺失，跨模型/粗估/组件组合与小规模绝对比例包络属条件假设。 | 冻结允许分层有来源估计并要求披露，现有来源/整账单/慢尾/失败压力充足，非本轮阻断；禁止承诺实测节费。 | final-delivery与用户汇报保留代理、生产未验证和待追认工程假设。自然真样本充足后再校准，不能本轮触发生产。 | 边界已披露，无新增整改。 |
| V-B02 | R6/R7，实际回放 | E03/E05/E07/E09短窗及当前模型/失败压力有负结果；raw coverage/unknown Reminder无维护。 | 已按固定预期逐段审查且基础E06/E08通过，不把未定的“每压力情景必盈利”加作新门槛；不是全部盈利PASS。 | 保留原JSON和负数，Validation按原预期独立判断，终态压力不得说已兑现收益。 | 边界已披露，无新增整改。 |
| V-O01 | R9冻结no-tmp | root-quality-check整命令失败之一指旧`.autonomous/20261031-evidence-recovery/validation.md:20`，与基线/HEAD字节相同（独立脚本复核）。 | 范围外既有失败；本轮未动其行或规则，不冒十项整体全绿。不是新增豁免，也不修历史报告求绿。 | 主会话保留范围说明并按既有权限另处理；本Verification仅核本轮增量无新增该项。 | 范围外已登记；不阻断本轮产品Verification。 |
| V-E01 | R1旧feature-ablation源码版本 | 旧消融/候选增轴报告非当前SHA。 | 若直接把旧数字当当前会证据失配。静态依赖核查后追加当前固定两时点纯预测反证，未改判据/产品，缺口已补足。 | `verification-r1/current-feature-counterevidence.json`保当前SHA和所有变体结果；旧报告只作原时点设计分析。 | 本次审查取证已关闭，无实现整改。 |

## 6. 修复与独立复审

本次为该轮首次独立Verification，未被主会话退回补审，未接收或共同拟定实现方案；独立判据自13:24:50 UTC起始版保持不变，无迁就实现的降低。§2原始版本在ignored副本可核。

### G17关键研讨链与评审

- **原判据：** 起始S2，冻结V2 R3：“样本稀疏应使用分层或可追溯的历史组件估计并披露范围，不用3M／3600秒等任意常量代替应有的历史建模”；没有为了反例新增要求。V2替代旧固定prior口径，纯compatibility helper可保留旧行为，但不得成为新正式主动决策的逃逸。
- **初步发现与来源：** 本报告尚未最终交回时，root提供零维护样本反证和G17提案。审查者先按已有S2/R3重新读正式调用链，再按官方runner独立运行负向测试；1项失败，实际T32768而应无提前T，0费用/时长/缩减样本及explicit_prior来源已核。此前未交回的全符合草稿保存在`verification-r1/report-pre-g17-draft.md`，最终判定已更正，不能把草稿当门禁结论。
- **主会话提案及理由：** 正式policy._maintenance只选择经验profile，无完整scenario则None；复用现有缺维护拒因、HB无提前候选和native_cost_unknown fallback；原生Force/容量保护不变。旧maintenance_profile compatibility helper可保留prior，但不进入新decide提前/原生干预计价。依赖旧prior的合成测试要改为来源明确的经验结构或明确隔离的compatibility helper测试。
- **Verification独立评审：** 方向符合S2/R3及W2/E7，不需要变更规格。不能将“无维护经验”扩大为禁用全部HB估算；不能把缺profile解释为原生保护关闭或免费干预。完整有来源legacy联合样本若能构成经验scenario仍应可用，不能一刀切废弃历史。None路径必须能正常选择HB并解释缺口，若候选共同需求会触原生容量但费用未知则保原生，不凭空比较收益。
- **必要关闭证据：**（1）本独立零maintenance反例修后无提前T/δ且明确missing empirical；任意改固定prior不能重新授权。（2）稀疏不完整组件不得落回prior；完整legacy/当前组件仍正式参与费用、风险及阈值。（3）无经验仍有合法HB估算/选择，原生capacity unknown和Force保持原生。（4）正常采集/显式导入后经验估计恢复更新，失败/取消/owner/关闭不退化。（5）按实际变更依赖定向测，并明确v11有经验路径是否受影响；不得改旧真实案例/费用/seed求绿。修后由全新审查者重新提取全轮覆盖并复审，不只复跑G17。
- **状态：** 产品仍`1ae2b0f`，尚无实现/关闭证据。提案方向评审通过不等于整改关闭；门禁不通过，Validation不得启动。无产品目标/权限/完成条件变更，不需用户补写函数级设计。

V-E01另为审查证据适用版本问题：原判据D2/S1要求当前作用与可知性→核出旧日志版本较早→独立按原固定时点补当前纯数值证据→当前来源/现轴实际作用已确认；未变规格或产品，没有把旧数值改写成新数值。
范围内既有修复G8后知特征、G10跨模型work end、G12低规模缩减、G13整数T、G15当前资格/local一小时拆分、G16结算mode-only均从当前正式路径和对应反例/新证据核实，未仅依据plan的“已关闭”。历史v1/v4/v7/v9/v10失败与不完整证据保留，不重新包装通过。无需因当前数值不变倒推旧G16曾覆盖。

供主会话最终摘要的实质边界：采用历史支持30m转移组成最多24h共同责任窗口、跨规模缩减绝对/比例包络及有标签组件费用代理，均为Agent工程设计且不等于用户逐项指定；当前自然数据不足以证明真实节费。主会话已登记待追认，必须随交付显眼说明。独立Validation尚未完成；本门禁因G17不通过，必须先整改和新全范围独立复审，不能推进下一门禁。最终交付状态由主会话根据两门禁及当前证据判断。

初审最终交回前更新：2026-11-06T13:33:19.292914+00:00；待审产品仍以`1ae2b0f268eace9516de5f2633a089752e9f4e3c`为准，之后若产品变化须按影响独立复审；仅动态文档变化不冒产品变化。

G17记录时间：2026-11-06T13:35:06.287851+00:00。本报告最终计数以§1及§3为准：31符合/1违规。
