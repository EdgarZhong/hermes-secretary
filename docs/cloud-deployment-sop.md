# Linux 上云部署 SOP

本文适用于独立 Secretary Web SPA＋原生 Hermes Web Dashboard、同源双 SPA、单后端和原生多 Profile。用户已于 2026-10-19 放行部署；本文记录操作口径，不以模板、上传或本机门禁代表云端成功。当前进度与待办只在根 [CLAUDE.md](../CLAUDE.md)，本轮依据及验收入口在 [Snapshot Index](../.autonomous/20261019-cloud-deployment/snapshot-index.md)。架构见 [06 §0.7–0.8](06-Hermes-Secretary-Web-UI-V1-Spec.md#07-confirmed-deployment-topology-and-dual-spa-routing-2026-10-17)、[08](08-profile-scheduler-files-clarification.md)。

## 0. 首尔正式入口的认证运维

首尔 Hermes 正式入口为 `hermes.edgarzhong.fyi`，使用 Authelia 双因素认证。旧 `test.edgarzhong.fyi` 已废弃，直接返回404。`eb-data.edgarzhong.fyi` 由 Caddy 反代 `127.0.0.1:8787`，保留 Ebbinghaus 原生 Bearer 鉴权，不套浏览器双因素跳转；`nmem.edgarzhong.fyi` 反代 `127.0.0.1:14242`，保留NM原生API令牌认证。三个域名均使用仅DNS的首尔A记录。

首尔 Hermes 使用 `ubuntu` 服务布局、Caddy 公网 HTTPS；`auth.edgarzhong.fyi` 仅提供认证门户。本节描述首尔入口；下文的 `/root`、`alex` 与 Cloudflare Tunnel／Access 布局属于既有部署模板，不直接套用到首尔机。当前迁移进展只记根 `CLAUDE.md`。

首尔稳定布局：Hermes仓库 `/home/ubuntu/hermes-secretary`，控制根 `/home/ubuntu/.hermes`，两实体Home `/home/ubuntu/.hermes_profiles/{Alex,study}`，通过控制根的 `profiles/{alex,study}` 注册；保留原生default，不通过前端隐藏规避身份解析。Ebbinghaus位于 `/opt/ebbinghaus`；NM官方0.10.101运行程序保持 `/usr/lib/Nowledge Mem`，原生四数据根保持原路径，`nmem.service`以root运行、只监听本地14242，客户端ubuntu使用自己的受限官方连接配置。NM使用阿里云专属Host的 `/compatible-mode/v1`、`qwen3.7-text-embedding`／1024维，启动器从 `/etc/secrets/dashscope.key` 读取Key，不加载本地GGUF；更换模型后必须原生reindex，不能因维数相同跳过。

同步专用Host `hermes-secretary-sync` 指首尔ubuntu，不改北京 `alex` alias。workspace为首尔 `/home/ubuntu/workspace` ↔ Mac `/Users/edgar/Desktop/Alex` two-way-safe；配置只传8白名单文件；DB完成包由首尔 `.hermes_profiles/.snapshots/databases-current.zip` 单向传Mac，再由既有接收器核验后落冷库。首尔快照timer每五分钟独立发布，Mac离线不阻塞源发布；不得把rawDB改成双向同步。切换时暂停旧lane、核定当前源配置、预对齐后启用，按真实marker往返、配置SHA、自动快照落地验证，不能只看connected。实际版本和收据见根CLAUDE。

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

## 1. 原北京部署模板与生产配置口径

本节为原北京部署模板（首尔运行布局按§0），不是当前主机选择。模板服务用户为 `root`，HOME 为 `/root`，SSH 使用本机既有 alias `alex`。云端 Ubuntu 24.04 / x86_64；不要把本机虚拟环境复制上云。

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
