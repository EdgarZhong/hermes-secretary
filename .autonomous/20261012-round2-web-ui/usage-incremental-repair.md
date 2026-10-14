# Usage / Context 原生字段增量修复交回

2026-10-14；实现 Owner `usage_incremental_repair`，禁止派生。UI 基线 `ab1f4c4bd7aabc6c129610d36dabf83314b909ea`，本任务不 commit、不 build、不跑 full suite、不发模型、不重启服务/浏览器、不改运行 profile。Root 授权了最小单 worker 测试及 typecheck，测试窗口已释放。仅修改五个前端 core 文件，主仓库只增加此报告及 ignored 证据。

## 1. 对应依据与阅读

- 已读主仓库 AGENTS / CLAUDE、executing-plans、autonomous-run 的消息/交接契约、本轮 snapshot-index / baseline / plan（含已有证据索引和复用选择）。
- 02 §1.1–1.3（L18–82）、§1.5–1.9（L166–257）、§4.1–4.3（L1095–1163）、§4.12（L1360–1386）：真实 Turn 与 provider call 分离，profile / Session / Conversation 不混用；原生 owner 及关闭行为不变。
- 06 §0.3–0.5、§1.13–1.14、§2.8–2.9、§3.2–3.3、§4.5–4.6：薄客户端、纯内存投影、已有 native APIs、真实 source，不造 count / API，不以消息行或 API calls 推 Turns，不用 Noting 计数填 Main。
- 本次用户明确要求经 Root 派遣传达：实际会话 active 或完成均可见；已取得数值不因缺失、失败或 Turn 变化清空，只有新有效数值按字段原位更新；底部胶囊及展开数据都遵循，纯内存，不新增 API，native 来源不足则未知。
- Root 最新安排：正式第二轮 Validation 先行，Verification 最后静态审查；此实现证据不替代正式 Validation。

## 2. 调查结论与实际变更

### 前端实际缺陷

1. 原 `retainNative` 以整包 token 字段判断是否保留；当新响应有某些有效 token 值、另一些字段为 null，整包替换清空原数值。独立有效 `turns` 也不参与原 known 判断，可能被旧整包遮住。
2. 原 `sessionView` 一旦保存了 canonical snapshot，遇到 cold unknown 就永久返回旧 snapshot，不再取 REST 原生保存计数；保存来源本身已更新也不显示。
3. 原新 runtime / epoch 会清 `usageDetail` / `usageSession` / `live.usage`。后续未知或失败使已取得数据消失。
4. `session.info`、`session.usage`、`message.complete` 三个 Context 接缝整包替换 `live.usage`；部分/缺失的 occupancy 字段清空旧数字。
5. 压缩续接时 route 仍是原 stored ID，而 native Usage 返回当前 tip；原 `readUsage` 用 route ID 验证会误拒绝正式 Binding 已确认的 tip。

### 修补范围

| 文件 | 机制 |
|---|---|
| UI `src/core/usage-counters.ts`（新 sibling） | 每个 token / total / ratio / Turns / Model Calls 独立合并；非负有限数值有效、0 有效，比例限制合法范围；缺失/未知/非法值保留已取得字段；不自行累加或推数。Context 只合并原生 occupancy 字段，并保留对应 estimated/source。 |
| UI `src/core/usage-view.ts` | 唯一 scope owner 保留数值投影；runtime/epoch 改变废止旧请求，不清同 scope 数值；canonical 与 REST saved 数据按字段更新；cold fallback 每次可读取新原生 totals；请求 serial / owner 防止晚回包。 |
| UI `src/core/controller.ts` | 正式 Binding / live reconcile / epoch / readUsage 委托。响应归属采用 Binding 的 current stored tip；scope 仍为 profile + selected route。文件仍 2,000 行。 |
| UI `src/core/projection.ts` | 三个原生生命周期事件的 Context 使用同一合并函数，不改变事件/Turn/历史语义。 |
| UI `src/core/controller-usage-view.test.ts` | 生产 Controller 路径反例覆盖字段更新、0、Turns独立可用、完成Turn、失败、cold saved刷新、runtime/epoch、rotation、会话/profile隔离和Context三个事件。 |

