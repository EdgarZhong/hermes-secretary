# C10-P 个人旧测试收口交回

状态：完成本包测试源码收口与本地证据，停止写入；未stage/commit，由主会话review和统一提交。没有生产代码改动、真实NM请求、模型调用或部署。

## 1. 条款

个人仓起点 `57d0abb854f4ae71207b85bf247afa446d5ac65e`；现行PHASE3 §1–7，重点§2–3/5–7的scope、Bundle原生生命周期、完成UID、整批egress与ACKprefix；§4.1及R3-010限定窄helper仅基本模拟。历史附录、旧完整HTTP正文写入、expected-sha、强制History成员验证与二层Bundle cache不继承。C9-S与共享Reminder fixture保持停写。

## 2. 变更

仅个人仓三文件：

- `nowledge-mem-hermes/personal_tests/test_personal.py`：真实公共host导入，移除永久agent/egress模块stub；所有临时库/安装/收据放ignored目录；Bundle每次native build hook读取，长opaque ID完整保留；真实SessionDB生成UID、原生发布compaction continuation后按同Ref/Thread只追加suffix；原有scope、offline、候选编码、失败不推进、restart、rewrite停止与隔离安装断言保留。
- `nowledge-mem-hermes/personal_tests/test_security.py`：真实SessionDB/规范UID通过当前completed History边界；只patch host egress函数观察调用，断言整个user/tool/assistant三行先脱敏再丢tool，原始输入不改，缺scrubber拒绝。数字配置与单Provider注册断言保留。
- 根`CLAUDE.md`：新增C10-P动态事实；旧P1/P2/P3首次交回区域标为历史记录，说明已由57d0abb接收。

原10项Metadata旧严格协议退出，改为2项**既有窄流程的基本模拟**：preview无I/O；metadata-only PATCH准确保留provenance与无关字段。没有恢复旧alias、skip/xfail、强制本地成员校验、完整Memory HTTP写入或通用CLI测试；不重复运行已有P2基本脚本。其余P1/P3新46用例未改未跑，既有endpoint/Space隔离等证据保持原范围。

## 3. 实际入口

插件目录带连字符，直接交pytest会在setup尝试按无package导入插件`__init__.py`，所有测试未进测试体。无需改生产包：在个人仓ignored `temp-r3-personal/evidence/c10-p/runner/` 建两测试源码symlink；`__file__.resolve()`仍指向真实源码，fixture ROOT正确，不复制源码、不加载conftest、不绕过canonical runner。

从个人仓执行的准确入口：

```bash
HERMES_PYTHON="/Users/edgar/code/hermes-secretary/.venv/bin/python" \
  /Users/edgar/code/hermes-secretary/scripts/run_tests.sh \
  "$PWD/temp-r3-personal/evidence/c10-p/runner/test_personal.py" \
  "$PWD/temp-r3-personal/evidence/c10-p/runner/test_security.py" \
  -q --tb=short --show-capture=no
```

链接指向对应`nowledge-mem-hermes/personal_tests/`源码。真实执行链为公开runner→独立pytest进程→实际个人Provider与公共SessionDB/History；网络边界仅FakeClient/Mock，不访问NM。测试库和receipts均在个人仓ignored `temp-r3-personal/`。

## 4. 执行证据

证据目录：个人仓 `temp-r3-personal/evidence/c10-p/`。

| 阶段 | 结果 / 日志 |
|---|---|
| 直接源码路径首轮 | 47项setup error，均未进入测试体；`initial.log`，不是产品失败或通过 |
| ignored链接取真实baseline | 32 PASS、15 FAIL；`baseline.log`，失败均旧契约 |
| 7项失败相关定向修复 | 4 PASS、3 FAIL；`repair.log`。3例实际断言已执行，cleanup时先删目录后DB.close导致失败；修fixture cleanup顺序 |
| 共享fixture变化后两文件 | **39 PASS、0 FAIL，1.3秒**；`shared-fixture-final.log`（personal35/security4）。真实host fixture影响两文件，因此此处一次共同复测，没有扩到新R3组 |
| Ruff / C901≤20 | `ruff.log`、`complexity.log`通过；未改规则或豁免 |
| 格式化与差异 | 两文件格式化前后AST相同；`format.log`及AST快照；`diff-check.log`为空通过 |

