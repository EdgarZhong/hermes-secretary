# Hermes Secretary 当前状态

## 自主口径收敛 · 待用户追认

暂无。UI-CAM-01已获用户确认，拍照压缩保留当前实现。

## 当前阶段

**Alex百炼模型目录已排除（2026-10-21 13:44）：** 用户要求排除语音阿里云Key自动带入选择器的全部百炼模型列表，保留独立Kimi／DeepSeek／GPT。仅Alex设置model_catalog.excluded_providers为alibaba、alibaba-cn及Coding Plan／Token Plan的国际／中国共六slug。前端同一model.options RPC核实Alex百炼3组194条消失，Kimi11／DeepSeek2模型集合保持，study GPT14与默认DeepSeek2保持，当前Provider／模型未切换；语音Key、其它Profile配置和认证文件指纹不变。页面已有目录需重新加载；未控制用户页面，未作视觉验收，无代码／服务重启／模型请求。备份与收据见operations-log。

**Alex／study工具配置已同步（2026-10-21 13:40）：** 用户要求关闭Alex的vision_analyze、不再顶层注入，并把这套工具配置原样复制给study。两者均agent.disabled_toolsets=[vision]；原生工具选择／折叠配置沿相同默认，kimi-tools与playwright完整定义复制、保持enabled和lazy。两Profile正式只读组装均26顶层，Web/TUI5个／微信4个原生折叠；延迟MCP未连接初始化，不计入此独立组装数量，加载后沿原生Tool Search折叠。模型／认证／Noting和Scheduler开关、其它配置与历史／排期保护表指纹保持，未重启服务或发模型请求。后续原生刷新／新Agent生效；备份和收据见operations-log。

**Main工具顶层声明已部署（2026-10-21 13:32）：** 用户确认Scheduler／Notebook Show按各自独立能力开关完整进入API顶层`tools`、退出折叠目录；Scheduler仅受scheduler开关，Notebook沿既有全局Noting读取门禁，当前Conversation的Noting参与不控制二者。`f7d93351ca`已部署Web／Gateway；部署时正式Profile配置独立组装核实两入口均27个顶层工具（后续按用户要求关闭Vision后为26），原生折叠Web/TUI5个／微信4个，差异仅desktop_project。303项相关测试通过，1项Noting全局活动任务计数失败在未改基线同样复现；冻结10检查通过。隔离K3样本：重复旧历史的Scheduler正确，新上下文Notebook正确，重复旧Notebook历史时有一次复述旧结果未调用，指定tool_choice对照400；不声称模型行为全通过。三库历史／排期／待投递／绑定全行SHA及配置保持，无主会话测试消息、排期写入或自动回退。07§8.2、运维记录已同步；证据ignored`.hermes-dev/main-direct-tools-20261021/`。

**Scheduler schema最小修复已部署（2026-10-21 12:57）：** 用户确认修复并部署，明确不动主会话历史和已有排期。`fba851b2ef`只为Kimi转换层无属性定义、未显式限制额外字段的泛型object补`additionalProperties:true`；保留required、明确关闭对象及类型字典约束。181项相关回归与冻结10检查通过，修复后三次隔离K3-256k／High查询／重复历史／创建均正确；部署后正式传输层再验重复历史查询正确。Web／Gateway实际同提交、微信connected、自动重启0；Alex10258条消息、20排期、13pending Reminder及三库全部历史／绑定前后全行SHA一致，配置指纹保持。未向主会话发测试消息、未改排期或回盖DB。原调查表明API schema触发Kimi兼容性问题；10:27与12:30均为Chat，上午成功不能被解释为协议切换。首次暴露的确切原因缺原始请求证据，Notebook首调／大快照不是必要条件。备份、两次临时校验脚本问题与最终收据见operations-log；证据ignored`.hermes-dev/scheduler-tool-investigation-20261021/`。

