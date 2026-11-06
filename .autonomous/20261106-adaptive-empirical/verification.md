# Verification：20261106-adaptive-empirical

## 1. 审查对象与结论概览

审查者：全新独立 `verification_empirical_r3`；日期2026-11-06。冻结依据 `24fe50ffcf588e9846b1902b0ad0f6cf62520924`，待审并实际核对产品 `c3017acaa4d9dfb8db127cdf67969879033ff21d`；索引 [snapshot-index.md](snapshot-index.md)、[baseline.txt](baseline.txt)。完整范围为V2 U1–U3/R1–R10、保留的历史/初始化/导入/隔离/模型合同与E1–E7、07顶部并发/取消及§8.15执行边界；不扩UI、旧被替代数学或未来愿景。

**门禁不通过：26条中25符合、1违规（R4，新G19）；0证据不足、0不适用。G17、G18已按当前证据关闭，原失败不抹除。** 新G19属于正式预测的取消后Main等待结算：可错误触发等待体验上限拒绝维护，不是G18字段名问题。当前Validation仍保留原V10失败，须整改后按套件独立复审/复验；本Verification不代替Validation或宣告用户目标完成。禁止上线、合main、生产模型及配置变更保持。

先完整读取autonomous-run和spec-implementation-review，只依据指定冻结原文提取26条判据并保存 [criteria-initial.md](../../.hermes-dev/adaptive-empirical-20261106/verification-r3/criteria-initial.md)，然后才读根三文档、当前实现、测试和原报告。起始判据未降低或改写。当前完整r2报告（含撤回PASS/G18研讨与失败）原样保存（SHA256 `d7ef4f3fa067fc01571897be3db04d86391a7ba25869952c94c027347e051199`）[verification-r2-final-with-g18-original.md](../../.hermes-dev/adaptive-empirical-20261106/verification-r3/verification-r2-final-with-g18-original.md)；r1及r2通过前原报告仍沿原链接可读。以下本地证据相对 `.hermes-dev/adaptive-empirical-20261106/`，均ignored；本审查仅改本报告和verification-r3，未改产品、预期、费用、seed或生产。

## 2. 独立要求清单与覆盖

