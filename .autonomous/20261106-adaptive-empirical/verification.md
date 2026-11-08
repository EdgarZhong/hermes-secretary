# Verification：20261106-adaptive-empirical

## 1. 审查对象与结论概览

审查者：全新独立 `verification_empirical_r4`；冻结依据 `24fe50ffcf588e9846b1902b0ad0f6cf62520924`；待审及实际审查产品 `3e08ea39ccf1a1ea2814f2a3e7fb710f049c52e4`，分支 `codex/adaptive-empirical-20261106`。依据 [snapshot-index.md](snapshot-index.md)、[baseline.txt](baseline.txt)，完整覆盖V2 U1–U3/R1–R10、历史来源/模型合同/初始化/导入/隔离/控制、E1–E7及07顶部10/28并发、11/1取消、§8.15。不扩大为UI改版、旧已替代算法或上线验收。

**Verification门禁通过：独立26条全部符合，0违规、0证据不足、0不适用；没有新范围内缺陷。G17、G18、G19在当前产品的关闭证据成立。** 此结论只关闭本轮Verification；原Validation在f7版本11通过/V10失败的报告仍原样保留，尚须主会话安排当前全部适用场景的独立复验，不能据本报告宣告整轮完成或上线。

严格独立顺序：先完整读两Skill，仅读冻结索引/指定规格建立26条判据并保存 [criteria-initial.md](../../.hermes-dev/adaptive-empirical-20261106/verification-r4/criteria-initial.md)，随后才看代码、动态CLAUDE/计划、测试和历史结论。判据没有修改或放宽。替换前逐字保全r3全文：[verification-r3-original.md](../../.hermes-dev/adaptive-empirical-20261106/verification-r4/verification-r3-original.md)，SHA256 `843dd4fbb4412cb76fcd060aaf7b8616f1e9ef7c6732f02702a2cd865098a4f3`；其内全部旧失败、撤回PASS、研讨与历史链接均保持。以下证据路径以ignored `.hermes-dev/adaptive-empirical-20261106/`为根。

产品/测试/配置/规格/原始证据始终只读；本审查只写本报告与ignored verification-r4。无生产访问、网络、模型、UI、提交、push或Huawei资料操作。进入时他人CLAUDE/plan修改及Huawei未跟踪目录保留。

## 2. 独立要求清单与覆盖

