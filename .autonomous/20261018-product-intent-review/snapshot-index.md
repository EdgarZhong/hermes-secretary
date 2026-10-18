# Snapshot Index：20261018-product-intent-review

## 授权与本轮目的

用户2026-10-18明确要求：“遵循自主实现，派遣一个astra high独立进行verifycation，找出所有这种不符合我预期的问题，但告诉verify者，规格也不一定是权威，也可能有错，以最新产品文档为准。修复后重新拟定测试计划，把场景和功能覆盖到”。后续明确：“对，继续自主实现直到交付，除了verify者其它任务不再使用astra模型”。

审查者Astra/high、全新无主会话上下文；其余实现/调查/实测GPT-6.1/high。主会话抓产品意图、覆盖、集成和最终判断。中途默认不发碎片消息，整包交回；只在真正阻塞或须主会话决策时主动联系。子Agent不派生。

## 要求权威顺序（用户本次明确覆盖旧技术规格冻结顺序）

1. 本聊天用户最新明确产品口径（下表），以及最新产品文档。
2. 最新产品文档的冻结副本：`/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/inputs/product-intent.md`。原始来源/内容SHA见同目录manifest.json。原文为《Hermes Secretary 场景、个人需求、长期愿景与产品设计原则》，2026-10-18。先全文独立恢复当前能力、使用目标、未来范围及上线前/长期观察的区别。
3. 主助手身份参考同目录identity-reference.SYSTEM.md；只作为身份/表达风格依据，不继承旧Pi专用工具、默认写权限、飞书时间或调度职责。两份同目录SOUL为用户要求的部署身份文案，可与产品意图对照审查，不是凌驾于产品文档的独立权威。
4. 白板及07、06、08和所保留旧规格是工程设计/实现契约的证据，**规格本身也可能出错**。与最新产品意图冲突时单列“规格偏离/冲突”，不能因代码符合旧规格判通过。不能反向由实现或历史测试创造用户要求。明确未来范围不扩成今天的开发清单。

## 用户最新明确口径（判据阶段可读，不含实现解释或预期结论）

| 编号 | 用户原意/明确要求 |
|---|---|
| PI-01 | 本轮实测建两个本机Profile：长期主助手与考研助手；接真实NM并安装插件。实测操作中主助手Default只读，考研使用“考研复习”Space按授权操作；两者Noting开启。主助手通过NM读取考研Space，不读另一个Hermes Profile。此为实测访问授权，不自动授予正式部署写权限，也不自动定义永久人格；SOUL是否混入测试专属设定须按PI-03审查。 |
| PI-02 | 真实功能实测，不演复习角色戏。DeepSeek仅本轮代理模型，拟正式用更强K3；不全信模型自述/建议，以实际工具与持久结果为证。 |
| PI-03 | 测试中现实10分钟代表一天，每条普通user message前置用户给定测试角色/时间尺度/禁止调查Harness代码的说明；不改系统时钟。SOUL必须能直接部署，不包含测试背景或10分钟尺度。 |
| PI-04 | 两Profile联合Idle Compact + Noting开启，阈值100000 tokens、空闲几秒（当前选5秒）；调整触发阈值，模型容量保持原生配置。 |
| PI-05 | Notebook结果不要给Hermes AI展示内部Snapshot ID、Coverage anchor审计标识；对象可读性遵守用户的Prompt原则。此要求不是只隐藏人类UI。 |
| PI-06 | Profile选择仅放首页独立下拉，不混入model selector；选择改变新Session原生环境，model/SOUL等随Profile；已有Conversation原归属保持。首页切Profile不允许只显示当前Profile会话；侧栏跨Profile展示，图标由每条Conversation所属Profile决定，前端维护固定映射，不新增配置。 |
| PI-07 | 用户重视首个Thinking在流式期间可见、工具卡无瞬间错误闪烁、完成高亮准确、普通提示统一5秒、错误需手动关闭；冷启动允许沿上次可信统计值估算Context/Session Total。 |
| PI-08 | 本轮真实Memory写入仍需明确批准具体内容/目标；提案/只修改措辞/沉默不授权写；先结算真正成功交付覆盖的来源，后关闭Candidate，保留未覆盖责任/纠正/其它依赖。 |
| PI-09 | 用户框架内写死Prompt原则上未经授权不擅改；本次明确纠偏对应的模型内部标识清理已授权。审查独立判断其余缺口与最小修复必要性，不自行改产品Prompt/代码。 |
| PI-10 | 尊重原生Profile/会话/模型/provider机制，关闭Secretary时原生行为保持；API新增兼容，用户数据归属和权限边界不擅改。主会话并行统筹、避免重复测试/流水账，尽快收敛交付。 |
| PI-11 | 用户本机其他桌面录屏，禁止CU/CUA/原生桌面/Chrome/Edge/切桌面抢焦点；所有界面验收只在Codex内置浏览器进行。没有非CU内置接口则明确界面未验，不能以外部浏览器代验。另明确禁止任何方式改变屏幕显示状态，包括open/open_in_codex、打开/导航可见页面、窗口激活/切换/最小化/关闭；只准保证不改显示的后台接口。此为执行约束，不改变产品功能判据。 |


