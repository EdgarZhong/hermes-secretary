# 第一板块：今晚实施并上线的完整指导

## 0. 目标与边界

用户决定的顺序为：本板块实施上线 → 短网络实验 → 按结果设计第二板块。

今晚复用现有架构与语义，减少已证明的无用传输/渲染并修复明确缺陷。保留产品的气泡、附件、Thinking/工具展开、发送/Stop/Steer、Rewind、历史加载、Profile 和 Secretary 行为。新增轻量加载占位沿用现有样式，不重做产品交互。没有任何补丁能保证零回归，因此用独立提交、真实边界验证和回退降低风险。

**不新增** event log、同步 revision、持久客户端缓存、媒体存储服务、提交队列/表、认证状态机或第二套 Runtime。不改生产模型/Prompt/Noting 预算/DB schema。不要把“纯前端改动”当成天然低风险；下面按前后端依赖成组执行。

## 1. 接手与基线

核对当前仓库说明、实际部署和本地工作树，保留已有未提交修改。必要时建隔离工作树；不能 reset/clean 覆盖用户工作。

审计基线：
- 后端 EdgarZhong/hermes-secretary：fcf5d08ac587b43c5aafd2f3e8656a6c5b147432。
- 前端 EdgarZhong/hermes-still-chat：83285d2be259f1ee9f7e24bba6dd4c70688831fe，secretary 分支。
- 原调查本地 ecc6695 相对上述后端仅多文档提交，运行代码可比；现在是否更新必须重新查。

先记录实际 Web/Gateway 前后端版本、Caddy 版本/配置、部署路径、服务单元、已有发布脚本、当前活动 Turn/Noting child。不能凭附件写死服务名、端口和重启命令。复用已有备份与就绪流程，并准备精确回退命令。

建议将下列任务拆成可独立回退的提交；不要求顺序以外的全仓重构。

## 2. P1-01：已有 Caddy 压缩与静态浏览器缓存

**修改端：Caddy 配置；前端功能无需改动。**

1. 检查实际目标响应是否已压缩。若已生效，记现状，不重复包一层 gzip。
2. 使用当前安装版支持的 encode gzip，对会话/messages REST JSON、必要文本型静态资源启用。配置在既有鉴权与反代结构中进行，保留响应语义。
3. 不升级 Caddy、不加 Brotli 插件，不把此次范围扩展到 WS、其他流式响应、认证 HTML 或整个代理缓冲策略。若已有 Content-Encoding，避免重复压缩；不要手动猜 Content-Length。
4. 已带内容哈希且部署能保证 URL 对应字节不变的 JS/CSS，可设置浏览器长期缓存/immutable。主 HTML、带 bootstrap token 的页面、动态接口不能套用 immutable；不新增 Service Worker。
5. 私人聊天/图片不能因此进入共享 CDN 缓存。这里只处理传输压缩与既有静态资产缓存。

**验收：**配置语法/适配检查通过；浏览器真实 Accept-Encoding 协商后看到正确 Content-Encoding，完整 loadingFinished，解码内容与行身份一致。记录同一窗口线上 encoded bytes。gzip 离线 545572 B 不是线上精确门槛。检查正常鉴权、WS 和原页面加载。

**回退：**恢复上一份配置并按现有流程 reload。Caddy 默认重载可能关闭现有 WS，必须在空闲窗口操作并验原重连/草稿保留；不能声称 reload 零影响。不要为此顺手重写重连机制。

## 3. P1-02：usage 使用现有 summary

**修改端：前端，复用后端已存在参数。**

定位：
- 前端 src/core/usage-view.ts，savedSession。
- 后端 hermes_cli/web_routers/sessions.py，get_session_detail。

将该消费者的 /api/sessions/{id} 读取改为 summary=true，继续通过 scoped 保持 profile。此消费者使用身份、profile、input/output/cache token 计数，不需要 origin_json、system_prompt、model_config。

保留完整 metadata 真正消费者的读取，不全局替换。保持 null/unknown、部分 usage 和缓存命中率的现有语义，不把缺失计数变成 0。

**验收：**正常/缺计数/空计数和不同 Profile 的显示与旧实现一致；请求确有 summary=true。原 full 215537 B，summary 51684 B；不能称为几百字节新状态接口。

