# 上下文开销记录（Context Cost Ledger）

记录产品改动对 LLM 上下文的开销影响。每次涉及 prompt 文本、工具 schema、消息载体的改动，在合并前按本文档的口径测量并追加一条记录。

## 测量口径

- Token 计数：`tiktoken` `o200k_base`（`uv run --with tiktoken`，无模型调用）。
- **完整 profile 基线** = 无 Secretary 的 root system prompt（实测 2,796）＋ Hermes 默认全量工具面（56 个工具 schema，实测 23,639）≈ **26,435 token**。
- 隔离测试 profile（仅 session_history + notebook_show 两个工具）不是基线，只用于取真实请求中的文本。
- Secretary 增量 = guidance 段＋Secretary 引入主会话的工具 schema（session_history、notebook_show、noting_memo）；不含 cron 提示词修订（描述文本级，增量可忽略）。
- Noting 追加 = task instruction＋`<noting-tools>` 控制消息（首条与每次 continuation 全量重发）；当前 Notebook 状态另计（随条目数变化）。

## 记录

### 2026-10-11 基线（V1.5 收口 / V1.6 施工前）

| 项目 | token | 占基线 |
|---|---|---|
| Secretary 主会话增量·现行（guidance 411 + session_history 317 + notebook_show 47） | 775 | 2.9% |
| Secretary 主会话增量·V1.6 目标（guidance 823 + 上列 schema + noting_memo 232） | 1,419 | 5.4% |
| Noting 首轮追加·现行（instruction 294 + `<noting-tools>` 2,239） | 2,533 | — |
| Noting 首轮追加·V1.6 目标（instruction 294 + `<noting-tools>` 3,237，三工具拆分后） | ≈3,531 | — |

分解备注：

- guidance 823 中身份段两例约占 300；三工具 schema（manage/edit/schedule + session_history + notebook_show + finish_noting）合计 ≈3,237，比单 `notebook_mutate` 版（2,239）多 ~1,000（entry_type 枚举与字段并集在三个 schema 中不可避免重复）；属已接受的拆分代价。
- History Search 截断预算：search 单行 content 超 ~800 字符就地截断并标记（全文唯一通道为 `read` + `message_uid`），20 条上限的 search 结果 ≈4–6k token，有界。

### 记录模板

```text
### YYYY-MM-DD <改动标识>
改动内容：…
测量对象与口径：…
改动前 / 改动后（token 与占基线 %）：…
结论与取舍：…
```
