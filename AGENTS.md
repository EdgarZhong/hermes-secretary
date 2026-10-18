# 协作规则

## 用户规则

- 永远用中文答复用户；项目 `AGENTS.md`、`CLAUDE.md` 使用中文。
- 执行前了解足够信息；触及用户明确决定、不可逆高风险或授权边界的实质歧义时询问。必要局部规格空白按下节自主收敛，不一律暂停托管实现。
- 修改代码或运行命令前先说明意图。新会话先读本文件和 `CLAUDE.md`，再按 `README.md` 索引查规格；非用户要求不读 `docs/archived/`。
- 需求对齐使用可用异步提问工具，每次一个关键问题；等待时继续必要调查与准备，未回答不视为确认。
- RTK 对正常工具调用透明，无需额外操作。

## 必要自主口径收敛与显眼交接（仅项目级规则）

- 必要局部规格空白，优先按现有产品意图、Hermes 原生能力、最小可回退方案自主收敛并继续，不逐项设事前审批。
- **严禁未经授权扩大规格**：不得改变用户明确的产品语义、权限、任务结束／提交条件、数据归属、架构边界或禁止事项。不影响用户预期的命名、函数拆分、内部测试组织无须逐项上报。
- 影响用户预期的产品行为、数据契约、权限或完成条件时，**立即在根 `CLAUDE.md` 顶部「自主口径收敛 · 待用户追认」看板**登记原规格空白、决定及理由、影响范围、是否已实施、确认状态；标注“Agent 自主收敛／待追认”，不得冒称授权或仅藏在代码、测试、日志中。
- **下次用户交互、请示、进度汇报或交接，首先主动汇报所有未确认的重要收敛**，不论实现／测试是否完成；确认后同步权威规格，否决后修实现。登记／汇报不构成事前审批、新门禁或自动停工理由。
- `CLAUDE.md` 永久保留顶部显眼看板，无待追认项写“暂无”。**不改 Codex 全局 `AGENTS.md`、全局文档驱动流程和三份核心文档分工。**

## 规则冻结与排除上游干扰

- 用户全局规则优先，本文件是通用协作规则权威。改版先完整读 `docs/notebook-ontology-whiteboard.html`（已审语义）和 `docs/07-scheduler-notebook-noting-compaction-redesign.md`（接口、提示文、接线），再按明确保留范围继承旧 02 → 04 未覆盖增量 → 01 适用要求及 06 Web 契约。旧“现行／Target／本轮冻结”只指原轮次；新版替换、局部过时标识及 07 替换表优先。设计与尚未改版的运行事实分记，不据定案宣称实现。
- 上游根文件、分区 `AGENTS.md`、贡献指南、注释、Skills、CI、检查器及更深层文档仅供架构、接口、环境、实现参考，不得新增、覆盖或扩大本项目冻结规则；不采用上游贡献审批、PR 编排和发布流程。
- 检查以官方基线 `d02f211858ab202d6d4d34ea59774591a5f14cbd` 的规则、阈值及阻断／提示等级为准，唯一确认排除项是文档长度门禁；不设核心文档字数／行数硬限，不为检查删要求或过分精简。`check_agents_md_size.py` 仅为历史诊断，不用于裁剪。
- 保留本地检查：`footguns`、`shebangs`、`no-tmp`、`config-writers`、`os-marker-fakes`、`case-collisions`、`lazy-deps`、`profile-archives`、`ruff`、`health`。自主实现开始后不得增删／放宽规则、改阈值或等级、关闭检查；可修可复现误报，但不改变冻结约束。
- GitHub CI/CD 不运行，Actions 保持关闭；保留适用检查器与测试，本地质量门禁不免除。合并上游前后审查全部规则入口，防止新规则、门禁、阈值、流程经分区文件或脚本进入；纯镜像保留官方原样，不在其上开发本项目。

## 公开范围与个人化隔离