下表原样取自先落盘的初始判据。方向明确而具体算法/接线未指定的R1–R8，按其机制和目标审查，不以实现命名或已有测试预期定要求。U2在此核查真实经验证据与诚实完成状态，双门禁未关闭不被当成已完成；不把后序Validation作为Verification进入前的循环条件。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| U1 | V2 U1 | 目标/全部 | 人的空闲维护思路须由真实特征与轻量模拟驱动三量 | 可追踪真实数据→特征→路径→m/T/δ，非只改标签 | 同编号证据 |
| U2 | V2 U2–U3 | 完成/全部 | 真实逐段经验判断独立于预测评分，未验不能交付 | 预先固定片段、动作回放、主会话判断及独立双门禁；失败继续整改 | 同编号证据 |
| R1 | V2 R1 | 数据/全部 | 来源分类、墙钟和有效epoch；规定特征须分析作用 | 真人/HB/Reminder/未知分开，分析多尺度活动/增长/趋势/持续/离开/条件空闲/时段/批次/后台/容量收益，消融可不用但须证据 | 同编号证据 |
| R2 | V2 R2 | 判断/全部 | 先工作与短停，再空档、再收益；后台与真人不同 | 不把HB当真人忙、不硬编码夜晚、不无证据宣称任务结束 | 同编号证据 |
| R3 | V2 R3 | 采样/全部 | 所有分布只用决策可知；稀疏估计可追溯且不挑成本 | 有界标准库可复现采样；回归/工作量/维护/阻挡/缩减/失败注明来源；跨模型分层不全废 | 同编号证据 |
| R4 | V2 R4；07顶部10/28、11/1 | 时间费用/联合 | 并发Compact不等Note；总费用和实际Main阻挡不同 | 含两者失败取消恢复，风险费用同源路径，不额外独立保守公式恒否；上限开关保留 | 同编号证据 |
| R5 | V2 R5 | 比较/全部 | 同外需/初态/终点，自生HB/context/cache；过去花费不回收 | 完整终点费用/恢复，长期平台不无限推迟，不人为强压缩，有理由和敏感性 | 同编号证据 |
| R6 | V2 R6 | 回放/真实历史 | 原件冻结，时间推进，未来只评分，先预期后候选 | SHA/来源/缺口，九类场景，分歧后重算context/cache；不可复原假设及敏感性 | 同编号证据 |
| R7 | V2 R7 | 经验/整段 | 密集/短停不抢，真实高存量有收益空档能执行，低量/无读不整理 | 逐段动作+错失机会验收；后台不无限延期，回归后收敛；不能全不维护靠合成免责 | 同编号证据 |
| R8 | V2 R8 | 接线/全部 | owner/事件/Main结束/原子三量/E契约不只是离线 | 正常路径可获取更新估计，自有状态，关闭非eligible零变化，安全/缓存/身份不变 | 同编号证据 |
| R9 | V2 R9 | 资源与质量 | 有界实测单次性能；正式路径失败生命周期均验 | 真实规模耗时内存，学习/关闭/失败/取消/模型切换/重启/失效；冻结检查不变 | 同编号证据 |
| R10 | V2 R10 | 权限/全部 | 只本地与自动push，禁止上线及个人数据入Git | 无main合入/部署/生产变更/模型，数据ignored，不改三核心职责 | 同编号证据 |
| H1 | proposal冻结117–232：数据归属/模型项 | 隔离/全部 | 原生provider+选项1:1；Profile/Conversation各自owner | 同名Provider/900k独立，窗口变化旧计划失效，缺参数不冒用；行为可跨模型、工作量严格兼容 | 同编号证据 |
| H2 | 同：配置/原生Idle | 启用/关闭 | 总开关与显式Conversation开关，不复活手控 | 原生解析路径和Conversation idle覆盖；无项走原生，非新定时器 | 同编号证据 |
| H3 | 同：bootstrap | 初始化/既有历史 | 显式同会话纯数值包，8成熟条件窗可就绪，非coverage | preview/apply、2048/32、幂等/拒绝原子；可知时间/unknown/来源不造；同owner只恢复已证原时刻 | 同编号证据 |
| H4 | 同：显式导入 | 迁移/新会话 | 同Profile显式冻结，普通Turn不偷搬，不继承运行态 | 幂等/冲突/替换/去重、源删除后仍可用、截止冻结、重叠不双算、不跨源造闲段、时间衰减及容量拒绝 | 同编号证据 |
| H5 | 同：导入证据/实时状态/缓存 | 标签与可知 | 工作量完整合同一致，未来证据最大可知，原文和Prompt不动 | 不切混模型半轮，不借迁移偷改当前context/cache/last_user/HB/plan；bounded索引不全库正文 | 同编号证据 |
| E1 | 冻结E1 | Main结束/计划 | 同快照原子三量，δ从真实结束算；到期不重优化 | 每种Main结束/结束后评估、每Idle一次、配置重启不伪造结束 | 同编号证据 |
| E2 | 冻结E2 | HB模式 | 锚点为真实交接b，切换只重算b+H | 不变不计时、过去due一次、暂停clear尊重、失败交接退款、忙碌合并 | 同编号证据 |
| E3 | 冻结E3 | 受理竞态 | 正式受理点优先，claim结算后更新，不抢已开始 | 新revision不破坏claim/refund；手控不复活 | 同编号证据 |
| E4 | 冻结E4 | Idle计划 | 一个未受理计划绑定epoch/config/结束/周期 | 入队/Main/模型/上下文/关闭/手动维护失效，读状态不延后，到期失败不重挂 | 同编号证据 |
| E5 | 冻结E5 | 同到期优先 | 用户/Reminder/原生保护优先，其次有效Idle再HB | 不依线程顺序，不额外等窗口，已受理不抢 | 同编号证据 |
| E6 | 冻结E6 | 维护后 | 维护不当HB，结束先结算再队列再新策略 | 成败取消保真，due用旧b，仍due仅一次 | 同编号证据 |
| E7 | 冻结E7 | 关闭/恢复/失败 | 两模式/正式C/∞仅提前Idle/δ合法；计划版本至多一次 | 错owner/busy不启，重启绝对时刻/不匹配丢弃，计算持久化失败不阻用户/原生保护 | 同编号证据 |
| J1 | 07顶部10/28及11/1 | 联合/Force | 普通并发触发与取消；完整Note留、未提交取消；Force独立不可取消 | 本轮不破坏现有接缝/容量保护/后续注入，不把Note总时当Main阻挡 | 同编号证据 |
| B1 | 07 §8.15 | HB执行/隔离 | 同Profile Conversation原生Main和宿主，不新执行器 | 共享领取/退款、active重启、paused/clear不复活、new/fork不继承、所有session同owner | 同编号证据 |

