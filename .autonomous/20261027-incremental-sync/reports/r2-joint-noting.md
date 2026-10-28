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

## 显式恢复来源区间只读窄查（2026-10-29，产品未改）

root提出的来源关联疑点已取得**正式入口真实反例**：存在合法当前区间失败Task，经`secretary.noting_recover` RPC恢复后，同区间错误注入完整Note。不是单凭`admission_id=None`的静态推断。另一个superseded半成品对照场景通过，未发现其进入恢复基础或模型输入。本次只写ignored隔离证据及本报告；没有改产品／现有tests／其它文档，没有提交／部署／UI／真实模型，也不代替整轮Verifier。

### 触发与实际结果

1. 在关闭Noting时，通过真实native `_compress_context`成功生成边界B1；该原生路径保留默认tail。随后开启Noting；此时尾部的合法m9 UID仍沿原始来源保留，当前Full Foreground将其展示在B1之后。
2. 发起下一次真实手动native Compact，其pre-summary正式准入普通Noting，实际冻结Anchor为**m9**，admission的`compression_interval_id=compaction:S17:11`，等于当前B1区间。没有手填Anchor／admission／区间。Noting用真实工具创建合法工作态后，受控SDK返回不可重试400，任务明确failed；待该终态已写，再令受控summary抛错，第二次Compact不提交新边界。当前区间仍B1，原Task保持failed、snapshot_id为空，并非cancelled／superseded，所以显式恢复合法。
3. 通过实际`server.handle_request`的`secretary.noting_recover`路由、目标Profile DB和正式`_run_recovery`／Noting Loop恢复该失败child。只控制SDK响应及host构造凭据依赖，未替换准入、恢复重建、提交、Note selector或FM写入。恢复提交成功，保留了先前合法工作内容。
4. **实际观察：** 恢复Snapshot `snap_54fbbea62bbd4163920f4f66492a857e`被写入B1的Note receipt，目标`interval_id=compaction:S17:11`与原Task所属区间完全相同；对应完整Notebook FM真实落库，carrier UID `78af6ce8265f4e5a9cf70f1b7702dd10`。恢复Snapshot在`secretary_noting_task_admissions`里没有任何snapshot关联行；原admission仍failed／snapshot_id为空。违例发生在真实发布，而非仅helper返回候选。

原始JSON的Full路径末尾为B1(id11,path_position8)、m10(id12,path_position9)、m9(id13,path_position10)；正式selector的原始来源位置却是m9 `(8,0)`、B1 `(10,0)`。这使carried旧UID仍满足来源在边界前的必要条件；对普通任务，所属区间关联会再排除“本区间自己的Snapshot”。显式recovery没有该关联，因而漏过第二层资格。

### 根因与修补所需事实（不自行定方案）

- `run_noting_task`在`noting_child.py:853`有意不把显式recovery写成原失败admission的普通执行。`commit_noting_snapshot`仍正常写Snapshot，但`noting_joint.record_commit`对None不建立attempt→Snapshot关联；这本身服务于“恢复独立owner、原失败注册不重绑定”的既有契约，不能简单将原failed admission恢复成admitted／committed来修。
- `_parent_rows`确实按原admission的真实`compression_interval_id`和child首条消息horizon分段、截至合法Anchor；本例恢复前缀正确来自B1区间，并未错误读入别的压缩代。这个来源分段不等于Note投递的区间资格记录。
- `select_note_conn`在`noting_notes.py:42`起只从`secretary_noting_task_admissions.snapshot_id`查所属区间。`_run_recovery`虽在recovery Session的`model_config._noting_recovery`写了原`admission_id`和最终`committed/snapshot_id`（`noting_recovery.py:228`），selector没有消费该持久事实，故恢复结果漏掉当前区间排除。
- root设计最小修补时需要保留：恢复Snapshot的原来源区间可追溯；原失败Task／child记录不改写、不假装重新准入；新旧压缩边界上的合法晚到结果仍可进入后继区间；同区间不得因缺少普通attempt关联而回注。现有recovery audit包含原admission及最终snapshot事实，可供方案评估；是否复用它或在提交同事务记录独立来源关联，由root决定。本次不新增schema、gate、mailbox或选择算法。
- 不能仅把carried UID一律改按最新物理行排序来掩盖缺口；原覆盖／晚到与本区间排除是两个独立判据，必须同时保留。

