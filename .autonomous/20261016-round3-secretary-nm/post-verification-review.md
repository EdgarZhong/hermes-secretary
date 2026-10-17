# 第2次 Verification 后的增量需求与实现审查

## 1. 范围、版本与结论

用户要求检查第2次 Verification 之后由其他模型推进的功能与细节，识别真实需求是否落档、代码与文档/文档之间的冲突、潜在回归，以及只接了部分链路的功能。本报告是主会话专项审查，不是第3次独立 Verification，不改写第2次门禁结论。

- 后端比较范围：`bd6207b6f2`（2026-10-17 12:28:29 第二次审查报告提交）至 `b6939f47e3ffdd81e507cc73a207e709fa0157d9`。开始时的两处本地模型选择器修改被其他会话提交为 `b6939f47e3`，本次已纳入读取；主会话没有替它们提交。
- Web 比较范围：`d554546`（12:27:47，紧邻该时点）至 `50cc8fd52dfe64a8f4afb4fe2d2cbbf8b8e5454e`。读取正式入口、相关调用者、测试与相邻生命周期；Orb 的部分旧接线缺口注明为继承问题，不冒称都是这个区间新增。
- 需求依据：现行 06、07、根 README/AGENTS/CLAUDE，以及本会话用户后续澄清。没有读取归档规格，没有将提交描述或测试预期自动当作用户需求。
- 本次审查基线发现**7项产品缺陷/实现缺口，另有1项质量门禁阻断**；后续Profile增量中F01的原会话4001重试错投已窄修并复证，现为6项产品问题仍开放。用户现场Timeline的两项已复现问题已修复并review接收；新增Profile功能的接收与证据见§7。原第二次 Verification 的4项不符合和2项证据缺口仍独立保留，不混作本次新增问题。

**用户在本次审查中直接确认的优先口径：** 冷启动允许沿用上次可信读数作为估算；普通提示统一5秒，错误手动关闭；Scheduler说明缩短但不改批量载体语义；首段Thinking直到Turn结束才出现及首工具闪动须修复，由子Agent负责。

## 2. 哪些是需求，落在哪里

“文档记为用户已确认”表示仓库现有确认记录；本次没有获得这些其他模型会话的原始用户消息，不把该标签扩大为亲自核验了逐字授权。“实现安排”不自动取得用户确认地位。

