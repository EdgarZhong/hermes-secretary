# 本轮实施计划：20261031-force-completion

## 目标与依据

按snapshot-index.md及baseline.txt，修复正式Main结束→Force／FM→完成回执→前端恢复与持久缓存→冷恢复完整链。生产BE88ed1ca／FE5f974b3。用户已授权发布及APK；先完成机制和实际用户路径，独立Verification通过后Validation，再main发布／APK交付。真实外网模型调用、生产测试消息／微信外发不在授权范围；Provider返回可控，正式Loop／DB／RPC不得绕过。

## 覆盖与任务
| 要求/口径编号 | 任务和正式路径 | 实现负责人及白名单 | 依赖和接口 | 验证方法 | 用户场景 | 完成条件 |
|---|---|---|---|---|---|---|
| U01–U03 | B：Main结束事实与Force／FM后续追加解耦，修正式回执 | backend；tui_gateway/prompt_turn.py、必要同目录sibling、agent/turn_finalizer.py／turn_facade.py／secretary结束接缝（必要才改）；tests/tui_gateway/test_native_recovery_settlement.py及相关新增专项 | 原生final_message_uid／当前合法来源；保持完整历史和恢复严格证明 | 真prompt.submit_idle、Main／child Loop、DB、回执、activate；普通／Steer、child运行／完成、后继发送／Compact与失败边界 | Main结束而Noting运行也可继续操作；FM及时可见 | 原反例失败→修后通过，无手造成功receipt |
| U01–U04 | F：前端正式接收与恢复／缓存检查；发现必要缺口则修 | frontend；独立前端src相关代码及测试；不改后端 | 正式事件／REST／恢复封套；保权限与缓存资格 | 完整Controller／App、真实IDB／hidden IAB；最新尾部与FM暖／冷恢复、Noting活动不锁Main | 同页解除恢复／刷新后最后输出仍在 | 不盲写半截缓存，不借Noting状态启Main |
| U05–U07 | I：集成亲审、两门禁、main部署／静态与APK | root；核心文档、本轮报告、运维、ignored构建发布 | B/F收敛；保护dirty与运行数据 | 当前范围定向检查、正式服务／静态SHA、APK原签名／资源一致性 | 用户重新进入能操作并取得新包 | 双门禁通过、发布verified、APK可下载 |

## 当前状态与编排
| 目标/任务 | 机制实现 | 正式接线 | 针对性验证 | 用户结果 | 当前负责人和下一步 |
|---|---|---|---|---|---|
| B | 原生final UID封闭回执 | 正式Web→Loop→Force／FM→activate通过 | 六文件177项、最终4＋6及冻结十检查；root亲审接收，backend.md | 子任务活动时后继发送／Compact可用 | 已集成，双门禁通过 |
| F | Pending未采用却报成功已最小修复 | 正式Controller／App／PageRecovery／IDB已接线 | 9文件273项、typecheck及冻结TS度量通过；见frontend.md | 自建隐藏IAB实际Send→Force held→冷刷尾部/详情→后继Send→Compact→child结束→同页重连通过 | frontend整包交回；root已提交6c132a4，进入独立门禁 |
| I | 目标完成 | BEef9051f／FE6c132a4已提交push | Verification12条全部符合；Validation7场景通过；原签名APK已交付 | 01:24:38发布verified，原尾部保持；交付事实独立补核通过 | root已完成交付判定，final-delivery.md |

后端现有分支继续承载本轮，前端同目录在codex/force-completion-20261031分支实施（无其它产品dirty，仅用户.DS_Store不动）。源码不交叉；子Agent不得再派生、不自行commit／部署。报告仅整包交回，真阻塞才中报。UI严格只许自建Codex隐藏IAB（iab、visible:false），不能桌面／外部浏览器／可见页／用户页面。主会话无重复实现，亲审正式链与证据。

## 缺陷与整改
| 问题编号 | 要求与触发条件 | 当前事实与影响 | 优先级及理由 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|
| F01 | Main正常结束后Force追加FM | 旧回执以共享历史尾行猜最终assistant，实际complete=false；现由原生final UID封闭 | P0，用户不可操作 | backend | 原反例、Main／child隔离、后继发送／Compact均通过 | 双门禁通过 |
| F02 | 首次恢复失败后Pending先于新cut返回 | 未adopt却报成功导致pendingSnapshot永久缺失；已改失败重试；正常尾部／FM缓存不缺实现 | P0，无法恢复 | frontend | 273项及隐藏IAB暖冷／真实IDB、后继Send／Compact通过 | 双门禁通过 |

## 取舍、快照与续接

00:42:26用户紧急授权救援：只读确认Web0／Gateway0且无活动Noting后重启Web，Gateway保持；health正常、正式REST末回复243字符及FM215字符存在，用户随后确认已能压缩。此为应急恢复，不是产品修复。原始证据在.hermes-dev/force-completion-20261031/；无凭据或用户正文进Git。最初冻结点产品未改，首有效反例before-3.log中2失败均在正式恢复complete断言；现两处修复、双门禁、main发布及APK交付全部闭合。
