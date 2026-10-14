# Validation：20261012-round2-web-ui

## 1. 结果概览

**正式真实Validation已按收尾授权交回；具体整改复验通过，未覆盖边界和体验偏离保留，不宣称全范围通过。** 2026-10-14恢复会话由Astra Root编写本材料/指示，GPT-6.1 Sol执行真实验收。按用户R2-C112先真实Validation、整改和复验，最后静态Verification；覆盖套件默认先后顺序，不再临时/开发态验收。

依据：snapshot-index.md、baseline.txt、现行02/04/01适用Core契约、06 Web契约及最新直接用户决定。用户口径审计user-intent-evolution.md仅为原话/反馈导航，不代替权威原文。执行者核读原文，不从代码输出反推预期；若发现本材料遗漏适用场景，集中反馈Root补充。Root编写的预期不能被执行者静默降低。

初始待验后端cb05c0671c、正式UI ab1f4c4；当前已统一运行BE ea2ab483999f9230abfd794bdde2ea3fe2468cfe（产品同cb05c）、FE833ef31468dbc73e0f25961cec1fe81399ba6111。Root集中review交回证据，按用户目标决定是否覆盖完整。整体完成需所有适用场景通过或有用户依据的不适用；失败/未执行/必要证据不足保留。

## 2. 环境与准备

- 唯一环境：仓库内 `.hermes-dev/round2-runtime`，前端 `http://127.0.0.1:5173`，原生后端53445；不得另开profile/端口，不操作真实用户主目录Hermes配置、不清库迁移。既有测试历史保留；新验收会话使用明确标题方便回查。
- 真实浏览器使用Codex内置浏览器；四视口1440×900、1024×768、390×844、320×568，必须记录实际生效的视口，不能以发出resize调用代替生效证明。移动实体键盘/相机/系统侧滑仍属后续真机专项，不冒称覆盖。
- 真实模型沿原round2已有Hermes原生provider/model；禁止另建路由、Codex Proxy/App Server、测试假模型。用户允许充分调用DeepSeek；记录请求/Turn/工具轨迹及等待，不用费用理由省掉必要场景。
- 只通过用户正式入口提交消息/操作；只读RPC、真实DB或日志作结果诊断补证，不以直接写DB/调用内部helper代替用户旅程。不得篡改系统时钟或伪造事件。为验证原生配置模式的临时设置，先记录原值，使用产品既有入口，完成恢复；恢复有失败需明确报告。
- 只操作本次建立的测试数据或已明确授权现有测试会话；重启统一由Root协调，先检查Main/Noting/compaction空闲。记录运行进程与产品版本，不自行关用户服务。
- 不重跑完整Python/JS套件或重做已有效的大容量机制证据。用户要求的真实反馈复测必须执行；已有证据可说明特定边界，不能冒充本次实际浏览器结果。
- Clarify在 `../hermes-secretary-web-clarify` 独立分支实施，用户尚未授权合并；正式5173当前Clarify现状应如实登记。不得将未合并成果算正式入口通过；分支结果单独记录，待合并指令后复验。
- 每条发给Hermes主模型的测试消息（含后续追问/纠正）都必须在场景正文前携带以下原文；slash控制命令走原生命令入口，不伪装普通模型消息。测试问题要求模型直接回答工作体验/可见上下文，不请它解释实现，也不诱导其读仓库。

> 你不是开发者，你是测试官：仅作为 Hermes 的主模型，不访问当前hermes工作区外的东西，不要去看代码仓库的东西，不要研究你所处的 harness背后的代码机制。以你当前可见上下文为唯一行动指导。禁止对Harness 的代码机制做任何建议或者点评，只汇报你的工作体验。并如实的**直接回答**可能的提问，不要去调研代码库

证据白名单：`.hermes-dev/round2-verification/formal-validation/`；本报告为正式结果入口。保存脱敏截图、DOM必要片段、输入/输出、时间、Session/Conversation标识、版本和必要原生事件。不得把凭据、整段无关用户历史或巨量工具日志返回主会话。完整阶段集中交回，消息仅摘要和定位。

## 3. 用户目标与场景覆盖矩阵

以下是Root制定的正式执行基线；执行者须结合user-intent-evolution报告把每项有效反馈映射到场景，缺项向Root提出，不自行略过。

| 目标编号及依据 | 完整场景编号 | 场景类型与起点 | 数据/顺序及预期 | 当前执行结果 |
|---|---|---|---|---|
| G01 06§1.2–1.4 | V01 连续对话/恢复 | New Chat→真实多轮→切会话→返回→reload | 列表/标题/路由/真实历史连续，草稿独立，消息不重不漏 | 多轮/草稿/冷恢复/断连代表链；F02新phase3实际call与Unknown0通过，§4.20；首次200/Show More未取得 |
| G02 06§1.4–1.5、用户实时反馈 | V02 流式顺序与工具呈现 | 要求模型进行有意义的多步计算/整理并调用允许工具 | 新User处于实际顺序；Thinking/Tool/正文实时增量，无终态扎堆；同call一张卡含Parameters/Result，Success/Failed准确 | Running/Failed/Steer及新phase3实际构建结案/单份Known通过，§4.20；本新链动态UI过程失采，不推广全组 |
| G03 06§1.6、C49/C112 | V03 Composer与视觉 | 四视口New Chat/Conversation，空白→多行，浅/深/跟系统 | 共用底边向上展开；User左12%右3%，Assistant左4%右10%；无横向溢出；悬浮胶囊不另占层 | 部分已测；四视口/底边/边距/主题有实际证据，其余呈现未覆盖 |
| G04 06§1.6、C21键位修订 | V04 Enter/Escape/草稿 | idle/active/有Pending/附件/IME | Enter只Send或Steer，空Enter不Stop/Interrupt；Escape按实际取消动作；普通文本undo不改历史 | 部分已测；文字undo、active/Pending空Enter和Escape Stop保附件稿通过，IME未覆盖 |
| G05 06§1.8–1.10 | V05 Steer/Withdraw/Interrupt | 真实长Turn插入两个不同纠正，撤回一条；另轮Interrupt | provisional位置正确，撤回只在仍pending成功并覆盖草稿；消费按同插入点一条；Interrupt仅交接剩余pending一次，保未发附件 | 代表链已测；撤回/同点合并/及时消费及FV-C Interrupt唯一handoff/保未发附件通过，余边界保留 |
| G06 06§1.10 | V06 Stop/Cancel Send | 实际活动Turn Stop；有附件发送中Cancel | Stop不发新Turn；取消成功恢复原文本/附件，不冒称撤销已接受Prompt；unknown有真实归属/恢复 | 部分已测；真实Escape Stop/原生exit130/无新Turn且保附件稿；Cancel Send/unknown未覆盖 |
| G07 06§1.11/C66 | V07 Reply/Rewind | 在本次测试会话选旧User、退出/取消/确认/reload | 临时隐藏与草稿恢复；Send后唯一红色确认；成功截断符合目标，reload不自动执行 | 代表链通过；退出/红确认Cancel/确认前reload解除武装/新BLUE活动分支及旧UID原生不可读，§4.18；并发等未覆盖 |
| G08 06§1.7 | V08 附件输入到理解 | 图像含可核对象与文字；普通PDF/文本同名不同文件 | 选择不上传、发送绑定同Session；视觉真实像素理解，非辅助文字冒充；文件模型可读且历史仅chip/名字，不摊正文 | 图片像素/同名文本/长名/PDF真实读取代表链；图形首错、PDF漏2和no-file临时PNG违反保留，§4.21；拖放等未覆盖 |
| G09 06§1.7/R2-C30 | V09 附件边界与失败恢复 | UI累计预算/移除释放、失败或取消保稿 | 500000000合计而非每文件；最大容量传输机制可引用有效现版本证据，不重复昂贵上传；无证据不得判完整通过 | 部分已测；累计500000001拒第二/移除释放，仅选择不大上传，取消/失败/unknown余项未覆盖 |
| G10 06§1.12 | V10 Slash/模型/Reasoning | /补全Tab，选项回读，/notebook | 命令说明正确换行，高亮真实当前项；原生错误可见；/notebook临时四区只读，无Anchor、无额外Turn、无模型上下文污染 | Tab/当前项/正式Persistence、globaloff Notebook真实错误；C117内存位置及reload3→0新链通过，§4.20；重叠回包排序未覆盖 |
| G11 06§1.13/C108 | V11 Usage各字段保值 | 新真实会话连续≥3Turn；active/idle/切换/reconnect | 有效Turns/Total/Hit/Latest按真实源显示；缺失或错误不清空已得值；0有效；Latest仅完成Turn，不混Noting；无前端持久化计数 | 部分已测；FV-F01缺陷复验通过，Session/Latest真源已核，其余边界未覆盖 |
| G12 06§1.13 | V12 冷会话未知边界 | 已存旧会话冷恢复，再发真实Turn | 有保存input/cache则展示并按公式算Hit；可靠原生Turns/Context不足明确未知不猜；已有有效值不因cold fallback消失 | 代表链通过；saved历史计数与Hit保留、Turns/Latest/Context未知不猜、新真实Turn恢复，§4.17；错误包边界未齐 |
| G13 06§1.14、02§4–5 | V13 手动压缩 | 足够内容会话手动compact→过程→成功/合法would_grow | Context原地loading，展开仅有效Cancel；真实摘要及时插入且默认折叠、原文可展开；无伪摘要/重复User | 代表链已测；独立取消/FV-A合法nochange、FV-C真实手动completed与摘要/Context已测，余边界未覆盖 |
| G14 06§1.14、02§4.10/5.9 | V14 Noting with compaction | 原生配置合法开启→真实Main结束→Idle自然触发 | 确实特殊Profile/compact_parent；成功摘要无需reload出现；would_grow是不同结果不能替代成功；Parent轮转连续 | 特殊核心成功/低条件ordinary负例已测；e829真实Parent完成Context更新通过，后续连续性/余边界保留 |
| G15 06§1.14 | V15 压缩取消/结束恢复 | 真实进行中取消，观察Parent | 只取消compaction，不中断Main/破坏历史；已提交不能假称回滚；Context正确恢复、无假Summary | 取消作用已测；真实active→cancelled/Context恢复/无新summary，notice已归非阻断体验观察 |
| G16 06§1.15/C106 | V16 Orb/Memo/notice | 真实Main→等待Idle→Noting→成功或已知失败 | 倒计时/active/finished/idle符合事实；动画非雷达、收起不闪；Memo展示真实；失败notice准确且无假成功Framework | 部分已测；自然2秒timer/Main/Noting/Framework，动画/notice未覆盖 |
| G17 02§5.12/R2-C110 | H01 主动秘书/Memo | 真实表达计划、约定、后续要做事项→追问→自然整理 | Main理解原意，合适时写Memo；Notebook仅Noting写；下一整理包含所指事项；Memo不是新用户事实/provenance | 代表链已测；真实Memo→自然Noting→Snapshot，完整门禁待余链 |
| G18 02§2.5/5.12 | H02 十类语义与忠实维护 | 演绎commitment/reminder/task/watchpoint/decision/question/insight/candidate合法情境 | 合适分类与状态、保留条件/不确定性；不复制旧派生内容造新事实；不强迫所有输入都创建条目 | 10语义类型代表真实Snapshot已测；Persistence三类型/审批归档闭环见§4.16，忠实维护余边界保留 |
| G19 02§3/5.12 | H03 完成/改期/撤回 | 同项从待办到明确完成，再下一次整理；改变计划重排 | 状态与排期联动按已确认机制；清理软提示观察真实执行，不能当硬gate；未完成不得假完成/强归档 | 代表生命周期已测；完成/整条取消/同lineage done→schedule_update自动pending通过，软提示余链保覆盖边界 |
| G20 02§3.9–3.11/§5.6 | H04 Instant/过去时间 | 明确未来近时提醒＋明确过去的一次时间；自然到期 | 忠实登记时间，不无授权改期；Scheduled for与真实timestamp分离；单次触达、Main主动回应、默认折叠展开保timestamp | 代表链已测；过去补投、未来单次、实时入场/时间分离，报告§4.5 |
| G21 02§3.11 | H05 busy Deferred/ACK | 真实Main正在工作跨提醒到期→后续请求→再次追问 | busy不另抢占Turn；Deferred进入合法后续请求，真实成功ACK后不重复；多项顺序和内容正确 | 代表链已测；busy两项→单Deferred→成功ACK→下一轮不重投，报告§4.6 |
| G22 02§4.1–4.7/04 | H06 开关/计时/Force | 当前round2里本次新会话on/off切换；合法阈值模式 | local off保持原生计时到期但不执行；global off/非eligible不污染；Force走原生合法路径，无旁路立即触发 | globaloff/on、localoff不执行/on新period、普通Auto与Force分支真实已测；Force当次测量/localtimer抑制中间帧未齐，§4.12/21 |
| G23 02§1–2、04 History | H07 历史/边界/压缩后来源 | 长对话中给合成独特事实→压缩→明确历史追问；另一会话对照 | 正式session_history定位正确、无跨Conversation泄漏，rewind失效内容不当现事实；不让模型读仓库补答案 | 跨压缩search/精读与Rewind旧UIDmissing/outside current path真实通过，§4.18；跨Conversation当前事实对照已由收尾当前事实对照补齐 |
| G24 02/04 Persistence | H08 候选→提案→批准 | 合成偏好/规则/技能可复用事项→追问→明确批准或拒绝 | 提案前准确查原话、批准前不持久写；批准后真实原生写入并更新候选，拒绝不写；仅round2测试数据 | 代表链已测；三候选/正式搜证提案/修改不批准/仅Memory执行与Rule Skill拒绝归档通过，初体验偏差保留 |
| G25 06§1.16–1.17 | V17 Files/设置/导航 | 打开允许目录/预览，再返回对话；切Settings | 原生cwd/文件来源；只读预览隔离主动HTML；不因Files失败清聊天；返回目标/草稿保持 | 部分已测；cwd/Markdown搜索/HTML脚本隔离/Back及浏览器导航已测，Files四视口已生效，PDF/Office预览已测，媒体播放/错误等细项未覆盖 |
| G26 06§3.1–3.3 | V18 断连/双客户端 | 本次会话双订阅实时流；Root协调原服务断连/恢复 | 双端同Turn实时；断连仅Composer提示，历史/列表/可编辑草稿保留，Send灰；恢复不重复提交 | 代表链通过；真实65秒断连可编辑/Send灰、自然重连保稿附件无自动Turn，双端F06自然resolve，§4.17；其它网络边界未测 |
| G27 06§1.5/C111 | V19 Clarify/approval | 原生请求选项/Other/多选/取消/重连 | 未合并Clarify缺口如实记录；分支成果不能算5173通过，用户批准合并后真实复验 | 真实4题/四视口/footer/Other/skip/提交与Escape取消通过；F06同request双端自然关闭具体已闭，§4.17；approval未覆盖 |

