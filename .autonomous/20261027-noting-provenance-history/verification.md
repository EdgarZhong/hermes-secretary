# Verification：20261027-noting-provenance-history

## 1. 审查对象与结论概览
审查者：独立 Verification Agent `/root/verification`。判据建立：2026-10-27 01:01–01:06 +08:00（以实际文件落盘为阶段界限）。

- Snapshot Index：本目录 `snapshot-index.md`；基线：`baseline.txt`，`02d55fdb45b4fb7c883fb477f4469912f4707f70`。
- 待审产品版本：尚未收到；当前仅完成独立规格判据阶段，**未开展实现调查，未给门禁通过结论**。
- 范围：索引C01–C20、本轮Notebook来源链／Evidence time、History／Prompt调整及所有适用保留契约；生产转换和发布作为C01单独交接，不与本地实现门禁或独立Validation混同。
- 阅读边界：先读根AGENTS通用规则、两项Skill、索引／基线；仅以冻结commit的规格原文建立第2节。尚未读取产品代码、测试、动态CLAUDE、plan、实现解释／报告、历史审查结论。按派遣的独立阶段指令，CLAUDE延后至判据落盘后。
- 原文定位：下文 `07`、`02`、`04`、`01`、`06` 分别为 `docs/07-scheduler-notebook-noting-compaction-redesign.md`、`docs/02-noting-system-specification.md`、`docs/04-hermes-secretary-v1.5-implementation-spec.md`、`docs/01-personal-hermes-v1-first-fork-iteration.md`、`docs/06-Hermes-Secretary-Web-UI-V1-Spec.md`；`白板`为`docs/notebook-ontology-whiteboard.html`。均使用冻结基线树原文，不把后续执行事实当要求。
- 进入下一阶段条件：主会话提供最终产品commit及同版本证据入口。产品只读；仅本报告及`reports/verification-*`可写，无生产写入、服务操作、真实模型调用或提交。

## 2. 独立要求清单与覆盖
本节是查看实现之前形成的独立起点。优先关系为：索引所录最新用户确认＋07顶部2026-10-26／27 > 07后续R20／done及v2未覆盖内容 > 白板未冲突内容 > 02保留身份／Foreground／Snapshot／来源／运行约束 > 04未覆盖增量 > 01原则；06保留原生客户端、只读Notebook及既有API契约。旧数组整体替换、time_range、物理role、哈希投影、旧四工具／双profile等被明确替换的内容不反向成为要求。本轮不改第8块生命周期／清退，保留其真实结算边界。以下均是直接要求；明确标“必要推导”的部分只从该要求恢复必需条件，未指定内部符号或算法。接口拼写、未知槽位表达、跨域外层组织、包装清理清单是工程细节薄弱处，须按语义取证，不因细节薄弱而降低判据。

