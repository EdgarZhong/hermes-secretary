# Round 2 正式前端整改交接

2026-10-14，唯一前端逻辑 owner。实施包已完成；未提交、未部署，交 Main 集中 review / 集成。本文是开发定向证据，不替代独立 Verification / Validation。

## 1. 范围、基线和阅读契约

- 修复树：`/Users/edgar/code/hermes-secretary-web-verification-fixes`，`codex/round2-verification-fixes`，base `002f7a27fcf7313491f0301e143df7d3b6148088`。
- 原正式前端树只读作对照；未写用户 5173 树、visual-polish / visual-design 树、后端产品、依赖或 lock。只写获授权前端接缝、对应 tests、本报告及 ignored 证据。
- 已按派遣阅读 AGENTS / CLAUDE、executing-plans、autonomous-run 消息交接、snapshot-index / baseline / plan / verification §6、06 现行基础/Composer/Timeline/Usage/slash/Sidebar及验收、02 身份/源/消息和 Final invariants。当前 02 §5.6 L1544 起、Final L2516 起；06 Usage/slash 插入后的章节已按章节名核准，不沿用旧行号。
- 新 RPC 以 `repair-attachment-rpc.md §6` 为接口依据；U04 以 Main 已冻结的 `repair-instant-source.md §3`、生成合同和实际 native callback 为依据。未新建 Hermes Agent Loop、消息 owner、业务数据库、事务或模型路由。
- 研究报告 `repair-timeline-latency.md` 继续保存能力核实和官方 sources；不把框架能力研究本身当作缺陷关闭。

## 2. 实际实施与问题映射

| 要求 | 正式接线与行为 | 开发证据 / 边界 |
|---|---|---|
| V-R2-01 附件 | 小文件 `file.attach` 原样；大文件 `file.upload_chunk`；清理 `file.upload_abort {session_id,upload_id}`；体积读取 `file.attachment_info {session_id,path}`。不发 `abort_upload` / `metadata_only`。 | API 方法名、params 和大 chunk 失败/清理定向测试；真实后端大附件→Agent 由 Main 集成。 |
| V-R2-02–04 编辑 | 编辑 Send 先于 active Steer / slash；单次红确认；native busy → interrupt → idle → 同一提交点 rewind+send。全 Timeline 在目标前剪裁，包括后续 live / temporary；Pending 整体卸载，避免 exit buffer 继续显示。 | 实 Controller / CommandActions / App 的 active、idle、busy、拒绝、取消、附件原文及重复 occurrence 测试。 |
| 编辑接受 / 拒绝 | 只有 native streaming receipt 接受后，且在后续 await 前，退役被剪临时节点及在途结果 holder。后返回 notebook/help/alias 不能重锚。失败保编辑稿、恢复完整原视图；Exit 恢复原未提交草稿。 | 成功与拒绝真实 promise 屏障反例；generic alias 共用原 holder，不能重新 capture 新边界。 |
| V-R2-05 Assistant UI | 稳定 UID readonly MessageProvider、message selector、Parts、真实 native Text part scope、Markdown `smooth=false` 实际用于正式正文 / live Thinking / system。 | 实 App 混合 role、源和截断生命周期测试；短历史 24→1→0→33 浏览器无 index subscriber 白屏。 |
| U-R2-01 Undo | 保留真实 textarea；Ctrl Z/Y/Shift Z 调浏览器原生 undo/redo，成功才 preventDefault；Cmd 保持系统原生，IME 先阻断快捷键。无自造 undo 栈。 | Chrome 真逐字输入 + 8 次 historyUndo/historyRedo，DOM值和 Controller 草稿逐次一致；没有用 fill 冒称输入历史。 |
| U-R2-02 流滞后 | 历史正文 memo、稳定 node / options 引用；仅 React render snapshot 每帧通知，native state / 原 listeners / seq / reducer 同步逐事件执行。 | 100event/s 长增长 Markdown/代码/Thinking及突发；终态同步 flush，最终全量一致。具体数据见 §4。 |
| U-R2-03 Sidebar 刷新 | 已有列表后台刷新时不插 Loading notice，保原列表位置；初始空列表 Loading、真实错误、列表更新 / 标题 / 排序仍保留。 | 实 browser 后台刷新 true→false，第一项 top 始终 116.796875px。 |
| U-R2-04 首源消息 | `message.source_committed` 在现 history owner 一次并入；外层 runtime binding + 已证明 Conversation ref + 真 UID / row / boundary 校验；不要求 physical stored ID 等于旧 route。 | 实 App 在 source event 后、Thinking 前已见真 user；受控 WS 序号2消息可见、序号3 Thinking，终态1 UID；真实事务/模型链由 Main 补。 |
| C73 Usage | 每个成功返回都发布并清旧错误；active 已有 available 最近 completed 数值时保其统计值，更新 observed_at 等成功状态；首次 / unknown 使用原生结果，不自造计数。 | 正式 readUsage active 可见 / 清错误与既有 C54 最近 completed 保持测试。 |
| C76 Slash | Tab 仅补 catalog 候选文本，不执行 / Send；command 和 description 同一个 span inline 文字流。 | 实 ChatComposer 无 perform；四视口原生键盘 `/sta` → `/status`。 |
| C80 Sidebar Mock 恢复 | 真 last_active 秒值按本地 calendar Today / Yesterday / Previous7 / Previous30 / Older 排他分组；unknown 诚实。真 Appearance 包裹结构恢复第二分隔，原 footer 分隔保留。 | 边界单测与四视口正式页面；长标题/selected/title/主题/footer/移动抽屉保留，没有增加 Mock 描述标签。 |