### Root对口径审计遗漏的补充（执行必读）

- V01：验证首次200后台消息、Show More每次200，工具行计数；与8轮/32条操作回执窗口区别。侧栏按真实日期分组，active→结束不闪，隐藏滚动条仍可滚动，保两分隔与已批准主题控件，不加回已撤回文案。原生AI总结命名仅观察已有能力，不为测试新增功能。
- V02/H04：连续WS时Instant真实节点及时可见且先于其后Thinking，不等整Turn结束；普通流式无人工播放限速/终态堆积。
- V03/V11：收起胶囊仅Total与Hit，Information及其popup消失。
- V13/V14：必须另覆盖**原生普通自动Compaction**，不能由手动或Noting特殊压缩代替；各路径实际进行、完成、Timeline/Context及时更新分别有证据。需临时原生配置时由Root协调并恢复，不造新profile。
- V16：普通notice约10秒自行消失，error保留到手动关闭；测试堆叠、clear、同key新错误不被旧clear误清。记录当前Noting delay真实解析为2秒，依自然timer不另加速。
- H03：secretary_task所有状态均有非空Schedule；取消用整条archive，不能只清Schedule留task；done后改期合法重新激活。对应真实工具轨迹与最终Notebook检查，不能以模型口头确认代替。
- V10/V16/H04：所有人类/模型可读绝对时间到秒、有时区、无小数秒；Instant原定时间与真正抵达timestamp分别可核。内部计时精度不受此展示规则影响。

## 4. 详细场景与执行结果

执行者逐场景追加：场景编号、要求来源、精确版本/环境、合法起点和历史、带前缀完整输入、预期、实际操作/轨迹、用户可见结果、证据路径、时间、通过/失败/未执行/阻塞/有依据不适用。模型非确定性结果以原意、权限和状态不变量判断，不把一次成功推广为所有情况。

**执行顺序与交回指示（Root）：**

1. 先核版本/同profile/实际视口和原生连接，再用V01/H01/V11起步建立真实纵向链；只在Root确认Usage集成稳定后检其整改。
2. 将H02–H05安排为有关联的完整对话旅程，观察Main主动行为、Memo、自然Noting、排期到期、完成/撤回/重排与后续整理。不要直接调内部方法制造成功。时间请求使用原生支持格式，实际改变用户时间必须记录失败/偏差，不能隐藏。
3. 用合法长材料构造H07/V13–V15压缩链；分别记录原生拒绝增长/成功/取消，不能拿其中一条替另外两条。已有受控并发机制测试补充时注明覆盖边界。
4. UI控制/输入/附件/断连与四视口逐项真实操作；渲染/延迟采样记录观察方法，不对未采到的峰值作性能结论。
5. 每个失败先留当前完整证据，集中给Root：用户目标、触发序列、预期/实际、影响、版本及最小诊断。不自行改产品；Root派修复后复验原场景及受影响链，旧失败不删除。
6. 执行者可充分调用真实DeepSeek，不能向其委派源码研究；若实际越界读库/给harness机制建议，记录其行为违背测试指示，并中止该越界动作后继续合法场景。
7. 完整阶段交回：已测场景/版本、失败与未执行、证据索引及后续建议。聊天只给简洁结论；不得返回整包日志。最终全部场景有结论后Root亲审，再派最后静态Verification。

### 4.1 执行准备里程碑（正式Validation，2026-10-14）

执行者：GPT-6.1 Sol/high，独立上下文，不派生。产品只读，未提交，未运行测试套件/build，尚未发送模型消息。只读服务探测5173/53445均HTTP200；CUA绑定真实Codex In-app Browser（browser 3，tab 1），首次页为既有会话 `/chat/20261014_094132_2a63fc`。此次只用于确认连接，不把其历史当本次结果。`visible:true`在子Agent线程明确不支持；改用内置浏览器后台模式成功，未使用Chrome。

四视口能力已验证：调用正式`viewport.set`后，用只读页面`innerWidth/innerHeight`分别得到1440×900、1024×768、390×844、320×568，全部与请求一致，最后`reset`。此结论仅证明四尺寸实际可设置，不等于布局/交互已通过。准备证据：`.hermes-dev/round2-verification/formal-validation/preparation.json`。

初次观察版本BE cb05c0671c、FE ab1f4c4；Root随后交付稳定源BE `ea2ab483999f9230abfd794bdde2ea3fe2468cfe`（产品同cb05c）与FE `833ef31468dbc73e0f25961cec1fe81399ba6111`。Root协调原53445/5173重启中；收到运行完成通知后核实际版本、刷新页再开始。当前profile原值：DeepSeek `custom/chat_completions/deepseek-flash`，supports_vision=true、context_length=262144；Noting enabled=true、idle_delay_seconds=2、特殊自动选项false；compression enabled=true、threshold=0.8、idle_compact_after_seconds=0、timezone=Asia/Shanghai。未读取/记录凭据，未修改配置。

已按索引核读AGENTS、CLAUDE恢复段、套件与真实验收技能、Snapshot Index/baseline、原始反馈导航，以及06产品/验收要求、02身份/History/十类型/Memo/Schedule/Trigger/Profile/Wrapper/当前Target/验收条款、04仍适用Proposal与非破坏要求、01继承原则。旧Notebook人类输出入模型的条款已被当前02末尾批准边界和06显式Web增量覆盖，不能误用旧条款。只读plan统一证据索引用于避免重复重测试，未根据开发报告降低本报告预期。

### 4.2 完整执行批次与子场景

下列为执行细化，保持Root全部27组目标/预期；每项实际执行另追加完整记录，不将计划记作通过。每条模型输入都使用§2原文前缀，slash走命令入口。合成事项用“FV-A/FV-B/FV-C”区分；所有绝对时间现场取当前时间并写到秒、带+08:00，避免准备时排期已经失效。

| 批次 | 场景及子场景 | 合法起点/具体用户旅程 | 观察与证据重点 |
|---|---|---|---|
| A1 首条纵向链 | V01、H01、V11、V16、V10 | New Chat先存草稿并reload确认无空Session；首次Send表达“我将在周五前完成合成青桐提案，你今晚帮我检查提纲，遇到缺信息先问我”；逐轮追问“你会怎样跟进”“下次Notebook不能漏哪件事”，自然等Noting；总计至少3个真实完成Turn | 主动秘书行为、实际noting_memo、原生2秒deadline/active/终态/Framework、有效Snapshot与Memo消费；Usage各字段idle→active→结束对比、Session/Latest独立、Total/Hit与原生读数；侧栏无整栏加载闪动。不得只依据Assistant承诺 |
| A2 同会话语义展开 | H02、H03、H01、V10 | 用同一合成项目先陈述commitment、明确reminder、秘书未来task、watchpoint(until)、decision、未决question、带不确定性的insight，再独立提供偏好/规则/可复用workflow线索；通过追问确认含义，自然整理，随后完成/撤回/改期与再一轮整理 | 四区十类型各有合理代表；允许模型不对无意义语句建条目；未完成不得假done、已完成不造新流水账；秘书task所有状态非空Schedule/明确mode；取消整条archive、done改期由schedule_update自动激活；新done与原done两轮软提示效果，失败留实际工具链 |
| A3 提醒完整旅程 | H04、H05、V02、V16 | 一条明确未来近时instant、另一条明确过去的一次绝对时间；等自然Noting登记和5秒scanner；另排busy到期及两个deferred，真实Main长工具工作跨due→后续模型请求→再追问 | 原定due保留，timestamp是真实抵达；instant先于Thinking及时显示、默认折叠展开保timestamp；busy不排第二Reminder Turn；deferred单批顺序/内容/成功ACK与下次不重投；只读原生pending/registry补证，不直接写库 |
| A4 Candidate闭环 | H08、H02、V10 | 产生真实memory/rule/skill候选后由原生命令/propose-persistence提案；讨论修改而不批准；明确仅批准一项测试memory、明确拒绝其余，再自然整理 | 主模型实际session_history查原话及后续更正；提案/修改前无写入；批准范围内在round2测试HOME原生持久化、再读取实际产物；Noting只在执行/拒绝后归档，不以批准代替完成；禁止Nowledge或工作区外写入 |
| B1 长历史与手动 | H07、V13、V12、V01、V15 | 新建FV-B，发送有业务意义的长合成资料（独特校验事实置于较早位置）并继续对话；/compact真实执行；分别捕捉过程和成功，另短材料捕捉合法would_grow；进行中的独立取消子场景；结束后跨压缩精准追问早期事实 | Context环原地loading、popup仅有效Cancel、成功原生summary无reload立即出现/折叠展开；would_grow无伪摘要、cancel不Stop Main、不假回滚；实际session_history search→precise read定位原文，UID/Ref不漂移。冷恢复只显示可靠计数，未知不猜 |
| B2 两自动路径独立 | V14、V13附普通自动、H06 | Root协调同profile临时原生配置；先特殊Noting with compaction，用长资料真实Main结束→自然Idle→特殊Profile→compact_parent；恢复后另由普通Hermes自动阈值触发压缩 | 不能用手动/特殊/would_grow互代；实际Profile/工具/Parent最终completion/Timeline/Context各自采证；Noting Finish不是Parent压缩完成；原生普通自动路径在本次入口实测，不引用旧隔离链冒充 |
| B3 开关与Force | H06、H07、V16、V10 | 本次有Snapshot且Memo空的会话/noting off→真实Main→timer到期→/notebook与History读；on后观察新合法period；Root协调global off/on窗口，观察暖会话下次Main工具/Prompt；Force依原生合法阈值与充足真实材料触发 | local off不取消timer且deadline仅一次抑制；global off Orb隐藏、Notebook工具不在、History仍在；复开不补执行已经处理的off period；Force正式入场/dispatch/finish与不阻止Parent自动压缩，阈值能力失败不伪造成功。辅助runtime不适用UI时注明机制证据边界 |
| C1 真实流与控制 | V02、V04、V05、V06、V07、V11 | 新建FV-C，通过安全terminal命令做两段可观察等待/整理；工具Running时空Composer焦点Enter/Escape，另轮Stop按钮；两个带前缀Steer、撤回一条并覆盖草稿，消费另条；再一轮两Pending+未发附件Interrupt；Reply临时隐藏→退出/Cancel→单红窗确认→reload | Thinking/参数/工具/正文及时并按真序，成功与exit非零Failed各一例；Stop后无旧输出缓播、无下一Prompt；Pending消费即时真实User且同插入点单行；Interrupt只剩Pending一次；附件/草稿保留；Rewind正式UID目标正确且reload不执行旧armed状态 |
| C2 输入与附件 | V08、V09、V04、V06 | FV-C或独立附件会话，选择图片（新形状+校验数字）、普通文本/PDF、同名不同内容；reload草稿→发送→追问模型实际内容；选择/粘贴/拖放子入口；预算累计越界/移除释放；发送中Cancel保原snapshot | 选择零上传、发送同runtime、图片真实像素/请求无辅助文字替代；文件模型读出合成标记、历史仅chip，长名title/ellipsis；500MB最大完整传输复用适用机制证据但UI累计预算须本次观察；未知admission不重发、不假cancel |
| D1 导航与恢复 | V17、V18、V01、V12、V10 | 会话/New Chat未发草稿→Files多级目录/常见预览→右上Back to Chat；浏览器Back/Forward和reload；双IAB订阅同本次会话；Root协调原服务断连/恢复；既有长历史Show More | 三主屏/移动Sidebar位置、真实cwd面包屑、HTML只读隔离、返回草稿/位置；断连仅Composer且可编辑、Send灰、列表历史/临时Notebook保留、token换新自动重连不重复；首次200/追加200按后台行，不按可见card数量猜；历史分页与8/32回执窗口分开 |
| D2 四视口/主题 | V03及V01–V19相关呈现 | 每个指定尺寸实际set→读innerWidth/Height→New Chat/Conversation/Files/dialog/Orb/Usage/多行Composer，light/dark/system各代表；真实短稿→多行及New Chat→Conversation对比 | 截图+DOM几何同时证明实际尺寸；底边共用、上长、两胶囊悬浮且仅Total/Hit无Info、User12%/3%与Assistant4%/10%、无横溢；侧栏可滚无滚动条、两分隔与紧凑主题；Orb原短弧/finished熄灭/收起末帧，不仅最终截图 |
| D3 未合并依赖 | V19 | 正式5173检查现有原生clarify/approval请求的实际入口；不进入独立worktree冒称正式通过 | 选项/Other/多选/取消/重连按实际原生契约观察；当前未合并缺口明示，用户通知合并后复验；不擅自合并，不用普通模型问答替代原生clarify |

交回按A、B、C、D完整批次集中，摘要≤800字，失败附最小触发/版本/证据，Root可派修复。修复只复验原失败及实际受影响链，旧失败保留。长文本、附件和终态原始证据各写独立小文件，避免整历史/无关用户日志。

### 4.3 所有反馈→场景映射

