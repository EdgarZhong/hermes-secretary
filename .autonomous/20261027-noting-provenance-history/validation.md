# Validation：20261027-noting-provenance-history

## 1. 结果概览

独立验收者：Validation 子 Agent（全新无实施上下文，不派生）；执行日：2026-10-27。依据为本目录 `snapshot-index.md`、`baseline.txt`，基线 `02d55fdb45b4fb7c883fb477f4469912f4707f70`；唯一待验产品 `3426c0fc9579dc0589fd0a831741b535aee71ca2`，执行期间保持此HEAD且产品只读。

**本地 Validation PASS：17项适用用户场景通过；生产执行D01对本地环境有依据不适用。无新产品缺陷或范围内未执行项。** 六节完整计划先落盘并经主会话完整过目、明确允许后才执行；原计划保存在 ignored `validation/plan-before-execution.md`，未缩减场景。新增独立正式旅程脚本最终10项通过，5.8秒；复用已核适用范围的机制与真实模型原件，不复跑大套或模型。

用户目标覆盖：无推进保持原样；真实属性编辑与本Task来源同传、同Task覆盖／后Task追加、旧节点不可改；逐来源组原始Evidence time；“稍后处理”仅补缺失Schedule建议；History三模式统一语义角色／默认范围／辅助与跨域开关／闭时间端点、Get Meta四字段与完整性、工具同次参数结果及有界续读、Compression辅助读取；正式权限、恢复、原子Snapshot及有效结果发布。

本地PASS不等于整个“改好、测好、上线”目标完成。主会话尚须执行D01：将通过双门禁版本合入main，按自然空闲、备份／转换／启动／版本及数据验真完成唯一获授权生产目标。未操作生产、用户页面或显示状态。

## 2. 环境与准备

- 软件／环境：macOS、项目官方PM既有 `.venv`、原lock；真实SessionDB／Secretary表、原生AIAgent／runner／SDK序列化、正式registry和RPC handler。未安装依赖、改配置或测试产品代码。受控SDK／本地回环HTTP只负责提供确定性模型响应与失败时序，不冒称真实模型内容表现。
- 数据：全为独立隔离虚构Profile、SQLite和合法中间态。Profile `terminal.cwd` 在仓库Git root外；当前测试的合法用户Conversation有真实user起点。脚本用外联socket硬拒绝，RPC仅127.0.0.1。正式入口包括 `tools.registry` 注册的 `conversation_history`、typed六工具、`run_noting_task`、原生Main `_invoke_tool`、`secretary.noting_recover/recovery_state`，没有孤立helper自证代替正式入口。
- 写入范围：只本报告、ignored `.hermes-dev/noting-chain-20261027/validation/` 和下列证据索引；不改产品／已有测试／其它报告，不提交push。原dirty文档及主会话新报告保持。测试自动写的ignored字节码／时长缓存不作产品变更。
- 唯一Python执行方式：`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh .hermes-dev/noting-chain-20261027/validation/test_validation_journeys.py -q`。最终日志 `validation/run-final.log`：10通过、0失败、5.8秒。夹具诊断各轮定向执行保存在 `run-1.log` 至 `run-5.log`，原脚本版本保存为 `journeys-run*-source.py`，未删失败。
- 显示保护：无UI变更，全部从软件正式入口验收；未启动浏览器、桌面控制、可见页或显示工具。UI/APK及生产Linux服务实际运行不是本地模拟等同物。
- 阅读与覆盖：根AGENTS／CLAUDE、Snapshot Index／baseline、07最新顶部与R20／v2保留条款、Notebook白板全篇（含动态类型与完整场景）、02身份／Foreground／Snapshot及来源／运行，04 §2–5保留接缝，01 §1、3–4，06 §0／1.12与现行读取边界。plan仅作线索，不作为判定依据。不读archived、不用Verification结论代替独立场景判断。

证据简称均相对 `.hermes-dev/noting-chain-20261027/`：

