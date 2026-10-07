# 协作规则

## 用户规则

- 永远用中文答复用户；项目 `AGENTS.md`、`CLAUDE.md` 使用中文。
- 执行前先了解足够信息。需求存在影响范围或结果的歧义时，先询问、给出建议，经用户确认后再执行。
- 修改代码或运行命令前，先说明意图，便于用户监控。
- 每个新会话至少先阅读本文件和 `CLAUDE.md`，再按 `README.md` 的文档索引查阅规格。
- 非用户要求，不读取 `docs/archived/`。

## 公开范围与个人化隔离

- `main` 是首轮唯一的功能开发分支，也是对外公开 Hermes Secretary 的发布基线；直接在 `main` 演进。公开范围以工作区 `docs/01-personal-hermes-v1-first-fork-iteration.md` 的首轮范围为基础，加上 System Prompt 调优。
- Notebook、Noting、Conversation Identity、History Search、Schedule、Reminder 的实现细节以 `docs/02-noting-system-specification.md` 为权威；旧稿不能覆盖现行规格。
- 公开项目的通用 System Prompt 调优与个人 Persona、Character、专属规则注入必须区分；调优的具体目标、修改位置及验收口径需在实施前确认。
- 下载目录旧版同名 01 中超出当前公开范围的改造，以及 03 路线文档中的改造，属于后续个人化范围。不得把这些旧稿引入公开首轮的实现依赖或验收依据。
- 个人化改造包括 NM Provider、Recall Bridge、个人部署及触达集成，以及后续 Memory Governance / Dreaming、RSI 增强、跨渠道连续性和 Remote Mac 等；使用独立个人分支，不直接进入 `main` 的对外发布范围。
- “个人分支”表示不对外发布，不要求 GitHub 私有可见性。公开仓库中的个人分支仍可被外部访问，不依赖分支名称实现保密。
- 个人分支基于公开核心维护；合并回 `main` 前必须单独确认公开范围并审查个人化内容。新增个人依赖、个人配置、个人背景或个人专属行为，不得默认成为公开核心要求。
- 敏感凭据不得进入 Git 历史或上传云端。密钥、令牌及带凭据的运行配置保留在本地或运行环境；示例仅使用占位符。提交前检查差异与待跟踪文件。
- `upstream` 指向 Hermes 官方仓库；`hermes-upstream` 跟踪官方 `upstream/main`，保持纯上游内容，不提交 Secretary 或个人化修改。同步到 `main` 前先审查上游变化。

## 核心文档职责

- `README.md`：只记录已落实的稳定事实与稳定入口，包括项目定位、架构、目录骨架、运行环境、开发命令、重要文档索引和测试入口。
- `AGENTS.md`：只记录通用规则、流程、原则、协作边界、工作区约定和验收要求；不记录项目长期背景叙述或动态任务状态。
- `CLAUDE.md`：记录当前目标、任务看板、进度、阶段决策、Agent 编排、修改范围、依赖、风险、启动条件和完成定义。
- 专项规格、专项 SOP、调试接口和测试用例说明存入 `docs/`；稳定入口补入 `README.md`。
- 非必要不创建新文档，优先更新三份核心文档或已有规格。
- 用户确认的口径立即写入对应文档；随实现和集成持续维护三份核心文档，移除过时表述。
- `main` 的三份核心文档按本文件中的用户全局规则撰写和持续维护，属于本项目自有文档；后续个人开发分支同样遵守文档分工，并维护该分支自己的动态状态。
- `hermes-upstream` 是纯上游镜像，不用于开发；其中三份核心文档若存在，保留上游原样，不应用本项目重写。

## 上游同步与核心文档保护 SOP