**移动端阶段一与Noting联合交付已上线（2026-10-21 01:30）：** 未开worktree，三个实现包与并行Noting会话已亲审并集成；首尔Web／Gateway实际运行`0bdddfc133`，Secretary前端`1d1b1a7`的439文件SHA通过，Caddy2.11.7已加载限定gzip／私有哈希静态缓存。真实同200行cards 863366B→212094B，实际Caddy gzip54696B；唯一图转换成功／fallback0，引用实际可下载。隐藏IAB经SSH回环观察静置详情0／图片0，展开单卡1次6783B，进入视口单次488384B图片成功解码；公网只验Authelia入口，未冒称登录后或蜂窝验收。纯图片持久受理／同row UID原子认领及失败路径已完成定向测试，未加生产Turn。Noting真实K3/High在1Turn、6HTTP200中正常维护并正式提交3条Snapshot；保留首版400及harness额外校验误用证据。用户C08简化部署后Validation、C09禁止自动回退已落实；切换后空闲检查短暂未通过，保留新版正常运行并续完Caddy，无回退或回盖DB。部署后原Alex10161／host2行内容身份、全部排期和微信绑定保持；既有7条Instant中最近2026-10-21 10:00，Scheduler线程／微信connected／发送工具及原生冷恢复路由已核。未提前触发提醒或测试发送，不把未来触达写成已发生。完整范围、有效证据与限制见[本轮交付](.autonomous/20261021-mobile-phase1/final-delivery.md)及[运维记录](docs/operations-log.md)。持续目标已完成；阶段二及手机蜂窝短实验不在本轮实施。

**K3-256k最小Anthropic验证已完成（2026-10-21）：** 用户明确授权“小贝子”使用实际`k3-256k`补验证；严格3次真实请求、无重试，High、原生Coding Anthropic端点。正式顶层注册1/1成功且参数完整；末尾system.tools携OpenAI schema及Anthropic schema各0/1，模型均表示未提供维护工具。主会话亲审脚本并独立核验实际wire／响应哈希、精确模型ID和父前缀不变；不为review复跑。总输入含缓存1,665、输出510，合计2,175 tokens，实际费用未知。与便宜模型方向一致，但只证明所测两种写法未生效，不推为官方或所有Anthropic动态机制均不支持。仅本地隔离虚构内容，无Chat重测／长会话／SSH／生产数据，不改实现／配置／部署；证据见[运维记录](docs/operations-log.md)及ignored`k3-256k-summary.json`。

**前轮便宜模型隔离验证已交回（2026-10-21）：** “小贝子”12次Coding `kimi-for-coding`／High验证中，Anthropic末尾两种动态封装0/4，顶层注册2/2；Chat动态2/2参数完整，不外推K3的Anthropic能力。历史上“不切协议”讨论限制已由最新用户授权覆盖；当前进入原生Chat配置及Noting接缝实施，实验原文与边界见[运维记录](docs/operations-log.md)。

**Noting模型对照调查已完成（2026-10-21）：** 按用户要求直接复制本地同步DB，用本地代码／独立Profile及数据库跑DeepSeek；原wrapper／root恢复，实际发送父历史250条，投影差异如实保留。`deepseek-flash`／High在87.07秒、8次API、1个Turn内完成，27次maintain中23成功／4字段校验失败，正常finish并提交19条目；无History调用，总token1,193,633。原Kimi50次History已记录7,913,013 tokens，另有未入账总结用量。主会话亲审正式接线、请求工具哈希、usage及副本Snapshot；Kimi10个虚构内容对照支持正文schema与正式／动态工具声明的兼容差异，动态system.tools仅已实测Chat接口。用户确认理解独立结构化声明及缓存边界，未要求改生产Anthropic接口；未改Prompt／工具面／模型配置或部署。接到用户限制后未再访问云端或复制云端材料；完整范围、差异、证据与结论边界见[运维记录](docs/operations-log.md)。