## 3. Assistant UI 使用边界、源状态与时序

`App → Controller render subscription → projectMessage / projectTimelineNodes → stableTimelineNodes → UID-key MessageSlot → MessageProvider → useAuiState(message.metadata.custom.node) → MessagePrimitive.Parts → readonly NativeTextPart → MarkdownTextPrimitive smooth=false`。现 Composer / controller submit / scroll / history paging 接缝保留；外部 runtime 的 isRunning 仍来自原 native live.active。

本地安装实际版本为 react 0.12.28 / react-markdown 0.12.11 / core 0.1.17 / store 0.2.9 / tap 0.5.10。本地 ThreadPrimitive.Messages 使用 index key 与 MessageByIndexProvider，旧 F12 18/18 越界已有证据；这里 index=0 仅 readonly provider 信息，不拿它 lookup thread message。未冒用最新 main 才有的 by-ID / defer / rows 虚拟化能力，未加依赖。

MessageProvider 的本地 readonly part 默认 complete，因此 Text leaf 使用已安装 public tap resource / useAui / AuiProvider 显式提供只读 part 状态：running / constructing→running，failed / error→incomplete(error)，interrupted / cancelled→incomplete(cancelled)，unknown→incomplete(other)。assistant 顶层 message.status 同样取 native；user/system role 原样。真实 UID、source、时间和 native 状态存于 node metadata，业务控制从未读取框架默认 complete。resource 的写 tool result / resume 方法拒绝执行，不能变成新的执行 owner。框架强制 Date 的缺时 fallback 从不经 NodeTime 展示为原时间。

不用整个框架 Composer：它的默认 active 禁 Send、默认编辑 / queue 控制与 Hermes rewind+send、Steer、附件 occurrence、单确认不相等。保当前原生 textarea 与 native catalog / submit owner，Undo 用浏览器输入历史。scroll / paging / source anchor 继续由既有 design Timeline 管理；本地无开箱虚拟化且最新示例需外库/不稳定 API，本次没有替换滚动 owner。

