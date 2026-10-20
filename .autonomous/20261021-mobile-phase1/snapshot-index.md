# Snapshot Index：20261021-mobile-phase1

## 审查依据索引

| 输入类别 | 实际仓库文件路径或本文件位置 | 修改等级 |
|---|---|---|
| 用户需求 | docs/hermes-network-experiment-20261020/README.md、HANDOFF.txt、PHASE1-IMPLEMENTATION.md、UX_ACCEPTANCE.md、EVIDENCE.md（均在同目录） | 二级 |
| 权威规格 | docs/06-Hermes-Secretary-Web-UI-V1-Spec.md（现有产品不变量）、docs/08-profile-scheduler-files-clarification.md（归属）；白板与07仅保留现有Secretary／Noting不变量；本轮具体变更以PHASE1-IMPLEMENTATION.md为准 | 二级 |
| 编码指导 | AGENTS.md、README.md、docs/cloud-deployment-sop.md；分区AGENTS只作接口／架构参考，不引入新规则 | 二级 |
| 会话确认口径 | 本文件“口径与决策” | 二级 |
| 本索引 | .autonomous/20261021-mobile-phase1/snapshot-index.md | 二级 |

冻结提交见baseline.txt。以上相对名称均相对仓库根；任务包内文件使用完整目录前缀。产品代码、计划与证据三级；根CLAUDE动态状态可依用户要求更新。白板、07与旧轮次报告不在本轮修改范围。

## 口径与决策

| 口径编号 | 用户意图、确认结论或约束 | 决策理由及确认假设 | 用户消息定位与授权来源 |
|---|---|---|---|
| C01 | 完成阶段一，不新开worktree | 同目录协作，保留他人修改，不整树暂存或覆盖 | 2026-10-21“明白，那就不开 worktree，开始完成阶段一” |
| C02 | Noting／Provider由另一会话负责；最终由本会话统一验证、一起上线 | 旧P1-07已上线不重做；另一任务最终变更须亲审，不能将现有调查当修复完成 | 同条消息及首次任务消息 |
| C03 | 允许直接向“分析品质会话未结束原因”会话协调并接收证据 | 文件／符号边界，冲突串行；不替另一会话决定Provider协议 | 异步提问回复“允许直接协调” |
| C04 | 挂持续目标，今晚完成，不使用Astra模型 | 委派使用gpt-6.1-sol／high | “给自己挂一个目标，今晚完成工作。无需使用astra模型” |
| C05 | 阶段一保产品交互，复用原机制；refs默认关闭且失败inline；纯图同一row/UID；不改模型／Prompt／预算／schema | 任务包给出完整实施与验证边界，当前授权明确援引阶段一 | 指定任务包及开始执行消息 |
| C06 | 只准自己创建的隐藏IAB，禁止外部浏览器／可见页／桌面／切焦点 | 用户显示保护持续有效；无法合规取证则如实记缺口 | 根AGENTS用户规则；本轮未获显示例外 |
| C07 | 阶段二等实验结果再设计，不在本轮实施 | 网络短实验仅在实际环境及权限允许时执行，不强改手机网络或动用户页 | 任务包README／EXPERIMENT与本轮范围 |

明确不做：新同步契约、SSE、持久缓存、新提交表、认证状态机、默认缩小200行、删除强制刷新、放松Send、扩大图片访问权限、重放旧生产Noting。无待确认的实施口径。
