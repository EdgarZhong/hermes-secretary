# 第二轮实施计划

> 当前R2-C73–C75：首轮Verification不通过（完整报告已交回）；附件后端合同整改与assistant-ui只读研究恢复。研究已完整交回且Main亲审，按用户“然后开始”释放独立前端整改树；Usage成功数据可见性纳入后续整改。

R2-C66/C67增量：用户确认8轮/32条旧回执窗口及聊天历史首次200/更多200。前端待审更新为 `002f7a27fcf7313491f0301e143df7d3b6148088`。Main直接完成微小分页修改并亲审两文件diff；定向既有 `history range preservation` 测试1通过/59未选（205ms），覆盖首次200、更多至400、新tail保留401；typecheck通过，build通过（5.51s、保留chunk-size提示）。命令：前端 `npm test -- src/core/controller.test.ts -t 'history range preservation'`、`npm run typecheck`、`npm run build`，各一次。证据 `.hermes-dev/round2-verification/paging-{test,typecheck,build}.log`；不新跑模型/大包，不把未选测试写成通过。独立审查者已接收新版本及原始用户授权，须按受影响条款核查。

## 目标与依据

R2-C68：用户授权首轮Verification完成后由GPT-6.1 Sol修复审出问题，Main在完整交回后亲审与验收，不逐步监工。开发服务已恢复供用户真实使用；具体状态和现场反馈只在根CLAUDE同步。当前4项初步违规及Main提案保留，等待首轮完整报告再确定修复白名单。

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
| U-R2-05 | C80，侧栏须保原Mock视觉并按更新时间分组 | 正式App单Conversations section且缺Mock专属元素绑定的第二分隔线 | P2 | 前端整改owner | 正式Today/Yesterday/过去7天/30天/更早的真实更新时间组，Files/主题分隔恢复，四视口/主题，后台刷新无位移 | Main已定位，集中整改 |
| U-R2-04 | C78，Instant触发源先于新Turn输出展示 | 用户实测Thinking先见、源Reminder直到Turn结束才上Timeline | P1 | Main追原生发布，前端研究owner核投影 | 原生入場→事件→状态→DOM时序证据，Reminder及时出现且与后续Thinking/Assistant顺序正确、终态不重复 | 用户已报，待定位；前端暂不实施 |
| U-R2-01 | C69，Composer草稿独立编辑撤销 | 用户实用Ctrl+Z不可用，根因待查 | P1 | 首轮报告后键盘Sol | 实际浏览器文字输入/替换/连续撤销与重做；不触发后端Rewind、不串会话草稿 | 用户已报，未修复 |
| U-R2-03 | C72，Turn active/结束列表刷新应稳定 | 侧边栏会话列表在边界刷新时闪动 | P2 | timeline_latency前端Sol | 真实Turn边界保已有列表，标题/排序/新建仍正确更新，加载/错误恢复不清空已有内容 | 用户已报，待首轮后实施 |
| U-R2-02 | C70纠正，Timeline显示远落后模型，Stop后仍缓慢补显示 | Stop失效推断撤回；Main日志确认一次explicit Stop至Turn interrupted为95ms，显示积压层未定位 | P1 | timeline_latency Sol先只读调查，首轮报告后释放实施 | server事件→client接收→状态→实际DOM具区别力的时序/负载证据；及时反映真实终态，无人工限速、无丢失重排 | 用户已报，后端停止证据已核；根因/修复待交回 |
| V-R2-01 | 06 §0.5/§2.1旧REST/RPC合同保留，新能力新名 | `file.attach`扩展分片/stat参数与结果shape，C30容量授权未豁免兼容约束 | P1 | Main提案，实施owner待初审集中安排 | 恢复旧合同，新名RPC复用原owner；新旧正式接线、重试/取消/metadata及上传提交证据由独立复审核定 | 初步违规；Main认可，提案已交审查者，未改产品 |
| V-R2-02 | 活动Turn Reply/Edit须走Rewind语义与确认 | primaryAction仍Steer，perform调用steer且没有确认 | P1 | 待初审后Main集中安排 | 正式UI/controller选择Rewind路径及busy原子机制，确认/取消/失败保稿证据 | 审查者已落生产反例，待Main亲审 |
| V-R2-03 | Edit暂时截断目标之后Timeline | history/live截断但temporary原样透传，Notebook失锚跳顶部且Pending仍显示 | P2 | 待初审后Main集中安排 | 临时卡片及Pending一并遵守编辑截断，取消编辑恢复 | 审查者已落生产反例，待Main亲审 |
| V-R2-04 | Reply/Edit恢复原用户正文与附件 | beginEdit只strip引用，真实普通附件row的Attached Context附录进入草稿 | P2 | 待初审后Main集中安排 | 正式存储消息还原作者输入与附件，保模型真实上下文，不带入注入附录 | 审查者已落生产反例，待Main亲审 |
| R2-F20 | 06组合Compaction载体保真实来源角色 | 真实压缩row121原role=assistant，App DisclosureNode对realText硬编码user并提供Reply | P1 | 前端Sol | 按真实role展示原文，仅user可Reply；React反例及实际carrier复验 | bfecc9f已提交；Main实际row121复验为Assistant且无Reply，carrier-role-final.json，开发缺陷关闭 |
| R2-F17 | 06 unknown acceptance 不盲重发 | Turn结束后旧op查询被前端active gate阻挡，普通Send可能重复提交 | P1 | 前端Sol | 同一owner保存原turn/op，Check/Send仅查询旧op，明确receipt前不发新请求；生产反例通过 | Main已接收修复及生产Controller证据，30d3135 |
| R2-F18 | 06 Pending 真实失效重取 | singleflight中pending_changed复用旧响应，漏掉在途变化 | P1 | 前端Sol | 唯一owner失效代次，过期结果不发布并顺序重读；生产并发反例通过 | Main已接收修复及生产Controller证据，30d3135 |
| R2-F19 | 06 压缩真实反馈与History | 原生拒绝摘要增长，前端丢RPC结果及warn，没有notice；仅ensureBinding不刷新History | P1 | 前端Sol | 真实summary/lock/error明确反馈，成功发布后按新tip刷新History，保owner草稿；受控与真实补证 | 机制及Main review已接收；真实refused完整反馈、成功12→10且History读到carrier均已补证；角色错误由F20处理 |
| R2-F15 | 06 §0.5/§1.12 命令失败正确反馈 | Controller.stop吞错误后command-actions仍consume输入 | P2 | 前端Sol | 失败保留原owner命令草稿、明确错误；production定向测试 | Main已接收机制，30d3135 |
| R2-F16 | 06 §1.5 Model/Reasoning真实能力选项 | 七档机制已修，但30d3135真实会话仍显示capability unavailable，与原生catalog captrue不符 | P2 | 前端Sol | 定位实际catalog/runtime身份或加载失败，真实菜单/设置回读正确 | bfecc9f已提交；37ce184服务真实七档恢复，high→medium的Current/Effective均回读一致，开发缺陷关闭 |
| R2-F14 | 02 §4.5 C16 合法 cold catchup、§5.5真实冻结前缀 | 5ccc619真实冷恢复事件已准入，parent._session_messages未恢复，spawn前失败无Snapshot | P1 | Core Sol调查/实现，Main集成，V1.6 Sol真实复验 | 原生恢复顺序/正确prefix，单事件不重复，未启用不变；先接缝设计，再定向机制和真实cold复验 | 37ce184已提交；Main接收17机制+21旧恢复复用，并复核新合法cold单event/Child/Snapshot无重复，开发缺陷关闭 |
| R2-F12 | 真实多工具 Turn 的 stream→durable 投影切换 | assistant-ui message index 18 越界（length18），NodeMessage 使整页空白；实际第三次 PDF/JSON请求复现 | P1 | 前端 Sol | 稳定身份/生命周期修复，真实多工具流终态切换无崩溃，不仅error boundary遮蔽 | 实现及源码review已接收，后续真实多工具未再现 |
| R2-F13 | PDF+JSON附件正式提交 | 同一用户消息两附件各显示两次，疑似预测与durable双投影 | P2 | 前端 Sol | 依据真实身份合并，无重复/丢失，刷新前后结果一致 | authored prefix实现review接收，真实后续附件单份 |
| R2-F11 | 06 Thinking/工具卡独立生命周期；多工具真实 Turn | 用户与 Main 实测：旧 Thinking 在后续工具运行时仍显示 running，Turn 结束才统一折叠；工具卡同类风险 | P1 | 前端 Sol | 按每段/调用真实事件与身份独立终态和折叠，保留手动行为；以动态连续观察及事件时序复验 | 逐卡折叠用户确认；空Thinking修复review接收，真实双工具无空卡 |
| R2-F10 | C17–C18；Files 打开 Markdown、长文本与常见文档 | 现有通用 pre 不渲染 Markdown/不折长行，多数二进制无法预览；面包屑含 Files/Parent folder 人工标签 | P1 | 前端 Sol；视觉配合容器 | 成熟本地预览库接入真实鉴权文件；代表文本/图片/PDF/Office/媒体验证；工作区相对路径及根强调色，四视口可用，无第三方文件外发 | 成熟库/边界机制及Main review已接收；真实文档/HTML/音频已验；视频完整播放、最终四视口仍待用户视觉交回后检查 |
| R2-F09 | 06 §0.3–0.4 的 bounded ephemeral state；长期切换多个 Conversation | histories/lives/bindings 等分散 Map 缺统一释放边界，历史投影可随浏览持续积累；当前未发现持久 API 缓存 | P1 | 前端 Sol | 用统一 owner/lifetime 管理当前视图和必要在途状态，其余按需原生重建；连续切换、回看、ACK/断线与草稿归属验证 | 统一owner/lifetime实现及Main源码review已接收；连续十会话/恢复受控通过；必要未决操作元数据保留至明确处理，无持久API cache |
| R2-F01 | 延迟发送/steer/withdraw ACK 期间切 Conversation 或编辑 | owner 草稿可能串线、撤回文本丢失或新编辑被误清 | P1 | 前端 Sol | 生产 controller 延迟 RPC + 切换/编辑反例通过，按 accepted 内容与原 owner 更新 | 机制修复及Main源码review已接收；延迟ACK/切路受控证据有效，真实Withdraw/Interrupt已验；真实断网分支未冒称覆盖 |
| R2-F02 | 分页、live refresh、replay 失败和 snapshot 字段缺失 | 旧页被覆盖，恢复可能卡住或把 unknown 猜成 idle | P1 | 前端 Sol | 保持已加载范围和滚动，竞态与失败可恢复，真实 REST/WS 不重复 | 机制与Main review已接收；真实工具运行中reload及最终单份持久结果已验；truncated/epoch及分页旋转交错保留覆盖边界 |
| R2-F03 | busy Turn 输入 slash、动态 catalog 与 command 结果 | 命令可能作为 steer 发送，通用结果误标 Notebook transient | P1 | 前端 Sol | 统一先解析 slash；依据真实 catalog 与原生行为验证 | 机制与Main review已接收；真实Notebook/compact反馈已验，Stop失败F15已修；各catalog命令不冒称逐一实测 |
| R2-F04 | Files/Photos、历史附件、Edit、大小/类型边界 | 附件分类、历史恢复与明确限制缺少完整证据 | P1 | 前端 Sol | 图片/文件/PDF 正式链路与 Edit 恢复、上限实测 | 机制与Main review已接收；真实图/PDF/JSON、16MiB/超限、Cancel与Edit恢复已验；真机专项不在本轮覆盖 |
| R2-F05 | New Chat 首次 admission 未知 | stored ID 未正确绑定，发送可能永久锁住 | P1 | 前端 Sol | 可查询/恢复实际会话与明确 unknown；不盲重发 | 机制修复及Main review已接收；lostACK/真实locator恢复受控通过，跨reload无持久submission ledger限制保留 |
| R2-F06 | 历史工具/thinking/system、compaction、reasoning | 部分投影猜测状态或遗漏事实，选项未证明后端支持 | P2 | 前端 Sol | 原生真实 DTO 覆盖且 provenance 明确；不捏造选项/状态 | 基本投影机制及Main review已接收；真实成功压缩已补，剩余Reasoning F16与carrier角色F20单列修复 |
| R2-F07 | Files retry、深链边界、消失的恢复目标 | 重试不重新 fetch，路由与草稿 fallback 不完整 | P2 | 前端 Sol | 实际错误后恢复、根目录限制与保草稿 fallback | 机制修复及Main review已接收；真实深层导航/Back to Chat已验；权限/消失目标/symlink错误代表尚无真实证据 |
| R2-F08 | Web Idle Send precheck 后另一客户端抢先准入 | 原生 prompt.submit 按原 busy 模式转换 queue/steer/redirect，违反 06 无隐式兜底；单独前端检查不原子 | P1 | Core Sol + 前端 Sol | 原生现有准入锁内新 idle-only 入口，竞争拒绝且不丢草稿；覆盖 busy/claim 交错及旧客户端兼容 | 后端及前端机制/Main review已接收；真实Send/Rewind通过；跨client精确竞争依生产锁与Controller受控证据 |

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

