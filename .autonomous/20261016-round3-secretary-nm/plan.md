# Round 3 Develop 编排计划：多 Chat 编码 → PR 集成 → 本地运行与修复

> 编制日期：2026-10-16。状态：**计划已编制，产品代码尚未按本计划实施，所有产品运行／测试均未执行。**
>
> 本轮先由用户委派多个独立网页 Chat 对话，分别通过 GitHub 连接器建立分支、准备一次或多次多文件提交、创建 PR；由原规划主会话审查和合并 PR。云端完成可以完成的源码修改、测试用例编写和静态接线审查后，再回到本地准备环境、实际运行、执行测试并修复编码阶段未识别的问题。不是每个子对话先自测，也不是把本地修复推给独立 Verification。
>
> 本文是静态执行契约，不是第二份动态看板。任务认领、分支实际 SHA、PR 编号、文件所有权转移、运行结果、阻塞和当前阶段只记根 `CLAUDE.md`；PR 保存各自变更与交回事实。本文不维护另一套完成勾选表。

## 0. 授权、阶段及停止位置

### 0.1 本次工作的边界

本次仅完成 planning 并提交仓库，不派遣实现、不运行产品、不创建真实 NM 数据、不部署。原 ask-and-align 与文档基线已经完成，不重新讨论已经冻结的产品取舍。后续执行遵循本轮 `snapshot-index.md`，其中 R3-012～R3-015记录本次用户对计划、测试后置、独立 Chat／PR 和本地运行的明确要求。它们覆盖先前会话“文档冻结后暂停”的阶段限制，不改变白板、07 和个人 PHASE3 的产品边界。

完整 Develop 被分成两个连续而不同的部分：

```text
D0 规划／分支准备
  ↓
D1 CLOUD_CODE：独立 Chat 编码、编写／调整测试源码、不执行
  ↓
D2 CLOUD_INTEGRATE：主会话逐 PR 静态审查、合并、补齐源码接线
  ↓
CODE_INTEGRATED_UNRUN：双仓固定提交；代码已集成、尚未运行
  ↓   用户将这对提交带回本地
D3 LOCAL_RUN：隔离环境、首次实际运行、定向开发测试
  ↔
D4 LOCAL_REPAIR：按失败归因分派修复，仅复测失败与实际受影响路径
  ↓
DEVELOP_READY_FOR_VERIFICATION：提交、接线、开发证据与缺口已交齐
  ║
  ║ 本计划在此停止，不启动独立 Verification／Validation
```

`CODE_INTEGRATED_UNRUN` 不是 Develop 完成、不是可用性验收、不是发布许可。独立 Verification 的规格符合性审查、其后的 Validation 产品验收仍保留独立职责；不能把 D3／D4改名成它们，也不能跳过 D3／D4直接声称完成。

### 0.2 云端阶段允许和不允许的动作

允许：读取冻结规格及当前分支源码，分析调用者，修改实现、测试源码与必要说明，创建 Git tree／commit／branch／PR，人工检查差异、参数、引用、返回值、权限和锁顺序。可以编写测试，但不得报告它已通过。

后置到本地：安装／构建 Hermes 环境、导入产品模块验证、compile/typecheck/lint、pytest/unittest、启动 CLI／Gateway／Dashboard、浏览器联调、真实模型调用和端到端运行。即使某个网页环境额外提供执行工具，也不据此打乱用户指定的顺序。不为云端 PR 临时建立 CI，不以别的运行平台替代用户要求的本地阶段。

GitHub 确认提交或合并，只证明仓库内容已写入。静态阅读发现的错误立即修；没有运行证据的行为统一标 `NOT_RUN`，不能写 PASS、回归通过、验收完成或已验证线程安全。测试缺失不阻止“编码交回”，但必须明确由谁补写、由哪个本地组执行；已知未完成的产品逻辑不能因测试后置而隐藏。

### 0.3 仍然保留的限制

- 两条工作线：公开 Secretary 核心改版；独立 `hermes-nmem-provider` 个人接入。禁止在公开核心加入 NM 依赖、凭据、个人 Persona 或 NM 治理规则。
- Web UI、Orb／Memo 面板、人类 Notebook 卡片、Settings 展示及其 Web 读 DTO 改版全部后置；不修改 `hermes-secretary-web`、`web/`、`ui-tui/` 或 `apps/desktop/` 的界面。原生后台 RPC／CLI 的必要运行接线不是界面重做。
- 不做旧数据／旧配置自动迁移；本地使用新隔离库。旧 tool_call 历史不删除、不重放；旧名不能继续成为可执行 alias。
- Noting 仍允许不同压缩区间的任务重叠，C 不要求继承尚未提交的 B；不增加串行、合并、重跑或语义结果超集条件。
- provenance 小脚本只做基本静态／调用检查，不设置独立严格验收，不重测官方 CLI 通用能力。不得以本计划授权真实 NM Memory／Thread／Space 写入、修改治理或正式云端部署。
- 不修改已冻结检查类别、阈值、阻断等级、上游同步规则或全局 Agent 设置。测试执行后置是本轮顺序调整，不是取消检查。

## 1. 已核对的版本与阅读契约

### 1.1 版本锚点

| 对象 | 冻结／调查版本 | 用途 |
|---|---|---|
| Secretary 产品实现起点 | `a51fd99abc783f245ab855526a10862f2c89656a` | 改版前源码事实，不能拿旧测试当本轮通过 |
| Secretary 需求文档冻结 | `d19018a7ba3e38ae01f76aa57821b55cbc15ff58` | 白板、07、旧规格保留段和核心规则 |
| Secretary 本次读到的 main | `dec457e2393dc3e7401449b19b068bf7c65e5a07` | 在冻结提交上记录双仓哈希；本计划从此树编制 |
| Provider 实现起点 | `f9733fcb31a0e6f468eabe6419cb76444fe16b30` | 既有个人 Provider／helper／测试源码 |
| Provider 文档冻结及本次 main | `97078118287bcd41ba8b02aa5a3a108c5026f7af` | 现行 PHASE3 §1–7与根文档 |

本计划的提交不会改写 `baseline.txt` 中历史冻结哈希。实际编码从包含本计划的集成分支最新已接收提交开始，不能每一波都退回上述旧 SHA。发包时记录精确 `PLAN_SHA / SPEC_SHA / START_SHA`；任务依赖以已合并 PR 的真实 SHA 为准。

已从源码确认的拆分理由：`NotebookStore` 仍有旧 edit／schedule 方法；Notebook pointer 重选仍调用 `reconcile_payload`，fork 仍继承 Schedule runtime；`noting_tools.py` 仍是旧三工具／十类型；`agent/secretary_prompt.py` 的 Cron 说明仍受 Notebook gate 控制；个人 `personal_provider.py` 已有 scope、Bundle、prefetch、Thread 收据骨架，而 `personal_cli.py` 仍需退出旧直接 HTTP 正文写入路线。**这些是修改起点，不是新行为已通过的证据。**

### 1.2 每个执行对话共同先读

1. 自己仓库根 `AGENTS.md`、根 `CLAUDE.md` 的当前第三轮区域、根 `README.md` 的相关入口。
2. 本轮 `snapshot-index.md`，尤其 R3-002、005、006、008～010、012～015。
3. 本文 §0～5、自己任务卡及其依赖的接口交回；不默认继承主会话聊天上下文。
4. Secretary 任务共读07 §0～3（源码行1～115）和§7（1180～1240附近的完整章节，以标题界定）；按下表再精读各自范围。主会话已负责全篇阅读与分配，子对话不重复阅读所有旧材料。

以下行范围以 `dec457e...` 的原始文件行号为定位窗口，包含必要上下文；章节／白板卡片 ID 同时是语义定位。若发包时规格 blob 与此基线不同，主会话重新核对该任务的范围，不能机械沿用旧行号。行窗口交叠表示需要共读，不表示可以共同写文件。

| 阅读包 | 精确依据与定位窗口 | 继承的旧条款，仅继承未被07覆盖部分 |
|---|---|---|
| R-NB | 白板 A2/A4/A5、C1～C4/C6～C9、I1/I2、U1/U2、T2～T5、L0/L2/L3/L7、E1/E2；C1的七类型数据还在HTML末尾`types`对象，不可只读空容器。07 §4，行116～907；§7，1180～1240；§8.10～8.13，1320～1424 | 02 §2.6～2.7、§3.1～3.4：Anchor、完整Snapshot、pointer、来源与分支；04 §4.1、§4.7只继承合法快照与审计分离，不继承旧类型／compact_parent |
| R-HIST | 白板K1的History详情、P6；07 §5，行900～1058；§7，1180～1240；§8.4/8.8/§9.1，1250～1320及1440～1480 | 02 §1.1～1.6、§2.1～2.2、§2.4/2.6/2.7；04 §2.1～2.6、§3.1～3.2中的资格、可见性、规范身份；旧session_history工具面不继承 |
| R-SCHED | 白板A3/A7、K1～K5、N5；07 §6～7，行1058～1240；§8.6/8.9/8.14，1265～1320及1425～1440 | 02 §3.9～3.12与04 §5.3中registry／claim／lease／carrier／实际请求ACK可靠性；不继承Notebook ownership、类型限制和pointer联动 |
| R-RUNTIME | 白板N0～N6、P1～P5、D6～D8；07 §3，行87～115；§4.5，865～907；§8.1～8.2，1235～1270；§8.11～8.13，1330～1424；§11/11.1，1500～文件末尾 | 02 §4中Force原生余量公式、§5.1～5.5/5.7～5.11的冻结、资源、权限与提交；04 §4.4～4.7的持久child、全程prefix parity、D01、五Turn及overflow；旧两profile／child压缩职责退出 |
| R-PROMPT | 白板C7/C8/C9、L1/L4/L6/L9、F1/F2、N1/N2/N5/N6、P6；07 §6.3/6.4、§7～8，行1140～1440 | 01 §1/§4/§7中Hermes-first与公共边界；04 §3.1～3.5的Main资格及原生提示／Schema同步边界；不继承上一轮禁止整体重写Prompt的范围限制 |
| R-PERSONAL | Provider `nowledge-mem-hermes/docs/PHASE3.md`现行§1～7，行1～183，遇“历史方案”即停止；分别精读§2～3、§4.1、§5～6；公共07只读§0/§5/§8.10以消费身份和提案契约 | 不继承PHASE3历史附录的替换session_search、旧personal_cli完整写入协议、旧分类；不把旧TEST_REPORT当当前运行证据 |

