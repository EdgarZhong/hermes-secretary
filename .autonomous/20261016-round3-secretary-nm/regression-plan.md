# 最终回归静态清单（尚未授权执行）

## 1. 范围、状态与版本

本清单已完成静态路径核对、分组和有效证据索引；**最终回归仍为 NOT_RUN**。本次收口没有运行pytest收集、测试、checks、模型或产品，没有改production／现有测试或round3。真实公共运行已完整交回，round3由主会话交个人owner接力；待Verification派出后，由主会话明确最终回归SHA、执行owner和start，本文件不授予运行权限。

源码对照基线 `a51fd99abc783f245ab855526a10862f2c89656a`；需求 `d19018a7ba3e38ae01f76aa57821b55cbc15ff58`；本次静态锁定调查HEAD为 `f66a8f80b4bab39b0a785a552019c91a6e9becba`。ignored目录 `.hermes-dev/round3-local-20261017-l0/final-regression-prep/` 保存 `manifest.json` 的实际调查HEAD、136文件SHA256和精确分组；`build_manifest.py`／`finalize_evidence.py`只读取源码路径、AST、报告和证据指纹／写静态清单，不导入产品或测试模块，不收集或执行测试。最终待测SHA尚为空，不能把当前调查HEAD写成已经通过。

## 2. 原生接缝增量回归

准确待审文件清单为ignored `public-native-files.txt`，每行一文件，**136文件、零重复**。对应分组文件也在同目录。均已静态确认文件存在，未按关键字把初始候选整批纳入。

| 分组／文件数 | 受影响正式接缝 | 回归重点及准确清单 |
|---|---|---|
| loop / 12 | run_agent→turn_context/preflight→turn_api_call→conversation_loop | 普通Main、实际响应/空响应/错误、取消、恢复、迭代；loop.txt |
| persistence / 13 | session_persistence→append、turn_finalizer→completed/failed sync；Codex同通用gate | 增量user/tool/final行、失败回复、异步memory、boundary、既有Codex原生历史/live事件，不启动AppServer；persistence.txt |
| compaction / 29 | context_compaction_request、manual/auto/Idle、conversation_compression→真实原生提交 | native关闭、no-op/失败、租约/fence、持久边界、回复锚、媒体、rotation、取消、anti-thrash；compaction.txt |
| dispatch / 16 | tool_executor、inline、turn_tool_validation、cache parity、prompt构造 | 原生批次/顺序/中断/非法参数、工具写库、root/tools/prefix、构造与恢复；dispatch.txt |
| catalog / 5 | model_tools/toolsets→tool_search bridge scoped catalog | 原生工具注册、描述、动态能力/ContextVar目录、关闭隔离；catalog.txt |
| state / 19 | native append/replace/archive_and_compact、History读投影 | UID、批量事务/repair、watermark与租约、原文/compacted可见、profile及Secretary基础身份；state.txt |
| cli / 11 | 既有CLI oneshot/resume/manual compress与配置验证 | 普通关闭场景、原生/部分压缩、完成与恢复、slash registry、配置validator；cli.txt |
| tui / 18 | session create/resume/control、persist、history、compression与queue | inline图、busy压缩、恢复、history fence、配置profile、重启/排队；tui.txt |
| gateway / 13 | run_agent_cache、正式compression/turn/lease/profile owner | cache owner释放、busy/profile、持久历史、不完整Turn、压缩失败/取消/并发、Secretary slash；gateway.txt |

补充一个**过滤执行的文件** `tests/tui_gateway/test_tui_gateway_server.py`：不加入136全文件列表，另用ignored `tui-server-selection.txt` 的 `-k` 表达式，准确函数清单 `tui-server-remaining-nodes.txt`、来源行号／接缝理由见 `tui-server-selection.json`。静态选择84个测试函数（参数展开数量尚未collect，不宣称84个参数场景），均含正式prompt.submit或`_run_prompt_submit`／`_commit_turn_history`调用、观测或pipeline patch；覆盖普通history version匹配提交、错误/空回复、图片persist、truncation/rewind、interrupt、notification归属等原生行为。没有把该大文件645项整组重跑，也没有遗漏变更过的核心提交路径。

