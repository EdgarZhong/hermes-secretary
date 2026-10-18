# Validation：20261019-cloud-deployment

## 1. 结果概览

验收者：独立 `cloud_release_validation`（6.1/high，无主会话历史）；日期2026-10-19，Asia/Shanghai。按真实用户验收及自主运行技能，从 [Snapshot Index](snapshot-index.md) D01–D14、[部署SOP](../../docs/cloud-deployment-sop.md)、06 §0.7–0.8及08契约独立提取用户目标；`plan.md`仅作定位，不作为预期来源。

本报告为**最终原件复核报告**：完整计划已由主会话过目，root按§3集中执行的一次只读UI包及同步最终整包均已独立接收；主会话已亲审接收VE02/VE03结论。UI结果见§4.1，同步结果及采样限制见§4.2，当前状态以§3覆盖表、§5和§6为准；§4前半保留历史初审记录，不再表示等待整包。冻结文件实际名为`baseline.txt`：冻结提交`d215922256a479f7cb7346cef59a234bb71dd1b0`，产品源码继承`c80e0d02b51ec2ddfe5feced776c842480f84516`；Provider增量`a7225f6075c0ead8cad559db93be8da5525e09e8`；UI功能提交`d5b20aab1fb5e7ecf1c3cf10ed476b5ab7b22c99`与另行保护的用户overlay。运行版本以实际Core/插件/产物原件绑定，不以本机HEAD替代。

用户目标是尽快在Access保护域使用双SPA、Alex精确身份/历史/模型和study独立配置，同时完成workspace、配置/SOUL与每五分钟DB快照到Mac两个冷态state.db，Mac离线不影响云端。**服务已运行供用户直接访问（D14），本报告未关闭不构成停服前置。** 最终原件复核结论为**门禁未关闭 / PARTIAL_ACTIVE_WAITING_TCC**：云回环真实模型、冷历史、Files返回、Profile来回已通过；配置同步、300秒定时与实际三库冷镜像、隔离快照传输暂停/恢复的代表结果已通过。workspace真实Desktop权限阻塞；公网仅到Access登录页，登录后SPA/API/WS未验；study无会话，侧栏毕业帽尚未实际呈现。不能据此全轮PASS或停服。

## 2. 环境与准备

- 云Ubuntu 24.04/x86_64；Core `/root/hermes-secretary`，官方PM Python3.14.7与冻结锁；两Home为`/root/.hermes_profiles/Alex`、`study`，native owner为`alex`、`study`。共享`/root/workspace`，Mac工作区`/Users/edgar/Desktop/Alex`。
- 正式入口`https://hermes.edgarzhong.fyi/`与`/dashboard/`。已有实际应用UI由root自己的隐藏IAB，经专用SSH forward `http://127.0.0.1:53458`进入云真实Caddy；经过云反代和后端，**未经过公网Access登录链**。
- 采样时点唯一backend/proxy PID3015797/3017385、两unit active/NRestarts0。PM/进程只是该次采样，不承诺PID不变。Secretary439文件、Dashboard67文件完整SHA绑定，实际HTML会注入token/重写prefix，不要求等于dist index。
- 数据：用户两SOUL原字节；Alex初始Pi48会话/6065消息；study新库；root唯一测试Conversation `20261019_013755_07e1d7`。用户后续合法使用会增加总数，对账须保留原48集合和新增数据，不把总数固定为48/6065。
- 操作边界：本Agent只写本报告与ignored `validation-evidence/`，产品代码只读，不CUA/桌面/外部浏览器/open/open_in_codex，不改变显示状态；不新建模型输入、Conversation、Reminder、Memory、NM或飞书写入，不动同步激活、不停服务。新UI动作只集中交root以其隐藏IAB执行，本Agent独立判定并明确**非亲操**。
- root补充公网实际证据：唯一隐藏IAB直接进入正式域，显示Cloudflare Access“Log in to hermes”及Email/Send login code；未填邮箱、未索OTP、未登录，已关自己的隐藏登录页。不得为验收另向用户请求登录、索OTP或把登录当停服前置。
- 复用固定v5不变接缝，不重跑100k/600秒/Memory/Reminder或昂贵全量。同步实现提交`5c7fad173e0b60ff55b9d2183e58499ceea93915`、状态文档提交`892c6bf20399d43ecc51f829a08ff9b19be2f120`；两端helper完整SHA `8e1ecc2de07f71a695588c7c6036d985536ffc7895558229be09d5baba0e97a4`。19不同针对节点为坏包/忙库等机制补证，实际落库/传输另核E09–E11，不重复或在生产故意造坏库。

