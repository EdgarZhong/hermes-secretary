# 运维记录

维护实际部署、故障处理、验证与回滚点；步骤和稳定布局见[部署SOP](cloud-deployment-sop.md)，当前任务只在根[CLAUDE](../CLAUDE.md)。以下时间均为Asia/Shanghai；PID、指纹和测试结论只对应记录时点，不代表实时状态。凭据、令牌、原始私人材料不写入本文件。

## 2026-10-20晚 · Gateway语音与缓存同步

**后续追加已上线并真实验收（23:51部署）：** 用户要求转录回显与AI首条实际回复合成同一消息，不再单发转录通知；保留回显内容。`532cadb4d81e4dcca3dbb3ec4ba05c94fd4fb072`已提交push并快进首尔，Web／Gateway正常、微信connected，原绑定和此前Alex10155条／host2条消息保持。显式`gateway.stt.echo_transcripts_with_reply: true`已在控制根启用，默认false，既有echo关闭仍优先；本次仅微信路径启用。事件持有回显，首条模型interim／final／错误回复出口带入，成功ACK才消费；队列递归明确传递事件归属，无chat全局队列，人类投递增强不回写模型assistant历史。短回显与AI正文先聚合，绕过微信逐行拆分，仍保留原生大小限制。专项24项、相关71项与配置加载99项分组通过（重叠6项，共188个不同场景），主会话亲审接线、重试、队列及历史隔离；完整暂存树冻结10检查通过，0 blocking／advisory，另清理一处新文件EOF空行后diff检查通过。

Alex Command Provider命令已增加16kHz单声道AAC64kbps压缩，复用命令临时目录及既有阿里脚本，adapter源码／Key／study配置不变。官方PM按现有锁安装FFmpeg9.0.1；旧样本WAV340844B→M4A49126B，新增编码0.1169秒，实测总5.0297秒，转录与旧结果完全相同；网络波动存在，不能把全部提速归因压缩。第二份真实样本经完整压缩Command Provider预检6.074秒、转录仍为“这是一条语音消息。”，原声保持、SILK和命令临时目录清理通过。用户新发语音已真实入库，模型输入仍有`Voice message transcript:`，assistant持久历史无投递回显头；用户明确确认“已收到合并回复，没有独立通知”，真实微信显示验收通过。随后另一条语音也正常入库。新语音处理后临时目录无残留。

本次备份位于服务器`gateway-voice-20261020/deploy-reply-20261020T235155/`（同下述运维工作目录）；含原控制根／Alex／study config、Alex env、三库在线备份及旧提交`b0c9252`。回滚先检查空闲并正常停启，仅撤回根gateway合并开关和Alex此次Command变更、源码回退`b0c9252`，不回盖运行数据库；保留原阿里适配脚本和凭据，不把初轮接通一起撤销。证据：同级`round2-deploy-receipt.json`、`compression-preflight.json`、`compression-timing-audio_434b5f3b17c9.json`，以及本机ignored回显／配置测试日志。

用户确认使用`paraformer-v2`非实时文件转写，复用Hermes原生STT Command Provider、原生SILK解码和已配置的DashScope Key，不接实时识别API。转写成功正文严格使用`Voice message transcript: <转录结果>`，取代此前来源／可能识别错误说明。用户接受阿里私有临时上传空间及48小时链接失效；本地原始媒体仍按Hermes原生24小时龄期清理，不作为永久原声归档，转录文字正常随message持久化。凭据只在获授权线上环境，不入Git。

Noting预算收尾修复已提交并push `02964de`；语音前缀已提交并push `b0c9252`，前缀／原生Command Provider相关5文件33测试通过、冻结10检查通过。个人阿里适配及57项离线通过测试只放ignored `.hermes-dev/gateway-voice-20261020/`，正式脚本安装在服务器`~/scripts/alex/paraformer_stt.py`，root:root／0555＋immutable，SHA256为`e5d66d877805421d6a036d72b70369bafa4bd6aa867a96df0d562e401bb1fc6e`；未写入公开核心。

