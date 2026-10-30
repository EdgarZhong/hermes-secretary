# Validation：20261031-force-completion

## 1. 结果概览
验收者：独立 force_validation Agent；日期：2026-10-31。依据为本轮 snapshot-index.md、baseline.txt（`56d0aefa0a174a861e67b17efd4d21f068053457`）、U01–U07、07 顶部两项确认及相关生命周期、06 C0–C3 的本故障适用数据／状态／操作资格。已完整读取 autonomous-run、real-user-acceptance 及模板；AGENTS、CLAUDE、plan 已读，计划仅作线索。

候选 BE `ef9051f2f5a51d2ed95e27c969848d0f9823992b`／FE `6c132a44a56fab8a72ddc6d51354d9923e2b78cb`。入口 `http://127.0.0.1:5201/chat/force-ui-fixture?profile=default`。范围：本次 Main 结束→Force→Framework→恢复及后续操作故障；不重新验原大轮全部 Android／认证／微信能力。主会话先过目S01→S03→S02→S04→S05→S06→S07，再于环境恢复后执行。**独立Validation通过：7个适用场景通过、0失败／未执行／阻塞，1个发布职责边界有依据不适用；本次产品用户验收门禁关闭。** 实际操作时间约2026-10-31 01:16–01:20（Asia/Shanghai）。生产发布／新 APK 交付仍由root随后完成，不以本验收、Verification或构建代替发布事实。

## 2. 环境与准备
实际 App＋正式 Controller／Loop／DB／Force／Framework／恢复链；依赖使用合成模型 SDK、合成 Profile roster/bootstrap 和本地 WS。只允许 loopback，外部临时 HERMES_HOME、Git root 外 terminal.cwd；不访问生产模型、凭据、用户数据，不外发。环境说明见 `.hermes-dev/force-completion-20261031/integration/README.md`。测试数据仅合成 Conversation；允许合法 SDK hold/release、usage 边界和断网准备，不修改 receipt、admission 或完成事实。

UI 仅使用本人新建 Codex 隐藏 IAB（iab、visible:false）；不操作桌面、外部浏览器、可见页或既有用户页。证据写 `.hermes-dev/force-completion-20261031/validation/`，产品代码只读。窄窗口呈现不代表 Android 实机；受控 SDK 可证明产品生命周期与结果交接，不能证明模型内容质量或真实外网服务。

执行前只读核验：两仓 HEAD 与候选一致；BE 仅现有报告／核心状态 dirty，FE 仅用户 .DS_Store，不触碰。首次 GET `http://127.0.0.1:8191/api/fixture/stats` 返回连接拒绝（curl exit 7）；root确认旧执行器回收后，以同一合成HOME恢复自身服务，未杀其它服务。新runtime记录候选准确HEAD、BE62514／FE62515；独立逐文件SHA比对8个BE／15个FE正式读取源全部匹配（`14-evidence-summary.json`）。HOME实路径 `/private/tmp/hermes-force-fixture-e9ZGyA`，初始Main idle／Noting idle、SDK调用0；合法成功压缩边界row23、活动上下文为摘要row23与完成Note row26，无本区间Force占用。环境准备原件 `integration/validation-root-ready.json`。

UI为本人自建隐藏IAB tab1，1280×720。合法复用已有合成DB及同origin浏览器持久缓存／草稿；未清全局浏览器数据。首轮原草稿被`typeText`追加，实际输入如S01记录；随后用setValue精确填写。本人观察并保存AX／截图，CDP只读调用夹具被动sample及真实IndexedDB，未改Controller或权限。新增依赖故障仅对`session.steer_pending_snapshot`返回显式错误，不手造成功snapshot。三个documentId为首次`101e1be9-08ac-4846-8029-0c3c26056dd2`、S03冷启`0c7e993b-6853-4a2e-9ade-36b5882116f7`、S07末冷读`523efe84-42ca-41e1-ba73-3a551114ca92`；S05/S06恢复始终为第二个document。结束已关闭本人tab，其它页面未动。

