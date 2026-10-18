# Hermes Secretary 项目主看板

## 自主口径收敛 · 待用户追认

**暂无。** 用户确认的来源先结算、Candidate 后处理、Prompt 控制体量沿 R3-019；Schedule 三种 kind 统一使用条目所属时区已落 07 §6.1。最新验收顺序、真实 NM 授权与测试时间尺度见下方，不是 Agent 自主扩大范围。

## 当前轮次：按最新产品意图自主复审至交付（2026-10-18）

用户最新要求覆盖此前“静态推迟/等用户看报告”的排程：**继续自主实现直到交付；只有Verification使用Astra/high，所有实现、调查、测试使用GPT-6.1/high。技术规格本身也可能有错，以最新产品文档及后续明确用户口径为准。** 当前轮次唯一入口为[20261018-product-intent-review/snapshot-index.md](.autonomous/20261018-product-intent-review/snapshot-index.md)，计划/审查/后续重拟测试分别在同轮目录。第三轮旧索引/结果保持历史，不据旧PASS或规格豁免当前偏离。

`product_intent_verification`是全新无主会话上下文Astra/high，先从固定产品原文建立判据，未收到代码快照前不查实现；root等待当前UI修补交回并集成后交固定三个仓库快照，防止审查移动目标。`validation_environment`继续6.1/high修侧栏Profile误筛选；`validation_profile_prep`的模型Notebook审计ID投影已root阅读接收，12独立节点及检查通过，尚未现场加载/真实模型补证。`validation_live`已整包交回NM注入与20条输入账本，只读追核不当新实测。

审查后按报告统一委派修复，主会话重新拟定覆盖当前场景与功能的Validation计划并交6.1执行；必要时等待完整包，不亲自下场实现、不让Agent流水账、不重复测试。框架Prompt一般授权边界仍遵守用户明确限制；本次用户已明确的模型内部标识纠偏已授权，不把其余未决事项当所有工作停工理由。

以下保留此前阶段证据与继承边界，涉及当前排程以本节为准。

## 当前目标与执行边界（2026-10-18）

**上下文恢复首要要求（用户反复强调）：主会话按产品负责人工作，抓全局、场景设计、体验质量和上线取舍；这是尽快上线的使用验收，不是一般编码任务。控制开发成本和token开销，细节实现/调查交子Agent，高并行且不重复测试；无必要全局工作时等待完整交回。子Agent默认整包完成一次交回，中途仅无法继续的阻塞或必须由主会话决策时发消息；每次派遣重新强调，不把单步骤包装为阶段汇报（已写AGENTS通用规则）。不能因压缩上下文重新陷入逐文件排查、泛化重构或无限扩测。** 用户现已托管，等待集中报告；非必要不打断。正式实测已由validation_live整包交回，主会话已按真实结果复核接收，不全信DeepSeek、不擅改框架Prompt。

第三轮进入**收尾与真实使用功能 Validation**，争取尽快部署。用户明确推迟静态 Verification：主会话设计场景及判据，GPT-6.1-sol/high 子 Agent 实际执行；后续静态复审仍用 Astra/high。历史 NOT PASS 保留，不阻止用户本次要求的 Validation，也不据此宣称部署就绪。**三份核心文档已精简；双Profile首轮真实功能实测完成，两项接入失败已修并真实复验，当前等待用户审阅来源交付的Prompt建议。** 本次以使用结果为中心，不扩大为一般编码任务；主会话管场景、边界、集成与判断，子 Agent 默认整包完成一次交回，中途仅真正阻塞或需主会话决策时汇报。

最新授权见 [Snapshot Index R3-024～038](.autonomous/20261016-round3-secretary-nm/snapshot-index.md)，主会话场景与逐条消息前缀见 [Validation 计划](.autonomous/20261016-round3-secretary-nm/validation.md)。