原件基址 **E**=`.hermes-dev/product-intent-review-20261018/deployment-release-20261019/`；**U**=`.hermes-dev/deployment-release-20261019/ui/`。私人正文/凭据不入报告；只保存证据路径和指纹，入口`E/validation-evidence/evidence-index.json`。

| 证据 | 原件（相对E，U另注） | 支持边界 |
|---|---|---|
| E01 | `access-probe/mac-anonymous.json`；`cloud-deployment/33-public-access-and-probe-metadata.result.json`；`browser/public-access-login-observation.json` | 匿名302与真实公网登录页；非登录后SPA |
| E02 | `browser/{alex-home,study-home}.ax.txt`、`root-browser-observation.json` | 云回环真实首页，精确model/reasoning、48链接及study无默认 |
| E03 | `browser/k3-probe-{sent,progress,complete,left-to-new}.ax.txt`；`cloud-deployment/28-root-model-diagnosis.result.json` | 唯一实际输入到“连接成功”，原生kimi-coding、1API/0工具、离开测试页 |
| E04 | `cloud-deployment/32-final-runtime-inspect.result.json` | 自有runtime0/lease0、历史2条保留、MCP工具暴露、原四入口保护 |
| E05 | `cloud-deployment/{26-config-model-mcp-validation,27-context-fact-merge}.result.json` | SOUL/配置/Space/Idle/可选模型，精确型号及目录窗口补齐 |
| E06 | `cloud-deployment/{23-verify-data-and-activate,31-final-runtime-retest}.result.json` | 48/6065对账，cwd move后原身份不变、真实REST/跨owner404、Files cwd与静态资源 |
| E07 | U `release-binding.json` | 双dist和用户overlay构建输入绑定；非真实图标视觉 |
| E08 | `browser/{old-pi-loaded,files-loaded,files-returned-to-pi,validation-study-home,validation-alex-restored}.ax.txt`；`browser/validation-{profile-menu,study-home,alex-restored}.png` | root按独立计划一次只读UI包；旧正文/Files返回/双Profile来回/49链接，图标视觉的实际边界见§4.1 |
| E09 | `sync/activation/{installation-and-commit,static-prealignment,scratch-result,production-sessions-final,cloud-final}.json`及`scratch_matcher.py` | 最终版本/两端安装绑定、8配置与1包运输、非SOUL预对齐/冻结SOUL与排除项 |
| E10 | `sync/activation/{first-mirror-reconciliation,final-reconciliation,real-repeat-idempotence,mac-cold-originals,cloud-installation,launchd-final}.json`及`{receive_and_check,final_check,db_fingerprint}.py` | 实际三库字节/逐表对账、initial原inode、同包幂等、真实timer与launchd落库 |
| E11 | `sync/activation/offline-{cloud-publish,recovery-transport}.json`、`post-offline-receiver.json`、`offline_recovery.py`；`sync/{commands-and-results.json,mirror-*.log}` | 暂停本任务快照lane、云独立发布、恢复追上及自动接收；既有19节点补拒绝/恢复机制；非真实Mac关机 |
| E12 | `sync/activation/mutagen-tcc-diagnostic.log`、`production-sessions-final.json`、`old-sessions-preserved.json`；`cloud-deployment/35-original-pi-readonly-resources.result.json` | workspace外部TCC阻塞、旧五session保护、原Pi idle runtime保留而非误报资源0 |

## 3. 用户目标与场景覆盖

下表“当前执行结果”为最终接收状态；预先独立建立的目标、场景和数据选择依据保持原样，采样偏差及未验范围另在§4.2明确记录。

