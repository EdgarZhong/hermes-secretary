# 证据与边界

来源：用户 astra-investigation-20261020.zip，45 个条目，前一轮已核对其中 44 个文件 SHA256。本包不包含私人聊天、图片或原始抓取。

## 真实手机现场

同机约 865 KB 完整 cards，均 h2，非磁盘缓存：

| ID | 北京时间 | 条件 | 到 headers | headers 到完成 | 总耗时 |
|---|---|---|---:|---:|---:|
| 1927.166 | 22:21:59.090 | 蜂窝 | 2.8763 s | 65.3223 s | 68.1986 s |
| 1927.271 | 22:35:33.025 | Wi-Fi 过渡 | 0.9954 s | 0.2953 s | 1.2908 s |
| 1927.300 | 22:35:53.593 | 稳定 Wi-Fi | 0.2463 s | 0.1577 s | 0.4040 s |
| 1927.321 | 22:37:28.238 | 蜂窝 | 1.9354 s | 54.1548 s | 56.0901 s |
| 1927.348 | 22:39:55.888 | 蜂窝、回合后 | 7.9098 s | 56.7736 s | 64.6835 s |

来源：evidence/phone-observe-20261020T222118.jsonl、phone-observe-20261020T223500.jsonl，前台 target 2513。蜂窝正文有效接收约 13–16 KB/s，只描述这些请求，不代表套餐/基站带宽。

同期 15 个 WS ping 中位数约 0.2498 秒。小包正常不保证大响应正常；缺少实际 connectionId/remote IP，不能认定 WS 与 REST 共用 TCP。CDP 分块不是 TCP 包，不能据 16 KB 分块推断运营商限速。

记录的长任务合计 598 ms、最长 409 ms，但无完整 CPU trace。回环 history 200 约 0.062539 秒，旁证源站查询不是该一分钟的主要耗时；回环绕过公网及外层认证。

## 载荷和离线压缩

| 响应 | 原正文 B | 离线 gzip B |
|---|---:|---:|
| 200 cards，inline 图片 | 864734 | 545572 |
| full session | 215537 | 81333 |
| summary session | 51684 | 16901 |

来源：evidence/loopback-read-redacted.json、methods/loopback_read.py。gzip 是 Python 离线结果，不是线上 Caddy 实测，压缩实现和等级可能不同。

最大 data URL 651203 字符，占 cards 约 75.3%；对应最大 user row 651943 B。原包没有图片本体，尚不能证明该图通过文件一致性 helper。864734−651203=213531 只是算术，不是新投影的实际大小。

第一段完整观察有 14 个 details 请求，合计 832845 B encoded；另有两次 full metadata。details 未保存正文，不能套用 summary 压缩率。全部 REST 流量不等于首屏关键路径。

## 已证明缺陷

纯图片：原 reproduction/test_user_bubble_audit.py、reproduction/user-image-gap.test.ts、reproduction/findings.md 证明，空 text+images 受理后无 user row/accepted_user/committed event；worker 之后才写入。caption 路径初始行仅含文字，缺图片引用。旧测试用于证明 bug，修复后应改为正确期望，并移植其中本机绝对路径。

Noting：正常原生 max_iterations_reached 导致 completed=False，旧逻辑未提交且漏通知分类。现有补丁接回原 Commit Gate，不解决模型反复只检索，也不保证空 Notebook 生成有效内容。原 test_r3_child.py 最终 54 passed，含 13 新边界；一轮相关五文件 156 passed/2 failed，两项在未改代码对照中同样失败，不能称全套绿。

## 不应当作已证明根因

- 22:03–22:04 的 28 个 mobile GET / 302 与 anonymous denied 证明那段认证不足，未证明具体 cookie、Redis 或 2FA 原因。
- 17:58 的 4 个 desktop 502 每次约 3–6 ms、首末跨度 5.743 s，属于启动窗口，与晚间 302 分开。
- compact 摘要已在 DB/cards，row 10036、42305 B、继承 14:24 timestamp；无完整“找不到摘要”UI轨迹，不能直接重排。
- 文字缺气泡是用户报告，已有受控文字样本未复现同一缺口，不能用纯图片修复声称全覆盖。
- cancel 不都代表丢包；现有强制刷新中的部分取消保护写后新状态。
