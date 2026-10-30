# B · Main 完成边界修复交接

状态：实现、正式接线、针对性验证已完成，待主会话亲审／集成与独立门禁。未自行提交、部署或派生。基线 `56d0aefa0a174a861e67b17efd4d21f068053457`；只修改 `tui_gateway/prompt_turn.py` 与已交接的 `tests/tui_gateway/test_native_recovery_settlement.py`。根 CLAUDE／operations-log 等并行修改未动。

## 1. 对应要求

- Snapshot Index U01–U03、F01：原生 Main 结束后触发 Force，后台 Noting 不得阻止 Main 完成恢复、后继发送或 Compact。
- U02／07 顶部 2026-10-31 与 10-28：最终输出事实与后加 Framework 的生命周期分开；FM 派生时及时入历史并展示；Force 仍在原生租约保护内冻结／派生，下一 Main 不抢先。
- U04／06 C0–C3 中 D01／D04／D12／D15、S05／S13／S14、P03／P05：正式历史及最新 Thinking 的可证明内容不丢失；恢复不放宽身份、来源、前缀、提交或压缩证明；Noting 状态独立。
- 保持原生禁用／非 Main／失败路径、权限、阈值、Schema、模型／Prompt 和普通联合入口语义。

## 2. 实际变更与机制取舍

`prompt_turn.py:1011` 新增 `_turn_receipt_messages`；`_persisted_turn_receipt` 仅将其返回的本次 Turn 范围交给原有证明计算。

原生 `agent/turn_finalizer.py` 在 final 持久化后已经产出独立标量 `final_message_uid`。成功 Main 回执现在用该 UID 的唯一出现位置正向封闭范围，随后仍执行原有 Assistant role、无 tool_calls、正文等于实际 final、真实 committed row、原始 User 来源、前缀与压缩未变化等校验。缺失、空、重复或不落在有效来源范围的身份不产生成功证明。没有按 Force 字串、Framework 类型、文本相等、timestamp 或倒查末个 Assistant 选择身份。

这不是删除后续历史：仅创建供回执计算的列表切片；`result['messages']`、`agent._session_messages`、`session['history']` 和数据库继续保留全部后加 FM。下一 Main 的实际 Provider 请求已验证含完整 FM。

没有新增完成事实表／快照或改写原生 finalizer。已有 final UID 是持久化完成时冻结的输出身份，无需新增第二个 owner。对于尚未提供 `final_message_uid` 的旧 runtime，保留原 transcript-tail 合约；error／interrupted 路径也保持原范围。

没有移动 Force 接缝或调整通知顺序。三个时点明确区分：①原生 Loop 的最终输出已持久化并确定 UID；②facade 最后清理，在仍持 admitted lease 时观察 Main 结束、冻结／派生 Force 并接入 FM，然后释放 lease；③Web 吸收完整结果、发出 `message.complete` 并清除 Main running。短暂 Web 收尾仍存在；后台 child 的寿命不能扩大第③步的证明范围。FM 的 `status.update` 仍及时出现，既有原生 lease 阻止下一 Main 在冻结前抢先。

Steer 的原有单 User 快路没有放宽：`persisted_turn.complete` 仍为 false；它沿原有完整 committed suffix 和 `source_boundary` 的严格闭合证明恢复。普通 Main 的成功回执只覆盖本次 User→已确定 final，随后 FM 不属于该 Turn 的输出回执。

## 3. 正式调用路径

`prompt.submit_idle` → 原生 Web admission／持久 User → 真实 `AIAgent.run_conversation`／Loop／finalizer → final UID → `_finish_native_lease` → `note_main_turn_finished` → `check_force_at_turn_end` → 真实 Force admission／冻结／后台 child／Framework publisher → Web `_absorb_turn_result` 保留完整历史 → `_complete_turn_payload`／`_persisted_turn_receipt` → 原有 replay／`session.activate` 严格恢复。

测试只控制 Provider 返回和 barrier、无关主机音频／后台展示依赖；Main Loop、child Loop、`finish_noting` 工具、真实 SQLite、原生租约、Framework publisher、正式 RPC、REST history sync 与恢复证明均实际运行。未手造成功 receipt 或 `complete:true`。原夹具禁止 socket connect，实际模型／网络请求为零。

## 4. 验证结果与原件

环境：本机 macOS、官方 PM 项目 `.venv` Python 3.14.7；`uv.lock` SHA256 `2bc4db483e9cba927cd7147f9ccbb09635f85bb3f1f36d6e9d51d06b65d1c67e`。所有测试经显式 `HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh`，最终相关套件禁用文件重试。

原件均在 `.hermes-dev/force-completion-20261031/`：

