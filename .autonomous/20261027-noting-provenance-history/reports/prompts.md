# Prompt 实现包交接

## 1. 对应条款

冻结提交 `02d55fdb45b4fb7c883fb477f4469912f4707f70`，分支 `codex/noting-provenance-history-20261027`；覆盖 plan P、C02–03、C18–20 和主会话派遣的已审 A–I 英文文案。已完整读取 executing-plans、autonomous-run 交接契约、本轮索引／基线／计划、根 AGENTS／CLAUDE、07 顶部新节及保留的 description／生命周期／结束／父子缓存段；agent/AGENTS 仅作参考。

## 2. 实际变更

- `secretary/noting_prompts.py`：精确替换父上下文说明、真实对话取证优先级、必要时才改 description、History 模式选择、已有条目双类分流和 Task 同槽来源、精确 UID／普通属性覆盖、Candidate 来源二选一、Schedule 建议。第2步保留稳定 entry_id、同情景原位更新、有意义旧条件、不同主题另建、新内容不继承旧批准和重读不刷新进展的原意。
- `agent/system_prompt.py`：仅替换 HISTORY_SEARCH_GUIDANCE 原首个检索句为已审两句；Conversation 定义、来源身份、证据安全与 session_search 边界保持。
- 新 `tests/secretary/test_noting_history_tuning_prompt.py`：真实 Main 构造与后续请求、真实 Noting 初始／续 Turn／finish 提交测试；SDK 回复受控，不调用真实模型。Profile terminal.cwd 和 TERMINAL_CWD 均在测试临时目录，仓库外。
- 主会话追加白名单后，更新 `tests/secretary/test_noting_r20_prompt.py`：仅将已撤销的时间范围／旧来源文案期待改为 Task 来源链与精确 UID；保留原位同情景、旧 done／字段保留、过时归档、新主题另建、旧 Snapshot 不变及完整父子 Prompt 断言。为保留原 R20 稳定句，Task 尾句沿用原始同情景原位更新文字。该测试亦显式使用库外 terminal.cwd。
- 未改 Schema、History handler、核心文档、NOTING_CONTINUATION_INSTRUCTION／CURRENT_NOTING_CONTROL，也未提交／push／部署。

## 3. 正式接线与保留

Main `_build_system_prompt` → 原生 `run_conversation` → 请求边界实际 root 包含新的 History 指引；开关关闭／开启均验证，暖态第二次请求 root 保持一致。

`run_noting_task` → `build_noting_child` → `_working_control` → 原生两 Turn → `finish_noting` → runner Snapshot 提交。测试查看真实请求中的完整 Task、control JSON、续 Turn、完整冻结父 messages／tools 和最终持久化 finish 工具回执；六工具仍在固定顶层 tools，任务没有 Schema 副本。

补充静态差异核对：相对冻结基线，当前 control／continuation 常量逐字不变；第3步与第4步、七类型生命周期表、Candidate 目标表至第6步之前的保留部分、第7步 finish 指导逐字不变（Candidate 来源句按本轮明确授权替换）。无“current interval／previous interval”术语教学，无额外预览免责声明。

## 4. 验证、版本和原始日志

执行方：Prompt Agent；PM `.venv` 软链复用 `/Users/edgar/code/hermes-secretary/.venv`，Python 3.14.7；未改依赖或锁。产品 HEAD 仍为冻结基线，运行包含当前白名单未提交差异和其它实现 Agent 的并行变更。

1. 初版测试（空 Notebook，3项）：`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/secretary/test_noting_history_tuning_prompt.py -q`，3 passed，3.0秒。原始日志 `.hermes-dev/noting-chain-20261027/review-evidence/prompts-tests.log`。
2. 补强已有条目保持场景后，定向回归：`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/secretary/test_noting_history_tuning_prompt.py tests/secretary/test_fixed_noting_request.py tests/secretary/test_noting_finish_exit.py -q`，31 passed／1 failed，14.5秒。fixed request 7项与 finish exit 22项通过；新增2个 Main 用例通过。已有条目创建失败于并行 Notebook 接线中间态：新 `notebook_model` 已不输出 `source_message_identities`，当时 `notebook_store.py:167` 仍读取它；未绕开该机制或改白名单外文件。原始日志 `.hermes-dev/noting-chain-20261027/review-evidence/prompts-regression.log`。

