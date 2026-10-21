# Verification：20261021-conversation-heartbeat

## 1. 审查对象与结论概览

**最新第二次独立全范围Verification通过（2026-10-21，后端ed94619／前端0b8843f）：36条全部符合，0违规、0证据不足；HB-V-01与R2-POST均关闭。** 独立判据先落盘后全轮审查，再按授权顺序补核修复版生产收据；实际Web/Gateway为ed94619、固定439文件一致、三库受保护全行指纹保持。Alex原7200秒／空prompt／active定义及revision1、创建时间、last_fired_at和19:58:09 next_due完全不变，未重复set、未提前模型触发。旧失败与前置时点记录保留，均不覆盖本段最新最终结论。

### 初审更正时历史（保留当时对象与判定）

- 审查者：独立 Verification 子 Agent；2026-10-21；未继承实现上下文；禁止再派生。
- Snapshot Index：`.autonomous/20261021-conversation-heartbeat/snapshot-index.md`；版本记录：同目录 `baseline.txt`。
- 冻结规格版本：`51300c06001e14af6bb91fd2c0d53b8c0b3fe9fa`。初审当时待审实现版本：`f32d70f703fd8995f6652ca71ff72ef0d56d535e`；固定前端 `0b8843fb87bf0ba109f7b744f4ae96faf09df597`。
- 范围：07 §0、§3、§6.3、§8.15，06 §0.7–0.8、Heartbeat呈现与本轮配套 failed_turn 来源标记，部署 SOP §0、§8，Snapshot Index HB01–HB10。
- 进入条件：本报告第2节已仅据上述冻结原文建立；此前未读代码、测试、实现报告、动态看板。
- 初审历史结论：f32前置代码／发布准备门禁曾通过，已进入独立Validation；当时26条符合、V26–V28发布准备符合且部署后补证、V29设置后补证。该初审没有作整轮完成声明。
- **初审更正时历史结论（生产RPC回执发现后）：Verification不通过，当时最终门禁保持未通过。** 原V13对正式管理输出的“符合”漏审成功note，现更正为违规；其它已核实机制与证据保留。已收到f32真实部署/设置日志，证明已执行，V26–V29交由修复后的全新独立审查者结合最终版本复核。不得以持久化数据正确或已部署代替关闭用户输出缺陷。

## 2. 独立要求清单与覆盖

判据建立时间：2026-10-21，首次实现调查之前。来源均为冻结版本原文；索引和版本记录仅用于定位。类型中“直接”指明确原文要求，“推导”指满足原文必需的不变量。方向明确但路径细节未指定的恢复、跨宿主及时间来源项保留重点核查，不据此降低规定机制。后续修订须在第6节保留规格依据和理由。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| V01 | 07 §8.15 L1445；HB01：仅目标Profile全局noting.enabled选择分支 | 直接；开关/边界 | 本地/noting不参与；启动Profile不能代替目标Profile | 全局开+局部关仍Secretary；目标全局关仍原生；跨Profile分别解析 | 第3节V01 |
| V02 | 07 §8.15 L1445–1458：英文XML user消息与固定检查正文 | 直接；消息行为 | 一条role=user、完整heartbeat包装、检查正文及最终回复文字逐字符合 | 正式请求、持久记录及重放一致；无fires every或周期称呼 | 第3节V02 |
| V03 | 07 §8.15 L1445、1458：单一实际触发时间 | 直接+推导；时间来源，接线薄弱处 | 目标Profile时区；首行内部timestamp；持久/请求/重放同一来源，不在外围再追加 | 检查跨时区及重放；时间在正式触发点产生并贯穿，不在各层重算 | 第3节V03 |
| V04 | 07 §8.15 L1458：Additional prompt可省略 | 直接；合法输入 | 省略/纯空白只省该段，基础正文保留；非空在正文后闭合前 | every无prompt与空白均成功；非空准确保留并放置 | 第3节V04 |
| V05 | 07 §8.15 L1458；HB02：HEARTBEAT_OVER只为模板回复要求 | 直接；结束/权限 | 不新增静默、过滤、自动调度或Turn结束策略 | 搜查所有消费者，无特殊运行语义；原生结束授权保持 | 第3节V05 |
| V06 | 07 §8.15 L1460；§3.1：正式UI执行和原生模型链 | 直接；指定机制 | 后端UI宿主→_run_prompt_submit→run_conversation；沿目标模型/Provider/推理/Profile及工具上下文 | 静态追完整入口与真实模型代表证据；无新Heartbeat Agent/执行器/路由或root Prompt旁路 | 第3节V06 |
| V07 | 07 §8.15 L1460；HB03：沿UI platform，不伪造Messaging入站 | 直接；渠道/缓存边界 | 绑定微信不把此次唤醒变渠道事件，不自动回复微信 | 绑定Messaging目标仍UI platform与正常工具上下文；渠道路由保持不变 | 第3节V07 |
| V08 | 07 §8.15 L1460、1466：host-only后台恢复 | 直接+推导；生命周期/机制薄弱处 | 页面/焦点/原runtime无权决定active定义；服务运行才执行 | 切会话、关闭页面、runtime回收后能按持久定义恢复原目标 | 第3节V08 |
| V09 | 07 §8.15 L1460；§6.3：Scheduler独立 | 直接；功能开关 | Heartbeat不受scheduler.enabled联动 | scheduler关但noting全局开仍扫描/投递Heartbeat；不得放宽Scheduler规则 | 第3节V09 |
| V10 | 07 §8.15 L1460、1470：原生用户优先与writer租约 | 直接；并发/执行机制 | busy等待、用户输入优先、未进入执行refund；不新增通用admission gate | 正式UI writer租约在后台路径仍生效；忙/拒绝/异常不丢定义或误执行 | 第3节V10 |
| V11 | 07 §8.15 L1462；HB10：全局关闭保持原生 | 直接；兼容 | native模板、非空校验及CLI/Gateway/UI路径和数据保持 | 原生各正式入口回归，Secretary不修改native定义；不自动迁移生产旧定义 | 第3节V11 |
| V12 | 07 §0、§8.15 L1464：Profile+稳定conversation_ref唯一owner | 直接；数据归属 | 所属Profile state.db内每Conversation最多一条；物理session不成为owner | DB唯一性及所有slash/结构化读写/扫描均使用同owner；跨Profile隔离 | 第3节V12 |
| V13 | 07 §8.15 L1464：every/status/pause/resume/clear | 直接；完整管理 | every设置或替换当前定义；pause保留，resume重新计时，clear移除；只影响当前owner | 正式命令及现有结构化控制完整操作，验证重设排期及其它Conversation不变 | 第3节V13 |
| V14 | 07 §8.15 L1466：持久激活与重启 | 直接；恢复 | active服务重启恢复；paused/cleared不得复活；切换/离开不清除 | 关闭重建宿主与数据库重开后状态/定义相符，离开不删除旧定义 | 第3节V14 |
| V15 | 07 §8.15 L1466：目标缺失/暂不可恢复 | 直接；失败恢复 | 保留待执行状态并报告真实失败；绝不投当前焦点/其它Conversation | 安全隔离负例可观测失败且可重试；无错误fallback | 第3节V15 |
| V16 | 07 §8.15 L1460、1466：漏tick合并与跨宿主去重 | 直接；频次/并发 | 停机多次仅合并一次，不补积压Turn；CLI/Gateway/UI不可重复同tick | 多宿主竞争及错过多间隔的正式认领/投递证据 | 第3节V16 |
| V17 | 07 §0、§8.15 L1468：压缩连续与新身份隔离 | 直接；身份/历史状态 | 有效压缩同Conversation全部物理入口共享定义；new/reset/真实fork独立且默认无定义；旧定义保留 | 多段压缩tip/旧段管理及new/reset/fork正式入口逐项核查，无复制迁移 | 第3节V17 |
| V18 | 07 §8.15 L1468；HB05–06：旧Gateway generation专用恢复 | 直接；路由/权限，接线薄弱处 | 旧declared generation只失去当前渠道路由；已登记Conversation可凭证明绑定与自身压缩路径恢复 | 旧generation唤醒原目标；不重绑渠道，不放宽通用route、权限/来源校验 | 第3节V18 |
| V19 | 07 §8.15 L1470；HB06：Secretary自有表 | 直接；存储约束 | 使用所属Profile state.db；不修改原生表schema/ownership；无新对话存储 | schema/diff/调用位置证明单一owner及原生表不变 | 第3节V19 |
| V20 | 07 §8.15 L1470：写事务与版本比较 | 直接；并发原子性 | 管理操作和due认领在原生写事务协调；同tick只能一worker胜出 | DB事务/版本条件审查及竞争运行证据；不可仅依内存锁 | 第3节V20 |
| V21 | 07 §8.15 L1470：退款只撤自身未被替代claim | 直接+推导；失败/竞态 | worker身份/claim版本必须匹配；后续every/pause/resume/clear优先 | 认领后交错各管理操作再refund，不覆盖定义、不复活暂停/清除 | 第3节V21 |
| V22 | 07 §3.1；06 §0.5：原生零增量与兼容 | 直接；架构/接口 | 不改变原生Loop/路由、必填参数、返回/错误语义；只在正式接缝增量 | diff与上下游正式调用核对；展示/辅助持久化失败不阻断主执行 | 第3节V22 |
| V23 | 06 §1.4 L268：Heartbeat精确分类与source保持 | 直接；前端产物 | 仅role=user完整包装；保留原文/UID；普通提及、assistant引用、旧模板不猜测；无合成消息 | 固定前端版本源码/产物与针对性分类证据支持正反例 | 第3节V23 |
| V24 | 06 §1.4 L268：Heartbeat卡片呈现 | 直接；UI | 默认折叠，标题Heartbeat，波形图标，陶土橙浅底含暗色；同类阅读宽度；展开只去外包装，保留timestamp/正文 | 固定产物及现有同版本有效浅/暗UI证据；无Reply/编辑/附件/外部时间 | 第3节V24 |
| V25 | HB07；06 §1.4 L270：配套failed_turn来源标记 | 直接；明确授权附带变更 | 只标明确生成取消诊断的实际消息行；不按正文/整个中断Turn标模型回复；旧历史不猜迁移；slash不变 | 后端写入分支及前端固定版本分类，部分模型回复/无独立诊断行/临时slash反例 | 第3节V25 |
| V26 | 06 §0.7–0.8；SOP §0：部署拓扑与guard保持 | 直接；发布准备/部署 | 以首尔ubuntu/Caddy/Authelia现状覆盖旧北京Access模板；同源双SPA单backend、token/REST/WS及stale4001保持；skew默认与独立消费者不变 | 发布准备确认目标与服务/产物绑定；部署后查真实同源入口与版本，不改认证/guard边界 | 第3节V26 |
| V27 | HB07：验后自主联合部署，固定已打包前端 | 直接；发布范围 | 前端必须0b8843fb87bf0ba109f7b744f4ae96faf09df597；包含已授权failed_turn；排除Android dirty | 发布清单及归档指纹绑定精确后端/前端版本，验收后再部署；不捎带其它工作区变更 | 第3节V27 |
| V28 | SOP §8：版本/快照/停服/回滚 | 直接；运维 | 升级前固定代码/产物/配置/SOUL指纹与可恢复快照；活动Turn/Noting结束后安全停唯一backend；保留新写入 | 发布方案及部署receipt证明静稳检查、保留数据、匹配环境/lock、恢复点与回滚入口 | 第3节V28 |
| V29 | HB08：部署后给Alex当时实际置顶Conversation每两小时无额外prompt | 直接；正式后置动作 | 通过正式状态入口解析真实Profile/ref；不立即触发测试Turn；保留历史/排期/微信/无关配置 | 部署后receipt含当时置顶选择、正式every 2h结果/读回与next_due；无真实触发及无关改动 | 第3节V29 |
| V30 | HB09、索引排除项、SOP §8：执行/证据边界 | 直接；审查与交付 | 禁Astra；独立两门禁；UI只自建隐藏IAB；不生产故障注入；接口/匿名302不冒称UI PASS | 角色与证据来源核查；运行隔离数据；交付区分已验证和限制 | 第3节V30 |

