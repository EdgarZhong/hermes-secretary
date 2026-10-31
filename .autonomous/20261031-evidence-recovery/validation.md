# Validation：20261031-evidence-recovery

## 1. 结果概览

独立验收者：Validation 子 Agent；日期：2026-10-31。依据为本轮 snapshot-index.md、baseline.txt（初始 8b31d986dc、追加冻结 67d0fab44e）、07 顶部2026-10-31 A/B及§12.3、Notebook白板C3/C6/C7/K6/N1/N3。待验产品为 `a51a0bf17fff5ccea52ae9faebc880dd200a457e`；工作树HEAD `7e55c0810e414362547d4d2d96e80001d439314d`只有后继文档，产品源码未改。

**产品 Validation 门禁通过：V01–V12全部通过，无产品失败、未执行或阻断。** 本Agent独立设计并实际执行六条完整旅程覆盖12场景，最终6 passed / 0 failed，5.2秒。主会话执行前已亲读并同意完整计划（原件保留于ignored `validation/plan-content.txt`）。V13是后续发布／清树实际事实，等待主会话收据，不阻断产品发布前门禁，不能据本报告宣称已经上线或整轮收尾完成。

**2026-10-31发布／清理后补核：V13通过，13/13适用场景全部关闭，Validation门禁最终关闭。** 正式Alex于2026-10-31T10:09:58+08:00发布`bf28ab565ae322965e3b8eb0797486e1d0cdbac7`，相对已验a51产品代码无变化；最终原目录`main`为`913084338b76d9188e60dc5b10c7c15bb1cfb633`，检查时clean、只剩一个worktree。上段“V13等待”保留发布前历史时点，现已由实际收据关闭；详细补核见第4/6节。用户并非最初要求采用自主实现流程，是Agent自行选择；用户后续要求按已展开计划干完并上线，本报告不把流程选择冒称用户原始要求。

用户E12明确取消真实模型验证：本次新增真实模型/API请求为0，生产操作、外发、UI操作为0。受控SDK仅控制外部回复，证明正式机制与可观察结果可用，**不证明模型自然选择工具、概括语义或未来必然遵从Prompt**。没有把这项已取消条件重新列为阻断。

## 2. 环境与准备

- 真实macOS arm64、本地官方PM `.venv`，Python3.14.7；环境／版本／23项逐文件指纹及产物SHA见 `.hermes-dev/evidence-recovery-20261031/validation/environment-and-evidence.json`。23/23与D1/D2/D3有效证据一致，锁SHA为 `2bc4db483e9cba927cd7147f9ccbb09635f85bb3f1f36d6e9d51d06b65d1c67e`。
- 正式入口：`AIAgent.run_conversation`、固定模型工具dispatch、已注册 `server.handle_request` JSON-RPC、原生manual admission／child runner／Commit Gate、Main `notebook_show`、原生压缩与Note发布。认证外层未改；本次从认证后的正式RPC dispatcher进入，不冒称真实WebSocket登录认证已另行测试。
- SDK回复经OpenAI SDK+httpx.MockTransport或原有受控客户端脚本返回；真实builder、请求JSON、工具执行、SQLite、Notebook工作态／不可变版本／Snapshot、History、child与提交未替换。History故障场景只令其底层存储依赖抛出OSError，正式处理器和错误封套仍执行；原生压缩仅摘要依赖受控。
- `HERMES_HOME`及`terminal.cwd`／实际cwd均在Git root外 `/private/tmp/hermes-evidence-validation-20261031-r2/`；临时Profile和DB全为新合成数据。没有读取生产正文、用户配置或凭据，没有生产manual Noting、微信／飞书外发或可见页面操作。
- 独立输入：用户先选“社区活动周六室内，避开周日交通管制；周日只是助手建议、未接受”；后纠正“主要限制为志愿者周日考试，交通只是次要因素，活动未完成”。无索引Conversation另用“口令松树、不能写枫树”。真实UID由原生DB生成；手动RPC用独立合成m1/m2与request键。
- 唯一有效独立运行：`HERMES_PYTHON="$PWD/.venv/bin/python" HERMES_TEST_FILE_RETRIES=0 scripts/run_tests.sh .hermes-dev/evidence-recovery-20261031/validation/test_validation_journeys.py -- --basetemp=/tmp/hermes-evidence-validation-20261031-r2 -q`；`validation/run2.log`记6/0、5.2秒。首次参数错误、夹具准备错误保留，不作产品失败或通过证据，见第5节。
- 复用同版本机制：D1数据151项／Candidate62项／权限86项；D2全Prompt8项及相邻／footer／协议；D3manual34项及恢复6项／生成1项。只为并发、租约、取消／替代、全部资格、数组边界及完整上下文投影补充机制覆盖，未代替独立用户旅程。Linux `release/linux-environment.txt`绑定QA HEAD=a51a0bf、tracked clean、Python3.14.7／pytest9.1.1、同锁；`release/linux-tests-valid.log`真实Linux七文件111/0、97.4秒。未重复这些有效证据。

