# T4b Usage 只读投影实施与交回

本任务依据冻结 `37ad76f5dfac02d4774d5e0faea55911b5fb8de9`：06 §0、§1.13、§2.8–2.9、§3、§4.5–4.7；02 §1、§5.2–5.5、§5.9–5.11、§6.1–6.3、§6.6–6.7、§6.11–6.16、Final invariants。一级规格不改。

## 精确 DTO 里程碑

- 方法 `session.usage_detail`；Params `{session_id: string, profile?: string|null}`。
- Result `{session_id, stored_session_id: string|null, session_total, latest_completed_turn: CompletedTurnUsage|null, latest_turn_availability, observed_at}`。
- `session_total`：`input_tokens/cache_read_tokens/output_tokens: int|null`，`cache_hit_rate: float|null`（0–1），`turns: int|null`，`availability: available|partial|unknown`，`source: native_canonical_accounting|unknown`，`scope: session`，`reasons: UsageReason[]`。
- `CompletedTurnUsage`：上述 token/cache/availability/source/reasons；`turn_id: string`，`model_calls: int|null`，`model_calls_source: native_model_dispatch|unknown`，`scope: completed_main_turn`，`completed_at: ISO UTC string`。没有 Session Turns 字段。
- `UsageReason`：`owner_unavailable|hosted_owner_unavailable|restored_session_totals_unknown|overlapping_turns|failed_dispatch|missing_usage|incomplete_usage_fields|incompatible_cache_semantics|opaque_moa_calls|opaque_external_dispatch|unobserved_dispatch|unaccounted_response|turn_exception|unobserved_iteration_summary`。
- 旧 `session.usage` 及所有旧 event 字段完全不改。前端收到原生实际 completion 后重新读取；不新增事件 socket 或浏览器持久响应缓存。

## 来源与 unknown 契约

`input_tokens` 是 Hermes canonical 非缓存输入；canonical prompt=input+cache_read+cache_write。只有原始 usage 的字段能证明 native buckets 含义时，cache rate 才以 `cache_read/(input+cache_read)` 算。0/0 为 null；MiniMax 原生已声明缓存计数不可靠，ratio 为 null。

完整性不足的相关计数直接 null，不能把已知部分显示成完整总量。无usage、失败dispatch、响应被validation丢弃、middleware短路响应无实际dispatch均显示相应partial/unknown；不补入原生未记录usage。model_calls只数真正native streaming/nonstreaming dispatch，不使用预算退款后的 finalizer api_calls、assistant/tool rows。SDK内部HTTP retries不可观测，这个数字明确是 native model dispatch 次数；MoA advisor或external facade opaque时为null，绝不伪装provider HTTP调用数。

Session计数仅基于从无历史真实开始连续观察的runtime，包含进行中已记录canonical usage及真正结束的driving Turns。在途不替换latest。恢复Session存在旧history时，Session Total和Turns返回unknown/null，不扫描user rows推Turns、不累计差分、不新建durable账本；恢复后的真实新Turn仍可显示Latest。物理Session旋转/重置不把旧计数冒充新Session。

## Owner、注册与生命周期接缝

RPC调用原生 `_sess_nowait` 和 `_profile_scoped`。stale session 4001，显式profile不匹配4001，unknown keys由原dispatcher 4000；profile不存在保留原生4064。hosted/compute owner不读parent代理冒充child，返回`hosted_owner_unavailable`。读取不构造Agent、不写DB、不建立owner、不触发Noting/Reminder/压缩。

Main注册：导入 `tui_gateway.contracts.usage_read`，调用 `tui_gateway.methods_usage_read.register(server)`，按原流程生成共享TS/OpenRPC。新DTO代码为唯一精确字段来源。

已批准小观察接缝：`turn_api_call.perform_api_call` 的原生preflight/Reminder verify之后，分别包围真实stream dispatch和relay回调内的nonstream dispatch；middleware未调用dispatch则不数。`turn_usage.record_response_usage` 只在既有canonical会计点和no-usage分支委托观察，不改变旧会计。

Main另已亲读批准并已串行接入 `turn_finalizer._resolve_budget_fallback` 的真实 `_handle_max_iterations` 调用前唯一`note_unobserved_main_summary`委托。此路径本身无canonical记录，且summary可能0–2次，不猜次数，相关token/model_calls为null并标`unobserved_iteration_summary`；pending verification直接复用分支不做该标记。不深入修改summary/provider。

