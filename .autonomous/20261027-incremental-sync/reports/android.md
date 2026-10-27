# A1 · Android 同页恢复实现交回

## 1. 目标条款与依据

- 已读本轮 snapshot-index、baseline、plan、根 AGENTS／CLAUDE、06 顶部 C0–C3／S17／P10、旧 §1.2 通知／认证／附件保留项，以及 executing-plans 与 autonomous-run 子 Agent 消息契约。
- 设计冻结后端 `cf5742c70b26e0dc954eabcb4b07c232c5231013`；前端基线 `c39086c1879cd46370bdc8f4e3d98a3c290aecc3`，工作分支 `codex/incremental-sync-20261027`。
- 对应 U09、S17、P10、C3.5 和 plan A1：Native 仅通知既有 JS owner 同页恢复；不因五秒／退避期限、初始化暂失败或心跳缺失重载文档。保留真实归属、通知导航、认证隔离、附件／拍照与权限窗口保护。

## 2. 实际变更

仅修改前端仓库以下 3 文件：

| 文件 | 实际变化 |
|---|---|
| `src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/ForegroundRefresh.kt` | 移除全部 WebView.reload 调用、迟到 ready 的期限 reload、Handler／watchdog／deadline／退避及受保护期限状态。保留心跳时间用于实际 ready／terminal 接收核验，不再定时轮询。新增两项局部状态记录本轮是否请求／已投递，重复 online／hello／权限 resume 不重发；真实 foreground／offline→online／初始化失败／附件返回可同页唤醒，未完成轮次沿用 nativeRecoveryId。真正新轮次或新文档仍更新 native ID。 |
| `src-tauri/gen/android/app/src/main/java/com/edgarzhong/hermessecretary/MainActivity.kt` | 构造改为 `ForegroundRefresh()`，移除仅供自动 reload 使用的 beforeReload 回调。真实 onDocumentStarted → clearPageState 保持。 |
| `src-tauri/gen/android/app/src/test/java/com/edgarzhong/hermessecretary/ForegroundRefreshTest.kt` | 保留原 30 个场景，按本轮明确免刷新契约改写旧 reload 断言，增加真实完成／未完成／错误归属断言；新增 6 场景，合计 36 项。 |

未改前端 src、IME／布局、AndroidViewport、通知语义、API／协议、设计／核心文档或 plan；未提交、打包或部署。

## 3. 正式路径与状态处理

- MainActivity 的真实 onStop／onResume、network-restored、health、initialization-failed 和 ActivityResult 回调，仍调用唯一 ForegroundRefresh owner。
- 仅可信 Hermes 文档收到 `hermes:android-recover`；无 documentId 时保留本轮请求，hello 到达后投递，不向认证外页注入。重复 hello 不重置 owner，真实 pageStarted 清理旧文档，恢复仍使用原 documentId／nativeRecoveryId／recoveryId／demandVersion。
- ready／terminal 仍先要求当前轮次的 recovering，再要求完全匹配的版本及 10 秒内真实心跳；普通 ready 还要求 connected。没有心跳、只有 connected 或只有终态均不能伪造完整就绪；terminal 可以表示实际已呈现的不存在等结果，不冒称连接成功。
- 同一未完成轮次再次真实唤醒时保留 native ID 与进行中版本，撤掉唤醒前尚待心跳的 ready，避免网络变化后消费旧 pending 回执；后续当前 JS 恢复重新报告。没有定时器／1ms 忙轮询，也没有另一套后台调度。
- 附件／拍照 ActivityResult 处理期间不发恢复信号；结果交还后，未完成恢复沿原 owner 同页继续，不清页面、Cookie、草稿、附件或运行观察。单纯权限 pause／resume 和配置变化不启动前台恢复。通知目标仍在原 NavigationMailbox 中等正确 document／目标确认。

## 4. 验证结果与证据

证据目录为前端 ignored `/Users/edgar/code/hermes-secretary-web/.archive/incremental-sync-20261027/android-recovery/`。

环境：macOS、OpenJDK 21.0.2、Android SDK `/opt/homebrew/share/android-commandlinetools`、Gradle 8.14.3、Robolectric SDK35。测试运行真实 MainActivity／Android 生命周期及 WebView；仅沿既有 ForegroundRefreshRustShadow 隔离 JVM 无法加载的 Rust JNI，不替换待测恢复 owner。

