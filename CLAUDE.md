# V1.5 暂停基线与接续看板

## 当前状态与恢复条件

2026-10-09 用户明确要求停止代码变更及继续验收，仅撤销刚刚口径偏离造成的 App Server 兼容改造、同步新口径、整理提交基线和详细交接。自主目标状态为 **paused**，V1.5 **未完成、未通过独立验收**。只有用户明确恢复实现后才能启动下面任务；本次收尾不运行模型、测试、扩大门禁或浏览器验收。

- 本轮权威索引：[index.md](.autonomous/20261009-v1.5-implementation/index.md)，snapshot-index.md 为同正文链接；C05–C10 是最新用户口径。
- 最新规格：[04](docs/04-hermes-secretary-v1.5-implementation-spec.md)；未修订契约沿用[02](docs/02-noting-system-specification.md)。原附件原样保留于 d5acc2cc27c6053ff198448fa3502bd8dd47e415 历史树，不追改首轮报告。
- 原代码起点：main / 41f7057a28f8e9bf2fc6c8fb769748d9f2534012；产品承接 7533173ca315d6308b121d313f0dd281777c8604。
- 原文档冻结：d5acc2cc27c6053ff198448fa3502bd8dd47e415；计划基线：5dc152f0dfa4086134a79e6366bfbcc1d615784a。暂停现状快照：b0f260afe1a4e09f86725d800b109939953e45b2，完整哈希另见本轮 baseline.txt；快照包含此前保留的普通路径实现与本次文档修订，不能当最终发布版本。
- 环境：macOS，官方PM工作区 .venv Python3.14.7，现有pyproject/uv.lock未修改。测试与未来运行状态仅限ignored .hermes-dev隔离目录。

## 最新口径与代码实际差距

1. **冻结父前缀始终存在（C05）**：同一个Noting Task每次实际模型请求、工具循环和continuation均保留触发时冻结的Parent root与截至Anchor的Active消息序列；只能累加Noting自有后缀，不能换成实时Parent历史。父前缀不复制到child持久转录。
2. **工具面从task起收窄（C06）**：`<noting-task>`说明工具面变更；首个及以后请求的真实Schema和dispatch只限session_history、notebook_show、notebook_mutate，特殊NOTING_WITH_COMPACTION另有compact_parent。保留原role=user控制载体，不新增第二root。**当前保留代码仍沿旧首请求Parent工具面、响应后加维护工具的方式；新收窄要求仅已落实文档，尚未实现。**
3. **模型通道（C07/C09）**：项目Main、Noting及后续真实验收统一DeepSeek官方Anthropic接口 https://api.deepseek.com/anthropic，deepseek-flash思考模式；不使用Codex App Server或Codex Proxy，不自动fallback到它们。用户授权从 /Users/edgar/code/Ebbinghaus-v2/.env.personal.local 读取DEEPSEEK_API_KEY。仅确认该变量非空，**未复制凭据、未验证有效性、未切换runtime配置、未调用DeepSeek**。密钥只能进入隔离配置或正常秘密读取，不进Git/报告。
4. **缓存证据（C08）**：使用Hermes自己的真实request/response日志或获授权抓包逐次查冻结前缀和provider缓存读取tokens；字节一致、缓存命中量和效果分别报告。**当前没有这条真实Noting缓存核验结果**；Codex App Server日志不得作为证据。
5. **停止边界（C10）**：本次仅文档、撤销偏离和本地现状快照；全部后续实施/验收保持暂停。

## 已保留的实现、接收与证据

