# 原视觉合同恢复与 Notebook 只读呈现修复报告

## 当前状态与范围

2026-10-13，按 Main 本轮 R01／R03 长名／R05 及新增 R13 授权实施。共享组件、正式单层确认和 Mock 修补已经完成，等待 Main 集中 review／App 两个薄接缝／统一类型与 health／实际浏览器复核。**不是完整用户验收或独立 Verification／Validation，不能据此关闭本轮所有现场问题。** 未提交、未调用模型、未重启服务、未操作用户浏览器、未派生 Agent。

已完整读取 executing-plans Skill 及自主运行交接契约、本轮计划／索引／baseline／当前 CLAUDE；依据包括 02 §1.6 Message Identity 行183–197、§1.7–1.8 source of truth 行198–249、§2.5 条目与四分区、§3.5 AI六键结构／人类视图边界、§6.18，以及06 Timeline／Composer／附件／§1.11最新单层确认／§1.15秘书只读要求。各问题以原用户合同和今天最新显式口径恢复；不继续开展历史追责。

## 恢复依据与原始证据

真实原会话标题：**阅读06文档，你是那个前端 agent，现在和我来一起调整视觉表现层,某个数据已就绪，Dive Server 已启动在5176**。Kimi会话 `session_85d4123e-217c-4be5-bc5b-1c6b199ffeba`，2026-10-12 21:52至2026-10-13 01:52（Asia/Shanghai）。[原始消息及checkpoint](/Users/edgar/.kimi-code/sessions/wd_hermes-secretary-web-visual-design_d8826a400d74/session_85d4123e-217c-4be5-bc5b-1c6b199ffeba/agents/main/wire.jsonl)含真实用户消息来源和时间；第7400行01:50:52 end checkpoint与[文件副本](/Users/edgar/.kimi-code/sessions/wd_hermes-secretary-web-visual-design_d8826a400d74/session_85d4123e-217c-4be5-bc5b-1c6b199ffeba/agents/main/file-history)是末版定位依据。收尾开工副本与专属补丁分别为[before](../../.hermes-dev/round2-evidence/visual-finish/before/)和[finish-only.patch](../../.hermes-dev/round2-evidence/visual-finish/finish-only.patch)；[收尾manifest](../../.hermes-dev/round2-evidence/visual-finish/source-manifest.json)22/22文件匹配`1c614ac` Git树。

| 原用户合同 | 原始时间／恢复依据 |
|---|---|
| “三态流转从完成到回归静息之间，没有一个渐渐熄灭的过程，补全最后一点过渡” | 2026-10-13 01:21:34，wire6038；只补finished→idle，不更改active运行形态／时序 |
| “外圈光晕不需要出现，内圈高亮慢慢熄灭即可” | 用户粘贴交接附件及[交接prompt](/Users/edgar/code/hermes-secretary-web-visual-design/docs/codex-handoff-prompt.md)；详细原句未在原Kimi末段找到独立同句，不混淆证据层级 |
| “我不是让弹两个弹窗确认…点了发送按钮之后，要有一个弹窗确认，一层就够…按钮颜色采用那个红色” | 2026-10-13 01:23:50，wire6109；原末版confirm一次即startSend，无后续原视觉用户消息覆盖。今日再次明确Send+该确认是两步，06§1.11已由Main同步 |
| 面板“锚定下边，统一向上生长，下边保持同一高度位置对齐”；“已验收悬浮球和面板的动向，没问题了” | 2026-10-13 00:15:58／00:31:50；保留360ms形变、130ms玻璃→实体交接、底边锚定及Status↔Memo过渡 |
| “光晕应该逐渐淡出…纯色背景。底下两个底边胶囊，自然浮现…composer…距离…一样” | 2026-10-13 00:46:42，wire4403；共享Welcome离场保留而不是条件立即卸载 |
| “在手动滚动停止的半分钟内都不再滚动” | 2026-10-13 01:19:20，wire5934；默认Mock30秒冻结；同时遵守06旧历史阅读者不能被拉到底 |

关键原末版hash：

