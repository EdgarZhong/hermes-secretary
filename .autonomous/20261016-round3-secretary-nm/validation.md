# Validation：20261016-round3-secretary-nm

## 1. 结果概览

本文件由主会话依据 R3-017 制定；执行者为全新、无主会话上下文的 GPT-6.1 Sol / high，必须在 Verification 关闭后才执行。当前状态：**计划已制定，全部场景未执行，门禁未关闭**。执行者填充实测版本、时间、证据与结论，不修改判据迎合实现。发现遗漏的适用场景先记录并通知主会话补入，不自行缩减。

依据：本轮 snapshot-index.md、baseline.txt；公开冻结 d19018a7ba3e38ae01f76aa57821b55cbc15ff58 的白板全文（含 types/scenarios）和 07；旧 01/02/04/06 仅继承索引明确保留条款；个人 Provider 97078118287bcd41ba8b02aa5a3a108c5026f7af 的 PHASE3 现行 §1–7。R3-016～018补充执行授权、模型与 round3 profile。待验双仓 SHA、Verification 版本、公开操作入口由主会话集成收敛后填写。

范围是本地公开核心及独立个人 Provider fixture 接线；UI 改版、正式云端部署、真实 NM Memory/Thread/Space 写入不在本轮授权内。provenance 小脚本只复核已有基本模拟调用证据，不重复严格验收或官方 CLI 通用测试。

## 2. 环境与准备

- 所有真实产品运行、DeepSeek 模型复测及本验收统一使用仓内 `round3` 隔离 profile：`.hermes-dev/round3-runtime/profiles/round3`。启动包装器为 `.hermes-dev/round3-local-20261017-l0/run-native.py`；它只在内存读获授权本地密钥，不打印密钥，不接 App Server/Proxy。
- 官方 PM `.venv`、现有锁不变；macOS arm64。模型走 Hermes 原生 custom / chat_completions / DeepSeek。执行时记录实际模型、API、推理设置和请求/响应证据，不以配置存在冒充联通。
- 使用原生 CLI 或既有 TUI Gateway RPC：创建/恢复/输入、slash、压缩、rewind/fork；无须启用后置的新 UI。执行者写明实际入口与可重复命令。若不能通过这些入口完成必要用户操作，记录阻断，不能直接调用内部 helper 冒充端到端结果。
- 各场景使用 round3 中不同 Conversation；有状态依赖时继续同一 Conversation。需要干净状态时先保留脱敏证据，再使用新 Conversation 或重建测试库，不连接用户真实状态。后台任务、RPC和子进程均绑定 round3。
- 个人 Provider 的网络只指向本机隔离 HTTP fixture，服务记录与 ACK 供观察；不得连接真实 NM。其端到端接线可使用同一 round3 profile 的受控配置阶段，执行后恢复公共配置，避免污染公共模型证据。若已有效开发证据覆盖真实 host→fixture 链路，引用同版本证据，明确它不证明真实 NM 服务可用。
- 证据集中于 ignored `.hermes-dev/round3-runtime/evidence/validation/`，只在报告保留摘要/路径/版本/时间。不输出密钥和完整私人上下文。数据库只含本轮合成数据。
- 本验收不重跑大型 suite。并发时序、强制 overflow、External 模拟等机制证据可引用同版本开发报告；模型行为、结构化工具可调用性、用户恢复结果须有实际产品入口证据。

## 3. 用户目标与场景覆盖

