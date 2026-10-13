# Verification：20261012-round2-web-ui

## 1. 审查对象与结论概览

审查者：独立 Astra high（round2_verification）；日期：2026-10-13。后端及规格版本 `24510d1c7c3b8dfc95b6d0626be30f090561fa30`，产品树前序 `4443aa7b18806246ef84d6003fbd7e1e40cff5a2`；前端 `c55120f92aca9acdcc5b7e7dc4fd1df06874e6b3`。索引 `.autonomous/20261012-round2-web-ui/snapshot-index.md`，初始基线 `37ad76f5dfac02d4774d5e0faea55911b5fb8de9`；授权修订见同目录 `baseline.txt`。用户 R2-C65 授权第二轮 Verification。

范围：06 divisions 0–4 的全部 Web V1、必要原生增量、V1.6 明确移交及本轮实际影响的继承约束。06 division 5 不实施；不重新做旧轮完整 Verification。权威为当前 02（包括 V1.6 / §5.12 Target）→04 未覆盖增量→01 适用部分，06 与明确用户修订为 Web 增量。三规格旧页首相互优先表述不覆盖当前 06/索引权威顺序。

进入条件：先完整读取 autonomous-run 与 spec-implementation-review，并仅阅读指定提交的 06/02/04/01 全文及索引用户确认内容。下列起始判据落盘前**未读取产品代码、测试、实现报告、旧审查、动态 CLAUDE**。之后才调查事实。当前阶段：首次完整独立初审已完成，**Verification 不通过**。65条中56条符合、6条不符合、3条证据不足；5项确定产品缺陷（V-R2-01–05）及3项用户现场未闭合事项（U-R2-01–03）阻断。本次不进入Validation；整改后按影响独立复审。前端补充审查版本为 `002f7a27fcf7313491f0301e143df7d3b6148088`。

## 2. 独立要求清单与覆盖

判据起点：2026-10-13，以上冻结版本。下表为独立起始版本；后续不得覆盖原解释，新增或修订须在第 6 节说明原条款、依据与理由。每行组合的是同一不变量的关联条款，行内所有条件均须满足。第一阶段完整阅读四份规格；K 条款为继承影响核查，不重开旧版全门禁。V1.6 精确移交依赖第二阶段原始交接索引确认，不能由实现自评界定。