白板完整语义集中于HTML的正文卡片和`types`／`scenarios`数据。网页的折叠、隐藏或没有展开不意味着没有要求。研究参考链接是设计背景，执行者无需重新做外部文献研究。对旧文档的读取始终服从顶部及逐章“第三轮适用性”，不得重新复活旧Memo或排期规则。

本环境未取得独立 `autonomous-run / writing-plans` 套件正文，因此不宣称逐条核过一份不可见套件。本文落实仓库明示的索引、冻结、覆盖、工作包、主会话review与独立门禁分工。后续本地可读取已安装套件的适用流程；不得借其默认顺序覆盖用户本次明确的先编码后测试要求。

## 2. GitHub-only 协作协议

### 2.1 分支和写权限

主会话在首次发包前创建两个集成分支，名称均为 `round3/develop`：Secretary 从包含本计划的 main 提交建立；Provider 从上述冻结提交或已核对的仅文档后继建立。它们是**待运行的开发集成区**，不代表发布。此次规划提交不预先创建实现分支或PR。

任务分支统一为 `round3/<任务小写ID>-<主题>`，例如 `round3/c1-notebook`、`round3/p2-provenance-helper`；PR base 为自己仓库的 `round3/develop`。一个任务一个分支，允许多次多文件提交和同一PR追加修补。执行者不得直接推 main、推集成分支、合并自己的PR或修改另一个任务分支。

主会话是唯一集成分支写者和PR合并者。Provider的PR留在Provider仓库，绝不跨仓复制个人代码到公共集成树。没有用户新的发布安排前，不把未运行的集成分支并入main，也不自动执行部署。

每个任务分支从派发时的最新集成提交建立。第一波可共用起点；后继任务从已包含依赖PR的起点建立。可先做只读调查／编写设计，但没有满足“可开始修改”依赖时不提前修改共享文件。默认不堆叠PR，不把下游PR base指向另一个尚未合并的功能分支。

### 2.2 用连接器准备一次多文件更新

按当前连接器提供的真实工具执行；工具名称或参数不确定时先discovery，不能把以下说明冒充已执行：

1. 读取目标分支当前commit、tree和需要改的文件完整内容；记录每个旧blob SHA。被工具截断的内容必须续读，不能拿半份文件覆盖整份。
2. `create_branch` 从确定的 `START_SHA` 建任务分支。已存在同名分支时先读head，确认属于本任务，不能覆盖他人的同名分支。
3. 以任务分支当前tree作为 `create_tree.base_tree_sha`，只提交白名单中的新增／修改／删除项；文本使用完整新内容。**禁止省略base tree而无意创建只有少数文件的仓库树。** 删除必须使用API明确的删除语义，不用空文件冒充删除。
4. `create_commit` 的parent必须是刚读取的任务分支head；多文件关联更新尽量同commit提交。
5. `update_ref` 使用 `force:false` 和 `expected_sha=刚读取的head`。lease失败后重读，不强推、不把旧tree挂在新parent上掩盖丢失更新。
6. 写后读取新commit及changed paths，核对只有预期文件；创建或更新PR。连接器失败时保留已创建commit SHA，查询实际ref再决定是否重试，避免重复commit／PR。

连接器写入不是本地git commit，不会经过本地post-commit hook；不声称该hook已经运行。它本身已是远端内容同步。本地阶段仍按AGENTS安装并保护实际hooks。

### 2.3 禁止意外云端执行

核心仓库规则为Actions关闭。Provider基线CLAUDE记录Actions当时仍enabled，不能推定两仓相同。**第一次代码push／PR前由主会话核对两仓实际触发设置**，确保用户要求的云端不运行测试成立。`[skip ci]`写入提交信息只是补充，不是对所有事件／外部机器人都有效的保证。

若Provider仍会自动运行而连接器不能修改设置，由仓库操作员关闭运行后再更新ref／创建PR；不通过改workflow、放宽检查或造绿色状态绕过。不能确认时，该仓任务可以读源码并准备未挂到分支的tree／commit，但暂不触发push／PR；不阻塞公共仓的独立编码，也不擅自执行真实服务。此为遵守用户运行顺序的操作边界，不是新增产品验收门禁。

### 2.4 PR交回格式

PR标题：`[R3][C1][CODE-ONLY] Notebook data and Snapshot`，其它任务替换ID和主题。PR正文必须包含：

```text
Task / Repo / Branch / Base SHA / Head SHA / Plan SHA / Spec SHA
Depends on: 已合并PR及SHA；不存在依赖写none
Changed paths: 完整文件清单；所有权扩大须列批准记录
Contract coverage: 本任务条款 → 实现符号／路径 → 测试源码位置
Exported interfaces: 精确函数签名、参数、返回形状、异常和锁／事务责任
Connection status: 已接入口；刻意留给C9的入口及所需调用方式
Static review: 实际检查过什么；发现并修了什么；未解决什么
Tests: NOT_RUN — user-directed deferral to local Develop
Planned execution: 本地测试组、实际文件／node ids、所需fixture和环境
Risks / decisions: 真实限制；必要自主收敛与原因；不写成用户已亲选
Remote result: commit SHA、PR URL；没有成功写入就明确失败
```

正文中的“验收场景”是待执行，不填想象中的输出。不附整份规格、源码或长日志；上游调用者只消费精确接口和对应代码位置。不把问题交回为“主对话自己查一下”。

## 3. 所有权、并行图和接力策略

### 3.1 拆分原则

一个现有文件同一时间只有一个写者。独立分支只能隔离Git写入，不能消除相同文件语义冲突；因此不采用“大家都能改，最后合并”策略。公共facade／dispatch／生命周期入口集中给C9，避免每个模块各自改一遍。

下表的测试文件是**拟新增的源码路径**，不是已存在／已执行的用例。旧测试按本域提出保留／改写／退出清单，C10统一落实跨任务fixture与遗留用例调整；不得用skip/xfail掩盖新行为失败。新增helper只限自己的模块职责，并在PR列出，不能复制另一个owner的实现或新建平行系统。

| 任务 | 可开始修改的依赖 | 写所有权／工作内容 | 预计PR交回后由谁消费 |
|---|---|---|---|
| C1 Notebook模型与Snapshot | D0 | notebook_model/items/store/render、hermes_state_secretary_notebook；新test_r3_notebook.py | C5、C8、C9 |
| C2 Conversation History | D0 | session_history_tool、hermes_state_search及窄查询helper；新test_r3_history.py | C5、C9、P3只读消费 |
| C3 Scheduler控制面 | D0 | schedules、notebook_schedule解析迁出、hermes_state_secretary_schedule、新scheduler工具模块；新test_r3_scheduler.py | C6、C9 |
| C4 配置及Main提示 | D0 | noting_policy/scope、config defaults/validation、prompt_builder/system_prompt/secretary_prompt、CLI Secretary命令；新test_r3_config_prompt.py | C5、C7、C8、C9 |
| P1 Provider资格／Bundle／Recall | D0 | personal_provider/personal_scope/personal_client及必要client复用；新test_r3_provider.py | P3 |
| P2 provenance窄脚本 | D0 | personal_cli、独立窄Metadata helper、nm-cli skill的脚本使用说明；不改P1文件 | P3只接安装／说明 |
| C5 Noting child／四工具 | C1合并；可按冻结Schema消费C2，合并前需C2/C4 | noting_child、noting_tools；新test_r3_child.py | C7、C9 |
| C6 Scheduler投递 | C3合并，取得schedule文件交接；合并前需C4 | reminders、reminder_request、cli_reminders；必要schedule接纳函数由C3交接；新test_r3_delivery.py | C9 |
| C7 父联合触发 | C4合并；合并前需C5 | noting_runtime/timers/capability/admission_receipt/compact、hermes_state_secretary_noting；新test_r3_joint.py | C9 |
| C8 pointer与Framework | C1/C4合并 | framework_messages；必要Snapshot事务扩展由C1交接；新test_r3_framework.py | C9 |
| P3 Thread归档与个人接线 | P1合并并交接文件；合并前需P2 | personal_provider/scope的归档部分、现有收据、install_personal与插件README；新test_r3_thread.py | 本地个人组 |
| C9 公共正式接线 | C1～C8都合并 | agent/tool_executor/inline_tool_executors、model_tools/toolsets/registry、noting_surface、host生命周期与压缩入口、结果预算反馈；新test_r3_wiring.py | C10／本地组 |
| C10 云端源码收口 | C9与P3合并 | 主会话负责；只修跨PR接缝、遗留引用和测试fixture，更新根文档 | D3／D4 |

