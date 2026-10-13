# U-R2-04 Instant Reminder 首源消息推送

2026-10-14，附件/原生源观察owner GPT-6.1 Sol / high。**Main已批准下述单Core接缝与冻结事件接口；后端机制与正式事件帧证据已完整交回，前端DOM与真实用户验收待集成。** 没有修改前端、用户53445/5173或运行库，没有外部模型调用、提交或派生。28个不同有效定向用例通过；冻结scoped检查通过，health 0阻断/0提示。本报告不自行关闭整轮缺陷或门禁。

## 1. 条款、现象与原生接缝

依据06 §0/§1.4/§2.1/§3.3/§4.5–4.7及用户R2-C78 U-R2-04；02 §1 L14–257、§3.11 L993–1033、§3.12 L1034–1090、§5.6 L1544–1714、最终不变量L2516–2560。身份、role=user/carrier/timestamp、正常准入/ACK和关闭行为均保持。核心事实来自原生持久行，不能根据Schedule/准入receipt/text猜新消息。

已核正式路径：

1. `tui_gateway/session_notifications.py::_secretary_deliver_claim` L272–300：同原admission锁确定idle→`admit_active_reminder`→running→`_run_prompt_submit`；busy转pending，不另起Turn。准入receipt只证明claim/route，不证明user行已提交。
2. `tui_gateway/prompt_turn.py::_run_prompt_submit` L1140后：在运行线程之前发空payload `message.start`；前端目前只设active，complete才读取真实history，因此Thinking可先于carrier可见。
3. `_invoke_agent` L778–821：将原生TrustedUserInput与persist_user_message交给同一`AIAgent.run_conversation`；仍未提交carrier。此处可安装一个本次执行期只读callback，并finally恢复先前值，沿现pending source observer的生命周期范式。
4. `agent/turn_context.py::build_turn_context` L1119起：真实_stage_turn_user_message产生role=user、原timestamp/UID，append到真实messages；随后`secretary.reminders.persist_active_before_compaction` L141触发现 `_persist_turn_start`（L1024–1041）。该提交点先执行native `_persist_session`，再 `require_active_delivery_persisted`，成功才可走turn-start compaction及首请求。
5. `agent/session_persistence.py::_db_flush_write` L317–337：原append_messages_batch事务将user行与active schedule settlement一起提交，之后同步原 `_row_id/message_uid`。`ActiveReminderAdmission.row_proof/durable`可证profile DB、physical session、UID、content、entry timestamp与settlement；未知COMMIT返回由require重新确认及恢复exact markers。事务rollback/claim失效在该点抛失败，不能发布源消息。

## 2. 批准机制、精确变更与源码版本

Main已亲审提案并批准 **`agent/turn_context.py::_persist_turn_start` 在现 `require_active_delivery_persisted` 成功返回后的一个只读callback调用**；该授权与§3接口冻结在本次派遣消息，不冒充用户逐字指定实现。未修改append、mark、ACK、claim、admission、run_conversation流程或配置。该函数是唯一正式观察点，不能把未持久的阶段消息当成功。

已新增可选执行期hook `_on_turn_user_persisted`，Core接缝共8行（L1041–1048）。给出现有`messages`及`agent._persist_user_message_idx`；若无callable则no-op。observer异常记录debug traceback后继续原生执行，不能阻断、回滚或让active persistence失败变绿。该hook只由Gateway `_invoke_agent`（L865–879）在**真实active_admission_witness(text)存在**时临时安装，finally恢复/移除；普通用户、Noting off/ineligible/无witness、伪造纯字符串wrapper路径不安装且行为原样。未修改`agent_init.py`或另建持久owner。

Gateway观察闭包只读：

- 按真实index选该user dict，复用现 `agent.pending_steer.native_source_message/native_source_boundary/native_source_suffix` 取得UID、已committed row_id与前驱事实；不按内容找行或扫完整history。
- 以`witness.row_proof`及同一agent._session_db为profile/session权威，明确校验实际DB路径等于witness所属路径（不能依赖witness.committed早返回而误信同UID的其它库）；用已有 `SessionDB.get_messages_around(proved_session_id, row_id, window=0)` 读取唯一真实row，核UID/role/content/entry timestamp及active事实；不新建identity，不查Schedule来重构carrier。
- 真实conversation_ref只取同admission witness的before.conversation_ref（或已证明等价的current agent ref），不因读操作mint/resolve新ref。
- 同本次_invoke closure最多发布一次该真实UID。observer失败不追加重试/补偿控制，不延迟Agent；无committed证明就不发，原生失败路径继续保留。
- 发布发生在持久化COMMIT及require校验之后、turn-start compaction/首请求/模型Thinking之前。之后可能重复调用_persist_turn_start，不重复发源。前后callback/source observer均finally归位，跨Turn不泄漏。

