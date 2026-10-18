# Hermes Secretary 当前主看板

## 自主口径收敛 · 待用户追认

暂无。以下为已确认口径及关闭记录。

**AC-03 · 历史自主收敛已被PI-24调整：NM Thread同步不一致时不再以永久暂停作为目标行为。** 用户要求自动定位分叉点、新Thread首条接续旧NM Thread/原生Message ID、后续仅保存分叉内容。原5秒Notice/晚到重放仅为既有降级通路，成功分叉不得继续误报暂停；分叉无法安全完成时保留准确失败反馈，不自动覆盖或删除旧Thread。旧受控证据保留，不再以旧暂停场景单独设置上线阻塞。v4真实NM分叉22项对账通过；root发现的编辑后旧尾部显示已由v5正式读取修复、原A冷REST/隐藏UI及独立复审关闭。本项无剩余待追认决定；准确降级反馈仍保留。

AC-01已确认：Candidate用Notebook refs或Message Identity，二选一禁止混用；refs按Memory/Rule/Skill身份特化简述，不复写源正文。AC-02同源分页及配套文字已确认。先处理真正交付覆盖来源，最后关闭Candidate，未交付部分保留。

## 云部署已获放行（2026-10-19，执行中）

**最新优先级（用户2026-10-19）：先部署并运行云端服务，用户直接访问；同步收尾及门禁报告不挡已授权服务启动。Access已由用户完成配置，Mac匿名实测302至Cloudflare Access登录路径。旧Pi Mutagen允许关闭清除，但明确留到最后清理，不与上线争用。**

**入口已运行：** 云唯一backend PID3015797监听53446、专属Caddy PID3017385监听53448；公网Host经反代两SPA及health返回200，Tunnel业务route已接通。可访问`https://hermes.edgarzhong.fyi/`与`/dashboard/`，已告知用户直接验收。Alex48会话/6065消息逐项原生workspace.move完成，旧身份/原文/来源不变；study原生空库0/0。其余云服务保持；同步仍待实现整包root审阅/激活，模型/MCP只读核查继续，不能把当前入口可用扩大为整轮交付通过。实际入口/初始数据里程碑见ignored cloud-deployment交回与云`~/.local/state/hermes-secretary/deployment/{entry-ready,initial-data-cwd-ready}.json`。

**真实云端短验收已通过：** root隐藏IAB经专属SSH转发进入实际云反代，Alex显示k3-256k/high，切study仍保留48历史链接且无默认模型。唯一新测试Conversation `20261019_013755_07e1d7`实际返回“连接成功”，云正式API1次、17824输入/34输出、0工具，idle完成；测试页已离开至New Chat，指定云Agent仅回收此自有Runtime、保留历史。两MCP initialize/tools/list成功，kimi_search/kimi_fetch/notify可见。原生自动元数据256000兜底按正式目录事实补齐Alex context_length=262144，原生API热合并、PID不变，不改型号或Provider。以上不代签未完成DB回传或整轮独立门禁。

本轮唯一入口：`.autonomous/20261019-cloud-deployment/snapshot-index.md`；计划/两门禁/交付同目录。旧v5门禁只作原版本证据。公网域名已选`hermes.edgarzhong.fyi`；数据库快照周期已由用户确认每5分钟；Mac离线不影响云端、不无限积压/无界日志，最终经校验回传到本机两Profile各state.db冷态副本。

用户已完成两份SOUL编辑并明确“开始部署”；此前禁止云端操作的等待条件解除。两原文已冻结在ignored `deployment-release-20261019/`：Alex SHA `f260652e36b478687605721d8b7850a0a057769cc36aefb0aa1856e0129d56f1`，study SHA `8d88f3c9abea47dcc020245924be2862d87037c96bc29650ade32edd60a0148d`，不得再改写。Pi导入的48会话/6065消息库明确归Alex，study新库；共享云端`~/workspace`、两物理Home和Mutagen布局不变。

最新明确口径：保留`thread_sync_space`功能，但study当前不设覆盖，NM Thread仍同步自己的考研Space；study不设默认模型，也不配置新增Idle节省参数。Alex用原生Kimi Code套餐Provider，复用云端现有Key；默认必须为**独立K3-256k型号**（官方模型目录已核实ID `k3-256k`），不是K3加上下文覆盖；thinking High。Alex开启联合Idle Compact+Noting，空闲500秒、阈值128K（按窗口单位131072 tokens落值）。DeepSeek作为Alex可选模型、非默认，用户明确允许本机DS Key上云。Alex复用云端已有MCP，至少Kimi Search/Fetch和飞书Notifier；只接入/探测，不因此发送通知。