没有修改后端、API DTO、App 或呈现组件、任何配置/锁文件、浏览器持久化白名单或模型执行机制。Existing Utilities 直接读 `usageSession` / `usageDetail.latest_completed_turn` / `live.usage`，所以胶囊和展开指标自动使用同一数值；没有新增 UI 接口。

## 3. 正式输入到输出链

1. 已绑定的 native `session.usage` / `message.complete` → Controller `sessionEventEffects` → 原 `session.usage_detail`；unknown owner 使用已有 `GET /api/sessions/{current stored tip}`。
2. `UsageViews.read` 验证 runtime + native stored locator、以 epoch/owner/serial 废止过期回包 → sibling 合并每个实际有效字段 → Controller owned publish → App Utilities 的 Session Total / Latest Turn / 胶囊和展开指标。
3. Native Binding `info.usage` 与三个事件 → Context sibling 合并 → `reconcileLiveView` 唯一 Usage scope owner → `live.usage` → Context ring / used / limit；没有第二个占用估算器。
4. 新会话/profile 使用新的 scope，不能获得旧数值。同一 scope 的 runtime 重新绑定、服务 epoch 改变、原生 compression continuation 保持最后已知字段，但新的合法数值（包括真实下降或0）直接更新，不取 max、不累计。保留值是 UI 最后已知投影，不把它伪造为新 runtime 的原生回执。

## 4. 验证与真实来源证据

证据目录：`.hermes-dev/round2-verification/usage-incremental-repair/`。

| 命令/证据 | 结果与范围 |
|---|---|
| `npm test -- src/core/controller-usage-view.test.ts --maxWorkers=1 --no-file-parallelism` | 39 项中 38 pass / 1 fail；原始 `focused-first.log` 保留。唯一失败是旧 HMR 测试要求 cold unknown 后不取 REST，与本次新有效原生值更新冲突；只修断言，产品代码未因本失败再改。Vitest duration 368ms、命令约1.27s。 |
| 同两文件 `-t 'adopts a real HMR snapshot\|keeps observed Usage\|epoch changes discard\|Usage failure does not block\|same-epoch disconnect discards\|all compaction terminal kinds'` | `affected-seams.log`：5 pass / 103未选，340ms（命令约1.02s）。含唯一失败复测与4个原 Controller正式 Usage/epoch/压缩失败接缝。最终 **43 distinct** 用例取得通过证据（38首包＋1修复HMR＋4既有接缝），不是某条最终43PASS全包命令；未重复首包有效38例。 |
| `npm run typecheck` | `typecheck-first.log`：通过，约1.66s。未 build/full suite。 |
| `git diff --check` | 通过。`source-manifest.json` 记录5个UI文件、只读backend来源hash、UI基线及controller 2000行；`owned-diff.patch` 给Root集中review。 |
| 只读 `read-native.mjs` → `native-source.json` / summary log | 当前53445 health commit=`cb05c0671c2c7e1e995e0f3b7d1c24ac216d3d5c`；`session.active_list` 没有已绑定runtime，故未调用resume/activate，不制造runtime以取证。现有REST三条真实保存Session返回 input/cache-read/cache-write/output 和 `api_call_count`，没有 `turns` / `turn_count`。 |
| `prior-cold-native-source.json` | 从既有 `prompt-main-final/current-usage-native.json` 原样复制，不重做模型/复验：runtime `a282dde6` / stored `20261013_223838_0ddd56` 在原生RPC返回 total unknown，reason=`restored_session_totals_unknown`、turns=null；Latest real completed Turn input=843 / cache-read=189696 / output=1207 / model_calls=3。这是既有真实响应证据，不冒充本次重启后的新响应。 |

关键反例与结果：

