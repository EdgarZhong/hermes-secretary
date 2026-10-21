# Verification：20261021-mobile-release

## 1. 审查对象与结论概览
审查者：独立 Verification Agent；冻结规格：57ffa1c355b4eef9b73f6ab10d3fb6da42b43176；索引：本目录 snapshot-index.md；范围：R01–R16及直接适用的06/07/08约束。待审后端：`9fabcdd73d817b55e6b819cb01681583d24a27ff`；Web：`ad7e4842c230bf65bf8b1d5491ea1a169407ca6a`。进入条件：实现集成收敛，既有证据可复用，构建在审查期间完成。审查时间：2026-10-21。总体结论：**门禁不通过**，20条中17条符合、2条证据不足（实际Android通知与真实WebView视口）、1条违规（旧候选Heartbeat入环前失败后误去重）、0条不适用；后续修补候选3b48cf0待全新独立复审；不得冒称整轮已验收或已上线。

### 2026-10-21 全新独立全轮复审：当前结论

审查者：独立子 Agent `release_reverification`（未继承主会话上下文、未派生）。复审记录时间：2026-10-21T13:16:11.434630+00:00。冻结仍为 `57ffa1c355b4eef9b73f6ab10d3fb6da42b43176`，当前产品候选为 backend `3b48cf0baeb3c49bb96849d24c6105bf6e39e6fc`／Web `ad7e4842c230bf65bf8b1d5491ea1a169407ca6a`；两个候选源码均与工作区一致，无产品 dirty。原初审20条判据、旧版本违规及历史结论全部保留；本次先仅读冻结原文建立32条独立判据并落盘，再读旧报告／指导／源码／证据。

**当前门禁不通过，不能进入正式 Validation。** 本次独立32条：**29符合、0违规、3证据不足、0不适用**。RV17为实际通知证据缺口；RV19／RV20是同一旧F01的WebView视口与Insets／IME两个观察面。按原20条复核口径：**18符合、0违规、2证据不足、0不适用**；V04／F03在当前修补版本关闭，V11／F02与V13／F01继续未关闭。统计是条款数，不累加重叠测试次数；既有五个后端基线失败继续保留，不宣称所有后端测试全绿。

隐藏IAB恢复可用是当前环境事实，但本审查没有执行浏览器UI操作。主会话正在补独立实际浏览器证据；它不能代替真实Android WebView或通知。当前没有获授权且可用的Android真实UI入口，不能把该缺口改成不适用，不能用Robolectric、组件或普通浏览器截图替代。候选APK／dist构建符合不等于整轮完成或已上线。

### 当前最新结论补充（稳定v2界面证据后）

**28符合、1违规、3证据不足，Verification不通过。** 原20条为17符合、1违规、2证据不足。新增F04/P2：同UID已完成Thinking在工具详情补齐接管时丢失手动展开；RV10／原V06改违规。稳定浏览器证据和源码因果详见第3–6节追加。早前本次复审“无新增违规／29符合”是补交实际界面证据之前的时点，保留历史，不再代表当前结论。F03已关闭，F01/F02未关闭。正式Validation不能开始。


### 2026-10-21 第三次独立整包复审：当前最终候选

审查者：全新独立 Agent `release_final_verification`，不派生；冻结依据仍为 `57ffa1c355b4eef9b73f6ab10d3fb6da42b43176`。先仅按冻结原文提取19条判据，写入ignored `.hermes-dev/mobile-release-final-verification-20261021/criteria.md`，之后才读指导、旧报告、当前实现与证据。当前待审后端 **`3b48cf0baeb3c49bb96849d24c6105bf6e39e6fc`**、Web **`bf279b2dc5ec5553ff9e370696b153e4aadb52cd`**；亲核两仓产品源码无dirty，原有其它文档dirty保持。

**当前Verification不通过，正式Validation前置未通过。** 本次19条全轮判据：**17符合、0违规、2证据不足、0不适用**。证据不足为FV09实际Android响铃／横幅与FV11真实WebView380宽度／比例／Insets／IME。对应原20条为18符合、0违规、2证据不足；对应上一32条为29符合、0违规、3证据不足（RV19与RV20拆分了同一F01）。不得把三套条款相加。旧F03已关闭；本次依据源码、正式Controller／组件及稳定实际DOM证据关闭F04，无新增范围内实现违规。F01／F02仍未关闭，不能以本地构建或组件浏览器证明“全部测好”。

当前统一构建已更新至F04后版本：dist439文件，清单SHA256 `555528b534bb2abec4464d1027fa1697de4254affbc2a0e495e9bf4c374f449e`；APK **`5c9cabe44fb5e0fa8fa580cdf46dc719d7a439887d3342fb37d844cdbce6f98b`**、32,048,497 bytes、0.1.3/1003，439内置文件与当前dist逐SHA一致。交付路径为后端 `.hermes-dev/android-apk-20261021/Hermes-Secretary-0.1.3-arm64.apk`。旧`40ef…`是保留的F04前历史包，不是当前交付。独立apksigner核新旧包均有效且同证书，不冒称已安装覆盖升级。无生产部署／模型请求／微信消息／重绑／配置修改／重启／设备控制。

## 2. 独立要求清单与覆盖
判据建立时间：2026-10-21T20:53:26.496583+08:00。先仅阅读冻结提交的 snapshot-index.md、requirements.md 与索引所指06相关条款、08 §1–1.1、07 §8.15；未读代码、测试、实现报告、CLAUDE或计划。下列为独立起点，后续如修正会保留原文、依据及理由。07/06其它历史章节不扩成本轮新功能范围。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| V01 | requirements R01；06 §0.5 | 行为/兼容 | 原文直接要求及必要推导：辅助标题真实生成；保持既有模型、Provider、推理选择；不把参数异常吞成成功 | 正式标题入口兼容现有原生请求接口，无unexpected keyword；路由及真实SDK路径有证据 | 第3节V01 |
| V02 | R02；06:293 | 机制/提交恢复 | 原文直接要求及必要推导：实际Send有可选client_submission_id；ID仅展示metadata；原生writer保存到真实用户行 | 提交→writer→ACK/event→只读精确核验完整接线；同文本/运行状态不能推定受理 | 第3节V02 |
| V03 | R02；06:293；§0.5 | 边界/失败/兼容 | 原文直接要求及必要推导：unknown不证明拒绝；无盲重发；晚ACK只消费一次原草稿，保留后来草稿；退休/rewind不复活 | 核断线、ACK丢失、精确ID、跨Profile/Conversation拒绝、历史退休与省略ID兼容 | 第3节V03 |
| V04 | R03；06:271,295；07 §8.15 | 机制/消息 | 原文直接要求及必要推导：Heartbeat正式持久回调立即发原文/UID；无需等Turn完成；完整user包装才分类 | 真实执行中载体及时可见；event/history UID合并；不按Thinking/status/结束词合成 | 第3节V04 |
| V05 | R03；06:271；07:1445–1470 | 兼容/Heartbeat | 原文直接要求及必要推导：修复仅展示故障；保持Profile全局Noting选择、独立Conversation owner、原生UI唤醒与route | 不扩大Heartbeat调度/结束/过滤；source、UID、时间、正文及普通/非user/旧模板边界保持 | 第3节V05 |
| V06 | R04；06:291 | 行为/懒加载 | 原文直接要求及必要推导：展开/Loading details只原位补facet；不能把同Turn其余段移到全局尾 | 核真UID/row/occurrence归属及展开前后稳定位置；缺详情与空详情分开 | 第3节V06 |
| V07 | R05；06:287,291,304 | 机制/顺序 | 原文直接要求及必要推导：Thinking和失败工具按真实顺序，调用occurrence独立；不靠结束重排纠正 | 核stream→history对账、乱序start/complete、失败与分页外parent路径 | 第3节V07 |
| V08 | R06；06:291 | 行为/历史 | 原文直接要求及必要推导：无active切回旧会话，早期Thinking归属原Turn的真实位置；不挂到尾 | 持久UID/row优先于完成回执旧尾锚；历史/恢复重复去重 | 第3节V08 |
| V09 | R07；06:281–291 | 机制/滚动 | 原文直接要求及必要推导：阅读锚需DOM连接且当前消息身份一致；程序scroll不能成为新用户请求 | 仅用户主动/发送受理及既有active20秒规则回底；重排/详情/结束/自动Turn不跳顶 | 第3节V09 |
| V10 | R08；06:106,304 | 性能/边界 | 原文直接要求及必要推导：修正可归因的慢渲染逻辑，事件仍逐条处理，画面合帧；不增持久镜像 | 正式渲染路径有结构与定向性能证据；不声称设备帧率提升；无积压/丢序 | 第3节V10 |
| V11 | R09；06:193–203 | 机制/Android通知 | 原文直接要求及必要推导：新HIGH响铃/横幅通道迁移，尽量保留主动静音/关闭；旧系统识别限制诚实 | 核新ID、默认sound、block/mute策略与真实安装包；区分机制与实机通知证据 | 第3节V11 |
| V12 | R09；06:195–203 | 兼容/通知边界 | 原文直接要求及必要推导：既有观察范围/只读完成证据/最终持久回复；后台才通知；owner去重与信任边界不变 | 核迁移不扩大观察/发送/权限，不削弱前台抑制与失效连接、冷启动归属 | 第3节V12 |
| V13 | R10；C02；06:191 | 机制/壳视口 | 原文直接要求及必要推导：Android壳竖屏实际380 CSS px等比；横屏大屏不反向放大；键盘不变缩放基准 | 核原生WebView配置及内置前端无按断点整页scale；实测innerWidth/比例/Insets/键盘 | 第3节V13 |
| V14 | R11；06:187 | 行为/图标 | 原文直接要求及必要推导：复用logo与深纸色，遵守adaptive safe zone和普通mask，不裁切不过小无白边 | 核所有dpi资源、adaptive/legacy指向、构建实物及mask呈现；不可仅看源图 | 第3节V14 |
| V15 | R12；08 §1–1.1 | 机制/微信初始化 | 原文直接要求及必要推导：显式绑定物理session须属目标ref/Profile；沿目标原session_key，无key沿compression；入口仅locator | 正式Gateway入站→构造Main→初始化身份不认领入口alias；保留source/接收者/投递者 | 第3节V15 |
| V16 | R12；08 §1.1 | 边界/身份兼容 | 原文直接要求及必要推导：旧source不同同key别名可各属不同Conversation；不合并旧身份/历史/Notebook/排期；可信冲突仍拒 | 新绑定正常初始化、晚回流不回绑不注入新目标、合法compression与未绑定原生兼容 | 第3节V16 |
| V17 | R13；C01,C07,C08 | 交付/构建 | 原文直接要求及必要推导：所有修复后统一dist/APK，递增版本、原签名覆盖升级、APK内置同一最终dist | 核双仓最终hash、构建日志/产物hash/签名/version及dist逐文件一致；凭据不入包/Git | 第3节V17 |
| V18 | R14；C04 | 禁止事项 | 原文直接要求及必要推导：关闭旧Kimi调查，不改旧历史/排期/root，不重开模型实验 | 核本轮差异与证据范围，不发生生产恢复/模型请求 | 第3节V18 |
| V19 | R15；C05,C06,C08 | 执行/保护 | 原文直接要求及必要推导：分包实现、主会话集成复核；显示保护与dirty/凭据保护；机制和真实证据分开 | 核本轮范围、版本、证据可信度；UI缺口不能伪作通过/不适用 | 第3节V19 |
| V20 | R16；C07；06 §0.4–0.5；08 §1 | 权限/最终完成 | 原文直接要求及必要推导：托管本地修复检查统一打包；生产部署/主动测试消息/绑定配置变更不在自动范围 | 交付准备上线而非冒称上线；Profile-owner/原生兼容、只读导航与源数据保持 | 第3节V20 |

### 2026-10-21 全新独立复审判据（先行落盘原件）

以下原样保留ignored判据原件；其建立先于本审查读取既有审查、编码指导和实现。旧20条及旧结论不覆盖。

# 全轮独立复审判据

建立时间：2026-10-21T13:07:11.573327+00:00。仅阅读冻结57ffa1c355b4eef9b73f6ab10d3fb6da42b43176的snapshot-index、requirements及所指06／08／07权威原文；未读代码、测试、实现报告、旧审查、动态看板或计划。下列判据先落盘，之后不以实现降低。

| 独立ID | 需求覆盖 | 冻结原文位置 | 必要不变量／判据 | 性质与适用条件 |
|---|---|---|---|---|
| RV01 | R01 | requirements R01；06 §0.5 | 新会话辅助标题通过既有模型／Provider／推理选择生成；消除unexpected keyword错误；辅助失败不能破坏已受理Turn。 | 直接要求；核真实SDK调用兼容和正式标题接线，并区分受控与真实Provider证据。 |
| RV02 | R02 | 06:293；§0.5:113–115 | 每次实际Send可选关联ID由原生writer写真实用户行展示metadata；不进入模型消息；省略ID保持原生。 | 指定机制；不能以同文、running或另一会话事件猜受理。 |
| RV03 | R02 | 06:293 | 状态查询只读核目标Profile／Conversation精确ID，accepted携实际回执，未见事实unknown；退休／rewind仅证历史受理。 | 指定机制；跨Profile、相同ID、重启、rewind需证明隔离与不复活。 |
| RV04 | R02 | 06:234,293 | 丢ACK／断连后可恢复accepted，不永久unknown；unknown不得自动重发，accepted后历史读取失败不变发送失败。 | 直接要求及必要恢复不变量；核正式前后端纵向接线。 |
| RV05 | R02 | 06:293；08 §1 | 晚ACK只消费原捕获草稿一次；保留后续文本／附件；导航不改owner；取消和终态竞态不造成重复提交。 | 直接要求；核事件和直接响应竞态、后续草稿、跨路由恢复。 |
| RV06 | R03 | 06:271,295 | 已持久Heartbeat沿原生回调即时发原文／UID；执行中已有客户端无需等待终态看到独立卡；重复事件／历史按UID合并。 | 指定机制；不能由Thinking、status或结束标记合成。 |
| RV07 | R03 | 06:271 | 仅完整user heartbeat包装分类，独立折叠Heartbeat卡，心电图标／陶土色／同类宽度；展开仅去外包装、保留timestamp与正文，不给用户编辑／附件／外时间。 | 直接要求；普通提及、assistant引用、旧无包装模板不分类；HEARTBEAT_OVER无额外行为。 |
| RV08 | R03 | 07 §8.15:1445–1462 | 保持目标Profile全局Noting模板分支、英文timestamp模板、可选Additional；UI唤醒沿原生Main路由／模型／上下文／持久化，不误作微信入站或自动回复。 | 本轮故障修复须保留的契约；不把非本轮功能重做当完成要求。 |
| RV09 | R03 | 07 §8.15:1464–1470 | Heartbeat Conversation-owner、合法compression tip、跨页面／重启、pause/clear、claim/refund/并发和原生关闭分支均不受即时展示修复破坏。 | 保留不变量；只审本轮改动影响及有效回归证据，不扩实现范围。 |
| RV10 | R04,R06 | 06:230–232,291 | 详情懒加载仅原facet替换；已结束Thinking按真实UID/row/occurrence定位；旧尾锚不能覆盖持久位置；切回无active会话不尾部重复。 | 直接要求；包括loading、成功、失败、完成回执及会话重入。 |
| RV11 | R05 | 06:287,291 | 流式Thinking及并行工具各自单卡，真实顺序和身份从构建到完成稳定；失败工具及result-only分页位置正确，不等终态纠正。 | 直接要求；start/complete乱序、重复、同Turn多段与持久对账反证。 |
| RV12 | R07 | 06:281–291 | 阅读锚点同时验证DOM和消息身份；程序scroll不成为用户输入；无用户操作不跳顶；分页原位置连续。 | 指定机制；React复用、折叠高度、prepend和历史刷新均需核。 |
| RV13 | R07 | 06:283–289,291 | 保持底部跟随、用户滚动暂停、主动回底恢复、20秒active恢复；仅accepted Send立即回底，Heartbeat不强制回底；滚动状态不持久化。 | 直接保留要求；无active时计时不回底。 |
| RV14 | R08 | 06 §0.4:106；06:304；R08 | 修掉可定位渲染慢逻辑；中间纯增量及身份配对按帧合并、控制终态立即；不改事件文本顺序身份，不堆已完成输出、不增加事实缓存。 | 直接要求；证据须区分逻辑／浏览器与真设备性能，不捏造帧率。 |
| RV15 | R09 | 06:195–199 | 通知沿既有全局active观察而非当前页，owner为Profile+stored；Active→Idle仅核验；连续epoch回放真实正常完成及持久最终assistant才可通知；失败／取消／中间输出不通知。 | 直接保留要求；不增加resume/activate/轮询/WS或后端通知服务。 |
| RV16 | R09 | 06:199–203 | 后台才通知、固定中文标题和真实末条回复开头，无LLM摘要；重复/旧异步/断线/重连不补发；多Conversation分别通知、所有Turn结束解保活。 | 直接要求；跨Profile同ID和查看B时A完成。 |
| RV17 | R09 | 06:201 | 覆盖升级实际使用新HIGH+系统默认音通道；尽量保留已可识别主动静音／关闭，不能同名重注册冒称提升；旧Android识别限制如实。 | 直接指定机制；新装、已旧默认低、主动静音/禁用分别核。 |
| RV18 | R09 | 06:197,202–203 | 权限拒绝不破坏对话；点击正确Profile／Conversation、冷启动认证后保留目标；桥接仅可信APK主frame；系统回收不保证且不影响云端。 | 直接保留安全边界；单测不等真WebView/通知实机。 |
| RV19 | R10 | 06:181–191；C02 | Android壳提供实测380 CSS px竖屏逻辑视口并等比显示；普通网页不整页断点缩放；横屏／大屏不反向放大、键盘不改缩放基准。 | 最后380覆盖旧360/390；应有真实WebView innerWidth/比例证据。 |
| RV20 | R10 | 06:183–191 | 设备实时Insets避让，Android顶栏56px／上下4px，键盘避让保持；不硬编码24px，普通浏览器不变。 | 直接保留要求；需区别布局计算与真实设备呈现。 |
| RV21 | R10 | 06:189 | 原生首次正常加载；后台／解锁回前台即重载并清退避；WS失败10/15/20/30秒循环恢复；附件/认证不受恢复打断，草稿路由Cookie与通知目标保留。 | 本轮壳改动须保留原生恢复契约；JS慢历史已连接不误判。 |
| RV22 | R11 | 06:187；R11 | 已有logo不重设计；深纸背景填满；adaptive安全区及普通mask完整可辨不过小、无四周白边；核产物实际图标。 | 直接要求；生成脚本或尺寸断言不能单独证明视觉。 |
| RV23 | R12 | 08 §1–1.1 初始化身份接线约束 | 显式改绑后按目标Profile核物理Session确属ref，再沿目标原生session_key；无key沿compression身份，入口key不可认领目标alias。 | 指定机制；source不同同key合法历史不得迁移/清理/合并；内部可信冲突仍拒绝。 |
| RV24 | R12 | 08 §1.1绑定不变量 | 只显式绑定/解绑改目标；改绑B后A晚结果不回绑不注入B；保留A结果；compression同身份，new/reset/fork新身份且不继承；不合并历史Notebook排期。 | 直接保留边界；原生未绑定路径不变；adapter投递身份仍保留。 |
| RV25 | R12 | 08 §1；§1.1 | 绑定目标owner隔离；微信入站沿adapter正常回复，Web/Heartbeat不自动向微信；不同入口不改source/session_key伪装绑定。 | 直接保留边界；只用隔离合成数据，不实际重绑/发送生产。 |
| RV26 | R13 | R13；C01,C07；06:181,203 | 全部修复后统一最终dist/APK；版本递增、签名与现有可覆盖升级一致、APK内置同一最终dist；不以纯线上壳代替。 | 直接要求；核版本/证书/资源hash/构建版本和构建时间，缺设备升级证据如实。 |
| RV27 | R13,R16 | R13,R16；C01,C06 | 交付候选有相关检查和完整证据，当前适用违规及必要证据缺口未关闭不能称已测好；真实UI/Provider/设备与隔离测试明确分界。 | 直接完成条件；Verification与真实Validation分别判断。 |
| RV28 | R14 | R14；C04 | 不重开旧Kimi实验，不改旧历史／排期／System Prompt。 | 明确排除项；检查本轮差异与取证行为。 |
| RV29 | R15 | R15；C05,C08 | 保护已有dirty、签名私钥／凭据／私人回放不进Git或公开包；UI只用新建hiddenIAB，不变用户显示；分包与主审可追溯。 | 直接执行约束；不要求为审查触碰生产。 |
| RV30 | R16 | R16；C07 | 本轮仅本地修复、检查、提交及统一打包准备；不擅自部署、改Profile／绑定／排期或发生产测试消息。 | 明确授权边界。 |
| RV31 | 全轮 | 06 §0.4–0.5；§2.1,2.9 | 薄客户端／增量兼容：事实server owner、无持久事实镜像、无伪历史；旧客户端默认／错误／返回不变；新字段可选，必要最小接缝有owner/错误/未知/锁/证据。 | 全轮架构约束；不以新功能名扩大范围。 |
| RV32 | R04–R08,R15 | 06:265,267–277；R15 | 保持现有设计、Pin、Profile图标及并行dirty；本轮Timeline变更不破坏failed_turn真实类型、部分正文、临时slash、System/Compaction宽度与审批现有语义。 | 保留非回归边界，检查本轮触及路径与对应证据，非重做其它能力。 |

