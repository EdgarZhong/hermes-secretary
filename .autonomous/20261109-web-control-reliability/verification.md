# Verification：20261109-web-control-reliability

## 1. 审查对象与结论概览
审查者：独立 verification_final（非实现者，无实现上下文输入）。日期：2026-11-09。BE：93c3b6d0bd0b91c110760c15f8063aec2d3b9a22；FE：9f525d33a328740490337f065c225f2462b576d9。依据为本目录 snapshot-index.md 与 baseline.txt 指定的冻结原文；二级索引只用于定位。产品只读，报告及 independent-verification 证据目录可写。第2节先于代码、测试、动态看板与历史审查阅读落盘，原始副本为下述 independent-verification/criteria-initial.md。首版概览中的FE SHA重复拼写已更正，判据未改变。

**总体结论：Verification 不通过，禁止把当前候选作为已验发布包。** 已核37条：28条符合其适用机制、5条违规（R01/R10/R11/R13/R19，同一D29根问题）、4条证据不足（R28/R29/R30/R37）。违规不是5个独立缺陷。D29为root真实隐藏IAB观察并有同版启动/DOM转录/原生消息提交元数据的范围内反例；本审查者未操作该保留页面，未把JSDOM绿例抵销真实UI反例。追加只读Controller现场表明事件已经到浏览器但仍held，当前恢复错误宣告完成；由此把R10/R11原“符合”修订为违规，判据不变。R28/R29的不足属于未来发布事实尚未发生；部署前保护机制及APK构建已核，不要求为了本次审查擅自部署。R30的另一独立Validation仍为后续门禁。R37包含两个完整旅程尚待补齐的测试证据，见第5节；旧版同样红不作豁免。

工作区HEAD 62aea9f2b60de8d9b946ac650b04d294559c0d22 相比待审BE仅CLAUDE及plan变化，产品树相同；FE为指定HEAD，五个既有.DS_Store未碰。没有执行生产、模型、浏览器、数据库写操作、提交或大套复跑。独立取证为源码追踪、同版指纹复核、原始日志/trace/产物核对；新证据写在BE `.hermes-dev/web-control-reliability-20261109/independent-verification/`。

## 2. 独立要求清单与覆盖
独立起点：2026-11-09，仅依据 U01–U15、E01、06 最新合同及保留条款、白板、07、02/04/01/08 明确保留部分及 V4/V3 继承合同形成。优先级为最新用户明确确认→白板/07→02→04未替换增量→01 Hermes-first；历史“已验/未实施”只属其原时点。白板/07 的其它成熟功能不是本轮重做目标，但作为控制/生命周期修改不能破坏的不变量核查。未知历史关闭原因、无 ADB 和发布后事实不得以本地测试代替。

