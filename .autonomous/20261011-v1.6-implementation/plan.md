# 本轮实施计划：20261011-v1.6-implementation

## 目标与依据

依据 snapshot-index.md 和 baseline.txt 冻结原文。完成根看板 V1.6 清单 A–D，继承未修订 V1/V1.5 契约，正式路径可用并关闭两个独立门禁。优先 Notebook 版本化→Noting Child→Snapshot→Main 读取／Reminder。只在 main 本地提交；隔离 runtime／测试库均位于 ignored .hermes-dev，可重建、不迁移；用户已授权最终汇报前 push；不部署。动态编排仅根 CLAUDE.md。

## 覆盖与任务

| 要求/口径编号 | 任务和正式路径 | 实现负责人及白名单 | 依赖和接口 | 验证方法 | 用户场景 | 完成条件 |
|---|---|---|---|---|---|---|
| C15 | 全部实际AI/human绝对时间外显可读 | Notebook原created_at/last_update_time直接暴露Unix数，用户扩大为全部时间暴露面 | 用户明确新增呈现口径 | readable_times / root集成 / 独立两门禁 | 全面外显入口清单、带时区且原瞬间不变、内部DB/调度/duration/prefix不变，定向证据及真实human/AI复验 | 已授权冻结，待专门Agent排查修补 |
| VAL04 | 02 §4.5 真正Main end后Idle、new Main取消旧period；§3.5 memo auto-on非Trigger | local off时Main start未更新旧Idle，memo add auto-on后旧due catch-up在同一Main忙碌期间准入，真实反例已落盘 | 范围内真实机制阻断，禁止以第二30秒成功抵消 | idle_busy_fix / root集成 / 新独立审查 / Validation复验 | 既有生命周期/timer最小修复；off→auto-on busy不准入、Main结束自然timer一次、关闭/owner/aux/race回归；新版本独立复审及原用户序列真实复验 | 已分派修复，产品82旧PASS不作为当前交付通过；CU05–08未闭环 |
| A1–4；02 §2.5、3.3a、3.7–10、5.12-3/6；C02；M09/10/16/17 | T1 INSERT-only item、ordered Snapshot ids、lineage、新 id、三工具、archive、time-range provenance、secretary_task/delivery_mode | storage：secretary/notebook_{model,store,schedule,render}.py、secretary/noting_tools.py、secretary/schedules.py、hermes_state_secretary_notebook.py、必要 sibling、相关 storage/tools tests | notebook_current 保持四区公共 payload；noting_tool_control_message(profile, notebook_state=...)；registry version 更新与 T3 协商 | 隔离 DB 生命周期、旧 id 拒绝、原子失败、branch/rewind、schedule/off，runner 定向测试 | S1 create/edit/status/archive；S2 provenance；S3 schedule | 无 restore/fused alias；新 id/lineage 正确、审计隔离 |
| C9；02 §4.5/8、6.6/15；M13 | T2 Turn end arm、start cancel、一次事件、attach catch-up、cap 排最后 | timers：secretary/noting_hosts.py、secretary/noting_runtime.py、hermes_state_secretary_noting.py、host Turn/reaper seams、timer sibling、相关 tests | 不碰 Child 和 Reminder 请求文件；Force 使用 T3 Framework 内部接口；显式 owning profile | 实时短 timer、重排、重复 tick、catch-up、reaper 压力、off/native | S4 idle/restart/reap；S5 Force/race | tick 不重复 freeze/attempt；cap 非绝对豁免 |
| C10/11；C07；02 §2.6、3.11/12、5.6、6.8/9/17；M18 | T3 durable deferred batch、装配前两阶段 ACK、重投、compaction 拒投、instant、Framework 双写/fence、anchor 标记；C07 External拒绝通知（Force/Idle/catch-up） | delivery：secretary/reminder_request.py、secretary/reminders.py、secretary/cli_reminders.py、hermes_state_secretary_schedule.py、agent/message_metadata.py、agent/conversation_loop.py、agent/turn_api_call.py、agent/turn_context.py、request builder seams、gateway/secretary_reminders.py、tui_gateway/secretary_reminders.py、Framework sibling、相关 tests | publish_framework_message(parent, body, *, display_metadata=None)；busy/fence 排队、Turn end flush；T2 Force/T4 finish 调用；T1 协商 version registry | live/durable 同行、batch、ACK 失败与丢行重投、compaction、busy ingress、重启、关闭回归 | S6 deferred/instant idle/busy；S7 Force/finish | 无每请求读库 reconciliation；仅实际携带且成功响应 ACK |
| B5–7、C8/12/13；02 §2.3/5、3.5、5.5–12、6.14/16/17；M08/14/15/19/20/27/28 | T4 Prompt Target 逐字、memo lifecycle、Child notebook/memo 后缀、overflow、History 截断 | 第二波：agent/system_prompt.py、agent/prompt_builder.py、tools/cronjob_tools.py、secretary/noting_surface.py、secretary/noting_child.py、tools/session_history_tool.py、history/memo sibling 与注册接线、相关 tests；共享文件交回后串行 | T1 声明、T3 Framework/wrapper；memo 与 Snapshot 同事务清空归档；overflow 原 Commit Gate | Target、warm/cold/off/aux、真实多请求 prefix/cache、memo no-trigger/失败保留、overflow、search/read | S8 memo→Noting；S9 compaction/overflow；S10 history；S11 global 切换 | 父 root/tools/messages 冻结；真实 DeepSeek 新工具可调用与缓存观察 |
| 全范围；02 §6；04 §7；D14/15；M01–28 | T5 主会话集成 review、必要扩大测试一次、Verification→Dashboard Validation→交付 | root；全新独立 gate agents 只读产品代码，分别写 verification.md/validation.md 和 ignored evidence | 收敛 commit 后 fork_turns=none；独立重提取原要求 | 实际影响范围统一扩大检查；官方 localhost Dashboard 真实 DeepSeek 输入→响应/Compaction/Proposal/Reminder/Full audit | S1–11 完整旅程、04 §7.3 六场景 | 全部符合或有依据不适用，Validation 无未执行，整改清空 |

