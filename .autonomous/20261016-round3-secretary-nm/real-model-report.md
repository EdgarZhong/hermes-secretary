# Round3 Development 真实 DeepSeek 运行报告

状态：Development 真实运行与已授权定向复测完成，停止写入并释放 round3，待主会话亲自 review。六组场景及 F08/F09/F11/F12/F13 真实补证已记录。本文不是独立 Verification／Validation，不填写 validation.md，不宣称整轮验收通过。

## 1. 条款与运行边界

依据冻结 `d19018a7ba3e38ae01f76aa57821b55cbc15ff58` 的白板七类型、N/P/D，07 §3、§4.5、§6.3、§7、§8.1–2、§8.11–14、§9、§11，继承旧02/04的实际Main来源、原生压缩、完整多模态父前缀、持久child、五Turn、单Idle deadline与真实成功响应ACK。执行计划为 c10-runtime-report.md §7，主会话明确 START 后实施。

唯一真实产品／模型运行 owner 为本 Agent。所有产品状态、配置、数据库和合成 MEMORY/USER 均在 `/Users/edgar/code/hermes-secretary/.hermes-dev/round3-runtime/profiles/round3`。只用原生 DeepSeek `custom/chat_completions`，`deepseek-flash`，`https://api.deepseek.com`；未启用 AppServer、Proxy、个人 Provider、真实 NM 或旧 Dashboard。凭据只由既有 L0 wrapper 从获授权本地环境读入子进程内存，没有输出或复制。

## 2. 实际变更与版本

tracked 仅新增本报告；没有改 production／tests、stage、commit、分支或规则。ignored 驱动与证据统一在 `.hermes-dev/round3-local-20261017-l0/real-model/`（下文简称 E）。`driver.py` 只发正式 stdio JSON-RPC并记录原始事件；SQLite 连接 `mode=ro`。`client.py` 是正式 RPC 客户端辅助，没有替代loop、模型、storage、scheduler或伪造usage／receipt。

初始生产 SHA：`f304b42bbd6c45a62d1fded490f005bde019b23e`。官方 PM `.venv` Python 3.14.7，无安装依赖／改锁。版本按实际启动分开，修复不回写为旧运行已通过：

| 阶段 | 实际启动 SHA／manifest | 适用证据 |
|---|---|---|
| 初始 CLI／Gateway generations1–2 | f304b42bbd6c45a62d1fded490f005bde019b23e；E/run-manifest.json | 七类型、否决/纠正、受限真实USER成功写入与候选归档（来源结算失败，见V23）、assistant尾图片5请求、History、Proposal、四入口/Idle时序；同时保留F08/F09/F11/F12真实失败 |
| 第一修复 Gateway generation3 | eff3235f6bc1ee53b5d29b5210ad397024959df6；E/repair-run-manifest.json | F08 streaming图片、F08b cold、F09/Scheduler注册/两deferred carrier与ACK、操作控制、闲置instant、busy降pending和下一ACK、global Noting off实际Scheduler、F11成功边界及下一Force、F13人类/model分界 |
| 最终微修 Gateway generation4及受控probe | f66a8f80b4bab39b0a785a552019c91a6e9becba；E/f12-run-manifest.json | F12首user尾7请求、两个真实同child跨5Turn链、Scheduler重启持久性和清理；不重跑前述已有效链 |

两次修复重启均先确认旧 child 全部结束，正规关闭原生host再启动；manifest保留wrapper与配置SHA256。两次受控probe也在f66a8运行，沿同一wrapper／round3／原生DeepSeek，不连接真实NM。

原始配置备份 E/initial-config.yaml。为真实触发而合法调整过 context_length 262144→130000、native compression threshold 196608→75000、protect_first_n=1/protect_last_n=4、target_ratio=.10。Idle 初始关闭，独立样本启用 delay=12秒、threshold_tokens=32000；样本结束恢复关闭。Proposal 阈值曾临时2000，取证后恢复12000。没有改模型路由或 provider。配置文件没有凭据。

