# 全部本仓 worktree／分支收尾审计

审计日期：2026-10-31；只读盘点基准为本地 `origin/main=c07b038d1c8e5542068910c0c7f386d23ce81bb9`。未 fetch，因此“最新 main”仅指当前已知本地远端引用；真正执行前须重核引用和其它 Agent 的最终提交。本报告不执行清理／切分支／合并／提交／停服，也不改变源代码。审计只新增本报告及本轮 ignored 明细。

## 结论与必须处理项

1. 本仓登记 **8 棵 worktree：原根目录＋6 棵现存附加树＋1 条已不存在的 tmp 登记**。原根目录必须保留，最终在原路径检出最新 `main`；所谓“清理所有 worktree”应落实为只留这一棵主工作目录，不能删除共享 `.git`／`.venv`／Python 实体。
2. 所有旧树的 **HEAD 均已是 origin/main 祖先**；但这不证明 dirty 已整合。逐文件核对后：Idle-owner 14 个 dirty 文件逐字等于已接收提交 `0a5d09cdcf3d3a03cb8d83e6bdad284d87a10acc`，该提交已在 main；Remediation 的 7 个 dirty 文件逐字等于当前 origin/main。两者属于已整合的旧工作态，不应再合或旧文件覆盖。
3. 原根目录的长期文档 dirty 确有尚未纳入 main 的资料及当前讨论，须逐段整合。根三文档和 07 已明显落后于现 main 的部分现行机制，**不可整文件复制旧版本**。三份 untracked 文档不是缓存，需 review 后保存到 Git 对应入口或明确归档，不能删除。
4. `hermes-secretary-web-release` 占着本地 main，仍有真正独立的 **手动新 Noting debug RPC** 包：7 个代码／测试／生成文件＋07 四行规格＋旧前端报告附录。它并未入 main；历史测试有 23 passed，但证据明确写“待亲审／冻结检查／发布并实际调用”。此包不能以“旧 HEAD 已合”清掉，也不能无 review 直接把旧树整体合进最新 main。
5. 非主目录的 ignored `.hermes-dev` 合计约 **4.48 GiB**（不含本轮持续增长的新证据），包含真实模型／迁移来源副本、运行库副本、APK 和完整验收日志。最保守可完成方案是先按原树名保留整个 `.hermes-dev` 到原根 ignored 归档、核清单／SHA／软链后再移除树；无需为了删工作树同时清理这些证据内部的数据。可重建缓存另列，不误删私有证据。
6. 本轮 `evidence-recovery` 正在实施，HEAD 比基准 ahead 1；本报告仅观察，不触碰。应在产品／文档最终整合、提交、门禁及已授权发布完成后最后归档和移除。

## 逐树现状

体积是 `du -sk` 的目录分配量，不保证等额释放；软链接不跟随。ahead/behind 相对上述 c07，顺序为本树领先／落后。

| 路径（均位于 `/Users/edgar/code/`，tmp 除外） | HEAD／分支 | ahead/behind | dirty | 目录／ignored 证据 | 收尾决定 |
|---|---|---:|---:|---|---|
| `hermes-secretary` | 219bfc22ea／codex/web-recovery-20261024 | 0/116 | 11 tracked＋3 untracked | 12.87GiB／.hermes-dev 10.03GiB | 保留原目录；先语义整合文档，再检出最新main |
| `/private/tmp/hermes-noting-baseline-20261027` | 02d55fdb45／detached | 0/59（目录不存在） | 不适用 | gitdir 指向不存在位置 | 可清 stale 登记，不能把它当待删除实体树 |
| `hermes-secretary-evidence-recovery` | 8b31d986dc／codex/evidence-recovery-20261031 | 1/0 | 活跃变化中 | 起始约297MiB，证据持续增长 | 本轮完成后最后归档／移除 |
| `hermes-secretary-idle-noting-owner` | e1b124d450／codex/idle-noting-owner-20261027 | 0/55 | 13 tracked＋1 untracked | 575MiB／163MiB | 14/14逐字等于已合0a5d09；证据归档后可清 |
| `hermes-secretary-incremental-remediation` | 0c33f3b83e／codex/incremental-r2-remediation-20261029 | 0/20 | 5 tracked＋2 untracked | 424MiB／11.5MiB | 7/7逐字等于c07；证据归档后可清 |
| `hermes-secretary-incremental-sync` | c07b038d1c／codex/incremental-sync-20261027 | 0/0 | 无 | 2.85GiB／2.44GiB | 干净且已合；证据归档后可清 |
| `hermes-secretary-noting-chain` | 33f3b64a55／codex/noting-provenance-history-20261027 | 0/56 | 无 | 1.78GiB／1.37GiB | 干净且已合；含私有实库／模型证据，先归档再清 |
| `hermes-secretary-web-release` | 5fc54fc233／main | 0/53 | 7 tracked＋2 untracked | 925MiB／508MiB | 先处理独立debug包与历史报告，再释放main |

