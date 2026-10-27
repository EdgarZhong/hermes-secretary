# 主会话集成审查与实际联调（进行中）

本报告尚非整轮通过结论。前后端产品收尾代码已完成并亲审；精确载入版本见ignored integration/runtime.json及各实现报告SHA。仅自己的隐藏IAB，真实App／Controller、真实SQLite、正式REST和native activate／replay／WS。Usage／Pending／配置／压缩状态响应为受控依赖，无生产模型或外发。

## 已完成亲审

- B1：实际DB／Profile／Conversation／selector绑定的短期fingerprint缓存；D0／S／D1及原生cut仍正式接线；详情revision变化不能靠cards matched跳过；手动维护保真实busy，仍核冲突租约／残留输出。
- F1：同IDB条目原子保存消息、完整详情、游标与版本；按UID统一最多500，详情不是新消息；旧owner／迟到结果无展示权限；Usage／Pending并行于历史、仍保原操作门禁。主会话发现的终态Context失败不重试和unknown订阅永久观察已按明确方案定向修复，合法unavailable／历史补读／详情共享收尾已亲审，最终IAB复验待完成。
- Android免刷新6ba37b4、Toast main 810aca3／功能分支03ef6d5已亲审；旧Signal Aborted／Notebook／键盘／微信main修复按各报告接收。未部署、未真机安装或微信真实试发。

## 实际IAB证据

证据根：前端`.archive/incremental-sync-20261027/integration/`，原始JSON和PNG不入Git。

| 场景 | 实际观察 | 证据／边界 |
|---|---|---|
| 200条长消息，同页断线期间追加并修改一行 | 同document恢复为新的200条窗口，草稿12字保持；新末条是外部修改正文；当前完整就绪、无通知 | root-append-state／requests；recovery封套18403 bytes、delta1行，REST仅摘要及侧栏，无正文全量 |
| 同页无变化再重连 | 同document就绪、草稿保持；delta0正文 | root-unchanged-state／requests；恢复封套17656 bytes，不含TLS／压缩，不冒称生产时延 |
| native手动维护运行中重连 | 原生_manual_compress_turn提供running／maintenance，正式activate成功；原Context环及Compacting可见；重连同document继续active并恢复就绪 | root-compact-active.json/png、root-compact-reconnected.json；压缩状态RPC受控、非真实模型摘要 |
| 结束且Context首次读取故障 | 同document退出active、Context由2000收敛为500、页面就绪、通知为空、草稿保留 | root-compact-finished.json/png；原生维护退出，摘要／计数受控 |
| epoch／cursor丢失 | 同document恢复并保草稿；必要snapshot回退成功 | root-epoch-state／requests；模拟epoch变化不是重启真实生产服务；发现重复全量见下表 |

首次开发服务重启后Vite自动热更新替换了夹具页，因此该次epoch观察作废；后续已在ignored专用Vite配置关闭HMR，再建立独立document完成压缩和epoch旅程。正常恢复旅程内没有主动reload。

## 主会话发现与待关闭项

| 问题 | 反例 | 已指定方案／状态 |
|---|---|---|
| F1终态Context一次失败后永不重读、unknown永久轮询 | 正式Controller新增反例改前失败，见frontend报告followup | 分离Context成功标记与history完成；unknown只退观察，不假确认命令；已实现，合法unavailable终态补验中 |
| 已finished压缩后的epoch恢复重复全量 | root-epoch-requests：两个并行snapshot各598805 bytes／200行，总RPC约1.20MB | 当前同owner历史在途读取先settle取得新cursor，再沿原强制终态对账；不得只跳过终态刷新。F1已实现并亲审，最终IAB复验待执行 |
| 首次展开旧Thinking重复详情读 | root-detail-requests：同row6两次REST各4740 bytes | 无staged画面时共享原HistoryDetails读取owner；staged隔离／版本核验保留。F1已实现并亲审，最终IAB复验待执行 |
| 历史typed来源不可判定 | B1正式反例可见同类typed既是Turn又可仅通知 | 用户U17已确认旧模糊片段懒取、新Turn最小内部source标记；B1已实现并亲审，候选862326c0a7 |
| Idle旧owner迟到host tick抢回绑定 | root审当前maybe_run_idle_noting路径 | 曾绑定但被替换的实例在attach/tick前拒绝，真实新Main边界保持；已亲审关闭；main 0a5d09cdcf，同补丁已接入增量 |

| Idle旧completion清理撞新native复用 | _end_completion提前读取pending后才等待Framework，可能清掉随后reserve的同handle | 在同一ACTIVE临界区reserve；Framework→ACTIVE重新核验并原子关闭；已亲审原子交接及71＋3项定向证据；main 0a5d09cdcf，Linux待验 |

最终版本须定向重验上述修复并核SHA，之后执行全轮独立Verification及Validation。本报告不把当前部分结果冒称交付完成。

## 恢复执行后的候选与环境边界

后端候选862326c0a7，前端候选91ad72f3898be4e6d98461f69566a76b54595290；最后六文件SHA与244项、typecheck、build和冻结度量证据一致，主会话已审上下游和owner／revision保护。当前已重启精确版本真实Python／SQLite／HTTP／WS隔离夹具，未调用模型或微信。隐藏IAB创建被工具拒绝：Local browser use is disabled in Work settings；用户随后截图证明开关已开启，重建连接仍同错，实际根因未知，不能据此断言用户关闭设置；未操作其它浏览器或用户页。最终epoch单snapshot、详情单请求及unavailable停止观察的实际浏览器复验尚未执行；上述旧反例保留，不以受控单测替代本项。独立Verification将核全部冻结要求及证据边界。

Linux7文件163项证据及19份日志／记录SHA已由主会话核对，全部相符；自建远程工作区已删除。复测时证据目录需预建，新增测试可移植性整改已登记plan，不改写既有产品路径测试结果。用户准备重启Codex，本地fixture服务5637/5638已正常停止；最后运行配置与SHA留在ignored runtime.json。