32条覆盖R01–R16全轮；保留契约按本轮影响复核，索引明示只修对应故障，不把未修改的其它长期能力扩大为新实现任务。真实设备/模型证据是否必要依各条完成宣称和原文，未知不得判不适用。

### 当前复审判据的模板列索引

上方先行判据原文未改；下表仅按报告规定六列建立索引，保持来源、必要不变量、适用条件及判据完全相同，不变更判据。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| RV01 | requirements R01；06 §0.5；R01 | 直接要求；核真实SDK调用兼容和正式标题接线，并区分受控与真实Provider证据。 | 新会话辅助标题通过既有模型／Provider／推理选择生成；消除unexpected keyword错误；辅助失败不能破坏已受理Turn。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV01 |
| RV02 | 06:293；§0.5:113–115；R02 | 指定机制；不能以同文、running或另一会话事件猜受理。 | 每次实际Send可选关联ID由原生writer写真实用户行展示metadata；不进入模型消息；省略ID保持原生。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV02 |
| RV03 | 06:293；R02 | 指定机制；跨Profile、相同ID、重启、rewind需证明隔离与不复活。 | 状态查询只读核目标Profile／Conversation精确ID，accepted携实际回执，未见事实unknown；退休／rewind仅证历史受理。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV03 |
| RV04 | 06:234,293；R02 | 直接要求及必要恢复不变量；核正式前后端纵向接线。 | 丢ACK／断连后可恢复accepted，不永久unknown；unknown不得自动重发，accepted后历史读取失败不变发送失败。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV04 |
| RV05 | 06:293；08 §1；R02 | 直接要求；核事件和直接响应竞态、后续草稿、跨路由恢复。 | 晚ACK只消费原捕获草稿一次；保留后续文本／附件；导航不改owner；取消和终态竞态不造成重复提交。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV05 |
| RV06 | 06:271,295；R03 | 指定机制；不能由Thinking、status或结束标记合成。 | 已持久Heartbeat沿原生回调即时发原文／UID；执行中已有客户端无需等待终态看到独立卡；重复事件／历史按UID合并。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV06 |
| RV07 | 06:271；R03 | 直接要求；普通提及、assistant引用、旧无包装模板不分类；HEARTBEAT_OVER无额外行为。 | 仅完整user heartbeat包装分类，独立折叠Heartbeat卡，心电图标／陶土色／同类宽度；展开仅去外包装、保留timestamp与正文，不给用户编辑／附件／外时间。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV07 |
| RV08 | 07 §8.15:1445–1462；R03 | 本轮故障修复须保留的契约；不把非本轮功能重做当完成要求。 | 保持目标Profile全局Noting模板分支、英文timestamp模板、可选Additional；UI唤醒沿原生Main路由／模型／上下文／持久化，不误作微信入站或自动回复。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV08 |
| RV09 | 07 §8.15:1464–1470；R03 | 保留不变量；只审本轮改动影响及有效回归证据，不扩实现范围。 | Heartbeat Conversation-owner、合法compression tip、跨页面／重启、pause/clear、claim/refund/并发和原生关闭分支均不受即时展示修复破坏。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV09 |
| RV10 | 06:230–232,291；R04,R06 | 直接要求；包括loading、成功、失败、完成回执及会话重入。 | 详情懒加载仅原facet替换；已结束Thinking按真实UID/row/occurrence定位；旧尾锚不能覆盖持久位置；切回无active会话不尾部重复。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV10 |
| RV11 | 06:287,291；R05 | 直接要求；start/complete乱序、重复、同Turn多段与持久对账反证。 | 流式Thinking及并行工具各自单卡，真实顺序和身份从构建到完成稳定；失败工具及result-only分页位置正确，不等终态纠正。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV11 |
| RV12 | 06:281–291；R07 | 指定机制；React复用、折叠高度、prepend和历史刷新均需核。 | 阅读锚点同时验证DOM和消息身份；程序scroll不成为用户输入；无用户操作不跳顶；分页原位置连续。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV12 |
| RV13 | 06:283–289,291；R07 | 直接保留要求；无active时计时不回底。 | 保持底部跟随、用户滚动暂停、主动回底恢复、20秒active恢复；仅accepted Send立即回底，Heartbeat不强制回底；滚动状态不持久化。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV13 |
| RV14 | 06 §0.4:106；06:304；R08；R08 | 直接要求；证据须区分逻辑／浏览器与真设备性能，不捏造帧率。 | 修掉可定位渲染慢逻辑；中间纯增量及身份配对按帧合并、控制终态立即；不改事件文本顺序身份，不堆已完成输出、不增加事实缓存。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV14 |
| RV15 | 06:195–199；R09 | 直接保留要求；不增加resume/activate/轮询/WS或后端通知服务。 | 通知沿既有全局active观察而非当前页，owner为Profile+stored；Active→Idle仅核验；连续epoch回放真实正常完成及持久最终assistant才可通知；失败／取消／中间输出不通知。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV15 |
| RV16 | 06:199–203；R09 | 直接要求；跨Profile同ID和查看B时A完成。 | 后台才通知、固定中文标题和真实末条回复开头，无LLM摘要；重复/旧异步/断线/重连不补发；多Conversation分别通知、所有Turn结束解保活。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV16 |
| RV17 | 06:201；R09 | 直接指定机制；新装、已旧默认低、主动静音/禁用分别核。 | 覆盖升级实际使用新HIGH+系统默认音通道；尽量保留已可识别主动静音／关闭，不能同名重注册冒称提升；旧Android识别限制如实。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV17 |
| RV18 | 06:197,202–203；R09 | 直接保留安全边界；单测不等真WebView/通知实机。 | 权限拒绝不破坏对话；点击正确Profile／Conversation、冷启动认证后保留目标；桥接仅可信APK主frame；系统回收不保证且不影响云端。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV18 |
| RV19 | 06:181–191；C02；R10 | 最后380覆盖旧360/390；应有真实WebView innerWidth/比例证据。 | Android壳提供实测380 CSS px竖屏逻辑视口并等比显示；普通网页不整页断点缩放；横屏／大屏不反向放大、键盘不改缩放基准。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV19 |
| RV20 | 06:183–191；R10 | 直接保留要求；需区别布局计算与真实设备呈现。 | 设备实时Insets避让，Android顶栏56px／上下4px，键盘避让保持；不硬编码24px，普通浏览器不变。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV20 |
| RV21 | 06:189；R10 | 本轮壳改动须保留原生恢复契约；JS慢历史已连接不误判。 | 原生首次正常加载；后台／解锁回前台即重载并清退避；WS失败10/15/20/30秒循环恢复；附件/认证不受恢复打断，草稿路由Cookie与通知目标保留。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV21 |
| RV22 | 06:187；R11；R11 | 直接要求；生成脚本或尺寸断言不能单独证明视觉。 | 已有logo不重设计；深纸背景填满；adaptive安全区及普通mask完整可辨不过小、无四周白边；核产物实际图标。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV22 |
| RV23 | 08 §1–1.1 初始化身份接线约束；R12 | 指定机制；source不同同key合法历史不得迁移/清理/合并；内部可信冲突仍拒绝。 | 显式改绑后按目标Profile核物理Session确属ref，再沿目标原生session_key；无key沿compression身份，入口key不可认领目标alias。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV23 |
| RV24 | 08 §1.1绑定不变量；R12 | 直接保留边界；原生未绑定路径不变；adapter投递身份仍保留。 | 只显式绑定/解绑改目标；改绑B后A晚结果不回绑不注入B；保留A结果；compression同身份，new/reset/fork新身份且不继承；不合并历史Notebook排期。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV24 |
| RV25 | 08 §1；§1.1；R12 | 直接保留边界；只用隔离合成数据，不实际重绑/发送生产。 | 绑定目标owner隔离；微信入站沿adapter正常回复，Web/Heartbeat不自动向微信；不同入口不改source/session_key伪装绑定。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV25 |
| RV26 | R13；C01,C07；06:181,203；R13 | 直接要求；核版本/证书/资源hash/构建版本和构建时间，缺设备升级证据如实。 | 全部修复后统一最终dist/APK；版本递增、签名与现有可覆盖升级一致、APK内置同一最终dist；不以纯线上壳代替。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV26 |
| RV27 | R13,R16；C01,C06；R13,R16 | 直接完成条件；Verification与真实Validation分别判断。 | 交付候选有相关检查和完整证据，当前适用违规及必要证据缺口未关闭不能称已测好；真实UI/Provider/设备与隔离测试明确分界。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV27 |
| RV28 | R14；C04；R14 | 明确排除项；检查本轮差异与取证行为。 | 不重开旧Kimi实验，不改旧历史／排期／System Prompt。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV28 |
| RV29 | R15；C05,C08；R15 | 直接执行约束；不要求为审查触碰生产。 | 保护已有dirty、签名私钥／凭据／私人回放不进Git或公开包；UI只用新建hiddenIAB，不变用户显示；分包与主审可追溯。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV29 |
| RV30 | R16；C07；R16 | 明确授权边界。 | 本轮仅本地修复、检查、提交及统一打包准备；不擅自部署、改Profile／绑定／排期或发生产测试消息。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV30 |
| RV31 | 06 §0.4–0.5；§2.1,2.9；全轮 | 全轮架构约束；不以新功能名扩大范围。 | 薄客户端／增量兼容：事实server owner、无持久事实镜像、无伪历史；旧客户端默认／错误／返回不变；新字段可选，必要最小接缝有owner/错误/未知/锁/证据。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV31 |
| RV32 | 06:265,267–277；R15；R04–R08,R15 | 保留非回归边界，检查本轮触及路径与对应证据，非重做其它能力。 | 保持现有设计、Pin、Profile图标及并行dirty；本轮Timeline变更不破坏failed_turn真实类型、部分正文、临时slash、System/Compaction宽度与审批现有语义。 | 依本行不变量在正式路径核证；缺必要实际结果判证据不足 | 第3节RV32 |


### 2026-10-21 第三次独立判据原件（先行落盘，原样保留）

# 最终独立 Verification 判据（先于实现调查落盘）

建立时间：2026-10-21。仅阅读 autonomous-run、spec-implementation-review、冻结 `57ffa1c355b4eef9b73f6ab10d3fb6da42b43176` 的 snapshot-index、requirements 及其指定 06 §0.4–0.5／§1–2相关原文、08 §1–1.1、07 §8.15 后提取；尚未阅读代码、测试、实现报告、历史审查、CLAUDE 或 plan。下表为后续追加到报告第2节的原始判据，不随实现降低。

| 条款ID | 来源原文与位置 | 独立审查判据／必要不变量 | 适用条件与判断理由 |
|---|---|---|---|
| FV01 | R01；06 §0.5 | 新会话辅助标题调用不再因 `_reasoning_config` 参数错误失败；实际原生模型／Provider／推理选择沿用，不另造路由。 | 新会话标题正式入口，含实际SDK调用边界；仅无异常的桩不能证明实际接口可用。 |
| FV02 | R02；06 §1.5提交受理恢复、§0.5.4/6 | 每次Send可选唯一client_submission_id经正式writer存入真实用户行display metadata，不进入模型；回执／事件／只读查询对精确Profile＋Conversation关联，accepted必须有真实受理事实。 | ACK丢失、断线、已回复、同文、跨owner、历史退休／rewind；unknown不证明拒绝，不以running或正文相同猜测。 |
| FV03 | R02；06 §1.5提交恢复、§1.6/1.10 | 重连或查询恢复后能退出永久unknown，无盲重发／双提交；晚到ACK至多消费原发送草稿一次，后来草稿保留；退休行只刷新权威历史，不插回。 | 未受理与已受理分支、旧客户端省略ID行为、切换Profile／Conversation、失败恢复。 |
| FV04 | R03；06 §1.5Heartbeat即时展示、§1.4Heartbeat；07 §8.15 | Heartbeat真实用户行持久化后立即经原生回调发布原文UID／row，前端独立卡无需等Turn结束，重复／历史按UID合并；不得从Thinking、状态、结束标记合成。 | 已连接、首次执行中挂载、重连和完成后恢复；保留来源、时间、身份与原文。 |
| FV05 | R03；06 §1.4Heartbeat卡片 | 仅完整heartbeat包装的role=user分类；默认折叠、固定Heartbeat标题、心电图标／陶土橙主题与阅读宽度；展开保留内timestamp及正文，只去外包装；无Reply／编辑／附件／外时间。 | 普通提及、assistant引用、旧无包装模板不分类；HEARTBEAT_OVER不新增过滤或结束机制。 |
| FV06 | R04/R05/R06；06 §1.5顺序／阅读修复、工具连续性 | Thinking详情补齐原位替换facet；真实UID／row与工具occurrence决定完成和历史位置；已有持久位置优先于旧尾锚，失败工具及并行调用数量／顺序稳定，无短暂错位后纠正。 | 流式→历史、展开loading、无active切回旧Turn、多段Thinking、重复同名调用、parent在页外result在页内。 |
| FV07 | R07；06 §1.5滚动最终澄清 | 阅读锚点同时验证DOM仍连接与消息身份；程序scroll不变成用户请求；手动位置／分页锚点保持，无自行跳顶；默认底随、用户回底立即跟随、Send受理回底及20秒active恢复按既有规则。 | 内容增长、折叠、详情、后台Turn、会话切换、完成刷新、React节点复用；Heartbeat不新增强制回底。 |
| FV08 | R08；06 §0.4、§1.5流式合帧 | 修正可定位的明显渲染慢逻辑，正文／推理及对应身份投影同帧合并；事件事实逐条保留，控制／边界／终态立即发布并取消旧帧，不人工积压输出。 | 正式Controller和组件；性能主张限观察能力，不以计数或浏览器结果冒充真机帧率。 |
| FV09 | R09；06 §1.2 Android通知通道升级 | 升级迁移到不同的新HIGH通道＋系统默认音，不能靠同ID重注册提级；尽量识别并保留主动静音／关闭；旧系统识别限制如实报告。 | 覆盖旧默认通道、主动静音／禁用、已迁移／重复、权限拒绝和Android版本差异；真实响铃横幅需设备。 |
| FV10 | R09；06 §1.2原生通知完成／断线／权限 | 仅既有全局可观察Turn、后台且正常完成、连续连接epoch有效，核验真实最终持久Assistant；前台／失败／取消／Thinking／工具／断线旧结果不发；精确owner／Turn去重与点击路由。 | 多Conversation／Profile及同ID、电脑发起、并发、前台抑制、冷启动认证、跨刷新目标保持；不加查询面、独立WS或后台补发。 |
| FV11 | R10；06 §1.2逻辑视口与Insets | Android壳真实提供竖屏380 CSS px且等比，非前端断点整页scale；横屏大屏不反向放大，键盘不改缩放基准；真实状态栏Insets与键盘避让保持。 | 必须实测WebView innerWidth／比例／Insets／键盘；浏览器viewport或公式仅机制证据。 |
| FV12 | R11；06 §1.2图标 | 复用既有logo、深纸色背景满铺，adaptive安全区与legacy实际mask下完整可辨、不过小、无白边；不改logo内容。 | 检查最终APK资源与mask；外部预览可支持资源判断但不冒充安装后launcher验收。 |
| FV13 | R12；08 §1–1.1初始化身份约束 | 显式改绑后Gateway先在目标Profile核物理Session属于ref，再用目标原生session_key／compression身份；入口key只作可变投递定位，不宣称alias，不合并旧身份历史Notebook排期。 | target有key／无key、跨source同key历史、真实可信alias冲突；冲突仍拒绝，receiver／sender保留。 |
| FV14 | R12；08 §1.1绑定不变量 | 只有显式bind／unbind改目标；晚到A结果不能回绑A或注入B，同Conversation合法压缩tip可更新locator；fork／new不继承，未绑定路径原生。 | Web↔微信恢复、runtime回收、suspended／delegation、Profile身份与原模型路由保持；本轮不主动生产重绑或发消息。 |
| FV15 | R13；C01/C07；06 §1.2APK交付 | 全部前端修复收敛后统一构建dist和APK、递增版本、同一最终dist内置、既有签名可覆盖安装；精确源码、产物hash与签名证据可追溯，不将旧包当当前包。 | 最终dist／APK必须到位；构建中不能判完成；真实安装覆盖与签名兼容区分。 |
| FV16 | R14/R16；C04/C07 | 不重开旧Kimi调查，不改历史／排期／root，不主动生产消息、绑定、配置、重启或部署；本轮止于本地修复、验证及打包准备。 | 所有本轮diff与取证操作。 |
| FV17 | R15/C05/C06/C08；06 §0.4–0.5 | 保护既有并行dirty、凭据／私人原件不入Git／公开产物；产品代码只做增量native接缝，不增独立转录库、执行器、事实持久缓存；旧接口和关闭路径保持。 | 所有变更；UI仅自建hidden IAB，证据区分mock、组件DOM、真实SDK、实际Android；未验不降为不适用。 |
| FV18 | R03；07 §8.15 | Heartbeat仍沿目标Profile全局noting开关、conversation_ref owner、UI原生提交／run_conversation和模型路由；busy／用户优先／tick认领退款保持，不因本轮显示修复复制执行或改时戳。 | 全局关闭原生路径、local noting off、host-only／页面关闭、跨owner、压缩、重启、并发定义变更；此轮不扩大Heartbeat功能。 |
| FV19 | R10/R13；06 §1.2自动恢复 | 壳改动保留首次正常加载；回前台即时原生reload且重置10/15/20/30秒监测；WS真实connected停止，JS无响应独立兜底；不清草稿Cookie路由、不打断认证附件。 | Android视口／打包改动的相关回归，真实WebView生命周期证据与纯单元区分。 |