### 原根目录：逐文件去向

| 文件 | 与 origin/main 的关系／内容审查 | 必须处理 |
|---|---|---|
| `.autonomous/20261024-web-recovery/final-delivery.md` | 字节相同 | 不再搬运，不改写历史结论 |
| 同轮 `plan.md` | 字节相同 | 同上 |
| 同轮 `snapshot-index.md` | 字节相同 | 同上 |
| 同轮 `reports/frontend-contract.md` | main 缺末尾4行“0.1.5 404来源与adapter复制修补”附录 | 按2026-10-25时点补入历史报告；不能把当时“未验／待审”改成今日结果 |
| 同轮 `reports/frontend.md` | main 缺末尾16行同包7项交回说明 | 保留当时边界及manifest入口，作为历史附录整合 |
| `AGENTS.md` | 生命周期／通用owner等已有同义规则；根旧版却含旧客户端恢复／APK重载口径，现main已是增量对账与禁止业务自动刷新 | 以最新main规则为底，仅吸收确实缺失通用约束；不得用根旧完整恢复文字回退现机制 |
| `CLAUDE.md` | 根有10/31调查与定稿、10/28讨论、迁移／视觉等同步；main已有后续实际实现／交付，根大量“讨论中／未实施”是旧时点 | 保留新增且未覆盖的当前调查／待办，历史结论转明确时点；当前状态由最新交付覆盖。不得把Noting解耦等已上线功能写回未实施 |
| `README.md` | 根多若干稳定索引；main已有更完整正式服务器／增量恢复／APK校验说明 | 只合新文档入口和有效稳定事实，保留main现行运行命令及校验入口 |
| `docs/07-scheduler-notebook-noting-compaction-redesign.md` | 根dirty相对旧HEAD增加约485行，但许多v2／History等已经被main后继收口；根顶部证据描述／Main回查是本轮已冻结输入 | 以本轮与main最新07为底，逐节保留尚缺用户确认；不能把整个485行patch无脑再应用，不能回退联合取消／Force／Note消费契约 |
| `docs/cloud-deployment-sop.md` | 当前main已含主要迁移SOP；根额外有旧北京模板边界、当前K3.1及废弃seoul说明 | 吸收缺失的历史边界／稳定入口文字，避免重复首尔迁移正文；保留main当前正式机事实 |
| `docs/operations-log.md` | 根补视觉配置与重启、迁移／MCP／0.1.8、SSH／清理／阈值／模型切换等历史收据；main有更新的后续部署 | 按日期／事件去重插入缺失条目，保持源正文与原证据有效／已删状态，不把旧部署版本当现版本 |
| `docs/adaptive-noting-threshold-proposal.md`（untracked，约12.5K字） | main不存在；10/21算法初稿，明确未实现，不授权自动写配置；当时131072是历史值 | review后保留讨论稿及README入口。标明分析时点，当前静态98304已获后续授权，不让读者误以为在线仍131072 |
| `docs/mobile-web-investigation-20261020.md`（untracked，约18.4K字） | main不存在；完整22组反馈调查，后续认证说明明确不改写10/20缺口 | review公开／个人内容后保留；历史证据不等于当前缺陷仍开放 |
| `docs/noting-compaction-framework-interruption-20261028.md`（untracked，约4.1K字） | main不存在；00:06重启中断调查原报告，根CLAUDE明确已移入docs且正文SHA保持 | 保留原报告及稳定索引；现main解耦实施另记，不回写历史时间线 |

上述文件的完整旧HEAD diff、相对main diff、源文件SHA及可审副本均在 ignored `hermes-secretary/` 明细。报告只是去向，不代表已经完成语义合并或公开内容审查。

### Idle-owner：14文件确认已整合

`reports/idle-owner.md` §8明确主会话接收在main提交 `0a5d09cdcf...`，本次独立逐字核对14/14全部相同；`git merge-base --is-ancestor 0a5d09cdcf origin/main`对应已合链。与当前main不同的6文件是后继修改，不能重新搬运旧文件。

