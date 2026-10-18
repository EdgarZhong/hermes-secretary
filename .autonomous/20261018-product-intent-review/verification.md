# Verification：20261018-product-intent-review

## 1. 审查对象与结论概览

**结论：不通过，尚不能宣布产品按最新意图交付。**本包独立建立 31 条产品要求，覆盖公开核心、独立 UI 和个人 NM 当前使用链。确认 3 个实现缺陷（F01–F03）；发现 2 项规格问题（S01–S02）；另外列出模型行为/正式接线的证据缺口及必须保持显式的产品取舍（E01–E05、Q01–Q03）。不把缺证写成代码失败，也不把已有代码写成真实使用通过。

本报告是独立 Verification，不参与实现或降低判据；遵循 autonomous-run / spec-implementation-review 六节模板，并以本轮用户指定的最新产品文档/口径覆盖旧“技术规格最终权威”顺序。先完整阅读产品原文、身份参考与部署 SOUL，再写 §2 v1；收到固定源码清单后才读技术规格、代码、看板、历史证据。未读 Default 私人正文/凭据、未写 NM、未派生、未改产品代码/Prompt/配置、未提交或重启，未进行屏幕/浏览器操作。

| 对象 | 本次审查版本（HEAD 只是来源标签，必须连同 dirty manifest） | 固定目录与完整性 |
|---|---|---|
| 公开核心 | `63761bd5d324b45437a5cf307e10915b4e20524b` + 捕获 dirty；manifest `542965d5eb76bda2f516a8d47219c35a4bba3eb601f81e588001b1126879e235` | `/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary`；18008 个清单文件 SHA 全部一致 |
| 独立 UI | `7f0fea60463c6731f8e04a00db923d28b80ade19` + 捕获 dirty；manifest `c2b95d767e2c0c3dfc6b5e5ea46f1f07028a0bf2b7677aac1d244d4e227d01ab` | `/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web`；156 个文件一致 |
| 个人 NM | `1eb8d9a2a4e81101255ee8ae3998275ab608e52f` + 捕获 dirty；manifest `828007e515a26b6388f692ec5e063f189ff124361a82f4154a0a78d333bca410` | `/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider`；699 个文件一致 |

Snapshot set SHA256：`ac550269de3b02303ce30d1d0bd74c72edebedbd3c2eaca74d1302358ffb2220`；封存时间 2026-10-18 07:47:35 UTC。[完整指纹核对](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/verification/frozen-integrity.json)及[产品输入指纹](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/verification/input-fingerprints.json)为可复查证据。移动工作区后来 HEAD、baseline.txt 后续变化、运行进程旧代码均没有代替这个版本。散列全树是完整性核对，不意味着逐文件语义审计了所有上游能力。

## 2. 独立要求清单与覆盖

本节 v1 在实现调查之前建立。`P:Lx–Ly` 指本轮冻结 `product-intent.md` 行；`PI-xx` 指 snapshot-index 中用户明确口径；`I` 指身份参考（仅身份/表达，不继承 Pi 工具、写权限、调度职责）；`S-main` / `S-exam` 为两份部署 SOUL，属于待对照材料，不是高于产品的要求来源。未引用个人原文。以下“必要推导”约束产品结果，不指定函数、存储或线程方案。

三种判据层次不能混淆：**当前机制/权限/明确行为**可以检查是否落实；**模型行为目标**检查 Harness 是否支持、是否存在反向诱导并查代表真实样本，单次自述不足以通过；**长期愿景**不要求本轮完成完整治理平台或证明数月可靠性。对实际证据的不足与产品未来范围分别列明。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| R01 | P:L11–31、L71–97、L294–304；I：完整个人生活的长期通用助手 | 当前身份与行为方向；主助手、专职角色 | 直接要求：学习/工作/生活/认知/情绪/自然交谈均为合法输入；不能把 Coding、企业任务或日程当唯一角色 | 实际拼装的主助手上下文与工具指引不把身份缩窄；学习、自然交流、实际事务都有正式入口；不能只检查 SOUL 文件本身 | §3 R01 |
| R02 | P:L25–29、L75、L125、L169–171、L195；I：独立、诚实、清晰 | 当前对话行为与身份 | 直接要求：区分交代事务、随口分享、探讨、答疑、倾诉；不将全部输入转为任务，不冒充治疗师；必要推导：Notebook 的候选整理不能强迫主助手认领责任 | Prompt/结构不要求每轮产生任务/建议；真实样本覆盖倾诉、探索和明确请求的差异；观点、未知、用户决定可区分 | §3 R02 |
| R03 | P:L37–43、L51–65、L268、L296 | 当前核心机制：长期 Conversation | 直接要求：Conversation 可持续，不被 Session 容量/寿命迫使重开；必要推导：压缩/上下文轮转不能改变其身份、归属、可访问历史或已接受责任 | 追踪正常对话、容量压缩、Idle Compact、重启恢复后的同一 Conversation；用户不必自行搬运摘要/重述背景；失败可恢复且不静默失联 | §3 R03 |
| R04 | P:L59、L63–65、L69、L89、L300 | 当前组织自由与数据模型 | 直接要求：Session、Conversation、Profile、Memory Space 不等同，不强制一一绑定；三角色只是个人安排 | 同 Profile 多 Conversation、多个 Profile、独立 Memory Space 选择不会被缩成唯一主助手/固定三空间；不能从当前两 Profile 部署推导产品只能两个 | §3 R04 |
| R05 | P:L101–103、L228–230；PI-01 | 当前历史互搜与边界 | 直接要求：同 Profile Conversation History 可检索其它 Conversation；跨 Profile 历史共享不因该能力自动开放 | 正式历史工具能定位同 Profile 历史与原文；所属 Profile 约束覆盖检索、读取与后台路径；主助手跨领域读取走 NM，不读另一个 Profile | §3 R05 |
| R06 | P:L109–113、L189–190、L260 | 当前记忆连续性机制与模型目标；薄弱接线项 | 必要推导：信息可留存、可发现、可回到语境，不能仅“数据库里还有”；相关重要背景须有模型能理解的入口，压缩不能只剩不可解析指针 | 检查历史→Notebook/摘要→后续上下文→按需原文检索整链；覆盖话题切换、久远背景、重复压缩、空结果/错误；样本不把不存在的回忆编成事实 | §3 R06 |
| R07 | P:L117–125、L191、L264；PI-08 | 当前责任连续性；薄弱生命周期项 | 直接要求：只对真正接受事项保留目标、原因、状态、阻塞、下一步和行动边界；必要推导：待用户、失败、部分完成、未触达不能被当成全部完成 | 正式状态变化与清理条件保留未完成责任；跨压缩、重启、唤醒仍可恢复；无“已提案即已完成”、遗漏依赖或仅靠用户重提的路径 | §3 R07 |
| R08 | P:L129–133、L192、L226–227 | 当前 Agent Reminder 机制与每日行为约定 | 直接要求：Agent 可创建 Instant Reminder 自行唤醒；至少24小时一次是行为约定，不是本轮要求新增代码强制器 | 模型实际可见行为要求与可调用工具；调度/投递/恢复正式接线有效；失败、重启、并发不会吞掉已承诺唤醒；不因缺强制守护器单独判违规 | §3 R08 |
| R09 | P:L133、L159–171、L194、L200、L280 | 当前主动性与负向行为 | 直接要求：唤醒不必通知，不得扩大授权、制造任务或用联想替代用户目标；必要推导：静默完成检查与应提醒却漏提醒须可区分 | 上下文/调度协议允许无变化静默；有接受责任时具备继续处理与需要用户时触达路径；真实样本同时观察过度行动和应该发生却未发生的动作 | §3 R09 |
| R10 | P:L143–147、L153、L193、L284；PI-08 | 当前真实性约束（不要求完整长期治理平台） | 直接要求：原始材料、用户确认、历史结论、当前推测不能混同；必要推导：摘要/Notebook 不篡改事实来源、不将模型生成文本伪装用户证据 | 检查原文保存、摘要/笔记来源、更新和压缩关系；纠正/撤回优先于旧结论且不抹掉必要条件；受控用例与真实样本能揭露建议→事实污染 | §3 R10 |
| R11 | P:L141–155、L231、L302 | 长期治理方向及当前已有溯源能力 | 直接要求：希望可追原始依据，但全文审计/决策演化并未声明完成；必要推导：当前已有 ref/来源入口必须真实有效，不能制造虚假追溯 | 对现有来源链验证能落回正确原文而非另一轮摘要；缺完整治理系统有依据不适用；无法恢复的事实诚实呈现，不能声称已全面实现 | §3 R11 |
| R12 | P:L183、L198–210、L238–254、L288 | 当前验收与长期观察边界 | 直接要求：验证支撑预期而非追求演示/更多权限；不把单次验证当长期良率，不要求用户每轮打分 | 真实样本有具体预期/工具结果与局限；报告不以模型自评定成功，不照搬外部 benchmark；无为了监控而增加强制用户操作 | §3 R12 |
| R13 | P:L77、L103、L216、L229–234 | 首版范围边界 | 直接要求：正式跨 Conversation 委托、责任/状态协调及通用跨 Profile 互通为未来；外部产品仅参照 | 无越权协作/共享；不因缺下一阶段功能判当前缺陷；PI-01 指定 NM 只读互通作为明确例外单独检查，不扩成通用代理总线 | §3 R13 |
| R14 | PI-01、PI-10；P:L59、L89 | 当前个人部署与原生身份机制 | 直接要求：两本机 Profile，主助手/考研各自身份，真实 NM 插件，Noting 开启；必要推导：后台与新会话仍使用所属 Profile 的身份和权限 | 只查获授权配置元数据/工具面/运行证据，不读 Default 正文；Profile 的 model/SOUL/provider/插件/Noting 选择一致，不能由启动进程的默认身份串用 | §3 R14 |
| R15 | PI-01、PI-08；S-main/S-exam 作为对照 | 当前 NM 数据归属/权限 | 直接要求：主助手 Default 只读且可读考研 Space，不读另一 Hermes Profile；考研仅获授权 Space 操作；必要推导：后台同步、工具、插件入口不能绕过相同边界 | 查 Memory、Thread、资料/规则/治理及自动写入路径的范围；读取指针不等于读正文；测试用 fixture/隔离结果验证拒绝与错误，不实际读取私人正文 | §3 R15 |
| R16 | PI-08；P:L145–147、L196 | 当前 Memory 写入授权 | 直接要求：真实 Memory 需具体内容和目标明确批准；提案、措辞修改、沉默不授权；空间写权限不是每条内容的批准 | 从候选/提案/用户确认→实际调用→持久结果追踪；歧义/目标变化/执行失败不冒称成功；不能由广泛身份规则或插件默认设置扩大本次授权 | §3 R16 |
| R17 | PI-08；P:L117–125、L147 | 当前来源结算与 Candidate 生命周期；薄弱机制项 | 直接要求：先结算真正成功交付覆盖来源，再关闭 Candidate；保留未覆盖责任、纠正、其它依赖；必要推导：聚合候选不得按“某次写成功”整包清除 | 对部分来源、多目标、多依赖、后续纠正、失败重试逐条追踪交付事实和关闭时点；成功写入的内容/目标必须与被关闭来源相符 | §3 R17 |
| R18 | PI-02、PI-03、PI-04 | 当前测试方法与环境 | 直接要求：真功能实测，DeepSeek 是代理模型；10分钟代表一天且不改系统时钟；普通 user message 带测试说明；双 Profile Idle Compact+Noting，阈值100000、idle当前5秒，不改模型容量 | 复用实测证据须证明实际配置、模型/API、输入前置说明及持久结果；人工强触发/helper 不能冒充自然 idle；部署 SOUL 无测试尺度 | §3 R18 |
| R19 | PI-05；P:L111–113 | 当前模型可见上下文可读性 | 直接要求：不给 Hermes AI 展示内部 Snapshot ID/Coverage anchor；必要推导：隐藏审计值不能把 Notebook 内容或有意义覆盖说明一并移除；模型需要有效历史来源/操作对象 | 检查真实 system/context/tool result/压缩/Noting 完成注入的全部模型面；内部元数据保持内部；人类 UI 脱敏不能替代模型面清理；有用来源身份仍有效 | §3 R19 |
| R20 | PI-09；P:L43、L196 | 当前 Prompt 修改与可观察性 | 直接要求：写死 Prompt 不因审查自行改；只本次明确标识清理获授权；必要推导：发现与修复权限分开，不能用改判据迁就实现 | 对 Snapshot 差异核对已授权范围；报告以原文/实际上下文判断偏离，不自行调整 Prompt；冲突列为产品取舍/待主会话方案 | §3 R20 |
| R21 | PI-06；P:L59 | 当前 UI Profile 选择 | 直接要求：首页独立下拉，不能混入 model selector；改变新 Session 的原生环境、model/SOUL 随 Profile | 正式首页 UI→新 Conversation/Session 创建→后端 Profile 解析完整接线；刷新/冷启动/选择竞争不产生显示选择和实际归属不一致 | §3 R21 |
| R22 | PI-06；P:L51–65 | 当前 UI 既有 Conversation 归属 | 直接要求：已有 Conversation 保持原归属；首页切 Profile 不应改变旧对话身份或过滤掉别的 Profile 会话 | 选择 Profile 后打开/发送/恢复旧 Conversation 仍走其原环境；侧栏跨 Profile 展示；不可仅新建正常、恢复路径仍串用当前选择 | §3 R22 |
| R23 | PI-06 | 当前 UI Profile 图标 | 直接要求：图标来自每条 Conversation 所属 Profile，前端固定映射，不增配置 | 首页切换、历史列表/刷新/搜索后的图标依据会话归属；不存在依赖当前全局选择或新增用户配置的分支 | §3 R23 |
| R24 | PI-07 | 当前 UI 流式 Thinking 与工具状态 | 直接要求：首个 Thinking 流式期间可见；工具卡无瞬时假错误；完成高亮准确 | 检查首包、并发/顺序工具、完成/失败/中断、恢复流与重绘状态；实际错误仍可见；只最终静态截图不足证明流式体验 | §3 R24 |
| R25 | PI-07 | 当前 UI 提示生命周期 | 直接要求：普通提示统一5秒，错误手动关闭 | 所有正式提示入口与错误分类一致；错误不被统一计时自动清；成功/普通提示无永久残留或不同默认时长 | §3 R25 |
| R26 | PI-07 | 当前 UI 上下文统计 | 直接允许：冷启动沿上次可信统计估算 Context/Session Total；必要推导：估算不能伪装新的实际统计或串会话统计 | 统计与 Conversation/Session 归属、压缩后的关系可信；未知/估算/实际值语义一致；读取/展示失败不阻断对话 | §3 R26 |
| R27 | PI-10 | 当前原生一致与 API 兼容 | 直接要求：Secretary 关闭保持 Hermes 原生行为，尊重原生 Profile/Session/model/provider，新增 API 兼容 | 对关闭、非适用、纯原生分支检查实际接缝；旧客户端必填/默认/返回语义不改变；新展示/估算失败不得改变原生核心执行 | §3 R27 |
| R28 | P:L53、L109–125、L129；PI-10 | 当前失败/恢复/并发；由连续性必要推出 | 不能保证外部服务永不失败，但失败不得产生虚假交付、永久丢失责任、串 Profile 或不可解释的重复；结构/时序保证比下游补救更可信 | 覆盖压缩/Notebook 更新与消息并发、后台重启、模型/工具失败、Reminder 重试；隔离用例可证伪“只 happy path”实现 | §3 R28 |
| R29 | P:L37–43、L198、L210、L268–290 | 当前整体管理负担；薄弱跨层项 | 直接要求：减少重复解释/上下文管理；必要推导：不能为自动机制要求用户经常操作 Session、修复内部 ID、手工补记或自行协调后台执行 | 从主要正式入口审查用户必须完成的管理动作、故障恢复提示与缺省行为；把依赖用户补偿的断链列明，不仅验证孤立 helper | §3 R29 |
| R30 | P:L189、L193、L196；I；S-main/S-exam 作为对照 | 当前纠正、未知与语音输入理解 | 直接要求：新要求/纠正生效，不假装记得、不虚构进展；身份参考要求结合上下文理解转录误差，不将一次口误固化 | 当前上下文/Notebook/NM 读取可区分已确认新口径与旧状态；检索空/失败明确区分，不以无结果推断用户未行动；代表纠正样本有后续检查 | §3 R30 |
| R31 | P:L9、L179–210、L238–254；PI-02 | 本轮证据有效性与模型能力界限 | 直接要求：模型实测检查支撑；必要推导：受控替身只能证明机制、代理模型样本不能证明正式K3长期行为；目标模型可见上下文必须真实 | 证据固定版本、实际入口、配置、输入/输出、工具与持久结果相互对应；区分代码缺陷、规格冲突、证据不足、模型单样本局限 | §3 R31 |

覆盖反查：产品第1章→R01/R02；第2章→R03/R06/R07/R29；第3章→R03–R05/R13/R21–R23；第4章→R06–R09/R28；第5章→R10/R11/R16/R17/R30；第6章→R02/R09；第7章→R12/R29–R31；第8章→R13；第9章→R08/R11–R13；第10章→R12/R18/R31；第11–12章→以上连续性/组织自由/真实性/负担条款。用户 PI-01→R05/R14/R15；02→R12/R18/R31；03–04→R18；05→R19；06→R21–R23；07→R24–R26；08→R07/R15–R17；09→R20；10→R14/R27/R28。身份参考仅支撑 R01/R02/R30，不继承旧运行平台、工具、记忆默认写权或调度安排。

尚不能从产品文档定案的解释保留：①并未规定所有长期治理的完整功能本轮上线，不把完整审计/纠错 UI 的缺失默认判违规；②多 Space 的通用权限产品尚未定案，只审 PI-01 这次明确配置与隔离；③每日 Reminder 是行为约定而非代码守卫，不发明全天运行承诺；④行为样本需有代表覆盖但原文没有给固定成功率/次数，不自设良率硬门槛。若实现调查发现会影响用户预期而上述原文不能唯一裁定的取舍，在 §5 列原文、分歧和最小问题。

判据变化记录：v1（2026-10-18，实现调查前）为独立起点；本版暂无后续变化。


**v2 澄清记录（进入源码审查前核对最新固定索引）：**最新 authority index SHA256 `fba5f2677a4e329e869ce9ec6a12d8bde1b8d49b58b8018b3253d89ee397a0dd` 只补 PI-11 和 PI-01 的实测授权语境。R14–R16 中双 Profile、Default 只读、考研 Space 操作是本轮实测边界；不能把它提升为永久人格、通用 Space 权限模型或正式部署写授权。SOUL 的可直接部署性仍须独立对照 PI-03；无正式写授权不能推导应开放写入。R18/R31 加入禁止改变屏幕状态的执行约束，功能判据不放宽。上表 v1 原文和建立时的未调查状态保留，初版完整副本见本地 `verification/criteria-v1.md`；源码事实没有反向修改任何产品要求。

## 3. 逐条实现证据

下表的“静态支持/未发现偏离”仅说明所列正式路径；它不是相应行为的真实用户验收通过。每条均承接 §2 产品来源和必要不变量；缺陷详 §5。旧 Pxx/VPxx/F16 指历史 Validation 的脱敏操作结果，不是本轮权威。没有将历史报告中模型自述或主会话解释用作判据。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| R01 | [agent/system_prompt.py:588](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/agent/system_prompt.py:588) → [agent/system_prompt.py:599](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/agent/system_prompt.py:599) | 所属 SOUL 进入 identity，Secretary/generic guidance 后续拼接；对照完整生活产品意图及部署文案。 | 固定 SOUL；代码；旧 P01/P06/P07 脱敏结果 | 方向支持，但 Q01/Q02：测试访问安排进入部署身份；全局默认委派须明确作用范围。 | 新部署 SOUL 的实际最终 root/真实模型未取证，不能只凭文件判通过。 |
| R02 | [secretary/noting_prompts.py:9](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_prompts.py:9)；[agent/system_prompt.py:41](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/agent/system_prompt.py:41) | Faithful extraction 区分用户问题/认可/AI建议，Notebook非每轮必写；检查不强制所有闲聊建任务。 | 代码；旧 P06：闲聊无新增排期，未完保留 | 静态支持；E03 行为覆盖不足。 | 已见样本不证明倾诉/多轮探索/所有措辞均不任务化。 |
| R03 | [hermes_state_secretary_identity.py:127](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/hermes_state_secretary_identity.py:127) → [hermes_state_secretary_foreground.py:300](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/hermes_state_secretary_foreground.py:300) → [agent/conversation_compression.py:3980](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/agent/conversation_compression.py:3980) | 逻辑绑定、压缩祖先、History恢复及 same-owner cold route；追踪物理与逻辑身份。 | 代码；旧 P03/P05；本次 T02 | 基本接线存在；F02/E04 阻止整体通过。 | 本次没有在新部署重启/真实压缩；长期性非单次测试结论。 |
| R04 | [hermes_state_secretary_identity.py:35](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/hermes_state_secretary_identity.py:35)；[personal_provider.py:283](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/personal_provider.py:283)；[src/core/profiles.ts:56](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/core/profiles.ts:56) | 新/fork绑定独立；多profile原生roster；NM从每profile配置选space，不用profile名强制等同Space。 | 静态路径；固定 PHASE3 §8.2 | 本次未发现强制一一绑定或固定三角色限制。 | 两profile运行样本只覆盖具体部署；手动跨space是授权策略，不是通用共享实现。 |
| R05 | [tools/session_history_tool.py:35](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/tools/session_history_tool.py:35) → [hermes_state_conversation_history.py:60](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/hermes_state_conversation_history.py:60) → [hermes_state_conversation_history.py:99](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/hermes_state_conversation_history.py:99) | 默认当前、显式cross、owner DB、合法路径、Noting绑定任务校验；参数无可选外来profile DB。 | 代码；旧 P03 cross/read实证 | 正式工具边界支持；无本次跨profile泄漏证据。 | 旧跨Conversation成功不代表跨profile被授权；长消息读回边界见Q03补充。 |
| R06 | [agent/system_prompt.py:34](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/agent/system_prompt.py:34) → [tools/session_history_tool.py:433](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/tools/session_history_tool.py:433)；[personal_provider.py:362](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/personal_provider.py:362) | History原文、Notebook索引、压缩footer、NM短指针→CLI按需读链。 | 静态；脱敏 nm-injection-audit；F01/T01 | 部分支持；F01和E02/E03尚未闭合“可发现且能用”。 | Recall非空仅1样本，其正文此前已可见；不是指针引发首次深读成功证据。 |
| R07 | [secretary/noting_prompts.py:16](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_prompts.py:16) → [secretary/notebook_store.py:78](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/notebook_store.py:78) | accepted责任、稳定entry/version、更新/归档引用约束、成功交付后按覆盖结算。 | 代码；旧 F16/P02真实顺序；S02 | 设计保留未完责任；现行Candidate来源形态已变，旧成功不能覆盖新形态。 | 部分成功、多目标、多依赖、后续纠正仍缺当前真实模型证明（E03）。 |
| R08 | [agent/system_prompt.py:48](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/agent/system_prompt.py:48) → [secretary/scheduler_table.py:32](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/scheduler_table.py:32) → [hermes_cli/web_server.py:284](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/hermes_cli/web_server.py:284) → [tui_gateway/scheduler_host.py:50](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/tui_gateway/scheduler_host.py:50) | Main登记instant→常驻5秒扫描owner→原生resume/ingress→durable承载；检查无浏览器冷态。 | 代码；旧P04/P05两个600秒窗口 | 正式调度接线支持；S01行为约定被弱化，需收敛。 | 有窗口实测但非现实24h良率；未要求新增代码强制器或关机唤醒。 |
| R09 | [agent/system_prompt.py:39](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/agent/system_prompt.py:39)；[secretary/noting_prompts.py:19](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_prompts.py:19)；[personal_provider.py:117](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/personal_provider.py:117) | 文案与真实wake结果对照，静默合法而非所有wake必发通知。 | 部署SOUL；旧P04第二窗口/VP05 | 旧样本“无需参与仍可见汇报”未关闭（E03）；不能据提醒成功判断行为符合。 | 无新SOUL复测；无法把一次噪音归因为所有模型/确定代码缺陷。 |
| R10 | [secretary/noting_prompts.py:9](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_prompts.py:9) → [secretary/notebook_contract.py:193](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/notebook_contract.py:193)；[hermes_state_conversation_history.py:85](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/hermes_state_conversation_history.py:85) | 原文读快照、真实来源合法性、讲话者/确定性/否定/纠正规则；Tool与framework不默认当用户事实。 | 代码；旧P02/P03/P06纠正轨迹；S02 | 基础机制支持；来源规格矛盾及模型执行缺口未关。 | 无结构化状态能单独证明模型归因正确；不要求完整事实治理系统。 |
| R11 | [tools/session_history_tool.py:394](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/tools/session_history_tool.py:394)；[personal_cli.py:109](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/personal_cli.py:109)；[skills/nm-cli/SKILL.md:24](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/skills/nm-cli/SKILL.md:24) | 现有原文身份可读；Memory provenance/helper具体落点可检查；不以Memory ID替代来源链。 | 代码；旧VP02真实Memory无来源元数据 | E02未关闭：现有窄接线存在但实际路径绕过。 | 完整审计/治理为未来；现有链路必须真实，不能拿未来范围豁免已经承诺的provenance。 |
| R12 | [secretary/noting_prompts.py:7](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_prompts.py:7) | 检查无强制用户打分机制；分开机制反证、代理模型样本、长期观察。 | 本报告方法及旧实测记录 | 本轮方法符合；未将单样本、模型自述或总PASS数当行为通过。 | 不设产品原文没有指定的固定样本量/成功率。 |
| R13 | [personal_scope.py:35](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/personal_scope.py:35)；[secretary/noting_runtime.py:145](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_runtime.py:145) | 个人Provider按Main/Cron/child资格；未从专职Profile存在推导正式跨助手委托。 | 代码；SOUL；产品未来范围 | 当前范围限定正确；Q02不等于要求开发跨Conversation协作。 | 未审未来治理/代理总线；native临时delegate并不自动构成未来正式协作系统。 |
| R14 | [secretary/noting_scope.py:11](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_scope.py:11) → [tui_gateway/scheduler_host.py:50](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/tui_gateway/scheduler_host.py:50)；[personal_provider.py:283](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/personal_provider.py:283) | 后台按state.db owner绑定配置，SOUL按agent home；双profile插件安装与scope元数据证据。 | 代码；脱敏root注入审计；NM安装源码hash匹配 | 所属身份机制存在；E01当前部署最终root尚未验证。 | 本轮实测配置授权不提升为永久人格/正式写权限。 |
| R15 | [personal_provider.py:283](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/personal_provider.py:283) → [personal_provider.py:442](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/personal_provider.py:442)；[personal_client.py:104](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/personal_client.py:104) | 自动Bundle/Recall/Thread绑定Space；archive_enabled=false前后gates；手动terminal仍受指令授权而非OS沙箱。 | 代码；旧Default receipt=0；固定provider/client与安装指纹一致 | 实测自动写边界有证据；没有宣称CLI具不可绕过只读。 | 不读取Default正文；正式部署权限范围Q01未裁定。 |
| R16 | [agent/system_prompt.py:41](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/agent/system_prompt.py:41) → [hermes_cli/cli_secretary_commands.py:78](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/hermes_cli/cli_secretary_commands.py:78) → [skills/nm-cli/SKILL.md:16](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/skills/nm-cli/SKILL.md:16) | candidate→具体提案→批准→action→确认结果；helper预览默认、--apply非授权、unknown不盲重试。 | 代码；旧P02仅改措辞0写、限定批准1写 | 批准边界已有正反样本；E02来源交付仍缺。 | 样本是既有授权写，不追加真实NM写；terminal不额外声称结构审批强制。 |
| R17 | [secretary/noting_prompts.py:18](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_prompts.py:18) → [secretary/notebook_contract.py:193](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/notebook_contract.py:193) | 必须先源后Candidate；引用检查不允许悬空；现行Memory候选不能同时带refs和messages。 | 旧F16成功；S02；静态状态机 | 来源结算原则存在；当前exclusive来源形态与旧条款冲突，缺新形态实际闭环。 | 不得用旧双来源样本证明新形态；也不能臆断新形态绝对无法通过转换完成。 |
| R18 | [secretary/noting_runtime.py:537](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_runtime.py:537)；[secretary/noting_compact.py:4](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_compact.py:4) | 核对真实窗口、输入前缀、原生262144容量、idle100000/5s；自然触发与手动触发分开。 | 旧Validation P01–P07明确记录实际admission均manual | 方法约束已记录；E01：自然Idle+Noting尚未实测，不能以配置存在宣称通过。 | DeepSeek仅代理；无K3/现实24h实测；新SOUL无10分钟语句。 |
| R19 | [secretary/notebook_render.py:36](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/notebook_render.py:36) → [secretary/noting_notifications.py:11](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_notifications.py:11)；[secretary/noting_tools.py:168](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_tools.py:168) | completion/Main show/working show/control各模型面，与API默认面分开。 | T01 1P2F；同hash12节点旧修补证据 | F01：隐藏ID已落实，但所有覆盖说明被一起移除。 | 未要求恢复内部ID；保留有用entry/version/History身份合法；旧冻结消息不重写。 |
| R20 | [secretary/noting_prompts.py:3](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_prompts.py:3)；[agent/system_prompt.py:34](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/agent/system_prompt.py:34) | 比对可观察指令与真实输出；不把内部知识当模型可见；发现后不擅自改Prompt。 | F01/S01/S02/Q02；本报告无产品修改 | 审查权限遵守；F01指令还要求识别不存在的coverage，须修复方案独立评审。 | 未对捕获dirty的所有其他并行改动臆断授权有无。 |
| R21 | [src/components/ChatSelectors.tsx:7](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/components/ChatSelectors.tsx:7) → [src/core/profiles.ts:85](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/core/profiles.ts:85) → [src/core/controller.ts:632](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/core/controller.ts:632) | 仅new允许Profile选择，阻止send/create中换owner；owner config/model/SOUL沿原生会话创建。 | 静态；owner后续68项证据中匹配Controller/Profile部分 | 正式接线方向符合，E05真实当前UI未验。 | 未用旧Chrome页面或jsdom冒充IAB真实界面。 |
| R22 | [src/core/controller.ts:495](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/core/controller.ts:495) → [src/core/profiles.ts:41](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/core/profiles.ts:41)；[src/core/controller.ts:632](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/core/controller.ts:632) | roster各owner列表合并、partial保留、同ID+owner、resume/rename/pin均捕获所属环境。 | 静态；匹配owner证据；pin最终24项对应文件hash一致 | 未发现仍用首页选择过滤会话或重归属；当前受控证据部分可复用。 | 早期234与Chrome属于修补前；不能整体搬为最终快照通过。 |
| R23 | [src/core/profile-icons.tsx:7](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/core/profile-icons.tsx:7)；[src/core/profiles.ts:32](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/core/profiles.ts:32) | 固定映射+逐row owner；fallback仅普通图标，不假称每profile独一。 | 代码；旧页面仅历史参考 | 静态符合PI06。 | 当前视觉仍E05，不新增配置要求。 |
| R24 | [src/App.tsx:191](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/App.tsx:191) → [src/App.tsx:211](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/App.tsx:211)；[src/core/controller-timeline-streaming.test.tsx:95](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/core/controller-timeline-streaming.test.tsx:95) | 实际Timeline生产组件/Controller事件fixture覆盖首reasoning增量、工具construct/queued/running/complete及history接替。 | 源码+已有后台jsdom测试设计；旧流式报告 | 生产投影有支持；E05真实当前首包/时序/高亮不足。 | 本次没重跑jsdom/全量；代码/fixture不能证明浏览器绘制和模型首段送达。 |
| R25 | [src/core/native-notices.ts:64](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/core/native-notices.ts:64) → [src/App.tsx:201](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/App.tsx:201) | 非error统一5000ms；error无timer；clear排除error，人工dismiss；通知scope绑定owner。 | 静态；owner补强native-notices文件hash匹配 | 代码路径符合；当前真实界面未验。 | 分类正确性仍依后端真实错误事件，不以仅timer测试证明全部消息语义。 |
| R26 | [src/core/usage-view.ts:28](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/core/usage-view.ts:28) → [src/core/usage-counters.ts:84](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/core/usage-counters.ts:84) | 按scope/runtime/epoch保留可信原生值，session_id和owner校验；未知/partial不造数，model变化invalidates。 | 代码；现有usage测试参考 | 主要契约有实现；E05冷恢复实际显示未验。 | 同名model跨provider仅provider变时未清context（observeIdentity:54），需定向确认是否后端必发失效；未先判确定用户错误。 |
| R27 | [secretary/noting_surface.py:65](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_surface.py:65) → [secretary/noting_surface.py:77](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_surface.py:77)；[tools/notebook_tool.py:11](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/tools/notebook_tool.py:11) | Main History独立、Notebook/global、Scheduler独立、local参与；默认API保持，模型面可选projection。 | 代码；ID投影12项同hash；T03 | F03旧工具路径不符合明确退役契约；其余关闭矩阵尚不能全称原生一致。 | 07继承Main强制History是明确特例；不把Noting off误判成必须移除History。全Secretary退出定义若需更严格应另明确，不臆造开关。 |
| R28 | [hermes_state_secretary_notebook.py:236](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/hermes_state_secretary_notebook.py:236)；[secretary/reminders.py:31](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/reminders.py:31)；[personal_provider.py:458](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/personal_provider.py:458) | 事务内pointer按有效覆盖顺序选择；durable carrier同事务settle；NM确认ACK才推进收据/前缀分歧停止。 | 静态；T02；旧P05/VP01；E04 | 结构保护存在但F02/E04阻止完整恢复结论。 | NM丢ACK/Cron/rewind后连续性不由首批22→24证明；安全停止不等于正常连续性。 |
| R29 | [agent/system_prompt.py:34](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/agent/system_prompt.py:34)；[personal_provider.py:493](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/personal_provider.py:493)；[src/core/profiles.ts:56](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web/src/core/profiles.ts:56) | 用户不用管Session/Notebook；界面跨owner可找；不靠重复提醒维持责任；梳理来源缺失与同步停止后的人工补偿。 | F01/S01/E02/E03；Q03 | 仍存在真实管理负担缺口；不得把可手工搜回视作原始链全部符合。 | 未要求新建完整管理台；最小恢复提示/定位按已有入口评估。 |
| R30 | [secretary/noting_prompts.py:9](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_prompts.py:9)；[personal_provider.py:362](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/personal_provider.py:362) | 转录仅明确语境纠错；来源不够保留未知；NM空结果≠没行动；纠正更新当前索引与提案。 | 代码；旧P03/P04/P06纠正/未知样本 | 已观察部分支持；E03覆盖有限。 | 无真实语音误转样本；不宣称所有语音/长期纠正均已通过。 |
| R31 | [frozen-integrity.json](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/verification/frozen-integrity.json)；[counterexamples.log](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/verification/counterexamples.log) | 固定三仓manifest、canonical runner本机隔离、同hash证据复用，真实模型/历史版本/未验分别列明。 | 本次3文件7节点：3P4F，5.2s；无重试/全量 | 本报告证据链可复查；门禁不通过。 | UI/新SOUL/自然Idle等缺证不改判据；既有大型混合工作区结果不作当前通过依据。 |

