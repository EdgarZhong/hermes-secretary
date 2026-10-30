# 前端交接报告 · Force 完成恢复

## 1. 对应要求与阅读依据

U01–U04、06顶部C0–C3的D01–D05／D12／D14／D15、S03–S14、P01–P09；07顶部2026-10-31和2026-10-28的Main结束／Force／FM独立契约。已完整读取executing-plans和autonomous-run子Agent交接契约、BE根AGENTS／CLAUDE、本轮索引／基线／计划及FE根AGENTS；FE无CLAUDE，动态记录复用BE。本包不提交、部署或派生。

FE分支`codex/force-completion-20261031`，基于`5f974b3bd70a67180039067df1e3b0356532e3cc`；保留全部既有`.DS_Store`。root负责五个版本文件0.1.10，不归本包。执行环境macOS／Node v24.21.0／npm 11.19.0／Vitest 4.1.11／已安装lock环境。

## 2. 实际变更与根因归属

- 产品仅改`src/core/controller-pending.ts`：当前owner旧`live.recoveryError`尚在、Pending结果因此不能采用时，拒绝本次读取并交既有自动重试，而非return一个未采用snapshot冒充成功。不使用Noting状态判Main，不放宽完成回执、切点、权限或缓存资格。
- 新增`src/core/controller-force-completion.test.tsx`和`src/core/fixtures/force-completion-native.json`。原生普通／Steer两分支的pre／active／finished REST、详情、真实RPC完整snapshot及事件取自BE正式`test_turn_end_force_keeps_main_settled_while_child_runs`导出，原件位于BE`.hermes-dev/force-completion-20261031/native-force-wire-{ordinary,steer}-base.json`；受控Provider，真实Loop／SQLite／handler，不造成功receipt。
- 首要后端根因由backend包修复：Force FM尾追加破坏共享结果末尾推断的Main final身份，产生错误完成证明，前端严格拒绝恢复，故新尾部没有成功缓存交接。
- 独立前端根因已复现：错误封套`revokeControls`清除Pending；下一次自动恢复中，Pending先于新cut返回，旧`recoveryError`令其跳过adopt但资源记成功。新cut随后清错误，`availability.ready=true`却`pendingSnapshot=undefined`，Send永久disabled。修前`force-tests-5.log`和`retry-state.json`记录；改成真实失败／重试后同正式路径自动解锁。
- 正常连接后台失效已存在continuity机制；实际Main complete令spinner退出，Noting active和finished只驱动Secretary区域。本包不再新增平行资格或视觉行为。

## 3. 正式接线路径

`Controller.event` → `observeControl`／`sessionEventEffects` → `refreshHistory` → 当前`ControllerPageRecovery.start(history-invalidated)`；正式REST窗口与`session.activate(recovery_view)`完成历史／有限流切点对账，React布局确认后`DisplayCache.putConversation`原子保存窗口、游标、最新Thinking及详情。Framework保留其真实持久UID，位于Main最后回复之后。

Pending沿`recovery-resources.pending` → `Controller.readPending` → `ControllerPending.read`；旧错误阻止adopt时现在抛出可重试读取失败，PageRecovery既有资源退避在新cut已确认后再次读取，正式adopt Pending后才恢复Composer资格。断连、错误封套、owner／epoch证明仍严格拒绝；Noting结束不授予任何Main权限。

## 4. 验证与证据

证据原件：FE`.archive/force-completion-20261031/`。

| 证据 | 范围／结果 |
|---|---|
| `baseline-tests.log` | 改前现有4个正式恢复相关文件201项通过，未为基线跑大套 |
| `force-tests-1.log`–`force-tests-6.log` | 保留初始夹具导入／matched游标输入问题、断言修正，以及真实Pending未采用仍报告成功反例；不把夹具失败冒称产品失败 |
| `force-tests-7.log` | 最终普通／Steer Force＋Pending／Steer接线3文件22项通过 |
| `final-tests.log` | 执行方frontend；最终前端本包源码＋最终真实夹具；9相关文件273项通过，7.40秒，执行1次；复用既有失败保留日志 |
| `final-typecheck.log` | `npm run typecheck`通过 |
| `ts-health.json` | 用主仓冻结`ts_units.mjs`和现有TS解析：controller-pending最大CC15／嵌套4／函数25行；新测试最大CC20／嵌套2／函数19行；无新增超限；`git diff --check`通过 |
| `controller-{ordinary,steer}.json` | Main complete且Noting active，Send可用；最后真实Assistant和FM分别进入IDB，最新Thinking为完整Native reasoning；Noting结束后资格保持 |
| `cold-{ordinary,steer}.json` | 新Controller从真实IDB先显最后回复／FM及详情；完整服务端cut尚未返回时禁写；服务端对账后Send可用 |
| `error-then-auto-retry.json` | 真实断连禁写，错误封套不以Noting结束解锁；错误消失后同页自动重试，Main idle、Pending有正式snapshot，Send可用，无Toast |
| `app-{ordinary,steer}.json`／`app-dom.html` | 正式App DOM中主spinner=0、FM可见、Composer无恢复行，Noting仍active，后继Send与Compact到达正式调用入口 |