以下所有判据在实现调查前冻结；核查位置列指第3节同编号。后续只能按原文补充，必须记录变更理由，不能迁就代码。标“机制薄弱”指规格未给出完整接线细节，仍须满足所列正向机制。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| R01 | U01；06:3–16、18–43 | 本轮覆盖/归因 | 直接：复核所有可复现已报故障；未知现场原因保持未知 | 原问题均有代码路径、反例或明确证据边界；不称已证网络抖动 | R01 |
| R02 | U02；07 §8.15；08 §2.3 | 所有内部运行/机制薄弱 | 同一实际 Main，无来源权限分叉 | 普通、Reminder、HB、delegation、Idle/手动维护均可绑定实时状态及适用输入/Steer/Stop/Interrupt/取消 | R02 |
| R03 | U03；06 顶部 | Gateway/租约 | 只允许真实独立 Gateway 活动造成 Session busy | 历史 source、路由、服务在线、未知 owner 不当 Gateway；不抢租约/第二 writer | R03 |
| R04 | U04；06 C3 | 原子受理/机制薄弱 | 原生 owner 下普通/Steer/安全等待统一选择 | 启动/终止/停止/维护/前端idle竞态不会吞输入、双执行或无故busy；旧调用默认兼容 | R04 |
| R05 | U04；06 C3、P09 | operation/未知回执 | 稳定身份，可查询；未知不当失败 | 同ID幂等；超时/断线查询原ID；不自动重发，附件不默丢；重启状态诚实 | R05 |
| R06 | U05、E01；06:11–15 | Idle/手动维护 | Send接收等待；Stop取消维护保已受理输入 | 安全边界继续处理；Send不暗取消，committing不伪取消，主Main不存在时Stop不丢queue | R06 |
| R07 | E01；U06；07 顶部取消条款 | Turn内压缩/取消 | 主Stop停止父Main并取消未消费；独立取消仅维护 | 精确当前operation，停止Main不等待Pending读取/冷建；普通未提交Note联动取消、已提交保留、Force不可取消例外 | R07 |
| R08 | U06；06 11/1维护流式 | 压缩运行/恢复 | 压缩独立身份和真实阶段，不当普通Turn | 初进/重连恢复当前部分摘要及真实状态；取消/提交/超时边界不串operation | R08 |
| R09 | U07；02 §1–2；08 §1 | 身份/隔离 | Profile/ref/lineage/Turn/op/epoch各有归属 | 同活父、真实绑定；合法压缩不换ref，fork/new不继承；无第二writer/身份字符串猜测 | R09 |
| R10 | U07；06 C0–C3、D/S/P矩阵 | 页面恢复 | 当前可见完整对账、有限切点、有序后缀 | 初进/断线/重连/epoch变化/owner切换/失败重试完整；旧轮次不能覆盖；不自动reload或重放写 | R10 |
| R11 | U07、U13、U14；06 11/8正常恢复 | 正常业务 | 事件/回执正向提交，局部刷新 | Send/Steer/开始结束/压缩/外部落库不无故整页恢复或重复激活；失败只重试相应范围 | R11 |
| R12 | U08；06 C1、C8 | Fanout | 有界、顺序、慢端隔离 | 健康突发/大帧不误踢，真实慢端有界退出；seq及legacy/typed对应一致，多订阅恢复并发 | R12 |
| R13 | U08；06 C2 | Unknown流式 | 不弱化身份，不猜文本 | 同已证片段继续追加不逐chunk裂；Thinking/正文/工具边界保真，Unknown不当running | R13 |
| R14 | U08；06 C3；06 §1.6 | 按钮/键盘 | Main事实与Pending资格独立 | Pending=false不能断言idle；普通Turn Send/Enter同Steer路径；Escape/原附件边界保持 | R14 |
| R15 | U08；06 C4–C5 | 双端诊断 | ID只诊断、字段白名单、异步有界 | connection/client ID关联；触发/诱因分开，close/队列/发送/loop/RTT/恢复量可见，无正文凭据URL查询/任意错误 | R15 |
| R16 | U08；06 C6–C8 | release Android | 常态滚动JSONL/固定只读导出 | UTC+monotonic、网络/前后台/版本、容量/丢弃；shell/root/app之外拒绝，ADB无需root/debug/reload；实机限制明确 | R16 |
| R17 | U09；06 11/8分组 | 历史折叠 | 已证结束与当前活动分别判断 | 新Turn/Steer/Interrupt/followup/分步checkpoint不全展开；未知边界后证同页收敛 | R17 |
| R18 | U09、U15；06 分组及P06/P08 | 显示选择/阅读 | 正文边界、未闭辅助段、稳定ID及用户选择 | 当前活动展开；结束闭段折叠；idle系统唤起保旧collapse/手动展开/阅读锚点；不靠remount刷新 | R18 |
| R19 | U13；06 顶部连续场景 | 连续流式 | 全链稳定，静态历史不能代签 | 手动→Steer→末delta/API延迟→结束前后HB/Reminder→后续流式单份消息/片段/真实状态无抖动或卡死 | R19 |
| R20 | U14；06 顶部 | 统一连接生命周期/机制薄弱 | 健康连接业务不主动关闭，所有意外关闭恢复 | 未知码、观察者异常仍重连，诊断不作白名单；明确直接关闭原因，恢复自动清对应未确认提示 | R20 |
| R21 | U15；06 顶部 | Gateway只读/机制薄弱 | 控制不可用不等于断线；持久消息和终态权威 | Gateway真实活动时逐条跟随落库、真实结束后既有分组；不要求token代理，不清历史显示、不整页恢复 | R21 |
| R22 | U10；adaptive V4 目标/状态表 | hot/standby | 默认暖高频、冷启才待机，无business候选 | 模型/思考变更后未使用按兼容证据；一般缺样本暖则hot，不由context/费用差单独停HB | R22 |
| R23 | U10；V4 C09–C13、C20、C23 | 缓存复核 | 执行前最新合同/真实due/TTL/前缀 | load/due/claim/首次API均不绕guard；无模型探测，无旧合同晚到覆盖；人工暂停不自动复活 | R23 |
| R24 | U10；V4 D1–D4、C14–C19 | 恢复/首读 | 正常User/Reminder后重评，高context尽快适宜整理 | 暂不适宜先恢复已暖hot；成功压缩仅一次当前owner合同边界首读许可，防重复/跨崩溃消费，计冷费；失败无许可 | R24 |
| R25 | U10；V4 C01–C08、C17、C21；V3保留 | 行为/维护分账 | 真人与系统分离，费用/时长真实 | 一次输入一次事实，等待非blocked_send；取消零调用不填正常量；规划max(Note,Compact)、Main阻挡另计；原HB anchor不重设 | R25 |
| R26 | U10；V4 C08整改/R4合同 | 历史推断 | 同独立离开段、knowledge time、近期权重/删失 | 提醒条件超真实覆盖上限回一般分布；不未来泄漏/重复增权；完整历史/敏感性负例和费用劣例如实保留 | R26 |
| R27 | U10；V4 C16/C22/C23；08 | 计划/持久状态 | 所有目标/开关/人工控制及owner配置隔离 | 新选择/配置/边界使旧维护计划失效；重启/并发不双领、不补积压、不复活人工暂停 | R27 |
| R28 | U10 | 发布后算法事实 | 合main且线上实际接线/配置/自然运行 | 线上版本、真实配置、自然运行决策对应V4 R4；本地绿不替代自然生效事实 | R28 |
| R29 | U11；08 §2.1；06部署 | 联合发布 | 正式main，Web/原证书递增APK，完整版本核 | main/构建/HTTP/进程一致，保护DB/绑定/模型/dirty；两套完整三库备份；源码/构建不冒上线 | R29 |
| R30 | U12；autonomous-run门禁 | 独立门禁/完成 | 本轮完整独立Verification与Validation，root亲审 | 同版证据可复用；无ADB自然网络明示；未验不得称通过；发布后事实仍需闭合 | R30 |
| R31 | 白板 A/O/C/I/U、07 §2–4/8.11 | Notebook保留不变量 | 原文事实源/派生、单Noting writer、完整任务 | 不因控制改造扩大Main写/Noting工具权限、改候选审批/清退/来源，模型可见世界及稳定前缀不变 | R31 |
| R32 | 白板 K6/N1–N6/P；07 §3/4.5/8.1/8.13 | Noting提交/失败 | 独立child冻结活父、至多5Turn、finish后runner原子提交 | 停止/并发/重启不发布草稿；anchor/pointer不回退，FM只当前有效完整Snapshot，不误开Turn | R32 |
| R33 | 07 顶部10/28解耦；§8.1 | 联合生命周期 | 普通并行、Idle正常提交后压缩再FM、Force区间一次 | 不把Note与Main忙混合；取消关系及owner保活有界；原生必须压缩不等Noting；失败回收准确 | R33 |
| R34 | 07 §6/8.14；02 §3.10–12；08 §2 | Scheduler/ACK | instant idle运行、busy→deferred；真见证/请求成功ACK | 控制改造不改变排期/claim/撤销/投递语义；冷runtime/无浏览器照常；profile与source正确 | R34 |
| R35 | 07 §8.15；08 §1/2 | Heartbeat/内部来源 | 原Conversation原生Main、持久owner/合法tip | 暂停/clear/new/fork不继承；无重复tick/重锚/跨渠道自动外发；适用Web真实流控制 | R35 |
| R36 | 02 §1/2/5；04 §2/3/4.4–4.7；01 Hermes-first | 继承边界 | 原生Loop/模型/Provider/权限/缓存，增量兼容 | 不造调度/路由/第二会话库；默认关闭原生、可选字段兼容；未改核心合同不回归 | R36 |
| R37 | 06 §0/1/2、C0–C3；08 §3 | 当前页面范围/展示 | 正文/详情/分页/草稿/附件/认证/Files归属 | 仅当前需求，列表摘要不绑全部runtime；缓存不授权限；真实失败可见、旧owner撤销，阅读与细节不丢 | R37 |