- 独立 Turns 2、token 全空：2 正确更新，其余保原100/50/20。
- Session Total 与新 completed Turn 有效0：input/output/ratio/Turns/Model Calls中的0更新；total、cache-read及缺失output按字段保留。
- 新 Turn全部未知：旧 completed tokens/model calls保持，不变成空卡。
- cold active `session.usage`：saved input从35068更新到36000，不将原生calls500填为Turns。
- `message.complete`：Turn2统计正式更新，缺失input与calls保持原真实数值。
- compression tip A→A-rotated：接受 verified tip，REST读取当前tip；route不变、原值不被身份误判清空。
- runtime重新绑定：unknown+REST503保持数字；随后input150更新，缺失Turns保持1，错误清除。
- epoch改变：数字/Context保留，旧inflight999不发布。
- Context三个事件分别验证：部分新max20000更新而used1000/10%保留；有效0 used/percent更新；无usage继续保留。
- 会话/profile隔离及负数/NaN/Infinity/越界比例：不能串用或删除已取得合法数值。

## 5. 缺口与风险

**总 Turns 目前有真实源限制，不能声称全面修复为可用。** `agent/usage_read.py` 的 `begin_main_turn_usage` 对已有 history 的 restored owner 设 `cold=True`；`main_usage_detail` L297–298 在 cold 或物理 Session rotation 时返回 Session Total/Turns unknown，后续完成新Turn不会把cold历史变成完整可计数历史。原生 saved REST 仅有api_call_count，`server._get_usage` 仅有calls，没有完整历史Turn数。前端已经把任何真实可用的 Turns 独立接好并保留，但未曾取得的 lifetime Turns 必须未知。

当前只读取证没有 live runtime，无法取得本次运行的新 `usage_detail`。正式 Validation 需由Root授权实际用户入口恢复/新建并使用会话；实现者没有重启、改profile、resume或发模型。此限制保留，不能拿控制器受控依赖证据冒称真实UI全部通过。

按用户逐字段要求，某字段缺失时可显示较早成功值，旁边另一字段来自较新成功值；total/rate不从混合数值重新推算，Latest保留槽位不等同于编造本次Turn的新原生receipt。原有retain flags记录投影保留事实，未新增过时文案或Information弹窗。内存owner仅留少量数值/归属，不保完整历史/API持久缓存，整页reload不会从本地恢复这些数值。

本次没有跑冻结health全包。新sibling最多约70行/函数约20行，controller未增长；Root可在最终静态审查统一检查冻结健康指标。后端原生owner/cold会计和Noting隔离机制完全未改，23例BE-USAGE有效证据按plan复用，不重复运行。

## 6. 接口影响与交接边界

前端内部 `UsageViews.clear()` 改为 `invalidate()`，唯一正式调用处已同步。`activate` 可接受verified stored locator，`context` 成为唯一数值保留owner的内部委托；RPC/REST DTO及旧事件形状不变。App无接线需求，Clarify独立工作树无文件交叉。

请Root review sibling与Controller上下游、响应身份/serial、原生cold限制及这份证据。五个源码/测试文件未提交，由Root统一集成快照及后续正式Validation。本任务没有改根文档/plan/规格，用户已有修改均保留。

## 7. 建议下一步（正式Validation材料）

1. 新建实际Session，从无旧history开始，至少两次Main完整Turn：检查真实 `session_total.turns` 0→1→2，在active和结束都显示；Latest只在实际完成边界更新，model_calls不能填Session Turns。
2. 使用已有cold恢复会话：真实REST保存token/rate/total可读并刷新；若native totals unknown，界面Turns保持未知并在验收记录标来源限制；不得把恢复后的新增Turn数冒充全部历史。
3. 同一页面已有值后断线/epoch恢复、会话runtime重绑、压缩续接：核所有胶囊/展开字段原位保留，最新有效原生字段更新；换会话/profile不能串值。不要为这些确定性边界重做附件/长模型/全套测试。
4. Context采用native实际usage，压缩期间沿既有状态形变/Cancel；完成后有新有效occupancy则更新，无值保持最后已知。新的cold页面没有可信occupancy则仍未知。