并行：`cloud_deployment_preflight`执行真实云部署、PM/Homes/模型/MCP/历史workspace及新入口；`deployment_ui_alias_build`窄补alex/study现图标和显示名、保护用户表现层并只交静态产物；`study_thread_space_split`受审21节点源码已接收，安装新study插件且保持自身Space，再授权个人提交。Root负责最终源/产物/权限/依赖与SOUL精确字节核对及实际访问；同步Agent单独实现并核接收端，SOP由文档Agent收敛。SSH整链用任务隔离sandbox禁启动open/浏览器等；所有界面验收仍仅隐藏IAB，不动屏幕。

## 历史：部署筹备等待阶段（已由上节放行覆盖）

用户最新确认：云端代码仓库 `~/hermes-secretary`；Profile Home `~/.hermes_profiles/Alex`、`~/.hermes_profiles/study`；两者共用 **`~/workspace`（单数，替换此前workspaces）**，与本机 `~/Desktop/Alex` 通过Mutagen同步。另增Profile Home同步：本机`/Users/edgar/.hermes_profiles`↔云端`~/.hermes_profiles`。用户确认数据库最关键，同意运行时通过SQLite一致性快照经原有Mutagen通道回传；配置和SOUL同步，其它运行态不回传，原运行数据库不作双向文件覆盖。具体备份频率尚未定，不擅自启动服务。前端只上传构建产物，不上传源码仓库；Alex复用当前主助手头像图标、study复习图标。当前已准备本机静态Home、官方插件及SOUL编辑入口，SQLite快照工具/Mutagen草稿/SOP整包已root亲审接收，用户编辑后按定案字节上传，禁止再替用户改写SOUL；尚未部署、上传、启动Mutagen或云端服务。另需沿原流程把Pi新增聊天增量同步进原生Hermes原导入库，不混入本轮合成测试数据库。两SOUL可编辑本机路径为`/Users/edgar/.hermes_profiles/Alex/SOUL.md`及`/Users/edgar/.hermes_profiles/study/SOUL.md`。

## study独立NM Thread同步目标（已改部署选择）

用户要求“Study那个profile，它的同步配置能不能单独拆出来？我希望它的NM同步往Default里面做”。按既有Thread同步语义拆分：新增个人Provider可选`thread_sync_space`，study保持现有`space: space`（考研复习）供Context Bundle/Recall/模型默认访问，自动Thread同步目标曾拟独立为`default`，用户随后明确撤回当前配置：保留可选功能，study仍继承自己的考研Space、不写override。未配置新项沿原space与既有receipt key，保持原生兼容；本次不迁旧Thread/Memory/收据、不修改任何Provider系统提示或SOUL，不扩大手动Memory写入授权。此项为用户后续部署配置调整，不回改固定v5门禁范围。

`study_thread_space_split`（6.1/high）负责个人Provider及相关定向测试/插件文档，禁止流水账及派生；root亲审后仅更新待部署study Home的配置与插件。原测试Profile/运行服务、云端和Mutagen不动；真实Default写入不作为此次定向测试动作。配置初始化生效，不做热切换。

## 当前目标与用户最新决定

**用户后续纠正已落实：仅创建Metadata错误需删除后重建，普通字段可经批准通过CLI修改。** 该范围纠正后的实际Provider提示定向1项通过（0.2秒）、Ruff及diff检查通过；两测试Profile磁盘已同步，无重启／NM写入／新模型调用。

第三轮固定v5本机Verification和Validation均已PASS（PI01–26范围）；继续收尾文档和新用户部署筹备，**明确尚未执行云端部署／Mutagen**。最高依据为最新产品文档及明确用户口径，技术规格也可错；不把未来愿景扩成当前开发。唯一轮次入口：[Snapshot Index](.autonomous/20261018-product-intent-review/snapshot-index.md)，计划/两门禁/最终判定在同目录。本机第三轮PI01–26实现与验收目标已完成；新部署筹备继续，云端运行和同步未验，不以构建、push或本机通过宣布上云完成。