## 3. 正式路径与六组实际结果

| 场景 | 实际入口与结果 | 主要证据 |
|---|---|---|
| CLI／TUI与开关 | 原生CLI oneshot真实回复；TUI session.create→prompt.submit。全关、仅Noting、仅Scheduler均真实回复，History均在请求；Role／Scheduler指导各自独立。global Noting off时native compress正常no-op、零新admission；修复后global Noting off也真实创建/list Scheduler，local off投递完整通过 | E/cli-smoke.log；sessions.json；switch-request-evidence.json；*-response.json；global-off-native-compress.json；scheduler-global-off-* |
| 七类型、否决、修正 | 第一任务13条覆盖matter/action/situation/implicit_gap/question/insight/decision及Candidate。青鹭周五纠正周六、未承诺今晚交付；委派owner小林；用户问题仍open、认识只是猜测；否决AI整套建议未变承诺。第二任务探访完成、青鹭测试仍pending、已回答缺口归档、限期决定expired | snapshot-first.json／snapshot-first-entries.json；notebook-after-settlement.json；noting-working-show.json |
| 四工具与多模态前缀 | 原生image.attach合成64×64左蓝右红PNG，DeepSeek真实接受并识色。初始干净child同一Turn5请求精确parity；F08修复busy图片6请求精确parity；F12首user尾7请求精确parity。实际自然任务调用全部四工具和standalone finish；真实同child跨5Turn每请求也精确parity，见下文受控边界 | multimodal-prefix-parity.json；f08-repair-prefix-evidence.json；f12-user-tail-prefix-repair-evidence.json；native-continuation*-cross-turn-prefix-evidence.json；child-actual-tool-counts.json；semantic-second-tool-trace.json |
| 跨压缩History与Proposal | 手动原生成功17→6后，Main用History读最早真实消息并区分图像观察和用户原话；/propose-persistence返回send后客户端转发原生directive，Main生成来源和版本明确草案；推迟不作批准。后续受限memory真实成功、候选13归档；来源6完整保留构成V23失败；第二经验未定目标未执行 | proposal-first-response.json；correction-response.json；memory-before/manifest.json；memory-after.json；framework-177.txt；rpc.jsonl |
| 四入口与Idle | 手动28→15父native先于child完成；Force同conversation_start一次admission，换anchor/child完成不释放。auto真实preflight9→3提交。Idle23,296<32k截止零任务；36,412>32k、两新Turn取消重臂、due+约8ms唯一idle admission，父8→6成功先child约21秒。F11修后成功边界登记compaction:20261017_012517_02e0f2:285，下一Force admission8使用新区间，后续换anchor仍只一次 | force-*-response.json；auto-pressure-*.json；idle-*-response/state.json；idle-final-evidence.json；native-boundary-interval-miss.json；f11-repair-boundary-force-evidence.json；f11-refill-*-state.json |
| Scheduler／重启 | 修复前真实未登记保留；修复后原Main工具桥实际create/list，pause/resume/update/delete；两deferred自然到期→一carrier→真实响应双ACK；idle instant自然唤醒；busy instant到期只pending、不启动第二Turn→下一Main实际携带ACK。重启前后registry逐项完全相等；合成未来排期最后实际delete清理 | scheduler-missing-catalog.json；scheduler-register-two-response.json；scheduler-deferred-*.json；scheduler-control-idle-register-response.json；scheduler-idle-wake-events.json；scheduler-busy-lifecycle-evidence.json；scheduler-restart-*.json；scheduler-cleanup-*-response.json |

主要Conversation：semantic `conv_8ed507015f4544f4820892042f67fc8d`；multimodal `conv_6a9caac1efcf4bc89f118a38fc05c3a1`；pressure `conv_2c67c04d65074b719f2df0b78e8dfb34`；Idle `conv_0688c7da4f274982b5860cb299aa8d78`。物理Session和runtime ID见 E/sessions.json。所有事实、人物、项目和图片均合成。