阅读完成范围：白板全篇（包括七类型动态文本及完整场景）；07全篇；02 §1、§2的Foreground／路径／Anchor、§3.1–3.4 Snapshot相关保留条款、§4–5适用运行条款；04 §2–5未覆盖增量；01 §1、§3–4；06 §0、§1.12及§2.6–2.9现行Notebook／只读／兼容API。旧Prompt／Schema按07替换声明处理，不继承旧限制。未读archived目录。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| C01 | 索引C01；07:23旧数据范围；01 §1.2／§4；06 §0.7 | 实施、测试、发布与单目标生产转换；生产待主会话 | 只转换Alex仍用的一条置顶Conversation；不建通用兼容／迁移；聊天事实、模型配置、Schedule／绑定及其它会话不变 | 本地产品与新结构可审；部署另核main版本／服务／目标身份及转换前后差异。不能用尚未发布阻止本地门禁，也不能将本地通过冒称上线完成 | 第3节C01；生产交接 |
| C02 | 07:8；索引C02；白板U1／U2；R20:72–78 | 内容保真／稳定ID | 未实质提及／无推进时正文和状态原样；Assistant提示、Reminder到期、未答不是更新证据；去留规则未改 | 场景中没有新事实且无建议缺口时，不润色正文、不改done、不新增来源节点；同情景澄清原位更新，真正不同对象仍可归档／创建 | 第3节C02、R01 |
| C03 | 07:9、v2 §4／§6.1第6步；索引C03 | Schedule建议例外 | “稍后处理”未明确推迟不更新正文／状态；缺登记才在相关entry补语义建议，不能造时刻或自行登记 | 无明确推迟＋Main无登记证据时补一对象两字符串建议；已有登记或无缺口不造；原内容保持，建议不等于Schedule，更新仍满足来源同传 | 第3节C03、R05 |
| C04 | 07:10–12、34；索引C04 | 来源链结构／UID合法性 | 直接来源是UID数组的数组，条目×Task分组；每次提交内无重复，跨Task同UID可重用；不用时间范围代替精确消息 | 非空合法完整UID组；不接收时间段新来源；跨Task复用同UID合法、同组重复拒绝；旧Task节点完整有序且只读 | 第3节C04 |
| C05 | 07:12–13；索引C05；v2 §3／§4.4 | Task身份／原子编辑；槽位持久机制未指定 | 同一条目同Task至多一新槽，无编辑无新槽；多次调用及续Turn只覆盖本Task完整来源组。每次真实编辑属性与本Task来源同时提交；fields按键合并，其余值覆盖 | 同Task创建后连续修改、续Turn、失败重试均只占一槽；新Task追加一槽；不得以每调用追加／整条重置／新UID全链替换实现。缺属性或缺来源、非法UID／只读旧链修改整次零副作用 | 第3节C05、R09 |
| C06 | 07:34；索引C06；白板C2／C3／C6／C8／C9；07 §4.1–4.2保留 | Candidate两模式及派生refs | 直接Task来源链或notebook_refs＋正确source_types二选一，目标无关；不复写来源正文；反向candidate_refs派生；gap标签映射situation | 直接／引用型创建、更新、转换合法；混传／空来源／错误标签／引用candidate或失效对象拒绝；refs型沿现行源，源更新不伪造直接链、不重置审批范围 | 第3节C06、R06 |
| C07 | 07:24–25；索引C07；v2 §5被新派生口径覆盖 | Evidence time链／只读；未知表达薄弱 | 每个直接来源组产生一个时间元素：有真人user只取这些user，一条点、多条最早／最晚范围；无user取最近Assistant；都无取组消息范围；未知不造现在、不丢槽 | 多组混合来源及未知组时逐槽一一对应；同Task只重算对应槽，旧槽时间不刷新；模型写入evidence_time拒绝；refs型沿源链派生，不伪造直接UID | 第3节C07 |
| C08 | 07:26；索引C08；白板T4／L2 | 时间来源与生命周期 | 消息原始timestamp是证据时间；正文“昨天完成”等不是事件时间抽取依据；重读／重写不刷新进展／讨论年龄 | 固定源消息原时刻，跨今日／重读／正文日期冲突仍一致；不改last_progress_time／last_discussion_time／gap识别时间来掩盖老化 | 第3节C08、R04 |
| C09 | 07:20、48–51、59；索引C09；07 §5.2 | Get Meta时间主查询／查询复用 | 不需关键词可按消息时间查询；include可选且就是原Search匹配语义，roles可选；不建新检索器 | 无include时间查询成立；关键词、短语、AND／OR／NOT／前缀及CJK等适用原Search路由，非法query／执行失败诚实；不可替换成独立字面包含逻辑 | 第3节C09、R14 |
| C10 | 07:21、52–56；索引C10 | Meta结果预算／字段严格性 | 单条严格message_uid、timestamp、role、content；头100＋尾100，短文不重复，跨域归属仅在外层 | 0、短、200、201、Unicode长文和结构内容都有明确预览；无第五单条字段／哈希／分段head-tail字段；总count及分组对应真实全部行 | 第3节C10 |
| C11 | 07:41、54；索引C11 | 正文清理／来源分类；包装清单薄弱 | 先可信分类与范围过滤，再剥本项目注入timestamp／HTML标签，再头尾截取；保留独立原timestamp和持久原文 | 注入timestamp、Reminder／Framework／Heartbeat／Compression／Notebook包装不占预览预算；用户自写HTML／日期／仿冒标签不可泛删或当可信分类证据；持久正文逐字未改 | 第3节C11、R12 |
| C12 | 07:51；索引C12；07 §5.1–5.2；02 §1／§2.7 | 全模式作用域与授权 | cross_conversation顶层独立默认false；Main只可显式同Profile授权真实Conversation；Noting只绑定父，不因模式或工具声明放权 | Search／Read锚点与邻居／无锚点Read／Meta默认本域；所有Noting跨域和错误owner请求拒绝且不泄露外域；fork、rewind与合法压缩路径仍成立 | 第3节C12、R07、R11 |
| C13 | 07:39、41–42；索引C13 | 全模式统一默认／辅助开关 | 默认只真人user与Assistant；顶层include_auxiliary独立默认false；旧roles／kinds／工具内容参数不可绕过 | 三模式及锚点邻居都默认排除tools／system；显式roles=system／tools、kinds或旧include_tool_*而无辅助开关仍不可放行；打开后仍需合法可见性与授权 | 第3节C13 |
| C14 | 07:40–41；索引C14；04 §2.4–2.6 | 语义role与可见性 | 输出／过滤统一user、assistant、tools、system；库内user系统载体归system；不泄露原不可见Prelude／隐藏内容 | 对物理user载体、真实用户、assistant、工具call/result、压缩消息按可信display_kind／origin分类，四种role过滤与输出一致；清理后不得改分类 | 第3节C14、R12 |
| C15 | 07:21、43–44；索引C15；07 §5.3 | 工具调用配对／完整Read | Search参数与结果各头100＋尾100无hash；Read选定工具可取完整当时参数与结果；同次call绑定，不猜相邻、不同call不混 | 单批多call／乱序结果／缺参缺结果／长JSON：准确按调用身份配对；Search无args_digest/content_digest，Read有界分页可还原完整源，缺失诚实且无旁call泄露 | 第3节C15、R15 |
| C16 | 07:16；索引C16；07 §5.2(5) | 所有时间查询闭区间 | 包含上下端点，筛消息timestamp而非Session start；单独上下界同样包含 | 三模式及可用时间入口，以恰等于start/end、单界、跨时区等价时刻及乱序Session时间反证；原timestamp独立不变 | 第3节C16 |
| C17 | 07:22、52；索引C17 | Meta完整返回／容量 | 过滤后的时间段每条都返回；复用200逻辑消息容量，超过明确缩小窗口错误，不成功截断 | 0、20以上、200、201过滤命中及大量辅助消息挤压场景：≤200完整，>200明确错误；不能只首200／默认20或partial成功冒称完整；跨域按总合法过滤量执行容量 | 第3节C17、R14 |
| C18 | 07:7、14–15、30–32；索引C18 | Prompt取证来源／有限查证 | 父最新可见压缩区间为更新主依据，早期消息只必要追溯；无缺口不查；真人user第一、Assistant具体回复第二；取UID默认Meta，Search定位，Read补细节 | 真正构建Task、History指导、工具说明一致；无机械全史重读、不搬已见全文取UID、不将旧证据复读当进展；系统user不冒真人、AI建议不冒认可；需真实模型证据支撑行为 | 第3节C18、R02、R17 |
| C19 | 07:30–35；索引C19；R20:63–78；done节；v2 §6／§8.11–8.12保留 | Prompt组织／结束边界 | 第5块集中无变化与需编辑两类及同槽同传，跨Turn说明同处；第6块保留来源／UID和属性合并，避免重复。不教本轮／上一轮；Candidate链／refs二选一、建议保留；第8块清退和原finish语义不改 | 审真实全Prompt及初始／续Turncontrol，不只常量diff；无重复schema／内部snapshot、版本、anchor、admission、DB等教学；冻结父完整tools／root／Active每请求一致，无临时补工具 | 第3节C19、R08、R09、R17 |
| C20 | 索引C20；07 §3.1、§4.5、§8.1／8.13、§9.3；02／04适用保留 | 正式链路／原子性／所有分支；详R01–R18 | 新机制必须接正式工具／dispatch／私有工作态／不可变版本／最终Snapshot／模型投影，保留权限、配置、并发、失败、fork／rewind、重启及cache-parity | 从真实注册和调用入口走到用户可见结果；不能用孤立helper／镜像测试／源码字符串断言替代；同版本机制＋真实模型证据，独立Validation另验，生产状态单列 | 第3节C20及R01–R18 |
| R01 | 白板C1–C9／I1–I2／U1–U2；07 v2 §1–3、R20、done节 | Notebook结构／类型／稳定身份 | work／situations／discussion／candidates；七类及Candidate合法字段不放宽；done顶层布尔默认false／更新省略保持、非布尔/null拒绝；done不等于成功、不自动归档 | 全类型可选必填与工具schema／validator一致；同事保稳定entry_id，真实改动新不可变版本、no-op无新版本／时间续期；模型投影无version_id，API原字段保留 | 第3节R01 |
| R02 | 白板C7／C8、N2；07 v2 §6.2／§8.11 FAITHFUL | 用户归因／内容取舍 | 用户问题／认识／决定须用户提出或明确认可；模糊确认只覆盖有证据点，AI未回应提问不入；真实不确定性不消失，不凭done=false造未开始 | 工作进展、情景／身份／偏好／情绪／关系、开放讨论／未采纳答案、纠正与有用历史均有代表证据；description语义索引软长度，无硬截断、无流水账、无强迫每类建条 | 第3节R02、R17 |
| R03 | 白板L0／L7／L2／L3／L4／E1–E2；07 v2 §6.4／第4–5步 | 生命周期／结算（本轮不改） | 7天／72小时为本次Noting处理点非自动删除；未完责任／有效约束／待批来源保留；外部成功覆盖退出，失败／未知不结算；后续变化／未覆盖部分保护 | 完整／部分成功和共享来源、用户拒绝／撤回／未知结果；先处理源再Candidate，不查目标存储、不盲重写、不因“仍有用”保已结算余额、不因旧证据重读回流；第8块原文保留 | 第3节R03 |
| R04 | 白板T4／L2；07 v2 §4.1／§5 | 生命周期时间独立 | Evidence来源时间不代替last_progress／discussion、gap首次识别和created／updated；处理注记仅留痕，重述／重写不刷新实质年龄 | 同源读写、多周期整理、只改processing_note和无变化路径核时间不被现在替换；unknown不造“未到期”或事件日期 | 第3节R04 |
| R05 | 07 v2 §4／§6.1 Main条件提示／§8.13 | Schedule语义建议／条件投递 | 每entry含Candidate最多一对象content＋schedule两字符串；普通语义不校验Cron／时间语法，不能新增refs／队列；只有实际有效Notebook含建议才附已定Main提示 | 所有类型创建／修改／null清除；建议内容自包含含必要背景，不套description软长度；非触发Framework不启Turn／不外发渠道；Noting仍无Scheduler权 | 第3节R05 |
| R06 | 白板C2／C3／C6／C8／C9／F1–F2；07 §4.1–4.2／§8.10 | Candidate来源与审批／引用 | targets不混conversation与持久化，标签集合正确且gap→situation；源正文原位，正向refs稳定ID、反向派生；批准仅当时具体范围，不继承新增内容 | 源更新／源归档／多来源／部分结算／目标变更后保持引用完整与语义同步；显式批准到实际成功链正确，无目标支持标签额外成功门槛 | 第3节R06 |
| R07 | 02 §1、§2.1–2.4／§2.6–2.7；04 §2.1–2.6；01 §1.3 | 身份／三Foreground／路径 | Conversation不等于Session，ref不按格式猜owner；压缩／resume同ref，新建reset真实fork新ref；History只当前合法原消息，不用Active／Full替代 | 原地／旋转压缩、合法inactive fork来源、rewind/edit/undo失效路径、分支共享版本、不混Profile；History只读不修binding、不建新Conversation，规范identity仍ref＋UID | 第3节R07 |
| R08 | 07 v2 §0／§3／§8.2；04 §3保留；02 §1.9／§5.7 | 工具正式面／能力开关 | 合格Main固定完整API顶层History、按门禁Notebook和独立Scheduler；Main禁create/update/archive/finish，Noting精确六工具；普通auxiliary不继承Main权 | 同步、并发、invoke／间接调用强制可信身份拒绝且无副作用；全局Noting／Scheduler四组合与local off、warm／cold、旧pinned schema重建边界一致，local不重建prefix | 第3节R08 |
| R09 | 07 §3.1／§4.4–4.5；02 §5.4／§5.8；04 §4.6 | 工作态／Finish／强制结束 | 单child最多5原生Turn，完整working初始／续Turn、成功回执完整单条；finish只end_requested，最后单独且混批整批拒绝，首次结束后工作态冻结 | 文本done不终结；结束后写拒绝／读可用／重复finish首次结果不改；原生Turn返回后合法状态才提交；预算及已处理overflow合法快照尝试、真实API失败可无新快照、资源总关闭 | 第3节R09 |
| R10 | 02 §3.1–3.4／§2.6–2.7／§5.10；07 §3.1／§8.13／§11.1 | Snapshot／pointer／完成消息 | insert-only完整快照与pointer同事务，检有效开关／Anchor／版本／来源；按合法覆盖位置非完成时间选pointer；只本次新生效结果准备完整Framework，排队追加再原子核pointer | 并发A/B晚完成不回退；rewind失效拒绝、fork共享不可变不串改；旧排队通知及Proposal整条丢弃；正文完整非delta／ID，durable/live同写，失败不伪提交 | 第3节R10 |
| R11 | 02 §5.2–5.5／§5.10–5.11；04 §4.4–4.5；07 §3.1 | 父子前缀／原生执行／持久化 | 准入冻结实际root／完整tools顺序／多模态Active到Anchor，所有请求＋重试＋continuation继承同前缀，仅累积child后缀；原生模型／Provider／推理路由，D01真实最后派发来源判断 | native/external／fallback／未知门禁、副作用前拒绝；父后续Turn／压缩／配置变化不刷新child；真实逐请求比较与缓存usage分开；仅child新后缀持久化，关资源／崩溃不自动恢复 | 第3节R11、R17 |
| R12 | 07顶部:39–44；07 §5.2–5.5；02 §2.2／§5.6；04 §2.4–2.6 | History可见性／载体／时间 | 模型可见系统消息可显式查，root／Prelude／隐藏注入不可；先可信语义分类再clean；timestamp以原瞬间及Profile时区可读到秒，不重铸 | 系统user与仿冒用户标签、复合Compaction carrier真实用户投影、不存在消息诚实；History内容不执行为指令，原始时间／正文／持久role不改 | 第3节R12 |
| R13 | 07 §5.1／§5.3–5.4 | Search／Read现行模式契约 | Search必填query，正向命中字面邻域受预算；Read锚点必达或source_unavailable，默认前2后3，时间／limit不得筛锚点；无锚点read本域有界；旧名／物理锚点明确退出 | Search／Read非法参数组合、空结果／缺锚点／多模态、辅助默认范围下邻居；读长内容不能用Search冒完整Read或任意换源，原生session_search行为未改 | 第3节R13 |
| R14 | 07 §5.2(2–8)／§5.4–5.5；07顶部:20／22 | 既有检索机制／diagnostics | 复用原生FTS5／CJK／trigram／LIKE／OR等既有降级；候选固定路由、FTS/gap分别有界推进去重并验证membership，不首批过滤后误报空；不建复制全文库／全会话扫描 | 合法inactive分支、索引gap、坏query、降级／执行失败／候选预算：诚实error/warning/partial，普通Search partial不声称穷尽；Meta需全量才成功 | 第3节R14 |
| R15 | 07 §5.3 content_offset／超限指导；根AGENTS | Read有界续读／工具预算 | 同一identity合法0/0分页按Unicode码点返回原片段、完整源元数据及next offset，末页null；每页重新权限校验；真实外层spill／总预算不诱导文件越权 | 长工具参数与结果／Unicode／结构内容可连页还原；offset末端／越界／路径失效；Noting无read_file等兜底，不能路径预览当全文；普通runtime预算不变 | 第3节R15 |
| R16 | 07 §7.2；v2 §3／§6.3；根AGENTS增量兼容 | 错误／关闭／接口兼容 | 具体字段、code、message、next_action；拒绝零副作用；展示／估算失败不阻主逻辑；关闭／非eligible原生保持，API增可选不改既有字段与错误语义 | 参数、来源、权限、引用、终态冲突、DB／索引失败及unknown结果分清，不自动修写输入／盲重试；人类API／现行DTO与CLI slash读取仍兼容 | 第3节R16 |
| R17 | 07 v2 §9／§9.3、R20、done节；根AGENTS Harness与测试闭环 | 真实机制／模型／证据有效性 | 同Conversation多Task／压缩、正文接续／未知不造、语义来源／权限、真实provider工具协议及全请求prefix需真实证据；模板常量或模型自报不足 | 同版本准确对象、受控机制非镜像／源码断言，正式构建全Prompt含project／skills／footer；真实模型样本覆盖适用分支、错误调用统计与强制拒绝证据；与独立Validation及生产状态分列 | 第3节R17 |
| R18 | 07 §6／§8.1／§8.13／§8.14／§11.1；01 §1.1–1.4／§4；06 §0／§1.12／§2.6–2.9 | 保留运行／部署架构／UI边界 | 无新loop／存储／调度／Provider／API hierarchy；独立Scheduler、due/claim/ACK重试、Idle正常Noting→durable压缩→Framework、Force区间占用、阈值自动保尾／显式here N／失败不吞消息等既有契约保持；无UI改版 | 按本轮变更影响核正式上下游和相关既有同版本证据：未启用原生、全部触发／失败／重启、不误外发渠道、Reminder真实请求ACK；Web API保字段与只读human-only Notebook，前端未改无需UI施工验收；生产C01另交接 | 第3节R18 |

