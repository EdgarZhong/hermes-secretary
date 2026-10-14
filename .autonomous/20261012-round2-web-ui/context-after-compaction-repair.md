# FV-F04 · 暖会话压缩完成后的 Context 接线

当前：**Root源码review已接收（含两gap返修）；隔离阶段提交已自动push，待正式集成及真实复验，FV-F04尚未关闭。** 未修改正式main、后端、服务/config/DB，不运行浏览器或模型。原只读来源审计与validator报告均未改。

## 1. 对应条款与授权

现行02 §1.1–1.9（L18–272：身份、原生复用、eligibility），§2.6–2.7（L577–650：Anchor及有效路径），§4.7（L1252–1275：复用原生测量），§5.10–5.11（L1823–1856：并发/cache）；06 §1.13–1.14（当前L267–301）及§2.5（L398–410）；C108逐字段内存保值与冷无可靠来源暂缓。本轮Snapshot Index/baseline/plan/validation§4.8及B1真实字段表作为定位/证据入口，未改变冻结规则或产品语义。

Root亲读只读审计后判定FV-F04是范围内接线缺陷，授权新树 `/Users/edgar/code/hermes-secretary-web-context-fix`、分支 `codex/round2-context-after-compaction`，基于正式 `7ea5e64555bd41964cee4b8ffb4de60926fc1b87`。node_modules链接既有依赖，未install/改lock；common hook与源一致，未替换。测试独占窗口由Root放行，结束已释放。新增本专项交回文档与ignored证据是本任务明确授权。

## 2. 实际变更

五文件：

| 文件 | 变更 |
|---|---|
| src/core/context-after-compaction.ts | 45行集中owner：只持有pending native read token，不持有Context业务缓存；有效原生字段投影、同scope新观察失效、晚回防护 |
| src/core/compaction-view.ts | 原压缩观察owner在真实active→inactive或可靠terminal完成边界发起一次原生Context读；guard绑定view/lifecycle/已确认revision/operation；加载不阻塞700ms状态轮询与原history完成 |
| src/core/compaction-read.ts | 50行：抽出既有原生压缩读取/fence/History+Usage接线，新增现有context_breakdown调用；为冻结行数门禁，取消操作亦原样抽出，文案/语义不改；支持HMR保留owner惰性升级 |
| src/core/controller.ts | 保公共入口；在原生event与binding info Context观察点通知pending read owner；通过既有reconcileLiveView/UsageViews/mergeNativeContext发布当前scope；2000→1979行 |
| src/core/controller-context-compaction.test.ts | 22新增正式Controller用例，使用真实B1字段及受控RPC/时序 |

没有改API/DTO/backend/权限，没有前端自产token计数、持久化、独立loop/ledger、工具/provider路由或root prompt；读取原生字段不改模型上下文。原取消处理仅结构移动，FV-F03的原生generic summary与无额外成功toast保持，不将体验观察扩规格。

## 3. 正式纵向路径及不变量

Manual `/compact`现有session.compress链，原生automatic `compacted`事件链，Noting-requested Parent压缩真实`compacted`/原生operation链，都进入原 `readCompaction`/CompactionViews。原native state证实结束后，现有runtime通过 **session.context_breakdown** 获取used/max/percent/source/estimated；只投影这五字段，复用同一mergeNativeContext及live owner。原App按context_estimated=true给数值加“~”，不把estimate冒称provider测量。

一次读取的身份为epoch + profile/draft scope + runtime + native operation；原valid还检查connected及绑定runtime。scope/profile/runtime/epoch变化使旧回执无效；原生operation变化或active转换递增lifecycle。状态请求的revision仍用于原生读取收敛，Context回包先等待当前在途状态请求完成，再确认lifecycle、operation、inactive及confirmedRevision===revision；同operation重复终态read只更新已确认revision，不永久废弃有效Context读，不额外重读或重试。

