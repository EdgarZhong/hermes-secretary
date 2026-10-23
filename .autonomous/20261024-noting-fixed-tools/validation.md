# Validation：20261024-noting-fixed-tools

## 1. 结果概览

验收者：独立 `fixed_tools_validation`（Sol/high，全新上下文，不派生）；2026-10-24。依据：本轮 `snapshot-index.md`、`baseline.txt`，冻结 `56b7ebc01131ea4eaad0a4690c0bfbab048c2803`，授权追加 `3ce7517dc7c4e6dbdae7de1607032c8281ff0e24`。产品 Core `1ea38ef16addaac2cb441029e38f07578d3738dd`；实际部署文档后继 `0e14d4e52ffcded688ddaafbc0f2d1d91deebaed`（已独立核对产品无变化）；独立 UI `589df02706d3c6738789ff97fcb652a0bf76c398`。

用户目标：保持原两工具Schema/description并固定完整顶层声明，Main禁用且真实Noting仅准四工具，任务及续Turn去重复Schema、父子冻结前缀一致；Alex隔离真实kimi-for-coding自然与能力旅程正常完成；实测超过N38的N46长前缀；与今日599d114/589df02联合发布，保持生产数据与配置。

进入条件：Verification本轮完整复审已PASS；本报告先独立建立场景并交root过目，然后执行。本地门槛与最终门禁分开：S1–S6/S8全部适用项通过可放行root部署；S7必须在真实部署后只读验真才可关闭最终Validation。root已完整过目并接收S1–S8计划，授权执行本地S1–S6/S8；2026-10-24开始。当前**S1–S8全部适用场景通过，最终Validation PASS，门禁已关闭**。本地验收先放行root部署，root实际stage/apply verified后，本验收者再独立只读核S7；不存在部署前预签生产通过。

## 2. 环境与准备

- 只读产品代码；只写本报告与 `.hermes-dev/noting-fixed-tools-20261024/validation/`。必要隔离操作使用仓库外新建0700目录，T3隔离测试DB经SQLite只读backup到新根；不改原件，不操作生产写入，不提交/push/部署。
- 公开入口：原生CLI `/notebook`、`/noting`；原生Secretary/History工具与AIAgent正式facade；TUI/RPC只读session/context/history/Notebook；生产只读版本、健康与静态资产接口。能用CLI/RPC则优先，不启动模型或新的付费请求。
- 真实模型证据复用T3各run的实际请求/响应、wire、DB、Framework、后续Main回答；独立核对产品SHA、输入和用户结果，不用模拟模型冒充真实Kimi。受控SDK证据只支持确定性权限/并发/失败/adapter机制，不冒称真实微信发送。
- 正式解释器与测试规则遵守AGENTS；若有必要定向反证，仅 `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh ...`，不裸pytest、不跑大套。
- 图形边界：仅可自己创建隐藏IAB `iab, visible:false`；禁止桌面、外部浏览器、现有用户页面、可见页、焦点变化、open/open_in_codex。不能保证后台就如实记未验，不回退。
- 真实样本环境差异：Alex完整业务Root/Persona，独立Home/runtime/DB与仓库外cwd；本地缩Idle/长度阈值，MCP外发/排期扫描/Heartbeat关闭。实际模型kimi-for-coding High（原生probe另列），生产仍K3/原生产阈值。最终报告须区分这两个环境，不声称模型泛化率/最大窗口/真实微信触达或手机长期表现。
- 执行准备将记录HEAD/UI HEAD、20文件产品SHA、PM/lock、原件SHA和新隔离路径；敏感原件只留ignored0600，不在报告中复制凭据或Persona。

## 3. 用户目标与场景覆盖

