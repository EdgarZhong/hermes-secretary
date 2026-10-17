> **接续说明（本次独立复审追加）：** 本文件是da68703/de810ba写入的较早GitHub静态复核，以下原文完整保留，NOT_RUN/INCOMPLETE只描述该次工作。当前公开主仓库第2次逐条独立审查及四组实测反证已追加到 [verification.md](verification.md)，当前门禁仍不通过。

# 第三轮自主实现 · 第二次 Verification（GitHub 独立静态复核）

> 日期：2026-10-17。审查对象：`EdgarZhong/hermes-secretary` 公共核心，固定产品提交 `b40fa1ff2a771066b4da1d8978a7abe44327e530`。本报告直接提交在 `main`；报告提交自身只改变文档，不作为产品修复或测试证据。
>
> **判定：NOT PASS / BLOCKED_EVIDENCE。** 已开展第二次独立源码/规格/历史证据复核，但**没有完成项目规定的 Astra/high 全量独立门禁，也没有在本环境运行本地测试、真实 DeepSeek 或产品交互**。因此这是一份可供正式门禁接续的、具备静态反证的第二次复核报告；不能称第二次全范围 Verification 已通过。Validation 不应据此启动。

## 1. 对象、权威依据与可重用证据

| 项目 | 固定内容 | 本次实际行为 |
|---|---|---|
| 公共目标实现 | `b40fa1ff2a771066b4da1d8978a7abe44327e530`；原位于 `codex/round3-local-completion` | GitHub 连接器回读代码、规格与历史报告；本会话按用户新指令将 `main` 从 `c099c8c490846e7989adc4d4aea9a1b4a9a37162` **非强推快进**到该提交；不把快进当验收 |
| 产品冻结要求 | `docs/notebook-ontology-whiteboard.html`、`docs/07-scheduler-notebook-noting-compaction-redesign.md`；旧01/02/04/06只保留新版明确继承部分 | 依据本轮冻结索引的现行范围和首次独立审查 V01–V60 判据；没有重新引入旧 Memo、旧工具、旧 Notebook-owned Schedule |
| 首次独立审查 | `verification.md`：公共 `323c64dacba1190c16bacc69bbe5e76db6f43529`、个人 `e1af6cc45ffbd53c930d1d2f14ab46858e966ecd` | 保留“56符合／2不符合／2证据不足”的历史固定版本结论；它不是本提交上的现行结果 |
| 第三轮开发复测 | `CLAUDE.md`、`real-model-report.md`、`regression-plan.md`、C10/C9交回报告 | 逐项区分 **报告声称的本机实测** 与 **本次能独立回读的源码**；ignored `.hermes-dev/` 原始请求、SQLite、log、manifest 当前不可读取，未复算哈希、未重放命令 |
| 个人 NM Provider | 独立仓库 `EdgarZhong/hermes-nmem-provider`，PHASE3 §1–7 | **本次未检查个人仓新HEAD**，不以公开仓结论覆盖 V52–V60；真实 NM Memory/Thread/Space 写入仍不获授权 |

本审查仅通过 GitHub 连接器读远端文件，并核对已存在的开发实测证据说明。未启动隔离 `round3` profile、没有重建用户本机库、没有调用服务商模型、没有执行 `scripts/run_tests.sh`／`scripts/check`、没有 Cloud/设备部署。**所有本次命令级结论均为 NOT_RUN**。既有报告中的 PASS 是其各自固定版本、owner 与日志的历史陈述，不能自动变成审查者亲自取得的 PASS。

## 2. 独立静态接线复核

本次直接阅读：`secretary/noting_prompts.py`、07 §8.10–8.13、`secretary/notebook_contract.py`、`secretary/notebook_model.py`、`secretary/noting_child.py`、`secretary/noting_runtime.py`、`hermes_state_secretary_notebook.py`、`secretary/notebook_render.py`、`secretary/scheduler_table.py`、`tests/secretary/test_r3_compaction_visibility.py`、`tests/secretary/test_r3_framework.py`，以及首轮 Verification 与本轮真实模型、回归、F18/F19 收口报告。

