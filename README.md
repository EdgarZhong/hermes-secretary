# Hermes Secretary

Hermes Secretary 是基于 [Nous Research 的 Hermes Agent](https://github.com/NousResearch/hermes-agent) 的公开扩展，面向长期对话中的工作状态维护、责任跟进与提醒。

第三轮改版的已审语义见 [Notebook 白板](docs/notebook-ontology-whiteboard.html)，工具、英文提示文与接线契约见 [07](docs/07-scheduler-notebook-noting-compaction-redesign.md)。二者共同组成Secretary新设计依据；第三轮同时开展独立的个人NM接入，保持个人实现隔离，界面改版后置。旧 01／02／04／06 仅在明确保留的范围继承。通用规则见 [AGENTS.md](AGENTS.md)，当前状态、代码版本、任务与证据见 [CLAUDE.md](CLAUDE.md)。

**阅读顺序：** AGENTS → CLAUDE → 白板 → 07 → 07 指定的旧规格保留段落。设计契约、实现接线和验收证据分别判断；当前集成状态以 CLAUDE 为准，旧轮次报告不能代替第三轮证据。

## 核心架构

沿用 Hermes 的 Agent Turn、physical Session、Gateway、原生工具、压缩与持久化，在既有接缝增量扩展。Conversation 原文是事实源，Notebook 是派生工作状态；Secretary 只向 profile-scoped `state.db` 增加自有表，不改原有表的 schema 或 ownership。现有官方 Dashboard（`web/` 与 `hermes_cli/web_server*.py`）仍是原生浏览器管理入口，独立 Secretary Web UI 的契约见 06。

| 模块 | 已落实的数据与职责边界 |
|---|---|
| Conversation Identity | `conversation_ref` 为稳定 ownership；physical Session、compression lineage 和 Gateway scope 为 locator |
| Conversation History | 复用原生检索候选流及合法 History Foreground，以 `(conversation_ref,message_uid)` 返回规范来源；不建立第二份原文库 |
| Notebook 数据层 | 三内容板块及 Candidates；稳定 entry 身份、不可变版本；Snapshot 固定版本映射，以原子 current pointer 发布；Main 只读 |
| Background Noting | 复用原生 AIAgent、持久 child 与冻结父前缀；任务生命周期和正式接线位于 `secretary/noting_*.py` |
| Scheduler 数据层 | 独立的 Conversation Schedule Table、原生时间解析、claim／pending／ACK；不随 Notebook pointer 重选修改 |
| 配置与 Main 提示 | `noting`、`scheduler` 独立配置解析；Notebook local 参与由 `/noting` 控制，配置与工具请求同步沿原生构建接缝 |
| 时间与消息载体 | 可读带时区绝对时间，以及 timestamp、Framework、Instant/Deferred Reminder 的真实载体契约 |
| Full Foreground | 内部逻辑审计投影：唯一 Context Prelude、真实消息节点与 Anchor/Snapshot 附着；Web 全量审计视图按 06 延后 |

底层模块具备接口不代表全部 host 接线或整版验收已完成；正式运行和测试证据统一见 CLAUDE 及本轮报告。

## Secretary Slash 入口

命令复用 Hermes 共享 catalog、补全与执行链路。CLI、Gateway、官方 Dashboard 与 Web 的人类呈现边界按现行 02／06 及 07 的保留和替换条款处理。

| 命令 | 行为 |
|---|---|
| `/notebook` | 人类查看当前 Conversation 的完整 Notebook 与 Snapshot 创建时间；无 Snapshot 时明确提示 |
| `/noting on`、`/noting off` | 修改当前 Conversation 的后台 Noting 参与状态；保留 Snapshot，不控制独立 Scheduler |
| `/propose-persistence` | 提供当前完整 Snapshot 与共用提案指令，由 Main 按需查核原文；可附自然语言，提议与修改均不等于执行批准 |

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

当前草稿全部附件合计上限为 500,000,000 bytes，选择时累计判断、移除后释放预算，发送时小文件沿原生 `file.attach`，分片使用增量 `file.upload_chunk` / `file.upload_abort`，元数据使用 `file.attachment_info`，并显式绑定本次图片。两个订阅同一会话的客户端共享原生实时事件；普通 Send 只在 Main Turn 空闲时启动新 Turn，活动时按既定 Steer/Stop/Interrupt 操作。

Web 的 `/notebook` 是仅保存在浏览器内存中的四分区只读临时卡片，按调用顺序固定在命令发起时的 Timeline 位置，刷新后清除；任务状态与排期分别呈现，不展示内部 Anchor。

`/notebook` 卡片时间标签为 `Updated at`，时间值沿用当前 Snapshot 的原生创建时间。后台进程和异步子 Agent 完成回报按原生 `display_kind` 显示为独立通知卡片，标题分别为 `process complete`、`async delegation complete`，复用 Framework Message 主题，默认折叠、可展开；前端不识别为 User Message，不提供 Reply／编辑。Noting Framework Message 保持原有展示。

聊天历史首次加载最近 200 条后台消息，`Show More History` 每次向前加载 200 条；工具调用与结果计入条数。历史按需分页，不在浏览器持久化转录副本。

Timeline 视口状态只在页面内存保存，刷新回底；用户 Send 被接受后立即回底跟随，其他来源的新 Turn 不触发回底。手动滚动暂停跟随，停止控制 20 秒后仅在 Turn 仍活动时恢复。向前加载历史保留当前内容锚点。完整工具调用段通过原生提交事件提供有序身份与展示元数据；并行调用逐张展示、按调用段顺序固定位置，各自更新状态。

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

Git 提交后通过 [post-commit hook](.githooks/post-commit) 推送当前分支的 upstream；工作区首次使用时按 [Git 同步约束](AGENTS.md#本地-ci--cd-与回归防护) 检查实际 hooks 路径并保留已有 hooks 后安装。独立 UI 的正式本地 main 对应 origin/secretary；新功能分支无 upstream 时推 origin 同名。失败时本地提交保留，不强推。

Python 不绕过 canonical runner 直接运行 pytest；JS/UI 入口及环境准备见 [Development Setup](CONTRIBUTING.md#development-setup)。`.venv/`、`.hermes-dev/` 不入版本控制。GitHub Actions 保持关闭，质量门禁在本地执行；测试范围、独立门禁与证据复用流程见 AGENTS。

## 重要文档索引

| 文档 | 内容 | 路径 |
|---|---|---|
| Secretary 改版实施契约 | 与已审白板互补：转向历程、术语、Conversation History、四工具 Noting、Scheduler、完整 Schema／反馈、英文提示文及源码接线路径 | [07](docs/07-scheduler-notebook-noting-compaction-redesign.md) |
| Notebook 已审方案白板 | 三板块七类型、逐类型进退、信息流、Noting 完整任务与联合触发的已审语义；工具／英文提示细节在 07 定案；支持会议批注 | [白板](docs/notebook-ontology-whiteboard.html) |
| V1 实施总纲 | 公开核心范围、边界与继承要求 | [01](docs/01-personal-hermes-v1-first-fork-iteration.md) |
| 改版前 Core 规格与保留机制 | 第三轮只继承就地标明的 Identity、Foreground、Snapshot、runtime 和投递不变量；旧 Target 不作为新施工要求 | [02](docs/02-noting-system-specification.md) |
| Notebook 清理机制旧提案（归档） | 原 07 研讨，已由白板与新 07 替代，不作为施工要求 | [归档](docs/archived/notebook-cleanup-mechanism-proposal.md) |
| Noting 文案／提醒结构旧提案（归档） | 原 08 研讨及旧英文草案，新版提示文以 07 为准 | [归档](docs/archived/noting-message-and-reminder-contract-proposal.md) |
| 改版前 V1.5 增量与保留机制 | 按新版替换标识继承缓存前缀、持久 child、有限续跑等机制 | [04](docs/04-hermes-secretary-v1.5-implementation-spec.md) |
| 上下文开销台账 | token 实测口径、基线与变更记录 | [05](docs/05-context-cost-ledger.md) |
| Web UI 基线与保留契约 | 继承原生客户端、交互、设计系统；Memo、旧类型／工具与开关按 07 替换 | [06](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md) |
| UI 只读 API 早期讨论（归档） | 已被正式 06 覆盖的早期讨论；旧 Memo 设计不进入新版 | [归档](docs/archived/06-ui-read-api-discussion.md) |
| 通用协作 / 当前看板 | 用户规则、开发测试 SOP / 动态目标与未完成项 | [AGENTS](AGENTS.md)、[CLAUDE](CLAUDE.md) |
| 第三轮依据索引 | Secretary改版与独立个人Provider的依据、会话口径及双仓库冻结记录入口 | [Snapshot Index](.autonomous/20261016-round3-secretary-nm/snapshot-index.md) |
| 第二轮依据索引 | Web UI 轮次授权、规格来源与冻结权限 | [Snapshot Index](.autonomous/20261012-round2-web-ui/snapshot-index.md) |
| 视觉交付与 Mock URL | 共享视觉组件接口、可点击全场景 Mock 清单及验收对账 | [视觉报告](.autonomous/20261012-round2-web-ui/visual-design.md) |
| 历史交付与移交 | V1 交付、V1.5 冻结、V1.6 剩余交接和证据 | [V1](.autonomous/20261007-v1-first-implementation/final-delivery.md)、[V1.5](.autonomous/20261009-v1.5-implementation/index.md)、[V1.6](.autonomous/20261011-v1.6-implementation/continuation-guide.md) |
| 开发与 PM 参考 | 官方环境准备、源码激活及锁文件管理 | [CONTRIBUTING](CONTRIBUTING.md)、[PM](website/docs/reference/package-management.md) |
| Hermes 架构 / 测试参考 | Agent、Gateway、状态层 / runner 与测试布局 | [架构](website/docs/developer-guide/architecture.md)、[测试](tests/AGENTS.md) |
| 安全策略 | 继承的安全边界与报告规范 | [SECURITY](SECURITY.md) |

专项规格在 `docs/`，自主依据与报告在 `.autonomous/`，继承的 Hermes 文档在 `website/docs/`；不把旧讨论或历史审查结论视为当前实现事实。

## 许可证与致谢

保留上游 [MIT License](LICENSE)。Hermes Agent 由 Nous Research 构建；本项目在其基础上增量扩展，原始上游代码和文档保留于 `hermes-upstream`。