### superseded半成品对照

真实第一任务已生成工作项`Audit-only partial work`，其SDK在飞时由新的真实native准入替代，留下`termination=superseded`审计；新任务从上一有效Notebook（此例为空）开始后也受控失败。正式RPC恢复旧superseded child立即返回4002 `A retired Noting task is audit-only and cannot be recovered`，零新增SDK请求。新failed child可正常显式恢复，其`base_snapshot_id=None`、重建工作态为空、最终Snapshot为空；实际恢复SDK请求中没有旧审计文字。与`reconstruct_noting`先拒绝superseded／cancelled、`_base_snapshot`跳过superseded及`NotebookStore`拒绝审计base的源码一致。本次不据此扩大宣称所有恢复竞态已证明安全。

### 版本、命令与证据

- 读取开始时HEAD cbbd7e45aa；隔离取证固定的HEAD为`8fcbd7aa844acf3d3aa214bbb9f5cb4f1516a89f`。已核两者间本次9个相关产品文件无diff；它们与源码副本SHA在运行后也完全一致。
- 所有产物在ignored `.hermes-dev/incremental-sync-20261027/r2-joint-noting/recovery-source-review/`：完整反例`test_recovery_source_review.py`、产品及fixture源码`.source`、`source-sha256.json`、两份`*-observation.json`、`summary.json`及`evidence-sha256.json`。
- 官方runner最终执行：`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh -j 1 --file-retries 0 .hermes-dev/incremental-sync-20261027/r2-joint-noting/recovery-source-review/test_recovery_source_review.py`，**1个预期契约反例失败、1个审计排除对照通过**，日志`final-with-wire.log`，约3秒。失败断言要求本区间无Note，实际却存在真实receipt与FM，产品尚未修复。没有运行180项或其它大套。
- `first-run.log`第一次误预期实际Anchor为m10，真实native准入实际选择m9；已只修正ignored夹具为读取正式admission的Anchor，不作为产品缺陷计数。原日志及后续`same-interval-run.log`、`final-run.log`全部保留；最终反例不再假设Anchor。

结论交root：**当前区间显式recovery Note来源关联是真缺口，需设计并实施后再定向复验；superseded审计排除在本次正式对照链上成立。** 现有隔离反例可由root移入后继正式测试或用于修后证据，本次未改任何产品或现有tests。

## C-R5显式恢复来源补齐与branch兼容（2026-10-29，待root亲审，未提交）

### 1. 对应条款与授权

落实07顶部U20“本区间自己的Note不得注回本区间”、plan正式接线第5／6条，以及root亲审C-R5指定方案。显式recovery仍为独立child／owner，原failed admission及child不重绑定、不改成admitted／committed。root另明确授权`hermes_state_secretary_notebook.py`的Snapshot提交内部可选参数及branch复制时剥除内部来源关联；其余范围不扩大。C-R6在飞候选问题另列，未混作本次已修。

### 2. 实际变更

- `secretary/noting_child.py`：从已核的恢复runner admission传递独立`origin_admission_id`，不改变普通`admission_id` CAS／record_commit。写事务内以`db.noting_admission_conn`查实际所属行，核Conversation／Anchor及非cancelled／superseded，由`noting_note_sources.recovery_origin_conn`构造来源；原failed记录完全保留。
- `hermes_state_secretary_notebook.py`：`notebook_commit_snapshot_result_conn(..., noting_origin=None)`仅增内部可选参数。严格`_termination_json`仍原样只允许模型／工具的type／reason；小helper在验证后构造副本，仅recovery将`noting_origin={admission_id,compression_interval_id}`随Snapshot同一INSERT耐久。没有INSERT后UPDATE，不等待recovery Session事后patch；Snapshot与pointer／items任一失败仍由原事务完整回滚。默认None序列化结果保持原样。
- `secretary/noting_note_sources.py`：一次Conversation限定的元数据查询统一读取普通admission关联、新Snapshot内部origin和既有committed recovery Session witness。旧形状只读，不改旧Snapshot／admission／child；核实际ref、snapshot、Anchor、原admission、failed-child与恢复Session原parent关系，不按ID格式猜owner；不读消息／工具内容，不逐Snapshot发查询。多来源owner／interval冲突抛出准确错误，外层既有best-effort检查记录日志并停止该次Note，不能默借另一来源权限。
- `secretary/noting_notes.py`：只增加上述来源区间关联过滤；Full原始来源排序、最近相关普通pending判据、目标interval单次receipt、同事务重选／原FM机制均保持。内部origin未进入Notebook正文、六工具Schema或Prompt。
- branch接缝：原`notebook_inherit_branch_conn`会复制termination_json。按root明确方案，仅新branch Snapshot副本剥除`noting_origin`，保持普通admission关联原本不跨ref复制的语义；原Snapshot不变，payload／provenance／Anchor／termination type原样继承，superseded仍在原guard跳过。普通无origin termination保留原字节。

