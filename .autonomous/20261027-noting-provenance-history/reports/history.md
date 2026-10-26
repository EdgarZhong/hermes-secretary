# History 实现整包交接

## 1. 条款与判据

执行者：History Agent；工作区 `/Users/edgar/code/hermes-secretary-noting-chain`；分支 `codex/noting-provenance-history-20261027`；冻结基线 `02d55fdb45b4fb7c883fb477f4469912f4707f70`。已读 executing-plans、autonomous-run交接契约、本轮Snapshot Index/baseline/plan、根AGENTS/CLAUDE、tools/AGENTS参考、07最新顶部与保留§5、白板K1/C7、02身份/Foreground、04§2来源路径。未读归档、未访问生产正文/凭据、未操作UI；不派生、不提交、不push、不部署，不改plan/核心文档/Notebook/Prompt文件。

覆盖C09–17、C20的History实现范围。C20真实模型、父子冻结工具/cache-parity和部署验真由主会话统一集成/门禁，本报告不宣称这些已完成。

## 2. 实际变更

- `tools/session_history_tool.py`：新增正式Schema/handler `mode=get_meta`、顶层`include`、`include_auxiliary=false`；role声明与返回统一user/assistant/tools/system。Get Meta必须提供闭区间start_time/end_time，不接受limit；过滤后≤200返回全部，201或候选预算/索引/来源验证不完整明确失败，无部分messages。
- `tools/conversation_history_time.py`（新增）：只读、有界的消息时间/角色元数据候选枚举，预算沿既有公式`min(10000,max(1000,20*limit))`、批200；不建表/索引/转录副本。带include时完全复用既有HistoryCandidateStream及其native FTS/CJK/boolean/prefix/降级语义。
- `hermes_state_message_provenance.py`：可信origin/display metadata优先；legacy Reminder/Heartbeat/Framework/Compression前缀回退，不能把物理user直接当真人。保留既有coarse kind/source及digest helpers供其他调用方使用，新增semantic_role；普通用户提到Notebook标记不再被无来源依据误归类。
- `tools/conversation_history_projection.py`（新增）：Get Meta先分类，再清理项目外层标签/与消息自身timestamp一致的独立timestamp标记，最后头100+尾100；短文不重叠。Gateway busy-steer精确origin前缀只剥包装、不改真人语义，普通HTML和正文日期保留。工具调用按call ID与其真实assistant批次配对；逆序结果、批次间重复ID、同批重复ID、重复结果、真人新Turn、隐藏边界、非相邻辅助载体均有明确处理，缺失或歧义源用null，不猜配。
- `hermes_state_conversation_history.py`：保持既有合法路径/winner；保留可见性过滤前的边界供工具配对，隐藏内容本身不输出；证明真人来源使用同一语义分类。
- 调整旧History哈希/默认system邻居测试，新增37项正式入口合成DB场景。主会话明确追加授权`tests/tools/test_session_history_identity.py`定点修改C13冲突断言并保留重复压缩/身份验证。

## 3. 正式路径与结果形状

注册`conversation_history` → registry handler（及原InlineToolExecutor保持）→ `_arguments` → owning_history_db/只读snapshot/真实Main或运行中Noting admission父绑定 → HistoryPaths当前合法Foreground/model visibility → Get Meta或Search候选membership/winner再验证，或Read合法锚点/邻居 → 语义来源门控 → 投影。

- include_auxiliary=false在Get Meta/Search/Read（定点和邻居）都先限制真人user/Assistant回复，roles/kinds/include_tool_content/include_tool_calls不能绕过。显式true且省略roles时允许四类；可继续按语义roles缩窄。原生session_search文件/Schema/handler均未改。
- Get Meta当前域外层conversation_ref，跨域按conversation_ref分组；单条严格`message_uid,timestamp,role,content`。content是消息原内容的清理预览，工具条不增加参数字段。
- Search工具结果的content为`{"arguments": <头尾200或null>, "result": <头尾200>}`；assistant调用行content为`{"content": <普通回复原有有界excerpt>, "tool_calls": [{"tool_call_id", "name", "arguments", "result"}]}`，每次调用参数/结果各用200预算。不返回args_digest/content_digest。
- 显式auxiliary Read工具结果的content为同一`{"arguments":...,"result":...}`完整值，仍受现有字符上限；assistant调用行为同次tool_calls结构。`content_offset`按该完整结构的canonical JSON继续读取，能够重建参数和结果，不靠hash替代。缺失值null，不捏造缺失来源。
- 当前Conversation默认、Main显式同Profile跨域、Noting仅父域、fork frozen membership、rewind/exclusions及只读拒绝原机制保持；同UID取正式Foreground当前权威winner，不能单取最早物理副本。

