# 本轮实施计划：20261021-conversation-heartbeat

## 目标与依据

依据Snapshot Index及baseline.txt。完成Conversation级Heartbeat并经独立Verification、Validation后部署后端＋既有前端包，最后正式设置Alex实际置顶Conversation的2小时无额外prompt Heartbeat。保留所有其它数据、配置和绑定。禁止Astra。

## 覆盖与任务

| 要求/口径编号 | 任务和正式路径 | 实现负责人及白名单 | 依赖和接口 | 验证方法 | 用户场景 | 完成条件 |
|---|---|---|---|---|---|---|
| HB01–06、10 | Store／Manager／load-save、CLI／UI slash与session.control、后台scan→自身tip→native UI submit | heartbeat_ui_runtime；Heartbeat源码及相邻store/route、自有schema、必要lazy入口、对应tests；不改文档/其它dirty | 前轮模板及UI runtime保留；目标Profile和稳定ref | 真实DB、原生入口、并发／取消屏障、关闭分支；目标Profile和源身份核对 | 两Conversation独立管理、压缩／fork、Gateway切换、关页回收、重启 | 机制、接线和失败边界均有证据 |
| HB07 | 集成已授权failed_turn标记与冻结前端`0b8843f`包 | 主会话亲审／最小接线；根三文档、07、运维记录；不改未授权Android | backend已授权4文件原有测试；前端包SHA／源树绑定 | 复用有效原版本证据，集成差异定向验证；固定产物清单 | XML卡片、失败卡片及审批展示与后端兼容 | 包与源码/构建证据对应 |
| HB01–10 | 独立Verification | 新fork_turns=none sol/high；只写verification.md及ignored证据 | 全部集成收敛，判据先于代码 | 独立规格→实现→证据；必要反证，不复跑大套 | 全范围条款 | 无范围内违规／证据不足 |
| HB01–10 | 独立Validation | 另一新fork_turns=none sol/high；只写validation.md及自有隔离环境 | Verification通过，场景计划先交主会话过目 | 实际合法公开入口用户旅程；复用真实模型接口证据 | 设置／切换／关页／恢复／暂停清除等完整链路 | 全适用场景通过 |
| HB07–08 | 首尔发布及Alex置顶正式设置 | 主会话；SSH seoul，仅指定服务／目录／目标ref | 两门禁通过，当前版本和空闲确认，线上备份 | 原库／配置指纹；源/dist SHA；health／Gateway连接；正式read-back | 新版可用且目标Heartbeat已登记 | 当前版本上线、7200s/空prompt、其它状态保持 |

## 当前状态与编排

| 目标/任务 | 机制实现 | 正式接线 | 针对性验证 | 用户结果 | 当前负责人和下一步 |
|---|---|---|---|---|---|
| Conversation Heartbeat | 已亲审集成 | 正式控制／后台UI宿主已接 | 156项有效定向，修补27复测/10检查，2独立负例 | 真实serve自然到期/停重启及管理通过 | 已发布ed94619；后置最终收据补审通过 |
| 发布输入 | 固定前后端及产物 | f32首次/ed补发已执行 | 前端917通过/1skip，439文件SHA逐个一致 | 双SPA/关键资源200，微信connected | 生产收据已取回 |
| 两门禁 | 新独立全范围复审前置通过 | 36条判据/18场景覆盖 | 三Home六进程/253帧，新模型0；未变真实路径证据复用 | 实际新note及原生en/zh逐字对照通过 | 两独立角色最终门禁关闭 |
| 首尔及Alex设置 | ed94619与固定0b8843f已上线 | Alex正式set后补发版只读核 | 保护表含Heartbeat全行SHA，原定义/锚点未变 | active/7200/空prompt/count0；19:58:09到期 | 不重set、不提前模型Turn；最终收据补审通过 |

主会话负责全局覆盖、review、独立宿主证据、冻结和部署；实现Agent负责完整实现，不在其并行修改区重复实现。其它前端任务只读既有提交及包。真实默认测试cwd在repo外。

## 缺陷与整改

| 问题编号 | 要求与触发条件 | 当前事实与影响 | 优先级及理由 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|
| HB-GAP-01 | HB04–05，前轮Session归属 | 已接Conversation自有表及自身tip路由 | P1，核心缺口 | 主会话／两门禁 | 真实serve断连、close、148.58秒停机恢复及暂停/清除跨重启通过，见Validation S04–08 | 已关闭 |
| HB-GAP-02 | HB04–05，正式设置回执 | 首次线上RPC仍打印只在当前进程有效的原生note；两门禁漏查该实际可见文字 | P2，误导持久化语义，阻断最终交付 | 主会话 | 已做全局分支提示修补，27项定向/10检查通过；新独立全范围复审和实际RPC输出复验后再补部署，保持原7200排期 | 已关闭；新独立全轮36判据／18场景及最终收据补审通过 |

## 取舍、快照与续接

本轮是在已有实现上追加自主授权，不重做前轮模板工作；baseline冻结文档及实际用户授权，前轮源码dirty保持到集成快照。冻结规则/阈值以AGENTS为准，不因门禁改变。每次commit自动push；仅暂存当前明确范围，不整树add。实际部署版本／源码hash／前端SHA及备份回执在此记录。

集成快照：`f32d70f703fd8995f6652ca71ff72ef0d56d535e`，自动push与ls-remote一致；最终31文件冻结10检查通过，16文件154项有效机制测试。主会话2次本轮真实K3-256k/High接口样本HTTP200（空/额外prompt），证据`.hermes-dev/conversation-heartbeat-20261021/evidence-index.json`。这是初始快照时点：当时Verification尚无修复要求、发布输入只已上传；随后发现回执缺陷并按下段修补；前端归档SHA`89e05ae6de4ea4d716f31f9202a58069e1e2ec27738bb7bd5808d47da1eb3458`，后端增量bundle SHA`7d88ddf519f9971c94f2da5023e75613b58f0e6a5cd7fa6ccf98674168108cd0`。

修补快照：`ed94619da81547bcb9e27aab60b608b2310e6890`已自动push；4文件冻结10检查health0，27项定向通过。新独立Verification重新建立36条全范围判据，前置31条符合、5条真实生产事实按顺序后置；旧成功note缺陷本地关闭。新独立Validation已独立制定18项计划，主会话完整过目后授权执行；零新增模型、三个隔离Home/六进程/实际HTTP/WS及新进程管理，未变机制的旧真实证据逐项核复用。补发版bundle SHA`3a255b31e99bffa8a7151844308923bcda0aedb9ee4d5015e52adb2158f81507`；上线后只读对账原Alex定义，不重设19:58:09锚点。

最终运行收据：`.hermes-dev/conversation-heartbeat-20261021/{deployment-receipt.json,post-release-readonly.json,alex-heartbeat-final-readback.json}`。18:21:17开始补发版快照，当前源码ed94619、前端439文件、Web/Gateway active/running且NRestarts0、微信connected。三库保护表/配置/绑定保持；Alex创建时间1792576689.5657868、last_fired_at0、revision1、7200/空prompt/active/count0和next_due1792583889.5657868均未变；未重set。

最终判定：Verification R2-01–36全部符合、Validation R2-U01–18全部通过，HB-GAP-01／02及所有后置项关闭；本次完整复审无新增整改。主会话已读最终报告、原始关键证据及生产收据，交付见final-delivery.md。范围内目标已达成，本轮文档随交付归档并关闭持续目标；不追加测试或重设Alex。