实际文件：`agent/turn_context.py`只上述函数；`tui_gateway/prompt_turn.py`新增L738 `_read_committed_user_source`、L765 `_committed_turn_source_observer`及invoke临时装卸；`tui_gateway/contracts/events.py` L209–231声明新模型/事件；官方generator更新两shared TS/OpenRPC生成物；新`tests/tui_gateway/test_instant_source_native.py`。`session_notifications.py`和所有Secretary持久/Reminder owner文件未改，原receipt保真透传已正确；旧message.start/complete/delta合同原样，没有新增service/API层/数据库/配置/环境变量。

未提交工作区HEAD `24510d1c7c3b8dfc95b6d0626be30f090561fa30`。精确SHA256在ignored `instant-source/source-manifest.json`：Core `fd80aaf74fed250929043c936a9e95ae379fe1d61d9d936191912bc4da7ad7c2`；prompt sibling `c1c6fbcc6c0086d87696608cba3de51a7073d48096a212b54791bdf9fd83740f`；events contract `c610a0f6d1c3c266abec29c5f5a6786976d9b135ba8bcb3910d8497fc8b737b0`。两生成物包括此前已批准附件新名的累积内容，未覆盖其成果。所有其他owner/user修改保留。

## 3. 已冻结新事件接口与正式路径

事件新名 **`message.source_committed`**。旧 `message.start`/complete/delta合同与发送时序原样保留。该新事件当前仅用于已正式准入、已原子持久的Instant driving user carrier，不扩成任意Schedule通知。

```text
payload:
  turn_id: string                   // 当前真实native Turn身份
  stored_session_id: string         // 此已提交行的真实physical Session
  conversation_ref: string          // 同active admission已证明的opaque Ref
  message:
    message_uid: string             // 真实durable UID，必填
    row_id: integer                 // 同profile DB内已提交正整数地址
    role: "user"
    content: string                 // 真实DB row完整carrier，不从schedule生成
    timestamp: number              // 原row entry timestamp，仅机器传输；UI沿原时间呈现
    display_kind?: string|null      // 若真实row有才带，不能新mint秘书kind
    display_metadata?: JsonValue|null // 若真实row有才带
  source_messages: NativeSourceMessage[] // 复用原只读source address列表
  source_boundary: NativeSourceBoundary // prefix/after UID/compression/committed事实
```

`source_messages/source_boundary`复用现契约，不伪造prefix_unchanged等true；当前source只含新driving row时all_rows_committed按实际计算。必要role/content/timestamp是规范化**真实存储结果**，不是第二份authoritative transcript。最大范围仅该首user carrier，不灌root/tools、API sidecar、历史prefix、图片bytes或凭据。

前端契约建议：同当前runtime/Conversation绑定接收；事件外层session_id仍为runtime路由，stored_session_id只是已提交行当时的physical locator，不能拿它与旧压缩根route直接比较而丢弃合法续接。通过(conversation_ref,message_uid)将真实行一次并入现source/history owner，按source boundary真实前驱接入，然后消费后续Thinking/stream；最终complete/REST同UID原位合并，不能在末尾再重复。Unknown predecessor或compression变更按原source reconciliation/refetch，不依epoch、内容或时间重排补偿。新事件正文按现Reminder classifier呈现Instant卡，保持role=user；不作为乐观bubble，不另建持久历史。

## 4. 冷恢复与初persist前后可见性

- 先前history可能由out-of-band/cold恢复改变；事件边界须从该次_invoke实际st.history及messages提取，不能用准入前旧history计数。row_proof指向实际恢复后的physical Session/UID，profile DB不随ambient路径变化。
- 初persist前无事件，包括message.start已出但active事务尚未成功阶段；claim被取消/lease回收/本地关闭/写失败/rollback不能产生ghost source。
- COMMIT成功但return丢失仍经现require恢复exact row markers，之后可发一次真实源；不能因异常返回错误而猜未提交。
- 正常COMMIT后的source事件早于首provider调用与Thinking。若后续压缩旋转，UID/ref继续稳定，event的physical address仅是当时已提交事实；最终原source/compression流程负责连续性。
- frontend reload/reconnect依原REST/replay与真实UID重建，不把此event视作新的持久cache或业务数据库。

