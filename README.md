# Hermes Secretary

Hermes Secretary 是基于 [Nous Research 的 Hermes Agent](https://github.com/NousResearch/hermes-agent) 的公开扩展项目，面向长期对话中的工作状态维护、责任跟进与提醒。

公开范围由 [V1 实施总纲](docs/01-personal-hermes-v1-first-fork-iteration.md) 定义，并包含通用 System Prompt 调优。Notebook / Noting 及相关基础能力以 [实现规格](docs/02-noting-system-specification.md) 为权威。具体实施进展与当前任务统一记录在 [CLAUDE.md](CLAUDE.md)。

## 架构与能力范围

沿用 Hermes 的 Agent Turn、physical Session、Gateway、tool/runtime、原生压缩与状态持久化机制，在已确认接口上增量扩展。

| 能力 | 公开规格约定 |
|---|---|
| Conversation Identity | Secretary-owned `conversation_ref` 作为稳定 ownership；physical Session、compression lineage 和 Gateway scope 作为 locator |
| History Search | 读取 History Foreground，跨有效压缩延续检索真实原文，独立于 Noting 开关 |
| Session Notebook | 每个 Conversation 的结构化 working state；完整 immutable Snapshot 与原子 current pointer；主 Assistant 只读 |
| Background Noting | Idle / Force Trigger、persistent Hermes child、Parent cache parity、受限写入工具与 commit-time Anchor 校验 |
| Schedule / Reminder | Notebook-owned 调度；被动提醒在下一 eligible request 注入，主动提醒复用 Gateway admission，busy 时转为被动提醒 |
| Timestamp / Wrappers | 统一真实用户时间标记及 synthetic `role=user` wrapper 契约 |
| System Prompt 调优 | 围绕公开 Secretary 行为进行通用调优，具体实施口径见当前任务记录 |

Conversation 原文是事实来源，Notebook 是派生工作状态。Secretary 持久化在原有 profile-scoped `state.db` 中增加自有表，不修改 Hermes 原有表的 schema 或 ownership。Notebook Schedule 与 Hermes Cron 的职责区分见实现规格。

## 仓库与分支

| 入口 | 用途 |
|---|---|
| [`EdgarZhong/hermes-secretary`](https://github.com/EdgarZhong/hermes-secretary) / `origin` | 本项目 GitHub 仓库 |
| `main` | 默认分支，首轮直接开发公开 Hermes Secretary 的分支与发布基线；三份核心文档按本项目规则维护 |
| [`NousResearch/hermes-agent`](https://github.com/NousResearch/hermes-agent) / `upstream` | 官方 Hermes 上游 |
| `hermes-upstream` | 官方 `main` 的独立镜像分支，跟踪 `upstream/main`，代码和文档保持上游原样，不用于开发 |

获取上游变化使用 `git fetch upstream main`；是否推进镜像分支及集成到公开 `main`，按 [协作规则中的上游同步与文档保护 SOP](AGENTS.md) 审查后执行。上游合并不得覆盖开发分支的三份核心文档，需保留本项目版本并人工吸收适用变化。Git remote 是本地配置，新 clone 如需同步官方上游，先运行：

```bash
git remote add upstream https://github.com/NousResearch/hermes-agent.git
git fetch upstream main
```

## 目录结构

```text
hermes-secretary/
├── README.md                  # 稳定事实、环境与文档入口
├── AGENTS.md                  # 通用规则、协作边界与开发测试 SOP
├── CLAUDE.md                  # 当前目标、任务与动态状态
├── docs/                      # Secretary 现行专项规格
├── run_agent.py、agent/        # Agent facade、Turn、prompt、压缩与模型调用
├── hermes_state*.py           # SessionDB 与状态持久化模块
├── cli.py、hermes_cli/         # CLI、配置、插件加载与服务入口
├── gateway/                   # 消息 ingress、路由与会话 admission
├── tools/、plugins/、skills/   # 工具及能力扩展
├── cron/                      # Hermes 原生 Cron
├── tui_gateway/、ui-tui/       # JSON-RPC backend 与终端 UI
├── apps/desktop/、web/         # 桌面应用与管理界面
├── pm/、hermes_platform/       # 依赖环境管理与平台能力
├── tests/、tests-js/           # Python 与 JavaScript 测试
├── scripts/                   # 测试、检查与开发辅助入口
└── website/docs/              # 继承的 Hermes 使用、开发及参考文档
```

## 运行与开发环境

开发运行目标为 Python 3.14，由 Hermes PM 提供固定版本解释器和依赖。`pyproject.toml` 对较旧 Python 的声明兼容范围用于上游更新路径，不表示旧版本是开发运行目标。Git、Git LFS 和 Node.js 要求见 [CONTRIBUTING.md](CONTRIBUTING.md)；Node 接受版本以 `package.json` 为准。

本项目保留 Hermes PM、锁文件及源码激活方式。先按 [PM developer workflow](website/docs/reference/package-management.md#developer-workflow) 选择隔离的开发 `HERMES_HOME` / runtime，避免测试迁移真实用户状态，再在仓库根目录激活：

```bash
export HERMES_HOME="$PWD/.hermes-dev"
export HERMES_RUNTIME_DIR="$HERMES_HOME/tools"
source ./activate
hermes --version
hermes setup
hermes
```

激活可能准备或同步运行依赖，不会安装全部 JS workspace。Gateway 入口为 `hermes gateway`；详细使用方式见继承的 [Gateway 文档](website/docs/user-guide/messaging/index.md)。源码开发不使用官方安装脚本替代当前 checkout。

## 代码规范与测试入口

通用规则与闭环流程以 [AGENTS.md](AGENTS.md) 的冻结约定为准。分区 `AGENTS.md` 和上游贡献指南供架构、接口及环境参考，不自动增加项目约束。沿用已确认的 Hermes facade / sibling 结构、profile isolation、prompt-cache 约束、依赖锁定和代码检查；核心文档不设字数 / 行数硬门槛。

测试使用独立环境，按 [Development Setup](CONTRIBUTING.md#development-setup) 和 PM 文档准备。使用已准备的项目解释器构建全新测试环境：

```bash
python -m pm.build_env --source . --out .venv --group dev --group test
scripts/run_tests.sh tests/<相关测试文件>.py
python scripts/check
```

`.venv` 目标必须尚不存在；测试 runner 自动发现仓库测试环境。完整 Python suite 使用 `scripts/run_tests.sh`，不直接绕过 runner 调用 pytest。JS / UI 检查使用对应 workspace 及 [CONTRIBUTING.md](CONTRIBUTING.md) 的入口。

`.venv/` 与 `.hermes-dev/` 不进入版本控制。PM 底层使用 UV，环境依赖按官方现有锁文件安装，不迁移包管理方式。

本项目不运行 GitHub CI / CD；GitHub Actions 关闭，质量门禁在本地执行。日常只选择相关检查及小范围回归；集成收敛后，主会话派生独立 Verification / Validation，在交付前统一安排一次必要扩大测试，共享同版本证据，避免重复的时间和上下文开销。具体范围、门禁职责和复测约束见 [本地 CI / CD 与回归防护](AGENTS.md)。

```bash
.venv/bin/python scripts/check --staged --only <相关检查>
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/<相关分区>/
# 以下入口仅在交付前唯一一次扩大测试中按实际影响选择：
.venv/bin/python scripts/check --staged
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh
# 修改相应前端时，在官方 PM 准备的 Node / npm 环境中运行：
npm run --workspace web check
npm run --workspace ui-tui check
npm run --workspace apps/desktop check
```

根目录三份核心文档不做递归扩展；现有分区文档非必要不修改。所有任务看板和动态进度只记录在根 `CLAUDE.md`。

## 重要文档索引

| 文档 | 内容 | 路径 |
|---|---|---|
| V1 实施总纲 | 公开首轮目标、边界、依赖顺序与完成定义 | [docs/01-personal-hermes-v1-first-fork-iteration.md](docs/01-personal-hermes-v1-first-fork-iteration.md) |
| Notebook / Noting 实现规格 | Identity、History、Notebook、Noting、Schedule、Reminder 的权威契约 | [docs/02-noting-system-specification.md](docs/02-noting-system-specification.md) |
| 协作规则 | 用户规则、冻结约定、上游干扰隔离、文档保护和开发测试 SOP | [AGENTS.md](AGENTS.md) |
| 当前阶段 | 当前目标、任务看板、已确认口径和验证状态 | [CLAUDE.md](CLAUDE.md) |
| 上游贡献指南 | 运行及测试环境准备、现有检查命令的参考，不引入上游协作流程 | [CONTRIBUTING.md](CONTRIBUTING.md) |
| PM 参考 | 开发激活、依赖及隔离环境管理 | [website/docs/reference/package-management.md](website/docs/reference/package-management.md) |
| Hermes 架构 | Agent、Gateway、工具与状态层的架构说明 | [website/docs/developer-guide/architecture.md](website/docs/developer-guide/architecture.md) |
| 上游测试参考 | canonical runner、测试布局、隔离与行为契约的实现背景 | [tests/AGENTS.md](tests/AGENTS.md) |
| 安全策略 | 继承的安全边界和报告规范 | [SECURITY.md](SECURITY.md) |

Secretary 专项规格放在 `docs/`；继承的 Hermes 文档保留在 `website/docs/`。规格权威与当前任务分别按 01 / 02 和 `CLAUDE.md` 的职责查阅。

## 许可证与致谢

保留上游 [MIT License](LICENSE)。Hermes Agent 由 Nous Research 构建；本项目在其基础上进行增量扩展。原始上游文档与代码可在官方仓库或本仓库 `hermes-upstream` 分支查看。
