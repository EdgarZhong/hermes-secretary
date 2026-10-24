# Verification：20261024-noting-maintenance-v2 最终全轮复审

## 1. 审查对象与结论概览

审查者：全新独立 Verification（noting_v2_final_verification），未参与实现和前两次审查，不再派生。日期：2026-10-24。工作区：`/Users/edgar/code/hermes-secretary-noting-v2`。Snapshot Index：`.autonomous/20261024-noting-maintenance-v2/snapshot-index.md`；冻结版本：`a4faa767e6b7c1d01ec688a083c71576d58638a5`；待审产品：`833277e804f82333a3e5be55e1c7386542e712a6`。

范围：本轮 R01–R15/O01 全部要求及其直接相关的既有上下游不变量。最终总体结论：**Verification 门禁不通过**。第3节16行中14符合、1违规（R05/F04）、1证据不足（R15/E00）。833真实续短已独立核验；其摘要被审计SIGTERM截断，尚无第二压缩/Framework/最终Main完整结果，N46实际请求0。不能进入Validation或宣称目标完成。本报告获授权另建，用于保留两份历史审查。

## 2. 独立要求清单与覆盖

以下判据于 2026-10-24 在读取实现、tests、实现报告、CLAUDE 或历史审查前独立建立并落盘。读取依据均来自冻结 SHA 的原文：07 顶部 v2 §0–9 优先；完整白板（含动态七类型、场景数据）；07 未替换契约；02 Identity/Foreground/Snapshot/原生后台及失败投递；04 未替代身份/配置/D01/有限续跑增量；01 产品定位；06 原生客户端、兼容/持久化/真实消息契约；08 Profile 和宿主归属。历史四工具/maintain、旧字段、旧 Prompt、旧并发 Idle 以 v2 明确替换为准。索引仅定位及追溯用户确认，未以实现解释作为判据。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| R01 | 07 v2 §0、§3、§6；07 §3.1、§8.2；02 §5.2–5.5；04 §4.4 | 机制；eligible Main/Noting 全生命周期 | 六工具完整固定 API 顶层；Main 可同时有其它工具。冻结 Root/tools/Active 原样共享，任务及续 Turn 只追加权限和完整工作视图；不以权限切换重建工具表 | 查实际序列化 Main、首 child、工具循环、重试/续 Turn；无折叠、messages.tools、重复 Schema；父后来活动不改变冻结 child | 第3节 R01 |
| R02 | 07 v2 §0、§3、§6、§9；白板 K1/K6；02 §1.9/§5.7 | 权限；同步/并发/invoke/间接 | Main 运行时拒绝 create/update/archive/finish；History/Show 合法；Noting 精确六工具，继承其它声明不授执行权。可信身份、绑定父域和工作态决定权限 | 主/子/普通辅助身份与包装调用均不可越权；拒绝零副作用；初始、current control、续 Turn 权限文字同步，父角色与任务明确失效 | 第3节 R02 |
| R03 | 07 v2 §3；07 §4.1/§4.4/§4.5、§7；白板 K6/C6 | 数据/机制；维护与最终提交 | 三工具扁平，同名同层；旧 maintain/alias 退出执行面。稳定 entry_id/不可改类型，不可变 version；真实改动新版本/no-op 不续期；fields 键合并/数组整体/可选 null；finish 独立且请求结束≠提交 | Schema/validator/dispatch 一致；非法字段错误可纠正、失败工作态不变；批次含 finish 整批预拒绝，结束后写拒绝；Turn 返回后才 Commit Gate | 第3节 R03 |
| R04 | 07 v2 §1–2、§6.1–6.2；白板 C1/C3/C7/C8/K6 | 数据/内容；七类型+Candidate | 七类必填准确，未知不造；删除 external_refs，不加 schedule_refs/材料字段；文件仅精选 description、不扩 situation 准入。Candidate 来源二选一、标签映射与原位来源保留 | 类型合法字段/必填/可选与 Schema 一致；Candidate refs/确切 UID 互斥，gap→situation，直接型不造标签；稳定身份及 provenance 合法 | 第3节 R04 |
| R05 | 07 v2 §2、§6/§6.1/§6.2；白板 I1/I2/U1/L7/N1 | 模型行为/Prompt | description 是可辨识语义索引，保留当前意义与有用历史，通常1–3短句/150中文或80英文词软指导，不硬截断；路径不计；第3写作/第5过滤表独立，七步全职责 | 真实构建 Task 和全部 suffix 没有未知摘要比较、配额或重复规则；实际内容跨轮保留转折/来源，非流水账、不误归因AI为用户 | 第3节 R05 |
| R06 | 07 v2 §5、§9；白板 L2/T4；07 §4.1 | 数据/时间；全模型投影 | runtime 派生 evidence_time 模型可见且不可写；仅range复用；UID真实user范围优先、否则最近assistant、否则全组；UID优先range仍展示；unknown不回填now。首次证据、progress/discussion、gap识别计龄不可混淆 | Show/初始/续Turn/回执/Framework一致；拒绝手写；source变更不靠重读/改写续龄，7天/72小时只处理不自动删除；Candidate refs不伪造直接时间 | 第3节 R06 |
| R07 | 07 v2 §3/§6.3；白板 K6/C8 | 引用/事务；archive | 普通 relations 在归档时运行时原子解除，回执列受影响项；gap情景和Candidate来源阻断须明确处理；不级联业务状态、不加DAG门禁 | 基本目标存在/类型/重复/自引用检查；受保护引用失败无任何归档/清理副作用；成功清理产生必要版本且旧快照不变 | 第3节 R07 |
| R08 | 07 v2 §4/§6.1 新第6步、§9 | 数据/模型行为；所有entry | 顶层零或一 schedule_suggestion，恰含非空 content/schedule 普通语义字符串；不做时间语法校验。每次Noting必查未来要求/接受责任/Main承诺，缺口才加，自包含正文不套description长度 | 任意语义排期合法，非法对象准确拒绝；真实模型补相关建议含背景对象动作条件，区分承诺/登记；无Scheduler执行、副队列/新材料字段 | 第3节 R08 |
| R09 | 07 v2 §4、§6.1；07 §8.13；白板 N3/P2 | 注入/时序；实际有效Notebook | 注入有效Notebook有建议时Framework最底部精确追加定稿 Main 提示；无建议不加。语义advice、尚未登记、考虑创建更新，不是强制操作/新授权 | 同一有效Snapshot正文与条件提示一致，过期队列结果剔除；无额外Turn、微信/adapter外发；错误或无新提交不假造Notebook | 第3节 R09 |
| R10 | 07 v2 §7/§9；07 §5.2.9/§11.2；06 §1.14 | 行为/机制；所有压缩触发与live/durable/request | Noting开且eligible Main：真实原生阈值自动保默认tail，其他取消；显式 /compress here N 保指定tail；off/非Main原生。不保tail先扩摘要输入并取消旧recency/消息下限/重插，不能只事后删tail | 阈值/Force后阈值/手动/Idle/overflow恢复分支；未处理新消息/steer/工具链与摘要外新Framework保真；取消/失败/no-op保原context；live/durable/后续真实请求一致，History原文保留 | 第3节 R10 |
| R11 | 07 v2 §7；白板 P1–P5/N4；07 §3.1/§8.1/§8.13；02 §2.6–2.7/§3.3–3.4；04 §4.5–4.7 | 时序/故障/并发；联合流程 | 仅Idle正常finish+合法提交→父durable压缩→Framework；现有运行任务等正常提交、已有正常可用；failed/forced/overflow/External不能Idle full。其它压缩仍并行不新增门槛。预算/溢出提交合法完整态，一般API失败可无快照 | 正式入口、Force区间去重、D01实际来源、关闭/资格/Profile、rewind/fork、旧Anchor/排队新pointer、失败释放/重启、强制限制通知均保持；Framework非触发不外发 | 第3节 R11 |
| R12 | 07 v2 §1/§6步骤3–5/§8–9；白板 E1/E2/C6/F1/F2/L3/L4 | 内容生命周期；三种外部目标 | 仅可见提案→明确批准→实际成功覆盖结算；来源先Candidate后；全覆盖且无后续变化/未完责任/其它提案需要归档，不留一般有用余额；部分只留未结算范围；失败未知保持；不审外部保管质量、不重建已结算索引 | 真实内容样本覆盖完整/部分成功、后续变化、共享依赖、失败未知和防回流；不能只以模型HTTP200、调用finish或helper测试证明内容符合 | 第3节 R12 |
| R13 | 07 v2 §6.4；07 §8.11第4步 | 精确文本；最小调整边界 | 第4步只将 still-needed scope and necessary context 改为 scope left unsettled by confirmed writes 及理解remaining scope所需context；其余保护不变，不多处额外硬清退 | 对原始Prompt对照，保留四保护、来源与Candidate顺序、失败未知处理；没有额外自动/长度/时间/数量删除门禁 | 第3节 R13 |
| R14 | 索引R14、AGENTS开发闭环/门禁；07 v2 §9 | 流程/交付 | 按冻结依据实施、主会话亲审、有效定向机制及真实代表链证据；独立双门禁顺序，保存历史证据，不以旧通过数替代新方案；提交/部署属主会话后续权限，本审查不执行 | 版本/环境/锁/证据适用路径能追溯；检查规则不变；不触碰其它任务、凭据/生产；本报告完成Verification后才可进入Validation，不能代签最终验收/部署 | 第3节 R14 |
| R15 | 索引R15；07 v2 §9及2026-10-24顶层修订末段；02 §6.16 | 真实接口及语义；隔离Alex/Kimi Coding | 实际Kimi，隔离owner及Alex Persona，N46超过旧N38长前缀，不先缩短再称长样本；真实Main→Noting→压缩→Framework→后续Main，逐请求Root/tools/Active与实际Usage/cache，内容场景含工作/个人/讨论/纠正/有用历史及多轮连续性 | 原始wire/DB/suffix/后续Main和semantic比较可审，少量拒绝错误需统计仍可完成；各真实明确分支必须有证据，mock仅证明机制；无生产资料/阈值污染，无公开Persona/Provider改造 | 第3节 R15 |
| O01 | 索引O01；07 v2 §0及07 §2/§9；01 §1.4；06 §0.3–0.5；08 §1–2 | 范围/架构/兼容 | 不做Web恢复/Android/标题/Provider协议切换/上游Issue/个人Provider；不迁移生产schema。复用原生loop/provider/history/storage/薄客户端；Profile真实owner、只Secretary自有表、原始消息与既有API兼容 | diff与完整接线无额外执行器/存储/调度器/API hierarchy及未授权变更；保留原生Main/aux路径、既有Scheduler/Reminder claim/ACK/冷宿主、非触发渠道边界和人类/notebook临时读契约 | 第3节 O01 |