此交回是实现和必要机制证据，正式第二轮Validation由Root编制材料/指示后由指定GPT-6.1执行，最终Verification按用户最新安排做静态审查。

## FV-F01 正式 Validation 真实失败后追加（2026-10-14）

本节覆盖本报告前述实现对 **canonical partial 的来源补齐** 结论，不改写旧43用例的实际通过结果，也不宣称它们覆盖了此次真实错误。正式失败仍由原 Validation 报告保留，Root review / 集成与原 Validator ≥3 Turn 同会话复验尚未完成。

### 1. 依据、版本与隔离

- 正式 Validation 的 FV-F01 / V11；Root最新明确授权：先查真实返回、按字段canonical优先/缺口用已有saved补Session，source标签不代表完整度；Latest原生failed_dispatch缺值保最后已知，不以Session差分造值，不改backend。
- 真实后端运行 `ea2ab483999f9230abfd794bdde2ea3fe2468cfe`，产品仍cb05c；正式前端 `833ef31468dbc73e0f25961cec1fe81399ba6111`。实际Session `20261014_162414_e964a3` / runtime `b03b78a2`。
- 获授权创建平铺 worktree `/Users/edgar/code/hermes-secretary-web-usage-live-fix`，分支 `codex/round2-usage-live-fix`，从833ef31创建；common hook原样保留/可执行，node_modules仅链接既有目录，不install。所有改动限该树；未触正在验收的5173正式main、未触发其HMR。
- 无派生、产品主目录修改、后端修改、模型调用、重启、改配置、build/full suite或commit。唯一测试窗口已通知Root起止并释放。

### 2. 完整真实根因与变更

只读53445取得 `fv-f01-fix/source.json`：

| 来源 | 实际字段与语义 |
|---|---|
| `session.usage_detail.session_total` | input/read/output/total/rate均null；availability=`partial`、source=`native_canonical_accounting`、reasons=`failed_dispatch`，但 **turns=2真实有效**。 |
| 同响应 `latest_completed_turn` | 五个token/rate字段均null，partial / failed_dispatch；实际新turn_id=`…:6c607caa`，**model_calls=4有效**，completed_at=`2026-10-14T08:28:15.182528+00:00`。 |
| 原 `session.usage` | total125795 / input16124 / output1895 / prompt123900 / calls5 / cache_hit_pct87；它提供已知native aggregate，不提供第二Turn的新token明细。cache_hit_pct为native舍入呈现，且原分母语义可能含cache-write，不能拿它猜精确hit。 |
| 已有 REST `GET /api/sessions/{stored}` | input16124 / cache_read107776 / cache_write0 / output1895 / api_call_count5；四个真实bucket完整，total确证为125795，按已冻结input/read定义rate=`107776/(16124+107776)`。API calls不当Turns。 |
| event replay | 原生replay truncated=true，保留的session.info/message.complete usage投影只有2个；原始筛选usage字段与seq留在source.json，不以缺失早期事件否定正式Validator的观察。 |

原后端 `agent/usage_read.py` 在failed dispatch后把相应token完整度标未知；这是本次 **Latest原生缺值** 的来源事实。前端 `sessionView` 仅看source是否canonical即提前返回，忽略已有saved字段来源，导致Session虽有新有效native计数仍保首轮48418。这个前端gate是FV-F01 Session缺陷根因，不需要改原生会计或新API。

实际修改四文件：