F08已有效的三个函数精确排除：`test_prompt_submit_history_version_mismatch_surfaces_warning`、`test_prompt_submit_merges_on_model_switch_marker`、`test_prompt_submit_merges_on_personality_pivot_marker`。最终command单独传此文件＋`-k`表达式，不能在公开136文件批次再放整个server文件。`test_restore_alternation_repair.py`三项原证据也明确记录，但F12随后改变同原生repair接缝，保留一次受影响回归是版本变化后的复证；不宣称所有计划项绝无历史重跑。

上述包含 `test_prompt_cache_prefix_contract.py`、`test_append_messages_batch.py`、`test_compression_watermark_commit.py`、`test_manual_compress_history_fence.py` 等原生邻域，避免只测试Secretary helper。初始 `agent-candidates.txt`仍为历史调查候选，不是执行列表；未受影响的模型路由/provider专项、Anthropic/Bedrock缓存、平台伪造及功能无关组未纳入。`test_web_compaction_control.py`是后台原生控制，已由C9-H有效证据复用；不能因名称含web误作本轮新增UI。

## 3. 已有证据复用与修复新鲜度

准确复用文件对照 `reuse-files.json`（64个文件范围）；这是报告与实际日志的索引，不是重新宣称单次运行的计数。各包最终有效并集及失败后定向证据见对应报告；按受影响源码和修复范围判断新鲜度，不能仅因HEAD变化全量重跑，也不能仅因测试文件未改忽略机制变化。

| 证据来源 | 已有效范围／数量 | 本轮复用边界与后继 |
|---|---|---|
| C1/C5 | r3_notebook93、r3_child34；c5-report与L-A/c5 | Notebook结构/版本、同步base、持久child、四工具、五Turn/overflow；F12修改后只用owner定向补证更新受影响prefix边界，原七类型保障不重跑 |
| C2/C10-A | History/Notebook/child旧组233；c10-notebook-history-report与L-A/c10-a | 原文/Identity/候选/branch/rewind、旧保障；F08/F08b/F12实际影响的模型投影和prefix按修复报告补node，不全重跑 |
| C3/C6 | Scheduler47＋Delivery30；c6-report与L-B/c6 | table/claim/单carrier/事务ACK/crash边界；正式caller另见C9-S，不以helper代替 |
| C4 | config/prompt38；c4-report与L-C/c4 | 嵌套配置、失败关闭、英文常量、slash；新修复没有改变配置语义，不重复整组 |
| C7/C10-H | runtime/joint/timers63、五旧组62，Idle修复另4受影响node；c7及c10-runtime报告 | interval、D01、single deadline、资源/关闭；F11/F13对应原失败必须由owner定向补证，不能用旧成功覆盖新缺陷 |
| C8 | 新/旧Framework59；c8-report | 同事务pointer、完整Snapshot、阈值、队列/锁/回滚；无变化部分复用 |
| C9-H | host45＋原生请求36＋后台控制19＋sync/finalizer12=112独立场景；response gate23节点定向复测 | 正式manual/auto、真实response ACK、completed/failed；F11用新修复报告替换受影响boundary证据，不重跑112 |
| C9-S | wiring/surface/hosts/dispatch/Gateway/TUI112；F09新增有效node并集6 | 原生bridge目录缺陷必须结合43a38089e4后的实际反证修复结果；原批次权限等未变部分复用 |
| C10-B | 十旧投递文件106；c10-delivery-report | 九个CLI/TUI/Gateway真实SIGKILL边界、native carrier/部分batchACK；非UI；C6/C9-S同版有效旧组不重跑 |
| F11/F12最终补证 | 最终78独立节点，62→74→78；cache_parity11、thinking_only_sanitizer20、replay_cleanup6全文件均为其子集；新增boundary_prefix与host/state定向节点；c9-host-report及f11-f12/manifest.json | cache_parity从136移除，其余已有效文件不另加；f66a8旧Anchor追加4新节点、复证6个实际受影响节点，最终anchor-green为10 PASS，不把多轮runner PASS累计作独立数量。原生loop/turn_context未跑邻域仍在136，restore_alternation留作同repair接缝改变后的受影响复证。 |
| F08/F08b | concurrent_feedback10＋旧TUI server3＋restore_alternation3＋display_projection12；slash-feedback-report／slash-feedback/manifest.json，4739b54896 | 新并发文件和display文件整体复用；旧server只复用3个准确函数。restore文件因F12随后修改同repair接缝留在136的受影响回归，不称零重复。deferred_model_history并无F08运行证据，现补入TUI分组 |
| C10-T/F10/F13 | 六旧文件90＋独立human/model投影1＋Framework完整正文1＝92独立PASS；c10-final-legacy-report及c10-t/manifest.json，pending_nodes=[] | 主会话已review完整接收；初次60PASS/17FAIL/10setupERROR仅保留历史。manifest现转completed_owner_scope，六旧文件归reuse，不在最终批次重复；F10六个正式caller受控节点及F11修后四个Force节点的node_evidence保留，F13实际人类/model边界另有真实模型正证。 |
| C10-P | personal/security两旧文件39；c10-personal-report | 已canonical通过，复用，不重复 |