下表原样沿用先落盘的独立判据；建立时点见criteria-initial.md。原文直接要求及必要推导分别列于不变量，薄弱机制仍按目标和时序核查，不以未指定函数名为豁免。后序Validation不被反向作为进入Verification前必须已通过的循环条件；C01核证据链及如实未完成状态，不冒称双门禁已关闭。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| C01 | V2 U1–U3/R6–R7 | 目标/完成 | 真实历史特征→经验采样→联合三量决策，预先经验验收不可由工程通过替代 | 有冻结真实历史、结果前案例、逐段策略与独立判断；不称已部署节费 | 第3节C01 |
| C02 | V2 R1/R2 | 特征/薄弱机制 | 多尺度真人活动、增长、趋势持续、活动及任务结束年龄、条件空闲、时段、回归批次、背景责任、容量收益均须分析 | 可用性、作用及排除对照逐项可查，不仅phase标签；不推断语义任务结束 | 第3节C02 |
| C03 | V2 R1/R6；旧来源合同361–383 | 来源/context | 真人/HB/Reminder/unknown分开；墙钟与同epoch增长 | 入口来源有证明；累计input不当增长，HB不重置真人年龄 | 第3节C03 |
| C04 | V2 R3/R6；历史影子301–310 | as-of/删失 | 事件、来源证据、完整训练标签须决策时可知；缺口、维护、未知删失 | 按时间推进、成熟条件成立，未来只评分，无完整覆盖不补无人 | 第3节C04 |
| C05 | V2 R3；117–232继承 | 历史/当前资格 | 跨模型行为可继承，费用速度按兼容性分层；历史不授予实时空闲资格 | 目标实时状态与来源训练隔离，未知不填零，旧模型不全作废 | 第3节C05 |
| C06 | V2 R3/R4 | 经验采样/薄弱机制 | 有界可复现相似情景路径；回归、工作、维护耗时费用结果来源明确 | 无任意固定巨额先验永久代替历史，无删除昂贵/慢/失败样本 | 第3节C06 |
| C07 | V2 R4；07顶部10/28 | 费用/并发 | 普通Compact与Noting并发，不等待Noting；全维护费用与Main阻挡分别建模 | 成本包含两组件和失败取消恢复；阻挡以真实释放，不拿任务总耗时替代 | 第3节C07 |
| C08 | V2 R4/R5 | 同源风险 | 费用与回归风险从同源经验路径及维护样本产生 | 无独立保守公式永拒，显式风险/体验上限保持 | 第3节C08 |
| C09 | V2 R5；统一成本549–554 | 比较/末态 | 共同初态、外部需求与终点，各自产生HB/context/cache；已付费不可追回 | 失败/取消费用保留，窗口尾责任可查；动作分歧后不沿用旧context | 第3节C09 |
| C10 | V2 R5/R7 | 阈值/解释 | 联合选择m/T/δ，平台长期可行收益能执行，无到期必压缩 | T实际可达且同模型经济比较，拒因/敏感性和整段错失机会可解释 | 第3节C10 |
| C11 | V2 R6/R7 | 真实回放 | 冻结SHA来源缺口，预期先于候选，按整段评价 | 上升/平台/短离开/后台长空闲/回归/无读取/失败取消缺数据覆盖；缺历史以机制补充明示 | 第3节C11 |
| C12 | V2 R6/R7 | 经验结果 | 密集短离开保护；高存量有利空档真模拟整理；低存量无读取不整理；HB不无限延期 | 主会话逐段判断与预期相符；反例不得由合成正例或每条拒因解释免责 | 第3节C12 |
| C13 | V2 R8/R9；继承数据采集 | 正式路径/更新 | 现有owner事件采集与导入、Main结束正式获取并更新学习 | 非仅离线脚本；运行新观测影响决策，异常不阻塞主工作 | 第3节C13 |
| C14 | 117–232；V2 R8 | 初始化/导入 | 显式preview/apply、幂等冻结快照、来源身份/时间保留、容量拒绝原子 | 同Profile明确目标；不搬实时状态/锚点/计划/正文；重叠去重，不造coverage | 第3节C14 |
| C15 | 117–232；V2 R8 | 配置/模型 | provider+原生模型项1:1，同项改窗口新合同使计划失效 | 按所属Profile config/native resolver；缺项不串参数、推理速度标签兼容、无凭据持久化 | 第3节C15 |
| C16 | V2 R8/E1 | 原子采纳 | 每次真实Main结束同一快照同版本采纳三量，δ从该结束算 | 用户/HB/Reminder均正式接线，未采纳不执行；到期只复核 | 第3节C16 |
| C17 | E1/E4 | 维护结算/Idle | 成功失败取消刷新策略，已消费周期不复活；新Main才能新Idle | 一次请求/失效及维护结束无无限重挂，不伪造Main结束 | 第3节C17 |
| C18 | E2/E3/E6；07§8.15 | HB生命周期 | 保锚点与计数；切模式重算due，claim交接结算后更新；忙due合并一次 | 不set重建、不普通Turn重锚、不抢占已启动，不因维护伪自查 | 第3节C18 |
| C19 | E4/E7 | 计划/fence | 单owner单未受理计划，绑Main/epoch/config/Idle cycle；新操作及Main撤销 | 旧timer不能执行新计划，重启保绝对due或不可证即丢，失败不阻断 | 第3节C19 |
| C20 | E5/E6 | 优先级 | 用户/必要Reminder及原生安全优先；双到期合法Idle先于HB | 正式受理点串行，无timer竞速；维护后排队工作先行，due不丢 | 第3节C20 |
| C21 | E3/E7；117–232；V2 R8 | 控制/native | pause/clear/Stop/global/conversation/noneligible均保持原生与人工控制 | mode-only可用而Idle关闭不复活；∞不关闭Force/auto，不改缓存前缀 | 第3节C21 |
| C22 | V2 R8；07顶部10/28和11/1 | 取消/Force | 普通Compact取消联动对应未提交Note，已提交保留；Force不可取消及封区间规则保留 | 真实取消受理与成本/释放记录；取消不悬空、不永久占区间；Force/native安全无变化 | 第3节C22 |
| C23 | V2 R8/R10；07§8.15 | 隔离/API/架构 | 仅Secretary表、增量接口、Profile/Conversation隔离，沿原生路由与执行 | 无独立调度器/模型路由/UI改版；跨owner读写与当前活动不泄露 | 第3节C23 |
| C24 | V2 R9；226–232 | 资源/边界 | 事件/训练/采样有界，真实规模单次决策耗时内存与总回测区分 | 官方PM环境，真实容量证据，不用长回测时间作单次延迟 | 第3节C24 |
| C25 | V2 R9/E7 | 测试/失败恢复 | 正式链路、更新、关闭、失败、取消、模型切换、重启、失效覆盖 | 测试从规格来且实际机制未被mock绕过；缺必要证据阻断 | 第3节C25 |
| C26 | V2 R9/R10 | 权限/质量/交付 | 冻结门槛不增删放宽，本地分支不main不部署生产，原始个人数据ignored | 产品只读审查；版本/范围证据可复用，范围外历史失败明示，不报十项全绿 | 第3节C26 |