真实memory例外经主会话明确授权：先wrapper内get_hermes_home核实round3，备份确认原MEMORY/USER均不存在；只通过原生memory `action:add,target:user`写获批具体75字符合成经验，返回success、entry_count1，实际文件是round3/memories/USER.md。没有写真实profile、NM、Skill或其它目标。第二部分没有目标和授权，**未执行／未结算**，不是发生了写失败。Noting根据可见真实tool成功结果归档候选13，但来源6 v34仍完整保留已写经验，仅加处理注记，未给新增/责任/其他候选等保留理由，构成V23来源结算失败；新未定目标经验保留为独立来源35，不能解释来源6的保留，未伪造目标。

完整Snapshot Framework分别保存在 E/framework-58.txt、81、106、177；177含完整正文与同条末尾PERSISTENCE PROPOSAL REQUEST。Snapshot payload存immutable version ID；查现行应hydrate对应版本并过滤archived。E/snapshot-second-entries.json是早期错误选旧版本的粗略导出，不作为当前视图证据；正式/notebook与working show已证归档无复活。

## 4. 验证、usage与协议证据边界

产品命令：`.venv/bin/python .hermes-dev/round3-local-20261017-l0/run-native.py .venv/bin/python -m hermes_cli.main chat --oneshot ...`；TUI driver启动同wrapper→`/usr/bin/env HERMES_DUMP_REQUESTS=1 .venv/bin/python -u -m tui_gateway.entry`。实际输入、RPC、事件、返回和时刻完整留 E/rpc.jsonl、operations.jsonl；原生请求dump在round3/sessions。只解析request.body；不输出headers，不把parsed JSON相等冒称HTTP wire字节相等。

API usage/cache原生日志原值摘录 E/api-usage-cache-original.log（最终继续补全）。例：压力Main in=66421/out=2/cache=53632/66421；下一Main in=66468/out=97/cache=66304/66468；auto后in=78020/out=2/cache=1280/78020。Idle高占用Main in=36290/out=38/cache=23424/36290，后续in=36370/out=3/cache=36224/36370、in=36412/out=3/cache=36224/36412。UI usage字段含累计值，独立逐请求值以上述原生API log为准；不由缓存百分比推导收益或伪造provider原始usage字段。

初始六个真实child均completed：ce69503de8ce4006、26817cf12a5e4026、76ad73e3c79d4062、5337438f5bbf4dda、5b258c6d00644ef4、6a2da0dba87945bb；修复后自然链另有97a0fa65303048b9、f6e081b44222476c、4816bb9ee87e49c3正常completed，两probe为76a6c1bdde474dd1、64f82b04be0f427f forced completed，共11个持久child。真实工具错误保留：维护字段错误后按guidance修正；无目标Candidate创建被拒后未代填目标；Force来源未就绪后真实History补读；probe桥工具误用按权限失败。没有把错误工具返回称为成功。

早期客户端wait错误曾把并发另会话完成误作摘要、或等待超时；已修为按event.params.session_id匹配。原始RPC未改变，最终结论只取匹配sid的原始事件／durable行，不把该客户端观测错误计为产品失败。

## 5. 真实缺陷、未完成与限制

