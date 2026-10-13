# V-R2-01 附件 RPC 合同整改交接

2026-10-13，GPT-6.1 Sol / high。**后端整改和定向机制证据已交回；V-R2-01 尚未整体关闭。** 用户要求 assistant-ui 研究先于前端整改，所以本任务未修改任何前端文件；新名正式 Web 上传→submit→真实 Agent 读取代表链尚待 Main 集成补证。本报告是实现者交接，不是独立门禁结论。

## 1. 任务对应条款、输入与权限

- 06 §0 L1–111（尤其§0.5旧合同不变）、§1.7 L193–204、§1.10 L233–240、§2.1 L317–334、§3.5 L496–502、§4.5–4.7 L583–617；02 §1.3–1.9 L60–258与§2.1–2.4 L260–356。按派遣读取根AGENTS/CLAUDE、snapshot-index、baseline、plan、完整Verification结论、executing-plans与autonomous-run交接契约；分区文档仅作架构参考。
- 依据首轮 Verification W03/W37及§6认可的 Main 方案：恢复原 `file.attach` 精确合同，以三个新名实现必要增量；保runtime/profile归属、现附件owner/锁/allocation、500000000草稿合计预算与原图片/PDF约束。Cancel只处理该上传，不Stop、不提交补偿Turn。
- HEAD `24510d1c7c3b8dfc95b6d0626be30f090561fa30`，产品基线 `4443aa7b18806246ef84d6003fbd7e1e40cff5a2`。旧精确合同取自 `5ba0481630^`，实际为 `7fea3f5adc695e459b08e1ed832403447f7fbe25`。
- 用户现用53445/5173未操作，未停服、重启、改运行库或发模型请求；原前端和修复worktree均未写。未提交、未派生。核心文档、规格、计划、verification及其他owner文件未改；已有工作区修改保留。

## 2. 精确变更与源版本

| 文件 | 变更 |
|---|---|
| `tui_gateway/contracts/prompt_voice.py` | 移除旧FileAttach新增参数/结果字段；新增独立Chunk/Abort/Info Params+Result，继承原SessionParams；旧六字段结果封闭保留 |
| `tui_gateway/methods_prompt.py` | 949行旧file.attach恢复原路径/bytes语义；969/981/993行注册三个新名。chunk沿原sess_building；abort/info用sess_nowait，避免取消/只读时暖起冷Agent。边界失败保持5028，并记录debug traceback满足冻结health |
| `tui_gateway/prompt_attachments.py` | 原chunk内abort分支抽至同owner的_file_attachment_abort；canonical UUID校验抽为共用_file_upload_id；实际append/sha/offset/hard-link发布实现保持 |
| `apps/shared/src/gateway-contract.generated.ts`、`gateway-contract.openrpc.json` | 使用官方generator重新生成；删除旧file.attach增量、发布三个独立方法/类型 |
| `tests/tui_gateway/test_file_attachment_chunks.py` | 改走正式server.dispatch；分片、abort、stat切至各自新名，保原有12例机制 |
| `tests/tui_gateway/test_file_attachment_compatibility.py` | 新增29例精确合同/错误/权限/只读/取消/失败机制测试 |
| `native-compatibility.md` | 仅更新附件方法manifest、L13增量依据与合同/证据状态 |

没有修改 `test_file_attachment_allocation.py`；其4项有效证据继续覆盖共用独占allocation。所有修改均在白名单。

产品精确SHA256见 ignored `attachment-rpc-fix/source-manifest.json`：methods `83f7eb57f501339b78dd8431d0fe04602d3c81345c1747f3376b36a8e053f491`；owner sibling `7f5428a96ef1f966efbf484beecd5dd6f5416a4ed6ce4700446618189afef5c4`；contract `0a452812965ed6d684d153548f9b052dc7fdc9c225e0026ada6855de12bdd5d0`。其余生成物与测试hash同manifest。冻结检查使用私有index的源树 `835ac9decd7fddc64f95ebf9e53eab5487281e8b`，没有操作共享Git index。

## 3. 正式路径、方法manifest与不变量