| 简称 | 原件及适用边界 |
|---|---|
| E1 | `validation/test_validation_journeys.py`、`validation/run-final.log`及H／N／R命名JSON；本次独立当前产品正式操作和原始结果，10项最终通过 |
| E2 | `final-integration-tests.log`：40文件1094通过；读取对应测试的正式入口、输入、断言与上下游，只复用未被后继V01改变的身份、权限、候选、时间、恢复、原子性、结束及发布分支，不复跑 |
| E3 | `review-evidence/history-v01-tests-final.log`：4文件107通过，覆盖现行53项source modes、30项Compression、23项paging和V01原反证；V01仅撤去额外Gateway文本清理，已读3426相对4032实际差异，不影响E2其它分支 |
| E4 | `e2e/live/`：两Task六wire、两个transcript／construction／usage、seed与前后Notebook；本次独立重新解析并记录于`validation/M01-M02.json`、`validation/model-actions-and-reuse.json`。真实模型为k3.1-pro／kimi-coding／high；不是当前HEAD全部路径模型测试 |
| E5 | `release/linux-final-tests.log`、`release/linux-final-source-verification.json`：实际Linux7文件132通过、3426的18,394 tracked blobs按attributes校验；只作平台机制补充，不等于生产发布 |

E4有17个来源文件指纹，其中8个在采样后变化：`hermes_state_message_provenance.py`、`hermes_state_conversation_history.py`、`tools/session_history_tool.py`、`tools/conversation_history_projection.py`、`secretary/notebook_contract.py`、`secretary/notebook_items.py`、`secretary/notebook_model.py`、`secretary/notebook_store.py`。主Prompt、六工具契约、runner、typed handlers、证据时间派生、投影和恢复源码与样本指纹一致；后继Compression辅助投影、Candidate本Task来源形式切换及V01文本清理另以E1/E3现行正式机制补证。故E4支持所观察的普通matter更新／建议／无推进／冻结前缀代表旅程，不能声称新增分支跑过真实模型。旧失败样本保留在 `e2e/failed-schedule-description`、`failed-schedule-description-clarified`、`book-gap-fixture`。

## 3. 用户目标与场景覆盖

| 目标编号及冻结依据 | 完整场景编号 | 场景类型与起点 | 数据/顺序选择依据 | 当前执行结果 |
|---|---|---|---|---|
| C09–11、16–18；07顶部 | H01 | 当前Conversation→Get Meta识别→Read原文→重开DB再读 | 无关键词／FTS include／roles、两个闭端点、长短正文、自写日期HTML及可信timestamp | 通过，E1＋E3 |
| C12–14、20；02 §1–2 | H02 | 真人／Assistant／系统载体／工具混合历史，三模式及邻居 | 默认范围不能被旧工具参数／roles绕过；分类在清理前 | 通过，E1＋E3 |
| C10、17 | H03 | Get Meta完整返回／显式拒绝 | 200整点／201、过滤后1条、45条及枚举／索引失败 | 通过，E1＋E3 |
| C12、20；02路径契约 | H04 | Main显式跨域、Noting仅父、fork继承后rewind/exclusion | 同Profile授权域／内部child／foreign数据隔离、同UID不同Ref、只读 | 通过，E1＋E2/E3 |
| C15–16；07 §5.3 | H05 | Search工具→Read→分页重组→后续可用 | 同批双call逆序、缺源、歧义、长参数／结果各头尾200、闭时间与每页授权 | 通过，E1＋E3 |
| C13–14、20；04 §2.5 | H06 | native纯／mixed Compression三模式 | 默认真人、显式system、同UID分片、隐藏／Prelude拒绝、分页不串片 | 通过，E1＋E3 |
| C02、04–05；白板U1／R20 | N01 | 已有Notebook无进展→no-op→Finish→Main再读 | 助手提示／到期／沉默无变化，不增item／节点／时间 | 通过，E1＋E4 |
| C04–05、20 | N02 | Task A创建→多调用／续Turn覆盖→提交→Task B追加→旧Snapshot再读 | UID槽完整替换、普通字段合并／数组替换、跨Task可重复UID、稳定ID | 通过，E1＋E2 |
| C04–05、07–08、20 | N03 | 非法编辑拒绝→修正→提交 | 属性与来源同传、仅来源／旧节点／缺源／时间范围／只读时间、原子拒绝 | 通过，E1＋E2 |
| C07–08；07时间确认 | N04 | 各角色组→时间链→覆盖／追加→show及持久再读 | 真人单点／多点范围、无真人最近Assistant、仅辅助范围、未知null、正文日期不改原timestamp | 通过，E1＋E2 |
| C06–08；白板C3／C6／C9 | N05 | direct／refs→源更新→形式切换→提交→后Task拒绝历史槽删除 | refs沿源派生、标签／反向refs、本Task唯一未提交槽与历史槽边界 | 通过，E1＋E2 |
| C02–03、18–19 | N06 | “稍后处理”缺口／已有排期／无提及→建议或原样→Main | 只建议及来源，不造推迟时刻、不登记；条件Framework | 通过，E1＋E4 |
| C20；07 §3／4.5／8 | R01 | Main／普通child拒绝写；Noting六工具；Finish和预算边界 | 同步／并发／invoke、混批、重复、end_requested后写拒绝、forced／overflow | 通过，E1＋E2 |
| C05、20；07 §12 | R02 | 失败child已有成功编辑→正式RPC恢复→同槽覆盖→查询幂等 | 冻结旧材料、失败记录保留、原生runner／Commit Gate、完成不等于提交 | 通过，E1＋E2 |
| C20；07 §8.13／11.1 | R03 | 新旧Anchor交错提交→busy队列→新pointer取代→Main | 完整Snapshot原子性、旧通知剔除、live/durable一致、无版本／owner泄露 | 通过，E1＋E2 |
| C02–03、18–20 | M01 | 真实模型：12→18盒、税表稍后处理、取书已有排期 | 六wire中第一Task4请求；实际History／编辑／Finish／Notebook | 通过，E4代表样本＋E1/E3现行机制 |
| C02、04–05、18–20 | M02 | 真实模型：第二Task助手提示未获回应→Notebook完全不变 | 第二Task2请求，只Get Meta／Finish，逐字段及item版本相同 | 通过，E4代表样本＋E1现行机制 |
| C01；部署SOP | D01 | main生产发布及唯一置顶Notebook转换 | 自然空闲、真实身份、三库备份、服务版本／数据终验 | 本地有依据不适用；主会话仍须上线终验 |