## 4. 验证、版本与原始证据

环境：macOS本地、官方PM既有`.venv`链接，Python 3.14.7；未安装依赖/更改lock。`uv.lock` SHA256 `2bc4db483e9cba927cd7147f9ccbb09635f85bb3f1f36d6e9d51d06b65d1c67e`。SessionDB均为pytest隔离临时库，不读生产Profile；测试runner清理环境、固定TZ/LANG/hash seed。测试不启动终端/模型/外部服务。

最终代码文件指纹：`.hermes-dev/noting-chain-20261027/review-evidence/history-version.sha256`（本报告末尾附同一份）；最终原日志`.hermes-dev/noting-chain-20261027/review-evidence/history-final-tests.log`、`.hermes-dev/noting-chain-20261027/review-evidence/history-check-final.log`、`.hermes-dev/noting-chain-20261027/review-evidence/history-complexity-final.log`。

最终命令：

```bash
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/secretary/test_r3_history.py tests/secretary/test_history_content_paging.py tests/secretary/test_history_source_modes.py tests/hermes_state/test_secretary_message_provenance.py tests/tools/test_session_history_identity.py tests/tools/test_session_history_truncation.py -q
```

最终结果：6文件162通过、0失败，runner耗时10.8秒（10 workers）；83+23+37+3+8+8。验证包括正式registry和既有inline Main/Noting执行、真实DB父绑定、闭端点/原消息时间、45/200/201、include与原Search一致、辅助user伪载体/隐藏消息、工具逆序/重复ID/同批歧义/隐藏边界/非相邻载体、完整参数结果分页、跨域/fork/rewind、重复压缩同UID权威slice、DB reopen、候选预算/真实stale index/读失败/拒绝无副作用、用户HTML/日期/Gateway正文保留。

检查用独立临时Git index只纳入本包9个文件，不触碰共享工作区真实index；基于冻结基线执行：

```bash
.venv/bin/python scripts/check --staged --only ruff,health --base 02d55fdb45b4fb7c883fb477f4469912f4707f70
```

结果：9文件，0 blocking、0 advisory（0.9秒），2 checks ok。附加对5个生产Python文件直接执行ruff C901阈值20检查，通过；本包`git diff --check`通过。未改检查器、阈值或规则。

早期定向运行先暴露旧hash/旧辅助开关断言及重复压缩默认system邻居断言；按最新C13/C15修正测试，同时保留显式auxiliary下原能力。最终通过不依赖放宽新契约。最后增加Gateway/legacy wrapper、stale index、reopen、重复compaction与非相邻配对后定向复测覆盖相关变更。

## 5. 缺口与限制

本包无已知范围内失败；没有真实模型/API、生产Linux、全轮双门禁或部署证据，不替主会话宣称整轮验收。Get Meta超过候选预算即使最终可能少于200也明确拒绝完整性，调用方须缩窗；这沿冻结有界枚举契约。来源无法关联时参数/结果null，不尝试跨scope、隐藏或新Turn猜配。历史格式无可信来源时不会泛化删除任意HTML/日期。

## 6. 接口影响

新增get_meta/include/include_auxiliary；roles对外只接受已确认的tools，不再把物理tool当公共枚举。旧kinds与include_tool_*仍接受其适用模式且不再拥有独立放大辅助范围的权限。旧digest-only工具读取是本轮明确替换行为，调用方需显式include_auxiliary并消费上述原文结构。Get Meta错误码`window_too_large`/`incomplete_window`；缺源/越权/无运行中Noting绑定仍沿原source_unavailable/scope_denied/state_conflict。

## 7. 后续建议

主会话亲审本包9文件及新增sibling，接入已审Prompt采用get_meta/include_auxiliary指导，复用上述同版本证据；在全轮真实模型、独立Verification→Validation及发布前统一核Schema、工具冻结/恢复与生产Linux。若主会话改变工具投影/可见路径，再定向复测受影响文件；无需为review重跑大套。生产Notebook转换不属本包，未触碰。

