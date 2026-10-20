# 来源与选型依据

查阅日期：2026-10-20 至 21 日（北京时间）。以下区分现场、源码和一般网络原理；不能用标准文档证明某次请求的具体故障原因。

## 1. 用户现场

原 astra-investigation-20261020.zip：
- report.md；
- evidence/phone-observe-20261020T222118.jsonl、phone-observe-20261020T223500.jsonl；
- evidence/loopback-read-redacted.json、access-redacted-evening.json、service-events-redacted.json；
- reproduction/test_user_bubble_audit.py、user-image-gap.test.ts、findings.md；
- changes/noting-budget-local.patch；
- validation/README.md 及 noting-budget-*.log。

数值与边界汇总于本包 EVIDENCE.md。原调查包包含隐私，不复制到新任务包。

## 2. 本项目审计源码

前端固定提交：
[usage-view.ts](https://github.com/EdgarZhong/hermes-still-chat/blob/83285d2be259f1ee9f7e24bba6dd4c70688831fe/src/core/usage-view.ts)；
[controller.ts](https://github.com/EdgarZhong/hermes-still-chat/blob/83285d2be259f1ee9f7e24bba6dd4c70688831fe/src/core/controller.ts)；
[history-details.ts](https://github.com/EdgarZhong/hermes-still-chat/blob/83285d2be259f1ee9f7e24bba6dd4c70688831fe/src/core/history-details.ts)；
[projection.ts](https://github.com/EdgarZhong/hermes-still-chat/blob/83285d2be259f1ee9f7e24bba6dd4c70688831fe/src/core/projection.ts)；
[attachments.ts](https://github.com/EdgarZhong/hermes-still-chat/blob/83285d2be259f1ee9f7e24bba6dd4c70688831fe/src/core/attachments.ts)；
[App.tsx](https://github.com/EdgarZhong/hermes-still-chat/blob/83285d2be259f1ee9f7e24bba6dd4c70688831fe/src/App.tsx)；
[api/client.ts](https://github.com/EdgarZhong/hermes-still-chat/blob/83285d2be259f1ee9f7e24bba6dd4c70688831fe/src/api/client.ts)。

后端固定提交：
[sessions.py](https://github.com/EdgarZhong/hermes-secretary/blob/fcf5d08ac587b43c5aafd2f3e8656a6c5b147432/hermes_cli/web_routers/sessions.py)；
[session_history.py](https://github.com/EdgarZhong/hermes-secretary/blob/fcf5d08ac587b43c5aafd2f3e8656a6c5b147432/tui_gateway/session_history.py)；
[methods_submit_idle.py](https://github.com/EdgarZhong/hermes-secretary/blob/fcf5d08ac587b43c5aafd2f3e8656a6c5b147432/tui_gateway/methods_submit_idle.py)；
[session_workdir.py](https://github.com/EdgarZhong/hermes-secretary/blob/fcf5d08ac587b43c5aafd2f3e8656a6c5b147432/tui_gateway/session_workdir.py)；
[prompt_turn.py](https://github.com/EdgarZhong/hermes-secretary/blob/fcf5d08ac587b43c5aafd2f3e8656a6c5b147432/tui_gateway/prompt_turn.py)；
[turn_context.py](https://github.com/EdgarZhong/hermes-secretary/blob/fcf5d08ac587b43c5aafd2f3e8656a6c5b147432/agent/turn_context.py)；
[image_routing.py](https://github.com/EdgarZhong/hermes-secretary/blob/fcf5d08ac587b43c5aafd2f3e8656a6c5b147432/agent/image_routing.py)；
[noting_child.py](https://github.com/EdgarZhong/hermes-secretary/blob/fcf5d08ac587b43c5aafd2f3e8656a6c5b147432/secretary/noting_child.py)；
[turn_failure_copy.py](https://github.com/EdgarZhong/hermes-secretary/blob/fcf5d08ac587b43c5aafd2f3e8656a6c5b147432/agent/turn_failure_copy.py)。

执行时以实际 HEAD 为准，不能依据旧 SHA 覆盖新改动。

## 3. Cloudflare 原理及边界

- [DNS proxy status](https://developers.cloudflare.com/dns/proxy-status/)：橙云代理、灰云仅 DNS。
- [Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/)：源站 cloudflared 主动连接 Cloudflare，区别于公网 HTTPS 回源。
- [Geographic traffic routing](https://developers.cloudflare.com/support/troubleshooting/general-troubleshooting/geographic-traffic-routing/)：anycast/ISP 路由不保证最近机房；不能按 zone/account 任意钉住香港/首尔。IPv4/v6 可能走不同路径。普通全球网络不等于中国网络。colo/CF-Ray 是机房证据，IP 地理库不等于真实入口；部分 origin 日志中的 CF-Ray 还可能描述回源出口。
- [WebSockets](https://developers.cloudflare.com/network/websockets/)：WebSocket 支持与产品兼容性；Argo 在其表中为 No。
- [CDN architecture](https://developers.cloudflare.com/reference-architecture/architectures/cdn/)：缓存与动态回源、Argo 的网络内路径优化，不能替代用户接入段。
- [China Network](https://developers.cloudflare.com/china-network/) 和 [Global Acceleration](https://developers.cloudflare.com/china-network/concepts/global-acceleration/)：独立商业产品/资格，并非普通免费橙云获得国内入口。具体资格/价格须按实际方案确认。
- [腾讯云 EdgeOne 国际加速](https://cloud.tencent.com/document/product/1552/96054)：可作为有额外商业条件的候选；不是未经手机测试的保证。今晚不采购。

本案判断：既有 Wi-Fi 负面经验 + 实际入口不保证，普通橙云只保留现成入口的蜂窝短对照；不默认重建 Tunnel 或买 Argo。

## 4. 网络与浏览器

- [RFC 6298 TCP retransmission timer](https://www.rfc-editor.org/rfc/rfc6298.html)：超时估计及重复超时退避；说明丢失/不稳定 RTT 的延迟可能非线性，不能证明本案实际重传次数。
- [RFC 9913](https://www.rfc-editor.org/rfc/rfc9913.html)：无线链路/移动网络特性及传输适配背景。
- [RFC 9113 HTTP/2](https://www.rfc-editor.org/rfc/rfc9113.html)：HTTP/2 运行于 TCP；多流不消除底层按序交付约束。
- [RFC 8305 Happy Eyeballs v2](https://www.rfc-editor.org/rfc/rfc8305.html)：地址族选择与连接建立，不保证后续吞吐最佳。
- [RFC 6888 CGN requirements](https://www.rfc-editor.org/rfc/rfc6888.html)：运营商 NAT 背景；CGN 不是自动慢的诊断结论。
- [Chrome Network reference](https://developer.chrome.com/docs/devtools/network/reference/)：Timing、协议、远端地址、连接等观察口径。Content Download 也受浏览器处理影响。
- [Chromium NetLog](https://www.chromium.org/for-testers/providing-network-details/)：需要时短时采集，避免敏感 raw bytes/cookies 模式。

同省/同品牌运营商不保证固定宽带与移动核心网、出口、地址族和回程相同。这里是一般原理，实际路径仍以手机请求和服务器关联为准。

## 5. 代理与流

- [Caddy encode](https://caddyserver.com/docs/caddyfile/directives/encode)：已有 gzip 能力、匹配与协商。
- [Caddy reverse_proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)：默认 reload 对 WS 的关闭行为、流式转发。使用已安装版本，不能照最新版本特性盲改旧安装。
- [WHATWG Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)：SSE/Last-Event-ID/重连语义。可靠恢复仍由应用保证。

SSE 不直接提高带宽，也不自动保证历史一致性；WS 在这次现场的小包表现并不支持“立刻换掉就会快”的结论。
