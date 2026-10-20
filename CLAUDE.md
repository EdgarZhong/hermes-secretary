# Hermes Secretary 当前状态

## 自主口径收敛 · 待用户追认

暂无。UI-CAM-01已获用户确认，拍照压缩保留当前实现。

## 当前阶段

**已完成本地窄修复（2026-10-20晚用户确认并要求提交）：** Noting原生每Turn迭代预算耗尽时，经既有Commit Gate保存合法工作态，所有触发来源共用，与`force`触发无关；末次调用已成功finish时保留显式结束。无模型／Prompt／预算变更。13个新增边界场景通过，所在测试文件54项通过，冻结10检查通过；相关5文件首次156通过／2失败，两项均在原版复现（旧Snapshot ID正文断言、旧文件活动任务计数污染），不冒称全绿。修复已纳入本次提交，尚未部署，不能反推线上已修或恢复旧失败任务。生产任务21:38:15–21:51:31达到50次上限后failed、无Snapshot，`/notebook`为空；口径已同步07，证据在`.hermes-dev/pinned-mobile-20261020/`。

**2026-10-20用户确认：部署基本告一段落，第一版可以正常使用。** 本轮文档／仓库整理及追加微信修复已完成，17:58部署首尔；后续按新任务推进，不自动重开旧挂账。

- 首尔正式入口、双SPA、Alex / study Profile、NM / Ebbinghaus迁移及三条Mutagen同步已落地；旧部署等待、TCC阻塞与初始化过程不再是当前任务。
- 已上线后端功能基线 `fcf5d08ac587b43c5aafd2f3e8656a6c5b147432`；前端 `83285d2be259f1ee9f7e24bba6dd4c70688831fe`；插件收尾 `f11a8db6c32e109bdc1de6c39c2920bcad14d617`已同步。后续纯文档提交不等于运行版本改变。
- Alex默认 `kimi-coding/k3-256k`，窗口262144、thinking High；Noting / Scheduler开启，联合Idle500秒／131072 tokens。已有Conversation保持自身模型配置；study不设默认模型，NM Thread目标仍继承考研Space，可选`thread_sync_space`能力保留。
- 微信绑定采用原生Gateway control socket与Conversation ref；Alex工具 `~/scripts/alex/weixin_bind.py`，调用方直接 `bind --self`。Kimi凭据已补到Alex自己的受限`.env`；多余Gateway凭据注入与用户副本已回滚，正常重启后连接及原绑定保持。独立K3请求HTTP200；未把它冒称新微信消息端到端验收。
- Prompt缓存清理已按当时授权完成，后续沿原生正常Turn懒构建，不追加离线重建。个人工具统一`~/scripts/`，只读保护、显式非空`--space`等规则见AGENTS／08。

## 本轮交付

| 工作 | 状态与完成条件 |
|---|---|
| 三份核心文档 | 已精简，运维过程独立记录；用户关闭项不再挂账 |
| 插件工作区 | 已亲审／定向验证，提交f11a8db已同步，工作区干净 |
| 三仓收口 | 后端／插件变更已提交同步，前端无改动；保持三个本地工作区干净，不清理ignored运行数据 |
| 微信slash | 已上线，121相关测试通过；拒绝执行并提示Web，不中断当前任务 |
| 绑定不变量与发送来源 | 已上线；绑定259相关测试、发送16项通过。仅显式工具改绑，A晚到不切回／不注入B；异Conversation主动发送给用户加标题，不报告给AI，缺身份仍原样发送 |

最终冻结10检查通过（0 blocking／advisory）。首尔Web／Gateway正常、微信connected、原绑定及配置／workspace文档保持；部署前Alex9956条消息逐行内容和身份无缺失／改变。发送脚本恢复root:root／0555＋immutable；真实只读control已核同ref原文／异ref来源头／缺身份原文，无生产微信测试发送。运维过程和回滚点见独立记录。

## 保留事项（不因本轮收尾自动立项）

| 事项 | 当前边界 / 下一步 |
|---|---|
| 详情接口 | 第10项pagination元数据漂移尚未得到用户关闭口径，暂保留；不主动扩大修复 |

侧栏旧“触摸／键盘均受影响”已纠偏，不再作已证实缺陷；手机重排后转宽屏的顺序同步仅静态观察，未UI复现，详情留运维记录，不自动立项。

用户已关闭／移出工程挂账：拍照参数接受；手机首触Send目前未见问题；会话列表关闭；补水总流量不构成问题；Reminder静默、编排分流句和主动核实／触达白名单属于模型行为调优，不再列开发待办。SOUL.md与workspace AGENTS.md可定初稿，不因本次整理改写它们。

入口识别口径已定：保留Hermes原生Gateway／其它Platform按消息来源轮换和切换时的notice注入；关闭System Prompt中当前Platform的身份注入（现代码已关闭），不再挂“稳定识别待定”。

## 证据与入口

- 通用规则只在 [AGENTS](AGENTS.md)，稳定规格索引在 [README](README.md)。操作、实际版本、备份与回滚统一 [运维记录](docs/operations-log.md)；执行步骤见 [部署SOP](docs/cloud-deployment-sop.md)。
- 固定v5产品意图复审及两门禁按其原版本保留：[Snapshot Index](.autonomous/20261018-product-intent-review/snapshot-index.md)。旧模型归因／Search完整性／Noting来源偏差为已接受的非阻断观察，不重开为新增开发。
- 不把未验证写成通过；历史全量存在失败，后续定向通过不等于全量全绿。原报告、固定证据、Git历史均保留，不将旧PID、Agent编排或过时等待条件带入下一轮。