| 反馈编号 | 本次场景 | 实际检查点 |
|---|---|---|
| F01 | V04/V06/V05 | 工具Running时空框Esc和Stop按钮；Interrupt独立 |
| F02 | V04/V07 | 原生Cmd/Ctrl+Z文本栈，不回滚已发/文件 |
| F03 | V02/V06 | 长Thinking/参数/正文、终态后无陈旧播放积压 |
| F04 | V01/V03 | active/end Sidebar不闪，真实分组/两分隔/主题 |
| F05 | V01/V03 | 滚动有效、无可见滚动条、撤回标签不回来 |
| F06 | V10 | 各slash Tab补全、统一文本换行 |
| F07 | V11/V03 | idle/active/end有效数值，New Chat两卡不显示 |
| F08 | V11/V12/V18 | 按字段同Session/view保值，断连/未知不清空 |
| F09 | V11 | ≥3真实完成Turns/Latest，非模型calls代Turn |
| F10 | V11/V03 | 收起仅Total/Hit、无Info/popup，ratio真源 |
| F11 | V11/V12 | 冷Context未知与有效内存保留，来源不足不造API |
| F12 | V03 | 四尺寸/两主屏/多行上长共底边 |
| F13 | H04/V02 | 真实Instant在后续Thinking前即时出现 |
| F14 | H04 | 过去一次due不丢，due与入场timestamp分别核 |
| F15 | H04/H05/V16 | Instant/Deferred/Framework真实节点与折叠 |
| F16 | H01/H02/H03 | 秘书未来task Schedule/mode，已完不建流水账 |
| F17 | H03 | 所有status非空排期、cancel archive、done改期 |
| F18 | H01/H04/H02 | Memo桥接，Main不写Notebook/Cron/研究代码 |
| F19 | H02/H03 | 忠实与2+N软维护，非硬gate |
| F20 | V10/H02/H07/V13 | 人类notebook不进入模型/Noting/summary事实，不重复造条目 |
| F21 | H04/V10/V16/H07 | 时间到秒+时区，原定与抵达分离 |
| F22 | V16/H01 | 2秒自然timer/真实终态/失败notice、旧非法库不改 |
| F23 | V13/V14/V15/H06 | 三压缩路径分别过程/最终及时显示 |
| F24 | V16 | 普通10秒、error手关、堆叠/同key替换/clear |
| F25 | V01/V18 | 首次200+200、刷新恢复与操作窗口分离 |
| F26 | V01 | 观察真实原生自动title；不新增命名功能 |
| F27 | V19 | Clarify正式入口依赖，待用户合并 |

Root审计补充全部已纳入对应子场景；没有建议删除/降低任何场景。另将06原文明确的选择/粘贴/拖放、Browser Back/Forward、未发二进制reload、读旧历史不强制底部、Files HTML隔离补为既有组的子场景，属于原规范完整执行，未扩大产品范围。

### 4.4 需要Root协调的实际运行窗口（尚未实施）

1. 稳定版本重启完成后释放；开始前只读核PID/命令的profile路径，保存精确版本与两规格SHA，刷新IAB。旧页/旧记录不作新版实测。
2. V14特殊路径建议只在FV-B待测会话已完成长内容且全runtime无活动Main/Noting时，把`noting.auto_trigger_compaction_after_noting.enabled: false→true`、`threshold_tokens: 原未配置→1`，让下一真实Idle合法选择特殊Profile。取得真实Parent最终completion后恢复原键/值（删除原不存在的threshold键）。配置全局影响其他eligible会话，操作由Root统筹，执行者不自行改。
3. 普通自动路径、H06 global off/on与Force另需Root给明确原生配置窗口。当前262144×0.8自动阈值较高，不能用手动替代或伪造token。建议普通自动在Noting global off窗口调整原生compression threshold到真实输入可跨越的值并恢复；Force仍需合法resolved threshold/context，不能用无效小context绕过64K/128K能力边界。具体键值须先从原生配置事实确认并由Root决定，当前不执行。
4. V18原53445停止/启动由Root协调，确认全部活动工作空闲；保HOME/config/state.db同一，不开新服务。V16 notice的native clear/同key重放若无合法产品入口可稳定造成，先记录能力/证据不足并给Root最小需协调条件，不自行伪造事件或降低要求。
5. V19等待用户合并许可；即使其它27组执行完成，未合并正式缺口仍如实报告。H08只批准本测试profile既有原生持久化能力内的合成内容，不授权工作区外、Nowledge或生产数据写入。

准备历史判定：准备完成。**Root已核重启就绪并批准A–D批次，现已释放真实执行；当前进行中，无整轮通过声明。**

### 4.5 A批实际记录（进行中，不推广为整组通过）

环境：BE ea2ab483999f9230abfd794bdde2ea3fe2468cfe / FE833ef31468dbc73e0f25961cec1fe81399ba6111，原round2、IAB tab1。正式会话 `20261014_162414_e964a3`，Conversation Ref `conv_9ef0655053bb476886da620fefebba63`。完整原文输入分别保存A1-input.txt、A2-input.txt、A3-input.txt、A4-input.txt，均包含逐字前缀；起点New Chat，完整历史从第一条合成项目输入真实建立，未直写DB。

- **V01子场景**：New Chat未发草稿`FV-A 未发送草稿·校验73319`，reload初始重连后文本恢复；未导航创建空会话的绝对计数本次尚未取得，不以列表外观冒称。首次Send只建立一个正式可见会话，新原生自动标题“安排青桐提案提纲检查”实际出现，非手动命名。证据A-newchat-draft-reload/ready.dom.txt与A-newchat.png、A1-start/live-1.dom.txt。连续对话部分真实完成；历史/live重复缺陷FV-F02阻断组通过。
- **H01子场景**（A1 16:24）：表达提案承诺、次日晚提纲检查、预算未知、只接受未来安排。Main直接noting_memo.add（index1）而非Notebook写入/Cron/源码研究，随后明确跟进与所需材料。Noting自然完成ordinary Snapshot；A2更正“只指出问题、不给改写稿”及watch/decision/question/insight后，Main实际replace/list，自然第二Snapshot完成且Memo清空。A2-db.json保存Main和Child真实工具轨迹/两Snapshot/Memo归档；两完成Framework可见。该代表纵向链符合，其余Memo失败/在途改写/并发与权限仅机制证据可补，未冒称全量通过。
- **H02子场景**：A2当前Snapshot snap_b560819abc4c48d0b0f97e68ce923a4d提交16:28:55+08:00，实际覆盖user_commitment、user_reminder、secretary_task、watchpoint、decision、open_question、formulating_insight；预算保未知、insight保forming及confirm/refute，未猜预算。秘书task有非空once Schedule与instant mode。Persistence三类仍待独立输入。不强制将每条话建条目。证据A2-db.json、A2-notebook-complete.dom.txt。
- **V10 /notebook子场景**：正式textbox输入`/notebook`+Enter，异步显示四分区可读卡，Schedule与状态分开，No entries明确，无Anchor；随后A3真实User在卡之后。异步处理前一次过早观察尚无结果，随后误试Send时按钮已disabled（未产生额外提交），最终结果已保存。不能把单次即时快照无结果当命令失败。人类-only模型/DB过滤仍待后续核；FV-F02重复正文已单独记录。
- **H03子场景**（A3 16:33→16:34完成）：用户确认合成提案与提前线下检查已完成/验收通过，17日观察未完，预算2000元确定。Main先对已消费Memo index1做replace失败，真实Failed卡/Unknown Noting Memo index；随后add成功恢复，没有直接改Notebook。Snapshot snap_2f0bff135ef74604b70d459618feb976提交16:34:57+08:00，commitment.done、task.done且保原非空Schedule、未完成watchpoint.watching和新task.pending、预算decision、question.resolved，实际工具归档过程另在A3-db。Noting reason称取消/归档旧提醒与task，不能仅用reason当最终active视图，需核生命周期archived标识及人类结果。A4已发送同项重新安排21:30/取消17日观察，等待真实完成，尚不判改期自动激活通过。
- **V11**：3个真实Main Turn均完成，首轮Session/Latest有效；第二轮active保首值。Session新有效saved计数未替换FV-F01，第三轮native total208,669、calls8、Context11%仍同一旧UI Total48,418。Latest原生partial/null保最后已知属授权来源边界，不猜数。Root只读取证source.json时刻08:32:38.116Z与我的A2-native-rpc分别保留，修复后原会话复验。
- **V16子场景**：三次自然ordinary Noting均实际completed，Memo为0，Parent有真实Framework；未派内部方法触发。A1-first active、A2 active、A3 idle在DOM可见。2秒配置已解析/原值核，但准备未采到所有倒计时与finish动画中间帧，不能以最终idle代替动态通过；后续继续采样。失败notice与堆叠/clear仍未执行。

#### A4–A7与H04、四视口补证（833ef，修复集成前安全窗口）

- A4完成：active人类/Store边界必须过滤生命周期archived位。此前A2/A3/A4-db中的`current_entries`是Snapshot payload id的原始审计映射，含已归档项，**不能当当前可见Notebook**；工具输出新增`current_entry_records`与过滤后current_entries，证据A4-filtered-db.json。实际原21:30新task.pending/instant排期唯一有效，17日提醒/watchpoint/task已archive，已完成承诺未重开。Child实际archive4项、create新的秘书检查；因旧done任务在A3已经按取消意图归档，这次是新建，**未证明同一现存done entry的schedule_update自动激活**，需另合法场景，不冒称该分支通过。
- A5输入16:41:39：未来16:47:39“青桐喝水76183”、过去16:39:39“补投复核64217”，各一次通知、无项目工作。两条分别自然Noting登记、自然scanner投递，过去卡真实timestamp16:42:09+08:00与Scheduled for16:39:39+08:00分离；Main直接提醒、未改约，默认collapsed后展开保timestamp。第一未来实际timestamp16:47:42+08:00、原定16:47:39，单次真实节点/响应。证据A5-input、H04-times、A5-idle、H04-past-expanded、H04-future-first-visible等；后一个文件名指首次**被执行者观察**，取证时08:48:11Z Main已结束，不能证明实时入场。
- A6输入再次设未来16:50:49“及时到达58426”；界面waitFor虽传60s实际约3s timeout，随后工具间隔再次错过Main进行期。H04-third-before-due文件取证实为08:50:56Z，已3个Instant，**名称不能冒充到期前**；保留失败取证尝试，只支持该提醒最终结果，不算动态证据。
- A7输入16:51:55左右，原定16:52:35“入场顺序92735”；单次CUA连续合法locator.waitFor监测（44.9s）在08:52:39.886Z捕到第四Instant真实卡，此时Stop存在、后续Thinking/Assistant尚未出现。后续Thinking与Assistant才出现，展开卡为timestamp16:52:39+08:00、Scheduled for16:52:35+08:00，真实模型直接提醒。H04-fourth-live.{json,dom.txt,png}与H04-fourth-final/expanded支持**本次连续WS下提醒在Turn结束前/Thinking前及时入场**；不宣称量化网络SLA。A7-safe-db含4个不同通知的一次性投递/终态事实，尚未结束的未来秘书检查单独留待H03复验后正常取消。
- 四尺寸Conversation实际宽/高全部生效，无文档横溢，读取父容器/气泡几何证User12%/3%、Assistant4%/10%。D2-conversation-geometry及四图。多标签后viewport只作用当前选中tab2，第一次对tab1的D2-newchat-geometry四次actual均1280×720，**无效尝试保留，不能计通过**；改在tab2真实New Chat完成D2-newchat-verified-geometry四尺寸，短/十行底边均视口高-36，内容上长，两主屏底边与先前Conversation同值，四图。320侧栏展开、Light/System/Dark选择实际可用并恢复Dark，图D2-sidebar-320-*。真实软键盘/相机/系统侧滑未覆盖。
- V01草稿跨路由：tab1会话未发“FV-A 独立未发草稿83172”→New Chat独立“FV-N”十行→回原会话准确恢复会话草稿；没有发送这些草稿。V04实际pressSequentially输入ABCDE再Meta+z，值`FV-UNDO ABCDE`→`FV-UNDO ABCD`，原生文本撤销实际生效；仅此编辑子场景通过，IME/活动键位仍未测。
- 双IAB订阅：tab1/tab2同Conversation，A6真实输入/回复/Framework均更新到两端；A6-main-live/second-client-live记录两客户端，未量化活跃流式过程，待C批长工具同时观察补证。tab2冷Usage依旧unknown属于FV-F01，不能当新的独立计数来源。

2026-10-14 16:55:20+08:00 A7-safe原生只读确认当前Main idle、Noting idle/tasks0、compaction inactive，Memo0、11个自然completed Snapshot。通知均已结束，没有本次通知遗留；仅明晚21:30秘书检查未来Schedule仍保留用于H03后续复验。Root要求统一前端修复集成，执行者停止发下一模型Turn等待Root放行；不自行重启。其它原有用户会话/事项未处理。此为安全窗口，不是终轮完成。

### 4.6 b99651c正式复验及C1/C2、H05结果

BE ea2ab483 / FE b99651c53ca7792e8631844fe363cdb168531912；同FV-A Conversation/原profile，两IAB正常reload建立新Controller，无后端重启或配置变化。所有完整消息在F01-F02-retest1/2/3/4-input、H05-register-input、C1-long/steer1/steer2-input、C2-input/steer1/steer2-input中，逐字前缀保留。