- 新建本机主助手、考研助手两个隔离 Profile，安装个人插件接真实 NM；这覆盖本阶段旧 round3-only / fixture-only 限制。原 round3 共享服务保留，不访问或修改其用户会话。
- **用户明确：两个Profile都开启Noting。** Scheduler亦按本次提醒场景启用；Default只读不禁止各自Notebook整理。
- **最新测试配置：** 两Profile开启节约上下文的联合Idle Compact + Noting，触发阈值100,000 tokens；用户要求空闲几秒，主会话选5秒。调整触发阈值，不改模型最大上下文。环境Agent按正式配置设置并与实测Agent协调安全生效，保留已有记录；未实际达到阈值不能声称自动触发分支已验。
- 主助手读取现有 **Default Space，只读**；考研助手使用用户已创建的 **“考研复习” Space**，允许测试写入，亦获准新建测试 Space。私人身份、凭据和原始材料不进入公开核心。
- 主助手通过 Reminder 读取考研 Space 跟进活动，跨领域汇总走 NM，**不读取考研 Hermes Profile**。测试中**现实10分钟代表一天**，每天至少一次落成每10分钟实际排期；用真实时间标识测试日窗口，不改系统时钟或 Harness 内部时间规则。
- 每条发给被测主模型的用户消息都附测试说明：按自己的 SOUL/职责为用户服务，禁止查仓库、研究/建议 Harness 代码；如实直接回答工作体验。工作区外文件禁读，已授权 NM 服务访问保留。观察实际工具行为与结果，不做复习角色戏、不向模型灌入验收答案。
- 已读 `~/.pi/SYSTEM.md` 与用户提供的《场景、个人需求、长期愿景与产品设计原则》；两份SOUL已按用户最新要求清除测试背景，可直接作为部署身份文件，源文件在ignored `validation-personal-20261018/personas/`并同步各Profile。测试角色/10分钟尺度/文件边界仅由逐条user message前缀提供，不写SOUL。身份为长期私人顾问/考研专职助手；允许闲聊倾诉，不强制转任务。旧 Pi 工具、默认写权限及飞书任务不自动继承。测试配置/SOUL可调，**框架写死Prompt未经用户再次授权禁止修改**；实测一轮后再给建议。DeepSeek只作本轮代理模型，实际K3未测，不将其自述/建议当事实或正式模型结论。

## 当前看板与接续

| 工作 | 状态 / 下一步 |
|---|---|
| 三份核心文档精简 | 已完成；主会话亲审两子 Agent 返回变更，核对规则、未结项与证据入口。README/AGENTS合并冗余，CLAUDE移除内嵌旧看板并保留原文快照；仅文档检查，不跑产品测试 |
| 双 Profile 环境 | 已整包交回：53446后端PID91341、5174 UI PID41912；插件指纹、两SOUL、Noting/Scheduler、owner密钥、正式Bundle读取均核对。原round3保持。证据 `environment-report.md`及evidence环境清单 |
| Default 只读 | 自动归档缺口已补：main archive_enabled=false，exam=true；正式manager/结束重试/上传出口无写定向证据。手动NM仍按SOUL/逐条消息授权限制并以实际轨迹核对，不宣称通用终端沙箱 |
| 手动 NM 访问 | 插件的Space提示不是终端权限隔离。NM只读追核已确认双Profile实际绑定system prompt含非空Bundle（2993/2986字符）、正确Space及排除WM；正式Recall三样本pointer数0/0/1，查询工具返回实际正文。命中pointer的Turn未新精读，因为正文先前已在上下文，不能称pointer驱动精读已验。证据`evidence/nm-injection-audit.json` |
| 归档配置修补 | 主会话已review接收：个人Provider可选archive_enabled（默认true），关闭时禁止自动归档/结束重试，保留Bundle/Recall；60 PASS及定向检查，未改Prompt。环境Agent获准安装，报告 `provider-archive-control.md` |
| 身份资料 | 下载需求原文及SHA留ignored inputs；两SOUL已改为部署身份文案并同步Profile，移除测试背景/10分钟尺度/测试官约束；原NM授权保留。旧版与新hash在`evidence/soul-deployment-cleanup.json`，已有系统快照不改写；测试语境只用逐条user message前缀 |
| 功能 Validation | 首轮P01–P07及两段真实600秒窗口已完成，NOT PASS。双Notebook、批准边界、来源先归档、跨压缩History、cold/warm跨Space跟进有真实证据；自有未来排期/runtime/lease/poller已清零，保留环境。`validation_live`维护实际结果，不重跑已有效链 |
| 首轮接入修复 | 已接收：VP-04在5秒预算下3个正式Turn自动Recall通过；VP-01真实首批22→同Thread同Space24，receipt/正文/旧前缀一致，回收后无重复。保留首轮及第一次补丁失败；7项定向+真实复验关闭本场景。没有框架Prompt修改或全量重跑 |
| 首页Profile误筛选侧栏 | 用户发现切换首页Profile只显示该Profile会话，未经授权、偏离06 §2.11。`validation_environment`负责跨Profile列表/真实owner打开/新建Profile与draft边界的窄修及真实UI只读复验；不接管Pin表现层。此前Profile验收漏了跨Profile列表可见性，不能沿用旧113项结果宣称本行为正确 |
| 模型Notebook内部标识 | 用户指出给Hermes AI的NOTING RESULT泄漏Snapshot/Coverage anchor内部ID，root先前误当人类展示已纠正。`validation_profile_prep`窄修完成通知及同步07英文模板，保留后台metadata/选择校验；同时只读检查其他模型输出，不混同已修的人类/notebook F13。待集中review/定向证据 |
| 来源交付与体验建议 | VP-02仍缺提案原文核对/内容标签及Hermes来源Metadata，待用户决定短Prompt修订；不由测试SOUL灌答案。VP-03模型自述有误，VP-05安静/无记录汇报测试要求有张力，不直接认定代码Bug。当前整体验收仍NOT PASS，详见final-delivery当前段 |
| 静态 Verification / 最终交付 | 按用户要求推迟；历史二审不通过。待实际功能结果后判定剩余修复与部署范围，不能用计划代替通过 |

