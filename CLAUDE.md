# Hermes Secretary 项目主看板

## 自主口径收敛 · 待用户追认

**Agent 自主工程细化／待用户追认：F16 Noting来源结算动作展开。** 白板E1已要求移除实际成功覆盖，但07 §8.11 Step4仅抽象写“Remove only successfully dispatched coverage”，真实模型只归档Candidate并给source加注记。决定将同一段明确为：对照实际批准／成功与现行版本，完整交付且无保护理由的来源归档，部分覆盖则精简已交付部分，保留具体新内容／未完责任／其它候选依赖，先修引用并说明保留理由。Astra已按原判据评审认可，不改变产品语义、权限或完成条件；已同步07与常量，真实round3复测待固定提交启动。用户尚未追认，不冒称用户指定措辞。原始d19018冻结与首失败证据保留。

## 第三轮自主实现 · 本地托管恢复（2026-10-17）

- 用户已授权：拉取全部远端分支；据本地环境调整计划并完整完成第三轮，优先派遣 C4。Verification 前高并行委派，主会话抓全局、review、集成，不重复执行子 Agent 有效测试。积极使用原生 DeepSeek 真实模型，token 消耗不设限制。
- 门禁：Verification 全新 Astra / high；Validation 文档与场景由主会话直接制定，6.1 / high 独立执行。原计划只到 Develop 的停止限制已被本次完整托管覆盖。
- 远端全部分支已 fetch 完成（含 upstream）；未集成官方上游新代码。云端 C1/C2/C3 已亲自审读核心实现并分别接入 `0e150cbce8` / `b41c549d4c` / `4022c5b`；这表示源码接收，不表示整链通过。
- 工作区：公开核心 `codex/round3-local-completion`；初始后端干净。前端既有 dirty 保留、UI 后置。个人 Provider 独立仓库；真实 NM 写入与云端部署未授权。两仓 Actions 已读回关闭；提交自动同步不代表验收。
- 实测约定（用户最新明确）：真实产品运行、DeepSeek复测、最终验收统一采用 `round3` 隔离 profile（`.hermes-dev/round3-runtime/profiles/round3`；L0 `run-native.py` 已固定此路径）；所有数据库在仓库 ignored 目录。单元测试仍按 runner 创建临时隔离状态；本地 Provider fixture 不连接真实 NM。原 L0 目录仅保留环境准备和证据，不能继续作为另一个实测 profile。
- 环境：官方 PM `.venv` Python 3.14.7、macOS arm64、现有锁不变；隔离目录 `.hermes-dev/round3-local-20261017-l0/`。DeepSeek 原生 custom/chat_completions 公共真实复测已完整交回并由主会话接收，实际阶段版本为f304b42／eff3235／f66a8；既有 Dashboard 保留。详见本轮 `local-environment.md`。