薄弱规格的必要推导：W25 的 pending buffer 原子归属必须覆盖 finalizer、withdraw、rotation 与重试，否则无法实现“恰一后续”；W13/W39 的真实顺序与无重复要求必须同时覆盖 REST snapshot、live delta、terminal 与重连竞态；W04/W35 的只读性意味着状态缺失不能通过启动任务去补齐。这些均由原文明定结果/机制推出，不规定函数或新API。C36只批准明确列出的限额，不能推导批准其他保留窗口。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| W01 | 06 §0.1–0.3 L15–82 | 架构/身份 | 直接：React/assistant-ui/shadcn/Tailwind 薄前端，直连既有 REST 与 /api/ws；stored/runtime/Conversation/Message identity 不混用 | 独立前端仓；无 BFF、平行 Agent/存储/映射 API；正确原生身份与压缩 lineage | §3 W01 |
| W02 | 06 §0.4 L84–96 | 持久化边界 | 直接：仅草稿二进制、路由、滚动、显式呈现偏好可落浏览器；runtime map、事件及 pending 仅内存 | 逐一审计所有持久写；不得缓存 API 响应/Notebook/turn ledger/unread mirror；刷新重建 | §3 W02 |
| W03 | 06 §0.5 L98–105；§2.1 L317–334 | 原生兼容 | 直接：既有 RPC/REST 名称、形状、错误及语义不变；新增原子能力用新名；非启用原生不变 | 全 delta 对比原生调用者及分支；不以新增 UI 需求改变原有方法 | §3 W03 |
| W04 | 06 §0.5 L102–105；§2.6 L398–410 | 只读/未知 | 直接：浏览/恢复/Secretary 查询不启动 Turn、不消费 Reminder/Memo、不改 Notebook；未知不猜 idle/success | 正式所有只读入口无业务副作用；错误/加载/未知有区分，快速切换不串数据 | §3 W04 |
| W05 | 06 §1.1 L115–122；C09/C12/C14–16 | 基础界面 | 直接：英文、响应式、无头像、项目素材限定两处；六条欢迎标题无副标题，三图标主题系统/浅/深；New Chat 无Usage/Context | 生产界面与主题/素材/欢迎文案遵循授权；深浅、选中和无障碍状态完整 | §3 W05 |
| W06 | 06 §1.2 L124–139 | 路由/返回 | 直接：仅 New Chat/Conversation/Files 三主状态；移动左上侧栏、Files右上Back to Chat | Files任意层级一键返回入Files前chat/草稿/位置，失效fallback New Chat；不借history.back、不改Turn | §3 W06 |
| W07 | 06 §1.2 L137–139 | 历史/恢复 | 直接：真实浏览器history管理子路径，reload还原合法route/preview/scroll/draft；系统手势能力保留 | Back/Forward自然工作，深链接鉴权失败安全回退；无滑动模拟/劫持 | §3 W07 |
| W08 | 06 §1.3 L141–152 | 会话生命周期 | 直接：New Chat不建Session，首Send恰好一次create；切换不停止旧Turn；历史不同cwd仍可发现 | 并发Enter/按钮无重复create；空/错/删除可恢复；列表与标题从真实REST | §3 W08 |
| W09 | 06 §1.3 L147–150；§3.2 L462–468 | continuity | 直接：stored locator REST history，必要时原生resume/activate；压缩同Conversation、branch/new分离 | memory-only map，失效/重启重绑，同target single-flight，不错误绑定或重发 | §3 W09 |
| W10 | 06 §1.4 L154–173 | 真实Timeline | 直接：单Timeline，真历史、live、pending尾投影；UID/序列/来源保真 | 无第二queue/转录；无猜测Reminder/compaction/消息时间；真实Framework/instant/deferred独立类型 | §3 W10 |
| W11 | 06 §1.4 L162–168；C23/C43–47 | 活动卡 | 直接：Thinking按段active展开后折叠、工具默认折叠且每调用状态独立；同调用参数/结果同卡 | 实际流与历史调用ID关联，不能按名称；Success/Failed/Running/Interrupted/Unknown；Framework折叠 | §3 W11 |
| W12 | 06 §1.4 L171–173；C39/C48/C52 | 时间/阅读 | 直接：隐藏timestamp原文仅呈现；最新修订仅真实User/Assistant外居中时间，今日时分/昨日/本年月日/往年年；无时区 | 原数据不改；User左12%右3%，Assistant左4%右10%，正文与活动卡共用边界 | §3 W12 |
| W13 | 06 §1.4 L173；§3.3 L470–479；C55 | 分页/流顺序 | 直接：长史分页锚定，不强迫旧消息读者滚底；stream在pending前；新User不插到前Assistant前 | page overlap/delta/end/reconnect无重复/丢失/乱序；stream不人为积压至最终瞬现 | §3 W13 |
| W14 | 06 §1.5 L175–181 | 内容安全/状态 | 直接：Markdown/code/copy安全，http(s)可开、local/file路径纯文本；工具原生敏感规则及approval/clarify状态 | 原生构造/执行/终态不混；工具完不等Turn完；断流可恢复 | §3 W14 |
| W15 | 06 §1.6 L183–191；C29 | Composer键盘 | 直接：一主操作，Enter仅Send/Steer，空/附件active不触Stop，Escape取消类；Shift+Enter/IME/native undo | 矩阵所有状态、模态优先、composition key处理；未决提交禁止新发送 | §3 W15 |
| W16 | 06 §1.6 L189–190；C53 | 草稿/模型 | 直接：route隔离文本+binary reload恢复；模型/effort实际原生选项和当前值，未应用选择仅draft | 当前项二级直接高亮无Current行；设置经native方法；草稿不串Conversation | §3 W16 |
| W17 | 06 §1.7 L193–204 | 附件选择 | 直接：Files普通file/PDF；Photos/Take Photo图片路径；paste/drop同规则；选择只local；重复文件名独立 | upload仅Send；type/size先校验；摄像capture实现；历史文件仅不可点击芯片/类型名、无注入正文、长名省略完整名保留 | §3 W17 |
| W18 | 06 §1.7 L202；C30 | 500MB完整链 | 直接：当前草稿附件合计≤500000000 bytes，所有选取/paste/drop计入现有、删除释放；无16MiB cap | 边界含既有附件与同名项；实际上限浏览器内存/WS/API/原生提交以及Agent读取证明，ACK不够 | §3 W18 |
| W19 | 06 §1.7 L197–204；§3.5 L496–502 | 附件正式接线 | 直接：file.attach data_url返回ref_text进prompt；image.attach_bytes同runtime并像素context；普通PDF不pdf.attach | 真实DeepSeek图片理解+普通file/PDF读取，重复名独立；历史image不猜blob路径 | §3 W19 |
| W20 | 06 §1.8 L206–221 | 主操作矩阵 | 直接：事务优先Cancel；idle空禁用/有内容Send；active纯文本Steer；active空或有附件按pending决定Stop/Interrupt | 正式selector/handler一致，Attach active可用；绝不静默丢附件/把Steer拒绝转Prompt | §3 W20 |
| W21 | 06 §1.9 L223–231；§2.2 L336–352 | Steer接受与恢复 | 直接：native队列/Turn fence；服务端独立pending occurrence receipt，仅ACK后尾泡；snapshot可恢复 | 拒绝inactive/compression/terminal区分，响应丢失不永久假ACK；禁止correction_offsets猜inventory | §3 W21 |
| W22 | 06 §1.9 L227；§2.3 L354–368 | Withdraw | 直接：同owner锁确切一次withdraw，已consume不可撤；成功overwrite Composer并退不兼容edit | 双撤/consume/finish/interrupt竞态只有一个赢；未知不抹真实行；accepted全集终态守恒 | §3 W22 |
| W23 | 06 §1.9 L229–231；§2.3 L366–368 | 消费/自然finish | 直接：同插点所有pending按接收序成一真实User；finish前未消费由native finalizer恰一followup | 消费IDs与真实行对应，UI即刻收敛且无时间猜测；刷新/切换不丢ACK纠正 | §3 W23 |
| W24 | 06 §1.10 L235；§1.8 L216–219 | Stop | 直接：无pending只停止当前Turn，保留未提交text/附件且无后续Prompt | 正式原生interrupt路径无意外followup，切换/断连不等于Stop | §3 W24 |
| W25 | 06 §1.10 L236；§2.4 L370–381 | Interrupt原子交接/薄弱工程接缝 | 直接+必要推导：选取/预留/旧Turn不能再consume/唯一新Prompt admission同一权威屏障；非两RPC拼接 | consume/withdraw/finalizer/rotation/重试并发无丢重；outcome区分已admit/无pending/退役/非active/拒绝/unknown并可查询 | §3 W25 |
| W26 | 06 §1.10 L237–240 | Cancel Send | 直接：pre-admission取消剩余传输并恢复captured text+binary覆盖新输入；不能当session.interrupt | 已upload残留不再提交；可能accepted时显式submitted/unknown/rejected，不盲重试/补偿；所有事务阶段可恢复 | §3 W26 |
| W27 | 06 §1.11 L242–250；C51 | Rewind交互 | 直接：persisted User eligible；入edit保存draft/隐藏target及后续含临时nodes/恢复附件；退出完整恢复 | Send+一层红色确认，拒绝/取消安全；reload无armed metadata；native文本undo不倒数据库/FS | §3 W27 |
| W28 | 06 §1.11 L247–250；§3.4 L489 | Rewind原生事务 | 直接：correct durable target走prompt.submit截断，busy按Desktop中断语义不能变queued/steer | 接受后真实历史为准；错误不永久遮行；Notebook有效路径/Anchor reconciliation继承K02 | §3 W28 |
| W29 | 06 §1.12 L252–262 | Slash dispatch | 直接：真实native目录动态能力；completion≠执行，navigation/control/result各正式分流，terminal-only过滤不删registry | typed/suggestion/pill/shortcut同动作；不误发command为普通Prompt；skills/bundles/plugin按真实可执行性 | §3 W29 |
| W30 | 06 §1.4 L169；§1.12 L258–262；§2.7 L412–420；C61 | Notebook临时人类视图 | 直接：native readonly结果仅requester临时Assistant样式，调用时序列边界固定，新消息其后；四区状态字段Schedule可读 | 当前Snapshot created_at或明确none，无Anchor/pointer/audit；不DB/model/Turn/Memo；refresh可丢；CLI/TUI保持 | §3 W30 |
| W31 | 06 §1.13 L264–280；C11/C16/C54 | Usage/Context | 直接：浮动，不独占composer下高度/New Chat不见；Session/Latest等尺寸；active留上次completed，turn终才更新 | input/cache-read/output、trueTurns/modelcalls与native来源；ratio语义正确，无cache-write/猜数字；Context真usage/max | §3 W31 |
| W32 | 06 §1.14 L282–288；§2.5 L383–396 | Compaction控制 | 直接：原ring同尺寸Compacting、展开替换Cancel；仅cancel compression、generation commit互斥 | 手动/自动/isolated-host分支，cancel/too-late/finished/error真结果；不停止Turn/丢pending/半历史 | §3 W32 |
| W33 | 06 §1.14 L288；§2.8 L428 | Compaction历史 | 直接：真实summary/handoff正确位置默认折叠；separate/composite/no-text/rotation/archived祖先 | 无合成notice、原始用户身份不复制、可展开原文；不实现Full audit | §3 W33 |
| W34 | 06 §1.15 L290–304 | Orb/Memo呈现 | 直接：existing Conversation+global on；local off仍可见；真实task执行/完成才亮；首层仅count，二层完整ordered memo替换首层 | 无run/stop/toggle/edit；无guessed countdown；entry/switch/reconnect refetch，event当前owner；C45末帧不闪/C50仅既定动画 | §3 W34 |
| W35 | 06 §2.6 L404–410 | Secretary read来源 | 直接：profile/Conversation owner，真实task registry非stale running DB；idle绝对due/未知；memo current | 无快轮询、无第二socket；不跨会话paint，不查阅触发Noting/ACK；完整关闭模式 | §3 W35 |
| W36 | 06 §1.16 L306–312；C17/C18 | Files | 直接：backend default cwd只读list/preview/download；不改历史cwd；真实相对breadcrumb根强调；成熟库多常用格式 | 授权边界/MIME/size，loading/empty/notfound/denied/unsupported/oversize；无写/改名/上传folder；text折行 | §3 W36 |
| W37 | 06 §2.1 L319–334；§2.8–2.9 L422–437；§3.7 L511–523 | 新增机制依据 | 直接：每功能N/F/A/D；A先真实source audit+失败不变量、mini-contract及最终name manifest | owner/file/reason/IDs/errors/timeout/lock/event/persistence/compat/tests齐备；无冗余API/未来scaffold | §3 W37 |
| W38 | 06 §3.1 L445–459；§4.5 L601 | transport/security | 直接：实际browser auth/origin REST+WS路径、URL/文件权限可信；local部署范围 | unauth/bad-origin拒绝、敏感数据/Markdown安全、真实连接；不将localhost替代所有鉴权证明 | §3 W38 |
| W39 | 06 §3.3 L477–479；C49 | 重连/断线 | 直接：epoch与bounded replay/truncated触发REST+runtime resync；不重发accepted Prompt；断连仅Composer持续提示并禁Send | 保留history/list/draft/in-memory；文件自身错误；epoch/seq/route race无串流或假完成 | §3 W39 |
| W40 | 06 §4.2 L546–558 | 设计系统 | 直接：统一semantic tokens/components states、reduced-motion响应式；不得散落颜色/重复magic/页级替代复用 | 检查tokens与共享组件治理，例外有依据；保持既定Mock（C40），不以后接线重设计 | §3 W40 |
| W41 | 06 §4.3–4.4 L560–581；C19–21/C28 | 角色与Mock交接 | 直接：视觉只样式，技术不得改产品；另行视觉交回与正式组件一致，静态Mock独立无backend/model | 可点击全场景Mock URL与逐条对账；视觉worktree授权边界；不得拿Mock当功能证据 | §3 W41 |
| W42 | 06 §4.5–4.6 L583–611；C05/C06 | 证据范围 | 直接：真实REST+WS browser、DeepSeek图像/Noting、race/native；四viewport完整可用；真机keyboard/camera/swipe后续专项 | 证据版本/底座不绕过待测机制；无falsegreen；Verification不替代Validation，真机延期明确 | §3 W42 |
| W43 | 06 §4.6 L610；C04 | V1.6移交 | 直接：复用有效旧证据、仅补移交缺口/实际影响，不重复旧轮全量门禁 | 明确移交清单与每项当前支持证据；缺原文索取，不以实现状态/旧结论作判据 | §3 W43 |
| W44 | 06 §4.7 L613–617；§5 L621–645 | 范围/交付 | 直接：当前rev/diff、N/F/A理由、compat、实证矩阵、设计治理、无新service/DB/cache、未完清单 | 排除Full audit UI、历史Snapshot浏览、Files写/workspace、多平台/个人Memory/cloud；没有未授权实现 | §3 W44 |
| W45 | C32–35/C39/C43–48/C50/C52–53 | 用户视觉修訂 | 直接：deferred箭头紧标题、原卡内展开无第二due/内框；Parameters无JSON标题深底横滚/留白，Result约10行内部滚/原卡底；卡高一致 | 逐项正式组件与Mock一致；Thinking间隔、百分比与标签规则见W11/W12；无擅改active动画 | §3 W45 |
| W46 | C36；06 §1.9/§2.4 | 用户接受容量边界 | 直接：每Turn256 Steer、64不同Interrupt请求、共享同会话一个Main可换客户端、image原生context且本体留server获授权；32旧压缩状态和8结束Turn窗口未获确认 | 限额不被写成用户全认可；必要错误/退役/幂等守恒仍须满足W21–26；影响证据完整 | §3 W46 |
| K01 | 02 §1 L18–256；04 §2.1–2.2；01 §1–2 | 继承身份/资格 | 直接：Conversation owner opaque，compression同owner、branch/reset新owner、alias冲突closed；eligible Main与auxiliary隔离 | 受本轮入口/压缩/重连影响的路径不能改所有权、创建平行registry；profile明确 | §3 K01 |
| K02 | 02 §2.6–2.7 L575–643；§6.11 | 继承Rewind/Anchor | 直接：重写后最新有效Anchor Snapshot pointer；运行Noting不取消，commit前重验；branch独立继承 | 本轮Rewind与busy/compaction正式路径保持，invalid Anchor不commit，不跨owner | §3 K02 |
| K03 | 02 §3.1–3.4 L648–760 | 继承存储 | 直接：仅state.db Secretary表；Snapshot/item INSERT-only、ordered ids/lineage与pointer原子，不改核心schema | 本轮变动不破坏原子性/不可变/版本推进；archived不出正常view | §3 K03 |
| K04 | 02 §2.3 L289–349；04 §2.6/§3.1 | 继承History | 直接：eligible Main always history/guidance；current valid跨compaction、排rewind；compact结果与full read定位、权限不变 | 本轮路径/原生关闭下保持；查询不引入其他Conversation/文件/NM；来源UID/timestamp完整 | §3 K04 |
| K05 | 02 §2.5/§3.5–3.7 L357–573,762–870 | 继承Notebook | 直接：四区十类合法fields/status；主只读+memo，Noting三个write，short new-version id；archive不可恢复 | 人类与AI独立projection；current+time，AI额外anchor仅；无termination/archived/audit泄漏 | §3 K05 |
| K06 | 02 §3.5 L782–804 | 继承Memo | 直接：per-Conversation ordered连续index；非空autoenable且阻off；不触发run；冻结memo与Snapshot同Anchor原子消费仅未变项 | 并发add/replace/delete或无commit不误clear；当前memo人类readonly与模型Markdown一致 | §3 K06 |
| K07 | 02 §3.8–3.12 L872–1085；04 §5 | 继承Schedule/Reminder | 直接：仅四类schedule、secretary_task explicit mode；复用parse/timezone而非Cron任务；durable due claim/restart/no loss | 只读Web不得触发/ACK；idle instant native admission/busy转deferred；off保留，on不过度replay | §3 K07 |
| K08 | 02 §4.1–4.4 L1091–1172；04 §3.4–3.5 | 继承开关/原生 | 直接：global/local gate分离；下一Main pre-message同步prompt/schema/dispatch，warm/cold；disabled无Noting副作用 | local off不重建prompt/tool且读保留；global off/aux原生行为；本轮新增hook不污染未启用 | §3 K08 |
| K09 | 02 §4.5 L1174–1195；C57 | 继承Idle事件 | 直接：Main结束arm、开始cancel；一period一次事件、deadline统一读local off消费；catchup仅漏事件，非polling反复触发 | existing registry/lock/timer/native host接缝、reaper last非免死；profile≥15秒仅本轮运行要求 | §3 K09 |
| K10 | 02 §4.6–4.13 L1197–1387 | 继承Force/Compaction | 直接：原生计数与确切reserve公式/2失败；freeze ordinary Anchor，sameAnchorDB去重、不同Anchor并发；force成功由快照位置推导 | 本轮压缩/取消影响下native优先不等Noting；无独立flag/threshold/counter/loop | §3 K10 |
| K11 | 04 §4.5 L262–281；02 §5.2 | 继承D01 | 直接：最近实际native/external单事实派发点记录、native原样external在freeze之前拒绝；无请求不覆盖、unknown不新拒绝 | Force内存/Idle和resume现有model_config一致；原生fallback和rotation，不另比model/cache热度 | §3 K11 |
| K12 | 02 §5.2–5.5 L1404–1540；§6.16 | 继承Noting前缀/生命周期 | 直接：真实persistent child独立DB/owner/close/no父seed/no crashresume；每次request同 frozen root/tools/messages+自有suffix，whitelist独立 | 首/两后续/重试/continuation/Parent并发压缩+真实cache实证；无provider改造；工具后缀完整且重复新control | §3 K12 |
| K13 | 02 §5.7–5.10 L1713–1831 | 继承任务完成 | 直接：同child≤5Turns；ordinary finish(reason)/special compact_parent；forced及context_overflow仍Commit Gate，true失败不commit | special fallback无第六Turn；parent compactionadmitted成功不被后cancel撤销Snapshot/Finish；termination四态仅audit | §3 K13 |
| K14 | 02 §5.6 L1542–1627；§6.17 | 继承Deferred | 直接：真实active request build前durable一batch user row，schedule→due_at；不timestamp，不scheduler idle入史；actual carried+response后ACK | compaction pass拒materialize、失败/丢载荷留pending、retired terminated，retry/重启无丢无无限重复 | §3 K14 |
| K15 | 02 §5.6 L1629–1702 | 继承Framework/Instant | 直接：instant native user timestamp；Framework由live runtime双写tail busy/fence后写不start，不durable pending；Finish仅validSnapshot一次 | Force dispatch上下interval成功compaction过期含queue/head/tail/summary/replay而history留；failed/cancel/noop不提前过期；external抑制规则 | §3 K15 |
| K16 | 02 §5.6 L1544–1585,1704–1711；C39 | 继承时间 | 直接：产品absolute time readable含timezone，Web timeline按用户C39覆写显示格式；只realuser/instant marker单次entry | source/event/entry不混，retry不重mint；noting-task/deferred/framework无marker，原始content不改 | §3 K16 |
| K17 | 02 §5.12 L1848–2213 | 继承prompt Target | 直接：最新Target逐字，Noting现行三工具/新Notebook view/Memo/Secretary role/cron区分、continuation、carrier | 受本轮影响或V1.6移交文本可核精确字节与gate；旧Frozen不能压Target；未启用原生文字不改 | §3 K17 |
| K18 | 04 §6 L372–396；02 §2.5 L536–573 | 继承Persistence Proposal | 直接：candidate仅线索，native Slash正常Main自主history检证，不prefetch源全文；提案+明确批准才写，讨论非批准 | 本轮slash可达路径不越权、Noting不外写；未受影响基础复用有效证据，不重复旧全门禁 | §3 K18 |
| K19 | 02 §2.4 L351–355；04 §2.3–2.5 | 继承三Foreground | 直接：Active真request/History有效原文/Full Prelude+Message identity，composite唯双投影；读取无副作用 | 仅本轮identity/compaction/rewind/read影响审基础，不实现Full audit UI；缺来源诚实 | §3 K19 |