| 缺陷 | 最小真实反证 | 当前处置 |
|---|---|---|
| R3-F08／F08b | busy时/noting feedback后durable输入仍在，Active后续请求丢实际输入／图片；cold model历史先repair后过滤human_only会隐藏Main回复 | eff3235复测通过：观察到真实streaming后送usage/off/notebook/on，下一Main及child首后6请求完整原输入/图/root/tools；冷恢复下一实际请求保留独特Main回复标记，4条human_only正文不入请求。原反证concurrent-slash-active-observation.json，新证f08-repair-*、f08b-cold-* |
| R3-F09 | scheduler已开、localNoting关，Main真实tool_describe/search均找不到scheduler，Schedule表空 | eff3235原对话实际bridge登记、list、投递与ACK通过；global Noting off独立创建也实际落库。修前未登记状态保留，没有Cron替代 |
| R3-F11 | 原生成功auto commit9→3，旧assistant row197 UID被新summary row200沿用，_compressed_summary 0→1，Noting interval仍conversation_start | eff3235原Conversation真实压缩新边界登记为compaction:20261017_012517_02e0f2:285；下一Force admission8使用新区间，后续换anchor仍只有该一次；f11-repair-boundary-force-evidence.json |
| R3-F12 | 父首Turn末尾user触发Force，[system,user]父请求在child变成同user附加task；root/tools相同，父字符串是前缀但完整message不等 | f66a8复测通过：真实首user图片Force父2消息与child前2逐项相等，task独立第3user；7实际请求完整prefix/root/tools/image均相等。真实跨Turn两probe全部31请求也相等。旧反证force-user-tail-prefix-observation.json，新证f12-user-tail-prefix-repair-evidence.json／native-continuation*-cross-turn-prefix-evidence.json |
| R3-F13 | 人类/notebook不应显示内部Snapshot/anchor header，模型show/Framework须保留完整状态 | eff3235真实slash无两header；实际Main bridge notebook_show仍有Snapshot/coverage及完整正文，读取原有工作状态正确；f13-human-notebook.json、f13-model-show-response.json；既有完整Framework正证保留 |

overflow、混批、提交竞争等确定性机制复用已有C5/C7/C9有效机制证据，没有用模型随机性重造这些竞态。**初始干净图片的五次provider请求均在同一个原生Turn工具循环内，不是跨Turn续跑。** 初始静态核对continuation出现0次的历史观察保留E/native-continuation-coverage.json，随后按主会话授权补如下真实机制证据，不能用后来的补证改写该初始观察。

跨Turn probe构造边界：沿原生TUI `_make_agent` 构造真实Main／原生AIAgent.run_conversation接收合成图片，使用现有Noting gate/手动准入函数及正式 `run_noting_task` 持久runner。仅task Prompt受控；没有新loop、伪造provider返回、修改tool_choice/provider路由或写admission表。不是CLI用户自然语义场景。

| 真实probe | 原生Turn／实际请求／continuation | 真实结束与结果 |
|---|---|---|
| admission10，child76a6c1bdde474dd1 | 5条原生turn_context调用日志＋5条原生Turn结束日志；18个实际provider请求，后续continuation块最多4；每请求冻结3消息/root/tools/image1全相等，parent已发送前缀及最后真实assistant内容也相等 | 模型没有遵守首纯文本预期，尝试继承桥工具，实际被拒；5Turn后forced，Snapshot snap_d2e10c622fde45b8bbc1faf85c3d8b46合法提交／pointer切换；资源关闭 |
| admission11，child64f82b04be0f427f | 保留完整DEFAULT Noting任务后追加同受控例外；仍5条原生Turn调用/结束日志；13个实际请求，continuation最多4；全部冻结前缀/root/tools/image1相等 | 同一模型选择边界，未正常finish；既有5Turn forced提交合法Snapshot，真实termination/receipt见native-continuation2-probe-result.json；资源关闭 |

两次probe均自然在原预算内结束，没有第三次随机尝试。它们证明同child跨原生Turn、完整实际continuation、完整多模态前缀稳定及有界兜底。没有取得特定“首纯文本、第二正常finish”的受控预期形态，该形态本身不是冻结规格的额外完成条件。正常standalone finish沿此前多个正式自然child链证明；桥工具失败不算成功，也没有修改产品放行父bridge。强制审计、Snapshot及已结束child/source Session行见E/final-product-state-before-stop.json；连接close原生日志、probe进程退出及最终零运行child共同构成资源释放证据。