## 3. 逐条实现证据
| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| R01 | FE Controller→reduceProjection→projection.ts:802/911；root真实App | 手动首Turn完成→第二Turn→Enter Steer→原生后继末delta→Stop，无断连/刷新；后端idle而同UID历史/live双份及Receiving response残留 | B/root-final-ui/{observation.json,backend-idle.json,native-turn-metadata.json,source-start.json} | **违规**：D29仍是用户已报重复/末尾转圈范畴，不能声明全部可复现缺陷修复 | 原现场历史1005/1006诱因仍未知；D29是本次隔离可复现代码结果，不倒推其为原生产唯一根因 |
| R02 | BE methods_web_control.py:233/298→原生prompt.submit/_run_prompt_submit；session_lifecycle；FE controlledAction/Controller/StopReceipts | 普通、Reminder/HB/Delegation统一native runtime控制；输入state及审批/Pending/维护各有原资源恢复 | B/final-new-tests.log；B/final-owner-maintenance-stop.log；F/r7-final-live-controller.json；F/revision-integration.log | 符合：控制资格不按内部触发源分叉；实际RPC/Loop/SQLite代表链已连接 | 后续输出交接D29另判；受控Provider，不声称生产模型行为 |
| R03 | BE methods_web_control.py:40/147；active_sessions.observe_native_turn_owner | exact native lease holder+活registry+DB/ref证明Gateway；未知外部为4090，非4009；历史wechat无活动租约可正常输入 | B/gateway-display/final-scope.log；tests/tui_gateway/test_gateway_read_only_follow.py:196；test_web_input_ownership.py | 符合：没有历史来源或holder字符串推断/抢writer；纯服务在线不拒绝为Gateway | 不包含跨进程控制broker，原文明确不做 |
| R04 | BE methods_web_control.py:176/203/233；methods_submit_idle→_lock_in_submit_turn(admission_held)；session_auto_continue:468 | 原history_lock/原准入决定idle/starting/running/maintenance/settling；先durable witness后可执行queue，Stop世代阻止旧摘head复活 | B/final-plain-lock-control.log（11文件67）；B/queued-claim-stop-green.log；B/final-new-tests.log | 符合：正式普通Lock下运行，修前RLock假证明不再使用；新可选input_policy保旧默认 | 不把所有未知owner变成可并行writer |
| R05 | BE web_input_receipts.py:27/111/181；operation_status:284；FE prompt-submit/readPromptAcceptance→Controller.acceptPrompt | stable operation_id+digest；先查询旧见证；epoch变更返回unknown/runtime_restarted并可取原输入；未知ACK只读查询，迟到ACK不清新草稿 | tests/test_web_controlled_input.py:45/158/202/220；B/final-shared-input.log；F/revision-integration.log及controller-submission-review.test.ts | 符合：幂等/同文不同op/通知失败/重启未知边界真实；附件queue保持 | 重启不自动重放RAM工作，作为已登记工程边界，不能称unknown必未执行 |
| R06 | BE _web_waiting_input:203、_web_stop_maintenance:71；compression_read:149；_drain_queued_prompt | 维护Send保存waiting且不cancel；Stop只取消无Main维护，finish/cancel/too_late均等安全边界再消费 | tests/test_web_controlled_maintenance.py:53/251；B/final-owner-maintenance-stop.log；F/r7-final-live-controller.json的maintenance_custody/natural_maintenance_commit | 符合：E01明确的等待保留与安全边界，未把Send计为取消 | partial只是运行展示，不冒充有效摘要 |
| R07 | BE _web_prepare_stop:25→session.interrupt→_interrupt_session_turn→agent.hard_interrupt(require_turn_id)；compression_read.cancel_compression | Main Stop取消未消费queue/Pending；startup latch不等cold build；expected token/Turn经过commit wait后再验；独立维护cancel exact op；noting_joint.cancel_operation排除Force且只未提交admitted | B/stop-fence-tests.log；B/final-owner-maintenance-stop.log；B/final-stop-default-hooks.log；tests/test_web_stop_target_fence.py:13/89/149 | 符合：目标fence与锁内清理防旧Stop影响新Turn，原默认入口保留 | FE残留显示D29不等同后端Stop未执行 |
| R08 | agent/compression_read.py:78/118/149；auxiliary_chat_stream→CompressionObservation.append；FE CompactionViews/Updates→MaintenanceActivity | op独立，65536 code points有界partial/revision/offset；exact缺口读仅补同op；Idle request未注册阶段仍暴露publication_id，可取消且已commit不伪取消 | B/final-maintenance-contract.log中的维护7项；F/revision-integration.log的partial/取消；r7真实自然commit链 | 符合：正常delta零RPC、旧op终态不覆盖当前；重连原资源读取 | 同文件contract catalog另有旧失败，不把整文件计绿；构建JSON-RPC摘录另核 |
| R09 | BE _web_control_session、_find_live_compression_owner、resolve_conversation_ref；FE scope/profile/runtime/epoch current fence | root42源same loaded版本；真实rotation恢复复用活父；foreign profile 4003；消息/receipt按ref解析合法tip | B/final-plain-lock-control.log；gateway-display/network-evidence.json；F/r7-gateway-live.json；independent-verification/loaded-source-check.json | 符合：未新增writer/身份库，不以source/格式猜归属，合法lineage连续 | Gateway delta代理不属于要求 |
| R10 | FE ControllerPageRecovery:843/851、installCut:1321–1352、commit:1497；Controller.event:1260 | 原恢复代表链绿；D29当前cursor62/replaying=true，63–70连续已到浏览器但仍held，含65 committed/67 closed/68 complete；page却committed/ready/backgroundSettled | root-final-ui/client-owner-read.json；F/r7-final-targeted.log及r7-final-live-controller.json作有限对照 | **违规**：当前有限切点及连续后缀尚未实际交接就宣告恢复完成，违反完整自动恢复/正向提交合同 | 尚未认定导致hold未释放的具体根因；不存在Socket断开证明，不以重新刷新替代 |
| R11 | FE pageRecovery.changed:310、readContinuousCut:1226、commit:1497；Controller.event replayHeld分支:1260 | 健康连接上正常history-invalidated局部提交完成后，replaying仍为true；终态持续进held、不进入reduceProjection；state与render同version503且非frozen | root-final-ui/client-owner-read.json；observation.json；native-turn-metadata.json | **违规**：局部业务对账未把已收到有序终态交回实时owner，原正向更新责任未完成；不能只隐藏恢复/接收提示 | JSDOM正常round不变证据不能排除该局部commit交界；不凭此臆测所有失效都过度恢复 |
| R12 | BE transport.FanoutTransport.write_ordered/_admit_frame；output_identity._native_write；ws FIFO write/async batch | prepare→stamp→serialize→queue同admission owner；consumer独立锁，inflight仍计量；256批/4MiB普通容量+单逻辑大帧/twin槽，慢端主动退出；Stdio/Tee兼容 | S/green-final-transport.log；S/green-identity-fifo.log；tests/test_stream_event_order.py:154/329/438/547/592；旧C1三订阅1046帧证据 | 符合：真实并发与大序列反证覆盖，seq不是仅ring有序而wire逆序；无删事件/无限队列 | 单个原生大结果本体仍按其固有大小，槽只容一组，非任意新增字节上限 |
| R13 | FE native-output.ts:284/320及projection.ts:802/911 | typed片段由native owner/source_event_seq绑定，Unknown追加路径保身份；但D29在commit65、closed67之后同一UID两份仍呈现 | root-final-ui/native-turn-metadata.json（65 source row8、67 closed）；observation.json | **违规**：当前输出对象未在其持久交接后收敛单份；旧Unknown绿不能证明这一合法Stop分支 | 根因尚由实现者调查；不得文本相似去重或放宽owner掩盖 |
| R14 | FE ChatComposer→command-actions→controlledAction；projection composerActionPolicy；BE _pending_steer_native_active_turn | 主Stop不依赖草稿/Pending读取就绪；内容动作按钮/Enter统一controlled submit；真实Main与Pending分离 | F/r7-final-targeted.log中app-steer-busy；F/revision-stop-actions.log；BE final-new-tests.log | 符合：正常手动Turn也可Steer，Pending inactive不误当idle；拒绝字段精确消费 | D29的Send按钮正确不等于整个Timeline已终态 |
| R15 | BE connection_diagnostics白名单及ws close owner；FE client.ts:126/299、connection-diagnostics；Android DiagnosticSchema | server/client id仅诊断；本地主动4100固定reason，server只记peer claim；未知reason不落盘；数值/固定枚举不收内容；所有close共用重试 | B/close-origin-audit/implementation/backend-close-tests.log（24）；frontend-api-tests.log（50）；原C4/C5脱敏；最终source-manifest逐SHA | 符合：直接触发与上游诱因明确分离，日志不作权限/重连门禁 | 原20:42 1005的客户端主动入口仍未知，无网络占比结论 |
| R16 | Android DiagnosticSchema/DiagnosticStore/DiagnosticsProvider；正式android:build→android:verify→导出脚本 | release私有滚动4×2MiB，固定URI与UID检查；DUMP权限，应用/shell/root之外拒绝；provider/schema各6绿；包0.1.14/1014原证书/非debuggable/439资源对齐 | F/release/apk-release-report.md、final-TEST-*.xml、artifact-binding.json；independent-verification/artifact-check.json（APK/archive/manifest全匹配） | 符合已授权机制和产物；原文明确无设备须披露，故无ADB不冒充实机通过 | ADB设备/自然运营商网络未验；修D29后此旧包应作废重构建 |
| R17 | FE timeline-folding.tsx:20/67/119；boundary mark、completed frontier、same native Turn | 分步checkpoint/Unknown时保已证completed边界；新Turn封存旧可见前缀；后证可同页修边界；保持当前活动展开 | F/r7-final-live-controller.json 103次DOM提交旧fold保持；F/r7-pure-idle.json（有限复用）；fold组件25项 | 符合当前证据：没有以起点未知将所有历史展开；D29 observation也明确旧折叠保持 | pure-idle的40源旧lab差3个Gateway文件，不能称完整当前BE同版；其非Gateway路径未受差异影响 |
| R18 | FE FoldedTimeline持久choices/links及boundary owner；external-turn-folding.ts:31 | prose闭段默认折叠/末未闭继续可见；选择绑定稳定source/facet，scope隔离；system唤起不抹旧选择 | F/r7-pure-idle.json HB/Reminder各lastdelta/API/terminal；F/r7-gateway-live.json 24提交；root D29旧fold仍保 | 符合：实际新/旧活动分开，手动选择保持；未靠remount恢复 | 阅读锚点按既有viewport机制保留，真实视觉流畅度仍由Validation验 |
| R19 | FE正式Controller/Gateway/Timeline；BE native Loop/SQLite→output commit/closed | 同版JSDOM连续链原绿，但root同版隐藏IAB经第二手动Turn/Steer/后继Stop合法路径复现：row8已持久，native_active_turn=null/running=false/phase=idle，历史+live两份及接收spinner | B/root-final-ui整包；F/r7-final-live-controller.json作对照而非否定反例 | **违规，P1 D29**：连续边界单份、准确终态不满足；因此不得进入发布完成 | 受控loopback SSE，不称Kimi特例/网络原因；真实UI反例高于静态历史/单一绿链 |
| R20 | FE client.ts:126/299统一connect/endConnection、PageRecovery.deliverGateway/deliveryFailure | ready先resolve/heartbeat；retire先结算pending/安排retry后best-effort close/通知；所有意外码重试，listener逐个隔离；业务异常只invalidates覆盖不close | close-origin-audit/implementation/frontend-api-tests.log；F/r7-persistent-observers-green.log；client.test.ts；BE peer close tests | 符合连接机制：诊断白名单不参与重连，旧attempt重入防污染 | D29是健康连接上的输出交接缺陷，本项通过不代表整个正常业务完成 |
| R21 | GatewayRunner真实租约/turn metadata→DB source/writes→change_watcher→sessions.changed→FE observeExternalInput/readContinuousCut/externalFoldTurn | 两起点already-open/cold-active，source前active、source回填、3次逐条durable append及terminal；无Gateway token delta代理、无轮次/Socket重置、旧fold保留；释放后Web Send/Stop | B/gateway-display/{network-evidence.json,final-scope.log}；F/r7-gateway-live.json；启动42源和FE47源独立核0漂移 | 符合：Socket、写控制、durable进展、外层折叠各守事实；未知owner拒绝但不伪Gateway | 不是完整生产微信adapter送达/实际网络验收 |
| R22 | adaptive_cache.assess:72→adaptive_policy→adaptive_store/adopt；config/model_config | 当前合同暖则hot；明确不兼容/真实TTL过期则standby；无business候选；缺行为历史只暂缓维护 | A/source-r4-final/manifest.json27源独立核0漂移；A/r4-*；test_adaptive_cache、standby_wiring | 符合：当前合入候选即指定R4，未偷偷修改公式/阈值 | 不保证Provider命中；D1/D4工程参数未冒充用户逐数值亲选 |
| R23 | heartbeat_store:load/due/claim94/claim_is_current136→adaptive_cache_runtime.inspect_conn10；usage_read→adaptive_runtime.request_started336→block_first93 | 真实API前复核当前配置/contract/epoch/path；无探测；首冷HB零调用guard保真人后继，source不改成user绕guard | B/final-heartbeat-observed-warm.log；test_web_controlled_heartbeat.py；A原C09–C13/C23机制证据 | 符合：决策不止Main结束时旧判断，guard首次请求接线未被控制改造绕过 | 观测一般缺项仍按规格hot，非所有未知一律停 |
| R24 | adaptive_cache._recovery55、assess；runtime._maintenance/request_started；store.request_start事务 | 成功真实缩减+同配置/epoch/path产生首读，request_start防崩溃重复；取消失败无成功许可；正常User/Reminder结束重评，暂不宜整理先暖hot | A C14–C19/standby_wiring真实事务与重启机制；B维护自然commit和cancel实链；27源同R4 | 符合：许可/费用/重评与原生提交相联，不靠被关闭HB自救 | 线上自然许可消费仍待R28 |
| R25 | adaptive_runtime.web_submit_input620→web_input(event_id)；_web_waiting_input只接收，不blocked_send；_snapshot/maintenance | 同operation输入事实去重；waiting非拒绝；HB/Reminder source独立；规划max两组件、Main阻挡另账；anchor不变 | B/test_web_controlled_heartbeat.py；final-shared-input.log；A C17/C19/C21及R4回放；原事件账本 | 符合：未把新queue接受伪记blocked_send，未将取消零调用纳入普通量 | H/C/M和费用条件性保留，不称实扣节省 |
| R26 | adaptive_reminder_history→stage_history/forecast/rollout；27源与R4字节相同 | 一个独立段选一个已知Reminder，不偷未来标签；过已观测后继覆盖上限回一般分布；E06/R2/R3失败、留一段399.6s负例保留 | A/r4-afternoon-continuation.json、r4-afternoon-leave-one.json、r4-windows/6h/24h；review/r4-final-provenance.json | 符合指定算法及诚实证据合同：GPT完整条件4HB/0维护/0等待；删除关键段仍失败如实 | 稀疏支持/条件成本不等于概率校准、普遍省钱或未来无阻挡 |
| R27 | runtime._plan_adoption_current/_idle_plan_valid；adaptive_refresh；heartbeat_store claim/refund/version；原noting_scope | 持久选择/owner/配置边界校验；旧plan不被暖旧runtime执行；人工pause/clear/全局关/非目标优先，保原anchor | A C16/C22/C23及持久新选择红例关闭；27源同R4；B/final-related-regressions.log | 符合：无新调度器、跨profile迁移或自动恢复人工暂停 | 线上配置/自然采纳由R28另闭合 |
| R28 | 计划发布输入含指定V4 R4；prepare.py/readonly adaptive probe | 本地27源已合候选，未正式发布本候选；当前无可把线上进程/配置/自然决策归到93c的事实 | B/release/{prepare.py,adaptive_readonly_probe.py}；control-recheck/root-audit.md；operations当前事实 | **证据不足（发布后事实）**：不能以源码合入/离线preview冒称线上自然生效 | 修D29、全新复审与Validation后，从main发布，采同进程版本+真实配置+自然User/Reminder/HB决策/guard/首读账证；不得操纵生产会话模型测试 |
| R29 | release.prepare→remote_release preflight/apply→post_phase/retention；FE build/verify | 已构建9f525原签名APK/439静态，独立复核SHA；发布器拒非main/dirty/版本不符，核DB/配置/绑定、停止前后保护及两套三库；未执行发布 | F/release/artifact-binding.json、apk-release-report；B/release脚本；independent-verification/artifact-check.json | **证据不足（发布事实）**：准备机制有据，但当前源码/HTTP/进程main事实及两套新有效备份/正式APK联合交付未发生 | D29修产品后当前9f525产物失效，需新SHA构建及上线事实；不因已签名便允许发布 |
| R30 | 本次独立37条矩阵；autonomous-run门禁顺序 | 独立判据先落盘后源码/证据；本轮本审查不通过；另一独立Validation尚未完成 | criteria-initial.md；本报告；U12 | **证据不足（依赖门禁）**：不能称整轮完成；root亲审/新独立复审/Validation及发布后delivery仍需执行 | 无ADB真机和未知原关闭原因已披露，非擅自新增实机完成门槛 |
| R31 | unchanged notebook_store/model/contract/noting_tools/prompts；noting_joint.cancel_operation/finish_operation | 控制修改只读状态与原生取消接线；未引Main Notebook写/Noting外部工具权限；原文/provenance/候选/生命周期owner不改 | Git baseline→93c产品diff；07保留模块未改；原R4+本轮noting/policy相关回归 | 符合本轮不破坏边界：无新Prompt/Provider路由/候选审批语义 | 不是重新证明所有既有模型语义必然服从，不扩大到本轮外Prompt调优 |
| R32 | noting_child/build freeze/runner→notebook Commit Gate；noting_joint.require_commit/record_commit/cancel_operation | 单child至多5Turn、finish请求与提交分离，取消只admitted未提交，Force排除；有效pointer/完整FM仍原机制 | unchanged上述提交/工具模块；B/final-related-regressions.log；test_web_controlled_maintenance真实旧Note/取消提交边界 | 符合适用继承不变量：没有把观察状态当Snapshot成功或把草稿发布 | 未新增真实Noting模型采样，原有有效证据依原范围复用 |
| R33 | noting_idle_joint→request_parent_compaction(wait=False)→native request registration→noting_child idle completion→native Compact/FM | Idle request在Noting阶段已可读/可取消；普通并行，Idle正常提交后父压缩再FM；noting_joint取消状态CAS，已提交保留、Force排除 | code noting_idle_joint/compact/native_link；B/final-owner-maintenance-stop.log；F真实maintenance_custody/natural_maintenance_commit | 符合：没有把Noting活动等同Main活动；安全边界释放输入；owner冻结/保活仍原接缝 | 不为测试新造周期或放宽原生容量/前缀 |
| R34 | existing due scanner→ActiveReminderAdmission.commit/_run_prompt_submit；deferred materialize/Provider成功ACK；新增控制不改这些写点 | 冷runtime正式唤起同ref；busy仍原子pending deferred；source/claim/ACK与控制queue分离 | test_cold_heartbeat_host、internal-source-regressions.log；r7真实Instant正入口；unchanged reminder_request/admission/registry | 符合本轮继承：无独立Cron agent/排期改语义，持久carrier/ACK owner不被queue替代 | 非新增全量Reminder验收轮；相关旧证据未受代码影响才复用 |
| R35 | heartbeat persistent owner/host-only restore→原UI prompt_submit/native Loop；adaptive guard及控制队列分支 | 与普通UI相同实际Main；冷guard0请求不丢新真人输入；来源/原HB anchor/暂停及目标隔离保持 | tests/test_web_controlled_heartbeat.py；r7-final-live-controller实际HB；r7-pure-idle有限复用；R4机制 | 符合：没有把Heartbeat改成用户来源来获取权限/绕缓存保护，无新执行器 | 原UI/微信渠道差异仍按各自授权，不自动外发 |
| R36 | baseline→93c/FE diff；可选input_policy/op/ready能力，Facade/sibling；PM锁与模型路由未改 | 旧API默认保留，controlled仅capability opt-in；Stdio/Tee/custom transport结果/异常保持；原生Loop/Provider、Profile路径复用 | S/green-stdio-native.log；B/final-stop-default-hooks.log；contracts生成及FE protocol-parity；git依赖/Prompt无变更 | 符合：未新增原生schema/通用admission/API层级，非适用路径不强制controlled策略 | no-tmp旧历史命中仍真实记录为失败，未把它改绿或增豁免 |
| R37 | ControllerPageRecovery历史/详情/缓存/Files/认证/草稿；command-actions→Notebook临时结果 | 分区与owner保护大部分已有有效回归；但当前354/4排除中的E1初始化Notebook完整旅程、E2合法Pending的260帧全Controller末端断言尚无完整有效同版绿例 | F/r7-excluded-tests-clarification.md；r7-final-targeted.log；相关真实链仅覆盖其组成部分 | **证据不足**：两项完整旅程未执行完，不用非法fixture失败误指产品，也不把组成机制代签全链 | E3/E4为默认闭段折叠的过时DOM期望，合法展开后取证仍应补齐；root已派仅测试修夹具，不改产品 |

