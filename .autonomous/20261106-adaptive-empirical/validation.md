# Validation：20261106-adaptive-empirical

## 1. 结果概览

验收者：独立validation_empirical（原独立验收者接续，无派生）；本轮20261106-adaptive-empirical。冻结依据24fe50ffcf588e9846b1902b0ad0f6cf62520924，snapshot-index.md/baseline.txt与原U1–U3/R1–R10、继承及E/07合同不变。**当前产品3e08ea39ccf1a1ea2814f2a3e7fb710f049c52e4的Validation通过：V01–V12全部适用场景通过，0失败、0未执行、0阻塞。** root已亲读接收全新r4 Verification26符合/0违规/0不足后才进入续验；续验计划已在§4先落盘并经root完整过目，再运行原取消输入的公开CLI。

当前结论来自原真实入口完整操作、逐场景版本/支持集适用性核查及原失败取消链路在当前版本的实际复验；不是把f7的11个通过直接重命名。G18原错误已实际关闭；G19的实际等待修正及对既有真实回放的无影响范围已核，原等待数值错误不被复用。六节报告及原场景预期保持，数值负结果和条件限制全部保留。最终目标交付判定由主会话负责，禁止上线继续有效。

历史：f7aecf8当时确为11通过/V10因G18失败，门禁开放；完整原文逐字保存在ignored validation/validation-f7-original.md，SHA256 fe0daf294e490eb03669b4bdc2d245c53c171e98e6581a27606f854fec20e742，不能据当前通过改写历史。下文原场景详细结果明确标为f7，当前逐项结论见§3及§4续验表。

## 2. 环境与准备

当前续验仍使用同一本地macOS-26.7-arm64与官方PM .venv Python3.14.7，产品HEAD固定3e08，公开入口scripts/adaptive_empirical_replay.py run，原cancel-input.json/原命令参数仅output改为validation/final/cancel-final.json。输入SHA5915218d3679bb032de7f30ff644c7fbbdb527b70b8a99d66b6d7b9fc7b436e9；实际CLI墙钟22.153秒，非单次决策性能。HERMES_HOME/runtime仍隔离validation/；新证据仅validation/final/，原f7/根g18/原输入未覆盖。原43样本隔离库以SessionDB(read_only=True)重开；全表语义与原拒绝后快照逐值相同。

当前全部75份受审源与3e08提交树匹配；相对v11只policy（G17）、Replay（G18）、rollout（G19）三源差异，相对f7产品仅Replay/rollout。导入、准备、采集、DB、模型合同、原生owner依赖未变。G19的21报告/43保存路径/2578重叠决定支持集、可知时间、来源及裁剪证明逐项核SHA并独立重查候选origin；不是2578独立统计样本。相应31独立/101相关及G18的33机制证据按当前源码适用性复用，不重跑大型套件。

以下保留首轮准备及其环境问题的原事实，供复现来源与历史审计：

实际环境macOS-26.7-arm64（environment.json记录原始platform）、官方PM .venv Python3.14.7；保持当前产品HEAD及原9数据SHA只读。所有新证据、派生输入、临时脚本与隔离Profile/DB放ignored .hermes-dev/adaptive-empirical-20261106/validation/。HERMES_HOME/HERMES_RUNTIME_DIR显式指向此隔离目录；不启动宿主/模型/真实整理。真实CLI离线模拟符合本轮禁止上线及无需模型合同；真实网络、UI和生产效果不在范围。

准备输入：既有replay-input-final.json、input-manifest.json、maintenance-components-normalized.json、experience-cases.json与inputs/9份冻结原件。先记录SHA、版本、Python/platform、dirty清单；CLI prepare重新生成到validation/prepared.json，比较固定预期/来源及包语义，不覆盖旧文件。时间标签与失败/删失/费用负结果原样保留。最初按交接使用normalized包prepare因缺censored失败；root确认prepare应使用本轮既有maintenance-components.json并授权只读，其SHA0f6f606f4c52721200176c756d48f86d233512e2b0c53cc2c27aef43d272f2d7与原包组件来源一致。重试生成prepared.json与原replay-input-final.json逐字段完全相同。此为输入说明失配，原prepare.stderr/command保留，未修改产品。实际一次base请求覆盖九段（127.189秒），连续旅程87.104秒；机械失败24.347秒、raw coverage67.076秒、无维护经验22.157秒，最多3并行。另串行运行声明Stop补充（cancel.command.json记录耗时）；整批不是单次决策延迟。导入仅使用自建validation/profile-import-v4和profile-b隔离default Profile/SessionDB，显式建target/other。准备脚本曾因WITHOUT ROWID、FTS blob序列化、传str而非Path失败，均在实际断言前的验收辅助脚本，未改产品；修正后从新建隔离库完整走通。首次原生SessionDB冷重开补fts_storage_version的观测保存在fresh-db-preparation-*，最终比较起点为已完成原生初始化的库，不把该初始化掩作导入写入，也不把首次冷库误报为成熟Profile预览产品缺陷。测试如必要仅官方runner，机制时序优先复用当前有效同版本证据。

## 3. 用户目标与场景覆盖