真实partial persistence failure没有人为制造；本次第二部分未执行，只证明USER真实写入、候选13归档及独立未批准来源35保留；来源6退出/精简未落实，不能宣称成功范围完整结算，也不是同candidate多目标部分失败。跨平台、真实NM、云部署均不属本次运行证据。

## 6. 接口影响与退出状态

没有产品接口变更。正式RPC包括session.create/resume、prompt.submit、session.compress、slash.exec、image.attach；`/propose-persistence`的type=send由客户端继续送入prompt.submit，未替换业务loop。数据库只读查询用于核对事件与持久事实，没有手工插表、改状态、设admission或伪造时间／receipt。

最终Gateway generation4（wrapper PID66980）正规关闭，实际returncode=0；驱动PID16204在原生已退出后SIGINT结束，两个probe均已正常进程退出。E/process-release-evidence.json确认本Agent driver/probe/TUI产品进程均为0，旧Dashboard仍存在，未停止他人服务。11个child全结束，没有未来enabled pending排期；仅本轮两个未来合成排期经实际Scheduler delete清理，已完成发生保留审计。

配置逐字恢复E/initial-config.yaml，SHA256 `ca8a60eb5cf213e74029452c7aedd1e8632e129031bc3ef6f1a5997aea6afc1e`，原生model pin262144。获批的75字符合成USER经验留在round3/memories/USER.md，与不存在的原文件备份manifest和最终内容/hash一并保留；没有删除归档证据或接触真实profile。E/state-before-cleanup.sqlite3与state-final.sqlite3均由只读源SQLite backup取得，不改源库。退出和恢复事实见E/handoff-runtime-stop.json。**round3现已释放给主会话安排C11-P接力，本Agent不再启动或写运行状态。**

## 7. 后续动作

主会话review本报告和ignored证据后安排C11-P独占round3。公开模型剩余清单已完成，无新增待改生产缺陷；真实模型输出仍有普通模型局限：global-off创建结果的额外自然语言把跨UTC日期误说为“早于当前”，但实际canonical时间／registry为真实未来07:13，未影响登记；已保留原回复，不把这句解释当metadata事实。

最终回归静态清单按主会话要求已转reuse cache_parity11与thinking-only sanitizer20：136全文件＋TUI server84函数过滤、已有有效证据对照见regression-plan.md及ignored final-regression-prep。本Agent没有运行大型回归或固定10类检查；等待Verification派出后主会话另定SHA／owner／start。真实NM、云部署、跨平台和真实多目标persistence failure仍是明确边界，不冒称已验证。


## V23 / R3-F16：来源结算首样本失败与调查里程碑（2026-10-17）

**状态：OPEN；只完成调查，未改Prompt、未启动新模型。** Astra V23及主会话已核对：原f304b42样本的USER真实成功与Candidate13归档成立，但source6 v6→v34仅增加processing_note，description逐字未变，且无新增内容、未完责任或其他active候选/关系需要它。source35 v36为另一条独立未批准经验，不是6的保留理由。上述历史范围表及结算说明已纠正，原始request/tool/Snapshot失败事实均保留；不得继续把本样本称为来源完整结算通过。

依据白板L2与第09章E1、07§8.11 Step4（当前1331节标题、1349动作段；1358来源保留直到结算；1363归档前修引用）；02§5.6只涉及时间投影。9个原Noting请求均注入逐字DEFAULT，与原f304b42源码及冻结07相等；完整父28消息/tools一致。实际批准、memory成功和独立新增内容在父上下文和child正式History Read返回中均可见。未发现相反的明确任务Prompt或配置例外。父Main泛述“source entries remain in place”是可能误导线索，child明确以追加任务为准，不能据此豁免来源结算。

