# 本轮实施计划：20261021-noting-kimi-chat

## 目标与依据

依据snapshot-index.md N01–N07与baseline.txt；遵从统一会话C08精简流程，不另起完整两门禁／重复大型测试。实现Noting自己的Kimi Chat动态声明接缝；真实短场景必须继承K3-256k/High完成maintain→finish→正式Snapshot提交。交付给“理解实验阶段一任务”统一暂存、提交、上线；本会话不SSH/部署。

## 覆盖与任务

| 要求 | 正式路径与任务 | 负责人及白名单 | 依赖／验证／场景／完成条件 |
|---|---|---|---|
| N01/N02/N06 | canonical schema→可信child边界→请求动态声明→原生SDK | noting_kimi_implementation：secretary/noting_request.py、noting_child.py必要marker、agent/turn_request_assembly.py及chat_completion_helpers.py必要接缝、新增tests | 父root/tools/prefix固定，声明续带且计量/审计；真实DB/AIAgent受控SDK工具/续Turn/summary/重试/权限及原生回归 |
| N03/N05 | 独立Profile虚构父Conversation→冻结→child→维护→finish→Commit Gate读回 | real_k3_short：仅ignored harness/evidence，产品源码只读 | 等实现亲审后运行真实模型；不改任务Prompt/tools/预算逼结果；保存精确route/wire/hash/usage/条目与来源/资源关闭 |
| N01/N04 | 默认＋已有Conversation持久路由、重建与重启交接 | xiao_beizi_kimi_anthropic：本地只读代码，ignored routing-handoff.md | 原生配置／RPC/control入口定位；不批改数据库、不假称改默认会切既有路由或复用跨协议缓存 |
| 全部 | 主会话亲审diff/正式路径/测试与真实证据、精确交接 | 主会话：本轮文档及微小接线修补 | 不复跑有效证据；范围内缺口整改；统一会话负责发布验证及线上健康 |

## 当前状态与编排

机制实现／正式接线／定向验证／真实用户结果均已完成；4产品+2测试文件已亲审并冻结，交统一会话提交部署。真实K3成功73.35秒／6API／1Turn，正式Snapshot3条，成功用量164333；首400失败原件保留且无usage。无文件白名单交叉；子Agent不提交、不再派生、不流水账。模型gpt-6.1-sol/high。显示保护沿N07，无UI必要。

## 缺陷与整改、取舍与快照

尚无已确认实现缺陷。真实K3/完整提交证据、默认及已存在Conversation的切换说明均是交接前必需，不能以小探针/静态helper通过替代。原失败任务不恢复，原测试证据不篡改。规则阈值冻结，index保持统一会话所有；本地日志ignored .hermes-dev/noting-kimi-chat-20261021/。

统一会话追加部署决定：仅Alex沿已有原生`save_env_value`/Profile scope配置`KIMI_BASE_URL=https://api.kimi.com/coding/v1`，配合model.api_mode/base、目标当前tip完整native route writer与正常重启；不扩大修通用pool/model picker。需持久.env→load_pool重播种→credential swap离线证据。此前仅model两叶足够的判断已由实际准备纠正，旧准备失败原件保留。

### D01 · 真实K3发现动态／顶层重名（已关闭）

2026-10-21真实短场景第1次HTTP400：父天然25 tools包含conversation_history，动态四schema又声明同名，Kimi明确拒绝。0工具执行/无Snapshot，1请求无usage不作零成本，子资源释放及父原文不变。实现者修为可信冻结父tool names差集，只追加缺少canonical工具，正文四工具与dispatch权限不变；无缺少工具不发空声明。定向覆盖父History/Show已有、无重名、多Turn/summary及正式commit后，主会话review再授权第二次真实短场景。失败原件real-short/run-20261021-011556/保留。

### 主会话与统一会话工程审查收窄

动态协议仅适配本轮已证实目标：原生kimi-coding及aliases、k3-256k、chat_completions、官方HTTPS api.kimi.com/coding/v1。未验证型号/其它Moonshot平台/同host custom或代理不自动启用，不新增全局开关。缺失工具schema按child冻结顶层tools差集，全部已有则不发空声明。原生fallback已强制重组装，主会话初步泄漏担忧经追线未证实；仅补正式Loop反证测试，不增加turn_api_request逻辑。

D01关闭：缺失schema去重及精确route门槛已亲审，39dynamic+4summary+3fallback不同场景分组通过；实际K3第2次6个HTTP200、3maintain、单独finish、唯一有效Snapshot提交，wire前缀/tools/声明固定，7受测产品hash一致。最终范围、历史失败及posthoc审计限制见final-delivery.md。统一会话已确认接收并准备提交／部署，源文件不再改动。