覆盖方法：以完整目标旅程为主，再按语义来源、权限域、模式、长度／容量／时间边界、同Task与后Task、direct与refs、正常与失败／重启、压缩／fork／rewind和通知顺序补充分支。E1实际连接History→UID→Task编辑→提交→Main输出；E2/E3用于稳定构造竞态、预算、失效及间接调用分支，不用helper或模型自报替代真实用户结果。范围外旧完整能力不重新立项；自然语言全部可能写法未穷举，模型结论仅限固定虚构样本。D01没有被移除或冒称完成。

## 4. 详细场景与执行结果

以下实际产品均为3426；E4单独标明先前样本及源码适用性。执行时间均为2026-10-27。完整参数、原回执、数据库再读和断言见E1脚本与同名JSON，本文保留足以复现的业务顺序。

### H01 · 识别来源后读取原文

起点／历史：当前真实user起始Conversation，UID `u` 正文为项目timestamp＋用户自写HTML／日期及长事项，Assistant位于上界；另有用户自写timestamp／framework文本。输入：Get Meta `[1800000000,1800000100]`，再单点闭窗和FTS include `"事项原文" OR 心跳`。正式操作：registry Get Meta→用返回UID anchored Read→重开同DB再Get Meta和Read。预期：四字段、先剥可信timestamp再头100尾100、自写正文保留、端点纳入、Read原文不改。实际：全部满足；include与Search命中UID相同；原始消息及重开结果相同、读取total_changes不增。证据：`validation/H01-H02-H04.json`、E3的原V01真人粘贴反证。**通过**。偏差：增加合法起始user；未改变输入内容特征或预期。

### H02 · 三模式统一真人范围

起点：同一历史含真人／Assistant、instant Reminder、Heartbeat、Framework、Notebook、hidden和工具；物理user并不等于真人。输入／操作：Get Meta、Search、unanchored Read和anchored邻居，各传四种roles并分别关闭／开启include_auxiliary；Search还显式传旧include_tool参数。预期：默认仅真人和Assistant；开启才出现系统／tools，hidden不出现，定点辅助无开关失败。实际：所有模式默认无四类系统载体；开启后统一system，工具统一tools；hidden始终不读，邻居不绕过。再读：原文与DB变更计数不变。证据：E1 H01 JSON及E3 `test_semantic_roles_and_auxiliary_gate_cover_all_modes_and_neighbors`／可信legacy载体用例。**通过**，无缩减。

