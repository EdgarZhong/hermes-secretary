# F4／A1 共享接线契约

本轮基于冻结06 R4/R5/R7/R8。源码已具备以下接口；最终正式App／Controller接线由frontend包负责。本文件是约定的整包接口里程碑，不作最终验收声明。

## Timeline 与胶囊

`useTimelineReading(scope, loading, nodes, active, {recovery:PageRecoveryPort,commit?:RecoveryCommit})` 保持旧四参兼容。hook登记 `setDemand('timeline',{viewport,facets})`；viewport含真实可见first/last/aliases/offset及visible签名；可见展开facet给持久source/detailSources，离屏facet标visible=false。Observer读取当前DOM与当前可见nodes，不依赖staging projection先发布。卸载移除需求。

`presentation-signature.ts` 导出 `timelineVisibleSignature(node,expanded)` 和 `timelineSourceIdentities(node)`，prefix比较直接复用；identities包含tool occurrence以及全部source/detailSources的uid/row，不从tool alias空集推断相容。签名只用于对齐窗口展示值，不将stream内容变化当成新读取依赖。

恢复commit由同一reading owner保anchor后layout ack；prefix相容用240ms ease-out滚到实际尾部，ResizeObserver和following instant在动画内让位；delta只更新尾部几何，不续期。wheel/touch/key/scrollbar立即取消。reduced motion一次定位。`local=true`只ack新需求并保留同recoveryId正在执行的handoff／既有following／人工阅读所有权，不重新启动或取消原动画。`prefixVerified=false`暖恢复仅保anchor，不把未知当破坏；cold无已建立阅读位置先定位真实尾部。DOM晚子树／文本挂载触发位置reconcile，需求按下一帧合并登记。

`UsageSummary`／`ContextIndicator` 新增可选 `ownerKey`、`displaySignature`、`hasData`；hasData=false仅表示未读取placeholder，首次变true只建基线；合法unknown须true，retained已有值仍true。ownerKey用稳定Conversation owner，displaySignature只传实际显示的估算、窗口、来源字段。组件内规范显示值比较，首次／同值／换owner／用户切view或open均不闪。数据更新600ms一轮，不重复续期；120ms高亮、480ms淡回；降动效120ms静态高亮并保600ms合并窗，selected/open独立。

## Files

`<Files state={state} recovery={controller.pageRecovery}/>`。组件用 `register('files-current', {key,required,read,accept})` 替换Controller失败占位，key精确固定FILES_PROFILE+routePath+preview；read每轮真实default-cwd→list或read-text＋必要authorizedFile，不读隐藏文件。资源owner始终FILES_PROFILE，不借聊天Profile。失败throw，不用fulfilled/旧Blob满足。

预览增加最小获批FileViewerPreview.onRecoveryState可选回调，透传真实loading/ready/error。新预览在无可见变化的staging容器中完成实际renderer；失败拒绝本轮，成功后保持该renderer实例在commit显示。Files收到commit后先采用accepted root/data/preview，再由实际React layout提交ack，App不能提前代ack。恢复期间保留旧列表／预览。

## Android

- `installAndroidRecoveryBridge({documentId,startRecovery(request)})`：documentId必须取PageRecovery.getSnapshot().documentId。先安装事件listener，再发hello；返回dispose。回调request含documentId/nativeRecoveryId/reason，调用同一startRecovery。Native hello可能同步派发事件。
- `reportAndroidRecoveryState({recoveryId,demandVersion,state},request?)`：需求变化／开始先recovering；当前可见React commit及anchor定位后ready；失败failed。ready不能取Gateway connected或后台settled。传request可过滤迟到native轮次。
- `reportAndroidNavigationReady({profile,sessionId,messageId})`：只在真实目标owner可见恢复完成后调用。文档ready仅允许原生派发navigation，原生保留目标直到此确认；跨reload保留。
- `observeAndroidConnection`保留既有2秒health，增加documentId/recoveryId；online无论当前socket是否connected都通知Native开始／合并恢复，不直接reload。普通网页无HermesAndroid时零行为。

Native ForegroundRefresh用uptime固定五秒；onResume真实后台返回与online合流、不续期；旧doc/nativeId/demand或无recovering的ready均不解除。ready先到、心跳后到可在同一期限内完成。无JS独立兜底，首次cold不额外五秒回归，后续10/15/20/30；auth origin／主frame／ActivityResults保护和通知内容、保活、竖屏保持。受保护附件若打断正在恢复的文档，返回用既有10秒宽限重建回执，避免过期回调抢断附件处理。

## 证据边界

定向Vitest及Robolectric日志：`.hermes-dev/web-recovery-20261024/presentation/`。最终计数及剩余边界写presentation.md。未操作用户页面／设备／AVD；Robolectric不等于实际APK生命周期验收。用户C17明确豁免本轮真实APK验收，Web实际验收与原生单测继续；无模拟器授权。构建由主会话在集成后统一安排。
