# Snapshot Index：20261021-noting-kimi-chat

## 审查依据索引

| 输入类别 | 实际仓库文件路径或本文件位置 | 修改等级 |
|---|---|---|
| 用户需求 | 本索引“口径与决策”的逐字用户消息；docs/operations-log.md的2026-10-21历史实验与边界 | 二级 |
| 权威规格 | docs/07-scheduler-notebook-noting-compaction-redesign.md §3、§4.5、§7、§8.11–12、§9；docs/notebook-ontology-whiteboard.html内容语义；docs/04-hermes-secretary-v1.5-implementation-spec.md持久child/cache parity保留条款；docs/08-profile-scheduler-files-clarification.md模型/Profile归属 | 二级 |
| 编码指导 | AGENTS.md、README.md；分区AGENTS仅接口参考 | 二级 |
| 会话确认口径 | 本索引下表 | 二级 |

索引自身二级。计划、实现和证据三级；根CLAUDE为当前编排。白板/07/04不在本轮修改范围，既有Schema/Prompt/结束语义保持。按统一会话指挥复用其316637e基线及本索引最新用户口径，不等待单独冻结提交；用户在统一会话C08明确豁免严格套件，仍要求代码亲审、定向测试及真实K3短Noting。本会话禁止擅自暂存。

## 口径与决策

| 编号 | 用户意图／约束与完成标准 | 决策、理由与授权来源 |
|---|---|---|
| N01 | “我同意，把Kimi的实际API改成OpenAI compatible…找最小改造方案” | 用户2026-10-21最新协议授权覆盖此前禁切协议；复用原生kimi-coding配置api_mode=chat_completions和https://api.kimi.com/coding/v1，不新造／替换官方Provider |
| N02 | “我同意你的选择…完成你的工作” | 用户确认最小方案：动态工具声明属于自有Noting请求接缝；沿child已继承runtime/parity判断实际协议/provider，不重读live Parent/config；不扩公共adapter接口、DB或持久消息格式 |
| N03 | “交付之前构造一个真实短noting场景，继承实测K3-256k顺利完成工作” | 独立Profile/DB/cwd、虚构短会话、真实K3-256k/High、原生建父→冻结→child→工具往返→finish→Commit Gate，读回Snapshot与来源；保留实际wire/usage及父root/tools/Active前缀证据；不以仅返回tool_call冒充执行 |
| N04 | “现在听从另外一个active会话的指挥…交给另外一个会话统一上线部署” | “理解实验阶段一任务”统一协调、暂存/提交/验证与部署；本会话只交Noting包及精确默认/已有Conversation路由配置、宿主重启影响，无单独部署 |
| N05 | 本地代码、本地独立DB，不动云端、不从云端拷贝 | 本轮虚构内容无需复制生产库；API最小真实调用获授权，禁止SSH、云运行数据/配置修改、恢复旧failed任务 |
| N06 | 缓存／原生／权限不变量 | 父root、顶层tools、Active前缀固定，新工具只在child自有后缀声明，固定位置续带；计量/审计覆盖；不启用即原生、非Kimi/非Chat/普通Main不变、同步并发四工具权限与finish/forced/失败资源释放沿原机制 |
| N07 | 显示保护 | 不需UI；如需只可自己新建隐藏IAB，不桌面、外部/可见浏览器、切焦点、open/open_in_codex；不能保证则记未验 |

明确不做：新Provider、独立模型路由、另一Agent Loop、修改原生API默认选择、历史正文工具解析、跨协议旧缓存命中承诺、生产数据重放或部署。新声明用canonical schemas与可信child边界，不从用户文字接受工具定义。已有Conversation路由不得靠改默认配置冒称切换；交接须给原生实际更新机制和跨协议缓存边界。
