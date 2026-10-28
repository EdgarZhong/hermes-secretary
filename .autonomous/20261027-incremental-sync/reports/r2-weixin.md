# D-WX / F08 第二迭代实施交回

状态：实现及本包针对性验证完成，待主会话亲审／集成；没有 commit、push、部署、UI 操作或真实微信发送。开始基线为 `b837b1665c965520f60e49f2a25725b3b780545d`，最终测试时共享工作区 HEAD 为 `f7347e3594f0240b768ff7a1824fab57596d6677`，本包四个源码／测试文件尚为工作区差异。其它并行任务的变更保留，未改写。

## 1. 对应条款与阅读依据

- Snapshot Index U11、06 顶部 C3.6、06「2026-10-23 用户确认微信正文与 Redirect」、云端审查 WX.1／WX.2；本包整改根因为 F08。
- 已读本轮 AGENTS／CLAUDE、executing-plans 与 autonomous-run 交接约定、plan、snapshot-index、baseline，以及云端整改计划 §2.5／§4 和原始审查 §1、§2–3 微信对应行、§4.4／4.6、§5.8、§6。
- 原始审查文件 SHA256 已实核为 `3546c0e1138804f25a4e24fcc8ca5d9f3dd1486399445b9300135a0f2b5b24bf`。其结论只针对旧 BE44eb／FE91ad；本报告不将旧静态或隔离 AST 证据冒称为当前实测。
- root 补充确认：同 UID 的真实发送成功事实优先于尾部文本相等；收尾附加 footer 不创造新消息身份。结构化 commentary 不能抢最终正文，长度续答必须投递合并后的实际最终文本。

## 2. 实际变更

| 文件 | 改动 |
|---|---|
| `agent/turn_final_response.py` | 在 stop gates 接受、output transform 完成、append 和正式 flush 返回 True 后，检查原生非空 UID 与启用的完整消息订阅，再发射实际 final_response 的可见投影；复用 surrogate 清理和既有 interim 完整消息发射回调。投影沿用已持久 UID，不改 native 历史内容或结构化载体。 |
| `gateway/stream_consumer_messages.py` | 增加既有 FIFO 的 native-final 绑定／收尾小函数；`bind_final_message` 只新增可选 `on_delivered`。同 UID 只依据成功回执去重，记录实际已发正文；排队／失败不算成功。尾部同 UID 重试仍走同一个 FIFO，连续失败交原有 Gateway 最终发送兜底。复用精确静默 predicate，标记／empty 继续留给原 Gateway 响应整形，不能提前外发。 |
| `gateway/run_turn_runner.py` | 仅将微信完整消息收尾接入上述 sibling，避免扩大文件；实际发送成功后，且原 Turn 与同 consumer 仍属当前 owner，才设置当前结果的 already_sent。其它平台不进入该分支。 |
| `tests/gateway/test_weixin_final_message_completion.py` | 19 项新增正式 Loop／真实 SQLite／真实 consumer／真实 finalizer 的针对性证据。 |

没有修改 `turn_finalizer.py`、micro-compaction、Gateway cache、Noting owner、规则／阈值／schema；未引入新队列、定时器或新发送执行器。

## 3. 正式接线与状态边界

正常模型 stop → `finish_text_response` → 原 stop gates（续 Turn 则不走本次 final 接缝）→ 原 output transform（每 Turn 一次）→ `append_message` → `_flush_messages_to_session_db` 正式事务及 UID 回填 → `_emit_flushed_final` → 既有 `_emit_interim_assistant_message` → 既有 `_assistant_message_callback` → `consumer.on_message(uid, text)` → 同一 FIFO → 真实 `WeixinAdapter.send` → 受控网络边界。

即时投递发生在真实 finalizer 的清理阶段之前。finalizer／micro-compaction／持久化收尾继续原流程运行，没有为了发送跳过它们。flush 返回 False、抛异常、或没有有效 UID 时，不造 UID、不将残片标完成，保持尾部可靠路径。

