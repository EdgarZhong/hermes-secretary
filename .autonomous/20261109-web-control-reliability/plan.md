# 实施计划 · 20261109-web-control-reliability

## 1. 目标与依据

依据snapshot-index.md与baseline.txt（12e2b45）；产品起点BE main b4ed135、FE cd5d12f，集成V4候选b232后BE为2e91189。先复核旧故障，再沿同一原生运行实例实现完整Web控制，最后main联合发布／确认V4实际生效。root已完成旧故障首轮复核，尚未解决项不冒称完成。

优先完成纵向链：App输入→正式RPC原子受理→真实runtime/Pending/维护→流式／回执／控制结果。稳定operation、owner、commit fence先于展示。沿现有Session、原生lease、Pending和队列持久事实，不建新通用gate、writer、调度器或对话存储。旧默认接口保持，Web capability opt-in；首选既有prompt.submit增加input_policy=web_controlled，名称可在正式协议交接时沿现有类型风格收口。

完成条件：U01–U12正式接线和针对性证据、root亲审、独立Verification再独立Validation通过；main实际服务／静态／APK版本及原签名一致；V4自然运行可核；范围内缺陷清空。无ADB真实手机的现场边界明确，不伪称完成运营商归因。

## 2. 覆盖与任务表

| 任务 | 要求与依据 | owner／白名单 | 依赖与接口 | 验证／完成判据 |
|---|---|---|---|---|
| B1 后端完整控制 | U02–U08/U10；白板K1–K8、N0–N4、P1–P5、D6/D8；07顶部21–39、87–128，§3约680–715、§6 1641–1771、§8.1 1826–1845、§8.13–8.15 1999–2091；02身份、3.11–3.12、5.4–5.11，04原生边界／cache，08全篇，06最新合同 | backend_control；tui_gateway既有Session/owner、prompt、Pending、recovery、通知／scheduler_host、interrupt、web_read及contracts和对应siblings；agent/pending_steer、turn_context、compression_read/partial/observation及registration接缝；必要active_sessions元数据与gateway/run_busy claim接缝；对应tests。禁止改算法公式、Prompt、锁仲裁、原生schema、部署或核心文档 | 已集成V4；交F1原子受理能力、control快照、可查询输入receipt、maintenance快照／delta。先交可实际接线的协议和状态转换表作为一次完整里程碑，之后整包交回。维护Stop按本轮E01仅取消维护、保留已受理输入 | 真RPC＋nativeLoop＋SQLite，受控外部Provider；覆盖启动／冷建／结束／idle竞态／各内部来源／维护提交取消／Force／双窗口／tip／跨Profile／重启／ACK丢／真正Gateway及旧wechat误判。V4冷HB零API时已受理真人不丢、不改source绕guard；真人观察一次、无假blocked_send，原claim退款和Reminder ACK保持 |
| F1 前端故障与控制 | U01–U09/U12；06顶部、C1–C8、11/8折叠及恢复／局部更新／维护合同；07相关维护／Force／Heartbeat | frontend_control；独立FE src/api、src/core/controller及siblings、timeline-folding、ChatComposer与压缩展示、相关测试和正式生成协议；必要既有Android诊断白名单兼容，不改Gradle／依赖／版本／签名／根文档 | 先修折叠并审seq覆盖，后按B1正式协议接实际Controller/App；不以mock-only代替接线，不busy后自动retry | 同页未知→已证边界恢复旧组，active展开／用户展开保持；各phase Enter/button/Stop、查询回执、ACK未知／owner切换、维护部分摘要恢复；正常事件零整页恢复。seq必须核真实作用域，不能把合法全局跳号误判缺口；C2 Unknown/typed回归。UI仅自建隐藏IAB |
| A1 V4整合 | U10；算法V4 C01–C23、D1–D4与保留V3合同 | root；merge／文档／微小跨包接线，算法公式不委派控制权子Agent | b232已合入2e91189，27模块与原验收SHA一致；控制输入与adaptive接缝待联验 | 复用32文件556机制和独立23场景同版证据；补控制输入×冷HBguard／当前配置／首读许可／维护提交取消。线上只读核配置和自然request/decision，不制造生产模型测试 |
| V/Va 两独立门禁 | U01–U12全部适用条款 | 各全新无上文独立Agent，产品只读，分别report与ignored证据 | 集成收敛及root亲审后，先Verification，阻断清零再Validation | 按冻结原文先建矩阵；实际产品入口与隔离数据；同版证据复用，必要反证真实运行 |
| R 联合发布 | U08/U10–U12 | root；main合并、0.1.14版本、构建／部署与运维记录 | 门禁通过，稳定源码，原签名，服务安全空闲 | 原生main发布器、439静态manifest/HTTP、APK签名/ZIP/ELF/资源、双端ID；保最近两套三库；无ADB实机不冒称实导，脚本和格式仍交付 |