- 当前main字节相同：`run_agent.py`、`secretary/noting_compact.py`、`tests/secretary/test_idle_noting_reuse.py`、`test_noting_busy_idle.py`、`test_noting_timers.py`、`tests/tui_gateway/test_cold_noting_resume.py`、`tui_gateway/session_lifecycle.py`、`session_reaper.py`。
- 与当前main不同、但字节等于已合0a5d09：`secretary/noting_child.py`、`noting_runtime.py`、`noting_scope.py`、`noting_timers.py`、`tests/secretary/test_noting_runtime.py`、untracked `tests/tui_gateway/test_idle_noting_owner.py`。
- `idle-integration-comparison.json`是逐文件凭据。当前main差异包括后续解耦／Force／取消／Note提交路径等，旧owner工作态只是历史版本，不是待合新增产品。

### Remediation：7文件确认已整合

以下全部逐字等于当前origin/main：`.autonomous/20261027-incremental-sync/verification.md`、`agent/compression_facade.py`、`agent/context_compaction_request.py`、`secretary/noting_joint.py`、`secretary/noting_native_link.py`、untracked `tests/secretary/test_joint_native_failure_independence.py`及`test_joint_native_fallback_identity.py`。未发现独立产品增量；归档补丁／来源后可直接清旧工作态。

### main占用树：尚未整合的manual Noting debug包

完整读过7个代码／测试／契约文件及07新增说明、`summary.json`和最终日志。用户2026-10-25授权记录是“当前原生Compact未伴随Noting时，明确补跑一次新manual Noting；不借旧failed child／伪造失败，不额外Compact，不改自动配置，忙时不抢Main”。其dirty与main所有对应文件都不同；新helper及测试在任何Git提交中均未出现。

| 内容 | 当前状态 |
|---|---|
| `tui_gateway/noting_debug.py`（untracked） | 新的启动／查询实现，audit存在root session model_config；原生resume／parent、lease、prepare_joint_noting、child及commit见证；已读完整文件 |
| `methods_noting_recovery.py` | 新增secretary.noting_start／secretary.noting_state注册 |
| `contracts/noting_recovery.py` | 新增Params／Result；显式status枚举仍为旧生命周期集合 |
| `server.py` | 启动入口进入_LONG_HANDLERS |
| `apps/shared/src/gateway-contract.generated.ts`、`gateway-contract.openrpc.json` | 新方法生成契约，不能只带helper不带生成产物 |
| `tests/tui_gateway/test_manual_noting_debug.py`（untracked） | 17项新入口场景，原生冷恢复／幂等／忙租约／关闭能力／失败释放等；旧fixture属于2026-10-25实现时点 |
| `docs/07...md` | 2行接口表＋1段授权及空行；需转入当前07相应调试章节 |
| `.autonomous/20261024-web-recovery/reports/presentation.md` | 13行2026-10-25移动侧栏导航性能交回附录，和debug不是同一产品包；仅历史报告整合，不借此引入独立前端代码 |

**已有证据：** `manual-noting-debug-20261025/final-rpc-v3.log` 为2文件23 passed（新17＋既有恢复6），10.7秒；`generated.log`为生成校验1 passed。summary明确未stage／commit／push／部署，待主会话亲审／冻结检查／发布实际调用，production_model_calls=0。早期真实自锁反例、失败日志、基线review.summary事件失败均保留。

**并入main前还需：**

1. 按本轮最新main的owner／lease／route恢复及锁序亲审，只移植本包增量；旧树比main落后53提交，不能整体checkout旧源覆盖新main。
2. 重新检查新的解耦／取消／替代生命周期：当前child可能返回 `cancelled`／`superseded`，旧NotingStartResult枚举没有这两项；旧receipt原样读child.status，必须核当前契约序列化及消费方并补相应行为验证。此为具体待审风险，尚未运行新基线反证，不直接声称已触发生产错误。
3. 新实现的提交后FM／Note消费已经改版，旧17项断言“父timeline末尾立即有noting_run_output”不能直接当现行验收；按用户已确认的新Note资格／投递契约核通知路径，不为通过旧测试恢复已废弃串行流程。
4. 在最终集成版本跑该入口／恢复／生成契约与相关失败路径、冻结相关检查，明确“不额外Compact／不改自动配置／不启动Main模型”。旧23项不是当前版本测试证据。实际生产补跑涉及模型／Notebook写入，不因清树授权自行重放一次；代码收尾和生产调用范围区分。
5. 该能力有历史明确授权，不是未经确认的新改版；但如果无法在现契约内窄修补，先保留完整独立包并显式列未完成，不能以归档代替“已合干净”，也不能默认引入改变完成条件的设计。

