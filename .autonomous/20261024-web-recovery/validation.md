# Validation：20261024-web-recovery

## 1. 结果概览

**最终判定：Web Validation通过（2026-10-24）。** 最终Web `2346a030a5ac4b25d4a4470daaa367f666098fd8`／后端产品 `52c5088fd6afb1b7da730ec8b0f65ad3068ec7e9`。原VAL-01/03/04/05/06均已有原用户路径或明确未变路径的有效结果，EVID-01呈现证据已补齐；无已知未闭的范围内Web用户结果阻断。旧版失败、首run预算失败、离屏无效动作及构建污染样本原样保留为历史，不倒写为成功。最终接续由父会话自建隐藏IAB执行，本验收者独立读取原始AX、截图、连续DOM、请求及DB证据裁判，**不声称亲自操作父UI**；同版未受影响U1及限定开发证据的复用边界见下。最终APK0.1.5/1005包装清单已核；实际APK生命周期按C17用户豁免、未验。

验收者validation_v1（gpt-6.1-sol/high，独立按冻结用户目标判定、不派生），2026-10-24。已完整读autonomous-run、real-user-acceptance及模板、两仓AGENTS、主仓当前CLAUDE（Web无CLAUDE，统一入口为主仓）。依据为本轮snapshot-index.md、baseline.txt及冻结主仓ba83d2b430e3448461dd7feb9f1acd8fc94c6cc9的06 §0.4、§1.2适用性、§1.3、§1.4/R1–R10、§1.13，08 §1/3的owner保持条款，用户C01–C18。plan仅作场景线索。

U1初始待验Web0eef2802725c7999636ca918e75d5513be608fcd（0.1.5）、后端产品dd9a4c57dd7c182ad8497f9538e115bbab3131b0。公开入口http://127.0.0.1:5178。进入条件为独立Verification v5全轮18组通过。同版机制证据可复用，仍须真实Web用户入口观察。

用户目标：缓存保住当前画面，无整页刷新自动恢复当前实际需求与活动Turn；分页、owner、读失败、历史改写及认证失效正确，保留阅读/胶囊呈现。主会话已完整过目并明确批准S1–S8执行；下述旧候选信息与原始失败为U1历史，当前结论以本节首段及第6节为准。 APK实际生命周期按C17用户豁免，明确未验，不以Robolectric当实际平台。C18最终包必须0.1.5。

## 2. 环境与准备

最终接续仅用父会话自建隐藏tab5，后续最小修后用其自建隐藏tab6（localhost同origin/storage/HTTP缓存）；父仅按独立场景操作采证，本验收者不以实现自评代替原始结果。未新建Files持久缓存；Files所称“保旧”是既有内存预览过渡，“warm”是既有浏览器HTTP缓存。当前faults{}，shapes.png原文件SHA2dfbc8e4c16bf07516a880a8830e2fddd4aa5edc65a827adcb24cbf8e47a60ca已与备份逐字节核同。

以下为U1原准备记录；接续另获授权证据目录validation-final/，代理已扩展为精确GET路径401/503，最终包信息以apk-delivery-manifest及第4节收口为准，原包SHA不代表当前包。

- UI只创建自己的Codex隐藏IAB（iab/visible:false），about:blank后导航本地；不动用户tab、Chrome、桌面、可见页或模拟器，结束关闭自有tab。CUA遵文档；DOM只读真实页面/几何，不访问Controller或内部业务state，不伪造协议/成功。
- Vite5178→fault proxy53576→真实隔离Dashboard53575，供应商替身loopback SSE53577。四服务由主会话持有，不自行停；新epoch协调主会话只重启53575。53445/53446不动。不得访问生产域、真实供应商API或部署。
- 合成SessionDB：default/recovery-validation 1200行（row0–1199，奇数Thinking为Expanded detail i）；recovery-other同storedID仅隔离问答；default/recovery-image含原生@image。Files固定default，两Profile工作区在仓库外。深分页先做；破坏性writer前通过SQLite backup备份授权合成库。不能seed重置custom模型路由。
- 已读fault_proxy.py/seed_validation.py/stream_control.py。当前faults.json仅支持block_ws及GET delay；图片失败可临时移开授权公开PNG再恢复。HTTP503/401需先协调代理能力扩展，不改产品。proxy-requests.jsonl只补充真实重读/无reload证据，不代替呈现。
- 唯一发送授权：正式New Chat/default输入 `RECOVERY_LOCAL_FIXTURE: Produce only the controlled local stream.`，先arm全新run、pause_after2/interval1；单run60秒，及时断WS/恢复仍running后resume。真实native Turn/租约/DB，只有供应商SSE是受控合成依赖；最终以UI及真实历史/唯一assistant落库和idle共同确认。
- 白名单：仅本报告和主仓ignored `.hermes-dev/web-recovery-20261024/validation-v1/`证据，以及授权faults/合成fixture。产品只读，无stage/commit/push。每次故障/文件恢复留receipt。
- APK路径为ignored Hermes-Secretary-0.1.5-arm64.apk，指定SHA256 e4c5d68b371364ac2a3a03756f0c5094fedb21dbeabdd8aa3d902ecb15dac7b7；version1005/439资源/同证书由同版证明核对，不安装。
- 差异/复用：桌面隐藏IAB、合成数据，未验生产门户/蜂窝/实际WebView。原子cut、ring/租约/并发/取消、容量/TTL/迟到结果和原生边界复用V5及同版机制证据，不重跑大套。精确动画内部时长/降动效机制可复用，但实际视觉必须观察。

## 3. 用户目标与场景覆盖

当前覆盖结论如下；紧随其后的原U1表为历史基线，未改变原失败记录。

