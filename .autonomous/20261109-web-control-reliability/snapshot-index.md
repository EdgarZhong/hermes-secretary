# 20261109-web-control-reliability · Snapshot Index

## 审查依据索引

本轮采用autonomous-run，审查依据仅为本索引及下列指定版本原文。baseline.txt记录冻结提交。索引自身二级；二级修改须用户明确新授权并保留版本／口径变更，不用实现结果反写预期。未改README、AGENTS及下列旧规格均已在基线树中；原算法工作区未提交文档及私人资料不在本轮输入。

| 输入类别 | 仓库实际路径／适用范围 | 修改等级 |
|---|---|---|
| 用户需求 | `docs/06-Hermes-Secretary-Web-UI-V1-Spec.md`顶部11/9Web归属、C1–C8、11/8整组折叠；11/1维护取消／流式与已有恢复／操作契约 | 二级 |
| 权威规格 | `docs/notebook-ontology-whiteboard.html`全篇；`docs/07-scheduler-notebook-noting-compaction-redesign.md`全篇（本轮主涉身份／并行／取消／Heartbeat／Scheduler／Framework，最新覆盖旧）；`docs/02-noting-system-specification.md`未替换的身份、单writer、原生ingress、ACK与cache-prefix；`docs/04-hermes-secretary-v1.5-implementation-spec.md`未覆盖增量；`docs/01-personal-hermes-v1-first-fork-iteration.md`仅保留Hermes-first／原生边界，不扩大个人化范围；`docs/08-profile-scheduler-files-clarification.md`；`docs/06-Hermes-Secretary-Web-UI-V1-Spec.md`；`docs/adaptive-noting-threshold-proposal.md`V4及明确保留V3合同 | 二级 |
| 编码指导 | 根`AGENTS.md`；`README.md`稳定目录／运行环境／文档索引；`CONTRIBUTING.md`环境参考，规则以根AGENTS冻结为准；独立前端仓`../hermes-secretary-web/AGENTS.md`按cd5d12f版本（blob 708f40eb120682607cd61de0d30a33b550a0447f）仅供其现有接口环境参考，不能新增审批／门禁 | 二级 |
| 会话确认口径 | 本索引“口径与决策”表；授权原文登记于06顶部及CLAUDE新目标段 | 二级 |

## 口径与决策