共38项（C01–C20、R01–R18）。C20为交叉覆盖总入口，不用它替代R行。判据修订记录：无；当前版本全部在实现调查前建立。C01生产发布完成判定需主会话后续证据，当前未因未上线推断实现违规。

## 3. 逐条实现证据
| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| 全部38项 | 未调查；待主会话给出最终产品commit | 当前只完成规格判据，不读取实现或已有测试 | 第2节为独立要求来源 | 未判定：尚未进入实现审查，不冒称符合或门禁通过 | 待逐行展开；不将此占位视为最终全要求矩阵 |

## 4. 核心目标及验证方法审查
当前只建立检查方法：以C04–C08来源链／Evidence时间、C09–C17 History和C18–C19真实Prompt构建为三个核心纵向路径，从正式入口追踪到持久状态及实际模型结果；C02／C03必须有内容保真和建议例外的联合场景。R01–R18检查完整保留契约和本轮接线影响。

接线细节薄弱处重点反证：同Task身份跨Turn是否稳定；旧节点权限是否由正式写入点保证；未知Evidence槽是否错位；辅助默认是否被旧参数绕过；工具参数／结果是否同次配对；Get Meta是否真的枚举全部过滤命中；清理是否误伤用户原文。先审证据对应的版本、真实入口和受控依赖是否绕过机制，再决定必要小范围反证；复用有效证据，不复跑大型套件／昂贵真实模型。真实模型证据不足交主会话补齐，独立Validation后续单列。

实际接线与已有测试评价：无，尚未进入实现调查，不能据规格推断已实现。

## 5. 发现、整改优先级与范围外项
| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| 无（判据阶段） | 尚未查看实现 | 暂无实现发现；最终产品版本未收到 | 无法作本地实现门禁结论 | 主会话提供最终commit后开展第3节全矩阵审查 | 等待版本；非已通过 |

范围外发现：无，尚未调查实现。明确排除：UI／APK改版、Scheduler机制重写、旧失败Noting重放、Provider／Persona调优、旧时间修复、NM或其它服务迁移。生产操作不由本审查Agent执行。

## 6. 修复与独立复审
当前无修复／独立复审或退回记录；尚未形成实现发现、主会话提案或工程收敛。无可供final-delivery.md摘要的实现收敛项，理由为本报告当前仅完成独立判据阶段。后续保留原判据、发现、主会话提案、评审理由、实现版本与关闭证据，不迁就已见实现改写判据。