## 3. 当前状态与编排

| 目标 | 机制 | 正式接线 | 针对性证据 | 用户结果 |
|---|---|---|---|---|
| 0.1.12/13连接／Thinking／Enter修复 | 已有 | 已发布 | 有同版证据 | 不能证明全部历史断连已归因 |
| 折叠边界 | fallback永久保留已有候选修复，最新活动Turn全展开反证仍待闭合 | F1追加实际App交接 | root组件反例及用户最新现场 | 已证历史组在Steer／新Turn交接始终保折叠，当前Turn展开 |
| 内部运行完整控制 | B1首版／正式接口已交 | F1已接实际App，补回归中 | 初版机制与App定向测试，待整包亲审 | 0.1.13仍不合新合同，新候选未发布 |
| V4 R4 | 已合隔离分支 | 新控制待联验 | 27模块源相同、旧证据有效 | 尚未线上生效 |
| 联合发布 | 未开始 | 未开始 | 未开始 | 线上仍9270933/cd5d12f/0.1.13 |

并行仅B1与F1，仓库和白名单隔离；root负责实际diff／上下游审查、协议协调、证据覆盖与集成。子Agent禁止派生、禁止提交、禁止流水账；仅真阻断、必须root决策或约定完整协议里程碑发消息，整包完成一次交回。UI只允许自建hidden IAB visible:false，不操作桌面／用户页／外部浏览器。root无独立全局工作则等待，不按文件数监工。

## 4. 缺陷与整改、取舍与快照