缓存同步已核实无需更改策略：Mutagen的Profile配置lane仅8文件白名单（Alex／study各`config.yaml`、`SOUL.md`、`nowledge-mem.json`、`profile.yaml`）；两端cache、日志、媒体和其它运行目录已排除。在服务器Alex／study的cache各建唯一临时标记后强制flush，两者均未到Mac，已删除探针。数据库完成包实查只有`Alex/state.db`、`Alex/projects.db`、`study/state.db`，不含缓存。Workspace双向同步另独立保持。证据为ignored目录的`sync-exclusion.json`。

阿里业务空间原有Key对`paraformer-v2`上传策略探测HTTP200、ACL为private；未输出Key／签名。服务器原无pilk，通过官方PM和现有锁请求silk；首次缺clang编译失败，安装系统clang后重试PM成功。个人辅助脚本误用`import yaml`导致预检失败，独立只读诊断确认项目应使用`hermes_yaml`；新旧PM generation仅新增pilk0.2.4，其余包版本和锁一致，正式启动依赖正常，重启前原服务保持旧环境lease。已修辅助脚本，不再额外重建环境。未裸pip、改锁或修改模型／Prompt／预算。

23:27首尔快进部署`b0c9252385f52d8212973e1e9b2fa9ee0d362b21`，一起包含Noting窄修复；正常停启Web／Gateway，微信connected，原Conversation绑定不变，部署前Alex10153条及host2条消息逐行内容与身份无改变／缺失。仅Alex新增STT command配置与自己0600的`.env`中的既有DashScope Key，使用原生profile secret scope及`env_passthrough`；host／study配置保持。首次尝试因辅助脚本多余Key字符限制拒绝，在写入Key前已回滚源码／配置并正常启服；改用原生dotenv写入接口后二次部署通过。未向其它Profile或全局进程注入Key。

真实验证分两层：已有微信SILK经原生解码／Command Provider／阿里API预检成功（22字，13.49秒），不写Conversation、不触发Alex；随后用户新发微信语音于23:28:52入库，正文为timestamp后接`Voice message transcript: 这是一条语音消息。`，Alex在约30.75秒后生成回复，用户明确确认微信已收到，形成新入站到回复端到端证据。两层处理后原始SILK保持，`hermes-silk-*`及`hermes-cmd-stt-aliyun-paraformer-*`无残留。真实云失败未主动制造；上传／HTTP／任务失败、坏响应、超时、空结果由57项离线测试覆盖。未再次触发生产Noting预算耗尽或恢复历史failed任务。

应用户询问另测同一旧音频分段：总13.4534秒，SILK解码1.2108秒、获取上传凭证1.4020秒、上传340844B WAV6.1175秒、提交0.1611秒、两次轮询0.1586秒、轮询sleep及本地开销1.0089秒、结果下载3.3945秒。上传＋下载约71%，未进一步分离DNS／TLS／正文传输，不能把耗时都归因模型计算，也不能将Alex约31秒响应时间算作ASR耗时。仍保持用户已定非实时API；未扩展为性能优化任务。

备份与回滚：服务器`/home/ubuntu/.local/state/hermes-secretary/gateway-voice-20261020/deploy-20261020T232706/`含部署前3库在线备份、Alex原config／env、host／study原config和旧提交；`deploy-receipt.json`、`preflight.json`、`timing.json`、`e2e-receipt.json`在同级工作目录。撤销须先查空闲，正常停止服务，退回`fcf5d08`并只撤回Alex此次STT／Key新增、移除此次适配脚本后启服；不回盖运行数据库或用户后续配置。原声和转录私有材料仅留服务器。stuck技能已按本次用户明确要求改为完整报告直接贴给用户、默认不派subagent，由用户转网页端调研。

## 2026-10-20 · 第一版收尾

用户确认部署基本告一段落、第一版正常可用，要求精简README／AGENTS／CLAUDE并保持后端、前端、插件三个工作区干净。稳定事实、协作规则和当前状态分别归位；历史轮次报告及固定证据不改写。

用户逐项关闭旧挂账：接受现有拍照压缩（长边2560、JPEG质量0.85）；手机首触Send目前未发现问题；会话列表关闭；补水总流量不构成问题；Reminder静默、编排分流、主动核实／触达均属模型行为指导，不再作工程待办。SOUL.md与workspace AGENTS.md可定初稿，本轮不改写个人文档。旧手机验收报告保留其当时观察，关闭挂账不回写历史测试结果。

