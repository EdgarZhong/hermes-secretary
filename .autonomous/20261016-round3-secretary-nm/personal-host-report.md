# C11-P 正式原生 host → loopback fixture 开发证据

状态：**六场景开发取证完成，round3 已恢复并显式释放**。原生TUI stdio RPC、真实DeepSeek、真实MemoryManager/Provider及本机HTTP依赖均实际运行。没有真实NM调用、Memory/Thread/Space写入、生产代码/测试修改或部署；不是独立Verification/Validation结论。

## 1. 条款、授权及实际版本

依据个人PHASE3现行§1–7，重点§2 Main/Cron/Noting资格、§3原生Bundle构造/冻结/重建与host准入Recall、§5 completed正文/真实UID/明确ACK prefix、§6独立Global Rule、§7正式接缝。§4.1/P2沿用户例外只引用已有基本模拟，未重测或真实写入。公共plan及snapshot-index R3-016～018、冻结d19018、executing-plans和autonomous-run交接节继续有效。

主会话明确START并移交round3；开始前核配置hash与其交接证据一致，未发现存活的原生gateway/driver。实际生产代码：公共 **`f66a8f80b4bab39b0a785a552019c91a6e9becba`**，个人 **`8682ff858a56ac735098ee6289d4ab547d3ae755`**。取证结束公共HEAD为`81a0e1da6ce6708bdbe3d437977ec27750b7b0dc`，与生产SHA差异仅plan/CLAUDE/real-model-report/regression-plan文档；没有把后继纯文档SHA冒称模型运行的产品版本。

本次沿既定`round3`隔离profile运行，未另建profile，不改Dashboard。cold新建/真正native rebuild抓fresh；有效root的cold resume保持冻结。没有新增二层Bundle缓存或产品语义。

## 2. 本次变更与临时配置

tracked仅更新本报告；公共和个人生产/测试均只读。完整材料位于个人ignored `/Users/edgar/code/hermes-nmem-provider/temp-r3-personal/evidence/c11-p/`，精确hash、请求定位和结果见最终`manifest.json`。

运行使用已review的fixture、官方CLI shim、RPC驱动和现有installer。ignored driver补了一项实际DTO适配：`tools.show`只接session_id，不接profile；首次参数被原生校验拒绝，发生在任何模型请求前。停止自有gateway后修ignored驱动并重启，没有改生产RPC或绕过校验。后续全部原生RPC正常。

安装前保存config原bytes和原插件状态；现有installer安装后，ignored wrapper按批准的原生字段临时设置：

- `platform_toolsets.cli: [memory, conversation_history]`，保留真实MemoryManager所需memory组及History。
- `agent.coding_context: off`，其余不含这两项能力的原生toolsets进入`agent.disabled_toolsets`，避免误禁含memory/History的复合bundle。
- `tools.tool_search.enabled: off`、`noting.enabled: false`、`scheduler.enabled: false`；配置的MCP entries关闭。没有terminal/execute_code、文件写入、skills、delegate、浏览器或外部连接行动。

临时配置已整体纳installed双hash；restore恢复所有原值。原生installer、模型路由及生产权限机制未改。Noting关闭不用于声称其资格已由本次实测证明，矩阵复用既有机制证据。Provider内部官方Search继续运行在固定loopback endpoint，不经过模型工具面。

## 3. 实际正式路径与身份

`rpc_driver`只发送原生TUI stdio RPC → `tui_gateway.entry`/真实Main → 原生Loop及MemoryManager → 安装的个人Provider → 本机fixture。真实模型沿既有`run-native.py`的原生DeepSeek通道，实际请求model为`deepseek-flash`；未mock模型、Loop、storage或Provider方法。未直接调用`_archive`，没有用MemoryManager孤立调用替代host生命周期。