环境已按独立runtime root、53446后端管理两新Profile、5174 UI部署；见[环境报告](.hermes-dev/validation-personal-20261018/environment-report.md)。数据库在仓库ignored目录，terminal.cwd在Git root外，原round3保留。最初Bundle HTTP被Cloudflare403拒绝，已在个人客户端复用官方CLI context read，内容契约/Prompt不变；root review及两Space真实只读核验通过（`provider-bundle-cli.md`）。旧[准备报告](.hermes-dev/validation-personal-20261018/preparation.md)仅保留调查时点；不得用`hermes serve --stop`误停共享实例。

## 当前代码与运行现场

| 项目 | 最近已核对事实（后续执行前再核对） |
|---|---|
| 公开主仓 | `main`；本次实际产品运行基线`4e21f787595571cad8efe36fa725fef1f8b2636f`+既有dirty，报告阶段`bbfc7c51`已同步origin/main；后续仅文档收口。同期UID、Running DTO、规格及测试改动仍保留，不整树提交 |
| 独立 UI | `../hermes-secretary-web` / `7f0fea60463c6731f8e04a00db923d28b80ade19`；含 Running 时长、侧栏触摸与滚动测试等未提交改动，保留他人工作 |
| 个人插件 | `../hermes-nmem-provider` / `1eb8d9a2a4e81101255ee8ae3998275ab608e52f` 已同步`origin/codex/round3-local-completion`、工作区干净；安装client/provider指纹与真实复验一致，不进入公开依赖 |
| 环境 | 官方 PM `.venv` Python 3.14.7、macOS arm64；现有锁不变。DeepSeek 原生 custom/chat_completions，不接 Codex App Server/Proxy |
| 现存 round3 | `.hermes-dev/round3-runtime/profiles/round3`；53445 后端 PID60820 / wrapper60815，5173 UI PID40290；准备 Agent 已只读确认监听，未重启 |
| 最近重启 | Notebook UID 行为验证前经用户授权 SQLite backup 后重启，health ready、Profile 配置 hash 不变；加载当次工作区代码，不保证之后磁盘变化都已载入 |
| 开发开关 | round3 启动配置 `gateway.model_code_skew_guard: false` 已生效；只跳过模型操作5098/503，独立4001等保护保留，不等于模块热更新 |