真实模型本轮的七类型、受限实际USER成功结算、同一原生Turn五请求图片parity、四触发入口与独立开关见 real-model-report.md；F08/F09/F11/F12/F13定向实测及跨原生Turn continuation、Scheduler余链均已完整交回。真实API证据不能代替原生离线可靠性回归，离线回归也不能声称真实模型通过。F10–F13及最后F12旧Anchor修复均已集成f66a8；F10 owner-race采用已接收的正式caller受控证据，不虚构额外真实模型race。后续若生产再改变，主会话再核对实际受影响node更新新鲜度。

### 最终证据指纹与适用范围

准确来源为 `evidence-reuse-manifest.json`，其SHA256由主manifest引用。它固定三份来源报告、C10-T与F11/F12 owner manifest、21个当前源码/测试指纹，以及下表真实补证文件。C10-T报告指纹与其manifest相等；F11/F12使用 `anchor_review.report_sha256`，不采用前阶段报告指纹。

F11/F12最终源码指纹按 `files → replay_review.final_sha256 → anchor_review.final_sha256` 的覆盖顺序解析，避免把中间replay版本误当f66a8终版。最后Anchor回修基准是eff3235，集成于f66a8，仅三路径；patch `anchor-review-delta.patch` SHA256为 `3a2d5afc89530e34c14b96be97076315ea86ce9d1660124387297628272443b8`。三条最终指纹已静态核对：

| Anchor回修路径 | 最终SHA256 |
|---|---|
| agent/cache_parity.py | e91d3d50a46e4deb3c6d630522a6b7b15fb9e699db92f23bcc411049cc44e40b |
| secretary/noting_child.py | 3b45312321a1ef97c84c2a3bc24648d18255b53636d6776c3ba6cc89c9a7cc50 |
| tests/secretary/test_r3_boundary_prefix_regression.py | bb418418acc4f71614cd94c51c6ac17aa2ac6cad2c9f6a56f1fe9aeb8b25a584 |

该回修覆盖preflight Force时DB Anchor早于当前未持久user，以及current索引为None／完整source末尾／越界三个无current模式；正式Parent请求、延迟worker及持久child五Turn完整prefix对比均沿原生机制。F11两个boundary owner文件在replay与Anchor回修中均未变，原有效边界证据复用，不重跑。`agent/turn_context.py`的replay回修指纹保留于owner manifest；其未运行原生邻域仍由136清单覆盖。

