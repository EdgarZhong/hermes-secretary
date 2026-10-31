# Hermes Secretary 当前状态

## 2026-10-31 · 证据集描述与Main强制回查（实施与上线中）

用户明确授权按已定稿规格／Prompt实施、验证后上线。隔离工作区`/Users/edgar/code/hermes-secretary-evidence-recovery`，分支`codex/evidence-recovery-20261031`，基于`c07b038d1c`（正式生产产品`ef9051f`已包含）。范围只含07顶部两项调优及配套接线、验证、部署；不混入其它重设计或原工作区dirty。旧证据组保留原文与UID，不自动补描述、重跑旧Noting或转换生产历史；本轮验证新建／修改组及旧组读取兼容。运行缓存沿已有调试接口在空闲时失效，下一次正常active构建新Prompt／工具；不改历史消息。实现→主会话亲审→独立Verification→独立Validation→空闲发布与终验，证据入口`.autonomous/20261031-evidence-recovery/`。数据／Prompt两个实现任务并行中。接口采用source_description与UID同传、provenance_descriptions逐槽对齐，旧组null只读兼容；根Main正常恢复接缝会采用新版指导／Schema并记录缓存变化，无需中途热改。用户追加所有本仓旧worktree的整合、清理及原目录回归main；先只读盘点独立改动、活动引用和证据保留，再执行收尾，不删除未保留内容。

## 2026-10-31 · Force 后 Main 完成交接故障（已完成并发布）

用户授权立即救援、随后自主修复、前后端重新部署、新APK和子Agent。00:42只重启空闲Web完成救援；本轮产品BE `ef9051f`／FE `6c132a4`已于01:24:38+08正式main发布verified，两实际服务同源active、微信connected。原故障尾部13441／13442完整保留；439静态及HTTP六资源、保护表／配置／绑定、两套三库已核。0.1.10／1010原签名APK已交Downloads，SHA4f3c795f…bb063，32127165字节，439内置资源严格一致。运维细节统一见operations-log。

前后端都有问题：Force FM后追加污染共享结果的尾部推断，使真实完成被拒；随后Pending未采用却误报读取成功，使Send仍锁。现在用原生final UID封闭Main回执，并让未采用Pending沿既有失败／重试收敛；完整Framework历史保留，不移动Force接缝、不放宽恢复或缓存权限。上次回归手造成功回执漏过真实Web收尾，本轮真入口反例改前失败、修后通过。

主会话已亲审，BE177项＋最终4／6、冻结十检查；FE273项、types／TS度量通过。独立Verification产品通过；独立Validation7适用场景通过、0失败，含真实隐藏IAB暖冷恢复、child活动时后继Send／Compact、断网期间child完成和Pending失败自动重试。最终发布及交付事实已独立补核，Verification12条全部符合／0缺口；本轮目标完成，最终简报已落盘。本轮索引／两报告／最终简报见`.autonomous/20261031-force-completion/`。原自主轮真机／外部验收边界独立保留，不冒称整个旧轮完成。两工作区原dirty及用户.DS_Store未动。

## 自主口径收敛 · 待用户追认

- **Agent自主收敛／待追认：中文粗体兼容的inline兄弟范围。** 原空白：既有中文标点邻接`**`兼容仅能处理单text节点；合法链接／inline code把同一显示范围切开后，末端无空格紧接中文的星号仍为字面。决定：同段／标题／表格格内，保原source双星／转义／CJK外侧与标点内侧证明，允许兼容span包含完整已解析link／inlineCode／inlineMath兄弟；内部payload／地址不变，不在其中寻找星号，不跨换行／block／模糊嵌套。理由：消除AST分割造成的兼容不一致。影响：扩展现有非标准CommonMark的中文粗体兼容，不冒称标准本来支持或原截图同型回归；源消息／Copy／安全协议保持。已实施于ccd4cfa并上线，111项及实际N30／Copy复验通过，待用户追认，可局部回退。

- **Agent自主收敛／待追认：混合压缩载体的读取。** 原空白：一个native UID可同时承载压缩摘要与真人消息，而用户要求辅助开关能读取Compression且Get Meta仍仅四字段。决定：默认保留原真人视图；显式辅助允许同UID的system摘要视图，Get Meta／Search按语义部分分别返回，anchored Read允许现有roles参数选部分，默认锚点优先原非压缩部分；同UID同role的system内容合并为一个视图；不造UID、不放开Full／隐藏内容。理由：使明确要求在native混合载体下可操作。影响：Read新增可选roles适用位置，同UID可有不同语义投影。已实现，201项History接受测试及56项原生路径通过；独立Verification／Validation已通过，已上线；不改变Message Identity或Notebook新证据准入。
- **Agent自主收敛／待追认：Candidate同Task来源形式切换。** 原空白：旧合法direct→refs操作与新旧Task节点不可删约束如何同时成立。决定：仅尚未提交且唯一节点属于本Task时，允许显式清空当前工作槽并切为合法refs；任何旧Task直接节点仍禁止删改。理由：继承原来源二选一操作并保持旧节点约束。影响：当前Task工作态边界，无迁移／旧节点特权。已实现，正式工具／恢复／原子失败98项通过；独立Verification／Validation已通过，已上线。