| ID | 缺口与证据 | owner／状态／关闭标准 |
|---|---|---|
| D01 | activeStart fallback0被错误retained：idle2fold→active未知0→已证仍0→同状态remount1。FE .archive/control-recheck-20261109/fold-probe.*。用户最新再次确认active时所有旧折叠消失，疑似Steer接续但不排除其它入口 | F1已有knownness候选，追加真实Controller→App普通Steer／Interrupt接续／自然followup／native ID先于checkpoint／Unknown交接反例；保已证结束历史与用户选择，不误折当前Turn，不靠remount |
| D02 | 实际App idle-only rejection仍确认4009保草稿，启动／维护／终态拒非Gateway输入 | B1/F1待修，一次显式请求原子受理与对应结果 |
| D03 | 4→6→5探针可能丢5，当前controller只拒旧seq未验证覆盖，需核真实scope | F1调查；真实缺口则诊断／统一恢复，不误判合法过滤，不以Socket有流量冒称数据连续 |
| D04 | accepted=false／本地phase拒绝诊断不足 | B1/F1沿新协议补最小枚举，复用脱敏桥，不记录正文 |
| D05 | 维护Stop后waiting输入去向 | 用户已后继明确确认“取消维护，继续处理已接收的消息”；原E01工程收敛现获追认。B1/F1实现和竞态验证中 |
| D06 | root亲读Controller.cancelCompaction发现refresh省略捕获的profile；ACK等待中切Profile后readCompaction默认借当前Profile；cancelNativeCompaction异常分支未按operation明确查询 | F1已接收；取消ACK丢／Profile切换／同runtime ID跨Profile实际入口反例，保原操作身份、不重放取消 |
| D07 | B1接口里程碑亲审：先入queue后写durable witness，ensure False／DB throw未清envelope，可能5071 accepted:false后仍执行；持久成功后的通知失败亦须区别受理结果 | B1整改；正式drain验证拒绝零副作用、已受理可查、同operation零重复；连同idle native晚期4009只能由真Gateway证明 |
| D08 | B1里程碑删除scheduler_host的Gateway来源筛选，而Gateway仍独立claim，可能使既有通道Reminder宿主／出站语义取决于扫描竞争 | B1核查并保原路由边界；历史source不作为Web输入拒绝依据，不等于可任意接管投递；必要方案须root先亲审 |
| D09 | 重启受理见证保留，但首版input_state只列RAM queue、operation_status不带原输入，需证明冷启可恢复文本／附件与显式再操作 | B1/F1接口整改；不能只显示中断却找不到输入，未知已执行不得冒称未执行 |
| D10 | Turn内auto compaction期间接收的文本不能仅留maintenance队列直到整Turn结束；第一个安全边界应为压缩发布后当前native Pending再次可用 | B1闭合阶段转换；正式auto compaction→下一API反例，不把Idle或假flag测试冒充；附件沿原下一Turn完整输入 |
| D11 | Stop等待compression commit fence期间可能跨Turn；仅RPC前比turn_id不足，锁外abort请求／线程／child传播亦可能命中新Turn | B1在原interrupt owner增可选身份fence，真实barrier＋新Turn接管验证；旧默认和hard_interrupt兼容语义保持，拒绝不得有清队列／cancel／信号副作用 |
| D12 | root亲审StopReceipts发现unknown仅按runtime/epoch/页面存，旧T1未知会吞掉用户对新T2显式Stop；旧启动target为空时可能一直只查询，旧query还可能覆盖新目标状态 | F1整改；按精确目标/动作世代隔离，允许新已证目标的新显式Stop，同目标未知不自动重放；实际Controller/App及交错查询反例 |
| D13 | U02现有审批/澄清恢复补查：3种内部source同epoch重连后q0选择丢为stages={}，Confirm disabled；当前retain直接requests=[]导致 | F1正式反例approval-recovery-counterexample.log；窄修ControllerPageRecovery/ServerRequests同owner同epoch草稿保留及needsCheck。须当前open_requests对账才允许确认；owner/epoch/认证/请求payload变化及已结束不复活 |
| D14 | CompactionViews与CompactionUpdates两个读取owner都publish完整phase；旧A终态/changed读取可能覆盖普通读取已证的新B活动状态；同op确认取消后旧unknown notice亦需清理 | F1统一当前operation/phase提交owner和cut，exact旧操作查询不得覆盖新；两个读交错的Controller反例，普通delta零RPC保持 |
| D15 | E01维护Stop保queue后，waiting消息只有展示、没有显式撤回，会使误发等待输入无法阻止 | B1/F1补现有Prompt operation撤回，沿原queue/Pending/witness，不取消维护、不影响其它输入；consume竞态、已消费too_late、未知ACK只读恢复 |
| D16 | 新controlled 5071明确accepted:false仍被前端一概视为5xxx未知事务，保草稿但阻塞后续输入 | B1保证false无执行残留，F1区分明确拒绝与真实未知；同code有/无受理事实两支实际入口验证，旧端仍保守 |
| D17 | controlled提交事件/input_changed只查询phase unknown；RPC ACK迟迟不settle时，已收到精确受理见证仍submitting挡后续输入 | F1按同owner/op事件或input_state见证立即只读query并退役已接收事务；ACK一直pending仍可第二次输入，迟到ACK不改新草稿/重复执行 |
| D18 | root亲审等待queue drain摘head后、generation复核前的Stop窗口：旧恢复分支可能把已Stop输入重新放回queue，再被poller执行 | B1优先真实barrier反例；明确Main Stop不得复活已claim输入，保其它原生generation变化恢复语义；红→绿与receipt／零后继Provider证据待交 |
| E01 | 15:05:43未知1006缺client_connection_id；旧13:41刷新前停顿无现场时序 | 历史证据边界，不强归网络／代码；后续依双端日志归因 |
| E02 | adb devices为空 | 不把包校验/IAB冒充真机，交付如实标安装／自然网络／实导限制 |

