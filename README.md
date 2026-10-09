# Hermes Secretary

Hermes Secretary 是基于 [Nous Research 的 Hermes Agent](https://github.com/NousResearch/hermes-agent) 的公开扩展项目，面向长期对话中的工作状态维护、责任跟进与提醒。

公开范围由 [V1 实施总纲](docs/01-personal-hermes-v1-first-fork-iteration.md) 定义，并包含通用 System Prompt 调优。Notebook / Noting 及相关基础能力以 [实现规格](docs/02-noting-system-specification.md) 为权威。V1.5 明确修订范围以 [V1.5 实施权威规格](docs/04-hermes-secretary-v1.5-implementation-spec.md) 为准，未修订 V1 契约继续有效。具体实施进展与当前任务统一记录在 [CLAUDE.md](CLAUDE.md)。

## 架构与能力范围

沿用 Hermes 的 Agent Turn、physical Session、Gateway、tool/runtime、原生压缩与状态持久化机制，在已确认接口上增量扩展。

项目最终部署形态为云端运行，通过官方 Dashboard Web UI 使用。Dashboard 对应浏览器 Web 界面（`web/` 与 `hermes_cli/web_server*.py`），沿用其现有 Hermes 对话运行路径。该部署口径与本地开发测试环境分开；实际部署与验收进度见 `CLAUDE.md`。

| 能力 | 公开规格约定 |
|---|---|
| Conversation Identity | Secretary-owned `conversation_ref` 作为稳定 ownership；physical Session、compression lineage 和 Gateway scope 作为 locator |
| History Search | 合格 Main 默认可用，按 canonical Message Identity 读取 History Foreground；跨压缩检索真实 User/Assistant/Tool/System 原文，独立于 Noting 开关 |
| Session Notebook | 每个 Conversation 的结构化 working state；完整 immutable Snapshot 与原子 current pointer；主 Assistant 只读 |
| Background Noting | V1.5规格：Idle/Force、持久Child与冻结Parent前缀；D01 最近实际请求 Native/External 来源门禁；普通finish_noting(reason)、特殊compact_parent正常结案，最多5 Turn，超限仍尝试提交有效Snapshot |
| Schedule / Reminder | Notebook-owned 调度；被动提醒在下一 eligible request 注入，主动提醒复用 Gateway admission，busy 时转为被动提醒 |
| Timestamp / Wrappers | 统一真实用户时间标记及 synthetic `role=user` wrapper 契约 |
| System Prompt 调优 | 围绕公开 Secretary 行为进行通用调优，具体实施口径见当前任务记录 |

Full Foreground 的首节点是唯一 Context Prelude，记录最新有效请求的实际 root System Prompt 与 Tool Schemas；不可观测部分明确标为 missing。其余节点按逻辑 Message Identity 投影，Snapshot 与 Anchor 作为审计附着，不增加消息节点。

V1.5 另外要求 Snapshot 结束记录（finish_noting含reason、compact_parent、forced）只进入内部审计元数据，日常notebook_show、/notebook和主Assistant读取不显示。**上述新规格当前尚未实施或完成验收。**

Conversation 原文是事实来源，Notebook 是派生工作状态。Secretary 持久化在原有 profile-scoped `state.db` 中增加自有表，不修改 Hermes 原有表的 schema 或 ownership。Notebook Schedule 与 Hermes Cron 的职责区分见实现规格。

## 对话中的 Secretary 命令

这些命令沿用 Hermes 共享 Slash catalog、补全和执行链路，在 CLI、Gateway 与官方 Dashboard Web UI 中使用。下表记录当前已实现入口；功能契约与用户确认的命令修订统一查阅 [1.5 实施索引](.autonomous/20261009-v1.5-implementation/index.md)，实现状态见 [CLAUDE.md](CLAUDE.md)。

| 命令 | 行为 |
|---|---|
| `/notebook` | 查看当前 Conversation 的 Notebook 与 Snapshot 创建时间；尚无 Snapshot 时明确提示 |
| `/noting on`、`/noting off` | 只修改当前 Conversation 的 Noting 参与状态；保留 Snapshot 与 Schedule 意图 |
| `/propose-persistence` | 核对 Notebook 的 Memory／Rule／Skill 候选及原文，向用户提出持久化草稿；可在命令后附普通自然语言 |

全局 Noting 开启时，local off 仍允许人类查看已有 Notebook 和提议已有候选；全局关闭时这两项命令不可用。提议本身不执行持久化，由主 Assistant 使用 History Search 自主核查候选来源、周边和后续反证；后续由用户以自然语言明确批准执行、修改或否决，修改不是执行批准，获批操作使用 Hermes 已有能力。 `/noting on` 会验证当前模型的实际上下文能力及原生 Idle 配置；无法启用时给出具体指导，不写入虚假的开启状态。旧 `/notebook on/off` 不再作为控制入口或别名；`/noting` 的反馈进入普通对话记录，不启动模型 Turn。旧 `/refine` 已移除，独立工作审查 `/review` 保留。

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
├── hermes_state*.py           # SessionDB 与 Secretary 自有状态表
├── secretary/                 # Notebook、Noting 与 Schedule/Reminder 服务模块
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

开发测试期间，前端与后端均在本机 localhost 运行；浏览器验收访问本地 Web UI。最终云端部署形态不改变本地开发测试口径。

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

本地官方 Dashboard Web UI 入口为 `hermes dashboard --host 127.0.0.1 --no-open`，默认端口 9119。直接调用源码的子命令入口是 `.venv/bin/python -m hermes_cli.main dashboard ...`；`cli.py` 是交互对话入口。

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
| 首轮状态记录 | 实际交付、独立审查、未验收范围与移交项 | [.autonomous/20261007-v1-first-implementation/final-delivery.md](.autonomous/20261007-v1-first-implementation/final-delivery.md) |
| V1.5 实施权威规格 | 增量修订与继承矩阵、Foreground、Prompt/工具门禁、提案和验收；§4.5 D01定稿唯一Native/External执行来源门禁，§4.6–§4.7定稿多Turn终止与审计 | [docs/04-hermes-secretary-v1.5-implementation-spec.md](docs/04-hermes-secretary-v1.5-implementation-spec.md) |
| 1.5 实施冻结索引 | 本次自主实施的四类依据、授权口径与冻结权限 | [.autonomous/20261009-v1.5-implementation/index.md](.autonomous/20261009-v1.5-implementation/index.md) |
| 1.5 文档准备快照 | 补充调整的需求来源、文档权限与确认口径 | [.autonomous/20261008-v1.5-adjustment-and-acceptance/index.md](.autonomous/20261008-v1.5-adjustment-and-acceptance/index.md) |
| 上游贡献指南 | 运行及测试环境准备、现有检查命令的参考，不引入上游协作流程 | [CONTRIBUTING.md](CONTRIBUTING.md) |
| PM 参考 | 开发激活、依赖及隔离环境管理 | [website/docs/reference/package-management.md](website/docs/reference/package-management.md) |
| Hermes 架构 | Agent、Gateway、工具与状态层的架构说明 | [website/docs/developer-guide/architecture.md](website/docs/developer-guide/architecture.md) |
| 上游测试参考 | canonical runner、测试布局、隔离与行为契约的实现背景 | [tests/AGENTS.md](tests/AGENTS.md) |
| 安全策略 | 继承的安全边界和报告规范 | [SECURITY.md](SECURITY.md) |

Secretary 专项规格放在 `docs/`；继承的 Hermes 文档保留在 `website/docs/`。规格权威与当前任务分别按 01 / 02 和 `CLAUDE.md` 的职责查阅。

## 许可证与致谢

保留上游 [MIT License](LICENSE)。Hermes Agent 由 Nous Research 构建；本项目在其基础上进行增量扩展。原始上游文档与代码可在官方仓库或本仓库 `hermes-upstream` 分支查看。