先通过原生`tools.show`检查raw目录，再发无行动合成首轮，检查首实际request dump的完整顶层工具。**两类证据不同**：raw目录不是完整agent.tools。二者及后续全部14个Main实际请求均只含`conversation_history`。插件MemoryManager仍实际加载：Bundle/Recall/完成归档都已产生依赖请求。

有效Main runtime初为`83356857`，冷恢复后为`a768c24c`；stored session为`20261017_022734_332db7`。数据库真实source为`tui`。Conversation为`conv_d292d194fa1f41db92fe015e210aa361`，同一Thread为`hermes-personal-conv_d292d194fa1f41db92fe015e210aa361`。所有规范来源以真实Conversation/UID定位，未用Thread或physical row ID替代。

全程SQLite只以`mode=ro`观察实际state.db/receipts.sqlite3；所有持久变化来自正式host/Provider。Thread累计24条正文均映射唯一真实native UID，时间沿既有Provider转换为带时区ISO秒精度；源DB保留亚秒值，不冒称出境保留亚秒。

## 4. 六场景与执行证据

共12个completed Main Turns、14个Main实际API request dumps；另通过原生`session.compress`做3次摘要尝试。实际请求路径与hash保存在`native-request-dump-manifest.json`，不在报告输出root/headers/凭据。

| 场景 | 实际结果与证据 |
|---|---|
| P-HOST-01 cold新Main/Bundle/Recall/completed归档 | **PASS**。Bundle A请求明确`include_working_memory=false`；真实root含独立Rule和A。官方Rust CLI实际GET `/memories/search?q=…&limit=5&mode=fast`，当前api_content含合成完整ID/标题/日期指针，没有Memory正文。完成回复后正式sync触发Thread import，明确逐项ACK，native UID/正文核对见`first-turn-identity.json` |
| P-HOST-02 短CJK | **PASS**。“之前”从真实用户输入到达官方`nmem --json m search -n 5 -- 之前`，有对应fixture请求；不通过Provider直调代替host准入。`cli.jsonl`、`cjk-result.json`及实际request dump |
| P-HOST-03 同Turn真实工具/冻结root | **PASS**。模型实际调用`conversation_history`，下一请求真实携带tool result。同Turn两请求root hash均`420113d036e65e76a55ed70b225d5a7dc7107f0f29f7a5a120c8e53dde21b26a`，工具Schema hash相同，Bundle GET仍1。`requests-before-offline.json`、`history-result.json` |
| P-HOST-04 Recall离线/History仍可用 | **PASS**。两次受控503，当前输入附`NM candidate lookup unavailable this turn`，未替换旧指针；在503期间真实History工具仍成功执行。旧历史api_content可能重放指针，已明确观察，不宣称清空历史或实现单Turn载体。`offline-evidence.json`、`offline-history-result.json`、`http.jsonl` |
| P-HOST-05 valid-root cold resume | **PASS**。fixture改B后正式close、原生gateway重启、resume同会话，再执行真实Turn；root逐字hash仍为A，Bundle GET保持1。只读核对原生`system_prompts`内容寻址表中的已持久化root。`before-cold.json`、`cold-evidence.json`、cold RPC记录 |
| P-HOST-06 真成功压缩重建/fresh Bundle/同Thread suffix | **PASS**。前两次原生摘要会增长，`summary.noop=true`，均不计成功。通过正常输入加入合成可压缩台账并移出原生近期保护区后，正式压缩**26→10消息、30,358→21,126 tokens**，`noop=false`、无fallback，真实DB summary UID落库。为区分no-op尝试，最终fixture用D；压缩后实际root含D、hash改变，规范Ref/Thread不变，归档仍只追加新UA。`compress-final-result.json`、`compaction-evidence.json` |

依赖请求总计：Bundle 4次（A/B/C/D；B/C分别发生于未成功的原生压缩尝试，未算成功边界），Recall 12次（含2次503），Thread import 1次、append 11次。严格fixture拒绝所有未声明endpoint/method，无转发。官方CLI协议已由实际host预取证实，不再停留于准备时假设。