所有新名经现 `HandlerRegistry`/binder 正式注册至 `server._methods`，由 `server.dispatch → handle_request → validate_params → handler → check_params_accepted/check_result` 执行。没有新增上传服务、持久库、API层或Agent执行循环。

| 方法 | 输入与结果 | 错误/owner/时序 |
|---|---|---|
| `file.attach`（N，准确恢复） | 原SessionParams=`session_id,profile?`加`path?,data_url?,name?`；结果仅`attached,name,path,ref_path,ref_text,uploaded` | 无path/bytes原4015；解码/处理异常原5028；任何额外键原dispatcher4000，包括此次撤除的upload/stat控制键。bare base64、data URL、workspace路径、profile存储与重复名原逻辑保留 |
| `file.upload_chunk`（A） | `session_id,profile?,upload_id,offset,total_bytes,data_url,name?`；六附件字段加`upload_id,received_bytes,size_bytes?` | runtime内file_uploads+history_lock是唯一owner；单片≤4194304，声明total≤500000000；UUID/offset/长度/元数据/bytes错误5028；额外键4000 |
| `file.upload_abort`（A） | `session_id,profile?,upload_id`；六附件字段加`upload_id,received_bytes` | 同锁仅删除未完成temporary及该owner状态；未知id幂等空progress；已完成文件保留，返回attached=false且path/ref为空；不更改running/inflight/Pending、不暖Agent |
| `file.attachment_info`（A） | `session_id,profile?,path`；六附件字段加真实`size_bytes`，attached/uploaded=false | sess_nowait解析同runtime；只stat真实profile attachments/images与合法local workspace；symlink越界/异profile路径拒绝、remote cwd不stat同名host目录；不建目录、stage/copy/暖Agent或改session |

分片底层沿现有实现：最新已收片的offset+SHA与name/total一致则复用同progress/final；错offset不追加；完成前path/ref为空；末片独占hard-link原子发布完整bytes，仍用原allocation。分片写失败仅清自己未发布temporary/owner，其他完整文件不动。abort与chunk共享同锁，取消不会误停Turn。

只读权限定位仍以session记录的profile_home/cwd为事实，没有新增由浏览器conversation_ref自证所有权的机制；runtime session不存在统一4001。草稿**aggregate**预算仍由原前端唯一预算owner负责，新分片total上限不是另建跨上传aggregate账本。原image25MiB与PDF-render50MiB/25页的合同和decoder未改。

## 4. 验证命令、次数、耗时与证据

全部日志位于 `.hermes-dev/round2-verification/attachment-rpc-fix/`。仅相关小包，无全量门禁、500MB重传或模型调用；PM `.venv`与lock未改。耗时区分runner实际测试wall与包括预编译的外层wall。

| 命令/执行 | 次数、耗时、结果 | 原始定位 |
|---|---|---|
| `.venv/bin/python scripts/gen_gateway_contracts.py` | 1次，0.46s，写两生成物；一致性用例随后通过 | 第一测试包generated 1pass |
| `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/tui_gateway/test_file_attachment_chunks.py tests/tui_gateway/test_file_attachment_allocation.py tests/tui_gateway/test_file_attachment_compatibility.py tests/tui_gateway/test_attach_does_not_wait_for_agent.py tests/tui_gateway/contracts/test_generated.py tests/test_tui_gateway_server.py -k 'not catalog_covers and (not test_tui_gateway_server or file_attach)' -q` | 1次，runner5.4s/外层14.55s，实际5文件47pass。最后legacy路径写错、runner未收录该文件，**没有把它算成验证通过**；已另用正确路径补测 | `tests-first.log` |
| `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/tui_gateway/test_tui_gateway_server.py -k file_attach -q` | 1次，runner1.2s/外层2.22s，7pass；不是discovery估计的645全包 | `legacy-tests.log` |
| `.venv/bin/python …/legacy_contract_probe.py` | 首次0.36s因ignored脚本root parents定位错误而import失败；修正后1.61s，13组原提交/整改正式dispatcher对照完全一致；原Params与Result字段集合一致 | `legacy-probe.log`（失败保留）、`legacy-probe-second.log`、`legacy-contract-comparison.json` |
| `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/tui_gateway/test_file_attachment_compatibility.py -q` | 缺参数/取消隔离/失败清理补充后1次，runner4.1s/外层5.22s，29pass | `compatibility-final.log` |
| `.venv/bin/python …/scoped_checks.py`；实调私有index下 `.venv/bin/python scripts/check --staged --base 24510d1c7c3b8dfc95b6d0626be30f090561fa30 --only ruff,health,os-marker-fakes` | 首次4.208s，4个宽except缺traceback导致health阻断；补debug traceback后1次4.642s，3检查全部pass、health 0阻断/0提示。未改变任何规则、阈值、等级或豁免 | `scoped-checks-first.{log,json}`、`scoped-checks.{log,json}`；脚本精确owned文件/私有tree已记录 |
| `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/tui_gateway/test_file_attachment_chunks.py tests/tui_gateway/test_file_attachment_compatibility.py tests/tui_gateway/test_tui_gateway_server.py -k '(not test_tui_gateway_server or file_attach)' -q` | traceback薄修后仅受影响包1次，runner4.4s/外层5.81s，48pass（12+29+7） | `after-health-fix.log` |
| `git diff --check -- <本owner文件>` | 最终通过；只检查附件源码、测试、生成物、manifest/report | 交接前执行 |