| 目标编号及冻结依据 | 完整场景编号 | 场景类型与起点 | 数据/顺序选择依据 | 当前执行结果 |
|---|---|---|---|---|
| G1 C01–05/10、R1/5/6 | S1 | 同源成功缓存→WS拒绝冷开→真实重读 | 保原storage/HTTP缓存；118摘要含两owner较早行 | 通过；连接前1199/胶囊/118可读，解除后保持并真实GET，后续分页/Turn可用 |
| G2 C04–06/09、R2–4/7 | S2 | 三页深历史→cold展开有效Thinking→断线→恢复→人工输入 | 正式可见按钮分页，稳定详情前置；连续几何取样 | 通过；首400/800articles、详情全程不空、实际中间运动、输入后不抢回；精确inflight时序复用P43 |
| G3 C02/05/11、R1/5/6、08 §1/3 | S3/S4 | 跨owner同ID→固定default Files→返回原聊天/草稿 | U1有效隔离/文本/PDF/下载复用，下载传输补复验 | 通过；ENV-02夹具修正后U1真实UI通过；二进制同URL实际新内容/GET已补 |
| G4 C03–05、R5/6 | S4 | warm同URL503→保旧→解除自动采用新内容 | 不清HTTP缓存、不改URL；真实资源替换后还原 | 通过；独立核Files原图/503/自动新图/11次GET，历史图片共享传输复用限定开发原始证据 |
| G5 C03/04/07/11、R3/5/7 | S5 | NewChat→发送→running重连→后续流→重开全文 | run3真实native Turn，仅供应商为loopback合成SSE | 通过；六段精确正文、DB唯一1+1、同document重开可读、无runtime_unavailable |
| G6 C03/06/09/10、R3–6 | S6 | writer改写/压缩/rewind/delete与新epoch | U1未受最小接线修影响的真实结果按范围复用 | 通过；不为复验重复破坏数据或在线回灌DB |
| G7 C10/11、R6 | S7 | 503保画面/自动重试；明确401清理 | U1实际历史/文本401，未改binary认证路径补充原始开发证据 | 通过；最终Files401过早截图明确不计成功，不以该图替代有效证据 |
| G8 C05/07、R5/7 | S1/S3/S5 | 菜单/侧栏分页/Usage与Context实际变化 | U1菜单与run3连续胶囊采样组合 | 通过；0→112/13%→0%，data-updated短亮后移除，不持续重播或动画缩放 |
| G9 C08/17/18、R8/10 | S8 | 最终APKmanifest与未变原生机制复用 | 最终Web2346a030/后端52c5088包装，actualAPK用户豁免 | 包装/机制证据符合；实际APK生命周期未执行，不据Web或Robolectric推断实际平台通过 |

**以下原U1覆盖表，仅代表Web0eef280／后端dd9a4c5当时结果：**

| 目标编号及冻结依据 | 完整场景编号 | 场景类型与起点 | 数据/顺序选择依据 | 当前执行结果 |
|---|---|---|---|---|
| G1 缓存仅过渡、每轮真实重读：C01–05/10、R1/5/6、§1.3 | S1 | 首次冷开→成功→同owner刷新/延迟→同epoch断线追加→恢复 | 1200行latest窗口；无缓存与已有缓存分开观察 | 失败（VAL-01） |
| G2 有界分页/展开/阅读：C04–06/09、R2–4/7 | S2 | 深anchor→展开Thinking→断线追加→恢复，等待中收起/滚动 | anchor不在latest200；深历史先做以保护样本 | 数据/锚点通过；运动过程直接证据不足，见EVID-01 |
| G3 owner/Files：C02/05/11、R1/5/6、08 §1/3 | S3 | 跨Profile同ID→Files目录/文本/PNG/PDF→返回聊天→New Chat Profile菜单 | 同ID隔离；other聊天与固定default Files不同 | owner/文本/预览/返回通过；二进制重读受VAL-04影响 |
| G4 图片当前依赖与重试：C03–05、R5/6 | S4 | 可见历史图片→断线/文件暂不可用→恢复失败→文件恢复自动成功 | 同URL本轮必须重取解码，不能借旧ObjectURL | 失败（VAL-04） |
| G5 活动Turn完整接续：C03/04/07/11、R3/5/7、§1.13 | S5 | New Chat真实发送→流中断WS→仍running时重连→继续→结束→重新打开 | 实际native Turn+受控SSE，输入到唯一持久回复 | 阻断（VAL-03），未发送 |
| G6 历史改写/epoch/404：C03/06/09/10、R3–6 | S6 | 正式edit/replace/rewind/compact→恢复；新epoch；最后delete | 每种真实writer留证，破坏前缀允许刷新感 | 通过；真实writer/epoch/404见S6 |
| G7 认证清理/普通失败：C10/11、R6 | S7 | 有历史/Files预览→503对照→真实401→清敏感展示 | 本地HTTP故障须协调，不能用JS假登出 | 通过；历史503与两类401真实UI |
| G8 菜单/侧栏/胶囊：C05/07、R5/7、§1.13 | S1/S3/S5 | 实际展开Usage/Context及Model/Thinking；同值与结束变化 | 结合业务旅程观察高亮、尺寸、展开和原地更新 | 部分已验；有效变化高亮受S5阻断，未完成 |
| G9 APK机制/包装：C08/17/18、R8/10 | S8 | 单测与最终签名资源证据复核 | 用户C17豁免实际平台，C18最终0.1.5 | 机制/包装证据符合；实际APK用户豁免、未验 |

以下保留执行前计划；实际结果以各场景执行记录及第5/6节为准。七条Web旅程组合正常、恢复、owner切换、可见需求变化、失败及后续可用性；每一关键目标独立记录观察，不能一条成功替代所有目标。不穷举低层时序，复用同版有效机制证据。执行中变化保留原项并注明理由，不缩减关键结果。

## 4. 详细场景与执行结果

### 最终候选复验计划（主会话已过目批准）

当前候选Web `b8f06ff70a0e2e02e52fa19c1136c2068d54e749`，后端产品仍dd9a4c5；仅接续原S1–S8目标，不重建判据或全量代码审查/单测。原U1失败和有效证据保留，不倒改旧版本结果。入口只localhost:5178同源隐藏IAB，保原HTTP缓存/URL，证据写ignored validation-final/。