| 文件／版本 | SHA256 | 核对 |
|---|---|---|
| theme.css v24 | `46255782439b3235255470b4c6f35e37c443eea48142a8536486fba27b7e175f` | 与before完全一致 |
| layout.tsx v7 | `93c1f96809e2fcc217471344e479f3ee5289c4f061d3fba855a0125b25aa5349` | 与1c614ac完全一致 |
| indicators.tsx v15 | `44d6ff9ff92aacbabf91139c6d8dc4f291613ce0f51f98f841ca8c096d415409` | 与1c614ac完全一致 |
| tokens.css v3 | `171661bfef93f3b4493f0c446487bd17a7581e3027d9c9cb98694696d2eadf85` | 与1c614ac完全一致 |
| MockComposer.tsx v4 | `6ca159f5f9ba874f4dcef1c993b1e30bdb03420c6181eadef7bc04100ddb0ac7` | 与before完全一致 |
| state.ts v4 | `510fa0efb30212d51efdec902a38682dcbc479bebf52244a135faba63192954c` | 与before完全一致 |

**保留完整用户成果：**`1c614ac`包含fork基线`27c5cb4`之后用户未提交的完整视觉成果，不能整体回滚。原光晕比例运动／三色／边缘约束／标题居中换行源码保持；[原active截图](/Users/edgar/code/hermes-secretary-web-visual-design/r7-orb-active.png)、[原形变截图](/Users/edgar/code/hermes-secretary-web-visual-design/r8-collapse-mid.png)、[原三色光晕截图](/Users/edgar/code/hermes-secretary-web-visual-design/r17-glow-trio.png)已查看。旧原checkpoint中primitives/chat内容副本缺失，但记录hash匹配before，不冒称副本本体存在。

**两树mask事实已校正：**原末版、1c614ac和visual HEAD86fa280均有有效`#000`环形mask；正式接线token化时同时定义`--hs-mask-opaque:#000`，本身等价。后续整份theme同步至visual而漏tokens，才形成visual未提交样式缺依赖。不能把“当前两树相同／不同”当作原合同，也不能把该雷达问题归到原末版。现按Main已恢复的`#000` hunk同步visual，保留14%短弧、3px圈宽、2.4s线性旋转。通用SVG1200ms慢过渡影响active点亮的额外变化，本次改为只在finished→idle适用。

## 实际修复与正式路径

| 范围 | 机制与实际接入 | 当前验证边界 |
|---|---|---|
| R01 active／finished | `useFinishedFade`只在前态finished且现态idle产生1200ms data-fading；进入active立即清。基础SVG无慢transition，冲击波后finished不重新加静态绿色外光。有效mask精确同步两树 | React切换／中途active／到期清理通过；环形mask及像素渐熄待Main浏览器中间帧 |
| R01面板 | 保留Main `settle(false)`关闭时持续遮蔽直到React卸载的修补；未回滚generation、反向取消、资源清理、360ms／130ms或底边锚定 | 既有反向／rapid close／unmount／末帧提交间隙用例在受影响包通过；真实中间帧待Main |
| R01默认Mock滚动 | 共享Timeline只有autoScroll=true时建立owner。记录程序滚动位置避免假手动；每次手动滚动冻结30秒，冻结结束仍仅following读者跟随；浏览旧历史不会被拉底。正式autoScroll=false不添加第二owner | 默认Mock人工scroll＋ResizeObserver回调、29999ms／30001ms、旧历史31秒不跳通过；原正式reading owner用例通过 |
| R01Welcome过渡 | ChatLayout新增可选welcome prop，保留同一个Welcome DOM离场420ms，既有opacity淡出与底栏自然入场；重新进入取消旧离场timer。MockStage直接接此prop，删除旧易取消的离场effect | 共享DOM连续性／清理／反向进入及实际Mock Send→1600ms接受→420ms离场通过；Main App薄接线待做 |
| R03附件长名 | 父flex文字区flex:1／min-width:0／overflow:hidden，文字子项max-width:100%＋ellipsis，图标／叉不缩；全名title和原名称保留，不添加历史点击动作 | 全名／无button或link组件行为通过；小屏实际省略号、越界与视觉待Main |
| R05正式／Mock | ChatDialogs只打开一个红色确认，确认直接controller.send，取消只关dialog保编辑；无edit时清confirm，不因刷新后遗留数字重新武装。Mock confirm1／既有confirm2 URL均直接发送，同一合同 | 正式实际dialog一次确认／取消／metadata清除不武装、交互Mock及状态契约通过；controller原生截断参数与安全边界未修改 |
| R13Notebook | 新共享NotebookView消费公开human output：创建时间、User／Assistant／Consultation／Persistence分区、条目type/status、字段／多行／列表、来源计数与Schedule。只有read-only显示，未知字段及文字保留，无整段pre／JSON卡，无新写操作 | native形状组件、无快照、实际Mock共享卡与全场景SSR通过；Main正式temporary接线与真实输出视觉待做 |

