# U16 · Idle Noting 父 owner 生命周期修复交回

状态：实施完成，待主会话亲审／集成；未提交、未push、未部署。执行工作区 `/Users/edgar/code/hermes-secretary-idle-noting-owner`，分支 `codex/idle-noting-owner-20261027`。

## 1. 对应条款

- U16、plan末尾主会话设计、07 §8.1新增生命周期条款；白板P1–P5／N1–N4的联合生命周期、正常提交与完成投递要求；保留02 §4.8／§5.4／§5.11的原子准入、持久child、真实Active冻结与缓存前缀。
- 原始Downloads问题报告已完整审读；使用虚构隔离Profile／Session／正文，不复制生产个案身份到实现或测试。
- 主会话本轮补充收敛：global／local／Idle关闭仍沿既有terminal cleanup，不增加重开自动补跑；“未消费due／period／trigger保持”针对关闭、epoch退休、owner被替代、弱引用消失及真实前缀不可用等生命周期失效。开关off不freeze／不admission／不起child，原开关状态断言保留。
- 未改schema、Prompt、预算、阈值、Provider、调度器、生成协议、增量包recovery/history/web routers，也未改三核心或规格文档。未派生子Agent。

## 2. 实际变更

1. `noting_timers`既有记录改为内部`_IdleTimer`：weak exact parent、DB／Conversation runtime key、原生epoch、原period，以及有效／firing事实。`holds_pending_timer`不再把同DB/ref其它父对象视为持有者。timer firing保持记录直至同步准备交接；过期attach也借同一记录做短暂准备保护，不建新账本。线程start失败移除准确登记，保留durable deadline。
2. `refresh_maintenance`在host锁外重新读所属Profile的有效设置、局部参与、当前session、period；`holds_maintenance`在host锁内只读短时注册事实及现有completion，既不查DB／网络，也不解析路径。已claim同周期的firing记录不因trigger时间更新而出现保护真空。
3. orphan、TTL、LRU接同一维护predicate；有效等待／有界工作沿原grace延期，cap沿原live-work豁免。关闭、归档／删除、开关失效、epoch变动与owner替换会失去豁免，不新增忙等或永久保活。
4. `noting_scope`保存可信runtime binding；closed对象不可重新bind。迟到host tick对“曾binding但已非current”的A先skip，不能抢回B；真实新Main／构造的通用bind边界保持。
5. Idle同步准备复用原生`_session_persist_lock`和epoch：核owner／当前route／归档后，真实冻结父Active前缀，再claim／admit并预注册现有completion。`close()`在同一短锁内标旧owner关闭、退休epoch、准确取消旧timer；通知、资源关闭和所有Framework发布在该锁外。没有真实可冻结前缀明确返回`parent_context_unavailable`，不消费周期，不拼DB前缀、不新建临时Agent。
6. 既有`_NotingCompletion`增补epoch、准确Idle continuation owner及native request交接事实。新child、等待现有child、已正常完成任务复用压缩，均保到原生压缩／Framework收尾。已完成任务复用只等原生`request.completed`事件释放，不重发旧Framework、不建任务账本；pending交接防原child cleanup抢先移除。准备／派发失败总能释放预注册completion；Force派发通知失败不破坏已启动child的owner。
7. 测试夹具补真实活动前缀；local off仍可有待清退timer，但它不再产生回收豁免，因此对应`holds_pending_timer`断言改为false，原period清退／重开断言未放宽。模拟改Conversation的旧测试增加真实身份边界bind，并先断言host tick自身不能重bind。旧cold测试唯一代码更新为内部timer记录`.timer`定位；其失效配置未改。

