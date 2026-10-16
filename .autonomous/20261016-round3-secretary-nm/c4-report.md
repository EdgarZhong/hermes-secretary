# C4 配置、Main Prompt 与原生命令交回

状态：C4 白名单实现与定向验证完成，待主会话 review。未提交、未切分支、未派生；停止本域写入。运行时跨域接线及独立门禁不在本报告内冒称完成。

## 1. 对应条款

- 权威冻结：`d19018a7ba3e38ae01f76aa57821b55cbc15ff58`；白板 C7/C8/C9、L1/L4/L6/L9、F1/F2、N1/N2/N5/N6、P6。
- 07 §6.3：独立 Scheduler 配置；Noting Idle 默认关闭、双参数与校验；Proposal 默认 12000/60；退休配置明确报替代位置且不迁移；原生 idle-return-compaction 互斥。
- 07 §8.2～8.10：Main 模块门禁、英文定案常量、窄 Session Search 覆写、私有 Cron Schema/manifest/Search、共用 Proposal。
- 01 §1/4/7 与 04 §3.1～3.5 的适用继承：Hermes-first、公开隔离、原生 stable 构造/恢复接缝、真实 Main 资格、配置切换同步与 local 开关不重建 root。新版覆盖的旧 Prompt/Memo/Notebook 排期语义未保留。

## 2. 实际变更与文件清单

修改仅以下 9 个白名单文件：

1. `secretary/noting_policy.py`：新扁平 immutable settings；独立两功能解析/读取；失败关闭和具体修法；有限非负 Idle delay、开启必需正整数 threshold、正整数 Proposal 阈值；退休 key 报错；删除特殊 profile 常量与 `idle_task_profile`，Force 原生测量及整数余量公式保留。
2. `secretary/noting_scope.py`：新增数据库 owner profile 的 Scheduler 配置读取，原 Noting scope 保留。
3. `hermes_cli/config_defaults.py`：按 07 嵌套默认值替换旧块。
4. `hermes_cli/config_validation.py`：正式 `_validate_noting` 钩子统一调用两功能各自 parser；错误有功能名称及修法，不修改另一功能。
5. `agent/system_prompt.py`：原位新 Role/History/Notebook/Time；Scheduler 独立能力字段且实际 tool 可用才注入；Main Session Search 窄覆写，非 Main 原生文案保留。
6. `agent/secretary_prompt.py`：Cron description/schedule note 定案；scope 改为 Scheduler Main 资格且实际 tool 可用；继续只复制当前 agent Schema，保留原生 global Schema。
7. `agent/prompt_builder.py`：替换本地 Cron 旧 Notebook 排期附言为新的 Scheduler 定案 note。
8. `hermes_cli/cli_secretary_commands.py`：slash 配置绑定 DB owner profile；配置失败返回具体修法；`/noting off` 仅 local 写入无 Memo 阻断；新共用 Proposal 常量；提案附当前完整 Snapshot（含 source 引用所需内容），不预检索 History、不访问目标、不批准写入；空候选仍由 Main 按共用指令解释是否有合适提案。
9. `tests/secretary/test_r3_config_prompt.py`：本任务唯一独占测试文件，共 38 个参数展开场景。

未改核心文档、plan、规格、noting_surface、dispatch、child、Framework、Schema 事务、依赖锁或个人 Provider。

## 3. 正式路径与权限边界

- 正式 `hermes_cli.config.validate_config_structure → _validate_noting` 已接两 parser；`load_config_readonly → resolve_* → owning_db_scope/settings_for_db/scheduler_settings_for_db` 保持 profile 归属。
- 正式 `system_prompt._guidance_parts → _tool_guidance_block/platform_hint` 实施 Main 文案与能力门禁；`cron_schema_scope → apply_scoped_cron_schema_guidance/apply_scoped_cron_search_guidance` 使用同一同步 Scheduler 能力。
- 各客户端既有 slash adapter 仍调用 `notebook_command/noting_command/propose_persistence_command`；local 仅调用 durable `db.notebook_set_local_enabled`，没有 root 或 Schema rebuild。
- 正式 Main 资格、Schema/dispatch 同步、冷/热恢复由 C9 的既有接缝落实。本报告没有用 SimpleNamespace 的提示模块测试冒称正式模型请求接线通过。