## 4. 核心目标及验证方法审查

### 4.1 以用户目标贯穿的检查链

- **长期聊、少管理：**身份/SOUL → 当前Conversation路由 → History有效路径 → 压缩恢复 → 完整Notebook → 后续模型上下文 → 原文按需回读。已核对这些正式调用点；F01/F02说明“有Notebook/有冻结函数”不足以证明模型拿到正确可用的连续上下文。
- **接受责任、以后继续：**Main实际登记Scheduler → 原生宿主常驻扫描 → target profile/cold resume → 同事务持久载体 → action result/失败重试。浏览器关闭不等于宿主关闭；本轮没有把关机恢复、全天推理或代码强制每天唤醒发明为要求。S01审的是模型行为约定被规格弱化。
- **形成可信记忆：**用户原话/纠正 → Noting来源与候选 → Main具体提案/批准 → 官方NM创建与来源附件 → 按实际覆盖先源后Candidate → 后续检索/原文。批准成功、NM有一条Memory、来源可追、源正确结算是四个不同断言。旧P02有前两项和一例结算，E02/S02仍阻止整链通过。
- **组织自由：**首页Profile只选新会话环境；已有row owner决定打开/发送/标题/Pin/图标；多Conversation与NM Space绑定互相独立。当前代码已修侧栏过滤及同ID跨owner污染方向，早期页面成功不覆盖后续owner/Pin变更。
- **关闭与失败：**检查各能力独立gates、Noting专用工具权限、Snapshot原子发布、Scheduler持久接受证明、NM ACK与重写分歧。异常时安全停止应如实呈现；不能用安全拒写证明用户的后续连续性已经满足。

### 4.2 本次必要反证（一次、无重复全量）

执行 cwd 为固定主仓副本；既有官方PM解释器 `/Users/edgar/code/hermes-secretary/.venv/bin/python`，macOS arm64/Python 3.14.7/pytest 9.1.1。没有创建新环境、改锁或更换依赖。使用固定副本 `scripts/run_tests.sh -j 1`，显式 `HERMES_PYTHON`、`HERMES_TEST_FILE_RETRIES=0`，加载固定 `tests.conftest` 提供收集前/逐test Hermes home隔离，模型client受控，无真实模型或NM请求。pytest因证据文件在ignored上层而发现原仓pyproject；已核对它与固定副本逐字相同；实际产品import root断言通过。完整命令/结果见 [counterexamples.log](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/verification/counterexamples.log) 和 [frozen-integrity.json](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/verification/frozen-integrity.json)。

| 编号 | 方法与真实可反驳点 | 结果 |
|---|---|---|
| T01 | [test_coverage_projection.py](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/verification/test_coverage_projection.py)：不同合法覆盖边界、相同Notebook内容/生成时间，比较Main show与completion；另确认imports来自固定副本 | 1P2F：ID隐藏后两边界所有模型输出相同，只剩生成时间，缺有意义覆盖说明 |
| T02 | [test_v2_context_selection.py](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/verification/test_v2_context_selection.py)：沿原生Main+持久Noting三次实际请求，配置公开ContextEngine选择hook；仅模型IO和引擎选择受控，DB/dispatcher/commit真实 | 1F：冻结父prefix一致性依次 true/false/false，tools均一致，仍committed=true；不是只读helper断言 |
| T03 | [test_v2_retired_tool.py](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/verification/test_v2_retired_tool.py)：原生Noting循环提交旧工具名，与新名正对照、另一旧名负对照 | 2P1F：notebook_maintain可写、notebook_manage拒写，而notebook_mutate被修复为新名并实际写入已提交Snapshot |

合计 **3文件、7节点，3通过4失败，5.2秒，0重试**。失败是独立反证而非产品测试期望复制；输出不含个人资料。固定manifest逐文件核对无漂移。T02/T03复用了旧审查的合成反例定义，重新在本次固定源码跑一次以解除历史版本歧义；未复跑大型suite。

### 4.3 既有证据的可复用范围

1. `/Users/edgar/code/hermes-secretary/.hermes-dev/validation-personal-20261018/notebook-model-surface-fix.md` 的8个产品/测试文件SHA与固定副本一致（[reused-evidence-hashes.json](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/verification/reused-evidence-hashes.json)）。其12个独立节点支持“审计ID不进入新模型面、API默认兼容、通知选择原子性”，**不支持有意义覆盖保留**；T01正是这些测试未检查的产品结果。
2. `/Users/edgar/code/hermes-secretary/.hermes-dev/validation-personal-20261018/profile-sidebar-regression.md` 的早期234项与Chrome页属于owner补强前。后续owner manifest中Controller/Profile/Notices/App/Sidebar代码相符，但Pin helper及两个测试已变化；最终Pin24项对应三个文件全部相符。[ui-evidence-hashes.json](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/verification/ui-evidence-hashes.json)保留匹配/不匹配。仅复用各自实际受影响路径，不把234+68+24相加宣称最终全UI通过；新版本真实界面未验。
3. `/Users/edgar/code/hermes-secretary/.hermes-dev/validation-personal-20261018/evidence/nm-injection-audit.json` 是脱敏root/Recall审计，未读取其指向的私人原始正文。它证明当时非空Bundle、Working Memory排除、Space明确和3次Recall载体，其中指针数为0/0/1；不是指针驱动首次深读，也不是新版部署SOUL实际装载证据。个人provider/client固定SHA与安装证据一致，支持已记录的首批22→24同Thread suffix链和禁归档样本；不外推网络丢ACK、Cron或rewind。
4. `/Users/edgar/code/hermes-secretary/.autonomous/20261016-round3-secretary-nm/validation.md` P01–P07记录了真实DeepSeek双profile、两600秒测试日、批准/未批准、cold/warm Reminder、原文纠正恢复，也明确VP02未关、VP05安静性偏差、natural idle未达阈值。旧root和本快照的区别保留。旧混合工作区大suite和603项UI总数均不作为本轮固定版通过证明。

### 4.4 执行/覆盖边界

只后台读取代码、公开技术规格、脱敏历史证据及受控测试；没有调用CU/CUA/IAB/Chrome/Edge/open/open_in_codex，没有改变任何屏幕状态。PI-11不豁免R21–R26，故当前真实UI留为E05，不能外部浏览器代验。没有新增真实NM写、没有Default正文、没有凭据、没有新模型样本。未覆盖的OS/渠道/Provider不能写成通过；本包也不以未测试全部上游无关功能为借口无限扩大任务。

## 5. 发现、整改优先级与范围外项

### 5.1 已确认实现缺陷与规格问题

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| **F01 · P1 · 实现** | R06/R19/R20；[secretary/notebook_render.py:36](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/notebook_render.py:36)、[secretary/noting_notifications.py:11](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_notifications.py:11)、[secretary/noting_tools.py:168](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_tools.py:168) | 清理审计ID时把coverage整个删除；completion只含Created at，control接受coverage参数却不输出任何覆盖描述。Main文案要求note its coverage，Noting要求identify anchor/coverage，却无该对象可读。T01两种边界的模型输出完全一样。 | 模型看不出Notebook覆盖到了哪段证据；晚到结果的生成时间不能代替事实覆盖。符合“无内部ID”的旧测试仍可违反“模型有用且可理解”的产品目的。 | 提供由内部锚点解析的、无内部审计ID的可读覆盖说明，区分Notebook生成时间与已读证据范围，覆盖show/working/control/completion各面；不恢复ID、不删有效来源UID、不重写冻结历史；定向实际wire证明较旧coverage不会被表现成更新事实。 | **未修复；反证确认** |
| **F02 · P1 · 实现** | R03/R10/R20/R28；[agent/turn_request_assembly.py:155](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/agent/turn_request_assembly.py:155) → [agent/conversation_loop.py:1307](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/agent/conversation_loop.py:1307)；[secretary/noting_child.py:211](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_child.py:211) | 公开可配置ContextEngine.select_context在每次Noting请求对完整api_messages运行，可改冻结父前缀；T02第一请求保持、后两次被替换，child仍成功提交。 | 冻结的证据/父上下文在整理过程中实际漂移；不只是缓存成本，Noting判断输入可能与提交声明的覆盖不一致。现用默认引擎未触发不等于兼容该原生机制。 | 在正式请求构建层保护已冻结前缀，仅对允许后缀应用选择/规范化；不全局禁用原生ContextEngine。关闭须T02通过，并核对第一/后续请求及续Turn、非Noting原生引擎仍可工作。 | **未修复；本版复现旧V2-F03** |
| **F03 · P2 · 实现** | R20/R27；[tools/secretary_dispatch.py:10](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/tools/secretary_dispatch.py:10)、[secretary/noting_surface.py:6](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_surface.py:6)；07:L84 | retired集合漏notebook_mutate。原生工具名模糊修复把模型输出旧名映射notebook_maintain；T03实际写入并提交。 | 当前工具协议已明确退役的动作仍执行，历史/幻觉旧调用被静默当成新写；不是Main越权写的证明，但违反显式拒绝和正式接线约束。 | 原始名称进入native repair前统一识别完整退休集合，返回legacy_tool_removed而非alias；同步/并发/直接调用一致；T03两负一正对照全部成立，未启用分支不受新拒绝波及。 | **未修复；本版复现旧V2-F02** |
| **S01 · P2 · 规格偏离** | R08；产品P:L129–133；[agent/system_prompt.py:48](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/agent/system_prompt.py:48)、[secretary/scheduler_table.py:32](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/scheduler_table.py:32)；07 §8.6 | 最新产品说默认至少每24h一次Instant（行为约定）；当前规格/Prompt只要求至少一个仍能fire的meaningful instant，24h空窗notice让模型“consider whether”。一个远于24h的未来排期可满足前一句，后一句没有每日行为要求。 | 不能以“有未来提醒”证明持续主动机会；代码符合这段旧文字仍可能偏离产品意图。旧两次测试日成功仅说明特定输入能续排。 | 把默认24h行为约定与用户关闭例外表述准确，同时保留无须通知/无须全天推理；不新增强制daemon任务。Prompt修改由root提出授权范围内方案，审查者评估；补无新输入/已有远期排期/无需通知场景。 | **规格须收敛；非已复现真实24h漏唤醒** |
| **S02 · P2 · 规格内在冲突/当前生命周期证据不足** | R07/R10/R11/R17；[docs/07-scheduler-notebook-noting-compaction-redesign.md:127](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/docs/07-scheduler-notebook-noting-compaction-redesign.md:127) vs [secretary/notebook_contract.py:193](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/notebook_contract.py:193)、[secretary/noting_prompts.py:31](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_prompts.py:31) | 07仍写每条Candidate保留原文来源、不能只剩notebook_refs（词表也“refs＋原文”）；现行schema/Prompt强制Memory refs与messages互斥、Skill/Rule只messages。两条不能同时满足。 | 审查/开发会各按不同条款自称通过；旧F16双来源的结算样本不覆盖新exclusive形态。最后一个refs清除时须同时保持合法来源，否则更新拒绝；不能让模型靠试错猜生命周期。 | 按最新产品“可追溯、真实覆盖、先源后Candidate”统一规格与实际状态转换；不预设恢复双来源。明确合法转换/原子处理方式及未覆盖依赖，当前正式child证明单源、多源、部分成功、最后引用删除和后续纠正。 | **待root定方案；不判当前形态绝对不可行** |

F01是本次新增独立反证，不是要求回退已授权ID清理。F02/F03虽曾在旧审查出现，本次以固定版反证重新确认，未靠历史结论判定。S01直接以最新产品而非07为判据；S02指出实现契约矛盾，没有把旧“必须双来源”抬成高于产品的永久规则。

### 5.2 验证与模型行为缺口（不得误列成确定代码缺陷）

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| **E01 · P1 · 当前部署/自动触发证据** | R01/R14/R18/R31；[secretary/noting_runtime.py:537](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_runtime.py:537)；system_prompt identity/guidance路径 | 新部署SOUL未有实际root/模型样本；旧业务旅程全部manual，最高上下文不足100000，自然5s Idle联合分支未发生。现场进程没有因本轮冻结重载。 | 不能说“当前部署身份正确”和“双profile自然Idle+Noting已可用”；磁盘代码/配置不等于当前进程。 | 修复后记录新冻结源码/配置/实际加载版本，使用自然容量/真实等待从正式入口观察两个owner的Idle admission及独立压缩结果，不能改系统钟、降低授权阈值或灌无意义文本冒充业务；不足时明确继续未验。 | **证据不足** |
| **E02 · P1 · 实际Memory来源链未完成** | R06/R11/R16；[skills/nm-cli/SKILL.md:24](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/skills/nm-cli/SKILL.md:24)、[personal_cli.py:109](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/personal_cli.py:109) | 旧真实批准写使用官方m add但没经已安装窄helper，Memory无Hermes来源metadata，标签映射/提案原文回查也缺。Current代码有helper和skill，但没有证明模型实际走到；新会话用户补一句位置后才找回原始History。 | 真Memory存在≠可追溯；这正增加用户补背景负担。Noting不能凭一个ID证明完整来源交付。 | root先给正式接线方案与批准范围，不以要求用户总说“请用helper”代替可用性。随后按授权隔离fixture/必要真实合成资料验证提案回读、精确来源/标签、实际Memory metadata、后续原文恢复；partial/unknown保留同ID修复，不重复创建。 | **旧VP02未关闭；未新增真实写** |
| **E03 · P1 · 代表行为与生命周期证据** | R02/R07/R09/R17/R30；[secretary/noting_prompts.py:18](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/noting_prompts.py:18) | 旧样本有纠正保留/待确认/批准反例，但第二次无新进展仍可见汇报；未覆盖新Candidate exclusive形态、partial写、多目标、来源后改、共享依赖、一次口误等。Recall pointer样本未证明首次深读。 | 缺证不能以单次“我做到了”或同题体验问答关闭；也不能全部甩给DeepSeek而忽略Harness可观察信息不足。 | 修复后场景围绕具体用户意图/实际结果判定：允许静默、应跟进不漏、未知不编、部分覆盖不全结算、纠正不被旧批准覆盖、指针→正文。报告模型样本局限，不自行设固定良率。 | **模型样本与当前版本覆盖不足** |
| **E04 · P1 · 恢复/并发的未闭合边界** | R03/R27/R28；[agent/turn_recovery.py:1852](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/agent/turn_recovery.py:1852)、[agent/turn_overflow.py:285](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/agent/turn_overflow.py:285)、[personal_provider.py:458](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/personal_provider.py:458) | Noting compression_enabled=false，但output-cap路径有豁免并可调用compress_scored_by_tokens；本次未取实际child请求恢复反证。Snapshot晚到/rewind、Reminder ACK重试/全宿主重启、NM丢ACK/Cron当前全链亦不能由已有happy path替代。 | 存在需要定向证实的真实路径，不宜把禁自动压缩布尔值或首批归档成功当完整保障。 | 优先一次最小output-cap受控Provider错误沿原生child观测父前缀/工作态/终止；其余先做同版本证据映射，只有缺口/集成变化再定向测。不得重开无差别全suite。 | **未判output-cap已破坏前缀；保留证据缺口** |
| **E05 · P1 · 真实UI验证边界** | R21–R26；UI上述正式路径 | 新版Profile owner/Pin、首Thinking/工具时序/高亮、提示5s和冷统计只有静态/后台fixture或旧版本页面；当前没有合规非CU且不改变屏幕状态的IAB接口。 | 用户明确重视的真实交互未验；不能因工具受限豁免或以Chrome代验。 | 保留当前代码/受控证据，后续在用户允许且合规的真实入口做短场景复验；记录实际版本/首段流式/切Profile+旧Conversation/通知计时/冷恢复。provider-only identity变更时Context是否失效另用后台定向证据确认。 | **真实UI未验；没有操作屏幕** |

### 5.3 产品原文不足以替用户定案的最小问题

这些是交回root集中处理的取舍，不是审查者擅自新增需求；没有因它们中途打断审查。

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| **Q01 · 部署身份与实测权限分层** | R01/R14–R16；PI01/03；inputs两SOUL末段 | 两份“可直接部署”SOUL把本轮两个Space/Default只读/特定专职关系写成恒常身份。最新PI01明确这只是实测访问授权，不自动定义永久人格/正式写权。 | 无从据此认定正式默认权限，不能通过“模型照SOUL”反向证明部署产品决定正确。 | 最小问题：这些具体Space访问限制是否也是正式部署政策？若只是实测，应留在本轮输入/权限配置，部署身份只表达已确认职责；任何改动不得推导Default可写或更广访问。 | **待产品取舍；非要求扩大权限** |
| **Q02 · 通用顾问与默认委派的适用范围** | R01/R02/R13；产品完整生活/直接帮助；[agent/system_prompt.py:39](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/agent/system_prompt.py:39) | 新SOUL是通用助手，随后全局Secretary Role仍要求除用户要求亲自做外，concrete work默认委派。旧07/常量继承了事务协调口径。 | 未证明会实际把答疑/建议都委派，故不判模型必然跑偏；但谁是默认执行主体会影响用户体验，不能由实现者自行把“助手”收窄为督办。 | 最小问题：此默认委派只针对明确可委派执行事务，还是也覆盖学习答疑/私人顾问的直接帮助？按产品意图明确作用域，评审实际拼装root及不同意图样本；不开发未来跨Conversation委托。 | **规格适用范围待裁定** |
| **Q03 · 正常改写历史后的NM恢复与原文大消息边界** | R06/R11/R28/R29；[docs/PHASE3.md:143](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/docs/PHASE3.md:143)、[personal_provider.py:493](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/personal_provider.py:493)；[tools/session_history_tool.py:27](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/tools/session_history_tool.py:27) | NM已ACK前缀遇正常rewind/edit后安全停止，当前无自动reconcile且主要log/return状态；History单条最多20000字符、Read无offset，长原文尾部不能靠同identity完整分页。两者不是伪造成功，但限制当前长期使用。 | 产品没有指定自动远端删改、全量治理或无界上下文；不能自行要求这些大功能。仍应明确可接受的当前恢复/取证路径及谁承担管理负担。 | 最小问题：本轮是否接受“正常rewind后NM暂停同步，需显式人工处理”的上线边界，且如何让用户/助手知道？对于超长原文是否以明确截断+可达原始资料入口满足当前取证，而非承诺一次全读？不盲自动覆盖NM或去掉工具预算。 | **明确限制与取舍，不自造修复方案** |

范围外且有原文依据：完整长期记忆治理/全历史演化审计平台、正式跨Conversation委托及责任同步、通用跨Profile共享、未来新角色、外部产品功能复制。它们不是本轮新增开发清单；当前已经存在的功能如果丢来源、错误认权、假报成功，不能归入“未来”逃避修复。Native内置memory的小容量全局事实约束与NM长期存储不同：本次真实双Profile关闭native memory/user profile，不将native狭窄memory guidance直接判成这两Profile的NM缺陷。

## 6. 修复与独立复审

本包截至固定快照完成调查；尚未收到root修复方案，没有任何发现被标已修复。§2 v1及v2澄清均保留，不因代码现状改判据。

| 轮次/输入 | 修改或方案 | 独立评审结果 | 关闭条件/下一步 |
|---|---|---|---|
| v1：产品/身份/SOUL固定输入 | 未看代码前立31条判据 | 已完成；原始版本留ignored criteria-v1.md | 不用后续实现报告改写原判据 |
| v2：authority index及三仓固定manifest | PI01实测授权澄清、PI11不改屏幕；进入代码审查 | 3实现缺陷、2规格问题、5类证据缺口、3项取舍 | 本报告完整交回root；root先定最小方案与Prompt修改授权边界 |
| 后续修复 | 尚未提供 | **未复审/未通过** | 新固定增量manifest→逐项检查必要条件→受影响反证/邻域→当前部署/真实模型与合规UI Validation；不要求无差别重跑 |

收敛顺序建议：先修F01/F02/F03及统一S01/S02（避免在错误上下文/冲突状态机上烧真实模型）；root集中裁定Q01/Q02和当前恢复边界；再拟覆盖批准、来源结算、自然Idle、冷暖唤醒、纠正/安静性、NM读写来源、跨Profile旧会话及UI流式的实际测试计划。对E04先复用同版本机制证据，确有缺口才定向补反证。E05若执行能力仍受限必须保持未验，不作假通过。

本报告提供“产品要求→必要不变量→正式路径→触发条件→证据→判定”全范围矩阵；不是证明已经找尽所有潜在缺陷。后续Validation的真实行为可以发现新问题，但不得回改本轮既有产品判据使当前实现过关。

### 6.1 集中方案评审（2026-10-18，未执行修复或测试）

本次仅评审 root 提交的方案，沿用 §2 已建立的产品判据；上面的“尚未收到方案”是初次交回时的历史状态，由本节更新。未读取移动中的实现半成品、未改固定快照/生产代码/Prompt、未跑测试、未请求模型或 NM、未操作屏幕。**方案方向接受不等于实现接受，更不等于发现关闭；当前整体结论仍不通过。**下表说明哪些可继续工程实施、哪些仍待授权/产品决定；不是审查者代替用户批准。

| 事项 | 独立方案判断 | 可继续范围与授权边界 | 必要关闭证据 |
|---|---|---|---|
| F01：可信锚点→可读覆盖，失败明确未知 | **接受方向。**生成时间和证据覆盖必须区分；可信 DB 解析正好补足缺失的可见对象，不需要把内部ID再交给模型。 | 属于既有“隐藏审计ID但保留有意义覆盖说明”的工程落实。解析必须绑定该任务/该Snapshot已经冻结的锚点与owner，不能读“当前最新”替换旧覆盖。只知道结束边界时不能虚构完整起点；显示时间不能自行声称时间之前每条事实均已索引。错误/未知应可读且不阻断Notebook主体/原生主逻辑。 | 新固定版本的 Main show、working show、首次/续Turn control、completion 实际模型面均有正确含义；同生成时间不同已知覆盖可区分，较旧结果不被渲染成较新覆盖；未知/缺消息/来源时间未知明确降级；内部ID不泄漏、API默认兼容、owner隔离不回退。旧T01中覆盖需要DB解析时可改fixture提供实际消息，而非为通过断言编造时间。 |
| F02：ContextEngine只选择允许后缀 | **接受方向，但需要整个正式请求边界保护。**仅在一处切数组不必然保证后续规范化仍保持前缀。 | 在Noting冻结接缝限制选择范围，普通Main继续原生选择。冻结前缀及多模态块须防止通过 `conversation_messages` / `incoming_message` 等旁路参数或共享可变引用被改写；调用后仍要保留父前缀的字节/结构契约。引擎无法处理后缀或返回异常时沿既有安全降级，不能悄悄用其返回的整段历史替换冻结前缀，也不为此引入全局新引擎协议。 | T02全部实际请求和续Turn保持冻结前缀，后缀可变化；普通Main选择hook仍实际执行；补与本次改动直接相关的失败/空后缀/多模态边界证据。E04的output-cap恢复独立列账，不能凭修好选择hook顺带宣布关闭。 |
| F03：原名在repair前识别完整retired集合 | **接受方向。**原始名称先拒绝才能阻止模糊修复把旧调用变成写入。 | 退休名称清单集中管理，适用的Secretary同步、并发、inline/registry入口一致；错误码和下一步仍为明确退役反馈。不得把Secretary局部规则变成全部原生运行环境的新工具拦截器；按既有明确适用边界保留未启用原生行为。 | T03新名正对照、两个旧名负对照通过；原始名称经过实际repair/dispatch的测试；相关直接/并发入口和不适用原生对照，不只测集合包含字符串。 |
| S01：默认每24h一次Instant，可静默且用户可关闭 | **接受产品方向。**与产品P:L129–133一致，不要求代码强制器。 | root已申请该Prompt修改授权；未答不能改。建议精确区分“有一次真实可触发的主动检查机会”和“必须发消息”，不得把有七天后排期当作当前24h覆盖，也不能用无事可说取消默认检查机会。用户取消一次具体提醒不自动等于永久关闭所有自主跟进，反之明确停止某类跟进也不能靠默认规则偷偷重建同一任务。 | 授权记录→文档/常量精确一致→实际构建root→无新消息、远期已有提醒、明确关闭/恢复、无需通知但仍检查的正式场景；不以强制守护程序代替模型行为验收，不以600秒样本声称现实24h长期良率。 |
| Q02：默认委派限适合Agent的执行事务，答疑/顾问/交流直接回答 | **接受方向。**能够消除“通用私人助手被全局督办口径收窄”的歧义。 | 同样已申请Prompt授权，未答不改。“适合Agent”不能变成不可观察的系统内部分类；以用户请求和工作内容表达适用条件。只约束已有native委派选择，不增加正式跨Conversation派遣权；用户明确要求亲自处理仍优先。 | 新最终root同时包含SOUL及通用guidance，普通答疑/倾诉/策略讨论直接回应，可独立执行事务按授权委派并验结果；不能只核对常量文本或以某一次直接回答证明所有意图区分。 |
| S02：保留exclusive来源形态、同步过时规格、必要时refs→exact messages | **有条件接受，详细条件见§6.2。**该转换在现有一次update能力内可表达，不需要改变“先源后Candidate关闭”的产品顺序。 | 可做现有契约一致化和合法路径证明；不得据此擅改Step4硬编码Prompt，亦不得让工程端自动判定某来源已经交付。尚无已审实现/真实模型证据，不能先将S02标关闭。 | 单一最后ref、多源部分结算、其它Candidate共享依赖、来源后改、确切来源不可得、转换后中断/forced提交的有效路径；规范、工具结果和真实模型操作相互一致，详下文。 |
| Q01：具体实测Space政策移出可部署SOUL | **接受分层方向，权限必须等效保留。**PI01从未给出永久人格或正式写权。 | 可清理待部署文案中的测试专属安排，并将本轮策略留在现有测试初始化输入/配置；不得把删除SOUL限制当成扩大权限。`archive_enabled=false`只管自动归档，不能替代手动CLI访问约束。策略必须对冷恢复、压缩后及自主Reminder等没有普通user前缀的Turn仍有效，不能仅依赖“每条普通user message附前缀”。若暂时无法保证等效，不应先移除当前运行实例唯一的限制载体。 | 新构建实际root/测试上下文证明身份无测试尺度与偶然Space安排，而本轮允许/禁止访问仍准确；自动和手动路径分别核对。正式部署将来写权仍未授权，任何新增Space/写范围仍需用户决定。 |
| Q03：rewind后用现有可见渠道报告归档暂停，保留本地事实 | **接受最小降级方向。**安全拒写合理，但只有日志不足以让使用者理解NM记录不再更新。 | 允许在既有状态/错误反馈接缝表达“同步暂停及其范围”；避免每Turn重复噪音，正确绑定Profile/Conversation，恢复前不能报正常。不得自动覆盖/删除远端、创建替代Thread伪装续接，或宣称远端旧副本已同步撤回。本地有效历史与远端旧副本的区别须明确。 | 正常编辑/rewind→前缀分歧→无远端写→现有渠道可见且定位正确→后续仍暂停；本地原文仍可用。怎样恢复远端一致性、是否接受带此限制交付仍是产品/接入决策，本方案只关闭“静默失联”部分。 |
| Q03：超长History明确截断并提供同来源剩余读取 | **接受有界、增量的工程方向。**产品需要可达原文，不需要单次无界payload。 | 优先复用已有正式入口；确需新增读取参数时必须可选、旧默认/错误语义不变，继续在同owner/同合法Conversation路径检查。不得把原始DB/文件路径当作普通模型应自行修复的接口，也不能另开绕过History权限的通道。剩余部分必须来自同一原文，不是摘要或搜索猜出的片段。 | 前/后分段合并与原文一致；长度上限、Unicode/结构化内容、合法路径变更后拒绝、跨owner拒绝及旧客户端均明确；返回可理解的继续读取提示。未提供接口方案前不预先批准具体游标/offset设计。 |
| E02：个人helper参数层级修复＋既有skill discovery配置 | **接受这两项工程方向，但不能关闭Metadata全链。**见§6.3。 | 保持现有helper参数含义，只修官方CLI参数位置；原生skills roots/discovery可发现性修补不需重写通用框架Prompt。新索引只能在合法的新构建时点加载，不中途重建冻结root。现有技能正文含已知错误的CLI等价示例，需单列处理，不能将“完全不改文案”作为全部指导已经正确的证明。 | 实际目标模型root列出该技能且skill_view读取的是正确安装内容；创建命令按当前CLI合法解析并仍绑定精确目标、未知/partial仍保守；另需正式Metadata契约与按授权的实际交付证据，不能凭helper单测/skill索引关闭。 |

### 6.2 S02：转换在现有契约下的可行性与最小边界

本次只读固定副本核对了：[NotebookWorkingState.update](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/notebook_model.py:235)先组装整个draft、校验后一次持久化；[Candidate校验](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/notebook_contract.py:193)允许“有效Notebook refs”或“非空确切Messages”两种形态；[archive](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary/secretary/notebook_model.py:277)拒绝仍有入向引用的源。因而该转换**在接口上可原子表达**，不需要先制造非法的无来源Candidate，也不需要先关闭Candidate。

必要顺序如下，任何一步不能用“标记已settled”代替真实处理：

1. 先从现有批准和实际动作轨迹确定写入覆盖，与源条目当前内容/版本比较。若源有未覆盖责任、后续纠正或另一未完成候选依赖，先保留对应范围；并不是因为本候选写成功就把源归档。源因其它依赖仍应保留时，只需完成符合原规则的保留/改写，再关闭本次已完全结算的Candidate；**不为追求清空最后ref而强制转换所有候选**。
2. 只有源确实满足可归档条件、且Candidate的入向引用阻止归档时，准备仍能支持Candidate当前描述的确切Message来源。原来源若只是时间范围，须通过授权History找到真实UID；多个源/限定/纠正不能只留下其中一个好找的引用，更不能以“写入成功”那条工具结果替代所有原始内容证据。跨fork/继承来源必须经当前合法路径校验，不把旧父Conversation身份直接移植成新内容的许可证。
3. 对同一Candidate的一次update同时清空 `fields.notebook_refs`、清空 `fields.source_types`，填非空 `source_message_uids` 并令 `source_time_range=null`；保持其仍待处理的描述及实际状态，不将转换本身宣称为已交付/已结算。工具已有这些字段及原子校验能力，参数只是路径说明，本次没有执行。若仍剩其它refs可保持refs形态并准确保留它们/所需类型，不必过早转成messages。
4. 转换成功后再归档本次确实可归档的源，确认每个源实际成功处理；最后才归档已完全结算的Candidate，或按未完成范围更新它。若来源不可确定、引用校验拒绝、源操作失败或后续证据改变覆盖，保留未完成状态与具体原因，不伪报成功，不去读NM/收据质量替Noting扩大权限。
5. 转换后任务可能中断或在预算结束时提交当前合法工作态。此时Candidate仍存活且直接来源可回读；后续Noting必须仍能区分“已写但源尚未处理”和“全部结算”，不能因为refs为空就误认无需处理源。既有Conversation操作轨迹/可见工作态应足以恢复；这一点必须有针对性证据，静态“validator允许”不足以证明生命周期可靠。

**与现有Step4是否冲突：**“先处理源，再关闭Candidate”明确满足，因为转换不是关闭。Step4同时要求“归档源前修复阻塞引用”，为上述引用修复提供已有动作依据；“保留description和provenance直到源处理完”应保持原始证据和内容，不是允许丢来源后稍后补回。本方案只有在转换前后证据实质连续、未覆盖scope未被抹去的条件下符合该要求。现有Prompt没有明确写出最后ref的转换技巧，因此只能判**已有契约容许这一合法路径**，不能判当前模型已经能够稳定执行。此处不是替root授权改Step4；先用现有工具/指引取得正式路径证据，若模型仍被指引歧义阻塞，再集中呈现具体失败与最小Prompt澄清申请，不能为“方便过关”擅改。

**是否有更小方案：**当源仍因未完成责任/其它依赖应保留，按原有保留/改写路径处理即可，比转换更小；当最后ref指向的源确需归档，上述一次合法update→源处理→Candidate关闭是现有工具下的最小候选。不建议放开无来源Candidate、让归档自动级联、倒置关闭顺序、伪造临时源或普遍改回双来源；这些会改变已定状态/权限/事实语义，并且并非修正过时文本所必需。统一07/白板时要逐处核对词表、Schema说明、示例和生命周期文字，不能只删掉一句旧要求后宣布S02全关。

### 6.3 E02补充事实、证据精度更正与方案限制

已阅读 [provenance-feasibility.md](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/provenance-feasibility.md)，作为只读调查事实输入，不作为新产品判据；本次未重放CLI/HTTP请求，也未读取其私人原始轨迹。其记录的当前CLI版本/help、实际root缺技能索引、唯一合成目标GET拒绝，与本次固定源码的helper命令组装和Skill示例对应。具体判断如下：

- **可发现性不是单纯模型不遵循。**已记录的实际system没有 `nm-cli` 索引；存在skill工具面不等于模型已看见这个技能。将现有技能通过原生discovery纳入当前Profile的新root，是合理的最小接线候选。仍需证明安装目录、root索引、`skill_view`解析的是同一个版本，不能仅看磁盘有文件。
- **helper当前参数确实不能以“skill选到就能用”关闭。**固定 [personal_cli.py:169](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/personal_cli.py:169)把 `--space`放在`m add`之前，调查记录0.10.103解析拒绝。移动到该子命令正确参数位置属于接口兼容修复；不要顺便把name/alias语义改成另一种ID契约，不放宽顶层ID解析或未知创建处理。
- **“技能文案完全不改”留有已知矛盾。**固定 [SKILL.md:46](/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider/nowledge-mem-hermes/skills/nm-cli/SKILL.md:46)的等价CLI示例同样把Space放在全局层。先做发现接线可继续，但不应对模型宣称这个错误示例已与修复后helper一致。root应核明现有授权是否涵盖这一行纯调用语法更正；若当前白名单确实只允许配置发现/不许技能正文，则保留该未关闭项，集中申请最小示例更正，不借机改技能行为政策或通用Prompt。本评审不自行授权修改。
- **GET被拒与Metadata能力是两个结论。**调查记录一次HTTP403/1010，使现有先GET再PATCH链在当前部署读阶段不可用；PATCH契约、字段合并/保留语义尚未验证。不能据此宣布服务端不支持Metadata，更不能换UA/凭据/endpoint或绕过CF来冒充普通工程修补。可继续只读寻找正式客户端/上游认可的窄入口；涉及接入策略/服务修改、新权限或真实写入须依相应授权办理。
- **更正初稿措辞精度：**§5 E02的“Memory无Hermes来源metadata”应理解并收窄为“已观察创建调用没有传递Hermes来源，且没有证据证明来源元数据实际持久化”。官方show未展示metadata不证明服务端字段一定为空；本次GET也未返回Memory对象。E02“现有来源交付链未被证明且实际调用绕过”的判断不变，不把缺证伪装成已读到空字段。
- **创建成功与来源补写成功仍分开结算。**已知Metadata读入口不可用时，修好helper可创建并返回partial，但这不是E02完成。不要为了证明接线连续制造更多真实Memory；未获授权不能写。按既有具体批准处理真实动作时，保留已创建ID、准确说明来源附件未确认；repair只针对同一目标，不重建，不把来源塞进自然语言正文或伪装NM原生Thread来源。Noting依据可见实际结果结算本次批准覆盖的内容，Main须把未完成的来源交付准确留在轨迹；不能把可见partial描述成全部完成，也不能强迫Noting探查目的地质量。