RenderStore 只保一个 latest snapshot 和至多一个 RAF，没有按 token 补播队列。Controller.state 和原 subscribe listeners 每事件同步；仅 active 不变的 message/reasoning/thinking delta 延 render 通知。message.start、active 改变、terminal、route、draft、edit、源事件和其他控制默认立即 flush，并取消 pending frame。卸载最后 subscriber 时采用最后快照，避免再挂载读旧视图。

U04 消息只取冻结事件的实际 DB row，不从 Schedule、receipt、timestamp 或内容造 carrier。已证明 ref 和 source boundary 的当前尾前驱匹配才接入；同 UID 重播原位替换。压缩后 physical tip 是合法 locator，不与旧 root route 作相等门禁。unknown ref / predecessor 或 prefix/compression 改变走原 force history refetch，不猜排序。读请求开始后到达的新增 committed UID 在旧 REST 返回时保留，后续 REST 同 UID 的 canonical 行优先，pagination offset 包含保留行；没有另建 source cache。turn_id 不与前端 numeric segment counter 冒充同一身份。

## 4. 当前正式 App 性能实证

证据目录：`.hermes-dev/round2-verification/frontend-fixes/`；`source-manifest.json` 保存两个 actual src trees、HEAD、逐文件 SHA256 和 harness SHA256；`performance-summary.json` 汇总原始 `baseline-long-*.json` / `final-long-*.json`。最终 src aggregate `4732e19c90be8833df3b383d25633303398a75c1a39a2caed96fa9afff3406f5`，原基线 `d9893ca1e8c3dc80a87993c78b7ff670a86b65913465a9a7a8e170edf6868618`；交回前逐文件一致，非只看 HEAD。最终 props 改动后重新取得对应样本，旧有效样本另存 `pre-props-passing/`，不冒为终稿。

隔离 controlled API 5182 / Vite 5181，Chrome + Vite dev / React development，一次同负载对照。实际原 WSTransport / FanoutTransport、production Gateway parser / Controller event / projection / React App；仅原生外部初始化、history完成读取、Usage/Compaction结果受控。没有模型/真实 profile，也没有连接用户 53445 / 5173。history 复用33条真实现场取证，含约44k正文、23k reasoning和15工具；current-growing 另增加300个独立 Markdown标题/加粗段/代码块，或300个独立 Thinking段，避免短重复片段代表长流。

| 当前增长负载 | chars / events（含start/terminal） | 原实现 emit→state p95 | 当前 emit→state p95 | 原 terminal emit→DOM | 当前 terminal emit→DOM |
|---|---:|---:|---:|---:|---:|
| 带历史 Markdown/代码，100event/s | 54,984 / 302 | 4,717.78ms | 102.46ms | 5,182.47ms | 128.00ms |
| 带历史 Thinking，100event/s | 31,692 / 302 | 2,815.91ms | 40.87ms | 3,093.73ms | 44.18ms |
| 带历史 Markdown/代码，突发240 | 43,944 / 242 | 5,302.61ms | 93.48ms | 5,715.48ms | 159.16ms |
| 空历史 Markdown/代码，100event/s | 54,984 / 302 | 1,686.30ms | 81.02ms | 2,019.23ms | 215.06ms |

所有有效样本 seq 完整且各唯一；Controller 原始累计字符串逐字等于源 chunks join；DOM 的完整可见文字（排除 Markdown 语法并规范化空白）逐段、顺序、全量一致；terminal active=false / receiving=0，修后 native state 为 interrupted，part selector真实状态另见视觉自审定向测试（正式DOM不加取证wrapper）。第一/最后 terminal DOM mutation 的长度相同，terminal 后150ms观察没有继续补播文字。突发 React Profiler commits 244→14；100event/s 的 commits 不一定减少（含 leaf / entrance 更新），收益不能归为整库固定倍率。DOM 证据来自 MutationObserver，不是屏幕 paint；emit/state跨进程时间使用本机 wall clock，单次 dev 结果不是SLA，也不证明任意无限长段无成本。

