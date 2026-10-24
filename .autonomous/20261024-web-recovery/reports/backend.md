# 后端 B1／B2／B3 整包交回

## 对应要求与结论

依据冻结 `ba83d2b430e3448461dd7feb9f1acd8fc94c6cc9` 的06 §1.4.1 R2、R3、R4、R9及相关R10。本包已实现正式REST范围读取、原子replay cut、activate v1封套和正式历史writer失效唤醒，交主会话亲审。未提交、push、部署、启动可见UI、调用外部模型或派生子Agent。根文档／规格／计划及其它dirty未由本包修改。

## 实际变更及正式入口

- **B1：** 新 `hermes_state_recovery_view.py`；`hermes_cli/web_routers/sessions.py` 为既有 `/api/sessions/{id}/messages` 增可选 `recovery_view=1`。同一conn显式BEGIN解析真实Profile、compression tip／spine、排除branch／delegate、UID退役与逻辑代表；SQLite只做全范围身份／顺序计算，Python只取得窗口payload。默认latest200、上限500，任意可展示UID／row anchor；coverage有首尾、邻居、逻辑坐标和cards SHA256。详情≤12行，另有digest。投影及既有验证型图片引用在读事务／history锁外，未能验证时保留原多模态内容；不为GET补索引／身份，不把正文强制降成图片占位。旧无新参数GET的分页／响应不变，参数冲突400、未知owner／anchor404。
- **B2：** `event_replay.read_replay_cut` 同锁复制events字节及latest_seq／truncated／epoch，解码在锁外；`session.events.since` 正式调用该helper，原字段／seq／epoch／ring上限保持；open_requests仍为原生独立request snapshot。
- **B3：** 新 `tui_gateway/recovery_view.py`，`session.activate` 薄接线；resume／activate及LiveSessionSnapshot宣告可选 `recovery_view_version:1`。有界history lock 250ms；既有attach后D0短事务→完整native snapshot S→D1短事务，锁不嵌套DB／replay，不持全局resume锁做范围读。D1额外重读D0固定区间，比较展示digest、身份／顺序、lineage／rewind和展开详情；append允许有限B后缀，超出窗口连续性报coverage_gap；服务端最多重做一次。只返回matched或完整替换窗口，不发补丁／不省网络正文。最新窗口为封套必需，暖恢复再加anchor，默认最多两窗口。
- **当前Turn／旧快照：** 当前活动输出必须同时有完整native snapshot、真实durable source UID、当前Turn ID与实际租约holder依据。外部owner接管／缺snapshot不假idle。工具按真实occurrence UID精确核对（不是字符串子串）。已持久输出用D1代表，已退役UID不复活；稳定改写发生在D0之前也覆盖：正式source_committed证明的来源已删除／退役则丢弃该旧Turn尾巴；idle未知输出没有来源证明时报runtime_unavailable；异常结束由真实持久terminal sidecar接管。不用inflight.assistant纯文字冒充完整性。成功外层仍携原有inflight／queued／open_requests／pending等可用字段。
- **变更通知：** 经主会话明确扩白名单，新增小型 `hermes_state_history_notifications.py`，仅在 `replace_messages`／`secretary_set_user_content` 真正成功改写后best-effort写真实db_path旁的轻量通知文件；`change_watcher`仅stat该文件并复用sessions.changed。它不是revision、coverage证明或客户端新通道，不含正文，不猜启动Profile；无变化不写、通知失败不影响writer。watcher同时补rewind_count签名。
- **DTO：** `contracts/sessions.py`只加可选字段，两个 `apps/shared/src/gateway-contract.*` 通过既有生成器同步。详细字段、失败语义与真实输出见 `reports/backend-contract.md` 和 `tests/tui_gateway/fixtures/recovery-view-v1.json`。

正式writer→失效入口：rewind_to_message／rewind_user_turn→sessions.rewind_count→watcher；prompt.submit edit／regenerate→既有session.info，底层replace同时补通知；set_user_message_content→secretary_set_user_content→新增通知→watcher；delete_session／session.delete／REST删除→sessions行集合变化→watcher；archive_and_compact及compression rotation→计数／lineage变化，既有session.info／Framework／complete及watcher。未将直接SQL视为实时支持接口，未扫全库正文。

## 验证证据及边界

统一使用项目 `.venv` 与 `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh`。没有裸pytest／真实模型／外网。