- 合并上游不得覆盖 `main` 或个人开发分支的 `README.md`、`AGENTS.md`、`CLAUDE.md`，即使 Git 判定没有冲突，也必须保护本项目版本。
- 开始前工作区保持干净，记录当前提交并阅读三份核心文档。先 `git fetch upstream main`，审查目标基线、接口、依赖和规则变化；纯镜像分支只允许快进到已审查上游提交。
- 在目标开发分支用 `git merge --no-ff --no-commit <已审查上游提交>` 合并，不允许直接快进或自动提交而绕过文档保护。出现冲突时停留在合并状态，按差异人工处理。
- 在创建 merge commit 前，执行以下恢复操作；未提交合并时 `HEAD` 仍是合并前的本项目提交，因此这也保护上游单侧更新、自动合并以及冲突路径：

  ```bash
  git restore --source=HEAD --staged --worktree -- README.md AGENTS.md CLAUDE.md
  ```

- 随后只人工吸收必要且适用的上游事实或规则，按三份文档职责编排；本项目公开边界、用户规则和当前进展必须保留。核对 staged diff、测试与文档后，才能提交合并。
- 不使用整文件 `checkout --theirs`、整树覆盖、自动同步脚本或机器人替换这些文档；其他集成方式（cherry-pick、rebase、补丁应用等）也必须满足同样的保护要求。
- Git merge driver 或“没有冲突”不能代替此 SOP：单侧变化和快进可能不触发自定义 driver。

## 实现与代码规范

- Hermes-first、复用优先、增量改造；遵循现有模块边界、公共接口、命名与代码风格。
- 保护每个 Conversation 的 prompt-cache prefix：不得在会话中途随意改写历史、切换工具面、重载记忆或重建 root System Prompt；压缩及已冻结的 Noting cache-parity 机制遵循各自契约。
- 原有 facade / sibling 模块结构继续有效：行为放入对应 sibling，保持 facade 公共入口；避免模块级循环导入，在生产代码实际读取的接线点进行 patch。
- 用户状态路径通过 `get_hermes_home()` 等 profile-aware helper 获取，不硬编码 `~/.hermes`；后台任务、tick、RPC、线程及子进程必须显式绑定所属 profile，不能使用启动 profile 代替目标 profile。
- 机器事实及可执行文件解析使用 `hermes_platform`；非凭据的行为配置进入配置系统，不任意新增环境变量控制功能。
- Core patch 必须位于已确认接线点；不得随手新增平行 Agent Loop、对话存储、主会话 admission gate、通用调度器或 API hierarchy。
- Secretary 的持久状态只向已有 `state.db` 增加自有表，不改变 Hermes 原有表的 schema 或 ownership 语义。
- 对话原文是事实源；Notebook 是派生工作状态。主 Assistant 只读 Notebook，写入权限仅属于 Noting。
- 实现必须覆盖正式接线、状态转换、失败处理和规格要求的关闭行为，不能用孤立 helper 代替实际可用链路。
- 本次规格未冻结的接口或产品行为，先完成口径确认再实现，不从旧版文档猜测。

## 开发测试闭环 SOP

1. 阅读 `AGENTS.md`、`CLAUDE.md` 和相关现行规格，确认任务范围、依赖及完成定义。
2. 检查工作区、分支、上游基线与已有未提交修改；不得覆盖其他人的工作。
3. 在 `CLAUDE.md` 更新任务状态和必要编排；说明意图后执行修改。
4. 采用最小相关测试验证正确性，并完成相关接线、回归和失败路径检查；真实验收需求使用对应验收流程。
5. 亲自审查变更、规格覆盖和证据缺口；检查待提交文件是否包含凭据或个人化内容。
6. 更新三份核心文档及必要规格，使稳定事实、动态状态和规则各归其位。
7. 交付时说明完成内容、验证结果、未完成项及实际限制；未经授权不扩大实现或发布范围。

