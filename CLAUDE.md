# Hermes Secretary 第二轮主看板

## 自主口径收敛 · 待用户追认

> 本区域按 AGENTS.md 永久维护；无待追认收敛时注明“暂无”。

| 原规格空白 | Agent 自主收敛／理由 | 影响范围 | 实施情况 | 用户状态 |
|---|---|---|---|---|
| 新增Pending occurrence与Interrupt查询回执要求稳定但无有限保留/容量具体值 | 同原生owner内存保留当前epoch至多256个Web提交回执、64个Interrupt操作；最近8个已结束epoch；超容量明确拒绝，过期明确unknown，避免无界内存且不捏造查询成功 | 仅新增Web精确Pending接口；legacy steer无新容量限制；重启本就不保证live receipt恢复 | 已实施；Main 集中审查接收 109 个不同机制/原生回归用例，真实 Withdraw/Interrupt 已通过，容量/过期仍仅机制证据 | **Agent 自主收敛／待追认** |
| 压缩操作终态查询未指定有限保留条数 | 每个原生 Agent 仅在内存保留最近 32 条压缩终态；超出窗口的操作返回 no_active，不推断过往成功 | 仅新增压缩观察/取消 RPC；不改原生压缩记录或执行 | 已实施并通过相应机制验证；Main review 接收，真实 UI 待联调 | **Agent 自主收敛／待追认** |
| 06 要求附件上限实测，未给出具体大小 | 前端暂以单文件 16 MiB 为选择上限，超限在提交前明确提示；已实际验证原生上传边界 | Web 图片和普通文件选择；不改变后端或旧客户端能力 | 精确16 MiB二进制实际上传并完成Main；16 MiB+1在前端拒绝 | **Agent 自主收敛／待追认** |
| Idle Send 的前端确认与原生 prompt.submit 之间，另一客户端可抢先准入，原接口随后会 queue/steer/redirect；06 禁止这些隐式兜底但未指定原子拒绝接口 | 在既有原生准入接缝增加最小 additive idle-only 提交入口；竞争后明确拒绝并保留草稿。复用原执行与原锁，不新建准入 owner/队列，不改变旧 prompt.submit 协议 | 新 Web 普通 Send 的竞争边界；Rewind 仍保留原生双确认/拒绝语义 | Main 源码反例确认并准入；T3c 设计已由 Main 源码审查接收，prompt.submit_idle / busy 4009 契约定案，Main 已审查接收实现与机制证据；真实 REST/WS 与 Send/Rewind 已通过；并发拒绝保草稿仍按机制证据 | **Agent 自主收敛／待追认** |
| 原生 image.attach 跨连接未完成时，断线后的 image.detach 可先完成，旧请求随后仍追加图片；06 未指定可证明安全的取消上传机制 | 新 Web 图片用原生 file.attach 取得路径，再由 submit_idle 显式传入本次 image_paths，复用原生图片执行参数；新请求默认空列表，不消费其他客户端共享图片暂存。取消/丢上传 ACK 最多留下普通文件，不使后续 Prompt 夹图 | Web 普通 Send/Rewind 图片绑定；普通文件仍用原生 ref_text；旧 prompt.submit/image.attach 语义保留 | Main 已亲查正式 inline 与 compute-host 两条接缝，Main 已接收显式图片实现、19 个不同图片用例及旧入口负对照；真实图片通过原生 vision_analyze 正确识别；Cancel Send未提交并恢复原草稿 | **Agent 自主收敛／待追认** |

本轮已确认口径的授权来源见 [Snapshot Index](.autonomous/20261012-round2-web-ui/snapshot-index.md)，不得将 Agent 安排或推断写成用户确认。

## 当前目标与阶段

最新用户口径 R2-C10 已写入 AGENTS：以同一 owner、统一判断点、同步临界区和正式提交点保证不变量；Main 据此复核当前增量，避免下游堆叠门禁。

