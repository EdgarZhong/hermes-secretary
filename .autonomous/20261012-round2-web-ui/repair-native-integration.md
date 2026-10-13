# 真实集成补证续接报告

本报告归 native_integration Owner，只记录开发集成补证，不是 Verification / Validation；第二轮 Verification 禁止启动。2026-10-14 准备阶段，尚未启动服务、浏览器页、模型、测试或构建。

## 1. 对应条款与边界

最新授权按 Snapshot Index C90–C98；02 §1.3–1.6 身份、§2.5 未来 task / 必填 Schedule / 显式 instant/deferred、§3.3–3.4 原子 Snapshot、§3.7–3.12 正式工具与 Reminder、§4.3/4.5 关闭及原生 Idle、§5.5–5.6 缓存前缀与真实 carrier、§5.8–5.10 终止/Anchor、§6.9/6.17 正式投递；06 §1.4–1.7 Timeline/附件、§1.11 编辑边界、§3.3/3.5 正式 WS/Agent、§4.6 IAB实际入口。行号已按当前章名核对。

清理硬门禁不实施；Memo 首段、事实来源与消费机制不动；user_reminder 不传 delivery_mode，secretary_task 必须显式 instant/deferred。不写产品、Prompt、规格、核心文档或 plan，不提交、不派生，不操作用户 5173/53445、视觉树或既有测试数据。

## 2. 当前准备变更与版本

仅新增本报告和 ignored `native-integration/preparation.json`。后端 HEAD `24510d1c7c3b8dfc95b6d0626be30f090561fa30`，前端修复树 HEAD `002f7a27fcf7313491f0301e143df7d3b6148088`；两树均有 Main/其他 Owner 已授权未提交修改，不能用 HEAD 单独代表源版本。当前关键源码逐文件 SHA 见准备 JSON。

旧 live manifest 对当前树的变化：后端 secretary/noting_tools.py（Main 新最小 Prompt），前端 controller.ts 与 verification-fixes.test.tsx（Main Usage 微修）。旧附件实现接缝 hash 未变；旧 Prompt / 新 Prompt 证据不能混用。

## 3. 服务、profile、PID 与 IAB 能力

- 只读 lsof 确认 53449/5183 无 LISTEN；定向 ps 未见对应 dashboard / serve-live / rpc-live 存活进程，本 Owner 自有 PID 为零。未结束任何旧 Owner 或用户进程。
- 旧隔离 profile：`.hermes-dev/round2-verification/frontend-fixes/live-integration-20261014/profile`，workspace 同目录下 workspace。setup 指向获授权 config_source `.hermes-dev/round2-attachment-live`，native custom DeepSeek / api.deepseek.com / chat_completions / deepseek-flash；凭据文件存在，未输出内容。旧 profile noting_idle_seconds=20（满足至少15秒）。未复制旧 state、未修改 DB。
- 当前 CUA `getState` inventory 确实列出 `Codex In-app Browser` id=2、type=iab、tabs=[]。仅inventory，不选用户 Chrome、未创建 tab、未改权限。旧报告“仅Chrome”是旧工具环境事实，不能覆盖本次能力确认；当前尚未执行 IAB DOM 操作。

## 4. 可复用的已有实际证据

旧 Owner 证据目录 live-integration-20261014。该 Owner 新 RPC 两片 4,194,400 bytes 上传、attachment_info stat、partial abort 已成功：upload_id `09a961ca-cb35-4ec0-a216-2fc5c2653aeb`，源与落盘 SHA 均 `b721fa457dc55d0699cb54a98693d7b13fe29d4990f79949161de816c1fd8e80`，首尾 HERMES_R2_NEW_RPC_HEAD_20261014 / HERMES_R2_NEW_RPC_TAIL_20261014。

runtime `85c42a4c`、stored `20261014_013750_6e40a5`、ref `conv_e5f550388ffa43489c9014cc0a00a651`。只读 DB 核真实 Main terminal 两次工具及 exit0，stat / head64 / tail64 与实际最终 Assistant 存在；Main 交回 terminal Assistant UID `b372e58c519f4991a221b1c161b7bf46`。旧 native WS 有 message.complete seq1200/status complete，可复用真实模型附件结果，不能重复上传或重跑模型读取。

旧 Noting child `noting_dc2f29f62e794253` 已查实际 session_history 来源，但 DB child 仍为 running、Snapshot0、Registry0；这不是成功 Notebook 提交或 Instant 链。旧 browser-events-dom.json 最后 seq831/message.delta、active=true/receiving1，比真实终态早，不能冒称终态 DOM 已闭合，也不证明 IAB。

BE59/BE28/C84 33distinct、现前端受控 WS、长流性能、Undo 和容量证据按已有报告复用；不重跑大包、500MB、Undo、性能或完整门禁。

## 5. 剩余正式路径与执行计划

等待 Main 完成当前 build 并正式释放资源；此后作为唯一浏览器/模型重任务方，使用 53449/5183 与上述隔离 profile，启动当前 source/new Prompt。先只读核原生重启后 unfinished child 的真实状态，不 SQL seed、不伪造 carrier、完成消息或改 child status。

若原生恢复没有合法可继续 trigger，IAB 正式 UI 最小一条新 Main 输入建立事实与真实 Anchor，要求未来 secretary_task（显式instant、有效Schedule），沿正常 Main→Idle20s→Noting→Snapshot→Registry→自然到点→原生 COMMIT→持续WS→IAB DOM，保存同链 sourceUID/ref/DB row+seq、模型/工具请求和DOM先于Thinking证据。之后用最小真实事实推动已确认done→schedule_update自动回pending，复用原工具/owner和Snapshot事务；不要求模型另补status。避免重复模型链，先观察再决定必要后续输入。

旧 observe.ts 在每次事件保存完整history/live与DOM，累计数组并反复序列化全量，8.17MB现存文件不应直接续用。本 Owner 使用白名单下有界 observer：仅 source/start/Thinking首次/terminal/必要DOM状态/差异时间，截断文本、固定容量、有限次数落盘；持续 WS append JSONL，敏感token/凭据不落证据。末尾断 observer、关闭自有tab/连接/服务并释放数组，记录实际PID与退出。

## 6. 缺口、接口影响与完成判据

准备阶段不宣告真实 Instant 或当前 Prompt 通过；未确认旧 child 重启关闭/恢复事实，未产生当前源版本 IAB 证据。服务重启只有已确认隔离且无活动工作才能做，不碰用户服务。当前 IAB 可用但实际DOM操作尚未证实。

没有产品/API/权限/Schema变化。完成需同链真实sourceUID/ref/DB seq、实际Hermes模型请求、IAB源先Thinking/终态及时且不重复、当前Prompt下futuretask/Schedule/自动状态结果，明确fixture与实际模型差别、源hash、边界和未覆盖；开发结果不代替独立门禁。

## 7. Main 接收建议

可先独立接收准备阶段：已有附件真实模型结果复用，当前IAB可用，53449/5183没有监听，当前Prompt与Usage差异已辨认，剩余集中为unfinished原生重启事实及新Prompt/Instant/IAB完整链。收到正式资源释放后继续，不自行开启并行重任务。