## 3. 逐条实现证据

每行与第2节同编号冻结来源/判据对应，构成“原文→不变量→正式路径→适用条件/方法→实际观察→判定”；以下“符合”仅对应本行已注明范围。源码均实际读取当前3e08树，既有证据迁移理由见第4节；证据路径均指ignored本轮根。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| C01 | scripts/adaptive_empirical_replay.py→Replay._decision:138→policy.decide:525→runtime.finish_turn:185 | 冻结9原件/9真实+3机制案例；逐时正式策略、root逐段判断，旧失败及门禁未完成如实保留 | data-analysis.md；experience-cases.json；root-experience-review.md；verification-r4/independent-evidence.json | 符合：真实历史→特征→经验路径→三量→动作及判断完整 | 条件回放；不等于生产节费/语义质量或Validation已过 |
| C02 | empirical_features.state；forecast.signature/_transition_weights→predict:268；policy.decide | 逐轴读17维：15m/1h/4h活动、操作年龄、机械工作结束quiet、活动趋势、时段sin/cos/周末、工作增长/未知、三尺度端点真人增长、背景增长、增长趋势、缺口轴；核年龄/增长/时段/quiet origin消融和24h/阶段持续候选对照 | policy/candidate-feature-comparison.md及plan/json；verification-r1/current-feature-counterevidence.json；r4独立SHA与消融数值核验 | 符合：重要特征真实影响邻居/回归路径，容量收益另在策略；排除轴有可用性/冗余/敏感性依据 | 4相关时点不是独立样本外选模，17维不保证最优；端点仅关联而非token因果 |
| C03 | runtime.mark_input/user_arrived/request_observed/finish_turn；features.clean_events/build_features；growth_by_source | 可信入口区分user/HB/Reminder/unknown；同epoch端点增量/真实秒；取消是活动不自动模型调用；raw包17操作含1取消 | data-analysis.md；inputs/events-20261106.json；test_adaptive_runtime.py及empirical_policy.py:169 | 符合：未用role或累计input推真人/增长，HB不归零真人年龄 | 不推断用户只看页面或未送达输入 |
| C04 | clean_events→forecast.visible/outcome:60/training_examples:94；learning._source/extend_bootstrap | 核at/available/imported门控、成熟30m、源独立和维护/gap删失；本次逐九段保存决策核visible及latest_label≤now；真实cancel两个可能label均被排除 | verification-r4/audit_evidence.py、independent-evidence.json；policy/knowability-tests.log；validation/independent-audit.json | 符合：未来仅评分；未知不补无人，后见排除不倒灌origin特征 | 旧coverage和来源知时重建为显式条件，不冒完整原始在线监测 |
| C05 | features.compatible_forecast_events/build_features；learning._source/extend_features/extend_bootstrap；policy._candidates | 行为跨合同保留，mixed Turn不拆半轮；local work_end跨合同保1800保护；历史不改local spans/last_user/cache/HB；当前资格80秒与完整本地训练小时分开 | empirical_policy.py:201/225/241/334及gap测试；test_adaptive_learning.py；current_activity_evidence实现 | 符合：行为继承与工作费用兼容、实时执行资格保持分层 | 缺当前工作用明确single-read条件代理，未知不当实测0 |
| C06 | policy._maintenance:55→empirical_maintenance.scenarios:120；forecast.predict:268 | 最多128成熟窗/32确定性路径/每路径256事件/12维护代表；原43组件及失败长尾、显式Stop receipt/unknown分开；无经验返回None而非3M/3600先验 | maintenance-components*.json；policy/g17-targeted-tests.log146；g17实现/反证原件；当前代码 | 符合：实际采样有来源；完整legacy可用，零或不完整经验不授提前维护 | 完整同parent联合账单0，边际组件组合/速度迁移明确条件估计 |
| C07 | compression_facade scope→auxiliary_hooks→samples.Collector→runtime._maintenance:297；noting_child→child receipt；rollout:46 | 读原生并发接线与独立收据；Noting全费用与Compact阻挡分别计；本次原G19反例及30边界：Stop实际释放结算wait，费用/context/碰撞原值不变 | test_adaptive_empirical_wiring.py:76/100/122/338；wiring/rotation-final-tests.log；verification-r4/independent-tests.log与counterexample.json | 符合：联合并发与总费用/实际Main阻挡一致，G19关闭 | 历史block为native注册/组件代理、联合额外交接未知，不等同真实租约上界 |
| C08 | rollout.evaluate:156→policy._evaluate_maintenance:287→原15%/30秒门槛 | 费用/risk共用path×maintenance权重；无独立Poisson veto；原10% user2/Stop3路径从99.8改.1，collision=.1、cost199855、baseline1009750均保；正式候选accepted | verification-r4/cancel-wait-counterexample.json；独立audit；policy/g19-targeted-tests.log101 | 符合：同源风险与实际取消结果一致；没有降体验上限迁就策略 | 不是实证校准概率；合成反例用于机制，不冒真实取消样本 |
| C09 | rollout.simulate_path；Replay._charge/_start_maintenance/_cancel_running:371/run:425；FixedMode | 共同需求/初态/终点、自有HB/context/cache；已付沉没费用不回收；费用含取消历史receipt与失败；末态冷读压力和共同延续单独呈现 | validation/base/journey/failure/cancel.json；g18-cancel.json；continuation-e03/e07-v11；r4独立G18归一化全results等值 | 符合：分歧后重算，未靠窗口外漏账或免费失败虚造改善 | 外部需求不受策略影响为声明假设；新策略因果收益未识别 |
| C10 | policy._candidates:451/_robust_improvement/_checked_threshold:392→runtime→Idle | T只返回当前floor以下实际可行整数点；probe重建规模相关profile并复用需求路径，至多4次；平台E06/E08实际模拟执行且连续旅程第二次有边际收益 | empirical_policy.py阈值整数/非单调/末态测试；policy/threshold-implementation.json；r4九段T审计；repeat-maintenance-v11.json | 符合：T/δ真实可执行且经济/风险理由可查，无人为到期强压或只解释拒因 | 证书仅检查点，不声称全域单调/最小T或所有压力盈利 |
| C11 | replay_data.prepare/past_events/coverage_at→Replay._known_history/_snapshot→正式decide | 9原件字节/SHA与源存在时逐一相符；experience SHA449d…448a；9真实段先于候选；知时/自有状态、rawcoverage/未知排期/费用压力均读证据 | verification-r4/independent-evidence.json；input-manifest.json；data-analysis.md；source-scope-v11.json；Validation命令原件 | 符合：覆盖真实增长/平台/短返/后台/回归；无真实无后读/完整Stop以声明机制补充 | 回溯coverage/Reminder已知条件披露，11/6截点后样本为holdout未倒灌 |
| C12 | 预登记experience-cases→公开CLI→base/journey及root逐段判断 | 独立核E01/E02/E04维护0；E06/E08各1且相对最佳固定分别少597664.01/2628378.29；连续旅程2次后回归低context不再维护；短截止亏损保持 | verification-r4/independent-evidence.json九段表；root-experience-review.md；journey-e01/continuation/repeat-v11；validation/base.json | 符合：核心真实机会与连续性符合原预期；后台未无限推迟，非合成廉价正例免责 | E03/E05/E07/E09原截止亏454485/23831/849495/6776；E07共同终点仍亏121905，不冒普遍节费 |
| C13 | 原生auxiliary/usage_read/noting_child→samples→runtime.snapshot:142→store.history/imported_history→decide | 完整读collector关联/receipt/dispatch/关后原owner结算及native publication路径见证；真实DB/Loop测试，导入后native新receipt确改变正式估计 | empirical_wiring.py:306/338与失败/关闭测试；wiring/rotation-final-tests.log10；policy/g17-targeted-tests.log146 | 符合：正常路径能获取并更新学习，不是离线独有；观察失败fail-open | 受控transport不证明Provider收费完整；缺usage持续unknown |
| C14 | history_bootstrap CLI→bootstrap.read/apply；history_import CLI→import.apply:342/_freeze:317；empirical_import→import_samples:393 | 显式preview/apply、owner/source proof、幂等/冲突/容量原子、重启读取；来源冻结与imported_at；不写实时事件/HB/Idle；重叠target优先 | test_adaptive_bootstrap/import/learning.py；empirical_wiring.py:142/172/183/287；validation/import-summary.json | 符合：只迁训练证据、保时间/来源/缺口，2048事件/32收据拒绝有界 | component_pool不冒目标亲历；跨Profile拒绝；源资料不自动共享 |
| C15 | adaptive_config.for_db→adaptive_model_config.resolve_contract/parent_contract→runtime.model_key | 原生provider+模型选项身份保1:1，窗口/API/推理/速度合同；snapshot从目标parent/native resolver测量；config/contract变旧计划失效 | test_adaptive_model_config.py；当前config/model/runtime及integration切模/窗口测试；75依赖SHA审计 | 符合：900k/普通与Provider隔离，缺项不套其它模型参数，不另选路由 | 未新增网络验证原生目录；复用同SHA原生合同证据 |
| C16 | runtime.finish_turn:185→snapshot→validate_decision→store.commit_plan:149 | 真实三类Main结束同一snapshot；commit_plan在原事务核expected_period并采纳m/T/δ；deadline=e+δ；shadow/fallback不采 | test_adaptive_runtime/integration.py；store/runtime当前代码；replay-mode-refresh-tests.log32 | 符合：原子三量且到期不优化，未采纳不执行 | 不以离线已建议冒运行已执行 |
| C17 | runtime._maintenance:297→adopt_mode_conn→state_refresh；Replay._finish_maintenance:332 | 维护完成/失败/取消先结算再mode-only，无新Idle timer；新Main才plan，消费周期不复活；mode-only即算出T也不采 | test_adaptive_empirical_replay.py:392等；replay-mode-refresh-tests.log32；execution-audit-v11；当前runtime | 符合：结束刷新与一次Idle契约成立 | Replay审计不是生产恢复实测 |
| C18 | heartbeat_store._effective_anchor/interval/claim/refund→store.register_claim/adopt_mode/settle_claim | 持久原b和计数；模式改仅b+H，claim在pending后结算；busy一个due；退款同revision；Stop/pause/clear优先 | test_adaptive_runtime/model_config/integration.py；heartbeat_store当前源码；execution-audit-v11 | 符合：无set重建/普通Main重锚/抢占已开始；维护不冒自查 | 共用原生执行，未重跑并发宿主压力套件 |
| C19 | user_arrived/turn_started→invalidate_conn；idle_settings:250→_idle_plan_valid/restore_native_idle；timer | 绑定Main finish/epoch/path/model/config/Idle cycle；旧回调和重启检查，绝对due；不匹配丢旧计划/回原生；错误catch | integration.py rewind/关闭/容量/旧回调/late plan；runtime/store/timer当前路径 | 符合：单未受理计划/fence/至多一次和失败不阻用户成立 | 未操作真实生产重启 |
| C20 | heartbeat_store.claim→_adaptive_priority_held/_adaptive_idle_precedes；noting_idle_joint.request；既有队列 | 正式事务先用户/必要Reminder及容量，再有效Idle与HB判优先；结束后队列user/Reminder在HB前；不等另一个窗口 | integration/runtime证据；empirical_replay.py queued_user/reminder及Stop测试；execution-audit-v11 | 符合：优先级不依timer线程先到；due保留合并且已开始不抢 | 回放越native容量明确拒绝，未凭空模拟免费不压缩 |
| C21 | _owner/for_db/settings_for_db→finish_turn/idle_settings；heartbeat store/status；native Force/auto | 总/会话关闭、非eligible、缺配置走原生；idle_off仅mode可采，不复活HB；∞只提前Idle；native threshold/Force与cache prefix接缝未改 | test_adaptive_integration.py:82/202/220/260；policy/g17缺经验原生unknown两分支；当前diff | 符合：人工控制/native行为与Force容量保护不变 | 不新增UI或模型前缀重建；本轮未启真实Conversation |
| C22 | compression_facade既有joint/noting lifecycle→新增只读samples；noting_child既有finish | 普通并发Compact取消联动未提交Note、已提交保留；Force独立封区间不可取消；本轮仅旁路观察数值，正式Stop释放和后续使用机制已读 | 07冻结契约；原生四接缝当前diff；wiring/integration及rollout/replay测试；r4独立Stop边界 | 符合：未串行等待Noting、未改变提交/取消/Force所有权 | Compaction流式UI为既有其它范围，不冒本轮完成/实机UI验收 |
| C23 | 所有DB owner→Conversation ref；store六表；samples.same_runtime/path witness；heartbeat_route→原Main宿主 | 仅自有状态/数值API增量；跨DB/ref拒，轮转合法发布与branch/rewind/替换/读取失败分支核查；无新路由/执行器/调度器 | wiring.py:338六种干扰；rotation-final-tests.log10；validation隔离导入；75源码/基线diff | 符合：Profile/Conversation隔离、原生执行及增量接口成立 | 不把已声明组件池当同owner历史；凭据/正文未入Git |
| C24 | features.MAX_EVENTS/store.history；forecast128/32/256；scenarios12；官方PM环境 | G19资源所有24依赖SHA当前匹配；249事件+43组件单次wall.192119秒；单独trace2.073341秒、Python增量峰1025839bytes；上限读码明确 | g19-resource.json；verification-r4/independent-evidence.json；源码有界常量 | 符合：真实规模资源与长回测总时长分清，无额外服务/权重存储 | 本机macOS非RSS/正式机/4096极限或统计上界；矩阵408.459秒不充单次延迟 |
| C25 | 正式decide/DB/Loop/CLI/facade/commit publication与claim→测试 | 亲读测底座，更新/关闭/失败/取消/切模/重启/失效/轮转正式路径；本次31项通过，原反例观测核正式candidate；复用146/101/32/33/10按依赖分工而非相加独立覆盖 | verification-r4/independent-tests.log；audit-evidence.log；g17/g19/rotation/mode-refresh/g18日志与对应测试 | 符合：预期来自冻结要求，受控模型仅替外部边界；未用镜像/字符串断言替正式接线 | 本次没有重复整矩阵；旧取消只看cost未查wait的缺口由原反例及本次边界补齐 |
| C26 | 当前功能分支/HEAD/产品SHA；冻结diff；根三核心及质量入口 | 当前产品提交匹配；9原件/经验未改、个人数值ignored；无锁/Actions/检查规则改动；root-g19-check ruff/health29文件0阻断；历史no-tmp同blob35daf…eb724 | git状态与diff；verification-r4/independent-evidence.json；root-g19-check.log；root-quality-check.log及冻结blob | 符合：本地授权与规则冻结保持；产品只读，未合main/上线/生产模型 | 十检查不是整体全绿：原health修后通过；既有no-tmp范围外历史失败仍保留 |

