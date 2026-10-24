# Hermes Secretary

基于 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 的公开扩展，面向长期对话中的工作状态维护、责任跟进与提醒。沿用原生 Agent Turn、Session、Gateway、工具和压缩机制；官方 Dashboard 与独立 Secretary Web 共用一个后端。

## 架构与功能

| 模块 | 职责 |
|---|---|
| Conversation / History | `conversation_ref` 标识稳定归属，Session 是物理定位；原文为事实源，复用原生持久化与历史检索 |
| Notebook | 三内容板块及 Candidates；稳定条目、不可变版本和原子 Snapshot；Main 只读、Noting 独占写入 |
| Background Noting | 原生 AIAgent child、冻结父上下文及完整顶层工具表、后台维护派生工作状态；任务提示与运行时身份仅授权四工具，任务不重复Schema |
| Scheduler | 独立排期表、claim / pending / ACK；宿主约5秒扫描，合法本地 Main 的 Instant Reminder 可冷态恢复 |
| Web / Gateway | 多Profile隔离、双SPA同源、消息渠道绑定持久Conversation；历史卡片首屏、显式详情补水与验证型图片引用／视口下载 |

Secretary 只在Profile的 `state.db` 增加自有表，不改原表 schema / ownership。`noting`、`scheduler` 独立配置，`/noting` 控制当前Conversation参与。微信入站的完整正式回复按消息及时由adapter发送，Redirect的半截正式正文并入对应通知；其它入口须显式调用发送工具，Framework等非触发式上下文注入不借用上一轮渠道adapter自动发送。实现边界及已知限制见 [当前看板](CLAUDE.md)。

Main的`scheduler`与`notebook_show`按各自能力开关完整独立声明在API顶层，不进入Tool Search折叠目录：前者受`scheduler.enabled`，后者沿全局`noting.enabled`读取门禁；当前Conversation的`/noting`参与开关不控制这两项权限。`notebook_maintain`与`finish_noting`也沿全局`noting.enabled`完整固定顶层且不折叠，Main只能看见定义、运行时禁止执行；绑定Noting仅授权`conversation_history`、`notebook_show`及这两工具。其它工具保留原生折叠策略。