R2-F14并发补充准入：正式prompt.submit在cold root恢复屏障期间已claim running并写入user，poller却在Agent Loop前消费旧Idle。Main亲读原host admission/history锁与共同timer接口后，准入session_notifications._maybe_fire_tui_noting_idle最小host busy观察接缝，仅eligible/global on；复用原锁/运行与isolation事实，无新owner/持久flag，不改timer/admission。实现者须证明history锁与同步compact/freeze无反锁，保留原失败并定向验证恢复期间及attach后ready前两窗口。非eligible/off行为保持。

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

F16/F20补充证据：frontend/reasoning-recovery/version-and-check-selection.json记录5/5源码、两次定向运行理由及精确命令；当前55 Controller/Timeline＋42未变contracts/theme=97 distinct，不重复累加89。Main已亲审代码与接口接线，真实成功恢复不提前声明。

BE-COLD证据：cold-resume-fix.md§8–9与ignored cold-resume-fix/final-manifest.json；Main核6/6源码报告、23/23日志，17不同新增机制（最终异步16＋压缩定向1）及21原恢复回归，ruff通过，health0阻断/1提示；全部18次canonical运行含失败fixture如实记，非18次大包。旧H04-A真实失败保留，待新合法period开发复验，不冒称已关真实缺口。

WEB-FINAL-F16/F20：37ce184后端＋bfecc9f前端，runtime/reasoning-{high,medium}-final.txt与medium-final.png、carrier-role-final.json；真实设置往返并恢复medium、现成成功压缩carrier按assistant且Reply=false；零新模型/不重做长对话。

