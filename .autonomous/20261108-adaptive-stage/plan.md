# Plan：20261108-adaptive-stage

## 1. 目标与依据

依据snapshot-index.md与baseline.txt，落实V31–V314。11/9用户已授权在原算法分支完成实现、历史回放并通过后合main上线；按轻量流程推进，最后独立场景复验与一轮研讨。基线产品为660b5a63所含V2，本轮冻结ea3001b56。根其它任务dirty保护；提交主会话统一，子Agent不提交／不派生。

核心：高频观察与缺样本保热、数据就绪立即重评、较长历史近期加权、维护规划max与Main阻挡分账、已知提醒接力、按完整费用独立选档。完成条件为真实情景整段行为接受、定向机制与最后独立场景复验完成；不以平均费用或旧V2 PASS替代。

## 2. 覆盖与任务表

| 任务 | 要求 | 负责人／白名单 | 接口与依赖 | 验证与完成条件 |
|---|---|---|---|---|
| A 策略、经验与计费 | V31–V33、V35–V310中的算法内容 | root（用户指定核心算法本人完成）：secretary/adaptive_policy.py、adaptive_cost.py、adaptive_empirical_maintenance.py、adaptive_forecast.py、adaptive_features.py、adaptive_empirical_features.py、adaptive_learning.py、adaptive_rollout.py；可新增adaptive_stage.py／adaptive_stage_history.py；tests/secretary/test_adaptive_stage_policy.py及自身算法相关原测试 | 保decide签名；Profile增可选planning_duration或等价明确字段，duration旧Main阻挡语义不混；diagnostics.stage/readiness/planning/reminder_bridge/history_support可JSON。config新可选字段与B协商；不写runtime／import／replay | 正式decide数据不足hot、short阶段不预约保护到点、长闲机会、Reminder桥接与反例、max计划不同Mainwait、冷热成本翻转、无未来泄漏；短/长历史与衰减敏感性；保存独立段支持及来源 |
| B 历史／就绪的正式接线 | V32–35、V311 | stage_wiring：secretary/adaptive_runtime.py、adaptive_config.py、adaptive_model_config.py、adaptive_store.py、adaptive_import.py、adaptive_bootstrap.py、adaptive_observation.py、adaptive_samples.py、scripts/adaptive_empirical_import.py、scripts/adaptive_history_import.py、scripts/adaptive_history_bootstrap.py；可新增adaptive_refresh.py；tests/secretary/test_adaptive_stage_wiring.py及该区域原测试 | 调正式decide；导入事务成功后既有owner通知／tick，忙／冷恢复不新造调度器；与A共同可选配置；学习语义归A，通知及持久来源归B | 真隔离DB导入→立即重评→持久结果／重复／失败／busy／cold／restart；已登记切模继续／未登记原生；manualpause优先／claim不丢／anchor不变；长history不因最近HB挤掉 |
| C 真实场景与回放 | V312–314、V37／38的实际模拟时序 | root（用户指定实际场景定性判断本人完成）：secretary/adaptive_empirical_replay.py、adaptive_empirical_replay_data.py、adaptive_empirical_replay_report.py、scripts/adaptive_empirical_replay.py；tests/secretary/test_adaptive_stage_replay.py及该区域原测试；ignored .hermes-dev/adaptive-stage-20261108/replay/ | 先冻结新增场景／输入来源／预期与基线；A/B完成且root接收后才执行新版矩阵。新Profile planning字段与实际Main释放分开，需双结束边界不得把规划全部当阻挡 | 复用9原场景+连续旅程；补11/8真实已知Reminder、明确条件价表比较、缺数据hot／导入／切模机制等16类；旧线上/V2/简单stage/V3共同输入比较。报告负数、原件SHA、未知及每次维护HB费用context理由 |
| I 主会话集成 | 全部 | root：规格／CLAUDE／本轮套件；微小接线修补 | A/B先交回实际diff并亲审，C再跑；正式契约冲突集中解决 | 不复跑同版有效证据；集成变化定向验；最后相关冻结检查一次 |
| G 独立场景复验与研讨 | V314及11/9用户新要求 | 完成后新fork=none独立Agent，root亲审研讨并判定 | 按规划定性场景重新验收，不让实现解释替代用户目标 | 真实历史与必要机制证据，意见逐项讨论；不执行完整自主流程 |

## 3. 当前状态与编排

基线已冻结并按hook推送；11/9主会话接手A/C核心与回放，B辅助接线继续。当前机制、接线、定向验证和真实窗口定性判断已完成；最终独立场景复验与一轮研讨通过，已合main发布并核自然心跳采集／重评。A与B只交换接口必要消息；C第一阶段只收集／准备历史与回放实现，不与尚变动产品争跑大型矩阵。每包七项返回：条款、变更、正式路径、验证、缺口、接口、下一步。

Python测试仅`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh <目标>`，官方现有PM环境／lock，测试HERMES_HOME和cwd在仓库外隔离；禁止直接pytest、改PM依赖、生产导入或模型请求。现有`.venv`可用，不为基线跑大套；质量冻结d02f211仅相关检查，禁止降低等级。UI不在本轮范围；若需UI只允许自己创建隐藏IAB，禁止桌面／其它浏览器／现有页。

本轮默认24h主费用窗口、6h与共同末点对照；指数近期权重7天时间尺度（3／14天敏感性）。采用少量直接状态／条件空档统计及整段经验采样，不以增维或固定维护先验换PASS。资源边界可沿V2最多128起点／32轨迹／12情景，但须核独立支持量，不把重复origin当独立经历。具体文件接线与统计工程收敛由各包报告记录、root审查，不新增用户容忍门槛。

## 4. 缺陷与整改、取舍与快照

| ID | 问题／风险 | 负责／关闭条件 | 状态 |
|---|---|---|---|
| R01 | 旧V2短静默直接预约保护到点维护 | A：保护阶段hot无维护预约，实际观察边界后重评；E06对照 | 已完成，414机制与真实窗口证据见CLAUDE |
| R02 | 缺样本／导入后仍原生或等用户新消息 | A+B：hot实际采纳、资料到达接线立即重评 | 已完成，414机制与真实窗口证据见CLAUDE |
| R03 | 规划与阻挡时长混同、Reminder仅相交门禁 | A+C：两时间轴、桥接候选、真实14:50段与反例 | 已完成，414机制与真实窗口证据见CLAUDE |
| R04 | 回看过短、合同切换／裁剪丢历史 | A+B：长期代表性、近权重与模型继承验证 | 已完成，414机制与真实窗口证据见CLAUDE |
| R05 | 现有原件不等于完整10/28至今 | C：必要只读安全数值补取、明确缺口／条件，不伪造日期和来源 | 已明确旧包覆盖与来源；45组件含11/8长尾，未伪造完整日期 |

快照：ea3001b56要求冻结（无新产品）；先前空worktree及同名空分支已删除，没有遗留产品变更。无需用户补填工程细节才能启动；遇真实权限／产品语义扩大才询问。

11/9轻量流程收尾：独立final_scenario_review的16场景报告已接收；费用劣势和负截窗如实保留，不归为未经证明的必要安全成本。无范围内阻断，已按新授权合main发布2b7b706，Kimi配置／45组件导入和自然HB结束ready=true→hot1740已核。生产保持main，备份收尾完成。