入口识别定案：保留原生Gateway／Platform按消息来源轮换和切换notice，不在System Prompt注入当前Platform身份；现`agent/system_prompt.py::_post_workspace_parts`已排除该注入。微信原生slash全部拒绝，提示到Web UI管理会话，换绑回Web告诉AI；该新增实现与验证单独登记，不冒称整理文档即已上线。

部署功能基线：后端`dd93e0053b4a92f1c686bc41e4fe37463e854972`；前端`83285d2be259f1ee9f7e24bba6dd4c70688831fe`。插件收尾前已提交基线`892c6bf20399d43ecc51f829a08ff9b19be2f120`，既有未提交的scripts拼写／显式Space修订本轮一并审查；提交与实际加载分别判断。

本次文档整理前的完整三核心文档副本保留在本机ignored `.hermes-dev/repository-closeout-20261020/`；已提交旧版另可沿Git历史追溯。不迁移整个流水到新看板，不重复启动已结束的Agent任务。

**插件收口验证：** 保留并亲审原10个dirty路径：独立Memory创建在preview／apply与直接调用均拒绝缺失／空／空白Space，Provider提示及wrapper路径统一`~/scripts/`；未增加其它功能。官方runner2文件／3项通过（0失败，0.2秒），5个相关Python文件沿Core Ruff及C901≤20通过；PHASE3历史附录不变。独立工具SHA256仍为下文已部署的`c3447cfd…a7e0e`。完整命令与指纹在插件ignored`temp-r3-personal/evidence/cleanup-20261020/verification.json`；本次未访问真实NM或新增Memory，不把文档／源码提交等同部署重验。

插件提交`f11a8db6c32e109bdc1de6c39c2920bcad14d617`已自动push至`origin/codex/round3-local-completion`，远端SHA核对一致；前端原工作区干净，保持`83285d2`，本轮未修改或重构侧栏。

**侧栏复核纠偏：** `AppFrame`常驻桌面Sidebar，手机抽屉打开时临时再渲染一份并在关闭动画后卸载；手机CSS给桌面副本`display:none`，Radix modal隔离背景。旧自动化选到隐藏节点并点击零坐标，不支持原汇总“键盘导航均受影响”的断言，已在原验收汇总显式更正，不改造布局。另静态发现两实例各持有置顶order、localStorage写入无同页通知，因此手机重排后切宽屏可能仍见旧顺序；尚未UI复现，单独保留待验证，不伪称旧键盘问题。

### 追加实现：微信slash、绑定不变量与主动发送来源

用户确认仅显式绑定／解绑工具可改变Conversation绑定；A的晚到delegation不能推翻已改绑B的结果、不能注入B，自动reset／异常恢复也须守住同一绑定。主动发送工具异Conversation时在用户消息头加调用方标题，不向调用方AI新增加注说明；缺身份、绑定／查询不可用时保持原文发送，不猜来源。规格已即时写入08。

微信slash子包已由root亲审：鉴权后统一拒绝入口，微信活跃adapter只inline引流，避免Base在runner之前执行取消；其它Platform、内部事件、普通文本／路径沿原生。6文件121节点通过（含新增64节点），临时index定向Ruff／health通过（0 blocking／advisory），主入口原超长文件2046→2044行，未调整阈值；完整证据在ignored`.hermes-dev/weixin-slash-20261020/`。仅本地真实入口＋模拟transport，未主动发送生产微信消息。

主动发送候选已root亲审：标准库单文件，默认peer发送前用原生control socket一次读取caller／binding，查询预算1秒；不同ref加`【会话：调用方标题】`单行头，同ref／身份缺失／查询失败保持原文，不改回执或发送次数，dry-run保留原语义。16项正式main路径离线测试通过（真实fake Unix socket＋mock iLink），Ruff／C901／结构检查通过；候选SHA256 `ef1e73266f87d2cb4b30b39c1e773dff19c41747595937c6ecec99846a0ffd67`，原件`f9983408981717d000cd0aba01fc8b4a918835169a18046dd0d9af4849cdabb4`。源、manifest、测试与脱敏diff在ignored`.hermes-dev/weixin-send-20261020/`，原件维护获用户明确授权，部署后须恢复root:root／0555＋immutable；未发送真实微信测试消息。