| 目标编号及冻结依据 | 完整场景编号 | 场景类型与起点 | 数据/顺序选择依据 | 当前执行结果 |
|---|---|---|---|---|
| G1 真实来源/特征/经验固定；U1/U2、R1/R3/R6 | V01 | 准备主流程：冻结原件→prepare→run输入 | 9原件/43组件，先固定预期而非按结果改 | 通过 |
| G2 连续工作与短暂停顿保护；R2/R7、E1/E4/E7 | V02 | 真实E01/E02/E04独立原截止 | 密集上升、4分钟短返、下午再增长 | 通过 |
| G3 平台不一刀切；R2/R5/R7 | V03 | 真实E03/E05/E09独立原截止 | 中/高存量、读取稀少/后台增长、不同窗口 | 通过 |
| G4 长平台有收益机会真实执行；U2/U3、R4–R7 | V04 | 真实E06/E08独立原截止 | 21h及近两日，禁止全程不维护免责 | 通过 |
| G5 回归与候选自有状态；R5–R7、E1/E4/E6 | V05 | E01新epoch起连续到共同截止，另看E07 | 有此前维护→回归→低存量→后续责任 | 通过 |
| G6 源缺口/失败压力；R3/R4/R6/R7 | V06 | E08 raw_coverage_only；E06 mechanical_failure | 缺口不假无人、真实失败样本不免费成功 | 通过 |
| G7 经济敏感性边界；R3/R5/R6 | V07 | 复用同版本现有费用/缓存/模型/慢尾矩阵 | 已证昂贵边界不重复13矩阵，负数保留 | 通过 |
| G8 显式导入到后续可读；R8、来源/导入合同 | V08 | 原组件包→preview→apply→重读→重复 | 用户公开CLI完整主流程，原件只读 | 通过 |
| G9 导入冲突/归属/隔离；R8、来源/隔离合同 | V09 | 已应用后同ID改内容；错误owner声明；另一ref/Profile | 幂等/原子拒绝，不能跨owner污染 | 通过 |
| G10 无经验/失败取消恢复；R3/R8/R9、E3–E7、07取消 | V10 | 无维护经验派生包CLI；复用正式生命周期受控证据 | 禁固定prior偷渡，原生容量/HB不被抑制；真实取消无历史实例 | 通过：当前原取消链实际复验关闭G18，原f7失败保留 |
| G11 无未来读取/迟到信息；R5/R6、M01/M03 | V11 | 复用已证正式机制及保存决策知时审计 | 无完整真实无后读片段，不虚构历史 | 通过 |
| G12 可重复/资源/不开启原生；R8–R10 | V12 | 重读所有产物/版本、原件SHA与DB实时表核对 | CLI结果可复核，范围外生产从未触碰 | 通过 |

从“拿真实数据→准备→看每阶段策略→看跨阶段责任→改变证据可信度/失败→显式导入→再次读取”枚举完整旅程。九段逐条保留而非代表点代替；E01/E02/E04属保护等价类，E06/E08属机会类但分别验。压力仅选行为不同的缺口与失败，其他费用/缓存/模型边界引用依赖与版本匹配证据；关开/重启/并发沿已有正式时序机制补充；取消另增加声明外部Stop的实际CLI链路，不伪称真实历史或新UI验收。数据行为不确定时按冻结预期判断，不追加盈利容差。

## 4. 详细场景与执行结果

### 续验计划与完成状态：3e08ea39（先于执行登记）

原f7完整报告已逐字保存在ignored validation/validation-f7-original.md，SHA256 `fe0daf294e490eb03669b4bdc2d245c53c171e98e6581a27606f854fec20e742`，原“11通过/V10失败/门禁开放”不改写为当时通过。当前产品3e08ea39ccf1a1ea2814f2a3e7fb710f049c52e4；root已亲读接收全新r4 Verification26符合/0违规/0不足，进入条件成立。已恢复根AGENTS/CLAUDE、两Skill、索引/基线、冻结U/R与继承执行边界、当前plan/verification和原报告。下列为原十二场景的完整续验方法，预期与范围均不改；该计划在新CLI前登记，root完整过目接受后执行，现均已完成。

