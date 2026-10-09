# V1.5 Cloud Resume — Verification

## 状态

**PENDING / 必须在本地独立执行。**

本文件不声明 Verification 通过。云端主会话通过 GitHub 连接器完成代码实施和静态 review，但没有可执行仓库工作树，也没有本流程要求的独立 reviewer/fork，因此不能替代 H6。

验证对象：从本轮基线 `70c772180d1bb2aaf8bba8d27a8a64f7c2fabb12` 到最新 `main`。核心产品代码候选在 `2a58d3e49e1f6303aaea853e3d724498bda1a535` 已收口；其后提交为过程/交接文档，除非后续本地修复再次改代码。

## 1. Requirement extraction

独立 reviewer 必须重新从以下权威来源提取要求，不以本文件的概括替代：

- `docs/02-noting-system-specification.md` 未被 V1.5 修订的契约；
- `docs/04-hermes-secretary-v1.5-implementation-spec.md` M01–M28；
- 历史索引 C05–C17；
- 本轮索引 R01–R05；
- 项目 `AGENTS.md` 的范围、规则和验收边界。

本轮新增重点至少覆盖：D01 最近实际 Main 执行来源；全生命周期冻结 Parent root/tools/messages prefix；Noting 后缀合法工具完整 Schema；双 Profile 最多 5 Turn；finish_noting/compact_parent 正常终止；forced Snapshot；termination 三态内部审计；synthetic wrapper/timestamp；终止工具参数契约。

## 2. Implementation and wiring matrix

至少逐项核对下列正式路径，而不是只看 helper：

| 要求 | 关键路径 |
|---|---|
| D01 actual dispatch | `agent/turn_api_call.py`、`agent/codex_runtime.py`、`secretary/noting_runtime.py` |
| Force/Idle no-side-effect reject | `secretary/noting_runtime.py` trigger/admission 与 parent compaction 分支 |
| frozen prefix / suffix declarations | `secretary/noting_child.py`、`secretary/noting_tools.py`、实际 request assembly/cache parity |
| dispatch isolation | `secretary/noting_child.py::noting_dispatch_block` 与两条 tool execution path |
| terminal tools / five-Turn | `secretary/noting_tools.py`、`secretary/noting_compact.py`、`secretary/noting_child.py` |
| Snapshot audit | `hermes_state_secretary_notebook.py` 迁移、commit、branch、normal/audit projection |
| carrier/timestamp | `agent/message_metadata.py` + Noting initial/continuation construction |

特别反证：
- External Idle 不得先触发 parent compaction/freeze/admission/reminder。
- 无真实 Main 模型请求不得清空/覆盖旧 D01 事实。
- fallback 到真正 native 执行后应以最后实际请求事实为准。
- Noting 首次、tool-loop、retry、continuation 均不得修改 Parent 顶层 tools/schema。
- continuation 必须仍是 `role=user` 的 `<noting-task>` carrier，使用原 admission source timestamp。
- finish_noting 只有必需 reason；compact_parent 必须零参数。
- 真 provider/task failure 不得伪装成 forced 完成；仅五 Turn 预算耗尽触发 forced。
- 特殊 Profile forced 时 native compaction 成败不改变 termination=forced，合法 Snapshot 仍走原 Commit Gate。
- 普通 notebook_show、/notebook、Main AI 不得看到 termination/reason。

## 3. Local executable evidence

先执行本轮最小受影响集：

```bash
export HERMES_HOME="$PWD/.hermes-dev"
export HERMES_PYTHON="$PWD/.venv/bin/python"
scripts/run_tests.sh \
  tests/secretary/test_noting_runtime.py \
  tests/secretary/test_noting_child.py \
  tests/hermes_state/test_secretary_notebook.py
```

随后按 diff 补跑实际受影响的 agent/cache-parity/turn lifecycle 测试，并按 `AGENTS.md` 统一安排本轮一次必要扩大回归与冻结检查。不得直接调用 pytest 绕过 runner；不得通过放宽规则、阈值或豁免使失败变绿。

每次记录：待测 commit、命令、通过/失败/跳过、耗时、失败归因和复测范围。旧版本测试数字不能自动算作当前 head 证据。

## 4. Native/cache evidence

使用用户已定案的 DeepSeek 官方 Anthropic / deepseek-flash 原生 Hermes 路径。至少捕获：

1. Parent 最后真实 Main request 的 actual execution source；
2. Noting first request；
3. 至少两个 tool-loop request；
4. same-child continuation；
5. Parent 并发新增 Turn/compaction 后的 child request；
6. 适用 retry 路径。

逐次比较完整 Parent root、原 tools/schema、截至 Anchor messages 的冻结 prefix；核对新增 Noting 工具声明只在后缀控制消息。单独记录 provider 返回的 cache-read/cache-hit tokens；字节一致不等同于真实缓存命中。

## 5. Independent verdict

独立 reviewer 在本节写：
- 覆盖矩阵；
- 发现的问题及严重度；
- 证据定位；
- 平台/环境未覆盖项；
- **PASS / FAIL**。

只要存在范围内违规、关键证据不足或当前 head 未实际验证，即不得 PASS。

## 6. Handoff rule

FAIL -> 回主会话/本地实现会话做最小定向修复，只复测失败项及受影响路径，再由独立 reviewer 重新判定。

PASS -> 才允许进入 `validation.md` 的官方 Dashboard 用户验收。