## 运行依赖、数据与环境保留

- 本机 `ps`／`lsof` 全进程cwd和打开文件已取证；快照时**未发现附加worktree作为cwd或源码打开路径**。根目录仍有Codex／node_repl／MCP／zsh等进程cwd，Git status服务有pack索引打开；这些不要求停服，但原目录不可移走。没有观察到Hermes uvicorn／Vite开发服；5174／53445／53446／53448监听均不在本次监听快照，不能沿用10/26历史服务仍运行的说法。执行删除前仍须重查瞬时变化。
- 未停任何服务，未访问云端。三条Mutagen connected/watching；端点是Desktop/Alex、用户Profile配置与`.snapshots`，均在源码树外。sqlite mirror LaunchAgent配置由`~/scripts/hermes-sqlite-snapshot.py`、mise Python及用户Profile目录驱动，cwd=`~/scripts`，不依赖附加树。
- `launchctl list`只读调用被工具策略禁止；没有绕过或停止任务。故launchd实时状态未取到，使用可读plist＋ps／lsof确认已观察事实，不宣称完整launchd注册审计完成。
- 5棵现存附加树（含本轮）`.venv`均为指向原根 `.venv` 的软链接；Remediation没有该顶层软链。删除软链接本身可以，**禁止跟随链接删除实体**。
- 原根 `.venv`实体约257MiB；其`bin/python`指向原根`.hermes-dev/tools/python-3.14.7+20260901-darwin-arm64/bin/python3`。`.hermes-dev/tools`约938MiB，是解释器／工具运行依赖，不能当测试缓存清。原根`.hermes-dev`、真实导入材料、已有retained证据等保持。
- 附加树ignored证据必须按树名保留，不能把相同`incremental-sync-20261027`目录直接覆盖合并：Idle-owner163MiB、Remediation11.5MiB、incremental-sync2.44GiB（其中force-completion约35MiB）、noting-chain1.37GiB、web-release508MiB。本轮额外新证据最后单独归档。
- `noting-chain`数据／配置文件15个约962MiB，`incremental-sync`21个约9MiB；只盘元数据，没有读取私有正文或凭据值。对应 `data-config-paths.json`列路径、体积、模式。其余附加树这类后缀统计为0不表示所有文件非敏感，真实API／wire／日志也可能含私有内容，整体按私有证据保存。
- 根ignored三百余个库／配置条目约2GiB，是保留范围，未尝试清理。真实运行用户Profile及其WAL／SHM、同步完成包在源码树外，不列为工作树垃圾。
- 本仓未发现Android签名实体；独立前端仓库`/Users/edgar/code/hermes-secretary-web/src-tauri/.android-signing/`存在，权限0700，属于独立仓库根，不得被任何本仓清理命令触及。

### 可清缓存（保留证据后的白名单）

附加树的普通`__pycache__`、`.pytest_cache`／`.pytest-cache`、`.ruff_cache`、`test_durations.json`、`.bytecode-fingerprint`均可随树移除。主目录`node_modules`约362MiB、`.build`约9.6MiB虽然可重建，却不属于“删除附加树”的必要动作，本次建议保留。`.hermes-dev`内嵌的source/head-source、测试Home、模型wire、数据库和APK不得用后缀或目录名字笼统清退；本次保留整个证据根可避免另外一轮数据删减审查。

## 分支收尾

只处理本仓用户功能分支；不合2723个remote refs，不改`upstream`／`hermes-upstream`镜像，不删除stash，不删除远端分支。