异常采样完整保留：首次 metadata.steps 被错误放入 user/system 造成 App error 已修，并由混合 role 正式测试覆盖（`initial-metadata-failure/`）；300瞬时事件触发原生 Fanout 256 backlog detach（`invalid-transport-backlog/`），其 burst / 后续empty无效，不把断连误算渲染性能。改为仍约44k的240突发后完整通过。最初多采样连接争抢 controlled peer 的旧 baseline 不用于最终表。新 API 原用5180，Main指出与用户 Mock分配冲突后核实只停本人 PID，迁5182；未停用户页/服务。

## 5. 定向验证记录与浏览器证据

- `development-tests.log`：Controller / Timeline / fixes / attachment 第一包108通过、2大chunk旧 mock失败。修改真实新 RPC mock，并把依赖执行顺序的 FileReader fixture 移到 beforeAll；`chunk-retest-fixture.log` 2通过/58 skip。失败原日志保留，不改断言或门禁。
- `formal-smoke-retest.log`：edit / Usage / App 定向12通过/59 skip。
- `current-source-tests.log`：新增 source 与现 Timeline/fixes 48通过、1测试 fixture缺 next_idle 失败；补完整 DTO fixture 后 `source-retest.log` 2通过/12 skip（正式源顺序与负反例）。
- `props-source-retest.log`：最终纯props接缝的 formal App、source、短历史生命周期3通过/46 skip。无需复跑未改变的整个包。
- typecheck 的 UUID 参数和测试 mock返回类型错误均保留原日志后修；`typecheck-final-complete.log` 通过。`build-visual-final.log` 为视觉包裹修正后的最终 source `tsc -b && vite build` 成功，6.45s；常规大 chunk warning仍记录，未调阈值/关闭检查。早一份 `build-final.log` / `build-props-final.log` 不冒作最终视觉修正版本。
- `browser-undo-native.json`：真实逐字输入、8次 native historyUndo/historyRedo、每次DOM value=controller draft，未用 fill。
- `browser-{1440x900,1024x768,390x844,320x568}.json`：实际 iframe viewport隔离，避免改用户整浏览器尺寸；四处 slash command+description 单span且无横向overflow，Tab `/sta`→`/status`（CUA实键盘），两条1px分隔。宽视口刷新busy=true/false首项top都116.796875px、无Loading文字；mobile hidden desktop首项top=0不能冒作抽屉位置测量，实际移动dialog六组/Files/Appearance已从DOM核实，Open/Close用原生键盘入口。iframe坐标 click未起效的取证改用原生 Enter，不改产品冒称通过。
- `fixes-identity-boundaries.json`：24→1→0→33，Timeline一直存在、无F12 index生命周期白屏；没有依数值造 UID。
- `browser-source-committed.json`：production Gateway/Controller/App受控 WS 事件，首次含 committed source 的DOM snapshot seq=2；Thinking seq=3、complete seq=4；UID最终一次，原user位置在Thinking前。这证明前端接线，**不是**后端DB COMMIT/实际模型证据，后者由 backend native-source report / Main集成提供。
- `git diff --check` 通过；Controller正好2000行，新增源/编辑纯投影 helper保持单owner，未加依赖 / lock / 自造测试规则。

### 用户视觉保护专项自审（恢复指令后完成）

用户澄清“停手”是禁止改掉既有视觉，Main恢复原授权并要求中层/地基接入。**发现并修了一处确实误改**：我此前在 MessageText 增加取证div，且 MarkdownTextPrimitive 本地默认又有div，使 `.hs-prose > :first/last-child` 与 disclosure直接子元素margin规则不再落到原段落/标题。现删取证div，primitive container改无DOM Fragment；不用 `display:contents` 等样式补丁，原 h/p/pre 直接DOM结构恢复，框架scope/provider/Parts本身无DOM。