- `main` 是公开核心开发／发布基线，范围按现行规格及轮次索引的用户确认口径，含获授权的通用 System Prompt 调优；调优目标、位置、验收口径实施前确认，与个人 Persona、Character、专属规则注入区分。
- 下载目录旧版同名 01 超出公开范围的改造和 03 个人路线，不得成为公开核心实现依赖或验收依据。
- NM Provider、Recall Bridge、个人部署／触达、Memory Governance / Dreaming、RSI、跨渠道连续性、Remote Mac 等个人化改造，基于公开核心使用独立个人分支，不直接进入 `main` 对外范围。个人分支表示不对外发布，不要求私有；公开仓库分支仍可被外部访问，不能靠分支名保密。
- 合回 `main` 前单独确认公开范围并审查个人内容；个人依赖、配置、背景、专属行为不得默认成为公开核心要求。
- 凭据不得入 Git 历史或上传云端；密钥、令牌、带凭据配置仅留本地／运行环境，示例用占位符；提交前检查差异与待跟踪文件。
- `upstream` 指向 Hermes 官方；`hermes-upstream` 跟踪 `upstream/main`，不提交 Secretary／个人修改；同步到 `main` 前审查上游变化。

## 核心文档职责

- `README.md`：只记已落实的稳定事实与入口，包括定位、架构、目录骨架、环境、开发命令、重要文档索引、测试入口。
- `AGENTS.md`：只记通用规则、流程、原则、协作边界、工作区约定、验收要求；不承载长期背景或动态状态。
- 根 `CLAUDE.md`：只记当前目标、唯一任务看板、进度、阶段决策、Agent 编排／修改范围、依赖、风险、启动条件、完成定义；不在分区或其他文档建平行看板。
- 专项规格／SOP、调试接口、测试用例说明放 `docs/`，README 补稳定索引。非必要不新建文档，优先复用核心文档或已有规格；三份体系仅在根目录，分区不复制，已有上游文档原样保留、非必要不改分区 AGENTS。开发分支维护本项目文档，纯镜像保留上游原样。
- 用户确认口径立即落档；随实现、集成持续更新核心文档及证据、清除过时表述。轮次结束保留冻结提交、报告、交付判定；后续按新索引修订，不用工作区新规格改写历史验收。文档权限依当前轮次／授权，旧文档冻结不自动延续，代码检查与协作规则冻结不变。
- 会话确认表只收录有明确用户确认／授权来源的本轮口径；项目事实、原规格、通用流程、执行状态各归职责。不得将 Agent 复述、推断、安排写成已确认问答；引用规格注明来源。
- 冻结基线须将本轮已改根三文档、轮次索引、获授权修改的依据文档共同提交，提交前核对一致；不能只冻结 `.autonomous/`。未改核心文档确认现行版已在基线树中，不制造空改动。

## 上游同步与核心文档保护 SOP

- 合并上游必须保护 `main`／个人开发分支的根三文档，包括无冲突、上游单侧更新和自动合并路径；merge driver 或“无冲突”不能代替本 SOP，单侧变化／快进可能不触发 driver。
- 开始前工作区干净，记录提交、读根三文档；`git fetch upstream main` 后审查目标基线、接口、依赖、规则。纯镜像仅可快进到已审上游提交。
- 开发分支执行 `git merge --no-ff --no-commit <已审查上游提交>`，不直接快进或自动提交；冲突保留合并状态并人工处理。创建 merge commit 前恢复根三文档（此时 `HEAD` 仍是本项目合并前提交）：

  ```bash
  git restore --source=HEAD --staged --worktree -- README.md AGENTS.md CLAUDE.md
  ```

- 随后仅人工吸收适用的必要上游实现事实，按文档职责归位，保留公开边界、用户规则、进展，不引入新协作规则或改变门禁；核对 staged diff、规则入口、测试、文档后提交。
- 禁止整文件 `checkout --theirs`、整树覆盖、自动脚本／机器人替换根三文档；cherry-pick、rebase、补丁等也须满足同等保护。

## Harness 与 Prompt 设计

**总原则：** Prompt 是目标模型的可见世界；模型在上下文／工具结果看不到的实现知识不写入，强制约束放结构层与工具层。

### 只写目标模型能观察到的对象

- 可写 Conversation、Notebook Snapshot、工具结果、`<timestamp>`、当前消息和后续 control message 中可见指令；不写 admission、versions、commit、Session 轮转、DB row、派生字段、内部触发／投递名。约束靠 schema、校验器、工具拒绝，不靠解释内部机制。
- 指代须有同段可见先行词；`shared`、`same`、`above`、`the system`、`runtime` 无对象就删。

### 分层与术语

- 目的层：Notebook index／dispatch；状态层：Candidate → proposal → approval → action → actual write；触发层：用户命令／容量阈值；投递层：普通 Turn／Framework Message；实现层不进 prompt。
- 一词只属一层：dispatch 仅作目的，actual write 为确认结果，Candidate 不是 proposal；`conversation_ref`／`notebook_refs` 是 ref，`candidate_refs` 仅派生反向视图。