## 4. 定向测试与证据版本

- 环境：macOS 26.7 arm64，PM `.venv` Python 3.14.7 / pytest 9.1.1；canonical runner 清凭据，测试自动 HOME/HERMES_HOME 隔离；没有模型或真实 NM 调用。
- 运行命令基础：`HERMES_PYTHON="$PWD/.venv/bin/python" HERMES_TEST_FILE_RETRIES=0 scripts/run_tests.sh tests/secretary/test_r3_config_prompt.py -q`。
- 首次执行原 32 场景：31 PASS、1 FAIL（测试夹具遗漏新版 `NotebookStore.commit(termination=...)`，不是产品失败），0.8 秒。修正夹具后 `-k slash_off`：1 PASS，0.5 秒。
- slash profile 与错误修法调整、新增场景后，`-k 'slash or unreadable_profile or platform_cron'`：4 PASS，0.5 秒。
- 补齐无穷/NaN 原生 idle 配置失败关闭后，`-k 'malformed_native_idle or native_idle_conflict'`：4 PASS，0.4 秒。
- 上述结果并集覆盖当前 38 个独立场景；没有为汇总重跑已经有效的其余场景。未单独持久化最初两次完整日志，对话工具输出保留其原始结果；后两次日志已落盘。
- 英文核对：07 §8.3～8.10 的 8 块及 §8.9 schedule note，共 9 个导出常量与原文逐字一致。
- 隔离 `GIT_INDEX_FILE`，真实仓库 index 未改。`scripts/check --staged --base HEAD --only health`：9 个 C4 文件，0 blocking、0 advisory，0.8 秒；`scripts/check --staged --only ruff` 最终版本通过。`git diff --check` 通过。
- 首次默认 base 的组合检查还发现已集成 C2 `tools/session_history_tool.py:248 _search` nesting 7>6，已向主会话报告，未越权修复。该全范围 health 结论为 FAIL，不能被 C4 的局部通过覆盖。
- 精确文件/依赖 SHA256、patch hash、交回 HEAD、测试执行历史：`.hermes-dev/round3-local-20261017-l0/L-C/c4/manifest.json`。日志同目录：`check.log`（含 C2 全范围失败）、`c4-health.log`、`c4-ruff.log`、`slash-profile-tests.log`、`idle-invalid-tests.log`；`c4.patch` 保存本域 tracked dirty diff，新测试由单文件 SHA256 固定。
- 初次 31 场景在 C1 集成后的代码上执行；后续 C2/C3 合并不涉及本任务已测实现。交回 HEAD 以 manifest 为准，本域仍为 dirty patch，不伪称已有 C4 commit。

## 5. 缺口与旧用例处置

- 旧 `secretary/noting_runtime.py` 仍 import `idle_task_profile`，并读 `auto_compact_after_force_noting_idle`、`auto_trigger_compaction_threshold_tokens`。这些旧接口已删除，C7 必须替换为新联合流程；当前在 C7 完成前导入此旧 runtime 会失败，不能投入使用。
- C9 仍需接通实际 Scheduler config、Main Schema/dispatch、恢复 root 检查和 gateway cache signature；本次仅提供所需接口及原有 Prompt 接缝，不越权改 noting_surface。
- C8 尚需从唯一 Proposal 常量追加超限尾部，并消费同一 settings 的两个阈值；本任务未检验 Framework pointer 一致性或计数。
- 真实模型、原生冷/热恢复、全局开关实际请求、全量门禁未执行，留给所属接线任务/最终验证，不重复已完成的 C4 小范围测试。
- 遗留 `test_noting_policy.py/test_noting_runtime.py/test_noting_timers.py/test_noting_busy_idle.py/test_noting_surface.py/test_noting_config_contract.py` 等仍使用旧字段/配置/工具名；按新 07 更新，不保留旧执行 alias。未运行或改动这些其他任务所属测试。