| 范围 | 结果与日志 |
|---|---|
| 最新新REST＋封套机制 | `recovery-final.log`：2文件32项通过（REST8、RPC24）。最终补原有inflight／queued后再跑 `activate-final.log`：24项通过。日志均在 `.hermes-dev/web-recovery-20261024/backend/` |
| B2与既有相关回归 | `targeted-tests.log`：replay17、watcher2、history_cards46、session_timeline6、inflight_output14通过；本包通知4通过；生成文件精确一致1通过。日志内早期新REST／RPC17项被最新32项覆盖，不重复累计 |
| 生成文件独立确认 | `generated-contracts.log`：精确生成一致1项通过 |
| 既有catalog缺口 | 仅 `test_catalog_covers_the_whole_wire` 报孤立旧review.summary；已将完整冻结Git树解包到ignored `backend/frozen-tree/`，从该树工作目录用正式runner隔离复现同一失败，证据 `frozen-catalog.log`。不是只凭rg判断；未删旧契约／改门禁 |
| 健康与ruff | `health-ruff-final.log`：冻结ba83d2基线，15文件0 blocking／0 advisory，两检查通过；超标facade methods_session净减，server只改原行不增行数；新模块／函数满足阈值。相关diff无空白错误 |
| 范围／锁／耗时 | 1400行深anchor只转换5行payload，最新只转换200；1102行的深anchor＋tail＋详情独立有界。真实1200行只读库一次latest200＋anchor5：DB范围读36.8ms，投影117.6ms（一次本机样本，不作SLA）；见 `read-timing.json`。另用真实锁／conn断言证明投影时history／DB事务／replay／全局resume锁都未持有 |

竞态证据包括：单conn BEGIN期间第二连接append仍保持旧快照；D0/S/D1之间独立进程正式replace／rewind／compression／delete；普通append、持续native delta有限切点（不等Turn结束）、snapshot后ring缺口重建、epoch变化拒绝跨cut、实际lease交接、深anchor与tail非邻接、旧接口兼容、UID及physical alias退役、工具call已持久但result未落库仍保live occurrence、结果落库后不重复、稳定idle旧snapshot改写不复活、真实异常terminal writer对账、通知跨进程同数改写／编辑和同ID不同Profile／失败不阻断。

未做：生产／实际WebView／Android验证、真实模型、全量无关测试；这些不由后端单测代签。新前端／APK集成与独立门禁待主会话。通知文件只补两类既有writer缺口，不泛化其它无关原生writer。极端持续破坏性变化／ring始终不足／缺正式relay依据仍可明确失败，前端须按契约退避。

## 接口影响与后续动作

约定契约里程碑已交主会话和frontend；真实fixture由正式FastAPI route＋session.activate handler＋真实SQLite生成，脚本和原始库仅ignored。封套失败 `complete:false` 的reason还包括 `read_failed`（SQLite读失败），不把外层状态当ready。成功封套／外层可增带原生inflight／queued；接线可继续沿原字段消费。前端每次封套至少带latest receipt，深anchor另带一个；不以旧缓存receipt替代本轮REST。

建议主会话先亲审D0/S/D1与idle旧snapshot处理、实际前后端字段及failure分支，再统一集成验证；两个独立门禁复用本报告同版本证据。既有review.summary catalog缺口按主会话范围决定处理，不计为本包新回归，也不宣称全仓全绿。

## 供隐藏IAB的真实隔离环境

已准备 ignored `backend/seed_validation.py`：真实SessionDB种1200行，无模型调用，owner=`default`、stored id=`recovery-validation`。终端cwd在仓库外 `/private/var/tmp/hermes-web-recovery-validation-workspace`；Noting／Scheduler关闭。命令语法已用Dashboard `--help`确认，seed已实际生成；三项常驻服务已由主会话启动，REV-10期间仅重启本轮53575加载修补。原53445／53446已有其它长驻Python进程，必须保留；本轮使用53575／53576，Vite保持5178。以下是重新启动入口，运行前先核占用，不重复启动现有进程。

```bash
cd /Users/edgar/code/hermes-secretary
.venv/bin/python .hermes-dev/web-recovery-20261024/backend/seed_validation.py seed
HERMES_HOME="$PWD/.hermes-dev/web-recovery-20261024/backend/validation-home" HERMES_WEB_DIST=/Users/edgar/code/hermes-secretary-web/dist .venv/bin/python -m hermes_cli.main dashboard --host 127.0.0.1 --port 53575 --isolated --skip-build --no-open
# 第二个自有后台终端：仅代理真实HTTP／WS，不合成协议数据
.venv/bin/python .hermes-dev/web-recovery-20261024/backend/fault_proxy.py --port 53576 --upstream http://127.0.0.1:53575
# 前端仓：Vite保留现有原生bootstrap token注入
cd /Users/edgar/code/hermes-secretary-web
HERMES_BACKEND_URL=http://127.0.0.1:53576 npm run dev -- --host 127.0.0.1 --port 5178
```