方向明确而接线薄弱的重点：R01全请求与重试/续Turn；R02间接dispatch；R06派生时间与原有计龄的区别；R09实际生效正文和末尾条件提示；R10取消tail的摘要输入、回插与durable提交；R11正常结束与成功Snapshot区别、Idle与其它压缩；R12语义部分结算和防回流。上述由原文机制必要推出，不要求用户补函数名。

判据修改记录：无；本节为独立初始版本。

## 3. 逐条实现证据

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| R01 | `noting_surface.py:78` apply_main_read_surface → direct catalog (`tools/secretary_dispatch.py:48–90`/tool_search) → native serialization；`noting_child.py:341–414` freeze/build → `cache_parity.py:83–105`；首Task与continuation累加 | 静审完整正式路径；B121五文件真实SDK/Loop证据，固定请求多模态、首轮/工具循环/同child续Turn/冷热恢复；旧short实际26条带tools wire前缀；833续短11个Noting出站wire逐请求Root/tools/Active全部相同、nullable存在，源码651项指纹无差异。独立SHA核对：B17生产文件只有noting_tools变动（F03）；其余16匹配，F03不动冻结/Schema。 | `.hermes-dev/noting-maintenance-v2/b-mechanism-version-{before,after}.json`、`b-mechanism-version-tests.log`；`tests/secretary/test_fixed_noting_request.py:74–173`；本审查`evidence-version-audit.json` | 符合：六定义固定顶层，Task/control无重复Schema，child不改tools；原生重试从同一冻结状态组装，不从父最新态重建 | 真实最终版长样本/Usage归R15；字节一致不等于缓存命中；旧short只按未变源码机制复用 |
| R02 | `noting_child.py:73–106`统一可信身份拒绝→Loop validation、inline、sequential/concurrent/invoke→model_tools.handle_function_call/registry.dispatch；`_bound_store`核工作锁/父域；cache_parity普通delegate减权限 | 强制Main四禁、child其它声明/包装/invoke/prechecked/raw registry、参数伪造及间接桥接负例；拒绝不写Notebook；Main混批保其它原生合法调用。 | `tests/secretary/test_fixed_noting_permissions.py:113–436`；`f03-final-tests.log`82权限＋56child；B121；源码`tools/registry.py:897`、`model_tools.py:899` | 符合：声明与执行分离；Noting恰六工具，Main/普通子Agent不能写，History/Show仍可用；所有任务权限文本一致 | 受控API用于强制走反例，没有以真实模型“未误调”替代权限证明 |
| R03 | `noting_tools.py:68–143` `_mutation_args` → Store.create/update/archive → NotebookWorkingState；finish `:161–199`冻结工作态；runner`:870–920`原生Turn后Commit Gate | canonical三个Schema及实际handler扁平；A243测试原子/no-op/稳定ID；F03最终invoke+Loop非法null/省略/[]/合法null正负例138通过；本审查原独立反证status/relations两项通过（4.6秒测试批的一部分）。 | `.hermes-dev/tools-prompt-v2/f03-report.md`、`f03-final-tests.log`；本审查`independent-old-repros.log`；`notebook_model.py:188–337`；`notebook_items.py:151–232` | 符合：F03已关闭，显式不合法null不再被猜为省略，错误字段准确且item/working零变化；合法null不被新检查拒绝。Finish混批预拒绝、后续写拒绝、不冒充提交 | 内部Store.maintain为兼容helper，当前registry/Schema/dispatch无旧maintain alias；不要求删除历史收据读取 |
| R04 | `notebook_contract.py:15–69,163–233`类型字段/状态/建议；`noting_contract.py`三完整Schema；items hydration只投影退休字段，底层旧版本JSON不改 | 七类新必填及八类型最小合法/nullable、Candidate refs或确切UID、gap→situation、非法字段/类型/来源/引用等真实SQLite验证；静审模型投影与来源继承许可 | A243 `.hermes-dev/notebook-data-v2/final-suite.log`；`test_notebook_maintenance_v2.py:72–202,284–345`；source SHA9/11匹配，两变化由F01定向26覆盖 | 符合：字段必填性与validator一致，无external_refs、schedule_refs或独立材料字段；未知不被validator补造；Candidate原有约束保持 | 人类材料取舍与用户归因由Prompt和真实语义样本另核，结构测试不证明语义支持 |
| R05 | `noting_prompts.py`完整七步与独立第三/第五类型指导→`_working_control`/实际Task wire；description逐段与v2§6.1对应 | 静审完整Prompt、Main/Tool/continuation；B真实构建文本断言只证明组织/注入；旧short真实内容保偏好/身份/紧张/信任/未采纳合并方案/纠正。但新增进展entry1/2/3没有对应新来源（F04）；833最终Snapshot仍未补齐，entry4新确认容量也仅引旧未知来源 | B121；`test_fixed_noting_request.py:172`；旧short`snapshot.json`、833续短`snapshot.json`及本审查`short-provenance-audit.json`/`resume-833-audit.json` | **违规（F04）**：真实当前833已提交结果保留了无对应支持来源的新重要断言；Prompt组织/注入符合，但实际内容契约未满足。不能因源UID结构合法就当作支持此新断言 | 未因单样本失败断言整个模型永不合规；也不因可能随机遗漏忽略本次已观察的契约缺口 |
| R06 | `readable_notebook_entry`→`notebook_evidence.evidence_time`；Show/初始/续Turn/单条回执/Framework全传owner DB/ref/state；可信Instant排除只影响真实user优先级 | runtime UID优先range，真实user组→最近assistant→全部；range-only/unknown/refs链；F01来源owner/UID/body精确持久证明，branch与外域同UID正文防借证，保真人wrapper/steer；26定向及本审查原正式Admission反例1通过 | `.hermes-dev/notebook-data-v2/instant-receipt-final.log`、`instant-receipt-sha256.txt`；本审查`independent-old-repros.log`；源码`notebook_evidence.py:22–125` | 符合：F01关闭，readonly顶层投影不改变版本或原文，不用now补未知；progress/discussion/created_at计龄保持。当前证据组时间不被代码写回首次年龄 | F04是模型遗漏新增支持来源，不能把runtime按实际旧来源正确派生的时间称为另一个runtime算法错误；真实模型provenance质量阻断R05/R15 |
| R07 | `NotebookWorkingState.archive:279–337`草稿受保护引用检查/普通relations清理→`NotebookStore._insert_versions`同DB事务→immutable row→成功后换working；items source_basis仅允许已证archived target的关系删除 | 真实SQLite清理完整回执/new version、受保护引用整批零变更、第二INSERT失败回滚、off-path继承只准删原关系；恢复按updated_entries精确版本重建 | A243及`test_notebook_maintenance_v2.py:248–345`；`noting_recovery_sources.py:70–100`；`notebook_store.py:165–184` | 符合：普通关系自动解除；gap/Candidate仍保护，没有半归档、悬空或业务状态级联；旧快照保持原版本 | 不把结构引用合法当关系语义真实性推断，不新增DAG/数量门禁 |
| R08 | create/update顶层单对象→validator普通两字符串→item/Snapshot→working投影；Task第6步必查登记缺口；Noting Scheduler硬拒 | A243全类型单对象/替换/null/no-op/unparsed字符串机制成立；旧short首轮自包含A17建议和后续Main实际登记成立；F02 transport修补保官方Coding nullable，111 SDK/原生assembly/fallback测试；833真实工具null清建议success/changed，随后合法finish_noting Snapshot建议数0已核 | `notebook_contract.py:210–225`；`noting_prompts.py:64`；`.hermes-dev/noting-maintenance-v2/nullable-probe/{version.json,tests-final.log,corrected/wire.json}`；旧short目录；833续短wire002、events、snapshot及本审查`resume-833-audit.json` | 符合：F02已以833正式Noting null调用成功及Snapshot持久结果关闭；建议单对象/语义字符串/必要Task指导成立，首周期自包含建议到Main登记可复用。被审计截断的后续压缩/Framework另归R15，不冒称全链完成 | 旧short第二轮8次空串清除拒绝历史保留；不能改为空串猜null或放宽validator |
| R09 | pointer-winning commit→`publish_noting_completion`→`append_runtime_row.prepare_completion`同事务重新取有效Snapshot→`completion_body:18–47`末尾条件advice | 建议存在/无建议/clear、超限Proposal之后仍最底部精确三句；Framework producer→safe append，未增加adapter/Turn；pointer改动/队列失效事务保护沿原路径 | B121、`test_schedule_suggestion_framework_v2.py`；`framework_messages.py:133–222,333–357`；旧short`framework-{live,durable}.json` | 符合：条件完全根据实际将注入Notebook，不按旧base判断；只考虑创建/更新，无强制照抄或权限扩大 | 最终模型是否按实际注册清建议归R08/R15；Framework本身非触发、不外发保持 |
| R10 | 正式turn-start/pre-API/post-tool真实threshold分类→`_run_summary_phase`attempt-local policy→built-in摘要输入window/prune→候选anchor→原生commit→publication真实DB读回 | C44覆盖full/native/off/nonMain/child/partial、三个阈值seam、overflow/maintenance、pending多请求/图片/steer/tool、新消息in-place/rotation、取消/lease/commit/summary失败/no-op/growth；Force18及native302仅复用相关有效分区。policy仅EOF空行差异独立重算旧SHA成立 | `.hermes-dev/compaction-policy-v2/{targeted-final.log,force-final.log,native-regression.log,source-sha256.txt}`；`test_noting_tail_policy_v2.py:52–310`；本审查版本审计 | 符合：按真实阈值原因保tail，其它先纳入摘要且禁旧回插；显式here1保指定tail；live/durable/后续request一致，失败不清尾，原文保持 | built-in本地macOS实测；未将自定义ContextEngine或远端Codex压缩宣称新增已验；D01 External仍维持原生必须压缩，不新增执行器 |
| R11 | Main timer/原生压缩seam→D01→admission同区间→spawn frozen child；normal commit association→Idle callback等待durable；其它压缩并行；异常结束合法Snapshot/真实失败通知 | 静审child、noting_runtime、noting_compact、hermes_state_secretary_noting/Notebook、Framework完整上下游；C44两真实built-in Idle in-place/rotation；19正常/异常＋24复用＋42Framework分区；B96/56child覆盖预算/失败/恢复 | `.hermes-dev/compaction-policy-v2/idle-framework-previous-run.log`；`test_noting_tail_policy_idle_v2.py`；`noting_child.py:155–228,795–919`；`noting_compact.py:21–60` | 符合：Idle只接受相应正常finish＋合法commit，forced/overflow/API失败/External不压；一般API失败不伪造Snapshot。Force区间占用不因失败/rewind解；old Anchor/pointer/queued superseded仍按合法路径 | 实际Kimi最终Idle时序另归R15；不承诺内存Framework队列跨重启必达；同Conversation并发草稿无自动合并要求 |
| R12 | Task第3防重建＋第4真实批准/写入范围结算＋第5类型生命周期→archive/update/Candidate引用保护→真实Snapshot | 对Step4原常量精确比对；旧short真实Noting按合成持久工具成功轨迹归档完整insight6及Candidate7，保action3未覆盖责任/后续进展并去规则余额，未查外部文件。833第二Noting已正常提交，旧insight6/Candidate7未重新入簿，未覆盖报名责任仍在entry3 | 本审查`prompt-step4-audit.json`；旧short`settlement-fixture.json`、`snapshot.json`、child transcript；`tests/secretary/test_candidate_settlement_lifecycle.py` | 符合：真实Noting完整/部分结算、后续变化/未完责任保留及第二Noting不回流可核；失败/未知不结算及共享依赖由受控生命周期测试和原文Prompt共同覆盖。最终多次压缩后Main仅读Notebook结果仍归R15 | 外部写入轨迹是明确合成fixture；没有实际外部写副作用，不能称真实Provider外部存储已验；规格只要求Noting据可见轨迹结算 |
| R13 | `noting_prompts.py:36`第4步 | AST提取冻结原常量与当前常量，除三工具必需替名、批准短语替换外逐字相同；结果true，保存两份原文 | 本审查`prompt-step4-audit.json` | 符合：四种保留保护、来源先Candidate后、失败未知/不审目标保管全保留；没有新增多处硬清退/到龄删除 | 精确静态文本证明，不代替R12真实语义 |
| R14 | 冻结Index/基线→三包Sol→root亲审/版本提交→独立初审/复审/本最终复审；质量检查及阶段状态 | 本审查独立先判据；产品833版本树一致；F01/F02/F03原红样本保留，补证按SHA分区；最新冻结10checks、63代码文件health0/0；uv.lock未动 | `.autonomous/.../{snapshot-index,baseline,plan,verification,reverification}.md`；`.hermes-dev/noting-maintenance-v2/f03-quality.log`；本审查`evidence-version-audit.json` | 符合（Verification前置流程）：实际证据/源码适用边界可追；没有降低规则、个人/凭据/生产污染；本报告不代签尚未执行Validation/最终交付/部署 | 整轮完成和部署仍属后续门禁/主会话判定，本行不意味着本轮已完成；当前必须继续补E00/F04 |
| R15 | 隔离Alex/Kimi实际原生Main→Noting→Snapshot→durable压缩→Framework→后续Main；N46超过旧N38 | 旧short首周期机制可复用，第二周期原失败不抹；nullable probe只证明传输能力。833续短13HTTP均200，其中12个完整Provider响应、11个Noting请求、null真实清除与正常Snapshot成立；审计SIGTERM截断summary，无新Framework/最终Main；N46实际0请求 | `.hermes-dev/noting-maintenance-v2/e2e/e2e-report.md`（旧失败报告）；本审查`short-provenance-audit.json` | **证据不足（E00/F04）**：必要最终压缩→Framework→后续Main及N46长前缀未执行完整，且F04真实内容失败，明确不PASS | 本审查0收费请求、无UI/生产/云；不从HTTP200或正常finish外推语义完整 |
| O01 | 全轮生产diff与本次上下游：Notebook/Prompt/原生压缩策略/官方Coding现有schema兼容窄修补；未动Web恢复/Android/标题/个人Provider | 比对冻结→833的68文件diff（含测试/报告）；无生产schema迁移、路由/协议切换、第二loop/存储/通用调度器/API hierarchy；继承owner/Profile和原生History/Reminder/ACK路径保留，nullable route只opt-in可信官方Coding | `git diff --stat a4faa767e6 833277e8`；`agent/moonshot_schema.py`/chat transport；`tests/agent/test_kimi_nullable_wire.py`；质量日志 | 符合：未扩本轮边界，保原生/非Main/关闭路径与既有API默认调用，依赖锁不变 | 生产既有desktop来源微信busy Instant独立缺口不是本轮变更，未冒称修复；未代做Web/Android/其它平台实测 |

