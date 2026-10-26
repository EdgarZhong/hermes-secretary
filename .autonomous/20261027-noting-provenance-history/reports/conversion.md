# 一次性Notebook转换交接

状态：按Notebook最终语义接口完成manifest重建及一轮副本／故障演练，整包待主会话review。生产未转换、未停服、未提交。本报告不含真实正文、凭据或真实Message UID清单。

## 1. 条款与范围

对应本轮C01、C04–08、C20和07顶部一次性旧数据转换授权。仅Alex核准置顶Conversation的51个历史item版本（59–109）变换来源表示。8个Snapshot、当前pointer、当前29个引用、所有条目的身份、正文、fields、done、关系、建议、创建／更新／处理时间、archived列、source_basis_id全部保持。其它Conversation／Profile、原消息、Schedule、绑定及配置不变。不建设产品兼容层／通用迁移，不触发Noting重放。

## 2. 实际文件与手选证据策略

所有运行脚本、数据及manifest在ignored `.hermes-dev/noting-chain-20261027/production/`，目录0700、文件0600：

| 文件 | 用途 |
|---|---|
| `build_conversion.py` | 私有人工证据选择表与manifest生成器；仅从只读副本读取，不联网模型 |
| `conversion-manifest.json` | 核准目标、51个旧／新payload哈希和新payload、真实Task owner、精确来源原文哈希／原timestamp证明 |
| `convert_notebook_once.py` | 固定manifest哈希的一次性preview／apply／verify／副本dry-run入口 |
| `rehearse_conversion.py` | 本地事务失败回滚、重复执行拒绝、关闭重开只读验证 |
| `state-before.db(.gz)` | 原生产只读backup的私有本地副本 |
| `state-final.db`、`state-final-rollback.db`（此前初演练副本亦保留） | 本地演练副本，不能替换生产库 |
| `legal-path.json`、既有两份inventory/meta | 正式Foreground合法路径及人工选择依据，含隐私，只留本机受限目录 |
| `preview-result.json`、`dryrun-result.json`、`rehearsal-result.json` | 不含正文的机读结果 |

按每个历史版本当时的正文逐条选择最少证据：真人用户原消息优先，具体Assistant回复补充；只有已注册排期、实际发送回执或咨询文档原始读取事实不能由前两者完整证明时才选相应工具消息。没有把旧大范围内连续全部消息机械塞进UID。

真实admissions／children时间窗口能唯一归属全部51个历史版本，采用正式owner `str(admission_id)`，不是自造迁移owner。同Task内纠错／补充保同槽；后Task继承旧槽并追加自己的新证据，未以当前正文反向改写历史正文。原有必要精确identities保留在其首次引入Task，未误归到最后Task。refs Candidate保持provenance／provenance_tasks／持久evidence_time均为空数组，仍由引用项派生可读时间。

81个不同UID，31个条目×Task独立节点、各版本链内合计55次节点出现及180次UID引用；单槽1–8个UID。真实选取表及UID只在私有脚本／manifest，不复制到报告。

## 3. 正式机制校验

使用当前正式代码的SessionDB只读模式、Foreground合法路径、`_source_validator_conn`、`item_entry`、`NotebookWorkingState._validate_entry`、`validate_provenance_transition`、`hydrate_snapshot_conn`及`validate_snapshot_state_conn`。所有51版本逐项新shape校验、全部直接来源均在允许路径；每槽时间由正式`derive_evidence_time`从原timestamp派生并逐项相等。

全部8个Snapshot包含空Snapshot及历史／当前Snapshot，均经正式hydrate和Snapshot校验；另覆盖`readable_notebook_state`、`show_notebook`、`model_notebook_data`、`model_notebook_view`、人类／模型`render_notebook`，内部owner与旧来源字段不进公开投影。原source_basis的同lineage及前缀许可沿正式校验保留。

## 4. 演练结果

初次apply演练因本脚本缺少文本投影所需created_at而在提交前拒绝，确认未发生部分提交；补齐真实Snapshot投影参数后通过。后继补source proof及所有投影验证期间，遇到Notebook并行接口切换的瞬时ImportError，未运行生产／未提交写入。最终接口稳定后重建manifest哈希未变，新建副本完整apply后关闭重开只读复验通过；另在原结构副本于提交前注入故障，全部表／schema／51个旧payload保持原指纹；对已转换副本再apply明确拒绝。正式payload新shape、逐槽Evidence time、全部人类／模型投影及来源正文哈希均通过。

