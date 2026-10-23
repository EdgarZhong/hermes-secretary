# 2026-10-24 固定Noting工具、端到端与联合部署：用户需求

## 用户原话（本轮起点）

> 确认，就按这版实施，Schema 和 description 完全不动，只改顶层注册、Main／Noting 的权限提示和运行时白名单。做好测试，尤其验证 Main 调不了、Noting 只能用四个工具，以及父子前缀一致。Schema 也不再需要重复在 loading task 的时候注入了。完成今天修复的自主实现。端到端，用 Kimi For coding 模型保证系统地址词一致的情况下，用 Alex Profile 在本地创建一个隔离副本跑通。其中可以调小各个配置，比如说，比如说，空闲、compact 和 noting 的阈值、延迟之类的，来小成本模拟真实使用情况，把整套代码机制跑通。并观察模型的行为观察主会话，是否经常误调用 notebook maintain？调用的时候能不能拦下来？在 noting task 不重新注入 schema 的情况下，观察 noting task 还能不能调用那4个工具？少量的行为轨迹错误，但是被 harness 正确拦了下来，然后最终任务也正常完成，是可以接受的，最后，把这些生效改动提交干净，部署到云端。现在开始，不要使用 astra模型做subagent。给自己挂个目标。

> 连同之前今天的那些修复一块部署。

## 已确认方案与最后修订

1. 两工具notebook_maintain／finish_noting原Schema、description及Provider转换不改，固定请求顶层tools，移除消息级动态工具注册。
2. Main原Notebook指导增加：`notebook_maintain and finish_noting are disabled for you and reserved for background Noting; do not call them even though their schemas are present.`
3. Noting任务保留父角色／工具策略作废，新增：`For this Noting task, notebook_maintain and finish_noting are enabled. Only conversation_history, notebook_show, notebook_maintain and finish_noting are authorized; do not use any other advertised tool.`
4. 用户本轮最后修订覆盖上一条方案中的“正文继续附完整四Schema”：初始和续Turn都不再重复Schema。只用既有API tools定义。
5. 真实绑定Noting执行白名单严格四工具，Main和其它非Noting身份不得执行两维护工具；不由模型自称或参数授予身份。Main其它原有能力保持。
6. 父子共享Root／工具／冻结Active前缀，子任务只追加任务及控制数据；不为Noting再改root或顶层tools。不将Schema不变混同工具列表前缀不变，首次生效在正常构造／恢复边界处理。
7. “系统地址词一致”按上下文理解为系统提示词一致：隔离副本沿Alex原Persona／业务指导，只增加已获准的权限提示；父子以真实发送字节／结构核对，不用缩减Prompt伪造低成本。
8. 本地隔离副本可用较低阈值和短延迟，指定实际kimi-for-coding，不改生产Alex模型或阈值。保密凭据／Persona／历史／raw wire不进Git，不发送微信／飞书或执行外部持久写入。观察自然主行为与纠错；另用受控输入确定性验证权限拒绝，不能将强制诱导误调用当自然频率。
9. 少量工具调用错误可被Harness明确拒绝并由模型改正，最终正常finish／合法Snapshot与用户任务完成；不把forced快照当正常完成。
10. 本轮同时部署599d114后端已审修补与589df02前端，以及新固定工具实现；已授权提交／自动push／云部署，保用户数据和既有配置／排期／绑定。APK竖屏包已有0.1.4，不自动安装用户手机。
11. 子Agent不得使用Astra；按AGENTS使用gpt-6.1-sol／high，不再派生。图形验收只许自建隐藏IAB，禁止显示／焦点变化；本轮优先正式CLI／RPC验证。
12. 不扩大为生产旧时间行恢复、旧失败Noting重跑、其它Provider改路由、Thinking留存／Timeline重做或来源包裹剥离。

## 冻结后用户追加（2026-10-24）

> 我又考虑了一下，你还是实际验证一下也，阈值超过我们实验测出来那个 n 等于38的情况吧。使用 Kimi for Coding 模型，这点成本我愿意支付。这次应该不存在动态工具声明导致的 bug 了，主要是看他在长上下文下还能不能在提示任务转换之后依然有效调用。这次应该不存在动态工具声明导致的 bug 了，主要是看他在长上下文下还能不能在提示任务转换之后依然有效调用 some prompts 头部声明的这几个工具。

新增完成条件：必须有超过原N38长度的真实kimi-for-coding长上下文样本，不用短请求成功代签。主会话选已有N46合成历史点作为可复用代表；按本模型实际Usage报告长度，不沿用K3校准冒充实测。长Main→Noting任务切换后无重复Schema仍可调用固定顶层工具并正常完成，记录父子wire；不得先自动压缩缩短再声称验证了长上下文。