V16-F14最终开发补证：v16-handoff-evidence§12及ignored v16-live/H04-F14/proof.json。37ce184，新stored20261012_231154_0e793a，Mainend→due前停机→跨due公开resume，1/1/1、10秒无重复；9/9产品与39/39证据hash Main核实，旧failed3不变。真实Root/ParentUID与toolpin一致，Child逐请求payload缺失及两次越权调用被拒如实保留。只补该周期，未重复H02/H03/H05–H08。现在按C24门禁前交接，后续先视觉合并再独立门禁。

## 2026-10-13 视觉交回后集成包

- R2-C31为本次最新停止边界：完成开发集成与阶段提交，在派遣Verification之前交接；不自动进入Astra门禁。
- F21：Enter只Send/Steer、Escape取消类；功能仓实际组件验证。
- F22：500 MB合计附件预算替代16 MiB单文件；已有草稿+新选项合计判断，删除释放；完整实际上传与原生引用/提交需证据。
- F23：视觉finished无回闪、Interrupt先收拢再涨入、顶部持久toast；worktree收尾及四视口、中间帧取证后Main合并并正式接线。
- 历史16 MiB上传证据仅证明旧边界，不再代表交付上限；同源其他路径沿已有证据复用。

## R2-F22 · 合计附件预算与真实大传输：Development 完整阶段交回（2026-10-13）