## 3. 用户目标与场景覆盖

| 目标编号及冻结依据 | 完整场景编号 | 场景类型与起点 | 数据/顺序选择依据 | 当前执行结果 |
|---|---|---|---|---|
| G1 A/E01/E02/E04：描述与UID共同维护 | V01 | create→同Task update→working show→finish→Main show | 区分用户选择与未接受的助手建议；一Task一槽 | 通过，V01-V02.json |
| G1 A/E04：跨Task追加及旧节点不变 | V02 | 前Task提交→用户纠正→新Task update→finish→重开DB读取 | 旧原因保留、新纠正追加、稳定entry身份 | 通过，V01-V02.json |
| G2 A/E06：旧组未知及no-op | V03 | 合法无描述旧JSON→Main读→Noting no-op／实改→再提交 | 缺描述为null、不回写，不造空描述或无意义版本 | 通过，V03-V04.json |
| G2 C3/C6/K6：Candidate与权限 | V04 | refs／direct候选→混传拒绝→源更新→提交→Main读 | 两来源互斥，refs沿源条目，不制造直接描述槽 | 通过，V03-V04.json |
| G3 B/E05：有索引按组Read | V05 | 真压缩→真实Notebook Framework→用户纠正→精确Read→回答 | 外层Conversation Ref及真实UID完整；已足够即停止 | 通过，V05-V07.json |
| G3 B：可见充分／即时问题 | V06 | 原文工具结果已可见→直接总结；无历史依赖算术 | 两种免重复读取的合法输入 | 通过，V05-V07.json |
| G3 B：索引缺失／不足／失败 | V07 | 无索引→Meta/Search→Read；失效UID→空Search；存储失败→未知 | 分开“无法定位”和“底层工具不可用”，不猜补 | 通过，V05-V07.json |
| G4 B/E09：正常恢复与完整Prompt | V08 | 正式builder→旧持久root→正常下一Turn→warm Turn | 定稿原文、原历史与工具不改、cache break一次 | 通过，V08.json |
| G5 §12.3/E11：manual请求到真实提交 | V09 | state not_found→start→running→create/finish→completed→Main show | 排队／运行不冒committed；真实child提交见证 | 通过，V09-V10-V12.json |
| G5 §12.3：幂等及owner隔离 | V10 | 运行中重复→完成重复→异request→branch／Profile→物理轮转重复 | 同键同child；不同owner不借旧操作；跨压缩保持 | 通过，V09-V10-V12.json |
| G5 §12.3：拒绝与无副作用 | V11 | busy／compression lock／空request→start；未知state；local关闭 | 错误可理解、零SDK、配置不变、不抢租约 | 通过，V11.json；全局等机制复用 |
| G5 现行Note边界 | V12 | manual成功无即时Note→真实原生压缩→唯一Note receipt | 不额外Compact，不修改自动参与／Idle配置 | 通过，V09-V10-V12.json |
| G6 E03/E08/E10：发布／清树收尾 | V13 | 发布及清树后实际收据 | 不把计划、代码通过当作已发布／已清理 | 通过；发布／清理后收据补核，见V13-final-receipt-review.json |

场景从冻结用户目标独立导出，plan.md仅作范围线索。等价类覆盖新／旧组、同／跨Task、direct／refs、Main／Noting、有索引／可见充分／无索引／缺口／失败、正常／busy／禁用、首次／重复／跨owner。严格并发时序、全部非Main资格、租约故障、取消／替代和平台回归复用同指纹机制证据。没有用SDK预置选择宣称模型自然行为；无新增UI／Android能力，不将其作为本轮新条件。

## 4. 详细场景与执行结果