## 上一轮自主目标状态：外部验收证据阻塞（本次故障另立目标）

产品实施、两仓主干发布和0.1.9-5f APK交付均完成；最后本地验收／文档已提交ee6ca63并自动push。连续三个目标turn均确认同一外部边界，最新只读核工作区clean、报告SHA及15个partial保持，原QA确认无必须新增的最小本地路径。自主目标当前标记blocked，不是用户暂停，也不是整轮已完成；不继续空转本地验证或开启第四轮。

剩余R02／31／51–59／62需要真实Android WebView初始入口、触摸／IME与系统前后台；R18／60／61需要真实认证／合法登录恢复（R61亦含APK前置）。微信真实送达也无测试外发授权。现行显示保护只许root自建隐藏IAB，不能改用用户页面／桌面／外部浏览器来填证。恢复条件：取得这些真实外部结果，或用户明确提供相应设备／操作权限并要求继续；仅按原第三轮报告补已有缺口，不重跑有效套件，不把外部未验改为N/A。线上88ed／5f正常，APK保持可用。

## 2026-10-30 · 最后维护恢复修复收口

主会话已亲审三个产品文件及正式原生回归：手动压缩借用busy不再清除已结算输出快照；同一DB snapshot仅为显式旧row引用比较唯一当前代表的完整显示／终态事实，所有已结算回执与committed帧共用内部证明，活动Turn来源保持严格。156项受影响回归及冻结十检查通过；独立第三轮R3-V09与实际T11–15原失败document复验已关闭。88ed1ca于21:13:41+08从main正式发布并verified，两实际服务同源／微信connected；前端5f及原签名0.1.9 APK保持。439文件／HTTP6、保护数据／配置／绑定通过，两套三库保持。当前独立Validation50限定通过／15部分／0失败／1不适用；最后键盘、连续动画与历史预览回执均已补判，当前授权范围内无必须新增的本地路径；设备／真实认证边界保留，整轮未冒签关闭。


同第三轮U/O/C共60份唯一label原件及真实六库恢复已获原独立QA接收：Usage真零／模型切换、Slash候选／Tab／冷目录、Orb全局local开关／真实unknown／跨Profile、三Blob冷恢复、可见图片404／离屏0重下、首必要History503、冷Pending／双审批完整Diff均补齐对应浏览器范围。两套真实保留备份六库已隔离恢复并核14原生语义样本，临时副本已清。剩余主要是物理Android／真实登录恢复／未授权外发边界；不能用50项通过覆盖这些限制。混合文件＋图片的Attached Context／标签重复显示已证attachments/content与冻结前c39086c逐Gitblob相同，登记为既存观察，不冒称本轮回归或已修。

## 2026-10-27 · 增量同步与免刷新恢复（最终集成与第三轮收敛）

**T10维护恢复反例已关闭并上线。** 根因与88ed修复／156项回归／独立补审及T11–15实际同document复验见顶部；原T7–T10失败保留，当前不再处于待修或未上线状态。

**自主接续补验：** 上轮草稿修复／发布属实际进展。本次沿原第三轮R13／R16补准旧分页在owner切换后才完成的成功／失败与详情迟到；原V10未命中不改写。A经正式Rewind后仅10条，使用同夹具B的长历史作为慢请求owner、实际切回A，保持同一正式代码路径与精确Profile隔离；只改隔离准备数据及取证，不改产品／重新部署／扩大外发权限。沿原独立QA补判，不新开第四轮。

**OBS-READING-CAS-01已窄修并正式交付，原第三轮补收：** 原L6已展开Thinking405／row408、scroll7979.5；同UID／row／content不变的正式CAS仅更新reasoning后，L7详情自动取到新全文，但普通sessions.changed将idle阅读强制跳到320585。原QA已按06:356／538及P08确认普通在线失效不应夺取仍存活的阅读anchor；不能套用真实重连前缀破坏豁免。root限定同一DOM精确anchor匹配helper：普通提交有存活阅读候选则保持原owner／20秒计时；真正全候选退役、U25首冷启、真实重连及Send受理规则保持。FE5f974b3已完成root亲审、79项定向证据、独立机制审与实际Y0–Y7原旅程复验；普通CAS后旧Thinking全文更新且scroll7979.5保持，冷启按U25到底／完整详情复用、600条阅读与IDB500身份实证齐。正式5f静态及原签名APK均已交付；原反例和13db历史保留，两门禁最终补收不冒整轮完成。

