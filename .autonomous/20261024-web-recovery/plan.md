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
| B1–B3 | 已交回、亲审中 | 已接正式REST／RPC | 新REST8＋RPC24及相关回归；旧catalog失败冻结复现 | UI未验 | 主会话核最终代码与证据，后续独立门禁 |
| F1/F2/F3/I1 | 整包已交回，亲审整改中 | Controller／App全部已接 | 17文件246项＋typecheck/build通过；最终小修待补证 | UI未验 | frontend修有序前缀、局部失败自动重试和侧栏读过滤后主会话复核 |
| F4/A1 | 已交回、亲审中 | 已交frontend接口，待整体核线 | 展示96、原生40通过；共享版本需核 | 实际APK／UI未验 | 主会话核最终代码、manifest与前端影响 |
| V/U | 未开始 | 不适用 | 未执行 | 未验 | 集成完成后按轮派，不按子包逐个审 |

主会话独占本轮内部文档与两仓根核心文档，源码全部由6.1子Agent修改。三个实现包并行白名单互斥；共享DTO经正式契约里程碑协调，不并行改相同文件。各实现者不再派生、不提交、不部署；禁止流水账，只有真正跨包接口／产品阻断、约定契约成包或最终交回才发消息。报告写入本轮reports/各包.md，含七项交回及证据定位；证据位于主仓ignored目录，日志不进Git。主会话亲读实际diff和上下游，不以复跑测试代review。

集成顺序：backend DTO与frontend公共契约→frontend与presentation正式接线→主会话review→6.1集成修补→相关集成验证／构建→V→U→交付判定。必要大型检查一次统一安排，重复仅因代码变更、失败修补或证据存疑。实际包状态与缺陷在此持续更新。

## 缺陷与整改

| 问题编号 | 要求与触发条件 | 当前事实与影响 | 优先级及理由 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|
| RISK-01 | C15 原生真实UI验收与显示保护 | 当前规则只许隐藏IAB，实际APK生命周期不能以Robolectric替代 | 交付证据风险 | 主会话 | 核获授权环境／可行隐藏路径；否则明确边界并获得所需授权 | 待核 |

## 取舍、快照与续接

2026-10-24用户明确授权按定稿启动自主轮，全部6.1、允许委派、亲审集成、测试验收后交付，独立门禁轻量；不扩大发布范围。已有方案R1–R10为执行依据，不重开Astra。冻结提交哈希写baseline.txt；阶段快照记录验证范围、未完与push状态。不得提交其他任务dirty，尤其07与其CLAUDE片段；本轮核心CLAUDE片段按索引入冻结提交。

冻结已提交并自动push核同：backend ba83d2b430e3448461dd7feb9f1acd8fc94c6cc9，frontend 9fd115d3b016bb51a8a78dd1724684fd1890665c。baseline.txt随后随阶段快照纳入Git。现SDK/JDK就绪，无在线adb设备；本轮此前未跑基线全量测试。


### 实施中批准的最小接口补充（工程细化）

- 后端生成产物扩白名单为`apps/shared/src/gateway-contract.generated.ts`和`gateway-contract.openrpc.json`，仅由现有生成脚本更新可选兼容契约。
- 跨进程同条数历史替换／内容编辑不会改变既有sessions签名。允许在`hermes_state_messages.py`的`replace_messages`、`set_user_message_content`及`hermes_state_secretary_foreground.py`的`secretary_set_user_content`成功且实际变化后，经小型`hermes_state_history_notifications.py`做best-effort通知。通知按真实db_path归属，现change_watcher将通知文件stat纳入签名并沿sessions.changed唤醒；通知失败不破坏写入。不传正文／凭据，不新增schema，不改变活动时间／rewind语义，不把通知当coverage／一致性证明，不因任意DBmtime刷新历史。补跨进程、Profile隔离和通知失败反例。
- presentation扩白名单`src/components/FileViewerPreview.tsx`，只增加可选`onRecoveryState`回调，传真实渲染loading／ready／error。Files ErrorBoundary不能替代内部渲染器错误，失败不算ready；不改用户视觉或渲染器行为。
- 主会话已review前端公共契约初稿，要求覆盖需求撤除后慢资源不挡、新facet／Files路径／失效后的读代次重建、迟到结果不能满足新需求；整包交回时以行为证据核对。


### 主会话实施中亲审记录（尚非整包验收）

