# Validation：20261021-conversation-heartbeat

## 1. 结果概览

### 最终独立Validation结论（2026-10-21 18:24，ed94619）

**整轮Validation通过，R2-U01–U18全部通过，门禁关闭。** 最终后端 `ed94619da81547bcb9e27aab60b608b2310e6890`、固定前端 `0b8843fb87bf0ba109f7b744f4ae96faf09df597` 已由三份真实发布/只读收据补齐。U01–U16新版前置全轮复验及实际WS成功note、false原生英文/中文逐字保持结论继续有效；U17/U18后置18:24独立补核通过。Web/Gateway同ed、active/running、NRestarts0、微信connected；固定439文件与双SPA关键JS/CSS匹配。host/alex/study的18组受保护表（含Heartbeat）前后全行SHA一致，配置/绑定保持。Alex原ref/stored、7200/空prompt/active/count0/revision1、created/last_fired/next_due及整份正式control保持，set_called=false，下一到期仍为2026-10-21 19:58:09北京时间，未提前触发。

本验收新增外部/模型请求0，无生产连接/浏览器/桌面/显示操作；六个自建服务进程均退出，临时定义清除。最终收据只读补验未重跑测试或追加模型。无新增产品缺陷，HB-UAT-01与后置项均关闭；初审错误note、漏核、失败与撤回完整保留为历史。未新增登录后在线UI、手机/微信触达或长期运行验收声明。报告和审计入口见第2/4/6节；目标最终完成由主会话结合Verification决定。

### R2前置验收历史（2026-10-21 18:19，ed94619；后置已由上段关闭）

**新版前置Validation通过：R2-U01–U16全轮适用场景通过；HB-UAT-01在实际用户入口关闭。最终整轮门禁仍待R2-U17/U18新版发布收据，不冒称已完成。** 计划已由主会话完整过目后执行。本验收18:15:36–18:18:44在3个自建临时Home、6个原生serve进程上实际执行HTTP/WS管理旅程；完整成功output准确说明Conversation保存、切换/关页保持、后端运行前提和重启持久。全局false英文与中文Profile的note与各自原生catalog逐字相同，中文确有原生翻译；空/空白prompt仍拒绝。两小时管理、双向会话隔离、close/断连与新进程状态恢复、pause/clear/resume、new/fork均得到真实入口结果。外部HTTP与模型请求均0，6进程全部停止，自建定义清除，未动用户/生产/显示。

其它全轮要求依据原始匹配证据独立复核：旧serve自然tick与148.58秒跨两due停重启、paused/cleared跨due恢复、4个既有真实K3/High样本、压缩/旧Gateway generation/目标Profile/失败/并发，以及固定前端与配套failed_turn；f32→ed仅note helper/导出/CLI调用及2分支测试，原路径未变。31运行/测试文件与ed一致、固定前端439文件和归档SHA一致，适用边界见第2/4节。无新产品缺陷；不复跑大套或追加付费样本。旧S01失败与撤回是初审历史，保留原事实，不代表新版当前结论。

### 第二次独立全轮复验计划历史（2026-10-21，执行前尚未执行）

验收者 `heartbeat_validation_r2`，新独立 Sol／High，不再派生。完整读 autonomous-run、real-user-acceptance 及六节模板；依据冻结 `51300c06001e14af6bb91fd2c0d53b8c0b3fe9fa` 的 Snapshot Index HB01–10、07 §0／3／6.3／8.15、06 §0.7–0.8／Heartbeat／failed_turn呈现契约、部署SOP §0／8推导以下全轮场景。计划不以旧场景或实现说明作为判定依据。待验后端 `ed94619da81547bcb9e27aab60b608b2310e6890`；固定前端 `0b8843fb87bf0ba109f7b744f4ae96faf09df597`。前置新Verification已通过，36判据中生产五项留后置。

本次目标同时覆盖准确的用户输出、持久管理与恢复、原生关闭分支、合法身份与Profile、失败及并发恢复、模型和固定前端，以及最终发布与Alex原排期保护。修复仅影响成功note仍须全轮覆盖，不能只重测旧缺陷。全部新场景当前**未执行**，门禁未关闭。计划交主会话过目后执行；生产最终收据按既定先验后发布顺序追加，不把尚未补发版变成前置循环。

旧报告完整副本：`.hermes-dev/conversation-heartbeat-validation-r2-20261021/validation-before-r2.md`。以下各节旧版文字保留原时点，包括S01失败与前置通过撤回，不代表新版结论。

### 原报告历史（保留）

验收者：独立 Validation 子 Agent，Sol／High，无实现上下文、未再派生。时间：2026-10-21 17:39–17:46（Asia/Shanghai），随后只读审计与报告。依据：同目录 `snapshot-index.md`、`baseline.txt`；冻结 `51300c06001e14af6bb91fd2c0d53b8c0b3fe9fa` 的07 §0、§3、§6.3、§8.15、06 §0.7–0.8及Heartbeat／failed_turn呈现合同、部署SOP §0、§8、HB01–HB10。实际后端 `f32d70f703fd8995f6652ca71ff72ef0d56d535e`，固定前端 `0b8843fb87bf0ba109f7b744f4ae96faf09df597`。

**初审历史更正：当时Validation不通过，S01存在范围内用户输出缺陷（HB-GAP-02／HB-UAT-01），此前“前置用户验收通过”结论撤回。** 主会话在初始f32生产设置RPC中发现成功note仍称“lives only while this Hermes process runs”；复核本次原始本地WS记录同样已包含该文字。我初审核了状态字段而漏查完整成功输出，不能以实际持久功能正确覆盖与持久语义相反的用户提示。S02–S17已核实的f32机制、用户结果及有效证据保留；不据此代签修复提交 `ed94619da81547bcb9e27aab60b608b2310e6890`。新版本须由全新独立Validation重新覆盖全轮并复验该输出，最终门禁保持未通过。

初审历史（保留，已被上述更正替代）：17:39–17:46验收后曾判“S01–S17全部通过，S18后置待收据，整轮最终门禁尚未关闭”。18场景完整计划在执行前已按六节模板落盘，主会话明确完整过目并同意执行；没有缩减场景或改变用户完成条件。核心新增证据为真实HTTP／WebSocket入口、原生serve进程及自动宿主自然到期的两条真实K3链路，未使用handle_request、直接scan或Heartbeat helper替代服务旅程。

结果：同Profile三个Conversation的设置／替换／暂停／清除独立；A正式runtime close且WS断开后恢复自身Main；服务实际停止148.58秒、跨过两个60秒周期后新进程无WS恢复，只合并执行一次；paused与cleared跨重启不复活；resume按恢复时刻重新锚定。两次真实 `k3-256k`／High请求均HTTP 200，以HEARTBEAT_OVER收尾，无重试。后置不代表未部署已通过，也不把该顺序变成前置循环。

## 2. 环境与准备

### R2最终后置证据

最终只读输入E中的 `deployment-receipt.json`、`post-release-readonly.json`、`alex-heartbeat-final-readback.json`；初始`*-initial.json`及`alex-heartbeat-receipt.json`保持。独立读取三收据及实际生成脚本 `deploy.py`、`verify_release.py`、`verify_alex.py`，确认生产版本来自health和Gateway control的code_sha、读回是session.resume/control.read而无set、保护表/配置和静态文件为完整内容SHA比较。自有`final_receipt_audit.py`实际逐字段比较，结果 `final-receipt-audit.json`（18:24:27+08:00）。未执行这些生产脚本或连接服务器。

部署恢复点为 `/home/ubuntu/.local/state/hermes-secretary/conversation-heartbeat-20261021/deploy-20261021T182117`；旧静态目录为 `/home/ubuntu/.local/share/hermes-secretary/static/secretary.before-heartbeat-20261021T182117`。脚本在无Web/Gateway活动、无writer lease/Noting后备份三库和配置/SOUL，核PM Python3.14.8/lock及依赖diff为空，停唯一服务再更新、重启后核版本/保护状态，无自动回盖。上述是收据与脚本支持的后置事实，不冒称本验收亲自在生产执行。

### R2实际环境与证据