本节由附件 owner 追加，仅记录 F22；待 Main 亲自 review / 集成，**不是独立 Verification 或 Validation 结论**。七项交回如下。唯一详细运行证据入口为 ignored `.hermes-dev/round2-evidence/attachment-budget/manifest.json`；不提交合成大文件、运行库、配置或凭据。

### 1. 对应条款与现行依据

- 用户 R2-C30 与现行 06 §1.7（202–204）：当前草稿的**所有附件合计 ≤ 500,000,000 bytes**，选取时包括已有项；duplicate-name occurrence 独立，删除释放预算，撤销旧 16 MiB 单文件限制。单文件刚好占满预算也允许。
- 06 §0.3–0.5、§1.6–1.11、§3.5、§4.5–4.7：薄客户端、本地只保存未提交草稿、选择不上传、只在 Send 上传、原生引用与真实 Agent 可读、Cancel Send 不提交、原生协议兼容与真实失败如实记录。
- Core 02 §5.12 Target 未修改；profile 隔离、未启用原生不变、原生模型/provider/锁与提交接缝保持。
- 索引冻结基线 `37ad76f5dfac02d4774d5e0faea55911b5fb8de9`；本阶段 backend/frontend HEAD 与实际源码 hash 见 manifest。新增预算是用户明确授权的冻结例外，不覆盖其它规格。

### 2. 实际变更及原生审计

前端 owner 修改：`src/core/attachments.ts`、`src/core/drafts.ts`、`src/core/contracts.test.ts`；新增 `src/api/attachments.ts` 与附件 transport 定向测试。`sizeBytes` 只来源于真实 stat；选择 Blob 直接以 `blob.size` 为事实。`attachmentBudget` 对全部 occurrence 累计；未知尺寸保留引用但阻止新增/发送，不伪造 0。按选中顺序准入，超额项拒绝，已有项保持原 ID 和顺序。

后端 owner 修改：`tui_gateway/prompt_attachments.py`、`tui_gateway/methods_prompt.py`、`tui_gateway/contracts/prompt_voice.py`；新增 `tests/tui_gateway/test_file_attachment_chunks.py`；按 Python 契约重新生成两份 shared TS/OpenRPC 文件。

容量反例：原 `file.attach` 普通文件没有 25 MiB 原始 cap，但现有整包 base64 500 MB 会产生约 666,666,668 个字符；当前 Node/V8 `MAX_STRING_LENGTH=536,870,888`，现 Dashboard WS limit 为 `384*1024*1024`。原 `/api/files/upload-stream` 属另一 managed-file 写权限/根，且 100 MiB cap，不通过放宽该路径解决附件问题。Main 接受沿既有 `file.attach` 的 optional 分片和 metadata-only 增量。**没有新 RPC 方法、上传 API、BFF、数据库或服务**；没有调大 WS limit，没有改 legacy image/PDF cap 或原生 provider。

新增 optional params：`upload_id`、`offset`、`total_bytes`、`abort_upload`、`metadata_only`；optional result facts：`upload_id`、`received_bytes`、`size_bytes`。旧 `path/data_url/name` 调用形态和原结果语义保留；progress 为 `attached:false`，path/ref 字段为空，末片才返回可提交引用。

### 3. 正式路径、owner 与失败机制

- App Files、paste/drop 仍共用 `selectAttachments`；Attach 只更新当前草稿，未在选择时上传。Controller 正式接线由 `web_logic_finish` owner 实施，我未写其白名单文件；对应源码 hash 也纳入 manifest，具体 87 个控制器/React 定向用例由该 owner 交回，Main复核，不由本 owner 重跑。
- `Controller.stageAttachment` 对 file/image Blob 都调用 `stageBlobAttachment`；≤4 MiB 沿旧 `file.attach(data_url)`，更大逐片 4 MiB，片 base64 字符串约 5.59 MB。最后原生 ref 进入 `prompt.submit_idle`；图片仍进入原生 explicit image_paths，未改 legacy image/pdf 方法。
- 客户端随机 canonical UUID 为 upload occurrence；服务端以 **session 内 map + 原生 `history_lock`** 为唯一 owner。总量/非负 offset/每片长度先验证，任意路径式 upload_id 拒绝。每片真实写成功后更新 offset。跨 session 即便同 UUID 也不共享状态；落盘根继续由 session profile/workspace 原生 helper 决定。
- 最新已收片的 offset+SHA256 与 total/name 相同则直接返回同一 progress/final result，丢 ACK 重发不再次 append；错序、旧片、变更元数据、超长或溢出片拒绝，不破坏已有 bytes。完成后用同一原生 filename allocation 序列独占 hard-link 发布完整文件，临时路径不成为引用。
- `stageBlobAttachment` 遇 `IndeterminateError` 仅重发相同片一次，拿到精确 received_bytes 才推进；不盲目推进偏移或提交。每片前后读同一 tx.cancelled；不完整结束 finally 尝试 `abort_upload`。已完成 staging 的 residual bytes 不撤销、不自动提交。断线/崩溃/进程重启可能残留 `.file-upload-*`，V1 不承诺持久续传或跨崩溃清理；重启丢失 runtime upload owner 后非零起始 offset 明确拒绝，草稿仍可恢复。
- 历史 Rewind/reload 引用由 `metadata_only:true` 做纯 stat；不 copy/write/stage，也不开始 Turn。路径解析锚定该 session cwd，与该 profile 的 attachments/images 合法根；symlink 逃出根拒绝。远端 cwd 不拿同名 host 路径冒充，缺可靠事实就保持未知/阻止发送；已暂存于 profile 本地附件根的文件仍能 stat。
- Controller 引用 hydrate 接线按 key/revision/generation 防晚 ACK 污染其它 route；发送在正式 upload 前**重新 stat 全部无 Blob 引用**，随后总预算验证，不能因为已有缓存 `sizeBytes` 而接受外部增大后的文件。当前已有 overLimit 快速拒绝发生在这一准备步骤之前；重新恢复/删除仍可更新草稿。