T3a完整交回并由Main明确释放后，已串行接入：`turn_context.build_turn_context` 在`_bind_turn_identity`后调用 `begin_main_turn_usage(agent, turn_id, has_prior_history=bool(conversation_history))`；`turn_context.export_current_turn_boundary` 的原early returns之前，按匹配active owner/current turn调用 `finish_main_turn_usage(agent, turn_id, result)`。此原生统一出口覆盖绕过finalizer的retry耗尽等失败envelope。真正raise且无result时，`prompt_turn._invoke_agent` finally委托`abandon_main_turn_usage`；unknown、不伪造success、不改变ticker stop/join或异常传播。无finalizer重复finish hook，不改prompt_turn旧completion字段，保留T3a全部pending生命周期与settlement接线。

## 已取得的独立模块证据

- 2026-10-12，官方PM `.venv` / canonical runner，`tests/agent/test_usage_read.py`：7项通过，约0.5秒；覆盖无owner读取、Noting/aux排除、canonical前丢弃响应、cache缺字段、Session边界、MoA unknown、exception与幂等结束。
- `tests/agent/test_usage_native_compaction.py`、`tests/secretary/test_usage_noting_isolation.py`：2项通过，约2.1秒。前者运行真实compression facade及DB发布（仅summary外部返回受控），不会记为Main调用；后者真实持久Noting child Loop与SessionDB，child canonical计数200 input / 30 output、1 call，Parent Main投影无变化。日志 `.hermes-dev/round2-evidence/usage/isolation-tests.log`。
- 当前本任务9个Python文件定向Ruff通过；针对相同9文件调用原生health Measurer/compare（冻结基线37ad76f5df、不改规则/阈值/豁免）0 blocking/0 advisory。第一次health识别fixture别名与本地同名fixture为F811，已改为pytest原生fixture插件复用后定向复查通过，日志 `.hermes-dev/round2-evidence/usage/targeted-health.log`。未运行全量门禁。
- 上述为接缝前历史证据。最终接缝与仓库内隔离库证据见下文；历史失败及日志保留，不用后续PASS抹掉。

## 七项最终交回

### 1. 任务对应条款

06 §0的原生owner/只读/薄客户端、不改变旧契约；§1.13真实Session Total与已结束Turn、canonical cache语义、真实model dispatch计数；§2.8–2.9仅已证明缺口的最小增量与精确mini-contract；§3原生映射；§4.5–4.7正式路径/回归证据。02 §1的Main/Session/Turn边界，§5.2–5.5 child隔离与prefix，§5.9–5.11压缩/并发/prefix，§6适用接线/原生不变/Noting隔离与Final invariants。无持久Turn账本、浏览器缓存、provider适配、API hierarchy或规格修改。

### 2. 实际变更与版本

源码快照 `HEAD=8e7ba807f8f4f827f947e5e4184f46173d80cfd2` 加本任务工作区变更；子Agent未stage/commit。12个Python文件：`agent/usage_read.py`、`turn_usage.py`、`turn_api_call.py`、已释放的`turn_context.py`、`turn_finalizer.py`、`tui_gateway/prompt_turn.py`、`methods_usage_read.py`、`contracts/usage_read.py`，以及4个独立测试文件（agent usage_read/native_compaction、tui_gateway usage_native_turn、secretary usage_noting_isolation）。本报告是唯一新增过程文档。共享server/catalog/生成产物由Main注册；未碰前端、根文档、一级规格、锁文件、运行服务。

源码SHA256完整清单：`.hermes-dev/round2-evidence/usage/final-source-manifest.json`，含12个Python源码、02/06权威原文及uv.lock。核心projection `agent/usage_read.py` SHA256=`626282f61caa86d9e25682c121c7b2bac04bfc5c45c558c23039dc2e0eb390c3`。此manifest记录测试时真实版本；Main如后续改共享文件须区分其版本，不把本报告当新版本已验证。

### 3. 正式调用路径

新RPC真实注册dispatch→原生Session/profile owner→只读projection。`prompt.submit`→原生deferred admission/worker→Main `run_conversation`→真实prologue开始→实际stream/nonstream dispatcher逐尝试观察→既有`record_response_usage` canonical会计观察→统一native返回出口freeze→原生`message.complete`→前端重读。failed retry/exhaustion/fallback进入原生错误/路由机制，不替换Loop；预算退款不会删掉已经观察到的真实dispatch。真正未返回异常通过Gateway finally标unknown。整个projection不改旧结果、原生计数、transcript、Root/tools/schema、Reminder ACK与pending settlement。