源码完整路径以§6任务卡为准。C1→C8、C3→C6、P1→P3是**顺序交接**：前任务停止写该文件，主会话在CLAUDE登记接收head及新owner后才能转交。前任务如需追加修复，先交还或让当前owner实施，不能同时推两个版本。

C9白名单以任务卡列明的现有接缝为主；发现未列文件，只提交“调用者路径＋必要修改＋影响”，由主会话明确分配，不自动放行整个agent／gateway目录。根三份文档、snapshot-index与plan只由主会话修改；子对话通过PR交回更新建议。

### 3.2 ASAP派遣，不设整波屏障

首批可发六个独立对话：**C1、C2、C3、C4、P1、P2**。它们不以测试、环境或其它首批任务完成为前提。

```text
C1 ─────→ C5 ─────→ C7 ─┐
 │          ↑            │
 └──────→ C8             │
C2 ─────────┴────────────┤
C3 ─────→ C6             ├→ C9 → C10 → CODE_INTEGRATED_UNRUN
C4 ────→ C5/C7/C8/C6 ───┘                 ↑
P1 ─────→ P3 ─────────────────────────────┤
P2 ─────→ P3最终接收 ──────────────────────┘
```

一条依赖满足就启动对应后继，不等整波齐。C2较重不应阻塞C3→C6或P1→P3；个人授权／连接配置问题不应阻塞公共代码。主会话可在等待完整PR时准备下一包接口／合并前置工作，不反复盯文件增长或要求半成品汇报。

C9可以提前只读记录公共接缝，但正式修改在上游收口后集中进行，避免从尚在变化的签名制造多轮返工。C10是主会话源码集成审查，不派“重复检查所有模块”的第二组开发审查者。只有明确跨模块疑难点才建立一个窄问题讨论，直接提供已有证据，不重新探索全库。

### 3.3 先交接口，后交完整实现的可选拆法

C1/C2/C3较大时，同一PR允许先提交完整可阅读的接口／数据模型，后提交实现。只有主会话明确标为接口稳定，依赖者才按其head准备代码；默认仍等它合并再建下游分支。接口未实现时不得放入生产no-op、虚假成功或catch-all静默降级来让下游看似完成。

真正需要进一步并行时，由主会话把该任务拆成不交叉的helper与facade两个写包并更新CLAUDE白名单；原任务不能自行再派生。网页Chat不一定有子Agent工具，本计划的执行单元就是用户开启的独立对话，不要求嵌套派遣。可选择模型时沿仓库默认`gpt-6.1-sol/high`；用户实际指定的网页模型优先，不伪造模型切换。

## 4. 跨PR接口合同：减少互相猜测

以下描述必须交接的内部数据和事务职责，不强制新建一套抽象层。除公开07已冻结的工具名／Schema外，内部函数名由唯一owner确定，在PR中给出精确签名；后继只使用已接收版本，不各自发明同名实现。

### I-N：Notebook与提交

- C1输出同一份标准entry：稳定`entry_id`、不可变`version_id`、类型、fields、status、relations、两种来源和runtime时间；payload固定四数组`work/situations/discussion/candidates`。
- 工作视图属于task，不因父pointer变化被重载；base_snapshot_id与coverage在启动时绑定。Main show只读有效已提交Snapshot；Noting show必须读绑定task当前working view。
- create/update/archive失败无工作态变化；no-op不新建version、不更新时间；数组整值替换、fields按键合并、来源和引用验证在同一成功操作内完成。
- C1向C5/C8提供**同一提交事务产生**的结果：新snapshot_id、当前effective_snapshot_id、本提交是否切换pointer、提交时间。不能由C8在提交后另查一次再推测pointer_changed；保留现有facade兼容返回时，通过同一内部结果转换，不产生第二份真值。
- C8需要的“pointer匹配＋durable append＋live发布顺序”接口在现有DB事务／runtime锁内完成；不得让调用方随意嵌套第二事务或锁序倒置。

### I-S：Schedule与接纳

- C3提供正式Table CRUD、原生时间解析、当前定义版本／撤销状态、只读24小时覆盖判定，以及供claim/materialize/instant commit使用的conn级当前定义校验。
- C6消费这些接口，不能把prepare时的旧content、generation、delivery_mode当提交时真值。失败与未知分别返回；ACK以原生实际携带／响应证据确认。
- 24小时helper输入owner、now、排除的本次occurrence集合；输出“存在／不存在／无法判断”。只读、不消费、不推进Table，不从过滤后的list计算。
- pending保留原instant来源标识，供busy→deferred实际materialize时重算notice；批量原instant只附一次。纯deferred不触发该notice入口。

### I-H：History与真实身份

- C2提供新的`conversation_history` Schema/handler和只读规范路径读取；身份由host注入，模型Ref／cross_conversation不是授权。
- 原生候选查询返回有界物理候选及真实diagnostics、稳定推进状态；不得以`search_messages(offset=...)`的空数组推断底层耗尽。
- C9负责真实同步／并发dispatch绑定，以及工具结果spill／批次裁剪中的Noting专属可行动提示。C2不能通过提高预算或新增read_file替代此接线。
- P3读取现有跨压缩History Foreground和message identity，不monkey-patch公开History，不用NM Thread回写公共事实源。

### I-R：child／联合触发／通知

- C5沿现有构造／spawn入口接受冻结prefix、同一admission、owner、base视图与触发类型；不会再请求父compaction。
- C7拥有区间admission和四种入口的决策，C9拥有把它挂进所有正式host调用路径的修改。不能同时保留旧preflight路径和新入口而发两次任务。
- C5结束只产生end_requested或forced/overflow兜底事实，原生Turn返回后提交；C8只为确实生效且派发时仍生效的结果构造通知。
- C4提供共用Proposal与配置读取，C8消费同一常量，不复制一份字面文本；子任务Prompt由C5独占，Main Prompt由C4独占。
- C9对每一个真实入口指出“谁拿锁、谁冻结、谁admit、谁spawn、谁compact、谁提交、谁append、谁释放”。这张调用链是本地执行的定位依据，不是运行通过声明。

## 5. 通用编码交回／主会话审查规程

### 5.1 编码完成判据（每张任务卡均继承）

本任务授权的实现及测试源码已提交；所有修改在白名单内；没有把必要实现替换为TODO／固定成功／只存在于测试中的假实现；上下游签名、返回值、异常、锁／事务边界已交回；旧用例处置和待运行场景可定位；PR明确`NOT_RUN`。代码可静态追踪，不要求在云端证明导入、构建或产品执行成功。

每张任务卡中的“后置测试”只要求给出或调整测试源码及明确预期。执行统一进入§8。测试应观察对外行为和失败后的状态，不读取源码字符串证明改动，不复制生产算法当oracle；clock/模型响应/本地HTTP只作为可控输入边界，真实数据层、handler与正式dispatch尽量保留。

### 5.2 主会话接收一个PR

1. 读取PR元数据、所有changed filenames、完整patch；patch省略或文件过大时读取对应head的完整必要区间。核对head SHA和依赖。
2. 对照该任务条款及白名单，亲自审查调用者、模式默认、owner、异常路径、事务和数据修改；核对提供的测试源码是否真的对应契约。**不运行测试，不再让另一个对话做同一套审查。**
3. 静态可确认缺陷以具体文件／符号／反例／预期写到原PR，让原owner一次性修；不把一个问题同时发给两人。不对未实测的行为给确定失败或通过判断。
4. 对“合并依赖未满足”“接口未确定”“关键产品逻辑未实现”“出现越界写入／删除”暂不合并；纯粹`NOT_RUN`不是云端拒收理由。
5. 接受时写“源码审查接收；测试按用户要求后置”，以`expected_head_sha`合并至集成分支；优先普通merge保留任务commit证据。不能把单个PR的分支tree直接覆盖不断前进的集成tree。
6. 读取实际merge结果、新的集成head和变更范围，更新CLAUDE的任务状态、接口与文件交接；下一个任务只消费该实际版本。读写竞争导致head改变时仅复审新diff及受影响连接，不重新审整轮。

同一GitHub账户可能不能APPROVE自己创建的PR；用COMMENT记录人工审查事实并按权限合并，不伪造独立审批人。`mergeable`、没有冲突、Actions不运行都不是正确性证明。

### 5.3 冲突处理

目标分支只前进了不相交文件时，不为追平主干要求任务反复rebase；由GitHub正常合并。出现实际冲突，主会话指定一个owner读取base/head/current三份相关文件，产出保留双方必要变化的合并；从当前集成head创建窄修复PR，或向任务分支追加经过审查的merge commit。禁止force push、整文件选theirs／ours、把旧版本全文件覆写当前版本。连接器无法安全表达合并时报告具体冲突，不冒称已解决。