证据前缀：B=`.hermes-dev/web-control-reliability-20261109/`；S=`.hermes-dev/stream-order-fix-20261109/`；F=`/Users/edgar/code/hermes-secretary-web/.archive/web-control-reliability-20261109/`；A=`/Users/edgar/code/hermes-secretary/.hermes-dev/adaptive-v4-20261109/`。代码路径未标仓库时，BE为本仓，`src/`/Android为独立FE仓。

## 4. 核心目标及验证方法审查
1. **真正目标不是“按钮能按”或“测试大多绿”。** U13要求连续手动→Steer→原生后继/内部Turn交界仍单份且状态准确。D29的同UID历史+live和Receiving response在后端idle后残留，是直接用户可见反例；按钮恢复Send和旧fold保持都不能抵消它。现有矩阵因此保留违规。实现者需追踪source commit/typed closed/terminal/权威idle到原生对象退役与渲染提交的整链，不能只隐藏spinner或按正文去重。
2. **控制正向机制已接到正式路径。** 受理在原native admission和history lock下决定，durable witness先于执行队列；startup/maintenance→Pending用原native epoch，结束/Stop由世代和target fence保护。疑问反证包括RLock掩盖死锁、摘queue后Stop导致复活、commit wait后新Turn接管、通知异常反转accepted、同文不同op及重启unknown；对应定向用例确实使用真实Loop/SQLite或真实Lock，而非仅helper。
3. **事件机制不能降成状态去重。** BE原ring stamp有序并不足以证明wire有序，当前将prepare/stamp/serialize/admit放同发送owner；consumer和admission分锁，大结果编码不阻断已完成发送credit；fallback、自定义transport和递归hook保旧语义。FE每runtime连续seq在副作用前核覆盖，缺口进既有恢复；不能靠忽略旧seq把合法晚帧吞掉。原反例、最终49传输/排序/身份/真实双WS证据按其范围复用，未加总成全套。
4. **Gateway只读是正常模式。** exact活租约/registry和同D1 source/windows证明当前外部Turn；原watcher在lease身份变更/到期和source回填后唤醒，纯renewal不发业务失效。FE先刷新input，再按必要同cut重读当前window，两个起点实际6次单条落库均在结束前自动呈现，terminal后折叠保旧选择。没有要求Gateway token代理，也没有把其缺控制权变成断线。
5. **证据版本审查。** FE47源R7清单及最后manual/Gateway before-import清单与9f525零漂移；两份BE启动42源与93c产品零漂移（详loaded-source-check.json），不能用启动head67a1b69代替这些SHA。早期backend-source-fingerprints/joint-precommit有后来Gateway/diagnostics差异，不能单凭标签复用；pure-idle旧lab40源差3个Gateway相关文件，仅其未受影响的内部入口/前端折叠路径有限复用。V4原27核心源与待审BE逐SHA一致，离线R4有效，但不等于线上自然生效。APK/archive/439 manifest独立SHA一致，签名/非debug/对齐依既有正式验证回执，未虚报ADB。
6. **测试不完整与旧红的处理。** FE354通过/4排除不能写358通过。E1未初始化合法PageRecovery/catalog、E2假Pending={}造成后半旅程中止，虽未证明合法产品缺陷，仍缺完整同版运行；E3/E4应按现规格先展开已折叠辅助组再验DOM，不以旧展开期望否定当前合同。BE旧protocol/catalog/source夹具红例、并行首次失败和后续定向绿证据分别保留；没有以“基线也失败”自动豁免本轮适用行为。未复跑大套，因同版正式路径已有证据且root在补所缺定向旅程。
7. **质量现状。** root-final-checks实际十项九过，no-tmp失败。独立`git rev-parse`确认所指20261031历史validation.md在12e与93c blob均为35daf5563d97496728892feb281ba89f5a7eb724；它是未修改的旧历史文字，不是本轮新增路径，但仍如实保留检查失败，不称“全检查通过”。health93文件0blocking/1advisory（Fanout raw Thread，原有线程拆分后显现），无抑制、改等级或新增豁免。本审查不授予改写历史报告或放宽规则的权力。
8. **发布完成与门禁分工。** U10/U11发布事实是整轮目标，部署前只能审main/dirty/保护/备份/构建绑定机制。当前D29优先修复；修复产品变化使已构建9f525 APK/静态失效，须重构建。后续从main发布并核源码、HTTP静态、进程/配置/自然V4决策、两套有效三库和交付APK；读preview/手动调用finish_turn不能冒称自然运行。独立Validation从真实入口检验，不能用本报告替代。