| 独立树文件 | 实际变化 |
|---|---|
| `src/core/usage-counters.ts` | `completeSessionUsage`检查每个呈现字段的有效性；`mergeSessionUsage`先补saved新有效字段，再由每个有效canonical字段覆盖，缺值继续保原字段；saved参与时明确source=persisted、partial及canonical/saved原因，保observed_at。Latest合并保新的partial/failed_dispatch原因，避免旧值保留吞掉新原生不完整事实。 |
| `src/core/usage-view.ts` | 只有每个实际字段都可用才跳过saved；partial/缺失实际读已有REST。若native明确 `incompatible_cache_semantics`，不以saved桶计算的ratio补这个被明确否定的字段，已知历史ratio按用户保值规则保持。 |
| `src/core/controller-usage-source.test.ts`（新） | 5个生产Controller测试：真实FV-F01来源组合与message.complete正式接线、按字段canonical优先、saved缺cache-write不猜total、saved403保原值并更新Turns、cache语义明确不兼容。 |
| `src/core/controller-usage-view.test.ts` | 现39项Usage owner包补齐完整canonical fixture的真实total字段；纠正旧“canonical partial不得读saved”断言；缺失保值反例明确saved也不可用，以免假造“存在新有效来源却不更新”的预期。 |

controller / projection / App / DTO均未改，controller与正式main逐字相同且2,000行，FV-F02的独立controller修复可无冲突集成。

### 3. 正式链与两类结论

正式 `message.complete` / `session.usage` → Controller原 `readUsage` → 原usage_detail → UsageViews字段完整度 → **必要时已有 saved REST读取** → 同owner/serial防晚包 → Session projection → 原Utilities胶囊和展开字段。

**Session缺陷：已在独立树修复并有反例关闭证据，尚待正式Validator复验。** 实际partial返回可令Session更新input16124/read107776/out1895/total125795/rate真实值、Turns2；有效canonical字段始终优先，不累计、差分或以calls补Turns。

**Latest合法未知：未伪造新token数。** 本次实际completed receipt不提供token值；依用户按字段保留，显示上次15014/read32640/out764/total48418/rate，同时更新真实Calls4并保 `failed_dispatch`/partial原因。不能把首轮token视作本轮新的原生结果，也不能把Session125795或其差分放到Latest；原Validator复验应按“源确实缺值则保最后已知、新有效值再更新”判定。后续即便Session仍受累计failed完整度影响，只要某次新Latest原生字段有效，仍直接更新该字段。

### 4. 验证与遗漏说明

证据目录：`.hermes-dev/round2-verification/formal-validation/fv-f01-fix/`。

- 修前仅运行新真实响应反例：`negative-before.log`，1 fail / 4未选，正式Controller完成事件后 **48418≠125795**，稳定复现，不靠源码断言或镜像实现。Vitest1.18秒、命令约1.82秒。
- 修后唯一受影响Usage包：`npm test -- src/core/controller-usage-source.test.ts src/core/controller-usage-view.test.ts --maxWorkers=1 --no-file-parallelism`；`focused-first.log` **44/44通过**，460ms、命令约1.12秒。只针对因来源选择与Latest原因合并而实际变化的Usage范围；不重跑旧4个不变Controller/压缩接缝、BE23、全套、附件或模型。
- `npm run typecheck`：`typecheck.log`通过，约1.51秒；`git diff --check`通过。没有build/full suite。
- `manifest.json`记录四个源码/测试hash、未变controller hash/2000行、worktree基线和原始source/负例/测试/tsc hash；`tracked.patch`供Root亲审（新测试在工作树中直接读取）。

**旧43项漏掉的真实错误：** 旧源选择测试把 `source=canonical + availability=partial + tokens全null + Turns有效 + saved新有效值` 这一组合明确断言为不读saved；它将source标签误当完整性，反而固化了缺陷。普通incremental反例只验证缺失保旧值，没有同时提供并要求使用新的可靠替代native源；fully-available canonical fixture也未包含实际total字段。本次用实际failed_dispatch返回及真实保存桶重建正式完成事件反例，纠正这些预期。旧43通过证据仍真实，**不能再据它证明canonical partial实际来源覆盖完成**。

### 5. 缺口、风险与原生边界