稳定架构、运行命令和规格入口见 [README](README.md)；通用规则、测试及提交同步流程见 [AGENTS](AGENTS.md)。本阶段仅提交自有文档和独立个人插件修补，保留其他人的代码；仅重启新双Profile的测试服务，原round3保留。

## 当前未结项

| 项目 | 当前判定与处理边界 |
|---|---|
| V2-F02 退休工具名 | `notebook_mutate` 仍缺退休集合，可被 repair 成新工具；截至部署审查未修，保留静态发现，不假称关闭 |
| V2-F03 冻结父前缀 | 自定义 ContextEngine 下 child 第2/3请求可重写冻结消息；相关生产文件与二审版本相同，尚未修 |
| V2-E02 output-cap | 正式错误恢复分支证据不足；不将普通 overflow 证据冒充该分支通过 |
| F16 来源结算 | **现行首轮真实NM样本通过**：成功写入后先归档来源#1，再归档Candidate#5，未覆盖事项保留；遇到入边拒绝后修正引用再成功。证据 `evidence/validation/f16-observation.json`。历史失败保留，本样本不外推所有模型/分支；不再把它当未做的新开发包 |
| 旧样本未批准写入 | F16旧A/B/C Main曾违反“不批准”而写USER，后续Prompt有调整；真实NM验证必须观察批准边界。round3仍保留旧合成Conversation/记忆及A/B排期，未清理，不误作新测试对象 |
| 压缩新增断言 | 两处 `_usage_context` 附加估算元数据使精确dict断言失败；原回滚/原文/身份/runway断言先通过，符合用户冷估算授权。测试待同步，不能回退估算功能迎合旧断言 |
| 全量其他失败 | cold/Slash/Instant旧夹具需恢复有效覆盖；in-place多活动行、未回复Turn合并、Gateway失败回写、CLI多模态持久化仍待区分旧断言/真实错误。299既有失败不等于已豁免 |
| UI现场 | Mobile抽屉后触控板wheel失效曾观察到，后续未稳定复现，未定位根因；长按菜单只有合成测试；首Thinking永久缺失原现象未被真实replay完整证明，已有DOM稳定修补不冒称全现场关闭 |
| 部署边界 | 双SPA、Cloudflare/Access/手机端未完成真实部署验证；Files真实SSH未验；当前Mac证据不覆盖其它平台。新运行产物尚未统一冻结提交 |

用户另指定 Agent 负责 Pin 表现与拖拽；本会话不接管。Orb Idle倒计时已取消，现有外观保留；真实 Running 正计时为另一个已确认需求。普通提示5秒、错误手动关闭，冷启动允许沿上次可信值估算，均已写入06，不能重新当未确认缺陷。

## 已接收的关键证据

### 冷态 Reminder：实际链已通过，不能扩大为整轮通过

[报告](.hermes-dev/deploy-readiness-20261018/reminder/report.md)：真实 IAB/WS＋DeepSeek，round3 合成Conversation `conv_ec6d07953a634ace94883b51b4202cc3`。Runtime/poller 回收后两次 Instant 由宿主自动恢复同一会话，到期约4.995秒/0.715秒写唯一见证并获真实响应；两条 deferred 到期不唤醒，后续用户请求合并成唯一 carrier，真实Provider成功后分别ACK。Instant沿witness/admitted语义，不误写成deferred ACK。

结束时自有Runtime/poller、claim、lease、pending和未来排期为零，四条done且各claim一次；其他会话保留。主会话亲审报告、final/verification JSON和原始记录后接收，不复跑。未做真实宿主全重启及所有失败竞争分支；这些仅有受控19项＋邻域76项证据，见 [.hermes-dev/cold-scheduler-fix-20261018/handoff.md](.hermes-dev/cold-scheduler-fix-20261018/handoff.md)。

### 10-18 全量自动化：一次混合工作区运行，不能作为冻结版本门禁

