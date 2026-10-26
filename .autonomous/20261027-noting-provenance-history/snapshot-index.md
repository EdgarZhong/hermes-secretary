# Snapshot Index：20261027-noting-provenance-history

## 审查依据索引

| 输入类别 | 实际仓库文件路径或本文件位置 | 修改等级 |
|---|---|---|
| 用户需求 | docs/07-scheduler-notebook-noting-compaction-redesign.md 顶部2026-10-26跨区间保真节，含2026-10-27时间含义确认 | 二级，已授权落实本轮实现事实与必要接口细化，产品语义改变仍询问 |
| 权威规格 | docs/notebook-ontology-whiteboard.html（全篇，最新07覆盖冲突）；docs/07-scheduler-notebook-noting-compaction-redesign.md（最新顶部优先，R20及v2保留未覆盖条款）；docs/02-noting-system-specification.md §1身份／§2 Foreground／§4 Snapshot及来源／§5运行；docs/04-hermes-secretary-v1.5-implementation-spec.md §2–5未覆盖原生接缝；docs/01-personal-hermes-v1-first-fork-iteration.md §1、§3–4；docs/06-Hermes-Secretary-Web-UI-V1-Spec.md §0、§1.12 Notebook与现行API | 二级，用户授权本轮变更，仅修改范围内事实和必要接线，保留历史版本结论 |
| 编码指导 | AGENTS.md（根权威）；README.md稳定入口；CONTRIBUTING.md及分区AGENTS仅环境／架构参考；docs/cloud-deployment-sop.md部署步骤 | 二级，用户授权随实施更新，不增改冻结检查规则 |
| 会话确认口径 | 本文件“口径与决策” | 二级 |

本索引二级；plan及报告三级。不读docs/archived。基线哈希写baseline.txt。最新用户明确口径高于旧规格；不得用旧数组替换／time_range／物理role／工具哈希许可否定新要求。范围外旧轮完整验收不重复立项。

## 口径与决策

