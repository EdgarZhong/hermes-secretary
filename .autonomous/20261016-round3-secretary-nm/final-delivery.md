# Final Delivery：20261016-round3-secretary-nm

## 目标状态与结束判定

**用户本次要求的主仓库第2次Verification已完成，产品门禁不通过。** 固定待审产品 `b40fa1ff2a771066b4da1d8978a7abe44327e530`；报告在main现有提交之后向前提交。四项新不符合有当前实现反证，F16最新Prompt及output-cap恢复窄分支仍有必要证据缺口。此为审查任务的完成，不是整轮产品交付完成；产品整改、再次独立复审及Validation仍待完成。依据：[snapshot-index.md](snapshot-index.md) R3-023、[baseline.txt](baseline.txt)、[verification.md](verification.md)。

## 本轮收敛与授权

用户要求继续主仓库第三轮第2次Verification、 findings写仓库并提交main；据此进入此前R3-020～022要求停在门禁前的下一阶段。本次范围为公开Hermes Secretary及其个人隔离边界，没有新增产品口径或修改权威规格。原来源先结算、Candidate后处理及Prompt体量要求继续有效，未要求用户重新批准既有语义。

## 已完成与交付物

三个全新审查上下文独立提取、核对87条细分要求，映射公开V01–V51/V52公开部分。正式报告沿原verification.md六节追加，首审各节原文和历史方案评审保留；同步根CLAUDE、原plan、snapshot-index、baseline。并行写入的verification-2.md只加当前报告入口，原静态结论保留。四个反证脚本、原始失败日志、合法对照、来源观察及版本哈希保存于 [evidence/verification2](evidence/verification2/README.md)。没有产品修复提交。

提交准备确认main已由并行更新从规划c099c8c快进到产品b40fa1f，再追加da68703/de810ba两份文档更新；本次保留后者，并在其后继续提交。报告提交不改变被审产品版本，不把集成或同步当发布/验收。

## Verification 与 Validation

Verification：公开规格全文及明确保留旧条款、正式同步/并发/失败/恢复路径、旧问题影响与新反证均逐条记录。主会话亲读脚本和输出：来源4F、退休名2P/1F、ContextEngine1F、Scheduler恢复1P/1F，合计3P/7F/10用例，四次canonical runner合计8.7秒，固定PM Python3.14.7/Linux/原锁。两次收集前沙箱退出单独留证。模型/时钟/engine依赖受控，数据库、正式Store/绑定工具或原生loop实际执行；不冒充新真实DeepSeek运行。

旧公共V51、F17/F18/F19/F20修复按具体证据范围接收；旧33回归失败/错误已有逐节点定向处理，六个相关测试源码与报告哈希、锁亲核一致，原始全量失败保留。F19更晚35邻域及新schema真实链已补，不再将早期“未执行”延用为当前缺口。原ignored模型/DB/日志未在本环境回放，未重跑大型回归或十类检查。

Validation：现有15组计划仍全部未执行，本次未启动独立用户验收。公开门禁未通过，个人Provider未在本次审查，不代签个人新版结果。真实NM、UI和部署边界保持。

## 剩余、阻塞与影响

| 项目 | 对用户结果的影响 | 恢复条件/责任 |
|---|---|---|
| V2-F01 隐藏来源 | 当前Notebook可能持有History无法取证的新条目来源 | Notebook/History owner统一可读真值，四反例及合法来源正例关闭 |
| V2-F02 旧名执行 | 规格已退休工具名仍可真实写入Notebook | dispatch owner修raw repair边界，原始名称到最终Snapshot复证 |
| V2-F03 冻结前缀 | 配置native ContextEngine时后续Noting请求可改变已冻父消息 | runtime owner在最终请求保护冻结段，保Main能力，逐请求复证 |
| V2-F04 恢复排期 | 提前恢复周期提醒可跳过下一次发生 | Scheduler owner修future occurrence推进，持久list与原生语义对照 |
| V2-E01 / F16 | 已成功交付来源正文仍缺最新版正确结算证据，可能持续占簿 | 固定修复SHA的round3完整真实链，明确成功覆盖退出及剩余保护；无须真实NM |
| V2-E02 output-cap | 该原生错误恢复的child禁压缩/冻结约束尚缺正式路径证据 | runtime owner受控provider错误穿过真实恢复链，按观察修复并关闭 |