### 3. 正式路径与反例闭合

原ignored真实反例转入正式`tests/secretary/test_recovery_note_source_u20.py`。真实SessionDB、native `_compress_context`、Noting SDK Loop与`server.handle_request→secretary.noting_recover→_run_recovery`均执行；仅控制SDK结果／native summary及host构造凭据依赖，未替换准入、提交、selector、FM或receipt机制。

- B1后carried m9正式准入、Noting失败且第二次压缩失败，当前仍B1；正式RPC恢复提交成功，pointer自然演进、原failed admission／child逐项保持；**同B1无完整Notebook FM／receipt**。
- 在真实恢复提交后的通知callback内、`_run_recovery`尚未写committed／snapshot_id的原危险窗口，直接核实际Session witness仍不完整，但selector已能依原子origin排除本区间；并非事后补关联才碰巧正确。
- 后继真实native成功边界后，恢复Snapshot尽早投递一次；后继普通Noting明确受控400失败，没有新有效Snapshot遮盖该结果。重复检查／重新bind／重开DB不重复。另覆盖先成功到后继边界、恢复结果晚到时立即合法投递一次。
- 旧形状fixture明确用真实Snapshot INSERT的原可选参数缺省路径准备，不使用当前recovery writer、不UPDATE不可变Snapshot；仅在隔离fixture中准备既有completed recovery Session witness，验证无origin旧Snapshot也排除本区间、后继边界可投递。
- 在真实Snapshot INSERT后／pointer重选处令恢复提交失败，事务内已见origin；异常后Snapshot／pointer无半条提交、原failed事实保持，后续真实native Compact仍成功且无伪receipt。
- missing／foreign Conversation／wrong Anchor／cancelled／superseded来源均拒绝；工具termination伪造origin仍被严格白名单拒绝；故意冲突的恢复witness明确报`Conflicting Note source owners`且不投递。branch真实继承及后继native archive publication可选中合法副本，父来源审计保持。
- superseded模型基础排除复用未改的recovery_sources／notebook_store／joint路径与此前正式对照；本次13项Note分区包含其pointer／branch／模型base排除回归，未扩大为所有竞态已证明。

### 4. 验证结果与原始证据

源码基于`8fcbd7aa844acf3d3aa214bbb9f5cb4f1516a89f`。最终5个变更文件（4产品＋1测试）与5个未变相关源原件、SHA、完整patch／独立index tree及按函数健康指标，保存于ignored `recovery-source-review/c-r5/`；精确入口为`source-sha256.json`、`product-and-tests.patch`、`index-tree.txt`、`health-metrics.json`。主工作区真实index未暂存本包，未commit／push。所有日志在同级`recovery-source-review/`，不覆盖原C-R5缺陷证据。

所有pytest均经官方runner：

