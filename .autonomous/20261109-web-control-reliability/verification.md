# Verification：20261109-web-control-reliability · 全新独立复审 v2

## 1. 审查对象与结论概览

审查者：`verification_integrated_v2`，2026-11-10，全新独立上下文、非实现者、不派生。待审BE `/Users/edgar/code/hermes-secretary-connection-20261109` commit `5edc3f6805566f97241383401d74094a92e044ce`；FE `/Users/edgar/code/hermes-secretary-web` commit `edbddb6bcdef356ff83c71323d0fdbb6da201f8e`。本报告只判这组对象；后续修复工作树/提交不自动继承结论。

**阶段技术判定：不通过，D32（P1）和D33（P2）阻断进入Validation。** 45条中38符合、4违规（R01/I08/R16/R17，只有D32/D33两个独立根问题）、3证据不足（A10/O01/O02，发布/自然运行/后继门禁完成事实）。D29事件hold移交/统一可见提交及D31真实owner公布后失效通知有同版本有效关闭证据，旧报告不通过保持原时点。不能因旧缺陷已闭合忽略本次全轮新增发现。

**整轮完成状态：未完成。** 范围内产品偏离须先修并全新全轮复审；另一独立Validation、main联合发布/新APK、线上版本/真实配置与V4自然运行及root最终证据审查仍须取得。后继步骤本身尚未执行不是当前实施阻断的理由，也不假标符合/N/A；此处没有要求本审查者先去生产部署制造顺序循环。

依据：本轮`Snapshot Index`与`baseline.txt`仅定位冻结原文和U01–U15/E01；白板/07及06当前合同优先，02→04明确保留→01/08及指定b232def V4 R4/V3保留合同。规格指纹`V2/spec-manifest.json`。产品只读，写入仅本报告和V2 ignored目录；未运行模型/生产/真实用户状态、未提交部署、未操作用户/root页面，也未复跑大套。复用了经独立逐SHA核实的实际证据。

证据前缀：`B`=本BE `.hermes-dev/web-control-reliability-20261109/`；`V2`=`B/independent-verification-v2/`；`S`=BE `.hermes-dev/stream-order-fix-20261109/`；`F`=FE `.archive/web-control-reliability-20261109/`；`A`=`/Users/edgar/code/hermes-secretary/.hermes-dev/adaptive-v4-20261109/`。路径/行号均为待审版本；`src/`和Kotlin为FE，其余BE。

## 2. 独立要求清单与覆盖

初始43条判据于2026-11-09T17:36:50.475038+00:00、先于实现/测试/CLAUDE/plan/旧报告调查落盘，原始完整六节副本`V2/criteria-initial.md`不改。判据初建已一次整包通知root。此前旧报告只做原字节备份，SHA256 `18e707de14ba8617b78c8655806ab39c6ee1c122b7d1ce8bc84b1ebd39d02ab2`，不先读其结论。索引/版本作定位，未用实现自评定义预期。