## 4. P1-03：验证型图片引用投影 + 真正按视口下载

这是今晚对大历史 JSON 最有价值的一组，前后端成组修改。**不能只把 inline_images=true 改成 false。**

### 4.1 后端只读 opt-in

定位：
- hermes_cli/web_routers/sessions.py，get_session_messages/_project_for_display。
- tui_gateway/session_history.py，_user_image_display_text。
- 既有带 Profile 和鉴权的 /api/fs/download。

新增一个默认关闭的布尔参数 prefer_image_refs（拟定名称，不是现有 API），cards 和 detail_row_ids 两种读取共用同一转换入口。老客户端默认得到旧行为；inline_images=true 原有语义保持。禁止修改 DB、模型输入或 submit 的 staged 数据来实现只读瘦身。

处理算法：

~~~text
查询本次现有分页/指定行集合
对响应副本中符合条件的 structured user row：
    在原始 structured content 上运行现有图片验证 helper
    只有整个 row 校验通过、既有下载访问边界成立：
        将响应副本 content 换为 helper 返回的 caption + 原生 refs
    否则：
        原始 inline content 完整保留
再沿用现有显示/card 投影
返回相同 row ID、UID、role、顺序、分页与身份信息
~~~

helper 已检查 parts 数、路径/引用格式、文件存在和类型、文件大小、Base64 与文件内容一致性等。先验证原始结构，不能先 inline=false 丢结构再猜路径。只对已查询页中的候选运行，不扫全库、不迁移历史、不增加媒体索引。保留 helper 的限制，不能为提高转换率放松校验。

前端 nativeMessageReferences 读取的是 content，**不是 display_content**。只改 display_content 不会完成附件识别。helper 返回 None 时禁止降级成只有 [image] 的假成功，也不做部分图片猜测替换。

校验本地文件相同不自动证明 Profile 下的下载接口可取。执行机须核对相同 Profile/owner 的文件授权边界和真实下载。如果权限不能由现有机制明确成立，该行保持 inline。不要为此开放更宽文件路径。

### 4.2 前端接线与视口加载

定位：
- src/core/controller.ts：cards URL。
- src/core/history-details.ts：detail_row_ids URL。
- src/core/attachments.ts：nativeMessageReferences/inlineImages。
- src/App.tsx：historicalAttachments/HistoryImage/attachmentImageUrl。

cards 和对应 details 显式启用新 opt-in，并保留 inline_images=true。让 detail 读取也支持，避免后来为同一 user row 重新塞回 Base64。正常工具/Thinking 行不做媒体转换。

当前 HistoryImage 对 URL 在 effect 挂载时已经 fetch，再设 img loading=lazy 不能阻止此前下载。改为：
1. 渲染真实可观察的图片容器/轻占位；当前无 source 时 return null 必须调整。
2. 使用现有聊天滚动容器作为 IntersectionObserver 根；按真实进入/接近可见区域触发一次现有 fetch。
3. 沿用现有鉴权 token、同源 cookie、profile URL、图片类型检查、错误表现。
4. 每个 URL/所属会话变更时正确重置；切会话/unmount abort，释放 object URL。
5. 已触发后不要每次离开视口就 abort 再重试，避免用户滚动导致反复下载。
6. data URL fallback 已随 JSON 下载，不能宣称观察器节省了其传输。保持原展示。
7. 有可靠原尺寸则沿用宽高占位；没有尺寸不伪造精确比例，不新增探测接口/缩略图服务。加载后的滚动锚点按现有机制验证。

### 4.3 发布门槛

在同一 200 行窗口、同一组 UID 上先做原/新只读对照，不通过换小页排除图片来制造结果。只输出：
- 原/新 JSON bytes、gzip bytes、处理耗时。
- 可转换行数/图片数、inline fallback 行数/原因类别。
- 行数、UID、顺序、caption、图片数量一致性。
- 正确 Profile 下引用图片实际可下载。

必验：纯文字、纯图、caption+图、多图/重复图、路径含空格、文件缺失/内容变化、跨 Profile；首屏图片、滚动进入、切会话、详情补水、已有编辑/重发入口和滚动位置。复用现有测试，只补真实缺口。