判定取值：符合／违规／证据不足／有依据的不适用。产品语义明确而环境缺证的适用项仍为证据不足。FV10、FV18、FV19仅审本轮修改所需的保留契约与影响，不能由此新增功能范围；FV11/15要求本轮真实目标与最终产物成立。统计按本表19条回查。


### 第三次独立判据模板列索引

以下仅将同一原始判据映射到既有六列表，不新增或降低判据。FV10／FV18／FV19按原件的回归范围读取，不能扩成完整旧产品重新施工。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| FV01 | R01；06 §0.5 | 行为／机制／边界；新会话标题正式入口，含实际SDK调用边界；仅无异常的桩不能证明实际接口可用。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | 新会话辅助标题调用不再因 `_reasoning_config` 参数错误失败；实际原生模型／Provider／推理选择沿用，不另造路由。 | 第3节当前FV01 |
| FV02 | R02；06 §1.5提交受理恢复、§0.5.4/6 | 行为／机制／边界；ACK丢失、断线、已回复、同文、跨owner、历史退休／rewind；unknown不证明拒绝，不以running或正文相同猜测。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | 每次Send可选唯一client_submission_id经正式writer存入真实用户行display metadata，不进入模型；回执／事件／只读查询对精确Profile＋Conversation关联，accepted必须有真实受理事实。 | 第3节当前FV02 |
| FV03 | R02；06 §1.5提交恢复、§1.6/1.10 | 行为／机制／边界；未受理与已受理分支、旧客户端省略ID行为、切换Profile／Conversation、失败恢复。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | 重连或查询恢复后能退出永久unknown，无盲重发／双提交；晚到ACK至多消费原发送草稿一次，后来草稿保留；退休行只刷新权威历史，不插回。 | 第3节当前FV03 |
| FV04 | R03；06 §1.5Heartbeat即时展示、§1.4Heartbeat；07 §8.15 | 行为／机制／边界；已连接、首次执行中挂载、重连和完成后恢复；保留来源、时间、身份与原文。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | Heartbeat真实用户行持久化后立即经原生回调发布原文UID／row，前端独立卡无需等Turn结束，重复／历史按UID合并；不得从Thinking、状态、结束标记合成。 | 第3节当前FV04 |
| FV05 | R03；06 §1.4Heartbeat卡片 | 行为／机制／边界；普通提及、assistant引用、旧无包装模板不分类；HEARTBEAT_OVER不新增过滤或结束机制。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | 仅完整heartbeat包装的role=user分类；默认折叠、固定Heartbeat标题、心电图标／陶土橙主题与阅读宽度；展开保留内timestamp及正文，只去外包装；无Reply／编辑／附件／外时间。 | 第3节当前FV05 |
| FV06 | R04/R05/R06；06 §1.5顺序／阅读修复、工具连续性 | 行为／机制／边界；流式→历史、展开loading、无active切回旧Turn、多段Thinking、重复同名调用、parent在页外result在页内。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | Thinking详情补齐原位替换facet；真实UID／row与工具occurrence决定完成和历史位置；已有持久位置优先于旧尾锚，失败工具及并行调用数量／顺序稳定，无短暂错位后纠正。 | 第3节当前FV06 |
| FV07 | R07；06 §1.5滚动最终澄清 | 行为／机制／边界；内容增长、折叠、详情、后台Turn、会话切换、完成刷新、React节点复用；Heartbeat不新增强制回底。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | 阅读锚点同时验证DOM仍连接与消息身份；程序scroll不变成用户请求；手动位置／分页锚点保持，无自行跳顶；默认底随、用户回底立即跟随、Send受理回底及20秒active恢复按既有规则。 | 第3节当前FV07 |
| FV08 | R08；06 §0.4、§1.5流式合帧 | 行为／机制／边界；正式Controller和组件；性能主张限观察能力，不以计数或浏览器结果冒充真机帧率。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | 修正可定位的明显渲染慢逻辑，正文／推理及对应身份投影同帧合并；事件事实逐条保留，控制／边界／终态立即发布并取消旧帧，不人工积压输出。 | 第3节当前FV08 |
| FV09 | R09；06 §1.2 Android通知通道升级 | 行为／机制／边界；覆盖旧默认通道、主动静音／禁用、已迁移／重复、权限拒绝和Android版本差异；真实响铃横幅需设备。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | 升级迁移到不同的新HIGH通道＋系统默认音，不能靠同ID重注册提级；尽量识别并保留主动静音／关闭；旧系统识别限制如实报告。 | 第3节当前FV09 |
| FV10 | R09；06 §1.2原生通知完成／断线／权限 | 行为／机制／边界；多Conversation／Profile及同ID、电脑发起、并发、前台抑制、冷启动认证、跨刷新目标保持；不加查询面、独立WS或后台补发。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | 仅既有全局可观察Turn、后台且正常完成、连续连接epoch有效，核验真实最终持久Assistant；前台／失败／取消／Thinking／工具／断线旧结果不发；精确owner／Turn去重与点击路由。 | 第3节当前FV10 |
| FV11 | R10；06 §1.2逻辑视口与Insets | 行为／机制／边界；必须实测WebView innerWidth／比例／Insets／键盘；浏览器viewport或公式仅机制证据。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | Android壳真实提供竖屏380 CSS px且等比，非前端断点整页scale；横屏大屏不反向放大，键盘不改缩放基准；真实状态栏Insets与键盘避让保持。 | 第3节当前FV11 |
| FV12 | R11；06 §1.2图标 | 行为／机制／边界；检查最终APK资源与mask；外部预览可支持资源判断但不冒充安装后launcher验收。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | 复用既有logo、深纸色背景满铺，adaptive安全区与legacy实际mask下完整可辨、不过小、无白边；不改logo内容。 | 第3节当前FV12 |
| FV13 | R12；08 §1–1.1初始化身份约束 | 行为／机制／边界；target有key／无key、跨source同key历史、真实可信alias冲突；冲突仍拒绝，receiver／sender保留。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | 显式改绑后Gateway先在目标Profile核物理Session属于ref，再用目标原生session_key／compression身份；入口key只作可变投递定位，不宣称alias，不合并旧身份历史Notebook排期。 | 第3节当前FV13 |
| FV14 | R12；08 §1.1绑定不变量 | 行为／机制／边界；Web↔微信恢复、runtime回收、suspended／delegation、Profile身份与原模型路由保持；本轮不主动生产重绑或发消息。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | 只有显式bind／unbind改目标；晚到A结果不能回绑A或注入B，同Conversation合法压缩tip可更新locator；fork／new不继承，未绑定路径原生。 | 第3节当前FV14 |
| FV15 | R13；C01/C07；06 §1.2APK交付 | 行为／机制／边界；最终dist／APK必须到位；构建中不能判完成；真实安装覆盖与签名兼容区分。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | 全部前端修复收敛后统一构建dist和APK、递增版本、同一最终dist内置、既有签名可覆盖安装；精确源码、产物hash与签名证据可追溯，不将旧包当当前包。 | 第3节当前FV15 |
| FV16 | R14/R16；C04/C07 | 行为／机制／边界；所有本轮diff与取证操作。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | 不重开旧Kimi调查，不改历史／排期／root，不主动生产消息、绑定、配置、重启或部署；本轮止于本地修复、验证及打包准备。 | 第3节当前FV16 |
| FV17 | R15/C05/C06/C08；06 §0.4–0.5 | 行为／机制／边界；所有变更；UI仅自建hidden IAB，证据区分mock、组件DOM、真实SDK、实际Android；未验不降为不适用。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | 保护既有并行dirty、凭据／私人原件不入Git／公开产物；产品代码只做增量native接缝，不增独立转录库、执行器、事实持久缓存；旧接口和关闭路径保持。 | 第3节当前FV17 |
| FV18 | R03；07 §8.15 | 行为／机制／边界；全局关闭原生路径、local noting off、host-only／页面关闭、跨owner、压缩、重启、并发定义变更；此轮不扩大Heartbeat功能。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | Heartbeat仍沿目标Profile全局noting开关、conversation_ref owner、UI原生提交／run_conversation和模型路由；busy／用户优先／tick认领退款保持，不因本轮显示修复复制执行或改时戳。 | 第3节当前FV18 |
| FV19 | R10/R13；06 §1.2自动恢复 | 行为／机制／边界；Android视口／打包改动的相关回归，真实WebView生命周期证据与纯单元区分。 | 直接要求及为保持原生契约必要的不变量，不引入新产品范围 | 壳改动保留首次正常加载；回前台即时原生reload且重置10/15/20/30秒监测；WS真实connected停止，JS无响应独立兜底；不清草稿Cookie路由、不打断认证附件。 | 第3节当前FV19 |

## 3. 逐条实现证据