| 证据 | 范围／结果 |
|---|---|
| `before-3.log`（主会话原件） | 旧产品代码上普通／Steer 正式 Force 反例都失败于 Main recovery complete；前两次夹具失误原件保留 |
| `backend-first.log` | 初次机制修复后，原 Force 两例＋普通原生多入口两次后继 Turn 共10项通过，8.0秒 |
| `backend-expanded.log`／`backend-followup.log` | 扩展夹具的早期失败保留；后继 FM 已在真实请求，但测试用含换行正文匹配 list repr 的转义字符串，修为逐条真实 content 检查；不改产品规避 |
| `backend-full.log` | 新增场景后本文件66项通过，43.4秒 |
| `backend-related.log` | 六文件177项通过，57.1秒、总子进程106.0秒；native settlement66、output identity16、recovery view54、history sync17、native Force lease6、Force owner18 |
| `backend-wire-final.log` | 最终导出助手／tmp_path 调整后，普通／Steer×有无后继发送和 Compact 共4项通过，5.1秒 |
| `backend-identity-final.log` | HX011表驱动修正后的6项最终身份破坏反例通过，5.1秒 |
| `backend-check.log` | 初次冻结检查发现测试损坏夹具 HX011 分支链，真实修正为表驱动，无例外 |
| `backend-check-final.log` | 独立临时 Git index 仅暂存本包两个源码文件，冻结十检查通过；health 0阻断／0建议；真实 index 未改 |

六文件覆盖：Main＋Force真实 child 活动与完成、普通／已消费 Steer、任意非 Force Framework 追加、后继真实发送、后继模型上下文保留 FM、child 活动时正式 `session.compress` 成功、压缩后恢复与完成 Note、来源和最终身份破坏拒绝、后加未知输出拒绝、跨 Profile、rewind／删除／compaction、租约竞争与前后继顺序、全局关闭／非 Main、Force 通知失败及原生异常终态。

产品文件 Git blob 为 `0d6147e199eda45ca4c098c5a4f5bf96276458bc`；最终测试文件 Git blob 为 `73fee3d1a3135c8df339b503f2bdb6eef45754cc`。177项后只改了导出助手及损坏夹具的等价表驱动，分别由最终4项与6项定向覆盖；产品源码自首次通过后未再变化。`git diff --check` 通过。

提供给前端的真实三阶段原件：`native-force-wire-{ordinary,steer}-{base,followup}.json`。顶层 `pre/active/finished` 各有完整 REST history_sync、details、完整 activate、无 cursor 的 activate_snapshot、secretary.state、实际 replay events。active 为 Main idle／recovery complete／child active；finished 为 Main idle／recovery complete／child idle。active／finished snapshot 以 pre 的真实 coverage 请求得到 matched=false；各 snapshot 都来自正式服务端，未改 sync／receipt。base 推荐作 App 暖冷恢复输入，followup 额外含下一 Main 和 child 活动期间压缩。

正常测试只写测试自身 `tmp_path/native-force-wire.json`，不写固定仓库路径，不新增环境开关。重新保留导出可执行：

```bash
HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/tui_gateway/test_native_recovery_settlement.py -k turn_end_force --basetemp="$PWD/.hermes-dev/force-completion-20261031/backend-wire-tmp" --tb=short --file-retries 0
```

随后从该目录每例 `native-force-wire.json` 原样复制到证据目录。已实际执行该命令并生成四份最终原件；不修改 runner allowlist。

## 5. 缺口与边界

本包未执行 UI、生产部署、真实外网模型或 Android 设备验收。前端正在使用最终协议原件作真实 Controller／App／IDB 及隐藏 IAB 验证，结论由对应报告负责。macOS 机制验证不能冒称正式 Linux 主机已部署或真实手机通过。

范围内后端已知阻断为零；独立 Verification／Validation 尚由主会话安排，不能用本包自评替代。旧 runtime 没有最终 UID 时按既有尾部合约工作，未扩大其能力。

## 6. 接口影响

无新 API 字段、必填参数、错误码、数据库结构、Prompt、阈值或状态机；没有更改 Force／普通联合入口、权限或 Main admission。既有 `persisted_turn` 字段保持，`row_ids/source_messages/final_assistant_row_id` 精确表达本次已完成 Main 的边界。完整 Conversation 历史及后台 Noting 状态独立可读。

## 7. 建议后续动作

主会话亲审本包两文件与正式上下游，接收177项及最终定向证据；前端用最终 base 原件完成暖／冷最新尾部、Thinking、FM、Noting 独立性和操作资格检查。之后按整轮安排独立 Verification、Validation；通过后由主会话统一提交／自动 push、main 发布并核真实服务、前端资源及 APK。无需为本包 review 重跑有效177项，集成改变或新发现才定向复核。