**当前有效distinct后端用例59项**：chunk12、allocation4、compatibility29、cold-attach6、generated-current1、legacy7；重复运行不再加计。初包47不是最终完整版本独立计数；最终48与另外11的有效证据按实际机制影响合并复用。`test_catalog_covers_the_whole_wire` 未跑，此前review.summary孤立事件失败原状保留，不能以本包生成一致性通过称其关闭。

旧合同对照执行历史提交的真实handler AST与真实Pydantic classes（没有重写镜像handler），通过同一正式dispatcher与现行原生stage owner运行；只比较原合同要求，对路径中的隔离owner前缀作规范化。证明bare/data URL/local-path结果、4015/5028及6种额外键4000一致；没有把此受控对照说成旧版本整仓真实服务。两输入源码SHA与原提交记录在comparison JSON。

新RPC定向机制覆盖：formal dispatcher注册/合同、非零未知起始offset、latest ACK精确重放/错误payload/错序、重复并发片不重复bytes、500000000声明边界和额外1byte拒绝、同名独占、同UUID跨runtime隔离、profile/workspace-storage与remote cwd权限、metadata无目录/状态/Agent-build副作用、abort与在途chunk同锁、partial取消后非零续片拒绝、已完成晚ACK/重试不撤销或重复文件、write失败只清自己temporary。

容量底层复用 `.hermes-dev/round2-evidence/attachment-budget/{single-500MB-proof,pair-500MB-and-cancel-proof,cancel-final-proof}.json`：实际源/落盘SHA与真实DeepSeek terminal读取。单500MB SHA `3bb68020b349b7006065e8d8218a1c1e8a34824e05d5f68d98f13cce61f6bf18`；同名两250MB SHA分别 `433f5df8845deca44ad859520a3010f3ba115a589030e9bcaa155ef59750151d`、`41fad0103aaa299914b0c648e2086d7f110dde42dccaf0ebf5b2d5c968965fa2`。这些证明未改append/allocation/read接缝的容量，不证明新RPC已经在运行Web端接好。

## 5. 未覆盖与实质缺口

- **前端暂未修改**。原前端/current修复树的>4MiB分片、abort和hydrate仍调用旧file.attach增量；新后台若先加载到用户服务，现前端大文件/历史stat会4000失败。因此Main须先统一接线再安全更新服务，不能提前重启用户53445。
- **正式新名上传→submit→真实Agent读取尚未取得**。本包证明新方法正式dispatcher+落盘+权限+锁，而未把其自动称为完整Web/模型成功。用户最新顺序要求与任务不得操作用户runtime的边界下，待Main采用隔离服务代表链补证；这是V-R2-01关闭依赖。
- 尚未运行前端新名测试、typecheck/build、浏览器真实Cancel晚ACK，或独立Verification复审/Validation。本包取消竞态/晚ACK为正式后端机制受控证据，不冒充真实断网浏览器过程。
- restart/crash丢runtime upload状态、可能留partial的既有V1限制未改；没有新增持久续传、跨崩溃cleanup或completed文件撤销承诺。真remote环境与其它host平台未实测。

