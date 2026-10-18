# Linux 上云部署 SOP

适用目标：独立 Secretary Web SPA 与原生 Hermes Web Dashboard，同域、单后端，通过 Cloudflare Tunnel + Access 邮箱白名单访问。本文是操作步骤，不代表云端已经验收。依据：[06 §0.7–0.8](06-Hermes-Secretary-Web-UI-V1-Spec.md#07-confirmed-deployment-topology-and-dual-spa-routing-2026-10-17)、[08](08-profile-scheduler-files-clarification.md)、[本轮 PI-16～20](../.autonomous/20261018-product-intent-review/snapshot-index.md)。当前交付状态以根 [CLAUDE.md](../CLAUDE.md) 为准。

## 1. 部署前填表

占位符必须替换为本次批准的值；不要直接复制本机测试 Profile、凭据或测试尺度。

| 项目 | 本次部署记录 |
|---|---|
| 已验收 Core commit | `<accepted-core-commit>`，尚待最终冻结，不用当前 dirty HEAD 代替 |
| 已验收独立 UI commit | `<accepted-ui-commit>`，与上项配套 |
| Secretary / Dashboard 产物 SHA256 清单 | `<secretary-manifest>` / `<dashboard-manifest>`，记录清单自身 SHA256 |
| Linux 发行版／架构、Python／Node／npm | `<versions>`，符合冻结版本的 PM 与 package engines；保留锁文件 SHA256 |
| 发布目录／服务用户 | `/srv/hermes-secretary/releases/<release>` / `<service-user>` |
| 当前发布软链接 | `/srv/hermes-secretary/current`，指向完整的一个 release |
| Profile 根目录 | `/var/lib/hermes-secretary`，不在源码或静态目录内 |
| 两个 Profile | `<main-profile>` / `<specialist-profile>`；可另配默认 Profile 供 Files 使用 |
| 仓外工作目录 | `/var/lib/hermes-secretary-workspaces/<profile>` |
| 公网入口／回环端口 | `<private-host>` / `<proxy-port>` / `<backend-port>` |
| 模型／原生 Provider／时区 | `<approved-model-provider-timezone>`，每个 Profile 分别配置 |
| Noting 联合空闲触发生产值 | `<threshold-tokens>` / `<delay-seconds>`，上线前由用户配置确认 |
| 可选个人 NM 插件 | `<accepted-plugin-commit-or-disabled>`；Space 和读写授权另行确认 |
| 独立 NM 创建工具 | `<accepted-tool-sha256>`，服务用户的 `~/scrips/nmem-memory.py`，不依赖Hermes安装或环境变量 |

本机使用过 100,000 tokens、空闲 5 秒、现实 10 分钟代表一天，均为测试配置；不自动变成生产参数，也不改变模型最大上下文。生产 SOUL 不带测试官前缀、测试角色或压缩时间尺度。

```text
浏览器 https://<private-host>/
  → Cloudflare Access：邮箱 allowlist
  → Cloudflare Tunnel
  → Caddy 127.0.0.1:<proxy-port>
  → Hermes 127.0.0.1:<backend-port>（唯一后端进程、单 worker）
       /                         Secretary
       /dashboard、/dashboard/   原生 Dashboard
       /api/*、/api/ws            共用 API
       /dashboard/api/*          后端重写至 /api/*，含 WebSocket
```

不部署第二 API 域名、第二后端或多副本；否则内存 Session 与 Scheduler／Noting 所有权会分裂。本文主路径直接运行 Linux 进程；容器需共享回环网络身份，不可直接换成 bridge 网络。

## 2. 固定源码与构建两个 UI

以下操作在已填表的发布目录完成，Core、独立 UI 分别放 `core/`、`secretary-web/`。按各仓批准的 commit 获取源码，保留原锁文件；不要把开发目录整体上传。先核对 `git rev-parse HEAD`、工作区差异及验收记录，构建后再核对一次，产物与源码须配套。

Core 使用官方 PM 和锁，不以裸 pip／uv 改环境。用符合该版本要求的 Python 创建尚不存在的 `.venv`；不要把本机虚拟环境复制到 Linux：

```bash
cd /srv/hermes-secretary/releases/<release>/core
<bootstrap-python> -m pm.build_env --source . --out .venv --group dev --group test
# 主仓官方 Dashboard：root workspace 依赖，构建入口在 web。
npm ci --workspace web --include-workspace-root
npm run --workspace web build
# 默认产物：core/hermes_cli/web_dist/index.html

cd /srv/hermes-secretary/releases/<release>/secretary-web
npm ci
npm run build
# 默认产物：secretary-web/dist/index.html
```

需要显式输出目录时，Dashboard 使用主仓正式入口 `node scripts/build/web.mjs --source <core> --icons <prepared-icon-source> --out <dashboard-dist>`，独立 UI 使用 `npm run build -- --outDir <secretary-dist>`。Dashboard 的 icons 输入须已准备完整，至少含 `web/public/favicon.ico`；缺失就修复构建输入，不以空图标或失败产物继续。

对两个产物分别生成清单，清单放在产物目录外；记录 Python／Node／npm、Core／UI commit、锁文件和清单 SHA256。以下为 Linux 命令：

```bash
cd <dist-directory>
find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > <manifest-outside-dist>
sha256sum <manifest-outside-dist>
sha256sum --check <manifest-outside-dist>
```

验收过的现成静态产物也可直接部署，但仍须核对配套 commit 与上述校验清单；不能用旧 UI 产物给新源码签通过。浏览器实际收到的 HTML 会注入 token，Dashboard 部分资源也可能做前缀改写，不能要求它们与构建文件全部逐字节一致。

## 3. 建立 Profile 与生产配置

由专用服务用户拥有状态及仓外工作目录；Profile 目录建议权限 `0700`，`.env`、NM 客户端配置、Tunnel 凭据及备份建议 `0600`，仅对应服务用户／运维读取。凭据、SOUL 私人正文、数据库和运行日志不进入 Git、静态目录或公开产物。

先建立并授权服务用户访问实际状态根和 `terminal.cwd`，包括下方unit使用的 `/var/lib/hermes-secretary-workspaces/service`；不存在的WorkingDirectory会使systemd在运行Python前直接失败。按填表值创建主助手和专职助手各自的仓外工作目录，不依赖启动时自动创建。

通过原生 CLI 在同一个明确的根目录创建两个 Profile，不克隆测试历史：

```bash
sudo -u <service-user> env HERMES_HOME=/var/lib/hermes-secretary \
  /srv/hermes-secretary/current/core/.venv/bin/python -m hermes_cli.main -p default \
  profile create <main-profile> --no-alias
sudo -u <service-user> env HERMES_HOME=/var/lib/hermes-secretary \
  /srv/hermes-secretary/current/core/.venv/bin/python -m hermes_cli.main -p default \
  profile create <specialist-profile> --no-alias
```

分别配置 `/var/lib/hermes-secretary/profiles/<profile>/` 内的 `config.yaml`、`.env`、`SOUL.md` 和 Skills；`state.db` 归各自 Profile。模型、API／Provider、推理选项沿 Hermes 原生配置。两个 Profile 都开启 `noting.enabled`、`scheduler.enabled`。若启用联合空闲 Compact + Noting，设置 `noting.idle.enabled`、已确认的 `noting.idle.threshold_tokens`／`delay_seconds`，并保持 `compression.idle_compact_after_seconds: 0`，避免两套 idle 机制冲突。

各 Profile 的 `terminal.cwd` 指向仓外目录，不可放源码或源码子目录，否则会加载项目开发指令。SOUL 写长期身份和职责；访问政策放对应 workspace 的 `AGENTS.md`，不要只依赖每条测试消息的前缀。主助手跨领域读取通过获准的 NM Space，不读取另一个 Hermes Profile 的 Home、数据库或历史。统一 UI 列表不扩大模型跨 Profile 读取权限。

Files 当前固定使用 `default` Profile 的文件后端，因此还须配置根 Home 的 `config.yaml` 中 `terminal.cwd` 为批准的仓外 Files 根；不能让它变成新聊天的 owner。切换 New Chat Profile 不应过滤其他 Profile 的已有会话。

所有受管配置均不设 `dashboard.public_url`，服务环境也不设 `HERMES_DASHBOARD_PUBLIC_URL`。生产保留 `gateway.model_code_skew_guard` 默认开启；本机 dirty 开发关闭该项不构成生产配置。配置变更按原生实例／服务重启生效，不在活动 Turn 中切换。

### 可选：安装独立个人 NM Provider

此插件不属于公开核心必需依赖。只使用已批准的个人仓版本；参考该仓 `nowledge-mem-hermes/README.md`、`nowledge-mem-hermes/docs/PHASE3.md`，不要运行上游 curl 安装器覆盖个人策略。对两个实际 Home 分别预览，再安装：

```bash
/srv/hermes-secretary/current/core/.venv/bin/python \
  <plugin-checkout>/nowledge-mem-hermes/install_personal.py --home <profile-home>
# 核对预览后，同一命令增加 --apply；安装另一个 Profile 时换实际 Home。
```

用服务用户的正式 `nmem` 客户端配置连接，密钥不放命令参数。确认服务 PATH 含 `nmem` 和原生 `curl`。插件安装保留 native memory toolset，以加载 Provider 提示；原生文件记忆开关由安装器按个人契约设置。每个 `<profile-home>/nowledge-mem.json` 显式选择已存在的 Space，不靠进程级 `NMEM_SPACE` 区分 Profile。

只读 Default 可设 `{"space":"","archive_enabled":false}`，同时在 workspace 政策约束手动操作。`archive_enabled:false` 仅关闭自动 NM Thread 同步与结束重试，不是终端沙箱或服务端只读凭据。其他 Space 的自动同步是否开启由用户批准；它会同步已完成对话文字，须纳入数据授权。Memory 新增／修改仍需具体内容和目标获批，不因安装、提案或 `--apply` 获得概括写权。NM Background Intelligence 保持关闭；不自动移动旧资料或更改治理设置。安装后重建运行实例，新 root 才加载新提示，旧对话快照不改写。

### 独立 NM Memory 创建工具

按用户指定，本机与云端均安装至实际执行用户的 `~/scrips/nmem-memory.py`（目录拼写为 `scrips`）。工具源码与SHA使用本次验收版本；只复制独立工具，不复制本机连接配置、凭据或Hermes环境。使用服务用户既有官方NM配置，服务PATH需包含 `python3`、`nmem`、原生 `curl`；不依赖Hermes虚拟环境、插件目录、`HERMES_HOME`或仓库工作目录。示例中的源码占位符须替换为已验收单文件：

```bash
sudo -u <service-user> -H sh -c '
  install -d -m 700 "$HOME/scrips"
  install -m 700 <accepted-standalone-source> "$HOME/scrips/nmem-memory.py"
  cd /tmp
  env -u HERMES_HOME -u PYTHONPATH python3 "$HOME/scrips/nmem-memory.py" --help
'
```

安装前检查同名现有文件并备份，不直接覆盖未知版本。工具接收调用方提供的正文、标题、标签、Space及通用Metadata JSON；不读取Hermes会话或推导来源。Memory创建一次携完整Metadata提交，其它读取／普通字段修改／删除仍走官方CLI；仅创建Metadata错误须获批删除后重建，unknown／partial不得盲目重复创建。上线验收需由模型实际调用，并通过同一真实ID回读确认Metadata；`--help`、preview或安装成功不能代替此项验收。

## 4. 用 systemd 常驻唯一后端

先将 `current` 指向已构建 release。`/etc/hermes-secretary/backend.env` 只手工列所需环境，不使用 `env > file`、`export -p` 或复制整份 shell 环境。它不是 shell 脚本，不写 `export`、`$HOME` 或命令替换：

```ini
HERMES_HOME=/var/lib/hermes-secretary
HERMES_WEB_DIST=/srv/hermes-secretary/current/secretary-web/dist
HERMES_DASHBOARD_WEB_DIST=/srv/hermes-secretary/current/core/hermes_cli/web_dist
HERMES_DASHBOARD_PREFIX=/dashboard
PATH=<approved-bin-directories>:/usr/local/bin:/usr/bin:/bin
```

Provider 密钥留各 Profile 的 `.env`／正式凭据配置；环境文件不放无关 shell token。不要带入 `HERMES_SERVE_HEADLESS`、Desktop 的父进程／SSH owner／token 环境。`--isolated` 是原生 CLI 绕过 attach-first／named-profile 重路由的启动选项，确保启动本服务登记的进程；它不代表第二套执行器，也不授权给每个 Profile 各开一个后端。

示例 `/etc/systemd/system/hermes-secretary.service`（替换占位符）：

```ini
[Unit]
Description=Hermes Secretary single backend
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=<service-user>
Group=<service-group>
WorkingDirectory=/var/lib/hermes-secretary-workspaces/service
EnvironmentFile=/etc/hermes-secretary/backend.env
ExecStart=/srv/hermes-secretary/current/core/.venv/bin/python -m hermes_cli.main -p default dashboard --host 127.0.0.1 --port <backend-port> --skip-build --isolated --no-open
Restart=always
RestartSec=5
RestartPreventExitStatus=78
KillSignal=SIGTERM
KillMode=control-group
TimeoutStopSec=180
UMask=0077
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

`hermes serve` 是 headless，同样能返回根路径握手 200，但不会挂载双 SPA；不要用它代替上述命令。不要加 `--insecure`，该参数不绕过认证。保持一个进程、一个 worker，不另开原生 Gateway／Cron 执行同一批 Profile 的排期。

检查 unit 后执行 `sudo systemctl daemon-reload`、`sudo systemctl enable --now hermes-secretary.service`。日常用 `systemctl status hermes-secretary.service` 与 `journalctl -u hermes-secretary.service --since <time>`；日志按私人运行数据管理，分享前去除 token 和内容。计划退出先等待活动 Turn／Noting 结束，再 `sudo systemctl stop hermes-secretary.service`；临时停用开机启动用 `disable`。不要运行 `hermes dashboard --stop`、`hermes serve --stop` 或泛化 `pkill`，它们可能停掉其他服务。

## 5. Caddy、Tunnel 与 Access

Caddy 配置路径 `<caddy-config-path>`，例如 `/etc/caddy/hermes-secretary.Caddyfile`。以下独立配置禁用 admin，并显式只监听回环；不要照抄仅 `:8080` 而遗漏 `bind`：

```caddyfile
{
    admin off
    auto_https off
    persist_config off
}
http://127.0.0.1:<proxy-port> {
    bind 127.0.0.1
    reverse_proxy 127.0.0.1:<backend-port> {
        header_up Host 127.0.0.1:<backend-port>
        header_up -Origin
    }
}
```

用 `caddy validate --config <caddy-config-path> --adapter caddyfile` 核对，再由该部署自己的 systemd unit 执行 `caddy run --config <caddy-config-path> --adapter caddyfile`；开启开机启动，日志归对应 unit。不要修改／重启同机其他 Caddy 服务。两 SPA 路径与 `/dashboard/api/*` 的重写由 Hermes 完成，Caddy 不剥除 `/dashboard`。后端与代理端口均不开放公网入站。

`<cloudflared-config-path>`（例如 `/etc/cloudflared/hermes-secretary.yml`）：

```yaml
tunnel: <tunnel-id>
credentials-file: <tunnel-credentials-path>
ingress:
  - hostname: <private-host>
    service: http://127.0.0.1:<proxy-port>
  - service: http_status:404
```

由此部署专属的 cloudflared systemd unit 执行 `cloudflared tunnel --config <cloudflared-config-path> run <tunnel-id>` 并开启开机启动。先核对其服务用户可读凭据，日志不暴露凭据正文；不覆盖同机其他 Tunnel。Cloudflare 将同一 hostname 路由至该 Tunnel，并建立覆盖整个 hostname 的 Access 应用，策略为 `Allow` + 指定邮箱白名单；不为 `/api/*`、`/dashboard/api/*` 或 WebSocket 设置 Bypass。Access 是唯一用户可见登录层，后端 machine token 由各自 HTML 自动注入。

## 6. 最小上线验收与记录

先验回环代理，再验 Cloudflare 公网入口；每项记录时间、版本／产物、实际结果和证据。API 结果只能证明接口，不能代签真实 UI。测试使用专用合成 Conversation、已批准的输入／排期，结束只清理自己的资源。

| 检查 | 必须观察的结果 |
|---|---|
| 暴露面／常驻 | `ss -ltnp` 核后端与 Caddy 仅 `127.0.0.1`；仅一个后端和宿主 Scheduler；退出浏览器不退出服务；重启主机后三个专属服务恢复 |
| 根入口 | `/` 是真实 Secretary HTML，JS／CSS 成功，token 自动注入；仅握手 200 不算通过 |
| Dashboard | `/dashboard` 和 `/dashboard/` 均可用；真实点击子页并刷新深链，assets 路径正确、无后端端口泄漏；不强行把未发生的斜杠跳转写为已验 |
| API／WS | `/api/health`、`/dashboard/api/health`；两套 `/api/ws`、`/dashboard/api/ws` 均真实升级成功并完成 gateway 只读调用；同 origin，无第二登录 |
| 错误边界 | 不存在的 API 和 JS 资源真 404，不返回 SPA 假 200 |
| 双 Profile／Files | 首页切换仅决定新会话，列表仍含两 Profile；打开／刷新／发送／恢复保持真实 owner；Files 固定 default，Back to Chat 恢复原聊天身份 |
| 冷态 Reminder | 关闭自己的浏览器连接，确认原 Runtime 与 poller 已回收；宿主到期自动恢复同一 Conversation，只受理一次，不依赖重新开页；核所属 Profile／配置、见证与最终响应 |
| 后台状态与 Timeline | 分别覆盖事先连接、中途打开／断线重连、完成后回收再打开；真实 running／终态、Reminder carrier、已提供 Thinking、每次工具和正文完整接续，无漏重；首页／侧栏也能观察未打开会话 |
| 恢复／资源 | 宿主重启后合法到期工作恢复；前端旧 Runtime 经原生 4001 恢复，不重复提交。测试结束自有 runtime／poller／lease／pending／未来排期／Noting child 回收，保留用户数据 |
| Access／公网／手机 | 未白名单身份被拒，允许邮箱登录后两 SPA、深链和两 WS 路径可用；TLS 正常，手机后台再打开能恢复；无 API Bypass |

没有真实 reasoning 时将 Thinking 子项记为未覆盖，不能伪造。静默行为不意味着隐藏后台执行；不把尚未批准的 `NO_REPLY` 提案当上线机制。

**截至 2026-10-18 本文编写时：** 本机已有同源 Caddy → 原生 dashboard 双 SPA 的基础 HTTP／assets／两 WS 路径证据，尚是过渡产物。当前最终真实浏览器旅程、Cloudflare Access／Tunnel、公网 TLS、Linux／systemd、云端重启及手机均未据此验收；后续只按对应最终版本的新记录关闭，不能沿本表预填 PASS。

## 7. 备份、升级与回滚

1. 变更前记录当前 release、两个 commit、产物清单、各 Profile 配置指纹与服务状态。备份配置、SOUL、授权政策、Skills／插件版本及必要附件；备份自身仍是私人数据，放受限目录，不上传公开仓库。
2. SQLite 使用在线 backup API，不能对活动 WAL 数据库只 `cp state.db`。对默认 Home／各 Profile 的 `state.db` 及已启用插件的 `nowledge-mem-personal/receipts.sqlite3` 等实际数据库逐一备份；不要假设所有库只有一个文件。示例在服务用户身份下运行，目标为新文件：

   ```bash
   umask 077
   <release>/core/.venv/bin/python - <source-db> <new-backup-db> <<'PY'
   import sqlite3
   import sys
   from pathlib import Path
   source, target = map(Path, sys.argv[1:])
   if not source.is_file() or target.exists():
       raise SystemExit("源数据库不存在或备份目标已存在")
   with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True) as src:
       with sqlite3.connect(target) as dst:
           src.backup(dst)
           if dst.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
               raise SystemExit("备份完整性检查失败")
   PY
   ```

   单库备份不保证跨库同一时点；需要整套一致恢复点时，先停止接收新工作、等待受管 Turn／child／NM Thread同步结束，停止本服务后再备份整套。配置备份不要顺手打包运行 token 或输出到终端。
3. 新版本在新的 release 路径按锁构建，完成相关验收；不要在正运行的源码目录 `git pull` 或改写正在使用的 `.venv`。确认 schema 兼容与回滚方案，优雅停本服务，切 `current` 到新 release，再启动并复验第 6 节受影响路径。系统不因此获得自动迁移、清库或重写旧对话的授权。
4. 失败时先停止本服务、保留失败日志和新数据，将 `current` 切回上一套完整 release，按兼容性恢复运行。若数据库与旧版本不兼容，不直接启动旧二进制；在用户确认新写入保留方式后恢复匹配备份。任何路径都不删除 Profile 目录、不用空库掩盖失败。

## 8. 最小故障表

| 现象 | 优先检查 |
|---|---|
| `/` 200 但只有握手，`/dashboard` 404 | 是否误用 `serve`／带入 headless 环境；改回本 SOP 的 dashboard 启动方式 |
| Secretary 正常、Dashboard／深链／资源失败 | 第二 dist 的 index／产物、`HERMES_DASHBOARD_WEB_DIST` 与 `/dashboard` prefix；代理不要裁路径 |
| WS 被拒／重连失败 | 两进程是否回环绑定，Caddy Host／Origin 改写，Tunnel 是否直达错误端口；不要用 `--insecure` 或放宽认证处理 |
| 第二登录／OAuth 页面 | 检查 `dashboard.public_url` 及环境覆盖；不通过 Access Bypass 绕过 |
| 服务“成功退出”却无监听 | 核实际 MainPID／端口／启动日志，是否 attach 到别的 host；使用本服务的 `--isolated`，不要启动第二后端补救 |
| 浏览器关后提醒不执行／串 Profile | 宿主是否常驻、目标配置／数据库／时区／排期是否合法、是否重复服务、是否把冷态误当取消；保留见证，不清库重试 |
| 后台有执行、页面缺 Timeline／终态 | 核精确前后端版本及正式 WS 恢复证据；接口 200／有界 ring 命中不等于完整恢复 |
| NM 只读 Profile 出现写行为 | 区分自动 NM Thread 同步和手动 CLI；核 archive_enabled、Space 与 workspace 政策；不以只读提示冒充终端隔离 |