**10月30日草稿补修已交付且定向独立关闭：** V33的Rewind受理后冷启复活旧Slash草稿已修于FE13db132；canonical成功写入才清退legacy，较新空草稿参与仲裁，失败回退映射可重试，受理消费推进事实时间。真实IDB／正式Controller基线17红、最终62项及类型／冻结健康通过，独立机制审接收；实际D1–10验证退出Reply、未提交编辑冷启、受理后暖／冷保持空、391秒无复活／无重放。已静态上线及交付原签名13db APK，独立QA与Verifier均已关闭R3-V07并核最终交付；原V33失败、D0环境失误和首次静态包拒绝全部保留，不开启第四轮。

**后继静态5f交付时点（后端其后已升级88ed，见顶部）：** 当时BE main00f0b28，FE5f974b3正式verified上线，439资源／HTTP六入口一致，双服务active／微信connected、0重启／DB写。Downloads新0.1.9 APK为5f974b3，32127841字节、SHA81a121d1537991534cd844d4060e29955b00d3121694a10702847069bdb28867，原严格签名／16KB／资源核验通过并已给用户链接。独立Verifier已接收5f正式CAS及交付证据并关闭R3-V08，报告SHA61936145…；QA继续原第三轮用户结果补判，未签整体完成。

**前版13db交付时点：** BE main `00f0b2879e0dede672cee0bb06989d9a032eb937`、FE `13db1320e672e613737f20900abb7450bff25858` 均已正式 verified 上线；最终原签名0.1.9 APK已交 Downloads 并给链接，SHA `051b0231964d7762a3bc89b7ed5544fc1751ccffea9d5bd365db07f8e7161081`、32127749字节。静态后继更新未重启服务／写库，两套完整三库仍保留。前三个动态缺陷和首次Socket失败恢复的有效证据保持；D组独立补判后为7项限定通过／58项部分通过／0项当前失败／1项不适用，整场均有执行记录不代表全部子分支已齐，尚未签整轮完成。外部动作／设备限制分记。下文旧版本与待验表述是各包原时点记录，当前实际状态以本段、唯一plan及operations顶部为准。

**中断partial补修已关闭并发布：** 独立动态N5／root P7证实原生中断partial直接append新UID，原stream作为terminal residual重复可见。root限定仅在明确保存当前partial的接缝绑定sameTurn／request／writer候选原身份，由原flush与terminal归账；不按同文去重、不改旧库／正文／权限。00f0b28实现、同轮独立影响审及Z段实际UI复验均已接收并上线。原Interrupt操作／Steer可见交接及Approval恢复已取得独立限定通过，原始失败保留。

**正式原生补证的新接线整改：** 完整工具callbacks证实final footer晚于首次持久化导致idle恢复证明不全，以及active恢复裁剪丢失typed工具owner依赖导致Diff不可重建；root分别限定首次final flush／running snapshot依赖闭包修复，不放宽receipt或权限。两项已亲审提交4be80c7并自动push；最终两原生ASGI场景2项通过、冻结十检查及health 0／0通过，同次第三轮影响审与实际复验继续，详plan当前表。原legacy夹具缺事实与这两处真实产品反例明确分开。

**历史验收整改（已由后继Z/T实际路径关闭）：VAL-R25-01。** 独立动态验收发现Interrupt跨Turn复用上一Turn operation导致unknown；原73a真实失败已保，FE ce69fbe已按严格同Turn身份窄修提交／自动push，11项及types／冻结度量通过，同次第三轮源码影响补审认可；待正式原生旅程复验再更新前端／APK。15:35:43已上线BE d172／FE73及原签名APK交付事实保持，不声称整体完成。

**当前完成条件（U22／U23）：** 持续自主执行；第一轮之后Verification与Validation各最多再两次正式全轮复审／复验，第三轮内完成两仓main集成、正式Alex上线和原签名0.1.9 APK交付。次数上限不豁免缺陷或证据缺口，不开第四轮。用户U24已明确将Verification改回本地，第二轮集成锁定后派全新上下文6.1 sol/high全范围独立审查；开发定向测试／主会话亲审不冒充独立门禁。生产模型和真实微信测试外发不在授权内。

**U31历史安排（已被U32覆盖）：** 紧急发布在切换前因计划文件上传／读取路径不一致退出，正式Alex仍main3426c0f、两服务active，没有停服／换源／换静态／生产库写入。用户随后明确“不着急了…先不用…临时的东西…赶紧继续，尽快收敛”，停止临时发布，回到最终集成→第三轮Verification→正式Validation→统一上线；现有APK先继续使用，不主动要求更新。最终上线授权及三轮上限保留。

**U32实际完成：** 用户15:21:32+08明确20分钟内上线并给新APK；正式Alex于15:35:43 verified（截止15:41:32），BE main d172250／FE73a，Web／Gateway实际版本均已核、active且微信connected。原签名0.1.9新包已交Downloads并给链接。第三轮168条产品Verification与交付事实已接收，R3-V01正式链及唯一真实Main消费关闭；独立66场景Validation继续，未将上线／签名包当作动态验收或真机通过。发布／备份／协议证据详operations-log。