## 3. 逐条实现证据

本节为首次完整初审结论。`符合`只覆盖该行要求及明确的证据边界，不代表整轮通过。前端源码下列简称 FE，根目录为 `../hermes-secretary-web/`；BE 为本仓。证据目录简称：

- MAIN：`.hermes-dev/round2-evidence/main-final-integration/`，最终 `repair-delivery-manifest.json` 的后端24510d1/产品4443aa7、前端c55120f；前端后来仅分页改为002f7a2，按差异复用。
- ATT：`.hermes-dev/round2-evidence/attachment-budget/`，500MB实际上传/模型读取/取消及来源manifest；正常分片链证据与最后错误输入guard版本区别见plan，不冒热载新guard。
- READ：`.hermes-dev/round2-evidence/reads/`，12源码hash匹配，53 distinct（自身读/压缩、真实Child、legacy fence/timer；分批日志不能相加重计）。
- PENDING：`.hermes-dev/round2-evidence/pending/`，owner提交109 distinct证据；`last-integrated.log`为91子集、`final-owner-lock-tests.log`为62子集，后续source投影与usage薄接线另核，不当同版本整套109重跑。
- USAGE：`.hermes-dev/round2-evidence/usage/`，`final-tests.log` 23 distinct/4文件/11.8s；新增source observer不改变canonical会计，对应新差异另审。
- COLD：`.hermes-dev/round2-evidence/cold-resume-fix/`，最终6核心源码hash匹配，原Root/history/UID/profile恢复及竞态定向证据。
- NATIVE：`repair-native-messages.md`及对应保留日志/源码SHA，正式原生插入、flush、completion receipt受控provider证据，最终12 distinct而非把两包重复相加。
- V16：`v16-handoff-evidence.md` §4、§8–12及`.hermes-dev/round2-evidence/v16-live/`，旧移交原文在`.autonomous/20261011-v1.6-implementation/continuation-guide.md`；§8–12实际产品5ccc619、cold修复37ce184，受影响源码/后续delta逐项核查，非用文档HEAD冒称产品已验。
- 独立反例与paging日志：`.hermes-dev/round2-verification/`。三个rewind反例运行生产TS模块，没有HTTP服务/模型；paging日志为Main按C67执行的1项定向例。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| W01 | App→useExternalStoreRuntime/Provider/ThreadPrimitive.Root；TimelineMessages与Markdown；api/client→原REST/WS | React/独立仓/无BFF成立；但消息通过自定义nodes.map与ReactMarkdown直接绘制，未消费assistant-ui消息订阅组件 | FE App.tsx:468、585、TimelineMessages；06§1.1；C71 | 不符合：框架只作外壳，未达到interaction/component foundation，见V-R2-05 | 未将框架浅接入直接当作滞后的已证实根因 |
| W02 | DraftStorage→IndexedDB；route/preferences→localStorage；Controller runtime maps | 仅草稿文本/Blob/refs/模型选择、路由/滚动/呈现偏好持久化；业务响应、绑定、pending、临时Notebook仅内存 | FE core/drafts.ts、route.ts、preferences.ts、controller.ts；controller.test.ts | 符合：持久化allowlist与releaseInactiveViews边界清楚 | reload不恢复已淘汰操作receipt，按C66 |
| W03 | file.attach注册→prompt_attachments helpers→前端stageBlobAttachment | 既有方法增加分片/abort/stat参数及返回shape；旧调用成功shape不变不能豁免明确合同 | BE contracts/prompt_voice.py:172；methods_prompt.py:950；FE api/attachments.ts | 不符合：V-R2-01 | 其它新增方法使用新名；新source只读观察字段不替换既有字段 |
| W04 | Controller select/refresh→REST；secretary.state/notebook_read→web_read | 不以ensure/create/Trigger填空；只读before/after表计数一致，unknown/error不猜idle；profile/route generation防串 | READ证据、BE secretary/web_read.py；FE controller readSecretary/readNotebook | 符合：既有查询和新只读投影无业务写入 | session.resume的原生attach生命周期与单纯Secretary读取分开 |
| W05 | design/layout/primitives、App New Chat、theme preferences | 英文六欢迎标题、无头像/副标题、三图标主题；New Chat不显示Usage/Context；品牌素材限定位置 | FE design/与App；MAIN repair-welcome-final.json、new-four-viewports.json | 符合：正式组件和现存四视口证据一致 | 不以静态Mock代替功能证据；真机未测 |
| W06 | route.ts→navigate/backToChat；FilesBreadcrumb/Sidebar | 三主路由；返回目标显式保存、入Files前草稿/scroll归属；无history.back模拟返回，无切换Stop | FE route/controller.ts、components/Files.tsx；MAIN files-four-viewports.json；controller.test.ts | 符合：正式返回、fallback与session运行相互独立 | 历史cwd不会因Files浏览被改 |
| W07 | parseRoute/popstate→select；scroll/draft恢复；Files preview route | 真实history push/pop；合法路由恢复与错误安全呈现；不劫持系统swipe | FE core/route.ts、useTimelineReading及Files；controller route测试 | 符合：刷新与浏览器历史有正式接线 | 真机系统侧滑按C05延期 |
| W08 | Controller create/send/list/select；App Sidebar | 首Send single-flight/idempotency_key才create；切换旧Turn继续；列表来自无cwd过滤REST；C72现场Turn边界列表闪动重新打开呈现证据 | FE controller.ts:435与App.tsx:709；controller.test.ts；C72 | 证据不足：生命周期机制成立，新增侧栏闪动尚未闭合，见U-R2-03 | 不把listLoading提示存在直接等同已定位全部闪动原因 |
| W09 | stored REST→bindFlight→resume/activate→runtime memory map | 压缩currenttip同Conversation；cold/epoch失效重绑；single-flight；不以空legacy resume当历史存在 | FE controller.ts；BE session_agent_context.py；COLD与H04-F14 proof | 符合：正式绑定、cold hydration与owner边界有证据 | 非目标compute-host不读代理冒充真实owner |
| W10 | projectMessage/projectTimelineNodes→nativeSource receipt→TimelineMessages | UID/row/tool-call identity定位；Framework/instant/deferred使用来源字段；consumed真实消息可在DBflush前呈现；不按正文或时间配对 | FE core/projection.ts；BE pending_steer.py/prompt_turn.py；NATIVE与MAIN repair-real-source-proof.json | 符合：常规history/live/pending同一投影，来源边界未知时不伪造 | 编辑期间临时节点错误单列W27/V-R2-03；性能见W13 |
| W11 | native tool IDs→project工具配对→design ActivityCard | Thinking分段running展开/结束折叠；每tool occurrence同卡Parameters/Result；status明确；原Framework折叠 | FE projection/design/chat.tsx；MAIN repair-tool-failed.dom.txt、repair-real-source-proof.json；presentation测试 | 符合：真实exit7为Failed，工具结束不冒Turn结束 | 未知tool结果保Unknown，不从同名配对 |
| W12 | content/timestamp formatter→Message；theme.css阅读边界 | 只显示真实User/Assistant时间；marker仅显示层剥离；User12/3%、Assistant4/10%、居中时间、无时区，原content不变 | FE content.ts/design/chat.tsx/theme.css；MAIN repair-four-viewports.json | 符合：四视口实际margin与当前用户修订一致 | C15底层AI/人类时间带时区，与Web展示覆写不混 |
| W13 | HISTORY_PAGE_SIZE=200→REST分页；useTimelineReading；reduceNativeEvent | 200/200、已加载range与锚点保留测试通过；source/native顺序证据有效，但C70再次实测模型完成后Timeline仍缓慢输出 | FE controller/projection；paging-test.log（1pass）；MAIN repair-*；latest-user-session.json | 证据不足：顺序/分页证据保留，吞吐/terminal→DOM及时呈现待真实定向取证，U-R2-02 | 未认定存在显式限速；未使用依赖中的useSmooth作根因 |
| W14 | Markdown urlTransform/components→原生approval/clarify handlers | http(s)与安全Markdown；local/file不自动打开；代码copy；原工具状态和输入对话分开；断流保留unknown | FE App Markdown、ChatDialogs、controller event handling；contracts/presentation测试 | 符合：无HTML执行旁路或工具终态伪装Turn完成 | 未进行独立渗透测试，结论限当前功能/原生边界 |
| W15 | ChatComposer textarea onKeys/onChange→shared perform | Enter/Shift+Enter/IME/Escape已有实际组件矩阵；Ctrl/Meta编辑键未主动映射业务Rewind；C69实际Ctrl+Z无效未复现关闭 | FE ChatComposer.tsx；timeline.test.tsx；C69/C70 | 证据不足：既有测试未证明真实草稿独立undo，见U-R2-01 | 撤回Esc/Stop后端失效推断；不将键盘单元通过覆盖现场反馈 |
| W16 | DraftStorage keyed profile/route；native model.options/config→selector→set配置 | binary reload恢复；选择草稿不改别route；当前model/reasoning来自实际配置，二级直接高亮 | FE drafts/controller/ChatSelectors；MAIN repair-model-menu.dom.txt、repair-reasoning-menu.dom.txt；ATT | 符合：真实选项/当前值与草稿分区机制接线 | 无法获得真实option时明确不可用，不造模型列表 |
| W17 | select/paste/drop→draft attachments；sourceAttachments+userAttachmentDisplayText→历史chips | 选择不upload，Files与Photos/Camera分开；重复名独立；历史正文剥注入、长名ellipsis/title，图片按原生identity恢复 | FE attachments/content/ChatComposer/design；ATT selection-no-upload.json；MAIN repair-four-viewports.json | 符合：常规选择与历史呈现有效 | Rewind恢复正文仍有V-R2-04，不能以常规history通过豁免 |
| W18 | draftBudget→chunk upload→native refs→submit→真实Main terminal读取 | 500000000边界、额外1byte拒绝、删除释放、reload Blob；单500MB与同名2×250MB源/服务端SHA一致，真实模型读首尾+stat | ATT single-500MB-proof.json、pair-500MB-and-cancel-proof.json、cancel-final-proof.json；plan附件段 | 符合：容量端到端有真实链路，不只ACK | 原生图片/PDF原有限制保留；renderer RSS非独立页heap；RPC合同违规单列W03 |
| W19 | stageBlobAttachment/explicit image_paths→submit_idle→native image parser | 普通file/PDF ref_text，非pdf.attach；图片像素走原生image路径且同runtime；DeepSeek真实读73729图与普通文件 | FE api/attachments；BE methods_submit_idle/prompt附件；MAIN repair-pixels-complete.dom.txt；ATT | 符合：按§6精化的verified equivalent native Image机制 | 不是500MB图片理解证明，不声称辅助视觉转述 |
| W20 | primaryAction→command-actions.perform→Controller | 普通idle/active/附件/Pending矩阵有测试；edit未进入selector，active编辑被优先Steer | FE App.tsx:529、command-actions.ts:190；独立rewind-active-proof.json | 不符合：V-R2-02，主操作与编辑事务语义冲突 | 普通非edit矩阵的通过不抵消正式错误分支 |
| W21 | session.steer_pending→PendingSteerBuffer.enqueue/snapshot；uncertainSteers重读 | 同Agent原slot/锁，turn/op identity去重与conflict；accept后才尾泡；pending_changed invalidation查真实snapshot；拒绝/unknown有区别 | BE agent/pending_steer.py、methods_pending.py；PENDING；FE controller tests | 符合：并非offsets或前端权威队列 | 有限receipt依C66；reload不恢复历史op结果 |
| W22 | steer_withdraw→同_pending_steer_lock→claimed/pending状态；Controller withdraw | consume/withdraw同锁单赢家；成功overwrite草稿并退出不兼容edit；已consumed不可撤 | BE pending_steer.py；PENDING race/owner-lock；FE withdraw测试 | 符合：服务端occurrence状态守恒，未知不删真实行 | UI exit animation只呈现，不延长withdraw权限 |
| W23 | native take→append_claimed_batch→real User；finalizer→settle/handoff→native admission | 同插点接收序合并一User/UID；無slot requeue原order；自然finish恰一followup，正式currenttip与generation | PENDING正式native Loop测试；NATIVE；MAIN repair-steer-final.dom.txt | 符合：插入receipt与持久映射来自同owner | 不是每个provider组合实测；外部返回受控测试和真实DeepSeek分开 |
| W24 | Controller.stop→session.interrupt→native interrupt/finalizer | 无pending只Stop；草稿不丢、无补发；真实日志22:42:48.821→.916 interrupted约95ms | FE controller；BE methods_session_interrupt；latest-user-session.json；PENDING regression | 符合：已取得后端实际停止，不支持“按钮/ESC后端无效”推断 | 用户3次操作不可强行一一对应2条日志；Timeline滞后另审W13 |
| W25 | interrupt_pending.reserve→stop→settlement barrier→_pending_dispatch_handoff→native submit | admission/history→pending锁序；预留使旧Turn不可consume；_stop_done/_settled双条件；同op只准入一次；query区分unknown/失败 | BE methods_pending/pending_steer/prompt_turn；PENDING自然/interrupt/rotation/Stop竞态；runtime真实Interrupt证据 | 符合：由原生owner完成原子交接，无客户端两RPC拼接 | accepted是实际准入非Stop ACK；非目标hosted明确不支持 |
| W26 | sending transaction→prepare/upload/submit阶段→cancelSend/inspectSubmission | pre-admission恢复captured draft/binary且取消剩余upload；submitting未知只inspect、不Stop/重试；晚ACK按tx owner过滤 | FE controller/api attachments tests；ATT browser-cancel*、cancel-final-proof.json | 符合：真实500MB取消marker user rows=0并保草稿 | 首次赶不上Cancel操作保留为未执行；crash残片清理不承诺 |
| W27 | beginEdit→App投影截断→perform confirm→send/exitEdit | active编辑走Steer；后续temporary移到顶部/Pending仍见；真实附件作者193字变579字包含Attached Context | 独立rewind-active-proof.json、rewind-proof.json、rewind-attachment-proof.json；§5三条 | 不符合：V-R2-02/03/04 | idle单确认截图只能证明一个成功面，不能覆盖这些生产模块反例 |
| W28 | send→submitNative→submit_idle truncate_before_message；4009原生interrupt后重交 | 底层busy rewind正式事务存在、拒绝可恢复；UI active path却在到达事务前转Steer | BE methods_submit_idle/methods_prompt；FE controller；独立active反例 | 不符合：V-R2-02，helper正确但正式入口不可达 | 原生Anchor/rewrite机制由K02保留，并未判其本身有错 |
| W29 | command catalog/completion→createCommandActions→native dispatch或导航/临时结果 | terminal-only过滤显示，registry不改；Notebook走只读；模型/分支/控制各走正式能力，不作为普通Prompt乱发 | FE commands/command-actions/controller；BE command dispatch；controller/commands测试 | 符合：动态native目录和执行能力分离 | active Rewind正文slash应先编辑确认，已纳V-R2-02修复条件 |
| W30 | Notebook command→request-time boundary→notebook_read→temporary结构化view | 四区/fields/status/Schedule可读；created_at/noSnapshot明确，无Anchor/audit；临时行不DB/模型，后消息其后 | BE secretary/web_read/renderer；READ before-after；MAIN repair-notebook-sequence.json与图 | 符合：正常命令时序和只读来源真实 | Rewind切除范围临时节点失效另由V-R2-03阻断 |
| W31 | native dispatch/canonical account→usage_read→usage_detail→Utilities | input/cache-read/output来源与null语义；active留上次completed；真实completed Turn计数；latest modelcalls非assistant rows推算 | USAGE 23 distinct正式Loop；FE controller/design indicators；MAIN repair-native-complete-receipts.json | 符合：模型调用/会计/完成边界一致 | cold旧Session总计未知、外部/MoA不可观测null，非伪造0 |
| W32 | compaction_state/cancel→CompressionCommitFence→publish result；Controller轮询状态 | generation下cancel/commit互斥，仅取消compression；queuedPrompt和Noting成功Snapshot不撤；pending保留 | BE compression_read、compression facade；READ 53 distinct；runtime真实manual compaction证据 | 符合：目标in-process原生接缝/失败结果有效 | hosted返回明确4010，未桥接非本轮目标模式；不假称所有平台实测 |
| W33 | REST原raw carrier/archived lineage→native-compaction projector | separate/composite/no text与rotation按真实字段展示折叠原文，不造完成notice/重复user身份 | FE core/native-compaction.ts/projection；timeline/contracts tests；实际manualcompaction记录 | 符合：历史投影保来源、不实现Full audit | 完整Full Foreground审计UI依division5排除 |
| W34 | secretary.state+changed invalidation→Orb/Memo panel | global/local资格、真实task registry控制亮态；count→ordered完整memo二层；无run/stop/toggle/edit控件 | FE Utilities/design indicators；BE secretary/web_read；MAIN repair-noting-idle.dom.txt、repair-motion-* | 符合：任务状态与面板只读，既定active动画保留 | 动效末帧证据按对应版本复用，不是实机GPU全面测试 |
| W35 | web_read解析profile/stored/Conversation→runtime registry/timer/Memo | 不靠stale running DB；absolute due/unknown；进入/切换/reconnect读取，事件同WS；无Noting快轮询/触发/ACK | READ全部12源码hash一致及正式dispatch/negative测试；H07 profile隔离 | 符合：来源与权限边界真实 | 数据不存在不创建Conversation/Agent补齐 |
| W36 | Files→native default-cwd/list/read-text/download→@file-viewer | 只读授权路径/MIME/size；loading/empty/error/unsupported；breadcrumb与折行；成熟Office/PDF/media renderers | FE api/files、Files/FileViewerPreview；MAIN files-four-viewports；runtime video-preview/playback-proof | 符合：文件浏览/预览基础正式链可用 | video证据只短时播放观察，非完整媒体/所有格式兼容性；独立Validation仍须典型用户旅程 |
| W37 | native-compatibility N/F/A audit→新增contracts/register→mini-contract owner报告 | Pending/Interrupt/compaction/readonly/usage/submit-idle有缺口依据/owner/错误/测试；file.attach直接扩旧合同不符A新名规则 | native-compatibility.md、各implementation报告；BE registry/contracts；§5 | 不符合：V-R2-01，附件增量应恢复旧合同并新名接线 | 只读source字段允许增量，未替换原字段或mint旧identity |
| W38 | Vite同源proxy/bootstrap→原生header token/WS origin guards | 53445及5173：health24510d1；无token/api/sessions=401；无token和正确token+bad-origin WS=403；仅握手未发RPC | 独立transport-auth-proof.json；BE web_server.py/web_server_chat.py；FE client | 符合：当前实际REST/WS拒绝与旧成功browser链互补 | 首次服务停机Connection refused不作拒绝证据；loopback非远程/公网认证验证 |
| W39 | Gateway attempt owner/fresh bootstrap→epoch/replay→Controller resync | 单socket/singleflight；truncated走REST+runtime读；断线pending RPC Indeterminate不重发；保history/draft/editable，Send禁用 | FE api/client 7例、controller replay tests；MAIN repair-disconnected*、repair-reconnect-final.json | 符合：真实服务token轮换后同页恢复证据与代码一致 | 刷新不恢复临时Notebook/旧op receipt；网络所有故障组合未测 |
| W40 | design tokens.css→共享layout/chat/primitives/indicators/files；reduced-motion | 颜色/字体/间距/状态集中；正式与Mock共享组件；focus/disabled/responsive，已确认视觉边界保留 | FE design/、visual-design/static-mock报告；MAIN四视口与CSS几何 | 符合：共享设计治理存在，没有把设计仅作最后皮肤 | assistant-ui消息组件欠接入在W01，不能以tokens通过豁免 |
| W41 | visual独立worktree→shared design props→静态Mock route | Mock无backend/model；正式复用同组件，技术/视觉职责分开；C32–C61修订对应实际组件对账 | static-mock.md、visual-design.md、repair-original-visual-audit.md；mock tests与MAIN几何 | 符合：Mock交接与功能证据区分清楚 | 已批准可点击Mock不代表全产品通过 |
| W42 | 正式REST/WS+DeepSeek+四viewport；canonical runner正式模块 | 真实图像/附件/Noting/控制/失败、macOS Chromium320/390/1024/1440；旧失败与skip留痕 | MAIN/ATT/V16及READ/PENDING/USAGE；§4方法审查 | 符合：已提供的开发证据底座真实且边界可审 | 本行只判证据方法，W13/W15/W08的新未闭合事实仍阻断；无全suite声明 |
| W43 | 旧continuation-guide→v16-handoff H02–H08→H04-F14新周期 | C15/C16/VAL04/Persistence/Reminder/profile/globalcold/branchundo明确移交并对应实证；旧cache等按未改路径复用 | V16 §8–12、H04-F14 proof/manifest、旧continuation-guide | 符合：未将旧失败删除或以自评替代本轮逐项核查 | H05多余3次空跨会话搜保留；完整旧版重验不在范围 |
| W44 | 两仓diff/版本+manifest+N/F/A+D；当前交付范围 | 无新service/业务DB/API hierarchy、Full audit或个人Memory依赖；本地证据与未完成清单明确 | snapshot-index/baseline；git delta37ad→24510d；FE002f7a2；本报告 | 符合：实施范围和交付记录可追溯 | 当前门禁不通过，不能用本行作整轮完成声明；未push/部署 |
| W45 | shared design chat/indicators/theme→正式/Mock | Reminder蓝标题紧箭头、无二次due框；工具同卡两区/无JSONlabel、Parameters深底横滚16px、Result十行原背景；统一折叠卡高 | MAIN parameters-390-proof/tool-result-proof/reminder-proof、repair-*；visual对账 | 符合：源码、实际几何和既定视觉同向 | 新增侧栏闪动C72另列，不擅自扩大美术改造 |
| W46 | PendingSteerBuffer epoch/operation retention；compression terminal ring；reload | 256/64获C36；8ended/32terminal获C66；current另留，过期unknown，refresh从真实历史/状态恢复不重发 | BE pending_steer/compression_read；FE recover/select；§6C66；PENDING/READ tests | 符合：原未授权窗口现经直接条件追认 | 不声称手动刷新可恢复已淘汰旧operation结果 |
| K01 | 原Conversation resolver/aliases→new read和native resume | 新投影显式profile/owner，compression同Ref、branch新Ref；eligible/aux与Main边界未被新registry替代 | BE secretary/web_read/session_agent_context；V16 H07/H08；READ | 符合：本轮受影响identity接缝保持 | 范围是本轮delta和明确移交，不重审全部Core |
| K02 | native truncate/undo/branch→Anchor reconciliation→Noting commit gate | 新submit_idle复用旧Prompt事务；branch/undo真实有效源与父Notebook隔离；cold恢复保UID | BE methods_prompt/submit_idle；V16 H08-effective-source-proof、H04-F14 | 符合：底层继承事务保持有效 | 正式Web edit可达性失败见W28，不能拿本行豁免 |
| K03 | state.db既有Secretary stores/atomic pointer；新增均内存投影 | 本轮未改Hermes表ownership/schema或Snapshot INSERT-only模型；只读增量不写 | git delta；READ before/after counts；V16当前Snapshot/branch证据 | 符合：受影响存储不变量未破坏 | 无迁移兼容承诺；运行测试库隔离 |
| K04 | 原session_history工具→有效源/UID/可读time；cold prefix恢复 | H08撤销银色原UID不再出现；parent原文保持；current valid跨compaction机制未替换 | V16 H08/H04-D/C15 actual proof；BE session_agent_context审查 | 符合：本轮有效历史/原文路径保持 | H05模型多余跨会话空搜是行为偏差，未引用/泄漏其结果 |
| K05 | 原Notebook renderer→new human readonly结构化view | 四区有效条目/status，current created_at；human不露Anchor/termination/audit；AI层未改权限 | BE secretary/web_read与现renderer；READ/H04-D/H05-final-items-human | 符合：人类与AI投影边界保持 | 无Snapshot时明确none，不合成空成功快照 |
| K06 | noting_memo原owner→web readonly列表→原Snapshot commit消费 | 只读不autoenable/Trigger/clear；真实H03 add/list/replace/delete与busy auto-on、后新Idle消费 | V16 H03-summary/busy-memo-main；READ before-after；BE web_read | 符合：本轮读入口不破坏原memo原子性 | 并发commit未改owner，复用原机制证据 |
| K07 | 原Schedule registry/scanner→instant/deferred→ACK；Web纯读 | H06一次提醒/offon、H07 busy转deferred/profile隔离，真实due及ACK；无Cron新任务 | V16 H06-H07 carrier/ack proof；BE只读审查 | 符合：真实Reminder链和只读不消费均有证据 | 失败重试/重启边界复用原未改机制，不宣称新造全套真实事故 |
| K08 | 原global/local同步→native pre-message/cold hydrate；新增read branches | H04 warm off→on/coldon Prelude实际History/Notebook面；off/aux不进入新增业务写 | V16 H04-C/D；COLD；PENDING legacy-dormant/native tests | 符合：启用边界与原生关闭路径保持 | usage只观察Main，不改原会计/Prompt/工具权限 |
| K09 | native Mainend idle arm/start cancel→统一deadline→cold合法恢复 | H02 off到点消耗后on不补；H03 busy memoauto-on不提前；H04-F14新周期仅1event/child/snapshot且10s无重投 | V16 H02/H03/H04-F14 exact times；COLD/READ timer回归 | 符合：真实自然时钟与统一owner接线 | 旧H04失败保留；本轮profile现≥15sec与最终恢复策略由Main维护 |
| K10 | 原force/facade→CompressionCommitFence+只读cancel observer | 未新增Force计数/flag；generation cancel只控制parent compression，不撤已commit Noting；原special路径未被重写 | BE compression_read/compression facade delta；READ child/fence/queue tests；旧移交§4 | 符合：受影响压缩边界及原生优先保持 | 不重做旧全部force特殊触发模型实验 |
| K11 | 实际native dispatch事实→usage observer；cold model_config恢复 | 未创建provider路由/热度比较；原native/external标识派发点不被投影改写，fallback unknown诚实 | BE turn_api_call/usage_read/session_agent_context；USAGE native-fallback tests；旧移交 | 符合：D01派发事实与冻结边界保留 | 没有验证所有外部provider；不额外拒绝unknown |
| K12 | 原Noting freeze/spawn child→原生Loop/工具白名单；cold restore | H04-F14 Root hash warm/restored/child一致；真实Child非法terminal/tool_call被拒，finish合法；冷恢复仅复原已有prefix | COLD代码/定向；V16 H04-F14 proof；旧cache-parity机制证据§4 | 符合：本轮实际影响的prefix/child生命周期有对应证据 | 该live Child未留每次完整请求tools字节，不冒逐request直接证明；旧受控cache证据保留 |
| K13 | 原finish_noting/compact_parent→Commit Gate；新增cancel observer | read/cancel不将parent取消倒滚已提交Snapshot/Finish，force/overflow/≤5Turn旧机制未改 | READ child-final/fence；V16 H04-F14 completedChild/Snapshot；旧移交§4 | 符合：本轮取消/完成影响核查成立 | 未重开旧全部极限模型Turn实测 |
| K14 | 原request build→deferred batch→actual response→ACK | H06两个occurrence单User、H07工具跨due后当前Turn下一request注入、response后ACK，无重复 | V16 H06-H07-carrier-proof/ack-summary；MAIN repair-reminder-source-proof | 符合：本轮Loop接缝的真实deferred代表有效 | 未把未设schedule的secretary_task误判pending Reminder |
| K15 | 原Framework/instant carrier+native lifecycle→Web source投影 | H06 instant一次timestamp；H04 Finish同Snapshot；Framework不启动Turn；新观测不改原过期/持久机制 | V16 carrier/C15/H04-F14；BE native source observer；旧移交§4 | 符合：受影响来源/投影不改变载体owner | force区间完整旧机制按不变路径复用 |
| K16 | 原time formatter/entry marker→history及Notebook人类/AI→Web显示 | C15实际24History+2Notebook精度回转最大差0；只Web按C39无zone；不改原始content/entry次数 | V16 C15-actual-interface-time-proof；FE content时间规则 | 符合：源时间与展示时间职责分开 | 系统原时间字段/Duration不被UI重写 |
| K17 | 02§5.12 Target→原Root保存→cold恢复与实际human view | 本轮未改冻结System Prompt目标；H05真实Root指导完整且hash一致；cold不重建主历史root | V16 H05-actual-request-guidance-proof；COLD；git delta | 符合：本轮影响的Target注入/恢复边界保持 | 5次H05请求没有逐次完整payload，不能用latest Prelude冒充每次直接日志 |
| K18 | native propose-persistence→Main自行History→提案/修订→批准→memory→Noting archive | H05初始/提案/修订Memory hashes空；批准后真实memory success+USER.md；后有效candidate0 | V16 H05-summary/approved-memory-files/post-execution-noting/actual-guidance-proof | 符合：批准边界、真实写入及后续归档闭合 | 模型多余3次跨Conversation空搜保留为指导偏差，无引用/范围扩大；不改Prompt让结果变绿 |
| K19 | 原Active/History/Full identity→只读增量及native compaction/rewind | 新web不用Full API替代源，不造Foreground；cold保原messages/UID，历史carrier按真实lineage | COLD、READ、FE native-compaction；V16 H08；旧移交§4 | 符合：本轮三Foreground受影响身份/只读约束保留 | Full audit UI本轮D；非完整旧版重新验收 |