**原文补充细化记录：** 实现调查发现直接修改活动附件动作与Scheduler面板，初始I08明确保留的06当前界面合同需可独立回查，故新增R16（06:53–58）/R17（06 §1.8）。原要求未改变；是全范围遗漏细化，非用代码命名重写或降低标准，初始版永久保留。root分别亲读最新原文后确认未有覆盖授权，接受D32/D33。其余初始判据保持。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| R01 | U01；06顶部11/9与C1–C8 | 行为/全轮 | 重复Thinking、断连、静默、Send/Enter busy、折叠与移动诊断均纳入；不以猜测归因 | 每个可复现缺陷有正式路径修复与匹配证据，未知历史原因保持未知 | 第3节R01 |
| R02 | U02；07 §8.15；08 §2.3 | 机制/普通及所有内部来源；接线薄弱 | 来源不能决定同runtime的观察或控制资格 | 普通/Instant/HB/Delegation/Idle/其它内部运行任意时刻可绑定实际对象，实时状态和对应Steer/Stop/取消完整 | 第3节R02 |
| R03 | U03；02 §1.5/3.12 | 边界/Gateway及未知owner | 历史source/route/服务存活不证明独立Gateway活动；未知不得假称Gateway | 仅已证独立Gateway当前Turn可占用busy；未知保明确受理状态且不抢原生租约 | 第3节R03 |
| R04 | U04；06 §1.5/1.8/2.2–2.4 | 机制/输入原子路由 | 在原owner/原准入下依据真实阶段唯一选择Prompt、Steer或安全等待 | 覆盖开始/结束/停止/维护/idle读取竞态；单writer、零吞输入、零双执行、稳定operation及状态查询 | 第3节R04 |
| R05 | U05/E01；06顶部11/9 | 行为/无Main维护 | Send接收等待不取消；Stop只取消维护并保留受理输入 | 等待可见；取消或原子发布后首个安全边界处理；未提交Noting取消、已提交保留 | 第3节R05 |
| R06 | E01；U06；06 §1.10/1.14 | 边界/Turn内压缩及取消 | 主Stop停止父Main并取消未消费Pending/queue；独立取消压缩只撤维护 | 两类Stop与Interrupt/Cancel Send明确；独立取消后等待文本安全转当前Steer；旧session.interrupt默认不变 | 第3节R06 |
| R07 | U06；06 §1.14/2.5/11/1；07 §8.1 | 机制/Compaction operation | 压缩operation独立，取消不得误指下一操作或回滚committing | 恢复部分摘要、真实阶段、operation定点取消；committing等待安全发布；Stop不等Pending读取/冷建 | 第3节R07 |
| R08 | U07；02 §1/2.6–2.7；04 §1.3；08 §1 | 边界/身份与并发 | Profile/Conversation/合法lineage/native Turn/operation/epoch隔离 | 同活父、同Fanout、原生单writer；跨Profile同ID/轮转/rewind/fork/迟到结果不串域 | 第3节R08 |
| R09 | U07/U14；06 C0–C3/§1.4.1 | 机制/初进与断线恢复 | Socket connected不等于页面恢复完成；当前可见依赖和有限流切点统一提交 | 同/异epoch、读取失败、owner切换、断线外部改写自动同页收敛；无reload、无写重放、无全库正文 | 第3节R09 |
| R10 | U07/U13；06 11/8正常交互分离 | 机制/连续连接 | 正常有序业务是局部失效，不无条件整页恢复/重新激活 | 发送/Steer/开始/结束/压缩/列表通知不清旧状态、不锁正文；读取局部失败局部重试 | 第3节R10 |
| R11 | U09/U13/U15；06 11/8折叠 | 行为/历史辅助组 | 正文边界、已结束历史、当前活动区间各有真实身份；未知新边界不抹掉旧完成证明 | 普通Steer/Interrupt/followup/HB/Reminder/idle唤起与分步checkpoint保持历史折叠及用户展开；同页最终收敛 | 第3节R11 |
| R12 | U13；06 §1.4–1.5/10/21顺序 | 行为/流式多Turn连续 | 同片段唯一、边界真实；最后delta后仍活动不当结束；终态不得靠重渲染纠错 | 手动→Steer→收尾立即HB/Reminder→后续流式；无重复/缺段/卡顿到结束/错误转圈，阅读锚点稳定 | 第3节R12 |
| R13 | U14；06顶部11/9 | 机制/统一连接生命周期；薄弱 | 任何意外断开均可重试；诊断和UI观察者不支配连接存活 | 健康连接不因业务/渲染关闭；未知close/观察者throw/断线活动Turn都自动重连恢复；实际直接原因可追 | 第3节R13 |
| R14 | U14；06 C3/§1.5受理恢复 | 行为/未确认提交 | 未知回执不等于确定发送失败；恢复不能自动重发 | 原operation查询并自动清理已恢复状态；草稿和新输入不被迟到ACK重复消费 | 第3节R14 |
| R15 | U15；06 §1.3 Gateway活动与顶部 | 机制/外部Gateway只读跟随；薄弱 | Socket健康、控制资格、持久进展、外部真实结束是分开事实 | Gateway持续运行逐条新落库消息增量出现；结束及时按真实边界折叠；不报断线/全页恢复/丢历史选择；不要求token代理 | 第3节R15 |
| R16 | 06:53–58（11/8 Noting面板最新确认）；初始I08/R09/R10细化 | 保留界面/本轮App直接改动 | Orb立即异步预取；展开前先测实际目标，缺二级数据保一级准备；最新覆盖10/26旧立即loading | 读取/测量/动画/数据/owner同生命周期；慢/失败/反向/降动效均保持；不因结果到达重启动画 | 第3节R16 |
| R17 | 06 §1.8:793–806/§1.6/§1.10；初始I08/R04细化 | 行为/活动Main附件边界 | 活动Main+任意附件时主动作Stop或Pending-only Interrupt；正文/附件不提交；Enter不触发取消类动作 | file/photo及有无Pending/文本均按表；公开Steer不越过附件资格；保无Main维护Send及idle上传竞态原子接收 | 第3节R17 |
| D01 | 06 C1；U08 | 机制/Fanout健康突发/大帧/慢端 | 既有发送owner优化，内存有界、慢端隔离、不能删事件或无限扩容 | 健康突发/真实节奏/多订阅/大结果无误踢；真正慢端有界退出；seq/legacy/typed顺序对应 | 第3节D01 |
| D02 | 06 C2；U08 | 行为/Unknown片段 | 运行未知不等于idle；已证同片段继续追加，不按文本猜去重 | typed身份持续片段与真实Thinking→正文/工具/新片段边界，恢复失败不裂卡/不放宽身份 | 第3节D02 |
| D03 | 06 C3；U04/U08 | 机制/Steer资格 | Main运行和Pending.active是两个独立事实；Pending未就绪不能推出Main空闲 | 普通按钮/Enter及内部来源在正式owner就绪后被原生通知刷新；未知不盲重发 | 第3节D03 |
| D04 | 06 C4；U08 | 机制/双端关联 | 服务端connection_id与客户端attempt ID只作诊断，不授权限 | ready/query新增可选、形状校验、旧新兼容；close code/reason、队列/帧/发送/loop必要量可关联 | 第3节D04 |
| D05 | 06 C5；U08/U14 | 边界/客户端诊断 | 固定枚举数值、无正文/参数/URL query/凭据/任意异常正文 | 尝试/ready/close/RTT/接收年龄/RPC/恢复/调度延迟；健康聚合及有界同源HTTPS探测不改业务 | 第3节D05 |
| D06 | 06 C6；U08 | 机制/Android release | 滚动落盘不阻UI/发送，墙钟/单调/版本/前后台/网络与JS关联 | 有界容量/频率、失败和裁剪计数可见；无敏感权限/伪基站判断 | 第3节D06 |
| D07 | 06 C7；U08 | 边界/ADB导出 | 固定只读诊断出口，仅shell/root或自身可读，不可任意文件访问 | release无需debuggable/root/重载可脚本导出ZIP，含版本窗口计数格式；不删手机日志 | 第3节D07 |
| D08 | 06 C8；U08/U11/U12 | 完成/移动构建 | 递增原签名APK必须绑定当前FE资源；机制测试不等于真机 | 包版本/证书/嵌入资源哈希核验；ADB未连接则未实机自然网络验收如实披露 | 第3节D08 |
| I01 | 白板A1/O1/N1–N4；07 §2–4/§8；02 §3.1/3.3–3.4 | 继承/Notebook权威及提交 | 原文事实源、Main只读、Noting独占工作态/完整不可变Snapshot、原子合法pointer | 本轮控制改造不使取消草稿生效、不绕Anchor/开关/版本/来源，不变更Notebook业务语义 | 第3节I01 |
| I02 | 白板C1–C9/L0–L9/E1–E2；07顶部来源链与v2 | 继承/内容权限/来源/结算 | 七类型+Candidate、done、来源槽/描述/evidence_time、外部批准/实际写入边界保留 | 本轮无无关Prompt/Schema/内容迁移；控制取消仍保失败/未知/未覆盖和已提交事实 | 第3节I02 |
| I03 | 07 10/28/§8.1；11/1取消；白板P2 | 继承/Noting与Compact解耦 | 普通共同触发、联动取消未提交；Force唯一提前不可取消；Idle正常Noting后压缩/FM | 压缩不等待普通Noting；已完整提交不回滚；Force不因Send/Stop旁路取消；框架不启动Turn | 第3节I03 |
| I04 | 07 10/31 Force完成边界/§8.13；02 §2.6/2.7 | 继承/Framework与pointer | Main真实结束不被后台Noting延长；FM完整最新合法簿，旧结果不回退 | 同事务pointer→durable/live一致，排队旧通知剔除；后续Framework不使结束Main转圈 | 第3节I04 |
| I05 | 02 §5.2–5.5/5.10–5.11；04 §3.5/4.5；07 §3/10/31跨平台 | 继承/缓存与原生模型 | 同活父冻结root/tools/order/messages/多模态及能力面；不临时补工具或建执行器 | 本轮绑定控制不重建root、不改变Provider/推理/Prompt/外部D01、不复制历史替代活前缀 | 第3节I05 |
| I06 | 07 §6/§8.14；02 §3.10–3.12；08 §2 | 继承/Scheduler及冷态Reminder | 独立开关/owner/due claim，busy→deferred、durable witness、Provider响应后ACK | 冷态无浏览器可恢复正确Main；控制改造不重排提醒、不丢/重复ACK、不改已持久载体 | 第3节I06 |
| I07 | 07 §8.15；08 §1 | 继承/HB范围与时钟 | HB稳定Conversation owner、真实触发时间、原UI Main路径、人工pause/clear优先 | 关闭/非eligible原生零变化；不改HB起点，不因网页路由/回收重置或串Profile | 第3节I07 |
| I08 | 01 §1/§3–4；06 §0/2；08 §1/3 | 约束/架构兼容 | Hermes-first、增量可选、原生writer/DB/模型/认证/文件owner边界 | 无新Agent Loop/通用admission/第二API/跨进程Gateway broker；旧调用/返回/错误默认兼容 | 第3节I08 |
| A01 | U10；V4目标/转换；C01–C04/C13/C20 | 行为/暖态默认hot | 仅hot/standby；context大/无人/缺样本/微费用差不能单独停HB | 暖态保持高频并避在途/短返；无business候选/三小时回退，缺维护证暂缓整理 | 第3节A01 |
| A02 | V4缓存依据/转换；C09–C13/C23 | 机制/执行前缓存guard；薄弱 | 按Provider合同、当前配置、真实请求前缀和实际due复核，不只用旧Main结束判断 | 显式切换未用且预计冷/真实过期→standby；reasoning兼容仍hot；旧证据不暖新合同；无探测模型 | 第3节A02 |
| A03 | V4 D1/D2；C14–C17/C19 | 机制/正常User或Reminder恢复 | 待机不阻正常入口；真实完成后高context优先尽快维护；不适合先恢复已暖hot | 复用经验阈值/32768/原生容量及原费用/风险/Reminder/工作保护；失败不永停或无界重试 | 第3节A03 |
| A04 | V4 D3；C18/C19/C23 | 机制/一次恢复首读 | 仅当前owner/配置/压缩成功边界产生一次许可；真实请求已暖无需额外许可 | 失败/取消零许可；变更失效；并发claim/调用/退款/跨崩溃防重复，费用计入维护，不称必暖 | 第3节A04 |
| A05 | V4 D4；C20/C22 | 边界/登记/缺配置/人工控制 | 合法hot周期按当前模型→目标共同→目标有来源旧hot；不借他模型价格/TTL | 无周期不调用并明确配置不可执行；未知缓存一般hot；人工pause/clear/全局关闭/非目标不复活 | 第3节A05 |
| A06 | V4 C08整改合同/R4；C08/C15/C23 | 机制/Reminder条件分布 | Reminder不重置真人年龄；按独立离开段、当时可知提醒条件化；超实际覆盖回一般分布 | 不偷看未来返回；同段多提醒不增独立权重；无提醒样本不称效果已过；无固定等待替代经验 | 第3节A06 |
| A07 | V4保留V3；V3决策/历史挖掘；C02–C07/C16 | 机制/经验维护决策 | 规则定顺序，条件剩余空档/删失/近期权重/样本支持驱动费用和风险 | 工作/Reminder保护、15%碰撞/30秒期望等待/4h间隔/日2次/收益门槛不放宽；计划失效不执行旧决策 | 第3节A07 |
| A08 | V4费用依据/后续回放；V3四桶/时长；C17/C19/C21 | 机制/成本与时长 | 真实四桶不重叠，max(Noting,Compact)规划和Main阻挡分账；取消零调用不补工作量 | cache观测可升可降、缺价/账单/配对披露；失败费用保留，不伪缩减/补0/以时长代上下文需求 | 第3节A08 |
| A09 | V4后续回放1–6/R4结果限制；C01–C23 | 证据/历史与声明场景 | 原9窗/两日/首夜/GPT/Kimi下午、原截止和负结果、独立演化context/cache | 原版同源字节证据可复用；H/C/M分清；留一段敏感性负例/6h24h/共同末点责任不抹掉 | 第3节A09 |
| A10 | U10；V4联合发布授权 | 完成/线上自然生效 | 合入指定b232def R4仅准备条件；线上实际接线、配置与自然运行是后继完成事实 | 发布后有源码/进程/配置与非人为模型测试的自然decision/due guard证据；保User/Reminder来源和等待非blocked_send | 第3节A10 |
| O01 | U11；06 C8；根发布授权 | 完成/发布与数据保护 | 正式仅main，Web+原证书新版APK；保护DB/绑定/模型/他人dirty | 源码/构建/HTTP/进程逐一对应；两套有效完整三库备份且清更旧；无测试资料入生产 | 第3节O01 |
| O02 | U12；autonomous-run门禁 | 完成/整轮验证 | Verification技术阶段与发布/自然运行/Validation后继事实分别记录；无顺序循环 | 范围内实现或必要机制缺证先阻断；后继事实不假符合/N/A；整轮须两独立门禁及root亲审 | 第3节O02 |