## 4. 核心目标及验证方法审查

六工具固定声明、可信权限、三维护工具、只读时间、关系原子清理和无默认tail均已追踪正式路径，不只查新helper。受控SDK/真实SQLite测试没有替换待测NotebookStore、Commit Gate、built-in摘要窗口、原生publication或Framework事务；受控内容只用于确定地强制触发分支，不证明真实模型质量。R05/R08/R12/R15仍以实际Kimi样本判，HTTP200、结构正确和Finish不足以签语义通过。

证据版本审计自行重算，结果见本审查`evidence-version-audit.json`：A原243包11文件9匹配，只有evidence_time及相应测试后来F01修补，两份最终SHA完全匹配26项及原反例；C9文件8精确匹配，policy差异只有一个EOF空行，补回换行可重算原SHA；B前后17文件16匹配，唯一变化noting_tools是F03七行，已核当前精确SHA与最终138项/原2反例；F02六文件全部精确匹配，111测试及真实探针可复用。旧B121不被宣称为当前F03全部证据。native302仅复用未改变的原生路径，不为审查再跑。

本审查额外只运行三项既有独立失败反例：真实Scheduler→Instant Admission→durable witness→Notebook取时一项；正式child invoke非法status/relations null两项。经规定runner在833精确代码上3 passed，4.6秒，0失败。测试保持真实DB/正式入口，非wrapper文本猜身份或镜像实现。后继F04通过只读证据DB/原文与Snapshot语义对照取得，证明本审查没有照搬两份旧报告的“无新缺陷”预期。

