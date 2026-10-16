# Verification：20261016-round3-secretary-nm

## 1. 审查对象与结论概览

审查者：全新独立 Astra/high 子 Agent（不派生）。2026-10-17。公共待审版本 `323c64dacba1190c16bacc69bbe5e76db6f43529`；个人待审版本 `e1af6cc45ffbd53c930d1d2f14ab46858e966ecd`。Snapshot Index 与 baseline.txt 位于本目录。公开冻结规格 `d19018a7ba3e38ae01f76aa57821b55cbc15ff58`；个人 PHASE3 冻结 `97078118287bcd41ba8b02aa5a3a108c5026f7af`。本地完整第三轮（R3-016–018），UI/Settings/Web DTO/云部署后置，真实 NM 写入未授权。

进入条件：主会话正式确认 Develop 集成收敛后按全轮派遣。当前阶段：固定版本首轮全范围调查完成。**Verification 不通过，不能进入 Validation**：V23 成功分发后的来源覆盖未结算；V51 多个绝对时间出口不符合格式契约；V01/V50 的首轮回归仍有未关闭证据缺口。其余条款的符合结论限于下述正式路径、运行环境与证据边界；不代表整轮交付判定。后继工作区修复不改写本次固定版本事实。

## 2. 独立要求清单与覆盖

