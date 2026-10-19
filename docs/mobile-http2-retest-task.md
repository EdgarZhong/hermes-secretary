# 暂停HTTP/3后的三轮真实双端复测任务书

## 用户交接入口

本任务包由用户自行交给本机DSH中的 **ds coding agent** 执行；主会话不再操控、启动或调整DSH。准备任务包不代表复测已经开始。可直接向ds发送：

用户后续已让主会话并行进行本地代码修复，尚未部署。协议对照仍以云端实际运行版本/静态产物为准；本地dirty不是线上已更新的证据。不要自行构建、同步或部署本地修复，否则会破坏“仅暂停HTTP/3”的对照条件。

> 请完整阅读 `/Users/edgar/code/hermes-secretary/docs/mobile-http2-retest-task.md`，按任务书执行全部三轮真实手机Chrome与桌面Chrome复测并保存底层日志。你是本机DSH的测试执行者，云端受测Hermes仍使用DeepSeek / deepseek-flash。HTTP/3已暂停，先核实实际协议；保留旧证据，不改业务代码或服务配置。完成后交回报告、原始证据清单和未解决问题；遇必须人工解锁或认证的真实阻塞再通知我。

## 1. 执行主体、目标与授权

执行者是用户本机 **DeepSeek Harness（DSH）的ds coding agent**。云端Hermes只是受测产品，三轮休眠任务均在正式Hermes UI选择 **DeepSeek / deepseek-flash** 后发送，不使用Kimi，不把本任务书作为云端Hermes的编排任务。

用户于本轮明确授权：暂停HTTP/3；完整复刻刚才三轮真实手机/电脑测试；由本机DSH的ds执行。前序授权原话包括“直接使用我的Chrome手机上的做实测和复现”“你也可以同时操作手机、电脑，从任何一边起一个turn”。此为**仅本轮Hermes业务页的真实Chrome窄例外**，优先于根AGENTS中通常仅允许隐藏IAB的限制。它不授权桌面控制、其它网页、原生App、切桌面或抢焦点。手机ADB可控制该Chrome页面、关闭/重开自有Hermes标签页及短时灭屏/唤醒；需要人脸/指纹/密码解锁时等用户亲自完成，不绕过。

目标是判断：**只暂停HTTP/3、不修业务代码时，手机慢加载、活动Turn恢复、列表/标题缺失、user气泡迟到是否改善，以及哪些代码问题仍存在**。不是证明“网络已修好”。正常样本、未复现、失败和缺证全部保留。

默认整包完成后一次性交回；中途仅在无法继续的真实阻塞、需要用户解锁/重新认证、必须由主会话决定的权限或产品取舍时汇报。不得逐条广播命令、小发现或“阶段完成”。**不再派生子Agent。**

## 2. 必须先读的入口

1. `/Users/edgar/code/hermes-secretary/AGENTS.md`、根`CLAUDE.md`顶部当前交接记录、本任务书。
2. 原轮次冻结分析：`.hermes-dev/mobile-network-20261019/preserved-complete-20261019T225604/analysis.md`。
3. 原件清单：上述目录`manifest.json`，SHA256 `96c02bd4395b22821eeb52a0e4013fbc10eaac3560c21c6f777b5166246fe080`。80文件、39921645字节。初始R1/R2固定副本也在原证据目录，禁止覆盖。
4. 协议切换收据：`.hermes-dev/mobile-http2-retest-20261019/cloud-cutover-receipt.json`。
5. 需要复用取证代码时，只读`.hermes-dev/mobile-network-20261019/{capture.py,dual_monitor.py,netlog_capture.py,phone_ui.py,server_logs.py}`及`r3/{phone_supervisor.py,dual_monitor.py,netlog_capture.py,phone_click.py,public_packet_metadata.py}`。**先复制到本轮新目录再适配；不直接运行带旧输出路径的脚本。**

原helper缺陷必须处理：手机target2479/2480已关闭，不能硬编码；桌面target/窗口要重新发现；旧`phone_ui.py`固定写r1-actions且把R3误称R2；R3的`r2User`字段实际检测R3 marker；工具按钮应取可访问名称，不用仅有textContent的旧选择器；CDP关闭目标的异常不等于产品网络失败；旧collector会省略/不转发部分dataReceived，缺数不可写为0字节。

## 3. 范围、现场与禁止事项

