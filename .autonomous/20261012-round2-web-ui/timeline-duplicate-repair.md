# FV-F02 · Timeline 重复 Assistant 修复交回

当前状态：**首修已提交/集成，真实重叠复验仍失败；第二修已获Root亲审接收，在独立分支提交并push，待Root统一集成及原validator真实复验。FV-F02仍open，不是Validation PASS。** 下文首修版本/测试保留为历史有效机制证据，不能替代最新真实关闭；正式UI、后端、服务/profile/config/DB未由本owner修改。

## 1. 对应条款与边界

依据现行 02 §1.1–1.9（Conversation/Session、Message UID、原生复用），§2.1–2.4（真实 History 与 Full/Active 区别），§2.6–2.7（身份/路径与 rewind），§5.6/§5.12（真实 Framework 消息及人类 Notebook 边界）；06 §0.1–0.5、§1.4–1.5、§1.12、§3.2–3.3、§4.5–4.6；本轮索引、基线、计划及最新正式 Validation 先行授权。

工作树 `/Users/edgar/code/hermes-secretary-web-timeline-fix`，分支 `codex/round2-timeline-fix`，基线 `833ef31468dbc73e0f25961cec1fe81399ba6111`。Root 亲审接收后提交 `4495596`（完整哈希见下文）。平铺隔离从该提交建立；node_modules 链接正式 UI 已有依赖，未 install、未改 lock。现有 common post-commit 与仓库源 hook byte-identical，未替换 hook。主仓报告/证据位置是唯一文档写入范围。

## 2. 真实失败与根因证据

实际会话 `20261014_162414_e964a3` 的 final Assistant row860 / UID `25c2948f4fca48cc882e498cd8a1f27f` 仅有一条真实持久消息；`A2-duplicate-assistants.json` 明确两个内容相同的可见 article，Notebook 独立。Root 已核 `A2-end.dom.txt` 第83/176/234行共三个普通 Assistant；`A2-slash-before` 与 `A2-notebook-complete` 也为三条。不能把 `/notebook` 断言为创建重复的原因：其 `readNotebook` 正式入口只做 `secretary.notebook_read`，并不 activate、submit 或发完成事件。

真实 REST 源显示第二 Turn 输出末尾是 final860 → Framework861；Framework861 的生产时间比 final860 早，合法展示序列由原生行顺序决定，不按时间排序。第二个自然 Noting 的 Framework882 随后出现。

原始 A2 WS/Controller 快照不存在；本任务只读 `session.events.since` 已 truncated，A2终态被后续验收 Turn 挤出。`source.json` 保存本次原始回放/REST，不能冒称捕获到 A2 原帧。

结构根因在生产 `projection.ts:522` 的 `bindSourceNodes`：将 native suffix 中每条非驱动 User 都变成必须有 live 对应的 slot，包括 History owner 才呈现的尾部 Framework。多一个 User slot 即导致 slot 数量与 live 数量不符，**整包 stream UID 都未绑定**。

同时原生后端 `tui_gateway/prompt_turn.py:956` `_persisted_turn_receipt` 仅在 tail 最后一行确为最终 Assistant 时输出 final_assistant_row_id。用只读真实852..861源行，补回 Hermes 的持久标记/row地址，并运行**实际生产函数**，结果为 complete=false、无 finalID、source_boundary 三项 true、source UIDs 全在；见 `receipt-probe.py` / `receipt.json`。这是按真实源序列的受控重建，不是假造 A2 的捕获帧。此形状进入实际 Controller 后稳定复现两真实 Assistant 变三 article，见 `red.log`。因此确认该结构性失败机制吻合真实迹象，最终具体 A2 闭合仍须同会话真实复验。

## 3. 实际变更与正式路径

仅三处文件：

- `src/core/projection.ts:529`：native User source 只有在已有 live 节点携带相同真实 User UID 时才创建 stream slot（已消费 Steer 等）；History owner 的 Framework/Reminder/User 不占 stream slot。Assistant reasoning/text 与 Tool 仍严格检验总 slot 数量、顺序、角色、UID 和 callID，再逐节点绑定原生 UID/row地址。
- `src/core/controller-timeline-reconciliation.test.tsx`：新增4个正式 Controller→真实 TimelineMessages/MessageProvider/ReactDOM 用例，包含实际命令 router 的异步 `/notebook`。
- `src/core/contracts.test.ts:693`：旧竞态夹具只对 `/messages?` 挂起；并行原生 saved metadata 读取返回 `{id:"A"}`。原“旧完成历史读取未返回时开始新 Turn，不能退休第二条 live”的实质断言全部保留。

正式纵向路径：`message.start/reasoning/tool/message.delta` → Controller.event → reduceEvent → message.complete/native source slots → reconcileLiveHistory → REST history → sourceTimeline → TimelineMessages → MessageProvider/真实 article；Notebook 走 createCommandActions.perform → readNotebook → 异步临时结果。没有新增组件、后端 API、Transcript mirror 或内容去重。

**缺 finalID 的正确行为**：未把 partial receipt 改称 complete，也未改 `sourceCoverage` 的 finalID/边界保护。合法 stream slot 按 native proof 取得精确 UID；当同 UID 的真实 History 行到达，reconcileLiveHistory 按身份退休这些节点及对应 checkpoint，完成时 live.nodes=0。Framework 的真实行始终保留，临时 Notebook 也独立保留。前缀/压缩证明为 false、shape 不匹配或实际未持久化的错误最终文本仍保持保守的 live 残留，不靠同正文“猜到”历史行。此次修复不声称消除所有无证据/非法形状的未知残留。

## 4. 验证结果与复用

唯一测试窗口获 Root 放行；single-worker，未 fullsuite/build。完整日志与源码 hash 在 `.hermes-dev/round2-verification/formal-validation/fv-f02-fix/manifest.json`。全部进程已退出，窗口已释放。

| 命令/证据 | 结果 | 解释 |
|---|---|---|
| `npm test -- src/core/controller-timeline-reconciliation.test.tsx --maxWorkers=1` / red.log | 3通过，1预期反例失败 | 修前真实 Timeline 两真实 Assistant 实际渲染三 article |
| 新用例 + contracts + timeline / green.log | 118通过，2失败，共120 | 新反例已过单卡/退休，随后错误的 catalog fixture 键失败；另一旧fixture被并行metadata读取覆写release |
| 新文件 / targeted-green.log | 4通过 | catalog 使用原生 `/notebook` 键后完整命令/后续/冷重绘链通过 |
| 旧竞态单例 / contract-isolated.log | 仍失败 | 定位旧夹具 |
| **833ef31原projection** + 旧竞态单例 / baseline-contract.log | 同失败 | 明确不是本次生产修复引入；随后恢复修复代码 |
| 同单例夹具修正 / contract-fixture-fixed.log | 1通过，69未执行 | 不弱化原断言，只区分正式REST路由 |
| 新文件 + Controller `-t 'terminal source reconciliation\|selected profile and stored identity\|live deltas before\|failed replay\|Rewind\|true tip' --maxWorkers=1` / final-targeted.log | 11通过，62未执行 | 4新增与7指定身份/replay/rewind/原生tip用例；最后源版本 |
| `npm run typecheck` / typecheck.log、final-typecheck.log | 两次均通过 | 第二次在最终夹具与顺序断言后；无build |
| `git diff --check` | 通过 | 工作树差异 |

