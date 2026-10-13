# Assistant UI 能力、显示吞吐与整改边界研究

> 2026-10-13；研究交回，**未实施前端整改，未关闭独立审查问题**。前端生产仓及隔离整改 worktree 都是 `002f7a27fcf7313491f0301e143df7d3b6148088`。仅新增本报告和 ignored 研究证据；不修改产品、package、lock、规格、全局看板或 verification，不提交，不派生。遵循 executing-plans 七项交回及 autonomous-run 消息交接契约。

**结论：Assistant UI 适合成为消息/part 的渲染与局部订阅基础，值得实际接入；不能接管 Hermes 事务。** 当前已保存的隔离对照证明，历史 Markdown 重复解析和每个突发事件触发整页渲染能产生秒级积压。框架结合稳定消息对象、局部订阅和按帧绘制，可以消除这个受控负载下的积压；不过普通 React memo 加按帧绘制也几乎达到同一延迟，不能把全部提速归于 Assistant UI。框架本身并未直接解决 Rewind、附件原生合同、侧栏刷新、Usage 发布或 Instant Reminder 源消息缺失。

**建议接入边界：** 保留 Controller、REST/WS、原生 UID、实际 source 顺序和既定 design 组件；使用现有本地版本的 `MessageProvider`、`MessagePrimitive.Parts`、`useAuiState` 与 `MarkdownTextPrimitive smooth={false}` 做真正的消息组件/订阅接入。保留自定义 Composer 的业务 action owner，先修复独立 undo 与已确认的 Tab 补全；不把框架默认 Send/Cancel/Edit/queue 语义直接接到 Hermes。暂不升级依赖或引入虚拟化。

## 1. 任务对应条款与证据基线

- 现行 06：§0–§1.6（L13–192）、§1.8–§1.13（当前 L206–284），§3（当前 L445起）、§4（当前 L531起）。Usage C73 和 slash C76 已由 Main 插入，不能沿用旧后续行号。
- 02：§1 L14–257 的 Conversation/Session/Message Identity、真实 transcript 与不引入第二 owner；§5.6 L1542–1712 的真实 carrier、时间与源顺序；Final implementation invariants L2514起。
- Snapshot Index、baseline.txt、plan.md 证据索引及 verification.md 完整初审；C69–C76、Main 新转交的 U-R2-04。初审仍为56符合、6不符合、3证据不足，本报告不是 Verification/Validation 通过证明。
- 当前实际依赖：`@assistant-ui/react 0.12.28`、`react-markdown 0.12.11`、`core 0.1.17`、`store 0.2.9`、`tap 0.5.10`。package 声明 `^0.12.0` 不等于只装了0.12.0；本报告以 lock/本地实现为准。
- 已有隔离证据：`.hermes-dev/round2-verification/timeline-latency/`。本次新增 `research-source-manifest.json`（当前源码/证据 SHA256、版本及边界）和 `research-metrics-summary.json`（原样本统计）。首次被中断研究没有完整报告，本次复用其采样，未重新跑大包/模型。

已读项目 AGENTS/CLAUDE 和所派 skills；权限更窄的本次白名单覆盖 skills 中通常要求更新 plan 的动作，因此本研究不改计划/看板。

## 2. 实际变更与官方/本地能力核对

产品变更为零。联网只读核对官方文档与官方 GitHub main 源码，再检查本地安装源码；最新 main 不是本地0.12版本，亦不等于已发布并能安全升级的版本。