| 目标编号及冻结依据 | 完整场景编号 | 场景类型与起点 | 数据/顺序选择依据 | 当前执行结果 |
|---|---|---|---|---|
| G01 Main 三能力独立，07 §3/6.3/8.2，04 §3 | V01 | 新建、warm与cold恢复 | noting/scheduler四组合；local参与独立 | 未执行 |
| G02 持续对话原文取证，07 §5/8.4/8.8 | V02 | 同Conversation跨压缩→读取 | 中文短词、精确身份、邻域、时间与真实纠正 | 未执行 |
| G03 跨Conversation授权取证，07 §5 | V03 | new/fork/rewind后搜索 | 默认当前与显式跨域；合法fork源、失效父路径 | 未执行 |
| G04 Notebook语义整理，白板C/L/E与07 §4/8.11 | V04 | 真实多Turn材料→手动联合整理 | 七类型、candidate、用户认可与AI建议区分 | 未执行 |
| G05 持久child与前缀，07 §3.2/8.11–12，04 §4.4/4.6 | V05 | 真实child工具循环和续跑 | 四工具结构调用、父多模态、5Turn/overflow | 未执行 |
| G06 四入口、D01与原生压缩，07 §8.1/11.1，04 §4.5 | V06 | auto/manual/Force/Idle | 同区间去重、成功边界、External拒Noting | 未执行 |
| G07 Snapshot发布与恢复，07 §3.1/8.13 | V07 | 合法异步完成与pointer变化 | 晚到/忙碌/压缩fence；完整正文、无额外Turn | 未执行 |
| G08 提案与批准边界，白板L/F与07 §8.10/8.13 | V08 | /propose-persistence及超限通知 | 等于/超过、延期/纠正、部分成功不全结算 | 未执行 |
| G09 自主登记与独立排期，07 §6/8.6/8.9 | V09 | 用户未来需求→Schedule Table | instant/deferred、中文意图、Cron分流 | 未执行 |
| G10 提醒可达与ACK，07 §6.2/8.14，02 §3.10–12 | V10 | 到期idle/busy、多条deferred | 同批载体、失败重试、实际携带响应、迟到 | 未执行 |
| G11 修改撤销与恢复，07 §6.2/8.14 | V11 | pending后更新/暂停/删除→恢复 | 接纳前撤销与接纳后在途、重启、24h notice | 未执行 |
| G12 通用原生不变量与旧面退出，07 §7/9.1 | V12 | 辅助runtime、关闭、历史旧工具 | 无新权限、legacy明确失败、预算真实反馈 | 未执行 |
| G13 个人Bundle与Recall，PHASE3 §2–3/6 | V13 | Main/cold/compaction与fixture | 稳定root、短CJK、离线无旧指针、恶意标题 | 未执行 |
| G14 completed归档，PHASE3 §2/5 | V14 | Main/Cron成功失败、续接/rewind | host完成gate、脱敏、ACK suffix、分歧停止 | 未执行 |
| G15 窄provenance接线，PHASE3 §4.1及R3-010 | V15 | 已有基本模拟调用证据 | 官方CLI真ID→仅补Metadata；partial不重建 | 未执行 |

场景是完整用户目标的分组，不表示每组只有一次调用。实际执行记录须区分表内行为不同的分支；等价数据可复用，不得用一个成功样例代表所有失败与恢复分支。异常时序优先引用正式路径受控证据，用户观察与恢复仍记录实际结果。没有真实服务授权的个人线限制必须保留。

## 4. 详细场景与执行结果

所有场景执行前统一记录：双仓 SHA、round3 配置摘要、起点 Conversation Ref/物理 Session、历史准备来源。执行后逐项追加实际输入/完整操作/输出和状态/证据时间路径/结论及偏差。以下为主会话批准的输入与预期，当前全部未执行。

### V01 三能力开关与恢复
通过原生配置和会话入口依次操作 noting/scheduler 四组合；同一 warm Conversation 下一Turn请求观察Schema、Prompt与dispatch，再cold恢复；用 `/noting off`、`/notebook`、`/noting on`检查局部参与。预期：合格Main始终History；Notebook只按global；Scheduler独立；local不重建root、不取消Schedule；坏配置只关对应功能并具体说明修法，旧key明确报错不迁移。与原生idle compaction互斥按现行契约反馈。辅助runtime不从此获得Main权限。

### V02 跨压缩原文与身份
用户依次说“项目代号是青鹭，截止周五”“纠正：截止周六，尚未承诺今晚提交”；完成真实压缩后要求查证原话与纠正，使用返回的Message Identity继续read邻域。预期跨压缩原文可读，锚点必达，身份不是物理row/session；时间边界按消息时间，中文短词可搜，空结果与不完整/错误区分。不得读Prelude或把压缩scaffold当原话。大结果的Noting反馈引用V12机制证据。

