# C-U20／F07／E02 实现交回

## 1. 对应条款与交付版本

- 依据本轮 `plan.md` 顶部“C-U20正式接线设计”8条、07顶部2026-10-28用户契约、Snapshot Index U20，以及原云端报告F07／E02；U20覆盖旧Idle串行时序，未改变其它Notebook语义或原生FM机制。
- 本包恢复前身未提交变更继续实施；未创建新方案、未重启自主轮次。当前产品仍是**未提交的可审diff**，提交／整轮审查／发布由root负责。
- 最终定向测试源码基于HEAD `e75321125f0194368cea9321cca9776f0188de8e` 加本包diff；HEAD相对`a5018ffd8206f54019f29f6bbb2c5edf641384bd`仅追加root文档提交。38份源码／测试的精确SHA在 `.hermes-dev/incremental-sync-20261027/r2-joint-noting/delivery-source-sha256.json`，收尾已逐份复核无变化。
- 收到root的U24通知：本地独立Verifier由root在全轮集成及BE／FE锁定后派遣；本报告不宣称独立门禁通过。

## 2. 实际变更

- 保留旧`secretary_noting_admissions`的原schema／UNIQUE和旧children；新增Secretary自有`secretary_noting_attempts`引用原Anchor记录，使用独立整数handle；统一只读views兼容旧历史归属。普通取消可同Anchor重试；旧表／Snapshot初始化与重复初始化保全有真实SQLite证据。
- 普通手动／Idle／原生自动压缩在安全准入后的同一native pre-summary接缝启动Noting；Idle直接请求同一native路径，不等待整理正常提交。operation_id来自真实compression registration／fence，不从holder字符串或Conversation猜关联。
- Snapshot提交资格与native取消在同一SQLite写事务竞争。已提交保留；未提交取消终态清理。新准入先原子撤销旧普通任务资格并写终态，再在工具锁下冻结已有工作为`superseded`审计；迟到工具、模型结果与提交均失效。pointer、Main读取、Noting初始化、branch继承、Note选择和显式debug recovery排除该审计。
- Force只由真实Main结束hook检查，移除preflight两处及Idle超线改派旁路；沿原生usage anchor及原公式计入Turn尾。现有Framework短锁与persist锁按Framework→persist顺序覆盖结束检查、冻结、准入、child启动与稳定FM提示，阻止下一Turn开始穿过这段边界。提示拒绝／线程启动失败均明确终态，未伪发请求；Force在飞／已提交都不被Compact取消，区间占用只由真实成功压缩解除。
- 快照提交与Note投递独立。任务完成立即终态并释放presence／child／completion；不靠FM carrier维持运行。已准入任务后续仍复核全局／本地开关、任务资格和合法来源，不依赖父runtime句柄、当前父能力、空闲或压缩完成。显式recovery也移除提交前Main lease等待；其失败通知仅即时尝试原生发布资格。
- Note按Full Foreground合法来源位置和成功边界选择，忽略墙钟提交先后及全局pointer遮挡；当前区间自己的Note不注入本区间，仅等待最新相关来源的在飞任务。提交、压缩发布、attach及下一请求前共享同一selector；仍走既有push FM与Turn间隙接入。实际row与目标interval／snapshot回执同事务，排队时重新核资格，append失败不记成功。
- Gateway TTL／LRU／pressure与实际soft release共用精确维护owner保护；已有timer→child／native handoff不断档，软回收与冻结在现有owner锁确定先后。终态释放，关闭开关回收跨due清退旧周期，暂时owner失效保留due；重启后无活跃presence的过期attempt写明确abandoned终态。
- 接续中修复了原API允许的运行中child重绑定被新表过严拒绝的兼容退化；仍拒绝已退休任务恢复执行资格。新增字段／参数保持可选及默认兼容。

## 3. 正式路径与接口