| 已收尾真实范围 | 适用版本 | ignored real-model/证据 |
|---|---|---|
| F08 streaming图片＋slash、child六请求完整prefix；F08b cold Main回复可见／human_only不入请求 | eff3235 | f08-repair-prefix-evidence.json；f08b-cold-request-evidence.json |
| F09原生bridge登记与local/global Noting off独立；两deferred一carrier双ACK；idle instant；busy只pending→下一Main ACK | eff3235 | scheduler-register-two-response.json；scheduler-deferred-after-response.json；scheduler-global-off-row.json；scheduler-idle-wake-events.json；scheduler-busy-lifecycle-evidence.json |
| F11真实成功native边界、新Force区间与换Anchor不重复 | eff3235 | f11-repair-boundary-force-evidence.json；f11-refill-1-state.json；f11-refill-2-state.json |
| F12首user尾七请求；同child跨5原生Turn，两probe共31请求完整prefix/root/tools/图片相等、最多4次continuation、forced合法Snapshot及资源释放 | f66a8 | f12-user-tail-prefix-repair-evidence.json；native-continuation-cross-turn-prefix-evidence.json；native-continuation2-cross-turn-prefix-evidence.json；final-product-state-before-stop.json |
| F13人类/notebook不含内部Snapshot/anchor头，模型show保留完整envelope | eff3235 | f13-human-notebook.json；f13-model-show-response.json |
| Scheduler真实host重启registry不变、合成未来排期清理、原生host退出0及profile释放 | f66a8 | scheduler-restart-after.json；handoff-runtime-stop.json；process-release-evidence.json |

两个跨Turn probe只有任务Prompt受控，实际DeepSeek未配合特定“首纯文本第二finish”形态，最终真实五Turnforced；不将它们冒称正常finish或CLI用户自然语义验收。正常standalone finish采用已有效正式自然链。初始f304b42七类型、结算、图片五请求与Idle时序仍按原版本保留，不为收口再运行。

## 4. Provider canonical补证

额外计划**仅两R3文件、46项**：独立个人仓 `nowledge-mem-hermes/personal_tests/test_r3_provider.py`（31）与`test_r3_thread.py`（15），精确源路径列在ignored `provider-canonical-files.txt`。先前是unittest受控HTTP fixture结果（personal-report.md），没有canonical runner证据，因此此次允许补证；不能误把39旧项重复加入。

插件目录含连字符，直接pytest源码路径曾导致整文件setup失败；最终owner应沿C10-P已验证方法，在个人仓ignored `temp-r3-personal/evidence/final-regression-runner/` 建**指向这两源文件的symlink**，不复制源码、不新增conftest、不修改包。canonical runner从个人仓执行，`HERMES_PYTHON=/Users/edgar/code/hermes-secretary/.venv/bin/python /Users/edgar/code/hermes-secretary/scripts/run_tests.sh <两symlink绝对路径> -q --tb=short --show-capture=no`。此处只列计划，没有创建symlink或运行；`__file__.resolve()`应仍指真实源码，以保持现有fixture ROOT。受控本地HTTP fixture不访问真实NM，不写用户真实profile；实际个人host→fixture证据另见personal-host-report，不混作真实NM通过。

## 5. 最终执行契约（等待主会话授权）

最终owner记录：明确SHA、clean/允许dirty状态、源码及锁hash、环境、开始/结束、每批耗时、完整参数、退出码、PASS/FAIL/skip/setupERROR，日志入ignored最终证据目录。静态manifest `execution_authorized=false`且final_sha_owner为空，当前不能执行。

