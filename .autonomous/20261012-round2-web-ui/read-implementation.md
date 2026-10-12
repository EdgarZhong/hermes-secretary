# T3b/T4a 接口里程碑与实施报告

基线 `37ad76f5dfac02d4774d5e0faea55911b5fb8de9`；工作区增量未提交。冻结依据：06 §0、§1.14–1.15、§2.5–2.9、§3、§4.5–4.7；02 身份、Notebook/Memo、Idle、Noting真实owner、原生压缩与关闭不变量。本报告是Development交回，不是独立门禁。

## 精确接口里程碑

四个新方法的Python单一契约在 `tui_gateway/contracts/web_read.py`，注册函数为 `tui_gateway/methods_web_read.register(server)`。Main统一把contracts模块导入catalog、把methods模块加入server module list，再生成既有共享TS/OpenRPC产物；本Agent不改共享入口。

- `session.compaction_state({session_id})`：runtime id，可选profile（显式提供时与runtime所属home核对，不一致4001），经既有 `_sess_nowait` 绑定owner。结果 `{active,operation_id:string|null,phase:idle|computing|committing|committed|cancelled|finished|unknown,cancelable,state:idle|running|completed|cancelled|no_change|error|unknown}`。phase来自真实registration/fence，非status文案。worker尚未退出但cancel获胜时active仍true、phase cancelled；终结后active false。operation为每次原生facade attempt的opaque随机ID，timeout retry归属同一次operation，最多保留32条终态（仅内存）。
- `session.compaction_cancel({session_id,operation_id})`：`{operation_id,outcome:cancelled|too_late|no_active|already_finished}`。fence `try_cancel_before_commit` 非阻塞；cancel获胜即该operation不再发布，包括后续fallback fence。commit先获胜或fence锁忙则too_late；取消不设置Turn interrupt、不动pending/普通queue、不回滚合法Notebook Snapshot。未知／过期operation no_active；保留终态已结束为already_finished。
- `secretary.state({stored_session_id,profile})`：profile必填，可显式空串表示原生launch；非空沿用native profile名称，stored id必填；无需create/resume/attach。结果 `{stored_session_id,profile,profile_home:absoluteOwnerPath,conversation_ref:string|null,availability:available|unavailable,global_enabled:boolean|null,local_enabled:boolean|null,task_state:active|idle|unknown,tasks:[{task_id}],next_idle:{state:scheduled|absent|unknown,at:timezoneReadable|null},observed_at:timezoneReadable,memo_count,memo_entries:[{index,content}]}`。所有Memo entries均当前effective有序；一级UI只显示count、二级显示entries。live tasks必须同时匹配真实active registry的child DB绝对路径和父ref；DB running孤儿为unknown。scheduled仅真实timer registry存在、period一致、owner存在、不在Main Turn、deadline未过；非有效participation absent，缺真实deadline owner unknown。
- `secretary.notebook_read({stored_session_id,profile})`：`{stored_session_id,profile,profile_home:absoluteOwnerPath,availability,exists,output,created_at:timezoneReadable|null}`。只读resolver `read_only=True` + currentpointer + existing renderer，无ensure/reselect/persist_feedback；无Snapshot是原生明确文本。没有完整已存identity bindings时unavailable，不mint。global off/unknown返回4030；local off仍可读。

错误：参数额外键/shape由现有contract dispatch给4000；未知stored session 4001；不存在profile沿用4064；DB/身份冲突/不完整快照等fail-closed 5010（不回退profile）；global Notebook read关4030。当前in-process target全部使用真实owner；compute-host压缩暂显式4010，不能以parent代理冒称child状态，保留桥接接缝待Main协调。

事件：`secretary.changed` payload `{profile_home:absolutePath,conversation_ref:string|null,reason:task_started|task_finished|memo_changed|notebook_changed|local_changed|idle_changed|global_changed}`，薄失效hint，consumer依正确owner refetch。现有owner `_emit` 与现有global WS peers；stored-only视图无runtime也能收到global owner-qualified hint。全局写后Main调用 `secretary.web_events.config_changed(config_path)`，只取path.parent，不同步读config/DB。一个进程 `subscribe("tui_gateway",callback)` 注册替换旧listener；清理可 `unsubscribe("tui_gateway")`，没有新线程/socket。无listener即no-op。跨进程直接编辑不产生本进程WS事件，entry/reconnect重新读；不造轮询器。

## 1. 任务条款与实际覆盖

