# V1.6 剩余交接

用户决定本轮只收尾实现，验收移至第二轮；**不要重做 V1.6 自身的全量 Verification**。复用已有有效证据，只补以下缺口及下一轮实际改动的影响。

第二轮按 `docs/06-Hermes-Secretary-Web-UI-V1-Spec.md` 实施：Web UI 在单独仓库，工作区仍为本仓库；本仓库按原生接口接线需要继续修改。外部 UI 完成后统一复查。

剩余：

- C15：通过实际 AI 工具和人类 UI 核对可读时间、时区与原瞬间；重建受改 UI 产物。Desktop 完整检查尚缺依赖，定向呈现测试已做。
- C16／VAL04：真实定时器到点后统一检查当前 Conversation 开关；off 不运行且之后 on／重启不补旧事件，on 只处理一次；补验 Main 忙碌时 memo auto-on、合法冷恢复。
- 未完用户链路：Persistence 查源→修订不写→明确批准实际写入→候选归档；Reminder idle／busy／deferred 批量／关闭恢复与隔离；剩余全局切换与冷恢复；branch／undo 与有效来源隔离。Full 审计 UI 按 06 的延后边界处理，不提前造接口。
- 已知检查限制：旧 Child fixture 的 `unknown_system_message` 在当前／冻结对照均出现；profile-archives 命中三份既有 SDK 归档。证据位于 `readable-times/`，不要冒称通过。

已有效完成的 History、六键 Notebook、长正文、memo 操作／消费和 Finish 呈现不机械重跑；原失败与版本证据保留在 `verification.md`、`validation.md`。

隔离 profile：`.hermes-dev/v1.6-validation/dashboard-final-4743943e`，库保留 6 sessions／157 messages／5 Snapshots；Dashboard 已停，临时 Idle 已恢复 2 秒。下轮使用最终源码重新构建／启动，不能沿用旧运行实例或旧 bundle 作为新版本证据。