root复核证据：BE ignored .hermes-dev/control-recheck-20261109/，FE .archive/control-recheck-20261109/。旧有效证据：BE connection-reliability-20261109/final-review.md、steer-busy-20261109/review.md及FE对应.archive。设计参考BE .hermes-dev/internal-turn-control-20261109/design.md仅作源码线索，不替代冻结要求。V4原件在原算法工作区.hermes-dev/adaptive-v4-20261109/{final-report,review}.md与verification-index.json，27模块已核b232一致。

no-tmp旧历史报告、旧Timeline测试及Android TV lint缺口保持原时点，不关闭门禁；新代码影响证据时定向补证。官方PM .venv，Python只用HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh。最终大型检查由root在集成收敛并派独立门禁后统一一次，日常只相关分区／正式机制／竞态。

root基线反证：main12e2b45、相关6个test／实现blob与2e91189一致，官方runner仅执行hidden_row_receipt与gateway_enabled_branch两项，均失败（各1.31／1.02秒）；证据`baseline-two-failures-12e2b45.log`。允许B1窄修fake签名透传accept_metadata，并将“禁止查找adapter”改为证明“零实际handle_message／模型派发／claim”，保原durable内容、display_kind、fire_count与Profile断言；不改产品迁就fake，不隐藏原失败。生成完整性中的review.summary为旧基线项，本轮compaction_delta须真实literal emitter通过，不能造假的emit或改扫描规则。

B1白名单工程补充：root亲读后允许`agent/auxiliary_chat_stream.py`在现有compression capture作用域通知实际Chat摘要增量，observer在累积锁外且不影响原模型流／超时／进度语义；无capture保持原生。`tui_gateway/ws.py`、`entry.py`仅增可选能力声明。此为既有维护流式要求的必要接线，不扩大产品范围。Responses已有observer不得重复发布。

F1白名单工程补充：`src/App.tsx`和`src/core/command-actions.ts`的实际Chat／Composer／Timeline控制接线；不改无关布局。仅Controller修改不能覆盖真实Enter／主按钮，必须一并接入。维护可Send和可Stop独立，不能因存在草稿就消失取消入口。FE无README为既有事实，不新建平行文档。

完整控制权包含既有工具审批／用户确认响应：root要求补核内部Turn→晚进入／重连→合法响应和旧owner拒绝；允许F1在现有ServerRequests恢复owner接缝修已复现D13，不新增审批语义／权限。B1对应核同一Agent/Fanout/原生open_requests及正式响应，已有同版证据可复用。

Stop接口收口：旧`session.interrupt`默认保持；新Web可选`input_policy=web_controlled`，`operation_id`指维护目标、`turn_id`指Main目标，均不是本次Stop动作的幂等id。服务端在原owner边界按真实Main／维护状态判断，目标变化不停止后来的run；ACK未知只查原目标，不能以自然结束反推Stop成功。允许B1在`agent/interrupt_control.py`及原`turn_context.py`身份绑定点追加可选target fence，沿既有锁，禁止引入新gate／锁体系或在history/pending锁中等待commit。

上述“不重放”约束指故障恢复不能自动重发旧动作；新的用户显式Stop仍必须有真实停止能力，不能被旧unknown记录永久改成仅查询。当前目标fence与动作世代保护新的动作，旧ACK/query不得清除或覆盖它。自动恢复只读原目标，不把自然终态冒称Stop成功。

发布准备仅本地ignored目录`.hermes-dev/web-control-reliability-20261109/release/`：沿旧已审remote_release/retention原字节，独立stage-20261109-web-control-014；expected_old=9270933、新包0.1.14/1014，尚未运行prepare／上传／发布。发布时按实际manifest核资源集合，不以旧439数量代替内容验真；保新批次和013、核验后清退012旧数据库集合。

快照：12e2b45冻结；2e91189纳入V4、核心文档保护与27模块指纹核；25baafb计划、63bd98f编排更新。新控制首版实施中，尚未整包亲审或独立验收。生产模型／排期／数据／凭据不作测试；原算法dirty与Huawei目录保持。