06 §0.4–0.5：新增投影不建立浏览器/服务端第二数据库、不改旧API；§1.14/§2.5：真实fence状态、非阻塞压缩独立取消、commit与cancel唯一胜者；§1.15/§2.6：真实global/local、live task、timer estimate及ordered effective Memo；§2.7：浏览器Notebook瞬时人类输出；§2.9：新方法契约/owner/error/状态/内存边界；§3/§4.5–4.7：正式原生接线与定向兼容证据。02 §1身份和profile、§3 currentpointer/Memo、§4 Idle生命周期、§5.4真实childowner、§5.9取消不撤销已成功Noting终端／Snapshot、§6未启用原生和只读关闭约束均保留。

## 2. 实际变更

当前Git HEAD `8e7ba807f8f4f827f947e5e4184f46173d80cfd2`；产品为工作区未提交增量，源hash见 `.hermes-dev/round2-evidence/reads/source-manifest.json`。没有stage/commit，没有改根看板、规格、前端、旧Secretary slash、Turn中断／finalizer或provider。

| 文件 | 实际职责 |
|---|---|
| `agent/compression_read.py` | 对真实registration/fence做只读state和原子try_cancel；32条内存终态，不建durable账本 |
| `agent/compression_facade.py` | 现有registration附observation，fallback换fence继承该operation已获胜的取消，原finally记录结果 |
| `secretary/web_read.py` | readonly resolver/currentpointer/renderer、Memo、真实task和真实timer投影 |
| `secretary/web_events.py` | 无线程／socket的薄订阅器、正确DB owner hint；无listener即no-op、observer失败不影响原写结果 |
| `secretary/noting_child.py` | 真实active注册／移除和真实Snapshot成功commit之后的observer，仅生命周期观测 |
| `secretary/noting_timers.py` | 真实arm/cancel/fire前后hint；只读同period/liveowner deadline观察，不attach/recover |
| `hermes_state_secretary_notebook.py` | Main已批准三个便利wrapper成功_execute_write后observer；不改conn/schema/事务语义 |
| `tui_gateway/contracts/web_read.py` | 四新method和secretary.changed契约 |
| `tui_gateway/methods_web_read.py` | 新handlers，显式profile／launch动态解析、独立readonlyDB、原生错误、既有WS fanout |
| `tests/agent/test_web_compaction_control.py` | 19项真实压缩DB/facade、Main auto、Noting请求、manual partial、fence races／fallback／晚worker／错误 |
| `tests/secretary/test_web_read.py` | 8项只读DB前后、profile/ref、noSnapshot/off、live/stale child、真实timer及正式WS fanout |
| `tests/secretary/test_web_read_child.py` | 1项实际run_noting_task循环中的只读观察、真实start/finish及成功Snapshot/Memo事件 |

## 3. 正式调用路径

Main已接通 `server.py` 的方法module注册和 `contracts/__init__.py` catalog，并生成共享TS/OpenRPC；本Agent的最后一轮RPC测试只调用实际 `server.handle_request`，不临时register。Main的global配置写入成功接缝调用 `config_changed(config_path)` 已独立取得3项保存路径证据（见Main对应报告/日志，本报告不冒称由本Agent执行）。

压缩manual/auto/Noting最终共同进入既有facade和原生compress_context，其registration观察既有fence；cancel在同registration RLock下调用同fence try_cancel，不获取其commit锁阻塞，不设置任何Turn event。Main实际auto压缩取消后继续同一run_conversation第二次provider调用并正常完成；普通queued Prompt通过实际 `_enqueue_prompt` 放入后，取消不会移除其envelope或图片。Noting通过实际compact_parent→原生request_context_compaction→native worker取得admitted，合法Snapshot commit后取消，不回滚Snapshot。manual通过实际compress_now／here 2保留尾部入口取消，真实DB与完整前后列表一致。

Secretary读取直接以stored id和profile打开 `SessionDB(..., read_only=True)`；不经create/resume/attach/ensure、没有identity backfill或pointer reselect。所有展示时间用现有profile-aware formatter；Notebook只向请求结果返回现有人类renderer，不持久化feedback/普通row/Message UID，也不碰Main模型prefix。状态实时registry要求DB绝对路径+父ref双匹配，DB running孤儿输出unknown。缺失存量identity为unavailable而非创建。事件只作失效提示；UI按结果中的profile_home/ref过滤、entry/route/reconnect重新读。

## 4. 验证结果与证据

环境官方PM `.venv` Python 3.14.7，canonical `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh`。测试全部是隔离测试DB；真实模型／外部HTTP调用0；summary/provider返回只在外部依赖边界受控，真实SessionDB、compression fence/commit、正式native Main/Noting请求、真实child Loop/timer与注册dispatch不被替换。未重启53445现有runtime。