## 4. 核心目标及验证方法审查

**全轮正式纵向路径成立。** 可信Web/Gateway/原生HB/Reminder→Main请求和结束→所属DB/Conversation bounded数值事件及显式import/bootstrap→来源/可知/成熟窗口和17维特征→128窗口/32条经验需求路径与最多12维护场景→同源成本、可执行性、collision及实际wait→m/T/δ原子采纳→原生Idle/HB受理→普通Compact/Noting并发→费用/失败/取消/释放收据→mode-only刷新。current activity资格、历史训练就绪、机械工作结束和模型工作量分开；不能用历史先验“证明当前无人”。阈值经实际相同路径/规模复验，非旧仿射根冒精确边界。无独立调度器、执行器、模型路由或UI改版。

**人的经验与薄弱机制核查。** 原经验先固定九真实段及三声明机制分支，SHA `449d078fdba53e7765306aa7649a5183daaccbe878fd4553ce0e9a0a33cd448a` 当前一致。独立审查支持E06/E08各一次有成本依据的真实模拟维护，E01/E02/E04密集/短返零维护，E07沿1800保护及连续旅程自有小context恢复；没有由“各拒因能解释”替代整段机会。连续E01以新epoch67817出发，两次维护后最终123878.5；第二次相同需求/终点边际少194336.60而非只按次数判好。E03同173613初态延续到共同终点才少2277454.61；E07大context独立起点共同终点仍亏121905.21。原截止负数和当前模型/整账单/失败压力负结果保留。冻结没有要求每个预测噪声窗口事后盈利，也不能把这些条件收益冒生产节费。