今日边距User左12%／右3%（最大85%）、Assistant正文／活动卡片左4%／右10%、真实User／Assistant居中本地时间、Framework／Deferred默认折叠46px等Main既有修补保留；未改源时间戳或Notebook事实。

## Main所需两个App薄接缝

1. **Welcome：**`ChatLayout.welcome?: ReactElement<{className?:string}>`。Main将当前children内的New Chat条件Welcome移至`welcome={state.route.screen === "new" ? <Welcome title={controller.newChatTitle} asset={<HermesMark className="hs-brand-icon" />} /> : undefined}`；children仅保留Conversation的ThreadRoot／Timeline（正式`autoScroll=false`不变）。不得给ChatLayout加route key强制重挂，否则无法保留离场DOM。Mock已使用同一入口；原比例运动不改。
2. **Notebook：**`NotebookView({output:string})`已由现有design/index通配导出。Main在确认的`node.kind === "temporary"`正文渲染`<NotebookView output={node.text} />`，不靠英文文字猜消息种类；共享Message kind=notebook已去重复小标题，卡片自己提供Notebook标题。序列固定由flow owner负责，本owner不改App／controller／projection。

真实输出来自controller.readNotebook→secretary.notebook_read.output→secretary/notebook_render.py.render_notebook，形状为`Notebook / Created at / 四分区 / - type [status] / 两空格field:value`。AI六键`notebook_show`含anchor_message_uid，02明确人类视图不展示Anchor；本组件不请求或混用该JSON。Created at保持源时区和时间，不生成read-time。无快照／不可用保原文本，不编造字段。Mock fixture改为同一native human形状的合成数据，保原场景URL。

## 修改与同步范围

前端只修改本任务白名单13文件（见下方hash）；其中MockTimeline仅Notebook分支、fixtures仅Notebook样例为Main追加明确授权。未改App／controller／projection／ChatComposer／Selectors／backend。

visual按明确函数／样式／Modal／fixture hunk同步11个design或Mock文件，没有整文件覆盖未核差异，没有依赖token遗漏；原untracked截图／docs全部保留。共享chat／indicators／layout／MockStage／MockTimeline／fixtures及两Mock测试最终完整相同；theme、MockComposer键位、state既有helper拆分差异保留。正式ChatDialogs不复制至视觉树旧正式App组件，Mock使用其自己的单层确认入口。

## 定向验证与未测

| 执行 | 结果／耗时 | 说明 |
|---|---|---|
| 12:03 `npm test -- src/components/presentation.integration.test.tsx src/mock/state.test.ts src/mock/render.test.tsx` | 首次40 pass／2 fail，42用例，1.31s | 两失败是新增测试选择器误用data-variant及Cancel send大小写；按实际按钮class／aria-label修测试，未改产品规避失败 |
| 12:05 presentation `-t 'one red Rewind|actual interactive Mock'` | 2 pass／20 skipped，2.94s | 原失败两项通过，不重复整包 |
| 12:06 presentation `-t 'fades only finished|actual standalone Mock first Send'` | 2 pass／21 skipped，0.894s | 熄灭薄hook最终版及新增真实Mock首发过渡 |
| 12:13 presentation＋render `-t 'native human Notebook|no-Snapshot result|Notebook Mock'` | 3 pass／26 skipped，0.844s | 新R13字段／多行／Schedule／列表／无快照／Mock |
| 12:15 `npm test -- src/mock/render.test.tsx` | 4/4 pass，0.649s | 去重复Notebook标题后的最终版；包含103场景实际共享组件SSR，不是103场景浏览器验收 |
| 两树指定文件`git diff --check` | pass | 无格式错误；报告本地链接另核 |

各运行按版本与实际用例复用，**不叠加重复通过数为全量验证**。未执行Types／health／full build／full suite，按派遣由Main最后统一；没有独立门禁。未操作IAB或抢用户tab，真实四视口／动画全过程／长名像素／Notebook真实输出由Main统一实测。源码已冻结交回，本责任人等待review，不冒称全部现场问题解决。

## 交回源码SHA256

基于前端HEAD `21aad02` 的未提交工作区，表中包含已有Main变更与本owner hunk，不能把整文件差异归给本owner。