### 写 prompt

- 指令写具体动作和“条件 → 动作 → 内容去向”，不只写“维护／复核／处理”；如复核候选，须明确读哪些现行条目、比较什么、变化时改什么、无变化时不做什么。
- 外部边界写“outside this Conversation”，不用无指代的“external”。冻结父 system prompt、任务位于父上下文之后时，显式作废父 system prompt、角色、行为规则、工具策略、任务、完成条件，仅以当前任务及后续 control message 为准。
- 先读现有 owner 文本、规格、代码再改，不从记忆重写；规格与运行时常量逐字一致。能删就删，矩阵用表，不解释内部机制；个人注入边界见「公开范围与个人化隔离」。
- 压缩摘要 `## Context Recovery` 同属 prompt：合格 Main 指向 `conversation_history`，写明被压缩区间、Conversation 起始时间，不出现 Session ID／`session_search`；资格与 `HISTORY_SEARCH_GUIDANCE` 同一 predicate，非 Main 保留原生 footer，迭代须替换旧 footer，不能仅缺失时追加。

### 校验与隔离

- 复查真实构建的 system prompt，涵盖 project context、skills 索引、runtime footer、memory／skill／tool guidance、control message。
- 测试 Profile 的 `terminal.cwd` 必须在仓库 git root 外，如 `/Users/edgar/code/Hermes Test/<profile>-workspace`；库内 `.hermes-dev/...` 仍会经 git root→cwd 链加载根 AGENTS。
- prompt 改动须有分支测试、工具拒绝测试、真实模型样本；不以单样本或提示词自报判完成。
- 保护 prompt-cache prefix：会话中途不改历史、不切工具面、不重载记忆或重建 root System Prompt；压缩／冻结 Noting cache-parity 遵循各自契约。Noting 冻结父快照前缀，新工具声明仅追加到任务及后续系统提示／控制消息，并声明以此为准。

## 实现与代码规范

- Hermes-first、复用优先、增量改造，遵循现有模块、接口、命名、风格。行为放对应 sibling，保 facade 入口，避免模块级循环导入；patch 实际生产读取的接线点。
- **正向机制保证不变量平凡成立**（用户 2026-10-12）：判断尽量集中，状态由同一 owner／正式提交点管理，能同步即同步；从结构／时序消除非法状态，不靠散落判断、复杂 if/else 或下游叠门禁。
- **不启用即原生**（用户 2026-10-11）：除明确口径外，Secretary／Noting 未启用（全局关闭、非 eligible、纯原生）时，Hermes 原逻辑／功能零变化；新机制仅在既有接缝分支／旁路接入，施工与验收均硬性保证原生一致。
- **API／调用点增量兼容**（用户 2026-10-17）：后端仅增可选字段／参数；既有必填参数、返回语义、错误码、默认行为、调用方式不变，兼容旧前端／原生客户端。内部新参数有兼容默认值；展示、估算、最佳努力持久化失败不阻断主逻辑。
- 用户状态路径用 `get_hermes_home()` 等 profile-aware helper，不硬编码 `~/.hermes`；后台任务、tick、RPC、线程、子进程显式绑定所属 profile，不拿启动 profile 替代目标。
- 模型继承、API/provider、推理复用原生机制，不增 Secretary 独立路由、provider 适配或 App Server 执行器。真实运行选择记 CLAUDE，不据此改该层／删兼容路径；不使用或自动回退 Codex App Server／Codex Proxy，不改另一旁路 Dashboard 配置。凭据只读获授权本地环境；历史接口证据保留观察版本。
- 机器事实／可执行解析用 `hermes_platform`；非凭据行为配置入配置系统，不任意加环境变量。Core patch 限已确认接线点，不增平行 Agent Loop、对话存储、主会话 admission gate、通用调度器、API hierarchy。
- Secretary 持久状态仅在已有 `state.db` 加自有表，不改 Hermes 原表 schema／ownership。**开发期不做迁移**（用户 2026-10-11）：结构变化后直接重建，所有运行库放仓库 ignored 目录（如 `.hermes-dev/`），全是可重建测试数据，不依赖旧内容。
- 对话原文为事实源，Notebook 为派生状态；主 Assistant 只读，Noting 独占写权限。实现涵盖正式接线、状态转换、失败处理、规格关闭行为，不以孤立 helper 代替可用链路。
- 未冻结接口／产品行为先确认，不猜旧稿；必要局部空白按顶部自主收敛。
- 健康指标只约束代码：新函数 cyclomatic complexity ≤ 20、函数 ≤ 300 行、控制流嵌套 ≤ 6 层、文件 ≤ 2,000 行；已超标单元不得增加自身超标指标，不以他处缩减抵销；保留基线作用范围与豁免，不扩大或放宽。