### 4. 验证结果、命令与真实证据

仅针对本任务执行小包，没有自行全量门禁。精确日志见 manifest 索引。

| 执行 | 范围与结果 | 次数 / 耗时及说明 |
|---|---|---|
| `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/tui_gateway/test_file_attachment_chunks.py tests/tui_gateway/test_file_attachment_allocation.py tests/tui_gateway/test_attach_does_not_wait_for_agent.py tests/tui_gateway/contracts/test_generated.py -q --basetemp=...` | 22 pass / 1 fail；生成一致性 pass；catalog 仅已知 `review.summary` 孤立事件 fail | 初次 4.0s；显式同一 basetemp 被 per-file 并行共享导致两个 fixture 初次波动，runner 自动重试后通过。原失败/重试均保留，不改检查规则 |
| 后续 canonical runner 同 chunks + attach-does-not-wait，无共用 basetemp | 17/17 pass，无 fixture 波动 | 1次 2.6s；纠正运行目录用法，不改测试产品行为 |
| canonical runner `test_tui_gateway_server.py -k file_attach -q` | 7/7 legacy file.attach pass（runner发现645估计值，但实际只运行7项） | 1次 1.2s，非645项大包 |
| `npm test -- src/core/contracts.test.ts src/api/attachments.test.ts` | 最终46/46 pass；累计预算/删除/未知引用，真实 helper 小包串行、取消、丢ACK重复参数、精确最终ref | 最终1次0.401s。此前 transport 4例首次因 Node 无 FileReader 失败；改为 jsdom 环境后5/5 pass，再在最终类型收窄后重测46，无额外机制变更 |
| `npm run typecheck` | pass | helper端口最初泛型 mock 类型不兼容，收窄实际 `Promise<Json>` 请求合同后最终pass；日志保留 |
| 指定4个Python文件 Ruff + 既有 scoped health ratchet | Ruff pass；health 0 blocking / 0 advisory | 只审本 owner 路径，未更改阈值/规则；两仓指定文件 diff --check pass |

后端**30个不同已通过用例**（12 chunks + 4 allocation + 6 attach-not-wait + 1 generated一致性 + 7 legacy）；17项复测与 runner重试不另计。catalog 失败不能算通过。前端本 owner 46 项与逻辑 owner 87 项按各自报告去重复用，不能直接相加当全项目计数。

真实运行：官方 PM `.venv`，独立 `dashboard --host 127.0.0.1 --port 53447 --no-open --isolated --skip-build`，profile `.hermes-dev/round2-attachment-live`，前端5177代理53447；未操作53445/53446，未改另一 Dashboard。启动首次未加isolated而被host-owner拒绝，未停止既有owner，修正为已有正式隔离模式。凭据仅复用获授权本地环境，复制本体只在ignored profile。浏览器全部用CUA，独立tab，不改变共享viewport。

