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

## 两阶段独立审查与版本定位

判据阶段只读上述产品原文、身份参考、用户口径和本Skill，独立把全范围要求/判据落入verification.md §2；不读动态CLAUDE、实现代码/测试、历史审查/实测报告或主会话解释。允许确认表引用版本。无须发送“判据完成”消息，写到报告即可。

两仓当前仍在集成；主会话随后提供**不变的源码/规格快照及SHA清单**。收到完整冻结交接之前，不进入代码/测试/历史证据调查。随后只审该固定版本，工作区之后的变化不能混入结论。公开核心、独立UI和个人NM三个仓库均纳入当前使用链，不把个人内容提交公开核心。

既有第三轮历史文档与证据入口：`.autonomous/20261016-round3-secretary-nm/`，但只能在判据完成且冻结交接后读取。旧结论不作当前通过证明。

## 固定待审实现（源码快照，不读取后续移动工作区）

- hermes-secretary: `/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary`；原HEAD `63761bd5d324b45437a5cf307e10915b4e20524b`+捕获时dirty；manifest SHA256 `542965d5eb76bda2f516a8d47219c35a4bba3eb601f81e588001b1126879e235`。
- hermes-secretary-web: `/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-secretary-web`；原HEAD `7f0fea60463c6731f8e04a00db923d28b80ade19`+捕获时dirty；manifest SHA256 `c2b95d767e2c0c3dfc6b5e5ea46f1f07028a0bf2b7677aac1d244d4e227d01ab`。
- hermes-nmem-provider: `/Users/edgar/code/hermes-secretary/.hermes-dev/product-intent-review-20261018/frozen-code/hermes-nmem-provider`；原HEAD `1eb8d9a2a4e81101255ee8ae3998275ab608e52f`+捕获时dirty；manifest SHA256 `828007e515a26b6388f692ec5e063f189ff124361a82f4154a0a78d333bca410`。

完整清单：`.hermes-dev/product-intent-review-20261018/frozen-code/snapshot-set.json`。运行中的后端未因冻结重启，不把磁盘源码当现场已加载。判据落盘后以此固定副本审查，不按后来工作区变化改结论。若必须运行反证，优先固定副本；需在原PM环境运行时先核对受影响文件与固定清单一致，不能把不匹配版本结果归入本轮。