下表后端位置相对 `/Users/edgar/code/hermes-secretary`，Web位置相对 `/Users/edgar/code/hermes-secretary-web`。E01–E12的具体日志、输入和版本边界在第4节；第2节对应行给出每项的独立不变量，构成本表判定链的上游。没有把实现报告的自评作为判据。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| V01 | `agent/title_generator.py generate_title → auxiliary_client.py _prepare_aux_request:7529 → _build_call_kwargs:6793 → auxiliary_reasoning_floor.py:33 uses_private_reasoning_config → _relay_sync_completion`；同Provider重试:3791、fallback:4033–4089均传实际client | 静态追三类请求、同步/异步；真实OpenAI SDK+MockTransport覆盖Chat和Messages；E01单次真实Kimi k3-256k返回标题，2.49秒、私有字段false、无失败 | E01；`tests/agent/test_auxiliary_reasoning_transport.py:23–145` | 符合：参数按实际adapter而非URL猜测；原生公开reasoning、Provider/凭据/fallback保持 | 真实请求只取代表Kimi Chat；Messages/重试故障分支为隔离SDK，未声明生产新会话上线 |
| V02 | Web `controller.ts:1504–1595 send/executeSend`生成UUID → `submitNative:1704` → `prompt.submit_idle` → `methods_prompt.py:661,702`原生锁/metadata → inline writer及native `persist_user_display_metadata`；`methods_submit_idle.py:174–227`真实row回执 → event/ACK → Web `reconcileEventView:1256` | 精确ID落真实用户行；模型请求不含ID；预写失败后native flush、compute实际frame consumer/loop均覆盖；重复ID拒绝 | E02；`test_submission_recovery.py:13–32,98–121,155–179` | 符合：真实writer、受理行、回执/事件及Web消费完整接线，无第二账本 | worker为同进程调用真实入口，无OS管道/进程重启声明 |
| V03 | `methods_submit_idle.py:70–99,254–267`按目标Profile、同Conversation binding只读SQL；Web `controller.ts:1604–1694,1753–1787`事务身份、admitted护栏、状态核验仅refresh | 相同正文/异会话/异Profile不认成功；压缩tip和退休行可证明历史受理但不复活；unknown不重发；事件先ACK、旧ACK晚失败、新未知事务/草稿与rewind临时结果竞态覆盖 | E02、E03；`test_submission_recovery.py:35–95,124–152`；`controller-submission-review.test.ts`5例 | 符合：精确事实与草稿生命周期分离，丢ACK可收敛；旧客户端省略ID仍原生 | 未承诺跨整页Controller销毁保留unknown事务；DB reopen是新连接而非服务重启 |
| V04 | 后端 `prompt_turn.py:913–934`安装/恢复observer → `agent/turn_context.py:1024–1048`实际持久后回调 → `heartbeat_presentation.py:10–71`校验本runtime/agent/token、active row、UID/原文 → `_emit(message.user_committed)` → Web `controller.ts:1256–1277`即刻adopt → `projection.ts:344`包装分类 | E02实际native loop先落库，在Provider gate未释放及message.complete前已有唯一原文事件；重复observer/历史重放UID去重；持久batch失败及退休/未落库行无卡；Web mid-session commit先于Thinking | E02、E03；`test_heartbeat_card_commit.py`4例；`controller-mobile-recovery.test.ts:373` | 违规（原候选9fabcdd）：正常载体接线符合，但入环前异常后误置published，后续同回调无法补发；真实native emit负对照已复现，详见F03/第6节 | 机制/组件证据，未声明真实浏览器在用户屏幕即时呈现；原候选异常分支有失败反例；3b48cf0新增修补及17/7项证据待新审查者复审 |
| V05 | 原 `secretary/heartbeat.py`与后台Conversation owner未改；本轮仅增加上述observer；Web `projection.ts:334–346`只匹配原生user完整包装，`App.tsx`既有Heartbeat卡片渲染 | 差异核验无调度/模板/结束词/root改动；现有timeline组件覆盖空/有Additional prompt、timestamp保留、Assistant引用/普通提及/旧模板/不完整包装不猜分类 | E03；`src/core/timeline.test.tsx:46–101`；当前后端差异 | 符合：没有把展示修复扩大为调度或结束机制，源身份/正文保持 | 不重验完整Heartbeat调度产品；其它既有Heartbeat能力不作为新交付 |
| V06 | Web `controller.ts:216–224 acceptHistoryDetails → commitHistoryView:1028 → reconcileLiveHistory`；`projection.ts:818–835`退休前驱传真实边界且保留更晚anchor；`projectTimelineNodes:848–902`真实位置优先 | deferred/full详情原位补齐、同Turn未退休failed tool后缀保持在后来user之前；当前expected对象、row ID、UID、role全部匹配才接受详情，切会话取消旧请求 | E04、E05；`mobile-render-order.test.ts`；`history-details.ts` | 符合：不因展开/Loading details将后缀丢到全局尾，失效详情不复活其它行 | jsdom组件/Controller和真实数据离线回放；实际浏览器像素展开仍交Validation |
| V07 | `projection.ts:174–277`按call occurrence组装；`:785–805`active tool adoption；`:865–889`parent缺页时按结果UID接管，保留detailSources | 失败result、parent页外、parent后补、并行调用乱序start/complete、后继Thinking及完整/延迟详情均断言一张卡与真实序列；真实512帧回放使用Controller相同reduce→seal→reconcile顺序 | E04、E05；`mobile-render-order.test.ts`；`timeline-replay-20261021/replay.test.ts` | 符合：位置取源UID/occurrence，不按完成先后或正文排序，不靠Turn结束纠正 | 不把离线真实数据回放当在线UI观察 |
| V08 | `controller.ts:706–813 select`同owner恢复history/live，`commitHistoryView`统一对账；`projection.ts:871–884`已有持久位置优先旧complete尾anchor | E05同一真实fixture旧HEAD早期737字符Thinking挂尾，候选回实际UID位置；新增idle select及早期Turn回归；跨Turn anchor不会传递 | E04、E05；`nodes.json`仅身份/长度 | 符合：无active时旧Thinking仍有正确持久位置，不重挂尾 | 不打印或提交私人回放正文；无重新打开生产会话操作 |
| V09 | `App.tsx:493–502`只有同scope acceptedSend revision恢复跟随；`chat-presentation.tsx:77–117`锚点核当前identity；`:139–255`placedTop排除程序scroll、ResizeObserver原位补偿、20秒active规则 | 实际hook/组件几何驱动覆盖DOM被复用、相同UID替换DOM、连续8次resize+scroll、程序滚动不延长手动hold、idle到期后背景Turn不回底、分页prepend与底边跟随 | E04；`timeline-reading.test.tsx`；`timeline-stream-layout.test.tsx` | 符合：程序重排不夺取用户所有权，DOM连接本身不再被当身份；既有主动回底/20秒规则保持 | 真实设备滚动/惯性/异步浏览器布局未验，不能声称所有现场跳动已实机消失 |
| V10 | `chat-presentation.tsx:147–164`following路径不遍历几何；`projection.ts:913–924 stableTimelineNodes`复用未变节点；`controller.ts`既有stream render合帧与即时终态发布保持 | 200卡组件回归following初始化及增长0次卡片getBoundingClientRect，上滚仍采集anchor；完整Web套件通过；未新增持久API镜像/回放限速 | E04、E06；`timeline-stream-layout.test.tsx` | 符合：去除实际每帧O(history)几何测量，内容/事件处理和原生顺序保持 | 无真实设备FPS、低端设备CPU或网络耗时改善声明 |
| V11 | Android `HermesNotifications.kt:18–76`新`hermes-completion-v2`；旧用户importance/API29可识别设置、null/custom sound、低重要度/禁用保持；`complete:78–91`HIGH与CATEGORY_MESSAGE | E07 Robolectric 28/29/35覆盖新装HIGH+默认音、旧DEFAULT迁移、主动静音/禁用、自定义声/振动、已建v2不覆盖；E10验证当前APK存在并签名 | E07、E10；`HermesNotificationsTest.kt`11例 | 证据不足：源码和Android API对象机制符合；实际用户要求的响铃与横幅仍无真实设备观察 | 厂商桌面、系统DND/音量、通知设置及覆盖升级后实际提示音/横幅未验，不可由Robolectric替代 |
| V12 | Web `session-recovery.ts SessionActivity → android-turns.ts observe/baseline/complete → android-turns-proof.ts terminalReceipt/readCompletedReply`；Native `MainActivity.kt:73–94,118–125,173–198`信任边界/前后台；`AndroidBridgeState.kt`owner目标/去重；原生service生命周期 | E07/E08覆盖全局列表而非当前active、跨Profile同ID、前台抑制、断线epoch/重复/失效、最终真实receipt+两行详情、点击目标和权限拒绝；源码无批量resume/独立WS/额外轮询 | E07、E08；`android-turns.test.ts`54例、`AndroidBridgeStateTest`11、`AndroidServiceTest`7 | 符合：迁移没有扩大观察权限或云端行为；证据不足时放弃通知，原生前台抑制和owner保持 | 背景系统冻结/回收不保证提示；实际设备/真实模型体验仍属V11及Validation缺口 |
| V13 | `AndroidViewport.kt:43–65 calculate/from/configure`原生稳定窗口扩展；`MainActivity.kt:97–117,141–162`真实设置/Insets/IME；`PackagedWebViewClient.kt:80–98,134–146`仅认证APK文档替换meta，认证页恢复原设置 | E09七个native测试验证360dp→380、等比scale .94736842、横屏836、平板不放大、状态栏转换、配置/IME padding及meta；代码无前端断点整页scale；source hashes30项匹配 | E09；`AndroidViewportTest.kt`；`geometry-cases.json` | 证据不足：指定原生机制已落实，但06:191要求的真正WebView `window.innerWidth`、比例与Insets/键盘实测尚缺 | Robolectric WebView shadow和算式不能证明Chromium实际viewport/旋转/命中坐标；API26–29真实分屏/厂商行为也未验 |
| V14 | `scripts/android-icons.mjs:14–41`原logo→108dp透明foreground中心56dp、独立#232120满底；真实5档生成PNG和adaptive XML；Gradle包入相同资源 | E09像素检查主体54–54.25dp、半径31.93–32.24dp在66dp安全区；旧62.18dp负对照失败；审查者亲看真实图层圆/圆角/方圆mask预览，完整可辨无白边；源码和30项资源hash匹配 | E09；`icon-checks.json`、`mask-preview/1024x1024.png`；E10最终APK | 符合：规定adaptive/普通资源机制及静态实际mask满足，无logo重设计 | 未宣称vivo桌面真实渲染/系统自动缩放体验；该视觉设备差异交Validation |
| V15 | `gateway/run_turn_runner.py:1127–1150 _build_fresh_agent → conversation_binding.py:20–35 agent_session_key`持Store lock，目标Profile DB核ref，再传目标原session_key/None → native `_init_session_state/initialize_conversation_identity` | E11沿正式bind control A→B、真实constructor kwargs与native初始化；desktop/pi-import目标，目标无native key/有native key/compression均覆盖；source入口对象/收发参数不改 | E11；`test_bound_agent_identity.py:21–114` | 符合：修复可变入口key冒充出生身份的正式接缝，不改路由归属 | AIAgent整体构造被替为真实native身份initializer；未跑真实微信入站模型 |
| V16 | 同上＋既有`allows_bound_target/restore_binding`及绑定控制锁/晚回流边界 | E11旧key直接复现aliases conflict、新接缝成功；旧不同source alias共存，前后Secretary表、sessions/messages全行相等；branch不继承、异Profile/伪binding/真正alias冲突仍拒绝；既有晚结果不回绑测试111范围通过 | E11；`test_bound_agent_identity.py:47–156`及binding/invariant/control相关套件 | 符合：新旧Conversation身份、Notebook/排期/历史和显式B绑定保持；原生未绑定路径不变 | 生产只读调查不能替代上线后用户入站；本轮无生产修库/重绑 |
| V17 | Web `npm build → dist`；`package.json android:build → icons/signing → Tauri release → Gradle bundleSecretaryFrontend:69–82`；APK `assets/secretary`按文件清单读 | E10独立读取APK验证签名退出0、version0.1.3/code1003/min26/arm64非debug；旧0.1.2证书相同；APK439个资源与最终dist清单逐SHA一致、secretary-files精确一致；无私钥/env/DB文件名 | E10独立`apk-integrity.json`；E06 dist/build日志；原证书比对文件 | 符合：统一最终资源、递增版本及同签名安装候选成立，不以push代构建 | 没有真实手机覆盖安装/登录草稿保留实测；构建成功不等于V11/V13实际呈现验收 |
| V18 | 本轮后端提交20文件与Web107文件逐范围静态审阅；旧Kimi调查未列修改/执行入口 | 差异只针对标题、提交/Heartbeat展示、微信身份、Timeline及Android；本审查只读源码/现有证据与本地APK；未调用Provider/生产写入 | 双仓候选diff；E12；本报告审查记录 | 符合：没有重开已关闭Kimi实验，不改生产旧历史/排期/root | 禁止事项核验限本轮仓库/已提供证据与审查者动作，不推断未知外部活动 |
| V19 | 本轮已有分包handoff、最终集成源码/测试/本报告；根规则显示边界 | 每包代码路径亲审而非照抄自评；E12核dirty保留；审查只用本地静态图，没有桌面/外部浏览器/可见页/模拟器或手机控制，未尝试绕过已知IAB禁用；真实与受控证据逐项分开 | E01–E12；完整本报告 | 符合：协作、保护、证据诚实边界满足；真实环境缺口显式保留为门禁不通过 | 不将“不能验”改成不适用或默认用户豁免 |
| V20 | 本地双仓候选、dist/APK及已有定向检查；服务端原owner接口未替换；无新增执行器、权限门禁或生产部署 | 改动限定原有接缝，旧API仅可选字段/新增只读方法，源消息不改，Profile拒错有效；受控测试和只读查证未发微信/重启/部署，交付定位准备上线 | E02、E07、E10–E12；源码差异 | 符合：已完成本地可审候选和构建权限内工作；不冒称已上线或全验收 | 整轮“全部测好”仍被V11/V13证据缺口阻断 |

### 2026-10-21 当前候选全轮复审矩阵（RV01–RV32）

以下每行的上游规格位置、解释与适用条件来自第2节独立判据；RE证据具体版本／边界在第4节。判据未因旧报告或当前代码调整。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| RV01 | `agent/title_generator.py generate_title → auxiliary_client.py:7529 _prepare_aux_request → :6741 _build_call_kwargs → auxiliary_reasoning_floor.py:33 uses_private_reasoning_config → _relay_sync_completion`；同Provider重试:3791与fallback:4033–4089均传实际client | 按第2节R01判据亲读三类正式请求与同步/异步客户端；10个真实SDK/受控HTTP分支及单次真实Kimi k3-256k标题均有效；私有reasoning=false，2.49秒，无失败 | RE01 | 符合：实际已解析Messages adapter才接私有参数，Chat SDK不泄漏；原生模型／Provider／推理和fallback保持 | 真实Kimi仅代表Chat；故障与Messages分支为隔离SDK；无生产会话上线声明 |
| RV02 | Web `controller.ts:1504 send/executeSend → submitNative:1714`携UUID；backend `methods_prompt.py:661,702`原生锁／metadata → native writer；`methods_submit_idle.py:174–227`真实row回执 → event/ACK | 亲读ID只进display_metadata；重复ID在原生admission锁内拒绝；native loop、inline失败后batch及compute真实frame consumer均保存ID；Provider入参无ID | RE02,RE03 | 符合：精确受理关联使用真实原生用户行而非第二账本；省略ID兼容 | compute真实入口在本进程执行，不证明OS pipe／服务重启 |
| RV03 | `methods_submit_idle.py:70–99,254–267`目标Profile `_session_db`＋同Conversation binding只读SQL；`controller.ts:1758–1782 readSubmission` | 相同正文不同ID、其它Conversation、异Profile同物理ID均unknown；compression tip仍可核已受理；退休行证明历史但不改active；重开实际DB连接 | RE02,RE03 | 符合：owner／精确ID约束明确；状态查询不写数据，前端不直接插回历史回执 | DB reopen是新连接，不是完整服务进程重启；没有借该证据宣称后者 |
| RV04 | `controller.ts:1648 failPrompt → checkSubmission/readSubmission → acceptPrompt`；`select:796`恢复unknown；`reconcileEventView:1256`观察实际commit | 丢ACK后用只读accepted收敛；unknown保留检查且不重发；admitted后存储失败／晚错误不变发送失败；当前正式Controller已额外亲读 | RE02,RE03 | 符合：恢复来自受理事实，不按文本或running猜成功；确认后强制新历史读 | 未承诺Controller整体销毁后的unknown事务持久恢复，本轮契约未要求第二事务数据库 |
| RV05 | `controller.ts:875 acceptedDraft(localOnly) → acceptPrompt:1595 → retireAcceptedTransaction:1670`，tx.key／originRoute／originEdit固定原owner | 晚ACK失败、事件抢先、之后新Send的unknown提示、后来草稿、lost rewind ACK临时结果等5例；原生已受理只消费捕获草稿一次 | RE02,RE03 | 符合：tx.admitted与事务对象身份使旧ACK不清后来草稿／新事务；导航不改归属 | 测试覆盖正式Controller，API依赖受控；不冒称手机后台现场复现 |
| RV06 | `prompt_turn.py:913–934`装卸observer → `agent/turn_context.py:1024–1048`实际持久后回调 → `heartbeat_presentation.py:25–92` → native `_emit`／replay → Web `reconcileEventView:1256` | 正常native loop在Provider gate未释放时已有唯一真实row/UID原文；持久batch失败／退休行不造卡；本次修补异常按runtime＋stored Session＋row＋UID查既有replay；False不盲重发 | RE02,RE03,RE04 | 符合：旧F03修补已独立闭合；入环前失败可由后续同持久回调补一次，入环后异常／False保持一次；未把尝试当完成 | RE04注入真实native replay冻结接缝，Provider受控；没有声称新增主动重试调度器；浏览器即时呈现证据另记 |
| RV07 | Web `projection.ts:334–346 projectBody → App.tsx:306–334`；`tokens.css:40–42`／`theme.css:240–247` | 实际组件测试检查折叠标题、心电图标、展开保留timestamp/Additional、无Reply/附件/外时间；assistant引用、普通提及、不完整包装、display伪包装均不分类 | RE03,RE05 | 符合：真实source role／UID／原文不变，展示仅去外包装；HEARTBEAT_OVER无新增行为；陶土色双主题接线明确 | 本审查亲读组件／CSS及有效组件证据；不是实际手机视觉验收 |
| RV08 | 原 `secretary/heartbeat.py`、UI runtime恢复入口未改；本轮仅`prompt_turn`追加展示observer，finally恢复prior | 以07 §8.15模板／路由判据审全diff；未改全局noting分支、timestamp、Additional、工具／模型／Profile路由与渠道发送；observer失败只debug不阻provider | RE02,RE04,RE09 | 符合：即时展示沿已存在的Main及原生持久路径，无独立Heartbeat Agent或微信入站旁路 | 按索引只审本轮影响及保留契约，不重新声明完整旧Heartbeat产品验收 |
| RV09 | 现有Conversation Heartbeat owner／claim表及宿主扫描未改；新增observer核session／agent／token／closing／finalized | 核本轮diff无Heartbeat定义、pause/clear、scheduler、claim/refund或恢复owner修改；同对象finally恢复，无跨Turn闭包累积；失败分支不修改排期 | RE02,RE04,RE09 | 符合：本轮展示修改未改变独立owner、合法压缩、并发／退款和原生关闭分支；未把全局调度器替换进来 | 本轮是故障修复兼容复核；没有把未改功能扩为本轮新实现或据此宣称全调度重验 |
| RV10 | Web `Controller.acceptHistoryDetails:216 → commitHistoryView:1028 → reconcileLiveHistory`；`projection.ts:818–835 retainLiveAnchors → projectTimelineNodes:848–902` | 真实expected row引用／row ID／UID／role匹配才原位补齐；详情取消旧owner请求；真实512帧＋200 cards旧版737字符挂尾反例，候选回真实UID，idle select覆盖 | RE05 | 符合：真实持久位置优先旧complete尾锚；退休前驱仅把合法位置传同Turn后缀，详情不推全局尾、不重挂早期Thinking | 真实材料为离线只读回放，不是在线浏览器用户现场 |
| RV11 | `projection.ts:174–277 combineToolCards`按occurrence；`:785–805`adoption；`:865–889`parent缺页时按result UID占位 | 并行独立卡、乱序start/complete、failed result、parent页外、parent后补、deferred/full均检查唯一卡与顺序；detailSources保留parent/result | RE05 | 符合：身份与真实原顺序在中间状态已稳定，不靠Turn终态纠正；未按正文／完成时间排序 | 机制及组件真实接线，未泛化为所有设备渲染性能证据 |
| RV12 | `chat-presentation.tsx:77–117 anchoredTop`同时检查dataset身份；`:139–255`place／placedTop／ResizeObserver；App真实Timeline接线 | 同UID换DOM、React复用到其它消息、连续8次resize＋scroll、prepend及历史更新测试；identity失配回退原top，自己放置的scroll被过滤 | RE05 | 符合：DOM仍连接不足以抢占锚点，程序重排不冒充用户请求，不会追随被复用节点跳顶 | jsdom几何受控；真实浏览器的更多时序由主会话补证，未把不合wire夹具当产品反例 |
| RV13 | `App.tsx:493–502`仅同scope acceptedSend恢复；`useTimelineReading`手动输入／20秒timer／prepend；滚动状态仅内存 | 主动回底立即跟随；手动上滚暂停；程序scroll不延长hold；20秒idle到期后后续背景Turn不回底；active增长和分页锚定保持 | RE05 | 符合：没有监听所有Turn启动强制回底，Heartbeat沿既有active／20秒规则；不新增滚动持久存储 | 未声称真设备惯性滚动全场景完成 |
| RV14 | `chat-presentation.tsx:147–164`following只取底边；`stableTimelineNodes:913–924`；`controller.ts:1241`与`render-store.ts`合帧 | 实际200卡组件following初始化与增长均零历史卡getBoundingClientRect，真正上滚仍采锚；control/terminal立即flush并取消旧RAF | RE05,RE06 | 符合：修正可归因的每帧O(history)布局读取；原生事件逐条处理，不改文本／顺序／身份、不增持久镜像 | 没有设备FPS／低端CPU提升测量，报告不捏造该结果 |
| RV15 | `SessionActivity.read → AndroidTurns.observe/baseline/complete → android-turns-proof.ts terminalReceipt/readCompletedReply` | 现有active_list＋sessions.changed／gateway.ready全局观察；正常终态proof及最终真实两行详情、连续epoch／序号／UID才触发；不批量resume/activate、不加WS/轮询 | RE07 | 符合：Active→Idle只是核验触发，截断／缺失／不可靠持久证据放弃通知；真实末条回复来源明确 | 隔离API及Robolectric机制；实际设备通知结果由RV17保留缺口 |
| RV16 | `AndroidTurns`Profile+stored owner、sent去重／deadline／invalidate；`MainActivity.receivePacket`＋`CompletionLedger`前台抑制；`AndroidRunCoordinator`active周期 | 查看B时A完成、电脑发起已观察、跨Profile同ID、并发、前台抑制、断线／epoch、重复／迟到／超时和最后解保活均受控覆盖；固定标题／真实正文去Markdown截断 | RE07 | 符合：未补发旧通知，不拿sidebar preview或Thinking作正文，系统冻结不改变云端Turn | 不保证系统回收后的通知，不冒称实际厂商设备或真实模型全场景 |
| RV17 | `HermesNotifications.kt:18–76 completionChannel`新hermes-completion-v2，HIGH＋默认音；旧user importance／null/custom声继承；complete:78–91 | Robolectric SDK28/29/35真实Android channel对象覆盖新装／默认旧通道升级／主动静音／关闭／自定义声／已存在v2不覆盖；最终APK字节有效 | RE07,RE08 | 证据不足：指定迁移机制符合，但用户实际响铃＋横幅故障无真实设备观察，旧F02未关闭 | API26–28不能完整识别用户自选；DND／音量／厂商策略及覆盖升级真实呈现不能由shadow证明 |
| RV18 | `AndroidBridgeState.kt AndroidBridgeTrust/NavigationMailbox`；MainActivity主frame受信消息；HermesNotifications权限／clickIntent；前台服务生命周期 | 主frame＋HTTPS exact origin、前后台、拒权、冷启动mailbox保存、正确Profile/Session/Message及资源释放已有隔离覆盖；源码不向普通网页／第三方开放bridge | RE07 | 符合：本轮通道迁移未放宽信任／权限／owner边界，拒权不阻聊天、目标跨reload保留 | 仅机制符合；设备点击／登录完整体验仍须真实Validation，不由组件替代 |
| RV19 | `AndroidViewport.kt:43–65 calculate/from/configure → MainActivity.kt:97–117 → PackagedWebViewClient.kt:80–98,134–146`只替APK文档meta | 360dp手机计算380／scale .94736842；横屏沿短边倍率、宽屏／平板不反放大；原生useWideViewPort／overview配置及source hashes匹配；无前端整页断点scale | RE08 | 证据不足：壳机制符合，06:191明确要求真实WebView window.innerWidth与等比；目前没有Chromium／实际窗口取证，旧F01未关闭 | Robolectric WebView shadow、geometry-cases算式、普通浏览器viewport均不能证明真实APK WebView |
| RV20 | `MainActivity.kt:141–162`设备实时Insets／IME physical padding，IME期间不重算viewport；`AndroidViewport.script`转换CSS；`theme.css:128`APK56px/4px | 原生Insets及键盘测试、源代码只给packaged dataset设置safe-top，普通浏览器样式不变；没有把24px写死 | RE07,RE08 | 证据不足：几何和接线符合，但Insets／IME避让、缩放不变与触控命中仍缺实际WebView观察；与RV19合属F01 | 需要合法设备真实window/visualViewport／Insets／IME结果，不能用native算法值替代 |
| RV21 | `ForegroundRefresh.kt`watchdog；`MainActivity`生命周期及ActivityResult；`android-health.ts/client.ts`现有health | 34例原生生命周期覆盖首次不重复刷新、后台/解锁回前台立即重载重置、10/15/20/30封顶循环、WS connected停止、慢历史健康、外部认证与附件不打断、路由／mailbox保持 | RE07,RE08 | 符合：视口改动未改变既有恢复owner与生命周期保护，第三方页恢复原viewport配置 | Robolectric恢复机制证据，非真实Android弱网／冻JS验收；按本轮影响复核既有契约 |
| RV22 | `android-icons.mjs:14–41`原logo居中56dp／108dp透明前景＋#232120深背景；五dpi PNG及adaptive XML；APK资源 | 30资源／source SHA当前一致；真实像素主体54–54.25dp、66dp圆安全区；审查者亲看实际图层圆／圆角／方圆mask，主体完整可辨、无白边；APK存在同产物 | RE08 | 符合：不是只看输入logo，实际生成图层和普通mask均检查；无logo重设计 | 静态实际mask，未声称vivo launcher真实设备视觉验收 |
| RV23 | `ConversationBindingControl._bind:108–124 → TurnRunner._build_fresh_agent:1128–1149 → agent_session_key:20–35 → _init_session_state/initialize_conversation_identity` | 同Store lock在owner Profile DB核Session ref＝绑定ref，传目标原session_key或None；真实control A→B＋native身份initializer；旧错误构造负对照aliases conflict，新接缝成功 | RE09 | 符合：可变入口key不认领目标declared alias；不同source同key旧alias共存，真正冲突仍拒绝 | 整体AIAgent构造以真实native初始化替代，不证明生产微信／真实模型链路 |
| RV24 | 上述接线＋既有`allows_bound_target/restore_binding`、显式bind驱逐缓存／clear scope及晚回流owner检查 | 7文件111通过含绑定不变量：A派发后B绑定，A晚结果不回绑／不注入B；新目标真实Notebook／排期，前后全Secretary表＋sessions/messages相等；compression沿ref，branch拒错／不继承 | RE09 | 符合：不迁移／合并／清理旧alias、原文或派生状态；只显式操作变目标，未绑定保持原生 | 生产只读报告只用于定位数据一致性，不代替实际入站或授权生产修改 |
| RV25 | `agent_session_key`经`store._db_for_key`定位；`_build_fresh_agent`其余source／user/chat/thread参数保持；Gateway adapter投递路径未改 | 异Profile ref绑定失败／伪造绑定初始化拒绝；无新增微信发送接线；ctx.session_key仍是入口，agent内部key使用目标原生身份；Web/Heartbeat没有自动转微信改动 | RE09 | 符合：真实owner隔离与adapter收发身份保持，未以改source/session_key伪装绑定 | 不实际生产重绑／发送；上线后用户自然入站仍需明确部署授权与观察 |
| RV26 | Web npm build → dist；android:build → icons/signing → Tauri → Gradle bundleSecretaryFrontend → APK assets/secretary | 当前独立ZIP SHA重算：439最终dist＝冻结manifest＝APK439文件；secretary-files集合一致；0.1.3/1003、签名证书与0.1.2一致，非debug arm64 SDK26+；APK SHA 40efadef…4a9208 | RE06,RE08 | 符合：本地可审候选内置同一最终dist，版本递增、签名一致；资源元数据曾不匹配已停止并恢复原字节后逐SHA确认 | 技术构建就绪不等于所有修复已真实验收；未实际手机覆盖安装，不用候选构建掩盖F01/F02 |
| RV27 | 当前双仓候选＋本报告门禁；有效定向测试／quality及构建日志 | 检查版本、测试底座、受控与真实接口范围逐项区分；对设备证据仍记不足；保留5个基线同失败，不以1025项通过率代完成定义 | RE01–RE10 | 符合（完成声明约束）：当前如实判未完成／门禁不通过，没有把准备候选包说成全部测好或可以直接上线 | 用户整体目标尚未达成的具体阻断由RV17/19/20记录；本行不把这些缺口重复计为独立产品缺陷 |
| RV28 | 本轮backend相对冻结20文件、Web当前提交范围，旧Kimi历史／排期／root无对应修改 | 差异核只涉及标题辅助、提交/Heartbeat展示、微信初始化、Timeline及Android；本审查无Provider调用、生产写或旧实验动作 | RE01–RE10 | 符合：未重开已放弃旧Kimi行为调查，真实标题probe是独立虚构新输入，不属于旧会话实验 | 禁止事项判定限当前仓库／提供证据与审查者行为，不猜测外部未知活动 |
| RV29 | AGENTS显示／凭据边界；实现分包handoff、主审记录、当前Git状态；APK与ignore | 分包及主会话亲审有记录；dirty只为轮次／运维及原有文档，审查只改报告与ignored；APK ZIP无.env／key／签名私钥等名称；实测级别分清 | RE08,RE09,RE10 | 符合：没有覆盖他人产品修改，没有将私密原回放或签名原件入Git；本审查无UI显示变化／外部浏览器／设备控制 | ZIP文件名审查不等任意内容泄漏检测；结合manifest所有文件均是正式dist，本报告不复制私信 |
| RV30 | 本轮本地修复／检查／commit／构建；原生Profile／绑定／排期配置接口未改为自动操作 | 现有证据与本审查均无生产测试发送／重绑／配置／重启／部署；公开交付定位候选准备，未扩大到上线 | RE08–RE10 | 符合：授权范围与生产边界保持，不把push或构建当部署／验收 | 后续部署和真实微信入站需由主会话按明确授权处理 |
| RV31 | 06薄客户端／增量边界对全diff；新可选ID＋新增只读status契约及generated TS/OpenRPC；所有事实沿DB／native event | 无持久事实镜像／新执行器／独立调度／WS；字段可选，legacy无ID仍原生；错误4003/4000/4031和unknown有明确测试；source UID/row/content不改 | RE02,RE03,RE07,RE09,RE10 | 符合：新增最小接缝的owner、输入、持久边界、admission锁与错误均可追踪，原生默认行为未被改写 | 既有contracts test的review.summary孤立声明失败与本改动无关，基线同失败保留 |
| RV32 | `projectBody failed_turn`、`projectTimelineNodes`临时锚、App真实组件与design CSS；现有Pin/Profile控件及approval入口 | 本轮改动没有替换现有主题／Pin／Profile图标／审批choices；完整66文件套件含真实组件；failed_turn仅明确display_kind，slash临时输出保持；两类卡宽度接线未改 | RE05,RE06 | 符合：修复顺序／滚动没有把中断全部正文卡片化或合成终态卡；现有并行设计保持 | 按本轮影响范围审旧契约，没有把所有既有产品功能另行验收声明通过 |

