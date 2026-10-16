# 个人 Provider P1/P2 接收与 P3 交回（2026-10-17）

状态：**个人源码与开发期 fixture 证据已交回，待主会话亲自 review；未作独立 Verification／Validation，未完成真实 NM／模型／云端验收。**

- 工作区：`/Users/edgar/code/hermes-nmem-provider`，分支 `codex/round3-local-completion`。
- HEAD 仍为冻结 `97078118287bcd41ba8b02aa5a3a108c5026f7af`，没有个人本地新 commit／push。已把 P1 `676fec37f439c2033ed046ecc1ad0c7de1c3cfd6`、P2 `e2c01dabd6a9b017b123203310dc0329a09f7563` 的完整 diff 应用到工作区；P1/P2 原 diff 在 index，个人续改在 working tree，新 P3 测试尚 untracked。主会话应看 `git diff HEAD` 加该新测试，不能只看 staged diff。
- Actions 起初实测 `enabled=true`，主会话后关闭，本子任务读回 `enabled=false`。实际 `.git/hooks/post-commit` 与公共 `.githooks/post-commit` 完全相同，保留未改。
- 可 review 全补丁（含新测试）：`temp-r3-personal/evidence/personal-review.patch`。SHA256：`bb6fb64a90df213a61090684ed7c483062f0d45dc94b31ac21c1b87ee859b7bc`；算法见同目录 `manifest.json`。

## 1. 对应条款

| 依据 | 落实内容 |
|---|---|
| PHASE3 现行 §1–3、§6–7；任务 P1 | 单 Provider、真实 source/origin/parent/delegate 与只读 binding 资格；Main 的稳定 Bundle／输入前 Memory Search；Cron 仅 sync，Noting／其他辅助／未知排除；Working Memory 不进入 Bundle；不新增工具、Loop 或第二同步插件 |
| PHASE3 §4.1、§6；R3-008～010；任务 P2 | 官方 CLI 创建→真实返回 ID→同 ID 仅补 `hermes_provenance`；保留无关 Metadata；同运行主机连接；unknown 不猜 ID、不重建；partial 保留 ID、attach-only 修复；只做基本模拟检查 |
| PHASE3 §2、§5–7；任务 P3 | 完成且未中断快照、跨压缩合法 History、整批 host egress、Main Ref／Cron 物理 Session Thread、ACK 收据／增量 suffix／失败不推进／prefix divergence 停止／无蒸馏 |
| 公共 07 §0／§5／§8.10 | 只消费规范消息身份和提案授权；公共源码不改，History 不依赖 NM；未恢复旧 `session_search` 替换／HTTP 完整正文写入 |

## 2. 实际变更与完整文件范围

| 路径（均相对个人仓库） | 来源及修改 |
|---|---|
| `nowledge-mem-hermes/personal_provider.py` | P1 Bundle／Recall／生命周期；P3 完成快照 admission、明确 ACK、既有收据事务、session-end 只重试已接纳快照、结构化归档结果 |
| `nowledge-mem-hermes/personal_scope.py` | P1 资格读取；修复原生 `_reset_from` 的合法独立 Main，保留 fork／同 Ref continuation；P3 `completed_history_rows` 只读到完成 assistant UID；排除 human_only／model_only／interrupted 等注入 |
| `nowledge-mem-hermes/personal_client.py` | P1 禁止 URL query／fragment 配置；候选 Search 的 query 放在 `--` 后，保留旧连接解析及 Thread payload |
| `nowledge-mem-hermes/personal_cli.py` | P2 窄 create／attach；本地没有扩大其行为 |
| `nowledge-mem-hermes/skills/nm-cli/SKILL.md` | P2 官方 CLI／提案／来源／部分失败说明；本地仅更新基本模拟检查状态 |
| `nowledge-mem-hermes/install_personal.py` | 保留原安装事务；检查 skill 完整；旧未声明 PyYAML 改为 Hermes 锁内 ruamel.yaml，保留 YAML 1.1、重复键 ValueError 和配置含义 |
| `nowledge-mem-hermes/README.md` | 替换旧 helper 命令；说明 host Bundle 生命周期、ACK／session-end 边界、R3 测试、fixture／真实服务区别 |
| `nowledge-mem-hermes/personal_tests/test_r3_provider.py` | 云端 P1 30 测试；临时库改为仓库 ignored 目录；新增原生 reset 资格断言，共 31 项 |
| `nowledge-mem-hermes/personal_tests/test_r3_thread.py` | 新增 15 项真实 SessionDB／MemoryManager／HTTP fixture 集成测试，含隔离安装及注册 |
| `CLAUDE.md` | 更新本地实施、证据、C9 缺口与 `round3` 实测约定；旧冻结状态置于历史折叠区 |

公共工作区只新增本报告，没有修改公共产品代码、核心文档或计划。未修改个人根 README／AGENTS、冻结 PHASE3、社区其他集成、注册表、依赖／锁、workflow、真实配置、NM 治理或数据。

## 3. 正式路径