唯一计划／索引在[本轮目录](.autonomous/20261027-incremental-sync/plan.md)。原始需求U01–U30、缓存D01–D18、表现S01–S20和操作P01–P11已落档。保持原产品／视觉／操作资格，主目标仍是500条消息与完整已取详情缓存、游标同步、SPA／APK无需刷新恢复，不为填缓存预读或重新发起写操作。

| 工作包 | 当前实际状态／交接 |
|---|---|
| 原独立修复及主体增量机制 | 已提交／push、合入主干并随d172／73a正式上线；独立产品Verification通过，动态验收继续 |
| U18 Steer／U19 Approval／冷Slash目录竞态 | 已集成并随当前5f上线；原真实交接／审批及冷目录代表已补收，本批原生候选Tab、unsupported拒绝、冷Pending唯一恢复／撤回、冷双审批完整Diff与明确Deny推进已获原QA接收 |
| F03/F04缓存 | 前端0ea002e已亲审提交：完整详情字段保留，窗口／详情／已核验前缀合计500身份预算，证明失效时仅退役selector；95项及真实IDB证据，见reports/r2-cache.md |
| F05/F06后端增量 | 918efda主体已亲审、集成并上线：原生Thinking合法尾追加、正式CAS改文通知；132项及22项原证据，正式App单条delta/CAS阅读保持与500身份缓存已有原件 |
| F01/F02前端恢复 | 已整包交回并亲审，166项＋末次14项通过；复杂度窄拆分完成且无增长，前端8313cf2已提交；见reports/r2-frontend-recovery.md |
| F08微信逐消息发送 | 已亲审提交后端a5018ff；final持久UID后立即沿既有FIFO投递、尾部成功回执去重；150项及最后47项影响复测，不真实外发；见reports/r2-weixin.md |
| U20／F07／E02联合Noting | 已随主干上线，当前BE88ed；普通手动／Idle／原生auto联合触发取消、已提交保留，Force仅Turn结束不可取消并封区间，特殊替代审计透明，Note独立四时点原FM投递。独立V及R34–40正式机制／真实消费代表已补收，不能冒全部真机／模型组合 |
| E01/E03与动态体验 | D07勘误已由独立Verifier接收，仅约束已有入口Desktop，Web/APK不新增索引UI；当前App流量／切点／阅读／缓存与菜单恢复的实际代表已补，独立Validation剩余边界按原报告 |
| 整轮门禁 | 第二轮不通过历史保留；第三轮168条产品及已授权发布交付Verification通过，R2-V01与R3-V01独立关闭。66场景Validation由独立验收者判断、root隐藏IAB远程手执行中；夹具页面关闭后预置owner回收导致环境失效，原失败保留、仅修ignored接线后复验 |
| U25冷启动视口 | 用户已确认新document首次真实历史提交后一次立刻到底，加载期用户滚动不阻止；cold_start_viewport已交回，root审查正式commit/ack接线后接收并提交ba7decd；5文件115项、types与冻结健康通过，同页规则保持 |
| Main notebook_show线上反馈 | 用户转述Main自述无工具且只限Noting，既定只读Main资格不变；只读核线上3426持久工具表有Show且同会话23:42实际调用成功；争议请求wire缺失，缺工具未确证。新候选17项正式Main工具接线通过；用户明确停止深挖旧逻辑，继续以新链路实际注入／读取为准，未改Prompt或扩大旧版追查 |
| Noting误恢复补修 | 独立Secretary token／child history token／scope事件消费已随主干上线，并经原生21／26／9／18及FE12原证据核实；本批实际A后台任务而B idle、切A running、失败回idle均无Main恢复；88ed再关闭维护误清快照／物理换代拒绝 |
| U30 Markdown链接误识别 | 已集成当前5f并上线／打包；裸链接中文边界、合法Unicode、代码／数学及原消息复制、协议安全由M1–M12实际流／冷恢复与独立QA R63–66补收，无外链访问／真实授权码保存 |
| K04内容取证／R3-V01 | 一次真实Noting12HTTP正常提交与Main Show成功；保留错误reason原件。d172正式FM消费指导经6项真实链与唯一Main请求证据独立关闭，四极性忠实、0工具／新Noting，不改Task／Schema；源／raw前后已核 |
| U29真机视觉反馈 | 用户已确认起手正常，但要求圈旋转放慢、阈值补明显高光／光晕；FE6628a2e已提交：旋转540→240度、等待700→1300ms、阈值主题高光／光晕；32项与types通过，root隐藏IAB浅深主题／回拖已核，不改已正常手势时序／行程／区域，新视觉真机反馈待 |
| U28真机触摸起手失败 | 用户e545实测标题栏完全无圆盘；root确认子lost capture冒泡误cancel，FE d1a53cf已亲审提交，31项及正式wrapper/StrictMode/types/健康通过。已交付`/Users/edgar/Downloads/Hermes-Secretary-0.1.9-preview-d1a53cf-arm64.apk`：32123717字节、SHAfb651a0bbeae025776016d58fa594b68aa2f0fb16faeaf88aa6b3983ef564a2d，439资源/原签名/ZIP/16KB/1009已核；用户随后明确反馈“之前你给我的第2次APK已经可以正常下拉刷新了”，d1a53cf预览实际顶栏起手故障已获真机关闭；其余场景不据此代签 |
| U26顶栏手动刷新预览 | APK only Chrome式圆盘阻尼／cap／阈值释放已集成当前5f APK，普通Web关闭；页面背景静止，真实mouse和原native边界证据保持，d1起手获用户真机关闭，其余当前真机动作／视觉不扩大签通过 |
| C-R5／C-R6 显式恢复Note资格 | Snapshot来源／operation证明、branch去父关联、恢复lease接手及终态补检查已集成上线；7文件源SHA、62项及十检查由root亲审并与原第三轮正式机制补收，不再标待集成 |
| U27 APK引导失败同页恢复 | e545接线已集成当前5f APK：初始临时引导失败承接内置SPA，原生自动reload取消；native13／TS35原证据及实际pending503／首次WS失败／慢凭据／首必要History503同doc恢复分层保持；真实APK首次进程到SPA现场仍未验 |
| 发布／APK | 后端88ed1ca／前端5f已正式verified；439资源／HTTP6、保护数据／配置／绑定通过，两套三库保持。原签名0.1.9-5f APK已交Downloads／链接；最后维护恢复缺陷独立审查和实际同doc复验关闭，整体验收边界保留 |