本版于2026-10-17仅依据指定冻结规格建立，**在读取产品代码、测试、实现报告、plan、CLAUDE之前落盘**。已读白板全文（含末尾 types/scenarios 数据）、07全文、旧01/02/04/06适用保留原文及个人PHASE3现行§1–7。Snapshot Index仅用于确认版本/范围/会话明确授权。旧工具、Memo、Notebook排期耦合、special profile、旧Prompt冻结及UI后置项均不复活。标“重点”者为事件/接线容易被弱化的判据，未因未指定函数名而豁免。全部列项为直接要求或由上述直接要求必然推出的失败/并发不变量；目前无另增产品解释。后续若调整判据，必须在第6节保留原判据与原文理由。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| V01 | 01 §1/4/7；07 §2/3/9；06 §0.3–0.5 | 架构／全局 | 公开核心Hermes-first；仅Secretary自有表；无个人NM依赖、平行loop/DB/API/客户端owner | 沿原生正式接缝，原生schema/ownership及未启用行为保持；UI/部署不纳本轮 | §3 V01 |
| V02 | 02 §1.1–1.6；04 §2.1 | 身份／所有入口 | Conversation独立opaque owner；压缩/continuation同Ref，new/reset/fork新Ref；alias冲突fail closed | 可信locator和generation，物理session/路由不替代owner；只读工具不mint/bind | §3 V02 |
| V03 | 02 §2.1–2.4；04 §2.3–2.5 | Foreground／所有模式 | Active来自实际请求；History真实合法路径；Full单Prelude+逻辑节点，复合carrier唯一双投影例外 | 多模态、去重、rewind排除、跨压缩原文、真实Prelude/缺失反馈；三视图不混用 | §3 V03 |
| V04 | 02 §2.6–2.7/3.1–3.4；07 §3.1 | Snapshot／并发与分支 | 完整不可变Snapshot与entry版本；Anchor非compaction且排除noting_run_output；按有效路径coverage选pointer | 事务内插入/重选；旧Anchor晚完成不倒退；rewind无效拒绝、fork重新绑定无泄漏 | §3 V04 |
| V05 | 07 §4.1–4.3；白板C1–C4及types | Notebook数据 | work/situations/discussion/candidates；稳定entry_id+不可变version_id；类型固定与Snapshot版本固定 | 八类型准确字段/状态/默认；额外字段/重复数组/无来源拒绝；无长度限制 | §3 V05 |
| V06 | 07 §4.4/7；白板K6 | 工具create/update | 单条动作参数互斥；fields浅合并、数组全替换、对象整体替换；null只清可选 | 失败不改工作态；no-op不建版本不刷新时间；完整单条返回与可修正英文错误 | §3 V06 |
| V07 | 07 §4.2/4.4；白板C6/C8/K6 | 引用与archive | 当前视图引用；gap→situation；Candidate不引用Candidate；有入向引用拒绝 | referrers准确，archive只移出工作视图、不删原文/排期/外部写入；无归档召回 | §3 V07 |
| V08 | 07 §4.1/3.1；02 §5.10 | 来源／权限 | 每项至少非空规范来源或有效时间范围；新引用限当前路径；继承按原版本逐项绑定 | 不能用合法旧来源洗白新内容；同事务提交重验来源与开关、Anchor、版本 | §3 V08 |
| V09 | 07 §4.5/7.1；白板K1/K6 | show／Main及Noting | Main当前生效完整Snapshot，child当前任务草稿；模型无scope/task selector | 无Snapshot成功空；working不伪造snapshot_id；包含coverage、正确版本；普通视图无审计 | §3 V09 |
| V10 | 07 §4.5；白板D8 | finish／同步并发 | 混合finish批次执行前整批拒绝；成功请求在锁下固定草稿；runner等Turn返回再提交 | 重复finish保首结果；后写state_conflict；show/History只读仍可；非提交收据 | §3 V10 |
| V11 | 白板I1/I2/U1/U2/N1；07 §8.11 | 语义／索引创建更新 | 先更新旧索引再补建有用新索引；稳定身份、原文支持、真实变化才变龄期 | 任务提示含具体动作；无需活动可不改；旧交付内容不因重读重建 | §3 V11 |
| V12 | 白板C7/N2；07 §8.11 | 语义／用户研讨 | 逐点定位用户表达或认可范围；模糊确认不扩散；无回应AI问题不收；关闭问题不重开 | 提示完整及真实模型代表证据覆盖模糊确认、未回应、关闭、确定性 | §3 V12 |
| V13 | 白板C1/types.matter/T1–T5/L7；07 §8.11 | 语义／matter | 持续责任与整体完成独立于子行动；完成/解除/7天无进展同次处理 | 保留未完责任、聚合成果、归档无价值过程；不把沉默当完成 | §3 V13 |
| V14 | 白板types.action/T1–T5/L7；07 §8.11 | 语义／action | 接受责任/授权与建议区分；owner/完成条件/依赖；完成/7天同次处理 | 保留未完，成果并入事项或独立候选，结果保留后归档；报告不等于完成 | §3 V14 |
| V15 | 白板types.situation/L7；07 §8.11 | 语义／situation | 个人情景无需任务或可复用性；首次证据7天/失去用途处理 | 保留现用情景、聚合经历、无当前/留存价值才归档；不重置年龄 | §3 V15 |
| V16 | 白板C8/types.implicit_gap/L7；07 §4.1/8.11 | 语义／gap | 具体缺项+影响+情景；首次识别72h/回答/失效/情景处理 | 答案或已知变化补回情景；未知≠答案；不借gap收AI猜测；外部映射situation | §3 V16 |
| V17 | 白板C7/types.question/L7；07 §8.11 | 语义／question | 用户提出/认可/实质讨论；回答撤回或7天无讨论处理 | 当前未决保持；有价值讨论候选；无价值结束问题归档；沉默非放弃 | §3 V17 |
| V18 | 白板C7/types.insight/L7；07 §8.11 | 语义／insight | 用户表达/认可及确定性；7天/修正放弃处理 | 保留现用，聚合重要认识及变化，归档无价值旧见；不写AI论证 | §3 V18 |
| V19 | 白板C7/types.decision/L7；07 §8.11 | 语义／decision | 用户选择、范围、生效/结束条件；7天/取代撤销范围结束处理 | 年龄不撤销有效决定；重要选择及变化候选；无价值失效选择归档 | §3 V19 |
| V20 | 白板L0/L1/L2/L3/L4/L7/L9；07 §4.1/8.11/8.13 | 生命周期／容量 | 7天/72h只是处理点；同次精简与去留；时间未知先取证；processing_note实际时间 | no-op不续期；无额外到期timer/循环压缩/硬容量拒收；归档无恢复通道 | §3 V20 |
| V21 | 白板C2/C3/C6/C9/F1；07 §4.1–4.3/8.10–8.11 | Candidate | 聚合description+稳定refs+原文provenance；直接原文可空refs/types；来源原位 | 来源类型映射集合准确、反向refs派生；源更新需修候选；无正文搬家或重复提案 | §3 V21 |
| V22 | 白板L6/F1/F2；07 §8.5/8.10 | Persistence／Main | slash/超限同一指令启动具体提案；按需回读现行原文、纠正；显式批准内容目标才写 | 包含实际entry/version/范围/标签/provenance/结果；不盲重试未知；目标元数据非公共成功门禁 | §3 V22 |
| V23 | 白板E1/E2/N1；07 §8.11 | Settlement／Noting | 只看Conversation批准及实际分发轨迹；部分成功按覆盖结算 | 保留新变更、未完责任、其他候选需要来源；修引用；失败未知不清退；不读目标存储 | §3 V23 |
| V24 | 07 §5.1/5.4/7 | History参数 | search、anchored read、unanchored read分模式验证默认与互斥 | canonical identity；跨域read须锚点+明确开关；无锚只当前；锚点必达或source_unavailable | §3 V24 |
| V25 | 07 §5.2/5.5；04 §2.2 | History资格 | 真实Main、同owner Profile、授权用户Conversation；Noting仅父域 | Ref/role=user/binding非授权；auxiliary不漏；query不写binding、不跨profile探测 | §3 V25 |
| V26 | 07 §5.2 | History搜索机制／重点 | 原生FTS/CJK/trigram/LIKE/OR；有界物理候选→membership→合法History/visibility | 合法inactive fork保留；消息时间含端点；稳定路由/gap推进去重；预算min(10000,max(1000,20*limit))、批200 | §3 V26 |
| V27 | 07 §5.2–5.4/7 | History反馈 | diagnostics区分语法错/完全失败/降级/预算；partial真实反映是否枚举完成 | 不把故障空数组当无命中；实际字面命中~800窗口；full/match/fallback诚实；分组无假总数 | §3 V27 |
| V28 | 07 §5.3/9.1；02 §2.2 | History Read与预算 | 原始结构+逻辑邻居；多模态不冒已读附件；原生spill和批预算保留 | Noting真实裁剪反馈缩窗口，单条过大明确不可读；不诱导read_file/terminal；其他runtime原生不变 | §3 V28 |
| V29 | 07 §2/5/7；白板A7/K1 | 旧面退出 | 当前Schema/同步并发dispatch无旧Notebook工具/Memo/compact_parent可执行alias | legacy session_history/message_id明确legacy_tool_removed和新路由；历史不重写/不执行 | §3 V29 |
| V30 | 07 §6.1/7；白板K2/K3 | Scheduler CRUD | Main绑定当前Table；六动作及参数互斥；runtime只读字段不可写 | 完整Table/单项/删除ID、时区/nextdue/pending/last_delivery；失败诚实、no-op明确 | §3 V30 |
| V31 | 07 §6.2；白板K4/K8 | Scheduler时间与owner | 复用原生解析/时区/周期推进；30m周期、in30m一次；独立owner | new/reset/fork不复制；compaction同route；Notebook状态/pointer无双向副作用 | §3 V31 |
| V32 | 07 §6.2；02 §3.9–3.12 | Scheduler可靠投递 | due scanner持久claim/lease/去重；instant原生idle/busy gate；busy转deferred不排未来Turn | 延期一次性仍投递、周期不补无限；失败不丢失；重启恢复；路由generation/profile隔离 | §3 V32 |
| V33 | 07 §6.2 | Scheduler并发变更／重点 | update/pause/delete与claim同事务；materialize及ActiveAdmission.commit最终重读 | 旧worker不可复活；未接纳变更/撤销；已接纳保witness并标in_flight；ACK不激活改动Schedule | §3 V33 |
| V34 | 07 §8.14；02 §3.11/5.6 | Deferred ACK | 同批一个durable carrier绑定全部occurrences；请求组装前materialize | 实际请求携带+成功响应逐项ACK；失败留pending；compaction pass不吞新载体；退休按既有规则 | §3 V34 |
| V35 | 07 §6.4/8.14；白板K5 | 24h notice／工具 | 每次调用成功/无修改/失败后读完整Table，含端点、逾期instant、周期下一次 | notice仅空档；未知不谎报无；不变原操作结果；不看筛选子集、不建timer/自动排期 | §3 V35 |
| V36 | 07 §6.4/8.14 | 24h notice／Reminder | instant及busy转deferred最终注入时重算，排本次occurrence；一批仅一次 | 纯deferred不新增入口；有覆盖省略；未知提示；不另发Framework/Turn | §3 V36 |
| V37 | 07 §6.3；白板P1/P5/K7 | 配置 | 独立Noting/Scheduler与local；Idle默认off、500s、开启需正threshold；proposal12000/60 | 旧keys明确报替代；坏配置只关所属功能；原生idle互斥；off保数据且停新投递 | §3 V37 |
| V38 | 07 §8.1；白板P1–P4 | 联合入口／重点 | manual/auto/Idle在原生压缩前freeze并行child，不等待；Noting失败不挡必须压缩 | 所有正式压缩路径接线；压缩失败不撤合法Snapshot，不重整同已受理范围 | §3 V38 |
| V39 | 07 §8.1；02 §4.6–4.9 | Force区间／重点 | 原生Resolved窗口测量余量max(1.2*reserve,66K)，阈值<64K或reserve>128K拒绝 | 同admission事务按成功compaction区间占用；换Anchor/失败/rewind不解锁；所有联合入口共享；成功压缩才新轮 | §3 V39 |
| V40 | 07 §8.1/6.3；02 §4.5 C16 | Idle事件／重点 | 仅Main结束计时、start取消；一次deadline事件；local开关只在事件消费时判 | 同时满足delay+真实占用；child不重置；off处理事件不重试；恢复catch-up同handler、不周期重造 | §3 V40 |
| V41 | 04 §4.5 D01；07 §8.1 | 执行来源 | 最新实际派发native/external内存及model_config同事实；unknown不新拒绝 | 四入口副作用前拒External；不妨碍压缩/History/Scheduler；native恢复重置suppression，fallback按实派 | §3 V41 |
| V42 | 07 §3.1/8.1；02 §5.6 | Force/External通知 | 原Framework producer保留；External同runtime/conv一次；Force成功压缩才退休 | busy/fence遵守；未成功compaction不退；耐久审计保留且摘要/tail不带旧Force通知 | §3 V42 |
| V43 | 07 §3/8.11–8.12；02 §5.1–5.5；04 §4.4 C13 | child生命周期 | 原生AIAgent独立SessionDB/父身份/线程profile/强引用/close；只持久suffix | 无父transcript复制、无child restart-resume/auto-compaction；failure释放资源 | §3 V43 |
| V44 | 07 §3.1/8.12；04 C13/§4.6；02 §5.11 | cache parity／每请求 | 同一父root/tools有序完整Schema/多模态Active冻结prefix，累积suffix，原生模型/provider | 每工具循环/重试/continuation不改头；完整四Schema随新control追加；真实调用可行与缓存读取分别有证据 | §3 V44 |
| V45 | 07 §3.2/4.5/8.11–8.12 | 权限与完整任务 | 唯一Noting profile，四工具真实sync/concurrent白名单；初始及续Turn全工作视图 | 禁止继承父工具放权；六步及逐类动作完整注入；父后变更不刷新child | §3 V45 |
| V46 | 07 §3.1–3.2；04 §4.6；02 §5.8 | 结束/失败 | 最多五原生Turn；文本完成非正常结束；合法视图forced/context_overflow仍尝试commit | 三termination正确、无修改可提交；真实中断/失败不伪成功；不请求父compact | §3 V46 |
| V47 | 07 §8.13/11.1；白板N3 | 完成投递／重点 | 仅本次commit成为新pointer准备；实际durable/live追加在同一致性边界重验pointer | 排队过期整条丢弃含proposal；完整Snapshot+notice同条、完成时间非dispatch；并发不需B→C合并 | §3 V47 |
| V48 | 07 §8.13；白板L1/L9 | 超限提案 | 有效Snapshot正文Unicode码点>12000或现行entry>60，同消息尾共用proposal | 不含wrapper/通知/指令；引用不重复数；不截断/拒交/自动删/重跑；失败无伪snapshot | §3 V48 |
| V49 | 07 §8.2–8.10；04 §3.1–3.5 | Main Prompt/工具生命周期 | 精确英文常量与独立资格；History恒定、Notebook global、Scheduler自身；原生stable/context/volatile | next pre-message global热切换root/tools/dispatch一致、cold pinned不复活；local不重建；Cron私有copy | §3 V49 |
| V50 | 07 §8.10/9.1；02 §3.6及2731–2733 | Slash | /noting只持久local；/notebook只读当前可读时间、无内部ID/审计；/propose共用指令 | local off仍读；human-only不入模型History/摘要；无需预搜原文；Memo slash退出 | §3 V50 |
| V51 | 02 §5.6；07 §8.13–8.14 | 载体与时间 | user角色wrapper；仅真实user及instant有timestamp且实际入ctx时刻；秒精度带时区 | durable/live/tail同步；framework不唤醒、无重启必达；重试不重铸；所有模型可见绝对时可读 | §3 V51 |
| V52 | PHASE3 §1–2/7；07 §2 | NM隔离/单Provider | 仅个人仓；现有system_prompt/prefetch/sync_turn；无NM tools/MCP/第二插件/loop | native memory/profile关闭不删文件且外部Provider仍可注入；NM失败不关公共History | §3 V52 |
| V53 | PHASE3 §2 | NM资格矩阵 | 真实Main bundle/recall/sync；Cron仅物理sync；Noting不独立取bundle/recall/sync；aux/unknown拒绝 | 真实origin/source/parent/delegate与只读绑定；不凭user role/Ref，不mint/跨profile | §3 V53 |
| V54 | PHASE3 §3.1/6 | NM Bundle | include_working_memory=false；Global Rule+Bundle随原生prompt构造恢复压缩 | 不每Turn改root；离线/非法明确；不以WM/猜背景替代；规则与公共prompt分离 | §3 V54 |
| V55 | PHASE3 §3.2–3.3 | NM Recall | 原host admitted有意义input→Memory Search无LLM/ask；默认8/2/5/2400；短CJK不一概拒 | 完整ID标题时间无正文/假置信；不可信编码；失败无旧指针；固定提醒；queue_prefetch no-op；承认api_content重放边界 | §3 V55 |
| V56 | PHASE3 §4/6 | NM Main流程 | 官方CLI正常读写；用户具体批准；查重复过时矛盾与原文限定；标签notebook:type及metadata规范source | 不假称代码批准门禁；不改premise/space/policy；direct来源不伪造，gap映射situation；Noting不审核目标 | §3 V56 |
| V57 | PHASE3 §4.1；R3-008–010 | 窄脚本／基本检查 | 官方nmem --json m add创建、真实ID、仅补hermes_provenance保无关metadata；同主机有效配置 | 无直接HTTP创建正文/第二配置；创建未知不猜ID重建；metadata失败报告ID仅修附件；本轮不加严格真实写门禁 | §3 V57 |
| V58 | PHASE3 §5 | NM归档正文 | completed且不中断；Main合法跨压缩History+host egress；Cron物理正文；只user/assistant时间 | 无tool payload/模型专用注入；Noting/aux不独立sync；正式host接线到本地fixture证据 | §3 V58 |
| V59 | PHASE3 §5 | NM Thread身份/账本 | hermes-personal-<conv_ref>，Cron/native fallback物理session；new/fork分开/compaction同Thread | owner HERMES_HOME receipts按endpoint/space/thread；明确ACK才推进prefix；divergence停止reconciliation-required | §3 V59 |
| V60 | PHASE3 §5–7；R3-005/006/010/018 | NM验收边界 | at-least-once不假exactly-once；Background Intelligence政策关闭，无自动治理/蒸馏 | 无真实NM Memory/Thread/Space写入、无云部署声明；round3统一实测，fixture不冒真实服务验收 | §3 V60 |

