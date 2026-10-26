# C13–C14 Compression History 只读接线核查

## 确切结论

**存在正式接线缺口，需要产品修改后才能关闭C14。** 现有`include_auxiliary=true`不能使原生压缩产生的Compression Message进入History工具：纯压缩载体被旧History Foreground去掉；混合载体只剩真人live view。Framework/Notebook的可信系统载体仍可显式读取；当前未发现model_only/human_only/hidden/Prelude泄漏。

不是说任意一条名为compression的普通system消息都读不到：若它不被native识别为handoff，仍可能按普通消息读取。反例针对真正由`archive_and_compact`持久化、带`_compressed_summary`与正式summary/end marker的原生上下文载体。

本任务没有改产品、原compressor、既有测试、Prompt、生产数据或凭据，也没有模型调用/提交。k3.1-pro样本未被本次调查改变。

## 冻结依据与代码链

07最新C13–C14明确：默认只真人/Assistant；显式独立辅助开关允许系统载体，system包括Compression Message与其它进入模型可见上下文的系统部分。旧07§5/02/04的默认History去scaffold不能用来否定这次新增显式辅助范围。

1. `hermes_state_conversation_history.py:191–195`的HistoryPaths固定调用`db.get_history_foreground_conn`；无论辅助开关值是什么，都只取得同一份旧History投影。
2. `hermes_state_secretary_foreground.py:243–261`识别native handoff；`full=False`对pure直接return None，mixed只保live content。`get_history_foreground_conn:311–312`固定full=False。因此来源富集与semantic role发生前，Compression部分已不可达。
3. 原native `split_user_originated_turn`（`agent/context_compressor.py:5851`）确实能拆出handoff与live；纯summary有handoff无live，混合有两部分；它没有失去识别能力。`_strip_context_summary_handoff_message:4674`按既有merged delimiter/end marker提取真人片段。无需修改compressor。
4. `_candidate_public`在`paths.winner(ref,uid)`缺失时直接排候选，不标unverified；所以pure压缩实际存在且FTS命中时，Search仍可成功0条并声称complete=true。Get Meta无include也会完整0条。Read按同一rows找不到锚点报source_unavailable。仅给classifier加Compression识别无法修复已经被上游删除的内容。
5. `HistoryPaths._by_uid:210`一UID一row，`_collect_search:579`按(ref,uid)去重；若直接把Full双投影塞进来，mixed同UID的compaction/user两部分还会覆盖/折叠，不是改一个开关就能完备。

## 实际SessionDB反例与结果

反例调用正式registry handler，构造隔离SessionDB并用真正`archive_and_compact`写入native载体；以`db._conn.total_changes`验证每轮观察无写入。没有mock History/Foreground或查询器。

| 场景 | 实际观察 | 判定 |
|---|---|---|
| pure压缩载体，当前合法path，FTS含purecompressionneedle | GetMeta(aux=true,roles=system)为returned=0/complete=true；Search同样0/complete=true；无锚Read system为0；锚点aux Read为source_unavailable；Full内部确有compaction节点；默认History仍可读原真人 | C14缺口，C13默认旧行为保持 |
| mixed summary+live同UID，经native compaction复制 | 所有system模式0；锚点aux Read仅role=user、content是真人live；Full内部同UID有compaction与user_message两个投影 | C14系统部分不可达；真人winner/slice保持 |
| framework与Notebook，display_kind=process_complete+可信origin | GetMeta/Search/无锚Read显式system均返回两条，role=system；默认Read只真人 | 正式辅助接线有效，不是所有system都失效 |
| human_only/model_only/hidden及root Prelude | 三个隐藏UID锚点aux Read均source_unavailable；辅助Search零隐藏结果；Prelude搜索不命中且结果不含root文案 | 当前边界保持；修复时必须继续保护 |

执行：

```bash
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/secretary/test_history_compression_review_evidence.py -q
```

结果：**3个反例测试通过，1.1秒**。这里的“通过”表示当前缺口被稳定复现，不表示C14验收通过。原日志`.hermes-dev/noting-chain-20261027/review-evidence/history-compression-review.log`；完整合成输入/输出快照为本目录`.hermes-dev/noting-chain-20261027/review-evidence/history-compression-observations.json`。

临时反例源码运行后移至本目录`.hermes-dev/noting-chain-20261027/review-evidence/history-compression-review-evidence.py`，避免以“当前bug就是正确结果”的断言进入正式测试集合。复现时先将该证据文件复制回命令中的原临时测试路径（测试conftest会隔离Home/运行环境），运行后移除该临时复制件。该文件仅证据，不能作为正式接受测试直接提交。

## 最小接线建议（尚未实施）

1. 保持`get_history_foreground_conn`默认行为以及所有现有非辅助调用；在state Foreground侧新增**显式选择的History辅助消息投影**，复用同一合法raw path、winner、branch overrides/exclusions、active/compacted判据与native split，不在tools重新扫描/复制另一套路径算法。
2. 辅助投影只补已存在且可被模型看到的Compression部分，内部给它可信`origin=framework/producer=compaction`语义；原真人live投影继续沿当前权威winner。不得给Summary正文造新UID或按正文猜普通用户身份。
3. **不直接调用`get_full_foreground_conn`作为工具来源，也不直接改full=True。** 前者含Prelude/Snapshot审计；后者native full分支跳过model_only过滤，并有carrier_sources及同UID双投影特殊语义。即使仅筛kind=message也不足以阻止model_only泄漏。新辅助投影须继续执行原model_only/human_only/隐藏约束；只有经native证明的compaction scaffold可按明确辅助语义进入，不能顺带开放所有display_kind=hidden记录。
4. mixed同UID必须先收敛内部读模型：推荐保留“一个逻辑Message Identity，多个有类型的内容part”，由一个正式owner集中管理；候选映射、角色过滤、完整性计数、锚点Read与邻居使用同一分组逻辑。Get Meta仍严格四字段，可按已选语义角色投影出相应part；Read以同一identity能取所需系统/真人部分。不建议仅把列表变两row却继续使用现有_by_uid/seen，否则只会随机丢一部分。
5. 这里有一个需主会话明确的接口细节：mixed的同一message_identity没有独立projection selector，且锚点Read按保留契约拒绝roles。若一次aux Read返回同identity的两类内容，需统一其表示及邻居/容量计数；若选择返回单一组合content，需明确role与原真人读取的关系。应在现有Schema/handler契约内集中落实，不能让Search和Read各取一个互不兼容的投影。本调查只指出所需接线，不替主会话做产品决定。
6. 修复后把本次反例改为“显式system可读/默认不变”的正式接受测试，并增mixed UID、branch继承、rewind、角色过滤/闭区间、分页、200容量及隐藏边界对照。当前已有效的Framework/Notebook回归证据可复用。

优先级建议：范围内C14阻断，进入独立Verification前关闭。纯压缩可读只是第一步，mixed同UID正式选择/读取机制必须一起核对，否则无法称所有已确认system范围已接线。

## 后续实施状态

上述只读发现保留为当时证据。主会话已授权实施；当前修复、201项正式定向通过、质量检查与基线15项失败对照，见同目录`history.md`第9节。不能再把本报告的修复前结果当作当前实现状态。

原始临时证据的受限副本统一在ignored `.hermes-dev/noting-chain-20261027/review-evidence/`；报告中历史路径对应运行当时，副本同名。
