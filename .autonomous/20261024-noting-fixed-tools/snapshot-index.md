# Snapshot Index：20261024-noting-fixed-tools

## 审查依据索引

| 输入类别 | 实际仓库文件路径或本文件位置 | 修改等级 |
|---|---|---|
| 用户需求 | .autonomous/20261024-noting-fixed-tools/user-request.md | 二级 |
| 权威规格 | docs/notebook-ontology-whiteboard.html；docs/07-scheduler-notebook-noting-compaction-redesign.md（2026-10-24修订优先，业务其余保持）；docs/06-Hermes-Secretary-Web-UI-V1-Spec.md（今日既有微信／Web修补）；docs/cloud-deployment-sop.md（首尔§0与升级／保护） | 二级 |
| 编码指导 | AGENTS.md；README.md；CONTRIBUTING.md（仅环境与架构参考，不导入新门禁） | 二级 |
| 会话确认口径 | 本文件“口径与决策” | 二级 |
| 本索引 | .autonomous/20261024-noting-fixed-tools/snapshot-index.md | 二级 |

## 口径与决策

| 口径编号 | 用户意图、确认结论或约束 | 决策理由及确认假设 | 用户消息定位与授权来源 |
|---|---|---|---|
| C01 | 两工具Schema／description逐字段不变；只固定API顶层注册，不折叠，不再消息级动态注册 | 避免不必要的Kimi Schema变动；不重写Moonshot转换规则 | user-request §1、2条1；用户“Schema 和 description 完全不动” |
| C02 | Main Root禁用提示；Noting明确启用两工具且只准四工具 | 继承父提示后当前任务显式接管身份／权限；Main其它能力保持 | user-request条2–5 |
| C03 | 初始与续Turn不再注入完整Schema；保留完整工作Notebook与必要数据 | 用户最新明确覆盖之前重复Schema候选 | user-request条4及原话“Schema也不再需要重复” |
| C04 | 执行权来自真实运行时身份和绑定；Main／其它子Agent拒绝两工具；Noting四工具外拒绝 | 顺序、并发、invoke／间接调用均不得绕过；声明不等于授权 | user-request条5；07§3.1–3.2、4.5、5.1 |
| C05 | 父子Root／tools／冻结消息及缓存作用域一致，冻结后不重建；旧前缀在正常边界一次生效 | 不在child临时补工具或重写父历史；首次新增工具不可声称旧缓存字节不变 | user-request条6；07§3.1及2026-10-24修订 |
| C06 | Alex本地隔离副本、实际kimi-for-coding、保原业务Prompt／Persona；仅本地缩阈值／延迟小成本跑通 | 使用独立Home／runtime／DB／仓库外cwd，不启动生产排期或外发；“地址词”按上下文为提示词 | user-request条7–8；用户明确准许 |
| C07 | 观察自然误调与Harness拒绝；任务无重复Schema仍实际使用四工具并正常完成 | 少量错误正确拒绝后改正可接受；确定性拒绝测试与自然频率分别报告 | user-request条8–9 |
| C08 | 今日既有修补与本次改动统一提交、push并部署云端，验证实际版本及数据保护 | 后端599d114、前端589df02在交付闭包；不把隔离配置带生产 | user-request条10及追加“连同之前今天那些修复一块部署” |
| C09 | 子Agent全部Sol系、不使用Astra；遵守显示保护和冻结10检查 | 自主流程含独立Verification／Validation；不降门禁，不伪称未验范围 | user-request条11；AGENTS |
| C10 | 不动生产历史／排期／绑定、不重放旧失败任务、不改来源包裹／Thinking／Timeline机制 | 隔离验证与发布不是数据恢复授权；旧47错误副本恢复不属本轮 | user-request条12与已有明确保留范围 |

当前不存在阻断实施的未决产品问题；内部任务安排和测试预算写plan，不改用户完成标准。历史文档中“任务后缀四Schema／动态声明”由上述修订覆盖；其它保留契约不扩大。Schema canonical SHA冻结：notebook_maintain `4fbaab4cec9b50d7ed87888ba1a3cebaf6453b438d7a3ae06c2d7171b2b2ad3d`，finish_noting `59b73e172fd24a3c704f85b84adce58075d58fd8f965e9334544d288e20f0267`。