| 事项 | 需求来源与落档 | 实际接线与判断 |
|---|---|---|
| Schedule Table读取，浏览器不另造状态 | 06 §2.6的`ScheduleTableRead`及`Browser state boundary`，记为用户已确认 | `secretary.schedules`→正式Scheduler list→Controller→SchedulePanel已接通；有归属时区、展示时区问题，见F04/F05 |
| 标题与AI起名分开 | 根CLAUDE及06 §1.12：`/title`读取/手工改名，`/ai-title`独立Web命令；记为用户已确认 | 路由、原生写入与一次性`llm.oneshot`已接；起名输入不完整，见F07。不是仅有按钮或孤立helper |
| 置顶由后端持有，无浏览器排序表 | 06 §2.6明确`pinned`再按活动时间；§1.3另将管理按钮限制在获批设计范围 | PATCH与Controller方法已实现，但侧栏不使用pinned排序，且没有置顶操作入口。排序明确未兑现；是否补按钮仍应按获批设计，不能仅因有API自行添加，见F06 |
| 单域名、双SPA、共享API、唯一后端 | 06 §0.7、README部署入口、根CLAUDE，记为用户已确认 | 双dist挂载、子路径HTTP/WS重写已实现；既有报告明确未部署/未手机端到端，不把这两项说成已经完成 |
| 后端重启后模型/思考设置自动恢复再重试一次 | 06 §0.7第6项，根CLAUDE，记为用户已确认 | 基线异步重试错投见F01；后续Profile增量已固定原owner并定向复证，见§7 |
| 思考档位由后端声明集合驱动，未知时兼容回退 | 06 §2.10、README索引，记为已决策 | 配置/三家既有厂商表/聚合目录→既有`model.options`→可选契约字段及生成物→Web三态已接；本次静态检查未发现该链新的明确缺陷，不代表所有厂商真实复测完成 |
| 不把runtime有无暴露为产品状态 | 06 §1.13，记为用户已确认 | Reasoning已移除`Effective on this route`，Context无值时有简短解释；不再把Unknown当可见产品状态 |
| 冷启动至少给可用估算值，可沿用上次值 | **本会话用户直接澄清**；已立即更正06 §1.13、根CLAUDE | 这是允许的需求，不是缺陷。Context有新恢复路径；Session Total已有原生REST持久计数回退。归属/当前模型错误仍是实际问题，见F02 |
| 三种排期统一条目所属Hermes时区 | 根CLAUDE的明确用户确认、07 §6.1 | `schedule_timezone`已统一，但新Web读没有绑定相同时区作用域，前端显示也未使用返回时区，见F04/F05 |
| Timeline必须来自真实消息，通知/工具身份和顺序真实 | 06 §1.4及README、UI AGENTS；原有已确认要求 | 新工具/切换标记投影确有实现；现场样本确认的空白补卡和首工具挂载闪动已修复接收，实际证据边界见§6 |
| 思考强度切换Toast | 提交`5d6121c`等与代码；06已有通用通知规则，但没有完整写清该新Toast的触发/合并条件 | 存在本地pick和外部`session.info`差异两入口，不能仅凭提交描述证明你确认了全部交互。寿命现由本会话明确统一为5秒 |
| 模型/人格切换卡片精确标题 | `d107394`与投影代码；06只有Framework/真实来源通用边界 | `Model changement`/`Profile changement`这些精确词没有找到单独权威确认条款，属于落档不全；不擅自当作你要求的精确文案 |
| 移动侧栏滑入/滑出、Orb换层位置与动效、标题加快、表格横滑 | 相应提交/Mock和代码，06覆盖通用响应式/稳定布局，未覆盖全部新细节 | 可以确认已经实施哪些视觉，不足以证明每个参数都是你的已确认需求；不因无精确参数就杜撰产品需求或要求重新审批所有CSS |
| 普通提示统一5秒，错误手动关闭 | **本会话用户直接确认**；06 §1.15已替换旧10秒 | 原生通知和本地思考Toast共用`NativeNotices.track`，已改；测试见§5 |
| Scheduler解释文案缩短 | **本会话用户直接确认**；07 §8.14与`scheduled_attention_text`逐字同步 | 42→26英文词，保留授权/当前情况/修改排期/投递不等于完成；每项各带一份说明，整批仍一个carrier，末尾instant空档notice仍至多一次 |
| 首页独立Profile菜单及Profile图标 | **本会话用户直接确认并修订**；06 §2.11 | 只在首页/New Chat另加Profile下拉，不并入Model selector；Conversation行按所属Profile取前端固定映射图标，不做配置界面；增量与受控证据见§7，不冒称真实模型全链验收 |

## 3. 审查基线发现与后续处置

下列位置均为上述待审SHA中的位置。UI路径以独立Web仓库为根。优先级表达修复顺序，不替代用户的产品范围决定。

### F01 · P1 · 原会话的4001重试会写入新打开的会话

- 要求：06 §0.7第6项只恢复原设置操作所属stored Conversation，再重试同一次选择；保持Session/profile边界。
- 路径：UI `src/core/controller.ts:1007–1030`，`setSessionConfig`在第一次请求失败后重新读取`this.state.route`，并以该新route执行`ensureBinding`；`send`同时动态读取当前profile。
- 反例：在A点击high，等待响应时切到B；A返回4001，第二个`config.set`实际带`session_id=runtime-B`、`value=high`。A的操作改了B，不只是错误提示画错位置。
- 证据：前端首组第3例FAIL；固定原操作的stored ID/profile/runtime owner，并在恢复/采纳各边界保持它，不能从当前页面推导原动作owner。
- 后续处置：新增Profile切换的正式接线将此写入与恢复固定到原route/profile，独立定向反例取得RED→GREEN，原同owner恢复一次及non-stale不重试邻域通过。主会话review确认此路径已关闭；原历史脚本未重新执行，不扩张为所有后台跨会话操作均已关闭。新证据见§7。

### F02 · P1 · 冷启动读数取启动profile的库，并忽略已知会话模型覆盖