| 原场景 | 当前预期/完整结果维持 | 本次方法与复用依据 | 执行状态 |
|---|---|---|---|
| V01 来源准备 | 9原件/43组件/8删失/原预期SHA不变，prepare不调用策略 | 重新核原件、prepared/raw/经验与原prepare命令/产物SHA；prepare/data/import依赖未变，重建结果原已逐字段等同，不重复准备 | 通过：已核、有效证据迁移 |
| V02 密集/短返 | E01/E02/E04不抢工作，1800保护不变 | 重新读三段完整原实跑；核G19全支持集/知时/删失证明覆盖这些相同输入与全部保存决定，核依赖后迁移；不据actual Stop=0免责 | 通过：已核、有效证据迁移 |
| V03 平台责任 | 保留E03/E05/E09原截止负数与同初态E03共同末点，不能换E01初态 | 核base与continuation E03/E07、压力产物原SHA及支持集；共同需求/初态/末点/负结果不变，G18仅取消动作诊断名不触本链 | 通过：已核、有效证据迁移 |
| V04 主要长平台 | E06/E08基础各至少一次实际完成且有益，不过早/频 | 核原CLI完整actions/state/费用，确认当前G19支持集证明逐case覆盖；既有经验入口/价格/seed/缩减/执行器无变，有依据迁移数值 | 通过：已核、有效证据迁移 |
| V05 连续恢复 | 自有context→回归1800保护→低存量不再维护，第二次独立边际收益 | 核journey、same-prefix仅首维护对照与mode-only/anchor机制；实际预测无有效Stop label的全程证明适用，不用独立片段冒连续 | 通过：已核、有效证据迁移 |
| V06 缺口/失败 | 缺当前证明不提前维护；失败付费无缩减，后续可继续 | 原failure/raw输入与完整输出SHA/依赖核；G19审计明确覆盖，实际恢复不变，负差不删 | 通过：已核、有效证据迁移 |
| V07 费用/模型压力 | 昂贵压力可拒绝、负数不掩；条件估计不当实测 | 核v11后仅policy/Replay/rollout三源差异；逐列21报告43路径2578重叠记录的版本迁移证明/原件/来源/裁剪边界，当前31独立+101机制证据替换旧等待主张 | 通过：已核、有效证据迁移 |
| V08 导入主链 | preview无写→apply43→新进程可读→重复不倍增且实时状态不转移 | 导入CLI/import/store/samples/原生DB等依赖SHA全相同；复核原command/receipt/全表快照/新进程证据，允许从合法隔离库重读；不重新apply无变化证据 | 通过：已核、有效证据迁移 |
| V09 冲突/隔离 | 内容冲突/无owner证明/跨Profile明确原子拒绝，其它ref/Profile无污染 | 与V08同未变依赖，重核原拒绝stderr、语义快照/owner绑定及隔离库当前只读结果，数值不受G19消费者影响 | 通过：已核、有效证据迁移 |
| V10 原失败与取消恢复 | 新诊断名诚实；paid1143046.3338可大于reference778332.0856，context275039不缩，后续38HB/6Reminder/另1成功维护，负数保留 | **实际公开CLI**用原cancel-input.json/原cancel.command.json参数仅换output=cancel-final.json；核全部results除实测elapsed/single_decision_seconds与G18明确名映射后等同原f7/根g18结果。核无receipt标签现名与高低无receipt现有效33项，G19实际等待/正式候选反例31+101证据；无经验44决定另核“有cancel支持但无profile/started”不能混称无Stop | 通过：原输入实际CLI复验 |
| V11 无后读/知时 | 非空维护经验却未来需求0时不为整理而整理；知时不泄漏 | 原M01 formal decide返回0费用/无维护的夹具和除policy/rollout外依赖未变；该路径无started所以G19 wait=0不变，核原1项证据与当前支持；613记录及新cancel逐时知时复核 | 通过：已核、有效证据迁移 |
| V12 可复核与范围 | 原件/经验/隔离及版本未变，无生产/网络/UI/模型/提交；缺陷无隐去 | 对所有引用SHA/当前树/git及最终产物作范围审计，单次资源与长矩阵分开；修后各适用场景均符合才PASS | 通过：已核、有效证据迁移 |

执行边界继续仅本报告与ignored validation/；不改原输入/产品/测试/其它报告/真实Profile；无网络/SSH/生产/模型/UI/提交/派生。只原取消完整run一次，必要受影响才定向补跑，不重跑13矩阵或31/101已有效机制。G19证明只限已列固定输入、cohort、起点、原生排除与730<2048边界；若SHA或边界不成立，保留为证据缺口并向root交回。原f7失败、g18产物和r3等待反例均不覆盖。


### 当前十二场景逐项续验结果（3e08）

证据前缀为ignored .hermes-dev/adaptive-empirical-20261106/validation/。共同版本/来源/支持集审计为final/current-applicability-audit.json，已核75源、9原件、经验/包SHA、21报告/43路径2578重叠记录及原始失败副本SHA。各行均回到原用户目标和完整结果判断；“迁移”明确指原实际操作证据在当前未受影响路径仍有效，不冒本次重新执行。

| 场景 | 当前实际结果与用户目标判断 | 当前证据/适用性与结论 |
|---|---|---|
| V01 | 9原件/43组件/8删失/预期SHA未变，prepared仍与原包逐字段相同；准备入口/数据投影未变 | final/current-applicability-audit.json及原prepare-raw.command/compare；通过（迁移） |
| V02 | E01/E02/E04全部0维护/0碰撞，持续增长与4分钟短返不抢工作；1800秒保护仍保 | 原base完整实跑和支持集各case覆盖，G19无有效Stop label进入等待变化；通过（迁移） |
| V03 | E03原截止亏454484.72、E05亏23830.64、E09亏6775.92完整保留；同173613初态E03共同末点条件少2277454.61；非每平台必压或必盈利 | base与continuation-e03/e07原SHA核，未用E01的67817初态替代；通过（迁移，边界显式） |
| V04 | E06/E08基础均1次实际完成、0碰撞，原截止分别条件少597664.01/2628378.29，未全程拖延；样本/价格/seed/门槛不变 | 原完整actions/states及每路径支持集成立，当前有经验scenarios/执行器未变；通过（迁移） |
| V05 | 连续E01自67817起2次完成，末context123878.5；回归E07 phase94778→102767.5且0维护；同前缀第二次边际少194336.60，有独立收益 | journey/repeat及mode-only/anchor证据未受影响；E07独立同308921初态共同末点仍亏121905.21；通过（迁移） |
| V06 | rawcoverage E08无维护，不能拿后见覆盖当当前无人；机械失败首费603446.87、context仍275039，之后38HB/6Reminder及合法新维护可恢复，费用亏1106461.40仍在 | failure/raw固定输入及支持集核，费用/执行/失败不在G19差异内；通过（迁移） |
| V07 | 当前模型E06亏46227.40、当前模型整账单E06无维护且亏105734.98、E08压力仍有条件正结果，全部按原来源披露，不掩负数 | 21报告SHA与G17有经验分支/G18输出名/G19支持集证明闭合；31+101修正等待证据替代旧错误主张；通过（有边界迁移） |
| V08 | 同43样本原preview→apply→重启读取→重复的收据链有效；当前以read_only重开仍43，实时/原生/计划/HB等全表与原快照完全相等 | final/import-final-reopen.json＋原import-summary/commands，全依赖未变；通过（原实操迁移＋当前重读） |
| V09 | 原内容冲突/无owner证明/foreign Profile/不存在目标拒绝与全表不变仍成立；当前other ref与另一物理Profile无导入 | 同未变导入依赖、拒绝stderr与当前只读重开；通过（迁移＋重读） |
| V10 | **原cancel输入当前完整CLI实际通过**：paid1143046.3337856613不截低，sampled_completion_cost_reference778332.0856089034可更低，取消context275039；后续38HB/6Reminder/另1成功，2次mode-only、不复活旧Idle；总费3542399.363008806、亏1646060.8680088043均保持 | final/cancel-final.command.json/json/md与cancel-comparison.json；完整results仅去实测时钟/映射G18名后与原f7及根g18逐字段相等；通过，G18关闭 |
| V11 | 非空经验无后读机制仍business/无维护/费用0；原613记录和新46条decision知时无越界。无真实完整无后读片段，明确机制补充 | 该M01完整receipt无cancel需求且无started，G19等待分支不变；原1项有效证据/current依赖核，新cancel逐条核；通过（迁移＋当前知时核） |
| V12 | 所有适用场景均有来源/当前依赖依据，原件/预期/失败未改；新CLI真实完成且当前树固定；无生产、模型、UI、网络、SSH或提交 | final/scope-final.json、current-applicability-audit及各命令；通过 |