- native facade／summary：`compression_facade` → `conversation_compression._run_summary_phase` → `prepare_noting_for_native_compression(commit_fence=...)` → `prepare_joint_noting` → existing `spawn_noting_task`／真实Noting Loop。
- Idle：原timer／catch-up → `request_idle_joint` → existing `request_parent_compaction` → 同一native summary接缝；不新增执行器、scheduler、mailbox或Loop。
- 取消：`compression_read.cancel_compression` → 精确operation CAS → `retire_invalid_tasks`；失败／no-op也在facade settlement收口；成功边界唤醒统一Note检查。
- 提交：六工具工作锁与运行资格 → existing `commit_noting_snapshot` → Notebook完整状态校验／snapshot写入＋attempt提交事实／原child所有权关联；native父busy／句柄不作为提交门槛。
- Note：`check_note_delivery` → `select_note_conn` → existing `publish_framework_message` → `append_runtime_row`同事务重选／row／receipt；保既有busy排队与Turn间隙flush。
- Gateway：三个真实cache sweep／cap选择及soft release → `claim_cache_release`，非只验证`holds_maintenance`返回值。
- 未触碰D的`turn_final_response`／`run_turn_runner`／`stream_consumer_messages`，未碰A-BE writer／recovery_view或前端。Force现有Main结束hook接线已在原链，未扩展D修改范围。

## 4. 验证结果与原始证据

证据目录统一为 `.hermes-dev/incremental-sync-20261027/r2-joint-noting/`；Mac arm64、项目官方PM环境Python 3.14.7；模型／summary返回和屏障受控，真实SQLite、原生compression fence／publication、Noting Loop、FM事务、跨进程状态读与Gateway cache均实际执行，无真实Provider请求。

- **最终一致源码：11文件180项通过，0失败，33.3秒。** 日志`delivery-tests.log`。覆盖普通三入口两种完成顺序、真正写事务cancel／commit双时序、同Anchor重试、替代审计及迟到结果、Force结束／下一Turn竞态、在飞Force抗Compact取消／成功解封、Notice／worker失败、两边界／排队重选／append回滚／重启去重、跨Profile、旧库保全、父句柄失效仍提交、recovery独立提交、任务终态／presence跨进程观测及三类Gateway完整维护阶段。
- 命令：`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh -j 6 --file-retries 0` 后接 `tests/secretary/test_joint_noting_{u20,force_owner_u20,notes_u20,races_u20}.py`、`test_noting_runtime.py`、`test_noting_task_settlement.py`、`test_noting_child.py`、`test_noting_recovery.py`、`test_noting_task_presence.py`、`tests/hermes_state/test_secretary_noting.py`、`test_framework_message_boundaries.py`，选择器为`-k 'not eligible_main'`。实际runner完整路径列表在原日志开头；这里花括号仅缩写说明。
- 上述选择器排除Framework中12个已确认基线失败的U17元数据场景，同时因名称匹配排除3个合法测试。3个`untrusted_timestamp`另以同官方runner定向补验，**3项通过**，日志`delivery-untrusted-timestamp.log`；不把名称过滤掩盖为全文件通过。
- **最终10项冻结检查通过，health 0 blocking／0 advisory。** `delivery-quality.log`；独立临时Git index，不改root暂存区。命令`.venv/bin/python scripts/check --staged --base a5018ffd8206 --only footguns,shebangs,no-tmp,config-writers,os-marker-fakes,case-collisions,lazy-deps,profile-archives,ruff,health`。临时index收录本包源码和root已修的历史报告no-tmp说明；未改规则／阈值／等级／例外。
- 前身`combined-first.log`的6文件136通过、2个Linux限定skip保留原事实；Gateway普通原生68项回归证据沿用。后续只因接线修补定向复测，没有复跑无关全库大套。
- 过程反例／修复日志保留：`resume-regression.log`、`resume-boundary-regression.log`等；不覆盖首次失败。最终源码manifest和原始日志哈希在`delivery-evidence-sha256.json`。

