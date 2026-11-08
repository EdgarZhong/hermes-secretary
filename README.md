# Hermes Secretary

基于 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 的公开扩展，面向长期对话中的工作状态维护、责任跟进与提醒。沿用原生 Agent Turn、Session、Gateway、工具和压缩机制；官方 Dashboard 与独立 Secretary Web 共用一个后端。

## 架构与功能

| 模块 | 职责 |
|---|---|
| Conversation / History | `conversation_ref` 标识稳定归属，Session 是物理定位；原文为事实源，复用原生持久化与历史检索 |
| Notebook | 三内容板块及 Candidates；稳定条目、不可变版本和原子 Snapshot；Main 只读、Noting 独占写入；模型以稳定 entry_id 指代条目，内部版本标识仅保留于存储与人类审计 |
| Background Noting | 原生 AIAgent child、冻结父上下文及完整顶层工具表、后台维护派生工作状态；任务提示与运行时身份仅授权六工具，任务不重复Schema |
| Scheduler | 独立排期表、claim / pending / ACK；宿主约5秒扫描，合法本地 Main 的 Instant Reminder 可冷态恢复 |
| Web / Gateway | 多Profile隔离、双SPA同源、消息渠道绑定持久Conversation；历史卡片首屏、显式详情补水与验证型图片引用／视口下载 |

Secretary只在Profile的`state.db`增加自有表，复用原生执行、存储和压缩。主要边界：

- Main只读Notebook，Notebook工具定义完整固定API顶层；绑定Noting仅可执行`conversation_history`、`notebook_show`、`notebook_create`、`notebook_update`、`notebook_archive`、`finish_noting`。Scheduler独立开关；条目`done`不等于成功或归档，证据时间由原始来源派生。
- Noting每个原生Turn最多50次迭代，预算耗尽沿同一任务及已有工作态续开下一Turn；整个任务最多5个Turn，第5轮仍未完成才强制提交当前合法工作态并收尾。
- History提供Get Meta／Search／Read，默认只当前Conversation的真实用户和Assistant；跨域、辅助消息分别显式开启。Notebook来源按Task保存UID链及逐组历史描述，真实编辑与本Task完整UID／描述同传，Evidence time逐节点只读派生；Main处理依赖历史的任务时先核原文，相关引用可用时先Read，见07顶部。
- 手动、Idle及未提前派出Force的原生自动压缩共用并发联合入口；压缩不等待Noting，取消只联合撤销对应未提交工作，已提交Notebook保留。Force只在Main Turn结束检查、不可取消并封住当前区间后续整理；成功压缩解除。Note按合法来源独立沿原FM推送，活跃Turn等待既有间隙。具体契约见[07顶部](docs/07-scheduler-notebook-noting-compaction-redesign.md)。Noting开启且合格Main的full compaction默认将旧尾部纳入摘要，真正达到原生阈值的自动压缩及显式`/compress here N`保留原生保尾。
- Main完成回执以原生最终输出身份封闭，随后Framework继续保留于Conversation历史，不扩大主Turn的完成边界。
- Web可跨进程读取Main及Noting完整生命周期状态；Gateway没有实时输出直连时仍能读取最新持久历史，落库／结束经既有Socket通知恢复。Context读数绑定当前压缩边界并计入后续内容，旧runtime不能覆盖新读数。
- Web同一document优先保留内存画面及阅读状态；刷新／冷启使用同owner持久正文及完整已取详情过渡，正文按最近500条消息统一计数；未取旧详情保持懒取，未核验的半截详情不持久化。正常连续交互沿原生回执／事件和当前可见范围局部读取；冷启、真实重连及身份／覆盖依据失效时完整恢复当前页面所需数据和Socket／Turn。两层缓存均不提供运行状态或操作权限；读取和衔接契约见06。
- Heartbeat沿目标Profile唤醒所属Conversation，是自查提醒；需要用户对接的事项在用户回归时汇报。开启Noting时使用带时间戳的`<heartbeat>`，额外prompt可省略；开关、冷恢复及隔离见[07](docs/07-scheduler-notebook-noting-compaction-redesign.md)。
- 微信回复走原生adapter；Redirect、Framework与其它入口的触达边界见07。入口识别保留原生来源切换notice，不在root System Prompt注入当前Platform身份。