## 4. 核心目标及验证方法审查

独立目标已覆盖：薄客户端/原生复用，真实会话与Timeline，提交/Steer/Withdraw/Interrupt/Cancel/Rewind，Secretary只读与Compaction，Files与设计系统、原生兼容及继承Core。调查从正式入口贯穿到owner、持久化/投影、失败状态；必要反证优先覆盖未知接受、重连、队列竞态、压缩提交与取消、全局/局部关闭、跨会话与profile。有效同版本证据按路径复用，UI Mock或RPC ACK不能替代实际后端/模型结果。真实用户Validation属于下一独立门禁，四视口可用性不能用真机延期豁免。

测试底座核查：后端定向包通过canonical runner、隔离profile及真实SQLite/正式dispatcher/Agent Loop；外部provider返回和并发屏障受控，不绕过被测owner/commit/finalizer。前端Controller/React测试运行生产模块，fake IndexedDB与传输响应只替代外部依赖；不能证明真实浏览器undo、DOM吞吐或真实网络。真实DeepSeek/浏览器证据独立补充图像、文件、Noting/Reminder、断线/控制/只读与四视口，Mock只证明呈现。现有版本hash核查将旧分区报告和最终source observer/paging增量分开；已失败的reasoning测试和后续修复、既有review.summary catalog/SDK档案/旧Child fixture边界均保留，不改规则让其通过。

