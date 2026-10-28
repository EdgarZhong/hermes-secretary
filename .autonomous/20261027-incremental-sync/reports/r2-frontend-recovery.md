# 第二迭代 A-FE：F01／F02 实现交回

状态：实现与定向机制证据完成，交主会话亲审；不是独立 Verification／Validation 结论。未 commit／push，未部署，未操作浏览器或桌面。

## 1. 对应条款与版本

- 本轮 `plan.md` 第二迭代 A-FE、整改计划 §2.2 的 A01–A03；06 顶部 C0、C1 的有效请求资格及 D01／D02／D09／D14，S02–S08／S14–S16、P01／P03／P08／P09、C3 的同页恢复与必要窗口边界。
- 原审查 `cloud-verification-20261027.md` 的 F01／F02、§5.1–5.2、§6.4 反例只对应 FE `91ad72f`。本报告不将旧报告说成当前版本实测。
- 分配时 FE 基线 `1a906aef96ff4f089a0a371e653c1c2d855be7f3`；交回时共享工作区 HEAD `12a2b90dc4ec805f372d11e014cb2512333ebf64` 加本包未提交修改。期间 B-CACHE／root 已集成其它文件，本包没有修改 cache 文件、Controller、App、command actions 或根文档。

## 2. 实际变更

| 文件 | 改动 |
|---|---|
| `src/core/page-recovery.ts` | 新增 `captureRead()`，普通页面读取借用当前正式 round／lastRound 的 owner、连接代次、recoveryId、AbortSignal 和 current；cancel 直接 abort 同一正式 round，所以 recoveryId 不变也立即撤销资格。没有另建恢复状态机。 |
| `src/core/controller-page-recovery.ts` | `loadEarlier` 捕获 key、HistoryWindows 实例、PageRecovery 读取上下文和 HTTP credentials；传递正式 signal，在 accept／commit 前及错误传播前复核。正常取消后成功、网络失败、迟到 401 均不能回写或冒成动作错误，当前真实 HTTP 错误仍抛出。 |
| 同上 | 先核 owner／runtime／epoch，才对 `complete:false,reason:anchor_not_found` 精确退役封套中请求的 anchor selector。利用 B 的 `HistoryWindows.retire()`，撤销该证明、同 anchor 的复用资格、适用 viewport／warm 需求和持久 sync 配对，保留 latest 与其它缓存。合法阅读目标和被复用窗口的 anchor 不同时，先重读合法阅读目标。REST 精确 404 使用同一退役入口。 |
| 同上 | 文档内退役集合只记录已经权威确认不存在的 anchor 资格，不参与页面 readiness／动作权限；后续旧 viewport 或迟到持久候选不能重新引入死 selector。当前需求的 anchor 可从同 owner 已加载窗口身份解析，不为缺失窗口扩大读取。 |
| 同上 | root 指定 B-CACHE 薄接线：无 sync 也恢复 details 提示；没有真实 sync 时不 accept 窗口、不造覆盖证明。后继正式快照的消息身份及 revision 才决定能否复用。 |
| `src/core/r2-frontend-recovery.test.tsx` | 正式 Controller／PageRecovery／HTTP 处理及真实 IndexedDB 的定向场景，另通过实际 App 的 Load earlier 按钮和 Toast 消费链验证认证后迟到结果。 |

## 3. 正式路径与接口

- App Load earlier → `Controller.refreshHistory(id,true)` → `ControllerPageRecovery.loadEarlier` → `PageRecovery.captureRead`／`captureHttpCredentials` → `readRecoveryHistory(...,signal)` → 有效后 `HistoryWindows.accept/view` → `commitHistoryView` → 正式 App 渲染。取消、断线、认证撤销、换 owner 共用既有 round abort 权威。
- `PageRecovery` 的 conversation resource → 正式 metadata／binding → REST／缓存必要窗口 → `session.activate(recovery_view)` → `validateEnvelope` → 精确 anchor 退役或完整封套 → 原正式 installCut／reconcile／commit。owner／epoch 错误仍走既有拒绝路径；临时 `view_changed` 不被当成删除。
- 只新增内部窄 API `PageRecovery.captureRead(): ReadContext|undefined`，未改变现有 API 必填参数、默认 200 条、分页入口、composerActionPolicy、availability 或主按钮资格。Steer 的 reconcileLiveView 和 Slash 目录接线保持。

## 4. 验证结果与证据

环境：macOS、Node `v24.21.0`、npm `11.19.0`、Vitest `4.1.11`，现有依赖，无安装／锁改动。证据根目录为 FE `.archive/incremental-sync-20261027/r2-frontend-recovery/`。

