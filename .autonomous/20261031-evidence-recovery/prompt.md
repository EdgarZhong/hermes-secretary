# D2 · Main回查与Noting证据组描述交接

状态：实施与定向机制验证完成，交主会话review；未执行真实模型或发布。实现者未提交、未改共享plan／核心文档／规格，无生产写入。

## 1. 对应条款

- 冻结索引E01／E02／E05／E07及07顶部2026-10-31 A/B定稿：证据描述与条目description互补，仅概括本组，描述／UID共同维护；Main按历史依赖MUST核实原文，已有可见充分原文免重复Read，先相关组Read、缺失再Meta／Search、无法恢复保留未知。
- 继承07 §8.2、§8.5、§8.11、§8.12及来源链口径；Notebook白板C3／C6／C7、K6、N1／N3的来源归属、Candidate两分支、真实认可范围、完整工作视图及完成通知不变。
- 沿现有资格、全局／local门禁、Main只读、Noting六工具权限及cache parity；不改compaction footer predicate、父历史、tools或Active前缀。

## 2. 实际变更

- `agent/system_prompt.py`：新增命名常量`MAIN_EVIDENCE_RECOVERY_GUIDANCE`，逐字包含顶部B的三个英文段落；原位纳入`HISTORY_SEARCH_GUIDANCE`。模式结果说明保持Get Meta头尾预览、Search定位、Read细节，以及范围／权限／provenance／证据非指令／禁止session_search回退等既有契约。
- 同文件Notebook指导原位去掉“index and visible dialogue sufficient即可不查／仅主观缺细节才查”的旧竞争句，统一指向Conversation and History核实依据；更新证据优先及其它Notebook／Candidate权限保持。
- `secretary/noting_prompts.py`：逐字加入顶部A英文定稿，补接`source_description`与`source_message_uids`同组提交、`provenance_descriptions`逐槽对应、旧组缺失不猜补、refs Candidate沿源条目读取；第2步的普通编辑及仅Schedule建议编辑同步描述字段。Noting原本按需取证策略、默认Get Meta、父规则作废、六工具、control及continuation不变。
- 新增`tests/secretary/test_evidence_recovery_prompt.py`。同步专属旧Prompt oracle：`test_noting_history_tuning_prompt.py`、`test_noting_r20_prompt.py`；R20两个模型写入样本补描述。经D1协调另接手`test_noting_request_protocol.py`的selector oracle：原脚本期待finish后的额外第4次模型请求，与既有成功finish立即结束不符；现在保留show→文字结束→续Turn finish三次请求及全部前缀／selector隔离断言。

## 3. 正式路径与全Prompt核查

- Main：真实`AIAgent`构造→`run_conversation`→`build_system_prompt_parts`／`_guidance_parts`→SDK实际JSON序列化。新指导只沿既有`_secretary_main_read_eligible`分支；History在eligible Main的Noting全局关闭时仍存在，Notebook／写工具继续受原全局门禁；local开关不改root／tools，四类非Main无新指导。
- 冷恢复：`secretary/noting_surface.py::synchronize_main_read_prompt`检查canonical整块，当持久旧root缺新指导时，在下一正常Main Turn边界调用原生builder，`record_cache_break(..., "toolset_change")`一次并持久化工具。第二个warm Turn原样复用；既有历史不改、工具Schema／pin保持。无需为这次Prompt更新另建热改入口，额外清生产root缓存并非生效所必需。
- Noting：`spawn_noting_task`／`run_noting_task`以默认Task追加到冻结父前缀，当前control编码工作视图，未finish的下一原生Turn追加原continuation＋新control。实际SDK请求验证A定稿仍只在初始Task一次，后续保留；父root／tools／Active逐项一致，拒绝非白名单scheduler后仍能show并finish。
- 实际完整Main根Prompt已人工阅读，覆盖真实项目AGENTS、自动加载Skill正文及索引、内置MEMORY／USER、memory／Skill工具指导、Conversation／Notebook／Scheduler、timestamp和runtime环境footer。未发现旧主观充分指引残留。Noting完整Task／control／续Turn和父规则作废均在实际请求中验证。样本内容为合成哨兵，terminal.cwd在Git root外。

## 4. 验证结果与版本／方法