- **V23 / 来源结算文本接线：静态一致，但行为未证成。** 最新07 §8.11 Step4与 `DEFAULT_NOTING_TASK_INSTRUCTION` 对应句均要求：获批内容及实际分发成功范围判定；先用 `notebook_maintain` 归档完全成功且无保留理由的来源，或改写 `fields.description` 留下真正未交付／仍需的部分；再整理 Candidate 的 `fields.notebook_refs`、修归档阻塞引用，最后关闭或更新 Candidate；失败/未知不清退。不是用只读 `candidate_refs` 写入。此处属于既有 E1/E2 语义的动作细化，未发现新增 Noting 外部写权限。
- **工具/提交职责：结构合法不等于语义已结算。** `NotebookWorkingState.update/archive` 强制形状、来源、当前引用和版本变更；`_commit_when_complete` 使用现有 owner/Anchor/合法 Snapshot gate。它们没有、也不应增加“见 Memory 成功就机械删除正文”的并行结算执行器。成功清退依赖 Noting 原生任务**实际提出合法工具操作**并产生正确 Snapshot，单凭最新版 Prompt 字面准确不满足 V23。
- **V04/V47 / pointer 复核：源码存在同一合法路径覆盖选择与发布时再验。** `_notebook_anchor_positions_conn` 从 Full Foreground 过滤合法 Anchor；对 compaction 复用 UID 使用冻结的 `_notebook_coverage_position` 避免“移动到更晚物理行”冒充新内容；通知测试覆盖 pointer 校验、durable append 锁与 live 顺序。F18 开发报告的定向 31 PASS 尚需关联原日志与实际产物。
- **V38/V39 / 压缩可见性：已有针对性修复与受控测试。** F19 的 `test_r3_compaction_visibility.py` 覆盖尾部／中部 human_only／无隐藏、完整／here1、失败回滚等 9 种组合，使用真实 AIAgent/SessionDB/压缩接缝，但摘要/模型响应被受控替代；报告称9项及原生邻域35项通过。不能把这等同 `b40fa1f` 真实模型下 Force+源结算整体复证。
- **V51 / 时间可读投影：确认代码层有定向修复。** `readable_notebook_entry` 在展示副本中规范 created/updated/processing/evidence/source_range；`schedule_public_conn` 的 `canonical_schedule.run_at` 和原生绝对 `display` 使用共用可读投影，原始 DB canonical 不在此处修改。报告中的17项/8项以及个人Recall修复需按精确版本与日志继承，而不是将首次 V51 失败改写消失。
- **V01/V50 / 原生关闭边界与入口：首次失败后的局部复证有记录，但本次没有重跑。** `regression-plan.md` §7首轮136文件及相应扩展入口为1766 PASS、29 FAIL、4 setup ERROR、3 skip、两类检查阻断。之后报告指向逐失败的修复与复测，并称33个失败/错误节点及两检查阻断已关闭；在本次审查环境中无法取得其 ignored 完整日志及确认每个依赖指纹，不能把“报告有PASS”写成“本次已亲自复核全绿”。

对其余 V02–V60 条款，**没有做出逐条新版 PASS 判断**：在首次审查中原已符合的事项可按冻结代码/依赖变化规则复用原 owner 的有效证据；受本次修复影响的入口须定向核对；个人 V52–V60 保持独立仓及授权边界，不冒充本次覆盖。

## 3. 发现项与关闭要求

### R3-V2-01（P1，V23/F16）：成功外部交付后的 Notebook 来源正文未按覆盖结算

**事实层级：旧版真实失败仍有效；最新版修复行为未得到证实（OPEN / BLOCKED_EVIDENCE）。**