前后端实施目录分别为`/Users/edgar/code/hermes-secretary-incremental-sync`与`/Users/edgar/code/hermes-secretary-web`，同名`codex/incremental-sync-20261027`分支。C、原恢复包及U25/U26均已亲审提交；两仓main历史已按SOP纳入候选（BE2dc4398／FEbc02d01），合并产品tree零增量，不触碰其它main工作区dirty。validation_round2已补完并过目56场景，release_preflight及27项本地发布保护演练已完成。隐藏IAB已恢复；root开发联调确认正式CAS改文→watcher→App同document自动delta更新1条，草稿保留，不把该开发证据冒称独立验收通过。子Agent6.1 sol/high、不再派生、不流水账；主会话负责方案、亲审、接线、正式门禁与发布。

保护原main工作区的Noting调试／生成协议／07／presentation等他人dirty。新状态表必须兼容正式旧库，仅加Secretary自有伴随表／读取视图，不重建生产数据库。冻结检查不增删放宽；no-tmp旧报告七处仅加既有允许的历史取证说明，原行原结论保留，原字节与SHA已在ignored存档；单项扫描通过，未改检查规则／阈值／baseline；de45版本已统一执行冻结十项且70文件health 0／0，后继整改须按影响补查。旧Timeline七项失败在原91ad同样存在，不能据此替代部署基线或当前用户体验判断。Android完整生命周期与真实微信送达未完整实测；用户已确认d1顶栏起手正常，不能扩大为新视觉及全部生命周期通过；包校验／受控adapter不冒称实机或真实外发。

U20详口径见07顶部及plan接线设计；旧“先Noting再压缩／FM结算后才终态”已被替换。U17旧模糊片段保持懒取，新Turn沿原生source精确主动取Thinking，不设逐Thinking游标。用户确认与原始云端报告保留索引，不改写旧审查时点结论。界面验收只许自建隐藏IAB，不动用户浏览器／桌面。

## 2026-10-27 · Noting来源链／History调优（已上线）

用户已确认全部语义和精简Prompt，并明确“开始改吧。改完，测好，上线”。轮次`.autonomous/20261027-noting-provenance-history/`，工作区`/Users/edgar/code/hermes-secretary-noting-chain`，分支`codex/noting-provenance-history-20261027`，基于main `d1de4db49b`；为隔离旧目录及main调试dirty新建，原修改保持。

范围：Get Meta、统一语义role／默认辅助消息排除、闭区间、工具参数及结果展示；每条目每Task一个不可改旧节点的来源链、runtime只读对应Evidence time；已审Noting／History Prompt。独立History／Notebook／Prompt实现包，主会话亲审集成、真实模型证据、独立Verification→Validation通过后已统一部署。仅人工转换Alex仍用的唯一置顶Conversation的Notebook，保留消息、排期、绑定、其它Profile／Conversation和前端；不建通用迁移层。正式机`ssh alex`，上线沿既有SOP／发布工具，备份最多两套三库。

冻结02d55fdb，产品3426c0f已合入origin/main并在正式Alex保持main上线；两服务实际版本、只读RPC、目标Notebook与保护数据／配置／绑定／静态均已验真。独立Verification38判据通过（37符合、1本地生产不适用）；Validation17适用场景及独立10旅程通过；40文件1094项、保真修复107项、最终Linux132项及十检查通过。旧29项／8文件和Prelude15项冻结基线失败保留，不称分区全绿。真实k3.1-pro/high两Task6请求代表样本通过，8个后继源码差异分支由当前正式机制补证。

