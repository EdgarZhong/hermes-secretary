# 第二轮实施计划

## 目标与依据

依据 [Snapshot Index](snapshot-index.md) 与 [baseline.txt](baseline.txt)，冻结提交 `37ad76f5dfac02d4774d5e0faea55911b5fb8de9`。交付 06 divisions 0–4 的完整 Web V1，以及 V1.6 移交未闭合验收；division 5 为明确排除范围。规格本轮不改。先打通新建/恢复会话→真实提交→流式结果，再完成控制、秘书和文件功能；不引入 BFF、持久浏览器历史或第二执行循环。后端在当前 main；前端 `/Users/edgar/code/hermes-secretary-web`，无远端。过程文档只在后端。

## 覆盖与任务

| 要求/口径编号 | 任务和正式路径 | 实现负责人及白名单 | 依赖和接口 | 验证方法 | 用户场景 | 完成条件 |
|---|---|---|---|---|---|---|
| 06 §0、§2–3；C03 | T0 原生兼容审计：当前 REST/WS/DTO、Desktop 对照、N/F/A/D 与增量缺口 | Sol 只读源码；只写本轮 native-compatibility.md、ignored native-audit 证据 | 产品基线 edd031f551；主会话审核 A 项后才授权施工 | 源码及精确原生反例，全部拟增量先有失败不变量 | 全部场景的真实入口 | 每项功能来源明确，A 有必要性证据、D 无施工 |
| 06 §1.1–1.6、§1.13–1.16、§4.2–4.4；C05 | T1 中央 tokens、共享无业务视觉组件及四视口样式 | Astra medium 视觉：前端 src/design/**；后端本轮 visual-design.md | React/assistant-ui/shadcn/Tailwind；组件纯 props；不触碰网络、导航、状态机 | 组件 props、焦点/对比/减弱动画、后续四视口真实截图 | S01 新建与恢复；S05 文件返回；S09 小屏 | 设计系统实际接入，不只是 mood board；固定控件语义/位置不变 |
| 06 §0.3–0.5、§1.2–1.5、§3.1–3.3 | T2 前端基础和真实对话：REST 分页+WS、内存 identity/replay、三主页面、草稿/二进制本地恢复 | Sol 前端除 src/design/** 外；不得改后端/过程看板，证据写本轮 frontend-report.md | 以 T0 实际 DTO 为准；与 T1 纯呈现接口集成 | 本地状态/身份契约测试、实际 REST+WS；刷新/断线/压缩谱系/非默认 cwd | S01 新建不建 Session、首次只建一次；S02 历史和流不重复/串线；S03 草稿恢复 | 核心纵向路径真实可操作，accepted 数据只归服务端 |
| 06 §1.6–1.11、§2.2–2.5 | T3 控制与附件：单按钮矩阵、pending/withdraw/atomic interrupt、Cancel Send、两次确认 Rewind、独立压缩取消 | Sol 后端白名单待 T0 源码审核后指定；前端同 T2 串行 | 原生 correction 队列/Turn fence/压缩发布接缝；先有最终方法 manifest | 真实 DB/正式 Loop+受控外部返回构造 races；native old-client compatibility；真实图片/普通文件/PDF | S04 attachments→实际理解；S06 steer/withdraw/finish/interrupt；S07 cancel/rewind/compaction races | occurrence 不丢不重；取消不能误停 Turn；未知 admission 不盲重发；附件上限有实测 |
| 06 §1.12–1.16、§2.6–2.8 | T4 Secretary 只读、Slash、Usage/Context、真实 carriers、Files | Sol 后端增量白名单依 T0；前端同 T2 串行 | 正确 profile/conversation_ref；现有 REST Files 和 native catalog；T1 呈现 | 只读前后 DB/model-context 对照、事件失效重取、计数 provenance、授权文件错误 | S05 文件深层返回原 chat；S08 `/notebook` transient、Orb/Memo、slash/usage | 只读不启动任务/消费、不猜计数；旧 CLI/TUI 不变 |
| C04、06 §4.6、02/04 当前有效条款 | T5 V1.6 移交补验：C15/C16、Persistence、Reminder、global/cold/branch/undo | Sol 机制补证与所需修复，白名单按具体缺口派遣；真实验收由 Validator | 旧有效版本证据复用；不重做旧轮整版 Verification | 实际 DeepSeek、自然 timer、合法冷恢复；隔离 profile；沿用真实接口 | S10 Main busy+memo auto-on；S11 source→批准后持久化；S12 Reminder/身份边界 | 已移交缺口闭合且旧失败不被抹除；未启用仍原生 |
| 06 §4.5–4.7、C05–06 | T6 全轮集成与独立双门禁、交付 | Main review；新 Astra high Verification；通过后新 Astra medium Validation | 交付 commit、实际构建、最终方法 manifest；全部范围内开发缺口已补 | 统一安排一次必要扩大检查；独立条款矩阵；真实 localhost 四视口/模型用户旅程 | S01–S12 及验收者独立展开的全部适用场景 | 无范围内失败/证据不足/未执行；final-delivery 诚实覆盖限制 |

## 接口与执行安排

用户增量 C20–C21：T7 由 `static_mock`（GPT-6.1 Sol high）在前端 `src/mock/**`、`mock.html`、`vite.mock.config.ts`、`public/mock-fixtures/**` 构造独立静态交互入口，覆盖 06 全部呈现场景与已确认修订，复用正式设计组件，不导入真实控制器/后端连接。过程报告 `static-mock.md` 收录场景矩阵和交接，Main 管 npm scripts 与阶段提交；其他产品文件仍归前端 owner。Mock 可运行且前端达到一致快照后，Main 创建独立前端视觉 worktree 供用户另行设计，用户交回再 review 集成。Mock 不代替真实接口或功能验收，主会话并行继续 T3–T6。

1. 主会话已审核 T0，最终方法名称见 native-compatibility.md §11；具体后端白名单随各 owner 派遣限定；增量的 owner、输入/状态/错误、unknown acceptance、锁/线程、事件、ephemeral/durable、兼容和测试逐项落在 native-compatibility.md，不改一级规格。
2. T1 可先行，纯视觉接口集中 `src/design/index.ts` 导出；仅依赖 React、Radix/shadcn 方式 primitives、lucide-react（若采用）及 CSS。设计师不改 package.json；交回依赖清单供 T2 集成。不创建 App/router/client/store，组件只通过 props/children/callback 呈现。
3. T2 开发负责 package/lock/config 与业务模块，避开 T1 白名单；等待 T0 的实际 DTO，不自行猜拟 A 方法。T3/T4 后端按不相交 owner 分组，必要共享文件串行；前端同一实现者完成控制接线。
4. 每项阶段完整交回七项报告；主会话集中读实际 diff/上下游，不用重跑有效测试代替 review。机制实现、正式接线、针对性验证、真实用户结果的动态状态仅在根 CLAUDE 维护，本计划不复制看板。
5. Development 必须读 executing-plans、索引/基线/计划与所派冻结原文；02 精确章行范围每次随派遣指定。独立审查先从冻结要求建立判据，不能先读实现自评。Validation 先交完整计划再真实操作。

## 缺陷与整改

T0审计已由主会话接收，S01–S05/I01–I03/C01为新增V1行为缺口的源码反例，T3/T4负责关闭；它们不被冒称原生旧功能回归。V1.6移交缺口继续保留。范围内审查发现按下表追加，不降低冻结判据。

| 编号 | 要求与触发条件 | 当前事实与影响 | 优先级 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|
| R2-F20 | 06组合Compaction载体保真实来源角色 | 真实压缩row121原role=assistant，App DisclosureNode对realText硬编码user并提供Reply | P1 | 前端Sol | 按真实role展示原文，仅user可Reply；React反例及实际carrier复验 | Main真实成功压缩后发现，精确源码已定位 |
| R2-F17 | 06 unknown acceptance 不盲重发 | Turn结束后旧op查询被前端active gate阻挡，普通Send可能重复提交 | P1 | 前端Sol | 同一owner保存原turn/op，Check/Send仅查询旧op，明确receipt前不发新请求；生产反例通过 | Main已接收修复及生产Controller证据，30d3135 |
| R2-F18 | 06 Pending 真实失效重取 | singleflight中pending_changed复用旧响应，漏掉在途变化 | P1 | 前端Sol | 唯一owner失效代次，过期结果不发布并顺序重读；生产并发反例通过 | Main已接收修复及生产Controller证据，30d3135 |
| R2-F19 | 06 压缩真实反馈与History | 原生拒绝摘要增长，前端丢RPC结果及warn，没有notice；仅ensureBinding不刷新History | P1 | 前端Sol | 真实summary/lock/error明确反馈，成功发布后按新tip刷新History，保owner草稿；受控与真实补证 | Main已接收机制，真实refused反馈通过；成功tip补证中 |
| R2-F15 | 06 §0.5/§1.12 命令失败正确反馈 | Controller.stop吞错误后command-actions仍consume输入 | P2 | 前端Sol | 失败保留原owner命令草稿、明确错误；production定向测试 | Main已接收机制，30d3135 |
| R2-F16 | 06 §1.5 Model/Reasoning真实能力选项 | 七档机制已修，但30d3135真实会话仍显示capability unavailable，与原生catalog captrue不符 | P2 | 前端Sol | 定位实际catalog/runtime身份或加载失败，真实菜单/设置回读正确 | Main真实复验重新打开，保留reasoning-unavailable-real.dom.txt |
| R2-F14 | 02 §4.5 C16 合法 cold catchup、§5.5真实冻结前缀 | 5ccc619真实冷恢复事件已准入，parent._session_messages未恢复，spawn前失败无Snapshot | P1 | Core Sol调查/实现，Main集成，V1.6 Sol真实复验 | 原生恢复顺序/正确prefix，单事件不重复，未启用不变；先接缝设计，再定向机制和真实cold复验 | Main已审设计及原生接缝，实施中 |
| R2-F12 | 真实多工具 Turn 的 stream→durable 投影切换 | assistant-ui message index 18 越界（length18），NodeMessage 使整页空白；实际第三次 PDF/JSON请求复现 | P1 | 前端 Sol | 稳定身份/生命周期修复，真实多工具流终态切换无崩溃，不仅error boundary遮蔽 | 实现及源码review已接收，后续真实多工具未再现 |
| R2-F13 | PDF+JSON附件正式提交 | 同一用户消息两附件各显示两次，疑似预测与durable双投影 | P2 | 前端 Sol | 依据真实身份合并，无重复/丢失，刷新前后结果一致 | authored prefix实现review接收，真实后续附件单份 |
| R2-F11 | 06 Thinking/工具卡独立生命周期；多工具真实 Turn | 用户与 Main 实测：旧 Thinking 在后续工具运行时仍显示 running，Turn 结束才统一折叠；工具卡同类风险 | P1 | 前端 Sol | 按每段/调用真实事件与身份独立终态和折叠，保留手动行为；以动态连续观察及事件时序复验 | 逐卡折叠用户确认；空Thinking修复review接收，真实双工具无空卡 |
| R2-F10 | C17–C18；Files 打开 Markdown、长文本与常见文档 | 现有通用 pre 不渲染 Markdown/不折长行，多数二进制无法预览；面包屑含 Files/Parent folder 人工标签 | P1 | 前端 Sol；视觉配合容器 | 成熟本地预览库接入真实鉴权文件；代表文本/图片/PDF/Office/媒体验证；工作区相对路径及根强调色，四视口可用，无第三方文件外发 | 用户审看发现，整改中 |
| R2-F09 | 06 §0.3–0.4 的 bounded ephemeral state；长期切换多个 Conversation | histories/lives/bindings 等分散 Map 缺统一释放边界，历史投影可随浏览持续积累；当前未发现持久 API 缓存 | P1 | 前端 Sol | 用统一 owner/lifetime 管理当前视图和必要在途状态，其余按需原生重建；连续切换、回看、ACK/断线与草稿归属验证 | 中期架构检查发现，整改中 |
| R2-F01 | 延迟发送/steer/withdraw ACK 期间切 Conversation 或编辑 | owner 草稿可能串线、撤回文本丢失或新编辑被误清 | P1 | 前端 Sol | 生产 controller 延迟 RPC + 切换/编辑反例通过，按 accepted 内容与原 owner 更新 | 整改中 |
| R2-F02 | 分页、live refresh、replay 失败和 snapshot 字段缺失 | 旧页被覆盖，恢复可能卡住或把 unknown 猜成 idle | P1 | 前端 Sol | 保持已加载范围和滚动，竞态与失败可恢复，真实 REST/WS 不重复 | 整改中 |
| R2-F03 | busy Turn 输入 slash、动态 catalog 与 command 结果 | 命令可能作为 steer 发送，通用结果误标 Notebook transient | P1 | 前端 Sol | 统一先解析 slash；依据真实 catalog 与原生行为验证 | 整改中 |
| R2-F04 | Files/Photos、历史附件、Edit、大小/类型边界 | 附件分类、历史恢复与明确限制缺少完整证据 | P1 | 前端 Sol | 图片/文件/PDF 正式链路与 Edit 恢复、上限实测 | 整改中 |
| R2-F05 | New Chat 首次 admission 未知 | stored ID 未正确绑定，发送可能永久锁住 | P1 | 前端 Sol | 可查询/恢复实际会话与明确 unknown；不盲重发 | 整改中 |
| R2-F06 | 历史工具/thinking/system、compaction、reasoning | 部分投影猜测状态或遗漏事实，选项未证明后端支持 | P2 | 前端 Sol | 原生真实 DTO 覆盖且 provenance 明确；不捏造选项/状态 | 整改中 |
| R2-F07 | Files retry、深链边界、消失的恢复目标 | 重试不重新 fetch，路由与草稿 fallback 不完整 | P2 | 前端 Sol | 实际错误后恢复、根目录限制与保草稿 fallback | 整改中 |
| R2-F08 | Web Idle Send precheck 后另一客户端抢先准入 | 原生 prompt.submit 按原 busy 模式转换 queue/steer/redirect，违反 06 无隐式兜底；单独前端检查不原子 | P1 | Core Sol + 前端 Sol | 原生现有准入锁内新 idle-only 入口，竞争拒绝且不丢草稿；覆盖 busy/claim 交错及旧客户端兼容 | 后端机制已由 Main review 接收；真实前端竞争/保草稿联调待验 |

## 取舍、快照与续接

- 文档基线 `37ad76f5dfac02d4774d5e0faea55911b5fb8de9`；V1.6 产品 `edd031f5518955a10a2c68210e1c65477d6f0991`；该产品尚未全验收。
- 用户数据：只用仓库 ignored 隔离 profile；不读/清理私人 Pi 库；凭据仅获授权本地读取，不入 Git。无云部署/远端 push。
- 官方 PM Python 解释器与锁沿用；前端新库正常 npm lock，不改后端依赖锁。测试必须 canonical runner；大型检查只集成收敛后统一一次，失败修复按影响复测。
- 四视口 1440×900、1024×768、390×844、320×568 均强制；软键盘/相机/系统侧滑真机证据后续专项，功能仍实现。
- 当前版本和完成状态见根 CLAUDE。每个阶段本地快照写明验证与缺口；最终双仓分别给出 commit。


### T3a correction 与 atomic handoff 具体授权

Sol同一任务负责 `agent/interrupt_control.py`、`agent/agent_init.py`、新 `agent/pending_steer.py`（或同义唯一owner sibling）、`agent/agent_runtime_helpers.py`仅steer helpers、`agent/turn_iteration_prep.py`仅原生插入、`agent/turn_finalizer.py`仅pending/关闭、`agent/turn_context.py`仅Turn epoch起点、`tui_gateway/methods_session_interrupt.py`及新pending sibling、`tui_gateway/prompt_turn.py`仅settlement/followup、`tui_gateway/session_auto_continue.py`/`session_lifecycle.py`仅相关handoff清理、独立新contracts文件、对应tests。共享server.py/module注册与contracts registry由Main统一接线；其他需改文件先报具体必要接缝。提交由Main做。开发先为真实竞态/传统路径取得必要定向证据，不能只测helper。


### T3b/T4a 压缩控制与 Secretary 只读投影

Sol任务白名单：`agent/compression_facade.py`只active registration观测/取消接缝、必要新compression read sibling；`tui_gateway/methods_web_read.py`（或分离的compression/Secretary新methods）、新独立contracts文件；`secretary/web_read.py`或同义只读sibling、`secretary/noting_child.py`仅真实task生命周期观测/事件、`secretary/noting_timers.py`仅只读观测/失效信号、`secretary/framework_messages.py`仅失效信号、必要memo mutation observer在具体写入点；对应定向tests。不触碰T3a的所有权文件，不改usage/原slash反馈语义。共享server/module注册由Main处理；需额外源码接缝先报告。该任务不得通过read触发Identity/Idle/Memo/Notebook写；压缩只读和取消复用现有fence，不影响Turn。


T3b/T4a白名单补充（Main源码review后）：允许 `hermes_state_secretary_notebook.py` 三个便利wrapper（memo mutate、local enabled、snapshot commit）在 `_execute_write` 成功返回后调用best-effort observer；新增 `secretary/web_events.py` 薄invalidation订阅器。无订阅者no-op，observer失败不能改变原操作结果；不改conn/schema/事务/写权限。global config观察接缝由Main统一接线。

T3a接口里程碑已review接收：详见 pending-implementation.md；有限容量/回执窗口影响已登记根CLAUDE待追认，非额外停工门禁。

### T4b 真实 Session/Latest Turn 用量投影

`web_usage_projection`（Sol high）负责 `agent/turn_usage.py` 的 canonical call 观察、新 `agent/usage_read.py` 或同义 sibling、新 `tui_gateway/methods_usage_read.py`、新独立 contracts、对应测试及 usage-implementation.md。Main 统一注册与生成契约。`turn_context.py`、`turn_finalizer.py`、`prompt_turn.py` 的小型生命周期委托接缝须等 T3a owner 完整交回后由 Main 明确释放，禁止并写。沿用原生会计与真实 Turn 边界；缺来源返回 unknown，不差分累计、不数消息行、不建立持久 Turn 账本。指定 02 阅读：§1 L14–257；§5.2–5.5 L1404–1541；§5.9–5.11 L1778–1847；§6.1–6.3 L2221–2261；§6.6–6.7 L2287–2315；§6.11–6.16 L2364–2451；最终不变量 L2514–2553。

Main 源码复核后补充白名单：`agent/turn_api_call.py::perform_api_call` 内真实 streaming/nonstreaming dispatch 前后可加薄观察委托；原 `api_calls` 含 retry/refund 的 logical iteration 语义，不能冒充实际 provider calls。观察在原 preflight/Reminder verify 之后，不改调用、中间件、返回、异常或 ACK；SDK 内部网络重试及 opaque advisor 无依据不得计成精确值。恢复的历史 Session Total 无来源就 unknown，新完成 Turn 仍可显示真实结果。

生命周期最终接缝：T3a 完整交回后已释放 `turn_context.py` / `turn_finalizer.py` / `prompt_turn.py`。begin 在真实绑定后；finish 在 `export_current_turn_boundary` 原 early return 前，以已 begin 的真实 owner 幂等冻结，覆盖正常返回的错误 envelope；UI 真正 throw 用 `_invoke_agent` finally 的薄 abandon，保持旧异常及 ticker 清理；finalizer 仅在真正调用 `_handle_max_iterations` 前标注额外总结无法计数，不影响复用 verification 响应分支。对应 `turn_exception`、`unobserved_iteration_summary` reasons 明确 unknown。

### T3c R2-F08 空闲提交竞争

Sol 新小阶段只允许 `tui_gateway/methods_prompt.py` 必要原生 claim 接缝、新 `methods_submit_idle.py`（或同义 sibling）、新独立 contracts、独立 `tests/tui_gateway/test_submit_idle.py`、submit-idle-implementation.md 和 ignored 证据。Main 注册与生成共享契约。先交最小设计/精确 DTO 里程碑，Main 确认后接线；不得修改 usage 已接管的三个生命周期文件，也不再修改 Pending 实现。复用原生准入 owner/锁，保持旧方法合同，明确覆盖 Web/旧客户端交错、busy→handler 与 idle→claim 间隙、锁序、真实 DB/附件、失败恢复和兼容。02 精确阅读为 §1 L14–257；§6.1–6.3 L2221–2261；§6.6 L2287–2301；§6.11–6.16 L2364–2451；最终不变量 L2514–2553。既有 T3a 有效证据不因新阶段机械复跑。

T3c 设计由 Main 亲查原 handler、claim、admission 与模块绑定后准入。最终接口 `prompt.submit_idle`，精确契约见 submit-idle-implementation.md；ContextVar 必须 finally reset，handler alias 经原 binder，claim source 标记仅原锁下元数据。两种先后顺序及 new/new 竞争由正式接缝屏障测试。

R2-F04 跨连接图片清理反例补充：旧 image.attach 未 settle，新 WS detach 可能先完成而旧 attach 随后 append。Main 亲查原生 `_admit_prompt_turn` 与 compute-host 均已有显式 image_paths 参数；T3c 同一 owner 最小扩展新入口携带本次图片列表，新请求默认空列表、旧入口保持 None。前端只上传取得路径，再随 Send/Rewind 传入；不再通过共享 staged images 绑定 Web 图片。校验在 claim/truncate 前；沿原生图片权限及执行路径，不新增图片账本或第二执行器。设计与正式测试仍由 T3c 完整交回，已登记 CLAUDE 待追认。

视觉阶段交接：前端 `27c5cb4`，worktree `/Users/edgar/code/hermes-secretary-web-visual-design`，分支 `codex/visual-design`，Mock5176。阶段快照不代表最终验收；用户另派设计，原前端继续功能整改。

执行边界 R2-C24（用户确认）：当前推进至 Verification 启动前；功能整改、Main集中review、开发期实测和阶段提交照常完成。用户/视觉Agent完工交回后，Main合并视觉并处理集成影响，再派完整独立 Verification；通过后 Validation。不提前派遣门禁，不以开发期证据冒称其通过。

R2-F14 准入：按 cold-resume-fix.md §4 白名单，Core Sol新增 session_agent_context sibling、methods_session eager、server build/attach及专用tests；Main已明确释放真实server接缝。完整native恢复在发布前完成；必要时eager薄传既有profile_home参数，保原生fallback政策、失败关闭及持久标记，不改timer/admission/freeze。真实复验待Main接收并集成commit后由T5 owner执行。

R2-C25：用户再次强调视觉层交由用户/视觉AI，Main专注底层功能和有效推进；现有阶段前端提交30d3135，成功压缩补证委派同owner仅操作53445新合成会话，零产品修改。既有89项有效证据不重复跑；原生cold修复仍由Core owner完成。

## 已有证据索引与回归选择（R2-C26，跨会话续接必读）

本节是**证据导航与测试选择依据**，不建立第二个动态任务看板。当前任务状态仍只看根 CLAUDE；下面的版本、观察与限制属于已取得的事实。续接者先读本节和相应报告，再决定是否运行测试；不能以“重新熟悉项目”“接收子Agent交回”“同文件又修改过”为理由重跑。

### 覆盖层次与计数口径

- **机制/正式接线**：生产 Controller 或真实 Gateway、SQLite、AIAgent Loop、timer/fence实际执行；只在外部provider/summary响应或时序屏障受控。证明边界与竞态，不冒充真实模型/浏览器。
- **真实协议/模型**：运行中的正式REST/WS/RPC、DeepSeek、自然timer和真实持久产物。证明跨系统链路，不冒充浏览器操作/独立Validation。
- **真实Web操作**：内置浏览器操作正式前端，再核原生事件或数据库。只覆盖实际做过的旅程，不以截图推断未观察动态行为。
- **独立门禁**：本轮尚未执行；上述三层都不能冒称Verification/Validation PASS。
- 不把多轮重跑数量相加。109/53/23/89等是各报告有来源的distinct覆盖，组间仍可能重叠，**不汇总为一个“总通过数”**。检查器失败、旧失败日志、未验证平台继续保留。

### 后端接线证据（可复用基线产品5ccc619）

源码精确版本以各报告的source manifest及Git树为准；5ccc619集成了这些正式接缝。后来的6d96e80为文档提交，不是新产品验证。共享文件后续变化只按实际受影响机制选回归，不能整份作废。

| 证据组 | 已测到的程度 | 证据/版本入口 | 当前复用与限制 |
|---|---|---|---|
| BE-PENDING | 30新增+79旧客户端=109 distinct；真实Loop/DB/RPC、重复文案与op、插入/撤回、终结晚ACK、单次handoff、旧queue/steer/stop、真实rotation到tip、关闭与off负对照 | [pending-implementation](pending-implementation.md) §4；ignored `pending/source-manifest.json`、`final-owner-lock-tests.log`、`last-integrated.log`、`final-regression-first.log` | 不因frontend修复再跑109；只有owner/epoch/插入/终结/原生准入变化才选相关子集。真实UI Withdraw/Interrupt另见WEB-CONTROL |
| BE-SUBMIT | idle-only锁内竞争、new/new/new/legacy、busy拒绝保状态、Rewind、profile、unknown；显式图片输入/顺序/真实parts/跨WS旧attach晚到、compute-host frame及inline fallback；typed Stop负对照 | [submit-idle-implementation](submit-idle-implementation.md) §4；`submit-idle/source-manifest.json`；15原设计、66旧回归、19最终图片、2 typed Stop分别复用 | 当前31用例覆盖由未变13+最终图片19扣重叠1组成，**不是一条最终31PASS命令**；旧T3a109未重跑 |
| BE-READ | 53 distinct：27Secretary/压缩+1真实Child+4legacy fence+21legacy timer；只读前后DB/prefix不变、真实child observer、取消/commit唯一胜者、fallback晚worker、queue保留、profile与global/local边界 | [read-implementation](read-implementation.md) §4；`reads/source-manifest.json`、`formal-and-error-tests.log`、`child-final.log`、`final-targeted.log` | 默认in-process已覆盖；新增compute-host read/cancel仍明确4010，未桥接。真实Web读/压缩另见WEB-READ/COMPACT |
| BE-USAGE | 23 distinct/4files/11.8s；正式Main stream/nonstream/retry/fallback/refund/异常/short-circuit、canonical计数、只读与profile、真实compression及Noting child不污染Main | [usage-implementation](usage-implementation.md) §4；`usage/final-source-manifest.json`、`final-tests.log` | `test_usage_read.py`、`test_usage_native_turn.py`、`test_usage_native_compaction.py`、`test_usage_noting_isolation.py`；无计数/Turn边界变更即复用，不因状态栏/纯外观变更重跑 |
| BE-INTEGRATION | 六新RPC真实WS返回预期unknown-session4001，生成一致性、正式注册；global config成功写后失效通知3例；相关ruff/health/config-writers通过 | `runtime/integrated-readiness.json`、CLAUDE接线记录、各owner生成物manifest | readiness不等于功能验收；既有review.summary孤立契约失败、profile-archives旧归档限制不抹掉；最后扩大检查只门禁前统一安排 |

### 前端与真实联调证据

| 证据组 | 已测到的程度 | 精确入口与观察版本 | 未覆盖/复验触发 |
|---|---|---|---|
| FE-CORE | 生产Controller+真实IndexedDB+真实ReactDOM，ACK归属、草稿、初次unknown、分页/replay、Files恢复、tool/thinking终态、稳定node.id、Stop失败、Reasoning能力fixture、Pending失效及unknown原op、压缩feedback/tip | [frontend-report](frontend-report.md) 21:45/21:54/22:01/22:22各节；`frontend/source-manifest.json`50/50由Main核对；前端`30d3135`累计89 distinct（74+15） | 不是所有真实浏览器场景已验；F16真实5098被吞、F20组合carrier角色后续单独修复，相关fixture通过不能覆盖实缺 |
| WEB-MAIN/FILES | 真DeepSeek Main与自然Noting；图片经native vision_analyze正确识别；PDF+JSON实际理解；单文件精确16MiB二进制上传完成、16MiB+1前端拒绝；重复chips/白屏修复后多次真实多工具无再现 | stored `20261012_213252_1fa75a`/`20261012_213956_bc8a48`；ignored `runtime/` 原始DOM/截图/事件，Main证据归属见CLAUDE | 不重发同图/PDF/16MiB来证明无关改动；IME/相机/真机专项未验；跨reload未知操作不保证持久ledger |
| WEB-CONTROL | 真Withdraw恢复；Interrupt只单续发；Reply/Edit退出恢复；双确认Rewind；Cancel Send保原稿与附件、无newTurn；双工具期间刷新用户row89和final row94各1条 | `runtime/interrupt-db-proof.json`、`rewind-real.dom.txt`、`cancel-real.dom.txt`、`stream-reload-{before,after}.dom.txt`、`stream-reload-db-proof.json` | unknown丢ACK依机制证据，没有冒称真实断网全部分支；没有控制/归属/发送机制变化不重跑完整旅程 |
| WEB-READ/PREVIEW | `/notebook`真实瞬时输出且前后tables/messages计数不变；Markdown/PDF/DOCX/XLSX/PPTX实际预览；HTML脚本/事件探针不执行；音频真实0→1秒ended且无error | `runtime/notebook-read-proof.json`、`html-preview-proof.json`、`audio-playback-proof.json`及Files截图 | 视频仅实际进入playing，施工HMR归零未算完整播放；真机、最终四视口未验；按C25 Main不扩展视觉检查 |
| WEB-COMPACT | 真实原生拒绝摘要增长，30d3135显示完整summary/28messages preserved；另一次真实成功12→10messages、约79243→29762tokens、无aborted/fallback/refused | `runtime/compaction-refused-after-fix.dom.txt`；`frontend/compaction-positive/{verdict,compress-result,identity-invariants,after-history}.json`；stored `20261012_223239_3eb664`，carrier UID `cdc55ef9bfb841a8b87db34ab3df5237` | native in-place故storedtip不变，Ref不变；真实Web已读carrier但F20角色错误待修；Cancel点击仅UI/状态观察，完整竞态按BE-READ机制复用 |
| MOCK | 96合成场景、16fixtures、20测试、独立类型检查/构建；Main亲读入口与组件复用、实际工作台/320预设 | [static-mock](static-mock.md)；`mock/file-hashes.json`；视觉基线27c5cb4 | 只作视觉设计工作台，不证明真实API/模型；Main额外Escape微修30d3135已记，视觉树未改；不将Mock测试算产品89 |

### V1.6 真实移交证据（独立门禁前开发补证）

唯一详细入口：[v16-handoff-evidence](v16-handoff-evidence.md) §8–10；ignored `v16-live/`。stage2-final-manifest记录7/7关键产品hash与5ccc619一致，Main已核，不以6d96e80文档HEAD冒新产品。

| 组 | 已取得事实 | 关键证据 | 保留边界 |
|---|---|---|---|
| V16-C15 | 2个真实Notebook、24History时间转回epoch最大差0，+08:00，human/Finish同Snapshot瞬间 | `C15-actual-interface-time-proof.json` | 不代替全部浏览器可读性 |
| V16-C16/VAL04 | 自然due读local；off事件结束后on不补；due前on单任务；真实8工具busy+memo auto-on，Mainend后新的合法period一次child/Snapshot | `H02-summary.json`、`H03-summary.json`、§8 | 不重跑这两条；cold H04-A/F14仍失败，修后新合法period定向补 |
| V16-GLOBAL | local/global warm/cold off/on、真实Main工具面和已有Notebookcold读取代表 | `H04-summary.json`及§8 | H04-A独立失败不能被其它H04通过覆盖 |
| V16-PERSIST | candidate→精准source read与本Conversation上下文→proposal/revision Memory未写→明确批准memory add→实际USER.md→自然Noting候选归档 | `H05-summary.json`、`H05-approved-memory-{main,files}.json`、`H05-final-items.json` | 模型后来3次无结果跨Conversation检索保留；§11已核冻结root指导各1次（hash838a1bc），正文经system_prompt_hash去重表读取，不能以旧字段NULL误判；缺逐次完整provider payload，不临时改冻结Prompt |
| V16-REMINDER | idleinstant；同due两deferred单carrier、成功response后各ACK、下次不重投；Schedule off/on合法overdueonce只触达一次；真实terminal35s跨due→busy deferred→同Turn下一request→ACK，无第二instant；跨Conversation/profile不泄漏 | `H06-H07-{ack-summary,carrier-proof}.json`、`H07-profile-isolation-final.json`、§10时钟表 | legacy跨profile resume可空建同key、0messages，不能冒称拒绝或恢复了原数据；旧ACK失败/崩溃受控证据按旧报告复用 |
| V16-BRANCH/UNDO | branch新Ref；undo5rows；失效银色UID不在History，新白色生效；parent Notebook全文与created_at不变 | `H08-effective-source-proof.json`、`H08-summary.json` | 不新建Full审计UI；不重做旧轮整版门禁 |

### 一次选包的回归方法

1. **先做变更影响表，再发测试命令**：列变更符号/正式接缝→受影响契约→可复用证据ID→此次新增/失效项→选择的测试文件或`-k`→真实联调是否必要。产品文件相同不代表所有旧契约都变化；测试版本以manifest/commit核对。
2. **按包集中执行**：同一交回阶段的相关失败/新增行为合并为一次定向命令；其后只有失败修正或额外实际变化才再测相应子集。不要一边点击一边无边界扩展邻近检查；真实发现先记清单，批量交原owner修复，再在稳定窗口集中复验。
3. **代表包**：Pending owner/Loop变更选BE-PENDING相关正式tests；准入/图片选`tests/tui_gateway/test_submit_idle.py`相关cases；读/fence选`tests/agent/test_web_compaction_control.py`和受影响read/child；计数选BE-USAGE四files；前端选`src/core/controller.test.ts`/`contracts.test.ts`/`timeline.test.tsx`中受影响tests，纯主题不跑API链路。canonical Python runner及仓库内basetemp不变。
4. **真实模型用在不可替代的边界**：代码回归优先真实生产机制+受控外部返回/屏障；实际provider/协议/prefix与用户输入输出代表链路已有结果直接复用。不要为UI文案/来源role等确定性变化重做模型长对话；复用已存在的真实carrier和会话进行只读复验。
5. **服务版本统一**：本地checkout提交变化可能触发native `model.options` 5098。先完成集成commit，核无活动Main/child/compaction后统一重启一次，记录health运行commit；必要真实复验集中在该稳定窗口。不得绕过版本保护、把错误吞成空能力或在未review源码上随意重启。
6. **当前剩余集中包**：F14冷恢复实现者的正式cold/并发/off负对照；F16能力加载错误/Retry与F20真实角色一组前端定向用例；Main接收并集成后统一重启，T5一个新Mainend→跨due冷恢复；Main同窗口实际Reasoning设置回读+复用已成功压缩carrier核角色。不重跑图片、16MiB、109 Pending、53 Read、23 Usage或整套V1.6。
7. **交回必须注明**：此次执行方、commit/源码hash、精确命令、范围/次数/耗时、通过/失败、复用证据ID、此次未覆盖。Main在本索引更新事实，CLAUDE只同步状态。全量/扩大检查仍按用户C24在视觉交回集成后的统一门禁安排，不能因本索引新增而提前跑。
