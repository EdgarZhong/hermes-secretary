# 云部署交接 · 2026-10-19

## 1. 目标状态与结束判定

**云端服务已部署并持续运行；用户最新D15要求的真实浏览器公网访问、Alex新DeepSeek只读自查及最终旧Pi清理均已执行。完整同步目标仍未完成，等待macOS Desktop目录授权；不声明整轮PASS。** 受信任Chrome实际通过已有Access认证加载Secretary与Dashboard，Secretary完成发送、流式工具输出及终态；不是匿名302或SSH回环代签。Dashboard数据/API已加载，不额外声称独立抓取了它的原始WS握手。

剩余外部依赖是Mutagen daemon访问指定`~/Desktop/Alex`被`tccd`要求Desktop隐私权限，已通过异步问题请用户亲自允许；禁止代点、绕过TCC或自行改目录。恢复第一步：允许后只接续现有workspace lane，完成自有marker双向/删除对账，不重建同步。网站、配置同步和数据库回传继续运行。Kimi Search/Fetch业务失败另列限制，未假称修复；当前可独立执行的验收和清理已经收束，不继续扩展开发。

## 2. 本轮收敛与授权

用户定案SOUL原字节、双物理Home、单数共享workspace、Alex原Pi库、study自己NM Space/无默认模型、Kimi Code独立k3-256k/high、可选DeepSeek/MCP、500秒/128K联合Idle、每300秒数据库快照与本机冷库目标均保持。用户后续明确先上线供其访问，门禁和同步收尾不作为停服前置；旧Pi同步可清除但留最后。

D15明确授权当前受信任真实浏览器Edgarzhong Profile作本次公网验收；实际扩展连接名Edgar，沿既有登录，无OTP、系统open或桌面控制。该授权是此次窄例外，不扩大旧规则。root按D15“公网→DS只读自查→清理→汇报”的顺序释放旧Pi五条精确ID清理；先前等待全部workspace链路再清理是Agent计划，已调整，未把该计划当成额外用户审批条件。

原生型号元数据自动兜底256000与正式目录262144不同；root按目录事实仅补Alex `model.context_length:262144`，不改型号/Provider，原生API热合并、PID不变。Astra独立核判满足独立型号/精确容量要求，但自动识别未被修好。新session附属`profile_name=custom`为原生物理Home推导；正式API owner=alex与数据库隔离有效，不改旧历史字段或扩大Core开发。

## 3. 已完成与交付物

