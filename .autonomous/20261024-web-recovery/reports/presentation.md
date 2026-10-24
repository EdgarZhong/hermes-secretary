# F4／A1 实现交回

状态：实现与定向验证交回，待主会话亲审及本轮独立门禁；本报告不宣称真实APK生命周期验收或完整产品交付通过。工作树为`codex/web-recovery-20261024`，冻结Web基线`9fd115d3b016bb51a8a78dd1724684fd1890665c`。未提交、push、部署、调用真实模型或操作用户页面／设备／AVD。

## 一、对应条款

- R4：真实可见持久别名、offset、工具occurrence及全部source identities；可见展开facet；未验证前缀不当破坏；窗口／分页本身由frontend包实现。
- R5／08：Files固定FILES_PROFILE，root＋当前目录／预览每轮重读，实际文件与真实renderer就绪，资源取消不能冒充成功；HistoryDetails对staging补水由frontend包消费登记。
- R7：同一reading owner一次layout anchor交接、240ms ease-out真实尾部、delta不续期、输入取消、降动效、局部commit保anchor不滚尾；Usage／Context规范显示值变更高亮。
- R8：JS／Native document、nativeRecovery、recovery、demand闭环；五秒硬期限、online合流、独立无JS看门狗与退避；认证／ActivityResults／通知目标／可信主frame及既有保活、通知内容、竖屏保护。
- R9：独占组件／设计／桥／Android文件；App／Controller／coverage正式接线由frontend包完成。获主会话批准最小扩白名单`FileViewerPreview.tsx`，仅增加真实renderer状态回调。

## 二、实际变更

Timeline hook保留原四参兼容，新增第五参。DOM登记实际可见节点与展开facet，使用共享presentation-signature函数比较，不以tool-only空集当相容；视口通过有序DOM有界测量，避免每个delta强制测量全部旧历史。旧reading owner在layout阶段清需求，避免卸载被动清理覆盖新owner登记。

完整恢复提交先恢复旧anchor的屏内位置并ack，再进入240ms尾部动画。ResizeObserver／following instant在动画中让位，目标持续读取真实尾部几何且总时长不续期；wheel（含嵌套工具滚动）、touch、滚动键、pointer输入立即取消。`local`或`prefixVerified=false`仅保anchor，不将未知当已删除／不兼容。已证破坏允许重定位。

胶囊采用实际呈现值的规范签名；首次／同值／owner或用户view、open切换重建基线。有效更新120ms高亮＋480ms淡回，600ms内合并；降动效120ms静态高亮，仍保600ms合并窗，独立于Popover open／selected。

Files注册`files-current`替换失败占位；精确key含固定Profile／路由path／preview，read每轮default-cwd→list或read-text＋authorizedFile。旧数据在同资源恢复期间保留；新预览用不可见staging容器运行真实第三方renderer，ready后保持该实例在commit显示。实际root/data/visiblePreview的React layout完成才ack。取消／替换stage主动reject并移除监听，旧请求不能accept新path；错误不以旧Blob或fulfilled满足。预览内部错误和ErrorBoundary均拒绝当前读取。

Native在真实后台回归启动固定五秒，重复onResume／online合流，不以connected或owner切换续期。hello绑定当前document；recovering→相同版本ready＋有效心跳完成，旧document/nativeId/demand拒绝；ready先到可等待同期限内心跳。五秒超时先胜出，之后10/15/20/30退避，不依赖JS存活。旧JS明确document-ready保留watchdog降级，但绝不解除新的foreground五秒窗。第三方认证暂停旧期限，可信页返回重新hello；相机／文件ActivityResults保留原路径，打断恢复后给既有10秒保护宽限。通知目标派发后保留，目标owner可见完成回执才清除，跨reload不丢。

## 三、正式调用路径

- App Chat→`useTimelineReading(...,{recovery:controller.pageRecovery,commit:state.recoveryCommit})`→`setDemand('timeline',...)`→Controller staging details／coverage→可见commit→layout anchor／ack→可选动画。
- App Files→`Files recovery={controller.pageRecovery}`→`register('files-current')`固定owner实际root／list／preview读取→renderer ready→协调器commit→Files实际React layout ack。
- App胶囊传稳定ownerKey和实际displaySignature，组件内部处理有效显示变更；未改变业务值与实际open状态。
- ControllerPageRecovery.installLifecycle→`installAndroidRecoveryBridge` hello／native event→同一startRecovery→协调器状态订阅→`reportAndroidRecoveryState`；目标owner ready→`reportAndroidNavigationReady`。Native MainActivity可信origin＋主frame入口→AndroidPacket.parse→ForegroundRefresh，或NavigationMailbox保留／确认目标。

完整稳定接口见`presentation-contract.md`。共享签名从`src/components/presentation-signature.ts`导出，frontend已正式复用，避免两套字段镜像。

## 四、验证证据与边界