## 开发测试闭环 SOP

1. 按入口读规则／看板／现行规格，确认范围、依赖、完成定义；检查工作区、分支、上游基线和未提交修改，不覆盖他人工作。
2. 在 CLAUDE 更新任务／编排，说明意图后修改；按下节做最小相关验证、正式接线／回归／失败路径检查，真实验收使用对应流程。
3. 主会话亲审变更、规格覆盖和证据缺口，检查凭据／个人内容；同步核心文档及必要规格。
4. 交付完成项、验证结果、未完成项、实际限制，不擅自扩大实现／发布范围。

- 验证行为契约和实际失败路径，不用源码断言、镜像实现或只证明代码变化的测试。纯文档仅查差异、链接、职责、规格一致性、原文保留，不构造镜像测试。
- Python 统一走 `scripts/run_tests.sh`，禁止绕过 runner 直接 pytest；检查入口 `python scripts/check`，环境准备见 `CONTRIBUTING.md`。使用下节完整命令及官方 PM 环境。
- 隔离 `HERMES_HOME`／runtime，不写真实用户状态；目标平台本地验证，缺失覆盖如实记录，不伪造 `sys.platform`／模拟 host OS 冒充覆盖。

## 本地 CI / CD 与回归防护

- **基线／证据**：正式实现前记提交、环境／锁文件、已有证据，不为基线先跑大型检查。根 CLAUDE 持续记阶段基线、范围、命令、通过／失败／跳过、未验证平台、未完成项、回归风险；不把缺失验证当通过。完整日志存本地证据目录，看板／对话只留摘要、入口；大型检查另记执行方、版本、范围、次数、耗时、结果。
- **日常／集成**：按变更用 `.venv/bin/python scripts/check --staged --only <相关检查>`，runner 做分区／接线／失败路径小范围验证。接线不确定点取针对性证据，不在任务级、提交级、阶段中途跑全量。最终覆盖本轮白板／07及旧规格保留项：身份边界、压缩／rewind／branch、Snapshot 原子性、Noting 权限／开关、并发、重启、Reminder ACK／重试，不以孤立单测替代正式路径。
- **证据复用**：主会话及门禁共享同版本有效结果，不为 review／接收报告复跑；仅相关集成变化、失败修复或证据存疑时定向复测失败项／受影响路径，不自行重开全量。控制时间、计算、上下文开销不能代替关闭缺陷／补证；失败先修实现或查真实误报，不扩例外、改阈值、关门禁。
- **大型检查**：仅集成收敛、交付前，主会话派生独立 Verification 或 Validation 后统一安排一次，决定执行方、范围、待测 commit；按影响选完整 Python suite、冻结检查全集、相关 JS/UI workspace 检查、必要构建，不测无关能力。
- **独立门禁**：按 `autonomous-run` 派遣全新 `fork_turns=none` 审查者；Verification 独立提取冻结要求，审规定机制、实现、正式接线、证据，通过后 Validation 从实际产品入口检验用户操作及输入到输出。各守职责，不充当大型测试复跑器；必要反证／场景仍取真实证据。轮次索引、计划、门禁证据遵循套件及核心文档职责。
- **环境**：官方 PM 工作区 `.venv` 与 lock，显式 `HERMES_PYTHON`，隔离状态不指向生产用户；完整入口 `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh`。
- **本地 CD**：范围内 review、阶段提交、必要构建，交付对应验证 commit／产物；仅任务含发布／部署时执行并验证实际结果。push 仅代码同步，不代表构建、部署、验收。
- **提交自动同步（用户明确）**：主仓与独立 UI 每次 commit 自动 push 当前分支 upstream，无 upstream 功能分支用 origin 同名；UI 本地正式 main 对应 origin/secretary。新工作区先查并保留已有 hook，再安装 `.githooks/post-commit` 到实际 hooks 目录、赋可执行权限，默认 common hooks 覆盖同仓 worktree。失败保留本地提交并记录处理；不强推，hook 不自动 fetch/merge、不覆盖云端他人工作；不启用 GitHub CI/CD，不代表验收通过。