以下所有独立场景均运行于第1/2节同一产品、隔离环境，执行时间为2026-10-31；完整可复现输入／步骤在 `validation/test_validation_journeys.py`，实际工具回执和SDK请求原件位于下列JSON。每项“预期”均执行前按计划确定，结论没有降低原判据。

**V01。** 意图：整理用户选择而不把助手建议当接受。起点为新Main／空Notebook。通过正式Main Turn写入上述合成原话，取得原生UID；原生Noting child调用create，再以同UID和完整新描述update blocker，show后finish。预期同Task只有一组且描述共同覆盖，成功工具回执／工作show／Main读一致。实际Main得到单槽`[用户明确周日方案只是助手建议，仍选择周六室内以避开周日交通管制。]`和对应UID；未制造第二组，Snapshot成功。通过；证据 `V01-V02.json`，含两轮所有请求。描述语义由脚本选定并人工对原话核对，不证明模型自主概括。

**V02。** 意图：纠正主要原因并保留先前说法轨迹。起点为V01提交后，真实Main新Turn加入“志愿者考试为主、交通次要、活动未完成”；新Task实改同entry并提交。预期追加第二组，旧Task／旧Snapshot／不可变版本不改，重开DB仍一致。实际entry身份保持，描述数组为原组加`用户纠正主要限制为志愿者周日考试，交通管制只是次要因素；活动仍未完成。`；两UID槽及时间槽对齐，旧time不变，旧raw前缀与旧Snapshot逐项相等，重开SessionDB读回成功。通过；证据 `V01-V02.json`。

**V03。** 意图：读取既有无描述资料并继续维护。准备为新隔离DB内合法旧形状INSERT-only JSON，唯一缺字段为provenance_descriptions。Main show得到`[null]`，raw不回写；Noting原样update返回success/changed=false，缺描述实改返回source_description错误且工作态／raw不变；合法实改后数组为`[null,新描述]`。预期未知保持明确、不猜补、不为补描述续期，实际符合；后续Main完整可读。通过；证据 `V03-V04.json`。旧数据准备不是对生产转换。

**V04。** 意图：候选沿现行源条目追溯并守权限。在V03工作态创建refs Candidate与独立direct Candidate；refs数组为[]，direct具有自身一句话；尝试混传direct+refs被拒且版本／工作态不变。更新源条目后working show和提交后Main show包含当前源说明，refs仍指稳定entry。Main create、Noting scheduler均真实dispatch返回scope_denied。预期来源二选一、Main只读、Noting不获额外能力，实际符合。通过；证据 `V03-V04.json`；所有目标、direct→refs限制及继承反证补充复用D1 Candidate62项／权限86项。

**V05。** 意图：压缩后按此前已发原话更正原因。先真实Main写“主因为志愿者周日考试、不能写交通管制”，建立相关组；原生DB压缩、现行Note发布使Main获得真实Framework（核外层含当前Conversation Ref）。用户要求纠正后SDK受控调用该ref+真实UID的Read，正式History成功回传完整原话，再输出一致的活动原因。预期有相关组优先Read、不宽泛猜关键词，实际此受控合法序列可走通、一次Read已足够、没有额外历史展开。通过；证据 `V05-V07.json`。不推导模型会自发选此顺序。

**V06。** 意图：已有充分可见原文时直接总结；即时算术直接回答。继V05真实工具原文已在传入的当前history中，两个Main Turn分别直接总结与回答49；各一SDK请求，无History调用。预期不强制重复读取或无关检索，实际符合。通过；证据 `V05-V07.json`。SDK直接回答属于受控外部回复，不把无调用当自然行为统计。

**V07。** 意图：无索引仍可定位原文，缺依据／失败时给可理解未知。独立Conversation无Notebook索引，DB有“口令松树、不能枫树”；正式Meta→Search→精确Read后可正确回答。随后失效UID Read返回失败，Search“午餐菜单”成功但无所需依据，最终明确菜单未知。最后令History backing-store依赖抛OSError，正式Search封套success=false，最终明确读取失败、旧菜单未知。预期区分缺失与工具故障且不猜补，实际工具结果和用户输出均符合。通过；证据 `V05-V07.json`中meta/search/found-read=true、missing-read=false、empty-search=true、failed-search=false及完整请求／输出。