特征审查不是只看phase：17个输入轴与其来源/缺失实读；相同输入去年龄、去增长、去时段、去quiet origins能改变预测，当前SHA匹配已有独立消融。24h计数与阶段持续未入最终向量，但确有先定4点/同128成熟窗/32粒子的对照：24h支持0–24/128、阶段回看11–47/128；410/410 quiet origin阶段持续为年龄封顶量化变换。新增轴仍会改变active/rising邻居和ESS，局部得分有利/不利均保，足以说明暂不纳入的工程判断，不证明17维最优。

**版本迁移与取消训练支持集。** 本次独立脚本逐核9原件、75份v11副本及当前产品树。相对v11只policy（G17零经验）、Replay（G18两诊断名）、rollout（G19等待）变更。G17有经验分支仍直接用同一scenarios，原r2九起点完整dict等值与1919保存经验分支证据可复用；无经验分支由正式缺样本机制/CLI另覆盖。G18同输入完整results仅规范诊断名/实测时钟后逐字段相等，paid1143046.3337856613、成功sample参考778332.0856089034、取消后context275039及后继费用/状态均不变。

不能仅以实际Stop=0或九起点抽样迁移G19。本次读并独立复核21报告/43保存路径/2578决策的完整适用证明（重叠记录，不是独立样本数）：唯一真实cancel发生于1793761222.4933662，后15.56335秒有native维护；能够包含cancel而避开该排除的origin仅1793759422.4933662–1793759438.0567162，所有原verified turn_end和全局1800格点均无候选。实际两个可能origin的正式outcome均因native维护删失；知道该cancel的run全部从维护end可知后起，生成checkpoint不能倒写更早区间。严格较晚end在时间裁剪中随更早cancel保留，start被裁仍由end.duration重建；模型过滤不删维护行。各bootstrap/cohort无cancel token，生成未来activity只来自成熟label，而非历史seed或费用receipt。E09全部决策早于cancel可知。