核心反证已检查：工具广告不能授权Main或child其它工具；结束请求不能变Snapshot收据；归档保护失败不能先清普通关系；来源继承不能支持新断言；无默认tail不能只事后删而跳过摘要；前后request/live/durable必须一致；Forced合法提交不能变Idle成功；重读已结算素材不能重建。F04正落在来源支持与实际模型语义的剩余缺口，需独立关闭。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| E00 | R15 | 833真实续短正常null清除/Finish/提交已核，但审计SIGTERM截断第二摘要，无对应新Framework/最终Main；N46实际0请求 | P1证据缺口；明确完整真实链与长前缀要求未闭合，阻断Validation | 最终受测版本补压缩→Framework→后续Main及N46，核原始wire/Usage/DB/语义，已有机制/首轮样本仅按变化影响复用 | **证据不足**，不能提前PASS |
| F01（历史） | R06 | 正式无display_kind Instant错误优先真人；本版按原物理owner/UID/body匹配既有receipt排除，仅影响真人优先组 | 原P2已修；无新身份/来源授权 | 当前精确SHA、26定向、原正式Admission反例1；本审查再次复验1通过 | 关闭（机制），保留原失败历史 |
| F02（历史） | R03/R08/R15 | 旧Coding sanitize删除nullable导致真实清建议8次失败；当前仅官方Coding可信URL opt-in保canonical nullable | 传输机制与833正式工作态null清除/正常Snapshot已证，剩余完整链归E00 | 六源码SHA匹配、111原生/SDK/fallback、纠正probe成功；833续短11wire nullable全保、真实null更新success、正常Snapshot建议数0 | F02关闭；833被审计截断的完整代表链E00仍不足 |
| F03（历史） | R03/R04 | 新create显式非nullable null原被内部None默认吞掉；当前wire层按canonical单一非null type拒绝 | 原P2已修；内部Store默认兼容/合法null保持 | 当前noting_tools SHA`bb153e97…`、最终权限/child138；本审查原独立反例status/relations两项通过，working/item零变更 | 关闭，不追改历史两失败 |
| F04（本次新增） | R05/R06/R15；冻结白板 I2“每一项重要断言必须有可定位来源”、07 v2 §6.1第二步；`noting_prompts.py:25` | 独立查旧short首轮及833最终续短Snapshot与只读证据DB：entry1/2/3写入饮水到货、记号笔未买、四人已核2剩2，但来源仍仅为原目标/原采购单/原分场决定；最新进展真实用户UID `0b3878cf689a42f097c95eb62af6cdae` 未进三者来源，source_time_range也均null。原引用文字不支持新增进度；entry4新确认容量40人亦仅引旧未知消息 | 新增重要断言无法从条目provenance定位，派生证据时间也停留旧来源；旧short不能无保留代签完整内容质量。此为真实模型行为，不是结构validator要求推断语义 | 833已确认仍未补齐；主会话提出基于既有来源契约的处理/补证方案，独立评审，不新增语义硬门禁或追改旧证据 | **违规，P2阻断**；当前真实已提交样本不满足对应来源支持。待主会话方案；证据`.hermes-dev/noting-v2-final-verification/short-provenance-audit.json` |

