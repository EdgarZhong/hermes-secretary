# B1 后端历史增量与手动压缩恢复交接

状态：B1、U13、U17 白名单实现与定向验证已交回，待主会话亲审；U17 已按用户确认实现“旧的模糊片段保持懒取，新 Turn 精确主动取 Thinking”。未提交、未部署、未调用生产模型或真实外发。

## 1. 对应条款与版本

- 依据冻结 `cf5742c70b26e0dc954eabcb4b07c232c5231013` 的06顶部 C0–C3、D01–D05／D15、S01–S08／S11–S14／S18及P01／P06；本轮 plan 工程接口1–5，保留旧 REST／activate 默认行为。
- U13增补依据 `394a08604fd29bac12d706f125c60b243afb2274`：原生手动压缩 busy 与生成 Turn 的恢复证明分开，保双快照、连续原生cut和真实运行状态。
- 主会话后续明确：完整详情 revision 变化即使 cards coverage 不变，opt-in RPC 也必须 unmatched 并返回变化 cards；Thinking 同行可短读完整事实用于锁外完整详情 hash，wire 不携未展开工具详情；queued／typed source 按原生事实识别。U17 用户决定优先于此前保守多取方案：旧的模糊片段保持懒取，新 Turn 精确主动取 Thinking；仅原生新 Turn 构建接缝写入可选内部来源标记。
- 工作区 `/Users/edgar/code/hermes-secretary-incremental-sync`，分支 `codex/incremental-sync-20261027`，交回 HEAD `0b596ad4c7e6ff523a3cafbac62ec6c126b81bcf`（已含主会话集成 U16；本包产品修改仍未提交）。实现期主会话提交了文档增补，交接精确 HEAD、十一文件 SHA、PM锁 SHA 见 ignored `backend/snapshot.json`，不把初始冻结或文档 HEAD 冒称已提交产品版本。

## 2. 实际改动

十一个代码／测试文件及本报告。U17 按主会话追加白名单接入原生新 Turn 构建与必要的 metadata 补写；无生成协议、server.py、Noting、schema、核心文档或 plan 改动。

| 文件 | 改动 |
|---|---|
| `hermes_state_history_sync.py`（新） | 短期有界 fingerprint LRU；完整可见详情 revision；同快照最新 Thinking 候选读取、锁外投影；按窗口统一差分。 |
| `hermes_state_recovery_view.py` | 内部可选 history_sync／native_source；同一 SQLite 快照加入额外 Thinking 事实；原窗口、详情及额外 Thinking 统一在锁外投影与 hash。 |
| `hermes_cli/web_routers/sessions.py` | REST 可选 history_sync=1／sync_cursor；仅 recovery_view 或 detail_row_ids 生效；详情 opt-in 加 detail_revision；旧默认不追加 sync／revision。 |
| `tui_gateway/recovery_view.py` | RPC recovery_view.sync_version=1、window.cursor；保 receipt 归属校验；D0／S／D1核完整 revision 和额外 Thinking；详情变化强制 unmatched；区分原生手动维护阶段。 |
| `tests/hermes_cli/test_history_sync.py`（新） | 真实 SQLite＋正式 REST 的差分／回退／owner／详情／Thinking／字节与小 wire fixtures。 |
| `tests/tui_gateway/test_history_sync.py`（新） | 正式 session.activate、原生 snapshot／replay、完整详情竞态、跨首屏Thinking竞态、原生source／跨渠道覆盖。 |
| `tests/tui_gateway/test_manual_compress_recovery.py`（新） | 真实 _manual_compress_turn、原生 settlement／terminal持久化、实际 compress core、失败／取消／排队接棒与证明拒绝。 |
| `agent/turn_context.py` | 在真实新 Turn staging 合并内部来源标记；既有持久锁内在普通 flush 后处理必要的 prewritten metadata 回填。 |
| `agent/turn_source.py`（新） | 复用原生 UID／Turn ID，合并 metadata；普通新消息直接沿原生 flush，不另开 metadata 写事务；失败为展示级 best effort。 |
| `hermes_state_turn_terminal.py` | 复用既有 metadata writer sibling，准确 UID／物理来源／原生 lineage 与 lease guard 下，只补写当前可见代表的 metadata。 |
| `tests/agent/test_turn_source_persistence.py`（新） | 真实 AIAgent 新 typed Turn→SQLite→冷进程 REST，CLI 预写、原地压缩、branch／rewind／同 UID 代表、guard、失败不阻 Turn及模型 wire／cache prefix。 |