- 工作目录：`/Users/edgar/code/hermes-secretary`；独立UI为`/Users/edgar/code/hermes-secretary-web`，均仅只读。先记录实际HEAD、dirty、锁文件SHA、云端HEAD和实际加载JS/CSS名；不假设与此前相同。
- 云主机：`ssh seoul`，不是北京`alex`。正式入口`https://hermes.edgarzhong.fyi`；认证门户`https://auth.edgarzhong.fyi`。
- 当前协议配置仅增加`servers { protocols h1 h2 }`；2026-10-19 23:00:38–43 +08已由主会话应用，Caddy PID181221；Hermes PID144598、Authelia35490、Redis21608未变。这些是切换时点证据，执行时重新只读核实。
- Caddy配置SHA256：`16d3de9039648b296602657833bec1f7dc0a619c754276aa6c4ae6b7ff67d2c3`。备份`/var/backups/caddy/http3-paused-20261019T230037/`。**不自行恢复HTTP/3、不再重启服务、不启用压缩。**
- ADB预期PHZ110 / Android16，序列号`QK6LIRY5RCEMOZ65`；先用`adb devices -l`确认，若多设备不猜。旧自建19222转发已移除；检查现有映射后选本轮专用本地端口，不覆盖其它映射。
- 真实桌面Chrome通过chrome-use CLI；技能`/Users/edgar/.agents/skills/chrome-use/SKILL.md`及`chrome-use skills get core`。只动用户授权的Hermes页，必要时`--tab ... --force`后台操作；不要`--activate`、bringToFront或系统open。
- 既有参考Conversation：旧只读会话`20261019_020701_6a255b`（历史约274KB）；另一条已有会话`20261019_222205_af4e08`（约54KB）；原诊断会话`20261019_223240_2dc5b2`。保留用户原历史、不删除、不编辑、不Stop其它用户Turn。推荐本轮新建一个专用QA Conversation，三轮复用该会话，另用上述旧会话作切换对照。
- 白名单写入：`.hermes-dev/mobile-http2-retest-20261019/runs/<实际开始时间>/`中的脚本、脱敏日志、截图、报告和manifest；可在根CLAUDE顶部本交接区补最终报告入口/执行状态，不改其它并行看板。测试引起的正式消息和自动标题是已授权产品操作。
- 不改业务代码、Prompt、SOUL、模型配置默认值、DB/索引/迁移、分页、依赖/锁、服务/代理/防火墙/路由/sysctl/MTU、监测系统；不commit/push/deploy；不安装全局工具；不写NM Memory/提醒/排期，不对外发送通知。
- 不读取/输出/复制`.env`、DSH凭据文件、Cookie、认证Token原值；复用现有正式登录态及配置。认证墙需用户操作时停止相关动作并报阻塞，不造临时账号或绕过双因素。

## 4. 前置检查及采集契约

### 4.1 保持对照有效

1. 校验旧manifest，不回改旧证据；记录开始时间（UTC及Asia/Shanghai）、设备网络类型/默认网络ID/MTU、是否VPN、桌面路线可见事实及服务PID。只读，不切手机网络、不关闭用户VPN、不清浏览器数据、不重启Chrome。
2. 验证Caddy无UDP443监听、TCP443正常；匿名Hermes302、auth200。验证手机实际REST `response.protocol`/ResourceTiming已为h2或HTTP/1.1。**WS HTTP/1.1升级是正常，不要求WS显示h2。**
3. 手机可能缓存旧Alt-Svc，首访尝试UDP后回退必须照实记录，不擅自清浏览器状态；无法证明REST已切TCP时，不能把后续结果当HTTP2对照通过。
4. 保存实际载入产物哈希/名称、后端版本，确认业务代码/压缩未变化。采集前不要先跑大套测试、压力测试或重新部署。

### 4.2 同时采集三条时间线

- 手机：Network request/response/data/finished/failed；协议、路径（剥query）、请求类型、requestId、连接ID、status、Content-Length/Encoding、DNS/connect/TLS/sendStart/receiveHeaders/body时长、取消及底层`net::ERR_*`；WS创建/握手/关闭、RPC方法/回执ID、事件type/seq/runtime/正式消息身份（不保存正文、token查询参数）。
- 电脑：同样事件和Performance ResourceTiming，用于精确对齐同一seq的到达时间；CLI若不提供某类字段就标未采，不伪造0。
- UI：约2秒一采、状态变化才落盘。当前路由、可见性、标题、侧栏是否Loading/列表条数、user marker是否出现、Thinking/工具名称与状态、Stop/Send可用、usage有无、错误提示。记录轮次自己的marker即可，避免无关聊天原文。关键异常/恢复保存同一业务页AX/PNG。
- 服务端：脱敏Caddy access/error、必要Hermes日志、服务PID/资源/只读回环健康；复用现有监测只读观察，不改它。需要tcpdump时只采公网443包头元数据（不抓loopback明文、不存正文/凭据），有timeout、仅目标手机来源、记录内核丢弃数；不要拿tcpdump checksum offload提示当链路损坏。
- 如采NetLog，用browser级连接跨标签页生命周期持续采集；不启用`sensitive`类别；只留必要数字、枚举、pid/source identity和目标关联，不存headers/原URL。未关联目标的浏览器全局事件不得冒充Hermes故障或算丢包率。
- 每个人为动作先落`actions.jsonl`：发送、刷新、灭屏、唤醒、解锁、关闭、重开、切换、采集重连。手机/电脑/服务器时钟差要记录；事件到达差与渲染采样间隔分开。
- 关闭手机标签页时CDP target会换；提前启动browser级观察或目标发现supervisor，保留旧target退出与新target接入原件，不能只采旧target后宣布重开正常。