- root抓目标、场景、体验、编排、review和最终判定；实现/调查/实测6.1/high，只有独立Verification用Astra/high。子Agent不派生，整包一次交回，禁止流水账；无必要全局工作允许等待。通用规则只在AGENTS。
- **静默方案最新决定（PI-21）：用户明确答“先保持现状，列为待决项”。** 不实施NO_REPLY新增句、过滤或“静默完成”展示协议；不改变deferred、未读/系统通知政策。无变化Reminder仍可能有业务汇报，作为明确待决/现状限制交付，保留原失败，不冒称静默已通过。具体提案仅在ignored `quiet-reminder-proposal.md`，不是授权。
- **Memory最新决定（PI-22）：废弃Skill方案，直接精简改个人NM Provider系统提示。** 仅Memory创建走窄入口，一次携完整内容与Metadata；其余操作官方CLI。普通Memory字段仍可经批准用CLI修改；仅创建时Metadata错误须批准删除后重新创建；既有失败对象不补写、不重建，partial/unknown不盲重试。前序窄包已完成；现按PI-24～26实施独立工具和NM Thread分叉同步，必要B实测已完成：真实模型唯一一次apply，独立同ID GET确认准确来源Metadata持久存在，自有资源0。旧A原失败保持。
- **PI-23：用户确认三类模型偏差不阻塞交付。** 错误归因、截断Search夸大完整核对/拼接原因、Noting补叙述未补来源身份均保留观察，不再要求为它们新增开发或补测。该确认不把原观察改成通过，不与Metadata实际落库/归档暂停提示独立缺证混同；Reminder静默仍按PI-21待决。
- **PI-24当前授权：** 统一“NM Thread同步”；History不一致自动分叉接续，只保存接续说明＋差异后缀，接续地址必须使用NM原生Thread/Message ID。模型实际创建带Metadata的Memory必须补证。新路径Provider英文句已由用户批准并仅替换此前长句，两测试Profile已按v4正式安装并安全加载；只做这两项及必要接线/验证，不扩开发范围。
- **PI-25独立小工具：** 用户拍板本机／云端统一 `~/scrips/`，不依赖Hermes／HERMES_HOME／插件安装路径。`metadata_live_acceptance`恢复实施独立NM创建工具（通用Metadata由调用方提供），不动Prompt；Thread契约／分叉两个Agent继续各自原任务，禁止重叠修改。PI-26已批准新路径精确英文，root已仅替换此前长句；两窄包已root亲审接收、统一加载，B单条真实创建和A实际编辑分叉已执行；不扩为旧对象修写。
- **NM Thread接续的必要实现细化（root决定，不冒称新用户口径）：** 多次分叉时，首条分别记录前一Thread，以及最后共同NM Message ID和其真实所属Thread，避免将祖先消息归属到错误Thread；尚无分叉后真实消息时等待，不创建只有接续说明的空Thread。保留既有远端Thread命名，Profile隔离证据仅按实际ledger/Space范围表述。
- **UIUX保护：** 用户现有布局、样式、动画、图标、Pin/拖拽及滚动为基线，只补状态/恢复接线，不接管Pin表现或整文件覆盖/挟带提交。
- **显示保护：** 只许自己创建的隐藏Codex IAB（iab、visible:false）。禁止桌面、外部浏览器、open/open_in_codex及任何显示/焦点变化。不碰用户恢复页/旧Tab；没有合规路由如实记阻塞。

## 当前版本与运行现场

