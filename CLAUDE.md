# Hermes Secretary 主看板

## 自主口径收敛 · 待用户追认

> 本区域按 AGENTS.md 永久维护。无待追认收敛时注明"暂无"。

| ID | 规格空白、收敛及理由 | 状态 | 用户确认 |
|---|---|---|---|
| — | **暂无待追认收敛。** 历史三项已闭环：P01（task instruction 四句系现行 04 §4.4 漏实现的补齐，非新口径）；P02（memo 非空 ⇒ Noting 保持开启，off 仅空 memo 时生效）已确认；P03（memo 触发来源记录名）前提被用户否定，已撤销——memo 不是触发源 | 已闭环 | 2026-10-11 |

## 当前状态

- **V1.5 轮次已收口（2026-10-11）**：本轮全部纠偏口径已并入 02 权威规格——新增 **§5.12 全量 prompt 冻结清单**（按代码归属逐条收录，Frozen/Target 双态，施工逐字对照）、**§3.3a 条目生命周期表**、archive 卸下语义、三工具拆分、secretary_task 改名＋delivery_mode、context_overflow、定时器机制、投递 ACK/M4 规则、anchor 判定（noting_run_output 标记）、History Search 截断规则。**V1.6 开工基线 = 本文件当前 HEAD（`ec4fc58057` 及最终审查提交）**，完整 docs 提交链见 git log（`14102ac85c` → 终）。
- **V1.6 自主实现已启动**（用户 2026-10-11 最新指令：“开始，1.6轮自主实现”，替代此前待启动及不走自主流程的安排）。轮次 `.autonomous/20261011-v1.6-implementation/`；当前准备冻结现行规格，随后分组实现、主会话集成、独立 Verification 与官方 Dashboard Validation。启动提交 `fa51561601`，工作区干净；尚未实施或验收。
- **本轮确认 C02**：item 表限制针对 Agent 直接查生命周期历史和找回条目；内部可以按当前 Snapshot 引用 id 取正文，归档项仍不可见、不可恢复。用户原话“是，原意就是禁止 Agent 查表和找回”，已同步 02 §3.3a。
- 历史轮次索引（细节与流水在各索引与 git 历史中，本看板不复述）：V1 首轮 `.autonomous/20261007-v1-first-implementation/`；V1.5 文档准备 `20261008-v1.5-adjustment-and-acceptance/`；V1.5 实施与云端接续 `20261009-v1.5-implementation/`、`20261009-v1.5-cloud-resume/`。
- 既有验证边界（V1.5 遗留，V1.6 收尾时重跑）：独立 Verification 未通过（含机制形状/时间语义检查项缺口）；官方 Dashboard Validation 未做（用户旁路体验）。
- 运行口径：Main/Noting 真实运行 DeepSeek 官方接口（OpenAI Chat Completions 格式已取证）；不使用 Codex App Server / Codex Proxy；测试一律隔离 `HERMES_HOME`，不触碰真实用户状态。
- 上下文开销：基线与 Secretary 增量实测记录在 [docs/05-context-cost-ledger.md](docs/05-context-cost-ledger.md)（tiktoken o200k_base；主会话增量现行 775 / V1.6 目标 1,419，占完整 profile 基线 2.9% / 5.4%）。

## V1.6 施工清单（依据现行 02；prompt 逐字对照 §5.12）

**A. 存储与工具**
1. `secretary_notebook_item` 生命周期表迁移（§3.3a）：snapshot payload 改存**有序 item id 列表**（无 FK、纯逻辑引用）；item 行 **INSERT-only**，edit/status/schedule 变更插新行并**继承 lineage_id**（create 开新 lineage）；id 为**自增十进制**（对外字符串），行 id＝agent 可见 entry_id＝版本 id；不可变由结构保证，历史演进可完全重放。
2. `notebook_mutate` 拆三工具（§5.12-3.6）：`notebook_manage`（create/archive）／`notebook_edit`（edit/status）／`notebook_schedule`（schedule_update/schedule_cancel，**无 schedule_create**——新条目的 Schedule 在 create 时经 `watchpoint.until` 或 `expression` 子参数设置）；状态机逐类型写死在 `notebook_edit` 的 status description（与 §2.5 一致，persistence 三类禁止 status）。
3. `agent_task` → `secretary_task` 改名（§2.5）：schema 枚举、required fields、status 描述、guidance 段③、提醒模板（`Secretary task due: {task}`）、§3.8/§6.17 同步；其 Schedule 加**显式必填** `delivery_mode`（instant/deferred，仅此类型；instant 到点可拉 turn，deferred 不拉）。
4. archive 卸下语义（§3.7）：archived 条目所有 agent 面过滤、下轮不可见；**无 restore、无任何找回通路**；归档行存 item 表、仅审计视图可见。返回契约（§3.7）：成功 `{"success": true, "entry": <完整条目含新 id>}`＋四分区 state；**任何内容变更都换 id**（旧 id 即刻失效，误用报 unknown-entry 点名）；失败 `success:false`＋可诊断报错。报错可诊断化（§5.12-6）：`Unknown semantic fields for {type}: {违规}; allowed: {允许}`、`Illegal status transition for {type} from {current}: legal targets {…}`。