## 3. 逐条实现证据

每行由§2冻结来源/必要不变量→正式路径→适用条件→检查方法与观察→判定构成；具体版本复用理由在§4。源码路径均为当前c3017ac树。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| U1 | scripts/adaptive_empirical_replay.py:46 run→Replay→adaptive_policy.decide→build_features/predict/evaluate→三量 | 真实资料特征分析、成熟转移组成32条需求路径、维护组件进入联合成本；独立读主要入口、各分支及正式runtime取数，非离线phase标签 | data-analysis.md；policy/candidate-feature-comparison.*；current代码；verification-r3/independent-audit.json | 符合：历史特征与采样真实驱动m/T/δ，不只增加字段 | 不声称统计最优、因果节费或语义任务结束 |
| U2 | 固定experience-cases→prepare/run→root-experience-review；当前验证报告 | 经验SHA449d078f…cd448a固定；9真实+3机制补充、主会话逐段判断、旧失败保留；当前新缺陷仍明确不完成 | experience-cases.json；data-analysis.md；root-experience-review.md；validation.md；本报告 | 符合：完成所需证据链存在，门禁失败被如实保留，未以分数/合成正例交付 | 当前整轮未完成，不能以此行宣称双门禁通过 |
| R1 | adaptive_runtime.mark_input/user_arrived/request_observed；features.build_features；empirical_features.state/growth_by_source；forecast.signature | 来源可信入口分user/HB/Reminder/unknown，墙钟多尺度与同epoch端点增长；17轴参与相似采样；任务结束仅机械turn_end、阶段持续/24h轴有候选对照 | inputs/events-20261106.json；data-analysis.md；verification-r1/current-feature-counterevidence.json；当前三源SHA仍匹配 | 符合：规定特征有来源/分析/实际作用，不把累计prompt或HB作真人；未用phase名代替特征 | 端点为来源伴随关联，不是逐token归因；4个消融点不证明全17维最优 |
| R2 | policy._eligibility_reasons→_candidates→_evaluate_maintenance；runtime后台Main记录 | 先保护真人及跨合同机械工作结束1800秒，再检查冲突/可执行空档，最后收益；HB不重置last_user；时段为历史轴 | validation/base.json E01/E02/E04/E05；test_empirical_policy跨合同/迟到work-end；当前代码 | 符合：密集与短返0维护，长闲后台能维护，不硬编码夜间、不声称知道项目结束 | 1800为保留显式保护，非统计推定用户永不返回 |
| R3 | clean_events→forecast.visible/outcome/training_examples/predict；empirical_maintenance.scenarios；policy._maintenance | 发生/可知/导入门控、成熟30m、128窗/32确定性路径、12维护场景；含长尾/失败，零或不完整经验不退固定3M/3600；完整legacy保留 | policy/g17-targeted-tests.log146；policy/g17-test_missing_maintenance_evidence.py；maintenance-components.json；verification-r3/audit-runner.log | 符合：估计有来源、有界可复现、跨模型分层且未知披露，固定prior不再授权主动维护 | 同完整parent联合支持0；GPT Compact账单不足，组件组合/规模迁移为条件估计 |
| R4 | 普通联合入口→samples收据；rollout.evaluate→simulate_path:87–100→policy._evaluate_maintenance | 总费用含并发Note+Compact，Main阻挡按Compact；G18解释已修。新独立声明反例：10% user2/Stop3应wait1、90%后返0，期望.1，正式输出99.8，仅expected_wait_limit否决有收益候选 | verification-r3/cancel-wait-counterexample.json；cancel-wait-runner.log；源码rollout.py:89/98；g18-cancel.json | **违规（G19）**：已按Stop付费释放，却用原完成时刻计等待，与实际阻挡不一致；正常并发/费用分离部分仍符合 | 机制输入明确非真实历史取消；不改变碰撞定义、费用或体验阈值，不据此推断九段全失败 |
| R5 | policy._candidates/_robust_improvement/_checked_threshold；Replay._charge/_plan/run；FixedMode | 共同外部需求/初态/终点，各自HB/cache/context；原截止与共同延续独立；整数T正式复核≤floor(C)，最多4探针；E06/E08基础实际模拟维护且不无限推迟 | validation/base.json/journey.json；continuation-e03/e07-v11；repeat-maintenance-v11；独立audit 9段数值 | 符合：过去费用不回收、尾责任保留，不人为deadline，理由/压力均显示 | 不把末态一次冷读压力作已实现收益；取消等待单独R4违规 |
| R6 | empirical_replay_data.prepare/past_events/coverage_at；Replay._known_history/_snapshot/_charge | 9原件SHA/字节独立核对；原经验先定；每决策visible/label≤now；分歧后自有context/HB/cache，初态epoch修正；rawcoverage/unknownReminder/模型费用压力保留 | verification-r3/independent-audit.json；input-manifest；validation/prepared.json/base.json；source-scope-v11 | 符合：真实按时前推而非套旧曲线，假设/缺口/无真实分支明示；原件未改 | coverage/已知排期/结束即可知是声明重建条件；无完整真实无后读或Stop完例，不伪称实测 |
| R7 | 正式decide被真实CLI调用；9固定段与E01全旅程 | 复核当前f7实际CLI非取消结果并审迁移：E01/E02/E04零维护；E06/E08各一次、分别条件少597664/2628378；旅程两次后回归低context不再维护 | validation/base.json/journey.json；root-experience-review.md；verification-r3/independent-audit.json | 符合：核心真实机会实际模拟执行，密集/短返/回归保护，不靠合成廉价正例免责 | E03/E05/E07/E09原截止亏损454485/23831/849495/6776保留；非所有平台/压力盈利 |
| R8 | runtime.finish_turn→snapshot(store.history/imported_history/read_bootstrap)→decide→store.commit_plan；samples采集→同history | 正式Main结束读取/更新估计；native Compact/Noting Loop收据、取消/关闭后原owner结算、真正发布路径见证；未新增表/调度器/执行器/UI，API可选兼容 | test_adaptive_empirical_wiring.py；policy/g17-targeted-tests.log；wiring/rotation-final-tests.log；当前diff | 符合：数据驱动不是离线专有，现有owner/三量原子接缝正式使用，关闭及原生保护保持 | 正式数值预测取消等待错误按R4阻断；本行不豁免该错误 |
| R9 | features.MAX_EVENTS；forecast128/32/256；scenarios12；runtime失败catch；资源正式decide | 事件2048+导入2048、收据32、观察512；G17单次249事件+43组件0.18253秒，trace2.08956秒/增量1025839；学更新/关/错/取消/切模/重启/失效有正式机制证据 | g17-resource.json（依赖仅非调用Replay变）；g17 146；root-g18-tests.log33；root-g18-check.log；本次3审计过/1反证失败 | 符合：明确真实规模、耗时内存类型，质量门禁未放宽，失败反证如实留存 | macOS本机，非RSS/生产/4096极限；408.459秒为矩阵总时长；已知G19仍需修 |
| R10 | 功能分支c3017ac；冻结diff/ignored证据；根三文档 | 当前git/产品SHA核对；本审查无网络/SSH/UI/模型/提交；产品diff无生产参数/锁/Actions/检查规则，个人原件ignored；未动Huawei | 独立audit源码/原件SHA；git status；当前diff | 符合：本地授权边界保持，未合main/上线；hook规则未改 | 不对未观察的历史外部动作作保证；本门禁不授部署权限 |
| H1 | adaptive_config.for_db→model_config.resolve_contract/parent_contract→runtime.model_key | 精确Provider/原生模型项与当前窗口/API/推理合同；会话实际值而非Profile默认；配置版本/contract变更使计划失效，跨模型仅行为保留 | test_adaptive_model_config.py；test_adaptive_learning.py；当前配置adapter和runtime | 符合：900k/普通及同名Provider分离，缺项不借别项；完整Turn工作量需同合同 | 不复测原生在线目录网络，保留同SHA正式测试 |
| H2 | _owner→for_db/settings_for_db；idle_settings/_restore_native_idle；HB status | 全局/Conversation显式启用，Idle仅三字段覆盖；关闭/缺项返回原生，手动pause/clear不恢复，未建HB定义 | test_adaptive_integration.py关闭/已受理/旧回调；runtime.py与heartbeat_store | 符合：不启用即原生，开算法不创建/复活Heartbeat或额外timer | 本轮未启任何真实Conversation |
| H3 | scripts/adaptive_history_bootstrap.py→bootstrap.apply/read→snapshot→extend_bootstrap | 显式同会话、幂等/容量原子拒绝、源身份/available/mature/unknown；历史就绪不强等新8次，frontier保原时间，沿自然Turn采纳 | test_adaptive_bootstrap.py；g17-targeted-tests.log；源码bootstrap/learning | 符合：初始化只训练证据，不造coverage/Turn或计时；缺工作量明确single-read条件代理 | 旧条件序列非完整在线观测，不能据此执行资格越过当前local安静证明 |
| H4 | adaptive_history_import preview/apply→import._candidates/_freeze→store.imported_history | 显式同Profile冻结，幂等冲突/替换容量事务，保origin/知时，来源删除/新活动不改快照；跨源独立并target优先去重，配置读取不偷偷搬 | test_adaptive_import.py/learning.py；validation/import-summary.json及实际CLI收据；当前import代码 | 符合：只训练迁移，不带运行态/锚点/计划，不跨会话拼安静，2048/32拒绝非静默挤出 | 新组件池默认未证owner，显式conversation须每条匹配owner证明，非所有池为目标亲历 |
| H5 | compatible_forecast_events/_runtime_mark→learning._cohort；store.history/imported_history | mixed-contract请求整Turn排除，mark知时取所有依赖最大，迟到/缺口删失；索引bounded数值，自有六表；导入不注Prompt/cache/原文 | test_adaptive_learning.py；current源码features/forecast/store；validation隔离库核实时表未改 | 符合：跨模型时序不偷渡token/output/耗时；历史/模型前缀无新增正文路径 | timing-only中未知额外调用/增长/output/busy明确排除，不是实测零 |
| E1 | runtime.finish_turn→snapshot→validate_decision→store.commit_plan；维护结束仅adopt_mode | 真实用户/HB/Reminder每种Main结束同快照三量事务；due=e+δ；到期不decide；维护结算不重挂Idle | test_adaptive_runtime/integration.py；replay-mode-refresh-tests.log32；execution-audit-v11 | 符合：Main结束事实与三量版本保持，新Main才挂新Idle | Replay mode_only审计不是生产重新上线证明 |
| E2 | heartbeat_store._effective_anchor/_effective_interval/claim/refund；store.adopt_mode | 保原last_fired/created/fallback anchor，模式变只b+H，不变不改时钟；忙只一个due，原claim失败可退款 | test_adaptive_runtime.py；test_adaptive_model_config.py；heartbeat_store.py:87–144 | 符合：用户/Reminder/维护不重锚，开始后失败不抹交接；手控保留 | 沿已有native执行生命周期，无新增调度器 |
| E3 | store.register_claim/adopt_mode/settle_claim→heartbeat claim/revision/refund→turn_started | 自动变更写pending等claim结算，旧退款只同revision；接受后不抢占；手控更新revision不被复活 | test_adaptive_runtime.py claim/并发；test_integration已删配置后claim；当前store/heartbeat | 符合：正式受理点与已有fence结算，非timer线程先到规则 | 模拟不单独证明所有并发宿主，复用同SHA机制证据 |
| E4 | user_arrived/turn_started→invalidate_conn；idle_settings验证config/path/epoch/model/idle_config | 单pending plan绑定结束事件/周期/路径/epoch/config，用户入队或任何Main使旧计划失效；读/scan无重优化重挂，到期一次 | integration.py rewind/切模/容量/关闭/旧回调；store.commit/invalidate/consume；timer.attach | 符合：HB/Reminder作废旧Idle但不当真人，错/取消不自动反复重试 | 与维护后仅mode刷新不同阶段已明确 |
| E5 | heartbeat_store._adaptive_priority_held/_adaptive_idle_precedes→原受理；noting_idle_joint.request | due Reminder先行，合法且C≥T Idle优先HB，owner/path/epoch/config复核；普通用户按既有宿主队列先行，原生容量保留 | test_adaptive_integration/runtime.py；execution-audit-v11 1401HB；当前代码 | 符合：同一正式接缝判优先，不等另一个timer、不抢已开始 | Replay最大context412646未跨原生容量；overflow明确拒绝伪造便宜不压策略 |
| E6 | runtime._maintenance→settle→mode-only；HB原anchor；既有主队列 | 完成/失败/取消结算真实状态后只采HB模式，不挂Idle；同b计算due，队列用户/Reminder先于HB；两失败付费不缩 | replay-mode-refresh-tests.log；validation/failure.json/g18-cancel.json；replay _finish_maintenance/_cancel_running | 符合：维护不是一次HB，无已消费Idle复活、无新周期锚点 | 正式预测的等待统计另由G19阻断，不混作队列未释放 |
| E7 | validate_decision；_idle_plan_valid/_restore_native_idle；store.commit_plan；timer.attach_idle_timer | 两档m、整数正式T/None、δ合法；expected_period/epoch/config/owner至多一次；重启用持久绝对due，无匹配丢旧计划回原生；catch不阻用户 | integration/runtime tests；g17原生unknown两分支；当前代码store/timer | 符合：未采纳不执行、∞仅提前Idle、Force/auto安全保留，失败退原生 | 缺维护费用不允许免费或固定先验压缩，HB不因缺维护样本被整体禁止 |
| J1 | compression_facade pre-summary→scope collector→原joint lifecycle；noting_child独立Loop | 本轮仅加数值观察和发布见证，未串行等Note；普通取消未提交Note/已提交保留、Force不可取消/封区间不变 | 当前native四接缝diff；test_empirical_wiring 19参数化；wiring/rotation-final-tests.log | 符合：计量按实际并发和owner，不改变触发/取消/容量/前缀 | 受控transport正式链证据，非付费模型/新UI流式验收 |
| B1 | heartbeat/conversation store→heartbeat_route→既有UI宿主run_conversation | DB所属Profile稳定ref、一个定义/claim；压缩同ref、new/fork无继承、active冷恢复、paused/clear不复活；原生模型/工具/Prompt执行保持 | test_adaptive_model_config/integration；wiring/initial-tests.log；75依赖SHA | 符合：本轮未造HB Agent/路由/执行器，页面不为owner，关闭走native | 不操作UI或生产；保留原生同SHA路径证据 |

