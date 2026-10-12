# T3a Pending / Atomic Interrupt 实施报告

**交回提示：** 当前epoch的256 Web提交、64 Interrupt操作及最近8个结束epoch保留窗口，仍为Main已在根CLAUDE登记的“Agent自主收敛／待用户追认”，不是用户已确认。实现与本阶段机制验证已完成，待Main集中review。

## 接口里程碑（2026-10-12，已实施，待Main review）

依据冻结 `37ad76f5df` 的06 §0/§1.6–1.11/§2.1–2.4/§2.9/§3.2–3.4/§4.5–4.7，以及本轮plan与native-compatibility §11。只实施获派白名单；不stage/commit、不修改规格/根看板、不操作53445。

新方法均以runtime `session_id`寻址，可带原生`profile`。服务器验证请求profile与runtime owning home一致；compute-host/hosted/external代理不提供假parent状态，拒绝unsupported。`turn_id`为Hermes真实`_current_turn_id`，由native Turn起点发布，不能由浏览器mint。start/build window尚无真实Turn ID时返回inactive/starting，不普通Prompt fallback。

| 方法 | 精确输入 | 精确结果 |
|---|---|---|
| `session.steer_pending` | `{session_id,profile?,turn_id,operation_id,text}` | `{accepted:boolean,state:pending|consumed|withdrawn|rejected|inactive|compressing|terminal_conflict|unknown_turn|capacity,pending_id:string|null,turn_id:string|null,reason:string|null}`；同epoch+operation_id同text重试返回同occurrence当前状态；不同text拒绝operation_conflict |
| `session.steer_pending_snapshot` | `{session_id,profile?}` | `{turn_id:string|null,active:boolean,pending:[{pending_id,text,order,state:pending|handoff_reserved,withdrawable}],receipts:[{pending_id,state:consumed|withdrawn|rejected,message_uid:string|null,reason:string|null}],operation:InterruptResult|null}` |
| `session.steer_withdraw` | `{session_id,profile?,turn_id,pending_id}` | `{state:withdrawn|already_withdrawn|already_consumed|handoff_reserved|rejected|unknown,turn_id,pending_id,text:string|null,message_uid:string|null,reason:string|null}`；仅首次withdrawn返回原文，重复无text，不重复恢复Composer |
| `session.interrupt_pending` | `{session_id,profile?,turn_id,operation_id}` | `InterruptResult`：`{operation_id,turn_id,state:stopping|dispatching|followup_accepted|nothing_pending|not_active|already_transitioned|rejected|unknown,selected_ids:string[],followup:{session_id,stored_session_id,turn_id:string|null}|null,reason:string|null}`；新方法ACK允许stopping/dispatching，只有原生准入成功才followup_accepted；未知不可重发普通Prompt |
| `session.interrupt_pending_status` | `{session_id,profile?,turn_id,operation_id}` | 同`InterruptResult`；已退场runtime报原生4001，旧epoch已过保留窗返回unknown；不会再次dispatch |

请求非法/owner mismatch/不支持的runtime使用JSON-RPC错误（4002/4003/4010等新方法专属错误）；正常竞态结果使用表中machine state。operation ID最多128字符、不能为空。当前epoch最多256个Web submit operation receipts、至多64个interrupt查询operation；容量拒绝只限新增Web路径，不改变legacy steer的容量/返回。终结receipt只存ID、digest、终结状态及可用Message UID，原文仅仍pending/首次withdraw回包需要。最近8个已结束epoch保留在同owner内存，epoch退出保留窗后明确unknown，不能让旧ID在新Turn重新提交；不使用持久表。

新事件：`steer.pending_changed {turn_id}`只是失效提示，重新snapshot/query；`steer.consumed {turn_id,pending_ids,message_uid:string|null}`对应真实插入点或成功handoff；全使用原有event transport/seq。不修改既有event字段。消费前batch可能短暂claimed，但仍withdrawable；append时同owner锁重新取仍有效集合，撤回与真实插入只有一个winner。

锁顺序：Gateway admission/`history_lock`→Agent现有`_pending_steer_lock`；buffer内部没有另一把权威queue锁。真实insert只持buffer锁，不反向取history锁；通知一律释放buffer锁后发。`_session_persist_lock`仅必要读取current tip，不在等待provider/tool时持有。Interrupt reserve在history+buffer锁内，调用native Stop和线程等待在锁外；old finally在history锁内为reserved followup claim `running`，实际dispatch在scope cleanup后经原生`_run_prompt_submit(image_paths=[])`，不经新Loop或client join。新RPC先reserve、旧natural finalizer/consume此后不能再投同IDs。