### V03 跨域与路径变化
创建第二Conversation放置独特合成短语；当前默认search不得泄漏它，显式cross_search才可定位。对第一Conversation执行真实fork并在父侧rewind/edit，沿fork读合法继承源，再在父侧查询失效段。预期fork拥有新ref但保留合法原文；无效父路径排除；辅助/未知目标不泄露存在性；new/reset不承袭旧Conversation身份。

### V04 真实模型整理语义
输入一组连贯合成材料：周末探访安排及一个已委派行动；亲属处境与尚缺的具体信息；用户提出的一个问题、一条带“可能”的认识和明确决定；一个AI建议明确被用户否决。经正式manual联合入口启动Noting，观察实际四工具调用与提交。预期七类型按需要而非凑数建立，gap附情景、不编动机/结论；AI建议不写成用户确认；来源完整、candidate聚合引用不搬走源。继续输入纠正、完成证据和部分交接，再整理，检查稳定entry与版本、no-op不续期、数组替换及归档引用无悬空。真实非确定性语义按证据支持范围判断，不要求模型逐字复现测试文案。

### V05 child执行、结束与缓存前缀
用正式父runtime启动持久Noting child，保留模型真实请求序列，至少覆盖工具循环及同child续Turn。父消息包含一个可由原生路径承载的合成图片块；对比每次请求root/tools/messages完整冻结前缀，后缀完整声明四工具；验证模型能结构化调用新工具并实际dispatch。继承schema中的父工具不授执行权。finish与其他工具混批必须整批拒执行；独立finish成功后冻结工作态，原生Turn返回才提交。五Turn/overflow强制有效提交、失败/中断不提交可引用同版本正式runner证据。实际cache-hit仅按provider响应/log记录，字节相同不冒称缓存命中。

### V06 联合触发与区间
在round3配置合法窗口/阈值，分别经原生手动、自动压力、Force及Idle触发。观察冻结在压缩之前，父压缩无需等待child；Force占用后同区间换Anchor、结束/失败/rewind不再启动，真实成功压缩新区间才可新启动。Idle要同时满足Main空闲delay与实际token，新Main Turn取消等待。External来源真实派发标记的受控证据覆盖所有入口：只拒Noting，无freeze/admission副作用且通知抑制正确；原生必要压缩、History/Scheduler仍工作。native/unknown不新增拒绝。失败/no-op压缩不退休Force notice。

### V07 完整Snapshot通知
通过合法后台整理并在父会话继续活动，观察完成时一条Framework含完整已提交payload及结束信息，不启动新Turn；忙碌时在Turn结束的durable tail出现，cold恢复仍可读取已落库正文。受控正式路径证据覆盖B先完成A晚到、A排队后B生效、pointer核对与append竞争、压缩fence；旧提交仅审计、不发过期正文或Proposal。rewind选pointer不凭空发完成通知，Scheduler不被重选改变。

### V08 提案与结算
以V04合法candidate调用 `/propose-persistence`，另以隔离配置降低提案阈值产生真实超限通知；边界等于不触发、大于才触发可引用计数机制证据。预期同一共用指令、完整正文，不要求用户再次下命令；Main按需读原文，展示内容/目标/labels/provenance/entry-version；仅提案不调用目标写入。用户输入“先推迟”“只修改措辞”不作为批准。后续使用合成正常Conversation轨迹记录明确批准及部分成功/失败，下一Noting只结算成功覆盖，不恢复旧内容、不因降计数捏造或删除来源。不执行真实NM写入。

### V09 Scheduler用户登记
用户要求“稍后提醒我检查探访安排”，模型应当立即调用Scheduler确认真实登记，不依赖Notebook或Memo；选择instant与deferred并列表查看。关闭Noting后继续操作；切到明确独立Cron任务意图检查正确分流与原生工具未被全局覆写。表为空或未来24小时缺instant时工具notice供模型判断，不自动由代码补排期；用户明确关闭自主follow-up时不强推提醒。