| 真实操作 | 证据与实际结论 |
|---|---|
| 选完整500 MB，不Send；追加1 byte；reload | `selection-no-upload.json` 服务端附件目录不存在；`browser-over-budget*`、`browser-reloaded*` 与后续正式发送证明500MB Blob恢复，新增1byte不进入草稿，原项未丢。当前普通错误toast展示仍待Main App接线，不能声称视觉反馈已完成 |
| 单500 MB实际Send / native refs / 真实Main | `single-500MB-proof.json`、`browser-first-result*`：stored `20261013_023020_8f37c0`；完整file=500000000；源/服务端SHA256均 `3bb68020b349b7006065e8d8218a1c1e8a34824e05d5f68d98f13cce61f6bf18`；点击Send→落盘约6.918s。原生binary Attached Context明确不inline正文；真实DeepSeek Main通过原生terminal读取head64/tail64，回报 `F22_HEAD_CEDAR_500MB`、`F22_TAIL_BLUE_ORCHID_500MB` 与stat500000000。持久tool/result/final rows保留，不拿ACK冒称理解 |
| 历史引用恢复、重载、删除 | `metadata-native-response.json` 真实 `attached:false,size_bytes:500000000,uploaded:false`；`browser-reference-{over-budget,reloaded}.dom.txt` 引用与稿留存；删除后 `browser-delete-releases-budget.dom.txt` 1byte立即准入。没有copy/stage/新Turn |
| 两个同名250 MB / 合计500 MB | `browser-pair-before*` 两个同名chip，不由Composer改名；`pair-500MB-and-cancel-proof.json` stored `20261013_023449_f5a878`。native路径 `same.bin/same-2.bin` 各250000000，源/服务端SHA分别一致：`433f5df8845deca44ad859520a3010f3ba115a589030e9bcaa155ef59750151d`、`41fad0103aaa299914b0c648e2086d7f110dde42dccaf0ebf5b2d5c968965fa2`。真实Main terminal读到了 ALPHA/BETA 头标及 END_ALPHA/END_BETA，各自stat250000000，证明独立内容，无吞500MB正文 |
| 真Cancel Send | 第一次跨CUA调用追赶取消未赶上（按钮已经消失），仅记未执行，不算成功。后用同批Send→DOM→Cancel Send→DOM实际点击成功；`browser-cancel-{before,after,final}*` 最终Send可用，完整500MB chip与 `F22_CANCEL_SHOULD_NOT_SUBMIT` 原文本保留。`cancel-final-proof.json` 取消标记user rows=0，附件目录仍仅3个完整文件、无partial。取消前后既有framework user-role row不当成新增实际用户输入 |
| 实际内存 | `memory-samples.json`/summary，0.5s名义间隔、809样本。独立backend PID30834 sampled RSS peak342589440 bytes（326.7MiB）；共享Codex renderer总RSS sampled peak1790066688 bytes（1.67GiB）。CUA readonly DOM scope不暴露performance.memory，renderer包括App UI与其它页面，因此明确**不是本页独立JS heap / 保证精确峰值**。实际1GB合计两轮传输均完成且未OOM |

最终亲审追加一项新参数负例：仅提供 offset/total/abort 控制字段而漏 upload_id 明确5028拒绝，不能退回legacy write。canonical runner当前12 chunks + 7 legacy＝19/19通过，1次2.0s；Ruff/health最终再核通过。真实500MB服务仍加载这项最后负例保护之前的源，具体6文件hash保留在 `live-source-before-control-guard.json`；最终只新增上述错误输入拒绝分支，正常UUID/metadata/legacy成功路径不变，沿前述实际大传输证据复用，不冒称服务已热载新分支。后续Main统一重启。

### 5. 当前缺口和保留限制

- **Main集成依赖**：Controller 已将普通notice写入notifications，当前 App 尚未消费 ToastStack；真实超预算选择已拒绝但无可见toast。合并视觉并接栈后，只需对保留的500MB取消草稿再次选1byte补“错误可见”证据，不重传大包/调用模型。
- 未声称跨平台、真机拍摄/键盘或500MB图片模型推理已验证；本轮真实上限传输用ordinary binary文件。原native image/PDF方法的限制保留。
- remote workspace没有已有可信stat通道时返回未知并阻止新增/发送，这是保护真实预算而非用本地文件冒充；远端专项未验。元数据仅stat事实，不保存API业务缓存。
- 丢ACK由真实正式handler重复请求、并发重复片与production helper拒绝/重试机制测试取证；未伪称人为实际断网的浏览器ACK丢失全过程。已完成真实全包传输与Main读取不依赖此模拟。
- crash/断网可残留暂存bytes，V1不保证清理；该次真实Cancel确认无残片。不承诺跨进程续传。
- catalog既知失败与首次测试环境失败保留，尚未本轮完整独立门禁。

### 6. 接口影响与交接

仅为既有file.attach增加optional能力和真实size字段，生成合同已同步。小文件和legacy clients保持原形；大文件需要支持分片的本轮客户端。Controller/App归其它owner：本 owner未修改 `controller/command-actions/ChatComposer/App/design/mock`。Main需亲读Controller tx owner/epoch/key接线、所有新server helpers与legacy上下游，不能以重跑上述有效测试代替review。

服务53447与前端5177暂留供Main最终toast补证；其PID、源码hash、profile和证据见manifest。Main在补证/集成后可只停止这两个任务实例。测试数据可清理但仅限此任务自建profile/fixtures，不动其它验收库。

### 7. 建议后续动作

Main集中review → 合并视觉并在App接ToastStack → 当前保留500MB取消草稿选1byte取得可见拒绝 → 统一阶段提交与native服务版本更新。无需重做2轮500MB传输、模型理解或旧16MiB上传；只有实际上传/预算接缝变化或证据存疑再定向复测。之后按本轮既定完整Verification→Validation执行，F22本节作为开发证据输入。

## Main最终集成审查与用户现场修补（2026-10-13）