## 3. 逐条实现证据

以下每行按第2节同号的“原文→解释/不变量→符合判据”连接正式路径、适用条件/方法、观察及证据边界；同一个测试数不重复累计为独立覆盖。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| R01 | FE controlledAction/Controller.steer/App Secretary；BE统一控制与事件owner | 逐条覆盖已报故障和本轮新增路径；D29/D31已核；发现D32/D33 | 本报告第5–6节；V2/attachment-boundary-inquiry.md与schedule-panel-current-contract.md | 违规：两项范围内明确产品合同仍偏离，不能称所有可复现问题已修 | 未知历史1005/1006诱因不归网络；不将D29等同旧生产唯一根因 |
| R02 | BE methods_web_control.py:233/298→native submit；session_notifications→_run_prompt_submit；FE controlled control/readInputState | 普通/Instant/HB/Delegation共享Main；内部确认/冷态状态及维护控制在正式Loop/SQLite/RPC链可用 | B/final-plain-lock-control.log；B/internal-source-regressions.log；F/d29-final-real-control.json；F/d30-final-full-app.json | 符合：没有按内部触发来源丢观察或对应控制；任意时刻恢复同父对象 | 活动附件动作另列R17；受控外部Provider，不代真实网络/模型效果 |
| R03 | BE methods_web_control.py:40–69/139–150；active_sessions.py:745；change_watcher | 活SQLite lease holder+同DB/ref的活registry exact host才gateway/4009，未知4090；D31公布后独立hint | tests/tui_gateway/test_gateway_read_only_follow.py:74/198/211；B/d31-research/formal-full-final.log与implementation-verification.json | 符合：历史source/单独foreign lease/服务在线不冒Gateway，不抢writer | Gateway token流/跨进程控制明确不做；真实浏览器D31补强见B/root-d31-ui/verification.json |
| R04 | BE methods_web_control.py:176/203/233→_session_turn_admission→methods_submit_idle→native Pending/queue | 真实history Lock原子分路；同op重用、同文不同op独立；startup/settling/maintenance/Stop世代和queue claim | B/final-plain-lock-control.log（11文件67）；B/queued-claim-stop-final.log；B/final-admission-withdraw.log | 符合：后端原owner/准入选择稳定，无第二writer/文本去重/新的主gate | 正确后端能力不授权前端改变附件主动作，见R17 |
| R05 | BE _web_waiting_input:203；web_stop_control.py:71；compression_read→native request/fence→queue drain | 真实维护计算/取消/committing赢家；Send只受理waiting，Stop保waiting到安全边界；新source仅执行一次 | B/final-owner-maintenance-stop.log；tests/tui_gateway/test_web_controlled_maintenance.py:53/251；F/d29-final-real-control.json | 符合：满足E01，不暗取消/假回滚，未提交Note联动、已提交保留 | 部分摘要只是运行显示；旧并行join5s失败仍保留，不冒称根因已治愈 |
| R06 | web_stop_control.py:25→methods_session_interrupt→session_lifecycle._interrupt_session_turn→agent.hard_interrupt(require_turn_id)；独立compaction_cancel | Main Stop清未消费queue/Pending；无Main维护只cancel；旧目标/原terminal token与redirect锁保护新Turn；不等Pending读取/冷建 | B/stop-fence-tests.log；B/final-owner-maintenance-stop.log；B/final-stop-default-hooks.log | 符合：主Stop/独立取消/Interrupt/Cancel Send仍各自职责，旧默认hooks保持 | 前端附件误动作独立判违规；unknown Stop不能从自然结束反推成功 |
| R07 | agent/compression_read.py:12/78/118/149；compression_facade/partial；FE compaction-read/updates | 同op revision和Unicode offset、65536最近前缀；32终态；重置/缺口仅重读确切op；原commit fence | B/final-maintenance-contract.log；tests/tui_gateway/test_web_controlled_maintenance.py；F/controller-web-control测试及d30-final-targeted.log | 符合：初进/重连恢复真实摘要/阶段；旧operation query/cancel不借新操作 | 无百分比/剩余时间承诺；committing仍too_late等待原发布 |
| R08 | session_lifecycle._find_live_compression_owner；methods_web_control._web_control_session；02原identity/Foreground/pointer；FE scope/fences | 同DB/Profile/ref合法compression tip；跨Profile同ID、旧epoch/owner/operation响应；不改原schema ownership | B/final-new-tests.log；B/final-plain-lock-control.log；F/d30-final-targeted.log内controller-page-recovery/ServerRequests；V2/backend-startup-parity.json | 符合：同活父和Fanout复用，合法lineage续接不误fork/new；opaque身份不解析格式 | 新通知只hint不授权；旧数据库迁移/跨profile查询不在范围 |
| R09 | FE ControllerPageRecovery.selected:735/readConversation:1051/retireReplayOwner:1120/installCut:1366；PageRecovery.reconcileRound:305/readLocalRequirements:421 | 完整/局部均当前owner/revision/demand后reconcile再commit；hold责任可移交退休；有效连续后缀序号严格一次排空；真gap保缓冲走原恢复 | F/controller-page-recovery.test.ts新增D29/原恢复矩阵；F/page-recovery.test.ts；F/d30-final-targeted.log；F/d30-final-full-app.json；B/root-final-ui/fixed-ui-verification.json | 符合：D29原有限读取失效遗留held已关闭，最后terminal无后续帧亦收敛；不等Turn结束、不reload/重放写 | 真实IAB为root执行，独立Validation后继；旧红和原现场不改写 |
| R10 | FE continuousControls/refreshChangedSessions→readContinuousHistory/cut；Controller.event→PageRecovery | 连续连接按回执/有序事件局部失效，viewport新alias不重新activate已证binding；metadata与有限cut对账 | F/d30-final-full-app.json；F/d29-final-gateway-follow.json；F/d30-final-targeted.log；B/d31-research/implementation-verification.json | 符合：正常发送/Steer/压缩/外部持久变化不无条件整页恢复；失败局部自动重试 | Scope实际失效仍完整恢复；Schedule读取时点另一条R16违规 |
| R11 | FE timeline-folding.tsx TimelineBoundaryOwner:67/activeStart:20；external-turn-folding.ts:31 | 已结束prefix mark与当前Turn分离，native proof/同cut external source；稳定source/facet choices；正文/末未闭组保持 | F/timeline-folding测试；F/d29-final-pure-idle.json；B/root-final-ui/fixed-ui-verification.json；B/root-gateway-ui/third-gateway-ui.json | 符合：idle→HB/Reminder、Steer/followup分步身份不清旧fold，真实后证同页收敛；用户展开保持 | 真实reading top 422.5390625/scrollTop0保持；不推断所有设备帧率 |
| R12 | BE native OutputIdentity→Replay/transport→FE event/projection/native facets→RenderStore/Chat | 正式App手动→Enter Steer→原生后继→Stop、自然结束/HB/Reminder，lastdelta/API/terminal屏障；state/render/DOM单份一致 | F/d30-final-full-app.json；B/root-final-ui/fixed-ui-verification.json（cursor189，8唯一Assistant，held/replaying空）；F/d29-final-real-control.json | 符合：D29同UID双份/末尾Receiving的实际反例现有对应关闭，不靠终态历史重渲染纠错 | 受控loopback SSE+真实原生Loop/HTTP/WS/DB；非云Provider/Android自然网络 |
| R13 | FE client.ts:126 deliver/299 endConnection；ControllerPageRecovery.deliveryFailure/holdSequenceGap:240 | retire先清pending/排retry后best effort close与观察者；所有意外码同生命周期重连；observer逐个隔离；健康业务仅失效读取 | F/client.test.ts；B/close-origin-audit/implementation/frontend-api-tests.log；F/r7-persistent-observers-green.log；B/peer-close定向日志 | 符合：诊断原因不作重连白名单，UI observer异常不截断retry/其它订阅者；不因业务正常关闭 | 原自然1005/1006直接诱因未知保留；不会由1006算网络责任比例 |
| R14 | FE prompt-submit/queryableSubmission/readPromptAcceptance；Controller.checkSubmission/acceptPrompt；submission-recovery | 断线未知保原op只读核验，input_changed/恢复后精确receipt退休；后续草稿用owner/revision保护 | F/controller-submission-review.test.ts；F/d29-final-real-control.json lostACK分支；F/d30-final-targeted.log | 符合：unknown不伪发送失败或自动重发，已受理不被辅助读取失败反转；对应状态自动清理 | 重启RAM执行未知显示accepted/unknown并可显式取回，尚待追认工程边界如实披露 |
| R15 | BE active_sessions.observe_native_turn_owner→notify_history_changed→change_watcher trailing；recovery_view.turn_source；FE observeExternalInput:453/readContinuousCut:1265/统一fold owner | D31先lease/首读unavailable→成功公布exact元数据→rows/source不变第二hint→同doc/socket/round/runtime自动gateway；两external owner、逐条durable append、release后idle | B/d31-research/implementation-verification.json（2302.8/2329.9ms）；formal-full-final.log39通过；B/root-d31-ui/verification.json与source-start.json；B/root-gateway-ui/third-gateway-ui.json | 符合：D31公布后漏唤醒已在原提交点修复，不降身份证明；Gateway只读进展与终态按持久事实稳定交接 | 强制时序完整App为JSDOM；root本轮另有真实隐藏IAB补强：B/root-d31-ui/verification.json（不虚构公布前counter或UI毫秒）；不要求token代理 |
| R16 | FE App.tsx:842–845/874–891 Secretary需求与SchedulePanel | 当前open && scheduleOpen才取列表；无数据即切二级loading；正式IAB准确观察Orb前后detail0/二级1 | 06:53–58；F/d30-classification.md G10；B/root-gateway-ui/scheduler-ui.json；V2/schedule-panel-current-contract.md | 违规：D33按10/26旧期待回退，直接违反11/8当前预取与真实目标就绪后过渡合同 | 本条为初始I08/R09/R10的原文细化；不改初始判据，修复须新完整App+实际过渡证据 |
| R17 | FE web-control.ts:19–29→ChatComposer contentAction/Enter→Controller.steer:2094→send/executeSend:1548；BE _web_waiting_input | 合法活动Main+任意附件无Pending返回Steer；公开steer先绕过canSteer，上传image进followup/file ref可进Steer；与原主动作Stop不同 | 06 §1.8:793–806；V2/attachment-boundary-inquiry.md；root已确认无覆盖授权 | 违规：D32可把原Stop意图变成附件上传/受理，改变明确动作与权限语义 | 无Main维护仍Send等待；idle Send上传中Main启动仍须后端安全接收，不以修复重加busy |
| D01 | BE transport.Fanout.write_ordered/_admission_lock/_admit_frame；output_identity._native_write；WS统一FIFO | 原有界byte/batch+一个大逻辑事件/twin；producer编号/冻结/准入同序，consumer短锁归还credit；真正慢端隔离 | S/green-final-transport.log49通过8平台skip；S/green-identity-fifo.log52；tests/tui_gateway/test_stream_event_order.py；同启动42源SHA | 符合：健康突发/大帧不误踢且wire/Replay顺序同owner；未改容量/timeout/删事件 | 8 Linux-only本机skip如实；无无限队列，单大payload仍按既有原生事件大小 |
| D02 | FE projection.reduceEvent/native-output；reconcileLiveHistory/retainLiveAnchors:864/terminal-history | Unknown只撤运行断言，同native facet连续追加；确切source/turn/ref/runtime/seq位置，不按相似文本去重 | F/r7-final-targeted.log；F/d30-final-targeted.log中的timeline reconciliation/native fixtures；B/root-final-ui/fixed-ui-verification.json | 符合：同片段不逐chunk裂卡，Thinking/正文/tool真实边界和原有类型不变 | D29真实终态证据另闭合，不用Unknown机制静态绿掩盖曾有的held故障 |
| D03 | FE controlledAction/Composer policy、BE _web_input_phase/_web_bind_pending；Pending native通知 | Main是否运行独立于Pending.active；统一控件不等Pending可读才Stop；普通Enter文字沿同submit | B/final-plain-lock-control.log；F/app-steer-busy.test.tsx及d30-final-targeted.log；root真实Enter/Stop链 | 符合：启动/维护/停止中的Main不误idle，owner就绪后原通知刷新；没有4009盲重发 | 此符合只文字/控制资格，带附件主动作R17违规 |
| D04 | BE WS diagnostics/ready connection_id/client query校验；Fanout._signal_overflow_detach；FE diagnostics | 可选32hex双ID、direct close原因、帧/队列/发送/loop指标；旧客户端仍无须传字段 | B/close-origin-audit/implementation/source-manifest.json；tests/test_peer_close_diagnostics.py；F/protocol-parity.json | 符合：只作诊断不授权，close直接触发与未知上游诱因分账 | shared ID可关联不等于已取得自然移动网络原因样本 |
| D05 | FE connection-diagnostics.ts/health-probe与client lifecycle；Android DiagnosticSchema双白名单 | 固定枚举数值/形状过滤；RTT/最后收包/未决RPC/调度/恢复；60s聚合及有界同源HTTPS探测 | F/connection-diagnostics测试；B/close-origin-audit；F/release/native-evidence-reused.json | 符合：无正文/参数/查询/凭据/任意异常payload；观察/探测不改业务状态或模型 | 已知标签不证明运营商内部切换；未输出敏感Token或用户内容 |
| D06 | Android ConnectionDiagnostics→DiagnosticSchema→DiagnosticStore单有界worker | 4×2MiB、单行8192、queue256、rate20/s；UTC/elapsed/process/app/lifecycle/defaultNetwork；计数与中断行恢复 | FE Kotlin源码；F/release/native-evidence-reused.json（87原生源同字节）；原DiagnosticsProvider/Schema12项 | 符合：release常态滚动异步落盘，丢弃/失败/裁剪可见，不增敏感权限 | 真实设备后台/自然网络时序未验，不由Robolectric冒签 |
| D07 | Android DiagnosticsProvider.enforceUid/openFile精确URI；仓库ADB导出脚本→ZIP校验 | shell/root/own UID外拒绝，固定/export且r-only，非任意文件；pipe有界串行快照不删原件 | Kotlin Provider源码；F/release/packaged-diagnostics.json；原Provider6项及export脚本 | 符合：原签名release无需debuggable/root/reload具备可导出机制 | 无ADB设备实际导出未验；该限制按C8披露不是伪通过 |
| D08 | FE edbddb6正式android:build/verify→APK内置assets/secretary；静态tar | 独立计算APK/tar SHA和439集合逐文件；原证书、0.1.14/1014、nondebug、16KiB严格原收据 | V2/artifact-parity.json；F/release/artifact-binding.json及APK.verification.json | 符合：该待审源码的本地构建/签名/资源绑定真实，旧9f包归档不可发 | D32/D33修源码后此绑定须作废重建；不是安装/自然移动网络/最终发布事实 |
| I01 | 未改notebook_store/model/items→hermes_state_secretary_notebook Commit Gate；noting_joint.cancel_operation:91 | 核本轮diff不引Main写/新Snapshot owner；取消只状态CAS未提交admission、已提交不回滚；有效Anchor和原pointer事务 | Git12e→5ed产品diff；B/final-related-regressions.log193；B/final-owner-maintenance-stop.log | 符合：本轮控制增量不绕完整不可变Snapshot/原子pointer/来源权限 | 未对不受改动影响的全部Notebook语义重新采样，按保留影响审查 |
| I02 | 未改noting_prompts/tools/notebook_contract及provenance读取；新custody display过滤仅公开来源投影 | 七类型/Candidate/done/Task来源链/描述/证据时间和外部结算权限均无产品改动；早写witness只受理非事实源 | Git产品diff；B/receipt-projection/report.md与green-6.log；相应178项回归的准确边界 | 符合：未把custody当真实model source，也未迁移/修改已提交Notebook或Prompt | 单项并行worker join5s红及隔离绿分别保留，不从旧测试镜像推断语义 |
| I03 | noting_idle_joint/native_link/request_context_compaction→noting_joint cancel/commit→native fence | 普通并行，Idle正常Note提交后压缩/FM；Force例外与区间占用未改；维护Stop按真实对应未提交项 | B/final-owner-maintenance-stop.log；B/final-related-regressions.log；F/d29-final-real-control.json维护自然finish/commit | 符合：未把Note/Main活动混为一体或使Send隐取消；Force不因普通联合取消失效 | 不新增高频Noting/调度；failure原资源清理和合法快照边界保持 |
| I04 | noting_child→current pointer FM安全追加；turn_terminal/output_identity正式Main结束；FE terminal-history | 有效pointer才FM、排队旧通知丢弃、FM不触发Main；后续Framework不延长Main的输出对象/转圈 | Git未改FM核心；B/final-related-regressions.log；F/E1全Notebook临时输出旅程与E2原260帧；root8Turn终态证据 | 符合：Main结束事实独立于后台Note/FM，完整簿与失败通知仍原owner | 真实模型Noting内容质量未被本轮重写/新增采样 |
| I05 | agent/cache_parity/noting_child freeze；turn_context/prompt_turn原native模型路径 | 核本轮diff无Prompt/Provider/tools表重写，控制回调与观察不改父前缀；原D01/多模态/子白名单保持 | Git12e→5ed；V4指定27源逐SHA；B/final-related-regressions.log；正式Loop受控transport证据 | 符合：无临时补工具、平行模型执行器或历史重拼活父前缀 | 不声称Provider实际cached token命中率；前缀机制与真实命中不同 |
| I06 | 原scheduler_host/scanner→ActiveReminderAdmission→_run_prompt_submit；materialize_pending_reminders/Provider ACK | 改动不迁移排期/改due/改变busy→deferred；冷runtime真正原Main恢复，claim/见证/响应后ACK保原接线 | B/internal-source-regressions.log24；cold host相关67项；F/d29-final-real-control.json实际Instant入口 | 符合：统一Web控制沿现有任务/来源事实，没有第二Cron或重复carrier | 非真实微信adapter送达或生产提醒时间保证；既有claimed/未提交边界不扩大 |
| I07 | ConversationHeartbeatStore/heartbeat host→UI _run_prompt_submit→native Loop；V4 guard | ref/Profile稳定owner、合法compression tip、status/revision/anchor和显式pause/clear；冷态/无页面仍原host | B/final-heartbeat-observed-warm.log；test_web_controlled_heartbeat.py；F/d29-final-pure-idle.json；R4原机制 | 符合：未将HB改真人source绕guard，不重锚/复制定义或跨渠道自动外发 | 维护/输入source分别入账；非目标/全局关闭保持原生 |
| I08 | 全产品diff；06主动作与最新面板；01/02/04/08架构边界 | 架构/原生Loop/DB/Provider/认证/Files增量边界保持；但UI附件与面板被未经明确替代改变 | Git12e→5ed及cd5→edb；V2两个发现；root确认 | 违规：D32/D33违反当前06明确保留动作，不能以新增可选策略或旧测试授权 | 其它原生/增量机制已核；本判定不扩大NM/外部broker/无关UI重设计 |
| A01 | adaptive_cache.assess:72→adaptive_policy.decide:551→adopt_mode；配置model_config | 27源同指定b232def R4；暖hot/冷standby，无business候选；context/无人/微费差/一般缺样本不单独停 | V2/source-parity.json；A/source-r4-final/manifest.json；A/r4-*.json；测试cache/qualitative/standby_wiring | 符合：保持V4定性合同及原保护；不是仅把business interval写空 | 不保证Provider命中；历史稀疏和负结果仍披露 |
| A02 | heartbeat_store.load/due/claim:94/claim_is_current:136→inspect_conn；usage_read→request_started:336→block_first93 | 当前config/route/epoch/path/due复核至真正首次API；合约兼容与pricing key不混；reasoning shared有证据才继承 | test_adaptive_standby_wiring；test_web_controlled_heartbeat.py真实预dispatch改变配置0HB请求；A C09–C13/C23 | 符合：旧Main结束判断不能绕首次guard，旧回执不暖新合同，无模型探测 | 一般未知非强制standby；未注册缺合法周期属于配置不可执行，非缓存冷 |
| A03 | adaptive_runtime Main结束/idle_settings:302/plan_adoption；cache policy→maintenance路径 | 正常User/Reminder可唤醒，完成后高context按经验阈值与既有保护；暂不宜先暖hot；失效计划CAS | A C14–C17/C19；test_adaptive_standby_wiring；指定27源相同 | 符合：不靠关闭HB自身恢复，工作/Reminder/费用/风险门槛未放宽，失败不永久待机/无界重试 | D1/D4工程细化未冒充用户逐数值指定 |
| A04 | adaptive_cache._recovery:55/assess；adaptive_runtime._maintenance:408/request_started；adaptive_store request_start事务 | 真实成功缩减同owner/config/epoch/path产生一次许可，首次physical dispatch持久消费；退款/重启/配置失效 | A C18/C19/C23及standby_wiring真实事务；F维护自然commit；V2/source-parity.json | 符合：成功恢复首冷读允许且费用入账，失败/取消不造许可，跨崩溃不双用 | 线上自然消费后继待A10；不称首跳必暖 |
| A05 | adaptive_config/heartbeat_for_db/adaptive_model_config；cache_runtime.heartbeat_only_decision/refresh_unpriced | 按当前模型→目标共同→目标有来源hot周期；无周期不调用并配置不可执行；人工status先验 | A C20/C22/C23/配置单测；27源指纹；heartbeat_store set_status/save/claim | 符合：缺其它模型价格/TTL不借用；人工pause/clear/全局关/非目标不复活/不重锚 | runtime观察失败最佳努力不更改用户控制；不将一般缺观测当切换未用 |
| A06 | adaptive_reminder_history.condition/_project→stage_history/forecast/rollout | 每独立离开段按可知clock选一次Reminder，未偷返回标签；超实际followup覆盖max回一般分布，保human age | A/r4-afternoon-continuation.json与leave-one；A/review.md/r4-final-provenance；源码27源一致 | 符合：符合R4 C08修复方向，不用固定保护分钟/重复提醒增独立权重 | 删除关键11/6段仍误整理并等待399.6s，稀疏支持限制必须最终披露 |
| A07 | adaptive_policy/forecast/stage/history/rollout；_idle_plan_valid/plan selection guards | 原15%/30s/4h/日2次/收益门槛、1800保护及原生容量未改；可知时间/删失/独立样本/Reminder候选 | A预冻结expectations与r4-windows/continuous/6h/24h；V2候选与manifest逐SHA27相同 | 符合：条件经验分布驱动维护而非事后改阈值求绿，计划变更不复活旧选择 | H/C/M分清；定性符合不是概率校准或普遍省钱 |
| A08 | adaptive_cost/rollout/forecast；runtime.web_submit_input:620→web_input(event_id)；maintenance事件 | 四桶/费用/缩减/max(Note,Compact)规划与真实Main阻挡分账；同op真人恰一次，waiting不blocked_send | A C17/C19/C21；B/final-heartbeat-observed-warm.log与final-shared-input.log；test_web_controlled_heartbeat真实请求 | 符合：保失败/取消/慢尾/缺价未知和cache可升降；未重置HB起点或偷免维护成本 | 费用为输入等价条件模拟非实扣；缺联合账单/同源配对不伪完整 |
| A09 | 指定R4 source/expectations/replay outputs+本轮相关机制接线 | 原9窗/连续两日/首夜/GPTKimi下午原截止与扩展已知后继、留一段/6h24h/共同末点分别保留 | A/final-report.md、review.md、r4-*.json；V2/source-parity.json直接核b232def与27源 | 符合：原R1/R2/R3红与E06/E08/E09劣于V3/稀疏敏感性负例没有改写；同版证据可有限复用 | 完整历史条件成绩不等于未来无阻挡/留一段稳定/生产自然生效 |
| A10 | BE指定R4已整合；release只读探针与线上运行链尚待发布 | 本轮仅证27源同指定候选，未见当前正式main进程配置及自然决策同版收据 | B/release/adaptive-runtime-entry-report.md；本轮baseline；V2/source-parity.json | 证据不足：后继发布/线上自然生效事实未闭合；不能用preview/合入源码代实际生效 | 这是同一目标后继完成步骤，不要求Verifier生产部署，不单独制造进Validation顺序循环 |
| O01 | release准备器→main前置检查/保护/版本/两套三库保留；FE APK/static | 现包本地SHA/原证书/439资源核实；未执行候选main/云HTTP/进程核验或DB保护收尾 | V2/artifact-parity.json；F/release；B/release；operations-log历史 | 证据不足：当前候选联合发布事实尚未发生，且D32/D33修后必须新包绑定 | 不是授权Verifier操作生产；不把push/构建当上线 |
| O02 | 本版全轮45条独立矩阵及另一独立Validation后继 | 技术阶段由D32/D33阻断；新产品修后需全新全轮Verification，另一独立Validation/root delivery尚未闭合 | 本报告；V2/criteria-initial.md及旧previous-report.md；U12 | 证据不足：整轮未完成，不能称两个门禁通过；发布/自然事实单列 | 无ADB/未知关闭原因如实披露不是额外设实机门槛 |