| PI-12 | 用户后续明确允许仅CUA下隐藏Codex内置浏览器（iab、visible:false），仍禁止任何可见页面/桌面/窗口/焦点改变及外部浏览器；此为PI-11的唯一例外，不放宽产品判据。 |
| PI-13 | 用户看过S01/Q02精确中英文前后对照后明确答“两处均按提案实施”：默认未来24h内至少一条Instant、检查已有承诺不造任务且无可汇报内容静默；答疑/建议/交流直接回应，适合Agent的执行事务委派并审核，用户要求亲自处理优先。仅这两处及明确获准History同源分页配套文字同步，不是无限Prompt调优授权。 |
| PI-14 | 用户明确允许仅窄Memory创建helper改用一次正式API创建并携Metadata，复用同一连接；其余NM操作仍官方CLI。真实写入具体内容/目标审批和原生权限不变，不重建旧partial对象凑成功。 |
| PI-15 | 用户明确Candidate来源为Notebook条目引用或Message Identity引用，二选一禁止混用；Notebook refs型不得重写条目正文，按Candidate的Memory、Rule或Skill身份作特化简述。先实际覆盖来源结算、后关闭Candidate及保留未交付部分沿PI-08。 |
| PI-16 | 用户要求按实际部署形态测试：本地开反代，浏览器访问反代端口检查URL路径；Cloudflare Access不验。部署为06§0.7独立Secretary Web与原生Web Dashboard、同域同后端；source=desktop仅独立Web客户端协议字段，不表示官方Electron Desktop。不得仅以开发服务器直连或后台API冒称该拓扑通过。 |
| PI-17 | 用户明确要求：不论Turn是否由Web触发，前端任意时刻接入后均应通过WebSocket API接收真实状态。静默不等于丢弃或隐藏执行事实；此前NO_REPLY及隐藏气泡／未读／通知的组合提案未获批准，不能据此屏蔽执行事件。实时订阅、中途接入和完成后恢复须分别取证。 |
| PI-18 | 用户明确授权补齐上述接线，不另起一套机制；后台Reminder运行时随时打开前端，应看到真实状态和完整Timeline。前后端并行，按本机反代部署形态实测并尽快收尾；不是只提供接口说明或用有界事件ring代替完整恢复。 |
| PI-19 | 用户确认表现层打磨完成，最终修改不得破坏现有UIUX。以用户最新表现为基线，状态／恢复接线不回滚布局、样式、动画、Profile图标、Pin／拖拽及滚动交互；必要状态体现优先复用既有组件，单独审查功能差异，不整文件覆盖或挟带用户变更提交。 |
| PI-20 | 用户明确要求最终留一份上云部署SOP文档；应可据实际部署形态执行，并区分本机已验证事实、最终版本／产物和云端尚未验证环节，不把文档编写冒充上云完成。 |
| PI-21 | 用户收到精确NO_REPLY新增英文/中文及“只可信自动Instant过滤、保留状态/Thinking/工具/静默完成记录、不改deferred/未读/通知”提案后，明确答“先保持现状，列为待决项”。故本轮不实施该Prompt/过滤/展示协议；保留安静性既有失败和当前无变化仍可能业务汇报的限制，单列待决，不能冒称已授权或静默验收通过。其余状态接线及验收继续。 |
| PI-22 | 用户明确废弃Memory创建Skill方案，授权直接精简修改现有个人NM Memory Provider系统提示：仅Memory创建使用窄入口，一次提交完整内容及Metadata；其余操作走官方CLI。用户后续纠正：普通Memory字段仍可经批准用CLI修改；仅创建时Metadata错误须经批准删除后重新创建，禁止将该限制扩大为Memory整体不可修改；不因此授权修改、删除或重建既有失败样本，也不豁免partial/unknown先核实、不盲重试。撤销本次Skill自动加载及模型可见入口，避免与Provider提示并存冲突；本次仅改该窄接线，不启动新实测。 |

