# U15 · Toast 圆角外直角灰底修复交回

## 1. 目标条款

按用户 U15 和主会话指定方案，修复 `.hs-toast-stack` 的滚动裁切把卡片阴影切成直角灰底；保持原卡片几何、系统安全区、最大高度、真实滚动、顺序、进入／退出与关闭、pointer行为。此独立问题先在 main 工作区完成，随后由主会话亲审提交并并入增量分支。

工作区 `/Users/edgar/code/hermes-secretary-web-toast`，main 基线 `37a8e4c6d6908d0a1409e3849b5ce5d1bde70a2f`。已读前端 AGENTS、主仓当前 CLAUDE／本轮依据；没有修改 hooks、提交、打包或部署。

## 2. 实际变更

仅修改 `src/design/theme.css` 两条既有规则：

- `.hs-toast-stack` 增加 `drop-shadow(0 12px 24px var(--hs-shadow-color)) drop-shadow(0 2px 4px var(--hs-shadow-color))`，让阴影在滚动内容裁切后绘制。
- `.hs-toast` 删除原 `box-shadow: var(--hs-shadow-panel)`，避免卡片内的大阴影再被 overflow 裁切。

沿用原阴影颜色、两个偏移及与原48px／8px box-shadow近似等效的24px／4px filter blur。未改全局 token、其它组件、toasts.tsx 或任何布局／交互规则，无新 wrapper。

## 3. 正式路径

原 ToastStack → `.hs-toast-stack`／`.hs-toast` 保持。实际验证直接导入正式 ToastStack；旧版对照注入基线完整 theme.css，并显式将新增filter设为none，确保对照没有叠加新阴影。所有控制均在 ignored harness；不替换产品关闭／动画或滚动实现。

## 4. 验证结果

证据目录 `/Users/edgar/code/hermes-secretary-web-toast/.archive/incremental-sync-20261027/toast/`。

- 既有 `presentation.integration.test.tsx` **37项通过**，覆盖通知 newest-first、跨路由保留与只关闭指定消息等正式行为；没有新增镜像／源码断言测试。`presentation.log`记录命令与结果。
- `git diff --check`通过；完整差异在`implementation.diff`，源码SHA在`source-sha256.txt`。
- 自己创建的 **Codex隐藏IAB visible:false** 实际渲染；没有桌面、外部浏览器、可见页或用户现有页面操作。最初浏览器旧ID不可用，读取当前可用IAB ID后继续；结束已关闭自己的标签并复原临时viewport，5203验收Vite已停止。
- **360×792浅／深色、单条**：旧截图可见左边／底边硬矩形，改后连续柔和阴影。卡片稳态`x=16,y=16,width=328,height=86.390625`，stack`x=12,y=12,width=336,height=94.390625`，旧／新完全一致。
- **12条长堆栈真实浏览器滚动**：浅／深色由harness按钮操作原DOM scrollTop，不伪造尺寸或scroll事件。旧／新均`scrollHeight=2224,clientHeight=768,scrollTop=1456.5`，滚到真实底部；圆角外缘不再出现原硬裁边，间距／顺序保持。旧／新JSON和截图分别`before/after-{light,dark}-stack-bottom.*`；另有新深色stack-top。
- **进入／退出**：正常进入320ms、正常关闭180ms实际完成，`after-enter.json`记录原hs-toast-in，`after-exit.json`记录hs-toast-out结束且count=0。为稳定观察中间画面，仅在harness用浏览器Animation API暂停原动画到160ms／90ms，未改原keyframe／duration；`after-enter-midpoint.*`与`after-exit-midpoint.*`保留截图与实际读取，退出时`data-exiting=true`、pointer-events=none、关闭按钮disabled。中点仅用于视觉取样，不作为原生计时精度证据。
- **1200×800宽屏**：stack仍为既有28rem=448px居中上限；`after-wide-single.*`记录。未改safe top表达式、最大高度或padding。
- **截图像素量化**（RGB各通道绝对差之和）：在旧clip左界x11→12、y35–89采样，浅色最大突变 **33→6**，深色 **9→3**；在底界y105→107、x40–320采样，浅色最大 **63→12**，深色 **19→4**。读自真实旧／新PNG，见`pixel-metrics.json`；这些采样只说明本夹具硬边改善，不扩大为所有设备量化结论。

浅色旧／新原始截图：

![旧版浅色Toast](/Users/edgar/code/hermes-secretary-web-toast/.archive/incremental-sync-20261027/toast/before-light-single.png)
![修复后浅色Toast](/Users/edgar/code/hermes-secretary-web-toast/.archive/incremental-sync-20261027/toast/after-light-single.png)

## 5. 缺口与限制

- 未Android真机或APK安装验收；隐藏IAB只证明实际浏览器呈现。
- filter与box-shadow模糊算法不是逐像素相等，已按主会话认可起点保持颜色、偏移与近似模糊；实渲染未发现需要产品重新决定的阴影／滚动变化。
- 正常关闭实际完成已有证据；受控动画中点用于截图观察，不把控制时钟取样冒称真实计时测试。

## 6. 接口影响

无API／数据／DOM结构／组件参数变化；没有更改阴影token、视觉设计或其它组件；仅这一个CSS文件有产品差异。

## 7. 后续

请主会话亲审main工作区两条CSS与截图后提交／push，再cherry-pick到增量分支。当前未提交；未扩大为整轮Verification／Validation通过。

## 主会话接收

已亲审theme.css两条差异、浅色旧／新实际截图与上述滚动／动画证据。独立main提交810aca3已自动push；前端增量分支cherry-pick为03ef6d5ecd2caf53ed434771c5b4c46d7b6cc2c3并自动push。未部署，真机缺口保留。上文“未提交”只描述子Agent交回时点。
