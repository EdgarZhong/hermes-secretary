# 真实集成补证续接报告

本报告归 native_integration Owner，只记录开发集成补证，不是 Verification / Validation；第二轮 Verification 禁止启动。2026-10-14 准备阶段与后续真实串行补证。当前新Prompt/未来task、自然Instant、done→重新排期已取得开发证据；Reminder内timestamp曾被本Owner误判；用户最新纠正已撤回该判断与临时隐藏修补。最终口径和资源清理见§9。

## 1. 对应条款与边界

最新授权按 Snapshot Index C90–C98；02 §1.3–1.6 身份、§2.5 未来 task / 必填 Schedule / 显式 instant/deferred、§3.3–3.4 原子 Snapshot、§3.7–3.12 正式工具与 Reminder、§4.3/4.5 关闭及原生 Idle、§5.5–5.6 缓存前缀与真实 carrier、§5.8–5.10 终止/Anchor、§6.9/6.17 正式投递；06 §1.4–1.7 Timeline/附件、§1.11 编辑边界、§3.3/3.5 正式 WS/Agent、§4.6 IAB实际入口。行号已按当前章名核对。

清理硬门禁不实施；Memo 首段、事实来源与消费机制不动；user_reminder 不传 delivery_mode，secretary_task 必须显式 instant/deferred。不写产品、Prompt、规格、核心文档或 plan，不提交、不派生，不操作用户 5173/53445、视觉树，不人为修改旧测试账目；正式联调仅沿Main批准的隔离profile自然更新。

## 2. 当前准备变更与版本

仅新增本报告和 ignored `native-integration/preparation.json`。后端 HEAD `24510d1c7c3b8dfc95b6d0626be30f090561fa30`，前端修复树 HEAD `002f7a27fcf7313491f0301e143df7d3b6148088`；两树均有 Main/其他 Owner 已授权未提交修改，不能用 HEAD 单独代表源版本。当前关键源码逐文件 SHA 见准备 JSON。

旧 live manifest 对当前树的变化：后端 secretary/noting_tools.py（Main 新最小 Prompt），前端 controller.ts 与 verification-fixes.test.tsx（Main Usage 微修）。旧附件实现接缝 hash 未变；旧 Prompt / 新 Prompt 证据不能混用。

## 3. 服务、profile、PID 与 IAB 能力

- 只读 lsof 确认 53449/5183 无 LISTEN；定向 ps 未见对应 dashboard / serve-live / rpc-live 存活进程，本 Owner 自有 PID 为零。未结束任何旧 Owner 或用户进程。
- 旧隔离 profile：`.hermes-dev/round2-verification/frontend-fixes/live-integration-20261014/profile`，workspace 同目录下 workspace。setup 指向获授权 config_source `.hermes-dev/round2-attachment-live`，native custom DeepSeek / api.deepseek.com / chat_completions / deepseek-flash；凭据文件存在，未输出内容。旧 profile noting_idle_seconds=20（满足至少15秒）。未复制旧 state、未修改 DB。
- 当前 CUA `getState` inventory 确实列出 `Codex In-app Browser` id=2、type=iab、tabs=[]。仅inventory，不选用户 Chrome、未创建 tab、未改权限。旧报告“仅Chrome”是旧工具环境事实，不能覆盖本次能力确认；当前尚未执行 IAB DOM 操作。

## 4. 可复用的已有实际证据

旧 Owner 证据目录 live-integration-20261014。该 Owner 新 RPC 两片 4,194,400 bytes 上传、attachment_info stat、partial abort 已成功：upload_id `09a961ca-cb35-4ec0-a216-2fc5c2653aeb`，源与落盘 SHA 均 `b721fa457dc55d0699cb54a98693d7b13fe29d4990f79949161de816c1fd8e80`，首尾 HERMES_R2_NEW_RPC_HEAD_20261014 / HERMES_R2_NEW_RPC_TAIL_20261014。

