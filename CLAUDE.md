# Hermes Secretary 主看板

## 自主口径收敛 · 待用户追认

> 本区域按 AGENTS.md 永久维护。无待追认收敛时注明"暂无"。

| ID | 规格空白、收敛及理由 | 状态 | 用户确认 |
|---|---|---|---|
| — | **暂无待追认收敛。** 历史三项已闭环：P01（task instruction 四句系现行 04 §4.4 漏实现的补齐，非新口径）；P02（memo 非空 ⇒ Noting 保持开启，off 仅空 memo 时生效）已确认；P03（memo 触发来源记录名）前提被用户否定，已撤销——memo 不是触发源 | 已闭环 | 2026-10-11 |

## 当前状态

- **V1.5 产品口径已收口，实施与验收尚未闭环（2026-10-11）**：本轮全部纠偏口径已并入 02 权威规格——新增 **§5.12 全量 prompt 冻结清单**（按代码归属逐条收录，Frozen/Target 双态，施工逐字对照）、**§3.3a 条目生命周期表**、archive 卸下语义、三工具拆分、secretary_task 改名＋delivery_mode、context_overflow、定时器机制、投递 ACK/M4 规则、anchor 判定（noting_run_output 标记）、History Search 截断规则。**V1.6 实际启动提交为 `fa51561601`，文档冻结提交为 `fc2668310b`**；此前 `ec4fc58057` 为口径整理过程中的历史提交，完整 docs 提交链见 git log。
- **V1.6 自主实现已启动**（用户 2026-10-11 最新指令：“开始，1.6轮自主实现”，替代此前待启动及不走自主流程的安排）。轮次 `.autonomous/20261011-v1.6-implementation/`；已冻结现行规格并进入分组实施；随后主会话集成、独立 Verification 与官方 Dashboard Validation。启动提交 `fa51561601`，启动时工作区干净；当前已有本轮未提交实现，尚未最终验收。
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
8. `noting_memo` 工具（§3.5）：operation 四值（add/replace/delete/list）；index 从 1、delete/replace 后重排；add 返回 `created: 内容, index=N`；replace/delete 返回 `replaced:`/`deleted:`＋完整 current memo；list 为 Markdown 有序列表、空态 `No memo after last noting`；**memo 非空 ⇒ Noting 保持开启**，`/noting off` 仅空 memo 生效；memo **不触发** Noting，随下次 Trigger 的 task 后缀进 child 上下文；commit 时仅消费该任务拿到且仍未替换/删除的条目并**随同一 Anchor 归档**，期间新增/替换内容保留（C03）。
9. Idle Trigger 定时器化（§4.5）：turn 结束 arm（due_at=finished+delay、registry+锁+daemon）；新 turn 取消重排；到点回查持久状态后**只产生一个 Trigger**；session cap 排序键改 `(持有待触发定时器, last_active)`——**排最后、非绝对豁免**；`idle_candidates` 仅作 catch-up 兜底，不得周期性合成 Trigger。
10. Reminder 投递改造（§5.6）：deferred 活跃时落 durable 行，多条到期**一次批量注入**（`以下提醒已到期。`＋JSON，schedule→due_at）；instant＝用户消息提交带 timestamp；**两步 ACK**（预登记→装配校验→成功响应才清 pending；失败保持 pending 重投，幂等键不阻止重落行）；**compaction pass 拒投**（识别本次装配为压缩则拒绝、保持 pending、下次装配重试）；**去掉每请求读库**。
11. Framework Message（§5.6/§2.6）：runtime 内部双写（活列表＋落库同一行）；Force 准入即发"已派发"句、finish 发统一 `Background: notebook updated at <time>. Processed memo entries have been cleared.`（C04）；Finish Notice 写 `display_metadata["noting_run_output"]=true` ⇒ **不推进 anchor**（anchor＝最后一条无该标记的行；其它一切行照旧推进；不用 kind 白名单）。
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

## V1.6 当前编排与证据

