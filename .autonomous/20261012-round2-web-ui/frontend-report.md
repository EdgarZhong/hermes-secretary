# 前端 Development 阶段报告

## T2 / 不依赖 A 的原生基础阶段（2026-10-12）

**状态：可供 Main 集中 review；未声明 Web V1 完成。** 前端 `/Users/edgar/code/hermes-secretary-web`，本地 main、无提交/远端。依据冻结 `37ad76f5df` 的 06 全文、所派 02 精确章节、Snapshot/plan 与 native-compatibility 实际 DTO。未修改后端产品、规格、核心看板、其他报告、私人 Pi 库；过程仅本报告与 ignored frontend 证据。

1. **对应条款**：06 §0.3–0.5 direct REST/WS 与持久 allowlist；§1.2–1.7 三主 route、首次 singleflight、分页/流/真实载体、Composer、草稿二进制、延迟 type-specific attachment；§1.8/1.10 primary matrix/Cancel；§1.11 Rewind 双确认/刷新退 armed；§1.12 native catalog 分流；§1.13 unknown usage；§1.16 Files read；§3.1–3.6 native mapping/replay/auth；§4.2 mandatory stack/design 正式接入。T3a 基于 pending-implementation 精确接口已写 client orchestration，尚无真实 A 验收。
2. **实际改动**：React/Vite/TypeScript 与 npm lock；assistant-ui external runtime、ThreadPrimitive.Messages 为正式 Timeline 基础；实际 shadcn 风格 Slot/CVA Button、Radix presentational design、Tailwind preflight；共享 src/design 由设计师提供，业务零改动。独立 api client/types；Controller 内存 binding/history/live/cursor/singleflight；IndexedDB 仅 draft；URL history 与 sparse local route/scroll。Files 真实 default/list/text/media/download（download auth fetch→Blob），无写操作。真实 wrapper/raw compaction classification、思考/工具 disclosure；Draft blobs 延迟 RPC 与 occurrence IDs；原生 submit/stop/rewind 参数，忙碌 rewind interrupt+wait 后保持 cut；服务器 approval/clarify 当前 native 请求有可回答 modal。Model actual config.set syntax，Reasoning 使用 Hermes 配置合法档位并告知 backend clamp，actual info 回读。
3. **正式路径**：App→共享 AppFrame/TopNav/Sidebar/Composer→Controller→原生 `/api/sessions` 与 `/api/fs/*` / `/api/ws`；首次 Send `session.create(idempotency_key,cwd from native)`→同 runtime 各 `file.attach`/`image.attach_bytes`→`prompt.submit`；Send admission 不等 Turn completion。New Chat 页/草稿、Files 读操作不调用 create。运行时映射只内存，换 route 不 interrupt。开发 Vite HTML transform 仅从原生 `/`提取 bootstrap token，REST header/WS token，token不输出日志或保存；最终 build 可交 native HERMES_WEB_DIST 托管。Vite在 `http://127.0.0.1:5173`，目标 `http://127.0.0.1:53445`。
4. **验证**：25 项 Vitest 契约通过，覆盖 matrix、源 UID/wrapper/timestamp 不改源、native hidden/composite compaction、tool complete 非 Turn complete、跨 rotation dedup、同文 occurrence、IndexedDB 文本+重复名不同Blob隔离、route/slash。tsc 与 Vite build 通过（完整 build/unit 日志 ignored）；首次 npm 宽范围 store 导致真实 build missing exports，已通过 pin `@assistant-ui/store=0.2.9`/tap0.5.10 修复，失败未冒称通过。实际 REST read HTTP200、0 sessions、WS gateway.ready、reasoning medium；model.options 命中原生5098 checkout版本保护，未关闭保护。内置 cua_repl 冒烟：New Chat填未提交草稿→Files真实目录→source-checks子目录→右上Back to Chat→reload恢复原文本；列表仍无会话；无模型提交；console error/warn=[]；截图 `frontend/core-smoke.png`。浏览器tab已关闭释放，四视口尚未验收。
5. **真实缺口**：A Secretary/Notebook/compaction state+cancel/usage_detail 精确DTO仍待owner交回；当前不得调用原持久 `/notebook`冒充临时结果。T3a协议已接但未真实服务验证；current turn starting无turn_id时仍须显式拒绝Steer。Main需统一注册、快照、重启53445再跑核心真实模型链路及A联调。重连 known-watermark 采用先park/replay/seq去重/flush策略；truncated/epoch时REST+snapshot重构的边界仍需真实受控验证，原生没有snapshot+seq原子cut。历史 tool/result/sidecar与accepted/terminal同步需真实大量历史/中断/旋转取证。附件暂代码选择16MiB/file **仅实施候选**，实际 transport/模型可读性未测、未宣称有效cap；需Main登记影响后实测并冻结最终V1选择。真实图/PDF/file、camera/IME、Cancel上传竞态、Rewind原生权限、四视口、security及快切session未完成。
6. **接口影响**：不改任何后端原生method/DTO；只新增独立 browser client；A方法名严格 native-compatibility §11，receipt形状来自owner报告。认证是开发静态 hosting基础设施，非业务BFF。能力失败/缺字段呈unknown/error；Latest Turn暂unknown、Session Turns不以calls代替；无client token估算。没有持久API缓存/Notebook/turn ledger。
7. **建议下一步**：Main review本阶段上下游，统一接线A/运行源码重启；本Agent继续T3/T4精确接口接入和定向Controller/receipt测试，再做真实输入到输出开发取证。核心真实流水与附件 cap取证后交完整前端阶段；设计师四视口打磨接续统一viewport；独立门禁不由此报告代替。