| 文件 | SHA256 |
|---|---|
| `src/design/chat.tsx` | `e865eeff7c48130689db71dff455a661bdae607fc8a8c0e4e1c6cb6d4c7e84a2` |
| `src/design/indicators.tsx` | `de1f96f4f242c9425e679f9ee284c40975336ba3b2c1923b4f4ae2b7cea9ef08` |
| `src/design/layout.tsx` | `38c59cb715bd2f557f6da41250579c56760fa7eb3a9918d90ed5fd239854f4ab` |
| `src/design/theme.css` | `6bcdbb4b9b6a86425c5c71cf0bf91651b04f72807058eab4bb122bb0acde75ce` |
| `src/components/ChatDialogs.tsx` | `926d584e61cedf3a2c9f86e6c92119d4a5a5178d349363ca3803269b70df0a1f` |
| `src/mock/MockComposer.tsx` | `acf509603eecb666c2f55327fa108d73bdd6c1f8e0d67b375300d4280e27244b` |
| `src/mock/MockStage.tsx` | `ec2eae8d3a3e14f0aa45f2b1dee7d35941b7169d78f764cb22a91ac9ec776360` |
| `src/mock/MockTimeline.tsx` | `59e03258d7d75cf8f207a1ebb7139f3c98bd6bbed2ad60dc51d2cade2f3e5fc0` |
| `src/mock/fixtures.ts` | `79c789e2487457361b58ec85be9da520646dffa4be593f2a705d3e989a351bdb` |
| `src/mock/state.ts` | `68cca6863ccc8dcaf025391ae00cc28f4f8b9f9c5300c0e862b3d6686a3b4c02` |
| `src/mock/state.test.ts` | `2570fa8d29be62187212d9654ccd2bbe2d701af3b1f1c7c9694b94c45cf6d4aa` |
| `src/mock/render.test.tsx` | `114a61fee7931eee80d3eac0c0a70ec2a39780c21990b4648a8372db8f96982e` |
| `src/components/presentation.integration.test.tsx` | `2ed2a0df68d3bd38a572f4996f064e042e4e1908144f07816f6babe4e37bf744` |

Main建议：集中review本报告及13文件hunk→薄接两个App入口→按影响统一Types／health→真实四视口、中间帧和必要DeepSeek实测→更新核心看板；保持Verification前停止边界。

## 12:36 · Message复杂度小修交回

Main冻结health发现Message CC25超过20（基线15）。本责任人仅将折叠／普通正文渲染分别提取为`FoldedMessageBody`／`OrdinaryMessageBody`纯展示helper，折叠状态和bodyId仍由原Message持有，保原DOM类名、ARIA、独立默认折叠、46px样式、百分比边距、附件／Reply／Withdraw／流式指示。统一图标映射改为显式Partial类型，不再在Message重复分支。没有调整门禁规则、阈值或关闭检查；最终CC与build由Main统一确认。

两树仅精确同步chat相同hunk；最终shared chat字节相同。保留Main新增`secretary_task`无Schedule字段时“Schedule · Not scheduled”及已统一顶部的ChatDialogs useEffect import；未修改该import、面板动画、CSS或Notebook字段。新增一条实际Message折叠交互用例，Mock Notebook断言确认未排期提示。

- `npm test -- src/components/presentation.integration.test.tsx src/mock/render.test.tsx -t 'source times|native human Notebook|no-Snapshot result|Notebook Mock|carrier kinds'`：5 pass／24 skipped，0.982s。
- 同两文件仅`-t 'Message folds independent|Notebook Mock'`：2 pass／28 skipped，0.825s；验证默认双折叠、独立点击、bodyId稳定与未排期提示，重复Notebook不另计通过总数。
- 两树指定文件`git diff --check`通过。没有重跑动画包、full suite、模型或浏览器，没有提交或另建文档。

上方chat／ChatDialogs／两测试hash已更新为此次小交回实际版本；ChatDialogs hash仅反映Main import修复的现行版本，不将该hunk归本owner。仍由Main统一health/build与产品实际复核，本小修不是独立验收。

## Main 最终集成接收

2026-10-13：Main集中亲审正式路径与改动并接收相应owner证据，最终前端c55120f、visual fc18614、原生产品4443aa7。用户自测整改的实际关闭范围、测试失败/修复留痕、真实DeepSeek/IAB及未验证边界统一见final-delivery「当前整改关闭证据」和根CLAUDE；本报告上方“待实测”是交回时观察，不覆盖该最新接收。最终冻结前端health0/0及build/types通过；两独立门禁未执行，不称整轮验收。