`visual-scope-retest.log`：实际 Timeline / App / source / 短历史4通过、46 skip；测试用真实 custom paragraph renderer读 useAuiState(part.status)，五种native状态确实分别 running / incomplete:error / incomplete:cancelled / incomplete:other / complete，不再拿data属性冒为框架状态证明。DOM直接H1/P/PRE、code.language-ts、无wrapper / 代码标题 / 按钮。`browser-markdown-dom-audit.json`为Chrome实际最终长流正文：直接首H3、末PRE，首marginTop=0px、末marginBottom=0px，wrapper=0、code buttons=0。最终对应长流样本重新采集，旧有wrapper性能样本保留`pre-visual-wrapper-fix/`，表内是修后当前版本。

| 自审区域 | 差异及依据 |
|---|---|
| design layout/chat/primitives/tokens、主题组件、Welcome/Orb/卡片/附件/滚动/动效 | 产品文件均未改，既有design components / classes / props及entrance hooks继续使用；没有框架默认UI替代。 |
| Markdown wrapper / pre / code / codehead / stylesheet | wrapper误改已恢复；本地DefaultPre/Code是原pre/code，DefaultCodeHeader=null，DefaultCodeBlock为Fragment；没有SyntaxHighlighter外观或copy按钮，没有dot.css或其他框架stylesheet导入；安全a/img和GFM语义原样。 |
| Sidebar JSX | 继续既有Sidebar/Section/Item和原链接/title/selected/ThemeSelector，只接用户C80互斥更新时间分组、无列表Loading跳位、真实Appearance分隔结构；不是侧栏重设计。 |
| Composer JSX / CSS | 既有Composer / Textarea / PrimaryAction / Button原样；仅用户C76候选正文与description合一span文本流，C80分隔所需结构。theme.css只有这两条接缝规则，不改tokens/尺寸/字体/颜色/动效。 |
| 用户视觉工作区 | 仅read-only核：visual-polish当前clean、HEAD002f7a2；visual-design HEADfc18614及其已有截图，不写/合并/回滚。这里不冒称已接收未知或未交回的最新用户视觉成果；Main后续按其实际交回纯props接线。 |

## 6. 已知边界、风险与未覆盖

本实施开发范围内无已知未修阻断。真实附件RPC→模型、Instant实际COMMIT→provider→浏览器和用户实际长运行仍需Main统一集成；不以本报告宣告独立门禁通过。IAB本工具环境不可用，inventory只有Chrome；未以Chrome iframe冒称IAB、移动真机或跨浏览器覆盖。旧有效Undo不重复。

当前 MarkdownText 仍会解析累计当前段；54k当前段可接受的实证不能证明无限增长恒定成本。帧合并不是速度上限，只跳过中间 render快照；后台tab RAF暂停时控制/terminal仍即时通知，但浏览器后台paint本身不受本代码保证。仍保原滚动/历史 paging，未新增 virtualization或另一个scroll owner。

U04 unknown源边界必须refetch，不能保证未知identity/prefix时在网络读取前先渲染源消息；这是冻结安全边界，不能靠内容/时间猜测补偿。完整source载入后的同UID模型场景由Main检查。未自动增范围改变 C54 Usage统计刷新语义；未把框架当作Hermes事务修复工具。

## 7. Main 集成交接

实际变更：App.tsx；api/attachments.ts及test；ChatComposer.tsx；core/controller.ts、controller.test.ts、command-actions.ts、projection.ts；新增 core/message-render.tsx、render-store.ts、session-groups.ts、verification-fixes.test.tsx；theme.css仅两条接缝规则。全部在授权修复树，未提交。Main集中检查 formal接线、源proof/跨owner、edit接受/拒绝、Usage与现后端接口后统一集成，独立门禁按本轮统一计划安排；不用重复已有效的大包和Undo。

后续用户视觉树合并时只协调两处实际接缝（Sidebar grouping/Appearance分隔、slash inline span），不回滚整树或覆盖用户视觉。5181/5182为本人取证服务，可按ignored serve.mjs/server.py重启；交回时仅关闭本人监听和agent临时tab，原研究服务/用户service不碰。报告、ignored原始证据和源码manifest共同交回，不修改全局看板/冻结规格/verification。