覆盖反查：目标、模板、事件时间、频次、生命周期、owner、原生分支、全部管理动作、恢复/失败/并发/关闭、新旧身份、渠道权限、前端及发布/生产设置均有条款。§3中Noting child、工具Schema与Snapshot等未改机制按V22回归边界核查，不将旧整轮Secretary重做列入本轮。

发现后补充解释（不改原判据）：V13正式设置命令的用户可见成功输出，不能否认V08/V14及07 §8.15 L1466明确规定的关页/切换不清除、服务重启恢复active。此项是原持久化产品语义对输出的必要约束，不是新增文案产品要求；初审遗漏该成功note，现据原文更正判定。具体英文措辞未冻结，可以在不改变原生关闭分支和执行机制的前提下修正。


### 第二次独立复审判据起点（2026-10-21）

审查者：heartbeat_verification_r2；指定模型 gpt-6.1-sol / high。判据版本 V2-起点，仅依据冻结提交 `51300c06001e14af6bb91fd2c0d53b8c0b3fe9fa` 的 Snapshot Index、07 §0／3／6.3／8.15、06 §0.7–0.8／Heartbeat及failed_turn呈现契约、cloud-deployment-sop §0／8建立。未读实现、测试、旧报告或动态看板；读取 baseline.txt 定位时遇到其附带执行摘要，明确排除该摘要，不作为判据或事实。索引与baseline仅用来定位。适用范围是本轮Heartbeat与固定前端配套增量，不扩大为重审07所有其它功能或既有全云部署。以下表需先正式落入报告第2节后再调查实现。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| R2-01 | 07 §8.15首段；HB01 | 开关／全入口 | 直接：仅目标Profile全局noting.enabled决定分支；Conversation局部noting无效；必要推导：不能借启动Profile判断 | 各入口读取目标Profile；local off仍Secretary分支，global off原生 | §3 R2-01 |
| R2-02 | 07 §8.15模板 | 提示／开启 | 直接：一条role=user、完整heartbeat XML及精确英文基础正文、HEARTBEAT_OVER；去fires every／周期称呼 | 正式请求及落库正文一致符合原文 | §3 R2-02 |
| R2-03 | 07 §8.15时间 | 提示／持久化重放 | 直接：内部第一行timestamp为实际触发、目标时区、原格式；同一来源时间贯穿，不再外包timestamp | 模型请求、原文及重放只有一个且同值内部timestamp | §3 R2-03 |
| R2-04 | 07 §8.15额外prompt | 输入边界 | 直接：可省略／空白不留空段；非空位于基础正文后、闭标签前 | 无prompt、空白与非空输入行为覆盖，间隔不变 | §3 R2-04 |
| R2-05 | 07 §8.15结束语义；06 Heartbeat | 原生边界 | 直接：HEARTBEAT_OVER仅模板最终回复要求，不新增静默过滤、调度、结束机制或授权 | 真实路径沿原生Turn，token不改变输出投递或权限 | §3 R2-05 |
| R2-06 | 07 §8.15 UI runtime；HB03 | 正式接线 | 直接：UI宿主恢复目标Main经_run_prompt_submit/run_conversation，UI platform/tool context | 完整正式调用链可追；无专属loop／adapter／执行器 | §3 R2-06 |
| R2-07 | 07 §8.15模型继承；§3 | 模型／Profile／缓存 | 直接：原生目标Conversation model/provider/reasoning/Profile、流式、持久化、中断、用量；不得root重建旁路 | 目标配置实际参与调用，已有root未无故改写，正式流式/持久化链 | §3 R2-07 |
| R2-08 | 07 §8.15 UI与Messaging | 渠道边界 | 直接：微信绑定不使heartbeat变渠道入站／自动渠道回复 | 从注册旧Messaging Conversation恢复仍UI platform，无重绑／自动发送 | §3 R2-08 |
| R2-09 | 07 §8.15 host-only与扫描 | 生命周期 | 直接：无UI实例、切会话、关页面、runtime回收不清／暂停；后台服务为实际执行前提 | 持久definition独立于client/runtime，host-only入口可恢复执行 | §3 R2-09 |
| R2-10 | 07 §8.15独立Scheduler | 开关边界 | 直接：Heartbeat不受scheduler.enabled联动 | scheduler关闭而Noting开启仍扫描/执行Heartbeat，Scheduler本身保持关闭 | §3 R2-10 |
| R2-11 | 07 §8.15 tick与busy | 时序 | 直接：用户输入优先、busy等待、漏tick合并、未执行refund，CLI/Gateway/UI同tick不重复 | 正式writer/claim链检查；停机多tick合一次，无排队积压Turn | §3 R2-11 |
| R2-12 | 07 §8.15关闭分支；HB10 | 原生回归 | 直接：global off保留原生模板、非空校验及CLI/Gateway/UI路径和native数据；不批量迁移 | 原生所有入口及native存储未被新表接管／删除，不自动导入 | §3 R2-12 |
| R2-13 | 07 §8.15 Conversation owner；HB04 | 身份／存储 | 直接：所属Profile DB+稳定conversation_ref每Conversation至多一条 | 唯一约束、入口owner解析一致，跨Profile同Session字符串不混淆 | §3 R2-13 |
| R2-14 | 07 §8.15控制接口 | 正式入口 | 直接：every interval [prompt]设置/替换，status/pause/resume/clear与结构化控制同owner | CLI／Gateway／UI现有控制全链覆盖；间隔校验沿既有约定 | §3 R2-14 |
| R2-15 | 07 §8.15暂停恢复清除 | 行为 | 直接：pause保留、resume重新计时、clear删除；其它Conversation/Profile不受影响 | 定义与状态/下次due转移正确，重复操作无串状态 | §3 R2-15 |
| R2-16 | 07 §8.15自身tip | 恢复机制；工程细节薄弱 | 直接：后台仅目标自身合法压缩tip，不依赖焦点/Gateway peer；必要推导：恢复绑定与合法路径须证明 | 旧declared generation/新peer存在时仍定位原ref合法tip，不投新generation | §3 R2-16 |
| R2-17 | 07 §8.15重启 | 持久化／历史状态 | 直接：重启active恢复、paused/cleared不复活 | 重开DB与新宿主还原状态；missed ticks合并 | §3 R2-17 |
| R2-18 | 07 §8.15缺失／暂不可恢复 | 失败；工程细节薄弱 | 直接：保留待执行状态并报告真实失败，不向其它Conversation投递；不能仅把持久定义存在视作完成 | 缺失/非法tip/恢复异常均保留可重试due，明确可观察失败路径，无错误目标 | §3 R2-18 |
| R2-19 | 07 §8.15压缩 | 身份连续性 | 直接：有效compaction保留ref，所有物理Session操作同definition，不复制迁移 | 原Session与tip设置/状态读写同一owner，压缩后执行新tip | §3 R2-19 |
| R2-20 | 07 §0／8.15 new/reset/fork | 身份边界 | 直接：新Conversation默认无Heartbeat，不复制父；离开父不清除 | 三类新身份均无定义，父definition保持，rewind不误归其它ref | §3 R2-20 |
| R2-21 | 07 §8.15 Gateway generation | 权限／路由边界 | 直接：旧generation仅影响渠道路由；专用恢复不得放宽通用route/权限/来源，不重绑 | 专用路径约束充分，通用resolver默认行为不变，peer映射无修改 | §3 R2-21 |
| R2-22 | 07 §8.15 state.db | 持久化机制 | 直接：Secretary自有表，不改原生schema/ownership；Profile绑定正式DB入口 | schema增量隔离，native表未改，不新建身份库/对话存储 | §3 R2-22 |
| R2-23 | 07 §8.15认领 | 事务／并发 | 直接：定义变更/暂停/恢复/清除/due认领使用原生写事务/版本比较；同tick并发仅一次 | 原子claim与多宿主争抢证据；无先读后写竞态 | §3 R2-23 |
| R2-24 | 07 §8.15退款 | 事务／失败竞态 | 直接：只能退原worker尚未被新操作取代的claim；不能覆盖新定义或复活暂停清除 | replace/pause/resume/clear与晚refund互斥，旧worker无法改新版本 | §3 R2-24 |
| R2-25 | 07 §8.15 writer | 资源／权限 | 直接：原生UI writer租约与用户优先，不新增通用admission gate | 正式入口前取得原生租约，busy不运行，finally释放；不绕过现有安全 | §3 R2-25 |
| R2-26 | 07 §3／6.3；根规则 | 兼容／隔离 | 直接：增量原生接缝、profile-aware、无独立路由、不开启即原生；坏配置不串功能 | 新参数默认兼容，非eligible与native调用无新行为，资源绑定目标Profile | §3 R2-26 |
| R2-27 | 06 Heartbeat卡片 | 前端分类 | 直接：仅role=user且完整heartbeat包装；source/原文/UID不变、不合成 | fixed前端解析路径与误分类负例；Assistant/文本提及/旧模板仍原类 | §3 R2-27 |
| R2-28 | 06 Heartbeat卡片 | 前端呈现 | 直接：同类卡片阅读宽度、默认折叠、Heartbeat标题、心电图标、陶土橙浅/暗；内层时间正文保留、只隐藏外wrapper | fixed产物对应源码/构建，UI验证由合规独立Validation提供；无reply/edit/attachments/外时间 | §3 R2-28 |
| R2-29 | 06 最终failed_turn；HB07 | 配套增量 | 直接：仅明确生成取消诊断的原文行标既有failed_turn；复用卡片、无标题；取消terminal派生卡 | 后端来源类型明确；模型部分回答/slash不误标，无旧历史猜测/迁移，恢复元数据保留 | §3 R2-29 |
| R2-30 | 06 §0.7–0.8；SOP §0 | 部署边界 | 直接：当前首尔单后端同源双SPA/API/WS，保留认证与stale/code-skew安全；旧北京模板不覆盖现状 | 部署配置/receipt证明目标正确，未新worker/API/auth旁路，版本守卫无被削弱 | §3 R2-30 |
| R2-31 | HB07 | 固定产物／范围 | 直接：后端及已打包前端0b8843fb87bf0ba109f7b744f4ae96faf09df597联合部署；不含其它Android dirty | 版本、归档指纹和清单可对账，范围内failed_turn纳入，部署产物真实对应 | §3 R2-31 |
| R2-32 | HB07；SOP §8 | 完成顺序 | 直接：测试/验收后部署；必要升级前快照、等待活动工作、安全停唯一backend、保留数据与回滚 | 时间线、前置门禁与部署receipt匹配；原库/新写入保护可回滚 | §3 R2-32 |
| R2-33 | HB08 | 生产后置／精确授权 | 直接：部署后Alex当时实际置顶Conversation，两小时、无prompt，正式入口实际ref，不立即触发Turn | 生产receipt证明查询pin->ref->正式control、7200s、prompt空、future due、未测试触发 | §3 R2-33 |
| R2-34 | HB08／排除项 | 生产保护 | 直接：除目标Heartbeat不改历史/排期/微信绑定/无关配置；无故障注入 | 前后指纹/计数及精确差异，既有native定义保留，生产只授权动作 | §3 R2-34 |
| R2-35 | HB09；SOP §8 | 方法／权限 | 直接：禁止Astra，两门禁独立、测试及验收证据真实；仅hidden IAB且本审禁止一切UI/生产操作 | 本审只读产品、隔离取证；独立Validation与receipt核验，缺口如实记 | §3 R2-35 |
| R2-36 | 根规则／07 §3／SOP §8 | 质量与证据 | 直接：冻结质量检查、PM/runner隔离测试、范围内真实接口代表证据不由mock替代 | 检查版本/范围有效，真实模型协议/时间/root边界样本存在，测试预期来自上述规格 | §3 R2-36 |