公开tests计划由Python读取`public-native-files.txt`成list，原样传给既有runner（不拼shell字符串）：`subprocess.run(['scripts/run_tests.sh', *files, '-q', '--tb=short', '--show-capture=no'], env={..., 'HERMES_PYTHON':官方.venv绝对路径, 'HERMES_TEST_FILE_RETRIES':'0'})`。可按9组顺序分日志以定位失败，但同一文件只跑一次；不要在组完成后又跑public合并列表。大型TUI server补充命令单独为同canonical runner＋`tests/tui_gateway/test_tui_gateway_server.py -k <tui-server-selection.txt完整表达式> -q --tb=short --show-capture=no`，精确排除上述3个已有效函数。setupERROR、runner自动summary遗漏等必须看原始pytest结果；失败修复后仅定向失败／实际受影响节点，不自行重开136文件。

保留检查固定10类，最终批准SHA一次命令：

```bash
.venv/bin/python scripts/check --commit <批准完整SHA> --base a51fd99abc783f245ab855526a10862f2c89656a --only footguns,shebangs,no-tmp,config-writers,os-marker-fakes,case-collisions,lazy-deps,profile-archives,ruff,health
```

不使用漂移origin/main，不修改规则／阈值／严重级别。ignored `rule-source-audit.json`已有25规则入口指纹，至原调查HEAD均未变；官方`d02f211858ab202d6d4d34ea59774591a5f14cbd`唯一差异是已授权移除agents-md文档长度入口。最终owner只刷新实际SHA和相同规则指纹，不新增门禁。

## 6. 排除范围与交接

Web读DTO、UI、Settings展示、旧Dashboard、独立UI仓构建均按07明确后置；不新增JS/UI测试或发布步骤。真实NM、官方CLI通用编辑/管理写入、云部署未授权，不纳回归。当前macOS不能冒称其它OS通过，不伪造sys.platform。

静态清单与现有证据收口完成，但没有最终回归执行或验收结论。下一步：Verification派出→主会话指定最终回归owner/SHA/start；如其后生产变化，仅按实际影响定向更新证据。准确范围仍是136全文件＋一个server文件的84函数过滤＋个人两R3文件46项，彼此不重复；个人旧39项不重跑。`execution_authorized=false`、`final_sha_owner=null`保持不变，没有因本文件列出范围而扩大运行授权。

## 7. 最终回归真实执行记录（2026-10-17 START）

主会话已派出全新Astra/high Verification，并明确授权本Agent作为唯一最终回归owner。此START覆盖上方静态编制时点的NOT_RUN／未授权状态；静态scope快照仍保留原值，实际执行授权与结果单独记录在ignored `final-regression/execution-manifest.json`，`execution_authorized=true`。

- 固定公共待测SHA：`323c64dacba1190c16bacc69bbe5e76db6f43529`，生产与f66a8相同。
- 固定个人待测SHA：`e1af6cc45ffbd53c930d1d2f14ab46858e966ecd`，生产与8682相同。
- 检查固定base：`a51fd99abc783f245ab855526a10862f2c89656a`。
- 官方PM `.venv`／显式HERMES_PYTHON，`HERMES_TEST_FILE_RETRIES=0`；Python测试全部经canonical runner。136文件九组顺序各一次，server过滤组、Provider两symlink文件及十类check各一次；完成组不再合并重跑。
- 状态：**FIRST_FULL_RUN_COMPLETE_WITH_FAILURES，已停止执行**。12次调用全部结束；各组各一次，未进行修复或重跑。每组args、源码前后指纹、lockhash、开始/结束、wall秒、EXIT、每文件PASS/FAIL/skip/error与失败node完整留证；原始失败和setup/collection error均保留。
- 未启动实际产品／模型，未操作round3或真实NM；不改production、tests、规则、核心文档，不stage/commit。工作区主会话已有CLAUDE.md动态修改已保留。


### 7.1 范围、版本与正式入口

本包落实本计划§2–6及主会话本次明确START，不承担独立Verification/Validation判定。公开136全文件与review清单逐项相等且无重复；另一个server文件按84函数表达式筛选，实际参数展开90项，原已有效3函数未入表达式。个人两个R3源文件以源码symlink从canonical runner运行，31＋15＝46 PASS，原39项未重复。共139个文件调用、11次测试runner调用、1次十类check调用。