8. **主会话亲审后的窄修补：** 首包47e7f531仍有cleanup在等待Framework前读取pending、以及begin返回后才登记pending的两处TOCTOU；主会话指出后，本次将handle选取／创建与`native_pending`及准确continuation owner登记合到一次ACTIVE短临界区。`_end_completion`先取得Framework锁，再在ACTIVE短临界区重新核pending／request／lifecycle，并原子closed／pop；固定Framework→ACTIVE，不在ACTIVE区等待Framework／persist／DB／native。callback与等待线程保持锁外。`noting_compact`只增内部callable属性，显式暴露已有relevant函数身份；child在persist短锁仅读当前request，并同时核parent／db／Conversation／epoch与relevance函数身份，不调用relevant，不将另一轮请求完成事件误当作本次receipt。主会话已明确批准这一最小内部接缝。


## 3. 正式路径与锁顺序

`scan_profile → 原生后台resume → 真Main Heartbeat → note_main_turn_finished → 原daemon timer → _run_idle_event → 短persist身份核验／真freeze／claim／admission／completion → 锁外spawn_noting_task → 真child工具循环 → Commit Gate → 正常finish后原生request_context_compaction → 摘要引擎／durable publication → Framework → 原task生命周期cleanup`。

普通orphan回调先在sessions锁外刷新维护资格，再在resume／sessions锁下核准确注册事实。TTL／LRU同样先刷新后claim；新predicate没有sessions→conversation／persist／Framework反向等待。Idle同步准备的persist锁不包Framework或模型请求；child正常提交后的压缩等待发生在现有child工作线程。已完成任务复用只等待原生admission receipt返回，native完成事件在独立context-scoped轻量收尾线程处理，不新增调度器／模型执行器。

## 4. 验证证据与版本

执行环境：`macOS-26.7-arm64-arm-64bit`，官方PM `Python 3.14.7`，所有Python测试通过`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh`，不直接pytest。Profile cwd均为Git root外临时目录；后台场景fixture禁止socket connect／connect_ex。模型与摘要只在返回边界提供受控数据，真实freeze、child、DB、Commit Gate、native compaction及publication均执行。真实Provider／微信／生产请求为0。

- 基线HEAD：`e1b124d4509cebf8b71a436a2237031cb3bf2087`。
- 最终可审tree：`8ffc46f25e02caa1d610c85c4b072c23b658d73d`（未commit，14个变更文件含新测试；替换首包47e7f531）；逐文件SHA见`source-manifest.json`。
- 完整补丁：`/Users/edgar/code/hermes-secretary-idle-noting-owner/.hermes-dev/incremental-sync-20261027/idle-owner/idle-owner.patch`，SHA256 `16c53b7f8dacb52e95cfce5f9916218235120ba06bad5d444ad1afd341c12f33`。真实Git index保持未暂存；检查使用ignored临时index。
- 证据目录：`/Users/edgar/code/hermes-secretary-idle-noting-owner/.hermes-dev/incremental-sync-20261027/idle-owner/`。