## 3. 逐条实现证据

每行沿第2节同编号的“原文 → 必要不变量”核查实际路径。固定提交中的代码是判定对象；实现报告只作为定位，关键事务/正式调用点已直接阅读。`符合`指该条在列明条件和证据内成立，不是“测试通过所以符合”。跨条缺陷仍阻断全轮。

证据简称（均在本地，可回查；不输出请求头、凭据或完整 root）：

| 编号 | 路径与用法 |
|---|---|
| E1 | 本目录 c5-report.md（C1/C5）、c6-report.md、c4-report.md、c7-report.md、c8-report.md、c9-host-report.md、c9-surface-report.md、c10-notebook-history-report.md、c10-runtime-report.md、c10-delivery-report.md、c10-final-legacy-report.md、c10-personal-report.md 及其 ignored 日志索引；准确复用文件/版本边界以 regression-plan.md §3 为准。报告中历史失败不冒充现版本成功。 |
| E2 | 公共 `.hermes-dev/round3-local-20261017-l0/real-model/`，本目录 real-model-report.md；实际 native DeepSeek chat_completions/CLI/TUI RPC。初始语义证据依原执行版本保留；最终 f66a8 至323c生产无差异。 |
| E5 | 个人 `/Users/edgar/code/hermes-nmem-provider/temp-r3-personal/evidence/c11-p/`，本目录 personal-host-report.md；已独立核 manifest 全部文件hash相符。真实 Hermes host/模型到本机HTTP fixture，非真实NM。8682ff至e1af6仅动态文档差异。 |
| E6 | 公共 `.hermes-dev/round3-runtime/evidence/verification/`：criteria-initial.md/sha256 保留判据先行初版；raw-evidence-recheck.json 独立重算169文件hash、43请求前缀/有序Schema；prompt-constant-recheck.json 核12个常量与冻结07逐字相等。 |
| E7 | 最终统一回归的个人 provider46 组：两源文件symlink经canonical runner，31+15=46 PASS；不重复旧39项。具体命令、版本、日志见E8。 |
| E8 | 本目录 regression-plan.md §7 以及 `.hermes-dev/round3-local-20261017-l0/final-regression/` execution-manifest.json、failure-triage.json 和各组原日志。唯一owner执行；本审查未重复运行大型检查。 |

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| V01 | 原生 AIAgent → turn_context/turn_api_call/turn_finalizer；SessionDB 的 secretary_* sibling；personal 插件独仓 | 审 schema/导入边界、原生关闭分支及136文件邻域；统一回归1766 PASS但29 FAIL/4 setup ERROR，原生压缩5项与 ACP 依赖1项待逐项关闭 | E8 §7.2–7.3；agent/context_compaction_request.py:20；run_agent.py:913 | 证据不足：结构符合，无公开NM依赖；未启用原生零变化的完整回归尚不能确证 | UI/Settings/Web DTO/云部署不在本轮；不以旧断言失败等同生产缺陷，也不豁免失败 |
| V02 | CLI/TUI/Gateway Session bootstrap → hermes_state_secretary_identity.ConversationIdentityMixin → binding/route；History只读 resolver | 逐路径检查压缩 continuation、显式 fork/new/reset、alias冲突、generation；只读查询不用mint路径；r3_history/notebook与已有identity证据交叉 | hermes_state_secretary_identity.py；hermes_state_conversation_history.py；E1/C10-A；E8 state失败明细 | 符合：opaque Conversation owner 与物理locator分离，冲突拒绝，读取不创建身份 | 旧 lifecycle 15项被终结审计夹具阻断，不能把其原主体写成此次通过；现行r3和静态事务链提供独立依据 |
| V03 | 原生持久/压缩/rewind → hermes_state_secretary_foreground → Active/History/Full投影 | 核当前winning UID、compacted/inactive fork membership、branch exclusion、复合carrier双投影、Prelude实际捕获；真实多模态prefix及跨压缩History | hermes_state_secretary_foreground.py:155–227、230–347；E1/C10-A；E2；E5 | 符合：原文路径和实际请求分离，唯一复合carrier有明确双投影；丢失Prelude不伪造 | 附件结构可返回不等于已读取图片语义；不借Notebook恢复归档 |
| V04 | NotebookStore.commit → notebook_commit_snapshot → insert versions/reselect pointer，同原生rewind/fork事务reconcile | 审固定base、有效Anchor、coverage优先晚完成、rewind无效拒绝、fork版本和来源重绑定；r3_notebook与Framework竞争事务用例 | secretary/notebook_store.py；hermes_state_secretary_notebook.py:153–207；hermes_state_secretary_foreground.py:368–426；E1/C1/C8 | 符合：Snapshot完整不可变，pointer按合法路径位置择优，读不重选；Scheduler不随fork复制 | 不要求后启动C继承未提交B；旧夹具失败列E8，不能混写成现行事务失败 |
| V05 | notebook_maintain → NotebookWorkingState → notebook_contract/immutable versions | 逐类型字段/默认/状态/额外字段/来源校验；真模型初始13条覆盖七类来源及Candidate；受控大文本合法提交 | secretary/notebook_contract.py；secretary/notebook_model.py；E1/C1；E2 snapshot-first-entries.json | 符合：8类型、4区域、稳定entry与版本身份、无正文硬限 | 真实样本覆盖代表语义，不承诺任意模型输出均正确 |
| V06 | 同步/并发 notebook_maintain → bound store锁 → create/update/_persist | 审先校验再变更、浅合并/数组全替/null、deepcopy；no-op原timestamp/version返回；参数互斥和英文error | secretary/notebook_model.py:112–198；secretary/noting_tools.py；E1/C1/C5 | 符合：失败无半写，真实变化才建version，返回完整单条 | 时间可读投影另在V51不符合，不把内部高精度当缺陷 |
| V07 | NotebookWorkingState._validate_state/archive → refs/referrers；public_state反向引用 | 检查现行引用、Candidate禁止引用Candidate、gap映射、archive入向引用失败；真模型先修引用再archive gap/candidate | secretary/notebook_contract.py；secretary/notebook_model.py；E2 semantic-second-tool-trace.json | 符合：归档仅退出工作视图，历史审计保留，不召回/不触排期或外部写入 | 某来源未被archive的语义缺口属于V23，非archive工具权限缺口 |
| V08 | NotebookStore捕获base+source_basis → notebook_items.same_source_claim → commit重验 | 新source限父合法History；继承basis精确绑定entry版本内容，改正文不能靠旧source洗白；事务检查开关和Anchor | secretary/notebook_store.py；secretary/notebook_items.py；E1/C1/C5、r3_notebook | 符合：来源权限不依赖模型声明，继承/新建路径分开且提交重验 | 不能从scope=parent参数自封权限；个人provenance窄脚本另按V57基本检查 |
| V09 | Main notebook_show → current Snapshot；Noting notebook_show → current working_view | 核空Snapshot成功、无scope/task selector、完整区域和版本、working无snapshot伪ID；真实Main/tool与slash对照 | tools/notebook_tool.py；secretary/noting_tools.py；secretary/notebook_render.py；E2 f13-model-show-response.json | 符合：两个身份入口选择各自唯一视图；无归档审计表暴露 | 日期格式V51；human入口只去内部pointer/Anchor头，不去合法entry/version标识 |
| V10 | turn_tool_validation/secretary_dispatch original batch → finish_noting → locked freeze → child runner | 审原批次在filter/validation前检查，sync/parallel均整批拒绝；首finish冻结；重复保首结果；等Turn返回才commit | agent/turn_tool_validation.py:94；tools/secretary_dispatch.py；secretary/noting_tools.py；E1/C5/C9-S | 符合：混合批次不能执行部分维护或finish；finish收据不冒持久提交 | 失败/中断在V46；show/History在freeze后仍可读 |
| V11 | Noting原生task注入 DEFAULT_NOTING_TASK_INSTRUCTION → 四工具维护 | 12个冻结英文常量逐字复核；task六步先对已有索引取证更新，再补缺失；真实第二轮改变既有版本而非整表重建 | E6 prompt-constant-recheck.json；E2 snapshot-first/second-entries.json | 符合：指定动作完整，稳定身份/no-op机制支撑语义 | V23证明Prompt逐字相等不能替代实际语义结果 |
| V12 | Noting task的user-owned discussion分支 → History回读 → maintain | 核逐点认可、无回应AI问题排除、关闭不重开；真实样本模糊“一实一虚”未扩为普遍接受，关闭问题保持退出，未回应问题未建 | secretary/noting_prompts.py:3；E2 semantic-first/second相关trace、snapshot-second-entries.json | 符合：已见代表性反例输入下保持用户归属和确定性 | 未声称概率性模型能对所有未来输入保证相同语义 |
| V13 | task matter对象分支 → update/聚合Candidate/archive | 逐项对照白板matter字段、整体责任与子行动不等价、7天处理点；实际1完成而2仍未完成的差异保留 | secretary/noting_prompts.py:3；secretary/notebook_contract.py；E2 snapshots | 符合：原文支持的整体责任单独判断，年龄不自动完成 | 其它时间跨度由受控旧日期输入/Prompt机制覆盖，不等待真实7天 |
| V14 | task action对象分支 → matter链接与独立候选维护 | 检查接受/授权而非建议、owner/完成条件/依赖；真实4完成而3未完成；无自动排期耦合 | secretary/noting_prompts.py:3；E2 snapshots与semantic trace | 符合：完成成果有保留去向，未完行动不因摘要/沉默清空 | 成功交付来源清退另见V23 |
| V15 | task situation对象分支 → evidence_time/当前用途 → maintain | 对照首次证据年龄、个人经历无需任务、现用情景保留；真实情形5按新答案更新、35为独立新经历 | secretary/noting_prompts.py:3；E2 snapshot-second-entries.json | 符合：情景不强行变行动或普适结论，正常更新不重置首次证据 | source6交付后继续保留为V23明确失败，不借本行绕过 |
| V16 | task implicit_gap分支 → 指定situation引用 → 更新情景后archive gap | 72h/回答/失效具体动作与未知不当答案；真模型11/12因有答案退出，答案进入5；source_type映射situation | secretary/noting_prompts.py；notebook_contract.py；E2 second trace | 符合：具体缺项与情景关联，答案先回写，未读附件不推测 | 没有新增到期timer |
| V17 | task question分支 → 用户归属/last_discussion_time → retain/candidate/archive | 对照回答撤回/7天只是处理点；真实7仍open，已关闭问题不重开，未回应AI问题不新建 | secretary/noting_prompts.py；E2 snapshots/trace | 符合：用户研讨边界和关闭语义有真实样本支撑 | 不因沉默自动放弃 |
| V18 | task insight分支 → 用户认可范围/确定性/变化聚合 | 检查AI论证不记成用户认识；真实8保持tentative而非确证；旧观点改变按同entry维护 | secretary/noting_prompts.py；E2 snapshot-second-entries.json | 符合：未提升确定性，有用认识与无价值过程分流 | 不以年龄自动删除重要认识 |
| V19 | task decision分支 → scope/end条件 → maintain | 核年龄不撤销有效决定、撤销/替代/范围结束才变；真实9按范围结束expired，10保留具体批准范围 | secretary/noting_prompts.py；E2 snapshots/trace | 符合：范围与有效性独立于最后讨论日期 | 用户批准记忆分发不外推其他目标 |
| V20 | task逐类型aging分支 + NotebookWorkingState no-op + notification超限 | 逐类7天/72h、取证未知时间、同task精简去留；no-op不续期；计数仅通知不拒绝commit；无到期定时器/归档召回 | secretary/noting_prompts.py；notebook_model.py；noting_notifications.py；E1/C1/C8 | 符合：机制不强制容量清理，不重置没有变化的年龄 | processing_note仍可能由模型错误解释，实际source6失败单列V23 |
| V21 | candidate fields/ref validation → derived candidate_refs → task更新候选 | 核refs/types集合、gap映射、direct原文可空refs/types；source保原位；真实13聚合情形6、旧来源有更新时维护候选 | secretary/notebook_contract.py；notebook_model.py；E2 proposal-first-response.json | 符合：候选是聚合索引与提案，未搬走source正文，不授权写入 | 结算后清退由V23单独判定 |
| V22 | /propose-persistence/超限Framework → 相同 PERSISTENCE_PROPOSAL_INSTRUCTION → Main原生Memory tool | 逐字冻结常量；真实具体USER提案→用户明确批准→75字符合成USER实际成功；核entry/version、source、target、结果轨迹 | hermes_cli/cli_secretary_commands.py:78；noting_notifications.py:30；E2 proposal-first-response.json/memory-after.json | 符合：提案不是许可，具体批准后执行，未知不得盲重试的规则已注入 | 未进行真实NM或多目标部分成功写入；不得把未批准其他内容称作目标写失败 |
| V23 | Main成功分发History → Noting step4 → maintain Candidate与来源 | 首真实样本：Candidate13 archive成功，source6 v34仍保留已交付探视经验；仅processing_note称“来源情形本身保留”；新经历独立35，无其他候选依赖/未完责任支撑6 | E2 notebook-after-settlement.json、semantic-second-tool-trace.json native150/157/173、memory-after.json；F-V23 | 不符合：只清退Candidate，未移除/精简已成功交付的source覆盖；Prompt正确不能推翻实际反例 | 不推断模型永久失败；本次实际轨迹已足以阻断，修复须真实重做并保留首失败 |
| V24 | conversation_history Schema → validate_request → search/read | 完整检查presence而非truthy、三模式互斥、bounded limits、canonical anchor及cross开关；真实工具read/search与r3参数反例 | tools/session_history_tool.py；E1/C2/C10-A；E2/E5实际History调用 | 符合：无锚只本域，跨域明确ref+anchor+开关，锚不可读不降为任意窗口 | 旧session_history参数明确退休，不当兼容alias |
| V25 | dispatch Main/noting eligibility → SessionDB.conversation_history_scope → logical user-owned membership | 核真实origin/parent/role/profile、Noting running admission与parent、只读snapshot；aux伪role/user/ref不能授权；无跨profile DB探测 | hermes_state_conversation_history.py；tools/secretary_dispatch.py；E1/C2、r3_history | 符合：资格、归属与locator分开，查询不写binding | 原生非eligible session_search维持原权限而不获得Conversation工具 |
| V26 | search → native search candidates(read txn) → membership → legalHistory/visibility | 逐语句追FTS/CJK/trigram/LIKE/OR、batch200/预算公式、route/gap各自cursor与physical dedup；fork inactive来源后验保留；时间端点比较 | hermes_state_search_candidates.py；hermes_state_conversation_history.py；E1/C2、r3_history | 符合：不是全表先过滤active，跨域noise也受候选预算约束 | 有界搜索不宣称全部命中；耗尽预算的partial另见V27 |
| V27 | search route diagnostics → results/excerpt/partial | 核语法异常与所有route失败、LIKE降级、probe判断实际还有候选；800字面窗口与fallback标记、group不虚构总数 | tools/session_history_tool.py；hermes_state_search_candidates.py；E1/C2、r3_history | 符合：故障不冒无命中，partial反映实际穷尽程度 | FTS排名不等于语义真实性，原文仍是事实源 |
| V28 | anchored read逻辑邻居 → 原生 tool_executor result budget/spill → Noting裁剪反馈 | 审多模态原结构、单条过大/批裁剪反馈，提示缩窗口且不给read_file/terminal绕过；正常runtime spill保留 | tools/session_history_tool.py；agent/tool_executor.py Noting feedback；E1/C9-S/C2；E2多模态 | 符合：原生预算继续生效，Noting可知道未完整读到哪些内容 | 没有凭结构返回宣称模型已见附件；真实图片可发送与语义识别分开 |
| V29 | Schema catalogs/secretary_dispatch/inline+parallel executors → legacy rejection | 检索旧profile/工具入口，无旧Notebook/Memo/compact_parent执行alias；session_history/message_id报legacy_tool_removed；原历史保留 | tools/secretary_dispatch.py；agent/inline_tool_executors.py；E1/C9-S；E8 loop旧断言5FAIL | 符合：退休面不可调用；旧测试期待旧工具名的FAIL不能用复活工具消除 | 原生非eligible session_search仍可存在，并非退休对象 |
| V30 | Main scheduler tool → bound owner → schedules._execute → scheduler_table action → DTO | 逐动作create/list/update/pause/resume/delete和互斥/runtime只读、empty/no-op、完整table/单项/删除ID；真实注册/读取/暂停 | tools/scheduler_tool.py；secretary/schedules.py；scheduler_table.py；E1/C3/C6；E2 scheduler-* | 符合：独立Table与正确CRUD收据；异常不伪操作成功 | canonical.run_at微秒另见V51；health异常日志缺口另见F-REG |
| V31 | scheduler_time → cron.jobs.parse_schedule/compute_next_run → bound Conversation schedule | 检查in30m一次、30m周期、原生timezone/DST、过期一次仍有效、bounded跳周期；fork/new/reset不复制，压缩route继续 | secretary/scheduler_time.py:34–116；scheduler_table.py；E1/C3、r3_scheduler | 符合：只有时间adapter，不引入新通用调度器，Notebook与Schedule无同步写依赖 | 跨平台没有伪造sys.platform |
| V32 | profile scanner → schedule_claim_due → native host admit idle/busy → pending/lease retry | 审持久claim/token/generation/owner、崩溃重试；真实idle instant唤醒、busy只pending、下一Main带入、真实host重启Table保留 | hermes_state_secretary_schedule.py；secretary/reminders.py；E1/C10-B SIGKILL；E2 scheduler-busy-lifecycle/restart | 符合：busy不预约未来Main Turn，重启不丢状态，失败不会清掉待投递 | 本机CLI/TUI/Gateway受控可靠性；不宣称所有网络服务exactly-once |
| V33 | CRUD transaction → claim revalidate → pending materialize → ActiveAdmission.commit最终read | 核update/pause/delete清未admitted旧claim，admitted保witness标in_flight；last-moment新generation不能由worker复活；ACK无schedule重新激活 | secretary/scheduler_table.py；reminders.py；hermes_state_secretary_schedule.py；E1/C6/C10-B、r3_delivery | 符合：同txn最终定义决定实际投递，不凭prepared文本或旧claim | 真实竞态主要由受控DB/native caller验证，不冒称实网重现所有race |
| V34 | turn preflight pressure-only → assemble_api_request materialize → verify carried → successful provider response → ACK | 审一个durable carrier绑定全occurrence、native重试与响应判别、compaction前不materialize；真两deferred一carrier双ACK | agent/turn_request_assembly.py:124；turn_api_call.py:119–212；secretary/reminder_request.py；E2 scheduler-deferred-after-response；E1/C9-H | 符合：实际请求携带+真实响应才ACK，失败留pending；响应空/伪mock结果不当ACK | Interrupted redirect在ACK前break保pending；at-least-once不冒exactly-once |
| V35 | 每次scheduler result/exception → read full table → 24h coverage →附notice | 审含端点/逾期instant/周期下一次、完整Table非list过滤结果、unknown不报false、失败保原结果；无定时器 | secretary/schedules.py；scheduler_table.py complete_table_coverage；E1/C3/C6 | 符合：成功/noop/失败都走同覆盖出口；read失败不会制造无覆盖结论 | 只提示，不自动排期；实际模型仍负责是否安排 |
| V36 | instant native admission/忙转deferred materialize → final coverage(exclude occurrence) → carrier | 审最终注入前重读、排本次occurrence、一批一次；纯deferred不新增提示入口；实际busy/deferred/instant证据 | secretary/reminders.py；reminder_request.py；E1/C6；E2 scheduler-busy-lifecycle-evidence.json | 符合：提示与本次carrier同边界，不能另唤醒或多发Framework | 有其他有效instant则省略；unknown有诚实提示 |
| V37 | 原生config → noting_policy.resolve_* → owning_db_scope → runtime tools/trigger gates | 核默认Noting/Scheduler独立true、Idlefalse/500、threshold正值、proposal12000/60、旧keys替代错误、坏配置分区关闭；真实独立off | secretary/noting_policy.py；noting_scope.py；E1/C4；E2 switch-request-evidence/scheduler-global-off | 符合：不借Noting关掉Scheduler或History，off保数据停新动作 | 已有admitted载体ACK保留与停新投递区分；UI展示后置 |
| V38 | compress_now/_compress_context → prepare_noting_for_native_compression → prepare_joint_noting → spawn，再原生compress | 审manual/auto/Idle marker只prepare一次，冻结先于native变更且不等child；实际manual28→15、auto9→3、Idle真实先spawn | agent/context_compaction_request.py:20–29；secretary/noting_runtime.py；E1/C9-H；E2 idle-final-evidence | 符合：Noting错误/关闭不阻原生必要压缩，原生失败不撤合法snapshot | 原生零变化回归未全闭见V01；不把真实压缩no-op称成功 |
| V39 | Force native resolved measurement → thresholds → admission write txn → native successful publication interval | 审max(1.2reserve,66K)、边界64K/128K、整数精算；物理publication(session,id)释放而非UID；失败/rewind/child状态不解锁；实际F11 | secretary/noting_policy.py；hermes_state_secretary_noting.py:104–161；hermes_state_compression.py；E1/F11-F12；E2 f11-* | 符合：四入口共享Force占用；新Anchor不能绕过，同UID新成功publication能开新区间 | 未要求所有manual admission互斥；占用语义依规格Force区间 |
| V40 | Main start/end → noting_idle_state deadline → timer/重启catch-up → claim_event唯一local判定 | 审新Main取消、child不改clock、原生真实usage、事件过期仅一次、localoff消费删除不重造；真实不足阈值/满足阈值与取消 | secretary/noting_runtime.py:312–374；hermes_state_secretary_noting.py:249–276；noting_timers.py；E2 idle-final-evidence | 符合：single deadline owner，不用tick无限重复判local开关 | 恢复catch-up同handler；非本机计时平台未模拟 |
| V41 | 实际request dispatch main_model_request_scope/adapter → runtime+model_config source → 四trigger gate | 审不是按URL静猜；external派发记事实、unknown不新拒、native恢复清suppression；四入口副作用前挡child、保原压缩HistoryScheduler | secretary/noting_runtime.py；agent/turn_api_call.py:112–165；native/external dispatch接缝；E1/C7/C9-H r3_joint | 符合：D01判实际来源，持久和内存同事实；fallback依实派 | 本轮未启用AppServer/Proxy；外部路径以受控接缝证据而非真实服务执行 |
| V42 | Framework producers → runtime queue/native append；compression_force_notice capture → candidate → commit retire | 核External同runtime/conv一次、native重置；Force只有实际commit后退休、失败留在原文、summary/tail不携旧通知；busy/fence排队 | secretary/framework_messages.py；agent/compression_force_notice.py:40–126；E1/C8/C10-T；E2 F11 | 符合：原通知机制保持at-most-once与审计，退休不等于删除历史 | Framework没有重启必达保证，不产生未来Turn |
| V43 | spawn_noting_task freeze同步 → owned native AIAgent/SessionDB/thread profile → run → finally close/registry | 审独立DB、强引用、native runtime/provider继承、skip memory/auto-compaction、父prefix不存child；真实31跨Turn请求结束资源释放 | secretary/noting_child.py；noting_scope.py；E1/C5；E2 native-continuation*、process-release | 符合：child状态归原生生命周期，持久只suffix，不重启resume后台task | 没有创建平行Agent Loop或专用provider routing |
| V44 | freeze_parent_active_prefix/FrozenParentPrefix → 原生repair/build_api_messages/request assembly →每tool/continuation | 独立核169请求文件hash全符；直接重算7+5+18+13=43调用parent prefix与orderedtools相等；不同user/assistant尾、多模态、五Turn；另实usage cache读取 | agent/cache_parity.py；secretary/noting_child.py；E6 raw-evidence-recheck.json；E2 prefix+usage证据 | 符合：冻结root/tools/messages每请求不变，新增内容只在suffix，继承原生模型可实际调用 | 比较解析JSON及保序序列化，未拦截HTTP字节；cache usage观测不等同保证服务永久命中 |
| V45 | task与每continuation _working_control → 4完整Schema；secretary_dispatch真实白名单 | 核父工具header保留但不可调用；初始/续Turn完整currentworkingview+supersede声明；同taskscope不随父变化刷新；严格finishbatch | secretary/noting_tools.py:157；noting_child.py:644；tools/secretary_dispatch.py；E1/C5；E6 prompt constant | 符合：唯一NOTING，四工具具备完整定义且权限在执行层，不靠Prompt自律 | 原父历史可含旧工具但执行仍被拒；公开不增加个人Provider工具 |
| V46 | native run_conversation Turn result → child loop<=5 → finish/forced/overflow commit → terminal registry | 审纯文本不结束task、失败interrupt不commit、合法无变化可commit、overflow保合法state；真实两个受控probe五Turnforced+正常自然finish | secretary/noting_child.py；E1/C5；E2 native-continuation*-evidence、real-model-report | 符合：三termination明确，成功/失败区分，资源释放且不请求父compact | 两个probe不是自然第二Turnfinish；未伪称模型配合特定结束形态 |
| V47 | Notebook commit result → enqueue completion → native append prepare+beforecommit pointer重验/live同步 | 读完整事务与rollback路径；竞争writer被DB锁隔离、owner变rollback、fence后过期整条连proposal丢弃；不是先检查后异步拼接 | secretary/framework_messages.py；E1/C8；tests/secretary/test_r3_framework.py:151–227、319–337 | 符合：durable/live实际追加与pointer一致性同边界；已发A后B成为新pointer属于合法历史 | 不要求未提交B被C合并；append失败最多一次不影响已commit Snapshot |
| V48 | completion body renderer → Unicode len/current entries → same carrier shared proposal instruction | 核>而非>=，正文不含wrapper/notice/proposal，refs不重复计entry；forced也可合法超限提交，失败无假Snapshot | secretary/noting_notifications.py；E1/C8 r3_framework阈值231–289 | 符合：超限启动共用提案，不截断或自动删除，不重跑Noting | 用户拒绝/延期受Main指令尊重，不以阈值强制外部写入 |
| V49 | turn_context next pre-message surface → restore/build/synchronize → system_prompt tiers + scoped cron copy | 独立核12英文常量全与冻结07逐字相等；核global/cold pinned/native rebuild、local不动root、History恒定、Scheduler独立、aux不继承新增面 | secretary/noting_surface.py；agent/system_prompt.py:585–602；agent/secretary_prompt.py；E6；E1/C4；E2 switches | 符合：root/tools/dispatch在同原生边界一致，Cron文案只私有copy | 旧Prompt冻结不复活；外部Bundle原生构造详V54 |
| V50 | CLI mixin/GatewaySecretaryCommandsMixin/TUI _cmd_secretary → shared slash functions → native transcript human_only过滤 | CLI/TUI真实busy图片+slash/cold恢复、human不进模型History/摘要；读gateway同profile适配及propose normalTurn；本轮4个gateway setup ERROR未执行主体 | hermes_cli/cli_secretary_commands.py；gateway/slash_commands_secretary.py；tui_gateway/methods_secretary.py；E2 F08/F13；E8 gateway | 证据不足：共享机制和CLI/TUI符合，Gateway当前正式入口四主体证据需恢复；V51另有输出时间缺陷 | 不以human反馈被显示就声称从模型所有路径剔除；已有F08真实修复证据可复用 |
| V51 | message wrappers/timestamp + Notebook render/tools/control/proposal + Scheduler DTO + personal Recall candidate_index | 对照02§5.6秒精度/时区；Notebook _now微秒被各出口直出，真实source6 created_at含.902319；Scheduler canonical.run_at原样；个人created_at允许raw epoch/fractions | F-V51；notebook_model.py:49–53；notebook_render.py；noting_tools.py；scheduler_table.py:115–130；personal_provider.py:92–97 | 不符合：已显式格式化的wrapper/History/next_due正确，但多个已知绝对字段绕过统一可读秒精度投影 | 内部精度必须保留；不改正文/ID/未知含义、冻结prefix或旧历史；缺陷不是存储精度问题 |
| V52 | 个人plugin.register → 单 PersonalNowledgeProvider → native MemoryManager system_prompt/prefetch/sync_turn；installer | 核get_tools空、无第二Provider/MCP/loop、公开无依赖；原生memory/profile config关闭不删MD；正式安装host加载唯一插件 | 个人 __init__.py、install_personal.py、personal_provider.py；公共agent/memory_manager.py；E5 | 符合：个人层走原扩展接缝，NM故障未使公共History失效 | 无需真实NM写入来证明插件注册；不把个人配置塞公开core |
| V53 | native provider binding → personal_scope runtime/origin/source/parent/provenance → readonly state snapshot | 逐矩阵Main/Cron/noting/delegate/review/background/unknown；实际main正式host；r3provider31项；role/ref伪装不能启用；不写绑定 | 个人 personal_scope.py；personal_provider.py；E7 provider46；E5 first-turn-identity | 符合：Main三能力、Cron仅物理archive、Noting/aux不独立Bundle/recall/sync | native fallback只在未具备Conversation Ref时，不能降级绕过来源不合格 |
| V54 | native build_system_prompt → provider.get_system_prompt → context_bundle(include_working_memory=false) | 初始化无I/O，原生构造/冷恢复/真压缩更新而非每Turn刷新；正式BundleA→cold仍A→真压缩D，offline明确不可用 | 个人 personal_provider.stable_bundle_text/system_prompt；E5 cold-evidence、compaction-evidence、offline-evidence | 符合：全局规则与Bundle沿原生生命周期，拒WM替代，失败不猜背景 | 服务返回Markdown为受控外部数据，不扫描/改写其自然正文；fixture不冒真实服务 |
| V55 | host meaningful input admission → provider.prefetch → official CLI search → candidate_index JSON pointers | 核默认8/2/5/2400、shortCJK无第二门槛、完整ID/标题/日期、无正文/假confidence、编码预算，scopeepoch丢迟到结果；正式短CJK及503无旧指针 | 个人 personal_provider.py:64–106；personal_client.py；E5/E7 provider46 | 符合本条指针/recall机制；可见日期格式同时受V51不符合阻断 | api_content既有重放不等于每次Recall；queue_prefetch no-op；不承诺prompt缓存命中 |
| V56 | 个人 nm-cli Skill → Main官方CLI → provenance payload/helper | 逐条读Skill对象动作：查询重复/矛盾/过时、原文核范围、具体批准后写；notebook:type标签/gap→situation/direct不伪造；无自动写门禁宣称 | 个人 skills/nm-cli/SKILL.md；personal_cli.py；PHASE3 §4；E1/C10-P | 符合：作为产品指令具体指示目标与步骤；Noting不直接读取目标判结算 | 本轮只审指令/受控执行，不声称真实NM Memory写入验收 |
| V57 | personal_cli create →官方 nmem --json m add → actual top-level ID → GET/PATCH metadata | 核配置同官方effective endpoint/key、stdin无shell、基本provenance结构、只补hermes保无关metadata；未知不猜ID/重建、已知ID失败仅附件repair | 个人 personal_cli.py；personal_client.py；E1/C10-P旧39 canonical；E7两R3另46 | 符合：窄辅助无HTTP建正文/第二配置，部分失败收据诚实 | 按R3-008–010不新增严格真实写入门禁；不会调用真实NM做关闭证据 |
| V58 | turn_finalizer completed/failed → run_agent._sync_external_memory_for_turn → native manager egress → provider canonicalHistory+egress/filter → fixture | 核先全batch egress学习toolsecret再只UA；截止accepted finalUID不吸未完尾；正式12completedTurns/24UA与跨压缩Thread，失败interrupt不sync | 公共turn_finalizer.py:587、772；run_agent.py:913；memory_manager.py:607；个人provider/scope；E5/E7 | 符合：真实host到本机fixture贯通，原文来自合法History，模型注入/tool不外送 | 原文脱敏是host规范，非逐字段猜凭据；fixture是真实HTTP但非真实NM |
| V59 | personal_scope thread_id → provider receipt SQLite(endpoint,space,thread) → import/append ACK → prefix cursor | 核new/fork/reset分Thread、compaction延续、Cron物理；锁下已ACK前缀对比/timeout不推进/divergence halt；正式import1+append11/UID唯一 | 个人 personal_provider.py ledger/sync；personal_scope.py；E5 Thread证据；E7 test_r3_thread | 符合：明确匹配ACK才前进，重启账本持续，分叉拒绝拼接不悄悄重建 | at-least-once，远端接受但ACK丢失可能重试，不宣称exactly-once |
| V60 | 个人Provider无自动distill/govern hooks；本轮执行隔离/fixture/cleanup manifests | 审onwrite/precompress/outcome noop；正式round3→loopbackfixture、结束恢复config/hash/插件和进程；无真实Memory/Thread/Space写或部署 | E5 manifest/process/env restoration；个人PHASE3 §7；E7 | 符合：验收边界与真实观察一致，未增加BI/自动治理策略 | Background Intelligence政策由已冻结配置前提保持，不把本地fixture解释为真实服务策略验证 |

