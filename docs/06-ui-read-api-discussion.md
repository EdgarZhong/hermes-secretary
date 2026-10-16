# UI 增量与只读 API 讨论口径

日期：2026-10-11。

## 文档定位

本文件独立记录本次 UI 增量期待、用户已确认口径和仍待确认的 API 提案。它是讨论文档，尚未冻结为实施规格，也不表示已授权开始 UI/API 产品施工。

V1.6 正在进行的实现与验收继续使用原冻结依据；本文件不覆盖或扩展该轮冻结规格、索引及历史审查结论。后续实施范围、具体接口与验收口径须另行收口。动态状态只记录在根 `CLAUDE.md`。

## 用户已确认的 UI 期待

### 1. Full Foreground 审计视图

- 参考用户正在使用的 PiWebUI 的 Branches 面板，以有序消息列展示当前 Conversation 的 Full Foreground。
- 在相应消息位置标出 Notebook Anchor，并能查看对应的 Notebook Snapshot。
- PiWebUI 是展示能力的灵感来源，当前没有冻结具体布局，也没有确认要新增完整分支树浏览。
- Full Foreground 的既有语义按现行 02 §2.4 及现行 04 的有效修订理解：Context Prelude、当前有效路径上的逻辑消息及审计附着；不要以普通聊天消息列表或 Active Context 替代。

### 2. Noting 状态悬浮球与详情

- 聊天面板有轻量 Noting 状态入口，可以使用小悬浮球。
- **只在 Noting Task 正在执行时亮起**。开启 Noting、等待 Idle Trigger 或已有 Notebook，不等于正在执行。
- 静息状态仍可点击打开详情，查看距离下次预计 Idle Trigger 还有多少秒等信息。
- 页面保持连接时，任务状态及时更新；复用现有所属会话的 WS 长连接/事件路径。
- **暂不设置手动触发 Noting**，详情面板不提供“立即整理”等按钮。
- 用户允许设计有趣的轻量交互，具体动画、颜色和展开样式尚未确认。

### 3. 倒计时的计算方式

- 后端提供定时器的预计触发时间，前端自行计算倒计时。
- 首次打开详情/连接时取得当前定时器信息；定时器取消、重排等实际变化发生时更新该信息。
- 不通过 WS 每秒传送剩余秒数，也不以逐秒 HTTP 请求取得倒计时。
- WS 用于推送实际任务状态和定时器变化；前端的本地时钟负责倒计时显示。
- 倒计时指向预计 Trigger 时刻，不表示到零必然启动任务；实际执行仍服从现有 Noting 准入规则。

### 4. 当前 Notebook 与 Memo 展示

- 用户能够直接查看当前完整有效 Notebook，无需先在聊天中执行 Slash 命令。
- 当前 Memo 单独展示，展示现有条目及顺序，不混入 Notebook。
- 暂不提供 Notebook 或 Memo 的前端编辑；也不增加 POST 或其他产品写操作。
- 全局 Noting 关闭后，人类只读 API 仍允许查看已有 Notebook、Memo 和 Full Foreground 审计，状态明确显示关闭。
- 这里新增的是人类查看能力，Agent 工具、既有 Slash 与后台任务的关闭规则保持原契约。

### 5. Framework Message 与 Reminder 识别

- Framework Messages 必须有前端能够稳定识别的形式。
- instant Reminder 与 deferred Reminder 也要能区分；用户指出可以按 content 的显式标签包装解析。
- 不依赖英文通知文案猜类型。具体分类字段、事件子类型及包装解析契约尚未冻结。

## API 技术提案：尚未确认

### 读取与事件分工

