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

1. 主会话审核 T0 后发布具体后端白名单及最终方法名称，增量的 owner、输入/状态/错误、unknown acceptance、锁/线程、事件、ephemeral/durable、兼容和测试逐项落在 native-compatibility.md，不改一级规格。
2. T1 可先行，纯视觉接口集中 `src/design/index.ts` 导出；仅依赖 React、Radix/shadcn 方式 primitives、lucide-react（若采用）及 CSS。设计师不改 package.json；交回依赖清单供 T2 集成。不创建 App/router/client/store，组件只通过 props/children/callback 呈现。
3. T2 开发负责 package/lock/config 与业务模块，避开 T1 白名单；等待 T0 的实际 DTO，不自行猜拟 A 方法。T3/T4 后端按不相交 owner 分组，必要共享文件串行；前端同一实现者完成控制接线。
4. 每项阶段完整交回七项报告；主会话集中读实际 diff/上下游，不用重跑有效测试代替 review。机制实现、正式接线、针对性验证、真实用户结果的动态状态仅在根 CLAUDE 维护，本计划不复制看板。
5. Development 必须读 executing-plans、索引/基线/计划与所派冻结原文；02 精确章行范围每次随派遣指定。独立审查先从冻结要求建立判据，不能先读实现自评。Validation 先交完整计划再真实操作。

## 缺陷与整改

尚无本轮已判定代码缺陷；T0 准备审计差距和 V1.6 移交缺口按各自依据处理。范围内审查发现按下表追加，不降低冻结判据。

| 编号 | 要求与触发条件 | 当前事实与影响 | 优先级 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|

## 取舍、快照与续接

- 文档基线 `37ad76f5dfac02d4774d5e0faea55911b5fb8de9`；V1.6 产品 `edd031f5518955a10a2c68210e1c65477d6f0991`；该产品尚未全验收。
- 用户数据：只用仓库 ignored 隔离 profile；不读/清理私人 Pi 库；凭据仅获授权本地读取，不入 Git。无云部署/远端 push。
- 官方 PM Python 解释器与锁沿用；前端新库正常 npm lock，不改后端依赖锁。测试必须 canonical runner；大型检查只集成收敛后统一一次，失败修复按影响复测。
- 四视口 1440×900、1024×768、390×844、320×568 均强制；软键盘/相机/系统侧滑真机证据后续专项，功能仍实现。
- 当前版本和完成状态见根 CLAUDE。每个阶段本地快照写明验证与缺口；最终双仓分别给出 commit。
