# 第二轮整改阶段交付：停在下一次 Verification 之前

## 目标状态与结束判定

2026-10-14夜间托管的代码整改、Main亲审集成、必要真实代表链与设计文档已完成；**整轮独立验收未完成，第二次Verification未启动。** 唯一尚未取得的末次开发GUI观察为C99 Reminder默认折叠/展开保内部timestamp：两条正式Timeline组件用例与当前构建通过，但内置浏览器绑定被安全策略明确拒绝，未绕过，留给明早正常UI复核。不能把这项观察写成通过，也不能把开发结果写成整轮PASS。

实际后端产品快照f8e416178ecf24021c614940052561f30dc7929d；UI正式main与修复树8b3867e3db220910b4bc9613af49a0740e07fc3c。后续文档/hook提交仅更新交接与Git同步。用户visual-polish/visual-design没有写入、自动合并或回滚；用户原有未跟踪文件保留。历史阶段交付详见Git历史及plan证据索引，不使用旧版本声明覆盖当前状态。

## 本轮收敛与授权

- 用户C90纠正Memo：它只给Noting指示，不是Notebook条目/provenance；Main撤回v3首段扩展，原Memo段和Snapshot消费机制保持。
- 用户C93明确清理硬机制先不实施，只做单文档论述与维护软提示；07十类型、统一owner/同步接缝、五Turn/overflow与下一轮承接为待审方案。没有取消/清理新工具、额外状态/调度器、M27行为变更或静默删除。
- 实际Prompt仅整体维护段和直接相关类型/工具description调整；6个完整改变字符串5214→5210字符，按此前相同11目标10532→10528；UTF-8少6字节、空白分词少11词，token未测。全部前后英文/直译/用户原话见repair-secretary-task-contract §10，Main自主收敛并非逐句用户批准。
- C84依02既有契约：同一owner让Schedule/status一版本改变，实际有效Snapshot事务同步Registry；不让模型另call status，不用新id/内容edit/恢复/branch重放已完成occurrence。
- C99：Reminder保内timestamp且默认折叠。Main撤回误加strip，仅现有foldable条件接入instant；无新增包装/CSS/源或模型上下文变更。
- C100：每次commit自动push，已安装两个仓库common post-commit并跟踪源；尊重upstream、无则origin同名功能分支。正式BE main→origin/main，UI main→origin/secretary；不强推、不hook自动集成、不启GitHub CI/CD。

## 已完成与交付物