仅自建隐藏IAB打开 `http://127.0.0.1:5178/chat/recovery-validation?profile=default`。这是原有1200行空闲场景；活动场景使用下文的明确合成输入及本地provider。Dashboard仍是真实正式认证／Gateway／SQLite，代理只为受控网络故障。本包没有操作UI，不冒称UI已验。

断线期间从主仓另一终端运行 `seed_validation.py append|replace|edit|rewind|compress|delete`，这些全部调用正式writer（要保持深历史样本先用append；replace会按明确命令替换隔离库内容）。`fault_proxy.py`读取同目录 `faults.json`：`{"block_ws":true}`关闭已连WS并拒新连接；写回false后允许正常重连，同Dashboard保持同epoch。`{"delay_seconds":8,"delay_paths":["/api/sessions/"]}`只延迟匹配GET再转发真实后端，WS继续工作；空对象解除。`proxy-requests.jsonl`只记方法和路径，不记认证header／正文。新epoch用停掉并重启自己启动的Dashboard（同隔离home），不能伪造epoch。也可对自有Dashboard PID使用SIGSTOP／SIGCONT控制整段网络不可用；恢复后逐轮核真实请求。

受控边界：seed提供真实持久空闲会话；活动Turn另有下文的本地SSE正式native证据。代理不伪造runtime、响应或成功ready。没有安装依赖、绕过认证、修改生产配置或启动可见页面。

主会话环境补记：53445／53446为其他长驻进程，保留不动；53575／53576和Vite5178已由主会话启动并核health200／入口200。需`--isolated`绕开主机服务附着；`--skip-build`＋现有Web dist仅提供正式bootstrap，实际测试前端由Vite提供。无真实模型／生产数据操作。

## REV-10：普通Web活动Turn起点与本地SSE环境（2026-10-24补交）

**条款／根因。** 对应06 R3第5–7项及C04，未改冻结规格。首次实际Dashboard→Gateway→native Turn→loopback SSE已经产生delta及真实落库，但活动activate返回`runtime_unavailable`：恢复只认Reminder专属`message.source_committed`，普通Web的正式durable来源保存在当前`inflight_turn._terminal_source`。原失败及原版本SHA保存在ignored `backend/rev10-before/`，新增普通Web回归先在旧实现失败（`regression.log`），没有覆盖失败证据。

**实际变更／正式路径。** 产品只改`tui_gateway/recovery_view.py`，测试只改对应`test_recovery_view.py`。在原history lock和D0／S／D1捕获区间取得当前agent／inflight对象、原生terminal token、current turn id及actual lease holder，前后核对同一归属；从正式observer写入的`_terminal_source`仅复制db_path／stored session／row_id／UID标量，不读取缓存正文作为证据。真实db_path必须与当前Profile DB相同，来源stored session须在lineage；把来源纳D1有界identities查询，核physical row_id＋UID＋user role＋active／visible。当前runtime holder须精确等于D1租约holder并匹配当前Turn。Reminder原`source_committed`路径继续保留；没有伪造事件，未放宽idle未知输出、退役来源、rewind或外部owner拒绝。没有wire DTO变化、schema或writer改动。

**验证与版本。** 测试与真实探测的产品源基于HEAD`574a7b7fa333ae1baa8880de477df86916c49443`及本次未提交差异；`recovery_view.py` SHA256=`b4ba02cb78965bc87ab558636009dc6b4e4280fa1706df01dfff073ce8397d5b`。完整实际源／测试／harness及阅读文件manifest见ignored `backend/rev10-source-manifest.json`。已复读executing-plans全文、autonomous-run阅读与消息交接契约、本轮index／baseline／plan及冻结06 R3；按根AGENTS／CLAUDE与README入口恢复上下文，未采用动态报告替代原始判据。

| 证据 | 实际结果 |
|---|---|
| `rev10-final-tests.log` | 正式activate＋真实SQLite39项通过；普通Web无Reminder事件成功，缓存message正文不作证明，实际另一Profile同locator的source DB拒绝，错误row／UID／role／lineage拒绝，正式replace／rewind／compression退役拒绝，token／Turn／holder变化或缺失拒绝；原Reminder、idle旧输出、epoch／ring等既有覆盖保留 |
| `rev10-native-regression.log` | 原生inflight output14＋terminal persistence21，共35项通过 |
| `rev10-health-final.log` | health／ruff通过，2文件0 blocking／0 advisory；相关diff空白检查通过 |
| `rev10-native-stream-probe.json`／同名log | 正式`session.create→prompt.submit_idle→本地SSE→关闭WS→继续同一Turn→resume→REST→activate`：同runtime`1abebeb4`，stored`20261024_164714_25020f`，真实lease存在，活动封套complete／running均true，snapshot_seq／B均12；快照＋后续native delta拼出的全部文本与最终唯一assistant行完全一致。fake仅1次请求、6个SSE文本chunk，3.113秒完成；Gateway将其合并为4个message.delta，未以SSE chunk数冒充原生帧数 |
| `rev10-settled-proof.json` | 流结束后只读resume／真实REST／activate再次确认complete=true、running=false、REST唯一assistant卡、未持久输出事件0；未发送第二条prompt |