主会话已批准立即执行。首次创建自有hidden IAB返回Browser is not available: iab，只读浏览器清单仅Chrome，无IAB。未退到Chrome或操作用户页，已交主会话恢复环境；证据validation-final/iab-unavailable.json。本次真实UI尚未开始，不以包装证据代替。 父会话已创建自有隐藏IAB tab5（browser2），本子会话getTab绑定仍返回Browser is not available:2。为避免工具隔离停工，采用父会话仅执行所指定的UI操作/采集原始AX、截图和只读DOM，本验收者独立读原始证据并判定；不引用开发自评作结果。显示保护仍只该新建隐藏页，不动用户页面。

执行顺序：①S1/N06：从真实侧栏Load older，记录default100+10/other8及较早行，成功后blockWS正式reload，确认连接前缓存/胶囊可读；解除后完整重读且已加载较早行不消失。②S2/EVID01：1200行会话真实分页到深anchor、展开Thinking，断线期间正式append，8秒REST延迟后连续DOM/几何帧观察统一交接/有限滚尾；第二次用真实wheel/键盘取消且不重播。③S5：New Chat/default唯一获准prompt，先arm唯一60秒run，快速Send→两chunk暂停→断WS/解除→仍running恢复→resume后续/结束；以真实UI再开历史与只读SessionDB核唯一assistant/精确正文/idle，采样Usage/Context有效高亮及稳定尺寸。④S4/Files：warm同URL下载503+重连，核实际代理GET、旧图保留、解除自动重试；合法备份后同路径换授权PNG观察实际内容变化再恢复；Files二进制同URL重读和明确401清预览。⑤S8仅复核最新APK0.1.5/1005/439/SHA，原生40项及U1未受影响S3/S6/S7按范围复用，actualAPK仍C17豁免未验；解除故障、原文件恢复、关闭自建tab，更新六节结论。

### 最终候选实际复验记录（Web b8f06ff，父隐藏IAB工具执行／本验收者独立原始证据判定）

- S1缓存/N06多页保留已观察通过，权威交接的后续可用性待S2/S5实操确认：s1-sidebar-loaded-dom.json逐href统计118（default110/other8），真实Load older后button消失，default recovery-sidebar-000在列表。真实default历史成功后，blockWS正式reload；s1-wsblocked-cache.png直接可读row1199、Usage0和Context36%，DOM同118及较早行，不是空历史。解除故障后s1-recovered-dom.json仍118/两owner计数/较早行、row1199、composerDisabled=false；截图无清空。s1-proxy-requests.jsonl有6次/api/sessions GET及当前messages/metadata重读。由原始截图和DOM相互印证，VAL-01连接前展示缺陷关闭；N06行保留符合，但S2首次两次Load earlier未推进，正在正常冷开对照，不将textarea可用独自当ready。未读写IDB或清HTTP缓存。其余复验进行中。
- S2补充对照：s2-normal-pagination-settled-dom.json在正常cold后仍只1000–1199，真实Load earlier未达到800；完整现场/请求细节待工具执行者交回，暂不关闭运动证据缺口或判分页通过。
- S5首run原始证据已独立核：正式Send可用并已发送；s5-reconnected-running.png/DOM在同URL20261024_214553_5855d0呈现唯一输入、精确前两段“本地合成恢复验证。 第一段已经到达。”、Stop可用、侧栏Running，证明仍running时恢复。执行者报告该run在resume前耗尽60秒、sent_chunks2/deadline_reached；不判完整流/最终正文通过，待第二run快速确定序列补后续及终态。
- S5第二run已独立核完整主链：s5-run2-reconnected-running.png为同URL20261024_214847_26aadb、前两段和Stop/Running；complete截图与final-dom六段正文精确匹配预期且Stop消失，DB proof正式读user1/assistant1/同精确正文、input64/output48/messages2。因此VAL-03正式入口缺陷关闭，实际running恢复与后续输出无重复/丢失通过；离开再开持久呈现待最后复核。s5-run2-live-samples为1101个实际DOM样本/3499ms；可见Usage始终0、Context13%，class始终hs-usage-summary/hs-context、尺寸32×162.59/32×116不变，无有效可见值变化。本样本只支持同值不闪/布局稳定，不冒称正向高亮已验；也不单凭raw DB112认规范Usage错误，待真实展开canonical读数。




动作始终走正式UI，不直接RPC/Controller/IDB，不改DOM或清HTTP缓存，不访问生产/真实供应商。缺陷提供最小序列，能继续部分继续；报告如实保留未执行/失败。需要额外环境协调才发消息。


以下统一版本Web0eef280/后端dd9a4c5；准备授权见第2节。以下保留先定预期，实际结果、时间序列和证据见本版执行记录。

### S1 冷开缓存、同epoch恢复与胶囊/侧栏

- 意图/对应：C01–07/10、R1/5–7。合法起点为全新隐藏IAB无该源缓存，从公开侧栏打开default/recovery-validation，之后已有同owner成功缓存。
- 完整步骤：①首次观察loading、真实末尾1199、侧栏/两胶囊；②展开Usage/Context，记录显示值/尺寸；③成功后同owner刷新，使GET延迟8秒，观察缓存过渡及真值接管；④断WS，正式append外部新行，解除故障，观察无整页刷新收敛；⑤同值再重连，保持Model/Thinking真实菜单展开，确认重新读取和后续可用性。
- 预期：每轮真实重读当前需求，首次不假空，缓存不能恢复旧运行事实；不清空/闪跳，最后真实末尾；侧栏原地更新，同值不高亮，变化轻亮，胶囊尺寸/展开稳定。用只读document/navigation记录及proxy日志补充无reload证明。
- 实际输出/状态/后续：已执行，详见本版实际执行记录。原证据计划s1-*.json/png、请求切片；实际文件mtime及执行记录提供时间。
- 结论/偏差：本版失败VAL-01；详见执行记录。

### S2 深历史与展开详情的完整阅读