### H03 · 完整窗口或明确失败

起点：200条当前user同窗消息。操作：Get Meta返回200条→添加第201条assistant→同窗再读→按assistant过滤。预期：200全部返回且complete；201不能成功带部分messages，须要求缩窗；过滤后容量按实际命中。实际：200完整，201 `window_too_large`无messages，过滤后1条，查询不写DB。枚举预算／来源判断／索引不可用和stale的有界失败，复用E3当前正式registry场景，确认错误而非“完整空结果”。证据：`validation/H03.json`、E3 source modes相应用例及107项日志。**通过**。

### H04 · 授权域、fork与失效来源

起点：用户main、同Profile另一真实用户Conversation、fork及绑定admission的Noting child。输入／操作：Main默认及cross=true Get Meta；Noting默认及cross=true；fork已继承UID后将父物理源置失效，再添加branch exclusion。预期：Main默认不跨、显式按外层Ref分组；Noting仅父、cross拒绝；父失效不抹合法branch继承，branch exclusion后不可读；不写binding。实际：均满足，Noting `scope_denied`，父返回0但fork仍读shared，排除后0。重开当前DB仍可用；foreign Profile和内部非用户runtime及跨压缩身份边界复用E2/E3正式权限用例，不探测实际用户Profile。证据：`validation/H01-H02-H04.json`、`H04-bound.json`及E2/E3。**通过**。夹具曾缺真人起点，补为合法Conversation，未将不合法起点的空结果误判产品缺陷。

### H05 · 同一次工具参数和结果可读

起点：同一Assistant批次A/B两call，B结果先到、A后到，A参数和结果均长；另有缺call的orphan。操作：显式aux＋tools Search定位needleA→取A结果UID，content_offset=0、每页64字符续读到null→JSON重组→orphan定点Read。预期：Search各头尾200，无哈希，不能混B；Read完整参数／结果，缺参null。实际：A正确配对，页拼接精确等于canonical JSON，B未串入，orphan参数null。再读及缺失／歧义／跨Turn／隐藏边界反例采用E3当前paging和source modes证据；每页仍验证同scope／合法路径。证据：`validation/H05-H06.json`、E3。**通过**。偏差：起初无真人起点不能成为检索用户路径；已保留run1–3并补合法起点，没有放宽搜索或配对断言。

### H06 · Compression仅在显式辅助视图可达

起点：native `archive_and_compact`构造同UID mixed摘要＋真人原文，保留原始消息；纯摘要、反复压缩、Assistant／tools mixed等合法变体取E3。操作：默认Read、aux＋roles=system Read、Get Meta、Search，随后同原UID分别再读片段。预期：默认真人不变；开启才读system摘要，不造UID；四字段Get Meta可分别投影，隐藏／Prelude及Notebook原始证据准入不扩大。实际：同UID两语义视图正确；默认搜摘要为0，aux搜得system；默认roles=system失败，私有Prelude从未出现；查询不改原生History/Full。证据：E1 `H05-H06.json`、E3 30项native Compression。**通过**。偏差：首次完整摘要读取超过原默认2000字符而有明确截断；按既有预算参数扩大到20000后完整返回，长片段分页另有E3，不将截断当丢失。

### N01 · 无进展不造变化

起点：已完成两Task的Notebook，第二Task已done=true；后续仅查询状态。操作：第三Task提交相同done值和来源→Finish→Main notebook_show；另审E4只有助手提示／到期且用户未回应的完整第二Task。预期：普通属性、版本、来源及时间完全不变。实际：no-op不增item，payload逐字段不变；第三Task合法Snapshot不意味着新entry版本；E4第二Task完整Notebook与第一Task相等、取书旧条目与seed完全相等。证据：`N01-N02-N03-N06-R01.json`及E4。**通过**，无以description润色代替保持。

### N02 · 同Task覆盖、后Task追加