## 证据入口

- `.hermes-dev/round2-evidence/frontend/unit.log`、`build.log`：当前有效定向自动化与构建。
- `.hermes-dev/round2-evidence/frontend/native-read.json`：真实原生读/RPC结果，含5098与首次证据脚本commands.catalog误带explicit_only的4000失败（生产client未带；下一阶段脚本修复）。无token。
- `.hermes-dev/round2-evidence/frontend/core-smoke.png`：实际共享组件接线后的New Chat/草稿截图。
- `.hermes-dev/round2-evidence/frontend/source-manifest.json`：本阶段前端文件哈希，供Main/门禁定位；工作区后续修改不冒充此阶段同版本。

## T2–T4 整改与可冻结阶段（2026-10-12 21:45）

**状态：产品文件暂冻结，供 Main 集中 review/真实失败面复验与阶段快照；不是 Web V1 完成交付。** 本节取代前节对当前实现的描述，前节保留为历史证据。未 stage/commit/push；未修改后端产品/PM/规格/根看板。Mock Agent 新白名单未触碰。当前源码哈希见 `frontend/source-manifest.json`，源健康/67 定向测试/build/audit 同目录。

### 1. 对应条款与整改覆盖

对应冻结06 §0.3–0.5、§1.2–1.16、§2.2–2.8、§3及§4；02身份/原生 Foreground事实、Rewind/Compaction、只读Notebook/Memo、消息时间及正式接线章节；本轮已确认C09–C18按Snapshot Index消费。F01–F13逐项情况如下，实施/受控验证与真实验收明确分开：