## 5. 缺口与边界

- 本包未做UI、真实模型、部署或真实微信外发；这些不在子Agent授权内。Linux限定两项未在Mac伪造执行，原生压缩／真实Provider行为仍由root安排适用整轮验收。
- 干净导出的`a5018ffd8206f54019f29f6bbb2c5edf641384bd`实跑证明：`test_context_compaction_request.py`原有4个历史反例失败、`test_secretary_notebook.py`branch旧来源字段断言1项失败，在未含本包时已存在。基线命令同官方runner、`-j 2 --file-retries 0`两文件；证据`head-baseline-tests.log`／`head-baseline-revision.txt`。没有把这些基线失败归咎U20或为通过改实现／断言。
- 同一干净基线另跑recovery／Framework／presence三文件：recovery22及presence7通过；Framework12项因U17新增`turn_source`与旧“display_metadata必须空”断言冲突而失败。证据`head-baseline-boundaries.log`。本包只调整其U20触发／下一边界准备，保留这12项历史断言交root按U17范围处理。
- 未执行全部Secretary历史分区；仍以旧串行前提命名和组织的`test_idle_noting_reuse.py`、`test_idle_noting_commit_order.py`及部分timer／TUI历史用例，不能凭本包新矩阵冒称旧全套通过。其旧时序与U20冲突时须先按最新契约审判据，不能把“等正常Noting再压缩／FM等完child才终态”重新加回产品。新正式时序的开发证据集中于本包U20矩阵和已更新的独立终态／recovery／presence测试。
- 这份报告为实现交回，不宣称全轮完成、Verification或Validation通过；root需亲审diff和范围、固定候选后执行U24门禁。

## 6. 接口影响

- 原admissions／children和原schema保持，新增companion表／只读view／Secretary Note回执表；未迁移／重建生产数据库。
- `prepare_noting_for_native_compression`增加可选`commit_fence`、`prepare_joint_noting`可选`operation_id`、`spawn_noting_task`可选`start_gate`，均有默认值；不改变普通原生调用必填参数。
- admission整数handle保持不透明，调用者不得假定正值或固定1；历史正整数与新独立attempt整数通过views读兼容。状态增加cancelled／superseded／abandoned等Secretary自有事实，不写原生会话状态。
- 未改变六工具Schema、Prompt、预算、阈值、Provider路由、原FM通用投递、API hierarchy或Main admission规则。

## 7. 建议后续动作

1. root按8条设计亲审本包未提交diff，重点复核Framework→persist锁序、companion旧库保全、独立提交与Note事务回执，以及D结束hook的正式链。
2. 先明确17项已证基线失败及旧串行测试判据的整轮处置范围，避免把历史断言当新产品要求；不用修改冻结检查来消除失败。
3. 集成锁定BE／FE SHA后统一派U24独立Verification及Validation；本包日志／SHA可直接复用，不按包开启门禁或重复当前有效全套。后续main／发布／0.1.9 APK由root按U23安排。

## 主会话亲审补记：A／B／Note回执／C-R4（2026-10-28）

上文保留首交回时点与原始证据。本补记为root亲审后指定的窄修；当前源码以`review-final-source-sha256.json`为准，仍未提交／部署，未派生或启动独立门禁。

### 1. 条款与root指定方案

- A：Force必须观察真实native Turn lease边界；受理后才started，模型及原生／relay收尾后、释放lease前，在同一Framework→persist短临界区完成结束事实、测量、准入和提示。
- B：旧／新admission依据实际所属行分派注册／finish；初始化不改旧事实，后续合法生命周期与死亡清理兼容新旧，不按整数正负猜归属，不迁移所有旧admission。
- Note回执：root明确幂等对象为目标成功压缩区间。B1已注入的S1在后继B2仍是最近有效Snapshot时，应在B2后再有一次完整Note；保每interval一次，移除跨interval全局snapshot去重。
- C-R4：Note专属资格读取／live adoption为best effort；不能将已真实成功的native publication变为异常返回，也不吞原生压缩本身异常。