| 目标编号及冻结依据 | 完整场景编号 | 场景类型与起点 | 数据/顺序选择依据 | 当前执行结果 |
|---|---|---|---|---|
| G01 D11/D14、06§0.7：受保护公网双SPA/API/WS | V01 | 匿名→Access→已登录双SPA→Dashboard子路径刷新 | 两SPA及两API/WS前缀均适用 | 匿名/登录页通过；登录后未执行 |
| G02 D01/D06/D09/D10：Alex身份、精确默认、生产配置 | V02 | Alex New Chat | UI选择与原字节配置互证 | 文字/模型/推理及Alex人物图标通过，Idle仅配置 |
| G03 D02/D03、08§1：Pi历史可读、身份/source/cwd保留 | V03 | 已迁cwd的原Pi会话冷读 | 原48集合全量对账＋一条实际读取，禁止续写 | 集合/REST/旧正文冷UI通过 |
| G04 D04/D05/D10、08§1：study独立无默认、列表保持 | V04 | Alex→study New Chat→Alex | 空study与已有Alex历史属不同合法数据类 | 来回切换/49链接/无默认通过，study侧栏图标未验，Space仅配置 |
| G05 D06/D12：实际KimiCode精确型号输入到输出 | V05 | 唯一获授权短纯交流 | 一次最小调用证明不可由配置替代的Provider链 | 通过（复核root原件，非亲操） |
| G06 D07/D08：可选DeepSeek和MCP暴露、不误发送 | V06 | 原生模型/工具列表 | DS非默认；只握手不通知/额外模型调用 | 列表/握手通过，不声称工具业务输出 |
| G07 D02、08§3：Files固定default、共享工作文件 | V07 | 旧chat→Files→原chat；工作文件跨端 | Files归属与同步分开核 | cwd API/真实UI与返回通过；workspace实际同步TCC阻塞 |
| G08 D01/D02/D07/D13：安全配置/SOUL同步 | V08 | 预对齐后激活三lane | allowlist与秘密/DB/runtime是不同数据类 | 配置/SOUL lane通过；workspace独立TCC阻塞 |
| G09 D13：每5分钟包最终落两Mac冷state.db | V09 | 活云库→timer→完成包→冷库 | 两Profile均须到实际DB，ZIP到达不算完成 | 通过，真实三库及自动接收；一次实际timer采样，长期未验 |
| G10 D13：坏/半包、忙库拒绝及恢复 | V10 | 已有known-good与冷库→无效输入/忙目标→恢复 | 传输不完整/校验错误/活连接分别处理 | 机制拒绝/恢复＋真实有效包/幂等通过；未在生产注入坏库 |
| G11 D13：Mac离线云继续、有界、重连追上 | V11 | 先成功同步→离线跨周期→重连 | 时序须保留，connected不证明内容成功 | 隔离snapshot lane暂停/恢复代表链通过；真关机/整网/多周期未验 |
| G12 D11/D12/D14：并存、显示保护、精确收尾 | V12 | 服务运行且root短测结束 | 用户资源与自有资源分开；旧Pi最后清 | 服务/自有回收/四入口/旧session保护通过；workspace收尾与旧Pi最后清理待完成 |

典型完整旅程V01→V02→V03→V04→V05→V07，可靠回传旅程V08→V09→V10→V11；V06/V12横切。关键顺序是切Profile后旧列表仍在、旧历史可冷读、无默认study不污染Alex、先有有效快照再受损/离线并恢复。本轮不穷举模型或重复既有昂贵边界。D09生产参数只核配置，本轮不等待500秒触发模型压缩，不声称实际阈值行为已验。

**历史集中执行计划（主会话已过目，原计划保留）：** 第1、3、4项的原件接收已完成，结果分别见§2、§4.1、§4.2；第2项公网登录后仍未执行，第5项workspace后续收尾/旧Pi最后清理仍待条件满足。以下将来时文字是原执行前计划，不是当前待收整包状态。