| 项 | 当前机制与证据 | 仍需 Main/独立验收 |
|---|---|---|
| F01 ACK归属 | Send tx捕获owner、完整draft和revision；acceptedDraft只删除被接受的文本/附件occurrence，保留新编辑和新设置。Steer延迟ACK、Withdraw离开后ACK写回原owner，不取当前B数据；统一retainOwner生命周期。production Controller延迟请求切路测试通过 | 多客户端/真实慢ACK与断线场景 |
| F02历史/replay | refresh保留已加载范围、按UID/row identity更新载体；older/latest同owner串行及generation；activate缺running维持unknown；replay finally必flush/release。terminal只按真实persisted_turn row_ids退休该终态已有live节点，不清下一Turn | 原生无snapshot+seq原子cut，cold/truncated/epoch与分页/旋转交错的真实受控场景仍缺；pre-binding buffer400条边界未实测 |
| F03 slash | Composer action先统一parse/catalog路由再busy Steer；/stop、/notebook走正式功能；new/reset仅Web NewChat导航，带参数明确不支持，未静默吞参；其它command.exec结果标command而非Notebook。Controller延迟config命令仅消费原owner文本；/stop先于busy Steer测试通过 | 各native command真实结果/失败、极短starting状态；当前stop失败可能仍消费已输入/stop文本（保留error提示，待补正确消耗语义） |
| F04附件 | Files入口保持file，Photos/Camera为image，paste/drop按实际MIME/扩展名分流。真实refs/inline_images恢复chips/图片与Edit附件；occurrence IDs保重名。所有图先file.attach取得真实路径，submit_idle携本次ordered image_paths，不碰shared image staging。取消后迟到file ACK不submit/夹图测试通过 | 单16MiB候选尚待实际transport边界/超限/unknown/取消实测；Main真实图、PDF+JSON链路已运行，其完整结果由Main证据归属；相机/软键盘真机未验 |
| F05首次unknown | tx存真实stored locator；inspect activate/REST而不重发，不以相同inflight文本猜accepted。unknown从New迁移到真实stored路由/草稿，释放新草稿空间，实际unknown保留；无凭空success/补偿Prompt。lostACK/打开实际route测试通过 | 无后端submission ledger，丢ACK不能无条件证明接受；需真实断线终态人工核对的完整恢复交互 |
| F06真实投影 | 原生source UID与physical row_id分开；native tool_calls/name/args/result失败标记、thinking sidecar、system独立Notice；compaction raw marker/combined realText识别，UID carrier更新不按同文去重；Reasoning只从真实model capability/config schema取合法选项 | 历史大样本/冷恢复tool名称与reasoning来源、真实压缩后carrier/旋转完整验收未完成；snapshot流文本与多段历史的冷重建仍需实证 |
| F07 Files恢复 | Retry真实重新fetch；root默认cwd、规范化路径及服务返回canonical path均校边界；深链越界明确拒绝；真实相对面包屑点击上行；缺失chat先REST验证，fallback New保原草稿，不触resume | 真实权限/消失文件/目标/symlink及深层Back to Chat错误恢复 |
| F08 idle Send | 正式Send/Rewind改prompt.submit_idle，busy4009明确保草稿，无旧queue/steer/redirect fallback；5xxx/-32603/lostACK提交阶段为unknown。生产Controller拒绝/unknown/不重发测试通过 | Main新后端已加载；真实跨client竞争/保草稿场景需运行（后端机制证据由Core报告归属） |
| F09 bounded lifetime | 统一releaseInactiveViews只留当前可见binding/history/live、实际replay/在途tx；已离开可原生恢复投影释放，回看REST重建；draftscope registry只内存、真实conversation_ref安全迁移，不覆盖更晚草稿；连续十会话/回来恢复测试通过 | unresolved Send/Steer保留其必要owner/operation元数据与draft直到明确处理，不能把unknown静默删除；这里上界是实际未决操作数而非固定全局容量，需Main确认是否足以满足架构条款；没有持久API registry/responsecache |
| F10成熟预览/面包屑 | 正式auth fetch→File→懒加载@file-viewer3.1.2 lite+PDF/Word/Spreadsheet/PPTX，本地renderer assets，filename/MIME保真，文本wrap/MD渲染与HTML安全选项；File/URL/worker随卸载释放，download保留原生鉴权路径；真实root basename/目录/文件名，无人工Parent folder标签 | 本子Agent无iab可用，未能实际逐格式点击验收；提供18个真实合成格式fixture与场景给Main，支持宣称仅库/API接线，不冒称逐格式通过；大文件/库error与安全HTML动态取证仍缺 |
| F11逐卡生命周期 | 原生没有thinking.end；正文delta/interim、tool.generating/start为上一thinking段完成边界，只封running thinking；tool.complete严格匹配tool_id，不结束其它call或Turn。终态工具/思考独立折叠，用户终态重新展开保持；连续多个工具/失败/段边界及React交互测试通过 | Main正在真实多工具动态复验 |
| F12白屏 | 移除ThreadPrimitive.Messages内建index订阅与NodeMessage的index selector，React列表以稳定node.id和直接props呈现；仍正式使用assistant-ui external-store runtime/Thread.Root，无error boundary遮蔽根因 | 真正external runtime+ReactDOM连续四轮24 live→1 durable反例通过，Main真实终态替换复验中 |
| F13重复chips | nativeReferences只解析原生输入prefix，不把追加Attached Context/Context Warnings里的ref再次计数；保留用户真正重复引用/重名occurrence。对应双附件反例测试通过 | Main真实同会话PDF/JSON刷新前后定向复验；当前附加上下文正文仍保留原文，未未经确认隐藏 |

### 2. 实际改动

产品正式接线分成 `api/`、`core/`、`components/` 与既有纯props `design/`。Controller统一draft归属、transactions、binding/history/replay所有权；草稿仅IndexedDB，localStorage仅route/scroll/theme选择，不存响应、Notebook、usage、runtime mapping。稳定模型标题仅新草稿内存createKey轮换六句已确认标题；无subtitle。用户原图仅favicon及Welcome标题左侧。

C14唯一ThemePreference owner存system/light/dark选择，原生matchMedia派生实际主题，html dataset/color-scheme反映有效结果；系统改变仅system模式跟随、手动模式不变，重载测试通过。Sidebar/移动drawer共享同状态ThemeSelector。C16 NewChat没有Usage/Context，实际Conversation保留两scope与全部五指标/Context展开和压缩取消。Usage来源详情Popover为Info IconButton、align=start；未引入收起全部统计的额外交互。配色遵循用户后续另委派，无新视觉重设计；design仅本阶段必要预览容器/真实breadcrumb root accent接缝。

Files依赖精确3.1.2、Apache2.0原包，React peer17–19，安装lite与四文档renderer，没有full/CAD。真实npm审计发现DOMPurify3.4.15低危问题，正常npm override至3.4.17，现0漏洞。库Markdown用DOMPurify片段、HTML静态sandbox无脚本；源检查不是浏览器安全通过。Vite按renderer分块、9组本地assets；主包约674KiB，PDF754KiB、表格625KiB、HEIC1.35MiB等按需chunk，构建体积提示保留未调门槛；JSZip stream browser外置警告需实际Office预览确认。