## 4. 核心目标及验证方法审查

**首轮全范围结论：56条符合（含明确交叉缺陷限制），2条不符合（V23、V51），2条证据不足（V01、V50）。Verification 不通过。** 这不是最终交付判定。即使待修内容已在工作树出现，323c/e1af6 的本次结论不变；任何整改均需明确新版本与独立复审。

核查覆盖了实际调用路径、运行时归属、持久事务、失败/关闭/并发及正式输出。重点反例包括：以现行Ref伪装auxiliary、旧来源洗白新正文、finish混合批次先过滤后执行、晚完成覆盖倒退、检查pointer后才异步追加、旧generation worker复活、未实际带入请求就ACK、同UID成功压缩无法释放Force、重启/rewind重开Force、local off消费后Idle周期重造、cold pinned root复活关闭工具、父user尾与Noting task合并、Noting五Turn续行重写prefix、个人账本接受非明确ACK、归档时吸入未完成尾部。对于这些机制，不以helper存在或函数名单代替正式入口追踪。

已直接核对的强证据：

- 现有真实模型的user尾7请求、assistant尾多模态5请求、两个五Turn续行probe18+13请求，独立从原始request.body重算冻结前缀和ordered工具相等；169个原始dump全部hash匹配。没有输出完整root/header。cache usage仅作服务实际返回的另项观察。
- 个人正式TUI/native MemoryManager/Provider到loopback fixture：12个completed Turn、14次模型请求、24条UA，Thread import1/append11；冷恢复不换Bundle，真实压缩后换Bundle；离线失败后History仍可读。清理与配置恢复依真实manifest，不把中断退出码误报正常关闭。
- Framework的当前pointer检查、durable insert、live append同事务边界；竞争writer在锁后观察一致，owner变化回滚，过期queue连proposal丢弃。Scheduler最终materialize与admission re-read不信旧lease或预渲染字符串。
- 冻结英文常量逐字一致是实现机制证据；V23的实际失败说明它不能单独证明语义符合。只在代码正确而实际场景尚未得到必要结果时保持阻断，不将模型错误豁免为“提示词已经写了”。