唯一目标转换完成：51历史item、8Snapshot／pointer不变，31独立条目×Task节点在版本内累计55次，180UID引用／81不同UID，162可见投影；生产重开只读验证通过。两套完整三库已逐库核SHA／integrity／FK，研究副本两文件清退；运行库及同步包不动。具体发布／恢复事实只记operations-log；[最终交付](.autonomous/20261027-noting-provenance-history/final-delivery.md)含范围、独立报告、工程细化与限制。本轮无未完成项／新阻塞；原main和旧目录他人dirty未纳入，未做UI／APK或生产模型测试。

## 2026-10-26 · Scheduler二级切换卡顿与0.1.8重建

用户明确卡顿发生在一级面板点击Tag切换Scheduler二级，不是打开球；要求修复、重建0.1.8暂不交付。前端0947ed5已提交／自动push：移除层级及异步尺寸更新触发整板隐藏360ms的玻璃动画，层级改为立即可见可操作的140ms轻量位移；球展开／关闭动画保持，数据到达不重启导航过渡，按需读取与恢复owner不变。旧APK及SHA已移出Mac和云端Alex工作同步区，Downloads原副本及云端同步区外副本保留。

验证：改前Tag导航透明／不可点击反例失败，修后通过；4文件112项、typecheck及冻结TypeScript度量通过。隐藏IAB390×844真实App受控排期延迟3秒，仅1次读取，切换约30ms可见；648采样帧里透明／不可点击／ghost均0。5秒未决请求期间可返回一级，迟到结果不重开；原球展开／关闭回归通过。无Android真机，不把IAB性能当作真机验收。

新0.1.8／1008已重建：本地ignored `.archive/qa018/apk-staging/Hermes-Secretary-0.1.8-0947ed5-arm64.apk`，32,106,601字节，SHA256 `1ffb96ff4476fdb261d01c8d1170f61c02e3eeacb17cd4ffde82085758f7b463`，原证书、v2签名／ZIP CRC／16KB对齐及439前端资源通过；仅本地暂存，未发送或复制至用户同步区。网页已沿先前授权只更新静态0947ed5，439文件和HTTP资源核验通过；后端6ef9459及Web／Gateway PID保持、微信connected。

## 前轮完成情况（2026-10-26）

**2026-10-26最新授权：用户已允许前后端上线，SSH `alex`为正式首尔43.128.131.30／ubuntu；由主会话独立接完迁移会话未完成的飞书notifier MCP（Alex、study均启用），发布本轮代码并恢复Hermes云端正常运行。同步修订全局服务器规则、补齐运维记录；第一台实验用首尔机废弃、准备回收，不再作为生产源。原迁移期间禁止上线约束已被本次授权替代。**

已按用户指定顺序完成统一恢复修复与b33e428阶段APK核验，再完成Noting按需优化。悬浮球仅由当前Profile全局开关决定，与连接状态解耦；未展开排期不取详情，概览用轻量计数，同owner突发失效合并为一个在途请求加一次最新读取，未生效的旧读不消费完成通知。不新增持久缓存。后端查询排除结束严格超过24小时的排期，仅返回hidden_count；删除不返回／不计数，暂停保留，原生模型工具完整列表不变。用户新增胶囊压高已落实：Usage／Context从32降至26px，字体／胶囊圆角不变，底栏36降至30px。最终0.1.8／20c9267已构建并完成交付副本完整性核验，已随本轮在正式Alex上线。用户明确追加修复Compaction message末尾的Conversation start：只取该Conversation的History Foreground第一条timestamp，禁止用内存最早时间或本次压缩区间代替，禁止另猜起点。已删除_summarize_window的内存min(timestamp)，Compaction footer直接读取get_history_foreground(current_session)[0].timestamp；真实数据库反例改前3失败、改后3通过，7文件201项相关测试与10项冻结检查通过。已上线；不改写生产历史／旧摘要。

统一恢复状态本地实现完成：PageRecovery复用原有owner、轮次、读取结果与提交点，派生当前可见依赖的availability；Composer单行提示、主按钮恢复资格及Android恢复／导航回执同源。只有Connecting to Hermes…、Restoring {对象}…、Retrying {对象}…三模板，固定20px单行、随Composer宽度、省略号、多个真实等待对象3秒轮换。移除聊天页其它自动恢复横幅／Toast；草稿保留可编辑，真实写操作及未确认回执反馈保留。已恢复同owner的普通后台刷新不重新锁定操作；隐藏预取不进入完整恢复资格。REST读取增加30秒可取消超时，失败交给既有owner自动重试。

已定位的静默恢复缺陷：Socket connected、Profiles读取成功与页面完整恢复原来各自决定提示，Secretary又错误等待历史／流恢复，导致提示消失但球未出现。现Secretary独立按当前stored owner读取，读失败与secretary.changed刷新均沿恢复owner重试。另一个后端根因：原生压缩后的完成回执来源仍visible，但active=0；恢复层误拒并返回runtime_unavailable。只放行exact UID／row／role且visible并active或compacted的已完成来源，rewind／删除／不匹配仍拒绝。此前只读取证与本地原生链路反例均可复现，不归因于网络。