Heartbeat按目标Profile全局`noting.enabled`分支：开启时使用带时间戳的英文`<heartbeat>`消息，额外prompt可省略，经现有UI runtime／platform唤醒所属Main；关闭时保留原生格式与执行路径。后台执行需UI后端运行，独立于`scheduler.enabled`；状态按Profile与稳定Conversation保存在自有表；支持独立设置／暂停／恢复／清除，压缩续接共享，new／reset／fork不继承。切换页面、关闭连接、runtime回收及服务重启后仍由后台扫描恢复自身Main，不跟随当前Gateway绑定。精确模板与运行边界见[07 §8.15](docs/07-scheduler-notebook-noting-compaction-redesign.md#815-heartbeat-形态与-ui-唤醒用户确认2026-10-21)。

| 命令 | 行为 |
|---|---|
| `/notebook` | 人类查看当前Notebook与Snapshot时间 |
| `/noting on` / `/noting off` | 切换当前Conversation的Noting参与；不控制Scheduler |
| `/propose-persistence` | 使用当前Snapshot提议持久化；提议不等于批准或执行 |
| `/heartbeat every 10m [prompt]` | 设置周期检查；全局Noting开启时prompt可省略；支持status／pause／resume／clear |

已认证后端提供按Profile／Conversation清空root和工具缓存、按失败child重建旧上下文及Notebook工作态并继续原生Noting的调试RPC；清缓存只在下次正常Turn重建，恢复不要求额外持久快照。接口与调用方式见[07 §12](docs/07-scheduler-notebook-noting-compaction-redesign.md#12-conversation-调试接口用户确认2026-10-21)。

## 仓库与目录

`origin` 为 [EdgarZhong/hermes-secretary](https://github.com/EdgarZhong/hermes-secretary)，`main` 为公开核心；`upstream` 为官方Hermes，`hermes-upstream` 为纯镜像。个人NM Provider独立于公开核心，独立前端在并列仓库 `../hermes-secretary-web`。

```text
hermes-secretary/
├── README.md / AGENTS.md / CLAUDE.md  # 稳定入口 / 协作规则 / 当前状态
├── docs/ / .autonomous/              # 规格与运维 / 轮次冻结与验收
├── run_agent.py / agent/             # 原生Agent、Prompt、模型调用和压缩
├── hermes_state*.py / secretary/     # 原生状态层 / Secretary扩展
├── hermes_cli/ / gateway/            # CLI、Web宿主和消息入口
├── tui_gateway/ / ui-tui/ / apps/    # RPC、TUI和桌面客户端
├── tools/ / plugins/ / skills/ / cron/
├── pm/ / hermes_platform/            # 官方环境管理和平台能力
├── tests/ / tests-js/ / scripts/     # 测试和本地检查
└── web/ / website/docs/              # 官方Dashboard / 上游开发参考
```

## 开发与测试

Python与依赖使用官方PM及现有锁；环境准备见 [CONTRIBUTING](CONTRIBUTING.md)。本地隔离 `HERMES_HOME` / runtime，不写真实用户状态。

```bash
# 仅创建新环境时执行，目标.venv须不存在
python -m pm.build_env --source . --out .venv --group dev --group test
export HERMES_HOME="$PWD/.hermes-dev"
export HERMES_RUNTIME_DIR="$HERMES_HOME/tools"
source ./activate
hermes --version
# 定向测试与相关检查
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/<相关文件>.py
.venv/bin/python scripts/check --staged --only <相关检查>
```

Gateway入口 `hermes gateway`；Dashboard入口 `hermes dashboard --host 127.0.0.1 --no-open`（默认9119），源码入口为 `.venv/bin/python -m hermes_cli.main dashboard ...`。运行中Git版本变化会触发模型操作漂移保护；开发开关与重启边界见 [06 §0.8](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#08-development-opt-out-for-model-code-skew-guards-user-confirmed-2026-10-17)。

独立前端使用 React / TypeScript / Vite：`npm ci`、`npm run dev`（默认连接53445）、`npm run typecheck`、`npm test`、`npm run build`。静态Mock入口 `npm run mock -- --port 5176` → `/mock.html`，不连接后端；说明见 [Mock交接](.autonomous/20261012-round2-web-ui/static-mock.md)。官方JS工作区按需执行 `npm run --workspace <web|ui-tui|apps/desktop> check`。

检查规则、测试范围、证据复用和自动push统一见 [AGENTS](AGENTS.md)。GitHub Actions保持关闭。完整Python套件仍用 `scripts/run_tests.sh`，仅在集成收敛后按规则安排。

### Android APK

独立前端仓库的 `src-tauri/` 提供 Tauri 2 Android 壳，固定竖屏，前端资源内置，业务仍经正式 HTTPS／Authelia、原生 API／WS 连接。Android 专属系统栏避让和通知桥接不会在普通网页启用；运行状态复用现有跨 Profile 列表观察，不增加后端协议、独立连接或轮询。后台保护仅在已观察到的 Active Turn 期间临时启用，不保证系统暂停／回收后仍通知。APK从锁屏或后台返回前台时由原生重载当前页面并重置恢复进度；连接持续未恢复时按10／15／20／30秒重载退避，连接恢复停止，正常慢历史加载不误刷。此机制保留登录／本地草稿／当前会话，不在普通网页启用。完整行为和验收边界见 [06 Android 契约](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#android-原生通知与临时后台保护用户最终确认2026-10-21)。

在独立前端仓库设置 Android SDK／NDK／Java 环境后执行 `npm run android:build`，输出 `src-tauri/gen/android/app/build/outputs/apk/universal/release/app-universal-release.apk`。当前目标为 Android 8.0+／arm64；release 非调试、使用本地签名，原件仅保存在 ignored `src-tauri/.android-signing/`，后续覆盖升级必须保留该密钥。应用图标由 `npm run android:icons` 复用现有 logo 与主题深色自动生成，release 构建会先刷新图标。`npm run android:debug` 仅供本地验收。实际包版本、网络验证及限制统一记录在 [运维记录](docs/operations-log.md)。

## 部署入口

当前首尔部署使用 Caddy HTTPS → Authelia双因素（Redis Unix socket保存会话）→ 回环单后端。Secretary `/` 与官方Dashboard `/dashboard` 同源共用API / WS；不增加第二后端或多worker。前端只部署构建产物。旧北京Cloudflare Tunnel模板与当前入口区别见 [部署SOP](docs/cloud-deployment-sop.md)。

运维步骤、Profile布局、凭据与同步责任见SOP；实际变更、验证和回滚点统一记录在 [运维记录](docs/operations-log.md)，不再堆入核心文档。

## 重要文档索引

| 内容 | 入口 |
|---|---|
| 通用规则、开发测试SOP | [AGENTS](AGENTS.md) |
| 当前阶段、未关闭事项 | [CLAUDE](CLAUDE.md) |
| 已审Notebook语义 | [白板](docs/notebook-ontology-whiteboard.html) |
| History / Noting / Scheduler / Prompt实施契约 | [07](docs/07-scheduler-notebook-noting-compaction-redesign.md) |
| Conversation缓存清理与失败Noting热恢复RPC | [07 §12](docs/07-scheduler-notebook-noting-compaction-redesign.md#12-conversation-调试接口用户确认2026-10-21) |
| Conversation级Heartbeat、英文模板与UI后台唤醒 | [07 §8.15](docs/07-scheduler-notebook-noting-compaction-redesign.md#815-heartbeat-形态与-ui-唤醒用户确认2026-10-21) |
| Web UI与交互契约 | [06](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md) |
| 页面恢复、展示缓存与统一交接实施方案 | [06 §1.4.1](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#141-页面恢复过渡展示缓存与统一交接实施方案2026-10-24) |
| Profile、模型窗口、渠道绑定、工具与冷态提醒 | [08](docs/08-profile-scheduler-files-clarification.md) |
| 公开范围及旧规格明确保留部分 | [01](docs/01-personal-hermes-v1-first-fork-iteration.md)、[02](docs/02-noting-system-specification.md)、[04](docs/04-hermes-secretary-v1.5-implementation-spec.md) |
| 部署、认证、同步与回滚SOP | [部署SOP](docs/cloud-deployment-sop.md) |
| 部署与故障变更台账、证据入口 | [运维记录](docs/operations-log.md) |
| 手机HTTP/2实测及残留问题 | [验收报告](docs/mobile-http2-acceptance-20261020.md)、[原任务书](docs/mobile-http2-retest-task.md) |
| 手机Web／微信交替使用、网络与Noting故障取证 | [2026-10-20晚调查报告](docs/mobile-web-investigation-20261020.md) |
| 移动端阶段一实施、验收与后续短网络实验任务书 | [任务包入口](docs/hermes-network-experiment-20261020/README.md)、[阶段一](docs/hermes-network-experiment-20261020/PHASE1-IMPLEMENTATION.md) |
| 上下文开销 | [05](docs/05-context-cost-ledger.md) |
| 自适应Idle整理阈值算法初稿、定性公式与条件预测（未实现） | [算法方案](docs/adaptive-noting-threshold-proposal.md) |
| 历史冻结与交付 | [产品意图复审](.autonomous/20261018-product-intent-review/snapshot-index.md)、[云部署](.autonomous/20261019-cloud-deployment/snapshot-index.md)、[第三轮](.autonomous/20261016-round3-secretary-nm/snapshot-index.md)、[第二轮](.autonomous/20261012-round2-web-ui/snapshot-index.md) |
| PM、架构与测试参考 | [CONTRIBUTING](CONTRIBUTING.md)、[PM](website/docs/reference/package-management.md)、[架构](website/docs/developer-guide/architecture.md)、[测试](tests/AGENTS.md) |
| 安全与许可证 | [SECURITY](SECURITY.md)、[MIT License](LICENSE) |

规格按最新明确替换关系使用；历史报告只证明其被测版本。`docs/archived/`非默认阅读入口。保留Nous Research上游版权与原生文档。
