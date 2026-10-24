# 前端恢复共享契约

本轮 F1 接口已落盘：`web:src/core/recovery-demand.ts`、`web:src/core/page-recovery.ts`。当前为接口里程碑，正式 Controller 接线、后台及局部需求语义和测试仍在实现；不声明整包完成。

- Controller 将公开 `pageRecovery: PageRecoveryPort`。`getSnapshot/subscribe` 可交 `useSyncExternalStore`；`getDemand/setDemand(source, demand | undefined)` 管理组件需求，每个组件使用独立 source，卸载时解除。
- `RecoveryDemand.viewport = {first,last,aliases,offset}`；first/last/aliases 用 `timelineReadingKey` 或持久 UID/row alias。offset 只在内存；不保存阅读位置。`facets = [{id, rows:NativeMessage[],visible:boolean}]`，只让实际可见已展开 rows 阻塞，offscreen 可后台。
- `sidebar:boolean`，`usageView:'session'|'latest'`，`secretary:boolean`，`schedules:boolean`；组件在实际 open/viewport 改变时登记，不自行判定 ready。
- 恢复订阅状态 `documentId/connectionId/recoveryId/demandVersion/phase/readyForDisplay/backgroundSettled/commit`。`commit={commitId,recoveryId,demandVersion,owner,prefixCompatible}` 是一次有限展示交接。Controller 给 App render snapshot 附相同 commit。Timeline layout effect 完成 anchor 放置后调用 `acknowledgeCommit(commitId)`，可见 ready 不等待滚动动画。
- Files：`register(id,{required(demand,owner),read(context),accept?(value,context)})`，read 必须 await 实际 root/directory/preview 的所有当前显示读取，失败必须 throw。`context` 含 owner/recoveryId/requestId/demandVersion/signal/current()；accept 只在本轮 owner 有效时调用。resource id 稳定，组件卸载解除；Files 页面 must register root/list reader，preview 打开再追加 reader，隐藏二进制不读取。可用 `setDemand('files',{files:true})` 等组件私有字段，required 结合 Files screen 判断。
- 所有冷开、select、gateway.ready、online、visibility 与 native recover 都调用 `startRecovery(reason)`；已有恢复会合并触发。局部需求变化不回退整页冻结。不要组件另建整页恢复 owner。
- Android：请桥接受协调器的 documentId，避免两个独立 document 身份。建议 `installAndroidRecoveryBridge({documentId,startRecovery,getRecoveryState,subscribeRecovery})`，或暴露创建 documentId helper，由 Controller 构建时唯一选择。Native recover 触发统一 startRecovery，state 上报来自 exact commit acknowledge。

展示层若现有阅读 hook 需要 props：可新增第五参数 `{recovery: PageRecoveryPort, commit?: RecoveryCommit}`；Controller/App 集成由 F1 包独占，最终按 presentation 报告实际导出名称接入。

## 最终接线补充

`RecoveryCommit.local=true` 是恢复后局部需求的布局提交，只保anchor、ack，不滚尾。`prefixVerified=false` 是未证明，必须保anchor，不能当成anchor删除；true且prefixCompatible=false才是已证明破坏。viewport.visible使用presentation-signature.ts共享签名；signature、行正文和offset的正常变化更新描述，不递增需求版本。

资源可提供key(demand,owner)精确覆盖身份；同连接online/前台dirty触发合并当前轮并失效重读，initialize/gateway.ready重复启动共用当前请求。显式invalidate按资源登记版本使旧结果不能accept。Files-current是强制slot，卸载后不能因reader缺席而ready。恢复后新局部需求发布可ack的local commit，不冻结全页。

App已按实际展示值使用胶囊内建签名，折叠隐藏字段不参与；Usage hasData按当前scope事实对象存在性，Context按真实context数值或明确unknown/available=false/invalidated语义，token-only usage对象不建基线。

Gateway新增onAuthenticationFailure，只接受bootstrap明确HTTP401/403；Controller统一取消恢复、关闭旧socket、清本document敏感展示并禁止再读缓存，原生roster再次成功后恢复授权。普通网络异常/503不触发清除。现有前端无独立logout入口。