- 后端 canonical runner `-j 8 -q --tb=short --show-capture=no`，无文件重试；11:01–12:01，3575.6秒：**59,466 PASS / 321 FAILED（91文件）/ 1,421 skip，另71次ERROR（69唯一节点）及1个300秒超时**。运行起点b9d355bcaa，期间有d58cd3e5b8/4e21f78759及dirty变化。
- 相同91文件在旧基线4e091754e1复现299 FAILED；差额22中20在干净工作区通过，2项为上表估算dict断言。ERROR不包含在321内：cold_noting_resume17、secretary_slash6均setup失败，主体未执行。
- 64个Provider失败停在旧tool断言，36个CI脚本失败涉及旧Bash；PM/update/插件部分为TLS或隔离环境。三个“无FAILED却非零”实为2P/20E、41P/8E、12P/1E，非已证明warnings-as-errors。只额外做Noting生命周期单节点1 PASS，文件内泄漏尚未证明。
- UI当次36文件 **603 PASS**（7.45秒），`tsc -b` PASS；不外推之后改动。
- [归因报告](.hermes-dev/deploy-readiness-20261018/suite-triage.md)、[逐节点索引](.hermes-dev/deploy-readiness-20261018/suite-triage/failure-index.json)、[主会话审查](.hermes-dev/deploy-readiness-20261018/main-audit.json)；原始日志 `.hermes-dev/full-suite-20261018/`。不重跑全量，失败修复只定向复证。

### 后续实现与专项证据

| 范围 | 已完成与有效证据 | 限制 / 定位 |
|---|---|---|
| Notebook局部来源UID | 模型/可读Notebook用source_message_uids，可信owner补全内部身份；拒双表示。393项有效覆盖通过，ruff/health/no-tmp通过；真实完整工具面父/branch整理、History查源、父子Snapshot隔离8项行为判据通过 | 尚未提交。证据 `.hermes-dev/notebook-local-uids-live/`；父conv_93d1456176c54d9d996b259c34e86c42、分支conv_6da3c0caca744dfcba8516ea85bed5dc。分支压缩因summary would grow被拒，Noting独立完成，不冒称压缩成功 |
| Noting Running正计时 | 可选started_at取真实child registered_at；前端每秒刷新，无start隐藏。修正持久注册先于live广播。后端相关10 PASS，前端33 PASS＋mock24 PASS，typecheck/build通过 | 无轮询/推测起点；health0/0。代码dirty；原旧Web2失败及review.summary orphan另记，不算本包通过 |
| 完成高亮 | 真实pointer_changed→可选completion_snapshot_id，并读取同owner当前pointer确认；失败/非winner/foreign/冷读不亮；完成事件不消灭未确认提示 | UI87 PASS＋集成新增1 PASS、Python定向与契约生成通过。任意异常延迟跨rewind重回同Snapshot无epoch区分，未声称覆盖；后端d58cd3e5b8/UI7f0fea6已同步 |
| 增量审查修复 | 冷估算owner/模型、所属时区117 PASS；UI绝对时区/AI起名分类与UID去重52 PASS；证据脚本健康修补保留原失败/hash | [专项报告§8](.autonomous/20261016-round3-secretary-nm/post-verification-review.md)，`.hermes-dev/post-v2-resume-20261018/`；不重复旧有效证据 |
| 冷态Scheduler/Files | 常驻宿主扫描→原生恢复/接纳；Files固定default，返回恢复聊天Profile；后端files22 PASS、前端194有效PASS、构建通过 | Scheduler受控19＋76邻域及上文真实链；Files真实SSH未验。UI524e479已同步，08为权威契约 |
| V2-F01/F04 | 来源统一History可见性；恢复未来排期不跳次日。F01新5 PASS、scheduler52 PASS、邻域261 PASS | 另外41P/2F及132P/6F的8失败在0dfa26a58d复现，不冒称全绿；F16旧样本见 `.hermes-dev/f16-retest-20261017/` |
| Context冷恢复/Compact | 可选_usage_context与精确anchor分离；按owner/model/rewind校验。Compact等待660秒、真实完成刷新、清原slash保护新稿；现场两次重启首resume ACK恢复44,743/262,144（17%） | 前端289有效PASS；后端70P/1环境F及集成定向通过。ACP依赖与review.summary orphan未关；`.hermes-dev/compact-cold-context-20261017/` |
| 恢复指引 | 合格Main摘要指向conversation_history，含压缩区间/Conversation起点，替换旧footer；protect_first_n默认0；手动Compact成功提示 | Python10＋73 PASS、UI48 PASS。自动压缩通知用户明确无需；tail逻辑未改，默认值现场生效未单独取证 |
| Timeline/Profile/提示 | 呈现key/空白补卡修补；首页独立Profile菜单，已有Conversation归属不变、固定图标映射；普通提示5秒，Reminder26词每条带说明/整批一carrier | Timeline最终56 PASS（旧有效并集99）、Profile113有效PASS、notice28 PASS、Reminder2 PASS；[增量审查报告](.autonomous/20261016-round3-secretary-nm/post-verification-review.md)。未映射Profile通用图标，不冒称独占图标 |
| Mobile长按/滚动 | 触摸contextmenu含pointercancel/卡片隐藏边界13 PASS，typecheck/build通过；抽屉wheel回归测试已加 | 现场wheel后续可滚动但根因不明；HMR旧状态仅假设。长按未实机验收，保留鼠标/键盘菜单 |
| 5098开发开关 | 相关73 PASS/1平台skip；round3真实checkout漂移后model/options仍200 | 非热更新；gateway/TUI独立进程及跨平台未验，06 §0.8 |
| 双SPA/4001/标题 | 双SPA235 PASS，UI Controller73 PASS及typecheck/build；4001按原owner恢复一次；`/title`手动/读取、Web本地`/ai-title`独立起名 | 06 §0.7及标题契约；真实Cloudflare/手机部署未验，旧标题测试9个jsdom失败为当时基线，不覆盖较新603PASS |

