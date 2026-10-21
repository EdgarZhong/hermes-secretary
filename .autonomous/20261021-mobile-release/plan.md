# 本轮实施计划：20261021-mobile-release

## 目标与依据

依据snapshot-index.md、requirements.md及baseline.txt。接续已实施候选，完成剩余Android380视口与图标、集成正式链路、独立两门禁、递增版本并在全部前端完成后统一构建dist与签名APK。真实生产会话／排期／配置／绑定不写，不自动部署；只读预检和隔离测试获授权。保存既有dirty及私人证据，不绕过显示保护。

## 覆盖与任务

| 要求/口径编号 | 任务和正式路径 | 实现负责人及白名单 | 依赖和接口 | 验证方法 | 用户场景 | 完成条件 |
|---|---|---|---|---|---|---|
| R01 | native标题→aux resolved client→SDK | 已交aux_title；agent/auxiliary_client.py、auxiliary_reasoning_floor.py及专测 | SDK类型而非URL猜测 | 真实SDK MockTransport／一次隔离Kimi请求 | 新会话生成标题 | 参数正确且正式请求可达，失败边界保持 |
| R02、R03 | Send writer→精确回执／user事件→Controller；Heartbeat native持久回调→卡 | submission_review；tui_gateway提交与Heartbeat、Web controller/API／独立测试 | 可选ID、原生display metadata、Profile／Conversation DB | native DB/Loop、实际worker入口（进程内）、晚ACK／失败／压缩／新连接 | 断线回执、后续草稿、Heartbeat先于输出 | 不误认／重发／复活退休行，真实落库才展示 |
| R04–R08 | cards/details→reconcile→sourceTimeline→reading hook | mobile_render原包＋timeline_final_review；projection/chat-presentation及测试 | UID／row／tool occurrence、读者锚点 | 真实512帧＋200cards旧失败/新通过；实际React hook几何／重排；全前端suite | 详情、分页、切回idle、上滚阅读 | 原位唯一且无自发跳顶，following不全卡测量 |
| R09 | 原生通知v2 HIGH迁移 | android_mobile原包；HermesNotifications及测试 | 系统channel／主动静音偏好 | 原生63／前端67既有证据，候选APK资源复核 | 完成通知 | 正式接线保持；真机响铃横幅须真实验收 |
| R10、R11 | WebView实际layout viewport380、Insets与adaptive/legacy icon | android_viewport_icon；Web src-tauri、scripts/android-icons及资源／原生测试 | 原生meta/settings、等比、现有logo；不改普通前端CSS | 原生测试／完整资源与mask预览；真实WebView证据边界明确 | 380整页、launcher显示 | 不裁切／露白／过小；比例及Inset正确 |
| R12 | binding handler→Gateway参数→原生身份 | weixin_identity_fix；gateway/conversation_binding.py、run_turn_runner.py及专测 | 保目标owner、入口仍投递key | 7文件111项，A→B构造、旧表全行不变、分支/跨Profile/真冲突 | 微信改绑新Conversation | B唯一身份、A保持、不修库合并 |
| R13 | 最终前端版本→dist→APK签名／版本／assets | 主会话集成，Android Agent构建 | 全部前端修复完成；版本统一；现有签名 | build退出、APK清单与证书、内置dist逐文件SHA | 覆盖升级安装 | 同一最终dist／APK且版本递增，产物可审 |
| R14–R16 | 保护范围、冻结规则、独立门禁／交付 | 主会话；文档和范围内集成快照 | 旧工具调查关闭，无生产模型消息 | 差异、凭据／范围审查、正式两门禁 | 托管交付 | 不虚报实际完成／UI验收；遗留明确 |

## 当前状态与编排

| 目标/任务 | 机制实现 | 正式接线 | 针对性验证 | 用户结果 | 当前负责人和下一步 |
|---|---|---|---|---|---|
| 标题 | 已交／主审接收 | 正式native helper | 18最终相关/真实SDK及单次Kimi标题成功 | 代表接口2.49秒成功，完整App新建未验 | FV01符合，未部署 |
| 提交／Heartbeat | 已交／主审接收 | writer/worker/observer/Web | 45相关、最终17/7重叠及Web竞态，10检查过 | 真实浏览器中途唯一卡；提交完整App未验 | F03已独立关闭 |
| 时间线／滚动 | 已交／主审接收 | select/details/replay/组件/hook | 最终68份1038过1跳，真实512帧反例；详情11/性能2 | 稳定浏览器详情原位/展开正文/19帧/8重排通过，非完整App | F04第三次独立关闭 |
| 微信身份 | 已交／主审接收 | bind→native init | 111过及10检查过 | 未发生产入站 | FV13/14符合；部署后正常用户消息验收 |
| Android380／图标／通知 | 已交／主审接收 | native viewport/channel/icon | 70原生过，五档像素/三mask/实际APK资源验证 | 真WebView/键盘/vivo/声音横幅未验 | F01/F02证据阻塞 |
| 集成dist／APK | 最终439文件/签名APK已完成 | Web bf279b2、0.1.3/1003 | 清单555528b534bb2abec4464d1027fa1697de4254affbc2a0e495e9bf4c374f449e；实际APK逐SHA同版/同旧签名 | 未安装 | 主审及第三独立验包符合，未部署 |

独立Verification只在全包集成收敛后新fork-none派出；先按冻结规格落独立判据，再查代码/证据。通过后另派新Validation，先场景计划交主会话过目，再执行；显示保护和API授权边界不变。两者不是大型套件复跑器。

## 缺陷与整改

