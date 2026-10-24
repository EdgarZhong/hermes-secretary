# 本轮实施计划：20261024-web-recovery

## 目标与依据

以snapshot-index.md和baseline.txt定位冻结06 §1.4.1 R1–R10；实现页面范围完整恢复、过渡展示缓存、渲染需求统一交接及APK5秒恢复。先贯通后端范围／cut→前端恢复→可见交接，再做视觉和原生链路。全部使用gpt-6.1-sol/high，主会话亲审；不再调用Astra。

两仓工作区原始代码：主仓5ea0f7fbaaa14df2d2b40c6cb0140cd2dda3eac4，前端f3a03ce32c0dd1e96719da210716caa2c1c7b8d4。原dirty均为文档，其他任务的07／部署／运维／调查文档与CLAUDE非本轮片段留原地；ignored备份与证据放主仓.hermes-dev/web-recovery-20261024/。新分支codex/web-recovery-20261024，两仓分别提交、自动push，不自动merge／部署。后端只用项目.venv及scripts/run_tests.sh；前端npm、既有JDK/SDK/NDK。hooks已安装、可执行且与仓库模板一致，保留不重写。

完成条件：C01–C16均有同版本证据；正式接线与关键竞态定向测试、构建、独立轻量Verification和Validation闭合，主会话交付final-delivery.md。轻量意为精炼报告／复用有效证据／必要反证，不降低判据。不跑真实模型；UI只使用自建隐藏IAB。原生真实UI与显示保护有冲突时保留未验，不伪造通过，先推进其它全部可做工作。

## 覆盖与任务

| 要求/口径编号 | 任务和正式路径 | 实现负责人及白名单 | 依赖和接口 | 验证方法 | 用户场景 | 完成条件 |
|---|---|---|---|---|---|---|
| C02/C04/C09/C11 | B1–B3 后端范围读、原子cut、activate恢复封套及变更失效 | backend：06 R9的B1/B2/B3精确文件；不改其它产品、schema或核心文档 | 输出可选v1 DTO、真实fixture及失败语义供frontend；B2/B3同一owner串行 | 真实SQLite、并发／跨进程破坏变化、原接口兼容、项目定向测试 | REST/WS交错，深anchor、rewind/压缩、持续Turn | R2/R3有界证明及正式REST/RPC接线 |
| C01–C05/C09–C11 | F1/F2/F3/I1 前端协调、coverage、缓存、reader及Controller/App集成 | frontend：06 R9 F1–F3/I1全部前端文件、对应测试；独占src/api/types.ts/client.ts、controller.ts/App.tsx/projection.ts/render-store.ts | 先输出page-recovery公共类型／接口契约，接backend真实DTO；调用presentation导出的需求／动画及Android桥 | FakeIDB、真实controller恢复及消息回放、失败/取消/owner/缺口、typecheck/build | 冷开缓存、同值、完整重请求、可见就绪提交、后台慢不挡 | 无缓存捷径、正式生命周期全覆盖、单次可见提交 |
| C04/C06–C08/C11 | F4/A1 视口／facet／Files、阅读衔接／胶囊高亮及APK桥 | presentation：06 R9 F4/A1精确文件；不改App/controller/types/client；可新增独立展示需求桥模块及测试 | 消费frontend公共契约，输出组件hooks/props供其I1；Android packet按R8、回调桥供frontend使用 | 阅读锚点／输入取消／降动效、原生Robolectric、JS桥测试；UI由Validation统一验 | 前缀平滑、侧栏原地、胶囊高亮、4.9/5秒/旧ready/online | 动画不竞争instant、Native只信本轮可见ready |
| C12/C13 | V 独立Verification | 全新6.1/none，只读产品，写verification.md | 集成收敛，先冻结原文独立建判据再看代码证据 | 精炼逐条覆盖＋必要反证；不复跑已有效大套 | 全范围机制／接线／边界 | 无违规或必要证据缺口 |
| C12/C13/C15 | U 独立Validation | 另一个全新6.1/none，只读产品，写validation.md及获准证据 | V通过；先交场景清单供主会话过目 | 隐藏IAB实际操作、复用有效机制证据、平台边界如实 | 冷开／重连／rewind／stream／动画／Files／APK | 全部适用场景通过或有依据不适用 |

## 当前状态与编排

| 目标/任务 | 机制实现 | 正式接线 | 针对性验证 | 用户结果 | 当前负责人和下一步 |
|---|---|---|---|---|---|
| B1–B3 | 未开始 | 未开始 | 未执行 | 未验 | backend待派；先产真实DTO契约／fixture后整包交回 |
| F1/F2/F3/I1 | 未开始 | 未开始 | 未执行 | 未验 | frontend待派；约定公共接口成包里程碑，随后持续实现 |
| F4/A1 | 未开始 | 未开始 | 未执行 | 未验 | presentation待派；先读共享契约，接口等待时可独立原生实现 |
| V/U | 未开始 | 不适用 | 未执行 | 未验 | 集成完成后按轮派，不按子包逐个审 |

主会话独占本轮内部文档与两仓根核心文档，源码全部由6.1子Agent修改。三个实现包并行白名单互斥；共享DTO经正式契约里程碑协调，不并行改相同文件。各实现者不再派生、不提交、不部署；禁止流水账，只有真正跨包接口／产品阻断、约定契约成包或最终交回才发消息。报告写入本轮reports/各包.md，含七项交回及证据定位；证据位于主仓ignored目录，日志不进Git。主会话亲读实际diff和上下游，不以复跑测试代review。

集成顺序：backend DTO与frontend公共契约→frontend与presentation正式接线→主会话review→6.1集成修补→相关集成验证／构建→V→U→交付判定。必要大型检查一次统一安排，重复仅因代码变更、失败修补或证据存疑。实际包状态与缺陷在此持续更新。

## 缺陷与整改

| 问题编号 | 要求与触发条件 | 当前事实与影响 | 优先级及理由 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|
| RISK-01 | C15 原生真实UI验收与显示保护 | 当前规则只许隐藏IAB，实际APK生命周期不能以Robolectric替代 | 交付证据风险 | 主会话 | 核获授权环境／可行隐藏路径；否则明确边界并获得所需授权 | 待核 |

## 取舍、快照与续接

2026-10-24用户明确授权按定稿启动自主轮，全部6.1、允许委派、亲审集成、测试验收后交付，独立门禁轻量；不扩大发布范围。已有方案R1–R10为执行依据，不重开Astra。冻结提交哈希写baseline.txt；阶段快照记录验证范围、未完与push状态。不得提交其他任务dirty，尤其07与其CLAUDE片段；本轮核心CLAUDE片段按索引入冻结提交。