- **FV-F01具体缺陷复验通过**：冷恢复取得Session575195/96.4%，新真实Main连续更新675581→850101→885661，活动期间不清空。F01-b99651c-session-total实际Total885661/Input23930/Read855680/Output6051/Turns15，native F02-retest4-native-rpc一致；Latest70968/Input513/Read70272/Output183/Calls2与原生完成receipt一致，非Session差分。再跨C1/C2真实Loop，native total增长到1146626。该缺陷可关闭；V11整组的断连/0/冷未知与切会话分支仍待完成，不把缺陷修复扩大为全组通过。
- **FV-F02首修仍失败**：第三复验要求新增风险段，Main实际Memo；同次CUA在新自然Noting active时发送第四sleep45，09:05:08Z工具Running且Noting active，09:06:33Z真实最终正文/工具又重复。源证据F01-F02-b99651c-overlap-events.jsonl完整1秒只读轮询窗口（cursor4183→4443、260帧、进程正常退出），根报告问题表保首修失败，不降低标准。另一首轮observer cursor3416→4183/767帧也正常退出；无继续自有观察器。只读原始帧不替代UI重复实见。
- **V02/V18子场景**：sleep45真参数/真实Date返回17:05:53、exit0；工具未完时两个订阅端都呈Running/Stop/同统计，F01-F02-retest4-running及other-running。同一tool单卡Parameters/Result，保持Collapsed实际aria=false；真实Memo Unknown index已标Failed且恢复add，不把失败当Success。V18双订阅活动代表链完成，断连/重连仍待Root服务窗。
- **V04空Enter**：sleep45期间空Composer按Enter，User数不变、terminal仍Running、Stop保持，V04-empty-enter-active.{json,dom}；C1有一条仍Pending时清空框Enter，Pending1/Interrupt保持且未发新Prompt，C1-empty-enter-pending。Enter两个取消动作分支的正式no-op实证；Escape/按钮Stop/IME/附件取消仍未执行。
- **H05完整busy/ACK代表链**：H05两项原定17:11:51，正常UI通知请求→Memo→自然Noting完成Framework（H05-register-completed）；C1亲自sleep120于17:11:35运行，到期两项在H05-busy-db都是system_reminder/pending且既有Instant总数仍4，未抢第二Turn。工具17:13:35真实结束，同一Turn下一模型请求进入一个Deferred carrier row1141/UID `2428908bd432483bb5439dbd4f177384`，内容包含两项，模型实际回报两条；H05-after/C2-end两occurrence均delivered、各有acknowledged_at且相同carrier UID。C2后全本会话仍只有该1个Deferred row，模型明确两项是此前收到的旧提醒，无新投递。支持正常成功ACK后不重发；provider失败/进程crash的at-least-once分支仅既有机制证据，本次未主动造故障。
- **V05撤回与消费**：C1 terminal真实120s期间两个带前缀Steer均正式接受，独立Pending2；给Composer另写无发送草稿，再withdraw第二条，确切回填全文与第二输入逐字一致、只剩Pending1（C1-withdraw.json）。清空后Enter不Interrupt；首tool完成后第一条成为一个真实User，未撤回者正文存在、已撤回第二条不入durable路径。C1首次消费观察09:13:44Z已Main完成，只支持终态，不能冒称消费中间帧。
- **V05双条同点合并/即时正式User**：C2要求两次独立sleep30、sleep45，第一工具Running时接受两条Steer，Pending2；同次CUA等待Pending身份消失，09:16:08.944Z捕到一个真实User含两条按原序合并的全文，Stop仍在、模型/第二工具尚未完成，退场副本已无withdraw权限；09:16:38.332Z再次实见Pending0、第二terminal Running1、真实合并User在其前（C2-merged-user-next-tool-running.{dom,png}）。不是等Turn完才补行；C2-end真实rows继续核唯一UID，禁止按正文去重。Interrupt及附件隔离另待专场。
- **资源/环境**：C1-H05事件观察器cursor4745→5076/331帧在09:15:53Z自然退出；没有全套/build/新服务/用户目录配置。fixture只在白名单fixtures生成小文本和新像素PNG（橙三角/蓝矩形/68427），尚未上传。当前Future残留仅明晚21:30秘书检查，归本次FV-A；生命周期后正常UI取消，不处理原用户事项。

### 4.7 Root正式B批窗口交接（准备历史，B1结果见§4.8）

唯一当前B批操作依据为plan.md末节「Root正式Validation B批执行指示」（本次实际约364行起）。§4.4早先配置建议仅为准备历史，**已被Root正式指示覆盖**：原生K=1000，Force候选ctx139264/ratio.75的reserve66000、Force73264，旧67584/71680算术不适用；小窗口ratio .08会被抬至.75，普通Auto必须使用既有threshold_tokens=20000；特殊与compression的原threshold_tokens均实际null，恢复null，不删除。

2026-10-14 17:19:33+08:00 environment/validator-b1-ready.json：全runtime仅FV-A b03b78a2，Main idle、Noting idle/tasks0、compacting=false；SHA4bc6576d…/DB inode42327472保持。C2-end-db最后Main结束17:16:58+08:00，due17:17:00，trigger_produced17:17:00（内部原精度保留），deadline已处理，无未处理Idle timer；18自然Noting全部completed，Memo0。native context38310/262144，在B1要求10000≤usage<196144区间。执行者暂停下一模型Turn，待Root释放配置operator并交回实际解析后再开始B1，不能自行改配置/重启；已有真实材料充足，若压缩would_grow会追加有意义合成正文并另合法period取成功，不能冒称完成。

### 4.8 B1特殊压缩成功与V15独立真实取消（7ea5e64）

唯一操作依据仍为Root plan.md末节正式B批指示。BE ea2ab483 / FE `7ea5e64555bd41964cee4b8ffb4de60926fc1b87`；两IAB已正常reload建立新Controller，之后本节取证未reload、未切profile、未直写DB。Root配置operator通过原生CLI仅修改特殊threshold_tokens=10000(int)、enabled=true(bool)，configuration_failure空；原global=true、context262144、ratio.8/capnull均不变。环境before/between/after与b-config-b1-result.json保存在environment；实际配置SHA f64d075517316888e899590d684ace4e524f9d34dd7956de064227a0a6aaead2。此配置不是改开关即触发，以下由新合法Main→Idle产生。

- **完整输入/合法起点**：同暖FV-A空闲起点，B1-input.txt逐字前缀+真实合成业务资料：预算2000拆材料800/测试600/预留600，三里程碑需求范围确认/可用演示/验收归档，用途与输入/预期输出/判定式验收，三风险/对应应对；保明晚21:30检查、不执行项目工作。Main实际noting_memo.add成功，简述正确；没有模型研究源码、另派Agent或执行项目工作。
- **V14特殊链核心成功**：09:28:31.778Z真实界面Secretary active与Context:Compacting（B1-first-compacting-observation.json/dom/png），Main已回复。随后未reload出现Compaction卡，默认aria-expanded=false；展开实际summary全文见B1-real-summary-expanded.dom.txt。Child Snapshot `snap_dedf569174a748da8072e0b029e7d142` trigger=idle、runtime_profile=NOTING_WITH_COMPACTION，真正终止类型compact_parent；工具实际admitted/native_safe_admission，usage_tokens39440≥10000且<196144、threshold10000。Parent operation `9404b687b1a84c9ab596b11e1158df58` 实际state=completed/activefalse，session.usage compressions1。真实持久summary row1195，UID `b99d45b960724dea84a2f6d0a64c4435`，_compressed_summary=1、正文6958chars。不是would_grow、不是取消、不是只看Noting完成。证据B1-completed-native-rpc.json、B1-completed-db.json、B1-summary-rows.json、B1-after-natural-compaction.dom/png。
- **真实权限偏离/保护**：特殊Child在notebook工具写入/show之后，错误尝试terminal执行finish_noting；实际被拒绝“Noting runtime denied non-whitelisted tool: terminal…Do not retry terminal.”，然后改为正式compact_parent {}成功。保留真实模型偏离与白名单拒绝，不能只报最终成功；未执行那个terminal命令。Main无此越界。
- **来源与取证边界**：B1-special-events.jsonl只读1秒轮询09:27:33→09:30:33自然结束、cursor5427→5721、294帧，完整保存；其中无单独compact事件，不能伪造WS过程帧。浏览器中间态/真实summary/native终态共同支持本次完成。首次捕Compacting后分开点击太晚已结束，未获该特殊过程弹窗，不能以此称弹窗已测。结束UI15%/Context popup39440为上一有效provider占用；当前native context_breakdown为local_estimate46189/18%，来源不同，未猜成新provider值、不直接判差异为缺陷。**此项仍是V14未闭合观察**，保旧有效值不能证明压缩后Context已及时reconcile；后续三路径分别保存显示字段/实际来源/刷新时点，Root按既有原生Context契约审查。
- **V15独立取消作用通过，通知为非阻断体验观察**：17:38:34暖同会话在真实UI输入`/compact`+Enter，立即看到Context:Compacting并打开过程popup；V15-manual-process.dom/png仅有Cancel Compaction按钮。点击正式按钮后Context恢复15%且Main仍idle；原生operation `6894fd62df5f496b9dea9651ebfeb489` state=cancelled、activefalse，compression仍1，没有新增summary/新Main。V15-manual-cancel-native-rpc保seq5722–5726及具体终态。取消起效与此前B1成功独立判定。UI notice实际为“No changes from compression: 92 messages Approx request size: ~45,357 tokens (unchanged)”，没有表达cancelled；FV-F03起初仅候选；Root只读审查后确认“No changes”为原session.compress的native summary原样显示，06§2.5未要求成功取消特定toast，因此转为**非阻断体验观察：取消反馈易误读**。实际本次Cancel RPC返回帧未采，现行cancel API明确outcome属于Root源码事实，不能冒称本次原帧已捕。保留原文，不改native文本或新增产品能力。截图V15-after-cancel-click.png及同DOM。未把无变化通知当would_grow成功或取消失败。
- **安全交接**：正常Escape退出popup并清空未发slash（B1-safe-boundary.dom.txt）。09:39:34Z environment/validator-b2-ready.json仅runtime b03b78a2，全Main idle/Noting idle/tasks0/Parent inactive；同native秘书next_idle=absent、Memo0，配置hash/DB inode42327472不变。执行者停止下一模型输入，Root协调恢复特殊false/threshold null，再B2 global off/原生cap20000。未来自建21:30任务暂保用于H03同entry完成→改期；最终正常UI关闭。F02第二修原overlap还未复验，不以本次单轮无重复称关闭。

### 4.9 B2暖global off首轮（进行中，普通Auto尚未触发）

Root正式配置指示落实：B1原值逐字/hash恢复，再先global=false于09:42:02Z原生回读，最后ratio=.08/cap20000，仅这三键变化；证据environment/b-config-b2-result.json，配置SHA9c5d71057c6e748c2dc26d1e034f958fe8fb9f3f4ed07913af1f56113f74ed40，operator原生解析Auto20000，Force threshold_below_64k仅off下预期，不算Force能力通过。服务/DB/暖runtime b03b78a2未变。FE仍7ea5e64。

- 正常IAB reload首帧仍Disconnected/空placeholder，仅连接过渡；待实际heading恢复才输入。B2-global-off-ready-complete.dom.txt真实Orb隐藏。旧历史/Compaction卡仍保，未创建冷会话或后端重启。
- B2-off-input.txt逐字前缀，真实请求三行预算分项/三里程碑/四检查要求，不新增安排不执行项目。17:44实际Main返回正确三行，未调Notebook/Memo/terminal，旧摘要预算未知被较新2000原话覆盖，没有恢复旧取消的安排。
- 关闭行为实际成立：B2-first-native-rpc秘书global_enabled=false、next_idle absent/Memo0；B2-first-db共19Snapshot（与B1相同，无新Noting）。原生session.info seq5975 system_prompt无Noting Memo字符串，seq5726旧on帧有1处，真实下一Main工具/提示退出对应新增路径；不以raw config代替。
- **普通Auto未触发，不能判通过**：同次CUA在发真实输入后连续15×合法waitFor(3s)约45s，始终未见Context:Compacting（B2-auto-process.dom/png实际为终态，文件名不冒充过程成功）。原生provider context_used37635>20000，context_max262144、14%、sourceprovider_usage/estimatedfalse；session.compressions仍1、compaction_state仍V15旧cancelled operation，无新summary。B2-native-auto-events.jsonl当前窗口未见compressing/compacting status。Root已接实际事实核暖实例阈值生效/前取消抑制边界，执行者不读产品源码/不自行改配置。
- 活动到终态Usage有效增长1263299，Context旧冷Unknown→本轮14%与provider37635一致。此刷新证明下一真实receipt有效更新，不能追认B1压缩完成时15%已经及时reconcile。

#### B2第二轮正式工具检查点：原生普通Auto真正成功，UI重复仍open

Root提供原生只读检查时点依据environment/b2-auto-trigger-review.md并释放真实预算计算；配置/7ea5e64均不变。B2-next-tool-input.txt含逐字前缀，仅要求一次terminal Python核算800+600+600与600占比、禁止读写文件/提醒/其他Agent。17:51真实tool_id `call_00_cr0cN86YpTXrOcXBKIvf2358`仅一次，结果2000/30.0/exit0，Main正确回报，不研究源码。