runtime `85c42a4c`、stored `20261014_013750_6e40a5`、ref `conv_e5f550388ffa43489c9014cc0a00a651`。只读 DB 核真实 Main terminal 两次工具及 exit0，stat / head64 / tail64 与实际最终 Assistant 存在；Main 交回 terminal Assistant UID `b372e58c519f4991a221b1c161b7bf46`。旧 native WS 有 message.complete seq1200/status complete，可复用真实模型附件结果，不能重复上传或重跑模型读取。

旧 Noting child `noting_dc2f29f62e794253` 已查实际 session_history 来源，但 DB child 仍为 running、Snapshot0、Registry0；这不是成功 Notebook 提交或 Instant 链。旧 browser-events-dom.json 最后 seq831/message.delta、active=true/receiving1，比真实终态早，不能冒称终态 DOM 已闭合，也不证明 IAB。

BE59/BE28/C84 33distinct、现前端受控 WS、长流性能、Undo 和容量证据按已有报告复用；不重跑大包、500MB、Undo、性能或完整门禁。

## 5. 剩余正式路径与执行计划

等待 Main 完成当前 build 并正式释放资源；此后作为唯一浏览器/模型重任务方，使用 53449/5183 与上述隔离 profile，启动当前 source/new Prompt。先只读核原生重启后 unfinished child 的真实状态，不 SQL seed、不伪造 carrier、完成消息或改 child status。

若原生恢复没有合法可继续 trigger，IAB 正式 UI 最小一条新 Main 输入建立事实与真实 Anchor，要求未来 secretary_task（显式instant、有效Schedule），沿正常 Main→Idle20s→Noting→Snapshot→Registry→自然到点→原生 COMMIT→持续WS→IAB DOM，保存同链 sourceUID/ref/DB row+seq、模型/工具请求和DOM先于Thinking证据。之后用最小真实事实推动已确认done→schedule_update自动回pending，复用原工具/owner和Snapshot事务；不要求模型另补status。避免重复模型链，先观察再决定必要后续输入。

旧 observe.ts 在每次事件保存完整history/live与DOM，累计数组并反复序列化全量，8.17MB现存文件不应直接续用。本 Owner 使用白名单下有界 observer：仅 source/start/Thinking首次/terminal/必要DOM状态/差异时间，截断文本、固定容量、有限次数落盘；持续 WS append JSONL，敏感token/凭据不落证据。末尾断 observer、关闭自有tab/连接/服务并释放数组，记录实际PID与退出。

## 6. 缺口、接口影响与完成判据

准备阶段不宣告真实 Instant 或当前 Prompt 通过；未确认旧 child 重启关闭/恢复事实，未产生当前源版本 IAB 证据。服务重启只有已确认隔离且无活动工作才能做，不碰用户服务。当前 IAB 可用但实际DOM操作尚未证实。

没有产品/API/权限/Schema变化。完成需同链真实sourceUID/ref/DB seq、实际Hermes模型请求、IAB源先Thinking/终态及时且不重复、当前Prompt下futuretask/Schedule/自动状态结果，明确fixture与实际模型差别、源hash、边界和未覆盖；开发结果不代替独立门禁。

## 7. Main 接收建议

可先独立接收准备阶段：已有附件真实模型结果复用，当前IAB可用，53449/5183没有监听，当前Prompt与Usage差异已辨认，剩余集中为unfinished原生重启事实及新Prompt/Instant/IAB完整链。收到正式资源释放后继续，不自行开启并行重任务。

## 8. 新 Owner 实际串行联调（资源正式释放后）

Main 唯一 JS build exit0 后释放资源。本 Owner 沿原隔离 profile 启动53449/5183；自有 backend PID / frontend PID分别保存在 ignored `native-integration/{backend,frontend}.pid`，运行日志同目录。仅隐藏IAB（子Agent `visible:true` 被接口拒绝，改为支持的 `visible:false`，仍是type=iab），tab1真实正式页面；没有Chrome/用户浏览器或权限变化。

执行时Main阶段版本前进为后端 `f8e416178ecf24021c614940052561f30dc7929d`、前端 `aacb6e9`。只记录git版本，不重启正在进行的链。原生API/provider/profileownership不改；`actual-native-chain.json`中Main持久执行来源为native、model deepseek-flash/provider custom/base_url api.deepseek.com，Main与Child实际model生成的tool requests/结果和API会计均保留。没有受控provider返回、SQL seed、fake carrier/finish，Notebook item均由实际Noting工具写。