| 最终有效证据 | 结果／覆盖 |
|---|---|
| `reads/formal-and-error-tests.log` | 27 PASS，11.0s：本分区8 Secretary +19 Compaction；正式dispatch，无临时方法注册；fallback成功和terminal 401失败状态真实 |
| `reads/queue-preservation.log` | 1 PASS，2.2s：加强后的实际Main auto取消，同Turn继续，native `_enqueue_prompt` envelope/附件保持；仅定向补受影响断言 |
| `reads/child-final.log` | 1 PASS，1.8s：最终observer版本的真实Noting Loop，running初亮、readonly前后DBdump/父prefix相同、Snapshot/Memo提交及finish回idle |
| `reads/final-targeted.log` | 49 PASS，9.5s：当时23自有测试+4既有fence overlap/fallback注册回归+21既有真实timer deadline/close/restart/disabled回归+1 child；其后自有测试扩为27，生产机制仍共享有效旧回归 |
| `reads/health-repaired.log` | `scripts/check --only health --base HEAD`：工作区29 files，0 blocking/0 advisory，2.9s；与主会话／T3a共享同版本结果，不是全量检查 |
| `reads/ruff.log` | 本Agent12个源码／测试文件定向ruff PASS |
| `git diff --check` | PASS，无空白错误 |
| `reads/source-manifest.json` | 当前HEAD、冻结基线、最终自有文件SHA256、解释器、真实模型0与覆盖声明 |

有效测试范围合计53项（27自有读／压缩＋1真实child＋4 legacy fence＋21 legacy timers），新增断言定向复测，未重复整套Python或全量门禁。

过程失败原样保留：`production-path-tests.log`首次late worker断言在summary刚返回、原生补偿未结束时读取了中间compression_count，修正为等待完整native compress_context退出；`formal-dispatch-tests.log`新增off deadline测试原先误以为会留下trigger_produced，原生实际消耗并删除period，按真实关闭语义修正。二者是证据等待／预期错误，修后分别在repaired/formal-and-error日志通过，不掩盖历史失败。`health.log`首次有两个本分支blind catch和当时T3a问题；本分支改为traceback日志，最终health-repaired已无blocking。

## 5. 缺口与覆盖边界

- 当前目标默认in-process（Main审计确认turn_isolation=False）新增方法完整可用并有机制证据。
- 原生compute-host可选模式没有伪读parent代理；新compaction RPC明确4010“requires owning compute host”。该模式的新read/cancel桥接未实施／未验证；旧compute-host／CLI/TUI接口保持原样。本任务未新增配置开关或改变默认模式。
- 本Agent未执行真实浏览器／HTTP WS连接、Main/Noting真实DeepSeek模型／图片、四视口或真机验收；这些由Main统一restart／Integration及后续独立Validation取得。既有Transport注册/fanout已验证，不冒称live53445已运行新代码。
- 跨进程直接手工配置编辑不能在当前进程产生writer observer事件；entry/reconnect重新读，未建立额外轮询器。
- 全量Verification/Validation／最终扩大检查由Main统一安排；本报告仅Development机制交回。

## 6. 接口影响与兼容

新增四方法及一个事件；原方法required/optional输入、旧response/error、slash feedback持久化、旧events字段全部不改。新Secretary profile required但允许显式空串''表示原生launch，在调用时使用server._launch_home()，不强映射default；new compaction profile optional，有值时核对runtime home，异profile4001。read返回profile_home是来源owner事实，只用于前端内存过滤，不能当请求权限路径。unknown/absent分开，stale-running不冒称active。Notebookglobaloff/unknown4030，localoff可读；所有read纯SELECT，无新Turn/Notebook/Memo/registry/Idle副作用。

事件有意义变化后走既有owning event及global peer fanout，没有专用socket、scheduler或一秒poll。订阅以固定tui_gateway键替换，进程结束无额外资源；测试／显式卸载可unsubscribe同键。

## 7. 建议后续动作

Main集中review这12个实际文件及共享注册／global writer hook。因DTO在初次生成后补了profile_home／空profile／compaction optional profile，重新生成既有共享TS/OpenRPC并验证generated契约；前端已收到修订接口里程碑。之后统一重启目标53445运行最终源码，复用本报告的53项机制证据，补真实REST+WS/浏览器status/Notebook瞬时读和四视口用户旅程。无需重复旧fence/timer完整测试或扩大产品范围。compute-host增量如需作为本轮目标启用，先派遣同native supervisor桥接，不能将parent read当有效来源。