**V08。** 意图：旧持久Prompt在正常恢复边界采用定稿。正式builder请求含逐字B英文与仓库外合成项目context；仅在合成Profile持久root及父缓存设置旧口径，使用现有history启动正常下一Turn，再warm一次。预期新版B恰好一次、旧“insufficient”口径消失、工具原样、旧历史不改、恢复cache break一次。实际全部相等检查通过，记录唯一toolset_change；warm root相同。通过；证据 `V08.json`。完整skills/MEMORY/USER/footer、A英文和Noting拒绝／续Turn父前缀逐字投递另复用D2同指纹8项实际SDK请求，不重跑。

**V09。** 意图：明确请求一次整理并得到可验证完成结果。新target Profile合成m1/m2和长历史，request=`validation-community-create-1`；state先not_found，start返回操作；控制外部首回复暂缓，state显示running、committed=false。释放回复后真实child执行create与finish，最终completed/committed=true，child=`noting_f9822bc522fd4a46`、Snapshot=`snap_22e98df9583641498c248f13e3e770b5`。Main show读到双UID同组及“用户选周六／助手周日未被接受”的描述。预期只从真实child提交见证报告成功，实际符合。通过；证据 `V09-V10-V12.json`，不是排队当提交。

**V10。** 意图：重试不重复执行，owner隔离可理解。V09 running时重复start返回同child；完成后重复返回相同结果，总SDK仅create/finish两次。新request在同anchor返回skipped/same_anchor_admitted且无child、committed=false；复制model_config的显式branch state为not_found，foreign Profile返回错误。随后原生compression结束父Session并创建其后继，重复原request仍同operation／child／Snapshot，stored_session_id变为rotated-parent，无新SDK。预期幂等可跨物理轮转但不跨显式branch/Profile，实际符合。通过；证据 `V09-V10-V12.json`。

**V11。** 意图：忙时、无效输入和关闭状态不能隐式起整理。先真实取得Main lease，start返回4010并保留原owner；真实compression lock同样4010；空request返回4002；未知state仍not_found；local关闭后新request返回skipped/local_disabled。SDK调用始终0、原config字节不变。预期错误明确、不抢租约、不更改参与／Idle，实际符合。通过；证据 `V11.json`。全局关闭、能力不足、并发准备、租约失效、取消／替代、存储故障由同SHA D3完整34项补充，未再跑大型故障套。

**V12。** 意图：手动整理完成但不额外Compact，按现行边界一次发布Note。V09 manual提交后父历史数不变、check_note_delivery=false、config不变。继而显式走真实原生 `_compress_context`（仅摘要外部依赖受控）成功，数据库只有一条该Snapshot Note receipt，再查false，父Framework可见描述与来源。预期手动任务不自行压缩／即时强发Note，后继压缩沿现有接缝唯一发布，实际符合。通过；证据 `V09-V10-V12.json`。

**V13。** 意图：确认最终上线与所有本仓工作树收尾。当前产品门禁时点未执行实际发布／清理，操作归root；待收正式版本、两服务实际健康、配置／业务／静态保护、两套三库、缓存恢复边界及清树归档/main收据后补核。当前不得据计划判已完成，无产品场景待执行。

**V13发布／清理后实际补核（2026-10-31）：通过。** 本Agent只读现有收据及本地Git，不重跑产品、生产、模型或UI。`release/receipt.json`的phase=verified、target=bf28ab5，完成时间为10:09:58+08；Web实际commit与Gateway code_sha均为该版本，双服务active、gateway running、微信connected，发布前后均无活动工作。逐对象比较确认host/Alex/study各22张保护表行数、列结构及内容SHA完全一致；24份配置指纹、微信绑定、Secretary静态439文件与Dashboard静态67文件完全一致。`postrelease-readonly.json`再次核HTTP健康commit正确、三Profile、目标Notebook可读（来源描述字段可见且内部Task隐藏）、78条排期可读、manual state已注册并只读返回not_found、六HTTP入口资源通过，生产测试模型请求与noting_start均为0。既有Notebook只展示新增字段的兼容投影，不把它解释为旧组已有新描述：`readonly-compat.json`确认Alex190 item、17 Snapshot、204个旧组只读兼容、新描述0、58个更早来源形状原样保持，database_writes=0；16个来源代码／锁指纹与当前产品一致。正常服务重启及既有恢复边界用于采用新版Prompt/Schema，未为证明它额外发模型请求或重写历史。

