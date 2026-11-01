# Hermes Secretary 当前状态

## 2026-11-01 · GPT订阅历史指令角色兼容修复（进行中）

用户明确要求修复；主会话亲自实施，不派sub。限定ChatGPT订阅出站角色：root仍instructions，中途system保原文／位置映射developer，不改持久历史／默认模型，不重放失败用户消息，不全量merge上游。统一主请求、auxiliary与native replay转换，预检接受developer，其它Responses路由保持system。主／aux／native replay已接统一转换，root／旧消息前缀／工具配对和通用Responses不变；4文件291项通过。补真实gpt-6.1-terra合成最小请求后main上线；真实探针只在隔离运行态，无用户历史／工具执行。

## 2026-11-01 · GPT-6.1 Terra调用失败调查（已定位，适配修复未实施）

用户反馈模型调用失败并要求检查原因。用户已自行将Alex置顶20261021_200341_2ce088切为openai-codex／gpt-6.1-terra／codex_responses／High；因此此前“暂停切换”仅为当时Agent未代执行，不再代表会话当前模型。22:55:24实际请求HTTP400 detail=System messages are not allowed，非目录缓存／上下文阈值问题，未自动重试生成。只读原生转换当前32条history，发现1条中途system，序列化后仍为system（位置3）；root instructions独立。现行adapter和runtime_system_transport测试同时保留并断言Codex backend历史system，缺少真实订阅端兼容证据。调查没有改源码、历史、Prompt或默认配置；后续须在实际订阅出站层保持文本／位置／root前缀，使用端点接受的指令角色，并覆盖main／aux／预检、其它Responses路由不变；尚未实施或宣称生成成功。服务器受限证据gpt-call-failure-20261101。 用户随后要求判断是否同步上游；已只读fetch upstream/main到c627ec84664d43e0b18b95d9d86d8963747d56c7，未merge／部署。blame确认发送中途system及相应预检／测试均由本地8969e32引入；最新上游仍仅接收user／assistant并跳过system，未提供保留这些历史指令且兼容订阅端的直接补丁。相关上游0ae220ff4e／a4a992645b／5af8fda75f为跨Provider端点抽象／Responses接线重构，68e4c2b31a为UA构造，不能当本错误现成修复。结论：先修本地订阅承载并补真实订阅证据，上游兼容按依赖另审；不能靠整批merge修本地回归，也不能恢复静默丢系统更新。

## 2026-11-01 · 连续模型切换误报修复（已合main并上线）

用户澄清连续切换两次：第一次令旧模型展示计数失效是正常行为，不能因此拿累计输入量新增异常切换门禁；明确要求修复。范围仅统一selection_context_for_agent移除session_prompt_tokens回退，无有效当前计数则不触发context-cache确认，保留有效大上下文及其它既有guard；不改默认模型、不发生成、不自动执行暂停的会话切换。主会话独立实施。改前正式_apply_model_switch连续切换回归精确复现390494错误警告（连同未知计数共4项失败）；仅移除累计回退后6文件31项通过，历史与默认配置保持，有效大计数仍需确认。ruff／health检查通过，产品5485324150已push并从main发布；Web／Gateway实际版本一致、微信connected。云端只读复核0／−1／None计数均不弹确认，真实390494仍弹；保护数据、配置／授权、双静态逐指纹保持，零生成请求／会话切换。原置顶切换仍按用户暂停状态未执行，回退与两套三库备份入口见运维记录。

## 2026-11-01 · Alex共享GPT授权（已完成；置顶会话切换按用户要求暂停）

用户明确确认复用study既有ChatGPT订阅授权，并允许迁入Hermes原生公共凭据库，接受default Profile也获得GPT能力；Alex默认Kimi及study默认GPT保持。主会话独立实施，服务器内原生锁／writer迁移单一openai-codex授权，避免复制旋转refresh token；不迁移其它凭据，不发模型消息，不重启服务。 已通过原生锁／writer将study的openai-codex单一授权迁入控制根auth.json并移除study重复条目，0600受限；三Profile原生作用域均读取同一源，Alex仍k3.1-pro、study仍gpt-6-sol，其余凭据保持。原生刷新及账号实时目录确认gpt-6.1-terra可用，零模型生成。用户进一步明确只把Alex当前置顶「Edgar 身心支持与就医跟进」切到GPT-6.1 Terra、不改默认；随后要求先暂停核对39万tokens警告。只读核验切换前最近有效usage_anchor输入67067＋输出155＝67222，Alex配置窗口512000（约13.1%）；当前stored model为kimi-for-coding而anchor为k3.1-pro，实时读数已标model_changed失效，不把0当真实占用。model_selection_guards直接用compressor.last_prompt_tokens并回退累计session_prompt_tokens，缺少现行anchor／有效性核验，存在明确误报路径；390494的精确内存来源尚未取证，不冒称已完全定位。授权迁移时保护未关闭、源码未改；随后连续切换误报已由上节修复，按用户“等一下”尚未执行目标会话切换。受限收据／回滚说明见运维记录。 用户随后反馈模型菜单找不到Terra，最后明确已看到，确认此前可能仅加载缓存目录。核对App菜单可见性已触发capabilities按需重读（早期只看组件而称重开不读不准确，已纠正）；Provider账号实时发现与Alex正式REST已含gpt-6.1-terra。经原生model.options显式刷新Alex／study后，各自普通缓存读取也含该模型；无需修改Provider、增加重复菜单请求／UI入口或重打包，未发送／切模型，证据服务器picker-refresh.json。

## 2026-11-01 · 真实Chrome性能复查（已合主线、Web已上线、APK已更新）

**本轮用户进一步确认：** 当前Conversation切换／重新进入／重连的恢复优先，流量尽量只传变化、消除可避免串行等待和本地重复工作；侧栏约108KB允许后台整页刷新，当前不新增列表差量协议。侧栏与Conversation恢复及发送就绪解耦：先展示已有缓存，缓存会话项立即可点击切换，不等待列表核验／增量；目标会话仍独立核对存在性与自身权限。隐藏的移动侧栏不抢占当前聊天恢复；Usage／Context等附属读取不能阻塞当前聊天关键路径。这是明确用户确认，覆盖本轮此前“需为侧栏新增差量”的排查方向。

用户授权操作／刷新两个已打开的Hermes Chrome页面，覆盖本轮显示保护限制；主会话亲自实施，未派sub、未发送消息。FE最终`129b9a2`已合main／origin/secretary，Web439文件／6HTTP资源verified；后端产品仍main `2e287d73b6`，本轮静态更新零重启／数据库写。统一Composer尺寸动画移除每次React提交的同步测量，改为布局后的ResizeObserver；恢复布局ACK幂等、局部显示引用与历史缓存去重、日期格式器复用。原真实slash样本85–129ms长任务／最高116ms帧间隔；修后两轮175帧无>50ms长任务，仅一次约32ms间隔，不等同所有设备全流程零卡顿。

侧栏缓存立即可导航（含Profile roster未返回时跨Profile缓存条目），不授予目标写权限；列表／Usage／Context不gate聊天发送就绪，较重读取在共享最终cut后启动，pending／controls与cut并行。viewport替代cut继续共享等待；已核验历史缓存写入不再被附属统计抢先更新取消，capsule取实际显示ACK快照。相关7文件232项、App专项4项及typecheck／生产构建通过，6产品TS相对基线无新增健康超标；旧warm／Profile失败在5a02a9a原样复现，未冒称全套全绿。

真实Chrome增量恢复200条窗口重传正文0条／thinking0条，逻辑JSON绑定约3.3KB＋最终cut22.1KB，无system_prompt。REST侧栏约107KB仍允许后台传输，不冒称timeline流量；实测其请求在cut后发起且未完成时Send可用。同协议生产新连接压缩收包对照约54.5KB→12.0KB（约−78%，仅绑定＋最终cut、loopback传输层、不含TLS，并非精确Chrome整轮线速）；服务端最终对账仍232–246ms、首次显示仍约100ms，本轮不能称只剩网络或到达极限。

最终0.1.10／1010 arm64 APK已严格核验原签名／v2／CRC／16KB／439资源及交付副本；Web／APK438文件逐SHA一致，另一资源清单仅copiedAt时间不同。APK路径、SHA、发布／回退收据和证据见[运维记录](docs/operations-log.md)。未安装Android真机，不冒称键盘黑块／设备流畅度已验；原用户两页保留，原草稿为空，无业务写入。
## 2026-11-01 · 表现层动态错位修复（已合主线并发布Web）

用户新录屏显示slash收起时列表先消失，工具栏／输入与外框未同步，出现空白和位置漂移；此前性能修复与组件几何验证不足以关闭实际表现问题。用户明确先把表现层优化做好，再做网络层优化。已按此顺序先完成表现层逐帧复现与修复并单独上线，再恢复传输优化；覆盖命令／附件／文本／选择器／恢复胶囊及快速反向，不以隐藏／取消动画替代。录屏证据ignored `.hermes-dev/recovery-transport-20261101/user-video-*`，不得把此前af60634标为已完成设备／实际入口验收。

已确认准确问题：原视频3.25–3.45秒外框底边基本固定，但发送按钮从约989上窜到820像素再回落；低频连环图漏掉关键帧。A/B实际绘制录制复现旧WAAPI的布局／合成线程不同步：人为130ms／90ms主线程停顿下旧按钮上窜约155px，新版统一rAF写入高度／位移／裁剪后未重现。FE `edb66eb`已合main并完成Web的439文件／6HTTP资源核验，尺寸仍唯一触发、每帧无几何读取／React更新；退出内容保留不可交互的临时副本，支持反向及中途目标变化。3文件17项、typecheck／健康检查通过；正式App含200条历史、五条命令，连续三次开合129→381→129px，207几何帧底边距偏差<0.01px，151实际绘制帧另录视频。移动胶囊／文字并发底边误差<0.5px，窄屏无横向溢出。证据前端performance/full-final-*、composer-full-app-fixed.mp4、unified-*；Android真机仍未验，不把隐藏IAB等同用户Chrome真机最终验收。

## 2026-11-01 · 恢复传输瘦身与串行等待优化（已合主线、上线并更新APK）

