# 本轮实施计划：20261021-mobile-phase1

## 目标与依据

按snapshot-index.md与baseline.txt完成阶段一、集成另一会话Noting／Provider、统一验证并首尔上线。优先打通图片历史瘦身与纯图持久受理；不改现有产品交互及数据身份。部署前同200行窗口取得原／新bytes、fallback与下载权限证据，完成独立Verification和Validation。保留原数据，代码／静态／Caddy可分项回退，不回盖运行库。

## 覆盖与任务

| 要求/口径编号 | 任务和正式路径 | 实现负责人及白名单 | 依赖和接口 | 验证方法 | 用户场景 | 完成条件 |
|---|---|---|---|---|---|---|
| P1-01、08/C02 | Caddy压缩／哈希资源缓存、bootstrap/WS/ready诊断、就绪／发布 | 主会话：部署／配置及最小集成；诊断前端由前端包实施 | 后端ready后前端opt-in；双方空闲后部署 | 配置校验、真实压缩协商／鉴权只读／监听／版本及重连 | 认证恢复、历史加载、草稿保留 | 目标JSON压缩，静态缓存边界正确，各宿主实际版本明确 |
| P1-02～05、08/C05 | usage summary、图片视口、cards/details opt-in、显式补水、Thinking首次展开、detailSources、分段诊断 | 前端Agent：../hermes-secretary-web/src/及其测试（不改后端／根文档） | prefer_image_refs=true，仍inline_images=true；不缩页／不删force | consumer审计、vitest、typecheck；随后浏览器真实UI | 文字／图／多图／滚动／展开刷新／切会话／复制编辑 | 正常消费者可取完整内容，无无需求请求，原动画状态保留 |
| P1-03/C05 | 查询页原结构helper验证→授权可下载→响应副本refs→cards/details | 投影Agent：hermes_cli/web_routers/sessions.py，必要同层sibling，相关新增测试；session_history.py只读 | 不改helper权限；与纯图包只读依赖 | 正式HTTP+SQLite，默认／fallback／跨Profile／下载 | 纯图／caption／多图／损坏／缺文件 | 默认兼容、身份不变，合法refs可下载，无越权 |
| P1-06/C05 | 原受理行持久refs、staged精确输入匹配、worker原位认领 | 受理Agent：tui_gateway/methods_submit_idle.py、session_workdir.py、session_history.py、prompt_turn.py、agent/turn_context.py、agent/image_routing.py及相关新增测试 | 与Noting会话接缝协调；不动provider／noting | 正式RPC+DB+worker屏障，native/text、持久失败／认领失败／旋转 | 纯图立即气泡，完成／刷新仍一行，原模型输入保持 | 同row/UID/owner，durable后失败保留，不重复／不伪回执 |
| P1-07/C02 | 已上线预算补丁确认与外部Noting最终包接收 | 外部会话；主会话亲审 | 不重复补丁；最终修复范围由用户在另一会话确认 | 复用有效证据，影响处定向集成验证 | Noting结束／失败／资源清理 | 有可接收最终版本与证据，不冒称调查即完成 |
| 全部/C01～07 | 集成、独立两门禁、构建、空闲窗口上线、回滚／证据 | 主会话+全新独立审查者 | 实现包亲审收敛后统一进门禁 | 同版本有效证据；必要真实入口取证 | 登录／草稿／历史／图／展开／发送／Stop/Steer | 全部适用要求证据闭环；缺口如实记录并继续整改 |

## 当前状态与编排

| 目标/任务 | 机制实现 | 正式接线 | 针对性验证 | 用户结果 | 当前负责人和下一步 |
|---|---|---|---|---|---|
| 前端包 | 待实施 | 待实施 | 待执行 | 待验 | 冻结后委派 |
| 后端投影 | 待实施 | 待实施 | 待执行 | 待验 | 冻结后委派 |
| 纯图受理 | 待实施 | 待实施 | 待执行 | 待验 | 冻结后委派 |
| 运维／集成 | 调查中 | 待接收 | 待执行 | 待验 | 主会话核生产版本、压缩、空闲与回退 |
| Noting／Provider | 外部会话负责 | 未交接 | 沿外部证据 | 未验 | 等最终包，联合发布 |

三个实现包文件不相交；session_history.py只有纯图包可改，投影包只读复用helper。子Agent不提交、不改动态核心文档、不再派生，不流水账；证据写ignored .hermes-dev/mobile-phase1-20261021/<包>/。前端包为所有前端文件唯一owner。主会话收到整包后亲审正式路径、数据与失败处理，再进入门禁。UI仅主会话创建隐藏IAB；不能合规则记录未验。

## 缺陷与整改

| 问题编号 | 要求与触发条件 | 当前事实与影响 | 优先级及理由 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|
| D00 | 联合上线依赖另一任务 | Noting／Provider尚未最终交接 | 发布前置 | 主会话／外部会话 | 接收diff／验证／宿主要求并集成验证 | 开放 |

## 取舍、快照与续接

初始后端HEAD 50214cd4ab95020fdfa522bc972ac20092829940；前端83285d2be259f1ee9f7e24bba6dd4c70688831fe。已有CLAUDE、README、operations-log修改及mobile调查文档属于先前／外部工作，本轮不擅自提交。冻结仅纳本轮核心文档hunk、轮次索引及用户指定任务包；规则文件和06／08／白板／07原已在基线树内。Git提交自动push，保留既有hook。不以基线跑大套；实现期相关验证，集成收敛后统一冻结检查及必要范围回归。