| 对象 | 当前有效定位 |
|---|---|
| 主仓 | 源码候选提交 `0dc4232f597f0c36d070fd5eabd578366436fca3`（main，含E04读取修复）；本轮86文件已提交自动同步；固定v5两门禁已PASS，最终文档另行收束 |
| 独立UI | `../hermes-secretary-web`，功能候选提交 `652f487a536874e0405fae547941be36950cc144`；19功能整文件＋App/Sidebar两窄patch已提交。用户表现层11路径dirty保留，实际验收产物含该受保护overlay |
| 个人插件 | `../hermes-nmem-provider`，`codex/round3-local-completion`，候选提交 `3732f5503eccc0c97df0ea0238b140b9997e69df`，18文件已提交；后续运维快照工具/测试/文档提交`4d4a00e56316119ac2e66bc8ffe2c98ece64eaa5`已同步，既有Provider生产代码不变；个人内容不入公开核心 |
| 历史不变源码候选 | v3 set SHA `7de214d8…`保持历史；PI-24～26新分叉同步／独立工具包已root review，v5 set SHA `272fbb07…f00c2a`含E04读取修复，旧v3/v4不改写 |
| 本机验收后端 | 53446，v5验收时PID8471；收尾文档提交后的最终运行绑定见ignored `product-intent-review-20261018/final-service-binding.json`，官方PM Python 3.14.7/macOS arm64；原生 `-m hermes_cli.main dashboard --host 127.0.0.1 --port 53446 --skip-build --isolated --no-open`，不是serve握手页或Electron |
| 实际反代 | Caddy 53448，L12真实响应中唯一一次优雅停启后PID77413（旧53882）；v4仅backend安全重启，反代未再次重启。入口 `http://127.0.0.1:53448/`，Dashboard `/dashboard/`，共用后端 |
| 已加载产物 | Secretary `secretary-dist-v3` manifest `ac2ad3d842b0c37643588e66fb2618f68e8550e747355e153490e6658623373a`；Dashboard `cab847d3163f1916f956e033ee405b8cac7eecdd504f00eff1b45241c0922e4a` |
| 安全加载证据 | v5 `history-rewind-display-fix/load-v5/result.json` SHA `0c576016ba49dfe33378e28b98e8ad62feaf7b53d8819fe6cbe29599c3f17b11`；5库在线备份/完整性OK、旧消息/root及身份配置保持。原加载守卫、pyc误报及roster覆写瑕疵均如实保留 |
| 原服务保护 | 原round3 53445及5173/5174一直保留，本包未动。旧记录PID60820/wrapper60815、40290、41912只作历史定位，操作前另核，禁止全局serve --stop |
| 开发5098 | round3原配置 `gateway.model_code_skew_guard:false`；仅跳模型操作5098/503，不等于热更新或关闭其它保护 |

上述证据基址均为ignored `.hermes-dev/product-intent-review-20261018/`。SOP稳定入口在[README](README.md)，规则在[AGENTS](AGENTS.md)。不把本机成功写成云端/Linux/Tunnel/TLS/Access/手机通过。

## 实测环境与访问授权

两Profile位于 `.hermes-dev/validation-personal-20261018/runtime/profiles/{main-assistant,exam-assistant}`；terminal.cwd在Git root外 `/Users/edgar/code/Hermes Test/validation-{main,exam}-assistant-workspace`，防止根AGENTS污染模型上下文。两者Noting/Scheduler及联合Idle100000 tokens/5秒开启，模型容量262144保持，DeepSeek原生custom/chat_completions；不接Codex App Server/Proxy。

- main：Default和“考研复习”Space只读，自动Thread archive=false；不读exam Hermes Profile。
- exam：用户现有“考研复习”Space（安装selector `space`），可按具体授权写，自动Thread archive=true。Memory提案/修改不算批准，禁止事实写入USER或其它长期存储。
- 两SOUL是可部署身份，已移除测试背景；测试权限在各仓外workspace AGENTS，确保冷恢复/压缩后仍可见。每条普通user message必须附原完整测试前缀、真实带时区时间和600秒一天；不改系统时钟，不将oracle/UID/预期答案灌给模型。
- v3历史安装Provider `96f17766…`、helper `75d8dca1…`、76行Skill `89cb013e…`曾同步两测试Profile；真实A模型未读Skill、直接CLI创建，官方GET确认无hermes_provenance。PI-22包已root亲审接收：PI-22时点Provider `f14d2cfe…`及无Skill注册入口曾同步两测试Profile，原Skill文件/auto_load/本插件external_dirs已撤销，其它配置/SOUL保持；4项定向检查通过，helper未改。以上为历史PI-22状态；现v4已正式安装重启，真实B模型独立入口创建及同ID Metadata持久回读通过，未改写旧A失败。
- Default不写，不触碰旧partial Memory `1805d328-eec9-4082-b0d2-e1051c1d6eac`，不清他人排期/历史/资源。所有凭据/原始私人材料仅本地ignored。

## 唯一当前任务看板