- 冻结基线：`fc2668310b`（完整哈希见本轮 baseline.txt）；启动 `fa51561601`。计划见本轮 plan.md；三份核心文档和 C02 一并纳入冻结树。
- T1–T4 实现及局部修补已交回，T5 主会话集中 review 中。预算正式入口／普通 System Anchor 已提供 50/50 集成定向证据；Framework 队列 owner、Force owner 与 branch 边界已交回；尚不能以子 Agent 测试代替主会话 review。白名单见 plan；子 Agent 不再派生、不提交。
- 用户明确讨论不暂停后台实施；2026-10-11 最新指令取消新 skill 单独试点，后续正式 Verification 直接使用，节省额度并抓紧推进。skill_trial 已停止，不续派试点；其执行曾返回额度限制，不计为审查证据。官方 Dashboard 隔离环境已就绪（localhost:53345，PID 24660；接管记录 `.hermes-dev/v1.6-evidence/dashboard-prep/launch.json`），首页与健康检查通过，尚未用户验收。真实 Native DeepSeek prefix/cache 取证已交回，最后 parent-compact 的八个关键源码哈希与当前一致；普通与 continuation 的 noting_runtime 哈希不同，不能冒充同版本全覆盖。两独立门禁尚未启动，尚无全范围最终完成证据。
- PM Python 3.14.7；lock SHA256 `2bc4db483e9cba927cd7147f9ccbb09635f85bb3f1f36d6e9d51d06b65d1c67e`。未预跑大型检查；日志 `.hermes-dev/v1.6-evidence/`。既有失败和平台边界见当前状态。
- 隔离真实运行准备：全新 `.hermes-dev/v1.6-validation/`，DeepSeek 官方 Chat Completions／deepseek-flash，未复用旧库；凭据仅 ignored 本地 `.env`，未输出。官方 Dashboard 已有构建；尚未运行真实验收。
- T1 首次 Prelude 节点缺少 `is_compaction` 导致 13 失败，已修复；已提供局部 model/store/schedule/atomicity/branch 证据，主会话 review 中。首次测试临时库在系统隔离临时目录，后续 runner 使用仓库内分组专属 `--basetemp`，不更改 runner 规则。完整日志见 storage 证据目录。
- T2 初步接收：34/34、正式 host Child→Snapshot 5/5、补充 timer 9/9；主会话核对 timer/DB 原子周期消费/attach/cap 正式路径。R1（已有 Framework queue 遇结束前关闭）已修复并提供 3/3 定向证据；尚未阶段提交。T3 已提供 compaction 拒投/下次重试、跨 host 崩溃恢复及旧 Reminder 回归证据，仍在收敛尾部持久化检查。不同日志有重叠，不累加用例数。
- 主会话接线：原 `secretary_reconcile_session_conn` 的 Notebook pointer reconciliation 后调用 `reminder_settle_retired_conn`，只结算已有 carry 且源行已 compacted、同 UID 无 active 行的 pending occurrence。M4 未落行和普通请求丢行保持 pending；证据由 T3 的原生压缩/重投场景提供。
- 集成 review：主会话已阅读 Memo 不可变行身份及同事务消费、Child 当前 Notebook 后缀／原生请求预算 guard／Overflow Commit Gate、Framework 所属 ref 冻结与 native tail flush／append transaction、Force及Finish调用、普通System Anchor／Full audit／branch和cron bridge ContextVar路径；按已交回日志接收 R2 定向证据，不重复复跑。规格补充已提交 `8626dc30d5`，baseline保留初始提交并追加此授权版本。
- 正式 Verification 已派遣全新无上下文审查者，阶段A仅从 `8626dc30d5` 的01/02/04规格建立全范围判据，落盘后再提供实现快照与证据。用户取消的skill试点不恢复。集成阶段快照及一次必要扩大检查随后执行；Dashboard Validation须在Verification通过后进入。
- **用户托管目标已挂载**：完成本轮 V1.6 自主实现，含两独立门禁与 final-delivery；用户暂时离开不停止执行。阶段实现提交 `3661812638171ec9a83a8553fcd4a05f7924ed0b`，尚未最终验收。旧 Dashboard `9119`／PID 97007 已按用户授权 SIGTERM 并确认退出，仅保留本轮 `53345` 隔离实例；最终验收前须重启以加载最新实现快照。
- **统一检查已完成**：root 执行一次10项全集，首次 health 发现主循环 CC 23>原基线22与新测试fixture导入同名 F811；提取提醒装配 helper、使用pytest_plugins注册fixture后仅复测 ruff/health，两项通过；其余8项首次已通过，冻结规则未改。日志 `integration-checks.log`／`integration-checks-fix.log`。
- **一次扩大回归已完成**：128个相关文件，四组各自 canonical runner `-j 1`、独立仓库内basetemp，178.4秒；首次1563通过、9失败、3跳过，失败已定向闭环：ACP依赖缺失经官方PM用现有锁在ignored环境补齐；Prompt/Checkpoint纯文件用例的仓库内basetemp引入父级Git根，改用runner默认独立临时目录（这些用例不创建运行数据库）；schema旧表清单补上新增memo表。四个失败文件定向复测分别22/22、57/57+1skip、3/3、9/9，覆盖结果为1572通过、3跳过，不累加重叠用例。未重跑128文件或无关全仓库suite。证据 `integration-test-plan.json`、`integration-group-{0..3}.log`、`integration-{acp,prompt-fixture,checkpoint-fixture,schema}-fix.log`；首次启动参数解析失败未执行测试，已记录。

