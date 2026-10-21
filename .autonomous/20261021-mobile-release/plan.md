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
| 标题 | 已交／主审接收 | 真实native helper | 360相关＋最后重叠18过；新10重跑有效 | 真实Kimi k3-256k/OpenAI SDK生成标题成功，2.49秒、1请求、无私有参数 | 独立门禁 |
| 提交／Heartbeat | 已交／主审接收 | inline/worker/原生持久／Web | 最新45后端、5前端与既有4恢复过，检查10过 | UI仍未验 | 集成构建后门禁 |
| 时间线／滚动 | 已交／主审接收 | select/replay/details/真实hook | 原212／最后152重叠；后5份144过；整体66份1025过1跳 | 真实历史回放通过；实际浏览器UI未验 | 门禁审查 |
| 微信身份 | 已交／主审接收 | 真实handler→构造→native init | 111过，检查10过 | 无生产入站Turn验收 | 保当前绑定等部署后正常输入 |
| Android380／图标 | 已交／主审接收 | 原生meta/settings/Insets及实际生成图标 | 70项原生全过；五档像素/三种mask通过 | 真WebView和vivo桌面未验 | 签名APK构建中 |
| 集成dist／APK | 最终dist已构建，APK构建中 | 0.1.3/1003 | 439文件，清单SHA ed540b2a693a8d53e9bd8fa3200f7f9d314523d8ad84f5f12f7a1f7d814424be | 待门禁 | android_viewport_icon打包，release_verification独立审查 |

独立Verification只在全包集成收敛后新fork-none派出；先按冻结规格落独立判据，再查代码/证据。通过后另派新Validation，先场景计划交主会话过目，再执行；显示保护和API授权边界不变。两者不是大型套件复跑器。

## 缺陷与整改

| 问题编号 | 要求与触发条件 | 当前事实与影响 | 优先级及理由 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|
| D01 | R02 晚ACK／预写失效／worker时间戳／rewind | 已补6个正式链路缺口 | 高，提交事实错误 | submission_review | 最新45后端＋5前端证据、主审 | 已关闭机制；UI验收待门禁 |
| D02 | R06 真UID位置被尾锚覆盖 | 旧版真实回放失败、候选通过 | 高，历史错位 | 原渲染包＋主会话 | 实际回放及虚构回归，独立复核 | 已关闭机制 |
| D03 | R07 DOM复用错锚与程序scroll反馈 | 新hook修补、8次重排/20秒反例通过 | 高，阅读跳动 | 主会话＋timeline_final_review | 144项含新边界、UI呈现待验 | 已关闭机制；UI待验 |
| D04 | R12 peer key冒充目标出生身份 | helper核owner并选目标key | 高，微信入站崩溃 | weixin_identity_fix | 111项、生产只读无需修库 | 已关闭机制；真实入站待部署后 |
| D05 | R10–11 380／图标裁切 | 已实现并亲审；真WebView与桌面证据仍缺 | 高，本轮新包要求 | android_viewport_icon | 70项＋图标像素／mask亲审；真实UI待验 | 已关闭机制；UI未验 |
| E01 | R04–11实际UI | Work禁用隐藏IAB，禁止绕过 | 证据阻塞，不能伪造 | Validation | 合法隐藏IAB恢复或获授权入口后验证 | 未关闭；继续不依赖它的工作 |
| B01 | 范围外旧suite5失败 | 未改ee2ba55副本相同5失败 | 不归本轮，不放宽检查 | 已记录 | baseline和integration对照日志 | 范围外保留 |

## 取舍、快照与续接

冻结文档提交见baseline；它在已授权实现之后固定接续轮次范围，不重写此前实施顺序。用户托管允许范围内本地阶段提交，按根规则每次自动push，不提交原有不相关dirty。生产只读预检显示git干净、运行ed94619，非部署。本轮确认380覆盖390，不再询问宽度。最终dist与APK等所有前端完成再构建，不用旧dist提前交最终包。源码／依赖未变化的既有有效证据复用；只针对集成、失败修复和证据存疑补跑。