| 工作 / Owner | 状态、剩余与完成条件 |
|---|---|
| 产品意图Verification / `product_intent_reverification` Astra/high | 53项独立判据，ad4/v2/v3源码及影响核对已交回，v4全范围30项判据已独立核；批准句实际B请求root证实仅一次，加载／Metadata／Thread真实证据E01–E03关闭。E04读取窄修复已亲审／70不同定向节点通过，v5实际REST/冷AX旧尾部消失、前缀及新UA保留，A33026cc0正式close资源0；新Astra25项全范围复审已PASS，加载/冷页/资源原件55项核对，后续文档收尾不重跑旧大套 |
| 部署/Reminder / `local_deployment_browser_validation`＋root必要UI执行 | L09/L10/L11/L12整包收口，4ordinary/2once/2Conversation/1次Caddy重启；全部自有运行资源0，F04及真实断线恢复已由Astra核对。两张L12截图均为恢复画面，断线由实际AX/事件证明，不混称。worker现筹备新Alex/study静态Home、SQLite快照工具、Mutagen草稿与新布局SOP；只限获授权白名单，不部署/激活同步/改SOUL或Alex历史库 |
| E02真实来源附件 / `metadata_live_acceptance` 6.1/high | A三输入已完成，唯一Memory `0c75569e-ed8c-40bc-b7ed-292e619cf6f9`正文/标签/Space正确，但模型走CLI创建、helper调用0，官方GET来源Metadata缺失，NOT_PASS_SOURCE_ATTACHMENT；原失败/旧对象保留，自有运行资源0。三次正式Noting child完成，第三父压缩20→9；实际全Messages型，refs先结算分支未新增覆盖；旧Candidate补叙述未补最终批准/结果来源身份，作为模型偏差保留。PI-22/后续纠正历史保留。当前独立工具已root亲审接收：~/scrips/nmem-memory.py与源码SHA256 256af367…ed1a9一致，标准Python -I -S／仓库外／无Hermes环境／通用Metadata受控11项通过，精确批准句1项通过；旧wrapper薄转同一创建实现。PI-26仅批准句已写源码，其它Prompt保持；Thread两包v4已统一加载，B单条真实模型唯一apply成功；独立CLI及GET核正文/标题/唯一标签/Space与真实accepted来源准确，自有资源0。报告§12及scenario-b/single-create-manifest.json记录范围；这是点名入口功能测试，不冒称自然路由 |
| Q03已由PI-24改为NM Thread分叉同步 / nm_thread_fork_impl＋root | root已亲审同步owner／Provider出口／CLI分页／安装接线及pending先落盘、unknown只读确认、祖先锚点与header计数。原39项受控通过；root发现合法Space名称/别名误拒，窄修后6项定向通过（不重跑39），正式CLI解析真实ID后仍严格核Space，Default清ambient保持。两批依各自manifest复用。已统一安装；root真实编辑第3条user后，正式同步新Thread为system接续头＋编辑UM＋新assistant，原生锚点正确、共同4条未重传、旧Thread6条不变、pending清空。root同页及冷页仍见旧尾部，正式REST预过滤新退休副本导致旧compacted别名复活，local_deployment_browser_validation已完成SessionDB展示读取窄修，root亲审／70不同定向节点通过，v5加载／原A冷页复验通过；不将底层通过代签UI。A已按正式close成功，资源全0；后续增量仍仅受控覆盖 |
| 独立Validation / `final_user_validation` 6.1/high | 全新独立六节计划15目标/18母场景已root过目收口，最多4条短普通输入，晚到核对另1须明确release，新增Reminder0。复用100k/600秒及实际包，不重跑原生全套。该Agent唯一一次hidden IAB路由检查失败，无reset/换浏览器；正式执行时独立设计动作，root隐藏页薄执行、保存AX/PNG，Agent独立判定并明确非亲操。v5正式Validation已PASS：15目标/18母场景，89原件指纹。FV02唯一main输入/1模型/0工具/0新增排期或内容条目；正式close资源0，E04按同源冷UI原件接收不重复操作。最终SOP/版本/DP01–05文档delta窄核已通过（validation §6.1），未增加产品动作 |
| 静默 / 用户明确待决 | 保持现状，NO_REPLY提案不实施，不把原安静性失败改成通过或伪授权；最终明确限制 |
| 新部署筹备 / `local_deployment_browser_validation`＋root | [docs/cloud-deployment-sop.md](docs/cloud-deployment-sop.md)依最新Home/共享workspace/静态产物/Mutagen与DB一致性快照口径改版；整包已root亲审接收：28配置/插件文件指纹与权限相符；独立快照工具9不同SQLite节点/检查通过，接收端全包验证后current/previous两槽。两用户SOUL/历史库未改，频率未定，云端与同步未执行 |
| Pi新增聊天 / `pi_native_history_increment`＋root | 原库增量79条，48会话/6065消息，旧数据身份保持；Alex当前schema白名单兼容副本已核完整性/History和实际native resume。旧sessions.cwd优先于新配置，正式部署前需原生workspace move到共享目录，原cwd保留origin_json；未对发布Alex库执行move，不能声称当前已满足新workspace续聊 |
| 最终集成/提交 / root | 亲审返回变更及上下游，版本与证据绑定，保护用户UI dirty和个人边界；范围内阶段commit自动push，最终release/门禁/产物分别记，不以push代验收 |

