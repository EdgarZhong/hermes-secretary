# 2026-10-20 手机 Web／微信交替使用调查取证报告

本报告面向网页版 Astra 的分析交接。调查者负责现状、证据与边界；改进方案由接收方结合仓库代码、用户原始描述制定。全文时间为 Asia/Shanghai（UTC+08:00），字节用十进制 B／KB。该报告不把多种现象归为同一个根因，不把成功样本写成历史问题已消失。

后续认证续查：2026-10-21已核普通登录12h／记住我1M与新一轮手机失效时序高度一致，现将两种登录均改为31d。具体证据、不能排除的原因及验证边界见[运维记录](operations-log.md#2026-10-21-1044--移动端重复登录续查与31天期限)；下文保留10月20日晚原取证时点，不以新结论改写当时缺口。

## 1. 调查结论与未闭环事项

| 事项 | 已获得的证据 | 判定边界 |
|---|---|---|
| 手机刷新后 timeline 长时间不完整 | 同机蜂窝 cards 请求三次耗时 68.199／56.090／64.684 秒，主要耗在响应头之后的正文接收；稳定 Wi-Fi 同类响应 0.404 秒。服务器回环读取约 0.063 秒 | 已定位慢等待所在阶段；没有定位到具体运营商、链路段、丢包／拥塞机制，也没有证明与跨境本身有关 |
| WS 已连接却仍看不到历史 | 上述慢 REST 期间，第一轮 WS ping 中位 RTT 0.250 秒；切回蜂窝 WS 约5秒完成重连，但紧随其后的 REST 正文仍耗54秒 | WS ready 不等于历史完整；用替代流式协议不能直接解释或解决这组已观测事实 |
| Thinking 出现、纯图片 user 气泡缺失 | 正式后端 RPC＋SQLite、正式前端 Controller 链分别离线复现：纯图片受理没有即时用户行回执，过早历史读后缺少落盘通知 | 机制缺陷已证实；21:16生产提交与用户确认相符，但当时没有客户端录制，不声称逐帧重建了现场 |
| 纯文字也可能缺气泡 | 用户有明确记忆；22:39本次纯文字实验回执、事件、气泡均成功 | 保留未复现问题；一次成功不能排除偶发问题 |
| Compact／Noting 后消息缺失与 Notebook 空 | 压缩21:41提交成功，摘要确实在DB及cards中；Noting21:51达到50次迭代后failed，没有Snapshot，原失败分类又没有发失败通知 | 压缩摘要、Noting Framework Message是两件事；前者的具体屏幕位置未复现，后者已找到明确终止路径缺陷 |
| 发送键灰到22:00 Reminder／22:35才恢复 | 既有用户反馈；本次记录到草稿先出现、连接恢复期间Send灰、之后恢复 | 历史22:00现场缺Controller内部状态，不能认定唯一禁用条件 |
| 22:04连接失败／后来跳登录 | 服务端约28次手机 `GET /` 302，认证层对应匿名拒绝；前端20秒ready计时包括bootstrap token刷新 | 支持认证bootstrap重试解释，但没有跳转前cookie／服务器session审计，不能判浏览器bug、cookie过期或WS底层故障 |
| 刷新先出现非微信Turn，之后才出现微信Turn | Web进程快照与REST持久历史是两条路径；22:21 replay包含22:00而未含22:07／22:09微信Turn，稍后REST完整到达 | 已给出实际时序与机制；不据此扩大Runtime生命周期改造 |
| 桌面timeline无操作跳上方 | 用户反馈、滚动锚定实现静态核查 | 未录制复现，尚不能指定根因 |

独立 Noting 迭代预算收尾修复已经本地完成并定向验证，**未提交、未部署，生产仍为旧版本**。没有恢复旧任务或补造Snapshot。为什么模型50次均检索却不主动结束，属于单独的模型行为问题，本轮没有调Prompt、模型或预算。

## 2. 版本、对象、采集范围与留存

### 2.1 版本和对象

- 后端线上：`fcf5d08ac587b43c5aafd2f3e8656a6c5b147432`，仓库 [EdgarZhong/hermes-secretary](https://github.com/EdgarZhong/hermes-secretary)。本地调查开始HEAD `ecc6695d5c6ad7e7b96c8415d4b8f878097de8c2`，其后只有本文列出的本地未提交改动。
- 前端线上：`83285d2be259f1ee9f7e24bba6dd4c70688831fe`，仓库 [EdgarZhong/hermes-still-chat](https://github.com/EdgarZhong/hermes-still-chat)，正式远端分支 `secretary`。本地目录 `../hermes-secretary-web`；交付时无前端实现改动。
- Profile：Alex；Conversation：`conv_8dc89e12cc9b42b5a77986f4d9b02cec`；stored Session：`20261011_223115_59ad08`；Web runtime：`3c5687de`。
- 手机：PHZ110、Android 16、Chrome，USB ADB／CDP真实设备。两轮前台目标2513；另一个同站旧目标2520处于hidden，不能将后者的断开当成前台失败。
- 入口：Caddy HTTPS → Authelia双因素 → 单Web后端；认证会话存Redis。当前h1／h2，HTTP/3先前已停；本轮未改代理或认证配置。

### 2.2 服务端已经保留什么

固定原件目录（首尔服务器，SSH别名 `seoul`）：

```text
/home/ubuntu/.local/state/hermes-secretary/incident-20261020/mobile-web-evidence-20261020T224259/
```

共9份，11,674,025 B；目录0700、文件0600。保留Alex `agent/gui/gateway/errors` 4份日志、host `agent/gateway/errors` 3份日志、system journal（Web、Caddy、Authelia、Redis）与user Gateway journal。应用文件为当前存在日志及轮转文件扫描结果；journal固定范围 **17:58:00—22:42:59**。普通日志为活动文件逐个复制，不声称跨文件原子快照。后续只读重算9份SHA256全部一致。

`server-preservation-manifest.json`记录来源、inode、大小、哈希、固定cutoff；`server-preservation-verification.json`记录复核结果及微信事件元数据。敏感原件不进入Git或ZIP。不是只凭后续轮转中的活文件追查。

脱敏Caddy摘录 `access-redacted-evening.json`：17:58:14.453—22:43:00.600，共1432条日志记录，其中1428条access、4条error；**不是1432个独立请求**（4个502各有access和error两条）。这个只读摘录取得时间比固定journal边界略晚，复算时分别使用各自范围。

- 1428条access覆盖API、HTML、静态资源、下载、WS握手、认证重定向；已去客户端IP、完整UA、cookie／认证头和非白名单query。
- 4个真实502均在17:58:16—22部署启动窗口、desktop `/`，没有把8条日志误写成8次晚间故障。
- 7条499分布在21:09、21:13／14、22:09、22:21、22:29等历史请求，存在客户端取消；200＋局部bytes也可能是取消中断，不把200一概视作浏览器完整收到。
- 两个desktop `/` 401样本不能自动等同用户手机退出登录。UA分类只区分mobile／desktop／other，不是唯一设备身份。

补充数据库原件留存：在 **22:57:33** 用SQLite online backup从只读连接取得当前一致性备份 `alex-state-at-20261020T225733.private.db`，186,507,264 B，quick_check=ok，同在上述私有目录。`server-db-preservation-manifest.json`附时刻、大小、SHA256、整库表计数；原库不进入ZIP。这是22:57当前状态保全，不能冒充22:22元数据读取时刻或早场历史快照。清单中的整库Snapshot计数不是目标Conversation的Snapshot计数。

### 2.3 手机实际采集范围

| 文件 | 实际记录边界 | 内容 |
|---|---|---|
| `phone-observe-20261020T222118.jsonl` | 22:21:18.460—22:25:41.031，527事件 | 登录后蜂窝加载，HTTP头／数据到达／结束，WS RPC及事件元数据，2秒采样UI、long tasks |
| `phone-observe-20261020T223500.jsonl` | 22:35:00.523—22:41:58.714，1440事件 | Wi-Fi过渡／稳定读取、切回蜂窝、一次授权纯文字发送及之后历史刷新 |
| `phone-metrics-redacted.json` | 两轮离线归并 | 以浏览器单调时钟算请求／RPC耗时，host wall只用于对时 |
| `actions.jsonl` | 22:39实验 | 先确认监测就绪，随后只点一次用户现有Send |

观察器只读路径／长度／ID／事件类型／时序／UI计数，不落聊天正文、图片内容、cookie值、bootstrap token。UI状态每2秒采样，不能当精确paint时间。long-task观察不等于完整CPU／layout trace。采集器收尾已停止并移除诊断observer／新document脚本；ADB转发已移除，没有关闭用户手机标签。

**缺口：22:21以前没有手机CDP或pcap录制，21:16、21:38、22:00、22:04的浏览器内部状态不能事后补造。服务端Caddy并不保留所有WS frame或TCP重传；本轮也没有运营商抓包、无线信号历史或路由逐跳证据。**

## 3. 全晚行为轨迹：微信、Web、Compact与Reminder

来源：`evening-turns-redacted.json`、`service-events-redacted.json`、DB元数据、手机采集、服务器原件复核。以下微信入站无媒体；msg正文不导出。

| 时间 | 来源／动作 | 观测结果 |
|---|---|---|
| 17:58 | 正式版本上线 | Web／微信Gateway开始当前进程，后续没有服务重启 |
| 21:00:00.841—21:00:38.261 | Web宿主原生`tui` Turn | history233，3次API后结束；仅凭platform不区分手打与Reminder |
| 21:06:29.407 →21:06:31.277—21:07:06.435 | 微信入站→模型Turn | history238，1次API，正常结束 |
| 21:07:06.710 →21:07:07.922—21:07:35.304 | 微信入站→模型Turn | history240，1次API，正常结束 |
| 21:08:01.526 →21:08:01.938—21:08:40.055 | 微信入站→模型Turn | history242，2次API，正常结束 |
| 21:09／21:13／21:18附近 | 手机Web连接／读取 | 服务端有WS1001／1006及取消历史请求，缺当时手机包，未确定底层断因 |
| 21:14 | 桌面／手机历史读取对照 | 同一cards174134B，服务器日志桌面0.816秒、手机18.408秒；详情与图片也存在明显差异 |
| 21:16:39.217—21:17:09.762 | Web纯图片提交→模型结束 | `chars=0, images=1`；用户确认正是一次缺气泡现场；没有当时前端帧录制 |
| 21:38:14.857／21:38:15.280 | manual Noting接纳／child登记 | admission3，`noting_0fd1567cdc064a58`，模型21:38:17.385启动，history250 |
| 21:41:41.355 | 压缩提交 | `in_place_committed`，250→61，total207363ms，commit2675ms |
| 21:50:57.933—21:51:31.630 | Noting迭代上限及结束 | 50/50，最终failed；DB finished21:51:31.656，未有Snapshot，未发对应失败Framework |
| 22:00:00.533—22:00:34.588 | Instant Reminder进入Web宿主Turn | history61，3次API，正常结束；用户观察此时灰按钮变可操作／Steer |
| 22:03:22.552—22:04:14.996 | 手机bootstrap／认证异常 | 约28个`GET /`302；匿名认证拒绝对应；没有当时客户端包 |
| 22:07:45.758 →22:07:46.164—22:08:08.277 | 微信入站→模型Turn | history67，2次API，正常结束 |
| 22:09:04.494 →22:09:04.901—22:09:19.061 | 微信入站→模型Turn | history71，1次API，正常结束 |
| 22:18:39.375 | 手机访问会话页 | 302，用户反馈跳Authelia登录 |
| 22:21—22:25 | 第一轮被动ADB采集 | 用户登录后先不完整、后完整；WS正常与68秒cards并存 |
| 22:34 | 服务／Runtime只读快照 | 同一Web runtime idle，Gateway无活动工作；两进程共用同一DB |
| 22:35 | 换Wi-Fi刷新观察 | 过渡轮cards1.291秒，稳定Wi-Fi再读0.404秒；Send、timeline恢复时间不同 |
| 22:37 | 切回蜂窝 | 短暂disconnected后恢复，随后cards却56.090秒 |
| 22:39:30.018—22:39:55.887 | 用户授权代点一次纯文字Send | 即时user回执／气泡均正常；complete后cards再耗64.684秒 |
| 22:42:59 | 固定服务器原件边界 | 原件9份、后续哈希复核通过 |

21:00及22:00服务端接受日志有587／570字符，它们是宿主提交内容长度，不能冒称用户亲自输入这么多字。Reminder身份需结合DB排期／carrier，不只按`tui`名称猜。详细每Turn API次数、platform、history、结束理由均在附件；微信adapter留存5次入站，已对上5次weixin模型Turn，不将“模型已结束”混作“手机已收到历史”。

## 4. 手机网络实测：WS与REST分别计时

### 4.1 同机历史cards对照

均为同一会话最近200行、`view=cards`、inline images的历史读取。encoded bytes来自CDP、通常含响应头；回环JSON bytes仅正文，两者不要求完全相等。

| 环境及起点 | 总耗时s | 到headers s | headers后正文s | encoded B |
|---|---:|---:|---:|---:|
| 蜂窝22:21:59.090 | 68.1986 | 2.8763 | 65.3223 | 865276 |
| 换Wi-Fi过渡22:35:33.025 | 1.2908 | 0.9954 | 0.2953 | 865302 |
| 稳定Wi-Fi22:35:53.593 | 0.4040 | 0.2463 | 0.1577 | 865267 |
| 切回蜂窝22:37:28.238 | 56.0901 | 1.9354 | 54.1548 | 865282 |
| 蜂窝Turn结束后22:39:55.888 | 64.6835 | 7.9098 | 56.7736 | 864614 |

换Wi-Fi轮开始时设备报告仍为cellular，22:35:32.856／34.046附近变wifi，**不是一次从头到尾纯Wi-Fi冷启动**。后续0.404秒是Wi-Fi稳定后对照。换网可能同时改变路径、连接、拥塞等条件；不能把倍率当成普适“蜂窝比校园网差多少”。这是具体会话、具体时段的同机证据。

22:21这一轮headers约3秒就到，之后正文收65秒；初期UI只有4nodes、0 user，22:23:09附近才有约229nodes、28 user。该首屏阶段记录4个long tasks、合计约598ms、最大约409ms。可确认这65秒不能直接解释成相同量级的主线程长任务；没有完整trace，不能据此断言前端零开销。

### 4.2 WebSocket分段

- 22:21:54.516建WS，55.534握手101，55.562 ready。resume约0.815秒，events replay约0.955秒。第一轮15个ping RTT：min0.2231、中位0.2498、max0.4944秒。
- 22:35:50.508连接关闭，52.791握手ready，replay约0.192秒、activate约0.583秒；随后稳定Wi-Fi cards0.404秒。
- 22:37:21.845关闭；23.232前台显示cellular、disconnected、Send禁用；24.263创建新WS；26.874握手ready；29.281采样时Send已恢复。ready与Send恢复也有先后，不能混为同一个状态。
- 第二轮26个ping RTT min0.0712、中位0.2305、max0.6809秒；含Wi-Fi和蜂窝，不能把混合分布说成纯蜂窝分布。
- 22:37重新握手已成功、按钮已经可操作时，cards正文仍在缓慢接收。这直接吻合用户“disconnected消失了但看不到东西”的一类体验。

21点早段服务端WS关闭有1001／1006，记录send_failures=0、dispatch_crashes=0。1006不是“运营商断网”诊断结论；也不能用后续心跳正常倒推22:04当时正常。

### 4.3 Caddy视角与浏览器视角的区别

21:14同cards174134B，desktop0.816秒、mobile18.408秒。手机full metadata215538B约18.013秒；两个附件229605／288216B约19.503／31.295秒。

两端详情同为14批、162行、合计862579B。desktop日志时刻21:14:05.781—06.976，phone21:14:29.187—21:15:27.355。手机前两批写出较慢，后续若干批Caddy duration只有0.012—0.033秒，下一批仍隔数秒。**代理写出结束不等于浏览器收完、JSON读完或页面画完**。以前仅凭这种间隔推断JS慢是不充分的，本轮客户端记录补上了主要正文接收阶段。

Caddy的`time`是日志记录时刻；不能未经核对当成fetch开始。CDP elapsed使用browser monotonic timestamp相减；报告展示的wall仅用于日志对齐。初次resume replay里的message.complete会触发历史刷新，实测有旧cards被取消的ERR_ABORTED／499；不能把每次取消都判网络丢失。

## 5. 请求负载、数据库和前端工作量

### 5.1 服务器实际回环GET

只读3个既有GET，不激活模型、不resume会话：

| 请求 | 头部s／正文s | 正文B | 离线gzip B（不是线上传输） |
|---|---|---:|---:|
| cards200＋inline_images | 0.061615／0.000924 | 864734 | 545572 |
| full session metadata | 0.007832／0.000224 | 215537 | 81333 |
| summary metadata | 0.006936／0.000082 | 51684 | 16901 |

本次线上相关API响应没有Content-Encoding，Caddy当前未配置encode。gzip列只为体积对照，没有部署压缩候选或修改代理。

首屏最大消息row10091为user、JSON651943B，content是两元素multimodal list：text90字符＋`image_url`数据URL651203字符，约占首屏JSON的75%。`content_chars=2`是list长度，**不是只有两个字符**。详情见`image-row-metadata.json`；不导出实际图片。

因此“cards很轻、图片必定另走附件下载”并不成立：此历史行有内联Base64；另一些`@image`引用又会单独下载。纯图片传输大与即时用户行回执缺失是两个不同事实，可叠加。

full metadata中`origin_json`约136261B，`system_prompt`约26588B，`model_config`约956B。usage fallback调用full接口，但当前消费仅id／profile／token计数；标题读取已summary。以上是代码及响应事实，不在本报告选定改造方案。

### 5.2 前端正式路径与隔离测量

前端引用以基线83285d2为准，行号仅定位阅读：

- `src/core/controller.ts:474` connect → profiles；`:704` select，本地草稿先取，summary与cards开始；cold首个cards不以完整Turn replay完成为前提。
- `:900` refreshHistory，limit200、latest、cards。首批合入后才排详情；普通消息正文在cards，不必等待全部详情补水。
- `src/core/history-details.ts`详情单并发、每批12，完成完整body／JSON／accept后才排下一批；队列通常按历史数组，不按可见区。
- `controller.ts:1435`已存活页面重连分支有replay／ensureBinding／refreshHistory串行，和cold首次加载不同。
- `src/App.tsx` HistoricalThinking＋Disclosure：关闭状态仍创建Markdown正文；历史图片组件挂载即fetch；已加载窗口全部挂载，无虚拟列表。当前初始是200行，不能说一次渲染全部近万行。
- `src/core/projection.ts`每次工具投影会重建detailSources数组，影响浅比较引用稳定性；这是重渲染事实，尚未量到用户真实手机上的总贡献。

本地Node v24.21.0隔离实验，生产IO禁用：14批模拟每批body40ms，共598.27ms，下批启动间隔0.73—2.46ms，**没有3—5秒定时等待**。200行／100工具卡投影约0.26—0.43ms；相同内容再次投影仍重建100工具节点。12／60个关闭Thinking SSR仍含完整正文、约42—59／137—152ms。SSR不是手机浏览器布局测量，不用其数值外推真实手机卡顿。附实验源码与结果，供接收方复算。

## 6. user气泡：纯图片机制与纯文字边界

### 6.1 正式链路已离线复现的竞态

1. 前端上传后提交`text=''`、`image_paths=[...]`。
2. 后端 `tui_gateway/session_workdir.py:_write_submit_user_row` 对空text直接返回，受理时没有真实用户row。
3. `methods_prompt.py:791`受理返回streaming；`methods_submit_idle.py`无真实row可构造accepted_user，亦无message.user_committed。
4. 前端接受后清草稿，`controller.ts:1633`立刻refreshHistory，可能早于worker落盘。
5. worker先message.start，再在原生prologue持久化含`@image`的用户行。普通提交没有Reminder专用source_committed observer，晚落用户行未对应广播user_committed。
6. thinking继续正常显示，而过早history只有旧行；message.complete之后finishHistory才重新拉到新用户行。若该次REST也慢，窗口进一步扩大。

正式后端RPC＋真实SQLite两例（纯图片／caption对照）2 passed；正式前端Controller／sourceTimeline链1 passed。测试文件在ZIP，导入正式实现，非复制reducer。这是离线可复算机制证据，不是当时手机网络包。

caption对照受理即有textrow和回执，但当时还不含图片引用。历史图片组件在blob未到前return null，文本又剥`@image`，可出现空user外壳；DOM气泡壳仍存在，不能称被CSS整个隐藏。

已核details接受路径按对象＋UID＋row核身份，未找到“详情补水直接删除新user行”的证据。未验证的修复候选曾保存后撤出源码，既未上线也不作为当前分析既定方案。

### 6.2 22:39一次纯文字实验

用户明确授权“你自己发，帮我点那个send，提前把监测拉起来”。使用其已有26字符草稿、当前蜂窝环境，只点一次，未另造消息、未重发。结果：

| 时点 | 事实 |
|---|---|
| 22:39:30.018 | prompt.submit_idle，chars26、images0 |
| 22:39:30.494 | message.user_committed，seq843 |
| 22:39:30.527 | RPC回执accepted_user，row10195、UID `742fb10d0f1240898f807102ead66be4` |
| 22:39:30.564／30.572 | message.start／thinking.delta，seq844／845 |
| 22:39:30.717 | UI user28→29、输入长度归0、Stop可见 |
| 22:39:55.887 | message.complete，seq1173；模型结束日志为54.887 |

用户确认这次看见气泡，并明确当下网络较好、不能证明历史问题解决。报告保留其“文字也发生过”的反馈；没有拿本次成功否定它。完成后64.684秒history刷新说明即便气泡正常，页面整体仍可有慢传输。

## 7. Compact、Noting与Framework Message分别发生了什么

### 7.1 压缩摘要在库，在本次cards内

21:41:41提交的压缩摘要为row10036，UID `79dddcfc98bc4a2c816c60ab071c869d`，active1、`_compressed_summary=true`，JSON42305B，正文24407字符，确实包含在回环200cards响应。

该载体timestamp继承为 **当天14:24:18.097**，不是21:41。用户在末尾寻找“刚刚compact”的消息可能涉及排序、投影、滚动或定位，但本轮未精确录制其寻找动作，也未证实唯一原因。不能说摘要DB丢失，不能仅凭DOM中的“Compaction”字符串认定用户看到的就是这一行。

### 7.2 Noting失败而且缺对应反馈

manual admission3的child从21:38:15.280登记到21:51:31.656结束约13分16秒，用户体感15分钟完整保留。50次API、50次工具均为`conversation_history`，没有`notebook_maintain`／`finish_noting`。21:50:57报上限后还有原生摘要收尾，到21:51:31返回`max_iterations_reached(50/50)`。

DB child status failed，Snapshots为空、pointer.current_snapshot_id=null，故`/notebook`空与数据库一致。不是成功Snapshot只在UI里没显示。

原代码 `_turn_completed`要求completed True；此原生结果completed False，进入failed处理。但 `_failed_turn_notice_reason`只在failed／error／failure_reason成立时给失败通知，原生迭代上限结果不满足，故没有失败Framework Message。这与“悬浮球熄灭却没消息”存在直接机制对应。为何模型一直检索属模型行为；保存、状态和反馈的分类属代码机制，用户要求分开处理。

### 7.3 已授权的独立本地修复及验证

所有触发来源（idle／force／manual／auto compaction）统一识别原生每Turn迭代预算耗尽；经原Commit Gate保存合法工作态，以forced结束审计。forced是结束方式，与force触发来源无关。末次已成功finish则保留显式结束。真实error／failure_reason／failed／interrupted不当作预算成功；保留版本、anchor与原子提交限制。

源码仅 `secretary/noting_child.py`、`secretary/noting_notifications.py`；正式回归在 `tests/secretary/test_r3_child.py`，口径同步07。未改生产50次、外层5Turn、Prompt、模型、路由或schema；未重跑生产Noting。

验证由本轮主会话执行，项目PM `.venv`＋官方runner：

- 新增13个边界场景通过，所在r3_child文件54 passed。
- 相关5文件首次合计156 passed／2 failed；两失败均用未改源码复现：旧Snapshot ID正文断言；另一文件活动任务计数污染（完整baseline37 passed／1相同failed）。未写“全套通过”。
- 冻结10检查全过，health 3代码文件、0 blocking／0 advisory；临时index未改真实暂存区。
- `changes/noting-budget-local.patch`含未提交源码、测试与07口径，`validation/`含实际日志与命令索引。接收方不能只看线上仓库就以为这个修复已经部署。

## 8. 认证、连接与发送键

前端`src/api/client.ts:27,100`：freshBootstrapToken先GET `/`（cache:no-store、redirect:error），20秒`Gateway did not become ready`计时从connect开始，**包含取bootstrap而非只等WS101**；失败后有1.5秒重试。

22:03:22—22:04:14约28个mobile `/`302，Authelia对应anonymous_denied_redirect，节奏约1.7—2.6秒。22:18会话页再次302。该形态与登录态不足时bootstrap重试相容；没有证据说明微信Gateway进程当时未启动。

Authelia PID35490自10/19 16:44，Redis PID21608自10/19 16:04，均NRestarts0。22:21cookie元数据显示存在secure／httpOnly／Lax的认证cookie、domain及未来expires；**cookie存在不证明服务器session仍有效或已经满足2FA**。未取得跳转前cookie值、认证等级、Redis会话对应审计，所以不能判手机浏览器bug、设备切换丢cookie或确切过期策略触发。

Send状态除了connected，还依赖live.active是否已恢复、draftReady、pendingBusy、uncertainSteer等。草稿来自本地能先出现；connected恢复也不等于运行态恢复完成。22:35实际采样28秒时灰、34.046时恢复，timeline大更新又在36—38秒。22:37 ready26.874，Send29.281采样亮。用户22:00才随Reminder恢复的早期现场没有内部状态，不能把某个predicate指定为其根因。

## 9. HTTP／WS分工、Runtime内存与跨入口历史

### 9.1 哪些请求走哪里

| 通道 | 当前主要内容 |
|---|---|
| HTTPS GET `/`／静态资源 | HTML及bootstrap，JS／CSS，认证可重定向 |
| HTTPS REST `/api/sessions` | 侧栏summary列表、分页；会话summary title／存在性、full metadata usage fallback |
| HTTPS REST `/api/sessions/{id}/messages` | 最近200cards、向前分页、detail_row_ids详情批次；微信完成的持久普通消息也由此读取 |
| HTTPS REST `/api/fs/download`等 | 图片／附件，上传另走文件接口；Base64内联图片也可能在cards JSON里 |
| HTTPS REST PATCH等 | 已有会话元数据写入等，非所有用户交互都走WS |
| WebSocket `/api/ws` | gateway.ready、capabilities；profiles.list／model.options／commands.catalog／config.get；session.resume／activate／events.since／active_list；prompt.submit_idle／steer／interrupt／compress；secretary状态与排期RPC |
| WS推送 | thinking／工具／输出／user_committed／source_committed／status／session信息／secretary状态变化及完成事件 |

WS是RPC＋流式事件通道；REST是持久历史主要数据源。成功握手、ready、replay完成、Runtime状态就绪、历史完整，是不同阶段。

### 9.2 22:34实际进程／对象快照

| 对象 | 观察值 |
|---|---|
| system Web服务 | PID688083，自17:58:14，NRestarts0；RSS564168KB、27线程 |
| user微信Gateway服务 | PID688086，自17:58:14，NRestarts0；RSS482792KB、22线程 |
| Web runtime `3c5687de` | started约17:58，stored Session同目标，22:34为idle、running=false |
| Gateway原生control | gateway_state running，active_agents0、active_work空；微信连接正常 |
| 两进程打开Alex DB | `state.db`同inode956088，WAL922312、SHM957545也相同 |

active_agents0只代表公开控制接口给出的活动工作，不代表Gateway不存在任何闲置缓存Agent。没有公开只读接口枚举全部缓存对象，本轮未对生产做堆注入、暂停或dump，不冒称看见所有Python内存对象。RSS是一次快照，不是泄漏结论。

Web的session.resume复用本进程Runtime，冷态才创建／异步加载；发消息前 `tui_gateway/prompt_turn.py:_adopt_out_of_band_turns`补采共享DB的新跨入口内容。Gateway有自己的Agent缓存与load_transcript路径，原生TurnLease约束写入。**Web发一条消息不等于每次销毁Gateway Agent再造一个UI Agent**，本晚Web runtime id持续同一个。

22:21resume快照seq842，末个message.complete834，覆盖22:00Web宿主Turn但未含22:07／22:09微信Turn。快照先显示非微信最近Turn、持久REST稍后带来微信内容，和用户桌面反馈相符。这里说明现有读取来源和顺序，不把它升格为本轮生命周期重构目标；用户明确该机制未在本轮改动、主线仍是手机体验调查。

### 9.3 桌面滚动

前端 `src/components/chat-presentation.tsx` 的 `useTimelineReading`管理following／anchor，并在nodes／resize变化时读位置。代码存在这种布局恢复机制，不等于证明它就是用户无人操作上跳的触发点。本轮未有该桌面操作的屏幕／scrollTop连续记录；“往下到底可见微信内容”保留为用户观察。

## 10. 用户反馈覆盖表与证据等级

完整原始反馈另附 `user-feedback.md`，这里将每项对应到调查位置，避免只总结成“手机网络差”。U=用户观察，S=服务端，C=客户端采集，R=正式代码／隔离复现；不能互相冒充。

| ID | 必须保留的反馈 | 本报告定位／等级 |
|---|---|---|
| U01 | 原置顶微信会话，微信Turn已结束，手机打开仍慢，桌面快 | §3—5，U/S/C |
| U02 | 手机打开页面近似gateway not ready，不是发消息后 | §8，U/S/R；当时客户端缺失 |
| U03 | 不先归校园网／蜂窝／跨境；4G／5G常在线、多地点、别站正常，调查时可能变快 | §4及原反馈，U；未定位运营商 |
| U04 | Thinking先出而user不见；21:16纯图片确认；纯文字也怀疑发生 | §6，图片R，文字U／本次成功C |
| U05 | 比昨晚title／conversation加载改善，基本不再那样卡 | §2版本及原反馈，U；不重开已关闭列表问题 |
| U06 | Compact message找不到、刷新timeline很久不出 | §4、7，U/S/C；具体卡片位置未验 |
| U07 | 手动Noting约15分钟、浏览器一直前台、其他已出、球停没Framework，再刷新又慢 | §7，U/S/R；主观15m与日志13m16分别保留 |
| U08 | Noting失败后/notebook空，预算上限应提交合法工作态 | §7，S/R，本地独立修复未上线 |
| U09 | 区分模型检索50次不结束与代码收尾；所有触发统一、不是force特例 | §7，已遵照；模型行为未调整 |
| U10 | 想量手机网络、怀疑WS换网稳定性／SSE，前提必须有断连证据 | §4、9，C/S；不预选协议方案 |
| U11 | disconnected消失仍慢／事件似未到；22:04连不上但别站正常 | §4、8，U/S/C；早场未抓手机包 |
| U12 | 草稿已在，Send灰到22:00 Reminder才恢复／Steer | §8，U；当时条件未唯一定位 |
| U13 | 桌面微信切回timeline无人操作上跳，下翻才见末尾 | §9.3，U/R；未复现 |
| U14 | 刷新先出非微信Turn，2秒后微信；问Runtime是否Gateway创建、Web会否回收重建 | §9，S/C/R；只是背景、非改造主线 |
| U15 | 要完整机制／内存谁在跑／网络轨迹，由调查者取证、Astra提方案 | 全文与§2、9；明确内存边界 |
| U16 | 手机PHZ110／Android16／Chrome、USB调试；跳Authelia登录，是否浏览器bug | §2、8，U/S/C；认证原因未闭环 |
| U17 | 登录后加载不完全，后来才完整 | §4首轮，U/C |
| U18 | Wi-Fi约10—20秒体感好一些，最终22:35 Send才亮，本地草稿先出 | §4、8，U/C；换网过渡事实保留 |
| U19 | 切回蜂窝disconnected几秒恢复，包括Send | §4.2，U/C；REST仍慢 |
| U20 | 授权代点一次Send，先开监测；本次文字气泡成功不代表修好，当前网络较好 | §6.2，U/C，唯一代发动作 |
| U21 | 图片体积大可能叠加网络卡顿 | §5—6，用户推测与651KB实测、回执竞态分列 |
| U22 | 今晚手机与微信交替日志、网络日志抓全，材料和报告ZIP留存交给Astra | §2、3、11；原件固定、附件可复算 |

## 11. 交付目录与后续分析边界

ZIP采用白名单打包，包含本报告、用户原文、脱敏证据、采集与归并脚本、正式链路离线复现、未上线Noting修复完整patch、验证日志、SHA256清单和给Astra的交接说明。包中不含生产聊天正文、图片、认证值、真实.env、手机其它站点信息、浏览器原始快照、候选代理配置或未验证性能修复补丁。文件哈希只能验证包内文件未变，不等于敏感原件已对外公开。

本机完整取证目录：`.hermes-dev/pinned-mobile-20261020/`（ignored）。服务器敏感原件位置见§2，当前原件已固定并复核。后续分析可基于报告和附件讨论机制，但以下仍是明确缺口：

1. 早场真实手机包、21:16／纯文字偶发气泡的连续现场。
2. 蜂窝慢正文究竟在哪段网络、是否丢包／拥塞／代理／连接复用等；只有HTTP阶段时序，无TCP／基站层证据。
3. 认证跳转的具体session失效原因与早场Send灰的内部条件。
4. 摘要具体投影／排序／定位和桌面滚动跳转的真实交互复现。
5. Gateway全部闲置缓存的内存对象枚举（本轮未侵入式取证）。

这些缺口不抹去已经拿到的三条独立事实：REST大正文慢传、纯图片即时回执竞态、Noting预算终止及通知缺口。请接收方分别评估，并结合原仓库代码核对正式接线，不用单一“网络差／换SSE／换Runtime”概括全部。
