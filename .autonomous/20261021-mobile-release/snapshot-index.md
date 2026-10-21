# Snapshot Index：20261021-mobile-release

## 审查依据索引

| 输入类别 | 实际仓库文件路径或本文件位置 | 修改等级 |
|---|---|---|
| 用户需求 | .autonomous/20261021-mobile-release/requirements.md | 二级 |
| 权威规格 | docs/06-Hermes-Secretary-Web-UI-V1-Spec.md：§0.4–0.5原生与增量边界、§1 Android通知／壳／图标、§2 Timeline阅读与新增提交／Heartbeat修复契约；docs/08-profile-scheduler-files-clarification.md §1–1.1 Profile与绑定；docs/07-scheduler-notebook-noting-compaction-redesign.md §8.15 Heartbeat现行契约 | 二级；本轮只修对应故障，不扩展其它能力 |
| 编码指导 | AGENTS.md；README.md稳定环境／入口；CLAUDE.md仅在判据落盘后作为当前编排，不作为独立判据来源 | 二级；未改README／AGENTS已在冻结树内 |
| 会话确认口径 | 本文件“口径与决策” | 二级 |
| 本索引 | .autonomous/20261021-mobile-release/snapshot-index.md | 二级 |

冻结文档完整提交哈希写 baseline.txt。实现与证据版本另由plan登记，不能用旧历史报告代替本次代码结果。全部依据二级；已有用户口径变更立即同步，主会话没有自行扩范围／生产权限。

## 口径与决策

| 口径编号 | 用户意图、确认结论或约束 | 决策理由及确认假设 | 用户消息定位与授权来源 |
|---|---|---|---|
| C01 | 覆盖R01–R13全部问题后统一构建，不赶包跳过修复 | 用户明确先修好／测过再准备上线 | “不着急打APK，先确保以上修复都已经完成”；最新统一dist与APK授权 |
| C02 | 壳提供380 CSS px逻辑视口、等比显示 | 380是用户最后明确选择，覆盖390 | “看了一下，还是380吧” |
| C03 | 通知新响铃＋横幅通道，保留可识别主动静音 | Android通道不可原地提高重要级，用户已选择迁移 | 本会话异步确认原话见R09 |
| C04 | 旧Kimi工具行为调查关闭，禁止改旧历史／排期／root | 用户自主放弃旧会话，显示故障调查不重开模型实验 | R14所引用户消息 |
| C05 | Sol/high分包实现与复核，主会话最终集成 | 后续委派授权覆盖此前“不再派extra”；仍不用Astra／Extra | R15与用户“托管执行” |
| C06 | 复用已有真实DB／native loop／真实SDK及同版本证据，补集成与失败边界；UI禁用如实记未验 | 不重复昂贵大套，不把组件／MockTransport当真实设备／Provider验收 | 根AGENTS、R15与用户要求“测好没有问题” |
| C07 | 托管范围包括本地阶段提交（根规则每commit自动push）、构建dist与APK；不主动向生产发送测试消息，不修改Profile／绑定／排期 | 既有技能默认本地阶段提交与用户明确打包授权；准备上线尚非实际部署指令 | “打包…”、“你托管执行，我先去吃个饭”及AGENTS |
| C08 | 凭据、签名私钥、私人消息／真实生产回放原件保留ignored，禁止进入Git或交付公开包 | 保护既有资料与公共核心边界 | AGENTS；测试只用虚构内容 |

未决事项：没有影响本地实施的产品口径待确认。环境缺口是隐藏IAB不可用及无获授权可用真机UI入口；最终呈现验收不得伪造通过。实际部署不在本轮自动执行范围；不触碰旧Kimi模型行为。