1. 既有 `__init__.register` 只注册 `PersonalNowledgeMemProvider` 和 `nm-cli` skill；不加 post_llm_call fallback。
2. 原生 MemoryManager 初始化→Provider `initialize`→只读 owner state.db scope；原生 root build 调 `system_prompt_block`，prefetch 调官方 Memory Search。P1 只在 host 真实调用该 hook 时取 Bundle；不维护跨 rebuild 的第二层 Thread cache。
3. 完成 Turn 持久化→`sync_all` 的 egress＋串行 background worker→`sync_turn`→规范 History Foreground 截到此完成快照最后 assistant UID→对包含 tool 行的整批做 `_redact_for_provider`→只保留合格 User／Assistant 正文及时间→Thread import／append→明确 ACK→同 receipts.sqlite3 事务推进 prefix。
4. session-end 的任意尾部不作为完成证据；仅重试此实例先前由 sync_turn 接纳的 scope／快照。switch／reinitialize 清除此 admission。
5. `personal_cli.main create` 参数数组运行官方 CLI，解析真实顶层 ID；`attach_metadata` GET 原 Metadata 后 PATCH 合并 Metadata，不 HTTP 创建／编辑正文；`attach` 不再创建。

规范 UID 已核实生产机制：`agent/session_persistence.py:_db_flush_write` 调用 `sync_flushed_message_markers`，在 finalizer 的持久化步骤把 UID 回填 live messages；不是测试自行发明字段。测试直接跑真实 SessionDB／History／MemoryManager，并在网络边界接本机 fixture。尚未用 AIAgent＋真实模型证明最终 host gate，见缺口。

## 4. 执行证据

解释器：公共 `.venv/bin/python`，Python 3.14.7，macOS 本机。公共核对时 HEAD `723343c60f65e6942f7a26113455cff53292c6cb`；PM uv.lock SHA256 `2bc4db483e9cba927cd7147f9ccbb09635f85bb3f1f36d6e9d51d06b65d1c67e`。host 依赖文件 hashes 和个人 dirty patch hash 见 `temp-r3-personal/evidence/manifest.json`。没有安装依赖／改锁。

| 命令／范围 | 实际结果 | 本地证据 |
|---|---|---|
| `PYTHONPATH=/Users/edgar/code/hermes-secretary /Users/edgar/code/hermes-secretary/.venv/bin/python -m unittest discover -s nowledge-mem-hermes/personal_tests -p 'test_r3_*.py' -v` | 44 通过，1.455s（P1 30＋P3 14，reset 修复前） | `temp-r3-personal/evidence/r3-personal.log` |
| 同解释器按 node 执行 reset 新增2项＋既有 fork／continuation 2项 | 4 通过，0.603s；范围内共 46 个独立测试（P1 31＋P3 15），没有重复再跑全套 | `temp-r3-personal/evidence/reset-repair.log` |
| `.../.venv/bin/python temp-r3-personal/evidence/p2-basic.py` | 基本模拟检查通过：preview无调用、单次CLI、顶层真实ID、metadata-only merge、partial ID、repair不create、unknown不PATCH、连接一致 | `temp-r3-personal/evidence/p2-basic.log`，脚本也留该目录；没有严格通用 CLI suite |
| P3 安装器 YAML1.1／重复键与隔离安装正式注册定向复测 | 2 通过，0.612s | `temp-r3-personal/evidence/installer-repair.log` |
| `.venv/bin/python -m ruff check` 明确列出的7个个人Python路径 | 通过 | `temp-r3-personal/evidence/ruff.log` |
| 同7路径 `ruff check --select C901 --config lint.mccabe.max-complexity=20` | 通过；reset 后 scope 定向复查也通过，未改门禁 | `temp-r3-personal/evidence/complexity.log` |
| `git diff --check` 与 `git diff --cached --check` | 通过 | 本次命令输出 |

P3 场景：真实 History 与后台 snapshot 边界；api_content 不出境；跨 tool→assistant 的 Bearer 秘密整批遮蔽；noncompleted/interrupted/failed 不调用；未接纳 session-end 不调用；失败 session-end 只重试已接纳快照；空／错误／不匹配 ACK 不推进；HTTP timeout 不推进且可 at-least-once 重试；相同 prefix 不再请求；restart 仅 suffix；edit／rewind／空路径 reconciliation-required；compaction 同 Thread、fork/new/reset 独立；endpoint／Space 隔离；Cron 物理身份与辅助排除；无额外治理请求；缺 UID 失败关闭；隔离安装保持 MEMORY/USER。

首次 P3 测试暴露 PyYAML 不存在，按环境 owner 核实使用锁内 ruamel.yaml 修复；首个脱敏断言错误假定所有原生掩码都为 `[redacted]`，改用 host 支持的 opaque Bearer fixture 专门证明跨行传播，完整秘密仍断言不出现。失败项都已定向复测关闭。

所有 runtime DB／receipts／临时安装都在个人仓库 ignored `temp-r3-personal/`；没有 `/tmp` 运行库、真实 profile、真实 NM Memory／Thread／Space、真实凭据或治理变更。

## 5. 缺口与限制

