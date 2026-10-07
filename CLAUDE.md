# 当前阶段与任务同步

## 当前目标

截至 2026-10-07，当前阶段为公开项目仓库初始化：以官方 Hermes `main` 为代码基线，保留工作区现有 01 / 02 规格，建立 GitHub 仓库和独立上游分支，并按文档职责重写三份核心文档。本轮不实施功能代码。

## 已确认口径

- 公开 Hermes Secretary = 工作区 01 的首轮范围 + System Prompt 调优；02 是核心能力实现的权威规格。
- 先完成公开核心，后续个人化改造使用个人分支，与公开发布范围隔离。
- 个人分支无需私有可见性；敏感凭据绝不提交或上传云端。
- 首轮 focus on `main`，直接在 `main` 演进；当前不创建个人分支。
- `main` 的三份核心文档按用户全局规则维护；`hermes-upstream` 不用于开发，保留上游代码和文档原样。以后合并上游不得覆盖开发分支的三份核心文档，按 `AGENTS.md` 的保护 SOP 执行。
- GitHub 简介面向公开用户，只介绍 Hermes Secretary，不包含个人后续改造计划。
- 下载目录旧版 01 和 03 已阅读，仅用来识别后续个人化范围；不复制进公开仓库，不作为本轮公开实现或验收依据。
- System Prompt 调优属于公开范围，但具体目标、接线点与验收口径尚待确认。
- 工作区 `.venv` 使用官方 PM 创建，包含 `dev` / `test` groups，按官方解释器与现有锁文件安装；不迁移管理方式，不改变全局 Python，也不改写锁文件。

## 当前任务看板

| 任务 | 状态 | 完成条件 |
|---|---|---|
| 理解现行 01 与旧版 01 / 03 的边界 | 已完成 | 确认公开核心与个人化范围，现行 02 保持权威 |
| 记录范围隔离与协作规则 | 已完成 | `AGENTS.md` 写入确认口径与全局规则 |
| 拉取官方 Hermes 基线 | 已完成 | 基线 `70dcdd640f0da6dd57c2ff362bf3a06cb837b885`，保留官方历史 |
| 创建公开 GitHub 仓库与简介 | 已完成 | `EdgarZhong/hermes-secretary` 为公开 Fork，默认 `main`，简介只描述公开项目 |
| 建立 `main` 与纯上游分支 | 本地已完成 | `hermes-upstream` 跟踪 `upstream/main`，待核实远端 |
| 重写三份核心文档 | 已完成 | 文档职责、开发分支、上游文档保护 SOP 及稳定索引已核对 |
| 创建工作区 `.venv` | 已完成 | 官方 PM 创建 Python 3.14.7 环境，安装 `dev` / `test`；官方锁文件未变 |
| 审查并提交、推送初始化内容 | 进行中 | 文档与环境检查通过，待集成 Fork 创建时新增的上游提交并推送 |

## 后续公开实施队列

以下是待实施的 Secretary 工作，不表示已有功能：

1. Conversation Ref / Identity Registry 与 History Foreground / History Search。
2. Notebook immutable Snapshot、current pointer、只读主会话工具与 Slash Command。
3. Noting runtime、Idle / Force Trigger、cache parity、Anchor admission 与 commit gate。
4. Notebook Schedule、passive System Reminder、active User Reminder 与 busy fallback。
5. Timestamp / wrapper contract、关闭行为回归、并发与失败路径、最小 Frontend / API 接线。
6. System Prompt 调优：先确认范围与验收，再实施。

正式实现前重新核对官方基线的符号和接线点；依赖顺序与正确性要求以 02 为准。

## 编排、风险与交付条件

- 本阶段由主会话直接执行，未启用子 Agent 或 worktree。
- 修改范围：Git 配置、GitHub 仓库元数据、三份核心文档、必要的仓库忽略规则及本地开发环境；不修改功能代码，不改写现有 01 / 02 正文或官方锁文件。
- 风险：旧版文档中的 Schedule、busy queue、Noting 设计不可覆盖当前 02；公开分支均可见，不承载敏感凭据。
- 初始化完成定义：官方代码历史保留，现有规格保留，公开 GitHub 默认 `main` 已推送，纯上游分支存在，简介及三份核心文档符合已确认口径。
- 验证范围：文档、Git 差异、基线一致性、远端默认分支与简介；本阶段不宣称 Secretary 功能已实现或上游测试已通过。

## 已完成验证

- 官方 PM 成功创建 `.venv`；解释器为 Python 3.14.7，来源与 `pm/lock.json` 的 `3.14.7+20260901` 固定版本一致。
- 当前平台适用的 36 项 core 依赖均满足官方 `pyproject.toml`；`dev` / `test` groups 已安装。
- 官方 Python / PM 锁文件及依赖定义未变；`.venv/`、`.hermes-dev/` 和 `.DS_Store` 均被忽略。
- 三份核心文档本地链接有效，`git diff --check` 与上游 `check_agents_md_size.py` 通过。
- 工作区 01 / 02 与初始化前 SHA-256 相同，下载目录旧稿未复制到仓库。
- Fork 创建时官方新增 10 个提交，增量只涉及 Cron / Gateway 及相关测试，不涉及核心文档或锁文件；按上游文档保护 SOP 集成。