## 文件指纹

```text
c1a5d4a1bee8b1cbb9f0d8d7a80143872b923503fe5c977dc045770950c00c7a  tools/session_history_tool.py
d7de89c8889c197862cbfad3e2b73bdbfef651d49e47f98d5e9e0b996c5ca4a9  tools/conversation_history_projection.py
9d85dead7d077072e4a8f03624a322e9ec151c8438253e41add1d19d6d798602  tools/conversation_history_time.py
1c2e19dd463f0bf29ba94a82a0f14b6ca1a95e92583f0921a7b3a23bebd300b5  hermes_state_conversation_history.py
c9d9d3b8cd16eae87994f14cc8e6954677615ef444c7b0396ed2f4ac2181c572  hermes_state_message_provenance.py
c7538056f426c279aab4dafcad68bf1b94a1c669b863eae65221cf31795bb48f  tests/secretary/test_r3_history.py
53971b631f3d42489c2d22f730e74a4b72a22f56bd31afffc87fff876d981f44  tests/secretary/test_history_content_paging.py
e774e93b5a49bacfd232492691a9898e14e75a58a29614a9901c0581f844066b  tests/secretary/test_history_source_modes.py
2bfd535425b47feef13c70404d33986e1d8d3003e3b1d7ccd364131bdcbf800e  tests/tools/test_session_history_identity.py

```

## 8. 集成review修复：可信来源统一（当前最终交付，覆盖初交相关分类陈述）

### 条款、发现与根因

本节为主会话集成review后续，替代§2/§5中将legacy正文前缀当作来源依据的初交实现。C13/C14/C20要求共享语义分类既排除实际系统载体，也不能把真人引用HTML/系统文本降为system。初交纯body前缀回退会破坏Notebook既有五项真人/foreign保护反例；这些保护断言未改、未删。主会话授权定点更新`tests/hermes_state/test_secretary_message_provenance.py`中旧“残缺body前缀即系统”期待，并要求真实legacy Heartbeat仍可排除。

### 变更与正式接线

- `message_provenance`继续优先可信origin/display metadata，取消任意wrapper正文前缀的身份权威；typed steer在无明确系统metadata时保持真人。
- 新共享只读`enrich_message_source(db,conn,row,*,content_decoded=False)`：解码原始来源，按已有消息/admission事实补充派生metadata，不写数据库。HistoryPaths在正式Foreground上使用`content_decoded=True`，避免二次解码；Notebook Agent在既有原始来源路径使用默认参数，再统一semantic_role。
- `instant_carrier(conn,row)`完整保留原精确SQL：物理row id/session/UID/content/role，join原source session binding和pending reminder owner，匹配完整receipt内容及instant语义。Foreign相同UID/body、同owner改正文不能借证；fork读取父物理来源保父owner；pause/delete后receipt仍成立。Deferred receipt也采用同等精确owner/source关系。Notebook已删除其私有重复SQL，复用同一helper。
- Heartbeat只接收正式producer完整wrapper、对应timestamp、完整固定instruction与规定的Additional prompt段。普通`<heartbeat>quoted…</heartbeat>`不构成证明；typed steer即使引用完整canonical正文也保持真人。
- 主会话补充旧生产格式后，从`git show 351770eaeb^:secretary/heartbeat.py`及`git show 351770eaeb -- secretary/heartbeat.py`核实：10/25前固定正文确实没有新增的self-check开头与coordination句。仅在共享helper集中增加这个完整历史instruction，未用关键词substring替代完整格式、未改持久原文/native compressor。
- 保留主会话追加的5行可信typed steer外框预览清理及`test_meta_strips_only_trusted_exact_steer_frame`，该断言继续通过。History此前任意build_user_wrapper("heartbeat","needle")的准备改为真实render_heartbeat或明确可信metadata，保留辅助排除主断言。

### 当前验证与版本

History正式registry、Get Meta/Search/Read、定点/邻居、原生receipt admission、foreign同UID/body、fork原owner、改正文失效、typed/普通真人完整Instant引用、当前及历史Heartbeat、HTML/日期、只读无副作用全部覆盖。