## 4. 核心目标及验证方法审查

**完整纵向路径：** 可信Web/Gateway/原生HB/Reminder入口标记→真实Main请求/结束→Profile/Conversation自己的bounded数值事件及显式import/bootstrap→可知/成熟特征→最多128个30m转移、32未来需求粒子→最多12维护组件场景→相同路径计算费用、执行、碰撞/等待→m/T/δ同快照原子提交→原生Idle/HB正式领取→普通Note/Compact并发→成功/失败/取消收据/结算→mode-only后续刷新。当前正式获取和更新均已读到，非孤立helper。权限/关闭/owner/config/epoch/claim/refund/重启/已消费Idle及原生容量/Force保护均逐项核查。

**人的阶段结果：** 预先固定九段合理覆盖增长、短暂停、低使用后台、再次回归及高存量机会。当前真实CLI（f7，与c301非取消代码等价）E01/E02/E04零维护，E06/E08各一次实际模拟完成，分别条件少597664.01/2628378.29输入等价，关闭“永远不维护”的结构性问题。连续E01从新epoch67817跨到共同截止两次维护，末context123878.5；回归阶段自己的94778→102767.5不再维护。第二次较只首维护同初态/终点边际少194336.60，有费用与下游责任依据。不是看单次T或可解释拒因就判过。

