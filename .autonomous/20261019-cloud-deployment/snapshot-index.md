# 20261019-cloud-deployment · 云部署要求索引

## 1. 审查依据索引

| 类别 | 文件/原文 | 权限与范围 |
|---|---|---|
| 用户需求 | 本索引§2逐条摘录当前用户指令；最终SOUL见ignored deployment-release-20261019/soul-final-manifest.private.json所列两原件 | 用户定案SOUL本轮不改，完整私人正文不入Git |
| 权威规格 | docs/cloud-deployment-sop.md；docs/06-Hermes-Secretary-Web-UI-V1-Spec.md §0.7–0.8；docs/08-profile-scheduler-files-clarification.md | 二级，按本轮最新用户决定覆盖旧筹备状态，固定v5历史结论不回改 |
| 编码指导 | AGENTS.md；个人仓AGENTS；UI仓AGENTS | 二级，显示/凭据/用户UI保护/原生兼容与既有检查不变 |
| 会话确认 | 本索引§2 D01–D12 | 二级，后续明确用户变更追加，不冒称root推断为用户原话 |

## 2. 口径与决策

| ID | 用户明确要求、完成判据及边界 |
|---|---|
| D01 | “两份SOUL已编辑好，开始部署”。本机Alex/study SOUL原文上传，字节SHA分别f260652e36b478687605721d8b7850a0a057769cc36aefb0aa1856e0129d56f1、8d88f3c9abea47dcc020245924be2862d87037c96bc29650ade32edd60a0148d；不得重写、格式化或添加测试身份。 |
| D02 | 云Core ~/hermes-secretary；物理Home ~/.hermes_profiles/Alex、study；两者共用 ~/workspace（单数），本机~/Desktop/Alex与之Mutagen同步；本机~/.hermes_profiles与云同名根建立配置/SOUL及DB快照同步。 |
| D03 | “从Pi导入的数据库作为主助手的”。Alex使用48会话/6065消息当前schema副本；保留原库、消息身份/来源/Ref/UID/root/binding。study新库，不导入合成测试数据。原生workspace.move统一运行cwd，原Mac cwd仍留origin_json。 |
| D04 | “保留同步目标拆分功能，但study先不往Default同步，改回自己的space”。可选thread_sync_space保留，study不配覆盖，读取/上下文及自动Thread仍考研Space；不迁旧NM对象。 |
| D05 | “Study profile先不设置默认模型”。其Home不写model默认，不通过clone混入Alex默认或DeepSeek测试model。 |
| D06 | Alex复用云已有Kimi Code套餐Key，必须是原生kimi-coding而非Moonshot平台API/custom；默认独立k3-256k型号，不是k3加窗口覆盖，thinking high。目录已核该型号262144窗口；实际部署仍需正式运行证明。 |
| D07 | DeepSeek作为Alex可选模型、不作为默认；用户明确允许本机DS Key上云。其余秘密不入Git/输出，云Kimi/MCP/NM凭据云内复用，不回传。 |
| D08 | Alex接云已有MCP，至少Kimi Search/Fetch与飞书Notifier；保留其原命令/参数/环境语义，只接入/探测不因此给他人发送消息。 |
| D09 | “上下文节省打开，空闲500秒，阈值128K”；用户随后“考研助手先不用配置”。仅Alex联合Idle Compact+Noting开启，study保持Noting既有开启但不加联合Idle新参数。按模型窗口单位128K=131072 tokens工程落值；原生压缩保留，不能启冲突idle机制。 |
| D10 | 前端只上传构建产物，不上传独立UI源码仓；Alex复用既有主头像、study复用复习图标，首页显示Alex但native canonical owner为alex；用户现有UIUX/Pin/布局/滚动和未提交表现层保护。 |
| D11 | 用户选hermes.edgarzhong.fyi，/与/dashboard同域同backend。Cloudflare Access沿用户自行配置安排，保留原Tunnel四入口/服务，不把未保护的原生machine-token入口公开；若Access未生效，先完成回环及安全占位，明确尚缺用户配置。 |
| D12 | 仍仅允许隐藏Codex IAB验收、禁止任何桌面/外部浏览器/open/显示状态改变；SSH及cloudflared须禁止拉起浏览器。部署和验证不重跑固定v5昂贵套或已有100k/600秒旅程，隔离新增真实输入并精确回收自有资源。 |

未决：数据库快照频率已向用户异步询问5/10/30分钟，未答不擅自设周期。公网Access是否已覆盖该hostname须实际检查，不修改其策略。正式DNS/Tunnel/系统服务/Mutagen在本轮部署授权内；保护现有服务及已有同步会话。固定v5产品两门禁作为不变接缝证据，不代签本轮云配置和新增代码。只有独立Verification用Astra/high，其余6.1/high，不派生子Agent。