## 3. 用户目标与场景覆盖
| 目标编号及冻结依据 | 完整场景编号 | 场景类型与起点 | 数据/顺序选择依据 | 当前执行结果 |
|---|---|---|---|---|
| G1 正式 Main 结束后才 Force，FM及时可见且不续开Main；U01/U02、07 10-31及10-28 | S01 | 主流程；新成功压缩区间、Main/child idle，实际Send | Main SDK先hold，观察运行中无新Force；release后以唯一合成尾部辨认完整回复和FM | 通过 |
| G2 Main已结束而child仍活动也能正常操作；U01/U03、06 D12/P03/P05 | S02 | 衔接；S01的Force child held | 在child未结束时实际再次Send，证明背景Noting不锁Main且不重复起Force | 通过 |
| G3 刷新后回复尾部、FM及已取详情可恢复；U04、06 D01–D05/S02/P06/P08 | S03 | 冷恢复；S01结束、child held，在S02之前 | 实际刷新同一自建隐藏页；比较完整尾部标识、FM、详情及恢复结束后可操作性 | 通过 |
| G4 压缩独立于Force整理且结束后可继续操作；U01/U03、07 10-28、06 S14/P07/P09 | S04 | 主功能交错；S02结束、Force child仍held | 实际Compact，须有真实removed>0；不能等待child，也不取消不可取消Force | 通过，7行真实压为1行，净移除6行 |
| G5 child完成发生于断网时，同document自动恢复且无永久Restoring；U03/U04、06 S03–S05/S08/P02/P04 | S05 | 中断续做；S04后、child held | 先写未发送草稿、断网，合法release-child；恢复网络后核同document、草稿、业务idle、历史／FM及按钮 | 通过 |
| G6 必要Pending读取失败不得虚报恢复成功，恢复后后续操作；06 S08/P03/P09、本轮FE修复影响 | S06 | 失败恢复；合法已结束Main／FM历史 | 用依赖层使真实Pending读取失败，观察Retrying／未授予动作，再恢复并同页自动收敛；精确旧recoveryError竞态复用同版本机制证据 | 通过，失败代表与机制证据组合边界见S06 |
| G7 故障恢复后完整后续旅程；U01/U03/U04 | S07 | 完整旅程收尾；S05/S06恢复完成 | 实际再Send并核唯一受理、回复完整、主按钮可用；再冷读核持久结果，无自动重放 | 通过 |
| G8 生产保护及发布交付；U05–U07 | S08 | 运维边界；当前候选未发布 | 本验收只核隔离边界；真实发布与原签名APK交付由root在门禁后执行，不提前签通过 | 有依据的不适用：本Agent没有发布职责，后续交付由主会话独立核验 |

枚举按生命周期分为运行中、Main终态且child活动、child终态；按恢复分为连续在线、新document、同document断网及必要读失败；按用户动作覆盖Send／Compact与未发送草稿保留。顺序为S01→S03→S02→S04→S05→S06→S07，保留Force区间和真实压缩历史。重复Force、Steer、严格拒绝与竞态机制可复用同版本有效证据，但不代替上表实际用户结果。原大轮的异epoch、owner切换、Android、微信与真实模型细分不因本故障重新全量执行；必要关联机制核同版本证据与影响范围，新增实质异常再扩展。

## 4. 详细场景与执行结果
所有场景候选版本与第1节一致；各场景预期均在操作前落盘，未因实际输出降低要求。下述证据文件均相对BE `.hermes-dev/force-completion-20261031/validation/`，PNG为本人实际界面，JSON为被动页面样本／真实后端读数；完整39份本人document被动样本在`14-independent-dom-samples.jsonl`，摘要在`14-evidence-summary.json`。