## 6. 可直接实施的任务卡

所有C任务仓库为`EdgarZhong/hermes-secretary`，所有P任务为`EdgarZhong/hermes-nmem-provider`。每卡在通用协议之外规定专属动作。执行对话不需要读取其它任务的全部报告，只需要依赖PR的接口交回和实际接收代码。

### C1 — Notebook数据、版本、工作态和Snapshot

**分支：** `round3/c1-notebook`。**依据：** R-NB，另读R-RUNTIME的原子提交部分、07§6.2排期解耦与§11.1并发边界。

**白名单：** `secretary/notebook_model.py`、`secretary/notebook_items.py`、`secretary/notebook_store.py`、`secretary/notebook_render.py`、`hermes_state_secretary_notebook.py`；可在`secretary/`新增只服务Notebook校验／表示的小helper；新增`tests/secretary/test_r3_notebook.py`。不改noting_tools、schedules、framework或公共facade。

**按顺序实现：**

1. 将旧十类型／四旧分区替换为07§4的新七类型＋candidate及四数组。按类型校验必要fields、合法status、可选字段清空和来源至少一种；拒绝未知字段、重复ID／标签、错误关系目标、candidate引用candidate。不要用旧单向状态图禁止有证据的修正／重开。
2. 复用item lineage表示稳定entry_id，将不可变row身份作为version_id。Snapshot引用具体版本；一次update不改变稳定身份，不能把旧版本来源依据复用给无关新内容。
3. 实现create、update(changes)、archive(reason)。先合并再整体校验再创建版本；失败不改变working view；no-op不续期。反向candidate_refs由当前引用派生；archive有入向引用时返回完整referrers，由模型先修引用。
4. 分离evidence_time／last_progress_time／last_discussion_time／首次gap创建时间与last_processed_at。成功带具体processing_note的操作才记处理时间；重写或读取不重置实质证据年龄，不新增每条定时器。7天/72小时是模型处置规则，不在存储层自动删除。
5. 保留任务私有完整视图、已提交视图及commit时来源重验。调整`validate_snapshot_state_conn`、item hydrate、fork继承，使继承依据绑定真实entry/version。新引用仅当前合法父路径；测试数据从新库建立，不写迁移。
6. 从pointer重选、Snapshot commit、fork继承中去掉`reconcile_payload`、`inherit_runtime_conn`和Memo消费／阻止off副作用。允许新trigger类型、唯一runtime profile及三种有效termination；保留合法晚结果审计但不回退pointer。
7. 在commit事务内产出I-N结果供C5/C8；render返回完整新payload，不加字符硬限制。删除本域Memo方法时记录仍引用它的调用者，交C9/C10收口；不为旧工具提供执行alias。

**后置测试源码／预期：** 全类型create；字段按键合并和数组替换；清空必需字段失败无写；no-op时间/version不变；候选双来源和标签映射；悬空引用拒绝；源条目新version不被旧批准自动结算；并发任务工作视图独立；晚Anchor不回退；rewind／fork来源合法性；pointer/fork不改变Schedule；严格大于阈值不影响写入。

**必须交回：** 新entry/payload形状、Store的准确方法签名、提交事务结果、C8可用conn接口；列出旧模型用例哪些改写及理由。交回状态为`CODE_READY_NOT_RUN`。

### C2 — Conversation History与原生稳定候选流

**分支：** `round3/c2-history`。**依据：** R-HIST；07§3/§7/§9.1；原生`session_search`当前公开契约只读保留。

**白名单：** `tools/session_history_tool.py`、`hermes_state_search.py`；允许新增`hermes_state_search_candidates.py`和窄History只读helper；新增`tests/secretary/test_r3_history.py`。不改原生session_search公开Schema/handler/toolsets，不改message ownership或另造索引；公共dispatch、spill提示交C9。

**按顺序实现：**

1. 暴露`conversation_history`的完整Schema，先选择search/anchored-read/unanchored-read再应用该模式默认值。锚点read不隐式带limit；参数冲突错误明确。保留规范双字段message_identity，不继续执行旧message_id。
2. 从真实host资格和owner DB确定当前域；Main显式cross_conversation仅授权同Profile真实用户Conversation；Noting只能父域；无跨域空查询browse。范围失败不泄露其它域对象存在性。
3. 原生检索层提供窄内部候选adapter：一次调用固定query与实际FTS／降级路线，FTS与未索引gap分别推进并去重；正确传递错误／降级／耗尽／预算诊断。候选预算`min(10000,max(1000,20*limit))`、批200；不循环滥用当前offset并在空页偷偷切OR路线。
4. 只对候选展开可能的Conversation membership，再经统一合法History/model_visibility入口核实。支持同一物理源在多个fork中的规范身份；合法branch引用的inactive源不能提前过滤。按消息timestamp筛选，不能拿Session started_at代替。
5. 构造约800字符字面命中窗口并合并重叠，区分full/match/fallback、truncated、partial。结果limit或候选预算阻止穷尽时诚实partial；索引全不可用或语法错误不能当空命中。
6. Read返回同一有效逻辑路径原文及默认前2后3，0/0锚点必达；排除失效路径／Prelude／不可见注入；保留多模态结构。用只读路径，不修binding、不遍历全Profile全文。
7. 交C9旧名拒绝代码及Noting超大结果指引所需信息；不新增cursor／scroll／chunk工具、不放宽budget、不让Noting转用文件工具。

**后置测试源码／预期：** 三模式互斥；CJK/phrase/AND/OR/NOT/prefix；消息时间闭区间；辅助噪声挤占首批后仍找得到；gap不重复；真实故障非成功空；多fork相同UID正确Ref；跨profile/aux拒绝；只读不建Conversation；excerpt字面来自原文；锚点不丢；原生session_search原行为保留。

**交回：** handler入口、候选诊断形状、membership读取和错误映射、正式调用者清单。不要另建History事实库。

### C3 — 独立Scheduler Table与Main工具

**分支：** `round3/c3-scheduler`。**依据：** R-SCHED，07§6全章、§7.1/7.2；C1提供的是独立Notebook，不可依赖其pointer。

**白名单：** `secretary/schedules.py`、`secretary/notebook_schedule.py`、`hermes_state_secretary_schedule.py`；拟新增`tools/scheduler_tool.py`及必要窄Schedule helper；新增`tests/secretary/test_r3_scheduler.py`。不改reminder_request/reminders、公共registry或Prompt。

**按顺序实现：**

1. 把registry从Notebook版本派生改为直接保存Schedule定义；继续以Profile/Conversation为owner。复用原生解析器，把`parse_schedule_expression`移回Scheduler职责内，移除Notebook状态反向控制；不新建Cron算法。
2. 完整实现list/create/update/pause/resume/delete和07返回值。list默认完整Table，可筛但不影响24小时判定；update只解析实际改变的schedule，name/content/delivery_mode省略不动，no-op诚实返回。
3. 与claim相同事务比较定义／generation；pause/delete撤销未接纳pending但保留已持久化carrier和ACK证据，返回真实delivery_in_flight；改期取消旧未接纳发生，不无限补历史周期。完成一次性不允许resume重投。
4. 保留claim/lease/dedup/pending核心，提供C6在materialize和ActiveReminderAdmission.commit使用的conn级重验接口。旧worker不能把已删除或更新的排期复活；ACK不能把暂停／删除项激活。
5. 实现I-S只读24小时helper：完整Table、包含端点、排除当前发生但计算同周期下一次、逾期其它合格instant可计、paused/deleted/completed/deferred不计、unknown不当无。工具所有action成功/失败可读状态均正确附notice。
6. 独立Scheduler开关消费C4契约；停止新投递但保留Table，开启按原生语义恢复；new/reset/fork空Table，同Conversation continuation保留。不要把Noting local/global gate传递成排期权限。

**后置测试源码／预期：** 原生`30m`周期 vs `in 30m`一次；时区；六动作模式错误；单次消费；update/pause/delete与claim交叉；无Notebook时可登记；24小时边界/筛选list/失败unknown；fork不复制。

**交回：** CRUD和conn重验准确签名、schema、24小时helper；将需要C6追加的schedule文件函数列为顺序所有权交接。

### C4 — 配置、Main Prompt与原生命令

**分支：** `round3/c4-main-config-prompt`。**依据：** R-PROMPT、R-SCHED配置段；07§8英文块逐字作为定案文本，而非再次创作文案。

**白名单：** `secretary/noting_policy.py`、`secretary/noting_scope.py`、`hermes_cli/config_defaults.py`、`hermes_cli/config_validation.py`、`agent/prompt_builder.py`、`agent/system_prompt.py`、`agent/secretary_prompt.py`、`hermes_cli/cli_secretary_commands.py`；必要配置说明仅限本任务相关位置；新增`tests/secretary/test_r3_config_prompt.py`。`noting_surface.py`与全局tool registration交C9，Noting Task Prompt交C5，Framework生成交C8。

**按顺序实现：**

