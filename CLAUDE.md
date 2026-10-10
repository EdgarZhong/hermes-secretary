# Hermes Secretary 主看板

## 自主口径收敛 · 待用户追认

> 本区域按 AGENTS.md 永久维护。无待追认收敛时注明"暂无"。

| ID | 规格空白、收敛及理由 | 状态 | 用户确认 |
|---|---|---|---|
| — | **暂无待追认收敛。** 历史三项已闭环：P01（task instruction 四句系现行 04 §4.4 漏实现的补齐，非新口径）；P02（memo 非空 ⇒ Noting 保持开启，off 仅空 memo 时生效）已确认；P03（memo 触发来源记录名）前提被用户否定，已撤销——memo 不是触发源 | 已闭环 | 2026-10-11 |

## 当前状态

- **V1.5 轮次已收口（2026-10-11）**：本轮全部纠偏口径已并入 02 权威规格——新增 **§5.12 全量 prompt 冻结清单**（按代码归属逐条收录，Frozen/Target 双态，施工逐字对照）、**§3.3a 条目生命周期表**、archive 卸下语义、三工具拆分、secretary_task 改名＋delivery_mode、context_overflow、定时器机制、投递 ACK/M4 规则、anchor 判定（noting_run_output 标记）。冻结基线见最近 docs 提交（`9052a28eb6` 及后续 02 补记）。
- **V1.6 待开启**（用户 2026-10-11：不走 autonomous 自主实现流程，开启方式与时机待用户定）。施工清单见下，全部依据现行 02。
- 历史轮次索引（细节与流水在各索引与 git 历史中，本看板不再复述）：V1 首轮 `.autonomous/20261007-v1-first-implementation/`；V1.5 文档准备 `20261008-v1.5-adjustment-and-acceptance/`；V1.5 实施与云端接续 `20261009-v1.5-implementation/`、`20261009-v1.5-cloud-resume/`。
- 既有验证边界（V1.5 遗留，V1.6 收尾时重跑）：独立 Verification 未通过（含机制形状/时间语义检查项缺口）；官方 Dashboard Validation 未做（用户旁路体验）。
- 运行口径：Main/Noting 真实运行 DeepSeek 官方接口（OpenAI Chat Completions 格式已取证）；不使用 Codex App Server / Codex Proxy；测试一律隔离 `HERMES_HOME`，不触碰真实用户状态。

## V1.6 施工清单（依据现行 02；prompt 逐字对照 §5.12）

**A. 存储与工具**
1. `secretary_notebook_item` 生命周期表迁移：snapshot payload 改存有序 item id 列表、无 FK、INSERT-only、lineage 继承、自增十进制 id（§3.3a）。
2. `notebook_mutate` 拆三工具：`notebook_manage`（create/archive）／`notebook_edit`（edit/status）／`notebook_schedule`（schedule_update/schedule_cancel）；schema 以 §5.12-3.6 为准；状态机逐类型入 description。
3. `agent_task` → `secretary_task` 改名＋Schedule 显式 `delivery_mode`（instant/deferred，仅该类型）（§2.5/§3.8/§6.17）。
4. archive 卸下语义（过滤、无 restore、audit-only）＋返回契约（success＋完整 entry 含新 id）＋报错可诊断化（§3.7、§5.12-6）。

**B. Prompt 落码**（§5.12 冻结版；分支注入：仅全局 Noting 开启的 eligible main conversation，其它会话/平台保持原生原文）
5. guidance 六段：身份首段（含两例）＋段序（Persistence Candidates 前移）＋④⑤合并段＋memo/routing 尾段（§5.12-1.2）。
6. task instruction 全文替换＋continuation 新文案（background-task 口径）＋`<noting-tools>` 追加当前 Notebook 状态（§5.12-2）。
7. cron 三处：主描述、schedule 字段、`_LOCAL_CRON_DELIVERY_NOTE` 追加（§5.12-7）。

**C. 机制**
8. `noting_memo` 工具：operation 四值（add/replace/delete/list）、index 从 1、Markdown 有序列表、空态文案、commit 清空并随 Anchor 归档、`/noting off` 仅空 memo 生效（§3.5）。
9. Idle Trigger 定时器化：turn 结束 arm、新 turn 取消重排、一周期一 Trigger、session cap 排序"持有待触发定时器排最后"（非绝对豁免）、`idle_candidates` 仅作 catch-up 兜底（§4.5）。
10. Reminder 投递改造：deferred 活跃时落 durable 行（批量注入"以下提醒已到期。"＋JSON、schedule→due_at）、instant 走用户消息路径、两步 ACK、compaction pass 拒投保持 pending、去掉每请求读库（§5.6）。
11. Framework Message：runtime 内部双写、Force 两条（派发句＋统一 Finish Notice）、`display_metadata["noting_run_output"]=true` 标记（§5.6、§2.6）。
12. `context_overflow` 强制收尾（与五 Turn 同款：Commit Gate 照走、Finish Notice 照发）（§5.8）。
13. History Search：结果行必附 entry timestamp＋message_uid；candidate provenance 支持 `source_time_range`（§2.3/§2.5）。

**D. 收尾门禁**
14. 独立 Verification 全范围复审（含机制形状/时间语义逐行核验）。
15. 官方 Dashboard Validation（用户旁路体验）。

## 施工硬约束

- **不启用即原生**（AGENTS.md）：功能未启用场景与原生行为完全一致，新机制一律分支/旁路接入。
- 冻结父前缀（root/tools/messages）不动；prompt 文本逐字稳定、分支注入。
- Secretary 持久化只增自有表，不改 Hermes 原有表。
- 测试走 `scripts/run_tests.sh`（隔离 `HERMES_HOME`），检查 `python scripts/check`；不为建基线预跑大型检查。

## 环境

官方 PM 工作区 `.venv`（Python 3.14.7），现有锁文件不变；运行状态仅 ignored `.hermes-dev/`；不 push 除非用户要求。
