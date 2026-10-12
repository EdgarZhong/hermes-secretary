# Hermes Secretary 第二轮主看板

## 自主口径收敛 · 待用户追认

> 本区域按 AGENTS.md 永久维护；无待追认收敛时注明“暂无”。

**暂无。** 本轮已确认口径的授权来源见 [Snapshot Index](.autonomous/20261012-round2-web-ui/snapshot-index.md)，不得将 Agent 安排或推断写成用户确认。

## 当前目标与阶段

第二轮交付独立 Secretary Web UI，并完成 V1.6 移交缺口及本轮实际变化影响的验收。当前为 **实施计划已建立，原生审计与视觉基础准备中；尚无已完成的产品施工**。用户授权在冻结前精简三份核心文档、最小修订新版 06；冻结后本轮不再修订权威规格。

- 后端工作区：`/Users/edgar/code/hermes-secretary`，继续按原生接缝实施必要增量。
- 前端：并列本地仓库 `/Users/edgar/code/hermes-secretary-web` 已初始化 `main`，目前为空、无远端；目录名属于实施安排，不是用户逐字指定。暂不上传远端。
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

## 编排与修改边界

| 角色 | 模型 / 推理 | 职责与边界 |
|---|---|---|
| Main / Integration | Astra high | 全局目标、要求覆盖、技术决策、委派、亲自 review、正式接线集成、微小明确修补及最终判定；不承担唯一实现人角色 |
| Development | GPT-6.1 Sol high | 指定白名单内具体前后端实现、相关测试与完整阶段证据；不扩大产品语义、不再派生 |
| 独立 Verification | Astra high | 全新无上下文审查者先从冻结规格建立判据，再核实现、接线与证据 |
| 独立 Validation | Astra medium | Verification 通过后由全新无上下文验收者操作真实入口，检查用户输入到输出 |
| 独立视觉设计 | Astra medium | 按 06 交付 tokens、设计系统、呈现组件、响应式与视觉质量；不改变交互、网络、状态机、事件或导航语义 |

当前活跃委派：`native_compatibility_audit`（Sol high，完整交回已review接收）、`web_visual_system`（Astra medium，前端 `src/design/**`）、`web_frontend`（Sol high，前端其余产品/测试/配置）。视觉与业务白名单不相交，后端A增量已准入；首派Core correction+Interrupt同owner实施。具体依赖与精确章节/行范围已随派遣指定，见本轮 [plan.md](.autonomous/20261012-round2-web-ui/plan.md)。主会话完整阅读权威规格；Development 派遣按 AGENTS 的精确阅读契约执行，不能只给整份规格路径。并行修改不相交，子 Agent 不再派生；主会话集中审查完整交回，不频繁盯零碎 diff。

## 任务看板

| 任务 | 状态 | 完成条件 / 下一步 |
|---|---|---|
| V1.6 实现提交与移交 | 已提交，验收未完 | 产品收尾提交 `edd031f551`；记录提交 `6c3659bdf8`；不得重复处理产品提交 |
| 本轮规格与核心文档对齐 | 主会话 review 接收 | 06 优先级、分工、双仓库、四视口与覆盖边界已同步；规则与历史入口保留 |
| Snapshot / 文档基线冻结 | 已冻结 `37ad76f5df` | 三份核心文档、06、索引与报告模板同批提交；规格本轮一级不可修改 |
| 技术审计及实施计划 | 审计完整接收；计划已执行 | 30项N/F/A/D、DTO和源码反例已审；最终新方法名称见native-compatibility §11；具体增量按owner实施 |
| 前端仓库与设计系统 | T1 视觉基础实施中 | 设计按 06，功能施工主要交 Sol；无远端发布 |
| Web UI / 原生后端增量 | T2 原生前端实施中；T3 correction+Interrupt开始 | 完整接线、状态转换、失败处理与原生兼容；不预建未来能力 |
| V1.6 缺口补验 | 未开始 | 按下表与旧轮交接补证，共享有效历史结果 |
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

## 环境、验收与风险

- 官方 PM 工作区 `.venv`；本轮只读核实 Python 3.14.7、Node 24.21.0、npm 11.19.0。沿用官方锁，uv.lock SHA256 为 `2bc4db483e9cba927cd7147f9ccbb09635f85bb3f1f36d6e9d51d06b65d1c67e`，package-lock SHA256 为 `9934677654ce672900b0946898cc28c73671f75896862b5768c24cca84776ccd`。本轮不为建基线先跑大型检查。
- Main/Noting 使用已配置 DeepSeek 官方接口；图片验收必须有真实请求与理解结果，不能以附件 ACK 代替。保留原生模型/API/provider 层，不用 Codex App Server、Codex Proxy 或回退到这些通道；不修改另一旁路 Dashboard 配置。
- 本机 localhost 内置浏览器验收四视口；真实 REST+WS、真实图片/文件与用户旅程。真机专项和当前无法覆盖的平台如实标未验证，不以视口模拟冒充。
- 隔离运行状态在 ignored `.hermes-dev/`。V1.6 profile `.hermes-dev/v1.6-validation/dashboard-final-4743943e` 保留 6 sessions / 157 messages / 5 Snapshots；Dashboard 已停，临时 Idle 已恢复 2 秒。后续从最终源码重新构建/启动，旧实例或 bundle 不作新版本证据。
- 私人 Pi 迁移库按既有特定授权暂存，不读、不重建、不清理、不发布，亦不接入验收实例；凭据不进入 Git。
- 第二轮隔离后端已以原生 Dashboard 启动于 `http://127.0.0.1:53445`，profile `.hermes-dev/round2-runtime`，首次 0 Sessions；health、原生 HTML bootstrap auth、default cwd 与列表只读 readiness 见 `.hermes-dev/round2-evidence/runtime/readiness.json`。启动时重建官方 Web bundle；产品仍 V1.6 基线，不能据 readiness 宣称 Web UI 或模型链路完成。接口差距必须先按 06 的原生审计要求证明，相关增量不得破坏未启用场景。
- 纯文档对齐仅核差异、链接、职责和原规则保留，不跑代码测试；本轮大型检查记录执行方、版本、范围、次数与结果，复用同版本有效证据。

## 历史轮次与证据入口

| 轮次 | 稳定入口 |
|---|---|
| V1 首轮 | [final-delivery](.autonomous/20261007-v1-first-implementation/final-delivery.md) |
| V1.5 文档准备 / 实施 | [准备索引](.autonomous/20261008-v1.5-adjustment-and-acceptance/index.md)、[实施索引](.autonomous/20261009-v1.5-implementation/index.md) |
| V1.6 | [移交](.autonomous/20261011-v1.6-implementation/continuation-guide.md)、[Verification](.autonomous/20261011-v1.6-implementation/verification.md)、[Validation](.autonomous/20261011-v1.6-implementation/validation.md)、[交付判定](.autonomous/20261011-v1.6-implementation/final-delivery.md) |
| 第二轮 | [Snapshot Index](.autonomous/20261012-round2-web-ui/snapshot-index.md)；其余计划及门禁按冻结后阶段生成 |
| 上下文开销 | [05 台账](docs/05-context-cost-ledger.md) |

V1.6 冻结/启动提交分别为 `fc2668310b` / `fa51561601`，收尾产品 `edd031f551`。详细历史、阶段测试与失败记录按上述报告和 Git 历史查阅，不改写其历史判定。