## 8. Main亲审与集成微修（2026-10-14）

Main已亲读App、MessageProvider/Parts/leaf真实status、RenderStore、完整source/history reconciliation、edit cutoff/temporary退休/作者附件正文、三新RPC与两条CSS接缝，核对上下游原生source合同及视觉保护；接收开发包，未宣告独立门禁通过。发现readUsage active时会无条件用previous覆盖新available数据，违反C73，已微修为仅new session_total unknown时保留previous有效总计；new latest_completed_turn存在则采用新值，否则保留最近完成轮。无本地累计，无显示当前未完成轮。Controller仍2000行。

在已有真实测试基础上仅扩充既有Usage行为用例：证明active中随后正常取得新值会发布；单worker `npm test -- src/core/verification-fixes.test.tsx --maxWorkers=1 --no-file-parallelism -t 'successful Usage'` 1通过/13跳过，500ms。`npm run build` 通过（含tsc），Vite5.37s，既有大chunk警告保留；没有重新跑Undo、性能或完整包。新日志见`.hermes-dev/round2-verification/prompt-main-final/usage-integration-test.log`和`frontend-integration-build.log`。旧有效性能/视觉证据版本不冒充新source完全相等；render/App/CSS机制未改，Usage微修的当前行为及构建由本次定向证据覆盖。

旧owner实际附件补证交回：live-integration-20261014里原生2片4,194,400bytes/stat/存储SHA/abort，正式Send真实DeepSeek正确读出size与首尾marker；runtime85c42a4c、terminal Assistant UID b372e58c519f4991a221b1c161b7bf46。Main待native_integration接收其日志/DB与manifest；不重做附件模型链。旧Chrome证据保留历史，但用户最新IAB-only不能由它替代。53449/5183旧owner已停止；新的真实Instant/Noting/IAB代表链由native_integration续接，重任务单执行方。


## 8. native_integration 新 Owner 续接实际联调

2026-10-14，新Owner不修改上文旧Owner证据。准备与真实串行补证完整见[repair-native-integration](repair-native-integration.md) §1–8及ignored `native-integration/`。

旧live-integration附件新RPC上传/stat/SHA/abort和真实DeepSeek首尾读取直接复用，没有重新运行。当前IAB实际提供且隐藏tab1可用，旧报告“只有Chrome”仅属旧环境。本次两个正式用户Send→当前最小Prompt三个自然Noting任务→自然Instant原生source/模型/真实DOM→done→schedule_update代码自动回pending，已取得同链身份/DB/seq/模型生成tool requests/DOM证据。source UID79b58919db1a49398fd4d62556158e02,row27,seq153；源DOM21ms/Thinkingseq157；completeseq313/DOM15ms、源唯一、receiving0。Snapshot和同lineage同Registry重新排期见新报告。

本Owner曾误判Reminder内timestamp为缺陷；用户最新纠正要求保留内部timestamp，Main临时隐藏修补与三测试已撤回，不能列缺陷或隐藏成功条件。原真实beforeFix证据复用；本次没有证明Instant默认折叠，已显眼交Main判断最新口径范围，不冒称通过。没有动用户Chrome/5173/53445/视觉树，未测试/build/大包/Undo/性能复跑，未启动Verification/Validation。自有PID/tab/observer最终清理及当前源hash在新报告后续段记录。

最终资源已交回：自有IAB tab1关闭，Node95453/Python94660仅核属本人后SIGTERM，两exec exit143、53449/5183无监听；详见新报告§9。旧unfinished child原生只读是unknown/tasks[]，无live任务，未擅自修DB。

Main随后按C99将Instant接入既有foldable/FoldedMessageBody，原timestamp保留；本Owner此时服务和页已关闭，最新默认折叠/展开IAB复验转Main，仅用既有真实row，不重跑自然Instant或模型。

