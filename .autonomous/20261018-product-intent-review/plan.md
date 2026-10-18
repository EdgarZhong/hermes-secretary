# 产品意图复审与交付计划

## 1. 目标与依据

最高产品依据为本轮snapshot-index指定的最新产品原文及用户明确口径，技术规格本身也是审查对象。固定版本及逐文件指纹见baseline.txt与ignored frozen-code/snapshot-set.json；不能把原HEAD当作全部待审代码版本。核心、UI、个人NM相互独立，个人资料不进入公开核心。

目标：当前范围内的使用预期、规定机制和完整链路都取得对应证据，关闭规格/实现偏离与必要证据缺口；修复后执行覆盖场景及功能的真实Validation，交付与版本匹配。未来正式跨助手委托、记忆治理/自动蒸馏、数月效果不扩成本轮功能；长期观察不能代替上线前可验证链路。

模型：只有独立Verification使用Astra/high；实施、调查和Validation使用GPT-6.1/high。主会话负责产品判断、分包、接线与review，不亲自实现细节。默认整包一次交回，不重复测试。

## 2. 覆盖与任务

| 输入/要求 | 任务及owner | 范围/接口/依赖 | 完成判据与验证 |
|---|---|---|---|
| 产品原文全篇、PI-01～11 | Q0 独立产品意图Verification；Astra/high | 固定产品原文先立判据，再读三个固定代码副本/工程规格/证据；只写verification.md和ignored反证 | 产品要求→判据→实现/规格路径→条件→证据→判定逐条可追查，包含规格偏离、实际入口与缺失场景，不能只核旧技术规格 |
| PI-05、PI-06 | Q1 当前用户纠偏集成；已由6.1交回，root review | 模型Notebook投影与UI列表/owner身份；不改内部Store/外部API语义，不擅动他人表现层 | 见当前证据表；未加载/未真实界面复验的部分明确不算通过 |
| Q0独立发现 | Q2 规格对齐与整改设计；root | 明确产品语义已有要求、规格错误、实现偏离、证据不足；范围/权限冲突显眼登记 | 每条发现给最小修复必要条件、owner、白名单、上下游和原场景关闭证据；不迁就现状降低判据 |
| Q2整改包 | Q3 并行实施；6.1/high | 修改范围不相交；依赖顺序显式；只补原失败与实际影响路径，不重复有效大套 | root亲自review正式接线/状态/失败/关闭行为，证据与精确版本匹配 |
| 产品原文§3～7、PI全部与Q0发现 | Q4 修后重拟Validation；root负责目标/体验判据，独立6.1补枚举/执行 | 使用下表覆盖清单作起点，须从产品原文独立反查并补齐，不将表当封闭上限 | 执行前有需求→用户操作→预期→正式入口→版本→证据→结论的矩阵，覆盖正常/纠正/拒绝/失败/冷恢复/重复/跨功能 |
| Q3收敛版本 | Q5 独立复审与真实Validation | 全新Astra/high复审全范围及影响；全新6.1/high独立验收，主会话过目完整场景计划后执行 | 适用要求/场景无违规、失败、未执行或必要证据不足；后台API/受控测试不能代签真实UI/模型结果 |
| 两门禁、产物与实际部署边界 | Q6 交付判定；root | delivery-evidence-review，版本/环境/剩余项/权限边界 | final-delivery准确说明当前目标状态；commit/push不代替构建、部署或验收 |

### 修后测试的最低覆盖清单（待Q0发现和修复结果补齐，不是已执行结果）