1. 先独立接收E01–E07原件及指纹，不新增产品动作。
2. 公网如无已存在的合规登录态，V01登录后保留未验，不找用户索OTP或另开浏览器。用户自行直接访问不能自动当作取证完成。
3. root若适宜补UI，只需一次只读包：用自己的隐藏页打开原Pi链接，见冷Timeline及owner；进入Files见共享目录后Back to Chat返回同一owner/route；New Chat切study留头像/模型空状态截图，再回Alex留头像/精确型号/high。可在已有合法公网会话合并完成，否则SSH回环只签回环。不给用户旧页加操作、不发送消息、不真正创建Conversation。无合规接口则保留未执行。
4. 同步执行者整包交回后，本Agent只核实际间隔/完成包→两冷DB、SOUL不变、秘密排除、半包/忙库拒绝、离线跨周期云运行与固定包/有界状态日志、重连最终到达；不抢操作、不复跑机制测试。
5. 新发现写§5，不改产品源码，不停已供用户使用的服务。旧Pi精确清理由root在所有新链路成功后最后安排。

## 4. 详细场景与执行结果

执行时间口径：本节为2026-10-19本Agent原件复核，不是重做产品操作。E02 root首页观测时间为2026-10-18T17:35:50.883Z；V05正式输入接纳为上海01:37:59、完成01:38:06；V01公网登录页为2026-10-18T17:50:12.280Z。其它原件没有单独执行时间字段的，保留其文件指纹/mtime作为收件定位，不捏造操作时间；未执行场景的执行时间不适用。复用root薄执行非本Agent亲操；后续调度/断传采样偏差见§4.2，禁止新增写入使Space/Idle实际触发保持明确未验。

**历史初审记录：以下V01–V12保留首次判断和预定步骤，粗体“未执行／待整包”等均是当时状态，不能作为当前摘要。UI相关结果由§4.1更新，V08–V11同步相关结果由§4.2更新，最终当前状态见§3、§5、§6。**

### V01 · 公网Access与双SPA

起点为本轮已部署服务；输入为`/`、`/dashboard/`、`/api/health`、`/api/ws`、`/dashboard/api/ws`。预期匿名跳Access，合法登录后两SPA/子路径刷新/同源WS可用且没有第二交互登录。E01 Mac根入口302→Access，云既有出站路径五入口也302；root唯一隐藏IAB亲见“Log in to hermes”及Email/Send login code，未提交邮箱或登录。**匿名保护/真实登录页通过；登录后未执行**，不得以回环/Host200代签。后续不额外向用户请求登录。

### V02 · Alex身份与精确默认（历史初审，后续见§4.1）

起点为`new?profile=alex`；操作为只读Profile/model/reasoning并对照Home原件。预期Alex、既有主头像、独立`k3-256k`/high，SOUL精确原字节；联合Idle500s/131072、原生冲突idle=0。E02 AX明确三项文字，E05 SOUL SHA精确匹配D01，生产参数符合。正式目录窗口262144已经原生API热合并，型号/Provider/PID不变；原自动兜底256000仍保留其事实。**文字/模型/推理与SOUL通过；头像视觉未执行，Idle仅配置补证**。AX泛化image不签图标视觉。

### V03 · 旧Pi历史到可读结果（历史初审，后续见§4.1）

合法起点为已原生move的原48条集合，不发送历史续聊。预期48/6065原文/Ref/UID/root/binding/source保留，运行cwd统一共享目录、Mac来源cwd仍在origin_json；实际冷读可见正文，study不能读同ID。E06：32表对账、48/6065、integrity ok/FK0，除四列cwd/git与heartbeat外原数据不变；真实历史REST200、返回1消息UID属于原session、study同ID404。E02各见同48链接。**全集合/API通过；旧Pi正文冷UI未执行**。不把1条API当6065条逐条UI读取。

### V04 · study独立与跨Profile衔接（历史初审，后续见§4.1）

步骤为Alex New Chat切study，再拟回Alex；预期列表保留、study不带Alex/DeepSeek默认或新增Idle、自己的考研Space且无override；回Alex仍原值。E02 study AX显示`Profile: study`、`Model: Model`、`Reasoning: Reasoning`且与Alex相同48个Pi链接。E05 study model/agent为空、Noting开启无新增Idle，NM space=space/archive=true、无thread_sync_space；Alex仍default/archive=false。**切study/列表/无默认通过；回切和图标未验，Space仅配置补证**，无study模型/NM写入，不冒称新Thread实际写入已验。

### V05 · 唯一KimiCode实际回复与结束