探测准备曾误用缺失PyYAML导入，shell继续后本地API以已消费run_id返回429、未接受SSE；该准备失败另存`rev10-before/preparation-failure.json`与Dashboard日志。随后改用既有配置reader，显式arm新run_id，才执行上述一次实际成功SSE。没有安装依赖、真实供应商请求、UI操作或生产修改。单测首次rewind反例返回runtime_unavailable而非view_changed，因为正式rewind也撤销真实lease；断言现准确接受两种明确拒绝。

**活动场景启动／控制。** 全部harness位于主仓ignored `.hermes-dev/web-recovery-20261024/backend/`。现有Dashboard53575为PID7423（`rev10-dashboard.pid`），仅此进程按已授权步骤从旧PID71427重启；proxy53576／Vite5178保持原进程。fake API53577为PID228（`local-stream-api.pid`），启动前已确认该端口空闲。保留原1200行`default/recovery-validation`、`recovery-other`同ID两行及Files材料；活动样本是另建会话，没有重写这些材料。

隔离default Profile经正式`atomic_config_write`配置named custom provider `custom:recovery-local`、model `recovery-fixture`、`http://127.0.0.1:53577/v1`及明确fixture占位key。原config备份为`validation-home/config.before-local-stream.yaml`，路由receipt为`local-route-receipt.json`；fallback为空、所有aux路由显式指向同loopback、title generation／Noting／Scheduler关闭，native run预算60秒／一轮／API最多一次。原生lazy runtime构造、模型路由、lease、output relay、持久化均未monkeypatch；fake只替代外部Chat Completions响应，未替代WS协议。

以下命令从主仓执行；服务器已运行，无须重复启动：

```bash
# 仅当自有53577已停止且端口空闲时启动；只绑定127.0.0.1
.venv/bin/python .hermes-dev/web-recovery-20261024/backend/local_stream_api.py
# 每次明确新run-id只准一次Turn；当前已arm validation-web-20261024-1
.venv/bin/python .hermes-dev/web-recovery-20261024/backend/stream_control.py arm --run-id validation-web-20261024-2 --pause-after 2 --interval 1
.venv/bin/python .hermes-dev/web-recovery-20261024/backend/stream_control.py status
.venv/bin/python .hermes-dev/web-recovery-20261024/backend/stream_control.py resume
# 允许前3个chunk，随后暂停；暂停设置不会撤销已在发送中的一个chunk
.venv/bin/python .hermes-dev/web-recovery-20261024/backend/stream_control.py pause --after 3
```

独立Validation从真实Web New Chat选择**default**，使用`recovery-fixture`／`custom:recovery-local`，输入`RECOVERY_LOCAL_FIXTURE: Produce only the controlled local stream.`。fake要求该合成标记、指定模型、stream=true与fixture key，否则拒绝；只接收内存中的隔离合成上下文，不记录请求正文／header。开始后60秒硬截止（暂停也计时），及时执行断WS／resume控制；用上文真实proxy的`block_ws`做断线、`resume`允许同请求继续，然后解除block_ws重连。正文仅六小段固定合成文本和合成Usage，不调用工具；控制脚本原子替换控制文件。`status_is_current_run`区分上一轮收据，不能把旧complete认作新请求。不要在`recovery-other`发送模型输入，其用途仍为只读Profile隔离场景。

停止方式：fake空闲时核`local-stream-api.pid`和53577仍对应本轮`local_stream_api.py`后，仅TERM该PID；如有活动流先走正式取消或等待60秒自然结束，再停fake。Dashboard同样仅核本轮53575 PID后TERM，重启沿上文同一隔离命令；proxy／Vite分别结束自己的终端。不得使用全局stop或触碰53445／53446。恢复原隔离配置可用现有正式配置writer读取上述备份后写回，但不能在本轮活动探测中途撤路由。

**缺口／后续。** 本次真实结果证明正式native活动恢复与最终持久投影收敛，不证明实际模型效果或Web呈现；没有真实供应商／实际APK／任何UI验收。Web隐藏IAB仍由独立Validation执行，C17只豁免实际APK。产品／测试差异与本报告交主会话亲审、集成及新候选独立复审；本子Agent未提交／push／部署，未改根文档、规格、计划或他人文件。
