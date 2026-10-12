# 全场景静态 Mock 交接

依据：冻结 06 divisions 0–4、02 指派章节、Snapshot Index C11–C21。Mock 是可交互的合成呈现，零后端、零模型；不能作为真实功能验收。颜色沿用现有 `src/design`，当前候选不是主题定案。

## 施工前场景矩阵

每行对应独立可定位场景或同组明确变体；目录由 `src/mock/catalog.ts` 管理。控制层位于产品画布外，仍只有 New Chat / Conversation / Files 三种产品页面。

| 组 / 入口 | 精确覆盖 | 交互与判断 |
|---|---|---|
| new / new-title-1…6、new-text、new-attachments | 六标题无副标题；空、文本、图片/普通文件/重复文件名 | 无 Usage/Context/Orb；Attach 可移除本地合成附件；输入启用 Send |
| conversation / conversation-rich、conversation-long | 普通 Markdown、代码、表格、历史日期分组、长标题/内容 | 时间在气泡外；历史加载只增加合成前文；无头像 |
| thinking / thinking-active、thinking-complete | active 默认展开；complete 默认折叠 | Disclosure 可切换，不代表整 Turn 结束 |
| tools / tool-constructing、running、complete、failed、interrupted、unknown、action | 七种工具状态 | 默认折叠；展开参数/结果；需用户动作展示真实类型的合成审批/澄清呈现 |
| carriers / carriers-all、compaction-summary、composite、no-text | Framework Finish/Force/External 原文；instant；deferred batch；独立/组合/无文本 compaction | 使用对应正式消息与 Disclosure；不误标 Assistant，不制造无文本压缩消息 |
| pending / pending-multiple、pending-consumed、pending-race | 多 occurrence、同点消费为单条、无法撤回 | Withdraw 覆盖草稿；消费移除尾部临时气泡；新增 stream 位于 pending 前 |
| primary / primary-disabled、send、steer、stop、stop-attachments、interrupt、interrupt-attachments、cancel-send | 完整优先表；active 有附件/有 pending | 只一个正式 PrimaryAction；Stop 保留草稿，Interrupt 只消费 pending；Cancel 恢复捕获草稿 |
| feedback / send-failed、admission-unknown、disconnected、recovering | 发送失败、准入未知、断线、恢复中 | 保留草稿；unknown 不可盲重发；恢复按钮仅模拟状态重建 |
| rewind / rewind-entry、confirm-1、confirm-2 | 隐藏源 User 及后续、退出恢复、两次确认 | 正式 RewindBanner/Modal；确认后仅改本地合成节点，无后端截断 |
| usage / usage-session、turn、unknown、context-unknown、compacting、compaction-too-late | 两 scope 稳定尺寸、未知；Context ring/详情/取消 | Usage tabs；压缩取消只改变模拟 compaction，不改变 active Turn |
| secretary / secretary-global-off、local-off、idle、active、finished、error、unknown、memo、memo-empty、memo-long | Global off 无 Orb；local off 保留；五状态；Status→Memo 完整替换 | 正式 Orb/Status/Memo；无编辑/运行按钮；local off fixture memo 必须为空 |
| slash / notebook、notebook-none、slash、command-result | 当前四节 Notebook/无 Snapshot、时间/无 Anchor；目录/普通结果 | human-only 临时 Assistant 呈现，不持久；普通 /help 不误标 Notebook |
| files / files-root、nested、text、markdown、image、pdf、word、sheet、slides、code、json、yaml、csv、html、jpeg、audio、video | 列表、多层真实路径、16 个常见代表本地合成文件 | 正式 list/breadcrumb/preview + 纯本地成熟 viewer；根强调色；Back to Chat 直接恢复草稿 |
| files-states / empty、loading、permission、notfound、oversized、unsupported | 必需错误与空状态 | retry 切换合成状态；不读真实路径；download 只本地合成 fixture |
| overlays / sidebar、attach、model、reasoning、confirmation | sidebar/Attach 3入口/模型/推理/slash/确认 | 正式 Radix popover/dialog；可点击，不接真实设备与配置 |
| stress / stress-small、stress-files、memo-long | 长标题/文件名/长 memo/小屏 | 四真实 iframe 尺寸预设；实际宿主浏览器视口由 Main 验证 |

