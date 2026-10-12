# Snapshot Index：20261011-v1.6-implementation

## 审查依据索引

| 输入类别 | 实际仓库文件路径或本文件位置 | 修改等级 |
|---|---|---|
| 用户需求 | `CLAUDE.md` 冻结版本的「V1.6 施工清单」「施工硬约束」；`docs/01-personal-hermes-v1-first-fork-iteration.md` 的公开目标和边界 | 二级 |
| 权威规格 | `docs/02-noting-system-specification.md`（V1.6 已定案修订及 §5.12 Target 优先）；`docs/04-hermes-secretary-v1.5-implementation-spec.md`（未被现行 02 修订的 V1.5 增量）；现行 02 未修订的 V1 契约全范围继承 | 二级 |
| 编码指导 | 根 `AGENTS.md`；根 `README.md` 的稳定环境与入口。上游分区文档仅架构参考，不新增规则 | 二级 |
| 会话确认口径 | 本文件「口径与决策」 | 二级 |

本索引为二级；依据文件修改需用户明确授权。`CLAUDE.md` 的冻结施工清单是需求来源，后续动态编排维护不改变冻结要求。计划、报告、代码为三级。初始冻结提交完整哈希见 `baseline.txt`；上轮证据仅事实参考，不代替本轮门禁。

## 口径与决策

