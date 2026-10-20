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

### 联合Noting交付依据补充（用户在并行会话明确确认）

2026-10-21并行会话“分析品质会话未结束原因”用户消息01a15a3b-187f-7ed1-9d85-2a238e35f300明确“我同意，把Kimi的实际API改成OpenAI compatible”，后续01a15a3f-7c4f-78c1-b75f-ae13043b712e明确“我同意你的选择”，要求听从本活跃会话指挥、本地构造继承K3-256k的真实短Noting后交本会话统一上线。主会话已通过read_thread读取原始用户消息核实。C02补充：保留原生kimi-coding Provider，原生配置chat_completions及https://api.kimi.com/coding/v1，动态工具声明仅在Noting请求接缝，不自造Provider、不改公共消息格式或DB；由外部会话实施。此为联合发布新增明确授权，不扩大阶段一实现Agent白名单。初始基线仍保留，补充依据提交随后追加baseline.txt。

### C08 · 用户调整执行与Validation顺序（本会话最新明确授权）

2026-10-21用户原话：“先部署，再做简单的 validation，并且记录表现。但重点应该不是响应，而是请求体大小，以及请求时机之类的，因为你现在在 WiFi 网络下。我授权你不严格按照 Autonomous Run 套件执行”。随后强调“最后一定要保证部署无误，保持 Hermes 线上运行健康”。据此本轮不以严格套件独立两门禁或部署前全场景UI作为发布前置；上线前仍亲审代码、完成相关测试、构建与回退准备，部署后以真实历史/图片数据验证字节、请求次数及触发时机，Wi-Fi耗时只作观察，不推断蜂窝体验。线上健康为硬门槛：空闲切换，后端真实只读API就绪后发前端，鉴权/WS/Gateway连接/Profile数据/实际宿主版本检查，新增回归及时分项回退且不回盖运行DB。并行会话用户明确要求的本地真实K3短Noting证据仍为该交付的接收条件。