### S01 Main结束、Force及时独立显示
- 意图／要求：G1，U01/U02。
- 起点／输入：维护者确认成功压缩后的无Force占用区间、Main/child idle。arm-force自定义完整尾部 `VAL-FORCE-END-20261031`，hold-main；UI输入“验收：完成本轮合成回复并保留末尾标识。”点击Send。
- 步骤／观察：Main held时检查运行中、无本轮FM／child；release-main后观察流式到终态、完整末尾、Force FM与球；对照正式receipt与事件仅为辅助。
- 预期：Force仅在Main结束之后出现，FM及时可见且只新增一次；Main停止转圈、恢复提示自行结束；child保持活动，Main为idle；不因FM启动Main。
- 实际／证据／时间：01:16–01:17。held阶段真实Main running、Stop可用、Noting idle、receipt为空、无child SDK调用；release后完整回复`独立验收完整回复。VAL-FORCE-END-20261031`，用户行27／final assistant28／Force FM29各有独立UID。FM展开为容量接近上限及已派Notebook任务提示；Thinking全文`Controlled SDK reasoning; real native loop.`。Main inactive／idle、recovery committed且availability ready，填写草稿后Send可用，球running；真实receipt仅rows27/28、complete=true，未把FM29算Main尾部。证据`01-main-held-stats.json`、`02-force-held.{json,png}`、`02-force-held-stats.json`。
- 结论及偏差：通过。首轮实际输入为既有合成草稿`Draft retained across reconnect after Force finished`追加计划输入，原因是typeText保留原值；内容仍为获授权合成输入，不影响生命周期判据，未更改服务端完成事实。

### S02 child活动期间后继Send
- 意图／要求：G2，U01/U03。
- 起点／输入：S03恢复完成，真实Force child仍held；输入“验收：背景整理期间的第二次用户请求。”。
- 步骤／观察：核主按钮可操作，实际Send，等待完整回复；对比本次user／assistant身份及child／Main活动。
- 预期：一次受理并完成，无重复Force、无限转圈或Restoring；child独立继续活动，不借其idle解锁Main。
- 实际／证据／时间：01:17。实际Send后唯一user31／assistant32，完整回复`Native Force fixture response 2. Tail marker FORCE-NATIVE-END-2.`。Main再次idle且availability ready、无恢复提示；Noting仍active、SDK child start总数仍1，未起第二轮Force。证据`04-followup-complete.{json,png}`、`04-followup-stats.json`。
- 结论及偏差：通过。空草稿时Send禁用是正常规则；S04前再填命令即可操作，不据空草稿误判锁定。

### S03 刷新后末尾、Framework与详情恢复
- 意图／要求：G3，U04。
- 起点／输入：S01终态、child held；记录最新完整回复与真实FM，展开Thinking并完整读取。
- 步骤／观察：刷新本人隐藏IAB，比较新document与缓存／服务端对账后的尾部、FM、Thinking；等待必要恢复完成，填写草稿检查Send资格。
- 预期：已落盘完整末尾与FM都能重新显示；详情不变半截或假空；child活动不造成永久恢复；新document按冷启到当前末尾，不把缓存授予写权限。
- 实际／证据／时间：01:17。本人tab.reload产生新document，初始先显示恢复中，随后自行committed／availability ready；完整末尾与FM29恢复，重新展开Thinking得到同一完整全文，Framework同文；刷新前草稿保留、Send可用且球仍running。末尾与FM身份保持28／29。证据`03-cold-restored.{json,png}`；末次真实IDB导出`13-real-indexeddb.json`保有相同origin/profile/storedId、完整尾部／Force FM／完整reasoning，`14-evidence-summary.json`独立检出均true。
- 结论及偏差：通过。正常终态Thinking／FM冷启折叠，按原规则重新展开核内容；未把缓存当动作权限。