最终执行命令与§4同六文件集合（源码测试文件顺序无语义差异）；原日志`.hermes-dev/noting-chain-20261027/review-evidence/history-trusted-final.log`：**171通过，0失败，10.9秒**，分布83+23+46+3+8+8。`.hermes-dev/noting-chain-20261027/review-evidence/history-trusted-check.log`：私有临时index纳入本包10文件，对冻结基线执行正式`--staged --only ruff,health`，**0 blocking / 0 advisory（0.9秒），2 checks ok**。没有改检查规则或阈值。

Notebook Agent提供并已阅读同一共享机制的结合日志`.hermes-dev/noting-chain-20261027/semantic-closed.log`：`test_notebook_provenance_arrays.py`28项＋`test_notebook_maintenance_v2.py`71项，**99通过（6.5秒）**，包括新四类辅助优先级、原五项真人保护、真实admission/暂停删除/fork/foreign精确owner。该日志在旧Heartbeat完整格式追加之前生成；新增分支不改变其当前Heartbeat/Instant/metadata路径。当前新增历史Heartbeat分支已由上述最新History六文件实际验证。

### 缺口、接口及后续

产品接口不变；新增helper只在内部分来源证据富集，不新增store/索引/schema/调度/权限。所有来源归属仍由已有合法路径与原owner决定。没有改生产/模型/核心文档/原compressor/Notebook文件，没有提交。没有待修的范围内失败；真实模型/双门禁/部署仍由主会话统一完成，当前正在运行的无辅助两Task样本可继续。

主会话请以本节及下列指纹为当前交付，初交162项保留为历史证据，不把初版body前缀方案作为现行机制。当前文件指纹原件`.hermes-dev/noting-chain-20261027/review-evidence/history-trusted-version.sha256`：

```text
c1a5d4a1bee8b1cbb9f0d8d7a80143872b923503fe5c977dc045770950c00c7a  tools/session_history_tool.py
544bb64759b65a06680eec4ca2a70c7b240637707407b1af9f8eb5d743a2e83a  tools/conversation_history_projection.py
9d85dead7d077072e4a8f03624a322e9ec151c8438253e41add1d19d6d798602  tools/conversation_history_time.py
7d9a82c2702e8c8fff2362a7595fcb97744694db718b85491e924d3c22295901  hermes_state_conversation_history.py
11099dbc4b3b8915f6f52ddc5bb5361f652f36688c73d44f63690221b15b0dad  hermes_state_message_provenance.py
c7538056f426c279aab4dafcad68bf1b94a1c669b863eae65221cf31795bb48f  tests/secretary/test_r3_history.py
53971b631f3d42489c2d22f730e74a4b72a22f56bd31afffc87fff876d981f44  tests/secretary/test_history_content_paging.py
ec077ab79bf535cfdb65b106812c4b56cc7b03faf5bce84abc4822d62d43164e  tests/secretary/test_history_source_modes.py
2bfd535425b47feef13c70404d33986e1d8d3003e3b1d7ccd364131bdcbf800e  tests/tools/test_session_history_identity.py
04a5e1f842d70b437d17b0c4b258fb7ed0005ec43ba2ec885ed9743b6e58f3a0  tests/hermes_state/test_secretary_message_provenance.py

```

## 9. C11/C14 Compression正式接线修复（当前最终交付）

### 1）条款及授权范围

主会话按只读报告`history-compression-review.md`确认C14缺口，授权原白名单＋`hermes_state_secretary_foreground.py`必要窄辅助投影。最新07/根CLAUDE已由主会话登记工程细化：mixed同native UID分语义部分；anchored Read允许roles选片段；同UID同semantic system合成单system视图；默认旧行为、源身份、Notebook引用门禁与隐藏边界保持。没有新增selector/fakeUID/表/索引/调度，也没有改native compressor。

### 2）实际变更