起点：原生Main真实对话→Task A Get Meta取得UID。操作：runner create matter→同Turn更新domains→文本结束但未Finish→同child续Turn仅加建议及完整来源→Finish提交；Main新消息→Task B补done及新UID→提交；再读旧Snapshot和旧item原始JSON。预期：A多次／续Turn始终一槽；B追加，稳定entry_id；fields合并／数组全替换；历史版本不变。实际：A `[[uid]]`，B `[[uid],[next_uid]]`；旧item原始JSON及旧Snapshot完整审计投影前后相等；Main show读到同链。跨Task同UID合法复用由E2当前来源数组用例支持。证据：E1 N01 JSON及E2。**通过**。初稿将审计投影与普通投影混比导致额外内部字段差异，改为同一审计投影前后严格相等，未放宽不可变要求。

### N03 · 拒绝后可以正确继续

起点：上述Task B已有条目。输入：done=true但缺本Task来源；随后同一编辑携合法新UID。预期：第一条拒绝且无变化；后续正确编辑提交。实际：`invalid_argument`具体指出完整Task来源数组；修正后只有一新节点。N05同传直接来源与refs拒绝前后working state严格相等。E2保留缺源／duplicate／missing或foreign UID／仅来源／时间范围／伪造provenance/evidence_time、rewind后新源失效及commit失败的原子反例。再读：Main只显示成功编辑、旧版本原文保持。证据：E1 N01/N04 JSON、E2来源／visibility／snapshot用例。**通过**。

### N04 · 时间来自每组原消息

起点：当前合法历史含user100/300、Assistant200/500、system400/600及timestamp未知UID；正文明确叙述“昨天完成”。操作：typed create按角色组合取证→show→提交→Main show；E2同Task覆盖、后Task追加、重开DB并读取原Evidence time。预期：user优先100–300／单100，无user取Assistant500，仅system取400–600，未知null；一组一槽、原消息timestamp不被叙述日期或维护时间替代。实际：五组均精确符合；可信system user载体未抢真人优先级，模型视图未知仍保留null槽。E2持久时间在读取／重启／源timestamp后继变化时不刷新。证据：`validation/N04-N05.json`、E2 `test_notebook_provenance_arrays.py`。**通过**。

### N05 · Candidate来源二选一与工作槽边界

起点：同Task matter源和direct Candidate。操作：typed Candidate direct→显式清本Task唯一未提交槽、改refs＋matter标签→尝试混传direct被拒→清refs切回direct→提交→新Task尝试清旧direct改refs。预期：refs无伪直接链，Evidence time沿源；同Task合法切换，旧Task／已提交来源不可删。实际：refs evidence等于source，混传拒绝且工作态不变，切回只一direct槽；提交后切换拒绝且状态相等，Main及Snapshot再读原direct链。反向candidate_refs／隐式gap标签映射、源更新及恢复切换的正式native链复用E2当前52项Candidate、32项来源数组及4项task恢复。证据：E1 N04 JSON、E2。**通过**。

### N06 · 稍后处理只补排期建议

起点／输入：虚构税表“稍后处理”、采购数量改变、取书已由正式Scheduler登记且对话给出证据；无明确推迟时刻。操作：真实模型Task1自行Get Meta、执行两次notebook_update、Finish；E1现行runner另仅补suggestion并在Main读取。预期：税表只suggestion和本Task来源，description/done及其它普通属性不改；不造具体时间、不自行登记；取书无缺口不改；有建议才附Main语义提示。实际：税表fields／done与seed严格相等，新建议自包含且写“未指定具体时间”，取书整条与seed相等；实际工具无scheduler调用；E1Framework含条件语义建议提示，Main show可读。无建议不附提示和建议不改变实际Schedule的分支复用E2 schedule_suggestion用例。证据：E1、E4和 `existing-book-schedule.json`。**通过**。

### R01 · 权限、Finish与合法兜底