| 分区 | 保留事实 | 已取得证据与边界 |
|---|---|---|
| T0/T2普通provider | 精确回退首轮混合SECRETARY_GUIDANCE；独立A1/A2、Main资格、global/local读门禁、Warm/Cold/pinned同步、正式dispatch及actual request capture | Prompt报告 .hermes-dev/evidence/v1.5/prompt/return-report.md；定向101/89/23/3项通过，有重叠不可相加；11文件ruff/health通过。主会话review已接管，未宣称全轮完成 |
| T1 Foreground/History | 唯一latest Prelude、actual root与native cached root隔离、canonical identity read、真实System History、Full消费者；branch压缩与carried/late Force反例窄修 | foreground/report.md；清理前最终7文件106项通过、11文件ruff/health通过；本次撤销Codex partial字段及专项测试后未复测，历史计数不能作为暂停版本的新结果；反例日志保留。主会话已核对核心机制，独立门禁未开始 |
| T3 Slash/Proposal/Schedule | /notebook展示、/noting局部反馈、共享CLI/Gateway/TUI/compute-host接线；提案不预拼源原文、附录C自主搜证；Candidate/Schedule两句与expression五类 | workflow/report.md；52个不同定向tests通过；主会话集中review。真实Candidate→搜证→修订→批准→归档未验收 |
| 主会话微小集成修补 | Gateway命令与反馈捕获同一Session，防路由变化写到新Conversation | workflow/route-move-before-fix.log真实失败；after-fix整文件4项通过；没有扩大路由框架 |
| 历史真实模型核验 | Codex Proxy/gpt-6-luna-high/chat_completions五lane实际请求完成：global_on/local_off/global_off/cold_off/global_on_again；Full来源一致 | integration/real-main.log/json/audit.txt仅证明当时provider及工作区；不能证明DeepSeek已通过，也不是Dashboard验收或Noting缓存命中证据 |

所有本轮证据在ignored .hermes-dev/evidence/v1.5/中，不包含于提交；跨版本只按实际变更范围复用，不复跑有效结果充当review。

## 已消除的偏离影响

- 撤销T2b及Codex Noting协议研究，不再作为本轮实现依赖或验收阻断。
- agent/codex_runtime.py、agent/transports/codex_app_server.py、codex_app_server_session.py、hermes_tools_mcp_server.py已恢复5dc152f前本轮未改版本；tests/agent/test_codex_secretary_transport.py已移除。另撤销Foreground仅为Codex RPC增加的partial_context参数/字段/返回投影及专门Codex Prelude测试；通用missing/source审计保留。只撤销本轮误加兼容改动，不删除既有上游可选实现。
- 本地备份仅在 .hermes-dev/evidence/v1.5/retired-codex/t2b-uncommitted.patch 与兼容测试副本，供审计，不是接续任务。
- 9139原隔离Dashboard目前无监听，先前exec句柄已不存在；不启动新服务、不继续用户场景。内置浏览器仅完成运行库准备，未执行本轮Dashboard验收。
- 三实现Agent目前无继续执行任务；此前prompt/workflow因usage限制中断，不把T2b未交回内容称为完成。

## 详细接续任务看板（全部暂停，需用户恢复）