### 2. 反例与实际修补

- **A真实反例：** 原`run_conversation`在native admission前调用started，结束观察又落在`lease.release()`之后。SDK真实返回、SQLite真实lease和后继请求在lease处等待的屏障证明：旧Turn尚未释放时，等待者已改写`last_turn_started_at`；未受理早退也重写了Idle周期。
- **A修补：** `agent/turn_facade.py`仅在实际受理lease之后调用Secretary started；结束先完成refresher stop／join／clear、旧activity／relay_pending清理，再调用ended并最终release。`note_main_turn_finished`以现有conversation timer锁→Framework→persist短区段包住markfalse、含Turn尾的原生测量、Force准入／提示；不锁跨SDK／Provider／child执行，不新增Main gate。
- **A附带真实pending反例：** 后继请求在旧SDK仍阻塞时进入lease等待，提前写入的`_relay_pending_turn_id`会让Force FM错过真实Turn间隙，下一SDK请求看不到提示。该标签改在受理后才写入同一个既有relay ID；未受理请求不占用运行标签。实际下一模型请求已含正式提示，旧Turn结束不再清掉新Turn的running。关闭／非Main仍走原生SDK，无Noting准入或FM。
- **B真实反例：** 真实旧schema／原children初始化保全后，旧正／负整数id均可读，但新register路径误把legacy `running`当作无资格，并且仅扫attempts使旧dead-running不终态。
- **B修补：** registry首先查attempt实际行，找不到时按旧admission／children事实沿原SQL合法rebind／finish；旧rebind仍只改身份／profile，保registered_at、终态和finished_at。新attempt handle分配避开两表已有整数，合法legacy `-1`也不会与新attempt重名。attach清理从统一view查未终态执行，精确核同DB active worker／Secretary presence／真实native lease；失效且过期才依法写abandoned。旧记录仅在后续生命周期发生时更新，不在初始化回写，不改有效Snapshot或Force区间占用。
- **Note回执真实反例：** 同一个真实native runtime连续两次成功压缩；S1的第一次FM已实际落库，第二次没有新有效Noting（同Anchor正式准入跳过）。旧全局UNIQUE／selector使第二个区间没有Note，反例`len(receipts)==2`改前失败。
- **Note回执修补：** 移除新自有表的`UNIQUE(conversation_ref,snapshot_id)`和selector全局snapshot已投递拦截；仅保`PRIMARY KEY(conversation_ref,interval_id)`。完整保留合法来源位置、本区间自身排除、最新相关pending等待及真实append事务重选；不引入mailbox。该新表未部署生产；测试均用新建开发库，没有迁移生产表。
- **C-R4真实反例：** 只在成功压缩边界已durable后令Note selector抛OSError，native原已成功写入却异常返回。现`adopt_native_publication`只围住Note专属adoption增量，记录异常并返回，原native result／commit／镜像保持；无伪receipt，下一正常检查可补偿。原生summary本身抛错仍原样传播，未变成成功。

### 3. 正式接线

`run_conversation` → 实际`admit_durable_turn_lease`成功 → `observe_admitted_turn_started` → 原生SDK／Loop／native与relay收尾 → `_finish_native_lease` → `observe_admitted_turn_finished` → 原子结束／Force观察 → 原`lease.release`。

旧registry和新attempts共用既有mixins的register／finish API；`bind_main_runtime`既有attach调用统一过期执行清理。Note仍沿原`publish_framework_message`推送和`append_runtime_row`事务，不改通用FM投递。

### 4. 当前版本验证