通用规则见[AGENTS](AGENTS.md)，稳定入口见[README](README.md)，逐次部署／故障历史见[运维记录](docs/operations-log.md)。历史CLAUDE可由f812c1d等已提交时点读取，不把旧阶段的“当前／正在”继续作为任务编排。

本轮发布及迁移收尾已完成：Alex、study飞书MCP握手均仅notify，未发通知；Hermes恢复正常运行。旧实验首尔机废弃、待回收，未销毁实例。全局服务器规则已精简。具体版本、验证、备份与限制统一见[运维记录顶部](docs/operations-log.md)。20c9267旧APK原已交付并核SHA，用户本轮要求后已移出两端Alex工作同步区，新构建暂不交付。

## 当前交付与运行版本

| 项目 | 已核结果 |
|---|---|
| 本轮本地代码 | 后端88ed1ca与前端5f974b3已合正式远端主干并上线；第三轮Verification无违规／不足，Validation50限定通过／15部分／0失败／1不适用；本地最小路径已齐，设备／真实认证边界仍未全闭 |
| 后端线上最后核验版本 | 88ed1ca7e34c2be5dbcdbc9b30b55ca6ed5407fe；21:13:41+08正式Alex检出main，两实际服务同源、active／running，微信connected，数据／配置／绑定保护已核 |
| 前端线上最后核验版本 | 5f974b3bd70a67180039067df1e3b0356532e3cc；439静态及HTTP六资源逐SHA保持 |
| 已交付APK | 最新0.1.9／1009：Downloads/Hermes-Secretary-0.1.9-5f974b3-arm64.apk，32127841字节，SHA81a121d1537991534cd844d4060e29955b00d3121694a10702847069bdb28867；原证书／439资源／v2／ZIP／16KB／交付副本通过；不冒真机全生命周期已验 |
| 运行设置 | 历史noting off不代表当前值；最后已核local_enabled=true，默认／Alex压缩总时限1000秒及Idle500秒／96K保持。本轮只追加授权飞书MCP配置／官方PM mcp依赖，不改模型或调用生产模型 |
| 保留他人工作 | presentation报告、手动Noting调试入口／协议生成、07等原dirty保持，不纳入本轮恢复补丁提交 |

## 前轮交付事实索引（本轮唯一任务看板见顶部）

| 工作 | 状态与完成边界 |
|---|---|
| Noting来源链／History Get Meta | 3426c0f已合入main并上线；双独立门禁通过，唯一目标转换及RPC／保护数据终验通过，详本轮交付报告 |
| Composer统一恢复契约 | 本地实现与正式App链路已验，已提交／自动push前端b33e428，等价抽取217项及复杂度检查通过；已部署正式Alex |
| 压缩后完成回执恢复误拒 | 本地正式入口及原生链路105项通过；补充中断／失败压缩路径7项通过，10项冻结检查通过；已提交／自动push后端98a707e，已部署正式Alex |
| 0.1.8重新构建 | 20c9267最终APK已构建并核验，唯一新文件名与SHA／verification sidecar已生成；无真机不声称安装验证 |
| Noting弱网按需读取／显示解耦 | 已提交／自动push前端20c9267、后端4b04546；本地实现及主会话隐藏IAB已验：未展开0次、展开1次、关闭／重连无额外列表读；底部隐藏摘要、全局开关控制球、断线球保留；不新增持久缓存 |
| Compaction末尾Conversation start | 已按用户再次明确的Foreground第一条修复，真实DB连续三轮原地压缩／Session轮转／冷恢复稳定；非单调时间与foreign owner反例覆盖。7文件201项及10项冻结检查通过，已提交／自动push后端453401d，已部署正式Alex |
| 重连阅读／流式漏显 | 388839c已交付：idle前缀兼容保视口；active或已证前缀失配才回底；连续连接手动20秒规则独立。旧恢复冻结挡住已到达消息的机制、首次NewChat／冷active慢Pending路径已补齐。本轮回归继续验证 |
| Composer满高闪动 | 小数scrollTop钳制导致的无效重复scrollTo已修：原90次含30次无位移，修后105次均有实际位移。未修改键盘／布局；Android Chrome真机绘制尚未验，不把桌面窄窗口等同问题全部关闭 |
| 既有工具展开状态 | construction→UID admission展开保持测试在未修改388839c隔离副本同样失败，已留证；本轮不改断言掩盖，不与流式可见修复混为一谈 |
| 已有成果 | 冷刷新正文缓存／暖态阅读保持、Thinking身份修复、Context终态单次高亮、Stop后持久终态恢复、Compact部分摘要提交均沿既有已发布成果保持；历史逐项证据见operations |
| 手动Noting调试入口 | 别的工作已有本地dirty，尚未发布／调用；本轮不混入或额外触发Noting |

