# Clarify 独立 UI 实现交回

日期：2026-10-14。Owner：clarify_ui（GPT-6.1 Sol high，未派生）。工作树 `/Users/edgar/code/hermes-secretary-web-clarify`，分支 `codex/round2-clarify`，基线 `ab1f4c4bd7aabc6c129610d36dabf83314b909ea`。

当前为**Root 已亲审并接收实现＋定向证据，独立分支阶段提交已完成**。提交 `3f6a45fe68144d9d8d33796f97d985336cc8160b` 已自动推送 `origin/codex/round2-clarify`；未 merge，用户另行通知后才能合并。没有在正式 5173 验收，没有启动服务、浏览器或模型，没有更改后端、Profile、库、配置、依赖定义或锁文件。不把本报告写成真实 Validation／静态 Verification 通过。

## 1. 任务依据与原生合同

- 用户 R2-C111：独立 UI worktree 交 Agent 完成 Clarify，什么时候合并由用户另通知；Root 最新流程为正式真实 Validation 先行、最后静态 Verification。
- 06 §0.1–0.5：原生 transport／runtime owner、薄客户端、短暂内存状态、既有 API 合同不变、ACK 与 Turn 完成分开、未知事实不得猜测。
- 06 §1.4–1.6：原生工具 Clarify／approval 的 user-required 状态；保现有 Timeline／Composer 语义与视觉。§3.1–3.4：REST+WS、runtime 与 stored identity 分离、原生恢复和 replay。§4.5–4.6：身份、断连、键盘、视觉和真实入口验收要求。
- 02 §1.1–1.3、§1.5–1.9、§4.3：本实现只处理原生请求的 runtime 归属，不改 Secretary identity、Notebook、Prompt、Noting、模型路由或开关机制。
- 已读取项目根 AGENTS／CLAUDE、UI AGENTS、executing-plans、autonomous-run 消息契约、snapshot-index／baseline／plan。根/规格/全局任务看板未由本 Agent 修改。

原生源码已核：

| 能力 | 实际入口/依据 | 本实现用法 |
|---|---|---|
| 问题投递 | `tui_gateway/server.py::_clarify_block` → `server_requests.send('clarify', sid, {questions}, qids=...)` | 只处理真实 `method:'clarify'` 的 server request，不从普通 Assistant 文本或工具名猜问题 |
| wire 形状 | `tui_gateway/contracts/server_requests.py` | `{id, method, params:{session_id, questions:[{qid,question,choices,multi_select}], answers?}}`；answers 只表示服务端已锁定答案 |
| 批次提交 | `tui_gateway/methods_prompt.py` 的既有 `clarify.lock`；`contracts/prompt_voice.py` | 单次确认，依次发送 `{request_id,question_id,answer}`；`status:'ok',remaining:[]` 才证明批次已结束；`expired` 只说明请求已失效 |
| 回答编码 | `tools/clarify_tool.py::_clean_answer`；Desktop `ClarifyToolPending` | 单选/自由文本为字符串；多选为 JSON 数组字符串，允许选项加自填答案；推荐标记不进入用户答案；未答问题用 `null` 跳过 |
| 取消 | `server_requests.resolve_response` | 原生同 ID JSON-RPC response `{result:{}}`；本地仅在 socket.send 成功后撤下请求，不宣称具有服务端取消 ACK |
| 超时/停止 | 原生 `request.cancel {id,method,reason}`，包含所属 runtime | 该 owner 按 ID＋runtime 撤下请求；不自行设置 300 秒倒计时，因为原生超时可配置/无限 |
| 恢复 | `session.resume`／`session.activate`／`session.events.since` 的 `open_requests` | 替换所属 runtime 的旧请求；恢复锁定答案；显式排除取消竞态、读期间新请求和旧进程快照 |

实际缺口：旧 Modal 没有 Other，长选项使用原生 select；多选逗号拼接会破坏含逗号选项；答案由未 keyed 的局部 state 管理；binding／replay 只追加 open_requests，无法清除已经不存在的请求；发送没有 pending/error/unknown 的统一 owner。

## 2. 实际变更

产品白名单内变更：