| 证据 | 输入／观察与结果 |
|---|---|
| `A01-cancel/disconnect/authentication/owner.json` | 4 种撤销，各覆盖迟到成功、网络失败、迟到 HTTP 401；recoveryId 保持不变但 signal 已 abort；旧 index 与当前 history 完全不变，notice／notifications 均空。认证后的敏感 history 保持 0 行。 |
| `A01-App.json` | 实际 App initialize、Load earlier 按钮、正式 Controller 与恢复类；当前独立 HTTP 401 清空后，旧分页成功仍不复活 DOM 历史，无 Toast。 |
| `A02-warm.json`、`A02-cold.json` | 真实持久配对窗口冷读／暖内存，正式封套 anchor_not_found；仅最初一次包含失效 m201 selector，后续两次为合法 latest；删除的 m201／m401 不复活，地址保持 chat，持久缓存无退役 selector，availability 最终 ready。冷入口的 viewport 是显式当前需求，不声称持久缓存自动恢复了阅读位置。 |
| `A02-automatic-retry.json` | 先让当前轮临时失败，恢复正式 1 秒退避计时器；下一轮收到 anchor_not_found，随后同 document 自动提交 latest，recoveryId 增加，未调用 reload／改变路由。 |
| 其余定向断言 | 正常更早分页 200→240；当前 503 仍抛出；暂时 view_changed、owner 错误、epoch 错误不退役 anchor，之后正常恢复；无 sync 的完整 details 在同 revision 复用、changed revision 拒绝，零旧详情网络读取，只有真实快照窗口取得 verified 资格。 |
| `regression.log` | 5 文件 166 项全通过，4.85 秒：本包最初 12 项＋controller-page-recovery、controller-incremental-sync、page-recovery、page-recovery-availability。该版本包含最终产品修改；之后只扩充本包测试。 |
| `tests-final.log` | 扩充后本包 14 项全通过，2.87 秒；含自动退避与无 sync 详情版本反例。 |
| `typecheck-final.log` | 最终 `npm run typecheck` 通过。首次曾遇 root command-actions 的模板字面量类型问题，root 已修复，本包未修改该文件。 |

初次 12 项有两个夹具失败：cold 初态有内存被正式 hasMemory 正确拦截，详情 cards 错误声明不需要 deferred 字段；分别改为真实空冷态＋明确当前 viewport，以及正式 deferred cards 后通过。没有放宽生产断言。

产品文件 SHA256：

- `controller-page-recovery.ts`：`1eb60dbf8f079a84866ecf5e87502349a0f57395c9174164be9c9c97a58550c1`
- `page-recovery.ts`：`e4a76adb7d896f7a83f2a4cc7aeb984d1a97dd8d03a517f2c60c37860f56364c`
- 本包测试：`e4bc38a75347e17bcf6360cbd6dcba371c2755f6478065a3503413ca7df290f8`

## 5. 缺口与证据边界

- 本包没有真实 Python／SQLite／HTTP／WebSocket 联调，没有使用浏览器、隐藏 IAB 或 Android 真机。RPC／HTTP 返回体与延迟是外部依赖受控；PageRecovery、Controller、HistoryWindows、IndexedDB、App 按当前正式源码执行。不能把 jsdom App 断言称为浏览器 UI 验收。
- A-FE／A-BE／B-CACHE 的最终联合关闭仍需 root 按指定真实后端和隐藏 IAB 场景取证，并进入用户云端 Verification、本地独立 Validation；此报告没有代替两门禁。
- 没有运行无关大套或全仓测试，没有新增发布／审批流程或调整检查阈值。

## 6. 接口影响

- B 的 `HistoryWindows.retire(selector):boolean` 已存在并直接调用；没有 cache 层修改或新 API 需求。
- 主会话无需补 Controller／App 一行接线；原分页入口已经接到本包实现。B 无 sync 详情恢复的薄接线也已随本包完成。
- 退役记录限文档内 owner 身份空间；认证清理清空。持久缓存只去掉失效 selector 配对，最终成功恢复再通过原 ready gate 写入最新合法缓存。

## 7. 建议后续动作

主会话亲审上述两产品文件与新测试后纳入统一候选；复用日志，不重复全量回归。重点在真实 Python／SQLite／HTTP／WS＋自建隐藏 IAB 复验：older 在途断线／认证／切 owner，RPC anchor_not_found 冷暖恢复及两轮后不复活；检查 B 详情完整性与 A-BE 同步封套共同工作。完成新候选全轮门禁后，按用户已授权流程统一 main 集成、Alex 上线和 0.1.9 APK 交付，本包未自行发布。

## 2026-10-28 · 主会话健康棘轮复核后的窄修补记

主会话指出原交回的 `readCachedDisplay` CC 从冻结基线19增至21、`readConversation` 从22增至26。按指定方案仅改 `controller-page-recovery.ts`：把缓存 index 的创建／details 恢复／sync 过滤与接纳抽为 `restoreCachedHistory`，调用点保留 value、current 和尚无 loaded 窗口资格；把失效 anchor 的选择、退役与 incomplete envelope 的有限重试判定抽为 `retryIncompleteEnvelope`。原循环次数、owner／epoch 先验、取消早退、异常类型和提交路径保持。没有修改测试、PageRecovery 或其它产品文件，没有提交／推送。

使用主仓现有 `scripts/code_health/ts_units.mjs` 与 UI 现有 TypeScript，直接对照 root 的 `root-health.json.before` 度量，完整输出为前端证据目录 `health-followup.json`：

| 函数 | 冻结基线 CC | 窄修后 CC | 长度／嵌套 |
|---|---|---|---|
| `readCachedDisplay` | 19 | 17 | 26／2 |
| `readConversation` | 22 | 21 | 58／4，原超标值不增长 |
| `restoreCachedHistory` | 新增 | 5 | 6／2 |
| `retryIncompleteEnvelope` | 新增 | 5 | 7／1 |

同一 before 内两产品文件全部函数按冻结 CC20／长度300／嵌套6与超标不增长规则比较，新增违规0。没有改阈值、改等级或豁免。

本次只复测本包14项，通过（`health-followup-tests.log`，3.17秒）；typecheck通过（`health-followup-typecheck.log`），`git diff --check`通过。没有复跑大套、操作 UI 或桌面。当前适配器 SHA256 为 `31a76ada0b886e7f53799803d9aa1f0e267f950d6ff5c3ef2f1e5b0075ac1e0e`；上文原 SHA 是首次交回时点。PageRecovery 与本包测试 SHA 保持。