- 意图/对应：C04–06/09、R2–4/7。起点1200行样本，通过真实Load earlier到row400附近非latest窗口，选assistant展开Thinking。
- 完整步骤：①连续分页并记录anchor/offset；②记录Expanded detail；③断WS，正式append后解除，在GET延迟中观察旧画面/详情，交接保anchor后有界滚向真实尾；④再从旧anchor恢复，等待中收起/滚动，核新需求与用户取消后不重播旧动画；连续短采样DOM几何及恢复前中后截图。
- 预期：有界anchor定位，深anchor与tail间明确分页间隔，不伪造邻接/下载所有正文；当前可见Thinking纳本轮读取；相容前缀不先清空/瞬跳，滚真实末尾；用户输入取消后不抢位。精确240ms/降动效机制复用同版证据，真实呈现仍观察。
- 实际输出/状态/后续：已执行，详见本版实际执行记录。原证据计划s2-*、几何/请求范围；实际时间见证据mtime。
- 结论/偏差：已完成可做步骤；本版实际结论与偏差见下方逐场景记录。

### S3 跨Profile、固定Files与返回

- 意图/对应：C02/03/05/11、R1/5/6、08 §1/3。输入为同storedID两个Profile及授权Files文件。
- 完整步骤：①侧栏切other，确认仅Other Profile isolated question/answer；②进入Files，真实目录/文本/PNG/PDF预览；③文本预览断WS，备份后外部更新recovery.txt，恢复观察新文本；④至少一种二进制预览重连确认实际重取/渲染，其余格式冒烟；⑤子目录Back to Chat直接返回other及原草稿/阅读；⑥New Chat Profile菜单选择但不创建，回default确认无串缓存；延迟读取时切owner验证旧响应不回盖。通过正式用户下载入口检查文件可下载。
- 预期：Files root/list/preview/download统一default；聊天仍other、返回完整身份，New Chat所属cwd不被Files污染；目录/预览每轮重读，旧ObjectURL不算成功；页面后续可操作。
- 实际输出/状态/后续：已执行，详见本版实际执行记录。原证据计划s3-*、备份/恢复receipt、请求；实际时间见证据mtime。
- 结论/偏差：已完成可做步骤；本版实际结论与偏差见下方逐场景记录。

### S4 历史图片失败保画面与自动恢复

- 意图/对应：C03–05、R5/6。公开侧栏打开default/recovery-image，先确认PNG真实解码；备份授权PNG。
- 完整步骤：①记录naturalWidth及可见截图；②断WS/暂移公开PNG；③解除WS，观察真实读取失败、旧图保留及自动重试；④恢复文件，不刷新观察成功重取/解码与下载；⑤切页再回来核owner资格。
- 预期：失败不以旧URL冒称本轮成功；资源恢复按1/2/5秒退避自行收敛，同URL新请求，实际图可见/下载可用。
- 实际输出/状态/后续：已执行，详见本版实际执行记录。原证据计划s4-*、文件恢复receipt；实际时间见证据mtime。
- 结论/偏差：已完成可做步骤；本版实际结论与偏差见下方逐场景记录。

### S5 真实活动Turn从输入到持久回复

- 意图/对应：C03/04/07/11、R3/5/7。New Chat/default，唯一prompt为第2节原文，arm新run后才Send。
- 完整步骤：①真实输入/Send，见一条已持久user、流式前缀/运行控件；②两chunk暂停后block_ws并及时解除；③60秒内见仍running的前缀完整恢复、无重复user/assistant，再resume；④见后续chunk及正常结束，记录胶囊有效变化/轻亮及布局；⑤离开再打开，核最终正文；只读正式历史/DB确认唯一assistant及idle。首次中途附着可用自建第二隐藏tab通过公开导航完成。
- 预期：真实native Turn/租约/DB；不等finish就恢复，后续流无丢失/重复，不重放发送；最终回复可重新使用。若60秒不足，留环境失败后协调，不改产品判据。
- 实际输出/状态/后续：已执行，详见本版实际执行记录。原证据计划s5-*、run receipt、最终历史/DB摘要；实际时间见证据mtime。
- 结论/偏差：已完成可做步骤；本版实际结论与偏差见下方逐场景记录。

### S6 正式历史改写、新epoch和删除

- 意图/对应：C03/06/09/10、R3–6。S2取证完成，SQLite backup授权合成库，不重置路由；UI可用编辑/rewind入口优先，否则使用已读正式SessionDB writer模拟外部客户端。
- 完整步骤：①断WS，对样本edit可见首行及同条数replace，分别恢复确认真正文；②正式rewind，确认截断尾不复活，Context不延续已知不兼容值；③正式compact，核真实summary/合法连续历史；④协调主会话只重启53575，新epoch自动恢复；⑤最后delete，确认安全退回New Chat/丢失提示、缓存不复活。需要恢复样本时仅从授权备份恢复并记录。
- 预期：前缀破坏允许重定位，但旧UID/正文不得复活；每种writer各留实际结果，不用replace代替rewind/compact；新epoch不沿旧运行态，明确404才退路由。
- 实际输出/状态/后续：已执行，详见本版实际执行记录。原证据计划s6-*、backup manifest/writer receipt；实际时间见证据mtime。新epoch已协调并实际观察，见S6。
- 结论/偏差：已完成可做步骤；本版实际结论与偏差见下方逐场景记录。

### S7 普通失败与明确认证失败

- 意图/对应：C10/11、R6。已显示历史和Files预览，仅本地代理故障，不触及真实认证/凭据。
- 完整步骤：①协调代理HTTP故障支持后，当前必需GET503，观察保画面/自动重试并解除成功；②有敏感历史/图片时真实HTTP401（公开reader链），观察当前document清历史/预览与安全禁用；③恢复故障，经既有正式入口重新确认身份并恢复正常；隐藏reader/旧凭据竞态复用V5，不重跑矩阵。
- 预期：普通503/图片404与401区分；401不得留下敏感旧内容或让缓存绕过认证。缺代理支持须协调，不能假登出或冒称已验。
- 实际输出/状态/后续：已执行，详见本版实际执行记录。原证据计划s7-*；实际时间见证据mtime。代理目前仅delay/block_ws，已由主会话扩展仅GET精确401/503，见S7执行记录。
- 结论/偏差：已完成可做步骤；本版实际结论与偏差见下方逐场景记录。

### S8 原生与最终APK证据边界