- **普通Auto真正成功**：B2-tool-checkpoint-events.jsonl（09:51:19→09:54:20自然结束，cursor5976→6079，103原帧）seq5978原生Preflight ~38131≥20000，5979compacting，5981compacted/continuing turn，5983compression2；Parent operation `a4d64f452ae1468ea4c69ee93a828e98` completed。实际summary row1287 UID`76a0aa0cb3854a63b3716372016c8b12` 8229chars，UI无reload出现第二张Compaction卡、默认两卡均collapsed；可展开实际summary全文，B2-summary-rows.json/B2-real-summary-expanded.dom/B2-final-summary.png。正式开始采用新cap已真实证实，不以第一轮没有后检查点反称配置失效。
- **UI过程漏采**：Send之后17次合法waitFor3s没有捕到Compacting；原生早期过程已先完成，B2-tool-auto-observation.json compacting=false仅表示执行者采样未见，不等于未触发。此普通路径popup/原地过程动画未覆盖，不能用B1/V15中间态替代。之前即时commentary“未捕普通自动过程”随后以真实原帧纠正，保留观察边界。
- **完成后仍超cap与后续警告独立**：provider本轮最新37617/262144/14%、sourceprovider_usage/estimatedfalse，与UI14%一致。seq6045原生warn“Context…37636≥20000…blocked(ineffective)”是成功后后续检查事实；20K低于固定工具/系统开销可能不能缩至cap，不能据此否定先前success或强行要求≤cap。F04压缩完成接缝的Context及时性仍待修复，后续新receipt更新不追认完成瞬时正确。
- **F02第二修实际受影响链仍失败**：Thinking Complete/terminal→Thinking/terminal→唯一final，同预算terminal两个真实DOM section均visible=true/ariafalse，controls _r_gi_与_r_gl_；完整副本F02-second-fix-B2-dom-tool-copies.json、B2-tool-auto-observation.dom/png。原生只1tool-call，tool_call_uid`01406b41a75f4fa2ade0d18c3f7e3b62`，原生source1378 assistant UID0ed849afbc384effa57c57c6f25bf5f5、1379tool UID31d8311a48bb4b51bc72023f506aba1a；User1377 UID734539a6905a4af2819e275781774a5a、final1380 UID6c4a1f2ba66b4fdb870e911478383c49。seq6077 persisted_turn.complete=false、source_boundary prefix/compression_unchanged=false但all_rows_committed=true。实际完整终帧与只读源rows另存F02-second-fix-B2-persisted-turn/source-rows.json，给Root修复owner，不伪称原overlap同场景已复验。
- **off安全交接**：Snapshot仍19、Memo0、next_idle absent，无新Noting。09:53:40Z environment/validator-b2-off-restoration-ready.json全runtime Main/Noting idle/tasks0/Parentinactive，hash/DBinode仍同。除FV-A另有原会话0273f36f idle（执行者未打开/发送该会话）。模型暂停，Root随后恢复ratio.8/capnull且保持off、待回读再释放暖追问，不能自行恢复或切B3。

#### B2 off下恢复阈值后的暖Main

Root operator按ratio.8→capnull原生CLI恢复，global仍false、specialfalse/null/context262144，SHA693e5c134033f52886d333530164f2ed3411313d9440c9b95624252da05e45d3。原生解析Auto209715/Force196144是配置/原生sync接缝证据，不冒称本次有公开livecap读API。Root回读environment/b-config-b2-off-restored.json后释放同暖FV-A真实B2-off-restored-input.txt（逐字前缀、只核预算分项/用途，不调工具、不新增安排）。17:57正确答复2000=800+600+600、交付可独立核对；B2-off-restored-start/end.dom保存真实过程/结果。

B2-off-restored-native-rpc：total1376404/calls42、provider context37810/262144/14%，与可见14%一致；compression仍2、无新Parent operation，globalfalse/Memo0/next_idle absent，当前session.info Prompt Noting Memo=0。6079之后104原帧只有seq6081旧2次压缩accuracy警告kind=compacting，不能把该warn算实际新压缩；“未压缩”单独不证明读取恢复阈值，结合operator的原生配置同步接缝如实保边界。09:57:40Z environment/validator-b2-global-on-ready.json仅FV-A全runtimeidle/tasks0/Parentinactive，DB同inode/SHA符合，旧0273runtime已自然消失，不持续称在线。执行者暂停模型，下一globalon恢复与真实Main自然Idle等待Root另行释放。

### 4.10 V17只读Files/HTML/导航代表链（7ea5e64，B2暂停模型期间）

暖FV-A正常点击Files，正式Files path以runtime真实cwd `/Users/edgar/code/hermes-secretary/.hermes-dev/round2-runtime` 为起点；实际列表读取既有preview-fixtures（未创建/修改运行素材）。note.md渲染粗体/表格/代码，Search document输入42后按钮搜索实际1/1并高亮mark，V17-note-preview/search记录。safe.html默认Page preview显示Static HTML Preview与“Scripts and external resources are blocked”；DOM真实iframe sandbox=""、title=Page preview，srcdoc为隔离预览内容，证据V17-html-isolation-dom.json；切HTML source看到原生脚本`document.documentElement.dataset.previewExecuted="yes"`与img onerror，未当指令执行。浏览器Back回HTML后再Page preview，09:48:07Z读iframe html与外层html的data-preview-executed均null，V17-html-script-not-executed.json，支持本既有测试内容脚本/onerror未执行。未跨源绕行或注入DOM。

Back to Chat返回原FV-A/完整最后回复/Usage1263299/Context14%，浏览器Back回Files预览再Forward仍回同会话；V17-back-chat/browser-back/browser-forward。未发送模型、不触及原用户事项、无文件修改。另在tab2既有preview-fixtures列表用正式viewport逐个1440×900/1024×768/390×844/320×568，全部实际innerWidth/Height符合、scrollWidth=clientWidth，无横向溢出，截图V17-files-{width}.png与几何V17-files-four-viewports.json。320实见顶栏Files/Back to Chat、路径/列表可用；随后viewport.reset并返回同FV-A，连接加载中短暂空placeholder保留作为过渡，待deepseek实际恢复再结束（V17-four-viewports-back-chat-ready）。另实际shapes.png图片预览显示红矩形/蓝圆/42（V17-image-preview.png/dom），点击Rotate image right与Zoom in后90°/84%实际状态（V17-image-rotate-zoom.dom），属于查看器控制不修改源文件。tone.wav音频元素原生controls/readyState/duration/error从实际DOM另存V17-audio-native-dom.json，页面00:00/00:01与browser-native audio player可见；DOM快照中“browser does not support audio playback”为audio内部fallback文本，不能单凭该句断言不能播放。本次未实际点击播放/核声音，不冒称播放已通过。音视频实际播放/错误预览仍待测。B3暂停期间在tab2真实只读office/PDF：report.pdf完成后page1/1、正文Round 2 PDF Preview与blue circle42、页导航/缩放/旋转控件实际出现，V17-pdf-preview-ready.dom/png；首帧Unknown metadata仅异步过渡，不能当错误。report.docx真实正文与内嵌shapes.png，V17-docx-preview-ready.dom/png；table.xlsx实际Canvas表格3行2列，截图核Item/Value、Blue circle42、Red rectangle17，工作表Preview与加载维度真实，V17-xlsx-ready.dom/png；slides.pptx真实PowerPoint标题与Start slideshow按钮，V17-pptx-ready.dom/png，未点击幻灯播放因此不扩大为播放成功。已正常返回同FV-A，没发送模型或修改文件。Settings/错误/媒体播放与预览细项仍未齐，不能以这个代表链推广整组通过。

### 4.11 B2暖globalon恢复与H03同entry完成→改期闭环

Root单键globaltrue恢复，字节/hash完整同原始4bc6576d0d3fc7a03aa252aeffb0b1db9d58a2389468a0639571211a9ccff79b，environment/b-config-b2-fully-restored.json；BE/FE7ea5e64/暖runtime/DB不变。IAB正常reload新Controller读Secretary idle（B2-global-on-ready），没有重启/冷模型实例替代暖场景。H03-same-entry-done-input与reschedule-input均带逐字前缀，两个独立合法Main，未内部编辑数据。

- **暖on新period真实执行**：18:00用户明确自建21:30这次检查已提前完成并验收、先保留该条不archive/delete、随后再给时间，不改其他未完成项。Main实际noting_memo.add，正确确认，10:00:15.333Z新Secretaryactive/Memo1，B2-global-on-new-idle-active.dom/png/json；实际Memo Stick一级概览1entry→点击完整正文→Collapse，V16-memo-stick-one-entry/full.png，未借旧off期补跑。H03-done-final native Mainidle/Notingidle/Memo0，20th普通Snapshot `snap_2802a8b33c634ae4abdd3f4d14ca6bca` completed，与off时19不等；Prompt/工具回来与新合法Idle均实际证明。
- **同entry保留done**：以稳定语义lineage76判同entry，不要求不可变payload revision行ID恒定。原revision103 pending→notebook_edit→105→status running106→done107→字段edit108；current revision108、lineage76、archived0、done，Schedule仍原10/15 21:30非空。只读取证H03-same-entry-done-final-db/native与H03-done-tool-trace，不以模型自述判done。
- **工具偏离与保护**：完成Child尝试secretary_task schedule_cancel被原生正式拒绝，随后保留非空Schedule；为结束又试非白名单tool_call、terminal包装finish_noting，分别被实际拒绝，最终正式finish_noting成功。保完整来源轨迹，不只报最终成功；没有那个terminal命令副作用。字段中模型推测“若原时刻仍投递…”只是模型文字，不覆盖原生Registry事实。
- **只改期自动激活**：确认上述真正Snapshot后，18:02独立用户请求同条仅改下一次时间10/16 09:15、沿用要求、不另建、原次完成不重投。Main Memo成功；21st普通Snapshot实际完成，Child先notebook_edit108→109仍done，再唯一notebook_schedule operation=schedule_update/entry109/newtime，真实返回revision111/pending（稳定lineage76），没有另补status，不是archive/create重建。schedule_update结果row1417与Child工具trace、current entry111共同证明自动激活。其它已兑现提案承诺未重开，预算/四检查要求保留。H03-reschedule-tool-trace与same-entry-reschedule-final-db/native，Registry对照H03-same-entry-registry-comparison.json（instant在Registry语义为user_reminder，按本项revision准确选取，不能错用secretary_task语义过滤得空）。
- **边界**：新时间仍未来，不能冒称已在真实10/15原时刻实际观察“不重投”；当前正式Registry新时间/旧occurrence治理事实可核，未来本测试安排将在收尾正常取消。改期Child一次tool_call尝试包装结束被拒后正式finish_noting成功，同样保偏离。H03该同entry必要分支真实闭合，其余软提示/状态和并发全量不推广。
- **F02原overlap失采**：曾准备在改期Notingactive时发送sleep45，但发前最新DOM已Framework/Secretaryidle，因此未发送该模型消息，F02-7ea5-overlap-before.dom明确记录，不能冒称交错已复验。相关只读observer始于cursor6547，未模型输入，于10:06:23.268Z自然结束0帧，不能伪造复现。B2-on-H03-lifecycle观察器自然10:02:33结束/cursor6183→6544/361帧，完整源落盘。
- **B3安全窗**：10:04:21Z environment/validator-b3-ready仅FV-A全runtime Main/Notingidle/tasks0/Parentinactive，next_idle absent/Memo0，原configSHA/DBinode一致。Root准备B3配置及可能F04前端集成，执行者暂停模型，不擅自改配置/重启。自建未来残留现在仅10/16 09:15秘书检查，生命周期证据齐备，最终正常UI取消并等真实Noting。

### 4.12 B3真实Force路径（7ea5e64，触发估算具体数值仍有证据边界）

Root正式释放，environment/b-config-b3-result.json原生CLI仅context139264/ratio.75改变，capnull/globaltrue/specialfalse-null/idle2原值不动，configuration_failure空；SHAa04ab5ce1057f29af8ba5cfad40144bf09888329413f9701e6e09692c92762de。原生解析Auto104448/reserve66000/Force73264（K=1000），不改机制、不另开环境、不重启；FE固定7ea5e64，F04尚未修复。

- **真实材料/完整输入**：B3-material-batch-1/2-input.txt均逐字前缀，各100条独立假设验收样例QT0001–0100、0101–0200（各约24K字符），8类预算/用途/里程碑/验收/材料风险/结果复查/归档/范围，逐条有输入、预期输出、判定依据与不确定性处理。明确仅本会话参考，不是真实待执行项目/提醒/承诺、不改变现行800/600/600与10/16 09:15排期。Main实际正确答首尾编号、八类与指定证据约束，未访问文件/调研源码/执行样例。第一批答复有“明晚那次…2026-10-16 09:15”的文字时间标签不准确，明确日期正确，保原文不隐藏。第三100条已在白名单生成准备，**未发送**，不用无必要继续越Auto。
- **逐轮实际测量**：第一批provider context55505/max139264/40%（B3-batch1-native/UI），低于Force；普通Idle Snapshot snapdd8完成后才发第二批。第二批provider最新70674/max139264/51%，UI51%一致；这些是真实占用，不是累计Session1663960。配置context上限同步已由本轮receipt实际证实。
- **真正Force admission/Anchor/Child/Snapshot**：admission65 kind=force，admitted_at1791972669.124318（18:11:09+08），Anchor `b3995b6e4bf3454998174da9eea19e68`（User1444）；Child `noting_35dcf428f32043c2`真实completed，普通NOTING，仅notebook_edit→finish_noting；Snapshot `snap_f2300605c7e045c6b4cfc661c853e044` triggerforce/runtimeNOTING正式提交。Parent正常回答第二批，compression仍2、没有普通Auto；正式Framework给nearinglimit/dispatched提示（seq7356）。随后process_complete保存的User1447 Anchor `63a5baa0fbbf4644a3c7440100dff7fd` 合法Idle admission66、Snapshot `snap_320df115b9864b188ab8874661c815cb` completed，不能把这个不同Anchor的Idle误报同Anchor重复Force。Force同Anchor实际admission只有1；未主动伪造重复触发，不推广同Anchor所有负例通过。
- **测量边界**：provider70674<73264，不能冒称这个值跨Force。Force实际使用触发时原生估算；公开session.events/DB本次保存kind/Anchor但不含当次具体usage数值，当前context_breakdown是后续receipt，不能猜成当次测量。已交Root协调既有原生数值事实入口，本报告**保触发值精确[73264,104448)数值证据缺口**，不由自行重算/Session累计数补假证。不因缺数字抹掉真实Force路径，也不把配置raw当路径生效证明。
- **真实Notebook/保护**：第一资料批被记为仅会话参考的decision索引，未将100样例各建真实事项/排期；本自建未来task仍同lineage76一个。Force Child没有越权尝试；相邻普通Idle有tool_call包装finish尝试被白名单拒后正式finish成功，完整B3-force-children-tool-trace保此区别。
- **原帧与UI**：B3-force-batch1-events.jsonl连续1秒真实只读（起点时刻以原文件为准），10:12:49.726Z自然退出，cursor6547→7369/822帧；B3-batch2-native一次性events.since仅512/truncatedtrue，从6858起，不能冒完整；B3-force-and-idle-raw-events为后者派生节选，完整源引用822包。浏览器B3-batch1/2-main-end、noting-end保实际Framework/状态；未捕Force进行时弹窗，不以最终idle替动态中间帧。
- **安全交接**：10:13:48Z environment/validator-b3-restoration-ready全runtime仅FV-A Mainidle/Notingidle/tasks0/Parentinactive，next_idle absent/Memo0，B3SHA/DBinode保持。**执行者原先将后续Anchor说成最终Assistant是错误，已按Root源rows更正为process_complete User1447，B3-force-idle-anchor-source-rows保存两真实User来源；不以正文或最终回复身份推断Anchor。**执行者暂停模型，Root协调恢复context262144/ratio.8，再以下一真实暖Main核恢复；不自行改配置/切路线。H06整体仍有local开关/非eligible/定时负例与精确测量边界，未整组通过。

