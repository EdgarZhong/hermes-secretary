# Validation：20261024-web-recovery

## 1. 结果概览

验收者validation_v1（gpt-6.1-sol/high，无主会话上下文、不派生），2026-10-24。已完整读autonomous-run、real-user-acceptance及模板、两仓AGENTS、主仓当前CLAUDE（Web无CLAUDE，统一入口为主仓）。依据为本轮snapshot-index.md、baseline.txt及冻结主仓ba83d2b430e3448461dd7feb9f1acd8fc94c6cc9的06 §0.4、§1.2适用性、§1.3、§1.4/R1–R10、§1.13，08 §1/3的owner保持条款，用户C01–C18。plan仅作场景线索。

待验Web0eef2802725c7999636ca918e75d5513be608fcd（0.1.5）、后端产品dd9a4c57dd7c182ad8497f9538e115bbab3131b0。公开入口http://127.0.0.1:5178。进入条件为独立Verification v5全轮18组通过。同版机制证据可复用，仍须真实Web用户入口观察。

用户目标：缓存保住当前画面，无整页刷新自动恢复当前实际需求与活动Turn；分页、owner、读失败、历史改写及认证失效正确，保留阅读/胶囊呈现。主会话已完整过目并明确批准S1–S8执行。当前已开始真实UI，门禁未关闭。 APK实际生命周期按C17用户豁免，明确未验，不以Robolectric当实际平台。C18最终包必须0.1.5。

## 2. 环境与准备

- UI只创建自己的Codex隐藏IAB（iab/visible:false），about:blank后导航本地；不动用户tab、Chrome、桌面、可见页或模拟器，结束关闭自有tab。CUA遵文档；DOM只读真实页面/几何，不访问Controller或内部业务state，不伪造协议/成功。
- Vite5178→fault proxy53576→真实隔离Dashboard53575，供应商替身loopback SSE53577。四服务由主会话持有，不自行停；新epoch协调主会话只重启53575。53445/53446不动。不得访问生产域、真实供应商API或部署。
- 合成SessionDB：default/recovery-validation 1200行（row0–1199，奇数Thinking为Expanded detail i）；recovery-other同storedID仅隔离问答；default/recovery-image含原生@image。Files固定default，两Profile工作区在仓库外。深分页先做；破坏性writer前通过SQLite backup备份授权合成库。不能seed重置custom模型路由。
- 已读fault_proxy.py/seed_validation.py/stream_control.py。当前faults.json仅支持block_ws及GET delay；图片失败可临时移开授权公开PNG再恢复。HTTP503/401需先协调代理能力扩展，不改产品。proxy-requests.jsonl只补充真实重读/无reload证据，不代替呈现。
- 唯一发送授权：正式New Chat/default输入 `RECOVERY_LOCAL_FIXTURE: Produce only the controlled local stream.`，先arm全新run、pause_after2/interval1；单run60秒，及时断WS/恢复仍running后resume。真实native Turn/租约/DB，只有供应商SSE是受控合成依赖；最终以UI及真实历史/唯一assistant落库和idle共同确认。
- 白名单：仅本报告和主仓ignored `.hermes-dev/web-recovery-20261024/validation-v1/`证据，以及授权faults/合成fixture。产品只读，无stage/commit/push。每次故障/文件恢复留receipt。
- APK路径为ignored Hermes-Secretary-0.1.5-arm64.apk，指定SHA256 e4c5d68b371364ac2a3a03756f0c5094fedb21dbeabdd8aa3d902ecb15dac7b7；version1005/439资源/同证书由同版证明核对，不安装。
- 差异/复用：桌面隐藏IAB、合成数据，未验生产门户/蜂窝/实际WebView。原子cut、ring/租约/并发/取消、容量/TTL/迟到结果和原生边界复用V5及同版机制证据，不重跑大套。精确动画内部时长/降动效机制可复用，但实际视觉必须观察。

## 3. 用户目标与场景覆盖

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