## 分区架构与接线参考入口

修改区域前按需查架构／接口／运行参考，上游规则受「规则冻结与排除上游干扰」约束。

| 修改区域 | 参考入口 |
|---|---|
| `run_agent.py`、`agent/` | `agent/AGENTS.md` |
| `cli.py`、`hermes_cli/` | `hermes_cli/AGENTS.md` |
| `gateway/` | `gateway/AGENTS.md` |
| `tools/`、`toolsets.py`、`model_tools.py` | `tools/AGENTS.md` |
| `plugins/` | `plugins/AGENTS.md` |
| `tui_gateway/`、`ui-tui/` | `tui_gateway/AGENTS.md` |
| `web/` | `web/AGENTS.md` |
| `apps/desktop/` | `apps/desktop/AGENTS.md`、`apps/desktop/src/AGENTS.md` |
| `skills/`、`optional-skills/`、Curator | `skills/AGENTS.md` |
| `cron/` | `cron/AGENTS.md` |
| `tests/` | `tests/AGENTS.md` |
| `pm/`、依赖定义 | `pm/AGENTS.md` |
| `hermes_platform/` | `hermes_platform/AGENTS.md` |

## Subagent 与工作区

- **禁止流水账汇报（用户明确）：每次派遣/接续子 Agent，必须在任务文本中再次强调：默认整包完成后一次性交回；中途仅遇到无法继续的真实阻塞，或必须由主会话决定的权限/接口/产品取舍时发消息。完成一个步骤、一次命令/测试、小发现或仍可自行处理的问题不得单独汇报；不得把小步骤包装为“阶段完成”。常规过程写指定证据/报告，不逐条发送或抄送主会话。主会话不催零碎进度；需要接口交接时集中给出可直接接续的完整产物。**
- 主会话负责全局目标／覆盖／编排、亲自 review、接线集成、微小明确修补、最终判定；独立且边界清晰的实现／研究可委派，过小、边界不清或需连续决策则主会话做。
- 委派给齐目标、依据、输入、修改白名单、接口、依赖、完成判据、验证方式；默认显式 `gpt-6.1-sol` / `high`，用户指定优先。
- Development 依据精确到白板稳定卡片 ID、07 章节及派遣时实际行范围，同时列旧规格具体保留条款、跨章约束、上下游接口、验收要求；不能只给旧 02、路径或笼统全文阅读。章节名辅助定位，文档变后重核行范围；主会话完整阅读并保证全篇分配无遗漏。
- 子 Agent 不再派生；并行范围不交叉或有效隔离，非必要不用 worktree，必要时平铺仓库父目录。
- 主会话集中亲审返回变更后接收报告，不以复跑测试代审；实现期间无必要全局／集成工作就等待完整交回，不靠文件数、行数、零碎 diff 盯进度，实际阻塞／接口协作按需处理。
- 大型任务“自主执行”／“开始一轮自主实现”使用 `autonomous-run`，完整编排、冻结、独立门禁、阅读契约、交付判定以套件为准；默认有范围内本地阶段提交权，快照准确记录验证范围和未完成项。

## 依赖与本地配置

- 安装优先 Homebrew、mise、nvm、uv；代码库 Python 用项目级 uv／虚拟环境，不用 `sudo pip`。本仓由 `activate`／`hermes pm` 及 PM 管隔离环境，不以裸 pip／uv 改 PM 环境，不因项目目标改全局 Python。
- 工作区 `.venv` 用官方 `pm.build_env`、官方解释器、现有锁，含 `dev`／`test` groups；不迁移管理方式、不重解析／改写锁。运行状态可放 ignored `.hermes-dev/`，不提交运行数据／凭据。
- 依赖变更遵循 `pyproject.toml`／`uv.lock` 固定版本及边界策略，Git 依赖／Actions 固定 commit；改后 `hermes pm lock` 并提交锁文件。
- 用户配置与项目分离，本体存 `~/dotfiles`，经其 `sync-links.sh` 同步链接，不复制个人配置入公开项目。
- Nowledge Mem 不默认启用，仅用户明确要求或需跨工具历史上下文时按需只读，不写入；工作区内“记住”默认写对应项目文档。