- 首轮V01–05：旧file.attach合同恢复与三增量RPC；活动Edit单确认后正确原生提交；完整历史/live/temporary/Pending截断，失败保稿；恢复作者附件正文；assistant-ui正式稳定UID scope/Parts/selector/Markdown接入，保原视觉。
- 用户问题：草稿Undo/Redo、真实stream及时呈现与terminal同步、列表刷新不插Loading跳位、Usage成功数据不按active隐藏/旧值覆盖、slash Tab及单文本流换行、Files/Appearance分隔与更新时间分组。Main微修HMR旧Controller新增render字段风险，同owner惰性初始化，不重建连接/草稿/历史。
- Core：秘书任务Schedule所有状态非空/mode必填、禁取消意图后保任务、取消用archive；四Schedule类型必要状态自动联动及同lineage/canonical重排期的真实Registry rearm。硬清理未实现。
- 真实附件：两片4,194,400bytes、新RPC/stat/SHA/partial abort、正式Send与真实DeepSeek读准确大小/首尾marker，复用旧owner证据，不重传大包。
- 新最小Prompt实际创建未来instant任务；自然到点源UID79b589…/row27，WS source seq153到IAB DOM21ms，Thinking seq157，complete seq313到DOM15ms，同UID唯一。三个真正Noting任务完成创建、pending→running→done，以及只schedule_update将done→pending（没有模型补status），同lineage/schedule_id、Snapshot/pointer/Registry/Memo正式提交。
- 受控长流修复样本终态DOM约44–215ms，旧样本约2–5.7s；有完整内容/顺序/terminal无补播证据。它是单机Chrome开发MutationObserver观察，不是paint/SLA、不是assistant-ui独立倍率；后续只改Usage/HMR初始化及C99折叠，App/Parts/Markdown/RenderStore策略保持，未重跑性能大包。
- 当前必要定向证据：Main Prompt真实spawn/prefix三个用例2pass/1保留原句失败，恢复原Persistence句后仅失败项1pass；Usage新有效数据1pass；C99两个组件2pass；HMR owner+Usage2pass及同步event/terminal1pass；各当前构建含tsc通过，最后HMR build日志可复核。footguns/ruff/health三项pass，0阻断/原未改文件1advisory；新增hook footguns/shebangs2项pass。未调阈值、未关闭提示、旧192/33/59/28/Undo/500MB等有效包未重复。
- 稳定文档入口[07](../../docs/07-notebook-cleanup-mechanism-proposal.md)、[Prompt/原话对照](repair-secretary-task-contract.md#10-main-实际最小-prompt-改动与用户原话对账2026-10-14)、[真实链](repair-native-integration.md)、[前端接线](repair-frontend-verification.md)、[Core联动](repair-secretary-task-contract.md#9-c84状态与schedule同owner联动)。具体函数/证据/版本以报告正文和manifest为准。

## Verification 与 Validation

首轮独立Verification历史报告保留：65项、56符合/6不符合/3证据不足，结论不通过；Main不能改它为PASS。本阶段依用户要求修复、亲审、接线与取证，没有派遣或启动第二次Verification，也没有启动独立Validation；不以开发用例数代替二者。用户明早审阅后才决定后续门禁授权。

## 剩余、阻塞与影响

- C99末次IAB历史实看被浏览器安全策略拒绝。实际HTTP请求被返回“protocol not allowed”且允许列表是HTTP/HTTPS；Main不绕URL/ID/其他浏览器/底层控制。代码与两正式组件用例/构建通过，实际图形操作仍未完成；先前自然source链IAB证据不失效。临时queued页未能合法绑定/关闭，明早可正常UI处理。
- 07提出的清理范围、强制结束A/B/C、刚done与即时取消例外、下一次时间要求都是待审政策；本文不批准任何硬机制。软提示不能保证永不积压。
- 开发旧非法Snapshot含无Schedule task的加载边界已记录，不迁移/修补用户库；真实Core/Noting代表使用合法隔离数据。现有运行库/config保留，未来新会话按新合同；不保证旧非法派生状态可写。
- browser本地选文件此前受真实Chrome扩展权限限制；已停止真实浏览器，不改权限。旧原生ref正式submit/模型、新上传API和前端接线机制证据有效，不能冒称新IAB本地filechooser全链通过。
- 原生parser不支持秒级in45s，本次模型收到真实拒绝后改合法in1m且说明偏差；未增加parser能力或伪造45s成功。
- 既有大chunk warning/未改文件HX012提示保留；手机真机、其他平台/provider及完整独立验收未被本次macOS/IAB开发取证覆盖。
- 自有53449/5183服务及子进程全部退出，临时隔离config逐字恢复、DB/Registry/API计数相等、无多余模型请求。只保供用户使用的53445/5173；不存在为了补证留多个worker/observer/模型循环。

## 用户复核建议

明早先看07与Prompt原话对照；正式入口http://127.0.0.1:5173。53445已在session.active_list无活动工作后由旧PID1521更新为PID20193，沿原round2-runtime HOME/config/DB；新RPC注册探测4001而非method-not-found，frontend HTTP200。前后端source版本一致，HMR同owner问题已修。

现场重点：Reminder默认折叠，展开保timestamp；新消息/Thinking追踪真实进度，无终态继续补播；Instant源先输出；活动/空闲Usage均可见；slash Tab/单流换行；侧栏分组与两分隔；活动编辑单确认/失败保稿及Undo。旧资料可读与新合法任务是不同边界，必要时使用新会话验证Core，不静默改旧Notebook。

续接先读根CLAUDE顶部、plan统一证据索引及本报告，保留有效证据，不重传500MB/重跑模型/重开已完研究。剩余GUI与两独立门禁如实记录；不要未经授权启动下一次Verification。