## 5. 问题、修复与复验

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| VAL-01 | 同源成功历史/胶囊→block_ws→正式reload；解除WS但GET history延迟8秒对照 | WS未连时No messages yet/Usage破折号；WS成功后缓存立即出现，证明持久快照存在却被连接门槛阻挡。s1-cached-*及s1-image-cache-* | 范围内失败，主会话已接收；C01/§1.4冷开过渡目标未满足 | Web0eef280，未修 | 新候选需全新独立复验，固定本版失败不改写 |
| ENV-02（原暂名VAL-02，已关闭） | default同ID→other同ID→Files→Back to Chat | other持续pending steer owner is not ready，Files返回路由/草稿正确但无历史。s3-other-loaded/s3-return-other | 主会话诊断是other自身未配loopback模型导致native Agent AuthError，非owner产品归因；已仅补隔离夹具并经真实UI复验关闭 | 产品未变 | s3-other-retest-loaded、s3-retest-return/reconnected及最终DOM通过 |
| VAL-03 | 正式New Chat/default→获准prompt；再正式reload同路由 | recovery-fixture/medium已就绪、草稿存在，Send持续disabled，不能开始活动Turn。s5-new-disabled.*；primaryAction对active undefined返回Unavailable | 范围内阻断，主会话已接收；S5未arm/未发送，不能以直接RPC绕过 | Web0eef280，未修 | 新候选须从真实New Chat发送、running重连、后续流、唯一持久回复全链复验 |
| EVID-01 | 深anchor恢复只取得等待前/中和最终tail几何，未捕获实际240ms运动；S5未能开始，缺有效Usage变化高亮用户证据 | s2-recovery-samples只证明等待anchor稳定与最终尾部，不能证明运动过程；同版阅读/胶囊机制证据仍有效 | 用户呈现证据缺口，非已证产品缺陷；下轮补实际动画/高亮 | 未修源码 | 新候选复验S2真实运动帧/用户取消和S5有效高亮，不重跑大套 |
| VAL-04 | 可见历史图片成功→精确/api/fs/download503+断WS→解除WS保503 | 新blob且图仍可见，proxy没有任何download GET。s4-503-dom/PNG/proxy切片；主会话核响应ETag/Last-Modified而无Cache-Control，reader无no-store | 范围内失败，不能以新blob冒称实际重取；涉及Files同authorizedFile缓存策略 | Web0eef280，未修 | 新候选真实GET、失败保图、自动重试及Files二进制重读需复验 |

## 6. 验收结论与推荐复核

**Validation未通过，门禁未关闭。** 固定Web0eef280/后端dd9a4c5有三个范围内产品缺陷：VAL-01缓存冷开等待WS才开始展示；VAL-03正式New Chat发送禁用，活动Turn旅程不能开始；VAL-04可见图片恢复没有实际下载GET，HTTP缓存可绕过本轮重取。主会话已接收，当前产品未修改，不用机制单测或先前native探针替代缺失用户结果。

- G1失败；G2深历史/可见Thinking/等待保anchor到真实末尾的数据结果通过；运动过程直接采样不足记EVID-01，取消/降动效机制证据可复用，真实运动呈现仍需补证。
- G3的owner隔离、固定Files文本/媒体呈现、下载与深层返回通过，ENV-02夹具问题已真实UI复验关闭；其二进制本轮重取和G4共同受VAL-04阻断。
- G5受VAL-03阻断，未arm/未发任何Turn；发送后running恢复、后续流/唯一最终assistant均未执行。G8菜单展开/有效值可读/布局已观察，但新的有效数值变化高亮缺真实本版用户证据，随S5复验补齐。
- G6正式replace/edit/compact/rewind/delete及已有历史新epoch自动恢复通过；没有在线回灌DB，没有伪造外部SQL或运行态。G7普通503保画面自动重试与明确401清历史/图片/Files预览通过。
- G9同版原生40项与APK0.1.5/1005、439资源、签名/指定SHA证据符合；**实际APK生命周期按C17用户豁免，未验**。构建不代表安装或实际5秒生命周期通过。

修复后推荐以全新独立验收者复验本轮全范围，并重点走三个完整路径：①同源已有成功缓存→WS被拒冷开→连接前即显示正确owner快照、随后每轮真实重读；②New Chat/default输入唯一获准prompt→正式Send→流中断线→仍running恢复→继续流→唯一持久最终回复并观察胶囊轻亮；③已显示历史图片/Files二进制→精确下载503+重连→代理实际GET、失败不ready且保画面→解除自动重试解码成功。其它有效同版未受影响证据按风险复用。

入口为http://localhost:5178/，只自建隐藏IAB。因本次S6已正式删除default/recovery-validation，下一候选若需1200行样本应由正式SessionDB writer重新准备，不在线回灌整库；initial-state-backup.db只保留起点。最终操作痕迹/安全恢复见ignored validation-v1/final-environment-receipt.json，故障{}、原PNG/文本哈希恢复、仅自建隐藏tab已关闭；PDF正式下载匹配source后移入证据。未真实供应商API/生产/部署/设备/commit/push，Web产品工作区保持干净。

本报告完整阶段交回主会话用于集中整改，最终目标结束判断由主会话负责。