起点：原生Main及冻结完整顶层工具的Noting child。操作：E1 Main直接invoke更新被拒；runner本Task成功用History／Create／Update及最后Finish，跨Turn继续同工作态。预期：声明不授权限，Main/普通child不写；Noting仅六工具；Finish回执end_requested不是committed，混批无副作用；退出后不能写，预算兜底诚实。实际：Main `scope_denied`，正常Finish后runner提交；逐请求root／tools相同、无消息级tools。同步／并发／invoke wrapper、普通child和Scheduler等拒绝、混批整批拒绝、重复保持首次reason、结束后写state_conflict，以及原生Turn返回后才commit、forced/overflow/真实失败、不启用保原生，逐项读取E2正式SDK／runner用例及相应通过日志，不依靠模型偶然没越权。证据：E1 N01 JSON；E2 `fixed_noting_permissions`86项、`noting_finish_exit`22项、`r3_child`56项及native surface证据。**通过**。

### R02 · 失败后沿旧任务继续

合法中间态：失败child已从base条目成功编辑一次并持久维护回执，但没有发布新Snapshot。输入：正式RPC目标Profile／Conversation／failed_child／request_id。操作：`secretary.noting_recover`→本地native HTTP请求先show恢复工作态→update来源`[evidence,anchor]`→Finish→recovery_state轮询→重复同request_id→读取Main尾部、失败旧child和Snapshot。预期：用旧root/tools/前缀及成功工作态，同Task覆盖第二槽，不新增第三槽；实际committed才能成功；旧记录、排期和launch Profile保持。实际：completed且committed，链从旧首槽＋失败Task槽变为旧首槽＋覆盖槽，长度不变；旧child全文相等；幂等返回相同operation／Snapshot，没有新模型请求；租约释放，当前尾部Framework指向新Snapshot。缺料／歧义／重启interrupted及同TaskCandidate切换恢复复用E2原生失败恢复用例。证据：`validation/R02.json`、E2正式debug integration及task recovery。**通过**。无生产旧任务重放。

### R03 · 只发布当前生效结果

起点：一个当前Main和三个从合法同base冻结的Task工作态，旧Anchor及新Anchor交错。操作：标Main busy→旧范围先commit并排队→新范围commit并排队→另一旧范围晚commit→busy结束flush→Main show及数据库尾部再读。预期：晚旧Snapshot可审计但不回退pointer，不发布旧通知；队列只留下新pointer完整Notebook；live/durable同一条、无新Turn及内部owner/version。实际：晚旧 `pointer_changed=false`且publish=false；busy期间原历史不变；flush仅新增一条指向新Snapshot，正文只含当前有效范围；Main show同内容，live与durable一致。事务中竞态、owner切换回滚、fence／rewind／off拒绝及失败不发布草稿复用E2 r3_framework／foundation／lifecycle。证据：`validation/R03.json`、E2 19项Framework及保留机制。**通过**。

### M01 · 真实模型实际执行代表旅程

原始输入：seed采购12盒S-17／只接受可退货／未下单、税表待决定、周五南门取书；当前用户采购改18盒、税表稍后处理，Assistant已给出取书登记证据。操作：独立读取4份原始wire、child1 transcript、construction、usage及before/after。预期：模型识别UID、只改相关意义、只补建议、已登记保持、最后独立Finish，正式持久结果可理解。实际调用顺序 `conversation_history(get_meta)→notebook_update→notebook_update→finish_noting`；4请求HTTP200，采购仅12→18，条件全保留；税表fields/done不动、建议与来源新增，取书整条不动；旧来源／时间槽保持。逐请求冻结父前缀相等、root和顶层tools各唯一SHA，无消息级tools。Task1实际cache_read=72192，输入15182／输出1306／reasoning634；无实际账单，不从estimated_cost=0宣称免费。再读：notebook-1.json对应实际Snapshot，内容如上，第二Task可继续使用。证据：E4与独立 `M01-M02.json`／`model-actions-and-reuse.json`。**通过，限代表样本**；8个后继源码差异按§2补证，不冒称全HEAD模型测试。

### M02 · 后续只有提示仍保持原样

起点：M01的完整Snapshot，第二Task可见Assistant提示／提醒，用户未回应，无新的采购／税表／取书进展。操作：独立读wire5–6、child2 transcript／usage和Notebook。预期：不重写普通属性、不改done、不追加来源／时间，不因提醒到期造进度或重复建议。实际调用仅Get Meta→Finish；2请求HTTP200，notebook-2与notebook-1全payload严格相等，原版本标识相同；因此原item／链未新造。cache_read=36608，输入6266／输出1192／reasoning937。子请求前缀均一致，后续可继续读来源。早期旧型号两次顺手改description失败及首次正确型号取书夹具缺证据样本保留；最终样本靠补正式已有排期证据，没有放宽“原样保持”断言。证据：E4及独立模型审计JSON。**通过，限代表样本**。