| 目标编号及冻结依据 | 完整场景编号 | 场景类型与起点 | 数据/顺序选择依据 | 当前执行结果 |
|---|---|---|---|---|
| G1 C01/C02/C05，user-request 1/2/5/6，07§3.1/8.5 | S1 | 自然Main普通工作→工具可见但不越权→正常回答 | 默认自然Main与显式能力样本分层；统计真实请求和误调，不以0次证明硬拒绝 | 通过（本地） |
| G2 C03/C07，白板N1/P2，07§4.5/8.11–13 | S2 | 合法prepared历史→Main进展→Idle新child→History/维护/纠错→独立finish→Snapshot→父原生压缩→Framework→后续Main | 使用完整成功默认短样本；保留初短insufficient与would_grow的未完成历史；正文来源/完成状态与用户意图逐项对照 | 通过（本地） |
| G3 C04/C07，07§3.2/4.5/7.2 | S3 | 有未提交修改的Noting→原生steer要求读working→Show→继续原任务→finish/Commit→可读持久结果 | Show默认自然0；独立能力分支只在未finish时执行，不复活旧child；旧护栏截断失败保留 | 通过（本地） |
| G4 C11，user-request冻结后追加 | S4 | N46=184条完整长历史→真实Main→manual joint Noting→固定工具维护/finish→合法Snapshot/Framework | 实测本模型input超N38代表点；不得先压缩，不把manual说成Idle；真实父子wire核对 | 通过（本地） |
| G5 C04/C05/C10，07§3.1/4.5/7.2/12，AGENTS不启用即原生 | S5 | Main/普通child越权、Noting非四工具/跨域、混合finish拒绝→合法恢复；开关/恢复/失败资源边界 | 等价类为真实运行身份、调用路径(sync/concurrent/invoke/Loop)、全局/local门禁；复用当前代码机制原件并实际读正式公开状态，保持拒绝零副作用 | 通过（本地） |
| G6 C08/C10，06§1.4/1.12/1.13，07§8.13 | S6 | 今日微信正式正文/Redirect/Framework边界、Web标题及context/usage/时间修补→原有用户结果可用 | 按599d114完整变更定位适用验收，不扩大Thinking/Timeline/旧历史恢复；adapter受控证据与真实发送分开 | 通过（本地） |
| G7 C08/C10，cloud SOP§0/2/8 | S7 | 本地放行→root固定版本部署→只读Web/Gateway实际版本/API/WS/微信连接→三库/Notebook四表/配置与静态资产对账 | 正式新表集preflight/apply和部署receipt；Secretary439/UI589df02、Dashboard保持；不以旧preflight或版本存在冒充上线 | 通过（生产独立只读终验） |
| G8 C06/C07/C10，白板P6，07§4.5/5/8.13 | S8 | 成功测试库冷备份到独立根→正式/notebook及/noting→History检索/Read→对照已完成/待办/预算/规则→再次读取 | 验证持久化与后续可用性；独立执行真实公开读入口，不只读测试通过数；不再调用付费模型 | 通过（本地） |

枚举边界：本轮增量及明确保留接缝；不重验整个旧产品或外部Provider治理。完整自然旅程覆盖正常路径、参数错误纠正、压缩后续做；S3覆盖合法中间态和显式能力变体；S4覆盖长输入边界；S5按身份/路径/门禁/并发/失败等价类核对；S6覆盖同批既有修补；S7覆盖实际发布闭包。真实Main自然频率只报告样本数量与所见，不能证明一般误调率。真实SDK/模型不可替代处复用有效原件，时序故障用受控集成原件补强。未改变任何原用户完成条件。

## 4. 详细场景与执行结果

### S1 自然Main工作与固定工具

- 意图/要求：正常执行业务，Main看见完整工具但遵从禁用；C01/C02/C05/C07。
- 起点/输入：T3默认短/长成功旅程的用户业务请求与完整Alex Root；排除两个显式Show控制样本的Main频率统计。
- 操作计划：核受测版本与原件SHA；读取真实Main输入/回答及wire；比较canonical两Schema、顶层完整tools、Main禁用文案和请求中的误调；核父子Root/tools/Active结构一致及无messages.tools/callable_tool_schemas。
- 预期：业务回答可用；Main其它能力不丢失；两Schema原样且不折叠；自然误调如实统计；未误调不代签拒绝。
- 实际结果：独立读取并核验305份原件SHA、55次实际HTTP（全200）；46业务请求均为kimi-for-coding/High，顶层28工具，两维护Schema经过原有sanitize_tool_schemas→sanitize_moonshot_tools后的实际wire与预期一致，canonical与description原件未改；全部父子Root/tools/冻结Active逐请求相等，无messages.tools/callable_tool_schemas。早期011441的harness身份误标全部summary，按真实wire重新分类为5Main/2Noting/1辅助，未重发。
- 用户观察：13次自然Main请求两维护工具误调0；两个显式控制样本的Main不计自然频率。默认用户回答正确区分已到货饮水、20支M-041待购、A-17已核2/4与手机号后四位规则、小林签到、整体未结束，未新增排期/外发/保存。样本不足以推断普遍误调率；确定性硬拒绝另见S5。
- 证据：`validation/model-audit.json`、`audit_models.py`、`business-answers.json`，以及e2e各run的wire/原响应/305项原件清单。执行时间2026-10-24；结论：**通过**。与计划无范围偏差；核验脚本最初直接比较canonical和wire导致断言失败，已按冻结要求中的既有Provider转换纠正，产品无改。