下一步是按plan §13整改和补证，随后再次独立复审。当前没有因权限/凭据失败而搁置已获授权的审查工作；这次停止是审查任务已完成并交回不通过结论，不是将整个原产品目标标完成。

## 用户复核建议

先看verification.md §5六个未关闭项，再看§6旧问题处置和§2/§3完整覆盖。四组原始输出可在证据目录直接核对，日志中的失败断言与正式参数/数据库结果对应；复现走该目录README中的canonical入口。关注F16时同时比对40f4ecc末次真实结果与b40fa1f Prompt改动，不能只看最新词句或Candidate数量。修复完成后以新的产品SHA记录证据，不覆盖本次失败。

此前final-delivery在b40fa1f中的额度收口历史可从 [固定旧版本](https://github.com/EdgarZhong/hermes-secretary/blob/b40fa1ff2a771066b4da1d8978a7abe44327e530/.autonomous/20261016-round3-secretary-nm/final-delivery.md) 回读；其中早于R3-022补证的“未执行”不是本次当前状态。


---

# 2026-10-18 真实使用 Validation 接续（覆盖上文历史阶段状态）

## 目标状态与结束判定

**本阶段实测、已确认接入Bug修复及定向复验已完成；整体Validation仍NOT PASS，尚未完成整轮或正式云端部署。** 用户明确以实际使用功能验证优先、推迟静态Verification。主会话按产品负责人组织场景和取舍；两个新Profile已在本机5174/53446运行，首轮完整旅程及两次定向复验已完成。VP-01自动Thread归档与VP-04自动Recall已取得修后真实证据；当前需用户决定VP-02相关Prompt调整，用户明确禁止擅改框架Prompt，因此先交报告与具体建议，不继续修改该部分。本文为当前交接状态，不以历史静态失败重新阻断用户已授权的功能实测。

## 本轮收敛与授权

按R3-024～035及用户后续要求：主助手Default只读、考研助手使用“考研复习”Space；两个Profile开启Noting/Scheduler，主助手经NM跨领域跟进，不读取另一个Hermes Profile。现实10分钟作为测试一天，每条普通用户消息附测试角色/时间窗口。SOUL来自用户身份及产品愿景资料，未继承旧Pi写权限或任务。框架硬编码Prompt未改，测试Persona/配置可调。两个Profile联合Idle Compact + Noting均enabled、100000-token阈值、5秒idle，模型上下文262144保持；实际未达到阈值，不冒称自动触发已验。

## 已完成与交付物

- 三份核心文档精简并保留历史快照；AGENTS新增禁止流水账规则，每次派遣再次强调整包一次交回。动态编排只在根CLAUDE。
- 首轮真实DeepSeek：双SOUL/Notebook、暂缓不写/批准后限定Space写入、跨压缩及同Profile跨Conversation查原话、两次600秒窗口cold/warm跟进均有正式入口证据。F16现行样本实际先处理来源再归档Candidate，未覆盖事项保留。
- 自动归档开关与Bundle官方CLI接入修补已review/安装。Recall两Profile从默认2秒调为已有配置上限5秒；第一次定向复验3个真实Turn的api_content均无不可用提示，考研一条带实际Memory指针，无新增超时。只证明本样本，不保证未来网络延迟。
- 自有未来排期、runtime/poller/lease已回收；Profile、Conversation、Notebook、1条合成Memory、1个考研Thread及本地服务保留供复核。Default未观察到写入；SOUL/终端授权不冒称OS或服务端只读沙箱。

## Verification 与 Validation

静态Verification按用户明确要求推迟，旧正式二审NOT PASS及剩余发现保留。本阶段没有宣称两个门禁均通过，也没有重复大型suite。

独立6.1/high执行者经实际Web UI/真实模型/正式工具取证，首轮P01–P07与两段真实600秒窗口；仅补VP-01/04接入链。报告[validation.md](validation.md)保留首次失败与复验。Thread窄修的真实CLI→fixture20 PASS不代替真实NM；首次补丁真实失败后，确认首批误用checkpoint导致thread_not_found，新反例3 RED→定向7 PASS。第二次正式聊天首批22条→同Thread后续24条，receipt/正文/旧前缀一致，关闭后仍24条无重复；root亲读两份一致性/最终状态证据接收。没有将受控结果或诊断调用冒充正式业务通过。

未测K3、现实24小时或长期生活表现、100k自动Idle触发、云端/手机部署；本轮不扩展全部历史V01～V15真实场景。DeepSeek只作代理模型，实际工具和存储结果优先于模型自述，不据其建议直接改产品。

## 剩余、阻塞与影响

1. **VP-01自动Thread归档：已关闭本次失败场景。** 正式聊天首批及suffix、ACK收据、同Thread/Space和关闭后无重复已有证据；网络丢ACK/跨端点竞争等未扩展为新的真实测试，不宣称长期exactly-once。
2. **VP-02来源交付：** 真实写入用了直接CLI，缺Hermes来源Metadata；提案未按07 §8.10回读原文及带内容类型标签。来源先结算样本通过不覆盖该缺口。框架Prompt未获修改授权，保留问题及下面建议，不通过测试SOUL灌答案刷绿。
3. **行为观察：** VP-03自述参数与实际不符，以工具轨迹为准；VP-05无新增仍汇报受到测试输入“安静”与“无记录也说明”两句张力影响，暂不认定代码Bug，不擅增通知规则。
4. 旧静态缺陷/全量混合工作区失败及未验证平台仍在CLAUDE，不用本次功能样本覆盖。现有他人未提交代码保留，个人实现不并入公开核心。

**待用户决定的Prompt建议：** 保持简短，在个人NM常驻指导中明确“已批准的新Memory先加载nm-cli流程，携带核实后的来源和内容标签”，并清除该Skill中过时的本轮禁写/未实施说明。依据是当前常驻提示泛称官方CLI，而带来源helper位于Skill、Skill残留旧阶段权限描述；这是可见指导不一致的审查发现，尚未证明它就是本次模型选择的原因。公共提案本已有查源/标签要求，先不叠加长篇规则。helper的Metadata真实联网能力也未被本次直接CLI写入证明，不能承诺只改一句Prompt即可全部关闭。

## 用户复核建议

打开本机 http://127.0.0.1:5174 ，查看主助手/考研助手已有Conversation、Notebook与两条已完成提醒；考研Space保留唯一带合成声明的Memory。环境清单、SOUL版本、实际请求/结果及资源清理证据在ignored `.hermes-dev/validation-personal-20261018/`；公开报告不复制私人正文或凭据。下一步由用户决定下列具体Prompt修改后，再做来源交付的短链复验；本阶段实现/环境/实测Agent均已整包交回，无后台模型测试继续运行。


### 待批准的最小Prompt改动

位置仅个人Provider的NM常驻guidance及对应PHASE3原文：在原官方CLI管理说明后加入一句：

> For approved new Memories, load nm-cli and use its provenance helper with verified sources and inherited content labels.

同步删除nm-cli Skill末尾过时的“本轮未授权真实写入”等阶段说明，保留审批、来源与部分失败处理规则。公共07已有查源/标签要求暂不增字。此提案尚未实施，也不承诺单句即可解决模型行为；获批后定向观察真实提案/来源交付，并据真实结果决定是否还有代码接入缺口。暂停该改动的依据是用户明确要求“框架里写死的prompt……未经过我授权，不要擅自动手更改”。
