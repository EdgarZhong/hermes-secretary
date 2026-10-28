# 第二迭代 B-CACHE：F03／F04 实现交回

状态：本包实现与针对性验证完成，待主会话亲审及跨包集成；不是独立 Verification／Validation 通过声明。未提交／未推送，未部署／未操作 UI。

## 1. 对应条款及实际阅读

依据本轮 plan、snapshot-index、baseline；06 顶部 C0–C3 全部 D／S／P 表，重点 C0.3–C0.7、D01–D05、S12–S14、P06、P08、C3.3；原云端报告 §1、§2–3 缓存相关判据、§4.6、§5.3–5.4、§6 原反例；整改计划 §2.3、§4 映射。已读两仓 AGENTS、主仓 CLAUDE（UI 根无 CLAUDE，AGENTS 指向主仓）、executing-plans 全文及 autonomous-run 消息交接条款。原报告 SHA256 实核为 `3546c0e1138804f25a4e24fcc8ca5d9f3dd1486399445b9300135a0f2b5b24bf`；其旧版本结论未冒充当前实测。

F03 对应 C0.4、D01、D05、S12、P06、C3.3；F04 对应 C0.3、C0.5、D04、S13。本包同时保护已有详情懒取、真实空／未取／半截区别、同 UID 落库和页面早期阅读内存。

## 2. 实际变更

只修改 UI 白名单 `src/core/history-coverage.ts`、`history-sync.ts`、`display-cache.ts`；新增小 sibling `history-cache-budget.ts` 与专属测试 `r2-cache.test.ts`。未改 Controller／PageRecovery、API 契约、后端产品、冻结阈值或环境。

- `retainDetails` 按 UID、物理行、role、revision 核验后，逐个保留已取得字段类别；Thinking 子集不再抹去完整工具参数／结果／终态输出。未取字段仍 deferred。Thinking 记录、窗口复用、restoreDetails 和 cachedDetails 共享相同版本边界；新 revision／代表／role 不借用旧详情。
- `DisplayCache` 写入与冷读都先执行白名单验证，再统一选择窗口、详情与经过 `checkedThinkingPrefix` 核验的 native prefix 的最近 500 身份。新前缀占一个名额，淘汰逻辑最旧候选；持久 UID 已出现则由持久行接管、退役过渡 prefix，避免双计。
- 淘汰命中任一窗口消息或其 latest_thinking bundle 时，整个 selector 的同步证明退出持久缓存，绝不裁行后保留旧 coverage／receipt／cursor。其它完整窗口原样保留。被退役窗口仍在范围内的行作为版本化详情／显示提示保存，不伪造新证明；在线 HistoryWindows 与当前早期阅读页不受落盘淘汰影响。
- 无同步证明的 legacy 展示壳同样为新前缀预留名额；所有证明被容量淘汰时，剩余版本化行提示仍可冷读。未新增预读、独立游标、权限或原始事件持久化。

## 3. 正式路径与数据边界

正式 `ControllerPageRecovery` 的 `syncSnapshot`／`cachedDetails` → `pendingCache` → `DisplayCache.putConversation` 路径自动应用新预算；无须调用新预算 helper 才生效。缓存清洗与 `conversation`／`peekConversation` 再次应用同一规则；仍沿一个 Conversation 条目的既有 IDB 事务原子写入。容量逻辑仅选择现有数据，没有网络请求。

正式 `HistoryWindows.accept`／`replace` → `reconcileSync`／`retainDetails` → `rememberThinking`、`cachedDetails`，冷读 `restoreDetails` → 再次服务端 revision 确认，保留完整字段。B01 冷读后实际 `HistoryDetails.select/schedule/prioritize` 对已完整字段不发请求；旧未展开／未取仍沿原懒取 owner。当前投影、默认折叠、按钮资格未改。

## 4. 实际验证、版本与原始证据

开始前 FE HEAD 为 `91ad72f3898be4e6d98461f69566a76b54595290`；已有 root 未提交修补全部保留。期间 root 收敛其独立差异为 `1a906aef96ff4f089a0a371e653c1c2d855be7f3`，本包无提交。该 HEAD 的三个既有产品文件与原 91ad 一致（`git diff --quiet 91ad HEAD -- <三文件>` 成功）。最终证据是该 HEAD + 本包五文件未提交差异，准确源 SHA256 在 UI 证据目录 `identity.json`。