| 口径编号 | 用户意图、确认结论或约束 | 决策理由及确认假设 | 用户消息定位与授权来源 |
|---|---|---|---|
| C01 | 开始 V1.6 一轮自主实现，采用 autonomous-run 套件；替代此前待启动及不走自主流程安排 | 明确的新启动指令；范围沿用已收口现行 02 及根看板施工清单；包括任务范围内本地阶段提交与两独立门禁 | 2026-10-11 本会话：“开始，1.6轮自主实现” |
| C02 | Agent 不得直接查询 item 生命周期表或找回条目；系统内部可按当前 Snapshot 的 id 列表读取对应版本正文，所有产品面仍过滤归档项，无恢复入口 | 澄清 §3.3a 的内部读取与 Agent 访问边界，已立即同步现行 02 | 2026-10-11 本会话异步回复：“是，原意就是禁止 Agent 查表和找回” |
| C03 | Noting 开始后新增或修改的 memo 应保留到下一轮；采用简单正向代码机制保证不变量，尽量避免复杂 revision 机制 | 澄清 §3.5 的并发消费范围，已立即同步现行 02；具体内部主键与事务实现属于工程方案，不冒充用户逐项批准 | 2026-10-11 本会话异步回复：“是应该保留，但你打算怎么做呢？用正向代码机制，保证不变量平凡成立，这是原则，尽量不要设计复杂的 revision 机制” |
| C04 | 认可上一答的简单 memo 行身份方案；统一 Finish Framework Message 追加“便签上已处理的条目，已清空。”，说明 Notebook 与已处理 memo 在同一 commit 更新 | 已同步 §5.6 与 §5.12 Target；新内容仍按 C03 保留，通知不宣称全部 memo 清空 | 2026-10-11 本会话：“可以。……现有的 noting task finish framework message。可以加一句，便签上已处理的条目，已清空” |
| C05 | C04 的中文是语义要求；完成通知应使用正常系统英文：`Background: notebook updated at <snapshot commit time>. Processed memo entries have been cleared.` | 覆盖 C04 的语言呈现；消费范围、同事务 commit 与单条通知机制不变，已同步现行 02 | 2026-10-11 本会话：“我让你稍微改转写一下，转写成正常的系统英文” |
| C06 | Verification 在无其他干扰下先仅依据规格建立审查判据；重点检查方向明确但接线/实现细节薄弱处，随后套代码。发现后主会话提方案，Verification依据判据评审，授权内工程细化自行收敛；研讨与结论进入审查报告、delivery和最终汇报，其他既有审查职责不缩减 | 已更新 spec-implementation-review、autonomous-run、delivery-evidence-review 及两个模板；此轮判据阶段只读01/02/04规格，索引/版本仅定位，代码/测试/历史报告/动态看板/主会话解释后读。讨论不暂停已授权后台实现 | 2026-10-11 本会话：“唯一的参考是规格”“主 agent……提议方，verification……评审方”“规格里比较弱的，指明了方向，但是没有写具体接线实现”“其他 verification 已有的职责也不要忘记”；此前明确未要求后台停工 |
| C07 | 最近实际Main请求来自External使Noting被D01拒绝时追加Framework Message，覆盖Force、Idle及冷恢复catch-up；具体追加位置、正常系统英文及简单通知抑制交主会话收敛 | 已同步02 §5.6；所属Parent尾部／busy与fence队列；同live runtime／Conversation持续External只提示一次，实际Native请求重置；保持参与开关及已有Notebook。文案与抑制方案是委托范围内工程决定，不冒充逐字批准 | 2026-10-11 本会话：“你自己收敛一下吧……因为这种情况失败的时候，追加一条 framework message”“但是，不只是 idol 吧。” |
| C08 | Noting 只触发父会话原生压缩，并负责自身 Snapshot 提交及 Framework Message 生产；active Turn 协调、压缩结果接收、Compression Continuation 均由父原生机制处理，不由 Noting 查表、拼消息或重做判断 | 用户纠正 VF02 修复职责；已同步02 §5.9。撤下此前 Noting 层读库拼接提案（未实施）；具体原生接线方案仍待调查及Verification评审 | 2026-10-11 本会话：“压缩本身应该是由父会话自己的机制、原生机制驱动的”“noting task，只是触发，不把这些重新判断一遍，也不干涉，父压缩实现” |
| C09 | compact_parent按既有原生成功契约成功触发请求后，即使父compact随后取消/失败，任务照常尝试Snapshot Commit Gate，合法提交后照常写Finish Framework Message；成功不等待最终压缩commit，也不因后续取消撤销 | 用户再次明确已准入请求与最终压缩结果独立；保留原Notebook/Anchor/enablement Gate及未准入正常terminal失败，已立即补02 §5.9 | 2026-10-11 本会话：“如果……compact被取消了，那么snapshot应该照常提交”“只要成功触发compact请求就可以……framework message照常写” |
| C10 | Main notebook_show对模型隐藏Snapshot身份、Conversation/Anchor/Message Identity、Trigger/Profile及审计字段；只保留Notebook完整正文，并添加last_update_time | 用户明确纠正AI返回契约。正向投影四区＋现有提交created_at值；内部Snapshot/Full审计、任务局部工作态及History权限不变，不引入docs06新UI | 2026-10-11 本会话用户粘贴Snapshot envelope后：“这些对模型隐藏掉……只需要加一个字段，last update time” |
| C11 | C10模型视图再允许anchor_message_uid；UID可用于History查源，除此不再加Snapshot元数据 | 最新用户补充仅覆盖C10对Anchor UID的隐去，保留裸UID、不加Identity包装或Conversation ref；正文四区＋last_update_time＋anchor_message_uid是最终白名单 | 2026-10-11 本会话：“再加一个字段 anchor message U I D……UID 是可以进入模型暴露面的……除此以外，不要再加神奇子弹” |
| C12 | session_history模型返回去重：Conversation ref在结果级一次，各消息仅单message_uid及timestamp/role/content，不重复Identity包装或物理地址 | 用户明确要求打磨暴露面、避免长UID重复浪费token；输出以正向白名单收敛，Main/Noting共用，保现有read参数、内部canonical身份及权限、原文/截断，不增selector | 2026-10-11 本会话：“为什么要把 message UID 写两遍……我的 token 很珍贵……打磨一下相关的东西？不要重复字段” |