负结果同样保留：E03原5h亏454484.72，共同终点才少2277454.61；E05亏23830.64；E07独立大context起点原截止亏849494.73、共同终点仍亏121905.21；E09亏6775.92，末态冷读压力为正不等于已赚。当前模型E06亏46227，当前模型整账单E06不维护且亏105735；机械失败E06亏1106461；rawcoverage/unknownReminder E08不维护。冻结R7没有要求每噪声/昂贵压力事后都盈利，且原案例未被改为新增容差；这些边界不能掩核心基础机会，也不能把条件估计冒生产实测节费。无真实完整无后读/Stop片段，用明确机制补充。Validation/no-future-decision.json为非空经验且无未来读取的正式decide零费用/TNone，非G17缺经验空跑。

**版本与证据复用：** 本次官方runner独立3项artifact审计通过（1.1秒），另1项针对正式取消等待的反证失败（0.03秒单次执行，完整runner日志保留），未重跑大套或13矩阵。独立核9原件SHA/字节及仍存在的原件一致，固定经验SHA不变；75份v11副本SHA均匹配，当前源均匹配c301树，仅policy与Replay不同。policy的G17修补在有经验路径直接调用同一未变scenarios，零经验不再fallback prior；r2曾独立九原始起点前后完整dict相同、1919保存经验分支审计，本次重新核其各artifact SHA并读路径。c301相对f7产品仅Replay取消两处诊断名称，测试扩高/低/无receipt；无取消base/journey/failure/raw/无经验路径不进入该分支，可迁移f7实际CLI证据。v11为有条件版本迁移，f7为实际公开CLI执行，G18修补取消为当前新CLI，三者不混称本次重跑。