判据边界与未决解释：R2-16、R2-18重点检查方向已明确但未指定具体实现函数的机制，不将“没有函数名”当作放宽理由。当前无须新增产品口径；认证以较新SOP §0的Authelia首尔现状为准，不将06旧Cloudflare Access模板要求重施生产。UI样式实测属于独立Validation；Verification检查固定源码/产物及有效实测证据。生产后置R2-30–34可先标未完成，再以实际receipt闭合，不伪造前置已完成。


## 3. 逐条实现证据

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| V01 | `secretary/heartbeat.py:17–31`；`heartbeat_store.py:21–26`；`hermes_cli/heartbeat.py:111–120,185–192`；host `scheduler_host.py:66–69` | enabled_for_db按目标DB作用域读全局；cold测试中目标开/本地关/启动home关仍只目标执行；原生反分支验证 | `tests/tui_gateway/test_cold_heartbeat_host.py:27–51`；`tests/secretary/test_conversation_heartbeat.py:139–158`；开发`tests-storage-final.log`、`tests-final-runtime.log` | 符合：局部参与和启动home不决定目标资格 | 坏配置读失败关闭，不伪称全局读取成功 |
| V02 | `secretary/heartbeat.py:9–40`→manager `due_prompt:259–268`→`session_notifications.py:307–316`→`prompt_turn.py:1258,1325` | 固定英文正文逐字核对07；真实K3请求含一条user载体，持久行相同，无周期文案 | 开发`real-summary.json`、`real-wire-1.json`、`real-wire-2.json`；`real_probe.py:103–153`；cold test L43–48 | 符合：正式模型/存储链使用规定正文 | 两个隔离真实模型样本，无生产请求 |
| V03 | claim `heartbeat_store.py:77–89`→`render_heartbeat(state.last_fired_at)`→`message_metadata.py:396–401,466–476`；timestamp guard L284,352–393 | source_timestamp为claim实际时间；wrapper首行内部时间；正式存储与wire一致；跨Profile时区定向测试 | `tests/secretary/test_conversation_heartbeat.py:153–158`；cold L43–48；`real-summary.json`两例；13文件`runtime-sha256.txt`校验全OK | 符合：单一来源时间贯通，无外围重复时间 | timestamp whole-second呈现，底层epoch保留原精度；无长期漂移宣称 |
| V04 | manager `set:212–227`统一strip；`secretary/heartbeat.py:37–40` | 原生CLI/Gateway控制非空条件仅关闭分支；空/空白省额外段；非空顺序保持；真实empty/extra样本 | `tests/hermes_cli/test_heartbeat_noting.py:28–98`；`real-summary.json`；正式wire两例 | 符合：空prompt合法且基础正文完整 | 用户输入首尾空白沿原生strip规则 |
| V05 | `secretary/heartbeat.py:13`；正式native submit/结束链 | 运行路径仅模板出现HEARTBEAT_OVER；无新增字符串消费者或过滤；真实模型分别回复HEARTBEAT_OVER及额外内容+结束文字，均按普通Turn落库 | `real-summary.json`；`prompt_turn.py:1325–1380`；全范围diff | 符合：没有结束标记运行语义扩张 | 模型是否遵循指令属实际模型结果，代码不强制替换输出 |
| V06 | `hermes_cli/web_server.py:284–285`启动既有SchedulerHost→`scheduler_host.py:98–118,168–217`→`session_notifications.py:275–326`→`prompt_turn.py:1258–1405`→native Agent | 已审冷恢复、正式prepare/invoke/settle/cleanup；真实K3/High二样本均宿主扫描进入原生UI Main；模型继承目标配置 | 开发`real_probe.py`、`real-runtime.log`、`real-summary.json`；`tests/tui_gateway/test_cold_heartbeat_host.py:27–75` | 符合：无Heartbeat独立执行器/Provider路由；正式输出、持久化及清理保留 | cold机制fixture替换模型transport、关闭部分展示回调；真实二样本补实际模型接口，用户完整体验另由Validation |
| V07 | `session_notifications.py:258–272`；`gateway/run_goals.py:128–149`；host用`_resolve_session_platform()`而非stored Messaging source | 微信持久source不改，runtime/agent为tui；已有runtime仅原生surface note追加，不重建cached root；Gateway enabled分支在claim前退出 | cold L27–75,94–110；`real-summary.json`empty例stored weixin/runtime tui；`agent/surface_switch.py`正式调用 | 符合：无伪造入站或自动Messaging发送；保持cache prefix | 原生surface note用于工具上下文转换；不改历史source/渠道绑定 |
| V08 | web lifespan host→`scan_profile`→持久`due_conversations`→专用route→host-only `BackgroundResume.background=True` | close和真实reap后新宿主恢复原stored key；无peer attach/auto-continue，runtime回收不删定义 | `tests/tui_gateway/test_conversation_heartbeat_host.py:34–63`，`tests-alias-final.log`；`scheduler_host.py:172–215` | 符合：执行资格不依赖页面、焦点或原runtime | backend停止期间不执行；后续原生scan恢复 |
| V09 | `scheduler_host.py:69–72`在Scheduler enablement判断前扫描Heartbeat；既有capability不改 | Scheduler关时Heartbeat实际运行；Scheduler工具不授予，直接调用仍scope_denied | cold L140–156；`real_probe.py`scheduler false二例 | 符合：开关独立，未借Heartbeat扩权 | fixed正文提register schedules不代表绕过当前能力开关 |
| V10 | `session_notifications.py:151–164,251–272,294–326`→既有`_session_turn_admission`、`_ensure_active_session_slot`及native submit | running/cancel/queued/estop先挡；writer拒绝在due claim前；拒绝或异常finally释放running并退款；存储异常后能重试 | cold L78–91,113–137；Conversation host L224–237；native `session_lifecycle.py:17–22,122–138` | 符合：保留用户优先与原生writer租约，未引入通用gate | 已正式admit的Turn不会因后续修改Heartbeat而新增加中断，符合原生边界 |
| V11 | `heartbeat.py:116–168,269–276,306–321`；CLI/Gateway/UI分支开关 | 开只读写secretary表，关只沿原生state_meta；native模板与非空prompt、CLI队列、Gateway adapter路径保留；native旧数据未迁移 | `tests/secretary/test_conversation_heartbeat.py:139–150`；native CLI26/Gateway相关20/TUI7项有效日志，见`evidence-index.json` | 符合：关闭保持原生，开启不导入原生定义 | 切换开关会选择两套既有/新owner数据，非自动迁移 |
| V12 | schema `secretary_heartbeats.conversation_ref PRIMARY KEY`；store init L36–44；所有manager路径共用_store | 同物理入口resolve稳定ref；Profile由DB路径绑定；控制读与pause/resume/clear均Manager | Store独立隔离/跨Profile测试L35–50；压缩控制test L111–132；`methods_session_control.py:138–203,359–376` | 符合：唯一owner与每Conversation一条受DB约束 | 物理session只是正式查找locator，无客户端ref推断 |
| V13 | CLI `_handle_heartbeat_command`/`_heartbeat_set`→manager；UI `slash.exec`→`_heartbeat_slash_session`；结构化控制如V12；成功note在`cli_commands_mixin.py:1928–1929` | 管理持久化机制及owner符合；但全局Noting开时仍无条件输出`_t("heartbeat.set_note")`，其英文声明“lives only while this Hermes process runs”；已在正式Alex RPC回执重现 | 原机制证据保留；`.hermes-dev/conversation-heartbeat-20261021/configure-alex-execution.log`的`rpc_output.output`；`locales/en.yaml:3118` | **违规（HB-V-01）**：正式设置成功输出反向否认冻结的Conversation持久性；原机制符合不能覆盖用户输出错误 | clear不可见tombstone等原结论保留；新helper/测试尚未由新独立审查者正式复审 |
| V14 | 表内active/paused/cleared；`due_conversations`仅active；宿主每次从DB扫描 | 关闭重开DB后active可due、paused/clear不due；关闭runtime后暂停/清除不复活；离开旧会话不清除 | store L122–136；host L157–166；Gateway departure L66–108 | 符合：激活持久，停服务不等于删除 | 测试重建DB/宿主的机制证据；本轮生产重启待V28收据 |
| V15 | `scheduler_host.py:110–120`route None日志后continue，resume异常日志且未claim | 独立补证真实缺失binding目标、原生max_resume_messages拒绝均不动due行/误投；修复条件后同目标执行 | 独立`test_verification.py`两例；`negative-tests.log`2通过/3.6s；非生产隔离库 | 符合：失败真实、待执行保留、可重试、不fallback到其它Conversation | 负例临时破坏仅测试DB绑定；未修改产品源码或生产 |
| V16 | due SQL＋store `claim:74–90` BEGIN IMMEDIATE；claim把anchor设实际now；CLI/Gateway enabled不claim | 两个独立DB连接屏障竞争只有一次；古老created_at一次scan仅一Turn，第二scan不补积压；native UI双driver共用同claim | Store tests L76–91；cold L27–51；`hermes_state.py:1006–1047`；CLI/Gateway放行测试 | 符合：跨连接事务排他，漏tick合并，无双宿主同tick | 允许后续真实到期tick；不把长Turn期间错过次数转积压队列 |
| V17 | store `resolve_conversation_ref`＋route自身native compression spine；继承身份实现未改 | 正式publish_compression_child保持ref，旧/新物理入口共享控制；真实session.branch、session.create、Gateway.reset不继承；父定义继续运行 | store L53–73,161–173；host L111–154、L66–108；identity L60–86,127–189 | 符合：压缩连续、new/reset/fork隔离；不复制/迁移表数据 | 使用原生compression marker/显式fork判断，未改身份规则 |
| V18 | 新`heartbeat_route.py:6–37`只查durable bindings→`_compression_path_conn`→tip binding匹配；不写peer；通用route未改 | 旧declared generation只在Heartbeat专用恢复绕过当前peer限制；原通用route仍None；switch/reset后原目标触发，新peer/source/metadata不变 | host L66–108；identity原通用route L196–228；全范围diff；store branch-marker例 | 符合：恢复证明来自既有绑定及自身合法tip，未重绑渠道或放宽其它route | 若tip无匹配绑定抛身份错误并保持待执行，不猜测其它generation |
| V19 | `hermes_state_secretary_schema.py:26–35`；store所有操作只自有表；native分支state_meta未改schema | diff核只有secretary表增量，无原生表/ownership调整，无第二对话存储；目标DB经正式scope绑定 | 35文件集成diff；runtime manifest校验13/13；store tests | 符合：规定state.db自有表机制 | 开发库由SessionDB初始化；无生产旧定义批量迁移 |
| V20 | `heartbeat_store.py:50–90`管理/claim均`db._execute_write`；revision同事务递增 | native BEGIN IMMEDIATE保证跨进程SQLite写序；没有先读后独立提交的claim窗口；双连接真实竞争证据 | `hermes_state.py:1006–1047`；store L76–91；开发`tests-storage-final.log` | 符合：同tick认领排他，不仅依内存锁 | 提交后的native执行不能与管理操作放在同DB事务内；以claim/current检查处理执行前变化 |
| V21 | immutable HeartbeatClaim revision及旧计数；`fire_is_current`检查enabled、active/revision/当前tip；refund WHERE active+revision | pause/clear/replace/resume任一后旧worker不能执行或refund；重复refund false；后续claim不覆盖；压缩claim后旧tip退款再由新tip执行 | store L94–119；host L169–181,240–261；manager L278–303 | 符合：退款只作用原未替代claim，不复活或回退新状态 | 不新增“修改定义就中断已运行Turn”的产品语义 |
| V22 | scoped sibling/原facade；API新增db/exact_session/display_kind均可选默认；既有Loop/路由保持 | 审全差异及上下游：非Heartbeat默认恢复仍follow_tip；原生CLI/Gateway开关分支保留；failed_turn只明确追加诊断；冻结10检查全通过 | integration `check-integration-final.log`31文件/10checks/health0；`tests-facade-final.log`；原native相关日志 | 符合：增量兼容与原生边界保持 | 未重跑全仓；只对本轮改变和接缝作判断，历史Noting子系统不重新宣称验收 |
| V23 | 固定Web `src/core/projection.ts:335–345`；native source content而非display伪造识别，role=user且完整锚定包装 | 正例空/extra包装；assistant/system/普通提及/未闭合/旧模板/伪造display_kind反例；UID/source对象不变 | 固定源码`src/core/timeline.test.tsx:46–103`；917前端测试通过；独立`asset-audit.json`绑定该源码与归档 | 符合：分类精确且不合成/改写source | 判断完整wrapper而非XML解析；符合给定包装合同 |
| V24 | 固定Web `src/design/chat.tsx:79–81,120–146`、theme.css；`src/App.tsx:300–350` | HeartPulse、默认foldOpen=false、固定标题、Heartbeat CSS；source附件排除、无普通user动作、NodeTime wrapper抑制；检查既有浅/暗移动/桌面/展开图片 | Web917测试；独立asset audit439文件；已读`heartbeat-mobile.jpg`、`heartbeat-dark-desktop.jpg`、`heartbeat-dark-expanded.jpg`（路径见第4节） | 符合：规定已确认卡片样式及展开内容保持 | 复用用户已确认同代码视觉证据；审查者只读本地图片，无UI操作；不当作新在线用户验收 |
| V25 | backend `turn_api_call.py:263–273`与`turn_finalizer.py:169–178`明确生成诊断后传failed_turn；通用tail helper仅显式display_kind；固定Web `projection.ts:338–341`/`terminal-history.ts:92–110` | 两分支无模型partial才标该行；有partial/模型相同措辞不标；user-tail不加行；old history不迁移；terminal metadata只恢复真实输出，slash command仍assistant | `test_turn_finalizer_final_response_persistence.py:533–660`18通过；`test_close_interrupted_tool_sequence.py:76–98`；Webtimeline/controller-terminal-history测试，917通过 | 符合：来源标记与显示边界精确；无整个Turn/正文猜测 | 既有retention有一条baseline失败，详第5节；本轮未更改其路径，未伪报该整套通过 |
| V26 | 准备脚本明确首尔`/home/ubuntu`/唯一Web服务+既有Gateway；相同/static与API入口；代码未改双SPA/auth/skew/stale入口 | 源码/发布脚本审查保持已有部署拓扑和guards；无依赖/认证/CORS变更；实际回环/公网版本及双SPA结果待receipt | 开发`deploy.py`；固定diff；冻结SOP §0、§8；第6节 | 发布准备符合；**部署事实后置待补证**，不阻断当前代码门禁 | 未通过SSH、浏览器或生产接口自行验证；不从匿名302推成UI PASS |
| V27 | `frontend-manifest.json`固定0b8843f；deploy解包后逐439文件核验；源bundle固定f32；Android dirty不进入源码/包 | 独立重新计算归档SHA与439文件SHA，关键10源码/测试/build输入与固定git版本逐字比；既有917/TS/build日志匹配release目录 | 独立`audit-assets.mjs`、`asset-audit.json`；归档SHA `89e05ae6de4ea4d716f31f9202a58069e1e2ec27738bb7bd5808d47da1eb3458`；开发manifest | 发布准备符合；**真实部署版本/产物后置补receipt** | 无重新构建或引入Web工作区dirty；既有构建chunk-size提示不影响本轮 |
| V28 | 审`deploy.py:39–75,80–173`静稳→三库快照/quick_check→固定PM/lock/config/SOUL→停服务→精确版本与dist→重启→保护指纹/绑定核对 | native active_list/Gateway active_work、DB Turn lease/Noting检查；备份受限配置/库；保留旧源码SHA、旧静态目录和新写入；依赖不变检查；无自动恢复旧DB | ignored准备脚本；主会话提交源bundleSHA `7d88ddf519f9971c94f2da5023e75613b58f0e6a5cd7fa6ccf98674168108cd0`；冻结SOP | 发布准备符合；**静稳/备份/重启/回滚点真实receipt后置补证** | 审的是准备机制，不声称部署已发生；上传不代表运行通过 |
| V29 | `configure_alex.py`：只读Alex当前pinned/非archived→唯一ref→正式session.resume/控制读/slash every2h/控制读→保护对账 | 脚本拒绝多owner歧义，0prompt/7200/active/fire_count0；对比历史/排期/绑定/其它Heartbeat，记录next_due；尚未执行 | ignored `configure_alex.py`；部署后的`alex-heartbeat-receipt.json`待提供 | **证据不足：后置实际动作尚未发生**；按用户“验后部署再配置”的顺序不阻断进入Validation，最终完成前必须补审 | 不以脚本正确代替实际设置；不提前触发Alex真实Turn |
| V30 | 独立阅读契约、报告白名单及本轮隔离取证；parent授权门禁顺序 | 本审查未spawn、未浏览器/桌面操作、未访问生产；只改本报告与ignored目录；补2例遵指定runner+显式PM Python；真实样本已审隔离Profile | 本报告/独立negative-tests.log及开发real_probe.py；baseline/index；第6节交接 | 符合：无显示状态变化、生产故障注入或提前真实Heartbeat；禁Astra沿指定角色执行 | Validation必须另一独立Agent；审查者不能代签后续结果 |