- **C9 必修，已交主会话：** 现有 `run_agent.py:_sync_external_memory_for_turn` 只 gate interrupted；`agent/turn_finalizer.py` 调用未传 completed/failed。失败或未完成但非空 final_response 仍可能进原生 sync_all。个人 Provider 接到 native completed hook 时默认视作已准入，不能从文本可靠推断失败。必须在正式 host owner 修，不能以本报告宣称闭环已全部完成。
- 真实 NM 自动 Thread 写入未授权；当前仅本机 HTTP fixture。实际服务的 import／append／明确 ACK 形状和去重未验证；不承诺 exactly-once。P2 的实际远端 Metadata／官方 CLI 兼容性按用户例外留后续授权部署基本调整，不新增严格验收。
- 用户最新约定：正式模型／产品实测统一 `round3` 隔离 profile，由主会话指定唯一 owner；本子任务未启动其他真实产品 profile。真实模型 gate＋完整 AIAgent 入口待 C9／正式实测 owner。
- 历史 `personal_tests/test_personal.py`／`test_security.py` 仍有旧 CLI (`write_memory`、`validate_evidence`、`edit_sha`)、Bundle 二层缓存、长 ID 拒绝、无完成 UID／旧 history_rows patch 等退出契约；本任务白名单外，未改、未运行。C10 应按现行规格收口，不能 skip/xfail，也不能宣称旧整目录通过。
- 个人根 README 目前仍展示旧整目录测试入口；因不在本任务写白名单，只更新了插件 README 和根 CLAUDE。主会话请把根稳定测试入口改为 R3 两模块；AGENTS 无新增规则需求。
- 独立 Verification／Validation 未由本子任务执行；UI、真实账户写入、NM治理和云端部署继续后置。

## 6. 精确接口与事务责任

- `resolve_scope(home: str, session_id: str, runtime: dict) -> Scope`：context_allowed 仅 Main，sync_allowed Main/Cron；Main 有 binding 则 `hermes-personal-<conversation_ref>`，否则／Cron 为 `hermes-personal-<session_id>`。只读不注册身份；fork/reset parent marker 必须匹配真实 parent。
- `history_rows(home, conversation_ref) -> list[dict]`：原有只读 canonical 投影；新增 `completed_history_rows(home, conversation_ref, messages)` 截到最终 assistant UID；缺 UID `ValueError`，UID 已退出合法路径 `HistoryReconciliationRequired`，绝不回退上传 live 摘要。
- `sync_turn(user_content, assistant_content, *, session_id='', messages=None, completed=True, interrupted=False, failed=False, **kwargs)`：native hook 兼容；显式非 completed／interrupted／failed 返回 skipped；正常返回 `{'status':'acknowledged'|'unchanged'|'unacknowledged'|'reconciliation-required', 'thread_id':...}`，ACK 时附 appended 数。host 可忽略返回，日志仍明确失败；不会抛网络正文或凭据。
- `_policy_lock` 保护 Provider 生命周期和 admission；现有 receipts DB 的 `BEGIN IMMEDIATE` 覆盖 prefix 读取、网络写入、明确 ACK、收据 commit，使不同实例不各自从旧 cursor 同时推进。失败回滚；body 不落 ledger。Bundle／Recall 网络读仍遵循 P1 epoch 校验。
- `on_session_end(messages)` 只重试已接纳 snapshot；不从此参数建立新的完成资格。
- `PersonalMemClient.request_json(method,path,payload=None)`、`context_bundle(...)`、`search(...)`、`memory_get(id)` 和继承 `import_thread`／`append_thread` 形状保留。
- P2：`main(argv=None)->int`；`create_memory(client,content,provenance,*,title=None,labels=None,space=None)->dict`；`attach_metadata(client,memory_id,provenance)->str`；`parse_created_id(output)->str`。exit 0 preview/complete，1 preparation failed，2 partial，3 creation_unknown。所有连接复用旧 client resolver，helper 不新增配置。
- C9 精确调用建议：finalizer 将实际 `completed`、`failed` 传到 `_sync_external_memory_for_turn`；该函数在 `completed and not failed and not interrupted` 才调用既有 sync_all／queue_prefetch_all。给兼容调用者默认值可保留既有同步 API；MemoryManager 无须新增 NM 专属协议。必要失败场景：completed=False且有最终文案、failed=True且有解释文案、interrupted=True且有partial、正常completed=True；前三者无 sync/queue，最后一次且仅一次。禁止回退为“只看非空final_response”。

## 7. 建议下一步

1. 主会话亲自阅读全量 P1/P2 差异和 P3 补丁，重点核对 native scope、root build 生命周期、完成 UID 边界、ACK 收据及窄脚本 config 路径；按十文件清单统一提交，不遗漏 untracked P3 测试，不触发部署。
2. C9 修正式 completed/failed gate，并在 `round3` 隔离 profile、fixture NM 下走真实 AIAgent／模型入口；不复跑本报告有效的46个个人用例，仅对改变的 host 接线补证。
3. C10 精确收口历史个人测试与根 README 入口；真实 NM 行为继续以授权边界如实交独立门禁判定，不能把模拟结果写为真实通过。
