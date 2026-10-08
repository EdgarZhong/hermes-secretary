# 1.5 轮：补充调整、完成剩余工作与最终验收

## 当前阶段

首轮自主实现已按用户要求告一段落，完整目标尚未达成。现在进入 1.5 轮的文档准备阶段：整理已确认的小调整，承接首轮剩余工作，最终完成独立审查和用户验收。

当前只修改、提交并推送文档；没有恢复编码，没有派遣子 Agent，也没有启动测试或验收。文档同步后暂停讨论，等待用户下一步指令。01 / 02 已按用户授权解冻；保留的代码检查、阈值和协作约束不变。Foreground 设计由用户另行调整，本会话不补方案。

- 产品代码起点：main，7533173ca315d6308b121d313f0dd281777c8604。
- 当前口径：[1.5 轮索引](.autonomous/20261008-v1.5-adjustment-and-acceptance/index.md)。
- 首轮实际状态：[首轮状态记录](.autonomous/20261007-v1-first-implementation/final-delivery.md)。
- 首轮冻结提交、计划和独立报告保留在原轮次目录；审查历史须读取当时的提交树，不能以新规格追改旧报告。
- 1.5 轮尚未建立实施冻结基线；Foreground 设计及其他未决口径收敛后，再按用户指令制定计划和开始实施。

## 已确认的设计调整

| 层次 | 最新要求 | 当前代码状态 |
|---|---|---|
| 用户主 Conversation | 只有直接与用户交流的主会话拥有 Notebook / Noting System；通用 Cron、Dreaming、Skill 打磨及 Subagent 均不参与，不论全局开关如何，其工具列表都不能出现 notebook_show | 需在 1.5 轮核对所有构造、继承和刷新入口，不能仅凭当前 main 判定 helper 宣称覆盖 |
| Notebook 读取 | 主会话资格成立后，notebook_show 只受全局配置控制；局部 Noting 关闭仍可读已有 Notebook，主 Assistant 永远只读 | 当前 surface、inline dispatch、handler 仍使用局部 Noting 门禁，待调整 |
| Slash 分层 | /notebook 只展示人类可读内容，AI 通过正常历史也能看到；/noting on、/noting off 只控制本会话后台 Noting | 当前代码仍提供旧 /notebook on、/notebook off，shared catalog / completion / dispatch 等待同步 |
| History Search | 与 read 同等的一等只读工具，配置、Agent 模板和权限规则与 read 对齐；能查当前未压缩历史及跨压缩历史，与 Noting 无关 | 当前 main hook 强制注入及通用 Agent 配置/模板覆盖需调整，旧测试不证明新契约已满足 |

专用 Noting Runtime 仍是主 Conversation 的维护者，按 02 的 Parent ownership、cache parity 与受限读写契约工作；它不为自身或普通后台 Agent 开启独立 Notebook。

01 / 02 已同步上述功能要求。README 的命令表继续如实列当前已实现入口，新命令不能在实施前宣称可用。

## 1.5 轮工作与启动条件

| 工作 | 当前状态 | 下一步 |
|---|---|---|
| Notebook / Noting 分层与主会话资格 | 已更新规格，未实施 | 用户授权恢复后安排实现，覆盖暖会话、冷启动、工具继承与局部切换的 schema 稳定性 |
| Slash 改名 | 已更新规格，未实施 | 复用共享链路，核对 CLI、Gateway、Web；不预先改 React 或新增 API |
| History Search 与 read 对齐 | 已更新规格，未实施 | 复用普通工具注册、配置、模板和只读边界，验证当前段历史与跨压缩检索 |
| Foreground 审计缺口 / 设计调整 | 首轮缺口保留；用户将另行修订设计 | 等待新设计，不自行补来源字段或引入新概念 |
| Branch 后继续压缩的路径风险 | 尚未取得完整反证或关闭证据 | 后续先复现并核对新 Foreground 契约，不把静态线索写成已确认缺陷 |
| 独立 Verification | 首轮报告不通过；1.5 未启动 | 新设计和实现收敛后，由全新审查者核对当轮完整要求，不只复测旧清单 |
| 官方 Dashboard 用户验收 | 首轮未执行；1.5 未启动 | Verification 通过后，在 localhost 用内置浏览器独立验收，不使用 Computer Use |

文档修订已改变契约，首轮通过项和局部测试只在未受影响的版本与行为范围内复用；不能当作 1.5 轮已通过的证据。实施任务与 Agent 编排只在本文件维护，目前无新任务派遣。

## 仍待收敛的提议与取舍

- MCP：用户提议以最小修改固定原生三工具桥接模式，并删除 /reload-mcp 一律宣称缓存失效的提示。只记录提议，尚未实施或作为已确认要求写入规格；不据此删除其他确认流程，不新增 Hub。
- 全局配置：当前 Secretary 在主 Turn 起点重读所属 profile 配置，全局 Noting 改变可以在同一 Conversation 的下一 Turn 增删 notebook_show，存在前缀缓存开销。原生 CLI /tools enable、/tools disable 开新会话；Web/TUI tools.configure 保存配置后调用原生 session reset。不存在所有全局配置变更统一热切换并接受缓存损失的策略。1.5 轮全局生效时机和取舍尚待收敛，不自行新增缓存管理机制。

## 首轮证据与实际限制

- Identity、Notebook / Snapshot、Noting、History、Schedule / Reminder、共享 Slash 和少量通用 Prompt 已在正式路径实现；旧 Background Review 开关及 /refine 已清理，独立 /review 保留。真实 Codex Proxy / GPT6 Luna / High 已完成 Parent → Noting → Snapshot 链路；Hermes 仅作为被测产品。
- 独立 Verification 钉住 7533173：101 条要求，98 符合，2 违规对应同一 V10 审计缺口，1 项本机平台不适用；报告不通过。用户输入到输出的 Dashboard Validation 尚未执行，前端构建成功不等于验收通过。
- 唯一扩大 Python 回归在 6a75369：13,318 通过、117 失败、109 跳过。后续按失败类别做了定向修复、测试适配和环境对照，没有重跑整套；因此没有完整 suite 全绿的结论。117 项分类及后续证据见首轮报告与 .hermes-dev/evidence/final-local-ci/。
- 后续主动 Reminder / 崩溃恢复共 184 项有效定向证据；cache-parity 已证明请求字节关系，没有实际 provider 缓存命中率测量。十类保留检查及增量检查按首轮证据记录，不扩大为新版本全量通过声明。
- 当前只在 macOS 实测；Linux / Windows 未实测边界保留。没有部署云端应用或接入个人外部消息渠道；本次 push 只是文档与代码仓库同步。