root隐藏IAB SSH页唯一Conversation`20261019_013755_07e1d7`，输入是授权测试前缀加只回复“连接成功”、禁止任何工具/文件/记忆/提醒/委派。完整原输入在E03，绝不再发送。预期一次真实原生KimiCode精确型号回复后idle、离开页、只正式close自有runtime且保留历史。E03实际AX为“连接成功”、idle、k3-256k/high；正式日志provider=kimi-coding，API #1输入17824/输出34、总17858、tool_turns0、text_response stop。E04目标runtime0/lease0、user/assistant两历史保留。E01附带stored输入15776属于另一存储读数，不覆盖实际API17824，也不据此推断第二调用。**通过，root实际薄执行、本Agent独立复核非亲操**。无Memory/Reminder/Notifier工具副作用；不外推长期可靠性。

### V06 · 可选DS和MCP接入

起点为云原生model options及MCP initialize/tools/list，只读、不切模型或调用Notifier。预期DS可选非默认/authenticated、Kimi Search/Fetch与notify暴露、默认仍Kimi。E05/E04实际列表符合，两MCP connected；原生provider独立解析到kimi-coding/anthropic_messages与deepseek/chat_completions，只报告Key非空不输出内容。**列表/握手通过**；无Search/Fetch实际业务、DS模型或飞书发送，未声称这些最终输出。

### V07 · Files与共享Workspace（历史初审，后续见§4.1–4.2）

预定步骤为已有Pi chat→Files list→Back to Chat回同owner/route；另以同步执行者合法工作文件双向到达补证。预期Files始终default、共享目录且不污染chat owner。E06三Profile default-cwd均`/root/workspace`。**cwd API通过，Files UI返回和实际跨端内容未执行**；相同cwd字符串不是文件同步结果。

### V08 · 配置/SOUL安全同步（历史初审，已由§4.2更新）

起点为已预对齐且SOUL精确D01指纹；只复核同步执行者三lane实际包。预期workspace双向、配置allowlist two-way-safe、快照单向分离；合法非凭据配置双向到达/冲突准确；SOUL不为测试改写；.env/raw DB/sidecar/运行态排除，云Kimi/MCP/NM凭据不回传。**未执行，待整包**；connected/草稿不能当成功。

### V09 · 五分钟定时快照到Mac冷DB（历史初审，已由§4.2更新）

起点为活云主库，禁止新增模型造数据。复用两个实际周期生成记录→固定完成包→Mutagen→全包校验/两槽→两Mac冷state.db，核各自SHA/SQLite/原48集合及唯一合法新增输入。预期云300秒独立执行不等MacACK，最终到两state.db，SOUL/config不由包覆盖；跨库不承诺同时事务。**未执行，待整包**；helper19节点或ZIP到达不能替代实际冷库。

### V10 · 半/坏包、忙库拒绝和恢复（历史初审，已由§4.2更新）

起点为已有known-good和冷DB，复用真实SQLite机制及正式接收代表拒绝/恢复原件。预期半包/校验失败/活连接/锁冲突不改变既有槽和冷库，恢复合法冷态后可应用；中途失败准确记已应用集合。不得为验收启动生产Home为第二写端或删sidecar强凑冷态。**未执行，待证据**；本Agent不新增故障注入，不争用激活。

### V11 · Mac离线与重连（历史初审，已由§4.2更新）

保留顺序V09成功→执行者仅断本任务链路→跨实际timer周期→观察云health/服务/完成包更新/有界目录日志→恢复→当前包到两冷DB。预期云不崩、不积无限历史包，恢复后冷库与接受包相等；锁屏或connected不等价离线/完成。**未执行，待整包**。本Agent不主动断网或停其它同步/云服务。

### V12 · 并存、显示和资源收尾（历史初审，后续见§4.1–4.2）

预期新唯一backend/proxy运行，旧Tunnel四入口保留，root短测只精确回收自有runtime、历史保留；旧Pi最后清理，不为门禁关服务。E04两unit active/NRestarts0、原四入口byte-preserved；E03/E04短测完成/目标资源0/其它runtime未动。**已观测运行并存/回收通过，实际同步收尾及旧Pi最终清理待证**。本Agent全程无浏览器/桌面调用。