**语音体验第二步已上线并验收（2026-10-20）：** 首尔已上线`532cadb4d8`，显式启用`gateway.stt.echo_transcripts_with_reply`；转录保留到模型首条实际回复合并投递，成功ACK才消费，interim／final／错误及队列分支已覆盖，不污染模型assistant历史。Alex上传改为16kHz单声道AAC64kbps，原始SILK保留；341KB→49KB，压缩样本5.03秒／6.07秒、转录与旧结果一致，网络波动不作固定延迟承诺。188个不同相关场景的分组证据有效，完整冻结10检查通过。原绑定、既有10155条Alex消息、adapter／Key及study配置保持。新微信语音已入库且assistant历史无回显头；用户已明确确认“已收到合并回复，没有独立通知”，真实显示验收通过；运维与回滚见operations-log。

**首轮已完成 · Gateway语音与缓存同步（2026-10-20）：** 首尔已部署`b0c9252`，包含Noting修复`02964de`及严格的`Voice message transcript: <转录结果>`前缀。Alex复用原生STT Command Provider、SILK解码和原有Key，调用`paraformer-v2`非实时文件API；私有阿里临时链接48小时失效获用户接受，原生媒体缓存24小时龄期清理，转录message正常入库。真实新微信语音已转录，Alex回复由用户确认收到，临时文件清理通过；33项相关回归、57项适配离线测试和冻结10检查通过。配置只改Alex，原绑定及既有10153条消息保持；study／host配置不变。Profile Home已是8文件白名单，两Profile缓存探针实测均不回Mac，快照只有3数据库，无须改同步策略。13.45秒预检的主要耗时为上传6.12秒和结果下载3.39秒，真实新消息入库到Alex生成回复另约30.75秒，不混算为ASR耗时；首轮未实施音频压缩。详见运维记录和ignored `.hermes-dev/gateway-voice-20261020/`。stuck技能已按用户要求改为完整报告直接贴用户、默认不派子Agent；移动端网络调查独立保留。

**Noting预算窄修复已上线（2026-10-20晚用户确认）：** Noting原生每Turn迭代预算耗尽时，经既有Commit Gate保存合法工作态，所有触发来源共用，与`force`触发无关；末次调用已成功finish时保留显式结束。无模型／Prompt／预算变更。13个新增边界场景通过，所在测试文件54项通过，冻结10检查通过；相关5文件首次156通过／2失败，两项均在原版复现（旧Snapshot ID正文断言、旧文件活动任务计数污染），不冒称全绿。`02964de`已随`b0c9252`部署，未重跑线上预算耗尽场景、未恢复旧失败任务。21:38:15–21:51:31旧生产任务达到50次上限后failed、无Snapshot为部署前事实；口径已同步07，原证据在`.hermes-dev/pinned-mobile-20261020/`。

**2026-10-20用户确认：部署基本告一段落，第一版可以正常使用。** 本轮文档／仓库整理及追加微信修复已完成，17:58部署首尔；后续按新任务推进，不自动重开旧挂账。

- 首尔正式入口、双SPA、Alex / study Profile、NM / Ebbinghaus迁移及三条Mutagen同步已落地；旧部署等待、TCC阻塞与初始化过程不再是当前任务。
- 已上线后端功能基线 `f7d93351ca1d93a46e1d9979eee6888f272ad5ec`（含阶段一、Noting动态工具、原预算修复、语音链、Kimi泛型schema修复及Main两工具独立声明）；前端 `1d1b1a7c53b9baf86576d3c19ebdd5a8b9a98975`；插件收尾 `f11a8db6c32e109bdc1de6c39c2920bcad14d617`已同步。后续纯文档提交不等于运行版本改变。
- Alex默认 `kimi-coding/k3-256k`／原生Chat及Coding `/v1`，窗口262144、thinking High；目标绑定Conversation当前tip同路由，Noting / Scheduler开启，联合Idle500秒／131072 tokens。已有Conversation保持自身模型配置；study不设默认模型，NM Thread目标仍继承考研Space，可选`thread_sync_space`能力保留。
- 微信绑定采用原生Gateway control socket与Conversation ref；Alex工具 `~/scripts/alex/weixin_bind.py`，调用方直接 `bind --self`。Kimi凭据已补到Alex自己的受限`.env`；多余Gateway凭据注入与用户副本已回滚，正常重启后连接及原绑定保持。独立K3请求HTTP200；未把它冒称新微信消息端到端验收。
- Prompt缓存清理已按当时授权完成，后续沿原生正常Turn懒构建，不追加离线重建。个人工具统一`~/scripts/`，只读保护、显式非空`--space`等规则见AGENTS／08。