第二轮交付独立 Secretary Web UI，并完成 V1.6 移交缺口及本轮实际变化影响的验收。当前为 **前端阶段快照 27c5cb4 与视觉 worktree 已交接；T3/T4 后端快照 5ccc619 已进入真实联调；T2 空 Thinking 继续整改，T5 冷恢复真实缺口 R2-F14 处理中；尚未进入独立门禁**。用户授权在冻结前精简三份核心文档、最小修订新版 06；冻结后本轮不再修订权威规格。

- 后端工作区：`/Users/edgar/code/hermes-secretary`，继续按原生接缝实施必要增量。
- 前端：并列本地仓库 `/Users/edgar/code/hermes-secretary-web`，`main`、无远端；React 应用已启动并通过基础导航冒烟，仍在整改和补齐功能。目录名属于实施安排，不是用户逐字指定。暂不上传远端。
- 过程计划、依据、协调、审计与验收证据全部留在本工作区；前端不建立并行过程看板。
- 范围只含 06 Web V1、必要原生后端增量和 V1.6 移交验收；不含 Memory Provider 或云部署。

规格顺序：现行 [02](docs/02-noting-system-specification.md)（含 V1.6 已确认修订）→[04](docs/04-hermes-secretary-v1.5-implementation-spec.md) 未被覆盖的增量→[01](docs/01-personal-hermes-v1-first-fork-iteration.md) 继承要求；显式 Web 增量以 [新版 06](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md) 为权威。旧 UI 讨论保留来源角色，不能覆盖新版 06。

## 本轮已确认口径与授权

| 范围 | 已确认口径 | 来源 |
|---|---|---|
| 托管 | 用户要求挂载目标，持续推进至最终交付；必要时显式 wait 子 Agent | R2-C08 |
| 文档与冻结 | Ask and Align 可最小修订 06、精简核心文档；冻结后不改权威规格 | R2-C01、C07 |
| 协作 | Astra 技术负责与集成，Sol 具体开发，独立审查与视觉权限分离；按完整阶段交回集中 review，无必要工作时主会话等待 | R2-C02、C07 |
| 双仓库 | 前端独立并列本地仓库，后端及全部过程文档在本工作区；无前端远端发布 | R2-C03 |
| V1.6 | 实现立即提交；收尾移至第二轮验收，不重做旧轮全量 Verification，只补缺口和实际变化影响 | R2-C04 |
| 验收 | localhost 内置浏览器，桌面 1440×900 / 1024×768、移动 390×844 / 320×568 全部强制；小屏布局、操作与视觉完整 | R2-C05 |
| 真机覆盖 | 软键盘、相机、系统侧滑后续专项验证；功能仍实施，本轮不冒称真机覆盖 | R2-C05 |
| 模型 | 已配置 DeepSeek，用户明确当前 V4.1Flash 支持视觉；Main/Noting 与真实图片验收沿用配置和原生 provider，不另换模型或新增路由 | R2-C06 |
| 品牌素材 | 用户原图位于前端 public/assets/hermes-secretary-icon.png；仅替换标签页图标及 Claude 主题 New Chat Composer 上方标题栏左侧十字花，其他位置默认不额外使用 | R2-C09 |
| 最新视觉纠正 | Usage/Context 悬浮、不另占底部高度层；New Chat 仅 5–6 句轮换标题，无副标题；先调布局与层级，主题色待用户提供，蓝灰色仅辅助 | R2-C11–C13、C15 |
| 深浅主题 | 完整 system/light/dark；侧边栏底部三图标滑动胶囊，无可见文字；默认系统，本机保存显式选择 | R2-C14 |
| New Chat 统计卡 | 不显示 Usage 和 Context；两卡仅在实际会话页面展示 | R2-C16 |
| Files 预览与路径 | 使用成熟库呈现常见文本/非文本；真实工作区相对路径，根名称强调色，删除 Files/Parent folder 人工标签 | R2-C17–C18 |
| 视觉交接 | Astra 视觉设计 Agent 已结束，不再操作；成果保留，用户另行委派设计。Sol 继续交互、卡片骨架和功能，Main 回归全局接线与审查 | R2-C19 |
| Mock / worktree | Sol 构造复用正式组件的全场景静态交互 Mock，再创建前端独立视觉 worktree 供用户另行设计；Main 并行推进逻辑工作 | R2-C20–C21 |