用户明确授权继续省略重复system prompt、减少可避免串行等待，保持兼容与完整恢复，测好后前后端合主线、上线并更新APK；主会话亲自实施，禁止sub。基线BE `0db380f93e`／FE `bc3ba70`，主仓干净，前端仅五个既有未跟踪.DS_Store。方案：新服务端在现有Profile读取中声明可选投影能力，旧客户端默认完整响应，新客户端仅能力明确时省略Prompt；只读metadata与Profile确认并行，绑定和最终对账仍等身份及数据核验成功。验证覆盖旧新两端、失效owner／失败／冷启／重连和真实传输字节；不改模型Prompt／缓存内容，不派sub。 前端107项恢复链路与112项相关集成通过；后端原生恢复／只读冷装载的可选投影通过，默认完整返回且运行态Prompt不变。扩展发现review.summary目录孤项及旧Noting配置导致17个setup错误，均在0db380f93e隔离基线原样复现；句柄测试共享关闭Event竞态也在基线复现，已改为等待目标句柄自身信号，10项通过，保留关闭次数断言。BE `2e287d73b6`／FE `5a02a9a`已合主线并发布；Web439资源／6HTTP校验、服务版本／数据库／配置／绑定保护通过。生产只读三轮默认→精简→默认的恢复窗口均complete／matched，Prompt保持；绑定＋最终对账JSON响应114074→25460字节（未压缩），不等同总耗时下降。正式构建隐藏IAB实际选会话及断测试隧道重连通过：239展示节点保持、document不刷新、两次activate均省Prompt、最终complete并退出提示。最终0.1.10／1010 APK（SHA105bcd1d…）原签名／CRC／16KB／439前端资源和交付副本通过，Android真机黑块／流畅度仍未验；构建脚本调用到旧Python导致校验入口失败，已用项目3.14执行原校验器通过，未修改或放宽校验。完整收据与回退／备份保留记录见运维日志；基线工作区、隐藏页及测试连接收尾清理。

## 2026-11-01 · 恢复传输链路调查与活动请求去重（已上线，后续机会已定位）

用户明确优先恢复／传输在网络瓶颈下的效率：减少多余往返、重复传输及可避免的串行等待，前后端CPU优化适度，不追求极限。实际生产构建经隧道正常恢复样本仍有本地长任务，不能宣称只剩网络；已将三个Profile各自的全局活动读取收敛到批次统一对账，保留外部失效触发与完整恢复判定。FE `bc3ba70`已合主线／Web上线；正式构建实测4→1次，正文就绪约1109ms仅是单样本、不声称总时长固定改善。相关111项／typecheck／健康检查通过，Android扩展7项失败在改前af60634原样复现。主会话独立实施，隐藏页／两个Vite／SSH隧道已关闭。

另已定位尚未实施的传输优化：绑定与最终对账各携带约44288字节system_prompt，当前Web/APK源码无消费；两次响应约52KB／65KB（逻辑JSON，非压缩后线上字节）。后续可增默认兼容的可选参数省略，不能直接删公共响应字段或冒称已省掉。仍有身份确认→元数据→绑定→最终对账的依赖，不宣称“只剩网络瓶颈”或带宽已充分利用。证据前端performance/activity-*、主仓activity-release；本次APK仍为af60634动画修复包，未把bc3ba70去重重打进APK。

## 2026-11-01 · Composer统一高度动画性能回退修复（已上线，APK待真机复验）

用户澄清所有原因触发的Composer高度动画都极其卡顿，而改造前attachment伸缩流畅。已移除逐帧继承CSS变量，改为一次读取几何、原生height／transform／clipPath同步动画；保留统一按实际高度驱动、内部内容同步、快速反向及减少动态效果。FE `af60634`已合主线并上线。隐藏IAB同六次开合Style由154.95ms降至14.68ms，Task由339.7ms降至148.43ms；5文件40项、typecheck及健康检查通过。移动端几何复验无明显跳变；新0.1.10 APK已严格核验，未安装真机，不把桌面结果冒称设备流畅度验收。证据前端`.archive/composer-motion-20261101/performance/`及主仓`.hermes-dev/ui-motion-20261101/performance-release/`。

## 2026-11-01 · 桌面胶囊420px定稿（已上线）

用户进一步确认最大宽度420px，替代此前480px；沿用右侧固定、左侧留白、自适应和轮播定宽规则，仅桌面CSS，FE `e5a3722`已合主线并上线，构建和439文件／6个HTTP资源校验通过。证据`.hermes-dev/ui-motion-20261101/width-420-release/`，前版480px记录只属当时版本。

## 2026-11-01 · 桌面恢复胶囊宽度微调（已合主线并上线）

用户要求桌面胶囊缩短、明显增大左侧留白：宽度设上限，窄Composer再自适应左侧空间，继续不随文字改变。沿已授权主线／Web发布收尾；实施值最大480px、右侧原位置不变、左预留按剩余列宽在32–64px之间收缩，达到最大宽度后多余空间留左。仅桌面CSS，移动端与恢复条件不变。FE `ce5a70d`已合本地main／origin/secretary并上线，构建及439文件／6个HTTP资源校验通过，零服务重启／数据库写。隐藏IAB宽1400／1100时胶囊480px，900／780时456／345px；长短文字宽度一致、中心偏差0，移动端保持330×26px（380px视口）。证据前端`.archive/composer-motion-20261101/width-cap-*`及主仓`.hermes-dev/ui-motion-20261101/width-release/`，实际组件图`desktop-width-cap.png`；隐藏页已关闭。

## 2026-11-01 · Composer统一过渡与恢复提速（已合主线并上线，APK待真机复验）

用户确认本轮前后端合主线并上线Web；主会话亲自实施，0 sub。Composer所有实际内容高度变化统一驱动320ms外框和内部区块过渡，覆盖附件、命令、选取器及文字增减，不按业务事件分别触发；快速反向承接当前位置，减少动态效果直接到终值。移动端恢复胶囊保持底部26px灰填充、12px左对齐、无描边、上下伸缩；桌面移入主按钮左侧，与左工具选项整行中心对齐，按父容器剩余空间定宽、不随文字或轮播变化，右侧固定横向展开折叠。保留用户所选D样式，覆盖此前全平台底部布局。

键盘改为支持页面保持完整WebView绘制表面，避免收起临时扩面；原生仅传动画边界／系统曲线，动画中保留背景已绘帧、结束续播。草稿／历史／元数据读取并行，草稿离线仍可用、同次读取共享且不覆盖较新编辑。后端在单次只读事务内复用身份／顺序内存TEMP索引、退出销毁；summary去除界面不用的完整工具快照，完整详情不变。对账／权限边界不提前放行。

验证：前端恢复137项、表现层43项、原生IME 11项通过，14个TS文件相对基线无新增健康问题；后端相关六文件最终有效174项通过，冻结检查9项通过、唯一no-tmp为未改历史报告基线。隐藏IAB逐帧覆盖文字／附件／命令增减、提示开合、快速反向及减少动态效果；桌面不同文字宽度相同并与左工具中心重合。统一高度初版曾发现内部工具栏先跳，已补位置差同步并逐帧复验；这些是浏览器真实组件／原生单测证据，不等同Android设备验收。

产品BE `1df27e5020`在main并上线；FE `bb8596b`已快进本地main、推origin/secretary并上线439静态文件。线上两轮历史读取107–112ms、恢复对账226–231ms，改前分别约290–320ms和760ms；summary由83KB降至1.5KB，不把服务端分项计时等同用户端总耗时。APK已通过原签名／CRC／16KB／前端SHA及交付副本校验，设备黑块和最终流畅度仍待用户新包复验。普通Conversation切换**仍显示恢复胶囊**；已如实回答用户，建议正常切换静默、异常／重连／长等待再显示，但用户尚未确认该改动，本轮未实施。

证据：前端ignored `.archive/composer-motion-20261101/`、主仓ignored `.hermes-dev/ui-motion-20261101/`；发布、测速、备份保留、APK路径／SHA及恢复入口见[运维记录](docs/operations-log.md)。隐藏验证页与Vite已关闭，未动用户页面／设备；前端原有五个未跟踪.DS_Store保留。

## 2026-11-01 · 空闲AI标题恢复修复（已合main并上线）

用户截图反馈`/ai-title`因完整native Main snapshot不可用而要求先跑普通Turn。最新确认：以当前生效上下文命名，复用完整Main前缀；Turn空闲就允许重新生成，不以已有缓存／旧Web runtime作为额外前提；后台压缩无活动Turn时读当前原子生效版本，不因维护标志一律拒绝（覆盖旧忙时压缩口径）。主会话审接线、DeepSeek隔离验证与发布；title_idle_fix（gpt-6.1-sol/high、不再派生）实现标题owner及正式RPC恢复、失败/并发回归。优先原生恢复owner，缓存缺失仅在隔离只读请求中构建；不得推进普通Turn、执行工具或改Main历史／业务状态。保护算法分支与APK原dirty，不使用完整autonomous-run。 9文件已由主会话亲审，157项相关测试及9项冻结检查通过；no-tmp为未改历史报告基线，health零阻断／零提示。隔离DeepSeek累计6请求（首2后的harness BLOB取证错误保留，修脚本后补4），有效前缀、全清缓存及cold空闲重复命名成功，当前目标/summary/Notebook完整；三次标题RPC前后45表、父缓存/工具/prefill、Main及session绑定一致，0工具执行。缺缓存时按当前原生配置重建，不宣称清缓存前后工具面恒同。产品`4bc3f2b4b802cdbeea0724d1c446a30ccbde349d`已push并从main发布，双服务实际版本及只读终验通过，保护数据/两套三库保持；Main System/工具文案未变，本次保留现有缓存。证据ignored `.hermes-dev/title-idle-20261101/`，具体发布事实见operations-log。

## 2026-11-01 · 平台切换通知精简（已上线）

用户要求取消或缩短频繁平台切换产生的目录更新。本轮首次及后续工具／权限／schema变化均仅提醒“能力可能变化，当前 N 个折叠工具，调用前重新 search/describe。”，N为当前可发现折叠工具数量；不重复目录和未变化的渠道指令，明确配置策略变化仍发送必要的新指令／撤销。root与既有历史不重写，完整快照仅留内部去重。主会话已完成40项相关回归、计数专项及footguns／lazy-deps／ruff／health检查，隔离DeepSeek最终10请求验证无详细目录仍能发现新增工具、正确计数1→2和新schema；提示仍为模型指引，实测曾先用旧参数被原生校验拒绝后纠正，不宣称硬性逐Turn发现保证。`0b43af0910e9c54b983d3c90037621163bed98c6`已从main上线，两服务／只读终验通过，按SOP清置顶缓存、保护数据一致、两套三库保持；运维事实见operations-log，算法与APK原改动保持。