| PI-23 | 用户明确确认三类实测模型偏差（用户假设错误归因、截断Search结果夸大为完整核对/拼接原因、Noting补叙述未补对应来源身份）不构成本轮阻塞；保留真实观察，不再以这三类要求新增开发或补测才能交付。此决定不把原失败改成通过，也不自动豁免Memory来源Metadata实际落库或归档暂停提示等独立未验事项；无变化Reminder按PI-21保持待决。 |
| PI-24 | 用户纠正术语为“NM Thread同步”，不是归档。已同步History出现不一致时，插件识别分叉点并新建NM Thread，不重复保存相同前缀；第一条由插件生成接续说明，引用原NM Thread ID及最后共同消息的NM原生Message ID（不得以Hermes消息身份代替），第二条起保存分叉点消息及后续。用户授权实现该机制并补齐必要真实验证，尤其须由模型实际调用专用入口创建Memory并确认Metadata落库。Provider系统提示英文原文必须先交用户审批，批准后仅落实该句，不改其它无关提示；root已提交简短原文待批，批准前不再修改Prompt。旧暂停设计不作为成功分叉的最终行为；保留旧Thread，不自动覆盖/删除旧数据，不把新Thread当Memory创建。 |

| PI-25 | 用户明确此类NM小工具独立于Hermes，统一放运行主机 `~/scrips/`，云端也相同。不得依赖Hermes安装目录、HERMES_HOME、仓库cwd或Hermes模块；使用运行主机官方NM配置。工具接受正文与通用Metadata，Hermes来源由调用方提供，不自行查Hermes。root据此安排独立创建入口 `python3 ~/scrips/nmem-memory.py create`，原HERMES_HOME版本英文因用户质疑未获批；新路径英文原文已单独提交待批，批准前不改Provider提示。 |

| PI-26 | 用户对新独立工具路径的精确英文原文明确回复“批准上述英文原文”：`For approved Memory creation, use \`python3 ~/scrips/nmem-memory.py create\` to submit the content and \`metadata.hermes_provenance\` together; use the official \`nmem\` CLI for all other operations, including edits to ordinary fields, and correct erroneous creation metadata only by user-approved deletion and recreation.` 仅替换root此前追加的长句，其余Provider提示保持；不恢复Skill，也不豁免真实创建/Metadata回读验证。 |

## 两阶段独立审查与版本定位

判据阶段只读上述产品原文、身份参考、用户口径和本Skill，独立把全范围要求/判据落入verification.md §2；不读动态CLAUDE、实现代码/测试、历史审查/实测报告或主会话解释。允许确认表引用版本。无须发送“判据完成”消息，写到报告即可。

两仓当前仍在集成；主会话随后提供**不变的源码/规格快照及SHA清单**。收到完整冻结交接之前，不进入代码/测试/历史证据调查。随后只审该固定版本，工作区之后的变化不能混入结论。公开核心、独立UI和个人NM三个仓库均纳入当前使用链，不把个人内容提交公开核心。