声明Stop的两条CLI路径在Stop前不可知，结算end后才mode-only；含该Stop的label与其正时长维护区间相交。Stop/end同刻不能泛称排序必保留，730<2048的实际历史总量上界单独支持当前两run，主会话审计脚本的保守计数已读，非未来通用保证。no-maintenance输入确有cancel训练支持，但无profile且44次全maintenance_model=unavailable，不能进入changed started分支。本次独立脚本重新核全部报告/输入SHA、时点/来源条件、两origin原始outcome、无profile路径；接受上述版本迁移。旧实现者一次E08实际predict/evaluate完整等值仅作补充，未用单点取代全程支持集证明。新增cohort、跨越escape区间的新run、取消/end裁剪边界或其它Stop支持不在复用范围，应定向重跑。

**G19实际反证与测试有效性。** 本次原独立测试逐字复制（SHA `4a8690c3f471593b0d507f96d9accc22ccecf3c927d827032528982b14532bd1`），仅在r4生成成功JSON；旧失败JSON SHA `b5c6ebb1b4f832e70466e30ba7ed6a39b4f87b724d4c1beb5f4a4e73de6fe15d`未变。正式evaluate由99.8秒改.1秒；其余原observed字段逐项等值，candidate不再仅因expected_wait_limit拒绝，原30秒上限未变。独立增加10个手算事件链×高/低/无receipt共30项：Stop-only、单/多排队、Stop后长Main及后继排队、自然完成、无事件、恰完成/开始边界，全部通过。官方runner两文件31项/0失败、0.2秒；实现者101项同当前源码SHA有效，包含正式候选接受与付费/HB释放等边界。没有把旧测试通过率当审查：r3发现表明仅cost/context断言仍能漏掉wait，这次是直接从实际Main释放不变量补证。

