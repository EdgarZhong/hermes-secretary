# 云部署交接 · 2026-10-19

## 1. 目标状态与结束判定

**云端服务已部署并持续运行，可由用户直接访问；完整同步目标尚未完成，当前等待macOS Desktop目录授权。** 这不是暂停云服务、也不是整轮PASS。公网真实显示Access登录页；合法登录后的公网双SPA/API/WS仍待用户实际验收，不能由回环成功代签。

阻塞为Mutagen daemon访问用户指定`~/Desktop/Alex`被`tccd`要求Desktop隐私权限，已通过异步问题请用户亲自允许；禁止代点、绕过TCC或自行改目录。恢复第一步：用户允许后只接续本项目workspace lane，完成自有marker双向/删除对账，再执行用户授权的旧Pi同步最后清理。期间网站、配置同步和数据库回传继续工作。

## 2. 本轮收敛与授权

用户定案SOUL原字节、双物理Home、单数共享workspace、Alex原Pi库、study自己NM Space/无默认模型、Kimi Code独立k3-256k/high、可选DeepSeek/MCP、500秒/128K联合Idle、每300秒数据库快照与本机冷库目标均保持。用户后续明确先上线供其访问，门禁和同步收尾不作为停服前置；旧Pi同步可清除但留最后。

原生型号元数据自动兜底256000与正式目录262144不同；root按目录事实仅补Alex `model.context_length:262144`，不改型号/Provider，原生API热合并、PID不变。Astra独立核判满足独立型号/精确容量要求，但自动识别未被修好。新session附属`profile_name=custom`为原生物理Home推导；正式API owner=alex与数据库隔离有效，不改旧历史字段或扩大Core开发。

## 3. 已完成与交付物

- 入口：[Secretary](https://hermes.edgarzhong.fyi/)；[Dashboard](https://hermes.edgarzhong.fyi/dashboard/)。后台专属systemd active/enabled，唯一backend/proxy回环53446/53448；Access保护五页面/API/WS入口匿名302，原Tunnel四路由和其它服务不变。
- 云Core固定d215922；官方PM frozen rc0/Python3.14.7，lock与固定提交一致。两前端只上传439/67份静态产物，完整集合/SHA已核，用户UI overlay保持；UI窄提交d5b20aab。个人Provider a722生产字节保持，周期实现5c7fad17、状态文档/远端892c6bf2，两端helper SHA8e1ecc2d…e97a4。
- 两SOUL SHA逐字保持，Home为`~/.hermes_profiles/Alex`和`study`，native owner alex/study。Alex原48会话6065消息按正式workspace.move迁共享cwd，原文/UID/Ref/root/binding/origin及原Mac cwd来源保持；study初始空库。
- Alex实际页面显示k3-256k/high，唯一真实KimiCode短输入API1次、17824输入/34输出/0工具，页面收到“连接成功”；正式close该自有测试runtime/lease0，历史2条保留。MCP真实initialize/tools/list含Kimi Search/Fetch/Notifier，未发送业务通知；DeepSeek可选非默认。study无默认，切换仍保留全部历史列表。
- 独立Validation计划后的只读Pi冷Timeline→Files共享目录→同owner/route→study/Alex恢复与图标截图已补，额外模型输入0/Conversation0。旧Pi043存在idle Runtime，无法证明仅root持有而保留，lease0/lock0，不冒称全宿主Runtime0。
- 配置8文件双向及完成包1ZIP单向已watching，SOUL未写、秘密不回传；云300秒timer已真实触发，Mac300秒/到件receiver已真实落Alex/state.db、study/state.db、现有Alex/projects.db，完整字节/逐表对账与源包一致，initial原Pi inode保留。实际同包幂等、仅暂停新snapshot lane而云继续发布、恢复追上及自动落库已通过；不冒称真关机/整网断线测试。
- 运维入口：[部署SOP](../../docs/cloud-deployment-sop.md)，含实际PM/unit/Caddy JSON、Profile/模型/目录、周期接收与安全恢复。详细受限证据位于ignored `deployment-release-20261019/cloud-deployment/`、`sync/activation/`、`browser/`，正文/密钥不入Git。

## 4. Verification与Validation

Astra/high无主会话历史独立核D01–D14，复用不变v5证据，独立审源码/正式接线/实际原件，未复跑昂贵套。D13源码19不同节点与正式实装收据已关闭；当前12条符合，D02 workspace TCC与D11登录后公网证据不足，**不签全轮PASS、不建议停服**。见[Verification](verification.md)§6.2。

6.1/high独立从需求建立12目标/12场景计划；root过目后按其最小UI包以唯一允许的隐藏IAB薄执行，审查者独立判定并注明非亲操。真实KimiCode回复/回收、Profile切换、冷历史/Files、Alex图标、同步实际输出均已独立核对；study无会话故侧栏毕业帽未实际呈现，不伪签其视觉。公网登录后和Desktop工作目录不代签。最终受影响结论见[Validation](validation.md)续节，不以配置/测试绿代替用户结果。

## 5. 剩余、阻塞与影响

1. **需用户操作：** 允许macOS提示中的Mutagen访问Desktop。workspace正式双向往返尚未通过，自有测试marker仍留Mac，允许后清自有marker再收尾；不删用户文件。
2. 用户自行登录公网入口验收；当前只证明真实Access登录页与云反代实际UI/API/WS、模型链路，未证明跨Access的登录后链路，不索取用户OTP。
3. 旧Pi五条Mutagen仍原样保留，作为新workspace收口后的最后清理任务，只按已核精确ID停止/清除，不删同步目录或其它服务。
4. 既有NO_REPLY静默方案按用户决定仍待决，三类DeepSeek行为观察已获确认非阻断；不借本轮修改Prompt或扩大开发。生产500秒/128K不重跑旧昂贵旅程；实测一次timer自动触发，隔离断传测试人工启动同一正式publisher，不冒称跨两次实际周期的关机测试。手机、多日稳定性和多GB传输性能未验。

## 6. 用户复核与恢复入口

现在直接访问正式首页，按本人Access登录；Alex应为k3-256k/high，可读旧Pi会话、进入Files并返回。New Chat切study应无默认模型，原会话列表仍在。Dashboard使用同域/dashboard/。SOUL保持用户原文，不需要再编辑。

Desktop授权后回复异步问题即可接续workspace实测；任何尚待授权/待验项目都不阻止当前云服务。Mac数据库是冷态副本，暂勿同时把这两Home作为本机第二运行writer；接收器会对打开句柄/sidecar暂停，不删WAL强行覆盖。

本轮自有隐藏验收页与SSH本地53458转发已精确关闭；没有停止云服务或关闭用户旧Pi Runtime。