按已ACK请求串接的24条payload fingerprints与真实receipt prefix完全相等；同prefix未重发import，合法压缩后没有换Thread、发送摘要/tool/API注入。逐条UID/时间/正文hash见`archive-UID-mapping.json`。这是本地fixture观察，不是实际NM服务端去重或exactly-once保证。

本次没有重跑39/46测试、P2、公共有效组或大型门禁。ignored harness最终Ruff通过；不以静态检查替代以上真实产品证据。

## 5. 失败、观察修正与覆盖边界

- 初次`tools.show`带不允许的profile字段，原生4000明确拒绝；发生于首模型请求前，ignored driver按正式DTO修正，未恢复alias或改产品。
- 两次压缩外层返回`status:compressed`但内层`noop/refused_would_grow=true`，真实消息全部保留；只按最后真实成功边界计PASS，没有调小原生保护参数或手工删root/写DB造成功。
- 最初只读观察查询legacy `sessions.system_prompt`得到NULL；原生实际从`system_prompts`按hash解引用。已按正式get_session投影修正观察，证明恢复root逐字相同；不是root丢失或生产修复。
- 最终UID观察初次把原生亚秒时间与Provider既有秒精度输出作精确浮点相等，触发观察脚本assert；按现行秒精度契约修正后24条均匹配唯一UID。该assert使最后显式close命令文件未生成；随后自有driver的stop成功关闭stdin并等待gateway退出。所有已接纳归档此前已明确ACK，进程/lease清理和收据已核。
- 准备驱动未单独保存native子进程returncode，不能宣称该码为0；driver本身exit0，原生/driver进程均已消失。fixture最后准确PID的SIGINT退出130/KeyboardInterrupt是预期停止，不是运行失败。

确定性失败/中断/ACK重试/divergence/脱敏/scope矩阵复用C9-H与P1/P3有效机制证据；本次Noting临时关闭，没有把它当Noting独立fetch/归档资格的真实模型反证。P2仍只已有基本检查。无真实NM服务端、治理、云端部署或独立门禁结论。

## 6. 安全、恢复与显式释放

ProviderHTTP与官方CLI全程同一个literal loopback `http://127.0.0.1:55670`，使用合成token，不继承真实NM凭据。fixture只返回合成Bundle/指针/严格ACK；未创建任何真实Memory/Thread/Space，不调用ask或治理。真实DeepSeek凭据仅由既有wrapper在内存读取，不打印或进入Git。原生request dump保留在ignored profile，仅报告路径/hash与工具名。

**已恢复并释放round3：**

- 原配置hash／恢复后hash完全相同：`ca8a60eb5cf213e74029452c7aedd1e8632e129031bc3ef6f1a5997aea6afc1e`。
- 原插件不存在，安装副本已移除并恢复为不存在；installed配置的所有临时字段均随原bytes恢复。备份和journal保留供review，未删除DB/历史/receipt或MEMORY/USER。
- 自有gateway/driver及fixture PID均不存在，control socket和fixture-ready文件已移除；`running_children=0`、`future_schedules=0`、`session_turn_leases=0`。既有11条child记录均completed，本次未新建child。
- accepted归档prefix为24且全部明确ACK，停止后不再有归档worker进程。`handoff-release.json`、`runtime-stop-evidence.json`、`restore.log`和installation journal保存恢复/停机证据。

没有遗留需要下一owner继续运行的服务、模型请求或待执行命令。round3现交回主会话调度；不要把C11合成session当用户真实会话继续。

## 7. 交接与下一步

主会话亲自review本报告、ignored manifest、真实请求/UID/ACK/压缩及恢复证据；可共享给本轮独立门禁复用，不重复同版本有效测试。当前六场景没有未关闭产品缺陷；全部生产和tests保持未改。此Agent停止写入，不stage/commit，等待主会话下一指令。公共round3独占权已明确释放。
