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