## 6. 公开接口精确签名与刷新时机

```python
NotingSettings(
    enabled: bool = True,
    idle_enabled: bool = False,
    idle_delay_seconds: float = 500.0,
    idle_threshold_tokens: Optional[int] = None,
    persistence_proposal_char_threshold: int = 12000,
    persistence_proposal_entry_threshold: int = 60,
    configuration_failure: str = "",
)
SchedulerSettings(enabled: bool = True, configuration_failure: str = "")
noting_settings_from_config(config: Any) -> NotingSettings
scheduler_settings_from_config(config: Any) -> SchedulerSettings
resolve_noting_settings() -> NotingSettings
resolve_scheduler_settings() -> SchedulerSettings
settings_for_db(db) -> NotingSettings
scheduler_settings_for_db(db) -> SchedulerSettings
```

- config 外部结构严格仍为 `noting.idle.{enabled,delay_seconds,threshold_tokens}`、`noting.persistence_proposal.{char_threshold,entry_threshold}`、`scheduler.enabled`，内部扁平 dataclass 是实现组织。
- `TASK_PROFILE_NOTING='NOTING'` 保留；`TASK_PROFILE_NOTING_WITH_COMPACTION` 和 `idle_task_profile` 删除，无旧配置 alias。
- `force_thresholds/measurement_from_agent/effective_noting_enabled/idle_due` 原签名与 Force 算法保留。`idle_due` 只做 Main 时间条件；C7 再检查 `idle_enabled`、真实 `measurement.measured_tokens >= idle_threshold_tokens` 并调用联合入口。
- C9 应在允许的构造/恢复/Pre-message Context 同步点设置 `_secretary_main_read_eligible`、`_secretary_notebook_read_enabled`、新增 `_secretary_scheduler_enabled`。真实 `valid_tool_names` 必须同时匹配；不要每 Turn 重建未变化 root，也不要 local toggle 重建 root。
- `synchronize_main_read_prompt`（C9 owner）现仅检测 History/Notebook 旧条件，必须增加 `SCHEDULER_GUIDANCE` 计数/实际状态，以及新 Session Search 覆写，防止 Scheduler 全局切换只变 Schema 不变 root；更新 gateway cache-busting signature 的 `scheduler.enabled`，坏配置使用解析结果，不能只测 raw truthiness。
- `apply_cron_schema_guidance(tools, *, enabled)`、`cron_schema_scope(agent)` 原签名保留。C9 在原来把 Notebook enabled 传入此函数的位置，改传独立 Scheduler enabled；工具面同步完成后再捕获请求 root/tools。
- C8 共用指令唯一入口：`from hermes_cli.cli_secretary_commands import PERSISTENCE_PROPOSAL_INSTRUCTION`；常量严格 07 §8.10，不复制字面值。
- 公开英文常量：`agent.system_prompt.{HISTORY_SEARCH_GUIDANCE, SECRETARY_ROLE_GUIDANCE, NOTEBOOK_GUIDANCE, SECRETARY_TIME_GUIDANCE, SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE, SCHEDULER_GUIDANCE, SECRETARY_SESSION_SEARCH_GUIDANCE}`；原 HISTORY/SECRETARY_WORK 常量名保持可导入。

## 7. 建议后续动作

1. 主会话 review 后接 C7，删除上述 runtime 旧接口消费者；C5 不再选择 special profile，C8 消费阈值/唯一 Proposal 常量。
2. C9 正式统一三能力、scope、恢复与全局开关的请求同步；接线新增行为测试由该 owner 执行，复用 C4 38 场景证据。
3. 指派 C2 owner 修复嵌套健康指标；最终统一门禁保留原规则，不以本域健康通过掩盖其他文件阻断。