### 4.1 · 经主会话过目后的只读UI集中执行增量

输入/环境：root自己的隐藏IAB Tab9、同一SSH云反代`127.0.0.1:53458`；无新增模型输入、真正创建Conversation、Reminder、NM或文件写入。本Agent仅读原件并用本地view_image检查三PNG，不CUA。原操作时间未另设字段，收件时间/指纹在E08索引，不臆造精确执行时刻。

1. V03：冷goto原Pi043 `chat/20261011_223117_07a84a?profile=alex`，初始loading后实际Timeline含4个You与3个Assistant容器及正文。完整标题、owner/route符合原历史；不是仅标题/链接或占位加载。旧历史**冷UI通过**。
2. V07：Files加载breadcrumb `workspace`，显示`This folder is empty`；Back to Chat恢复完全相同Pi route、owner、标题，Timeline仍在。与E06固定default-cwd互证，**Files进入/返回通过**。目录当前空不证明Mac文件已双向同步，workspace内容结果仍独立待证。
3. V04：New Chat切study，Model/Reasoning空；再回Alex显示k3-256k/high；两AX精确同49条chat链接，其中原Pi48条＋唯一已授权K3测试1条。原48条无丢失、不污染默认。**双Profile往返与列表通过**，并未因为New Chat导航真正建新Conversation。
4. V02/V04视觉：Alex截图侧栏与选择器可见沿用的轮廓人物图标，符合主助手既有图标；study截图选择器也是通用人物图标。当前全部49条会话owner均Alex，study无会话，所以截图**没有study侧栏会话条目，无法观察毕业帽图标**。UI绑定source中`study: GraduationCap`只能作安装机制补证，不把它当真实显示已验；当前截图也不能判定study侧栏图标显示失败。保留这一窄取证边界，不为补图新建study会话或更改现有选择器UI。

root随后E12只读确认旧Pi有idle runtime `4edf8b55`、running=false、lease0、compression lock0、原8条持久消息不变。无法证明该旧用户会话只由root持有，因此没有close或其它写操作，**不能写全部runtime资源0**。原唯一K3测试资源0证据继续复用，不重测。此次执行按计划完成，无场景缩减；公网登录后结论不变。

### 4.2 · 同步最终原件独立接收与范围

执行者为同步Agent，root已review；本Agent独立读取原始JSON、日志及产生读数的脚本后比较，未重新运行helper/同步/数据库测试。以下均是**原件复核非亲操**，用户预期仍以D01–D14而非实现者报告为准。

**V08通过（配置/SOUL lane）：** scratch真实匹配器前向八允许配置文件、仅一个固定ZIP，反向允许配置修改且未知`remote-secret.env`排除；unknown/.env/rawDB/WAL/receipts等不进入实际传输。生产profile-config是two-way-safe、两端8文件、watching且无conflict/lastError；snapshot为one-way-replica、两端1文件watching。六个非SOUL文件先受限备份及安全预对齐，实际仅两config.yaml变化，最终云/本机八文件SHA全等，两SOUL SHA仍精确D01原值，env_transferred=false。既有云Kimi/NM/MCP秘密没有回传，DS云内专门落地不混入此lane。真实正式配置变化的双向交错采用同配置同忽略规则的scratch代表，不为测试修改用户SOUL或生产配置。

**V09通过（实际最终冷库）：** E10第一次已验包`87e30562…`与三Mac目标完整字节/大小/全表行hash均相等，本Agent程序化核比较`source_package == mac_mirror`三个全真；Alex49会话/6067消息，study0/0。原Mac Alex库SHA `cf052567…`及inode50959517在initial原样保留。最终完整包`c1ce43fe99d620ca27c6a1fd492a290c3bd06f520c7b296d2f370761a8534dac`经正式launchd在17:52:42 UTC接收，应用Alex/state.db，另两库相同无需替换；final脚本核当前ZIP/incoming/status SHA同一且与每库manifest一致、SQLite integrity/FK及全表hash。最终三库如下：

