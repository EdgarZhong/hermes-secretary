# Hermes Secretary 第二轮主看板

## 自主口径收敛 · 待用户追认

> 本区域按 AGENTS.md 永久维护；无待追认收敛时注明“暂无”。

| 原规格空白 | Agent 自主收敛／理由 | 影响范围 | 实施情况 | 用户状态 |
|---|---|---|---|---|
| 结束轮次的操作查询记录未指定保留窗口 | 同原生owner内存保留最近8个已结束轮次；更旧查询明确unknown，避免无界内存 | 只影响旧Steer/Interrupt操作结果追查，不限制持久消息历史；重启本就不保live记录 | 已实施；256次Steer/64个Interrupt请求已获用户追认，8个结束轮次窗口未单独确认 | **Agent 自主收敛／8轮窗口待追认** |
| 压缩操作终态查询未指定有限保留条数 | 每个原生 Agent 仅在内存保留最近 32 条压缩终态；超出窗口的操作返回 no_active，不推断过往成功 | 仅新增压缩观察/取消 RPC；不改原生压缩记录或执行 | 已实施并通过相应机制验证；Main review 接收，真实 UI 待联调 | **Agent 自主收敛／待追认** |

已追认（R2-C36）：单Main Turn累计256次新Web Steer（消费/撤回仍计数）；同Turn64个不同Interrupt请求记录；idle-only保持同会话一次Main Turn、并发普通Send失败保稿，结束后任一客户端可发；同会话两个在线订阅端实时流式接收；图片经原生上下文注入，本体允许留服务器。第三项“32条压缩终态查询”在用户纠正后仍未确认；不得把查库未见摘要等同于取消成功。

2026-10-13 附件工程调查：整包500 MB Base64超过运行时字符串上限；沿原生 `file.attach` 增加可选分片参数，使用同session/profile owner及末片正式发布引用，不新增上传API。具体容量/取消/偏移/丢ACK实证由附件owner交回，尚未验收。

本轮已确认口径的授权来源见 [Snapshot Index](.autonomous/20261012-round2-web-ui/snapshot-index.md)，不得将 Agent 安排或推断写成用户确认。

## 续接先读：已有测试与回归选择