### S04 child活动时实际Compact
- 意图／要求：G4，U01/U03、07压缩解耦。
- 起点／输入：S02完成且真实Force child held，有可压合成历史。
- 步骤／观察：通过App现有Compact入口操作，观察Compacting与原生完成；辅助核removed>0、新boundary及child仍活动。
- 预期：Compact不等待也不取消Force；成功后退出压缩／恢复提示，主操作可继续，历史按新权威顺序而非复活旧缓存。
- 实际／证据／时间：01:18。在实际Composer输入`/compact`点击Send；正式`session.compress`进入Compacting，随后退出并回到Context12%，Main idle、恢复ready。真实压缩前当前活动DB行7（23/26/27/28/29/31/32），压缩后仅摘要33，净移除6；SDK仅辅助摘要返回可控，算法／持久化真实。期间Force child始终active，未release、未取消；UI有正式Compaction卡。证据`04-followup-stats.json`、`05-compact-stats.json`、`05-compact-complete.{json,png}`。
- 结论及偏差：通过。Context胶囊仅有读数浮层，随后使用既有Slash命令入口；未用fixture RPC代替用户Compact。

### S05 断线期间child完成，同页自动恢复
- 意图／要求：G5，U03/U04及恢复／草稿契约。
- 起点／输入：S04后、child held；写入“验收未发送草稿-S05”。
- 步骤／观察：记录documentId，合法disconnect，观察Connecting及旧画面／球／草稿；release-child走真实finish_noting；reconnect，等待自动恢复，核documentId、末尾与FM、球终态、主按钮；不得手动刷新。
- 预期：断网不伪造成功，不自动发送；网络恢复后必要读取及流完成，退出Restoring，Main仍idle、Noting按真实任务结束；草稿保留、可继续操作。
- 实际／证据／时间：01:18。断网后实际界面单行`Connecting to Hermes…`、Send禁用，完整旧画面及草稿保留、球仍running；断网期间release-child走真实finish_noting，服务端Main idle、Noting idle且持久完成FM36。reconnect后同document `0c7e…16f7`自动ready、无恢复提示、球idle、Send可用，草稿仍`验收未发送草稿-S05`，完成Framework卡已出现。证据`06-before-disconnect.{json,png}`、`07-offline-child-completes.{json,png}`、`07-child-completed-offline-stats.json`、`08-reconnected-after-child.{json,png}`。
- 结论及偏差：通过。同epoch真实断网，不模拟服务重启；没有手动刷新或自动写重放。

### S06 Pending必要读失败与恢复
- 意图／要求：G6，S08/P03/P09。
- 起点／输入：恢复具备合法已结束Main及独立FM的页面；仅依赖层注入一次Pending读取失败。
- 步骤／观察：触发真实同页重连读取，必要读失败时记录提示、操作资格；放开依赖，观察自动重试；禁止改Controller、receipt、pendingKnown或availability。
- 预期：失败不报已恢复，不放宽动作资格；自动重试成功后沿正式结果收敛，页面无需刷新且不重复写入。
- 实际／证据／时间：01:19。首次count1确有一条显式Pending依赖失败并自动恢复，但观察到页面时已恢复，故保留`09-*`为短瞬态尝试，不据其声称亲眼见到Retrying。为补齐失败表现取证，同一正式路径再设count3并断线重连；本人实际AX／截图可见`Retrying live updates…`、Send禁用，页面sample明确`readyForDisplay=true`但`availability.ready=false`、waiting仅`pending/retrying=true`；Main idle、球idle也没有提前放行。三次失败耗尽后自动重读原生成功snapshot，仍同document／同recoveryId12，availability ready、提示消失、草稿保持且Send可用，无Toast。证据`09-pending-retry-stats.json`、`10-pending-failure-held.{json,png}`、`10-pending-failures-stats.json`、`11-pending-auto-recovered.{json,png}`与完整被动序列中的3份pending失败样本。
- 结论及偏差：通过。增加count3仅为延长合法依赖错误观察窗口，无产品改动；与root过目的组合方法一致。精确旧`live.recoveryError`导致Pending先返回却不能adopt的竞态，复用FE同候选`controller-force-completion.test.tsx:145–160`及`.archive/force-completion-20261031/error-then-auto-retry.json`、`final-tests.log`273项证据：错误cut不放行，Noting终态也不解锁，新cut后Pending自动retry/adopt方可Send。该机制原件SHA分别`05ab444a…1039d`／`b8bdb064…b55cd`，当前Pending源SHA与runtime一致；实际浏览器未手造错误完成封套，不宣称重建该精确竞态。