### S2 默认短Idle完整旅程

- 意图/要求：自然使用后自动整理并压缩，保留真实用户进度；C03/C07、白板N1/P2、07§8.1。
- 起点/输入：成功默认短run的16条只读诊断+10业务原文/6Notebook prepared中间态；后续普通Main与真实30秒Idle。
- 操作计划：独立读取所有业务输入、History结果、每次维护回执、最终reason/Snapshot、压缩publication与Framework持久行、后续Main回答；比较完成/待办/价格/约束与原文；逐请求核Schema只在顶层、父子冻结前缀、资源关闭。保留9次参数拒绝及纠正顺序。
- 预期：合法错误不修改状态，最终正常独立finish、合法Snapshot；Idle次序为正常Commit→父原生durable压缩→完整Framework→Main继续；未完成事项不被误报完成。
- 实际结果：013830从明确prepared的26条历史/6Notebook开始；真实Main后原生manual30→4 removed26，再有Main进展与30秒Idle。默认Noting实际History2、Maintain15（9次invalid_argument无写入，随后6成功）及独立finish1；没有以“少量”概括9错。真实正常Commit→父native durable→Framework→第5Main承接，SQLite publication66 < Framework70，资源释放。
- 用户结果对照：原文确认饮水到货、剩20支M-041、重复姓名已核2/4、小林确认40人，Notebook保留未完成整体责任、修正场地、把已解决gap5归档（audit row虽保留missing旧状态但archived=true，不在当前人类/模型工作视图）；后续Main正确输出采购与报名剩余责任、已完成子项不再待办、活动及费用未完成。关键680元预算、型号及辨别规则可由S8原文读回；本样本摘要已含细节，不伪称制造了模型知识缺口。
- 保留历史：011441正常空Snapshot但原生insufficient/backoff，013228 would_grow/removed0，均不能算完整Idle成功；原件仍在e2e，不被本次通过覆盖。
- 证据：`validation/sequence-audit.json`、`model-audit.json`、`business-answers.json`，e2e/run-short-20261024-013830/{events.jsonl,maintain-correction-trajectory.json,snapshot-audit.json,main-result-5.json}；实际DB只读核行序。结论：**通过**，无范围偏差。

### S3 Show工作态能力分支与正常收尾

- 意图/要求：四工具真实可达，Show读本任务未提交工作态；C04/C07、07§4.5。
- 起点/输入：成功新Show run；保持原Task/Root/Schema，第一次维护成功后、尚未end_requested时仅一次原生steer。
- 操作计划：读取真实control持久行和wire，核Show完整working的entry/version对应当前成功维护且不同于父旧Snapshot；接续原任务到独立finish、原生Turn返回、Snapshot、父压缩/Framework及资源释放；比较旧失败run与新成功run，核不抹除收费/错误。
- 预期：Show不直接提交、不越权读父新Snapshot；正常提交和后续公开读取一致；默认自然Show0与能力成功分列。
- 实际结果：020652的新独立样本保留完整原Task/Root/tools，未finish时一次原生steer实际落库row81/UID1ee3267eb0484eafb8ff7f43e6a73b9e；真实Show返回view_kind=working，无snapshot审计ID，报名entry3/version13/completed与matter1/version14对应先前成功维护，而父旧Snapshot分别为version10/11。采购entry2仍in_progress且剩20支M-041，未把局部完成扩成活动完成。
- 后续完整性：Show后继续原任务，更新conversation Candidate6，独立finish accepted→原生Turn正常返回→Commit snap_adcbd201689242cbb148d63aad3352ed→父native durable→Framework，publication89 < Framework93，资源释放。S8重新打开正式/notebook后报名完成与其余待办仍正确。能力样本四工具History1/Maintain3/Show1/Finish1全部成功，默认Task自然Show0分开保留。
- 失败保留：015853真实Show/finish accepted后被旧short40分类护栏截断，无Commit；12次HTTP保留，另21次SDK本地预算拒绝不算Provider失败/收费HTTP。新样本是获准的新隔离任务，不热改/复活旧child。
- 证据：`validation/sequence-audit.json`、020652-cold-read.json、e2e/run-short-20261024-020652/{events.jsonl,child-transcript-1.json,wire-004.json,snapshot-audit.json}。结论：**通过**，显式能力分支不被冒充默认自然行为。