| 场景组 | 产品目标/功能 | 必须观察的用户结果和边界 |
|---|---|---|
| J01 多Profile、多Conversation | 首页选择、全侧栏可见、真实owner、模型/SOUL/draft | 两Profile已有会话同时可见；切首页选择不隐藏/迁移旧会话；新建及打开/重命名/置顶等操作归正确owner；同stored ID不混用；迟到响应/pending Send不换owner |
| J02 角色与自然交流 | 主助手/考研助手身份、共享/独立记忆、交流方式 | 新部署SOUL真实进入上下文且无测试背景；同题跨角色观察职责相关行为，不仅自称身份；分享/倾诉不硬转任务，具体求助得到具体帮助；不从少量回答推断人格因果或K3表现 |
| J03 约定、责任及不确定性 | 接受责任、暂缓、纠正、用户补充结果 | 目标/状态/阻塞/下一步跨话题及整理后可接续；未知不编造完成；用户撤回或改变约定后不沿旧目标擅自行动 |
| J04 长对话与原始依据 | 压缩、History、同Profile跨Conversation及分支 | 成功压缩后能回读原话与后续纠正；索引/摘要不代替原文；同Profile跨会话能正确定位，不用另一个Profile历史；分支/回退失效段不恢复为当前事实 |
| J05 自动上下文管理 | 真实100k阈值、Idle5秒、联合Compact+Noting | 使用有明确合成结构及可核查事实/修订/责任的数据，使真实context达到100000，空闲后从正式运行链观察自动触发；与模型容量区分。阈值未达、新输入打断、无变化/失败不算成功提交；不以手动compact/伪usage/低阈值代验100k |
| J06 Notebook到持久化 | Candidate、提案查源/内容标签、批准、真实NM写入与结算 | 暂缓/只改措辞不写；明确批准后写限定Space/内容并携带标签和真实来源；失败/partial/unknown不盲重建；已成功覆盖来源先处理再关闭Candidate，未覆盖责任/其它依赖保留 |
| J07 NM上下文与召回 | Context Bundle、正确Space、WM排除、pointer和精读 | 实际系统上下文含真实Bundle；每Turn指针属于当前owner/输入，空与不可用不同；新上下文命中指针后需要时实际读取正文并据其作答；不能把旧上下文已有全文或一次命中当新精读通过 |
| J08 主动跨领域跟进 | 10分钟测试日、两真实到期窗口、cold/warm | 到期后实际读取考研NM记录；区分新旧/无记录/读取失败，不读考研Profile；续排与结束取消正确。仅有意义变化/需用户介入时汇报的输入必须无歧义；不以无记录推断未行动，不制造任务/噪声 |
| J09 对话自动归档 | completed→Thread、跨压缩同Thread、增量与收据 | 正确owner/Space、正文与收据一致；后续仅新增suffix、回收/重试不乱推进；main实测只读仍无自动写。相同版本已有22→24真实证据可按代码匹配复用，其它异常用原机制证据与必要用户恢复结果组合 |
| J10 模型可见内容 | Framework、Main show、Noting working/control | 实际模型输入不含内部Snapshot/Pointer/coverage审计标识，保留完整有效Notebook及可操作条目/来源；内部过期丢弃/metadata/gate不被删除；现有历史不重写 |
| J11 时间线及反馈 | 首Thinking、工具卡状态、完成高亮、统计冷估算、提示时长 | 真实流式期间能看到首Thinking，不到Turn结束才补；工具卡无错误状态闪现；完成高亮跟真实有效结果；Context/Session Total估算与owner匹配；普通提示5秒、错误手动关闭 |
| J12 列表交互与持久偏好 | Pin拖拽/取消/重排、跨owner排序、重载、滚动 | 全局列表下跨Profile卡片顺序重载后保留；操作不影响别owner；现有手势/占位/滚动不回退。桌面模拟pointer证据与真实触摸设备覆盖分开，不以jsdom代签实机 |
| J13 关闭、隔离与恢复 | Noting/Scheduler独立、Secretary关闭原生、owner切换、冷恢复 | 正式开关和局部参与按契约生效；未启用路径仍原生；辅助/未知origin无越权；重启/失败恢复的责任、排期和状态归属不漂移 |

场景数量不是覆盖率。执行者须根据Q0独立要求与实际合法分支继续细化，保留负观察；一条旅程可共享前置但每项结果单独取证。真实模型/平台/工具版本、合成数据、Profile/Conversation与原始输出都可定位；所有测试user message使用既定前缀，SOUL不承担测试协议。

## 3. 当前证据与执行边界