1. 引入独立`scheduler.enabled`；Noting采用`idle.enabled/delay_seconds/threshold_tokens`及`persistence_proposal`阈值，默认按07。Idle启用须正整数threshold、非负delay；旧key明确报替代位置，不自动迁移。
2. 保留Force原生测量和余量公式；去掉旧profile选择和special配置，只输出一套Noting设置。坏配置仅使所属功能失败关闭，不能连带关闭History或另一个功能。
3. 沿原生配置同步／Prompt构造与恢复边界落实Noting与原生idle-return-compaction互斥；local开关不重建root。不要每Turn刷新root／MCP／memory，也不取消已冻结的全局切换一致性要求。
4. 原位替换Main Role、Notebook、Time、History模块；Scheduler指导独立受其开关控制。原生session_search只在实际可用且eligible Main内窄覆写指导；Cron私有Schema copy、manifest/tool_search说明仅Scheduler可用Main启用，不修改全局原生Schema。
5. `/notebook`仍为查看、`/noting on|off`仍为local参与；去掉Memo阻止off／Memo帮助。`/propose-persistence`与超限提示共用一个Proposal常量，不预检索全History、不把命令视为批准。
6. 将C9要同步的能力字段、Schema刷新时机和新的setting类型精确交回；不得靠Prompt声称存在尚未dispatch的工具。

**后置测试源码／预期：** Noting×Scheduler四组合＋local off；未知坏配置不影响其它功能；冷恢复/全局切换Schema与Prompt一致；非Main原生Cron/search文案不变；Proposal两个入口同常量；无新个人依赖。

### C5 — Noting child、四工具、显式结束与续跑

**分支：** `round3/c5-noting-child`。**依据：** R-RUNTIME、R-NB；特别07§4.5、§8.11/8.12完整英文任务及白板C7／N1。

**白名单：** `secretary/noting_child.py`、`secretary/noting_tools.py`和本域小helper；新增`tests/secretary/test_r3_child.py`。不改cache_parity、父compaction入口、framework_messages或全局executor；只给C9需要调用的guard／handler。

**按顺序实现：**

1. 保留`freeze_parent_active_prefix/build_noting_child/NotingTaskRunner/spawn_noting_task`的真实父消息冻结、deep clone多模态、持久child、独立DB及资源关闭。每次请求的父root/tools/messages前缀保持，后缀追加本任务四工具完整Schema，不重新从History组装父前缀。
2. 四工具仅`conversation_history/notebook_show/notebook_maintain/finish_noting`。maintain调用C1工作态；show按真实绑定task返回working，不读父最新Snapshot覆盖草稿。Main show留给C9真实资格注入。
3. 使用07§8.11完整任务和§8.12续跑文本，六步顺序、逐类型具体动作、来源/用户认可、7天/72小时、原位候选、部分结算及不访问外部目标全部保留；不再输入或消费Memo。
4. 同步／并发工具批次在**执行任何一项前**判断：含finish且多于一调用，整批invalid_argument且零副作用。成功finish在同一任务锁内记录首次reason、end_requested并固定工作态；后续maintain拒绝，重复finish幂等，show/History仍只读。
5. 原生Turn返回后才经Commit Gate提交；文本done不是显式完成。最多五Turn，子任务禁止auto-compaction；五Turn或已处理context_overflow可提交合法完整状态含无修改视图，分别留forced/overflow限制。其它失败/中断不能伪报成功。
6. 删除special profile和compact_parent工具／forced compact分支。C7负责父压缩；C8负责有效结果通知。提交C1的事务结果原样传给通知接缝，不额外查询猜生效。

**后置测试源码／预期：** 四工具权限含并发；finish混合批次前后顺序均零写；finish后不可再写；重复finish保留首次reason；五Turn与overflow；正常失败不发布草稿；多模态/prefix结构不变；子runtime不触发NM独立Bundle/Recall/sync。

### C6 — Scheduler实际投递、在途竞争与ACK

**分支：** `round3/c6-delivery`。**依据：** R-SCHED；07§6.2/6.4/8.14，继承既有deferred carrier与成功响应ACK。

**白名单：** `secretary/reminders.py`、`secretary/reminder_request.py`、`secretary/cli_reminders.py`；C3合并并交接后允许窄改`hermes_state_secretary_schedule.py`的接纳／ACK函数；新增`tests/secretary/test_r3_delivery.py`。host全局入口接线交C9，不增另一投递队列。

**按顺序实现：**

1. due scan使用独立Schedule定义与开关，不读Notebook业务状态；正文改为07 SCHEDULED ATTENTION，保留每项schedule_id/due_at/delivery_mode/content。
2. idle instant沿现有Main admission唤起，busy原子转pending deferred，不排一个未来强制Turn；new/reset/fork／continuation路由按当前owner。
3. `materialize_pending_reminders`在真正追加carrier的事务内重读每个occurrence和当前定义／撤销状态，不能仅在claim/prepare检查。instant保留`ActiveReminderAdmission.commit`落库前重验。定义先变则旧witness不落库，carrier先提交则在途不可撤回。
4. 批量deferred仍一条durable carrier，绑定全部实际occurrences；只对真正请求携带且Provider成功响应的项ACK。provider失败、空结果、载体准备成功都不能吞掉pending；pause/delete后ACK不得复活定义。
5. instant实际投递排除本次发生后重算24小时notice；busy降级的原instant在最终注入重算、同批只附一次；纯deferred不新增检查入口。unknown只给未知，不断言没有；Due与timestamp保持不同含义。
6. 保留已有lease释放、失败重试、资源退休和持久witness，不增加exactly-once承诺或重启必达通知队列。

**后置测试源码／预期：** claim→pause/delete/update→materialize；materialize后pause的在途语义；instant idle/busy；失败后可重试；单carrier多ACK；同批有一项撤销；响应成功但未携带不ACK；24小时在prepare后变化；Noting关闭Scheduler仍工作。

### C7 — 父runtime联合触发与压缩区间占用

**分支：** `round3/c7-joint-runtime`。**依据：** R-RUNTIME；07§8.1、§11.1和D01保留规则。

**白名单：** `secretary/noting_runtime.py`、`secretary/noting_timers.py`、`secretary/noting_capability.py`、`secretary/noting_admission_receipt.py`、`secretary/noting_compact.py`、`hermes_state_secretary_noting.py`；新增`tests/secretary/test_r3_joint.py`。C4独占policy/scope；C9独占`agent/turn_context.py/turn_preflight.py/context_compaction_request.py`等正式调用者。

**按顺序实现：**

1. 提供自动/手动/Idle/Force共用的联合入口，普通压缩前冻结并admit child，与原生compaction并行，不等待child；Noting失败不能阻止原本必须执行的压缩。
2. Force继续原生ResolvedContextWindow与阈值余量，不重新估算；在同一admission事务按最近成功compaction边界或Conversation起点取得区间身份，检查并登记Force占用，覆盖所有联合入口。
3. 区间占用独立于Anchor是否仍可见；新Anchor、child成功/失败/释放、rewind都不清掉本区间占用。只有真实成功compaction形成新边界才可在新区间整理；失败/no-op压缩不能重置。后续达到压缩条件只做原生压缩，不补起更晚大任务。
4. Idle默认关；Main结束并实际仍空闲达到delay且真实token占用达threshold才联合；Main新Turn取消等待，child活动不重置Main时钟。沿现有daemon timer/owner恢复，不新建定时系统。
5. 四入口freeze/admission副作用前复用真实Main请求D01；已证External只拒绝Noting，未知沿旧规则，不增加拒绝条件，不检查缓存是否热。History/Scheduler与必须执行的压缩不受影响。
6. 保留Force接纳及External拒绝Framework producer/suppression；Force通知只在成功compaction后从当前上下文退休，持久原文保留。结束资源释放不等于区间重新可用。
7. 向C9给出各入口准确参数及“何处只调用一次”的替换表。重启不自动恢复child，不新增持久任务队列。

**后置测试源码／预期：** 四入口共享谓词；同区间换Anchor/finish/failure/rewind仍不重启；成功compaction新区间可启动；无须等待旧child；D01两种External封装；unknown/native保持旧行为；Idle双条件；失败压缩不退休通知；Noting关闭原生压缩仍正常。

### C8 — 生效pointer、完整Snapshot及Framework通知

**分支：** `round3/c8-framework`。**依据：** 白板N3/L1/L6/L9/P2，07§7/8.13/11.1；消费C1事务结果和C4共用Proposal。

**白名单：** `secretary/framework_messages.py`及窄通知helper；C1合并交接后可窄改`hermes_state_secretary_notebook.py`的pointer条件追加接口；新增`tests/secretary/test_r3_framework.py`。notebook_render由C1提供，不重写第二renderer；不改Web DTO或人类UI。

**按顺序实现：**

1. 只有本次成功提交使pointer切到自身才准备完成通知；旧结果可保留提交审计但不发正文/Proposal，也不冒充失败。
2. 同一Framework包含结束通知、该Snapshot完整payload正文、可选Proposal。正文从已提交有效Snapshot读取，不让模型转写；不能只给ID或让Main额外show才获得内容。
3. 排队保持snapshot_id，实际追加前在既有事务/锁边界核对pointer仍匹配；已被取代整条丢弃含Proposal。比较与durable追加/live发布保持一致序，不先查再无条件append。明确统一锁顺序，避免与Snapshot commit反向锁形成死锁。
4. 完成时间保持提交/完成语义，不作coverage排序；允许跨compaction晚到，不新起Turn、不等待下一次compaction。
5. 统计实际注入Notebook正文Unicode码点及独立当前entry总数，三板块与candidate均计；引用不重复计entry。严格`>`阈值才追加C4同一Proposal常量；不计包装、不截断、不拒绝commit、不启动精简任务。
6. failure与forced/overflow成功分别渲染；无新Snapshot才使用失败文案；保持原有内存队列能力，不承诺重启必达。