最终机读结果：51版本、8Snapshot、31个独立来源节点（版本内累计55次）、180次UID引用、81个不同UID；各历史Snapshot累计162个可见条目投影通过；integrity=ok，FK无违例。初次脚本参数失败和并行接口瞬时错误均保留在本节，不掩盖失败尝试。

| 固定对象 | SHA-256 |
|---|---|
| manifest | `9d7e0b907c91460b6fcb913e5e212739c5842c03f2c4bbf046bbd2592bc67951` |
| apply脚本 | `0aefaa07e575c1395effb7eeb16ce54e7b3e6d3d6d895ab6fb0fc1f2718f2838` |
| 51条目标旧rows | `4d5e8746a1abb8aa70aac96cf84e3c6813aef128fede1418575a130c8f237039` |
| 51条目标新rows | `645c77c15bdef5a5f55a79b378101583a0c6d35c46c850ff17f841ac1807f0d2` |
| 本地副本其它表／非目标item | `1230e19911c06693609d08d90758442c434e7d905c252b1f8d8b051687763373` |
| schema | `18cd745093463ff381c6fc989ff66e8d1ad5f2249b416d4337701bff4efd27f1` |

其它表指纹只代表本次副本时点，生产可有正常新消息／运行状态变化；正式事务前后应比较生产当时的其它表指纹，不能强制等于旧副本值。9个正式机制源码哈希锁在私有`mechanism-fingerprints.json`；本报告验证版本以该精确源码状态为准。执行者Conversion Agent，直接运行获授权私有演练脚本，未调用pytest／模型／生产写入口。环境及完整安全计数见私有execution-receipt。

## 5. 缺口与风险

旧宽时间范围没有保存“原Noting当时精确选了哪些消息”的事实，因此本次是对存留原消息的人工作证重建，不宣称恢复不存在的旧节点链。原日期、正文和旧来源范围原件都保存在私有原库及inventory，转换不伪造进展、修改日期或原始精确选择意图。

本任务不验证模型行为、UI、APK、服务启动或生产发布；这些归主会话及独立门禁。正式apply未运行；不能把本地演练视作生产已转换。

## 6. 接口与安全条件

`apply_conversion(db_path, manifest_path)` 返回安全计数、目标前／后指纹、未受影响数据及schema指纹。`preview_conversion`只读拒绝过时目标；`verify_conversion`只读验证新结构；`dry_run`使用SQLite backup到不存在的新本地路径，再对副本apply／重开verify。CLI apply还要求`--services-stopped`，函数调用由已授权发布编排负责停服条件，禁止Python `-O`关闭断言。

apply先`BEGIN IMMEDIATE`，核目标身份／pointer／8Snapshot／51条精确旧payload哈希，核所有非来源JSON结构相等，再暂移除item UPDATE INSERT-only触发器、更新精确51行、按原DDL恢复同名触发器。提交前正式全版本／全Snapshot校验，核其它所有表、非目标item及schema指纹完全相同，核数量、integrity、FK，任何异常rollback。无upsert／自动重跑或“已新结构则跳过”路径，重复执行明确拒绝。

生产消息可继续新增但不得打断现有Turn；停服后若目标发生任何变化导致哈希／pointer／计数不符，停止并重核，不更新白名单绕过。81个来源消息的原content哈希、role、timestamp也重核，不能用同UID不同正文借用旧证据。

## 7. 主会话接入停服发布

1. 亲审私有选择表、manifest和脚本；上表最终接口与演练指纹已锁定，只将脚本和manifest复制到正式机0700私有发布目录，文件0600，不入Git。
2. 按既有backend-only发布器完成自然空闲、三库备份、停服务及已审main快进。
3. 在已切到新正式代码的运行环境导入本脚本，调用`apply_conversion('/home/ubuntu/.hermes_profiles/Alex/state.db', manifest_path)`；保存无正文结果到受限发布日志。
4. apply返回后记录新的`expected_databases=databases()`，再启动并比较expected；只读`verify_conversion`和实际服务／目标数据验真由主会话完成。
5. 若事务内失败，库原样回滚；提交后发布失败保留现场，禁止自动恢复数据库。新来源结构不兼容旧代码，不可单独回源码；先核新写入／兼容性及权限再决定人工恢复，不能直接覆盖运行库。生产备份按最近两套完整三库收尾，本任务另生成的受限state只读证据副本需由主会话纳入清理，不冒充正式三库回滚点。