### 3. 正式路径与接口

- Send/Rewind：原生session.create/activate/resume→各file.attach（上传发生在Send后）→prompt.submit_idle `{session_id,profile,text,image_paths,...原生truncate双确认字段}`。图片不是普通file ref_text，不再image.attach_bytes/attach/detach；lost ACK只可能普通文件残留，不产生共享latent图片。重复图片路径及顺序保留。busy4009不queue，不猜success。
- Pending：session.steer_pending_snapshot / steer_pending / steer_withdraw / interrupt_pending / interrupt_pending_status，沿真实turn_id+operation_id；stopping/dispatching需查询到明确终态，unknown不盲重发；Withdraw仅首次withdrawn text回草稿。
- 只读：secretary.state/notebook_read `{stored_session_id,profile}`，launch显式`''`，不改default。真实profile_home只内存匹配secretary.changed invalidation。Notebook只临时human输出，Memo两层readonly，Orb由global_enabled驱动。session.compaction_state/cancel只影响压缩；session.usage_detail真实nested availability/source，Session turns不冒native model_calls，最新完成Turn不以客户端差分补。
- Files：原生/api/fs/default-cwd、list、read-text、download；下载X-Hermes-Session-Token鉴权fetch→Blob/File，库没有token、私有URL或第三方Office外发。preview bounded native text以truncated提示，binary/media/full文档实际auth File。
- 原生REST/WS token只内存开发HTMLbootstrap/原生dist注入；没有BFF/新模型层/旁路Dashboard。

纯文件预览可复用接口：`src/components/FileViewerPreview.tsx` default `({file: File, theme: 'light'|'dark'})`；无API/Controller/存储/主题读取，Mock可传合成File。父层负责Suspense/错误fallback、File获取和实际theme。Vite必须加载同版fileViewerRenderers `{preset:'lite',formats:['pdf','docx','xlsx','pptx'],inject:false,chunkStrategy:'renderer',copyAssets:{baseDir:'file-viewer'}}`，该组件注册virtual:file-viewer-renderers，不能只import后缺worker assets。

### 4. 验证结果

当前本Owner定向4文件 **67测试通过**（contracts/controller/theme/timeline），不是Mock测试计数；完整日志`frontend/unit.log`。生产Controller测试用延迟正式request与真实IndexedDB，不镜像被测机制；React测试用真正assistant-ui external-store/runtime及ReactDOMact。TypeScript与Vitebuild通过，build日志保留提示；npm audit0。先前一次顺带运行全src为85测试包含他人Mock，不作为本Owner67证据。未跑Python/全量门禁、未重复Core已交机制测试。

只读TS AST健康扫描：除`adoptDraftScope`为22分支需非语义拆分，其余本Owner新函数≤20、≤300行、嵌套≤6，文件≤2000；**该项未写成全通过**。Main正在真实UI验证要求产品暂冻结，因此当前不引入HMR，待协调解除后修复再更新哈希/定向结果。

实际浏览器：此前T2 core-smoke是已运行基础route/draft证据；当前本子Agentcua.getState只返回Chromeextension，createBrowserTab('iab')报Browser not available: iab，按Main要求没有fallbackChrome、没有操作Main viewport。当前浏览器占用为Main，子Agent无活跃页面/视口。四viewport和预览逐格式不能冒称已验。

真实格式fixture在获授权 `.hermes-dev/round2-runtime/preview-fixtures/`，SHA/bytes见 `frontend/preview-fixtures.json`；文本/Markdown/JSON/YAML/Python/CSV/安全HTML、PNG/JPG、PDF、DOCX、XLSX、PPTX、WAV、MP4、unsupported.bin和nested.md，生成器在ignored frontend evidence。内容为red rectangle/blue circle/42、表格及短音视频，没有真实用户资料。Main点击场景：Files→preview-fixtures→逐文件（MD标题/表、长行wrap、JSON/YAML/code、CSV表、图形、PDF/Office同内容、音/视频）→各级真实breadcrumb→Back to Chat；system/light/dark与reload；safe.html不执行标记脚本；unsupported明确退路；下载原始文件类型/内容。库支持范围不能代替这些实际结果。

### 5. 缺口与风险

按上表真实验收缺口继续；主要是cold/replay/epoch/旋转确定性、16MiB实际transport边界和unknown、真实Rewind/compaction/carrier/only-own-cancel、Office/媒体预览错误与安全HTML、四viewport和真机专项。Main真实Main/Noting/图片/PDF/withdraw/Interrupt证据归Main，不自行改写其结论。必须优先完成健康拆分与Main三失败面复验，后续独立Verification/Validation按本轮冻结口径判断。

