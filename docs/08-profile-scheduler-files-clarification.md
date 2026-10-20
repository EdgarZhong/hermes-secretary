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

### 1.1 模型窗口与微信入口绑定（2026-10-20 用户确认）

同一 Conversation 的 Web 与微信入口共用历史及其实际模型路由；冷恢复统计按该路由解析 Context 上限，不能借用 Profile 当前默认模型的窗口。Kimi Coding 的 `k3-256k` 原生窗口为262144；DeepSeek 的自定义500000只在匹配的模型路由上生效，未知元数据不得以256000兜底冒充已知窗口。DeepSeek模型选择器保留一个正式Provider。

微信绑定到持久 Conversation，跨Runtime回收、服务重启及compact沿同一Conversation接续，不自动退回另一条微信独立会话；显式解绑／新会话仍由用户决定。绑定记录复用原生路由条目的metadata，adapter保留接收者／投递者身份，不能改写被绑定Main的source或session_key来伪装绑定。工具成功须持久保存该身份关系。用户操作fork／branch会创建新的Conversation；微信绑定留在分支前的原Conversation，新分支不继承绑定，不将分支视为原Conversation的Session延续。

**2026-10-20 用户确认的不变量：** 只有显式调用绑定／解绑工具可以改变持久Conversation绑定；压缩耗尽、suspended恢复、后台delegation回流及其它自动路由恢复均不得替代绑定目标。A派发任务后已显式改绑B，A的晚到结果不能把绑定切回A，也不能注入B；保留其原有持久结果记录。允许沿同一Conversation合法compression lineage更新物理locator，不得以新Conversation冒充延续。未绑定的原生路径保持原行为。

AI使用的绑定工具对外以Conversation ref为唯一目标身份，废弃Session ID参数／查询口径；内部可解析当前物理Session，不将该实现责任交给AI。当前Conversation查询必须依据调用方上下文，缺失时明确失败，不回退到当前绑定、最近会话或标题猜测。这是2026-10-20确认的接口要求；绑定操作由存活Gateway通过原生本地控制通道保存，工具不通过停启服务或离线改路由实现。

工具统一位于`~/scripts/<profile>/weixin_bind.py`，每个工具只负责其自己的Profile，不提供跨Profile选择入口；当前只制作Alex工具。绑定调用方直接使用`bind --self`一步完成，不设单独的`self conversation`查询，也不保留`current`或`--current`别名。`list`只列所属Profile最近的Conversation，每个Conversation一条，带完整ref、标题等属性及`is_self`（调用方）和`is_current_binding`（当前通道的显式绑定目标）两个独立标记；两个身份相同则同一条都为true。调用方身份缺失时，列表仍可查询，但`is_self`为null并明确身份不可用，绑定调用方则失败，不猜测；明确来自其它Profile的调用直接拒绝（包括只读查询），不读取Alex状态。若调用方或绑定目标不在最近结果内，顶层身份／绑定信息仍说明其ref，不伪称未绑定。指定其它Conversation用`list`和`bind --conversation-ref <完整ref>`，`status`只查询绑定状态。

保持Hermes原生收发：微信消息触发的Turn，由adapter投递原生回复；Web、Instant Reminder及其它入口触发的Turn，只有显式调用发送工具才发微信。Web显示与发送微信是两个独立动作，不把全部Web回答自动转微信。

**主动发送来源标题（2026-10-20 用户确认）：** Alex显式微信发送工具在调用方Conversation与当前绑定不同时，自动在发给用户的消息头添加调用方Conversation标题；同一Conversation不加。该标注由工具完成，调用方AI的正常发送回执不增加来源标注说明。拿不到可靠调用方身份时保留发送，不猜测／添加标题；绑定或查询不可用时同样不猜，不为来源展示失败阻断原发送。不改变绑定，不新增发送次数；其它peer不得借用默认peer的绑定作判断。

**2026-10-20 用户追加确认：** 微信不再提供原生slash命令控制；收到slash命令时直接拒绝执行，并提示回Web UI管理Conversation。不会将命令作为普通消息提交模型，也不触发会话重置、分支、切换或其它原生命令。换绑应回Web UI直接告诉AI，由既有工具完成；其它Platform的原生slash保持不变。此段是已确认需求，实现状态见CLAUDE。

入口提示保留Hermes原生Gateway／其它Platform按消息来源轮换，以及入口切换时的notice注入；不在System Prompt注入“当前Platform”身份。SOUL.md与workspace AGENTS.md已可定初稿，不将模型行为指导挂成未实现工程功能。

### 1.2 预置独立工具（2026-10-20 用户确认）

个人小工具统一`~/scripts/`，本机与云端不保留旧拼写目录或别名。当前首尔保护对象为通用`nmem-memory.py`及Alex下的`alex_weixin_send.py`、`weixin_bind.py`：原件可读／可执行、防普通误改，扩展先读源码并在`~/scripts/custom/`另建副本，不自行解锁、替换原件。用户仅要求防下意识误操作，不扩大为账号或sudo权限隔离。

Memory写入工具在preview与apply均必须显式传非空`--space`，Default也写`--space default`。缺失、空串、纯空白在输入读取、CLI及网络操作前拒绝；不得隐式继承Profile或环境目标。此要求只约束手动Memory创建工具，不修改Provider自动Thread同步的Space配置语义。

## 2. 冷态 Instant Reminder 的宿主责任

### 2.1 Runtime 可回收，排期不能因此停止

只要 Hermes Web 宿主正常运行，目标 Profile 由该宿主管理、Scheduler 已启用，且排期与目标 Conversation 仍合法可执行，到期扫描和 Instant Reminder 的投递尝试必须持续工作，不依赖以下条件：浏览器打开、WebSocket 在线、页面当前选择该 Profile／Conversation、驻留的 TUI Runtime Session 或 Agent 实例。双SPA部署使用README既有的 `hermes dashboard --no-open` 入口；`hermes serve` 是不挂载SPA的headless入口，根路径握手页的HTTP 200不能算网页已部署。这是原生启动模式的区分，不引入第二个后端或新的调度机制。

必须覆盖：浏览器关闭，原 Web Runtime 已完全回收，Web宿主仍运行；到期后无需用户重新打开或发送消息，后端仍自动发现并处理该 Conversation 的 Instant Reminder。仅在用户重开页面后补投，不满足本条。自动回收内存对象不能被当作用户暂停排期、结束逻辑 Conversation 或撤销后台处理意愿。

扫描生命周期由常驻宿主负责，不得以“每个存活 Session 都有轮询器”替代所有受管理持久排期的覆盖。优先复用原生周期维护与恢复接缝；确无合适接缝时，02 §3.10 已允许窄的 Secretary 扫描器，不得另造完整 Cron 执行系统。07 §6.4 的“不新增独立轮询／定时器”仅约束 24 小时空档提示，不禁止本节必要的到期扫描。

### 2.2 投递、恢复与时效

正常负载下，冷态Instant到期应在5秒扫描窗口内被发现并开始投递尝试；不增加来源名称白名单，合法导入Main同样覆盖。该节奏描述发现到期工作的频率，不是模型完成响应、外部网络送达或用户阅读的 5 秒硬保证；资源、原生接纳或 Provider 失败必须如实保留和报告，不能静默忽略。

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
