# Final Delivery：20261021-mobile-release

## 目标状态与结束判定

**受限候选交付；整轮目标未完成，阻塞于真实Android证据。未部署。** 本轮代码修补、正式接线、开发期回归及最终统一构建已收敛；独立Verification最终19条为17符合、0违规、2证据不足，正式Validation前置未通过，尚未启动。不能把原生测试、构建和浏览器组件补证视为真机或完整App验收。

冻结依据：[Snapshot Index](snapshot-index.md)、[要求](requirements.md)、[当前计划](plan.md)，冻结提交`57ffa1c355b4eef9b73f6ab10d3fb6da42b43176`。实际后端产品快照`3b48cf0baeb3c49bb96849d24c6105bf6e39e6fc`，Web／Android源码`bf279b2dc5ec5553ff9e370696b153e4aadb52cd`，均已提交并推送。恢复条件是取得符合显示保护的真实Android验收入口，补齐F01/F02后再独立复核并启动正式Validation；上线另需明确部署授权。

## 本轮收敛与授权

按用户本轮确认C01–C08收尾：旧置顶Kimi调查及恢复关闭；Android壳提供380逻辑视口并等比显示，覆盖390；升级迁移新的响铃＋横幅通道并尽量保留主动静音；保留完整且尺寸合适的logo，无白边；全部前端修好后统一dist与递增版本APK。采用既有Sol/high分包，主会话亲审集成；没有再重开Astra／Extra或旧会话调查。托管不扩大为生产消息、Profile／绑定／历史／排期写入或服务部署。

两项有实质影响的工程细化均沿既有契约，未新增产品语义或待追认项：

- F03：发布前失败允许真实持久行回调恢复；已经进入原生replay后，即使传输返回False或随后异常，也按真实replay去重。主会话发现发布标记过早，子Agent修正并用实际native入口红绿对照，独立复审关闭。没有新建重试调度器。
- F04：既有06原位补facet与交互连续性要求未细述live→history交接。主会话提出由当前Timeline按唯一UID／row持有手动展开选择，独立审查者按06原条款认可，子Agent落实。真正running→finished仍自动折叠；不同scope／多phase不猜归属，不持久化正文或新增卡片。主会话再补Context引用稳定，防纯文本流触发静态卡重绘。正式组件红绿及真实DOM复验关闭，未修改用户既定完成规则。研讨及历史反例见[Verification](verification.md)。

最终APK构建时，查看器JSON仅copiedAt变化；先核对其它438文件及该JSON其余字段，再复用本次冻结JSON原字节，439文件逐SHA门禁保持。没有放宽门禁或修改源码／依赖；旧中间包及失败证据留存，不作最终交付。

## 已完成与交付物

| 修复组 | 本轮结果与证据边界 |
|---|---|
| 新会话标题 | 根据实际SDK client处理私有推理参数，修复unexpected `_reasoning_config`；最终18项相关含真实SDK传输，另一次隔离Kimi k3-256k正式generate_title请求2.49秒成功。线上尚未部署。 |
| 提交状态／恢复 | 可选提交ID沿native writer落库，同Profile／Conversation只读查真实回执；晚ACK／错误不清新草稿，不自动重发，不复活退休行或重做rewind。45项后端及前端竞态证据有效；worker只在进程内入口验证，未声称OS进程重启全链路。 |
| 中途Heartbeat | native真实落库observer发独立卡，同源UID去重，不从Thinking内容猜造卡；F03发布异常路径已关闭，真实浏览器中途重复投递仅一张卡。 |
| 时间线／慢渲染／滚动 | 真UID优先尾锚、同Turn后缀续接及工具occurrence修正；DOM身份与程序scroll反馈分清，following不再逐卡测量；F04详情交接保同身份展开及正文。真实512帧＋200cards旧版反例通过，隐藏浏览器19帧顺序／Heartbeat、详情补齐及八次重排阅读锚偏移保持。 |
| 微信改绑 | Gateway使用绑定目标自身native身份初始化，peer key继续负责投递；不合并别名、不修生产库。7份111项通过，旧错误参数负对照可复现；真实生产入站未执行。 |
| Android | v2 HIGH通知通道及可识别静音迁移、恢复退避与回前台刷新；原生380逻辑视口、Insets换算；adaptive／legacy图标资源与safe zone修正。70项原生测试、五档像素及mask预览、实际APK资源通过；真机显示、键盘、vivo launcher及声音／横幅未验。 |

最终前端全套**68份、1038通过、1跳过**，TypeScript和生产构建通过；构建保留既有大chunk警告。Heartbeat最终17项相关／7项直接测试与此前提交测试有重叠，不累计；后端冻结十检查0阻断／0提示。范围外5项旧失败已在未改基线复现，不宣称整个后端全绿。完整日志与执行范围见Verification及ignored证据目录。

