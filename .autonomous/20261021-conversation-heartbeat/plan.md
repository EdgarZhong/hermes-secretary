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
| Conversation Heartbeat | 实施中 | 待整包 | 实施者构造 | 待独立验收 | heartbeat_ui_runtime，不派生／不提交 |
| 发布输入 | 前端包与commit已定位 | 后端待集成 | 前轮前端917通过/1skip，已固定构建；failed_turn既有38/14项 | 未部署 | 主会话核对包清单、保护基线 |
| 两门禁 | 未开始 | — | — | — | 集成收敛后顺序派遣 |
| 首尔及Alex设置 | 尚未实施 | — | — | — | 两门禁后发布；不得提前模型Turn |

主会话负责全局覆盖、review、独立宿主证据、冻结和部署；实现Agent负责完整实现，不在其并行修改区重复实现。其它前端任务只读既有提交及包。真实默认测试cwd在repo外。

## 缺陷与整改

| 问题编号 | 要求与触发条件 | 当前事实与影响 | 优先级及理由 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|
| HB-GAP-01 | HB04–05，前轮Session归属 | 尚无稳定Conversation存储，Gateway切换仍清native键 | P1，核心缺口 | 实现Agent | 正式控制＋无页面后台恢复完整验证 | 实施中 |

## 取舍、快照与续接

本轮是在已有实现上追加自主授权，不重做前轮模板工作；baseline冻结文档及实际用户授权，前轮源码dirty保持到集成快照。冻结规则/阈值以AGENTS为准，不因门禁改变。每次commit自动push；仅暂存当前明确范围，不整树add。待部署版本／源码hash／前端SHA及备份回执在此续接记录。