### 6. 接口影响

前端只消费Main/Core已锁定的additive A及idle-only/image_paths契约；没有后端产品改动。shared design公开props基本不变，新增纯File wrapper供Mock复用。类型/16MiB仍是CLAUDE待追认候选，不静默变规格；unresolved操作必要元数据生命周期边界在F09显式说明，不能假装所有运行态固定容量。

### 7. 建议下一步

Main集中review此阶段真实源manifest/正式路径及准确缺口；先定向真实F11–13与附件transport复验，再解除短暂产品冻结完成健康拆分并更新证据。Mock可继续自己的白名单，Main阶段快照/独立视觉worktree不需要本Agentcommit。此一致阶段可供可回退快照，但保留F01–F13待验/待修事实；后续继续功能整改，最终两个独立门禁不由本报告替代。

## 定向补修最终交回（2026-10-12 21:54；阶段快照27c5cb4之后）

**当前再次冻结原功能工作区产品文件，未提交；视觉worktree完全未触碰。** 本节更新上节中的当前未修项/数量，未更新处仍按上节七项与F01–F13范围；非V1完成判定。

1. **条款**：06 §1.4独立Thinking/工具终态、§0小型真实投影，以及代码健康约束。对应F11现场第二轮反例：“每工具前两个Thinking complete，第二卡为空”。
2. **实际变更**：只改原工作区core/projection.ts、core/drafts.ts、core/controller.ts及相关测试。原生agent_callbacks._agent_thinking_update明确thinking.delta来自等待通知/quiet spinner；agent.turn_iteration_prep发ruminating占位，turn_api_call.stop_thinking_spinner发空串清除。因此thinking.delta只更新内存activity（空串清除），完全不创建推理卡。真实reasoning.delta有实际非空文本才创建/续写Thinking段；tool/text开始仍逐段封口。不使用CSS隐藏/同文去重冒充修复。草稿迁移判断拆成hasDraftContent/preferSavedDraft，adoptDraftScope从CC22降至12，语义/晚版本保护不变。
3. **正式路径**：native WS事件→生产Controller.event→reduceEvent→真实node.id列表；wait activity与模型reasoning两个协议事实各归其位。生产Controller真实事件顺序用ruminating→reasoning→tool.generating→empty spinner clear→tool.start/complete→下一wait/empty clear/第二tool，验证只有一个真实非空推理段，第二工具running/Turn仍active。
4. **验证**：当前定向4文件 **69测试通过**，production Controller事件反例+reducer空delta/clear反例+真实ReactDOM终态缩短/单卡折叠均通过；typecheck通过，当前产品build通过。TS AST健康扫描无>20/300/6与>2000文件；adoptDraftScope CC12/16行。Main已在真实UI确认先前F11逐段瞬间折叠、动态双工具终态无白屏、16MiB实际上传及模型确认、Cancel恢复原文/附件且无newTurn、重复chips修复后16MiB单卡；这些证据来源是Main，不冒称本AgentUI取证。新的spinner分离尚待Main同类定向现场确认。
5. **缺口**：上节cold/replay/epoch/历史旋转、真正unknown断线恢复、附件超限实际拒绝、Office/媒体/HTML动态预览、独立四viewport/真机等缺口仍在。16MiB边界由Main已实测通过，但尚不能把未知ACK所有分支/超限真实传输自动写成通过。
6. **接口影响**：没有后端API或设计props变化；仅区分原生existing thinking.delta与reasoning.delta。无第三方/视觉树/Mock变更，无新持久字段、规则或门禁。
7. **下一步**：Main只需定向复验新的无空卡/只有真实reasoning路径，集中review69测试日志与最新source-manifest；不要重复已通过附件/白屏整链。原功能树保留后续非视觉整改，27c5cb4视觉快照继续独立使用；本阶段交回不替代Verification/Validation。

## Main review 剩余两项完整交回（2026-10-12 22:01）

**原功能树当前产品文件再次冻结；未commit/stage，未触视觉worktree/design/Mock。** 本节为27c5cb4后的两项定向补修；上节F01–F13真实缺口继续保留。

