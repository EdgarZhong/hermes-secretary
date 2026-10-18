# 云部署实施计划

## 1. 目标与依据

按Snapshot Index D01–D15将已验软件、本轮Provider可选配置/图标增量及用户定案身份部署至现有Ubuntu；核心是原生双Profile、正确模型/MCP、完整Pi历史、同源双SPA与可靠同步。原v5固定软件门禁不重开；新增源码/部署配置和实际用户入口另作独立审查与验收。所有权威新增决定先落索引，最终源码/产物逐一绑定。

## 2. 覆盖与任务

| 要求 | 工作与owner | 白名单/依赖 | 完成条件与验证 |
|---|---|---|---|
| D01–03/05–09 | 云Core/PM、Homes、模型、MCP、历史cwd与systemd/反代，cloud_deployment_preflight后续执行 | 云新Core/Homes/sharedcwd/专属unit和新反代；保护旧服务，依赖root批准源/产物/SOUL | 精确SOUL SHA、数据库原身份/来源对账；原生配置与真实模型；MCP tools list；回环双SPA/REST/WS/状态完整 |
| D04 | study_thread_space_split | 个人Provider/测试/文档，新study Home安装；禁止SOUL/DB | 21不同定向节点、未配兼容；study无override，本Space保持；源commit和安装字节绑定 |
| D10 | deployment_ui_alias_build | UI四窄文件，保护用户overlay；静态双dist | 37不同定向节点/typecheck/build，完整build输入与产物清单，窄提交不夹带用户UI |
| D02/数据重要 | Mutagen/SQLite快照，独立执行包 | workspace双向、配置SOULallowlist双向、完成DB快照单向；同步外已验两槽 | 不覆盖liveDB/WAL；真实allowlist/方向/传输、半包保护和恢复验证；每300秒，Mac离线独立运行，实际本机冷state.db接收 |
| D11 | 新hostname DNS/Tunnel入口，云执行者 | /etc/cloudflared实际配置仅增新host；旧四入口不变 | 配置校验及安全原生服务；先检查Access存在，未保护不发布业务路由，明确交接 |
| 全部 | root集成＋独立Verification Astra/high＋独立Validation6.1/high | 本轮冻结版本/全部实际证据；UI只root隐藏IAB | 先独立要求判据后核真实源/配置/产物；真实浏览器/Profile/模型/MCP/历史/同步代表用户结果，不重复大套 |

## 3. 当前状态与编排

用户优先级已更新：云服务先上线供其访问，同步与审查报告继续并行收尾，不把这些作为服务启动前置。Access匿名302已核；旧Pi Mutagen允许关闭清除，但仅最后执行。

Preflight已核Ubuntu/root/20GiB空闲，云所有新目录无覆盖；精确Kimi Code目录200与既有MCP/NM可用。Profile/模型原生接线已定位。个人Provider源码/新study安装已交；UI新产物已交、四窄文件提交d5b20aab已同步。root封存用户SOUL和整体配置口径，冻结后并行Core部署与同步实施，接口以明确完成文件为交接，不流水账。

## 4. 缺陷、取舍与快照

只做新增部署所需最小增量；已有全量不绿及模型观察沿v5原边界，不伪通过。Access未覆盖或DNS凭据缺失是真实交接条件，不试错重配其它服务；SOUL用户原文优先，不擅自修人格。故障回滚仅本轮新服务/配置，保存原服务和已有数据。每轮实际失败与重试保留；凭据只在受限本机/云文件，不进入公开报告。最终源/配置/产物/真实运行绑定见ignored deployment-release-20261019，各门禁报告独立维护。

## 5. 实装交接（2026-10-19）

服务与首次K3真实回复已运行；云完整PM/单进程/双SPA/两WS/历史迁移和精确自有Runtime收据已root接收。同步helper19节点/源码及实装包已亲审，配置8文件、数据库1完成包lane与云/本机300秒周期已接通并落三库；隔离暂停接收→云继续发布→恢复追上通过。workspace仍被macOS Desktop TCC权限拦住，已请求用户手动允许，绝不代点/绕过/改路径。原独立两门禁报告保留该时点D02/D11缺证；后续D15实测及清理如下，不冒称全轮PASS，不以此关闭站点。

## 6. D15最终实测及交接

root沿用户窄授权的现成受信任Chrome完成真实公网Secretary与Dashboard访问；Alex新DeepSeek Conversation完成7次API/12次工具只读自查，20条历史保留；原K3默认/high未变。两自有Chrome页及精确测试Runtime已关闭，用户原三页/云服务保留。旧Pi五条同步配置备份后精确终止，仅新三条保留。该顺序遵循最新D15，不把之前Agent制定的workspace全通过前置作为新用户审批门禁。

| 剩余/发现 | Owner与状态 | 完成条件及边界 |
|---|---|---|
| Desktop workspace双向往返/marker | 用户系统授权→root；外部权限未解除 | 接续现有精确session，双向到达并清理自有marker；不代点/绕TCC/换路径，不重建三lane |
| Kimi Search/Fetch业务408/403/404 | 只读诊断已交接，业务未通过 | 换目标/既有代理无改善；不可假称鉴权/额度/路径细因已定位，未盲改接口/Key/代理或扩开发 |
| 单次NM自动Recall超时 | 只读诊断已完成，保留真实降级 | 默认2秒超时；同环境一次CLI0.562秒成功，仅证明当前可用，未调预算或宣称原请求应命中 |

新原件入口为ignored `deployment-release-20261019/final-acceptance-20261019/{browser,ops,nm-diagnosis}/`；root亲审实际参数/原件，不采信模型自报、不重新运行有效旧测试。无在途实现Agent，完整同步及独立门禁仍未全部关闭；停止扩展工作并如实交接。