## 本轮产品边界确认与实施方案

- **C03 Memo 并发消费已确认**：用户确认未处理的新增/修改内容应保留，要求“用正向代码机制，保证不变量平凡成立”，尽量避免复杂 revision；已同步 02 §3.5 与轮次索引。
- **C04/C05 完成通知已确认**：用户认可简单行身份方案，并要求现有 Finish Framework Message 表达已处理便签已清空；C05 明确须转写为正常系统英文，正文为 `Background: notebook updated at <snapshot commit time>. Processed memo entries have been cleared.`，已同步 02 §5.6、§5.12 与轮次索引；接线与定向证据已交回，主会话待复核。Notebook 与已消费 memo 同事务提交后才发送该统一通知。
- 工程方案（主会话选择，不冒充用户逐项批准）：单 active 表增加不可复用的内部行主键，内容不可变；replace 删除旧行并插入新行，对外仍按连续 index 操作。dispatch 冻结行身份与内容；Snapshot commit 同事务仅归档/删除该任务实际拿到、且仍活跃的行，再重排显示 index。新增/替换行天然不在清理集合；失败不改 active，用户删除的内容不复活。实施与局部证据已交回，尚未通过全范围验收。

## Verification 历史复盘与 skill 调优

- 用户要求沿 Git 文档历史主动识别 1.5→1.6 口径纠偏与漏审，不要求用户复述；讨论不暂停后台实现。
- 已核实：最早 `89a78c193e` 02 §4.5 已明确 main Turn 生命周期 timer；首轮/V1.5 报告 R050/V43 却只验证 elapsed，接受固定 5 秒轮询。历史 `1127da8731:CLAUDE.md` D02 记录 673 次尝试、672 次 same-anchor skip，是机制被替换后的真实症状；具体 registry/thread/cap 细节为后续细化，不能据此否定原 timer 要求。
- 已核实：首轮报告 R077 接受首响应后修改 child.tools，并称为 suffix-only divergence；历史 `14102ac85c:CLAUDE.md` 已承认头部与后缀被混淆、测试把偏差当预期，原规格没有授权该修改。
- 静态反证：V1.5 V39 只以外层 middleware 返回成功 ACK staged IDs；合法 middleware 删除载体或本地短路时，Provider 未收到提醒仍可能 ACK。V25 则接受额外 role=system Anchor 排除，旧普通逻辑消息定义未授权这一限制。两项为旧树源码反证，本次未新运行测试。
- 另需区分：历史 `1127da8731:CLAUDE.md` 明确记录 request-only System Reminder 是起草规格偏离用户一贯原意；这是审查输入/规格解释失真问题，不能仅以代码符合旧文档合理化。V-001/002/003 已被旧审查抓到，不冒充漏审；真正新增产品要求不倒推旧版本违规。
- **C06 已确认并更新 skill**：Verification先仅读规格建立判据并落盘，之后才读代码/测试/报告/看板；特别关注方向明确但接线与实现路径未详述的要求。主会话是提案方，Verification是依据规格与判据的评审方，授权内工程细化自行收敛推进。关键研讨及结论进入报告、final-delivery与最终汇报。全部原有审查职责保留，未修改冻结代码检查类别或阈值，历史报告不追改。
- 已修改三个全局 skill（spec-implementation-review、autonomous-run、delivery-evidence-review）与两个模板，格式校验全部通过；原件及差异证据位于 ignored `.hermes-dev/v1.6-evidence/skill-tuning/`。这只证明结构有效，实际审查效果仍待本轮独立门禁验证。