## 5. 发现、整改优先级与范围外项
| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| V-D29（P1） | R01/R10/R11/R13/R19；FE Controller.event:1260、ControllerPageRecovery.installCut/commit、projection/native-output；root实UI证据 | 无断连/刷新，第二手动Turn→Enter Steer→后继末delta→Stop；65 source row8/67 closed/68 complete已到浏览器held，cursor62/replaying=true；PageRecovery却committed/ready/backgroundSettled，render/state同503非frozen；backend idle但同UID历史/live双份及spinner。旧fold保持 | 用户明确故障仍可复现；恢复宣告完成与未交接有序终态自相矛盾。root真实DOM转录、只读Controller、native metadata和startup42源零漂移互相支持，不因JSDOM既有绿而关闭 | 主会话提通用正式切点交接/缓冲释放/退役方案，由Verifier按原判据评审；修复后保真实输入到DOM链及Stop/自然完成/内部接力/旧owner负例，禁止文本去重/隐藏spinner/放宽身份；全新独立全范围复审和Validation | **开放，发布阻断**；root已派F1调查，当前产品未修 |
| V-E01（P2，证据） | R37；F/r7-excluded-tests-clarification.md E1/E2 | 两个必要完整Controller旅程因未初始化catalog/非法Pending假响应而中止；后半断言未跑到 | 无法按当前有效证据确认Notebook临时输出跨Framework/后继Turn及260帧完整自动恢复；旧失败不是豁免 | 仅修合法初始化/正式RPC夹具，保原功能断言完成全旅程；E3/E4按现规格展开折叠再核工具DOM；取当前产品指纹，原红保留 | **开放，root已委派补证**；若发现合法产品失败转产品整改 |
| V-DEPLOY（完成事实） | R28/R29；U10/U11 | V4/RPC源码与APK准备完成，不代表main/云进程/HTTP/static/配置/自然策略已生效 | 整轮交付缺发布与自然运行事实，不能宣称上线或完成 | 先关闭D29及门禁，再main联合发布并核四层版本、原签名新包、配置/绑定/DB保护、两套完整三库、V4自然事实；不触发生产模型测试补数 | **待后续授权内发布步骤闭合**，不是要求本审查者部署 |
| V-GATES（完成事实） | R30；U12 | 本次不通过，另一独立Validation未运行完 | 不满足自主轮次收敛/完成条件 | 修复后全新独立全轮Verification→真实Validation→root delivery复核 | **开放** |