唯一buffer表达：新增Web路径首次启用后，`agent._pending_steer`由原有字符串转为同owner occurrence buffer，legacy后续steer与new submit写同buffer；未启用时原string/Lock/返回/消费路径原样。legacy已合并字符串只作为一份既有buffer输入，不反推其原始occurrence。drain返回带owner/IDs的`str`子类batch；真正append时确认消费，失败requeue恢复相同IDs且旧先新后。finalizer最后drain同时关闭Web admission；lateWeb ACK不可能落在关闭后。异常/旧hard Stop/Session shutdown将已accepted未消费项标明确rejected；显式Interrupt的reserved batch由其operation继续拥有。

共享注册接线由Main负责：新 `tui_gateway/methods_pending.py::register(server)` 与新 `tui_gateway/contracts/pending.py` import；server.py既有方法注册与contracts registry不在本任务白名单。Main已完成正式注册，以下最终测试使用实际 `server.handle_request`，没有临时register或替代dispatcher。运行中的53445尚未重启，不把测试装配等同于该进程已加载。

## 1. 任务对应条款

本阶段实施冻结06 §0、§1.6–1.11、§2.1–2.4、§2.9、§3.2–3.4、§4.5–4.7中的Core correction与Atomic Interrupt。现行02适用身份、Message UID、不可变prefix、profile、原生未启用、Compaction current tip及接线验收约束。覆盖审计S01–S05/I01–I03；压缩只取消由另owner实施，不在本阶段修改。此报告是Development交回，**不代表独立Verification/Validation通过或本轮交付完成**。

## 2. 实际变更与白名单

| 文件 | 实际职责 |
|---|---|
| `agent/pending_steer.py` | 唯一occurrence owner、真实epoch、withdraw/claim/consume/requeue、有限Web回执、原生最终关闭与单次handoff；占用原 `_pending_steer`，没有RPC第二队列 |
| `agent/interrupt_control.py` | legacy/new同槽steer与drain；native hard-clear给新occurrence明确terminal，显式handoff reservation仍由operation拥有 |
| `agent/agent_runtime_helpers.py` | 仅两处steer helper旁路，真实post-tool append重新验证claim；被撤回批次不伪报Delivered；文件总行数相对产品基线减少2 |
| `agent/turn_iteration_prep.py` | 真实pre-API insertion重新验证claim，重锚当前驱动user，仅搜索其后的工具结果，禁止插入历史prefix；legacy分支保留旧搜索行为 |
| `agent/turn_context.py` | 仅真实 `_bind_turn_identity` 启动epoch；真实follow-up Turn起点确认此前已跨native准入 |
| `agent/turn_finalizer.py` | 原最后drain接缝关闭Web admission；失败把ACK项明确rejected，natural finish只保留一次owner handoff |
| `tui_gateway/methods_pending.py` | 五RPC、实际profile/runtime校验、锁内reserve与op去重、native Stop/settlement/一次准入、literal两事件发布 |
| `tui_gateway/prompt_turn.py` | 仅old finally保留running reservation，scope/marker cleanup完成后dispatch；owned `SteerBatch`不再落回普通queue字符串fallback |
| `tui_gateway/session_lifecycle.py` | 仅hard Stop/close清理，显式handoff私有kwarg保留原ordinary queue；默认Stop仍清其原队列并增generation |
| `tui_gateway/contracts/pending.py` | 新增独立DTO及五method/two event契约，不改旧契约字段 |
| 两个新test文件 | Agent owner边界10例；正式Gateway/AIAgent/SQLite路径20例 |

`agent/agent_init.py`最终无产品差异；不向既有超2000行文件增加行数。没有修改usage、compression、Secretary、前端、规格、根看板或共享registry；没有stage/commit、启动UI/后端、重启53445、真实模型请求或大型检查。

首次opt-in时现存legacy合并字符串只作为一项导入，不反推此前occurrence。另覆盖实际过渡竞态：旧字符串先drain、Web后启用owner、旧字符串再requeue时，旧批次导入同owner头部，不能覆盖新回执；其原始legacy ACK没有Web pending ID。

## 3. 正式调用路径与锁