| 本机冷库（`~/.hermes_profiles/`下） | 源包/目标完整SHA256 | 会话/消息 |
|---|---|---|
| Alex/state.db | `e3bd0b0a0e4bca90b964b5a8e0973bf4a16768ead75485eb8355e3d56c163ce4` | 49 / 6067 |
| study/state.db | `8ff76062cdcb2fb7d655b303e8a75a94a144f4f86f883fb162e228b71490d3f2` | 0 / 0 |
| Alex/projects.db（已存在批准可选库） | `e4c5ecd6e97c33e4973e2a2c81d9c6dddfea4eedc728a5c8c5cb9a43c89b89d9` | 4空表 |

这不是初始48/6065覆盖云后续数据；增加的是唯一合法K3会话/两消息。首次目标真实lsof无句柄且无sidecar；Mac冷态不作为第二写入端。两槽current/previous、initial和固定status/lock在最终目录，未出现无界历史包。不是跨三DB全局事务。

**V09调度采样边界：** 云timer实际LastTrigger=01:50:00 CST、Next=01:55:00、active waiting；calendar为`*:00/5:00`。Mac launchd真实run interval=300seconds、WatchPaths、runs2、last exit code0；1:52:42到件轮落库成立。计划原拟“两次实际定时包”现接收的是**一次真实timer触发＋同一正式systemd publisher入口的另一次人工启动**，不是两次完整300秒间隔样本。基于已见实际自动触发、确定的300秒配置与同正式入口代表，不为多等一次周期重复已足够证据；长期多周期/多日和性能未验，这一采样调整不削减最终冷库目标，不冒称长期稳定。

**V10通过（可复用机制＋真实恢复结果）：** 同受审helper SHA的19不同真实SQLite节点覆盖打开句柄、stage后晚到句柄、sidecar、半包/hash/manifest错误、部分替换失败与恢复、正式独立CLI、源身份行、初始保留和幂等，canonical runner原日志可核且未重跑。正式真实包再次receive为unchanged、applied=[]、三个inode不变；有效包→全验证→真实冷库的后续结果已经V09验证。受控错误输入不伪装为生产故障；不在生产故意创建坏库/sidecar，也不假称正式运行从未可能部分失败。

**V11通过（断传代表链），保留真实关机边界：** 原件及脚本显示仅pause本任务snapshot session，不是Mac关机或整机断网；暂停期间Mac包保持`87e30562…`，通过`systemctl start hermes-secretary-snapshot.service`的正式入口云仍发布新`c1ce43fe…`，只一个完成ZIP、暂存仅lock/status，固定status222字节；不等待Mac ACK。resume同一session后真实Mutagen追上新包，起初post-offline-receiver原件仍旧status且有临时`.receive-*`，**不把该中间状态误当完成**；随后final-reconciliation与launchd证据才确认新包落库并清临时。backend/proxy PID及启动时间全过程与before相等，运行中无停服/模型/NM/飞书请求。

这覆盖“Mac接收链不可达时云publisher仍独立完成→恢复最终到冷库”的代表业务路径；没有跨第二次真实timer等待、真实Mac关机/整网断线或多日积压测试，不声称这些亲测过。采用实际pause隔离新lane替代整机故障，保护其它用户同步与服务，明确记录与原跨周期计划的采样偏差。

**V07/V12剩余阻塞：** E12原始tccd日志01:49:31明确PID647的Mutagen对DesktopFolder进入AUTHREQ_PROMPTING，生产workspace仍scanning、marker云端未达；不是代码成功或单纯connected。root已请求用户手工授权，未答复不能当允许；本Agent不操作系统UI/绕过/改路径。marker只在Mac保留，授权后精确workspace ID双向核及删除自有marker才可关闭。旧五条Pi session ID/模式/端点/ignore/paused均保持，按用户要求新链全部成功后最后清理，当前不清。

