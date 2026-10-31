# D1 · 证据组描述数据与工具交接

状态：产品代码稳定，交主会话review；未commit、未生产写入、未部署。未改D2的Prompt、专属Prompt oracle、共享plan或核心文档。真实模型与双门禁由主会话集中进行。

## 1. 对应条款

- 冻结索引E01／E02／E04／E06、07顶部2026-10-31 A：组描述补充条目description，仅概括本组消息；描述和完整UID共同覆盖本Task槽，跨Task追加，旧节点不可改，Evidence time仅从UID派生。
- 保留07来源链条款及白板C3／C6／C7、K6、N1／N3：原文事实源，Candidate direct与refs二选一，源条目现行读取；Main只读、Noting独占写、不可变版本及原子Snapshot；全部模型投影与工具回执一致。
- E06旧组只读兼容：缺失描述显式null，不猜造、不重跑旧Noting、不转换生产历史。

## 2. 实际变更

八个产品文件：`secretary/notebook_contract.py`、`notebook_model.py`、`notebook_items.py`、`notebook_store.py`、`notebook_render.py`、`noting_contract.py`、`noting_tools.py`、`noting_recovery_sources.py`。

- 输入新增可选`source_description:string`；持久／投影新增`provenance_descriptions:(string|null)[]`。直接来源逐索引对应原`provenance:UID[][]`及`evidence_time`，没有替换原数组契约，没有新增数据库列或迁移。
- canonical读取仅为旧缺字段提供等长null数组；原不可变JSON不改。严格检查组数、描述类型和非空文本，不根据UID／时间／当前条目推断旧描述。
- 同Task修改同时覆盖UID、描述及UID派生时间；后续Task追加完整节点。描述纳入来源前缀及claim继承证明，不能借相同UID转借旧支持；已提交Snapshot引用的末节点也不能通过重用trusted Task ID替换。自动archive／relations清理保留原组。
- 正式Noting初始化启用`require_source_description=True`：新建或真实修改direct组须非空描述；只提供描述、缺UID、空描述、描述用于refs均拒绝。无真实属性变化仍不产生来源节点／版本。没有句子解析或硬字符截断。
- trusted Python API保留省略参数和默认行为；缺描述产生null，而非有效新描述。`require_source_description`为内部可选默认false参数，模型不能传入或关闭。
- `noting_recovery_sources`是必要只读接缝：历史初始control及成功receipt同样canonical化缺字段，仍按完整不可变内容／Task owner精确匹配，不放宽历史继承或重放旧任务。
- 更新相关旧测试输入。两处很旧的Notebook测试仍使用已退役的identity／四旧分区接口，改为当前UID链／四现行分区。三个投影用例沿现已上线的后续压缩区间实际投递，不再假定同区间立即收到Note。

## 3. 正式路径

`notebook_create/update`固定Schema → `_notebook_mutation`原权限／local／任务门禁 → `initialize_notebook_work`绑定严格Store → `NotebookWorkingState`组级同步更新 → `NotebookStore._insert_version_conn`当前路径复核及时间派生 → INSERT-only item → 原Snapshot事务精确校验 → Main `notebook_show`／Noting working show与control／`render_notebook`及真正Note Framework投递。

失败后状态仅在成功持久化后替换；正式工具的SQLite失败回执沿原`temporarily_unavailable`。Candidate refs没有直接组／描述槽，通过`notebook_refs`读取完整当前源条目；既有引用时间投影保持。

## 4. 验证结果与版本

环境为真实macOS、官方PM `.venv`软链接、Python3.14.7、pytest9.1.1；`uv.lock`与主仓SHA256均`2bc4db483e9cba927cd7147f9ccbb09635f85bb3f1f36d6e9d51d06b65d1c67e`。所有Python测试都通过`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh`逐文件隔离；没有把库内目录用作真实模型Profile.cwd。

冻结依据`8b31d986dca870c8656dde2b69826ad65dc24e65`。交回时HEAD为`a4681a1b25d0ce6d2d3856a167a63b8ecaa884db`加D1／D2未提交变更；不能把HEAD单独冒称包含产品实现。D1八文件最终SHA及diff位于`.hermes-dev/evidence-recovery-20261031/data/{product-sha256.txt,product.diff}`。