| 能力 | 本地实际支持 | 相对当前实现的帮助与限制 |
|---|---|---|
| External Store Runtime | 有；原数据由外部 owner 提供，convertMessage 转成呈现格式，能力由 callbacks 决定 | 与现有 Controller 相容；不需要 LocalRuntime、AI SDK、Cloud 或新增后端。不会自动处理 Hermes replay/admission/Conversation identity。 |
| 消息/part 局部订阅 | `useAuiState` 使用 `useSyncExternalStore` 选择 slice；`MessageProvider`、`MessagePrimitive.Parts` 可用 | 历史卡片无需读取整个 AppState；文本 part 能独立更新。selector 每次构造新对象仍会重复渲染，父组件不 memo、对象不稳定也会抵消收益。 |
| Thread 消息列表 | 本地 `ThreadPrimitive.Messages` 以 length 订阅、`key={index}` 和 MessageByIndexProvider 构造列表 | **不可原样接回已移除的旧方案。** F12 曾在 live→durable 缩表时 index18/length18 白屏。现行 main 改了 ID keys 并有缺失ID返回null的 `Unstable_MessageById`，本地没有这个 UI primitive；不能拿最新修复冒充已安装能力。 |
| Markdown 流式呈现 | 本地 MarkdownTextPrimitive 使用 part 文本、ReactMarkdown、代码头/复制基础，支持 components override；默认 `smooth=true` | `smooth=false` 才符合本次及时输出方向；默认平滑会增加显示追赶，不能误当后端running。库提供 `memoizeMarkdownComponents`，但须显式使用、稳定 components/plugins，不是自动增量Markdown parser。 |
| 最新 Markdown 优化 | 官方 main 的 MarkdownText 新增 renderer memo、稳定 props 和可选 `defer`；本地没有 `defer` 和对应 renderer memo实现 | 最新能力是真实存在的，但本轮不应未经评审升级。当前可以用稳定消息/part订阅及外层memo取得主要收益。重解析正在增长的一条文本仍有开销。 |
| Viewport / 自动跟随 | 本地有 Viewport、ResizeObserver、底部判断及runStart/initialize/threadSwitch滚动选项 | 能复用一般聊天跟随；当前自有 `useTimelineReading` 还负责route位置恢复和历史prepend锚定。双owner同时写scrollTop会打架，不能简单叠加。最新文档 `hasEarlier/onLoadEarlier` 本地不存在。 |
| 虚拟化 | 官方明确**没有开箱虚拟化 Thread**，指南组合 `@tanstack/react-virtual` 和最新 row primitives | 本地没有 `createThreadRowsSelector`/`ThreadPrimitive.Row`。增加外库/升级、动态行测量、折叠和prepend/follow协调都是工程成本；不能称“换Viewport自动虚拟化”。当前33行负载在不虚拟化时已能解决主要积压。 |
| Composer 输入 | 本地 Input 是controlled textarea，支持autosize、IME、focus、键位以及事件组合/override | 不提供可直接替代浏览器undo的独立文本历史管理；替换controlled textarea不保证Ctrl+Z修复。默认active时禁普通Send且Cancel为框架语义，与Hermes Steer/Interrupt/Rewind矩阵不同。 |
| Slash候选 | 本地有 `Unstable_TriggerPopover*`、Action/Directive、上下键/Enter/Escape处理；官方最新guide有slash adapter | 本地 trigger键盘switch没有Tab。其默认选候选会执行Action/插入directive，不符合当前“补全文本，Send正式dispatch”的语义。Hermes native catalog/completion、Tab补全和候选统一换行仍需业务接线；不能照搬文档静态命令或两列布局。 |

本地源码定位：`node_modules/@assistant-ui/core/src/runtimes/external-store/external-store-thread-runtime-core.ts`、`react/primitives/thread/ThreadMessages.tsx`、`store/clients/thread-message-client.ts`、`@assistant-ui/store/src/useAuiState.ts`、`@assistant-ui/react-markdown/src/primitives/MarkdownText.tsx`及`memoization.tsx`、`@assistant-ui/react/src/primitives/composer/ComposerInput.tsx`及`trigger/triggerKeyboardResource.ts`。这些是审阅依据，不修改依赖源码。

**一个具体浪费点：** 当前 App 的 `convertMessage` 是每次render新建的inline函数；本地 ExternalStoreThreadRuntimeCore 在convertMessage引用变化时清空WeakMap converter。即使历史 TimelineNode 对象仍稳定，runtime也失去转换复用。callbacks/plugins/components和未变化节点应保持引用，不应仅靠引入库名。

