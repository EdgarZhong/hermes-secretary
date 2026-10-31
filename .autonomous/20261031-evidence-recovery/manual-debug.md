# D3 · 遗留单次 manual Noting 调试接口移植

状态：实现及本地定向验证完成，待主会话亲审、全轮独立门禁与发布。无commit／push、无生产操作、无工作树清理。遵循用户最新“不用真实模型验证”，真实模型请求为0。

## 1. 对应条款与依据

- 本轮snapshot-index E10/E11，07 §12.3（当前2174–2177行）；原2026-10-25已授权dirty包，只接收单次新的manual Noting，不替代失败child恢复。
- 保留原生Main／Profile／Conversation／route、完整工具面冻结、manual admission／真实child／Commit Gate；不额外Compact、不改自动Noting参与／Idle配置、忙时不抢Main租约、不绕原生压缩锁，回执来自真实child提交见证。
- 现行取消／替代／Force及Note资格／投递契约优先；没有恢复旧“Noting成功立即在当前timeline追加FM”的流程。
- 已读executing-plans、autonomous-run子Agent交接、本轮index／plan／baseline、当前AGENTS／CLAUDE、分区参考及相关原生上下游。plan／07／根核心文档由主会话维护，本Agent仅写本报告。

## 2. 实际变更与白名单

仅修改以下7个产品／测试文件，完整SHA及binary patch在ignored证据中：

| 文件 | 变化 |
|---|---|
| `tui_gateway/noting_debug.py`（新增，234行） | 单次启动、状态查询、root session audit及幂等、短持原生Main lease、原生后台resume／准备／冻结／派发和真实child回执 |
| `tui_gateway/methods_noting_recovery.py` | 只新增secretary.noting_start／secretary.noting_state两个profile-scoped注册，旧恢复入口保持 |
| `tui_gateway/contracts/noting_recovery.py` | 新Params／Result；profile、conversation_ref、request_id必填，拒空／超长／额外参数；status包含当前cancelled／superseded |
| `tui_gateway/server.py` | 仅_LONG_HANDLERS加入secretary.noting_start，一行窄修改 |
| `apps/shared/src/gateway-contract.generated.ts` | 按正式生成器更新，增21行 |
| `apps/shared/src/gateway-contract.openrpc.json` | 同步正式生成器更新，增164行 |
| `tests/tui_gateway/test_manual_noting_debug.py`（新增，约582行） | 原17项适配当前生命周期，追加并发／故障／租约／取消替代／Note原生成功边界及真实工具落库等共34项 |

没有复制旧server／methods全文覆盖当前实现，没有修改D1/D2的Notebook／Prompt／工具权限／压缩实现、依赖或配置。没有新增调度器、执行器、Schema表或API层级。

## 3. 正式路径与关键适配

`已认证RPC → profile-scoped → 目标Profile SessionDB → resolve_conversation_route → 原生compression-only ancestry root审计 → exact Main Turn lease → 原生scheduler_host.resume_session(exact_session=True) → _sess正常builder → context cache同步／当前Main root及tools准备 → canonical当前历史／attach → prepare_joint_noting(trigger=manual, operation_id) → 原生freeze／admission／spawn → 真实child工具循环 → 原Commit Gate／child commit见证 → state回执`。

1. **后台resume及route。** 复用现有host-only原生resume，不附着／替换调用方transport，不触发普通resume的自动继续Main任务。冷态真实_make_agent builder、当前存储route、root与完整tools继承在测试中执行；没有自行创建另一个Agent执行器。显式launch Profile也使用实际host Home。
2. **上下文与锁序。** `_prepare_parent`只临时借Main holder同步其正常缓存边界，准备最新持久原文并原生attach；不跨attach持有history_lock，避免旧包已记录的重入自锁。最终history锁内只短读sessions注册身份，随后释放全局sessions锁，再进入原生Framework/context准备；不持全局sessions锁等待原生Noting锁。原生入口继续检查准确Main owner／关闭状态及能力。
3. **租约。** 仍用原生同Conversation的Main Turn lease，busy／已有压缩返回4010。准备期间借既有periodic_scheduler每60秒刷新300秒租约，callback和最终释放用短锁串行；取消定时器后才释放。刷新是同一个DB事务内的exact holder＋expires_at CAS，不复活已过期准备租约；准备后、freeze前再次核lease及原生compression lock。失效时不派child，不删除继任者租约。
4. **幂等与compaction。** operation由Conversation ref＋request_id派生；audit存在compression-only root，跨原生物理轮转仍定位同一root。不同Profile用不同DB；显式branch具有新ref／新root，即使复制model_config也不能命中父operation。audit字典合并与model_config写入在一个原生DB事务，保留其它配置字段。不同请求竞争准备阶段不抢占，相同已保留请求返回同queued事实。
5. **接受／提交原子性。** 把operation_id传入现行原生admission。queued audit先存，实际admission durably绑定operation后才dispatch；最终audit写入失败或进程在两步之间中断，后续state从原生admission的operation_id找回真实child，不重复起任务。初始audit保存／定时器启动失败未接受，不创建child并释放租约；存储异常走明确5010，提示查询同request。
6. **真实回执。** status读当前child记录；committed／snapshot_id只读该child的`_secretary_noting_commit`并核admission一致，不把排队、SDK结束或superseded审计Snapshot当提交。注册先于presence的短交接窗口有本地completion／准备lease时报告queued，不误报interrupted；真正无任务／无准备见证才报告interrupted。原生取消、替代、启动失败及旧同Anchor去重状态按现有机制返回。
7. **Note保持现行语义。** 新manual任务本身不Compact、不在当前区间强行注入FM。SDK受控真实child提交后，当前interval Note资格为false；随后真实原生压缩成功，现有发布接缝才为该Snapshot落一条Note receipt，再检查不重复。没有新增Note资格例外，也不改Main权限或Force占用规则。

