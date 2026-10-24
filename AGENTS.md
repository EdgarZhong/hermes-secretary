# 协作规则

## 用户规则

- 永远中文答复；项目AGENTS、CLAUDE使用中文。新会话先读本文件与CLAUDE，再按README索引查规格；非用户要求不读`docs/archived/`。
- 命令运行、文件修改前说明意图。先调查足够信息；涉及用户明确决定、权限、不可逆高风险的实质歧义必须询问。需求对齐用异步提问，每次一个关键问题，未答不算确认；等待时继续独立调查。
- **显示保护**：界面验收只许自己创建的Codex隐藏IAB（`iab`、`visible:false`）。禁止桌面控制、外部浏览器、可见页、切焦点，以及`open`、`open_in_codex`等显示状态变化；不得动用户现有页面。无法保证后台执行就记未验，不回退其它方式。每次UI委派重申。
- RTK正常使用，无须额外操作。Nowledge Mem不默认启用，仅明确要求或需跨工具历史时按需只读，不写入；工作区内“记住”默认写项目文档。

## 必要自主口径收敛与显眼交接

- 必要局部空白按现有产品意图、Hermes原生能力、最小可回退方案收敛；不扩大用户已定的产品语义、权限、结束/提交条件、数据归属或架构边界。
- 影响用户预期的行为、数据契约、权限或完成条件时，立即登记根CLAUDE顶部永久保留的“自主口径收敛 · 待用户追认”：原空白、决定与理由、影响、是否实施、确认状态，明确“Agent自主收敛／待追认”。下次交互首先汇报未确认重要项；确认后同步规格，否决后修实现。不冒称授权，也不把登记变成事前审批或自动停工。
- 无待追认项写“暂无”。命名、函数拆分等内部选择无须逐项上报。不修改Codex全局规则或三核心文档职责。

## 规则冻结与排除上游干扰

- 最新产品文档及明确用户口径优先；技术规格也接受审查。冲突分别记录规格偏离、实现偏离和证据缺口；不因符合旧技术稿就判通过，不从未来愿景扩大范围。历史验收只对应当时版本。
- 改版先完整读Notebook白板和07；按明确保留范围继承02→04未覆盖增量→01及06 Web契约。旧“现行／冻结”只属原轮次，新替换关系优先；设计定案不等于已经实现。
- 本文件是通用规则权威。上游／分区AGENTS、贡献指南、Skills、CI、检查器只供架构、接口、环境参考，不新增或扩大本项目规则、审批／PR／发布流程。
- 检查冻结于官方`d02f211858ab202d6d4d34ea59774591a5f14cbd`的规则、阈值及等级；仅排除文档长度门禁，不为检查裁剪要求。保留`footguns`、`shebangs`、`no-tmp`、`config-writers`、`os-marker-fakes`、`case-collisions`、`lazy-deps`、`profile-archives`、`ruff`、`health`。自主实施开始后不得增删、放宽、关闭或改等级；可修复真实误报但不改变约束。
- GitHub Actions保持关闭，本地质量检查照常；上游同步前后审全部规则入口，防止新门禁／阈值／流程被带入。纯镜像保留官方原样，不在其上开发。

## 公开范围与个人化隔离

- `main`为公开核心基线；通用System Prompt调优须先确认目标、位置和验收，不等同个人Persona／Character／专属规则注入。旧下载目录01越界改造及03个人路线不作公开核心依赖。
- NM Provider、Recall Bridge、个人部署／触达、Memory Governance / Dreaming、RSI、跨渠道连续性、Remote Mac等在独立个人分支／仓库。个人分支不代表保密，合回main前单独确认范围、审查个人内容。
- 凭据不得进Git或上传云端；只留获授权本地／运行环境，示例用占位符。提交前审差异和待跟踪文件。
- `upstream`为Hermes官方，`hermes-upstream`只跟踪`upstream/main`，不提交Secretary或个人修改。

## 核心文档职责

- README只放已落实的稳定事实、架构／目录、环境／命令和重要文档索引。
- AGENTS只放通用规则、流程、原则、协作边界和验收要求；CLAUDE只放当前阶段、唯一任务看板、必要编排、风险、待决及完成条件。三份只在根目录，不在分区复制或另建平行看板。
- 专项规格／SOP／调试接口／测试说明放`docs/`并补README索引；**运维变更和回滚记录统一`docs/operations-log.md`**，不堆入核心文档。非必要不新建文档，尽量复用现有文件。
- 用户确认立即落档，随集成更新现状并去除过时表述；会话确认表只收真实用户确认，不把Agent推断／执行状态冒充授权。历史冻结提交、报告、证据和判定保持原时点，不用新规格改写历史；专项文档权限按当前轮次，旧冻结不自动延续。
- 冻结基线必须包含本轮已改根三文档、轮次索引和获授权依据文档；未改文件确认已在基线树内，不制造空修改。规则冻结不因轮次／文档权限变化失效。

## 上游同步与核心文档保护 SOP