### S4 N46真实长前缀切换

- 意图/要求：超过原N38的长输入切换后仍可调用固定工具并正常完成；C11。
- 起点/输入：固定184条N46历史（46个工具ID），真实kimi-for-coding Main→manual联合Noting。
- 操作计划：重算合成历史与每请求冻结前缀、实际Usage、Root/tools/High、维护与finish原响应；核无提前压缩/缩历史，核8条最终Notebook与来源以及合法Framework/资源关闭。
- 预期：本模型实际长input被报告，任务无重复Schema仍正常finish/Commit；不宣称最大窗口、长Idle或旧K3单变量因果。
- 实际结果：独立将long-history-n46.json的184条逐项role/content/tool_calls/tool_call_id与冻结前缀前184条比较，全部原样；所有4个Noting请求逐请求保持相同Root/tools/186条父前缀。实际Main input140765、首次Noting143828，后续147639/151706/152234；未先缩长历史。manual父压缩虽随后发生，child已冻结原长前缀，不影响此能力样本。
- 结果质量：7HTTP200，8次Maintain成功、独立Finish，1Turn正常提交8条有效索引：matter1、action3、situation1、gap2、decision1，candidates为空；对应用户三周写作工作坊、20人、280元预算、A-17/讲义/小林场地入口及两个未知，保留“活动结束并结清费用”的完成条件，无外发/写外部记忆。合法Snapshot/Framework与资源释放已核。
- 证据：`validation/sequence-audit.json`、`model-audit.json`及e2e/run-long-20261024-012630/的wire/Usage/Snapshot原件。结论：**通过**。只证明此真实长输入代表点；不宣称最大窗口、长Idle或旧K3单变量因果。

### S5 权限拒绝、恢复与原生边界

- 意图/要求：定义不授予权限，所有正式路径硬拒绝后能继续合法操作；C04/C05/C10。
- 起点/输入：当前产品对应的受控正式Loop/dispatch/registry/invoke/同步并发、绑定工作Store与真实DB机制材料；无真实外部服务调用。
- 操作计划：核机制原件及源码SHA匹配，检查拒绝error.code/message/next_action、无写入、合法混批仍执行、finish混批整批拒绝、普通child不获权、间接调用与参数自称不获权；核Noting关/非eligible的原生行为、local开关不改prefix、旧pin在freeze前补canonical及source明示、失败资源释放。必要时仅小范围正式入口反证。
- 预期：scope_denied形状完整并给纠正动作；正常能力不受新增权限错误阻断；无绕过/跨域信息泄露/伪提交；已有恢复接口能力保持，不实际恢复生产旧任务。
- 独立实际操作：在S8新副本真实SessionDB绑定的冷态AIAgent读宿主（沿原生noting_capability相同无init方式，无SDK/client/Turn）调用正式_invoke_tool，Main notebook_maintain/finish_noting各覆盖pre_tool_block_checked=false/true，4次均完整success=false/error.scope_denied/message/next_action，参数自称Noting无效，Notebook不变；随后合法History原文仍成功。
- 同版本机制复用：重算permission-errors/version.json的6源码及4日志SHA全匹配当前；亲读正式Loop/同步并发/invoke/包装解包前拒绝、合法混批/错误后Show、finish混批零效果、end_requested后写拒绝且重复finish保首次结果、普通child不获维护权、local不改root/tools、global关闭保History、stale pin正常恢复的断言与有效执行原件（47权限、9原dispatch；不相加宣传覆盖）。32请求与20恢复证据对应当前源码，跨协议/多模态/续Turn来自受控SDK，不伪称每分支在线模型。Idle43机制证据覆盖异常不压缩、旧任务复用、owner/fence/失败资源边界；本地真实失败原件亦正常释放。
- 证据：`validation/boundaries-today-audit.json`、audit_boundaries.py，permission-errors/{version.json,final-permissions.log,targeted-1.log}、prompt/{receipt.json,final-requests-tests.log,final-recovery-tests.log}、tests/secretary/test_fixed_noting_permissions.py及Idle两文件。结论：**通过**。不执行生产旧任务恢复，不以Main自然0误调替代拒绝证明。