同scope有效原生Context观察（event.payload.usage或binding.info.usage）只给pending token对应numeric字段加失效mask，**数值相同也代表新观察**。晚回仅删这些字段，used对应source/estimated一起删；仅max新观察不会舍弃used/percent，完整新provider观察保护全部。后续provider事件仍正常更新。

Context请求不阻塞History/Usage或700ms状态循环；请求失败、字段缺失/非法时保旧值，不伪造零或取消真实压缩。有效zero按C108可更新，缺max保旧max。不同选中会话不会被晚响应涂上旧会话值；原Conversation合法保留内存view可得到其自己的更新。无active/terminal operation的cold/idle状态不发Context请求，也不为cold新建runtime。

## 4. 验证结果与版本

证据根 `.hermes-dev/round2-verification/formal-validation/fv-f04-context-fix/`；最终源码/依赖、原始B1输入与命令结果hash见manifest。全部Vitest单worker，无fullsuite/build/新模型/真实请求。

| 证据 | 结果与覆盖 |
|---|---|
| red.log：新增文件 `-t 'reads B1'` | 原7ea5e64三条路径全部失败：没有session.context_breakdown正式调用，UI保旧39440 |
| green.log：新文件+controller `-t 'warm Context after native compaction\|native compaction completion ownership'` | 23通过/1失败；失败是手动原生rebind也会readUsage，夹具误要求仅一次；实际新Context接线通过。保原失败 |
| final-context.log：新文件 | 15通过；修正次数断言、Context请求仍精确一次；更新异步晚回验证，不以assert跑早冒充防护 |
| final-regression.log：同相关24例 | 24通过（15新+9既有），292ms；真实B1旧39440→46189/18%/estimated=true，三路径同正式完成接缝；后续provider48000覆盖估算正常 |
| cancel-extraction.log：controller `-t 'compression\|compaction\|Compaction'` | 14通过/55未执行，277ms；原取消、锁跳过、晚scope结果、HMR、状态/History等。抽取消后只复测实际相关路径 |
| typecheck.log / final-typecheck.log / typecheck-final-tree.log | 三次均通过，末次为最终产品树。没有build |
| health.log→health-final.log/health.json | 首次发现controller2002>冻结2000；原样抽取消后最终0 blocking/0 advisory，未改阈值/作用域/等级。最终controller1979，compaction-view最大CC18；新context owner最大CC9，compaction-read最大CC7/函数14行 |
| git diff --check / hook cmp | 通过，未stage/commit |

初次交回 **29 distinct**：15新Context用例 + 14既有压缩/取消用例；其中9旧例与24包重叠，不能相加成38，也不叠加此前78/127。初次五次窄Vitest，日志中runner Duration最大292ms，完整命令/失败/跳过保留。最初health阻断日志保留；后续只改结构再定向验证，不关闭门禁。未采历史峰值RSS，不以当前进程退出宣称历史资源峰值已覆盖。

Root亲审指出并授权修正两个gap后，**最终36 distinct = 22新Context + 14旧压缩/取消**。本次新增7例：max/used局部新观察2、真实Controller manual RPC返回+两次同op compacted交错1、回包先于在途同/新/失败状态确认3、同op重新active1。原15例全部保留，zero用例补等待异步发布完成；无弱化断言。

| 本次gap证据 | 结果 |
|---|---|
| gaps-red.log | 修改产品前3失败/1通过/15未执行；max/used局部增量与同op重复终态真实反例失败，active负例原先已有保护 |
| gaps-green.log | 32通过/1失败：新增等待状态确认后，原zero夹具少等待异步发布，补flush |
| gaps-final.log | 35通过/1失败：新operation会合法发起自己的Context读取，夹具未区分它与旧回包；只将新op自身响应设为空，再断言旧回包丢弃 |
| gaps-final-confirmed.log / gaps-final-tree.log / gaps-final-source.log | 36全部通过/55未执行；末份对应最终源码，339ms |
| gaps-typecheck.log / gaps-typecheck-final.log / gaps-typecheck-source.log | 全通过，末份对应最终源码 |
| gaps-health.log / gaps-health-final.log / gaps-health-source.log | 前两次CompactionViews.read.flight CC23/21阻断；抽集中readContext与confirmLifecycle后最终0/0、flight CC18；冻结阈值不改 |