测试仅受控HTTP／RPC传输、时序与不相关读；生产Controller／PageRecovery／App／真实IndexedDB机制原样运行。回放选择后端导出的完整snapshot，不自行补`persisted_turn`或成功标志。App的后继Send使用明确RPC拒绝、Compact使用aborted回执，只证明已恢复并可正常派发；真实后继受理与Compact成功由backend／隔离真实浏览器夹具补齐，不冒称此处模拟响应等同成功。

已流式但未被完整证明的半截不得写缓存：本包未修改缓存资格；`controller-incremental-sync.test.ts`既有真实native snapshot前缀＋后续未确认chunk反例纳入本次273项，核实后续半截只在内存、IDB仅保有限完整前缀，冷缓存不恢复running权限。

## 5. 隐藏IAB结果与限制

本Agent自建`iab visible:false` tab1，实际App入口`http://127.0.0.1:5201/chat/force-ui-fixture?profile=default`／隔离BE8191；未触用户页面、桌面或外部浏览器。SDK屏障及断网由夹具API控制，实际Send／Compact／详情展开均由真实App UI执行。浏览器证据汇总`browser-results.json`，正式链／环境见BE ignored integration/README与runtime.json。

| 实际用户路径 | 结果与证据 |
|---|---|
| 实际Send→Force child held | Main真实流式完成、receipt.complete=true、最后Assistant row18和独立FM row19落盘，Secretary仍active；`browser-force-held-stats.json`／`browser-held-ready-state.json`／`browser-held.jpg`证明Main无spinner、Composer无恢复行且有草稿时Send可用 |
| 真实浏览器IDB | 直接从`secretary-display-v1.snapshots`只读取得2个条目，Conversation条目同时含精确tail、FM及完整`Controlled SDK reasoning; real native loop.`；`browser-real-idb-before-cold.json`，非内存cache断言 |
| 用户主动冷document刷新 | documentId从`7d179a68-aa39-41d8-a05d-19184a099f16`变为`b84c4327-87cc-4a7e-89df-6f21f73da502`；相同尾部两UID／完整Thinking恢复、草稿保持，child仍running，Send可用；首次真实提交到底9667+497=10164；`browser-cold-state.json`／`browser-cold.jpg` |
| child held时实际后继Send | App实际输入、点击Send、原生Main完成，真实row21 user与row22 Assistant `Native Force fixture response 2. Tail marker FORCE-NATIVE-END-2.`落盘且新receipt完整；`browser-followup-stats.json` |
| child held时实际Compact | App `/compact`实际调用`session.compress`，仅摘要SDK受控，原生活动上下文由21条收敛为1条；child仍active；UI及时显示Compacting后回12%并清空命令草稿。完整历史沿原契约保留。`browser-compact-stats.json`／`browser-compact.jpg` |
| release child后收敛 | 真实finish_noting／Snapshot提交，球idle、Main idle、无spinner、无恢复提示，压缩后Note以新Framework row26独立出现；`browser-finished-state.json`／`browser-finished.jpg` |
| 真实断连→同页恢复 | 夹具disconnect时Composer Connecting、Send禁用、正文和草稿保留；reconnect自动回ready、Send可用、零主spinner。前后documentId同为`b84c4327-87cc-4a7e-89df-6f21f73da502`，无reload；`browser-disconnected-state.json`／`browser-reconnected-state.json` |

夹具迭代如实保留：初次将session.resume误转activate，defer_history被正式合同拒绝；维护者改用正式resume并只重启隔离BE后，原document自行恢复，未为该错误修改产品。后续发现fixture未承接生产WS外层gateway.ping，周期心跳请求经核心方法表报unknown，期间正文／草稿保留并真实禁写；已交维护者补生产等价传输接缝。上述正常关键路径、明确controlled disconnect／reconnect均已独立取证，不把夹具遗漏当产品缺陷或隐去其边界。

Android设备／真实模型／微信外发未执行，不冒称通过。前端错误封套→新cut→Pending先返回的稳定竞态由正式Controller／App＋真实IDB测试构造，真实浏览器夹具未手造incomplete/receipt。

## 6. 接口影响

无API／Schema／缓存格式／权限／视觉变化。新增错误文本只作为内部读取失败供既有恢复单行投影为Pending重试，不新增Toast或用户门禁。版本五文件由root另行集成，本Agent未改动。

## 7. 建议后续

root已亲审产品和273项阶段证据，已统一提交前端`6c132a4`并构建0.1.10；本Agent未提交／部署。整包实现、真实IDB和隐藏IAB关键路径证据已齐，建议接收后进入本轮独立Verification／Validation；夹具ping补齐后的长稳／异epoch证据可沿相同被动采样补充，不改变产品包。此报告不声明整轮或Android设备验收完成。
