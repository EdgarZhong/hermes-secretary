# 第二轮视觉设计交付

依据：冻结 `37ad76f5dfac02d4774d5e0faea55911b5fb8de9` 的 06 全文及派遣所列 02 章节；权限限前端 `src/design/`，不承担导航、模型、网络或业务状态机。本报告记录设计决策及接线契约，不建立平行任务看板。

## 编码前计划与自评

- 主题：长时间阅读、发送真实任务及查看秘书事实的私人聊天工作区。视觉优先顺序是内容、输入、真实状态。
- 六个基础色：Paper `#FFFFFF`、Mist `#F2F5F8`、Ink `#202D3C`、Slate `#5C6B7C`、Harbor `#315F88`、Leaf `#3F705D`。警告与错误作为语义扩展集中定义，不参与装饰。
- 字体：展示位用系统 `Avenir Next` / `Trebuchet MS`，正文用系统 UI 字体，数值和代码用 `SFMono-Regular` / Consolas。无在线字体请求；展示字仅用于 New Chat 欢迎标题，不给消息添加额外字体性格。
- 布局：安静的固定侧栏与可伸缩主区，正文限宽，Composer 与正文同轴；小屏侧栏成为受控抽屉，输入保持底部而非覆盖消息。
- 特征：Secretary Orb 使用克制的双环，只有真实运行态运动；Framework 与两种 Reminder 用文本标签、图标和细边共同区分。它们仍在真实 Timeline 原位。

```text
Desktop                       Mobile
+------------+--------------+ +------------------+
| New Chat   | title        | | Sidebar   title  |
| chats      |              | |                  |
|            |  Timeline    | |    Timeline      |
| Files      |              | |                  |
|            |  Composer   | |    Composer      |
|            |  usage ring | |    usage ring    |
+------------+--------------+ +------------------+
```

自评：装饰渐变、巨型 welcome hero 或独立提醒卡片会让工具变成展示页并分散主任务，因此不采用。白底本身普通，但以真实 carrier 的窄边、克制双环、固定阅读轴形成适合本项目的辨识；不创造新 logo、品牌或产品交互。选择柔和中圆角而非整页胶囊，避免 sidebar、工具和消息拥有同等视觉重量。

## 实现接口、验证与交回

### 七项阶段交回

1. **对应条款**：06 §1.1–1.16 的呈现层与 §4.1–4.4 的设计系统要求；02 指定阅读范围提供身份、Memo、开关和真实 carrier 语义，06 `/notebook` 临时展示增量优先。完整阅读冻结 06、派遣指定 02 章节、根 AGENTS/CLAUDE、本轮索引/基线/计划及 executing-plans、autonomous-run 交接节、frontend-design。
2. **实际变更**：前端 `src/design/{tokens.css,theme.css,primitives.tsx,layout.tsx,chat.tsx,indicators.tsx,files.tsx,index.ts}`。统一语义颜色、字体、间距、圆角、阴影、动效、布局尺寸；没有修改 package、lock、业务源码、后端或权威规格。未 stage、未 commit；前端目前未提交，本阶段精确源码指纹见 `.hermes-dev/round2-evidence/visual/design-sha256.txt`。
3. **正式路径**：`src/design/index.ts` 是单一公开入口并引入两份 CSS。组件已可被正式 App 导入，契约已交给前端 Development；本阶段组件自身完成，但实际 App 接线由 Development 负责，不能据此声称正式用户链路验收完成。页面/网络/状态机/消息来源均未在设计层实现。
4. **验证结果**：前端现有环境运行 `./node_modules/.bin/tsc --noEmit --strict --skipLibCheck --target ES2022 --module ESNext --moduleResolution Bundler --jsx react-jsx --lib ES2022,DOM,DOM.Iterable --types vite/client src/design/index.ts`，退出 0。初版检查通过；补焦点恢复后定向复查通过；最后仅为留档重复一次（小范围编译，不是整版门禁），日志 `.hermes-dev/round2-evidence/visual/design-typecheck.log` 无诊断。WCAG 相对亮度公式计算：Ink/Paper 13.98、Slate/Paper 5.46、Slate/Mist 4.99、Harbor/Paper 6.72、Harbor/selected 5.67、Leaf/Paper 5.70、warning/soft 5.41、danger/soft 5.66，均 ≥4.5:1；这是 token 对比计算，不替代渲染后的完整无障碍验收。无全量构建/测试，无真实浏览器截图。
5. **缺口**：正式接线后须做四视口（1440×900、1024×768、390×844、320×568）截图与交互审查，尤其是长模型名称、长文件名、长工具参数、长 Memo、New Chat/Files/弹层、键盘焦点与滚动。真实移动软键盘、相机和系统侧滑仍按本轮约定后续真机专项验证。组件不证明数据真实、默认展开规则、权限或控制语义。
6. **接口影响**：仅需已有计划允许的 `react`、`@radix-ui/react-dialog`、`@radix-ui/react-popover`、`lucide-react`；无字体 CDN、额外图标/动画库、API/浏览器存储依赖。所有开闭状态通过受控 props；仅 `useId` 与焦点 ref 属于局部呈现机制。CSS 为 `hs-` 前缀，不重置全站 body。业务需让根容器无外边距；Tailwind 的 preflight 可承担此点。
7. **后续动作**：Main review 接收接口，Development 正式接入 assistant-ui runtime 与真实来源；集成完后由视觉 Agent 在同一白名单完成四视口视觉打磨，独立两门禁由主会话统一安排。无待用户确认的产品语义收敛。

### 组件契约与接线要点