既有第三轮历史文档与证据入口：`.autonomous/20261016-round3-secretary-nm/`，但只能在判据完成且冻结交接后读取。旧结论不作当前通过证明。

## 固定待审实现（源码快照，不读取后续移动工作区）

- hermes-secretary: `/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary`；原HEAD `63761bd5d324b45437a5cf307e10915b4e20524b`+捕获时dirty；manifest SHA256 `542965d5eb76bda2f516a8d47219c35a4bba3eb601f81e588001b1126879e235`。
- hermes-secretary-web: `/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web`；原HEAD `7f0fea60463c6731f8e04a00db923d28b80ade19`+捕获时dirty；manifest SHA256 `c2b95d767e2c0c3dfc6b5e5ea46f1f07028a0bf2b7677aac1d244d4e227d01ab`。
- hermes-nmem-provider: `/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider`；原HEAD `1eb8d9a2a4e81101255ee8ae3998275ab608e52f`+捕获时dirty；manifest SHA256 `828007e515a26b6388f692ec5e063f189ff124361a82f4154a0a78d333bca410`。

完整清单：`.hermes-dev/product-intent-review-20261018/frozen-code/snapshot-set.json`。运行中的后端未因冻结重启，不把磁盘源码当现场已加载。判据落盘后以此固定副本审查，不按后来工作区变化改结论。若必须运行反证，优先固定副本；需在原PM环境运行时先核对受影响文件与固定清单一致，不能把不匹配版本结果归入本轮。

## v5集成后固定候选（历史定位不覆盖）

当前复审对象为ignored `delivery-snapshot-v5/snapshot-set.json`，SHA `272fbb072da400fe5119b87bbd742e366e3e2a6ab806e211554ebaa941f00c2a`；三仓完整只读副本／manifest同目录。Core源码提交`0dc4232f597f0c36d070fd5eabd578366436fca3`、UI功能提交`652f487a536874e0405fae547941be36950cc144`、个人提交`3732f5503eccc0c97df0ea0238b140b9997e69df`已自动同步且显式核远端一致。UI受保护表现层overlay随固定manifest／已构建产物验收，没有挟带整文件提交；裸UI功能commit不等于实际产物的完整源码树。v4→v5仅Core一个生产读取文件及其定向测试变化，UI生产零变化；当前动态文档另据报告更新。此候选不代表门禁／部署已通过，历史各版本结论不改。

## 后续部署筹备确认（不回改固定v5的PI01–26门禁范围）

| 编号 | 用户最新明确决定 |
|---|---|
| DP-01 | 先不要部署；先筹备将上传的两个Profile Home并提供两SOUL文件位置。用户编辑定案后原文上传、不再改写。主Profile名Alex，辅助名study；Alex复用当前主头像，study复习图标。 |
| DP-02 | 云端代码仓库`~/hermes-secretary`；物理Home`~/.hermes_profiles/Alex`与`~/.hermes_profiles/study`；前端不上传源码仓库，只部署构建产物。 |
| DP-03 | 两Profile共用同一个云端`~/workspace`（用户明确改为单数，替换先前workspaces），整个目录与本机`~/Desktop/Alex`走Mutagen；本机不存在可创建。 |
| DP-04 | 另增本机`/Users/edgar/.hermes_profiles`↔云端`~/.hermes_profiles`同步。数据库最关键；用户同意云端唯一运行库，经SQLite一致性快照复用原Mutagen通道回传，配置与SOUL同步，其它运行态无需同步。不把正在变化的数据库做两端直接文件覆盖。备份频率尚未定，当前不启用。 |
| DP-05 | 将Pi在此前原生Hermes导入后的新增聊天继续同步到原库，保留原数据／身份和既有导入方式；为新Alex部署筹备当前版本兼容副本，不把本轮合成测试历史搬到生产。 |

上述为部署筹备而非上云执行授权。固定v5两个独立门禁仍只对其已冻结范围作判断；新部署文件与数据打包单列验证，不据此宣称云端／Mutagen运行已验。