**Pending：** Main正式server模块清单 → `methods_pending.register/bind_module` → `server.handle_request` → 原 `_session_turn_admission` → history lock → Agent原 `_pending_steer_lock` → 同槽owner。history/admission证明当前runtime记录与profile，不把browser `conversation_ref`当权限。RPC不持有平行string清单。start/build没有真实Turn owner时不接受；hosted/compute-host/Codex App Server明确4010 unsupported。

**Consumption：** 原native Loop pre-API/post-tool drain返回`SteerBatch(str)` → 真append处同buffer lock重新选择仍claimed且claim token相同的IDs → 普通`steer_user_row`/native Message UID → 一次append/insert和terminal consumed → 释放锁后发布exact IDs/UID。普通SessionDB flush仍负责落库；真实测试确认一行合并消息及receipt UID一致。batch字符串不是权限，withdraw后不再送旧冻结内容；requeue保同IDs与接受顺序。

**Natural finish：** finalizer在owner锁内关闭epoch并reserve剩余；lateWeb submit明确不接受。Gateway old finally在同history lock释放旧inflight并维持running reservation；旧marker/profile/notification scopes全部清理后才能claim一次dispatch。新方法状态在真实原生Turn起点或native `_run_prompt_submit`成功时标记`followup_accepted`；worker先于外层ACK结束也不会阻塞ordinary queue。

**Interrupt：** history→buffer锁内仅reserve未消费/未撤回IDs，op_id同epoch原子去重 → 释放全部owner/admission锁后调用真实 `_interrupt_session_turn(preserve_pending_handoff=True)` → Stop结束和old worker settlement两个条件汇合 → 同owner一次dispatch claim → `_run_prompt_submit(..., image_paths=[], queued_prompt_generation=原生当前generation)`。原生ownership、retirement、closing、generation、存储及Loop入口继续真实执行；只在true admission后确认consumed/accepted。Stop后来先赢native准入时明确rejected，不发第二Prompt；异常/close不会留下已ACK的无归属条目。

`_session_persist_lock`/DB native compression publication未改；handoff在旧线程彻底settle后读取agent真实current stored tip，rotation测试使用真实compression lease/fence/SQLite child publication。无持buffer/history锁等待provider/tool/线程。

## 4. 验证结果与反例关闭

证据全在 `.hermes-dev/round2-evidence/pending/`。使用官方PM `.venv` Python 3.14.7、canonical `scripts/run_tests.sh -j 1`，`--basetemp=仓库内证据目录`，真实SQLite、正式`AIAgent.run_conversation`及Gateway admission/lifecycle；只控制provider/summary返回与时序屏障，关闭无关host/UI副作用。fixture禁止socket connect/connect_ex；model metadata探测由受控外部返回替代；最终30例无网络连接。

| 范围 | 证据与结果 |
|---|---|
| 最终全部新增机制 | `final-owner-lock-tests.log`：10新Agent +20新Gateway +32旧steer，62 PASS；最后single-lock requeue检测/修改版本，真实RPC注册无临时装配；此前`final-owned-tests.log`新30 PASS |
| 受影响原生steer/queue回归 | `last-integrated.log`：32旧Agent steer +32旧busy queue +当时27新增，91 PASS |
| 其余原生Stop与queue持久 | `final-regression-first.log` 中三个旧文件：loop-stopped hook 4、background review cancellation 2、queued persistence 9，15 PASS；此记录的其他失败单列如下，不能称整条命令成功 |
| 并发同operation | `concurrent-operation.log`：1 PASS，同op两个RPC只有一次真实Stop与一次follow-up |
| 首次opt-in过渡 | `activation-race.log`：2 PASS，正式Loop与owner层证明旧requeue不覆盖新owner且旧先新后 |
| 最终精确健康ratchet | `owned-health-final.log` / `owned-health.json`：任务12文件0 blocking/0 advisory；使用未修改的官方Measurer/compare/apply_allows，按白名单筛选真实Git差异，未修改规则/阈值/scanner；两处BLE001用原有comment waiver说明可变native/provider异常要保留terminal receipt |
| 共享contracts | `final-regression-first.log`：生成一致性PASS；catalog仅失败既有`review.summary` orphan，由Main调查。新两事件已在真实gateway发布接缝literal `_emit`，不改scanner/不加dead emitter |
| 差异检查 | 本任务tracked产品文件 `git diff --check` PASS；未跟踪新文件由真实import/tests/health测量覆盖 |