E02完整关闭至少需要三个独立事实同时成立：①模型确实发现并使用正确接线，且提案回查/内容标签不再遗漏；②正式目标端支持且当前普通访问路径能够执行精确来源附件，范围/返回/合并语义明确；③在已有或另获具体授权的受控合成目标上，实际结果可回查并能从派生内容恢复正确原文。前两项工程修补不代替第②项契约，也不代替第③项实际证据。若目标端暂不可用，可继续交付已修子项并保留E02，但把“来源附件未完成”接受为本轮最终交付范围必须由用户决定，不能由审查者豁免。

### 6.4 本次方案评审后的状态

- **允许按已有授权继续的工程方向：**F01/F02/F03局部正式接缝修复；helper参数层级兼容；原生skill发现配置；S02不改变exclusive/权限/先后顺序的规格一致化与合法转换验证；Q01测试策略/部署身份分层但权限等效；Q03有界原文可达性及现有可见渠道的准确降级反馈。需要影响用户预期的细化仍按仓库规则登记自主收敛，不把本评审伪称用户确认。
- **仍待明确授权/决定：**S01与Q02硬编码Prompt修改（root已申请，未答不实施）；Step4若后续实际失败证明必须改，应单独列最小澄清；错误Skill示例的修改范围须root核实，不能用配置发现授权代签正文修改；正式部署写权、远端一致性修复策略、接入策略改变或新的真实NM写范围不由本方案扩张；保留Metadata/暂停归档限制的最终交付范围不能自行接受。
- **没有任何实现问题关闭。**待三包完成后提供不变的增量源码/规格快照、文件manifest及相应必要证据，再作代码复审；本次不审半成品，不重复测试。新方案相关的定向证据可复用，旧已过证据只在依赖仍一致时复用。
- **验证门禁保持：**E01新版root及自然Idle、E02真实来源交付、E03行为/生命周期、E04恢复边界和E05真实UI仍分别列账。PI-11继续生效；没有合规且不改变显示的后台IAB接口时，E05仍未验，不能安排任何可见页面/外部浏览器操作。

# 第二次全范围复审：独立判据阶段

## 1. 审查对象与结论概览

- 审查者：独立 Verification，Astra/high；2026-10-18；本次为全新判据提取，未读取实现者上下文或旧审查结论，未派生 Agent。
- 依据：本轮 `snapshot-index.md` 的授权与目的、权威顺序及 PI-01～PI-19；冻结原文 `inputs/product-intent.md` 全文 1–304 行；身份参考全文及两份 SOUL 只作待核对文案，不提升其旧工具权限。已完整阅读 `autonomous-run`、`spec-implementation-review` 及根 `AGENTS.md`。按独立阅读契约，本阶段不读动态 CLAUDE。
- 固定原文 SHA256：产品文档 `955bd57947841d707bdb91300e923bc12d78c0f26f1f3d24f1d247f64d671780`；身份参考 `8e69b78a82ceb8a4604d9c67fc014d7fea093c0679bd06015f8dabe3d45fe815`；主助手 SOUL `6fff7eef65cd47d7252fe114fad929b9e7ddf38b778b218fe1f1b428aa1e6823`；考研 SOUL `131b1cb5da6c26d15156e7cf1310387829f2a26cc65e3983dd1796933cb3b70f`。均与原始 manifest 匹配。
- 范围：公开核心、独立 Secretary Web、个人 NM 接入构成的完整当前使用链；涵盖既有连续性、Notebook/Noting/History/Reminder、身份与权限、个人实测、UI 和最新后台 WS/恢复/反代要求，不限于最新接线包。
- 待审实现版本、`baseline.txt`、运行加载版本及实测版本：依派遣契约等待主会话最终不可变交接。本阶段未读取索引列出的旧源码快照，不将其自动认定为第二次复审最终版本。
- **阶段结论：独立判据完成；实现审查尚未开始；本阶段不作 Verification 门禁通过/不通过判定。** 下列“待查”是阅读顺序状态，不是判整个新版本失败，也不是豁免任何适用场景。
- 本阶段没有运行测试、模型、NM 调用、UI、服务重启或改动产品实现；未读取 README、06/07/08、白板、实现代码、测试、旧 verification 正文、历史实测或实现者自评。旧报告全部保留，此节只追加。

## 2. 独立要求清单与覆盖

建立时间：2026-10-18T10:29Z 起；落盘时间见本阶段独立证据目录 `append-proof.json`。下表为接触实现前的原始判据，后续补充只能依据产品原文、明确用户口径和适用工程契约，并记录改变理由。

来源缩写：P=冻结 `product-intent.md`（行号）；PI=Snapshot Index 用户明确口径；G=根 `AGENTS.md`（章节/行号）；I=身份参考；S=两份部署 SOUL。类型中“机制”要求正式接线与状态证据，“行为”要求真实模型样本与实际结果，“边界”约束本轮范围，“执行”约束取证方式。标记“薄弱”表示方向明确但具体实现仍需后续独立查证，不能因此免责或任意换机制。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| V2-01 | P11–31、71–97、270–272、294–304：完整生活的长期助手 | 行为；当前主助手/专职助手 | 直接要求：学习、职业、知识、情绪与自然交流均有价值；不默认 Coding/企业办公，不将倾诉强转任务；不冒充专业治疗师 | 实际身份与提示支持多种交流；实测覆盖事务、答疑、探索、倾诉，不以角色宣言或只测提醒代替 | §3 V2-01 |
| V2-02 | P49–59、224、266–268：Conversation 长期存在，Session 是执行单位 | 机制；所有 eligible 长期空间；薄弱 | 原文直接要求及必要推导：底层上下文变化不迫使用户新开空间、重新介绍；不能仅给旧 Session 改名 | 从正式入口跨压缩/交接可回到同一 Conversation；历史与现行背景可用，所属关系稳定；保留可审计实际载入证据 | §3 V2-02 |
| V2-03 | P59–65、67–69、89、274–276、300：多空间组织自由 | 机制/边界；当前产品 | 不强制三角色、唯一主助手或 Conversation/Profile/Memory Space 一一绑定；用户偏好不变产品限制 | 可同时保有和返回多个 Conversation；每个可独立持续；组织选择不由容量限制强迫，既有多入口保持 | §3 V2-03 |
| V2-04 | P99–103、228；PI-10：同 Profile 历史互搜 | 机制/权限；History 正式工具 | 已有能力须真实可用；同 Profile 可检索其他 Conversation，不因此推导跨 Profile 权限 | 同 Profile 跨空间实际命中并读取原文；不存在仅当前会话过滤或未经授权跨 Profile 读取；检索与读取身份一致 | §3 V2-04 |
| V2-05 | P107–113、189–190、224–225、258–260：记忆连续性 | 机制+行为；Compaction/Notebook/History/NM 当前链 | 重要信息不必永久全量驻留，但应保留并按相关性找回；摘要不应成为唯一事实 | 压缩前后、话题切换、久远事项突问有原始材料找回路径；区分缺失与不确定，不编造；机制证据与模型表现分记 | §3 V2-05 |
| V2-06 | P115–125、191、262–264：责任连续性 | 机制+行为；已接受事务；薄弱 | 必须保留原因、目标、进展、阻塞、下一步和行动边界；用户没继续说话不等于撤销，不把闲聊自动登记成承诺 | 正式受理→持久背景→压缩/唤醒→后续推进可追踪；纠正/未完成/暂停等待权限不丢失；不只判断是否存在一条待办 | §3 V2-06 |
| V2-07 | P127–135、192、226：Reminder 自唤醒行动连续性 | 机制+行为；无新用户消息场景 | Agent 可自己创建并在恰当时机恢复已授权责任；准备提醒不等于真正唤醒/执行 | 创建、到期、目标 Conversation/Profile 唤醒、执行、结果可审计完整接线；用户不发新消息仍工作；错误/重试不伪报完成 | §3 V2-07 |
| V2-08 | P131–133、227；PI-13：未来 24h 内至少一条 Instant | 行为及获准 Prompt；非代码强制日配额 | 原文明确是模型行为约定；未来滚动 24h 的既有承诺检查，不能降成仅“支持创建”，也不能擅增强制调度器 | 正式注入可见该约定；真实模型与实际 Reminder 核验，而非自述；无凭据不得称永远可靠；不要求新增代码强制配额 | §3 V2-08 |
| V2-09 | P157–171、194–196、200、278–280；PI-13、17 | 行为/边界；主动跟进与静默 | 先关注已有责任，非每次唤醒都造任务或通知；静默是无需打扰，不是删执行事实或任意隐去气泡/未读/通知 | 有进展、无变化、无权限三类观察；不把 NO_REPLY 或未获批隐藏方案当要求；真实状态及 Timeline 仍能观察 | §3 V2-09 |
| V2-10 | P137–155、193、282–284：事实、决定、旧结论、推测可区分 | 行为+当前数据契约；完整长期治理属未来 | AI 可以新见解，不能写成用户已确认；修订不能抹去重要前提或原话 | 提案/确认/修订/冲突样本对应真实原文和结果；当前机制不制造不可辨别的伪事实；不要求本轮实现完整决策演化系统 | §3 V2-10 |
| V2-11 | P141–153、190、193；PI-13、15：直接查原始依据 | 机制+行为；当前 History/来源引用；薄弱 | 索引/摘要不等于已读内容；历史事实不是当前现实；获准同源分页不能混用其他语境来源 | 能从整理内容/引用定位准确原文及时间，长内容分页完整可续读；新决定与旧结论可区别；不把只看摘要作为精读证据 | §3 V2-11 |
| V2-12 | P173–210、236–254、286–290；PI-02 | 取证方法/行为观察边界 | 上线前验证当前设计与具体案例，上线后长期体验另行认识；不设 Muse 基准、即时评分或扩大托付目标 | 场景覆盖十项观察维度，含“应发生但未发生”；以用户预期和事实为证，不以单次演示推导数月可靠/模型升级后效果 | §3 V2-12 |
| V2-13 | P77、99–103、155、212–234；PI-01 | 范围边界；未来愿景 | 正式跨 Conversation 委托、责任同步、跨 Profile 共享及完整记忆治理非本轮自动开发项；本轮指定 NM 跨 Space 读取是窄授权 | 不将未来条款列为当前缺陷；不声称已经完整实现；现有机制与明确 PI 授权仍须审，不能以“未来”免掉当前来源、权限或历史完整性 | §3 V2-13 |
| V2-14 | P71–97；I3–18、22、38、46、60；PI-01、03 | 身份/表达风格；部署 SOUL | 可采用长期顾问、诚实独立清晰、按情绪语境回应、转写理解；旧 Pi 工具、默认写权限、飞书时刻和调度职责不继承 | 对照实际装载的身份文案与行为，主助手/考研分工合适；无旧工具权限与固定调度污染；参考身份不是覆盖最新权限的依据 | §3 V2-14 |
| V2-15 | PI-01、03；S两份全文 | 部署边界；人格和访问设定 | SOUL 可直接部署，不含扮演测试或 10分钟一天；测试授权不是永久人格授权，具体 Space ID 必须是真实身份 | 实际加载 SOUL 无测试措辞，角色/Space 标识可核对；区分永久文案、实测角色说明和本轮访问授权；不得自定永久权限 | §3 V2-15 |
| V2-16 | PI-01、08：两本机 Profile、真实 NM、Noting | 实测环境/权限；本轮链 | 两 Profile 都启用 Noting/插件；主助手 Default 只读，通过获准 NM 读考研 Space，不能读考研 Hermes Profile；考研按授权目标空间操作 | 实际进程/profile/插件/工具结果匹配；跨领域查询从 NM 正式入口完成；权限和数据归属不因同机共享失效 | §3 V2-16 |
| V2-17 | PI-02、03：实测时间与代理模型 | 执行/证据边界 | 每条普通 user message 含用户指定角色/尺度/禁止调查 Harness 说明；现实10分钟一天仅测试叙事，不改系统钟；DeepSeek 本轮代理 | 原始请求与时间戳可查，实际功能而非复习表演/伪进展；不把 DeepSeek 样本当 K3 通过，不以模型自述取代工具结果 | §3 V2-17 |
| V2-18 | PI-04：联合 Idle Compact + Noting | 配置+机制；两个 Profile | 100000 tokens 触发阈值、空闲当前5秒；模型容量原生不变；两个 Profile 均在联合开启状态测试 | 实际装载配置、容量信息和触发记录可查；走正式空闲/压缩/Noting 链，不能只手工 helper 代验 | §3 V2-18 |
| V2-19 | PI-05；G65–70：模型可见 Notebook | 机制/Prompt 边界 | 不向 Hermes AI 正文泄漏内部 Snapshot ID、Pointer、Coverage anchor；保留完整 Notebook 与有意义覆盖说明，实用 entry_id/message_uid 不能误删 | 检查真实模型请求、工具结果及后续注入所有适用分支；仅 UI 隐藏不够；内部审计/API 兼容与信息完整性仍保留 | §3 V2-19 |
| V2-20 | PI-06：首页独立 Profile 下拉 | UI+原生环境机制 | Profile 不混入模型选择；新 Session 模型/SOUL/原生环境随选择，旧 Conversation 归属不变 | 从首页切换→新会话→实际请求/身份确认；返回旧会话保持旧归属；非仅视觉标签改变 | §3 V2-20 |
| V2-21 | PI-06：跨 Profile 侧栏及图标 | UI/数据归属 | 首页当前 Profile 不能过滤掉其它 Profile 会话；每条图标按自身 Profile，固定前端映射不增配置 | 两 Profile 会话同时可见，切换选择不误换归属/图标，重载恢复一致 | §3 V2-21 |
| V2-22 | PI-07：首个 Thinking 流式可见 | UI+流式机制 | 首段 reasoning 在生成期间即可呈现，不能等 completion 后补画冒充实时 | 真实流式时点证据和消息/状态路径，包含后台触发路径的适用 reasoning；未提供 reasoning 的模型分支明确说明 | §3 V2-22 |
| V2-23 | PI-07：工具卡状态与完成高亮 | UI+事件机制 | 正常执行/中间工具结果不短暂误报错误；完成高亮对应真实完成，失败也真实保留 | 连续工具及中途接入/结束结果检查开始、执行、成功/失败状态序列；静态最终截图不能证明无闪烁 | §3 V2-23 |
| V2-24 | PI-07：提示寿命 | UI | 普通提示统一5秒，错误需手动关闭；不能用自动消失掩盖错误 | 两种真实提示显示与消失/关闭行为可复核，不只校验常量 | §3 V2-24 |
| V2-25 | PI-07；G96：冷启动统计估算 | UI+兼容；可选估算许可 | 允许沿上次可信值估算 Context/Session Total；不要求虚构精确值，展示/估算失败不阻断主逻辑 | 数据来源/适用会话可信，恢复显示不混 Profile；真实统计到达可更新；没有可信值时不冒充精确，失败可继续使用 | §3 V2-25 |
| V2-26 | PI-08、14：真实 Memory 写入批准 | 权限+行为；真实写操作 | 必须明确批准具体内容与目标；提案、只改措辞、沉默、Space 的一般写权限均非逐条批准 | 正/负授权输入与真实写结果逐一匹配；拒绝/未批准不得创建；不把归档原始线程当 Memory 交付 | §3 V2-26 |
| V2-27 | PI-15：Candidate 来源二选一 | 数据契约/机制 | Notebook 条目引用型或 Message Identity 型，禁止混用；引用必须有来源，不拿派生反向视图当来源 | 正式读写 schema/校验及真实工具链能保证互斥和有效身份；合法两型均可用、非法混用被拒绝 | §3 V2-27 |
| V2-28 | PI-15：引用型 Candidate 特化简述 | 数据契约+模型行为 | Notebook refs 型不得重写条目正文；按 Memory/Rule/Skill 身份简述，避免重复事实漂移 | 三身份候选与引用型实际内容可查；保留来源引用并聚焦对应交付用途，非复制正文或通用无用途摘要 | §3 V2-28 |
| V2-29 | PI-08、15：交付结算与关闭顺序 | 机制+行为；薄弱 | 以真正成功交付所覆盖来源结算，先结算后关 Candidate；部分成功不得消掉未交付责任、纠正或其它依赖 | 成功/失败/部分覆盖/多依赖正式路径，状态时序和持久结果匹配；准备/尝试/API返回前不能当完成 | §3 V2-29 |
| V2-30 | PI-14：窄 Memory create helper | 指定机制；NM 创建 | 一次正式 API 创建并携 Metadata，复用同一连接；不是多个副作用拼出看似成功结果 | 正式调用链/请求/对象元数据证明单次创建和连接复用；异常不伪报完成，不重建旧 partial 对象凑成功 | §3 V2-30 |
| V2-31 | PI-14：其余 NM 操作保留官方 CLI | 架构/权限；NM 非创建操作 | 窄例外不等于全面绕过 CLI、原生权限或审批；真实 NM 与隔离空间必须一致 | 实际工具路由、CLI 调用、权限结果及获批目标核对；不引入平行 NM 执行框架 | §3 V2-31 |
| V2-32 | PI-10；G95：不启用即原生 | 机制/兼容；关闭、非 eligible、纯原生 | Secretary/Noting 关闭不改变原生模型、会话、工具、错误或默认行为；新接线只在合法接缝 | 从正式入口对照各关闭分支及未启用客户端；后台 WS/History 等改动也需评估回归，不只正常新功能路径 | §3 V2-32 |
| V2-33 | PI-10；G96：API 增量兼容 | 机制/接口 | 仅增可选参数，默认兼容；既有必填、返回语义、错误码与调用方式保持；最佳努力辅助失败不阻断 | 旧调用方、缺省字段、错误路径、新旧前端适用调用可查；恢复/统计/持久辅助失败不升级成主流程失败 | §3 V2-33 |
| V2-34 | PI-06、10；G97–100：原生归属与运行环境 | 机制/隔离 | 后台 tick/线程/RPC/子进程绑定目标 Profile，模型/provider 继承原生；不得拿启动者替换目标 | 交错两 Profile 的请求/Reminder/恢复均只用目标身份、配置和状态；不硬编码 home、不新增独立路由或回退 Codex Proxy/App Server | §3 V2-34 |
| V2-35 | PI-09、13；G79–89：Prompt 授权与注入 | 权限/机制 | 已授权内部标识、S01/Q02及明确 History 同源分页文字；其余写死 Prompt 不擅改；真实构建结果比常量更权威 | 差异逐项对授权；实际 system、项目上下文、skill/tool/runtime/control 注入核验，无越权新增产品行为 | §3 V2-35 |
| V2-36 | PI-13；P25–27、169：直接回应与委派 | 行为/获准 Prompt | 答疑/建议/交流直接回应；适合 Agent 的执行事务委派且审核；用户要求亲自处理优先，不等于正式跨 Conversation 协作授权 | 三类任务真实样本及委派后的审核结果；不把全部交流委派、不把“亲自”要求覆盖掉，区分原生 Agent 委派与未来跨空间协作 | §3 V2-36 |
| V2-37 | PI-17、18：所有来源 Turn 的实时状态 | 机制/WS；薄弱 | Turn 是否由 Web 发起不决定前端能否看到；已有正式运行接线统一产生真实事件，不另起代理执行机制 | 订阅在场时后台 Reminder 与 Web Turn 均显示真实开始/流式/工具/结束或失败；不可仅 Web 请求方本地状态；隐匿静默事件不合格 | §3 V2-37 |
| V2-38 | PI-17、18：任意时刻中途接入 | 机制/WS+UI；薄弱 | 无前端时已有 Turn 运行，前端接入应还原当前状态并继续跟随；订阅/恢复交界不得漏发/重复/错归属 | 后台先启动再接入、工具运行中接入、接近结束接入三类风险时点有事实证据；状态与 Timeline 保持一致，非靠下一条新事件才看见 | §3 V2-38 |
| V2-39 | PI-17、18：完整 Timeline 与完成后恢复 | 机制/持久历史+UI；薄弱 | 有界事件 ring 不能替代完整恢复；迟接入或重新打开仍有完整执行事实，不丢早期 Thinking/工具/文本及失败等实际存在项 | 超出短期缓存覆盖的长执行与完成后再接入，原始事实与恢复 Timeline 对齐；顺序、身份、内容、终态正确；恢复不重复重跑业务动作 | §3 V2-39 |
| V2-40 | PI-17、18；P200：静默执行事实可见 | 机制/行为边界 | 静默无需造用户回复，但不能清空/过滤执行事件；NO_REPLY/隐藏气泡未获批准 | 无可汇报内容的后台检查仍有真实 Timeline/状态；不得以未获准组合策略过滤；不从“静默”推出必须通知或必须造消息 | §3 V2-40 |
| V2-41 | PI-16、18：本地反代真实部署拓扑 | UI/部署/正式接口 | 独立 Secretary Web 与原生 Dashboard 同域同后端；浏览器访问反代端口检查 URL 路径；source=desktop 不是 Electron | 正式反代入口的静态资源、深链/刷新、API、WS、两 Web 入口及路由路径取证；不能以 dev 直连/API curl 代浏览器拓扑验收；只豁免 Cloudflare Access | §3 V2-41 |
| V2-42 | PI-11、12：无显示变化的验收 | 执行约束 | 仅隐藏 Codex IAB（visible:false）是 CUA 例外；禁止外部浏览器、桌面、可见页、焦点/窗口变化 | 后续 UI 证据说明接口与隐藏方式；无法保证则记未验，不用外部浏览器替代，也不把未验改为通过；本阶段不操作 UI | §3 V2-42 |
| V2-43 | PI-02、04、16–18；G118–123：证据版本与正式链 | 取证方法 | 磁盘文件不是进程已加载证明；实现说明、测试自报和旧证据不等于当前版本事实；代表样本不免必要分支 | 每条实现结论能追溯固定源码、配置、加载版本及原始运行结果；同版本有效证据可复用，受影响路径变化需补证 | §3 V2-43 |
| V2-44 | G101、74–75；P111、143–153：Notebook 所有权 | 机制/权限 | 对话原文为事实源，Notebook 派生；主 Assistant 只读、Noting 独占写；Candidate/proposal/approval/action/actual write 不混为同一状态 | 正式工具与存储权限拒绝越权，模型自我克制不能替代；原文可追、快照内容与提交结果一致，派生反向视图不当主写源 | §3 V2-44 |
| V2-45 | G89、101、119：生命周期/并发/恢复 | 机制；身份、压缩、rewind、branch、Snapshot、Noting、Reminder | 根规则明确需覆盖这些适用路径；细节待冻结工程规格核查，不从旧代码猜规则；责任/权限/完整性跨生命周期仍成立 | 身份边界、Snapshot 原子性、并发提交/关闭、重启恢复、ACK/重试有正式接线证据；不以单线程 helper 成功替代 | §3 V2-45 |
| V2-46 | G65–89：模型可见世界与 cache prefix | 机制/Prompt | 内部实现审计信息不靠提示词解释；约束结构/工具层保证；冻结 Noting 任务显式覆写父任务边界，不中途重建 root/prefix | 真正请求的完整前缀/任务/控制消息核对，工具约束与权限分支可查；无中途改历史/重载记忆/切工具面破坏 cache 契约 | §3 V2-46 |
| V2-47 | G82；P111–113；PI-13：压缩后的恢复指引 | 机制/Prompt | eligible Main 的 Context Recovery 指向 conversation_history，含压缩区间/Conversation 起始时间；与 History guidance 同资格；非 Main 原生 footer | 正式构建摘要在更新时替换旧 footer，不留旧 Session 搜索指引；同源分页实际可恢复，不仅文字宣称 | §3 V2-47 |
| V2-48 | G93–100；PI-10、18：原生增量架构 | 架构约束 | 复用既有 owner/正式提交点与接缝；不增平行 Agent Loop、对话存储、admission gate、通用调度器或 API hierarchy；Secretary 自有表不改原表 ownership | 后续固定源码 diff 与上下游正式路径核对；后台可见性补齐既有链路，开发期数据重建不借迁移扩范围 | §3 V2-48 |
| V2-49 | G「公开范围与个人化隔离」「核心文档职责」；PI-01、10 | 发布/数据/文档边界 | 个人 NM、SOUL、凭据、专属行为不默认进入公开核心；稳定事实、规则、动态进度分别归根三文档 | 固定版本公开差异/待提交内容无凭据与个人越界；文档不把未实现/未验写为完成，不以分支名作为保密 | §3 V2-49 |
| V2-50 | G「规则冻结」「实现与代码规范」103、「本地 CI/CD」 | 质量/执行约束 | 既有检查类别、阈值、等级不放宽；仅文档长度门禁排除；新函数复杂度≤20、长度≤300、嵌套≤6、文件≤2000，既有超标不增加 | 后续核对适用范围/豁免与同版本检查证据；不因产品意图审查改变门禁；本阶段不跑检查 | §3 V2-50 |
| V2-51 | G87、112–123；PI-02、03 | 实测隔离/方法 | 测试 cwd 在 git root 外，隔离 runtime/HERMES_HOME，避免根 AGENTS 污染模型；Python 官方 runner/PM环境，不假造 host OS | 运行配置及请求实证；测试断言行为而非镜像实现/源码字符串；平台未测如实标注；本阶段不启动任何验证 | §3 V2-51 |

| V2-52 | PI-19（索引40行）：现有 UI/UX 保护与变更边界 | UI/修改约束；现有表现层基线 | 用户已完成表现层打磨；状态/恢复接线须保留现有布局、样式、动画、Profile图标、Pin/拖拽、滚动交互；优先复用既有组件，不挟带用户修改 | 以交接中用户最新表现版本为对照，逐项区分必要功能差异与表现回退；不得整文件覆盖或把用户变更混作本轮成果；功能证据之外需有适用交互保护证据 | §3 V2-52 |

覆盖反查：P§一→01/14；§二→02/05/06/12；§三→02/03/04/13–16；§四→05–09/18/44–47；§五→10/11/26–31/44；§六→01/09/36/40；§七十项观察→01–12/17/43；§八→13；§九→02–08/13；§十→12/17；§十一→01–12；§十二→01–13。PI-01→13–16；02→12/17/43/51；03→15/17/51；04→18/43；05→19；06→20/21/34；07→22–25；08→26/29；09→35；10→32–35/48/49；11/12→42；13→08/09/11/35/36/47；14→26/30/31；15→27–29；16→41/43；17→09/37–40/43；18→37–41/48。PI-19→52。没有将 PI-12～19 当作替代既有条款的新独立范围。

## 3. 逐条实现证据

本阶段仅建立判据。为保持每条覆盖可追踪，下列逐条登记，所有实际路径/运行证据均待最终固定交接后查核；这不是已经调查后的“证据不足”判定，亦不产生新版本门禁结论。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| V2-01 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-02 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-03 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-04 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-05 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-06 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-07 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-08 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-09 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-10 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-11 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-12 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-13 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-14 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-15 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-16 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-17 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-18 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-19 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-20 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-21 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-22 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-23 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-24 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-25 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-26 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-27 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-28 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-29 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-30 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-31 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-32 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-33 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-34 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-35 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-36 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-37 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-38 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-39 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-40 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-41 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-42 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-43 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-44 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-45 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-46 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-47 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-48 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-49 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-50 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |
| V2-51 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |

| V2-52 | 待固定源码交接后逐条追踪 | 已完成原文判据；实现/测试/运行未调查 | 本节§2同编号；实现证据待交接 | 待查，当前不作符合性判定 | 只覆盖要求提取；不声称已验 |

## 4. 核心目标及验证方法审查

目前无实现与测试方法结论，原因是独立判据阶段明确不读它们。后续审查须以本矩阵为起点，而非以实现包或旧缺陷清单缩减范围。

1. **长期可返回的 Conversation**：同时核查用户入口、上下文交接、Notebook、原文检索及责任的保持。反证重点：表面 Conversation 未变但真实 History/Notebook/Reminder 仍绑旧 Session；压缩后只有摘要而原始依据不可读；同 Profile 其他 Conversation 被遗漏。该目标要求现行机制正式接通，数月后模型良率属于长期观察，不由一次实测保证。
2. **权限、事实及交付真实性**：分别追踪用户批准、Candidate 来源、执行、实际成功结果、来源结算、关闭。反证重点：提案当批准；一次创建缺元数据再多次补写冒充单次；部分成功关闭整个责任；引用型候选重复正文；主 Assistant 可写 Notebook；NM Space 权限误推为跨 Profile 权限。代码硬约束与模型行为观察分开判断，不把提示词自述当结构性保证。
3. **Reminder 和前端全过程**：应分别有实时订阅、中途接入、完成后恢复三类证据。反证重点：后台无 Web 请求方导致无事件；先恢复后订阅或反之有遗漏/重复窗口；状态空闲但执行仍在；长执行早期事件超出 ring 后无法恢复；静默路径过滤事实；恢复后重复执行业务。完成时间线需要适用的文本、Thinking、工具与终态等实际事实可恢复，不要求凭空产生模型未输出的内容。
4. **真实部署和实际浏览器**：经本机反代访问独立 Secretary Web 与原生 Dashboard，检查 URL 路径、资源、API、WS、深链/刷新。后台 API 与开发直连只能支撑接口局部结论，不能替代该拓扑。Cloudflare Access 是唯一明确不验项；不据此豁免本机可覆盖功能。本审查者本阶段不操作 UI，后续复核符合隐藏 IAB 限制的取证。
5. **真实模型但不表演角色**：两 Profile、Noting/Idle Compact、真实 NM、获批 Memory 内容/目标、普通消息测试前缀与时间尺度均应匹配；请求、工具记录、持久结果为核心。样本应涵盖自然交流、答疑/建议、委派执行并审核、显式亲自、责任变化、无新消息推进、合适静默、历史纠正、授权拒绝，而非只演考研进展。S01/Q02 行为必须实测，不应擅加代码强制 24h 调度。
6. **原生与生命周期回归**：关闭/非 eligible、旧 API 调用、不同 Profile、压缩/rewind/branch、Snapshot 原子性、并发、重启、Noting 权限/开关和 Reminder ACK/重试是适用覆盖面。依据根规则保留；具体技术判据在冻结白板/07/06/08和旧保留条款阅读后展开，若与产品冲突则分别记规格偏离、实现偏离、证据缺口。
7. **证据效力**：源码/工程规格固定版本、现场装载版本、配置、前端构建、代理路径和实测时间需能对应。复用同版本有效证据，不重跑已有昂贵测试；需要补证时只针对缺口/影响。通过数量或源码字符串不等于目标成立，失败/未发生的预期亦需归因。

8. **现有 UI/UX 保护**：需要明确用户最新表现层基线与最终接线版本的对应关系，功能补齐不能回滚用户已打磨的布局、样式、动画和交互。检验状态传播/恢复新增行为时同时确认首段 Thinking、工具卡、完成高亮、提示时效及 Profile/Pin/拖拽/滚动等适用既有体验；不把新增功能成功等同于无表现回归。

以上反证问题是审查方法，不是声称目前存在这些缺陷，也不是替主会话指定新的实现设计。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| 无 | 本阶段仅原文与规则 | 尚未调查实现、历史结果或当前运行 | 无实现发现可判，不以交接尚未到达判新版本失败 | 下一阶段以不可变源码/规格和加载/实测证据逐条核验 | 独立判据阶段完成，等待既定交接 |

范围外边界：正式跨 Conversation 任务委托/责任同步、一般跨 Profile 共享、完整长期记忆治理、长期生活效果与 K3 模型总体良率不自动变成本轮实现任务；产品范例及 Pi 旧配置不授权新增角色模板、飞书任务或写权限。尚未发现可报告的范围外实现问题，因为未读实现。

必要解释保留：P 的“保持安静”与 PI-17/18 的“完整执行事实可见”同时成立，不能将未获批准的 NO_REPLY/隐藏组合提案写成完成条件；P 的每24h行为约定不能升级为代码强制配额。原始长期愿景不能被当成当前全面实现承诺，当前明确能力也不能借愿景边界免审。

## 6. 修复与独立复审

本次作为第二次全范围复审的独立判据起点：已从产品全文与 PI-01～19 新建 52 项矩阵，未阅读旧报告或实现者解释，未复用旧通过/失败结论；旧全文原样保留。

尚未开始修复复核，无旧问题关闭证据、实现版本结论或新缺陷判断。待主会话提供最终不可变三个仓库源码/规格 SHA 集、运行加载证明及实测证据后，继续同一次审查：先核验版本和范围，再独立阅读工程规格及正式代码路径，填充 §3 的逐条证据；随后才复核历史问题/测试方法及同版本证据，检查修复影响与遗漏。任何受影响的判据细化保留此原始版并引用来源；不得为迁就代码降低判据。

判据增补记录：落盘前收到用户最新 PI-19，已只读取索引对应原文并新增 V2-52；这是用户明确要求的补充，不是由实现形状反推。

关键研讨链：本阶段无实现发现或主会话修复方案进入审查，因此无工程收敛、权限更改或规格变更；无需用户决定的新产品口径。供最终交付摘要的当前事实仅为“全范围独立判据完成，尚未作实现门禁结论”。


### 6.1 第二次复审中途实质阻断包：终态失败事实跨运行时回收（2026-10-18）

本记录属于已完成独立判据之后的实现调查；不是最终门禁结论。待审仍为不可变 `delivery-snapshot/snapshot-set.json` SHA `ad4abaa634029c298fa1ebdf087bab72c7990d7596f6aaef4c7f7032895cf28c`；主会话另行准备 v2，尚未用移动实现补结论。

**V2-F04 / P1，V2-39、V2-40（PI17/18）：已产生的后台失败事实不能在完成后重新打开时恢复。** 固定 core `tui_gateway/session_auto_continue.py:558` 的 `_emit_terminal_turn_error` 把真实异常转成 `message.complete(status=error)`，只调用 `_fail_inflight_turn` 并发事件；没有写入持久历史或失败 sidecar。`session_history.py:439` 明确只保存于 session.inflight_turn，寿命为下次 Turn 或 session close。新 inflight_output 投影同样挂 session 内存；`session_lifecycle.py:946` 附近的合法 orphan reaper 对已结束 detached runtime 执行 `_pop_session_by_id`，使两份内存事实一起消失。`server.py:2990` 后的 `_live_session_payload/_live_visible_history` 在新 runtime 只能读正式持久历史，无法恢复前述异常终态；旧运行时的 replay ring 也不属于新 runtime 的恢复身份。后台 Reminder 经 `scheduler_host.resume_session` 使用 detached transport，并安排该正常回收，所以这不是只靠人为篡改状态才能触发的分支。