Turn 尾以 `final_message_uid` 绑定实际结果。此前已成功的原 UID 可在结果晚构造时回放成功事实；此前失败则通过同 FIFO 重试，成功后才确认。footer 或 response_transformed 标记不会推翻同 UID 的真实成功；记录的已发 payload 仍是外部实际收到的内容，不把后来 footer 冒称已发送。不同 UID 同文各自发送。原 Turn 已退休或 holder 已换 consumer 时，旧回执不能确认新结果。

## 4. 验证、原始日志及版本

环境：Darwin arm64，官方 PM `.venv`，Python 3.14.7；runner 隔离 HERMES_HOME、清凭据，使用真实 native Loop／SessionDB／TurnRunner／consumer／finalizer／WeixinAdapter。外部 SDK／Provider 响应与微信网络发送边界受控；没有真实外发。正式 Responses 结构化样本走实际 Codex transport 的归一化，不以人工改 final dict 替代该机制。

所有原始记录位于 ignored `.hermes-dev/incremental-sync-20261027/r2-weixin/`。

| 证据 | 实际输入／观察 | 结论及日志 |
|---|---|---|
| 原版本负对照 | 三个产品文件临时换为 b837 原件，同一新增正式 Loop 测试分别无工具／有工具；finalizer 清理屏障未释放时等不到最终消息。测试结束自动恢复本包文件。 | 2 项均失败，8.55 秒；`baseline-counterexample.log`。这是完整正式路径反例，不是 AST／源码字符串断言。 |
| D01 | 无工具 final，以及前序工具前正文＋final（两条 UID 正文完全相同）。屏障在真实 finalizer 的 cleanup 内，未释放时 adapter 外发边界已收到完整 final、SQLite 已有同 UID、native Task 尚未完成。 | 释放后两种场景均没有重复；新增 `test_final_reaches_adapter_before_finalizer_and_replays_success_receipt`。 |
| D02 | 完成前重复调用同一原生行回调；不同 UID 同文、前序工具消息；成功先发生、结果后构造。 | 同 UID 一次，不同 UID 全部保留，FIFO 顺序保持；既有 Redirect 连续／合并与成功回执测试同时回归。 |
| D03 transform | raw model body 经实际 transform hook 成为另一正文，finalizer 被阻塞；尾部再加 footer。 | adapter 只收变换后正文，hook 一次；尾部同 UID 不重复，真实回执不含未发送 footer。 |
| D03 失败 | 即时发送失败一次／连续两次，各自含 transform 开／关；callback 自身抛异常；flush False／异常／伪 True 但无 UID。 | 屏障期无伪成功；失败按同 FIFO 和原有 Gateway 尾部路径最终发送一次；不吞失败、不造身份。 |
| owner／排队 | adapter 在途期间换 generation 或 consumer；另一例结果已生成但 adapter 尚未返回。 | 旧 generation 的迟到成功不形成 receipt；换 consumer 不确认当前结果；排队阶段不标 already_sent，成功后才确认。 |
| 结构化／续答 | 实际 Codex Responses 同响应含 commentary＋final_answer，final 被 hook 改写；另一次先 length、再 stop。 | 及时收到真实变换后 final／合并全文。commentary 不能盖正文，历史原结构化载体和长度片段不被发送投影改写。 |
| 原能力回归 | 微信管理 slash 拒绝、会话内交互、授权／busy／Stop、工具前完整正文、Redirect、Framework 不外发、非微信／原生 interim、finalizer 持久化。 | 静默保护追加前六文件 150 项通过，无 file retry；`delivery-tests.log`，14.7 秒，10 workers。其中新增文件当时 16 项，既有微信投递 25、slash 86、Framework 4、finalizer 18、TUI interim 1。 |
| 静默及最后影响复测 | 原有 `NO_REPLY`／`[SILENT]` 不从即时通道泄漏，也不伪造成功；正文仅提及 marker 仍发送。响应之后交原 Gateway 整形，由其决定人类输入的可见兜底或允许静默。 | 保护追加后，受影响的新增文件 19 项＋既有微信 25 项＋原 consumer 静默 3 项，最终三文件 47 项无重试通过，12.9 秒，`delivery-final-tests.log`。非受影响的原四文件有效证据复用，覆盖共七文件 156 个不同判例；不是声称单次七文件运行。 |