字段、权限、Prompt、触发分支和投递契约统一见[07](docs/07-scheduler-notebook-noting-compaction-redesign.md)，Web恢复见[06](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md)。

可选自适应空闲省token使用Profile的`noting.adaptive_idle_token_saving`，按Conversation显式启用、按原生Provider/模型选项读取两档Heartbeat与固定费用倍率，窗口沿原生继承；默认关闭。历史继承通过`python scripts/adaptive_history_import.py preview|apply --profile NAME --target REF`显式冻结数值训练证据，不继承当前空闲/缓存/排期状态。配置、容量和评测限制见[算法方案](docs/adaptive-noting-threshold-proposal.md)。 原生Idle可用`noting.idle.conversations[conversation_ref]`仅覆盖目标的开关、等待及容量门槛，其它会话保留Profile设置。

既有Conversation可用`python scripts/adaptive_history_bootstrap.py preview|apply --profile NAME --target REF --input FILE --id ID`接入已审数值历史；成熟行为历史跨模型／窗口参与预测，无须重新累计上线后的活动量。初始化保留真实发生与可知时间，不制造新Turn或重锚计时；推荐沿下一自然Turn结束采纳。来源限定、条件费用代理和显式迁移边界见同一[算法方案](docs/adaptive-noting-threshold-proposal.md)。

自适应模型保留连续覆盖能证明的长空闲年龄下界；风险证据分级、维护各项费用来源与逐候选拒因可追溯，Heartbeat使用有界Turn联合费用情景。可用`.venv/bin/python scripts/adaptive_idle_replay.py --input <数值包.json> --output <报告.json>`离线重放显式快照；`--source-root`可指定冻结源码，`--scenarios`读取显式假设场景。不访问生产，缺完整历史运行快照时只报告缺口，不伪造历史前推；统计假设、六小时比较和实测费用限制见[算法方案](docs/adaptive-noting-threshold-proposal.md)。

| 命令 | 行为 |
|---|---|
| `/notebook` | 人类查看当前Notebook与Snapshot时间 |
| `/noting on` / `/noting off` | 切换当前Conversation的Noting参与；不控制Scheduler |
| `/propose-persistence` | 使用当前Snapshot提议持久化；提议不等于批准或执行 |
| `/heartbeat every 10m [prompt]` | 设置周期检查；全局Noting开启时prompt可省略；支持status／pause／resume／clear |