缓存每进程最多128窗口、TTL一小时；每项仅保存 owner、行ID→hash、Thinking ID→hash与coverage，不保存正文／Thinking／工具参数结果。owner包括 resolve 后的实际DB路径、实际Profile、requested Conversation、规范selector、投影版本。窗口与Thinking联合身份超过500时不留该项，后续安全回退快照。缓存锁仅保护短期字典／LRU；DB／history／replay锁内不做正式显示投影、hash或序列化。

## 3. 正式路径与边界

### REST／RPC

REST `/api/sessions/{id}/messages?recovery_view=1&history_sync=1&sync_cursor=...` → 既有 Profile DB owner → read_view 的单 SQLite snapshot → 既有 _project_for_display／history_cards → 窗口完整详情 hash → synchronize_window。snapshot 返回全部 cards；delta 仅新增／变化 cards；sync.order始终是该窗口完整权威物理行顺序，sync.revisions是完整窗口的详情版本。删除靠order排除，返回行数以coverage.window.returned为准。

RPC `session.activate` 保原 receipt 与 owner核验，增加 recovery_view.sync_version=1、各window.cursor。D0／原生S／D1捕获、原生snapshot／epoch／seq、后续read_replay_cut仍由原机制负责。仅opt-in计算完整详情 revision；同cards不同详情不再matched。合法cursor无变化可matched并省messages；缺失／空／过期／不认识或跨owner的cursor提供必要窗口snapshot，不依赖REST与Gateway共享进程内存。旧未opt-in的matched／默认回复保持。

详情仍沿原detail_row_ids最多12行；opt-in返回detail_revision，使用与窗口同一完整可见投影。hash不含api_content、Codex原始replay字段或opaque reasoning签名／加密项；公开commentary与原生可读Thinking文本保留。默认旧详情正文与字段不变。latest_thinking只发送原消息身份／Thinking字段／source／order／positions／revisions，不携正文、未展开工具参数结果或原始事件；可读reasoning_details采用去除opaque材料的原生文本项。

### 最新 Thinking 来源

- 优先读取当前原生 _terminal_source；完整保留的原生输出快照中 source／user_committed／完成receipt可提供身份级来源。只复制UID／物理行／Session身份，不复制输出正文。
- 活动原生来源须与当前DB可见代表、原生运行证明配合；旧本地快照不覆盖更新的外部Turn租约。已完成的本地来源也不能覆盖逻辑顺序更晚的可证明跨渠道来源。
- 持久事实使用同一 SQLite snapshot 的原生 UID、display_kind、QUEUED_PROMPT_METADATA_KEY 及 metadata origin／producer。合法 turn_source 要求 message_uid 与本行同 UID、turn_id 为非空字符串；它与同 UID turn_terminal 是明确证据，优先于仅 queued 的弱标记。其次使用普通非 queued User／auto_continue；排除 steer、hidden、model_switch、skill_invocation、compaction、Framework／Notebook／Noting 结果。
- 最新候选只在最近500条逻辑位置内；跨首屏仅读取有Thinking候选的完整同行事实用于同一个详情hash，未请求的非Thinking行不额外hydrate。Thinking同行工具参数原位变化会改变revision，但工具正文不进入bundle或服务端缓存。
- 无 source 标记、无法证明是否启动 Turn 的 typed 行若位于最近可证明 source 之后，则 latest_thinking.source=null、order=[]、rows=[]，旧详情继续懒取；完整 retained snapshot 也不能跨过这个未知边界。当前 active 原生精确 source 仍可提供强证明。
- 原生 `_stage_turn_user_message` 仅为本次真实新 user 对象合并 display_metadata.turn_source，复用原 UID 与当前 Turn ID；不为普通 append、Steer 或历史回放补猜。普通新 flush 已持久化该 metadata，不额外写 DB。CLI 预写／早期原地压缩可能跳过该行 metadata flush，故在既有 `_persist_turn_start` 同 persist 锁内，对准确 UID 的当前可见代表补写 metadata；复用原 DB 事务及 turn lease guard，无正文重写／新 schema／新事件。保留其它 metadata、role、content、timestamp 及 transcript CAS 语义；失败不阻主 Turn。
- 新内部 turn_source 与 provider replay／opaque 材料均不进入可见详情指纹；真正 Thinking／工具详情变化仍改变 revision。原生 provider 剥离契约保证 turn_source／display_metadata 不进模型 wire，连续两 Turn 的前缀和 token 估算保持一致。

### 手动压缩恢复

原生 _manual_compress_turn 在history_lock下置 _manual_compress_active 与running，而不建立生成Turn／Main租约。新分支只在该原生flag明确且没有冲突Main租约、没有真实活动inflight时允许维护证明；保留失败inflight对象时，还须精确DB路径／UID／物理行及原生已持久terminal、outputs_complete证明。无证明的残留对象继续失败。