## 5. 三轮步骤（必须完整覆盖，不以孤立HTTP探针替代）

所有发送经正式UI；先核实际`Model: deepseek-flash`，再发。无需改变Profile默认模型。提交结果不明先核回执/运行状态，不重发；不能因界面显示K3的短暂初始化态断言已调用Kimi。每轮标记独立、保留失败尝试，不加无限重跑。

### R1：电脑发起10×30秒，手机接入、刷新、切换、灭屏恢复

1. 两端采集先启动；电脑正式UI新建本轮专用QA Conversation，选择deepseek-flash；手机先保持其它已有会话前台，不锁屏。
2. 电脑发送以下任务，记录accepted/message.start为T0：

> HTTP2-RETEST-R1：用户授权的双端网络复测。严格顺序调用terminal工具10次，每次单独执行sleep 30后输出HTTP2-RETEST-R1-step-N，N从1到10。不要合并循环、不要后台运行，不读写文件、不做其它操作或创建提醒。每次结束立即继续下一次；浏览器断开也继续，最后只回复HTTP2-RETEST-R1-DONE。

3. T0后约25秒：记录手机其它会话侧栏是否出现新Conversation；然后进入同一QA会话。优先实际侧栏链接；无链接时先截图留证再用已知URL进入，并注明这是地址导航。保存历史、标题、列表、usage和当前工具状态的各自恢复时间。
4. 保持前台至少一个完整工具开始→完成→下一工具开始；比较同seq在两端到达差。不能把0.2–0.7秒正常延迟写成断线。
5. T0后约137秒：手机刷新当前活动会话；记录文档加载与完整可用的分离时间，不以document complete代表成功。
6. T0后约184秒：手机切到其它已有Conversation；约209秒切回QA。不要等Turn结束后才切。侧栏不可用先留证，地址整页跳转单列，不能冒称SPA切换成功。
7. T0后约265秒、确认Turn仍active：手机真实灭屏30秒再唤醒。不要用离线模拟替代；如需用户解锁，报一次明确阻塞，记录实际解锁时刻，等待用户，不绕过。不能把人未解锁时间算作应用恢复延迟。
8. 唤醒后先不刷新，观察WS、bootstrap、重放、历史和列表是否自己恢复；记录首个新事件、追上最新seq、各UI恢复时间与错误是否清除。此前原样本有WS关闭/7个ERR_QUIC_PROTOCOL_ERROR/20秒bootstrap Abort，需分别查证，不预设本轮也失败。
9. 持续到message.complete及至少60秒后，保存最终状态、剩余在途请求和列表错误；确认10个工具开始/完成及最终DONE，按seq去重。原计时仅作复刻目标，网络卡住/模型思考使实际动作晚到必须保留，不补造时点。

### R2：同一会话手机发起2×30秒，电脑持续观察

1. R1完成后，两端均保持同一QA会话且连接已建立。不得先刷新电脑来掩盖跨端问题。
2. 手机确认deepseek-flash并发送：

> HTTP2-RETEST-R2：继续用户授权的双端诊断。用terminal执行sleep 30，一次结束后再用terminal执行sleep 30。不要合并，不读写文件、不做其它操作，最后只回复HTTP2-RETEST-R2-DONE。

3. 独立记录本端：手机草稿/临时气泡、accepted回执、正式user气泡、Thinking、历史请求发出/完成。尤其记录草稿清除后至气泡出现的空窗；未复现也写未复现，不称消息丢失。
4. 独立记录跨端：电脑收到message.start、Thinking、每个工具、普通user正文和气泡的时间，以及是否必须等message.complete后历史回读才出现。不能用“电脑列表出现了新会话”证明user气泡已同步。
5. 同一工具start/complete按seq比较到达时间和UI切换时间。保持到最终DONE及双方user/assistant均完整；不把事件已收到但UI尚未渲染混成网络延迟。

### R3：手机300秒任务，关标签重开同URL，再关重开另一URL并切回

1. 手机在同一QA会话选择deepseek-flash，发送：

> HTTP2-RETEST-R3：用户授权的300秒标签页关闭/重开恢复诊断。严格顺序调用terminal工具10次，每次单独执行sleep 30后输出HTTP2-RETEST-R3-step-N，N从1到10。不要合并循环或后台运行，不读写文件、不做其它操作或创建提醒。浏览器断开也继续到第10次，最后只回复HTTP2-RETEST-R3-DONE。