- 新证据根`.hermes-dev/conversation-heartbeat-validation-r2-20261021/`：`journey.py`、`service_launcher.py`、`reverse.py`、`rpc-transcript.jsonl`（253原始帧）、`http-transcript.jsonl`、`lifecycle.jsonl`、`journey-state.json`、`evidence-audit.json`、`reviewed-note-only.diff`、`service.log`、初始/续接/反向旅程日志。新实际平台darwin、官方PM Python3.14.7，未安装依赖、未跑测试套。
- True/en临时Home `/var/folders/t3/wq4xbhq16h52sj254q8sk7s80000gn/T/heartbeat-validation-r2-iq0d43x2`，PIDs87693/87782/88628；false/en Home末尾`heartbeat-validation-r2-b65uowl2`，PIDs87824/87928；false/zh末尾`heartbeat-validation-r2-_00ozela`，PID87989。每次Home均在启动前实际枚举唯一default及其managed Home，cwd在临时workspace、repo外；启动环境去除继承HERMES_*和API_KEY/AUTH_TOKEN/ACCESS_TOKEN后显式绑定自建Home/runtime。HTTP探针和模型guard只观察/拒绝外部请求，不伪造产品成功返回。
- 六进程均已正常终止并逐PID核不存在；所有Secretary自建定义为cleared/fire_count0，native亦正式clear后control.read为null。zero-budget外部attempt文件未生成；实际0新外部/模型请求。新增证据不含机器token帧或用户凭据，未访问用户库/生产/显示。原native第一次断言漏算两空格显示缩进，已仅续验原生分支，首次日志保留；中文fallback的早期检索假设也被真实中文输出纠正，见第5节。
- 独立审计31文件working SHA与ed完全一致；读完整f32→ed四文件diff确认机制无变化。原S两wire的SHA/HTTP200、原始RPC/HTTP/lifecycle、载体/回复及root/tools一致已程序核；原E两真实样本源码hash均匹配f32、note以外路径对ed仍适用。F归档SHA为89e05ae6de4ea4d716f31f9202a58069e1e2ec27738bb7bd5808d47da1eb3458，439文件逐个匹配。未将受控transport故障/并发证据冒称真实模型/生产操作。

### R2原计划环境、授权与证据复用（保留执行前预期）

- 写权限仅本报告、ignored `.hermes-dev/conversation-heartbeat-validation-r2-20261021/`和自建临时Home；产品代码只读。无浏览器、桌面、可见页、焦点、open或open_in_codex操作。不接触用户Home、生产库、Alex设置或其它已有服务。
- 正式入口采用本机 `start_server(..., host=127.0.0.1, open_browser=False, headless=True, isolated=True)` 的原生serve lifespan、合法HTTP与WS RPC。Mac PM Python现有`.venv`，不装依赖。cwd在repo外自建workspace。启动前清除全部继承HERMES_*，显式绑定临时Home/runtime；**先实际枚举profiles_to_serve及managed_profile_homes，确认只有自建Home后才启动**。原生全局true／false用两个独立临时Home，互不借用配置。
- 使用虚构seed消息公开创建Conversation，不复制用户库。新旅程一律2h间隔，立即管理和清理，在到期前停止；配置辅助标题、memory、MCP和自动维护关闭。实际模型HTTP请求预算0：观察httpx请求并在任何非回环请求发送前拒绝，记录尝试计数；不替换模型成功返回或产品宿主。预期attempt=0，任何意外尝试会停止旅程并报告，不付费补样本。
- 新实际旅程重点为完整成功输出、空／空白／非空prompt、/hb别名、两Conversation交错、local Noting关闭、status/pause/resume/clear、close／断连及新进程读回、新身份，以及global=false原生非空校验和本地化note逐字保持。只读诊断补充用户入口结果，不以数据库字段代替可理解的输出。
- 复用源E=`.hermes-dev/conversation-heartbeat-20261021/`的evidence-index及receipt_fix、最终日志；源S=`.hermes-dev/conversation-heartbeat-validation-20261021/`的原始HTTP／RPC／wire／lifecycle／history／service-summary；源F为固定前端包、manifest、构建测试及既有截图；源N为独立Verification负例。逐项核原始序列、版本、真实依赖及最终用户状态；读f32→ed精确diff核成功note helper／导出／CLI调用之外机制未变，并保存运行文件hash复用审计。S的自然tick／三真实进程停重启和两真实K3请求、E的两匹配样本可支持未变路径；不能拿旧成功note为新版输出代签。并发／故障用匹配受控集成证据，不冒称真实模型或生产故障注入。
- 新部署前仅只读初始三收据核已发生事实；收到主会话新版最终receipt后核精确后端ed、前端包439文件、双SPA、服务、备份、保护指纹、无新增测试模型请求、Alex原定义**全字段及锚点**未变。Alex既有ref `conv_8dc89e12cc9b42b5a77986f4d9b02cec`、stored `20261011_223115_59ad08`、7200秒／空prompt／active／count0、next_due `1792583889.5657868`（19:58:09北京时间）；绝不再every或提前触发。若补验已跨自然到期，按正式自然执行证据解释合法变化，不把count0当永久要求。
- 差异边界：本地Mac不代签首尔Linux上线；无新浏览器视觉和手机长期验收。固定产物无变化的已确认视觉可复用；匿名302／HTTP200不推为在线UI通过。新UI呈现要求不存在时不额外制造浏览器验收。

### 原报告历史（保留）

- 本机macOS／darwin，项目官方PM Python 3.14.7，既有`.venv`，未安装依赖、未复跑大型测试。实际入口是 `hermes_cli.web_server.start_server(host='127.0.0.1', port=54411, open_browser=False, headless=True, isolated=True, start_mcp_discovery_after_bind=False)`，完整原生lifespan自动启动SchedulerHost。服务启动器只观察httpx实际wire并实施跨重启两请求预算，没有替换产品入口、宿主、模型返回或执行器。
- 自建Home：`/var/folders/t3/wq4xbhq16h52sj254q8sk7s80000gn/T/hermes-heartbeat-validation-20261021-l9j18pzv`，cwd为其`workspace/`，在Git root之外。启动前清除继承的全部`HERMES_*`，显式设置此Home／runtime；其下无命名Profile注册。补充只读复现 `profiles_to_serve(multiplex=True)`及`managed_profile_homes()`，唯一Home为此临时目录（`/private/var`为macOS规范路径），未枚举Alex／study，详`profile-isolation.json`。枚举复核发生在服务完成后；隔离启动环境及空Profile注册从准备时即存在。
- 自建配置：全局noting开启、idle关闭、scheduler关闭、compression关闭；原生Kimi Coding `/v1` Chat、准确`k3-256k`、262144窗口、High，辅助标题／记忆／MCP关闭。Key仅继承已有进程环境，未读用户凭据文件、未写入配置／argv／证据。结束时按Key字节检查整个证据目录及临时Home未命中；三服务PID均已退出。此为安全性检查结果，不公开Key。
- 数据从公开`session.create`的合法seed messages建立，明确虚构且无待办、排期、承诺、外部联系或工具任务；未复制用户数据。A=`20261021_173957_b157da`，B=`20261021_173958_3a5b7d`，C=`20261021_173958_f1db95`，fork=`20261021_174034_6b80a1`。持久source均tui；A通过公开`/noting off`设本地关闭，诊断读回`noting_enabled=0`。Profile和DB诊断为用户入口结果的补证。
- 本轮自有证据统一位于 `.hermes-dev/conversation-heartbeat-validation-20261021/`：`journey.py`、`service_launcher.py`、`audit.py`、`rpc-transcript.jsonl`、`http-transcript.jsonl`、`lifecycle.jsonl`、`journey-state.json`、`service-summary.json`、`profile-isolation.json`、`service.log`、两份`service-wire-*.json`、`model-requests.jsonl`、`disconnected-close-history.json`、`process-restart-history.json`、`evidence-audit.json`。31个本轮Python源／测试文件逐字哈希与f32一致，前端归档SHA与固定manifest一致。
- 复用开发证据 `.hermes-dev/conversation-heartbeat-20261021/`：`evidence-index.json`列16文件154项有效定向测试；`tests-alias-final.log`为最终15个Conversation宿主场景，`tests-storage-final.log`为最终23项store／开关场景；`tests-final-runtime.log`、`tests-facade-final.log`、`tests-edge.log`及原版保留失败日志只按各自版本和适用路径引用，不累加重跑次数。真实Messaging／额外prompt样本为同目录`real-summary.json`、两份`real-wire-*.json`，源码哈希与f32运行文件匹配；不重发已有请求。配套failed_turn证据为 `.hermes-dev/failed-turn-20261021/`。
- 固定前端439文件、176构建输入、917通过／1skip、TypeScript和生产build复用 `/Users/edgar/code/hermes-secretary-web/node_modules/.cache/hs-timeline-check/` 的固定发布目录和包；包SHA `89e05ae6de4ea4d716f31f9202a58069e1e2ec27738bb7bd5808d47da1eb3458`，本验收重新计算匹配。只读既有截图，未操作浏览器、桌面、显示／焦点或open入口，未触用户现有页。
- 差异与影响：本地Mac隔离服务不能代签首尔Linux实际部署、双SPA、认证及Alex正式设置，必须由S18收据补验。视觉复用同固定版本，不声称本轮新在线UI、手机／蜂窝、微信触达或长期运行验收。
- 后置已收到主会话执行的初始f32收据：开发证据目录的 `deployment-receipt-initial.json`、`post-release-readonly-initial.json`、`alex-heartbeat-receipt.json`。本次更正仅只读这些本地收据，未连接生产；只核其记录的初始发布／设置事实，不将其当作ed94619最终运行或新版本独立验收证据。