1. **条款**：06 slash执行/失败草稿恢复、原owner归属及Reasoning真实能力与生效值；Main集中review指出 `/stop`捕获错误却返回正常、命令层随后消费草稿，以及Reasoning只有current+none而缺完整请求档位。
2. **实际变更**：Controller.stop捕获binding/key/storedRoute，验证原生`status=interrupted`才接受；not_interrupted/缺回执/RPC错误/unknown抛出，notice仅归原owner。routeReadControl await此结果，失败不进入consume；按钮动作catch显示错误，不形成未处理promise。切路迟到Stop失败不会影响B或吞A。Reasoning新增只读能力选择helper，当前模型provider以原生slug/name/aliases匹配；真实cap.reasoning=true提供原生七档请求levels，false为unsupported、无cap为unknown；none仅明确can_disable_reasoning=true。当前requested独立读config.get/session.info/draft选择；actual wire独立读reasoning_effort_wire，Conversation缺值明确Unknown，不从requested推断。菜单不把当前值列成唯一选项、不造Provider档位表。
3. **正式路径/来源**：App→ChatDialogs实际props/options→已有config.set reasoning→ensureBinding回读，NewChat仅draft override；没有新后端方法/模型适配。来源为`hermes_constants.py:996` VALID_REASONING_EFFORTS、`apps/shared/src/reasoning-effort.ts:4`、`apps/desktop/src/app/shell/model-edit-submenu.tsx:209`；native `hermes_cli/inventory.py:538` 明确故意不转发supported_efforts（会漏合法档位），只转reasoning/can_disable。模型请求档位不宣称各provider原样wire，clamp唯一事实为原生session.info。Stop来源`methods_session_interrupt.py` / contracts.sessions，只认真实interrupted回执。
4. **验证**：新增生产Controller `/stop`失败保文本+Blob、丢ACK切路保A不污染B、not_interrupted保草稿3例，原成功Stop控制用真实形状fixture继续通过；reasoning provider别名/完整七档/none mandatory/unsupported/unknown测试；正式ChatDialogs ReactDOM分别展示Current ultra、wire max、全部七档列表。只重跑受影响两核心文件 **68通过**（`stop-reasoning-unit.log`）及受影响React文件 **3通过**（`stop-reasoning-ui.log`），保留前一69中的3个未变theme结果：当前 **74个不同产品定向用例** 有效，不把重叠重跑累加。typecheck与最终vitebuild通过，健康扫描无超标，最新source-manifest包含50个tracked/新产品文件，排除Mock。

真实只读新服务WS `model.options({profile:'',explicit_only:true})` + `config.get(reasoning)` 已运行，结果default deepseek-flash/provider custom、cap.reasoning=true、current medium、无RPC错误，证据`frontend/reasoning-live.json`；脚本只存model/provider/cap/current，无token/APIURL/凭据，无config写/模型调用。actual can_disable字段未知，所以不猜none；当前可显示七档合法Hermes请求，wire必须由真实session.info另报。本Agent无法iab，未冒称按钮实际模型响应已验。

5. **缺口**：Main仅需实际Reasoning菜单/设置回读和现场无空Thinking卡定向确认；待整体独立门禁继续cold/replay/rotation、附件unknown/超限、预览逐格式/HTML安全和四viewport等既有缺口。不能因两项定向通过改变全轮完成条件。
6. **接口影响**：现有stop Promise失败现在对命令层可辨；官方interrupt DTO不变。Reasoning沿原native请求level标准与真实capability，未扩大API/增加持久响应/新模型路由，未修改纯视觉props体系。
7. **下一步**：Main集中review此定向变更并合入原功能树阶段；复用已有效74例/构建/真实能力read，必要仅补实际Reasoning与无空卡反证，不重复附件/白屏整链。视觉worktree仍独立27c5cb4基线，当前功能改动不擅自同步过去。

## F17–F19 集中闭合交回（2026-10-12 22:22）

**当前原功能树再次冻结，供Main集中review/必要真实定向复验；未stage/commit，未触视觉树/design/Mock。** 沿R2-C24停在Verification之前，不派门禁；视觉完成合并后的独立审查由Main另行组织。此节只收敛Main三个新反例，不重复其已接收F15/F16的74例。

1. **条款**：06 §0.5/§1.8–1.9/§3.4原生单owner、unknown无盲补偿、真实pending事件重取；既有slash/Compaction真实状态与失败反馈、真实历史/tip和草稿归属。
2. **实际变更**：
   - F17：uncertainSteers同一操作owner保留原runtime/profile/storedId、turn_id/op_id/text、draft/revision；`checkSteer`直接调用既有session.steer_pending查询相同回执，不先读当前active快照、不生成新operation。steer与Send入口遇该owner均只恢复旧op；UI不变原主按钮矩阵，未知时禁普通Send/Steer并明确Check Steer，Stop/Interrupt不被误当补偿Prompt。accepted pending/consumed仅消费captured内容；withdrawn/rejected保现稿并解除已明确状态；unknown_turn或错配turn_id的terminal_conflict继续unknown。明确匹配旧turn拒绝才能解除unknown；已收到Steer ACK后后续snapshot失败不重新捏造admission未知。
   - F18：pendingReads由同一单飞read owner包含runtime/generation/promise；pending_changed/consumed只使此owner失效；过期响应不发布，顺序再读到最新代次。多次失效合并、一时只有一个请求；第二读途中再失效则继续下一读；不同runtime响应不能覆盖当前owner；finally只释放自己的owner。没有新store/轮询器/持久缓存。
   - F19：slash compact交正式Controller.compact，消费原生summary.headline/token_line/note、status/lock_held/message；refused_would_grow、aborted、fallback/lock明确warning，不以compaction_state completed冒充实际压缩成功。lock_held/pending保留命令与附件。原生status.update kind=warn作为owner-qualified通知展示，ready不抹掉其事实。RPC结果后activate原runtime读真实info.stored_session_id/tip，REST正式历史从该tip读取但仍归原Conversation路由/内存key；不只ensureBinding、不拿RPCmessages冒持久事实。迟到结果不改B草稿/通知。
