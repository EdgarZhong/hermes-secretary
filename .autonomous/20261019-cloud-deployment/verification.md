# Verification：20261019-cloud-deployment

## 1. 审查对象与结论概览

**当前最终结论：Verification 未通过；14条全覆盖，12条符合，D13实际部署与接收链路已关闭。仅余D02 workspace等待Desktop TCC、D11登录后公网链路未验。完整最终复审见[§6.2](#62-d13真实激活整包的最终集中受影响审查)。服务继续运行，不将审查收尾作为停服条件。**

审查者：独立 Astra/high Verification；日期：2026-10-19。依据为本轮 `snapshot-index.md` §2 D01–D14、`baseline.txt`、当前 `docs/cloud-deployment-sop.md`、06 §0.7–0.8、08 全文；最新用户决定优先，旧 v5 的未变接缝只复用已有效证据。冻结 Core `d215922256a479f7cb7346cef59a234bb71dd1b0`，运行源码继承 `c80e0d02`；UI `d5b20aab`＋受保护用户 overlay；Provider `a7225f60`。`baseline.md` 不存在，采用套件规定的实际 `baseline.txt`。

阶段范围：稳定部署已核；2026-10-19续包已核D13冻结helper `8e1ecc2d…e97a4`、19节点证据及云最终收据，D13实际包已按§6.2完成核对，源码提交`5c7fad17`、文档提交`892c6bf2`。报告不是停服指令。总体：**未通过（12条符合；D02 workspace等待Desktop TCC，D11登录后公网未验）**。本审查不运行模型、不操作云或同步/用户数据、不使用浏览器、不修改源码。

## 2. 独立要求清单与覆盖
以下判据于 2026-10-19 在读取实现代码、测试和实现报告前，仅依据上述原文建立并落盘。按显式阅读要求已先读取 AGENTS/CLAUDE/plan，但其动态解释不作为判据。后续更新只补事实与证据，不降低本节判据。D13 冷态识别/跨库部分失败是方向明确、具体工程接线须重点审查的薄弱处。

| 条款编号 | 来源位置及要求 | 类型/适用范围 | 规格解释及必要不变量 | 符合判据 | 核查位置 |
|---|---|---|---|---|---|
| D01 | 索引 D01；SOP §1 | 原字节身份 | 用户定案两 SOUL 不作语义或格式改写 | 两地 SHA 分别 f260652e…9d56f1 / 8d88f3c9…a0148d，受限权限，Git 无私文 | §3 D01 |
| D02 | 索引 D02；SOP §1/3/4；08 §1/3 | 路径、归属、同步 | Home 分离、原生 canonical alex/study；共享 cwd 不合并状态；Files default 不改聊天 owner | 精确目录/链接及正式 API；workspace 双向，配置限定 allowlist 双向，DB 完成包单向 | §3 D02 |
| D03 | 索引 D03；SOP §3 | 历史数据与正式迁移 | Alex 48/6065，全部身份/原文/来源/root/binding 保持；只有运行 cwd 改；study 新库 | 原生 workspace.move 全48；前后逐条对账；原 Mac cwd 留 origin_json；无测试数据混入 | §3 D03 |
| D04 | 索引 D04；SOP §1/3 | 可选 Provider 行为 | thread_sync_space 能独立覆盖但未配时仍沿自己 Space；study 不迁旧对象 | 可选接口与未配兼容分支、正式安装字节；study 自 Space/无覆盖配置 | §3 D04 |
| D05 | 索引 D05；SOP §1 | 默认模型边界 | study 不配默认、不得继承 Alex/DS 测试模型 | study 文件与原生 API 无默认；独立 Home | §3 D05 |
| D06 | 索引 D06；SOP §1 | 原生 Provider 与实际模型 | kimi-coding / 独立 k3-256k / high / 262144；云既有 Key；禁止 custom/Moonshot/Codex 替代 | 目录、配置、正式运行模型与请求/回复证据一致 | §3 D06 |
| D07 | 索引 D07；SOP §1/3/4 | 可选模型、秘密边界 | DS 可选非默认；只允许 DS Key 上云；云秘密不回传不公开 | Alex 正式模型目录含 DS，默认仍 Kimi；权限与 allowlist 排秘密 | §3 D07 |
| D08 | 索引 D08；SOP §3 | MCP 接入 | 复用云已有 command/args/env 语义，至少 Search/Fetch/Notifier；探测不发消息 | 原配置/接入映射与真实 tools list；不执行通知工具 | §3 D08 |
| D09 | 索引 D09；SOP §1 | 联合 Idle / 关闭冲突 | Alex 500秒/131072、Noting 联合；study 保留 Noting 不新增 idle；原生正常压缩保留 | 正式配置字段/实际读取链，原生另一 idle 定时关闭；无测试缩放配置 | §3 D09 |
| D10 | 索引 D10；SOP §1/2 | UI/产物/用户改动保护 | 只上传 dist；Alex/考研图标复用，显示 Alex owner alex；现用户 UIUX/Pin/布局/滚动保护 | 窄变更、overlay/build输入/双产物指纹、云静态集合、实际显示证据 | §3 D10 |
| D11 | 索引 D11；SOP §6/7；06 §0.7–0.8 | 拓扑与访问保护 | 同域双SPA/REST/WS、单backend、双回环、Host/Origin处理；Access整个host；不破坏旧4入口 | unit/监听/Tunnel差异/路由/API/WS与登录后结果；不关闭既有guards，不公开未保护token入口 | §3 D11 |
| D12 | 索引 D12；SOP §8 | 验收边界与资源 | 仅root隐藏IAB；SSH不拉浏览器；不重复旧昂贵旅程；新增输入资源精确回收 | 执行证据/合规入口；唯一自有runtime确切close，用户历史不删 | §3 D12 |
| D13 | 索引 D13；SOP §4/5 | 快照生命周期；工程细节重点 | 云300秒独立完成包、Mac离线不影响云/不积压；同步外全包验证/两槽；最终更新两个本机冷DB；活库拒绝、原子性/失败准确 | 源timer/固定完成发布、实际Mutagen方向、坏/半包/忙库/离线恢复，逐库原子应用与部分失败记录、有界状态日志；不回写配置 | §3 D13 |
| D14 | 索引 D14；SOP §7/8 | 最新上线优先级 | 先提供可访问入口；收尾审查不阻塞/关停；旧Pi清理最后精确执行 | 服务保持运行、匿名Access及用户入口结果；旧同步不提前清理 | §3 D14 |

## 3. 逐条实现证据

**阅读口径：本表保留初审取证事实并已合并§6.1/§6.2的判定更新。初审时的“待交接、待整合、0实际操作”等仅描述当时阶段，不是当前完成状态；原阶段结论作为历史保留在§6及§6.1，当前结论以§1和§6.2为准。D13当前为符合，未交接状态已被最终实装证据关闭。**

证据前缀：`E=.hermes-dev/product-intent-review-20261018/deployment-release-20261019/`，`C=E/cloud-deployment/`，`U=.hermes-dev/deployment-release-20261019/ui/`，`P=.hermes-dev/product-intent-review-20261018/study-thread-space-split/`。均为本机 ignored 原件；不含本报告新发起的云操作。独立离线核对摘要为 `E/verification-evidence/stable-audit.json`。C 中某些 `.result.json` 是 JSONL；以实际行解析，不把空文件当成功。

| 条款编号 | 正式入口及完整关键代码路径 | 方法、输入、配置及实际证据 | 证据位置 | 判定及理由 | 证据边界 |
|---|---|---|---|---|---|
| D01 | 用户原件 → 受限部署包 → 两物理 Home/SOUL.md；C/07-stage-homes.py 与09续行；C/13及26读取最终SHA/权限 | 独立重算两本机封存原件SHA；云13/26两次值完全相同；Home0700、SOUL0600 | E 两份 *.SOUL.final.md；C/13-plugin-and-init.result.json、26-config-model-mcp-validation.result.json；stable-audit.json | 符合：精确用户字节、权限与实际云目标一致，无格式重写 | 未输出私人正文；不承诺后续用户编辑后的字节 |
| D02 | 原生控制根profiles/alex、study→物理Home；三Profile default-cwd；正式Mutagen配置two-way-safe、DB one-way-replica、workspace two-way-safe | 原生身份/cwd成立；实际config两端各8文件一致、snapshot两端1包、无冲突；真实scratch匹配与反向排除通过；production workspace在Desktop TCC请求下scanning，marker未往返 | C/09、19、30；E/sync/activation/{production-sessions-final,static-prealignment,final-reconciliation,scratch-result}.json、mutagen-tcc-diagnostic.log；§6.2 | 证据不足：仅workspace正式双向链路未完成，真实外部权限阻塞；配置及DB传输已闭环 | 不以scratch工作目录成功代签Desktop；不绕TCC、不改用户路径、不关停服务，旧Pi同步最后清理 |
| D03 | 封存Pi副本 → Alex新Home → session.workspace.move → tui_gateway/methods_session.py:1005 → profile DB.update_session_cwd；study原生SessionDB新建 | 48精确key逐个RPC，0活runtime/0lease，迁后48/6065；32表按完整列hash对账，仅cwd/git四列和运行heartbeat例外，origin_json/UID/root/binding/原文均在对账内；实际REST正确UID、study同ID404 | C/02-source-db-fingerprint.json、19-rpc-workspace.py/.result.json、23-verify-data-and-activate.py/.result.json、30-final-http-data-assets.py/.result.json；13 study 0/0 | 符合：正式迁移而非SQL替代；历史原文/身份/来源保持，初始study无合成数据 | 迁移后唯一获授权新测试Conversation另记，不要求总量永远48；非多库同事务承诺 |
| D04 | a7225f60 personal_provider.py:initialize→_thread_sync_client/_receipt_key→_archive_cleaned→sync_thread；省略字段复用原client，Context/Recall仍原client；两Home正式installer | 亲审增量及初始化清理、首批同ID拒绝、冷pending/分页/fork测试；21不同节点有效证据；独立按Git blob核云20个FILES SHA全等；study space=space/archive=true/无override | P/report.md、manifest.json、commands-and-results.json、final-targeted.log、collision-and-routing.log；C/13及26；stable-audit.json | 符合：可选拆分保留、当前study仍自己的Space、旧receipt键兼容；未迁旧对象 | 未向真实NM新增Thread；显式override跨客户端抢建竞态无服务端原子预留保证，当前未启用该覆盖，不扩当前上线范围 |
| D05 | study独立config→原生profile作用域→/api/model/options及info→New Chat selector | C/26原始model/agent为空，options current model/provider空、rows空；root隐藏AX study无默认 | C/26-config-model-mcp-validation.result.json；E/browser/study-home.ax.txt、root-browser-observation.json | 符合：未写study默认，未克隆Alex或DS测试model | 用户未来选择模型不属于此部署初始化结论 |
| D06 | Alex config及云Pi Key→原生kimi-coding→真实云Main模型请求；原生PUT /api/config补context_length | preflight真实目录k3-256k=262144；C/26原配置与options；C/27正式API合并后effective262144且PID不变；C/28日志真实provider=kimi-coding/model=k3-256k，1次17824入/34出/0工具；AX显示high及“连接成功” | E/preflight/06-targeted.json；C/26、27、28结果；E/browser/k3-probe-complete.ax.txt | 符合：独立型号、原生provider/high配置与一次正式推理一致；按目录补窗口事实满足精确容量 | 自动目录识别仍兜底256000，未宣称已修该原生机制；本次high由有效配置/UI佐证，不声称审到上游完整私密请求 |
| D07 | Alex .env安全落DS Key→原生模型options；默认仍Kimi；云MCP/NM原地读取 | C/11只新增获授权DS Key、其它本机env未传；C/26可选DS authenticated且is_current=false，Kimi is_current=true；静态dist安全扫描未含秘密 | C/11-authorized-ds-key.py/.result.json、26结果；U/artifact-safety-scan.json；C/07受限权限及白名单 | 符合：可选DS未替换默认，已查部署包/代码未输出秘密 | 不发DS真实模型请求；初审待核的同步秘密排除已由§6.2实际matcher与预对齐证据补齐 |
| D08 | 云Pi mcpServers→原生mcp_servers保留command/args/env；POST /api/mcp/servers/<name>/test?profile=alex | C/07按字段拷贝，requestTimeoutMs转秒、lazy语义保持；26实际initialize/tools/list，kimi_fetch/kimi_finance/kimi_search、notify且ok=true；study无MCP | C/07-stage-homes.py、26-config-model-mcp-validation.py/.result.json；preflight/07-reuse-details.json | 符合：原命令/环境及真实协议发现接通，无业务notify调用 | 不声称飞书送达；初审待核的工具注册收据已由§6.1成功32/34原件补齐 |
| D09 | config→secretary/noting_policy.py:105–143→noting_timers.py:95–126→noting_runtime.py:455–505；原生compression读取 | Alex启用500/131072，正常compression.enabled=true，另一idle=0；study无idle块；读取链使用所属DB settings并阈值比较，未改源码；旧v5相同机制证据复用 | C/26结果；上述源码；旧轮verification.md最终§6.1及validation.md | 符合：精确生产参数进入已验正式机制；study不新增联合idle，无测试时间缩放 | 不重跑500秒/100k旅程；未宣称短请求实际触发阈值 |
| D10 | UI NativeProfile.display_name→ChatSelectors展示；profile-icons按canonical映射；实际overlay构建→云双dist→注入HTML/资源 | 亲审4窄文件，选择/URL继续name；37不同节点、tsc/build有效；独立比较before/build只4路径变；独立重算439+67集合SHA；云30再次全量静态核SHA并实取JS；root Alex显示及48链接 | U/task-only.patch、source-before/、source-build/、profile-tests-*.log、build.log、commit-reception.json；C/30结果；stable-audit.json；E/browser | 符合：仅产物上传、用户overlay保持、label不改owner，全部静态字节和实际入口绑定 | 构建包含用户既有overlay，裸d5b20aab不能代签；未重新验整套Pin/布局/滚动，因其字节未改复用旧证据 |
| D11 | systemd单Hermes dashboard + Caddy回环→Tunnel新hostname→Access；/dashboard/api重写共用后端 | 19两WS、20双SPA/深路由、23旧路由保护、30静态/404；续包34 PM rc0/锁/真实proc/仅两回环监听/启用unit齐；5条公网匿名路径均Access302；root隐藏IAB实际到邮箱OTP页 | C/17、19、20、23、25、30、32、34原件；E/browser/public-access-login-observation.json；06§0.7/0.8 | 证据不足（仅余登录后公网）：正式环境与单backend拓扑已绑定，匿名全路径保护成立；未取得登录后同域双SPA/API/WS结果 | 25 Host请求不是公网TLS完整旅程；未请求验证码/接管用户认证，不以索取OTP作停服或继续收尾前置 |
| D12 | 所有云命令remote.py→sandbox-exec SSH；root隐藏IAB→唯一测试Conversation→session.close | 合规wrapper与AX、唯一短请求；29的tools.list错误保留，32正确参数成功后核目标不存在，34真实WS再读runtime_count0、原DB leases0、2条user/assistant保留且end_reason=tui_close | E/ssh-no-ui.sb；C/remote.py；E/browser/*；C/28、29失败、32-final-runtime-validation.json、34-integrated-success-receipt.py/.result.json | 符合：成功复采独立证明精确自有runtime已回收，历史保留；无新增模型输入或其它runtime操作 | 不把29原失败改成成功；本审查者只读原件，不亲操runtime/UI |
| D13 | 固定helper→云systemd五分钟publish-cycle→正式Mutagen snapshot lane→Mac launchd receive-cycle→两槽/冷库原子替换 | 已审源码/19节点；实装helper两端同SHA，timer01:50真实触发且下次01:55；launchd300秒/WatchPaths/exit0；真实3库逐字节/完整行指纹等值，原Pi initial inode保留；暂停仅新snapshot lane时云仍发固定包，恢复追上且自动接收 | E/sync/activation/{installation-and-commit,cloud-installation,cloud-final,launchd-final,first-mirror-reconciliation,final-reconciliation,real-repeat-idempotence,offline-cloud-publish,offline-recovery-transport}.json；final_check.py/receive_and_check.py/db_fingerprint.py/offline_recovery.py；§6.2 | 符合：规定周期、独立发布、真实通道与最终本机冷state.db已接通；完整包校验、原子替换、失败保护/有界性证据链成立 | 离线证据是暂停新snapshot接收lane，非真实Mac关机/整网中断；坏/半包/忙库复用已验19节点，不在生产造坏库；多日/大规模性能未验、跨库非全局事务 |
| D14 | 用户明确先上线→cloudflared业务route→运行backend/proxy；原Pi同步最后清理 | 25服务active/业务route、原其它服务不变；匿名Access302，root实际云UI工作；未收到旧Pi清理执行记录 | C/25结果；E/access-probe/mac-anonymous.json；E/browser/root-browser-observation.json；同步保护初审记录及§6.2实际5旧session对账 | 符合：已先提供运行入口；本审查未建议关停或以报告作前置，旧Pi仍留最后 | “用户能完成公网登录”未由此条代签，仍归D11；后续清理精确session需新链路完成证据 |

最终集中审查统计：14条全覆盖；12条符合，2条证据不足（D02/D11），0条确定实现违规，0条不适用。前两阶段10/11条符合及缺证历史保留于§6的阶段说明。符合仅限该行已查范围；正式全轮门禁尚未通过。

## 4. 核心目标及验证方法审查

核心的“正确身份/原历史/原生模型可用”已沿正式入口取得证据，不能被同步收尾遮蔽：两SOUL原字节、native Profile映射、48次正式workspace.move、完整数据列指纹、真实WS/REST身份、实际模型完成与云静态资源均可交叉对应。Cloud VM使用Ubuntu/Linux，不拿本机v5测试冒充Linux运行；当前Linux正式链路由云原件支持。

D03重点反证：只检查48/6065计数会放过消息内容/UID变化，或把所有origin改掉。本包核查23的全列fingerprint算法及预先02 source，排除仅四个合法cwd/git字段与运行heartbeat，原文/来源/root/binding都参与hash，因此该错误实现不会轻易通过。19的48条RPC、0 runtime/lease避免以静态config代替历史cwd；30实际REST又覆盖owner隔离。

D04重点反证：只把首次import改目标会漏冷恢复、分页、fork或receipt。本次源码把独立client集中传入既有sync_thread，receipt与观测键一致；21不同节点含真实SessionDB、AIAgent完成hook、MemoryManager worker、官方CLI→受控HTTP的分页/unknown/fork/同ID失败。受控远端不是生产服务，不声称真实跨Space写入；当前study省略新字段，原路由及receipt完全保持，此边界足以覆盖本轮上线选择。

D10重点反证：仅功能commit/测试绿不能保证用户未提交UI被打包。已比较before/build的实际字节，变更仅约定4路径，云安装清单与本机产物一致，显示名仅进入文本/aria，所有选择/路由仍canonical；无交互重构。37节点来源为36中其余22通过加修复后组件15，不能说重复37次或全UI suite绿。

D09沿真实读取链确认生产参数；同代码的v5完整门禁用于不变机制，未重跑旧100k/600秒/Memory、大型套。真实单条模型只证明本轮Provider/模型/普通输入输出代表链路，不证明Idle实际触发、所有工具/长程良率。未以模型自报“连接成功”单独判定，另核日志API provider/model、次数/用量/工具数与完成事件。

D11重点反证：Caddy的Host头请求200与匿名Access302相加，仍可能漏登录cookie、公网WS或Dashboard重写失败。因此保留登录后公网证据缺口。PM出现腾讯镜像卡住后通过官方PM在同lock下切官方index重试，路径合规；初阶段原件只有启动/进行中；续包32/34已补最终rc0/锁/运行绑定，此部分缺口按§6.1关闭，不需重建环境或重跑大套。

D13重点反证已固定：只把ZIP放到Mac、connected、手动验证或删WAL再替换均不能满足要求；需实际周期/离线有界/精确包集合/忙库拒绝/每库原子替换与部分失败可恢复。初阶段未读未冻结实现；续包已审冻结源码与19节点，见§6.1；随后§6.2已完成实际部署与冷库接收证据核对。独立判据未改变。

本次没有执行产品测试或云/浏览器动作；仅读文档、固定代码/原件，运行本机离线SHA/集合/字段审计。检查冻结约束未改变。历史v5最终§6.1明确PASS及PI21待决、PI23观察等边界原样复用，不重写历史初次失败结论。

## 5. 发现、整改优先级与范围外项

| 问题编号 | 对应条款/代码位置 | 触发路径与事实 | 影响及阻断理由 | 建议修复与关闭证据 | 当前状态 |
|---|---|---|---|---|---|
| V-CLOUD-01 / P1外部阻塞 | D02；production workspace lane | config/snapshot与D13实际包均通过；Desktop/Alex在tccd DesktopFolder授权请求处等待，PID647、workspace仍scanning，自有marker未往返 | 阻断D02/全轮完成，**不阻断现有服务**；不是实现缺陷 | 用户自行允许Desktop后，精确workspace ID往返marker并清除自有marker；不得用其它目录/绕TCC代签；再按用户顺序处理旧Pi | 待用户系统权限；D13部分已按§6.2关闭 |
| V-CLOUD-02 / P1证据 | D11；SOP§6/7 | 实际云回环两SPA/两WS有效；匿名Access302有效；尚无登录后公网完整访问 | 不能宣称公网登录后双SPA/API/WS都通过，不要求停服 | 由root合规隐藏IAB或用户实际访问反馈取得登录后同域Secretary及Dashboard、API/WS结果；若无法登录如实保留未验，不用匿名302代签 | 待最终用户入口证据 |
| V-CLOUD-03 / P1证据 | D11/D12；C/18、29→32/34 | 原进行中/失败不覆盖；32与34成功复采已给PM rc0、锁一致、真实proc/监听、精确runtime0/lease0及两条历史保留 | 原缺口关闭，不需重建或重发输入 | 34收据与实际采集源码已独立核，锁SHA再与本机冻结Git blob一致 | 已关闭，见§6.1 |
| V-CLOUD-DOC / P2文档 | 根CLAUDE历史区/唯一云部署看板 | root已将v5与筹备段改为历史，新增唯一云部署看板，解除旧当前语气冲突 | 原文档矛盾关闭；最终SOP实装字段仍随同步包更新 | 独立读取当前CLAUDE，当前/历史分工已明确 | 已关闭；未代签尚未落地的同步字段 |

没有在本阶段确认确定性产品源码缺陷。范围外/既有边界：自动model metadata仍为256000但配置已正确补262144；显式thread_sync_space跨独立客户端同时抢建无原子服务端预留；手机、长期稳定性及未来完整治理未验，不把它们扩成当前发布新增开发门禁。用户允许旧Pi清理，但必须新链路完成后最后精确执行，当前不建议提前操作。

## 6. 修复与独立复审

**以下开头为初审历史；§6.1为第二阶段历史，均保留其当时事实和结果。当前最终状态见§6.2，不应将旧阶段等待项重新解读为未完成。**

初审时为预先约定阶段审查，D13尚未进入实现调查；仅核稳定增量并建立全D01–D14判据，没有后验改低判据，没有替实现者设计新机制。无退回补审历史，尚无缺陷修复后复审。

已观察工程处理：原生Kimi元数据兜底256000→root依正式目录262144提议只补model.context_length→正式API合并且PID未变→本审查依据“精确k3-256k及262144”原判据接受；没有把k3换窗口冒充型号，没有把自动识别标为已修。此项应在最终交付摘要保留实际限制。

初审时约定待root交D13冻结代码和云整合包后，只集中核受影响D02/D11/D12/D13及全范围证据版本关联；不重复旧v5、昂贵模型旅程或已有效定向测试。初审当时结论：**Verification未通过，属于阶段证据未齐；当时上线入口继续运行，10条符合结论保持上述边界。** 此历史判定已由§6.1和§6.2更新。 本报告不代签独立Validation或最终交付。


### 6.1 云端最终收据及D13冻结源码续包审查

**第二阶段历史记录：本节“待实装/11符合”是收到最后实际包前的状态，现已由§6.2更新。**

本续包不重读/重跑此前十条已符合实现，只核新收据与相关机制。正式云Core仍d215922；源lock SHA `2bc4db48…d1c67e`独立与本机冻结Git blob相同。`C/34-integrated-success-receipt.result.json` SHA `217a5ebb63573043045495917bf63229d1f6279a5b97294d31aaf110df84cc9e`；其采集源码真实读取systemd、/proc、ss、官方PM最终文件、原生WS及目标DB。PM rc0/frozen、Python3.14.7、原单backend3015797/回环53446及proxy3017385/回环53448、准确cwd、启用unit与既有服务保持齐全，V-CLOUD-03的环境缺口关闭。最终proxy实际是同语义caddy.json，不能继续将初次不兼容Caddyfile模板当部署事实。

32成功收据SHA `8a9f0601f8eb1df194037684fe4ff4dcff2598b9f9e054fbac2739476b72a0f0`；34再次确认root唯一`20261019_013755_07e1d7`已无runtime、无lease，历史仍2条user/assistant，end_reason=tui_close。29的原生4000发生在精确close后续探针，失败保留；关闭结论来自成功32/34的实际复采，不来自29空文件。两MCP已实际registry connected，工具集有search/fetch/notify；无业务消息调用。

D11公网边界：33/34五个匿名路径（两SPA、health、两WS）均跳Access，root隐藏IAB确实见“Log in to hermes”邮箱OTP页，未认证且未申请验证码；摘要SHA `d174f281a3d1a86ffab6add07b9153e5931272e55862de4bbd0ceb88ae0fea6b`。这补强整host保护，不能填补登录后的双SPA/API/WS。用户明确自己访问，不把要求用户提供OTP作为审查/服务前置；保持V-CLOUD-02未验，服务继续。

D13冻结helper SHA `8e1ecc2de07f71a695588c7c6036d985536ffc7895558229be09d5baba0e97a4`；新增测试SHA `a4e9cfd2b6b25e68d06713be09d09cf0b4a37b263f693c232f696b62d47bdc3c`；精确补丁与manifest hash均匹配，独立摘要在`E/verification-evidence/second-stage-audit.json`。源码/分发副本/被测文件同字节，未读取移动中的生产激活文件。

机制核对如下：

- `publish_cycle:312–327`只认2必需/4已知可选DB，源码不存在远端ACK/网络依赖；单flock、同步树外暂存、低磁盘预留、每库SQLite backup/校验、ZIP_STORED及close后fsync+原子固定名replace。timer草稿300秒，service240秒上限且无backend依赖，stdout/stderr不追加文件；未签实际timer已启动。
- `receive_cycle:493–498`经私有根隔离与单flock；`_receive_verified:459–490`先复制、完整验证并提升两槽，后处理目标。坏/半包无法进入目标替换；manifest精确必需/已知可选集合、重复/路径/size/hash/SQLite检查。旧格式静态附件可验证但不进入目标集合，不回写SOUL/config；发布周期自身static=[]。提升已验包发生在busy判定前，故current变更不等于DB应用，status正确区分。
- `_lock_targets:384–398`在lsof/sidecar确认后持POSIX整文件锁，读取hash用pread避免另FD close释放锁；`_replace_mirrors:440–456`每次replace前再查活句柄/sidecar及目标inode，目标单文件同目录stage→replace。写锁/检查不阻止未来任意新进程打开替换后的新inode；这与明确Mac冷态副本运维约束一致，不声称通用写入准入锁。
- 19不同节点从真实SQLite和真实子进程/lsof检查出发，覆盖活连接、三sidecar、准备后晚到reader、坏/半包/未知DB、低磁盘、inode幂等、锁冲突与有界状态。中途study replace注入OSError时Alex已应用，返回partial/applied=[Alex]且initial保持，重试只补study；该反例能暴露“全包成功”假结论。CLI节点真正调用两个子命令，但运输为shutil.copyfile，只证明已完成文件到达后的接线。测试不是源码断言，预期来自D13/SOP，6次runner结果复用不再执行。

第二阶段当时D13源码机制可接收，真实三lane matcher/方向/传输、云周期、Mac launchd及目标冷库、离线恢复仍须最后实装整包。跨两库不承诺全局事务；SIGKILL/断电瞬间可能保留上次status，下一周期按完整包/hash恢复，当前证据不声称任意断电后状态日志立即准确或持久化全批事务。未新增产品门禁或要求为此扩大实现。

关于新行`sessions.profile_name=custom`：已追到原生`run_agent.py:_ensure_db_session`调用`hermes_cli/profiles.py:get_active_profile_name`，后者先resolve物理Home，物理`~/.hermes_profiles/Alex`不在控制根`profiles/`下，落入既有custom分支。该值不能证明跨Profile串库；实际REST owner=alex且study读同ID404、物理Home隔离已证。Secretary宿主扫描按真实Home/DB作用域执行，Provider Space从所属Home配置读取，均不把该列作为跨库选择器。相同路径推导也可能影响部分原生profile标签/agent_identity，故不宣称所有原生附属消费者已校正；此为既有路径标签限制，当前未出现错误owner运行证据，不据此修改历史字段、引入Core补丁或扩大当前上线范围。后续如发现具体功能误归属，再按实际用户结果定缺陷。

V-CLOUD-DOC已由root修订当前/历史分区关闭；本审查未改根文档。第二阶段当时为 **Verification未通过：11符合，D02/D11/D13三条实装/用户入口证据不足**。当时约定等待最后实装包后仅一次受影响证据结论；现已在§6.2完成该集中审查，D13关闭，不重复v5或模型旅程。


### 6.2 D13真实激活整包的最终集中受影响审查

审查仅限冻结源码实装绑定、真实运输与周期/冷库结果及旧资源事实，不重跑测试、不读写真实DB、不操作SSH/Mutagen/systemd/launchd/UI或模型。`A=E/sync/activation/`。独立解析交叉核对保存在`E/verification-evidence/final-activation-audit.json`。

版本：源码提交`5c7fad173e0b60ff55b9d2183e58499ceea93915`只改个人根CLAUDE/README、helper、新测试四文件；后续`892c6bf20399d43ecc51f829a08ff9b19be2f120`只改CLAUDE状态文档。独立读取Git blob重算helper SHA `8e1ecc2de07f71a695588c7c6036d985536ffc7895558229be09d5baba0e97a4`，与两端实际安装原件一致；Provider仍a722字节。云Core仍d215922，backend/proxy PID及启动时间与同步前完全相同，实装没有改动已验产品源码/运行模型。

| 受影响要求 | 真实原件与机制审查 | 判定 |
|---|---|---|
| D02配置/SOUL运输 | `scratch_matcher.py`使用正式配置生成真实双端scratch，含8允许文件与.env/rawDB/WAL/receipts/未知目录负对照；原件`scratch-result.json`显示精确8/1、反向允许更新与未知秘密排除。生产`profile-config`真实two-way-safe、两端各8文件watching且无冲突；snapshot真实云alpha→Mac beta one-way-replica各1文件。`final_check.py`核云/本机8个静态SHA完全相等，SOUL固定两SHA不变；6文件预对齐有原件备份且仅2config实际变 | 该部分关闭；workspace仍缺，D02整体不通过 |
| D13定时及独立发布 | 实际systemd service/timer SHA与受审草稿一致；cloud-installation的calendar每5分钟，cloud-final LastTrigger01:50、Next01:55且service exit0，timeout240秒/低IO优先级/输出null。云发布根仅固定ZIP，暂存仅锁/status。Mac launchctl原件300秒、WatchPaths、runs2、exit0及17:52:42自动applied，准确消费同helper | 关闭；实际Linux/Mac接线成立，不称多日稳定性通过 |
| D13最终冷库与原始数据 | 亲读`receive_and_check.py`、`final_check.py`与`db_fingerprint.py`：对已验current包逐库解出副本，与本机目标做全字节SHA/size及全部表行SHA/计数相等，另核SQLite integrity/FK；文件全字节相等也包含schema。首轮2份state.db及Alex/projects.db全等，原Mac Alex初始SHA cf052567…ec8b6/inode50959517硬链接保留。最终目标是Alex49/6067（含唯一已授权测试2消息）与study0/0，未拿初始48/6065回滚新内容 | 关闭；两本机state.db真实更新，不只是ZIP到达 |
| D13幂等及离线恢复 | 首轮`real-repeat-idempotence.json`同包unchanged/applied=[]、3目标inode保持。`offline_recovery.py`精确pause新snapshot ID，云实际systemctl本地发布新包，Mac旧包不变、状态222字节、固定1包；resume/flush同ID后包SHA追上，launchd自动应用。最终发布SHA、运输到达SHA、receiver SHA与current SHA独立交叉全相等为c1ce43fe…34dac；既有19节点坏包/半包/活库/部分失败继续有效 | 关闭；这是“接收链不可用时云独立发布”的真实代表证据，未执行Mac关机或整网中断，不扩大声明 |
| D12资源范围 | `C/35-original-pi-readonly-resources.result.json`显示用户旧Pi043（20261011_223117_07a84a）runtime4edf8b55仍idle/runningfalse，lease0/compressionlock0，原8消息保留；root已离页但无独占归属证明，未close。该对象不是此前唯一新增K3测试07e1d7 | D12既有符合保持；精确新增测试资源0不等于全宿主runtime0，保留用户旧runtime是授权边界 |
| D14服务与旧同步保护 | `final_check.py`实际对比5旧session的ID/mode/ignore/symlink/watch/permissions/paused及端点未变；云backend/proxy PID和启动时间不变；旧Pi待workspace确认后最后清理 | 符合保持；未提前清理旧同步或关停入口 |

关键指纹：`A/final-reconciliation.json` SHA `4683c95ef5b97073443deb310dae141c8f5a028119dffb28c546249ecf4e7593`；`A/installation-and-commit.json` SHA `e79fe4702040c1576d8b9ffd4b10c4020db338bfb257f71b7e7a4629d5f6ce75`；`A/offline-recovery-transport.json` SHA `93d829d4a96c9e211a1434b6bec912cdc8ac5b9fcfe8121ba7bd8d02a752af4a`。其它逐件SHA见独立audit。

仍未关闭的真实边界只有本报告要求范围中的两项：

1. **D02 workspace Desktop TCC**：`mutagen-tcc-diagnostic.log`记录2026-10-19 01:49:31的AUTHREQ_PROMPTING/service=kTCCServiceSystemPolicyDesktopFolder/Mutagen PID647；生产session `sync_Svc6Epz265hHktU7CcFUR0jE3TPl61MsUGjNWLRyvvA`仍scanning，真实marker往返未完成。用户是否允许由其自行操作；本审查不要求绕授权、换目录或启动控制屏幕。scratch工作目录成功不能填此缺口。自有marker仍须随后精确清理，不删除用户文件。
2. **D11公网登录后链路**：Access全路径匿名跳转及邮箱OTP页面已见，已认证公网双SPA/API/WS无新证据。用户自己访问的决定不等于已成功结果；不索要OTP或将它作为停服前置。

最终集中结论：**Verification未通过，12条符合、D02/D11两条证据不足；D13正式链路已关闭。** 未发现需扩大当前开发范围的新确定性实现缺陷。服务继续可用；独立Validation与最终交付由各自owner按真实TCC/公网边界判断，不将这份报告解释为全轮PASS。