### 第二次独立全范围复审矩阵（ed94619）

各行判据原文及必要不变量见第2节R2表；以下代码位置为待审 `ed94619da81547bcb9e27aab60b608b2310e6890`。证据短名均是第4节定义的精确文件/范围；旧V表保持历史，不代表本轮当前判定。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| R2-01 | `secretary/heartbeat.py::ui_heartbeat_enabled`；`heartbeat_store.py::enabled_for_db`；`scheduler_host.py:66–69`；CLI/Gateway/UI各入口 | 静态追目标DB scope与全局开关；cold fixture的启动Home关闭、目标开启且local off仍执行 | E的tests-storage-final/tests-final-runtime日志；`test_target_profile_timezone_is_used_when_caller_scope_is_another_home`；S | 符合：资格来自目标全局，不从local/启动Profile | 坏全局配置日志后关闭，不声称读取成功 |
| R2-02 | `heartbeat.py::HEARTBEAT_INSTRUCTION/render_heartbeat`→manager `due_prompt`→`_maybe_fire_tui_heartbeat_tick`→`_run_prompt_submit` | 英文与07原文逐字核对；真实wire中一条user完整wrapper与持久载体相同，回复结束文字保留 | M的两份real-wire、real-summary；S的service-wire与历史 | 符合：正式模型输入和落库使用规定基础正文 | 真实模型是否每次遵循结束文字不作绝对承诺 |
| R2-03 | `heartbeat_store.py:claim`→`render_heartbeat(state.last_fired_at)`→`message_metadata.py:build_user_wrapper/user_input_timestamp_marker` | claim时间为source_timestamp；目标时区测试上海；wire/持久carrier单timestamp且相等 | `test_cold_messaging_heartbeat_runs_ui_platform_and_target_profile_with_local_noting_off`；E tests-edge；M/S | 符合：实际发生时间沿可信载体保留，外包时间抑制 | 字符串呈现至秒，epoch保留精度；不声称长期钟漂实测 |
| R2-04 | `HeartbeatManager.set`统一strip→`render_heartbeat` | 空、空白、省略与extra顺序测试；实际WS空白输入；真实extra LANTERN_GREEN输出 | `test_empty_prompt_and_native_template_follow_global_switch`、`test_extra_prompt_is_text_inside_existing_wrapper`；M/S | 符合：空段省略、基础正文完整、间隔仍独立 | 首尾空白沿原生strip；无额外转义产品要求 |
| R2-05 | `secretary/heartbeat.py`唯一结束语引用；native `_run_prompt_submit`与Agent loop | 审全部运行diff无新增token消费者；真实普通回复/extra+结束字均保存 | M/S两组模型证据；全范围diff | 符合：HEARTBEAT_OVER未引入新静默/调度/授权 | 只核本轮增量与正式链，不把模型遵循等同新执行器 |
| R2-06 | `web_server.py`既有lifespan启动SchedulerHost→`scan_profile/scan_heartbeats`→`resume_session`→`_maybe_fire_tui_heartbeat_tick`→`_run_prompt_submit:1258`→`_invoke_agent/run_conversation` | 逐段追正式resume/prepare/admit/invoke/settle；实际serve自动自然到期执行 | `test_close_or_actual_reap_then_new_host_recovers_same_conversation`；M；S journey/service_launcher/service-summary | 符合：无独立Heartbeat Agent/执行器，复用原生宿主入口 | cold底座替换模型transport，S/M补真实接口 |
| R2-07 | host-only native `_Resume`与`_session_profile_runtime_scope`；`_notif_prepare_ui_heartbeat_surface:258`；native prompt turn | 目标test/b与目标Home机制测试；同一Agent既有root不变，surface note追加；真实High/K3 wire与root/tools相等 | `test_existing_messaging_surface_becomes_ui_without_rebuilding_root`；M/S；A runtime hashes | 符合：模型/Profile与缓存前缀沿原生，正常持久/流式/终态链保留 | 未新增所有Provider实测；保持既有路由无需穷举模型 |
| R2-08 | `scheduler_host.scan_heartbeats:115`以UI source恢复；`_notif_prepare_ui_heartbeat_surface`；Gateway `run_goals`提前退出 | 原weixin source持久不变，runtime/agent tui；新peer无carrier，无adapter调用 | `test_gateway_departure_keeps_old_conversation_and_does_not_rebind_peer`两变体；M heartbeat-empty | 符合：Heartbeat不伪装入站，不重绑或自动渠道回复 | 虚构peer机制测试与真实模型样本，无真实微信发送 |
| R2-09 | 持久表→`scan_heartbeats`→host-only detached `_Resume`；关闭/回收不清definition | 实际runtime close/断WS后自然扫描；TTL实际reaper函数；成功note明确关页/切换持久及服务前提 | host 15项；S close/lifecycle/service-summary；`heartbeat_set_note`与新receipt测试 | 符合：不随页面/runtime销毁；用户说明已同步真实生命周期 | 不承诺后台停机执行 |
| R2-10 | `scan_profile:69`先scan_heartbeats再查Scheduler；能力门禁未动 | 目标scheduler=false仍UI执行；真实wire无scheduler；正式工具调用scope_denied、排期0 | `test_heartbeat_does_not_grant_disabled_scheduler_capability`；S | 符合：独立开关，提示不授予关闭的Scheduler能力 | 不扩大Scheduler配置语义 |
| R2-11 | UI `_notif_ui_heartbeat_held/_notif_claim_turn`；DB `claim`；CLI watchdog/Gateway poll enabled skip | running/cancel/queued busy不claim；解除后一次；两DB连接同tick一次；实际停机148.58s只合一次 | cold heartbeat busy测试；store concurrent；S process-restart-history | 符合：用户优先、busy等待、漏tick合并、跨入口不重复 | 不把当前已经开始Turn定义变更解释成新增中断权限 |
| R2-12 | `HeartbeatManager`native state_meta分支；CLI/Gateway/UI false分支；`migrate_heartbeat_to_session` | native prompt非空、原模板/执行路径，开启另写表不改legacy；切回false读legacy | `test_native_definitions_are_preserved_without_automatic_migration`；E native26/Gateway/native tick7 | 符合：关闭原生、保留native数据，无自动迁移 | 只检查适用Heartbeat原生分支，不重测全Hermes |
| R2-13 | `secretary_heartbeats.conversation_ref PRIMARY KEY`；store init `resolve_conversation_ref`；DB ownership scope | 双Profile相同Session ID与同Profile双Conversation交错；各自prompt状态隔离 | `test_two_conversations_and_profiles_are_independent`；S实际A/B/C | 符合：唯一owner是Profile DB+稳定ref | 引用规范身份库，无新registry |
| R2-14 | UI `_heartbeat_slash_session`识别heartbeat/hb并正式落库→CLI handler→manager；Gateway handler；`methods_session_control.py` | every/status/pause/resume/clear正式入口；新空draft的alias正式接线；成功note true/false覆盖 | E tests-alias-final；新tests-receipt-final27；S公开WS；`test_cli_set_receipt_describes_selected_lifecycle` | 符合：统一owner、无孤立helper；HB-V-01本地关闭 | 新正式WS文案由独立Validation补用户入口，不靠生产重set |
| R2-15 | store `save/set_status`；manager pause/resume/clear；structured controls | pause留定义、resume更新last_fired_at重新计时、clear墓碑对外null；其它owner保持 | store测试；S pause/restart/resume/clear与B全字段对账 | 符合：可管理定义被清除，内部墓碑不代表有效definition | 不要求物理DELETE；不把created_at未改视作恢复失败 |
| R2-16 | `heartbeat_route_conn`只遍历durable bindings、native compression path并校验tip owner/排除child；host exact_session | 旧generation通用route None而专用route原owner；压缩tip执行；当前新peer无载体 | gateway departure两变体；compressed controls；branch marker测试 | 符合：从已证绑定恢复自身合法tip，不借焦点/peer | 不放宽通用resolver；无任意Session猜测fallback |
| R2-17 | `due_conversations`只查active；原生DB重开；每次扫描新读 | 服务真实停机跨2due、新进程无WS恢复一次；paused/cleared跨重启跨due无载体 | S service-summary/lifecycle与HTTP histories；store restart测试 | 符合：active持久恢复，paused/cleared不复活 | 实际服务必须运行；无任意机器断电保证 |
| R2-18 | `scheduler_host.py:110–120`无route警告continue，恢复异常警告；claim前未消费 | 两隔离负例损坏绑定/原生恢复guard拒绝，断言warning、due不变、无错误目标；恢复条件后成功 | N test_verification.py两项与negative-tests.log 2 passed | 符合：失败真实报告、待执行保留、无错误fallback | N改隔离fixture非生产；日志为后台真实失败载体，无新UI通知承诺 |
| R2-19 | store owner resolve；`heartbeat_route`native `_compression_path_conn`；migration true仅确认ref | 原/新段公开control相同、交错pause/resume/clear；再arm只tip执行；claim后压缩退款再投tip | `test_compressed_physical_sessions_share_public_controls`、`test_compression_after_claim_refunds_old_tip_and_next_scan_runs_new_tip` | 符合：合法压缩不复制状态，物理段读同owner | 使用原生publish_compression_child持久接缝，非模型压缩新请求 |
| R2-20 | 原身份new/reset/branch路径未复制表；绑定仅现owner；原definition不清 | 实际new/branch_stored；UI branch、Gateway reset/switch；fork inherited marker压缩 | S公开RPC；host tests；store branch compression测试 | 符合：新身份无父设置，旧owner保持 | 继承原身份rewind/分支契约，本轮未改它 |
| R2-21 | 新heartbeat_route模块专用；general `resolve_conversation_route`未改；host exact_session仍_resume_guard | 源码追仅专用Heartbeat调用；old route仍None；peer路由/metadata/source前后一致 | gateway departure测试；N guard拒绝；全diff | 符合：old generation不删除旧Heartbeat，且未弱化其它模块安全 | 不把专用恢复扩成Noting/Scheduler公共路线 |
| R2-22 | `hermes_state_secretary_schema.py:26`新增自有表；`ConversationHeartbeatStore`使用现DB | diff只加Secretary表；native tables/schema/ownership不变；无外库 | schema与store；E runtime manifest；A hashes | 符合：state.db自有增量、原生owner不变 | 开发期无生产旧native迁移 |
| R2-23 | store所有mutation经`db._execute_write`；claim事务重读due/route再update revision | 两独立SQLite连接屏障并发仅一claim；manager每次读DB；唯一ref约束 | `test_concurrent_managers_on_separate_connections_claim_once`；E tests-storage-final | 符合：原子事务协调，并发同tick只一次 | 无通用新admission gate；非长期负载压测 |
| R2-24 | claim revision；fire_is_current比status/revision/tip；refund WHERE active AND revision | replace/pause/resume/clear交错旧claim，拒执行/退款；refund一次；后claim不被旧退款覆盖 | store四变体+exactly_once；host pause-after-claim、compression-after-claim | 符合：晚退款不能覆盖后续操作或复活状态 | 新操作晚于正式Turn接受时不强制撤销已运行Turn，沿原生契约 |
| R2-25 | `_notif_claim_turn`原生history admission；`_ensure_active_session_slot`writer lease；submit false/异常finally release/refund | lease拒绝原surface不变；busy/queue不执行；storage error不留running、下次可恢复 | cold heartbeat lease/refund测试；host storage failure | 符合：用户优先、原生租约和资源关闭完整 | 锁/租约仍由原owner管理，未增全局gate |
| R2-26 | 新模块sibling、facade新增可选db/timestamp/keyword display_kind；Profile-aware scope | 审全增量与调用者，原必填/返回/默认保持；非enabled native tests；无env/模型route变化 | 全范围diff；E native+facade+provider tests；freeze checks | 符合：增量兼容原生接缝，坏所属配置日志fail closed | 不重审无变化Noting内部；不以分区指导新增规则 |
| R2-27 | fixed frontend `core/projection.ts:343–345`→App timeline kind→Message | 仅user完整raw wrapper正则；source/uid保持；固定测试正反例覆盖assistant/system/plain/old/forged display | fixed `core/timeline.test.tsx:46–105`；F 439全文件一致 | 符合：分类有明确原文边界，不合成消息 | 不根据HEARTBEAT_OVER猜类型 |
| R2-28 | fixed `design/chat.tsx:80–81,120–151`、tokens:40–42、theme:239–246、App attachments/reply/NodeTime | fold state false、HeartPulse、主题陶土橙、同类结构；NodeTime排除carrier；展开只投inner text | fixed component测试；既有浅/暗360×792及1280×800截图与Validation S17；F/A | 符合：固定版本样式/内容/操作边界有源码和同产物有效视觉证据 | 本审无浏览器/桌面；复用用户已确认同版图，不声称新线上UI |
| R2-29 | `turn_api_call.handle_api_interrupt`与`turn_finalizer._resolve_budget_fallback`明确生成诊断时标记→`close_interrupted_tool_sequence`；fixed projection failed_turn | 审仅tool tail原本应补row时标记；模型partial分支不标；no user-tail新行；fixed取消terminal派生card但保持恢复metadata | paired agent tests、`.hermes-dev/failed-turn-20261021/`18项针对证据；fixed timeline tests | 符合：来源标记准确、无正文推断/历史迁移，部分回答/slash保持 | 既有retention缺帧失败保留为基线范围外，不宣称全仓绿 |
| R2-30 | SOP首尔ubuntu单backend双SPA；原生guard未改；deploy/post-release现有服务路径 | 最终ed Web health、Gateway running；双SPA与关键资源HTTP200、两index有原生token；匿名302到Authelia；两服务active/running且NRestarts0 | E/deployment-receipt.json、post-release-readonly.json；A-post | 符合：目标首尔、单backend同源与认证/原生guard边界保持，实际运行版本正确 | 没有新线上UI视觉、手机或WebSocket抓包结论；接口不冒称UI PASS |
| R2-31 | HB07固定前端0b8843f、后端ed94619；manifest与精确发布 | 最终receipt对应ed，frontend commit/归档SHA/439文件均匹配；关键JS/CSS实际HTTP SHA等于manifest，未含Android dirty | E/frontend-manifest.json、最终三receipt；A与A-post | 符合：固定配套产物实际联合发布，不只是准备打包 | 前端176构建输入/已有测试按原精确版本复用，不重构建 |
| R2-32 | deploy preflight idle/leases/Noting→snapshot/config/SOUL→安全停既有服务→固定版本/产物→重启及对账 | 新前置Verification及18:19 Validation通过后，18:21:17补发版；receipt old=f32、target=ed；PM3.14.8、lock/pyproject SHA与本地一致、依赖diff空；备份及旧static恢复点明确 | E/deploy.py、deployment-receipt.json；新版Validation；A-post | 符合：验后发布顺序、唯一backend安全升级、原库/新写入保护及配套恢复点满足SOP | 未实际演练生产回滚，无自动旧库覆盖，不声称做过故障注入 |
| R2-33 | 初始configure_alex正式唯一pin→ref→every2h；新版正式control.read只读保持 | 同ref conv_8dc89e12cc9b42b5a77986f4d9b02cec／stored 20261011_223115_59ad08；7200/空prompt/active/count0/revision1及原created/lastfire全同，next_due=1792583889.5657868 | E/alex-heartbeat-receipt.json与alex-heartbeat-final-readback.json；A-post | 符合：初始设置在部署后正式成功，新修复部署不重set、不重锚，19:58:09保持 | set_called=false、production_model_requests=0；不提前等到期或主动触发生产模型 |
| R2-34 | deploy protected全行SHA及config/SOUL指纹；微信ref；新版含secretary_heartbeats | host/alex/study各messages、schedule、pending、bindings、aliases及heartbeats六表前后SHA/行数全同；config/binding保持；Alex formal control与初始逐字段相同 | E最终deployment/post-release/Alex readback；A-post24项核验全true | 符合：原历史/排期/微信/配置及已登记Heartbeat均保护，生产无额外测试/故障注入 | 收据时count0不承诺永远不触发；未来自然due按既定用户设置执行 |
| R2-35 | 本审只读产品、写白名单报告与ignored证据；独立gate按冻结执行 | 全新独立起点先正式落盘、后查实现；sol/high无再派生；仅本地证据，无browser/生产 | 本报告第2/6节；A；独立Validation报告 | 符合：执行边界与审查独立性可核，未冒称另门禁已通过 | 独立Validation及最终生产动作由各owner完成 |
| R2-36 | 官方PM `.venv`+runner；冻结10checks；真实模型wire与版本指纹 | E有效154+新增2=156定向项；ed27针对复测及4文件10checks health0；A13运行文件commit与working SHA全一致；M/S真实接口 | E evidence-index/tests-receipt-final/check-receipt-final；A；M/S | 符合：可复用证据匹配待审机制，预期来自冻结行为，未以mock冒充真实接口 | 未复跑无关大套；两新note文件变化仅helper/reexport，审diff确认不影响旧真实链 |