| 组件 | 关键输入 / 接线责任 |
|---|---|
| `AppFrame` | `sidebar`、`sidebarOpen`、`onSidebarOpenChange`、children；桌面侧栏与移动 Radix drawer，关闭恢复原焦点。Sidebar 内容用可访问 links/buttons，路由与 aria-current 由应用负责。 |
| `TopNav` | `screen` 联合类型强制 Files 才接受 `onBackToChat`；按钮固定右侧。`onOpenSidebar` 始终对应移动左上。Conversation 的 `trailing` 可放 Orb。 |
| `Sidebar/SidebarSection/SidebarItem` | 用 children 保留 router 的原生链接；selected 仅着色，不进行导航。 |
| `ChatLayout/Timeline/Welcome` | 正文与 dock 同宽，Timeline forwardRef 供业务分页和滚动锚定。无自动滚底。Welcome 未提供 asset 时仅标题，不创造 logo。 |
| `Composer` | `editor/attach/model/reasoning/primaryAction` 插槽；可用 assistant-ui primitive 的 asChild 或原生事件绑定。附件/editBanner/feedback 可选。 |
| `ComposerTextarea/PrimaryAction` | 均 forwardRef；textarea 默认 16px、原生可撤销输入。PrimaryAction 的 `action` 必须由 §1.8 状态矩阵解析，组件不猜状态；发送时忙碌仍显示可取消图标。IME、Enter、Escape 与 admission 锁由业务处理。 |
| `Message/TimelineTime` | `kind` 为纯 UI 呈现类型，不是新增服务端领域对象；kind 必须由真实 carrier 映射。仅 `user` 允许 Reply，`pending` 允许 Withdraw；时间独立兄弟节点，pending 不给时间。Notebook 为 Assistant 形式，显示临时标记。调用方先安全渲染 Markdown 并移除原 timestamp 标记，组件不解析/改写源消息。 |
| `AttachmentChip` | 普通历史附件不传 onRemove、不包链接；图片缩略图必须来自真实已授权 URL/blob。kind 图标由真实扩展名/媒体类型映射。所有 occurrence key 在应用侧。 |
| `Disclosure` | `kind/open/onOpenChange/title/status/children`；Tool 默认折叠、Thinking 活跃展开结束折叠、Compaction 默认折叠全由业务传入，视觉不拥有这些生命周期。 |
| `UsageCard` | `view/onViewChange/metrics`；input/cacheRead/output/cacheHitRate/count 全是可信来源的格式化字符串或 null；null 显示不可用。Session count 是 Turns，Turn count 是 Model calls。固定网格与数值行高，两个切换同尺寸；不算任何计数或比率。 |
| `ContextIndicator` | percent 或 null、compacting、usedLabel/limitLabel、受控 open；压缩态在同尺寸 ring 内替换，展开内容以 Cancel Compaction 代替计数。只有取消仍有意义时传 callback；不画假分类。 |
| `SecretaryOrb` | 仅由业务在 existing Conversation + global on 时渲染；本地 off 不移除。state 只能由真实任务事实提供。finished 的短暂展示时长由业务任务完成事件控制；视觉不启 timer。 |
| `SecretaryStatus/MemoStick` | 一级只 status/localParticipation/nextTriggerLabel/memoCount；二级完整 ordered entries 替换一级，应用不能同时渲染两层。没有写入/控制接口；没有触发时不传 nextTriggerLabel。 |
| `Modal/Popover` | 受控 Radix primitives，提供可见标题/描述、焦点陷阱与恢复；Rewind 两次确认由业务分别调度，组件不代确认。 |
| `FilesLayout/FileList/FileRow/FilePreview` | 原生 href + 可选 onNavigate 保留 browser history；download 只接授权 REST URL；文件内容作为安全 children。EmptyState/Notice 支持加载、空、权限、超限、不支持、404 反馈，不添加任何写操作。 |

```tsx
import {
  AppFrame, TopNav, ChatLayout, Timeline, Composer, ComposerTextarea,
  PrimaryAction, Message, TimelineTime, UsageCard, ContextIndicator,
} from './design';

// state/controller 来自正式应用；设计层不提供这些业务值。
<AppFrame sidebar={sidebar} sidebarOpen={drawerOpen} onSidebarOpenChange={setDrawerOpen}>
  <TopNav screen="conversation" title={title} onOpenSidebar={() => setDrawerOpen(true)} trailing={orb} />
  <ChatLayout composer={
    <Composer
      editor={<ComposerTextarea value={draft} onChange={onDraftChange} onKeyDown={onComposerKeyDown} />}
      attach={attachPopover} model={modelSelector} reasoning={reasoningSelector}
      primaryAction={<PrimaryAction action={resolvedAction} disabled={actionDisabled} onClick={onPrimaryAction} />}
      attachments={attachmentChips} feedback={submissionFeedback}
    />
  } footer={<>{usage}<ContextIndicator {...realContextProps} /></>}>
    <Timeline ref={timelineRef}>{realTimelineNodes}</Timeline>
  </ChatLayout>
</AppFrame>
```

### 样式治理与覆盖边界

- 所有颜色只定义在 tokens.css，theme.css 使用语义变量；组件不含内联颜色、字体选择或页面专属覆盖。常规样式修订回到 token 或共享组件。
- 响应式断点集中 theme.css 的 48rem、23rem 与短屏条件；320px 不隐藏固定 Composer 控件，允许控制栏折行。Sidebar 顶左、Files 返回右上不变。数值宽度恒定，最长内容可滚动/换行。
- safe-area 上下 inset、`100dvh`、触摸目标至少 44px、focus-visible、prefers-reduced-motion、forced-colors 均已实现。`keyboardInsetStyle` 仅接受应用实际观测的遮挡量；应用若已随 visualViewport 缩短高度，不应再重复计算同一遮挡。
- 只含 React/CSS 纯呈现组件及焦点管理，不调用 fetch/WebSocket/IndexedDB/localStorage，不含后端服务、客户端业务数据库或持久 API cache。
- 暂无实际产品截图；设计初版完成 ≠ 四视口通过 ≠ 功能验收通过。

## 第二阶段：正式应用视觉打磨

### 当前环境与边界

本阶段遵守新增 R2-C09 图标约束：仅 favicon 与 New Chat 标题左侧既定图标槽，不增 sidebar/topnav/Orb 图标，不新建主题。R2-C10 不改变呈现权限。前端入口 `http://127.0.0.1:5173`；后端仍是 Main 指定的待更新进程，本阶段不重启、不创建会话、不提交模型 Prompt、不改配置。

