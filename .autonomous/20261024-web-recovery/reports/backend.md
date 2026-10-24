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

已准备 ignored `backend/seed_validation.py`：真实SessionDB种1200行，无模型调用，owner=`default`、stored id=`recovery-validation`。终端cwd在仓库外 `/private/var/tmp/hermes-web-recovery-validation-workspace`；Noting／Scheduler关闭。命令语法已用Dashboard `--help`确认，seed已实际生成；下列常驻服务尚未由本包启动，原53445／53446已有其它长驻Python进程，必须保留；本轮使用已确认空闲的53575／53576，Vite保持5178，启动前仍核占用。

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

仅自建隐藏IAB打开 `http://127.0.0.1:5178/chat/recovery-validation?profile=default`；不发送prompt。Dashboard仍是真实正式认证／Gateway／SQLite，代理只为受控网络故障。脚本已编译检查；其常驻转发尚未实际端到端跑通，不冒称UI已验。

断线期间从主仓另一终端运行 `seed_validation.py append|replace|edit|rewind|compress|delete`，这些全部调用正式writer（要保持深历史样本先用append；replace会按明确命令替换隔离库内容）。`fault_proxy.py`读取同目录 `faults.json`：`{"block_ws":true}`关闭已连WS并拒新连接；写回false后允许正常重连，同Dashboard保持同epoch。`{"delay_seconds":8,"delay_paths":["/api/sessions/"]}`只延迟匹配GET再转发真实后端，WS继续工作；空对象解除。`proxy-requests.jsonl`只记方法和路径，不记认证header／正文。新epoch用停掉并重启自己启动的Dashboard（同隔离home），不能伪造epoch。也可对自有Dashboard PID使用SIGSTOP／SIGCONT控制整段网络不可用；恢复后逐轮核真实请求。

受控边界：seed只提供真实持久空闲会话；活动Turn／租约／ring竞态以本包真实native/replay/SQLite机制测试证据为准。代理不伪造runtime、响应或成功ready。没有安装依赖、绕过认证、修改生产配置或启动可见页面。

主会话环境补记：53445／53446为其他长驻进程，保留不动；53575／53576和Vite5178已由主会话启动并核health200／入口200。需`--isolated`绕开主机服务附着；`--skip-build`＋现有Web dist仅提供正式bootstrap，实际测试前端由Vite提供。无真实模型／生产数据操作。