原包最大 651203 字符 data URL 的图片本体未包含在调查附件中，**执行机必须实测可转换性**。转换率低时如实报告。若需要新媒体存储才能成立，此项转第二板块，其余独立项继续。

**部署顺序：**后端支持默认关闭参数并就绪，再发布 opt-in 前端。回退时先停用前端 opt-in/回退前端，再视需要回退后端。默认旧路径始终可用，无 DB 迁移。

## 5. P1-04：停止无需求的后台详情补水

**修改端：前端请求策略，复用现有后端 detail_row_ids。**

定位：src/core/history-details.ts 的 schedule/prioritize/pump；controller 的 historyDetails.schedule；App.tsx 的 useDeferredDetails、NodeDisclosure、HistoricalThinking。

目前 schedule 会把 deferred rows 自动排入背景队列，原采集有 14 个 details/约 833 KB。现有 prioritize、Loading/Retry 和打开动作提供局部基础。

先列出实际完整内容消费者：展开、复制、编辑、导出或其他当前存在的动作。不要凭空新建产品入口。确认每个消费者都能使用现有按需加载后，只停止“无需求自动发请求”，保留：
- 当前 locator/profile/row 登记；
- 显式打开/操作的 prioritize 和 waiters；
- 错误重试、对象 identity 校验；
- 切会话取消、失效结果丢弃；
- 现有卡片预览、状态、标题/参数必要事实。

不能直接删掉 schedule 调用导致登记失效，也不能只删 schedule 末尾的 later()：read.finally 也会继续驱动队列，显式展开后可能仍下载剩余闭合卡片。调整的是无需求项的入队/执行条件，不另建全局可见性/多级优先级系统。不要为了“快”提高并发。若需要新接口或改变操作流程才能完整补水，该策略后移，已有 summary/图片优化照常发布。

**验收：**历史静置且未打开详情时，相关后台请求消失；首次展开、重试以及实际需要完整内容的动作仍然正确；一张卡片展开并加载完成后，其他闭合卡片不继续后台下载。已展开工具/Thinking 在 complete 强制刷新、恢复或同 UID 源行替换后，若再次 deferred，仍须按现有显式需求补水，不能要求用户重新开合。当前 useDeferredDetails effect 仅依赖 open/node.id，须修需求与当前源行的关联；不能停在 Loading。若此边界无法完成，保留原背景策略。此项用实际请求数/bytes 验证收益，不套用 metadata 的压缩率。

## 6. P1-05：有限渲染优化

### Thinking 延迟首次 Markdown

src/App.tsx::HistoricalThinking 闭合时不首次构建完整 Markdown。第一次打开后保留已挂载内容及原 Disclosure 动画/状态，后续补水仍更新。

不要全局改 design/primitives.tsx::Disclosure，不要每次关闭立刻卸载；否则可能改变动画或组件状态。保留标题、图标和开放入口。覆盖默认闭合、首次打开、详情到达、关闭/再开即可。

### 工具卡来源引用稳定

src/core/projection.ts::callPresentation、combineToolCards、stableTimelineNodes：仅当 detailSources 数组长度、顺序、每个源对象引用都一致时复用数组引用，让现有浅比较有效。

不能只比较 UID；同 UID 的参数、结果/状态、完整 detail 到达需要刷新。覆盖工具结果更新、详情补水、live→history 过渡，不新增一套缓存。

## 7. P1-06：修复纯图片即时受理缺口

这是明确缺陷，但必须完整修现有 row 的交接，**不能只放开空 text guard**。

定位：
- tui_gateway/methods_submit_idle.py：图片校验、canonical paths 捕获、admission、_submit_persist_with_receipt。
- tui_gateway/session_workdir.py：_write_submit_user_row、_persist_submit_user_row、_adopt_submit_user_row。
- tui_gateway/session_history.py：_build_persist_message_with_image_refs、_build_persist_user_message。
- tui_gateway/prompt_turn.py、agent/turn_context.py、agent/image_routing.py：worker/native/text 路由及持久认领。
- 前端现有 accepted_user / message.user_committed 合并路径。

