# Hermes Secretary 当前主看板

## 手机恢复与历史分层加载修复（2026-10-20 00:06 已部署首尔，待真机验收）

用户在HTTP/3暂停及DSH任务包交接后明确要求开始改代码；补充要求保持其它优化，并先加载普通可见内容及Thinking/工具卡片外侧，折叠内部内容随后渐进加载。用户要求不再新增子Agent，root直接实现分层读取与集成；既有三项已在写的实现按原范围交回。线上仍保持仅暂停HTTP/3，不部署代码以免混入DSH协议对照。本轮不改分页200、默认模型、业务Prompt或生产DB/schema/index。

- 基线：主仓`e879cf863142a2277883d37cd57b747be3c68e35`，独立UI`8821080`；原有dirty为本轮诊断/交接文档。主仓PM `.venv`及原锁，UI既有node_modules，不改依赖。
- root：历史`view=cards`可选投影、同接口`detail_row_ids`限12行详情、规格/看板、亲审集成。首屏保留真实身份/顺序/可见正文，折叠正文延后；未加载不冒充空内容，详情不跨compression spine或复活rewind行。默认API保持完整。
- root 亲审收束（本轮新增）：
  - 卡片状态与客户端`toolResultState`对齐：`content:null`在两侧都表示“空结果=complete”，不再出现完整投影/卡片/补水三态互翻；终端残片仅在确有`result`字段时写`display_tool_status`，字段缺失时保留客户端unknown回退。
  - 详情读取尊重`include_compacted`：调用方没要归档展示历史时，不能靠物理行号单取一行；客户端page与detail请求均显式传`true`。
  - 前端补一条对称替换规则：live已显示真实参数/结果、历史行只有延迟外壳时保留live；此前只写了反方向。`compact()`的`refreshHistory`统一带profile参数。
- `mobile_recovery_frontend`：列表同owner合并/取消/渐进结果、恢复标题、已持久化user即时呈现、分层卡片与详情队列、相关行为测试；只改独立UI，不改视觉、分页或业务语义。该子Agent 23:29因额度中断未交报告，文件已由其写入，root补上述两处修复并跑通全部UI套件。
- `web_delivery_backend`：列表/详情可选summary剔除重型origin_json；Web idle成功持久化点的可选accepted_user回执与message.user_committed可重放事件，兼容旧客户端及原生路径；正式合同/生成文件与定向测试。
- `history_read_optimization`：只读legacy历史两次线性扫描替代逐行generation子查询，root已亲审接收；31新增+116既有测试通过，本机合成2191行VM步约1450万→6.67万，不外推云端实测。
- 验证：`tests/hermes_cli/test_history_cards.py` 42项、legacy显示+5个既有回归文件147项、submit_idle相关85项通过；独立UI 57文件/836项通过且typecheck通过；`scripts/check --staged`（临时索引仅本轮20路径）10项ok、health 0 blocking。基线`review.summary`孤立合同声明仍失败，非本轮引入。
- 新增边界测试：显式`/branch`代际不参与详情退休；详情不能翻页或取越权行；卡片+详情逐字段还原完整展示投影（reasoning、tool arguments、工具结果、终端残片）。
- 独立对抗审查（无上下文子Agent，2026-10-20 00:00交回）发现6项，均未被既有套件覆盖，root已复核并修复：
  - F1/F2（高/中）：`view=cards`下重连恢复出的live Thinking被排到回答之后甚至后续消息之后；无绑定live Thinking还会与空壳Thinking同时出现。修：延迟正文时把live Thinking放回其回答之前；未绑定节点归属最后一个延迟回答并清空壳。
  - F3（中）：切会话后、B的history尚未schedule时展开卡片，会沿用A的locator补水。修：`select`清空locator/profile，`prioritize`由controller传入当前会话地址并回退到key。
  - F4（中）：打开会话先串行等`?summary=true`，失败还会阻断history/resume。修：history立即并行，summary仅advisory（404仍路由走），native resume等存在性检查后再发。
  - F5/F6（低）：`exit_code`为整数值浮点（2.0）时卡片与补水后状态翻转；Python接受NaN/Infinity而浏览器JSON.parse拒绝。修：整数值浮点按整数判定，非标准常量拒绝解析。
- 保留不修（已记录）：详情响应`pagination`仍报order/limit/offset但详情忽略它们（客户端不读，契约漂移）；后台补水按整页deferred行排队（规格允许“随后渐进”，真机再定）；`SessionList.refresh(older)`并发窗口在UI路径不可达。
- **已部署（2026-10-20 00:06 +08）**：后端`9a0c479`（父`e879cf86`）已推`origin/main`并快进首尔，重启后PID144598→202401、`/api/health`=200、无schema变更；前端`83285d2`（父`8821080`）已推`origin/secretary`，439文件/manifest`7bd37306…`，原子exchange后live 456文件（17个旧哈希资源保留），入口`index-CRPV46M2.js`与本地dist逐字节一致，旧入口仍200。回滚点：后端`e879cf86`；前端`.secretary-before-83285d2-20261020T000620`（454文件，8821080构建）。报告与receipt在`.hermes-dev/seoul-frontend-20261019-83285d2/`（含首次tar带入453个`._*`、未切换即修正的记录）。
- 真机验收未做：按`.hermes-dev/mobile-http2-retest-20261019/next-round-acceptance.md`的A1–A7由本机DSH执行；单测与部署本身不算验收通过。
- 证据与报告统一`.hermes-dev/mobile-code-fixes-20261019/`；已提交并部署（见上），尚未完成真实手机验收。先前冻结80文件证据不修改；DSH任务书仍按线上旧代码仅协议对照执行。

## HTTP/3暂停与本机DSH复测交接（2026-10-19 23:00起）

用户已明确授权暂停HTTP/3，并要求把之前三轮完整复测写成详细任务书，交给**本机DeepSeek Harness（DSH）的ds coding agent**执行；云端模型仍为Hermes deepseek-flash，不将任务书发送给云Hermes作为编排者。只做协议对照，本轮不改业务代码、DB、索引、分页或压缩。

- 23:00:38–43（+08）应用仅增加`servers { protocols h1 h2 }`的已校验候选并重启Caddy，耗时5.29秒；PID65134→181221，Hermes144598、Authelia35490、Redis21608均保持。新配置SHA256 `16d3de9039648b296602657833bec1f7dc0a619c754276aa6c4ae6b7ff67d2c3`，原配置`1777603b33528967643d271dd58acda818d8956d3841206e74156dd35494dad1`。
- 备份`/var/backups/caddy/http3-paused-20261019T230037/`；本地收据`.hermes-dev/mobile-http2-retest-20261019/cloud-cutover-receipt.json`。验证UDP443不再监听、TCP443保持；loopback TLS+证书+HTTP2正式Hermes匿名302、auth200。手机真实REST协商及三轮恢复表现待独立DSH采集，不能提前宣称问题解决。
- **最新交接口径（用户明确）：只准备任务包，由用户自行命令本机DSH中的ds执行；主会话不再操控或启动DSH。** 详细任务书`docs/mobile-http2-retest-task.md`已完成并在README索引，包含可直接粘贴的交接指令、三轮完整步骤、底层采集、旧基线与交付要求。复测尚未开始，不宣称已派出或通过。
- 先前三次headless交接均在实际模型/测试执行前因凭据或账号服务依赖失败，失败原件保留在`.hermes-dev/mobile-http2-retest-20261019/delegation/`；未改桌面/全局DSH配置。用户收窄范围后已停止这条排障路径，不再处理DSH接入，任务包不依赖这些失败会话。
- **复测已完成（2026-10-19 23:17–23:50，本机DSH ds coding agent执行，未派生子Agent；代码未改）**：报告`runs/20261019T2330+0800/report.md`，同目录`environment.json`/`results.json`/`metrics.json`/`actions.jsonl`/`cleanup.json`/`manifest.json`（128文件10738937B，SHA256 `31176e43addfc62200bec687971f7f902e122bea8083ce17b24f2a745921bec1`，逐文件复核通过；固定副本`preserved-20261019T2352+0800/`）。要点：手机全部REST已h2、无QUIC错误；但590KB列表TTFB中位7.6–13.9秒、单请求最长146秒，R1出现5个`ERR_CONNECTION_ABORTED`；Caddy侧同一URL中位0.03–0.04秒却有115–139秒写出耗时，桌面同窗0.19–0.63秒——瓶颈仍在手机↔首尔路径，协议切换未带来可判定改善。未改代码缺陷全部复现：本端user气泡9–13秒、跨端user直到完成后回读（68.6秒）、R1唤醒90秒内0侧栏且标题“Conversation”，需整页重载才恢复。未恢复HTTP/3、未重启服务；测试QA会话`20261019_232723_ec8c4d`与消息保留，自建ADB转发与自有标签已清理。
- **待验收（用户明确，2026-10-19 23:52）**：另一侧正在改代码；**部署完成后由本机DSH再跑一轮真实双端实测，验收代码修复成果**。验收标准与复用流程已固化在`.hermes-dev/mobile-http2-retest-20261019/next-round-acceptance.md`（A1本端气泡、A2跨端user、A3标题不依赖列表、A4列表合并/取消、A5分层加载、A6旧会话读取、A7一致性与无回归）；触发条件=修复已部署首尔+HTTP/3仍暂停+真实手机/桌面Chrome；不得用“代码已改/单测通过”代替实测，网络路径慢本身不计入代码验收失败。

## 手机Chrome网络故障复查（2026-10-19，现阶段分析完成，故障未关闭）

用户报告：桌面同URL约1秒、手机列表/标题/消息/统计需30–60秒；active turn中断线后恢复困难，刷新或切无active turn的Conversation也受影响。补充：手机始终前台、不锁屏也看不到桌面新建Conversation和user message，不能将故障限定为后台回收。用户已连接ADB并要求开始排查；本轮仅对手机Hermes页进行ADB/CDP取证，不扩大电脑显示操作权限。