范围外发现：无新增。本轮没有执行收费模型、访问凭据/生产/云、UI控制、提交/push/部署，也没有修改产品/测试/规格/主文档。只读证据DB为已授权隔离副本。

## 6. 修复与独立复审

本审查为全新独立全轮最终复审；第2节先独立落盘，再审全轮diff/正式上下游及旧报告。待审833静态机制未发现新增产品代码缺陷；F01/F03以原失败反例在当前版重验关闭，F02以真实null更新/正常Snapshot关闭；F04为当前真实内容违规，E00为完整真实链与N46缺证。全部初始判据保持，未为实现降低标准，无规格变更。没有退回缺行报告的历史。

F01：原判据真实用户优先→正式Instant原反例→主会话既有receipt精确证明提案→前复审认可→本次独立读SQL owner/UID/body及继承路径，并重验真实Admission反例，通过。只改变时间投影分类，不改原文/metadata/权限/计龄。

F02：原判据null清除→真实旧wire删除null/8次失败→主会话官方Coding精确路由opt-in保nullable提案→独立核源及可信URL/fallback、原生kwargs、SDK出站；Probe第一次配置400及纠正200/null均保留，不以能力probe代正式清建议。随后独立核833续短11个Noting真实wire全部保nullable，合法null更新success/changed、正常Snapshot建议为0，故关闭F02。审计者截断随后摘要不能冒称第二全链完成，E00仍阻断。