反例路径：合法 desktop Reminder 已 materialize → 正式 prompt worker/Provider或初始化异常经 `_emit_terminal_turn_error` 发出了真实终态 → 当时没有前端 → 正常孤儿回收/服务重启 → 用户稍后重新打开。既有持久 carrier/此前成功工具可能仍在，但本次错误文本、失败终态缺少持久权威。`agent/turn_finalizer.py` 可以持久化某些有 final_response 的失败正文，**不能覆盖** dispatcher exception/build失败等上述明确只有内存终态的分支；也不能以普通assistant正文代替精确失败状态。成功路径的 durable reasoning/tool sidecar测试不能关闭此反例。

检查方法：只读正式生产调用链与 `test_inflight_output_recovery.py`；该测试的 error 场景只检查同runtime retained projection，重启场景只人工持久化成功 user/assistant/tool/assistant，无真实失败→回收→重开。未运行新测试或改变服务。属于源代码已明确存在的恢复空洞，最小运行反证可由主会话统一安排；本报告不预设新表/新API/隐藏气泡方案，不要求复制事件日志。整改条件是沿既有合法事实持久化/读取接缝保留可恢复的失败事实与身份，并证明同owner后台失败在回收/新runtime后仍显示真实Timeline且不重跑动作，旧原生API默认语义保持。

其余52项继续审查；统一集成已发现的health/UI三项由root处理，本包不重复测试。最终结论等待不可变v2与加载/本机反代/Metadata现场证据。该发现不因它是原生既有边界而从PI18任意打开/完整恢复判据中豁免。

### 独立判据增补：PI-20 上云部署 SOP（2026-10-18）

来源：本轮 snapshot-index.md:41 的 PI-20，用户明确要求“最后，给上云部署留一份SOP文档”。这是新增交付物要求，不授予本轮上云执行权限；不得据文档声称 Cloud/TLS/Access 已验。原有52项判据全部保持，新总数53。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| V2-53 | PI-20：最终留上云部署SOP | 文档交付；现行部署/操作入口 | 根据最终实际拓扑、版本与产物给出可操作步骤；不默认新架构/新授权，不将本机HTTP或文档等同云端验收 | 正式docs文档及README索引；命令与当前dashboard/dual-SPA同后端路径一致；版本/产物绑定、profile状态备份和回滚、个人配置/凭据隔离、已验/未验边界明确；禁止把未授权远端操作写成已完成 | 后续实现审查§3 V2-53 |

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| V2-53 | 待最终v2固定SOP及README索引 | 按最终源码/启动参数/本机部署事实核对 | 待root不可变交接 | 文档撰写进行中；不提前作门禁判定 | 仅审SOP可执行性和事实边界，不执行云部署或Access验收 |

# 第二次全范围复审：ad4 固定源码与既有证据阶段整包（2026-10-18）

## 1. 审查对象与结论概览

**当前阶段完成，最终门禁仍待最终不可变 v2 与集中现场证据。ad4 已确认不符合项，不将其提前代称为尚未交接的 v2 失败，也不将等待视为通过。** 本阶段保持独立原始判据，以产品意图及 PI-01～20 为准；未把符合工程旧规格当作满足产品的替代证据。

本阶段源集为 `delivery-snapshot/snapshot-set.json`，SHA256 `ad4abaa634029c298fa1ebdf087bab72c7990d7596f6aaef4c7f7032895cf28c`。逐文件 manifest 为 core `a1db0b041ede64443a58857e6a382e612c27cfa3faf4d0e5269f50ec4f8b1c70`、UI `94bf12ea938f118a60b52e7007ada8dbadcf37e143c2487260f7a5b0751ca10e`、personal `a59bd2a42d553e054a361c61c085a0e47a36e50792550394f6eed5af1d1e6977`。固定 tree 含捕获的 dirty，不把 HEAD 标签等同全部内容。产品源核验匹配；两个历史 snapshot-index 为固定树内相对 symlink，跟随内容哈希与 link 身份计算差异单列，不是当前产品源码漂移。详见独立 `source-integrity.json`。

范围覆盖原始52项，并按用户 PI-20 追加 V2-53 SOP。实际阅读固定 README/CLAUDE、06/07/08与白板；正式路径涉及 Conversation/History、联合 Noting/压缩、Notebook写权限与原子提交、Scheduler/Reminder、模型输入与缓存边界、Profile/内核隔离、WS投影/恢复/UI、个人NM创建与归档。历史独立报告在判据建立后才读。各旧证据经依赖文件映射和方法核查；没有为了审查复跑大型检查或已有有效套件。

本 Agent 全程零测试、零模型、零 NM 调用、零 UI/浏览器/桌面/服务操作；未读凭据和 Default 私人正文，未修改产品、规则或其它人的实现。所有新增内容只在本 verification 追加与 ignored 独立审查证据目录。

## 2. 独立要求清单与覆盖

原始要求完整保留于前文“第二次全范围复审：独立判据阶段”§2（V2-01～52）；用户新增 PI-20 独立增补 V2-53 已附于前文。此阶段不重写或降低原始判据，表内“静态支持”“受控机制支持”“行为反例”“待集中现场”分别标明证据效力。V2-53不是上云执行授权。

全部产品章节与最新口径的覆盖反查仍沿原判据。技术解释冲突分别处理：06旧两次确认与较新单dialog条款按最新确认；白板旧 Snapshot ID占位不能压过PI05及07最新模型文案；原先暂停“serve宿主”的说明不能把headless握手页当双SPA，现行dashboard入口已有源码支持。

## 3. 逐条实现证据

下表代码路径指 `delivery-snapshot/` 下三仓固定副本；报告/证据路径未写全前缀时指 `.hermes-dev/product-intent-review-20261018/`，另明确写出的首轮F16为 `.hermes-dev/validation-personal-20261018/evidence/validation/f16-observation.json`。详细路径与方法见 `independent-reverification/review-notes-ad4.md`、`evidence-source-map-ad4.json`。表中待v2的范围已经安排交接，不因此提前结束最终门禁。

|条款编号|正式入口及完整关键代码路径|方法、输入、配置及实际证据|证据位置|判定及理由|证据边界|
|---|---|---|---|---|---|
| V2-01 | 部署 SOUL；secretary prompt；原生委派 | main/exam natural-idle：答疑、规划、纠正等实际 Turn | main/exam-natural-idle-live.md | 身份支持；行为仅部分覆盖 | 倾诉、情绪语境和新 Q02 委派/亲自尚无完整代表样本 |
| V2-02 | secretary Conversation identity→合法路径→原生压缩；Notebook pointer | 双自然 100k Idle 后仍相同 Conversation；正式 child 提交 | main/exam-natural-idle-live.md；repair-noting-protocol.md | 机制与代表链支持 | branch/rewind/restart 全边界另见45，不能由双样本概括 |
| V2-03 | 原生 session.new/list/resume；独立 UI controller | 固定源码保留多会话；两 Profile 多 Conversation 记录 | 06/07；双自然 Idle 报告 | 静态支持 | 最终多入口浏览器旅程待集中证据 |
| V2-04 | tools/session_history_tool.py→same-profile main scope→合法 History | 正式长读 handler 与 paging 受控测试；自然模型 search | history-long-read.md；authorized-prompt-sync.md | 机制支持 | 同 Profile 跨 Conversation 实际模型精读覆盖有限；跨 Profile 不获准 |
| V2-05 | compaction→Notebook→History；personal_provider prefetch/archive | 自然压缩完成；真实 NM 首次全文精读但自动 Recall 0 pointer | 双 natural-idle；recall-first-read-live.md | 部分成立；可靠召回未闭合 | 手工 search→show 不能代签自动 pointer 首读；归档暂停见Q03 |
| V2-06 | Notebook Context/Commitment；Reminder→provider ACK | 自然 Noting 保存责任；cold Reminder 真正唤醒 | candidate-lifecycle-evidence.md；repaired-reminder-live.md | 机制有支持，行为需分项 | 责任纠正/暂停/多依赖不能由有待办替代；归档暂停不可见 |
| V2-07 | secretary/scheduler_host.py→resume→deferred request→ACK | desktop 冷执行真实成功，旧 web source 失败保留 | repaired-reminder-live.md | 原有正式链有效；最终版待核 | 终态跨 runtime 回收缺口 F04；真实 v2 中断恢复待证 |
| V2-08 | 授权 S01 prompt 注入与 reminder tool | 原文24h约定已恢复；19机制测试核真实构建 | authorized-prompt-sync.md | Prompt 机制支持，行为待补 | 不能以 code 强制配额代替模型实际建未来24h Instant |
| V2-09 | S01/no useful update；模型最终文本 | 旧 cold Reminder 输出26字符无事汇报 | repaired-reminder-live.md | 已观察静默反例；新 Prompt 未关闭 | NO_REPLY/隐藏气泡未获准，不将其指定为修法 |
| V2-10 | Notebook contracts/source IDs；实际模型归因 | main 把用户假设归因助手；exam 合并独立字段 | 双 natural-idle 报告及 raw | 数据可追；模型表现有反例 | 不把同一代理模型样本推断成结构 bug 或未来K3通过 |
| V2-11 | conversation_history content_offset + digest + next | 30006 Unicode 分页；真实 NM show 全文546字 | history-long-read.md；recall-first-read-live.md | 长读机制支持，原文精读行为未全面成立 | 自然样本只 search 自称核原文，不能当read |
| V2-12 | 全范围52判据与实际样本/反例 | 请求、工具、持久结果而非模型自报；负面观察保留 | criteria-v2.md；本矩阵 | 方法遵循；场景覆盖仍待最终核验 | 长期生活效果/数月可靠性不能本轮证明 |
| V2-13 | 公开核心/个人插件分离；原生 delegate | 未发现新增跨 Conversation 责任委托机制 | 固定 core/UI/personal 源 | 范围边界支持 | 未来治理未实现不自动列缺陷；当前来源完整性仍审 |
| V2-14 | 实际部署 SOUL 指纹与内容；参考身份隔离 | 四份policy先核SHA后全文阅读，精确匹配；无Pi工具/飞书权限 | snapshot-set identity fingerprints | 静态身份政策符合；运行加载与行为另核 | 输入旧SOUL仅参考，不能当最终已加载 |
| V2-15 | Profile policy SOUL；仓外 AGENTS；每条测试前缀 | 部署指纹明确，测试时间尺度单列普通user | snapshot-set；load-profile-isolation-repair.md | 静态文本符合；实际加载待最终集中绑定 | 不得将测试限定永久写SOUL |
| V2-16 | personal provider owner scope；原生 Profile env | 双Profile realNM/Noting；main Default只读；exam授权space | 双 natural-idle；load-profile-isolation-repair.md | 代表链支持 | 最终新helper真实发现/获准创建待集中旅程 |
| V2-17 | 原生 DeepSeek custom provider；普通user完整前缀 | 双自然Idle与修复load真实wire、时间戳 | 双 natural-idle；load-profile-isolation-repair.md | 已有样本方法支持 | 不代表K3良率；不额外运行模型 |
| V2-18 | 原生 Idle Compact + Noting config/trigger | main101029/104312；exam102871；5秒真实触发 | 双 natural-idle 报告/原始持久证据 | 代表链通过 | 主首次取证 premature close 失败保留；新加载不等于重新自然触发 |
| V2-19 | notebook_render→show/control/framework completion | 同owner真实anchor转可读coverage；原子正文投影 | repair-coverage；双 natural-idle 真实请求 | 机制与实测支持，原F01可据同源关闭 | 实用entry/message UID保留；白板旧占位不高于PI05 |
| V2-20 | UI profiles.ts/controller→native session.new owner | Profile选择与新旧session owner解析 | 固定 UI 源；最终浏览器待交 | 静态支持，UI现场待核 | 标签变化不是模型/SOUL实际切换证明 |
| V2-21 | loadSessions all profiles；profile icon映射/sidebar | owner+storedid key；最新sidebar两行必要变更 | presentation-baselines.json；固定UI | 静态支持，UI现场待核 | 断连列表引用回归ad4已被统一检查发现，待v2 |
| V2-22 | projection reasoning.delta→即时thinking | 流式事件即时归并，无completion gate | 固定 projection.ts；UI机制测试 | 机制支持；真实流式现场待核 | 模型不发reasoning不捏造；后台来源同样适用 |
| V2-23 | tool.start/result→toolResultState；message.complete | 仅明确false/error/nonzero判错；未完成unknown | projection.ts；UI相关证据 | 机制支持；连续界面状态待核 | 最终截图不能排除短暂假错 |
| V2-24 | native-notices normal5000/error手动 | 通知rail真实生产常量及owner归属 | native-notices.ts；UI测试 | 静态支持；现场时效待核 | 不以constant单独签UI |
| V2-25 | 原生usage/context冷估；controller merge | 完整冷读model_config精确断言；session/model/代次标识 | cold-estimate-assertion-sync；final-integration-checks | 生产机制有支持；v2 test组织待核 | epoch恢复timeout仍是ad4实测回归，等待v2 |
| V2-26 | 个人Skill批准政策→personal_cli create | 具体内容/目标须由真实普通user批准 | metadata-create-api.md；新创建证据待交 | 政策/接口支持；真实写入闭环待核 | 空间一般写权限不等于逐条批准；不读Default私人正文 |
| V2-27 | notebook_contract三目标exclusive sources；noting_tools | 52受控契约；正式child lifecycle10复用 | candidate-source-contract-sync.md；source-map-ad4 | 结构支持 | 正文是否实际特化属28，不由schema保证 |
| V2-28 | Candidate refs型按Memory/Rule/Skill brief | schema/prompt授权；真实自然候选有限 | candidate-source-contract-sync.md；双自然Idle | 机制支持；模型语义证据有限 | 不得复制来源正文冒充特化简述 |
| V2-29 | Noting source mutation→Candidate final state；引用校验 | 正式child 10场景含partial/pending/restart等 | candidate-lifecycle-evidence.md；source-map-ad4 | 受控机制支持 | 旧F16真实source v13→candidate v14结算且未覆盖保留可复用为代表；新helper/多依赖须版本关联 |
| V2-30 | personal_cli→native connection→single API create metadata | 7文件manifest全同；安装9文件新版本 | metadata-create-api.md §8 | 静态/受控支持；一次真实create待证 | 旧partial禁止重建，API失败不假报完整 |
| V2-31 | 非create走personal_client官方CLI；Skill路由 | alias解析/CLI show/旧attach显式 | personal_cli.py；personal_client.py | 静态支持 | create后metadata GET只校验；不引入平行执行框架 |
| V2-32 | eligibility/global/local checks；native context hook suffix分流 | 关闭原生selector仍工作；Noting output cap单独分支 | repair-noting-protocol；固定源 | 受影响路径受控支持 | WS为原生新可选投影仍须旧caller兼容；F04修复需再核 |
| V2-33 | DTO optional owner/epoch/inflight；history optional offset | 25后端文件与有效兼容包同SHA；旧默认保留 | websocket-backend-state.md；source-map-ad4 | ad4静态/受控支持 | v2持久终态新字段/默认与旧读路径须复审 |
| V2-34 | session profile runtime scope；code_kernel scratch helper | 真实2execute_code内核/脚本/spill环境各归owner | load-profile-isolation-repair.md；44受控 | 受影响隔离机制与代表现场支持 | 实际大输出落盘未发生；不硬扩成全部平台已验 |
| V2-35 | 三处获准Prompt常量/文档同步；真实rootwire | S01/Q02/History分页精确授权差异 | authorized-prompt-sync.md；snapshot-index | 目前授权边界支持 | 不得悄改静默策略；最终v2差异再核 |
| V2-36 | 授权Q02：直接回应/适当委派/亲自优先 | 新prompt实际构建；旧代理样本不全面 | authorized-prompt-sync.md | 机制已改；行为证据待补 | 原生Agent委派不等于未来跨Conversation协作 |
| V2-37 | 原生stamp→inflight fold/replay→sessions.changed | 同seq锁、native callback全来源；130受控有效 | websocket-backend-state.md；source-map-ad4 | ad4机制支持；现场待v2 | 真实后台Turn非Web发起；F04终态另项 |
| V2-38 | UI session-recovery snapshot+continuation+strict seq | 8文件同SHA；gap有界retry；epoch/generation归属 | websocket-state-recovery.md；source-map-ad4 | ad4存在统一集成3回归；v2待核 | 不能将bounded retry或active list当完整恢复 |
| V2-39 | native durable History + inflight snapshot + ring | 同runtime超ring有效；error只内存并可正常reap | terminal-failure-recovery-finding.md | ad4不符合：F04 P1 | v2须正式持久writer/冷读；真实中断闭环+受控build/dispatcher可组合关闭 |
| V2-40 | 无事件/Timeline过滤；真实后台终态持久 | 静默执行也走原生event，terminal error却可回收丢失 | F04；固定backend/UI | ad4受F04阻断；静默模型另记09 | 无授权NO_REPLY/隐藏气泡不得引入 |
| V2-41 | dashboard --no-open→dual SPA prefix middleware→same ws/api | 48 HTTP两WS已成功；serve headless失败保留 | local-deployment-browser-validation.md 加载里程碑 | 加载/拓扑接口支持；浏览器待最终产物 | HTTP不代签UI；CloudflareAccess唯一明确排除 |
| V2-42 | 审查无UI工具；取证只hidden IAB | 本Agent零UI/服务/模型；root后续隐藏浏览器限制 | 本审查工具历史；现场记录待交 | 审查执行符合 | 不使用open/其它浏览器/桌面或显示变化 |
| V2-43 | 固定三个tree manifest；source-map；加载指纹 | ad4全产品hash匹配；2历史symlink另释；新backend已载过渡artifact | source-integrity.json；source-map；加载里程碑 | 源码版本可追；最终v2/现场待绑定 | 移动工作区不作为符合性源码；源文件存在不等于已加载 |
| V2-44 | Main只读；noting_scope四工具；retired alias统一拒绝 | 正式child write session；storage source/anchor validation | repair-noting-protocol；candidate生命周期 | 静态/受控支持，原F03可据同源关闭 | 工具拒绝非仅Prompt自律；临时Notebook不是独立事实库 |
| V2-45 | pointer transaction；framework same transaction；Reminder deferred/ACK | 正式child fail/interrupt/forced/restart；late snapshot丢整条 | candidate-lifecycle；repair-noting；旧门禁证据 | 适用机制有分支证据；完整边界待汇总 | Reminder late/cancel/restart与NM rewind归档降级需单列，不能笼统全通过 |
| V2-46 | frozen parent/root/tools；selector只suffix；child四工具 | 真实AIAgent4calls/2Turns；nativeoutputcap7pass | repair-noting-protocol.md 原始log | 同源正式机制支持，原F02可关闭 | 未知provider全覆盖不宣称；不以源码字符串证明cache parity |
| V2-47 | same main_read_surface predicate→Context Recovery replace | 带Conversation开始和压缩区间；旧footer替换；非Main原生 | context_compressor.py；conversation_compression.py | 静态机制支持 | 有意义说明不泄露Snapshot/Session内部审计ID |
| V2-48 | 原生AIAgent/SessionDB/ContextEngine/WS接缝；个人独立插件 | 无独立Agent Loop/对话存储/通用调度器/API hierarchy | 固定三仓源码 | ad4架构边界支持 | F04修复不能以event journal等新机制绕过 |
| V2-49 | core/UI/personal三仓边界；根文档职责；ignored证据 | 个人NM未默认公开核心依赖；旧原文保留 | 固定README/CLAUDE/AGENTS；snapshot | 范围基本支持；最终公开变更需root审 | 不读取/输出凭据；不能因branch名声称私密 |
| V2-50 | 官方10类check；UI正式npm test | 9check通过/health1阻断；UI696pass3fail1skip | final-integration-checks.md＋raw结果 | ad4检查未通过；修复定向证据待v2核验 | 不放宽阈值/超时/等级；不复跑大型suite |
| V2-51 | PM官方runner；isolated home；actual native OS | 受控报告对应runner；本审查零动态执行 | 各报告命令/日志；source-map | 已复用证据方法可用 | 测试私有数据ignored；模型prefix遵17；未测平台不冒充 |
| V2-52 | 现有UI表现baseline；状态接线小diff | sidebar两行；主题tokens/layout SHA保留，用户dirty初值部分未知 | presentation-baselines.json；最终浏览器待交 | 静态保护有证据；交互无回归待核 | 不以新功能成功代签Pin/拖拽/滚动/动画；旧基线缺失如实保留 |
| V2-53 | docs/cloud-deployment-sop.md＋README索引（待最终固定版） | PI-20新增授权；只审部署SOP | criteria-v2-pi20-addendum.md | 待固定文档与实际拓扑核验 | 不执行或宣称云端/TLS/Access已验 |

## 4. 核心目标及验证方法审查

1. **连续 Conversation/派生状态/原始证据**：以真实自然100k/5秒触发、父压缩明确commit、child独立终态和Framework正文证据支撑代表链。未将child完成当作父成功；Main首次取证过早close的abort保留。History同身份分页通过正式handler执行并保持旧默认，但两个自然长上下文模型只search、自称核原文，不能当完整Read行为通过。
2. **责任、批准与实际交付**：Noting正式child受控测试验证权限、合法来源、working view、提交/失败路径，真实旧F16证明来源v13先结算、Candidate v14后关闭且未覆盖内容保留；它不自动证明新Metadata helper的实际单次创建或所有多依赖行为。Main不得写Notebook由生产拒绝与存储边界保证，不靠提示。
3. **缓存前缀与原生兼容**：真实AIAgent请求循环在原生selector前分离冻结前缀，传入suffix深拷；Noting原生output-cap先于compression返回，普通原生分支保持。查看受控Provider与throw哨兵的实际测试方法及raw PASS，不以源码字符串/镜像helper证明机制。
4. **后台状态与完整Timeline**：ad4的inflight聚合+seq/epoch+有界ring能支撑同runtime长运行，中途snapshot/replay有明确边界；已完成后的冷History必须有正式持久事实。独立反查发现F04绕过finalizer的error只进内存，可被合法reap回收，不能用同runtime测试或人工写成功消息的restart测试替代。
5. **Profile与个人接入**：固定政策SHA核对后读取实际两SOUL/仓外AGENTS，身份与本轮权限分离。实际execute_code的owner脚本/内核/spill环境已被两真实Turn证明；小输出未实际触发spill，44受控覆盖不得冒称真实大输出实测。个人helper复用native连接、一次POST携metadata、先receipt再核验，无盲重建旧partial；真实创建仍待新集中证据。
6. **检查和UI**：复用root统一一次check/UI全套，不重跑。ad4 health1、UI3失败按事实保留；定向修复只有报告/证据尚未纳入固定v2，暂不关闭。普通notice5000/error手动、Thinking即时、明确工具错误判定的源码支持不代签真实时序UI。表现保护静态SHA/diff与实际交互需分开判。
7. **模型观察与长期愿景**：保留错误归因、独立字段拼接、无事汇报反例；不据单样本断言整个长期产品不可用，也不因DeepSeek是代理而免掉当前观察。24h安排/直接答疑与委派的获准Prompt已改，需实际样本判断行为。未获准NO_REPLY/气泡隐藏不作为修复条件。正式跨Conversation协作、完整长期治理、K3长期良率仍在本次范围外。

版本复用审计：后端25/25、UI8/8、Metadata7/7关键文件精确匹配ad4；旧Noting协议5/6（变化为测试接线）、Candidate生命周期17/22（变化为本次契约/Prompt/History/规格）逐项记录，不把报告整体“通过”无条件搬来。root新dashboard进程与48HTTP/两WS只证明加载及传输，当前UI过渡artifact不用于产品浏览器通过。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| V2-F04 / P1 | V2-39/40；session_auto_continue.py `_emit_terminal_turn_error`→session_history `_fail_inflight_turn`→session_lifecycle reap→cold History | build/dispatcher真实异常只入session内存投影，合法回收后丢失失败事实；正常部分失败finalizer不覆盖这条分支 | 违反PI17/18任意打开完整Timeline；结构缺陷，非仅缺证 | 既有writer持久真实accepted源终态与已有输出；正确owner/幂等/late隔离；受控build/dispatcher真实DB冷读＋至少一条真实后台中断冷恢复 | root接受范围内P1并修复；ad4原结论保留，待v2 |
| V2-CHECK-01 | V2-50；原测试文件FILE_LINES2131>2105 | 统一冻结检查实际health阻断 | 冻结阈值不得豁免或他处抵销 | 原两节点完整断言提取helper；已见2pass及ruff/health0阻断报告，需核固定v2差异 | 定向证据已到；未据移动代码关闭 |
| V2-UI-01～03 | V2-25/38/52；controller恢复 | 统一UI实际epoch超时、断连list引用改变、离开返回历史读取2→4 | 当前集成回归，不能忽略旧行为或放宽timeout/断言 | 最小owner修复及定向分支证据、最终v2静态复审和隐藏反代现场 | root正在收敛；ad4失败保留 |
| Q03归档暂停可见性（继承而独立复核） | V2-05/06/11/45；personal_provider `_attempt_archive`→MemoryManager `_sync` | 正常rewind/edit导致ACK前缀不符后安全拒写；返回状态被丢弃，仅日志，研究报告未实施 | 不能宣称使用者/模型已知道NM不再更新；当前记忆连续性的真实限制 | 现有渠道准确、owner明确的降级事实，或用户明确接受带限制的边界；不擅自远端覆盖/新Thread | 尚未关闭；研究不是实现/批准，不自造治理方案 |
| 模型观察项 | V2-08/09/10/11/28/36 | 自然样本归因/原文核对夸大与静默反例；新S01/Q02行为证据未齐 | 影响用户意图判断，区别代码bug、模型表现和样本覆盖 | 按授权场景与版本复用/集中验证；不靠Prompt自报或删执行事实 | 保留观察，不宣告全模型/长期良率通过 |
| 集中现场证据 | V2-20～26/30/37～43/52 | 新版本加载、实际一次metadata创建、隐藏反代三时点Timeline/UI仍待最终包 | 不能把HTTP、磁盘文件或单测代替真实产品 | 固定v2/manifest/构建及加载绑定；正常与中断后台旅程；实际metadata与批准/写结果 | 已安排，等待不提前判新版本失败 |
| V2-53 SOP | PI20新增交付 | 文档Agent正在撰写，尚未固定交接 | 是最终交付物，不是自动云端部署许可 | 文档/README索引与最终拓扑/版本/备份回滚/隔离/未验边界一致 | 待v2 |

范围外：Cloudflare Access按用户明确排除；云端/TLS/Access不因SOP存在而成为已验。长期正式跨Conversation协作/全面记忆治理不自动列当前开发项。旧规格矛盾不是理由去恢复被用户否定的审计ID、双来源或额外确认。

## 6. 修复与独立复审

- 旧 F01可读coverage、F02冻结前缀selector、F03退休别名拒绝的ad4实现已沿正式路径核对，受控/适用真实证据支持修复方向；最终v2需确认相关源未受影响，再在最终结论中准确关闭。
- root已接收F04必要阻断包。独立审查明确六条件：真实accepted source/UID与owner；typed error/interrupted终态；真实已有输出/工具顺序；与正常/失败finalizer幂等；保存失败不覆盖原错误且不重跑业务；正式cold History与新UI可读。方向为既有messages.display_metadata在真实源行merge可选turn_terminal，不改变role/content/UID、不注入api_content、不造assistant，不新增表/事件日志。该方向可接受审查，但尚未核实际固定实现。
- 对root提出的验证组合，认可真实Reminder→原生Stop/interrupt→close回收→反代重开冷History可满足至少一条真实后台终态恢复；不要求在服务中注入dispatcher故障。后者通过正式writer＋真实SessionDB冷读的受控分支覆盖，另核正常已保存失败/迟到retired等边界。
- 表现保护只接受必要状态恢复改动。最终v2应包含F04、controller三回归、测试组织、README无屏幕启动参数及08宿主说明、PI20 SOP等实际增量；以最终manifest核差异，不能用移动工作区替换ad4。
- 本阶段整包交回后释放并行槽。后续接续同次独立审查：核v2完整性与ad4差异→复核受影响53项→核加载/构建/实际反代与metadata原始材料→明确每条关闭、模型表现/剩余取舍和最终Verification门禁。**本段不是最终PASS或最终NOT PASS，当前不授权把未关闭项视为通过。**

独立产物索引：`criteria-v2.md`、`criteria-v2-pi20-addendum.md`、`source-integrity.json`、`evidence-source-map-ad4.json`、`terminal-failure-recovery-finding.md`、`review-notes-ad4.md`、`matrix-ad4-draft.md`与本整包同文副本均在 `independent-reverification/`。

# 第二次全范围复审：v2 固定源码及修复证据阶段整包（2026-10-18）

## 1. 审查对象与结论概览

**v2源码/已有证据阶段完成；未发现须追加的确定实现阻断。原F04代码与受控跨层恢复修复成立，最终真实后台中断及反代现场证据尚待；Q03在本版明确未修。最终总门禁尚未作出，不因代码阶段完成而宣告整轮PASS。**

固定源集 `delivery-snapshot-v2/snapshot-set.json` SHA `05da51175ef7159799e7cacc3d5858ad0ece107414f2bae630526e2f70484396`；core manifest `179c16c258d55036655f0f9e976e4115afbc75db1bfdcdba55288e732c09aa03`；UI `cc25495a32d9a67f6be1cf3bd3c001dc00d3a064afc9a4b888c1c1edc8a17d1b`；personal `454fdaba5e7baa308342951aea89ad77164ed1af9952b52454b6f9b2a460a840`。逐文件核 core18200/UI163/personal701：普通文件全部匹配，core两条历史symlink与ad4相同，已在原阶段识别为固定树内链接。

相对ad4：core23文件（含轮次/根动态文档、F04生产/测试/生成契约、两测试组织文件、README/08/SOP），UI9文件，personal0产品差异；没有删除。新SOUL与仓外访问政策指纹同ad4。只读取固定v2及指定已有证据；没有读取移动实现、运行测试/模型/NM/服务/浏览器。

## 2. 独立要求清单与覆盖

维持原始 V2-01～52 与PI20新增V2-53，不增减/降级。全范围原判据与ad4报告均原样保留。下面53项矩阵以同字节未变源复用原审结论，受影响项改按v2核对；不是把F04小包冒充全部产品审查。Q03归档降级和模型行为项继续分别记录；Cloudflare Access排除及未来愿景边界保持。

## 3. 逐条实现证据

代码路径均指v2固定三仓；未变路径的原始证据入口沿ad4阶段。`evidence-source-map-v2.json`显示backend29/29、UI13/13与实施证据manifest精确匹配；`f04-dto-verification-v2.json`显示UI10份REST fixture与后端原始DTO完全相等。实际运行版本/构建/现场尚待集中证据，表内不可据此预填通过。