C99最后IAB复验尝试受接口阻塞：本次inventory仅Chrome、createBrowserTab(iab)不可用，未造页/模型或绕用真实浏览器。自有隔离全局off防overdue后启动的11773/11805及两frontend子进程已清理、无listener，config字节恢复且DB counts/Registry/真实source row前后相等。新默认折叠IAB仍未执行，交Main在可用环境仅验已有row；证据/源hash在native-integration/c99-result.json，新报告§10。

C99最终由Main接任浏览器、Owner仅管全局off隔离服务；两个HTTP200后Main IAB绑定被Browser安全策略明确拒绝，按禁止workaround立即收尾，最后默认折叠/展开IAB未执行。自有15149/15179与两子进程均退出、无listener，config逐字节恢复，DB counts/Registry/source/API call_count全相等零新模型；详新报告§11和c99-main-result.json。原queued内置临时页未可控绑定，按排队未显示保留待正常UI处理，不用替代surface关闭。旧自然Instant实证及2组件/build有效，不冒称最后实看通过。


### Main最终接线：C99与开发HMR（2026-10-14）

C99用户明确Reminder默认折叠、内部timestamp保留；Main撤回所有临时strip改动/断言，复用既有FoldedMessageBody仅将instant加入foldable条件，无新wrapper/CSS/源数据变更。正式Timeline两个kind用例2pass/36skip（956ms），展开可见原timestamp；build（含tsc）pass，Vite5.15s。真实最后IAB实看被浏览器策略拒绝，报告边界见native-integration §11，未改真实Chrome或使用底层旁路。

Main随后亲审发现此前HMR同owner Object.setPrototypeOf会保留旧实例，但新增renderStore/subscribeRender/getRenderSnapshot实例字段不会自动初始化。改同owner惰性renderStore getter/public subscription getters，保持旧gateway/history/draft且不创建第二Controller；controller仍2000行。新旧shape行为+Usage2pass/13skip（497ms），原同步event/按帧render/控制terminal flush专例1pass/14skip（453ms）；当前build pass，日志hmr-render-owner-{test,build}.log、hmr-render-flow-test.log。先前性能样本中App/Parts/Markdown/RenderStore机制未变；不把早一份完整manifest冒充最终Controller byte-identical，也不重复整套。

UI阶段提交0f8d891已由post-commit自动推feature upstream并ff main/push origin/secretary；随后HMR提交8b3867e同流程。主仓库hooks配置保持原样，仅安装post-commit；云端同步不等于独立门禁通过。


## Main最新侧栏截图补修与文案撤回（2026-10-14，C102–104）

用户截图暴露之前C80新增全宽appearance wrapper后，原Mock footer grid item的内容收缩约束丢失。不是ThemeSelector本体差异：原fc18614 Mock直挂footer、footer有grid/justify-items:start；正式wrapper使控件按block自动拉满。sidebar_visual_restore只在theme.css wrapper补display:grid/justify-items:start，43795c8自动推。Main正式5173 IAB实看：胶囊112×44、三按钮34×34且dark被选中、footer与appearance两border均1px，截图/读数在ignored native-integration/sidebar-visual-restore*.png/.json。

用户随后指出文案遗漏，子Agent按fc18614/002f7a2最后Mock源码暂时恢复Adjust visual style（bb66da4），Main整块实看12px/16.8px行高、gap12、胶囊112×44；r10旧未跟踪截图文本不同，不冒称最后代码依据。用户最新明确“算了，不要文案了，你赶紧专注于交会你的原目标”，精确撤回标签及其字号/新增gap，保宽度修复。最终2c019acfa34c0383e3c86e22c1b22871f8f1d73d与43795c8树diff为空，可复用同树正式IAB证据，不再重复构建或页面操作。阶段一次build、追加标签一次typecheck通过；最终diff检查通过，自动push后远端一致。原用户视觉树未修改，业务/控制器/API未改。此次补修不构成独立Verification/Validation。