split module 的导入/绑定可能使调用处与定义处不同，按函数名检索实际定义。_build_persist_message_with_image_refs 用于持久显示；不要误换成构造 model-only vision 提示的 _build_image_ref_message。

原问题：纯图受理无 durable row/receipt/committed event；caption 行最初仅文字。现有 worker 稍后才写真实图片内容，前端可能提前读空，再等长历史刷新。

最小修改：
1. 用本次已验证/捕获的 image_paths，为原受理行构造 caption+refs，复用既有编码 helper；不在受理阶段读取完整图片生成 Base64，也不额外调用 vision。
2. 扩展现有 staged handoff 的输入匹配信息，保持本次清理后原始 text 与 canonical image_paths 的严格对应，或等价可靠校验。
3. worker 继续认领同一 row_id/UID/owner/db_path，沿用 set_user_message_content 原位更新与 _db_persisted，不另造一条 user 行。
4. receipt 与 committed event 都来自真实持久行。前端沿用 UID 合并，不创建第二套乐观消息权威。

陷阱：当前 _adopt_submit_user_row 有 staged.content == text 的匹配。若受理行 content 改成 @image 引用，而纯图片原 text 仍为空，worker 会认领失败并另写一行。必须同步修正匹配，不能用修改模型原 text 绕过。

**模型输入保持原行为：**原 caption 与 images 继续走已有 native image parts 或 text+vision tool 路径。不要把 UI refs 拼进模型 raw text，避免改变 @ 预处理和 vision 路由。保留 model-only notes、sidecar、timestamp marker 与原 persist 构造职责。

少量必须验证的边界：
- 阻塞 worker：纯图受理后立即已有正确 durable row、accepted_user 和 committed event。
- 放行 worker/完成：没有第二条 user 行，row ID/UID/owner 不变。
- caption+图、纯文字、多图/空格路径正确。
- native 与 text 两路图片输入语义不变。
- receipt 先到、event 先到、刷新/replay 后前端都只有一条。
- 持久写入失败不得生成 accepted_user/committed event。真实持久受理后 worker build 失败或中断不撤销 accepted、不删除用户行、不自动重发，沿现有 Turn 失败/中断通道收尾；认领更新失败须验证原处理，不扩大重复行问题。
- Profile/会话旋转沿用原 owner 捕获；TUI/busy queue/Reminder 等既有无图调用不受污染。

原 reproduction 测试是证明旧 bug，必须移植并更新期望。若无法证明同一行认领，停止本项上线，其余项继续；不为赶工引入 submission 表或自动补发。

此项只保证同一次受理在 receipt/event/worker/replay 不重复，不新增跨断线 exactly-once。结果未知时不能自动重发 prompt.submit_idle。

## 8. P1-07：应用已存在的 Noting 预算收尾补丁

补丁：patches/noting-budget-local.patch，来自原包，单独提交。执行前 git apply --check 或等价逐差异审查；如果已有部分/全部修复，不强行重复应用，不覆盖工作树。

运行文件：secretary/noting_child.py、secretary/noting_notifications.py，另有 tests/secretary/test_r3_child.py 与规格说明。

保留原 Commit Gate、合法工作态、版本/Anchor/开关检查。正常原生迭代预算结束接回已有 force close/commit；显式 finish 优先；真实 failed/interrupted/error/failure_reason 不伪装成功。forced 是结束方式，不能混为 force 触发来源。

不改原生 50 次和外层 5 Turn 预算、模型、Prompt、DB schema，不重跑旧生产 admission，不补造旧 Snapshot。原案例只检索未维护，修后允许合法空 Snapshot；不能承诺“有有效笔记”。

验证：
- 实际 HEAD 复跑相关定向测试。原 test_r3_child.py 54 passed/13 新边界；相关五文件一轮 156 passed/2 旧失败。两项分别涉及旧 Snapshot ID 文案断言和 active count fixture，记录真实失败签名，不删断言后写全绿。
- 新边界为四触发×有/无修改 8 项、末次显式 finish 1 项、真实失败类 4 项。
- 有必要时在隔离 Profile/provider fixture 以测试预算 1 走真实 native loop；生产预算不变，不在线故意耗尽 50 次。
- 正常 finish 小例、Snapshot/pointer/child 最终态/active count/Framework 行为一致。
- 新失败、旧失败签名变化、child 无法清理，则暂停该项。