- 意图/对应：C08/17/18、R8/10。只读V5、原生40项/JS桥/最终APKmanifest，核0.1.5/1005、439资源、签名和指定SHA。
- 预期：只能说明同版机制/包装，不能说明实际前后台、相机、通知目标或5秒画面连续；不安装/启动模拟器。
- 实际输出/状态/证据/时间：已复核；见S8执行记录及final-environment-receipt.json。
- 结论/偏差：实际APK生命周期用户豁免、明确未验；机制/包装已核符合，无偏差。

执行顺序：S1首次→S2深历史→S1缓存/重连/菜单→S3→S4→S5独立快节奏预算→S6→S7→S8。主会话过目后才建隐藏tab。新epoch与HTTP故障支持到需要时集中协调。改变顺序可减少准备成本，但保留每个关键结果。

### 本版实际执行记录（2026-10-24，保留上方执行前预期）

- **S1：失败（VAL-01）。** 首次localhost源先Loading conversations，遇stale-module环境保护（运行aed15db/磁盘9ada8bd）；主会话只重启53575后原页自动恢复，不归产品缺陷。真实侧栏打开default1200行，首屏截图可读row1199、DOM top28950/full29441/height491；Usage展开为Session Total/Input/Cache/Output0，真实Model/Reasoning菜单可用，未切路由配置。其后成功缓存冷开在WS被拒时显示No messages yet；同源recovery-image重复对照，WS解除但history延迟8秒时缓存两条正文/侧栏/Usage0/Context12%立即出现，证明已持久缓存而读取被连接门槛挡住。证据s1-latest.png、s1-geometry.json、s1-cached-*、s1-image-cache-*、s1-model-menu.txt/s1-reasoning-menu.txt。无IDB/内部state操作。胶囊真实有效变化高亮因S5被阻断未得最终用户证据，不能判全目标通过。
- **S2：数据/锚点结果通过，真实运动过程直接证据不足。** 真实Load earlier三次从1000→800→600→400；展开Expanded detail401，anchor正文400屏内204.8px、Thinking278.5px、正文401437.3px。断WS并正式append，8秒延迟期间连续5个样本保持上述位置/正文。随后真实tail包含1197/1198/1199/External append while disconnected，top58353/full58844/height491，两个Load earlier控件明确表示不连续窗口，旧未验证中页没有伪装相邻。s2-before/disconnected/recovery-samples/recovered-*。没有逐帧捕满240ms，不将前后截图冒称动画精确时长；用户输入取消/降动效未再单独制造，因同版P阅读43项已覆盖且本轮采用用户轻量复用，实际核心锚点保留→真实尾部已独立观察。该偏差不缩减已证的数据/最终可读结果，但不能将机制时长断言替代本版运动过程直接证据，记EVID-01，下轮补采样。
- **S3：owner/文本/预览/返回通过；二进制重读按VAL-04失败。** 固定Files root/list/文本/PNG/PDF均实际可用，other返回路由不改变Files default工作区。文本从Recovery text baseline断WS后正式文件更新为Recovery text updated during disconnect / S3 actual Files refresh，无reload自动出现；PNG真实红矩形/蓝圆，PDF真实读到Round 2 PDF Preview / The blue circle number is 42.，正式Download得到与授权source逐字节匹配的PDF（自有下载已移入证据downloaded-report.pdf）。Back to Chat回other同ID及VALIDATION LOCAL DRAFT ONLY草稿；其历史初受ENV-02阻断；主会话只补other自身loopback路由、正式重建失败idle runtime后，真实UI复验显示Other Profile isolated question/answer，模型recovery-fixture、Context11%。随后从other进入固定default Files子目录/recovery-folder/note.txt，实际显示Nested recovery file baseline，再Back to Chat，正确回other同ID、两条隔离历史及原草稿；再断WS/解除，自动恢复历史且Send重新可用。default同storedID此前真实历史/其后删除，未污染或删除other。证据s3-other-retest-*、s3-retest-*；因此ENV-02关闭为夹具问题，不归产品缺陷。New Chat Profile菜单只列default/recovery-other，未创建新Session、未发送other。PNG重连画面存在，但未获新GET，相关二进制重读按VAL-04失败，不能混作通过。证据s3-*。
- **S4：失败（VAL-04）。** 初始history Attached image真实640×360，352×198.9px可见。先临时移动workspace PNG但仍得到可解码新blob，已恢复原文件；继而按正式pathname精确GET503断WS/恢复，容器仍可见且新blob，完整proxy切片只有bootstrap/WS/metadata/history，没有/api/fs/download。故本轮实际网络重取/失败自动重试未发生，不能判成功。未移动public产品源。证据s4-before、s4-503-dom.json/.png、s4-proxy-503.jsonl；响应缓存策略由主会话复核。
- **S5：阻断（VAL-03）。** 正式New Chat/default、recovery-fixture/medium、唯一获准prompt输入后Send disabled；新文档reload恢复相同草稿和模型仍禁用，无断线或错误提示。未arm、未请求供应商、未发送任何Turn，未绕UI直接RPC。fixture/native曾有同版机制证据但不替代此真实入口失败。s5-new-disabled.txt/.png；活动流后续/完成/唯一assistant真实用户结果均未执行。
- **S6：通过，限已执行正式writer结果。** 深历史证据完成后、已备份initial-state-backup.db；断WS正式replace后恢复只有Replacement question/answer，1200行不复活；正式edit在同条数下自动变Edited externally，侧栏原地跟随；compact出现可展开Validation summary并保真实先前历史；主会话只重启53575（PID2584→9754，新epoch），原页/展开摘要自动恢复不reload；正式rewind撤去summary，保原先Edited externally/Replacement answer（符合原生lineage）；正式delete后安全退New Chat且列表删除目标。第二次夹具rewind因最新子Session已空而StopIteration，未写入，不当产品失败或第二次rewind通过。未在线回灌DB。s6-*及主会话epoch日志。Context合法失效数值的实际变化无可用样本，按同版V5/Q机制证据，不推断该数值已实测。
- **S7：通过。** recovery-image/messages真实503时图文保留，显示Error503/Retry recovery；解除代理后自动重试成功、错误控件消失，未点Retry或reload。侧栏/api/sessions明确401后当前图文/图片/列表清空，发送禁用；Files真实文本/api/fs/read-text401同样清自持预览与面包屑。解除后用正常新文档重新确认本地身份，非JS赋权。s7-*。401/503都是只GET精确路径的外部依赖故障，产品/WS协议未改；文件权限403/迟到凭据等边界复用V5而不声称实际逐项操作。
- **S8：机制/包装证据符合，actual APK用户豁免且未验。** 只读同版XML22+13+5项全部failures/errors/skipped0；apk-v5-manifest/badging为0.1.5/1005、439资源零差异、指定SHA和v2同证书。未为验收复跑Gradle，未安装APK/开模拟器。final-environment-receipt.json记录复核字段与恢复结果。

