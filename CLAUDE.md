# V1.5 自主实施与最终验收

## 当前阶段与目标

2026-10-09 用户授权开始 V1.5 自主实现，依据附件自行完成 ask-and-align，无须新增需求问答。已挂 active goal：纳入规格、冻结基线、实现、独立 Verification/Validation 与最终交付。当前完成全篇规格核对和文档同步，准备冻结文档基线；尚未开始产品代码修改和新测试。

- 本轮索引：[index.md](.autonomous/20261009-v1.5-implementation/index.md)，snapshot-index.md 为同一正文链接。
- 增量权威：[V1.5 规格](docs/04-hermes-secretary-v1.5-implementation-spec.md)，附件原样纳入；M01–M25 全覆盖，未修订 V1 契约继续有效。
- 代码起点：main / 41f7057a28f8e9bf2fc6c8fb769748d9f2534012；产品代码承接 7533173ca315d6308b121d313f0dd281777c8604。
- 启动状态：工作区原先干净；Python 为官方 PM `.venv` 3.14.7；沿用现有 pyproject/uv.lock，不为建立基线重跑大型检查。
- 历史记录：[首轮实际状态](.autonomous/20261007-v1-first-implementation/final-delivery.md)、[1.5 文档准备快照](.autonomous/20261008-v1.5-adjustment-and-acceptance/index.md) 均保留，不追改其冻结结论。

## 本轮口径与覆盖

附件已解决前次 Foreground、History 暴露和全局缓存取舍未决项：合格 Main 默认 session_history+独立指导；Notebook 读取只按 Main 资格+全局开关；局部 /noting 只管后台；下一 Pre-message Context 同步 Prompt/Tools；Full 的唯一首节点为最新有效 Prompt/Tools Prelude；提案由主模型自主搜证。详见本轮索引与 04，不能继续采用旧 read 可配置 Main 暴露策略。

## 任务看板与编排

| 任务 | 当前状态 | 依赖与下一步 |
|---|---|---|
| 文档纳入、自主澄清、索引与冻结 | 文档已同步，待提交冻结 | 核对差异、原文和入口，提交后写 baseline.txt |
| 精确回退首轮未授权混合 Prompt | 待实施 | 冻结后审计 Git 差异并先回退指定增量 |
| Foreground/History/identity read | 待分派 | Full Prelude、逻辑节点、system 历史、source identity、branch 后压缩 |
| Main Prompt/工具门禁与 Warm/Cold | 待分派 | 真实资格、全局同步、局部稳定、dispatch 和 pinned tools |
| Slash/Noting/Schedule/Proposal | 待分派 | 共享 /noting、两句 task、五类 expression、自主搜证与审批 |
| 主会话接收与集成 | 待开始 | 亲自 review 正式接线、状态/失败/权限和证据 |
| 必要扩大本地检查 | 未执行 | 集成收敛并派独立门禁后统一一次，按影响选择范围 |
| 独立 Verification | 未启动 | 全新无上下文审查 V1 未改条款+M01–M25 |
| 官方 Dashboard Validation | 未启动 | Verification 通过后独立本机浏览器+真实模型验收 |
| 最终交付判定 | 未开始 | 两门禁关闭、缺口清空、证据匹配交付提交后判定 |

实现 Agent 使用 gpt-6.1-sol/high，白名单互不重叠；具体安排待 plan.md 建立。主会话负责全篇覆盖、接线、接收和最终判定。测试状态隔离，不写用户实际 Hermes 数据。

## 基线证据与限制

- 首轮独立 Verification 在 7533173 上为 101 条：98 符合、2 违规对应同一 Full root provenance 缺口、1 本机平台不适用；Dashboard Validation 未执行。本轮必须完整重新核对，不能把旧通过项冒充新门禁。
- 首轮唯一扩大 Python suite 在 6a75369：13,318 通过、117 失败、109 跳过，后续定向修复但未重跑整套；无完整 suite 全绿结论。证据在 `.hermes-dev/evidence/final-local-ci/` 与首轮报告。
- Branch 后继续压缩为首轮静态风险线索，尚无完整反证；本轮要求取得实际证据。
- 首轮实际 Parent→Noting→Snapshot、cache parity、主动 Reminder/崩溃恢复定向证据仅在对应版本范围内有效；不宣称实际 provider 缓存命中率。
- 平台只实测 macOS；Linux/Windows 未实测。如本机环境不具备相应能力，明确登记，不能模拟 OS 冒充验证。
- 不执行云端部署或个人外部触达；本轮本地提交默认获授权。