绑定不变量子包已root亲审：持久绑定owner统一限制reset／force_new／switch／compression推进；只有显式control解绑传窄授权参数。回流在全部await后再次检查当前store owner，覆盖A→B并发及已结束A，不把旧结果注入B；durable结果内容保留。耗尽压缩保持原Conversation并提示Web处理，suspended的内部事件不解挂起、真实新输入恢复原Conversation；清理／删除不隐式解绑。显式bind／unbind主库成功后才发布，失败保留原绑定。259相关测试通过（22新增真实SessionStore／DB／派发队列回归），冻结10检查通过，0 blocking／advisory，超长文件指标未增加；证据ignored`.hermes-dev/incident-20261020-reminder-weixin/binding-invariant/`。生产极端场景及微信实发未冒称通过。

### 17:58 · 统一上线与交付

用户催办后优先部署。完整集成暂存树22路径的最终冻结10检查全部通过，health14代码文件／0 blocking／0 advisory，未改规则或阈值；未为收尾重跑已有效的大型／定向套件。后端提交`fcf5d08ac587b43c5aafd2f3e8656a6c5b147432`已自动push并快进首尔，含微信slash与绑定不变量；前端保持原版本，不重构侧栏或重新构建。

17:58:09原生Web active_list与Gateway control均确认运行任务0，在线备份host／Alex／study三库并核完整性；服务器原dirty CLAUDE及补丁另备份后，按用户文档清理授权恢复版本库文件再快进。正常停启Web及Gateway加载代码，发送工具按已确认SHA替换并重新保护。17:58:28回执：Web688083、Gateway688086，running／微信connected，Gateway code_sha与部署提交一致；服务器工作区干净。

保护核对：原显式绑定不变；Alex `.env`、config与workspace SOUL／AGENTS字节保持；部署前Alex9956条／study0条消息逐行内容及身份缺失／改变均0。发送脚本为root:root／0555＋immutable，SHA与已审候选一致、help正常。随后使用真实原生control和现有Main身份，只读验证同ref保持原文、异ref精确来源头、缺身份原文，绑定前后保持；未调用iLink发送、未新增模型Turn。极端绑定场景仍以本地真实DB／worker验证为证，不冒称生产故障注入。

备份：首尔`/home/ubuntu/.local/state/hermes-secretary/incident-20261020/v1-closeout-20261020T175809/`（三库在线备份、旧发送脚本、旧服务器CLAUDE及补丁、receipt）；本机ignored`.hermes-dev/repository-closeout-20261020/`含部署／预检脚本与日志。回滚代码到`dd93e0053b4a92f1c686bc41e4fe37463e854972`及旧脚本需先空闲检查、正常停启并恢复工具保护；不覆盖运行库或回滚已新增用户消息。后续纯文档收尾提交只同步仓库，不推进线上checkout，避免再次触发运行中Git漂移保护。

## 2026-10-20 17:14–17:19 · 微信Kimi凭据修复及冗余操作回滚

**症状与根因：** 微信入站和目标路由正常，但模型报`missing_api_key`。Gateway进程虽有Kimi变量，多Profile作用域仍只读取目标Profile自己的凭据；Alex `.env`缺Kimi。注册路径`~/.hermes/profiles/alex`与实体`~/.hermes_profiles/Alex`是同一Home，不是双目录问题。最初误连旧北京`alex`仅查询服务状态，未修改；实际排查／修复在`seoul`。

**修复：** 备份Alex `.env`，用原生`save_env_value`仅补`KIMI_API_KEY`，0600，其余条目逐项相同。不改隔离、Provider代码、历史、模型、Prompt或绑定。每次入站重新构建作用域，配置本身无须重启。

**验证：** 正式`_profile_runtime_scope`＋`resolve_runtime_provider`从`AuthError/missing_api_key`变为`env:KIMI_API_KEY`、`anthropic_messages`、`https://api.kimi.com/coding`；default／study仍不可继承该Key。原生客户端独立请求`k3-256k`实际HTTP200、end_turn、正文OK，3.267秒，91输入／33输出tokens；未向用户Conversation写测试消息或主动发微信。

**按用户要求重启／回滚：**