统一回归记录：唯一owner在固定双SHA运行139个文件调用（136完整＋1 server过滤90参数项＋2个人），11次canonical runner＋1次十类check，各组一次，合计311.402秒。结果1766 PASS、29 FAIL、3平台skip、4 setup ERROR；八类check通过，no-tmp/health阻断。原始失败全部保留。33个节点按E8精确分组：旧工具断言5、ACP依赖1、原生压缩/通知5、Snapshot夹具审计15、History旧契约3、Gateway缺Anchor setup4。**这些是待修复输入，不是审查者已批准的失败豁免。** 三skip只代表本机平台边界；未验证其它OS，不模拟host OS。未运行文档长度门禁，未修改冻结规则。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| F-V23（主会话F16） | V23；白板E1/E2/N1、07§8.11 step4；noting_prompts.py注入/实际maintain轨迹 | 用户具体批准探视经验写USER，实际工具成功且memory-after存在；Noting archive Candidate13，但source6 v34全文保留同已交付经验，仅加processing_note“来源情形本身保留”；新经历是35，无其他候选或未完责任支持6 | 高优先级阻断：成功结算只做了候选退出，已交付覆盖未清退，仍可重复候选/提案；不能以Prompt逐字相同判符合 | 主会话提方案、审查者评审。关闭须正式Main具体批准→真实受限合成写入结果→合法Noting，前后版本与原文证明成功覆盖移除/精简，同时保新变更/未完责任/其他候选依赖；不SQL删、不伪写成功、不硬编码工具结果自动删source | 固定版本不符合；root认可事实并登记F16，整改方向获评审；尚无关闭证据 |
| F-V51（公共及个人） | V51关联V09/V30/V50/V55；02§5.6:1635–1637；notebook_model._now、notebook_render、noting_tools、cli proposal；scheduler_table:115–130；个人personal_provider:92–97 | Notebook created_at/updated_at/处理及证据时间被JSON/人类render原样输出，真实created_at带.902319；Scheduler canonical_schedule.run_at保留native parse的微秒；个人Recall日期显式接受raw epoch/fraction ISO | 阻断：项目绝对时刻输出须有时区可读秒精度，已格式化next_due/History不能覆盖旁路；不是内部存储精度错误 | root方案：保留内部精度/immutable provenance/no-op，明确字段在既有输出边界共用native时间投影。关闭须覆盖Main/tool/slash/Proposal、Noting maintain/show/初始及continuation、Framework、Scheduler nested run_at、个人Recall；同时验证ID/正文/null/unknown语义/input/内部值不变 | 初审固定版本不符合；公共Notebook补丁已由root接收但不在323c；个人/Scheduler仍待方案/修复及新版本独立复审 |
| F-REG | V01/V50；E8 33个失败/错误节点与2检查 | 首轮原生邻域29FAIL/4setupERROR；no-tmp为报告否定表述，health为scheduler_available blind except。原生压缩5项/ACP1项尚不能由猜测归类关闭；Gateway4主体未运行 | 阻断：不能用1766PASS/既有真实模型抵销未证原生行为和当前入口测试底座。旧契约应按现行规格修fixture，不能恢复退休alias或删保障 | root按精确节点提修复并定向复证失败与实际受影响路径；保留首失败日志、固定新版本、环境依赖依据；不重跑大型集合、不放宽规则、不加skip回避 | 首轮保留；root正在分派。scheduler异常日志微改已在工作区，尚非本次固定版本关闭 |