|条款编号|正式入口及完整关键代码路径|方法、输入、配置及实际证据|证据位置|判定及理由|证据边界|
|---|---|---|---|---|---|
| V2-01 | 部署 SOUL；secretary prompt；原生委派 | main/exam natural-idle：答疑、规划、纠正等实际 Turn | main/exam-natural-idle-live.md | 身份支持；行为仅部分覆盖 | 倾诉、情绪语境和新 Q02 委派/亲自尚无完整代表样本 |
| V2-02 | secretary Conversation identity→合法路径→原生压缩；Notebook pointer | 双自然 100k Idle 后仍相同 Conversation；正式 child 提交 | main/exam-natural-idle-live.md；repair-noting-protocol.md | 机制与代表链支持 | branch/rewind/restart 全边界另见45，不能由双样本概括 |
| V2-03 | 原生 session.new/list/resume；独立 UI controller | 固定源码保留多会话；两 Profile 多 Conversation 记录 | 06/07；双自然 Idle 报告 | 静态支持 | 最终多入口浏览器旅程待集中证据 |
| V2-04 | tools/session_history_tool.py→same-profile main scope→合法 History | 正式长读 handler 与 paging 受控测试；自然模型 search | history-long-read.md；authorized-prompt-sync.md | 机制支持 | 同 Profile 跨 Conversation 实际模型精读覆盖有限；跨 Profile 不获准 |
| V2-05 | compaction→Notebook→History；personal_provider prefetch/archive | 自然压缩完成；真实 NM 首次全文精读但自动 Recall 0 pointer | 双 natural-idle；recall-first-read-live.md | 部分成立；可靠召回未闭合 | 手工 search→show 不能代签自动 pointer 首读；归档暂停见Q03 |
| V2-06 | Notebook Context/Commitment；Reminder→provider ACK | 自然 Noting 保存责任；cold Reminder 真正唤醒 | candidate-lifecycle-evidence.md；repaired-reminder-live.md | 机制有支持，行为需分项 | 责任纠正/暂停/多依赖不能由有待办替代；归档暂停不可见 |
| V2-07 | secretary/scheduler_host.py→resume→deferred request→ACK | desktop 冷执行真实成功，旧 web source 失败保留 | repaired-reminder-live.md | v2正式sink补终态；原代表链有效 | 新真实Reminder正常/中断冷恢复仍待现场，不把受控当实服务 |
| V2-08 | 授权 S01 prompt 注入与 reminder tool | 原文24h约定已恢复；19机制测试核真实构建 | authorized-prompt-sync.md | Prompt 机制支持，行为待补 | 不能以 code 强制配额代替模型实际建未来24h Instant |
| V2-09 | S01/no useful update；模型最终文本 | 旧 cold Reminder 输出26字符无事汇报 | repaired-reminder-live.md | 已观察静默反例；新 Prompt 未关闭 | NO_REPLY/隐藏气泡未获准，不将其指定为修法 |
| V2-10 | Notebook contracts/source IDs；实际模型归因 | main 把用户假设归因助手；exam 合并独立字段 | 双 natural-idle 报告及 raw | 数据可追；模型表现有反例 | 不把同一代理模型样本推断成结构 bug 或未来K3通过 |
| V2-11 | conversation_history content_offset + digest + next | 30006 Unicode 分页；真实 NM show 全文546字 | history-long-read.md；recall-first-read-live.md | 长读机制支持，原文精读行为未全面成立 | 自然样本只 search 自称核原文，不能当read |
| V2-12 | 全范围52判据与实际样本/反例 | 请求、工具、持久结果而非模型自报；负面观察保留 | criteria-v2.md；本矩阵 | 方法遵循；场景覆盖仍待最终核验 | 长期生活效果/数月可靠性不能本轮证明 |
| V2-13 | 公开核心/个人插件分离；原生 delegate | 未发现新增跨 Conversation 责任委托机制 | 固定 core/UI/personal 源 | 范围边界支持 | 未来治理未实现不自动列缺陷；当前来源完整性仍审 |
| V2-14 | 实际部署 SOUL 指纹与内容；参考身份隔离 | 四份policy先核SHA后全文阅读，精确匹配；无Pi工具/飞书权限 | snapshot-set identity fingerprints | 静态身份政策符合；运行加载与行为另核 | 输入旧SOUL仅参考，不能当最终已加载 |
| V2-15 | Profile policy SOUL；仓外 AGENTS；每条测试前缀 | 部署指纹明确，测试时间尺度单列普通user | snapshot-set；load-profile-isolation-repair.md | 静态文本符合；实际加载待最终集中绑定 | 不得将测试限定永久写SOUL |
| V2-16 | personal provider owner scope；原生 Profile env | 双Profile realNM/Noting；main Default只读；exam授权space | 双 natural-idle；load-profile-isolation-repair.md | 代表链支持 | 最终新helper真实发现/获准创建待集中旅程 |
| V2-17 | 原生 DeepSeek custom provider；普通user完整前缀 | 双自然Idle与修复load真实wire、时间戳 | 双 natural-idle；load-profile-isolation-repair.md | 已有样本方法支持 | 不代表K3良率；不额外运行模型 |
| V2-18 | 原生 Idle Compact + Noting config/trigger | main101029/104312；exam102871；5秒真实触发 | 双 natural-idle 报告/原始持久证据 | 代表链通过 | 主首次取证 premature close 失败保留；新加载不等于重新自然触发 |
| V2-19 | notebook_render→show/control/framework completion | 同owner真实anchor转可读coverage；原子正文投影 | repair-coverage；双 natural-idle 真实请求 | 原F01修复机制关闭；适用真实模型面支持 | v2相关生产源未变；未见的四面wire不外推 |
| V2-20 | UI profiles.ts/controller→native session.new owner | Profile选择与新旧session owner解析 | 固定 UI 源；最终浏览器待交 | 静态支持，UI现场待核 | 标签变化不是模型/SOUL实际切换证明 |
| V2-21 | loadSessions all profiles；profile icon映射/sidebar | owner+storedid key；最新sidebar两行必要变更 | presentation-baselines.json；固定UI | 静态支持；断连引用回归定向关闭 | 最终跨Profile图标/列表浏览器现场待核 |
| V2-22 | projection reasoning.delta→即时thinking | 流式事件即时归并，无completion gate | 固定 projection.ts；UI机制测试 | 机制支持；真实流式现场待核 | 模型不发reasoning不捏造；后台来源同样适用 |
| V2-23 | tool.start/result→toolResultState；message.complete | 仅明确false/error/nonzero判错；未完成unknown | projection.ts；UI相关证据 | 机制支持；连续界面状态待核 | 最终截图不能排除短暂假错 |
| V2-24 | native-notices normal5000/error手动 | 通知rail真实生产常量及owner归属 | native-notices.ts；UI测试 | 静态支持；现场时效待核 | 不以constant单独签UI |
| V2-25 | 原生usage/context冷估；controller merge | 完整冷读model_config精确断言；session/model/代次标识 | cold-estimate-assertion-sync；final-integration-checks | 冷估机制及health组织修复关闭；epoch原失败定向关闭 | 旧fixture错误按真实RPC分流修正，未改5000ms或原值断言；现场待核 |
| V2-26 | 个人Skill批准政策→personal_cli create | 具体内容/目标须由真实普通user批准 | metadata-create-api.md；新创建证据待交 | 政策/接口支持；真实写入闭环待核 | 空间一般写权限不等于逐条批准；不读Default私人正文 |
| V2-27 | notebook_contract三目标exclusive sources；noting_tools | 52受控契约；正式child lifecycle10复用 | candidate-source-contract-sync.md；source-map-ad4 | 结构支持 | 正文是否实际特化属28，不由schema保证 |
| V2-28 | Candidate refs型按Memory/Rule/Skill brief | schema/prompt授权；真实自然候选有限 | candidate-source-contract-sync.md；双自然Idle | 机制支持；模型语义证据有限 | 不得复制来源正文冒充特化简述 |
| V2-29 | Noting source mutation→Candidate final state；引用校验 | 正式child 10场景含partial/pending/restart等 | candidate-lifecycle-evidence.md；source-map-ad4 | 受控机制支持 | 旧F16真实source v13→candidate v14结算且未覆盖保留可复用为代表；新helper/多依赖须版本关联 |
| V2-30 | personal_cli→native connection→single API create metadata | 7文件manifest全同；安装9文件新版本 | metadata-create-api.md §8 | 静态/受控支持；一次真实create待证 | 旧partial禁止重建，API失败不假报完整 |
| V2-31 | 非create走personal_client官方CLI；Skill路由 | alias解析/CLI show/旧attach显式 | personal_cli.py；personal_client.py | 静态支持 | create后metadata GET只校验；不引入平行执行框架 |
| V2-32 | eligibility/global/local checks；native context hook suffix分流 | 关闭原生selector仍工作；Noting output cap单独分支 | repair-noting-protocol；固定源 | 既有原生分支支持；F04成功零写及API不污染受控支持 | metadata写失败nonfatal；全平台/所有Provider不外推 |
| V2-33 | DTO optional owner/epoch/inflight；history optional offset | 25后端文件与有效兼容包同SHA；旧默认保留 | websocket-backend-state.md；source-map-ad4 | v2可选DTO增量兼容有静态/受控证据 | 旧role/text/default保持；REST不改，新Message UID不进模型请求 |
| V2-34 | session profile runtime scope；code_kernel scratch helper | 真实2execute_code内核/脚本/spill环境各归owner | load-profile-isolation-repair.md；44受控 | 受影响隔离机制与代表现场支持 | 实际大输出落盘未发生；不硬扩成全部平台已验 |
| V2-35 | 三处获准Prompt常量/文档同步；真实rootwire | S01/Q02/History分页精确授权差异 | authorized-prompt-sync.md；snapshot-index | 授权边界支持；v2未改Prompt常量/模型构建 | Q03下一增量仍须独立核公开通用桥与个人边界 |
| V2-36 | 授权Q02：直接回应/适当委派/亲自优先 | 新prompt实际构建；旧代理样本不全面 | authorized-prompt-sync.md | 机制已改；行为证据待补 | 原生Agent委派不等于未来跨Conversation协作 |
| V2-37 | 原生stamp→inflight fold/replay→sessions.changed | 同seq锁、native callback全来源；130受控有效 | websocket-backend-state.md；source-map-ad4 | 同源旧WS证据及F04受影响回归支持 | 真实最终后台时点现场待交 |
| V2-38 | UI session-recovery snapshot+continuation+strict seq | 8文件同SHA；gap有界retry；epoch/generation归属 | websocket-state-recovery.md；source-map-ad4 | 旧三UI失败定向关闭；snapshot/replay机制保留 | 最终三时点反代现场未到；不以fakeRPC代签真实WS |
| V2-39 | turn_terminal.persist→SessionDB原生事务/guards→真实源display_metadata→原生RPC/REST→terminalHistory | 真实DB重开10份DTO；生产Controller/Timeline消费；后台真实旅程待交 | F04后端/UI报告、source-map-v2、DTO核对 | F04源码及受控冷DB→正式History→生产UI修复成立 | 最终真实后台中断冷恢复待核；identity完全失败时显式incomplete不宣称完整 |
| V2-40 | 无事件/Timeline过滤；真实后台终态持久 | 静默执行也走原生event，terminal error却可回收丢失 | F04；固定backend/UI | v2终态事实持久/可见接线有证据，无新增隐藏策略 | 真实静默模型行为另见09；实际现场待到 |
| V2-41 | dashboard --no-open→dual SPA prefix middleware→same ws/api | 48 HTTP两WS已成功；serve headless失败保留 | local-deployment-browser-validation.md 加载里程碑 | v2启动/双SPA接线与SOP一致；最终浏览器待核 | 旧48HTTP/2WS仍仅过渡加载证据，不代签最终构建 |
| V2-42 | 审查无UI工具；取证只hidden IAB | 本Agent零UI/服务/模型；root后续隐藏浏览器限制 | 本审查工具历史；现场记录待交 | 审查执行符合 | 不使用open/其它浏览器/桌面或显示变化 |
| V2-43 | 固定三个tree manifest；source-map；加载指纹 | ad4全产品hash匹配；2历史symlink另释；新backend已载过渡artifact | source-integrity.json；source-map；加载里程碑 | v2三仓完整核验匹配；29backend/13UI证据源全匹配 | 加载/现场产物未到；personal零产品差异，Q03不可据声明关闭 |
| V2-44 | Main只读；noting_scope四工具；retired alias统一拒绝 | 正式child write session；storage source/anchor validation | repair-noting-protocol；candidate生命周期 | 原F03退休别名/权限修复机制关闭 | v2相关正式拒绝源未变；不以Prompt自律代替 |
| V2-45 | pointer transaction；framework same transaction；Reminder deferred/ACK | 正式child fail/interrupt/forced/restart；late snapshot丢整条 | candidate-lifecycle；repair-noting；旧门禁证据 | 适用机制有分支证据；完整边界待汇总 | Reminder late/cancel/restart与NM rewind归档降级需单列，不能笼统全通过 |
| V2-46 | frozen parent/root/tools；selector只suffix；child四工具 | 真实AIAgent4calls/2Turns；nativeoutputcap7pass | repair-noting-protocol.md 原始log | 原F02冻结prefix修复机制关闭；原受控证据复用 | v2相关源未变；F04真实SDK序列化另证无metadata污染 |
| V2-47 | same main_read_surface predicate→Context Recovery replace | 带Conversation开始和压缩区间；旧footer替换；非Main原生 | context_compressor.py；conversation_compression.py | 静态机制支持 | 有意义说明不泄露Snapshot/Session内部审计ID |
| V2-48 | 原生AIAgent/SessionDB/ContextEngine/WS接缝；个人独立插件 | 无独立Agent Loop/对话存储/通用调度器/API hierarchy | 固定三仓源码 | v2沿原writer/metadata/History/UI投影补线，架构边界支持 | 无新增表/迁移/模型输入通路/事件库；不保证异常observer丢失时全量恢复 |
| V2-49 | core/UI/personal三仓边界；根文档职责；ignored证据 | 个人NM未默认公开核心依赖；旧原文保留 | 固定README/CLAUDE/AGENTS；snapshot | 范围基本支持；最终公开变更需root审 | 不读取/输出凭据；不能因branch名声称私密 |
| V2-50 | 官方10类check；UI正式npm test | F04后端21+受影响8+契约1；UI21/52skip；原三项+新两项5pass；health2节点+check通过 | final-integration-checks；F04/v3原始日志 | 原health阻断与3UI失败定向关闭；F04相关检查通过 | 保留原ad4失败；未复跑全量；后续Q03增量另核 |
| V2-51 | PM官方runner；isolated home；actual native OS | 受控报告对应runner；本审查零动态执行 | 各报告命令/日志；source-map | 已复用证据方法可用 | 测试私有数据ignored；模型prefix遵17；未测平台不冒充 |
| V2-52 | 现有UI表现baseline；状态接线小diff | sidebar两行；主题tokens/layout SHA保留，用户dirty初值部分未知 | presentation-baselines.json；最终浏览器待交 | v2八表现文件SHA不变；新增终态沿既有组件 | 真实Pin/拖拽/滚动/动画保护仍待适用现场；初始dirty无SHA限制保持 |
| V2-53 | docs/cloud-deployment-sop.md＋README稳定索引 | 核dashboard/PM/npm入口、Profile目录、双SPA前缀、单后端/回环反代、备份回滚/未验边界 | v2固定SOP全文及正式入口源码 | SOP文档与README索引交付成立，静态可执行性支持 | Linux/systemd/Tunnel/Access/TLS未执行；最终release/产物仍需按交付版本填表 |
## 4. 核心目标及验证方法审查

### F04正式接线与六条件

- **真实源与owner**：`session_workdir`只取正式submit已保存row/UID/物理session/DB路径；后台路径在`agent/turn_context._persist_turn_start`已完成原生persist与`require_active_delivery_persisted`后调用observer。`turn_terminal`核同registry/session/agent、opaque token、关闭状态、真实Profile DB路径；`_observe_source`再查row的物理session与UID。不会用当前压缩tip冒充祖先owner。
- **事务与幂等**：`hermes_state_turn_terminal.persist_terminal_metadata`在原`_execute_write`事务内使用原transcript guards/turn lease、lineage与display active语义；校验row+session+role=user+UID、首终态CAS、合并原metadata、同步可见克隆。错误owner、已retired、未accepted、rewind均不得造历史。compute-host沿原dispatch lifetime token拒迟到后才进入现有done接缝。
- **保持真实终态**：returned failed/interrupted、build异常、dispatcher异常、compute-host turn.error均走既有sink；正常complete在DB前返回。真实源role/content/api_content/UID不变，不造assistant/user。已存在finalizer失败只引用真实final UID，重入不增正文；保存失败不替换原error/不触发重执行。
- **已有输出**：原生write_frame同seq捕获已有OutputIdentity到既有inflight内部；对外snapshot移除内部字段。语义残余只有真实reasoning/message/tool，不是逐事件库。正文/reasoning仅凭同UID、晚于片段的原生output_committed和持久facet剔重，tool只凭tool_call_uid；无identity时不凭正文或provider tool id猜配。
- **冷读与呈现**：原RPC只增可选message_uid/tool_call_uid，既有REST raw透传metadata。UI只认真实user源且source UID一致的typed终态，source角色/编辑身份不变；真实final assistant标终态，残余投影按身份替换live前半段，既有Notice显示操作事实，未完成工具不冒称成功。正式source被rewind后自然消失。
- **模型输入边界**：源码无api_content/root Prompt新通路；真实`build_api_messages→_build_api_kwargs→SDK HTTP序列化`的受控测试证明新终态键不进入模型请求。不是只搜源码字符串。

受控backend21节点覆盖正式idle submit dispatcher异常、真实native finalizer、build无输出、partial/tool、typed附加帧失败、owner/lease/token/rewind/祖先、writefail保留原错并可后续重试；8受影响旧节点保留WS折叠与原native路径。10份真正DB关闭重开、新runtime、正式RPC/REST DTO经UI生产Controller/Timeline21节点消费（含5旧受影响节点），不能称为实际模型/真实浏览器。原始日志已读，manifest匹配，无审查者复跑。

明确局限：identity观察彻底失败且已有持久输出时，无法安全去重的片段省略并标`outputs_complete:false`，UI明示恢复不完整，保留可识别live；这不应被包装为“所有失败情形完整”。同UID旧facet后残余delta的UI处理在代码上保留，当前正式DTO是另一个真实UID的partial，不把它代签该特例。真实后台Reminder→原生Stop→回收→反代冷读仍待root集中证据，最终F04不在本阶段全关闭。

### 原集成失败与UIUX

health修复完整保留两条冷估断言，仅提取小helper，原超限文件回到HEAD2105，没有删契约/阈值豁免。epoch timeout源于旧测试把所有RPC共用悬挂Usage resolver；新fixture按真实method分流，5000ms/拒绝旧999/Usage与Context原断言保留。历史2→4源于旧fixture对events.since返回无epoch `{}`导致必要fallback；新合法同epoch响应恢复原2读，并新增真truncated需第二次读取的反向测试。断连引用变化为实际生产回归，现只使已观察运行状态失效，未知/纯元数据行与无变化数组保持引用。定向5pass与类型检查有效。

v2没有App/CSS/layout/图标/Pin/拖拽/滚动文件变更；F04八文件表现比较与固定tree一致。它证明静态保护，不能替代真实交互/动画无回归的现场检查。

### PI20 SOP

完整核读固定SOP与README索引，核官方PM `--source/--out/重复--group`、npm正式build、dashboard `--no-open --isolated --skip-build`、双SPA前缀与回环单后端路径；文档明确serve握手不等于部署网页。Profile state与仓外cwd、可选个人插件及逐项批准、Files default归属、systemd专属服务、Caddy/Tunnel/Access不绕API、产物清单、SQLite backup、整套一致停机点与兼容回滚均有步骤。没有把本机测试尺度/Space权限写成生产默认；没有上云执行或宣称Linux/TLS/Access已验。最终commit/产物填表位置刻意留待正式交付，不用dirty HEAD替代。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| 原F01/F02/F03 | 19/44/46；可读coverage/selector冻结前缀/退休alias | ad4已核修复，v2生产路径未变 | 原确定代码问题已有正式修复与适用证据 | 沿既有有效证据，不重跑 | 代码机制关闭；历史报告保留 |
| V2-F04 | 39/40；终态持久/History/UI | v2正式sink和cold DB→RPC/REST→UI受控证据成立 | 代码缺口已补；真实后台现场未到，不能全签关闭 | 最终加载绑定＋真实Reminder中断冷恢复，核owner/顺序/无重执 | 代码及受控跨层修复成立；最终现场待核 |
| V2-CHECK-01 | 50；原2131>2105 | 同v2测试组织源、2节点与ruff/health通过 | 原health缺陷已解除，未放宽规则 | 无需复跑整套 | 定向关闭 |
| V2-UI-01～03 | 25/38/52 | 两fixture真实协议修复＋一处断连引用生产修复；原3+新2通过 | 原实测失败已分因处理 | 适用真实UI/重连现场另核 | 定向关闭，ad4失败保留 |
| Q03 | 05/06/11/45；个人归档反馈 | v2 personal文件与ad4完全相同；仍仅日志/被丢弃返回 | 真实降级不可见未关闭；root将另交窄增量 | 独立核通用可选反馈/个人判断隔离/owner/迟到/无Prompt变更及可见结果 | v2明确未修，不据声明关闭 |
| 真实集中证据/模型观察 | 08/09/10/11/20～26/28～30/36～43/52 | 尚未交最终加载、metadata一次创建、后台各时点与浏览器完整包；旧模型反例保留 | 机制或文档不可代签真实行为 | 等已安排材料，按版本/原始事实逐条收束 | 最终门禁等待；不提前判v2总体失败 |
| V2-53 | docs/cloud-deployment-sop.md；README | 文档/索引已交，静态步骤与正式入口一致 | 本次文档交付满足；不构成云端已验 | 最终交付填入配套版本/产物，云端执行另行授权 | 文档项代码阶段通过 |

没有新增确定P1/P2。上述identity完全失败显式不完整属于现有best-effort观察/显示边界；不扩权为新事件库或业务重跑。CloudflareAccess及真正未来愿景仍按原判据范围处理。

## 6. 修复与独立复审

v2影响核对已经覆盖全部53项：未变源按精确字节复用ad4审查，F04/3UI/health/README08/SOP增量逐条复审。root已告知Q03通用可选Provider→MemoryManager→既有Notice桥接正在独立实现；本Agent未读取其移动代码、不推定其效果。后续只在其不可变窄增量与实际加载/现场包到达后继续同次门禁，不重提53条、不降低行为和真实部署判据、不复跑有效大套。

本阶段整包副本 `independent-reverification/v2-code-evidence-stage.md`；完整校验/证据源映射/DTO对应详见同目录 `source-integrity-v2.json`、`evidence-source-map-v2.json`、`f04-dto-verification-v2.json`。一次只读汇总脚本曾因display_metadata=null取值报错，后用原契约允许的null处理修正；它不执行产品/测试，不是产品失败，也不修改原证据。旧报告及失败结论全部追加保留。


# 第二次全范围复审：不可变 v3 源码与既有证据阶段

## 1. 对象概览

本阶段完成既有53项独立判据的v3影响核对。**Q03“归档安全暂停只记日志、没有可见反馈”的代码缺口已补，受控正式链证据支持最小可见降级机制；尚未据此关闭实际运行可见性。未发现v3新增确定代码阻断，不作最终PASS。** v2 F04源码/受控冷History修复、原health/3UI定向关闭与所有原模型反例保持；最终加载、后台时点、反代UI、Metadata真实一次创建仍待集中证据。

唯一源码对象为 `delivery-snapshot-v3/snapshot-set.json`，SHA256 `7de214d8210ce2752ad2b1b1c36f736b9f5ce6d558cd78310de6d1a76dbcae30`。核心manifest `5a44ceba0cada8f0747f507a70d7ec3321ea450bd1fd4b2138fc06bce73449c9`；UI `84d85ccf1d4a5ca2af9677697295e3393e081d161df3d7d3a9213c1ae25b01a9`；个人 `347032a259b66530217e042771780cd9db0c39bec056f610a41c72d20fec3636`。完整校验core18202、UI163、personal701普通文件，无不匹配；两历史内部symlink仍按前阶段说明处理。

v3相对v2：核心8项变化，其中3项为根动态记录，5项为本包代码/测试；个人2项；UI零字节变化、零删除。新增检查只针对这些差异与正式影响链，未用移动工作区补结论，未运行测试/模型/NM/服务/UI，未派生。7个增量源码与10个关键依赖逐项匹配开发证据，原测试日志及补丁hash匹配，详见 `independent-reverification/evidence-source-map-v3.json`。证据报告在审查期间追加安装§8并更新manifest，保留该事实；此变动不改变固定v3产品源，安装与源码验证分层。

## 2. 独立要求及适用边界

继续使用先于实现建立的V2-01～V2-53，不重提或缩减判据。产品原文、PI01～20及独立criteria原件仍为权威；技术规格、root接收和实现者自评不是答案。Q03的最小要求是准确暴露归档暂停范围，同时保留本地合法原文、原来的安全拒写与个人权限；不得把检索正常当归档恢复，或把旧远端副本当已撤回。

本次选择现有5秒Notice、无ACK的attempt和下一合法完成边界重放，是AC-03已登记的Agent自主收敛形式，未冒称用户确认。原要求没有指定永久面板、edit当下必达或新通知ACK；因此不把这些额外能力作为新代码门禁，也不把现有形式包装成可靠送达保证。应保留实际可见性验收，不能只检查函数存在。

## 3. 逐条实现与证据矩阵

以下保留53个原编号。未受v3影响的行沿用上节v2完整审查及其证据边界；其中“v2”表示所复用证据版本，不表示使用移动旧源码。已逐文件确认对应生产路径未变。受影响行更新为v3事实，不将原未验/反例改成通过。相对证据路径均在本轮 `.hermes-dev/product-intent-review-20261018/` 下；实现位置均指固定v3副本。

|条款编号|正式入口与关键路径|方法、输入及实际证据|证据位置|判定与理由|证据边界|
|---|---|---|---|---|---|
| V2-01 | 部署 SOUL；secretary prompt；原生委派 | main/exam natural-idle：答疑、规划、纠正等实际 Turn | main/exam-natural-idle-live.md | 身份支持；行为仅部分覆盖 | 倾诉、情绪语境和新 Q02 委派/亲自尚无完整代表样本 |
| V2-02 | secretary Conversation identity→合法路径→原生压缩；Notebook pointer | 双自然 100k Idle 后仍相同 Conversation；正式 child 提交 | main/exam-natural-idle-live.md；repair-noting-protocol.md | 机制与代表链支持 | branch/rewind/restart 全边界另见45，不能由双样本概括 |
| V2-03 | 原生 session.new/list/resume；独立 UI controller | 固定源码保留多会话；两 Profile 多 Conversation 记录 | 06/07；双自然 Idle 报告 | 静态支持 | 最终多入口浏览器旅程待集中证据 |
| V2-04 | tools/session_history_tool.py→same-profile main scope→合法 History | 正式长读 handler 与 paging 受控测试；自然模型 search | history-long-read.md；authorized-prompt-sync.md | 机制支持 | 同 Profile 跨 Conversation 实际模型精读覆盖有限；跨 Profile 不获准 |
| V2-05 | compaction→Notebook→History；personal prefetch/archive→可选反馈 | Q03正式sync及冷receipt只读重判；原自然Idle/Recall证据复用 | archive-pause-feedback；source-map-v3；原natural-idle | 归档暂停反馈机制已补；可靠自动Recall仍未闭合 | 新fact不证明模型精读；实际L09/L10待核 |
| V2-06 | Notebook责任/Reminder；个人archive→MemoryManager→Notice | Q03真实隔离DB编辑/rewind安全拒写、原receipt保持、既有Notice事件 | archive-pause-feedback；原candidate/reminder证据 | 责任原机制复用；只记日志缺口在代码层修复 | 5秒attempt不是用户ACK；不保证编辑当下必达 |
| V2-07 | secretary/scheduler_host.py→resume→deferred request→ACK | desktop 冷执行真实成功，旧 web source 失败保留 | repaired-reminder-live.md | v2正式sink补终态；原代表链有效 | 新真实Reminder正常/中断冷恢复仍待现场，不把受控当实服务 |
| V2-08 | 授权 S01 prompt 注入与 reminder tool | 原文24h约定已恢复；19机制测试核真实构建 | authorized-prompt-sync.md | Prompt 机制支持，行为待补 | 不能以 code 强制配额代替模型实际建未来24h Instant |
| V2-09 | S01/no useful update；模型最终文本 | 旧 cold Reminder 输出26字符无事汇报 | repaired-reminder-live.md | 已观察静默反例；新 Prompt 未关闭 | NO_REPLY/隐藏气泡未获准，不将其指定为修法 |
| V2-10 | Notebook contracts/source IDs；实际模型归因 | main 把用户假设归因助手；exam 合并独立字段 | 双 natural-idle 报告及 raw | 数据可追；模型表现有反例 | 不把同一代理模型样本推断成结构 bug 或未来K3通过 |
| V2-11 | conversation_history分页；personal canonical History与receipt | 既有30006 Unicode长读；Q03冷只读检测同原清洗/指纹 | history-long-read；archive-pause-feedback | 原文读取机制保持；暂停事实范围准确 | 冷未知不报正常；模型精读/误归因观察不由本修复关闭 |
| V2-12 | 全范围52判据与实际样本/反例 | 请求、工具、持久结果而非模型自报；负面观察保留 | criteria-v2.md；本矩阵 | 方法遵循；场景覆盖仍待最终核验 | 长期生活效果/数月可靠性不能本轮证明 |
| V2-13 | 公开核心/个人插件分离；原生 delegate | 未发现新增跨 Conversation 责任委托机制 | 固定 core/UI/personal 源 | 范围边界支持 | 未来治理未实现不自动列缺陷；当前来源完整性仍审 |
| V2-14 | 实际部署 SOUL 指纹与内容；参考身份隔离 | 四份policy先核SHA后全文阅读，精确匹配；无Pi工具/飞书权限 | snapshot-set identity fingerprints | 静态身份政策符合；运行加载与行为另核 | 输入旧SOUL仅参考，不能当最终已加载 |
| V2-15 | Profile policy SOUL；仓外 AGENTS；每条测试前缀 | 部署指纹明确，测试时间尺度单列普通user | snapshot-set；load-profile-isolation-repair.md | 静态文本符合；实际加载待最终集中绑定 | 不得将测试限定永久写SOUL |
| V2-16 | personal provider owner scope；原生 Profile env | 双Profile realNM/Noting；main Default只读；exam授权space | 双 natural-idle；load-profile-isolation-repair.md | 代表链支持 | 最终新helper真实发现/获准创建待集中旅程 |
| V2-17 | 原生 DeepSeek custom provider；普通user完整前缀 | 双自然Idle与修复load真实wire、时间戳 | 双 natural-idle；load-profile-isolation-repair.md | 已有样本方法支持 | 不代表K3良率；不额外运行模型 |
| V2-18 | 原生 Idle Compact + Noting config/trigger | main101029/104312；exam102871；5秒真实触发 | 双 natural-idle 报告/原始持久证据 | 代表链通过 | 主首次取证 premature close 失败保留；新加载不等于重新自然触发 |
| V2-19 | notebook_render→show/control/framework completion | 同owner真实anchor转可读coverage；原子正文投影 | repair-coverage；双 natural-idle 真实请求 | 原F01修复机制关闭；适用真实模型面支持 | v2相关生产源未变；未见的四面wire不外推 |
| V2-20 | UI profiles.ts/controller→native session.new owner | Profile选择与新旧session owner解析 | 固定 UI 源；最终浏览器待交 | 静态支持，UI现场待核 | 标签变化不是模型/SOUL实际切换证明 |
| V2-21 | loadSessions all profiles；profile icon映射/sidebar | owner+storedid key；最新sidebar两行必要变更 | presentation-baselines.json；固定UI | 静态支持；断连引用回归定向关闭 | 最终跨Profile图标/列表浏览器现场待核 |
| V2-22 | projection reasoning.delta→即时thinking | 流式事件即时归并，无completion gate | 固定 projection.ts；UI机制测试 | 机制支持；真实流式现场待核 | 模型不发reasoning不捏造；后台来源同样适用 |
| V2-23 | tool.start/result→toolResultState；message.complete | 仅明确false/error/nonzero判错；未完成unknown | projection.ts；UI相关证据 | 机制支持；连续界面状态待核 | 最终截图不能排除短暂假错 |
| V2-24 | AgentNotice→notification.show→native-notices | 新warn/info沿既有5000ms；error仍sticky/手动；owner映射不改 | memory_sync_feedback.py；agent_callbacks.py；UI native-notices.ts | 原通知契约复用；受控原生事件接线支持 | 没有新增持久状态面板或投递ACK；最终浏览器待核 |
| V2-25 | 原生usage/context冷估；controller merge | 完整冷读model_config精确断言；session/model/代次标识 | cold-estimate-assertion-sync；final-integration-checks | 冷估机制及health组织修复关闭；epoch原失败定向关闭 | 旧fixture错误按真实RPC分流修正，未改5000ms或原值断言；现场待核 |
| V2-26 | 个人Skill批准政策→personal_cli create | 具体内容/目标须由真实普通user批准 | metadata-create-api.md；新创建证据待交 | 政策/接口支持；真实写入闭环待核 | 空间一般写权限不等于逐条批准；不读Default私人正文 |
| V2-27 | notebook_contract三目标exclusive sources；noting_tools | 52受控契约；正式child lifecycle10复用 | candidate-source-contract-sync.md；source-map-ad4 | 结构支持 | 正文是否实际特化属28，不由schema保证 |
| V2-28 | Candidate refs型按Memory/Rule/Skill brief | schema/prompt授权；真实自然候选有限 | candidate-source-contract-sync.md；双自然Idle | 机制支持；模型语义证据有限 | 不得复制来源正文冒充特化简述 |
| V2-29 | Noting source mutation→Candidate final state；引用校验 | 正式child 10场景含partial/pending/restart等 | candidate-lifecycle-evidence.md；source-map-ad4 | 受控机制支持 | 旧F16真实source v13→candidate v14结算且未覆盖保留可复用为代表；新helper/多依赖须版本关联 |
| V2-30 | personal_cli→native connection→single API create metadata | 7文件manifest全同；安装9文件新版本 | metadata-create-api.md §8 | 静态/受控支持；一次真实create待证 | 旧partial禁止重建，API失败不假报完整 |
| V2-31 | 非create走personal_client官方CLI；Skill路由 | alias解析/CLI show/旧attach显式 | personal_cli.py；personal_client.py | 静态支持 | create后metadata GET只校验；不引入平行执行框架 |
| V2-32 | 原sync completed gate；可选MemorySyncFeedback | 旧None/未知结果零状态；原失败/中断不sync；原生Main真实token | archive-pause-feedback；core.patch；final-focused.log | 关闭/原生默认路径支持；无新强制执行条件 | 可选Provider主动返回类型才有反馈；不外推所有Provider平台 |
| V2-33 | MemoryManager.sync_all可选feedback_callback；原Provider sync | 原调用签名默认兼容；可选类型/结果；原FIFO、redact、异常接缝 | memory_provider.py:64；memory_manager.py:595–664 | 增量接口兼容有源码和受控证据 | 不增加客户端API/表；既有F04可选DTO判断不变 |
| V2-34 | ctx_bound→canonical profile owner；捕获native token/callback | 通用key含provider.name/home/scope；真实ContextVar同ID两Profile反证2F→5P | profile-key-red/green.log；memory_manager.py:629–664 | 跨Profileattempted/pending抑制回归已定向关闭 | 新callback不能接旧token；pending只在同physical session完成边界重放 |
| V2-35 | 授权Prompt三处；Q03纯事实prefetch与原notice | 两次正式AIAgent请求受控响应；root逐字相同，原history无新fact | archive-pause-feedback wire/final-repair；固定diff | 未新增Prompt指令/权限；事实仅当前可见数据 | 不以受控请求证明真实模型会告知；AC-03具体形式仍待追认 |
| V2-36 | 授权Q02：直接回应/适当委派/亲自优先 | 新prompt实际构建；旧代理样本不全面 | authorized-prompt-sync.md | 机制已改；行为证据待补 | 原生Agent委派不等于未来跨Conversation协作 |
| V2-37 | 原生stamp→inflight fold/replay→sessions.changed | 同seq锁、native callback全来源；130受控有效 | websocket-backend-state.md；source-map-ad4 | 同源旧WS证据及F04受影响回归支持 | 真实最终后台时点现场待交 |
| V2-38 | UI session-recovery snapshot+continuation+strict seq | 8文件同SHA；gap有界retry；epoch/generation归属 | websocket-state-recovery.md；source-map-ad4 | 旧三UI失败定向关闭；snapshot/replay机制保留 | 最终三时点反代现场未到；不以fakeRPC代签真实WS |
| V2-39 | turn_terminal.persist→SessionDB原生事务/guards→真实源display_metadata→原生RPC/REST→terminalHistory | 真实DB重开10份DTO；生产Controller/Timeline消费；后台真实旅程待交 | F04后端/UI报告、source-map-v2、DTO核对 | F04源码及受控冷DB→正式History→生产UI修复成立 | 最终真实后台中断冷恢复待核；identity完全失败时显式incomplete不宣称完整 |
| V2-40 | 无事件/Timeline过滤；真实后台终态持久 | 静默执行也走原生event，terminal error却可回收丢失 | F04；固定backend/UI | v2终态事实持久/可见接线有证据，无新增隐藏策略 | 真实静默模型行为另见09；实际现场待到 |
| V2-41 | dashboard --no-open→dual SPA prefix middleware→same ws/api | 48 HTTP两WS已成功；serve headless失败保留 | local-deployment-browser-validation.md 加载里程碑 | v2启动/双SPA接线与SOP一致；最终浏览器待核 | 旧48HTTP/2WS仍仅过渡加载证据，不代签最终构建 |
| V2-42 | 审查无UI工具；取证只hidden IAB | 本Agent零UI/服务/模型；root后续隐藏浏览器限制 | 本审查工具历史；现场记录待交 | 审查执行符合 | 不使用open/其它浏览器/桌面或显示变化 |
| V2-43 | 固定v3三仓manifest；Q03日志/依赖映射 | core18202/UI163/personal701逐文件；7源码/10依赖/原日志一致 | source-integrity-v3.json；evidence-source-map-v3.json | 固定源及受控证据关联成立；产品UI与v2逐字相同 | 现场新PID/安装是另层证据，尚未在本源码包独立签认 |
| V2-44 | Main只读；noting_scope四工具；retired alias统一拒绝 | 正式child write session；storage source/anchor validation | repair-noting-protocol；candidate生命周期 | 原F03退休别名/权限修复机制关闭 | v2相关正式拒绝源未变；不以Prompt自律代替 |
| V2-45 | 原Noting/Reminder生命周期；NM legalHistory→receipt→观察 | Q03编辑/官方rewind、late callback、同Ref DB continuation、冷实例只读 | archive-pause-feedback；原candidate/repair-noting证据 | 本次影响路径有受控边界证据；原机制继续有效 | continuation不冒称全compressor；真实重启/后台现场待核 |
| V2-46 | 原冻结root/history；当前prefetch纯事实 | Q03两次真实原生request build；current user数据追加、root同字节 | wire-repair/final-repair-2；固定personal_provider | F02机制关闭保持；新事实不回改历史或冻结prefix | 没有外发模型HTTP；模型输出行为仍待现场 |
| V2-47 | same main_read_surface predicate→Context Recovery replace | 带Conversation开始和压缩区间；旧footer替换；非Main原生 | context_compressor.py；conversation_compression.py | 静态机制支持 | 有意义说明不泄露Snapshot/Session内部审计ID |
| V2-48 | 原MemoryProvider→MemoryManager→AgentNotice；原receipt/history | 个人判断留个人仓；公开只可选通用值；冷读无remoteIO/新表 | core.patch；personal.patch；固定v3 | 沿既有接缝补线，未增AgentLoop/调度器/对话库/API层 | 内存pending是提示尝试管理，不是归档修复/远端恢复授权 |
| V2-49 | 公开通用桥；个人归档规则；根CLAUDE AC-03 | diff无personal_scope/SOUL/Skill/Prompt/权限修改；AC-03显眼登记 | 固定v3 CLAUDE顶部；三仓diff | 公开/个人隔离保持；重要自主形式已登记 | 登记非用户确认，亦不自行新增门禁；最终公开范围仍由root审 |
| V2-50 | 官方runner；冻结check/health | 22不同新增有效节点；旧安装fixture定向1P；原32P/1F保留 | final-focused/final-repair-2；profile-key-red/green；installed-assertion-repair | Q03受影响检查有效；原health/3UI关闭结论复用 | 不同批次并集不虚报全套新跑；本审查零复跑 |
| V2-51 | PM官方runner+isolated状态；依赖受控 | 真实SessionDB/manager/AIAgent；网络/模型受控；本审查只读 | Q03原始命令/日志及source-map-v3 | 本次方法合规，适合代码机制证据 | 没有真实NM/模型/浏览器；安装日志仅校验准备，不等于加载 |
| V2-52 | v2现有UI baseline；v3全部UI字节相同 | 163文件全部hash相同；新Notice消费原warn/info rail | source-integrity-v3；固定UI native-notices | 未回滚用户表现；原F04/状态接线表现判断复用 | 实际Pin/拖拽/滚动/动画及toast现场仍待最终包 |
| V2-53 | docs/cloud-deployment-sop.md；README | 文档/索引已交，静态步骤与正式入口一致 | 本次文档交付满足；不构成云端已验 | 最终交付填入配套版本/产物，云端执行另行授权 | 文档项代码阶段通过 |