**B. Prompt 落码**（§5.12 冻结版；**分支注入**：仅全局 Noting 开启的 eligible main conversation，其它会话/平台保持原生原文；prompt 字节稳定、幂等）
5. guidance 六段（§5.12-1.2）：身份首段（秘书心智：不亲自下场、指派督办、用户视角验收、主动沟通；两例）＋段序（Persistence Candidates 前移）＋④⑤合并段＋memo/routing 尾段。
6. task instruction 全文替换＋continuation 新文案（background-task 口径）＋`<noting-tools>` 追加**当前 Notebook 状态**（首条与每次 continuation）。
7. cron 三处（§5.12-7）：主描述（独立定时 agent、与主会话无关；仅显式要求全局管理/免验收重复任务时用；会话内 schedule 归 Notebook）、schedule 字段（删 "remind me in N minutes" 诱导＋加边界句）、`_LOCAL_CRON_DELIVERY_NOTE` 追加反诱导段。

**C. 机制**
8. `noting_memo` 工具（§3.5）：operation 四值（add/replace/delete/list）；index 从 1、delete/replace 后重排；add 返回 `created: 内容, index=N`；replace/delete 返回 `replaced:`/`deleted:`＋完整 current memo；list 为 Markdown 有序列表、空态 `No memo after last noting`；**memo 非空 ⇒ Noting 保持开启**，`/noting off` 仅空 memo 生效；memo **不触发** Noting，随下次 Trigger 的 task 后缀进 child 上下文；commit 时清空并**随同一 Anchor 归档**（§3.3a 同款归档语义）。
9. Idle Trigger 定时器化（§4.5）：turn 结束 arm（due_at=finished+delay、registry+锁+daemon）；新 turn 取消重排；到点回查持久状态后**只产生一个 Trigger**；session cap 排序键改 `(持有待触发定时器, last_active)`——**排最后、非绝对豁免**；`idle_candidates` 仅作 catch-up 兜底，不得周期性合成 Trigger。
10. Reminder 投递改造（§5.6）：deferred 活跃时落 durable 行，多条到期**一次批量注入**（`以下提醒已到期。`＋JSON，schedule→due_at）；instant＝用户消息提交带 timestamp；**两步 ACK**（预登记→装配校验→成功响应才清 pending；失败保持 pending 重投，幂等键不阻止重落行）；**compaction pass 拒投**（识别本次装配为压缩则拒绝、保持 pending、下次装配重试）；**去掉每请求读库**。
11. Framework Message（§5.6/§2.6）：runtime 内部双写（活列表＋落库同一行）；Force 准入即发"已派发"句、finish 发统一 `Background: notebook updated at <time>`；Finish Notice 写 `display_metadata["noting_run_output"]=true` ⇒ **不推进 anchor**（anchor＝最后一条无该标记的行；其它一切行照旧推进；不用 kind 白名单）。
12. `context_overflow` 强制收尾（§5.8）：请求装不下时与五 Turn 同款——Commit Gate 照走、Finish Notice 照发、termination 记第四型 `context_overflow`；禁止无 Snapshot 丢弃。
13. History Search（§2.3/§2.5）：结果行必附 entry timestamp＋message_uid；candidate provenance 支持 `source_message_identities` 或 `source_time_range`（不强调优先）；**search 单行超 ~800 字符就地截断标记，无强制全文参数；全文唯一通道＝read＋message_uid 精确取**。

**D. 收尾门禁**
14. 独立 Verification 全范围复审（含机制形状/时间语义逐行核验）。
15. 官方 Dashboard Validation（用户旁路体验）。

## 施工硬约束

- **不启用即原生**（AGENTS.md）：功能未启用场景与原生行为完全一致，新机制一律分支/旁路接入。
- 冻结父前缀（root/tools/messages）不动；prompt 文本逐字稳定、分支注入。
- Secretary 持久化只增自有表，不改 Hermes 原有表。
- **开发阶段不做数据迁移**（AGENTS.md）：持久化结构变更直接重建库；所有库在仓库内、全是测试数据。
- 测试走 `scripts/run_tests.sh`（隔离 `HERMES_HOME`），检查 `python scripts/check`；不为建基线预跑大型检查。

## 环境

官方 PM 工作区 `.venv`（Python 3.14.7），现有锁文件不变；运行状态仅 ignored `.hermes-dev/`；不 push 除非用户要求。