审查者没有重跑整套Python/前端，不新增大型检查。本轮不存在“统一保留检查全集/完整Python suite已通过”的证据。Main明确决定：已知待修版本不触发大型检查，待集中整改集成收敛后统一安排必要扩大范围一次；缺完整suite本身不使所有条款自动失败。现有证据只称分区定向、scoped ruff/health/config-writers与前端types/build。实际未闭合的必要证据是：四项原始缺陷修复后的正式入口/失败路径复验、assistant-ui实用接入及旧索引越界回归、真实草稿undo、真实事件→DOM/terminal吞吐、Turn边界侧栏无闪动。初始transport缺口现由当前两个端口的只读实际401/403补齐。

独立测试限制：三个Rewind反例直接运行生产selector/dispatcher/controller/projection，属于机制反证，不冒称本人操作浏览器复现；readonly transport只访问health/拒绝的HTTP/WS握手，未发业务RPC。首次Node缺ws包没有安装依赖；首次Python网络检查服务停止而Connection refused，没有取得拒绝证据。服务由Main恢复后，2026-10-13 14:59 UTC取得成功拒绝证据；/api/health显示24510d1 dirty（工作区文档推进），不读取或操作用户会话。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| V-R2-01（P1） | W03/W37；`tui_gateway/contracts/prompt_voice.py:172–188`、`methods_prompt.py:950–972`；前端 `src/api/attachments.ts` | `file.attach` 原参数新增 upload_id/offset/total_bytes/abort_upload/metadata_only，结果新增 upload_id/received_bytes/size_bytes；同名既有方法新增分片未完成及纯stat结果。06 §0.5/§2.1要求旧参数/shape保留、新原子能力新名；C30授权500MB预算及完整链路，未豁免API兼容要求 | 既有方法合同被扩展，违反明确机制；旧入参仍返回旧shape不足以关闭。现有分片真正被正式前端调用，并非未使用代码 | Main提出满足原契约的新接线方案；须保留旧方法准确合同，核新增方法manifest、前后端完整上传/取消/重试/metadata证据 | 违规；Main新名方案已评审，未实施，待复审 |
| V-R2-02（P1） | W27/W28；前端 `App.tsx:529`、`core/command-actions.ts:190–231`、`controller.ts:1898` | 活动Turn中点击旧User的Reply，`beginEdit`保留active；正式`primaryAction`仍选Steer，`perform`先调用owner.steer，尚未到达edit确认分支；已有busy Rewind底层代码未由该UI路径到达 | 已编辑旧消息会变成当前Turn纠正，既未确认也未rewind。production selector+dispatcher反例实际输出Steer、Controller.steer、确认0 | Main提案须让编辑事务在正式UI有正确确认/原生busy处理；至少覆盖active/idle、text/file、Enter/Button、取消及拒绝，不仅直接测controller.send | 违规；`.hermes-dev/round2-verification/rewind-active-proof.json` |
| V-R2-03（P2） | W27；前端 `App.tsx:442–466`、`core/projection.ts:572–596` | Chat截断history并隐藏live，但原样传所有temporary；目标之后Notebook锚点消失时projectTimelineNodes以anchor=-1在顶部插入。Pending尾同样未按编辑边界隐藏 | 未满足“目标及所有后续Timeline节点暂时隐藏”，Notebook移到更早位置，退出/确认前看到错误前景 | Main提案须按原真实顺序/临时边界隐藏后续全部节点，保留目标前临时节点，退出恢复且不写后端；确认后不能残留指向已截断历史的临时卡 | 违规；生产投影反例`rewind-proof.json`中编辑期间nodes=[notebook,earlier,answer1] |
| V-R2-04（P2） | W27/W17；前端 `controller.ts:1898–1917`；后端 `hermes_cli/web_routers/sessions.py:703–708` | 普通附件User的REST原生content包含--- Attached Context---，无display_content覆盖；beginEdit只删引用，未沿已有author-prefix projection剥离原生附件附录。对真实500MB验收row1调用生产beginEdit，原作者193字恢复成579字，并仍有Attached Context | 用户编辑框含非用户输入说明，再发送会把旧附录作为用户正文重复带入，与独立附件重复；当前测试仅无附录简单引用，未覆盖真实形状 | Main提案须还原用户可编辑正文并保真实附件occurrence；覆盖inline text/PDF、on-disk、图片placeholder、空display与重复名，保持原历史与模型content不改 | 违规；`rewind-attachment-proof.json`，生产Controller与保留真实行 |
| V-R2-05（P2） | W01；06 §1.1 L119；C71；FE `App.tsx:468,585` / TimelineMessages / Markdown | 实际assistant-ui只提供external runtime/Provider/ThreadRoot；Timeline直接自定义nodes.map、ReactMarkdown绘制，没有以成熟框架消息组件/订阅为交互组件基础。源码与Main事实交叉核对；不是因package安装即判接入 | 未达到既定框架复用要求；C71明确要求实用其消息渲染/订阅。当前浅接入与性能滞后同时存在，但尚不能据此断言因果 | Main/修复owner提出保视觉、Hermes事实owner和身份边界的接回方案；正式真实页面与旧索引越界反例、吞吐、工具/特殊消息/临时节点回归证据 | 确定结构事实及规格缺口，尚未整改；性能根因独立调查 |
| U-R2-01（待定位） | W15；C69 | 用户真实反馈Composer草稿Ctrl+Z不可用；生产textarea为controlled value/onChange，现有组件键位测试不涵盖真实浏览器原生undo栈 | 必要用户功能证据未闭合，不能拿React通过否认现场；未断言controlled本身就是根因 | 实际Composer输入/编辑/撤销/重做，确认只影响本草稿、不触发数据库Rewind；跨正常stream更新与focus场景；修复后正式浏览器取证 | 用户现场失败，审查未自行操作用户会话/穷尽根因 |
| U-R2-02（待定位） | W13；C70覆盖C69初步Stop表象；C71 | 用户观察模型已停止/完成后Timeline仍缓慢输出。Main只读日志显示22:42:48.821 hard Stop→.916 interrupted约95ms；最新row431 interrupted，22:44:14 row456为Noting Framework | 真实事件→DOM滞后尚无速度测量；撤回未证实“ESC/按钮后端Stop无效”。用户3次操作不能与2条日志强行一一映射；不能使用模型对自身行为的解释作事实 | 在隔离生产页面度量事件到达→状态发布→DOM提交及terminal最终可见时间，覆盖高频stream/tool/Stop，保全部内容/顺序；再按结果修复积压 | 现场反馈成立为待验收事项；是否显式限速、瓶颈位置未知；Main已派Sol只读调查 |
| U-R2-03（待定位） | W08；C72；FE controller.ts:435、App.tsx:709 | 用户观察Turn active/end侧边栏刷新闪动；正式refresh发布listLoading，Sidebar渲染Loading提示；当前代码/反馈不足以断言所有闪动均同一根因 | 常规列表机制通过不能覆盖用户现场呈现失败；需要保持已显示内容又更新真实事实 | 真实新建/标题/排序/Turn start/end/错误恢复的DOM证据，保旧列表连续呈现并消除加载切换闪动；不通过停刷新让数据陈旧 | 未自行复现、未替owner实现，待集中修复 |