G18本次独立比较原validation/cancel-input SHA一致，原f7与新g18-cancel整个results在仅替换旧字段名并排除elapsed_seconds/single_decision_seconds实测时钟后逐字段相等。paid仍1143046.3337856613，高于完成参考778332.0856089034；取消恢复275039，后续1成功/1失败，总费3542399.363008806，来源是原历史取消receipt而非免费/截断。33项新测试实际校验低30/高150相对完成100和无receipt代理的费用、状态、来源；字段无依赖消费者。旧错误“上界”不成立，现在如实称sampled reference，因此G18关闭，未改价格、抽样或费用。

**测试依据审查与新反证：** 多数受控测试直接调用正式策略或原生facade/真实DB/Loop/发布路径，能抓owner替换、mixed合同、迟到信息、零经验、取消费用、epoch及关闭失效，不是镜像实现/源码字串断言。旧取消路径测试只断成本/context/碰撞，没有核Stop实际缩短后expected_wait；Replay测试已核actual wait释放，却未对照正式预测，错误实现仍会通过33/146项。此次从初始R4独立提出“排队后Stop改变实际阻挡，风险是否同步结算”并取得反证：同源成本/释放正确、wait错误，可单独导致拒绝。真实历史九段没有Stop，不能用它们PASS豁免该合法历史分支，也不因此改写其有效数值。后续修复须按同一判据验证，不能放宽等待上限或丢掉取消样本。