上述证据均在ignored validation-v1/；每场景截图/AX文件mtime提供本次实际时间序列。仅用户明确要求的合成文件/SessionDB变化；未生产、真实API、部署、commit/push。当前故障{}，PNG/文本原副本恢复，本次唯一自有隐藏tab已关闭。计划顺序因环境与阻断调整为先完成可执行路径，所有未执行项明确保留。

- S5重新打开：s5-run2-reopen-afterwait.png/AX明确Error: Recovery unavailable: runtime_unavailable及Retry recovery，当前只呈现user，完整assistant虽已真实入库却不可重新使用；usage-expanded仍在同错误下显示retained0。因此S5不能整体判通过，追加VAL-05，不用raw SessionDB112直接将胶囊0另判产品错。S2当前无法权威安装historyindex与该恢复失败的关联由原实现者诊断；本报告保留实际“cold/重连分页均未进800”，不从机制解释豁免用户操作。
- S4/Files热资源复验通过其可执行部分：baseline真实3913B红矩形/蓝圆42；download503重连时截图保留同旧图并有真实Error503/Retry；同一路径合法临时换51568B橙Hermes图标、解除故障后未reload/未点Retry自动显示新图与新字节数。s4-files-proxy-requests有11次/api/fs/download GET，证实本轮实际资源重取及失败重试，不把新blob独自当成功。故VAL-04的Files/共享下载传输结果已获正向证据；历史图片owner恢复的影响边界仍随VAL-05处理，不冒称其重开已通过。Files无新增持久缓存，纯内存旧预览过渡。
- 本次s4-files-auth.png捕获太早，仍显示旧图，未证实401清理，**不用该图片判通过**；此前U1真实文本401清Files及V5/开发同未改认证路径的binary401有效证据可限定复用，最新实际捕获边界明确保留。故障已{}，原PNG当前SHA/备份SHA/原记录SHA一致，未改public产品源。

### 后端52c5088后的阶段复验（前端b8f06ff，以下VAL-06待修为当时历史）

- **S5完整通过／VAL-05关闭。** run3正式NewChat→唯一授权输入→前两段/Stop→真实WS断开→同sid223438_957ee5恢复仍有前两段和Stop→resume六段完成→同document NewChat→侧栏重开同sid，原完整回复与Usage112/Context0真实可读且无runtime_unavailable。已独立查看two-chunks/disconnected/reconnected-running/complete/new-after-complete/warm-reopen的AX和两张最终PNG。read-only actual SessionDB proof为user1/assistant1、精确六段、两真实UID；fake requests1/chunks6/complete4.237秒。首run超60秒及run2重开失败历史保留，不回写成成功。
- **G8有效胶囊高亮通过。** run3的1430个真实DOM样本（4497ms）中，0tokens/13%于1788ms变112tokens/0%，两卡data-updated=true从1788到2402ms，随后移除，open始终closed且无持续重置。Context始终116×32；Usage新值后198.72×32在高亮内不变，旧文本宽162.59，属于内容变化后的自适应宽度，不能写成跨所有文本尺寸绝对不变；实际动画未缩放/改变展开。精确CSS淡入/淡出沿未变P机制证据，不新设卡片固定宽度或FPS要求。
- **S2分页与实际运动通过相应目标。** 此前按钮离屏的click未产生真实用户动作，不能据无GET判产品分页失败；实际tab.scroll至top0且按钮可见后，真实click立即首行800，三次真实页达首400/800 articles（s2-fixed-three-pages-ax）。稳定collapsed anchor实验2850个样本/10.5秒，top0→57617→58309.5→58313，minNodes600、anchor DOM从未缺失、errors均None；最终原图显示真实External append尾部，无整页清空。连续几何确有中间位置，非仅前后截图；不把CUA取样间隔当动画精确时长。
- **真实人工输入后无抢回，通过可观察结果；精确inflight边界复用P43。** 3283个样本中检测top57894（小于tail58313）后调用真实up1，API429ms延迟使input发生在Node6047ms，不能绝对宣称在240ms动画结束前；输入返回后到10.5秒top57606恒定、最终截图停在1193–1195而非tail，无重播旧滚尾。P43同源阅读机制证据补精确动画内取消，明确区分实际结果与时序机制，不伪造实机动作时刻。
- **VAL-06仍未关闭（原R4/R5/S2详情）。** s2-final-detail-101截图/AX为真实展开Thinking但Loading details；父执行者后续确认未取得有效值并诊断cold initialize未给HistoryDetails选owner、派生Thinking DOM身份未纳facet/visible映射。此为原有可见详情恢复接线要求，不新增能力/节点/协议。等待最小修后实际cold展开有效值→断线→重连同详情复验；早前刚Loading就断线的实验不算稳定详情前置成功。已通过U1的导航展开401只代表当时路径，不替代本次cold缺口。


### 最终Web2346a030原详情缺口复验及收口

