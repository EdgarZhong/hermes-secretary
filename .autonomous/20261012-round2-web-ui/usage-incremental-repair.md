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
