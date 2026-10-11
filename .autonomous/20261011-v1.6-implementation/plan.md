# 本轮实施计划：20261011-v1.6-implementation

## 目标与依据

依据 snapshot-index.md 和 baseline.txt 冻结原文。完成根看板 V1.6 清单 A–D，继承未修订 V1/V1.5 契约，正式路径可用并关闭两个独立门禁。优先 Notebook 版本化→Noting Child→Snapshot→Main 读取／Reminder。只在 main 本地提交；隔离 runtime／测试库均位于 ignored .hermes-dev，可重建、不迁移；不 push、不部署。动态编排仅根 CLAUDE.md。

## 覆盖与任务

| 要求/口径编号 | 任务和正式路径 | 实现负责人及白名单 | 依赖和接口 | 验证方法 | 用户场景 | 完成条件 |
|---|---|---|---|---|---|---|
| A1–4；02 §2.5、3.3a、3.7–10、5.12-3/6；C02；M09/10/16/17 | T1 INSERT-only item、ordered Snapshot ids、lineage、新 id、三工具、archive、time-range provenance、secretary_task/delivery_mode | storage：secretary/notebook_{model,store,schedule,render}.py、secretary/noting_tools.py、secretary/schedules.py、hermes_state_secretary_notebook.py、必要 sibling、相关 storage/tools tests | notebook_current 保持四区公共 payload；noting_tool_control_message(profile, notebook_state=...)；registry version 更新与 T3 协商 | 隔离 DB 生命周期、旧 id 拒绝、原子失败、branch/rewind、schedule/off，runner 定向测试 | S1 create/edit/status/archive；S2 provenance；S3 schedule | 无 restore/fused alias；新 id/lineage 正确、审计隔离 |
| C9；02 §4.5/8、6.6/15；M13 | T2 Turn end arm、start cancel、一次事件、attach catch-up、cap 排最后 | timers：secretary/noting_hosts.py、secretary/noting_runtime.py、hermes_state_secretary_noting.py、host Turn/reaper seams、timer sibling、相关 tests | 不碰 Child 和 Reminder 请求文件；Force 使用 T3 Framework 内部接口；显式 owning profile | 实时短 timer、重排、重复 tick、catch-up、reaper 压力、off/native | S4 idle/restart/reap；S5 Force/race | tick 不重复 freeze/attempt；cap 非绝对豁免 |
| C10/11；C07；02 §2.6、3.11/12、5.6、6.8/9/17；M18 | T3 durable deferred batch、装配前两阶段 ACK、重投、compaction 拒投、instant、Framework 双写/fence、anchor 标记；C07 External拒绝通知（Force/Idle/catch-up） | delivery：secretary/reminder_request.py、secretary/reminders.py、secretary/cli_reminders.py、hermes_state_secretary_schedule.py、agent/message_metadata.py、agent/conversation_loop.py、agent/turn_api_call.py、agent/turn_context.py、request builder seams、gateway/secretary_reminders.py、tui_gateway/secretary_reminders.py、Framework sibling、相关 tests | publish_framework_message(parent, body, *, display_metadata=None)；busy/fence 排队、Turn end flush；T2 Force/T4 finish 调用；T1 协商 version registry | live/durable 同行、batch、ACK 失败与丢行重投、compaction、busy ingress、重启、关闭回归 | S6 deferred/instant idle/busy；S7 Force/finish | 无每请求读库 reconciliation；仅实际携带且成功响应 ACK |
| B5–7、C8/12/13；02 §2.3/5、3.5、5.5–12、6.14/16/17；M08/14/15/19/20/27/28 | T4 Prompt Target 逐字、memo lifecycle、Child notebook/memo 后缀、overflow、History 截断 | 第二波：agent/system_prompt.py、agent/prompt_builder.py、tools/cronjob_tools.py、secretary/noting_surface.py、secretary/noting_child.py、tools/session_history_tool.py、history/memo sibling 与注册接线、相关 tests；共享文件交回后串行 | T1 声明、T3 Framework/wrapper；memo 与 Snapshot 同事务清空归档；overflow 原 Commit Gate | Target、warm/cold/off/aux、真实多请求 prefix/cache、memo no-trigger/失败保留、overflow、search/read | S8 memo→Noting；S9 compaction/overflow；S10 history；S11 global 切换 | 父 root/tools/messages 冻结；真实 DeepSeek 新工具可调用与缓存观察 |
| 全范围；02 §6；04 §7；D14/15；M01–28 | T5 主会话集成 review、必要扩大测试一次、Verification→Dashboard Validation→交付 | root；全新独立 gate agents 只读产品代码，分别写 verification.md/validation.md 和 ignored evidence | 收敛 commit 后 fork_turns=none；独立重提取原要求 | 实际影响范围统一扩大检查；官方 localhost Dashboard 真实 DeepSeek 输入→响应/Compaction/Proposal/Reminder/Full audit | S1–11 完整旅程、04 §7.3 六场景 | 全部符合或有依据不适用，Validation 无未执行，整改清空 |