### V10 到期与请求ACK
短时合成instant在idle时唤起同Conversation，busy时转pending deferred而非排第二Turn。两条deferred在真实Main请求前形成一条durable carrier，正文每项schedule_id/due_at/mode/content，deferred无timestamp；instant只在实际entry写一次timestamp。模型成功响应实际携带的请求才ACK。受控provider失败/空响应/载体未携带的正式路径证据应证明不吞pending；恢复后一条原载体可成功结算，不重复持久化。迟到once仍可投递。

### V11 改定义、在途与重启
pending后通过工具更新content/mode、改期、pause/delete；下一实际materialize必须用当前合法定义，旧witness不得落库。已admitted carrier后pause/delete保留在途结果，late ACK不复活排期；周期resume不无限回放，once消费后不重播。重启round3 runtime后读取持久Table/pending继续合法投递。instant最终投递与busy降级最终注入重算24h全表，混批只附一次，unknown不假称无覆盖；不因Notebook rewind/fork自动复制或重绑排期。

### V12 原生边界与旧工具退出
通过正式注册/dispatch证据核对Main三能力、Noting四工具和辅助runtime；对历史旧名执行应返回明确legacy_tool_removed与新工具引导，历史不删除/重放。单结果spill和批次总裁剪分别在真实executor路径构造：Noting History反馈先缩窗口，单条仍超限明确无法继续，不提示无权工具；其他runtime原生提示/预算/落盘不变。无个人Provider安装时核心能加载与运行。

### V13 个人Bundle与Recall
仅本机HTTP fixture：Main首次构造、cold恢复及compaction原生重建获取稳定Bundle（无Working Memory），连续Turn不每次重建root；有意义输入包括短CJK触发Memory Search指针（完整ID/标题/可得时间、不正文）。恶意标题编码为不可信数据。端点故障不得复用旧指针，保留不可用/Memory check短提示；History仍可用。Cron仅归档、Noting/其他辅助无独立Bundle/Recall网络；无模型工具Schema/第二同步插件。

### V14 completed归档与收据
公共真实host生命周期接本机fixture：completed且未failed/interrupted才sync；失败但有final_response不上传。跨压缩Main使用合法History及host批量egress脱敏；Cron仅自身合格正文。相同ACK前缀只上传suffix，失败不推进，重试可恢复；continuation同thread，new/fork分开。rewind/edit导致prefix差异返回reconciliation-required，不覆盖旧Thread/换ID。endpoint/Space隔离，无自动蒸馏或治理变更。引用开发44项时标明其真实SessionDB/MemoryManager与fixture范围；公共完成gate集成后受影响路径必须另有证据。

### V15 provenance小脚本
只审阅本轮P2基本模拟调用证据：参数数组调用官方CLI、解析真实ID、同配置仅补hermes_provenance并保留无关metadata；partial明确ID、修复不重新m add，unknown不猜ID。确认安装/skill指向新入口，其他管理回官方CLI。不重复真实NM写入、不把小脚本例外扩为整个Provider免验。

## 5. 问题、修复与复验

| 问题编号 | 场景及完整触发序列 | 预期/实际与证据 | 影响和状态 | 修复版本 | 原场景及受影响路径复验 |
|---|---|---|---|---|---|
| 无已观察问题 | 尚未开始执行 | 当前只是场景计划，不能推断无缺陷 | 门禁未关闭 | 未定 | 未执行 |

## 6. 验收结论与推荐复核

当前全部目标未执行；不得据本计划宣布通过。执行者逐目标填写结果与边界，所有适用场景有证据且缺陷关闭后才建议关闭Validation。最终是否完整完成第三轮由主会话结合Verification与实际代码版本决定。用户最终复核入口至少包括：同Conversation压缩后原文/Notebook连续性、Scheduler实际到期与取消、Persistence提案无越权、个人fixture归档证据；不推荐用户在真实NM服务执行测试写入。