范围外：UI/Settings可视展示、Web读DTO、独立UI仓构建、云部署、真实NM Memory/Thread/Space写入、通用官方CLI编辑/管理写入、跨平台实机运行。它们不是本轮缺陷，也未被写成通过。本轮个人验收明确是正式host→本机fixture；窄provenance脚本按授权基本检查，未擅加真实写入门禁。未新增产品规格或真实NM操作。

## 6. 修复与独立复审

本报告为初审完整交回，尚无缺陷在待审固定版本关闭。第2节独立判据未改动；初版及hash保存于E6，后继记录不得覆盖原始阅读顺序。流程规则/动态CLAUDE不作为产品判据；旧规格按冻结07/白板明确保留范围继承，不以旧“当前”字样复活被替代内容。

| 事项 | 主会话提案 | 独立评审意见 | 后续证据与复审状态 |
|---|---|---|---|
| Notebook V51 | 保留_now/Store/版本内部精度，notebook_render统一已知绝对时间；所有既有输出边界投影，不改旧历史/父prefix | 方向认可，明确补充/propose-persistence原始payload出口；须含字段内部时间与source_time_range，unknown/null/正文不误改 | root报告17定向PASS与3生产文件，已纳入ac7032be96114016bc26d1fa8825c4ba04b925f4；尚未按新固定SHA独立复审，不能写已关闭 |
| 个人Recall V51 | candidate_index对epoch/带offset ISO用native秒精度；纯日期保来源语义，未知timezone不伪instant，保ID/编码/预算 | 认可边界。无zone datetime或不可解析值的输出行为须明确，不能原样当已规范化绝对时刻；不扫描Bundle自然Markdown | 待实现/定向证据与新SHA |
| Scheduler V51 | root提案在public_conn验证后的局部canonical副本仅投影run_at，复用native renderer；DB/expression/推进不变 | 认可：同出口覆盖create/list/update，关闭须显式微秒ISO和相对一次性表达式、实际Store/tool输出与内部原值证据 | 待定向证据与新SHA独立复审 |
| V23/F16 | 先查实际Prompt对象分支/相反保留指令，再沿正式Main→Noting重做成功覆盖结算 | 认可，必要指令修订需忠于原语义并留痕；不可仅因新增一次成功就抹除首失败 | 已确认冻结Prompt逐字一致，尚待actual注入/场景排查与关闭证据 |
| 统一回归失败 | 精确节点分类修fixture/真实生产缺陷与正式PM环境；定向重测 | 方向认可，但初归旧契约不等于已关闭；不复活退休工具，不免除原native保障 | 待owner交回、root review及独立证据复审 |