- Main已亲读最终接线9个文件及通知、任务完成、Pending、标题、滚动相关上下游，9/9owned、6/6依赖、21/21证据hash匹配；接收48受影响React例、最后13＋native6定向、Mock20一次和构建/冻结health0/0。未复跑Controller88、附件46/后端30、大上传或模型。
- R2-C32/C33：Reminder合为蓝色标题＋右侧箭头，展开正文直接在同bubble；Parameters删除JSON额外label及内层框，直接pre/code，横向滚动和深色底保留。正式/Mock/用户查看中的visual worktree已最小同步。
- R2-C34/C35：工具正文左右16px；Result单独max-height=10em×1.65，溢出自动滚动，原卡片背景，无深色文本框。390视口真实DOM：Result max247.5px/line24.75px=10行、背景透明、左右16px、JSON额外标题0。
- ignored `main-final-integration/` 是本次Main证据入口；`parameters-390-proof.json`记录324px参数内容/564px滚动宽，`reminder-proof.json`记录标题展开、正文直接child、无嵌套box，`tool-result-proof.json`记录十行高度与留白。浏览器read-only沙箱不提供parseFloat，第一次取证算比值报错；改在工具侧计算后完成，未改页面或假造几何。
- R2-C32/C33后已typecheck/build成功、冻结health0/0；后续C34/C35是CSS/容器小修，最终构建只在收尾稳定包补一次，不重做模型/大文件。
- 5177真实1byte超额toast及完整500MB草稿保持、跨route保留/显式dismiss、Orb最终0ghost复用owner原始proof，Main已读。未把360ms中间帧1ghost当最终泄漏。
- R2-C31本次严格在Verification派遣前停止；全部开发证据仍不构成独立门禁通过。R2-C36只追认明确列出项，压缩32及结束8轮窗口保留待定。

Main前端最终快照611b734；visual用户查看树86fa280保留全部既有untracked成果，仅提交本次3个明确修补文件。最终C32–35后的build-delivery.log/health-delivery.log通过，health0/0；没有因接收报告重跑88、46、30或既有97。后端原生preflight在53445/53447均无活动session，原服务版本37ce184/7fea3f5，供安全统一重启依据。

最终稳定窗口：后端产品5ba0481、前端21aad02；源tool_name薄适配、无参数结果行删除空框、已读取Current Reasoning传Composer，正式浏览器现成工具卡片证实terminal名称/Result透明/16px/247.5px高度；54个受影响contract＋presentation例1.20s、最后build/health0/0。三屏各四视口new/conversation/files JSON及JPG全部保存；页面无横溢、320 drawer→Files→Back回原会话。源端首次预检错用session_id为4000，保存native-preflight-wrong-read-params，改stored_session_id后Noting idle；不抹去诊断失败。没有新模型或大包重传，本次按C31至Verification前结束。

## 用户自测后整改（R2-C38–C60，当前执行）

范围与动态Owner唯一看根CLAUDE现场整改总看板R01–R11。各owner先落排查报告，Main集中读取后已派三项明确修复：原视觉合同恢复、history/live顺序与及时呈现、原生Steer插入事实和精确持久映射。工具／附件／选择器／Noting报告已接收；不继续追历史责任或重复500MB/旧全套证据。

本次Main新增实际证据在ignored `.hermes-dev/round2-evidence/main-final-integration/repair-*`：Model/Reasoning当前项高亮及无Current行；真实历史附件正文移除与同工具双分区；真实Noting idle/Memo0。用户旧页HMR遗留断连尚未刷新，Main独立新页连接正常，待统一native新版本后验证断线保状态。用户授权任意必要真实DeepSeek调用；最终新Turn/Steer/像素/流式/usage/视觉收尾实测仍未完成，阶段未闭合；严格停在独立Verification派遣前。

整改最终接收：原生产品4443aa7/前端c55120f/visual fc18614，R01–R13开发期闭合与具体证据/失败边界见final-delivery当前章节；根CLAUDE唯一动态总表已更新。新增Main实际会话122700_433f46：像素73729、连续Tool/Steer/Usage、Notebook固定位置/刷新、单确认Rewind、exit7 Failed；actual服务停启确认状态保留+token自动恢复。最终build/types与冻结health0/0；同版本有效包按报告并集复用，无全套/两门禁。


### 2026-10-14 夜间托管最新执行覆盖

- Main：亲审前端及C84产品差异/正式接线；自行最小Prompt与用户原话对账；集成快照、证据接收和资源控制。Prompt原Memo不动，硬清理gate不实施。
- frontend owner：真实新附件RPC/模型及Instant→WS→内置浏览器DOM代表链；用户Chrome禁用；资源自查后重任务仅Main安排一个执行方。既有有效测试/性能证据复用。
- cleanup_mechanism_proposal：单文档只读研究，不改产品/Prompt/测试/服务。涉及额外清理类型、统一同步机制、forced/overflow及下一轮义务承接均为待审提案。
- Core owner：C84交回/33distinct机制证据复用，Main亲审尚未完成；当前仅资源轻量复盘。
- prompt_review_v3：用户要求停止，只有用户另要求的资源自查，不继续Prompt任务。
- 重任务并发：浏览器/真实模型/构建/测试先暂停，资源审计后串行安排，不为已交回有效证据复跑。不会停止用户进程。
- 停止点：本轮授权开发/联调/阶段提交完成后交付；第二轮Verification不启动，也不把本阶段写成整轮独立验收通过。


### Main阶段集成验证与续接（2026-10-14）

C84/BE附件/Instant三机制包与前端完整整改包已亲审；Main只补Prompt相关真实spawn/prefix用例、active Usage新有效数据行为与当前build。日志/失败修复见各owner报告新Main段，不重跑全包。staged footguns/ruff/health当前pass（0阻断、未改文件既有HX012提示1）。当前唯一重任务执行方native_integration，旧附件真实模型terminal证据复用；IAB现真实可用，须关闭旧报告能力阻塞并取得新的实际链，旧Chrome不是新IAB证明。Main负责stage快照/接线，不启动第二轮Verification。