### S07 恢复后继续完整用户旅程
- 意图／要求：G7，U01/U03/U04。
- 起点／输入：S05/S06结束，输入“验收：恢复后的第三次请求，仅一次发送。”。
- 步骤／观察：实际Send、完整回复到idle；重新读取页面确认该user／assistant只各有正式预期身份，无自动重放；核Compact仍可操作。
- 预期：用户持续使用无需救援／手动刷新，回复完整可持久恢复。
- 实际／证据／时间：01:19–01:20。实际Send仅生成user37（UID f59f6fa3…9f237）／assistant38（UID56115484…7a4b36），原生complete=true且真实Main idle／Noting idle。完整输出`Native Force fixture response 3. Tail marker FORCE-NATIVE-END-3.`；随后本人主动再冷读，新document恢复同身份／同全文，填未发送草稿后Send可用，零额外Main请求／重复user输入。证据`12-final-send-complete.{json,png}`、`12-final-send-stats.json`、`13-final-cold-restored.{json,png}`、真实IDB及最终stats。
- 结论及偏差：通过。末次冷读仅用于持久可用性核验，不替代S05/S06同页免刷新恢复。

### S08 发布及APK交付职责边界
- 意图／要求：G8，U05–U07。
- 起点／输入／操作：无；主会话在门禁后执行真实发布与交付。
- 预期：不冒称当前已发布／交付、实机或真实外发已验。
- 实际／证据／时间：本Agent无生产操作。
- 结论及偏差：有依据的不适用；后续发布验真由主会话负责，不影响本地产品场景必须全通过。

## 5. 问题、修复与复验
| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| ENV-01 | 执行前只读GET /api/fixture/stats | 应可用；实际8191连接拒绝，curl exit 7；原执行器被回收 | 已关闭；root恢复同合成HOME，不涉及产品问题 | 候选未变 | 新runtime真实HEAD／23个源SHA独立匹配，初始idle，S01–S07全执行通过 |

本次无产品失败、新整改项或需修复复验。S06 count1瞬态取证不足与count3补证均如实保留，不覆盖旧样本、不改判据。未运行大型套件；同版本精确竞态证据仅按§4限定复用。

## 6. 验收结论与推荐复核
G1通过：实际Main执行中无Force，结束后完整尾部与Force FM出现，Main完成不受FM追加影响。G2通过：child active期间后继Send可完整完成。G3通过：冷刷新恢复精确尾部、Framework、Thinking及动作资格。G4通过：实际Compact独立完成、7→1行而Force未取消。G5通过：断线期间child完成后同document自动恢复、草稿保持。G6通过：真实必要Pending读失败保留禁用／Retrying，依赖恢复自动收敛；精确旧recoveryError竞态按已过目方法复用同版本机制原件，观察边界明确。G7通过：恢复后再次Send及冷读取完整持久、身份唯一，无自动重放。**本轮产品Validation门禁关闭；7通过／0失败／0未执行／0阻塞；S08为root发布职责有依据不适用。**

用户主要复核路径：在可触发Force的合法区间发起普通请求，Main输出结束后应看到Framework提示、后台整理球继续活动，同时可以发送或Compact；主动刷新末尾仍在；断网后恢复无需再刷新，草稿及操作自行恢复。实际结果可直接查看`02-force-held.png`、`03-cold-restored.png`、`05-compact-complete.png`、`10-pending-failure-held.png`、`11-pending-auto-recovered.png`和`13-final-cold-restored.png`。无需为了复核再运行昂贵全套。

剩余边界：无当前产品场景未执行；真实Android安装／生命周期、外网模型内容质量、认证服务与微信外发未执行，冻结索引已明确本故障不重开原大轮对应缺口；不能由IAB／受控SDK冒称通过。生产发布与0.1.10原签名APK实际交付尚待root执行并独立补核，最终目标结束由主会话负责。本人隐藏tab已关闭，隔离服务由root继续持有，未擅自停止。