## 当前状态与编排

动态机制／正式接线／针对性验证／用户结果状态仅根 CLAUDE.md。T1/T2/T3 白名单不交叉，共享工作区、无 worktree；子 Agent 不再派生、不提交。交回后 root 亲自阅读关键变更和上下游，核对要求覆盖、机制、接口、失败、证据缺口，之后 T4 串行接共享点。同版本有效证据不重跑；集成变化定向复测；门禁只在全局收敛后派遣。

基线：启动 fa51561601；冻结见 baseline.txt；PM .venv Python 3.14.7；uv.lock SHA256 2bc4db483e9cba927cd7147f9ccbb09635f85bb3f1f36d6e9d51d06b65d1c67e；V1.5 Verification 未通过、Dashboard 未执行，不能沿用通过结论；macOS，Linux/Windows 未覆盖。未为建基线预跑大型检查。日志 .hermes-dev/v1.6-evidence/。

## 缺陷与整改

| 问题编号 | 要求与触发条件 | 当前事实与影响 | 优先级及理由 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|
| R0 | V1.5 遗留门禁缺口 | 旧 Verification 未通过，Dashboard 未执行 | 必须，不能施工代替验收 | root/T5 | 当前版两门禁关闭 | 待收尾 |
| R1 | 02 §5.6 Framework 已排队后 Turn 结束前关闭 Noting | flush 依赖 Idle recorded 和再次 effective gate，可能丢已准入生产的通知 | 集成正确性 | timers/delivery | timers/framework-off-race.log 3/3；已有队列尾部双写同 UID，空队列无新调用；root复核接收 | 已关闭 |
| R2 | 02 §2.6 Anchor仅排 Finish marker及Compaction | 旧role=system排除阻止真实普通System事件推进Anchor | 接线正确性 | root/storage | root已复核foreground Anchor／freeze／Commit Gate／Full audit与branch路径；child-memo/integrated-final.log 50/50含普通System、Finish及真实预算装配；delivery/branch-boundary.log 10/10含原生create_session与TUI持久化helper | 集成关闭；正式门禁待审 |

| R3 | C07拒绝判断后或通知排队期间发生actual Native | 过时“latest External”通知应丢弃；仅撤当前ref未落盘External producer，其他通知和durable行保持 | 用户委托范围内必要工程收敛，主会话提议／Verification评审 | delivery/root | external-notice/refs-final.log 27/27及queue-race/compat证据；正式Verifier按原V132–V136判据评审方案及关闭状态 | 已实施并经root接线review；待独立评审 |

| VF01 / R4 | V036：历史已提交UID被rewind移除后新create或显式source edit复用 | 正式Verifier对fba6ec5真实SessionDB反例确认：全历史Snapshot来源UID并集给新输入通用许可，新候选可错误提交 | 范围内阻断，来源不能复活失效历史 | storage/root | 新create/source edit与commit并发移除来源均拒绝且状态/pointer不变；具体既有item原引用维护、并发旧base、branch与compaction source正例；root方案由Verifier评审，修复后全新全轮独立复审 | 已实施／root接线review接收；provenance-fix基础138、接线77（含专项28）通过，待新独立全轮复审关闭 |

| VF02 / R5 | V099/V077：Noting异步原生父压缩结果未发布live | 固定fba真实6→4 native提交后durable5/live7，worker局部tuple无人消费；Framework等fence清除后仍向旧list追加。root先暂列harness边界，已被正式反证推翻 | 范围内阻断，父下一请求可能复用retired源／错误tail | timers/root | 本次native有效commit结果在fence释放前所属live adoption，保共享引用、不覆盖新Turn/reset/branch/另一压缩；fail/blocked不fake；三个真实profile结束后live=DB且下一Mainwire压缩前缀，一FinishUID两视图，独立全轮复审 | 已确认／接口方案设计中，未关闭 |

## 取舍、快照与续接

无新增产品取舍。C02 用户确认，非自主假设。02 残留 memo add guarantees run 和 schedule_create 以更具体已定案 §3.5/3.7、§5.12 Target 为准：memo 不触发，初始 Schedule 在 create。04 旧 agent_task/restore/三型 termination/旧 Prompt 按现行 02 明确修订替代，不追改上轮结论。阶段提交准确记录验证边界，最终由 delivery-evidence-review 判定。