### 8.1 旧真实证据复用与重启边界

IAB恢复旧正式会话，实际DOM已读到旧新RPC附件结果size4194400与首尾marker；没有再传文件或发模型读取。旧unfinished child在dashboard启动及native session.resume后仍持久running、Snapshot0，未被伪改状态，也没有继续运行或生成完成Notice。规格Noting为process-lifetime、不restart-resumable，本报告不把这个历史账目称恢复成功。新真实Main产生新Anchor后原生正常准入新Child，旧历史账目未阻断本链。

### 8.2 当前最小Prompt实际未来task

IAB在旧Conversation正式Send一条新用户意图（UID `838d70e72d124f23b43308bb0fe32e60`），Main仅替换Memo。Main结束后原生Idle20s准入child `noting_e136ec3959324e1a`，其真实持久task同时包含新维护段 `Keep all four sections current`、工具字段 `future work, not a completed-work log` 与 `REQUIRED for every secretary_task`，原Memo首段保持。

实际Child查询session_history确认新用户事实，notebook_manage create秘书未来工作；第一次 `in 45s` 被原生时间parser拒绝（不支持秒级），模型改为合法 `in 1m` 并在finish reason/最终child文本准确说明此偏差。随后finish_noting成功，Snapshot `snap_9efdd01a06e84b9ca82179d8b1504581`、Anchor `32c3f48d0ca246958e5d0bfad6cad051`、payload[1]。item1为pending的secretary_task，内容未来执行sleep2/回复marker、实际来源是上述用户UID，Schedule非空/instant显式；不是已完成流水账，也不以Memo作来源。Registry同事务注册 `sched_b8769b1b351443c0b8befddb033c2587`，Memo消费清空、真实Framework Finish Notice存在。

### 8.3 自然Instant → COMMIT →持续WS → IAB DOM

不人为tick或SQL修改时间。到点scanner经原生入场生成user行：UID `79b58919db1a49398fd4d62556158e02`、row27、ref `conv_e5f550388ffa43489c9014cc0a00a651`、timestamp `2026-10-14T02:19:39.932106+08:00`；source boundary明确all_rows_committed，DB同一原行可复核。正式Gateway原生 `message.source_committed` seq153；同持续IAB WS里源DOMseq153先出现（21ms），新的Thinking卡到seq157才出现；实际模型请求继续原生terminal sleep2/exit0，最终Assistant回复marker；message.complete seq313后15ms DOM进入complete、receiving0、同source UID唯一一份。源DOM单卡数1，最终同UID行数1，没有等complete才补源。

`instant-first-proof.json`是有界观察原始记录，`instant-summary.json`提供身份、seq和时间。21/15ms是同机MutationObserver的event→DOM开发观察，不是paint/SLA；delta只累计计数，未持有全部快照/文本。被取证捕获的native.active短暂状态不据此造新的产品语义。

**已撤回的Owner误判**：本Owner曾将Reminder内部字面 `<timestamp>…</timestamp>` 按一般Timeline规则误报为缺陷，Main曾临时在解包后withoutTimestamp。用户随后明确纠正“Reminder 不需要额外包装处理”“Remind 默认折叠，里面的 timestamp 不需要在表现层消除”，Main已撤回临时修补及三测试。此标记保留是最新授权行为，不能再列缺陷、隐藏成功条件。`instant-terminal-iab.png`为实际保留timestamp的真实原行证据；`instant-fixed-iab.*`仅记录已被撤回的临时行为，不作为正确实现依据。源身份/事件/DOM先后证据未受该误判影响。

### 8.4 真Noting完成语义与自动重新排期

Instant Main真实成功后下一个Idle任务child `noting_478dcaaa342a4235`将原任务1合法status到running版本2，再done版本3；Snapshot `snap_e568ccc648b2481a85a980f3d92f28ea` payload[3]。done仍保Schedule意图和instant，并没有构造完成流水账。