## 已接收证据与实际边界

| 范围 | 已核事实 / 不可扩大结论 | 唯一报告入口（上述ignored基址，另注除外） |
|---|---|---|
| 首页Profile/侧栏 | root真实切exam再main，全局会话与owner图标保留；Dashboard sessions子路径及刷新可用，telemetry横幅未选择。Pin最新表现未改，不拿旧截图代签新交互 | `local-deployment-browser-validation.md`，`local-deployment-evidence/root-home-exam.png` / `root-dashboard-*` |
| L09正常冷提醒 | `conv_e732ee1ad1d3450fb0ff8859fe517be6`：登记后正式回收，到期宿主恢复，同步首页Running；430；回收冷开9Thinking/3成功工具/结果。工具毫秒级，原断线窗口未覆盖。关闭尾部poller首采失败保留，复采rc0、全资源0 | 同报告；`L09-final-readonly-resources.json` |
| L10真实中断冷恢复 | `conv_a3c611b55dbe4cefbb8ee081e6a1c224`：cold到期，中途接入见首Thinking流式/Stop；首工具成功1830，第二运行时真实UI Stop，持久interrupted。close后冷开Thinking/Success/Interrupted及explicit stop详情6.28秒保留，全部自有资源0。首Streaming工具回执在主会话，但未单独保存该首AX，不能伪造原截图 | 同报告；`root-L10-*` / `L10-*-private.json` |
| L11/L12后续可用/断线 | 同L10会话续做真实有限校验0.06秒完成；首Thinking Streaming已保存。L12无工具状态核对，精确新accepted UID/连续seq真实响应时重启Caddy；同页断线→恢复完整答复，未重发，旧Thinking/工具/Interrupted仍在。仅一次反代重启，不声称backend crash | 同报告；`L12-response-trigger-proof.json` / `root-L12-*` |
| Main自然100k | 101029 tokens、约5秒idle，第一次驱动提前close使父abort，失败保留；同Conversation正式恢复后父committed/child完成。33普通Turn，Main46/Noting8 Provider完成；有原话归因过度声称，不能签完整Read/分页 | `main-natural-idle-live.md` |
| Exam自然100k | 102871、idle5.0246秒，父committed72→12、child完成；29普通Turn，Main41/Noting5＋summary；Search不等于完整Read，部分解释过度声称保留。自有资源0，58收据仅本地指纹非远端逐条对账 | `exam-natural-idle-live.md` |
| 模型可读Notebook | 双自然Noting task/工具/Framework有完整内容和可信可读覆盖，不给模型Snapshot/Pointer/Coverage审计ID；无完整Provider出站wire，不签所有控制面/cache-parity | 两自然长包；两自然长包的模型面原件及本轮verification索引 |
| NM自主检索 | 新main Conversation陌生546字符目标自主skill/search/show、回答准确；自动Recall0pointer，不能签pointer驱动首次精读。只读CLI完整前缀0/自然问题5条对照仅支持输入敏感性，不删用户前缀/改生产query，研究结束 | `recall-first-read-live.md` |
| 既有600秒提醒 | 暖态NM读/比较/续排、正确desktop冷窗17:52:05→17:52:07宿主恢复、实际读NM/比较/续排；旧错误source=web失败保留。无变化仍有业务汇报现按PI-21保持待决；自有资源/未来排期0 | `repaired-reminder-live.md` / `quiet-reminder-contract-probe.md` |
| F01/F02/F03/output-cap | 可读覆盖、冻结父前缀、退休工具在repair前拒绝、仅限本次请求限额不压冻结历史；71不同节点及检查，按不变接缝复用，不外推真实Provider全部超限分支 | `repair-noting-protocol.md`及verification索引 |
| D01执行内核隔离 | 同stored ID/共享workspace旧反例B读A变量41；修复五文件11d9e626，44不同节点＋检查；两真实Profile execute_code成功/按owner回收。非remote/跨平台/宿主异常残留扫除 | `repair-kernel-profile-scratch.md` / `load-profile-isolation-repair.md` |
| 已批准Prompt/Candidate | S01/Q02/History精确提案19P；Candidate来源二选一52P含31正式child，旧10生命周期按不变路径复用。真实新交付/结算样本在Metadata包中验证，不把受控证据冒充模型行为 | `authorized-prompt-sync.md` / `candidate-source-contract-sync.md`及verification索引 |
| F04与状态接线 | 当前Turn独立完整输出投影＋原子水位，accepted/carrier UID owner，既有messages.display_metadata终态CAS，当前输出真实UID去重，API增量兼容。后端21＋8＋契约，UI21P/52选择skip，八表现文件SHA保持；实际L10由Astra核后F04关闭 | `websocket-backend-state.md` / `websocket-state-recovery.md` / `verification.md` |
| Q03 | 最小通用反馈/原生token/冷读事实，跨Profile去重缺陷2F→5P，22不同新增节点及安装原失败1P、冻结检查；不用受控结果冒充实际Notice。权限限制与AC-03仍有效 | `archive-pause-feedback.md` / `archive-pause-visibility.md` |
| 本次一次大型检查 | ad4阶段冻结10 checks为9P/health1F、UI696P/3F/1skip；health组织超标原2节点＋检查修复，UI原3＋新2节点/typecheck关闭，均root审v3，不重跑大套 | `independent-reverification/`及各返回报告 |
| 历史全量 | 混合工作区Python59466P/321F/71E/1421skip/1超时，3575.6秒；旧基线299F复现不是豁免。原UI603P/tsc仅当时版本。后续只定向关闭，不把历史全绿化 | `.hermes-dev/deploy-readiness-20261018/suite-triage.md`及failure-index/main-audit |