最终命令：`HERMES_TEST_FILE_RETRIES=0 HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/gateway/test_weixin_final_message_completion.py tests/gateway/test_weixin_message_delivery.py tests/gateway/test_weixin_slash_refusal.py tests/gateway/test_framework_injection_delivery.py tests/agent/test_turn_finalizer_final_response_persistence.py tests/tui_gateway/test_interim_assistant_callback.py`。

最后影响复测命令：`HERMES_TEST_FILE_RETRIES=0 HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh tests/gateway/test_weixin_final_message_completion.py tests/gateway/test_weixin_message_delivery.py tests/gateway/test_stream_consumer_silence.py`。

版本收据：`source-before-final.sha256`／`source-after-final-check.log` 记录前次六文件运行时 20 份源码；最后投递版本由 `delivery-source.sha256` 记录 22 份正式路径源码／测试／pyproject／uv.lock，`delivery-source-check.log` 全部 OK，证明最后运行期间这些文件未变化。源码清单与日志校验集合供主会话绑定最终集成 SHA；本包不将共享工作区 dirty 冒称已冻结提交。

中间尝试如实保留：`projection-tests.log` 是人工 SIGTERM 的未完成运行（65.5 秒，不算通过）；之后的夹具调试日志分别显示 Chat transport 不承载 Codex 额外字段、Responses 需要非空 model 和 SDK 对象结构。夹具已改为真实 Responses shape；`structured-final-2.log` 定向通过，最终六文件无重试通过替代中间未完成证据。没有为这些夹具问题改变产品判据。

静默补证首次 `silence-regression.log` 的两处失败来自原 finish 测试 helper 跳过 Gateway 响应整形、将 intentional_silence 固定传 False；未将它当作真实产品静默判定。补证改为真实 consumer 交接后核原 Gateway predicate，精确断言即时通道不得泄漏标记／确认成功，将原有下游整形保留给其 owner。`silence-final.log` 的六项定向及后继最终三文件运行均通过。

## 5. 缺口与检查边界

- 未验证真实 Provider 网络或真实微信送达；证据只证明正式产品机制及时交 adapter，并在受控边界获得成功／失败事实。没有 UI、生产 DB、部署或真机测试。
- 最终冻结检查以独立 index 只纳本包四文件、基线 b837 执行，避免动共享 index；规则／等级／阈值不变。首次发现的本包文件长度与测试夹具 F811 已按 sibling／pytest plugin 修复，后继 health 为零问题。
- `no-tmp` 扫描全树仍报已有 `reports/idle-owner.md` 第 95／106／107／108／113／128／137 行的七处历史 Linux 路径。原始 b837 独立 index 的 `baseline-no-tmp.log` 报完全相同七行；本包未改历史报告或加豁免。其它九项冻结检查已通过，不能将十检查写成全绿；最终日志 `delivery-final-checks.log`。
- 本包不是独立 Verification／Validation，不替主会话关闭整轮 C3.6 中其它 UI／Android 条款或 E 类事项。

## 6. 接口与兼容影响

- `_emit_flushed_final` 仅在已启用完整 native 消息订阅的路径生效；既有 turn 订阅资格检查继续由发射接口负责。未启用时没有新增通道调用。
- `bind_final_message(identity, text, *, on_delivered=None)` 保留原参数，新增回调可选；只在有真实成功 UID receipt、当前 Turn 仍有效时回调。原有普通 streaming final 路径和其它平台保持原调用。
- 微信有效 UID 的普通完成结果，尾部不再另入竞争的 text-only final，而是同 FIFO 对该 UID 补交；失败后原 Gateway 最终发送继续兜底。中断／失败结果和没有稳定 UID 的恢复路径保留原尾部规则。
- 回执 payload 是真实已发投影，原消息 UID 和原生持久正文不因变换／合并投影或后置 footer 被重造。

## 7. 建议下一步

主会话亲审四文件正式接线及本报告，重点核同 UID 成功回放、两次失败后普通兜底、晚 owner 保护，以及结构化／续答投影与原生历史的分工；将证据清单绑定后继集成提交。已有同版本机制证据可复用，仅集成改动影响本路径时定向复测。已有 no-tmp 历史报告问题交主会话统一处理，不由本包修改受保护历史证据或放宽门禁。全轮云端复审与实际用户 Validation 仍按本轮计划进行。
