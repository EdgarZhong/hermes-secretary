# V1.5 Cloud Resume — Validation

## 状态

**PENDING / 仅在 Verification PASS 后执行。**

云端阶段没有启动 localhost Gateway、官方 Dashboard 或真实 DeepSeek 用户会话，因此本文件不声明任何端到端场景通过。

## 1. Preconditions

- `verification.md` 已由独立 reviewer 明确 PASS；
- 使用最新 `main`，无未提交产品修改；
- 隔离 `HERMES_HOME`，不得污染真实用户状态；
- 使用既定 DeepSeek 官方 Anthropic / deepseek-flash 原生 Hermes 路径；
- 官方 Dashboard Web UI + localhost native Gateway；不以 CLI、mock、单元测试或个人 UI 替代。

## 2. Core user journeys

至少从真实用户输入到最终模型/Notebook/Reminder结果覆盖：

1. **Main / History**：跨 Compaction 查询旧原文，History Search 保持可用且 canonical identity 正确。
2. **Global/local switches**：global on/off、local /noting on/off、cold resume；local off 不改变 Main 的稳定 tools bytes，允许按规格读取已有 Notebook。
3. **D01**：Native Main 可以进入 Noting；确认 External Main 时触发条件成立但无 Noting side effect，给出既定框架提示/跳过行为。
4. **Ordinary Noting**：真实 task 使用 History/Notebook 后调用 finish_noting(reason)，提交 Snapshot；日常 Notebook 不显示 termination。
5. **Special Noting**：NOTING_WITH_COMPACTION 正常 compact_parent 结束；另构造五 Turn 未终止场景，验证 forced Snapshot 与框架 parent compaction。
6. **Parent concurrency**：Noting 运行时 Parent 可继续 Turn/compaction；child 仍使用 frozen Anchor/prefix，commit 时重新校验 Anchor。
7. **Proposal persistence**：Candidate -> Main 自主查原文/后续反证 -> 提案；“修改草稿”不等于批准；明确批准只执行批准范围；后续 Noting 正确归档。
8. **Schedule/Reminder**：passive commitment/task/watchpoint 不启动新 Turn；idle user reminder 走原 admission；busy user reminder 转 pending System Reminder；provider failure 不丢提醒。
9. **Audit visibility**：内部 audit 可见 finish_noting(reason)/compact_parent/forced，普通 /notebook、notebook_show 与 Main AI context 均不可见。

## 3. Failure/retry evidence

对任何失败保留实际输入、可见输出、相关 runtime 日志和状态库证据。至少验证 provider request failure 不 ACK 丢失 System Reminder，以及 Noting 真失败不产生无效 Snapshot。

## 4. Cache observation

在真实 Noting journey 同时记录 Verification 要求的 request prefix 与 provider cache-read 统计。若 provider 不暴露某项统计，写“不可观测”，不得推断成命中。

## 5. Verdict

Validator 在此写 **PASS / FAIL**，并逐场景列观察结果。任一适用核心场景失败、由 mock/CLI 替代、或证据来自旧 commit，则不得 PASS。

## 6. After PASS

Validation PASS 后回到 `final-delivery.md` 完成最终 delivery-evidence-review，并同步根 `CLAUDE.md` / README 稳定状态。