审计分析脚本首次缺PYTHONPATH在import前失败，原日志 `verification-r4/audit-evidence-initial-harness-error.log` 保留；改为`PYTHONPATH="$PWD" .venv/bin/python .../audit_evidence.py`后完整审计通过，无产品修改。只复用有效同版本机制证据，不重跑无关大套或13矩阵。资源采用当前所有24依赖SHA匹配的g19-resource：249事件/43组件，单次wall0.192119秒；独立trace2.073341秒/增量峰1025839bytes。不是RSS/服务器/极限或统计保证；矩阵408.459秒属于整个矩阵。冻结检查未改，旧no-tmp不能包装十项全绿。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| G19 / 原V3-01 | C07/C08/C25；rollout.simulate_path:46/evaluate:156→policy:287 | 原user2排队/Stop3释放仍按自然end1000计wait，99.8误拒；当前first_blocked保存原到达、最终maintenance_end结算为.1 | 原P1/P2范围内缺陷真实存在；现实际等待与同源成本结果一致，无需降体验上限 | 本次原反例+30手算边界31通过、正式candidate accepted；101当前源码测试；21报告全程影响支持集证明 | **已关闭**；r3原失败/提案/修后证据都保留，非原轮次曾通过 |
| G18 / 原V2-02 | C09/C25；Replay._cancel_running:371 | paid1143046高于原所谓upper_bound778332，旧诊断错；当前称sampled_completion_cost_reference | 原解释缺陷成立；不截断付费、不改历史receipt或状态 | 同输入新CLI g18-cancel；33项；本次完整results规范名/时钟等值 | 已关闭；原Validation V10失败不改写 |
| G17 / 原V-01 | C06/C13/C21；policy._maintenance:55 | 原零经验仍沿任意prior给主动T32768；当前只经验scenarios，缺失None | 原P1成立；缺成本不允许免费/固定prior维护，HB仍可独立/native安全保持 | 146项、r2独立反证/九起点及1919分支证据、当前代码与版本核查、无经验CLI44次 | 已关闭；原失败链保留 |
| B01（条件边界） | C02/C06/C07/C11/C12 | 完整同parent联合支持0；GPT Compact缺独立账单，prefix规模、绝对/比例缩减包络、跨模型速度/覆盖排期重建均为工程条件 | 冻结允许稀疏可追溯组件估计及敏感性，当前披露/对照完整，非新阻断；不得冒实测保证 | 最终交付显眼说明Agent自主收敛待追认、负结果、未部署/内容质量未测；自然样本后续校准 | 保留披露；不能被PASS抹掉 |
| B02（后序门禁） | C01；validation.md | 原f7 Validation 12场景中11过/V10因G18失败；r4只Verification | Verification通过不等于用户目标已完成；原报告仍失败须当前独立复验 | 主会话接续全部适用场景/原取消链及G19适用性复验后做交付判定 | 后序工作，非本Verification新缺陷或自授通过 |
| O01（范围外） | C26；冻结no-tmp历史报告 | .autonomous/20261031-evidence-recovery/validation.md:20既有告警，冻结及HEAD blob都35daf5563d97496728892feb281ba89f5a7eb724 | 非本轮新增；不得改历史报告求绿/改门槛；root原health真实问题已修后0阻断 | 保持历史报告；主会话按独立授权处理，不声称十项全绿 | 范围外保留，无新增豁免 |