| C13 | Force Noting 触发的 Framework Message 不得带入下一个 compaction 区间 | 用户明确生命周期边界；成功压缩后模型上下文不携带该旧通知，原历史保留；取消/失败/no-op没有进入新区间；特别覆盖active同Turn中途压缩Continuation后，旧区间排队通知在Turn结束迟到落尾的情况。正式压缩器60→10实际反例已确认旧UID/body保留，修补属于本轮新增授权 | 2026-10-12 本会话：“force noting 触发的那个 framework message，不允许被带到下一个 compaction 区间”；随后要求“检查一下，现在有没有可能造成这个问题？”；进一步明确担心active Turn中途压缩后续跑、Turn结束才落通知的情况 |

| C14 | 为尽快完成真实链路验收，允许临时调整隔离验收profile的现有配置（Idle delay示例半分钟）；禁止用代码强制触发，必须验证真实定时器逻辑 | 只调整合法配置与测试输入，不改产品默认值/机制/规则；一般Idle设30秒、memo操作可按现有配置暂加长，记录前后并在验完恢复原值。所有Idle/Schedule通过真实Main/Noting与真实时钟；不直接trigger/tick、不改DB due、不伪busy/时钟；既有provider/API边界不变 | 2026-10-12 本会话：“可以把那个delay……调到半分钟”“不能用代码强制触发，必须检查真实的定时器触发逻辑是否工作正常”“其他的一些配置可改的……可以临时改一下……尽快完成真实链路测试” |

| C15 | 所有实际面向AI和人的绝对时间戳统一为带时区可读日期时间，不仅Notebook；内部持久数值/调度比较和时长不变 | 用户先确认human Created at及AI last_update_time都改，随后明确扩大到全部暴露面并要求专门子Agent；保原瞬间/字段/权限/时间来源，复用已有profile/native时区格式，不新增时间marker或改历史prefix | 2026-10-12 本会话：“两处都改为可读时间（建议）”；随后“所有的面向AI和人……时间戳都得改……专门派遣一个subagent” |

| C16 | 定时器照常到点，会话参与开关只在统一到点事件入口读取；off结束本事件不重试，on走既有准入；/noting off只改偏好不取消timer，扫描只恢复未处理合法事件 | 最新用户纠正优先于此前关闭即取消提案：禁止开关判断散落在host/attach/scan或新增flags；在全局启用且eligible边界下保持既有真实Main生命周期timer，复用已有单次事件/原子ownership，不改global关闭/资格/权限安全边界 | 2026-10-12 本会话：“定时器照样触发……触发之后检查当前……conversation的开关状态为唯一条件”“不要把条件散落在各处……以这个点为条件”；此前“关闭不执行不能后续重试”“别乱加标志位” |

| C17 | 本轮实现层立即收尾，独立门禁/真实验收移至第二轮；只交接最小缺口，不要求重做V1.6全量Verification | 用户变更结束条件与后续编排；第二轮外部UI单独仓库，工作区仍本仓库，本仓库也按接线需求修改；已有有效证据复用 | 2026-10-12 本会话：“本轮到此为止……实现层面收尾……验收……下一轮”“不要……重新做一遍1.6……全量verification”“交接文档写最小缺口即可”；随后明确工作区仍这里及本仓库第二轮被改，要求赶紧结束 |

初始冻结提交见 baseline.txt；C03–C17 是初始冻结后的用户确认补充（C14仅真实验收配置/操作约束，不改产品规格默认值）。C03–C05 产品口径已进入现行02 §3.5、§5.6、§5.12，C08已进入§5.9；先按C06独立建立规格判据，之后再核对本表及其他证据；不能只按初始提交的旧清空描述及旧 Finish 文案审查。明确不做：个人化集成、外部 Mem 写入、provider/模型路由重构、新通用调度器、新 API hierarchy、数据迁移、未授权 push/部署。运行与权限约束来自根 AGENTS.md 和既有权威规格，不冒充本轮新增会话问答。