工具链：child尝试update6时混入只读candidate_refs而失败；archive13成功；随后合法重试仅加processing_note成功得到v34；finish明确称“来源6保留”，真实提交Snapshot `snap_52fa429915ab45db8845a90c7a9184e3`。因此不是提交丢失或资料缺口，而是模型把“候选归档＋来源加已保存注记”当成已完成结算。现行Step4没有展开source archive/update具体分支，应按已冻结语义提出工程Prompt细化，不能硬编码按memory返回删源。

集中根因、证据UID、版本/引用、完整英文Step4替换提案及待START真实方案见ignored `.hermes-dev/round3-local-20261017-l0/v23/investigation-report.md`；逐请求及只读Snapshot审计见同目录 `investigation.json`；替换提案为 `proposed-step4.txt`。仅提案、尚未注入；需要root与Astra评审及明确修复SHA/运行START后，才通过同一正式Main批准→真实成功→合法Noting补证，并同时观察成功覆盖移除/精简和未交付新增/责任/其他候选依赖保护。不重复随机采样、不伪造第二部分写失败，不动真实NM、其它profile、生产/tests或最终回归。


### V23 实施交回：仅Step4文本同步（尚未模型START）

主会话采纳、原Astra评审认可完整Step4提案后，按明确白名单实施。工程细化仍为CLAUDE顶部登记的Agent自主细化／待用户追认，不冒称用户亲选措辞。实施基准HEAD `ac7032be96114016bc26d1fa8825c4ba04b925f4`；本包未stage/commit，待主会话review提交后另给真实运行SHA/START。首样本失败与调查原证据均保留，V23仍OPEN。

准确变更仅两行：07 §8.11 Step4为第1349行；`secretary/noting_prompts.py` DEFAULT对应第18行。均逐字采用`proposed-step4.txt`完整第4段，不含文件前两行说明；英文段落SHA256 `42eb85bb48f70f1a793385de48e922792943f8a06b8c9bab67f25f76c47ba79c`，评审提案文件SHA256 `e0d68140116a3857b221ca727f38e68ae64f922293038097f04c29c21f0ac4de`。07完整文件新SHA256 `6aa214963a2d7f806fa3d006f1b9e5a2185b4992c1b8d1246a51590fe630fc8d`；noting_prompts完整文件 `669e109185556b82fcc7f688078b9875827b00f38e1ca74825f3e83097337ace`。

只做静态文本/AST核对：12个相关英文常量均逐字出现在07，其余11常量内容与hash不变；DEFAULT及07段落外字节不变。准确before/after/hash/行号在ignored `v23/implementation-manifest.json`，局部差异为`step4-implementation.patch`（SHA256 `d6fd0cc567a4cc5335c4b1c3401414d997f55f93f906a546003259270b571e7c`）。没有runtime、Schema、权限、commit gate、tests或规则改动；未运行镜像测试、大组、check、实际产品或模型。archive/update/引用约束复用既有机制证据，不能把文本核对当成模型语义结算通过。

一次性后续输入计划在ignored `v23/scenario-input-plan.json`：原正式Conversation resume后仅一次/noting恢复首失败，不重复USER写入；另建一个正式Main链，合成事实→一次合法Noting形成现行来源→具体草稿→明确逐字USER批准→真实memory结果→新增未批准事实→一次合法Noting→正式/notebook与只读版本审计。输入没有测试专用Task/工具动作指令，不改DEFAULT以外任何Prompt；包含全覆盖个人经验、后来新增范围、资料册未完责任和待审Skill用途。按实际模型条目结构判断覆盖；若自然拆条使同entry partial未出现，明确缺口，不再抽样挑成功。任何真实失败/未知原样报告，不编造第二目标失败、不盲目重试。所有运行仍等待root review、提交SHA及明确START。


### V23 首次真实恢复：正式联合入口受F17阻断（生产d033c505，已恢复并释放round3）