本次没有新增范围内违规或证据不足；辅助审计启动错误不是产品缺陷，已保留初错及成功日志。

## 6. 修复与独立复审

本次是全新r4全轮复审，重新仅从冻结文本建立26条判据后才读旧发现。全范围机制/正式接线/来源及隔离/开关与失败恢复均重核，非单G19复测；未发生退回补审或判据更改。产品仍3e08，产品/测试/规格只读一致，写入仅本报告及verification-r4；完整旧r3原件及其内r2/r1历史链接保存，未把旧失败改成当时通过。

**关键研讨链完整保留：** G17原判据要求可追溯经验维护，零样本反例→root提案统一只用scenarios、legacy完整保留、缺样本不禁HB及native容量安全→原独立审查明确必要证据→f7实现/146项/独立九起点与保存分支审计→r2关闭，r3/r4核当前仍成立。G18原R4/R5要求解释诚实，Validation真实CLI费用高于所谓上界→root提案只改诊断参考名/未知代理标签，费用状态不动→r2撤回PASS并按原判据评审→c301和原输入CLI/高低无receipt机制→r3关闭，本次再核全部results/输入/代码等值，无冻结规格变化。

G19原r3按实际Main阻挡不变量独立发现→root提案常数空间保存最早实际受阻普通user原到达，最终按实际维护释放结算；Stop仍为回归碰撞，自身立即释放不虚构等待，后续Main busy不混入→r3依据原R4评审方向并要求自然完成/Stop-only/多队列/严格边界/付费及正式选择、完整预测支持集影响证据→3e08只改rollout该聚合，原费用/来源/队列/碰撞/阈值/案例/seed不变→本次31独立检查、原observed其余值等同、101同SHA机制和完整支持集证明关闭。此为既有授权内实际等待结算修正，**没有降低冻结判据或变更用户产品语义**。

供final-delivery及主会话最终汇报摘要：当前Verification通过且三项旧缺陷均有当前关闭证据；真实基础长平台机会已实际模拟，不承诺普遍节费。必须保留维护组件/缩减迁移/覆盖排期的条件假设及Agent自主收敛待追认、有限负结果、内容质量未测、本机资源局限，并完成后序独立Validation与主会话交付判定。禁止上线/合main/生产改动仍有效，本报告不扩大授权。