## 2026-11-01 · 跨平台缓存前缀Bug验收与上线（已完成）

用户本轮明确授权核查上一会话交回的前缀修复、验收、提交并上线，由主会话托管收尾，不使用完整自主实现流程。范围为原15文件修复、固定工具桥description、实时目录／渠道策略尾system通知，以及必要的provider传输兼容补正；算法稿、06／07并行规格、APK与其它文档原有改动不纳入本轮提交。依据为同一Conversation跨平台不得改变完整system／tools／prefill及既有历史前缀；自动能力更新只追加通知，成功压缩、显式reload／清缓存与原生代码／模型路由重建沿既有边界。

主会话亲审正式接线、集成与部署；`prefix_review`独立初审后修核心，`stable_tool_bridge`固定工具桥并承担隔离DeepSeek验证，`transport_tail_review`修后继system的传输兼容，均gpt-6.1-sol/high且不再派生。原170+10项为前版证据，最终按变化定向复验及Linux实测；生产用户会话不发测试模型请求或外发消息。证据统一ignored `.hermes-dev/prefix-release-20261101/`；上线事实只记运维记录。

用户追加确认：复杂边界按上一会话原则自主收敛完成。已回读《评估压缩 Idle Note 阈值算法》原话：真实平台切换本身无问题，底层必须保证不因平台切换改变任何既有前缀，不通过统一标签、固定使用入口或算法规避来修补。凡工具／System Prompt变更，上线后必须调用既有热调试清缓存接口处理置顶会话，下次正常Turn自动按新版重建；SOP已写入现有部署文档，本轮纳入执行。

用户进一步确认Tool Search／Tool Call采用标准固定description：不嵌动态数量／目录，以可能能力类别提供语义发现入口，明确注册会变化、每个Turn使用额外工具前先search并describe当前schema再调用。顺带排查同一compaction区间内system／顶层tool schema不稳定的其它正式接线。`stable_tool_bridge`限工具桥及对应测试实施，主会话集成；原算法文档不动。独立初审发现显式禁用catalog跨平台被误判为配置变更，以及冷MCP发现交接缺口，均已修复并由主会话定向复审。

**后继最终架构（覆盖“仅泛化入口”和渠道策略冲突拒绝方案）：** 先区分不受platform／MCP／外部运行态影响的稳定能力与可变能力；初始system保留有意义的语义入口及可变目录快照，明确可变部分可能更新。后续真实变化只在正常历史尾部追加system message，保留其指令权威，不修改既有root／工具schema／已发送消息，不因换平台要求用户清缓存。固定bridge描述与动态目录快照分离；每Turn使用额外工具前重新search／describe。用户明确组织子Agent、跑必要回归和实际验证；真实模型只用DeepSeek，禁止读取或使用本机K3.1凭证；隔离合成会话验证，生产用户会话不发测试请求。main上线、置顶缓存清理及终验均已完成；本轮按最新用户确认完成托管收尾。

**当前验收：** 主会话已亲审完整接线及真实模型原件，接收固定头部／实时目录策略尾system、即时执行权限隔离、压缩及冷恢复、多warm实例和Bot Chat自动刷新修复；额外修正目录读取失败不得丢渠道策略、目录不得误列Main不可执行的Noting工具。正常路径传输622项、工具桥最终131项、本地核心111项及最终25项、Noting权限10项通过（各组有覆盖重叠，不累计冒称独立总数）；Linux分组98／131／最终25项通过。冻结十检查9项通过，唯一no-tmp来自未改历史报告且已核与初始基线同blob；最终28文件health 0阻断／0提示。

**DeepSeek证据与边界：** 隔离DeepSeek v4-pro累计24请求。初批14请求四任务结果正确但跳过发现流程，已保留失败证据并修正wrapper豁免及错误重试提示冲突；后8请求两自然任务均search→describe→call，冷建后新schema／新增工具及真实Gateway渠道策略替换通过。21／21相邻请求root/tools及旧消息按JSON对象键规范化后前缀相等，数组／内容／arguments字符串不变；冷建raw对象键序不同，不能声称原始HTTP字节全等，Provider缓存命中下降原因未证实。最终两文件目录scope／读取失败补正由定向及Linux25项覆盖；最后2请求在最终28文件SHA一致的源码上验证首次目录仅列真正额外能力、冷建目录读取异常时旧目录不丢且新策略生效，两次HTTP200、零重试。Anthropic中途system只能用Framework Message承载，不能等同原生system优先级；原生模型／Provider切换及持久化故障沿既有边界，不扩大前缀保证。

**交付状态：** 产品提交`8969e32b796fc40af16357ac9450ba05a3479e14`已push并从main发布，正式Web／Gateway实际版本一致、微信connected。01:50通过既有RPC清理Alex当前唯一置顶Conversation，三个缓存字段NULL；三库业务表、非缓存会话字段／配置／绑定保持，下一正常Turn重建。只读Notebook／排期／状态与6个HTTP资源通过；两套完整三库已核验保留，清退更旧9文件。具体时间、保护证据与恢复入口只记[运维记录](docs/operations-log.md)。算法稿及APK原dirty未纳入本轮提交。

**本轮完成后的串行交接（用户明确授权）：** 必须先完成本修复、main上线、置顶缓存清理和终验，再唤醒已有chat《评估压缩 Idle Note 阈值算法》（`01a19262-fefa-7ff3-8582-74fd94e855a1`），提醒挂目标。由该主会话自主收敛剩余规格、设计初版算法；一个子Agent并行承担Heartbeat变化、决策执行框架与接口等代码机制，避免稀释算法主会话上下文。框架优先准备，主会话完成算法测试／回放模拟后再审接线集成、构造模拟场景判断合理性。以两核4GB、现占约2GB及秒级决策为资源约束；重点是算法有效性的模拟Validation，不执行完整autonomous-run／全量Verification。全部留独立分支，不自主上线；若使用真实模型仅DeepSeek。本轮修复及发布验收现已完成，按此授权串行交接；算法仅由该会话接续，本会话不实施算法或修改算法稿。

## 2026-11-01 · 自适应维护讨论收尾（口径已归档，算法未实施）

用户要求今天结束讨论，整理已确认与待办并作一次文档提交；下次直接从**未定执行规则、损失函数与体验约束**继续，不重问已确认部分。本轮不实现算法、不调线上参数、不部署。正式讨论入口：[算法稿的收尾清单与P1–P6定义](docs/adaptive-noting-threshold-proposal.md)；产品边界同步06/07，README沿既有索引进入。

**已确认，不再重开：**

- 三决策量为Heartbeat模式m、Idle上下文阈值T、等待时间δ；以真实Main Turn结束为主要决策点。保热/业务二模式对应预配置周期，周期数字和实际next_due必须输入；业务周期可∞。Heartbeat保持独立周期，不新增Idle Heartbeat，不按普通Turn结束重置它。
- 费用以未缓存input=1、cache/output相对倍率计全部实际调用；包括Heartbeat输出、联合维护、失败/取消与恢复。热保活仍有成本，不能据此无限延长高上下文停留；已付费用不是未来可追回收益。
- 用户可通过现有主Composer取消空闲维护，Compaction消息应流式可见。普通Noting/Compaction保持共同触发、联动取消，已提交有效结果保留；不改为串行等待，不新增独立频繁Noting，Force是保留的唯一提前独立例外。
- 不新增反馈按钮。Compaction未结束时的主动取消为反馈；真实发送因它被拒绝、之后未取消且完成，记本次容忍阻挡，窗口为首次有效受阻发送→Compaction结束。同一operation去重、先受阻后取消归取消，失败/未结算另列；无操作不推断满意或无碰撞。
- “独立频繁整理更贵、收益有限”是上一轮Noting改版/零期文档与设计白板阶段甚至更早的认识，本轮沿用，不能写成本轮新发现。算法研究与provider参数研究分层；前缀不变是代码机制责任，不进入预测变量。

**下次按此顺序继续，仅讨论未定部分：**

| 顺序 | 待决问题 | 已有入口/限制 |
|---|---|---|
| 1 执行规则 | 模式切换保留何种锚点，旧计时如何处理；∞/无锚点转有限首次due；已领取任务与切换结算顺序 | 算法稿E1–E7是建议，不是已确认规则；不反复调用set重置计数 |
| 2 计划生命周期 | δ是否明确为Main结束后的剩余等待，T/δ合法表示及上下界；计划替换/失效、维护结束刷新、重启、同到期优先级 | “有效Idle压缩先于Heartbeat”仍待确认；不凭线程竞速冻结产品规则 |
| 3 损失与约束 | 共同比较窗口及末态责任；碰撞/阻塞、业务时效、质量与高上下文停留如何形成可计算约束或惩罚 | 成本单位、反馈事件已定；容忍值、权重与质量代理未定，不擅自折成token或设零 |
| 4 后续模型 | 上述冻结后再选预测/搜索与时序回放；以真实时间/来源分析，避免等间隔假设与未来泄漏 | 尚未证明动态策略优于稳健固定策略；维护受理/执行/完成均有不确定性和时延 |

**另行保留，不抢占下次主线：** K3.1缓存稳定性/TTL与保热周期；Heartbeat真实业务有效性及Instant Reminder覆盖，据此选择业务周期（可∞）；采集实际维护/阻塞历时和取消结果，TPS仅辅助；验证Force所依据的Noting上下文余量是否确实高于Compaction；Compaction流式内容及事件接线、Gateway排队/Stop边界核实（终端/Git Bash交互不纳入）。参数没有新定值，不把29/30分钟、900秒等候选当授权配置。

**已有取证边界：** 冷启/压缩交互图及统计完成，算法未回测/实施。10/30约330K平台12次冷启首请求API等价51.318元，占周已记录等价19.21%；映射已用79.9%约15.35整周百分点只属条件估计，不是精确套餐扣额。Idle已核10/28 00:24:50关闭，保留96K/500秒、Heartbeat两小时；不是本轮新选择。最长较可靠热间隔31分05秒不保证TTL；29–30分钟15同平台近完整/2跨平台部分样本不能当独立存活概率。压缩成功日志11条约7.1–14.6分钟，中位9.1，旧Idle联合约14–16分钟，不当完整占用分布；超时1000秒不保证联合总耗时上限。详细数字、限定与证据目录统一在算法稿，原件仅在ignored `.hermes-dev/adaptive-audit-20261031/`，不纳入提交。