范围外新产品发现：无。既有不在本轮产品diff内的检查/测试红及原移动网络原因未知已在第4节保留；不由本报告扩成未经授权的规则、部署或网络归因工程。

## 6. 修复与独立复审
本审查是集成93c/9f525的全范围独立Verification，不是逐任务碎片验收；独立起点37条已先落盘并通知root，未以其后实现报告改变判据。后续补读同原文只用于覆盖核对，未新增/降低产品要求。原判据副本保持（概览FE SHA拼写误差仅在本报告更正）。当前无报告因缺列/缺行被root退回历史。

本轮接收到的讨论链：

- 原判据R01/R13/R19要求单份输出及真实终态→root在真实隐藏IAB发现D29并交完整observations/DB/native source元数据→独立审查核对正式projection/native-output/Controller路径与启动指纹，确认该反例确在当前待审产品、已提交/closed但仍双份；**维持违规**。
- 后续root提供只读CDP client-owner-read.json→独立复核cursor62/replaying、连续held63–70、ready/backgroundSettled、state/render同503，且正式Controller.event在replaying路径确可把终态留held后返回；R10/R11因此从原候选绿链支持的“符合”改为**违规**。这是新反证更新事实判定，不是改变/降低判据。实际阻断更准确指向恢复cut交接/held释放，尚不认定具体函数为最终根因。D29 source-start42源与待审BE产品独立逐SHA零漂移，结果在independent-verification/d29-source-check.json。
- root已提出先由F1调查通用交接机制、保现场、不以正文去重或隐藏spinner修补；当前尚无具体修复设计/产品提交交本审查者评审，因此不虚构“已共同收敛”或关闭证据。修复设计由主会话提案，Verifier只按原判据评审。此过程没有变更规格，不需要为满足既有“单份/真实终态”再请用户改写语义。
- root要求补FE E1/E2合法完整旅程及E3/E4展开DOM证据，本审查认可“修合法夹具并保持功能断言”作为补证方向；**尚未收到最终绿包，V-E01未关闭**。该要求不以旧版红作豁免，也不授权放宽产品输入校验。
- 事先约定的独立判据里程碑已一次交回；其它例行调查只在报告/证据目录留痕。未操作root保留页面或用户界面；没有派生Agent。