已读前端协调器、缓存、范围窗口、视口需求及后端D0/S/D1和事件切点的初稿与正式接口接缝；向原6.1实现者交回以下核对，整包及独立门禁须以最终代码／行为证据确认关闭：

| 编号 | 初稿风险与要求 | 负责人 | 当前状态 |
|---|---|---|---|
| REV-01 | 撤除慢需求不挡；resource身份／代次防旧结果满足新需求 | frontend | 已反馈，待最终证据 |
| REV-02 | 缓存嵌套原生content中的图片binary／data URL不得落盘；损坏rows/capsules可靠丢弃 | frontend | 已反馈，待最终证据 |
| REV-03 | tool-only视口不能因alias未匹配而空集判相容；已展示facet参与前缀判等 | frontend＋presentation | 已协调，待最终证据 |
| REV-04 | 同轮dirty历史失效不得复用旧成功读取；commit→需求变更→layout ack不死锁 | frontend | 已反馈，待最终证据 |
| REV-05 | settled idle snapshot在恢复前正式replace／rewind／delete后不得复活旧输出；未知未持久输出须当前Turn证明 | backend | 已反馈，待反证／修复证据 |

后端契约整包已接收：reports/backend-contract.md与真实SQLite正式handler fixture；其定向检查初报107通过／1条未emit的review.summary旧catalog失败，已要求冻结代码隔离复现，未据此认定新版全绿。主会话不复跑有效测试来代替review。

隔离环境：已有53445／53446不动。本轮Dashboard53575（session44012）、fault proxy53576（session56855）、Vite5178（session8438）已启动，health／入口200。home与seed均在ignored本轮backend目录，workspace在仓库外；不发送prompt。Dashboard正式--isolated＋--skip-build避免附着原进程及无关管理页构建。

环境纠偏：首次Dashboard启动遗漏skip-build，触发未修改原生管理页源码的本地静态构建；中断后留有部分已清理backup（15文件），逐SHA核均与新完整web_dist同名资源一致。残留已移入ignored native-ui-build-leftover保存，不用不完整backup回盖完整产物；后续明确skip-build，无源码／生产部署或用户进程变更。

主会话后端亲审完成首轮：正式REST/RPC调用、D0/S/D1锁序与固定区间重读、idle旧输出／tool occurrence处理、writer通知与真实db_path归属、生成契约及失败边界已核。18个本轮源码／测试／fixture文件已明确暂存，不含他人文档。主会话运行冻结10检查全部通过（staged-ten-checks.log），health15文件对原代码5ea0f7f为0 blocking／0 advisory；尚待独立门禁，不作整轮完成判断。

APK环境补查：PackagedWebViewClient.ORIGIN及isHermes固定生产HTTPS域，Rust启动URL同源，无既有本地后端切换配置。不能把正式包直接启动后访问生产作为隔离验收。RISK-01还需同时解决显示保护及测试流量隔离；不为验收擅改正式origin／扩大生产访问。待可审APK构建后再处理权限／必要证据边界，先完成独立可做工作。


整包亲审追加：
- REV-06：viewport.visible分支逐项find缺有序LCP，重排可能误判兼容；同UID正文／Thinking需按kind正确匹配。已交frontend最小修及重排／同UID／append反例。
- REV-07：恢复后局部依赖失败只ready=false，缺1/2/5自动重试；要求局部保画面、自主补读失败资源，撤需求／断网／隐藏／owner取消，不整页重冻。
- REV-08：侧栏缓存读侧也需摘要白名单，损坏条目额外runtime/running字段不得恢复；成功时间不能因过滤或访问更新。
- 先前REV-01～05已由整包实现与证据说明修补，主会话已核最终协调器／缓存／cut代码，仍由独立门禁复核。首次高亮真值补hasData接缝及App实际显示字段签名已接，原生包相关证据更新。

主会话实际隔离只读探测：REST recovery_view200／200行、原生roster1且path全在本轮home、session.resume能力v1／idle成功；无prompt／模型调用。后端与前端fixture正式接口形状一致。

集成候选：前端c4f2f6d已提交并自动push核同；主会话已核REV-06～08最终代码及相应行为证据，frontend两个最终manifest全匹配、两仓真实fixture逐字节一致。三包代码已稳定，正式冻结候选后开始独立门禁与APK构建；不宣称验收已过。