IAB再正式Send用户指示：同一工作再次需要未来跟进，现有task重新排期in10m，保instant，不新增/归档、不另status。Main仅add Memo。自然Idle child `noting_a3978b7126a64dbe`的实际工具请求顺序为notebook_schedule schedule_update → notebook_show → finish_noting；没有notebook_edit status/create/archive。工具返回在同一个新版本中id3 done→id4 pending，lineage1不变，task/purpose/来源保留；Snapshot `snap_c0f52ad9a3554e76a2715aade7f43a3a` payload[4]。Registry保原schedule_id，notebook_entry_id4、pending/enabled1/next_run有效、last_fired_at保首次实际投递、claim_attempts1，正式提交链激活新Schedule。

随后IAB使用正式只读 `/notebook`，实际用户面为Assistant1/Secretary task/Pending/once in10m，其余三区空；`notebook-rearmed-iab.{txt,png}`保存只读输出。该slash不启动额外模型。

### 8.5 取证范围、失败与资源控制

只有两个新IAB用户Send、一轮自然Instant；本链产生三个真实新Noting任务（创建、完成、重新排期）。没有测试、build、500MB、Undo/性能复跑，未运行独立门禁。旧附件真实模型结果直接复用。

取证首版错误保留：observer把整个binding存入native摘要，引发150KB落盘端拒绝/Failed to fetch，未修改产品；即时改为session/stored IDs、最多50个非delta事件/80个状态变化，并在Instant到点前重载自有页。当前proof有限且source/terminal完整。原旧observer8MB文件未返回对话。旧 `in45s`原生拒绝也完整保留，不改parser/规则。

`actual-native-chain.json`约151KB，含真实SQLite只读导出的item/每个Snapshot/Registry/Memo与实际消息、model tool requests及result；它是审计证据，不是SQL构造测试数据。未抓原始HTTPS provider包，本报告的actual model request证据是native执行来源/API会计及模型生成的真实工具请求/结果/终态，不把它冒称wire字节记录。旧有效缓存前缀、失败/重启/权限/并发与边界机制证据按BE28、BE59、C84复用。本次仅macOS/IAB开发观察，真机/其他provider/跨平台不在此补验。

## 9. 用户最新纠正、只读边界与最终资源交回

用户最新明确覆盖本Owner此前对06§1.4的误读：Reminder不需额外包装，默认折叠，内部timestamp保留。Main撤回临时inner withoutTimestamp与三测试；最终projection为原 `text=match[1]`。本Owner在收到纠正前已关闭IAB，不再开启新模型/整链，复用原真实beforeFix DOM与截图；临时“隐藏复验成功”不代表最新授权要求。本次AX中的Instant为container/text直接呈现，未提供collapsed按钮，故**本补证未证明Instant默认折叠**，已显眼交Main按最新口径判断范围/后续接线，不能把此项冒称通过或自行改产品。

旧unfinished子链只读核查：admission1归同ref conv_e5f…，Anchor b372…/idle，child noting_dc2f29f62e794253仍durable running。现原生 `secretary.state` 返回availability available、task_state unknown、tasks[]、Memo0、next_idle absent；现 `session.active_list {}`只列runtime70978bbd/status idle。web_read._tasks正式机制为live→active、stale durable row→unknown、否则idle；没有把崩溃任务冒充live运行，也没擅自补abandoned/修改DB。只读结果见`current-native-read.json`。后续02恢复/审计要求的判断归Main，不新增清理或恢复逻辑。

资源清理：自有隐藏IAB tab1已关闭，页面销毁释放observer/数组/WS；Node frontend PID95453、Python dashboard PID94660在核command和实际端口listener归属后仅发送SIGTERM。两个exec会话均exit143；随后lsof53449/5183无监听、ps两PID均不存在。无模型/Noting live任务，未kill用户或旧Agent进程，未碰5173/53445。cleanup-start.json记录归属与动作；最终source-manifest/end状态见`final-manifest.json`。

明早启动隔离已测入口（不构建，凭据仅沿现ignored profile原生加载）：