- `src/core/server-requests.ts`：一个短暂请求 owner，统一接收、stage、顺序锁定提交、直接取消响应、断连保护、快照确认、runtime 退休和取消撤销。无持久化、后台同步或第二 transcript/Turn ledger。
- `src/components/ServerRequest.tsx` 与 scoped `server-request.css`：复用现有 Button／Modal／tokens，原选择框改可点选的 radio/checkbox，附自由文本 textarea，长选项保换行；推荐标记独立显示；提供提交等待、错误和未知状态核对入口；服务端锁定的题目只读。
- `src/App.tsx`：将旧内联表单抽为正式组件，按 request ID keyed；只在已绑定的所属 Conversation 展示，New Chat／Files 不展示该请求。保普通消息、Timeline、Composer 和已有 approval 语义。
- `src/core/controller.ts`：仅改原有请求接缝。请求接收、disconnect、request.cancel、epoch 更换、installBinding、replay、answerRequest 接到同 owner；绑定 RPC 开始时记录快照界限，结束时处理真实 open_requests。当前 1977 行，未增加已达 2000 行文件的健康超标指标。
- 测试：`src/core/server-requests.test.ts`、`src/components/ServerRequest.test.tsx`、`src/components/server-request-app.test.tsx`，及既有 `src/core/controller.test.ts` 中两条正式绑定用例。

没有修改 `src/api/client.ts` 的传输协议；沿用其已经核实的 server request 收发能力。没有无关样式整理、依赖/lock 修改。

## 3. 正式路径与状态/失败处理

`Gateway.onRequest` → `Controller.serverRequests.receive` → `App.state.requests` → 所属 runtime 过滤 → `ServerRequest` 表单 → owner.stage → owner.submit → **原生 clarify.lock** → 原生 ACK。

同一 owner 在第一个异步等待前同步设置 submitting，重复点击不能发第二批；每个 ACK 才记录该题锁定，后续题只在前题 ACK 后发送。确定错误显示 error 并保留已锁定题目；不确定错误进入 unknown，禁止自动重发，用户 Check request status 经既有 `session.events.since` 读取真实 open_requests，再决定恢复可回答状态或撤下卡片。取消仍使用原生 response frame，不借助新 RPC。

断线保题目与暂存答案、禁用提交；同进程恢复与会话再访由原生快照重新确认。会话切换只改变展示，不回答/取消后台会话的问题。新 request ID 不沿用上一请求答案。请求取消时记录到所有当前在途快照，即使此前原始 frame 漏收，也不能被迟到快照复活。快照只清除读取开始前所属 runtime 的旧请求，保留其他 runtime 和读取期间新到的问题；旧 gateway epoch 快照不能恢复旧进程请求。

approval 保既有 choices／Allow once／Deny 和 `{choice}` response，复用 owner 的断连/error 保护，不转换为 clarify.lock。

## 4. 验证结果与证据

环境：现有 UI node_modules 的软链接；`package.json`／`package-lock.json` 与正式 UI SHA 完全一致；未 install/解析/改锁。新工作树 node_modules 及 Vitest 复制的 file-viewer renderer assets 均 ignored，不提交。

证据目录：`.hermes-dev/round2-verification/clarify-ui/`。

| 命令/执行范围 | 次数、实际结果 | 日志 |
|---|---|---|
| 新 worktree 首次 `npm test` | 1 次；立即环境准备失败 `vitest: command not found`，Vitest 未启动，不记为测试失败 | `focused.log` |
| `npm test -- src/core/server-requests.test.ts src/components/ServerRequest.test.tsx --maxWorkers=1` | 补既有依赖链接后 1 次，17 passed，794ms | `focused-deps.log` |
| `npm test -- src/core/controller.test.ts -t 'formal binding entrance\|authoritatively absent requests' --maxWorkers=1` | 1 次，2 passed／69 未选，203ms | `controller.log` |
| 正式 App 新用例初版放在 presentation 文件 | 1 次，1 failed／29 未选：夹具直接赋 controller.state 未发布 render snapshot，读到旧 UI；未改产品掩盖失败 | `app-scope.log` |
| `npm test -- src/components/server-request-app.test.tsx --maxWorkers=1` | 将 App 用例隔离并通过正式 publish 接缝后 1 次，1 passed，967ms | `app-scope-final.log` |
| `npm run typecheck` | 首次 1 处 TS18048（可选 previous 的收窄）；改为可选访问，定向复查通过；加入最终独立 App 测试后最终再检查通过 | `typecheck.log`、`typecheck-final.log`、`typecheck-app-final.log` |
| `git diff --check` | 通过，无 whitespace error | 本次工具结果 |