- 要求：允许估算，但必须来自该Session所属profile；沿用既有已知模型不匹配规则。
- 路径：后端 `tui_gateway/server.py:2202–2245`的`_restored_cold_usage`使用`_get_db()`；该函数明确返回启动profile共享库，不是`session.profile_home`的库。模型从该库JSON或metadata mirror取得，跳过已有`_live_session_identity`中的`model_override`。
- 反例A：两个真实隔离SessionDB都有相同stored ID及相同文本，启动库anchor=1020，目标库anchor=9020；目标Session读出了1020。一般ID不相同时则无值，形成看似“无法恢复”的假象。
- 反例B：持久anchor为model-a，当前会话`model_override`已为model-b，既有正式identity函数也返回model-b；新恢复函数仍把model-a的值作为匹配值返回。
- 证据：后端首组第1例、模型补例均FAIL。修复不能只在前端掩盖，也不能将“允许估算”解释为可以跨owner取值。

### F04 · P2 · Web Schedule读的是目标库，timezone却来自环境profile

- 要求：07 §6.1及用户确认的“条目所属Hermes时区”，06 §2.6真实profile归属。
- 路径：`tui_gateway/methods_web_read.py::_secretary_handler`选对db但未进入目标profile runtime scope；`secretary/web_read.py:108`调用Scheduler投影，`schedule_timezone`仍通过环境`hermes_time.now()`解析时区。只有部分timestamp渲染显式收到profile_home。
- 反例：环境Asia/Tokyo、目标库America/Los_Angeles，正式注册的`secretary.schedules` RPC读取目标行，返回的timezone却是Asia/Tokyo；`observed_at`同时正确为目标的-07:00。
- 证据：后端首组第3例FAIL。已有测试覆盖两库行隔离，没有覆盖两库不同时区，因此未暴露此问题。

### F05 · P2 · 排期绝对时间按浏览器时区格式化，却贴上后端时区名

- 要求：Schedule Table忠实显示后端实际时点和所属时区，不能让格式化后的钟面与标签矛盾。
- 路径：UI `src/design/indicators.tsx::formatScheduleTime`使用`date.toLocaleString`但没有传`timeZone`，随后拼接`item.timezone`。
- 反例：浏览器UTC、后端`2026-10-18T10:00:00+08:00`、timezone=Asia/Shanghai，实际组件渲染`Oct 18, 02:00 AM · Asia/Shanghai`，相差8小时；last_delivery同样受影响。
- 证据：前端首组第1例FAIL，使用实际SchedulePanel服务端渲染，不是源码字符串断言。

### F06 · P2 · 置顶只完成写入层，实际侧栏排序忽略pinned

- 要求：06 §2.6明确按后端pinned、再按活动时间形成确定排序；不建立浏览器置顶顺序表。
- 路径：UI `controller.setSessionPinned`与REST helper存在，但`src/core/session-groups.ts`完全忽略pinned，App侧栏仅遍历这些日期分组；组件没有调用`setSessionPinned`的入口。
- 反例：旧pinned会话和今天未置顶会话同时已加载，侧栏仍将今天未置顶会话排在前面。不能以API单测通过宣称置顶体验完成。
- 证据：前端首组第2例FAIL及正式App调用者静态检查。置顶按钮有无另受06 §1.3的已批设计条件约束；本报告不自行授权新增按钮。

### F07 · P2 · AI起名没有使用完整的当前可见对话输入

- 要求：06 §1.12为当前Conversation命名，保留真实输入来源；标题helper自身也声明排除运行机器信息。
- 路径：UI `src/core/conversation-title.ts:38–68`只要有一条persisted消息就彻底不用live；历史过滤只排几个文本前缀，未排`display_kind=hidden`等机器行。
- 反例A：历史已有旧主题、live已有新任务，生成输入只有旧主题；存在历史时最新实时内容不会进入标题请求。
- 反例B：历史隐藏工具白名单/维护控制行被包装为`User: ...`传给起名请求，可能让标题命名内部机制而非实际聊天。
- 证据：前端首组第4例、额外组第3例均FAIL。应复用同一真实可见投影并处理已持久化/实时重叠，不是再添加一串任意前缀。

### F09 · P2 · 失败任务的结束事件也会点亮“Snapshot ready”

- 要求：06 §1.15明确Noting失败不得产生成功完成高亮。
- 路径：后端`secretary/noting_child.py:586–594`在失败/abandoned等finally路径也注销任务并发`task_finished`；UI `controller.ts:1185`据该事件无条件设置`secretaryCompletion`，`App.Secretary`随后显示`Noting finished — Snapshot ready.`，没有提交/有效Snapshot证据。
- 反例：仅发一个真实协议可出现的failed-task结束hint，未有Snapshot变更，Controller仍生成completion revision。后端结束事件表示生命周期已结束，不能当作提交成功。
- 证据：前端额外组第2例FAIL及后端finally路径。该问题在比较区间前的Orb实现中已存在，本次是发现仍未接完整，不称作后续提交新增回归。