```bash
cd /Users/edgar/code/hermes-secretary
HERMES_HOME="$PWD/.hermes-dev/round2-verification/frontend-fixes/live-integration-20261014/profile" \
HERMES_RUNTIME_DIR="$PWD/.hermes-dev/round2-verification/frontend-fixes/live-integration-20261014/profile/runtime" \
HERMES_WEB_DIST="/Users/edgar/code/hermes-secretary-web-verification-fixes/dist" \
.venv/bin/python -m hermes_cli.main dashboard --host 127.0.0.1 --port 53449 --no-open --isolated --skip-build
```

另一终端正式修复前端，不加载本Owner取证observer：

```bash
cd /Users/edgar/code/hermes-secretary-web-verification-fixes
HERMES_BACKEND_URL=http://127.0.0.1:53449 npm run dev -- --host 127.0.0.1 --port 5183 --strictPort
```

IAB入口 `http://127.0.0.1:5183/chat/20261014_013750_6e40a5`。端口启动前核无已存在listener，版本变动按Main统一窗口协调。该profile保留已确认重新排期的in10m一次性测试intent，恢复绑定后可能按原生overdue规则投递；这是真实测试状态，未静默清库、取消或改审计账目。现无监听，不会在后台继续触发。

交回结论：新附件真实结果复用；当前最小Prompt实际未来task/有效显式Schedule、自然Instant COMMIT→WS→IAB源先Thinking/即时终态、真实done→schedule_update自动pending同Registry链取得证据。时间parser45s→1m偏差、旧child unknown、Instant默认折叠未证明、原始HTTPS请求未抓包、跨平台/真机未覆盖均保持可见。不宣告第二轮Verification/Validation或整体独立验收通过。


### 9.1 Main最新统一Reminder折叠接线的交接

本Owner清理后，Main按用户最新“Reminder默认折叠”统一类别，将instant-reminder加入现有Message.foldable条件，复用FoldedMessageBody；不另wrapper/CSS，不改原文/来源。现行06已由Main同步C99 Reminder例外。本Owner未重新启动服务或页，**该最新接缝的IAB默认collapsed/展开保内部timestamp复验归Main**；不得把本报告的旧默认呈现或临时隐藏截图冒称新实现通过。自然source21ms/terminal15ms与状态联动未重复运行，依未改机制有效保留。final-manifest记录的是本Owner关闭时的确切源/证据版本，Main之后的折叠改动应使用其新的source记录。


## 10. C99最后呈现复验：IAB工具不可用，未执行真实DOM

Main最新foldable仅将instant-reminder加入现有条件，复用FoldedMessageBody；Main已完成2个组件行为用例及最新build exit0。本Owner未重复这些有效证据。准备只读核Registry为pending/enabled1且02:32:44已overdue；按Main明确授权仅隔离profile临时将noting.enabled改false，备份原config字节/SHA，未改DB。Main释放后启动无observer注入的正式53449/5183，准备读取同一真实历史UID79b589…。

**实质接口阻塞**：本次CUA createBrowserTab(iab, visible=false)返回`Browser is not available: iab`；立即listBrowsers只列Chrome id3，上次IAB id2已从当前工具inventory消失。未创建任何tab、未走Chrome或权限变更、未发模型。没有把组件测试或旧IAB自然源证据冒作此次C99默认折叠/展开实际通过。

随即仅停止自有backend11773/frontend npm11805及其实际descendants11837/11838，归属经ps parent tree确认；两个exec均exit143、53449/5183无listener。服务退出后逐字节恢复config；SHA与前置完全相等。SQLite只读前后messages/children/Snapshots数量、Registry完整行、真实source row全部相等，零新模型/Noting工作。记录见`c99-before.json`、`c99-cleanup-start.json`、`c99-result.json`；最终source hash包括design/chat.tsx与projection.ts，后者仍保内部timestamp。未提交/推送。

C99现仅剩IAB环境可用时，由Main对既有真实历史行核默认aria-expanded=false、展开同卡保timestamp/无额外wrapper/唯一卡；不存在Deferred真实行则明确未覆盖，不造fake source。原自然Instant源先Thinking及即时终态、附件/Noting/自动重新排期证据继续复用，不重做模型链。本次报告准确标记接口阻塞，不将其误认为产品失败或整轮验收通过。


### 10.1 Main恢复IAB后的上下文可见性复查