## 本轮交付

| 工作 | 状态与完成条件 |
|---|---|
| 阶段一P1-01～06、08 | 已实现、亲审、定向测试及构建，联合部署；线上同窗字节与按需请求观察完成 |
| P1-07预算收尾 | 原02964de已部署，本轮未重复应用；新Noting包验证仍正常finish并提交 |
| Noting／Provider协作 | 并行会话本地整包接收，0bdddfc已上线；保留原生Provider，仅Alex默认与绑定tip切Chat／High |
| 后端提醒健康 | Web／Gateway active且自启、Linger=yes，0自动重启；7条Instant排期与绑定／工具保持，最近10月21日10:00；到点实际触达尚未发生 |
| 验证与限制 | 冻结10检查通过；真实回环历史／隐藏IAB请求行为有效。未做公网已登录／蜂窝长实验、生产发图Turn／微信测试发送；不冒称全量测试全绿 |

本轮按用户明确豁免不另跑严格两独立门禁；前端286定向与usage54（重叠）、后端投影26及兼容48、纯图受理34及受影响60、Noting dynamic39／summary4／fallback3的原版本证据由主会话亲审复用。冻结检查对初始50214cd基线，附包CDP工具的两项问题已等价拆分并核51事件输出一致，最终0 blocking／advisory。工作区先前手机调查文档dirty保留，不整树提交。运维详情只在operations-log。

## 保留事项（不因本轮收尾自动立项）

| 事项 | 当前边界 / 下一步 |
|---|---|
| 详情接口 | 第10项pagination元数据漂移尚未得到用户关闭口径，暂保留；不主动扩大修复 |

侧栏旧“触摸／键盘均受影响”已纠偏，不再作已证实缺陷；手机重排后转宽屏的顺序同步仅静态观察，未UI复现，详情留运维记录，不自动立项。

用户已关闭／移出工程挂账：拍照参数接受；手机首触Send目前未见问题；会话列表关闭；补水总流量不构成问题；Reminder静默、编排分流句和主动核实／触达白名单属于模型行为调优，不再列开发待办。SOUL.md与workspace AGENTS.md可定初稿，不因本次整理改写它们。

入口识别口径已定：保留Hermes原生Gateway／其它Platform按消息来源轮换和切换时的notice注入；关闭System Prompt中当前Platform的身份注入（现代码已关闭），不再挂“稳定识别待定”。

## 证据与入口

- 通用规则只在 [AGENTS](AGENTS.md)，稳定规格索引在 [README](README.md)。操作、实际版本、备份与回滚统一 [运维记录](docs/operations-log.md)；执行步骤见 [部署SOP](docs/cloud-deployment-sop.md)。
- 固定v5产品意图复审及两门禁按其原版本保留：[Snapshot Index](.autonomous/20261018-product-intent-review/snapshot-index.md)。旧模型归因／Search完整性／Noting来源偏差为已接受的非阻断观察，不重开为新增开发。
- 不把未验证写成通过；历史全量存在失败，后续定向通过不等于全量全绿。原报告、固定证据、Git历史均保留，不将旧PID、Agent编排或过时等待条件带入下一轮。