## 4. 核心目标及验证方法审查

1. **控制权与原子接纳。** 正式能力沿`gateway.ready.web_controlled_input=1`启用，普通/内部源均走同Main、同native admission/history Lock和原Pending/queue。核了最容易绕过的起始无Pending、结束/Stop摘queue、压缩提交/取消、原tip旋转及old target清退；durable witness先于可执行queue，通知失败不反转已受理，未知只查原operation。没有新writer、通用gate、模型路由或第二输入ledger。D32暴露了“后端可安全接收”与“当前用户按哪个动作”不可混同；原子接收能力不能授权把Stop主按钮变成附件提交。
2. **恢复是事件责任交接。** 从真实D29反例出发核了bindingAuthority与可见window分责、selection代次、hold持有token、新读接手、旧finally不能删新hold、无后续帧亦主动排空、严格seq/epoch/runtime/owner、不越gap。full/local均在current revision/demand（local还serial）有效时reconcile再提交，安装cut前验证整个有限suffix/held。控制事实可先观察，但投影必须实际沿原reducer一次交付。现有定向用例不仅断言flag；还核cursor、terminal、单份对象和当前ready。真实完整App把390×400几何及真实HTTP响应后40ms延迟纳入，修复前红/修后绿都保留；root真实隐藏IAB另完成原Stop窗口及8Turn链。没有用文本去重、隐藏spinner、固定Stop延迟或断健康Socket“修复”。
3. **Gateway通知由真实成功提交驱动。** observer在exact PID/host slot内比较opaque四元组，原registry写成功后、锁外发所属DB的既有history hint；相同identity/单纯renewal不发，写失败不假发，通知异常不改变原lease/运行。原watcher的2秒floor保留trailing。正式39项证明首lease唤醒→合法unavailable→metadata发布且rows不变→后继唤醒；完整App连续两个external owner可自动gateway/同cut uncommitted，后续durable条目在结束前可见、终态及Web Send/Stop正常。root新`B/root-d31-ui/verification.json`以5ed/edb真实IAB再证同因果；公布前input观察直接有效，但未另捕获其页面counter，因此稳定doc/connection1/recovery4仅指公布后至结束/Web followup，也不虚造UI毫秒。启动42源独立逐SHA零漂移。
4. **当前规格优先于测试期待。** D30中E1/E2现有完整合法Controller旅程分别保Notebook临时输出/Framework后继和原260帧断言，E3/E4按当前折叠先实际展开再核内容，旧缺证可关闭。52旧红的实例隔离/Response clone/局部恢复等分类可按其各自证据接受，不能一概因基线同红豁免。但G10根App改法依据10/26旧条款，恰违反11/8新面板合同；当前583通过/1原有可选wire fixture跳过、完整App62+Composer4全绿是准确运行事实，**并不证明D33符合**。错误实现仍能通过这些旧期待，已要求撤回相关期待并依最新原文取证。
5. **证据指纹与复用。** 独立计算`V2/backend-startup-parity.json`：D31 PID80615启动前42源与待审BE5ed完全一致；`V2/source-parity.json`：FE D29全258 src、D31 import前251 code文件与待审edb零漂移，R4原27核心源与BE及指定b232def逐SHA一致。较早进程和不同App时点不冒称当前全版；旧D29部分run仅五控制/恢复源同字节，D30后完整App另外有新源旅程，D31新链还核真实启动。独立计算`V2/artifact-parity.json`：APK32,176,929bytes/SHA `2e37b3ed…eaafb`、static SHA `9bdfb85b…e40b`，439份APK内置/静态tar/manifest集合及内容一致。原证书/nondebug/16KiB复用严格包收据，不伪称本审查者安装或重跑签名校验；D32/D33修后需新FE/产物绑定。
6. **V4有限条件验收与线上完成分离。** 原C01–C23、9窗/连续两日/首夜/两下午及已知后继、6h/24h和共同末点均按原来源等级复用。独立核27源相同后再追load/due/claim/首次physical dispatch缓存guard、正常User/Reminder恢复、同owner成功缩减首读持久消费、计划与人工控制fence及web input恰一次事实。没有新增低频或修改公式/体验阈值。保留E06/E08/E09不如V3、原R1/R2/R3失败、删除关键11/6段后399.6s等待负例，不能以完整历史绿冒留一段稳定性/概率校准/未来不阻挡。当前未取得正式main进程同版配置与自然生效事实，A10待后继闭合。
7. **失败/环境与质量如实记录。** 本次没为review复跑有效大套，也没有新增真实模型请求。B旧maintenance并行finish在join5s仍alive、隔离同版通过但缺原栈，不能宣称已定位根因或原并行整绿；当前真实自然维护finish→commit→waiting consumed链提供其明确适用范围的补强，非抹旧红。S的8个Linux-only项本机skip，未伪OS；Android无ADB自然网络/实机导出明确未验。冻结十检查原日志`B/root-final-checks.log`为9过/no-tmp失败（历史20261031 validation报告的原命令路径），health93文件0blocking/1advisory；D31相关5检查通过。独立看了失败行、检查器说明及未改历史blob关系，未把它改绿、加豁免或改历史证据，也不以“旧版同红”豁免本轮适用产品机制。最终交付必须如实披露该检查状态，不能称“全检查通过”。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| D32（P1） | R17/I08/R01；FE web-control.ts:19–29、Controller.steer:2094、ChatComposer Enter | 活动Main+任意附件在controlled路径返回Steer；公开steer先send，实际上传提交；原表应Stop/有Pending Interrupt，Enter无取消动作 | 可把原Stop意图变成未准备附件的实际受理；明确产品动作/权限边界违规，阻断技术阶段 | 按root提案恢复真实活动Main附件Stop/Interrupt/草稿保留，公开Steer同资格；正式Composer主按钮/Enter、file/photo/文本/含无Pending；无Main维护Send与idle上传竞态保原原子接收；新源码指纹/完整旅程 | **开放**；root已亲读原文承认无覆盖授权，已派F1修复；本报告不审未来dirty |
| D33（P2） | R16/I08/R01；06:53–58；App.tsx:842–845/874–891 | D30把Schedule读取延迟到二级并立即loading展开，root IAB detail0/0/1证明同事实；依据是旧10/26条款 | 与11/8明确Orb立即预取、缺数据保一级/实际几何就绪后展开相反；测试预期权威来源错误，阻断技术阶段 | root提案恢复异步预取/原target测量生命周期；真实App及IAB核running一级、数据/几何就绪、慢/失败Retry、快速反向/owner/减少动画，异步结果不重启动画；撤旧期待保旧证据 | **开放**；root明确承认四处App修补为错误回退，已派F1 |
| V-DEPLOY（完成事实） | A10/O01；U10/U11 | 本地指定R4/控制代码/当前原签名APK已准备，未发当前main/云进程/HTTP/static/配置/自然策略证据；修FE后旧包还需新绑定 | 整轮未完成；后继事实缺口不当成Verifier必须先部署的循环前提 | D32/D33及fresh两门禁按序收口，从main联合发布；核四层版本、绑定/模型/DB保护、两套有效三库备份及自然V4事实，不在生产发测试模型消息补数 | **待后继闭合**；不能标符合/N/A |
| V-GATES（完成事实） | O02；U12 | 当前技术不通过；另一独立Validation/root最终交付未完成 | 自主轮次未收敛 | 新产品修复后由全新独立审查者先全范围判据/复核，再真实Validation与root delivery；复用本版有效证据，不能只复测D32/D33 | **开放** |