## 编排与修改边界

| 角色 | 模型 / 推理 | 职责与边界 |
|---|---|---|
| Main / Integration | Astra high | 全局目标、要求覆盖、技术决策、委派、亲自 review、正式接线集成、微小明确修补及最终判定；不承担唯一实现人角色 |
| Development | GPT-6.1 Sol high | 指定白名单内具体前后端实现、相关测试与完整阶段证据；不扩大产品语义、不再派生 |
| 独立 Verification | Astra high | 全新无上下文审查者先从冻结规格建立判据，再核实现、接线与证据 |
| 独立 Validation | Astra medium | Verification 通过后由全新无上下文验收者操作真实入口，检查用户输入到输出 |
| 视觉设计 | 原 Astra medium 已按用户要求结束；后续用户另行委派 | 保留既有成果和未验项；不再由原 Agent 操作。Sol 继续已确认交互/卡片骨架及必要接线，不自行定案新主题 |

当前活跃委派：`web_frontend` 处理空 Thinking 与局部代码健康；`v16_gap_evidence` 独占 53446 真实移交补验；`native_compatibility_audit` 调查 R2-F14 冷恢复，先交接缝设计。`static_mock` 已完整交回 96 场景、16 合成文件、20 定向测试和构建证据，Main 已验证工作台并创建视觉 worktree；`web_frontend`（Sol high，前端整改与接线）、`web_usage_projection`（Sol high，T4b 已完整交回，Main 已审源码/上下游/23项机制证据并接收）。`native_compatibility_audit` 的 T3c 已完整交回并经 Main 集中 review 接收；已完整交回 T3a，30 项新机制及 79 项原生回归有效通过；Main 已固定源码证据、核对 13/13 hash，并集中审查 owner/插入/终结/原生准入/关闭与实际 Loop、SQLite 测试后接收。T3c 报告列原设计 15 项、图片边界 19 项、旧回归 66 项及 typed Stop 2 项；不将重叠证据简单加总为独立用例，Main 已亲查准入/临界区、alias 绑定、ContextVar 释放、inline/compute-host 图片传递、原生忙碌兼容及完整测试；5/5 源码、4/4 注册生成物、14/14 日志 hash 相符。`web_backend_reads` 的 53 项机制证据及 12 文件 hash 已由 Main review 接收；`web_visual_system`（原 Astra medium）已按 R2-C19 结束并 interrupt，不再操作；当前四视口欢迎页与浅深移动侧栏六张完整截图已独立审图接收，Files/菜单/Conversation 浮卡和最终色系仍未验。成果与未完成项留在 visual-design.md，用户另行委派视觉。Sol 可继续已确认交互、卡片骨架及必要 design 组件接线；不继续自主纯视觉重设计。独立 Verification Astra high、Validation Astra medium 分工不变。白名单与精确章节/行范围见 [plan.md](.autonomous/20261012-round2-web-ui/plan.md)。主会话集中审查完整交回，不盯零碎 diff。

主题色暂不定案，原 Astra 视觉 Agent 已结束；保留现有布局与颜色候选，等待用户另行设计。New Chat 两统计卡已移除并取得四视口图像证据；Sol 继续交互/卡片骨架与功能接线。

## 任务看板