本次6次定向Vitest（包含反例与两次真实结构修正后必要验证），runner最大360ms；连同原交回共11次小包，不重复计distinct，不跑full/build。测试窗口已释放。

## 5. 已证、漏检与缺口

原完成逻辑只读History与usage_detail累计统计，该DTO没有Context；原native usage在成功压缩后可省略Context，新有效breakdown从未正式获取。既有压缩测试只验证state/ring/History/Usage刷新，夹具也未含B1真实“usage缺Context但breakdown有估算”组合，所以未识别FV-F04。

22新增覆盖：Manual/automatic/Noting三入口、失败/空/非法值保留、字段独立更新及zero；晚estimate不能覆盖同runtime更新provider（同数值也失效）、后续provider正常替换；epoch/profile/runtime/disconnect/native operation晚回丢弃；选中别的route不污染且保留原scope；cold无operation不读。复用实际Controller/CompactionViews/mergeNativeContext，不镜像业务实现或读取源码断言。

初版Context专项只覆盖完整provider更新，遗漏局部max/used观察的逐字段保护；完成后的重复终态read也未覆盖。Root亲审识别后，现有owner从整读superseded改为字段mask，并以权威lifecycle而非每次读revision作为Context身份。revision没有全局放宽：未确认的新revision或state read失败依然丢旧回包；新operation/active变化保持无效。Context等待的是已有native state flight，不新增请求或无界retry；History/Usage仍不等待Context，完成锁不被其卡住。

本次三路径是正式产品机制+受控RPC时序，**不是三个新真实模型/浏览器旅程**。原B1真实UI与native字段仍作为失败来源，修后~46189/18%可从有效estimated字段与既有App渲染接线证明，但真实页面结果由原validator复验。parent Noting完成不替代压缩完成，测试中task_finished本身不会更新Context；真正结束仍由native operation/compacted事实决定。

失败读取保旧是授权边界，不表示新值已取得；此owner不新增重试循环。已有scope和原生API之外的cold来源仍暂缓。未测试本机以外平台，不冒称跨平台或整轮验收通过。

## 6. 接口影响与风险

对外接口、输入输出、RPC错误与原生cancel行为不变；只调用既有session.context_breakdown，不返回新DTO。新增owner仅有pending token Map，finally释放，disconnect/epoch的原clear入口一并清掉；业务Context缓存仍只属于UsageViews/原live状态。未引入独立计数、类别图、Prompt重建或配置写入。Context读错/缺失不影响已成功压缩的History/Usage接线，不把其误报成压缩失败。

HMR保留的CompactionViews和Context reader在原getter接缝更新prototype并惰性建立新owner，不覆盖已有连接/草稿/历史；旧legacy timer清理保持。其它owner的Usage来源字段逻辑没有改动。

## 7. 后续建议

Root已亲读五文件、原Controller上下游、36 distinct报告，并接收字段mask/lifecycle+confirmedRevision的正式接缝。按授权仅五文件阶段commit `3ad35d55f166e8fe8d50e7daf0cd778bbf1534c2`，既有hook自动push至upstream `origin/codex/round2-context-after-compaction`，远端同hash、隔离树clean。提交前git diff --check/manifest五文件hash/凭据模式扫描通过，hook可执行且与仓库源一致。未合正式main，未触服务或模型；不要复跑有效36例。原validator在统一源码后，同profile/runtime复验暖特殊Noting、普通自动、手动三个实际压缩完成边界，保存Context原生字段/source/estimated与UI更新时间/“~”标记，覆盖同runtime较新provider观察的必要时序。FV-F04由真实复验关闭；保留B1原失败与本实现机制证据的层次，不改validator原报告。
