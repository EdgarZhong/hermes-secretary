# Linux 上云部署 SOP

本文适用于独立 Secretary Web SPA＋原生 Hermes Web Dashboard、同源双SPA、单后端和原生多Profile。**当前仅部署筹备，未连接云端、上传、注册Profile、启动Mutagen/服务/定时器。** 下文命令均为正式部署放行后的操作模板，不能据此宣称已部署或云端验收通过。当前动态状态看根[CLAUDE.md](../CLAUDE.md)；架构依据见[06 §0.7–0.8](06-Hermes-Secretary-Web-UI-V1-Spec.md#07-confirmed-deployment-topology-and-dual-spa-routing-2026-10-17)、[08](08-profile-scheduler-files-clarification.md)。

## 1. 用户已定布局与待定值

| 用途 | 云端 | 本机 |
|---|---|---|
| Core源码仓 | `~/hermes-secretary`，固定已接收commit，官方PM | 本机开发仓不整体同步 |
| Alex物理Home | `~/.hermes_profiles/Alex`，大小写保持 | `/Users/edgar/.hermes_profiles/Alex` |
| study物理Home | `~/.hermes_profiles/study` | `/Users/edgar/.hermes_profiles/study` |
| 两Profile共用工作目录 | **`~/workspace`（单数）** | `~/Desktop/Alex`，Mutagen双向 |
| 原生逻辑注册入口 | `~/.hermes/profiles/alex`、`study`，分别软链至上述物理Home | 本轮不注册真实本机默认根 |
| 两份静态产物 | `~/.local/share/hermes-secretary/static/{secretary,dashboard}` | 已验收dist及外置SHA清单 |
| 完成的SQLite快照 | `~/.hermes_profiles/.snapshots/databases-current.zip` | 同名快照目录，仅云→本机 |
| 同步之外的快照暂存 | `~/.local/state/hermes-secretary-snapshot-staging` | 验证临时目录，不能作为本机运行库 |
| 独立工具 | `~/scrips/nmem-memory.py`、`~/scrips/hermes-sqlite-snapshot.py` | 同路径，各自独立于Hermes |

数据库只有**云端一份运行库**。本机Alex的Pi导入兼容副本是待交付初始数据，不能当另一运行主库；study不导入Pi或合成测试数据。首次交付初始库与之后云端快照回传是不同动作，首次上传须在停机状态按最终批准清单进行，不能放开rawDB双向同步。

两份SOUL本体由用户编辑：`/Users/edgar/.hermes_profiles/Alex/SOUL.md`、`/Users/edgar/.hermes_profiles/study/SOUL.md`。用户定案后逐字上传核SHA；不格式化、补写或另建平行SOUL文档。两者Noting/Scheduler开启；Alex保留原Default读取lane、自动NM Thread同步关闭，study保留已授权学习Space和自动同步开启，不因部署扩大手动写权限。

正式放行前记录：Core/个人插件commit、UI功能commit＋受保护表现overlay、两dist完整清单及清单SHA、独立工具SHA、Linux架构/PM解释器/锁、服务用户HOME、生产模型/API/推理/上下文/时区、端口、Noting联合Idle阈值与延迟、快照频率与保留策略。**已测DeepSeek、自定义262144窗口、100000 tokens、5秒、600秒一天都不是生产定案。** 未确认项目保持原生默认/未配置，不以现存API key自动选定生产模型；当前模板不能直接开业务。

## 2. 固定Core与仅交付前端静态产物

云端Core按已接收版本落在`~/hermes-secretary`，保留锁文件；不上传本机虚拟环境，不裸pip/uv改PM环境。使用符合该版本要求的解释器：

```bash
cd "$HOME/hermes-secretary"
<bootstrap-python> -m pm.build_env --source . --out .venv --group dev --group test
```

Secretary和Dashboard都在本机按配套版本构建并验过后，只交付dist目录＋外置完整文件SHA清单，不上传独立UI源码仓、不在云端npm安装/构建UI。静态目录不能含Home、凭据、DB、日志。Core本身固定仓内的官方资源不是另一份UI部署入口，运行时明确指向交付的两个dist。

每个dist核实际文件集合与逐文件SHA，再核清单本身SHA；不能仅查index或以旧产物代签新源码。已接收v5本机证据的Secretary/Dashboard清单分别为`ac2ad3d842b0c37643588e66fb2618f68e8550e747355e153490e6658623373a`、`cab847d3163f1916f956e033ee405b8cac7eecdd504f00eff1b45241c0922e4a`，对应下表固定版本；后续变更须重新绑定，不能用旧清单代签。后端会注入machine token/改写Dashboard部分前缀，不能要求实际HTML与构建index逐字相同。

已接收v5绑定（云端仍未执行）：

| 项目 | 固定版本 / 证据 |
|---|---|
| Core | `0dc4232f597f0c36d070fd5eabd578366436fca3` |
| Secretary UI | 功能commit `652f487a536874e0405fae547941be36950cc144`＋固定受保护overlay；裸commit不是完整构建输入 |
| 个人插件 | `3732f5503eccc0c97df0ea0238b140b9997e69df` |
| Secretary dist | 439文件，manifest SHA `ac2ad3d842b0c37643588e66fb2618f68e8550e747355e153490e6658623373a` |
| Dashboard dist | 67文件，manifest SHA `cab847d3163f1916f956e033ee405b8cac7eecdd504f00eff1b45241c0922e4a` |
| 本机门禁 | 固定v5 Verification / Validation均PASS，仅覆盖其记录范围，不代签云端 |

本次SQLite快照脚本是**v5之后的运维筹备增量**，已在个人仓提交`4d4a00e56316119ac2e66bc8ffe2c98ece64eaa5`，源码/本机安装SHA均为`6d9d25bf78c526692dde70618f638b837be960e4fc6b134a80892a8a0852d237`；此提交只增加运维工具/测试/文档，既有Provider生产代码保持v5，不冒称上述固定v5门禁覆盖新工具。图标/显示名仅提案，尚未进入上述dist，不能据现有产物宣称Alex/study别名已上线。

## 3. 物理Home、原生注册与共享Files

静态配置准备只包括`config.yaml`、`.env`、`nowledge-mem.json`、`profile.yaml`和已批准插件代码。不得clone测试Home或复制测试DB/session/Notebook/Reminder/active/locks/log/cache、测试AGENTS、时间缩放和仓内cwd。凭据仅保存在本机受限0600文件，正式上传和生产原生Provider选择另经部署放行；不要打印、入Git或复制整份shell环境。

原生ID会把`Alex`规范化为`alex`；仅`HERMES_HOME=~/.hermes_profiles/Alex`会把该物理目录当独立default，发现根错误，不能作为多Profile启动方式。元数据fixture已验证以下既有接缝：原生`resolve_profile_env('Alex')`保留逻辑`profiles/alex`拼写，get_default_hermes_root能找回控制根，目录发现跟随该软链，profile.yaml可给display_name。**尚未在真实Home或云端注册/启动验证。**

正式部署先检查云端现有`~/.hermes`和同名注册，拒绝覆盖未知入口；用户批准后才建立：

```text
~/.hermes/                         原生控制根，不替换已有用户配置
  config.yaml                      default Files仅配置terminal.cwd: ~/workspace
  profiles/
    alex  -> ../../.hermes_profiles/Alex
    study -> ../../.hermes_profiles/study
~/.hermes_profiles/
  Alex/                            用户指定物理目录；profile.yaml display_name: Alex
  study/                           用户指定物理目录；profile.yaml display_name: study
```

两个业务Home的`terminal.cwd`均为`~/workspace`，原生local backend会按实际服务用户展开`~`。default仍是原生控制/Files身份，可能出现在原生列表中；它不是第三个待导入业务Home，不为它创建聊天历史。只对现有default config做必要cwd字段合并，不整份覆盖。Files当前使用default后端，共享目录需与两业务Profile一致；New Chat选择alex/study，列表仍保留跨Profile会话，切换不授权模型读取另一Home。

### 导入的48会话迁到共享工作目录（部署放行后、业务恢复前）

只改Profile `terminal.cwd`不足以迁历史会话：持久`sessions.cwd`优先，原Mac路径存在时会继续进入旧目录，在云端不存在时还可能形成runtime/context cwd分流。正式注册、共享目录存在且唯一后端只读就绪后，先核全受管idle/无lease和在途任务，按Pi导入封存清单逐个确认48个精确stored session_key属于alex，同Conversation Ref/UID/原文一致，**不启动模型、不resume历史**。用现成stored-session RPC逐个迁移，非SQL批量改库：

```json
{"method":"session.workspace.move","params":{"profile":"alex","session_key":"<exact-imported-stored-key>","cwd":"<absolute-cloud-home>/workspace"}}
```

此正式方法不要求live agent；核返回cwd及git metadata，然后只读复查48条sessions.cwd均为共享绝对路径、Profile owner/Conversation Ref/Message UID及消息/root/bindings未变化。原始来源目录继续留在`origin_json.imported_from.source_header.cwd`作为导入溯源，不删除、改成云目录或当作运行cwd。此步当前仅文档规划，**没有打开/修改本机已发布Alex库**；study不参与这48会话迁移。迁完再做新一致性快照，不能拿原物理Home的default身份取证代签alex注册后的正式读取。

Home/控制根目录建议0700，配置/凭据0600。对用户正在编辑的两SOUL不做chmod或重写；部署定案逐字校验。生产保持native code-skew guard默认开启，不复制测试`false`。当前Noting仅设置enabled，联合Idle采用原生默认关闭，待确认生产阈值后再开启；不把测试5秒带入。

### 个人NM插件与独立工具

首次插件作为固定installer＋FILES静态安装包放服务用户`~/.local/share/hermes-secretary/install/nowledge-mem-hermes`，不带收据/缓存、不把整个个人仓或插件运行目录双向同步。对两个明确物理Home使用该已批准源的`nowledge-mem-hermes/install_personal.py --home <home>`预览，再同一版本加`--apply`。安装器只接线静态代码/config，不能clone运行历史或覆盖SOUL；保留原生memory toolset和已撤销Skill状态。检查全部FILES源目标SHA、权限和Space/archive设置。真实客户端配置沿运行主机官方NM机制，不复制本机全局NM凭据，不启Background Intelligence。

Alex `nowledge-mem.json`保留`space: default, archive_enabled: false`；study保留原已授权Space选择与`archive_enabled: true`。关闭自动Thread同步不是终端沙箱或服务端只读凭据；Memory创建/修改仍需具体内容与目标授权，不因安装扩大权限。

`nmem-memory.py`只安装已验收独立文件至服务用户`~/scrips/`，同名未知版本先停下核对，不覆盖。服务PATH含python3/nmem/native curl，实际terminal HOME应为该服务用户HOME，不能偷偷把独立工具复制到各HermesHome。工具不依赖Hermes/Provider路径/HERMES_HOME/cwd，不复制NM凭据。创建一次携内容与Metadata；其它操作官方CLI，unknown/partial不盲重试。`--help`不能代签模型实际使用。

## 4. 同一Mutagen project的三种方向

项目草稿位于本轮ignored `deployment-preparation/mutagen.yml`，不是全局配置；没有setup/teardown钩子、命令、定时器或已创建session。本机已装Mutagen0.18.1，仅查看version/help；未调用list等daemon RPC。现有全局配置保持，不写`~/.mutagen.yml`。正式启动仍先审项目与全局配置的合并影响，必要时显式使用`--no-global-configuration`；当前不执行。

| 逻辑session | alpha → beta | 模式与范围 |
|---|---|---|
| workspace | 本机`~/Desktop/Alex` ↔ `alex:~/workspace` | two-way-safe，整个共享工作目录 |
| profile-config | 本机`~/.hermes_profiles` ↔ `alex:~/.hermes_profiles` | two-way-safe，仅Alex/study的四项非凭据静态配置/SOUL；rawDB、备份子树及所有其它运行态忽略 |
| database-snapshot | `alex:~/.hermes_profiles/.snapshots` → 本机同目录 | one-way-replica，只传稳定名`databases-current.zip`；本机改/删不会反向影响云端 |

这是同一既有SSH/Mutagen通道中的方向分工，不另建HTTP/rsync/S3。普通Home同步明确排除整个`.snapshots`子树，避免它被双向session接管；snapshot session绝不指向运行DB路径。profile配置用明确allowlist，未知新增目录不会自动回传。配置/SOUL双向冲突应人工核对，不用two-way-resolved让一端悄悄获胜。当前草稿不包含`.env`，本机现存密钥仅留本机0600，不默认随双向配置上传；云端生产凭据须后续明确放行并使用原生运行环境机制，不复制本机全局NM凭据。

忽略规则/方向/SSH URL/项目语法依据[Mutagen ignores](https://mutagen.io/documentation/synchronization/ignores/)、[同步模式](https://mutagen.io/documentation/synchronization/)、[SSH](https://mutagen.io/documentation/transports/ssh/)、[project](https://mutagen.io/documentation/orchestration/projects/)。草稿仅做文档与YAML校对，未连接端点验证忽略器或传输；正式放行后先核真实文件allowlist、无rawDB/WAL/SHM/locks/logs进入，再启动。频率未定；本筹备阶段不执行start/create/resume/flush或SSH。

## 5. SQLite快照、完整性与离线恢复

先评估原生`hermes backup`：它可在线备份DB，但全Home包包含本次排除的其它状态/Provider外部目录；`backup --quick`固定STATE_FILES并在Home内建立snapshot/锁与保留策略。两者没有本次“显式DB清单＋同步根外暂存＋全部文件hash完成条件＋稳定文件名”的直接窄入口。因此个人仓新增单一stdlib工具`nowledge-mem-hermes/deployment/hermes-sqlite-snapshot.py`，最终路径为`~/scrips/hermes-sqlite-snapshot.py`，不改Core或Harness生命周期。

操作只在云端，输入明确物理profile根和批准DB列表，不扫描/自动加入未知数据库。每库`mode=ro`连接，用SQLite backup API得到一致副本；关闭连接后检查integrity和foreign_key_check及SHA。**每库内部一致，不承诺跨多个独立库同一事务时点。** 配置/SOUL只按显式静态文件名单读取；从暂存副本形成manifest与全文件SHA。

发布为**固定名、未压缩ZIP_STORED单文件**：manifest与其SHA以及全部DB/静态文件同包，完整close/校验后在同一文件系统原子replace到`.snapshots/databases-current.zip`。暂存在同步根之外，Mutagen只看到完成文件；保留一个当前完成包，不按时间无限新建文件，不因每次改名迫使整份140MB库重传。稳定路径和未压缩布局适合Mutagen差分，但**实际网络增量比例尚未测**，每次本地SQLite快照仍会读取/写入完整副本；频率、磁盘空间与是否额外保留离线历史须最终确认。

以下只是未来手动命令模板，**本包未对真实Home执行**；DB列表在实际创建/启用插件后核定，不把不存在的projects/receipts库当已存在：

```bash
python3 "$HOME/scrips/hermes-sqlite-snapshot.py" snapshot \
  --profile-root "$HOME/.hermes_profiles" --sync-root "$HOME/.hermes_profiles" \
  --staging-root "$HOME/.local/state/hermes-secretary-snapshot-staging" \
  --publish-file "$HOME/.hermes_profiles/.snapshots/databases-current.zip" \
  --database Alex/state.db --database study/state.db \
  --static Alex/config.yaml --static Alex/SOUL.md \
  --static study/config.yaml --static study/SOUL.md
```

`.env`、nowledge-mem.json、profile.yaml可按最终批准清单通过`--static`加入；不自动打包凭据。配置/SOUL直接同步仍保留用户编辑本体，快照中副本只是该批恢复依据，不反写本体。计划快照前避免同时编辑静态配置；不把多个文件复制包装成全局事务。

接收端的`.snapshots/databases-current.zip`只是**待验输入**，不能作为唯一已验副本。`promote`先复制到同步根外私有暂存，再做全包校验；成功才原子提升到`~/.local/state/hermes-secretary-known-good/current.zip`，把上一已验包保留为固定`previous.zip`。坏包/半包验证失败不改这两个已验槽；锁冲突停止，不接管另一提升操作。只保留固定两槽，不无限累计；此为显式命令，不启常驻watcher或定时器。

目的端不能以manifest先到、文件大小、Mutagen“已连接”或ZIP能打开作为可恢复。工具`verify`要求**精确DB集合**、manifest SHA、每个完整文件size/SHA、无缺失/额外/重复/路径逃逸，SQLite再过integrity/FK，全部匹配才算该包可恢复；传输中断、只有manifest、部分payload和损坏文件均拒绝。源命令输出的archive SHA可进一步固定恢复点：

```bash
python3 ~/scrips/hermes-sqlite-snapshot.py verify \
  --archive ~/.hermes_profiles/.snapshots/databases-current.zip \
  --database Alex/state.db --database study/state.db --archive-sha256 <chosen-source-sha>
# 通过全包校验后提升到同步树之外；旧known-good不因输入正在替换/坏包而丢失。
python3 ~/scrips/hermes-sqlite-snapshot.py promote \
  --archive ~/.hermes_profiles/.snapshots/databases-current.zip \
  --sync-root ~/.hermes_profiles --known-good-root ~/.local/state/hermes-secretary-known-good \
  --database Alex/state.db --database study/state.db --archive-sha256 <chosen-source-sha>
# 只从已验槽恢复到尚不存在的新根；绝不覆盖已有Home或运行库。
python3 ~/scrips/hermes-sqlite-snapshot.py restore-new-root \
  --archive ~/.local/state/hermes-secretary-known-good/current.zip \
  --database Alex/state.db --database study/state.db --archive-sha256 <chosen-source-sha> \
  --destination <nonexistent-offline-recovery-root>
```

恢复不自动运行Hermes、不注册新Profile、不重放排期、不覆盖当前库。正式替换云端运行库必须另经恢复放行：停唯一后端、保留失败现场及新写入、完整核定恢复点/源码schema兼容/配置SOUL与UID/Ref/会话对账、检查旧WAL/SHM已脱离运行、再由操作者切换；不可自动从本机快照反覆盖。定频、cron/systemd timer均未启用。

## 6. 单后端原生启动与服务模板

正式注册/配置和产物校验完成后，启动时使用**原生控制根＋显式alex selector**，让CLI保留逻辑Profile路径，不传物理Alex路径替代控制根：

```bash
cd "$HOME/workspace"
HERMES_HOME="$HOME/.hermes" \
HERMES_WEB_DIST="$HOME/.local/share/hermes-secretary/static/secretary" \
HERMES_DASHBOARD_WEB_DIST="$HOME/.local/share/hermes-secretary/static/dashboard" \
HERMES_DASHBOARD_PREFIX=/dashboard \
"$HOME/hermes-secretary/.venv/bin/python" -m hermes_cli.main -p alex dashboard \
  --host 127.0.0.1 --port <backend-port> --skip-build --isolated --no-open
```

上述`-p alex`会使实际Home成为逻辑`~/.hermes/profiles/alex`，两命名Profile由同控制根发现，物理仍为用户的Alex/study。`--isolated`绕过attach-first，**不是**每Profile起一进程；只运行一个backend/worker与宿主Scheduler，不另启Gateway/Cron共用库。`serve`只可能返回headless握手页，不能代替双SPA。不得带入HERMES_SERVE_HEADLESS、Dashboard public_url或Desktop的父进程/SSH/token变量。

服务账户的HOME必须指向上述真实用户目录；不复制整个shell环境。systemd只在正式部署时创建专属unit，用绝对路径替换`<cloud-home>`（EnvironmentFile不展开`$HOME`）：

```ini
[Service]
Type=simple
User=<service-user>
WorkingDirectory=<cloud-home>/workspace
Environment=HERMES_HOME=<cloud-home>/.hermes
Environment=HERMES_WEB_DIST=<cloud-home>/.local/share/hermes-secretary/static/secretary
Environment=HERMES_DASHBOARD_WEB_DIST=<cloud-home>/.local/share/hermes-secretary/static/dashboard
Environment=HERMES_DASHBOARD_PREFIX=/dashboard
ExecStart=<cloud-home>/hermes-secretary/.venv/bin/python -m hermes_cli.main -p alex dashboard --host 127.0.0.1 --port <backend-port> --skip-build --isolated --no-open
Restart=on-failure
KillSignal=SIGTERM
TimeoutStopSec=180
UMask=0077
```

unit还须补标准network-online依赖、安装目标及实际PATH（python3/nmem/curl等）；不在筹备阶段注册/启用。后续修改源码/HEAD可能触发native code-skew退出，最终固定版本后安全重绑定，不关guard。不用全局dashboard/serve --stop、pkill或强杀接管其它服务。

## 7. 回环反代与Cloudflare（用户后续配置）

```text
浏览器 → Cloudflare Access → Tunnel → Caddy 127.0.0.1:<proxy-port>
       → Hermes 127.0.0.1:<backend-port>，唯一backend
         /                         Secretary Web
         /dashboard、/dashboard/   原生Dashboard
         /api/*、/api/ws            同源API/WS
         /dashboard/api/*          后端重写至共用API/WS
```

Caddy仅回环，Host改回backend、删除Origin；不剥`/dashboard`，不另起API域名/CORS/多worker：

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

Cloudflare Tunnel指向该proxy回环端口；Access覆盖整个hostname和邮箱allowlist，不给API/WS设Bypass。两SPA各自index注入原生machine token，Access是用户可见登录层。用户后续自行配置Access/Tunnel；本包不创建、修改、启动或验收任何云端入口。

## 8. 正式验收、升级与回滚

部署release后先代理回环、再公网。真实浏览器从入口进入，核两个SPA资源、Dashboard子路径刷新、同源REST/两WS/404边界、alex/study owner/图标/显示名/跨Profile列表和Files default共享cwd。Alex复用现主头像/图标、study复习图标；现前端只需增加规范id的图标别名并消费原生display_name，提案待UI owner review，未覆盖用户表现层。本机隔离副本已通过原生alex注册、Web同参数session.resume、owner绑定与History消费检查，未构建模型；该检查发现旧cwd优先，已列入第3节正式move步骤。它不代签云端已部署，也不代签正式库迁后结果；部署时仍只读复核owner/History/共享cwd，不迁移或重建旧库凑结果。

经用户授权才做少量合成模型/Reminder场景，覆盖冷态宿主触发、事先连接/中途接入重连/完成后冷开、真实Thinking/工具/终态、关闭后资源归零；无reasoning记未覆盖，不伪造。模型跨Profile/NM权限不因统一列表扩大，NO_REPLY仍未实施。UI接口证明与真实页面分开记录，Cloudflare/TLS/Linux/systemd/手机未执行不填PASS。

升级前记录Core/插件commit、dist清单、独立工具、配置SOUL指纹和已验证快照。准备新版本后等活动Turn/Noting结束，安全停唯一backend、保留工作数据，再于`~/hermes-secretary`核固定版本/锁及PM环境后起服；不在活Turn中git pull或替换解释器。失败保留原库/新写入/日志，核schema兼容后恢复已接收源码和配套dist；不兼容时先确认恢复点再离线恢复，不清空Home、不自动用本机旧库覆盖。