### S6 今日修补的用户结果

- 意图/要求：今日已审后端599d114与前端589df02同批交付；C08/C10。
- 起点/输入：按该提交变更及冻结06/07定位的真实入口或受控adapter/Web专项材料。
- 操作计划：先列完整今日修补覆盖，再核当前版本未回退这些变更；检查完整正式正文及时发送、Redirect半正文同通知不重复、Thinking不误发送，Framework及冻结分类下的非触发式deferred上下文注入不借最近adapter外发；合法后台触发Turn/InstantReminder沿既有契约；核标题正式写入/失败保留、提交恢复与context/usage/时间对应正式数据。UI呈现若必须操作，仅自建隐藏IAB；无法合规则标缺口。
- 预期：所需变化的用户可观察结果与规格一致；不新增生产消息/历史恢复，不以adapter模拟当真实微信发送；APK不自动安装。
- 今日完整闭包：599d114包含微信正式正文/Redirect、非触发Framework渠道边界、Idle先提交后压缩、Kimi输出字段、K3辅助标题和压缩时间继承；589df02包含WebContext保值/迟到保护和APK竖屏。已独立核当前源码/测试与对应原件SHA，Core1ea的后继仅4文档，UI仍589df02。
- 微信/Framework：复用真实SDK流→原生Turn→consumer→实际adapter模拟发送机制；完整消息及时发送、Redirect半正文并同通知/FIFO/不重复，Thinking不外发；仅按冻结分类的非触发式Framework/deferred上下文注入不借最近adapter，合法触发Turn/InstantReminder契约保持。亲读关键完整序列与assert；未做真实微信发送。
- Kimi可信URL：正式https精确host/path/443及无userinfo/query/fragment才用max_completion_tokens；其它Provider/代理/Anthropic/Responses保原字段；ephemeral/显式/profile、override/extra_body优先级与copy-on-write及400/402原重试契约由同源码SDK wire原件支持。不是把字段修补说成长N38动态工具400根因证明。
- K3标题：原生llm.oneshot→session.title/info/真实SessionDB，k3/k3-256k/provider前缀省略不兼容temperature，失败保旧名，自动title持久化并通知；5原生标题/4温度回归原件有效。时间：in-place/covered/rotation及full/cards/details/resume按UID继承原时间，未知UID不借同文时间；104相关后端原件与源码SHA有效，不恢复旧生产47行。
- WebContext：589df02正式controller50项原件/源码SHA匹配；context unavailable保旧有效值、显式invalidated、迟到owner/lifecycle/revision及先观察字段保护均已审，不以build代签。APK：0.1.4/1004真实签名release32048481B，SHA fdc72109…ee08，portrait、非debug、同证书、439内置文件；独立重算APK及全部dirty-source SHA与589df02一致。无安装用户手机或新视觉/长期后台验收；本轮为既有验包复用，不将其扩大为手机实测。
- 证据：`validation/boundaries-today-audit.json`、frontend-context-receipt.json与test.log、.hermes-dev/weixin-message-source.sha256及final-integrated.log、kimi-output-wire-20261023/、apk-title-20261023/、timeline-timestamps-20261023/receipt.json、android-apk-20261023/package-verification-0.1.4.json。结论：**通过**；无需新增图形操作，未碰任何显示状态。

### S7 生产联合部署与数据保护