## 4. 核心目标及验证方法审查

### Q03完整接线与owner

`finalize_turn → AIAgent._sync_external_memory_for_turn → MemoryManager.sync_all → personal sync_turn → canonical History/receipt → MemorySyncFeedback → 原生AgentNotice → notification.show → 既有UI notice rail`。原completed、非failed/interrupted、有效user/assistant gate不变；原redaction、Provider FIFO和后台ContextVar不变。公开核心只识别可选通用类型，不导入个人NM策略；旧None/未知返回没有新状态或可见行为。

`memory_manager.py:629–664`按 `(provider.name, canonical_profile_home, opaque_scope)` 管理attempted/pending；pending另记physical session。重放只在同owner、现有provider的后续完成边界发生。新反证刻意使用完全相同provider名、scope、state、stored ID，只有真实ContextVar home不同：旧key两分支失败，补home后5个受影响节点通过。不能依赖个人插件恰好把home编码进scope来代替通用隔离。

`memory_sync_feedback.py:9`捕获当时native token、session、manager、notice/status callback；退休、替换、shutdown都拒绝，不借用新Turn回调。False/exception不算尝试成功，pending保留；只有返回True才记attempted。原Notice调用没有driver/人类ACK，True只证明尝试调用；通知偏好、离线或driver丢弃仍可能不可见。warn/info沿原5000ms，error仍手动关闭。

### 暂停、冷态与相容恢复

个人`personal_provider.py:475–545`将原reconciliation-required转为带UTC时点、当前Profile/本Conversation范围的事实：自动Thread归档暂停、本地合法History可用、NM旧副本未撤回、并非全部Memory检索失效。scope由原endpoint/Space/Thread receipt key与canonical home派生不透明hash，正文不泄露endpoint/路径/审计身份。

只有同scope正式归档检查unchanged，或明确ACK且receipt提交，才能从暂停转相容；不把unacknowledged、skipped、禁用、空Recall、检索成功当恢复。相容文字明确仅该时点前缀相容，未重核远端。状态转换revision使“暂停→相容提示未发→再暂停”仍能提示新的暂停；先重放旧带时点相容、再得到新暂停，不冒称当前重新检查正常。

冷实例通过已有receipt只读SQLite与canonical History按原清洗/指纹判断不相容；没有新表/持久观察库、没有网络读写或自动远端修复。匹配、未完成尾部、无receipt或读取失败保持未知，不造正常状态。每次合格prefetch可再携带事实，超时丢弃不产生一次性假ACK；该事实只入当前输入数据，不改root/旧历史，不加“通知/修复/停写”指令或权限。真正冷服务重启和模型如何使用仍需现场核对。

### 证据有效性与测试断言

读取原始日志和对应固定测试：20个新增不同节点的有效并集，加上跨Profile两节点，合计22不同新增有效节点。重叠复测不相加。真实隔离SessionDB、官方rewind、原生enter/leave token、MemoryManager与AIAgent正式接缝成立；网络和模型边界受控。两次实际原生request组装证明root逐字相等、历史无新fact、当前输入含事实，不能称外发真实模型。普通Main通知测试暂hold token/flush确定受控时序，只证明正式事件接线，不证明自然后台时序必达。

`final-focused.log`的19P/1F保留；失败是恢复pending先重放的新测试预期，`final-repair-2.log`定向3P修正，未改生产规则。`profile-key-red.log`2F与green5P保留。原回归32P/1F中的安装断言只认连续`create --content-file`，实际已获准Skill为`create --space … --content-file`；修复仍在同create fenced示例要求content-file，正式安装/注册/Bundle/sync后续断言实际执行1P，未改Skill或安装器。

核心5文件冻结ruff/health/no-tmp通过，health零blocking/advisory；个人两文件用相同公开health engine/rules/thresholds与原scope pattern比较，ruff/health/no-tmp通过。无新增例外或阈值放宽。测试失败和原安装fixture失败均保持历史原貌，不将未重跑的整组写成全绿。

## 5. 发现、整改与范围外项

|问题/条款|v3独立结论|剩余关闭证据或边界|
|---|---|---|
|Q03，05/06/11/24/34/45|只记日志缺口在源码及受控正式事件链层已补；最小可见降级方向成立|最终版本加载后实际L09/L10，核准确范围、owner、迟到/去重与可见结果；本阶段不全关|
|Q03通用跨Profile key|原缺home真实问题已按反证修复，2F→5P，源码匹配|不再要求复跑全部22/33；不外推全平台|
|AC-03|5秒attempt、可能下一完成边界，已显眼登记；不据登记新增门禁|用户尚未确认具体形式；交付须如实说明，不宣称永久/必达|
|F04，39/40|沿用v2源码/受控冷DB→正式History→UI修复成立，无相关字节变化|真实后台中断→回收→反代冷读仍待集中现场，不能只靠安装/PID签关|
|原F01/F02/F03、health及3UI|沿用已独立核闭合的适用代码机制/定向检查|旧失败保留；真实UI总体仍另核|
|08/09/10/11/28/36模型行为|原样保留机制支持、静默/归因/未精读反例及未覆盖项|Q03受控响应不关闭模型表现问题；NO_REPLY/隐藏气泡仍未获准|
|20～26/30/37～43/52现场|源码支持程度沿用矩阵，不预填通过|最终加载指纹、隐藏IAB实际输入输出、Metadata一次真实创建与后台时点完整包|
|53 SOP|v2稳定文档/索引静态交付成立，v3产品文档无变化|最终版本产物填写；Linux/TLS/Tunnel/Access未执行不冒充已验|

本阶段未新增确定P1/P2，不要求新架构或远端恢复来补本任务。Cloudflare Access与明确未来愿景不擅自扩成当前本机执行要求。隐藏IAB故障造成此前0输入/0Reminder属于未执行，不当产品通过或产品失败。root后来报告的PID32366与final-restart.json属于待独立核对的现场交接，本源码阶段没有以口头说明代签加载。

## 6. 修复与独立复审交接

v3源码阶段整包完成：53判据影响审查、7增量源码/10依赖/日志匹配、Q03正式接线与公开个人边界、原失败修复方式均已核对；未变部分复用v2完整独立审查，不重跑有效大套。对应证据为 `source-integrity-v3.json`、`evidence-source-map-v3.json`及本报告副本 `v3-code-evidence-stage.md`。

下一次同门禁只接最终加载、反代实际旅程、L09/L10、Metadata正式创建等集中原始证据，核源版本及实际输入输出后再收束；若最终源码再变，只做适用影响核对。保持本次53条、历史结论和失败，不把等待等同成功或提前判整个版本失败。


# 第二次全范围复审：v3 实际加载及 L09／L10 证据复审

## 1. 对象概览与审查方式

**L09 正常后台 Reminder 完成后冷恢复、L10 真实后台 Reminder 中途接入／UI Stop／正式回收／冷恢复的代表链成立。F04 所要求的至少一条真实后台中断终态恢复条件已满足；结合 v2 同源源码和受控失败分支，F04 修复可关闭。此结论不等于全来源、全故障或最终总门禁 PASS。** 实际断线恢复、Metadata 一次创建及其余53项未关闭内容保持待核。

UI 操作是 root 在其主聊天自建隐藏 IAB 完成，后台记录／正式 close 由指定 worker 完成。本 Agent 只独立读取已保存 AX、PNG、版本记录和只读 DB／事件快照，比较身份及持久事实；没有浏览器控制、请求服务、模型调用、NM 操作或测试复跑。只读查看既有 PNG 不作为本人操作产品的证明。子 Agent 浏览器路由此前失败及 0 输入历史不覆盖、不改写。

本组仍对应固定 v3 set `7de214d8210ce2752ad2b1b1c36f736b9f5ce6d558cd78310de6d1a76dbcae30`。`local-deployment-evidence/final-restart.json` 实际 SHA `8628c049002ffce9b0c811bd13b9e4f710f794ecf2a47bc13cfb1e8ede3d0b36` 匹配交接；记录 20:25:04 原生 dashboard `--host 127.0.0.1 --port 53446 --skip-build --isolated --no-open`，56112→32366。三仓实质 drift 空、两份 v3 产物、5 库 integrity ok、旧消息/root binding 保留、身份与已安装插件保持。`final-loader-check.json` 将 53448 两 SPA 首 JS hash 与新产物绑定，Caddy53882与后端32366一致。以上是加载证据，不单独代签 UI；后续真实 AX URL 均在相同 53448 深链。

## 2. 独立判据与此次覆盖

沿用 V2-01～53。本包影响07、17、20～25、37～43、45、48、51、52；F04六条件不降低。真实中断属于原本明确接受的真实后台终态，既有受控 dispatcher/build 异常仍负责其专门分支，不能临时把“必须生产故障注入”加作门槛。也不能把正常短工具样本当作取得断线或在跑工具窗口。

## 3. 实际链与逐条证据

|范围/判据|实际证据与正式对象|独立判定|限制|
|---|---|---|---|
|43 最终加载|final-restart 与 final-loader-check 的源集、产物、PID/端口、旧历史保持记录；实际页面相同53448|本组样本与最终v3本机加载关联成立|不冒充云端、TLS或Access；不是本Agent亲自启动|
|07/37 L09 冷唤醒|ordinary UID `80f97ae022984bd786afbf4b63f4dd8c`；Conversation `conv_e732ee1ad1d3450fb0ff8859fe517be6`；schedule `sched_29db5564ee394835b9a916eeefb3fb29`；真实carrier UID `feb42fce81b144d9914334d2c5fc5ead`|已注册once、原运行回收后宿主到期恢复；首页Running有实际AX/PNG|原90s表达式失败保留，改ISO后仅一条有效once；非自动强制24h样本|
|39 L09 正常冷恢复|root-L09-cold-ax/PNG；只读DB20行、9个真实reasoning row、3个到期execute_code工具结果、final430；所有display_metadata无turn_terminal|正常完成后冷页面显示原Thinking、工具和结果；成功路径没有新增失败terminal写入|3个计算是毫秒量级，未覆盖工具运行中断线；没有凑时长|
|37/38 L10 中途运行|stored `20261018_204959_5b561e`、conv `conv_a3c611b55dbe4cefbb8ee081e6a1c224`；注册runtime ba6a34e0正式close后0；到期runtime3987dfb4；Tab5实际Running/Stop截图和AX|后台运行中首次打开后的真实工具Success→下一工具Running成立；首页Running成立|root报告首次Thinking Streaming；目前交回的保存AX直接证明Thinking Complete及运行工具，首Streaming原始片段未见，暂不独立签首delta时点|
|22/23 L10 状态|before-stop AX：空Message、Stop、execute_code Success与Running；after-stop AX：Interrupted、Send disabled；PNG一致|真实尚在跑工具没有误标Failed；Stop后显示Interrupted，保持成功工具1830|点一次Stop来自root操作归属记录，后台快照只能佐证已中断，不能证明鼠标动作本身|
|39/40 F04 真实冷恢复|after-ui-stop DB source.metadata；20:52:11 close runtime3987dfb4、runtime/lease/poller0；新Tab6冷页面；20:54:19最终DB快照|持久中断事实、两个已有工具及Thinking在冷读恢复，未依赖旧runtime/ring存活；代表现场条件满足|本例残余outputs为空，已有reasoning/tool由原生写入；dispatcher绕过finalizer、未持久残余仍按既有受控正式DB证据|
|25 冷usage/context|L10冷AX及PNG显示139,464 tokens、87.3% hit、10%；L09冷显示249,266、90.0%、11%|冷页面统计可用，未空白/复位为零|数值来源精确性仍复用已有冷估测试，不用截图代替计算核验|
|41/42/52 本机反代与表现|root新建hidden IAB，实际53448页面与工具卡PNG；v3 UI字节与v2相同|本机反代实际产品入口成立，已见页面无明显布局回退|未全面验Pin/拖拽/动画等；没有操作桌面或可见页，不据此签整个UIUX无回归|
|45/51 资源与无重执|L09-final-readonly-resources九项0；L10-final-close与final快照runtime/active/lease/child/compression空，schedule done、next空/claim空、delivered见证保留|本组自有对象回收成立；L10中断后、close后、冷开再close后三份14行messages完全相等，UID唯一，无新工具执行行|L09第一次poller采样阳性保留，后只读复采0才签最终0；global其他样本不拿来计自身泄漏|

## 4. F04 六条件及真实 UID 对账

1. **真实源及owner**：L10登记user UID为 `e9efd0d4bd21445aa5f3b06e8953391f`，到期carrier为另一真实源UID `1c53dc99be854278a6b1cb9e650811e1`，均属main-assistant同stored/Conversation。pending reminder的carrier_message_uid与该源行一致；terminal.source_message_uid也精确相同，没有误挂原ordinary。对比中途快照与Stop后快照，row366的id、session、role=user、UID、content、api_content、timestamp全部不变，仅增加原display_metadata中的terminal。
2. **首终态与回收持久性**：terminal为`status:interrupted`、空text、finished_at1792327912.190372。正式close后runtime0/lease0，OS sample rc0且自有poller空；新Tab6不是保留原对象假冷读。中断后、close后、最终冷开再close后全14行messages逐项相等，message UID唯一。此真实样本证明一次中断保留且冷开无重执行；CAS竞争、retired/错误owner/rewind拒绝仍复用v2代码与受控证据，不声称此次现场注入过这些竞争。
3. **真实终态与不伪造内容**：actual tool结果是explicit stop，exit_code=-1，6.28秒，kernel killed；不是Stop回执即假定中断。UI显示Interrupted，未冒称第二校验完成或伪造最终1830回复。已有末尾空assistant行是原生finalizer保存的一部分，现场未因terminal恢复再加行。正常L09全部metadata无新terminal，与成功零写机制相符。
4. **已有输出与身份**：L10到期reasoning UID `5fd9328ff98c47f590e13ff80258e5e1`（4268字符）与 `a7f33b658f524c1d8b72c3b491e739a9`（1541字符）持久存在；总5个reasoning对应冷AX5个Thinking。成功工具message UID `68c73e875e104934aa73aef9b3b28610`、occurrence UID `839966b7c79b444e94b582f20f7a10ca`，输出1365+465=1830，0.07秒。中断工具message UID `4a4f504de1b44dedac2fcbb33086407f`、occurrence UID `b3d6cb0563fc45c391cef9211a8da0ae`，6.28秒，中断正文完整。顺序与冷AX一致，没有两个同identity重复卡。冷工具展开AX内容和原DB JSON一致；Thinking仅核卡片与持久源数量，未用折叠卡冒称全文逐字视觉核对。
5. **正式History与UI消费**：Tab5中途→用户Stop→离开→原生session.close→runtime0→Tab6相同反代深链冷读；冷卡真实展示Success1830和Interrupted，后者展开显示上述explicit stop/kernel killed。冷resume新runtime1dcf162c只见history14条加载，无新模型turn；最终14行原样。该链与固定v3原生History/终态投影代码及v2受控RPC/REST fixture互相支持。不能将这次已原生落盘的工具卡当作真实dispatcher异常的残余outputs路径已经现场验证。
6. **模型输入与失败保真**：源api_content前后相等，没有把terminal改成新user/assistant正文；正常完成不写terminal。展示/DB失败不覆盖原错误与不污染实际模型请求，仍以v2正式SDK序列化、writefail/owner/lease受控分支为依据，本例没有人为造写入失败。六条件证据组合满足原F04修复与代表现场要求，并明确哪些依靠真实样本、哪些依靠已有效受控反证。

独立对账摘要和被审文件SHA保存在 `independent-reverification/l09-l10-independent-crosscheck.json`，包括全行相等、source不变、真实occurrence UID、工具结果hash、AX/PNG与版本证据hash。原始私有记录仍仅在ignored证据目录，不复制私人Default正文或凭据。

## 5. 保留的问题与证据边界

- **断线子项仍未覆盖**：L09工具过快，Caddy重启实际0/1。L10是中断，不替代WS掉线/重连；root已另准备L11，但本次没有该结果，不预填通过。
- **事件ring确有截断**：L10中途latest_seq1966、结束2995，保存回放标truncated=true、512条。它不能证明全程逐事件无遗漏；这次冷恢复证明来自已落盘History与真实页面。完整inflight/replay严格seq机制仍依据此前同源受控证据，不能仅拿末512条“全量核验”。
- **首Thinking Streaming记录不足**：root叙述该时点，已归属记录；本包保存的L10中途AX是Complete/Running阶段。22项首帧时点不由叙述直接签关闭，后续若集中原工具返回/已保存片段可补核，无需为审查者重跑模型。
- **场景账本动态字段未收束**：已读ledger顶层仍为RELEASED_BLOCKED_IAB_UNAVAILABLE、executor仍旧子Agent，实际ordinary/reminder已各2，部分terminal/cold字段空。它是汇总记录滞后，不否定原始UI/DB事实；最终交付须按真实root执行及已完成场景校正，并保留原阻塞历史，不能直接以该顶层旧状态报最终结论。
- **Q03仍待实际专门样本**：L09/L10为无NM操作的算术Reminder/中断，不是归档edit/rewind降级通知场景，不能因为场景编号曾被口头关联就关闭Q03可见性；源码及受控接线结论保持。
- Metadata本次尚无真实attempt/release证据，26/30保持待核。08/09/10/11/28/36的原静默、归因、精读、委派等模型行为反例未由算术场景关闭。53文档交付及云端未验边界不变。

## 6. 同次复审结论与后续

F04代表真实后台终态恢复已补足，原缺陷按“源码机制＋受控专门失败分支＋真实中断冷恢复代表链”关闭；不扩大为所有故障现场已验。本组未发现新的确定产品代码阻断。其余53项按本表提升证据等级，未涉及项保持v3前节结论。待集中断线旅程、Metadata、必要行为与UI剩余材料及最终记录收束后，继续同次总门禁，不重提判据、不复跑有效套件、不先给最终PASS。


# Q03 最小真实用户入口：执行前独立判据补充

此为方案评审，尚未执行，不关闭Q03现场项，不增加原53判据。既有固定v3源码、受控owner/late/cold/recovery分支继续有效，本次只需补真实Notice闭环。

**所提正式UI编辑方案足够覆盖Q03核心真实分支，条件是编辑确实打破该Profile／Conversation已经ACK的归档前缀，并在真实页面看到同owner、范围准确的暂停Notice。** 仅完成Metadata Memory创建不证明Thread已经归档；须先从既有receipt／正式归档记录确认同Conversation、同Space／endpoint的ACK前缀包含拟编辑的原消息。选自动归档已启用的自有合成Conversation；不得为测试打开main归档或改配置。

最低执行及关闭条件：

1. 保存该自有源消息UID／正文hash、Conversation／Profile、原ACK receipt和既有批准创建Memory的ID。等待Metadata任务结束、无进行中写入，再经原生UI编辑一条确已归档的合成消息。安全同义纠正必须保留不批准持久写入、不跟进和完整测试访问边界，不修改身份Prompt，不补入新审批或远端恢复指令。若可选择同样已ACK且位于批准创建之后的自有合成普通消息，编辑它可减少合法History回退影响；没有该消息不必为此额外造输入，原第一条方案仍可用。
2. 原生edit可能截去后续合法分支。这里的“后续批准失效”只指它不再作为新分支后续执行的授权；不能倒推既有已批准且完成的Memory创建变成未授权，也不会自动撤回远端Memory／Thread。旧真实创建证据与Memory ID独立保留，既有远端对象不重建、不改写、不删除。
3. 允许正常编辑Turn完成并由既有后台sync检查。核真实reconciliation-required、安全拒写、原receipt不推进、合法本地History仍可读取；直接保存实际页面Notice的AX／PNG和owner／时点。Notice须准确表达本Conversation自动Thread归档暂停、本地History可用、旧远端副本未撤回，不能泛化为所有Recall不可用。不要以模型口头复述、日志或手造toast替代真实Notice。
4. v3后台结果可能晚于原Turn token，首次无Notice不直接判失败。先确认是否已有pending；只有必要时，再在同Conversation发一条明确“不执行任何持久操作、不创建提醒”的最短核对消息，以提供下一合法完成边界。这属于额外实际输入，须由root纳入明确场景预算，不能默默追加。既有受控测试已覆盖该延迟，无需为抢首次窗口改时序或重复模型调用。
5. settle后正式close并核资源回收；冷恢复合法History不产生归档写入或凭空healthy。冷页没有永久告警不等于healthy，也不构成失败，现有形式只有5秒Notice。冷实例未知不得伪报相容；只有后续正式兼容／ACK边界才可转相容。本次无需再造恢复或额外冷态模型Turn，已有受控冷receipt检测证据有效；若现场实际出现healthy／相容声称，必须核真实依据，不能忽略。

满足上述真实暂停Notice＋正式拒写＋合法History与owner对账后，可关闭Q03核心现场缺口；不把它扩展为持久状态面板、edit当下必达、投递ACK或远端修复验收。AC-03具体5秒attempt／延迟形式仍是已登记待追认的自主收敛，不冒称用户确认。本Agent本次未运行任何产品／模型／NM／测试／浏览器，也未读移动实现。


# 第二次全范围复审：L11／L12 最终本机补证与 PI-21

## 1. 对象概览

**本机反代在真实响应期间断开并自动恢复的代表链成立；22项首Thinking可见的现场证据已补。最终本包自有资源归零，F04原关闭结论保持。** 不把本次代理重启说成后端crash／进程重启恢复，不签Cloudflare/TLS/公网或最终总门禁。Metadata及Q03现场仍待各自整包。

仍沿固定v3源码和同次53判据，未重提判据、未读取移动实现、未复跑测试。UI执行者为root主聊天自建隐藏IAB，后台worker只做获准记录／回收／唯一Caddy重启，本Agent只独立审文件、既有PNG与事件／DB记录。

报告 `local-deployment-browser-validation.md` SHA `707f380fd66856a4d4f6f70e76c7ad613ec512e1b4dbf46318c6f03572e51559`及 `local-deployment-final-evidence-manifest.json`所列20个文件全部匹配。另独立校验L11/L12事件文件、最终DB摘要、首Thinking AX；结果保存在`independent-reverification/l12-independent-crosscheck.json`。

## 2. PI-21 权威与范围影响

已直接读取snapshot-index PI-21：用户对精确NO_REPLY提案明确答“先保持现状，列为待决项”。因此V2-09的原安静性失败继续作为真实已知限制，但其本轮处置已由用户明确指定为保持现状、单列待决。**不能要求本轮未经授权继续实现NO_REPLY／过滤，也不能把该条改为静默验收PASS；该已知限制本身不再要求本轮必须修复才能结束获准工作。** 最终交付若满足其余门禁，只能按已确认范围说明完成和此待决项，不能声称原完整安静性目标已实现。

V2-35 Prompt授权、40真实执行事实可见不变；不删Thinking、工具、状态、不新增隐藏／未读／通知策略。PI-21不豁免Metadata、Q03、后台真实状态与完整Timeline，也不把尚未解决的其它模型表现/证据缺口一起转成用户接受。该新口径只影响相关条目的授权/交付状态，不扩为第54项或新产品机制。

## 3. 正式链与本次判定矩阵

|条款/场景|原始证据核对|判定|界限|
|---|---|---|---|
|22 L11首Thinking|root-L11-streaming-ax同一53448深链，在新用户输入后展开Thinking，显示尚未完成的实际reasoning文本；之后才出现工具及final|此前只见Complete的首响应现场缺口已补为代表样本支持|AX标签为Thinking Thinking，不虚称保存了字面Streaming；没有统计所有请求首token延迟|
|37/38 L12触发归属|UID991e1d1794294236831c2a0b93e95638，row376，同main/stored/Conversation/runtime c2c29c5e；seq2113新message.start、2116同新Turn output_state、2117原生reasoning.delta “Report”、2118带身份投影|确为当前新响应触发，不是历史delta或旧Turn|非工具执行窗口；L09/L10工具中途和终态恢复另有证据|
|38/41 真实断线与自动恢复|root-L12-during-ax同页出现实际Thinking文本及“Disconnected. Reconnecting to Hermes…”；restored-full AX同页出现完整final、旧Success和Interrupted，断线文案消失|真实反代断线／同页自动恢复代表链成立|UI事实来自root操作与保存AX，本Agent未亲操；不据后台健康探测替代页面|
|39/40 身份及无重执|message.complete source_boundary精确该UID，committed rows376/377；仅一user/一assistant，无新tool；旧L10字段逐项保持|恢复未重发当前输入、未重复工具，旧中断事实保持|有界ring后段有gap；不是全事件流逐条无缺口证明|
|43 同源部署|Caddy53882→77413，backend32366不变；v3加载关联复用前节|在同一部署上验证代理恢复|没有后端重启、crash或持久库恢复实测|
|45/51 资源与预算|总4ordinary/2once/2Conversation/1proxy重启；原2样本账和L11/L12独立账；九类自有资源0|授权增量单列，最终回收支持|不把额外两ordinary伪装成原2条预算；不把Exam并发对象当本样本泄漏|
|52 表现保护|恢复后的实际PNG／AX保持原卡片、侧栏、布局；产品UI字节无改|已见页面无明显表现回退|Pin/拖拽/动画等非本组全面覆盖，不泛签全UIUX|
|09/35/40 PI-21|直接读取新用户明确口径；原失败与待决保留|用户要求保持现状，禁止擅实现提案|不等于静默通过，不豁免其它条目|

## 4. 独立原始对账

### 连续触发前缀与真实代理操作

重新解析L11的2112条原始事件与L12头部，runtime c2c29c5e的seq1～2118恰2118个序号，无缺失。seq2116的turn_id为`20261018_204959_5b561e:20261018_204959_5b561e:4e8f0ce9`，assistant UID `62f00126d1a24b75a01636fda26247a4`；seq2118指回原生seq2117非空reasoning，最终row377身份一致。触发证明记录同source、同owner仍running，21:07:43.354611；代理实际操作21:07:43.398208～43.720569，只有53882→77413，backend32366保持。caddy记录中的`root_running_window_confirmed:false`对应改用已授权的实际响应触发证明，不能误读为root当时肉眼确认工具窗口；本次没有该工具窗口主张。

watch操作后退出，没有把后续缺口偷偷填平。最终message.complete seq3026在较晚采集尾部仍真实保存，payload的source_boundary、持久row、answer与DB一致；后续ring截断单列。完整页面恢复是实际AX＋持久History的证据，不能改称旁路全程事件收集成功。

### UI与持久事实

断线AX里末段先出现当前输入、Thinking及片段“Report ~300 characters, no”，并有Disconnected文案；恢复全AX同URL显示最终完整回答，区分原短计算1830已完成、第一次有界校验中断、后续独立有限校验已完成。之前Success/Interrupted工具卡及Thinking未丢失。最终DB仅新增row376 user与row377 assistant，UID唯一；对原L10基线的id/session/role/content/UID/tool字段/reasoning/display_metadata逐项相同，原carrier terminal仍interrupted。没有为恢复再提交或重新执行工具的持久证据。

**证据纠正：** `root-L12-disconnected.png` 与 `root-L12-restored.png` SHA均为`cdf5c005762bd510477bd591fc33575b76e0952bc820565a4fefe1f6c00e8030`；实际查看图像均为恢复后的最终回答，不是两个时点。故本审查不使用“disconnected.png”证明断线，也不声称有独立断线截图。断线原始AX和代理/事件记录已提供充分的实际界面状态证明，无须为补截图重跑产品；最终报告应注明该PNG误名／重复，保留原文件。reconnected与restored-full AX也同SHA，按同一份完整恢复记录使用，不计两次独立观察。

### 最终回收与账本

L12最终close成功；原sample rc0但发现poller尾部的阳性记录保留，下一次有界复采rc0且poller空才确认最终0。最终DB own_active/lease/child/compression空，正式registry done、next/claim空，delivered见证保留；summary九类资源0与这些原始事实相符。旧L09资源证据继续有效。新ledger已修执行者、已执行状态、终态证据及增量预算，原冻结L09-L10-final-ledger hash不变；此前“仍阻塞/旧执行者”汇总滞后项关闭。精确点击/cold-open墙钟未取到则留null，未伪填。

## 5. 保留项与发现

本阶段没有新增确定产品代码阻断。新增一项证据标注纠正：断线PNG实际为恢复图，须按上节缩窄其用途；有真实断线AX，故不阻断该代表链结论。

本组明确未验证backend crash/outage、Cloudflare Access/Tunnel/TLS公网、其它平台、所有Provider失败或全UI交互；Secretary显式reload、浏览器前进后退未专门取证。原受控机制证据继续适用，不用这些未覆盖点虚构产品失败，也不当已验。

Metadata attempt-0的外围lazy读取阻塞据交接为0输入/0模型/0NM写，不能当产品失败或创建成功；attempt-02尚执行中，本阶段不审未交结果。Q03仍等正式编辑后真实归档暂停Notice包，不由L12算术/回应场景代替。原模型归因、精读等观察保持，不能被单一准确算术总结一并关闭。

## 6. 同次门禁状态

L11／L12本机补证已独立接收其实际覆盖范围：首Thinking、真实响应期反代断线与同页自动恢复、持久身份无重执、最终自有资源清理。F04维持前阶段关闭。V2-09按PI-21转为“用户明确保持现状的待决限制，未通过静默验收”，不再要求本轮擅改修复。最终总门禁仍待Metadata／Q03及其余矩阵收束，不预设总PASS。


---
# 独立最终 Verification · delivery-snapshot-v4（2026-10-18，新审查者）

## 1. 审查对象与结论概览

审查者：独立 Astra/high；本次仅写本报告，不修改产品、调用模型／NM、操作 UI 或服务。对象为三仓完整 v4 快照，主清单预期 SHA256 `27b624d059b2f17d7d1c7e33147a5da1048eef43544b92093517340759332afb`。baseline.txt 仅为历史定位；dirty 内容以 v4 实体为准。当前结论（第三次窄补证）：**v4统一加载、B真实模型Metadata创建、B实际请求root精确批准句及A首次真实Thread分叉均已核；E04正式History REST与页面混入退休分支内容已确认，整体门禁不能通过，待根因/修复及针对性证据。** 不由Thread底层成功豁免History出口偏差。历史报告和本次各阶段事实保留，最新判定见§6.6–6.8。

权威：2026-10-18 最新 product-intent.md 全文＋snapshot-index.md PI-01～26；身份参考只继承身份与表达；白板、07、06、08、个人 PHASE3 的适用现行工程条款服从最新产品意图。旧技术规格及历史通过均不能覆盖用户后续决定。先独立建立下表，再读取实现、测试、旧报告和动态看板。

## 2. 独立要求清单与覆盖