**后置测试源码／预期：** B先完成A后提交；A排队后B生效；A已追加后B生效；pointer检查和append竞争；rewind重新选pointer不凭空发完成；字符/条目阈值等于与超过；单条完整正文；无新Turn。

### P1 — 独立Provider资格、稳定Bundle与输入前Recall

**分支：** `round3/p1-provider-context`。**依据：** R-PERSONAL，PHASE3§1～3/6/7；不把旧Helper的严格来源验证扩展回来。

**白名单（Provider仓库）：** `nowledge-mem-hermes/personal_provider.py`、`personal_scope.py`、`personal_client.py`，必要时窄改`client.py`以复用现有连接解析；新增`personal_tests/test_r3_provider.py`。不改公共Secretary、personal_cli、社区其它集成或integrations.json。host通用缺口交C9判断，个人特有host改动只能另在个人分支实施。

**按顺序实现：**

1. 检查实际origin/source/parent/delegate及只读Secretary binding，落实Main/continuation/Cron/Noting/其它辅助/unknown矩阵；Cron只归档，Noting不独立抓Bundle/Recall/sync，不因user role或Ref存在变Main。
2. 单Provider，get_tool_schemas空，queue_prefetch no-op，sync_turn保留；不新增MCP／nmem模型工具／第二同步插件。配置关闭内置MEMORY/USER活跃来源不删除旧文件，不盲目关闭影响Provider注入的整个toolset。
3. Bundle使用include_working_memory=false，GLOBAL RULE按PHASE3§6替换；贡献跟随原生构造/恢复/压缩重建生命周期，不每Turn抓取改root。检查既有按thread缓存是否会错误跨过原生重建边界，必要时在本Provider生命周期内修正，不自建全局缓存管理。
4. 有意义的host已准入输入通过prefetch做Memory Search，默认timeout8/recall_timeout2/limit5/max_chars2400；不调用ask或LLM预检索。保持完整ID、标题、可得时间与不可信数据编码；不返回正文，不称已读记忆。
5. 失败不复用旧指针，保留短不可用提示和Memory check；空结果不证明无记忆。短CJK不得被旧最小长度一概拒绝。api_content重放限制明确保留，不声称本轮实现一次性注入。
6. 网络故障不关闭公共History，不改NM治理配置；将Scope、连接解析、Bundle调用及P3要消费的读取接口写入PR。

**后置测试源码／预期：** 全runtime矩阵；no network during availability；Bundle无Working Memory；重建生命周期；CJK/恶意标题/完整ID；离线无陈旧指针；无独立Noting网络；History不受NM故障影响。

### P2 — 官方CLI创建＋仅补Metadata的小脚本

**分支：** `round3/p2-provenance-helper`。**依据：** PHASE3§4.1/6，索引R3-006/008/009/010。**本任务不是重写nmem。**

**白名单：** Provider的`nowledge-mem-hermes/personal_cli.py`，必要新`personal_metadata.py`，插件已有nm-cli skill中本脚本用法。不修改P1的personal_provider/scope/client；只消费其现有公共连接能力。具体skill路径从本分支树确认，不凭文件名假定存在。

**按顺序实现：**

1. 删除当前helper直接HTTP创建/编辑Memory正文、expected-sha通用写入、强制本地History成员核验及完整写后回读体系的活跃入口；正常管理直接官方CLI。
2. Main提供已批准正文、类型标签、完整Hermes来源。窄脚本用参数数组调用官方`nmem --json m add`，不shell拼接，不自动猜来源、不改写正文；labels仍走官方CLI字段。
3. 依据可读取的官方CLI实现/JSON契约解析真实返回主键，失败或outcome unknown不能猜ID。只向此ID补写metadata.hermes_provenance，保留无关Metadata，不填NM原生Thread来源字段。
4. CLI和补写沿同一运行主机有效配置与覆盖规则，包括endpoint、credential和remote selection；不硬编码Mac路径、localhost服务、端口或第二套脚本配置，不输出密钥。
5. 创建成功而补写失败时明确返回ID和partial状态；修复路径只接受这个已创建ID补Metadata，不再m add；创建结果未知不盲重建。不得把两步说成原子事务。
6. 若运行主机CLI JSON或Metadata协议在云端源码中不能确定，隔离到一个小解析/补写函数并列出待本地基本调用检查，不虚构字段已验证。不能因此恢复旧完整helper或取消provenance要求。

**检查边界：** 云端只人工审读；本地只基本语法/参数/模拟返回与调用顺序检查，不设独立严格测试组、不做真实NM写入、不重测CLI通用功能、不加来源审批系统。实际连通调整留后续云端部署，不能把这一例外扩成其它Provider免验。

**交回：** 命令调用方式、真实ID解析依据、同配置接线、部分失败返回及仅修复Metadata方法；其它操作如何回到官方CLI。

### P3 — completed Turn归档、收据及个人实际接线代码

**分支：** `round3/p3-thread-archive`。**依据：** PHASE3§2/5/6/7；C2只消费现有合法History接口，P1/P2先合并。

**白名单：** 顺序接手P1的`personal_provider.py`/`personal_scope.py`中归档与生命周期；已有收据逻辑、`install_personal.py`、插件README和必要skill入口；新增`personal_tests/test_r3_thread.py`。不新增转录事实库、蒸馏任务或改NM治理；不在本次执行安装。

**按顺序实现：**

1. 只同步真正completed且未中断Turn的合格User/Assistant正文及时间。Main取合法跨压缩History Foreground并使用host批量egress redaction；Cron取已按host规则处理的自身执行正文，辅助/unknown/Noting无sync。
2. Thread key为hermes-personal-identity：Main用conversation_ref，独立Cron/普通原生fallback用physical session_id；new/reset/fork分开、合法continuation保持。Thread不是Hermes规范来源身份。
3. 复用现有receipts.sqlite3，按endpoint/Space/Thread维护ACK prefix fingerprint；相同prefix仅suffix上传。明确服务ACK才推进，失败不推进；不承诺exactly-once，不把本地去重当服务端去重证据。
4. rewind/edit/path变化使已ACK前缀不一致时reconciliation-required，不覆盖删除旧Thread，不偷偷换Thread续写；不把这种限制修成未经授权的新同步协议。
5. 完成Provider安装代码对新窄脚本/skill的引用和公共host接口适配说明，但不修改用户真实profile、不开Background Intelligence。若公共host确有一般性接缝缺失，交C9最小通用补丁；个人专有补丁不能落公共main。
6. 列出本地测试端点与真实服务的严格区分；任何真实Thread写入仍待明确授权。普通Hermes运行也可能自动sync，不能在连接个人服务的配置下启动一次“只读试跑”而意外归档。

**后置测试源码／预期：** completed/interrupted；Main/Cron/Noting矩阵；redaction跨行重复秘密；continuation/new/fork；ACK/timeout/重试；prefix divergence；endpoint或Space切换隔离；no distillation。仅隔离本地HTTP／假客户端结果不得称真实NM通过。

### C9 — 公共正式dispatch、host生命周期与预算反馈接线

**分支：** `round3/c9-core-wiring`。**依据：** R-HIST/R-SCHED/R-RUNTIME/R-PROMPT；07§9.1每一行及§9.3，06只保留原生客户端边界，不引入UI任务。

**白名单：** `secretary/noting_surface.py`、`secretary/noting_hosts.py`、`agent/inline_tool_executors.py`、`agent/tool_executor.py`、`model_tools.py`、`toolsets.py`、`tools/registry.py`、`tools/tool_result_storage.py`、`tools/budget_config.py`；`agent/turn_context.py`、`agent/turn_preflight.py`、`agent/context_compaction_request.py`、必要`agent/conversation_compression.py`；`tui_gateway/session_compression.py`及实际调用它的原生RPC接缝；必要`hermes_state_secretary_schema.py`、`hermes_state.py`只作facade/schema组合。其它CLI/gateway host glue或`agent/memory_manager.py`如确有缺口，先向主会话列出具体文件/符号/必要性取得单文件所有权，不获得整个目录的任意修改权。新增`tests/secretary/test_r3_wiring.py`。

**按顺序实现：**