G19专项用户效果与影响判定：原声明“10% user2排队、Stop3释放，其余90%晚归”的真实维护等待应为0.1秒；r4当前正式evaluate观测0.1、collision0.1、cost199855、baseline1009750，candidate accepted且无拒因。原99.8错误不得沿用，30秒门槛/费用没有调低；31独立边界与101相关结果的当前源SHA已核，覆盖Stop-only、多排队、自然完成、后续长Main/HB等。该机制补充是用户输入→真实释放→后续可用性的不变量，不能用本次“Stop-only无排队”的实际CLI单独代替它。

对原真实回放，独立核唯一真实cancel后的15.56335秒原生维护；能包含该cancel却避开删失的origin范围1793759422.4933662–1793759438.0567162内，原verified turn_end与全局1800格点均为0。仅两个可能origin的正式outcome均被维护删失。已知cancel的被审run都在相应维护end可知之后起步，不能生成更早origin；bootstrap/cohort无cancel token；严格较晚end与duration恢复防止保cancel丢exclusion。声明Stop/end同刻不靠排序臆断，实际两旧路径730<2048上界及新路径同动作/结果等值保证保留。无经验输入确可含cancel label，但44次无Profile/无started，改变等待分支不可能进入。故当前支持集内其余真实结果可迁移；新增输入/cohort/跨越该时间窗或触及裁剪边界不受该证明覆盖。

### f7首轮详细场景结果（历史保留，非当前门禁状态）

以下预期均在本次候选CLI运行前登记。所有场景产品版本固定f7aecf8；起点与历史由获授权包保留。以下保留执行前计划并附实际结果。

### V01 原始证据准备链
- 意图/要求：让真实历史可审且不泄露未来（G1）。
- 输入/起点：manifest的9冻结原件、43维护组件、原经验表。步骤：SHA/字节对照；CLI prepare --input-dir inputs --manifest input-manifest.json --components maintenance-components-normalized.json --experience-cases experience-cases.json --output validation/prepared.json；比较原包的案例、预期、事件/组件/来源/假设。任何不一致保留并调查。
- 预期：原件匹配；prepare无候选调用；9真实+3声明补充不变，维护缺测/来源/知时与条件假设明确，不用累计input代context增长。
- 实际/证据/时间/结论：**通过**。2026-11-06本地CLI prepare-raw成功；9原件SHA/字节匹配，43组件/8删失与来源索引匹配，经验SHA仍449d078f…cd448a；prepare输出policy_calls=0，prepared包与原包完全相等。证据validation/{environment.json,prepare-raw.command.json,prepare-raw.stdout,prepare-compare.json,independent-audit.json}。首次错误输入/完整异常保留在prepare.*；偏差为root授权改用正确raw格式，未变案例/样本/预期/成本。

### V02 密集工作/短返保护
- 意图/要求：G2，不抢当前工作。步骤：CLI run --input prepared.json --cases E01,E02,E03,E04,E05,E06,E07,E08,E09 --output validation/base.json；逐段检查E01/E02/E04完整动作、用户/机械工作年龄与碰撞，非仅单点decision。
- 预期：密集上升及约4分钟再提交不受理主动整理；用户/新Main使旧计划失效；高增长不能掩盖工作连续性；保护至少原1800秒，不能把机械Turn结束称语义任务结束。
- 实际/证据/时间/结论：**通过**。base.json完整E01/E02/E04均0维护/0碰撞；E01新epoch67817→158766、E04 173969→228240的增长没有抢整理。E02 4分钟短返段0维护，不能把source unknown完成Turn冒为已证user工作。完整工作年龄与1800秒保护审计无违例。证据validation/base.{json,md}与independent-audit.json，CLI wall127.189秒。偏差：无。