**root接收及现场续记：** root已完整亲读本报告六节并接收“不通过”结论；37条覆盖、D29、E1/E2缺证及发布事实分离全部保持，没有退回补审或关闭问题。root随后报告同一保留页面的新只读事实：`stagedConversation=false`、`continuousStream`不存在，但`replaying=true`且`held63–70`仍在；`conversationReads`保留6个同`recoveryId=5`、不同`viewport.first`的键，当前`viewport.first`为第二条Assistant UID `ffc5a525c17b4e0fb6c6ed885b58cc29`。证据继续归入`B/root-final-ui/`，新增字段由root补充；本次报告维护未操作页面，新增字段当前按root交回事实记录，不冒充本审查者独立读取这些字段。它进一步定位恢复读取/交接现场，但尚不证明具体根因或修复方案。当前没有具体实现提案，本审查等待F1整包调查后由root提出方案，再依据原判据评审；不提前设计、降低判据或关闭D29。修复后的全范围复审仍须另派全新独立审查者。

**root正式四项方案评审（后继记录，替代上段“尚无具体提案”的当前状态）：** 已完整读取F1的`F/d29-replay-handoff-report.md`，核对`d29-independent-summary.json`及`d29-full-app-viewport-red.log`。独立完整App红例使用正式Chat/useTimelineReading产生可见需求，外部DOM几何390×400、HTTP读响应实际返回后延迟40ms；原生Loop/SQLite/HTTP/WS真实，Provider受控。它在request91因viewport.first变化失效后遗留hold，cursor39、held40–67而page仍ready，并在“followup typed output delivered to client”处失败。该结果支持同类失效交接机制，不冒称完全复现root相同UID的Stop后DOM，也不把JSDOM几何当真实浏览器。

**方案结论：四项方向可接受，属于U07/U13/U14及原R09–R11/R13/R19/R20的工程细化，无需变更规格。** 当前仅认可其满足判据的设计条件，不认可实现已完成；D29及本报告不通过状态保持。逐项评审如下：

| root提案 | 原判据评审与必须落实的条件 |
|---|---|
| 1. 连续连接已证binding与viewport/history读取职责分离 | 满足R09/R10/R11，能够避免first alias变化反复reattach。借用须依据当前owner、epoch、connection及**有效连续序列覆盖**，不能仅凭page已committed、Socket connected、can_submit或没有recoveryError放行。当前可见/展开/分页新增依赖仍须按原完整内容及版本合同对账；合法未持久native-facet不能伪造成durable anchor，也不能因其尚未落库而永久等待。初进、真实断连、owner/epoch/覆盖依据失效仍走完整恢复。 |
| 2. 既有hold有明确读owner、接手与退休 | 满足R10/R11/R19。旧读只能处置自身持有的hold，新读接手须保留同runtime已收到的buffer及水位。连续前缀仍有效时，held必须沿原event reducer严格按seq一次交付，不越缺口、不重复投影/生命周期副作用；已经观察过的control不能被旧帧倒退。连续依据失效则由当前有限cut接手，不能仅delete布尔flag、清buffer或把旧owner证据借给新owner。取消/失败/无后续新事件时也须自动完成退休或移交，不能依赖用户刷新、再发消息或另一条通知来解挂。原有有界缓冲与溢出恢复约束保持。 |
| 3. full/local共用reconcile→commit义务 | 满足R10/R11及既有可见提交契约。localSerial/revision/demandVersion/owner有效性不仅在await前后检查，也须在**实际安装cut、更新历史/流状态和发布ready的提交点**成立；await后发现已过期，不能已经先把旧cut写进当前状态。当前staged cut及其有限连续后缀处理/移交完成后才能ready；若读取失败或真实gap尚未对账，保原画面、真实失败与自动重试，不假成功。采用有限切点，不为等最新尾部无限追赶，也不等无关后台请求；local可见需求变化仍按原范围重验。 |
| 4. 保正式native输出语义 | 满足R13/R19/R20。原commit/closed/terminal及同owner历史事实决定对象退役和终态，正向消除双份及spinner；不能通过正文去重、只隐藏spinner、固定Stop延时、放宽身份匹配、丢事件或关闭健康Socket达标。未提交/未知对象仍按原保真边界展示，不能为清残留一律删live。 |

**关闭前所需证据（沿原判据的必要分支，不新增产品门槛或阈值）：**

1. 保root70帧及原DOM/Controller/源SHA证据；保独立fullApp当前红日志。修后完整App沿真实可见需求+读延迟屏障完成原NewChat→手动→Enter Steer→原生接续→Stop，而非仅跑到旧失败前；同时完成自然结束及HB/Instant Reminder后继。每条链核state、RenderStore和实际DOM：同native UID只一份、closed/turnEnded等真实终态、spinner收敛、旧fold/手动展开/阅读锚点保持；正常连续连接不增加无谓reattach/整页恢复。root再用自建隐藏IAB原步骤验证，不能靠测试专属直接改state或手工解除hold。
2. 用真实读取屏障制造旧读失效→新读接手→旧结果迟到；同时覆盖新读已持有hold时旧finally、同runtime新Turn到来、owner/Profile/runtime/epoch/connection切换。证明旧读不能释放/覆盖新hold，新读不丢已收buffer；旧身份帧不污染新页，未消费写操作不重放。
3. 有效连续held严格有序一次排空，**最后一帧后停止所有新事件**仍能自动交接并退休；加入重复/迟到帧及真实seq gap，后者必须保buffer并进入原有限恢复，不能越gap自行ready。缓冲超过原有容量沿原恢复而非无限增长/静默删除；不改现有阈值。
4. full与local分别覆盖current staged、stale staged、read取消/失败、demandVersion或localSerial在await中变化及新可见依赖；旧cut不能提交，真实失败持续自动重试，ready不能与本代未交接的必要staged/held并存。确认source/UID/epoch/seq校验仍在原installCut，不以新白名单替代。后台非可见慢请求不能阻断当前有限可见交接，当前所需窗口也不能被借binding跳过。
5. D29修复后补E1/E2合法完整旅程及E3/E4按现折叠语义展开后的DOM证据，保原功能断言和旧红。新产品指纹明确后进行root亲审及另派fresh独立全范围Verification，再Validation；当前APK/静态绑定如受产品变化影响需重构建，发布后U10/U11事实仍另闭合。