3. Notebook Agent 通知产品接线稳定后最终定向验证：`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/secretary/test_noting_history_tuning_prompt.py tests/secretary/test_noting_r20_prompt.py tests/secretary/test_fixed_noting_request.py tests/secretary/test_noting_finish_exit.py -q`，4文件33项全部通过，18.3秒（子进程总计39.0秒，10 workers）。新增3项、R20 1项、固定请求7项、finish exit 22项。原始日志 `.hermes-dev/noting-chain-20261027/review-evidence/prompts-final-tests.log`。已有条目无改动通过两 Turn/control 和最终 payload 深比较；R20 保持同条目ID／原 done／未改属性，旧 Task 来源节点与时间未动，新 Task 追加一组新 UID，正常归档无价值临时条目且另建不同主题。

最终本包四个文件 `git diff --check` 通过；未为运行 checker 而修改共享 index，冻结 staged 质量门禁由主会话统一执行。初版失败日志保留，不能抹成全部运行均一次成功。

## 5. 缺口

- 先前并行中间态失败已由 Notebook 包收敛解决，最终33项通过覆盖；未改白名单外实现来绕过该失败。
- 真实模型遵循行为、真实 API 父子缓存／工具协议由主会话统一取证；受控 SDK 测试只证明组装、正式执行和提交，不证明模型自然选择。
- 原 R20 测试已按主会话追加白名单更新并定向通过，未为迁就旧断言回退新规格。
- 未运行大型套件／全仓质量门禁，无生产数据、UI 或部署验证声明。

## 6. 接口影响

无新增 Python 接口或参数；沿既有 Task／Main 指引常量消费点生效。Schema 由 History／Notebook Agent 管理；Task 使用批准的用户语义“Get Meta”，不重抄 get_meta／include_auxiliary 的 Schema。Notebook 编辑输入维持 source_message_uids 一维本 Task 槽位，模型对外 provenance 二维及 runtime evidence_time 契约依 Notebook 包提供；本包不更改这些实现。

## 7. 后续

主会话亲审 A–I 差异和保留尾句，复用本包最终33项有效证据；统一真实模型样本／父子 prefix 证据，并执行冻结 staged 质量检查。通过独立 Verification／Validation 后再按授权统一提交／发布。本包不派生、不提交、不 push。

## 追加修复：Schedule 建议独立编辑（真实模型失败驱动）

1. **条款与失败依据：** C03 既定语义要求“稍后处理”未明确推迟时正文／状态保持，只在有登记缺口时补建议。已核主会话真实模型样本 `.hermes-dev/noting-chain-20261027/e2e/live/result.json` 和 `notebook-1.json`：旧税表 description 为“税表尚未提交，等待用户决定。”，当前用户仅说“税表稍后处理”。模型正确补了 Schedule 建议，却重写 description 为“税表尚未提交；用户说稍后处理，未指定具体时点。”；result 标记 ok=false，并在 fields 不变断言失败。该真实失败保留，不能用受控 SDK 测试冒称模型已修好。采购18盒／原条件和无关条目的正确结果不受本次修复扩大。
2. **实际变更：** 仅在 Task 第2步原 `check Schedule suggestions separately.` 后追加：`If only a Schedule suggestion is needed, edit only schedule_suggestion and its supporting provenance; keep every other attribute unchanged.` 这是用户既定边界的最小明确化，无新产品决定；其它已审文案、结尾、生命周期及 control／continuation 不改。
3. **正式接线：** 新断言仍检查原生 Main→Noting 两 Turn 实际请求中的 Task，要求新增句只出现一次，且位于第2步 Schedule 分流句之后；保持原父子 tools／messages、control、finish／持久提交验证。无源码字符串断言替代正式构建。
4. **验证与日志：** 同冻结 HEAD `02d55fdb45b4fb7c883fb477f4469912f4707f70` 加当前未提交差异；同 PM Python 3.14.7，无依赖变化。执行 `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/secretary/test_noting_history_tuning_prompt.py tests/secretary/test_noting_r20_prompt.py tests/secretary/test_fixed_noting_request.py -q`：3文件11项全部通过，6.4秒，原日志 `.hermes-dev/noting-chain-20261027/review-evidence/prompts-schedule-only-tests.log`；本次两改动文件 diff-check 通过。未跑大型套件、真实模型或生产。
5. **缺口：** 本次测试证明新增指令经正式构建到达模型并保留已有机制，不能证明模型自然遵循；待主会话重跑既有真实合成场景验税表正文／状态不变且建议存在。
6. **接口影响：** 无接口／Schema／来源结构变更；仅明确已有 schedule_suggestion 及其本 Task 来源的编辑范围。
7. **后续：** 主会话亲审单句与正式构建断言后，统一真实模型复验和独立门禁。本人不派生、不提交、不 push、不部署；原失败与新日志均保留。