1. 逐条接入C1～C8的已合并接口；实际schema、tool catalog、同步执行、并发执行、inline专用分支、工具发现与冷/热恢复统一一套新工具。资格由真实runtime传入，Main不可maintain/finish，Noting不得Scheduler/跨域History/父工具。
2. 将finish整批预检放到任意工具实际执行之前，覆盖原生并行executor；不能只在单工具handler检查。结束后工作态固定与任务锁保持同一语义。
3. History所有eligible Main常有，Scheduler独立gate，Notebook按既有全局Noting gate；noting local仅影响参与。原生session_search和其它runtime工具集不被强制改变。
4. 把自动/手动/Idle/Force接到C7唯一入口；冻结必须在父上下文压缩前，原生必需压缩不能因Noting gate失败取消。精确删除旧重复启动路径，不保留special child→parent compact调用。
5. 将C6接到真实due scan、Main busy admission、request materialize、响应ACK及退休路径；profile/route在正式入口一致，关闭Noting不导致Scheduler host tick被跳过。
6. 在真实单结果spill与批次总裁剪接缝区分可信Noting身份：History太大先缩小邻域，单条仍超限明确允许工具无法续读；不提示read_file/terminal。保留其它runtime原提示、预算和落盘能力，不改阈值。
7. 更新公共Schema初始化与facade组合，移除本轮退出的Memo注册、旧tool alias/dispatch、Notebook排期耦合和旧配置消费者。恢复历史中旧调用返回legacy_tool_removed并引导新工具，不静默重放、不删除历史记录。
8. 建立源码调用图：各入口→资格/配置→工具/联合runtime→事务→输出/ACK。检查import与实际参数对应；若暂存兼容旧DTO代码，只能是无执行权的历史／延期展示路径，不能把旧Memo工具复活。

**后置测试源码／预期：** 从真实注册/dispatch而非直调helper覆盖四工具、Main三能力和开关矩阵；独立child不得父工具；批次预检；host触发不重复；request携带与ACK；冷/热恢复；单spill和批spill；legacy明确拒绝；公共核心无Provider安装仍可加载。

### C10 — 本会话负责云端源码集成收口

**分支：** 必要修补使用`round3/c10-code-closeout`，PR仍回集成分支，由本会话处理；不对已接收PR再派整轮审查者。

1. 合并C9/P3后固定双仓候选SHA；使用GitHub差异与符号读取核对07§9.1全部owner已接线。特别检查跨PR函数改名、导入、返回值从ID到结果的变化、锁嵌套、旧工具残余、schema/default与handler不一致。
2. 收口遗留测试：各owner提交的旧用例处置清单按现行契约更新；保留原生identity、prefix、ACK、错误路径的有效断言；退出的是旧行为要求，不是检查规则。不跑这些测试。
3. 检查没有意外改UI、真实配置、原生表ownership、锁文件、全局规则、个人依赖、密钥或运行数据。大型文件新增实现沿sibling原则，不在facade堆业务逻辑。
4. 对照§7覆盖清单，确认每行都有代码位置、拟执行测试和唯一后置执行组；缺代码的继续原PR或窄修复PR，不把缺口直接留给Verification。只需运行才能发现的问题诚实列为待运行。
5. 根CLAUDE记录`CODE_INTEGRATED_UNRUN`、双仓SHA/锁文件blob、已合并PR、开发未运行清单、预计本地入口；README只更新源码已落实能力并明确未运行，不更新旧轮次通过结论。
6. 到此停止云端编码阶段，准备本地D3/D4，不创建PASS报告、不安排正式发布。保留原始冻结要求，不为了代码方便反向改白板或07。

## 7. 全范围覆盖和唯一责任

本表用于主会话检查“是否有人负责”，不是开发通过证据；运行结论留根CLAUDE和本地证据。

| 契约组 | 实现owner | 云端必须有的可审查产物 | 后置运行owner |
|---|---|---|---|
| 七类型＋candidate、用户来源与原位引用 | C1/C5，C1结构、C5语义Prompt | 数据/关系校验；完整任务英文；行为fixture | L-A |
| entry/version、no-op时间、来源继承 | C1 | 单任务版本与commit事务、fork例子 | L-A |
| finish独立调用／四工具权限／五Turn | C5/C9 | handler＋正式批次guard＋runner，不只是Schema | L-A |
| 父prefix/多模态/D01 | C5/C7/C9 | 冻结及实际来源调用链，保留原生cache_parity | L-A |
| Force区间／四入口／Idle双条件 | C7/C9 | 同事务占用、成功压缩边界、全host替换表 | L-A |
| pointer与排队失效通知 | C1/C8/C9 | commit事实→条件append→live顺序 | L-A |
| 完整正文／Unicode阈值／共用Proposal | C4/C8 | 同消息生成与阈值函数，不截断正文 | L-A |
| History模式／域／物理候选诊断／fork | C2/C9 | 原生候选adapter＋合法路径读取＋dispatch | L-B |
| History spill反馈与legacy退出 | C2/C9 | 单结果与批结果两条正式路径 | L-B |
| Scheduler CRUD／独立开关／原生时间 | C3/C4/C9 | registry直接定义、当前Table、真实Main注册 | L-B |
| 在途撤销／busy转换／单carrier／ACK | C3/C6/C9 | materialize和instant commit事务重验 | L-B |
| 24小时notice含unknown | C3/C6 | 全Table helper＋工具结果和最终投递两入口 | L-B |
| Main Prompt／Slash／冷恢复门禁 | C4/C9 | 英文常量、私有Cron覆写和真实工具面一致 | L-C |
| Provider矩阵／Bundle／Recall | P1 | 单Provider hooks，无Working Memory／陈旧指针 | L-C |
| Thread正文／redaction／ACK收据／rewind | P3 | host完成边界→合法正文→收据 | L-C |
| provenance窄脚本 | P2 | 官方CLI真实ID→同端点Metadata，partial不重复创建 | L-C基本检查，不设严格独立组 |
| 原生不变量／退出旧要求／文档 | C10 | 现行条款映射、遗留用例处置、双仓SHA | L0统筹，各组只跑分配部分 |
| UI／真实NM写入／云端部署 | 不在云端实施 | 后置或未授权清单，不能写完成 | 不自动执行 |

## 8. 本地Develop：首次运行、测试与修复

### 8.1 L0：接收云端代码，不先跑全量基线

本地执行者先拿到C10的双仓SHA与PR清单，读取当前根文档和适用套件。原本Mac路径只是历史，不要求环境必须在固定目录，也不把本地机器当正式云端部署目标。

1. 检查两个checkout及并列Web工作区的dirty状态，保护已有前端修改／用户数据。只fetch后按确认分支切换；有未提交变更不reset/clean、不擅自stash后忘记还原。必要隔离checkout/worktree平铺父目录，不能覆写用户正在使用的目录。
2. 固定双仓代码提交，记录OS、Python/Node、PM/lock、依赖状态及运行入口。没有执行过的基线不补写通过；不为了建立基线先跑整套旧测试。
3. 按官方PM与锁文件准备`.venv`，显式`HERMES_PYTHON`；不裸pip/uv替换依赖管理、不改全局Python、不重新解锁。已有环境能复用则不重建。
4. 独立新`HERMES_HOME`和runtime，确认不指向生产profile；新schema只用新测试库。任何旧child结束／停止并经过原生fence后才换运行版本，不中途给活child换Schema。
5. Provider联调先接专用本地HTTP fixture／假客户端且无真实凭据。启动Hermes会触发sync的场景必须先隔离NM端点，不能因测试名称“只读”就连接个人服务。真实Thread写入仍需另获授权，小脚本真实写入不安排。
6. 把C1～P3待测文件与已有相关用例展开为互斥的L-A/L-B/L-C命令清单，记录首次测试commit；本地运行期间该checkout源码冻结，不一边跑一边由另一个进程改代码。

### 8.2 第一次执行的顺序

先最小环境/导入/测试收集问题，再分组行为测试，再实际host开发联调。不能先运行几小时大套件才发现模块根本无法导入。这个顺序是本地Develop排障，不是云端编码门槛。

| 组 | 范围 | 不重复跑的边界 |
|---|---|---|
| L-A | C1/C5/C7/C8：Notebook、child、joint、Framework与这些路径对应的C9用例 | 不重跑History/Scheduler/Provider全组 |
| L-B | C2/C3/C6：History、Schedule、materialize/instant/ACK、spill及相应C9用例 | 不重复L-A的child生命周期全套 |
| L-C | C4的配置/Main提示、真实注册组合、P1/P3 Provider hooks及P2基本调用检查 | 不以Provider例外免除公共接线检查，也不重测官方CLI管理能力 |

三组可在互不共享状态、端口和可写fixture时并行。环境构建与共享索引准备由L0做一次；不能三组各装一份依赖或用同一state.db。实际原生模型／运行服务联调由一个owner统一持有该runtime，避免三个组重启同一后端或重复付费测试。

核心测试使用canonical runner，不直接pytest。例如以下命令只有在拟新增文件已真正存在并被L0列入相应组后执行：

```bash
export HERMES_PYTHON="$PWD/.venv/bin/python"
# L-A首次运行；其它组使用各自准确文件清单，不展开整套tests
scripts/run_tests.sh tests/secretary/test_r3_notebook.py tests/secretary/test_r3_child.py tests/secretary/test_r3_joint.py tests/secretary/test_r3_framework.py
# L-B首次运行
scripts/run_tests.sh tests/secretary/test_r3_history.py tests/secretary/test_r3_scheduler.py tests/secretary/test_r3_delivery.py
```

配置/正式dispatch测试由L0按实际node ids分配一次，不能各组都跑全部`test_r3_wiring.py`。Provider沿其既有unittest入口选择本轮具体模块，例如在Provider根用实际解释器执行`python -m unittest discover -s nowledge-mem-hermes/personal_tests -p 'test_r3_provider.py' -v`，Thread模块同理；命令中的python应替换为L0记录的实际解释器。