已认证后端提供按Profile／Conversation清空root和工具缓存、按失败child重建旧上下文及Notebook工作态并继续原生Noting的调试RPC；清缓存只在下次正常Turn重建，恢复不要求额外持久快照。接口与调用方式见[07 §12](docs/07-scheduler-notebook-noting-compaction-redesign.md#12-conversation-调试接口用户确认2026-10-21)。

启用Secretary的Main Conversation在同一上下文区间内固定root System Prompt、顶层工具声明与prefill，平台切换不改历史前缀；工具执行仍受当前入口权限约束。Tool Search／Describe／Call使用稳定能力说明，首次及后续工具变化以历史system消息追加一句折叠工具数量与重新发现提示，不附目录；额外渠道指令仅变化时发送必要的新指令，每Turn调用额外工具前重新search／describe当前schema。成功压缩、显式reload／清缓存及原生代码／模型路由重建沿既有边界；工具／Prompt发布后置顶会话的清缓存步骤见[部署SOP](docs/cloud-deployment-sop.md)。Chat Completions与通用Responses保留历史system；ChatGPT订阅Responses将中途system在原位置映射为developer指令，root仍由instructions独立承载，持久历史不变；Anthropic不支持中途system角色，使用原位Framework Message承载，不能等同system优先级。

`/ai-title`依据当前Main生效上下文只读命名，复用完整提示词、工具和prefill前缀。Turn空闲即可重复请求；缓存缺失或冷运行态沿原生owner准备，不要求先发送普通Turn。后台压缩无活动Turn时读取原子生效版本；真正活动Turn仍提示稍后重试。标题任务不执行工具或改写Main上下文，取材及命名写回边界见[06标题命令](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md)。

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

键盘开合由Android Insets提供边界与系统曲线，网页以合成位移衔接Composer和实际正文位置，支持的页面保持完整WebView表面，仅在边界调整网页可用高度；Android 11+关闭系统额外缩窗／平移，APK根层固定且不参与滚动，正文仍可独立滚动。键盘开合期间保持背景画布尺寸并暂停背景绘制，结束后续播。Composer统一按实际内容尺寸进行320ms高度及内部位置过渡。连接／恢复提示采用中性灰胶囊，移动端顶满内宽并留左右间距；桌面位于工具栏主按钮左侧，按父容器剩余空间定宽且最大420px、扩大左侧留白、与左侧选项中心对齐，横向展开折叠，12px文字靠左、展开高度26px，暗色采用灰色填充且无描边；提示自身从固定底边伸缩，Composer同步移动，同阶段最多展示三个恢复对象，保留轮播和省略号，恢复操作资格不等待动画结束。

独立前端的`src-tauri/`提供Tauri 2 Android壳，固定竖屏、内置网页，经正式HTTPS／Authelia连接同一API／WS。系统栏、通知和临时后台保护仅在APK生效；后台保护限已观察到的活动Turn，不保证系统挂起后仍通知。返回前台和网络恢复沿同一SPA自动重连并对账历史／Socket／Turn，不自动整页重载；冷启临时引导网络失败由内置SPA承接自动重试。顶栏支持用户主动下拉刷新，认证导航及自然进程冷启动保留；具体边界按[06 Android契约](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md#android-原生通知与临时后台保护用户最终确认2026-10-21)处理，保留登录、草稿和会话。

在独立前端仓库设置 Android SDK／NDK／Java 环境后执行 `npm run android:build`，输出 `src-tauri/gen/android/app/build/outputs/apk/universal/release/app-universal-release.apk`。当前目标为 Android 8.0+／arm64；release 非调试、使用本地签名，原件仅保存在 ignored `src-tauri/.android-signing/`，后续覆盖升级必须保留该密钥。应用图标由 `npm run android:icons` 复用现有 logo 与主题深色自动生成，release 构建会先刷新图标。`npm run android:debug` 仅供本地验收。 正式构建还需要 Python 3.11+（仅标准库），完成后自动检查 ZIP 全条目 CRC、原证书／v2 签名、版本／ABI、ZIP／ELF 16KB 对齐及内置前端与 dist 逐 SHA 一致。可单独运行 `npm run android:verify`；使用 `npm run android:verify -- --delivery <新文件路径.apk>` 仅在全部校验成功后原子生成交付副本，同时输出 `.sha256` 与 `.verification.json`，拒绝覆盖已有文件；`npm run android:test` 验证截断／CRC／签名／版本／资源等拒绝路径。产物校验不代替设备安装与生命周期验收。实际包版本、网络验证及限制统一记录在 [运维记录](docs/operations-log.md)。

## 部署入口

正式服务器为首尔 Alex（`ssh alex`，ubuntu，`43.128.131.30`）；部署使用 Caddy HTTPS → Authelia双因素（Redis Unix socket保存会话）→ 回环单后端。Secretary `/` 与官方Dashboard `/dashboard` 同源共用API / WS；不增加第二后端或多worker。云端检出main，仅发布已合入main的后端代码；前端只部署构建产物。旧北京Cloudflare Tunnel模板与当前入口区别见 [部署SOP](docs/cloud-deployment-sop.md)。

运维步骤、Profile布局、凭据与同步责任见SOP；实际变更、验证和回滚点统一记录在 [运维记录](docs/operations-log.md)，不再堆入核心文档。

## 重要文档索引

| 内容 | 入口 |
|---|---|
| 通用规则、开发测试SOP | [AGENTS](AGENTS.md) |
| 当前阶段、未关闭事项 | [CLAUDE](CLAUDE.md) |
| 已审Notebook语义 | [白板](docs/notebook-ontology-whiteboard.html) |
| History / Noting / Scheduler / Prompt实施契约 | [07](docs/07-scheduler-notebook-noting-compaction-redesign.md) |
| Conversation缓存清理、失败恢复与单次新Noting调试RPC | [07 §12](docs/07-scheduler-notebook-noting-compaction-redesign.md#12-conversation-调试接口用户确认2026-10-21) |
| Conversation级Heartbeat、英文模板与UI后台唤醒 | [07 §8.15](docs/07-scheduler-notebook-noting-compaction-redesign.md#815-heartbeat-形态与-ui-唤醒用户确认2026-10-21) |
| Web UI与交互契约 | [06](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md) |
| Profile、模型窗口、渠道绑定、工具与冷态提醒 | [08](docs/08-profile-scheduler-files-clarification.md) |
| 公开范围及旧规格明确保留部分 | [01](docs/01-personal-hermes-v1-first-fork-iteration.md)、[02](docs/02-noting-system-specification.md)、[04](docs/04-hermes-secretary-v1.5-implementation-spec.md) |
| 部署、认证、同步与回滚SOP | [部署SOP](docs/cloud-deployment-sop.md) |
| 部署与故障变更台账、证据入口 | [运维记录](docs/operations-log.md) |
| 2026-10-28联合Noting／压缩中断的历史取证（后继实现另见07） | [问题报告](docs/noting-compaction-framework-interruption-20261028.md) |
| 2026-10-20手机Web／微信、网络与Noting历史调查 | [调查报告](docs/mobile-web-investigation-20261020.md) |
| 自适应维护实验：默认关闭的联合决策/执行合同、历史影子评测与复跑、实盘影子配置、定性验收及局限；历史配置不代表现值 | [算法方案](docs/adaptive-noting-threshold-proposal.md) |
| 手机HTTP/2实测及残留问题 | [验收报告](docs/mobile-http2-acceptance-20261020.md)、[原任务书](docs/mobile-http2-retest-task.md) |
| 手机Web／微信交替使用、网络与Noting故障取证 | [运维记录](docs/operations-log.md)中的10/20调查与证据入口 |
| 移动端阶段一实施、验收与后续短网络实验任务书 | [任务包入口](docs/hermes-network-experiment-20261020/README.md)、[阶段一](docs/hermes-network-experiment-20261020/PHASE1-IMPLEMENTATION.md) |
| 上下文开销 | [05](docs/05-context-cost-ledger.md) |
| 历史冻结与交付 | [产品意图复审](.autonomous/20261018-product-intent-review/snapshot-index.md)、[云部署](.autonomous/20261019-cloud-deployment/snapshot-index.md)、[第三轮](.autonomous/20261016-round3-secretary-nm/snapshot-index.md)、[第二轮](.autonomous/20261012-round2-web-ui/snapshot-index.md) |
| PM、架构与测试参考 | [CONTRIBUTING](CONTRIBUTING.md)、[PM](website/docs/reference/package-management.md)、[架构](website/docs/developer-guide/architecture.md)、[测试](tests/AGENTS.md) |
| 安全与许可证 | [SECURITY](SECURITY.md)、[MIT License](LICENSE) |

规格按最新明确替换关系使用；历史报告只证明其被测版本。`docs/archived/`非默认阅读入口。保留Nous Research上游版权与原生文档。
