# 第三轮本地环境 L0 准备记录（2026-10-17）

本记录仅是环境证据与稳定执行入口，不是动态任务看板或产品验收结果。执行时观察的公开仓库提交为 `c099c8c490846e7989adc4d4aea9a1b4a9a37162`；其他 Agent 正在集成，后续用例必须由主会话另行固定实际待测提交。没有运行产品测试、正式产品、模型请求或真实 NM 写入。

## 可复用环境

- macOS 26.7 / arm64；Node v24.21.0；仓库 `.venv/bin/python` 为官方 PM Python 3.14.7，基础解释器在仓库 ignored `.hermes-dev/tools/`。
- 逐项核对当前平台适用的项目 runtime 与 dev/test 直接声明，共 46 项，全部满足声明版本。例：pytest 9.1.1、pytest-asyncio 1.3.0、ruff 0.15.10、openai 2.24.0、anthropic 0.87.0、ruamel.yaml 0.18.16。PyYAML/pytest-timeout 未声明，不是本次缺失项；未据此安装。
- 官方 PM `--check-lock --offline` 单独退出码为 0；三份输入哈希执行前后相同；未改锁、未裸装、未重建现有 `.venv`。PM 首次执行在新隔离目录初始化自己的管理运行环境，不是产品启动。

| 文件 | SHA-256 |
|---|---|
| `uv.lock` | `2bc4db483e9cba927cd7147f9ccbb09635f85bb3f1f36d6e9d51d06b65d1c67e` |
| `pyproject.toml` | `cadde2f6a92574d292103f43abf66408b1d841cd9ea332ca7f3e3dfc5dcc87fd` |
| `pm/lock.json` | `8b1278f3b535a18077020e21c2549d92c273149a64c2407715eca51178cd92ae` |

## 隔离环境与原生 DeepSeek

已新建 ignored `.hermes-dev/round3-local-20261017-l0/`，目录权限 0700。`core-home/` 与 `core-runtime/` 用于公共核心；`provider-fixture-home/` 与 `provider-fixture-runtime/` 留给个人线 fixture；`L-A/`、`L-B/`、`L-C/` 留作互斥证据目录。没有复制任何旧数据库、会话、auth.json、个人 Provider 或旧完整配置。

`core-home/config.yaml` 仅复用既有 `round2-runtime/config.yaml` 的 model 路由：原生 `custom` provider、`chat_completions`、`https://api.deepseek.com`、`deepseek-flash`、`key_env: DEEPSEEK_API_KEY`。保留的 context_length/supports_vision 是原配置值，不是本轮实测结论。密钥仍在既有 ignored `round2-runtime/.env`；新配置、脚本、报告均不含密钥，新环境没有 `.env` 副本。

`run-native.py` 是只存在 ignored 目录的启动包装器：清空继承的模型/Provider/NM等配置变量，只保留基本系统变量；从上述既有隔离凭据文件读取单个 DeepSeek 密钥并仅放入子进程内存；固定本轮 `HERMES_HOME`、`HERMES_RUNTIME_DIR`、`HERMES_PYTHON`；无密钥则停止，不回退其他通道。没有配置或加载个人 Provider，不能将其用于个人线联调；个人线须先使用 fixture 端点并由唯一 owner 持有其 runtime。

集成完成、主会话固定待测版本和唯一真实模型执行方后，可从仓库根运行：

```bash
# 正式原生 CLI；执行后会启动产品，目前未执行
.venv/bin/python .hermes-dev/round3-local-20261017-l0/run-native.py .venv/bin/python -m hermes_cli.main
# 若后续选择官方 Dashboard：53445 是旧用户服务，53446 在本次观察时空闲；启动前重新检查
.venv/bin/python .hermes-dev/round3-local-20261017-l0/run-native.py .venv/bin/python -m hermes_cli.main dashboard --host 127.0.0.1 --port 53446 --no-open --isolated --skip-build
```

新配置尚未打开 Secretary，后续须由 C4/集成 owner 按新配置契约启用；不应直接以本记录默认配置声称已覆盖 Secretary 场景。上述命令没有添加 Codex App Server/Proxy 或第二模型执行器。

## Python 测试入口与隔离边界

唯一入口继续是 `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh <主会话分配的准确文件/node ids>`。未启动 runner、compileall、收集或产品用例。

runner 没激活时接受具 pytest 的显式 `.venv`，随后 `env -i` 清凭据，按文件启动独立子进程。它不透传调用者 `HERMES_HOME` / `HERMES_RUNTIME_DIR`，不能只靠在 shell 中 export 就声称测试写进本轮 core-home。现有 `tests/conftest.py` 会在导入前创建 session sandbox，并以 per-test fixture 重定向 HOME/HERMES_HOME；测试数据库属于临时隔离数据，不能据此外推真实原生入口已通过。三组必须由主会话分配互斥文件/节点；真实服务/模型由单个 owner 统一运行，不能一边改源码一边取得冻结版本证据。

## 既有运行与远端设置

- 旧官方 Dashboard PID 94335 正监听 `127.0.0.1:53445`，保持运行；不停止、不重载、不改其配置。9119 与 53446 本次未发现监听，端口未预占。
- Provider 工作区初始干净；Web 仓库存在用户未提交源码、package 文件与 `ISSUES.md`，完整保留。主仓根文档的进行中修改属其他 owner，未触碰。
- 只读 `gh api repos/EdgarZhong/hermes-secretary/actions/permissions` 与 Provider 同接口均为 `enabled: false`。没有修改仓库设置或 workflow。

## 证据与限制

脱敏本地清单：`.hermes-dev/round3-local-20261017-l0/evidence/manifest.json`；直接依赖明细：同目录 `dependency-audit.json`。包装器仅 AST 解析通过，未启动它，未验证 API 在线可用性/模型效果。没有本轮测试或真实模型通过证据；没有真实 NM 写入授权。接下来由主会话在集成完成后确认实际 SHA、按组分配测试、由唯一真实运行 owner 接续。

## 后续依赖问题定位（2026-10-17）

个人线确认使用同一公共 `.venv/bin/python`；其 `install_personal.py` 的旧 `import yaml` 在安装器测试中失败。公共项目依赖声明为 `ruamel.yaml`，不是 PyYAML；不是解释器选错或公共 PM 环境缺少已声明依赖。已将明确源码位置与现有依赖交给个人线文件 owner，由其将安装器改用现有 ruamel.yaml，并保留 duplicate key 拒绝、配置语义和事务写入；不向公共环境补装 PyYAML，不改公共锁。环境 Agent 未执行安装器或产品测试，修复验证由个人线唯一执行者负责。