- 意图/要求：真正上线并保护用户现状；C08/C10、部署SOP。
- 起点/输入：本地场景全部通过后root独占部署；固定Core后继（产品同1ea）和UI589df02/439资产，正式新表集preflight/apply前后receipt。
- 操作计划：接收root实际部署版本及受限收据后，只读复核Web/Gateway运行版本/进程启动时刻与代码绑定、API/WS、微信connected；对照三库消息/排期/绑定及Notebook四表的保护指纹、config/SOUL/auth和生产模型/阈值、静态Secretary439与Dashboard集合SHA；保护服务与认证入口保持，不发模型或微信消息。
- 预期：目标实际运行且双SPA/单后端健康、微信连接正常；全部保护对象保持，未带入隔离阈值/Persona/合成DB；可恢复点保留。生产尚未部署不是最终PASS，且不阻止本地放行流程。
- 实际部署与顺序：root按本地放行后执行正式stage/apply，私有receipt phase=verified，Core0e14d4e（产品同1ea）、UI589df02/439文件。两服务2026-10-24 02:37:53 CST启动，Web/Gateway实际版本均精确0e14d4e；服务active、NRestarts=0，Gateway running、active_agents0、active_work空、微信connected。验收者仅随后只读核验，没有操作部署。
- 实际接口：回环Secretary `/` 与Dashboard `/dashboard/`均200，页面token仅在内存；`/api/profiles`及`/dashboard/api/profiles`已认证200。两WS `/api/ws`及`/dashboard/api/ws`实际连接后只调用session.active_list，均成功且running0。公网匿名HTML302到auth.edgarzhong.fyi，匿名JSON API401，访问保护保持。没有图形/登录后UI或手机操作，不由接口成功扩成视觉PASS。
- 数据保护独立核：完整receipt before/after三库各10表严格相等，覆盖messages、Schedule registry/pending、session bindings/aliases、Heartbeat及Notebook item/snapshots/pointer/local_state；生产只读重新计算现时全部行/列SHA，再与before逐项相等。Alex messages11099／排期41／pending37／bindings77，host messages2、study0；Notebook四表全部保持。未改旧47行或恢复旧任务。
- 配置与资产：24项配置指纹（23个路径状态+Profile registry）包含config/SOUL/.env/auth/nowledge/profile/AGENTS及微信账户，receipt前后及现时严格一致；微信绑定摘要相等，未带入测试模型/Idle阈值。Secretary当前完整439文件集合/SHA等于UI589df02正式manifest；Dashboard67文件集合/SHA与部署前相等。两SPA共享machine token/API/WS，未增加第二后端。
- 可恢复性：三份真实SQLite备份独立核SHA/字节数、integrity_check=ok、foreign_key_check0，均0600；17份实际存在的配置备份SHA逐份相等且受限。恢复说明与旧静态保留，未自动回滚DB。部署root receipt与独立核验期间均无生产模型测试/微信消息。
- 证据：`validation/production-receipt-audit.json`、production-independent-readonly.json、production-backup-auth-readonly.json及三个只读脚本；原私有收据 `.hermes-dev/noting-fixed-tools-20261024/release/production-receipt.json`，云原件 `/home/ubuntu/.local/state/hermes-secretary/release-20261024/20261024-fixed-noting-0e14d4e/receipt.json`，SHA119d1a8a20b060e58b663822bca69403604ba957bff909b58136698c29719a91。执行2026-10-24部署后；结论：**通过**，与计划无范围偏差。

### S8 独立冷读与后续可用性

- 意图/要求：用户实际能继续使用持久结果而非仅有测试通过；C06/C07、白板P6。
- 起点/输入：S2/S3成功隔离DB原件，合法SQLite backup到仓库外新0700根；不启动Gateway/扫描/模型。
- 操作计划：通过原生CLI命令handler正式/notebook读取，/noting无参Usage及现有可读状态入口，再执行off/on在新副本核参与与Scheduler独立；正式History Search/Read查业务关键原文和UID；比较Notebook事实、用户进度与后续真实Main回答，再关闭/重新打开读回确认持久化；只读RPC可用时补session/context/history投影一致性。
- 预期：快照/来源/任务进度准确、可操作ID保留；完成与待办清楚；读入口不创建Turn/改历史，开关只改副本本Conversation参与，不改Scheduler；重复读取一致。
- 独立实际旅程：SQLite只读backup成功默认013830与Show020652到仓库外 `/Users/edgar/.local/state/hermes-validation-fixed-tools-20261024-final/` 两个新0700根；只复制测试DB及无凭据测试config，不复制.env/SOUL，不启动模型、Gateway、timer或扫描。真实原生notebook_command返回可读完整Notebook，noting_command无参返回Usage，原生冷能力预热后off/on均成功，local off仍能读Snapshot，Scheduler及全部消息/Session/Notebook内容/快照表SHA不变；仅预期参与偏好表updated_at变化。
- 后续可用性：正式History Search分别用M-041、A-17及记号笔取得规范UID再Read；还直接沿Notebook原source UID读取原始采购单，完整680元、12箱W-2406、20支M-041及手机号后四位/不可同名删除均在。默认结果正确保留2/4待办，Show后报名全部完成而采购与整体仍未完；关闭DB后重新打开/notebook逐字一致，源T3 DB文件SHA前后相同。
- 观察/修正：最初预算检索词“680”按FTS词项无命中，不等于预算不存在；沿原锚点完整回读，业务词检索正常。最初保护指纹误含参与偏好updated_at，定位后将该预期可写表单列，不放宽消息/排期/Notebook四表保护；未改产品。最初内部冷能力cache试验仅在第一失败副本，最终完整旅程全部使用原生prime_cold_main_capability，失败副本保留审计，不当成功样本。
- 证据：`validation/cold_read.py`、cold-read-summary.json、run-short-20261024-013830-cold-read.json与020652-cold-read.json；真实业务回答比对见business-answers.json。结论：**通过**。公开读取采取原生CLI共享handler及原生History facade；没有另启完整CLI交互/WS服务，不宣称额外UI验收。