## 4. 核心目标及验证方法审查

核心纵向路径已落实：正式slash/结构化控制→Profile state.db稳定ref→持久扫描→自身合法压缩tip→既有UI恢复与writer租约→原生prompt submit/Agent→持久user载体与真实模型输出。原文未指定恢复函数名，但明确的“绑定不因Gateway丢失”没有弱化成当前路由恰好有效才执行；专用route只复用已有durable绑定和native spine，原Scheduler/Noting route不变。管理与认领均原生写事务，claim/refund revision fencing覆盖新操作和tip变化。

证据可信度与边界：

- 读取开发16文件154项有效定向日志及各测试底座，不相加历次重跑冒充独立测试数量；最终`tests-alias-final.log`覆盖已修正/hb正式入口。13个runtime SHA已由独立`shasum -c`核验全部OK，产品源码相对指定f32无dirty。真实二样本源码SHA也与最终runtime manifest相同。
- 冷恢复fixture通过真实SessionDB、native resume、native AIAgent、native submit/持久化运行；替换最底层模型transport、禁网络、关闭自动压缩及部分display/housekeeping回调。它足以证明owner/接线/认领，不足以证明实际模型接口或完整UI体验。主会话两次实际K3-256k/High请求HTTP200补接口证据，empty Messaging source和extra UI source均从持久scan进入正式Main，无生产访问；后续真实用户验收仍单独执行。
- 对测试可能漏掉的错误实现主动反证：若仅当前peer route有效才允许恢复，则Gateway switch/reset例失败；若按物理Session存储，则压缩旧/新控制及branch例失败；若依内存去重，双独立连接屏障例失败；若refund忽略revision，四管理交错例失败；若恢复异常改投焦点，独立两个负例失败。新增2例均在ignored隔离目录，规范runner结果2通过/3.6秒，不复跑大套。
- 前端由固定归档SHA和439个文件SHA校验，不使用当前Android dirty源码。独立核对10个关键源文件/测试/build输入与固定前端commit；完整176输入对应证据复用manifest；917通过/1skip、TypeScript和生产构建来自该release目录。读已有浅色移动、暗色桌面及展开截图确认固定标题/折叠/宽度/配色/内层timestamp，无新的UI操作。图片目录：`/Users/edgar/.codex/visualizations/2026/10/21/01a15d70-fbb7-7190-b233-211cd9270a42/`。
- 质量证据为最终31代码/测试文件冻结10检查，health 0 blocking/0 advisory；不改检查阈值或豁免。Mac机制证据及真实模型接口已覆盖本轮平台无分支代码；Linux实际服务启动/版本/保护数据由发布receipt补证，不以本地证据冒称生产结果。
- 原生关闭分支、CLI/Gateway/UI正式入口、Profile隔离、busy/Stop/queued、writer拒绝、submit异常、storage异常、旧generation、压缩/fork/reset、服务/宿主关闭和退款均有源码及匹配证据。Noting child/Notebook/Scheduler其余全量产品能力不在本轮重做范围；本轮未改其指定机制，不借引用旧证据扩大声明。