## 再次定点修复：直接约束“稍后处理”及真实来源参数

1. **条款／两次失败保留：** 仍仅落实 C03、C05 及原已审的正文保持和 Task 来源槽位语义。已核第一次 `.hermes-dev/noting-chain-20261027/e2e/failed-schedule-description/{result,notebook-1}.json` 为 ok=false，税表正文被改为“税表尚未提交；用户说稍后处理，未指定具体时点。”。已核第二次当时位于 `e2e/live/{result,notebook-1}.json` 也为 ok=false，正文被改为“税表尚未提交；用户在2026-10-27表示稍后处理，未给出具体时间，等待用户决定何时处理。”。主会话已确认第二次实际 wire 包含此前新增句且 fields 非必填，仍未遵循正文保持要求；来源数组也出现把旧、新 UID 一并作为本次提交数组的概念混淆。第二次样本将由主会话改名保留为 `failed-schedule-description-clarified`，本人未移动／覆盖样本。
2. **实际变更：** Task 第2步原 Assistant／Reminder／later 长句与 only-Schedule 条件替换为直接指令：`An Assistant prompt, a due Reminder or no response does not establish a content or state change. When the user only says “handle it later” / “稍后处理” without explicit postponement, keep description, done and every other ordinary attribute unchanged; if a Schedule registration is missing, edit only schedule_suggestion and its supporting source_message_uids.` 同段每次编辑句使用真实参数：`On every edit, submit the attribute changes and source_message_uids for this task’s complete flat UID array together.` 后面的覆盖／保留旧 Task 节点／跨 Turn 同槽文案保持。无新增步骤、长免责声明、Schema 或产品语义。
3. **正式接线：** 新测试继续检查原生 Main→Noting 两 Turn 的实际 Task，要求这两处文字出现一次，并定位“稍后处理”指令在第2步；R20 仅同步来源文案构建期待。未修改任何行为测试期望、税表不变判据、场景范围、清退／finish 或 runtime 接线。
4. **定向验证：** `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/secretary/test_noting_history_tuning_prompt.py tests/secretary/test_noting_r20_prompt.py tests/secretary/test_fixed_noting_request.py -q`：3文件11项通过，6.8秒，Python／环境同前，无安装或锁变更。日志 `.hermes-dev/noting-chain-20261027/review-evidence/prompts-schedule-direct-tests.log`；本次3改动文件 diff-check 通过。
5. **证据边界与型号纠正：** 两次失败确为真实 API 调用，但旧 harness 强制使用 `kimi-for-coding` 别名；主会话随后直接核正式配置及当前置顶 session.model 均为 `k3.1-pro`。因此两次失败只能作为旧别名样本证据，不能等同当前生产型号的问题。主会话已纠正 harness 为 `k3.1-pro`，待按线上实际型号重验本次新指令。两次失败均保留，不以构建测试通过宣称最新模型已遵循；本人未调用模型或生产。
6. **接口影响：** 无接口变更；只在 Prompt 中明确既有 `source_message_uids` 参数承载本 Task 完整一维数组，而非提交整条 provenance 历史链。
7. **交接：** 代码和定向验证已稳定，交回主会话 review／真实样本复验。不派生、不提交、不 push、不部署。