### F10 · P2 · 后续增量未通过冻结代码健康门禁

- 入口：`.venv/bin/python scripts/check --staged --base a51fd99abc783f245ab855526a10862f2c89656a --only ruff,health,no-tmp`，固定基线、类别和阈值未改。结果ruff/no-tmp通过，health覆盖158文件、13条blocking、0 advisory，11.9秒；原始输出保留。
- 8条可定位到后续实现/测试：`hermes_cli/inventory.py::_declared_efforts`两处静默catch各触发BLE001/S110，共4条；`_apply_capabilities`嵌套7层（原5，目标6）1条；`tests/hermes_cli/test_model_switch_custom_providers.py`原已超长2441行增长至2497行1条；`server.py`两个冷启动helper静默catch共2条。不能以功能测试通过代替这些固定约束。
- 另5条为旧Verification证据脚本F811诊断，不能直接当作五个代码重定义事实：只读源码每个相关函数只有一个定义，直接运行当前ruff对这两个文件返回空数组/exit0。这里保留为检查器诊断待排查，不能悄悄删旧证据或放宽规则消除红色。
- 本次用户授权的变更是通知/Timeline/Profile增量及Reminder文案；本报告不顺手调整这些其他后续实现。当前门禁仍失败，不宣称代码健康全绿。

## 4. 文档本身的冲突、缺失与本次更正

1. **冷启动估算：已按用户更正，撤回旧判据。** 06旧增补同时要求从上次读数恢复、又写`never estimate locally`，与用户明确允许估算不一致。现已写明允许沿用同Session可信旧值估算。不能再以“不是当前精确值”判失败；也不能把单次context占用和Session累计当作同一统计量。实际Web已通过`src/core/usage-view.ts::savedSession`回退到REST原生持久Session counters，不能仅凭live返回unknown断言整个Session Total没有恢复。原先该断言撤回。
2. **普通提示时间：现已由用户统一为5秒。** 旧文档10秒、旧本地Toast4.5秒曾不一致；用户现在给出新的统一值。已把新确认写入06，并将两条提示路径归同一计时owner。原反例仅保留历史观察，不再作为现行规则的待修项。
3. **置顶与日期分组缺少明确整合。** 06 §1.3旧规则要求按日期互斥分组，后来§2.6又要求pinned优先，未说明Pinned是否单独分组或如何对日期分组应用优先级。不是数据所有权空白；全局pinned优先的实现仍缺，但具体布局不能由Agent假定为已获批。
4. **新Orb动效/层级设计未完整替换旧表现契约。** 06 §1.15就地替换了Memo，但旧表格仍描述有资格的Next Idle estimate；当前App固定`Waiting compaction trigger`，不使用服务端已有`next_idle`；Mock/注释又涉及elapsed、Force/普通完成区别，而正式DTO没有相应字段。能确认“显示和资料未对齐/部分未接”，不能据此臆断你还要求旧倒计时或已经确认了全部新动效状态。应先把你的实际新设计决定补到原06相应段落。
5. **部分新精确交互只存在于提交和代码。** Toast的本地/外部触发与去重，切换卡片精确标题，移动抽屉动效与若干几何参数，没有完整的用户确认索引。这里区分产品交互与普通CSS实现选择；后者不逐项要求用户审批。
6. **有替换说明的历史文字，不硬判为双重权威。** 06表格残留`CurrentMemoRead`和Memo字样，但章节顶部明确写了第三轮删除/替换范围；应按就地替换条款解释，不能借残留旧表要求恢复Memo。根CLAUDE的历史details也不能反过来覆盖顶层当前状态。
7. **5098是上游原生保护，不是本次新增。** 已对照`hermes-upstream`与上游提交`eb8a1580c65c380a539ba1fcdc53f96a8770fa47`：`gateway.code_skew.detect_code_skew`比较启动与磁盘Git指纹，`model.options`/`model.save_key`等直接拦截；调查时没有关闭该保护的config/env/CLI选项。文档提交也会改SHA，开发中会频繁触发，不等于已发生实际模块不兼容。用户随后已批准默认开启、进程级、仅绕过模型拦截的开发开关，确认范围落06 §0.8，提交`8a374fb`；本会话只提供实施prompt，用户安排其他执行者，尚未修改保护代码或运行配置。