资源复用明确：g17-resource的decide及所有依赖SHA与当前相同，唯一改Replay不被单次decide调用，故249事件+43组件、无trace0.18252979秒、trace2.08956342秒、Python增量峰1025839字节可用；非RSS/正式机/4096极限。原13矩阵408.459秒是整体，不充单次延迟。规则/等级/Actions/锁无本轮变更；ruff/health修后通过，旧十检查no-tmp失败是冻结基线原历史行，非全绿、不加豁免。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| G19 / V3-01 | 初始R4；rollout.py:87–100，policy._evaluate_maintenance | 同经验路径维护0–1000，10% user2排队/Stop3实际释放，90%1200回归；应等待期望.1，实际99.8；collision.1在.15内，候选有809895收益/reads.9，只被expected_wait_limit拒绝 | P2范围内阻断：风险仍使用已被取消的完成时刻，违反实际Main阻挡计量及同源结果；合法Stop历史可令有收益机会被误否。不是字段解释或要求降阈值 | root调查并提案；保持费用/来源/碰撞定义/显式上限，按实际释放结算取消前队列等待，Stop本身不制造未发生等待；补无排队/单/多排队/无Stop/失败/同刻边界及正式候选选择证据，原反证留存 | 开放，已集中告root；本轮不改产品 |
| G18 / V2-02 | R4/R5；Replay._cancel_running:376/390 | 原paid1143046.33高于错误full_cost_upper_bound778332.09；c301仅名改sampled_completion_cost_reference/unknown成本代理 | 原解释缺陷成立；当前费用及来源/取消恢复不变，参考名不冒上界 | 高30/低150/无receipt33项、同输入当前CLI与完整results等值独立核验，源码与输入SHA明确 | 已关闭；原失败/提案/r2撤回结论完整保留 |
| G17 / V-01 | R3/R8/E7；policy._maintenance | 原零经验仍可用任意固定prior产生主动T；当前只用empirical.scenarios，缺失记录unknown、HB不全禁、原生unknown容量回原生 | 原P1缺陷成立；当前完整legacy/组件保留，零/不完整不偷渡，修补未删坏样本 | r2全轮独立146项/9起点/1919分支证据；本次源码路径与SHA及实际无经验CLI复核 | 已关闭，历史反证仍留存 |
| B01（条件边界） | R3–R7；scenarios/prepare | 完整同parent联合账单支持0，GPT Compact缺独立账单，prefix费用/跨模型组件/绝对与比例缩减包络/coverage与排期为声明工程假设 | 冻结允许稀疏组件估计且要求披露；当前有同target/模型/整账单/慢尾/失败/raw压力，非新阻断；不得冒实测节费 | 最终交付显眼摘要待追认工程收敛及负数，后续自然样本校准，不因本轮补生产模型 | 保留披露，非PASS保证 |
| B02（经验边界） | R6/R7 | 真实原截止及压力负结果保留；E06/E08基础机会满足；无真实完整无后读/Stop只机制补充 | 按预固定整段机会与保护判断，不追加每窗口都盈利/0.52%容差；G19机制不能因九段无Stop豁免 | 当前真实CLI与条件迁移区别清楚；Validation仍须独立复验 | 保留披露 |
| O01（范围外） | 冻结no-tmp历史行 | 旧全十检查报.autonomous/20261031-evidence-recovery/validation.md:20，已与基线逐字证明不变 | 非本轮新增，不改旧报告求绿、不放宽检查，不宣称全套全绿 | 旧artifact-source-audit.json；root按原权限另行处理 | 范围外保留 |