## 3. 用户目标与场景覆盖

### R2全轮覆盖矩阵（执行前）

| 目标编号及冻结依据 | 完整场景编号 | 场景类型与起点 | 数据/顺序选择依据 | 当前执行结果 |
|---|---|---|---|---|
| R2-G01 HB01/04/05，07 §8.15 | R2-U01 | 主流程，新Conversation设置→status→替换→读回 | 空、空白、extra及/hb；输出必须准确表达持久性与后端前提 | 通过；新实际入口与匹配原始证据见第4节 |
| R2-G02 HB04 | R2-U02 | 衔接，两Conversation交错管理→重读对方 | owner唯一，A操作不能影响B | 通过；新实际入口与匹配原始证据见第4节 |
| R2-G03 HB01，07 §6.3/8.15 | R2-U03 | 模式，全局开、本地关、Scheduler关 | 本地Noting与独立Scheduler不决定Heartbeat资格或权限 | 通过；新实际入口与匹配原始证据见第4节 |
| R2-G04 HB03/05 | R2-U04 | 完整旅程，设置→close→唯一WS断连→自然到期→重读 | 无页面/runtime恢复自身Main | 通过；新实际入口与匹配原始证据见第4节 |
| R2-G05 HB05 | R2-U05 | 恢复，停止进程跨多个due→新进程→结果 | active保留、只合并一次；TTL回收合法分支 | 通过；新实际入口与匹配原始证据见第4节 |
| R2-G06 HB04/05/06 | R2-U06 | 返回修改，pause/clear→close→重启→resume→读回 | paused/cleared不复活，resume重新计时 | 通过；新实际入口与匹配原始证据见第4节 |
| R2-G07 HB04/06，07 §0 | R2-U07 | 压缩，旧/新物理入口交错控制→tip执行 | 同ref共享定义；claim后tip变化退款 | 通过；新实际入口与匹配原始证据见第4节 |
| R2-G08 HB04 | R2-U08 | 新身份，new/reset/fork→读回父/子 | 新owner默认无定义，父保留 | 通过；新实际入口与匹配原始证据见第4节 |
| R2-G09 HB03/05/06 | R2-U09 | 跨入口，Gateway switch/reset→旧owner后台恢复 | 旧generation仅渠道route失效，UI执行、不重绑 | 通过；新实际入口与匹配原始证据见第4节 |
| R2-G10 HB01/04/06 | R2-U10 | 隔离，双Profile同物理ID、相反配置 | 目标DB/模型/时区，不能借启动Profile | 通过；新实际入口与匹配原始证据见第4节 |
| R2-G11 HB05/06 | R2-U11 | 失败恢复，busy/queued/lease拒绝/缺目标/异常→条件恢复 | 用户优先、真实失败、due保留、无误投、最终可用 | 通过；新实际入口与匹配原始证据见第4节 |
| R2-G12 HB06 | R2-U12 | 并发，双连接claim→pause/replace/resume/clear与晚refund | 同tick一次，旧worker不能覆盖新状态 | 通过；新实际入口与匹配原始证据见第4节 |
| R2-G13 HB01/10 | R2-U13 | 原生关闭，空prompt拒绝→有效设置→本地化note→管理 | false模板/校验/执行/数据原样，note逐字原生 | 通过；新实际入口与匹配原始证据见第4节 |
| R2-G14 HB02/03，07 §3/8.15 | R2-U14 | 模型结果，空/extra正式宿主请求→持久/重放 | 精确英文、单时间、UI platform、目标模型/High、root/tools不变 | 通过；新实际入口与匹配原始证据见第4节 |
| R2-G15 HB07，06 Heartbeat | R2-U15 | 呈现，固定包浅/暗移动/桌面折叠展开与反例 | 原role/UID保持；仅完整user wrapper分类 | 通过；新实际入口与匹配原始证据见第4节 |
| R2-G16 HB07，06 failed_turn | R2-U16 | 配套，明确取消诊断行/partial/同措辞模型回复/slash | 仅真实标记行、无terminal合成、无历史猜迁移 | 通过；新实际入口与匹配原始证据见第4节 |
| R2-G17 HB07，06 §0.7–0.8，SOP §0/8 | R2-U17 | 后置发布，新两前置门禁→补发版→版本/双SPA/保护对账 | ed与固定0b8843f、单backend、恢复点，不带Android dirty | 通过，最终ed收据独立补核；见U17/U18与final-receipt-audit.json |
| R2-G18 HB08，SOP §8 | R2-U18 | 后置只读，初始正式set→补发版→同定义读回 | Alex实际pin与7200/空prompt，全部字段/锚点保持、不提前测试 | 通过，最终ed收据独立补核；见U17/U18与final-receipt-audit.json |

覆盖为主流程、合法模式、输入等价类、不同入口、重复修改、历史状态、取消与恢复、跨功能与并发。跨due依S真实等待证据，确定性故障依E/N受控序列，真实接口依S/E匹配样本；每项会分别标观察层次及适用边界。未穷举所有组合，但没有因为修补仅note而缩减全轮目标；所有18项均需通过或有依据不适用，生产两项可在前置接收后补证。

### 原报告历史（保留）

| 目标编号及冻结依据 | 完整场景编号 | 场景类型与起点 | 数据/顺序选择依据 | 当前执行结果 |
|---|---|---|---|---|
| G01 HB01、04；07 §8.15 | S01 | 主流程：新Conversation设置、status、替换 | 空／空白／有值prompt；每owner最多一条 | **失败，更正初审漏查；成功note否认持久性，HB-UAT-01** |
| G02 HB04–05 | S02 | 衔接：A、B不同设置后切换 | 同Profile双Conversation交错管理 | 通过，实际WS及最终B全字段保持 |
| G03 HB01；07 §6.3、§8.15 | S03 | 合法变体：本地Noting关闭、Scheduler关闭 | 全局开关是唯一资格 | 通过，实际服务／wire与诊断 |
| G04 HB03、05 | S04 | 整体旅程：断开唯一WS、无页面等待自然tick | 自动宿主到自身Main，重连／历史读回 | 通过，第一次自然真实模型结果 |
| G05 HB05 | S05 | 恢复：正式runtime close／实际回收 | 内存释放，持久active仍存在 | 通过，实际close后自然冷恢复；TTL另复用 |
| G06 HB05 | S06 | 恢复：完整进程停止跨due、重启 | 无连接恢复，missed ticks合并 | 通过，实际停机148.58秒后只执行一次 |
| G07 HB04–06 | S07 | 返回修改：pause、关闭／重启、resume | pause不触发；resume重新计时 | 通过，实际跨due与恢复锚点 |
| G08 HB04–06 | S08 | 取消：clear、关闭／重启、重新设置 | cleared不复活、不影响其它owner | 通过，实际C无载体、可重新管理 |
| G09 HB02；07 §8.15 | S09 | 输出：基础／额外prompt真实模型链路 | 单timestamp、英文模板、wire／持久一致 | 通过，2个新服务样本＋同版本extra样本 |
| G10 HB03、05–06 | S10 | 来源衔接：Messaging、Gateway switch／reset | UI唤醒旧owner，不误投／重绑 | 通过，复用匹配机制与真实Messaging证据 |
| G11 HB04–06 | S11 | 恢复：压缩旧／新Session控制及tip变化 | 同Conversation共用自身合法tip | 通过，复用同版本完整集成序列 |
| G12 HB04 | S12 | 合法分支：new／reset／fork | 新owner不继承，父定义保持 | 通过，实际new／branch_stored＋匹配reset证据 |
| G13 HB01、04、06 | S13 | 隔离：两个Profile同物理ID及不同配置 | 目标DB／时区／配置，不借启动Profile | 通过，复用同版本隔离完整旅程；本次自建枚举另核 |
| G14 HB05–06 | S14 | 异常恢复：busy、队列、writer拒绝、submit失败 | 用户优先、未执行退款、后续可继续 | 通过，复用同版本受控故障／恢复证据 |
| G15 HB06 | S15 | 并发管理：双连接claim及后续pause／clear／replace／resume | 同tick一次、旧worker／退款不覆盖新操作 | 通过，复用双真实SQLite连接与最终状态证据 |
| G16 HB01、10 | S16 | 原生关闭：旧native定义和CLI／Gateway／UI | 关闭路径保持、不自动迁移 | 通过，复用正式分支定向证据 |
| G17 HB02、07；06 §1.4 | S17 | 呈现：Heartbeat折叠／展开、failed_turn | 固定浅／暗移动／桌面，来源身份保持 | 通过，复用固定版本视觉／测试／包证据 |
| G18 HB07–08；部署SOP | S18 | 后置：部署双SPA及Alex置顶正式设置 | 7200秒、空prompt、fire_count0，不提前触发 | 初始f32部署／设置事实已核；回执缺陷并入S01，最终修复版待独立验收／发布收据 |