## 5. 验证结果、命令次数、耗时与真实证据

使用canonical runner和隔离profile/SessionDB、真实AIAgent Loop/active schedule registry/原生事务。只控制provider返回或持久化时序，不替换待验证commit/witness/source机制。

28个不同有效用例为：新native source21（`native-third.log`18＋正式frame1＋`conversation-boundary.log`1＋地址反证1）＋原active persistence5＋原Pending/source1＋生成一致性1。**不存在单条28或21全包通过命令**；是按新增断言与最终地址核验逐次定向补证的有效并集，重复运行不相加。旧附件59项没有重跑。本轮没有大型检查、模型调用或浏览器操作。最后review补充实际返回row.id必须与proof选中row_id一致（不能因删除竞态读到另一个同UID副本而发布地址不一致的source）；只有精确地址反证与正式帧正例受影响并定向复测，其余机制不变。

正式事件帧证据 `native-event-frame-proof.json` 使用原 `_emit → _event_frame/check_payload → write_json/_stamp_event → session transport` 及正式 `session.events.since`，不只是替换_emit记录payload：source seq=3、真实Thinking seq=4、complete尚无，replay首两条同序。原生首源UID、row_id、turn_id及前驱UID的精确实测值在该JSON中；message与SQLite原行逐字段一致、无第二份消息写入。transport本身为内存接收端，provider返回受控，不能把此证据写成真实网络/模型/DOM验收。

全部日志在 `.hermes-dev/round2-verification/instant-source/`；下表命令前缀 `T = HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh`。耗时均外层wall，另列runner实际测试wall。未装依赖或改PM/lock。

| 精确执行 | 命令次数 / 耗时 / 结果 | 原始日志 |
|---|---|---|
| `.venv/bin/python scripts/gen_gateway_contracts.py` | 1次，0.43s，两生成物更新；随后generated-current通过 | generator工具结果／native-regression |
| `T tests/tui_gateway/test_instant_source_native.py -q` 第1版 | 1次，12.57s（runner11.4s），9pass/1fail。源顺序/事务已通过，失败为把fixture从off→on前的固定root当成不可变；按原global开关规则只核本次实际native root，不改生产root机制 | `native-first.log` |
| 同命令第2版（增加边界） | 1次，19.50s（runner18.3s），16pass/1fail。冷恢复源顺序/身份已通过，失败为比较旧fixture root与不同constructor合法native重建root；改为比较原prepare_resumed_parent_context实际接受后的root，未更改冷恢复流程 | `native-second.log` |
| 同命令第3版（含真实旋转） | 1次，10.11s（runner8.9s），18pass，无fail；此前失败按runner默认内部重试政策保留，不把重试当新distinct | `native-third.log` |
| `T tests/secretary/test_active_reminder_persistence.py tests/tui_gateway/test_pending_native_turn.py tests/tui_gateway/contracts/test_generated.py -k 'generated_files_are_current or failed_native_write_stops_only_active or transaction_rollback_and_unknown_commit or plain_json_carrier or old_carrier_cannot or rpc_consume_withdraw' -q` | 1次，4.22s（runner3.2s），7pass；必要原生失败/普通持久/旧Pending与source合同子集，不是这些文件全包 | `native-regression.log` |
| `T tests/tui_gateway/test_instant_source_native.py -k native_event_frame -q` | 初加正式帧1次3.85s（2.2s）1pass；追加实际JSON证据输出后定向1次3.22s（2.1s）1pass；不重复20小包 | `event-frame.log`、`event-frame-proof.log` |
| `T tests/tui_gateway/test_instant_source_native.py -k copied_uid_in_different_conversation -q` | 最后补唯一Conversation边界1次，2.65s（1.6s），1pass | `conversation-boundary.log` |
| `T tests/tui_gateway/test_instant_source_native.py -k 'native_event_frame or changed_row_address' -q` | 最后地址核验薄修与反证补充后1次，4.69s（3.5s），2pass；正式帧正例更新JSON，错误物理地址拒绝source但原native Turn/settlement正常 | `address-proof.log` |
| `.venv/bin/python …/instant-source/scoped_checks.py`，实际官方`.venv/bin/python scripts/check --staged --base 24510d1c7c3b8dfc95b6d0626be30f090561fa30 --only ruff,health,os-marker-fakes` | 初次4.455s以旧附件tree作base，被官方base必须commit类型要求拒绝，未测health；修正为HEAD后4.928s三检查pass；测试证据输出新增后4.403s同scope pass；Conversation边界补充后4.304s pass；最后地址核验后5.523s pass，health0阻断/0提示。没有修改规则/阈值/等级/豁免 | `scoped-checks-first/second/third/fourth.{log,json}`、最终`scoped-checks.{log,json}` |
| `git diff --check -- <本owner源码/测试/生成物/报告>` | 最终通过；不纳入其他owner文件 | 交接前执行 |

