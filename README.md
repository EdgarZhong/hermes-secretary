# Hermes Secretary

Hermes Secretary 是基于 [Nous Research 的 Hermes Agent](https://github.com/NousResearch/hermes-agent) 的公开扩展，面向长期对话中的工作状态维护、责任跟进与提醒。

已审语义见 [Notebook 白板](docs/notebook-ontology-whiteboard.html)，工具、英文提示文与接线契约见 [07](docs/07-scheduler-notebook-noting-compaction-redesign.md)；旧 01／02／04／06 按明确保留与替换范围使用。通用规则见 [AGENTS.md](AGENTS.md)，当前目标、代码版本与验收证据见 [CLAUDE.md](CLAUDE.md)。设计规格与历史报告不代表当前版本已通过验收。

## 核心架构

沿用 Hermes 的 Agent Turn、physical Session、Gateway、工具、压缩与持久化，在既有接缝增量扩展。Conversation 原文是事实源，Notebook 是派生工作状态；Secretary 只向 profile-scoped `state.db` 增加自有表，不改原有表的 schema 或 ownership。官方 Dashboard 与独立 Secretary Web UI 共用原生后端。

| 模块 | 已落实的数据与职责边界 |
|---|---|
| Conversation Identity | `conversation_ref` 为稳定 ownership；physical Session、compression lineage 和 Gateway scope 为 locator |
| Conversation History | 复用原生检索候选流及合法 History Foreground，以 `(conversation_ref,message_uid)` 返回规范来源；不建立第二份原文库 |
| Notebook | 三内容板块及 Candidates；稳定 entry、不可变版本与原子发布的 Snapshot；Main 只读。Noting 以 `source_message_uids` 引用本 Conversation 来源，可信绑定补全归属；内部与全局 Message Identity 保留完整身份 |
| Background Noting | 复用原生 AIAgent、持久 child 与冻结父前缀；任务生命周期和正式接线位于 `secretary/noting_*.py` |
| Scheduler 数据层 | 独立的 Conversation Schedule Table、原生时间解析、claim／pending／ACK；不随 Notebook pointer 重选修改 |
| 配置与 Main 提示 | `noting`、`scheduler` 独立配置；Conversation-local Noting 参与由 `/noting` 控制，沿原生构建接缝接入 |
| 时间与消息载体 | 可读带时区绝对时间，以及 timestamp、Framework、Instant/Deferred Reminder 的真实载体契约 |
| Full Foreground | 内部逻辑审计投影：唯一 Context Prelude、真实消息节点与 Anchor/Snapshot 附着 |

`hermes serve`／Dashboard 宿主在启动时及每轮后约 5 秒扫描受管理 Profile 的持久排期。合法本地 Main 的 Instant Reminder 可在无浏览器、Runtime 已回收时沿原生入口恢复；deferred 不主动唤醒，busy 转 pending，消息渠道路由保留原 owner。配置、失败及投递确认边界见 [08 §2](docs/08-profile-scheduler-files-clarification.md#2-冷态-instant-reminder-的宿主责任)。

## Secretary Slash 入口

命令复用 Hermes 共享 catalog、补全与执行链路；客户端呈现边界按 02／06／07 的保留与替换条款处理。

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

上游同步执行 [文档保护 SOP](AGENTS.md#上游同步与核心文档保护-sop)；新 clone 按需添加并 fetch `upstream`，审查后集成。

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

本地开发与浏览器验收使用 localhost、隔离 `HERMES_HOME` / runtime。开发 Python 3.14 与依赖由 Hermes PM 和官方锁文件管理；Git、Git LFS、Node.js 与 JS workspace 环境见 [CONTRIBUTING.md](CONTRIBUTING.md) 和 `package.json`。

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

### 模型代码版本漂移保护（开发开关）

进程启动时记录 checkout 的 Git revision；运行中版本变化后，模型列表、密钥保存、模型切换等操作拒绝请求（TUI/Desktop RPC `5098`、Dashboard `503`）。保护默认开启。

本地开发需要在同一 checkout 内继续这些模型操作时，在启动 Profile 的 `config.yaml`（默认 `~/.hermes/config.yaml`）中设置：

```yaml
gateway:
  model_code_skew_guard: false
```

也可执行 `hermes config set gateway.model_code_skew_guard false`。后端启动时读取一次，同进程所有 Profile 共用；修改后需重启对应 gateway、dashboard/`hermes serve` 或 TUI。关闭只跳过模型操作的漂移拒绝，保留原始检测、Cron 使用方、退休/watchdog、Session `4001`、认证及模型/provider 校验。此开关不热更新模块，真实导入或运行错误仍会暴露，必要时仍需重启；详见 [06 §0.8](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#08-development-opt-out-for-model-code-skew-guards-user-confirmed-2026-10-17)。

## 独立 Secretary Web 开发入口

独立前端位于并列本地仓库 `../hermes-secretary-web`，使用 React / TypeScript / Vite，直接调用原生 REST / WS；开发服务默认连接 `http://127.0.0.1:53445`。主要交互按以下规格定位：

| 主题 | 稳定边界与详细契约 |
|---|---|
| Profile | 仅 New Chat 选择归属，已有 Conversation、草稿与附件保持 owner；共享 Workspace 不合并身份。新增图标维护 `src/core/profile-icons.tsx`。[06 §2.11](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#211-new-chat-profile-selection-and-conversation-icons-user-confirmed-2026-10-17) |
| Files | 临时固定 `default`（`src/core/files.ts`），list／preview／download 同 owner；返回聊天恢复原 Profile 与路由。[08 §3](docs/08-profile-scheduler-files-clarification.md#3-files-固定-profile-的临时接线) |
| Timeline | 原生消息分类、完成通知、200 条分页、滚动跟随与逐调用工具卡。[06 §1.4](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#14-timeline-streaming-message-kinds-and-timestamps)、[§1.5](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#15-tool-rendering-markdown-and-errors) |
| Notebook／Noting | `/notebook` 为浏览器内存中的临时只读卡；运行状态与 Snapshot 成功高亮分别呈现。[06 §1.12](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#112-slash-catalog-command-dispatch-and-human-only-notebook)、[§1.15](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#115-secretary-orb-noting-status-and-memo-stick) |
| 附件与 Send | 草稿附件总上限 500,000,000 bytes，复用原生附件与增量分片接口；Send／Steer／Stop／Interrupt 按真实 Turn 状态执行。[06 §1.7](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#17-attach-entry-points-and-local-selection)、[§1.8](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#18-primary-action-normative-decision-table) |
| Context／Compaction | 原生 usage、冷恢复估算与精确计数分离；压缩状态和历史使用真实载体。[06 §1.13](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#113-usage-cards-and-context-indicator)、[§1.14](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#114-compaction-presence-cancellation-and-authentic-history) |

Schedule Table 按条目时区（IANA／`UTC±HH:MM`）显示绝对时间，缺失或无效时区以明确标记的 UTC 回退；只读数据边界见 [06 §2.6](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#26-secretary-human-only-read-contracts)。

在前端目录执行 `npm ci` 后，以 `npm run dev` 启动页面；`npm run typecheck`、`npm test`、`npm run build` 分别执行类型检查、测试与构建。静态工作台入口为 `npm run mock -- --port 5176` → `/mock.html`，不连接后端或模型；检查／构建用 `npm run mock:test`、`npm run mock:build`。场景和组件边界见 [Mock 交接说明](.autonomous/20261012-round2-web-ui/static-mock.md)。

## 部署形态

Cloudflare 入口部署使用**一个业务域名、一套 Cloudflare Access、一个后端进程**。首尔正式入口使用 Caddy HTTPS＋Authelia 双因素认证，认证会话存于仅通过 Unix socket 访问的 Redis；其运维入口见[部署 SOP](docs/cloud-deployment-sop.md#0-首尔正式入口的认证运维)。

```text
手机 / 浏览器
  → https://<private-host>/            Cloudflare Access（邮箱白名单）
  → Cloudflare Tunnel
  → 本机 Caddy（仅 127.0.0.1）         Host 改写为 127.0.0.1、删除 Origin
  → Hermes 后端（仅 127.0.0.1）
       ├─ /                Secretary SPA（HERMES_WEB_DIST）
       ├─ /dashboard       官方 Dashboard SPA（HERMES_DASHBOARD_WEB_DIST）
       ├─ /dashboard/api/* 重写为 /api/*
       └─ /api/*、/api/ws  两套共用
```

- 不配置第二个 API 域名，不做浏览器跨域/CORS；Access 是唯一用户可见认证层，后端 token 由各自的 `index.html` 自动注入。
- 两套 SPA 必须由**同一个后端进程**挂载；不要用第二个后端进程或多 worker，否则内存会话、Scheduler/Noting 会分裂或重复。
- 后端与 Caddy 只监听 `127.0.0.1`；Cloudflare Tunnel 是唯一入口。Docker 部署需要 host 网络或等价共享命名空间，否则 WebSocket 的 loopback peer 检查会拒绝。
- 未设置 `HERMES_DASHBOARD_WEB_DIST` 时，后端行为与原来完全一致（不挂 `/dashboard`、不改写路径）。

启动示例：

```bash
HERMES_WEB_DIST=/opt/hermes-secretary-web/dist \
HERMES_DASHBOARD_WEB_DIST=/opt/hermes-secretary/hermes_cli/web_dist \
HERMES_DASHBOARD_PREFIX=/dashboard \
hermes dashboard --host 127.0.0.1 --port 53445 --skip-build --no-open
```

本机 Caddy（只监听回环，两层 Web 认证都不由它承担）：

```caddyfile
:8080 {
    reverse_proxy 127.0.0.1:53445 {
        header_up Host 127.0.0.1:53445
        header_up -Origin
    }
}
```

Cloudflare Tunnel（cloudflared 主动出站，不开放入站端口）：

```yaml
tunnel: <tunnel-id>
credentials-file: /etc/cloudflared/<tunnel-id>.json
ingress:
  - hostname: <private-host>
    service: http://127.0.0.1:8080
  - service: http_status:404
```

Access 应用使用同一个 hostname，策略为 `Allow` + 邮箱白名单；不要为 `/api/*` 或 `/dashboard/api/*` 配置 Bypass。`/dashboard/api/*` 的前缀重写由后端完成，Caddy 不需要额外 path 规则。

官方 Dashboard 需要单独构建：`cd web && npm run build`。完整约束与验收口径见 [Web UI 规格 §0.7](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#07-confirmed-deployment-topology-and-dual-spa-routing-2026-10-17)。

## 代码规范与测试入口

代码规范、原生兼容、Profile 隔离与开发测试 SOP 统一见 [AGENTS.md](AGENTS.md)。

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

提交后由 [post-commit hook](.githooks/post-commit) 自动同步当前分支；首次安装、upstream 与失败处理见 [Git 同步约束](AGENTS.md#本地-ci--cd-与回归防护)。独立 UI 正式本地 main 对应 origin/secretary。

Python 测试统一使用上述 runner；环境准备见 [Development Setup](CONTRIBUTING.md#development-setup)。`.venv/`、`.hermes-dev/` 不入版本控制。GitHub Actions 关闭，质量门禁在本地执行。

## 重要文档索引

| 文档 | 内容 | 路径 |
|---|---|---|
| Secretary 改版实施契约 | History、四工具 Noting、Scheduler、Schema、英文提示文与源码接线 | [07](docs/07-scheduler-notebook-noting-compaction-redesign.md) |
| Notebook 已审方案白板 | 三板块七类型、进退、信息流、任务与联合触发语义；支持会议批注 | [白板](docs/notebook-ontology-whiteboard.html) |
| V1 实施总纲 | 公开核心范围、边界与继承要求 | [01](docs/01-personal-hermes-v1-first-fork-iteration.md) |
| 改版前 Core 规格与保留机制 | 按标识继承 Identity、Foreground、Snapshot、runtime 和投递不变量 | [02](docs/02-noting-system-specification.md) |
| Notebook 清理机制旧提案（归档） | 原 07 研讨，已由白板与新 07 替代，不作为施工要求 | [归档](docs/archived/notebook-cleanup-mechanism-proposal.md) |
| Noting 文案／提醒结构旧提案（归档） | 原 08 研讨及旧英文草案，新版提示文以 07 为准 | [归档](docs/archived/noting-message-and-reminder-contract-proposal.md) |
| 改版前 V1.5 增量与保留机制 | 按新版替换标识继承缓存前缀、持久 child、有限续跑等机制 | [04](docs/04-hermes-secretary-v1.5-implementation-spec.md) |
| 上下文开销台账 | token 实测口径、基线与变更记录 | [05](docs/05-context-cost-ledger.md) |
| Profile、冷态提醒与 Files 补充契约 | Profile 配置归属、serve 冷态 Instant 恢复、Files 固定归属及最低验收场景 | [08](docs/08-profile-scheduler-files-clarification.md) |
| Web UI 基线与保留契约 | 客户端、交互、设计系统、部署；思考档位见 §2.10，漂移开关见 §0.8；旧机制按 07 替换 | [06](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md) |
| 上云部署 SOP | Linux 双SPA单后端、Tunnel／Access及首尔Authelia／Redis认证、Profile、常驻、验收、备份及回滚 | [部署 SOP](docs/cloud-deployment-sop.md) |
| 手机HTTP/2三轮复测 | 本机DSH执行的真实双端流式、灭屏、关标签重开与切换取证任务书 | [复测任务书](docs/mobile-http2-retest-task.md) |
| UI 只读 API 早期讨论（归档） | 已被正式 06 覆盖的早期讨论；旧 Memo 设计不进入新版 | [归档](docs/archived/06-ui-read-api-discussion.md) |
| 通用协作 / 当前看板 | 用户规则、开发测试 SOP / 动态目标与未完成项 | [AGENTS](AGENTS.md)、[CLAUDE](CLAUDE.md) |
| 产品意图复审与交付依据 | 最新产品文档、用户纠偏、独立审查及场景/功能覆盖验收入口 | [Snapshot Index](.autonomous/20261018-product-intent-review/snapshot-index.md) |
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