## 下一步与结束条件

1. 固定v5两独立门禁均已PASS，E04原A冷显示与安全加载关闭，FV02纯交流一次真实输入/一模型请求/零工具及新增内容或提醒、精确close资源0。不重复100k、600秒、Memory创建或大型套。
2. 新部署筹备整包已root亲审接收，SQLite快照工具/接收两槽及9不同真实SQLite节点证据接受；28静态文件指纹/权限和实际测试源码绑定已核。数据库原文件不双向同步，不回传其它运行态。只准备不启动；UI alex/study图标/显示名仅最小提案，正式构建前处理。
3. 最终版本/产物与文档已收束，独立Validation的SOP/DP文档delta窄核已通过，不重复产品动作；收尾提交后仅校正本机测试服务版本绑定、保护原round3。按delivery-evidence-review已更新[final-delivery](.autonomous/20261018-product-intent-review/final-delivery.md)。保留PI21待决、PI23非阻断观察及云端/平台未验。
4. 用户先编辑两份SOUL并定案。收到正式部署放行后，才按最终字节核SHA上传、原生迁入历史会话cwd、配置生产参数和备份频率、启动云端服务/同步；此前不触云端或激活Mutagen。

## 历史入口与防重复

第三轮初始冻结、二审NOT PASS及旧分包留在 `.autonomous/20261016-round3-secretary-nm/`，不重开已交回任务。当前全范围报告在 `.autonomous/20261018-product-intent-review/`；更早功能/专项证据经README索引。此次整理前主看板完整原文留ignored `CLAUDE-before-closeout-sync.md`，v3固定副本也保留其捕获时点文档；仅本页维护当前动态状态。

旧已接收功能不重新立项：Notebook局部UID/分支来源、Noting真实Running计时、完成高亮、冷Context/Session Total估算、历史恢复指引、Files固定default、跨Profile列表/Pin顺序、普通5秒提示、5098开发开关、双SPA/4001/标题。各自验证范围和未验平台以原报告为准；稳定入口在README，规则在AGENTS，不能拿旧测试代签较新变化。
