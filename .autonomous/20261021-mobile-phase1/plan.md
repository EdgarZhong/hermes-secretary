# 本轮实施计划：20261021-mobile-phase1

## 目标与依据

按snapshot-index.md与baseline.txt完成阶段一、集成另一会话Noting／Provider、统一验证并首尔上线。优先打通图片历史瘦身与纯图持久受理；不改现有产品交互及数据身份。上线前完成代码亲审、相关测试／构建和恢复材料准备；部署后同200行窗口取得原／新bytes、fallback与下载权限、请求时机／次数证据并做简化Validation（用户C08授权不严格执行套件）。保留原数据，准备代码／静态／Caddy可恢复材料，但依C09不擅自回退；保留运行库及新写入。

## 覆盖与任务

| 要求/口径编号 | 任务和正式路径 | 实现负责人及白名单 | 依赖和接口 | 验证方法 | 用户场景 | 完成条件 |
|---|---|---|---|---|---|---|
| P1-01、08/C02 | Caddy压缩／哈希资源缓存、bootstrap/WS/ready诊断、就绪／发布 | 主会话：部署／配置及最小集成；诊断前端由前端包实施 | 后端ready后前端opt-in；双方空闲后部署 | 配置校验、真实压缩协商／鉴权只读／监听／版本及重连 | 认证恢复、历史加载、草稿保留 | 目标JSON压缩，静态缓存边界正确，各宿主实际版本明确 |
| P1-02～05、08/C05 | usage summary、图片视口、cards/details opt-in、显式补水、Thinking首次展开、detailSources、分段诊断 | 前端Agent：../hermes-secretary-web/src/及其测试（不改后端／根文档） | prefer_image_refs=true，仍inline_images=true；不缩页／不删force | consumer审计、vitest、typecheck；随后浏览器真实UI | 文字／图／多图／滚动／展开刷新／切会话／复制编辑 | 正常消费者可取完整内容，无无需求请求，原动画状态保留 |
| P1-03/C05 | 查询页原结构helper验证→授权可下载→响应副本refs→cards/details | 投影Agent：hermes_cli/web_routers/sessions.py，必要同层sibling，相关新增测试；session_history.py只读 | 不改helper权限；与纯图包只读依赖 | 正式HTTP+SQLite，默认／fallback／跨Profile／下载 | 纯图／caption／多图／损坏／缺文件 | 默认兼容、身份不变，合法refs可下载，无越权 |
| P1-06/C05 | 原受理行持久refs、staged精确输入匹配、worker原位认领 | 受理Agent：tui_gateway/methods_prompt.py（仅可选image_paths透传）、tui_gateway/methods_submit_idle.py、session_workdir.py、session_history.py、prompt_turn.py、agent/turn_context.py、agent/image_routing.py及相关新增测试 | 与Noting会话接缝协调；不动provider／noting | 正式RPC+DB+worker屏障，native/text、持久失败／认领失败／旋转 | 纯图立即气泡，完成／刷新仍一行，原模型输入保持 | 同row/UID/owner，durable后失败保留，不重复／不伪回执 |
| P1-07/C02 | 已上线预算补丁确认与外部Noting最终包接收 | 外部会话；主会话亲审 | 不重复补丁；最终修复范围由用户在另一会话确认 | 复用有效证据，影响处定向集成验证 | Noting结束／失败／资源清理 | 有可接收最终版本与证据，不冒称调查即完成 |
| 全部/C01～07 | 集成、独立两门禁、构建、空闲窗口上线、回滚／证据 | 主会话（C08简化流程） | 实现包亲审、定向测试及回退准备后部署；简化Validation在部署后执行 | 同版本有效证据；必要真实入口取证 | 登录／草稿／历史／图／展开／发送／Stop/Steer | 后端Scheduler／Instant排期／微信路由和发送链可继续运行；字节与请求时机证据闭环，Wi-Fi耗时不外推蜂窝 |

## 当前状态与编排

| 目标/任务 | 机制实现 | 正式接线 | 针对性验证 | 用户结果 | 当前负责人和下一步 |
|---|---|---|---|---|---|
| 前端包 | 完成 | 完成 | 286定向＋usage54（重叠），typecheck/build通过 | 已部署后观察 | 已亲审，前端1d1b1a7已push；439文件SHA上传通过 |
| 后端投影 | 完成 | 完成 | 新26＋原48不同场景有效证据 | 已部署后观察 | 已亲审／提交aaaa991 |
| 纯图受理 | 完成 | 完成 | 新34及受影响60场景有效证据，旧失败已对照 | 已部署后观察 | 主会话已复审，1df86af已提交推送 |
| 运维／集成 | 完成 | 已联合发布 | 冻结10检查有效通过／部署后验完成 | 实际0bdddfc＋前端1d1b1a7，提醒链保持 | 已收口，无自动回退 |
| Noting／Provider | 完成并亲审 | 正式Loop与summary | 动态39／摘要4／回退3；真实K3短场景正式提交 | 已联合上线 | 原生Alex及绑定tip路由已核 |