Main用open_in_codex恢复其可用IAB id2/tab1/provider4bac…后派本Owner只绑定 existing URL。实际本Owner getState仍仅Chrome，getTab({url:5183/},{browser:iab})报不可用；从本Owner调用同一open_in_codex入口返回queued/thread01a13676…，随后的inventory仍无IAB。此次未改config/启动服务/模型，原config SHA仍相等，资源零新增；没有绕用真实浏览器/权限变化。证据`c99-main-tab-binding-block.json`。

这是Main与本Owner工具上下文的实际可见性差异，不能以Main看到IAB反推本Owner可操作。建议Main使用其已可用existing页完成三项历史呈现复验；隔离服务/config可由Owner单独管理，但不再尝试模型/自然链。queued内置页入口未出现在本Owner可控inventory，Main需在对应chat实际激活时处理关闭，不能假称本Owner已关闭它。


## 11. Main浏览器／Owner服务管理最后窗口：策略阻塞与准确停止

Main确认task上下文隔离后，停止Owner所有CUA/open页尝试；Owner仅管理隔离服务，Main成为唯一浏览器操作方。再次备份原config字节，临时全局Noting false，启动既有profile53449/5183，无observer、无fake source；两个HTTP入口200，交Main准确route `/chat/20261014_013750_6e40a5`/profile default。

**最终实看被Browser安全策略明确阻塞**：Main绑定IAB GET URL5183被拒，错误理由为URL protocol not allowed（提示允许http/https），实际请求本为http；本报告不自行解释或绕过。Main明确禁止workaround/alternate surfaces/raw CDP/间接browser命令，双方没有再尝试URL/ID/底层控制。Main未合法绑定页，不能为关闭页绕过策略。既有open_in_codex queued临时页按排队未显示／未可控状态记录，留待正常UI或用户明早关闭／打开，不假称已关闭。

Owner只做收尾：核ps归属后SIGTERM backend15149/frontend npm15179及实际子进程15205/15206；两个exec均exit143，53449/5183无listener。服务退出后原config逐字节恢复/SHA一致。前后messages/children/Snapshots计数、完整Registry、真实source row、每Session API call_count全部相等，零新模型、零新Noting/Snapshot/source。`c99-main-before.json`、`c99-main-cleanup-start.json`、`c99-main-result.json`为前置、动作与结果；最新chat.tsx/projection.ts和两repo HEAD同result，未提交/推送。

C99开发证据：Main的默认折叠/展开保timestamp组件2pass、最新build exit0可复用；**最后IAB默认折叠/展开实看仍未执行，明确策略阻塞**。先前自然Instant真实IAB source先Thinking与终态、真实任务排期/状态链有效，不与此阻塞混淆，不重复模型链。产品默认折叠实现不被工具拒绝推定失败；真实浏览器通过也不被实现测试替代。后续正常IAB访问恢复后只读同一现存行即可补最后呈现，不新增模型或伪造source。


## 12. 用户要求重试：C99真实界面补验通过（2026-10-14，Main）

同一Main上下文正常CUA getState列出IAB id2；正常createBrowserTab打开5173成功，原protocol拒绝未复现。随后沿已记录的原隔离profile53449/5183打开实际会话20261014_013750_6e40a5，只查看已有历史，无新Send/observer/模型。原Noting配置临时停用以避免测试调度，服务退出后配置原始字节完整恢复。

现存真实Instant源在正式Timeline仅一份，按钮aria-expanded初始false；正常点击展开后true，正文含原`<timestamp>2026-10-14T02:19:39.932106+08:00</timestamp>`及原task；再次点击回collapsed。两张实际截图及结构化读数保存于ignored native-integration/c99-retry-{collapsed,expanded}.png、c99-retry-ui.json。原策略拒绝的具体根因仍不明，不把本次恢复解释为已修复某浏览器缺陷。

自有IAB页关闭，53449/5183监听PID84571/84700按归属SIGTERM、exec均exit143；原配置逐字恢复；messages/children/Snapshots、Registry完整行、session API计数均与前置一致，零新增模型。c99-retry-before.json与c99-retry-result.json可复核。C99最终GUI观察现通过，仅为开发补验，不是第二轮Verification或Validation。