范围外新产品发现：无。原自然网络具体关闭原因/责任比例仍未知、无设备限制、未改历史no-tmp检查失败和原并行join限制按第4节保留，不扩展成未经授权的新工程，也不凭正常样本声称全部环境无故障。

## 6. 修复与独立复审

### 旧报告与本次独立起点

旧`verification.md`在本次读取前原字节备份为`V2/previous-report.md`，SHA见第2节，涵盖初始37条判据/逐条矩阵、D29反例及后续四项提案评审、D31发现及五项关闭条件。该原件所有发现/讨论/当时开放状态均保留；本版只续记当前证据，不把旧93c/9f525时点改成已经通过。初始`V2/criteria-initial.md`保持本次规格先行起点；本版新增R16/R17只细化明确原文，并在第2节说明遗漏及原因。没有主会话退回本报告因缺列/缺行的历史；本版六节各项按模板维护，不派生Agent。

| 旧问题/讨论 | 原判据与当时事实 | 当前独立复核及结论 | 证据/边界 |
|---|---|---|---|
| D29（旧P1） | 单份消息、真实终态、有限cut一致交接；root旧IAB cursor62/held63–70，后端已idle仍历史/live两份及Receiving，旧报告不通过 | 追新replayOwner/bindingAuthority/selection代次/full+local reconcile接线；旧read失效可移交/退休，无新帧仍排空，真实gap走原恢复；**当前技术机制关闭** | F/d29-full-app-viewport-red保红；F新增D29测试及d30-final-full-app绿；root fixed-ui八Turn、cursor189、8唯一Assistant、held/replaying空；不伪称旧版通过 |
| D29四项root方案 | 旧报告接受条件：分离binding/viewport职责、hold明确owner/接手、full/local同reconcile→commit、保native输出语义；不是共同降低判据 | 本版核方案落实及原条件：旧finally不删新hold、后缀严格序号、stale current检查、无text去重/隐藏spinner/固定Stop延时；保原失败/当前真实App证据 | 详V2/previous-report.md第6节完整讨论；当前源码/启动指纹逐SHA，不以旧head标签替代 |
| V-E01 / E1–E4 | 旧完整Notebook/260帧Controller旅程被非法初始化/假Pending中止；默认折叠后旧DOM期待未更新，旧不能豁免 | 当前合法initialize/catalog/typed finitecut/Pending、原260帧和原结果断言完整执行；先真实展开再核tool/terminal；**原缺证关闭** | F/d30-final-targeted.log583/1可选skip、完整App62+Composer4/0skip；不把D33错期待混进此关闭 |
| D31（旧开放） | 原Gateway exact身份尚未公布首读合法unavailable；metadata成功后缺第二hint，页面不再重读。旧方案只条件接受，未关闭 | 成功发布同提交点比较exact四元组→锁外Profile hint→watcher trailing→FE局部input/同cut source；两external owner/rows不变全App及新5ed真实IAB，**当前技术机制关闭** | B/d31-research/{implementation-report,implementation-verification,source-manifest}/39项；B/root-d31-ui/{verification,source-start,metadata-trace}；前公布counter未捕获与UI精确耗时未测如实限定 |
| V-DEPLOY/V-GATES | 旧版未部署/自然生效/另一Validation，旧报告不能称整轮完成 | 仍为A10/O01/O02后继缺口，D32/D33修后新FE/APK必须重绑定；不因本次旧缺陷关闭改成已发布 | 原包完整保留；后继main/运行/保护/自然事实和独立门禁由root安排并另补 |