**127 distinct 的精确组成**：contracts70（初包69有效 + 修夹具后原竞态1）、timeline46（初包全过）、新增4（最终定向全过）、Controller定向7，共127。不是一条127 PASS命令，不叠加重复执行；初包两个失败历史保留。七次小范围 Vitest 实际运行均不超过5.1秒；最后11例总1.55秒。原生receipt probe首尝因未设置仓库PYTHONPATH而导入失败，正确指定后生产函数成功；不是产品测试。未采历史峰值RSS，不宣称内存峰值无风险。

## 5. 旧测试漏检与剩余缺口

旧 completion 夹具都假设 final Assistant 是 suffix 最后行，使用 `complete:true/final_assistant_row_id` 或正好等长的source slots；已有 Framework 案例在 message.complete 之后另发 status.update。它们未覆盖**原生 terminal proof 内含 history-only尾部Framework**与正式 live 退休的组合。旧 Notebook 测试确认临时位置与单条 finalID handoff，也不覆盖该 partial receipt。新 ReactDOM 反例在修前稳定失败，证明断言能识别真实重复，未镜像实现。

已证：完成live全退休、native final→Framework顺序、异步Notebook独立/后续消息排后、两相同正文不同真实UID都保留、下一Turn不会被旧completion退休、冷重绘无duplicate且临时卡可消失、前缀/压缩信任负对照和未持久化error保留。既有 consumed Steer/History契约、rotation UID merge与同文合法消息用例复用；七个Controller定向用例补profile/replay/rewind/真实tip。此次没有真实浏览器、模型、服务重启、真实rotation/rewind操作，因此不能冒称覆盖这些实际旅程。对于源slots还存在其他无法匹配形状的分支保持旧fail-closed规则，未扩大身份推断。

## 6. 接口与风险

原生 DTO/RPC、终态回执生成、sourceCoverage、backend、权限、存储和模型上下文均未改。所有消息仍由真 History/live owner 投影，临时结果仍无持久UID。对压缩continuation继续使用现有作用域/UID；rewind与分支继续依原路径/权威history，未新增去重数据库或跨Conversation表。正文相同从不参与身份决定。

集成仅需三个前端文件；contracts夹具修正须保留未削弱的旧断言。正式UI另有Usage修复，先由Root亲审合入，再原validator统一reload建立该源码版本的新Controller；旧浏览器live残留不会被凭内容强行清除。没有修改正式5173资产，也没有触及其他owner的Usage/Context/Clarify文件。

## 7. 建议后续动作

Root亲审并接收三个文件，记录新FE版本；原validator同一会话重载后核持久row860唯一/Framework861与882存在/临时Notebook刷新可消失。随后一个真实新Turn让自然Noting完成与Main输出发生合法交叠，取 native terminal persisted_turn 的完整帧（source_messages/source_boundary/finalID）与 article UID/位置和live状态；完成后 `/notebook` Enter、等待异步结果、再发一Turn且返回/reload，确认每个真实final单卡和后续正确。继续保留A2失败，不让本报告覆盖validation.md原结论；真实复验后由原validator负责关闭FV-F02。

## Root 接收后的冻结检查与提交（2026-10-14）

Root 已亲读生产接缝、精确UID退休与四个正式Timeline用例，接收身份方案及finalID保护，授权只补产品相关冻结检查并提交独立分支。沿用既有 `check_health.py` 的后端冻结 Measurer/compare/apply_allows 与规则资源，只测 `src/core/projection.ts` 对基线833ef31：**0 blocking、0 advisory**；`health.json` 保存完整metrics，`health.log`保存结果。没有复跑测试、build或全检查；其它Python/shebang/config-writers等类别对纯TS投影变动不适用。

显式 stage 恰为前述三文件，staged diff --check通过；独立分支提交 **`44955963782f2572289a11f2661f8faa358e5b2b`**，既有post-commit自动push至 `origin/codex/round2-timeline-fix`。独立读取远端hash为 **`44955963782f2572289a11f2661f8faa358e5b2b`**，与本地一致；工作树干净、hook与源仍byte-identical。未合入正式main、未改5173/53445或profile。FV-F02仍须原validator同会话真实复验，不能以该commit/health通过替代验收关闭。

## 首修真实复验失败：原帧定位与第二修提案（2026-10-14）

**FV-F02仍open。** 首修集成正式b99651c后，原validator真实重叠旅程仍有两份final Assistant及重复Thinking/Tool。首修机制证据有效，但未覆盖原生source中已持久化却未产生reasoning.delta的reasoning segment，不能冒称真实缺陷已关闭。

完整解析 `F01-F02-b99651c-overlap-events.jsonl`：180批、260个唯一seq、没有truncated批次。两次Main分别从4184/4311开始，4305/4435完成。第二Turn在4316产生terminal call `call_00_ET_24Q8IG85wd2T7DCsuCib8929`；4318/4319自然Noting更新/完成；4320工具完成；4433Framework；4435终态含真实source `[1085 User,1086 Assistant(reasoning),1095 Tool,1096 Assistant(reasoning+content),1097 Framework]`，complete=false/no finalID且source_boundary全true。真实final UID `faaae83f53234d0ea52e9a17d87ce386`。

**确切失配**：4311–4316原帧只有thinking.delta（原生spinner消息）、tool.generating、tool.start，**没有任何reasoning.delta**；真实source1086却has_reasoning=true。对当前正式生产reduceEvent离线原帧重放（直接TypeScript编译加载原模块，无镜像reducer、无模型/浏览器）可见第二Turn live只有 `[Tool,Thinking,Message]` 三节点；首修跳过History-only Framework后native slots仍是 `[Thinking1086,Tool1095,Thinking1096,Message1096]` 四slot，旧“全部slot必须等长”拒绝全包UID绑定。无finalID使whole-turn退休保护正确拒绝；三个live节点都无UID，于是REST真行到达后全部仍残留。`fv-f02-overlap-fix/reducer-replay.json`保存每个关键帧/node；probe读取并处理了全260原帧。真实reasoning.available载荷其实是final正文，不能拿它补造未streamed Thinking。

最小提案（待Root接收后实施）：保第一修对History-only User的ownership规则与sourceCoverage/finalID保护；native reasoning source slot允许没有live对应（native source已存reasoning并不保证delta可见），其它Assistant text/Tool/已投影真实User slot继续必需。对现有live与source slots做**唯一、保序的完整匹配**：每个live必须匹配，匹配仍检验kind/role/已有UID/tool callID；只能省略native-only Thinking slot。多种可能对应时整包fail-closed，不按正文/时间/相似度选择，也不从最后同文消息猜final。唯一映射成立后按原生UID退休，既有sourceCoverage不放宽。此真实序列唯一略过1086 reasoning后严格匹配，三个live可获原生身份并正式退休。

建议验证：在新隔离b99651c树使用这次**真实260原帧**驱动Controller/Timeline，证明首修3live残留及两article，修后0live/1final并保真实1086历史Thinking、工具与Framework；补两个可选Thinking对应存在歧义的负对照、不省略普通Assistant正文、未持久error/前缀或压缩变化保护；复用既有Notebook/同文多UID/rewind包按影响选择。未开始第二次产品施工、测试或提交，未更改正式产品或服务。