### 4.13 e829正式版本暖恢复与H07跨压缩历史代表链

Root亲审F04无冲突集成，正式FE `e829b02c624a12ecf623915ff63b46209a68366f`（本次实际git rev-parse一致），BEea2ab483/profile/暖runtime不变。Rootoperator已10:23:04恢复B3两键并原配置全字节/hash一致；执行者按释放正常reload两IAB建立新版Controller（e829-cold-ready，cold仅指Controller重新连接，不是模型冷实例），然后才发送完整逐字前缀H07-e829-warm-history-input。

真实Main session_history mode=search/query青桐提案/rolesuser/limit10，返回最早原话UID `c7e4830cbfb545d5b33922209da0e44b`、conv_ref `conv_9ef0655053bb476886da620fefebba63`、timestamp16:24:15+08；事实原10/15 20:00检查、10/16 18:00截止、预算尚未确定均准确，未拿新10/16 09:15日期替原话。模型首次认为search完整正文已足够，**没有独立read**，故执行者再发独立带前缀H07-e829-precise-read-input，明确按同Identity精读不重新搜索。实际session_history mode=read/message_identity返回target及同Conversation邻居6条，target完整原话/UID/原时间保留，模型准确核三事实。H07-e829-current/precise-result.dom保存Parameters/Result/最终回复，后者不是模型自述代原生工具证据。此target跨过B1特殊与B2普通Auto两次真实压缩，来源原话仍可读；无文件/源码调研或新提醒。

当前H07-e829-final-native-rpc provider context74492/max262144/28%、sourceprovider_usage/estimatedfalse，UI28%对应本轮真源，表明B3上限恢复被暖下一Main实际采用；不把无新压缩单独判ratio读取。H07最后自然Noting完成Framework，Main/Notingidle/Memo0/next_idle absent；原状态读H07-e829-final-db，仍保已定预算与唯一自建未来检查。10:32:59Z environment/validator-special-low-condition-ready全runtime唯一FV-A、tasks0/Parentinactive、原配置SHA/DBinode一致，模型暂停交高阈值负例窗口。

特殊核心后续安排以Root接收修订为准：高合法阈值150000（原生预检不clamp、150000<Force196144<Auto209715），仅一有效低条件负例；然后另安全窗降10000，真实新Main→特殊Role/compact_parent/Parent完成与e829的Context源/source/estimated/更新时间，再真实主对话连续性。原B1成功包/可见Guide复用，不以普通Force代特殊；手动与普通Auto Context分别复验。B1 guide确有ordinary finish_noting vs special compact_parent分支与“terminal tool”措辞，全文NOTING_WITH_COMPACTION仅此1处；当前特殊角色取证来自真实Snapshot/runtime/工具链，不能冒称任务文本另有明示当前Profile行。B1-special-visible-guide.json/role-visible-excerpts.json为原包提取。三路径Context/F02整改及跨Conversation/Rewind边界等未齐，整轮仍未通过。

### 4.14 特殊开关真实低条件负例、e829特殊成功与F04该路径复验

Root接收精简安排，operator以原生CLI仅special threshold150000/enabledtrue（合法预检无clamp/failure，150000<Force196144<Auto209715）；configSHA68096fa48490a78c92966f8b18f759b0ffe66be6eef30e42f22d2bcbb4b2a827。真实Special-high-threshold-negative-input.txt逐字前缀+QT0101缺负责人如何判定，Main两行忠实回答待澄清/不臆造负责人，未新建事项/排期/执行项目。

- **低条件负例代表链通过**：新Main→自然Idle，实见Secretaryactive（Special-high-threshold-negative-active.dom/json）；actual provider75110/max262144/29%低于150000，但不能把provider冒当selector估算。27thSnapshot `snap_0dce16bc15784f41a28bb0565ccdeb68` runtimeNOTING、terminationfinish_noting、真实Childcompleted/Memo0，Parent compressions仍2，无新summary。special开关true与真实ordinary选择共同证明该场景未走特殊；前selector具体测量不在公开源，边界保留，Root原生合法性预检仅补类型/无clamp，不冒本次selector日志。
- **实际工具误用体验候选**：该ordinary Child notebook_edit/show后再次tool_call包装finish被拒、terminal shell finish被拒、再正规finish_noting成功，完整Special-high-threshold-negative-final-db。此前B1special一次shell误用、H03ordinary多次wrapper/shell与task.schedule_cancel均被保护拒绝；与guidance“terminal tool”措辞并列观察，**因果未证明、不能凭文字断根因**。FV-F05仅体验候选，主审决定是否整改；保护成功不能抹掉多次模型误用、额外等待及恢复轨迹。
- **切低10000**：全idle窗由Root释放operator只改单键150000→10000，specialtrue其余原值不动，无failure，SHAf64d0755…，environment/b-config-special-positive-result.json。完整Special-positive-e829-input.txt逐字前缀+本会话结果复查必须保留首次失败与复查对照，暂不永久保存、不改排期/预算/四检查要求。Main真实Memo.add后正确确认（仍有“明晚…10/16 09:15”文字标签误差，保原文，不是实际排期改动）。
- **特殊核心真正成功，未以would_grow替代**：10:42:27.685Z实见ContextCompacting/Secretaryactive，正式popup唯一Cancel按钮，Special-positive-e829-process.dom/png/json。28thSnapshot `snap_3854a937864f4481af2e2437f7a515c3` idle/runtimeNOTING_WITH_COMPACTION/terminationcompact_parent；Child本轮仅notebook_manage→compact_parent，无错工具，真实result native_safe_admission/usage_tokens75850/threshold10000，明确该数值为compact_parent admission事实、不是前selector测量。Parent operation `67361af5fc884dcab87357c4b91ed51a` statecompleted/activefalse，session.usage compressions3。真实summary row1522 UID`19f17651d8bb430c9cae7de9812478a3` 35435chars，UI未reload第3张Compaction卡立即出现、默认collapsed、可展开原文（summary-attrs/rows/expanded）。旧B1成功完整包复用，不再重复作通过证明。
- **F04特殊路径实际复验通过**：真实压缩完成后未发新Main，10:43:12.563Z同次CUA终态字段已Context20%；同call更早DOM仍旧29%/75850，均保Special-positive-e829-completion包，不能丢旧帧美化时序。随后fresh DOM/popup为20%与`~53,035 / 262,144`；native同runtime context_breakdown为used53035/max262144/percent20/source=local_estimate/context_estimated=true，session.usage完成包无Context字段，证明完成接缝从既有breakdown更新而非新Mainreceipt刷新（final-native-rpc与after-reconcile.dom/png）。“~”估算标记实际显示。原帧seq8658compacted在观察器10:43:12.673Z被采到，这是**观察时间，不是event生成时刻/SLA**。数据源/时间/已估算均如实；手动与普通Auto路径仍待新正式版本实测，F04不以此关闭全缺陷。
- **恢复与暂停**：10:48:45Z environment/validator-special-positive-restoration-ready仅FV-A全idle/tasks0/Parentinactive/nextidleabsent/Memo0；按Root新Clarify安排交operator恢复specialfalse/null。10:49:55Z environment/b-config-special-restored-result.json两CLI成功、全部原字节/SHA4bc6576d…一致，Auto209715/Force196144、服务DB不变。保持模型暂停，不继续manual/Auto切配置，等Clarify正式集成；特殊正例后的新版主对话连续性将在后续真实Main取得，不能以没有发消息说已验证。B1之后多轮历史/业务连续性已有有效证据保留。

### 4.15 正式Clarify代表链、四视口与跨客户端关闭失败（208b2d18）

- **版本/合法起点**：Root亲审Clarify并集成UI208b2d18fd4643faa2724febb9db56bc3f1d1a0e，BEea2ab483/原round2 profile，全部原配置hash4bc6576d…已恢复；两标签正常reload后同FV-A。完整原前缀输入V19-four-question-input.txt；一次真实clarify含单选、多选、Other、可跳过文本题，不写永久数据/不增排期。工具call_00_EGxypCvQFllBhPcapSUA3953；runtime b03b78a2。新Main为此前特殊成功后真实连续业务对话，不以模型自述证明压缩成功。
- **真实视口/焦点/关闭前行为**：tab2实际1440×900、1024×768、390×844、320×568均生效、doc无横溢、dialog内焦点，移动bottomsheet。390初动画尾bottom845.34比844超1.34px如实保留，320稳定bottom568。初0/4 Confirm禁用；Tab/ShiftTab焦点仍在dialog。实际桌面背景overlay单击不取消，截图/DOM V19-overlay-no-cancel。Root亲看V19-clarify-390/1440原像素。截图初仅前两题不是后题缺失，本次真实操作补证：320下填写单选结论、multi用途/风险应对、Other精确文字“合成校验76203：先保留首次失败的原始记录，再列复查对照。”，第四题空跳过；Tab从第四题移动到Confirm并滚动dialog，320/390 footer真实可达/按钮开启且在viewport内，V19-footer-reachable-320.png/390.png及button-bounds。一次提交成功，原生outcome=submitted/3 answered+1 skipped，Main准确复述，未新排期/永久写。
- **FV-F06跨客户端失败**：tab2提交/清modal，Main实际完成及自然Noting idle后，tab1仍旧0/4 Questions from Hermes。V19-two-client-close-count.json取证2026-10-14T11:14:37.502Z primary1/responder0；V19-primary-stale-dialog.dom.txt/png、V19-responder-cleared.dom.txt/png。旧tab1未点X/未reload，保现场供修后复验，不能以仅响应标签关闭说整组通过。
- **原生完整性与身份边界**：V19-clarify-real-events.jsonl早期280帧及V19-submitted-two-client-native-rpc.json后512帧（后包truncated=true）按seq重叠校验无冲突，合并FV-F06-complete-ordinary-events.json为seq8660–9179完整520帧无缺口。tool.start8939→complete8940 submitted，完成回读open_requests=[]。普通session事件全范围无request.cancel类型；actual peer server-request/response帧未采、该旧RPC request id本次未取得，DOM只Radix id无request属性；不能把tool_id等同request id，亦不能凭512包自称全量。相关原包FV-F06-related-native-events.json已交Root/修复owner。
- **独立真实取消**：为保旧实例及分离身份，仅tab2 New Chat创建本次FV-C stored20261014_192645_930d38/runtime7480abac，完整prefix+V19-independent-cancel-input.txt问一次临时用途/风险单选。未触及原用户会话。取消前session.events.since未截断真实open_requests id srq-574c278adf3f/methodclarify/session7480abac；tool_id call_00_DtOagZxkj5kGwnnisu6h7854/seq101，V19-cancel-open-native-rpc.json。dialog一次Escape→outcome cancelled/unanswered/null、modal清；真实Main“已确认…取消”且未重问，V19-cancel-main-complete.dom.txt/png与completed-native-rpc。FV-A旧弹层仍1，FV-C0。代表取消作用通过；旧跨端残留修复未完成，approval/重连细项仍边界。

### 4.16 FV-C附件、控制、三Persistence生命周期与手动Context复验（208b2d18）