### 本次实质研讨链（供final-delivery与最终汇报主动摘要）

**D32：** 初始I08/R04保当前动作边界→独立发现合法活动Main+附件被controlledAction/公开Steer当提交→核06 §1.8后向root整包交回→root亲读原文确认无覆盖授权，提出恢复活动Main附件Stop/Interrupt、公开Steer同资格，保无Main维护Send等待及idle上传竞态→Verifier按原判据条件接受：Main活动依真实native事实、不以Pending=false认idle；file/photo/含文本/含无Pending均保草稿、Enter不触发取消类动作，公开入口不得先上传；后端竞态仍原子安全接收，不加busy/丢附件→当前尚无固定新提交/关闭证据，**保持违规/开放**。没有规格变更或判据放宽。

**D33：** 初始I08/R09/R10保当前06与新增读取覆盖→独立发现App直接回退预取/准备过渡，D30 G10使用已被覆盖旧期待，真实IAB passed只证明发生→root亲读06:53–58确认自己的4处App修改错误，提出恢复Orb异步预取、原target measurement、缺二级数据保一级准备/失败Retry、数据与几何就绪后完整展开，沿原owner/反向/降动效→Verifier条件接受并强调一级running计时纳入目标、晚结果不重开已关闭/新owner、不重启动画；要求最新原文正式App反例/实际IAB过渡证据，撤旧期待保历史→尚未收到固定新提交/关闭证据，**保持违规/开放**。没有要求用户重新批准已明确语义，也没有降低当前标准。

本次新发现说明旧“所有相关测试全绿”与现行规范之间仍需全篇优先级核验；D29/D31及其它通过机制有可复用证据，但不足抵销两项明确产品偏离。root已决定本版固定5ed/edb整包交回，不等F1 dirty修补；新候选须再派全新独立全范围审查，不能把本报告改成仅D32/D33补测报告。本版未操作任何UI/生产/用户状态、未提交部署或复跑大套。