## 第二修七项实施交回（2026-10-14）

### 1. 条款、授权与范围

沿用§1所列02/06身份、原生事件、Timeline、Notebook、路径与无假绿条款。Root读原帧分析后明确接收仅跳native Thinking的唯一保序匹配，授权从正式 `b99651c53ca7792e8631844fe363cdb168531912` 隔离实施与独占定向测试/类型/health窗口；没有产品语义自主变更。工作树 `/Users/edgar/code/hermes-secretary-web-timeline-overlap`，分支 `codex/round2-timeline-overlap`，未commit。旧44955963分支/证据保留。新树依赖链接现有node_modules，lock未改，common hook与源一致。

### 2. 实际变更

四文件：`src/core/source-slots.ts`（46行新小helper）；`src/core/projection.ts`（现有bindSourceNodes只调用唯一匹配、使用返回的native refs）；`src/core/controller-timeline-reconciliation.test.tsx`（原4例保留，新增4例）；`src/core/fixtures/fv-f02-overlap.json`（真实重叠事件的测试数据）。

helper用迭代prefix-state动态规划计数，路径数饱和2，引用用共享链；时间/空间上界O(source slots × observed nodes)，无递归/指数回溯。每条live必须对应source，只有native Thinking slot可跳；普通Assistant正文、Tool、已投影User都是必需。shape、role、现有source UID或sourceMessageUid、tool callID都必须相符；最终只有恰好一个完整映射才绑定。prefix/compression与source完整UID检查原样保留；未改sourceCoverage、finalID或complete权限。

### 3. 正式链与实际原帧

完整260事件type/seq通过Controller.event→reduceEvent→native terminal proof→uniqueSourceSlots→reconcileLiveHistory→真实REST History→sourceTimeline→正式TimelineMessages/MessageProvider/ReactDOM。无镜像reducer、独立loop、内容匹配/相似度/时间排序或删除真实行。外部fetch/RPC为受控依赖，真实事件归并及React组件为正式产品机制；并非浏览器/模型Validation。

测试fixture保留全部260原事件的type、seq、runtime ID与归并/receipt/delta字段；session.info只保留运行/储存身份及模型基本字段，剔除与归并无关的System Prompt/个人config/tool catalog，Secretary profile路径换为隔离标识，保护公开边界。该操作不重造任何message/reasoning/tool事件或源UID。History来自本次原生REST只读产物 `history-native.json` 的1079..1097真实投影。

必要纠正：source1086的has_reasoning=true是原生completion source事实，但本次REST1086没有reasoning正文；不能把前节“native-only reasoning”冒称该正文在历史已可见。实际final1096的REST reasoning存在并完整保留。测试不造1086正文，验证真实final1096的reasoning与输入源一致。

### 4. 验证、版本与证据

证据根：`.hermes-dev/round2-verification/formal-validation/fv-f02-overlap-fix/`，最终源码、fixture与原始输入hash见manifest。无fullsuite/build；全部进程已退出，测试窗口已向Root释放。

- `red.log`：首修binder＋新4例，2通过/2失败（另4旧例未执行）；真实260帧留下3live；已有stream UID被兼容shape错误改绑。
- `green.log`：`npm test -- src/core/controller-timeline-reconciliation.test.tsx src/core/contracts.test.ts --maxWorkers=1`：**78 distinct通过**（本文件8=旧4+新4，contracts70），2.07秒。不叠加首修127或重复次数。
- 为明确取得正式Timeline而非只看reducer，调整单个断言的执行位置后临时恢复**b99651c原binder**：`timeline-red.log`同260帧正式article预期2/实际3稳定失败；恢复最终binder后，仅复测该case，`timeline-green.log`1通过/7未执行，756ms。没有再次跑78。
- 类型检查 `npm run typecheck` 通过；其后只把live数量断言移到article断言之后，没有更改类型声明或产品字节。
- 原冻结Measurer/compare/apply_allows与backend规则资源，产品projection/source-slots对b99651c：**health 0 blocking/0 advisory**。新helper CC最大9、函数最长20行、嵌套最多3、文件46行；原projection相同最终产品字节。health.json/health.log保完整证据，无规则修改。
- `git diff --check`通过；hook byte-identical；未stage/commit。两次预期red、一次78green、一次单例green均保留；没有构建、依赖安装、模型请求或浏览器操作。没有历史峰值RSS记录，不冒称峰值无风险。

### 5. 漏检、已证与剩余缺口

首修用例要求所有source has_reasoning都有对应reasoning.delta；真实DeepSeek terminal调用前只有spinner（thinking.delta）而无reasoning.delta，native source仍has_reasoning=true。这一原生协议差异使slots必等长假设失败，首修只去掉Framework slot无法弥补。最新fixture包含实际差异，不把spinner改造成reasoning事件。

修后：260帧结束live.nodes=0，final1096单真实UID/单Assistant呈现（两Turn总2Assistant）、2真实Tool、2Framework、真实final reasoning仍在。歧义两种对应拒绝绑定、普通Assistant正文不可省略、已有UID不可改绑；旧4例维持异步Notebook/后续同正文双UID/冷重绘/前缀或压缩不可信/未持久error保护，70contract维持consumed Steer/原生顺序/UID rotation与合法相同正文等行为。不是以相同正文去重。

保守边界：若source与live缺的是普通正文/工具、prefix/compression无证明、UID冲突或有多种Thinking对应，仍fail-closed并可能保留无法可靠关联的live；不把不完整或歧义receipt伪装成成功。此次不扩大它们的退休推断。没有本owner的新真实模型/浏览器/rotation/rewind旅程，最终缺陷关闭仍须原validator。

### 6. 接口影响

无后端修改，无新API、DTO、存储、长期缓存、模型上下文或业务状态。runtime/stored/Conversation作用域沿用Controller原owner；slot匹配只是该scope内native source identity接线。source-slots对projection只有type import，无runtime循环。合法同正文消息由不同UID保留；History不删，临时卡不隐藏，错误未存储时不靠文本选持久行。

### 7. 后续动作

Root集中亲审四文件与manifest，接收后决定独立提交/集成；正式UI完整源码统一后，原validator正常reload同会话复验该Noting overlap，保存真实terminal proof、sourceIDs、可见article与后续Turn/Notebook/reload。保留首修真实失败与新修机制通过两个层次，FV-F02仅由真实验收关闭。

## 第二修提交同步（2026-10-14）

Root亲读projection接线、完整46行helper、4新增测试与报告，核260事件/10条History的fixture及敏感模式扫描后接收，明确授权独立提交。仅显式stage上述四文件，staged diff --check通过；提交 **`351dd2852bc0f448db21c7a36408743c3d3c3424`**，现有post-commit自动push至 `origin/codex/round2-timeline-overlap`，远端独立读取hash与本地一致。工作树干净，common hook与仓库源byte-identical。未再运行测试/构建，未合正式main或改服务。FV-F02仍open，待Root统一集成并由原validator真实复验关闭；本节覆盖此前“未commit/待Root亲审”的动态状态，既有版本/失败证据保持历史原样。