- `before.log`／`before.xml`：在冻结原实现仅添加 4 个新契约反例，4/4 失败，分别为超过35秒仍保当前文档、无新鲜心跳的迟到 ready、初始化失败同页信号、连续真实回前台不更换进行中 native ID。
- `after.log`／`after-initial.xml`：移除 reload 后，原场景修订与首批新测试 34/34 通过。
- `final.log` 及 6 份 `TEST-*.xml`：强化旧回执、重复信号和附件保护后，6 类共 **82 项全部通过，0 跳过**：ForegroundRefresh36、AndroidViewport9、AndroidBridgeState14、HermesNotifications11、HermesBootstrap5、AndroidService7；执行耗时 10 秒。
- 具体覆盖：恢复超过5秒／35秒并最终完成、连续无JS／离线数分钟不刷新且不伪成功、在线弱网、offline→online、重复 resume／online／hello合并、错误 doc／native ID／recovery ID／demand版本拒绝、ready与心跳任意先后、terminal非connected、文件与拍照、ActivityResultRegistry原URI返回、权限暂停、通知目标确认、认证往返、初始化失败后同页完成、Cookie／URL／当前运行观察保留。
- `diff-check.log`：`git diff --check`通过。`implementation.diff`保存本包差异，`source-sha256.txt`绑定本次实际三个源码／测试文件，方便集成后判断证据复用范围。

最终命令：

```sh
ANDROID_HOME=/opt/homebrew/share/android-commandlinetools ./gradlew :app:testUniversalDebugUnitTest \
  --tests com.edgarzhong.hermessecretary.ForegroundRefreshTest \
  --tests com.edgarzhong.hermessecretary.AndroidViewportTest \
  --tests com.edgarzhong.hermessecretary.AndroidBridgeStateTest \
  --tests com.edgarzhong.hermessecretary.HermesNotificationsTest \
  --tests com.edgarzhong.hermessecretary.HermesBootstrapTest \
  --tests com.edgarzhong.hermessecretary.AndroidServiceTest \
  -x rustBuildUniversalDebug
```

工作目录为前端 `src-tauri/gen/android`。跳过 Rust APK 构建，不构建／签名／发布安装包；Android Kotlin 及原生单测正常编译。一次中间命令误在前端根目录调用 gradlew，未执行测试；纠正工作目录后取得上述有效证据。

## 5. 缺口与限制

- 没有 Android 真机／实际 WebView 页面中断线与后台冻结证据，不把 Robolectric 的 WebView 对象保留／reload计数和 fixture tag 当成真实 DOM／草稿端到端验收。
- 完全失活且不再执行 JS 的文档不会由软件强制 reload；仍不判恢复成功，后续自然系统杀进程冷启沿初始链路。这是本轮明确取消主动刷新后的行为，不引入替代 reload 定时器。
- 本包没有访问可见UI、桌面或外部浏览器；也没有调用生产服务／模型或发送通知。整轮独立 Verification／Validation 尚待主会话统一安排；本报告不是门禁判定。

## 6. 接口影响

- JS 桥接事件、reason枚举、数据包字段和回执格式不变，继续使用已有 ControllerPageRecovery／PageRecovery。
- 私有原生类移除 beforeReload 构造回调，仅有 MainActivity 与对应测试使用，均已接线。清理无作用的私有 reload／期限状态，无用户界面变化。
- 未触及其它 Agent 的前端 src 工作，也未改原有 DS_Store 或其它脏文件。

## 7. 建议后续动作

- 主会话按三个文件实际 diff 亲审，重点核对唯一 JS owner 接线、同页信号合并与归属校验；当前实现可进入整轮集成快照。
- 前端集成变化若影响 Android 桥接／恢复回执，定向复用或重测相应证据；无需为 review 重跑本包整套。
- 独立门禁结合真实App的 SPA 同页恢复与数据一致性证据，保留 Android 真机弱网／后台冻结／附件与通知旅程未验限制；未授权部署不自动上线。

## 主会话接收审查

已亲读三文件diff及MainActivity消息分发、JS android-health桥接和PageRecovery.startRecovery上下游：无额外reload入口；同native ID重复唤醒被当前JS轮次合并，不创建第二恢复owner；通知回执仍须文档和恢复版本对应。原生82项证据范围匹配，未复跑。APK真实设备缺口仍保留，正式前后端集成和独立门禁尚未执行。