- `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh -j 1 --file-retries 0 tests/secretary/test_recovery_note_source_u20.py tests/secretary/test_noting_recovery.py tests/secretary/test_joint_noting_notes_u20.py`：**3文件46项通过**（11新回归＋22恢复＋13Note），`c-r5-regression-first.log`。
- branch增量后同runner定向新文件：**12项通过**，`c-r5-branch-second.log`；最后补显式`branch_ref != ref`断言并只重跑`-k branch`，**1项通过／11 deselected**，`c-r5-branch-final.log`。不把重复项加总成新的通过数。
- 相同runner对既有`tests/hermes_state/test_secretary_notebook.py -k branch`：**1通过、1已知基线失败、11 deselected**，`c-r5-existing-branch.log`。失败仍为旧`source_message_identities`字段断言KeyError；已在未含本包的`a5018ffd8206`干净基线实跑记录于`head-baseline-tests.log`。本次不改该旧断言。`c-r5/existing-branch-baseline.json`核当前test／notebook_model／notebook_items与当时原件SHA相同；notebook_store仅多既有superseded base拒绝（原forced测试不走该分支），差异存`notebook-store-baseline.diff`。
- 独立ignored Git index只收本次5文件：`.venv/bin/python scripts/check --staged --base HEAD --only footguns,shebangs,no-tmp,config-writers,os-marker-fakes,case-collisions,lazy-deps,profile-archives,ruff,health`，**10项通过、health 0 blocking／0 advisory**，`c-r5-quality-final2.log`。规则／阈值／豁免均未修改。`run_noting_task` CC11／107行、branch复制CC5／23行保持；Snapshot writer CC6／36行、selector CC6／32行；新来源helper CC5／17行，均未增长自身超标指标。
- 早期导入名／把失败提示FM误计为完整Note／尝试UPDATE不可变Snapshot的fixture失误日志原样保留，最终fixture已改为正式bind、按snapshot标识计完整Note及旧形状INSERT。这些不记成产品缺陷。第一次branch夹具误预期尚无新native边界就可投递，后改为真实branch后继publication。

### 5. 缺口与C-R6独立候选

C-R5及root指定branch兼容已实现并有上述定向证据。没有做UI、生产、真实模型或发布；不宣称整轮Verification／Validation通过。没有复跑180项或其它大套。

另按root要求只读单列的在飞recovery候选已由root确认为**C-R6待设计**，本次未改实现：旧有效m1 Snapshot在B1已投递，m9普通Task失败；B2成功时旧Note在Main busy队列等待。正式显式恢复同m9已进入真实SDK屏障，Main间隙flush仍只见原admission为failed，同事务重选把旧Snapshot落B2、占唯一receipt；随后恢复完成的新Snapshot无法再投B2。两次普通admission均为m9／B1区间、failed，实际来源位置相同。旧Snapshot由真实writer作为早来源晚到fixture准备；RPC／在飞SDK／FM队列／append与receipt均真实。根因仅记录为独立recovery owner未进入现有pending来源资格，不能只看model_config running永久阻塞Note。

C-R6证据独立保留：`test_pending_recovery_probe.py`、`pending-probe-final.log`（1个预期契约反例失败）、`pending-observation.json`（包括所有真实admission及path），不混入C-R5通过数。root已要求先交C-R5整包，待其按既有native recovery lease／queued注册／origin提交事实指定最小方案；本包未新增队列／Main gate或顺便重写pending选择。

### 6. 接口影响

仅两个默认None内部可选参数：`commit_noting_snapshot(..., origin_admission_id=None)`与`notebook_commit_snapshot_result_conn(..., noting_origin=None)`。普通CAS／record_commit、原failed admission／child、公开API返回、工具参数、Prompt、schema及生产历史数据无变更。新审计只随新recovery Snapshot INSERT；旧恢复关联只读现有metadata。branch仅去掉不跨ref的内部owner关联，不改Notebook内容。

### 7. 建议后续动作

root亲审C-R5／branch的5文件diff及源码SHA后统一集成；按已确认C-R6候选另给最小设计，沿保留反例定向关闭。独立Verifier／Validation仍由root按整轮统一安排，本包不自行提交或开启门禁。

## C-R6显式恢复在飞来源资格（2026-10-29，待root整包亲审，未提交）

### 1. 对应条款与授权

落实U20／plan第5、6条的最新相关来源等待、同事务Note资格重选，以及root已确认的C-R6反例。按root指定方案复用既有recovery native Turn lease、独立recovery Session audit和C-R5原子origin，不新增schema、调度器、通用队列、Main gate或FM机制。root另确认：另一进程已持现有recovery lease但尚无durable Session、重读仍not_found时，允许既有NotingRecoveryError／4002极窄拒绝`being reserved; retry the same request`；已有durable记录的重复请求仍返回原状态，不伪queued、不换ID、不自动重放、不新增轮询等待。

### 2. 实际变更

