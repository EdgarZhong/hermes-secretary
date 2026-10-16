# R3-F08 / F08b：并行 slash 反馈与冷恢复

## 1. 对应条款

依据 d19018 冻结白板 N1（冻结父上下文输入）/N6（保持冻结父前缀），07 §3.1（89–104）、§8.1–8.2（1237–1265）、§8.11–8.12（1331–1378）。继承02 §2.1（272–284）实际Active、§2.6（599–619）Anchor；04 §2.3（111起）及§4.4（265–295）完整root/tools/messages、多模态，不从存储重拼；§4.6（317起）持久child。此次不改Prompt、cache parity、任务/模型机制。

## 2. 实际变更与根因

- **F08**：`tui_gateway/methods_secretary.py::_cmd_secretary` 在Main在途时，正式反馈已持久化后登记追加前基线、批次UID/消息副本和版本。原有`prompt_turn._commit_turn_history`只容忍pivot，并行反馈导致版本冲突，整份Main结果被拒收；因此durable原输入仍在，session Active却缺输入/图片。新增窄helper `_merge_secretary_feedback` 只验证正式owner登记的连续追加；保留完整原生结果（包括短压缩结果），同UID反馈去重，再按实际追加顺序保留feedback/pivot。任意未知内容变更、伪造/未登记反馈仍拒绝。成功后session和agent Active引用同步；空闲slash也同步Active。不忙等待，不拒绝busy，不改root。
- **F08b**：真实冷恢复反证确认，busy `/notebook` 的human_only assistant与稍后Main assistant相邻；model-fed原生alternation repair先合并，Main回复被human_only承载遮蔽。`hermes_state_messages.py::_rows_to_conversation`仅在`repair_alternation=True`先调用既有`model_visible_messages`再repair。无human_only时helper返回原list，原生行为不变；display projection、durable原文不改。该文件仍为2000行，增加两行接线并移除两行冗余注释，未增加控制流复杂度。
- `hermes_cli/cli_secretary_commands.py`只读核对，无需修改。

## 3. 正式路径与锁

F08：`prompt.submit`→原生AIAgent Loop/provider返回屏障；同时`slash.exec`→实际noting/notebook命令→native append batch→history_lock下登记并发布；Main原生返回后同一history_lock核验/合并并清理批次。反馈登记仅session内存，不新增存储字段，不给普通模型文本合并权限；在途不改agent正在使用的消息列表。DB写完成后才取history_lock，不在该锁内做DB写；没有DB→host反向嵌套。

F08b：`_load_resume_transcript`→`get_resume_conversations`→模型投影先visibility再repair；独立display投影保留human_only。测试将正式冷恢复的model_history交给新建原生AIAgent发出不同文本下一请求，确认第一轮Main回复可见、Notebook正文不入请求。不是镜像repair或直接拼凑预期结果。

## 4. 验证结果

基于 `e2fd9081a6a128d682ec1d59785ae600e0069c88`＋本包dirty patch，官方PM .venv / canonical runner，隔离临时库，不触碰round3、不调用真实模型。

最终有效 **28 PASS**：新文件10（3个正式busy RPC场景＋6合并边界＋1空闲发布）；旧冲突/pivot3；原生restore3＋display parity12。正式busy场景均从非空原生Main历史开始，附件用正式TUI staging，断言provider未返回时off/on即时生效、完整图片块、冻结前缀、下一请求、root不变、持久化标记、UID无重复、human_only可见性和冷恢复。

| 证据日志 | 结果 | runner秒 |
|---|---:|---:|
| before | 0P/3F；原history版本冲突复现 | 3.2 |
| after-first | 3P | 2.9 |
| expanded | 3P/5F；测试UID返回值/恢复投影假设需修正 | 4.3 |
| expanded-fixed | 7P/1F；human_only计数受repair影响 | 4.3 |
| expanded-final | 9P；随后增强不同响应反证 | 4.6 |
| cold-visibility | 2P/1F；排除第二轮同文遮蔽，实证F08b | 3.3 |
| complete | 最终9P | 5.0 |
| pivot-regression | 3P（仅-k指定3节点，非全文件645项） | 2.0 |
| restore-regression | 15P | 1.3 |
| preserved-prefix | 最终6个合并边界PASS；保留既有pivot原位置 | 2.6 |

共10次定向runner执行，累计runner wall 33.5秒；只有源码/断言变更、实际失败及新增边界后定向重测。最后一次修复仅收紧pivot差异合并，既有效pivot留在原位置；只定向复测6个合并边界，复用与其无关的Main/冷恢复/空闲及旧回归证据。最终命令和全部日志指纹见ignored manifest；`git diff --check`本包无空白错误。不运行保留check全集、完整Python或既有效C1–C10大组。

## 5. 缺口与保留边界

真实DeepSeek原失败序列尚由原owner定向复测：Main streaming中/noting查询、off/on，后续child第一实际请求必须含原输入和图片。本包验证freeze函数得到的实际Active前缀，未以其替代真实child请求/缓存命中证据。F08b为真实DB/原生冷恢复读取及新AIAgent实际provider请求的受控机制证据，未声称真实模型验收。未修改durable时间顺序、重建root或补写历史。

先前最终回归准备已保存并暂停；以下六文件在本包准备时未运行，之后已由独立C10-T owner执行并修复，不作为当前未运行清单：
- `tests/secretary/test_external_notice_v16.py`
- `tests/secretary/test_force_notice_compaction.py`
- `tests/secretary/test_timestamp_origin.py`
- `tests/secretary/test_usage_noting_isolation.py`
- `tests/hermes_cli/test_noting_config.py`
- `tests/hermes_cli/test_secretary_commands.py`

前两项需检查旧Idle夹具，CLI两项有退休配置/Notebook契约；不得恢复alias。Web旧DTO/UI仍明确后置。

## 6. 文件、证据与接口

源码manifest：`tui_gateway/methods_secretary.py`、`tui_gateway/prompt_turn.py`、`hermes_state_messages.py`；新增`tests/tui_gateway/test_secretary_concurrent_feedback.py`。无公开函数签名变更；仅新增私有session批次登记。源文件SHA256、锁指纹、日志、精确最终命令与patch在 `.hermes-dev/round3-local-20261017-l0/slash-feedback/manifest.json`、`final.patch`（已跟踪源码差异）及`test-source.py`（新测试完整快照）。原真实证据只读摘要来源：`real-model/concurrent-slash-active-observation.json`，未输出完整root或请求正文。

## 7. 后续动作

停止本包写入，交root review/集成，再由唯一真实owner重跑F08实际失败序列。最终回归manifest准备保持暂停；须待root明确恢复，且Verification启动后另行给start＋批准SHA才执行大型回归及固定base的十类检查。未stage/commit、未派生。

## Review 后补证

仅四路径固定Ruff通过；未修改的冻结 Measurer/compare/apply_allows/verdict 对 `e2fd9081a6a128d682ec1d59785ae600e0069c88` 的四路径增量结果为 **0 blocking / 0 advisory**，diff-check通过。执行脚本 `slash-feedback/check_scoped.py`、最终日志 `checks-final.log`、测量 `scoped-checks.json`；耗时 0.856秒。首次执行检查已通过但证据序列化Counter报错，仅修证据脚本后重执行一次，未复跑28有效测试。未执行大型或最终十类门禁。回归静态准备按主会话新指令继续暂停，转F11/F12。