| 交付物 | 实际版本／校验 |
|---|---|
| [签名APK](/Users/edgar/code/hermes-secretary/.hermes-dev/android-apk-20261021/Hermes-Secretary-0.1.3-arm64.apk) | 0.1.3／1003，32,048,497字节，arm64，Android8.0+；SHA256 `5c9cabe44fb5e0fa8fa580cdf46dc719d7a439887d3342fb37d844cdbce6f98b` |
| [统一Web dist归档](/Users/edgar/code/hermes-secretary/.hermes-dev/mobile-release-20261021/Hermes-Secretary-Web-0.1.3-dist.tar.gz) | 11,421,381字节；SHA256 `f5b9b2cfb3bd7685a1ff8351312649659c0327cee8fdbf808b4956d2223563fd` |
| [产物收据](/Users/edgar/code/hermes-secretary/.hermes-dev/mobile-release-20261021/final-artifacts.json)／[逐文件清单](/Users/edgar/code/hermes-secretary/.hermes-dev/mobile-release-20261021/dist-manifest.json) | 439文件，清单SHA256 `555528b534bb2abec4464d1027fa1697de4254affbc2a0e495e9bf4c374f449e`；APK内置439文件逐SHA与最终dist一致 |

APK实际证书与既有0.1.2相同，签名v2、release非debug、ZIP／ELF16KB对齐通过；22图标资源与20PNG可见RGBA／尺寸一致。未执行覆盖安装，不把同证书等同实际升级验收。旧ad7e484中间候选不是当前交付。

## Verification 与 Validation

三次全新fork-none独立审查保留各自独立规格判据、版本与历史：初审20条17符合／1违规／2不足发现F03；第二轮32条28符合／1违规／3不足，F03关闭而真实浏览器新增F04；最终整包19条17符合／0违规／2不足，F03/F04均关闭。不同粒度不得相加。[Verification报告](verification.md)记录正式接线、失败分支、主会话工程提案和独立评审、证据来源及最终验包。

主会话亲审了提交／Heartbeat实际writer、replay和worker接线，微信native初始化及保护表对照，标题SDK真实请求，时间线投影／交互owner及性能引用，并在自建隐藏IAB观察实际DOM、正文、顺序和阅读锚。首次浏览器补证暴露F04，主会话未按当时单测通过结论直接交付，保留反例并组织修补、新测试、新构建与第三次完整复审。最后一位审查者独立核对最终源码及APK内置439文件、签名和资源。主会话接收其17符合／2不足判定。

**正式Validation未启动、未通过。** [validation.md](validation.md)仅为主会话记录前置阻塞，不冒称独立验收报告；组件隔离输入与本地fixture不能等同完整App用户端到端旅程。F01真实WebView380／Insets／IME和F02真实系统声音／横幅是必要证据，公式、JVM测试和构建不能替代。根AGENTS显示保护仅允许自建隐藏IAB，禁止控制手机／桌面／可见页；当前没有合规真实Android运行入口。[真实验收Skill](/Users/edgar/.agents/skills/real-user-acceptance/SKILL.md)明确“呈现要求直接检查真实呈现”，故不能自行豁免。

## 剩余、阻塞与影响

1. **F01／F02阻塞整轮验收**：真实Android短边380、等比、状态栏／键盘Inset与恢复，以及升级后系统响铃／横幅、可识别静音保持尚未观察。API26–28不能识别全部用户设置，API26–29多窗口兼容及vivo launcher也未真机复验。不能保证设备结果已满足。
2. **未执行完整App验收及生产入站**：标题真实接口与机制已验；完整新建会话、断线恢复、微信改绑后正常消息仍需在获授权环境验证。不得向现有生产会话自动发送测试或改写历史／排期。
3. **范围外基线失败保留**：宽后端检查67通过／5失败，未改ee2ba55隔离副本相同5失败（review.summary orphan及四项instant_source旧fixture）；未放宽检查、未夹带无关修复。
4. **生产保持旧版本**：最终只读收据中服务器仓库HEAD仍`ed94619da81547bcb9e27aab60b608b2310e6890`且工作区干净。本轮未部署、未重启、未写生产DB／配置／绑定／排期；线上标题及其它症状不会因本地提交自行消失。
5. 本轮自建隐藏复现页已关闭，专用5187 Vite测试服务已停止；保留截图／DOM／日志供复核，不触碰用户页面。代码与交付记录提交按项目hook推送；原有不相关dirty及两份未跟踪文档保持。

后续由主会话在取得合法设备入口后补证，再派独立Verification及Validation；必要缺口未关闭前不宣布“全部修好／验收通过”，不自动上线。

## 用户复核建议

优先审阅上述APK／dist及[最终审查结果](verification.md)。恢复设备验收时，使用隔离或明确允许的数据：先覆盖升级确认0.1.3／1003与logo完整；进入会话检查380布局、等比与键盘开关／Insets；切后台让实际完成通知出现声音和横幅，并核对主动静音保持；再走新会话标题、断线后提交回执、中途Heartbeat、手动展开Thinking后加载相邻工具详情与上滚阅读。微信改绑后从正常用户入口确认目标会话接收、旧会话保持，不能把离线111项当成真实入站已通过。

浏览器现有证据入口：[展开与详情交接截图](/Users/edgar/code/hermes-secretary-web/.archive/mobile-render-02/ui-probe/browser-F04-visible.png)、`/Users/edgar/code/hermes-secretary-web/.archive/mobile-render-02/ui-probe/browser-review.md`。这些仅支持实际正式组件的呈现结论，不支持Android或完整生产App验收。无需重开已经放弃的Kimi旧会话调查。