- 现场设备PHZ110 / Android16；ADB Chrome Hermes tab2479。首尔Hermes/Caddy/Authelia/Redis均active，未重启或改配置。
- 首次页面Resource Timing：HTML约0.417秒；messages HTTP/3约25.607秒（TTFB0.369秒，正文25.236秒，273982传输bytes），随后详情约11.978秒（TTFB0.587秒，正文11.387秒）。静态资源命中缓存，不能把HTML成功当完整可用。
- Caddy同25分钟窗口：手机113条REST/资源HTTP/3、5条WS HTTP/1.1升级；桌面145条HTTP/2、8条HTTP/1.1。手机约585KB列表最长72.8/82.6/84.3秒；桌面同类列表0.318秒。当前手机已完成请求无302/401，仅200/101；不能由此排除未完成/客户端失败请求。
- 用户提出跨境UDP/QUIC不稳定假设。现证据支持协议路径差异，尚未做同手机同网络HTTP/2对照，不得断言蜂窝网络或UDP封锁为根因；WS另沿TCP需独立解释。
- HTTP/1.1+HTTP/2候选已在首尔`/var/backups/caddy/mobile-h3-20261019T222805/`校验通过、原配置已备份，尚未应用。Caddy admin off，不能依赖热reload，实际需短暂restart；用户明确暂不验证、保持现场，该阶段候选未应用（后续用户放行并暂停HTTP/3见顶部新交接）；先深入只读取证，由用户另一侧DeepSeek复核下午事故监测。候选影响共用443监听的域名，不终止Hermes任务。
- 用户追加明确授权：直接操作真实手机Chrome及桌面Chrome，可从任一端发起Turn并比较流式/刷新/切会话/断线恢复；**实测只用DeepSeek，不用Kimi**。R1通过桌面正式UI选择`deepseek-flash`后发送10×30秒顺序terminal休眠，Conversation `20261019_223240_2dc5b2`／Runtime `5d7275a5`；中断前只填草稿，未发送Kimi请求。两端CDP仅采元数据，敏感NetLog类别不启用。
- 已证代码放大：`loadSessions`普通刷新无single-flight/取消/并发上限，逐事件重读全部Profile；allSettled等慢Profile，generation淘汰旧结果不终止下载。后端55行584934bytes，`origin_json`序列化约498823bytes；回环headers36.9ms/body0.8ms。HTTP内容无压缩。该机制不等于单次网络慢的根因。
- R1手机首次messages5987bytes/0.867秒、流工具正常；列表约586KB三次37.3/54.2/55.7秒。桌面已有标题、手机Conversation：顶部只读sessions，未采用active resume info.title；输出snapshot无title但水位跳过旧title，缺列表行的title事件也只触发全表。源码证据充分，尚未保存该次resume字段原件，不冒充wire事实。
- 人为刷新时间22:34:57（+08），已标记；随后WS约1.3秒ready、history约4秒恢复，不能当自发断线或永久失败。用户前台手动切其它会话messages约6.8秒，切回R1约4.2秒；保留用户“3–5秒可接受”现场观感，不宣称所有路径顺畅。22:37:05开始30秒真实灭屏/唤醒测试，桌面保持运行。
- 原始NetLog已见QUIC收发与PTO retransmission枚举，但browser级可能包含其它连接，当前未完成目标源关联，不能给出丢包率或断言被拦；手机本轮已完成REST仍200，无抓到Failed fetch精确底层码。下午事故v2为Caddy→9091回环3秒dial超时/502，当前窗口Caddy错误级为空，不合并根因。监测复核由用户另一侧DeepSeek进行。
- R1灭屏已复现真实底层失败：22:37:11手机WS关闭；22:37:35唤醒时7个已有200/h3响应头但未完正文的sessions请求同时`net::ERR_QUIC_PROTOCOL_ERROR`，同窗口NetLog quic_error85（官方QUIC_TOO_MANY_RTOS）。bootstrap请求另因本地20秒ready超时被Abort（不是同一种故障）。22:37:39.5 gateway.ready；列表Failed fetch错误至R1完成刷新才清。R1实际87个列表请求、28个大列表；手机大请求18.4–58.7秒，7失败；未完成列表峰值19（含三Profile小请求，不能写成19个大列表）。桌面同窗无相同失败。NetLog为browser级，不能据未关联来源推丢包率/运营商封锁。
- R2正式手机UI/DS发送两次30秒terminal，电脑一直在线接收Thinking/工具，但user message直到`message.complete`后history刷新才补齐（3条对比时当时为phone2／desktop1）；R2约66秒后两端均完整。第二工具start桌面约快0.22秒、complete约快0.45秒，属正常到达延迟样本，不与失败合并。
- 用户要求先固存再继续：R1/R2固定副本`.hermes-dev/mobile-network-20261019/preserved-r1-r2-20261019T224207/`，41文件/15051885bytes，manifest SHA256 `e785a75991626d5f34cac5f26c4fe5b885665a9b6c0187671f5309094b42fdd3`逐文件复核通过；不修改该副本。
- R3用户点名300秒实测：同Conversation从手机DS正式发送10×30秒terminal；22:43:33关闭手机target2479，重开同URL得到2480，历史33.8KB/5.20秒、恢复活动流，但侧栏0链接/Loading与Conversation标题持续。保存截图/AX摘要后22:44:56关闭2480并改开不同旧Conversation URL得到2481，旧历史273.7KB/24.06秒，详情89.3KB/10.81秒；另一个Turn仍运行时同样慢。侧栏仍Loading/无入口，22:46:08按已知URL整页切回R3（不是SPA成功），历史42.4KB/3.47秒后恢复流。活动resume wire实见info_title_present=true/model=deepseek-flash，输出snapshot无title，补齐源码结论证据。
- R3桌面同活动会话22:46:53刷新：HTTP2列表586.7KB/1.20秒、历史45.8KB/0.607秒，约4秒内UI采样完整标题/列表/Stop；中间瞬态显示Profile默认K3不等于发起Kimi请求，未点击Send。R3仍运行，最终完成/收尾证据待收，不提前签全场景通过。R3所有原件单独在`mobile-network-20261019/r3/`。
- 用户后续正常样本（必须保留，不泛化缺陷）：手机新建Conversation后user气泡正常、电脑列表很快出现新会话；用户未复现自己手机该次气泡消失。因此本端问题限定为连接/拥塞时显示健壮性，不称手机必现或发送丢失。另有R2跨端user直到完成才回补的独立受测证据，不能拿它替代原始本端问题。
- R3本端原件已闭环：手机submit_idle回执22:43:04.344、message.start22:43:04.367，自己的第3个user气泡约22:43:17.242才出现；post-submit history33.8KB请求在浏览器sendStart等待10129.8ms才发出，随后收到头并很快读完，支持请求积压时已接受输入缺临时显示保留。消息最终存在，不宣称数据库丢失。
- R3已完成：两端message.complete约22:48:20，十次休眠最终DONE；phone之后仍无完整列表/标题的样本已保存；桌面后续用户自行浏览其它Conversation，主会话不改变其选择。无新增模型任务/协议切换/服务重启。已有有界采集完成后转分析。
- 长导入会话用户追加量化：最长Pi041 path3共2191原生消息，正式latest/include_compacted/inline_images读取200条1148602bytes、100条707029bytes、50条290653bytes；云端loopback对应首头11.94/10.61/15.98秒，非仅网络下载。真实桌面该200页13.38秒，其中首头11.22秒、正文2.15秒；还需查服务端读取机制，不能宣称只改分页就解决。只读CPU profile已完成：50条17.224秒主要在_legacy_display_page；仅2条缺展示索引使2191条全量回退，SQL另有逐条generation相关子查询。未修改生产数据库/索引。
- 最终证据固定副本：`.hermes-dev/mobile-network-20261019/preserved-complete-20261019T225604/`，80文件/39921645bytes，manifest SHA256 `96c02bd4395b22821eeb52a0e4013fbc10eaac3560c21c6f777b5166246fe080`，逐文件校验通过；原R1/R2副本仍原样保留。R3跨目标事件按seq去重确认1次message.start/10次tool.start/10次tool.complete/1次message.complete。自建ADB19222转发已移除，用户手机/电脑现有页面保留，不关闭其它页面。
- HTTP/3旧基线分析整包：`.hermes-dev/mobile-network-20261019/analysis.md`；该阶段有界采集已完成，冻结原件按当时时点保留。该阶段尚未进行同网HTTP2对照、修改代码或协议配置；后续用户放行的协议暂停、DSH交接和本地代码修复以顶部当前看板为准，不能将旧“保持现场／未修改”当现行禁令。
- ignored证据：`.hermes-dev/mobile-network-20261019/initial-timing.json`、`server-access.jsonl`、有界CDP采集。Cookie/token不保存。只读代码研究子Agent `mobile_recovery_readonly` 不改文件、不部署、不操作UI；主会话亲自取证/复核。


## 提示词修订台账（2026-10-19，用户要求记录）

用户已明确：先自行弄清「稳定识别表面」的问题，再处理微信接入；**凡涉及表面识别的改动一律搁置**。

