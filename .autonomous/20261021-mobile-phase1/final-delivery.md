# 阶段一联合交付

目标已完成：阶段一与Noting修复一起部署首尔，后端提醒链及既有数据保持。用户C08允许先部署后简化Validation，C09禁止自动回退；本轮按最新口径执行。不开worktree，不使用Astra，未改冻结检查等级。

## 实际交付

- 后端Web／Gateway：`0bdddfc133b830dd73db3b3dfbe23bc20edfd4e1`。
- Secretary前端：`1d1b1a7c53b9baf86576d3c19ebdd5a8b9a98975`，构建439文件逐SHA核对。
- P1-01／08：Caddy2.11.7限定gzip／成功hashed静态private immutable，原生SIGUSR1重载；bootstrap／WS诊断不含敏感内容。鉴权仍Authelia。
- P1-02～05：usage summary；验证型图片引用及真正视口下载；显式详情需求；Thinking首次Markdown与detailSources稳定引用。
- P1-06：纯图立即持久refs／receipt／committed，worker认领同row/UID/owner/db；事务核活跃身份，默认旧调用兼容，失败不重复写。
- P1-07：原预算补丁已上线，未强行重复；并行Noting接收并亲审，K3原生Chat自有后缀声明冻结父工具缺少的canonical能力，不替换Provider或改父前缀。

## 验证与实测

相关测试／构建通过并亲审复用有效证据；最终冻结10检查通过，0blocking/advisory。附包CDP工具初次两项复杂度问题已等价拆分，51事件×3筛选及2非法输入输出一致。旧失败、首版Noting400及中间脚本错误原件保留，不冒称全仓全绿；未运行严格独立两门禁。

真实K3-256k／High在独立虚构Profile中73.35秒、6HTTP200／1Turn，3次maintain成功、显式finish、正式提交3条忠实索引；wire父前缀与顶层tools不变。成功运行164333 tokens；首400无usage，整体费用未知。不把短场景推广为长会话可靠性保证。

同一正式会话、同200行身份顺序：

| 指标 | 原 | 新 |
|---|---:|---:|
| cards raw正文 | 863366B | 212094B（-75.43%） |
| cards离线gzip | 544803B | 51160B |
| 同安装Caddy规则实际gzip | 原未启用 | 54696B（解码校验相同） |
| metadata full→summary消费者 | 215536B | 51683B |

1图可转换、fallback0，content651372B→90B；同Profile实际下载488384B与原文件相同。自建隐藏IAB→临时SSH回环→单一正式后端：静置约27秒details0／图片0；展开一张Thinking只1个单行GET／6783B；进入视口后1次图片请求且解码1920×2560，后续滚动无额外下载。所有观察GET request body为0B，主要收益是response bytes与请求时机。未称公网已登录浏览器压缩实测；公网只核Authelia入口正常，回环Caddy及浏览器时延不外推蜂窝。

## 部署及后端健康

01:28空闲准入、正常停启后端，真实JSON／微信连接就绪后发布前端；Caddy前idle短暂未通过，保留新版正常运行，重新空闲后续完加载，01:30完成。切换窗口7次连接拒绝502（14日志），之后未再出现；没有自动回退／回盖运行DB／重复停启后端。三库SQLite backup API、配置、Caddy及旧静态材料已保全。

原Alex10161、host2条消息的内容身份无改变／缺失；所有排期定义／generation／sequence／next时间及原微信绑定保持。目标7条Instant启用，最近**2026-10-21 10:00+08**；Scheduler扫描线程存在，原生冷恢复实际解析到Alex K3／Chat／High／262144及正确端点，现有KIMI_BASE_URL持久覆盖与有效池条目核对通过。Web／Gatewayactive/running、0自动重启、自启且Linger=yes、微信connected、发送工具可执行且SHA保持。01:33后验仍idle、pending0，Noting数量未增。

未提前触发提醒、未生产微信测试发送，未来自然到点尚未发生，不能写成已触达。阶段二、手机蜂窝实验、生产纯图发送Turn及公网已登录全流程未做；其余同一行／身份／失败路径由正式RPC／DB／Loop隔离测试覆盖。临时relay、SSH转发及本会话隐藏页均关闭；未动用户现有页面。

## 复核入口

完整实际版本、指标、失败及恢复过程在[运维记录](../../docs/operations-log.md)。本轮索引／计划及并行[Noting交付](../20261021-noting-kimi-chat/final-delivery.md)保留授权边界。ignored `.hermes-dev/mobile-phase1-20261021/`保存脱敏测量、脚本、源码hash、测试与部署日志；私人正文／图及三库只在首尔受限证据目录。备份在`/home/ubuntu/.local/state/hermes-secretary/mobile-phase1-20261021/deploy-20261021T012830/`；备份不代表自动恢复授权。先前独立手机调查文档dirty保留，未整树提交。