框架通知原机制仍非重启后必达的持久事件总线；此补丁不额外作出该保证。核对 Web 与微信 Gateway 等实际加载 Noting 的宿主都使用预期代码。

## 9. P1-08：必要诊断与部署就绪

只记录现有 bootstrap 开始/完成、WS 创建/open/ready、错误阶段与 elapsed、状态码/请求 ID；不记录 token、Cookie、请求正文或 WS 内容。复用现有日志/观察器，不另建遥测平台。

现有 302 不能证明具体认证配置问题；普通 fetch TypeError 也不能统一判为登录失效。只有复现到明确局部错误才修，不猜改 TTL/2FA/Redis，不新增登录状态机。

部署分别确认：进程 active、端口监听、经过预期鉴权的应用只读请求成功。一个 200 HTML 登录页不是接口就绪。

## 10. 今晚明确后移的项目

| 项目 | 原因/第二板块归属 |
|---|---|
| 200 行直接改 50/20 | offset/已载入窗口/anchor/工具跨页配对/滚动有联动；默认保留。完整分页覆盖已存在且能验证时才可另做独立补丁，非今晚默认任务 |
| 删除 force 或统一 debounce 完成刷新 | 可能复用写入前的旧 flight，丢 Gateway/compaction/rewind 事实；revision/cursor 方案后置 |
| 放松灰色 Send，recover 改 Promise.all | unknown 不能当 idle，涉及回放缺口和安全受理；状态机后置 |
| SSE 替换、双 WS+SSE、event log | 需按网络实验定选型及一致性契约 |
| 全面媒体 URL/缩略图/缓存系统 | 第一板块只转能验证的现有 refs；全面资产化后置 |
| 改 compact 时间、强插“新摘要” | 显示位置根因未完整复现，影响历史语义 |
| 重写认证与自动重发 | 证据不足且改变重要状态语义 |

现有非 force history flight/event seq 已有去重。只有真正复现的同一最终状态重复读取、且合并后保留写后一次读取，才允许局部去重；不要为了任务数量重做已有能力。

## 11. 上线与回滚

1. 完成独立提交和针对性验证，记录未通过项及原因。已有用户授权覆盖本次验证后上线，不额外申请同一意图许可。
2. 按现有一致性方式保全 DB 与配置；不要只复制正在写的 SQLite 主文件。不要并起另一个带 scheduler/Gateway 的生产 DB canary。
3. 在实际 Web Turn、Noting child、相关 Gateway 工作空闲边界发布，不中断合法工作态。
4. 后端就绪后发布新前端；Caddy 语法校验后 reload。仅重启需要加载变更的宿主，并记录各入口实际版本。
5. 验登录/草稿/历史/原图片/Thinking+工具展开/发送/Stop/Steer/历史继续加载；纯图片补丁通过后验一次受控 Turn，完成与刷新后始终单行。
6. 同一 200 行窗口记录新旧 bytes、转换率和必要请求，再进入 EXPERIMENT.md。
7. 5xx、认证循环、图片丢失、重复行、Profile 错配、Noting 无法清理等新回归触发对应补丁回退。

回滚按依赖：停新前端 opt-in → 必要时回退其后端投影；压缩异常恢复 Caddy 配置；纯图片或 Noting 回退独立代码，保留发布后合法聊天/Snapshot。**代码回滚不能默认整库恢复，不能删除“看似重复”的真实生产行。**

若真实访问/审批机制阻断，在完成所有可做准备后说明具体阻断与来源，不绕过、不假装已上线。

## 12. 回交格式

每项记录：状态（完成/未做/阻断）、commit、实际部署宿主/版本、针对性验收、回退命令。

性能表至少包含：相同会话窗口/UID 集；原新 raw/gzip/线上 bytes；可转换/fallback；详情请求数/bytes；图片视口行为；headers/body/total 分段。敏感正文不交回，仅长度与必要身份校验摘要。

最终清楚列出：第一板块实际改善、剩余分钟级路径是否复现、短实验结果，以及第二板块需要解决的事实。不能把条件估算写成实测。