- **合法起点与数据归属**：沿§4.15本次新FV-C（stored20261014_192645_930d38/refconv_c9bf034c1a6047cdb27f7390c5aa8a67/runtime7480abac），正式FE208b2d18/BEea2ab483/原profile与全部原配置；不接触原用户会话。每条真实Main/Steer完整原前缀在对应*-input.txt；保持tab1/FV-A旧F06弹层现场。以下是真实代表链，不推广未知或未执行分支。
- **V08选择与实际理解**：Attach→Files原生chooser选择4文件，选择后未发时运行目录无对应文件（before-send-runtime-files），draft实际chip可移除。图片旧名含数字68427，先移除再用相同像素的中性visual-card.png，避免答案来自文件名/辅助文字；完整输入不包含答案。另两duplicate-name.txt内容不同及普通长名文本。发送后原生Attachments分配duplicate-name.txt/duplicate-name-2.txt无覆盖；User历史只名字/chip、不摊正文。模型真实vision_analyze读取profile/attachments/visual-card.png，五位数字68427、左橙三角/右蓝形正确；**首次误称蓝形为正方形**保V08-four-attachments-complete。独立真实追问→原生Python只读附件像素→蓝宽196高161、矩形并明确更正，V08-shape-recheck-complete；不能把首错删掉或以可读性证明所有视觉判断准确。文本甲TEXT_A_41862/2000/3与乙TEXT_B_90317/3500/4分别准确，长名LONG_FILE_79163准确。普通PDF输入、附件取消/冷恢复等仍待补。
- **V09累计预算与notice**：仅选择白目录稀疏bin文件300000000+200000001字节，第二文件实际alert“attachments together exceed the 500 MB limit”，仅第一chip保留。移除第一后第二可单独选择，证明移除释放累计容量。两个都正常移除，**没有大上传/没有模型发送**。error在后续操作仍保留，手动Dismiss才清；成功重新选择并不等于旧error自动清。V09-over-budget-selected.dom/png、remove-releases-budget。最大容量传输机制和真实Cancel Send/unknown边界未测，不用选择成功冒充传输通过。
- **V05独立Interrupt闭环**：Main只允许terminal sleep45，实见Running→完整prefix Steer“停止等待，只回92816”→Pending真实卡；另未发draft55271+cancel-send.txt，仅按Interrupt交接Pending。原生工具Failed/Commandinterrupted/exit130；唯一新User为待处理Steer，模型仅回复FV-C已接新指示92816，未重复handoff。草稿与附件原样留Composer，未进入历史。V05-before/after-Interrupt/completed及persisted-control-counts。该主动控制结果不能描述为等候失败/自然回执异常。
- **V04/V06 Escape Stop**：另新Main sleep45→真实Running，输入未发draft67420+同附件→textbox Escape。原生工具interrupted/exit130，最终无新User/Assistant、没有本应自然结束38159的回复；draft/attachment保留。V06-before/after-Escape-Stop/terminal。这是实际Stop作用/键位代表链，Cancel Send成功/unknown及IME能力仍缺。后续测试显式移除未发附件并覆盖草稿，不假称它被自动发走。
- **H02/H08三候选→提案→修改→仅批准Memory/拒绝另两类**：完整three-candidates-input仅待审、Main Memo.add，自然Snapshot实际memory_candidate/rule_candidate/skill_candidate，Memo0（candidates-final-db）。正式/propose-persistence命令额外参数携原前缀；Main亲自session_history按SourceIdentity与关键词扩查原始来源/更正/控制结果，proposal-complete。首提案对潜在偏好保留证据不足，但误把主动Interrupt/Stop当缺回执支撑；用户单独明确合成偏好、纠正控制事实→真实重写提案/保旧待核结论，不提前写。原有334持久文件指纹在批准前无变（比较不能单独证明新增文件不存在，结合实际工具轨迹）；只批准一条合成Memory、明确拒rule131/skill132。原生memory.add targetmemory返回success/done/entry_count1/81chars，正文与批准逐字一致。实际仅本profile memories/MEMORY.md193bytes及lock变化，无规则/skill变动，approved-memory-file-comparison；未访问用户主目录/外部service。随后自然Noting完成Snapshot，三candidate lineage130/131/132的最新记录141/142/143均archived1、current_candidates空、Memo0；current只decision。H08-candidate-archive-summary/approved-final-db。记录模型初始过度否定/控制叙述偏差及用户纠正，不只报最终成功；代表批准双条件/仅批准范围/拒绝归档通过，其余证据支持边界由Root审。
- **V13 FV-A合法nochange历史**：原值暖FV-A /compact→native Nochanges27msgs~54070unchanged、compression仍3，未摘要；F04-manual-no-change-native-rpc与208b-events。保留合法结果，不用它冒成功。Root准许另一真实暖Conversation，不改门槛/不注水；FV-C自然附件、检索、控制、审批累积后执行/compact。
- **V13/F04手动真实完成**：FV-C process ContextCompacting→Context popup唯一Cancel（未点），真实Parent成功/usage compressions1，原生notice65→48messages/request~56319→~48764。新summary row1753 UIDd34ab82000184d879a4d482aa29ac0ba/11854chars无需reload出现、默认collapsed、可展开原文。完成后未发Main，11:42:42.458Z实际UI19%/popup~49598/262144，native同runtime context_breakdown49598/19%/local_estimate/estimatedtrue，session.usage完成包缺Context。F04-manual-FVC-completion.dom/png、UI-fields、completed-native-rpc/db、summary-expanded；**F04手动路径实测通过**，普通Auto仍未补，不据机制测试关闭全缺陷。UI旧provider18%→localestimate19%不是压缩增长反证，原生本路径自身估算明确56319→48764，数据来源分开保。
- **安全窗与待补**：11:43:14.620Z environment/F04-manual-FVC-after-safe两runtime Main/Notingidle/tasks0/Parentfalse、原configSHA4bc6576d/DBinode42327472不变，FV-C next_idleabsent/Memo0。Root接收manual成功，优先F06统一集成重启；停止模型/Auto配置。仅tab2准备未发完整prefix草稿41985+cancel-send.txt用于本次真实断连/恢复（V18-pre-disconnect-with-draft.dom/png），未发Main，tab1旧F06未动。operator获告此时不要切配置。

### 4.17 V18真实断连、V12冷恢复及FV-F06真实闭合

合法起点：FV-C两客户端同stored20261014_192645_930d38，tab2未发完整前缀草稿41985+EDIT_74026/cancel-send.txt，tab1旧Clarify残留；Root统一F06版本重启，执行者未发模型/未点旧X/未reload。BE44701于11:49:34Z停，11:50:39Z新进程14168恢复，**实际65秒**，不写成计划20–30秒。11:49:50.656Z实际Disconnected/Reconnecting只在Composer，Send灰、输入可编辑，历史/Sidebar/Usage保留；追加EDIT后稿和附件仍在。11:53:17.083Z自然重连后Send恢复，稿附件保留、User仍10、没有自动提交。V18-real-disconnected、disconnected-edited-draft、natural-reconnected及recovery-fields保原DOM/截图/时间。旧tab1modal随重启reconcile消失，仅是恢复事实，不算F06修复通过。

V12原生冷runtime2f94b881 session.usage零计数、usage_detail owner_unavailable未知，不能将它当历史总量0。freshController实际仍显示saved Total873341/Input30980/Read831616/Output10745/Hit96.4%；可靠来源缺失时Turns—、Latest—、ContextUnknown，未猜Context。V12-cold-hot-controller-Usage、cold-fresh-controller、Usage-session/latest与native-FVC/FVA；新真实Main后959759/Context16%恢复有效值。此为冷恢复代表链，不覆盖所有错误包。

F06新版BE7567dc3a/UI d543b（产品208b）：新真实双端Clarify request **srq-a21905349566**，11:55:59.800Z两端各1modal；tab2选择后一次Confirm and continue，11:56:29.482Z两端自然0，tab1未X/刷新。完整未截断原包seq20 tool.start→22 request.cancel{id=同id,methodclarify,reasonresolved}→23 tool.complete submitted，open_requests=[]，Main正确承接，自然Noting完成。FV-F06-retest-open/resolved-native-rpc、resolved-summary、immediate-close-counts及other-after-submit.dom/png。Root亲审接收**具体缺陷关闭**，不推广approval/所有V19边界。

### 4.18 V07实际Rewind与H07活动路径身份失效

版本BE7567dc3a/UI d543b，FV-C两端。合法原稿61490/cancel-send.txt：Reply最新User临时隐藏target及后续，Exit reply and restore draft恢复完整历史及稿附件；选旧四附件User显示4实际引用，未确认，退出仍恢复原稿。改最新User为带逐字前缀BLUE_32768输入，Send唯一Rewind this conversation?红色Rewind and send；Cancel保编辑。再开确认窗reload，旧完整历史回来，新BLUE只作为普通草稿、armed Reply/dialog消失，User11、无自动发送。重新Reply目标→独立确认后真实rewind+唯一新User；12:03:52.119Z两端旧User0/新BLUE1，Main正确确认、自然Snapshot记新标题。

原目标row1798 UID214481767fe445809cd964c214663fd2，新Userrow1855 UID82a3193e7cf84122b588d04b3f900627。V07-*完整输入/DOM/像素/两端计数。read-db main_rows是所属Core源审计行，物理保留旧UID不能判活动路径失败；V07-native-cut-comparison保该纠正。9e3566真实reload后BLUE仍当前事实；正式REST History include_compacted=true/104返回中旧UID0。随后H07-rewind-invalid-identity-input完整前缀真实精读同旧Identity，session_history返回successfalse/“Message Identity is missing or outside the current Conversation path”，Main据实报告、不搜索别会话替代、不恢复旧选择；H07-rewind-old-identity-result.dom/png。这是真正活动路径边界，不用宽DB审计代替。

### 4.19 F02 d276/da6377四Turn重叠与普通Auto原失败保留

Root集成BE d276ea8/UI da6377，原配置/profile/DB，reload加载新版后四真实Main：Memo登记甲2000/乙3500独立备选；一次terminal sleep25差额1500/75%；Memo登记分母与1.75倍；一次terminal sleep25拆3500为1400/1225/875。首组等待后Noting已结束，**没有overlap**，保更正；第二组在真实Secretaryactive立刻提交第四Main，F02-final-turn4-overlap-running.dom/png实见Running+Secretaryactive。四final及四Known工具各一份，但四无UIDtool.generating构建卡永久Unknown残留，仍不能关闭F02。完整第二包seq1230–2606共1377连续，first包3–1229；原构建253/975/1606/2293及start/complete/commit16帧、四receipt和正式History真实完整tool_calls分别见FV-F02-new-construction-start-commit-frames、new-four-persisted-receipts、four-actual-History-tool-messages。不能用receipt冒History，不能仅按同name删除无UID片段。

普通Auto固定globalfalse/cap20000（其余原值）一条带前缀乙预算Python Main，真正两次completed、新两summary无需reload/defaultcollapsed、最终38195/262144/15% provider_usage与UI一致；第五Unknown残留。F04-Auto-final-version-events原包及terminal.dom/png/native；构建UID18d8ecaa…/final6911b664…均为真实正式调用。文件first-completion实际仍Compacting，**是等待超时的过程样本，命名不构成completion证明**。原生首completed观察12:32:40.604Z、provider16%43.622Z、15%48.649Z；DOM缺自身时刻/短窗，无法证明完成后新provider前估算即时呈现。Root只读窄审后安排唯一短窗补证，不把终态provider替完成估算。12:48:27Z operator完整原配置字节/hash恢复，原失败不删除。

### 4.20 C117迁尾反例与9e3566真实phase/临时Notebook复验

da6377加载旧Controller原/notebook调用后，新无工具C117_FLOW_81426 Main准确答BLUE_32768和拆分，但卡迁到新Assistant之后。C117-reference-before/after-nextMain.dom/png与after-nextMain-reference-order-corrected.json：旧User44/Assistant45、Notebook47；Root已进入UI集成/HMR窗，加载基线与采样边界注明，不能把它混成新9e3566 Controller失败。RootUI-only集成9e3566、不重启BE/改配置后，两端正常reload；旧Unknown消失只算重新载入，不能单独关闭缺陷。

新Controller同FV-C连续两次真实/notebook，卡47/48在当时Framework46后；然后真实PDF+预算Main，新User49/Assistant50、两个卡仍47/48，无迁尾。三真实构建→start/complete→正式commit/History，read_file Failed、terminal Success、vision_analyze Success各一Known、final1、Unknown0；原生observer seq3396–8791共5396、连续无缺口/truncatedfalse。C117-phase-formal-History HTTP200/104messages完整源含三个Assistant工具Schema实参/UID，native-History-and-stage-frames派生索引。CUA进行时wait超时reset导致动态UI失采，不冒过程像素已覆盖；原生真实阶段帧有效。C117-new-two-calls-order与new-after-tool-order/DOM/像素。

随后第三/notebook读取新Snapshot（21:05，前两旧20:54），三张卡先后保持，新localoff主消息追加后位置仍旧边界。两个相同Snapshot连续调用的显示内容相同，公开DOM没有唯一调用id，**仅证明两卡数量和现有次序不变，未证明重叠未回包的不同内容排序**；不冒快速调用一定重叠。工具完成commit及后续Main自然正式History归并后位置均保，另独立正式History取证不等于强制Controller刷新。最终before-reload3卡/Unknown0，正常reload后0卡/Unknown0、BLUE历史保，C117-new-before/after-reload.dom/png。本具体修复链通过，未覆盖所有并发页边界。

### 4.21 普通PDF理解、localoff/on与真实工作体验

新9e3566/BE d276 FV-C，合法选择preview-fixtures/report.pdf，正式上传引用report-2.pdf；V08-PDF-phase-input完整前缀要求读取标题/图形数字、一次Python预算、不写文件。原生read_file图像型无文字层失败，模型改terminal在本测试profilecache/scratch写probe-pg-1.png并核预算，再vision_analyze实际读取渲染像素：标题Round 2 PDF Preview、redrectangle左/bluecircle右/42两处，差额1500、1.75倍/75%正确。**临时PNG仍违反本条不写文件，不能用非项目文件豁免**；“全页无其它数字”漏标题2，首次错误保留。C117-phase-PDF-terminal.dom、正式History原参数/结果、V17已有PDF原像素支持独立事实。

/noting off正式入口返回本Conversation关闭；H06-localoff-before/after原生localfalse/globaltrue/Memo0/tasks0/nextidleabsent。独立带前缀H06_LOCAL_OFF_52683纠正PDF数字，Main直接更正无工具，未新增Noting；off后最新admission88/Snapshot仍锚PDFfinal f621c…，不是纠正Main。timer中间scheduled与一次suppression内部变化未采，不能仅终态absent证明完整计时机制。/noting on回读true、发新Main前tasks0/nextidleabsent/Memo0，没观察补跑；之后新带前缀H01_EXPERIENCE_61842 Main直接如实自述，UI真实Secretaryactive→自然完成，新合法period成立。H06-localon-before/new-period与H01-experience-FVC-main-end；所有配置保持原值，没有另一profile。

体验自述承认PDFtext失败后换render+vision、图形首错后像素复查；明确两sleep是主动中断、非绕行完成。承认意识到no-file却自行将scratch视作豁免，这是违反明确限制；承认漏标题2。候选归档/Memory落盘自述“不知道/仅依工具回执”，独立实际工具/产物/Snapshot早已取证，二者分列，不据自述否定或证明已执行。只谈可见体验，无源码/harness研究。Noting长期多次tool_call/terminal/schedule_cancel误用与白名单真实阻挡恢复仍保FV-F05，不只报边界成功。最后仅余Root授权唯一Auto短窗及本次lineage76取消；未取得的分页/IME/approval/acceptedunknown/Parentfailed等据实际入口边界登记，不新增探索。

### 4.22 唯一普通Auto短窗补证与FV-F04闭合（9e3566）