覆盖包含设置→切换→close→断连→后台执行→读历史，设置→停机跨两due→新进程恢复，pause／clear→重启→跨due不复活，resume→新锚点，以及身份、配置与失败交错。等价类保留空／空白／额外prompt、active／paused／absent、当前／压缩／旧generation／新fork、全局开／关、独立Profile。并发故障用已有同版本受控证据避免昂贵重构；核心用户服务旅程独立真实执行。未穷举全部组合，未删计划场景。

## 4. 详细场景与执行结果

### R2实际结果与复现证据（18:15–18:19）

实际执行已获主会话过目。新证据路径统一第2节，E/S/F/N含义沿该节；下列结论与原始预期逐项比较，无场景缩减。U01–U16版本ed／固定0b8843f；复用的f32路径由reviewed-note-only.diff及evidence-audit证明影响匹配。

- **R2-U01 通过。** 新WS依次/hb无prompt、every extra、every纯空白，全部7200/active，prompt为空/R2_EXTRA/空；status可读。每次完整output为“Saved for this Conversation. The UI backend runs due heartbeats while it is running, even after you switch conversations or close the page. Settings survive backend restarts. /heartbeat pause | resume | clear to manage.”，无旧进程存续限制。RPC原文及state真值均留存，准确描述持久行为与运行前提。
- **R2-U02 通过。** 新WS A替换/pause/resume/clear各步B_before全字段一致；补反向B pause/resume/clear时A全字段一致，最终都null；C初始null。reverse.log及state `reverse_b_management_kept_a=true`，不以单方向冒充双向覆盖。
- **R2-U03 通过。** 新true Home scheduler=false，A/noting off后every仍新持久note及active；只读隔离DB local state noting_enabled=0。实际到期沿S两自然结果仍成功；E `test_heartbeat_does_not_grant_disabled_scheduler_capability`真实dispatch返回scope_denied且表0，未用“无工具名”代替权限证据。
- **R2-U04 通过。** 新WS正式close A/B/C、断唯一连接、HTTP读回历史、重连resume A仍完整active设置。S原始close→无WS→自动宿主61.859秒后恢复自身Main，HTTP读完整carrier+HEARTBEAT_OVER，B/C零载体；未调用handle_request/scan代替该旅程。TTL变体E实际reap timer.function触发回收后新宿主恢复，独立区别受控时序。证据S RPC/lifecycle/disconnected-close-history/wire1及E最终15项。
- **R2-U05 通过。** 新真进程87693结束→87782启动，active B全字段读回不变，A paused/C null（按U06合法历史准备，未把本次说成A active重启）。S原始三PID/lifecycle证明148.584687948秒停机跨两due后无WS新进程只一新请求/载体、count1；未补积压、不投B/C。无变化机制复用，不新增等待/付费。
- **R2-U06 通过。** 新close/restart后A paused全字段保持、C cleared为null、B active不变；A resume anchor为恢复时刻、next_due=anchor+7200、created/count0保持，随后pause/clear。S98.121秒paused跨due与C多重启无carrier补实际时间边界；新旅程不声称已跨2h。新state/RPC、S service-summary/history。
- **R2-U07 通过。** E完整native publish_compression_child序列旧pause→新read、新resume→旧read、旧clear→新null；arm后仅tip有carrier。claim后真实tip轮转使首scan无模型/count0，下一scan仅新tip/count1；old段无载体。已读正式测试序列及final15/store23日志；受控transport不冒称新压缩模型。
- **R2-U08 通过。** 新公开create三Conversation与branch_stored fork，子read null、父A_active全字段保持；E native SessionStore reset/switch和session.branch/new draft序列补reset及fork-marker后压缩自己的owner。离开父不删除，父后续恢复仍可用。新RPC/state与E最终宿主/store证据。
- **R2-U09 通过。** E虚构weixin peer→旧ref登记→switch/reset新generation，通用route拒旧但专用合法spine恢复旧owner；UI platform、旧source/新route/metadata保持，新generation无carrier。真实E heartbeat-empty来源weixin、runtime/platform tui、HTTP200/HEARTBEAT_OVER补接口；无自动向渠道发送。读取完整测试/底座/日志，不声称生产微信触达。
- **R2-U10 通过。** 三新Home启动前枚举均唯一自建default，无用户Profile。E双真实DB同physical字符串的A/B/C设置与pause/resume/replace/clear不串库；目标Asia/Shanghai timestamp为1970-01-01T08:02:00+08:00；冷宿主目标test/b、启动Profile禁用/count0，完整最终状态已核。配置/模型受控证据与真实K3样本分开描述。
- **R2-U11 通过。** E busy running/cancel/queued解除后恰一成功；lease拒绝/submit拒绝或异常/claim storage异常无call、count0、running释放，后续storage恢复成功；N缺绑定/原生resume guard拒绝保留due、真实warning、无焦点误投，条件恢复后目标执行。完整输入/序列/终态和10/15/2项有效日志匹配，未注生产故障。
- **R2-U12 通过。** E双独立SQLite连接屏障仅一claim、count1；claim后pause/clear/replace/resume新操作使fire_is_current/refund false，最终与管理后全状态相等；退款一次有效、旧退款不覆盖后claim，宿主claim后pause无模型且paused。完整store13/最终store+mode23及宿主15日志，未复跑或冒称压力测试。
- **R2-U13 通过。** 新false/en及false/zh真实WS空/空白prompt均不建立定义，非空2h成功；output最后行仅原有两空格显示框架＋catalog原文，英文及中文分别逐字相同。中文为“会话空闲且间隔已到时，作为普通回合触发。使用 /heartbeat pause | resume | clear 进行管理；仅在当前 Hermes 进程运行期间有效——如需持久化的计划任务，请使用 `hermes cron`。”，并非fallback。pause/resume/clear正常且最终null；E native template/CLI/Gateway/UI及旧meta保持不迁移完整序列支持关闭边界。源码note helper直接return native_note，与新真实输出相符。
- **R2-U14 通过。** S两真实自然serve wire和E两代表样本SHA/HTTP200与持久carrier匹配，原文固定英文、user role、单内部timestamp、无fires every/空Additional；extra位于正文后闭合前，实际LANTERN_GREEN+HEARTBEAT_OVER保留。S root/tools逐字一致、K3/high，E source weixin→tui保持。4样本复用有精确diff/hash边界，新增0请求，未用机制mock替代真实接口。
- **R2-U15 通过。** 本验收重新逐个核F439文件/归档SHA，读取既有浅色mobile、暗色desktop/expanded、failed-turn图及固定timeline原始测试。Heartbeat折叠标题/HeartPulse/陶土橙棕底/阅读宽度清楚；展开保留内部timestamp/英文/extra，无外时间/操作/附件。固定测试真实wrapper/empty/extra正例及assistant/system/plain/quoted/unclosed/old/forged display反例、source对象及UID保持均核。917/1skip/TypeScript/build仅既定包证据，无新浏览器或在线UI声明。
- **R2-U16 通过。** 阅读取消诊断SQLite持久18项、partial及同措辞模型反例、fixed timeline failed-turn/slash/terminal-only序列与既有图：仅实际类型行原文卡片无标题，无额外terminal合成，模型正文与partial/slash保持。后端路径未因note修补变化，既有retention缺帧基线失败保留，不声称全仓全绿。
- **R2-U17 通过（18:24后置补验）。** 三新收据表明18:21补发版精确ed、前端0b8843f/439文件/归档SHA匹配。实际`/`和`/dashboard/`各HTTP200/含机器token，index JS/CSS200且SHA等于固定manifest；匿名公网302认证、ui_visual_acceptance=false。生成脚本同时核Web health commit与Gateway code_sha均ed，两个unit active/running/NRestarts0，微信connected；无活动安全停服务、三库quick_check备份/受限配置SOUL指纹/PM-lock依赖diff为空/旧源码与static恢复点完整。三Profile18组表（messages/schedules/pending/bindings/aliases/heartbeats）完整行SHA前后相等，config/binding true、请求0、无自动回滚；只比较本次真实部署前后，不用初始f32旧消息数覆盖期间用户新写入。新receipt+脚本及独立final-receipt-audit.json支持通过，无在线登录后UI新声明。
- **R2-U18 通过（18:24后置补验）。** 原真实唯一pin/正式设置回执与最终只读ref `conv_8dc89e12cc9b42b5a77986f4d9b02cec`、stored `20261011_223115_59ad08`相同；final heartbeat字段prompt空/status active/interval7200/created1792576689.5657868/last_fired0/count0，revision1。最终formal_control_read整份字典与原receipt.control相等，包括控制revision哈希和updated_at；next_due1792583889.5657868即19:58:09.565787北京时间保持。完整Heartbeat表在补发版前后SHA相等，read-back自身全部六表SHA和原行也相等，set_called=false、production_model_requests0；脚本只resume/read且观察无模型start/delta。原错误成功note是历史事实，由本地ed真实输出及新版部署一起关闭，不涂改原回执，也不为复验再次every。