## 2026-10-31 · 跨平台缓存前缀Bug（前版交接，已由本轮扩查修订）

用户明确授权一个子Agent本地修复：同一Conversation不因UI/微信/Reminder/Heartbeat平台切换改变完整system、prefill、工具定义/Tool Search目录或已有历史前缀；平台身份和真实投递保留。规格见07本日补充，不含部署授权。

已定位恢复工具pin后Secretary按当前平台raw目录重建bridge，以及Gateway追加平台相关ephemeral system；root hash相同不等于完整请求前缀相同。历史缺完整HTTP原件，不能断言13312精确边界或唯一原因。`platform_prefix_fix`（gpt-6.1-sol/high，不再派生）已交15文件修复与170+10项测试报告，**代码仍待主会话亲审/验收，不纳入本次文档提交**。需核旧pin首次变化、渠道策略冲突拒绝、claim/恢复及原生回归；no-tmp失败报告称已在HEAD复现，须核证，不冒称全绿。报告、原始前缀调查及验证日志在上述ignored目录；修复验收与Provider缓存存活研究分开。

## 2026-10-31 · D方案与键盘弹飞修复（前版记录，已由11月1日版本替代）

用户明确否定revision2效果，提供15.66秒真机录像：约8.7–9.1秒键盘唤出时Composer与顶栏过度上移再回落，9.8秒附近收起亦存在瞬时高度交接；状态框仍显细描边／嵌套输入栏，不符合期望。上轮隐藏浏览器模拟不覆盖系统焦点避让，不再作为真机问题已解决的证据。继续由主会话亲自处理，不派sub，不部署。

样式需同时核灰底、描边、圆角和比例，不能只改留白。已复核b33e428之前Notice约44px单行高度、12px圆角、上下12px内边距；暗色灰底#2e2b29／边框#4f4b47。用户在四候选对照后最终明确采用D：26px灰色填充、无描边、胶囊圆角；暗色背景#47433f／文字#c1b9b2，保留12px字号、文字靠左、框内左右16px及框外左右12px间距。此选择覆盖此前短暂选择的历史描边26px方案，已落入产品样式。动画排查系统窗口避让、根文档滚动与网页合成位移叠加，原录像关键帧保留于前端ignored `.archive/composer-motion-20261031/revision3/`。保持真实恢复资格、草稿、同页恢复及安全区契约。

已修复：API30+改为SOFT_INPUT_ADJUST_NOTHING，避免系统ViewRoot焦点平移与既有Insets owner叠加；API28兼容入口保留adjustResize。APK标记下html／body禁止根滚动、#root固定于窗口，普通网页不变。主会话隐藏IAB反证旧根层可额外滚动300px／顶栏−300px；修复后同请求scrollY=0／顶栏0，提前缩窗、开合全帧无根位移且Composer不越终点，内部时间线scrollTop=40仍可用，草稿保持。原生10项及Kotlin编译通过。四候选对照及用户最终D确认已落档。实际产品组件复验：0↔38px恢复区／0↔26px胶囊连续伸缩，暗色颜色／无描边／16px水平内边距与D预览一致；380×844隐藏IAB中提前缩窗并持续请求根滚动，键盘与恢复状态同时变化时scrollY及顶栏位置全程0，Composer底边在544↔844范围内，背景缓冲恒定299×601，草稿保持。深浅主题及减少动态效果已核；当前前端41项通过、原生10项通过，TS源码与上轮健康证据一致，typecheck／release构建通过。不冒称真实Android复验通过。

交付为前端ignored `.archive/composer-motion-20261031/revision3/Hermes-Secretary-0.1.10-composer-D-arm64.apk`：0.1.10／1010、32130749字节，SHA256 `7cbe8476b451c3cd6ed9f85982886448da366367087b9fffcfd7f2cc004897b1`。原签名／v2／CRC／16KB／439资源和交付副本一致性通过；本轮生成dist/.DS_Store与此前同样移至证据目录，原未跟踪文件保持，严格校验不放宽。最终深浅截图、D-combined-motion逐帧数据、根层反证、回归／构建日志、源码manifest与收据均在revision3。临时隐藏验证页及开发服务已清理；两仓修改未提交／未push、无部署或真机安装，旧APK保留作历史证据，当前交付仅D方案包。

## 2026-10-31 · 键盘动画卡顿与状态框二次修订（前版记录，见上节真机问题反馈）

用户真机反馈前版键盘动画极卡，明确禁止派sub；本次修订全部由主会话独立修复、验证与构建。最新口径覆盖前版内容宽度／居中小框：提示顶满内宽但左右留间距，可用与Composer协调的胶囊；文字靠左，灰框自身从固定底边展开高度、Composer同步上移，反向同步折叠，不接受框先淡出再降Composer。保持12px／20px，同一Restoring或Retrying状态最多并列三个真实等待对象，3秒轮播及省略号保留。用户最后要求整个过程无跳变／闪动，作为目标；未取得真实Android帧率证据，不能宣称真机已完全解决。

已移除IME progress逐帧updatePadding：原生只发送起止／取消，网页用系统曲线的合成位移／裁剪、边界调整真实高度；反向捕获当前视觉位置，过期回调忽略，原生结束与实际viewport同时到位才交还布局。查出并修复末帧矮屏规则缩短输入框、新聊天标题改排、短正文按全键盘距离移动后回弹的问题；正文按自然内容高度预测终值，提示／流式尺寸变化时更新目标；键盘期间固定背景表面尺寸，按表面而非外层viewport分配WebGL缓冲。恢复提示只改变展示，真实恢复资格不延迟。

验证：前期相关7文件130项通过，最后增量5文件41项通过（IME9／恢复4／阅读22／背景6），typecheck、生产build及冻结TS健康基线比较通过；原生IME9通过，其余原生Viewport9／ForegroundRefresh36／SystemBarTheme1有效证据复用，Kotlin及release编译通过。API28兼容序列与API35 Activity接线由Robolectric验证，非真实设备。主会话隐藏IAB390×844受控采样覆盖新聊天、短正文、同时开合、反向及过期end：Composer终点高度一致，正文终点无额外回弹，草稿保留；最终背景缓冲开合全程306×601无重分配。恢复区0↔32px、框体展开20px／字号12px／宽340px／左右各13px，底边恒定，文字靠左，无淡出后移动。构建资源更新触发的开发页重载样本未采纳，最终连续采样已重取。

签名交付APK为前端ignored `.archive/composer-motion-20261031/revision2/Hermes-Secretary-0.1.10-composer-motion-v2-arm64.apk`，版本0.1.10／1010、32130505字节、SHA256 `040bfcb53bea4443ef26f56708cea3bb144b1247d9aa418586e38f4a3855a1f8`；原证书／v2／CRC／16KB／439资源／交付副本一致性全通过。首次末端校验仅发现构建生成dist/.DS_Store，多余项已移至本轮证据目录，原五份未跟踪文件保留，校验未放宽。日志、逐帧JSON、深色预览、源码SHA及校验收据在同目录；运维记录列出本地产物。两仓修改未提交／未push，无云部署、设备安装或真实Android流畅度验收。前版APK保留为历史版本。

## 2026-10-31 · APK键盘与Composer恢复提示过渡（前版记录，已由上节替代）

用户要求：APK虚拟键盘唤出／收起平滑衔接，消除瞬时跳变；Composer下方恢复状态出现／消失同样平滑，恢复为底边居中小灰框，保留现有字号和单行高度，整体比旧版更紧凑。范围仅表现层，不改恢复资格、模板、请求或输入行为。依据06对应补充；前端基线6c132a4；两仓既有修改保留。

用户补充连接提示样式须参考提交历史：已核b33e428之前的中性Notice灰底／边框／圆角；保留当前12px字号、20px高度，按本次明确要求内容宽度居中。编排：主会话处理恢复提示、规格同步、集成亲审与定向验证；独立实现Agent仅处理Android IME Insets动画接线及必要验证，不再派生。显示保护保持，仅自建隐藏IAB可做界面验证；真实Android键盘动画尚未验，不用桌面模拟冒称真机通过。本轮未获新增部署授权。

已实现并亲审：Android单一IME padding owner在prepare后暂缓最终Insets、按progress真实高度更新，结束／取消收敛，旧动画及销毁后回调不覆盖；原生缩放／系统栏／恢复机制保持。恢复提示常驻可收缩容器，180ms高度／透明度过渡，消失时仅保留无障碍隐藏的退出视觉，操作资格即时恢复。前端5文件117项、types、生产build与冻结TS度量（无新增／恶化超限）通过；原生IME10＋Viewport9＋ForegroundRefresh36＋SystemBarTheme1共56项及Kotlin编译通过。API28为AndroidX独立View兼容帧验证，API35为正式Activity分发，不冒称真机。

root自建隐藏IAB390×844实测：恢复区0↔32px连续中间帧，灰框20px／字体12px／宽约155px、居中偏差小于0.01px；开合与快速反转归零，草稿保持，退出动画未结束Send已可用；深浅主题和减少动态效果通过。期间Vite热更新干扰的首次收起样本未采纳，最终同document连续样本已重取。证据在前端ignored `.archive/composer-motion-20261031/`（browser-frames、两主题截图、TS度量、原生测试及构建日志）。产品修改尚未提交／部署；本轮不改变线上版本。

原签名本地APK已完成：同目录`Hermes-Secretary-0.1.10-composer-motion-arm64.apk`，0.1.10／1010、32128253字节、SHA256 `de1558650339e4d28fd7305bab6eaac00f5de5dcf7e496c68ee3b159cf093d8d`；原证书／v2／ZIP CRC／16KB／439前端资源与交付副本全部通过，收据同名`.verification.json`。首次构建末端校验误用旧系统Python，改用主仓官方PM Python3.14后发现dist额外`.DS_Store`；仅将该生成杂项移到本轮证据目录保留，仓库原有五份未跟踪`.DS_Store`均保持，原校验规则不变。实际资源零缺失／零差异；无真实Android设备验收，不冒称真机流畅度通过。临时隐藏页面及开发服务已清理。