- `noting_note_sources.recovery_source_tasks_conn`将显式恢复纳入现有最新相关来源集合，实际关联同DB／ref的recovery audit→原admission→合法Anchor／来源区间，并核failed-child及原parent关系。沿Full原始来源位置与当前边界判断；原admission为failed不再掩盖独立恢复的queued／running状态。
- 活跃性只依既有`recovery:operation_id` native lease的有效期、精确holder及原生PID存活判断；新audit持久`lease_holder`以区分失效旧owner。旧无holder审计沿既有lease事实兼容。不会仅凭running字符串或`_WORKERS`字典残留永久等待，不解析holder格式，不在DB事务内取得`_RECOVERY_LOCK`。
- `noting_origin`仅recovery新增内部`recovery_session_id`。Snapshot同事务核可信child audit及其实际native lease owner，防已失去lease的在飞旧worker继续提交。提交完成即由该operation的原子Snapshot证明解除它自己的pending，不依赖SDK清理或事后audit patch；同一failed admission上的另一个恢复operation仍独立判断，不能借别人的Snapshot解pending。branch既有剥除整个origin的窄接缝自然覆盖此内部字段，正文／工具／Prompt不见该字段。
- `start_recovery`先受理现有native recovery lease，再对外持久queued Session；新holder具有独立token，worker以同一holder接手并沿原renew/finally释放。专属SessionDB构造移到queued发布前；失败在尚未受理阶段释放预留，不伪造queued成功。有效queued接手使用同native行的holder／未过期CAS，过期或被另一owner接管者不能复活执行。
- 启动线程失败对已存在queued Session明确failed、结束并释放；parent构造失败沿原worker失败路径明确终态。成功、失败、lease失效后的finally在释放恢复lease后，通过准确当前父owner调用既有`check_note_delivery`补检查；状态读取确认interrupted也补同一检查。冷父仍沿原`_publication_scope`，无新Turn，不把恢复末尾展示／补偿异常变成原生Compact异常。
- `select_note_conn`只把上述来源事实合入原latest集合，保留原来源位置排序、普通admission、目标interval一次receipt和实际append同事务资格复核；没有重写通用FM，也未改变原failed admission／child或任务来源业务口径。

### 3. 正式路径与反例闭合

新增精确正式回归`tests/secretary/test_recovery_note_pending_u20.py`，沿真实SQLite、native Compact、Noting SDK Loop、recovery RPC／实际start入口、现有FM队列与实际append。仅在SDK／worker开始／构造处控制结果或时序。

- 原反例：旧m1完整Snapshot在B1投递，m9普通任务失败，B2成功时旧Note排队；显式恢复进入真实SDK在飞后，Main间隙flush不得先占旧receipt。成功时新恢复Snapshot实际FM／receipt仅一次；失败时旧候选经终态补检查重新择取、实际落库一次。
- 在成功提交callback内核audit仍running／committed尚未事后patch、recovery lease仍持有，新Note已经实际落库，证明不会被自己的清理短窗挡住。两个不同request恢复同一admission时，A提交不能解除较新B的pending；B失败后A结果才由补检查投递。
- queued在worker尚未接手的屏障前已具精确native owner；该时点flush仍等最新来源，重复同request无第二worker／SDK。持`_RECOVERY_LOCK`的另一线程不阻实际FM append资格检查，验证DB事务没有反向取该registry锁。
- 线程start失败、parent构造失败、queued前专属DB构造失败均不留假成功／悬空lease；已有queued失败写terminal，尚无durable Session的构造失败保原错误并释放。失败后准确父owner可立即重新取得旧Note候选。
- expired／无lease／不同holder的旧queued不会阻Note或随后复活执行；旧worker不会释放新holder的lease。在飞SDK失去owner后，来源提交校验明确abandon，不能迟到新增Snapshot。
- 真实并发两个同request RPC只进入一次SDK／一次恢复Loop，原failed记录保持。真实独立子进程持native lease、尚无Session时，RPC按已确认4002拒绝；该进程释放后同request显式重试仅执行一次，未误释放对方lease或暗中重试。
- 真实子进程留下running audit及未到期lease后退出，沿原生PID死亡事实判interrupted，不等待字符串状态；相同request不会自动重放。另覆盖同DB其它ref，以及复制相同ref／operation标识但无对应lease的独立DB，不借全局worker事实互串。
- C-R5的12项当前区间／旧形状／原子回滚／合法晚到／来源拒绝／branch回归，22项既有恢复及13项Note分区同时通过；不据此扩大宣称全轮所有分区或独立门禁已通过。

### 4. 验证、版本与证据