范围外发现：未确认新的范围外产品缺陷。已知范围排除：06 division 5；真机键盘/相机/系统侧滑的专项实测按C05延期，但对应实现及四视口仍在范围内。

## 6. 修复与独立复审

这是本轮首次完整独立 Verification。初始判据不根据实施现状或既有自评调整。范围内违规或必要证据不足均阻断进入Validation。

- 2026-10-13 新增直接用户授权 R2-C66：用户有条件追认8个结束Turn和32条压缩终态记录窗口；手动刷新从真实历史/当前状态恢复，但不恢复旧操作结果。W46起点保留；有效判据更新为窗口数本身获认可，仍审当前操作保留、unknown诚实、不重发及手动刷新可恢复。
- 2026-10-13 新增直接用户授权 R2-C67：首次及Show More History均按后台消息记录200条（含工具），覆盖先前实现80/80。W13起点保留；在顺序/锚点/不丢重复要求外增加200/200核查。前端当前HEAD已变化为002f7a27fcf7313491f0301e143df7d3b6148088，待核对应差异和证据。
- V-R2-01初步发现已落§5：依据冻结明确API契约，等待Main作为提议方回应；审查者不代为实现设计。

- V-R2-01 Main承认无其他授权豁免；提案恢复旧file.attach准确合同，新增file.upload_chunk/file.upload_abort/file.attachment_info并复用现有helper/owner。Verification评审方向满足W03/W37，无须改判据；关闭要求旧额外键/错误语义对照、新stat只读/owner权限、offset重放/取消晚ACK、完成才发布ref、正式新RPC代表上传→submit→Agent读取。底层不变500MB证据可复用；仅提案未实施，等待全初审后集中整改。
- 解释精化（W19）：06 §1.7原文明定image.attach_bytes **or verified equivalent native Image Attachment**；起始简写不得误读为只能固定旧方法。C36直接批准原生上下文注入和本体留server。实际显式image_paths应审绑定/像素及原生校验，不因调用file.attach用于staging自动判违规；该方法合同变化独立由V-R2-01处理。
- 新独立反证仅运行生产TS模块loader，没有监听HTTP、连接后端或模型。首次Vite关闭时自动dep-scan报outdated警告，实际projection结果已取得；后两次禁自动发现，不改变产品且正常退出。全部产物限已确认ignored的round2-verification目录。