## 6. 修复与独立复审

这是r3全新全轮复审，先重新提取26条完整判据再查看旧发现，不限G18。没有退回补审。r1初审32条及完整报告仍在verification-r1/criteria-initial.md和verification-r2/verification-r1-final-original.md（SHA ba29e4f…5031）；r2原通过时点报告verification-r2-before-g18.md及含更正/研讨的完整报告verification-r3/verification-r2-final-with-g18-original.md均保留。旧通过因G18撤回是真实历史，不能改成当时即通过；r3当前G18关闭不恢复此前整体PASS。

**历史实质研讨链保留：** G17初始判据要求真实/可追溯维护分布，零经验反例T32768→root提议正式_maintenance集中只用empirical.scenarios、完整legacy保留、无经验不禁HB/unknown容量回原生→r1审查方向及五类必要证据→f7实现/146项/九起点及1919经验分支证据→r2全轮关闭；r3核机制与版本有效性继续接受。G18原R4/R5要求费用解释如实，Validation实际CLI反例paid高于所谓上界→root提案仅改两诊断名、保持paid/选样/风险/状态→r2评审方向与五类关闭条件，撤回PASS→c301两处改名及高/低/无receipt机制、同输入当前CLI→r3独立归一化完整结果与来源/取消恢复/后续结算，G18关闭。两者均未改变冻结规格或用户阈值，提案通过从未冒称已实现。

**G19当前研讨：** 原初始R4“Main阻挡仅按实际会阻挡Main阶段估计”固定不变。独立读正式rollout而非旧问题清单，发现成本按Stop更新、事件按Stop释放，但wait仍max到旧maintenance_end；声明反例经官方runner失败，原json/log完整保留。根因是风险聚合未随取消的实际释放重新结算，不是需要用户补统计公式或取消语义。root已提出最小方案：常数空间记录同一维护最早实际被挡的普通user原到达时间，最终maintenance_end确定后按max(0,最终释放－最早受阻)结算该路径最大维护等待；Stop仍属真实回归collision，但自身立即释放不生成原剩余等待，后续Main自身busy不计入维护。Verification按原R4判据评审方向通过，要求原反例evaluate=0.1、正式候选旧expected_wait_limit拒因消失，以及Stop-only、单/多排队、自然完成、同刻边界、取消后继续使用及高/低/无费用receipt不回归；必须按原到达而非重排时刻，完成边界保持严格<原语义。root另提出核预测路径是否含cancel后决定真实矩阵重跑范围，Verification认可不能仅看实际外部Stop为零即宣称不受影响。原包确有1条可信activity=cancel，未来评估可采到过去取消，须按依赖/输入分支实证影响。截至本报告产品仍c301，方案未实施，无关闭证据，G19开放。费用、来源、碰撞语义、显式体验上限及经验预期不得为通过而改变。

供final-delivery及主会话汇报摘要：当前不是可交付完成状态。主要真实经验机会已模拟成立，G17/G18关闭，但G19须修复并取得当前正式预测等待/选择证据，再按套件全新全范围Verification及全部适用Validation复验。费用/规模迁移/历史coverage与排期条件仍为Agent工程收敛，非用户逐公式批准或未部署实测节费保证；明确禁止上线。