判据建立于源码调查前。产品原文简称 P；白板简称 W；07/06/08 为 v4 中同名规范；NM 为 v4 Provider PHASE3 现行§1–7。仅有未来愿景的内容不扩为本次新开发或常驻产品面板。PI21、PI23是用户接受的未解决限制，不更名为历史通过。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| V4-01 | P§一、二、三、十一、十二；身份参考及两SOUL | 产品定位/全体Main | 长期通用个人助手；交流本身有价值，不强制任务化，不冒充心理治疗师 | 部署身份与实际指导覆盖学习、情绪、自然交流；不强加唯一空间/工作助手定位 | §3同号 |
| V4-02 | P§3.1、4.1–4.2；07§0、3；02身份/Foreground保留项 | 连续性/身份 | Conversation跨压缩和恢复稳定；new/reset/真实fork独立；原文保留 | 正式compaction/resume/rewind/fork路径保持合法历史、Notebook选择、来源身份，用户不需手工Session交接 | §3同号 |
| V4-03 | P§3.3、九；PI01、06、10；08§1 | 权限/边界 | Profile与Conversation/Space不默认等同；统一列表不授予模型跨Profile | Main History同Profile显式跨Conversation，Noting只父域；新建选择owner，既有不可迁移 | §3同号 |
| V4-04 | PI01–04；P§7.3、十 | 实际验证/本地 | 双Profile真实NM，Noting＋Idle 100k/5s；用户测试前缀独立于可部署SOUL；不改模型窗口/时钟 | 实际配置、普通输入、工具/持久结果证明；模型自述不作完成证据 | §3同号 |
| V4-05 | P§五、7.2；W C7/I/U；07§5 | 事实与来源 | 用户确认、推测、建议、历史结论可分；来源存在不等于支持内容 | Guidance与结构保留来源，检索原文/后续纠正；模型失误按PI23保留真实观察 | §3同号 |
| V4-06 | PI05；07§4.5、8.12–13 | 模型投影/API | 内部Snapshot/Pointer/Anchor审计标识不入AI正文；完整有意义覆盖说明不丢 | show、维护返回、初始/续Turn、完成/提案都用模型投影，旧API保留；unknown不阻断正文 | §3同号 |
| V4-07 | W C1–9/I/U/L/N；07§4、8.11 | Notebook类型/生命周期 | 七类型、稳定entry与不可变version；职责六步；7天/72h不自动撤销责任 | 来源、类型、关系和状态校验；年龄不被重读/改写刷新；合规完整状态才发布 | §3同号 |
| V4-08 | PI08、15；W C2/3/6/E1/K6；07§4.1、8.10–11 | Candidate/结算 | 来源严格二选一，refs型不复制正文；实际成功覆盖先结算来源再关闭候选 | structural exclusivity、目标特化简述、引用完整性；保留失败/未知/未覆盖与共享依赖 | §3同号 |
| V4-09 | PI08；W L6/F；07§8.10 | Persistence/授权 | slash或超限只授权提案；明确内容和目标批准后写 | 草稿/措辞修改/沉默不写；实际结果成功/partial/unknown可追查；Noting不查NM保管质量 | §3同号 |
| V4-10 | W L1/L9/N3；07§8.13 | 容量/原子通知 | >12000字符或>60条仅提示提案；完整快照同条注入；旧pointer通知剔除 | 计数边界、完整正文、busy/fence、pointer事务一致，失败不发布草稿、不自动唤醒 | §3同号 |
| V4-11 | 07§3.1–3.2、4.5、8.11–12；04保留 | Noting权限/结束 | 四工具真实执行白名单；冻结父指令失效；finish独调用，返回后提交；五Turn有界 | 同步/并发拒绝越权与混批；end_requested锁写；forced/overflow合法提交，其他失败不伪成功 | §3同号 |
| V4-12 | 07§3.1、8.1–2、11.1；W P | 联合压缩/cache | Active多模态前缀冻结，父root/tools/cache等价；四入口；Force区间一次；重启不自动恢复child | 正式父接缝、不等待Noting；External只拒Noting；成功compact才新区间；不要求并发任务互相合并 | §3同号 |
| V4-13 | P§4.3、六；PI13、21；07§6.4、8.6 | 主动性/明确待决 | 24h Instant为行为要求而非强制配额；不造任务；NO_REPLY提案未获实施批准 | 精确获批S01/Q02落位；保持现状，静默失败明列待决，不以过滤隐藏执行 | §3同号 |
| V4-14 | W K1–8；07§6.1–6.3、8.14 | Scheduler/交付 | Main独立排期，原生解析/owner；instant空闲唤醒、busy转deferred；deferred等待请求 | 注册/更新/暂停/删除与claim原子；实际请求与响应ACK；重试/重启不丢pending不重复；Notebook不联动 | §3同号 |
| V4-15 | 08§2.1–2.2；PI16–18 | 冷态宿主/薄弱接线重点 | 无浏览器/Runtime时常驻宿主仍按owner恢复原Conversation Main；重启自动发现 | 真实冷态、跨Profile、busy竞争/取消，复用claim/lease；不新建替代Conversation或永久驻留Agent | §3同号 |
| V4-16 | PI17–19；08§2.3；06§1.4/3 | 状态/完整恢复 | 任意入口Turn、实时/中途/完成后、全局未打开会话状态均真实可见 | 不只running/body、不以有限ring代完整Turn；Thinking/工具/Reminder/正文/后续流接续无重漏 | §3同号 |
| V4-17 | PI06、07、19；06§1 | UIUX保留 | 首页独立Profile下拉、跨Profile侧栏固定图标；Thinking、工具状态、通知时长、滚动/Pin/拖拽保留 | 当前UI差异限定状态/恢复；原显示体验不回滚；需隐藏IAB事实，不由API签视觉 | §3同号 |
| V4-18 | 06§0.3–0.5、1.8–1.14/2–3；PI10 | 原生API/控制 | 薄客户端，旧必填/返回/错误/默认兼容；Stop/Interrupt/Cancel不同；/notebook人类只读 | native RPC/REST接线、受理不等完成、未知不猜idle、恢复不写/唤醒；无第二transcript | §3同号 |
| V4-19 | 08§3–4；06§1.16 | Files归属 | Files固定Profile不随聊天；owner/附件/新建cwd保持；真实错误不fallback | list/preview/download/default-cwd一致，返回原chat完整身份；不改进程环境/cwd | §3同号 |
| V4-20 | PI16、20；06§0.7；08§2.1 | 部署/交付 | 双SPA、同源单后端、反代，source=desktop非Electron；云未验不冒称 | 本机反代URL HTTP/WS深链/静态、机器token注入；dashboard模式；可执行云SOP区分版本产物与云未验 | §3同号 |
| V4-21 | PI09、13、22、26；07§8 | Prompt授权 | 仅批准更改；S01/Q02、History分页、内部标识、NM精确句授权；不恢复Skill | 实际注入源对照审批英文，其余Provider提示不变；没有未经批准NO_REPLY | §3同号 |
| V4-22 | PI10；07§3、6.3；08§1 | 关闭/原生兼容 | Noting、Scheduler独立；History不依赖二者/NM；原生未启用路径不变 | 各开关按真实Profile；坏配置局部fail-closed；原生模型/API/路由复用，无Codex旁路 | §3同号 |
| V4-23 | 07§5.1–5.5；PI13 | History真实性/原生检索 | 同源原文而非摘要，合法路径/消息时间；预算partial、异常不是空命中；分页保留身份 | 原生候选固定路由去重；精确Read/同源offset、content digest；oversize可续读且不越权文件 | §3同号 |
| V4-24 | NM§1–3、6–7；PI01、10 | 单Provider/Recall | Bundle排WM，稳定root；有意义输入轻量pointer非已读；无新增模型工具/治理器 | 资格矩阵Main/Cron/child；endpoint/space owner，故障不阻History、不复用过期pointer | §3同号 |
| V4-25 | PI14、22、25、26；NM§4.1 | Memory窄工具 | 独立~/scrips单文件，不依赖Hermes/Provider/Home/cwd；通用Metadata由调用者提供 | 官方配置同连接冻结，一次POST内容+Metadata、真实ID、CLI与GET读回；preview无网络；普通编辑仍CLI | §3同号 |
| V4-26 | PI14、22、24、26；NM§4 | Memory真实结果/unknown | 模型实际调用批准入口，来源Metadata实际落库；旧partial不覆盖/盲重试 | 原用户批准→实际tool调用→正式POST/ID→正文/Space/labels/Metadata回读完整链；unknown/partial保留 | §3同号 |
| V4-27 | PI24；NM§5 | NM Thread自动分叉 | prefix不一致最长共同点新Thread；说明第一条，分叉suffix第二条起，不重发共同前缀 | 真实NM Thread ID和原生Message ID/所属祖先；旧Thread不改；零前缀、纯截断、再次分叉、冷恢复 | §3同号 |
| V4-28 | NM§5、PI24 | Thread可靠性/unknown | completed未中断用户/助手正文同步；ACK推进，unknown先只读核实，不重放 | endpoint/space/thread账本事务，正式分页total_messages/原生IDs，错误Scope/ACK/竞争不误确认 | §3同号 |
| V4-29 | PI23；P§七、九、十 | 接受限制/非新增要求 | 三类模型偏差不阻塞，历史失败保留；未来协作/全治理/长期可靠性不本轮实现 | 不抹失败、不扩测/开发；独立Metadata/Thread证据不被此豁免 | §3同号 |
| V4-30 | PI11–12；套件证据契约 | 方法/执行限制 | 仅root隐藏IAB；本人不操作UI；固定版本同源证据可复用 | 逐文件绑定、事实归属、未执行如实，不能昂贵重跑代review或API冒称UI | §3同号 |

## 3. 逐条实现证据

### 固定对象、同源性与证据简称

本审查者实际计算主清单 SHA256，与派遣值一致：`27b624d059b2f17d7d1c7e33147a5da1048eef43544b92093517340759332afb`。逐文件复核 core 18,202、UI 163、personal 703 项，零不匹配；符号链接按清单中的链接文本校验，不追随移动源。

| v4仓 | manifest SHA256 | 相对v3实际变化 |
|---|---|---|
| hermes-secretary | `0124760e1f603f1837feede5fb669dfec437521887fe6fab54b6f463f959d347` | 8份文档变化，产品源码零变化 |
| hermes-secretary-web | `da1c36b51b8c1d7315adfe419372a2b8b324fd0c7a12a7ca724cc70b68a07992` | 零变化 |
| hermes-nmem-provider | `7211847d1aee7b52943fec903d905ec8c8f013afcb9083b12f251753e4e19673` | 16项新增/变化、删除旧nm-cli Skill；新Thread与独立创建工具单独审查 |

下文 C/U/N 分别指上述固定快照三仓；N路径省略 `nowledge-mem-hermes/`。E指 `.hermes-dev/product-intent-review-20261018/`，不是移动生产源码。来源要求及判据逐行对应§2，以下给实际路径、方法、观察及边界。

已逐项复核既有 evidence-source-map：ad4有实际hash且可定位的68项中47仍同，21变化不直接沿用；v2的42项全部同源；v3可定位7项中核心5项同源、个人Provider及Thread测试2项由v4证据替换。新 `nm-thread-fork/manifest.json` 7项源全部同源；`standalone-helper/manifest.json` 7项中6相同，README后续文档变化另行静态审查，不把旧README哈希冒充当前。`local-deployment-final-evidence-manifest.json` 所列20份证据文件自身hash全部匹配。上述比对为本审查者只读复算，不是运行产品测试。

证据包简称：A=`independent-reverification/evidence-source-map-ad4.json`及对应历史全范围审查；B=`evidence-source-map-v2.json`、`v2-code-evidence-stage.md`；C3=`evidence-source-map-v3.json`、`v3-code-evidence-stage.md`；D=`local-deployment-browser-validation.md`与`local-deployment-evidence/`；T=`nm-thread-fork/{contract-research,implementation}.md`及manifest、原始canonical日志；M=`metadata-live-acceptance.md`§11及`metadata-live-evidence/standalone-helper/`、`standalone-final-source-binding.json`。A/B/C3只复用经过同源核对的事实，不继承其判据或把过去未验改成通过。

| 条款 | 实际实现位置/正式路径 | 方法及证据 | 实际观察 | 判定及证据边界 |
|---|---|---|---|---|
| V4-01 | 固定SOUL输入/部署policy；C secretary主提示；原生Main | 完整阅读P、identity及两SOUL；A、自然Idle实际问答 | 通用陪伴、学习与自然交流身份没有强制任务化；未继承Pi的工具权限 | 静态符合；自然样本支持学习/纠正等，倾诉情绪及长期生活效果不作全面行为PASS |
| V4-02 | C secretary身份绑定、History合法路径、原生compact/resume及Notebook选择 | A/B同源机制；main/exam-natural-idle-live.md持久结果 | Main101029/104312、exam102871真实token触发，压缩后Conversation身份仍连续；首Main取证关闭导致abort保留 | 机制及代表链符合；branch/rewind等用既有正式DB受控证据，不声称所有边界均真实模型遍历 |
| V4-03 | C History scope；U core/profiles.ts:36–47、85–103与controller路由 | 静态owner键/异步绑定审查；A/B权限与Profile证据；D跨Profile侧栏AX | stored ID与Profile共同定身份，新建可选、既有owner不迁移；未知/重复owner不猜测 | 符合；UI跨Profile列表不扩大模型权限 |
| V4-04 | 两隔离Profile配置、SOUL与普通user测试前缀；原生模型路由/Idle | load-profile-isolation-repair.md；main/exam-natural-idle-live.md与原始持久证据 | 两边100k/5s自然链实际完成；测试尺度来自user，不改系统时间/模型窗口；旧失败未清除 | 既有范围符合；v4新Provider统一加载须另核，不能用旧加载替代 |
| V4-05 | C notebook_contract与conversation_history；N正文/来源政策 | candidate-source-contract-sync.md；自然模型原文与工具结果 | 结构提供可核来源；真实模型仍有假设归因错误、Search夸大和来源补齐不足 | 结构符合；三类模型反例按PI23保留为不阻塞限制，不称可靠性全通过 |
| V4-06 | C secretary/notebook_render.py:41–145；noting_tools:64/99/168；完成carrier | 亲审全部投影；repair-coverage.md及自然Noting注入 | 完整Notebook保留；模型视图移除snapshot/base/内部coverage，另给可读证据覆盖；无法解析如实不可用 | 符合；旧客户端审计字段仍可保留，不能误当人类UI隐藏要求 |
| V4-07 | C notebook_contract/store/state投影；07/W固定规范 | A/B；candidate-lifecycle-evidence.md；亲审maintain与提交owner | 七类型/引用/版本约束由正式owner；working view合法才commit；年龄责任语义未被新工具改写 | 机制符合；真实模型来源维护失误见V4-05，不以schema成功掩盖 |
| V4-08 | C notebook_contract.py Candidate二选一、noting_tools维护；六步prompt | candidate-source-contract-sync.md 52受控项；candidate-lifecycle-evidence.md 10项/12child | refs/message二选一与目标特化；真实DB/native child受控结果覆盖先源后候选、共享/partial/changed source/unknown | 符合受控契约；模型API结果受控不冒称真实NM维护成功 |
| V4-09 | C persistence proposal/approval政策与完成通知；N创建入口 | A/B、M；旧metadata-live-acceptance失败记录 | 提案不等于批准，工具apply不创造授权；失败/partial/unknown保存真实ID与待处理来源 | 机制符合；实际新获批创建仍待V4-26，旧A失败不修写成通过 |
| V4-10 | C noting_child.py:395–418/674–728；framework_messages.py:257–365 | 亲审事务/锁/通知；B及repair-coverage原证据 | pointer事务成功才通知；通知携snapshot条件，实际append重检；busy/fence排队，过时丢弃；不自动唤醒 | 符合；队列崩溃丢失属于既有非持久通知契约，不擅增可靠消息系统 |
| V4-11 | C noting_tools全部；noting_child.py:630–728；模型工具dispatch | 亲审白名单/finish锁/五Turn；repair-noting-protocol.md 71不同节点 | finish混批拒绝；返回后提交；五Turn与overflow只提交合法状态；错误/中断不伪成功 | 符合机制与真实代表链；受控失败路径和真实自然样本分列 |
| V4-12 | C noting_child冻结prefix/build；noting_runtime联合接缝；run_agent实际调用 | repair-noting-protocol.md；A/B；双自然Idle；固定源码同源 | 父root/tools/历史前缀冻结，新增工具声明只追加；本请求输出上限不回改prefix；退休alias修前即拒 | 符合；不据单样本宣称所有provider cache计费一致，不新增并发合并要求 |
| V4-13 | C获批S01/Q02与Scheduler原生入口 | authorized-prompt-sync.md；quiet-reminder-proposal/probe与PI21 | 24h行为政策恢复；历史无事仍输出反例真实存在；NO_REPLY未实施 | **按用户决定保持待决**，不阻本轮修复，不签静默通过；不得把隐藏气泡当修复 |
| V4-14 | C secretary Scheduler store/claim/ACK；gateway正式deliver | A/B受控并发/重启/ACK；repaired-reminder-live.md；D L09/L10 | 排期独立Notebook；instant空闲恢复、busy走deferred；真实carrier、实际结果、pending/ACK按正式路径 | 机制及代表链符合；旧web-source失败保留，不能按原失败对象重述为全已通过 |
| V4-15 | C tui_gateway/scheduler_host.py:19–187→native_resume→owner | 亲审完整宿主；D L09/L10真实先close Runtime再到期 | 主机发现受管Profile，lease/claim控制；恢复原Conversation，不需浏览器常驻，不抢messaging owner | 符合现有本机链；不等于Linux部署已验 |
| V4-16 | C inflight_output全部、session_history:397/547/570、turn_terminal全部；U session-recovery.ts/terminal-history | 亲审正式write/owner/水位恢复；websocket-backend/state-recovery、F04 DTO；D L09–L12 | 完整snapshot不受ring截断；gap重取有界，失败unknown；真实中途Thinking/工具，Stop后原carrier终态冷恢复，断线再接续 | 符合受控与代表实际链；ring后段gap明确保留，不冒称所有事件全收 |
| V4-17 | U现有组件、Profile/Sidebar、notice/scroll/Pin及增量Running | UI v3→v4逐文件零变化；presentation-baselines与Sidebar两行增量；D原始AX | root隐藏IAB见跨Profile列表、Thinking、Success/Interrupted、完整冷恢复；未见本轮回滚原表现 | 实施差异与已验表现符合；未重新全面操作Pin/拖拽/滚动，不能签所有像素/UIUX全量验收 |
| V4-18 | C native RPC、终态best-effort；U controller恢复/只读Notebook/控制 | A/B兼容与正式handler；亲审可选snapshot与native metadata；D实际Stop | 新字段可选；旧后端降级保留；真实控制有对应结果；展示持久化异常不阻主逻辑；无独立transcript | 符合；Stop/Interrupt/Cancel各语义不能由此次Stop样本一并宣称实际全验 |
| V4-19 | U Files独立scope、core/profiles.ts默认cwd；C profile-aware fs handler | A/B既有Files/owner受控证据；08与当前源码/同源核对 | Files固定default，与聊天owner分开；明确错误不回退启动Profile；不切进程cwd/env | 符合机制及既有证据范围；不新增文件管理能力 |
| V4-20 | C dashboard启动/双SPA与docs/cloud-deployment-sop.md；两产物/反代 | 阅读SOP安装、服务、单后端、token/Origin、Profile、NM步骤；D manifest与HTTP/WS/AX | 本机两个SPA同源单backend，source=desktop；SOP区分Linux待执行/版本配套/真实创建验收，独立工具路径已纳入 | 本机既有拓扑符合；v4统一加载待核；云端/Access/开机生命周期未执行不签通过 |
| V4-21 | N personal_provider.py:55 `_MAINTENANCE`；__init__.py；C批准提示常量 | AST比v3/v4全部模块级字符串；M批准原文；authorized-prompt-sync | 只有_MAINTENANCE变，原段其余文字保留，PI26英文逐字同；注册仅memory provider，Skill删除 | 源码授权符合；实际新root加载待集中包，不能拿文件已安装冒充已注入 |
| V4-22 | C maineligible/noting_trigger_gate/native分支；Scheduler与History独立；N scope | A/B/C3关闭矩阵及亲审；Noting提交再次gate | profile-aware判断；禁用/非eligible不增Noting；History不依赖NM；原生接口/模型路由未被替换 | 机制符合；无Codex App Server旁路，也不扩大原生功能约束 |
| V4-23 | C tools/session_history_tool.py:448–511、合法paths/search | history-long-read.md 23受控项，30006 Unicode；authorized-prompt-sync；真实Search | offset/digest/identity保留，同消息逐页读取；每次合法域校验；partial/truncated明确；不以文件直读绕边界 | 机制符合；实际模型仍会误把截断Search当完整读取，PI23保留 |
| V4-24 | N personal_provider.py:287–442、584；C MemoryManager | 亲审Bundle/Recall/资格；repair-nm-wiring.md；recall-first-read-live.md | Bundle排WM且root缓存由原生owner；prefetch仅ID/title/date；单Provider；child无独立NM；首次陌生内容真实精读546字 | 机制符合；该陌生样本automatic pointer为0、模型自主CLI检索，不宣称pointer驱动精读已验；撤Skill不改CLI机制 |
| V4-25 | N nmem_memory.py全文；personal_cli.py:161–224；README/install | M 11创建项+精确句1项原日志；亲审单POST、连接冻结、stdout/stderr、同ID读回；标准Python隔离执行证据 | stdlib单文件，官方配置/CLI/curl；通用Metadata；唯一POST后CLI+GET核正文/title/labels/Space/metadata；unknown不重试；help/preview零网络 | 受控与安装符合；README更新另审，wrapper仅兼容；真实服务创建由V4-26待核 |
| V4-26 | 模型批准输入→terminal→~/scrips→POST→实际ID GET | M §11/11.1与single-create-handoff只为准备；旧A原失败 | 当前集中交接尚无新实际accepted消息、真实调用/ID/回读链可供本审查判定 | **待核**；新结果不能覆盖旧A NOT PASS，亦不因未收到就判产品失败 |
| V4-27 | N personal_thread_sync.py:84–135/136–189；personal_client.py:144–228 | 全文亲审；T 39项与后Space alias6项（不相加）；真实DB→MemoryManager→正式CLI→loopback | 最长共同prefix按正文/时间/UID；首system说明带真实原生Message ID与祖先Thread；第二条起suffix；纯截断等待新消息；旧Thread不重写 | 代码与受控符合；**真实NM分叉待核**，不用旧暂停观察冒充新fork成功 |
| V4-28 | N thread_sync pending ledger/readonly recovery；provider反馈；C memory_manager:593–664、capture_sync_feedback | 亲审两次BEGIN/先写intent后网络、分页total_messages、ACK、owner通知；T失败/竞争/unknown | 未知先只读同Thread核完整正文/时间，不盲重放；错误Space/ID/分页拒绝；cursor ACK后推进；completed-only；通知为attempt非人类ACK | 机制受控符合；实际远端ACK/冷恢复需随V4-27包核；不宣称全局exactly-once |
| V4-29 | 历史失败与现行PI21/23范围；无新增未来治理模块 | 逐项对照产品原文、用户决定和旧报告 | 静默与三类模型缺陷明确保留；新Metadata/Thread不被PI23豁免；未来跨Conversation协作/全治理不转成本轮开发 | 范围处理符合；长期可靠性、K3表现不据现有样本外推 |
| V4-30 | 本报告过程、固定对象、分层证据 | 本审查仅文件读取/hash/AST比对及报告写入；不运行产品测试/UI/服务/NM/模型 | A/B/C3只同源复用；所有AX/截图归root操作，本人只读；没有重跑100k/600秒/全量 | 方法符合；总门禁待核，不以流程或文档本身扩新增验收开发 |

## 4. 核心目标及验证方法审查

本轮核心目标是以最新产品意图判断真实助手能否持续协作，并关闭已确认实现缺口。代码符合技术规格只是必要证据，不能替代用户实际体验。§2先于实现/旧报告落盘；本审查未根据实现者报告倒推判据。

- 正式接线：检查了Main→History/Notebook、联合Noting→合法提交/通知、宿主→原Conversation→Reminder、正式writer→完整Turn→冷History→UI、MemoryManager→Provider→原生CLI/HTTP。没有用孤立helper存在代替接线。
- 验证层次：同源复用受控正式对象测试，实际模型与root隐藏IAB样本另层核对。T的39项及Space alias修后6项、M的11项+单句1项都是局部证据，不累加成全量总数；测试通过只说明声明范围。Thread测试使用正式CLI到loopback，不等于真实NM。M的普通Python`-I -S`/仓外cwd执行证明独立性，不证明实际模型已使用。
- 反例：历史A Metadata实际失败、主自然Idle首次abort、静默输出、模型归因/Search/source偏差、旧UI恢复失败均保留。后续代码与同源修复证据可以关闭对应机制缺口，不改写原失败事实。UI F04新终态是原消息display metadata，不是第二份对话原文；本次还亲审残余片段、真实UID及best-effort错误边界。
- UI原证据：L10原AX确有Success 1830和Interrupted、冷重新打开后工具参数/实际结果；L12 `root-L12-during-ax.txt:127–139`有当次Thinking和Disconnected，恢复AX保留历史与后续回复。`root-L12-disconnected.png`和restored图片相同，不能把该PNG当断线截图；断线结论依据原AX、响应触发与Caddy记录。L11短窗口不足不能代签L12；L12新UID/seq证明是当次响应。操作者均root，本人没有UI操作。
- 范围：本机运行、安装、加载、源版本、远端实际写入、云部署分别判断。没有把Linux SOP可读当上云完成，也没有把既有v3新root替代v4新Provider加载。所有当前尚未收到的新实际证据保持待核。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| V4-E01 | V4-04/20/21/25 | 新Provider、Thread模块与精确提示源码/安装存在，尚未收到统一实际加载包 | 新旧混版会使真实旅程失去v4归属；总门禁待核 | 集中交实际加载模块路径/hash、两Profile有效配置及新root精确注入事实，绑定v4，不需重复旧大套 | 待核，非已发现产品失败 |
| V4-E02 | V4-26 | M目前准备单条B，旧A失败不变 | 用户指定真实模型创建Metadata不能被loopback或CLI直接创建代替 | 实际批准输入、accepted来源、模型工具调用、唯一POST与真实ID、同ID持久Metadata及资源结算；partial/unknown如实交回、不补写重试 | 待核，阻止全门禁PASS |
| V4-E03 | V4-27/28 | T目前正式对象受控证据，尚无集中交回的真实fork包 | PI24的新行为需要实际NM原生ID/远端结果核实 | 旧Thread/共同末消息原生ID、新Thread第一说明与第二条起suffix、无重发prefix/无旧Thread修改、续接ACK/ledger/冷读事实 | 待核，阻止全门禁PASS |
| V4-L01 | V4-13 | 无事仍有输出历史反例；NO_REPLY未批准 | PI21用户决定保持待决，不阻本轮修复 | 保持原现状与待决标注；不得擅自过滤/改结束语义 | 用户接受的待决限制，非PASS |
| V4-L02 | V4-05/23/29 | 假设归因、截断Search夸大、来源身份补齐不足 | PI23明确三类不阻塞，不豁免V4-E02/E03 | 原反例保留；不为本轮强加K3或未来长期治理开发 | 不阻塞限制，非历史通过 |
| V4-L03 | V4-01/17/20/29 | 情绪长期效果、全量Pin/拖拽像素、Linux/Access、数月可靠性未本次实际覆盖 | 不在本轮已批准实际执行范围，不增开发门禁 | 交付明确未验；未来用户要求时另按真实入口验收 | 范围外/未验，不能宣传通过 |

此次未发现新增确定源码缺陷需要产品修复。该结论仅指当前已审固定对象与证据，不把缺失的真实旅程推定成功。历史发现仍按其版本保留，F01–F04已修机制证据可按本表范围复用。

## 6. 修复与独立复审

本次新审查者从原始要求重建30项全范围判据；先写§2，后读实现/测试/旧报告。仅修改本文件追加段，原历史报告不改。三仓实际源码完整性验证完成，重点新Thread/独立创建工具与上下游接线已独立审完，旧产品代码证据经逐文件同源复用。

**阶段交接：源码和既有证据审查完成，总门禁待核。** 唯一剩余集中交接为V4-E01～E03；收到root/owner完整实际包后只核版本、调用、持久事实与必要原始证据，在本节追加结论，不重提判据、不重跑昂贵测试、不自行启动任何模型/NM/UI/服务。若包内真实结果失败，按实际失败判定，不能借PI23豁免；若只是不充分，则仍待核而非臆造产品失败。

### 6.1 集中补证范围与完整性（同次v4，不重新建立判据）

root交回统一加载与B完整包后，本审查者只读取本地证据，未执行测试、模型、NM、服务或UI。核对`standalone-final-load/result.json`、`standalone-final-source-binding.json`、加载manifest、`metadata-live-acceptance.md`§12、`scenario-b/single-create-manifest.json`及原始批准输入、canonical轨迹、CLI/GET回读、资源收据。加载manifest所列32文件、B manifest所列22文件哈希全部匹配；两Profile各10个安装模块hash均逐一匹配固定v4源码，独立工具源/安装hash均为`256af367007db972d6f9ccf2164794d93ad6327d8942c4ead5d5400d9f3ed1a9`。

此前§3/§5的“尚未收到”是第一阶段事实；本节明确替代V4-E01/E02的当前状态，不改写原观察，也不重提已冻结判据。

### 6.2 v4统一安装、重启及加载边界

`result.json`绑定正确v4主清单，三个产品源drift均空；旧backend32366在两Profile无活动资源时退出，安装后新backend70121以正式`dashboard --isolated --no-open --skip-build`启动，反代仍77413，两个SPA产物manifest保持。五数据库备份integrity为ok；Main旧377条消息/15份root、exam旧316条消息/16份root及身份绑定保留，config/SOUL/policy字节与权限未改；其它旁路服务未被重启。前后活动Runtime、poller、lease、child、pending等均0。

安装模块无网络import确认实际文件路径、Provider类、Thread模块和精确批准句常量；后端在安装之后启动。随后B新Runtime成功执行新独立创建入口，提供真实运行接续证据。**V4-E01的统一安装/重新加载缺证关闭；V4-04/20/21/25相应加载状态更新为已核。** 但无网络import明确没有调用Provider initialize；B prelude只有root哈希和tool schemas，没有完整出站System Prompt。不能据此宣称本审查者已独立逐字查看新批准句的真实wire，也不能因prelude找不到句子推断未加载。当前授权源码逐字核对、实际安装及新进程加载事实成立；此证据边界保持，不自行重建root或启动新模型补抓。

### 6.3 B真实模型创建与独立持久回读（V4-E02关闭）

本审查者对`single-create-actual.txt`与canonical原用户行全文SHA复算一致，唯一accepted UID=`cf10ccf363e04fb39608b873d76ce4ea`，ConversationRef=`conv_ad59cfc5f10b47b48f9bd8e967ac67f7`，Profile=exam-assistant，stored=`20261018_225814_37c851`，runtime=`1e196065`。声明T0为22:57:58.652745，实际accepted为22:58:14，两者未混同。原输入明确批准一个新合成对象、确切正文/标题/唯一标签/Space、单次尝试及专用入口；没有把metadata身份答案预填给模型。

完整canonical共26行、13个工具调用。本审查者核到模型先以`conversation_history(search)`返回真实来源身份，再读独立入口help、写本次正文与Metadata文件、一次preview、**一次含--apply的实际terminal调用**。search匹配正文片段truncated=true，但准确身份完整，且完整批准原文已在当前user上下文可见；不能把这次search称为完整History Read。apply对应真实tool result包含ID `64b1f9a0-369e-43ec-b464-d58edc3d39ff`、complete/confirmed/readback_confirmed/EXIT=0。后续错误的顶层--space经help改为合法只读show，未形成第二次创建。

另行保存的官方CLI与GET不是helper回显。本审查者逐字核GET中的正文、标题、Space=`space`、`label_ids=["label_notebook:situation"]`及CLI唯一`labels=["notebook:situation"]`，均匹配原批准对象；GET真实`metadata.hermes_provenance`精确为version1和上述Ref/UID单条来源。服务端自己的额外Metadata保留，没有覆盖或补写。由此**V4-26所要求的真实模型入口创建及精确来源Metadata落库通过，V4-E02关闭。** 旧A ID及旧partial失败不变，新B不代修/代签旧对象。

B自有Thread本地正式ACK为2、pending=null、UID与canonical用户/最终assistant一致；本包没有另GET远端Thread内容，不把该收据扩大为分叉实测。最终只读资源audit为active/lease/child/schedule/pending均0、26行History保留。observer准备close前发现原owner已消失而停止，实际session.close调用0；不编造“close成功”或猜回收原因。

证据限制：初始event ring截断，单次POST判断来自唯一持久apply和固定已审单POST实现，不是全程网络抓包或硬拦任意shell。root唯一发送/操纵隐藏IAB，观察者仅获准只读GET，本审查者仅本地文件复核。用户明确点名入口，故这是专用入口功能通过，不代签自然发现/自然路由、全提案流程、100k/Noting或长期质量。

### 6.4 A真实Thread底层结果与新UI矛盾分层

本次仅先读`nm-thread-fork/live-after-fork.json`及root的`root-A-edit-final-ax.txt`、`root-A-edit-cold-ax.txt`。前者报告22项真实核对全部true：新Thread=`hermes-personal-conv_08b0e53da01a40248939441b528142d5-fork-964a21a3ee504182a4b65436f9e2cffb`，共同末消息原生ID=`msgocc_80c75a165bd45ad9517d9a433a9f68e6`；首system说明含前Thread/原生anchor，remote_count=3、逻辑count=6、后两条为编辑用户/新assistant；旧Thread身份、消息ID/hash保持、共同4条不重发、ACK匹配/pending清零。

这些是owner阶段汇总，完整实际包尚待其集中交回，本审查者不单凭22个true替代原始远端与canonical复核。更重要的是，root发现同页和reload冷页仍有旧第3批准及旧assistant，随后又显示新用户/assistant：两份AX均在172行显示旧“我明确批准”段、217行旧创建回复、223行新“不批准任何新的Memory”段，页面事实可复核。依据V4-02/16/18，这涉及编辑/rewind后当前合法History与用户所见的对应关系，**不能因Thread底层正确而签整体通过**。

新增记录 **V4-E04：A edit/rewind后页面保留旧分支内容的矛盾，待根因及影响范围**。当前不猜是canonical、native History RPC、UI投影或其它状态问题，也不以reload后的现象归咎纯缓存。root已委派原本地owner只读调查，本审查者不并行改代码或重跑UI。关闭至少需解释实际编辑目标/分支身份、canonical与用户API/页面的对应关系；若确为实现偏离，须相应修复与针对性同源证据，不能用旧Thread不可修改这一独立契约合理化当前页面混入旧分支。

### 6.5 更新后的交接结论

**统一加载与B创建已核；整体Verification仍待核，不签PASS。** V4-E01统一加载缺口、V4-E02真实Metadata创建缺口关闭，精确wire未捕获边界保留；V4-E03等待A完整真实包，V4-E04等待新页面矛盾的根因/影响/必要修复证据。PI21静默待决和PI23三类模型偏差仍按用户决定不阻塞，不能豁免E04。此处尚未断言新代码根因，只记录实际页面反证与总门禁限制。

### 6.6 B实际请求root的精确批准句（只读持久证据关闭边界）

遵root明确授权，本审查者以SQLite URI `mode=ro`且`PRAGMA query_only=ON`只读exam-assistant的既有state.db；只输出身份、boolean、hash，不泄露提示正文。未调用Provider initialize、模型、NM、服务或UI，也未修改Prompt/重建root。

关联链为同一个真实B：`secretary_session_bindings`将stored/session `20261018_225814_37c851`绑定`conv_ad59cfc5f10b47b48f9bd8e967ac67f7`；其`sessions.system_prompt_hash`、`secretary_context_preludes.root_prompt_hash`、`native_root_prompt_hash`均为`9c22404dbb1ceed6d3d224b7fca5da9218ae44b5fe8773c594e640e711314080`，prelude source为`provider_neutral_request`。这个hash也与B封存的`single-create-parent-snapshot-private.json`原prelude一致，不靠“当前最新”猜对象。

按该hash查`system_prompts`得到对应实际正文；本审查者重新计算SHA256与键完全相等，精确批准英文存在=true、出现次数=1。单句去尾换行SHA256为`15a1826ced26f02092aceef8f76adc24db12e0589bb60b630ea07c6f13d075fe`；批准句原文件含末尾换行，其字节SHA为原记录`305013a4f407938897a0e1f0acc50daa5f2e1ddf2973537126ccfacdd49ae6a7`，二者差异仅来自末尾换行，不是改词。Session内联system_prompt为空是原生hash存储，不解释为未注入。

同时只读固定v4 `agent/conversation_loop.py:509–527`与`secretary/noting_runtime.py:245–262`确认该prelude来自正式provider调用前最终request中的root/tools，而不是安装时import或测试自造提示。因此**V4-21实际B模型请求root精确句证据已补齐**，替代§6.2当时“未捕获正文”的缺证边界；不声称取得网络报文，也不把该单B请求扩大为所有Profile/所有旧root逐个已核。现有证据足够，无需额外模型调用或Prompt取证动作。

### 6.7 A完整真实分叉包独立核验（V4-E03关闭）

已读`nm-thread-fork/implementation.md`§9–9.1及`live-manifest.json`，对baseline/after/delivery去重后21文件逐项重算SHA，全部匹配。独立读取before远端全文/精确anchor、after新旧远端、canonical/cleaned/selected_uids、实际thread_sync收据和root编辑输入，未仅采信22个true。