## 边界与组件来源

前端白名单为 `src/mock/**`、`mock.html`、`vite.mock.config.ts`、`public/mock-fixtures/**`。无 package/lock、正式产品源文件、根文档、规格修改；无 stage/commit/worktree。唯一正式组件外部复用接口为 `src/components/FileViewerPreview.tsx` 的纯 `{file: File, theme}`，已由 Main 确认无网络或业务状态依赖。

正式设计来源统一 `src/design/index.ts`。Mock CSS 仅负责开发工作台/iframe、成熟预览器宿主与独有布局缝隙，使用正式语义 tokens，不覆盖正式卡片颜色。视觉 Agent 后续可修改 `src/design/**`；不应把 Mock fixtures、模拟 state owner 合并进产品逻辑。

## 完整阶段返回报告

1. 条款：以上矩阵与 06 §1.1–1.16、§4.2–4.3；C11–C21。
2. 实际变更：前端 30 个新增源/资源文件（`src/mock` 12、两入口/配置、16 个 fixture）。96 个独立场景，包含三产品页、全部指定状态与交互。后端仅本报告与 ignored 证据。无 stage/commit/worktree、根文档、规格、package/lock 或正式产品源修改。
3. 静态装配入口：`mock.html` → `src/mock/main.tsx` → Workbench 或 MockStage。Workbench 是开发控制层，不是第四产品页；产品 iframe 内仍只有三页。所有通用卡片直接从 `src/design/index.ts` 导入，Files 异步导入已获准的纯 File viewer。模拟状态全部归 `state.ts::reduceMock`，无真实 domain 执行器。只允许读取 `/mock-fixtures/*` 静态资源；无 API/WS、认证、真实草稿写入、localStorage/IndexedDB 或模型调用。
4. 验证结果：Mock 专属 TypeScript strict 检查 PASS；两测试文件 20 项 PASS（617ms），包括所有 96 场景实际组件 SSR 装配、七类 Tool、Thinking 默认态、no-text 无伪压缩消息、完整 primary 表、Stop/Interrupt/Withdraw/Cancel/Rewind/Files/压缩取消的实际 reducer 变化。最终 Vite 静态构建 PASS（5.32s）；预览库大 chunk 提示保留，没有放宽阈值。HTTP root 302 → mock.html、独立 HTML 200、本地 PDF 200。当前服务在 5174，exec session `78282`，日志见下。SSR 不等于真实浏览器交互/布局验收。
5. 缺口与限制：真实 API/模型/持久草稿/设备能力不在 Mock 内验证；成熟库在浏览器中对 PDF/Office/音视频的实际显示、Radix 自动定位、四宿主视口视觉与触摸可用性尚待 Main 检查。Mock 模型/Reasoning/slash catalog 是明确标识的合成选项，不证明后端支持；Take Photo 只添加合成图片，不调用设备。结束 Highlight 5 秒后退回 idle，工作台可重复触发。主题沿用现有候选 tokens，未定案新色系。
6. 接口影响：正式产品零修改；Main 接线 npm script 与构建目录忽略。预览插件按已批准同版配置自动复制 9 个 renderer 资产到既有 ignored `public/file-viewer/`；这些生成文件不纳入源文件清单。最终 Mock 构建目录已从前端移入后端 ignored 证据 `mock/dist/`，避免误提交生成资源。
7. 后续动作：Main review、内置浏览器四视口与本地预览检查；前端源阶段快照后创建独立视觉 worktree。视觉 Agent 可集中调整正式 `src/design/**` 的 tokens/组件布局和 Mock fixtures 的呈现内容；不得修改 controller/core/网络/业务权限、固定动作矩阵、三产品页边界或真实文件接口。视觉树改动由 Main review 后回收，不混入模拟 state owner 的产品实现。

## 启动与定位

前端根目录直接运行（无需后端）：