| 包 | 当前 owner／状态 | 独占验证与待办 |
|---|---|---|
| C1/C2/C3 | 主会话已 review 并接收云端实现 | C1 93、C2 69、C3 47独立场景已有有效证据；C2 `_search` 嵌套由C10-A修复 |
| C4 | 主会话已review接收；c4-report.md | 38场景取得通过；ruff、C4增量health通过；不把全范围C2阻断写成通过 |
| C5 | 主会话已review接收；c5-report.md | C1 93场景、C5 34场景有通过证据；三Schema和三Prompt与07静态逐字一致；时间秒精度单节点由原owner补证 |
| C6 | 主会话已review接收；c6-report.md | C3 47、C6 30独立场景有通过证据；原生append_messages_batch事务prepare_rows，先持久化后live，实际携带与成功响应ACK；正式caller交C9-S |
| C7 | 主会话已review接收；c7-report.md | 63独立场景有通过证据；正式manual/auto与成功boundary接线交C9-H |
| C8 | 主会话已review接收；c8-report.md | 59场景有通过证据；pointer核验/durable/live同事务与既有锁，完整正文与严格超限Proposal；C5时间秒精度1节点通过 |
| C9-H | 主会话已review接收；c9-host-report.md | 正式pre-summary唯一联合准备、原生成功发布事务更新interval、非空成功响应ACK、completed/failed归档gate；112独立场景有通过证据。review修正工具args业务校验不属投递ACK，23项定向复测通过 |
| C9-S | 主会话已review接收；c9-surface-report.md | 23路径指纹一致，112独立场景有通过证据；原始整批guard、退休名不fuzzy、可信catalog scope、独立Scheduler及完整claim、原生持久化prepare接线。无真实模型结论 |
| C10-A | 主会话已review接收；c10-notebook-history-report.md | 233独立场景有通过证据；C2嵌套修复、坏UID来源不可用、Snapshot时间ISO；保留旧有效保障，退出接口有处置映射 |
| C10-H | 主会话已review接收；c10-runtime-report.md | 62旧组场景＋4受影响Idle节点有通过证据；恢复deadline唯一local决定，提交gate仍检查。公共真实DeepSeek复测已交回，证据见real-model-report.md |
| C10-B | 主会话已review接收；c10-delivery-report.md | 十个旧测试文件106独立场景PASS，含九个CLI/TUI/Gateway SIGKILL边界；无生产修改，旧Notebook耦合退出。F08/F11/F12已review接收；c4接手最终回归静态清单，未执行大型检查 |
| C10-P | 主会话已review接收；个人8682ff8，c10-personal-report.md | 两旧测试39项PASS，canonical runner通过ignored源码链接避免错误包收集；无生产修改。正式host→本机fixture六场景已完成并review接收 |
| P1/P2/P3 | 主会话已review接收个人线并提交57d0abb854f4；personal-report.md | 46独立用例通过；真实SessionDB/MemoryManager+本地HTTP fixture，P2基本模拟通过；主会话已review，公共finalizer gate及历史旧测试已收口，真实host→fixture六场景已通过并review接收 |
| C10-T | 主会话已review接收；c10-final-legacy-report.md | 六旧文件及相关节点有效并集92 PASS；F10/F13、F11受影响旧组定向关闭，未启动独立门禁 |
| C11-P | 主会话已review接收；personal-host-report.md | 原生host→loopback fixture六场景、临时工具收窄及完整配置/插件备份恢复；公共f66a8f80／个人8682ff85实测；12 completed Turns／14请求／24真实UID与ACK；配置和插件恢复，round3已释放 |
| L0 | 环境已交回；yaml问题是个人脚本旧导入，P3 owner修复 | 不跑产品测试；不改锁或裸装依赖 |
| 门禁 | verification_astra（全新Astra/high）正在全范围初审；发现项已回到修复循环 | 初审固定公开323c64dacba1／个人e1af6cc45ffb；首审60项：56符合、2不符合、2证据不足，主会话已review接收；修后需全新独立全范围复审，Validation待通过 |
| F14 最终回归 | 首轮已完成；27个旧测试失败／错误已修复并由主会话review接收（含邻域共29）；压缩6原失败＋邻域共10已review接收；两失败检查已修复通过 | 1766 PASS／29 FAIL／4 setup ERROR／3平台skip；固定136文件等范围只执行一次，后续仅失败与影响路径定向复测 |
| F15 时间投影 | 公共六路径17项PASS，主会话已review接收；个人Recall8节点＋17子例已review接收；Scheduler run_at／绝对display共8项有效证据已review接收 | V51：仅人／模型可读Notebook投影为秒精度，覆盖工具、control、Main、slash、Proposal、Framework；内部精度不变 |
| F16 来源结算 | 主会话及Astra已评审具体Step4细化，c4已实施；待固定SHA真实补证 | V23：候选13已归档但来源6仍保留成功写入的完整经验；不能宣称完成结算，首样本失败保留 |

- 真实运行新发现 R3-F08：TUI Main streaming期间/noting反馈后，durable原文仍在但后续Active冻结缺输入／图片；修复已由主会话review接收：busy历史批次合并与cold human_only投影共28项PASS，ruff/health通过；eff3235真实busy图片六请求与cold回复／human_only隔离已通过，主会话接收。