| 本地分支 | 相对c07 | 处理 |
|---|---|---|
| codex/evidence-recovery-20261031 | ahead1且正在实施 | 最终实现合入main后再删本地功能分支 |
| codex/idle-noting-owner-20261027 | ancestor | 归档树后可删本地branch |
| codex/incremental-r2-remediation-20261029 | ancestor | 同上 |
| codex/incremental-sync-20261027 | 与main相同 | 同上 |
| codex/notebook-context-heartbeat-20261025 | ancestor | 无worktree占用，可删本地branch |
| codex/noting-maintenance-v2 | ancestor | 同上 |
| codex/noting-provenance-history-20261027 | ancestor | 归档树后可删 |
| codex/round3-local-completion | ancestor | 无worktree占用，可删 |
| codex/web-recovery-20261024 | ancestor | 原目录迁到main后可删 |
| codex/web-recovery-production-20261025 | ancestor | 无worktree占用，可删 |
| codex/round2-clarify-settlement | 非ancestor，独立1提交8b880c7 | `git cherry origin/main <branch>`显示`-`，补丁已等价整合；不再合产品，先保引用／bundle后可删本地分支 |
| codex/round2-output-identity | 非ancestor，独立1提交839d8f3 | 同为`git cherry -`，同上 |
| fix/remove-platform-prompt-hints-20261019 | 非ancestor，独立1提交3c8e995 | 同为`git cherry -`，同上 |
| hermes-upstream | 官方镜像 | 原样保留，不作为Secretary待合分支 |
| main | 落后origin/main53 | debug包先处理并释放占用；最终原目录main必须等于最新已集成origin/main |

三个非ancestor分支并非只做近似判断：已找到main内对应提交，逐文件的before／after Git blob完全一致，`git show --format= --binary`完整补丁字节也完全一致：

| 旧分支独立提交 | main对应提交（均是c07祖先） | 完全相同的文件delta |
|---|---|---:|
| 8b880c7df3d4434101b5061f60ccf13f98a7fcfb | 7567dc3a17d8a1fa48b78fc45c3de3503901494f | 3/3 |
| 839d8f3a47bf9e9737828a0d2a8abbd084816be8 | d276ea8b60441da61745c31be36ab2ff1fea58c3 | 12/12 |
| 3c8e995c5656d2b540889ff262d1ff23e7fd2b16 | e879cf863142a2277883d37cd57b747be3c68e35 | 6/6 |

证据`equivalent-branch-commit-proof.json`包含21个文件的前后blob ID、补丁SHA与字节相等判断；六份完整补丁留ignored供主会话review。因此没有发现这三个branch保有独立未合产品delta。删除前仍保精确ref或bundle；不因当前文件被后继改版就恢复这些旧全文。

`stash@{0}: On main: codex-incremental-sync-preserve-noting-spec`含07四行，必须保留。未把stash apply到任何树；它可能与debug规格重复，后续先读差异再决定是否另归档，用户明确要求保留时不drop。

### 独立前端仓库附带发现（不计入本仓清理）

为防误删签名，顺带只读取得它有4树：根`hermes-secretary-web`在`codex/force-completion-20261031`，另`-web-clarify`、`-web-toast`（占main）、`-web-visual-design`。这属于另一个Git common dir，不在本次主会话明确“本仓旧worktree及分支”的删除名单。根有untracked .DS_Store；不能据本报告推断另外三树dirty已合。若用户“所有”也要求前端，需对这个仓库另做同等级差异／签名／运行证据审计，不能用本仓ancestor结论清它们。

## 建议执行顺序与具体命令

以下是主会话后续执行建议，**本审计未执行**。无需再开新worktree；使用现有本轮实施树完成集成。

1. 在原根ignored建立 `.hermes-dev/worktree-retained-20261031/<原树名>/`。先保存所有旧树tracked完整binary patch、untracked源文件、refs／stash清单及原始manifest；审计中的副本只覆盖旧dirty，不代替完整证据归档。每树`.hermes-dev`使用保留软链且不跟随的复制／同卷移动，禁止`rsync -L`、禁止`--delete`。可用：

   ```bash
   git -C "$source_tree" diff --binary HEAD > "$archive_tree/tracked.patch"
   git -C "$source_tree" ls-files --others --exclude-standard -z > "$archive_tree/untracked.paths0"
   rsync -a "$source_tree/.hermes-dev/" "$archive_tree/.hermes-dev/"
   ```

   `source_tree`／`archive_tree`均需设为已核准的绝对单树路径；路径清单随后按NUL安全逐文件复制untracked。生成源／目标普通文件SHA、相对路径、模式及软链目标清单，核一致后才能移除源。`.venv`软链只记录，不复制其目标。私有归档根0700，文件权限保持；归档不入Git、不上传。