| 任务 | 状态 | 完成条件 / 下一步 |
|---|---|---|
| V1.6 实现提交与移交 | 已提交，验收未完 | 产品收尾提交 `edd031f551`；记录提交 `6c3659bdf8`；不得重复处理产品提交 |
| 本轮规格与核心文档对齐 | 主会话 review 接收 | 06 优先级、分工、双仓库、四视口与覆盖边界已同步；规则与历史入口保留 |
| Snapshot / 文档基线冻结 | 已冻结 `37ad76f5df` | 三份核心文档、06、索引与报告模板同批提交；规格本轮一级不可修改 |
| 技术审计及实施计划 | 审计完整接收；计划已执行 | 30项N/F/A/D、DTO和源码反例已审；最终新方法名称见native-compatibility §11；具体增量按owner实施 |
| 前端仓库与设计系统 | T1 组件初版review接收，正式接线/四视口未完 | 设计按 06，功能施工主要交 Sol；无远端发布 |
| Web UI / 原生后端增量 | T2 九组整改中；T3a 与 T3b/T4a 已由 Main review 接收；T4b usage 23项证据已接收；T3c idle-only 与显式图片实现已审查接收 | Main已核实际读/压缩/fence/事务接缝与定向测试；真实 Main、图片/PDF/JSON、withdraw/interrupt/rewind/Cancel Send 与 16 MiB 二进制上传已验证；剩余前端整改与补验见 plan |
| V1.6 缺口补验 | 真实 H02/H03 已有通过证据；H04 发现冷恢复前缀缺失 R2-F14，后续场景继续 | 最小 H01–H08 与可复用范围见 v16-handoff-evidence.md；先补 C16/VAL04/cold，不重跑旧轮全量审查 |
| 全场景 Mock 与视觉 worktree | 阶段快照 27c5cb4 已交用户 | `/Users/edgar/code/hermes-secretary-web-visual-design`，`codex/visual-design`；`http://127.0.0.1:5176/mock.html`，`npm run mock -- --port 5176`；96 场景。用户另行视觉设计，原工作区继续逻辑 |
| 第二轮独立两门禁与交付 | 未开始 | 第二轮完整 Verification → Validation → 主会话交付证据复核，准确声明限制 |

## V1.6 交接：保留证据，只补缺口

[交接指南](.autonomous/20261011-v1.6-implementation/continuation-guide.md) 为具体入口。旧轮实现完成不等于最终验收完成；旧 `82cd557` Verification PASS 属历史版本结论，不能覆盖其后的 VAL04 或当前新版本。**不重做 V1.6 自身全量 Verification**；第二轮自身两个独立门禁仍完整执行。

| 缺口 / 限制 | 第二轮处理 |
|---|---|
| C15 绝对时间呈现 | 实际 AI 工具与人类 UI 核对可读时间、时区、原瞬间；重建受改 UI 产物。Desktop 完整检查缺依赖，已有定向呈现测试不冒称整版通过 |
| C16 / VAL04 | 真实定时器到点读当前 Conversation 开关；off 结束旧事件，之后 on/重启不补；on 只处理一次。补 Main 忙碌时 memo auto-on 与合法冷恢复 |
| Persistence | 实际查源→修订不写→明确批准实际写入→候选归档 |
| Reminder / 生命周期 | idle、busy、deferred 批量、关闭恢复及隔离；剩余全局切换、冷恢复、branch/undo 与有效来源隔离 |
| 已知检查限制 | 旧 Child fixture 的 `unknown_system_message` 在当前/冻结对照均出现；profile-archives 命中三份既有 SDK 归档。保留失败和版本证据，不冒称通过 |
| 已有有效证据 | History、六键 Notebook、长正文、memo 操作/消费、Finish 呈现不机械重跑；新变化影响按实际补测 |

Full 审计 UI 按 06 延后，不提前造接口。旧轮首次失败、修复和验证版本保留在原报告及 Git 历史，不复制旧流水为新看板。

最新执行优先级（R2-C22）：立即以 `5ccc619` 的 fresh 53445 服务推进真实 DeepSeek/Main/图片/Secretary；不等待表现层或静态 Mock。控制 Codex 开销与重复检查，不限制获授权测试模型 API 调用成本。视觉 worktree 与网络/逻辑实测并行。