1. 工作区干净，记录HEAD并读三核心文档；fetch后审目标提交、接口、依赖和规则。镜像仅快进到已审上游。
2. 开发分支使用`git merge --no-ff --no-commit <已审提交>`，不快进或自动提交；人工处理冲突。提交merge前执行：

   ```bash
   git restore --source=HEAD --staged --worktree -- README.md AGENTS.md CLAUDE.md
   ```

3. 按职责人工吸收必要上游实现事实，保留用户规则和范围；核staged diff、全部规则入口、测试和文档后提交。

保护覆盖无冲突、上游单侧更新和自动合并；merge driver不代替本SOP。禁止整文件`--theirs`、整树／机器人覆盖；cherry-pick、rebase、补丁同样适用。

## Harness 与 Prompt 设计

- Notebook内容选择须服从已确认的生命周期与结算边界：外部成功交接范围按规则退出，不能因“以后可能仍有用”另设保留豁免；未覆盖内容、后续变化、未完责任及其必要上下文仍按原规则处理。审Prompt须同时防积压和误清退，不用宽泛有用性覆盖结算，也不把成功交接写成无条件删除整条记录。

- Prompt是模型可见世界：只写Conversation、Notebook内容、工具结果、timestamp、当前及后续control message中的对象；不解释admission、versions、commit、Session轮转、DB row、派生字段或内部触发／投递名。强约束在schema、校验器和工具层保证。
- Snapshot ID、Pointer、Coverage anchor审计标识不进模型正文；注入完整Notebook及有意义覆盖说明。History的message_uid、可操作entry_id和既有客户端API身份按各自契约保留；这不是人类UI隐藏要求。
- 指代须有同段可见先行词；外部边界写“outside this Conversation”。层次分清：目的index／dispatch；状态Candidate→proposal→approval→action→actual write；触发用户／容量；投递普通Turn／Framework Message。`conversation_ref`／`notebook_refs`是ref，`candidate_refs`仅派生反向视图。
- 写具体“条件→动作→内容去向”；先读owner文本、规格和代码再改，规格与运行常量逐字一致。冻结父Prompt后执行新任务，显式作废父system／角色／规则／工具策略／任务／完成条件，仅遵循新任务及后续control message。
- `## Context Recovery`：资格与`HISTORY_SEARCH_GUIDANCE`共用predicate；合格Main指向`conversation_history`，说明被压缩区间和Conversation起始时间，不出现Session ID或`session_search`；非Main保留原生footer，迭代替换旧footer。
- 检查真实构建的全Prompt，包括project context、skills、runtime footer、memory／tool guidance和control message；改Prompt需分支／工具拒绝测试及真实模型样本，不能靠单样本或自报。
- 保护cache prefix：会话中途不改历史、工具面、重载记忆或重建root System Prompt。工具面变更在父运行态正常构造／恢复边界生效并如实记录缓存变化；Noting冻结后继承父完整工具表，不在子任务临时补工具。任务及后续提示／control message明确当前身份权限，遵守压缩／Noting cache-parity契约。
- 测试Profile的`terminal.cwd`必须在仓库Git root外；库内`.hermes-dev/`仍会加载根AGENTS。

## 实现与代码规范

- Hermes-first、复用现有接口与风格，行为放对应sibling、保facade；避免模块循环导入，patch正式读取的接线点。判断集中、状态由同一owner／提交点管理，优先同步，从结构和时序消除非法状态，不堆下游门禁。
- **不启用即原生**：全局关闭、非eligible、纯原生路径零行为变化；新机制仅从既有接缝分支／旁路接入。
- **增量兼容**：API仅增可选字段／参数，内部新参数有默认值；原必填、返回语义、错误码、调用方式和默认行为不变。展示、估算、最佳努力持久化失败不阻断主逻辑。
- 路径用profile-aware helper；任务、tick、RPC、线程／子进程绑定目标Profile，不借启动Profile。模型继承、API／Provider、推理沿用原生，不增Secretary独立路由／适配／App Server执行器；不回退Codex App Server／Proxy，不改另一Dashboard旁路配置。
- 平台事实／可执行解析用`hermes_platform`，非凭据行为进配置系统，不任意加环境变量。Core patch限已确认接线点，不新增Agent Loop、对话存储、主会话admission gate、通用调度器或API hierarchy。
- Secretary状态只在既有`state.db`加自有表，不改原schema／ownership；开发期不迁移，结构变化重建ignored测试库。原文为事实源、Notebook为派生，Main只读、Noting独占写。覆盖正式接线、状态转换、关闭和失败路径，不以孤立helper代替链路。
- 未定产品行为先确认；必要局部空白依自主收敛规则。健康阈值：新函数复杂度≤20、长度≤300行、嵌套≤6层，文件≤2000行；超标单元不得增长自身超标指标，不能靠他处缩减抵销；保留冻结作用范围和豁免。

## 开发测试闭环 SOP

1. 读规则／看板／当前规格，核分支、基线、依赖、完成条件和dirty，保护他人工作；在CLAUDE登记本轮范围／编排后实施。
2. 说明意图、增量修改；按行为契约验证正式接线、失败路径与原生回归，不写镜像实现／源码断言测试。纯文档只审差异、链接、职责、规格和原文保留。
3. 主会话亲审覆盖、接口、失败状态、证据缺口及凭据／个人边界，更新文档；交付完成项、验证、未完成与限制，不扩大发布范围。

