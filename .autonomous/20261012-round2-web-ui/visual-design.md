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