- 2026-10-13 初审期间新增直接用户口径C68–C72：允许真实服务供用户使用，初审后Sol整改、Main验收；Ctrl+Z现场失败；C70纠正Stop表象为Timeline滞后；C71强调assistant-ui真实组件/订阅复用；C72侧栏Turn边界闪动。原判据保留，分别在W15/W13/W01/W08追加当前证据/判定；不据实现状态缩减要求。未新增假想“必须某内部hook”的判据。
- 02–04 Main修复提案已评审方向可行：同一composer action selector显式edit优先；perform编辑分支先于Steer/Interrupt/slash，唯一红确认后复用busy interrupt→idle-only truncate；先完整timeline投影再按durable target裁切，并在真实提交接受点使切除区间临时节点及在途结果失效；恢复作者正文复用既有userAttachmentDisplayText/nativeAuthoredText。取消/失败应保原投影与草稿，Button/Enter共用正式动作。提案通过不是修复通过。
- 初审最终统计由§3逐行计算：56符合、6不符合（W01/W03/W20/W27/W28/W37）、3证据不足（W08/W13/W15），共65；0待调查占位。V-R2-01–05未关闭，U-R2-01–03未闭合。**本次Verification不通过；整改复审前不进入Validation。**审查者仅改本报告与ignored证据，没有产品修改、提交、模型请求、服务启动/停止或操作用户会话。