2026-10-12 首次启动视觉观察时，本子会话 cua inventory 仅提供 Chrome extension（id 1），没有内置浏览器。`getTab(..., {browser:'iab'})`、`createBrowserTab('iab', ..., {visible:false})` 均返回 `Browser is not available: iab`；按 Main 给出的 id 3 调用 `getBrowser({id:'3'})` 返回 `Browser is not available: 3`。已向 Main 请求可接管的实际内置 tab；未以 Chrome 或其他工具替代规定入口，尚无截图或浏览器布局/console结论。

### 已可独立完成的呈现修正

- Welcome asset 与标题进入同一横向标题容器，asset 在左侧；移动尺寸缩为 32px，桌面 48px。公共 props 不变。
- Usage metrics 固定网格行高与 tabular-nums；detail 统一固定 44px 触发器加 8px 上间距，即使不同数据视图缺省 detail 也保留同高槽。完整说明由业务已接的 Usage details Popover 展示，不挤压输入框。
- 菜单列表、utility row 和选择器统一移入 `theme.css`；portal 内选择器也获得 44px 触摸目标与统一颜色。协调前端 owner 删除 `app.css` 的页面级重复规则和泛化 pre 覆盖，以保留中央代码块横向滚动。
- `design/index.ts` strict TypeScript 定向检查退出 0；日志 `.hermes-dev/round2-evidence/visual/design-stage2-typecheck.log`。这不是实际浏览器验证。

### 用户审图后修订（以当前 Snapshot Index 为准）

- R2-C11–C15：统计悬浮、无副标题、六句标题由业务提供、侧栏最下方 system/light/dark 无文字图标胶囊。配色现仅候选，等待用户网页 AI 方案；蓝灰不得是主要主题色。初版蓝灰与之后暖色都不再视为最终定案。
- New Chat 不显示 Usage/Context 已由用户后续明确确认，业务 owner 条件移除；Welcome 收窄为 `asset? + title:string`，不接受副标题。
- ThemeSelector 为纯 `value/onValueChange`，三个 44px hit area，滑块/焦点/reduced-motion。有效 html `data-theme`、跟随系统及选择持久化由前端唯一 owner 处理。tokens 使用 `light-dark()` 成对定义候选浅/深语义色，未做最终配色验收。
- Main 已明确浮卡的合法布局解释：保留全部常显字段，两卡绝对定位在 Composer 上方；现有 Timeline 内用 padding/scroll-padding 留出末条安全区，不创建 Composer 下的独立高度层，不增加展开/隐藏交互。已照此实现。桌面约 400+84+8px，移动 216+72+8=296px（Context 72px 使 `Compacting` 完整可读）；Usage详情原动作移至卡头 Info 按钮，公共业务语义不变。真实 Conversation 尚未具备观察条件，尺寸与避让仍待实际验证。
- Welcome 与 Composer 组成连续居中区块；Conversation 保留底部输入。菜单行去除重叠卡片边框、Sidebar 空态降为中性文本、Popover 统一段落间距；没有新增页面或状态机。

### 实际图像证据与当前限制

Main 作为同一内置浏览器的操作员，设计 Agent 用本地 view_image 独立审图。首批 `new-base-1024x768.jpg`、`new-base-390x844.jpg` 完整，呈现出标题/输入距离过大的问题，已修正。`new-base-1440x900.jpg` 实际 507×900、`new-base-320x568.jpg` 实际 262×568，被明确判为截图异常，不计完整视口证据。Main 后续 `new-recapture-1440x900.jpg` 与 `new-recapture-320x568.jpg` 已审看为完整对应尺寸，但捕获时 New Chat 统计卡尚未移除，仍不是最终版本。

`new-base-metrics.json` 和 `new-four-viewports.json` 记录首批四视口 DOM 根 scrollWidth 与 viewport 宽度相等，主要按钮 44px；`new-console.json` 为当时 error/warn 空列表。此为历史阶段观察，不能替代后续主题、无卡欢迎页、Files、浮卡与真实会话的最终取证。

最新定向编译日志：`design-theme-typecheck.log`、`design-floating-typecheck.log`，均退出 0。未执行完整构建或模型请求，无 stage/commit。

### 集成截图复核：欢迎页四视口与移动侧栏

本批由 Main 操作正式内置浏览器取证并核实 JPEG 尺寸，视觉 Agent 独立使用 `view_image` 查看全部六张原图：`layout-new-{1440x900,1024x768,390x844,320x568}.jpg`、`layout-drawer-320x568.jpg`、`layout-drawer-light-320x568.jpg`，均位于 `.hermes-dev/round2-evidence/visual/`。

1. **对应要求**：06 的响应式布局、New Chat 与 Composer 呈现，以及当前已确认的标题左侧图标、无副标题、New Chat 不展示统计卡和底部图标主题胶囊。
2. **实际变更**：本批仅审图并补充本报告，没有继续修改产品代码、颜色或公共接口。
3. **正式路径**：截图来自已集成 App 的 New Chat；移动侧栏来自实际打开的 drawer。Main 另观察到主题选择 `system → light → system` 的 checked 状态转换；这是 Main 的交互证据，本 Agent 不将静态截图视为交互机制证明。
4. **本批接收**：四个视口的标题与 Composer 已组成连贯居中区块，桌面阅读宽度克制，手机边距稳定；320px 标题完整、Attach/Model/Reasoning/发送控件保持同排且未裁切；New Chat 已无 Usage/Context 和副标题。320×568 的浅/深侧栏中关闭、新建、Files 和主题三选项均完整可见，底部留白充分，滑块对应当前选项；图中未发现可见水平溢出、遮挡或层级冲突。无需针对这六张图追加布局修补。
5. **明确缺口**：仍须检查已接成熟预览库的 Files 列表/面包屑/内容/返回；Attach、Model、Reasoning 和相关弹层；真实 Conversation 的全部常显 Usage/Context 浮卡及末条消息安全区、长内容和运行状态。尚无本批 DOM overflow/点击目标尺寸与 console 数据，不能沿用历史数据宣称新版全部通过；静态截图也不覆盖键盘焦点、滚动及真机软键盘/相机/系统侧滑。
6. **接口与视觉边界**：欢迎页、侧栏与主题选择器的当前布局接收，不代表候选配色定案；浅/深主题最终色彩和对比仍等待用户网页 AI 方案并在最终主题上复核。没有增加产品交互或改变业务状态所有权。
7. **验证与后续**：本批没有源码变化，不重复运行已通过的 tsc、不跑大型检查。后续在 Main 提供剩余实际产品状态后继续同一白名单的视觉 QA；整体视觉验收仍未完成，不能以本批局部接收替代独立功能 Validation。