F03：原判据非法参数零副作用→前独立两项反例实际create→主会话wire canonical单一非nullable type拒null七行提案→本次独立核handler/Store及正负对照，复验原反例2通过。只实现既有Schema，不增加产品语义或硬门禁。

F04：本次独立将旧short真实Snapshot的新增重要进展逐条对照所列来源，发现原文不支持新进度且最新进度UID未列。依据冻结白板I2、v2第二步对应来源要求落盘后交主会话；833最终Snapshot亦确认未补齐，主会话已认可漏源事实；未修复，待主会话提案。不能用结构来源合法/模型HTTP成功代替支持语义，也不建议为此自行新增推断性代码门禁。实质发现及最终收敛须由主会话在final-delivery和用户最终汇报摘要，旧样本保持失败/局限原貌。

当前门禁：**不通过（R05/F04违规、R15/E00证据不足）**。静态/机制结论及历史修补关闭不代表整个目标完成；不进入Validation前置通过声明。

### 主会话新增提案评审：成功Finish后不再发模型请求

主会话交接：833续短已实际null清建议、首次合法Finish及8次幂等重复；原生Turn最终自然返回并正常commit；审计者提前SIGTERM截断其后摘要，不能把审计中断伪报为runtime结束违约。收费已停43/70，N46尚未执行。交接后本审查已从原始wire/events/Snapshot独立确认，详见`resume-833-audit.json`；F02关闭，完整链E00不足。

