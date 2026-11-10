# 本轮修复与发布交付记录

2026-11-10：已完成认真代码审查、针对性回归、原故障实际页面复验、合main与正式发布。用户明确取消完整自主流程前置，本记录汇总真实交付，不冒充新一轮独立双门禁PASS；旧Verification/FAIL保持其原候选含义。

## 已发布

- 后端云main：`72d5d1e8909cd3eaca6309e590a38879799b7912`。Web/Gateway同版active，微信connected。
- 前端构建：`655ecf56fb3ff082d5a84db810388c32d420f9b0`，UI main `9097f19`。439静态资源与HTTP抽样、APK一致。
- APK：`/Users/edgar/Downloads/Hermes-Secretary-0.1.14-655ecf5-arm64.apk`，0.1.14/1014、32181021字节，SHA256 `833db90fb1bdb330193ff65cf52f375475e96f3db4235c49dff19a6e98303449`。原签名、非debug、arm64、ZIP/ELF16KiB核验通过。
- 算法最新b232的27核心逐SHA一致并已合main、上线。自然Heartbeat在11:07完成，产生新版cache warm/hot决策，effective1740秒；原生10800起点不变。没有为验收发送生产模型消息。

## 故障结论

| 用户问题 | 已证原因／最终处理 | 证据及边界 |
|---|---|---|
| 流式重复Thinking、双份正文、结束前白屏 | legacy/typed被合法通知交错，旧邻接配对生成重复render ID；按同一owner精确贡献认领，保稳定身份及真正Turn边界 | 原79真实IAB红，655同页六请求绿；419有效针对性回归。不能将每次旧卡顿都归此因 |
| 系统唤起/Steer丢旧collapse、上下跳、停止实时输出 | custody提前投影改变fold前沿、过期读取残留replay hold、终态Thinking顺序错误；统一可见投影与有限恢复交接 | 连续原生链、Gateway逐条持久跟随、旧手动展开、终态阅读锚点及无reload已实测 |
| Enter/内部Turn Session busy、控制权丢失 | 旧idle提交与真实owner状态脱节；普通/Heartbeat/Reminder/Delegation等接原生runtime的原子输入与控制 | 正式RPC/Loop/SQLite及实际页面；只有真实独立Gateway占用可拒写，页面仍可跟随历史 |
| 空闲维护期间控制 | 已接收等待输入；Stop只取消维护，安全边界继续已收消息 | E01为用户明确选择；Main Stop仍按父Turn语义清理未消费输入 |
| 意外关闭不重试、恢复期间卡住 | 同步观察者异常截断退休后重试；事件编号/入队逆序及旧恢复owner覆盖 | 连接owner先提交生命周期和重试，隔离展示观察者；陌生关闭码同样恢复、正常业务局部读取；无盲重放 |
| 已发送却提示Submission outcome unknown、取消再报错 | 该提示表示缺ACK，不能表示未受理；20:42正式持久受理早于关闭约127ms | 原ID自动查询并退休对应未知事务，不假撤销/误恢复旧草稿；当次关闭发起方仍未知 |
| 同页微信XML时隐时现 | 中断恢复把干净persist正文覆盖成模型包裹；保入口正文，并只读投影既有错误行 | 57针对性+101读取回归、22 Windows限定跳过；线上昨晚/今早两行显示干净、原文和API副本SHA不变 |
| 手机可导出日志 | 正式APK常态8MiB滚动，网络/前后台/连接/恢复/固定渲染失败类别，双端连接ID，受限ADB导出 | 产物/原生schema及出口测试通过；设备0，实际手机安装和ADB导出待后续 |

root亲读实现、正式接线、失败路径和测试调整，不以测试数量替代审查。最后React异常诊断六浏览器案例保原错误只报告一次且不改变Socket；消息原文、凭据和异常堆栈不写诊断。目标范围内无已知尚未修复的可复现产品阻断。

## 仍然不能宣称的结论

历史所有断线的触发方、网络/代码责任比例没有充分双端现场证据；真实WiFi/5G自然连续使用、设备安装及ADB导出待用户接设备。算法自然决策证明新版接入生效，不保证所有情景更省或Provider必然命中缓存；原反例和条件性限制保持。超过原20秒active自动跟随窗口的阅读样本不算永久滚动锚点证明。

## 证据入口

- [运维记录](../../docs/operations-log.md)：两次发布、正式版本/配置/数据保护、两套备份与回退。
- 连接工作区ignored `.hermes-dev/web-control-reliability-20261109/root-d38-ui/fixed-verification.json`、`gateway-wrapper-regression/`（含正式API只读核验）及`release/`。
- UI ignored `.archive/web-control-reliability-20261109/d38/`、`d38-diagnostics/`、`release/`。
- [原技术审查](verification.md)只对应固定旧候选；不改写其FAIL。本轮后继复验见[实际验证范围](validation.md)。

两次发布都保护三Profile各30表及配置/绑定/旧Dashboard；只保两套完整三库，运行库及同步ZIP保持。原算法工作区dirty、Huawei资料和UI五个.DS_Store保留。后续文档提交不代表重新部署。