scoped检查使用私有Git index，仅本项6文件；没有操作共享index或创建commit。最终诊断源tree `0d1b2bbffe3bfdbedd1991c562ab4bd0d09c2d0a` 是scoped检查材料（生成物累积附件增量），不冒称完整集成产品快照。源码hash/执行范围/证据入口见source-manifest。两次失败日志继续保留；没有以修改生产cache/root/规则让断言变绿。

实际范围逐项结果：

1. **通过**：正式_secretary_deliver_claim→_run_prompt_submit→真实Loop→COMMIT→新事件→原生Thinking→provider→complete；provider屏障前已存在完整原行，事件恰好一次，UID/ref/role/body/timestamp/order一致，不等complete，旧start无payload。
2. **通过**：真实cold Parent prepare/attach及真实native压缩DB旋转（仅summary provider受控）、after UID/physical地址/稳定ref；same UID复制至另Conversation的真实AIAgent被原admission拒绝，same UID/row_id复制到不同profile的真实DB不能满足witness路径。helper读取不mint身份、不重排。
3. **通过**：rollback/claim失效/local off/lease回收/write失败事件0且provider0，原registry仍pending/可重试；unknownCOMMIT按原require恢复exact marker后一次source，无重复user行，发生过的schedule settlement不被回滚或再claim。
4. **通过**：observer读异常/发事件异常只traceback，真实provider与完成照常、原settlement保持；先前callback finally恢复或移除，第二次persist不重复，普通Turn不安装新observer。
5. **通过**：ordinary/关闭Noting/辅助runtime/伪造纯字符串carrier/busy→passive/closing均不安装新observer或发新source；busy原pending仅一项且原running保持，closing无user ghost，不改关闭行为。
6. **通过**：generated-current与旧失败/普通写入/Pending	source回归子集；冻结ruff/health/OS marker0/0，适用code健康标准未放宽。

## 6. 当前未覆盖、接口影响与授权依赖

后端已实施且§3接口已冻结；正式Loop/SQLite/原事件帧/replay具备开发证据。**前端没有改，实际源事件→Controller/source owner→assistant-ui Timeline DOM尚待其owner/Main集成验证**；本包没有真实网络/模型/内置浏览器或独立门禁证据，不能自行关闭U-R2-04整体。

保持原生best-effort事件传输/replay策略：掉线/observer失败可能该次未呈现，真实历史仍按原REST/replay恢复；没有新增可靠事件ACK或重试协议。尚未实测真实浏览器断网/跨进程重启/其它平台，此观察不承诺跨崩溃exactly-once。原Message/Reminder持久与ACK机制的已有证据复用，未改变其语义。

## 7. 后续交接

Main亲审6文件与实际上下游/源证明/旧契约，前端owner按§3冻结接口接线。不得以复跑有效28例代替review；仅集成改变source/read/时序或证据存疑时定向补测。前端应在同(runtime,Conversation owner)接收真实row，按(conversation_ref,message_uid)和原source boundary并入现source owner，Thinking前呈现；complete/REST同UID原位接收、无双份，role仍user，使用现Instant classifier，不重造乐观消息或schedule投影。

必要联调：隔离正式服务的真实Instant触发→new source frame→Thinking→complete，记录时间/seq及首DOM卡片位置，刷新同UID单份；另核冷恢复/压缩locator与快速切会话不串、网络恢复可重放。是否需要新真实模型由Main按范围决定，不在用户5173/53445先行操作。全轮仍须新独立Verification及Validation；用户服务统一更新归Main，先确认接口集成和无活动工作窗口。