主会话提案：在既有原生tool-round结束接缝，仅对可信Noting已接受首个合法独立Finish的情况，完成本工具批次结果追加/持久化后，沿原生loop break/finalize正常返回；runner仍在Turn返回后Commit Gate提交。不改Schema/description/Prompt、不在finish里提交，不改非法/混批/Main/普通child/forced/overflow。

Verification依据原判据R03/R11及07§4.5评审：**方向属于既有契约的接线细化，不必为这一机制另改产品完成条件**。原文明示Finish最后独立调用后停止，接受end_requested与最终Snapshot提交两阶段；它没有要求成功Finish后必须再发模型请求或等待模型再说一次完成。可信首合法Finish停止原生tool-loop、完整落下工具结果、正常Turn返回后再提交，恰可同时满足这些约束。不能把finish handler内直接commit、伪造模型final、绕过原生finalization或取消/owner保护混入该提案。

关闭须提供最终版本正式SDK/Loop/SQLite证据：首合法独立Finish后模型HTTP/SDK请求增量为0，工具调用与成功结果先完整持久，正常Turn返回后仅一次Commit Gate，Idle再durable压缩再Framework、资源释放；非法reason/混批不结束且整批无副作用；end_requested后的写拒绝、重复finish幂等；Main/普通child仍走原生，forced/overflow/API失败标识不变；同步/并发调用与owner/取消/提交失败路径不越权不伪成功。收费代表链若在新版本取得，须绑定新SHA；833旧语义和nullable取证按影响保留，不能将43请求或审计SIGTERM重写成新版本正常全链成功。修补如实施，套件仍要求全新独立全轮复审，本审查不代新版本最终PASS。