## 4. 验证结果与精确版本

本包测试使用官方PM `.venv` Python3.14.7、macOS arm64，全部由canonical `scripts/run_tests.sh`执行，`HERMES_TEST_FILE_RETRIES=0`。外部SDK和摘要返回受控；真实RPC注册／参数结果校验、Profile DB、原生builder、AIAgent child循环、工具执行、不可变Notebook／Snapshot、lease、native compaction发布及Note资格均执行。fixture cwd为Git root外临时目录；没有网络模型、真实用户正文或生产库。

本包接入起始集成HEAD为`a4681a1b25d0ce6d2d3856a167a63b8ecaa884db`。最终七文件SHA见`source-manifest.json`，不以会并行变化的分支名替代精确产品指纹。

| 日志 | 结果与适用含义 |
|---|---|
| `final-current.log` | 最终3文件41 passed／0 failed，23.6秒：manual debug34＋既有Noting恢复6＋生成文件逐字校验1；不含下述独立基线catalog失败 |
| `checks-final.log` | 最终临时index candidate十项冻结检查全部通过；health范围36文件（含当前HEAD已集成本轮代码）0 blocking／0 advisory；未修改真实index |
| `baseline-catalog.log` | 从上述HEAD完整git archive导出，在独立源码cwd用同canonical runner，仅跑catalog：1 failed，1.13秒；唯一失败为既有孤立事件review.summary，与新方法无关 |
| `initial.log` | 首次适配时生成精确校验及16项新入口通过；旧测试误要求立即FM失败，另catalog基线失败。未为旧断言修改Note契约 |
| `expanded.log` | 中间24项通过／3项失败：首回执child可为null的异步测试预期、以及两个注入存储异常缺明确RPC错误封套；已分别调整为真实异步事实、补5010及幂等恢复后定向关闭 |
| `final-rpc.log`、`native-note.log` | 中间27／29项及既有恢复通过，验证租约／取消替代及真实native Note边界；后继新增场景以final-current为准，不把次数累计成新覆盖 |
| `final-directed.log`、`final-expanded.log` | 中间31／33项新入口及既有恢复／生成通过；最终真实工具落库测试初稿误用不存在的snapshot_view，失败保留于final.log，改用正式notebook_show后tool-write.log及final-current已关闭 |

34项覆盖：原生冷／暖builder；一child及真实commit；固定父root/tools；真实notebook_create→finish→Main notebook_show读回新证据描述；同请求running重试、准备阶段并发同键复用／异键4010；跨compaction rotation幂等／branch隔离；原生Main busy、开始前及准备中新增compression lock；租约周期刷新／过期被继任／调度器启动失败；全局与Conversation参与关闭、能力不足、Force占用；未知／错Profile、参数拒绝；child启动／执行失败、owner detached；queued audit失败／dispatch后最终audit失败；原生cancelled／superseded不冒称commit；注册presence交接；旧completed admission不冒充fresh；真实原生成功压缩后的唯一Note receipt。

生成契约完整目录没有全绿：catalog本来就因review.summary orphan失败。本包没有修改该无关事件或检查器。最终命令用`-k 'not test_catalog_covers_the_whole_wire'`只排除这个已在完整当前HEAD复现的独立基线用例；它仍在证据／限制中明确列出，未关闭／降低项目门禁。

## 5. 缺口与限制

- 未真实模型验证，按用户最新明确要求不再安排；上述controlled SDK不冒称模型自然行为。
- 未在Linux目标机运行本包、未启动真实生产manual Noting、未上线、未做浏览器／APK或渠道投递验证。Linux与最终部署由主会话统一安排；能力上线不等于获授权补跑生产任务。
- 当前HEAD完整catalog已有review.summary孤立事件失败，只完成范围隔离与同基线反证，未修无关能力。
- 没有发现需改变既定产品／权限／完成条件的冲突。原包“立即FM”的测试已经被现行Note契约替代；这一点不是新增产品豁免。

## 6. 接口影响

新增`secretary.noting_start`及只读`secretary.noting_state`，两者必填profile／conversation_ref／request_id，长度及空白校验、额外参数拒绝由正式schema和入口保证。start异步返回opaque operation／admission／nullable child、状态、真实committed／nullable snapshot；查询可先于请求，返回not_found，不起模型／任务。状态兼容当前cancelled／superseded，queued的child_id允许为null；不在start排队回执中保证已经有child。旧noting_recover／recovery_state的参数／返回／执行路径保持。只新增manual start到_LONG_HANDLERS，状态查询沿现有普通RPC读取。

未新增前端UI、SDK／Provider路由、用户配置或生产写入默认行为；全局未调用该新接口时无新增行为。

## 7. 建议后续

主会话亲读七文件diff、租约／audit事务及正式owner接线，复用`final-current.log`与`checks-final.log`的同SHA证据；将E11和07当前接口语义一并纳入冻结版本／全轮Verification及Validation。旧main工作区原包在本轮最终提交接收并证据归档后才能清树；本报告不代替主会话最终“合净”判定。生产manual补跑不属于本轮收尾动作，不自行调用。

证据：`.hermes-dev/evidence-recovery-20261031/manual-debug/`内`summary.json`、`source-manifest.json`、`manual-debug.patch`、全部日志及精确HEAD源码baseline导出。公开报告只含机制与测试摘要，不含用户原文、配置／凭据或私有wire。