- 入口：[Secretary](https://hermes.edgarzhong.fyi/)；[Dashboard](https://hermes.edgarzhong.fyi/dashboard/)。后台专属systemd active/enabled，唯一backend/proxy回环53446/53448；Access保护五页面/API/WS入口匿名302，原Tunnel四路由和其它服务不变。
- 云Core固定d215922；官方PM frozen rc0/Python3.14.7，lock与固定提交一致。两前端只上传439/67份静态产物，完整集合/SHA已核，用户UI overlay保持；UI窄提交d5b20aab。个人Provider a722生产字节保持，周期实现5c7fad17、状态文档/远端892c6bf2，两端helper SHA8e1ecc2d…e97a4。
- 两SOUL SHA逐字保持，Home为`~/.hermes_profiles/Alex`和`study`，native owner alex/study。Alex原48会话6065消息按正式workspace.move迁共享cwd，原文/UID/Ref/root/binding/origin及原Mac cwd来源保持；study初始空库。
- Alex实际页面显示k3-256k/high；首次KimiCode短输入API1次、17824输入/34输出/0工具，收到“连接成功”，该自有Runtime已close、历史2条保留。最新DeepSeek自查另有1个Conversation、7次API/12次工具调用、20条历史/12条工具结果保留，精确自有Runtime资源0/lease0；完成后New Chat和云配置仍K3/high。study无默认，切换仍保留全部历史列表。
- 真实公网DeepSeek自查确认Linux、共享cwd、NM Context Bundle、官方nmem status/doctor；未观察到Memory/Thread/Reminder/Notifier写入或委派。Kimi Search/Fetch失败，公开网页由web_extract替代成功；自动Recall单次2秒超时，独立同环境无私人主题CLI探针0.562秒成功。模型回答仅为观察输入，root另核真实工具参数、日志和持久结果，不按模型自报签功能通过。
- 独立Validation计划后的只读Pi冷Timeline→Files共享目录→同owner/route→study/Alex恢复与图标截图已补，该UI包额外模型输入0/Conversation0。旧Pi043当时idle而未close；后续原生已不在Runtime列表，不归功为本次手动回收，不擅自操作用户旧会话。
- 配置8文件双向及完成包1ZIP单向已watching，SOUL未写、秘密不回传；云300秒timer已真实触发，Mac300秒/到件receiver已真实落Alex/state.db、study/state.db、现有Alex/projects.db，完整字节/逐表对账与源包一致，initial原Pi inode保留。实际同包幂等、仅暂停新snapshot lane而云继续发布、恢复追上及自动落库已通过；不冒称真关机/整网断线测试。
- 最后已备份旧Pi同步配置，仅按五个已核ID暂停/终止，剩新三lane不变；不删用户文件、不重启daemon。最新02:15云发布与Mac接收包SHA `8f97164a61432359021abcc0ff0c310ac3fae4785d791b867ab0dea9ed6e1c13`相同。两自有真实Chrome页已关闭，用户原三页保留；原自有隐藏页与SSH转发早已清理，云服务没有停止。
- 运维入口：[部署SOP](../../docs/cloud-deployment-sop.md)，含实际PM/unit/Caddy JSON、Profile/模型/目录、周期接收与安全恢复。详细受限证据位于ignored `deployment-release-20261019/cloud-deployment/`、`sync/activation/`及新增`final-acceptance-20261019/{browser,ops,nm-diagnosis}/`，私人正文/密钥不入Git。

## 4. Verification与Validation

Astra/high无主会话历史独立核D01–D14，复用不变v5证据，独立审源码/正式接线/实际原件，未复跑昂贵套。D13源码19不同节点与正式实装收据已关闭；报告时点12条符合，D02 workspace TCC与D11登录后公网证据不足，**未签全轮PASS、未建议停服**。见[Verification](verification.md)§6.2；原独立结论不由root改签。

6.1/high独立从需求建立12目标/12场景计划；root过目后按其最小UI包以唯一允许的隐藏IAB薄执行，审查者独立判定并注明非亲操。真实KimiCode回复/回收、Profile切换、冷历史/Files、Alex图标、同步实际输出均已独立核对；study无会话故侧栏毕业帽未实际呈现，不伪签其视觉。公网登录后和Desktop工作目录不代签。最终受影响结论见[Validation](validation.md)续节，不以配置/测试绿代替用户结果。

上述两份报告先于D15真实Chrome公网/DeepSeek/旧Pi清理包；新增证据由root亲审，补齐实际公网用户结果并揭示Kimi业务失败，不把旧报告倒写成已审新结果，不重新跑大型测试。D02权限未解除，故仍不声明两门禁或全轮关闭。

## 5. 剩余、阻塞与影响

1. **需用户操作：** 允许macOS提示中的Mutagen访问Desktop。workspace正式双向往返尚未通过，自有测试marker仍留Mac，允许后清自有marker再收尾；不删用户文件。
2. **Kimi Search/Fetch业务不可用：** 实际408/403/404；换目标且直连/现有代理均408。现wrapper丢弃非200细节，不能确定鉴权、策略、额度或上游细因；未盲改Key/接口/代理或重启，不能把协议握手通过说成业务成功。Notifier只读发现，不测试真实发信。
3. **NM单次自动召回超时：** 默认2秒预算真实超时；Context Bundle和CLI状态正常，后续一次搜索0.562秒可用，只证明当前路径，不证明原请求应命中或已定位瞬时慢因。没有改预算/提示或补写NM。
4. 既有NO_REPLY静默方案按用户决定仍待决，三类DeepSeek行为观察已获确认非阻断；不借本轮修改Prompt或扩大开发。生产500秒/128K不重跑旧昂贵旅程；实测一次timer自动触发，隔离断传测试人工启动同一正式publisher，不冒称跨两次实际周期的关机测试。手机、多日稳定性和多GB传输性能未验。

## 6. 用户复核与恢复入口

现在直接访问正式首页，按本人Access登录；Alex应为k3-256k/high，可读旧Pi会话、进入Files并返回。New Chat切study应无默认模型，原会话列表仍在。Dashboard使用同域/dashboard/。SOUL保持用户原文，不需要再编辑。

Desktop授权后回复异步问题即可接续workspace实测；尚待授权/待验项目不阻止当前云服务。Mac数据库是冷态副本，暂勿同时把这两Home作为本机第二运行writer；接收器会对打开句柄/sidecar暂停，不删WAL强行覆盖。

可查看[DeepSeek只读自查会话](https://hermes.edgarzhong.fyi/chat/20261019_020701_6a255b?profile=alex)。本轮两次自有模型Runtime、隐藏验收页、真实Chrome两自有页与SSH本地53458转发均已精确清理；旧Pi五同步已关闭，用户历史和云服务保留。剩余workspace marker待权限放行后按精确路径验证和清除。