| 证据 | 结果与精确含义 |
|---|---|
| `before.log` | 原HEAD同一后台Heartbeat→native orphan→Idle反例：1通过／1失败；失败直接证明父owner被提前弹出。此时尚未修改产品代码 |
| `targeted-3.log` | 当时7文件105项全通过：timer、Main忙闲、真实child／正常压缩／失败／复用；后续边界补强按下述定向复测 |
| `final-targeted.log` | 7文件112项中111通过，1项旧模拟身份切换测试缺真实bind边界；现已补输入与拒绝断言，由`final-directed.log`关闭，未删断言 |
| `final-directed.log` | busy 6、reuse 25、owner 23，54项全通过；包括主会话追加A→B→A迟到host tick、预注册派发异常、Provider／forced／取消矩阵 |
| `final-timer.log` | owner 24＋timer 20，44项全通过；新增timer.start失败释放／合法attach恢复 |
| `final-completion.log` | 首包completion补强时reuse 25＋commit-order 19，44项通过；主会话后续发现的TOCTOU不能由该日志排除，已由下述原子barrier测试补证 |
| `final-check-3.log` | 首包47e7f531十项检查通过，health 13文件0 blocking／0 advisory；该版本已由本次窄修补替换 |
| `completion-atomic-1.log` | 三个确定性新增反例均通过：旧cleanup已开始且等待Framework时新reuse先reserve；旧cleanup先closed／pop时新handle登记；同parent／epoch的另一轮native request槽不得附着 |
| `completion-atomic-final.log` | 原子修补主路径定向3文件71项全通过：reuse 28＋commit-order 19＋owner 24；24.2秒，仍保真实child／原生压缩／Framework路径 |
| `completion-atomic-owner-final.log` | 最后补强request引用须同时匹配当前parent epoch／Conversation后，定向重测3个原子barrier／同owner槽替换反例全通过（4.1秒） |
| `completion-atomic-check-final.log` | 最后14文件十项冻结检查全部通过，health 0 blocking／0 advisory；`git diff --check`通过，未改规则／阈值／等级 |
| `native-regression-1.log` | 原生orphan races 29、startup sweep 10、gateway-owned reap 8、profile flush 3、close tool sequence 5，共55项通过；native compaction另32通过／4失败。新增failure夹具初次漏termination的4失败已在最终owner矩阵全部关闭 |
| `baseline-native.log` | 完整HEAD隔离导出中同样复现native compaction 4失败与cold resume 17 setup错误，证明不是本轮新增；导出来源为上述HEAD，测试配置未改 |
| `targeted-2.log` | 原冷Scheduler宿主20项通过；其它中间失败日志保留，不作为当前通过凭据 |

最终七个聚焦文件的适用测试合计116项，以上同版本定向证据组合覆盖；不是一次116项的单次总跑，不冒称全仓绿。`source-manifest.json`给最终文件SHA；每次中间日志属于对应修补前状态，主会话亲审后的最后completion原子修补以`completion-atomic-final.log`的71项、最后`completion-atomic-owner-final.log`的3项及当前十检查为准。首包源码指纹另保存在`source-manifest-before-completion-atomic.json`，不改写历史日志。

后台新增场景的4路（保留／实际orphan × 不压缩／真原生摘要引擎）自然触发Idle，记录准确父对象与非空prefix、completed child、Snapshot；真压缩在`_call_summary_llm`返回边界给虚构摘要，核durable commit及其后Framework。摘要期间再调用实际orphan仍保留父owner，结束后再次orphan可正常清退。另覆盖长期Main反复orphan、TTL／cap压力、exact旧owner取消不碰B、跨DB同ref取消隔离、close先赢／freeze先赢、弱引用消失、无前缀保原周期后合法attach、各种失败不压缩与旧Notebook保留、forced合法快照及保护释放。明确的失败注入不作为成功freeze／spawn证据。

## 5. 缺口与限制

- Linux真实目标平台定向未执行，按分派由主会话集成安排；本地为macOS arm64，不伪造OS。不把受控返回边界当真实模型行为验收。
- native compaction基线4失败：`test_supported_framework_writer_can_create_native_foreign_tail`原地／轮转两项、`test_foreign_framework_cannot_forge_a_summary_publication`、`test_ordinary_native_compaction_keeps_credential_refresh_and_status_seams`；均检查旧摘要标记。未改断言，未将它们说成通过。
- `test_cold_noting_resume`的17例在setup使用旧`noting.idle_delay_seconds`等已退出配置而被配置门禁关闭，基线同样无period；没有用这套失效夹具冒称冷恢复通过。当前合法attach／无前缀／真实后台resume已由新增原生测试覆盖。
- 未执行生产旧失败Noting补跑、数据库重置／迁移、真实模型、真实微信、UI、部署。独立Verification／Validation仍属主会话整轮门禁。

## 6. 接口影响

公开API／schema／默认预算／开关清退语义保持。`_begin_completion`仅增内部默认参数`native_pending=False`，用于原子reserve；compaction callback仅增内部relevant身份属性，不改native API。内部`prepare_joint_noting`与`_run_idle_event`只增可选`expected_owner`；timer取消只增可选exact parent及通知控制。`_timers`是内部实现记录，由tuple改dataclass；对应私有测试定位已改。closed父实例不再被判Main，避免关闭后的旧producer或host tick复活运行身份。没有更改Noting正常结束／强制快照、非Idle压缩独立前进和原pointer规则。

