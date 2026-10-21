# Snapshot Index：20261021-conversation-heartbeat

## 审查依据索引

| 输入类别 | 实际仓库文件路径或本文件位置 | 修改等级 |
|---|---|---|
| 用户需求 | `docs/07-scheduler-notebook-noting-compaction-redesign.md` §8.15；本文件口径与决策 | 二级 |
| 权威规格 | `docs/07-scheduler-notebook-noting-compaction-redesign.md` §0、§3、§6.3、§8.15；`docs/06-Hermes-Secretary-Web-UI-V1-Spec.md` §0.7–0.8及Heartbeat呈现契约；`docs/cloud-deployment-sop.md` §0、§8（其余旧北京模板不替代首尔现状） | 二级 |
| 编码指导 | 根 `AGENTS.md`；原生身份／Profile／执行与持久化约束继承07及既有正式接缝；README仅事实入口、CLAUDE仅动态状态 | 二级 |
| 会话确认口径 | 本文件“口径与决策” | 二级 |

本索引二级；基线完整SHA在`baseline.txt`。plan及两门禁报告是三级执行记录，不作为新增产品要求。前轮模板／UI样本只按当时受测版本引用，不代替本轮Conversation管理验证。

## 口径与决策

| 口径编号 | 用户意图、确认结论或约束 | 决策理由及确认假设 | 用户消息定位与授权来源 |
|---|---|---|---|
| HB01 | 仅目标Profile全局`noting.enabled`开启时使用Secretary Heartbeat；不看Conversation局部`/noting`。关闭保持原生 | 用户在两选项中明确选择全局开关 | 本会话异步回复“只看全局 noting.enabled，忽略当前 Conversation 的 /noting 开关” |
| HB02 | 英文`<heartbeat>`、内部单一timestamp、固定检查正文、可选Additional prompt、以HEARTBEAT_OVER回复；去掉fires every | 精确文案以07 §8.15为准；结束文字不新增静默或调度控制 | 本会话“XML风格标签…Time Stamp…最终以HEARTBEAT_OVER回复”及“文案模板用英文” |
| HB03 | UI runtime／platform唤醒目标Conversation，复用原生Main／模型／Profile；不因微信绑定伪造入站／自动回复 | 保持用户实际UI模式及缓存前缀 | 本会话“唤醒的 platform 延用我们的 UI模式” |
| HB04 | 全局开启时按Profile＋稳定Conversation独立设置／暂停／恢复／清除；压缩身份不变，新建／reset／fork独立且不复制父设置 | user-facing Conversation为owner，不能退回物理Session | 本会话“Conversation级独立管理也一起改好，每个Conversation独立设置、暂停和清除Heartbeat” |
| HB05 | 切换会话、关闭页面、runtime回收及后台服务重启不删除设置／激活；后台解析自身合法tip，不跟焦点／Gateway peer串会话 | 服务运行是实际执行前提；missed tick沿原生合并，暂停／清除不得复活 | 本会话“切换会话或关闭页面后不影响heartbeat的触发”；后续“不要因为Gateway，或者别的逻辑，而失去conversation，有效绑定和激活” |
| HB06 | 采用state.db自有表、既有身份／压缩路径、原生writer租约与宿主扫描；事务认领及过期退款不能覆盖后续操作 | 07、根AGENTS既有机制约束；不得放宽Scheduler／Noting通用route安全来实现旧Conversation恢复 | 既有项目规则及07；用户确认按Conversation保存绑定 |
| HB07 | 完成测试与验收后自行部署后端，并一起部署已打包前端 | 静态产物绑定前端`0b8843fb87bf0ba109f7b744f4ae96faf09df597`；不包含其它Android工作区dirty；与其配套的已授权failed_turn来源标记纳入集成发布，不扩大其它功能 | 本会话“完成测试验后，自行部署，前端的表现层也有调整，构建产物已经打包，你直接一起部署” |
| HB08 | 部署后给Alex当时实际置顶Conversation设置每两小时Heartbeat，无额外prompt；不立即触发测试Turn | 通过正式状态控制入口绑定实际ref，保留历史／排期／微信绑定；除目标Heartbeat外不改生产配置 | 本会话“然后给Alex现在的顶置conversation配置一个每两小时的heartbeat，不用额外prompt” |
| HB09 | 创建持续目标，一口气完成；禁止Astra | 本轮实现与独立门禁均gpt-6.1-sol／High；两独立门禁由无实现上下文第三方完成 | 本会话“给自己挂个目标，一口气完成”及“不要使用astra模型” |
| HB10 | 开发期不自动批量迁移生产旧原生Heartbeat，关闭分支保留native数据；新Conversation表由正式设置建立 | 继承根AGENTS开发期不迁移；Alex此次明确新设置，无需导入旧原生定义 | 根AGENTS及HB08授权的具体设置；无旧native迁移授权 |

不做：新的Agent Loop／模型路由／通用admission gate、浏览器定时器、改变HEARTBEAT_OVER运行语义、部署Android dirty、生产故障注入、提前触发Alex真实Heartbeat、修改用户历史／排期／微信绑定／无关配置。UI检查仅自己创建的隐藏IAB（visible:false）。无影响冻结的未决问题。