首次default Ruff还识别旧两文件保留的一行多statement等格式问题；仅对这两文件格式化，并将模糊`I`改为INSTALLER、动态导入实际host，最终通过。不为格式化重跑相同测试。无生产缺陷需要扩权。

## 5. 缺口

不含真实NM Memory/Thread/Space验证、真实模型/产品或云端部署，不宣称服务端去重/Metadata保管已验；本包不重跑P1/P3新46场景，不复验公共C9-H或C9-S。正式产品仍由唯一owner在round3执行。Provider根README未改，稳定入口是否要补canonical symlink示例由主会话结合最终测试SOP审定；没有引入第二测试runner或依赖配置。

## 6. 接口与manifest

没有生产接口变化。测试内`FakeClient`、`transcript`保留名称；新增`temporary_home()`仅供两测试共用，无conftest或生产导入。Fake上传仍要求明确ACK；canonical Main场景消费真实completed assistant UID；所有收据在临时owner home。

`manifest.json`固定三文件、日志hash与`c10-personal.patch`；个人HEAD仍57d0abb。交回时公共HEAD为`f304b42bbd6c45a62d1fded490f005bde019b23e`；公共仓源码未被本包修改，仅新增此报告。

## 7. 下一步

主会话亲自review两测试、个人CLAUDE与报告；确认退役用例映射和fixture范围后统一提交。两仓无本包stage/commit，C10-P已停止写入。独立门禁复用有效证据，不重复本包39或既有个人46场景；仅对后续实际相关变化定向补证。

## 8. V51 · Recall 日期输出修复（2026-10-17）

### 8.1 条款与版本

本包在历史 C10-P 后独立授权。个人起点／交回 HEAD `e1af6cc45ffbd53c930d1d2f14ab46858e966ecd`；冻结依据个人 `97078118` 的 PHASE3 现行 §2、§3.1–3.3（45–86行），公共 `d19018` 的 02 §5.6（1635–1637行）：可见绝对时间用秒精度和显式时区，内部值、来源语义和权限不改；完整 ID、JSON安全、指针预算、短 CJK、离线诚实行为保留。

### 8.2 实际变更

`_candidate_date` 是 created_at/updated_at 的唯一投影点：epoch（含小数／数字字符串）和有 offset ISO 复用公共 `hermes_time.format_timestamp`；合法 YYYY-MM-DD 原样保留，不伪造午夜／时区。None、bool、非有限数、越界epoch、naive datetime、坏日期视作不可得的可选日期，只省相应字段，保留候选及其他正常日期，不使一次正常查询整体不可用。原input、字段名、完整 ID／标题JSON编码和整行预算机制不变。没有扫描／修改 Context Bundle Markdown。

prefetch 在既有 policy lock 内捕获 owner home 并传到投影点，避免 launch profile／HERMES_TIMEZONE 覆盖 owner 时区。带 offset ISO 保留来源 offset 和对应 instant，只依已确认精度省去小数。

### 8.3 正式路径与白名单

正式链为 `PersonalNowledgeMemProvider.prefetch → scope.context_allowed → client.search → candidate_index → _candidate_date → native format_timestamp(profile_home=owner)`，末尾原 epoch/scope 复核不变。仅 Search 外部返回边界使用 StubClient，正式短CJK用例用真实只读 SQLite owner；不调用 NM 或模型。

仅改个人 `nowledge-mem-hermes/personal_provider.py`、`personal_tests/test_r3_provider.py` 及本报告追加。测试加强两个既有节点，新增4个日期节点和1个正式 prefetch 节点；另定向运行既有整行预算／去重节点。根文档、规格、锁、安装器、其他tests和公共 formatter 未改；公共27节点包的六测试保持停写。

### 8.4 执行证据

官方 PM＋canonical runner：`HERMES_PYTHON=/Users/edgar/code/hermes-secretary/.venv/bin/python HERMES_TEST_FILE_RETRIES=0 /Users/edgar/code/hermes-secretary/scripts/run_tests.sh <ignored源码symlink::准确nodes> -q --tb=short --show-capture=no --junitxml=<本次XML>`。个人 ignored `temp-r3-personal/evidence/v51/{red-invocation.json,green-invocation.json,manifest.json}` 保存完整 argv、cwd、指纹和时长。沿既有源码symlink方案，不复制插件、不另建runner。