## Root待审 A 设计与事件名 manifest（FV-F02 普通Auto反例，2026-10-14）

**状态：仅设计，未施工。** Root已亲读本次真实反例/文件级audit和06 §0.5/§2.1，接收必要event visibility的A缺失证明；本节提交精确实现边界供Root审定，不另请用户批准。现有两轮shape修复和真实失败全部保留，不将当前设计写成已修复。

### 阅读与缺失证明

已按实际标题读02 §1.1–1.9（Message Identity/Conversation与Session/Turn/原生owner）、§2.6–2.7（压缩continuation、rewind、branch）、§4.7、§5.10–5.11；06实际文件为`docs/06-Hermes-Secretary-Web-UI-V1-Spec.md`，读§0.4–0.5、§1.4–1.5、§2.1。06要求旧REST/RPC名字、参数、响应、errors和语义完全不改，新event/read projection只能在证明缺失后增加。不得前端Turn ledger，不改model cache/prompt，不按正文/时间/provider callID推断Message Identity。

本次源证据`formal-validation/fv-f02-auto-overlap-review.md`：103真实帧5977–6079、Auto实际提交后count1→2；6077真实receipt `prefix_unchanged=false/compression_unchanged=false/all_rows_committed=true`。生产reducer重放完成后保留无UID的Thinking和Tool，终答凭row1380退休；DB各只有一次，DOM两Thinking/两tool。现有`source_messages`给持久源UID，但没有声明每个真实流式输出所属原生消息，两个false不能放宽。`uniqueSourceSlots`在false门禁前已返回，继续允许缺失shape不能解决它。

### 设计选择：提前分配原生UID，不增加相关ID namespace

使用既有`agent.message_metadata.stamp_message_uid/mint_uid`分配真正的原生`message_uid`。**仅当TUI Main的可选展示观察者已安装时**，原生实际stream writer claim为这个attempt准备一个Assistant候选字典（只有role与原生UID）；候选不插入transcript、不创建DB行。成功返回的实际stream response由其本地writer token交回该候选，统一`build_assistant_message`把该UID写入实际新Assistant字典。后续原生`_db_flush_row/message_identity`保留此UID，复用既有`PERSISTENCE_ONLY_MESSAGE_FIELDS`剥离它，provider请求不含该字段。非流式响应没有提前候选，在实际统一builder创建字典时分配UID，再用于interim/真实输出；不造一个“猜到的历史Assistant”。

`_current_turn_id`、`_current_api_request_id`和原生single-writer token只校验实际owner/attempt，不成为新实体ID。不能从“当前最新writer”反推返回响应：`_StreamingCall.run`/`_BedrockStream.run`必须用**自己成功返回的本地writer token**调用sibling接受函数；失效或未返回候选不接入实际builder。实际native retry每次writer claim产生不同原生UID，旧writer仍由原有fence阻止late chunks。没有frontend ledger或第二个backend Turn调度器。

观察sibling只有本次调用持有的候选/已接受响应/实际消息对象，当前native Turn作用域，及实际已提交Assistant的原生tool UID索引。工具索引复用`index_tool_call_uids/resolve_tool_call_uid`与原生`_tool_call_uids`；键必须包含**实际Assistant message_uid**，不跨dispatch仅按provider ID查找。并行工具线程沿既有`propagate_context_to_thread`继承已接受Assistant作用域；tool callback从该实际已提交Assistant读取UID。一个provider ID复用到下一Assistant/Turn得到另一原生occurrence；同一Assistant中的重复ID按Hermes现有共享/多occurrence语义处理，原生索引不能证明唯一时只标unknown，绝不任选。

### 唯一正式接线与最小产品白名单

所有实质逻辑置sibling；以下是**审定请求的封闭白名单**，不触F04 owner的compaction/controller文件，不修改服务。相比上一候选清单，去掉各类final/interim/tool执行分支、response intake/normalizer、provider适配器、Agent Loop、agent_callbacks/tool_progress、compute_host_bridge的产品修改。

| 文件/函数 | 唯一改动责任及顺序 |
|---|---|
| 新`agent/output_identity.py` | 可选观察者及候选/实际对象身份；复用native UID、Turn、writer fence、tool UID index；无存储、执行或provider逻辑 |
| `agent/stream_delivery.py::_claim_stream_writer`、`_fire_stream_delta/_fire_reasoning_delta/_emit_interim_assistant_message` | claim后创建该writer候选；既有scrubber/fence及原callback全部保留；在实际已过滤输出范围绑定观察上下文，interim用实际Assistant字典UID |
| `agent/chat_completion_helpers.py::build_assistant_message`、`_StreamingCall.run`、`_BedrockStream.run` | builder复制已接受候选UID到实际message；stream return以本地成功writer接受原生响应；不改normalize、内容、工具、请求、retry分支。该文件4054行已超基线，接缝改为sibling调用，不能增加原超标指标 |
| `agent/session_persistence.py::_db_flush_write` | 原append transaction成功且`sync_flushed_message_markers`完成后，通知观察者实际batch message UID/row/tool UID；原失败路径无通知，无第二次写入 |
| 新`tui_gateway/output_identity.py` | native Main观察器生命周期、已处理旧event的只读身份投影、source payload构造；内存owner在当前invoke结束销毁。公开字段来自已有profile/Conversation/runtime，未知则不造身份 |
| `tui_gateway/prompt_turn.py::_invoke_agent` | 安装/恢复可选观察者，并在`run_conversation`结束、已有终态处理后销毁；观察者仅绑定实际当前agent/session/profile；不改persisted_turn receipt或原kwargs接口 |
| `tui_gateway/server.py::write_json` | 保留原stamp/routing/transport bool语义，以小facade调用sibling：只为已安装native owner的既有输出frame生成新投影event，旧frame内容完全不变。该文件3581行，拆原body到sibling，不能增长原超标指标 |
| `tui_gateway/contracts/events.py` | 只注册下列4个新event；旧event类、字段、RPC合同全不改 |
| UI `src/core/projection.ts`＋新`src/core/native-output.ts` | 新event消费放单一sibling；节点持原生UID/occurrence UID和native Turn作用域；同scope History真UID到达后退休；旧event路径保持。`source-slots.ts`保留旧帧退化逻辑，不再补shape |

UI `NativeEvent.payload`当前是Json，无需修改API类型或DTO，也无需controller接线：新event沿原Controller.event→reduceEvent现成入口到达。若实施证明某项不成立，回报具体断点，不擅自扩大白名单。对应定向测试在上述模块附近单独文件，Root统一释放串行窗口；本节不运行。

实际调用顺序：原`message.start`→native Turn established→writer claim/候选原生UID→新`message.output_state(open)`→原已过滤stream callback/旧event→新typed output投影→真实builder沿候选UID创建Assistant→原DB提交→新`message.output_committed`→原工具执行/start/complete，投影带已提交Assistant的native tool occurrence UID→真实Tool result提交再发committed→原native message.complete仍不改→观察器close。普通Auto发生任何上述阶段都不改变output identity归属，不重建或改写pre-turn proof。

### 新 event-name manifest（旧RPC/旧字段零变化）