### R2详细执行计划（执行前预期，原样保留）

共同版本为ed／固定0b8843f；新实际数据为自建临时Home的公开seed Conversation A/B/C，所有新定义2h且完成前清除。证据写本次ignored目录，原始RPC完整output、不含token/凭据。每项执行后追加实际、时间、证据、结论、偏差，不用通过率覆盖用户输出。

- **R2-U01**：公开session.create A→`/hb every 2h`→control.read→status→`/heartbeat every 2h R2_EXTRA`→read→纯空白prompt替换→read。预期每次成功output都说明Conversation保存、切换/关页保留、重启持久、仅后端运行时执行，含管理指引且无“仅当前进程”；状态一条7200、prompt分别空/extra/空，owner保持。新实际WS核完整文本，不只断言DB。
- **R2-U02**：B设置2h B_ONLY，记录全字段；A依次替换/pause/resume/clear，各步读B并保持一致，反向B操作读A；新建C默认null。预期无串owner、无多条有效定义，B用户状态清楚可继续管理。新实际WS＋只读HTTP历史。
- **R2-U03**：true Home中scheduler=false，A `/noting off`后every/read/status。预期A仍Secretary持久提示与active，local关闭不转native，Scheduler仍无授权；到期用户结果及工具拒绝审S/E完整已有效链路，不在本次新触发模型。
- **R2-U04**：审S原始RPC设置、正式close、唯一WS断连与lifecycle、HTTP历史、wire：预期无原runtime/页面仍自然恢复A，B/C无载体，原user/assistant完整持久。E补TTL真实timer回收序列；新旅程再执行close/断连/reconnect读active，校验本次success note与实际恢复一致。复用前先独立核diff不改机制。
- **R2-U05**：审S进程PID退出、148.58秒跨两due、新PID无WS启动、单新carrier/单HTTP200及count1；预期不补积压、不投B/C。结合本次新进程只读回A active，证明输出与现版本持久读回；不声称本次又等多个due。
- **R2-U06**：A pause、C clear、B active；关闭服务并启动新进程，分别read paused/null/active→A resume→read锚点为本次恢复时刻且next_due=anchor+7200→再pause。预期创建时间/count保留、对方全字段不变。跨due不复活审S原始98秒和C多重启历史。最后clear所有自建定义。
- **R2-U07**：读取E合法publish_compression_child完整前置及旧/新session控制序列：旧pause→新read、新resume→旧read、旧clear→新null；arm后只向自身tip执行，claim后tip变化退款后下一scan向新tip。预期同ref、无复制、无旧段carrier。
- **R2-U08**：A有定义时公开create新C与branch_stored合法fork→read新owner null且父A状态保持；reset与fork-marker后再压缩审E原生SessionStore/UI序列。预期三类新Conversation独立，无从父继承，无离开清除。
- **R2-U09**：审E原Messaging虚构peer登记→switch/reset新generation→旧refHeartbeat恢复与新路由诊断，以及匹配真实weixin样本。预期旧合法spine恢复UI platform，原source保持、不自动渠道投递，不放宽通用resolver、不重绑，新的peer无carrier。
- **R2-U10**：启动前新Home枚举必须唯一；审E双真实DB相同physical ID、不同设置与全局配置、目标Asia/Shanghai时间与目标模型冷恢复，逐步读最终状态。预期A操作不能改另一Profile，启动Home不能主宰目标资格/时区/模型；不访问用户Profile。
- **R2-U11**：审busy running/cancel_requested/queued→解除→成功；writer拒绝、submit拒绝/异常、storage异常、缺目标/恢复guard拒绝→恢复条件→最终正确目标。预期拒绝前无模型/count消耗，失败真实可观察、due可重试、无错投、资源释放。只用匹配受控证据及N两独立负例，不向生产注故障。
- **R2-U12**：审双独立SQLite连接屏障claim唯一成功；claim后pause/clear/replace/resume再旧worker submit/refund。预期同tick一次，old false且新管理状态全字段不变，当前claim仅一次退款有效。检查完整序列与终态而非只看测试名称。
- **R2-U13**：独立false Home正式RPC空/空白every应拒绝、非空2h设置成功；实际output末note与该本地化语言的原生`heartbeat.set_note`逐字比较，native模板/管理保持。若原生支持两种语言，则分别在隔离Home验证英文及中文catalog，不改用户locale。原生CLI/Gateway/UI执行与旧native表保留不迁移审E；关闭分支不应用新持久承诺。
- **R2-U14**：逐条核S两真实K3与E empty Messaging/extra样本的实际wire、HTTP200、role/content和持久history：精确07英文、单一内部实际timestamp、无fires every/空Additional、extra正确位置；Assistant保留HEARTBEAT_OVER、root/tools及High/目标模型一致。版本hash/diff证明未变路径后复用；新增真实模型预算为0。
- **R2-U15**：重核固定前端归档SHA/439文件及构建输入；只读既有浅/暗360×792、1280×800、展开截图和正式组件测试：预期标题Heartbeat/HeartPulse/陶土橙棕底/同类宽度/默认折叠、展开内层timestamp/正文/extra，无普通用户操作/附件/外时间。普通提及、Assistant引用、残缺/旧模板/伪display不能分类，source/UID不变；无新浏览器操作。
- **R2-U16**：审已授权failed_turn后端取消诊断真实SQLite写入、模型partial与同措辞反例、固定前端展示与terminal-only/slash反例。预期只标真实原消息行、原文卡片无标题、无额外合成卡，无历史猜测迁移，metadata恢复及其它消息保持。
- **R2-U17**：先核已有初始f32 receipt只支持其当时事实，接收主会话ed最终发布receipt后逐项读实际服务version、固定dist指纹/双SPA静态资源、token/REST/WS契约适用证据、Web/Gateway状态、空闲切换/PM-lock/备份恢复点、history/schedule/pending/binding/config等前后保护。预期新版精确上线、无无关变更/自动旧库回盖；接口成功不冒称登录后UI。
- **R2-U18**：只读初始Alex唯一pin→正式7200s/空prompt设置回执与新发布后readback，核同ref/stored/定义全字段及原锚点、其它Heartbeat与绑定/历史/排期/配置不变、未重set/提前触发。初始错误note由U01新实际输出关闭产品缺陷，原生产回执历史不涂改；最终运行ed后不得把初始f32收据当最终版本。