- **最终精确源码5文件46项通过，0失败，11.6秒。** 原始日志`review-final-tests.log`。执行：`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh -j 4 --file-retries 0 tests/secretary/test_joint_noting_native_turn_u20.py tests/secretary/test_joint_noting_legacy_u20.py tests/secretary/test_joint_noting_u20.py tests/secretary/test_joint_noting_notes_u20.py tests/agent/test_turn_facade_lease.py`。
- 其中native真实SDK／lease 6项包含：释放前后并发交接、SDK尚在飞时后继等待与提示进入下一请求、未受理早退、已受理后relay准备失败、global off／非Main；legacy 11项包含实际旧初始化保全、正／负id合法API、native lease／presence有效时保护及过期后重新attach明确终态、已提交快照保全、Force占用与Conversation／Profile隔离；其余覆盖真实双边界、冷重开／重复attach去重、队列跨边界重选、append回滚和Note读错／原生错误边界。
- 改前真实失败保留`review-abc-before.log`、`review-b-before.log`、`review-a-pending-before.log`、`review-r4-before.log`。首轮legacy夹具另有SQL占位数及只读连接调用写入型interval getter的问题，后续已纠正；这些夹具错误不作为产品缺陷证据。有效产品反例为legacy rebind／过期running、native两个生命周期反例、跨边界receipt及R4；未覆盖原始失败日志。
- `review-extra-boundaries.log`的原生异常测试曾误预期observer必须是error；正式native异常cleanup会撤销fence并标cancelled，原始RuntimeError仍传播。仅纠正这项测试判据，未改原生实现，`review-extra-boundaries-final.log`及最终46项已证。
- **最终冻结10检查通过，health 42文件0 blocking／0 advisory**，日志`review-final-quality.log`；命令与上文检查相同，独立临时index，无规则／阈值／等级变更。`git diff --check`通过。
- 本次没有重跑原180项大套；旧有效证据保持原时点，新增／受影响接缝定向验证。42份当前源码SHA在`review-final-source-sha256.json`；补记证据哈希在`review-evidence-sha256.json`。

### 5. 缺口

未执行真实模型、UI、Linux限定项、生产／外发或全分区大套；原17项已证基线失败及历史串行测试范围仍按上文处理。本次不宣称独立Verification／Validation通过。A的改动只把现有事实观察和relay运行标签接到实际native admission／release，不新增租约、Main admission gate或跨Turn锁。

### 6. 接口影响

新增内部`secretary/noting_turn_boundary.py`隔离原生lease受理观察；原`note_main_turn_started/finished`调用签名保持。新增的native cleanup helper只复用原refresher／label／release方法。旧register／finish恢复原有合法契约，新表仍以实际行分派；schema变更只作用尚未部署的Secretary Note回执表，旧admissions／children schema与初始化数据保持。

### 7. 交回建议

root继续亲审A／B／Note／R4的实际diff及42份源码manifest，重点核正式lease锁序、等待者不能抢先写running／pending、旧终态保留和同interval事务幂等。接收后统一固定BE／FE版本再按U24派全轮门禁；本包没有自行commit／push／派生／部署或扩大发布范围。

## main历史纳入的四文件冲突交回（2026-10-28）

root已提交C为`27c74b094f`；本次仅处理其发起的`origin/main`历史merge：当前HEAD `0ca4a3ef3fe7e4a0d84cb58b3d020ad2f1653876`，MERGE_HEAD `5fc54fc233a0379321c13c22494923e06f302dad`。仅四个源码文件共10个hunk，未提交／push。README／AGENTS／CLAUDE保持root按SOP恢复后的HEAD内容。

完整保存stage1／2／3、`0a5d09cdcf`原始逐文件补丁、incoming→C差异及决策于ignored `.hermes-dev/incremental-sync-20261027/r2-joint-noting/merge-u16/`。已核四个stage3文件均与`0a5d09cdcf`相应文件**逐字一致**；并逐hunk审视原U16目标与最新U20接线，不使用整文件ours命令。