**已完成（本地工作区，未提交、未部署）：**
- **note 文案**：`agent/memory_manager.py` 改为 `The following is recalled memory context, possibly relevant, not user input. This is the agent's persistent memory.`，去掉 `[System note: …]` 标签；`_INTERNAL_NOTE_RE` 与前端 `nativeMemoryNote` 兼容裸句/带标签/全部历史文案；`tests/agent/test_memory_context_note.py` 7 项通过。
- **Scheduler**：`agent/system_prompt.py:48` 删掉 `and stay quiet when there is nothing useful to report`；文档副本 [07:1280](docs/07-scheduler-notebook-noting-compaction-redesign.md#L1280) 同步。
- **SOUL 第 30 行**：删掉「每个新会话你都需要先概览记忆」义务句，保留「必须通过记忆了解用户」，已同步首尔。
- **Skill 阈值**：`agent/prompt_builder.py` 改为「实际做工作前，先看 matches 与相关 skill」，去掉 `even partially relevant MUST … Err on the side of loading` 的绝对化表述。

**未做（与表面识别无关，仍需处理）：**
- **第 4 条 编排 vs Finishing**：SOUL 加分流句，拟放第 32 行后，拟稿「小闭环（单文件、几步命令、即时可验证）由你直接做完；长任务、并行、项目型或需要改代码的，编排给 Agent；最终验收始终由你负责。」待用户确认措辞。
- **第 5 条 主动核实白名单**：尚未设计，需定义「可主动触达」的四类边界。

**搁置（等用户弄清稳定识别）：**
- **第 7 条 表面提示**：`PLATFORM_HINTS["tui"]` 中「You are in the Hermes terminal UI (TUI)」的身份句，以及所有按客户端/进程判断表面的方案。

**已关闭：**
- **第 6 条 身份分层**：用户判定不构成问题。
- **第 9 条 Profile 显示名**：`2a6bcb5` 已修，首尔实测 `profile_name_for_home('/home/ubuntu/.hermes_profiles/Alex') == 'alex'`。

**相关交接**：[.hermes-dev/handoff-20261019-wechat-and-surface.md](.hermes-dev/handoff-20261019-wechat-and-surface.md)（两个问题、已查事实、待决事项）。

## 自主口径收敛 · 待用户追认

**UI-CAM-01 · Agent自主收敛／待追认：** 用户要求Take Photo上传前压缩，未指定参数。暂定仅拍照入口长边最多2560、JPEG质量0.85、不放大、小图/更大结果保留原图、失败回退原图并反馈；其他入口原字节不变。影响拍照草稿bytes，实施中，待实际效果追认；已向用户显式汇报。以下为已确认口径及关闭记录。

**AC-03 · 历史自主收敛已被PI-24调整：NM Thread同步不一致时不再以永久暂停作为目标行为。** 用户要求自动定位分叉点、新Thread首条接续旧NM Thread/原生Message ID、后续仅保存分叉内容。原5秒Notice/晚到重放仅为既有降级通路，成功分叉不得继续误报暂停；分叉无法安全完成时保留准确失败反馈，不自动覆盖或删除旧Thread。旧受控证据保留，不再以旧暂停场景单独设置上线阻塞。v4真实NM分叉22项对账通过；root发现的编辑后旧尾部显示已由v5正式读取修复、原A冷REST/隐藏UI及独立复审关闭。本项无剩余待追认决定；准确降级反馈仍保留。

AC-01已确认：Candidate用Notebook refs或Message Identity，二选一禁止混用；refs按Memory/Rule/Skill身份特化简述，不复写源正文。AC-02同源分页及配套文字已确认。先处理真正交付覆盖来源，最后关闭Candidate，未交付部分保留。

## 图片气泡、Memory隐藏与拍照压缩（2026-10-19，进行中）

用户明确：用户气泡直接隐藏原生memory-context及System note，图片显示受最大宽高限制的缩略图；不改原始消息/model API内容。现场JPEG6202636bytes、3072×4096，历史content为[Image attached at:path]＋[screenshot]＋memory-context，无@image/inline image，现有UI遗漏此持久载体。System note由原生MemoryManager包装、官方基线同样，不是个人Provider文案；多模态持久化需按真实载体投影。用户进一步明确确认后端note采用两句：`The following is recalled memory context, not user input. This is the agent's persistent memory.`；删除authoritative reference data及should inform all responses，兼容清理旧包装，不重写历史API sidecar。2026-10-19 18:40 用户再次改口径：**去掉 `System note` 标签，直接陈述**，并加入 "possibly relevant"，现行文案为 `The following is recalled memory context, possibly relevant, not user input. This is the agent's persistent memory.`；后端 `_INTERNAL_NOTE_RE` 与前端 `nativeMemoryNote` 同时兼容裸句、带标签句与全部历史文案。

分工：root负责后端note及来源调查/集成/发布；bubble_memory_images只改UI content/attachments/App与定向测试；camera_compression只改ChatComposer与camera-image helper/tests，互不交叉。两Agent不commit/deploy，root亲审后统一构建。

## 聊天共用磨砂流光背景（2026-10-19，本地预览版）

用户确认仅改表现层，由主会话独立实现，不委派。New Chat 与 Conversation 共用覆盖整个聊天主面板及 Composer 的背景；磨砂漫射、高模糊、柔和低饱和度，参考现有 Warm Foundation / Cool Accents 色卡。明暗模式分别调校颜色与视觉参数。两态均持续可见地流动，保护文字、气泡、Composer 的清晰度及既有业务行为。

最新视觉口径：拒绝几片色带、长条拉伸和锋利轮廓；采用连续的火雾质感，以流淌为主、减少翻卷。首页主要在画布中间、标题下方附近流淌；进入 Conversation 较快速向边缘移位，随后以常态速度沿四周流淌，允许偶尔漫入中心，不出现明确分界；返回 New Chat 反向聚拢。用户补充：暖陶／浅琥珀流光的实际视觉占比应略高，不能只按参数比例判断；冷暖倾向随时间缓慢变化，有时偏暖、有时稍偏冷，保持交融而非整屏换色。已撤换色带实现，改为连续噪声密度场与平流驱动；同一背景在约1秒内聚散移位，常态持续流动，冷暖缓慢变化。改动限独立UI的 `src/design/ambient-backdrop.tsx`、`layout.tsx`、`theme.css` 及本段/06规格，未改业务逻辑、未提交或部署。类型检查、24项Mock测试、31项表现层集成测试通过；隐藏IAB验证真实WebGL渲染、明暗模式、New Chat↔Conversation及320/390宽度首页，浏览器错误日志为空。无真实手机GPU性能结论；本地视觉候选待用户动态观感反馈。预览沿现有5174 Mock入口。

## 部署转向：首尔轻量服务器（2026-10-19 用户决定，当前目标）

**用户已全面转向：不再在现北京云服务器上部署，改在腾讯云首尔地域新购轻量应用服务器（2 vCPU / 4 GiB / 60 GiB SSD），迁移 NM（Nowledge Mem）与 Ebbinghaus（爱宾豪斯）数据托管；NM 此后不再使用本地 embedding，改用云端 embedding 服务。**

- **性质与当前状态**：用户口径确认；**首尔正式Hermes／Ebbinghaus／NM入口及原生数据已迁入；NM索引重建完成，Hermes Profile身份修复与最终验收进行中**。北京源端保留数据备份，相关业务已停止。
- **最新只读复核（2026-10-19 15:28 +08:00）**：首尔 `hermes-secretary.service`、`caddy.service`、`authelia.service` 均为 active/enabled；仓库 HEAD `5bb20e54ed6a`；内存 3659 MiB 中使用 801 MiB、可用 2858 MiB，4095 MiB swap 使用 0；根盘 59 GiB、使用 11 GiB、可用 47 GiB。`/var/run/reboot-required` 已不存在，不再列为当前待办；本次未执行重启或服务变更。以下初始化、凭据准备与入口部署段保留各时点过程，先前“尚未部署／待上传 Key／待放行 443／待绑定 TOTP”等状态由后续完成记录取代。
- **私钥与接入**：私钥已落位 `~/.ssh/seoul_vps.pem`（600，RSA 2048，原下载目录已清空该文件）；SSH 别名 `seoul` 已写入 `~/dotfiles/ssh/.ssh/config`（HostName/User 仅存本地，不写入仓库），待现北京实例清除、最终确认无误后再改名为 `alex`。**私钥不得写入 Git、不得放进 `~/dotfiles`、不得上传云端**。
- **接入与网络实测（2026-10-19）**：`ssh seoul` 可用；Cloudflare `cdn-cgi/trace` 返回 `colo=ICN`、`loc=KR`；到 `1.1.1.1` **1.75 ms / 0% 丢包**，到隧道边缘 `198.41.192.227` **1.34 ms / 0% 丢包**（对照北京机 292 ms / 62.5% 丢包）。
- **大陆直连实测（2026-10-19，本机关闭 VPN、Clash 走 DIRECT、服务器端确认源为陕西电信出口即真直连）**：ICMP 平均 **62–66 ms**（min 52 / max 160，stddev≈20 ms），丢包 **0–5% 且呈突发型**（30×1 s 为 0%，100×0.2 s 为 3%）；SSH 握手 **0.57 s，5/5 成功**；MTU 1500（DF 1472 通）无分片问题；吞吐单流下载 11.5 Mbps、上传 12 Mbps、4 并发聚合 22 Mbps，本机国内基线下行 100 Mbps（清华源 12.6 MB/s），说明瓶颈在国际段而非本机带宽或服务器；下载过程中延迟无明显抬升（并发 25 包 4% 丢包、均值 62 ms）。**结论：相对北京机（292 ms / 62.5% 丢包）延迟约降 4.5 倍、丢包趋零，长肥管道单流受 RTT 制约、多流可叠加；真实浏览器经域名/Tunnel 的路径仍未部署未验。**
- **现北京服务器**：不再是部署目标；其上 Hermes/NM/Ebbinghaus/OpenClaw 等保持现状作过渡运行，不再为该机做降配、迁移或隧道改造。
- **迁移范围**：NM（Hermes 侧使用）与 Ebbinghaus 数据托管；**OpenClaw 不迁移**（用户明确新机上不再使用）。
- **Embedding**：NM 已采用用户确认的阿里云专属Host／`qwen3.7-text-embedding` OpenAI兼容接口，不加载本地GGUF；Key仅在首尔受限运行环境。成本/内存估算见 [cloud-embedding-sizing-estimate.md](docs/cloud-embedding-sizing-estimate.md)。
- **目标规格一致性**：2C4G 与本轮估算结论一致（4G 为下限，2G 不可行）；迁移时需同时确认 NM `MemoryMax`、journald 限额与 swap 配置。
- **系统初始化进度（2026-10-19，用户同意后执行）**：Ubuntu 24.04.4 / kernel 6.8 / x86_64，2 vCPU、3659 MiB 内存（可用 ~3150 MiB）、59 GiB 盘（已用 5.2 GiB）；时区出厂即 `Asia/Shanghai`；**swap 已由 2 GiB 调整为 4 GiB**（`/swap.img`，fstab 已挂载），`vm.swappiness=10`（`/etc/sysctl.d/99-swap.conf`）；passwordless sudo 可用；已有 git/curl/python3.12/ufw/nft，待装 pip/venv/Node 22/uv；无全局 IPv6；仅 sshd 监听。**API 连通性探测**：`api.deepseek.com` 可达、TTFB 180–230 ms（北京对照 98–119 ms）；Kimi 国内端点 `api.moonshot.cn` 可达但 TTFB 280–2425 ms、TCP 50–1230 ms 抖动大（跨境 RTT ~165 ms，北京对照 118–170 ms）；国际端点 `api.moonshot.ai` 首尔 116–152 ms、Kimi Coding Plan 路径 `api.kimi.com/coding/v1` 首尔 320–450 ms。**未使用任何真实 API Key**（用户明确：暂不带 Key 上云）。**SSH 加固（2026-10-19 13:29，用户明确要求，覆盖此前“保持现状即可”口径）**：新增 `/etc/ssh/sshd_config.d/01-hardening.conf`（`PubkeyAuthentication yes`、`PasswordAuthentication no`、`KbdInteractiveAuthentication no`、`PermitRootLogin no`）；`01-` 字典序早于 `50-cloud-init.conf`，主配置第 12 行 `Include` 在前、sshd 取首次值，故加固项生效。`sshd -t` 通过；`sshd -T` 在默认上下文与 `-C user=ubuntu,addr=…` Match 上下文均显示加固值；reload 前布置 120 秒 systemd 自动回滚并在成功后取消。实连验证：密钥登录成功、密码登录与 root 登录均 `Permission denied (publickey)`、`sudo` 正常、`ssh` active/enabled。**未启用 ufw（用户明确），继续只用腾讯云 Lighthouse 防火墙。** `ubuntu` 免密 sudo 来源不变（`/etc/sudoers` 两行 `NOPASSWD` + cloud-init drop-in）；账户仍存镜像随机密码（`$1$` MD5），已不能用于 SSH。

- **基础初始化（2026-10-19）**：`apt update && upgrade` 完成（libc6、apparmor 等已更新；**当前存在 `/var/run/reboot-required`，尚未重启，待用户决定**）；时区确认 `Asia/Shanghai` 且 NTP 已同步；安装 build-essential、python3-venv、python3-dev、sqlite3、jq、unzip、rsync、htop、iotop、sysstat、mtr-tiny、ncdu、tmux；运行时为 **Node v24.22.0 LTS**（NodeSource apt）、**uv 0.13.1**（`/usr/local/bin`）、**uv 管理的 CPython 3.14.8**（`/root/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu`，符合项目 `requires-python >=3.11,<3.15`）；系统 Python 3.12.3 保留未动。磁盘已用 8.0 GiB、可用 49 GiB；journald 用量 16 MB、未设 `SystemMaxUse`；unattended-upgrades 已启用。**未部署 Hermes、未建 venv；部署时须完整按 [cloud-deployment-sop.md](docs/cloud-deployment-sop.md) 执行。**
- **凭据测试准备（2026-10-19，未读取任何真实 Key）**：`/etc/secrets` 已建为 `root:root` 700，等待用户自行上传 `deepseek.key`、`kimi-code.key`（`root:root` 600）；探测程序 `~/scrips/provider-probe.py`（仅标准库；读 Key 文件但绝不打印/落盘/记录，错误文本经 `***` 脱敏）。已用假 Key 自测两个端点：TLSv1.3、401 预期返回，DNS 2–3 ms、TCP 3–4 ms、TLS 6–8 ms、TTFB 197 ms（DeepSeek）/ 418 ms（Kimi Code）。**待用户确认上传完成后再跑真实认证、流式首 Token 与错误场景测试。**
- **Provider 真实连通性验证（2026-10-19，用户授权后执行；凭据仅在进程内存读取，未输出内容）**：Key 元数据合规——`/etc/secrets` root:root 700；`deepseek.key` 35 B、`kimi-code.key` 72 B，均 root:root 600。**DeepSeek** `POST https://api.deepseek.com/chat/completions`（`deepseek-flash`，stream）：HTTP 200、TLSv1.3、13–14 分块、`finish_reason=stop`、usage 37 in / 12–13 out；TTFT **218–233 ms**、总耗时 862–979 ms；DNS 2.4 / TCP 3.7 / TLS 7.4 ms。**Kimi Code** `POST https://api.kimi.com/coding/v1/chat/completions`（`k3-256k`，stream）：HTTP 200、TLSv1.3、23–31 分块、`finish_reason=stop`、usage 93 in / 35 out；**首字节 3.32–3.41 s（先出 `reasoning_content`）、首个正文 4.26 s、总耗时 4.27–4.29 s**；DNS 3.0 / TCP 2.5 / TLS 5.9 ms。端点依据源码 `hermes_cli/auth_zai_kimi.py`：`KIMI_CODE_BASE_URL = "https://api.kimi.com/coding"`，`sk-kimi-` 前缀 Key 经 `_resolve_kimi_base_url()` 指向该地址，属 Coding 会员接口，**未使用 Moonshot 按量计费端点**。连接质量：两端点各 **10/10** TCP+TLS 成功，DNS 0.6–2.1 ms、TCP 1.4–2.5 ms、TLS 4.6–10.7 ms；分别解析到 CloudFront `3.173.21.63` 与 Cloudflare `104.18.21.246`（均为首尔边缘）。异常：测试期间一次 SSH 入站连接被关闭（重试即成功），Provider 侧 0 失败；主机 iptables 存在腾讯「云镜」自动封禁（`109.160.32.128`、`109.160.32.34` 的 22 端口 REJECT），本人来源 IP 未被封。临时文件已清理，除 `/etc/secrets` 外无凭据副本。
- **测试入口部署（2026-10-19，未完成公网验收）**：首尔机已装 **Caddy 2.11.7**（`/etc/caddy/Caddyfile`，`admin off`）、**Authelia v4.39.28**（GitHub Release 二进制 + 官方 checksums 校验，`/etc/authelia/configuration.yml`，服务用户 `authelia`）。布局按 `ubuntu` 用户适配：仓库 `~/hermes-secretary`（HEAD `5bb20e54ed`，与已验候选 `0dc4232f59` 同代码）、`.venv` 由官方 PM + 既有 lock 构建、双 SPA 在 `~/.local/share/hermes-secretary/static/{secretary,dashboard}`（**439/439、67/67 文件 SHA 全匹配 manifest**）、后端 unit `hermes-secretary.service` 绑 **127.0.0.1:53446**、Authelia 绑 **127.0.0.1:9091**。路由：`auth.edgarzhong.fyi` 仅反代 Authelia；`test.edgarzhong.fyi` 经 `forward_auth`（`/api/authz/forward-auth`）后反代 Hermes，向 backend 改写 Host 并删除 Origin。证书：Let's Encrypt **http-01 成功签发**两个域名（说明 80 通、**443 被腾讯云轻量防火墙拦截，待用户放行**）。已验证：未登录全部 302 至认证门户（含 `/api/ws`、`/api/pty`）；登录后 `/`、`/dashboard/` 200，`/api/sessions` 带注入 token 200，`/api/ws`、`/api/pty` 均 **101**；仅带 Cookie 无 token 的 WS 仍 403。**TOTP 注册链路**：v4.39 把 TOTP 存 DB（users 文件 `totp:` 字段无效），注册需先 `POST /api/user/session/elevation` 触发通知 → 从 `/var/lib/authelia/notifications.txt` 取 **8 位字母数字** 一次性码 → `PUT` 提交换取 elevation → `PUT /api/secondfactor/totp/register` 得 `base32_secret`/`otpauth_url` → `POST` 提交 6 位码完成。临时账号 `pwtest`/`e2e-temp` 已全部删除，`edgar` 无 TOTP、密码为未知随机值（锁定）。**密码初始化脚本** `~/scrips/authelia-set-password.sh`（Argon2id m=64MiB t=3 p=4，argon2 CLI 从 stdin 读密码，不经 argv，只改 password 行，原子替换后重启服务）。**2026-10-19 14:42 用户已完成密码设置、TOTP 绑定与首次公网登录（`totp_configurations.last_used_at` 有记录）。** 公网 443 已由用户放行（此前仅 80 通）；外部实测（北京机）`test` 302 → 认证门户、`auth` 200、HTTP/2、Let's Encrypt 证书有效（2027-01-17 到期）。**Fail-Closed 已实测**：停 Authelia 后 `test`/`dashboard`/`api/ws`/`auth` 全部 **502**，恢复后回到 302。登录后验收（临时账号 `pwtest`，已删除）：`/`、`/dashboard/` 200；带后端注入 token 的 `/api/sessions` 200；`/api/ws`、`/api/pty` 均 **101**；仅 Cookie 无 token 的 WS 仍 **403**；60 秒级未出现断连。**注意**：v4.39 的 TOTP 注册必须经过 `session elevation`，而 elevation **绑定客户端 IP**；用户线路为电信 CGNAT（观测到 `124.114.148.30` → `113.140.3.69` 同一会话内变化），浏览器内注册因 IP 不匹配失败，最终改用 `authelia storage user totp generate` 在服务端注册并以二维码交付。**该限制保留**：今后新增/重置第二因子需从稳定出口 IP 操作或继续用 CLI 方式。一次性二维码 `~/totp-enroll.png` 与 `/root/authelia-totp-uri.txt` 已 shred 删除。
- **已放弃**：经现有机场香港节点做 Cloudflare Tunnel 出站代理。实测机场在 SNI 层拦截 `h2.cftunnel.com`、放行 `region1.v2.argotunnel.com`，cloudflared 数据面无覆盖开关（2024.12.2 / 2026.8.2 / 2026.10.1 均用 `h2.cftunnel.com`）；实验已完整回滚，生产保持 4 条 LAX 连接、PID 未变。
- **历史看板**：以下「最终公网验收与清理」「云部署已运行」等章节保留为当时证据与边界，不再作为当前目标。

### 首尔前端更新（2026-10-19，已提交、构建与上线）

用户要求将最新表现层改动重新打包，并先提交独立前端仓库。已提交`../hermes-secretary-web`的14路径（新版共用流光背景、侧栏Pin及owner处理、Noting计时与配套测试），提交`3a674f1eb4a2dbf9a0d254fe7f1118ec6fa5f7c7`已自动推送，`ls-remote origin refs/heads/secretary`同SHA，工作区干净。

- 验证：5个相关测试文件共62项通过；`npm run typecheck`、`npm run build`成功。构建保留既有大chunk和jszip浏览器外置模块提示，不改门槛。未运行无关全量套件。
- 产物：439文件／22638767字节，外置manifest SHA256 `c6a81e7934d4d0f67360af5212183e586fdf0a7a47f00c492aaa39b60ba1fafc`。首尔逐文件集合／大小／SHA核对通过，16:34:45以Linux原子exchange更新Secretary目录；保留3个旧哈希资源供旧页面使用。旧完整目录位于`/home/ubuntu/.local/share/hermes-secretary/static/.secretary-before-3a674f1-20261019T163445`。
- 实际验收：真实Chrome「Edgar」测试站刷新后仍登录；加载`index-CNc-teN4.js`和`index-C4MBQJq3.css`；背景canvas ready=true，浅／深色截图已查看，主题恢复跟随系统。未发送聊天或调用模型；未实测Conversation动画、手机GPU与长时性能，不扩大验收结论。
- ignored证据：`.hermes-dev/seoul-frontend-20261019-3a674f1/`含manifest、生产包、部署receipt和浅／深色截图。Dashboard、认证、后端产物及进程保持；无需服务重启。Ebbinghaus首尔副本已停，源机继续服务，迁移切流尚未实施。

### 首尔迁移与配置收敛（2026-10-19，服务侧完成）

**最终权威状态（覆盖本节下方过程记录）：** 首尔NM原生数据库/配置迁移、阿里OpenAI兼容embedding接入与全量原生索引重建已完成；独立只读验收PASS，原令牌不变，正式nmem受保护接口401/200、context/search成功。Hermes生产Noting/Scheduler开启，Alex Idle500秒/131072tokens，NM Provider配置恢复；Kimi凭据、Search/Fetch及Playwright真实验证通过。三同步点已运行并实际内容验证：workspace双向、8配置双向、300秒云DB完成包自动回传Mac。UI最终`974a51f`439文件已上线、test404。

**Profile根因已修复并上线：** Core提交`2a6bc5b00d803b0ef6211cf0dd1a7d65bd3c29dd`已自动push，首尔快进同提交；本机相关259通过/9平台跳过、4相关检查通过，首尔18定向节点全部通过。修复canonical注册身份反查，保留default，不做选择器过滤、不搬Home、不改历史pi-import/custom metadata、不重写已有缓存Prompt。首尔实际函数对lexical/physical Home、CLI、Prompt、plugin info、file_safety均为alex。active_list确认1 idle/0 running后重启一次后端，真实WS临时新空会话create和异步built info均alex、kimi-coding，随后关闭；无模型消息提交。空会话system_prompt为空属于原生懒构建，不能据此冒称真实首轮Prompt/模型验证。已有会话缓存不会被本轮强行改写，新会话按原生生命周期采用新配置。

**交付证据与边界：** `.hermes-dev/seoul-migration-20261019/`中`profile-binding-fix-report.md`、`nm-online-verification.md/json`、`sync-cutover-report.md/json`及UI报告；原生Provider→MemoryManager只读链路Bundle6549字符/Recall1215字符、无unavailable、0.834秒。独立工具`/home/ubuntu/scrips/nmem-memory.py`已按北京原字节恢复、SHA256 `256af367007db972d6f9ccf2164794d93ad6327d8942c4ead5d5400d9f3ed1a9`一致、help成功，未创建测试Memory。六服务Hermes/NM/Ebbinghaus/Caddy/Authelia/Redis均active，Hermes/NM无自动重启。北京NM及旧重启timer已inactive/disabled，源数据保留。尚未实测新会话首轮模型输入到输出、500秒真实Idle/Noting触发、手机待机、最终蓝绿观感；不把配置开关或模拟DOM测试代签这些真实体验。以下为迁移阶段历史及取代关系。

**17:47阶段记录（后续Profile修复见最终状态）：** NM原生迁移已落地，0.10.101远程embedding健康非degraded；原生reindex completed/success，169memories／468entities／1community／61sources／3009source_chunks，无需重启。ubuntu官方CLI context --source-app hermes-tui返回成功；nmem正式Caddy已从503切localhost14242，独立鉴权/检索验证通过：正式受保护接口无token401／原token200、ubuntu context与search成功；原生Provider→MemoryManager只读集成得到6549字符Bundle／1215字符召回、0.834秒，均无unavailable。Hermes名称根因确认：symlink真实路径丢失profiles/<id>导致Prompt default、CLI/custom，非default写库；default库0会话、Alex51，新desktop的custom身份仍待统一解析修复，不改历史pi-import metadata。已派profile_binding_diagnosis定向实现，root随后review/集成。

**同步整包已root亲审接收：** workspace two-way-safe写入/删除往返通过；8配置先首尔→Mac预对齐后watching、两端SHA一致；300秒真实timer在暂停snapshot lane时独立完成新包，恢复后Mac自动落地，三库逐payload SHA／完整性／外键核验通过，current/previous槽保留。TCC旧阻塞被本次正式往返取代，不再列当前未完成。报告`.hermes-dev/seoul-migration-20261019/sync-cutover-report.md`。北京旧nmem重启timer发现inactive/enabled后已由root禁用，源service/timer均inactive/disabled，源数据不删除。

**UI最终包上线：** 独立UI提交`974a51f392912306fae3fa8cc43ce919a8c17bda`已自动push；49项相关测试、typecheck及build通过，439产物逐文件验证并原子exchange上线，留7旧哈希资源供旧页。只改蓝绿内部权重与手动回timeline底部立即恢复，未重设计／改Markdown。备份`/home/ubuntu/.local/share/hermes-secretary/static/.secretary-before-974a51f-20261019T174642`；本最终微调尚无真实浏览器/手机观感验收。

**先前配置恢复阶段记录（已由最终权威状态取代）：** 先修Hermes生产配置与Profile绑定，再完成NM上线及同步，最后集成UI微调。用户说明阿里云曾欠费且已充值；充值后首尔OpenAI兼容embedding复测HTTP200／1024维／0.914秒，不把该外部故障归为Hermes登录或Profile问题。NM2871文件／341019351字节原生冷包已完成逐文件SHA／大小／权限验证并安装，首尔服务刚启动，健康／重建索引与正式入口尚在验证，不能仅凭CLI存在宣称召回可用。运行中Hermes config.get RPC已读到Alex/study Noting与Scheduler开启、Alex Idle500秒／131072tokens、NM provider；Alex profile home返回`/home/ubuntu/.hermes/profiles/alex`，模型自报default根因仍排查。用户确认default若原生必需就保留，不做前端特殊隐藏。

**同步保护：** 配置lane预对齐时发现首尔Alex SOUL第14行比Mac旧版少末句、17:39:47修改；root未修改该文件，本轮保留首尔现状为权威，不用旧Mac回盖。已授权sync子Agent以现场8文件SHA对齐Mac后启lane；workspace及snapshot证据待整包接收，未提前宣称三同步点全部完成。

**最后一批UI用户口径（已按最终包上线）：** 冷色内部蓝／绿仍随时间变化，但双方均不过度占主导，也不混成均匀蓝绿色；覆盖上一版蓝始终主导权重，`title_animation_and_glow`仅微调ambient。Timeline用户手动滚动后暂停，但主动回到底部应立即恢复流式跟随，不等原暂停计时；已立即写06 §1.5，`markdown_cjk_bold`已结束Markdown任务，转独立timeline hook/测试实现。两包白名单不交叉、均不commit/deploy，由root亲审后统一集成。


**NM迁移执行中：** 同版0.10.101程序已复制并通过动态库检查；DashScope OpenAI兼容`/compatible-mode/v1/embeddings`HTTP200／1024维／0.783秒，原生协议探测200保留但不采用适配器。北京NM正常停止并disabled，四根目录同批冷态清单2871文件／341019351字节，原数据保留。Tunnel流式复制偏慢，追加两机直连的一次性SSH键，仅forced command写目标固定data-direct.tar.gz、restrict禁止forward/PTY；Seoul host key从已验证SSH连接读取钉住，完成即撤销该键。原传输未当完成副本，尚未启动首尔NM或开放正式入口。


**当前实装补证：** UI`50f43af`439文件已逐文件校验并Linux原子exchange上线，前版备份`/home/ubuntu/.local/share/hermes-secretary/static/.secretary-before-50f43af-20261019T171958`；真实Chrome跨两Conversation切换后同一h1 DOM保持、目标标题正确、WebGL ready，加载`index-DARTskAu.js`。未发送测试消息。test HTTPS实测404。

**MCP真实通过：** npm安装`@playwright/mcp@0.0.83`及对应Chromium，Ubuntu仅对精确浏览器路径添加专用AppArmor userns许可（参照系统Chrome配置），不加no-sandbox／不改全局sysctl。MCP browser_navigate Example Domain成功／close成功。Kimi Tools放`/home/ubuntu/tools/kimi-tools`，复用已传Kimi Key；旧agent-gw端点403保留，查官方Kimi CLI配置后通过原有env接缝改`api.kimi.com/coding/v1/{search,fetch}`，MCP搜索／抓取真实均成功。Alex配置已写两MCP lazy，凭据不入config；kimi_finance仍旧网关、未验，不外推通过。


**实测插入项最新：** 用户确认Conversation切换顶部标题也应触发既有重命名动画；子Agent定位TopNav按Conversation key重挂载，改为按screen保留实例，34相关测试／typecheck通过，root亲审仅三文件后提交`50f43af757e8f623a7022db139c66134e0f385f2`并自动推送，构建成功／上线中。光晕仅将原蓝绿mix绿色权重限为0.46，仍随原密度场变化，冷暖总体／形状／速度／聚散不变。Markdown按用户最新减负口径不改：实际渲染定位为CommonMark标点闭合定界行为，需额外解析层，保留报告与书写规避，不引入新依赖。test域名用户最终要求直接404，已替换此前重定向，Caddy配置验证后重启。

**Provider修复补证：** 使用实际service进程环境、Hermes原生resolve_runtime_provider解析kimi-coding，正式K3-256k真实请求HTTP200／3.229秒／2字符正文／stop，凭据接线问题已关闭；首个诊断直接拼错原生base后的路径产生404，改用coding/v1成功，不改Provider本身。真实Chrome新聊天填输入时Send未启用，未发送测试消息，不以浏览器dispatch冒称真实Turn通过。


**用户实测插入项：** 已派`title_animation_and_glow`独立前端子Agent检查标题变更动画消失并微调蓝绿：减少绿、增加蓝，蓝绿占比仍随时间变化但不出现绿占大半；冷暖总体比例／暖色／形状／速度／聚散及现有资产保持，禁止重设计。root继续NM迁移。用户确认废弃test入口、正式使用hermes域名，计划将test改为正式入口重定向。

**凭据接线纠错：** 用户实测Kimi报No usable credentials，查首尔service进程无Kimi／DeepSeek环境而文件存在；已通过systemd LoadCredential＋~/scrips启动wrapper读取既有root受限key，进程内注入KIMI_CODING_API_KEY／KIMI_API_KEY／KIMI_PLUGIN_API_KEY／DEEPSEEK_API_KEY，未打印／复制Key。后端已重启，真实Kimi最小请求正在验证。先前仅UI／数据库读取验证不能代表模型可用，保留该证据缺口与失败。


**最新接入纠偏（用户明确）：** NM直接使用阿里云OpenAI兼容embedding，不实施本地协议适配服务；保持专属API Host和`qwen3.7-text-embedding`，先实测兼容路径再落配置。Playwright使用正常npm安装。Kimi Tools复用首尔现有通用Kimi Key，不额外索取。DashScope Key已由用户上传，原生接口HTTP200／1024维／0.496秒，兼容接口正在验证。


**用户追加部署范围：** 将本机Kimi Tools MCP接入首尔，并配置Playwright；先核本机现有启动方式与凭据位置，个人MCP源码／项目安装目录按`~/tools/`。npm安装例外。独立`~/scrips/`小工具约定不因此替换。


**云embedding已由用户定案：** 模型`qwen3.7-text-embedding`，正式URL `https://llm-fufl3n7xry3qgmv5.cn-beijing.maas.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding`；Bearer DASHSCOPE_API_KEY，DashScope原生JSON `model`＋`input.texts`。待用户确认首尔Key文件路径；不得把示例改成其它模型／URL，先核NM原生Provider协议再配置，若需适配须明确说明。此前厂商／模型待定状态由本条取代。


**当前完成状态（正式域名切流后）：** 用户已将hermes／eb-data／nmem A记录灰云指向首尔，已从首尔解析核实。Ebbinghaus正式上线：源北京service disabled/inactive，首尔enabled/active；最终413事件／146内容／18设置及五表逐行摘要一致，HTTPS health200、无令牌settings401、原令牌settings与sync/pull200，保留原域名／令牌。最终副本／验证在两端root受限`/var/backups/seoul-migration-20261019/ebbinghaus-final/`。独立只读复核Agent遇账户usage limit退出，不能宣称独立验收通过；root实际证据如上。

**Hermes当前正式库已迁入：** 北京服务与旧snapshot timer已disabled/停止，迁移前无runtime／lease／compression lock。以北京当前原生库为源，SQLite backup复制`Alex/state.db`（50会话／6160消息，40表）、`Alex/projects.db`（4表）、`study/state.db`（0会话／0消息，40表）；源／目标SHA、完整性和外键检查通过。首尔原空库先备份，未丢弃既有数据。随后以`session.workspace.move`正式RPC迁50条cwd至`/home/ubuntu/workspace`，未resume历史／提交消息／调用模型。启动后所有表逐行对比仅gateway heartbeat变化；sessions逐列仅cwd与git_metadata_generation变化，其他内容／身份／Notebook／绑定不变。首尔Hermes已active/enabled。正式Chrome「Edgar」在`https://hermes.edgarzhong.fyi/new?profile=alex`实际API200返回50条且全部owner=alex，新JS及canvas ready；未新增聊天。

**入口与剩余：** 首尔Caddy新增hermes双因素forward_auth、eb-data原生Bearer反代8787、nmem维护503，证书已生效；Authelia仅增加hermes two_factor规则，Redis及会话时长保持。Authelia/Caddy本次配置校验后重启，备份在`/var/backups/seoul-migration-20261019/formal-domains/`。Hermes源／目标前置及最终证据在对应`hermes-final/`和首尔`hermes-seoul-before/`。NM仍在北京、数据未复制，首尔不启本地embedding；旧北京快照/Mutagen端点未迁接首尔，冷库回传暂未恢复，不宣称整个迁移完成。源库与配置保留供回退，未删除北京数据或OpenClaw。


- **最新用户授权：** 用户确认`hermes`、`eb-data`、`nmem`三个正式域名均已改首尔A记录／灰云，继续Ebbinghaus最终切流；追加要求将北京Hermes `state.db`（此前Pi原生迁入后继续运行的库）迁到首尔。来源以北京当前正式Profile库为准，保留全部原文、身份、后续新增记录；先停写、备份核验，再启目标，不回退昨天旧导出包、不覆盖丢弃首尔现有数据。


- 用户要求继续部署；明确先完成不依赖云 embedding 选择的部分，厂商／模型／Key 暂缓。
- **用户确认迁移方式：NM 直接复制原生数据库及配套配置，不通过 NM 导入／导出，避免数据和配置脱节。** 实施前核对数据目录、版本、配置与数据库一致性要求；不将运行中的数据库普通文件拷贝冒称一致快照。
- **历史准备时点（已由上方最终上线取代）：** 已以SQLite原生backup取得一致副本并携原认证配置、代码／依赖／Node24.21.0运行包复制到首尔；非NM导入导出。11095个运行文件／链接SHA或目标核对一致，五表逐行摘要一致，413事件／146内容／18设置，integrity=ok、外键违规0。回环health200，无令牌settings401、原令牌settings200、正式`sync/pull?after_seq=0&limit=1`200。首尔unit仅启动做验证，当前disabled/inactive；北京旧服务未停，仍是唯一对外运行源。首尔Caddy候选配置验证通过、现行未改；已异步请求用户将`eb-data`改为首尔同test的A记录／灰云，待回复再做最终停写复制和上线。原错误参数`after=0`返回400保留为测试输入错误，不混写成服务缺陷。
- 首尔Ebbinghaus原生副本／清单／校验日志在root受限`/var/backups/seoul-migration-20261019/ebbinghaus-stage1/`；原包`/opt/ebbinghaus`、认证文件`/etc/ebbinghaus/server.env`仅运行环境保存，未入Git／输出令牌。仅将unit的pnpm包装入口改为同包tsx CLI＋原Node绝对路径，不安装全局pnpm或改业务代码。待切流前副本仍为准备时点，不能当最新权威库。
- NM只读盘点进行中，尚未复制其业务数据或停服务；embedding厂商／模型／Key暂缓。首尔基础服务正常，磁盘可用约47 GiB、内存可用约2.8 GiB。
- **用户确认Ebbinghaus切流口径：** 保留`eb-data.edgarzhong.fyi`和原Bearer令牌，从北京Cloudflare Tunnel改为首尔Caddy直接HTTPS；切换前先验证副本，最终停旧写入并复制一致数据库，避免双主。
- 保留同时进行的聊天背景UI修改与文档，不混入本次部署产物。

### 首尔登录态异常排查与云端修复（2026-10-19，云端修复及短验收完成）

- 用户报告手机锁屏／刷新及校园网电脑反复登录，并提供15:25截图；本次明确授权操作真实Chrome「Edgar」测试站页面，含刷新、关闭、新开。这是本次排查的显示保护窄例外，不扩为其它页面／原生App授权。
- **已核线上现象：** 手机15:24:07 TOTP成功，15:24:28默认目录API仍200，15:24:37及15:25:16同接口已被Authelia以匿名身份302到登录页；前端`loadDefault()`吞下真实请求错误，`create()`随后抛出“Backend default directory is unavailable”。三个Profile的后端默认目录接口现均200，`/home/ubuntu/workspace`真实存在，不是目录缺失或图片／模型调用错误。
- **修复前排除与范围：** 诊断时Authelia实际`expiration=12h`、`inactivity=5d`、`remember_me=1M`，使用memory会话存储；官方v4.39.28、commit `8da42b2348b0351c6284a2940a9c5eec3d4cd3fd`，15:18:07启动后PID1371未重启。15:18主机重启可解释此前登录失效，不能解释15:24登录后几十秒的再次失效。不能把蜂窝网络或IP变化直接当根因。
- **已复现服务端缺陷／主要根因判断：** 该版本`internal/session/memory/provider.go`通过无拷贝`B2S(sessionID)`保存Map键，而会话库从可复用HTTP请求Cookie缓冲区取得ID。隔离源码不变量测试原版失败，仅在诊断副本改为独立字符串拷贝后通过；首尔同一官方二进制、独立虚拟账号／独立库、仅回环19091完整登录测试中，已登录与匿名鉴权请求交错后，第36／39轮分别从200变401，记住我关闭／开启均复现，耗时0.019／0.023秒，无重启且未到期。此前仅交错`/api/state`的30轮未复现，保留该限制，不混写成所有请求都触发。
- **修复前真实浏览器对照：** 用户称15:53登录，实际TOTP日志15:52:55；Chrome「Edgar」一枚父域认证Cookie、一个月有效期，无重复Cookie；随后用户／root刷新、新开、关闭自建测试页后重开均保持登录。该桌面样本未捕获同一Cookie由有效到失效的瞬间，不冒称线上逐次机制追踪已闭环；已复现缺陷由同二进制隔离测试支持。
- **用户授权与实际修复：** 用户明确“我授权你动手在云端做修复”；16:05:25已将首尔`/etc/authelia/configuration.yml`的session切换到专属Redis。原配置其余字节完全相同；当前Authelia PID22789（16:07:07正式重启验证后）、Redis PID21608。Caddy PID896、Hermes PID906保持，双因素认证／会话时长／模型／目录／前端产物未改。前端认证失效误报未在本轮修复。
- **Redis实装：** Ubuntu官方包Redis7.0.15；`redis-authelia.service` active/enabled，默认包服务停用。仅Unix socket `/run/redis-authelia/redis.sock`、`port 0`，目录redis:authelia 750、socket770，普通用户实测Permission denied。`/etc/redis-authelia.conf`启用AOF/everysec，maxmemory64mb/noeviction、systemd128M上限；Authelia新增Wants/After依赖及失败重试。AOF最后写入／重写状态ok；诊断DB1已清空，正式会话使用DB0。正常重启保留会话，非正常断电仍有everysec持久化窗口。
- **修复验证：** 同一官方Authelia二进制／独立虚拟账号／回环19091，原匿名鉴权请求交错场景切Redis后，记住我开关各200轮全部保持200；重启隔离Authelia、重启专属Redis后原Cookie仍200；Redis停止期间401拒绝，恢复后同Cookie重新200。上述故障注入均在正式切换前完成，未反复中断用户新登录态。16:05切换后用户已重新Chrome登录，root在正式Authelia重启前后核同一Cookie指纹及全部属性一致；真实刷新、新开、关闭自建页后重开均登录有效，默认目录200。16:08:46关闭自建页结算WS101/81.726秒，保留旧窗口与新窗口证据区别，不冒称手机锁屏／长期运行实测。
- **备份与交付：** 云端原配置及回滚入口在root受限`/var/backups/authelia/redis-session-20261019T160524/`；配置校验通过，切换失败自动回滚保护已取消，未遗留定时回滚。ignored `seoul-auth-diagnosis-20261019/cloud-cutover-receipt.json`、`redis-binary-probe.py`、`real-cookie-*-auth-restart.json`及修复汇总绑定证据；只存Cookie不可逆指纹和非秘密属性。README／既有部署SOP已补首尔认证运维入口；本轮不提交既有混合工作区修改、不扩部署数据迁移。
- **原诊断证据与清理：** ignored `.hermes-dev/seoul-auth-diagnosis-20261019/diagnosis-summary.json`、`reproducer-results.json`及固定版本源码指纹；Cookie仅输出不可逆指纹，不保存原值；两次有界观察均结束。隔离实例／虚拟账号文件已删除，19091无监听；PID1371仅为修复前定位，修复后PID见上文。诊断／修复验证无聊天提交或模型调用；自建测试页已关闭，原用户测试页保留，16:09:45最终刷新后同Cookie仍不变。

## 最终公网验收与清理（历史目标，2026-10-19）

当前目标：用用户当前受信任的真实浏览器Edgarzhong Profile检查公网前端，Alex新Conversation用DeepSeek严格只读自查，确认后清理旧同步/自有测试资源并停止汇报。**本次用户明确授权真实Chrome Profile，是此前仅隐藏IAB规则的此次窄例外；当前扩展仅有Chrome“Edgar”连接，沿其既有认证进入，无切桌面/原生App/系统open操作，不扩大为任意外部浏览器授权。** 之前本机v5和云部署阶段历史证据仍按当时边界保留。

root实际通过该Chrome公网`hermes.edgarzhong.fyi`进入首页、加载会话列表和连接WS；Dashboard公网也已加载50会话/6087消息统计，未请求OTP。Alex新Conversation `20261019_020701_6a255b`选择deepseek-flash，高思考，已完成只读自查：7次API/12次工具调用，terminal/nmem status/doctor与公开网页替代抓取正常，收到NM Context Bundle；20条历史/12条工具结果保留。Profile配置仍kimi-coding/k3-256k/high/262144，离开自查页后New Chat实际恢复K3/high。仅本次自有Runtime `d62ee84e`已正式close，资源0/lease0；两自有Chrome页已关闭，原用户三页保持。

两项6.1/high只读诊断与最终清理整包已root亲审，无在途子任务。Kimi Search/Fetch实际408/403/404失败；换公开目标、直连/既有代理均408，不能确定鉴权/策略/额度细因，不猜改Key/接口/代理。该轮NM自动召回真实超过默认2秒预算；同环境一次官方CLI搜索0.562秒成功，仅证明当前路径可用，不抹去超时或承诺召回质量。未改Core/Prompt/SOUL/业务配置或重启服务，未写Memory/Thread/提醒/通知。

**最终清理已执行：** 用户最新D15要求公网/DS自查后清理；旧Pi五条同步已备份配置并仅按精确ID终止，新三条保持，未删用户目录/数据或重启daemon。先前“待workspace通过后清理”是Agent计划，已按用户最新结束顺序调整，不增加审批门禁。root最终只读复核：config与snapshot均watching；workspace仍scanning、两端scanned=false，Desktop隐私授权仍待用户操作，禁止代点/绕过。自有workspace marker待放行后双向验证/精确删除，完整同步目标未完成，不宣称全轮PASS。新证据位于ignored `deployment-release-20261019/final-acceptance-20261019/`；独立门禁报告保留原审查时点结论，不由root改签。

## 云部署已运行（2026-10-19，里程碑与边界）

**最新优先级（用户2026-10-19）：先部署并运行云端服务，用户直接访问；同步收尾及门禁报告不挡已授权服务启动。Access已由用户完成配置，Mac匿名实测302至Cloudflare Access登录路径。旧Pi Mutagen允许关闭清除，但明确留到最后清理，不与上线争用。**

**入口已运行：** 云唯一backend PID3015797监听53446、专属Caddy PID3017385监听53448；公网Host经反代两SPA及health返回200，Tunnel业务route已接通。可访问`https://hermes.edgarzhong.fyi/`与`/dashboard/`。Alex初始48会话/6065消息逐项原生workspace.move完成，旧身份/原文/来源不变；study原生空库0/0。其余云服务保持；同步实装已root审阅/激活，config/snapshot已闭环，workspace独立等待TCC。最终真实公网与DS结果见上节，不把入口可用扩大为整轮交付通过。实际入口/初始数据里程碑见ignored cloud-deployment交回与云`~/.local/state/hermes-secretary/deployment/{entry-ready,initial-data-cwd-ready}.json`。

**真实云端短验收已通过：** root隐藏IAB经专属SSH转发进入实际云反代，Alex显示k3-256k/high，切study仍保留48历史链接且无默认模型。唯一新测试Conversation `20261019_013755_07e1d7`实际返回“连接成功”，云正式API1次、17824输入/34输出、0工具，idle完成；测试页已离开至New Chat，指定云Agent仅回收此自有Runtime、保留历史。两MCP initialize/tools/list成功，kimi_search/kimi_fetch/notify可见。原生自动元数据256000兜底按正式目录事实补齐Alex context_length=262144，原生API热合并、PID不变，不改型号或Provider。以上不代签未完成DB回传或整轮独立门禁。

本轮唯一入口：`.autonomous/20261019-cloud-deployment/snapshot-index.md`；计划/两门禁/交付同目录。旧v5门禁只作原版本证据。公网域名已选`hermes.edgarzhong.fyi`；数据库快照周期已由用户确认每5分钟；Mac离线不影响云端、不无限积压/无界日志，最终经校验回传到本机两Profile各state.db冷态副本。

用户已完成两份SOUL编辑并明确“开始部署”；此前禁止云端操作的等待条件解除。两原文已冻结在ignored `deployment-release-20261019/`：Alex SHA `f260652e36b478687605721d8b7850a0a057769cc36aefb0aa1856e0129d56f1`，study SHA `8d88f3c9abea47dcc020245924be2862d87037c96bc29650ade32edd60a0148d`，不得再改写。Pi导入的48会话/6065消息库明确归Alex，study新库；共享云端`~/workspace`、两物理Home和Mutagen布局不变。

最新明确口径：保留`thread_sync_space`功能，但study当前不设覆盖，NM Thread仍同步自己的考研Space；study不设默认模型，也不配置新增Idle节省参数。Alex用原生Kimi Code套餐Provider，复用云端现有Key；默认必须为**独立K3-256k型号**（官方模型目录已核实ID `k3-256k`），不是K3加上下文覆盖；thinking High。Alex开启联合Idle Compact+Noting，空闲500秒、阈值128K（按窗口单位131072 tokens落值）。DeepSeek作为Alex可选模型、非默认，用户明确允许本机DS Key上云。Alex复用云端已有MCP，至少Kimi Search/Fetch和飞书Notifier；只接入/探测，不因此发送通知。

上述部署、UI、Provider及同步委派均已整包接收；无新增实现任务。Root已核源/产物/权限/依赖与SOUL精确字节，最终公网验收使用上节用户D15窄授权的真实Chrome；此前各阶段隐藏IAB证据按原边界保留。SSH整链保持任务隔离sandbox，禁止启动open/浏览器等。

**当前唯一需用户操作的同步阻塞：** macOS `tccd` 确认Mutagen daemon PID647请求 `kTCCServiceSystemPolicyDesktopFolder`，`~/Desktop/Alex` 初始扫描等待Desktop隐私授权。已async请用户亲自允许，未获答复不得视为批准；不得代点UI、绕TCC或自行改路径。云站/配置/数据库回传不受影响。待放行后只接续workspace `sync_Svc6Epz265hHktU7CcFUR0jE3TPl61MsUGjNWLRyvvA`，将自有marker `.hermes-sync-proof-0a0b0a1561054222b76dd9ab8330bc78` 做双向并清自己文件；旧Pi五条已按最新D15最终清理，不再重复操作。当前没有整轮完成声明。

**冷UI新增证据：** 原Pi043冷Timeline可读、Files实际workspace空目录、Back精确原route/owner；study→Alex列表均49（48原历史+唯一测试），study无默认，Alex恢复k3-256k/high，截图/AX在ignored browser/validation-*。只读旧Pi `20261011_223117_07a84a`仍有idle Runtime `4edf8b55`、running=false/lease0/compression lock0，原8消息不变；不能证明仅root持有，未close旧用户会话。与已close的自有K3测试区分，不冒称全局Runtime0。

## 云部署当前任务看板

| 工作 / Owner | 状态与剩余 |
|---|---|
| 云运行 / cloud_deployment_preflight | 整包已root亲审：官方PM rc0/锁/单进程回环绑定、原48/6065迁移、MCP/双SPA/两WS/实际K3均已证；唯一新测试Runtime正式close资源0，服务active/enabled持续运行 |
| 同步 / study_thread_space_split | 整包已接收：config8文件双向与snapshot1ZIP单向watching，云/Mac300秒周期已真实落三库；最新发布/接收包SHA8f97164a…6e1c13一致，断传代表恢复通过。workspace WAITING_TCC；旧Pi五session已最后精确清理，新三条保持 |
| Verification / cloud_release_verification Astra/high | 最终独立复审12条符合，D13实装已关闭，仅D02 workspace TCC与D11公网登录后缺证；未发现需要扩开发的确定源码缺陷，不签全轮PASS，不挡运行 |
| Validation / cloud_release_validation 6.1/high | 独立12目标/12场景、56份原件，接受只读Pi冷Timeline/Files返回/Profile往返和实际三库回传/断传恢复；workspace TCC和公网登录后未验保留，study无会话故侧栏图标未实证；门禁未关闭 |
| 集成 / root | 已亲审SOP/实装/独立报告与D15新增真实公网、DS、清理证据；当前公网缺证已由root实测补齐，独立报告保留原时点。自有页/SSH转发/测试Runtime已清，云持续运行；仅待Desktop授权接续workspace，Kimi业务失败及单次NM超时准确交接，不宣称全轮PASS |

## 历史：部署筹备等待阶段（已由上节放行覆盖）

用户最新确认：云端代码仓库 `~/hermes-secretary`；Profile Home `~/.hermes_profiles/Alex`、`~/.hermes_profiles/study`；两者共用 **`~/workspace`（单数，替换此前workspaces）**，与本机 `~/Desktop/Alex` 通过Mutagen同步。另增Profile Home同步：本机`/Users/edgar/.hermes_profiles`↔云端`~/.hermes_profiles`。用户确认数据库最关键，同意运行时通过SQLite一致性快照经原有Mutagen通道回传；配置和SOUL同步，其它运行态不回传，原运行数据库不作双向文件覆盖。具体备份频率尚未定，不擅自启动服务。前端只上传构建产物，不上传源码仓库；Alex复用当前主助手头像图标、study复习图标。当前已准备本机静态Home、官方插件及SOUL编辑入口，SQLite快照工具/Mutagen草稿/SOP整包已root亲审接收，用户编辑后按定案字节上传，禁止再替用户改写SOUL；尚未部署、上传、启动Mutagen或云端服务。另需沿原流程把Pi新增聊天增量同步进原生Hermes原导入库，不混入本轮合成测试数据库。两SOUL可编辑本机路径为`/Users/edgar/.hermes_profiles/Alex/SOUL.md`及`/Users/edgar/.hermes_profiles/study/SOUL.md`。

## study独立NM Thread同步目标（已改部署选择）

用户要求“Study那个profile，它的同步配置能不能单独拆出来？我希望它的NM同步往Default里面做”。按既有Thread同步语义拆分：新增个人Provider可选`thread_sync_space`，study保持现有`space: space`（考研复习）供Context Bundle/Recall/模型默认访问，自动Thread同步目标曾拟独立为`default`，用户随后明确撤回当前配置：保留可选功能，study仍继承自己的考研Space、不写override。未配置新项沿原space与既有receipt key，保持原生兼容；本次不迁旧Thread/Memory/收据、不修改任何Provider系统提示或SOUL，不扩大手动Memory写入授权。此项为用户后续部署配置调整，不回改固定v5门禁范围。

`study_thread_space_split`（6.1/high）负责个人Provider及相关定向测试/插件文档，禁止流水账及派生；root亲审后仅更新待部署study Home的配置与插件。原测试Profile/运行服务、云端和Mutagen不动；真实Default写入不作为此次定向测试动作。配置初始化生效，不做热切换。

## 历史：固定v5本机验收与部署筹备决定

**用户后续纠正已落实：仅创建Metadata错误需删除后重建，普通字段可经批准通过CLI修改。** 该范围纠正后的实际Provider提示定向1项通过（0.2秒）、Ruff及diff检查通过；两测试Profile磁盘已同步，无重启／NM写入／新模型调用。

第三轮固定v5本机Verification和Validation均已PASS（PI01–26范围）；以下保存当时的收尾文档和新用户部署筹备记录，**该时点尚未执行云端部署／Mutagen；不是当前运行状态**。最高依据为最新产品文档及明确用户口径，技术规格也可错；不把未来愿景扩成当前开发。唯一轮次入口：[Snapshot Index](.autonomous/20261018-product-intent-review/snapshot-index.md)，计划/两门禁/最终判定在同目录。本机第三轮PI01–26实现与验收目标已完成；当时新部署仍为筹备阶段，云端运行和同步未验，不以构建、push或本机通过宣布上云完成。

- root抓目标、场景、体验、编排、review和最终判定；实现/调查/实测6.1/high，只有独立Verification用Astra/high。子Agent不派生，整包一次交回，禁止流水账；无必要全局工作允许等待。通用规则只在AGENTS。
- **静默方案最新决定（PI-21）：用户明确答“先保持现状，列为待决项”。** 不实施NO_REPLY新增句、过滤或“静默完成”展示协议；不改变deferred、未读/系统通知政策。无变化Reminder仍可能有业务汇报，作为明确待决/现状限制交付，保留原失败，不冒称静默已通过。具体提案仅在ignored `quiet-reminder-proposal.md`，不是授权。
- **Memory最新决定（PI-22）：废弃Skill方案，直接精简改个人NM Provider系统提示。** 仅Memory创建走窄入口，一次携完整内容与Metadata；其余操作官方CLI。普通Memory字段仍可经批准用CLI修改；仅创建时Metadata错误须批准删除后重新创建；既有失败对象不补写、不重建，partial/unknown不盲重试。前序窄包已完成；现按PI-24～26实施独立工具和NM Thread分叉同步，必要B实测已完成：真实模型唯一一次apply，独立同ID GET确认准确来源Metadata持久存在，自有资源0。旧A原失败保持。
- **PI-23：用户确认三类模型偏差不阻塞交付。** 错误归因、截断Search夸大完整核对/拼接原因、Noting补叙述未补来源身份均保留观察，不再要求为它们新增开发或补测。该确认不把原观察改成通过，不与Metadata实际落库/归档暂停提示独立缺证混同；Reminder静默仍按PI-21待决。
- **PI-24当前授权：** 统一“NM Thread同步”；History不一致自动分叉接续，只保存接续说明＋差异后缀，接续地址必须使用NM原生Thread/Message ID。模型实际创建带Metadata的Memory必须补证。新路径Provider英文句已由用户批准并仅替换此前长句，两测试Profile已按v4正式安装并安全加载；只做这两项及必要接线/验证，不扩开发范围。
- **PI-25独立小工具：** 用户拍板本机／云端统一 `~/scrips/`，不依赖Hermes／HERMES_HOME／插件安装路径。`metadata_live_acceptance`恢复实施独立NM创建工具（通用Metadata由调用方提供），不动Prompt；Thread契约／分叉两个Agent继续各自原任务，禁止重叠修改。PI-26已批准新路径精确英文，root已仅替换此前长句；两窄包已root亲审接收、统一加载，B单条真实创建和A实际编辑分叉已执行；不扩为旧对象修写。
- **NM Thread接续的必要实现细化（root决定，不冒称新用户口径）：** 多次分叉时，首条分别记录前一Thread，以及最后共同NM Message ID和其真实所属Thread，避免将祖先消息归属到错误Thread；尚无分叉后真实消息时等待，不创建只有接续说明的空Thread。保留既有远端Thread命名，Profile隔离证据仅按实际ledger/Space范围表述。
- **UIUX保护：** 用户现有布局、样式、动画、图标、Pin/拖拽及滚动为基线，只补状态/恢复接线，不接管Pin表现或整文件覆盖/挟带提交。
- **显示保护：** 只许自己创建的隐藏Codex IAB（iab、visible:false）。禁止桌面、外部浏览器、open/open_in_codex及任何显示/焦点变化。不碰用户恢复页/旧Tab；没有合规路由如实记阻塞。

## 历史：固定v5本机版本与运行现场

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

## 历史：固定v5实测环境与访问授权

两Profile位于 `.hermes-dev/validation-personal-20261018/runtime/profiles/{main-assistant,exam-assistant}`；terminal.cwd在Git root外 `/Users/edgar/code/Hermes Test/validation-{main,exam}-assistant-workspace`，防止根AGENTS污染模型上下文。两者Noting/Scheduler及联合Idle100000 tokens/5秒开启，模型容量262144保持，DeepSeek原生custom/chat_completions；不接Codex App Server/Proxy。

- main：Default和“考研复习”Space只读，自动Thread archive=false；不读exam Hermes Profile。
- exam：用户现有“考研复习”Space（安装selector `space`），可按具体授权写，自动Thread archive=true。Memory提案/修改不算批准，禁止事实写入USER或其它长期存储。
- 两SOUL是可部署身份，已移除测试背景；测试权限在各仓外workspace AGENTS，确保冷恢复/压缩后仍可见。每条普通user message必须附原完整测试前缀、真实带时区时间和600秒一天；不改系统时钟，不将oracle/UID/预期答案灌给模型。
- v3历史安装Provider `96f17766…`、helper `75d8dca1…`、76行Skill `89cb013e…`曾同步两测试Profile；真实A模型未读Skill、直接CLI创建，官方GET确认无hermes_provenance。PI-22包已root亲审接收：PI-22时点Provider `f14d2cfe…`及无Skill注册入口曾同步两测试Profile，原Skill文件/auto_load/本插件external_dirs已撤销，其它配置/SOUL保持；4项定向检查通过，helper未改。以上为历史PI-22状态；现v4已正式安装重启，真实B模型独立入口创建及同ID Metadata持久回读通过，未改写旧A失败。
- Default不写，不触碰旧partial Memory `1805d328-eec9-4082-b0d2-e1051c1d6eac`，不清他人排期/历史/资源。所有凭据/原始私人材料仅本地ignored。

## 历史：固定v5任务看板（已由云部署看板接替）

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

## 历史：固定v5已接收证据与实际边界

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

## 历史：固定v5结束条件与部署筹备步骤

1. 固定v5两独立门禁均已PASS，E04原A冷显示与安全加载关闭，FV02纯交流一次真实输入/一模型请求/零工具及新增内容或提醒、精确close资源0。不重复100k、600秒、Memory创建或大型套。
2. 新部署筹备整包已root亲审接收，SQLite快照工具/接收两槽及9不同真实SQLite节点证据接受；28静态文件指纹/权限和实际测试源码绑定已核。数据库原文件不双向同步，不回传其它运行态。只准备不启动；UI alex/study图标/显示名仅最小提案，正式构建前处理。
3. 最终版本/产物与文档已收束，独立Validation的SOP/DP文档delta窄核已通过，不重复产品动作；收尾提交后仅校正本机测试服务版本绑定、保护原round3。按delivery-evidence-review已更新[final-delivery](.autonomous/20261018-product-intent-review/final-delivery.md)。保留PI21待决、PI23非阻断观察及云端/平台未验。
4. 用户先编辑两份SOUL并定案。收到正式部署放行后，才按最终字节核SHA上传、原生迁入历史会话cwd、配置生产参数和备份频率、启动云端服务/同步；此前不触云端或激活Mutagen。

## 历史入口与防重复

第三轮初始冻结、二审NOT PASS及旧分包留在 `.autonomous/20261016-round3-secretary-nm/`，不重开已交回任务。当前全范围报告在 `.autonomous/20261018-product-intent-review/`；更早功能/专项证据经README索引。此次整理前主看板完整原文留ignored `CLAUDE-before-closeout-sync.md`，v3固定副本也保留其捕获时点文档；仅本页维护当前动态状态。

旧已接收功能不重新立项：Notebook局部UID/分支来源、Noting真实Running计时、完成高亮、冷Context/Session Total估算、历史恢复指引、Files固定default、跨Profile列表/Pin顺序、普通5秒提示、5098开发开关、双SPA/4001/标题。各自验证范围和未验平台以原报告为准；稳定入口在README，规则在AGENTS，不能拿旧测试代签较新变化。