## 2026-10-31 · 证据集描述与Main强制回查（实施、上线及清理完成）

用户授权按定稿规格／Prompt实施两项调优、验证后上线，随后要求清理所有本仓worktree、整合分支并使原目录回归main。两项调优已提交d6c0088，已授权的遗留manual Noting调试RPC窄接收a51a0bf；于2026-10-31T10:09:58+08:00正式发布bf28ab5，receipt verified。Web／Gateway实际同源active、微信connected；三库业务数据、配置／凭据／绑定及两套前端静态均保持，认证只读RPC与HTTP六资源核验通过，两套完整三库备份已保留并清退更旧备份。

source_description与UID共同维护、provenance_descriptions逐槽投影；描述仅含本组消息，与条目description互补，为Main提供证据历史概括以维护一致性。Main按定稿MUST先核历史依据，已有充分原文无需重复读，有相关引用先Read，不足才Meta／Search，失败保持未知。旧组缺描述只读为null，不回填、不转换生产历史或重跑旧Noting。新版Prompt／Schema沿正常Main构造／恢复边界生效，不热改运行中前缀。用户后续明确不补旧Noting，并要求用已有热调试接口清缓存；已调用conversation.context_cache_clear返回cleared，目标三个持久缓存字段均NULL，下一正常Turn重建。目标13份历史Snapshot及23张业务表前后保持，无模型／Noting启动；见operations-log顶部。

验证完成：D1最终151项／Candidate62项／权限86项等、D2共33项、遗留RPC41项、冻结十检查、真实Linux7文件111项；独立Verification及Validation产品门禁通过，独立6完整旅程6/0，发布与清树事实补核见本轮两报告。用户“不用真实模型验证”后无新增真实调用；此前3个隔离合成样本／6请求原件保留，纠正样本漏Conversation Ref不作Prompt失败证据。生产测试模型、manual Noting启动及外发均0；受控SDK不证明未来模型必然服从。

全部六个附加实体工作树已保全后移除，另清失效登记；13个本地功能分支经ancestor或补丁／blob等价核对后删除，非ancestor原件另有bundle。原目录`/Users/edgar/code/hermes-secretary`只剩唯一main工作树，原Python实体、stash、远端功能引用及独立前端仓库保持；只保留本地main和纯镜像hermes-upstream。旧dirty和证据归档在ignored `.hermes-dev/worktree-retained-20261031/`，本轮完整证据在`.hermes-dev/evidence-recovery-20261031/`。本轮索引、两报告及交付简报见`.autonomous/20261031-evidence-recovery/`，细节见operations-log。用户未要求自主实现流程，系Agent自行选择；后续按用户要求完成已展开计划，不倒称最初由用户要求自主实现。

## 2026-10-31 · Notebook连续性调查结论（调优已进入本轮）

原始原因消息及其UID索引当时都可回查；条目首次创建已遗漏原因，压缩后事实缺失，Main未核实即起草，用户纠正后才5次Search＋1次Read恢复。Noting当时读到完整用户原话且正常提交，不能归为字段截断或存储丢失；Main已有索引无逐组描述，恢复触发依赖主观不足判断，两道保护同时失效。只读原件保留于原根ignored `.hermes-dev/alex-draft-investigation-20261031/`；此次实施两调优，不改写旧组或旧模型轨迹。其它旧看板的已完成运维／历史讨论以当前主干及operations-log、07为准，清理时完整原件另留私有归档，不用旧“未实施”状态覆盖后继上线事实。

## 2026-10-31 · Force 后 Main 完成交接故障（已完成并发布）

用户授权立即救援、随后自主修复、前后端重新部署、新APK和子Agent。00:42只重启空闲Web完成救援；本轮产品BE `ef9051f`／FE `6c132a4`已于01:24:38+08正式main发布verified，两实际服务同源active、微信connected。原故障尾部13441／13442完整保留；439静态及HTTP六资源、保护表／配置／绑定、两套三库已核。0.1.10／1010原签名APK已交Downloads，SHA4f3c795f…bb063，32127165字节，439内置资源严格一致。运维细节统一见operations-log。

前后端都有问题：Force FM后追加污染共享结果的尾部推断，使真实完成被拒；随后Pending未采用却误报读取成功，使Send仍锁。现在用原生final UID封闭Main回执，并让未采用Pending沿既有失败／重试收敛；完整Framework历史保留，不移动Force接缝、不放宽恢复或缓存权限。上次回归手造成功回执漏过真实Web收尾，本轮真入口反例改前失败、修后通过。

主会话已亲审，BE177项＋最终4／6、冻结十检查；FE273项、types／TS度量通过。独立Verification产品通过；独立Validation7适用场景通过、0失败，含真实隐藏IAB暖冷恢复、child活动时后继Send／Compact、断网期间child完成和Pending失败自动重试。最终发布及交付事实已独立补核，Verification12条全部符合／0缺口；本轮目标完成，最终简报已落盘。本轮索引／两报告／最终简报见`.autonomous/20261031-force-completion/`。原自主轮真机／外部验收边界独立保留，不冒称整个旧轮完成。两工作区原dirty及用户.DS_Store未动。

## 自主口径收敛 · 待用户追认

- **Agent自主收敛／待追认：中文粗体兼容的inline兄弟范围。** 原空白：既有中文标点邻接`**`兼容仅能处理单text节点；合法链接／inline code把同一显示范围切开后，末端无空格紧接中文的星号仍为字面。决定：同段／标题／表格格内，保原source双星／转义／CJK外侧与标点内侧证明，允许兼容span包含完整已解析link／inlineCode／inlineMath兄弟；内部payload／地址不变，不在其中寻找星号，不跨换行／block／模糊嵌套。理由：消除AST分割造成的兼容不一致。影响：扩展现有非标准CommonMark的中文粗体兼容，不冒称标准本来支持或原截图同型回归；源消息／Copy／安全协议保持。已实施于ccd4cfa并上线，111项及实际N30／Copy复验通过，待用户追认，可局部回退。

- **Agent自主收敛／待追认：混合压缩载体的读取。** 原空白：一个native UID可同时承载压缩摘要与真人消息，而用户要求辅助开关能读取Compression且Get Meta仍仅四字段。决定：默认保留原真人视图；显式辅助允许同UID的system摘要视图，Get Meta／Search按语义部分分别返回，anchored Read允许现有roles参数选部分，默认锚点优先原非压缩部分；同UID同role的system内容合并为一个视图；不造UID、不放开Full／隐藏内容。理由：使明确要求在native混合载体下可操作。影响：Read新增可选roles适用位置，同UID可有不同语义投影。已实现，201项History接受测试及56项原生路径通过；独立Verification／Validation已通过，已上线；不改变Message Identity或Notebook新证据准入。
- **Agent自主收敛／待追认：Candidate同Task来源形式切换。** 原空白：旧合法direct→refs操作与新旧Task节点不可删约束如何同时成立。决定：仅尚未提交且唯一节点属于本Task时，允许显式清空当前工作槽并切为合法refs；任何旧Task直接节点仍禁止删改。理由：继承原来源二选一操作并保持旧节点约束。影响：当前Task工作态边界，无迁移／旧节点特权。已实现，正式工具／恢复／原子失败98项通过；独立Verification／Validation已通过，已上线。

## 上一轮自主目标状态：外部验收证据阻塞（本次故障另立目标）

产品实施、两仓主干发布和0.1.9-5f APK交付均完成；最后本地验收／文档已提交ee6ca63并自动push。连续三个目标turn均确认同一外部边界，最新只读核工作区clean、报告SHA及15个partial保持，原QA确认无必须新增的最小本地路径。自主目标当前标记blocked，不是用户暂停，也不是整轮已完成；不继续空转本地验证或开启第四轮。

剩余R02／31／51–59／62需要真实Android WebView初始入口、触摸／IME与系统前后台；R18／60／61需要真实认证／合法登录恢复（R61亦含APK前置）。微信真实送达也无测试外发授权。现行显示保护只许root自建隐藏IAB，不能改用用户页面／桌面／外部浏览器来填证。恢复条件：取得这些真实外部结果，或用户明确提供相应设备／操作权限并要求继续；仅按原第三轮报告补已有缺口，不重跑有效套件，不把外部未验改为N/A。线上88ed／5f正常，APK保持可用。

## 2026-10-30 · 最后维护恢复修复收口

主会话已亲审三个产品文件及正式原生回归：手动压缩借用busy不再清除已结算输出快照；同一DB snapshot仅为显式旧row引用比较唯一当前代表的完整显示／终态事实，所有已结算回执与committed帧共用内部证明，活动Turn来源保持严格。156项受影响回归及冻结十检查通过；独立第三轮R3-V09与实际T11–15原失败document复验已关闭。88ed1ca于21:13:41+08从main正式发布并verified，两实际服务同源／微信connected；前端5f及原签名0.1.9 APK保持。439文件／HTTP6、保护数据／配置／绑定通过，两套三库保持。当前独立Validation50限定通过／15部分／0失败／1不适用；最后键盘、连续动画与历史预览回执均已补判，当前授权范围内无必须新增的本地路径；设备／真实认证边界保留，整轮未冒签关闭。


同第三轮U/O/C共60份唯一label原件及真实六库恢复已获原独立QA接收：Usage真零／模型切换、Slash候选／Tab／冷目录、Orb全局local开关／真实unknown／跨Profile、三Blob冷恢复、可见图片404／离屏0重下、首必要History503、冷Pending／双审批完整Diff均补齐对应浏览器范围。两套真实保留备份六库已隔离恢复并核14原生语义样本，临时副本已清。剩余主要是物理Android／真实登录恢复／未授权外发边界；不能用50项通过覆盖这些限制。混合文件＋图片的Attached Context／标签重复显示已证attachments/content与冻结前c39086c逐Gitblob相同，登记为既存观察，不冒称本轮回归或已修。

## 2026-10-27 · 增量同步与免刷新恢复（最终集成与第三轮收敛）

**T10维护恢复反例已关闭并上线。** 根因与88ed修复／156项回归／独立补审及T11–15实际同document复验见顶部；原T7–T10失败保留，当前不再处于待修或未上线状态。