本地证据目录：`.hermes-dev/web-recovery-20261024/presentation/`。`evidence-source-manifest.json`记录行为测试时本包及共享接线源码SHA，`typecheck-source-manifest.json`记录最终类型检查时全仓源码SHA；两次之间共享包仍在修补，不能把类型检查当成该变更的行为测试。共享包后续若改变相应源码，按影响复核证据，不把旧测试当新版本证明。

- `frontend-final.log`：六文件96项通过。覆盖原Timeline阅读／App呈现回归、稳定owner需求替换、anchor先于ack、ResizeObserver不抢位、动画中尾部增长、wheel／嵌套scroll／touch／key／pointer取消、降动效、local和未验证prefix不滚尾、tool-only持久源、胶囊同值／零／unknown／burst／owner与view／降动效、Files固定owner每轮真实读取／保旧列表／renderer失败与重试／换path取消旧stage、真实FileViewer状态映射、JS桥旧包与普通网页零行为、待定读取／失败／可见ack。
- `typecheck-final.log`：`npm run typecheck`最终通过。期间发现并交frontend修复display-cache的IDB open结果类型错误，修复后已补验；该次全仓源码另记录`typecheck-source-manifest.json`。
- `android-final.log`及三份XML：`testUniversalDebugUnitTest`三个定向类共40项通过（ForegroundRefresh22、AndroidBridgeState13、HermesBootstrap5）。含4.9秒ready、五秒connected不能解除、旧generation、ready先于心跳、online合流／重复resume不续期、无JS和10/15/20/30、迟到pageStarted、认证返回不沿用过期期限、拍照／文件与真实ActivityResultRegistry URI、通知目标保留至确认、Cookie／当前URL／完成去重及Active失效、销毁取消。

环境：Vitest/jsdom、React实际组件与真实PageRecovery协调器，外部网络／第三方renderer仅在依赖返回点受控；Android正式MainActivity／Wry生命周期在Robolectric API35运行，仅隔离JVM不能加载的Rust JNI。mise OpenJDK21.0.2、既有SDK／NDK；生成工程的`:app:testDebugUnitTest`简写有Arm／Universal歧义，使用明确Universal任务，未改Gradle规则。旧测试夹具直接替换state需补正式publish；不是以调整预期掩盖真实呈现行为。

Robolectric不能证明实际WebView生命周期与画面连续。未运行真实APK后台／前台、杀JS、实际Authelia、设备拍照／附件或通知UI；未进行隐藏IAB图像验收，由本轮Validation统一执行。未改dist或打包，最终APK资源／签名校验由主会话统一安排。

## 五、缺口

本包已知范围内机制／定向行为验证缺口：无。跨包最终收敛、后端真实DTO完整恢复、隐藏IAB用户验收、实际APK生命周期、最终构建与独立门禁尚不由本报告证明。真实APK权限／显示保护冲突由主会话处理，不能用上述40项单测代替。

## 六、接口影响

仅增可选props、hook参数、读取resource与packet类型，普通网页无HermesAndroid不启动APK层行为。Controller唯一documentId作为桥身份；组件不另建全页恢复循环。`RecoveryCommit.local/prefixVerified`由frontend新增并被本包消费；不修改App/controller/types/client/projection。MainActivity仅接packet／NavigationMailbox确认，不改通知通道／内容、保活或锁屏方向。其它dirty保持。

## 七、建议后续

主会话亲审上述正式路径、共享接口与SHA证据，检查frontend最终变更对本包的影响；集成后统一构建、冻结代码并运行两独立轻量门禁。实际APK安装／生命周期权限满足后再验并记录，交付声明保持真实边界。本子Agent不提交／push／部署。

## R7 主会话亲审整改：未读取 placeholder 不能作为旧基线

触发：原高亮仅比较规范签名，使同owner的未读取`—`／null切至首次真实数值也产生数据更新动画；旧测试只覆盖已知值首次mount。

修复：只修改`src/design/indicators.tsx`与对应`recovery-handoff.test.tsx`。两个胶囊新增可选`hasData`，默认true保持已有调用兼容；hook只有前后均为已取得的展示结果才允许比较高亮。`hasData=false → true`只建立基线，不闪；合法unknown结果必须为true，因此unknown↔零／数值仍按实际变化高亮。owner／view切换、同值与600ms合并窗保持。App由frontend独占接线，未在本包修改；已交接不能用非null数字推断、恢复retained不应清基线、token-only usage对象不是Context真值的判断边界。

证据：`capsule-baseline-review.log`七项高亮测试通过（12项无关阅读用例跳过），新增Usage／Context各自的placeholder→首次零值、后续变化／600ms合并、换owner／view及placeholder→合法unknown→零→unknown。`capsule-baseline-typecheck.log`全仓类型检查通过。未重跑未受影响的Android、Files或其它大套。

版本：`capsule-baseline-source-manifest.json`记录本次两个文件与当时App接线SHA，原`evidence-source-manifest.json`以revisions追加本次证据，不把原96项报告改写为新版全量验证。此项组件机制与针对性验证已完成；App语义接线由frontend包交回主会话审查。未提交、派生Agent或操作设备。