### V03 中/高存量与读取责任
- 意图/要求：G3。步骤：同次base检查E03/E05/E09整段candidate与两固定模式、维护时点/费用、原截止与共同终点责任，判断拒绝/维护是否有经济解释；不因audit自动通过就忽略负数。
- 预期：不要求每平台压缩；E03若选择维护需展示可完成空档及未来责任收益，原5h未回本须显著保留；E05后台不能重置真人quiet；E09看空档而非夜间硬编码，允许因经济性拒绝，整段机会审计必须可读。维护/恢复不能移出比较末点，原截止亏损如实记。
- 实际/证据/时间/结论：**通过（条件经济边界保留）**。E03原173613初态、约5h仅1HB，维护一次费用629304.22，原截止相对较便宜固定模式**亏454484.72**，不是短窗口盈利。另直接读取同一173613初态、同外部需求延至既有共同终点的continuation-e03-v11.json：费用3784740.85、条件净少2277454.61；没有用E01的67817初态代替。E05一次维护后HB16，背景自增未伪真人；短截止**亏23830.64**。E09 412646→55227，一次218.218秒维护，先于首冷读、实际安静1800秒，26HB使原截止**亏6775.92**，一次末态冷读压力差另为正361648.08，不冒已实现收益。三段可解释且履行固定原预期的机会/保护审计，不能归纳为全部盈利；E09非强制必压。证据base.json、同初态continuation-e03-v11.json与independent-audit.json.reuse（SHA已核，见V07）。偏差：共同末点按计划复用，原截止本次实跑。

### V04 21h及近两日机会
- 意图/要求：G4，主要用户痛点。步骤：base E06/E08读全部计划/实际维护/结算、quiet/风险/费用与context/cache；与同初态同终点固定两模式比较。
- 预期：基础经验均至少有一次有限、不过早/过频、有收益且实际模拟执行的维护，不可只建议不执行或全程推迟；失败/Noting费用保留，阻挡按Compact而非Noting总时长；不得修改费用/种子/案例凑正例。
- 实际/证据/时间/结论：**通过**。本次真实CLI E06 21h基础一次实际维护并完成，275039→56872.25（维护后），602.802秒、维护费用778332.09，28HB，原截止条件少597664.01；E08近两日基础一次完成，228240→47195.21，90HB，原截止条件少2628378.29。整段不是只有计划；最短实际quiet1800秒，0碰撞；历史Noting费用入总账、Compact时长为阻挡，paid失败样本仍在训练分布。没有改价格、seed2、案例或截止。证据base.json中E06/E08完整actions/decisions/states、base.md及independent-audit.json。偏差：无；上述是声明组件/coverage/排期条件下的代理费用，非实测节费。

### V05 跨阶段持续使用
- 意图/要求：G5。步骤：CLI run --cases E01 --extend-to-cutoff --output validation/journey.json；检查新epoch67817起的工作→平台→维护→回归→第二平台完整序列；对照E07独立起点与phase_projections，不沿历史大context回填。核维护后mode-only刷新/不复活Idle、HB锚点与后续自然Main。
- 预期：自有缩短context加真实新工作，真人回归重置quiet，1800秒内不再维护；不能以低context为整理而整理；后续维护有独立边际收益来源（可复用同前缀只首维护对照），生命周期/模式不因维护重计时。独立E07短截止亏损不隐去。
- 实际/证据/时间/结论：**通过**。E01实际CLI连续到原共同截止，2次成功维护/108HB/19Reminder/0碰撞，费用4269334.14、较最佳固定条件少2122049.91，末context123878.5。两次开始context159572→39081、131675.5→38608，quiet2698.092/7033.086秒；不贴历史大context。回归E07 phase从94778→102767.5，新增真实工作但0维护；恢复工作及低context下不追着整理。独立E07大context起点等1800保护后整理，原截止亏849494.73、同308921初态共同终点仍亏121905.21，完整保留，不冒独立窗口盈利。复用同前缀/共同终点只首维护对照：第二次另付950450.24，下游少1144786.84，独立边际少194336.60；本次连续数值与该参考base精确一致。维护后每个结算有mode_only，未借结算复活Idle；锚点/代次细审复用原同版observer审计与32项机制证据。证据validation/journey.{json,md}、repeat-maintenance-v11.json、continuation-e07-v11.json和execution-audit-v11.json。偏差：无。

### V06 缺口与失败压力
- 意图/要求：G6。步骤：CLI run E08 --variant raw_coverage_only，CLI run E06 --variant mechanical_failure，分别新文件；检查完整执行、拒因、结算后状态与后续读取。
- 预期：当前观测无证明不得提前维护，不能跨缺口制造安静；失败必须付已发生费用且无成功缩减，后续可继续HB/自然Main，不能立即复活已消费Idle或伪造取消；允许负收益，原数据长耗时/失败不剔除。该变体是明确压力模拟，不冒真实发生。
- 实际/证据/时间/结论：**通过**。E08 raw_coverage_only完整CLI0维护、96HB/19Reminder，source current资格不因重建长段假定通过；条件亏177680.20照录。E06 mechanical_failure首维护失败，已付603446.87、阻挡600.014秒，维护结束context仍275039；后续38HB/6Reminder继续，冷却后下一自然Main生成合法维护并成功，共2次/1失败/0碰撞，原截止条件亏1106461.40。没有把失败当免费成功，也没即刻重挂已消费Idle；实际失败情景来自保留历史内部失败，不虚构Stop。证据validation/{raw-coverage,failure}.{json,md}及independent-audit.json。偏差：无。