3. **正式路径/依据**：Controller.sessionEventEffects→同一readPending invalidation owner；Controller.steer/send/checkSteer→既有methods_pending.py receipt lookup BEFORE active gate，agent.pending_steer.py epoch/submissions与真实state。Composer仅投影同owner unknown和Check action，不持第二份ledger。routeReadControl→Controller.compact→session.compress→native session.activate→REST history＋readCompaction。压缩反馈来源contracts.sessions CompressionSummary/SessionCompressResult与agent.manual_compression_feedback.summarize_manual_compression；本次Main真实seq424 warn说明“不删消息”的refused fact，不能被status compressed/operation completed覆盖。
4. **验证**：先前原产品三条production反例均实际失败，日志`pending-recovery-before.log`：inactive后旧op不能查、unknown被普通Send提交、在途快照失效漏读。压缩summary丢失同样先失败，`compaction-feedback-before.log`；warn事件测试当时已随集中实施补入，所以该日志为summary1失败/warn1通过，不冒称两项都先红。

当前生产Controller **43测试通过**，包含本阶段14个新增：旧turn晚ACK原参数幂等、编辑/附件不阻恢复、unknown不能Send、unknown_turn/错配terminal保留、同turn明确拒绝释放、切route接受只消费A、多个失效顺序三读且max concurrent1、已知ACK后读失败不变unknown、真实refused summary/tip历史、warn、lock保稿、迟到压缩不串B。实际ReactDOM恢复控件1新例通过，证明普通Send disabled/Check Steer可操作/新文本保留。首次DOM用textContent查图标Send失败，为测试locator错误；改按正式aria-label后通过，失败未遮蔽/丢失。证据`pending-compaction-unit.log`保留Controller43与React原3通过及该locator失败；纠正后`pending-recovery-ui.log`为新UI1通过。仅搬迁无语义的historyLocator/ComposerFeedback避免函数复杂度，随后`compaction-tip-final.log`定向验证真实tip读取。**当前累计89个不同产品定向例有效（已接收74+新增15，不累加重复执行）**。最新tsc/Vitebuild通过，健康扫描0超标，Controller1778行；source-manifest更新50文件，排除Mock。

Main真实双sleep12期间reload恢复同会话一份STREAM_RELOAD_OK；native replay为0reasoning.delta/9thinking.delta，现场0Thinking符合真实spinner分离，不杜撰推理；历史reasoning sidecar继续真实展示。真实压缩Cancel后环回9%只证UI操作/后端状态观察，未捕获原RPC终态，未宣称全部取消机制验收。本Agent当前依旧无iab，没有替Main实际点这三项复验。

5. **缺口**：F17–F19新真实定向复验待Main；当前op身份仅浏览器内存保留，未增加跨reload的持久operation ledger，不冒称跨reload同op恢复保证。未决旧epoch被裁剪时如实unknown，不能假拒绝；原生无snapshot+seq原子cut，既有cold/replay/rotation完整交错、附件unknown/超限、预览逐格式/HTML安全/四viewport与真机缺口继续按此前表保留。用户等视觉完成后再门禁，不等同于这些缺口自动完成。
6. **接口影响**：无任何后端DTO/新API/模型路由/规则门禁。Controller.stop等已接收功能未复做；本阶段只核心操作/read生命周期、native压缩feedback、必要Composer恢复提示。noticeTone是当前视图内存呈现事实（warning/neutral/error），不持久响应；共享design纯props不改。
7. **下一步**：Main集中review三个正式路径与before/after证据，稳定窗口只补旧op回执/并发失效和真实refused压缩反馈/tip历史，不重复已过模型/附件/白屏整链。完成必要底层review/复验后由Main阶段提交；视觉独立worktree用户施工持续，合并后再Verification/Validation。

## 正向压缩真实取证交回（2026-10-12；原生53445）