| 顺序/任务 | 范围、负责人和修改边界 | 依赖与实施步骤 | 完成与验证条件 |
|---|---|---|---|
| H0 恢复依据与状态 | 主会话；根CLAUDE及本轮索引/计划 | 读取AGENTS/CLAUDE/index/baseline/01/02/04和自主套件；核对暂停快照、工作区、实际锁文件、Agent可用性。C05–C10覆盖旧工具parity/provider表述；不恢复T2b | 现行口径与保留实现差距明确，分派行号重新核对，无未授权规则/范围变化 |
| H1 Noting实际工具面收敛 | 新实现Agent gpt-6.1-sol/high；secretary/noting_child.py、noting_tools.py及必要agent/turn_request_assembly.py/turn_api_call.py窄接线；对应tests/secretary/test_noting_child.py和tests/agent/test_cache_parity.py，根文档由主会话负责 | 沿原构造/Notebook work初始化设置profile工具面，首请求即session_history/notebook_show/notebook_mutate，special另compact_parent；移除旧first-response扩工具假设与陈旧pin回流。task消息明确变更，保留Candidate/Schedule指导、root/消息冻结、原child/Trigger/commit机制 | 每次实际request均无fs/Web/Memory/Skill/普通Cron/delegation工具；dispatch负例拒绝；普通/特殊profile、重试、工具循环、continuation不扩大工具面。不改Main工具或全局原生Loop |
| H2 全生命周期父前缀 | H1同Agent或非重叠独立Agent；既有freeze/child循环及测试，深入范围先明确白名单 | 确认Parent root/到Anchor消息在首次、多个tool request、同child continuation均不变；Parent并发追加、global切换、Parent压缩不刷新已冻结task前缀；仅child suffix持久化；不得重扫描全History重建Active | 实际provider kwargs与冻结源比较、每次prefix hash/内容一致；异步/Anchor失效原规则仍有效，child不自行压缩。不能只测第一次或仅查看对象属性 |
| H3 DeepSeek隔离配置与实际适配 | 主会话环境接线；需要深入adapter修复则新Agent白名单；只读Ebbinghaus-v2指定环境文件 | 使用官方Anthropic endpoint、deepseek-flash思考模式；凭据不输出，原生atomic config/secret读取；移除隔离runtime中的codexproxy/fallback。核对官方当时模型上下文及思考/工具协议，用Hermes native resolved window/threshold避免Force capability误判，不扩大例外或新增能力失败条件 | 真实请求URL/协议/model/thinking确认；一次正常回复和多轮tool思考块回传成功，credentials仅到官方域名；无Codex App Server进程/Proxy调用。实际配置、reasoning/上下文与参数取证，不虚报已切换 |
| H4 Hermes缓存核验 | 主会话统一真实取证，必要实现Agent只在既有observability接缝；证据落integration/cache/ | H1–H3后跑真实Main→Noting→Notebook/Snapshot；在Hermes request/response层记录task/child/request关联、root/父messages指纹、实际tools、suffix长度和provider usage.cache_read/cache_creation字段。取样首次、后续工具请求、continuation及Parent并发继续；无新日志框架或第二缓存管理器 | 逐次说明父前缀是否保持、cache read实际值及可观测边界；0命中/字段不可用也诚实记录并诊断，不能用Prompt字节一致替代缓存证据。只捕获本隔离流量，屏蔽认证头，Codex日志不参与 |
| H5 接收集成与定向证据 | 主会话亲自review、微小接线；深入修复重新分派 | 接收七项报告、正式请求/权限/状态/失败与上下游；同时对本次Foreground兼容字段清理做必要定向复测，然后按DeepSeek重新验证global on↔off、local schema稳定、Warm/Cold/pinned、Full latestsource。更新README稳定事实、CLAUDE状态，创建明确待审提交 | 新口径代码与文档一致；未改V1未修订机制；凭据/个人内容不进Git；版本与证据匹配，不用反复复跑已有tests代替review |
| H6 一次必要扩大回归+独立Verification | 全新fork_turns=none reviewer；产品只读，仅verification.md与证据；主会话统一安排测试执行方 | H5收敛后按冻结输入独立重新提取V1未改要求+M01–M25+C05–C10；统一一次10类检查及实际影响的Secretary/Agent/State/Gateway/CLI/TUI/History分区、必要共享catalog验证；不无差别重测无关能力 | 六节完整矩阵与原文→路径→条件→方法→观察→判定闭环，无违规/证据不足；macOS边界明确。已知失败与新回归区分；修复仅定向复测，不能关闭规则让结果变绿 |
| H7 官方Dashboard独立Validation | 另一个全新fork_turns=none validator；产品只读，validation.md与隔离runtime/证据 | H6通过后先写场景供主会话过目，再用官方Dashboard+localhost native gateway+真实DeepSeek Main/Noting操作：跨compaction查原文、global/local/cold、真实Candidate自主搜证/后续更正、修订不写、明确批准限定写、Noting归档、Schedule idle/busy、Full Prelude/身份/Anchor审计 | 全部适用用户场景真实输入到输出通过，保留失败序列；构建/CLI/mock不替代，平台未测不冒称；无个人UI/新API/云部署 |
| H8 交付判定 | 主会话delivery-evidence-review；根状态及新轮次final-delivery | 两独立门禁关闭、范围内整改清空、最新版本无新增必要缺口；对照本轮暂停历史与新轮次原始要求 | 才能标goal complete并交付实际commit/证据；未关闭继续修复，不以阶段测试通过替代整体完成 |

恢复实现时按autonomous-run建立新的接续轮次索引，引用本暂停快照、原始d5acc及C05–C10；保留本轮暂停交付和历史结论，不追改为后来已通过。

## 已知验证边界

- 本轮独立Verification、Validation均未启动；唯一扩大检查尚未执行。恢复后按H6/H7统一安排，不先跑大型检查“建立基线”。
- 首轮7533173审查101条：98符合、2违规对应Full root provenance、1本机平台不适用；不是本轮通过声明。
- 首轮扩大suite在6a75369：13,318通过、117失败、109跳过，后续定向修复，未重跑整套；无全suite全绿结论。
- 平台只实测macOS，Linux/Windows未实测。真实cache hit未测，DeepSeek未调用。本次Foreground兼容字段清理未复测，隔离旧DB可能保留unused nullable列，新捕获采用显式列名不要求迁移；恢复后只定向核实。当前代码不满足最新Noting工具面要求，不能以旧测试绿代替H1/H2。
- 本次不push、不部署、不发布、不复制或提交凭据；自主目标暂停，下一步只等用户恢复。
