# Snapshot Index：20261024-noting-maintenance-v2

## 审查依据索引
| 输入类别 | 实际仓库文件路径或本文件位置 | 修改等级 |
|---|---|---|
| 用户需求 | docs/07-scheduler-notebook-noting-compaction-redesign.md：2026-10-24最终方案v2 §0–9 | 二级 |
| 权威规格 | docs/07-scheduler-notebook-noting-compaction-redesign.md、docs/notebook-ontology-whiteboard.html；未覆盖不变量继承docs/02-noting-system-specification.md、docs/04-hermes-secretary-v1.5-implementation-spec.md、docs/01-personal-hermes-v1-first-fork-iteration.md、docs/06-Hermes-Secretary-Web-UI-V1-Spec.md、docs/08-profile-scheduler-files-clarification.md（仅继承07未替换不变量，不扩大个人化或UI范围） | 二级 |
| 编码指导 | AGENTS.md、README.md、CONTRIBUTING.md | 二级 |
| 会话确认口径 | 本文件“口径与决策” | 二级 |
| 本索引 | .autonomous/20261024-noting-maintenance-v2/snapshot-index.md | 二级 |

07的2026-10-24最终v2及本表是本轮变更权威，后面的历史四工具Schema／Prompt及历史验收保持其时点，不覆盖新口径。二级依据仅有用户明确修改授权时改；plan/报告为三级。冻结哈希保存baseline.txt。

## 口径与决策
| 口径编号 | 用户意图、确认结论或约束 | 决策理由及确认假设 | 用户消息定位与授权来源 |
|---|---|---|---|
| R01 | 六工具完整固定API顶层，父子共用Root/tools/冻结Active前缀，Task不重复Schema、不动态注册 | 解决动态工具兼容且保护缓存前缀 | 用户“6个专属工具改到顶部…白名单” |
| R02 | Main拒绝create/update/archive/finish，History/Show可用；Noting只六工具且可信身份运行时控制 | 不依赖Prompt自称身份，同步并发间接路径一致 | 同上与六工具批准 |
| R03 | maintain拆create/update/archive，参数扁平、同字段同层；stable ID/类型/版本/原子失败机制保持 | 纠正模型原先update层级错误 | 用户“我已经批准…同一个字段…不一样层次” |
| R04 | 七类字段必填性按07；删除external_refs，文件引用仅在description精选记录，路径不计软长度 | 不增文件字段、不扩独立材料准入、不列全文件 | 用户“删除”“只需要改一个prompt”“路径不计…不要大量瞎引用” |
| R05 | description完整指导与1–3短句、约150中文字符/80英文词软长度；第三步写作、第五步过滤两表独立 | 索引清晰有效、不复述历史、不要求Noting比较未知摘要；无硬长度门禁 | 用户确认description及“不要合并” |
| R06 | evidence_time模型可见、runtime派生只读数组：每条真实用户各一个时间戳，无用户取最近Assistant，再无列全部来源时间；显式时间段数组独立加入；Candidate refs沿原来源链聚合数组 | 不让模型手填，不把分散证据压成宽区间；保持原7天/72小时及progress/discussion/gap计龄，未知不造日期 | 原只读时间确认＋用户“evidence time加成数组”及取时答复“每条用户消息各列一个时间戳…” |
| R16 | 七内容类型source_time_ranges数组与IDs可混传，每段沿原起止结构、数组完整替换；同一处证据通常二择一仅Prompt软指导，无跨表达覆盖重复／重叠硬门禁；兼容旧单范围只读规范化，不改历史原件 | 多时点证据保留；同字段同层及来源域不变；当前API只声明新数组 | 用户“时间段同样改成数组…provenance可以混传…prompt软约束” |
| R07 | relations普通关系归档同时解除；gap情景/Candidate来源仍保护 | 无悬空、原子清理、不级联状态、不加图门禁 | 用户确认简化门禁 |
| R08 | 每entry零或一Schedule建议，entry顶层content+schedule两语义字符串；Noting必查漏登记，content自包含完整，schedule不作时间语法校验 | Noting无Scheduler权限，Main考虑创建/更新；建议不代表实际登记 | 用户“一对一”“普通字符串”“只是advice”“未实际创建schedule” |
| R09 | 注入Notebook含建议时Framework最底部追加已定稿Main提示，非触发、不误发微信 | 不要求立即照抄或再作强制复查，不增队列/强制注册 | 用户逐句确认Main/Noting提示 |
| R10 | Noting开且eligible Main：原生阈值自动保默认tail，其它取消默认tail；显式/compress here N保持原生指定tail；off/非Main原生 | 全部被覆盖旧尾部进入摘要，保新输入/工具协议/DB原文 | 用户压缩分支与“不用禁用它” |
| R11 | 仅Idle正常Noting提交→父durable压缩→Framework；failed/forced/overflow不触发Idle full，合法快照及非正常通知保原契约；其它压缩不新增成功门槛 | 不丢上下文，不把一般API失败伪装新Snapshot | 用户Idle原则与“一般API错误可以没有新快照” |
| R12 | 外部成功交接范围按原规则退出；保未覆盖变化/责任，不留“仍有用”余额、不重建已结算范围 | 三种外部体系负责后续使用，避免Notebook无限增长 | 用户“还是应该归档…三种途径” |
| R13 | 第4步只替换still-needed scope短语为scope left unsettled by confirmed writes及其必要上下文，其余保护保持 | 平衡积压与误清退，不多处强硬强调 | 用户“这一处最小修改，我同意” |
| R14 | 自主实现、Sol并行、主会话亲审、定向回归/端到端及独立双门禁，确认后提交部署 | 保其他任务改动、凭据与生产数据；提交自动push | 当前用户“开始自主实施，挂个目标…提交部署” |
| R15 | 实际Kimi Coding/隔离Alex Profile，真实长前缀超过历史N38，真实Main→Noting→压缩→Framework→后续Main代表链路 | 已授权付费及缩小隔离阈值；不动正式Conversation/Notebook/Snapshot、不改公开Persona | 先前用户“Kimi…Alex隔离副本”“阈值超过…n等于38”与本轮端到端授权 |
| O01 | 不做Web恢复/Android/标题/Provider协议切换/上游Issue/个人Provider改造，不改生产Schema迁移策略 | 用户本轮明确范围 | 本轮范围表及排除事项 |

未决产品项：Candidate直接来源是否也允许时间段数组与IDs混传已异步询问，未答不算确认；此项暂不实施，保留原仅IDs或notebook_refs模式，不阻止七内容类型及只读时间数组的已确认改造。最终收费验证、独立双门禁及发布前须完整收口。工程衔接按已定机制收敛，不扩大权限、结束条件或硬门禁；重要自主取舍按AGENTS登记。
