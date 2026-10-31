# Linux 上云部署 SOP

本文适用于独立 Secretary Web SPA＋原生 Hermes Web Dashboard、同源双 SPA、单后端和原生多 Profile。用户已于 2026-10-19 放行部署；本文记录操作口径，不以模板、上传或本机门禁代表云端成功。当前进度与待办只在根 [CLAUDE.md](../CLAUDE.md)，本轮依据及验收入口在 [Snapshot Index](../.autonomous/20261019-cloud-deployment/snapshot-index.md)。架构见 [06 §0.7–0.8](06-Hermes-Secretary-Web-UI-V1-Spec.md#07-confirmed-deployment-topology-and-dual-spa-routing-2026-10-17)、[08](08-profile-scheduler-files-clarification.md)。

## 数据库备份保留

按用户2026-10-24确认，云端历史数据库备份只保留最近两套完整host／Alex／study三库。新备份校验并发布确认后，将更旧的部署／调试数据库副本及对应WAL／SHM清退列为部署收尾；精确按备份清单删除，保留轻量收据，不额外复制或压缩待删库。清退前核保留两套的完整性／SHA及无活动引用，禁止触及运行库。配置备份和旧前端资源按各自任务处理，不随数据库清理扩大范围。

`.hermes_profiles/.snapshots/databases-current.zip`是每五分钟覆盖的云→Mac同步完成包，不是累积的历史备份；保留既有发布／同步链，不因数据库历史只留两套而删除它。实际保留版本、执行记录及释放空间见运维记录。

## 0. 首尔正式入口的认证运维

首尔 Hermes 正式入口为 `hermes.edgarzhong.fyi`，使用 Authelia 双因素认证。旧 `test.edgarzhong.fyi` 已废弃，直接返回404。`eb-data.edgarzhong.fyi` 由 Caddy 反代 `127.0.0.1:8787`，保留 Ebbinghaus 原生 Bearer 鉴权，不套浏览器双因素跳转；`nmem.edgarzhong.fyi` 反代 `127.0.0.1:14242`，保留NM原生API令牌认证。三个域名均使用仅DNS的首尔A记录。

首尔 Hermes 使用 `ubuntu` 服务布局、Caddy 公网 HTTPS；`auth.edgarzhong.fyi` 仅提供认证门户。本节描述现用首尔入口；下文的 `/root`、旧`alex` 与 Cloudflare Tunnel／Access 布局属于北京历史模板，不直接套用到首尔机。第二台首尔正式机的迁移按§0.1；当前迁移进展只记根 `CLAUDE.md`。

首尔稳定布局：Hermes仓库 `/home/ubuntu/hermes-secretary`，控制根 `/home/ubuntu/.hermes`，两实体Home `/home/ubuntu/.hermes_profiles/{Alex,study}`，通过控制根的 `profiles/{alex,study}` 注册；保留原生default，不通过前端隐藏规避身份解析。Ebbinghaus位于 `/opt/ebbinghaus`；NM官方0.10.101运行程序保持 `/usr/lib/Nowledge Mem`，原生四数据根保持原路径，`nmem.service`以root运行、只监听本地14242，客户端ubuntu使用自己的受限官方连接配置。NM使用阿里云专属Host的 `/compatible-mode/v1`、`qwen3.7-text-embedding`／1024维，启动器从 `/etc/secrets/dashscope.key` 读取Key，不加载本地GGUF；更换模型后必须原生reindex，不能因维数相同跳过。

同步专用Host `hermes-secretary-sync` 和日常`alex`均指正式首尔`43.128.131.30`／ubuntu，私钥为本机受限`~/.ssh/alex_vps.pem`；`seoul`为已废弃、待回收的原实验机入口，不作为生产／同步源。workspace为正式Alex `/home/ubuntu/workspace` ↔ Mac `/Users/edgar/Desktop/Alex` two-way-safe；配置只传8白名单文件；DB完成包由正式Alex `.hermes_profiles/.snapshots/databases-current.zip` 单向传Mac，再由既有接收器核验后落冷库。首尔快照timer每五分钟独立发布，Mac离线不阻塞源发布；不得把rawDB改成双向同步。切换时暂停旧lane、核定当前源配置、预对齐后启用，按真实marker往返、配置SHA、自动快照落地验证，不能只看connected。实际版本和收据见根CLAUDE。

study使用原生`openai-codex`及ChatGPT订阅独立设备码授权，凭据只留实体Home的`auth.json`（0600），不在同步白名单、不导入Mac Codex登录态。默认`model.default: gpt-6-sol`、`agent.reasoning_effort: high`；`delegation.model: gpt-6.1-sol`同时覆盖普通子Agent与后台delegate_task，Provider／凭据及High沿原生继承。Noting按父冻结运行态继续使用主模型，不受delegation覆盖；已有Conversation仍遵循各自持久模型配置。当前部署版本在空命名Profile上首次`auth add`可能误报成功而未存凭据，首次授权优先使用`hermes -p study model --no-browser`中的订阅登录入口；最终须核Profile级凭据落盘、正式runtime解析与实际请求，不能只看成功提示。实际绕行与证据见运维记录。

Authelia 使用官方二进制，`/etc/authelia/configuration.yml` 仅在 `session` 下增加：

```yaml
redis:
  host: /run/redis-authelia/redis.sock
  port: 0
  database_index: 0
  timeout: 2s
  max_retries: 0
```

Web系统服务的 Provider 密钥由 systemd `LoadCredential` 从 `/etc/secrets/{kimi-code,deepseek}.key` 读取，启动 wrapper 在进程内注入原生 Provider 环境，不把 Key 放入 argv、仓库或非受限配置。**多Profile Gateway不继承启动进程的Provider密钥**：路由到Alex后，原生凭据作用域只读取该Profile的`.env`及正式外部凭据源；单凭`/proc/<pid>/environ`中存在Key不能判定可用。Alex的`KIMI_API_KEY`通过原生`save_env_value`保存到实体Home的受限`.env`（0600），不加入同步白名单或Git；注册路径`~/.hermes/profiles/alex`与实体路径`~/.hermes_profiles/Alex`指向同一Home。Gateway使用原生启动入口，不额外复制凭据到`~/.config/hermes-secrets/`或添加Provider注入drop-in。轮换Key时须同时核对Web服务和Profile级配置这些实际消费者，不放宽作用域隔离；以正式`_profile_runtime_scope`内Provider解析及真实认证验证，不能只查进程环境。每次入站重建Profile作用域，单独更新该`.env`无需重启Gateway。

Alex 的 Kimi Tools 项目位于 `~/tools/kimi-tools/`，复用同一 Kimi Key，Search/Fetch 地址为官方 `https://api.kimi.com/coding/v1/{search,fetch}`。Playwright MCP 通过 npm 安装；无头 Chromium 的精确安装路径使用专用 AppArmor userns 配置，保留浏览器沙箱，不修改系统全局 userns 限制。

当前普通会话有效期与“记住我”均为 `31d`，空闲期限保留 `5d`：每天正常访问时不再因漏勾“记住我”走12小时期限，符合2026-10-21用户确认的至少一个月免重复登录目标；连续5天无认证访问的普通会话仍会失效，“记住我”按Authelia原生语义不受空闲期限制。期限用于新签发会话，不把已失效的旧Cookie恢复为有效。Cookie作用域、双因素规则和会话密钥保持；实际变更、证据与回滚见[运维记录](operations-log.md)。启用Redis后不再使用Authelia的进程内会话存储；首次切换需重新登录一次。会话密钥仍只保存在受限云端配置中，不复制到仓库或输出日志。

- 专属服务为 `redis-authelia.service`，配置 `/etc/redis-authelia.conf`，数据 `/var/lib/redis-authelia`。系统包默认 `redis-server.service` 停用，避免运行第二实例。
- Redis `port 0`，仅监听上述 Unix socket；目录 `redis:authelia 0750`、socket `redis:authelia 0770`，普通用户无访问权限。不开放 Redis TCP 端口。
- 使用 AOF、`appendfsync everysec`；正常重启会话可保留，非正常断电仍有最近约一秒写入的持久化窗口。Redis `maxmemory 64mb`、`noeviction`，systemd `MemoryMax=128M`，不靠驱逐有效会话腾空间。
- `/etc/systemd/system/authelia.service.d/redis-session.conf` 用 `Wants`／`After` 启动并排序专属 Redis；Authelia 失败后重试。Redis 短时不可用时鉴权拒绝，恢复后继续读取原会话；不会回退为绕过认证。
- 切换前备份在 `/var/backups/authelia/redis-session-<timestamp>/`，其中 `rollback.sh` 仅恢复该次原 Authelia 配置并移除本次 drop-in，再重启认证服务。回滚会切回内存会话，并再次要求登录，不处理 Hermes 数据库或前端产物。

只读检查入口：

```bash
sudo systemctl is-active authelia redis-authelia
sudo -u authelia redis-cli -s /run/redis-authelia/redis.sock PING
sudo redis-cli -s /run/redis-authelia/redis.sock INFO persistence
sudo systemctl show authelia redis-authelia -p MainPID -p NRestarts
```

会话修复验证应覆盖已登录／匿名请求交错、记住我开关、认证服务重启、Redis 正常重启和不可用后恢复。故障注入优先使用独立虚拟账号／数据库和回环认证实例，不在正在使用的用户会话上重复制造故障。浏览器验收需遵守本轮明确显示授权；不把隔离测试冒称手机锁屏或长期运行实测。

## 0.1 第二台首尔正式服务器迁移SOP

本节用于**现用首尔临时机→第二台首尔正式机**，覆盖Hermes、Nowledge Mem（NM）、艾宾浩斯数据服务及共同依赖。新机沿用Alex名称；SSH别名使用`alex`，不代表把Hermes的Alex Profile改名。正式机已完成迁移，执行结果与原实验机废弃／待回收状态见运维记录。旧北京机已关闭，不能作为本轮数据源；其历史模板／备份只作追溯。

**本轮认证口径（2026-10-26用户确认，优先于下方通用保会话步骤）：** NM和艾宾浩斯复用现有API token；Authelia保留原账号、密码hash、2FA注册／TOTP及其持久库和加密密钥，但不继承旧登录会话／放行记录。新机Redis从空会话状态启动，不导入源机AOF会话；切换后重新登录。源机认证数据留作回滚，不因不迁会话扩大删除持久身份或轮换两服务API token。

**本轮复制／安全范围（同日用户确认）：** 本机如需中转，数据／归档／临时备份放仓库外独立私有目录，禁止放进任何Hermes Secretary相关目录；本轮目录为`~/Library/Caches/alex-migration-20261026`（0700）。NM正常停服后直接复制原生数据库、WAL等附属文件／索引及完整四数据根，不使用NM提供的导入／导出数据包功能。监测、健康检查、小工具、timer／cron一并迁移；网络安全有效策略与源机统一，腾讯云TCP443由用户放行，主会话验证主机内防火墙及公网连通。SSH host key和当前登录公钥属于新机身份，禁止拿旧机身份文件覆盖；健康检查自动拉起在业务恢复后启用。

### A. 固定源和目标、盘点范围

| 对象 | 盘点与迁移要求 |
|---|---|
| 源临时机 | 已废弃、待回收实验机`seoul`（原IP `43.128.156.186`），用户`ubuntu`；`hermes-secretary-sync`已切新机，不能再用它执行源端命令。以实际运行进程、systemd unit、配置和文件为准记录版本／路径／所有者／权限／容量，不能只看仓库HEAD |
| 目标正式机 | `alex`→`43.128.131.30`／`ubuntu`，新专用私钥`~/.ssh/alex_vps.pem`（0600），已实测登录；架构x86_64／Linux内核6.8。OS为Ubuntu24.04，实际环境已核；初次连接主机密钥仅按原生首次信任留存，仍须与云控制台可信指纹核对。未复用已回收北京密钥，SSH配置本体仍在`~/dotfiles`并由软链接引用 |
| Hermes | Core及个人插件实际commit／dirty、本机对应可恢复源码、配套双SPA产物及完整SHA清单；官方PM、现有lock和运行依赖。新OS原生建环境，不复制Mac或旧主机`.venv` |
| Hermes持久状态 | 控制根`/home/ubuntu/.hermes`、实体Home`/home/ubuntu/.hermes_profiles/{Alex,study}`及profile注册软链接；host／Alex／study三运行库、Conversation身份／历史／Notebook／排期／Heartbeat／pending／渠道绑定、实际引用的附件／媒体、workspace、Skills和规则。控制根还存在`kanban.db`、`shared-state.db`、pairing、pending_messages、hooks、auth等，须逐项判定持久状态并纳入正式迁移清单；不能只复制`state.db`或8文件同步白名单，也不因此扩大日常同步范围 |
| Hermes配置／凭据 | Profile配置与SOUL、`.env`、study原生`auth.json`、Web machine token、微信adapter凭据／绑定文件、`/etc/secrets/`实际消费者、服务unit／drop-in、启动wrapper、语音转录／上传及解码依赖、`~/tools/`和`~/scripts/`实际工具。受限传输／恢复原权限，不能进入Git／公开日志，不能混用Profile凭据 |
| NM | 官方程序`/usr/lib/Nowledge Mem`；四数据根`/root/.local/share/NowledgeGraph`、`/root/.config/co.nowledge.mem.desktop`、`/root/.nowledge-mem`、`/root/ai-now`。覆盖图／正文／usage／SQLite等存储、搜索索引、Spaces／认证／远程LLM配置、CLI状态和Working Memory／归档／Skills／Library源文件。服务配置、ubuntu客户端连接配置／token及`/etc/secrets/dashscope.key`单独核权限。不能用Memory导出或只复制图数据库替代完整恢复 |
| 艾宾浩斯 | `/opt/ebbinghaus`源码／lock与实际运行依赖；权威库`/opt/ebbinghaus/data/ebbinghaus.db`及WAL／SHM；环境文件`/etc/ebbinghaus/server.env`、Bearer token及服务配置。现启动链使用`runtime/node-v24.21.0-linux-x64/bin/node`→server内tsx→`server/src/index.ts`，Node约束`>=24.21.0 <25`，better-sqlite3须匹配新机架构和Node ABI；不能把旧原生模块直接用于异构新机 |
| 公网与认证 | Caddy配置／实际版本／TLS存储；Authelia配置、用户文件、二次认证数据库及加密／签名／session密钥；专属Redis配置和完整持久化集合。保留Cookie域／期限及NM、eb-data原生API认证，不能只迁移登录页 |
| 同步与外部消费者 | 三条Mutagen精确ID／端点／模式／ignore／8文件白名单；源快照service／timer、Mac冷库接收器；所有使用`hermes`／`auth`／`nmem`／`eb-data`域名或旧IP的客户端、API调用、MCP、Web／APK与脚本 |

在受限运维目录记录新旧机映射、运行版本、配置路径及SHA、三服务数据清单、DNS A／AAAA／代理状态／TTL、各服务启动命令和恢复点；公开运维记录只保存脱敏摘要和入口。凭据文件只核权限、存在性和安全指纹，不输出内容。迁移沿现有产品配置，不顺带升级NM、换embedding模型、改Profile语义或迁OpenClaw。

**服务作用域现场核对表：** Hermes Web是系统级`hermes-secretary.service`（User=ubuntu、cwd=`/home/ubuntu/workspace`），Gateway是ubuntu**用户级**`hermes-gateway.service`，不能在系统级查不到它就视为停用。NM为系统级`nmem.service`（root、cwd=`/root`），艾宾浩斯为系统级`ebbinghaus-sync.service`（cwd=`/opt/ebbinghaus`），另有`hermes-secretary-snapshot.timer`和认证相关unit。目标要恢复实际systemd层级及用户Linger／自启，不按名字猜作用域。

**NM版本与认证待核：** 历史验收为官方0.10.101，正式迁移前重新取运行程序真实版本；包管理器未识别版本不能用历史记录冒充当前证明。NM远程LLM／认证加密配置跨机可移植性、Authelia实际storage／用户文件及secret绑定、Caddy证书存储／续签、NM全部写入客户端、艾宾浩斯全部设备／外部消费者、当前完整数据体积均须现场核清，缺失项明确保留，不能虚构默认路径。现机路径已确认不等于已具备全套恢复证据。

**艾宾浩斯客户端边界：** V2 macOS／Android客户端持有完整本地SQLite，后台经HTTP同步到云端权威库；`server_seq`游标、设备身份、outbox和连接凭据留客户端。迁移窗口前核各设备已上传／待上传范围，正常完成已有同步后暂停新增同步写入；离线设备的待上传数据仍留原客户端，恢复后核幂等接续和游标，不把本地工作库或旧V1测试库覆盖到云端。客户端契约见Ebbinghaus-v2仓库README与部署留档，其中旧北京`ssh alex`／Tunnel拓扑不作现入口依据。

### B. 新机准备与预复制（源保持服务）

1. 新机完成SSH／sudo、时间同步、磁盘及防火墙准备；明确数据容量、临时归档空间和恢复空间。保持现有Linux用户／目录布局可减少路径改写；若目标布局不同，先列出软链接、unit、wrapper、AppArmor／Chromium路径和客户端配置的完整映射，不能全局字符串替换。
2. 安装源机对应版本的运行程序及依赖：Hermes官方PM环境／lock、配套双SPA、NM官方程序、艾宾浩斯环境、Caddy／Authelia／专属Redis。固定服务用户、UID／GID权限及`LoadCredential`消费者，验证配置语法；目标后台任务及Gateway暂不启用。
   Hermes不能只重建项目`.venv`：原生Gateway启动器使用`HERMES_HOME/installs/<install_key>/facts.json`及已保存workspace／lock、feature／plugin选择。迁移这些登记与记录后用官方`pm repair`重建原生已提交环境，不复制旧venv，也不伪造facts或改Gateway启动路径绕过PM；核实际Web／Gateway运行版本和control socket就绪后再算恢复。按深层路径打包时也须恢复所需父目录的源所有者／权限（尤其`~/.local`、`~/.local/state`），不能只校子文件SHA。
3. 可先传静态源码／产物、依赖清单和大文件；活跃数据库／NM文件的首轮拷贝只是预热，不能作为切换快照。通过已核主机身份的SSH受限传输，不能把凭据塞进命令行、Git或共享包。最终数据包须有相对路径清单、文件SHA及所有者／权限／软链接信息。
4. 以回环或自己建立的SSH转发预验新机，不提前改生产DNS。恢复副本的Hermes不能连接真实微信、启动Scheduler／Heartbeat／Noting等写入任务；NM副本不得启动会写数据的后台工作。使用正式入口的只读检查，并留意启动本身可能升级Schema／产生任务；必须先固定兼容版本和恢复副本。
5. 核定迁移窗口和未完成工作：活动Turn／Noting／委派、到期Reminder／Heartbeat、NM索引／后台任务、艾宾浩斯请求，以及同步冲突。准备需要暂停／恢复的精确unit／timer／session清单和源机恢复顺序。此阶段源机仍是唯一生产写入方。

### C. 停写与最终一致副本

1. 暂停三条Mutagen的精确session并保存模式／端点／过滤规则，暂停源快照timer，避免最终快照期间Mac双向修改或旧完成包覆盖新冷库。保留Mac已验`current`／`previous`及当前完成包，不把Mac冷库当最新源。
2. 从已记录的公网入口暂时挡住新写入，防止Web、微信、NM客户端和艾宾浩斯外部请求继续写。等待活动Turn／Noting／委派自然结束；再停源Hermes Web／Gateway及实际后台写入者，停止NM写入／索引和艾宾浩斯服务。停服顺序按现场unit及依赖核对，不能凭服务名字猜测或使用广域`pkill`。
3. 停止Authelia写入和专属Redis后，保存Redis完整AOF／RDB集合及manifest（现AOF目录`/var/lib/redis-authelia/appendonlydir`）、Authelia二次认证库／用户配置／密钥。NM正常退出、确认无残留写入进程／打开写FD后保存四数据根的完整同批副本；嵌入式多文件数据库不能从运行中文件随意拼接。各SQLite用既有backup接口或已确认无写入的完整停服副本，记录WAL／SHM处理结果，不能只拷主文件遗漏已提交WAL，不能删除WAL／SHM来伪造干净停机。
4. 把源最后快照与预复制差量对齐，核清单／SHA、权限／所有者／软链接、各SQLite完整性及foreign_key_check基线。跨独立库不声称事务原子性；停写窗口内固定共同业务边界，记录截止时间及待处理任务状态。NM对每种数据存储做对应完整性／打开验证，不把SQLite检查套到全部存储。
5. 新机保持生产写入关闭，恢复相同路径和权限，逐服务核数据／schema／原生启动解析、回环只读API和认证拒绝边界。源最终副本、配置和源码／静态配套版本保持可恢复；此时发现问题，直接继续用源机，无须切DNS。

### D. 切换域名、后台owner与同步

1. 新机受保护的Caddy／认证先就绪，检查`hermes.edgarzhong.fyi`、`auth.edgarzhong.fyi`、`nmem.edgarzhong.fyi`、`eb-data.edgarzhong.fyi`的证书、正确Host路由和匿名拒绝；NM和艾宾浩斯仍沿原生token认证。检查A及AAAA，避免遗漏旧IPv6记录；是否有代理以源实际配置为准。
2. 旧机继续拒绝外部写入且后台保持停止，切四域名的实际DNS记录到新机；传播期间不能让缓存旧IP的客户端把写入留在源机。必要时旧入口维持明确维护状态；采用旧机转发新机须单独核实际配置，不作为默认已实现能力。保留原记录／TTL供回滚。
3. 确定新机成为唯一生产数据owner后，按依赖启动NM／艾宾浩斯，再启动Hermes Web／Gateway和其后台任务。核微信只有一端在线、原Conversation绑定保持，Scheduler／Heartbeat／pending经原生语义恢复，不手动重放所有错过任务；源快照timer保持关闭，新机独立发布。
4. `alex`固定指新正式机；切`hermes-secretary-sync`前保持旧session暂停，留存旧主机可恢复连接入口。虽然别名字符串相同，远端owner已改变，不能直接恢复旧Mutagen archive；核对预对齐结果后按已保存模式／ignore重建三lane，避免旧归档的删除／冲突解释带到新机。SSH主机指纹须独立核对，不关闭StrictHostKeyChecking。
5. workspace真实marker创建／修改／删除往返；配置只核定的8文件SHA并验证双向、`.env`／auth／cache／raw DB仍排除；快照只传稳定`databases-current.zip`，等待新机timer自然发布及Mac接收器校验host／Alex／study三库。保留坏包／忙库保护，不让过期包反盖新库；单纯connected不算迁移成功。

### E. 验收、回滚与回收

| 范围 | 最少证据 |
|---|---|
| Hermes | 进程实际版本／配置；两SPA、API／WS；两个Profile和当前Conversation完整恢复；历史／身份／Notebook／排期／Heartbeat／pending／微信绑定指纹；受引用附件和workspace可读；Provider／工具解析。不通过生产合成消息或新增真实模型调用验证，除非本轮另有明确授权 |
| NM | 受原token保护的正式status、Memory／Thread／Space／关系及资源的数量与抽样只读内容；图／向量／正文存储可读；同embedding模型／1024维和云Host解析正确。迁移保持同模型且完整索引时先验证，不无条件重建；若实际缺索引／变模型再按原生流程处理，真实embedding请求和成本单独记录 |
| 艾宾浩斯 | 健康检查、原Bearer认证成功／未授权拒绝、数据库完整性／schema及记录数量、只读抽样内容；原客户端继续使用同域名和token。服务启动不等于真实读写业务验证；有必要的写入验证先用隔离副本或单独确认 |
| 认证／同步 | Authelia匿名拦截、二次认证数据、原Cookie适用条件及Redis持久化加载；TLS／四域名／DNS；三lane正式数据往返、自动三库完成包与Mac冷库新鲜度。登录页302不等于原登录态保留成功 |

界面仍只允许自己创建的隐藏IAB；无合规登录态或手机实测条件时明确记未验，不操作用户页面。原Authelia会话只有在Cookie域、session密钥、Redis数据、软件兼容和期限均满足时才可能保留；迁移是否免登录必须实测，不能先作保证。启动／恢复出现问题，先保留日志及原数据，不清库重建或回盖旧快照。

Authelia现有“启用Redis前”的`rollback.sh`会切回内存会话并重新要求登录，只适用于那次配置变更，不能用作本轮跨主机迁移回滚脚本；不迁移登录态须先明确接受重新登录，不能由Agent自行省略该数据。

**回滚分两种情况：** 新机尚未接受生产写入时，停止目标服务，恢复原DNS／同步端点和源机服务即可，仍只允许一端生产写入；新机已经接受任何写入时，必须先冻结目标、留存新写入和最终副本，核兼容性并完成回迁／数据对账后才能恢复源机。仅把DNS改回旧机或拿旧快照覆盖会丢失新数据，不能作为此阶段回滚步骤。DNS传播期间两端始终避免同时接收业务写入。

三服务、认证、真实消费者及同步验收确认完成后，才回收临时首尔机服务、旧同步lane／SSH密钥和云资源。云端Hermes历史三库备份遵守最近两套完整集合的既有规则，NM／艾宾浩斯恢复包不混入该计数、不借此扩删；不删除唯一恢复点。记录实际迁移／回滚结果到operations-log，当前状态更新CLAUDE。


## 1. 原北京部署模板与生产配置口径

**§1–§8保留原北京部署／初次验收时的模板和证据语境，出现`/root`、`~/scrips`、旧`alex`、Tunnel及旧unit时不能作为第二台首尔的执行命令；首尔迁移执行以§0及§0.1的现场清单为准。** 下文仍有效的快照、权限、单写入端和验收契约继续沿用；历史“完成”不代表本轮完成。

下方模型表保留初次部署模板；Alex默认及当时置顶Conversation于2026-10-24变更为`kimi-coding/k3.1-pro`，当时使用262144上下文、High、原生Chat路由。这里不把当时窗口冒称现值；后续实际变更、官方额度核对和回滚点见[运维记录](operations-log.md)。

本节为原北京部署模板（首尔运行布局按§0），不是当前主机选择。模板服务用户为 `root`，HOME 为 `/root`，当时SSH alias为`alex`，现已回收；未来新首尔同名alias不能用于执行本节的北京路径命令。原机Ubuntu 24.04 / x86_64；不要把本机虚拟环境复制上云。

| 用途 | 云端 | Mac |
|---|---|---|
| Core 仓库 | `/root/hermes-secretary`，官方 PM 与既有锁 | 开发仓不整体同步 |
| 原生控制根 | `/root/.hermes` | 本轮不注册本机默认根 |
| Alex 物理 Home | `/root/.hermes_profiles/Alex`，保留大小写 | `/Users/edgar/.hermes_profiles/Alex` |
| study 物理 Home | `/root/.hermes_profiles/study` | `/Users/edgar/.hermes_profiles/study` |
| 共享工作目录 | `/root/workspace`，单数 | `/Users/edgar/Desktop/Alex`，双向同步 |
| 双 SPA 静态目录 | `/root/.local/share/hermes-secretary/static/{secretary,dashboard}` | 仅交付 dist 和外置完整 SHA 清单 |
| SQLite 完成包 | `/root/.hermes_profiles/.snapshots/databases-current.zip` | `~/.hermes_profiles/.snapshots/databases-current.zip`，云→Mac |
| 云快照暂存 | `/root/.local/state/hermes-secretary-snapshot-staging`，同步树外 | 接收验证暂存也必须在同步树外 |
| 本机已验快照 | 不作运行库的替代来源 | `~/.local/state/hermes-secretary-known-good/{current,previous}.zip` |
| 独立工具 | `/root/scrips/nmem-memory.py`、`hermes-sqlite-snapshot.py` | 同为 `~/scrips/`，独立于 Hermes |
| 正式入口 | `https://hermes.edgarzhong.fyi/`、同域 `/dashboard/` | Cloudflare Access 登录后访问 |
| 回环端口 | Hermes `127.0.0.1:53446`；Caddy `127.0.0.1:53448` | 不把云回环端口直接公开 |

数据库只有云端一份运行主库；Mac 对应 `Alex/state.db`、`study/state.db` 是经校验更新的冷态副本，不能同时启动为第二写入端。首次上传 Pi 导入库与日后快照回传是两个动作，不通过放开 raw DB 双向同步实现。

| 项目 | Alex | study |
|---|---|---|
| 初始历史 | Pi 导入 48 会话 / 6065 消息，保留 Ref、UID、root、binding 和来源 | 新库，不混入 Pi 或合成测试历史 |
| 显示与原生 owner | 显示 `Alex`，canonical owner `alex`，复用现主助手头像 | 显示 / owner `study`，复用复习图标 |
| 默认模型 | 原生 `kimi-coding` / **`k3-256k`**，reasoning `high` | 不写默认模型，不继承 Alex 默认或测试模型 |
| 可选模型 | DeepSeek 可选、非默认；用户已允许其本机 Key 上云 | 不因部署新增默认模型 |
| 上下文节省 | 联合 Idle Compact＋Noting，500 秒、131072 tokens | 不加本轮新增 Idle 参数 |
| NM | `space: default`，`archive_enabled: false` | 自己的考研 Space，`archive_enabled: true` |
| NM Thread 目标覆盖 | 不擅自增加 | 不配置 `thread_sync_space`；保留该功能但沿自己的 Space |

Kimi Code 的目录已核：`k3-256k` 是独立型号，窗口 262144；`k3` 是另一型号，不能用它加窗口覆盖冒充。云内复用与 Pi 现默认对应的既有 Kimi Code Key，走 Hermes 原生 Provider，不改为 Moonshot 平台 API、custom 或 Codex 旁路。原生自动元数据曾落256000兜底；保持正确型号，显式按正式目录补齐`model.context_length: 262144`，不据此宣称自动识别已修。该配置已通过原生API热合并，未重启服务。Alex 配置应含：

```yaml
model:
  provider: kimi-coding
  default: k3-256k
  context_length: 262144
agent:
  reasoning_effort: high
noting:
  enabled: true
  idle:
    enabled: true
    delay_seconds: 500
    threshold_tokens: 131072
compression:
  idle_compact_after_seconds: 0
```

最后一项避免另一个原生 idle compact 定时机制与联合机制冲突，不关闭原生正常压缩。两 Profile 既定 Noting / Scheduler 保留；不得带入测试 5 秒、100000 tokens、600 秒一天或关闭 code-skew guard 的配置。

两份 SOUL 已由用户定案，只按原字节上传、核 SHA，不重写或格式化：Alex `f260652e36b478687605721d8b7850a0a057769cc36aefb0aa1856e0129d56f1`；study `8d88f3c9abea47dcc020245924be2862d87037c96bc29650ade32edd60a0148d`。原文和凭据只留受限运行环境 / ignored 证据，不入 Git。

## 2. 版本、产物与证据绑定

每次部署先记录 Core / 插件 commit、UI 功能 commit＋受保护用户 overlay、双 dist 完整文件集合及 SHA、工具 SHA、PM 解释器 / lock、配置与 SOUL 指纹。升级后重新绑定，不拿历史产物代签新源码。

本轮已收到的绑定如下，**不代表运行服务已加载这些字节**：

| 对象 | 绑定 |
|---|---|
| Core 云安装记录 | `d215922256a479f7cb7346cef59a234bb71dd1b0`；官方 PM frozen 构建 rc0、Python 3.14.7，lock 与该提交一致 |
| UI 窄提交 | `d5b20aab1fb5e7ecf1c3cf10ed476b5ab7b22c99`，仅四任务文件；裸 commit 不含完整用户 overlay |
| UI 实际构建输入 manifest SHA | `f4603149b04fd4262947eddf23481e2c5bbdcce7ca66d5c3c4e29eae3db23a18` |
| Secretary dist | 439 文件，manifest SHA `abcbe7bd95af3a0e89ca1ad78831851b1f499372121c36b473cbbff55359c0b7` |
| Dashboard dist | 67 文件，manifest SHA `cab847d3163f1916f956e033ee405b8cac7eecdd504f00eff1b45241c0922e4a`；沿用已验产物 |
| Provider / 新快照工具 | Provider `a7225f6075c0ead8cad559db93be8da5525e09e8`，两Home共20份安装文件SHA已核；新增周期helper SHA `8e1ecc2de07f71a695588c7c6036d985536ffc7895558229be09d5baba0e97a4` 已审，实际两端同SHA、周期落库与离线接收恢复原件已绑定于sync/activation；workspace旧TCC等待已由首尔正式往返验证取代 |

固定 v5 两门禁只覆盖各自记录的软件范围；本轮 UI 图标 / 显示名、Provider 可选 Thread Space、新快照接收和云配置另按本轮证据接收，不重跑旧昂贵全套。静态产物逐文件核集合、大小和 SHA，再核清单本身；后端会注入 machine token / 改写 Dashboard 前缀，实际 HTML 不要求与 dist index 逐字相同。

云 Core 用官方 PM 和既有 lock 构建 `.venv`，不裸 pip / uv 修改 PM 环境、不重新解析锁。本轮实际环境创建命令如下；升级前核对应版本，不在服务活 Turn 中重建：

```bash
cd /root/hermes-secretary
/root/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu/bin/python3.14 -m pm.build_env \
  --source . --out .venv \
  --python /root/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu/bin/python3.14 \
  --extra web --extra anthropic --extra mcp --group dev --group test
```

两个前端只交付 dist＋外置 SHA 清单，不上传独立 UI 源码仓、不在云端 npm 安装 / 构建。构建输入快照和日志留本机；静态目录不含 Home、SOUL、配置、凭据、DB 或日志。现产物中的构建路径字面量已按正式消费者核对为非运行依赖，不因此改写产物或丢失原指纹。

证据按职责查阅，不把中间脚本或文件存在当成功：

- `.hermes-dev/product-intent-review-20261018/deployment-release-20261019/`：用户定案 SOUL、preflight、cloud-deployment、sync。
- `.hermes-dev/deployment-release-20261019/ui/`：UI `report.md`、`release-binding.json`、`commit-reception.json`、构建输入与产物清单。
- 云运行整合收据：`cloud-deployment/34-integrated-success-receipt.result.json`，含最终PM/锁、unit/监听、48会话迁移、MCP/模型、精确自有Runtime回收与原服务保护；独立门禁不由此代签。同步与冷库实装收据仍须另绑定。

## 3. 原生注册、历史与个人插件

先检查未知同名目录 / 注册，不覆盖已有用户配置；原生逻辑 ID 是 `alex`，物理目录保留 `Alex`：

```text
/root/.hermes/                         原生控制根
  config.yaml                         default Files 仅合并 terminal.cwd: /root/workspace
  profiles/
    alex  -> ../../.hermes_profiles/Alex
    study -> ../../.hermes_profiles/study
/root/.hermes_profiles/
  Alex/                               profile.yaml display_name: Alex
  study/                              profile.yaml display_name: study
```

两业务 Home 的 `terminal.cwd` 同为 `/root/workspace`。只合并控制根 default 必要 cwd，不整份覆盖；default 是原生控制 / Files 身份，不额外导入第三份聊天历史。单独把 `HERMES_HOME` 指向物理 Alex 会变成独立 default，不能代替原生多 Profile 注册。跨 Profile 会话列表不授权模型读取另一个 Home。

### 48 会话共享 cwd 迁移

持久 `sessions.cwd` 优先于 Profile 配置。业务恢复前核受管会话 idle、无 lease / 在途任务，按封存清单确认 48 个精确 stored session_key 属于 alex，通过已有 stored-session RPC 逐个迁移，不直接批量改 SQL、不 resume 历史或启动模型：

```json
{"method":"session.workspace.move","params":{"profile":"alex","session_key":"<exact-imported-stored-key>","cwd":"/root/workspace"}}
```

核返回 cwd / git metadata，再只读对账全部 48 条 cwd、48 会话 / 6065 消息、owner、Conversation Ref、UID、原文、root 和 binding。原 Mac cwd 留在 `origin_json.imported_from.source_header.cwd`，不删除或替换溯源。study 不参加迁移。迁后重新生成一致性快照；成功与否以实施对账结果为准，不能以本机隔离副本证据代签。

### 插件、MCP 与凭据

仅安装获批准的静态配置和插件代码，不 clone 测试 Home、DB、Notebook、Reminder、active、locks、logs、cache、测试 AGENTS 或时间缩放。Home / 控制根使用受限权限，配置 / 凭据 0600；不打印 Key，不复制整个 shell 环境。

插件固定安装源为 `/root/.local/share/hermes-secretary/install/nowledge-mem-hermes`；按同一版本对两个物理 Home 分别预览再 `install_personal.py --home <physical-home> --apply`，核 FILES 全集合源 / 目标 SHA、权限及 Space / archive 设置。保留原生 memory toolset 与已撤销 Skill 状态，不覆盖 SOUL。

NM 客户端复用云主机官方配置，不复制 Mac 全局 NM 凭据，不启 Background Intelligence。Thread 自动同步关闭不等于终端沙箱或服务端只读；Memory 创建 / 修改仍依具体授权。`nmem-memory.py` 安装到 `/root/scrips/`，不依赖 Hermes、Provider 路径、HERMES_HOME 或 cwd；创建一次携完整内容与 Metadata，其它操作走官方 CLI，unknown / partial 不盲重试。

Alex 复用云 Pi 既有 `kimi-tools` 与 `feishu-notifier` 的 command / args / env 语义并转换为原生 `mcp_servers` 配置；检查实际 tools list 至少含 Kimi Search / Fetch 和 Notifier。只接入 / 探测，不因此发送飞书消息。凭据云内复用；DeepSeek Key 仅按已授权路径安全落地，不能随配置双向同步。

协议发现与真实业务分别验收。D15真实模型调用暴露Kimi Search/Fetch的408/403/404失败，换公开目标及直连/现有代理均408；当前不把握手通过写成业务可用，也不凭通用HTTP错误盲改Key、端点或代理。NM Context Bundle/status正常与自动Recall为不同请求：本轮Recall默认2秒超时，后续同环境一次官方CLI查询0.562秒成功，保留该次降级事实，不据单次观察擅改预算。

## 4. Mutagen 方向与旧 Pi 清理顺序

使用项目级配置，不覆盖 `~/.mutagen.yml`，不添加 setup / teardown 隐式命令。先核本机现有 sessions、端点、全局合并影响及范围重叠，必要时显式 `--no-global-configuration`。实际配置本体为`~/dotfiles/hermes-secretary-sync/`，链接`~/.config/hermes-secretary-sync/mutagen.yml`；SSH专属Host为`hermes-secretary-sync`。三lane名称固定如下，精确ID/安装SHA在本轮ignored `sync/activation/installation-and-commit.json`；不要猜ID或执行全局terminate。

| 逻辑用途 | 端点 | 模式与范围 |
|---|---|---|
| workspace | Mac `~/Desktop/Alex` ↔ `alex:/root/workspace` | `two-way-safe`，共享工作目录 |
| profile-config | Mac `~/.hermes_profiles` ↔ `alex:/root/.hermes_profiles` | `two-way-safe`，仅 Alex / study 的非凭据 `config.yaml`、`SOUL.md`、`nowledge-mem.json`、`profile.yaml` |
| database-snapshot | `alex:/root/.hermes_profiles/.snapshots` → Mac 同名目录 | `one-way-replica`，仅稳定完成包 `databases-current.zip` |

同一既有 SSH / Mutagen 通道分工，不另建 HTTP / rsync / S3。配置 session 排除整个 `.snapshots`、raw DB / WAL / SHM / journal、备份和其它运行态；未知新目录不能自动回传。`.env` 不进 allowlist。配置 / SOUL 双向冲突人工核对，不用 `two-way-resolved` 自动选胜方；接收 DB 不能反写配置 / SOUL。正式起同步前核真实 allowlist、方向与端点；“connected”不能证明内容已正确到达。

**同步验收口径：** 三lane分别核workspace真实写入/删除往返、8配置文件两端SHA、单向完成包的自动接收及三库payload完整性；SOUL冲突按核定当前权威版本处理，不固定回盖旧冻结SHA。首尔切换已完成这些验证，旧Desktop TCC等待已关闭；Agent仍禁止代点或绕过TCC，不用初始扫描代替正式workspace往返。动态状态与完整证据只记根CLAUDE。

**旧 Pi Mutagen 的关闭与清理必须最后执行。** 用户最新D15明确真实公网访问、DeepSeek只读自查后清理并汇报；完成该顺序后，五条已核旧Pi session已备份配置并按精确ID暂停/终止，新三条保留，未删用户目录/数据或重启daemon。此前“待全部workspace往返后清理”是Agent计划，已按最新顺序调整；不重复清理。当时workspace的Desktop TCC另待放行；后续首尔正式往返已通过，不用清旧会话解决新链路故障。恢复配置/精确ID收据保存在受限`final-acceptance-20261019/ops/`，不动其它同步、SSH、NM或OpenClaw服务。

## 5. 每 5 分钟 SQLite 快照与本机冷库

云端每 **300 秒**独立产生一次快照。它不等待 Mac、SSH / Mutagen 握手或远端 ACK；Mac 离线不阻塞模型 / 服务，也不生成无限待传队列或无界日志。只保留固定当前完成包、有界状态 / 日志及接收端已验两槽；临时文件和失败重试必须有界。云`hermes-secretary-snapshot.service/timer`已实际触发；Mac `gui/501/fyi.edgar.hermes-sqlite-mirror`已启动，300秒与WatchPaths到件触发、ThrottleInterval60、输出/dev/null。固定云状态`/root/.local/state/hermes-secretary-snapshot-staging/status.json`，Mac状态`~/.local/state/hermes-secretary-known-good/status.json`。两端受审工具SHA为`8e1ecc2de07f71a695588c7c6036d985536ffc7895558229be09d5baba0e97a4`；个人实现commit5c7fad17、实装状态commit892c6bf2。

工具为 `/root/scrips/hermes-sqlite-snapshot.py`，个人部署工具不改 Core / Harness 生命周期。原生全 Home backup 的范围与本次窄清单不同，不用它替代这里的完成包契约。每库只读连接，通过 SQLite backup API 得一致副本；关连接后核 integrity / foreign_key_check、size、SHA。**保证单库内部一致，不承诺多个独立库同一事务时点。** 必需库为 `Alex/state.db`、`study/state.db`；额外 projects / receipts 库仅按最终已核存在的显式批准名单加入，不扫描未知 DB。

固定名未压缩 `ZIP_STORED` 包含 manifest、manifest SHA 与全部 payload；同步树外暂存，完整 close / 校验后同文件系统原子 replace 到 `.snapshots/databases-current.zip`。Mutagen 只传完成包，Mac 离线时后续周期替换当前包，不堆积历史。稳定路径便于差分，但实际网络增量比例未测；每周期仍有完整 SQLite 副本读写成本，应监控磁盘空间及耗时。

以下是既有工具的手动诊断模板，不代替最终周期命令；周期正式命令为下面的`publish-cycle`/`receive-cycle`，保留旧手动入口用于诊断：

```bash
python3 /root/scrips/hermes-sqlite-snapshot.py snapshot \
  --profile-root /root/.hermes_profiles --sync-root /root/.hermes_profiles \
  --staging-root /root/.local/state/hermes-secretary-snapshot-staging \
  --publish-file /root/.hermes_profiles/.snapshots/databases-current.zip \
  --database Alex/state.db --database study/state.db --database Alex/projects.db
```

实际周期入口：

```bash
/root/hermes-secretary/.venv/bin/python /root/scrips/hermes-sqlite-snapshot.py publish-cycle \
  --profile-root /root/.hermes_profiles --sync-root /root/.hermes_profiles \
  --staging-root /root/.local/state/hermes-secretary-snapshot-staging \
  --publish-file /root/.hermes_profiles/.snapshots/databases-current.zip
/Users/edgar/.local/share/mise/installs/python/3.13/bin/python3 ~/scrips/hermes-sqlite-snapshot.py receive-cycle \
  --archive ~/.hermes_profiles/.snapshots/databases-current.zip \
  --profile-root ~/.hermes_profiles --sync-root ~/.hermes_profiles \
  --known-good-root ~/.local/state/hermes-secretary-known-good
```

云与Mac命令分别在对应机器运行，不额外启动第二个周期服务。只读状态入口：`systemctl status hermes-secretary-snapshot.timer --no-pager`（云）、`launchctl print gui/501/fyi.edgar.hermes-sqlite-mirror`（Mac）以及各自固定status.json。

自动 DB 回传不打包凭据；配置 / SOUL 走第 4 节独立同步。若手动快照需附非凭据静态文件，逐项批准 `--static`，其副本仅作恢复参考、不反写本体。

Mac 收到的包只是待验输入。先复制到同步树外私有暂存，严格验证精确 DB 集合、manifest SHA、每文件 size / SHA，无缺失、额外、重复或路径逃逸，再核 SQLite integrity / FK。坏包、半包、传输中断不改变已验槽和冷库。成功后原子提升固定 `current.zip`，旧已验包留固定 `previous.zip`，不无限累加。

既有手动全包验证 / 提升入口如下；`<chosen-source-sha>` 用实际源完成包 SHA，当前实装另有Alex/projects.db，以下已列入；未来其它已知可选库出现时，手动参数须与该次manifest一致：

```bash
python3 ~/scrips/hermes-sqlite-snapshot.py verify \
  --archive ~/.hermes_profiles/.snapshots/databases-current.zip \
  --database Alex/state.db --database study/state.db --database Alex/projects.db --archive-sha256 <chosen-source-sha>
python3 ~/scrips/hermes-sqlite-snapshot.py promote \
  --archive ~/.hermes_profiles/.snapshots/databases-current.zip \
  --sync-root ~/.hermes_profiles --known-good-root ~/.local/state/hermes-secretary-known-good \
  --database Alex/state.db --database study/state.db --database Alex/projects.db --archive-sha256 <chosen-source-sha>
```

**完成回传还必须更新本机两个对应的冷态 `state.db`，仅有 ZIP 不算完成。** 接收器确认目标无运行进程 / 活连接、无 WAL / SHM / journal、路径与锁安全，先完整验证并准备所有副本，再逐库原子替换；目标忙、未知、坏包或锁冲突时暂停 / 拒绝，不覆盖活库、不删 sidecar 强行凑冷态。跨两文件不是全局事务；中途失败应准确记已应用集合并可由已验包重试 / 恢复，不冒称全包已应用。实际三库`Alex/state.db`、`study/state.db`、当时已存在的`Alex/projects.db`已回传到对应冷态路径，并核完整字节/逐表身份相等；两槽及initial原Pi inode保留。同包幂等、仅暂停本项目snapshot lane而云继续固定发布、恢复追上及launchd自动落库均有实装原件。半/坏包/忙库/部分失败保护复用同SHA的19不同实际SQLite受控节点，不在生产库制造故障；不冒称已真关机或长时间整网断线。

灾难恢复只从已验包恢复到不存在的新根，不直接覆盖运行 Home：

```bash
python3 ~/scrips/hermes-sqlite-snapshot.py restore-new-root \
  --archive ~/.local/state/hermes-secretary-known-good/current.zip \
  --database Alex/state.db --database study/state.db --database Alex/projects.db --archive-sha256 <chosen-source-sha> \
  --destination <nonexistent-offline-recovery-root>
```

恢复不自动启动 Hermes、注册 Profile 或重放排期。正式替换云运行库须另确认恢复点：停唯一后端、保留失败现场 / 新写入、核源码 schema 兼容与 Ref / UID / 会话对账、确认旧 WAL / SHM 脱离运行后再切换；不能从 Mac 自动反覆盖云端。

## 6. 后台 systemd 与原生启动

先完成配置、历史 cwd 迁移和 dist 校验，再由 systemd 管一个 backend / worker 与宿主 Scheduler。不要按 Profile 各起进程、另启 Gateway / Cron 共享库，或使用 `serve` 的 headless 握手页代替双 SPA。以下是最终启动参数模板，不是在当前 shell 再起第二实例的操作：

```bash
cd /root/workspace
HERMES_HOME=/root/.hermes \
HERMES_WEB_DIST=/root/.local/share/hermes-secretary/static/secretary \
HERMES_DASHBOARD_WEB_DIST=/root/.local/share/hermes-secretary/static/dashboard \
HERMES_DASHBOARD_PREFIX=/dashboard \
/root/hermes-secretary/.venv/bin/python -m hermes_cli.main -p alex dashboard \
  --host 127.0.0.1 --port 53446 --skip-build --isolated --no-open
```

`-p alex` 保留原生逻辑路径与多 Profile 发现；`--isolated` 绕过 attach-first，不表示多 worker。unit 使用绝对路径，显式 `User=root`、`HOME=/root`、`WorkingDirectory=/root/workspace`、必要 PATH / 上述环境，配 network-online 依赖、`Restart=on-failure`、`KillSignal=SIGTERM`、`TimeoutStopSec=180`、`UMask=0077` 及安装目标。EnvironmentFile 不展开 `$HOME`。日志有界，不复制整个 shell 环境或 Desktop 父进程 / SSH / token 环境，不带 `HERMES_SERVE_HEADLESS` 或另一路 Dashboard public_url。

已绑定专属unit：`/etc/systemd/system/hermes-secretary.service`、`/etc/systemd/system/hermes-secretary-proxy.service`，均 active/enabled；使用下列只读命令查看，不据历史PID杀进程：

```bash
systemctl status hermes-secretary.service hermes-secretary-proxy.service --no-pager
journalctl -u hermes-secretary.service -n 100 --no-pager
```

源码 / HEAD 变化可能触发原生 code-skew guard，最终版本安全重绑定，不关 guard，不用全局 `serve --stop`、`pkill` 或强杀接管其它服务。

## 7. 反代、Tunnel 与 Access

```text
浏览器 → https://hermes.edgarzhong.fyi → Cloudflare Access → Tunnel
       → Caddy 127.0.0.1:53448 → Hermes 127.0.0.1:53446
         /                         Secretary Web
         /dashboard、/dashboard/   原生 Dashboard
         /api/*、/api/ws            同源 API / WS
         /dashboard/api/*          后端重写至共用 API / WS
```

Caddy 仅回环，Host 改回 backend、删除 Origin；不剥 `/dashboard`，不另起 API 域名、CORS 或多 worker：

正式Caddy为2.6.2，配置文件为`/root/.local/state/hermes-secretary/deployment/caddy.json`，二进制为`/root/.local/share/hermes-secretary/caddy/usr/bin/caddy`，由上述专属proxy unit读取。JSON设置admin disabled、admin.config.persist=false、自动HTTPS关闭、回环监听；路由不限制原始公网Host，向backend改写Host并删除Origin。旧Caddyfile的`persist_config off`在此版本不支持，不可照旧模板直接启服。保留已验JSON并在修改后先校验：

```bash
/root/.local/share/hermes-secretary/caddy/usr/bin/caddy validate \
  --config /root/.local/state/hermes-secretary/deployment/caddy.json
```

不另启全局Caddy服务。

运行 Tunnel 的真实配置入口是 `/etc/cloudflared/config.yml`，不是 `/root/.cloudflared/config.yml`。新 hostname 指向 `http://127.0.0.1:53448`，保留原 SSH、NM、eb-data、OpenClaw 四入口及末尾 404；任何必要变更先校验、不替换其它入口。保留其它已有服务；不因它们的既有失败而接管修复。

用户已完成 Access 配置；root 已观察匿名请求 302 至 `edgarzhong.cloudflareaccess.com/cdn-cgi/access/login/hermes.edgarzhong.fyi`。这证明该次匿名入口受登录跳转保护，**不代签登录后双 SPA / API / WS 成功**。Access 覆盖整个 hostname 与用户邮箱 allowlist，不给 API / WS Bypass；两 SPA 的原生 machine token 仍由后端注入。后续检查沿用用户策略，不重配 Access。若保护失效，不直接公开 machine-token 业务入口。

## 8. 验收、升级与回滚

按真实部署版本先验回环，再验公网。代表性检查包含：两个 SPA 资源、Dashboard 子路径刷新、同源 REST / 两 WS / 404 边界、Alex / study owner 与显示名 / 图标、跨 Profile 列表、Files default 共享 cwd、48 会话历史与来源对账、Alex 实际 `k3-256k` / high 和可选 DeepSeek、study订阅及主模型`gpt-6-sol`／High、委派`gpt-6.1-sol`／继承High、无新增Idle／自Space、MCP tools list、5 分钟完成包、Mac 离线不中断云、坏包 / 忙库保护及最终冷库一致。

UI **仅由主会话通过自己创建的 Codex 隐藏 IAB（`iab`、`visible:false`）验收**，不使用桌面、外部浏览器、可见页、open / open_in_codex 或任何显示 / 焦点变化；没有合规接口就记未验。登录后入口未验、手机未验等按实际记录，不能从接口或匿名 302 推成 UI PASS。

**本轮D15窄例外：** 用户明确指定其当前受信任Edgarzhong浏览器Profile进行最终公网验收，root仅沿既有Chrome扩展连接（名称Edgar）认证访问双SPA；真实完成Secretary发送/流式/终态及Dashboard会话数据/API加载，无OTP和桌面/原生App/系统open。仅关闭自己创建的两页，原用户三页保留。该次结果不扩大今后默认浏览器权限，也不从Dashboard数据加载推断另有原始WS握手抓包证据。

只做本轮必要少量合成模型 / Reminder 场景并精确回收自有资源，复用固定 v5 不变接缝证据，不重跑旧 100k / 600 秒 / Memory 创建旅程或昂贵套。真实 Thinking / 工具 / 终态缺覆盖时如实记录；NO_REPLY 仍按用户决定保持未实施，不借部署改变权限或静默政策。先让正确配置的服务可用；文档待绑定字段和非阻断历史观察不作为停服理由，真实数据 / 凭据 / 访问保护问题则按事实处理。

升级前固定版本 / 产物 / 配置 / SOUL 指纹和可恢复快照。等活动 Turn / Noting 结束，安全停唯一 backend、保留数据，在 `/root/hermes-secretary` 核固定版本 / lock / PM 环境后启服务；不在活 Turn 中 git pull 或替换解释器。失败保留新写入 / 日志 / 原库，schema 兼容时恢复配套源码＋dist；不兼容先核恢复点再离线恢复，不清空 Home、不用 Mac 旧库自动覆盖。旧 Pi Mutagen 已按§4/D15最后精确清理；剩余workspace权限和自有marker验证按现有lane接续。