- R3-F09真实Scheduler目录缺失已由主会话review接收单点catalog修复，正式TUI四开关及热关闭等6项PASS；eff3235真实bridge登记、投递与ACK已通过。C10-T六旧文件已收口，最终有效并集92项PASS；首轮60 PASS／17 FAIL／10 setup ERROR保留。R3-F10 External通知owner重读由主会话只补传现有ref，原失败及owner/suppression六项定向通过。F08b冷恢复human_only与正常回复合并已反证并修复；R3-F13原生/notebook误显Snapshot/anchor ID已修正，原CLI失败、human/model投影及Framework三项PASS。

- R3-F11／F12：真实原生成功压缩复用UID时漏记新interval；Force父尾为user时Noting任务被并入冻结消息。local_environment首包62项PASS；F11主会话review接收，C10-T另四项通过。F12首次review发现child时钟重做父历史清理，补四个真实native RED后回修；主会话已review接收累计74项有效证据并提交eff3235f6b；追加review确认preflight旧Anchor截断缺口，已补正式preflight RED并窄修，累计有效78项PASS；主会话接收；f66a8真实user尾七请求及两条五Turn链共31请求的完整前缀／root／tools一致，已核对真实forced提交与资源结束。

- eff3235真实定向复测首批：F08 busy图片+slash后child六请求前缀一致、F08b cold回复及human_only隔离；F09两deferred单carrier成功ACK、CRUD/instant idle；F11实际新boundary后Force再准入；F13 human/model视图区分已取得正证。忙碌instant已真实pending→下一Main单carrier→成功ACK；重启registry保持。F12及恢复已完整交回，11个child结束、未来排期零、配置原bytes恢复、原生host退出0。

- 公共真实模型开发证据已由主会话review接收，详见real-model-report.md；跨Turn两次受控probe真实执行五Turn forced，未取得“第二Turn正常finish”的特定模型形态；正常finish由自然链独立证明。受限合成USER成功不冒称多目标写失败；真实NM与部署仍未执行。C11-P已完整交回并review接收；round3配置hash恢复，插件恢复为原不存在，自有进程及lease归零。原生子进程退出码未独立记录，不宣称该码0；归档ACK完整。Verification正在进行；c4统一最终回归已完成：136文件＋server84筛选函数（展开90项）＋Provider46项canonical＋冻结10类检查一次，12次调用、311.402秒，详见regression-plan.md §7。八类检查通过，no-tmp／health两项有窄修补；主会话不重复有效测试。

- 初审整改：V51输出投影修复不降低内部时间精度；V23真实来源结算样本存在缺口，已与Astra按冻结成功范围结算要求研讨，先核对实际Prompt分支，再通过round3正式Main批准→实际成功→Noting语义结算补证。不得用SQL删除、伪造写成功或硬编码删来源替代。首失败保留，新增成功证据须同时证明已交付覆盖移除及未交付内容／责任／其他候选依赖保护。

<details>
<summary>云端规划时点记录（历史，状态以上方本地托管为准）</summary>

## 第三轮自主实现 · Planning已编制，等待按任务分发

**当前阶段：** `PLANNING_DOCUMENTED`。本次完成计划撰写和仓库文档同步；没有派遣实现、启动产品、执行测试、写NM或部署。不能把本文中的待执行包当作正在后台运行的任务。

**最新用户指令（2026-10-16）：** 接手第三轮计划，覆盖整个Develop直到独立Verification／Validation之前；尽可能详细、减少子对话与主会话重复验证、增加并行度。随后明确：多个独立网页Chat各自通过GitHub连接器创建分支、一次或多次多文件提交和PR，由本规划会话处理PR；完成可完成的云端代码修改之后，再回本地实际运行、测试及修复编码阶段未识别的问题。测试后置，不取消；本次不直接启动编码。

**唯一计划：** [.autonomous/20261016-round3-secretary-nm/plan.md](.autonomous/20261016-round3-secretary-nm/plan.md)。

**确认索引：** [snapshot-index.md](.autonomous/20261016-round3-secretary-nm/snapshot-index.md)，新增R3-012～R3-015覆盖先前“文档基线后暂停”的阶段口径，既有产品约束不变。历史冻结哈希仍见[baseline.txt](.autonomous/20261016-round3-secretary-nm/baseline.txt)，不改成规划提交哈希。

