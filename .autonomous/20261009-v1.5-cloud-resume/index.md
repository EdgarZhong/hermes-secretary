# Snapshot Index：20261009-v1.5-cloud-resume

本轮是 V1.5 同一目标在历史暂停轮次结束后的恢复实施轮次。历史 `.autonomous/20261009-v1.5-implementation/` 保持原样作为暂停证据，不追改其 final-delivery。当前轮次以本文件为唯一动态索引，根 `CLAUDE.md` 为显眼状态看板。

## 冻结输入

| 类别 | 权威输入 |
|---|---|
| 当前代码/文档基线 | `70c772180d1bb2aaf8bba8d27a8a64f7c2fabb12` |
| V1.5 权威增量 | `docs/04-hermes-secretary-v1.5-implementation-spec.md`（M01–M28） |
| V1 未修订契约 | `docs/02-noting-system-specification.md` |
| 历史定案记录 | `.autonomous/20261009-v1.5-implementation/index.md` C05–C17 |
| 项目规则 | `AGENTS.md`、根 `CLAUDE.md` |
| 自主实现方法 | 用户本轮提供的归档自主实现套件；当前主会话已读取 ask-and-align / autonomous-run / writing-plans / executing-plans / spec-implementation-review / real-user-acceptance / delivery-evidence-review |

## 本轮用户授权与边界

| ID | 决定 | 状态 |
|---|---|---|
| R01 | 恢复 V1.5 编码；当前网页端主会话独立完成 GitHub 连接器可以完成的实现，并直接提交 main；不派 subagent | 已确认 |
| R02 | 除代码外，同步维护自主实现过程文档，最终提交必须让本地 Coding Agent 拉取后可立即续跑 | 已确认 |
| R03 | 本地真实运行、DeepSeek/缓存抓取、Dashboard 用户验收由后续本地继续；云端不得把未执行门禁写成通过 | 已确认 |
| R04 | 已定稿 D01、冻结父前缀/后缀工具声明、五 Turn 双 Profile、forced Snapshot、termination 审计直接实施，不重新发明方案 | 继承 C11/C14–C16 |
| R05 | 项目 AGENTS 的“禁止扩张 + 必要最小自主收敛并登记待追认”继续有效；本轮尚无新的用户影响型自主收敛 | 继承 C17 |

## 本轮核心目标

只处理 V1.5 当前已查明的三个编码缺口：

1. **D01 实际执行来源门禁**：真实 Main 模型派发记录 native/external；Force 使用内存事实，Idle/Cold Resume 使用 sessions.model_config 同名持久事实；只在确认 external 时、任何 Noting 副作用前拒绝。
2. **Noting 生命周期与冻结前缀**：顶层 Parent tools/root/Anchor 前缀始终不改；Noting 合法工具及完整 Schema 只追加到 task/continuation 后缀；两个 Profile 都最多 5 Turn，以各自终止工具正常结束，超限 forced 收尾仍尝试 Snapshot。
3. **Snapshot termination 审计**：Secretary Snapshot 表新增可迁移的内部审计字段；新 Noting Snapshot 写入 finish_noting / compact_parent / forced；历史为空，branch 继承；普通 Notebook 投影严格不暴露。

不顺手重写已经保留的 Foreground、History、Schedule、Reminder、Proposal、全局/局部开关、Provider 路由或缓存层。

## 门禁状态

- 实现与主会话静态 review：本轮执行。
- 可在云端完成的源码级验证：本轮执行并记录真实边界。
- 独立 Verification：当前网页端无独立 subagent/fork_turns=none 执行条件，**未通过/待本地**。
- 真实 DeepSeek + 缓存日志/抓包：**未执行/待本地**。
- 官方 Dashboard 端到端 Validation：**未执行/待本地**。
- 最终交付只能标记为“云端实现完成、最终发布门禁待本地”，除非后续证据真正关闭上述项。


## 云端实施结果（截至本轮交接）

代码与定向回归测试已写入 `main`，云端静态 review 的实现收口范围如下：

| 范围 | 主要提交 | 当前结论 |
|---|---|---|
| D01 最近实际 Main 执行来源 | `aefd94b6f0`、`db88b6ce48` | native/external 在实际 dispatch 接缝记录；Force 用内存事实，Idle/Resume 用持久事实；External 在 Noting 副作用前拒绝；同 Turn rotation 继承事实 |
| 五 Turn / 冻结工具头 / Profile 终止 | `0edf956211`、`27d4463472` | 不再首响应后改写顶层 tools；task/continuation 后缀声明完整 Schema；同 Child 最多 5 Turn；continuation 继续使用同源时间戳的 `<noting-task>` carrier |
| Snapshot termination 审计 | `0edf956211` | Secretary-owned `termination_json` 迁移；三种 termination；普通 Notebook 投影不暴露；branch 继承 |
| 参数与回归锁定 | `c5a4405fab`、`0fb3e8cf96`、`32349fc25f`、`2a58d3e49e` | finish_noting 严格只收 reason；compact_parent 严格零参数；增加 D01、5 Turn、wrapper、审计与终止 Schema 回归断言 |

当前主会话无法获得仓库工作树执行环境：通过 GitHub 连接器完成了逐文件接口/控制流核对，但**没有实际运行 Python tests、ruff、health、DeepSeek、缓存抓包或 Dashboard**。因此这些提交是“待本地执行门禁的实现候选”，不是最终发布通过版本。

## 本地 Coding Agent 唯一接续点

拉取最新 `main` 后不要重新设计 M26–M28，也不要另开新的实现轮次。先阅读本索引、根 `CLAUDE.md`、`verification.md`、`validation.md`、`final-delivery.md`，然后按以下顺序继续：

1. 对最新 head 运行本轮新增/受影响的定向 Python 测试与冻结代码检查；若失败，只修真实失败及其受影响路径。
2. 完成 H6 独立 Verification，并把矩阵/证据写入本轮 `verification.md`；未通过则回到定向修复。
3. 按 C07/C09 用真实 DeepSeek Native 路径取得首请求、工具循环、continuation、Parent 并发时的完整父前缀和 provider cache-read 证据。
4. H6 通过后再做官方 Dashboard H7 Validation；真实用户输入到模型输出，不以 CLI/mock 代替。
5. 两门禁均关闭后更新 `final-delivery.md` 与根三文档，才允许把 V1.5 标记为整体 complete。

本轮未产生需要用户追认的新产品口径；静态 review 中补的 continuation wrapper 与 terminal 参数拒绝均直接落实现行 02 §5.6/§5.7 和 04 §4.6 的已冻结契约。