## 2026-10-13 表现层收尾与完整 Mock URL 交回

此节是最新事实；前文初版配色、组件形态及“没有浏览器截图”属于初版历史。worktree `/Users/edgar/code/hermes-secretary-web-visual-design`、分支 `codex/visual-design`、基线 `27c5cb4`，保留原有用户视觉成果，未提交、未合并。完整源码指纹、开工快照和收尾差异位于 `.hermes-dev/round2-evidence/visual-finish/{source-manifest.json,before/,finish-only.patch}`。

### 七项交回

1. **对应条款**：06 §1.1–1.10（视觉权威/固定键位/真实Pending）、§1.11（两次明确确认）、§1.14–1.15（只读Orb/Memo）、§4.2–4.7（设计系统/四视口/验收）；02真实完成与只读约束保留。未改权威规格、Core/API/Controller。
2. **实际变更**：finished基础只留柔和阴影，900ms冲击波后无静态绿色glow；SVG内亮在finished→idle用1200ms filter transition渐熄。共享Message进出props接入Mock，两条Pending先220ms收拢再由Mock owner合并涨入。ToastStack新卡顶部入、旧卡下移，无自动消失，叉关闭由owner移除。持续connection在Composer反馈插槽，恢复时移除。Mock Enter仅Send/Steer、Escape仅取消类；Rewind同一dialog两次明确确认。保留New Chat原底部占位，隐藏阶段不挂载Usage/Context交互控件。
3. **正式接口**：`src/design/index.ts`导出ToastStack；`src/design/toasts.tsx`接收`items: readonly {id:string,message:ReactNode,tone?:'neutral'|'error'|'warning'|'success',action?:ReactNode,onDismiss:()=>void}[]`，newest-first，无timeout/存储/网络。持续网络由`Composer.feedback:ReactNode`独立控制。`Message.exiting?:boolean/entering?:boolean`纯动画；另提供`.hs-pending-exit`/`[data-pending-exiting='true']`容器220ms收拢（内部Pending入场禁用），供功能owner权威删除后aria-hidden ghost复用；入场可用Message.entering或`.hs-node-in`。真实RPC不可复制Mock延时；不本地伪造merged history。接口已交给逻辑Development，Main正式接线。
4. **验证**：`npm run build`（包含tsc -b）、`npm run mock:build`、`npm run mock:test`（2文件20例）及`git diff --check`通过；完整日志同证据目录。初次类型检查发现继承视觉API/App不一致：UsageCard缺total、nextTriggerLabel改名，仅修pure props，total=null不猜合计。旧Mock测试期待已移除可见Static Mock标签，改为现有Appearance入口断言，仍检查New Chat无统计控件。因窄屏fixture按钮被Toast覆盖，将“Add notification”移到Mock Composer反馈区；保留原New Chat底部占位后定向复测。没有执行后端全量或真实API测试。构建保留已有文件viewer大chunk提示，未改阈值。
5. **缺口**：这是Mock开发检查，不是独立Verification/Validation；真实toast生命周期、真实Noting完成事实、RPC接线、真机软键盘/相机/侧滑未验。全部103场景SSR挂载；非本次专项浏览器项明确列未验收。旧“51条”只有编号1–42；缺失9条原始记录不在本次输入，不补造。
6. **接口影响**：只用已有React/Radix/lucide与原生Web Animations API，无新依赖/API/业务owner；颜色全部既有var(--hs-*)。App纯视觉修补仅total=null和countdownLabel改名，原logo改动保留。
7. **后续动作**：Main亲自review全部用户差异与收尾，统一提交/合并并正式接toast/connection/Pending/rename；复用此证据，只补实际集成影响，随后独立门禁。

### 浏览器实看与动画中间帧

仅操作localhost:5176 Mock，未触碰53445真实服务。内置浏览器四视口检查：1440×900、1024×768、390×844、320×568；rich conversation/new attachments/toast/stress/files nested/memo long/rewind dialog无页面横向溢出，Composer与dialog均在边界内。最新New Chat保留底部36px占位、无隐藏统计按钮；网络Reconnect后Composer状态移除。

| 实看项 | 观察 | 证据（同visual-finish目录） |
|---|---|---|
| Orb三态 | 98帧；波后只有基础阴影，idle内亮alpha约0.804→0.44→0.235→0.12→0.067 | orb-frames.json、orb-finished-after-wave.jpg |
| Interrupt | 两条Pending opacity 1→0.727→0.489→0.311→最低0.005；再一条combined气泡涨入 | interrupt-frames.json、interrupt-deflate-mid.jpg、interrupt-inflate-mid.jpg |
| Toast | 新卡opacity0入；旧卡translateY(-94px)回0；3卡等6秒仍3卡，叉关闭仅移对应项 | toast-frames.json、toast-in-mid.jpg、toast-dismissed.jpg |
| 键位 | Enter后仍2 pending；Escape后0 pending和一条combined user | keyboard-proof.json |
| Rewind | 第一点击到2/2，未sending；取消保编辑草稿；第二次确认才send | rewind-second-320.jpg、小包20例 |
| 四视口 | 28张代表截图，最新两个变更场景另复验；页面scrollWidth==viewport宽 | four-viewports.json、four-viewports-final-changed.json、场景-宽度.jpg |

![Pending收拢中间帧](/Users/edgar/code/hermes-secretary/.hermes-dev/round2-evidence/visual-finish/interrupt-deflate-mid.jpg)

![320px通知卡片栈](/Users/edgar/code/hermes-secretary/.hermes-dev/round2-evidence/visual-finish/toast-stack-two-320-light.jpg)

### 全量Mock URL（实际catalog枚举103条）

旧清单确有66个不同URL，但不是全量；缺6标题中的后3条、Tools全部7态、Secretary具体5态、Files预览/错误等36条；本次新增toast-stack后共103条。所有URL可点击，theme可替换light/system。每条已做仅指Mock代码与SSR挂载，不是正式真实产品验收；本次专项实看之外保留未验收，未做0条。