环境：macOS 本地 Node `v24.21.0`、Vitest `4.1.11`，项目已安装 fake-indexeddb；真实执行其 IDB transaction/objectStore，未用自建 KV 替代。合成消息／owner；无真实浏览器、服务端或设备运行。

原始证据目录：`/Users/edgar/code/hermes-secretary-web/.archive/incremental-sync-20261027/r2-cache/`。

| 证据 | 命令／观察 | 实际结果 |
|---|---|---|
| `baseline.log` | 新专属测试在未修改三个产品文件前运行：完整参数→移出窗口→同版本 Thinking-only→IDB 冷读；合法 latest200+anchor200+outside100 再来新 prefix | 2 项均失败：完整 tool_calls 丢失、新 prefix 丢失；实际类＋真实 IDB，不是源码／helper 反例 |
| `first-fix.log` | 原两反例及历史窗口／缓存相关四文件 | 62 项通过 |
| `expanded.log` | 扩展字段、版本及容量边界 | 72 通过、1 测试断言失败：把白名单清洗后的整页与未清洗原件全对象比较；差异仅 deferred_details 空数组与 undefined 属性。后将断言改为精确 coverage、sync 及消息 UID／正文，未改产品迁就断言 |
| `final-tests.log` | `npm test -- src/core/r2-cache.test.ts src/core/history-sync.test.ts src/core/history-coverage.test.ts src/core/history-details.test.ts src/core/display-cache.test.ts src/core/controller-incremental-sync.test.ts` | 6 文件／95 项通过；最后一次 2026-10-28 21:41:33 +08，耗时 1.30 秒 |
| `typecheck.log` | `npm run typecheck` | 通过 |
| `diff-check.log` | `git diff --check` | 通过、无输出 |
| `identity.json` | 最后测试后记录时间、HEAD、Node 与五文件 SHA256 | 可逐文件核验证据身份 |

专属文件 15 项（含 it.each 展开）：B01 跨窗口完整工具详情冷读＋正式懒取类不重复请求；B02 revision／代表／role／UID 四种变更；真实空和半截区别；完整 terminal 工具参数／结果和独立 tool result；B03 500+1 新前缀、旧 selector 整体退役且最新证明精确保留；B04 同 UID 落库暖／冷不双计、无切点证明拒绝、配额失败保内存且无原始事件／权限、早期阅读内存不裁；另覆盖只有一个 proof 时被淘汰及 legacy 展示壳名额。

## 5. 缺口与限制

- 本报告是开发期机制证据，不代签全轮云端审查／实际 UI 用户结果。Z03 的真实 App 跨包恢复及最终候选复验仍归 root；本包未操作 UI，也未启动其它浏览器。
- 极端场景：latest window 的 Thinking bundle 含恰好被新 prefix 挤出的最旧候选时，该窗口证明必须整体退役。缓存仍保 latest 显示壳、有效详情提示和最新 prefix，但现有 `ControllerPageRecovery.readCachedDisplay` 把 `restoreDetails` 放在 `value.sync` 条件内。root 在后续 A-FE 集成应将同 owner `restoreDetails(value.details)` 与“是否有可复用同步窗口”解耦，确保这种情况下在必要 snapshot 后仍可复用详情；本包不越白名单改 Controller。当前主路径 B01/B03 有最新完整窗口，已验证闭合。
- 未运行无关大套，未触动 root 的 Steer／Approval／Slash 测试或产品文件。未改根计划／CLAUDE。

## 6. 接口影响

新增窄接口 `HistoryWindows.retire(selector: RecoverySelector): boolean`：仅删除精确 `recoverySelectorKey` 对应的窗口（包含 receipt、cursor、recoveryId），保留其它窗口与详情提示；重复退役返回 false。之后 `loaded`／`verified`／下一次 delta base 均不再看见该 selector。供 A-FE 仅在确证 anchor_not_found 时调用；展示画面与阅读锚点的处理仍由 A-FE owner 决定，本包未自行接线。

现有 public 方法参数／默认语义保持，API／wire 无改动。新的 `historyCacheBudget` 为 `DisplayCache` 内部 sibling，不要求 Controller 引入。外部同条详情仍不多占消息名额。

## 7. 建议下一步

root 亲审五文件和对应正式路径；接收 `retire` 给 A-FE，并处理上述无 sync 时详情恢复的薄接线。集成后只定向补 Z03／A-FE 影响路径，固定完整 FE/BE SHA 与构建身份，复用本包同版本有效证据。最终 F03/F04 关闭由全轮门禁判断；本包不自行修改缺陷台账或宣称已验收。
