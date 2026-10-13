# Composer 与选择器修复记录

本报告记录本轮修复结果及证据，供 Main 集中 review；不作责任归因。实现均为前端工作区未提交增量，最终提交与实际 UI 核对由 Main 统一完成。

## 问题与原因

- 正常连接、无未知回执时仍有空 feedback 槽：传给共享 Composer 的 Fragment 始终为 truthy。
- Slash suggestions 位于底部反馈区；模型与推理入口使用 Modal，偏离用户已经调好的 Mock Composer。
- 当前选项缺少直接高亮，推理额外显示重复 Current 行。
- 原生 runtime provider 与 catalog slug 可以不同；仅按 slug 比较会漏亮，而按同名模型猜 provider 会误亮。
- 本地菜单连续切换时，旧菜单的关闭回调可能清掉新菜单的打开状态。

## 已实现

- Feedback 仅在未知 Steer／提交回执或断线时生成；网络状态与回执恢复动作保留独立语义。
- 真实 slash catalog 搬到 editor 上方，保留原最多八项及点击填入草稿行为；未引入 Mock 列表。
- Model／Reasoning 使用共享向上 Popover 和通用菜单样式，支持 pill 点击及 App 受控 `/model`、`/reasoning` 入口。Attach 恢复同款菜单结构与图标。
- 选项通过 `aria-pressed` 直接标记当前值，Main 已接入选中色 CSS；去掉 Current 行。Effective 仅在实际 Conversation 中未知或与请求值不同的时候说明。
- Model 优先精确 provider slug；仅在没有精确行、没有未应用模型草稿、catalog 当前 model 相符且唯一 `is_current` 行时接受原生目录标记。不猜 provider 名称或 aliases；未知不选任意项。
- 原 `config.set`、profile／runtime session、`ensureBinding`、模型 `confirm_required` 保护、本地草稿分支与 capability error／Retry 保留。Rewind 两次明确确认仍为原 Modal。
- 旧菜单关闭仅清除自身本地 owner，避免清掉新菜单；App 受控回调保留。

实现入口（前端 `/Users/edgar/code/hermes-secretary-web`）：`src/components/ChatComposer.tsx`、`src/components/ChatDialogs.tsx`、`src/components/ChatSelectors.tsx`；现有测试入口为 `src/core/timeline.test.tsx`。通用样式与 App props 由 Main 集成。

原生 provider 事实来源（后端）：`tui_gateway/methods_complete.py` 的 `model.options` 使用 `_model_picker_context`；`tui_gateway/methods_complete_helpers.py` 恢复 custom identity；`hermes_cli/inventory.py` 的 `build_models_payload` 与 `_local_runtime_row` 依据 managed endpoint 标记 Local 的 `is_current`，并排除重复 custom 行。采用该 DTO 标记，不将模型名称唯一性作为 provider 证据。

## 验证与版本边界

所有命令均在前端工作区执行；以下是开发证据，不替代实际 UI 验收。

| 验证阶段 | 命令／结果 | 覆盖与限制 |
|---|---|---|
| 首次呈现恢复（10:52） | `npm run test -- src/core/timeline.test.tsx`：35／35 PASS，1.17 秒；`npm run typecheck`：PASS | Popover／feedback／slash 恢复，以及既有键位、未知回执、角色呈现用例；先于后续高亮修订与 HMR 增量，不冒称最终版本整包证据 |
| 高亮修订首次定向（11:20） | 下列两例命令：导入失败，35 项全部跳过 | 当时 `import.meta.hot?.data.controller` 在测试环境遇到缺失 data，尚未进入组件断言；Main 已安全化 hotState 读取，原失败保留为版本边界 |
| 修复导入后的定向（11:28） | 同两例命令：1 PASS／1 FAIL | Retry 已通过；连续 Reasoning→Model 切换暴露本地关闭回调竞态，随后按同 owner 修正 |
| 最终定向（11:29） | 同两例命令：2 PASS／33 跳过，906 毫秒 | 高亮当前推理、不同 Effective、同名模型仅原生 Local 被选中；无能力时无误亮、Effective Unknown、5098 与真实 Retry 动作；并覆盖菜单连续切换 |
| 最终差异静态检查 | `git diff --check -- src/components/ChatSelectors.tsx src/core/timeline.test.tsx`：PASS | 无空白差异错误；不等同功能测试 |

最终两例命令：

```bash
npm run test -- src/core/timeline.test.tsx -t 'formal reasoning popover|displays the actual native guard'
```

## 实际 UI 与交接

Main 尚需从当前集成页面核对菜单高亮、Popover 锚定、slash 位置、空反馈槽消失及受控命令入口。此前 Mock／旧版本 UI 观察不代替当前新修订的实际界面证据。

本次未提交、未修改真实设置或运行数据、未调用模型、未重启服务；未重跑全套测试或扩大后端检查。交回 Main 亲自 review 后统一接收与记录。

## 2026-10-13 快速切换的关闭焦点竞态修复

