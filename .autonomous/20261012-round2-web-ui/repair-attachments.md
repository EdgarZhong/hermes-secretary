# 附件展示修复记录

2026-10-13；本轮负责修复者完成实现与证据交接，Main 负责最终整合及浏览器实测。此记录只说明当前问题、修复和验证状态。

## 问题与确凿原因

真实发送普通文件后，文件正文展开在 User 气泡中，不符合历史附件只显示文件图标和名称、保留用户输入的要求。

只读检查隔离运行库 `.hermes-dev/round2-runtime/state.db` 的 user row155（Session `20261013_111430_4c8d85`）：`content` 长 61,800 字符，包含用户输入、原始 `@file:` 引用，以及原生追加的 `--- Attached Context ---`、`📄 同引用 (32605 tokens)` 和 Markdown fence；`display_kind`、`display_metadata` 均为 NULL。本报告不复制附件正文。

这不是 `<file>` 包装。原生 [引用预处理](/Users/edgar/code/hermes-secretary/agent/context_references.py:236) 保留作者输入并追加上下文；[文本文件格式化](/Users/edgar/code/hermes-secretary/agent/context_references.py:376) 生成 `📄` 和 fence；[磁盘文件提示](/Users/edgar/code/hermes-secretary/agent/context_references.py:646) 生成 `📎` 格式。原前端只移除引用 token，未隐藏该追加正文，因而把模型可读内容直接摊入气泡。原生 Desktop 已有 [展示尾部剥离逻辑](/Users/edgar/code/hermes-secretary/apps/desktop/src/lib/chat-messages/hydration.ts:111)，可作为现有机制证据。

## 实际修改与正式接线

- [nativeAuthoredText](/Users/edgar/code/hermes-secretary-web/src/core/content.ts:26) 仅在原始 prefix 引用与原生 `📄/📎` 包装匹配时剥离附件扩展；单有标题、缺少匹配引用或不完整包装时保留正文。
- [userAttachmentDisplayText](/Users/edgar/code/hermes-secretary-web/src/core/attachments.ts:45) 优先使用 `display_content`，包括明确空串；仅对 User 的界面展示去掉 timestamp、附件扩展和引用 token，保留用户输入文字。
- [nativeReferences](/Users/edgar/code/hermes-secretary-web/src/core/attachments.ts:21) 仍从原始 source 内容派生附件，并复用同一 prefix 提取，避免正文中的引用重复生成 chip；重复文件名和重复引用 occurrence 保持独立。
- Main 已在正式 [projectBody](/Users/edgar/code/hermes-secretary-web/src/core/projection.ts:239) 的普通 User 分支调用 helper；Framework、Reminder、Compaction 分类保持原接线。历史附件仍从原始 source 派生。

本次 helper 不修改持久 `content`、metadata 或模型上下文；模型可读正文保留在原始内容中。

## 已有验证

只执行一次 `npm run test -- src/core/attachment-display.test.ts src/core/contracts.test.ts`：两个文件 **78/78 通过**（原 contracts 63 例及新增附件展示 15 例），Vitest 耗时 242 ms。一次 `npm run typecheck` 和相关文件 `git diff --check` 均通过。未运行全量测试、build、模型请求或服务重启。

[新增测试](/Users/edgar/code/hermes-secretary-web/src/core/attachment-display.test.ts:10) 使用 row155 的真实包装结构和受控正文，覆盖用户文字保留、附件独立展示、原始/model 内容不变、空 display_content、附件-only、重复名称与引用、刷新一致、磁盘文件提示，以及无可信包装时保留普通输入。contracts 仅将附件旧 fixture 改为真实原生格式，其他实现者的工具投影测试保留。

## 待 Main 现场验证

- **长文件名显示**：[AttachmentChip](/Users/edgar/code/hermes-secretary-web/src/design/chat.tsx:74) 接收完整 `name` 并设置 `title`；[文本父容器](/Users/edgar/code/hermes-secretary-web/src/design/theme.css:170) 有 `min-width: 0`，子 span 有 ellipsis/nowrap，但历史文本父容器未设 `flex: 1`。这只是源码调查，可能与硬裁有关；CSS 修复及实际浏览器效果由 Main 核对，本任务未修改 design。
- **原生图片链路**：Main 已确认当前隔离 profile 的原生配置 `supportsvision=true`。尚缺 DeepSeek 实际请求携带图片像素、模型实际识别图片内容的证据，不能仅凭配置或上传 ACK 判定闭合；待 Main 组织浏览器实测。
- **正式 User 气泡**：Main 接线后仍须用已有真实附件消息核对气泡只显示原用户输入与附件图标/名称，刷新不重新摊开正文；本记录中的自动测试不冒充该现场结果。

## Main 最终集成接收

2026-10-13：Main集中亲审正式路径与改动并接收相应owner证据，最终前端c55120f、visual fc18614、原生产品4443aa7。用户自测整改的实际关闭范围、测试失败/修复留痕、真实DeepSeek/IAB及未验证边界统一见final-delivery「当前整改关闭证据」和根CLAUDE；本报告上方“待实测”是交回时观察，不覆盖该最新接收。最终冻结前端health0/0及build/types通过；两独立门禁未执行，不称整轮验收。