R2-F11：逐卡即时折叠已由用户现场及 Main 连续 DOM 共同确认；后发现第二空Thinking，Sol已区分原生thinking.delta等待活动与reasoning.delta真实思考，69定向测试通过，Main亲读差异接收，真实复验待进行。动态验证须连续观察与事件时序，不能只截图；必要时异步请用户协助，未答时继续独立工作。

真实集成：`20261012_213252_1fa75a` 已完成 DeepSeek Main、自然 Noting、图片原生 vision_analyze 与 PDF/JSON理解；`20261012_213956_bc8a48` 已真实完成 Withdraw、Interrupt 单续发、Reply/Edit退出恢复、双确认 Rewind、Cancel Send 恢复冻结草稿。16 MiB+1 前端拒绝、精确16 MiB二进制实际上传并完成Main；Notebook只读前后表计数不变。R2-F12白屏与F13重复附件实现已交，Main后续双工具实际未再现，源码集中复审待完成。证据位于 ignored `round2-evidence/runtime/`。

视觉交接：前端首次阶段提交 `27c5cb4`，79文件，明确尚未最终验收；npm锁安装成功，新树独立依赖，Mock实际打开96场景。Main仅补mock脚本/忽略产物、PDF二进制属性及合成长文本末尾空格；未上传远端。设计工作区归用户另派Agent，Main与Sol不在其中写入。

T5 `v16_gap_evidence` 独占53446 / `.hermes-dev/round2-v16-live/`，真实公开协议集成先H02–H04再H05–H08；不操作Main53445，不是独立门禁。H04-A cold恢复已发现 R2-F14：事件单次准入后父Active上下文未恢复，Noting在创建child前失败（`The Parent's active context is unavailable for freezing`）；失败证据保留。Core Sol先调查原生恢复/接缝设计，不能以重建专用prefix或伪造Main遮蔽。


Files补验：HTML合成脚本/事件探针被移除，sandbox空权限+CSP阻断，DOM执行标记为null；`html-preview-proof.json`。WAV1秒/MP4 640×360均readyState4/error null，见audio/video-preview-proof.json；仅加载/解码证据，不冒称音频听感或实际播放过程完成。

Main前端集中review：已读27c5cb4的完整Controller、command-actions、projection、App/Timeline/Secretary/Dialogs、Files/附件/草稿与上下游DTO。F12稳定node.id直接props和F13 authored prefix修复机制接收；新发现F15命令Stop失败错误被吞仍消费文本，F16Reasoning仅当前值不能选完整native支持档位，交原前端Sol修复。健康拆分adoptDraftScope CC22→12已亲读无语义扩展；69定向测试/构建证据不重复运行。

## 环境、验收与风险

- 中期架构检查：REST/WS、后端事实源与本地持久化白名单当前源码符合；前端内存投影缺少统一释放边界已登记 R2-F09，正在按统一 owner/lifetime 整改。尚未把进行时实现写成 06 全部合规。