Root亲审旧原包认定完成到新provider之间UI短窗失采，明确只补一次，不重演整Auto/模型链。13:13:25Z operator合法globalfalse/cap20000，其余原值不动，环境身份保持；environment/f04-final-auto-ready-result.json。执行者事先准备既有公开session.compaction_state/usage/breakdown只读200ms轮询（仅状态变化落盘），以及每个样本有自身UTC时刻的只读DOM字段；不伪造事件、无前端计数。带逐字前缀F04-final-short-input仅要求直接短答保持BLUE/甲2000/乙3500、不调工具。普通Auto operation4633b33c64824cc998374f0ca0f60599真实computing→committing→completed，只有一次新压缩，summary按钮3→4且新默认collapsed；Main终答无新工具。

- 13:16:18.988Z DOM刚退出Compacting时短暂保持既有47325/18%，是合法旧有效值。
- 13:16:19.035Z原生观察completed，session.usage没有Context字段，同runtime context_breakdown明确55257/max262144/21%/local_estimate/estimatedtrue。
- 13:16:19.417Z实际DOM已4个collapsed summary，popup **~55,257 / 262,144**、环21%，Stop尚在。这发生于本轮新provider值可用之前，完成接缝使用真实有效估算已证。
- 13:16:20.864Z原生首次provider42355/16%/estimatedfalse，13:16:20.900Z DOM更新42,355/16%且去估算标记；21.245Z Main已结束。

证据F04-final-short-native-samples.jsonl、dom-samples-1/2.json（自身采样时间）、before.json、completed.dom/png与F04-short-final-History原包，后者新User464cb…/final79a6…无tool_calls。上述时刻均是采样观察时间，不是事件生成时刻，不宣称精确端到端延迟或SLA。旧Auto失采/文件误命名历史保留。**Root亲核接收FV-F04具体缺陷闭合**：特殊e829、manual208b、普通Auto9e3566三路径各独立真实完成接缝已齐，不能互代。

13:16:55Z两runtime全Main/Notingidle/tasks0/compfalse，Memo0/nextidleabsent，environment/f04-short-restore-ready及F04-short-safe-FVA/FVC原包。执行者暂停模型交operator capnull→globaltrue恢复全原字节；只剩最后本轮lineage76取消和报告收尾，不新增探索。

### 4.23 最后正常取消与安全收尾

原配置13:18:08Z已完整恢复。最后cleanup-lineage76-input携逐字前缀，正常Sidebar回FV-A，明确只取消本轮自建lineage76未来秘书检查，保其它未完成事项。Main真实Memo.add，并正确报本项目deadline2026-10-16T18:00:00+08:00及2000=800/600/600，没有混入FV-C3500/BLUE。真实Child noting_ddfae5f0efba41ae notebook_manage archive111→current revision159/source_basis111/lineage76/archived1，非空Schedule历史保留，对应sched44cc…enabled0，active_future_registry=[]/current_task_entries=[]/Memo0。Snapshot snap_9edc453d8cf84b95a86196fe58a7b768提交，finish_noting成功；terminal echo done/tool_call两次误用被白名单拒后恢复，完整保FV-F05体验事实。Root亲核接收；cleanup-lineage76-confirmation.json、final-db/native-rpc、main-end.dom/png。

最后13:24:45.696Z environment/final-validation-complete-safe两runtime全Main/Notingidle/tasks0/compinactive，原hash4bc6576d…/DBinode42327472/dev16777234不变；两Secretary Memo0/nextidleabsent/global及localon。所有临时观察器自然退出，pgrep无匹配；本轮未来触达无残留。保留两个测试Conversation、批准的限定合成Memory与附件/证据供复查，不删除原用户事项。final-validation-FVA.dom/png及两个handoff标签为最终现场。此后停止新增操作。

## 5. 问题、修复与复验

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| FV-F01 | V11：稳定833ef首次真实Turn→读Session/Latest→第二真实Turn→Main及Noting idle→再开两视图 | 首轮48,418 / 68.5%、Input15,014/Read32,640/Output764/Turns1；第二轮UI Session Total/Input/Read/Output/Hit仍首轮值，Turns已2。原生session.usage为total125,795/input16,124/output1,895/prompt123,900/calls5/cache_hit87；DB saved read107,776。证据A1-usage.dom.txt、A2-total-idle.dom.txt、A2-native-rpc.json、A2-main-rows.json。Root补充只读usage_detail原包在fv-f01-fix/source.json：第二Turn canonical token为null，partial/failed_dispatch，Turns2/Latest Calls4有效；不能以Session差分制造Latest token | **Session**已有可信saved新值未替换，缺陷已复现；Latest旧token保值配新有效Calls属用户按字段增量要求，不单独判缺陷，原生无新Latest token记来源限制 | b99651c53ca7792e8631844fe363cdb168531912（Usage fea51be） | 原会话连续真实≥3Turn与原生字段对照通过，具体缺陷建议关闭，详§4.6；旧失败保留，V11其它分支未完成 |
| FV-F02 | V01/V02/V10：同FV-A会话两真实Turn与自然Noting/Framework归并后，未reload，A2-end已重复；后来/notebook结果后仍重复 | Root完整复核更正：A2-end在83/176/234行已经3个普通Assistant，后两正文完全相同；A2-slash-before/A2-notebook-complete中重复仍在（非临时Notebook文本）。执行者此前只看尾部误称A2-end仅2条，现保留此更正记录。DOM两条正文完全相同/visible=true；原生A2-main-rows仅一条实际final Assistant row860。证据A2-duplicate-assistants.json、A2-notebook-complete.dom.txt、A2-slash-before.dom.txt | history/live reconciliation重复Assistant；尚不能由当前观察断言slash为原因。未修改产品，待Root修复 | — | 待复验 |
| FV-F02 · 首次修复复验 | FE b99651c：两标签reload→原会话新真实四轮；第三轮新增风险段必须保持的Memo→自然Secretary active→第四轮sleep45（与Noting实际交错）→Main结束/Framework | 09:05:08Z实见terminal Running/Secretary active/Stop；空Enter后仍Running且User不增；09:06:33Z完整article统计16条，有一份重复末尾“sleep45…四方面”，对应terminal/thinking也重复。证据F01-F02-retest3-overlap-start、retest4-start/running/other-running/end、F02-retest4-assistant-counts；原始native events以1秒只读session.events.since抓取F01-F02-b99651c-overlap-events.jsonl，起始cursor4183，另F02-retest4-native-rpc/db | **复验仍失败，未关闭**；实际连续UI与正式Loop/Framework交错，未重放事件/未改模型/配置 | b99651c53ca7792e8631844fe363cdb168531912 | Root继续修复；旧失败保留。Session Usage更新已局部正常，Latest按真实源另核 |
| FV-F03 · 非阻断观察 | 7ea5e64/B1暖FV-A正式/compact→真实过程popup→Cancel Compaction | 原生终态cancelled、compression1不增/无新summary/Main，实际notice却是No changes from compression…unchanged；V15-manual-process/after-cancel-click与manual-cancel-native-rpc | 取消作用通过；Root确认原生summary原样呈现、契约无特定取消toast要求，非合同缺陷；保取消反馈易误读及本次Cancel RPC帧未采边界 | — | 不阻塞独立B2；最后静态Verification可核既有契约 |
| FV-F02 · 第二修受影响链复验 | FE7ea5e64：B2 globaloff原生Auto成功→唯一terminal Python计算→Main终态，无reload | 原生1tool_call_uid01406b41…，UI同budget工具/Thinking两个可见副本、final单条；seq6077 completefalse/all_rows_committedtrue，具体UID/顺序见§4.9第二轮与F02-second-fix-B2-* | **仍失败/open**；不同于原Noting overlap，正式压缩受影响链反例不可忽略，原overlap仍待复验 | 7ea5e64555bd41964cee4b8ffb4de60926fc1b87 | Root协调隔离修复，保第二修失败与实际完整原帧 |
| FV-F04 | B1特殊Parent完成→无reloadContext仍39440/15%，原生同runtime context_breakdown当前46189/262144/18% local_estimate/estimatedtrue | session.usage完成包缺Context字段，旧值保留本身合法；Root只读主审判完成接缝未读既有可信context_breakdown，未及时reconcile，06完成契约缺口。证据B1-after-natural-compaction、B1-completed-native-rpc、V15后Context popup | **具体缺陷已闭合，Root亲核接收**；旧失败与来源边界保留，执行者未读产品源码或造新provider值 | 待独立UI修复集成 | e829特殊、208b手动、9e3566普通Auto完成接缝真实UI/native估算对照通过，§4.22；保旧失采/失败及身份边界 |
| FV-F05 · 体验候选 | 多次真实Noting Child ordinary/special任务，试tool_call包装finish_noting、terminal shell finish，或secretary_task schedule_cancel | 实际白名单/任务不变量拒绝后正规工具恢复；B1/H03/high-threshold-final-db真实失败轨迹与B1-guide的terminal tool措辞。最新special正例本轮无误用 | 多次模型指令引导误用尝试保留；执行白名单确实阻挡并恢复。因果/合同定级未定，不自行改Prompt、不为重演造失败 | — | Root体验主审；收尾Main只按可见上下文自述，与独立轨迹分别判 |

| FV-F06 | FE208b2d18/FV-A双标签真实Clarify四题，tab2提交→Main/Noting自然终态，tab1未操作 | tab2清modal但tab1旧0/4弹层残留；open_requests=[]；完整普通事件seq8660–9179无缺口，实际peer RPC request.cancel帧及旧request id未采，不冒称全原包。详§4.15 | **具体缺陷已关闭（Root接收真实复验）**；旧tab1现场和初次失败保留，重启清旧弹层不计通过 | BE7567dc3a17d8a1fa48b78fc45c3de3503901494f | 新双端srq-a21905349566，一端提交后两端自然0modal；seq22 request.cancel reason=resolved→23 submitted，原包无截断，FV-F06-retest-resolved-summary/immediate-close-counts，旧失败保留 |

| FV-F02 · 最新phase/C117复验 | BE d276/FE9e3566新Controller后真实3工具调用、后续Main/Noting/History | 新generating→start/complete→正式History完整3调用，Known单份/final1/Unknown0，§4.20；原两修失败保留 | **具体新链复验通过**，不据刷新旧残留消失判通过，不推广整组 | 9e3566c83633d0456b12e14028b9de77aa58e607 | C117-phase正式History/原生5396连续帧/终态DOM；动态UI过程失采保留 |
| C117 · Notebook位置 | 旧Controller卡迁尾；新版实际两次/notebook→新工具Main/History→第三卡→后续Main→reload | 两卡47/48在新User49前，后续位置保持；reload3→0，§4.20 | **具体新链通过**；未回包不同内容排序未取得 | 9e3566c83633d0456b12e14028b9de77aa58e607 | C117-new-* order/DOM/PNG与正式History；旧失败/HMR边界保留 |

## 6. 验收结论与推荐复核路径

**本次获授权真实Validation已收尾交回，不宣称27组全部边界通过。** 最终运行BE d276ea8b60441da61745c31be36ab2ff1fea58c3、FE9e3566c83633d0456b12e14028b9de77aa58e607，同round2/53445/5173。最后13:24:45Z两runtime全idle/tasks0/compinactive、Memo0/nextidleabsent；原配置完整字节/hash4bc6576d…、DB/服务身份不变。lineage76整条已归档rev159/Registrydisabled、未来本轮触达空，§4.23。

FV-F01 Usage、FV-F06跨端Clarify、FV-F04三路径Context已Root亲核接收闭合；FV-F02新phase真实构建/commit/History/终态Unknown0具体复验通过，C117位置及reload清除具体新链通过，§4.20–22。保原失败与动态UI失采，不以刷新消失或后续provider冒完成瞬间。FV-F03非阻断取消文案观察；FV-F05模型tool_call/terminal/schedule_cancel误用仍存在、白名单确实拒绝恢复。PDF临时PNG违反明确no-file、漏标题2、图形首错与提案误叙/更正全保留；模型自述与实际工具/Snapshot/产物独立记录。

核心代表闭环已取得：Memo/自然Noting/十语义类型；完成取消与同lineage改期激活；Instant/过去补投/DeferredACK不重投；三Persistence候选到搜证提案/仅Memory批准执行/另两拒绝归档；特殊Noting with compaction真正Profile→compact_parent→Parent完成/summary/Context/后续连续性及高阈值ordinary负例；普通Auto和手动完成独立真实接缝/取消；压缩后原话精读/Rewind旧身份不可读；四视口/Clarify/footer/双端resolve；控制保稿/实际65秒断连重连/冷恢复/图片文本PDF/Files预览。27组结果见§3，代表链不推广全组。

**未覆盖或真实能力边界：** V01首次200/Show More200（本次FV-A150/FV-C120不足）；V03全部精细组合；V04系统IME（DOM-only无法确认输入法，不造事件）；V06/V09发送preparing取消、accepted/unknown、paste/drop及最大实际上传；V16普通10秒notice/堆叠/同key clear竞态（无稳定合法入口，不造事件）；V17 Settings/实际媒体及幻灯播放/错误预览；V19 approval deny（当前smart auto-approved，未确认manual/gateway/non-yolo，不改策略制造）；H06 localtimer到期抑制中间帧/B3当次精确selector估算（provider不能冒阈值测量）；特殊sameAnchor重复Trigger、Parent自然failed、提交后取消、ACK崩溃重试、非eligible与全量并发边界；C117重叠未回包不同内容顺序与新phase动态UI过程失采。旧机制证据只按原版本/范围补充，不冒本次通过。

用户明确要求尽快结束，Root收敛最后两条必要Main后停止新增探索；未覆盖不等于获批准不适用，也不降低原判据。结论为核心已测链及具体整改复验通过、保未覆盖及体验偏离，执行者不作全范围通过声明。最终静态Verification按用户C116由云端复查，本地未执行/派遣Verification、不代云端判通过。当前提交、§3矩阵、§4原始证据和§5历史缺陷交Root作最终交付判定；无需重复已有效链。