| 编号 | 用户确认意图、约束与完成标准 | 理由／保持边界 | 用户原话定位与授权 |
|---|---|---|---|
| C01 | 实现、测好、上线；生产仅Alex仍用的一个置顶Conversation做一次性Notebook新结构转换 | 不做通用迁移／兼容层；先核准真实目标，不改变聊天事实／模型配置／Schedule／绑定／其它会话 | 10/27“开始改吧。改完，测好，上线”；10/26“直接手改一下” |
| C02 | 无用户实质提及、无推进的条目正文／状态不变；助手提示、Reminder到期、未回应不构成变化 | 非必要不润色description，保持稳定entry_id；清退／结算规则本轮不改 | 10/26“这条条目原样保留，什么都不修改”及批注撤回第8块 |
| C03 | “稍后处理”未明确推迟不改正文／状态，但Main未登记后续Schedule时补schedule_suggestion | 建议不代表登记，不造推迟时刻，Noting无Scheduler权限 | 10/26“应该属于scheduler建议” |
| C04 | 新消息来源仅精确UID，无时间范围；按条目×Noting Task分组为UID数组的数组 | 当前提交数组去重，不新增跨Task全链去重；来源只读旧节点保持 | 10/26“Providence链应该是message UID的数组的数组”；10/27精简稿“确定了” |
| C05 | 同Task每条目最多一个新来源节点，无改动不新增；后续调用／续Turn覆盖本Task槽位 | 每次真实编辑同时传属性修改和本Task完整来源数组；字段按键合并／提交值覆盖，不整条重置；拒绝无副作用 | 10/26“province和编辑必须同时传”及第5块确认 |
| C06 | Candidate来源保持直接UID来源链或Notebook条目引用二选一 | 不混传，不取消refs；不重复源正文；source_types标签／反向refs原契约保持 | 10/26“Candidates…统一来源链…二选一” |
| C07 | Evidence time需要、runtime派生只读，时间链与provenance内层UID组一一对应 | 每组真实用户优先：一条单时刻，多条最早／最晚范围；无用户取最近Assistant；两者皆无取组消息范围；未知不造现在／不丢槽位 | 10/26“每一个元素…刚好从…内层UID数组…产生，逻辑不变” |
| C08 | Evidence time使用来源消息原始timestamp，不抽取正文所述事件时间 | 不因重读／重写刷新进展、讨论及证据时间；Candidate refs沿源链派生 | 10/27异步选择“来源消息的原始时间，沿用旧派生逻辑” |
| C09 | 增加Get Meta：时间段主查询，include关键词与语义角色可选过滤 | include复用Search原查询语义；不建检索器／向量库 | 10/26“Get Meta…主查询参数是时间段”“Include就是Search” |
| C10 | Get Meta每条严格只有message_uid、timestamp、role、content；每个过滤命中都返回 | content头100＋尾100，共200；短内容不重复；跨会话外层分组保归属，不加第五单条字段 | 10/26“只有3个”后追加role；认可预览预算 |
| C11 | Get Meta先去本项目注入正文timestamp及HTML／标签包装，再截头尾 | 保留独立原消息timestamp；不删用户自写日期／HTML，不改持久原文，先分类后清理 | 10/26“对于user message…去掉timestamp…其他消息…我们的HTML体系标记” |
| C12 | 全工具默认当前Conversation，cross_conversation顶层独立默认false，模式不改变含义 | Main授权同Profile显式跨域；Noting仅绑定父；不改身份／branch／rewind合法路径 | 10/26“开关保持在最顶层…不因为模式改变”及既有权限 |
| C13 | 全模式默认只真人user及Assistant；顶层辅助消息开关独立默认false | 系统user载体按可信display_kind／origin归system；role/kinds旧参数不能绕过此默认。开关名采用include_auxiliary（工程拼写） | 10/26“整个conversation_history默认…在顶层再加额外控制字段” |
| C14 | 对外role及角色过滤统一user、assistant、tools、system语义 | system包括Heartbeat／Reminder／Framework／Compression／Notebook等模型可见载体，不直接照搬DB role；不泄露原本不可见内容 | 10/26“role并不等同于库里…system里面应该包括…” |
| C15 | Search显式工具返回参数与结果各头100＋尾100，不返回hash | 工具配对必须同次调用；不混同批其它call；Read选定工具可完整取参数／结果，长正文沿正式有界窗口／分页 | 10/26“Search…不展示哈希…参数和结果头尾截断”；“read…完整返回当时参数和结果” |
| C16 | 所有timestamp查询／过滤包含上下端点的闭区间 | 查询消息时间，不是Session start，不改变独立原消息timestamp | 10/26“所有timestamp过滤，包括查询，都是闭区间” |
| C17 | Get Meta过滤后的时间段返回全部；超容量明确要求缩小，不静默漏条或宣称完整 | 实现用既有200逻辑消息上限作Get Meta完整返回容量，超过则明确错误；不得返回不完整成功 | 10/26确认剩余第3项；具体200为既有接口上限的工程复用 |
| C18 | 已审精简Prompt：父最新可见区间作更新主依据，早期消息仅必要溯源；History默认Get Meta，Search定位、Read补细节 | 无必要不查History；不重读已见正文取UID；用户真实发言第一、Assistant具体回复第二，辅助证据仅必要时；旧证据重读非新进展 | 10/26逐块批注、精简稿“确定了” |
| C19 | Prompt第5块集中双类条目及属性／provenance同传、Task跨Turn同槽；第6块去重复；Candidate统一链／refs二选一；Schedule建议保留 | 不教本轮／上一轮术语，不改第8块清退，不单改续Turn结尾，finish_noting原结束语义保持，父完整tools/cache prefix保持 | 10/26 Harness准则批注及后续确认 |
| C20 | 正式工具接线、读写权限、Snapshot原子性、父子冻结工具与cache-parity、并发／失败／fork／rewind／重启契约保留 | 单元测试不能替代正式机制／真实模型；独立Verification与Validation；部署后版本、数据及服务验真 | 根AGENTS及最新07保留契约；上线授权 |

范围外：UI／APK改版、Scheduler机制重写、旧失败Noting重放、Provider/Persona调优、旧时间修复、NM／其它服务迁移。显示保护：只能自建隐藏IAB，禁桌面／外部浏览器／可见页／切焦点；本轮核心可经正式工具入口验收，无须动用户页面。个人数据／凭据／真实wire只留ignored或受限运维环境，不入Git。