- 首审在 `323c64d` 真实链路观察到：Memory实际成功、Candidate13归档，但 source6 v34 仅新增 `processing_note`，已成功交付内容继续留在 `description`；独立新增 source35 并不是保留 source6 全文的理由（`verification.md` F-V23）。
- 后续 `R3-019` 的模型迹线依旧出现 Candidate 先关、部分来源不精简且 Anchor commit 失败；F17–F19 针对提交路径/覆盖进行了真实或受控整改，不消除源语义失败。
- `R3-022` 固定 `40f4ecceb772e6faaa98b99d95b8f4b0de5e31f0` 的新库正式链**两个真实 child 已完成且新 pointer 生效**，但 source1/3/4 仍仅加已保存注记，source4保留已交付段，source2只是在同一字段追加新事实，Candidate6/7/9却被归档。此证实 F18/F19 有效后 F16 仍可失败（`CLAUDE.md` R3-022、`real-model-report.md`）。
- `b40fa1f` 已把 Step4 细化为明确的 `fields.description` 重写或完全归档；**此 SHA 没有新的正式模型结算轨迹**。因此不能说最新版仍然复现相同失败，也不能说已经修好。

**用户影响：** 用户已经批准且成功保存的事项仍占 Notebook 当前工作视图，长期积累重复的已交付记忆候选和上下文成本；真正尚未交付的部分可能被错误合并或忘记。违反 Notebook“工作状态、精确溯源且成功范围结算”的核心体验。

**最小关闭操作：** 固定 `b40fa1f` 或本报告后实际产品 SHA，在隔离 `round3` 新库通过原生 Main/Slash/RPC：创建有原始来源与 Candidate 的合成事项 → 具体草案 → 用户逐字批准受控测试 USER 目标 → 真实 authorized native tool success → 同源追加未批准内容、未完责任及仍需引用的另一 Candidate → 真正 manual/auto/Idle 联合入口启动 Noting → 读取正式 `/notebook` 和版本审计。必须观察：(a) 全部成功交付且无保留理由的来源归档；(b) 同条部分交付时 `fields.description` 实际移走已交付覆盖、完整保留新内容及必要背景；(c) Candidate 仅在来源成功处理后清退/收缩；(d) 失败/未知与其他候选依赖不误删；(e) 新 Snapshot 合法提交并可在 Main 当前视图读取。留存实际 tool_calls、result、UID、before/after 源版本、pointer、Prompt版本与请求hash。**不进行真实个人 NM 写入，不人工 SQL 删除、不伪造模型写入收据、不新增自动强制归档门禁。**

### R3-V2-02（P2，V01/V50）：统一回归与 Gateway 正式入口的证据索引尚未可独立回读

**事实层级：开发报告称定向整改已完成；本次不能确认同版本全范围门禁，EVIDENCE_GAP。**

首次 Gateway 4 setup ERROR 没有运行主体、原生压缩/ACP 与退休工具旧断言各有旧失败。后续交回报告描述了按现行契约修复并定向补证（原33失败/错误、两检查）；这不等于未修。关闭时保留首失败及修复对应节点、现行版本 hash、具体 runner 命令、环境/锁及日志 hash，逐项指向哪条原始失败被哪次定向 PASS 关闭；仅因共享依赖变化影响原证据时补相邻测试。**不为审查者重复跑既有136文件／十类规则全套**，也不能单用 1766 PASS 抵消首失败。

### R3-V2-03（P2，V04/V38/V39/V47）：F18/F19 修复边界需要最终目标 SHA 的完整产品链归因

**事实层级：静态补丁方向符合冻结路径；报告中的新测试是开发证据，不是本次独立验收。**

F18 的复用UID排序、F19 的 human_only 摘要源一致性、Force/通知邻域及 pointer 原子发布须在**最终实现版本**核对：同一 Source UID 被压缩携带而 coverage 不前移，隐藏反馈不进入模型摘要与 Anchor，原生失败/no-op恢复 raw、真实联合压缩不因 child 失败被阻断、成功 pointer/Framework 仅对当前结果发布。可与 R3-V2-01 的同一真实链合并取证，不专为不同审查人重新建第二套试验。

### R3-V2-04（P2，V51）：已修时间展示应按原样继承证据、但不要把初审缺陷直接标 PASS