## 7. 建议后续

主会话亲审此tree／补丁，重点核原生锁顺序、completion事件交接、A→B迟到tick及异常释放。按约定先合main再并入增量分支；集成后只对变化及Linux目标平台取定向证据，保留基线失败说明，再进入整轮独立双门禁。无需改模型／Prompt或生产配置；上线必须另有授权及实际发布验证。

## 8. 主会话接收（2026-10-27）

主会话亲审完整源码、正式接线、锁顺序、准确request身份、失败释放与确定性barrier测试；最终14文件SHA与manifest逐一一致。先在main提交0a5d09cdcf并自动push，再将同一14文件补丁接入增量分支；07只纳本轮生命周期段，main原有dirty逐字保持。已关闭本包主会话发现的迟到owner抢绑定和cleanup／reuse竞态。Linux定向与整轮独立门禁尚未执行，未部署。


## 9. Linux目标平台定向补证（2026-10-27，依赖阻塞）

**结果：未运行测试。** 主会话接收后的精确main提交为`0a5d09cdcf3d3a03cb8d83e6bdad284d87a10acc`。已按本轮授权通过`ssh alex`只读检查指定解释器；它是Python 3.14.8，但`import pytest`退出1并明确报`ModuleNotFoundError: No module named 'pytest'`，`find_spec("pytest")`亦为None。因此遵照“缺依赖不安装／不改生产venv”的分派要求停止，没有调用runner、没有直接pytest、没有切换其它Python或安装工具。此项是实现证据补证受阻，不是独立门禁结论，也不推翻先前macOS证据；Linux范围保持未验。

| 项目 | 证据 |
|---|---|
| 目标主机 | Alex，ubuntu；`Linux VM-0-13-ubuntu 6.8.0-138-generic #138-Ubuntu SMP PREEMPT_DYNAMIC Fri Jul 31 22:41:49 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux` |
| 指定Python | `/home/ubuntu/hermes-secretary/.venv/bin/python`；`3.14.8 (main, Oct 14 2026, 01:04:34) [Clang 23.1.3 ]`；只读探测显式`-B`及`PYTHONDONTWRITEBYTECODE=1` |
| 精确源码归档 | 本地`/Users/edgar/code/hermes-secretary-idle-noting-owner/.hermes-dev/incremental-sync-20261027/idle-owner/linux/source-0a5d09cdcf.tar.gz`；83,761,717字节，SHA256 `1420d7b72b974c7421aa941b056768bb0c2b92018cec1ab33b97f9c448f4472e`；归档与逐文件核验用时4.504秒；未上传 |
| 14文件SHA | `/Users/edgar/code/hermes-secretary-idle-noting-owner/.hermes-dev/incremental-sync-20261027/idle-owner/linux/manifest.json`逐文件记录提交内容SHA256，与原最终`source-manifest.json`的14项全部一致；不从dirty工作树打包 |
| SSH探测收据 | `/Users/edgar/code/hermes-secretary-idle-noting-owner/.hermes-dev/incremental-sync-20261027/idle-owner/linux/dependency-probe.json`记录完整只读命令、UTC开始时刻、退出码1和耗时3.595秒；原始输出`dependency-probe.log`，首轮／补充分别为`environment.log`、`python.log` |
| 实际测试范围／次数 | 0文件、0项、0次执行；预定三文件`test_idle_noting_owner.py`、`test_idle_noting_reuse.py`、`test_noting_timers.py`未执行，不能将预期72项记成通过 |
| 生产与清理边界 | 未修改生产checkout／venv／配置／数据库／服务／凭据，未重启或调用模型／微信／生产CLI。未创建远端专用/tmp目录、未上传源码或生成远端测试产物，因此无远端专用目录需清理；未触碰其它/tmp或生产备份 |