三个实现包文件不相交；session_history.py只有纯图包可改，投影包只读复用helper。子Agent不提交、不改动态核心文档、不再派生，不流水账；证据写ignored .hermes-dev/mobile-phase1-20261021/<包>/。前端包为所有前端文件唯一owner。主会话收到整包后亲审正式路径、数据与失败处理，按C08/C09完成发布前验证与备份后上线；随后简化Validation。UI仅主会话创建隐藏IAB；不能合规则记录未验。

## 缺陷与整改

| 问题编号 | 要求与触发条件 | 当前事实与影响 | 优先级及理由 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|
| D00 | 联合上线依赖另一任务 | 最终包已接收并亲审，6次真实K3完成正式提交 | 发布前置 | 主会话／外部会话 | 0bdddfc已联合上线并核宿主／提醒链 | 关闭 |

## 取舍、快照与续接

初始后端HEAD 50214cd4ab95020fdfa522bc972ac20092829940；前端83285d2be259f1ee9f7e24bba6dd4c70688831fe。已有CLAUDE、README、operations-log修改及mobile调查文档属于先前／外部工作，本轮不擅自提交。冻结仅纳本轮核心文档hunk、轮次索引及用户指定任务包；规则文件和06／08／白板／07原已在基线树内。Git提交自动push，保留既有hook。不以基线跑大套；实现期相关验证，集成收敛后统一冻结检查及必要范围回归。

冻结文档提交316637e；任务包旧patch原样保留，其diff上下文空格被git diff --check报告10处；排除该历史原件后其余冻结文档检查通过。未修改检查规则。首尔只读预检：后端532cadb4d8、Caddy2.11.7；服务单元需按实机发现，不套用旧模板名称。

联合交付补充：已独立读取并行会话用户原始授权，允许原生Kimi切chat_completions（不替换Provider）；外部会话负责Noting请求接缝及真实K3短场景。已要求其精确交接默认与既有Conversation路由更新、宿主重建要求。统一提交前禁止并行暂存，外部会话已通知。
生产只读原200行窗口：cards863366B/gzip544803B，full-session215536B，summary51683B；唯一structured user图片行10091，现有helper校验可转换（651372B→90B，不代表新API实测），fallback0。原始正文/图片仅留首尔受限证据目录。

C08已明确调整：先部署、后简单Validation，重点真实历史传输bytes／图片fallback／背景详情请求与视口触发；保持线上健康是发布硬门槛。严格独立两门禁不再作阻断条件，前置相关测试与代码亲审不减少。不为Wi-Fi下时延做蜂窝效果承诺。

C09用户纠正：后端健康以目标会话明日Instant Reminder自动触发及微信发送能力为核心，非泛UI清单。禁止部署失败自动回退；出现问题修复继续完成新版本上线。正式排期／绑定／Profile状态只读核验，不能新建或提前触发用户生产提醒。

主会话亲审后端图片包通过：新增opt-in仅在True组合启用，原结构helper及同Profile正式fs_download准入，响应副本content，整行fallback；26新场景及48原兼容场景有效证据，未为review复跑。已提交aaaa991，待前端/纯图集成及生产同窗取证。
当前生产目标会话既有7条启用instant；最近2026-10-21 10:00+08，内容显式微信触达，Scheduler启用/扫描线程存在、Gateway微信connected，工具可执行；证据ignored operations/reminder-before.json。新Kimi路由采用原生配置＋精确目标tip原生完整writer＋受控宿主重建，不用已知会强制回Anthropic的/model路径。

发布准备：前端构建1d1b1a7，439文件22662600B，55个沿用哈希JS/CSS URL字节一致；候选已上传受限release目录，线上静态未改。Caddy2.11.7候选语法及8个响应压缩/缓存边界通过，另原生SIGUSR1同PID重载隔离实测通过；生产未改。正式入口隐藏IAB到Authelia登录页，未动用户现有页或登录；部署后可经获授权SSH回环观察单一正式后端真实历史/请求行为，明确区别公网认证链。

主会话第二次亲审纯图包通过：text同内容认领反证6失败已关闭；图片统一实际DB校验与原setter事务内owner/row/active/UID，guarded等值no-op不clone，默认旧setter行为保留。新增34场景及相关受影响60项有效通过；两项History及旧sidecar失败均有冻结原版复现，不冒称全套绿。纯图包未动Noting或agent/turn_context.py。

集成冻结检查：私有index与原始50214cd基线核10检查，8 guards/Ruff通过；随任务包新增的CDP汇总脚本有CC24及事件ladder两项，已等价事件分派拆分后ruff/health通过（0 blocking/advisory）。51事件×3筛选、2非法输入，原新输出逐字节一致；脚本修正164eb4f已提交。Noting6文件hash自审查后未变。完整证据ignored integration-check*.json/log。

最终发布：2026-10-21 01:28停启，01:30完成Caddy；后端0bdddfc、前端1d1b1a7。后验同200行身份一致，cards raw212094／离线gzip51160／同配置Caddy真实gzip54696B；历史静置0details/0image，显式一行6783B、进视口图488384B。原7排期／绑定／既有消息保持，Scheduler和微信链就绪；没有提前触发／测试发送。公网未登录、蜂窝与生产发图Turn未做，范围限制见final-delivery。
