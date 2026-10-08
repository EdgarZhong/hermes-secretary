# Snapshot Index：20261008-v1.5-adjustment-and-acceptance

1.5 轮是首轮小调整之后的补充完成与最终验收，不是 Personal UI 产品化的第二轮。用户已结束首轮、解冻文档，并授权本次文档提交和推送；实施尚未启动，讨论在同步后暂停。

本次是文档阶段快照，不是实施冻结。Foreground 新设计等未决项需后续收敛；尚无本轮 baseline.txt，也不把首轮的冻结哈希冒充 1.5 轮基线。动态看板仅在根 CLAUDE.md。

## 审查依据索引

| 输入类别 | 实际仓库文件路径或本文件位置 | 修改等级 |
|---|---|---|
| 用户需求 | docs/01-personal-hermes-v1-first-fork-iteration.md | 二级；用户已明确解冻并授权修订 |
| 权威规格 | docs/02-noting-system-specification.md | 二级；用户已明确解冻并授权修订 |
| 编码指导 | AGENTS.md | 二级；文档状态与入口可同步，原代码检查类别、阈值和协作约束保留 |
| 会话确认口径 | 本文件“口径与决策” | 二级；记录用户明确确认，调查推断与提议不冒充已确定要求 |

首轮历史依据和报告留在 ../20261007-v1-first-implementation/，由其 baseline.txt 和报告钉住的提交树确定。1.5 轮最终审查必须重新读取届时冻结的完整现行要求，旧符合项只有在版本和行为范围仍有效时才能复用。

## 口径与决策

| 编号 | 用户确认的内容 | 适用边界 | 用户消息定位与来源 |
|---|---|---|---|
| B01 | 首轮告一段落，进入“1.5 轮”：小调整后的补充完成与最终验收；01、02 文档均可修改 | 解冻的是文档基线，不代表目标已经完成或允许改变代码检查规则；第二轮 Personal UI 产品化边界保留 | 用户“首轮自主实现告一段落……解冻文档……进入1.5轮……补充完成和最终验收……02文档、01文档也都可以修改” |
| B02 | 局部 Noting 开关成为后台行为开关，不影响主会话读取 Notebook；主 Assistant notebook_show 只受全局配置控制 | 先满足 B04 的用户主会话资格；后台参与门禁与主读取门禁分开，不新增缓存管理或桥接机制 | 用户“我们要改的是自己的设计……只变成一个行为开关，不影响主会话，正常访问 Notebook……工具……只和全局配置有关” |
| B03 | /notebook 保持人类可读展示，AI 也能看到；/noting on、/noting off 控制本会话的后台 Noting | 替换旧 /notebook on、/notebook off 入口；保留普通历史、Snapshot 时间、无 Snapshot 提示；不默认增设别名或 UI/API | 用户“把 slash 命令改成 notebook，以及 noting on 和 off……notebook 还是一样的逻辑……AI 也能看到……只决定……background noting 功能” |
| B04 | 只有直接与用户交流的主 Conversation 拥有 Notebook 和 Noting System 的功能与暴露；Cron、Dreaming、Skill 打磨及通用 Subagent 与之无关，任何全局开关值下都不暴露 notebook_show | 普通配置、模板或工具继承不能授予这些 runtime Notebook；专用 Noting worker 仍只维护所属主 Conversation，保持原 §5 契约，不获得自身独立 Notebook | 用户“只有和用户直接交流的这个会话，才有 notebook……Cron Task……dreaming……skill的打磨……subagent……不管全局配置……notebook show 也从来不会出现在他们的工具列表里” |
| B05 | History Search 是与 read 同等的一等只读工具，配置及 Agent 模板对齐 read；可主动检索当前未压缩历史，也可查跨压缩历史，不从属于 Noting | 遵守原生工具选择、模板及只读权限，不由 Secretary 强制注入；可供普通后台/子 Agent 按正常配置使用，不据此扩大历史读取范围 | 用户“history search……跟read、write、bash……一等工具一样。配置方式……agent模板都保持一致……本轮也可以搜……主动召回……属于只读……直接对齐到read” |
| B06 | Foreground 审计缺口涉及用户将另行修订的 Foreground 设计，可能增加新概念，本会话不展开 | 保留首轮实际缺口，不自行设计补字段或新来源机制；后续以用户修订的契约决定实施与验收 | 用户“Foreground审计缺口……有必要改一下Foreground的设计……新概念……就不在这里进行了” |
| B07 | 本次按现状整理文档，提交并推送到云端，随后停止讨论 | 覆盖文档与状态同步，不恢复编码、派遣或测试；Git push 不等于云端应用部署或最终验收完成 | 用户“提交一轮文档……状态都推送到云端……讨论……先停在这里……按现状整理好文档，然后提交推送就行” |

继承的已确认范围：公开 main 核心；少量通用 Prompt 文本；共享 Slash 优先零 Dashboard 专属补丁；官方 Web UI、localhost 前后端、内置浏览器验收；macOS 实测并如实记录其他平台；必要的本机 Codex Proxy / GPT6 Luna / High 测试，Hermes 不参与编码；/propose-persistence 只提议、后续自然语言批准；旧 Review 开关和 /refine 删除，独立 /review 保留。原授权来源见首轮索引 A02、A05–A07、A11–A12、A14–A17、A19–A26，不冒充本次新增问答。

未决事项：Foreground 的新设计等待用户另行提供；全局配置改变工具面时的生效时机和缓存取舍尚未确定。MCP 固定三工具桥接模式及删除统一缓存失效提示仅记录为用户提议，未作为已确认实施要求写入 01 / 02。

明确不做：本次编码、测试或应用部署；Personal UI 选型/面板及新的结构化 API；新增 MCP Hub、缓存管理或平行 Agent/调度/存储机制；在本会话自行提出 Foreground 新概念。