阶段快照：BE/依据/报告 `f8e416178ecf24021c614940052561f30dc7929d`；FE `aacb6e9`（已ff primary main）。Snapshot不表示新的Verification通过。后续只补native_integration返回与必要运行版本接线；Main不得重跑已交回有效包。当前用户服务兼容版本核对未完；需要保持原正在用的Conversation/profile/库，不迁移或静默清库。


### 夜间最终交接（2026-10-14）

当前BE产品f8e4161，FE正式main/修复树8b3867e，origin/secretary已同步；post-commit真实自动推两次feature提交，主repo最后文档/hook快照已同机制推origin/main；两仓库本地/远端hash一致。用户运行53445同旧HOME/config/DB安全更新为PID20193，5173 HTTP200，新RPC注册只读探测4001非not-found，active_count0。C84正式机制和实际3个新Noting链均收回；Main记录API in45s原生拒绝后模型改1m，不伪造精确秒成功。

C99两正式Timeline组件用例pass、当版build pass；末次GUI实看被IAB浏览器安全策略明确拒绝，协议理由与http请求不一致，但禁止任何绕过。旧真实IAB source153→DOM21ms→Thinking157→complete313/DOM15ms与唯一UID证据有效；C99最后实看留明早正常UI操作，不冒称通过。清理07单文档已Main亲审，全部硬范围/M27/恢复设计未实施，用户明早审核。最终交付结论和限制见final-delivery.md；不再开第二次Verification或独立Validation。


### 用户重试与最新侧栏截图修复（2026-10-14）

C101正常IAB重试成功；原真实Instant行折叠/展开保timestamp/单卡/再折叠实际通过，native报告§12及c99-retry证据。临时服务退出、原配置逐字恢复、DB/Registry/API计数无变化，无模型重跑。C102用户截图指出Files/Appearance宽胶囊迁移遗漏，sidebar_visual_restore直接干净UI main修局部CSS，Root不并行改UI、原visual-design只读，Root唯一正式5173 IAB验收。原因：正式全宽appearance wrapper改变ThemeSelector原grid item收缩布局。两独立门禁不启动。


最新结束状态（C104）：C99实际IAB补验已完成；C102侧栏胶囊宽度修复/Main实看完成；临时文案经用户明确撤回，最终UI main2c019ac与已实看43795c8树完全一致，auto-push成功。原目标的Main集成与交付记录收尾，不再展开视觉或重复有效测试。两独立门禁未启动；单文档硬清理待用户审核，未实施。


## 2026-10-14 用户继续授权：压缩与运行闭合

用户原话：“我审Prompt，你继续干活啊。你不是说没干完呢吗？”本次继续已有范围，Prompt仅提案；第二轮Verification仍不启动。

| 整改项 | Owner | 完成条件与定向证据 | 状态 |
|---|---|---|---|
| 全部压缩完成边界到真实Timeline | compaction_timeline_audit | 消费原生compacted，统一状态/Usage/force历史读取，实际UID无假卡，scope/epoch正确；focused及真实IAB | 实施中 |
| 原生operation开始/phase/完成顺序 | compaction_backend_audit | owner建立后可被Context真实读取，compacted在真实发布后，避免手动首次false竞态；最小runner -j1 | 亲核必要接缝 |
| 正式运行新后端与Noting notice | Root | 确认真实Main/Noting全idle后同HOME/DB/config安全更新，原生notice既有事件链 | 待集成 |
| Usage/侧栏/Compact/notice实际页面 | Root | IAB核真实冷恢复Usage、idle不清、scroll无条、同位loading仅Cancel及普通10秒/错误永久策略 | 待闭合 |

复用df123c6/d4896f2定向测试及唯一统一build，不复跑旧包。新相关测试串行放行，采PID/RSS；各调用短输出，不批量展开长规格。禁止模型并行、服务多开、真实浏览器和任何Prompt代码变更。

## 2026-10-14 用户审定后集成续接

用户已授权应用独立 Prompt 审阅稿；“仅提案／不得 Prompt 代码变更”的前次限制已被本次授权替代。开发阶段缓存失效与原生重建属于正常结果，不追加旧措辞保护逻辑。Root 保持唯一服务与 IAB owner，任务继续至相关测试通过、实际集成完成，第二轮 Verification 不启动。当前动态编排和待完成项以根 CLAUDE 为准。

可复用交回：时间 9a816c06 的 102 distinct 用例；Notebook visibility f0750bdd 的四条正式模型消费路径；BE Total 32418ea 的 12 用例；UI Total/缓存率 55d483d/a9723d2 的 26 最终用例；UI Info/底边 ab1f4c4 的两项 focused。Root 最终 UI typecheck 1.72 秒/RSS568.6MiB，build7.88秒/RSS1.31GiB、零swap（既有chunk提示）；不重跑上述包。Prompt 包88通过、两项失败及定向修复记录见 completion-integration/prompt-integration-tests.log。桌面 New Chat／Conversation bottom=671、增高仍671，底部胶囊栏=707；移动 viewport API 未改变真实尺寸，标记未覆盖，不能算移动通过。
