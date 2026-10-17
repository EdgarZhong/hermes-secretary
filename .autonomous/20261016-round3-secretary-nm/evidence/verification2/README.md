# 第二次 Verification 反证材料

固定产品SHA：`b40fa1ff2a771066b4da1d8978a7abe44327e530`。这些文件记录第二次独立审查的原始失败和合法对照，不是修复补丁。审查结论与逐条覆盖只维护在上两级的 [verification.md](../../verification.md)。

四组都使用官方PM Python 3.14.7、原锁dev/test环境、Linux x86_64，经 `scripts/run_tests.sh` 运行，禁文件重试、每次单文件单worker。10个参数用例为3 PASS / 7 FAIL；4次真正进入测试的runner wall合计8.7秒。另两次普通沙箱在收集前因原runner临时目录不可写退出，0 tests；保留sandbox日志，不将其混入产品计数。

| 问题 | 脚本 | 原始输出 | 实际结果 |
|---|---|---|---|
| V2-F01 隐藏来源提交 | [test_v2_provenance.py](test_v2_provenance.py) | [provenance.log](provenance.log)、[四例结构化观察](provenance-observations.json) | 0P/4F，真实绑定工具、finish、Store/SessionDB commit |
| V2-F02 退休名称修复 | [test_v2_retired_tool.py](test_v2_retired_tool.py) | [retired-tool.log](retired-tool.log) | 2P/1F，真实native child loop与最终Snapshot |
| V2-F03 配置ContextEngine改前缀 | [test_v2_context_selection.py](test_v2_context_selection.py) | [context-selection.log](context-selection.log) | 0P/1F，Main1请求、child3请求，前缀true/false/false |
| V2-F04 周期resume跳过未来发生 | [test_v2_scheduler_resume.py](test_v2_scheduler_resume.py) | [scheduler-resume.log](scheduler-resume.log) | 1P/1F，正式Store及native时间计算对照 |

## 复现方式与观察范围

在独立的固定产品checkout按项目PM准备 `.venv` 后，将所选脚本以同名文件放到该checkout的 `tests/secretary/`。它们复用同SHA已有测试fixture，必须经过原tests的隔离conftest。不要覆盖已有同名文件；本次执行时四个同名文件都是新增。

示例（以来源反例为例，脚本位于标准tests目录之后）：

```bash
HERMES_PYTHON="$PWD/.venv/bin/python" HERMES_TEST_FILE_RETRIES=0 scripts/run_tests.sh tests/secretary/test_v2_provenance.py -q -j 1
```

其余三文件用相同入口替换文件名。没有绕过runner直接执行pytest；原runner失败输出自带的裸pytest Repro行只是其原始文本，不是本次使用的命令或建议入口。main中保留的审查脚本位于证据目录，不自动加入产品默认测试集合；修复者应将有意义的断言整合到对应正式测试并保留原失败。

模型客户端/时钟/可配置ContextEngine加载依赖受控；来源反例只控制外部Noting readiness，使用真实绑定工具、Store与SessionDB提交，未经过原生模型Turn。退休名与ContextEngine两组使用实际原生child循环，Scheduler组使用正式Store和原生时间计算。来源判定、版本、事务及目标断言都由实际产品实现执行。所有消息都是合成数据，无真实NM、真实模型调用、用户profile修改或部署。它们证明列出的具体路径，不证明整个用户体验或真实缓存收益。

## 版本和历史证据

[manifest.json](manifest.json)保存当前脚本/日志/原始规格/关键实现/测试fixture哈希和执行摘要；[requirements.json](requirements.json)为三条独立审查线的完整要求及证据数组。[historical-evidence-reuse.json](historical-evidence-reuse.json)只读核对旧失败修复六个测试文件和锁，不把旧报告冒充本次重跑。

F16最新真实失败在40f4ecc，随后b40fa1f改Prompt而尚未新实测；其原始模型日志本环境没有读取。output-cap恢复仅静态定位，不在这四组已执行测试中。这两项证据不足详见正式报告。