- `hermes_state_secretary_foreground.py`：抽出共用`_foreground_winners`，原History/Full仍沿原本的有效latest generation、branch overrides/exclusions与active/compacted筛选，不改现有API签名/默认。新`get_history_auxiliary_foreground_conn`仅在显式辅助入口使用，复用同一源/winner及native split/`_handoff_only_content`；不读Full Prelude/Snapshot audit，不把Full输出拿作工具源。
- `HistoryPaths`显式接入辅助开关，缓存UID对应的part列表；同UID不同角色部分并存。对已经过model_only/human_only/hidden裁剪的同UID system部分集中合成一个system context，Read返回其原物理消息完整可见system正文；没有引入可见性较低的part。
- Search/Get Meta以(ref,UID,projection)去重，分别用现有native literal projection predicate验证各部分。只在user部分命中的内容不能假冒system命中，反向同理；没有建新检索器。原生降级/预算/索引完整性边界继续明确反馈。
- anchored Read接受既有semantic roles，默认优先原非compression部分（user/assistant/tools），roles=[system]可精确读compression；纯compression只有显式aux可见。分页固定同identity及roles对应的源部分，Schema明确重用同一选择。邻居/limit沿当前可见message parts计数；200/201容量仍为明确全返/拒绝，Get Meta单条仍严格四字段。
- 系统摘要部分清掉继承的tool call元数据，ToolInvocations跳过该合成部分；保留的assistant/tool部分继续按真实call ID与调用批次配对，系统摘要不能借到参数/结果。
- `cleaned_preview`仅对native已证明的compression part，复用原生summary prefix/end/delimiter解析去项目壳，再取头尾；结构化text parts也先取真实文本再去壳。mixed真人的字面引用、HTML、正文日期均保留。同semantic system合成预览从原来可见的两个部分分别清壳后按native相对顺序组合，Read不改原文。
- C11延迟stamp：仅当已可信归system且匹配项目标准外壳时，外壳内合法runtime timestamp允许与rowtimestamp相差数秒而清除。普通真人独立timestamp/自写HTML/无receipt Instant引用仍受原保护；返回独立timestamp始终用原rowtimestamp。

### 3）正式路径与边界

registry/原inline入口 → Schema/实参校验 → owning DB/Main或运行中Noting父域 → HistoryPaths（aux=false原History；aux=true新窄消息parts）→ 共用合法winner → 可见性裁剪/可信来源/同role system合成 → 按part独立查询匹配或角色锚点Read → 原有字符/容量预算及投影。

新辅助可读不扩大Notebook新事实来源资格。新接受例实际先读到纯摘要，再调用NotebookStore.create引用同UID，仍source_unavailable且无副作用；mixed原user部分仍可正常作为source创建条目。没有改NotebookStore、source validator或其它Notebook文件。

### 4）验证、版本、原始日志

最终History命令：

```bash
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/secretary/test_history_compression_parts.py tests/secretary/test_r3_history.py tests/secretary/test_history_source_modes.py tests/secretary/test_history_content_paging.py tests/hermes_state/test_secretary_message_provenance.py tests/tools/test_session_history_identity.py tests/tools/test_session_history_truncation.py -q
```

最终**7文件201通过、0失败，12.2秒**；分布30+82+47+23+3+8+8。原日志`.hermes-dev/noting-chain-20261027/review-evidence/history-compression-final.log`。新增Compression文件30项覆盖pure/mixed user/assistant/tool/system、同role system合成、逐角色query/分页、跨域fork memberships、Noting父域、原时间闭端点、200/201、double compaction/winner/rewind、隐私边界、同次toolpair、原生结构化消息、去壳预览、Notebook引用门禁。source_modes追加可信系统timestamp早于落盘5秒而原timestamp不变、真人相同包装与独立timestamp保持反例。读路径均核无DB写副作用。

扩核原生持久路径：`test_secretary_foundation.py`26＋`test_secretary_lifecycle.py`30全部通过，原日志`.hermes-dev/noting-chain-20261027/review-evidence/history-compression-second.log`。这两个文件未改；其受测`hermes_state_secretary_foreground.py`与最终该文件相同，后续只在History工具侧收敛同role合成/预览。

最终正式质量检查（独立临时Git index仅含本包12文件，真实共享index不动）与§4命令相同：`scripts/check --staged --only ruff,health --base 02d55fdb...`，**12文件、0 blocking / 0 advisory（1.0秒），2 checks ok**；原日志`.hermes-dev/noting-chain-20261027/review-evidence/history-compression-check.log`。直接ruff C901≤20与本包diff whitespace核查通过；检查规则/阈值未改。最终12文件SHA原件`.hermes-dev/noting-chain-20261027/review-evidence/history-compression-version.sha256`，见下方。

### 5）已有基线失败，不冒称关闭