证据根为`.hermes-dev/evidence-recovery-20261031/data/`：

| 适用证据 | 结果／耗时 | 日志 |
|---|---|---|
| 最终10文件：新描述23项、旧组／legacy control读取、真实插入后回滚、不可变继承／重启、Main／Noting／control／实际Framework、恢复、UID／投影／DB／Main工具 | 151通过，18.7秒 | `targeted-final.log` |
| Candidate全部目标的direct／refs／切换／无效来源及实际settlement链 | 62通过，24.9秒 | `candidate-final.log` |
| 最终来源数组32项、来源继承23项、Store8项、Task恢复4项、done120项、SDK wire7项、Noting child38项、时间投影9项 | 每文件通过；整次另一个旧candidate文件缺字段而人工中止，不能把整次标绿 | `targeted-fourth.log`；其中专属描述17项后由最终23项覆盖 |
| 固定权限／直接invoke／正式Loop／所有六工具 | 86通过，85.5秒 | `targeted-third.log`中该完整文件；之后仅收紧已提交来源替换，相关最终反例另由23项及来源数组覆盖 |
| 动态工具19、source visibility5、joint lifecycle12、正式wiring52 | 每文件通过 | `targeted-third.log`相应完整文件 |
| R3 child当前契约适用子集 | 44通过，6.7秒 | `r3-current-compatible.log` |
| 冻结基线对照 | 下述同样12项失败，44项未选；6.34秒 | `baseline-control.log` |
| 开发health／ruff及whitespace | 0 blocking／0 advisory；diff check通过 | `check-final.log`；主会话仍须最终staged冻结检查 |

初次日志如实保留：`targeted-first`有测试调用control函数方式错误，已修；`targeted-second`有旧工具测试接口与缺描述输入，已修；`targeted-third`中4个旧same-array Prompt oracle及旧同区间Framework假设已在后续wire／投影复验通过，selector请求数由D2独占修复并验证。`targeted-fourth`的candidate旧provider helper缺描述造成连续拒绝，我仅终止自己PID67907；runner输出的SIGTERM不是产品native fault。补齐其受控脚本输入后，独立`candidate-final`全62项通过。

## 5. 缺口

- R3 child整文件仍有12项既存失败：9项仍假定本区间立即注入Note，另3项查询旧registration／owner表。已在另建的只读detached基线工作区、原冻结代码与原测试准确复现相同12项，日志保留；临时工作区已移除。本包不改已上线生命周期／旧审计视图来迁就旧oracle，也不将这些失败签成通过。
- 没有执行真实模型，不能由非空字符串／受控脚本证明每个描述的语义仅含本组及区分提出／接受／完成。主会话真实样本及独立Validation仍需人工核。
- 未运行本轮最终staged冻结十检查、真实Linux或生产验收；未更新旧生产组、重跑旧Noting或清生产缓存。

## 6. 接口影响

- 已与D2及主会话一次协调最终输入`source_description`及输出`provenance_descriptions`。Schema字段保持可选，以兼容refs及trusted旧调用；模型direct新建／实改分支由任务绑定的runtime强制非空。null仅代表旧组缺失，不满足新模型写入要求。
- 不改变UID去重、来源授权、Candidate二选一、时间优先级、Main只读、Snapshot提交、cache prefix或FM生命周期。描述不是新来源权限。
- 未修改`agent/system_prompt.py`／`secretary/noting_prompts.py`，也未碰D2的history tuning／R20／request protocol oracle；共享测试helper的补描述仅在本包数据相关文件。

## 7. 建议后续

主会话按八产品文件亲审正式接线，使用SHA绑定已稳定代码及真实模型样本，重点核描述只取本组而非复制当前entry，并核保留旧null。统一最终检查、阶段提交及两门禁；12项基线旧oracle作为已有测试债记录，不改本轮已确认生命周期。发布时沿正常恢复边界换Prompt／Schema，不转换旧Notebook。
