# 08 · Profile 隔离、冷态 Reminder 与 Files 归属澄清

> 用户确认的补充契约，记录于 2026-10-18。本文只收敛本次明确讨论的边界，不代表代码已实现或通过测试。实现状态与待办统一记录在根 `CLAUDE.md`。
>
> 权威关系：补足 02 §3.10–3.12、07 §6.2–6.3 的宿主生命周期要求；在 Files 入口归属上补充并优先于 06 §1.16／§2.11 的旧含混解释。未明确变更的原生 API、权限、Conversation 身份、busy、claim／lease、消息持久化及 ACK 契约继续保持。不得把本补充扩成 Personality 改造、跨 Profile 检索或新的 Workspace 管理产品。

## 1. Profile、配置与 Conversation

Profile 是 Hermes Agent 身份、配置与持久状态的独立归属域。各自拥有 Hermes Home、`config.yaml`、`.env`、`SOUL.md`、`state.db`、原生记忆与 Skills。共同的程序安装、依赖或宿主进程不合并这些数据；这也不是操作系统沙箱隔离的承诺。

`noting.enabled` 与 `scheduler.enabled` 的“全局”均指所属 Profile 内的全局配置，不是宿主机或所有 Profile 的共同开关。后台工作须按持久状态的实际所属 Profile 读取配置，不能借用启动 Profile、浏览器当前选择或 Files 的固定 Profile。Conversation-local `/noting on|off` 只控制所属 Conversation 的 Noting 参与状态；不能关闭 Scheduler，也不改变其他 Conversation。History 不依赖 Noting 或 Scheduler 开关。

Profile 选择器仅出现在首页／New Chat，用于决定即将创建的 Conversation 的归属。Conversation 一经创建，Web UI 不提供重新选择、修改或迁移其 Profile 的功能。打开另一 Profile 已有的 Conversation 是导航到另一个既有对象，不是更改当前对象的身份。发送、草稿、附件、恢复、控制与配置操作均保持真实 owner；已经受理的工作不能被页面导航重新归属。

`conversation_history` 保持当前权限：合格 Main 可显式检索同一 Profile 内其他合法用户 Conversation；不开放跨 Profile 检索。Noting 只检索绑定的父 Conversation。统一的用户会话列表不授予 Agent 跨 Profile 历史读取权，也不要求合并 `state.db`。

各 Profile 可以配置相同或不同的 `terminal.cwd`。共用 Workspace 只是可选部署方式，不是产品前提，不合并 Home、数据库、记忆、指令或会话历史。打开 Files 不修改任何已有 Conversation 的 cwd。

## 2. 冷态 Instant Reminder 的宿主责任

### 2.1 Runtime 可回收，排期不能因此停止

只要 Hermes Web 宿主正常运行，目标 Profile 由该宿主管理、Scheduler 已启用，且排期与目标 Conversation 仍合法可执行，到期扫描和 Instant Reminder 的投递尝试必须持续工作，不依赖以下条件：浏览器打开、WebSocket 在线、页面当前选择该 Profile／Conversation、驻留的 TUI Runtime Session 或 Agent 实例。双SPA部署使用README既有的 `hermes dashboard --no-open` 入口；`hermes serve` 是不挂载SPA的headless入口，根路径握手页的HTTP 200不能算网页已部署。这是原生启动模式的区分，不引入第二个后端或新的调度机制。

必须覆盖：浏览器关闭，原 Web Runtime 已完全回收，Web宿主仍运行；到期后无需用户重新打开或发送消息，后端仍自动发现并处理该 Conversation 的 Instant Reminder。仅在用户重开页面后补投，不满足本条。自动回收内存对象不能被当作用户暂停排期、结束逻辑 Conversation 或撤销后台处理意愿。

扫描生命周期由常驻宿主负责，不得以“每个存活 Session 都有轮询器”替代所有受管理持久排期的覆盖。优先复用原生周期维护与恢复接缝；确无合适接缝时，02 §3.10 已允许窄的 Secretary 扫描器，不得另造完整 Cron 执行系统。07 §6.4 的“不新增独立轮询／定时器”仅约束 24 小时空档提示，不禁止本节必要的到期扫描。

### 2.2 投递、恢复与时效

正常负载下采用已认可的约 5 秒到期扫描节奏。该节奏描述发现到期工作的频率，不是模型完成响应、外部网络送达或用户阅读的 5 秒硬保证；资源、原生接纳或 Provider 失败必须如实保留和报告，不能静默忽略。

持久 `conversation_ref` 及其所属 Profile 是投递身份依据。若 Main Runtime 不存在，宿主必须沿原生恢复能力定位正确的当前物理 Session／合法 continuation，恢复 Main，再经原有 ingress 与原子接纳入口处理 Reminder。不得新建一个替代用户 Conversation、借用另一 Profile、错投同 Profile 的微信会话，或改成独立 Cron／Noting 子 Agent 执行。

空闲时，Instant Reminder 可发起原 Conversation 的 Main Turn；busy 时保留现有原子转 pending deferred 语义，不积压一个未来强制 Turn。纯 deferred 仍不主动唤醒，只在下一次合法模型请求中承载；本补充不改变其语义。