有效结果为30个新机制+79个相关旧客户端用例，**109个不同用例**。未因共享usage变化重跑其测试；曾全工作区health看到usage文件7个F811，已交其owner，最终任务健康采用原ratchet白名单测量，不把其他人的进行时文件写成自己的通过。

| 审计反例 | 对应实际证据 |
|---|---|
| S01 identity不可恢复 | 同文重复、多行、不同op唯一ID，精确撤回；256 Web cap、64 interrupt cap无mutation、retry不占capacity |
| S02 ACK被当pending | 真实工具插入、真实UID/一行SQLite、已消费不能withdraw；snapshot不使用inflight corrections推测 |
| S03 finalizer lateACK | 真实finalizer关闭后屏障，lateACK rejected；natural/Interrupt只有一次handoff |
| S04 requeue反序 | claimed原IDs旧先新后；首次opt-in legacy drain/requeue正式Loop仍保序 |
| S05 ACK/记录窗口 | 真append前withdraw屏障与insert/withdraw winner；实际插入重新validate IDs；不依赖RPC offsets |
| I01 读后被消费再拼 | 真工具消费后第二provider屏障，Interrupt只选剩余ID，不重发已消费内容 |
| I02 Stop/finalizer/未知准入 | 显式与natural两种Stop先赢generation；op query unknown不猜成功；真实ownership refusal terminal；同op并发一Stop/一准入；关闭/异常无幽灵Prompt |
| I03 rotation/current tip | 真summary受控返回、native compression rotation+DB child；follow-up实际落在tip，receipt stored_session_id一致 |
| 未启用与混合 | Noting global-off且不用新RPC仍原string/原返回/无新steer事件；启用后legacy/new共享owner按实际顺序合并；ordinary queue不被清除或改为新调度器 |

保留首次失败日志：runner参数错误、空Buffer错误truthiness、测试夹具符号不匹配、metadata网络防护诊断；最终已针对原失败复验，不删除历史失败或据部分pytest通过掩盖teardown error。

## 5. 缺口与限制

- 本阶段没有实际DeepSeek、HTTP/WS浏览器、用户端渲染、移动视口或跨平台验收；不能把受控provider的Loop机制证明当作真实模型/用户验收。由后续集成和独立门禁执行。
- 当前目标为原生in-process，hosted/compute-host代理没有对应child bridge，明确unsupported；没有换运行配置或造parent pending事实。
- 回执仅进程内，重启/epoch超出8已结束保留窗返回unknown或原生runtime不存在；不引入持久表。当前Web提交最多256、Interrupt最多64；legacy无新增容量拒绝，继承原生无限输入边界，不以Web容量封锁旧客户端。
- shared catalog现有`review.summary`失败仍由Main解决；generated artifacts/registry属于Main版本，正式运行进程待其统一快照/restart。以上不是本任务的独立门禁通过。

## 6. 接口影响与原生不变边界

DTO保持已review里程碑，最终名五项及两事件如上。snapshot/status事件只是失效提示，网络ACK可能先停留stopping/dispatching；前端必须query，不将超时当follow-up成功，不重发普通Prompt。已withdrawn重复返回无text，避免覆盖新Composer编辑；consumed row UID可定位历史；handoff消费UID为null时只表达真实准入，不捏造已持久化link。

未启用新路径时原 `_pending_steer`仍string/None，legacy steer/redirect/Stop原返回与行为未改。新所有权才使用occurrence与更强prefix保护；不改旧inflight corrections DTO、model/provider、压缩publication、普通queue结构、历史权限或Secretary状态。

## 7. 建议后续动作与文件交接

Main集中review上述12产品/test文件及证据后，确认现有正式server模块注册与contracts import属于集成快照，并处理shared `review.summary`。前端按里程碑query/invalidations接线；统一重启53445后才进行真实REST/WS/DeepSeek旅程，随后两独立门禁。

**本报告完整交回后释放 `agent/turn_context.py`、`agent/turn_finalizer.py`、`tui_gateway/prompt_turn.py` 给Main/usage owner串行接线；T3a不再修改。** 其它任务文件也已停止施工；若Main review有范围内缺陷，按新授权修复，不能让旧证据覆盖后续差异。源码/测试哈希与准确基线见 `source-manifest.json`；Main可据此复用有效证据，不必为接收报告重复跑109用例。