### 稳定v2界面补证后的当前矩阵更正

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| RV10／原V06 | 真实Controller.hydrateDetails → HistoryDetails GET row41 → acceptHistoryDetails → reconcileLiveHistory退休同UID live → `App.tsx:94–106,234–247,324,916–935`改挂HistoricalThinking | 稳定v2全新goto排除HMR；已完成Thinking手动展开且内容可见，再展开工具引发1次真实fixture GET；前后同scope/UID／active=false、请求数1不重置；补齐后同thinking锚aria=false且正文从DOM消失，tool仍true；顺序始终正确 | RE11；第6节稳定v2补充发现 | **违规**：仅详情facet接管却丢失同身份已完成Thinking手动选择，06:291原位替换、06:255手动展开及06:287内容连续的必要条件未满足；F04未关闭 | 真实产品组件／Controller详情接线、受控本地数据；非完整App/select，非真设备；不把顺序正确的一部分结论撤销 |
| RV12–RV13／原V09 | 同版实际Timeline/useTimelineReading，真实上滚→8次自然reflow＋增量 | scrollTop5696→6220；archive-27和offset=-27.44完全不变；reflows0→8、无fixture网络请求；真实DOM／ResizeObserver，无stub scrollTop | RE11 browser-reading-before/after.json／browser-reading.png | 符合：补强原组件几何证据；程序补偿保持实际阅读对象／偏移，没有跳顶 | 当时reading场景为legacy未绑定推理；该输入足以审reading hook，对native身份恢复／投影顺序不作证明；不推广为完整App或手机性能 |


### 2026-10-21 第三次独立全轮当前矩阵

本矩阵以第2节FV判据为唯一产品判断起点；FE证据在第4节定位。全部源码为上述当前候选；同版未变证据经过哈希／diff核对后复用，未再次跑大型套件。每行来源与适用条件从FV原件继承，并给出实现、方法、结果及观察边界。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| FV01 | `agent/title_generator.py:generate_title → auxiliary_client._prepare_aux_request → _build_call_kwargs:6741 → relay`；同Provider retry:3791／fallback:4033–4089均传实际client；`auxiliary_reasoning_floor.py:33` | 亲读三条构建路径：只有实际Messages适配器收私有reasoning；OpenAI SDK保留公开原生参数；真实generate_title单次Kimi请求2.49秒成功，private=false。10 SDK路径及最终18相关用例支持兼容性。 | FE01 | **符合**；消除原参数错误且不改路由／推理owner。 | 真实代表Provider有效；未发新请求，非上线标题UI端到端。 |
| FV02 | Web `Controller.send:1530／nativePrompt:1706` UUID → `prompt.submit_idle` ContextVar → `methods_prompt:577/702`原writer → DB metadata；`methods_submit_idle:69/253`状态只读查询 | 亲读native history_lock内重用拒绝、目标Profile DB、Conversation binding SQL；10项真实DB/native loop覆盖同文异ID、跨Conversation／Profile、压缩tip、退休行、DB重开；模型payload无ID。 | FE02 | **符合**；真实持久用户行是唯一受理依据，optional字段不进模型。 | Provider受控；DB重开不等于OS重启，worker为真实入口在本进程执行。 |
| FV03 | `Controller.failPrompt:1655 → checkSubmission/readSubmission:1752 → ensureBinding(owner) → acceptPrompt:1597 → acceptedDraft:878 → retireAcceptedTransaction:1685`；`observeSubmissionCommit:1775` | 亲读admitted在await前成立、事务对象退休、draft版本与attachment ID消费；unknown只查不发；查询accepted不插回回执行；事件先到／晚拒绝／较新unknown通知／rewind临时项有5新增与4既有覆盖。 | FE02、FE03 | **符合**；无按文本／running推受理，无盲重发，晚ACK不丢后来草稿。 | 事务只在Controller内存；整页重建后从权威历史恢复，不声明持久发送账本。 |
| FV04 | `prompt_turn.py:916–938`叠加并finally恢复observer → `heartbeat_presentation.user_observer:24`核DB active user／row／UID／exact bytes → 原生`server._emit → output_identity._native_write → event_replay._stamp_event`；Web `Controller.reconcileEventView:1256 → adoptCommittedUser:1021` | 亲读先入环后transport，修补在正常emit后published，异常查既有replay且限定完整身份；7项真实native入口覆盖Provider前可见、重复、未落库、退休、pre-ring/False/post-ring；F04后浏览器19帧第5帧重复Heartbeat保持单卡且active。 | FE02、FE04、FE06 | **符合**；F03已独立闭合，未把尝试发布当完成，没有第二事件账本或补发Prompt。 | 受控Provider及浏览器虚构wire；不冒充真实Scheduler到设备验收。 |
| FV05 | `projection.ts:344`完整user wrapper分类 → `App.tsx:309–337`独立heartbeat卡 → design既有Disclosure／Heartbeat样式 | 亲读source role和原文不改、固定标题／默认折叠／保留内部timestamp、排除用户动作；分类与正式组件测试、实际中途卡DOM／截图支持。 | FE03、FE06 | **符合**；提及／assistant引用／无包装旧模板不猜，HEARTBEAT_OVER无新增语义。 | 浏览器呈现属真实DOM、输入虚构；并非实际tick／模型样本。 |
| FV06 | `Controller.acceptHistoryDetails:216 → reconcileLiveView:1031 → reconcileLiveHistory:806/retainLiveAnchors → projectTimelineNodes:864/combineToolCards:268 → TimelineMessages:117 → ThinkingExpansionOwner/App.tsx:141/237/920` | 亲读真实持久位置胜过旧tail anchor、同Turn后缀锚及分页外result唯一卡；F04内存owner按scope＋真实UID/row移交，真正running完成仍折叠；11实际Controller详情用例、2性能用例、stable browser同UID Loading前后true、唯一Thinking/tool仍在后来user之前。旧版失败对照与新通过均保留。 | FE05、FE06 | **符合**；旧R04–R06顺序与原位详情成立；F04手动展开丢失在bf279b2关闭，未以全展开或留重复live卡规避。 | 多phase／未知身份不猜移交；scope退出清空；A→B→A浏览器为隔离scope切换，完整select由正式Controller测试补足。 |
| FV07 | `useTimelineReading` capture/anchoredTop:104、place:140、reconcile:157、onScroll:233及20秒输入owner；`Chat`只监听acceptedSend回底 | 亲读DOM身份重新核对和placedTop过滤，following时无全卡扫描；55项及144相关集覆盖身份复用、8重排、20秒active／idle；F04后真实wheel上滚，8次真实增高＋stream后archive-26及-91.48px偏移不变。 | FE05、FE06 | **符合**；没有重排跳顶或Heartbeat新增强制回底，保留用户滚动所有权。 | 几何来自真实浏览器DOM，无geometry／ResizeObserver桩；不证明实际手机触控／WebView。 |
| FV08 | `RenderStore.publish/flush`合并纯增量及身份sidecar，控制终态立即flush；`chat-presentation.tsx:157`跟随底部不量前史；`thinking-expansion.tsx:32–51`只在identity/phase变化广播context | 亲读非事实异步化、终态取消frame；80静态卡memo负对照先红后绿，真正phase变化会通知；最终68文件1038通过/1跳过；真实19帧DOM无结束后补序。 | FE03、FE05、FE06 | **符合**；已修具体布局与无效重渲染开销，无渲染限速积压或持久镜像。 | 没有声称真设备FPS改善；测试计数不能当帧率。 |
| FV09 | `HermesNotifications.kt:18/45–75`新hermes-completion-v2、HIGH、默认系统音与旧通道可识别设置沿用；`complete:78`权限拒绝静默 | 亲读新ID、API29 hasUserSetImportance、低于DEFAULT／null sound及已有v2保留；SDK28/29/35 Robolectric和真实APK DEX证明机制进入包。 | FE07、FE08 | **证据不足**；机制符合，但冻结R09明确要求的覆盖升级后实际响铃／横幅尚无设备结果，F02继续阻断。 | 无获授权可用Android实际UI入口；API26–28主动设置识别不完整，不冒充系统呈现保证。 |
| FV10 | 既有`SessionActivity.read → AndroidTurns.observe/complete → session.events.since → terminalReceipt/readCompletedReply → trusted main-frame bridge → CompletionLedger/HermesNotifications → NotificationTarget` | 亲读不新增poll／resume／WS，正常完成持久proof与最终行、连续epoch、前台消费去重、owner跨Profile、导航Mailbox；前端67相关／原生70重叠集及最终Web suite覆盖失败、取消、断线、重复及并发。 | FE03、FE07 | **符合**；本轮通道改动未扩大观察／权限／发送范围，完成不靠preview或active→idle猜。 | 保留机制审查；实际后台保活／通知点击／系统回收运行归入F02真实设备缺口，不称端到端通过。 |
| FV11 | `MainActivity.kt:onWebViewCreate/applyInsets/onConfigurationChanged` → `AndroidViewport.calculate/document/script` → `PackagedWebViewClient.appDocument/onPageStarted`；IME只缩高度不改基准 | 亲读壳宽viewport meta、wide/overview、稳定WindowMetrics、statusPx换算及普通页面还原；7 native viewport及geometry覆盖窄／横／大屏，30源hash当前全同。 | FE07、FE08 | **证据不足**；机制提供380等比路径，但未实测真实WebView innerWidth／比例／Insets／键盘，F01继续阻断。 | Robolectric／公式／普通浏览器viewport不是实际WebView测量；不降为不适用。 |
| FV12 | `scripts/android-icons.mjs → android-icon-resources.mjs`五density前景／深底／legacy → adaptive XML → 最终APK22资源 | 亲读复用现logo，54dp主体maxRadius≤33安全区、深底满铺；独立目检实际生成mask图完整可辨无白边；最终APK20PNG逐可见RGBA匹配源，native/resources与已验版本无diff。 | FE07、FE08、FE09 | **符合**；资源及实际打包mask层面修掉过放／裁切，未改logo内容。 | mask是实际图层静态合成，未宣称vivo launcher安装后亲验。 |
| FV13 | `ConversationBindingControl`真实bind → `TurnRunner._build_fresh_agent:1128–1150 → conversation_binding.agent_session_key:20 → _init_session_state/initialize_conversation_identity` | 亲读同store lock内目标DB ref证明，再沿目标已有native key／None走compression身份；111相关项含六新增，旧参数负对照抛alias conflict，新构造成功；全Secretary/sessions/messages前后不变。 | FE10 | **符合**；入口不再认领目标出生alias，receiver/sender仍沿原TurnContext，真冲突仍拒绝。 | 构造native初始化真实，AIAgent其它部分受控；未部署后真实微信入站。 |
| FV14 | `conversation_binding.allows_bound_target/current_tip`及既有control/session_store/cache/late delegation归属，native key变更仅已绑定fresh构造 | 当前diff仅helper与构造参数，不写alias／历史；相关绑定invariant、control、prompt-cache/foundation/lineage覆盖压缩tip、branch、外Profile、未绑定、旧A晚回流；实际读取目标无需修库。 | FE10 | **符合**；不自动回绑、不合并旧Conversation资源；未绑定原生输入不变。 | 生产资料只读；后续用户正常入站属于部署后验收，不获授权主动测试。 |
| FV15 | 最终Web bf279b2 → `npm run build`439文件 → Tauri beforeBuild精确门禁 → signed release → 交付副本 | 审查者独算dist／APK439 SHA与inventory无差；新包5c9c…、32,048,497 bytes、aapt0.1.3/1003/min26/arm64、独立新旧apksigner均退出0同证书449b…；post-F04清单555528…精确对应新JS。 | FE08、FE09 | **符合**；最终候选已统一重构，旧40ef包仅历史，版本比0.1.2/1002递增。 | 签名兼容支持覆盖安装，不声称已在设备安装；整轮测试准备完成仍受F01/F02阻断。 |
| FV16 | 双仓当前diff／操作证据、生产只读ed94619、R14排除范围 | 亲审本轮改动无旧Conversation修复／调度／root改写，无本审查模型调用、消息、绑定、配置、重启、部署；标题真实probe仅虚构独立输入。 | FE01、FE09、FE11 | **符合**；本地托管与准备范围保持，不重开旧Kimi工具调查。 | 生产只读HEAD单行不单独证明所有运行状态；结论结合本轮diff与取证操作。 |
| FV17 | root规则、当前diff、native REST/WS seams与metadata可选字段／生成契约；ignored资料／APK inventory | 亲审未新增转录存储／独立Agent/WS、source不重写，schema optional与生成物同步；两仓product dirty空；APK无keystore/.env/signing.properties；独立检查无产品写或显示操作。 | FE02、FE03、FE08–FE11 | **符合**；薄客户端／增量兼容与保护边界保持，旧接口省略ID回归有效。 | 无UI越权；实际浏览器证据复用主会话hidden IAB，输入与能力限制明确，非设备代替。 |
| FV18 | 既有`secretary.heartbeat`／UI宿主→`_run_prompt_submit`原native loop；新增observer只读display | 亲读本轮没有更改模板／due/claim/owner/route，每Turnfinally恢复prior，真实native Heartbeat测试及cold-host10回归；未改全局关闭路径，不由HEARTBEAT_OVER新增过滤。 | FE02、FE04、FE11 | **符合**；本轮即时展示没有改变既有conversation_ref/Profile与tick执行归属。 | 仅本轮影响及保留契约回归，不扩成整套Scheduler/Notebook重验；较广旧失败如实保留。 |
| FV19 | `MainActivity.onPause/onStop/onResume → ForegroundRefresh`，JS`android-health`，PackagedWebViewClient可信page边界 | 亲读首次背景标记、回前台resetBackoff、10/15/20/30封顶、健康connected停止、init/JS独立兜底、resultReturn认证附件保护；native34恢复测试＋前端health及当前source30hash与旧已验相同。 | FE03、FE07、FE09 | **符合**；视口／F04打包改动未破坏既有恢复owner／基准；不清Cookie／draft／route。 | 仅未改恢复机制相关回归，真实WebView生命周期不是已验；不据此新增本轮功能要求。 |