Notebook、Scheduler 绝对时间展示本次已查到代码层修订；真实时区/秒精度、source_time_range、slash/Proposal/Framework 及个人Recall分别有开发阶段定向记录。正式复审只需复核相应测试/日志/产品SHA是否覆盖已修出口，未知时间不得捏造成有效时刻；禁止为了显示格式改真实 timestamp 的存储精度或 Schedule 计算。个人Recall需在个人仓单独核对，不能由公开仓代签。

## 4. 需求覆盖状态与用户链路

| 用户链路 / 对应条款 | 第二次审查已确认 | 仍不能宣称 |
|---|---|---|
| 一直在同一Conversation交谈、跨压缩定位原文（V02–V04/V24–V29） | 历史/Notebook有效路径与新coverage排序有代码接线；首审和开发证据可定位 | 最终SHA所有分支、rewind、跨平台真实入口都已重新端到端通过 |
| Notebook内容维护、完成持久化后结算（V05–V23） | 四工具与来源/引用/commit gate有效；Prompt明确要求来源先结算 | **V23/F16成功清退已交付源正文已通过** |
| Scheduler、Reminder、ACK、并发/重启（V30–V36） | 定向源码与原交回报告可定位，未发现因F16文本改动而需重构 | 本次已现场执行任何到期、ACK、失败恢复或跨进程竞态 |
| Force/Idle/联合压缩/Noting child（V37–V48） | 源码有F18/F19修补与受控正式接线测试，记录了旧失败→修复路径 | `b40fa1f` 的所有真实Force＋语义结算在本次通过 |
| Main工具、Prompt、Slash/时间（V49–V51） | 最新Step4、可读时间投影及独立工具面可核 | 只凭源码和报告就关闭所有首次时间/四Gateway失败 |
| 个人Provider（V52–V60） | 只确认公开主库仍隔离个人代码 | 本次完成个人仓二审或真实NM写入；个人线不属于本仓报告的“PASS” |

## 5. 决策、下一执行顺序及变更边界

**当前验收结论：NOT PASS / BLOCKED_EVIDENCE；不进入 Validation，不允许将 `main` 快进理解为“已发布/通过”。** 已知最关键的产品阻断是 V23/F16 **历史真实失败且最新版本缺少成功复证**。本次没有取得证明 `b40fa1f` 新引入结构性失败的证据，所以不用错误标签宣称该 SHA 新失败；同时不能降格为“只是一点测试没跑”。

最小接续顺序：

1. 在可访问用户本地忽略证据的执行环境，先把首轮33失败/错误、两检查及V51/F18/F19定向关闭的 manifest／source hash 与当前产品依赖对齐；仅对真实失效依赖定向复测，不全量复制已有通过运行。
2. 在唯一隔离 `round3` profile、**真实但获准的合成目标**上以最终 SHA 完成一次 R3-V2-01 规定的正式 Main→批准→成功→Noting→Snapshot/Proposal 的证据链，同一次观察F18/F19关键边界；失败原样留下，不用随机重复调用掩盖。
3. 由符合项目设定独立执行人／模型要求的第二次全范围 Verification 审查者，复用可溯源的有效开发证据并独立判断 V01–V60。只有所有范围内不符合/证据不足闭合，才交给独立 Validation；个人仓必须单独审查。
4. 不修改旧首次 `verification.md`、旧报告/原失败、不降低门禁、不复活旧工具，不对真实NM、用户profile、其它环境或Cloud做本次未授权操作。

## 6. 本次提交审计

- 代码目标为 `b40fa1ff2a771066b4da1d8978a7abe44327e530`；第一审查报告对应旧版 `323c64...` 不修改。
- 本次仅将第二次**静态复核的发现与限制**写入新文档，并在根 `CLAUDE.md` 登记。没有改测试、产品代码或规格。
- 实际运行状态：`NOT_RUN`（无本地/模型/命令运行），源代码：`REVIEWED_STATICALLY`，历史开发证据：`REPORTED_NOT_REPLAYED`，独立全量第二门禁：`INCOMPLETE`，总裁决：`NOT_PASS`。