采用**新事件**承载身份，不向旧message.delta/reasoning.delta/tool.start/tool.complete/message.complete添加字段。全部仍走同一个native event stream、原seq/epoch/replay广播；无需新RPC、socket、API参数、DB表或Schema。下表每种payload为新独立合同。

共同字段`turn_id:string`=原生真实Turn，`stored_session_id:string`=实际当前物理Session，`conversation_ref:string`=已有registry已证明Ref（只读，不为event新建），`message_uid:string`=实际候选/提交对象的原生UID；没有可证明Ref或实际owner时不发布“identified”事件，保原legacy/unknown，不以裸UID跨branch关联。

| 新event名字 | 精确字段（含共同字段的适用范围） | 触发者/意义 |
|---|---|---|
| `message.output_state` | 共同字段；`state:'open'\|'uncommitted'\|'closed'`；`api_request_id:string\|null`；`stream_writer_token:int\|null` | 首个真实输出前open；native attempt/Turn结束且未提交时uncommitted；完成closed。api/writer只审计/拒stale，不用于持久身份。非流式writer为null |
| `message.output_delta` | 共同字段；`native_type:'message.delta'\|'reasoning.delta'\|'message.interim'`；`native_payload`为对应原event已授权/已过滤payload的逐字段拷贝 | 旧event仍正常发；新投影的正文/推理/interim属于明确原生UID。`already_streamed`按原interim事实，不再追加同段文本 |
| `tool.output` | `turn_id,stored_session_id,conversation_ref`；`assistant_message_uid:string`；`tool_call_uid:string\|null`；`phase:'generating'\|'start'\|'complete'`；`native_payload`逐字段复制对应旧tool.generating/start/complete payload | generating尚无已提交occurrence时UID为null，仅候选Assistant所属preview；start/complete必须有原生唯一tool UID，否则维持unknown/legacy，不能猜。Tool result持久message UID只由下项声明 |
| `message.output_committed` | `turn_id,stored_session_id,conversation_ref`；`source_message:NativeSourceMessage`（复用现有message_uid/role/row_id/tool_call_uid/tool_calls/has_content/has_reasoning，row_id必须真实正int） | 成功原batch事务且marker sync后；只通知本观察器真实输出对象，不包含history prefix/Framework/任意旧行。Assistant及Tool result都从实际batch对象生成，无shape排列 |

旧事件仍发布，旧TUI/Desktop客户端忽略未知新event即可。V1 projection在收到本native Turn的`output_state(open)`后，该被识别输出的正文/推理/interim采用新投影，工具采用明确tool.output；旧相应presentation frame只保持原状态/HUD，不再次追加节点。**这只是既有LiveState当前输出模式和节点字段，不是Turn记录表或额外Map。** spinner `thinking.delta`、status/usage、Reminder/Framework、Steer、原message.complete生命周期仍按原路径消费。任何未被识别的来源保legacy，不拿新协议模式吞掉unknown source。native typed delta复制安全处理后的payload，不能绕过show_reasoning/notification mute/工具redaction/approval；身份observer不能拿未授权原始SDK token作为新可见内容。

为避免同文本发送两次导致两个UI append，新typed owner标志必须在首个旧presentation frame**之前**publish；UI对本owner只使用新typed text。一旦new observer回调失效，不得任意把后续旧token并入另一UID：保已知节点并显示未知/失败，与原Turn控制独立。流式双event的网络开销是本方案的明确代价；只复制已经发给这个客户端的payload，无新采样/缓存。小范围证据测实际event数量/bytes和无重复append，不为了省字段恢复shape猜身份。

### 状态、失败及身份销毁

- **retry/failed stream**：每次原writer claim对应新的native候选UID；接受的是返回该response的本地writer，不是全局最新。旧fence继续拦late text/reasoning。未进入真实persist的候选只保持未提交/失败live体验；绝不发送committed、不制造历史行。新的UID不能复用旧失败候选。
- **interim/无reasoning delta**：统一builder与实际interim字典共享UID；reasoning/text为同Assistant的不同展示facet。无delta只由History真实reasoning展示，没看到的facet不需要匹配或补造。截断/重试的ephemeral scaffolding即使构造了msg也不发送committed；重复builder必须保持同一实际候选归属，不将新消息误用上个已消费候选。
- **工具及重复provider ID**：实际Assistant提交后 `_tool_call_uids`是owner；回调带该Assistant的作用域读原生index。跨Assistant/Turn同ID不会共用UID；同一native occurrence多slot按原生UID呈现一张卡，不能因为同callID/args自行去重。并行callback验证父scope仍有效；Tool live直到真实result UID/History result出现才退休，不能因为call sidecar落库提前丢运行状态。
- **压缩/rotation**：原UID继续由原生flush/clone保留；发布当前stored_session_id与不变Conversation Ref。原old proof两个false照实保留，新output observer只认自己actual object→实际commit，不将“压缩后suffix完整”外推全部旧stream覆盖。若早期output被压缩删出当前path，没有真实当前History身份就不退休为成功，也不复活该行。
- **rewind/branch/多端/迟到**：UI现有profile/runtime绑定及epoch/seq过滤仍第一层；新节点键用传入scope＋Conversation Ref＋nativeUID/facet，继承UID的branch因Ref不同不合并。committed只绑定同native Turn/scope的既有节点，不能按旧Turn的late帧建立新节点。native observer验证实际agent/session/active Turn，失去owner只丢观察回调、不干涉执行。销毁在invoke的finally，恢复旧callback；离线/reload无新持久化状态，按真History重绘。

### 不破坏证明与定向验证计划

1. 先取得**真实commit UID保持与provider wire parity**机制反例：有observer/无observer分别运行相同受控native response，复用实际request builder、原flush；除随机UID/新event外模型messages/tools/System Prompt/cache scope字节相同、所有既有event payload/RPC合同相同。未观察路径不提前UID、无额外事件；Secretary global off下仅展示观察，原native Auto/Prompt/工具/Turn/admission语义不变。observer故障与提交失败不得改变API返回、原legacy event或DB事务。
2. 单worker最小正式链覆盖：实际stream writer attempt→统一builder→DB commit→真实Gateway/compute-host event relay→生产reducer→History→Timeline；retry/stale/failure、interim/nonstream、native-only reasoning、相同正文不同UID、重复provider ID跨Turn、并行tool、压缩前后candidate/commit、rotation/branch/rewind迟到及双客户端replay。保旧103原帧反例原样，缺新event的旧帧不能假称自动取得native identity。新受控事件必须由正式owner产出，不能手写UID“让测试过”。
3. 仅新identity/相关回归＋typecheck/frozen health；不fullsuite/build、不重复已接收F02第一/二修包。现有两个超长facade不得增长指标；sibling函数CC≤20/300行/6层、文件≤2000。
4. Root亲审/集成后，由原正式validator在统一运行版本执行新的**真实普通Auto→tool→final**交接，核每个native UID/occurrence对应唯一Thinking/工具/终答、多端/刷新一致；再次有Noting交错/合法压缩continuation。实际前缀与model cache不变证据、旧客户端原合同证据均需同版；本节没有宣称测试或真实复验通过。