环境：共享官方PM `.venv`（指向主仓），CPython 3.14.7／uv 0.12.3，macOS；锁文件未改。测试只用`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh ...`，TZ=UTC、干净凭据、真实OpenAI SDK JSON序列化经MockTransport受控返回。真实builder、权限dispatch、Noting Loop、SQLite及提交未替换。

产品HEAD与逐文件SHA保存于ignored证据根的`head.txt`／`source-sha256.txt`（记录时HEAD `0e4cc640b7bb4619f0e37c5d72e9678eb5e4c1ab`，叠加D1／D2未提交修改）。Prompt最终测试针对当前已集成数据接口；未把HEAD误作仅包含本包的提交。

证据根：`.hermes-dev/evidence-recovery-20261031/prompt/`。

| 范围 | 结果 | 次数／耗时 | 证据 |
|---|---|---|---|
| 专属完整Main／冷恢复／全局local／4种非Main／Noting拒绝续Turn | 8通过 | 有效初测5.3秒；D1集成后最终复测5.5秒 | `tests-prompt-final.log`；`pytest-final/test_full_main_prompt_and_cold0/{main-full-request,main-restored-request}.json`；`pytest-final/test_noting_exact_description_0/noting-initial-continuation-requests.json` |
| history tuning／R20／fixed request | 11通过 | 最终3文件5.8秒 | `tests-adjacent-final.log` |
| selector／关闭Noting原生context选择／overflow恢复 | 4通过 | 修oracle后2.5秒 | `tests-protocol.log` |
| lean压缩恢复／Main History与非Main原生footer | 10通过 | 1次1.3秒 | `tests-footer.log` |
| 固定权限整文件 | 86通过，复用D1有效证据 | D1执行85.5秒 | D1报告／日志，不再重复 |
| 本包diff whitespace | 通过 | 最终`git diff --check -- <本包六文件>` | 命令无输出／exit 0 |

无效运行保留：首轮多文件错误共用`--basetemp`，逐文件并行runner互删目录，造成FileExists／SQLite干扰，`tests-first.log`不作通过证据并已终止其进程；随后默认隔离的4文件试跑在权限文件旧样本缺描述时停止（前三文件各自已通过），`tests-adjacent.log`也不作为最终总结果。最终日志如上，未隐藏初次错误。完整检查由主会话按最终staged范围统一执行，本包不作未运行的lint／全量通过声明。

## 5. 缺口

- 未执行真实模型，不以脚本预置调用证明模型会按新指导先Read、及时停止、避免猜补或只概括本组；这部分由主会话集中模型样本及独立Validation承担。
- 未以macOS测试冒称真实Linux／生产验收；未发布、未清生产缓存、未改旧Notebook组。
- 数据持久链、Candidate direct／refs两来源及旧组兼容主要复用D1机制证据；本包验证Prompt真实投递及其边界。

## 6. 接口影响

- 与D1一次协调并使用其最终输入`source_description:string`＋`source_message_uids:UID[]`，投影`provenance_descriptions:(string|null)[]`逐槽对应原`provenance:UID[][]`。没有修改D1产品文件。
- Prompt新增描述义务仅针对建立／修订组，不要求旧组回填。refs Candidate明确没有直接组；来源时间仍是runtime只读，未把description用于派生。
- 没有新API／Provider／模型路由／工具定义变更逻辑；已有Main资格与正常恢复边界自动使新常量生效，飞行中的Noting保留其冻结版本。

## 7. 建议后续

- 主会话亲审这六个文件及D1正式接线后统一快照和冻结检查；使用本报告有效证据，按集成变化定向补证。
- 已阅读主会话`.hermes-dev/evidence-recovery-20261031/model/probe.py`：现有indexed、visible、no_index、correction、unavailable、noting覆盖主要分支。建议补一个History工具实际失败／不可定位后仍未知的真实模型场景；当前unavailable只有“事实原本未定”，尚不能证明工具失败后如实处理。另补普通即时且无历史依赖问题，验证不强迫检索。
- Noting真实样本人工核新组描述只含新UID消息、旧组不回写，且区分助手建议／用户接受／实际交付；脚本的“非空字符串”断言不能独自证明语义。可直接复用已有probe，不必另外建立模型执行器。
- 独立Verification／Validation及正常空闲发布由主会话统一推进。