1. **条款**：真实Main→正式压缩成功发布→carrier/UID/Conversation身份事实；不伪造summary、不插DB、不改阈值/模型/保留策略。
2. **实际动作**：只新建合成stored `20261012_223239_3eb664`（runtime `f1f3c0a7`）。先读native head3/尾部floor+最近user/assistant保护、lean每用户4,000字符节选机制；两短确认作为head，第三条900行重复温室记录212,463字符，随后三短确认使其进入middle。共六次默认DeepSeek真实Main，回复均正常；只调用一次正式session.compress，未重试模型/机械反复压缩。实际输入/脚本/回复在`frontend/compaction-positive/**`。
3. **正式路径**：bootstrap仅内存→session.create→六次prompt.submit_idle→session.compress→activate实际tip→REST live/archive历史及secretary.state；没有触现有两会话、53446、真实用户配置/库、产品/视觉/门禁。
4. **结果**：native summary **12→10 messages、~79,243→~29,762 tokens**；noop/aborted/refused_would_grow/fallback_used均false。carrier UID `cdc55ef9bfb841a8b87db34ab3df5237`/row121真实发布。原生当前in-place，tip保持原storedID，不捏造rotation；Conversationref `conv_0c38d52e956247fd854b2e6fa8734178`前后相同。12个原UID全部仍在archive，missing0，live carrier及canonical事实见verdict/identity-invariants/after-history；数值是原生approx估计，不冒充wire计数。Main已用该stored在实际Web看到carrier；由此发现的原角色呈现错误在下节修正。
5. **缺口**：此例不覆盖旋转、取消/unknown、所有cold交错；不用一次正向成功替代既有门禁。原生默认in-place不为取证改成rotate。
6. **接口影响**：无；native source/process按现行53445，token未保存，JSON敏感key扫描无非空凭据字段。
7. **后续**：Main复用该stored/完整证据，不重复模型；当前合成会话保留供只读UI验证。

## F16实际5098恢复 / F20组合carrier真角色（基于30d3135，集中交回）

1. **条款**：真实能力/error/unknown，不猜七档；组合carrier原文保持真正source role，仅human user可Reply，summary独立Compaction折叠。
2. **根因/变更**：实际53445 model.options global/scoped均5098：运行5ccc619723、checkout6d96e80bf8，见`reasoning-recovery/native-shape.json`；旧loadCapabilities allSettled静默吞成models={}。保留guard，公开modelError+Retry capabilities；默认/当前runtime请求按当前视图owner+serial归属，真实gateway-ready/binding/model变化重读，失败不捏造cap，NewChat重新取launch默认而不带前一runtime模型。App的carrier原文曾硬编码You；现按node真实assistant/user/system呈现，assistant/system不Reply，reserved synthetic wrapper也不Reply。没有改design/视觉树/Mock/参数/模型路由。
3. **正式路径**：native model.options→Controller当前owner投影→Model/Reasoning错误与Retry→相同原生读；requested/wire规则保持此前已审来源。NodeDisclosure→CarrierOriginal→真实role Message或System Notice→独立summary Disclosure；实测row121 assistant/MATERIAL_RECEIVED为准确fixture。
4. **检查选择/证据**：只选Controller+Timeline两个受影响文件（绑定/重连/read owner/消息呈现），复用不变contracts39+theme3以及此前89对应机制证据，不跑模型/全量/Mock。精确命令 `npm exec -- vitest run src/core/controller.test.ts src/core/timeline.test.tsx`、`npm run build`。第一包54通过；随后静态review发现新增scoped catalog须在NewChat释放旧runtime默认值，补修并加1反例后同一受影响包最终 **55通过**，构建通过；不是零碎逐点包，实际两次执行及理由/耗时如实记录，不把重复相加。新增8例，当前**97 distinct产品用例有效=55当前包+42不变复用**。最新源hash、版本与选择表在`reasoning-recovery/version-and-check-selection.json`；frontend HEAD `30d31350f726b366ade95cef123fc9b08bfec472`＋当前5文件未提交变更，manifest50/健康无超标。日志`reasoning-recovery/regression.log/build.log`。
5. **程度/缺口**：实际5098失败已证；成功cap恢复为生产Controller受控形状测试，不冒称当前阻挡服务已成功恢复。Main在F14集成后统一安全重启53445，批量实测Reasoning+角色carrier；当前不重复模型/不绕guard。89中原enum/owner契约仍有效，F16“真实UI可用”与F06 carrier角色正向声明曾不足，已明确由本节取代，不能以旧单元绿掩盖真实失败。原有cold/unknown/预览/四视口等仍按索引。
6. **接口影响**：只新增临时当前视图错误/能力scope，无持久response/identity registry，无后端DTO修改；shared design公开契约不变。
7. **后续/冻结**：原功能产品现在再次冻结、未stage/commit；Main集中review后统一快照/restart和必要底层批量实测，等视觉合并再开Verification/Validation。本Agent释放浏览器（没有可用iab/无活动tab），不自行启动门禁或扩大场景。