### 基线、范围与禁止项

| 项目 | 当前事实 |
|---|---|
| Secretary源码起点 | `a51fd99abc783f245ab855526a10862f2c89656a`；改版前代码 |
| Secretary需求冻结 | `d19018a7ba3e38ae01f76aa57821b55cbc15ff58` |
| 规划开始读取的main | `dec457e2393dc3e7401449b19b068bf7c65e5a07`，仅追加冻结哈希记录 |
| Provider冻结main | `97078118287bcd41ba8b02aa5a3a108c5026f7af`，源码仍来自`f9733fcb31a0e6f468eabe6419cb76444fe16b30` |
| 公开需求 | 已审Notebook白板＋07；旧01/02/04/06仅明确保留段 |
| 个人需求 | 独立Provider仓库PHASE3现行§1–7；历史附录不作为本轮并列依据 |
| 本轮产品范围 | Secretary改版与独立NM接入；UI、Settings展示、Web DTO及云端部署后置 |
| 本次实际变更 | 计划、索引和当前看板；原看板逐字保留为不可变文本快照 |
| 当前运行／测试 | `NOT_RUN`，没有本轮产品通过证据；旧报告不作为新版本通过 |

两仓源码／配置／运行数据库未因本次规划改变。未读取用户本地当前dirty状态；旧路径、端口、PID和前端未提交记录都不能当作本次现场核验。回本地前必须保护实际已有变更，不reset/clean，不部署。

### 已确认且不得重新扩张的产品边界

- 并发Noting保持现状：已提交A、B未提交时C可从A独立整理；不要求C继承B，不新增串行／合并／重跑机制，不以缺少B→C成果继承阻断验收。pointer通知仍须正确。
- 完成通知只由本次提交使有效Snapshot pointer切换产生；实际追加前再同事务／锁判定，失效整条丢弃，含完整正文及Proposal；完成时间不替代coverage。
- Noting仅四工具；finish独立批次，成功后固定工作视图，原生Turn返回才提交。五Turn／overflow兜底保留，child不再请求父compaction。
- Scheduler独立于Notebook／Noting；deferred继续原批量carrier、durable materialization、真实携带与成功响应ACK；完整Table未来24小时空档notice沿工具返回／原instant最终投递提供，不自动补排期。
- 个人Memory必须保存Hermes provenance。窄脚本官方CLI创建→真实ID→仅补Metadata，复用同一运行主机配置；不恢复旧完整HTTP正文写入体系。小脚本仅基本检查，不严格验收、不重测官方CLI、不做真实测试写入。
- Provider自动Thread归档真实NM写入尚未授权。普通Hermes试跑也可能经sync hook写Thread，本地必须先用隔离fixture端点。不得创建Space、改个人记录或治理；正式部署另行安排。
- 不做旧数据／配置迁移；不删除旧消息调用历史；新执行面不保留旧名alias。不把旧UI要求拉回本轮；公开核心不能依赖个人Provider成功。

### 执行顺序与分支策略

```text
独立Chat代码与测试源码 → 本会话PR静态review/merge
→ CODE_INTEGRATED_UNRUN（双仓SHA，仍未运行）
→ 本地LOCAL_RUN/LOCAL_REPAIR（首次测试、接线运行、定向修复）
→ DEVELOP_READY_FOR_VERIFICATION → 停止
```

首次发包前由本会话建立两仓`round3/develop`，分别从含本计划的公开main和已核对Provider基线创建；当前尚未创建。任务各自`round3/<id>-<topic>`，PR base为本仓集成分支。本会话唯一合并者，执行对话不改main／集成分支、不合自己的PR。未经运行／独立门禁不作发布判断。

云端不安装、不运行、不lint/compile/typecheck、不启动模型和产品；可编写测试源码，统一NOT_RUN。静态发现的错误当场修。PR接收表示源码已审，不是测试／独立验证通过。后续本地保留canonical runner与冻结规则，不为每任务或每PR重复跑大套件。