Root审定上述manifest和封闭接缝后，一次性实施，不逐文件请示；不以设计代替当前F02缺陷关闭。B1/B2/B3配置已通过另行明确授权全部恢复原字节，下一暖Main同步仍由validator负责。

### Root审定的配对故障增量（取代open吞旧输出，2026-10-14）

Root接收“observer和release控制包可同时失败”的具体反例，批准仅在新`message.output_delta`/`tool.output`加入必需`source_event_seq:int`，引用**实际既有legacy envelope.seq**，不新增ID。原open状态只作审计/界面状态，不开启永久抑制。Gateway记录原frame真正stamp后的seq，typed如实引用；并发发布不假定两帧永不插队。compute host parent再次stamp时由write_json sibling将child实际引用投影为parent实际引用，必须有正式桥接证据，不能按最近顺序/文本猜。仅同native producer/scope且确切child seq的映射可用；未知则不发identified typed。

UI只在一个瞬时呈现slot内配对确切`source_event_seq`，无对应typed时有界回退legacy未知；迟到不能精确定位只更新unknown状态，不能追加第二份正文。这里的slot是render buffer，不是业务Turn ledger、无界队列或持久化。配对失败、observer抛错、typed投递失败都默认保留旧输出可见。UI有界刷新回退机制由UI owner负责，不修改controller；正常message.complete/nonpresentation/disconnect事实不能被包缓存吞掉。全旧RPC/event字段不改；4个新event名字及其它字段保持本manifest。Root批准后端封闭8文件及相邻tests在隔离树实施，UI另owner，未审前不commit/合main/重启。


### FV-F02 第二真实反例 · A 后端实现交回（2026-10-14，Root 审前未提交）

本节为 `/root/usage_incremental_repair` 的封闭后端交回，取代上节“仅设计”的当前施工状态；保留既有真实失败及历史方案。旧设计中的 open 抑制旧输出、close 在普通 complete 之后的文字不再是最终实现：**legacy 默认先可见，只按真实 source_event_seq 配对；scope 在 `_invoke_agent` 返回前关闭，普通 message.complete 仍由原 owner 随后发布。** 前端由 timeline owner 独立完成，本节不宣称已修复真实 Validation。

#### 1. 依据与边界

- 已读根 AGENTS/CLAUDE、executing-plans/autonomous-run 消息契约、本轮 index/baseline/plan；实施依据为现行 02 §1.1–1.9、§2.6–2.7、§4.7、§5.10–5.11，以及 06 §0.4–0.5、§1.4–1.5、§2.1 和旧接口兼容合同。Root 已接收真实 Auto 原帧的 A 缺失证明并审定四新 event，随后批准两新 presentation event 增 `source_event_seq:int`。
- 基线 `ea2ab483999f9230abfd794bdde2ea3fe2468cfe`；平铺树 `/Users/edgar/code/hermes-secretary-output-identity`，分支 `codex/round2-output-identity`。只改授权后端/相邻测试/必要生成物；无派生、无 UI 产品修改、无模型或网络请求、无配置/运行 DB/服务操作、无 commit/main 集成。正式配置已另项恢复原字节，本任务无待配置操作。
- 不新增 RPC、DB/schema、相关 ID namespace、业务 Turn ledger、计数、模型路由或 Agent Loop。复用 `message_uid`、`tool_call_uid`、native Turn/API request、writer token 与 profile 绑定的现有 SessionDB/Conversation Ref。

#### 2. 变更与正式接缝（12 文件）

- `agent/output_identity.py`：invoke 生命周期内的可选观察器，借用原生 Assistant dict；writer claim 通过原生 `stamp_message_uid` 早分配 UID，实际接受的 response 和统一 builder 保留同 UID。`for_message` 是 prepare/bind 的同一判定 owner，未知/空 API ID 不会二次分配。失败/retry 的已宣布候选以 uncommitted 关闭；实际持久标记已成立者 closed；观察器异常只记 debug，不改返回/执行。read-only 原生 Conversation Ref 按实际 Session 切换刷新，缺真实绑定就不造 scope。工具只认当前 actual Assistant 已提交的 native occurrence map；跨 Assistant 重复 provider ID 保持不同 UID，同一次响应重复 provider ID 按原生共享 UID 语义保持。多个不同 UID 的合并列表不能从旧 callback 猜单个 occurrence，新 commit DTO 保留可证明 Assistant 行及 call ID、缺单一 UID则不冒充。
- `agent/stream_delivery.py::_claim_stream_writer`：既有 token/TLS 建立后旁路观察，原 fence/回调/文本处理不变。
- `agent/chat_completion_helpers.py`：实际 `_StreamingCall.run`（含 partial stub）与 `_BedrockStream` 在原成功响应交接点接受所属 writer；`build_assistant_message` 的原 reasoning fallback 前 prepare、返回实际 dict 时 bind。provider wire/请求构建未改；文件仍 **4054 行，与基线相等**，原超标 facade 不增长。
- `agent/session_persistence.py::_db_flush_write`：原事务成功、Reminder confirm、原标记同步后，观察**本次真实 batch_msgs**；失败无新 committed 事件，不前移 DB 提交点/改变 transaction。
- `tui_gateway/output_identity.py`：保留原 `write_json` stamp/room/transport/返回路径，旧 frame 完整写一次；成功后新 typed frame 引用其真正 stamp seq。observer lookup/source/typed sink/安装/销毁异常均保旧输出。parent compute-host relay 在本 sibling 以 `(native turn, child 原 seq)` 的有界瞬时映射投影 actual parent seq，容量沿用既有 replay 512，不改 compute_host_bridge。缺精确映射、类型不符或旧 Turn 迟到则不发布 identified typed；不按正文或最近帧猜。
- `tui_gateway/prompt_turn.py::_invoke_agent`：只在原 `run_conversation` 的原 notification scope 中安装/销毁观察器，保原运行参数、admission、usage/失败与最终完成链；`tui_gateway/server.py::write_json` 仅转 sibling，**3581→3570 行**。
- `tui_gateway/contracts/events.py`：仅四新 event/DTO；`tests/tui_gateway/test_output_identity.py` 为真实 writer/builder/DB/Gateway/SDK 接缝及失败用例；`tests/tui_gateway/contracts/test_generated.py` 只让既有 inventory 精确读取新增正式 emitter/factory，不删 orphan 或放宽断言。
- `apps/shared/src/gateway-contract.generated.ts`、`gateway-contract.openrpc.json` 由既有 `gen_gateway_contracts.py` 生成，Root 追加批准。四新增事件外，有**原 source/产物既有漂移修正**：基线 `tui_gateway/contracts/usage_read.py:25` 已定义 `total_tokens:int|None=None`，两既有 Usage 派生 schema 的旧产物遗漏该字段；source 本身与基线字节完全相同。生成物同步该事实，不手工回删。旧 RPC/method/server-request 与旧 event 定义逐项全等；旧 schema 除这两项既有字段同步外全等，见 contract-parity.json。

#### 3. 最终调用链和失败语义