相关冻结检查在本地执行：repair有staged变化时可用`.venv/bin/python scripts/check --staged --only <适用检查>`。**云端提交已经是clean工作区时，空staged检查不构成覆盖证据**；先读取当前`scripts/check`支持的范围参数，选择实际云端变更范围并记录展开的文件。不得虚构命令选项，也不得用空检查“通过”代替检查该批代码。

整套Python／全部保留检查／无差别UI构建不在任务级或此时反复启动；按AGENTS由后续独立门禁在集成收敛后统一决定和安排一次，共享同版本结果。此次界面未修改，不自动跑整个前端workspace。

### 8.3 实际host开发联调，和独立Validation区分

局部测试可控模型边界后，沿真实原生Main入口检查新工具是否真的送入请求、同步和并发调用是否受约束、自动/手动/Force/Idle是否只有一套接线、正常provider响应如何驱动ACK。使用隔离Conversation和已授权配置，不另选旁路模型执行器。

先公共核心无个人Provider运行，再把个人Provider装入专用隔离profile接本地fixture，观察真正host资格、Bundle重建、prefetch和completed sync。实际模型样本用于发现接线及新Prompt的明显问题，日志明确模型、请求、场景和限制；不把一个样本写成普遍效果／缓存命中／节费结论。不能只让测试直接调用helper而跳过正式入口。

不为开发联调重新设计UI；原生CLI／后台RPC可作为正式入口。这里处理实现者首次运行遇到的缺陷；独立Validation之后仍按自己的职责检验用户输入到输出结果，不是把相同整套命令再跑一遍。

### 8.4 失败归因与修复循环

```text
失败证据（精确SHA＋命令＋fixture＋输出）
 → L0区分环境／收集／契约替换／新增实现／跨模块接线／无法判断
 → 同一根因合并为一个修复包
 → 原owner或唯一当前文件owner修复
 → 原PR追加或新local-fix PR／阶段提交
 → 只复测原失败＋实际受影响相邻路径
 → 更新证据索引；其它同版本有效结果继续复用
```

- 环境失败先解决环境，不能改测试断言；测试本身仍验证旧已退出语义时，用现行07逐条说明替换，不将真实失败一概归类“旧测试”。
- 声称失败“早已存在”必须有相同fixture与受控基线的可复现对照；确需归因才做最小对照，不在正式工作区撤销用户代码，不因此重跑全部旧套件。
- 发生真实实现缺陷，修实现及必要回归用例，不加skip/xfail、放宽budget、重试掩盖、降低规则或改冻结产品要求。
- 并行修复只允许不相交文件；同一数据库/dispatch根因由一个owner负责。扩大影响超过任务边界由主会话重新分配，不让三个组各自修一遍同一个helper。
- 已静态确认的问题不拖到本地才故意修；本地循环负责云端未识别或必须运行才确定的问题。
- 无法覆盖的平台、真实NM协议／服务写入、云端部署分别记录为未覆盖／未授权，不伪装PASS；不把个人服务缺口连带阻断公共源码修复。

### 8.5 证据复用，避免主会话重复验证

每次执行记录：`evidence_id、repo/SHA或双仓SHA、dirty patch hash（有则必须）、规格版本、测试文件/node ids、命令、OS/解释器/lock/配置与fixture标识、实际依赖范围、结果、耗时、日志路径、执行者`。日志在隔离本地证据目录，不上传凭据、个人正文或完整生产数据；CLAUDE与PR只放摘要和定位。

证据状态区分`NOT_RUN / PASS / FAIL / BLOCKED_ENV / BLOCKED_AUTH / SUPERSEDED`。下游代码变化不自动废弃全部证据：只有被测实现、相关共享依赖、配置、fixture或环境发生影响该场景的变化，才标相应条目失效并安排定向复测。仅文档／其它不相关模块变化不能成为全套重跑理由；也不能只看被测文件hash不变就忽略其共享依赖变化。

主会话接收完整证据后审查版本与覆盖，不为了自己看到输出再运行。接线新增的测试验证跨模块关系，不复制上游单元用例。后续Verification/Validation可以使用这些证据，但仍保有必要反证和真实场景操作；节省重复不等于取消独立判断。

## 9. Develop停止条件与交接内容

### 9.1 云端阶段退出条件

全部范围内可完成源码修改与必要测试源码已集成；C10已处理静态可见的跨PR问题；两仓有确定提交；每个未运行项有执行位置／owner；无悬而未决的关键接口和偷留的产品TODO。状态写`CODE_INTEGRATED_UNRUN`，不是Develop完成。

### 9.2 本地Develop退出条件

实际环境可用；本轮相关局部检查、行为测试和正式host接线运行已执行；已识别范围内缺陷修复并获得针对性复测证据；适用旧不变量没有靠删断言逃避；实现、测试源码、必要文档及stage commits均已同步。主会话完成源码与证据接收，保留真实未覆盖/未授权项，不伪造整轮PASS。

交给后续独立Verification的材料仅需：冻结需求索引和实际双仓commit；PR／变更清单；条款→实现→正式接线→开发证据的映射；本地环境与命令；失败修复和证据失效记录；未授权NM写入、P2例外、UI／部署后置等边界。若范围内仍有可复现未修缺陷，标Develop未完成，不把它转嫁成“请Verification发现”。

真实NM自动Thread写入尚未授权时，个人接线可有本地fixture证据，但不能宣称真实服务或服务端去重通过。这个缺口必须显式交后续门禁判定；它不应阻止公共实现线推进，也不能被静默免除。P2仅按用户指定基本检查，不新增严格验收门禁。

**停止：** 不在本计划中创建或执行独立Verification/Validation任务、不填写其结论、不发布、不部署。后续启动时由主会话按现行套件派遣全新独立审查者；Development作者和本轮PR审查不冒充独立门禁。

## 10. 发给任一独立Chat的启动文本

用户只需替换任务ID；仓库、分支与依赖从该任务卡读取。主会话首次发包前先完成D0并在根CLAUDE记录集成分支真实SHA。依赖未就绪时先读规定材料，不替主会话擅自合并PR。

```text
你负责Hermes Secretary第三轮Develop计划中的【任务ID】。
请先通过GitHub连接器读取EdgarZhong/hermes-secretary根CLAUDE.md的第三轮当前看板，
以及.autonomous/20261016-round3-secretary-nm/plan.md、snapshot-index.md。
个人P任务再读EdgarZhong/hermes-nmem-provider根三份文档和PHASE3现行§1–7。
按plan的共同协议、阅读包和本任务卡执行，不要求我重新讲项目背景。

本轮执行方式已明确：你在独立网页Chat中完成源码修改；创建自己的任务分支，
准备一次或多次多文件更新，创建PR到本仓round3/develop。
代码写入前读取当前head/tree及待改文件完整内容；用原tree为基础创建新tree/commit，
非强推且校验expected head；不要覆盖他人变化、不要直接改main或集成分支。
不合并自己的PR；由规划主会话在原会话统一review/merge。

实际运行、安装、lint/编译、测试、浏览器、模型调用全部后置到本地Develop。
可以且应按任务卡编写必要测试源码，但统一标NOT_RUN，不宣称测试或验收通过。
静态已发现的问题现在修正；必须运行才能确定的问题列清楚，交后置本地组。
只改白名单，不派生其它Agent；共享文件需要主会话明确交接。
不改根看板/冻结规格/规则/CI，不做UI、不写真实NM、不部署、不引入个人公开依赖。

完成后按plan §2.4交回：PR链接、head/base SHA、实际改动、精确导出接口、
条款覆盖、待接入口、测试源码/预期/执行组、未运行与真实风险。
不只给建议或补丁文本；有写权限时实际创建分支、commit和PR。
工具不支持或写入失败时说明具体步骤和已生成对象，不虚报已提交。
```

## 11. 发给本地执行者的启动文本

```text
继续第三轮Develop的LOCAL_RUN/LOCAL_REPAIR，不开始独立Verification/Validation。
先读取根CLAUDE中CODE_INTEGRATED_UNRUN的双仓SHA、PR和未运行清单，
再读本计划§8～9与当前规则。保护用户现有工作区、前端改动和真实profile。

按官方PM/lock准备或复用环境；新隔离HERMES_HOME/runtime和新库；
Provider先接本地fixture且无真实NM凭据，防止completed hook意外写入真实Thread。
先解决启动/导入/收集，再执行互不重复的L-A/L-B/L-C定向测试，
由一个owner运行真实host接线联调。不得先跑一轮全量旧基线。

把首次实际失败按根因归类，委派给唯一owner修复，
修后只复测失败及实际影响路径；主会话复用准确版本证据，不再重复跑。
保留现行规则，不能为绿色结果放宽断言/阈值/预算或改变已审产品行为。
P2只做基本检查，不重测官方CLI，不做真实NM写入。

最后交回实际双仓commit、环境、条款/接线/证据映射、修复和未覆盖项。
云端代码集成、局部测试通过、真实NM通过、独立门禁通过、云端部署是不同状态。
完成Develop后停在独立Verification之前。
```