| 能力 | 当前建议 | 待定内容 |
|---|---|---|
| 当前 Notebook | 按需读取完整有效 Snapshot 的四分区正文，无 Snapshot 明确为空 | HTTP/RPC 方法名、DTO、刷新通知 |
| 当前 Memo | 单独读取有序条目 | 方法名、DTO、变化通知 |
| Noting 状态 | 首次同步完整状态，之后沿现有 WS 推送实际变化 | 初态读取方法、事件名、状态来源、重连同步 |
| Idle 定时器 | 提供绝对预计触发时间 `due_at`，前端计算；变化时同步 | 无定时器原因、时钟偏差校正与观测时间字段 |
| Full Foreground | 按逻辑消息路径分页，消息节点携带 Anchor/Snapshot 附着 | 分页游标、Prelude 返回结构、失效处理 |
| Snapshot 审计详情 | 限定所属 Conversation，读取当时完整版本与相关审计内容 | 独立详情读取还是随 Foreground 页直接携带 |

此前提出的 `/api/sessions/{session_id}/notebook`、`/noting-memo`、`/full-foreground`、`/notebook-snapshots/{snapshot_id}` 只是路径建议；API 不限定 HTTP。此前以短轮询作为 Noting 实时状态主要方案的建议已撤下。

### 状态与倒计时的工程建议

- 状态包含实际活动任务列表，避免把不同 Anchor 的合法并发压成单个 `current_task`；不能仅凭旧数据库 `running` 记录证明任务仍存活。
- 定时器信息建议包含 `due_at` 与后端观测时间，用于前端校准时间差；没有有效定时器时明确无倒计时，不伪造下一次触发时间。
- 到零后显示等待实际结果，不在浏览器自行触发 Noting。真正的任务开始由后端状态事件确认。
- 首次连接、切换会话及重连都重新同步当前状态，避免错过开始/结束事件后卡住；状态未知不能冒充“已结束”。
- 现有 Dashboard 有 `/api/ws` 聊天 JSON-RPC 链路及 `/api/events` 广播链路；后者目前不回放。应按真实 owning host/channel 复用现有链路，补齐必要初态与重连同步，不新建专用 Noting socket。
- Notebook/Memo 的变化可以只推送轻量通知，再按需读取正文。事件名及是否纳入本次范围仍待确认。

### 消息与审计 DTO 建议

- 归属携带 `profile` 和稳定 `conversation_ref`；Session ID 作为现有定位入口。
- 保留原始 `role`、`content`、timestamp、Message Identity 与压缩投影事实。
- Framework/Reminder 分类由后端正式标记或明确包装投影，不改原消息正文；具体 `kind`、`event`、`delivery_mode` 字段为建议。
- Anchor/Snapshot 作为对应消息的审计附着，不新增聊天消息；同 UID 的不同投影需要独立节点键。
- 当前 Notebook 只展示当前有效条目；历史 Snapshot 的版本、归档信息、结束原因和已消费 Memo 属于审计详情。详情字段尚未冻结。
- 所有读取无产品副作用：不启动 Turn、触发 Noting/Schedule、消费 Memo、移动 Snapshot pointer 或写聊天记录。

## 轻量交互建议：尚未确认

悬浮球静息时使用柔和轮廓，点击展开小卡片；执行时点亮，并以缓慢环绕的光点表现后台工作。详情显示真实状态和前端计算的倒计时。倒计时归零后可显示“等待触发结果”，收到实际任务开始事件才点亮；不设置手动触发按钮。

动画强度、减弱动态效果、状态未知的呈现方式，以及详情中除倒计时外显示哪些内容，后续设计时再收口。

## 确认来源

| 口径 | 用户来源 |
|---|---|
| 只读范围与审计展示 | “先都做读取 API，POST 的先不做”；“展示那种消息列……Notebook 锚点以及对应的 Notebook snapshot” |
| 关闭后仍允许读取 | 异步回复：“允许查看已有数据（推荐）” |
| 实时状态复用 WS | “只要我的页面还连接着……状态应该是及时更新的”；“现有的这个 WS 长链路径复用一下” |
| 悬浮球与不手动触发 | “只在 noting task 正在执行的时候亮起”；“静息状态，点开就能显示倒计时”；“暂不设置手动触发 noting” |
| 前端计算倒计时 | “获得定时器的触发预期发一个时间，然后前端自己计算倒计时” |
| 独立文档边界 | “你改现有的冻结文档合适吗？你新开一个文档” |