- Python 测试统一使用 `scripts/run_tests.sh`，不绕过 runner 直接调用 pytest；检查入口是 `python scripts/check`。具体环境准备见 `CONTRIBUTING.md`。
- 测试使用隔离的 `HERMES_HOME` / runtime，不写入用户真实 Hermes 状态；跨平台行为在对应平台验证，不伪造 `sys.platform`。
- 修复验证行为契约和实际失败路径，避免读取源码断言、镜像实现或仅证明代码变化的测试；纯文档修改以差异、链接、职责和规格一致性检查为主。

## 分区规则阅读入口

修改相应区域前阅读其规则；更深层 `AGENTS.md` 同样适用，用户已确认口径优先。

| 修改区域 | 规则入口 |
|---|---|
| `run_agent.py`、`agent/` | `agent/AGENTS.md` |
| `cli.py`、`hermes_cli/` | `hermes_cli/AGENTS.md` |
| `gateway/` | `gateway/AGENTS.md` |
| `tools/`、`toolsets.py`、`model_tools.py` | `tools/AGENTS.md` |
| `plugins/` | `plugins/AGENTS.md` |
| `tui_gateway/`、`ui-tui/` | `tui_gateway/AGENTS.md` |
| `web/` | `web/AGENTS.md` |
| `apps/desktop/` | `apps/desktop/AGENTS.md`、`apps/desktop/src/AGENTS.md` |
| `skills/`、`optional-skills/`、Curator | `skills/AGENTS.md` |
| `cron/` | `cron/AGENTS.md` |
| `tests/` | `tests/AGENTS.md` |
| `pm/`、依赖定义 | `pm/AGENTS.md` |
| `hermes_platform/` | `hermes_platform/AGENTS.md` |

## Subagent 与工作区

- 主会话负责全局目标、覆盖、编排、亲自 review、接线集成、微小明确的集成修补和最终判定。
- 独立且边界明确的实现或研究可委派；过小、边界不清或需要连续决策的任务由主会话直接处理。
- 委派必须给出目标、依据、输入、修改白名单、接口、依赖、完成判据和验证方式；默认显式使用 `gpt-6.1-sol` / `high`，用户指定优先。
- 子 Agent 不再派生。并行修改范围须不相交或有效隔离；非必要不用 worktree，必要时平铺到仓库父目录。
- 主会话亲自 review 返回变更，不以复跑子 Agent 测试代替审查，复核后才接收报告。
- 用户要求大型任务“自主执行”或“开始一轮自主实现”时使用 `autonomous-run` 套件；完整编排、冻结、独立门禁、阅读契约和交付判定以套件为准。
- 自主运行默认包含任务范围内的本地阶段提交权限；阶段快照需准确记录已验证范围与未完成项。

## 依赖与本地配置

- 安装依赖优先使用 Homebrew、mise、nvm、uv；具体代码库的 Python 依赖使用项目级 uv / 虚拟环境，不使用 `sudo pip`。
- 本仓库继承 Hermes 的 PM 与锁文件管理：使用 `activate` / `hermes pm` 和 PM 构建的隔离环境，不以裸 pip / uv 修改 PM 管理的环境。默认全局 Python 不因项目运行目标而改变。
- 工作区 `.venv` 按官方 PM 的 `pm.build_env` 创建，使用官方解释器和现有锁文件，纳入 `dev` / `test` groups；不迁移环境管理方式，不重解析或改写锁文件。开发运行状态可放入已忽略的 `.hermes-dev/`，不得提交运行数据或凭据。
- 依赖修改遵循 `pyproject.toml` / `uv.lock` 的固定版本及边界策略，Git 依赖和 Actions 固定到 commit；变更后执行 `hermes pm lock` 并提交锁文件。
- 用户配置文件与项目配置分开；用户配置本体放在 `~/dotfiles`，通过其 `sync-links.sh` 同步链接，不把个人配置复制到公开项目。
- Nowledge Mem 不默认启用；仅在用户明确要求或需要跨工具历史上下文时按需只读查询，不写入。工作区内的“记住”默认落入相应项目文档。