开始 `2026-10-16T18:46:44.442494+00:00`，结束 `2026-10-16T18:51:57.818831+00:00`（时间采用执行manifest UTC原值）；各命令wall合计311.402秒。实际结束时间以manifest `finished_at`精确值为准。Python为官方PM工作区3.14.7；`HERMES_PYTHON=/Users/edgar/code/hermes-secretary/.venv/bin/python`、`HERMES_TEST_FILE_RETRIES=0`。每次测试调用均为 `scripts/run_tests.sh <精确列表/过滤> -q --tb=short --show-capture=no`；runner自身每文件隔离、10 workers，组间顺序运行。完整argv、cwd、开始结束、源码前后检查和日志hash见 `final-regression/execution-manifest.json`，不以此简写代替参数原证据。

`uv.lock` SHA256：`2bc4db483e9cba927cd7147f9ccbb09635f85bb3f1f36d6e9d51d06b65d1c67e`；`pyproject.toml`：`cadde2f6a92574d292103f43abf66408b1d841cd9ea332ca7f3e3dfc5dcc87fd`；review范围manifest：`bad7b9c98e1b9f66bde85432380f89512615dc0f714f81bdd30251499e26fd19`。各组执行前后源码／锁均匹配固定SHA；已有主会话CLAUDE与Verification报告变更保留。25个规则来源指纹静态核对仍与review版本一致，只有既授权文档长度入口排除，不改变规则、阈值或严重级别。

### 7.2 首轮结果（不可写成已通过）

| 顺序／组 | 文件数 | PASS | FAIL | skip | setup ERROR | EXIT | wall秒 |
|---|---:|---:|---:|---:|---:|---:|---:|
| loop | 12 | 391 | 5 | 0 | 0 | 1 | 77.923 |
| persistence | 13 | 72 | 0 | 0 | 0 | 0 | 19.050 |
| compaction | 29 | 241 | 6 | 0 | 0 | 1 | 33.098 |
| dispatch | 16 | 291 | 0 | 2 | 0 | 0 | 48.797 |
| catalog | 5 | 114 | 0 | 0 | 0 | 0 | 3.549 |
| state | 19 | 235 | 18 | 0 | 0 | 1 | 34.155 |
| cli | 11 | 63 | 0 | 1 | 0 | 0 | 6.327 |
| tui | 18 | 171 | 0 | 0 | 0 | 0 | 60.843 |
| gateway | 13 | 52 | 0 | 0 | 4 | 1 | 3.780 |
| tui-server84 | 1 | 90 | 0 | 0 | 0 | 0 | 7.708 |
| provider46 | 2 | 46 | 0 | 0 | 0 | 0 | 3.165 |
| **测试合计** | **139** | **1766** | **29** | **3** | **4** | **非全绿** | **298.395** |
| 十类check | — | 8类通过 | 2类阻断 | — | — | 1 | 13.007 |

无collection error、teardown error或解释器崩溃。Gateway一个文件4项均为setup error，主体未运行；runner将该文件列入“no tests ran”，不能因摘要只显示FAIL=0而判通过。3 skip来自prompt_builder的非macOS大小写场景，以及tool_batch_segmentation和chat_q_exit_clear各一Windows场景；此处skip节点/原因按静态platform marker定位，原runner仅有每文件数量，不冒称取得跨平台证据。

统计解析的最初regex把时长`1.8s`的小数部分误读为8 skip。首轮结束后只解析原日志补了token边界；PASS、FAIL、error完全未变。初版manifest与各文件初始observed单独保留，原日志hash不变，未为统计重跑测试。修正过程脚本见 `summarize_first_run.py`；最终3 skip与原runner Summary相等。

### 7.3 失败、缺口与精确接力

完整33个失败/错误node、phase、日志和初步归类见ignored `final-regression/failure-triage.json`及同名Markdown，不省略参数node。以下归类是原日志＋静态代码的修复输入，不能据此声明生产行为已通过：