主会话明确START的生产SHA为`d033c5057df419fb7d7122cba3085105dd13d89e`；启动时HEAD为`fd5ec4614326940d13a315f3311fe60f6a2952ba`，两者仅baseline/CLAUDE文档差异，生产相同。个人`5a2fe444042c1d19e29ff9e7a781c6eb4a348f70`未加载。wrapper原生DeepSeek custom/chat_completions，profile及get_hermes_home均为固定round3。配置SHA256仍为`ca8a60eb5cf213e74029452c7aedd1e8632e129031bc3ef6f1a5997aea6afc1e`，Noting/Scheduler配置缺省按产品默认；Idle未启用。配置、USER和空plugins目录已备份；未安装插件、未接NM、未接AppServer/Proxy或旧Dashboard。

本次先纠正计划触发错误：裸/noting只是Usage，实际只用正式`session.compress`手动联合入口；/noting on|off仍仅控制参与。原链以`session.resume`恢复原stored ID，原生返回runtime `5a70c314`，用一条获批普通确认消息推进Main，未重放USER写入。Main真实完成后用正式/notebook保存整理前视图，再只调用一次session.compress。原生压缩成功`26→22`消息、removed4，~52,829→47,329 tokens，noop/aborted/refused_would_grow/fallback均false。

**真实机制失败：** manual admission12已接纳，anchor为`37c3c8b6bbd04ed88797ff102c3f69b5`，children.status=failed，child_session_id=null。worker在`noting_child.py:534`第二次freeze，经:155报`The frozen Anchor is not present in the Parent's active context`，发生于child构造前，零Noting模型请求。只读原行是row502 assistant、display_metadata=`{"human_only":true}`、observed0，正是紧邻compress前/notebook产生的反馈；它不是Main正常确认回复（row500 UID`320004f07c3d4d5b8d64487b2feecc16`）。同步freeze先按durable Anchor截断，再经正式model_visible_messages移除该human_only条目，worker对这份已投影prefix再按同UID定位而失败。未独立dump同步内存prefix，因而该投影原因是由实际row metadata、正式代码及trace共同证实的时序，不冒称抓到了完整独立prefix对象。精确metadata与traceback已交主会话和原local owner，主会话按F17处理。

故本次没有执行新Step4模型语义，也没有新增F16来源结算成功证据。原source6仍为v34且未归档，pointer前后同为`snap_52fa429915ab45db8845a90c7a9184e3`；首样本FAIL继续保留。收到主会话停止指令后没有重触发原链、没有新Conversation、新批准、新USER写入或随机抽样。新链全部未运行，不宣称未交付/责任/其他候选保护已新增覆盖。

正式路径证据在ignored `v23/runtime/`：原始RPC/operations、recovery-confirmation、recovery-notebook-before、recovery-compress完整response、before/after Notebook版本及只读state备份、admission12与Anchor metadata、traceback、唯一新parent request.body及hash、usage-raw-observations和原始API/cache日志。Main实际API原值in47202/out34/total47236/cache46848/47202；原生summary有一次dispatch日志，未暴露独立aux逐call usage/cache原值，不用Main统计冒充。没有Noting请求可供新prefix或新Prompt对比。所有headers/key/root正文均未打印，body仅本地ignored。

**退出与恢复：** 原生host已正常stop，wrapper returncode0；随后自有客户端driver以明确SIGINT退出130（不冒称0），两个自有PID均不在。turn leases0、running children0。配置原bytes已恢复，USER仍原75字符合成经验且hash`8f4eda659573177d245d2c1ca01f60664deefa1a3833ce8df4bfb1f519708ed4`，MEMORY/插件状态与备份一致，零新增USER正文。证据见handoff-host-stop-and-restore.json及process-release.json。round3已明确释放，不能在旧活runtime载入后续代码。

本包只新增ignored运行驱动/证据与本报告，未改生产/规格/tests/core docs，未stage/commit或重跑最终回归。后续由root组织F17机制修复及定向证据；新提交review后，再明确分配固定SHA/START和剩余运行预算。当前F16仍OPEN、首次恢复因正式host冻结机制失败而阻断，不能据Prompt静态一致性关闭。