官方依据（均2026-10-13读取，链接为primary source）：[ExternalStoreRuntime](https://www.assistant-ui.com/docs/runtimes/custom/external-store)、[External Store API](https://www.assistant-ui.com/docs/api-reference/external-store/runtime)、[Primitives](https://www.assistant-ui.com/docs/primitives)、[Message](https://www.assistant-ui.com/docs/api-reference/primitives/message)、[Primitive hooks](https://www.assistant-ui.com/docs/api-reference/hooks/primitives)。

版本差异直接核对：[官方main ThreadMessages源码](https://raw.githubusercontent.com/assistant-ui/assistant-ui/main/packages/core/src/react/primitives/thread/ThreadMessages.tsx)、[官方main MarkdownText源码](https://raw.githubusercontent.com/assistant-ui/assistant-ui/main/packages/react-markdown/src/primitives/MarkdownText.tsx)、[官方main ComposerInput源码](https://raw.githubusercontent.com/assistant-ui/assistant-ui/main/packages/react/src/primitives/composer/ComposerInput.tsx)。最新[Markdown element](https://www.assistant-ui.com/elements/markdown-text)、[虚拟化guide](https://www.assistant-ui.com/docs/guides/virtualization)、[Composer API](https://www.assistant-ui.com/docs/api-reference/primitives/composer)、[Slash guide](https://www.assistant-ui.com/docs/guides/slash-commands)不能替代本地版本检查。

## 3. 当前正式路径与建议接线

当前正式路径：

1. `api/client.ts:127` 的WebSocket onmessage解析全部event并同步通知listener；没有逐字播放或固定token限速。
2. `controller.ts` event按runtime、epoch/seq和route owner处理；reduceEvent/reconcileLiveHistory更新实时投影；`publish` L251–252每次替换整个AppState并通知所有subscriber。
3. `App` 通过 `useSyncExternalStore(controller.subscribe, controller.getSnapshot)` 订阅完整AppState，每个选中会话event重新走App/Chat。
4. Chat `App.tsx:440–467` 投影history/live/temporary；`useExternalStoreRuntime` L468只提供runtime/Provider；消息实际由 `TimelineMessages` L116 的自定义map和 `NodeMessage` 绘制。
5. `Markdown` L73 使用普通ReactMarkdown，inline components、plugin数组每次新建。历史节点的Markdown随父render再次解析；折叠卡虽然有HTML hidden，children也在DOM/React树中，历史Thinking亦参与工作。
6. `useTimelineReading` 以layout effect/ResizeObserver协调跟随、prepend和恢复，不是显式输出速率限制；读layout/写scroll会消耗主线程，但已有对照尚未单独量化该成本。
7. Composer受控value来自整个AppState；onChange→setDraft→publish，async保存IndexedDB与原生action路由另属Controller。Primary selector/perform/submit才负责Hermes业务。

建议仍只有一个Hermes事实owner。上游identity/replay/order projection继续由Controller持有；在**已完成真实source投影及工具同ID合卡后**，以稳定 `node.id` 挂载framework message scope。普通/Thinking文本通过MessagePrimitive.Parts→MarkdownTextPrimitive；卡片外围、真实时间、工具Parameters/Result、Framework/Instant/Deferred、临时Notebook四区沿用现有design组件。metadata.custom保存UI投影kind与源引用，不改provider role、UID或durable正文。

本地0.12下可先采用公开 `MessageProvider message={stableReadonlyRenderMessage}`：其中index仅呈现字段，无index→thread lookup；message/part使用framework selector；父slot memo仅传需要的primitive props，不传整个AppState。`useExternalStoreRuntime` callbacks固定且不开放内置branch/edit/frontend tool execution能力，避免frame默认业务进入Hermes。该方式是受控的内存**渲染快照**，不新增Transcript DB/持久缓存/ledger。

**接线约束：** 普通MessageProvider的本地ThreadMessageClient为只读，edit composer是NoOp，其part状态默认complete；不能据此宣称已经实现live part状态。当前POC靠node.status保留native busy视觉且smooth关闭。正式实施须将running/interrupted/failed/unknown及分段完成状态按源映射或通过TextMessagePartProvider传递，并测试framework状态不会覆盖native active；不能把所有assistant status映射成complete/stop。若改为thread runtime的ID scope，还须证明缺失/切表/part数量变化安全；本次未测这一不同设计。

按帧合并应只合并**UI通知/绘制快照**：每条event仍顺序reduce、不丢源消息、不延迟业务事实；complete/interrupted、route切换、submit/withdraw确认、error等正式边界及时发布最终快照，清理旧帧，不能把模型或Steer消费改成UI scheduler。当前POC对complete做flush，仅证明该思路；正式方案需避免无差别更换所有controller subscriber或用frame延迟控制与草稿保存。

Viewport可先保留当前单一scroll owner；如果接入framework Viewport，应显式关默认initialize/runStart/threadSwitch强跳，由已存在的恢复/阅读规则控制，且只能一个owner写scrollTop。虚拟化留作更大history负载仍有实测瓶颈后的选择。

## 4. 验证结果：可量化收益与原因

### 4.1 既有隔离采样方法和有效范围

独立5178 FastAPI采样服务使用生产 `WSTransport`/`FanoutTransport` 发送受控event；独立5179 Vite加载生产App、Gateway、Controller、projection和design。读取已保留真实会话fixture（33源记录、44,767正文字符、23,073 reasoning字符、15工具结果）；不连接53445/5173、不调用真实Hermes/profile/model。初始化、finishHistory、readUsage、readCompaction被隔离stub，fixture是在采样入口直接装入内存的已保留投影。**因此它测的是既定输入下正式React/Controller渲染吞吐，不是完整backend/API/终态REST协调验收。**

负载A：300个delta，100 event/s、3秒，之后terminal `message.complete(status=interrupted)`。负载B：200 delta约2–3ms突发，再terminal。空history负对照同入口。

四种受控方案：

- Full：当前生产App、每event正常通知、普通ReactMarkdown；仅alias wrapper计数。
- Memo：其余同Full，只有ReactMarkdown按text equality跳过重复解析。wrapper忽略其他prop变化，**仅可用于此稳定配置反事实，不能复制为生产通用memo比较器**。
- Batch：Memo加requestAnimationFrame合并UI订阅通知，complete立即flush。
- Library POC：Batch基础上用稳定ID MessageProvider、selector、MessagePrimitive.Parts和MarkdownTextPrimitive smooth=false；继续用正式卡片/Controller/源投影。它不是开箱Thread套件，也未覆盖完整Hermes业务。

采样记录emit、write前时间、client handler起点/同步耗时、React Profiler和MutationObserver。表中“terminal→DOM”是emit到terminal序号对应首次DOM变更；**不是屏幕compositor完成绘制，也不是全量可见文本逐字符断言**。client最终累计文本与尾部DOM一致且seq无缺失；工具/临时节点/重连交互完整回归另行必要。

### 4.2 对照数值

| 受控负载 | Full 当前 | Memo | Batch | Library POC |
|---|---:|---:|---:|---:|
| 33行history，300正文delta，terminal→DOM | 1,528.9ms | 8.6ms | 10.7ms | 7.5ms |
| 同history，300reasoning delta，terminal→DOM | 1,545.9ms | 10.0ms | 13.4ms | 10.4ms |
| 同history，200delta突发，terminal→DOM | 2,903.4ms | 897.6ms | 41.4ms | 41.1ms |
| 正文负载 React Profiler累计actual耗时 | 3,829.4ms | 1,107.5ms | 887.0ms | 912.2ms |
| 突发负载 React Profiler累计actual耗时 | 2,455.0ms | 572.1ms | 27.9ms | 31.9ms |
| 正文负载 React commit数量 | 304 | 304 | 183 | 543 |
| 突发负载 React commit数量 | 203 | 203 | 4 | 10 |

来源：Full/Memo/Batch采用各自`*-final-*.json`；Library采用`library-dto-*.json`。单次值、同一设备/dev模式，并非跨设备稳定SLA。Library局部订阅使commit数量增加，每次工作更小；不能用commit少/多直接代替性能判断。Library总Profiler时间略高于Batch，差异没有统计意义，**没有证据称框架比妥善优化后的React方案更快**。

对正文负载，普通ReactMarkdown调用从Full 5,149次（累积输入8,152,518字符）降到Memo316次（836,906字符）、Batch197次（515,606字符）。Library的alias计数没有覆盖全部框架内部ReactMarkdown，**不能拿其197次声称框架总解析次数**。源码显示本地框架仍用ReactMarkdown重解析累计当前文本，没有增量parser。

当前Full空history terminal→DOM仅4.9ms；同33行history达到1,529ms。生产Controller不渲染的样本同步handler p95为0.1–0.2ms、普通stream client到达p95约1ms。Full terminal从emit到write前仅0.23ms，从write前到client handler开始约1,514ms，handler到DOM约15ms。突发Full对应约24.9ms、2,864.5ms、14ms。采样服务器的“wire”是调用websocket send之前，不能视为网络内核真正写完；但在同传输不改情况下，memo/batch反事实显著缩小积压，支持浏览器主线程被渲染占用、后续event回调得不到运行时间的解释。

**结论强度：**

- 强：当前受控生产React路径存在历史重复渲染负担；仅memo历史Markdown足以解决100event/s样本的大部分积压。
- 强：memo单独不能消除burst逐event绘制成本；按帧聚合后terminal约41ms，文本不在UI排队逐字播放。
- 强：Library组合在同量级负载可工作，提供符合规格的框架消息/part基础，且无需重设计视觉或更换Hermes执行层。
- 中：这能有效改善U-R2-02所描述的同类滞后；尚未操作用户真实当次页面并逐event观测，因此不是所有现场问题的唯一根因证明。
- 未证明：仅引入框架本身获得上述倍数；更大history/长代码块/大量图片/真实网络/移动软键盘的表现；硬Stop点击到最终屏幕paint的SLA。

旧样本缺完整当次source哈希manifest；新manifest记录的是**当前review时**的源码，不追认旧运行版本。保留`full-actual-burst.json`（0event）及`memo-empty.json`（HMR导致580event/最终4986字）为无效/污染样本，统计排除，不覆盖成通过。Vite旧日志首次后端未开、dependency reload均保留。

### 4.3 本次新增的身份边界采样

仅新开独立后台IAB tab：`http://127.0.0.1:5179/?mode=library&run=identity`，使用已在运行的隔离服务；执行3个合成delta和interrupted终态，随后24→1→0→33源记录替换。`library-identity-stream.json`记录5个event、最终45字、active=false；`library-identity-boundaries.json`四帧Timeline均存在、消息卡5→1→0→7、errors=[]；CUA页面实际显示DONE，console error/warn为空。独立标签页已关闭，没有改变用户页面、viewport、profile或服务。

这个证据证明**按ID局部MessageProvider方案**不依赖旧index lookup，能通过所测缩表/归零/恢复场景；不证明未经测试的ThreadPrimitive.Messages改回方案或全部工具动态part生命周期安全，不能单凭此关闭F12/全轮审查。

### 4.4 侧栏独立证据

已有`sidebar-dto.json`运行生产 `loadSessions()`，受控REST延迟150ms：第一条link top从116.80px变164.99px，结束后回116.80px（位移48.20px）。触发点是刷新时上方新增 `Loading conversations…`；现有列表本身仍在，不能描述成“列表被清空”。这是可复现的一个闪动来源，仍须覆盖用户Turn start/end链与标题动画/排序变化。Assistant UI不会自动消除App的这个业务刷新提示。

## 5. 缺口与首轮问题逐项映射

| 问题 | 框架直接解决 / 帮助 / 无关 | 本轮必须实际整改或补证 |
|---|---|---|
| V-R2-01 原file.attach合同扩展 | 无关 | 后端恢复原合同、新RPC名称/manifest，前端附件stage/stat/abort接线。框架AttachmentAdapter不修native API兼容、500MB传输或取消晚ACK；不应以“换附件组件”关题。 |
| V-R2-02 active Reply/Edit变Steer | 无关于事务；组件可呈现edit态 | 同一个primary selector和perform将edit事务优先，单红确认后走native busy interrupt→idle truncate，不走Steer/普通slash。Framework onEdit不是Hermes rewind。 |
| V-R2-03 edit后temporary/Pending错误 | 稳定ID组件有助生命周期；不能修边界 | 完整Timeline真实顺序投影后按durable target切除全部后续节点，目标前临时节点保留；exit恢复；接受提交时失效切除区及其在途结果。 |
| V-R2-04附件编辑正文污染 | 无关 | beginEdit复用既有author/body展示剥离，保真正附件occurrence；不修改原历史/model content。 |
| V-R2-05框架仅外壳 | **直接可解决结构缺口** | 正式页面实用framework消息/part和订阅；保既定design。不能仅增加另一Provider标签，必须使变化文本真正从其part/selector更新，回归F12。 |
| U-R2-01草稿Ctrl+Z | Input提供浏览器textarea基础、IME/focus；**不保证解决** | 真实键盘输入/替换/撤销/重做，检查DOM是否被重建及value写回、选区/异步恢复等。浏览器Ctrl和macOS Meta分别核；不能用fill()或jsdom键位mock冒原生undo。只撤草稿文本，不撤Rewind/附件/已提交消息。 |
| U-R2-02显示积压 | **有直接受控性能证据支持帮助** | 稳定对象+局部订阅+历史memo+按帧绘制，smooth=false；event逐条顺序reduce、terminal及时flush。实际正式入口下补event→state→DOM及Stop终态证据。 |
| U-R2-03侧栏边界闪动 | 无关 | 保已显示列表，刷新提示不增加列表高度；更新真实新建/标题/排序/错误恢复。上述48.2px反例供定向关闭，不通过取消刷新掩盖。 |
| C73 Usage成功数据可见 | 无关 | 当前Utilities本身不是active显示gate；readUsage L1489的active gate会抑制成功数据的发布/错误解除。修发布与可见性，而不是擅自改变计数口径；C54 active保最近completed统计、Latest Turn不等当前token段、unknown不伪造仍有效。 |
| C76 Slash Tab/统一换行 | trigger UI有帮助，**本地没有Tab开箱能力** | 继续native `complete.slash`/catalog。Tab仅补全文本；候选命令和description一个inline文字流，不用独立flex/grid文本盒；不能选中即自动执行命令/插directive，保Send原dispatch与IME/modal优先。 |
| U-R2-04 Instant Reminder源消息晚出现 | **若源event已到达且state有节点，渲染优化帮助；若源未到/未投影则无效** | 先分别测native落史/source通知、Gateway到达、Controller projection、DOM。Main已核 `session_notifications.py:282` admit_active_reminder→L290 _run_prompt_submit；`prompt_turn.py:1179–1180` 只发空payload message.start；对应前端reducer只改Turn active、不携带/渲染User源，sessionEventEffects在complete才finishHistory。正文/Thinking可先到，terminal/后续REST才把真实Reminder补齐。已核路径支持独立source可见性缺口，首消息durable UID发布hook仍待核，不宣布所有现场延迟的唯一根因。应在既有native persistence/observation接缝暴露真carrier UID/role/order并在Thinking前呈现；不能从schedule猜一条Reminder、换成Assistant或等终态排序补偿。 |

C73与C54并存：成功来源可见是显示/发布政策；Latest Turn仍是最近**完成**Turn，active时保留正确completed snapshot，不得把source变化导致的暂时null或任意新Assistant段当最新Turn。Main需在源契约内决定成功data与保留completed投影的合并，不写第二本地计数账。

U-R2-04是新增source可见性问题，不能被本报告33行history渲染对照或backend Stop约95ms证据关闭；也不能把它归为框架浅接入的必然结果。用户最新明确：WS持续连接、Thinking正常但慢，体验像播放离线动画、模型进度落后；这是P1真实进度要求。源码没有显式限速不反驳这种现场观察，验收必须量事件→状态→DOM、terminal最终可见延迟及是否持续积压。Main正在单独查native首消息源事件。

## 6. 接口影响、收益与成本

**无需改变的边界：** Controller及Hermes持有对话/Turn/Pending/Usage/Reminder事实；Assistant UI仅持有内存呈现结构。UID仍按Conversation限定，源role不由卡片kind改写；临时Notebook保持本地occurrence，Pending保持server receipt；压缩/rewind、replay/epoch、附件取消与unknown acceptance照旧业务owner。无新增模型、BFF、API、云服务或持久浏览器转录缓存。

**可量化的收益：** 在本受控负载，最终可见DOM延迟从约1.5–2.9秒降至约8–41ms；历史重复Markdown输入工作降约90%，突发绘制工作从203个整页commit减至4个按帧commit（普通React优化对照）。这是组合工程改善，不能宣传为库固定倍率。Assistant UI提供可复用的消息scope、part dispatch、局部selector和代码复制基础，减少这些通用机制的自写与后续维护；节省代码量/实施工时尚未测，不虚报百分比。

**成本：** 建立唯一stable render mapping，涵盖所有special kinds/metadata、真正的part状态、实例移除和原生UID；重新接安全link/image overrides和CSS容器/代码块，避免覆盖已定Mock；按帧绘制仅限渲染，保即时业务结果；补browser identity/undo/scroll/terminal证据。框架不能删除现有Hermes action/attachment/identity/replay逻辑，迁移Composer全过程反而扩大本轮风险。

**本地0.12限制：** readonly MessageProvider无原生Edit执行；部分最新helper不存在；默认Markdown平滑不适合本次吞吐要求。先用已有依赖做接线，不升级package/lock；未来若选最新by-ID/row APIs或虚拟化，需要独立审阅版本、差异、依赖和验收，不把upgrade当当前最低前置。

## 7. 建议后续动作与可 review 实施包（尚未实施）

1. Main先向用户交本结论，取得前端整改开始确认；本研究不自行进入实施。
2. P1真实进度包：在正式既有视觉组件内接MessageProvider/MessagePrimitive.Parts/selector，稳定转换/渲染对象，smooth=false，历史Markdown memo；加仅渲染的按帧合并及terminal flush。并由native source owner关闭U04首消息可见性缺口，两者证据分开。不能只关闭一条就称“流式进度已修”；不恢复旧index订阅列表，不新增虚拟化依赖。
3. 独立业务包：已审的Rewind事务/全Timeline边界/作者正文修复（V02–04），C73成功Usage可见，C76 Tab/统一换行，侧栏background refresh。每项修自己owner，不混入framework默认事务。之后的逻辑整改保持既有verification-fixes树；不操作用户另行新建的visual-polish树或其浏览器，视觉交回由Main集成。
4. Composer先保单一真实textarea实例/原生undo栈并修业务同步；是否进一步套ComposerPrimitive.Input由真实undo及action冲突测量决定，不以成熟库替代需证明的浏览器行为。原生catalog建议列表仍由Hermes来源生成；框架trigger只有实际帮助且不改变补全/执行语义时再用。
5. 定向关闭证据：active/idle Reply（button/Enter、text/file、取消/拒绝/busy）、完整临时/Pending边界与reload、不污染附件编辑正文；多工具live→durable 24→1→0/restore、paging prepend/compaction/rewind及跨Conversation；100event/s和burst的完整输出/真实terminal DOM及时；原生文字输入Undo/Redo；新建/标题/排序/start/end侧栏不位移；Usage cold/active/idle/错误后成功；Tab不提交/不执行，四视口slash文本统一流。
6. U04另查source→projection完整链；有真source通知则尽快按原位置呈现，没有则在原native接缝做最小增量。不得靠框架乐观消息或schedule模拟补齐。
7. Main集中亲审产品差异和接口影响后，统一安排必要检查/独立复审；本报告、采样数据和一项identity试验只作输入，不替代首轮未关闭项的正式关闭证据，也不重跑已有效模型/大包。

交回的实际产物：本报告；ignored `research-source-manifest.json`、`research-metrics-summary.json`、`library-identity-stream.json`、`library-identity-boundaries.json`。无产品文件、依赖或提交变化。