### 第二次复审的证据与方法

E=`.hermes-dev/conversation-heartbeat-20261021/`：evidence-index.json及其逐文件日志，最终156有效项（初154+新增note两分支2）；ed的tests-receipt-final.log为27项/9.3s，check-receipt-final.log为4文件冻结10检查、health 0 blocking/0 advisory。未改31文件整合检查check-integration-final.log有效，本轮未为review重跑大套。

M=E中的real-summary.json、real-request-summary.json、real-wire-{1,2}.json及real_probe.py：两个隔离K3-256k/High HTTP200，原weixin/extra两种真实接口代表链。S=`.hermes-dev/conversation-heartbeat-validation-20261021/`的真实serve、HTTP/WS、service-summary、wire和history原件：新进程、无WS、自然tick、停机跨两due合并及pause/clear恢复。它们对机制的旧结论可复用；新note用户输出仍由新独立Validation实际RPC复验。审查了捕获器/受控底座：M/S只观察真实请求，不替换模型输出；cold fixture明确替换transport，不能独立证明模型接口，因此组合真实样本。

N=`.hermes-dev/conversation-heartbeat-verification-20261021/test_verification.py`与negative-tests.log：两项原独立反证，使用真实隔离DB/UI路径，缺绑定或原生resume guard拒绝后保持due、不误投，恢复条件后可执行。ed未改其运行路径，复用2 passed，无须复跑。