## 4. 核心目标及验证方法审查

本次审查固定产品候选：后端 `9fabcdd73d817b55e6b819cb01681583d24a27ff`，Web `ad7e4842c230bf65bf8b1d5491ea1a169407ca6a`。冻结要求来自 `57ffa1c355b4eef9b73f6ab10d3fb6da42b43176`，不是候选实现的解释。未运行新的模型、生产写、部署或大型套件，复用已核验有效证据；审查者新做源码追踪、SHA校对、静态遮罩图目检、APK ZIP/签名/badging取证。

证据索引（相对后端或注明Web）：

| 证据 | 执行方、方法与版本 | 观察结果及能支持的结论 |
|---|---|---|
| E01 | 标题实现包；`.hermes-dev/aux-title-20261021/{review.md,final-targeted.log,final-regression.log,check-final.log}`；真实probe脚本/日志`.hermes-dev/mobile-title-live-probe.{py,json,log}` | 最终4文件18项通过（内含10个transport）；更早360项是重叠相关集，不能累加。真实probe直接调用正式generate_title/真实SDK，45秒上限、单请求、禁SDK重试、无生产Conversation写。结果标题成功、2.49秒、OpenAI/k3-256k、私有reasoning=false；脚本从stdin取凭据，没有输出凭据。 |
| E02 | 提交/Heartbeat实现复核包；`.hermes-dev/submission-review-20261021/{backend-final.log,review.md,backend-checks-final.log}` | 正式runner3文件45项通过，29.9秒；冻结10检查0 blocking/advisory。native loop/DB真实，Provider仅gate；worker真实frame consumer在本进程内执行。接口预期来自06:293/295，未通过模型文本猜事实。 |
| E03 | 同包Web `{web-tests-final.log,web-existing-recovery.log,web-typecheck-final.log}`；Web最终E06 | 新5项及既有4项精确恢复覆盖晚ACK/草稿/未知/退休行；typecheck通过；完整Web套件另涵盖timeline真实React组件及分类。 |
| E04 | Web `.archive/timeline-final-review-20261021/{handoff.md,targeted-tests.log,typecheck.log,reviewed-sha256.txt}`与`.archive/mobile-render-02/{handoff.md,final-targeted-tests.log,settled-and-reading-tests.log}` | 5文件144项通过、typecheck通过；实际Controller/history/details/reading hook/React组件接线，200卡几何负担、DOM身份复用、8次reflow、20秒边界均有反例。实现测试不是源码字符串断言。旧报告中“无关联ID故不能恢复”的临时结论已经被本轮E02/E03正式新增契约替换，不沿用旧状态。 |
| E05 | Web `.archive/timeline-replay-20261021/{replay.test.ts,result.log,nodes.json}`及`timeline-final-review-20261021/real-replay.log` | 真实只读512事件帧+200 cards离线回放，旧版本末端737字符Thinking异常可复现，候选不再挂尾；含idle select公共虚构等价。原私有fixture仍ignored，未复制进报告/Git。它证明投影反例，不证明真实浏览器现场。 |
| E06 | Web `.archive/mobile-render-02/{integrated-final-web-suite.log,final-dist-build.log,final-dist-manifest.json}` | Node24/Vitest4，66文件1025通过/1跳过，5.13秒；构建成功439文件，有既有bundle大chunk警告，不冒称零warning。清单SHA `ed540b2a693a8d53e9bd8fa3200f7f9d314523d8ad84f5f12f7a1f7d814424be`。 |
| E07 | Web `src-tauri/target/android-evidence/mobile-20261021/{native-final-v2.log,test-summary.json,frontend-tests.log,handoff.md}` | Robolectric SDK28/29/35原生63项、前端health/turns67项；实际channel/通知对象及MainActivity生命周期，Rust JNI被shadow。旧通道默认DEFAULT有默认音，v2默认HIGH，识别主动importance/静音的覆盖合理；API26–28不能识别所有用户选择属于已登记限制。 |
| E08 | Web `src/core/android-turns{,-proof}.ts`、`android-turns.test.ts`、`session-recovery.ts`及E07/E06 | 现有全局Activity读不新增查询API或WS；完成核验只用既有事件回放及精确最终row详情；前台/断线/epoch/跨Profile/并发/重复与native目标信任边界有隔离覆盖。没有把sidebar preview或active→idle当最终回复。 |
| E09 | Web `.archive/android-viewport-icon-20261021/{native-tests-final.log,native-summary.json,geometry-cases.json,icon-checks.json,source-hashes.json,mask-preview/1024x1024.png}` | 最终5 suites70项通过、0 fail/error/skip，13秒；与63项重叠不可相加。审查者核30个源/资源SHA全部一致；目检实际生成图层mask完整主体与深背景。计算与native API测试不能成为WebView DOM实测。 |
| E10 | Web `.archive/android-apk-final-20261021/{build-final.log,dist-check.json,signature-0.1.2.txt,dist-mismatch-root-cause.json}`；审查者`.hermes-dev/mobile-release-verification-20261021/{integrity.json,apk-integrity.json}` | 当前APK SHA `40efadefc358bd2604709e490451064762ad2d1c017cf48c9cfff239ab4a9208`，32,047,121 bytes，version0.1.3/1003，SDK26/target36/arm64-v8a。独立apksigner verify退出0、证书SHA `449b5f36662cb5ff2979004ce6472ca5c8ea5d992b334e2a4191eda6e7e53ad9`与0.1.2相同；APK内439文件和resources索引均与最终dist精确一致。构建因viewer `copiedAt`时间字段首次不一致而停止，后确认只有该元数据差异、恢复冻结原字节再完整SHA核验；没有忽略不匹配。 |
| E11 | `.hermes-dev/weixin-rebind-20261021/{report.md,tests-related.log,files.sha256,checks.log,production-readonly.txt}` | 7文件111项通过，63.9秒，冻结10检查0/0；3文件SHA与候选一致。真实绑定handler→constructor→native身份initializer；全Secretary表及messages/sessions不变，旧构造负对照冲突。生产只读资料支持新目标无需修库，不支持真实微信链路已验。 |
| E12 | `.hermes-dev/{mobile-integrated-check.log,mobile-integration-backend.log,mobile-baseline-tests.log}`；双仓git status/log；当前diff与ignore边界 | 最终冻结10检查0 blocking/advisory。较广6文件后端回归67通过/5失败，基线复现同5失败（孤立`review.summary`声明及4个instant source旧断言），故不称后端全绿、不修改旧断言凑绿。现有相同失败不证明本轮引入回归；observer finally恢复prior，无跨Turn闭包累积。 |

有效性核对：时间线12项文件hash中11项与独立复核时相同，`controller.ts`已随提交恢复最终收尾改变，因此不能只凭时间线旧hash证明最终Controller；本审查亲读其最终select/details/events/send/ACK/status接线，并复用之后最终66文件套件覆盖该变更。微信3项、Android30项全部相同；最终dist439项和APK内439项另由审查者直接计算，不只信主会话的成功叙述。所有计算证据写ignored目录，产品源码只读。

反证重点：若实现靠文本相同推受理，异ID/异Conversation测试会失败；若只改helper而未接原生writer/worker，持久行/Provider前事件及payload无ID检查会失败；若靠结束重渲染修正，展开前后/active failed tool/真实旧版对照会暴露；若仍信DOM连接或把程序scroll当用户意图，复用DOM与8次重排/20秒测试会失败；若只是同ID注册通知通道，真实Android API channel迁移测试会失败；若入口key继续当目标身份，真实native初始化负对照会失败。上述错误实现不是被测试镜像掩盖。

范围边界：本轮仅修故障，未新增完整Scheduler/Notebook验收任务；07 §8.15与08 §1.1中本轮未改能力按兼容约束核差异及相关回归，没有以本轮测试重新宣称整个旧产品通过。真实用户完整链路属于独立Validation；特别是V11/V13原文明确要求的真实测量缺口，已经足以使本Verification门禁不通过，不能用后续Validation名义从本报告剔除。

### 2026-10-21 当前复审的证据与方法

本次没有复跑大型套件，也没有新的模型／生产操作。亲读冻结原文后，逐项追当前正式入口、下游writer／SDK／native初始化／组件／原生生命周期，复核同版本证据；另外独立重算产品源码与产物哈希、读APK ZIP，亲看本地静态图层mask。当前产品版本与初审相比仅backend的Heartbeat发布异常2文件改动，Web及产物完全未变；其它同版本有效证据可复用。源码审查不是照抄实现者自评。

| 证据 | 执行方、版本、方法 | 观察、有效性与边界 |
|---|---|---|
| RE01 | 既有标题包`.hermes-dev/aux-title-20261021/{review.md,final-targeted.log,final-regression.log,check-final.log}`＋真实`.hermes-dev/mobile-title-live-probe.{py,json}`；当前aux文件自9fabcdd以来未改 | 10个SDK/MockTransport路径；最后18相关通过与更早360重叠不累加；单次正式generate_title真实Kimi成功、2.49秒、私有reasoning=false。probe禁SDK重试、stdin凭据、虚构输入且无生产状态写。未复发请求。 |
| RE02 | `.hermes-dev/submission-review-20261021/{backend-final.log,review.md,backend-checks-final.log}`；亲读当前native锁、writer／flush、查询与worker入口及测试 | 45通过、29.9秒，受控Provider但真实DB/native loop；跨Profile/Conversation、compression、retired、DB新连接和compute正式frame consumer均有直接断言。修补后17项覆盖提交10项；身份只在展示metadata，API payload模型消息无ID。 |
| RE03 | 同包`web-tests-final.log,web-existing-recovery.log,web-typecheck-final.log`；当前Controller与完整RE06 | 新5项＋既有4项精确提交恢复；普通user/Heartbeat真实commit即时adopt、UID去重；晚ACK／新草稿／rewind临时输出收尾可核。API依赖受控，非实际浏览器或生产现场。 |
| RE04 | 当前3b48cf0源码`heartbeat_presentation.py`＋`test_heartbeat_card_commit.py`；既有`emit-boundary-red.log,emit-boundary-final.log,emit-boundary-heartbeat-final.log,emit-boundary-checks.log` | 旧9fabcdd真实native emit/DB/ring红1失败2通过；新版本同三分支通过，17相关／最终7Heartbeat（重叠不相加），10检查0/0。入环前冻结异常、transport False、入环后异常分别观察ring和实际write调用；先有旧error不误匹配。审查亲追`_emit→write_frame→_native_write→_stamp_event`，状态从尝试前移到成功后，异常只查同源既有ring；observer finally恢复。日志最后7项只增加负对照的旧error，当前测试字节与提交一致。 |
| RE05 | Web`.archive/timeline-final-review-20261021/{handoff.md,targeted-tests.log,real-replay.log,reviewed-sha256.txt}`、`.archive/mobile-render-02/{handoff.md,final-targeted-tests.log,settled-and-reading-tests.log}`和`.archive/timeline-replay-20261021/{replay.test.ts,result.log,nodes.json}` | 5文件144项与此前相关集重叠；真实只读512帧／200 cards旧版反例与当前投影对照，材料ignored不复制私信。当前12源码/测试hash独立核11相同，controller因最终提交恢复收尾有变化；已亲读当前accept/details/select/event/send/ACK/status正式接线，并由后来的RE06覆盖当前版本，不直接把旧hash当最终Controller证明。 |
| RE06 | Web`.archive/mobile-render-02/{integrated-final-web-suite.log,final-dist-build.log,final-dist-manifest.json}` | 66文件1025通过／1跳过，5.13秒；Node24／Vitest4；439文件构建成功，有既有大chunk告警。当前Web HEAD及产品dirty检查一致；未重新累加或重复全量。 |
| RE07 | Web`src-tauri/target/android-evidence/mobile-20261021/{native-final-v2.log,test-summary.json,frontend-tests.log}`及当前AndroidTurns/bridge/refresh/notification/tests | Robolectric SDK28/29/35 63原生、67前端，其中最终通道11项；当前70原生包含这63项且多7 viewport，不累加133。Rust JNI／WebView为shadow，不能成为真Chromium、厂商通知或实机用户结果。接口测试主动缺失／截断／旧epoch反证，错误实现只看Idle或preview无法通过。 |
| RE08 | Web`.archive/android-viewport-icon-20261021/{native-tests-final.log,native-summary.json,geometry-cases.json,source-hashes.json,icon-checks.json,mask-preview/1024x1024.png}`与`.archive/android-apk-final-20261021/{build-final.log,dist-check.json,signature.txt,signature-0.1.2.txt,badging.txt}`；本审查独立`artifact-integrity.json` | 70原生0失败／错误／跳过；30 source/resource SHA全匹配。mask亲看完整主体、深背景；当前APK SHA `40efadefc358bd2604709e490451064762ad2d1c017cf48c9cfff239ab4a9208`／32047121 bytes，与初审已独立签名验证之字节相同，可复用签名证据；证书SHA `449b5f36662cb5ff2979004ce6472ca5c8ea5d992b334e2a4191eda6e7e53ad9`，与0.1.2一致。独立ZIP重算439资源＝当前dist＝冻结manifest，索引集合439一致，无所列私钥/env名称。构建首次copiedAt元数据不一致先停止后恢复原字节，未放过不一致。 |
| RE09 | `.hermes-dev/weixin-rebind-20261021/{report.md,tests-related.log,files.sha256,checks.log,production-readonly.txt}`；亲读current binding helper/control/constructor/native initializer测试 | 7文件111通过／63.9秒；10检查0/0；当前3源文件SHA全匹配。正式control→constructor→native身份初始化，表全行不变，旧参数直接失败负对照。真实生产只读现场仅证明无需修库，不证明微信入站验收；无生产发送／重绑。 |
| RE10 | `.hermes-dev/mobile-integrated-check.log`＋当前修补`emit-boundary-checks.log`；既有`mobile-integration-backend.log,mobile-baseline-tests.log`；当前双仓Git状态和本审查`integrity-preflight.json,source-audit.json,artifact-integrity.json` | 原集成10检查0 blocking/advisory＋修补2文件10检查0/0；6文件后端67通过5失败，冻结基线同5失败，涉及review.summary声明及4旧instant source断言，未修改或隐藏。产品源码与当前hash一致，报告及ignored之外无本审查改动。 |