Python只用`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh`，禁止直接pytest。检查用`.venv/bin/python scripts/check --staged --only <相关检查>`；环境见CONTRIBUTING。隔离HERMES_HOME／runtime，目标平台真实验证，缺覆盖如实记，不伪造OS。

## 本地 CI / CD 与回归防护

- 实施前记提交、环境／锁和已有证据，不为基线先跑大套。CLAUDE只留当前验证摘要和证据入口；完整日志本地保存，大型检查记执行方、版本、范围、次数、耗时及结果。
- 日常只跑相关分区、接线和失败路径。最终按本轮白板／07及保留规格覆盖身份、压缩／rewind／branch、Snapshot原子性、权限／开关、并发、重启、Reminder ACK／重试。
- 主会话和门禁复用同版本有效证据；仅集成变化、失败修复或证据存疑才定向复测，不为review复跑全量。先修失败或核真实误报，不扩例外、改阈值、关检查。
- 大型检查只在集成收敛、交付前，派生独立Verification或Validation后统一安排一次，明确执行方／待测提交／相关范围；不测无关能力。使用官方PM `.venv`和lock、显式HERMES_PYTHON，不指生产用户。
- 自主轮次依`autonomous-run`：全新`fork_turns=none`独立Verification先核冻结要求／指定机制／正式接线／证据，通过后Validation从实际入口验用户输入到输出；两者不充当大型套件复跑器，必要反证仍取真实证据。
- 本地CD包括范围内review、阶段提交和必要构建；仅授权部署时才部署并验结果。push不代表构建、部署或验收。
- **每次commit自动push**：主仓和独立UI推当前upstream，无upstream的功能分支推origin同名；UI本地main对应origin/secretary。新工作区先保留已有hook，再安装`.githooks/post-commit`到实际hooks目录并赋执行权，默认common hooks覆盖worktree。失败保留本地提交并处理，不强推、不自动fetch／merge／覆盖他人，不启CI。

## 分区架构与接线参考入口

按修改区域查对应`AGENTS.md`（仅参考，不导入新规则）：`agent/`、`hermes_cli/`、`gateway/`、`tools/`、`plugins/`、`tui_gateway/`、`web/`、`apps/desktop/`及其`src/`、`skills/`、`cron/`、`tests/`、`pm/`、`hermes_platform/`。根`run_agent.py`归agent，`cli.py`归hermes_cli，toolsets／model_tools归tools，optional-skills／Curator归skills。

## Subagent 与工作区

- 主会话抓目标、全篇覆盖、编排、亲审、集成、微小明确修补和最终判定；边界清楚的独立实现／研究可委派，过小或需连续决策则自己做，无独立全局工作就等整包交回。
- 每次派遣／接续写全目标、依据、输入、白名单、接口、依赖、完成条件和验证；Development精确到白板卡片ID、07章节／当时行范围，并列旧规格保留条款、跨章及上下游。主会话完整读并防遗漏。
- 默认显式`gpt-6.1-sol`／`high`，用户指定优先。子Agent不再派生；并行范围不交叉或隔离，非必要不用worktree，必要时平铺父目录。
- **每次任务文本重申禁止流水账**：整包完成一次交回；只有真阻塞或必须主会话决定的权限／接口／产品取舍才中途发消息。步骤、命令、小发现、可自行处理问题写证据，不单独报“阶段完成”；主会话不催碎片或按文件数盯进度。
- 主会话核返回diff及正式接线，不以复跑测试代review。用户要求大型“自主执行／一轮自主实现”时用autonomous-run套件，其冻结、Snapshot Index、阅读契约、两门禁和交付判定为准；默认范围内本地阶段提交权，快照写清验证及剩余。

## 依赖与本地配置

- 官方PM管理项目`.venv`，用`pm.build_env`、既有lock及dev／test groups；不裸pip／uv改PM环境，不重解析锁或改全局Python。其它安装优先Homebrew、mise、nvm、uv，禁sudo pip。
- 依赖遵循pyproject／uv.lock边界，Git依赖和Actions固定commit；变更用`hermes pm lock`并提交锁。运行数据放ignored目录，不入Git。
- 用户配置本体在`~/dotfiles`，经`sync-links.sh`链接，不复制个人配置入公开仓库。
- 个人MCP源码／安装在运行主机`~/tools/`（npm安装例外）；个人独立小工具统一`~/scripts/`，不设旧拼写别名，不依赖Hermes／Provider／HERMES_HOME／cwd，只收调用方内容与Metadata、复用官方NM配置、不自行读Hermes状态。不借此迁移无关工具。
- Memory创建preview／apply必须显式非空`--space`，Default也传`--space default`；缺失、空值、纯空白拒绝，不推断目标。
- 已验工具原件只读／可执行，禁止自行改删、替换、解锁／提权绕过；扩展先读源码，在`~/scripts/custom/`另建并标未验收。明确授权维护原件时可更新，验证后恢复保护；不扩大为账号／sudo隔离工程。