| 类别 | 数量 | 真实失败事实／建议边界 |
|---|---:|---|
| Loop旧执行名断言 | 5 FAIL | test_run_agent三项和reasoning_only_stop_persistence两项仍断言session_history存在；不得恢复退休名alias。后两项尚未进入reasoning主要行为断言，应以现行工具契约保留原断言目标 |
| ACP可选依赖 | 1 FAIL | conversation_compression_manual的[acp]分支导入acp_adapter.commands时报ModuleNotFoundError: acp；先查官方PM依赖组/锁，不裸装、不加skip |
| 原生压缩夹具与Noting通知 | 5 FAIL | in_place_compaction四项见额外Noting失败Framework或persist多调用；persist_marker一项active5!=期望4，日志未展开第五行内容，须owner定向核对，不能提前冒称已证同一通知原因 |
| Snapshot夹具缺audit | 15 FAIL | secretary_lifecycle八项及secretary_migration_lineage七项，在notebook_commit_snapshot夹具阶段缺termination audit抛NotebookError；原身份/分支/原生回滚/重启主体保障仍需按现行契约恢复测试 |
| History旧调用契约 | 3 FAIL | secretary_foundation：search结果无messages、read success为false、注册目录无session_history；保留跨压缩UID/原文、parent scope与身份边界目标，改用现行接口 |
| Notebook夹具缺Anchor | 4 setup ERROR | gateway/test_secretary_slash.py routed:24未传NotebookStore必需keyword-only anchor_message_uid；四个主体未执行 |

十类check固定base与commit、单次执行exit1：footguns、shebangs、config-writers、os-marker-fakes、case-collisions、lazy-deps、profile-archives、ruff八类通过；`no-tmp`命中 `.autonomous/20261016-round3-secretary-nm/personal-report.md:64` 的否定事实语句，`health`命中 `tools/scheduler_tool.py:62 scheduler_available` 的BLE001（blind except Exception）。主会话已接收：前者由root按事实改述，后者交实现owner补合理诊断或精确异常处理，不修改检查器、不追加豁免。

### 7.4 实际变更、接口影响与下一步

本包tracked仅更新本文件真实执行节；ignored新增执行编排、日志、初版及校正后manifest、33-node归类、规则指纹与证据索引；个人ignored目录只新建两源码symlink。没有production/tests/规则/核心文档修改，无stage/commit；没有实际产品、模型、round3或NM操作。没有产品接口变化；本包交付的是可共享、不可覆盖首轮失败的回归证据。

主会话及Astra共享本首轮结果，下一步只针对明确失败和实际受影响路径分配修复/定向复证，不重新运行136文件、server90、Provider46或十类全集。主会话另发现Notebook输出微秒的问题及其修复影响由主会话统一安排，不纳入本包擅自改动。当前首轮里程碑已完整交回，整体仍有29 FAIL、4 setup ERROR、2检查阻断，不能据1766 PASS或既有真实模型证据宣称最终回归／独立验收通过。本Agent停止执行与写入，等待主会话后续指令。

### 7.4 首批定向修复接收

主会话已亲自review六旧测试路径，原27失败／setup错误＋2实际影响邻域有效并集29 PASS，完整映射见c10-final-legacy-report.md §8。其余压缩6节点仍未关闭，不能宣称回归全绿。公共V51输出投影另有17项有效定向证据，见c9-host-report末节；个人Recall与Scheduler run_at追加出口仍待修。

两检查窄修：personal-report的否定事实语句改述；scheduler_available原fail-closed异常支路补debug诊断，不改规则／阈值／严重等级。主会话执行`python scripts/check --staged --only no-tmp,health`均通过；因默认health对照为c099c8c49084，仅采用其中no-tmp结果，随后显式`--staged --base a51fd99abc783f245ab855526a10862f2c89656a --only health`通过，121文件0 blocking／0 advisory、8.3秒。此为失败检查的定向修复复验，没有重跑十类全集或136文件。