反证与证据层级：精确提交的同文异ID／异owner、先事件后失败ACK能排除“猜成功”和“旧事务清新草稿”；native真实flush及worker入口能排除仅helper存在。Heartbeat故障对照在原生事件入环前后两侧，证明不能按bool返回／异常整体猜是否未发。Timeline真实旧版负对照及中间详情替换可排除结束后才纠正；阅读identity替换与八次resize/scroll、20秒边界可暴露DOM连接误认和程序滚动误认。通知tests主动缺失proof／截断／旧epoch，排除状态直接等同完成。微信负对照重现真实native alias冲突，表级恒等验证排除靠清理旧身份修“成功”。图标目检的是实际生成图层／mask，APK与dist逐字节；这些仍不能替代设备实际380/Insets/IME和响铃／横幅。

主会话提供的首轮浏览器诊断夹具缺api_request_id／stream_writer_token，不满足native wire绑定契约，因而没有被本审查用作产品违规反例或通过证据。产品代码未因该夹具改变。有效浏览器证据应另记其真实输入和观察范围；Android两类必要缺口不受该补证自动关闭。

### RE11：主会话稳定隐藏IAB补证的独立核验

证据位于Web`.archive/mobile-render-02/ui-probe/`。审查者亲读README、probe.tsx、产品SHA清单和browser-v2-idle-before/loading/after.json、browser-reading-before/after.json；产品组件直接导入当前ad7e484源码，JSX与CSS没有镜像，原位详情通过正式Controller／HistoryDetails真实fixture GET。隔离页不挂完整App、不连生产，scope切换为内存安装，因此不证明完整select／真实API服务／微信／真设备；输入审计和缺owner首版对照完整保留。reading证据是此前legacy流片段的真实DOM自然增高，只用于几何锚点，不将其当已绑定native输出恢复证明。

稳定v2 JSON前后fixtureRequests均1且scope/owner/active连续，主会话明确全新goto并待准备者停止编辑后执行，可排除初轮HMR重载；loading中Thinking正文真实可见，after同`thinking:uid:old-thinking` aria=false仅剩标题，tool仍aria=true。这支持F04，而同组domOrder同时支持旧挂尾／工具顺序修复已经生效。F04并非以失配v1或HMR初轮下结论；机制代码`HistoricalThinking useState(false)`与真实观察构成独立因果链。第6节记录完整规格解释及修补关闭条件。


### 2026-10-21 第三次整包复审的方法与证据

本次不采用实现者自评作为判据；全轮判据先落盘，随后亲读backend对冻结全部产品diff、Web本轮产品diff与F04当前实现、正式writer／source observer／emit/replay上下游、Controller send/details/select/commit与投影、scroll hook、Android bridge／通知／viewport／生命周期／资源／打包入口。没有只对旧F04复测，也没有复跑已有同版大套。独立新增取证限源码追踪、哈希、ZIP/inventory、aapt/apksigner及本地证据图目检；产品源码只读。

| 证据 | 执行方、版本、方法 | 观察结果与可信边界 |
|---|---|---|
| FE01 | `.hermes-dev/aux-title-20261021/{review.md,final-targeted.log,final-regression.log,check-final.log}`与`.hermes-dev/mobile-title-live-probe.{py,json}`；标题源码当前与已验相同 | 真实SDK/MockTransport正式3路径，10例和18定向与更早360重叠不累加。单请求实际Kimi generate_title成功2.49秒；脚本stdin凭据、禁SDK重试、虚构文本、不写生产Conversation。本次未再发请求。 |
| FE02 | `.hermes-dev/submission-review-20261021/{backend-final.log,backend-checks-final.log,review.md}`及当前10项submission测试原文 | 真实DB/native loop、45通过/29.9秒、冻结10检查0/0；worker真实frame consumer但进程内；DB新连接有opener断言，不包装成进程重启。ID只持久display metadata，实际模型payload无ID。 |
| FE03 | 同包`web-tests-final.log/web-existing-recovery.log`；Web`.archive/mobile-render-02/post-F04-full-web-suite.log` | 新5＋旧4恢复覆盖ACK竞态／草稿／unknown；最终68文件1038通过/1跳过，5.21秒，未相加旧1025；最终bf279b2，亲读当前实现确认相关断言未绕正式逻辑。 |
| FE04 | `.hermes-dev/submission-review-20261021/emit-boundary-{red,final,heartbeat-final,checks}.log`、当前`test_heartbeat_card_commit.py` | 旧9fabcdd pre-ring负对照1失败2通过；3b48cf0下真实_emit/write_frame/_stamp_event，pre-ring／transportFalse／post-ring异常及旧error干扰正确；17通过含提交10，与单独7重叠。没有将False等同未入环。 |
| FE05 | Web`.archive/timeline-final-review-20261021/{handoff.md,targeted-tests.log,real-replay.log,thinking-detail-red.log,thinking-detail-green.log,thinking-detail-related-final.log,thinking-render-red.log,thinking-render-green.log,thinking-render-typecheck.log}`及`.archive/timeline-replay-20261021` | 旧真实只读512帧/200cards能复现737字早期Thinking挂尾，新正式投影修正；F04正式Controller/details旧反例红、新11例绿；memo80静态卡旧Context广播红、新实现绿，真正phase仍广播。新性能5文件25项与详情6文件114项重叠，按最终1038口径。 |
| FE06 | Web`.archive/mobile-render-02/ui-probe/{README.md,browser-review.md,browser-F04-source-sha.json,browser-F04-loading.json,browser-F04-after.json,browser-F04-visible.png,browser-F04-reading-before.json,browser-F04-reading-after.json,browser-F04-stream-frames.json,fixture-audit.log,owner-investigation.json}` | 审查者独算5个产品SHA全匹配、亲看截图及原始DOM；正式Timeline/Controller详情/投影/scroll真实DOM，F04前失败与F04后同UID展开保留、8重排锚稳定、19帧与中途Heartbeat单卡。虚构合法输入；v1缺owner与开发HMR轮排除。不是完整App.select、真实后端或Android。 |
| FE07 | Web`.archive/android-viewport-icon-20261021/{native-summary.json,native-tests-final.log,geometry-cases.json,icon-checks.json,source-hashes.json,mask-preview/1024x1024.png}`及`src-tauri/target/android-evidence/mobile-20261021/{native-final-v2.log,frontend-tests.log}` | 原生70通过、5 suites、0失败/跳过；SDK28/29/35 Robolectric，JNI shadow。独立当前30源/资源SHA全匹配、亲读原生路径并目检mask。63旧native和67前端相关不可与70或1038累加；几何公式／native API测试无实际WebView或系统响铃结论。 |
| FE08 | Web`.archive/android-apk-post-F04-20261021/{handoff.md,delivery-receipt.json,verification.json,build.log,signature.txt,badging.txt,dist-check.json,copiedAt-reuse.json,source-provenance.json}`；Web`.archive/mobile-render-02/{post-F04-dist-build.log,post-F04-dist-manifest.json}` | 当前bf279b2/3b48cf0收据，439dist及439APK逐SHA，v0.1.3/1003，同0.1.2签名，20PNG逐像素匹配，22图标资源进入实际包，无签名私钥或.env。构建只有copiedAt元数据差异，核其它438及JSON其它字段后恢复本次冻结原字节；未忽略不匹配。 |
| FE09 | 本审查ignored `.hermes-dev/mobile-release-final-verification-20261021/{integrity.py,integrity.json,signature-new.txt,signature-old.txt}` | 独算浏览器产品5项及Android30项哈希全匹配；dist439精确匹配555528…清单，APK5c9c…内439与inventory无差，两仓候选HEAD准确/product dirty空；交付副本SHA同新包；aapt确认1003/0.1.3/min26/target36/arm64，独立apksigner两包退出0、证书同449b…。不重复运行构建／测试。 |
| FE10 | `.hermes-dev/weixin-rebind-20261021/{report.md,tests-related.log,files.sha256,checks.log,production-readonly.txt}`及当前正式构造／initializer与六新增用例 | 111项、63.9秒，冻结10检查0/0；旧构造真实alias conflict反例，新target无key／own-key／compression／branch／外Profile／真冲突；完整Secretary表及messages/sessions全行不变。真实入站未发，生产只读无需修库不等于已上线。 |
| FE11 | `.hermes-dev/{mobile-integrated-check.log,mobile-integration-backend.log,mobile-baseline-tests.log}`与`.hermes-dev/mobile-release-20261021/production-readonly-final.txt`、本轮diff和当前状态 | 冻结10检查0blocking/advisory。较广后端67通过/5失败，基线复现同5（review.summary catalog及4个instant旧断言），不冒称后端全绿；冷Heartbeat host10有效回归，observer finally不累积。生产只读HEAD仍ed94619，本轮未部署。 |

主动反证结论：精确ID的异正文／异owner、迟ACK与较新unknown事务、retired回执、native批写失败、发布入环前后、真实UID胜旧尾锚、parent页外result页内、DOM连接但身份变换、程序scroll、同UID详情接管／真正完成／多phase／scope退出、memo静态卡与identity计数变化都能分别暴露错误机制；测试没有靠源码字符串或镜像helper替代这些正式接线。原生设备缺口不因受控测试覆盖宽而放宽。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| F01 / P1 | V13；06:191；AndroidViewport/MainActivity/PackagedWebViewClient | 真实布局取决于Chromium meta interpretation、设备窗口、Insets、IME与旋转；现只有算法+Robolectric WebView shadow，无window.innerWidth/visualViewport/真实触控坐标 | 380原生逻辑视口与等比是明确完成条件，计算值不能代替实际结果；范围内证据不足 | 获授权且符合显示保护的实际WebView只读取证：竖屏innerWidth=380、比例、旋转/大屏不反向放大、IME不变scale且避让、真实顶部Insets；不能绕过当前环境限制 | 未关闭；环境限制，禁止伪作通过/不适用 |
| F02 / P1 | V11；06:201–203；HermesNotifications.kt | 当前APK已正确创建v2 HIGH+默认声并保留识别出的静音，Robolectric通过；无真实设备覆盖安装后的响铃/横幅与用户设置观察 | 用户原始故障是实际通知无响铃/横幅，系统/厂商设置影响结果；隔离对象不足以证明已解决 | 合规获授权的设备完成代表链路：旧正常默认升级有声/横幅、主动静音/关闭保持、前台抑制、点击归属；记录系统版本、通道设置和真实结果，不发生产测试消息 | 未关闭；环境限制 |
| F03 / P2 | V04；旧候选heartbeat_presentation.py:67–68 | 原候选在_emit前published=True；真实native turn/DB/emit/replay的freeze接缝一次pre-ring异常后，row已持久而ring/transport均0；再次调用两次仍0 | 把发布尝试当完成事实，后续同持久回调无法恢复；违背V04源消息及时展示及失败恢复边界 | 新候选3b48cf0将状态放到_emit之后，异常按真实replay对应row/UID判断；红1失败2通过，修补后17相关及7Heartbeat通过；须全新独立全范围复审核关闭 | 已修补待独立复审，不在本初审闭合 |
| O01 / 范围外既有 | V20兼容观察；后端旧contracts/instant source测试 | E12候选5失败，冻结基线同5失败；`review.summary`孤立声明、instant source旧native断言已存在 | 不作为本轮新违规；限制“所有后端测试全绿”声明 | 主会话登记保留原报告，不为本轮扩大修复或削弱门禁；后续独立任务处理 | 已识别，未在本轮改动 |
| O02 / 非阻断证据边界 | V06–V10/V14–V16 | Timeline机制、静态实际mask、微信native初始化有有效证据；真实手机/浏览器像素、vivo launcher、线上微信正常入站尚无新观察 | 不把静态/组件测试冒称实际用户验收；与F01/F02共同限制整轮完成声明 | 独立Validation按原用户入口检验；生产入站仅在明确部署授权后用户自然消息，不能审查者自行触发 | 交Validation/主会话，未伪造关闭 |

初步静态调查未直接确认发布异常缺陷；在报告交回前，主会话补交真实native emit入环前失败负对照，现将原候选V04改判违规（判据未变）。最终为17条符合、1条原候选违规、2条证据不足。后续候选3b48cf0有修补，不由本初审自行宣告独立复审通过。优先补齐F01/F02实际环境证据；在合规入口不可用时保留候选、如实交付受限状态。不得为补证擅自部署/重启/控制真机/开启可见浏览器或改变产品验收条件。

### 2026-10-21 当前复审发现与旧项关闭

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| F03复审关闭 | 原V04／当前RV06；heartbeat_presentation.py:10–92；backend3b48cf0 | 已将published提交放到正常emit后；异常查同runtime＋stored Session＋row／UID真实replay。入环前首次失败后重复持久回调只补1帧1ring；False／after-ring仍1帧1ring，旧error无干扰 | 旧版违规确有负对照，当前修补不新建publisher/ledger/调度，不弱化源身份或正常事件 | RE04旧红、新绿17／7、当前源码亲审和字节核查足以关闭原发布异常；Web和产物无变 | **已关闭于3b48cf0**；保留旧候选违规历史 |
| F01继续／P1 | 原V13／当前RV19、RV20；AndroidViewport/MainActivity/PackagedWebViewClient | 380与Insets／IME只有算法、真实Android API＋Robolectric shadow，无真实Chromium window.innerWidth/visualViewport、缩放、触控／键盘证据 | 冻结06:191明确要求实际WebView测量，指定壳机制不等真实结果；是范围内必要证据不足 | 获授权且符合显示保护的实际WebView：竖屏380、比例；横屏／大屏无反放大；IME不变scale并避让；实际Insets及命中坐标。无合法入口时保持未验 | **未关闭，阻断**；隐藏IAB普通浏览器不替代Android |
| F02继续／P1 | 原V11／当前RV17；HermesNotifications.kt | v2 HIGH／默认音及主动静音迁移机制正确，真实设备旧默认覆盖升级后是否实际有声／横幅尚无观察 | 用户原始通知故障受系统／厂商／设置影响，Robolectric对象不能证明已解决 | 合规设备代表场景：旧默认通道覆盖升级声音／横幅，主动静音／关闭保持，前台抑制和点击owner；记录系统／设置／真实结果，不发生产测试消息 | **未关闭，阻断** |
| O01保持范围外 | 原有contracts／instant source基线失败；RV31证据边界 | 同5失败在冻结基线和候选均存在；修补不涉及它们 | 不判本轮新违规，也不称后端全绿 | 保留原日志、后续另项处理，不为凑绿改断言／关闭检查 | 本轮不修，已保留限制 |
| O02保持证据边界 | 当前RV07、RV10–16、RV18、RV21–25 | 组件／native初始化／静态mask或离线回放证据有效；未由本审查实际操作浏览器／手机／生产微信 | 不把机制证明扩成真实用户验收；其中明确必要Android缺口已独立列F01/F02 | 浏览器有效入口可补本轮观察；真实用户完整路径仍由后续独立Validation执行；微信等生产入口按另行授权 | 不伪造关闭，不扩大权限 |

本次没有发现新的已证实实现违规；本次三条证据不足对应两个既有阻断事项，不以拆分条款增加独立缺陷数量。不要求用户改目标／降规格来适应现有环境；在合法设备入口不可用时保留实际未完成状态。

### 稳定v2补充整改项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| F04／P2 | RV10／原V06；06:255,287,291；App.tsx:234–247,324,916–935 | 同UID已完成Thinking已手动展开；展开相邻failed tool触发parent row41详情；live被正常退休，由新HistoricalThinking默认false接管，正文消失；active始终false、无新完成／折叠动作、顺序正确 | 详情facet替换丢失同身份当前用户选择，超出原位补齐；旧组件测试未断言live→history展开交接，错误实现可通过现有全套；范围内新增违规阻断 | 原授权内方案保持同scope/UID当前展开选择，仍保留新Thinking/running→完成真实折叠与默认历史折叠；组件＋Controller详情链路先红后绿，稳定浏览器重验；不持久化、不跨owner、无双卡 | 未关闭，待主会话提案／修补；不是新规格请求 |

当前统计更正为28符合／1违规／3不足；原20条17符合／1违规／2不足。前面同日“无新增实现违规”的段落属于收到稳定v2之前的时点，本追加明确替换其当前性而不删除历史。