| 时点 | 操作与结果 |
|---|---|
| 17:16:53 | live确认active_agents=0、active_work为空；Gateway595732→669615，running／微信connected；Web584724不变，原绑定保持 |
| 17:19:27 | 核用户凭据副本与`/etc/secrets/`原件字节一致，systemd／scripts中仅新增drop-in引用；备份无Key的drop-in，撤掉它并恢复原Gateway启动入口 |
| 同次回滚 | daemon-reload，Gateway669615→671152，running／微信connected；删除`~/.config/hermes-secrets/{kimi-code,deepseek}.key`及空目录；未另存Key副本 |
| 回滚后 | 三个Kimi进程变量均不存在，Alex正式作用域仍可解析Key；Alex `.env`字节、原绑定及Web584724均保持，证明修复不依赖冗余注入 |

原绑定ref为`conv_8dc89e12cc9b42b5a77986f4d9b02cec`。独立Provider请求不是新微信消息端到端证据；用户随后总体确认第一版可正常使用，不反推补造逐条微信测试记录。

备份：首尔`/home/ubuntu/.local/state/hermes-secretary/incident-20261020/kimi-scope-20261020T171430/`，含0600的`alex.env.before`和无Key的drop-in备份。脱敏`receipt.json`、`api-probe.json`、`restart-receipt.json`、`rollback-receipt.json`亦在本机ignored `.hermes-dev/weixin-kimi-20261020/`。若撤销本次Profile配置，仅原生移除新增Key；后续已有编辑时不能整文件回盖。原`/etc/secrets/`及Web系统服务凭据配置不属于回滚范围。

## 2026-10-20 12:22–13:57 · 冷态提醒、模型窗口与Conversation绑定

- `43940df105998b9c74636b1739ce5dcd8c76f7f5`修复合法Pi导入Main冷扫描、会话实际路由的Context窗口、Kimi canonical目录和持久Conversation绑定，已部署首尔。三批定向52／78／74项合并146个不同节点通过，冻结10检查ok／health0；未跑全量套件。
- 用户确认Alex默认`kimi-coding/k3-256k`、262144窗口；仅改Profile默认，不覆盖已有Conversation。DeepSeek自定义500000窗口仅属匹配路由，目录保留一个正式DeepSeek Provider。
- 12:37–12:39在不重启Web宿主情况下，desktop和pi-import测试Conversation真实回收Runtime后由5秒扫描器恢复K3；接纳延迟3.935／4.131秒，两排期done、claim_attempts=1、receipt delivered。自有Conversation正式归档，未触原置顶或微信绑定。
- `5fb8ffcc7c`引入Gateway原生本地控制通道绑定入口；`dd93e0053b`收口Alex专用工具`bind --self`、最近Conversation去重列表及is_self／is_current_binding。最终36个不同节点通过、冻结10检查ok／health0；实际CLI幂等绑定、无身份和跨Profile拒绝通过，不冒称真实AI自调用。工具正式SHA256 `15a55eeea9fb2d70422d69ccc263a1923cd8e3fa47bca01a68d1a76b19c9fe5a`。
- 工具统一`~/scripts/`，旧拼写目录／别名已清；Memory preview／apply强制显式非空Space，Default传`--space default`。Memory源码／两端SHA256 `c3447cfd1535b32d324ecf50e89c86a808950680ac5f01188c1c41983e8a7e0e`；当时14定向通过，首尔离线5场景通过。首尔三工具root:root／0555＋immutable，Mac Memory0555＋uchg；普通误写拒绝，不扩为sudo隔离。
- 13:57按用户授权仅清原置顶持久System Prompt缓存，空闲正常重启Web／Gateway清内存，随后由正常Turn原生懒构建。部署前后消息／Secretary表、身份／模型／绑定／workspace规则指纹核对保持，不做额外离线resume或模型Turn。

备份／证据：首尔`~/.local/state/hermes-secretary/incident-20261020/`内`20261020T122213`、`alex-default-*`、`binding-v2-*`、`binding-v3-*`、`tools-final-*`、`scripts-unify-*`、`prompt-reset-*`；本机各本轮ignored日志保留。

### 微信异常恢复调查的有效边界