- 当前运行main仍833ef31，独立树未集成。真实UI缺陷尚未正式复验关闭；保留原FV-F01失败，不把此机制证据等同完整正式验收。
- 完整Session saved bucket可用时才给total；缺cache-write等必要来源时仍保持上次可用total/未知，不从API calls、Session差分、文本数或native rounded hit推新数。
- 当saved读取失败/错误owner，原canonical有效字段仍更新，其余保最后已知，错误记录；既有profile/runtime/epoch/serial机制不变。
- 有些字段可分别来自当下canonical、saved或上次已知投影，这是用户逐字段规则；availability与reasons保source缺口。Latest本轮确实缺值，不以UI首值保留掩盖新receipt不完整，也不扩大backend权限。
- 原生owner/cold、Main与Noting计数隔离、后台关闭及原API/事件合同完全不变；BE-USAGE23证据继续复用。

### 6. 接口、责任与交接

仅前端内部新增完整度/来源合并helper，无DTO/呈现组件接口变化，不改controller；Root已接收完整根因与修复方案里程碑，明确不授权backend改动。全部四个文件留在独立Usage worktree未提交，由Root亲审后集成；common post-commit钩子保持，后续提交/push由Root统一管理。

### 7. 建议正式复验

Root亲审并集成后，由原正式Validator在同一FV-A Session继续至 **≥3个真实完成Turn**：对比usage_detail每字段有效性、native saved桶、Session胶囊/展开字段、Latest完成receipt与Calls；第三Turn若Latest有新有效token数必须替换首轮值。若源仍null，按最后已知保留并在正式报告明确source缺口，不能猜新数。后端无需重启；前端切换稳定快照与运行实例由Root安排，禁止本实现者触正在验收的主目录/页面。

#### FV-F01 最终健康拆分与定向补证

最终静态自审将同义的Latest来源原因/availability合并提为 preserveTurnFacts 小helper，避免既有 mergeUsageDetail 复合条件增加复杂度；没有语义、controller或接口变化。Root释放FV-F02窗口后只批准新来源5例+typecheck，没有重复44包。

- 当前最终产品树 final-source-five.log：新来源5/5 pass，211ms（命令0.84秒）；final-typecheck.log通过，约1.50秒。
- 冻结 scripts/code_health/ts_units.mjs + Measurer._typescript + compare/apply_allows/verdict，使用现有lock的TypeScript5.9.3，对基线833ef31与当前两个产品文件定向测量/比较：frozen-health.json **0 blocking / 0 advisory**；mergeUsageDetail CC19/19行/嵌套1，preserveTurnFacts CC7/7行/嵌套1。没有改规则/阈值/级别、豁免或安装依赖，也没有跑health全包。
- manifest-before-health-extraction.json精确保留44项包执行树；当前 manifest.json记录最终四文件及5项/tsc/health/raw-source证据hash，tracked.patch更新至最终版本。39项旧owner包按此次同义提取的未变机制复用，**不将早先44命令冒称最终byte-identical树的一次44PASS**。
- 最终 git diff --check通过，controller仍2,000行且完全未改；未commit，主目录/运行服务未触及。Root完整亲审后再安排正式Validator复验。

#### FV-F01 已亲审提交，待真实复验（2026-10-14 16:54）

Root已完整亲读两个产品模块、正式Controller来源反例与旧断言修订，接受按字段canonical优先/saved补缺、Latest保值及原生原因；已接收测试/冻结health证据，不复跑。其后授权仅显式stage上述四文件并commit。

提交 b2be3fecf075528b421e7858ec7086ee60eae361（fix: 补齐原生 partial Usage 的有效 Session 来源），位于独立 codex/round2-usage-live-fix。共四文件135增/8删，没有controller/App/DTO/backend改动。common post-commit自动push成功，git ls-remote独立核对 origin/codex/round2-usage-live-fix 远端hash与本地完全一致；工作树干净，最终测试源码manifest4/4匹配，证据 fv-f01-fix/commit.json。

未合main，未改53445/5173服务。Session缺陷已完成实现、机制反例与Root亲审，**正式FV-F01仍待Root集成后原Validator在同FV-A会话≥3个真实完成Turn复验**；Latest原生failed_dispatch缺字段继续按最后已知保留，不能把本提交冒称取得不存在的新receipt。