- **VAL-06关闭：cold展开与重连详情真实恢复。** 已独立读取s2-detail-final-before/disconnected/recovered的AX及原图。cold实际Thinking1001展开显示Expanded detail 1001，断WS时仍展开且保原值；构建结束后的s2-detail-final-recovery-samples.json有2758个真实DOM样本/8498ms，详情全文始终为ThinkingExpanded detail 1001、open=true、节点300持续存在，没有Loading或空白。top0→24309.5→25885→27012→27852.5→28421.5→28770→28926→28986.5→28992，连续中间位置及最终真实尾部共同支持统一交接/有限滚尾，不将单张前后截图充当运动过程。
- **用户输入后的最终可观察结果通过，保留时序精度边界。** s2-input-final-samples.json检测top23347.5小于tail28992后，通过正式原生up1输入，invoked3962ms/done4011ms；随后top27492.5保持至8500ms，没有到tail或重播。已独立看对应AX/PNG，最终可见1187–1190附近而非最后一行。检测读数有252ms接口延迟，故不绝对声称wheel位于240ms运动结束前；实际人工输入后不抢回已观察，精确inflight取消复用未变同源P43机制证据，未新设FPS/时序门槛。
- **排除污染样本。** s2-detail-fixed-cold的有效详情值可保留；其后s2-detail-fixed-recovery-samples受并行Android构建改public/assets触发Vite整页reload干扰，不能作为同document重连成功或产品失败。只采用构建结束后上述final批次关闭VAL-06，准备失败历史保留。
- **限定复用及实际证据归属。** S3/S6/S7的U1独立操作结果沿未变owner/writer/epoch/认证路径复用；本次没有重新造全部历史破坏或新epoch。历史图片下载503/解除与binary401沿未改通用reader复用dev-browser-v6原始图/AX/请求和receipt（source b0ff8824cce5603e06aa1e73f962a3da6090c65e）：image-503.png实际历史图保留且报503、image-recovered.json为错误消失/新blob/640×360、请求有正式download GET；files-auth.png/AX为预览及面包屑清理。它们是开发执行证据，本验收者已独立直接读原始文件，**不冒称本次独立UI执行**。独立关键补证为本轮Files同源warm后真实503保图→同路径内容变化自动采用以及11次GET。最终s4-files-auth过早图不计401成功。
- **最终包装只作包装判断。** 已读apk-delivery-manifest.json：Web2346a030a5ac4b25d4a4470daaa367f666098fd8／后端52c5088fd6afb1b7da730ec8b0f65ad3068ec7e9，APK0.1.5/1005、32,091,269字节、439资源零差异、v2原证书，SHA256 b92f0ade5594e5005c6f9b57e9f1ea1e2a4477920fce988492d5b6ede261b949。旧apk-final-manifest的b8f06ff包不充当此最终包。原生40项按未变源码范围复用；actualAPK始终C17用户豁免、未安装/未验，未部署生产。
- **恢复与显示保护。** faults{}，授权shapes.png原SHA与备份一致、文本原副本已恢复，无生产/真实供应商/部署/设备/源码修改/commit/push。U1自有页已关闭；最终父隐藏tab6由父会话持有，交付前由其关闭，不虚写本验收者已关闭父页。

独立数值复核摘要保存在validation-final/independent-observation-summary.json；本验收者未操作父UI/模型/源码，所有判断均基于指定原始证据及原冻结目标。

## 5. 问题、修复与复验

以下首表为U1历史失败，当前关闭状态见其后最终追加复验表。

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| VAL-01 | 同源成功历史/胶囊→block_ws→正式reload；解除WS但GET history延迟8秒对照 | WS未连时No messages yet/Usage破折号；WS成功后缓存立即出现，证明持久快照存在却被连接门槛阻挡。s1-cached-*及s1-image-cache-* | 范围内失败，主会话已接收；C01/§1.4冷开过渡目标未满足 | Web0eef280，未修 | 新候选需全新独立复验，固定本版失败不改写 |
| ENV-02（原暂名VAL-02，已关闭） | default同ID→other同ID→Files→Back to Chat | other持续pending steer owner is not ready，Files返回路由/草稿正确但无历史。s3-other-loaded/s3-return-other | 主会话诊断是other自身未配loopback模型导致native Agent AuthError，非owner产品归因；已仅补隔离夹具并经真实UI复验关闭 | 产品未变 | s3-other-retest-loaded、s3-retest-return/reconnected及最终DOM通过 |
| VAL-03 | 正式New Chat/default→获准prompt；再正式reload同路由 | recovery-fixture/medium已就绪、草稿存在，Send持续disabled，不能开始活动Turn。s5-new-disabled.*；primaryAction对active undefined返回Unavailable | 范围内阻断，主会话已接收；S5未arm/未发送，不能以直接RPC绕过 | Web0eef280，未修 | 新候选须从真实New Chat发送、running重连、后续流、唯一持久回复全链复验 |
| EVID-01 | 深anchor恢复只取得等待前/中和最终tail几何，未捕获实际240ms运动；S5未能开始，缺有效Usage变化高亮用户证据 | s2-recovery-samples只证明等待anchor稳定与最终尾部，不能证明运动过程；同版阅读/胶囊机制证据仍有效 | 用户呈现证据缺口，非已证产品缺陷；下轮补实际动画/高亮 | 未修源码 | 新候选复验S2真实运动帧/用户取消和S5有效高亮，不重跑大套 |
| VAL-04 | 可见历史图片成功→精确/api/fs/download503+断WS→解除WS保503 | 新blob且图仍可见，proxy没有任何download GET。s4-503-dom/PNG/proxy切片；主会话核响应ETag/Last-Modified而无Cache-Control，reader无no-store | 范围内失败，不能以新blob冒称实际重取；涉及Files同authorizedFile缓存策略 | Web0eef280，未修 | 新候选真实GET、失败保图、自动重试及Files二进制重读需复验 |

### 最终候选追加复验表（旧版本行保留）

