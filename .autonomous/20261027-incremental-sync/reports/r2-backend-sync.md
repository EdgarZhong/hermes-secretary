# 第二次迭代 A-BE：F05／F06 实现交接

## 1. 对应条款与版本

本包对应 F05／F06、A04–A06；依据 06 顶部 C0–C3、D01／D04／D15、S05／S11／S14，以及保留的 R3.2–R3.8 有限 D0／S／D1 原文。已读本轮 plan、snapshot-index、baseline、根 AGENTS／CLAUDE、executing-plans 与 autonomous-run 消息交接条款。

原云端报告 SHA256 已核为 `3546c0e1138804f25a4e24fcc8ca5d9f3dd1486399445b9300135a0f2b5b24bf`；其结论固定于 BE44eb0be／FE91ad72f，本包没有把它当作当前版本通过证据。已核 §1、§2–3 相关要求、§4、§5.5–5.6、§6 对应反例与整改计划 §2.2／§4 映射。

实施基线：`b837b1665c965520f60e49f2a25725b3b780545d`，分支 `codex/incremental-sync-20261027`。本包未 commit／push，证据以该基线加本报告列出的四文件补丁与哈希固定；其他 Agent 的 dirty 保持。交回前共享 HEAD 已由主会话推进到 `c202feda47b3725bbc57a74e8a92c01a62eacbe4`，本包四文件 SHA256 未变，独立 index 对固定 b837 基线只含这四文件。平台 macOS Darwin25.6 arm64，既有官方 PM `.venv` CPython3.14.7；未改环境／lock。`hermes_state_messages.py` 最终1984行，未越过2000行阈值。

## 2. 实际变更

- `tui_gateway/recovery_view.py`：以 `_thinking_prefix` 代替整个 bundle 相等。真实 source 必须相同；D0 的 order 是 D1 的前缀，所有已有 Thinking 行内容／身份／顺序／position／完整详情 revision 保持。新增候选必须按逻辑位置递增且位于 D0 全部持久消息切点之后。旧的非 Thinking 行在窗口外新增 reasoning 也不被误作合法尾追加。窗口 proof、detail_digest、Turn／租约与 native cut 校验保留。
- `hermes_state_messages.py`：在既有 `before_rewrite` 接缝记录将被原生 repair 处理的行的 owned-payload digest，保留 Secretary 原有 branch-source preserve；本事务末尾仅比较这些准确行的最终 digest。事务成功返回后，仅存在实际变化时调用既有 `notify_history_changed`。未用全程 `total_changes`，未按“尝试更新过”发通知。
- 新增独立测试：`tests/tui_gateway/test_history_sync_append_boundary.py`、`tests/tui_gateway/test_native_repair_history_notifications.py`。

没有修改原生 transcript_repair、watcher、协议／schema／API、U20、Gateway cache、前端、质量规则或核心文档。

## 3. 正式路径与受控边界

F05：正式 FastAPI REST `GET /api/sessions/stored/messages?recovery_view=1&history_sync=1` → 服务端真实 cursor／receipt → 正式 `server._methods['session.activate']`，请求 `sync_version=1` → 真实 SQLite D0 → 原有完整 native snapshot S → 第二连接实际提交写入 → 真实 SQLite D1 → 原有证明／投影／cursor delta／native cut。测试 wrapper 先完整调用原 snapshot，仅在其返回边界插入外部写入；没有替换待测读写或证明机制。活动测试使用原生 source observer／Turn lease／output_state 及既有事件流，未调用模型。

F06：第二个 SessionDB 的正式 `append_messages_batch` → 原生 `resolve_and_repair_transcript_batch` 的 CAS／legacy blank-row repair → 原 `_execute_transcript_write`／`_execute_write` commit → 原 `notify_history_changed` 信号文件 → 原 `_sessions_sig`／`_broadcast_watched_changes` → 实际产生 `sessions.changed`，仅在广播出口记录结果。没有手工发送事件、显式 refresh、新 Turn 或额外 append 来唤醒 watcher。测试从第二连接证明内容已改而消息数和 session-table signature 保持不变；提交前回调中独立连接仍读到旧内容，通知尚未变化、watcher 无事件，提交后才观察到新内容与通知。

watcher 由测试按明确 tick 调用其生产检查入口，未启动永久后台线程或真实前端。UPDATE 拒绝负对照使用 SQLite trigger `RAISE(IGNORE)`，回滚使用正式 before_commit 回调抛错；其他持久化机制均真实运行。

## 4. 验证结果与原始证据

原始记录统一位于 `.hermes-dev/incremental-sync-20261027/r2-backend-sync/`，全部 Python 测试使用 `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh`。