| 次数 | 证据 | 实际结果 |
|---|---|---|
| 1 RED／生产未改 | red.log、red.xml | 6顶层选择：4普通node失败；坏日期矩阵6子例失败／11子例通过；pytest原始摘要2 passed／10 failed，包含subtest计数，不能当作12个顶层函数。纯日期保留原本通过；wall 1.255秒 |
| 2 GREEN | green.log、green.xml | **8顶层nodes全部PASS＋17坏日期subtests PASS，0失败／0跳过**；XML tests=25即8＋17，不是25个独立顶层函数；wall 1.315秒，runner自身0.9秒 |

8个有效节点均在 test_r3_provider.py：

| 精确节点 | 现行保障 |
|---|---|
| `ProviderContextTests::test_short_cjk_prefetch_returns_only_pointers` | 实际“之前／她／近况”prefetch；真实owner DB及上海时区，launch home／纽约时区不覆盖owner；日期秒精度、正文隔离、limit与源响应不变 |
| `ProviderContextTests::test_prefetch_omits_unavailable_dates_without_reporting_lookup_failure` | 坏日期字段省略、候选保留；正常候选及date-only共存；不误报lookup unavailable，提醒与原input不变 |
| `CandidateEncodingTests::test_full_ids_dates_and_untrusted_markup_round_trip` | 超300字符opaque ID完整、恶意标题JSON安全，ISO微秒裁到秒、epoch变带offset字符串，正文／confidence不出 |
| `CandidateEncodingTests::test_fractional_epochs_and_aware_iso_keep_instants_at_second_precision` | 正负小数epoch、数字字符串、有offset纳秒ISO及Z；正确秒边界／来源offset，原input不改 |
| `CandidateEncodingTests::test_date_only_is_preserved_without_inventing_midnight` | 普通日期和闰日原样保留，不增加午夜／时区 |
| `CandidateEncodingTests::test_unavailable_optional_dates_do_not_lose_other_pointers` | 17子例含None/bool/nonfinite/越界/naive字符串及datetime/非法日期/坏文本/空值/容器；只省字段，保候选／正常日期，原输入引用不变 |
| `CandidateEncodingTests::test_date_projection_obeys_whole_row_budget_without_cutting_ids` | 日期投影后恰好装一整行；少1字符则整行省略；不截长ID或日期JSON，提醒及输入不变 |
| `CandidateEncodingTests::test_budget_omits_whole_rows_and_deduplicates_without_truncation` | 保留原预算、整行省略、去重及非法控制字符拒绝 |

两路径Ruff、冻结C901≤20及git diff --check通过。未重跑46／39全组、P2或公共回归。整理交接脚本的一次非UTF-8解析错误发生在脚本运行前，没有执行其写入；改用ASCII manifest脚本和独立文档patch完成，不是新增产品或测试失败。

### 8.5 缺口与边界

V51出口问题已复现并关闭，无额外产品语义／扩权待决。无来源时区或无效日期按外部可选字段不可得处理，不伪装为规范绝对时间，不因单条坏日期丢正常候选。本包不是独立Verification／Validation、真实NM或部署证据；未操作round3、真实配置或模型。测试配置／DB全部在个人仓ignored临时目录。

### 8.6 接口与指纹

`candidate_index(result, *, limit, budget, profile_home=None)` 只新增可选owner参数；唯一正式 Provider caller 总是传既有锁内捕获的owner home，直接旧helper调用兼容。公共 formatter 签名不改；无新status字段、合成时区或第二时间系统。

| 文件 | 最终 SHA256 |
|---|---|
| personal_provider.py | `bcedd4fb3e214212288cae6ae9fb87d7bc54f7175d8beb40c790831c9f03d37c` |
| personal_tests/test_r3_provider.py | `b88a5cf79d6d2825ddf9927d08e043cca4fb3ab2884568bd0b4fe6427d4fe6cb` |

`v51.patch` SHA256：`14a74be3b3cb0f367ff31296dd09df39162463cd0338fbe0da9e8d7f53dfebf5`。公共观察HEAD `ac7032be96114016bc26d1fa8825c4ba04b925f4`；本次 native hermes_time.py 指纹 `327d66d64231651e0bde085655d874803cc034b2fd3591f06bd3a8484af8a169`。manifest另存完整锁／runner／native依赖和日志／XML指纹；不以后继HEAD冒称本包已提交。

### 8.7 下一步

交root亲自review唯一投影点、prefetch owner传递及manifest后统一提交。本包已停止写入和测试，未stage/commit；不启动round3／真实模型或连接真实NM，不把本开发证据替代独立门禁。