**自主接续补验：** 上轮草稿修复／发布属实际进展。本次沿原第三轮R13／R16补准旧分页在owner切换后才完成的成功／失败与详情迟到；原V10未命中不改写。A经正式Rewind后仅10条，使用同夹具B的长历史作为慢请求owner、实际切回A，保持同一正式代码路径与精确Profile隔离；只改隔离准备数据及取证，不改产品／重新部署／扩大外发权限。沿原独立QA补判，不新开第四轮。

**OBS-READING-CAS-01已窄修并正式交付，原第三轮补收：** 原L6已展开Thinking405／row408、scroll7979.5；同UID／row／content不变的正式CAS仅更新reasoning后，L7详情自动取到新全文，但普通sessions.changed将idle阅读强制跳到320585。原QA已按06:356／538及P08确认普通在线失效不应夺取仍存活的阅读anchor；不能套用真实重连前缀破坏豁免。root限定同一DOM精确anchor匹配helper：普通提交有存活阅读候选则保持原owner／20秒计时；真正全候选退役、U25首冷启、真实重连及Send受理规则保持。FE5f974b3已完成root亲审、79项定向证据、独立机制审与实际Y0–Y7原旅程复验；普通CAS后旧Thinking全文更新且scroll7979.5保持，冷启按U25到底／完整详情复用、600条阅读与IDB500身份实证齐。正式5f静态及原签名APK均已交付；原反例和13db历史保留，两门禁最终补收不冒整轮完成。

**10月30日草稿补修已交付且定向独立关闭：** V33的Rewind受理后冷启复活旧Slash草稿已修于FE13db132；canonical成功写入才清退legacy，较新空草稿参与仲裁，失败回退映射可重试，受理消费推进事实时间。真实IDB／正式Controller基线17红、最终62项及类型／冻结健康通过，独立机制审接收；实际D1–10验证退出Reply、未提交编辑冷启、受理后暖／冷保持空、391秒无复活／无重放。已静态上线及交付原签名13db APK，独立QA与Verifier均已关闭R3-V07并核最终交付；原V33失败、D0环境失误和首次静态包拒绝全部保留，不开启第四轮。

**后继静态5f交付时点（后端其后已升级88ed，见顶部）：** 当时BE main00f0b28，FE5f974b3正式verified上线，439资源／HTTP六入口一致，双服务active／微信connected、0重启／DB写。Downloads新0.1.9 APK为5f974b3，32127841字节、SHA81a121d1537991534cd844d4060e29955b00d3121694a10702847069bdb28867，原严格签名／16KB／资源核验通过并已给用户链接。独立Verifier已接收5f正式CAS及交付证据并关闭R3-V08，报告SHA61936145…；QA继续原第三轮用户结果补判，未签整体完成。

**前版13db交付时点：** BE main `00f0b2879e0dede672cee0bb06989d9a032eb937`、FE `13db1320e672e613737f20900abb7450bff25858` 均已正式 verified 上线；最终原签名0.1.9 APK已交 Downloads 并给链接，SHA `051b0231964d7762a3bc89b7ed5544fc1751ccffea9d5bd365db07f8e7161081`、32127749字节。静态后继更新未重启服务／写库，两套完整三库仍保留。前三个动态缺陷和首次Socket失败恢复的有效证据保持；D组独立补判后为7项限定通过／58项部分通过／0项当前失败／1项不适用，整场均有执行记录不代表全部子分支已齐，尚未签整轮完成。外部动作／设备限制分记。下文旧版本与待验表述是各包原时点记录，当前实际状态以本段、唯一plan及operations顶部为准。

**中断partial补修已关闭并发布：** 独立动态N5／root P7证实原生中断partial直接append新UID，原stream作为terminal residual重复可见。root限定仅在明确保存当前partial的接缝绑定sameTurn／request／writer候选原身份，由原flush与terminal归账；不按同文去重、不改旧库／正文／权限。00f0b28实现、同轮独立影响审及Z段实际UI复验均已接收并上线。原Interrupt操作／Steer可见交接及Approval恢复已取得独立限定通过，原始失败保留。

**正式原生补证的新接线整改：** 完整工具callbacks证实final footer晚于首次持久化导致idle恢复证明不全，以及active恢复裁剪丢失typed工具owner依赖导致Diff不可重建；root分别限定首次final flush／running snapshot依赖闭包修复，不放宽receipt或权限。两项已亲审提交4be80c7并自动push；最终两原生ASGI场景2项通过、冻结十检查及health 0／0通过，同次第三轮影响审与实际复验继续，详plan当前表。原legacy夹具缺事实与这两处真实产品反例明确分开。

**历史验收整改（已由后继Z/T实际路径关闭）：VAL-R25-01。** 独立动态验收发现Interrupt跨Turn复用上一Turn operation导致unknown；原73a真实失败已保，FE ce69fbe已按严格同Turn身份窄修提交／自动push，11项及types／冻结度量通过，同次第三轮源码影响补审认可；待正式原生旅程复验再更新前端／APK。15:35:43已上线BE d172／FE73及原签名APK交付事实保持，不声称整体完成。

**当前完成条件（U22／U23）：** 持续自主执行；第一轮之后Verification与Validation各最多再两次正式全轮复审／复验，第三轮内完成两仓main集成、正式Alex上线和原签名0.1.9 APK交付。次数上限不豁免缺陷或证据缺口，不开第四轮。用户U24已明确将Verification改回本地，第二轮集成锁定后派全新上下文6.1 sol/high全范围独立审查；开发定向测试／主会话亲审不冒充独立门禁。生产模型和真实微信测试外发不在授权内。

**U31历史安排（已被U32覆盖）：** 紧急发布在切换前因计划文件上传／读取路径不一致退出，正式Alex仍main3426c0f、两服务active，没有停服／换源／换静态／生产库写入。用户随后明确“不着急了…先不用…临时的东西…赶紧继续，尽快收敛”，停止临时发布，回到最终集成→第三轮Verification→正式Validation→统一上线；现有APK先继续使用，不主动要求更新。最终上线授权及三轮上限保留。

**U32实际完成：** 用户15:21:32+08明确20分钟内上线并给新APK；正式Alex于15:35:43 verified（截止15:41:32），BE main d172250／FE73a，Web／Gateway实际版本均已核、active且微信connected。原签名0.1.9新包已交Downloads并给链接。第三轮168条产品Verification与交付事实已接收，R3-V01正式链及唯一真实Main消费关闭；独立66场景Validation继续，未将上线／签名包当作动态验收或真机通过。发布／备份／协议证据详operations-log。

唯一计划／索引在[本轮目录](.autonomous/20261027-incremental-sync/plan.md)。原始需求U01–U30、缓存D01–D18、表现S01–S20和操作P01–P11已落档。保持原产品／视觉／操作资格，主目标仍是500条消息与完整已取详情缓存、游标同步、SPA／APK无需刷新恢复，不为填缓存预读或重新发起写操作。

| 工作包 | 当前实际状态／交接 |
|---|---|
| 原独立修复及主体增量机制 | 已提交／push、合入主干并随d172／73a正式上线；独立产品Verification通过，动态验收继续 |
| U18 Steer／U19 Approval／冷Slash目录竞态 | 已集成并随当前5f上线；原真实交接／审批及冷目录代表已补收，本批原生候选Tab、unsupported拒绝、冷Pending唯一恢复／撤回、冷双审批完整Diff与明确Deny推进已获原QA接收 |
| F03/F04缓存 | 前端0ea002e已亲审提交：完整详情字段保留，窗口／详情／已核验前缀合计500身份预算，证明失效时仅退役selector；95项及真实IDB证据，见reports/r2-cache.md |
| F05/F06后端增量 | 918efda主体已亲审、集成并上线：原生Thinking合法尾追加、正式CAS改文通知；132项及22项原证据，正式App单条delta/CAS阅读保持与500身份缓存已有原件 |
| F01/F02前端恢复 | 已整包交回并亲审，166项＋末次14项通过；复杂度窄拆分完成且无增长，前端8313cf2已提交；见reports/r2-frontend-recovery.md |
| F08微信逐消息发送 | 已亲审提交后端a5018ff；final持久UID后立即沿既有FIFO投递、尾部成功回执去重；150项及最后47项影响复测，不真实外发；见reports/r2-weixin.md |
| U20／F07／E02联合Noting | 已随主干上线，当前BE88ed；普通手动／Idle／原生auto联合触发取消、已提交保留，Force仅Turn结束不可取消并封区间，特殊替代审计透明，Note独立四时点原FM投递。独立V及R34–40正式机制／真实消费代表已补收，不能冒全部真机／模型组合 |
| E01/E03与动态体验 | D07勘误已由独立Verifier接收，仅约束已有入口Desktop，Web/APK不新增索引UI；当前App流量／切点／阅读／缓存与菜单恢复的实际代表已补，独立Validation剩余边界按原报告 |
| 整轮门禁 | 第二轮不通过历史保留；第三轮168条产品及已授权发布交付Verification通过，R2-V01与R3-V01独立关闭。66场景Validation由独立验收者判断、root隐藏IAB远程手执行中；夹具页面关闭后预置owner回收导致环境失效，原失败保留、仅修ignored接线后复验 |
| U25冷启动视口 | 用户已确认新document首次真实历史提交后一次立刻到底，加载期用户滚动不阻止；cold_start_viewport已交回，root审查正式commit/ack接线后接收并提交ba7decd；5文件115项、types与冻结健康通过，同页规则保持 |
| Main notebook_show线上反馈 | 用户转述Main自述无工具且只限Noting，既定只读Main资格不变；只读核线上3426持久工具表有Show且同会话23:42实际调用成功；争议请求wire缺失，缺工具未确证。新候选17项正式Main工具接线通过；用户明确停止深挖旧逻辑，继续以新链路实际注入／读取为准，未改Prompt或扩大旧版追查 |
| Noting误恢复补修 | 独立Secretary token／child history token／scope事件消费已随主干上线，并经原生21／26／9／18及FE12原证据核实；本批实际A后台任务而B idle、切A running、失败回idle均无Main恢复；88ed再关闭维护误清快照／物理换代拒绝 |
| U30 Markdown链接误识别 | 已集成当前5f并上线／打包；裸链接中文边界、合法Unicode、代码／数学及原消息复制、协议安全由M1–M12实际流／冷恢复与独立QA R63–66补收，无外链访问／真实授权码保存 |
| K04内容取证／R3-V01 | 一次真实Noting12HTTP正常提交与Main Show成功；保留错误reason原件。d172正式FM消费指导经6项真实链与唯一Main请求证据独立关闭，四极性忠实、0工具／新Noting，不改Task／Schema；源／raw前后已核 |
| U29真机视觉反馈 | 用户已确认起手正常，但要求圈旋转放慢、阈值补明显高光／光晕；FE6628a2e已提交：旋转540→240度、等待700→1300ms、阈值主题高光／光晕；32项与types通过，root隐藏IAB浅深主题／回拖已核，不改已正常手势时序／行程／区域，新视觉真机反馈待 |
| U28真机触摸起手失败 | 用户e545实测标题栏完全无圆盘；root确认子lost capture冒泡误cancel，FE d1a53cf已亲审提交，31项及正式wrapper/StrictMode/types/健康通过。已交付`/Users/edgar/Downloads/Hermes-Secretary-0.1.9-preview-d1a53cf-arm64.apk`：32123717字节、SHAfb651a0bbeae025776016d58fa594b68aa2f0fb16faeaf88aa6b3983ef564a2d，439资源/原签名/ZIP/16KB/1009已核；用户随后明确反馈“之前你给我的第2次APK已经可以正常下拉刷新了”，d1a53cf预览实际顶栏起手故障已获真机关闭；其余场景不据此代签 |
| U26顶栏手动刷新预览 | APK only Chrome式圆盘阻尼／cap／阈值释放已集成当前5f APK，普通Web关闭；页面背景静止，真实mouse和原native边界证据保持，d1起手获用户真机关闭，其余当前真机动作／视觉不扩大签通过 |
| C-R5／C-R6 显式恢复Note资格 | Snapshot来源／operation证明、branch去父关联、恢复lease接手及终态补检查已集成上线；7文件源SHA、62项及十检查由root亲审并与原第三轮正式机制补收，不再标待集成 |
| U27 APK引导失败同页恢复 | e545接线已集成当前5f APK：初始临时引导失败承接内置SPA，原生自动reload取消；native13／TS35原证据及实际pending503／首次WS失败／慢凭据／首必要History503同doc恢复分层保持；真实APK首次进程到SPA现场仍未验 |
| 发布／APK | 后端88ed1ca／前端5f已正式verified；439资源／HTTP6、保护数据／配置／绑定通过，两套三库保持。原签名0.1.9-5f APK已交Downloads／链接；最后维护恢复缺陷独立审查和实际同doc复验关闭，整体验收边界保留 |