维护对外仍running=true／真实busy，不伪造Turn、source、lease或旧inflight正文；仅明确无有效inflight的安全维护阶段允许建立空native cut。旧输出调用原idle／terminal严格核验，而非因manual盲弃；存在未核验输出仍拒绝。manual phase、inflight token／终态、source身份纳入D0／S／D1上下文稳定性；Main租约冲突／phase变化均拒绝或有界重试。正常自动压缩中的生成Turn仍需原生source和Main租约，未宽放。

## 4. 验证证据

全部测试使用官方PM共享`.venv`与 `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh`，单文件子进程隔离、retries=0。宿主macOS arm64、Python3.14.7；真实SQLite、正式FastAPI route／session.activate、原生snapshot与replay；模型／摘要器／执行等待点为受控替身，无生产模型或真实微信外发。

B1／U13 阶段有效证据为 **9 文件199项**，由 `final-tests.log` 其它7文件165项、`source-final-tests.log` 16项和 `manual-final-tests.log` 18项组成。U17 最终相关回归见下表：8 文件124项通过；随后仅内部标记排除指纹的小修再测 REST／RPC 两文件61项通过，其中新增1项正式反例。旧证据中来源读取文件以 U17 新结果替代；未改手动维护／原生恢复的范围复用原证据，不把重叠运行次数相加冒称覆盖项数。

| 证据（ignored `.hermes-dev/incremental-sync-20261027/backend/`） | 结论 |
|---|---|
| `legacy-tests.log` | 初始3文件107项旧接口／cards／恢复回归通过；最终同范围复核仍包含在final-tests。 |
| `final-tests.log` | 一次9文件定向回归；其它7文件165项通过。RPC文件原15项通过后新增已完成跨渠道分支，以最终16项复核替代。手动文件新增valid夹具误释放Main租约导致1项失败，修正测试条件后整文件18项通过。 |
| `source-final-tests.log` | 16项正式REST→RPC、详情变化unmatched、D0/S/D1窗口／跨首屏Thinking竞态、原生source／保留snapshot／外部活动和已完成Turn通过。 |
| `manual-baseline.log` | 改前真实 _manual_compress_turn 无inflight却busy时，正式activate complete=false的反例失败。 |
| `manual-final-tests.log` | 18项通过；真实维护context、完成／异常／取消、native压缩原地／轮转、queued原生drain接棒、source／lease缺失拒绝、旧输出证明、terminal残留、native epoch连续性。 |
| `delivery-checks.log` | B1 七文件阶段十项冻结检查通过。 |
| `u17-baseline.log` | 用户确认的旧模糊片段保持懒取：改前正式 REST 反例失败，旧实现错误地多取 Thinking。 |
| `u17-final-tests.log` | U17 8文件124项通过：真实 Turn 持久链、REST／RPC来源、metadata／增量flush／terminal与租约原生回归。 |
| `u17-private-revision-baseline.log`／`u17-visible-final-tests.log` | 内部标记不影响用户可见指纹：正式 REST 改前1项失败，修后 REST／RPC 61项通过；包含详情／额外Thinking D0/S/D1竞态。 |
| `u17-final-checks.log` | 最终独立 index 纳入本包十一文件，十项冻结检查通过；health 相对 main 基线涵盖25文件（含已集成 U16 十四文件），0 blocking／0 advisory。临时独立 GIT_INDEX_FILE，不改正常 index 或他人 dirty。 |
| `snapshot.json`、`patch.diff` | 最终精确HEAD／分支／十一文件SHA／锁SHA与可review差异（含新文件）。 |
| `wire-fixtures.json`、`rpc-wire-fixture.json` | 正式入口产生的小型可消费样本，分别约7.1KB、6.7KB；含snapshot／无变化／追加及REST→RPC owner／receipt／cursor封套。 |

覆盖的关键边界：

