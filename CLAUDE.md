# Hermes Secretary 当前状态

## 自主口径收敛 · 待用户追认

暂无。UI-CAM-01已获用户确认，拍照压缩保留当前实现。

## 当前阶段

**2026-10-20用户确认：部署基本告一段落，第一版可以正常使用。** 当前整理仓库／文档，另按用户追加要求禁用微信原生slash、只读核实侧栏和delegation旧挂账，不扩修其它事项。

- 首尔正式入口、双SPA、Alex / study Profile、NM / Ebbinghaus迁移及三条Mutagen同步已落地；旧部署等待、TCC阻塞与初始化过程不再是当前任务。
- 已上线后端功能基线 `dd93e0053b4a92f1c686bc41e4fe37463e854972`；前端 `83285d2be259f1ee9f7e24bba6dd4c70688831fe`。文档／插件收尾提交不自动等于重新部署。
- Alex默认 `kimi-coding/k3-256k`，窗口262144、thinking High；Noting / Scheduler开启，联合Idle500秒／131072 tokens。已有Conversation保持自身模型配置；study不设默认模型，NM Thread目标仍继承考研Space，可选`thread_sync_space`能力保留。
- 微信绑定采用原生Gateway control socket与Conversation ref；Alex工具 `~/scripts/alex/weixin_bind.py`，调用方直接 `bind --self`。Kimi凭据已补到Alex自己的受限`.env`；多余Gateway凭据注入与用户副本已回滚，正常重启后连接及原绑定保持。独立K3请求HTTP200；未把它冒称新微信消息端到端验收。
- Prompt缓存清理已按当时授权完成，后续沿原生正常Turn懒构建，不追加离线重建。个人工具统一`~/scripts/`，只读保护、显式非空`--space`等规则见AGENTS／08。

## 收尾任务

| 工作 | 状态与完成条件 |
|---|---|
| 三份核心文档 | 已精简，运维过程独立记录；用户关闭项不再挂账 |
| 插件工作区 | 已亲审／定向验证，提交f11a8db已同步，工作区干净 |
| 三仓收口 | 后端、前端、插件分别核对Git差异、凭据与upstream；完成提交／push，最终工作区干净 |
| 微信slash | 已实现／亲审，121相关测试通过；拒绝执行并提示Web，不中断当前任务；待部署 |
| 绑定不变量与发送来源 | 已实现／亲审；绑定259相关测试、发送16项通过。仅显式工具改绑，A晚到不切回／不注入B；异Conversation主动发送给用户加标题，不报告给AI，缺身份仍原样发送；待统一部署 |

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