前后端实施目录分别为`/Users/edgar/code/hermes-secretary-incremental-sync`与`/Users/edgar/code/hermes-secretary-web`，同名`codex/incremental-sync-20261027`分支。C、原恢复包及U25/U26均已亲审提交；两仓main历史已按SOP纳入候选（BE2dc4398／FEbc02d01），合并产品tree零增量，不触碰其它main工作区dirty。validation_round2已补完并过目56场景，release_preflight及27项本地发布保护演练已完成。隐藏IAB已恢复；root开发联调确认正式CAS改文→watcher→App同document自动delta更新1条，草稿保留，不把该开发证据冒称独立验收通过。子Agent6.1 sol/high、不再派生、不流水账；主会话负责方案、亲审、接线、正式门禁与发布。

保护原main工作区的Noting调试／生成协议／07／presentation等他人dirty。新状态表必须兼容正式旧库，仅加Secretary自有伴随表／读取视图，不重建生产数据库。冻结检查不增删放宽；no-tmp旧报告七处仅加既有允许的历史取证说明，原行原结论保留，原字节与SHA已在ignored存档；单项扫描通过，未改检查规则／阈值／baseline；de45版本已统一执行冻结十项且70文件health 0／0，后继整改须按影响补查。旧Timeline七项失败在原91ad同样存在，不能据此替代部署基线或当前用户体验判断。Android完整生命周期与真实微信送达未完整实测；用户已确认d1顶栏起手正常，不能扩大为新视觉及全部生命周期通过；包校验／受控adapter不冒称实机或真实外发。

U20详口径见07顶部及plan接线设计；旧“先Noting再压缩／FM结算后才终态”已被替换。U17旧模糊片段保持懒取，新Turn沿原生source精确主动取Thinking，不设逐Thinking游标。用户确认与原始云端报告保留索引，不改写旧审查时点结论。界面验收只许自建隐藏IAB，不动用户浏览器／桌面。

## 2026-10-27 · Noting来源链／History调优（已上线）

用户已确认全部语义和精简Prompt，并明确“开始改吧。改完，测好，上线”。轮次`.autonomous/20261027-noting-provenance-history/`，工作区`/Users/edgar/code/hermes-secretary-noting-chain`，分支`codex/noting-provenance-history-20261027`，基于main `d1de4db49b`；为隔离旧目录及main调试dirty新建，原修改保持。

范围：Get Meta、统一语义role／默认辅助消息排除、闭区间、工具参数及结果展示；每条目每Task一个不可改旧节点的来源链、runtime只读对应Evidence time；已审Noting／History Prompt。独立History／Notebook／Prompt实现包，主会话亲审集成、真实模型证据、独立Verification→Validation通过后已统一部署。仅人工转换Alex仍用的唯一置顶Conversation的Notebook，保留消息、排期、绑定、其它Profile／Conversation和前端；不建通用迁移层。正式机`ssh alex`，上线沿既有SOP／发布工具，备份最多两套三库。

冻结02d55fdb，产品3426c0f已合入origin/main并在正式Alex保持main上线；两服务实际版本、只读RPC、目标Notebook与保护数据／配置／绑定／静态均已验真。独立Verification38判据通过（37符合、1本地生产不适用）；Validation17适用场景及独立10旅程通过；40文件1094项、保真修复107项、最终Linux132项及十检查通过。旧29项／8文件和Prelude15项冻结基线失败保留，不称分区全绿。真实k3.1-pro/high两Task6请求代表样本通过，8个后继源码差异分支由当前正式机制补证。

唯一目标转换完成：51历史item、8Snapshot／pointer不变，31独立条目×Task节点在版本内累计55次，180UID引用／81不同UID，162可见投影；生产重开只读验证通过。两套完整三库已逐库核SHA／integrity／FK，研究副本两文件清退；运行库及同步包不动。具体发布／恢复事实只记operations-log；[最终交付](.autonomous/20261027-noting-provenance-history/final-delivery.md)含范围、独立报告、工程细化与限制。本轮无未完成项／新阻塞；原main和旧目录他人dirty未纳入，未做UI／APK或生产模型测试。

## 2026-10-26 · Scheduler二级切换卡顿与0.1.8重建

用户明确卡顿发生在一级面板点击Tag切换Scheduler二级，不是打开球；要求修复、重建0.1.8暂不交付。前端0947ed5已提交／自动push：移除层级及异步尺寸更新触发整板隐藏360ms的玻璃动画，层级改为立即可见可操作的140ms轻量位移；球展开／关闭动画保持，数据到达不重启导航过渡，按需读取与恢复owner不变。旧APK及SHA已移出Mac和云端Alex工作同步区，Downloads原副本及云端同步区外副本保留。

验证：改前Tag导航透明／不可点击反例失败，修后通过；4文件112项、typecheck及冻结TypeScript度量通过。隐藏IAB390×844真实App受控排期延迟3秒，仅1次读取，切换约30ms可见；648采样帧里透明／不可点击／ghost均0。5秒未决请求期间可返回一级，迟到结果不重开；原球展开／关闭回归通过。无Android真机，不把IAB性能当作真机验收。

新0.1.8／1008已重建：本地ignored `.archive/qa018/apk-staging/Hermes-Secretary-0.1.8-0947ed5-arm64.apk`，32,106,601字节，SHA256 `1ffb96ff4476fdb261d01c8d1170f61c02e3eeacb17cd4ffde82085758f7b463`，原证书、v2签名／ZIP CRC／16KB对齐及439前端资源通过；仅本地暂存，未发送或复制至用户同步区。网页已沿先前授权只更新静态0947ed5，439文件和HTTP资源核验通过；后端6ef9459及Web／Gateway PID保持、微信connected。

## 前轮完成情况（2026-10-26）

**2026-10-26最新授权：用户已允许前后端上线，SSH `alex`为正式首尔43.128.131.30／ubuntu；由主会话独立接完迁移会话未完成的飞书notifier MCP（Alex、study均启用），发布本轮代码并恢复Hermes云端正常运行。同步修订全局服务器规则、补齐运维记录；第一台实验用首尔机废弃、准备回收，不再作为生产源。原迁移期间禁止上线约束已被本次授权替代。**

已按用户指定顺序完成统一恢复修复与b33e428阶段APK核验，再完成Noting按需优化。悬浮球仅由当前Profile全局开关决定，与连接状态解耦；未展开排期不取详情，概览用轻量计数，同owner突发失效合并为一个在途请求加一次最新读取，未生效的旧读不消费完成通知。不新增持久缓存。后端查询排除结束严格超过24小时的排期，仅返回hidden_count；删除不返回／不计数，暂停保留，原生模型工具完整列表不变。用户新增胶囊压高已落实：Usage／Context从32降至26px，字体／胶囊圆角不变，底栏36降至30px。最终0.1.8／20c9267已构建并完成交付副本完整性核验，已随本轮在正式Alex上线。用户明确追加修复Compaction message末尾的Conversation start：只取该Conversation的History Foreground第一条timestamp，禁止用内存最早时间或本次压缩区间代替，禁止另猜起点。已删除_summarize_window的内存min(timestamp)，Compaction footer直接读取get_history_foreground(current_session)[0].timestamp；真实数据库反例改前3失败、改后3通过，7文件201项相关测试与10项冻结检查通过。已上线；不改写生产历史／旧摘要。

统一恢复状态本地实现完成：PageRecovery复用原有owner、轮次、读取结果与提交点，派生当前可见依赖的availability；Composer单行提示、主按钮恢复资格及Android恢复／导航回执同源。只有Connecting to Hermes…、Restoring {对象}…、Retrying {对象}…三模板，固定20px单行、随Composer宽度、省略号、多个真实等待对象3秒轮换。移除聊天页其它自动恢复横幅／Toast；草稿保留可编辑，真实写操作及未确认回执反馈保留。已恢复同owner的普通后台刷新不重新锁定操作；隐藏预取不进入完整恢复资格。REST读取增加30秒可取消超时，失败交给既有owner自动重试。