| ID | 已确认要求／边界 | 授权与定位 |
|---|---|---|
| U01 | root本人复核本会话Thinking重复、断连／静默停顿、Send／Enter Steer busy、整组折叠、移动诊断；修复所有可复现范围内代码缺陷。区分已证代码原因与未知现场原因，不许宣称已证明网络抖动。 | 用户“复查之前的问题报告，确保全部修复”“都找到了明确原因，再复查一遍”；原折叠曾暂缓，最新全部复核修复覆盖该项。 |
| U02 | 普通Turn、Instant Reminder、Heartbeat、Delegation返回、Idle自动压缩／整理及其它内部运行均必须可从Web绑定实际runtime，得到实时状态与对应输入、Steer、Stop／Interrupt／取消等完整控制。不是只收新消息，不按来源丢权限。 | 用户“Web Socket应该能连上，然后拥有所有控制权”。 |
| U03 | 唯一允许因会话占用返回Session busy拒发的情形为目标Conversation当前确由独立Gateway运行。历史wechat来源／路由／服务在线不等于Gateway活动；未知owner不能伪称Gateway，也不能抢单writer租约。 | 用户“我能允许…只有一种情况…正在gateway运行”。不授权跨进程Gateway代理或抢占。 |
| U04 | 在既有owner／原生准入下统一原子选择普通提交、当前Steer或安全边界等待；覆盖启动、结束、停止、维护与前端idle读取竞态。稳定operation identity与可查询受理状态；客户端不因busy／超时自动重发，不能吞输入／双执行。旧调用默认保持，新增可选策略／能力。 | U02/U03结果要求；工程实现沿根AGENTS原生、兼容与写恢复规则。 |
| U05 | 空闲维护期间Send先接收并显示等待，Send不暗含取消；用户另按Stop取消维护。committing等待原子发布，不能假取消已提交内容。 | 用户对异步问题明确答“先接收并等待，想取消时我按Stop”。 |
| U06 | 压缩保持独立operation身份，恢复部分摘要／真实状态，取消精确指向当前操作；普通联合取消仅对应未提交Noting，已提交保留，Force原例外保持。停止Main不等待Pending读取或冷建完成。 | 06维护流式／取消既有确认＋07取消和Force合同＋U02；不新增压缩模型／提交机制。 |
| U07 | Profile／Conversation／合法压缩lineage／native Turn／operation／epoch严格隔离，同一活父对象和既有Fanout，不造第二writer；首进／重连当前可见范围完整自动恢复，正常有序业务只局部更新，不整页刷新。 | 根AGENTS和02／04／06／07／08继承；U02同runtime意图。 |
| U08 | 保留0.1.12/13已修的有界Fanout及顺序、Unknown同片段、Enter路由、心跳失败退休、双端诊断和release可ADB导出；补本轮控制状态必要诊断。不记录正文／凭据，不由1006计算臆测网络比例。 | C1–C8；用户“两边可以对比着来”。设备未连接不能冒称真机验收。 |
| U09 | 已证结束的历史组不因活动Turn边界暂缺或Steer／接续／新Turn交接全部展开；未知边界后续确证同页收敛，无须刷新。活动Turn仍展开、正文边界／用户手动展开状态保持，不把当前内容误折。 | 11/8折叠合同＋用户11/9最新再次复现“所有的折叠都消失掉了”，怀疑Steer接续但不排除其它入口＋U01。此后继明确报告强化旧永久清空条款，不改历史快照判定。 |
| U10 | 合入最新自适应候选b232defac76ab3c0a2d0dcf389cbc6cc6707d54f的V4 R4到main，与修复一起发布并验线上实际接线／配置／自然运行。保hot/standby、首次HB缓存guard、首读一次许可／成本、用户/Reminder输入事实和来源；接收等待不再伪记blocked_send。 | 用户最新“把自适应算法分支…合并到main一起发布，确保…生效”。替代上一算法轮次仅本地授权；不重写原负结果／敏感性结论。 |
| U11 | 正式仅main，Web与新版原证书APK联合发布；保护运行数据库、绑定、模型配置和他人dirty。两套完整三库备份保留；源码／构建／HTTP／进程版本逐一核。 | 用户明确上线、新APK与联合发布；根AGENTS部署规则。 |
| U12 | 完成须通过整轮独立Verification与Validation并根亲审证据；旧同版本证据可复用，改动只按影响补测。无ADB实机自然网络未验如实披露；未知历史关闭原因保未知，不为填比例强归网络。 | 根AGENTS/autonomous-run及用户可归因诉求。 |
| U13 | 先解耦查清连接／控制层的Socket、事件覆盖／顺序、Turn身份／状态、恢复交接，再决定必要Timeline重构。验收连续手动Turn→Steer→结束中或结束后立即Heartbeat／Reminder→后续流式，覆盖最后delta到API／Turn结束的延迟；单份消息、连续片段、正确运行状态、稳定历史折叠和阅读锚点，不要求用户刷新或避开交界。静态历史通过不代表流式稳定。 | 用户后继明确“复现、排查、修复”“先排除掉连接层本身的混乱”，必要允许Timeline重构；API延迟为待证线索，不是已定原因。 |
| U14 | 以统一连接生命周期和正向提交机制保证健壮性；健康连接不因正常业务/渲染关闭，所有意外断开均自动重连与当前页恢复，不因未知关闭码或观察者异常漏掉重试。关闭触发原因如实记录，诊断不能成为重连白名单/业务门禁；待确认与发送失败分清，恢复后自动清理对应状态。 | 用户后继“非必要不关连接，关了连接也应该有明确的退出原因”“所有的连接，都应该能恢复”“用正向代码机制来保证健壮性，而不是到处…写门禁”。延续U07/U13，不新增认证/写重放权限。 |
| U15 | Gateway真实运行时可限制Web写/控制，但当前页仍逐条跟随已持久消息、识别外部Turn真实结束并按既有出现／分组折叠规则稳定呈现；不丢旧collapse或用户展开选择，不因不能绑定Gateway控制runtime而误断线／全页恢复。不要求token流代理或跨进程控制；其它内部源仍完整Web控制。纯idle页面→系统唤起也须保已有显示选择。 | 用户“就算是Gateway…新的条目落库了…Web页面上应该也是能看到…外层渲染逻辑不会紊乱”，随后明确“我说的是Gateway和Web UI渲染逻辑”；系统唤起丢collapse是后继明确复现。 |

### 明确不做及待决边界

不改Reminder排期语义、Heartbeat原生起点、Provider／Prompt、通用调度／admission体系；不偷改算法公式或体验阈值，不建立跨进程Gateway控制broker，不操控生产会话做模型测试；不触碰用户现有浏览器或桌面，UI仅自建隐藏IAB。

索引勘误：前端仓库本来没有README；移除初稿该无效文件引用并固定实际AGENTS的版本和blob。此为路径／证据定位更正，未修改任何U条款或扩大规则、权限和完成条件，根README仍为稳定环境索引。

既有原生Steer附件限制和受理后重启处理按现有持久事实与明确可查询状态实现，不默丢附件或盲重放；必要局部工程细化在CLAUDE待追认中登记。

**E01 · 已获用户后继明确确认：** 用户回答“维护期间已经接收了一条等待中的消息，这时按Stop是否只取消维护然后处理消息”时，明确选择“取消维护，继续处理已接收的消息（推荐）”。无活动Main的Idle／手动维护中，Stop只取消维护，保留已受理等待输入；取消结束或原子提交发布后，在第一个安全边界处理。Turn内自动压缩时，主Stop仍停止父Main并取消未消费Pending／queue；独立取消压缩仅撤销维护，等待文本在安全发布后交当前Steer。旧session.interrupt默认不变，Web沿新增可选input_policy=web_controlled启用真实阶段判断。该项原为按U05和根AGENTS作出的可回退工程收敛，现由本轮用户异步答复明确确认；旧快照不回写为当时已获确认。