### 原报告历史（保留）

以下各场景预期均先于执行写入原计划，主会话已过目。实际产品版本统一f32／前端0b8843f。服务数据为第2节虚构seed；引用证据目录按第2节解释，不将受控transport替换误写成真实模型。

- **S01 设置／替换／status。** 起点是实际WS创建的新A；输入依次`/hb every 1m`、`/heartbeat every 2m VALIDATION_B`、`/heartbeat every 1m    `，公开control.read核对。预期原owner只有一条且字段匹配、空白额外段省略；正式用户输出须与07 §8.15规定的关页／重启后持续有效语义一致。实际interval依次60→120→60，prompt依次空→VALIDATION_B→空，原owner不变；最终实际`/heartbeat status`返回paused。末尾另从空draft实际`session.create`、`/hb every 2h`、control.read、clear／close，7200秒且新owner默认无定义。证据`rpc-transcript.jsonl`与`journey-state.json`；17:39–17:46。初审曾判通过；**现更正为失败（HB-UAT-01）**：同一原始RPC记录第14、19、24、29、60、87、147、164行的成功输出均保留旧note“lives only while this Hermes process runs”，与实际持久产品语义矛盾；Alex生产正式set回执再次确认。状态／owner／空prompt结果保留，但不能据此判整个用户目标通过。该提示是否可理解属于原有用户结果判据，不是新增文案要求；未规定必须采用某一句新英文。修复提交ed94619尚未由本验收者复验，不能关闭本项。
- **S02 独立Conversation交错。** A各次替换／pause／resume／clear期间，B设`/heartbeat every 2h B_ONLY`，分别resume／read；C另设60秒后clear。预期互不影响。实际每次B读回均与初始B_before全字段相同，fire_count0且历史无Heartbeat；最终清理前再次核一致。A的后台结果只写A，C为absent。证据RPC、三者HTTP历史、service-summary。**通过**；与S04–S08共享完整历史，未删步骤。
- **S03 局部／独立开关。** 起点全局noting=true、scheduler=false；实际`/noting off`，A仍active。预期本地关闭不影响Heartbeat、不授Scheduler能力。实际两次自然后台均完成；只读自建DB显示A的noting_enabled=0；两份真实wire含History／Notebook等原生工具但无scheduler，原生Scheduler拒绝分支另复用`test_heartbeat_does_not_grant_disabled_scheduler_capability`及最终运行日志。**通过**；不以无工具名代替拒绝证据。
- **S04 无页面／无WS用户结果。** A在17:40:35设置后正式close，唯一WS当时断开，此后只用HTTP读取历史；后台自然在设置后61.859秒认领。17:41:58读到一条完整user Heartbeat及assistant：`Nothing to attend to — no tasks, commitments, reminders, or pending work.\n\nHEARTBEAT_OVER`。预期只有A结果；实际B／C零载体，A fire_count1。HTTP没有触发执行入口，期间无WS prompt.submit或管理调用；真实serve lifespan自动宿主完成。证据`lifecycle.jsonl`、`disconnected-close-history.json`、`service-wire-1.json`／HTTP200、完整RPC／HTTP记录。**通过**；无页面事实指无浏览器和无WS连接，并不声称视觉结果。
- **S05 runtime被关闭／回收。** S04前实际`session.close`返回成功，runtime `afa5ea5f`释放，持久定义active；后台恢复后重连获得新runtime，A历史及ref保持。预期close不撤销定义；实际从无原runtime到Main结果如S04。真实TTL定时器回收分支另复用最终`test_close_or_actual_reap_then_new_host_recovers_same_conversation[True]`，包括timer实际function、旧runtime消失、host恢复、单载体与wire一致。**通过**；实际close与受控TTL证据分开，不说本次等待了完整TTL。
- **S06 完整进程重启及漏tick合并。** 第一次结果后将A重新设60秒、close其runtime，17:42:00 SIGTERM停止PID77885，确认不存在；等待148.584秒后17:44:28以同Home启动PID78842，保持无WS。149.067秒间隔后自身A被恢复，17:44:35 HTTP读到第二载体和相同正常末尾回复，替换定义后的fire_count为1，last_fired_at锚到本次实际触发时刻。预期停机多个due只合并一次、不补积压。实际只有一个新载体、一个新API请求，B／C无结果；随后才重连pause。证据生命周期、`process-restart-history.json`、wire2／HTTP200及state。**通过**；实际等待长于计划最少125秒，覆盖强度更高。
- **S07 pause跨重启／resume重计时。** 第二结果后实际pause，17:44:47全新PID78945启动；在重启计时98.12秒后第一次read仍paused／fire_count1，HTTP载体总数仍2。预期旧到期不复活、resume后等完整interval。实际status为paused；resume时last_fired_at重锚为1792576013.274324，下一到期1792576073.274324，创建时间和fire_count1保持，随即再次pause避免第三次请求。B保持。证据RPC、`service-summary.json`、`journey-state.json`。**通过**；原脚本错误限定created_at重写已纠正，见第5节，不改“恢复重新计时”判据。
- **S08 clear跨重启／重新管理。** C在首次管理时60秒定义后实际clear；经历停机跨due及第二次重启跨due，HTTP历史始终无Heartbeat，control.read为null。随后C实际`/heartbeat every 2h NEW_C`后读回prompt，再clear成功；A／B不受影响。预期清除不复活且新定义可用；实际满足。DB保留内部cleared墓碑不作为有效定义，用户控制入口始终null。证据RPC、HTTP及最终状态诊断。**通过**；无产品语义变化。
- **S09 模板／真实模型输出。** 本次两实际服务样本检查role=user、完整wrapper、每条恰一个timestamp、无fires every／空Additional段；实际wire包含与持久carrier逐字相同文本，两次root system和顶层tools完全一致，High参数明确，最终回复保留而未被静默。额外prompt复用同版本原生K3真实样本`heartbeat-extra`：Additional prompt位于基础正文后闭合标签前，返回`LANTERN_GREEN\nHEARTBEAT_OVER`，1请求HTTP200，真实wire／来源哈希已核。预期基础及可选正文均符合；**通过**。本验收新增2请求，不把复用样本计作新增请求或再次服务执行。
- **S10 Messaging／Gateway身份。** 合法历史为原生SessionStore虚构weixin peer→登记旧Conversation→switch或reset新peer。最终15场景日志及源码序列证明：旧Heartbeat专用恢复旧owner／合法tip并走UI平台，通用route仍拒绝旧generation；新peer路由、metadata、原source保持，新generation无carrier。实际模型补证复用`heartbeat-empty`原source weixin、runtime_source／platform=tui、HTTP200正常HEARTBEAT_OVER，未向渠道投递。**通过**；机制时序受控、模型样本真实，未新建生产渠道或宣称微信触达。
- **S11 压缩归属／tip切换。** 复用原生publish_compression_child建立合法历史，旧／新物理Session公开control读相同定义，旧pause→新read paused、新resume→旧read active、旧clear→新null；再arm后正式UI只向tip提交。claim后压缩场景首次无模型、退款count0，下一scan向新tip完成count1，旧物理段无载体。依据最终Conversation宿主15项及store23项日志、相应完整测试序列。**通过**；未新跑真实压缩模型，此为同版本原生DB／UI受控集成证据。
- **S12 新Conversation不继承。** 本次A已有定义时实际`session.branch_stored`读取其持久历史，返回新stored ID，control.read为null；A仍active且后续自然结果正常。三初始create及末尾空draft均默认无Heartbeat。reset真实SessionStore及branch原生UI分支复用最终同版本序列，原父设置保留、新ref无定义；fork继承marker后压缩仍属fork的边界由store最终测试覆盖。**通过**；首次fork额外title字段拒绝属脚本误用，纠正后合法入口通过。
- **S13 Profile隔离。** 复用同版本双真实DB相同物理IDfirst、不同prompt A／B／C，one pause／resume／replace／clear不改变另一Conversation或另一Profile；目标Home配置时区Asia/Shanghai而调用方其它Home，实际载体为`1970-01-01T08:02:00+08:00`；冷宿主从target Home恢复模型test/b而启动Profile disabled、计数保持0。读取完整fixture／断言与最终store23、runtime39日志核对。**通过**；不把受控模型test/b冒称真实Provider样本。本次实际服务单Profile隔离枚举独立核实，见第2节。
- **S14 用户优先／拒绝／失败恢复。** 复用同版本busy running／cancel_requested／queued三变体，先无calls／count0，解除后正式UI一次成功；writer lease拒绝无call、count0且原weixin surface不变；submit refused／raised退款不保持running；storage claim异常解除后后续成功。缺目标／恢复错误独立负例维持待执行、不误投其它owner。预期拒绝不消耗发生、用户工作优先且可恢复；完整序列及最终状态符合。证据`tests-final-runtime.log`、`tests-alias-final.log`、`tests-edge.log`及Verification独立2负例。**通过**；不在本次服务或生产注入故障，也不重跑大套。
- **S15 并发／管理交错。** 同版本两个真实SQLite独立连接同时屏障claim，仅一个返回发生，最终count1；旧worker claim后pause／clear／replace／resume，fire_is_current false、旧refund false且最终state与新操作后完全相同；原refund仅一次有效，后续claim不能被旧退款覆盖；UI claim后pause无calls且最终paused。依据store最终23项、宿主最终15项及完整步骤。**通过**；使用机制层稳定构造竞争，不以本次两次真实请求冒充并发压力覆盖。
- **S16 全局关闭／原生路径。** 复用全局false时empty prompt ValueError、native模板逐字保留、CLI／Gateway命令非空规则及watchdog／Gateway ownership／UI poller正式分支证据；native meta旧定义在开启时不自动迁移／被覆盖，Secretary新定义只进自有表，切回false读到旧legacy且原模板正常due。最终26个native Heartbeat、10个全局分支、7个UI tick及Gateway相关日志由evidence-index定位。**通过**；未切换用户全局配置或批量迁移生产定义。
- **S17 固定前端呈现及配套失败卡片。** 只读既有`heartbeat-mobile.jpg`、`heartbeat-dark-mobile.jpg`、`heartbeat-dark-desktop.jpg`、`heartbeat-dark-expanded.jpg`、`failed-turn-final.jpg`；目录 `/Users/edgar/.codex/visualizations/2026/10/21/01a15d70-fbb7-7190-b233-211cd9270a42/`。浅／暗移动360×792、桌面1280×800的固定Heartbeat标题、HeartPulse、陶土橙／棕底、同类阅读宽度、折叠状态清楚；展开仅内层timestamp／正文／Additional prompt，无外时间／普通User操作／附件。固定组件测试复用完整wrapper空／extra正例、assistant／system／普通提及／不闭合／旧模板／伪造display反例及source对象／UID保持；failed_turn只真实标记行，无额外派生卡，partial及slash为正文。后端明确取消诊断与模型同措辞反例的18项SQLite持久证据匹配。**通过**；固定包SHA重新匹配，非新在线浏览器验收。917／1skip只对应已绑定版本，历史retention既有1失败仍保留，不声称全仓全绿。
- **S18 后置发布及Alex。** 预期主会话前置两门禁完成后部署f32＋固定0b8843f包，实际双SPA／health／保护指纹／备份读回，再对实际唯一置顶Conversation正式配置7200秒／空prompt／active／fire_count0及正确next_due，不提前触发测试Turn。初审时动作未发生，曾记“后置待收据”，此历史保留。现只读收到的三份初始收据：后端health准确f32，固定前端0b8843f／439文件／归档SHA匹配；双SPA首页及关键JS／CSS实际HTTP200、各自含机器token，Web／Gateway active且NRestarts0、weixin connected，匿名公网302至认证入口，ui_visual_acceptance=false。部署有旧源码／静态目录恢复点及云端备份，依赖diff为空，host／alex／study受保护历史／排期／pending／绑定／alias指纹前后一致，config_unchanged与binding_unchanged为true，生产模型请求0、无自动回盖。Alex正式ref为`conv_8dc89e12cc9b42b5a77986f4d9b02cec`，stored ID为`20261011_223115_59ad08`，正式控制读回7200秒、prompt空、active、fire_count0，next_due_epoch=1792583889.5657868（2026-10-21 19:58:09 Asia/Shanghai）；protected／binding／other_heartbeats保持，未提前触发。**上述初始f32发布及设置事实有收据支持；成功回执仍含错误note，判失败部分并入S01。最终ed94619修复版独立全轮复验和最终发布读回仍待完成，不签最终S18通过。** 不重设Alex、不改变其已登记排期；不从匿名302或接口HTTP200推成在线UI通过。