本节为 Main 后续独占派遣的修复，覆盖此前 functional close setter 仍不足的实际失败；不是历史追责。仅改前端 `ChatComposer.tsx`、`ChatSelectors.tsx`、共享 `design/primitives.tsx` 的 Popover关闭焦点接缝，以及 `timeline.test.tsx` 当前同一 reasoning popover case；未动 Controller/Projection/App/视觉 chat/layout/theme。

1. **条款**：R04 Model/Reasoning真实选择器、既有单 selector owner、当前项高亮与自然焦点行为。用户快速切换不能被旧菜单关闭副作用取消；全部关闭仍应回原 trigger。
2. **原因与实际变更**：同用例三个独立 `act` 正式点击：打开 Reasoning→关闭 Reasoning→立即打开 Model。原代码 focusin 实测为 `[route-model, Reasoning: ultra]`，随后 Model dialog=null。Radix FocusScope 的 unmount autofocus 通过 `setTimeout(...,0)`执行，Popover NonModal默认把焦点归还旧 trigger；已聚焦新 Model之后旧Reasoning恢复焦点，触发新Model focus outside关闭。fixture操作合法，无需放宽或添延时。修补在 Composer 当前 Model/Reasoning/Attach 共用的菜单焦点 owner ref上读取实际 open状态，仍有菜单打开时 `preventDefault`旧关闭回焦；全部关闭时保留原Radix归还trigger机制。
3. **正式路径**：`ChatComposer.returnMenuFocus → ModelSelector/ReasoningSelector（及同Composer Attach）→ Popover.onCloseAutoFocus → Radix Content`。共享Popover只增加optional回调并透传；独立Popover未传回调仍原默认行为。functional close setter原保护保留；没有新业务状态、计时器、下游强制重开或改变模型/能力应用。
4. **验证**：`npm test -- src/core/timeline.test.tsx -t 'highlights native current choices'`。修前一次明确FAIL（956ms、Model null及以上焦点实测）；接线后原casePASS（981ms）；删除临时console、保留正式焦点断言和全部关闭反例后最终1PASS/34skipped（913ms、case298ms）。这都是同一用例的修复复测，不相加为3个用例。最终断言：同快速点击序列中Model实际仍在、真实Local当前项唯一高亮；新Model聚焦后不会再focus旧Reasoning；全部关闭后由实际`focus`事件证明归还Model trigger，无固定等待。`git diff --check`通过；未重跑fullsuite/build/typecheck/model/浏览器。
5. **缺口**：ReactDOM＋真实Radix机制已覆盖快速竞态和正常回焦，未由本owner进行IAB实际菜单快切；Main既有慢切UI观察不能冒充本case修复后的快切。其它文件现有合法修改全部保留，未提交或重启。
6. **接口影响**：Popover新增optional `onCloseAutoFocus:(event:Event)=>void`；两个selector新增相同可选回调，由同Composerowner注入。Main如同步visual worktree，只吸收shared Popover这几行可选prop/Content透传及适用Composerowner接线，不整体覆盖视觉文件。
7. **后续**：Main亲读4文件精确新增hunk和Radix关闭事件时序，按必要同步visual共享Popover，集中阶段检查/真实页面确认；仍停Verification前，不因一个返回派独立门禁。

| 前端文件（当前合法未提交工作区） | SHA256 |
|---|---|
| `src/components/ChatComposer.tsx`（下述health微小重构后） | `56aad0a3375f6a72236ecdff9871bdf86c8c8b6d5ffa63c4235c8ee6e603d45a` |
| `src/components/ChatSelectors.tsx` | `d37e34e0771bb93757718432254611cdb5163c4724347aea41012ab00fb93a64` |
| `src/design/primitives.tsx` | `08dfff1bf964b13f6159b46f601a0efb265e02ec7ea3d4f18a09deca7811a941` |
| `src/core/timeline.test.tsx` | `37b0a082ded0ba7d1521ea95a0190f43149eceeff24c84f5490a199dbaf515a3` |

最终health接收补充：Main产品build已PASS（6.26s＋types），冻结health指出本次新增四个boolean branch使ChatComposer CC22＞20（原18）。按Main唯一授权微小重构，仅在同文件将isModel/isReasoning与focus ref/any-open计算原样提为`useComposerMenuFocus`，原调用返回和焦点行为保持，无新业务/文件/allow/阈值调整。定向同rapidcase再次1PASS/34skipped（980ms，case314ms），差异检查通过；最终ChatComposer hash已更新如上。未重跑全suite/build，Main统一执行最终health与产品build；本owner未冒称尚未运行的最终health通过。

## Main 最终集成接收

2026-10-13：Main集中亲审正式路径与改动并接收相应owner证据，最终前端c55120f、visual fc18614、原生产品4443aa7。用户自测整改的实际关闭范围、测试失败/修复留痕、真实DeepSeek/IAB及未验证边界统一见final-delivery「当前整改关闭证据」和根CLAUDE；本报告上方“待实测”是交回时观察，不覆盖该最新接收。最终冻结前端health0/0及build/types通过；两独立门禁未执行，不称整轮验收。