## 5. 问题、修复与复验

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| VE01 | V01匿名→Access→合法登录后双SPA/WS | E01到真实登录页，E02/03走SSH回环 | 登录后必要证据缺口，未关闭；不代表保护失效，不停服 | 无源码缺陷判定 | 仅有现成合规登录态时root隐藏IAB/用户可核原件；不索OTP |
| VE02 | V02/03/04/07旧Pi冷读→Files→返回→Profile来回/图标 | E08实际旧正文、多角色Timeline、Files空共享目录、返回同route/owner、双Profile往返49链接与默认符合 | **行为与Alex图标证据关闭**；study无会话故未观察侧栏毕业帽，仅该视觉覆盖边界保留，不判失败 | 无源码修复；原运行产物 | §4.1原件复核通过，无新增模型/Conversation |
| VE03 | V08→09→10→11激活→周期冷库→拒绝→离线恢复 | E09–11原始JSON/脚本/日志：配置精确到达、真实三DB冷库、同包幂等、断传云独立/恢复落库 | **必要实际结果已关闭**；19机制复用不当生产故障。timer和断传采样边界见§4.2，workspace另见VE06 | source5c7fad1，双端helper完整SHA8e1ecc2d…；状态doc892c6bf | 本Agent独立原件对账/指纹，无复跑/同步操作 |
| VE06 | V07/V08 workspace lane访问Mac Desktop | E12 tccd原始日志AUTHREQ_PROMPTING/PID647，workspace scanning，云未收marker | **真实外部权限阻塞，未关闭**；用户手工允许待定。网站/config/snapshot正常不因此停站，Agent不点系统UI/绕过 | 非源码修复 | 授权后仅精确workspace双向marker及清理，不重复19节点 |
| VE04 | V02独立型号正式目录窗口与自动兜底 | 旧自动256000；E05原生API补context_length262144后effective正确，型号/Provider/PID不变 | 配置事实已纠正，不声称自动识别已修 | 同运行Core的配置delta | 前后API已有，不追加模型 |
| VE05 | V05用量日志与stored summary不同 | API17824in/34out与UI17858一致；stored15776为另一观测字段 | 诊断口径边界，不伪造一致值、不推断重复调用 | 不适用 | 以正式API日志核1次/0工具，保留两读数 |

本Agent无产品修复或重试，无“三次修复仍失败”序列。后续修复保留旧结果/版本，只复验原场景及受影响链路，不降低判据。

## 6. 验收结论与推荐复核

当前**门禁未关闭**。可接收：云Alex精确型号/high、一次真实KimiCode回复→idle→自有runtime回收；study与Alex往返保留49链接（原Pi48＋唯一合法测试），study无默认；旧Pi冷Timeline实际可读；Files加载共享空目录并返回完全相同owner/route；Alex既有人物图标可见；公网匿名跳Access及真实登录页。历史集合/来源及REST、MCP握手、Files cwd有补证。UI/模型均为root薄执行原件，本Agent非亲操。

最终可接收的同步结果：生产config/snapshot两lane安全接通、SOUL冻结字节不变；云真实300秒timer及Mac正式launchd；实际三库完整字节/全表/源身份对账到冷库、initial原inode、同包幂等；snapshot隔离暂停时云继续固定包发布、恢复后自动落库。均复核原件而非只接root转述，详§4.2。

**未完成与未验分开：** workspace因真实Desktop TCC权限阻塞仍未完成，marker只留Mac、用户允许后须双向核及清理；旧Pi最后清理仍待新链路完备。公网Access登录后双SPA/API/WS未执行；study无会话导致侧栏毕业帽未实际呈现，不能由通用选择器图标判失败或全视觉通过。Space/Idle只证配置/安装，不声称实际新Thread/500秒压缩。实际Mac关机/整网故障、多周期/多日或多GB性能未验；断传代表测试是pause新snapshot lane＋正式服务人工触发一次，不写成跨真实周期关机测试。以上不全轮PASS，不挡已运行入口。

推荐用户自主复核路径为[正式首页](https://hermes.edgarzhong.fyi/)→本人Access登录→Alex精确型号/high→一条旧Pi历史→Files再返回→New Chat切study无默认/列表保持→[Dashboard](https://hermes.edgarzhong.fyi/dashboard/)及既有sessions子路径刷新。无需再发测试文本、建提醒或Memory；不因此额外请求用户登录/OTP。同步主要复核产物是两Mac冷DB、已验包和各自SHA/SQLite/时间戳。已按主会话过目的计划接收UI/最终同步原件；当前56份原件指纹及独立比较摘要在`E/validation-evidence/`。后续workspace权限解除只补该受影响链，最终完成/继续补证/交付由主会话判断。