本审查者重算核对成立：旧Thread仍6条，全部原生ID/role/content/timestamp与编辑前逐字相同；offset3 anchor与全文第4条是同一原生消息；新Thread ID取正式ledger，Space正确，总数3且角色严格为system/user/assistant；system说明含旧Thread和真实共同末消息ID；新user逐字等于root实际编辑输入；新后两条role/content/timestamp等于当前合法cleaned尾两条；前4条与旧共同前缀相同但未上传到新Thread；logical6、remote3、locators为旧0..3加新1..2，selected_uids与ledger相同，pending=null。

故**V4-27首次真实分叉和V4-28本次正常ACK路径通过，V4-E03关闭**。真实窗口从完成ACK后开始，未捕获pending瞬间；不推称丢ACK/上传崩溃/冷进程重启已真实验证。root明确不再增加ordinary，后续增量及异常复用已审受控证据，未把未执行写成通过。A资源收尾由root保留控制，本包未close，不声称A资源0；observer只读旧A三次/新A一次，没有Memory写入或代发编辑。

### 6.8 E04正式出口偏差已确认，整体仍不能通过

独立读取`live-history-rest-check.private.json`：当前canonical原始投影16行（含工具/脚手架），Provider合法清洗6条；正式REST响应23行。旧批准UID`721770c422184e8c83a9e34f8dbeb5c1`和旧assistant UID`610a920baba04bde8601d73b851ad60d`在canonical出现次数均0，但在REST各出现一次，均`active=0/compacted=1`；新user `3c85721aeb88453083afae70e970b453`、assistant `f09046c2488e48dfb6f42983e4461a07`在canonical各一次，REST为`active=1/compacted=0`。REST目标owner/session与A一致，query含`include_compacted=true`。此证据与root warm/cold AX共同证明退休旧分支混入用户实际展示，**并非仅有root口头观察或仅缓存推测**。

本次只确认正式出口偏差，不提前代替local_deployment_browser_validation的根因调查：合法压缩旧消息与rewind退休消息如何区分、正式REST/前端应该在哪里改，仍须其完整包。V4-02/16/18不能继续用本轮此前未覆盖此反例的“机制符合”概括当前编辑回退体验；这三项对此路径的状态更新为不符合，E04为当前阻断。PI23不含这类确定History出口偏差，不能豁免；NM旧Thread保持与当前页面应对应合法分支是两项不同契约。

当前收口：**E01/E02/E03已关闭；批准句实际B请求root已证；E04未关闭，整体Verification不能PASS。** 等待已委派owner交根因/必要修复、版本绑定与针对性受控/实际证据；本审查不重新审全套、不重跑既有测试或执行任何产品动作。此前§6.5“E03待包/批准句缺完整正文”是当时事实，由本节窄补证更新。


# v5 全新独立 Verification（2026-10-18，Astra/high）

## 1. 审查对象与结论概览

**最终补证复审：Verification PASS（固定v5、本轮已批准范围）。V5-E04与V5-ELOAD已由下文§6.1关闭；此前“待补证”保留为阶段历史。独立Validation仍须另行判定，PI21/PI23及长期/上云未验边界不变。**

判据阶段：仅读取两项Skill、snapshot-index产品权威与PI01–26、产品原文、身份参考与两SOUL全文。未读取代码、测试、动态CLAUDE及历史报告。待审v5 snapshot-set SHA256 `272fbb072da400fe5119b87bbd742e366e3e2a6ab806e211554ebaa941f00c2a`。总体结论待调查；不预签最终加载及冷UI项。

## 2. 独立要求清单与覆盖

建立于实现调查之前。依据产品原文2026-10-18及PI01–26；以下初版保留，不以实现调整。身份参考只取风格，旧Pi调度/写权无效。当前要求与长期观察分离，PI21待决、PI23三类已确认不阻塞不能扩豁免。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| V5-01 | 产品§1、3、11；身份参考；两SOUL | 身份/当前 | 完整生活、自然交流有自身价值，不强迫任务化；身份参考不继承Pi权限 | 部署SOUL无测试角色/时间尺度，答疑直接回应、事务委派遵守PI13 | §3同号 |
| V5-02 | 产品§3.1、3.2、9 | 长期空间/当前 | Conversation持续，Session技术生命周期不迫使用户重开；允许多个空间 | 轮转、压缩、branch、rewind维持真实归属和连续历史 | §3同号 |
| V5-03 | 产品§3.3、9；PI01、10 | 身份隔离/当前 | 同Profile可互搜；跨Profile不由History实现 | History按Profile归属；主助手只由NM读取考研Space | §3同号 |
| V5-04 | 产品§4.1、5、7 | 记忆连续性/当前基础 | Notebook派生、原文可恢复；不能把摘要当原始事实 | 压缩交接+Notebook+History正式接线，覆盖区间和来源可核验 | §3同号 |
| V5-05 | 产品§4.2、6 | 责任连续性/当前 | 真实接受的责任持续；保留原因/状态/阻塞/下一步，不创造任务 | Notebook组织与Noting责任维护、重启/并发/失败不丢已接受责任 | §3同号 |
| V5-06 | 产品§4.3、6；PI13、21 | Reminder/当前与待决 | 未来24h Instant为行为约定不是代码强制；没有内容静默是目标但PI21保持现状 | 检查Prompt及Reminder正式唤醒；NO_REPLY新协议不实施，静默失败不伪报通过 | §3同号 |
| V5-07 | 产品§5；PI08、15 | 事实/候选交付 | 建议≠批准；来源覆盖成功后结算，未覆盖责任/纠正/依赖不丢 | Candidate仅Notebook或Message一种来源，Notebook型特化简述；真实写结果决定关闭 | §3同号 |
| V5-08 | 产品§7、9、10；PI02、23 | 实测与边界 | 上线前真实模型证据不等长期可靠；指定三模型偏差保留但不阻塞 | 区分模型/机制失败，确切记录豁免，不扩到Metadata或其它未验 | §3同号 |
| V5-09 | PI01、02、03 | 实测配置 | 两真实Profile、真实NM/插件；普通user前置测试说明；10分钟一天不改时钟 | 实际配置和原始输入支持测试范围，SOUL可部署 | §3同号 |
| V5-10 | PI04 | 联合压缩/当前 | 两个Profile Noting+Idle Compact同开，100000tokens/5秒，仅调触发 | 真实联合运行阈值及容量原生；触发、冻结、提交、恢复机制有效 | §3同号 |
| V5-11 | PI05、09 | Prompt可见对象 | 内部Snapshot ID/Pointer/Coverage anchor不能进入Hermes模型正文，非仅UI隐藏 | 真实构建Prompt和Notebook工具输出清理；保留有意义覆盖与可操作来源身份 | §3同号 |
| V5-12 | PI06 | Profile UI | 首页独立选择新Session原生环境，旧Conversation归属不变；侧栏跨Profile | 固定前端图标映射，不混model selector、不过滤掉别Profile | §3同号 |
| V5-13 | PI07、19 | UIUX | 流式首Thinking、工具卡稳定、准确完成高亮，5秒普通/手关错误；保护用户表现层 | 连接/恢复不回滚布局动画Pin拖拽滚动；冷统计用可信值估算 | §3同号 |
| V5-14 | PI08、14、22、26 | NM Memory创建 | 批准具体内容目标；窄入口一次创建正文及Metadata、复用连接；其它官方CLI | 实际模型调用与回读Metadata，partial/unknown先核实、不盲重试；无Skill竞争 | §3同号 |
| V5-15 | PI10 | 原生/API兼容 | 关闭Secretary/非eligible零变化；沿原生Profile/模型/provider和API默认语义 | 正式分支接缝、可选参数兼容、失败不阻断主逻辑 | §3同号 |
| V5-16 | PI11、12 | 执行限制 | 只有隐藏IAB允许UI，绝不改屏幕/焦点 | 只核操作者原件且明确非本审查者亲操，无外部浏览器代验 | §3同号 |
| V5-17 | PI13、09、22、26 | Prompt授权 | 仅精确获批文字及History配套；框架Prompt不得无限调优 | 对照精确文本；Provider仅批准短句替换，保留其余，清除旧Skill | §3同号 |
| V5-18 | PI16 | 部署拓扑 | 独立Secretary Web和原生Dashboard同域同后端，本地反代实际URL；非Electron | 反代入口、路由、WS、原生Dashboard原件；Access云端未验明示 | §3同号 |
| V5-19 | PI17、18 | 全来源实时状态 | Web触发与否均可订阅真实执行；静默不抹除事件 | 实时、中途接入、完成恢复独立证据；完整Timeline不可用ring替代 | §3同号 |
| V5-20 | PI20 | 交付SOP | 可执行上云步骤、版本产物、事实与未验区分 | 固定版本SOP覆盖真实部署且不冒称上云完成 | §3同号 |
| V5-21 | PI24 | NM Thread同步分叉 | 已同步History不一致创建新Thread，保留旧；第一条引用原Thread+共同NM原生Message ID，第二条始增量 | 不重复相同前缀，不拿Hermes UID代替；失败不污染关联，真实分叉回读 | §3同号 |
| V5-22 | PI25、26 | 独立工具 | ~/scrips/nmem-memory.py无需Hermes安装/HOME/cwd/模块；官方NM配置，内容及metadata来自调用方 | 独立部署产物、无隐式状态读取；批准英文一致且真实Memory元数据落库 | §3同号 |
| V5-23 | 产品§3.3、5、9、12 | 未来范围 | 正式跨Conversation协作/跨Profile共享治理/完整决策演化为未来 | 不虚称已有，不强加首版全部实现；当前明确授权机制仍须完成 | §3同号 |
| V5-24 | 产品§4、5、7；PI10 | 数据生命周期/必要推导 | 连续性须正确处理rewind/branch/新旧Session、事务提交、重启并发和关闭 | History与持久身份为源，Notebook原子性与独占写权、失败回退不制造历史 | §3同号 |
| V5-25 | PI17、18、24；产品§5 | 历史展示/必要推导 | 显示与同步必须共同遵循有效分支和真实消息；恢复不能混旧前缀/截断窗口 | 分页、rewind/branch、工具/Thinking状态与正式持久历史一致，兼容旧调用 | §3同号 |

## 3. 逐条实现证据

本节路径约定：`S/`指`.hermes-dev/product-intent-review-20261018/delivery-snapshot-v5/`；`C/`、`U/`、`P/`分别指其`hermes-secretary/`、`hermes-secretary-web/`、`hermes-nmem-provider/`；`E/`指`.hermes-dev/product-intent-review-20261018/`。源码只读取固定S，不把moving工作区产品文件作为v5实现。旧报告仅定位；实际原件及精确差异另核。以下“符合”均受证据边界约束，不等同长期产品已验证。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| V5-01 | C的SOUL部署材料、`agent/secretary_prompt.py`与P Provider prelude | 对照产品/身份参考、两部署SOUL及清除测试专属身份前后原件；通常交流未被结构层强制改成事务 | E/`deployable-soul-policy.md`、`soul-policy-evidence/`、`authorized-prompt-sync.md` | 符合本轮身份及授权边界 | 真实样本不能证明长期自然交流质量；不继承身份参考旧Pi写权限 |
| V5-02 | C/`hermes_state_secretary_identity.py`、`hermes_state_messages.py`、`hermes_state_secretary_notebook.py:279` | Session与Conversation绑定、压缩祖先、显式fork、rewind路径；重新核v5按UID最新代次先判有效性再分页/去重 | E/`history-rewind-display-fix/implementation.patch`、`result.json`、reader/native日志 | 机制符合；原A最终显示留V5-25补证 | 没有对生产历史做迁移；本轮运行库为可重建测试状态 |
| V5-03 | C/`hermes_state_conversation_history.py:59–127,139–204`、`tools/session_history_tool.py`；P/`personal_provider.py` | 只接受宿主DB、Main或已绑定running Noting；Noting固定父Conversation；同Profile显式cross；NM空间配置继承 | E/`repair-nm-wiring.md`、`repair-kernel-profile-scratch.md`、`history-long-read.md`及绑定证据 | 符合：模型不能以参数选择其它Profile DB，子任务不能扩scope | NM授权为本轮明确两Profile/Space关系，不推广为任意跨Profile共享 |
| V5-04 | C/`secretary/noting_surface.py`、`notebook_render.py`、`tools/session_history_tool.py:395–520`、`hermes_state_conversation_history.py:76–87` | Main History资格、压缩恢复footer和可读覆盖；Search切片不改写，Read按原文分页、digest/截断明示，同一读事务固定候选与路径 | E/`history-long-read.md`、`recall-first-read-live.md`、`repair-coverage.md` | 机制符合；Search未Read等真实偏差按PI23记录 | 不把Search摘要作为已读原文；不把PI23扩为历史真实性免责 |
| V5-05 | C/`secretary/notebook_store.py`、`noting_tools.py`、`noting_child.py:590–750`、`framework_messages.py:250–370` | Main只读、Noting编辑完整Scratch并提交；退出/取消不提交；有效晚到Snapshot保留但不倒退pointer；完成通知在宿主边界发布 | E/`candidate-lifecycle-evidence.md`、`repair-noting-protocol.md`、`repair-coverage.md` | 当前责任连续基础符合 | 责任质量的长期观察未完成，不能由一次Notebook写入证明 |
| V5-06 | C/`agent/secretary_prompt.py`、`tools/secretary_dispatch.py`、`tui_gateway/scheduler_host.py` | Reminder沿既有调度/owner唤醒，Instant24h为已批准政策；无新增代码时间硬阈值或未经批准NO_REPLY协议 | E/`repaired-reminder-live.md`、`quiet-reminder-contract-probe.md`、PI21 | 当前实现按用户选择保留；静默目标明确未解决 | PI21为待决并非通过静默验收；不能外推其它失败均不阻塞 |
| V5-07 | C/`secretary/notebook_store.py`、`notebook_contract.py`、`noting_tools.py`、`noting_prompts.py` | Candidate Notebook/Message XOR及Notebook简述特化；先源后Candidate、partial/unknown纠正、实际写入结算；工具拒绝边界与生命周期原件 | E/`candidate-source-contract-sync.md`、`candidate-source-contract-green.xml`、`candidate-lifecycle-evidence.md`、traces | 符合现行PI15及生命周期契约 | 受控provider样本是机制证据，不冒称自然模型全链质量 |
| V5-08 | C正式Main/Noting路径与P真实NM调用 | 区分真实运行、受控验证和失败；保留Search未Read、既有三类模型偏差与实际失败记录 | E/`main-natural-idle-live.md`、`exam-natural-idle-live.md`、`metadata-live-acceptance.md` | 本轮有限真实样本要求满足；长期观察未证 | 仅PI23所列偏差不阻塞；Metadata及History显示没有借用豁免 |
| V5-09 | 两Profile部署配置、SOUL及P安装文件 | 原始普通user测试前缀、真实Profile/NM、压缩触发配置；时钟未改，10分钟一天是样本说明 | E/`soul-policy-evidence/`、natural-idle原件、`standalone-final-load/result.json` | 符合本轮配置及样本边界 | v4个人产物与v5逐文件同源；v5新backend实际装载另列 |
| V5-10 | C/`secretary/noting_runtime.py:453–525,564–617`、`noting_timers.py`、`agent/context_compaction_request.py` | 真实Main101029、exam102871tokens，约5.026/5.025秒；原生usage/容量，先冻结派发、父独立压缩；任意Noting拒绝不取消native callback | E/`main-natural-idle-live.md`、`exam-natural-idle-live.md`、`repair-kernel-profile-scratch.md` | 联合机制及两Profile真实运行符合 | Main首驱动过早关闭abort及授权续跑保留，非首次无故障；未重复100k/600秒 |
| V5-11 | C/`secretary/notebook_render.py`、`noting_tools.py`、`noting_surface.py`、`framework_messages.py` | 重新逐段审模型正文渲染与公开工具响应：完整Notebook+有意义覆盖，无内部snapshot/pointer/anchor；操作entry_id和History message_uid仍保留 | E/`repair-coverage.md`、framework/projection定向日志、`noting-protocol-targeted.log` | 符合模型可见边界 | API审计元数据不是模型正文；不把UI隐藏误认实现要求 |
| V5-12 | U/`src/core/profiles.ts`、`components/ChatSelectors.tsx`、conversation controller | Profile独立于model；仅new时选择环境；旧owner保留；全局侧栏用(profile,id)身份 | E/`local-deployment-browser-validation.md`及root AX原件 | 符合静态接线与已有实际样本 | U的163文件与v4完全同源，overlay逐hash保护；本审查无UI亲操 |
| V5-13 | U/`session-recovery.ts`、timeline projection/controller；C/`tui_gateway/inflight_output.py`、`turn_terminal.py` | 首Thinking/tool时间线依write seq聚合；terminal写原source row；普通与错误notice不同生命周期；实际L10冷AX包含Thinking与Interrupted工具卡 | E/`local-deployment-evidence/root-L10-cold-interrupted-ax.txt`、`websocket-state-recovery.md`、`cold-estimate-assertion-sync.md` | 所列呈现与恢复机制符合 | 不声称逐像素/每个Pin拖拽手势本次再验；真实原A退休尾残留转V5-25 |
| V5-14 | P/`nmem_memory.py`、`personal_client.py`、`personal_provider.py`，独立部署脚本 | 核B26条持久消息/13工具调用，只有1次--apply；批准正文=actual输入；单次创建结果与独立GET的id/title/content/space、label、provenance一致 | E/`metadata-live-evidence/scenario-b/single-create-manifest.json`及其raw/GET/POST-close原件；本次`independent-verification-v5/live-original-crosscheck.json` | 符合真实一次创建含metadata和批准边界 | B是明确指令入口功能样本，非自然路由；旧A/partial不由本次擅改；unknown不得重试 |
| V5-15 | C/`secretary/noting_runtime.py:99–123,145–172,564–617`、`noting_surface.py`及既有native调用缝 | 关闭/不eligible不进入新写路径；模型/provider仍原生；新增参数默认兼容；v5只改读取，不改writer/schema/API签名 | E/`history-rewind-display-fix/result.json`、native seams原始日志；noting-disabled回归 | 所列正式兼容边界符合 | 同源差异复用局部证据，不据此宣称Hermes全量测试全绿 |
| V5-16 | root的UI取证记录及本审查行为 | 只核root hidden IAB AX/保存原件；本审查仅文件读取/hash/静态分析/报告写入，无UI/网络/服务操作 | E/`browser-capability.md`、root-L10/L12 AX、`independent-verification-v5/` | 符合本审查执行限制 | UI操作者root，不能将其执行写为审查者亲操 |
| V5-17 | C/`agent/secretary_prompt.py`、History guidance；P/`personal_provider.py`批准句 | 对照PI13/26精确文本及旧Skill清理；Provider根句限定批准Memory创建；已取B真实provider-neutral request root hash绑定 | E/`authorized-prompt-sync.md`、`metadata-live-acceptance.md`§12、`standalone-final-load/result.json` | 符合授权文本和已证B请求范围 | 继承旧B真实root审查证据，不声称本次读取未提供的网络wire payload |
| V5-18 | C Dashboard独立host、部署Caddy路由及U产物 | 本地双SPA/同域53448/同backend53446，WS/原生Dashboard原件；v4到v5前端/个人产物不变 | E/`local-deployment-browser-validation.md`、`local-deployment-evidence/`、`standalone-final-load/result.json` | 拓扑与既有运行符合；v5最终加载待闭环 | 本轮没有Cloudflare Access真实上云验收；不冒称公网完成 |
| V5-19 | C/`tui_gateway/{scheduler_host,inflight_output,turn_terminal}.py`；U/`session-recovery.ts`与projection | 非Web来源可投递/订阅；snapshot+seq/epoch，buffer后接入，gap重新同步；L10真实中途冷接入、L12真实在途断线恢复与terminal来源行 | E/`local-deployment-evidence/`20项manifest原件hash全符；L12真实reasoning2118晚于baseline2112；本次`deployment-original-crosscheck.json` | 所列实时/中途/完成恢复符合 | L12只重启Caddy一次，非backend崩溃；断线PNG重复，断线依据AX+events而非PNG |
| V5-20 | C/`docs/`云端SOP及本地隔离部署入口 | 检查双SPA、单backend、反代、Access准备、环境/权限与回滚步骤；版本固定与实际加载分开 | C/README稳定索引；云部署SOP；E/`standalone-final-load-plan.md`、v5加载原件（未完成） | 操作SOP具备；最终版本实际加载登记待主会话收口 | 版本产物更新属于交付闭环，不以过渡文档宣称最终运行版本已确认 |
| V5-21 | P/`personal_thread_sync.py`、`personal_provider.py`的export/receipt链 | 独立比较A old6不变、新3(system/user/assistant)，header原Thread+old[3]原生anchor，new两条精确等于cleaned增量，不复传4条相同前缀 | E/`nm-thread-fork/live-manifest.json`、`implementation.md`§9及远端原件；本次`live-original-crosscheck.json` | 符合真实分叉机制；远端与本地receipt绑定一致 | 网络失败/后续增量仅受控部分不冒称真实网络故障；History UI另验 |
| V5-22 | P/`nmem_memory.py`与部署`~/scrips/nmem-memory.py` | 源码无Hermes状态/模块依赖，官方NM连接配置、调用方输入metadata；v4正式安装helper SHA与v5相等 | E/`standalone-final-source-binding.json`、`metadata-live-evidence/standalone-helper/manifest.json`、B实际调用 | 符合独立产物与PI26批准入口 | 根目录按用户拼写scrips，不扩为迁移其它脚本/全局配置 |
| V5-23 | 产品§3.3/5/9/12与PI范围 | 独立判据先区分未来跨Conversation治理与当前明确机制；不将已确认NM同步/metadata归未来 | 本报告§2初版；snapshot-index PI01–26 | 当前范围界定符合 | 长期责任/决策演化无长期实证；不因核心可用便声称愿景全部落实 |
| V5-24 | C/`hermes_state_secretary_notebook.py:166–300`、`noting_child.py:590–750`、`framework_messages.py:250–370` | 同事务验证anchor在现行Foreground、完整校验/插入/按覆盖选择pointer；晚到不倒退，branch只继承合法anchor；C8当前pointer在durable append同事务重核 | E/`repair-coverage.md`、`candidate-lifecycle-evidence.md`、`repair-noting-protocol.md`及同源证据 | 原子性、独占写权与失败路径符合所审范围 | 只读入口不偷偷重选pointer；不以孤立helper代替宿主锁和事务正式接线 |
| V5-25 | C/`hermes_state_messages.py`indexed/legacy/native读取；U controller refreshHistory/projection merge | v5在分页及总数之前查同UID最新代次；读取包括退休行以判定但不返回退休有效尾；explicit audit保留；8修前反例、70不同节点修后证据 | E/`history-rewind-display-fix/{implementation.patch,result.json}`及logs；原A旧REST/冷AX | 源码及受控修复符合；最终实际E04仍待v5加载后原A正式REST+冷AX核对 | 不允许仅用新Conversation、NM远端正确或受控测试代签原A冷显示 |

## 4. 核心目标及验证方法审查

审查采用先产品判据、后固定实现、再原始证据的顺序。上述25项覆盖本轮产品身份、长期空间、记忆/责任连续、Reminder、Candidate、双Profile、联合压缩、Prompt、UI、NM、部署、兼容及未来边界，并非只围绕E04旧缺陷复审。工程规格接受产品判据审查：白板旧示意中的混合来源及内部标识说明，不能覆盖PI15的XOR和PI05的模型可见对象边界；07旧轮次“尚未实施/后置”的状态也不能当本轮范围。实现核对按明确用户口径及最新正式契约。

**版本与复用。** 本次独立逐文件hash校验v5三目录：core18202、UI163、personal703，均与各manifest一致；符号链接按链接内容核验、不跟随到moving工作区。相对v4：core仅7个文件变化，其中产品代码仅`hermes_state_messages.py`，另有该reader测试、CLAUDE及轮次报告；UI0变化；personal仅CLAUDE。对旧测试来源映射以其`expected`源hash重新比对：ad4可定位68项中40同源/28变化，v2为42/42同源，v3为5/7同源，另2项personal分叉代码及测试由后续真实A/定向证据替代。旧ad4变化不能整包默认为同源；本次仅复用未受影响路径和后续替换证据。完整结果见`E/independent-verification-v5/{source-integrity,evidence-source-reuse}.json`。

**不把测试数量作为充分证明。** E04的8个RED是实际SessionDB压缩+rewind后的旧user-3残留断言；随后reader59P/2F原日志保留，2F为使用带持久内部字段fixture的restore调用，经改fresh输入定向2P，native seams9P；去重70节点为47既有+14新增+9接缝，不把多轮日志相加。index/legacy分页、count、resume、祖先和显式audit均静态核对；受控证据仍不能替代原A实际REST/冷页面。没有重跑100k、600秒、大型套或模型。

**真实原件与测量局限。** A旧远端6条不变、新3条header及增量与canonical逐项比对；B26条持久message中13工具调用、唯一创建命令及GET元数据逐字段比对，相关原件hash无偏差；local deployment20项原件hash无偏差。L12的两个截图字节相同，不能据此证明断线视觉，实际断线/恢复证据取AX、seq及新reasoning；只证实Caddy重启，不写成backend崩溃。复用UI是操作者root的隐藏IAB原件，本审查未亲操。

**既有不绿与当前覆盖分开。** 历史完整Python为59466P、321F、71E、1421skip及1timeout，不能改写成全绿；本轮既有10类检查中health失败经定向修复/复核，UI696P/3F/1skip中的3F及新增相关项有后续定向关闭。这里不依据总数签发全仓质量保证，采用本轮冻结范围、同源证据及失败分层。PI21静默保留现状、PI23三模型偏差、未来愿景/长期观察、云端Access未验均显式保留。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| V5-E04 | V5-02/25；C/`hermes_state_messages.py` | 原A rewind已退休旧user/assistant在旧REST及冷AX仍出现；v5源码改为先判最新UID代次，再筛选/分页 | 核心历史真实性，不能以PI23、NM远端正确或受控测试豁免 | v5实际backend版本绑定；原A正式REST和零模型冷IAB AX显示新输入/输出且无两个旧UID/旧正文；资源关闭及保留事实 | 源码/受控修复已核；实际加载/冷页面最终包待核，当前阻断最终PASS |
| V5-ELOAD | V5-18/20/25；v5加载交付 | 已见`load-v5/backend-started.json`新PID8471及旧PID退出，但`resume-error.json`仍为AssertionError且no_automatic_retry；无最终result/manifest，不能从启动记录推断成功 | 最终实际运行版本及状态保留证据未闭环；属于交付证据缺口，不自行认定新产品代码缺陷 | 提交一次完整加载最终包：source hash/命令/PID、旧状态与配置保护、原A REST、资源终态、root冷AX；失败原件保留并解释 | 等主会话取证；本审查不启动或修服务 |
| V5-L01 | V5-06；PI21 | 无内容静默协议仍待用户决定，当前保留 | 用户明确暂不新增NO_REPLY；不以待决阻塞本轮其它已批准机制 | 保留待决与真实偏差，后续用户决定再收敛 | 当前有界非阻断；不写静默通过 |
| V5-L02 | V5-08；PI23 | 三类指定模型偏差有真实失败样本 | 明确用户不阻塞仅限所列情形，不能推广 | 持续记录真实样本，长期行为另行观察 | 有界非阻断 |
| V5-L03 | V5-01/05/18/23 | 长期责任演化、所有未来治理、真实Cloudflare Access及跨平台未完成实测 | 超出本轮已授权实际验收，禁止虚报完成 | 最终交付列清未验，后续独立任务补证 | 范围/证据边界，不要求本轮擅自扩实现 |

除V5-E04实际关闭与V5-ELOAD最终包外，本轮固定v5全范围静态及所列原件审查未发现新的确定性阻断产品缺陷。此结论不等于“所有代码不存在缺陷”。

## 6. 修复与独立复审

v5源码完整集及manifest已独立核验：snapshot-set SHA256 `272fbb072da400fe5119b87bbd742e366e3e2a6ab806e211554ebaa941f00c2a`；core提交`0dc4232f597f0c36d070fd5eabd578366436fca3`，UI提交`652f487a536874e0405fae547941be36950cc144`加受保护overlay，personal提交`3732f5503eccc0c97df0ea0238b140b9997e69df`。manifest hashes分别`3c22055938139687ee40d77ce416938564b7b98c43252362e3ea6becc0fb2a40`、`d43fb844a31a20c0b088162ff5c32e14b2529f69f19996f5cae3adc5ecf8158b`、`837f8a90f5578c3e315ff5e392da420293453ead977338519dd78e2a86d0c2cb`。

本次记录没有覆盖历史结论或修改初版判据。仅独立审查证据写入`E/independent-verification-v5/`；无产品代码/测试/其它报告修改，无测试执行、模型调用、NM操作、网络、服务或UI操作。

**当前总体判定：待补证，不能签发PASS。** 已完成固定v5全范围源码/产品判据核对、E04修复静态审查与定向原件核验；剩余集中核查只需要V5-E04/V5-ELOAD完整实际包，不需要再重跑全范围审查、大型套或真实长模型。若最终包证明加载/原A冷显示及状态终态满足，可在本节追加限定复审关闭；若实际仍失败，保持阻断并给出原件定位。通过后由另一个全新独立Validation审查者判断实际产品入口的最终验收，不由本Verification替代。


### 6.1 最终v5加载、原A冷显示与关闭资源的集中补证复审

本次仅核上一阶段集中待核的V5-E04与V5-ELOAD，不重提判据、不重跑全范围审查或测试。读取本地保存原件、固定v5源码及离线PNG，未执行产品、UI、网络、模型、NM、服务或测试操作。root仍为隐藏IAB实际操作者；本审查者只阅读其完整AX并查看已保存PNG。

| 问题编号 | 补证版本与原件 | 独立核对方法 | 实际结果 | 剩余边界 | 复审结论 |
|---|---|---|---|---|---|
| V5-ELOAD | `E/history-rewind-display-fix/load-v5/result.json` SHA `0c576016ba49dfe33378e28b98e8ad62feaf7b53d8819fe6cbe29599c3f17b11`，同目录manifest、restart脚本、原错误、cache解释及postload原件 | manifest52项逐文件hash；固定v5 reader源码SHA与实际fresh import指纹相等；审脚本TERM/单次Popen及protected核验路径；源码核原生cache清理；核HTTP/WS、全局roster、资源及五库/旧行证据 | 旧70121退出，新8471单次启动，Caddy77413及原round3进程保持；加载前后资源均0、health就绪/WS101；五库完整性ok、旧messages/root/bindings保持；两dist439/67文件不变，正式插件/配置/SOUL/helper保持 | fresh import是独立子进程指纹，不声称运行中解释器反射；初始被覆roster只有明确标注的二级转录；不是全程首次无失败 | 关闭 |
| V5-E04 | 同目录`original-A-rest.json`；上级`root-cold-ui-result.json`、`root-A-fixed-cold-ax.txt`、`root-A-fixed-cold.png`、`root-after-fixed-newchat-ax.txt`、`cold-ui-resources.json` | 再算REST消息数组UID计数；与原A`live-after-fork.private.json`的16条identity/content逐条比对；完整AX逐段核旧尾缺失/共同前缀/新UA/Compaction；查看尾部PNG；独立比较close前后与旧实际receipt/thread_sync | 两退休UID各0，合法六条各1；REST17展示节点不误当canonical6条；16既有源内容hash全部一致；全AX保持共同四项、工具/Thinking、真实Compaction及新UA，旧批准/旧完成答复无残留；实际New Chat离页后精确33026cc0 close=true，各自资源0，未增ordinary/修改同步账本 | PNG只证明当前尾部视图，全量内容结论来自完整AX与REST；root未新增输入/编辑/模型调用；不冒称本审查者操作UI，也不替代另独立Validation | 关闭 |

加载失败按原件保留并解释：第一次守卫发现原A runtime19048d39仍在（root此前goto根路径实际被恢复到A），当时未备份/TERM/启动；随后root真实点击New Chat离页并明确授权精确close，正式新收据核owner，稳定空roster后才唯一重载。初次`before-active.json`被续跑覆为新的停前空roster，`initial-blocked-roster.from-tool-output.json`只是二级转录，不能恢复原SHA；关闭前新的正式roster/close收据及原失败日志足以支持后续安全重载，不用二级转录证明未保存的原字节。

第二次`resume-error.json`确为tester过宽安装目录指纹断言：`resume-execution.log`定位restart脚本209行；`post-load-protection-diff.json`与`post-cache-guard-resolution.json`只列exam五个旧pyc消失、protected无差异、产物仍匹配。已亲读固定v5 `hermes_cli/main.py:2287–2306,3552–3554`与`main_web_build.py:38–68`，确认启动HEAD指纹改变会递归清理checkout中的`__pycache__`，未排除ignored测试Home；属于原生可再生缓存清理，不是正式插件文件被改。随后只读继续审计，没有第二次重载、安装、缓存恢复或配置改动。此处修正的是测试指纹范围，没有放宽产品源码/配置/权限/静态产物保护，也不删除错误记录。

最终冷页面资源包SHA `ca4051073db845c1593e9379c12908094e246b8df846c32e7210734b5ddfd3a8`：profile为exam、stored `20261018_211409_356f17`、Conversation `conv_08b0e53da01a40248939441b528142d5`，本次冷恢复owner `33026cc0`。已独立比较before/after bindings、canonical摘要/16身份、receipts、thread_sync完全一致，且16身份及receipt/thread_sync与原真实A分叉原件一致；实际REST源内容哈希按原脚本`sha256(json.dumps(content, ensure_ascii=False, sort_keys=True).encode())`口径16/16相符。close后active/runtime/lease/compression/child/schedule/claim/pending均0，其他owner关闭、ordinary输入、NM读写、服务重启均0。

补证manifest52项加冷UI三项，共55项hash均匹配；核验摘要及逐项结果在`E/independent-verification-v5/load-cold-original-crosscheck.json`。冷AX SHA `24520c5bfd944269c8fd34a8aef3e978da1f00f2c8dcd1481a337b11722d8848`；PNG SHA `a57f28907276a204e5f27dd4a87cab1c8c732657fee40a05ac4742c51ff674bf`；New Chat离页AX SHA `fb4081be9f65064b0ff3cf4f36a2d2c74ff3a95c6ab41b03088f85a51ff2c0e7`。最后AX实际URL为`/new?profile=exam-assistant`，并有独立Profile选择器，不再以根路径推断已离开A。

**最终总体判定：Verification PASS，限定固定v5、本轮产品意图与PI01–26已批准当前范围。** 原V5-E04和V5-ELOAD均关闭，§3中的加载/原A“待核”状态由本节正式更新；无剩余确定性阻断实现缺陷。PI21待决、PI23三模型偏差、不绿历史大套的既有失败分层、长期运行观察、真实云端Access/未验平台保持原边界；不得改写为全仓/全愿景/全平台通过。下一门禁由全新独立Validation依据实际产品入口及本次版本原件作出自己的结论；本报告不预签Validation或最终交付完成。