依赖具备后，待主会话提供获授权的测试解释器／隔离环境再执行原定命令；本次没有自行扩大权限。原定但**未运行**的入口为：在专用`/tmp/hermes-incremental-verify-<唯一后缀>/source`中，设置独立tmp `HERMES_HOME`、显式`HERMES_PYTHON=/home/ubuntu/hermes-secretary/.venv/bin/python`，经`scripts/run_tests.sh -j 2 --file-retries 0 tests/tui_gateway/test_idle_noting_owner.py tests/secretary/test_idle_noting_reuse.py tests/secretary/test_noting_timers.py -q --tb=short`执行；Profile cwd仍须在源码Git root外。缺pytest时未尝试启动该入口，避免runner转向自动环境构建而改动未授权依赖。


## 10. Linux集成候选补证收尾（2026-10-27，已完成）

**结果：目标提交`862326c0a71547e3315e66eb76496a5ab8ccb1dd`的7文件163个适用测试已覆盖通过。** 该提交集成U16与B1／U17；不是仅测main 0a5d09cdcf，也不是独立Verification／Validation门禁。第9节保留首次缺pytest的历史事实；随后主会话授权按CONTRIBUTING与官方`pm.build_env`在自有临时目录构建全隔离环境，本节记录其实际结果，未改第8节主会话接收结论。

### 版本、环境与依赖边界

- 精确commit：`862326c0a71547e3315e66eb76496a5ab8ccb1dd`；从本地Git提交归档，上传后核SHA256为`f90a7d370653d11aef43864dbd5b503de4d843aa747999ce6e70e10b875bcb22`。对应本地`/Users/edgar/code/hermes-secretary-idle-noting-owner/.hermes-dev/incremental-sync-20261027/idle-owner/linux/source-862326c0a7.tar.gz`及`linux/integrated-manifest.json`。
- U16原14文件逐一匹配接收manifest；远端提取、首次执行后、四例复测后均保持一致，未修改产品代码、测试断言或规则。新增B1／U17所涉四个测试文件SHA另记`linux/final-evidence/result.json`。
- Linux：`Linux-6.8.0-138-generic-x86_64-with-glibc2.39`；Python 3.14.8、pytest 9.1.1；解释器prefix为`/tmp/hermes-incremental-verify-20261027-32f3cf02da9a/test-env`，产物位于专用tmp工作区内。
- 官方PM创建命令（source目录执行）：`/home/ubuntu/hermes-secretary/.venv/bin/python -B -m pm.build_env --source . --out /tmp/hermes-incremental-verify-20261027-32f3cf02da9a/test-env --python /home/ubuntu/hermes-secretary/.venv/bin/python --cache /tmp/hermes-incremental-verify-20261027-32f3cf02da9a/pm-cache --group dev --group test`，默认frozen，退出0，用时23.118秒。生产Python只作启动器，未向其venv安装依赖；未裸pip／uv、未`--resolve`、未改lock或用户配置。
- `HERMES_HOME=/tmp/hermes-incremental-verify-20261027-32f3cf02da9a/home`，`HERMES_RUNTIME_DIR=/tmp/hermes-incremental-verify-20261027-32f3cf02da9a/home/tools`，PM缓存及TMPDIR均在本次tmp根内。测试由canonical runner提供每文件隔离temp Profile，terminal.cwd位于源码Git root外；真实后台测试fixture禁用socket connect／connect_ex，只控制Provider／摘要返回边界，继续运行真实child、DB、Commit Gate和原生压缩publication。没有生产模型／微信请求。
- `uv.lock`前后SHA256：`2bc4db483e9cba927cd7147f9ccbb09635f85bb3f1f36d6e9d51d06b65d1c67e`；`pyproject.toml`前后SHA256：`cadde2f6a92574d292103f43abf66408b1d841cd9ea332ca7f3e3dfc5dcc87fd`；二者也与0a5d09cdcf一致。PM和测试前后核验均未变化。

### 首次七文件与唯一补测