最终2346a030／52c5088补充：VAL-05由run3 warm-reopen/DB1+1关闭；VAL-06由构建结束后的cold有效详情/断线/完整恢复样本关闭；EVID-01已补齐。原失败不回写，当前无未闭Web用户结果阻断。

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| VAL-01／N06 | Load older→default110/other8→已有真实历史→blockWS冷reload→解除 | 连接前有正确Timeline/胶囊/118摘要，解除后较早行仍在及真实sessions重读。s1-*原始证据 | 已关闭；后续正式分页、running恢复及同document重开全文均通过 | Web b8f06ff | 独立读图/DOM及proxy切片，未清缓存 |
| VAL-03 | New Chat/default→真实Send→两段→断WS/恢复仍Stop→resume六段/DB1+1 | s5-run2-*主链实际通过，精确6段及唯一持久assistant；重新打开另报VAL-05 | 已关闭；run3含重新打开的完整S5通过 | Web b8f06ff | UI/DB均核，不把首run60秒预算失败算通过 |
| VAL-04 | Files同URL预热→503重连保旧→同路径换图→解除自动采用 | 3913B红蓝图→503错误且保旧→51568B橙图，proxy11次真实download。s4-files-* | 已关闭；Files/共享下载传输真实补验，历史图/认证按明确未改路径限定复用 | Web b8f06ff | 文件SHA已还原；本次401截图过早不用作清理成功 |
| VAL-05 | 正式完整Turn结束→导航离开→重新打开同Session | DB唯一assistant精确六段，但UIruntime_unavailable且仅user缓存，s5-run2-reopen-afterwait.png/AX | 原后端失败；52c5088后run3原会话重开全文通过，已关闭 | 后端52c5088 | s5-run3-warm-reopen原图/AX及DB proof，S2实际分页也成功 |
| VAL-06 | cold已有Conversation→可见Thinking展开101→等待；修后cold1001→断WS→恢复 | 原Loading details保留；最终2758样本始终Expanded detail1001/open true/300节点，真实连续交接 | 已关闭；原范围详情接线缺口修后原路径通过 | Web2346a030 | s2-detail-final-before/disconnected/recovered及recovery-samples；排除构建reload污染批次 |
| EVID-01 | 运动与有效数值变化 | 原1101同值样本仅同值不闪；最终连续运动/真实人工输入后保持及1430样本有效胶囊高亮齐 | 52c5088后证据齐，已关闭；精确inflight时序复用P43且明确边界 | 后端52c5088／前端b8f06ff | stable-motion/cancel-motion连续DOM及run3实际有效data-updated开关 |

## 6. 验收结论与推荐复核

**最终Web Validation通过。** 固定最终Web2346a030／后端52c5088，无已知未闭的范围内Web用户结果阻断。连接前缓存与多页摘要、真实分页/详情/连续交接、活动Turn断线后的后续流与唯一持久回复、同document重开、Files同URL真实资源变化/503保旧自动重试、有效胶囊轻亮已由本轮原始用户结果支持；未受影响的owner/Files返回、历史writer、新epoch与401按上文明确版本边界复用。没有把实现说明、模型正文数据库存在、按钮可用或连接成功单独当完整用户成功。

精确240ms/动画内取消及未变原生机制复用已有同源证据；本轮实际人工输入后不抢回直接观察已通过，不把接口取样时间当精确事件时刻。未增加新的固定宽度、FPS或全量Verification要求。父执行/独立读证据、开发证据限定复用与受污染样本排除的边界如第4节所列，均不隐瞒。

最终APK包装证据符合0.1.5/1005、439资源零差异和原签名，最终SHA为b92f0ade5594e5005c6f9b57e9f1ea1e2a4477920fce988492d5b6ede261b949；**实际APK生命周期按C17用户豁免、未验**，不据构建/Web/Robolectric声称平台实际通过。无生产部署或真实供应商请求。父会话负责最后关闭其自建隐藏页和最终交付复核，无需因旧报告的待修文字再追加全套审查。

以下为**U1历史结论**（Web0eef280／后端dd9a4c5），保留原失败和当时建议，**不是当前状态或新的执行要求**。

**Validation未通过，门禁未关闭。** 固定Web0eef280/后端dd9a4c5有三个范围内产品缺陷：VAL-01缓存冷开等待WS才开始展示；VAL-03正式New Chat发送禁用，活动Turn旅程不能开始；VAL-04可见图片恢复没有实际下载GET，HTTP缓存可绕过本轮重取。主会话已接收，当前产品未修改，不用机制单测或先前native探针替代缺失用户结果。

- G1失败；G2深历史/可见Thinking/等待保anchor到真实末尾的数据结果通过；运动过程直接采样不足记EVID-01，取消/降动效机制证据可复用，真实运动呈现仍需补证。
- G3的owner隔离、固定Files文本/媒体呈现、下载与深层返回通过，ENV-02夹具问题已真实UI复验关闭；其二进制本轮重取和G4共同受VAL-04阻断。
- G5受VAL-03阻断，未arm/未发任何Turn；发送后running恢复、后续流/唯一最终assistant均未执行。G8菜单展开/有效值可读/布局已观察，但新的有效数值变化高亮缺真实本版用户证据，随S5复验补齐。
- G6正式replace/edit/compact/rewind/delete及已有历史新epoch自动恢复通过；没有在线回灌DB，没有伪造外部SQL或运行态。G7普通503保画面自动重试与明确401清历史/图片/Files预览通过。
- G9同版原生40项与APK0.1.5/1005、439资源、签名/指定SHA证据符合；**实际APK生命周期按C17用户豁免，未验**。构建不代表安装或实际5秒生命周期通过。

修复后推荐以全新独立验收者复验本轮全范围，并重点走三个完整路径：①同源已有成功缓存→WS被拒冷开→连接前即显示正确owner快照、随后每轮真实重读；②New Chat/default输入唯一获准prompt→正式Send→流中断线→仍running恢复→继续流→唯一持久最终回复并观察胶囊轻亮；③已显示历史图片/Files二进制→精确下载503+重连→代理实际GET、失败不ready且保画面→解除自动重试解码成功。其它有效同版未受影响证据按风险复用。

入口为http://localhost:5178/，只自建隐藏IAB。因本次S6已正式删除default/recovery-validation，下一候选若需1200行样本应由正式SessionDB writer重新准备，不在线回灌整库；initial-state-backup.db只保留起点。最终操作痕迹/安全恢复见ignored validation-v1/final-environment-receipt.json，故障{}、原PNG/文本哈希恢复、仅自建隐藏tab已关闭；PDF正式下载匹配source后移入证据。未真实供应商API/生产/部署/设备/commit/push，Web产品工作区保持干净。

本报告六节已定稿交回主会话；当前Web验收通过，旧版整改历史保留。最终目标结束与交付判断由主会话负责。