## 5. 执行证据与适用边界

原始脚本、实际日志及SHA256见[evidence/post-verification-review/manifest.json](evidence/post-verification-review/manifest.json)。证据脚本放在专项目录，临时执行文件已从默认产品测试目录移除，不把有意保留的反例加入默认suite。

| 执行 | 范围与结果 | 现行含义 |
|---|---|---|
| 后端首组 | canonical runner单文件，3 FAIL；`backend-probes.log` | 2个现行反例：库归属、时区；1个关于禁止估算的旧预期被用户澄清覆盖，不能继续计作现行失败 |
| 后端模型补例 | 同runner仅选新节点，1 FAIL/3 deselected；`backend-model-probe.log` | 已知model_override与读数比较模型不一致；没有重跑首组 |
| 前端首组 | Vitest单文件4 FAIL；`frontend-probes-run.log` | 时区/置顶排序/错会话重试/最新起名输入四个现行反例 |
| 前端额外组 | Vitest单文件3 FAIL；`frontend-extra-probes.log` | 失败高亮及隐藏起名输入两个现行反例；旧10秒预期已被新5秒授权覆盖 |
| Reminder缩短 | canonical runner精确2项PASS；`reminder-shortening.log` | 同批一个carrier、逐项ACK、混合instant空档notice至多一次；文案与07逐字一致 |
| 普通提示5秒 | 首次28项：26 PASS、2个旧4.6秒断言FAIL；修正这两个旧断言后仅定向2 PASS | 有效并集28项PASS，涵盖原生/本地提示、错误持久、clear/replacement、重连/HMR；主会话没有复跑整个suite |
| 固定代码检查 | ruff/no-tmp PASS，health 13 blocking/0 advisory，158文件，11.9秒 | F10；直接ruff对两证据文件为0诊断，不改写原health失败 |

历史总计11个反例执行失败，经用户澄清后其中**9个适用当时需求，归为上述7项问题**；两个旧需求预期已明确失效。后续F01窄修见§7，现仍开放6项产品问题。没有将历史失败日志改成绿色，也没有把新授权倒填为旧运行已符合。首次前端外部symlink因Vite根限制在收集前失败，0 tests，移入UI正常临时测试路径后执行；该环境问题不计产品缺陷。

后端使用官方PM Python 3.14.7/macOS arm64，经`HERMES_PYTHON=... HERMES_TEST_FILE_RETRIES=0 scripts/run_tests.sh`。使用真实隔离SessionDB/注册RPC、受控会话/外部请求边界；UI使用实际Controller、实际组件渲染或正式输入/排序函数及fake timers。反例证明具体机制，不宣称真实浏览器/真实模型已全部验收。所有数据合成，不修改用户round3状态、不调用NM、不部署、不重跑大型回归。

复现：将后端证据脚本临时放入主仓库`tests/secretary/`以获得隔离conftest，再走canonical runner；用`-k`选现行反例，勿选已撤回的禁止估算预期。前端脚本放到Web `src/core/`运行`TZ=UTC npm test -- <具体文件>`；首组保留了本次实际绝对import，异机复现需仅将import改为对应本地源码路径；额外组已使用该目录相对import。不覆盖已存在文件，执行后移除临时测试。

## 6. 用户现场Timeline回归及后续

用户直接观察并确认：Send后首段Thinking在整个流式阶段缺失，Turn结束后才出现；首工具卡片开始时有瞬间闪动。用户已授权修复并要求委派。

`timeline_stream_regression`（GPT-6.1/high）负责正式流式投影/组件与定向反证、修复和typecheck；主会话处理本报告、普通通知与根文档，修改范围分离。调查必须区分真实reasoning.delta与等待提示thinking.delta，核对legacy/typed sidecar配对、WS顺序、history/live retire、组件身份和工具状态，不能以结束后的静态历史正确代替动态正确。不得靠延时、伪造Thinking或状态掩盖。