## 5. 问题、修复与复验

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| 无新增产品缺陷 | S1–S8完整执行，先本地放行再实际部署与只读终验 | 真实模型、独立CLI/History/拒绝读回与生产版本/保护均达到判据 | 全部适用场景通过；最终门禁关闭 | 产品Core1ea／生产0e14d4e／UI589df02 | model/sequence/boundaries/cold-read/production六组独立证据 |
| 历史不完整/失败保留 | 011441父压缩insufficient；013228 would_grow；015853旧内部护栏截断收尾 | 原8/4/12HTTP与失败状态保留，不算完整成功；013830与020652提供新的完整证据 | 历史事实不被新成功抹除；无待整改产品缺口 | 产品相同；root已批准修内部测试护栏 | S2/S3核真实Commit、SQLite行序、公开冷读 |
| 验收脚本修正（非产品缺陷） | 初始canonical直接比wire；早期harness身份标签；FTS数字词；参与偏好时间指纹 | 按既有Provider转换/真实wire/规范锚点/预期local写入纠正，未改产品和原始判据 | 已关闭，原失败副本保留，不作为成功样本 | 不适用 | 最终各独立脚本成功，原件只读 |

## 6. 验收结论与推荐复核

**最终Validation：PASS，门禁关闭。** G1–G8对应S1–S8全部适用场景通过；没有失败、阻塞、未执行或新增产品整改项。本地场景先独立通过并放行生产，root随后部署0e14d4e/589df02，S7再独立确认实际Web/Gateway/双SPA/API/两WS、微信连接、三库十表/配置/绑定与静态资产保护及备份可恢复性。

已证明：原两Schema/description固定完整顶层、Main可信拒绝且Noting仅四工具、无任务Schema重复、父子冻结前缀一致；默认短Idle及显式Show能力分支正常finish/Commit/压缩/Framework；N46真实长输入140765→143828切换有效；独立/notebook和History读回/重开后用户状态正确；今日Kimi wire/K3标题/时间继承/WebContext/APKportrait闭包与实际联合发布成立。

证据边界：自然Main13请求误调0仅为样本观察；默认Show自然0与显式能力分支分列。默认短9次参数拒绝与旧失败/费用计数保留。并发/错误时序、跨协议/多模态续Turn、微信adapter及标题采用当前源码/日志SHA匹配的受控集成原件；不冒称每个分支均在线模型或真实微信发送。未安装手机、未做新视觉/手机长期表现验收，也没有生产模型/微信测试发送；这些不属本轮新增完成条件，不把接口通过扩大为UI视觉结论。

推荐复核路径：

1. 默认完整旅程：e2e/run-short-20261024-013830/main-result-5.json，观察饮水已到货、报名仅2/4、M-041待购与整体未结束；publication66→Framework70和独立CLI冷读对应一致。
2. Show能力：020652/wire-004.json及child-transcript-1.json，working entry3/version13已完成、matter/version14；随后正常snap_adcbd…与89→93，冷读仍保留采购/整体待办。
3. 长前缀：long012630实际wire/Usage、sequence-audit.json，184条原文完整、140765→143828输入，8维护/独立finish及8索引；不外推最大窗口。
4. 用户可读产物：validation/*-cold-read.json包含/notebook完整结果及History规范锚点原文；重新打开一致。
5. 线上：production-independent-readonly.json与production-receipt-audit.json，对照0e14d4e实际运行、439/67静态和三库十表前后/现时相等；production-backup-auth-readonly.json确认备份及匿名保护。完整证据根 `.hermes-dev/noting-fixed-tools-20261024/validation/`；私人原件仅保存在受限ignored目录。

验收者没有提交/push、部署、生产写入或显示变化；只读S7未触发模型或消息。最终目标结束判断由主会话负责。