- 本次基于HEAD `8fcbd7aa844acf3d3aa214bbb9f5cb4f1516a89f`，C-R5及本次C-R6共同7文件候选（5产品＋2测试）均未提交。精确源码副本／SHA、完整patch、独立index tree、逐函数指标位于ignored `recovery-source-review/c-r6/{source-sha256.json,product-and-tests.patch,index-tree.txt,health-metrics.json}`，摘要`summary.json`。真实共享index未暂存本包；root其它docs／APK工作未改。
- 最终官方命令：`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh -j 1 --file-retries 0 tests/secretary/test_recovery_note_pending_u20.py tests/secretary/test_recovery_note_source_u20.py tests/secretary/test_noting_recovery.py tests/secretary/test_joint_noting_notes_u20.py`，**4文件62项通过**（15 pending＋12 source＋22 recovery＋13 Note），36.6秒，原日志`c-r6-final-tests.log`。没有重跑180项或无关大套。
- 原ignored正式probe在本次最初修后定向也通过，`c-r6-first.log`（probe1＋C-R5 source12）。其修后JSON另存`c-r6/fixed-probe-observation.json`：before1／在飞仍1／结束后2。改前原失败日志`pending-probe-final.log`、原反例源码及C-R5源码副本继续保留。
- 最终独立ignored index只收7个候选文件：`.venv/bin/python scripts/check --staged --base HEAD --only footguns,shebangs,no-tmp,config-writers,os-marker-fakes,case-collisions,lazy-deps,profile-archives,ruff,health`，**10项通过、health 0 blocking／0 advisory**，`c-r6-quality-final.log`。规则／阈值／豁免不变，`git diff --check`通过。先前C-R5已证旧branch字段断言基线失败仍保留原事实，C-R6没有重跑或改写它。
- 过程日志保留：`c-r6-second.log`的启动错误fixture误按RPC封装、专属DB构造故障误打到RPC上游及独立脚本Path参数错误；修后`c-r6-third.log`11项通过。扩展matrix的`c-r6-fourth.log`14通过／1个lease丢失fixture遗漏显式interrupted观察；补状态观察后定向通过并纳入最终62项。没有把这些夹具错误算作额外产品缺陷。

### 5. 缺口与证据保留说明

C-R6指定范围已实现并取得上述定向证据，待root亲审；没有UI、生产、真实模型、外发、commit／push或独立Verifier。Linux PID namespace的未知／外部namespace仍沿原生TTL保守语义，不伪造平台验证；实际独立进程取证在本机Darwin完成。

证据维护中有一处明确纠正：原ignored probe自带同名JSON写入，C-R6最初修后复跑使`pending-observation.json`被修后观察重写。当前该JSON**不得再作改前证据**；已另存修后文件并在`c-r6/summary.json`标明。原`pending-probe-final.log`失败原文及原C-R5源码／probe保持，`c-r5-evidence-sha256.json`保存了原JSON哈希；不冒称原JSON仍逐字保留，也不手工重造原始观测。改前结论继续由原失败日志和原源码／正式入口反例支撑。

### 6. 接口影响

沿C-R5两个默认None内部参数；`_run_recovery`新增默认None的内部`lease_holder/reserved_db`以接续同owner及专属DB。新增内部审计`lease_holder`与origin的`recovery_session_id`，均不进模型正文／工具参数／公开业务数据。既有request成功受理后的幂等返回不变；只有root已确认的尚未受理预留竞争使用既有4002明确拒绝。没有更换lease类型／表、原admission归属、Main admission、六工具Schema、Prompt、发布脚本、前端或规则。

### 7. 建议后续动作

root亲审C-R5＋branch＋C-R6整体候选，重点核同事务可信origin、operation专属提交证明、queued lease接手、准确owner补检查及本次极窄busy错误。可直接复用最终62项／十检查及源码SHA；本包未开启逐包门禁，统一候选及整轮V继续由root负责。

## Root集成接收 C-R5／C-R6（2026-10-29）

已完整复核7文件及正式runner／selector／FM提交上下游：来源写入同一Snapshot事务、原failed admission保持、branch副本不借父来源、operation单独证明提交、queued先具原生lease且旧owner不能复活、终态准确父owner补查与锁顺序均符合U20。7文件当前SHA逐一匹配c-r6/source-sha256.json；复用最终62项及十检查，不重复大套。接收进入统一候选，尚非独立Verification／Validation通过。Noting通知误触发恢复另由root设计独立修补，不混作本包证据。
