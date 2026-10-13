# Hermes Secretary

Hermes Secretary 是基于 [Nous Research 的 Hermes Agent](https://github.com/NousResearch/hermes-agent) 的公开扩展，面向长期对话中的工作状态维护、责任跟进与提醒。

继承的 Secretary Core 契约以 [现行 02](docs/02-noting-system-specification.md)（含 V1.6 已确认修订）为先，再继承 [04](docs/04-hermes-secretary-v1.5-implementation-spec.md) 未被覆盖的增量和 [01](docs/01-personal-hermes-v1-first-fork-iteration.md) 的适用要求。[Web UI V1 规格](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md) 是显式 Web 增量的权威入口，替代旧 UI 讨论；独立前端入口见下文；实现不等于整版验收通过。通用协作规则见 [AGENTS.md](AGENTS.md)，实施进展、任务与验收结果见 [CLAUDE.md](CLAUDE.md)。

## 架构与能力

沿用 Hermes 的 Agent Turn、physical Session、Gateway、原生工具、压缩与持久化，在既有接缝增量扩展。Conversation 原文是事实源，Notebook 是派生工作状态；Secretary 只向 profile-scoped `state.db` 增加自有表，不改原有表的 schema 或 ownership。现有官方 Dashboard（`web/` 与 `hermes_cli/web_server*.py`）仍是原生浏览器管理入口，独立 Secretary Web UI 的契约见 06。

| 能力 | 已落实的核心机制 |
|---|---|
| Conversation Identity | `conversation_ref` 为稳定 ownership；physical Session、compression lineage 和 Gateway scope 为 locator |
| History Search | 按 canonical Message Identity 读取真实 History Foreground，独立于 Noting 开关 |
| Notebook | Snapshot 保存有序不可变 item 版本 id，以原子 current pointer 发布；Main 只读，Noting 用 manage/edit/schedule 三工具维护 |
| Background Noting | 原生 Main 生命周期与 Idle 定时器、Force/catch-up；D01 实际 Native/External 来源门禁；冻结父前缀，最多五 Turn 与 context_overflow 收尾 |
| Noting Memo | add/replace/delete/list；非空保持本会话 Noting 开启；提交同事务消费实际处理的条目，期间新增或替换内容保留 |
| Schedule / Reminder | Notebook-owned 调度；deferred 批量投递并在实际携带且 Provider 成功响应后 ACK；instant 复用原生用户消息入口 |
| 时间与消息载体 | 可读带时区绝对时间，以及 timestamp、Framework、Instant/Deferred Reminder 的真实载体契约 |
| Full Foreground | 内部逻辑审计投影：唯一 Context Prelude、真实消息节点与 Anchor/Snapshot 附着；Web 全量审计视图按 06 延后 |

实现不等于整版验收通过；对应版本证据和未关闭项统一见当前看板及历史报告。

## Secretary Slash 入口

命令复用 Hermes 共享 catalog、补全与执行链路；既有 CLI、Gateway、官方 Dashboard 入口的契约以 02 为准，新 Web 的显式差异以 06 为准。

| 命令 | 行为 |
|---|---|
| `/notebook` | 查看当前 Conversation 的 Notebook 与 Snapshot 创建时间；无 Snapshot 时明确提示 |
| `/noting on`、`/noting off` | 修改当前 Conversation 的参与状态；保留 Snapshot/Schedule；memo 非空时 off 拒绝并说明原因 |
| `/propose-persistence` | 查核候选及原文，提出持久化草稿，可附自然语言；提议与修改均不等于执行批准 |

全局关闭时 Notebook/候选命令不可用；全局开启且 local off 时仍可查看或提议已有内容。获用户明确批准后使用 Hermes 既有能力执行持久化。旧 `/notebook on/off`、`/refine` 已移除；独立工作审查 `/review` 保留。

## 仓库与目录

| 入口 | 用途 |
|---|---|
| [EdgarZhong/hermes-secretary](https://github.com/EdgarZhong/hermes-secretary) / `origin` | 本项目仓库；`main` 为公开核心开发与发布基线 |
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) / `upstream` | Hermes 官方上游 |
| `hermes-upstream` | 纯官方 `upstream/main` 镜像，不用于项目开发 |

上游同步执行 [文档保护 SOP](AGENTS.md#上游同步与核心文档保护-sop)。新 clone 如需官方上游，添加 `upstream` 后 fetch，先审查再集成。

```text
hermes-secretary/
├── README.md / AGENTS.md / CLAUDE.md  # 稳定入口 / 通用规则 / 动态看板
├── docs/、.autonomous/               # 专项规格 / 自主轮次依据与报告
├── run_agent.py、agent/              # Agent facade、Turn、prompt、压缩与模型调用
├── hermes_state*.py、secretary/       # SessionDB、Secretary 自有表与核心服务
├── cli.py、hermes_cli/、gateway/      # CLI、Dashboard、消息 ingress 与路由
├── tools/、plugins/、skills/、cron/   # 工具、扩展与原生 Cron
├── tui_gateway/、ui-tui/              # JSON-RPC backend 与终端 UI
├── apps/desktop/、web/               # 原生桌面应用与官方 Dashboard
├── pm/、hermes_platform/             # 官方依赖环境与平台能力
├── tests/、tests-js/、scripts/        # 测试、检查与辅助入口
└── website/docs/                    # 继承的 Hermes 使用与开发参考
```

## 运行与开发环境

本地开发与浏览器验收使用 localhost、隔离 `HERMES_HOME` / runtime。开发 Python 3.14 由 Hermes PM 提供；依赖按官方锁文件管理，不迁移 PM 或改全局 Python。Git、Git LFS、Node.js 与 JS workspace 环境见 [CONTRIBUTING.md](CONTRIBUTING.md) 和 `package.json`。

按 [PM developer workflow](website/docs/reference/package-management.md#developer-workflow) 准备环境，在源码根目录激活：

```bash
export HERMES_HOME="$PWD/.hermes-dev"
export HERMES_RUNTIME_DIR="$HERMES_HOME/tools"
source ./activate
hermes --version
hermes setup
hermes
```

Gateway 入口为 `hermes gateway`。官方 Dashboard 入口为 `hermes dashboard --host 127.0.0.1 --no-open`，默认端口 9119；源码子命令为 `.venv/bin/python -m hermes_cli.main dashboard ...`。激活不自动安装全部 JS workspace；不以官方安装脚本替代当前 checkout。

## 独立 Secretary Web 开发入口

独立前端在并列本地仓库 `../hermes-secretary-web`，使用 React / TypeScript / Vite，直接调用原生 REST / WS；开发服务默认连接 `http://127.0.0.1:53445`。部署范围及验收进度见 CLAUDE，不替代官方 Dashboard。

当前草稿全部附件合计上限为 500,000,000 bytes，选择时累计判断、移除后释放预算，发送时沿原生 `file.attach` 分片上传并显式绑定本次图片。两个订阅同一会话的客户端共享原生实时事件；普通 Send 只在 Main Turn 空闲时启动新 Turn，活动时按既定 Steer/Stop/Interrupt 操作。

在前端目录执行 `npm ci` 后，`npm run dev` 启动正式接线页面；`npm run typecheck`、`npm test`、`npm run build` 为类型、定向测试与构建入口。静态交互工作台使用 `npm run mock -- --port 5176`，访问 `/mock.html`；可选择场景、主题与四种视口，不连接真实后端或调用模型。`npm run mock:test` 和 `npm run mock:build` 分别验证、构建静态工作台。场景与组件边界见 [Mock 交接说明](.autonomous/20261012-round2-web-ui/static-mock.md)。

## 代码规范与测试入口

代码遵循 [AGENTS.md](AGENTS.md) 的 Hermes-first、原生兼容、facade/sibling、prompt-cache、profile 隔离与冻结检查约束。上游分区文档只作架构和环境参考。

```bash
# 按官方 PM 创建全新环境；目标 .venv 必须尚不存在
python -m pm.build_env --source . --out .venv --group dev --group test
# 日常按变化选择分区与相关检查
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/<相关测试文件>.py
.venv/bin/python scripts/check --staged --only <相关检查>
# 集成收敛后按实际影响统一安排扩大检查，复用同版本有效证据
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh
.venv/bin/python scripts/check --staged
# 修改对应 workspace 时使用其官方入口
npm run --workspace web check
npm run --workspace ui-tui check
npm run --workspace apps/desktop check
```

Python 不绕过 canonical runner 直接运行 pytest；JS/UI 入口及环境准备见 [Development Setup](CONTRIBUTING.md#development-setup)。`.venv/`、`.hermes-dev/` 不入版本控制。GitHub Actions 保持关闭，质量门禁在本地执行；测试范围、独立门禁与证据复用流程见 AGENTS。

## 重要文档索引

| 文档 | 内容 | 路径 |
|---|---|---|
| V1 实施总纲 | 公开核心范围、边界与继承要求 | [01](docs/01-personal-hermes-v1-first-fork-iteration.md) |
| Notebook / Noting 现行规格 | Identity、History、Notebook、Noting、Schedule、Reminder，含 V1.6 修订与 §5.12 Target | [02](docs/02-noting-system-specification.md) |
| V1.5 增量规格 | 未被现行 02 覆盖的增量契约 | [04](docs/04-hermes-secretary-v1.5-implementation-spec.md) |
| 上下文开销台账 | token 实测口径、基线与变更记录 | [05](docs/05-context-cost-ledger.md) |
| Web UI V1 权威规格 | 产品交互、原生接口、设计系统与验收；替代旧 UI 讨论主入口 | [06](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md) |
| 通用协作 / 当前看板 | 用户规则、开发测试 SOP / 动态目标与未完成项 | [AGENTS](AGENTS.md)、[CLAUDE](CLAUDE.md) |
| 第二轮依据索引 | Web UI 轮次授权、规格来源与冻结权限 | [Snapshot Index](.autonomous/20261012-round2-web-ui/snapshot-index.md) |
| 视觉交付与 Mock URL | 共享视觉组件接口、可点击全场景 Mock 清单及验收对账 | [视觉报告](.autonomous/20261012-round2-web-ui/visual-design.md) |
| 历史交付与移交 | V1 交付、V1.5 冻结、V1.6 剩余交接和证据 | [V1](.autonomous/20261007-v1-first-implementation/final-delivery.md)、[V1.5](.autonomous/20261009-v1.5-implementation/index.md)、[V1.6](.autonomous/20261011-v1.6-implementation/continuation-guide.md) |
| 开发与 PM 参考 | 官方环境准备、源码激活及锁文件管理 | [CONTRIBUTING](CONTRIBUTING.md)、[PM](website/docs/reference/package-management.md) |
| Hermes 架构 / 测试参考 | Agent、Gateway、状态层 / runner 与测试布局 | [架构](website/docs/developer-guide/architecture.md)、[测试](tests/AGENTS.md) |
| 安全策略 | 继承的安全边界与报告规范 | [SECURITY](SECURITY.md) |

专项规格在 `docs/`，自主依据与报告在 `.autonomous/`，继承的 Hermes 文档在 `website/docs/`；不把旧讨论或历史审查结论视为当前实现事实。

## 许可证与致谢

保留上游 [MIT License](LICENSE)。Hermes Agent 由 Nous Research 构建；本项目在其基础上增量扩展，原始上游代码和文档保留于 `hermes-upstream`。