下一门禁须等本范围全部不符合与证据不足关闭，再由主会话正式派遣Validation。本审查者不判整轮最终交付，也不授权进入真实NM/部署范围。

### 6.1 F16 Step4 具体提案审议（2026-10-17，原审查者追加；非缺陷关闭）

按主会话限定，仅复核 `.hermes-dev/round3-local-20261017-l0/v23/proposed-step4.txt` 全文及 investigation-report.md / investigation.json，不重做60条、不修改第2节判据、不修改产品或规格。提案文件 SHA256：`e0d68140116a3857b221ca727f38e68ae64f922293038097f04c29c21f0ac4de`；获评审全文副本及逐请求复核结果在E6 `f16-proposal-reviewed.txt`、`f16-proposal-review-evidence.json`。本次再次从原始request.body独立核对9个请求：各hash相符，完整DEFAULT均已注入，28条父prefix及有序工具均相等。批准、真实成功结果与独立新增素材已可达，不能将首失败归因于缺少事实或遗漏task。

**提案评审结论：认可该全文作为既有结算语义的动作细化，未发现实质新增产品语义、权限或完成条件。** 这只是方案符合性审议，V23/F16仍为OPEN、首样本FAIL保持。具体依据如下：

| 提案内容 | 既有原文依据 | 审议结论与不可改变的边界 |
|---|---|---|
| 用Conversation批准、实际操作与结果定位内容/source版本/目标；需要时合法History回读 | 白板E1步骤1–3、F1；冻结07§8.11原Step4 | 忠实展开事实对齐；不新增目标接收证明，不因仅有批准或声明保存就认为成功 |
| 对比每个受影响Candidate和source的现行版本；完整结算archive Candidate、部分结算update剩余范围 | 白板E1步骤4、F2；原Step4保护later changes与partial success | 合法调用已有notebook_maintain，不引入新状态机或按memory工具成功自动删源；仍按内容与目标的实际成功范围结算 |
| source全部成功覆盖且无新内容、未完责任或其他未完成提案用途时archive；部分可退出时update移除该覆盖、保剩余内容/必要上下文/provenance | 白板E1步骤4及输出；原Step4 protecting later changes, unfinished responsibilities, sources still needed by other proposals | 明确原要求的具体动作，不能把“来源本身”或“加已保存注记”当永久保留理由。保护条款继续有效，不得为了退出而删未交付事实或必要上下文 |
| 每个保留部分说明具体责任、新内容或未完成提案；仅归档Candidate/给source加注记而原交付正文不变不算来源结算 | 白板E1步骤4–5、E2退出边界；原V23必要不变量 | 针对已观察反例消除抽象执行空间，不添加独立产品目标，也不要求无依据地强制归档 |
| archive前修存活Candidate引用及entry relations | 白板E1步骤5；07§8.11 TOOL USE及现行archive入向引用约束 | 符合既有接口；不能通过删除实际仍需的引用来人为满足归档条件 |
| 失败/未知保留，未知写入不得重复；不检查目标文件/存储标签/provenance质量 | 白板F1/F2、E1步骤3、E2；原Step4 | 权限与证据边界保持；Noting仍不得执行外部写入，新增这句话不构成重试授权 |
| finish_noting说明已结算对象、保留范围/理由及Conversation证据，不重现内部已完成正文库 | 白板E1步骤5及输出；07§8.11 Step6 brief result/limitation summary | 是既有结束说明内容具体化，不增finish接口参数、代码提交gate或额外批准条件；brief要求仍有效 |