原 Main/notification owner → invoke observer → 原 native Turn/API/stream writer claim → UID 候选 → 首个已授权旧 presentation frame 前 open（审计）→ **原 legacy write** → 新 delta/tool.output（实际 `source_event_seq`）→ 实际 response 接收/统一 builder 沿用 UID → 原批写成功/标记同步 → output_committed（真实 UID/row）→ 原工具执行（ContextVars 沿既有 `propagate_context_to_thread`）/工具结果原提交 → 原 tool.complete → invoke observer close → 原 message.complete/receipt → 客户端按真实 History 更新。

没有 typed 的最后一个 legacy 帧仍立即可见。new sink 失败不要求另一个 release 包才能恢复。source/open/close 故障不影响原 return、旧 event 或 API wire；failed commit 只有 uncommitted，不宣称真实 row。unknown/迟到仅保原始可见输出，不能补正文、绑定另一个 UID或把 call ID 当跨 scope 身份。压缩 two-false proof 原值不改，新机制仅解决真实 output object→native commit 的身份交接。

#### 4. 有效验证与证据

证据根：`.hermes-dev/round2-verification/formal-validation/fv-f02-identity-fix/`；完整源码 diff `product.diff`，12 文件/sha256/基线与现行行数 `product-manifest.json`。

- 最后新增 **16/16**，canonical `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/tui_gateway/test_output_identity.py -j 1 -q --tb=short`，5.3s；日志父目录 `fv-f02-output-identity-final-16.log`。覆盖：actual UID/batch/History + SDK HTTP body/旧 payload parity；observer source 抛错；typed 投递抛错；真实 child relay→parent seq 且插队 status；缺 source reference；retry uncommitted；跨 Assistant provider ID 复用；failed commit；native publish_compression_child + row-addressed History adoption；原生工具线程 ContextVars；nonstream builder reasoning fallback；同响应重复 ID 原生共享 UID；正式 owner fixture；observer 安装/销毁失败各一；旧 Turn reference 迟到。参数化故障分别计数，fixture 是受控驱动，不冒真实模型。
- 已有效受影响回归 **53 项**只运行一次：partial-stream finish 28、single-writer guard 2、incremental tool persistence 21、bot-mode 原生静默 2；日志 `fv-f02-output-identity-final-tests.log`。当时总 67 pass 含旧版新增 13 与 generated snapshot 1；后续新增包演进只复测该受影响包，**不把 67 与新增 16 相加冒 distinct**。
- generated snapshot 1 pass。catalog 1 fail：只剩基线 `review.summary` 合同注册但无 emitter。以 ea2ab 同一源文件/同一 canonical 单测试反证确为已有失败，`baseline-catalog.log` 为 `1 failed,1 deselected`，失败字符串同一 `['review.summary']`；原产品文件在隔离树内临时基线后全部恢复。现行 failure 见父目录 `fv-f02-output-identity-final-tests-2.log`，不删合同、不关闭 check、不伪造 emitter。
- 最后冻结检查 `scripts/check --base ea2ab... --only footguns,ruff,health`：三项通过，health **10 files，0 blocking / 0 advisory，2.0s**，日志父目录 `fv-f02-output-identity-final-checks.log`。无 full suite/build/模型、未扩跑其它平台；测试窗口结束已给 FV-F06 并抄 Root。
- `typed-native-fixture-v3.json`：9 场景/164 个实际 Gateway params event，实际 native UID、实际 SessionDB commit/History、实际 native interim callback、正式 `_persisted_turn_receipt`，MockTransport 捕获真实 SDK 序列化 HTTP body，零网络/模型。normal、observer failure、typed failure、重复 provider ID、retry、rotation、failed commit、native worker、nonstream。原 v1 的人为 interim 与 actual content 不一致已纠正，v1/v2只保历史不作最终正例。v3 中 Tool result commit 在 tool.complete 前，scope close 在普通 complete 前；生成前后 API/UID正式接缝不是给旧103帧补身份。
- `contract-parity.json` 记录旧合同全等及已接收产物漂移；`event-cost.json` 只量受控 normal：旧7事件/params JSON1825B，新增12事件/4937B。新 visibility 的协议体积成本明确，不把该小样本外推整体网络。

#### 5. 缺口、风险与准确限制

- **真实 Auto overlap 缺陷尚未宣称关闭**：新后端未提交/集成/启动，UI owner仍独立实现；v3 rotation 是真实 DB child 发布/读取，未执行模型 Auto、未人为改变 compression_count 或制造两个 false。原103真实 two-false 证据原样保留；须原正式 validator 在新版完整正式链复验。
- branch/rewind/两真实客户端/异步迟到的完整真实场景未由本小包操作；这里有 native scope/close/old-turn-reference 机制反证，不能冒充真实浏览器验收。源不足或 seq 配对已过期时只能 unknown；协议不保证 UI 可在无正式源时猜退休，前端有界 slot/History 机制及真实结果由 UI owner/validator 负责。
- 合并多个不同 occurrence UID 的列表保未知，当前16例实测的是跨 Assistant 不同 UID与单响应原生共享 UID；不声称已实际执行合并后的模型工具。
- `review.summary` 原基线失败保留为 Root 门禁判定项。typed 双发布增加网络与事件体积；source ref仅在实际 native DB已有合法绑定时可用，未知不创建身份/改 DB。

#### 6. 接口交接

四个名字：`message.output_state`、`message.output_delta`、`tool.output`、`message.output_committed`。公共 scope 为 native `turn_id/stored_session_id/conversation_ref`，state/delta 带 native `message_uid`，tool 带 `assistant_message_uid/tool_call_uid|null`；state含 `api_request_id|null/stream_writer_token|null`及 `open|uncommitted|closed`；delta/tool 两种新呈现包必须带 actual `source_event_seq:int>0` 和已授权旧 `native_payload`原样副本；committed仅复用真实 `NativeSourceMessage` row/UID/facet flags。没有旧 event 加字段/旧 RPC新增参数。

v3 fixture路径已交 timeline owner。UI legacy默认可见；只在确切seq的瞬时slot替换该旧增量，未配对/断线保持unknown，不追加第二份正文；真正 commit的 has_content/has_reasoning 与 actual History证明才允许退休 facet。Assistant call row commit不等于Tool result commit。Source UID可以跨native compression physical row复制保留，仍受 Conversation/scope/current path限制。

#### 7. 下一步

Root亲审本树 12 文件、正式接缝、fixture与基线失败证据后，再授权显式stage/commit（保共用自动push hook）；当前不提交。完成 UI 消费与集成后，由原正式 validator 使用同一 FV-A 正式会话真实连续至少3 Turn并再触普通 Auto，核 seq/UID/实际 DB/History/Thinking/tool 每一节点一次，以及 observer未知/历史路径边界；需要服务切换由 Root另行放行。Verification仍是最后独立静态审查，不由本实现者用小包替代。


### Root 窄 review · builder 基数与 candidate 生命周期（2026-10-14，只读）

**结论范围：现行正式通用 Loop 的10个统一 builder 调用点，未发现一次实际 dispatch 同时构建并 append 两个不同 Assistant dict 的路径。** 不能将此结论扩大为“任意外部重复调用 `_build_assistant_message` 自动有不同UID”：当前 for_message 在相同 native request 复用 accepted 是一对一正式 producer 的契约；不增加猜测性门禁，未改产品/未跑测试/未提交。