### V07 昂贵压力复核
- 意图/要求：G7。步骤：阅读现有v11费用、缓存、整账单、当前模型、慢阻挡、恢复/终值压力和只首次对照产物；核当前75源依赖/有经验分支适用性，摘录真实费用负数与不维护边界。
- 预期：昂贵可不维护，不为每压力盈利降门槛；不能把条件收益称实测或掩E07/E09负数。明确跨模型/缩减迁移、prefix估计来源与限制。
- 实际/证据/时间/结论：**通过（有依据版本迁移复用）**。独立核source-scope-v11的75份冻结源码均SHA相符；当前仅adaptive_policy.py变化，正式_maintenance从compatibility helper变为相同empirical.scenarios，有经验返回路径相同。当前真实CLI9段/连续/失败/raw的同起点核心费用、context和动作计数与旧对应产物相符，故保留其余费用敏感性复用；不是把旧报告重命名为本次执行。旧保存分支1919记录核为经验样本非空由Verification另证，本次核相应artifact SHA与源码适用性。
- 保留结果：当前完整Provider/model E06亏46227.40、E08少1977662.65；当前模型整账单E06 0维护且亏105734.98、E08少571017.52；同target E06/E08分别少607946.83/2554572.22；慢阻挡E06/E08仍有一次维护，E08少2626901.53；未知Reminder E08 0维护。原字段条件/缺口未转实测，费用／cache／排期不确定性确会改变机会，不能宣称稳健普遍节费。组件43份含跨模型与未证owner池，完整同parent联合支持0，GPT Compact账单缺口、prefix成本迁移与绝对/比例缩减包络仍是明确工程假设。证据independent-audit.json.reuse记录各产物SHA和费用，原13矩阵/只首对照不重跑。偏差：计划内复用。

### V08 导入预览到可重读
- 意图/要求：G8。合法准备：在validation/创建隔离default Profile/SessionDB，建立target与other会话；记录实时events/plans/HB等基线。步骤：CLI preview原43组件包；重读数据库确认未写；CLI apply同包同ID；新进程重开store.imported_history读取；再次preview/apply同ID；原包SHA复核。
- 预期：预览显示模型/来源/缺口，无写入；apply仅目标import表与receipt，原发生/可知时间不改，imported_at另加；新进程可读数值而非正文/凭据；重复相同receipt不倍增，不迁当前context/last_user/HB/计划/Idle。
- 实际/证据/时间/结论：**通过**。真实CLI preview event_count43，models/ownership=unproven_historical_component_pool、缺口/限制可读；成熟隔离DB全表语义逐项相等，无导入写入。apply显式成功，新进程重开读43样本，原at/available_at逐条相等，另加imported_at；仅secretary_adaptive_imports/import_events/import_members改变，目标本地event、pending计划、hot/1740锚点等所有原生/实时表不变。重复preview与apply已应用receipt稳定、全表不变，不倍增。原normalized输入SHA未变。证据validation/import-*.{command.json,stdout,stderr}、import-{before,after-preview,after-apply,after-repeat,reopen,summary}.json；实际Profile仅validation/profile-import-v4。偏差：脚本/冷库准备问题见§2，最终完整主链重做，无产品修改。

### V09 冲突与owner隔离
- 意图/要求：G9。步骤：从原包生成仅用于冲突探针的数值副本（不改原件），同ID preview/apply；以source-kind conversation声明不匹配owner的原组件；对不存在target和另一独立Profile/other target读取；每次前后比较数据库语义。
- 预期：同ID内容冲突和无逐样本owner证明均明确拒绝且原子不污染，源缺证明不能变有证明；另一ref/Profile看不到目标导入，目标已有本地事件/实时状态不变；合法可修正后继续读取原receipt。
- 实际/证据/时间/结论：**通过**。同ID一项duration+1内容副本apply明确conflicting declaration；原组件按source-kind conversation/source-conversation目标声明，因每样本缺owner证明拒绝；不存在目标拒绝；显式foreign origin_profile拒绝cross-Profile。各错误后全表与apply后快照完全相同，原receipt/43事件仍可重读；目标other ref无导入，另一物理Profile数据库无导入，不污染本地实时状态。证据validation/import-{conflict,unproven-owner,missing-target,foreign-profile}.{command.json,stderr}、conflicting-components.json/foreign-components.json及import-summary.json。偏差：无，派生副本只用于负向输入，原件未改。