普通原地压缩、rewind、换模型、Runtime回收和正常重启不等于创建新Conversation。已识别的风险仍须与正常路径区分：压缩耗尽reset；活动任务跨连续重启后suspended、下次入站reset；异步delegation晚到时恢复旧owner。历史5项隔离诊断证明过旧行为，不是修复通过或生产极端场景实测，原件为ignored`.hermes-dev/incident-20261020-reminder-weixin/test_binding_identity_audit.py`及`binding-identity-audit-tests.log`。

Delegation风险有严格前提：回调携带派发时的`session_key`／`parent_session_id`；只有它关联的同一路由后来从A换到B且A仍存活时，`_resolve_async_delegation_session`可能把该路由切回A。不存在“同Profile任意其它Web Conversation完成任务就抢微信绑定”的通用扫描。现测试`test_live_spawning_session_rebinds_from_different_route`明确覆盖旧切回行为；本轮只核实解释，不扩修回调机制。

## 2026-10-19晚–10-20凌晨 · 手机恢复与历史分层加载

先暂停Caddy HTTP/3，只开放h1／h2；对照显示协议切换本身未解决所有慢传输和恢复问题。随后后端`9a0c479`／前端`83285d2`上线：列表summary、已持久化user回执及可重放事件、标题独立恢复、历史cards首屏及按ID详情补水、legacy读取优化。默认API完整语义、分页200、DB schema／索引与模型配置保持。

当时验证：cards42项、legacy及回归147项、submit_idle85项，UI57文件／836项及typecheck通过；冻结10检查ok／health0。无上下文对抗审查6项已修。部署后HEAD变化触发一次stale-module 503，空闲重启宿主解除；不因此关闭保护。

真实手机／桌面DSH在00:21–00:31完成三轮5／2／5工具场景：A1输入及时显示、A2跨端user、A3标题、A5分层、A6首屏、A7一致性取得记录；A4列表合并取消未达当时目标，并记录首触Send／总字节／双侧栏等观察。**这些是当时版本结果，用户后续关闭的挂账见本文件首节；不修改原判定。**

报告：[手机验收](mobile-http2-acceptance-20261020.md)。原件在本机ignored `.hermes-dev/mobile-http2-retest-20261019/runs/20261020T001037+0800/`，118文件manifest SHA256 `ecf2764e6fe585162e75f9b62eea993b236abd615df9018823f53ee18d7d4de0`。部署receipt在`.hermes-dev/seoul-frontend-20261019-83285d2/`；前端回滚目录`.secretary-before-83285d2-20261020T000620`；HTTP/3原配置在首尔`/var/backups/caddy/http3-paused-20261019T230037/`。

## 2026-10-19 · 首尔迁移与同步完成

正式Hermes／Ebbinghaus／NM从北京迁首尔；Hermes原文及身份逐表核对、原生RPC迁workspace，NM保持官方0.10.101及原token，改阿里OpenAI兼容云embedding并原生reindex；源数据保留，北京相关服务／旧snapshot timer停止。OpenClaw未迁移。

首尔Caddy HTTPS＋Authelia双因素与Redis会话已落地，正式域名生效，旧test入口404。Profile实体Home注册反查由`2a6bc5b`修复；default保留，不靠UI隐藏绕过。Kimi Search／Fetch及沙箱Chromium MCP有真实成功样本，不外推Finance等未验业务。

三条同步已验证：workspace two-way-safe、8文件配置双向、每300秒云端SQLite完成包单向回Mac并冷态验包。Desktop TCC旧等待已由正式marker往返关闭，不能再列阻塞。SOUL按用户定稿，不回盖较旧Mac副本。详情／备份见SOP及ignored `.hermes-dev/seoul-migration-20261019/`、首尔`/var/backups/seoul-migration-20261019/`。

## 历史验收与证据保留

固定v5产品意图PI01–26及独立Verification／Validation按原版本PASS，入口[20261018索引](../.autonomous/20261018-product-intent-review/snapshot-index.md)。第三轮早期NOT PASS、真实模型误归因／Search完整性等失败和已接受非阻断观察不回写为成功；不将本次运维增量冒称旧门禁覆盖。

历史全量Python／UI曾有失败，后续仅按影响定向关闭，不能宣称全量全绿；原件见ignored `.hermes-dev/deploy-readiness-20261018/suite-triage.md`和产品意图复审报告。旧Agent分工、旧PID与初始化等待不再是当前任务；需追溯时查对应轮次报告或Git历史。