## 当前状态与编排

动态机制／正式接线／针对性验证／用户结果状态仅根 CLAUDE.md。T1/T2/T3 白名单不交叉，共享工作区、无 worktree；子 Agent 不再派生、不提交。交回后 root 亲自阅读关键变更和上下游，核对要求覆盖、机制、接口、失败、证据缺口，之后 T4 串行接共享点。同版本有效证据不重跑；集成变化定向复测；门禁只在全局收敛后派遣。

基线：启动 fa51561601；冻结见 baseline.txt；PM .venv Python 3.14.7；uv.lock SHA256 2bc4db483e9cba927cd7147f9ccbb09635f85bb3f1f36d6e9d51d06b65d1c67e；V1.5 Verification 未通过、Dashboard 未执行，不能沿用通过结论；macOS，Linux/Windows 未覆盖。未为建基线预跑大型检查。日志 .hermes-dev/v1.6-evidence/。

## 缺陷与整改

C14验收操作授权：仅合法隔离配置可临时调节，一般Idle30秒、memo操作可暂加长，验完恢复原值；真实Turn结束/timer/时钟驱动，不直接trigger/tick、不改DB due、不伪busy/时钟。产品默认值与既有规格不变。

| 问题编号 | 要求与触发条件 | 当前事实与影响 | 优先级及理由 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|
| VAL03 | 官方Dashboard CHAT恢复旧Session | 原生自动TUI build的scratch位于源码树，被productOutput拒绝，PTY未创建、0模型输入 | 阻挡全部用户验收，先恢复合法入口 | root（环境协调）/独立Verifier评审/Validator复验 | 既有native prebuilt入口与official bundle/source hash一致；保库重启后同CHAT/Session真实可用、原失败保留 | 独立提案接受，root保库重启PID68046（dff文档HEAD/82同产品）；原入口同Session/真实Main/正式Node→Python复验成功，VAL03关闭；产品源码未变 |
| C13 | Force通知不得跨下一compaction区间 | 原生compress真实60→10保留旧Force UID/body，无生命周期过期 | 用户明确新增成功压缩上下文边界 | root/timers | 正式原生成功发布后不携带，summary/tail/replay涵盖；取消失败不误清，历史保留，其他producer不变 | 31b1f757澄清冻结；六文件已root集中review并关闭pause四事项：窄复测5/5、新增对照2/2、生产者闭集静态核查、18/18当前源码；七项条件证据见root-review-c13-final.json；已提交82cd557aaf；当前整版Verification已独立按K55及关联条款关闭，Validation引用正式机制证据 |
| C12 | 用户明确History模型返回不要重复字段 | 旧result各row同时message_uid及嵌套Identity重复UID/ref、物理message_id | 本轮新增用户确认输出去冗余 | History子Agent/root | result单Ref＋row单UID/ts/role/content；原read兼容／隔离／压缩查源／截断精读/Noting共用不变，实际模型补验 | 9fa277授权冻结；39/39＋四项检查，root接收正式接线并提交bc9cd6d7a1，待整版门禁／模型补验 |
| C10／C11 | 用户明确Notebook Show正文＋last_update_time＋anchor_message_uid | 旧AI结果暴露Snapshot/ref/Anchor/Trigger/Profile审计，占模型token | 本轮新增用户确认口径 | root | 正向四区＋last_update_time＋裸anchor_message_uid投影、内部持久审计不变、null／gate／归档／deepcopy证据与实际模型补验 | 8df8885授权冻结；两个产品文件修补及13/13定向证据完成，待当前整版独立复审／真实模型补验 |
| VAL02 | 02 §3.6／04 §7.3：human Notebook完整可读 | 实际PTY515chars长Notebook折叠、AX和坐标点击均无展开 | 范围内真实用户结果缺口 | timers/root | 既有Slash展示薄修补，不扩新UI；实际长正文无需不可用鼠标可完整阅读 | 修补与30项UI证据已root接收并提交bc9cd6d7a1、官方构建完成，已由CU02原515字符及localoff人类完整阅读实际复验关闭，原失败保留 |
| VAL01 | 02 §5.6 L1656–1658／1694：Framework tail写入同步用户timeline可见 | 实际Dashboard Main→Idle Noting成功，Snapshot/memo/Finish durable正确，但23:20:55→23:21:30终端无Finish通知；首证据validation-final/U01/ | 范围内用户结果缺口待调查 | timers/root | 原TUI/PTY及CLI正式通知接线分析；复验真实Idle／busy tail事件用户可见且同UID单行，不新增Turn或carrier | 正式接线及专项证据已root接收并提交bc9cd6d7a1，CU04真实Finish用户可见及后续使用复验关闭，原失败保留；VAL04 timer修复后核影响 |
| R0 | V1.5 遗留门禁缺口 | 旧 Verification 未通过，Dashboard 未执行 | 必须，不能施工代替验收 | root/T5 | 当前版两门禁关闭 | 82cd557aaf当前整版Verification通过并root接收；真实Dashboard Validation正式执行，最终交付待关闭 |
| R1 | 02 §5.6 Framework 已排队后 Turn 结束前关闭 Noting | flush 依赖 Idle recorded 和再次 effective gate，可能丢已准入生产的通知 | 集成正确性 | timers/delivery | timers/framework-off-race.log 3/3；已有队列尾部双写同 UID，空队列无新调用；root复核接收 | 已关闭 |
| R2 | 02 §2.6 Anchor仅排 Finish marker及Compaction | 旧role=system排除阻止真实普通System事件推进Anchor | 接线正确性 | root/storage | root已复核foreground Anchor／freeze／Commit Gate／Full audit与branch路径；child-memo/integrated-final.log 50/50含普通System、Finish及真实预算装配；delivery/branch-boundary.log 10/10含原生create_session与TUI持久化helper | ce2fa6f全129独立复审已关闭 |
| R3 | C07拒绝判断后或通知排队期间发生actual Native | 过时“latest External”通知应丢弃；仅撤当前ref未落盘External producer，其他通知和durable行保持 | 用户委托范围内必要工程收敛，主会话提议／Verification评审 | delivery/root | external-notice/refs-final.log 27/27及queue-race/compat证据；正式Verifier按原V132–V136判据评审方案及关闭状态 | ce2fa6f全129独立复审已关闭 |
| VF01 / R4 | V036：历史已提交UID被rewind移除后新create或显式source edit复用 | 正式Verifier对fba6ec5真实SessionDB反例确认：全历史Snapshot来源UID并集给新输入通用许可，新候选可错误提交 | 范围内阻断，来源不能复活失效历史 | storage/root | 新create/source edit与commit并发移除来源均拒绝且状态/pointer不变；具体既有item原引用维护、并发旧base、branch与compaction source正例；root方案由Verifier评审，修复后全新全轮独立复审 | 已在87228全范围独立复审关闭；保留原fba失败结论及对应版本证据 |
| VF02 / R5 | V099/V077及C08：异步父压缩缺少原生runtime结果接收 | 固定fba真实6→4 native提交后durable5/live7，worker局部tuple无人消费；Framework等fence清除后仍向旧list追加。root先暂列harness边界，已被正式反证推翻；用户明确Noting只触发，撤下Noting层查表拼tail方案（未实施） | 范围内阻断，父下一请求可能复用retired源／错误tail | root／原生接线实现者 | 父原生机制协调active Turn并发布有效结果，保留当前Turn及新消息、同Conversation continuation；Noting不重建父上下文；fail/blocked不fake；真实profile结束后live=DB且下一Mainwire压缩前缀，一FinishUID两视图，独立全轮复审 | 已在87228全范围独立复审关闭；55e92三真实组压缩publication及后续wire成立，新VFR03单独阻断 |
| VF03 / R6 | V080/V120/V099：cached root误作原始custom supplement | 固定fba Noting将完整cached root传入native builder；实际无API反例root13054→20663字符，旧root整块被追加为custom context | 范围内阻断，压缩接线错误参数破坏有效root | timers/root | active使用当前Turn原始system_message，idle仅可信原始supplement/None；真实builder不重嵌完整root，下一Main实际请求正确；冷恢复未知参数诚实处理；新独立全轮关闭 | 已在87228全范围独立复审关闭；真实root归属与完整prefix成立 |
| R7 | 02 §4.10：正式Idle回调须用当前真实usage选择profile | ab209实际freeze usage8137/threshold1000却选NOTING；runtime仍import已删除_reread_usage，异常捕获后measurementNone | 范围内阻断，特殊profile正式timer入口退化；root此前接线review漏审已更正 | timers/root | 正式timer→当前native usage→admission→special/低usage ordinary正反证据、Force-after-idle影响检查；修复后真实三分支补证及独立审查 | 55e92修复及13/13已接收，87228全范围独立复审关闭；旧失败7HTTP保留 |
| VFR02 | AF061/062/066：一idle周期仅一个timer事件，读数故障不得被hostattach重造 | 55e92读错在claim前，真实timer＋4attach重复读5次；原None断言仅不派ordinary不能证一次事件 | 范围内阻断 | timers/root | 原claim/External后惰性读数，错误period消费且多attach读1/FG0，新周期恢复，off/notidle/owner/External不误读 | 87228已由独立Verifier关闭；21timer＋5直接接口及源码/manifest一致 |
| VFR03 | AF105/107关联AF013/109：真实用户timestamp及Framework双视图逻辑身份 | 55e92真实forced/overflow nextMain repair合入Finish旧UID，live6/DB7、用户继承noting_run_output并丢timestamp；不是wire-only适配 | 范围内阻断，常见下一输入边界 | root/timers | allFramework producer与newuser独立live/DB UID-content-meta、actualwire stamp、nextIdle真实Anchor；纯native/关闭行为零改 | 414d37已由独立Verifier核四file hash和六raw正式观察关闭；新连续真实input问题另列VFR04 |
| VFR04 | AF105：每genuine user input原arrival marker须独立保留，localoff base contract active | 414d37两个正式Main连续真实input实际wire旧marker1/new0；live merge丢api_content并保旧fresh witness；原native合并断言不能证明timestamp | 范围内阻断 | timers/root | 复用本Turn既有Main eligibility＋Fresh witness保护live边界；globalon/localoff/off、warm/cold/贴标签/双UID/双marker/下一Idle真实freeze、实际aux资格false仍原merge；API副本归一不改，原字典/伪marker反例 | ce2fa6f已提交并由独立Verifier关闭；正式Main/aux观察与版本hash已核，原失败保留 |