## 5. 问题、修复与复验

### 最终问题关闭状态（18:24）

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| HB-UAT-01 / HB-GAP-02 | f32设置回执错误生命周期→ed按全局分支修补→新独立全轮前置→补发版 | U01/U03实际完整WS正确持久说明、U13 en/zh逐字native；U01–U16全轮与最终ed运行证据均符合 | 已关闭；初审失败/撤回仍保留历史 | ed94619 | 新RPC/state/audit + 最终deployment/post-release收据；原提示不需重设Alex以补证 |
| HB-UAT-POST | 新前置通过→主会话18:21补发版→真实只读回读 | U17/U18版本/静态/服务/保护表与原Alex定义及整份control一致，next_due保持、set_called=false、请求0 | 已关闭，整轮最终Validation通过 | ed94619＋fixed0b8843f | final-receipt-audit.json；生产三receipt；无新范围内发现 |

### R2前置问题与复验历史（18:19，后置已由上表关闭）

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| HB-UAT-01 / HB-GAP-02 | 原S01/S18成功note否认持久；新版新HTTP/WS完整管理与恢复旅程 | U01/U03新true output准确持久语义，U13 en/zh各逐字native；close/新进程状态保持。253帧与state/audit见本次证据根 | 新版前置用户结果已关闭，旧失败及撤回仅初审历史 | ed94619 | R2-U01–U16全轮通过；最终发布后U17/U18继续补证 |
| HB-UAT-POST | 初始f32发布/设置→新两前置→ed补发版 | 初始事实保留，等待ed最终receipt和Alex全字段/锚点只读保持 | 后置待补，最终门禁尚未关闭 | ed待上线收据 | U17/U18，不重set/提前触发 |
| R2-HARNESS-01 | native en成功后脚本最后行比较漏两空格 | 实际原文已正确；断言应比较原CLI framing的两空格+catalog，未改产品。journey-run.log原断言保留 | 已关闭，首次流程finally停进程；只续native分支 | ignored脚本 | 续接en/zh实际WS逐字通过，native定义清除；6PID均停 |
| R2-HARNESS-02 | 目录检索只命中en误推中文fallback，审计发现zh实际不同 | 实际zh Profile解析中文catalog且WS逐字一致；原假设纠正，未改翻译/产品/判据 | 已关闭，仅审计假设，非产品失败 | ignored audit | state native_success_output/isolation_before_start核真实中文，fallback=false |

无新增范围内产品缺陷。原范围外retention缺帧不重开、不隐藏；未调整冻结规则/等级或新增豁免。

### R2执行前状态（历史保留）

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| HB-UAT-01 / HB-GAP-02 | 原S01/S18 every成功，完整output否认Conversation持久性 | 原失败与撤回保留；新Verification已核ed代码及27定向/10检查，不代替本Validation实际输出 | 本次未关闭，待R2-U01/U03/U13及全轮影响核验 | ed94619 | 新真实HTTP/WS true准确持久提示、false逐字native本地化note；其余18全轮场景逐项判定 |
| HB-UAT-POST | 初始f32联合发布并设置Alex后，note补发版 | 初始事实已发生；ed新版收据尚未收到 | 后置待补；不阻断先验后发布顺序，不签最终通过 | 初始f32；待ed | U17/U18只读补审；Alex原定义及锚点保持，绝不重set |