### 当前任务看板（所有任务尚未派遣）

下表是唯一动态编排看板；plan中的任务卡保持静态。以后在本表填实际owner/branch/PR/head和状态，不新建分区看板。

| 任务 | 工作线 | 修改启动依赖 | 当前状态／实际PR |
|---|---|---|---|
| D0 | 两仓集成分支、运行触发设置、发包SHA | 用户开始分发 | 未执行 |
| C1 | Notebook模型／版本／Snapshot | D0 | 未派遣 |
| C2 | Conversation History／候选流 | D0 | 未派遣 |
| C3 | 独立Scheduler控制面 | D0 | 未派遣 |
| C4 | 配置／Main Prompt／Slash | D0 | 未派遣 |
| P1 | Provider资格／Bundle／Recall | D0 | 未派遣 |
| P2 | provenance窄脚本 | D0 | 未派遣 |
| C5 | child／四工具／结束续跑 | C1；合并前C2/C4 | 未派遣 |
| C6 | 投递／在途竞争／ACK | C3；合并前C4 | 未派遣 |
| C7 | 联合触发／Force区间 | C4；合并前C5 | 未派遣 |
| C8 | pointer／Framework／完整快照 | C1/C4 | 未派遣 |
| P3 | Thread归档／收据／个人接线代码 | P1；合并前P2 | 未派遣 |
| C9 | 公共正式dispatch／host接线 | C1～C8 | 未派遣 |
| C10 | 本会话源码收口／遗留测试调整 | C9/P3 | 未执行 |
| L0/L-A/L-B/L-C | 本地环境／分组首次运行 | CODE_INTEGRATED_UNRUN，回到本地 | 未执行 |
| LOCAL_REPAIR | 真实失败归因及定向修复 | 有实际失败证据 | 未执行 |
| Verification／Validation | 独立门禁 | Develop完成后另行启动 | 本次不进入 |

首批六个任务可并行；依赖满足就接力，不等整波结束。共享文件顺序交接：C1→C8的Snapshot事务、C3→C6的Schedule接纳、P1→P3的Provider归档。全局facade／dispatch由C9集中写。准确白名单、精读范围、实现步骤、后置测试与启动文本见plan，不在此重复。

### 本会话处理PR的责任

亲自读取完整patch和关键调用者；核对白名单、冻结契约、实际接口及未实现项；一次性交回具体修改意见。只因未运行不拒绝云端源码接收；有实质源码缺口／依赖未合并不能标完成。以expected_head_sha合并，确认真实merge结果后更新本看板；不把功能分支tree覆盖集成tree，不强推。后置本地证据有效时直接复用，不为主对话接收报告再跑测试。

### 启动前操作风险

1. Provider冻结看板记录Actions当时enabled；第一次代码push／PR前必须核对实际设置，确保不会违背用户测试后置。`[skip ci]`不保证所有触发事件均不运行，不能当唯一措施；本次不改Provider设置或工作流。
2. GitHub连接器能读写不表示拥有Hermes实际运行环境。云端只做内容和静态审查，不声称compile／测试通过。
3. 本轮源码更改较大，模块PR之间可能暂有待C9替换的旧调用点；待运行开发集成区不得当生产版本使用，C10必须在回本地前完成可静态识别的接线收口。
4. 真实NM服务写入授权与本地fixture证据分开记录；不能省略个人线，也不能把未授权写入变成自动执行。

### 历史原文与冻结事实保留

规划前完整根看板原文逐字保存在[CLAUDE.before-planning.txt](.autonomous/20261016-round3-secretary-nm/snapshots/CLAUDE.before-planning.txt)，其Git blob与`dec457e...:CLAUDE.md`相同。它是只读历史证据，不是第二动态看板；内含的相对路径按原仓库根解释。第二轮与10-15所有历史结论、未提交工作记录和报告版本未被改写；恢复第三轮以本页当前区域、plan和冻结索引为准，非必要不重读历史。

稳定产品入口仍由README维护，通用规则仍由AGENTS维护；本次没有改动两者或冻结白板／07／PHASE3，没有以规划状态改写“已实现”或“已验收”。

</details>