| 范围 | 机制/正式接线证据 | 真实模型/用户结果边界 |
|---|---|---|
| 模型Notebook审计字段 | 6 RED→12独立节点PASS，覆盖inline/catalog/child多Turn wire及通知metadata；root review接收 | 修后版本已加载，双owner自然Noting样本待整包复核；最新UI仍未验 |
| 跨Profile列表 | 首包234相关PASS/typecheck；首次修补曾真实看到3条跨owner会话 | 后续owner/Pin补强的界面没有复验，不挪用首包Chrome截图为新版通过 |
| 同ID owner及Pin全局顺序 | 原反例→68相关PASS，再补Pin重载反例→24相关PASS；各自按变更版本和实际影响记录，不相加假称一轮全量 | 受用户显示约束，最新UI未验 |
| 既有NM/Reminder/压缩 | 历史第三轮报告与逐文件SHA可按相同接缝复用 | NM Bundle确实入上下文；Recall三样本0/0/1指针，pointer驱动新精读未独立证明；两600秒跟进、来源结算、22→24Thread各按其样本范围，不代表全轮 |

界面执行边界以PI-12为准：仅允许CUA下隐藏Codex IAB（visible:false），仍禁止外部浏览器、可见页面、桌面和任何显示变化。用户PI-16/18要求从本机反代53448进入双SPA同后端验收；已有准备产物随本次UI修复重建。API/jsdom不能代签UI。

所有运行库在仓内ignored目录，terminal.cwd在git root外；Default仅实测读取，exam Space仅获授权合成资料操作。凭据、身份原文和NM私人正文不入Git/公开报告。只清理自有未来排期/runtime/poller/lease，不清理桌面或关闭用户窗口；服务/已授权测试资料按计划保留。

## 4. 缺陷、取舍与快照

Q0完整报告为NOT PASS（31条矩阵，7节点反证3P/4F）。下表定义整改完成条件；动态编排和进行时状态只在根CLAUDE，不在此建立第二看板。

| 发现 / 整改责任 | 最小完成条件及复验 |
|---|---|
| F01 / coverage包 | 恢复真实、可读覆盖范围，四类模型面无内部审计ID；生成时间不能冒充证据覆盖，旧/新边界T01可区分；解析失败诚实未知，默认API兼容 |
| F02 / protocol包 | 正式请求保护冻结父前缀且原生ContextEngine仍处理允许后缀；T02三次请求、续Turn、非Noting原生对照成立 |
| F03 / protocol包 | 原始退休名在模糊repair前被一致拒绝，完整集合覆盖同步/并发/直接路径；T03两负一正及未启用原生对照 |
| S01 / root授权后修订 | 产品默认24h自唤醒行为约定不弱化为任意远期Reminder；保留静默/用户关闭，不新增强制daemon；现有远期排期/无新输入场景 |
| S02 / root统一契约 | 来源形态、先源后Candidate、最后引用处理与部分成功一致，避免实现和规格各自宣称通过；不借旧双来源要求擅自推翻现有契约；正式child证明转换和未覆盖依赖 |
| E01 / 独立Validation | 新部署SOUL实际加载，双owner真实100k和5秒自然联合Idle，不降阈值/手动触发冒充 |
| E02 / NM包+后续实际链 | helper参数层级和技能索引先修；Metadata正式传输、提案原文/标签/来源回读仍单独关闭，不把工具可发现当实际全链成功 |
| E03 / 独立Validation | 纠正/未知/安静性、partial与多目标、来源后改、共享依赖、pointer首次深读；不由模型自述或单样本外推K3 |
| E04 / protocol包+证据映射 | 首先最小output-cap受控正式恢复；晚到/rewind、Reminder全宿主/ACK、NM丢ACK/Cron按同版本证据映射只补实际缺口 |
| E05 / 合规UI Validation | 真实首Thinking/工具状态、跨Profile旧会话、提示计时/冷统计；无合规后台IAB接口仍记未验，不操作屏幕、不用jsdom/API代签 |
| Q01–Q03 / root | 部署身份与测试权限分层、委派适用范围、正常rewind后归档暂停与长原文取证边界；未授权写权不扩大、未决定限制不冒称用户接受 |
| D01 / 执行工具隔离窄包 | execute_code实际kernel scratch必须显式归当前Profile，不沿启动Profile的进程级tempfile默认目录；两个Profile各自首建与续用、原生单Profile默认和失败清理须有定向证据。不据路径或reused计数误报跨Profile共享变量，不扩大成执行器重构 |