子Agent已只读取到一个完整156帧、2个Turn的现场replay：两Turn均无`reasoning.delta`，首工具前是`thinking.delta`等待字串/清空，实际assistant reasoning_content仅空格，却在结束历史投影生成空Thinking；另一个512帧replay已截断，不能宣称覆盖完整。不得将该样本描述成“真实推理增量被前端吞掉”。同时定位工具构造卡取得正式UID后呈现key改变、React重建的路径；实际组件逐帧反证及修复已完成如下。原始现场事件只保存在ignored目录，不公开用户内容。

用户还明确补充：第三轮自主实现前Astra曾修好前端且当时实测正常。已交子Agent按Git历史/既有证据定位参考版本，不能未经核验假定任意SHA就是该正常版，也不重复整套旧测试。

**修复已由主会话review接收并提交UI `01be26a1630fd4c28aecab6205be6493d3a31ba9`。** App的呈现key映射仅维持当前列表内挂载身份，精确承接构造节点→真实occurrence UID→历史行；不改原生ID、顺序或按名称匹配。历史Thinking渲染要求原文trim后非空，展示仍用原文。新增7项逐帧Controller→RenderStore→生产Timeline组件测试：改前2个RED，修复过程中保留10个自引null/undefined失败及回修；最终版本56 PASS，前一版本有效并集99项，不能冒称最终又全跑99项。整合主会话通知后typecheck一次PASS。完整命令、次数、耗时、文件哈希与正常历史参考保存在ignored `timeline-fix/report.md`；已核对没有回退此前正确的UID、并行次序、分段/去重及滚动机制。未发起新真实模型/新Conversation、未做真实浏览器肉眼验收。

同一子Agent随后接收用户新增Profile任务；基线为上述已提交UI版本，改动与证据单独交回，不把旧Timeline测试重跑充作新功能验证。其余开放项未经本次用户逐项修复授权，不在审查中顺手改变产品行为。

## 7. 新Chat UI Profile功能及归属修复

UI已提交并同步`0371c6c19b2d4a5224ffdce2989efbc2a3fda6b1`；该提交排除用户同期表现调整。

主会话已集中review接收：New Chat独立Profile下拉，菜单仅显示名字；沿原生`profiles.list`、`session.create(profile=...)`及profile-scoped REST/RPC工作，不复制系统提示、不新增Profile存储、不迁移已有Session。启动无显式名字时以原生`config.get(key=profile).home`精确匹配roster.path，不能把`is_default`误作当前启动Profile。各Profile草稿、模型/effort及已staged路径分开；创建/Send未决时禁止改变owner；默认目录、能力、列表、恢复晚回包均按原owner采纳。

Conversation图标集中在UI `src/core/profile-icons.tsx`：default为MessageSquare、round3为FlaskConical；未来新增Profile需补映射，未知名字为UserRound通用fallback。Session原生归属仍是唯一真值，当前列表沿既有profile查询，不新增跨Profile聚合。用户同期表现层调整保持原样，不纳入本次功能修复。

F01配置重试由`writeOwnedSessionConfig`固定原route/profile/runtime，4001只恢复原Session并重试一次，受控反例RED→GREEN；未选中的owner不展示成功toast，不以当前页面替换原动作owner。主会话review另发现并要求修复根URL显式Profile被last-route覆盖、以及另一owner旧Conversation ID被带入的两处初始化缺口；分别取得RED2→GREEN，只允许恢复同owner旧路由，不同/未知owner进入所选Profile的New Chat，无显式owner时保留原恢复行为。

有效并集**113项PASS**：新增Controller11、App/组件13、既有Controller80和metadata9。共11次Vitest、两次对应不同代码版本的typecheck通过；最后定向8项PASS，未重跑113项全套。中途104P/1F的空New Chat缓存回归通过收敛保留范围修正，原测试断言未改，仅失败项复测通过。主会话没有复跑子Agent有效测试。合成日志、脱敏原生观察与哈希见[evidence/post-verification-review/manifest.json](evidence/post-verification-review/manifest.json)的`profile_ui`及`profile-ui/`。

真实只读观察确认default/round3名单、启动home唯一匹配round3；未修改用户Profile、重启后端、真实create/发送、调用模型、上传真实附件、连接NM或部署。请求owner及原生整套继承由受控Controller→App正式入口测试和后端接线源码共同核对，不冒称真实模型全链或浏览器视觉验收。其余6项产品问题及F10质量阻断继续开放；本次不是新的独立Verification/Validation，也不改写第三轮未通过结论。