2. 首个tool.start确认后约25秒，关闭**该手机Hermes标签页**；立刻重新访问同一QA URL。只关自己这一个页，不force-stop Chrome，不关闭其它用户页。桌面保持该QA，确认服务端任务继续且未重发。
3. 新target接入后记录HTML/WS/history/状态快照/标题/侧栏/usage完整时间。在流恢复但侧栏空时打开实际侧栏，保存AX/PNG；不能拿正常流代签侧栏。
4. 第一次重开约83秒后、确认R3仍active：关闭这个手机标签页，改开旧会话`/chat/20261019_020701_6a255b?profile=alex`。新target单独采集；记录其历史约274KB及后续详情约89KB是否仍慢，注意目标本身无active Turn而QA在运行。
5. 改开旧URL后约72秒、仍确认R3 active：尝试从正式侧栏切回QA。若列表未就绪，先保存无链接/Loading证据，再按已知QA URL整页导航，标注真实操作方式。记录追上当前工具/seq所需时间，是否必须等Turn结束。
6. 约再过45秒，在电脑刷新同一活动QA做恢复对照；若用户已切桌面到其它页，先读取当前tab归属，不覆盖无关用户动作，可用另一授权Hermes页；记录与原样本的差异，禁止抢焦点。
7. 观察到第10个tool.complete、message.complete和DONE，再继续至少60秒，核对手机列表/标题/usage是否最终恢复。即使没报错但列表一直Loading，也应作为该场景未通过。

## 6. 必须比较的原基线与判定

| 范围 | 原HTTP3样本 | 本轮需报告 |
|---|---|---|
| 手机列表 | 约587KB，成功18–59秒；初始另见73–84秒；峰值19在途列表请求（含空Profile），7个QUIC失败 | 协议、数量、字节、峰值、每请求阶段及失败码 |
| 手机冷旧会话 | history约274KB/24–26秒，detail约89KB/11–12秒 | 相同URL、同参数和数据量下实际时间，缓存区别 |
| 手机本端user | R3 accepted后Thinking先出，约13秒后气泡；history sendStart等约10.1秒 | 是否有显示空窗、在哪个阶段等、历史最终是否一致 |
| R2跨端user | 电脑已收工具，user直到完成后回读才显示 | 保持订阅时真实气泡出现条件 |
| 冷标题/列表 | 活动resume已有info.title，但UI等全列表；流恢复、标题Conversation/侧栏0链接 | 是否仍存在，不把暂停HTTP3当代码已修复 |
| 桌面恢复 | 同会话history约0.61秒、587KB列表1.20秒 | 作为对照的实测，不默认必定1秒 |
| R1灭屏 | WS约6秒后关闭；唤醒约3.5秒WS ready；7个QUIC错误及bootstrap超时分开 | 手机已解锁后的恢复时长/错误清除/数据完整 |

本轮不新增性能SLA硬门槛。每场景分别判：已恢复且证据完整／明显改善但有剩余缺陷／失败／未覆盖。完整结果必须覆盖路由、列表、标题、user、Thinking/工具、usage、最终一致性，不能仅看HTTP200或WS101。一次未复现不是永久修复；协议切换伴随Caddy重启/连接重建，应在结论中保留这一混杂因素。

最长导入会话的200/100/50条基线与17秒旧展示回退已经取证；本任务**不重跑长会话profiling，不修那2条缺索引记录，不改分页**。可引用既有报告说明这是独立未修代码瓶颈，不将其混入HTTP2收益。

## 7. 交付、收尾与完成定义

输出目录中至少有：

- `environment.json`：时间、设备/网络、实际版本/产物、协议和采集能力/缺口，凭据只留不可逆指纹或不采。
- `actions.jsonl`、每端/每target事件原件、服务器脱敏日志、关键AX/PNG；各轮独立标记。
- `results.json`：按场景列完整性、耗时、请求数/峰值/字节、错误码、事件与UI差、原基线对照、证据路径。
- `report.md`：三轮步骤实际执行表、正常/失败/未覆盖、HTTP2改善到哪、还剩什么、不能下哪些结论。明确本端气泡和跨端气泡的区别。
- `manifest.json`：原件相对路径、大小、SHA256；完成后逐文件复核并固定副本，不回写旧证据。
- `cleanup.json`：自建ADB映射/trace/采集进程/SSH采样已结束；保留测试消息和用户当前页，不关闭他人页面/会话。只有明确自有、idle且无其他持有者的测试Runtime才可按正式close回收；不关闭旧用户参考Runtime。

本机DSH持续执行，完成后整包交回报告路径与摘要。遇真实认证/解锁/权限阻塞写清具体现场并保留可接续状态，不假报已执行，不改环境绕过。主会话负责亲审证据并最终判定；完成提交/发出本任务书不等于复测通过。