### V10 无经验与失败取消恢复
- 意图/要求：G10。步骤：复制prepared包到validation/标明声明变体，仅清空maintenance_samples而不改历史/体验约束；CLI E06完整run检查无固定prior维护；引用当前g17-targeted-tests及正式采集/并发取消/模型切换/重启/失效证据，核版本和实际状态结论。
- 预期：无经验明确missing empirical，不用3M/3600或廉价prior授权主动整理；HB可独立选择，原生容量保护不被取消；真实Stop仅在合法外部动作存在时触发，已发生费用保留、已提交Note不撤销，失败/取消后可继续使用。引用不足即未通过，不以“无需模型”豁免。
- 实际/证据/时间/结论：**失败：G18为R4/R5范围内诊断解释错误**。无经验CLI分支本身符合：除43maintenance_samples外，额外去掉残留maintenance_start/end两事件（missing-removal.json逐ID列明）；没有完整legacy可授权，所有decisions T/δ均None、maintenance_evidence.reason=missing_empirical_maintenance_scenarios且compatibility_prior_allowed=false，38HB/6Reminder仍可用，0主动维护。原3M/3600等config未下调，也未修改原包。
- 补充探索实际跑声明Stop：从prepared副本在E06首维护开始+10s加入verified external activity=cancel（cancel-input.json，明确非真实历史）。首维护11/5 14:30:26.392开始，10秒后取消，原context275039保留，后续38HB/6Reminder运行，冷却后新Main成功维护，主使用恢复；原1800秒及费用不变。实际总费3542399.36、较最佳固定条件亏1646060.87，不隐去。
- 发现：actual_user_cancel.paid_cost=1143046.3337856613来自历史取消receipt，但同动作full_cost_upper_bound=778332.0856089034只是原成功sample费用，前者大于后者，不能称上界。费用与状态链本身保留真实来源、未被截成较小值；错误在给用户的可解释输出。源码secretary/adaptive_empirical_replay.py:390直接把active.cost命名上界。已交root并被认定G18，root拟只改名sampled_completion_cost_reference及未知取消源名，不改paid/算法；尚未实施/复验，不能先报通过。
- 证据validation/no-maintenance.{json,md}、missing-removal.json、cancel.{json,md}、cancel.command.json及原f7 SHA。原生容量/关闭/模型/重启/已提交Note保留/取消队列同路径机制引用当前g17-targeted-tests.log146项及replay-mode-refresh-tests.log32项、正式integration/runtime有效证据，不冒真实历史观察或新UI验收。偏差：在复用之外新增声明Stop完整CLI，正因此发现G18；保持失败，不重跑掩盖。

### V11 无后续读取与知时
- 意图/要求：G11。步骤：复核当前同路径M01/M03机制证据、来源available/imported_at/成熟窗口及本次base每决策visible/label时间；真实无后读样本不存在，机制明确标注。
- 预期：没有未来需求不制造读费/为整理而整理；未来/迟到/未成熟费用与结果不进入过去训练，完整未来仅作事后评分；自有context/cache不贴回旧曲线。
- 实际/证据/时间/结论：**通过（明确机制补充）**。本次613条保存decision逐条核visible_event_max和forecast_latest_label_end≤决策时间，无未来泄漏；原43样本at/available/imported_at仍各自门控。当前有效g17 146项中的迟到exclusion/gap/maintenance、bootstrap及learning测试与本次知时审计相接，非仅自报。
- 额外定向补强M01：既有business∞例缺维护样本会因G17走无经验分支，不能单凭它证明“有完整经验仍不为整理而整理”。在ignored validation/test_declared_no_future_reads.py保留声明成熟无后续需求、business∞、无Reminder并加入完整数值维护receipt（90K/600秒/.18，明确合成机制而非历史）；正式decide返回business/T=None/δ=None/estimated_cost=0，maintenance_evidence为empirical…且samples=1，故非缺样本空跑。官方runner1项通过0.4秒；首次辅助脚本parents[4]定位错，未触产品即失败，修为parents[3]后通过，初错日志保留。真实九段无完整无后读实例，未伪造。
- 证据validation/{independent-audit.json,no-future-decision.json,no-future-tests.log,test_declared_no_future_reads.py,no-future-tests-initial-harness-error.log}；原正式知时/采样证据按同SHA复用。偏差：加定向非空经验机制反证，不替代CLI主旅程。

### V12 收尾重读与范围保护
- 意图/要求：G12。步骤：重读CLI JSON/MD产物，记录耗时版本，核每个适用场景证据及原件SHA；核git HEAD与dirty仅自身报告新增；核隔离库实时表未变、原件未变。
- 预期：可复核、无生产/模型/UI/提交；区分单次决定与整段回放资源，既有范围外no-tmp不伪报全绿；不开启/非eligible/owner/Force契约沿有效同版证据。无场景默删。
- 实际/证据/时间/结论：**通过（交付仍被G18阻断）**。实际6次run产物（9段base加5个单旅程/变体）、prepare、导入全链及1项定向机制结果均可从command.json/JSON/MD重读。HEAD仍f7aecf8，9原件/经验SHA不变，当前源码与各本次报告SHA一致；本验收仅新建ignored validation/和修改本validation.md，不触Huawei或他人动态文档。613条决定的知时/quiet/无经验/结算审计errors为空，但诊断G18未包含在该机械audit，不以errors空当全通过。旧no-tmp范围外失败、非生产/RSS资源边界原样披露。没有网络、模型、SSH、UI、生产、提交或部署。证据environment.json/independent-audit.json及最终scope-final.json。偏差：无。

## 5. 问题、修复与复验

**当前关闭结果：** G18已在3e08由本验收使用原输入实际完整CLI关闭，证据final/cancel-comparison.json；G19在当前等待/正式候选/后续队列结果及支持集影响核验下关闭，证据r4独立31项、当前101项与final/current-applicability-audit.json。没有新增缺陷或证据缺口。以下表中“尚无/待复验/门禁开放”为f7首次发现时的原状态，保原文并由上述当前证据追加关闭，不改写历史。