扩核`tests/hermes_state/test_secretary_prelude_history.py`观察到15失败、9通过，主要仍调用已退休session_history或构造缺必填termination的Snapshot。遵主会话要求，在**未改源码/断言**的隔离树冻结临时基线树（精确路径见ignored `.hermes-dev/noting-chain-20261027/review-evidence/baseline-environment.json`）（实核HEAD=`02d55fdb45b4fb7c883fb477f4469912f4707f70`）以官方runner同文件定向复现：**同样15失败、9通过**，pytest自身2.32秒。

baseline原日志`.hermes-dev/noting-chain-20261027/review-evidence/history-compression-prelude-baseline.log`；当前扩核原日志`.hermes-dev/noting-chain-20261027/review-evidence/history-compression-second.log`；程序化比对的完整case IDs为`.hermes-dev/noting-chain-20261027/review-evidence/history-compression-baseline-compare.json`（same_failure_set=true，15项完全一致）。未改/删除这些测试，也不把它们算成新产品通过。此前扩核另外两项本包失败（aux邻居现在包括compression及完整读需显式大预算）已经按新明确契约保留原能力断言并修测试准备，最终201项全部通过。

### 6）接口影响与有效证据边界

接口仅既有roles在anchored Read正式可用，以及Compression显式辅助分部；Schema/handler实际入口同步。默认范围、原History/Full APIs、Message Identity/UID、权限、source timestamp、native session_search不变。Get Meta同UID可返回user/system两个四字段行；同semantic system只一个合成视图；Read无角色选择优先原非summary部分，纯摘要才取system。

主会话`reports/model-evidence.md`的k3.1-pro/high两Task6次HTTP全200样本在新增Compression分支前已完成；其受测source hashes保留在私有result.product_sha256。该样本没有compaction/auxiliary输入，此修复不影响其受测分支，不能冒称它覆盖了新C14；新增分支由上面的正式native DB机制覆盖。未再网络调用模型；父子Schema冻结/当前构建一致性由主会话按最新交付定向补证，无理由不重跑昂贵样本。

### 7）后续建议

主会话亲审本包与本节，复用当前201项/原生56项及基线15项对照；优先复核shared winner提取保持默认API、可见性在system合成前、各part匹配/角色续读与工具配对，然后进入独立Verification→Validation。无已知本包范围内未修失败；全轮独立门禁/部署、生产转换及基线失败最终判定仍归主会话。未提交、push、部署或修改生产/凭据。

```text
25485c9a0f567dda5d89e5191caabc7518b072823c779a2136f02d9a12deb94e  tools/session_history_tool.py
562e3ebda61e40a970d8c27af443802db453d672e1314f3b55d6157b60abbda0  tools/conversation_history_projection.py
9d85dead7d077072e4a8f03624a322e9ec151c8438253e41add1d19d6d798602  tools/conversation_history_time.py
fd6ec47f1f792b713ac8b4f58eb2ab10f0fd6e10f8fde40958c7d67e1ee87ca4  hermes_state_conversation_history.py
c3fdd47db95698820a26e78e5233b6412cc99edc730c21649b8414cff428fe06  hermes_state_message_provenance.py
9db481d1665cc1af608e0d97fb12ea342e642e3f8672ad9d0afb76ab4824d524  hermes_state_secretary_foreground.py
979cfc08366fde69635382ae565018a31857c7a5287a2fe33188133c90a19814  tests/secretary/test_r3_history.py
53971b631f3d42489c2d22f730e74a4b72a22f56bd31afffc87fff876d981f44  tests/secretary/test_history_content_paging.py
2e45e670808e97a87a6cc03aea648ce64ff1c296fd25c06c558846acedc5b372  tests/secretary/test_history_source_modes.py
1836110f4c808f3afe98a6c11149215ac8684c1b6c06fb14a250b476d350a67a  tests/secretary/test_history_compression_parts.py
15c2157c01bd7e34a07e81214e3ef9522910542ea9df199bc3ffdd8326ce14c3  tests/tools/test_session_history_identity.py
04a5e1f842d70b437d17b0c4b258fb7ed0005ec43ba2ec885ed9743b6e58f3a0  tests/hermes_state/test_secretary_message_provenance.py

```

原始临时证据的受限副本统一在ignored `.hermes-dev/noting-chain-20261027/review-evidence/`；报告中历史路径对应运行当时，副本同名。