## 历史轮次与证据入口

| 内容 | 唯一依据 / 历史结论 |
|---|---|
| 第三轮冻结与用户口径 | [snapshot-index.md](.autonomous/20261016-round3-secretary-nm/snapshot-index.md)、[baseline.txt](.autonomous/20261016-round3-secretary-nm/baseline.txt)；初始冻结不改写 |
| 开发分包与接线 | [plan.md](.autonomous/20261016-round3-secretary-nm/plan.md)及同目录c1～c11/personal报告；旧分包已交回，不沿旧“未派遣”表重新开工 |
| 真实模型 / 回归 | [real-model-report.md](.autonomous/20261016-round3-secretary-nm/real-model-report.md)、[regression-plan.md](.autonomous/20261016-round3-secretary-nm/regression-plan.md)；旧1766P/29F/4setupE/3skip保留，后续逐失败关闭不改原日志 |
| 个人Provider旧证据 | [personal-report.md](.autonomous/20261016-round3-secretary-nm/personal-report.md)、[personal-host-report.md](.autonomous/20261016-round3-secretary-nm/personal-host-report.md)；46用例、正式host→fixture六场景，非真实NM验收 |
| 正式二审 | [verification.md](.autonomous/20261016-round3-secretary-nm/verification.md)、[final-delivery.md](.autonomous/20261016-round3-secretary-nm/final-delivery.md)；公开b40fa1f，87细项，10反证用例3P/7F，NOT PASS；个人线未代签 |
| 较早静态复核 | [verification-2.md](.autonomous/20261016-round3-secretary-nm/verification-2.md)，保留当时NOT_RUN/INCOMPLETE，不冒充正式二审 |
| 本次精简前原文 | [CLAUDE.before-validation-trim.txt](.autonomous/20261016-round3-secretary-nm/snapshots/CLAUDE.before-validation-trim.txt)；保留所有旧分工、历史PID、失败/修复过程及原始段落，只读快照，非第二看板 |

后续只在本页维护当前状态，长轨迹进入已有专项报告/ignored证据目录；不再把旧看板全文嵌回。未执行、已修复、已定向验证、已真实验收、已部署分别记账。