- 官方 PM 工作区 `.venv`；本轮只读核实 Python 3.14.7、Node 24.21.0、npm 11.19.0。沿用官方锁，uv.lock SHA256 为 `2bc4db483e9cba927cd7147f9ccbb09635f85bb3f1f36d6e9d51d06b65d1c67e`，package-lock SHA256 为 `9934677654ce672900b0946898cc28c73671f75896862b5768c24cca84776ccd`。本轮不为建基线先跑大型检查。
- Main/Noting 使用已配置 DeepSeek 官方接口；图片验收必须有真实请求与理解结果，不能以附件 ACK 代替。保留原生模型/API/provider 层，不用 Codex App Server、Codex Proxy 或回退到这些通道；不修改另一旁路 Dashboard 配置。
- 本机 localhost 内置浏览器验收四视口；真实 REST+WS、真实图片/文件与用户旅程。真机专项和当前无法覆盖的平台如实标未验证，不以视口模拟冒充。
- 隔离运行状态在 ignored `.hermes-dev/`。V1.6 profile `.hermes-dev/v1.6-validation/dashboard-final-4743943e` 保留 6 sessions / 157 messages / 5 Snapshots；Dashboard 已停，临时 Idle 已恢复 2 秒。后续从最终源码重新构建/启动，旧实例或 bundle 不作新版本证据。
- 私人 Pi 迁移库按既有特定授权暂存，不读、不重建、不清理、不发布，亦不接入验收实例；凭据不进入 Git。
- 第二轮隔离后端已以原生 Dashboard 启动于 `http://127.0.0.1:53445`，profile `.hermes-dev/round2-runtime`，首次 0 Sessions；health、原生 HTML bootstrap auth、default cwd 与列表只读 readiness 见 `.hermes-dev/round2-evidence/runtime/readiness.json`。启动时重建官方 Web bundle；已于后端快照 `5ccc619` 重启加载本轮增量，实际 REST health commit 相符；六个新增 RPC 经真实 WS 返回预期未知会话 4001，证据 integrated-readiness.json，不能据 readiness 宣称 Web UI 或模型链路完成。接口差距必须先按 06 的原生审计要求证明，相关增量不得破坏未启用场景。
- 纯文档对齐仅核差异、链接、职责和原规则保留，不跑代码测试；本轮大型检查记录执行方、版本、范围、次数与结果，复用同版本有效证据。
- Main 接线定向证据（当前暂存增量，尚未产品快照）：原生 `atomic_config_replace` 成功后失效通知 3 项测试通过；`scripts/check --staged --only config-writers,ruff,health` 三项通过（health 0 blocking / 0 advisory）。新方法模块与契约已正式注册并生成共享 TS/OpenRPC。生成一致性通过；事件目录测试初次失败含两个新增 steer emitter 扫描缺口（已交 owner 修复）及冻结基线已有的孤立 `review.summary` 契约，后者由 `git grep 37ad76f5df -- tui_gateway` 证实仅有声明。正式 RPC/WS 运行联调待阶段完成重启后取证，不以注册通过代替。

- T3c Main review：新请求在原 admission/history_lock 同步检查并 claim，旧入口保留原 busy 政策；图片 validation 在 claim/truncate 前，显式列表沿既有 inline/compute-host/fallback 薄传，旧 None staging 不变。最终机制证据按 submit-idle-implementation.md 分版本复用，不虚称一次全量最终通过。无须退回产品修复；F08 后端机制关闭，真实客户端边界待联调。
- T5 Main review：v16-handoff-evidence.md 的 H01–H08 为补验输入，旧版本 7/7、11/11、57/57 证据及 edd031 的 71/71 源码可追溯；当前同源范围按实际 observer/usage/Pending 差异区分。旧库无 Candidate/Schedule，不能据此宣称 Persistence/Reminder 已验；零新测试/零模型调用的研究报告不替代门禁。

## 历史轮次与证据入口

| 轮次 | 稳定入口 |
|---|---|
| V1 首轮 | [final-delivery](.autonomous/20261007-v1-first-implementation/final-delivery.md) |
| V1.5 文档准备 / 实施 | [准备索引](.autonomous/20261008-v1.5-adjustment-and-acceptance/index.md)、[实施索引](.autonomous/20261009-v1.5-implementation/index.md) |
| V1.6 | [移交](.autonomous/20261011-v1.6-implementation/continuation-guide.md)、[Verification](.autonomous/20261011-v1.6-implementation/verification.md)、[Validation](.autonomous/20261011-v1.6-implementation/validation.md)、[交付判定](.autonomous/20261011-v1.6-implementation/final-delivery.md) |
| 第二轮 | [Snapshot Index](.autonomous/20261012-round2-web-ui/snapshot-index.md)；其余计划及门禁按冻结后阶段生成 |
| 上下文开销 | [05 台账](docs/05-context-cost-ledger.md) |

V1.6 冻结/启动提交分别为 `fc2668310b` / `fa51561601`，收尾产品 `edd031f551`。详细历史、阶段测试与失败记录按上述报告和 Git 历史查阅，不改写其历史判定。