F=固定前端0b8843fb87bf0ba109f7b744f4ae96faf09df597、E/frontend-manifest.json及原审查者unpacked/dist；A=本次`.hermes-dev/conversation-heartbeat-verification-r2-20261021/evidence-audit.json`，独立重核13运行文件的working与ed提交SHA，以及439前端文件均一致。M与ed的两个文件SHA不同，已审f32→ed精确diff仅新增成功note helper/导出，不改变render、claim、host或真实模型路径；其余样本运行文件SHA相同，因此复用有明确影响界限。

D=E/deployment-receipt-initial.json、post-release-readonly-initial.json、alex-heartbeat-receipt.json及deploy.py/configure_alex.py：本审只读已发生初始生产事实，绝不自行连接生产、调用set或模型。新发布receipt尚未发生，仅保留后置状态。固定UI有效浅/暗同产物截图和组件测试由原Validation S17已核；本审只查源码/固定产物，不操作任何显示。

主动反证核查：遗漏global目标作用域会被双Profile冲突配置暴露；仅跟焦点会被旧generation/close/reaper场景暴露；先读后写claim会被双真实连接屏障暴露；无revision退款会被四种交错操作暴露；以持久definition存在冒充恢复成功会被N日志/无carrier/条件恢复断言暴露；只检查DB会漏success note，故此次独立审完整CLI用户输出，并以新两分支输出测试关闭旧项。未发现新增核心机制弱化。

## 5. 发现、整改优先级与范围外项

### 初审更正时历史发现表（状态为当时记录）

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| HB-V-POST | V26–V29；发布及Alex真实设置 | 初审后已部署f32/固定前端并正式设置；已收`deploy-execution.log`及`configure-alex-execution.log`，原“尚未执行”仅为初审时点 | 当前不是未部署阻断，而是HB-V-01待修；最终交付仍需对修复版本及保护状态补审 | 保留f32已有日志，修复后新审查者核最终上线版本与既有7200/空prompt定义未重设、排期/历史/绑定未变 | 已收首版真实收据，最终版本待复核 |
| HB-V-01 | V13关联V08/V14；07 §8.15 L1466；`hermes_cli/cli_commands_mixin.py:1928–1929` | 全局Noting开时正式CLI/UI slash设置成功仍显示原生进程生命周期note；生产RPC输出已证实；manager实际持久状态正确 | P2，范围内用户输出与持久化语义冲突，阻断本轮最终交付；不表示定义/排期已丢失 | 接受主会话最小提案：按目标Profile全局分支选择成功note，false逐字回原生note，true说明Conversation持久保存/后端运行前提/管理命令；正式CLI两分支输出测试、冻结检查、新独立全范围复审及最终发布读回 | 初审更正当时开放；提案认可，尚未关闭 |
| HB-V-OOS-01 | V25证据边界；既有`test_failed_turn_retention.py:345` | `.hermes-dev/failed-turn-20261021/baseline-retention-tests.log`在既有基线同样发生terminal-complete缺帧断言失败；本轮未改该模块/路径 | 范围外既有失败，不作为本轮增量缺陷；禁止声称该整套通过 | 主会话保留基线证据；如另行处理，独立登记，不借本轮放宽断言 | 已标记范围外 |