[全部场景工作台](http://localhost:5176/mock.html?workbench=1) · [浅色](http://localhost:5176/mock.html?scenario=conversation-rich&theme=light) · [跟随系统](http://localhost:5176/mock.html?scenario=conversation-rich&theme=system)

| 分组 | 场景 | 完成 | 本次Mock浏览器检查 | URL |
|---|---|---|---|---|
| New Chat | new-title-1 · Welcome 1 | 已做 | 未验收 | [new-title-1](http://localhost:5176/mock.html?scenario=new-title-1&theme=dark) |
| New Chat | new-title-2 · Welcome 2 | 已做 | 未验收 | [new-title-2](http://localhost:5176/mock.html?scenario=new-title-2&theme=dark) |
| New Chat | new-title-3 · Welcome 3 | 已做 | 未验收 | [new-title-3](http://localhost:5176/mock.html?scenario=new-title-3&theme=dark) |
| New Chat | new-title-4 · Welcome 4 | 已做 | 未验收 | [new-title-4](http://localhost:5176/mock.html?scenario=new-title-4&theme=dark) |
| New Chat | new-title-5 · Welcome 5 | 已做 | 未验收 | [new-title-5](http://localhost:5176/mock.html?scenario=new-title-5&theme=dark) |
| New Chat | new-title-6 · Welcome 6 | 已做 | 未验收 | [new-title-6](http://localhost:5176/mock.html?scenario=new-title-6&theme=dark) |
| New Chat | new-text · Text draft | 已做 | 未验收 | [new-text](http://localhost:5176/mock.html?scenario=new-text&theme=dark) |
| New Chat | new-attachments · Attachments draft | 已做 | 专项实看 | [new-attachments](http://localhost:5176/mock.html?scenario=new-attachments&theme=dark) |
| Timeline | conversation-rich · Rich conversation | 已做 | 专项实看 | [conversation-rich](http://localhost:5176/mock.html?scenario=conversation-rich&theme=dark) |
| Timeline | conversation-live · Live turn · streaming | 已做 | 未验收 | [conversation-live](http://localhost:5176/mock.html?scenario=conversation-live&theme=dark) |
| Timeline | message-image · Image in history | 已做 | 未验收 | [message-image](http://localhost:5176/mock.html?scenario=message-image&theme=dark) |
| Timeline | conversation-long · Long history / title | 已做 | 未验收 | [conversation-long](http://localhost:5176/mock.html?scenario=conversation-long&theme=dark) |
| Timeline | conversation-empty · Empty conversation | 已做 | 未验收 | [conversation-empty](http://localhost:5176/mock.html?scenario=conversation-empty&theme=dark) |
| Timeline | conversation-loading · History loading | 已做 | 未验收 | [conversation-loading](http://localhost:5176/mock.html?scenario=conversation-loading&theme=dark) |
| Timeline | conversation-error · History error | 已做 | 未验收 | [conversation-error](http://localhost:5176/mock.html?scenario=conversation-error&theme=dark) |
| Thinking | thinking-active · Active / expanded | 已做 | 未验收 | [thinking-active](http://localhost:5176/mock.html?scenario=thinking-active&theme=dark) |
| Thinking | thinking-complete · Complete / collapsed | 已做 | 未验收 | [thinking-complete](http://localhost:5176/mock.html?scenario=thinking-complete&theme=dark) |
| Thinking | thinking-interrupted · Interrupted | 已做 | 未验收 | [thinking-interrupted](http://localhost:5176/mock.html?scenario=thinking-interrupted&theme=dark) |
| Tools | tool-constructing · constructing | 已做 | 未验收 | [tool-constructing](http://localhost:5176/mock.html?scenario=tool-constructing&theme=dark) |
| Tools | tool-running · running | 已做 | 未验收 | [tool-running](http://localhost:5176/mock.html?scenario=tool-running&theme=dark) |
| Tools | tool-complete · complete | 已做 | 未验收 | [tool-complete](http://localhost:5176/mock.html?scenario=tool-complete&theme=dark) |
| Tools | tool-failed · failed | 已做 | 未验收 | [tool-failed](http://localhost:5176/mock.html?scenario=tool-failed&theme=dark) |
| Tools | tool-interrupted · interrupted | 已做 | 未验收 | [tool-interrupted](http://localhost:5176/mock.html?scenario=tool-interrupted&theme=dark) |
| Tools | tool-unknown · unknown | 已做 | 未验收 | [tool-unknown](http://localhost:5176/mock.html?scenario=tool-unknown&theme=dark) |
| Tools | tool-action · Needs user action | 已做 | 未验收 | [tool-action](http://localhost:5176/mock.html?scenario=tool-action&theme=dark) |
| Carriers | carriers-all · Framework + reminders | 已做 | 未验收 | [carriers-all](http://localhost:5176/mock.html?scenario=carriers-all&theme=dark) |
| Carriers | compaction-summary · Separate summary | 已做 | 未验收 | [compaction-summary](http://localhost:5176/mock.html?scenario=compaction-summary&theme=dark) |
| Carriers | compaction-composite · Composite carrier | 已做 | 未验收 | [compaction-composite](http://localhost:5176/mock.html?scenario=compaction-composite&theme=dark) |
| Carriers | compaction-no-text · No textual handoff | 已做 | 未验收 | [compaction-no-text](http://localhost:5176/mock.html?scenario=compaction-no-text&theme=dark) |
| Pending | pending-multiple · Multiple accepted steers | 已做 | 未验收 | [pending-multiple](http://localhost:5176/mock.html?scenario=pending-multiple&theme=dark) |
| Pending | stream-steer · Streaming + steer | 已做 | 未验收 | [stream-steer](http://localhost:5176/mock.html?scenario=stream-steer&theme=dark) |
| Rename | rename-demo · Typewriter rename | 已做 | 未验收 | [rename-demo](http://localhost:5176/mock.html?scenario=rename-demo&theme=dark) |
| Pending | pending-consumed · Same-point consumed | 已做 | 未验收 | [pending-consumed](http://localhost:5176/mock.html?scenario=pending-consumed&theme=dark) |
| Pending | pending-race · Withdraw unknown | 已做 | 未验收 | [pending-race](http://localhost:5176/mock.html?scenario=pending-race&theme=dark) |
| Primary action | primary-disabled · Idle · Send disabled | 已做 | 未验收 | [primary-disabled](http://localhost:5176/mock.html?scenario=primary-disabled&theme=dark) |
| Primary action | primary-send · Idle · Send | 已做 | 未验收 | [primary-send](http://localhost:5176/mock.html?scenario=primary-send&theme=dark) |
| Primary action | primary-send-attachments · Idle · attachment-only Send | 已做 | 未验收 | [primary-send-attachments](http://localhost:5176/mock.html?scenario=primary-send-attachments&theme=dark) |
| Primary action | primary-steer · Active · text-only Steer | 已做 | 未验收 | [primary-steer](http://localhost:5176/mock.html?scenario=primary-steer&theme=dark) |
| Primary action | primary-stop · Active · empty Stop | 已做 | 未验收 | [primary-stop](http://localhost:5176/mock.html?scenario=primary-stop&theme=dark) |
| Primary action | primary-stop-attachments · Active · attachments Stop | 已做 | 未验收 | [primary-stop-attachments](http://localhost:5176/mock.html?scenario=primary-stop-attachments&theme=dark) |
| Primary action | primary-interrupt · Active · pending Interrupt | 已做 | 专项实看 | [primary-interrupt](http://localhost:5176/mock.html?scenario=primary-interrupt&theme=dark) |
| Primary action | primary-interrupt-attachments · Active · attachments + pending | 已做 | 未验收 | [primary-interrupt-attachments](http://localhost:5176/mock.html?scenario=primary-interrupt-attachments&theme=dark) |
| Primary action | primary-cancel-send · Pre-admission · Cancel Send | 已做 | 未验收 | [primary-cancel-send](http://localhost:5176/mock.html?scenario=primary-cancel-send&theme=dark) |
| Feedback | send-failed · Send failed | 已做 | 未验收 | [send-failed](http://localhost:5176/mock.html?scenario=send-failed&theme=dark) |
| Feedback | toast-stack · Persistent notification stack | 已做 | 专项实看 | [toast-stack](http://localhost:5176/mock.html?scenario=toast-stack&theme=dark) |
| Feedback | admission-unknown · Admission unknown | 已做 | 未验收 | [admission-unknown](http://localhost:5176/mock.html?scenario=admission-unknown&theme=dark) |
| Feedback | disconnected · Disconnected | 已做 | 专项实看 | [disconnected](http://localhost:5176/mock.html?scenario=disconnected&theme=dark) |
| Feedback | recovering · Reconnecting | 已做 | 未验收 | [recovering](http://localhost:5176/mock.html?scenario=recovering&theme=dark) |
| Rewind | rewind-entry · Reply editing | 已做 | 未验收 | [rewind-entry](http://localhost:5176/mock.html?scenario=rewind-entry&theme=dark) |
| Rewind | rewind-confirm-1 · First confirmation | 已做 | 专项实看 | [rewind-confirm-1](http://localhost:5176/mock.html?scenario=rewind-confirm-1&theme=dark) |
| Rewind | rewind-confirm-2 · Second confirmation | 已做 | 专项实看 | [rewind-confirm-2](http://localhost:5176/mock.html?scenario=rewind-confirm-2&theme=dark) |
| Usage / Context | usage-session · Session Total | 已做 | 未验收 | [usage-session](http://localhost:5176/mock.html?scenario=usage-session&theme=dark) |
| Usage / Context | usage-turn · Latest completed Turn | 已做 | 未验收 | [usage-turn](http://localhost:5176/mock.html?scenario=usage-turn&theme=dark) |
| Usage / Context | usage-unknown · Usage unavailable | 已做 | 未验收 | [usage-unknown](http://localhost:5176/mock.html?scenario=usage-unknown&theme=dark) |
| Usage / Context | context-unknown · Context unknown | 已做 | 未验收 | [context-unknown](http://localhost:5176/mock.html?scenario=context-unknown&theme=dark) |
| Usage / Context | compacting · Compacting / cancel | 已做 | 未验收 | [compacting](http://localhost:5176/mock.html?scenario=compacting&theme=dark) |
| Usage / Context | compaction-too-late · Cancel too late | 已做 | 未验收 | [compaction-too-late](http://localhost:5176/mock.html?scenario=compaction-too-late&theme=dark) |
| Secretary | secretary-global-off · Global off · no Orb | 已做 | 未验收 | [secretary-global-off](http://localhost:5176/mock.html?scenario=secretary-global-off&theme=dark) |
| Secretary | orb-loop · Orb three-state loop | 已做 | 专项实看 | [orb-loop](http://localhost:5176/mock.html?scenario=orb-loop&theme=dark) |
| Secretary | secretary-local-off · Local off · Orb retained | 已做 | 未验收 | [secretary-local-off](http://localhost:5176/mock.html?scenario=secretary-local-off&theme=dark) |
| Secretary | secretary-idle · idle | 已做 | 未验收 | [secretary-idle](http://localhost:5176/mock.html?scenario=secretary-idle&theme=dark) |
| Secretary | secretary-active · active | 已做 | 未验收 | [secretary-active](http://localhost:5176/mock.html?scenario=secretary-active&theme=dark) |
| Secretary | secretary-finished · finished | 已做 | 未验收 | [secretary-finished](http://localhost:5176/mock.html?scenario=secretary-finished&theme=dark) |
| Secretary | secretary-error · error | 已做 | 未验收 | [secretary-error](http://localhost:5176/mock.html?scenario=secretary-error&theme=dark) |
| Secretary | secretary-unknown · unknown | 已做 | 未验收 | [secretary-unknown](http://localhost:5176/mock.html?scenario=secretary-unknown&theme=dark) |
| Secretary | secretary-memo · Memo replacement layer | 已做 | 未验收 | [secretary-memo](http://localhost:5176/mock.html?scenario=secretary-memo&theme=dark) |
| Secretary | secretary-memo-empty · Empty memo | 已做 | 未验收 | [secretary-memo-empty](http://localhost:5176/mock.html?scenario=secretary-memo-empty&theme=dark) |
| Secretary | secretary-memo-long · Long memo | 已做 | 专项实看 | [secretary-memo-long](http://localhost:5176/mock.html?scenario=secretary-memo-long&theme=dark) |
| Slash / temporary | notebook · Notebook four sections | 已做 | 未验收 | [notebook](http://localhost:5176/mock.html?scenario=notebook&theme=dark) |
| Slash / temporary | notebook-none · No Snapshot | 已做 | 未验收 | [notebook-none](http://localhost:5176/mock.html?scenario=notebook-none&theme=dark) |
| Slash / temporary | slash · Command suggestions | 已做 | 未验收 | [slash](http://localhost:5176/mock.html?scenario=slash&theme=dark) |
| Slash / temporary | command-result · Ordinary command result | 已做 | 未验收 | [command-result](http://localhost:5176/mock.html?scenario=command-result&theme=dark) |
| Files | files-root · Root list | 已做 | 未验收 | [files-root](http://localhost:5176/mock.html?scenario=files-root&theme=dark) |
| Files | files-nested · Deep folder list | 已做 | 专项实看 | [files-nested](http://localhost:5176/mock.html?scenario=files-nested&theme=dark) |
| Files | files-text · Text · wrapped long line | 已做 | 未验收 | [files-text](http://localhost:5176/mock.html?scenario=files-text&theme=dark) |
| Files | files-markdown · Markdown | 已做 | 未验收 | [files-markdown](http://localhost:5176/mock.html?scenario=files-markdown&theme=dark) |
| Files | files-image · Image | 已做 | 未验收 | [files-image](http://localhost:5176/mock.html?scenario=files-image&theme=dark) |
| Files | files-pdf · PDF | 已做 | 未验收 | [files-pdf](http://localhost:5176/mock.html?scenario=files-pdf&theme=dark) |
| Files | files-word · Word | 已做 | 未验收 | [files-word](http://localhost:5176/mock.html?scenario=files-word&theme=dark) |
| Files | files-sheet · Spreadsheet | 已做 | 未验收 | [files-sheet](http://localhost:5176/mock.html?scenario=files-sheet&theme=dark) |
| Files | files-slides · Slides | 已做 | 未验收 | [files-slides](http://localhost:5176/mock.html?scenario=files-slides&theme=dark) |
| Files | files-code · Code | 已做 | 未验收 | [files-code](http://localhost:5176/mock.html?scenario=files-code&theme=dark) |
| Files | files-json · JSON | 已做 | 未验收 | [files-json](http://localhost:5176/mock.html?scenario=files-json&theme=dark) |
| Files | files-yaml · YAML | 已做 | 未验收 | [files-yaml](http://localhost:5176/mock.html?scenario=files-yaml&theme=dark) |
| Files | files-csv · CSV | 已做 | 未验收 | [files-csv](http://localhost:5176/mock.html?scenario=files-csv&theme=dark) |
| Files | files-html · HTML | 已做 | 未验收 | [files-html](http://localhost:5176/mock.html?scenario=files-html&theme=dark) |
| Files | files-jpeg · JPEG image | 已做 | 未验收 | [files-jpeg](http://localhost:5176/mock.html?scenario=files-jpeg&theme=dark) |
| Files | files-audio · Audio | 已做 | 未验收 | [files-audio](http://localhost:5176/mock.html?scenario=files-audio&theme=dark) |
| Files | files-video · Video | 已做 | 未验收 | [files-video](http://localhost:5176/mock.html?scenario=files-video&theme=dark) |
| Files | files-unsupported · Unsupported binary | 已做 | 未验收 | [files-unsupported](http://localhost:5176/mock.html?scenario=files-unsupported&theme=dark) |
| Files states | files-empty · empty | 已做 | 未验收 | [files-empty](http://localhost:5176/mock.html?scenario=files-empty&theme=dark) |
| Files states | files-loading · loading | 已做 | 未验收 | [files-loading](http://localhost:5176/mock.html?scenario=files-loading&theme=dark) |
| Files states | files-permission · permission | 已做 | 未验收 | [files-permission](http://localhost:5176/mock.html?scenario=files-permission&theme=dark) |
| Files states | files-notfound · notfound | 已做 | 未验收 | [files-notfound](http://localhost:5176/mock.html?scenario=files-notfound&theme=dark) |
| Files states | files-oversized · oversized | 已做 | 未验收 | [files-oversized](http://localhost:5176/mock.html?scenario=files-oversized&theme=dark) |
| Files states | files-direct-entry · Direct Files entry | 已做 | 未验收 | [files-direct-entry](http://localhost:5176/mock.html?scenario=files-direct-entry&theme=dark) |
| Overlays | sidebar · Sidebar drawer | 已做 | 未验收 | [sidebar](http://localhost:5176/mock.html?scenario=sidebar&theme=dark) |
| Overlays | attach · Attach entries | 已做 | 未验收 | [attach](http://localhost:5176/mock.html?scenario=attach&theme=dark) |
| Overlays | model · Model selection | 已做 | 未验收 | [model](http://localhost:5176/mock.html?scenario=model&theme=dark) |
| Overlays | reasoning · Reasoning selection | 已做 | 未验收 | [reasoning](http://localhost:5176/mock.html?scenario=reasoning&theme=dark) |
| Overlays | confirmation · User confirmation | 已做 | 未验收 | [confirmation](http://localhost:5176/mock.html?scenario=confirmation&theme=dark) |
| Stress | stress-small · Small-screen content | 已做 | 专项实看 | [stress-small](http://localhost:5176/mock.html?scenario=stress-small&theme=dark) |
| Stress | stress-files · Long file name / path | 已做 | 未验收 | [stress-files](http://localhost:5176/mock.html?scenario=stress-files&theme=dark) |

### 用户反馈逐条对账（实际42条，不冒称51条）

保留原编号1–42。已做的用户视觉成果不重写；未专项验收指本次未重复动效参数专项。无原始记录的43–51不虚构。

| # | 要求 | 当前状态 |
|---|---|---|
| 1 | 移动端 new chat 标题渲染逻辑错，icon 应作为文字参与排版、整体居中 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 2 | icon 不能压到和文字一样高，要略大 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 3 | 标题整体居中 + 自动换行 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 4 | 标题到画布边缘留距，宁可换行也不顶满 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 5 | 光晕轨迹不得出画布；resize 时只受迫改横坐标、速度不变 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 6 | 用速度而非轨迹建模、加约束；缩放时保持相对位置 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 7 | 加第三个光源，黄/绿/蓝三色都用色卡 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 8 | 桌面端光晕有效半径偏小、速度偏慢 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 9 | 初始三光源太聚，要分散 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 10 | 移动端作用半径仍偏小 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 11 | 游走范围偏保守、移动端常聚在一起；应用"比例速度" | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 12 | Composer 副容器不透明，在 New Chat 遮盖光晕、出现灰色截断 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 13 | 新建页 composer 太靠下，整体上抬 | 已做；底部占位保留，四视口与Conversation底边一致。 |
| 14 | attachment 时 composer 原地形变：锁底边、向上长高，其余不动 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 15 | attachment 移动端不得竖排，要单行 + 左右滚动、无滚动条、无分割线 | 已做；四视口横排/局部横滚。 |
| 16 | compacting 时 usage 胶囊位置不得错动，Context 胶囊向右伸展 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 17 | "Compacting" 要流光动效（Codex 那种），不是呼吸 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 18 | Compacting 圆环每转一圈复位 → 应无缝持续转 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 19 | cancel-send 不得在按钮内部转圈，统一到外侧半透明环槽 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 20 | pending 消息看不到撤回按钮，应放在气泡**左侧贴着** | 已做；常驻Withdraw，Interrupt场景实看。 |
| 21 | pending 气泡根部比普通气泡更靠左，应与普通气泡竖对齐 | 已做；既有对齐保留，四视口实看。 |
| 22 | Reply 符号应在气泡**下方靠根部**，且仅 hover 显示 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 23 | Withdraw 常驻、Reply 隐藏，两者显示逻辑不同 | 已做（继承用户既有视觉成果）；本次未专项验收，旧证据保留。 |
| 24 | assistant 右间距 = 用户气泡左沟槽，形成交错 | 已做；保留assistant右clamp(24px,6%,64px)，未改口径。 |
| 25 | "最大间距啊，都是最大间距，气泡不必顶满" | 20%历史方案已被后续覆盖，未重新实施。 |
| 26 | 20% 看不出来（桌面端） | 历史问题已被后续覆盖，未回改20%。 |
| 27 | 应该是宽侧 15% / 窄侧 5%（按 timeline 内容宽） | 未做15%；最终15%未授权，保留现6%/5%。 |
| 28 | assistant 左间距小了、右间距大了，右边距再调小 | 已做；保留当前6%/5%布局。 |
| 29 | "现在分别都是多少？统一用父容器宽度百分比说话" | 已回答：assistant右margin=clamp(24px,父容器宽6%,64px)；user max-width95%故至少5%左沟槽，短气泡空白更大；小屏clamp下限实际占比高于6%。 |
| 30 | 两条主过渡至今没看到（new chat→conversation、pending 合并入气泡） | 已做；Interrupt中间帧完成；New Chat发送过渡既有实现保留，未重做完整专项验收。 |
| 31 | 会话重命名逐字动效 + 事件触发接口 | 已做；rename-demo/事件接口保留，本次未专项验收。 |
| 32 | 流式输出 + steer 永不注入（长链场景） | 已做；stream-steer保留，本次未重做长链专项验收。 |
| 33 | Interrupt 触发的 pending 合并 / 气泡放入动效 | 已做/专项实看：220ms收拢，再combined气泡涨入。 |
| 34 | Rewind 不要双层确认，合并为一层，按钮用红色 | 已做：同一dialog两阶段红色确认；仍须两次deliberate confirmations，不能单点击截断。 |
| 35 | Tool 外层标题显示工具类型：原生工具名 / MCP | 已做；7态全部URL补齐，未专项浏览器验收。 |
| 36 | 画布更新自动滚底；用户手动滚动后 30s 冻结 | 已做；原自动滚底/手动30s冻结保留，未专项验收。 |
| 37 | 报错提示改成顶部卡片、不自动消失、点叉关闭、多条下顶 | 已做/专项实看：顶部持久卡片栈/叉关闭/旧卡下移。 |
| 38 | 把最近要的 3 个链接给我 + stream-steer 链接 + interrupt 过渡链接 | 已交付103条可点击URL，含rename/stream-steer/primary-interrupt。 |
| 39 | 这一层是否涉及表现层以下的界限？涉及就汇报 | 已汇报纯组件/业务owner消失时机与网络恢复边界，见接口。 |
| 40 | 持续态（disconnected/reconnecting）放输入框、一次性通知走横幅 | 已做/实看：持续connection在Composer，恢复移除；一次性Toast留栈。 |
| 41 | 写一份 prompt 让 coding agent 查清下层接线 | 已有codex-handoff-prompt.md交付且Main启动接线；不另建文档。 |
| 42 | 悬浮球三态流转：冲击波后外圈光晕又亮一下（本会话新反馈） | 已做/98帧实看：波后无外圈回闪，内亮渐熄。 |

收尾补充：动画中间截图实看发现父画布 `overflow:hidden` 可被浏览器焦点自动滚动，导致顶栏移出屏幕、底部留白。已以纯样式将 `.hs-app/.hs-app__main` 改为 `overflow:clip`，仅Timeline仍滚动；不是新增业务状态或滚动owner。最终100帧Interrupt重采样保留收拢/涨入；四视口实际点击后appScroll/mainScroll均0、navTop均0、Composer bottom分别852/720/808/532，证据 `canvas-scroll-four-viewports.json` 与 `interrupt-after-宽度.jpg`。构建按这一最终CSS版本重做，未重跑后端或前端完整业务suite。

Mock取消优先级最终对齐真实组件：Escape先关闭overlay，再执行当前Cancel Send/Stop/Interrupt，仅无取消动作时退出Rewind编辑。实测Rewind两次确认→模拟Send未admission→Escape，回到Send、编辑文本和Reply banner仍在；不会把发送中误当退出编辑。证据`rewind-cancel-send-proof.txt`/`rewind-cancel-send.jpg`。final build/mock-build日志对应这一最终源码。