- 总路由 `agent/conversation_loop.py:1706–1720`：normalize_model_response 的 continue/return 先退出；随后工具与纯文本由 `tool_calls` 互斥选择 run_tool_round/finish_text_response，不同时执行。新 outer iteration 的 begin_iteration `agent/turn_iteration_prep.py:423` 增 api_call_count，`conversation_loop.py:1693` 设置当前 native API request；stream 每个实际 attempt 又由原 writer claim 更新 candidate，既有 token 单调隔离。
- Codex incomplete：`turn_response_intake.py:179–193` 调 `continue_codex_incomplete`，后者 `turn_truncation.py:588` 构建一个 interim、`627`至多 append一次（或只刷新既有上一行而不append）；intake 随后 continue/return，不落入工具或 final builder。
- length continuation：`turn_truncation.py:321–324` 一个 builder/append；`343–344` 设原 restart flag并break。`turn_response_check.py` 对 return/break/continue直接传回，`conversation_loop.py:1543–1544` 退出内 retry loop，`turn_iteration_prep.py:569–574`与 `conversation_loop.py:1699–1703`回 outer continue。下一构建属于新iteration；截断工具立即 retry 分支 `turn_truncation.py:398–411`不调用 builder。无“先append fragment再fallthrough到final”的实际路径；TruncationVerdict也注明fallthrough实践不可达。
- 工具验证：`turn_tool_validation.py:136–146`（全invalid工具）与 `212–225`（JSON恢复）各构建/append一个并return continue；`turn_tool_round.py:77–85`立即传回，不再stage。成功分支仅 `turn_tool_round.py:107–110/246` 构建/append一次。mixed-invalid不走第一处builder。guardrail halt `turn_tool_round.py:181`可能另append一个原生literal Assistant，但**不经过统一builder、不复制候选UID**，由原native flush各自mint；不能把它混写成两个builder复用accepted。
- 纯文本：空回复 `turn_final_response.py:130–148`进入recover后一定return；`turn_empty_response.py:215–222`的nudge、`241–245`的thinking-prefill、`110–113`的terminal各互斥，terminal在`294–295`返回break。非空continuation `turn_final_response.py:231–249`一个interim后return continue；普通final仅`283`构建一次，dropped-call nudge `310–318`退出，stop gate在 `turn_stop_gates.py:94–101`复用**同一final_msg对象**并append后由 `turn_final_response.py:340–342`continue，普通路径`360`才append，二者互斥。
- 原生内部 refund/counter与retry不能当“实际 dispatch 新ID”保证；本结论依靠具体 builder/append控制流互斥，而不是把API call当Turn或用request字符串猜对象。未跑额外验证；Root继续静态review其它接缝。

**fixture数量更正**：此前口头“184”是加总误差；v3实际9场景 **164 events/37 History rows**，各场19/10/14/27/23/19/18/19/15，maxseq169包含typed failure造成5个缺号。原fixture字节未改、未补数，正文当前计数已纠正；前端按原v3真实字节消费。


### A 后端阶段提交与源码接收（2026-10-14）

Root 已亲读正式生产接线、四 event/生成物、全部新增测试与 inventory、parity/失败/真实 batch 后 commit、基线失败及 builder 互斥 audit，明确批准既定12文件敏感检查后阶段提交。实际只 stage 这12文件，新增diff无私钥/token/带凭据URL等敏感模式，仅受控fixture-key。共用 post-commit 与仓库原hook字节相同，未改/绕过hook。

- 隔离分支 commit：`839d8f3a47bf9e9737828a0d2a8abbd084816be8`；原hook自动push成功，`origin/codex/round2-output-identity`直接ls-remote为同hash，worktree clean。最终 manifest已记commit/remote/12文件SHA；源码diff对应该提交，旧机制日志仍保留。
- 未合main、未动正式服务/配置、未跑有效旧包。Root接收是源码/机制接收，**F02真实缺陷尚未关闭**；必须新正式BE+UI完整链由原validator同会话真实Auto及连续≥3Turn复验。
- v3 fixture保持真实原字节9场景164events/37rows，不为修口头计数补事件。

### 新版真实生成阶段残留：后端窄归属核对（2026-10-14）

本节仅只读研究，未改产品、测试、配置或服务；Auto配置独立授权操作已交validator。原帧依据 `formal-validation/FV-F02-new-construction-start-commit-frames.json`，相邻实际typed帧摘录 `environment/F02-generating-native-owner-evidence.json`（直接复制原包，不补身份）。

| 原generating → typed | 真实Assistant UID | Assistant真实commit seq / row | 真start → typed |
|---|---|---|---|
|253→254|79cee7d698314c20bc6868a73bdb175e|257 / 1867|258→259|
|975→976|2393673e6dc947b78fe62c1e0538cd99|978 / 1882|979→980|
|1606→1607|07c954194db74521a2bb4a67140a80c4|1609 / 1901|1610→1611|
|2293→2294|32d41543ef7d4714b40d5f4d206f4927|2296 / 1906|2297→2298|

**实帧事实**：每组generating的 `tool_call_uid=null`，同scope的Assistant commit却有真实accepted `tool_calls`，start带相同Assistant UID及真实occurrence UID。四个UID都与最终实际receipt相同；第四Turn receipt.complete=false并不否定其Assistant真实提交。History完整参数卡的实际可见性由前端owner/validator已有包另证，本后端核对不冒充UI可见性证明。

**源码依据**：`agent/chat_completion_helpers.py:2723–2785`的原 `_ToolCallAccumulator.feed`按真实provider index/id维护当前stream累积对象，但回调只返回首次完整name；`:3247–3256`传入 `_emit_tool_started`，`:2924–2926`和 `agent/stream_delivery.py:366–368`继续只传name。因此这是参数构造阶段通知，不能证明某个accepted occurrence。stream结束时`:3262–3270` materialize/finish或adopt正式response，`:4035`接受实际writer；`agent/output_identity.py:34–44,65–96,110–128,202–207`让同writer候选native UID沿accepted实际builder保留，`chat_completion_helpers.py:1673,1761–1763`构造真实calls并bind。`session_persistence.py:316–333`在原batch提交、marker sync后才通知真实commit；四组原帧直接证实此链。

**最小方案（供Root审定）**：前端仅保存并退休有typed证据的Assistant生成阶段；同runtime/Conversation/nativeTurn/AssistantUID的真实commit成立，且实际History同UID非空完整tool_calls已可投影时，结束该Assistant的generating临时呈现。它是同owner阶段交接，不把name-only片段绑定到特定occurrence，也不按名称/文本/顺序或providerID猜匹配。复用现有source UID/row节点字段，不加后端event/API/ID/ledger；保留没有可靠typed配对、未提交、未被History替代的unknown。候选new-writer时closed/uncommitted仅表观察器状态，不能单凭close或message.complete全局清unknown；retry失接受/commit失败/迟到失scope必须保留诚实未知。压缩row可变时以同Conversation真UID及当前History为准，不能只依旧row或完整Turn proof。

结论：四片段的Assistant归属真实，参数生成已经由同UID真实提交的accepted calls结束；当前原生四事件足够给这四例做阶段退休，无需扩后端接口。本次无测试执行；关闭F02仍需前端修复与原validator真实复验。