## 6. 前端精确接线建议与接口影响

在用户确认研究阶段完成、Main释放前端施工后，仅 `src/api/attachments.ts` 及专属test即可完成本项端口切换，无需改Controller/Composer业务owner：

1. ≤4MiB `gateway.request("file.attach", {session_id,name,data_url})` 完全保留。
2. 大文件两个分片request（正常与IndeterminateError精确重试）从file.attach改file.upload_chunk；params保`session_id,name,data_url,upload_id,offset,total_bytes`。
3. finally未complete的清理改 `gateway.request("file.upload_abort", {session_id,upload_id})`，删除`abort_upload:true`；保原cancelled/complete/lateACK过滤，不新增session.interrupt。
4. hydrate改 `gateway.request("file.attachment_info", {session_id,path})`，删除`metadata_only:true`；保真实size与未知保留引用语义。
5. `attachments.test.ts` mock对正常与重试应断言method新名、abort只有该上传两字段、stat只有session/path；小附件原方法原参数断言继续有效。不得仅忽略_method使方法误接也通过。

generated RpcMethods已导出新Params/Result。上述新客户端需要具备新方法的后端；旧Hermes客户端只用file.attach原合同继续兼容。旧本轮前端非法扩展调用须随该整改一并升级，不能以它拒绝4000为由重新放宽旧合同。

## 7. Main后续动作与可复用命令

先亲审3源码、生成合同、两测试与manifest；不得复跑有效59例作为review替代。完成前端研究后释放本项端口切换，再集中实际接线/验收。

建议**新隔离profile/服务**代表链，沿原PM与原生DeepSeek/provider（配置由Main从已授权本地运行环境准备，凭据仅ignored；本任务未复制或启动）：

```bash
HERMES_HOME="$PWD/.hermes-dev/round2-verification/attachment-rpc-fix/live-profile" \
  .venv/bin/python -m hermes_cli.main dashboard --host 127.0.0.1 --port 53449 --no-open --isolated --skip-build
```

明确避开用户53445/5173。通过已切新名的修复前端或正式WS client，在该隔离runtime执行下列**真实**链路并保存合同/事件/持久tool/result：

- 创建一个新session；用 `crypto.randomUUID()` 标识上传4MiB+96bytes的测试binary，首尾设可识别marker；仅两次 `file.upload_chunk`（offset0与4194304，total4194400），ACK要验证received_bytes及仅最后attached/ref；本地源SHA与实际stored path SHA一致。
- 对最终path调用 `file.attachment_info`，验证真实4194400且不新增/stage文件；同runtime `prompt.submit_idle {session_id,text:<下面任务加最终ref_text>,image_paths:[]}`，按现 `contracts/submit_idle.py` 合同，不添加其未声明的操作ID，不猜stored/runtime映射。
- 模型任务：“这是V-R2-01新RPC代表验收。请用原生terminal执行Python，只对所附bin做os.stat、读取前64bytes及seek末尾64bytes，返回精确大小与首尾marker；不读取整文件，不访问其它文件/记忆/Notebook，不派生Agent。”保真实tool调用、exit0、末回复及DB source，而不以ACK当模型读取成功。
- 同隔离runtime另建partial upload，调用 `file.upload_abort`；验证metadata/目录里无未完成引用、该取消marker无新user行/Turn，现Main/Pending不变。真实Web取消另按原Controller事务测试覆盖晚ACK与草稿恢复。

修复前端定向命令：`npm test -- src/api/attachments.test.ts`、`npm run typecheck`，以及实际改动所需一次最终build；后续回归由Main按集成影响选择，不重复500MB大包。新真实链补证、Main review接收并统一快照后，仍须按整轮规格执行新独立Verification/Validation；本报告不自行关闭发现。