| 冲突 | 保留及替代依据 |
|---|---|
| noting_child H1：`frozen_work` | 保留C新增字段，供异步child尚未构造时的替代审计保存合法基础；U16原准确owner／epoch／request字段全部保留。 |
| noting_child H2：`_end_completion` | 保留C立即终态释放与同registry精确handle关闭。main旧等待native／FM结算的child生命周期已由U20明确替换；活跃native资源改由当前owner的fence／request及cache release原子保护，不重新使已结束child等待FM。 |
| noting_runtime H1：Force dispatch | 保留C稳定admission身份、start_gate和提示失败明确终态，替代旧“提示失败仅日志、child继续”的分离状态；仍走原push FM。 |
| noting_runtime H2：prepare／Idle接缝 | 保留C `operation_id`和`request_idle_joint`。该sibling在persist锁内继续核准确实例、epoch、DB/ref、当前route、archive、开关和可冻结前缀，再消费due／请求原生压缩；native pre-summary才冻结并准入child。原U16关闭／替换先后关系与缺前缀保due目标均保留，旧串行callback由U20并行机制替换。 |
| noting_runtime H3：source／callback | 保留独立任务提交，不恢复`after_normal_commit`串行压缩。原生／External来源事实仍在；owner bind位于合法wrapper及attach，保C的Framework→persist锁序，不能把bind／Note检查重新移回反序锁区。 |
| noting_runtime H4：trigger参数 | 保留可选`operation_id`，对应真实native registration的联合取消身份；`expected_period/expected_owner`沿Idle sibling完整传递。 |
| noting_runtime H5：native_idle映射 | 保留内部`native_idle`→持久kind `idle`及operation关联，兼容原schema枚举，不恢复无关联的旧准入。 |
| noting_scope H1：attach尾部 | 保留准确weak runtime绑定后的dead-task清理与统一Note检查。main原closed判断、registry RLock、DB/ref绑定及实例相等判断原样在；不因合并而删除U20四时点中的恢复检查。 |
| noting_timers H1：policy早退 | 保留C对已受理工作的资源保护：待触发timer仍由原`refresh_maintenance`、`entry.valid`及准确owner限制；已在飞child／native资源不能因为Idle开关切换而提前回收，终态会释放。不能恢复main对所有维护资源统一以Idle policy短路的旧前提。 |
| noting_timers H2：native保护 | 保留当前准确owner的活跃fence／request保护，后者核epoch、DB、Conversation、完成状态；原pending timer／completion owner检查均保留，覆盖同步冻结→真实native工作交接。 |

额外核对：U16的`_begin_completion`、`holds_parent_completion`、`_same_completion`、`_reuse_committed_completion`、`_matching_native_request`，timer准确实例／epoch／period、cancel旧owner不伤新owner、firing到冻结不断档、start失败释放、attach补偿，以及scope准确绑定，共20个相关函数在incoming与C中逐字一致。`_run_idle_event`仅说明文字变为U20时序，去docstring后AST一致，原`expected_owner`传播完整。`request_idle_joint`、`claim_cache_release`、原生close接缝与TUI/Gateway实际维护调用另已亲读；旧串行reuse helper不再是新Idle正式入口，不能以恢复其等待条件覆盖U20。

**零差异证明：** 逐hunk生成候选后，四文件均与HEAD逐字一致，已仅`git add`这四文件；无unmerged条目。非白名单index条目在操作前后逐字不变。全部index tree与HEAD tree同为`4b98595279d1afe786d6e830876d15f65fcf8b12`，`git diff --cached HEAD`为空；四文件源码SHA见`merge-u16/resolution.json`。报告补记仅留在工作区未暂存；其它文件未改。merge仍由root掌握，未commit或abort。

因实际源码／依赖／冻结检查入口均未变化，本次不重跑测试或健康大套，复用27c74b094f已审46项及十检查有效证据；不宣称新增测试通过。`git diff --check`及四文件AST解析通过。root可继续最终merge审查与提交，当前无源码整改或冲突遗留。