初审更正时的范围外发现如上。当时新增范围内HB-V-01必须关闭；初审前置通过是原时点结论，不再作为最终门禁通过依据。最新缺陷状态以本节后续第二次复审表为准。


### 第二次独立复审最终发现状态

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| HB-V-01 | R2-09/14；secretary/heartbeat.py::heartbeat_set_note；CLI _heartbeat_set | f32成功note错误；ed正式调用按全局分支选择新持久说明，false逐字返回native_note | 原P2输出缺陷；本地实现已符合，不再阻断前置门禁 | 已审ed diff及27项/10check；新独立Validation与补发版后置收据继续完成 | 已关闭：ed代码、真实HTTP/WS用户入口及最终部署收据均补齐 |
| R2-POST | R2-30–34 | 初始f32发布/设置与最终ed补发版三收据均核；A-post24项全true | 原后置缺口已消除，无最终阻断 | 最终实际版本/439前端文件/三库保护/原Alex定义和锚点证据完整 | 已关闭 |

没有新增范围内产品缺陷；原报告已记范围外基线失败保持历史，不扩修。

## 6. 修复与独立复审

2026-10-21初审：先独立提取30条判据落盘，向主会话集中交回该里程碑后，才接收并读取f32实现/证据/动态看板。第2节原判据未降低或改变。初审时未要求代码修复；后续生产回执发现的HB-V-01及独立复审要求记录如下，覆盖原“无需新审查者”的当时判断。

关键研讨链：原判据V26–V29要求真实部署/正式设置事实→冻结用户明确要求“测试验收后部署，再设置Alex”→主会话提出将发布准备纳入前置审查、真实执行receipt在部署后补审→Verification认可该阶段顺序，不把未发生动作写成符合，也不以它阻断前置代码门禁→本报告明确区分前置通过和整轮最终Verification待补，无规格变更。主会话补齐准备脚本的PM/lock指纹与依赖差异检查、受限config/SOUL备份后，审查者已重新读取相应脚本；这些是既有SOP的工程落实，未改变原判据。

供final-delivery摘要：Conversation Heartbeat持久owner、旧Gateway generation专用恢复与条件退款已独立审查通过；独立补2负例通过；固定前端439文件核验一致；整轮完成仍等待真实部署及目标设置收据。后续收到receipt只补审V26–V29及其相关影响，不重跑无变化大套，不提前宣称目标完成。

### 生产回执发现与提案评审（2026-10-21，HB-V-01）

1. **原判据与发现：** V13要求正式管理入口完整符合Conversation语义，V08/V14要求离开/关页不清除、重启恢复；主会话在实际Alex设置RPC中发现成功输出仍声称仅当前进程存续。审查者读取该原始执行日志及f32调用点，确认冲突，并更正原V13判定。初审机制测试未断言成功输出note，这是证据覆盖遗漏，不能用实现存储正确否定用户输出问题。
2. **实际状态：** 已收执行日志显示f32后端、0b8843f前端439文件已上线；Alex定义为7200s/空prompt/active/fire_count0，next_due已登记，保护历史/排期/绑定对账保持。此处只陈述已读日志中的观察，不因此最终关闭V26–V29或本轮目标；正式定义不重设、不触发测试Turn。
3. **主会话提案：** 在`secretary/heartbeat.py`新增选择成功note的helper，CLI原行调用；按目标Profile全局Noting分支，关闭时逐字返回调用方原生note，开启时用英文说明按Conversation保存、UI后端运行时后台执行及管理命令。只改该说明，不改模型模板、调度、持久化或当前生产定义。
4. **Verification评审：** 认可为既有授权内必要修补，无须变更规格或用户补写文案。helper应复用既有全局enablement及正式目标Profile作用域，不能误看局部/noting、启动home或另立配置。false应直接返回传入的原生本地化note，避免翻译/空白/字节差异。true不得许诺后端停机时执行；应明确切换/关页不删除与重启保留，并列原有pause/resume/clear。已看到工作区出现符合该方向的未提交helper和测试，但此评审只认可方案，不作为修复代码通过。
5. **关闭证据：** 正式`CLICommandsMixin._heartbeat_set`捕获输出的两分支行为测试；true有持久性/后端前提且无原生进程限制，false末行与既有`_t("heartbeat.set_note")`逐字相同；核实际CLI接线及目标Profile全局策略，冻结相关检查通过；新无实现上下文独立审查者重新提取全轮判据、全范围复核并核旧发现；后续Validation与最终发布补证沿原套件执行。模板/调度未改，不因此重复昂贵模型样本。上线后只读核既有Alex定义/时间锚和其它数据保持，禁止再次every设置而重锚其next_due。
6. **当前结论与交接：** 无规格变更；HB-V-01开放、最终Verification不通过。主会话负责修补/验证/发布，新独立审查者负责修复后全范围复审。本审查者未改产品代码。final-delivery及面向用户汇报须主动说明“生产设置已成功，但发现设置成功提示沿用原生临时生命周期说明，已按Conversation持久语义修正并重新审查”的实质收敛及最终证据，不能只埋于子Agent记录。


### 第二次独立全范围复审前置时点历史（2026-10-21，待审ed94619）

新审查者 heartbeat_verification_r2，sol/high，不再派生。先完整读两技能及冻结索引、指定规格；独立36条草稿落ignored，协调旧审查者停止写报告后，正式追加第2节，再读取实现/测试/旧报告/动态看板。读取baseline定位时不可避免见其附带执行摘要，已经明确排除，未将其作为判据/事实；过程留存criteria.md与verification-before-r2.md。第2节独立起点未因代码或旧结论降低。

全轮范围已重新核查，不局限HB-V-01：模板/单时间、目标Profile、local与Scheduler边界、UI正式Main链、来源与缓存、所有管理入口、持久恢复、新旧身份、专用合法tip、失败可重试、原生writer、并发claim/退款、原生关闭、固定前端/failed_turn以及发布后置均逐项有R2矩阵。31条前置符合，5条明确后置待新版生产事实。

旧发现研讨链复核：原V13/V08/V14持久语义→f32成功note否认持久性→主会话提仅helper+CLI原行、目标global选择且false逐字原note→本审依据独立R2-09/14核其实现与原输出两分支测试→ed94619的note准确说明后台运行前提、切换/关页保持、重启保留及pause/resume/clear。无规格变更；模型模板、调度、store未改，旧真实证据按路径复用。HB-V-01本地代码关闭。实质收敛仍须final-delivery及用户汇报明确说明初始设置成功但提示生命周期矛盾、已修正并重新审查，不能只写测试通过。

**前置时点历史结论：Verification前置通过，可进入新版独立Validation及既定补发版顺序；当时最终Verification尚未通过，等待ed真实发布receipt与既有Alex定义/next_due只读保持证据。** 不再次every、不提前模型触发，不重锚原19:58:09。补receipt后仅追加后置行及相应影响，保留全轮判据、历史结论与本次证据。


### 第二次独立复审最终后置补审与关闭（2026-10-21）

仅从本地读取最终E/deployment-receipt.json、post-release-readonly.json、alex-heartbeat-final-readback.json及初始三收据；未访问生产、模型、浏览器或重跑测试。补审R2-30–34及相关版本/权限/证据影响，结果已回写第3节对应五行。独立生成`.hermes-dev/conversation-heartbeat-verification-r2-20261021/post-release-audit.json`（A-post），24项核验全true并记录三receipt SHA；第4节A提供原13运行文件/439静态文件独立核验，矩阵其余31条结论不受本次纯note发布影响。

新版独立Validation实际HTTP/WS前置R2-U01–16通过，18:18:44审计早于18:21:17部署；true输出准确，false en/zh原native note逐字保持，6自建进程均停止，0新外部/模型请求；其后置由独立验收者另补，不代替本审结论。最终部署receipt实际Web和Gateway均为ed94619，固定frontend0b8843f/439文件及JS/CSS HTTP SHA一致，匿名认证302及服务active/running/NRestarts0、微信connected保持。备份目录`/home/ubuntu/.local/state/hermes-secretary/conversation-heartbeat-20261021/deploy-20261021T182117`及旧static入口明确；无依赖差异、PM解释器与lock/pyproject指纹匹配。

最终三库六张受保护表（含secretary_heartbeats）全行指纹一致、config/binding保持；Alex初始正式设置与新版formal_control_read逐字段相同，ref/7200/空prompt/active/count0/revision1/created_at/last_fired_at/next_due保持。next_due为2026-10-21 19:58:09.565787+08:00；set_called=false，没有重设/重锚或提前测试Turn。

**最终Verification通过：R2-01–36全部符合，0违规、0证据不足，HB-V-01及R2-POST关闭；本次完整复审没有新增整改项。** 初审漏查用户输出、失败与撤回历史保持，实质修正链必须由final-delivery及用户汇报摘要：首版持久设置成功，但成功提示错误沿用临时生命周期；已按原冻结语义修补、全新独立全轮复审/真实用户入口复验，并已补发版且保持既定Alex排期。没有新增规格或放宽判据。