### D01 · 生产发布与唯一转换

用户目标C01仍要求上线。预期顺序为双门禁通过→main发布→自然空闲停服及三库有效备份→核准Alex唯一置顶Conversation转换→服务／数据／版本终验。本地验收者只获隔离虚构数据写权限，故生产写入、真实服务启动与唯一真实Notebook转换对本地环境**有依据不适用**。E5可补Linux同代码机制、已有转换副本证据可供主会话审查，但均不能冒称已上线。本报告未调用SSH生产或复制真实Notebook正文。

## 5. 问题、修复与复验

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| VAL-F01 | 原独立runner夹具调用run_noting_task缺task_instruction | 正式函数必填任务正文，TypeError；run-1.log | 验收脚本错误，不是产品缺陷；已补当前DEFAULT正文 | 产品始终3426；只修ignored脚本 | 最终N01–N03/N06/R01通过 |
| VAL-F02 | H05只有Assistant与tools、无真人起点；先误以为FTS词边界，补空格仍空 | 不属于获授权真实用户Conversation，返回完整0；H05-debug及run1–3 | 合法起点准备不足；已补起始user，不改实际工具输入特征／预期 | 产品始终3426 | 最终Search→分页重组→Compression通过 |
| VAL-F03 | N02把旧Snapshot审计entry与普通current投影直接比较 | 业务字段相同，但审计owner／archived与candidate_refs投影不同；run-2.log | 比较视图错位；改为同一旧Snapshot审计前后严格相等及原item JSON字节相等 | 产品始终3426 | 最终旧版本／旧Snapshot不可变通过 |
| VAL-F04 | H06以默认2000字符Read要求完整native摘要 | 返回有明确省略的预算截断；run-4.log | 未传足够预算；按既有参数20000／100000读取，保留分页证据 | 产品始终3426 | run-5及run-final通过 |
| 历史模型失败 | 旧别名模型两次顺手改税表description；首次k3.1-pro缺取书已登记证据 | 失败原件保留；最终正确型号、正式已有Schedule条件下通过 | 已修Prompt明确边界／补合法夹具；不删除或宣称旧样本通过 | E4采样版本，§2限定 | M01/M02独立复核通过；当前机制另E1/E3 |

无新产品缺陷，无为通过而修改产品或既有测试，无需主会话新增整改项。本表保留夹具与视图错误的完整原因，避免将修夹具隐去。最终10项全通过；以前失败不被删除，也不累计为当前产品失败。

## 6. 验收结论与推荐复核

**本地Validation PASS，17项适用场景通过，D01仅对本地环境不适用；没有范围内失败、阻塞或未执行场景。** 当前证据支持3426的来源链／Evidence time、History三模式及其正式权限／恢复／提交旅程；支持既有真实模型两个Task代表输入的内容表现和逐请求冻结前缀，不承诺所有未来自然语言输入，也不将后继新增分支包装成已跑真实模型。

建议主会话复核实际产物：

1. `validation/N01-N02-N03-N06-R01.json`：同Task跨Turn仅一槽、后Task两槽、no-op item不增、旧版本不变、Main show与有效Notebook一致。
2. `validation/R02.json`／`R03.json`：正式恢复同Task槽位及幂等、busy队列只发布新pointer完整结果。
3. `validation/H05-H06.json`：工具参数结果的Search头尾预览与完整canonical重组、同UID真人／system压缩两视图；E3原V01反证确认用户自写Gateway文本保留。
4. `e2e/live/notebook-1.json`与`notebook-2.json`以及独立模型审计：税表只补建议、取书原样、第二Task完整payload不变，实际工具和wire可逐项核对。

最终整体目标判定仍由主会话负责。下一必做为D01生产发布、唯一Notebook一次转换及服务／消息／排期／绑定／其它Profile不受影响的真实终验；本报告不授权扩大数据转换范围、不宣称线上成功。