首次使用上述新环境，显式`HERMES_PYTHON=/tmp/hermes-incremental-verify-20261027-32f3cf02da9a/test-env/bin/python`，通过`bash scripts/run_tests.sh -j 2 --file-retries 0`一次执行以下7文件，runner耗时115.7秒（完整进程117.453秒）：

| 测试文件 | 首次实际结果 | 最终覆盖 |
|---|---|---|
| `tests/tui_gateway/test_idle_noting_owner.py` | 20通过、4失败 | 24通过，失败四例按下述环境准备后定向关闭 |
| `tests/secretary/test_idle_noting_reuse.py` | 28通过 | 保留有效证据，未重跑 |
| `tests/secretary/test_noting_timers.py` | 20通过 | 保留有效证据，未重跑 |
| `tests/agent/test_turn_source_persistence.py` | 12通过 | 保留有效证据，未重跑 |
| `tests/hermes_cli/test_history_sync.py` | 44通过 | 保留有效证据，未重跑 |
| `tests/tui_gateway/test_history_sync.py` | 17通过 | 保留有效证据，未重跑 |
| `tests/tui_gateway/test_manual_compress_recovery.py` | 18通过 | 保留有效证据，未重跑 |

首次合计159通过／4失败；四失败均为`test_background_heartbeat_then_idle`在写`source/.hermes-dev/incremental-sync-20261027/idle-owner/result-*.json`时发生`FileNotFoundError`，源码归档不含ignored证据目录。不是模型／冻结／Snapshot错误；原始失败日志完整保留，未改断言。主会话授权且用户恢复自主执行后，仅`mkdir`上述精确目录，复用原PM环境执行：

```bash
HERMES_PYTHON=/tmp/hermes-incremental-verify-20261027-32f3cf02da9a/test-env/bin/python bash scripts/run_tests.sh -j 2 --file-retries 0 tests/tui_gateway/test_idle_noting_owner.py -k test_background_heartbeat_then_idle -q --tb=short
```

四例为`keep-owner-no-compact`、`keep-owner-native-compact`、`native-orphan-reap-no-compact`、`native-orphan-reap-native-compact`；**4通过／0失败**，runner15.1秒（完整进程16.451秒）。已通过159项未重跑；最终163项由首次有效证据＋仅四例失败复测组合证明，不冒称一次全绿。复测再次核14文件和两份锁SHA全部不变。无`.git`导出下runner预编译阶段的`fatal: not a git repository`提示未阻断随后真实pytest执行，两次退出码和逐项结果均已留存。

### 本地证据与远端清理

- 本地根：`/Users/edgar/code/hermes-secretary-idle-noting-owner/.hermes-dev/incremental-sync-20261027/idle-owner/linux/`；`final-evidence/`含首次`tests.log`、PM构建、解释器核验、`result.json`及最终`four-case-retest.log/json`，`four-case-results/`含四份实际结构化Snapshot／child／压缩结果。
- 汇总与指纹：`linux-final-summary.json`记录163唯一测试的证据组合及各日志SHA；命令／耗时分别在`isolated-run.json`、`four-case-ssh.json`、`final-collect.json`。最终补测日志SHA256为`9da7c9a0318e7390f598c3983ce069e46c06f17f57b713bdd652e121217b95aa`。
- **清理已完成：** 先成功取回所有日志与四份JSON并在本地核SHA，再核远端根路径／非symlink／对应commit／测试成功后，用`shutil.rmtree`只删除`/tmp/hermes-incremental-verify-20261027-32f3cf02da9a`。`cleanup.json`、`cleanup.log`、`cleanup-command.json`明确记录解析后精确路径与`exists_after=false`。该目录包含本次源码导出、独立PM env／cache／home和证据；未删其它tmp、生产备份或运行目录。
- 无产品文件新改动、无commit／push／部署、无生产checkout／venv／配置／数据库／服务／凭据变更、无重启或显示操作。整轮独立门禁仍由主会话组织；本节只关闭本次Linux目标平台定向证据缺口。