| 证据 | 执行范围／结果 | 耗时 |
|---|---|---|
| `baseline-targets.log` | 在 ignored `baseline-tree/` 用 git archive 导出完整固定 b837b166 基线、只复制新增测试，筛选两个目标测试函数：Thinking 追加4例与正式 CAS 通知2例全部失败，正好复现 F05／F06 | 每文件约1.7秒；完整原始失败输出保留 |
| `targeted.log` | 8文件132项通过：两个新增文件、history_sync、recovery_view、change_watcher、change_watcher_sessions、append_messages_batch、unaddressed_rewrite_identity | 13.9秒，10 workers |
| `final-tests.log` | 最终新增两文件22项全部通过；在原132项后把 digest 比较移至 before_commit 之后，并补拒绝 UPDATE／提交前观察；之后仅整理测试 fixture／分发表，最终再验证22项 | 5.0秒，10 workers |
| `quality-final.log` | 独立 `GIT_INDEX_FILE=.../check.index`，从 HEAD 建 index 并只加入本包四文件；正式 `.venv/bin/python scripts/check --staged --only ruff,health` 两检查通过，health 28文件对 e1b124d，0 blocking／advisory；共享 index 未动 | health2.9秒 |
| `package.patch`／`sha256.txt` | 可复核的四文件完整补丁与产品、测试、lock及核心日志 SHA256 | 非提交快照 |

最终新增场景：

- A04：idle／active × 首屏内／首屏外210条 padding，带已有详情，真实同 source 尾追加 reasoning，首轮即完成，原 Thinking revision及可见详情保留。
- A05：旧 Thinking 改文、删除、重排、source变化、同 UID 换代表，各覆盖一次变化后第二轮重新证明成功，以及两轮持续变化明确拒绝；另测首屏外旧非 Thinking 行新增 reasoning，拒绝伪尾追加。
- A06：digest CAS 与 legacy blank-row repair 同计数实际改文，均在 commit 后到达 watcher；no-op flush、stale CAS 采用并发 winner、legacy 同值写、SQLite 拒绝 UPDATE、实际回滚均不通知。

初期 `before.log`／`before-corrected.log`／`after.log` 包含重排夹具的字段／预期顺序修正过程，已保留，不作为干净修前证据；干净修前依据为独立基线导出的 `baseline-targets.log`。首次 `quality.log` 的失败仅为新增测试 fixture 导入遮蔽及场景条件链，已修代码，未加豁免／改规则。

关键 SHA256：

| 文件 | SHA256 |
|---|---|
| `hermes_state_messages.py` | `c9c01096ec6e15cb5637c26bbf513f92552c752629de7cec1e2929395e51627f` |
| `tui_gateway/recovery_view.py` | `6c38a780971c0a1836bb4dd174a2b56f29bb365aee8be043d562e9d39fd74068` |
| `package.patch` | `1557a606ddd642879c46eb27c96feede735446a11be0be18d277c7783b73db42` |
| `baseline-targets.log` | `8594b3430c265f73d04691000c9035bdf7d8aa45e55e56ca02873f13eaff61f6` |
| `targeted.log` | `d3a42baa79ec51fd59e939e7b4f25d458d3c8c1fe007ecd3a3726091e4c66498` |
| `final-tests.log` | `fa36294999abd2566e9a71261102fc9aba7fda6cb1aa309e59a2e34053a657ff` |
| `quality-final.log` | `09804a69f63bd48cb47cd84753b2bdb60284e50808a587a8fa85caf978ec875c` |

## 5. 缺口与结论边界

F05／F06 的后端正式入口反例及负对照已取得，本包可交主会话 review。没有进行 UI、浏览器、Android、真实网络 WebSocket／生产模型、Linux 或真实渠道发送验证；A06“同一实际页面由事件更新”的前端消费段仍由主会话最终 App 联调接续，不能仅以本包 watcher 证据宣布全 A 包或整轮通过。原生 runtime snapshot／事件使用正式机制，但模型内容与运行对象为既有受控 fixture。

本包仅允许 D1 对 D0 Thinking bundle 增加新尾部；500条范围移动导致已有候选退出、旧 source 消失等仍走既有拒绝／有界重证明，不把删除／淘汰误作此前事实未变。没有扩大本轮恢复重试次数。

## 6. 上下游接口影响

`append_messages_batch` 的签名、默认返回 int、插入计数、chunk 行为、调用方式和错误传播保持；内部事务 callback 仅向原 `_execute_transcript_write` 返回本地 tuple，由本方法解包，不影响其他 writer。通知沿实际 DB 路径，未增加新的 wire 字段或 Profile 来源。原 before_rewrite Secretary preserve 仍执行。

前端收到的 `sync.latest_thinking` 形状、cursor、权威 order／revisions、native snapshot／stream cut 均不变，只修正合法尾追加被错误拒绝。root 可直接接既有 A-FE／B-CACHE，无生成协议更新需求。

## 7. 建议后续动作

主会话亲审这四文件的范围、正式接线和证据，更新其独占的计划／CLAUDE；最终 App 以同一 document 保留旧画面，安排同 source Thinking 尾追加及无附带 append 的正式 CAS，观察真实 watcher事件使当前页面取得新 revision／内容。然后合并其它包形成新的固定 BE／FE SHA，再交用户指定云端审查与独立 Validation。本包未执行部署、commit 或 push。