### 4. 验证结果

最终已通过 **23 distinct，4 files，0 failed，11.8秒，单worker**。命令：

```bash
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh -j1 \
  tests/agent/test_usage_read.py tests/tui_gateway/test_usage_native_turn.py \
  tests/agent/test_usage_native_compaction.py tests/secretary/test_usage_noting_isolation.py \
  --basetemp="$PWD/.hermes-dev/round2-evidence/usage/final-runtime"
```

日志 `.hermes-dev/round2-evidence/usage/final-tests.log`；真实测试DB全部在该仓库ignored basetemp。14个Gateway/正式Main用例覆盖stream/nonstream两call累计、旧usage响应完全一致、连续Turn/在途latest不替换、无usage不伪装总量、cold user+steer历史不推Turns、middleware短路unknown、实际failed retry、retry耗尽early result、真实native fallback config+路由/预算退款、budget summary unknown与preserved verification分支、真实未捕获prologue异常、RPC读取前后DB/history/counters不变、profile mismatch/hosted/stale/未知参数。7个边界用例及真实compression/持久Noting child隔离2例也通过。

原生socket connect/connect_ex门禁保留，全部14个Main用例最终没有网络尝试。控制点仅模型response/stream返回、fallback客户端构造与外部context/定价metadata；native Loop、fallback config同步/路由切换、canonical/pricing逻辑、SessionDB与read dispatch真实运行。fallback真实dispatch=2而native退款后result api_calls=1；该Turn缺失败尝试usage所以token为null。

最终12文件定向Ruff通过（`final-ruff.log`）；采用原生health Measurer/compare，仅本任务12文件相对冻结基线，**0 blocking / 0 advisory**（`final-targeted-health.log`）；diff whitespace检查通过。未运行全量suite或旧T3a109。

首次Loop测试错误等待deferred worker（13 fail）、函数名与fallback源配置（修正后12 pass / 2 fail）、fallback附带定价metadata网络门禁（断言通过但teardown error）均保留原日志。准确栈为native usage pricing→模块级导入`agent.usage_pricing.fetch_endpoint_model_metadata`→httpx happy-eyeballs connect_ex，六次均被原门禁阻断，未真正发送provider流量。按Main读栈确认仅控制此准确外部依赖返回`{}`，保留`get_pricing_entry/estimate_usage_cost/canonical`真实运行；诊断wrapper已删。首次用默认 `/private/var/tmp` 不满足项目运行库位置约定，已按Main明确授权为纠正位置将本阶段23 distinct合并重验一次，最终基准为仓库内证据。完整诊断历史见usage目录，最终PASS不掩盖旧失败。没有重复旧T3a门禁，也未修改规则或阈值。

### 5. 缺口与诚实边界

本任务实现/定向机制验证无未关闭失败。未执行真实模型、浏览器与正式WS运行服务重启联调；这些属Main/全轮后续验收。SDK内部HTTP重试不可观测，`native_model_dispatch`明确是Hermes实际dispatch次数；MoA advisor、external facade、无canonical的迭代summary均不伪装精确总量。cold Session全历史总量/Turns未知，而恢复后的真实Latest可显示；此契约不是待补durable ledger。压缩隔离证据运行真实facade/DB publication，summary外部返回受控；未把它当真实模型cache测量。Noting证据是真持久child Loop，不以标签helper代替。

### 6. 接口影响

新方法和DTO仅增量；old `session.usage`/old events、参数、响应与错误不变。profile mismatch4001、原生profile不存在4064、unknown params4000、cold/hosted source/availability/reasons明确。精确契约此前已交Main和前端；Main最终生成共享类型须包含新增`turn_exception`、`unobserved_iteration_summary` Literal。没有新增事件：实际completion后read；Session Total可在原生usage失效提示后按正确owner读取。

### 7. 建议后续动作

Main亲自review本报告与manifest/source，统一生成最终契约、阶段提交与后端重启，前端以native runtime owner做实际RPC/WS联调，检查23 distinct版本及生成一致性。复用有效定向结果，不重复旧109或本23；仅接线修改影响、真实失败或证据存疑时定向重验。范围内浏览器场景与真实模型cache/附件仍由本轮独立门禁与Validation完成。本任务三共享生命周期文件现已完整交回，不再修改，等待Main接收。