产品语义冲突给依据、影响和最小决策；必要工程空白按既有授权收敛并显眼记录。修复后全新独立复审仍检查全范围，历史失败保留，不能只核上表旧发现。

当前固定快照详见baseline.txt；不变副本供独立审查，之后修复建立新版本和关闭证据，不能覆写本版失败。全部受影响检查按冻结基线，不放宽门禁求绿。相同原因连续三次修复无效时停止重复尝试，做根因复盘。


### PI-18增量验收要求

复用既有会话生命周期、历史／输出投影、事件回放和全局广播，补齐后台Turn可观察性：已连接、首次中途接入（含工具正在运行及ring早期事件淘汰）、断线重连、完成后打开；状态与完整Timeline按真实owner恢复，无漏项／重复，未打开会话全局运行状态变化可达，不resume全部会话。通过本机反代及隐藏IAB对账真实Reminder、WS和持久结果；此项尚未完成，不用旧cold执行成功代签。
# PI-24 当前增量：NM Thread分叉同步与真实Metadata创建

**PI-25后续修订：** 独立NM创建工具统一安装运行主机 `~/scrips/nmem-memory.py`，本机／云端一致，不依赖Hermes／插件／HERMES_HOME／仓库cwd；接收通用Metadata，调用方提供来源。metadata owner先实施独立工具和受控验证，Provider新路径精确英文已获PI-26批准并实施；v4已正式加载，B唯一模型apply及独立GET准确Metadata通过。此修订替换下面旧helper路径准备，不重开已完成测试。

用户明确更正“归档”为“NM Thread同步”。不一致时的最终行为改为自动分叉接续，原安全暂停作为无法确认锚点/写入结果时的降级，不再把成功分叉后的暂停提示作为单独目标。

| 任务 / Owner | 范围与依赖 | 完成判据 |
|---|---|---|
| NM原生消息身份契约 / nm_thread_native_ids 6.1/high | 只读官方CLI/一级文档；必要时限已有合成Thread核ID，不写NM | 确认原生Message ID读取/稳定性与CLI接口，不伪造ID，集中交接实现者 |
| 自动分叉接续 / nm_thread_fork_impl 6.1/high | 个人插件同步/receipt/client和必要受控测试；禁止动任何Provider Prompt常量、Memory helper及主仓生产代码 | 首条引用旧NM Thread＋最后共同NM Message ID；第二条起差异后缀；后续/冷恢复/再分叉/并发/unknown/profile隔离；不重复共同前缀、不覆盖删除旧Thread |
| 真实带Metadata创建 / metadata_live_acceptance＋root薄UI | 先准备；用户审批英文原文及root统一加载/release后才跑，旧失败对象保留 | Hermes模型实际调用专用入口，一次新合成Memory创建，官方同ID回读核正文/标签/Space及来源Metadata；失败保留不重试，资源回收 |
| Provider一句原文 / root | PI-26精确英文已批准，已仅替换此前长句；v4正式安装加载 | 仅落实用户批准的精确英文句，不改其它无关提示；不引入Skill |

子Agent禁止流水账和派生，整包交回；禁止任何显示变化，UI仅root自己的隐藏IAB。前序证据不重跑，原PI-23三类模型偏差不设新增阻塞。

### v4实际编辑发现：E04历史显示分支一致性

root经隐藏IAB对A正式Reply→Rewind and edit→Rewind and send后，NM同步canonical清洗路径6条、新NM Thread3条／22项对账通过；但同页及reload冷页仍显示退出当前分支的旧批准／assistant，再追加新UA。正式REST include_compacted=true返回旧两项active=0/compacted=1，故不是仅warm缓存推测。既有compaction历史应保留，rewind退出分支的尾部不应混入当前显示；由local_deployment_browser_validation先只读定位最小修补范围，root亲审后接线。关闭需正式History分支过滤契约／针对性负例、原A冷UI不含旧尾部且保留共同前缀与新UA。不得借此改用户表现层、重试Memory写入或重复100k旅程。