已定位的静默恢复缺陷：Socket connected、Profiles读取成功与页面完整恢复原来各自决定提示，Secretary又错误等待历史／流恢复，导致提示消失但球未出现。现Secretary独立按当前stored owner读取，读失败与secretary.changed刷新均沿恢复owner重试。另一个后端根因：原生压缩后的完成回执来源仍visible，但active=0；恢复层误拒并返回runtime_unavailable。只放行exact UID／row／role且visible并active或compacted的已完成来源，rewind／删除／不匹配仍拒绝。此前只读取证与本地原生链路反例均可复现，不归因于网络。

通用规则见[AGENTS](AGENTS.md)，稳定入口见[README](README.md)，逐次部署／故障历史见[运维记录](docs/operations-log.md)。历史CLAUDE可由f812c1d等已提交时点读取，不把旧阶段的“当前／正在”继续作为任务编排。

本轮发布及迁移收尾已完成：Alex、study飞书MCP握手均仅notify，未发通知；Hermes恢复正常运行。旧实验首尔机废弃、待回收，未销毁实例。全局服务器规则已精简。具体版本、验证、备份与限制统一见[运维记录顶部](docs/operations-log.md)。20c9267旧APK原已交付并核SHA，用户本轮要求后已移出两端Alex工作同步区，新构建暂不交付。

## 当前交付与运行版本

| 项目 | 已核结果 |
|---|---|
| 本轮本地代码 | 后端88ed1ca与前端5f974b3已合正式远端主干并上线；第三轮Verification无违规／不足，Validation50限定通过／15部分／0失败／1不适用；本地最小路径已齐，设备／真实认证边界仍未全闭 |
| 后端线上最后核验版本 | 88ed1ca7e34c2be5dbcdbc9b30b55ca6ed5407fe；21:13:41+08正式Alex检出main，两实际服务同源、active／running，微信connected，数据／配置／绑定保护已核 |
| 前端线上最后核验版本 | 5f974b3bd70a67180039067df1e3b0356532e3cc；439静态及HTTP六资源逐SHA保持 |
| 已交付APK | 最新0.1.9／1009：Downloads/Hermes-Secretary-0.1.9-5f974b3-arm64.apk，32127841字节，SHA81a121d1537991534cd844d4060e29955b00d3121694a10702847069bdb28867；原证书／439资源／v2／ZIP／16KB／交付副本通过；不冒真机全生命周期已验 |
| 运行设置 | 历史noting off不代表当前值；最后已核local_enabled=true，默认／Alex压缩总时限1000秒及Idle500秒／96K保持。本轮只追加授权飞书MCP配置／官方PM mcp依赖，不改模型或调用生产模型 |
| 保留他人工作 | presentation报告、手动Noting调试入口／协议生成、07等原dirty保持，不纳入本轮恢复补丁提交 |

## 前轮交付事实索引（本轮唯一任务看板见顶部）

| 工作 | 状态与完成边界 |
|---|---|
| Noting来源链／History Get Meta | 3426c0f已合入main并上线；双独立门禁通过，唯一目标转换及RPC／保护数据终验通过，详本轮交付报告 |
| Composer统一恢复契约 | 本地实现与正式App链路已验，已提交／自动push前端b33e428，等价抽取217项及复杂度检查通过；已部署正式Alex |
| 压缩后完成回执恢复误拒 | 本地正式入口及原生链路105项通过；补充中断／失败压缩路径7项通过，10项冻结检查通过；已提交／自动push后端98a707e，已部署正式Alex |
| 0.1.8重新构建 | 20c9267最终APK已构建并核验，唯一新文件名与SHA／verification sidecar已生成；无真机不声称安装验证 |
| Noting弱网按需读取／显示解耦 | 已提交／自动push前端20c9267、后端4b04546；本地实现及主会话隐藏IAB已验：未展开0次、展开1次、关闭／重连无额外列表读；底部隐藏摘要、全局开关控制球、断线球保留；不新增持久缓存 |
| Compaction末尾Conversation start | 已按用户再次明确的Foreground第一条修复，真实DB连续三轮原地压缩／Session轮转／冷恢复稳定；非单调时间与foreign owner反例覆盖。7文件201项及10项冻结检查通过，已提交／自动push后端453401d，已部署正式Alex |
| 重连阅读／流式漏显 | 388839c已交付：idle前缀兼容保视口；active或已证前缀失配才回底；连续连接手动20秒规则独立。旧恢复冻结挡住已到达消息的机制、首次NewChat／冷active慢Pending路径已补齐。本轮回归继续验证 |
| Composer满高闪动 | 小数scrollTop钳制导致的无效重复scrollTo已修：原90次含30次无位移，修后105次均有实际位移。未修改键盘／布局；Android Chrome真机绘制尚未验，不把桌面窄窗口等同问题全部关闭 |
| 既有工具展开状态 | construction→UID admission展开保持测试在未修改388839c隔离副本同样失败，已留证；本轮不改断言掩盖，不与流式可见修复混为一谈 |
| 已有成果 | 冷刷新正文缓存／暖态阅读保持、Thinking身份修复、Context终态单次高亮、Stop后持久终态恢复、Compact部分摘要提交均沿既有已发布成果保持；历史逐项证据见operations |
| 手动Noting调试入口 | 别的工作已有本地dirty，尚未发布／调用；本轮不混入或额外触发Noting |

## 验证摘要与边界

- Compaction start修复：真实DB反例改前3项失败，旧代码将Conversation的9月21日起点写成内存后段9月22日。改后3文件96项及4文件105项通过，合计7文件201项；原地压缩／Session轮转各连续三轮，重开DB／重建compressor，末尾始终等于同Conversation History Foreground第一条timestamp。另测后续行时间更早、外部Conversation更早、旧RAM字段与确定性摘要路径，均不改变权威起点。10项冻结检查通过，证据见ignored `frontend-018-20261026/conversation-start/`。

- Noting／排期／紧凑胶囊收尾：前端22文件504项通过、6项跳过（5项已证旧失败＋1项可选原生wire夹具未配置）；typecheck及冻结TS复杂度检查通过。后台5文件73项通过（24h前／整点／之后、删除不计数、暂停保留、foreign owner隔离、SQL先过滤再投影、只读不改库、原生Scheduler语义），10项冻结检查通过。仅暂存本轮生成协议增量的隔离快照亦通过字节级重新生成检查。
- 扩大检查发现controller.test的4项旧失败，与此前工具展开1项一并保留；均在改前隔离快照复现。后端whole-wire目录检查的review.summary孤立契约同样在改前98a707e复现，未改断言或纳入本轮修复。测试中旧方法级夹具不启动PageRecovery，已隔离其刷新副作用；正式恢复owner／完成回执合并由完整native DTO测试覆盖。
- 390×844隐藏IAB实际App：胶囊各26px、上下padding2px、圆角999px、字体12px、底栏30px。关闭Noting详情不取排期，概览仍显示轻量计数；展开仅一次读取并显示4条隐藏摘要；关闭再失效／重连仍只有1次。断线球仍显示，Composer单行Connecting；恢复提示消失，球回到idle。

- 前端最终相关21文件483项通过、1项明确排除的已复现基线失败；typecheck通过。初次467项中465通过，旧Usage横幅断言按新合同更新；另补Android导航等待本地状态恢复测试，141项定向通过。等价复杂度抽取后217项通过，18个变更TS文件按主仓冻结度量／阈值检查无新增问题；Controller保持2550行。
- 后端正式恢复与原生结算2文件105项通过（46.2秒），包含改前失败的compacted回执、实际archive_and_compact和有／无Steer路径；随后新增中断／失败再压缩两条反例与夹具等价调整，7项定向通过；10项冻结检查通过，初次测试分支HX011已按表驱动修正，不改规则。不扩大为全仓通过。
- 主会话自己的隐藏IAB，390×844隔离真实App／Controller：实际Send后历史／Pending仍等待即可见User、Thinking、工具和流式正文；历史完成只剩Restoring live updates…；Pending返回后提示消失、球存在且Stop可用。失败Noting后台刷新只显示一条Retrying且不锁操作；断线与重连尚未恢复时同位置提示且主按钮等待；全部恢复后提示消失、草稿保留、Steer可用、零Toast。真实业务请求全部受控替身，无生产模型／用户页面操作。
- 0.1.7本地原件和副本核验通过，用户手机损坏根因未证实；后继APK产物核验不等同真机安装／生命周期通过。

## 保留事项（不自动立项）

| 事项 | 当前边界 |
|---|---|
| 跨进程busy Instant Reminder | desktop来源且Gateway持Main租约时，Instant可能另起Web运行而非转Deferred；10/24已确认，本轮未修。Deferred已验正常，未发现原文误外发 |
| 微信主动出站`prepare failed` | 既有失败与脚本exit 0误判风险仍独立保留；本轮connected不等于主动出站恢复，未试发 |
| 微信早期正文投递时序 | 18:18长正文已定位为刚生成即发送且拆成两段；更早正文是否积压尚缺逐消息发送身份回执，不将现有记录推断成已修 |
| Conversation时间／分页 | Compaction末尾Conversation start已本地修复并列入看板。旧第10项pagination反馈及47条历史时间副本仍未关闭；没有生产恢复写入授权 |
| 旧失败Noting内容重建 | 空工作态历史反例在原HEAD2122223复现；本轮只验证恢复入口生命周期，不冒称其内容重建已修 |

已关闭的拍照参数、首触Send、会话列表、补水流量及旧Kimi专项不重新挂账；Reminder语气、编排分流与触达白名单归模型行为调优，不变成开发任务。SOUL／workspace AGENTS不因文档整理改写。

## 证据入口

- 本轮恢复：ignored `.hermes-dev/frontend-018-20261026/`，前端ignored `.archive/qa018/status-evidence/`；最终日志会随收尾复制到同目录。
- 原388839c部署／APK：`release-388839c/apply.log`、`final-388839c.json`及Downloads交付旁SHA／verification收据；旧JSON的awaiting发布语句属于构建当时，实际上线结果以apply.log为准。
- 历史冻结／验收：[README索引](README.md#重要文档索引)及[运维记录](docs/operations-log.md)，不改写原报告时点。