| 问题编号 | 要求与触发条件 | 当前事实与影响 | 优先级及理由 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|
| D01 | R02 晚ACK／预写失效／worker时间戳／rewind | 已补6个正式链路缺口 | 高，提交事实错误 | submission_review | 最新45后端＋5前端证据、主审 | 已关闭机制；UI验收待门禁 |
| D02 | R06 真UID位置被尾锚覆盖 | 旧版真实回放失败、候选通过 | 高，历史错位 | 原渲染包＋主会话 | 实际回放及虚构回归，独立复核 | 已关闭机制 |
| D03 | R07 DOM复用错锚与程序scroll反馈 | 新hook修补、8次重排/20秒反例通过 | 高，阅读跳动 | 主会话＋timeline_final_review | 144项含新边界、最终真实DOM八次reflow锚偏移不变 | 已关闭，设备仍未验 |
| D04 | R12 peer key冒充目标出生身份 | helper核owner并选目标key | 高，微信入站崩溃 | weixin_identity_fix | 111项、生产只读无需修库 | 已关闭机制；真实入站待部署后 |
| D05 | R10–11 380／图标裁切 | 已实现并亲审；真WebView与桌面证据仍缺 | 高，本轮新包要求 | android_viewport_icon | 70项＋图标像素／mask亲审；真实UI待验 | 已关闭机制；UI未验 |
| E01 | R04–11实际UI | 隐藏IAB现已恢复；真实Android设备入口仍不可用 | 证据阻塞，不能伪造 | Validation | 补浏览器真实呈现；Android须合法真实运行入口 | 浏览器组件补证完成；真Android仍阻塞 |
| D06 / F03 | Heartbeat发布前异常误去重 | 已按真实replay区分发布前/后，17项相关及7Heartbeat通过 | 中，少见发布失败恢复 | submission_review | 独立复审已核关闭 | 已关闭 |
| D07 / F04 | 已完成Thinking详情接管 | 稳定真实浏览器：展开Thinking后相邻tool详情row41补齐，Thinking被历史facet重挂并折叠 | 中，违反原位补facet/手动展开连续性 | timeline_final_review | 正式组件＋Controller详情红绿；真实浏览器同UID手动展开/收起/状态转换及scope边界；新dist/APK和新独立整包复审 | 已关闭于bf279b2；正式红绿/真实DOM/第三次全范围复审及新包齐备 |
| B01 | 范围外旧suite5失败 | 未改ee2ba55副本相同5失败 | 不归本轮，不放宽检查 | 已记录 | baseline和integration对照日志 | 范围外保留 |

## 取舍、快照与续接

冻结文档提交见baseline；它在已授权实现之后固定接续轮次范围，不重写此前实施顺序。用户托管允许范围内本地阶段提交，按根规则每次自动push，不提交原有不相关dirty。生产只读预检显示git干净、运行ed94619，非部署。本轮确认380覆盖390，不再询问宽度。最终dist与APK等所有前端完成再构建，不用旧dist提前交最终包。源码／依赖未变化的既有有效证据复用；只针对集成、失败修复和证据存疑补跑。

托管追加（F04前历史候选，以下旧产物非当前交付）：后端产品快照3b48cf0baeb3c49bb96849d24c6105bf6e39e6fc，Web ad7e4842c230bf65bf8b1d5491ea1a169407ca6a。正式emit入环前异常误置published已补：入环前允许重复回调恢复、False或入环后异常按真实replay去重，3个实际native链路对照先红后绿；17项相关/最终7Heartbeat/10检查过。无新发布器或重试调度。APK SHA256 40efadefc358bd2604709e490451064762ad2d1c017cf48c9cfff239ab4a9208；dist归档SHA256 0ea07e0885a7a3e7dd721e0f065b0dfb7e53a67d50e89ca1d4f7d5325d1b8454。查看器copiedAt生成时间差异只在构建层复用冻结JSON原字节，439全SHA门禁仍保留。

独立初审与新fork-none复审已完成，保留历史：初审17符合/1违规/2不足；第二次以32独立条款核28符合/1违规/3不足，F03关闭、F04新增，Android真实运行缺口F01/F02仍在，正式Validation前置未通过，未启动。隐藏IAB恢复后主会话真实读DOM：稳定v2中途Heartbeat唯一卡、idle切换/详情顺序通过；八次reading几何偏移保持。新F04由稳定v2排除HMR后证实，按既有规格工程修补，无新增产品口径或用户待追认。旧dist/APK不能作为最终交付，修完前端再统一重建。

最终实施更新：Web bf279b2dc5ec5553ff9e370696b153e4aadb52cd，Context owner按身份/phase计数语义稳定引用；80张静态memo卡纯增量仅一次渲染，新phase仍通知。正式Controller详情11项和性能2项红绿、相关114/最终25重叠通过；最终68份1038过1跳、typecheck/build过。browser-F04*稳定真实DOM证明原反例修复且正文保留，19步中途Heartbeat去重/顺序及八次重排锚偏移保持。最终dist439清单SHA555528b534bb2abec4464d1027fa1697de4254affbc2a0e495e9bf4c374f449e，最终APK SHA5c9cabe44fb5e0fa8fa580cdf46dc719d7a439887d3342fb37d844cdbce6f98b，32,048,497bytes；dist归档SHAf5b9b2cfb3bd7685a1ff8351312649659c0327cee8fdbf808b4956d2223563fd。release_final_verification第三次独立19条17符合/0违规/2不足，F03/F04关闭；F01/F02仍阻断，正式Validation未启动；不因组件UI通过就关闭真Android证据缺口。

最终停止判定：本地实现、正式接线、开发期针对性验证与候选构建已收敛，整轮未完成；阻塞为合法真实Android运行证据F01/F02，不能用组件/公式关闭。未部署。恢复时先建立合规设备验收入口补证，再重开独立门禁及正式Validation；不重开旧Kimi。当前事实与产物见final-delivery.md。