**用户R2-C26：不得跨会话/压缩后遗忘已有测试而重复运行。** 先读 [plan的统一证据索引与回归选择](.autonomous/20261012-round2-web-ui/plan.md#已有证据索引与回归选择r2-c26跨会话续接必读)，再读所涉及的owner报告/manifest。该处已区分机制、真实协议/模型、真实Web及独立门禁；本轮独立门禁尚未执行。

- 可复用：后端Pending109、Read53、Usage23、Submit分版本证据；前端30d3135累计89；真实Main/图片/附件/控制/刷新/Notebook/压缩；V1.6的C15/C16/VAL04、Persistence、Reminder、branch/undo。各组有重叠，不相加为总通过数。
- 剩余集中包已完成：F14机制及新合法cold真实补证，F16设置往返、F20已有carrier只读复验均已由Main接收。后端37ce184eca/前端bfecc9f；此为视觉交回前已完成的开发基线；本次按C28/C30继续收尾和集成，未启动门禁，不重跑已有效包。
- Reasoning根因已由真实RPC定位为5098：服务5ccc619与checkout6d96e80不一致，loadCapabilities吞错成空能力。保留native保护，修错误与Retry；待统一重启再验，不猜provider别名或伪造支持。

## 当前目标与阶段

**当前执行授权（2026-10-13，R2-C31 覆盖此前自动进入门禁安排）：继续托管，完成开发/主审/必要实测/阶段提交并准备好审查输入，在启动或派遣 Verification 之前停下向用户交接。阶段目标已挂载。整轮后续仍需 Astra high Verification 与 Astra medium Validation，本次不启动。**

R2-C32 用户现场纠正 Deferred reminder 已完成：箭头在蓝色标题右侧，原卡片向下展开直接展示正文，无独立due按钮或嵌套文本框；Reminder业务合同不变。

R2-C33 用户现场纠正工具 Parameters：保留深色可横向滚动的JSON内容，去掉额外JSON标题。Main同步Mock，正式参数pre原本无此额外标题；不改变工具执行或分区。

R2-C34/C35：工具正文恢复左右16px留白；Result最大约10行正文高度，超出区域内滚动，原卡片背景，无深色文本框。正式页面与Mock已同步并完成定向核对。

自主取舍产品影响已向用户补充明确：256是单Main Turn累计新Web Steer次数上限，消费/撤回仍占名额；64按同Turn不同Interrupt请求计数，不是整个聊天中断次数；32仅后台旧压缩操作状态追查，不限制历史卡片。多客户端共用会话的Turn状态与实时流式广播，非客户端独占。用户已追认256/64、idle-only和图片留存；压缩旧操作状态确认及8轮保留窗口继续待追认。

2026-10-13 新确认：当前草稿所有附件合计不得超过 500 MB（500,000,000 bytes）；选择/粘贴/拖放按已有附件状态累计判断，移除释放预算。撤销未获确认的 16 MiB 单文件临时限制，06 §1.7 已按本次授权同步；完整上传链路和边界仍待实测。表现层由 Sol 在视觉 worktree 收尾；逻辑和大附件在功能仓完成，Main 集成。进入 Verification 前不调用 Astra。

2026-10-12 用户要求将 Force dispatch Framework Message 改为英文；运行时代码、02 规格及对应测试断言已同步。未运行测试，按本次请求仅做固定文案替换与静态差异核对。

2026-10-13 自动命名指读：`auxiliary.title_generation.enabled` 与 `model_upgrade_enabled` 默认均为 true，隔离运行配置未覆盖；`session.title` 事件后端会发送，但原 Web Controller 未应用事件标题。前端功能仓 `src/core/controller.ts` 已按会话 ID 即时更新侧栏/页标题，缺少列表行时回拉会话列表。源码及差异静态核对完成，未运行自动化测试。

2026-10-13 用户现场确认并经其授权，对 06 做**此前键位规格修订**并重新提交：§1.6 Composer 键位绑定强化为「**Enter 只负责发送类动作（Send / Steer）**，空输入框且无附件时 Enter 不执行任何动作，不得触发 Stop / Interrupt / Cancel Send，也不得消费 still-pending 纠正；**Escape 负责全部取消类动作（Cancel Send / Stop / Interrupt）**」，§1.10 交叉引用同步对齐，状态行登记该唯一授权例外；提交 `4939d340c0`。同批提交此前已授权的 02 Force dispatch Framework Message 英文文案（`faa78ecb90`）。**随后用户另授权 §1.7 合计500 MB修订；其余条款仍冻结。**

R2-F21（2026-10-13 用户现场发现，**逻辑层缺陷**）：活动 Turn 中空输入框按 Enter 会触发 Stop；存在待发 steer 时触发 Interrupt 并把 pending 合成一条真实用户消息发出（误触级操作）。前端功能仓 `src/components/ChatComposer.tsx:138-141` 的 Enter 守卫只挡 `sending`/`pendingBusy`，**未限定为提交类动作**；`src/core/projection.ts:298-311` 在空文本 + active 下解析为 `Interrupt`/`Stop`；`src/core/command-actions.ts:206-216` 真调原生 `session.interrupt_pending` / Stop。同文件 `142-147` 的 Escape 处理已正确。按新 06 §1.6 由前端 owner 收敛为「Enter 仅 Send/Steer、空文本 no-op」，取消类全部留给 Escape；未运行测试，本条为源码与实机双重核对结论。

最新效率约束 R2-C27：本阶段已完成两组补丁→Main集中review/提交→统一重启定向复验；后续继续复用既有证据，减少重复读档/过程输出，不扩展邻近测试。

推进分工：Main专注全局接线与review，视觉由Sol收尾；用户新C28授权Main review后合并，不改变此前基础能力优先与避免监工的原则。

最新用户口径 R2-C10 已写入 AGENTS：以同一 owner、统一判断点、同步临界区和正式提交点保证不变量；Main 据此复核当前增量，避免下游堆叠门禁。

第二轮交付独立 Secretary Web UI，并完成 V1.6 移交缺口及本轮实际变化影响的验收。当前为 **开发集成与阶段提交完成：后端产品5ba0481、前端21aad02，按R2-C31停在Verification派遣前；整轮尚未验收，两门禁本次不启动**。用户授权在冻结前精简三份核心文档、最小修订新版 06；冻结后本轮不再修订权威规格。

- 后端工作区：`/Users/edgar/code/hermes-secretary`，继续按原生接缝实施必要增量。
- 前端：并列本地仓库 `/Users/edgar/code/hermes-secretary-web`，`main`、无远端；React前阶段已提交并完成开发期集中复验，现施工逻辑收尾与附件预算、待视觉合并及独立门禁。目录名属于实施安排，不是用户逐字指定。暂不上传远端。
- 过程计划、依据、协调、审计与验收证据全部留在本工作区；前端不建立并行过程看板。
- 范围只含 06 Web V1、必要原生后端增量和 V1.6 移交验收；不含 Memory Provider 或云部署。

规格顺序：现行 [02](docs/02-noting-system-specification.md)（含 V1.6 已确认修订）→[04](docs/04-hermes-secretary-v1.5-implementation-spec.md) 未被覆盖的增量→[01](docs/01-personal-hermes-v1-first-fork-iteration.md) 继承要求；显式 Web 增量以 [新版 06](docs/06-Hermes-Secretary-Web-UI-V1-Spec.md) 为权威。旧 UI 讨论保留来源角色，不能覆盖新版 06。

## 本轮已确认口径与授权

| 范围 | 已确认口径 | 来源 |
|---|---|---|
| 托管 | 用户要求挂载目标，持续推进至最终交付；必要时显式 wait 子 Agent | R2-C08 |
| 文档与冻结 | Ask and Align 可最小修订 06、精简核心文档；冻结后不改权威规格 | R2-C01、C07 |
| 协作 | 本次接手Main为Sol，具体收尾也Sol high；进入Verification前不调Astra；独立Verification Astra high/Validation Astra medium；完整交回集中review | R2-C28覆盖此前C02、C07安排 |
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
| Main / Integration | GPT-6.1 Sol（本次接手） | 全局目标、要求覆盖、技术决策、委派、亲自 review、正式接线集成、微小明确修补及最终判定；不承担唯一实现人角色 |
| Development | GPT-6.1 Sol high | 指定白名单内具体前后端实现、相关测试与完整阶段证据；不扩大产品语义、不再派生 |
| 独立 Verification | Astra high | 全新无上下文审查者先从冻结规格建立判据，再核实现、接线与证据 |
| 独立 Validation | Astra medium | Verification 通过后由全新无上下文验收者操作真实入口，检查用户输入到输出 |
| 视觉设计 | 原 Astra medium 已按用户要求结束；后续用户另行委派 | 保留既有成果和未验项；不再由原 Agent 操作。Sol 继续已确认交互/卡片骨架及必要接线，不自行定案新主题 |

当前视觉成果已合并；逻辑与附件 owner 已完整交回并由 Main review 接收，修改窗口已释放。最终接线 `ui_final_wiring` 曾因额度限制中断，2026-10-13 按用户要求恢复后已完整交回，现待 Main 集中 review；其超额toast实测证据一并核查，不重复上传500 MB或模型调用。三个 owner 均已完成待命。此前前端功能阶段bfecc9f、后端37ce184eca及T5最后F14真实补证有效；各阶段报告和manifest统一从plan证据索引进入。Main 继续审查、必要定向复验及统一阶段快照，按 R2-C31 在派遣 Verification 前停止。

用户视觉 worktree 已交回，现由 Sol 仅收尾已确认表现层缺口，保留用户设计成果；Main 负责合并与正式接线。New Chat 两统计卡已移除，不更改当前配色决策。

## 任务看板

| 任务 | 状态 | 完成条件 / 下一步 |
|---|---|---|
| V1.6 实现提交与移交 | 已提交，验收未完 | 产品收尾提交 `edd031f551`；记录提交 `6c3659bdf8`；不得重复处理产品提交 |
| 本轮规格与核心文档对齐 | 主会话 review 接收 | 06 优先级、分工、双仓库、四视口与覆盖边界已同步；规则与历史入口保留 |
| Snapshot / 文档基线冻结 | 已冻结 `37ad76f5df` | 三份核心文档、06、索引与报告模板同批提交；规格本轮一级不可修改 |
| 技术审计及实施计划 | 审计完整接收；计划已执行 | 30项N/F/A/D、DTO和源码反例已审；最终新方法名称见native-compatibility §11；具体增量按owner实施 |
| 前端仓库与设计系统 | T1 组件初版review接收，正式接线/四视口未完 | 设计按 06，功能施工主要交 Sol；无远端发布 |
| 自动会话命名标题回显 | 跨层缺少的前端事件接线已在功能仓补齐；待视觉 worktree 合并后集成复核 | 后端 auto-title 默认开启并通过 `session.title` 事件回传；功能仓 `src/core/controller.ts` 按持久会话 ID 即时更新侧栏和页标题，缺少列表行则回拉；合并后确认即时标题与异步模型标题均可见 |
| Attach / Photos & Media / Take Photo | 真实前端入口与原生提交链路已接通；视觉 Mock 仅展示合成操作；移动设备拍照体验待真机验证 | `ChatComposer` 用标准 `<input type="file">` 文件选择、`accept="image/*"` 媒体选择、`capture="environment"` 移动拍摄提示；结果留在草稿中，Send 时走原生附件上传。视觉合并后复核入口保留；相机/选片实机行为尚未覆盖 |
| Web UI / 原生后端增量 | 功能阶段37ce184eca/bfecc9f已提交并由Main review接收；F14/F16/F20最终开发实测关闭 | Main已核实际读/压缩/fence/事务接缝与定向测试；真实 Main、图片/PDF/JSON、withdraw/interrupt/rewind/Cancel Send 与 16 MiB 二进制上传已验证；未覆盖边界及后续门禁见plan |
| V1.6 缺口补验 | H02–H08及C15均已由Main复核接收实际覆盖；F14新合法cold真实补证通过，仍非独立验收 | 最小 H01–H08 与可复用范围见 v16-handoff-evidence.md；先补 C16/VAL04/cold，不重跑旧轮全量审查 |
| 全场景 Mock 与视觉 worktree | 已合并且正式接线完成 | 功能集成611b734/最终21aad02；visual86fa280仅同步C32–35。103可点击URL/42实际反馈详见视觉报告；toast/Pending/finish接线与表现机制已Main审收。用户未跟踪成果保留 |
| 合计500 MB附件预算/传输 F22 | Main亲读接收，真实超额toast可见性已补 | 当前全部attachment合计，历史引用真实stat；chunk沿file.attach旧method，末片才发布引用；真实500 MB上传/取消/越界取证 |
| 键位/通知/原生完成事件 F21/F24 | Main亲读接收；正式App已接入 | Enter只发送；通知显式关闭；网络自动恢复；task_finished唯一完成信号，Main合并后App接线 |
| 第二轮独立两门禁与交付 | 本次停在门禁前（R2-C31） | 三个 Sol 已交回并由 Main review 接收，前端611b734；后端产品5ba0481、前端21aad02；三屏四视口已完成开发核对，本次不派 Verification/Validation |

## V1.6 交接与此前开发证据（历史版本记录）

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

历史实测安排（R2-C22）：曾以 `5ccc619` 的53445服务并行推进真实模型；以下为已取得的阶段证据，不是当前服务版本或待执行清单。当前施工与服务统一重启安排见上方看板。控制Codex开销与重复检查的授权继续有效。

R2-F11：逐卡即时折叠已由用户现场及 Main 连续 DOM 共同确认；后发现第二空Thinking，Sol已区分原生thinking.delta等待活动与reasoning.delta真实思考，69定向测试通过，Main亲读差异接收，实际双工具中刷新后正常收敛且未出现空卡；本次原生仅发 thinking.delta 而无 reasoning.delta，不能冒称验证了流式真实思考内容。动态验证须连续观察与事件时序，不能只截图；必要时异步请用户协助，未答时继续独立工作。

真实集成：`20261012_213252_1fa75a` 已完成 DeepSeek Main、自然 Noting、图片原生 vision_analyze 与 PDF/JSON理解；`20261012_213956_bc8a48` 已真实完成 Withdraw、Interrupt 单续发、Reply/Edit退出恢复、双确认 Rewind、Cancel Send 恢复冻结草稿。16 MiB+1 前端拒绝、精确16 MiB二进制实际上传并完成Main；Notebook只读前后表计数不变。R2-F12白屏与F13重复附件实现已交，Main后续双工具实际未再现，稳定node.id与authored prefix源码集中审查已接收。证据位于 ignored `round2-evidence/runtime/`。

视觉交接：前端首次阶段提交 `27c5cb4`，79文件，明确尚未最终验收；npm锁安装成功，新树独立依赖，Mock实际打开96场景。Main仅补mock脚本/忽略产物、PDF二进制属性及合成长文本末尾空格；未上传远端。设计工作区归用户另派Agent，Main与Sol不在其中写入。

T5 `v16_gap_evidence` 独占53446 / `.hermes-dev/round2-v16-live/`，真实公开协议集成先H02–H04再H05–H08；不操作Main53445，不是独立门禁。H04-A cold恢复已发现 R2-F14：事件单次准入后父Active上下文未恢复，Noting在创建child前失败（`The Parent's active context is unavailable for freezing`）；失败证据保留。Main 已亲审 cold-resume-fix.md 与上下游，准入原生 build/attach 发布前恢复完整 Parent Active；Core Sol 实施，不改 timer/admission/freeze，不重试旧失败事件。


Files补验：HTML合成脚本/事件探针被移除，sandbox空权限+CSP阻断，DOM执行标记为null；`html-preview-proof.json`。WAV1秒/MP4 640×360均readyState4/error null，见audio/video-preview-proof.json；音频后续通过实际 Space 触发播放，从0到1秒ended=true/error=null，见audio-playback-proof.json；未验证听感。视频仅观察到实际进入播放，随后施工HMR使Controller重置并播放归零，video-playback-proof.json保留原结果，不宣称完整视频播放通过；按C25不再扩展此类表现层检查。

Main前端集中review：已读27c5cb4的完整Controller、command-actions、projection、App/Timeline/Secretary/Dialogs、Files/附件/草稿与上下游DTO。F12稳定node.id直接props和F13 authored prefix修复机制接收；新发现F15命令Stop失败错误被吞仍消费文本，F16Reasoning仅当前值不能选完整native支持档位，交原前端Sol修复。健康拆分adoptDraftScope CC22→12已亲读无语义扩展；69定向测试/构建证据不重复运行。

## 环境、验收与风险

- 中期架构检查：REST/WS、后端事实源与本地持久化白名单当前源码符合；R2-F09已通过统一owner/lifetime整改并由Main源码review接收，必要未决操作仅保留owner元数据。尚未把进行时实现写成 06 全部合规。

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

开发期新增事实：R2-F17 unknown Steer 在旧 Turn 结束后被前端 active gate 挡住且 Send 可盲重发；R2-F18 Pending 请求飞行中失效通知未安排重读，三项生产控制器反例已失败确认，Sol按同一owner修复。R2-F19 实际两次压缩中后一次原生拒绝摘要增长（replay seq424），前端未显示反馈且不刷新正式History；已交Sol按真实RPC结果与summary反馈，不把facade completed冒称压缩成功。真实双工具中刷新保持同会话并最终单份结果；HTML安全和媒体解码证据沿用。

R2-F15/F16：Main已亲读Stop、reasoning helper/App/Dialogs及官方常量/inventory，接收22:01交回的修复与74项不同定向证据，不复跑。R2-F14设计微调：因native root恢复可能写DB，eligible eager沿现有claim/build唯一owner执行准备，允许内部prepared_agent薄参数，保持非eligible/off原路与原eager等待语义；具体实现与资源所有权仍待完整review。

前端阶段提交 `30d3135`：Main亲读F15–F19实际source/tests及native契约，50/50源码manifest匹配；89 distinct定向用例、tsc/build/health有效证据复用。真实UI压缩拒绝明确展示28messages preserved与summary/no messages removed，`runtime/compaction-refused-after-fix.dom.txt/png`。同库只读核对双工具刷新用户row89/最终assistant94均各一条，`stream-reload-db-proof.json`。未重复模型/附件测试；未独立门禁/最终验收。Mock Escape微修仅原功能树，同批提交；视觉树仍27c5cb4独立。

R2-F16真实复验重新打开：30d3135实际第二会话Reasoning仍显示Current medium但capability unavailable/空选项，与owner原生catalog captrue证据不符。`runtime/reasoning-unavailable-real.dom.txt`；Main没有改设置。已交原前端owner在成功压缩补证期间核实际runtime/catalog身份及加载失败原因，再作必要逻辑修复；不能把既有fixture测试通过冒称实链关闭。

成功压缩正向真实证据：新会话20261012_223239_3eb664 / Ref conv_0c38d52e956247fd854b2e6fa8734178，一次正式12→10消息、约79243→29762 tokens，native in-place故storedtip不变；carrier UID cdc55ef9bfb841a8b87db34ab3df5237/row121，Web已实际读取。但发现F20：该row真实assistant，DisclosureNode将realText硬编码user并给Reply，已交Sol按真实来源role微修和反例验证；不改design/视觉。证据frontend/compaction-positive与runtime/compaction-positive-history.dom.txt。

T5完整阶段Main接收：H05–H08报告/原始摘要与7/7产品hash已审，真实Persistence/Reminder/branch/undo范围有效，F14仍单列。H05§11只读补核：sessions.system_prompt旧字段NULL，正文从system_prompt_hash→system_prompts.prompt读取；实际冻结两句History指导各1次，Root hash838a1bc，proposal前后留存WS Root一致，但无逐API完整payload，不冒称逐请求直接证实。附带模型多余3次空搜索保留为行为限制，不改冻结Prompt。

F14并发补充：正式prompt.submit可在root恢复期间先claim running并落user，旧Idle随后在Agent Loop前误启动；开发期反例已捕获。Main准入poller使用原host history锁下的busy/isolation事实，限定eligible/global on，不新建owner或改timer/admission策略；锁顺序与两个窗口由Core定向验证后完整交回。

F16/F20前端小阶段Main已亲读5文件及生产Controller/React反例，5/5hash相符，接收55当前包＋42不变复用=97 distinct、build/health证据，不复跑。capability由当前视图/序号归属，保原生5098并支持Retry/ready；carrier按真实role且仅user可Reply。真实恢复与已有carrier最终检查等待F14集成后的统一restart。

F14完整交回Main已亲审五源码/测试文件、root/tool pin与DBownership/锁上下游：同原claim/build、恢复后最新history引用发布、仅on eligible host忙碌临界区；6/6源码报告和23/23日志hash匹配。接收17不同新增机制例（16当前包+压缩1定向修正）、21旧恢复回归复用、ruff通过、health0阻断/1原bareThread迁移提示。没有重跑109/53/23或旧V1.6。真实cold尚待新合法period补验；前端F16/F20阶段bfecc9f已提交。

稳定实测窗口：后端37ce184eca、前端bfecc9f。53445已安全重启，health精确匹配；首次因漏HERMES_RUNTIME_DIR/HERMES_PYTHON/HERMES_TUI_DIR启动未上线已停止，未改lock/依赖策略。正确完整启动沿用下列环境，避免续接重复踩坑：`HERMES_HOME=$PWD/.hermes-dev/round2-runtime HERMES_RUNTIME_DIR=$PWD/.hermes-dev/tools HERMES_PYTHON=$PWD/.venv/bin/python HERMES_TUI_DIR=$PWD/ui-tui/dist .venv/bin/python -m hermes_cli.main dashboard --host 127.0.0.1 --port 53445 --no-open`。

F16/F20真实开发复验关闭：同原成功压缩会话，Web Reasoning七档显示，medium→high实际config回读Current/Effective均high→恢复medium两值均medium；已有row121原文MATERIAL_RECEIVED为Assistant且无Reply。证据runtime/reasoning-{high,medium}-final.txt、reasoning-medium-final.png、carrier-role-final.json；没有新模型/长对话。点击Apply后原对话框异步关闭，一次过早继续定位超时，重开确认后完成；没有产品错误。F14真实新period复验正在T5自己的53446执行。

最终阶段状态（覆盖以上进行时历史记录）：F14真实新周期补证Main已完整读§12/proof并核9/9产品、39/39证据hash；正常Main结束→due前停机→跨due公开eager resume，1event/admission14/1completed child/1Snapshot，10秒无重复，旧失败admission3保持；Root/Parent工具pin/UID一致。Child两次越权调用被拒绝，缺逐请求完整payload限制保留。Idle恢复2，53446已停，Main53445保持37ce184运行。F16/F20真实复验也已关闭。当时按C24停在Verification前，整轮未完成；本次用户交回视觉后已恢复同轮施工，当前安排见上方。收尾证据文档暂留工作区，待视觉合并统一提交，避免仅文档HEAD变更使当前服务再次5098。

2026-10-13 Main补核：Force dispatch英文文案保留此前用户修改，修两条测试大小写匹配失配。canonical runner三文件 -k force/measurement_spawns，6通过、0失败，runner 3.2秒；未扩大测试。最新附件上限只有R2-C30合计500 MB，不再待追认16 MiB。

合并后集中接线清单（2026-10-13）：Enter/ESC真实组件；持久通知栈与持续网络状态；session.title顶栏/侧栏统一事件；Pending退出/进入动画只延迟表现不改变原生RPC；500 MB合计草稿及历史引用真实字节；Orb finish取原生task_finished全局通知而不以active→idle猜测；Rewind保留共享单层dialog的两次明确确认。完成后统一前后端快照和服务重启，再选一次受影响包与四视口，之后启动Astra门禁。

2026-10-13 Main集中review接收：视觉22/22源码hash相符、三项动画和四视口中间证据已读；视觉提交1c614ac→UI merge3df93c9，Mock键位冲突按真实矩阵微修。完整报告含103可点击Mock URL、42条实际反馈（原66/51不完整计数已纠正）。逻辑7文件与上下游已读，88机制/React及Esc edit-first修补24小包证据复用；其ChatComposer后续仅必要视觉class/icon适配由最终接线owner处理。

F22 Main接收：11产品文件和额外2Controller接口源码hash相符，49/49固定证据hash匹配，已读正式file.attach锁/偏移/last-ACK/原生分配及readonly metadata、前端预算/重stat/tx取消上下游；30后端不同用例、46前端用例复用。真实单500 MB及同名250 MB×2源/服务器SHA一致，DeepSeek原生terminal实际读首尾标记/精确尺寸；真Cancel后取消标记user rows0、草稿500 MB保留、无partial。仅普通超额通知可见性待Main App补证，不重传大包。分片完成回执按runtime session生命周期保留；断线/崩溃可残留暂存bytes，不承诺跨进程续传/清理，符合06残留边界。最后缺upload_id负例guard未在53447热载，正常传输同路径证据复用，统一提交/restart再查负例。

Main最终接收：最终接线9/9owned、6/6依赖、21/21证据hash相符；前端阶段611b734（22文件），用户查看Mock的86fa280仅3文件。最新build/tsc成功，冻结health0阻断/0提示。C32–35修补已现场390核对，无JSON内层卡片、Reminder直接展开、正文左右16px、Result10行/滚动/透明背景；后端5ba0481及稳定窗口三屏四视口已完成，严格在派遣Verification前停止。

本次门禁前最终交接：前端21aad02、后端产品5ba0481。最后native工具名/空参数框/Current Reasoning薄修后，54例受影响包1.20秒通过、build/tsc成功、health0/0；三屏四視口JSON和截图在main-final-integration，未重跑大包或模型。主测试服务实际guard5028拒缺upload_id、capabilities无5098。预停机事实：Main idle、压缩inactive、Noting idle；首次秘书预检错用session_id出现4000，改正式stored_session_id后正常，原失败文件保留。新建页/会话/Files四视口无页面横溢，320 Files返回原会话；这是开发观察，非独立Validation。最新阶段final-delivery已写，本次不派两门禁。