- 有效／空／未知／丢失／过期cursor、LRU淘汰、不同Conversation／selector／真实Profile／实际DB路径；独立新Python服务进程不认识旧cursor时提供完整必要窗口。
- 无变化、少量追加、删除、同UID新物理代表、原位Thinking／工具参数修改、rewind、原地压缩／Session轮转、跨渠道写入；cards不含的详情变化仍有新revision。
- 详情opt-in revision与对应窗口完全一致；provider replay／opaque签名变化不改变可见revision；原生可读reasoning_details完整保留，不外发opaque材料。
- 最新Thinking跨首屏、500范围限制、中途Steer／Framework／queued、真实auto_continue／terminal来源、旧未知 typed 边界懒取、新合法 marker／queued 启动精确来源、晚到旧 snapshot 不越界；同行工具参数改写改变hash但wire无参数；opaque-only及malformed sidecar不额外hydrate非Thinking行。
- D0／S／D1之间通过真实另一个SQLite连接／进程原位改写、追加、rewind、删除、压缩；一次变化重试后收敛，持续变化两次后有界失败；hash／投影锁外验证。
- 手动phase切换测试在原生snapshot接缝受控调用真实_manual_compress_turn退出，重入锁夹具使该native变更可在同一线程精确发生于S，随后按真实上下文检查重试；实际生产锁序未改变。实际compress测试使用原生compress core／真实SQLite提交，摘要器为受控替身。

### 200条长正文传输量

`wire-bytes.json`记录正式REST返回的UTF-8 JSON字节（未压缩），每场景一次请求：

| 场景 | JSON字节 |
|---|---:|
| 完整200条窗口 | 6,873,547 |
| 同窗口无变化 | 16,205 |
| 少量追加后200条当前窗口 | 16,757 |

无变化／少量追加约减少99.76%的JSON字节。仅证明该受控数据的payload，不冒称生产弱网耗时或HTTP压缩后的真实流量；运行生成时间戳尾数变化可使完整样本差1字节，以JSON证据为准。

## 5. 缺口与限制

U17 已关闭此前“无标记 typed 历史保守多取”缺口。真实新 Turn 的来源在原生构建边界写入；历史旧 typed 行无法证明是否启动 Turn 时，按用户已确认兼容策略不主动取 Thinking。该旧片段仍可沿既有详情接口按需读取；不迁移、不回填猜测来源，不把旧数据兼容边界冒称已精确追溯。

原生 `session_notifications._notif_submit` 与 `bot_mode_dm._persist_reply_when_done` 的 process_complete 同型行分别可为真实 Turn／仅投递，因此读取不靠 display_kind 猜启动。新测试使用真实 AIAgent.run_conversation typed 输入、原生 staging／flush／provider 构建、实际 SQLite，并通过独立 Python 进程正式 REST 验证 runtime 丢失后仍只取最新 Thinking。普通 append 的同型行不生成 marker，旧 unknown typed 后 bundle 为空。没有用 isolated helper 或测试自建 marker 冒充原生新 Turn 持久链；合法／畸形 marker 的读取分支另外直接构造 DB 事实覆盖。
没有生产部署、真实模型／微信发送、真实浏览器／APK或Linux验证。本包提供后端真实入口证据与fixtures，前后端wire联合、实际App与独立双门禁仍由主会话统一安排。未把新UI、权限、完成条件或原生事件格式纳入实现。

## 6. 接口影响

- 仅可选 REST query、RPC现有 dict 内的可选 sync 字段、opt-in 详情 revision，及新 Turn 的内部 display_metadata.turn_source。无生成协议、数据库 schema、持久事件日志、新执行器／调度器；旧 API 默认行为保持。
- sync版本1；cursor不透明且可随时安全失效；delta messages不能按追加拼接，必须按完整order／revisions／coverage重建。匹配需包括详情版本，unknown cursor不能凭只含cards的旧receipt猜完整详情仍有效。
- latest_thinking与窗口共用cursor，无逐Thinking游标；完整详情hash可能因同行其它可见详情变化而更新，但bundle仅传Thinking。已完成跨渠道来源覆盖旧本地snapshot，活动prefix仍只由既有原生完整snapshot／cut证明。
- 手动维护恢复修复适用于已有recovery调用，不改变真实busy、压缩owner、生命周期或操作权限；自动压缩仍为普通生成Turn证明。

## 7. 建议后续

主会话亲审十一个文件及正式上下游，与 F1 真实 wire／缓存／前缀恢复集成；复用本包同版本证据，只有集成变化或发现证据问题时定向复测。完成整轮独立Verification／Validation后再判交付。本包未commit／push／部署，不修改plan或核心文档，不触碰并行前端报告／其它dirty。

## 8. 主会话接收（2026-10-27）

已亲审十一文件、正式REST／activate接线、原生Turn staging与持久锁／lease guard、完整详情指纹与有限游标缓存，以及真实AIAgent→SQLite→独立进程REST来源测试。最终十一文件SHA与snapshot.json逐一匹配。U17旧片段懒取、新来源精确定位已落实；普通新消息无需额外metadata事务，预写／压缩代表回填不改正文、timestamp及模型wire。沿用有效定向测试，不复跑无关整套。前后端最终联调、Linux及全轮双门禁尚未完成，未部署。
