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