研讨状态：root为正式提案方，本审查者依据既定判据作上述条件性接受；无规格变更、无判据放宽、无当前产品关闭证据。本次只更新第6节，未修改产品、测试、页面或生产；没有派生Agent。

**D31 · Gateway所有权公布后失效通知方案评审（2026-11-10，保持开放）：** 已读`B/d31-research/{report.md,evidence-summary.json}`，并追踪现有`active_sessions.observe_native_turn_owner`、`_write_entries`、`notify_history_changed`及watcher签名/trailing edge。独立研究起点为FE `edbddb6bcdef356ff83c71323d0fdbb6da201f8e`、BE PID28249启动42源快照；不是将本报告初始待审版本或后来HEAD冒称本次启动版本。研究先完成8个真实Web原生Turn并保持同Web Agent，再以独立GatewayRunner获取真实lease；本次lease提交至registry公布约28.03ms，页面首次input读取确在此间返回合法unavailable，registry公布后raw Socket已见gateway，而source屏障尚未释放的2664.6ms内无后继sessions.changed，页面仍旧值。该结果支持H1；本事件runtime为空且FE实际发了input读取，**H2同runtime过滤不是这个反例的原因**。原有正常Gateway链不抵销该竞态；研究Vitest的passed只表示测量/清理完成，`productContractSatisfied=false`不作验收绿。

**root提案的条件性评审：可接受，符合原R03/R10/R11/R21的正向提交方向，无须变更产品规格。** 在成功公布exact native owner身份的现有提交点补既有失效hint，解决“lease先醒、owner后公布但无人再醒”的事实缺口；不应放宽消费者认定Gateway的证明条件，也无须为此新增轮询、API、broker、writer或错误码重试分支。必要实施条件如下：

- 比较的是匹配host slot的opaque四元组`native_session_id/native_turn_holder/native_db_path/native_turn_id`，不是updated_at、TTL续期、渠道名称、holder字符串格式或推定的Gateway身份。沿现有PID/matching和真实所属DB路径，不改变slot、lease或Conversation归属；相同四元组重复观察不增失效通知。
- 只在四元组真正变化且`_write_entries`成功后，**离开FileLock**再发`notify_history_changed(db, session_id=实际native Session)`。无DB/holder/session、无matching slot或写失败不发“已公布”hint；不能在finally无条件发送。通知回调即使重入读取registry也不能死锁。
- 通知仍只是失效hint，不是owner证明、受理回执或权限。消费者必须重新核活SQLite lease、活registry及exact DB/ref/holder/Turn；公布后到消费前owner再次变化、lease结束或Profile切换时，旧hint/旧响应不得让新页面误得Gateway或写控制资格。通知异常按原best-effort边界处理，不撤销已公布metadata、不抛出改变原生Turn受理/lease/执行结果；也不把通知失败伪报为页面已更新。
- 原watcher必须实际消费metadata后marker变化，即使数据库source/body/rows完全不变也能产生后继失效；早lease通知与晚marker通知落在2秒floor内时，trailing edge仍保晚变更，不把旧signature提前消费。当前`_sessions_changed_payload`遇普通history marker变化会退回原宽hint `{}`，不能误说它产生精确Conversation证明；沿既有消费者仅刷新当前页input/必要有限cut及列表摘要，不扩成全会话正文/全部runtime激活或整页恢复。
- FE保持unavailable为合法未知owner状态，安全拒写且不伪称Gateway；它不是网络读取错误，不应被改成永久错误重试或自动重发输入。后继有效hint到达后须在同Socket/页面轮次/runtime自动重读并收敛到真实gateway及同cut `turn_source=uncommitted`，不用等source出现、用户动作或Turn结束。真正恢复依据失效时仍按原完整恢复，不为保持round数字强行沿用旧资格。

**D31关闭证据要求：**

1. 正式observer→真实registry成功发布→原Profile-aware history marker→watcher/trailing edge→sessions.changed→正式完整App局部input与finitecut贯通；把首查询明确置于真实lease已提交/metadata未公布窗口，先证合法unavailable，随后metadata公布且**source/body/DB rows不变、没有其它唤醒事件**仍自动更新gateway/uncommitted。记录同document/connection/recoveryId/runtime、请求范围及实际来源SHA，不能只断言notify helper被调用或独立rawRPC已正确。
2. 保已有8真实Turn/活Web Agent起点及连续多个external owner；分别核holder/Turn等identity真正变化有后继hint，相同identity及单纯updated_at/续期不重复醒。四个tuple字段的比较边界、无matching/PID不符/缺参数、registry写失败、通知异常、锁外可重入均有针对性证据。失败分支保原生受理/lease与已公布状态，不伪成功、不新增writer。
3. 跨Profile及合法compression lineage、旧owner晚到通知/响应、lease在通知与读取之间释放/更换、快速连续公布按最终权威状态收敛；未知/旧metadata继续fail closed，不能“有foreign lease即Gateway”。原通知可合并，不要求每个中间状态单独发事件，但不得永久停在已失效状态。
4. 验source公布后逐条持久append同页自动出现、真实外部结束后idle/原分组折叠及用户展开选择保持，释放后Web正常Send/Stop；确认不新增token代理、Socket重建、常态轮询或写重放。先用重启后新源码manifest的独占lab取得绿，root再以自建隐藏IAB验实际入口；不得把旧lab或研究instrumentation的SHA冒称修后运行。
5. 保D31原反例、版本与源SHA、no-post-metadata-event事实及测量passed的真实含义；修复后另派fresh独立全范围Verification/Validation。当前只接受方案条件，未读取修后产品/证据，**D31未关闭、没有新增通过声明**；本报告前部矩阵属于初始93c/9f525时点及所列证据，不能被用作D31后候选已经全轮通过的证明。

本次研讨只更新本节；root为提案方，本审查者依据原判据评审。没有产品/测试/页面/生产操作，没有派生Agent，也未新增判据迁就实现。

供最终交付摘要的实质项：统一控制与连接生命周期的正式机制已有证据，原1005/1006具体诱因仍未知；D29证明候选正常Stop终态仍重复且转圈，当前不通过；V4指定源码/有限条件回放不等于线上已生效；0.1.14旧构建因后续修产品须重新绑定；无ADB自然移动网络不冒验。后续应安排全新独立审查者重新提取全范围判据、复核D29修复影响及全部适用条款，再进入独立Validation，不能只复测D29一个样本。