```bash
./node_modules/.bin/vite --config vite.mock.config.ts --host 127.0.0.1
```

默认入口 `http://127.0.0.1:5174/mock.html`；根 `/` 和 `/index.html` 自动转入该入口，不启动真实 App。工作台包含可搜索的 96 场景分类选择、Reset、system/light/dark、四精确 iframe 尺寸与 Fit window、可折叠 Simulate 控制层、Open canvas。Simulate 按钮仅在产品画布外推进合成状态。

直接画布格式：`http://127.0.0.1:5174/mock.html?embedded=1&scenario=<id>&theme=light`。例如 `conversation-rich`、`primary-interrupt-attachments`、`rewind-confirm-2`、`secretary-memo-long`、`files-word`、`stress-small`。独立画布适合 Main 在宿主实际 1440×900 / 1024×768 / 390×844 / 320×568 下验收；工作台 iframe 是便捷设计预览，不能冒称宿主验收。

建议 Main 新增 package scripts（本 Agent 未改 package）：

```json
{
  "mock": "vite --config vite.mock.config.ts --host 127.0.0.1",
  "mock:build": "vite build --config vite.mock.config.ts",
  "mock:test": "vitest run --config vite.mock.config.ts src/mock"
}
```

并把 `dist-mock/` 加入前端 `.gitignore`。独立 worktree 沿用 package-lock，安装既有依赖即可；本地 Office renderer 和 worker 资产由同版 plugin 自动复制，无公网 Office 传文档。

## 证据与文件哈希

证据根为 `/Users/edgar/code/hermes-secretary/.hermes-dev/round2-evidence/mock/`：

| 文件 | 内容 |
|---|---|
| `scenario-catalog.json` | 96 场景 id/分类/标签/说明/直接 URL；源目录为前端 `src/mock/catalog.ts`，跨工作树可直接复用 |
| `file-hashes.json` | 全部 30 个新增前端源/fixture 的相对路径与 SHA256 |
| `dependency-hashes.json` | 未修改正式 design、FileViewerPreview、package/lock 的取证哈希 |
| `entry-module-graph.json` | esbuild 实际入口模块依赖；项目源仅 Mock + design + FileViewerPreview；审计时 virtual renderer external，正式 Vite 构建仍完整注入 |
| `typecheck.log` | 无诊断，命令 exit 0 |
| `tests.log` | 20 项最终 PASS，包括 96 场景 SSR 装配 |
| `build.log`、`dist/` | 最终静态构建日志与产物；库的大 chunk 提示诚实保留 |
| `readiness.json`、`dev-server.log` | 独立静态服务的入口/资源响应及运行日志 |

定向类型检查使用：

```bash
./node_modules/.bin/tsc --noEmit --target ES2022 --lib ES2022,DOM,DOM.Iterable --module ESNext --moduleResolution Bundler --jsx react-jsx --strict --skipLibCheck --types vite/client src/mock/main.tsx src/mock/state.test.ts src/mock/render.test.tsx src/env.d.ts src/file-viewer.d.ts vite.mock.config.ts
```

测试和构建各因新增代表场景、入口隔离与局部状态拆分做了定向复测，最终只引用最新源码证据；未运行全量产品 suite、Python suite 或真实后端。没有通过 Mock 结果宣布 Web UI、Secretary Core 或本轮独立门禁完成。

## Main 集成复核（阶段快照之后）

Main 已亲读独立入口/Vite、Stage、Timeline、Composer、Files、state owner与组件复用关系，并实际打开5176工作台、切换Pending及320预设。30源哈希中仅合成长文本的已知行尾空格清理、以及本次Mock Escape微修不同。Escape在active有输入时不得调用primary模拟Steer，现已改为停止模拟Turn并保留稿；sending仍模拟Cancel。仅原功能仓库修改，未触视觉worktree，视觉交回时一并集成。既有20项证据属于原版本；此微修不冒称已做完整键盘或四宿主视口验收。脚本/忽略目录与worktree已由Main落实，实际用户设计入口为5176（默认5174保留为本地Mock启动默认）。