| 当前问题编号 | 复验完整序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| G18 / VAL-01 | 原cancel-input＋原命令仅换输出→取消→结算→后续38HB/6Reminder/成功维护 | 新参考名/未知代理名正确，paid>reference仍保原费用；完整results与旧规范后等值，final/cancel-comparison.json | 已关闭，V10通过；原失败保留 | c301诊断修复，当前3e08有效 | 当前真实CLI22秒级完整链，来源及无receipt33项机制适用性核 |
| G19 / 原r3 V3-01 | user2排队→Stop3释放→按实际维护终点结算→正式候选判定；真实21报告影响核 | expected_wait99.8→0.1、cost/collision等值、candidate接受，31独立/101当前证据；支持集与SHA核见final/current-applicability-audit.json | 已关闭，未降低30秒门槛，无新增整改 | 3e08 | 原取消CLI当前完整复验；其余场景逐路径影响证明有效迁移，无无理由大套复跑 |

首轮f7发现与准备问题原文：

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| G18 / VAL-01 | f7原prepared→声明E06首维护+10秒真实外部Stop动作→公开CLI run→actual_user_cancel输出→结束后继续HB/Reminder/新维护 | 应准确表示历史取消付费与成功sample参考，实际paid1143046.3338 > full_cost_upper_bound778332.0856；cancel.json/command.json与源码:390 | R4/R5诊断解释错误，root已确认范围内；费用/状态正确也不能豁免，V10失败，门禁开放 | 尚无，root拟改名参考字段及无receipt源名，保持算法/paid/采样 | 待修补后原cancel输入CLI复验，核paid/context/动作不变及新字段语义，保留本原反例；相应Verification由root编排 |
| PREP-01（非产品） | normalized组件包送prepare→KeyError censored | 实际应raw组件投影，root确认交接说明失配；prepare.stderr保留；raw SHA/43+8已核 | 输入准备纠正后关闭，无产品/预期修改 | 不适用 | prepare-raw成功，prepared与原包完全相同 |
| HARNESS-01（非产品） | 隔离DB辅助全表快照/重读及新增机制测试定位 | WITHOUT ROWID/bytes/str Path/parents索引错误发生在验收脚本；新冷库首次FTS版本初始化独立保留 | 辅助脚本纠正并从新库完整重做；不冒产品失败，也不隐去初始日志 | 不适用 | 最终import-summary全真；no-future-tests1项通过，初错日志保留 |

首轮当时：本验收未自行修改产品，G18方案尚为root提案，不能作当时关闭证据；当前关闭由上表新增实际复验支持。原失败和全部数据保留。其余范围内未发现新缺陷；费用敏感性与原截止亏损不是改预期后的PASS，见逐场景说明。

## 6. 验收结论与推荐复核

**当前3e08的Validation门禁通过：V01–V12全部通过，0失败/0未执行/0阻塞。** 原G18失败已用原输入实际CLI复验关闭；G19按实际释放修正等待、费用与风险同源，当前机制及真实数据支持集影响均有证据。逐目标结论见§3/§4，完整原f7当时11通过/V10失败报告及其SHA保留；旧PASS撤回/r3等待反例也保持原历史。

主要经验结论仍为：密集/短返不抢整理，E06/E08基础实际有益维护，连续旅程自有context回归且后续低存量不重复整理；无后读及缺证不为整理而整理，失败取消付费并恢复后续使用。所有有限负结果保留：E03/E05/E07/E09原截止约亏454485/23831/849495/6776；同初态E03共同终点才条件少2277455，E07共同终点仍亏121905；机械失败及声明Stop完整费用负差没有抹平。这不是“全部经济窗口盈利”或生产实测节费结论。

推荐主要复核路径：

1. 本次当前实际完整取消链：validation/final/cancel-final.command.json→cancel-final.json/md→cancel-comparison.json。应见paid1143046.3338、sampled_completion_cost_reference778332.0856、取消context275039、38HB/6Reminder/另1成功维护、总费3542399.3630及负差1646060.8680；不是费用上界，不能为显示上界截低paid。
2. 真实历史全段经验：原validation/base.json/md、journey.json/md及同173613初态continuation-e03-v11.json、repeat-maintenance-v11.json。当前版本迁移范围与逐SHA依据见validation/final/current-applicability-audit.json及G19原impact-evidence；不混初态、末点和末态压力收益。
3. 显式导入完整链：原import-summary/commands/receipts和当前final/import-final-reopen.json，只读自建profile-import-v4及profile-b；应有43样本、全表不变与其它owner为空。不得把隔离Profile命令作为生产导入授权。
4. 风险等待的声明机制：verification-r4/cancel-wait-counterexample.json及31边界/101相关证据。应见0.1秒而非99.8、collision=.1、费用不变、正式candidate接受；这些是机制反证，非真实历史取消统计。

本次仅新运行原取消完整CLI，另做只读重开和依赖/支持集分析；原实跑证据在已证条件内迁移，没有重跑13矩阵或重复大型套件，没有把旧11通过直接换版本名。源3e08保持冻结直到本报告交回，最终scope-final.json将标product_operations_complete与safe_for_root_version_switch。主会话接收并亲审后决定目标交付，不由本报告授权上线。

限制持续有效：跨模型组件、prefix费用缩放、绝对/比例缩减包络、coverage/Reminder重建、固定倍率与同源需求不随策略改变均是条件估计；完整同parent联合支持0及GPT Compact账单缺口仍在，非充分生产实测、Notebook内容质量、真实模型/UI取消或目标服务器性能验证。Agent自主工程收敛仍待用户追认；真实原件仅ignored本地，未合main/上线/改生产，禁止上线未撤销。冻结十检查仍保原no-tmp范围外历史失败，不能声称十项整体全绿。