最终 **20 distinct 用例通过**，不把 69/29 未选项计为通过。覆盖含逗号多选＋自填、依次 ACK 与重复点击、partial failure 与已锁定题不重发、lost ACK 不盲重发、expired/非法 receipt、cancel send failure、approval 保留、runtime 隔离、取消/超时 replay 竞态、漏 frame 取消、旧 epoch、断连保答案、快照不解锁在途批次、正式 binding 入口和正式 App 再访。

所有重检查按 Root 串行窗口执行，无 full suite／build。没有测量 RSS 峰值，不宣称本次证据覆盖历史资源峰值；测试/typecheck 均退出，无本人遗留验证进程。

## 5. 缺口与实际限制

- **尚未在 5173 验收且未合并**。未跑真实 REST+WS/模型发起 Clarify 的端到端用户链，未做四视口、焦点/屏幕阅读器/真实 IME/移动软键盘的实机验收；jsdom 不能替代这些证据。
- 取消 JSON-RPC response 没有原生 ACK；UI 只表示本地发送后撤下，不新增伪 ACK。最终原生工具结果/Turn 由现有 Timeline 链展示。
- 原生超时/中断的 request.cancel 清卡，不伪造 timeout 倒计时或历史结果；尚待真实模型超时场景核对原生工具卡呈现。
- 暂存答案只在请求仍存在时保留于内存，跨会话再访/短断线可恢复；完整浏览器 reload 只恢复服务端已锁定答案，不把未提交问题草稿写入永久 API 缓存。
- 未运行完整旧测试包；旧有效证据不复跑。本次未修改 Secretary/后端的事实不等同其全部验收已完成。

## 6. 接口影响与集成注意

- AppState.requests 仍为原来的 `Json[]`；raw native request 保其 id/method/params，额外 ui 字段仅属于短暂呈现状态（status、stages、error、needsCheck、revision）。没有 native DTO/schema 改动。
- 新 `Controller.serverRequests` 是前端请求 owner 的唯一入口；现 `answerRequest` 保留 facade 并委派。
- 共享 controller 改动收窄于请求 owner/getter、initialize onRequest/onState、installBinding/ensureBinding、request.cancel、gateway epoch、recover 和 answerRequest；**UsageViews 的数据合并/读取接口没有改动**。后续人工合并 Usage owner 的 controller 接线时保双方最小块，不整文件替换。
- `src/App.tsx` 仅新组件 import、删除旧内联 ServerRequest、替换组件调用；其余表现与 Composer 不动。
- branch/worktree 由 Root 管理；Root 亲审接收后仅授权本 Agent 提交本分支的 9 个 src 文件，已按授权完成阶段快照与自动推送；无合并权限，不能仅因用例通过进入正式分支。

## 7. 建议后续动作

Root 已亲审报告、App/controller 正式接线、请求 owner 与表单源码，接收本次实现和定向证据；这不冒称真实验收。独立分支阶段提交已完成，按用户等待合并口径，不将它合入正式 UI。用户另行通知合并后，由唯一服务与浏览器 owner 在既有 5173/53445/Profile 上验证真实 Clarify 的单选、多选＋Other、部分失败恢复、切换/重连、native 取消/超时与小屏操作；真实 Validation 材料记录上述未覆盖项，最后静态 Verification 复核。

## 独立分支阶段提交记录

- Root 本次明确授权：只提交独立工作树 9 个 src 文件；保自动 push，不 merge/rebase 正式 main，不吸收 Usage，不重测/build；只更新本交回报告。
- 提交前：branch `codex/round2-clarify`；暂存名单恰为本报告列出的 9 个 src 文件；staged diff --check 通过；新增差异凭据模式扫描未发现；package.json/package-lock.json 无差异；现有 common post-commit 可执行且与 `.githooks/post-commit` 相同。
- 提交：`3f6a45fe68144d9d8d33796f97d985336cc8160b`，`feat: complete native Clarify request UI`；9 files changed，461 insertions，138 deletions。提交正文明确 20 focused cases/typecheck 的证据范围，以及真实 5173 验证与合并尚待后续授权。
- 自动推送：post-commit 成功，建立 upstream `origin/codex/round2-clarify`；实际 `git ls-remote origin refs/heads/codex/round2-clarify` 返回同一完整 hash，本地 HEAD／remote-tracking ref 同值。未 force push、fetch、merge、rebase。
- 提交后 UI 工作树干净；node_modules/renderer assets 为 ignored。未再运行测试/build，没有启动服务/浏览器/模型；原 20 distinct 与最终 typecheck 证据复用。
- 仍**未合并、未在正式 5173 真实验证**。Root 已将独立分支列入正式 Validation 等待项，用户另通知合并前保持隔离。