### 2026-10-21 第三次整包复审：当前发现与关闭状态

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| F01（沿用） | FV11；原V13、RV19/RV20；AndroidViewport/MainActivity/PackagedWebViewClient | 壳机制已进入新APK，但尚无真实WebView innerWidth／比例／Insets／键盘测量；只有Robolectric及公式 | R10原文直接要求实际逻辑视口，适用且无豁免；阻断Verification与正式Validation前置 | 在获授权实际Android入口测380／等比、横竖／大屏、IME基准与避让及真实Insets；保持现行显示保护，不自行控制设备 | **未关闭／证据不足**。本次未改规格，不用普通浏览器替代。 |
| F02（沿用） | FV09；原V11、RV17；HermesNotifications | v2 HIGH／系统音／主动设置保留机制已验，新APK签名有效；未安装覆盖升级观察真实响铃横幅 | R09要求用户实际接收效果，Android系统呈现不能由notification对象断言证明；阻断门禁 | 获授权设备覆盖升级验证旧默认响铃＋横幅、主动静音／禁用、前台抑制／拒权；明确系统版本限制 | **未关闭／证据不足**。无可用获授权真实入口。 |
| F03（沿用） | FV04；原V04/RV06；heartbeat_presentation.py:81–90 | 旧9fabcdd在入环前置published；当前3b48cf0正常emit后置，异常按既有replay完整身份判是否实际发布 | 原违规不再存在，不能删历史失败；False及post-ring仍只一事件 | 真实native pre-ring／False／post-ring负对照及17相关、7最终证据FE04 | **本候选关闭**，独立亲审与已有同版证据有效。 |
| F04（沿用） | FV06；原V06/RV10；App.tsx:141/237/920及thinking-expansion.tsx | 旧ad7e484同UID已完成Thinking手动展开在tool详情接管时折叠；bf279b2内存scope/identity owner接管后保持，实际DOM与截图可见 | 原细节原位和手动交互连续性缺陷已修，running真正完成、未知身份、scope／多phase边界仍保持 | 正式Controller详情11项、旧版失败对照、同源实际DOM/browser-F04，FE05/FE06与源码5SHA一致 | **本候选关闭**，无降低判据，修补后dist/APK已重构。 |

无新增范围内实现违规。既有5个后端基线失败属于已记录范围外限制，继续交主会话保留，不修改断言／关检查换绿；本次未新增范围外事项。优先补F01/F02所需获授权真实入口及证据；在此前只能交付未完成验收的本地候选，不声明全部测好／正式上线。

## 6. 修复与独立复审

本报告为本轮首次独立Verification，非实现者自评；第2节先仅读冻结原文落盘，再读编码指导、代码及证据。无降低原判据、无新增规格、无退回补审历史。全部20条全范围已列矩阵；17条符合、2条证据不足、1条违规、0条不适用，门禁不通过。

候选9fabcdd/ad7e484并非因本报告新修复；它们纳入此前实现包已发现并关闭的正式缺口（标题SDK私有参数、精确受理身份、Heartbeat持久回调、微信目标身份、详情/历史位置及滚动identity），本审查逐包亲核路径和关闭证据，不把历史发现列成审查者新发现。

关键工程研讨：

- 原判据V04要求实际持久源→及时事件，不能把“准备发布”当“已经送达”。主会话提出核查`heartbeat_presentation.py`在`_emit`前设置`published`的异常语义；审查者沿`server.py:692`、`output_identity.py:98–143`与原生frame记录路径核对，`_emit=False`可能只是没有live transport，但帧已经进入ring，不能简单据False重发导致双事件。主会话随后补交真实_run_prompt_submit/DB/_emit/_stamp_event负对照：入环前冻结一次异常使旧版重复持久回调仍无事件（emit-boundary-red.log，1失败2通过）；False与after-ring异常原本各已有1条replay，因此不是重发依据。该反例证明原候选发布状态提前提交，V04按原判据改为违规。主会话提案保持原生publisher，仅在正常emit后置published；异常查既有replay的stored Session/row/UID，只有未入环才保留可再试；不新建重试调度器或第二账本。审查者认为提案满足原判据所需条件，实际关闭仍须新独立审查者。后续backend3b48cf0baeb3c49bb96849d24c6105bf6e39e6fc已提交上述2文件修补，emit-boundary-final.log为17相关通过，加入旧error干扰的emit-boundary-heartbeat-final.log为7通过，冻结10检查过。报告保留旧版本违规及新版本待审，未更改规格或迁就降低判据。
- 源码`prompt_turn.py:930–938`总在finally恢复原observer，否定“每Turn永久累加闭包”的初步反证假设，因此不列产品缺陷。此为静态反证关闭，有具体代码位置。
- 构建一致性曾因`file-viewer/flyfish-viewer-assets.json`的`copiedAt`唯一字段发生变化，主会话采用恢复冻结构建元数据原字节的工程收敛；审查者独立核最终dist与APK所有439个文件SHA完全一致，保留首轮停止与最终证据。没有降低“同一最终dist”判据或改产品规格。此项应在final-delivery构建说明简述。
- F01/F02没有工程修复提案能用现有隔离证据替代真实结果；保持未决环境证据缺口。没有要求用户重定产品语义，也没有把不可用环境当作默认豁免。

供主会话最终摘要：本地代码机制与统一签名候选已落实；最终APK与439文件dist一致；真实WebView/实际通知证据仍缺，Verification不通过，不能进入“全验收通过/可以直接上线”的完成声明。实质收敛仅是原生身份接缝、精确受理事实与源消息原位投影的工程落实，以及构建时间元数据的确定性校对；没有新增用户待追认产品决定。

版本/环境追加（报告交回前）：后端从9fabcdd推进到3b48cf0，仅Heartbeat发布异常2文件；Web ad7e484及APK/dist字节未变。主会话通知隐藏IAB已可创建，原“当前禁用”环境事实已解除，后续浏览器UI可补；本审查未进行任何浏览器UI操作，不继续沿用“现在无法打开隐藏IAB”的断言。Android真WebView/通知仍没有获授权真实入口，F01/F02不变。主会话已准备全新fork-none复审；本报告第2节独立判据和本次旧候选矩阵须保留，复审追加不得覆盖历史。

### 2026-10-21 全新独立全轮复审记录

先行判据原件：`.hermes-dev/mobile-release-reverification-20261021/criteria.md`，建立时只读取冻结Snapshot Index／requirements／06相关§0.4–0.5、§1、§2／08§1–1.1／07§8.15；随后才读取AGENTS、CLAUDE、README、RTK、旧报告、代码与证据。第2节原样追加原件；本次未改动判据语义或以实现降门槛。旧20条和原六节／表列／历史结论保留；当前第3节另列32条矩阵覆盖R01–R16全范围。

原20条当前覆盖映射（每个原条均有当前判定，无只看旧缺陷）：

| 原条款 | 对应本次独立条款 | 当前判定 | 说明 |
|---|---|---|---|
| V01 | RV01 | 符合 | 标题真实SDK／代表Provider |
| V02 | RV02 | 符合 | 原生writer与身份关联 |
| V03 | RV03–RV05 | 符合 | owner／unknown／ACK草稿及退休 |
| V04 | RV06–RV07 | 符合 | F03修补闭合；完整source卡片 |
| V05 | RV07–RV09 | 符合 | 模板／调度owner及边界保持 |
| V06 | RV10 | 符合 | 详情原位及后缀 |
| V07 | RV11 | 符合 | 并行工具／真实顺序 |
| V08 | RV10 | 符合 | idle旧Thinking位置 |
| V09 | RV12–RV13 | 符合 | identity锚／程序scroll／20秒 |
| V10 | RV14 | 符合 | 去无用每帧几何扫描 |
| V11 | RV17 | 证据不足 | F02实际通知缺口 |
| V12 | RV15–RV16、RV18 | 符合 | 通知既有资源／权限／owner |
| V13 | RV19–RV21 | 证据不足 | F01实际WebView／Insets／IME缺口；恢复保留机制符合 |
| V14 | RV22 | 符合 | 实际资源mask及产物 |
| V15 | RV23、RV25 | 符合 | 正式微信目标身份初始化 |
| V16 | RV24–RV25 | 符合 | 旧身份／历史／排期／晚回流隔离 |
| V17 | RV26 | 符合 | 签名、版本及439资源一致 |
| V18 | RV28 | 符合 | 旧Kimi排除范围 |
| V19 | RV29 | 符合 | 分包、保护与证据边界 |
| V20 | RV27、RV30–RV32 | 符合 | 授权、薄客户端／兼容与声明边界 |

F03关键研讨链完整保留在旧第6节：原判据要求真正持久源即时投影 → 旧版emit前published把尝试误作完成 → 主会话提出只在正常emit后提交、异常查原生replay区分前后边界 → 本复审先从冻结规格独立建立RV06后才读该方案 → 当前源码与真实native边界对照符合不变量，因此关闭原F03。没有改变规格，没有增加独立重试器／账本，没有为可用性越过原消息事实和显示限制。修补只影响展示observer，检查普通提交ID、既有原生Turn／Reminder prior observer、False/mute和关闭／finalized条件；finally恢复原observer，原生持久／provider流程不被展示异常阻断。RE04／RE02覆盖修补相关提交和Heartbeat失败路径，无需重新复跑全量。

当前版本独立判定：**32条＝29符合＋0违规＋3证据不足＋0不适用；按原20条＝18符合＋0违规＋2证据不足＋0不适用。** F03已关闭；F01／F02不变。既有5失败为范围外基线限制，无新增产品缺陷。**Verification仍不通过，正式Validation不能开始；**允许继续合法补证、独立筹备场景，不得把筹备当门禁已通过。未接到主会话因缺行／证据链不足退回本次报告；若后续补充当前同版有效证据，可在同一报告继续追加，保留本次时间点结论。

供主会话final-delivery主动摘要：本轮原生身份／精确受理／真实源位置与最终签名候选已具备可审机制；旧Heartbeat发布异常已独立闭合，最终APK仍与439文件dist精确相同；真实Android视口／Insets／IME与响铃／横幅未验仍阻断“全部测好／可以上线”的声明。构建时间元数据复用后逐字节核对属于工程收敛，不是放宽dist一致性；没有新增用户待追认产品语义。所有本审查新证据在ignored目录，产品代码只读，未部署／发送／重绑／改配置／重启／控制设备或显示页面。

### 2026-10-21 补充发现：稳定v2浏览器证据引起的当前结论更正

主会话在本报告当前矩阵落盘后补交稳定v2、全新goto且不再HMR的实际隐藏IAB观察。审查者独立读取`Web .archive/mobile-render-02/ui-probe/{README.md,product-sha256.txt,browser-v2-idle-before.json,browser-v2-loading.json,browser-v2-idle-after.json}`并亲读`App.tsx:94–106,234–247,324,916–935`。这些是当前ad7e484相同产品源码导入的真实Timeline组件、原生投影及`Controller.hydrateDetails → HistoryDetails → acceptHistoryDetails`，不是完整App/select或真设备；v1无owner夹具及HMR初轮均排除，不据其定产品。

**新增当前范围内违规F04／P2，RV10（原V06）从符合改为违规；其余判据不变。** 依据是冻结06:291“详情懒加载补齐只能原位替换对应facet”及06:255保留已完成Thinking手动展开交互、06:287动态转静态内容连续。这里不是要求额外的新持久交互状态：同一已完成Thinking、同一UID在本页已由用户展开，后来仅展开相邻工具／补其parent详情，没有新Turn完成或用户折叠动作，旧Thinking却因live退场改由HistoricalThinking接管而无条件折叠、正文从可见DOM消失。这是同身份展示交接丢失当前用户状态，超出了“只补对应facet”；R04所需修复范围与独立RV10已经覆盖详情原位接替，不另加产品要求。

直接观察链：`browser-v2-loading.json`为active=false、fixtureRequests=1、GET真实detail_row_ids=41；nativeOwner旧Thinking UID=old-thinking且closed，DOM可见其推理正文。`browser-v2-idle-after.json`仍active=false、同scope/main:A、同GET且fixtureRequests仍1（没有页重置）；同`thinking:uid:old-thinking`现在aria-expanded=false且只有Thinking标题，tool保持aria-expanded=true并展示详情；原DOM顺序始终oldquestion→Thinking→failed tool→lateruser→latest。源码解释与该结果一致：live `NodeDisclosure`用自己的useState；native详情退休live之后，`OrdinaryNode`内新挂`HistoricalThinking`，其`useState(false)`并无同UID交接。**顺序修复仍符合，违规仅在同身份详情替换丢失已完成Thinking的手动展开与可见内容。**

F04关闭要求：主会话提出符合冻结语义的工程方案；同页同scope同Thinking身份，在live→history／详情接管时保持用户当前展开选择；新的Thinking仍遵循running展开、真正完成自动折叠和默认历史折叠，不跨Conversation串状态；正式组件及真实Controller详情链路取得反例先红后绿和有效浏览器观察。不允许把全部历史默认展开、禁止live退休或制造双Thinking当作修复。不要求持久保存展开状态。当前ad7e484下F04未关闭，需进入本轮整改；修补后重新独立全轮复审，不能仅用本报告其余符合行拼成通过。

**以本补充为当前最新统计：32条＝28符合＋1违规＋3证据不足＋0不适用；原20条＝17符合＋1违规＋2证据不足＋0不适用。** 原矩阵及旧时点的无新违规结论保留作历史，本补充明确更正RV10/V06。F03仍已关闭，F01/F02继续证据不足，F04为新增本轮阻断。Verification不通过，不能进入正式Validation。主会话须将F04纳入plan，提出修补与关闭证据；不能因前述顺序已正确就抹掉手动展开丢失的独立反例。

### F04工程方案评审（待实现，非关闭）

主会话提案：由当前Timeline呈现owner在内存持有Thinking手动展开选择，按scope＋真实UID/row及必要phase关联；live NodeDisclosure与HistoricalThinking交接读同一选择。不写native消息、DB、localStorage，不复制正文或保留额外卡；初始历史仍默认折叠、running默认展开、真正running→finished仍自动折叠；只有已完成后手动选择在同owner、可证明同facet的详情补齐／源接管继承。切scope清除，UID不同或身份不明不猜继承，多phase独立，合并facet仅在原生UID证实时收敛选择。

Verification依据原RV10与06:255/287/291评审：**方向满足现有范围，不需新增用户口径，可以实施最小工程细化。** 条件是该选择确属当前呈现owner，不借永存memo充当消息事实；手动已完成选择不能被迟到同状态／详情重新初始化覆盖，而真正running→finished仍执行既有自动折叠。多phase／身份不可证不串状态，scope退出清理，关闭与失败补水保持已持有选择，实际源切换不出现双卡。需要正式组件与Controller详情链路的当前失败负对照、修补后的定向回归及稳定浏览器同场景补证。评审接受的是机制条件，未代主会话实现设计；实现版本／检查／新dist与APK一致性及后续独立全轮复审仍待完成。**F04尚未关闭，当前统计和门禁不变。**

### 2026-10-21 第三次全新独立整包复审记录（当前）

1. 阅读独立性：先完整读两技能、冻结索引／requirements／所指06相关原文、08§1–1.1、07§8.15；19条判据先落盘，之后才读AGENTS／CLAUDE／README／分区参考、旧报告、源码、测试与实现说明。判据原件完整追加第2节，另按原模板六列定位；没有先看旧F04再反向改判据。产品源码只读，新增只在本报告及ignored证据。
2. 全范围复核：FV01–19覆盖R01–R16与直接保留契约；正式入口、原生数据owner、模型／Profile／身份、关闭／失败／重连／退休／并发、消息顺序、Android桥接／打包及权限均有当前矩阵，不只复查F04。无新增产品要求或待追认口径。上一矩阵有效结论通过本次独立路径复核再接收，不简单拼接历史“符合”。
3. F03研讨链沿旧第6节保留：原判据要求真正持久源即时投影 → 旧实现发布前状态提交 → 主会话提出正常emit后提交、异常查原有replay区分pre/post环 → 本次从冻结独立建立FV04后亲审正式emit／frame／ring和当前测试 → 3b48cf0符合，关闭。没有新重试器或账本，未改变规格。
4. F04研讨链：原06§1.5详情仅原facet补齐及§1.4手动Thinking交互 → 旧真实DOM证明同UID已完成展开被接管折叠 → 主会话提出当前Timeline scope＋真实UID/row的内存选择owner，真正running→finished仍折叠、歧义不猜 → 历史审查已接受方案条件，本次独立FV06先建立后再核当前实现 → bf279b2正式Controller详情测试与稳定DOM均保留手动展开，scope退出／multi-phase／未知身份不串；memo性能反例也已修，68文件1038通过/1跳过。**F04关闭**，未扩大用户交互或持久化范围。
5. 构建收敛：F04修补后重新统一dist与APK，439文件精确一致。本次beforeBuild唯一copiedAt变化，经核其它438与JSON其余字段后恢复本次新冻结原字节；审查者独算439及inventory无差，旧40ef候选保留但不作为当前包。新包5c9c…与0.1.2同证书、版本1003递增；无实际安装／设备操作。该工程处理没有放宽“同一最终dist”，应在final-delivery摘要当前精确hash及证据边界。
6. 当前判定：**19条＝17符合＋0违规＋2证据不足＋0不适用；Verification不通过，正式Validation前置未通过。** 原20条当前18符合/2不足，上一32条当前29符合/3不足（同F01拆面）；F03/F04关闭，F01/F02未关闭。未接到本次报告被退回补审；没有分歧被静默丢弃。真实浏览器组件证据补齐了可观察UI，不能替代Android原生结果。主会话后续可筹备真实用户场景，但不得将筹备或局部验包当门禁已过。

供final-delivery及面向用户汇报主动摘要：标题、精确受理恢复、即时Heartbeat源事件、Thinking／工具真实位置与阅读锚、微信目标身份及最终统一包均具备当前有效实现证据；F04的内存呈现选择交接和构建copiedAt确定性核对是范围内工程收敛，无用户语义变更。**实际Android通知与WebView380／Insets／键盘仍未验，是整轮未完成的明确原因**。产物已准备并签名，未部署；真实Provider标题单次成功不是生产Conversation端到端完成。本次审查不发生产消息、不重绑、不改配置、不重启、不控制任何显示／设备，不消耗重复大套。