“successfully dispatched coverage”必须按提案首句已经列明的**获批内容＋目标＋实际结果**理解。例如同一Candidate含两个目标、仅一个目标成功时，剩余目标仍未完成，其确有需要的来源受保护；不能只比较正文字符串相同就判全部结算。纯source归档也不能消除既有保护理由。该解释来自冻结F1/F2/E1及原V23，不是本次新增判据；提案整体已有destination、actual outcome、partly settled Candidate与unfinished proposal分支，无须为认可方案改变判据。

主会话已说明推进依据是用户提供的项目级“必要自主口径收敛”和“AI指令必须写具体动作”规则：在CLAUDE顶部登记“Agent自主工程细化／待追认”，索引单列工程依据，不混入用户确认表；保留d19018历史基线并追加修订SHA。对此，本审议仅确认**语义仍在既有白板E1范围内**，不把工程决定写作用户已确认，也不以流程规则替代产品判据。

后续仍需：同步07 Step4与DEFAULT唯一段落、记录新固定SHA；从正式Main具体批准到真实受限合成写入再到合法Noting保留第一次结果，证实已交付source覆盖确实移除/精简，且新增/未交付/未完责任/其他提案需要的范围得到保护。若自然模型拆条导致同entry部分结算未覆盖，应诚实标缺口，不能挑样本或称全覆盖。首失败不可覆盖；不得SQL删源、伪造写成功或新增机械清退gate。**关闭由主会话后续派出的全新全范围复审者判断，本次认可不能替代。**

### 6.2 V51 / F15 Scheduler 生成式 display 补充评审（2026-10-17；非关闭）

主会话补报并提出仅在 `schedule_public_conn` 局部canonical副本复用 `hermes_time.readable_schedule_display(schedule, display)`。本审查者只读核对了正式路径：`cron/jobs.py:819–832` 对显式ISO生成 `run_at=dt.isoformat()` 和 `display="once at YYYY-MM-DD HH:MM"`；`scheduler_table.schedule_public_conn` 将该canonical放入正式工具DTO；现有helper `hermes_time.py:189–200` 对一次性 `once at ` 标签从run_at生成秒精度、显式时区的可读时刻，其他标签原样返回。

**认可：这是V51必须修复的同类出口，不是新增产品范围。** 该display由产品解析器生成，实际表达绝对时刻，却缺秒和时区；旁边另有正确的run_at/next_due_at不能豁免它。它不同于应保留的用户原始expression，也不同于 `once in 30m` 这种相对时长标签。冻结02§5.6:1635–1637已明确所有实际对人/模型暴露的绝对时间格式要求，第2节V51无需修改。

提案复用既有native helper、只改已验证的局部输出副本，符合不变内部精度与原生时间解析/推进的边界。应保持DB canonical.display、DB run_at、原expression、claim/next_due计算及相对/周期显示原值。定向关闭证据应由正式scheduler create/list/update出口观察显式ISO（包含非零秒、offset、微秒）的生成display与run_at/next_due_at表达同一秒级时刻，检查内部值及原expression未变；相对一次性 `once in` 和周期标签不被改写。无需因此复跑60条或启动模型，本次未运行任何测试/模型。新RED与修复后定向证据应并入原F15版本链，原初审失败仍保留；最终关闭留给全新全范围复审者。