`backup-retention.json`实际保留20261031 evidence-recovery与force-completion两套，每套host/Alex/study三库均integrity及foreign_keys=ok；删除更旧maintenance-final的三库及WAL/SHM共9文件，运行库和当前同步zip未动。`cleanup-final.json`确认旧5个工作树及本轮工作树已删除，13个本地功能分支清理（10已合、3有等价证明并保bundle），仅main与官方镜像hermes-upstream保留；其它仓库及远端功能分支未触碰。当前本地只读git实证与收据相符：唯一worktree为原目录、main/HEAD/origin_main=9130843，报告修改前clean。旧五树保全目录和先前evidence_verified收据仍在 `.hermes-dev/worktree-retained-20261031/`；本轮原六份独立验收JSON逐SHA完整匹配，环境解释器实体及原stash保持。相对a51到正式bf28的diff只有文档/报告，无产品源码改动，已有产品旅程不复跑。完整计算结果和输入收据SHA保存在 `validation/V13-final-receipt-review.json`。

## 5. 问题、修复与复验

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| ENV-01 | 首命令向canonical runner传独立--basetemp参数 | 解析即退出，未进入测试，first.log | 命令准备错误，已关闭 | 无产品变更；改--basetemp=形式 | run1进入全部场景，最终run2有效 |
| ENV-02 | V08续Turn省略当前显示history | root已更新，但未命中预期恢复计量，breaks=[]；run1.log | 验收调用方式错误，未当产品缺陷 | 专属turn helper传真实parent history | run2全旅程6/0，V08.json唯一break及历史不改 |
| ENV-03 | V12仅在DB追加长历史，未刷新父active | 原生拒绝would_grow／Anchor不在父active，Note为0；run1.log | 合成准备不一致，原生保护正确，已关闭 | 长历史移至manual前合法起点，父active从DB重读 | run2真实压缩成功，V09-V10-V12.json唯一Note |
| FINAL-01 | V13发布／清树事实 | 原产品门禁时点无最终收据；后续verified发布及cleanup-final实际收据已核 | 已关闭，V13通过，原等待时点保留 | 无产品修复；bf28ab5正式发布、9130843本地main | V13-final-receipt-review.json；第4节逐项补核 |

没有发现范围内产品缺陷，没有修改产品源码、规格、门禁、完成条件或测试规则。旧R3同区间Note等12项和catalog review.summary孤立事件为已准确基线复现的独立测试债，本轮未改其语义、未将它们签成全绿。run1失效产物由run2同名JSON覆盖，原失败日志永久保留；有效产物SHA已在环境收据绑定。

## 6. 验收结论与推荐复核

G1/G2：新／旧来源兼容、同／跨Task、Candidate与权限的实际工具／DB／Main链通过。G3/G4：强制回查定稿正确投递，压缩后合法精确Read、可见充分、无索引、缺口与失败的正式用户输入到输出链通过；正常恢复不改历史／工具且记录一次缓存变化。G5：manual RPC到真实child／提交／Main读取、重复查询、隔离、拒绝及后继唯一Note通过。以上12适用产品场景均关闭，**无须产品修复，产品Validation门禁通过，可按既有授权发布。** E12不要求新增真实模型，不以SDK脚本代表自然模型决策。

G6／V13待实际发布和清树收据补核；无需等清树才发布，也不能据当前报告宣称V13完成。推荐复核入口为运维RPC start→state真实committed/snapshot→Main notebook_show完整读回来源描述；生产能力上线不代表授权实际补跑生产Noting，本轮不建议用户为验收额外触发。主要原件为ignored `validation/summary.json`及六个V*.json、`run2.log`。发布／最终目标结束由主会话结合后续实际收据判定。


**第6节最终补充（2026-10-31）：** G6/V13实际发布、数据保护、只读可用性、两套三库及工作树收尾均已补核通过，原“待收据”属于发布前历史时点。当前V01–V13全部通过，无失败、未执行或阻断；Validation门禁最终关闭。上线版本bf28ab5与已验a51产品相同，原目录唯一main及证据保全已核。保留E12和受控SDK边界，仍不声称自然模型服从率、真实微信送达或新增生产manual整理已验；本轮未授权这些外发/调用，也无新增此类条件。最终交付判定由主会话汇总两门禁与已核实际事实完成。