2. 亲审并语义整合原根长期文档（上表），先把当前实际07／README／AGENTS与历史讨论区分；处理web-release手动debug包以及两个历史报告附录，必要定向验证。不能执行`git add .`把旧树全部dirty一起提交。最终待集成修改落现有实施分支，按规则每次commit自动push；保留旧dirty快照到明确完成接收。
3. 本轮产品／文档及旧包处理收敛后，做范围内必要检查／门禁／提交。先合入origin/main后再切原目录。main目前在web-release签出，须在其所有旧dirty已被接收或明确归档、不再承载独立未完成工作的前提下，移除该附加树以释放main：

   ```bash
   git -C /Users/edgar/code/hermes-secretary worktree remove --force /Users/edgar/code/hermes-secretary-web-release
   ```

   `--force`只用于已经逐项处理且归档核验过的已知dirty／ignored；不是当前可直接执行的删除许可。任何新增dirty／进程依赖均暂停重审。
4. 原目录有已review的长期dirty，即使已把其内容整合到实施分支，也需先存最终原件／patch并复核相同内容已被接收，然后按明确文件清单恢复旧HEAD、移出已经接收的三份untracked原件。不可`git clean -fdx`、不可整树reset、不可删除原根ignored。原目录干净后：

   ```bash
   git -C /Users/edgar/code/hermes-secretary switch main
   git -C /Users/edgar/code/hermes-secretary merge --ff-only origin/main
   ```

   本轮提交尚未合origin/main时，主会话先在最新main按已授权流程合最终功能分支并push；如果采用`--no-ff --no-commit`，三核心保护及人工职责吸收按AGENTS，不能套`--theirs`。原根最终应为该集成后main，不是c07旧基准。
5. 证据归档核验完即可逐树移除其余旧树：`-idle-noting-owner`、`-incremental-remediation`、`-incremental-sync`、`-noting-chain`。本轮树在报告／证据已收进原根、所有工作落Git且原目录main核验后最后移除。操作前重跑ps／lsof并复查git status；不停止用户服务，不动原根cwd。
6. `git worktree prune --dry-run --verbose`本次仅显示不存在baseline登记及`.git/worktrees/.DS_Store`。收尾再看dry-run然后`git worktree prune --verbose`清无效登记；不是删除实体目录的替代命令。
7. 本地merged分支用`git branch -d <明确列表>`逐个清；三个patch-equivalent非ancestor分支需先保精确SHA／bundle，核当前`git cherry`仍为`-`后才考虑`git branch -D <单一分支>`。不要为了让`-d`成功而把历史旧产品强行merge，也不删镜像／stash／remote refs。无须强推、fetch、merge外部未知变化。
8. 最终只读验：`git worktree list --porcelain`只剩原目录main；`git status --short`无tracked／普通untracked未处理；`git rev-parse HEAD main origin/main`一致；`.venv/bin/python --version`及真实目标软链存在；本轮／旧验收证据SHA／文件清单一致；运行用户Profile／同步端点未变。写operations-log实际清理回执，CLAUDE留当前结果，不能把本预案写成已执行。

## 证据入口与限制

明细根：`.hermes-dev/evidence-recovery-20261031/worktree-audit/`。

- `inventory.json`：逐树HEAD／branch／祖先／ahead-behind／每个dirty字节SHA与main相等性、ignored目录体积、深3层软链。首轮status解析的首条空格问题已修正，最终JSON与下述副本manifest为准。
- `<树名>/{status,ignored,head-diff,main-diff,dirty-vs-main,independent-commits,main-new-commits}.txt/patch`：完整Git输出；`main-diff`大量删除只是旧HEAD落后，不是待删除产品清单。
- `<树名>/dirty-files/`及`dirty-copy-manifest.json`：旧树所有普通dirty源文件可审副本，含untracked代码／文档；未复制正在实施的本轮产品文件。
- `idle-integration-comparison.json`：14文件与接收提交的独立逐字比较。
- `ignored-top-sizes.json`、各树`data-config-paths.json`：体积及可能有私有内容的数据／配置路径元数据。
- `processes.txt`、`cwd.txt`、`open-files-hermes.txt`、`mutagen.txt`、两个`launchagent-*.plist`：只读运行依赖快照；原始全进程清单／打开文件在ignored中，不入公共报告。
- `all-local-branch-audit.json`记录全部15个本地refs的祖先／领先落后／git cherry结果；`equivalent-branch-commit-proof.json`及6份完整patch记录非ancestor分支的精确整合证明。
- `local-branches.txt`、`stash.txt`、`stash-stat.txt`、`worktree-prune-dry-run.txt`：本地引用与无效登记。

没有跑产品测试，没有改Git index／refs，没有fetch、部署、真实模型请求、UI、云端读写或服务管理。当前实施树和进程均可能继续变化，因此删除前必须复核；“可以归档后清理”不等于本报告已删除，也不等于独立debug包已被现版验收。