## 取舍、快照与续接

无新增产品取舍。C02 用户确认，非自主假设。02 残留 memo add guarantees run 和 schedule_create 以更具体已定案 §3.5/3.7、§5.12 Target 为准：memo 不触发，初始 Schedule 在 create。04 旧 agent_task/restore/三型 termination/旧 Prompt 按现行 02 明确修订替代，不追改上轮结论。阶段提交准确记录验证边界，最终由 delivery-evidence-review 判定。


本次接续整改状态（2026-10-12）：C10–C13及VAL01/VAL02已集成82cd557，独立Verification曾PASS，Validation复验VAL01/02/03已关闭但新增VAL04忙碌Idle时序阻断，待修复版新独立复审/原序列复验。同隔离profile已升级，现安全空闲可保库重启；有效受控机制、真实API与已完成用户链路按源码影响复用，CU05–08及剩余切换/cold/CE01仍待完成；动态编排仅见根CLAUDE.md。

接手授权更新（2026-10-12，新会话用户确认）：①恢复自主目标授权，按continuation-guide A→F收尾；②Dashboard补充验证前先保库重启并复用Codex最近实测profile（dashboard-final-4743943e，不重建库），重启在C13提交且Verification通过后执行；③中间自主执行仓库快照提交方便回退（本轮既有授权确认）；④最终汇报前push云端（用户明确授权push；push前核对无凭据/个人化/私人Pi数据，不改变验收门禁）。