其余新问题当前无：尚未实际执行，不能据此声称未发现缺陷。若出现新失败，记录完整合法输入和序列、原预期/实际、版本、证据及恢复；不改产品代码、不降低判据，交主会话整改。

### 原报告历史（保留）

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| HB-UAT-01（对应HB-GAP-02／HB-V-01） | S01实际WS every成功→状态字段正确→原note称仅当前进程有效；S18 Alex实际set再次出现 | 预期提示符合Conversation持久语义；实际`rpc-transcript.jsonl:14`等8处及`alex-heartbeat-receipt.json`均为旧note；初审已取得但漏核完整output | P2范围内产品输出缺陷；S01更正失败，撤回前置通过；实际持久功能仍有效 | 主会话报告修复提交ed94619da81547bcb9e27aab60b608b2310e6890，27项／10检查通过；**本验收者未复验，不代签** | 全新独立Validation全轮覆盖后实际RPC复验true持久提示、false原生note及相关管理／重启用户结果；最终发布收据须匹配修复版 |
| HB-UAT-POST | S18：前置验收→部署→Alex实际置顶正式设置 | 初始三receipt补齐f32实际版本、双SPA、保护数据及7200／空prompt／active／count0；原“尚未发生”只为初审时点 | 初始发布／设置事实已核；成功回执缺陷归HB-UAT-01，整轮仍不通过 | 初始运行f32；最终修复版未由本报告签收 | 新独立门禁及最终修复版发布收据待完成；Alex已生效设置不重设、不提前触发 |
| HB-UAT-HARNESS-01 | 准备脚本import yaml；未启服务 | PM使用hermes_yaml且无顶层yaml，原脚本ModuleNotFound；改写JSON兼容配置 | 已关闭，零模型调用，无产品缺陷 | 仅ignored脚本 | 后续实际服务成功读取配置；未安装或更改环境 |
| HB-UAT-HARNESS-02 | S12 branch_stored带title→RPC拒绝 | 合法schema拒绝额外字段4000；去掉title后正常建立fork，父state保持 | 已关闭，错误使用不作产品失败 | 仅ignored脚本 | RPC原拒绝及修正后的新ref／null控制均留存 |
| HB-UAT-HARNESS-03 | S07 resume→脚本误要求created_at重写且last_fired_at=0 | 冻结要求是重新计时；原生实际更新last_fired_at，保留创建时间和count；17秒内正式pause保护，无第三请求 | 已关闭，判据不变，字段假设已纠正 | 仅ignored脚本 | 按原始行为判据再resume读回新锚点＋60秒、count1，立即pause；原输出及纠正记录保留 |

初审曾写“未发现范围内产品缺陷”；现明确更正，HB-UAT-01为范围内用户输出缺陷。漏查原因是把设置／状态／持久结果作为S01主要判据，未逐字核对已取得的成功output与持久语义是否一致；这是本验收覆盖遗漏，不是证据缺失。后续全轮复验应同时核用户能否正确理解当前状态与下一步，不能只断言状态字段。以上更正不抹除原有效服务、wire、恢复及隔离证据，不降低原始判据迁就修复。

只读审计脚本另修正server stdout转stderr的捕获和本地Noting字段名（noting_enabled），没有启动额外服务、请求或修改产品。范围外既有retention缺帧失败沿Verification／原日志保留，不在本轮重开、不隐藏、不据此声称全量通过。未降低门禁、改规则／阈值或新增豁免。

## 6. 验收结论与推荐复核

### 最终全轮验收结论

**R2-G01–G18全部通过，整轮最终Validation通过、门禁关闭。** 新版成功note实际用户结果、持久管理与全轮未变路径复验、固定前端/failed_turn配套，以及ed实际补发版和Alex原定义全字段/锚点保护均有匹配证据；无失败/未执行/证据不足场景，无新范围内缺陷。初审原失败和撤回不抹除，修复→全轮独立复验→最终版本回读的关闭链明确。

交付入口为 `.autonomous/20261021-conversation-heartbeat/validation.md`，本次证据根 `.hermes-dev/conversation-heartbeat-validation-r2-20261021/`，新实际RPC/HTTP、state/evidence-audit、final-receipt-audit及E三最终生产收据可复核。Alex已设2h无额外prompt，下一自然到期19:58:09北京时间；无需用户重复配置，不为复核提前触发。新版前端浅/暗视觉仅复用同固定产物证据，未声明新在线登录后UI、手机/蜂窝、微信触达或长期运行实测；历史范围外基线失败保留，不声称全仓全绿。

本验收全部资源收尾，无新模型/外部HTTP、生产连接或显示操作。最终目标完成及用户交付由主会话结合最新独立Verification、当前收据及交付判定决定。

### R2前置验收结论历史（18:19；后置已由上段关闭）

R2-G01–G16用户目标通过，**新版前置Validation通过**。HB-UAT-01已由真实WS成功output与两原生语言分支逐字对照关闭，持久管理/close/重启与状态回读可理解且可继续管理；全轮身份/开关/恢复/故障/并发/模型/固定前端均按适用原始证据复核，无仅重测旧缺陷。新增模型/外部请求0，3自建Home/6进程全部收尾，用户/生产/显示未触及。

R2-G17/G18新版部署与Alex原定义全字段/锚点保护仍后置待收据，**整轮最终Validation尚未关闭**，初始f32发布/设置不当作ed线上事实。主会话可按既定顺序接收前置并补发版，然后交只读receipt补审，不重设Alex。不新增浏览器/手机/微信触达/长期运行声明，不声称全仓全绿。

推荐复核本次`rpc-transcript.jsonl`的/hb、every空/extra/空白及en/zh完整output，配`journey-state.json`/`evidence-audit.json`和S自然tick/跨due原件；用户若自验，可在独立Conversation设2h后查看准确提示、管理并切换/关页。生产Alex无需为复核重锚或提前触发。最终目标结束由主会话结合两门禁与最终生产事实判断。

### R2执行前结论

全轮18项场景已独立制定并落盘；当前均未执行或后置待收据，**新版Validation门禁尚未关闭**。计划交主会话过目后，先进行隔离与源码/证据适用性审计，再执行新版合法HTTP/WS零模型管理旅程，同时核所有未变机制的原始完整用户结果，集中交回前置结论。新前置通过后等待主会话补发版receipt，只读补U17/U18，再判定整轮门禁。

推荐复核路径：自建Conversation `/hb every 2h`完整成功输出→status/替换→A/B独立pause/resume/clear→close/断连→新进程恢复→全局false原生输出逐字比较；自然到期/多due恢复沿S真实service与wire审计。生产只读原Alex7200s定义与锚点，不重设或提前触发。固定前端复用准确同版本图及产物，禁止新显示操作。最终目标是否结束由主会话综合两独立门禁和最终发布事实判定。

### 原报告历史（保留）

**当前Validation不通过：G01／S01的成功提示与冻结持久语义冲突；此前前置通过声明撤回。** G02–G17在f32版本已核实的实际服务用户结果及匹配证据保留，尤其是A正式close＋无WS自然执行、完整进程停机跨两个due后的冷恢复与单次合并、pause／clear跨重启不复活及resume重新计时。实际2请求、2HTTP200，无重试；三服务进程均停止，Key不落盘，用户／生产数据未触及。保留这些历史结论不代表修复后的ed94619全轮独立验收已通过。

G18初始f32联合部署及Alex正式设置已由三份本地receipt补核，7200秒／空prompt／active／count0及19:58:09 next_due有效，保护数据保持；不把已发生动作继续写成尚未发生。但成功note缺陷仍阻断整体用户目标，ed94619尚待全新独立Verification／Validation全轮复验与最终发布证据。**整轮最终Validation不通过，门禁未关闭。** 本验收者本次仅更正原报告及补核原发布事实，未运行修复版、未新发模型请求、未连接生产或重设Alex。

新验收者应从原冻结全范围重新列场景，保留有效同版本／无影响证据，重点实际读成功output和持久状态，再检查两全局分支及完整管理／恢复旅程。主要用户复核路径为隔离Conversation `/heartbeat every 2h`→准确持久提示→切换／关闭页面→后台到期结果→pause→重启后不触发→resume后重新计时；生产Alex不得为复核提前触发。前端只按固定包同版本证据复核，不引入显示操作。最终目标完成由主会话结合两门禁及最终发布结果判定。