## 验证摘要与边界

- Compaction start修复：真实DB反例改前3项失败，旧代码将Conversation的9月21日起点写成内存后段9月22日。改后3文件96项及4文件105项通过，合计7文件201项；原地压缩／Session轮转各连续三轮，重开DB／重建compressor，末尾始终等于同Conversation History Foreground第一条timestamp。另测后续行时间更早、外部Conversation更早、旧RAM字段与确定性摘要路径，均不改变权威起点。10项冻结检查通过，证据见ignored `frontend-018-20261026/conversation-start/`。

- Noting／排期／紧凑胶囊收尾：前端22文件504项通过、6项跳过（5项已证旧失败＋1项可选原生wire夹具未配置）；typecheck及冻结TS复杂度检查通过。后台5文件73项通过（24h前／整点／之后、删除不计数、暂停保留、foreign owner隔离、SQL先过滤再投影、只读不改库、原生Scheduler语义），10项冻结检查通过。仅暂存本轮生成协议增量的隔离快照亦通过字节级重新生成检查。
- 扩大检查发现controller.test的4项旧失败，与此前工具展开1项一并保留；均在改前隔离快照复现。后端whole-wire目录检查的review.summary孤立契约同样在改前98a707e复现，未改断言或纳入本轮修复。测试中旧方法级夹具不启动PageRecovery，已隔离其刷新副作用；正式恢复owner／完成回执合并由完整native DTO测试覆盖。
- 390×844隐藏IAB实际App：胶囊各26px、上下padding2px、圆角999px、字体12px、底栏30px。关闭Noting详情不取排期，概览仍显示轻量计数；展开仅一次读取并显示4条隐藏摘要；关闭再失效／重连仍只有1次。断线球仍显示，Composer单行Connecting；恢复提示消失，球回到idle。

- 前端最终相关21文件483项通过、1项明确排除的已复现基线失败；typecheck通过。初次467项中465通过，旧Usage横幅断言按新合同更新；另补Android导航等待本地状态恢复测试，141项定向通过。等价复杂度抽取后217项通过，18个变更TS文件按主仓冻结度量／阈值检查无新增问题；Controller保持2550行。
- 后端正式恢复与原生结算2文件105项通过（46.2秒），包含改前失败的compacted回执、实际archive_and_compact和有／无Steer路径；随后新增中断／失败再压缩两条反例与夹具等价调整，7项定向通过；10项冻结检查通过，初次测试分支HX011已按表驱动修正，不改规则。不扩大为全仓通过。
- 主会话自己的隐藏IAB，390×844隔离真实App／Controller：实际Send后历史／Pending仍等待即可见User、Thinking、工具和流式正文；历史完成只剩Restoring live updates…；Pending返回后提示消失、球存在且Stop可用。失败Noting后台刷新只显示一条Retrying且不锁操作；断线与重连尚未恢复时同位置提示且主按钮等待；全部恢复后提示消失、草稿保留、Steer可用、零Toast。真实业务请求全部受控替身，无生产模型／用户页面操作。
- 0.1.7本地原件和副本核验通过，用户手机损坏根因未证实；后继APK产物核验不等同真机安装／生命周期通过。

## 保留事项（不自动立项）

| 事项 | 当前边界 |
|---|---|
| 跨进程busy Instant Reminder | desktop来源且Gateway持Main租约时，Instant可能另起Web运行而非转Deferred；10/24已确认，本轮未修。Deferred已验正常，未发现原文误外发 |
| 微信主动出站`prepare failed` | 既有失败与脚本exit 0误判风险仍独立保留；本轮connected不等于主动出站恢复，未试发 |
| 微信早期正文投递时序 | 18:18长正文已定位为刚生成即发送且拆成两段；更早正文是否积压尚缺逐消息发送身份回执，不将现有记录推断成已修 |
| Conversation时间／分页 | Compaction末尾Conversation start已本地修复并列入看板。旧第10项pagination反馈及47条历史时间副本仍未关闭；没有生产恢复写入授权 |
| 旧失败Noting内容重建 | 空工作态历史反例在原HEAD2122223复现；本轮只验证恢复入口生命周期，不冒称其内容重建已修 |

已关闭的拍照参数、首触Send、会话列表、补水流量及旧Kimi专项不重新挂账；Reminder语气、编排分流与触达白名单归模型行为调优，不变成开发任务。SOUL／workspace AGENTS不因文档整理改写。

## 证据入口

- 本轮恢复：ignored `.hermes-dev/frontend-018-20261026/`，前端ignored `.archive/qa018/status-evidence/`；最终日志会随收尾复制到同目录。
- 原388839c部署／APK：`release-388839c/apply.log`、`final-388839c.json`及Downloads交付旁SHA／verification收据；旧JSON的awaiting发布语句属于构建当时，实际上线结果以apply.log为准。
- 历史冻结／验收：[README索引](README.md#重要文档索引)及[运维记录](docs/operations-log.md)，不改写原报告时点。