多宿主接缝并存时复用已有 claim／lease 和原生接纳所有权，避免重复受理。Runtime 回收不是释放 durable occurrence 的理由；暂停、删除、配置关闭、并发用户输入、取消及身份变更继续按已有事务边界处理。失败保留可恢复的排期事实，不得仅凭取得 claim、创建 Runtime 或写入推送任务就确认最终交付。消息见证与 ACK 仍按各自既有契约结算。

宿主停止期间不承诺按时执行；宿主重启后须自动恢复合法的到期工作，不等待浏览器连接。迟到一次性任务不能仅因过期丢弃；周期排期继续使用原生推进规则，不无限重放积压。不得为了掩盖接线缺口而关闭 Runtime 回收或让所有 Agent 永久驻留。

这里要求的是进入原 Conversation 并自动执行 Main 的能力，不新增浏览器离线系统通知或微信推送必达保证。没有到期工作时，扫描不能为了保活而新建 Main、调用模型或拼装所有 Conversation 的完整上下文。

### 2.3 浏览器任意时刻接入的执行可见性（2026-10-18 用户明确）

后台Reminder与Web发起的Turn共用原生执行与可观察链。用户在Reminder运行前、中途或完成后打开前端，必须能取得正确Profile／Conversation的真实状态与完整可用Timeline；断线重连同样适用。中途恢复包括真实Reminder载体、上游已提供的Thinking、工具调用及当前／完成状态、已输出正文，后续事件无遗漏或重复地接续。不能只恢复running和一段正文，也不能用有界ring掩盖已淘汰的当前Turn事件。首页／侧栏须能取得并持续更新未打开Conversation的后台状态，不为观察状态唤醒全部Runtime。复用现有生命周期、历史／输出投影、事件回放和全局广播，不新建平行机制；静默不意味着隐藏真实执行。具体验收遵06的同源单后端部署，通过本机反代及隐藏内置浏览器分别取证，不用后台执行成功代签前端可见。

## 3. Files 固定 Profile 的临时接线

V1 Files 固定借用一个现有 Profile 的文件后端及默认 Workspace，不跟随当前聊天、New Chat 的 Profile 选择或服务器 sticky active Profile 改变。固定选择集中在前端单一位置；可采用 `default` 作为临时绑定，不随机取列表第一项，也不引入新的设置页、Workspace 注册表或文件数据库。

目录根读取、列表、文本／媒体预览和下载必须一致使用这个固定 Files Profile。不能只固定 `/api/fs/default-cwd` 而仍用当前聊天 Profile 读文件。固定 Profile 不可用、目录无效或权限不足时显示真实错误，不悄悄切换到另一个 Profile。

Files 自己的固定根目录，与新会话按所属 Profile 解析的默认 cwd 必须分开；Files 绑定不得污染 `session.create`、会话恢复、模型配置或附件上传的 owner。进入 Files 时保存此前聊天的 Profile 与路由；Back to Chat 必须恢复该完整身份。刷新、深链接及新标签页也不能把文件绑定错当为 Conversation owner。

后端 `/api/fs/default-cwd?profile=P` 的契约仍为读取 P 的有效默认目录。即使前端只借用一个固定 Profile，本地文件分支也必须在请求 Profile 的配置作用域中解析 cwd，不能在 SSH 探测作用域结束后回到启动配置读取。保持现有响应字段、可选参数及旧客户端兼容；不得通过修改进程全局 `HERMES_HOME` 或进程 cwd 实现按请求切换。

## 4. 后续编码的最低验收场景

以下是验收要求，不是本次已运行的测试结果。

| 场景 | 必须观察的结果 |
|---|---|
| 浏览器关闭且 Runtime 已确认回收 | `serve` 无客户端连接时发现到期 Instant，在同一 Profile／Conversation 执行真实 Main Turn |
| 全冷启动／宿主重启 | 无浏览器、无预先构建 Agent 时恢复合法逾期工作；一次性不丢失，周期不无限补发 |
| A 页面聊天、B 的 Reminder 到期 | B 按 B 的配置和数据库处理；A 的界面选择不成为 B 的开关或路由 |
| busy、暂停／删除与到期竞争 | 保留现有 busy→deferred、claim 撤销和接纳事务语义，不产生多余强制 Turn |
| Serve／Gateway 竞争同一到期发生 | 保持真实 owner 及已有去重保证，不错投渠道，不以测试替身 ACK 冒充最终交付 |
| A、B 配置不同的真实本地目录 | `default-cwd?profile=A/B` 各返所属配置，不借用启动 Profile |
| 固定 Files Profile 与当前聊天 Profile 不同 | list／preview／download 都访问固定文件后端；新会话仍使用自己的默认 cwd |
| Files 返回、刷新及新标签页 | 文件入口绑定稳定，返回原聊天时 Profile 与 Conversation 不串线 |

对冷态场景，测试必须让原 Runtime 和其 Session 轮询器真正不存在，再驱动常驻宿主接缝；预先构建 Agent 后手动调用会话轮询函数，只能证明恢复后的投递，不能证明冷态自动唤醒。
