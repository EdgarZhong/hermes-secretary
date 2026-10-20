# CDP JSONL 离线汇总工具

`summarize_cdp.py` 使用 Python 3.9 及以上版本，仅依赖标准库。它只读取本地文件、生成汇总，不连接手机、浏览器、服务器或互联网。

输入格式是调查包 `methods/phone_observer.py` 生成的**脱敏、扁平 JSONL**，不是 HAR，也不是未经转换的 CDP 原始协议消息。一个文件是一份独立采集源；不同文件不会自动续接请求或去重。

## 使用

```bash
python3 tools/summarize_cdp.py \
  /path/to/phone-observe-first.jsonl \
  /path/to/phone-observe-second.jsonl \
  --target 2513 \
  --label baseline-mixed-networks \
  --out-dir /path/to/analysis-output
```

- `--target` 可重复使用；省略时包含所有 target。旧调查的前台 target 是 `2513`，旧后台页是 `2520`，新采集不能直接沿用旧编号。
- `--label` 是使用者为本次输入标记的条件；它不会把一份混合 Wi-Fi／蜂窝日志自动变成纯蜂窝样本。
- 多个条件建议分别运行到不同输出目录，使用不同 label。若放在一次调用中，顶层统计会混合这些条件。
- 输出目录中的 `requests.json`、`summary.json` 会被原子替换；输入文件不修改。同一路径重复输入会报错，防止误算两次。
- 非法 JSONL 会报文件名与行号并停止，不回显原始行；已经存在的结果不会因为解析错误而被重写。

## 输出

### requests.json

顶层包括 schema 版本、label、采集源文件名／SHA256 和 `requests` 数组。

每项以 **source + target + request_id + hop_index** 定位。即使两个文件或两个标签页出现相同的 request ID，也不会串在一起。HTTP 重定向复用的 request ID 会拆成独立 hop；前一跳不会被后一跳的 200 成功覆盖。

| outcome | 含义 |
|---|---|
| `completed` | 观察到 `Network.loadingFinished`，只代表浏览器网络层传输结束 |
| `failed` | 观察到 `Network.loadingFailed`，且没有取消证据 |
| `cancelled` | `canceled=true` 或错误码为 `net::ERR_ABORTED` |
| `redirected` | 后续 requestWillBeSent 的 redirect_status 标明上一跳发生 HTTP 重定向 |
| `capture_truncated` | 文件结束时尚无终止事件；不推断超时或网络断开 |
| `superseded_without_redirect` | 未见重定向标记时，同一个活动 request ID 又出现新请求起点；保留不完整旧记录 |

`cancelled_by` 一律为 `unknown`：这些事件不能区分用户取消、页面导航、Controller AbortController 等具体来源。`completed` 也不保证 HTTP 成功、JSON 已解析或气泡已可见；另看 `status`／`http_result`。

若采集从请求中途开始，仍保留可见的响应／结束事件，但 `start_observed=false`，无法计算的耗时保持 unknown。重定向的前一跳若没有请求起点，也保存为缺少起点的部分记录。

### 时间与字节口径

- `total_seconds`：终止事件 `ts` 减请求起点 `ts`。重定向 hop 的终点只能用下一跳请求出现的时间，`end_time_basis` 会明确标注，不当作普通完整下载。
- `headers_seconds`：`responseReceived.ts - requestWillBeSent.ts`，表示 CDP 响应头事件出现；不是精确 TCP 首包时间。
- `body_after_headers_seconds`：终止事件到响应头事件的差；失败／取消记录表示在失败／取消前观察到的阶段长度。
- 耗时**只用浏览器单调时钟 `ts`**。`wall` 仅转换为 UTC 展示，不在缺少 ts 时偷偷代替。
- `encoded_bytes`：只取 loadingFinished 的 encodedDataLength；通常包括响应头，不等同纯 JSON 正文、TCP 字节或套餐计费流量。失败／取消时不会用已观测分片字节冒充完整响应体积。
- `observed_data_bytes`／`observed_encoded_data_bytes`：分别累加可见 dataReceived 中的 dataLength／encodedDataLength。没记录分片或某个分片字段缺失时为 unknown，而不是零。
- `data_event_count=0` 仅表示没有观测到分片事件，不能证明没有正文。
- `cdp_resource_timing` 仅保存安全白名单时序字段；其中 CDP 的 `-1` 表示该阶段不可用／不适用，不能拿来计算耗时。

缺失的数值、布尔值或新字段统一输出字符串 **`"unknown"`**。显式零字节与 `false` 会保留。旧采集器没有记录 connectionId、remoteIPAddress、fromServiceWorker 等字段，工具不会编造；protocol=h2 与 fromDiskCache=false 也不证明其他缓存来源一定不存在。

### 正文进展间隔

dataLength 或 encodedDataLength 为正的 dataReceived 才算一次可观察的网络正文进展。零字节事件不会把一次长停顿人为切短。

`max_body_progress_gap_seconds` 取以下**有效非负间隔**中的最大值：

1. 响应头 → 第一批有字节进展；
2. 相邻两批进展；
3. 最后一批进展 → 终止事件。

同时输出首段、尾段和 `progress_gap_coverage`。缺少头／尾事件、或存在负时间差时，覆盖标为 partial／unavailable，不能把最大值当成完整请求的确定最大停顿。负差会留在 `timing_anomalies`，不静默钳成 0，也不改用主机 wall 时间。原始 Chrome 数据中确实可能有很小的事件时戳交错。

若完全没有正字节分片，最大进展间隔保持 unknown；另外报告 `headers_to_end_without_progress_event_seconds` 作为观测空窗。它不能证明整段时间都没有网络进展。文件末尾也不会被冒充 loadingFinished；截断记录仅可提供 `observed_until_seconds` 的观测跨度。

这些分片是 CDP 事件，**不是 TCP 包**。长间隔不能直接证明重传、运营商限速或具体哪一跳故障。

### summary.json

包含总数、按 outcome／HTTP 状态／protocol／磁盘缓存标记的计数，以及按 source、target、请求类型分组的统计。

耗时统计只包含有请求起点、网络传输完成且 HTTP 为 2xx 的记录。失败、取消、重定向、文件截断不混入成功延迟。缺失／无效指标不当作零；每项指标独立提供 `n`、`min`、`median`、`max`，因此不同指标的 n 可能不同。

**不计算 p95，不作 SLA 推断。** 小样本、不同网络条件、后台页、连接复用、缓存和不同时段可能混杂；即使有若干成功样本，也不能排除用户历史上的偶发问题。顶层统计只是输入样本描述，判因时必须检查 per-request 条件与来源。

## 内容边界

工具只提取元数据白名单：方法、主机／去掉查询串的路径、有限分页参数、状态、时序、体积、连接／缓存标记等。它不提取或输出响应正文、请求正文、Cookie、Set-Cookie、Authorization、完整 URL／查询串、WS frame 正文或 COOKIE_METADATA 内容。任意浏览器错误消息也不原样复制，只保留 `net::ERR_*` 错误码。

`observed_network_types` 来自 UI_STATE 的连接类型采样，不是逐字节路由证明；一次请求中出现 cellular 和 wifi，应视为有换网观察，不用 label 强行覆盖。它不能替代实际远端 IP、ASN 与连接 ID 证据。

实际采集日志与生成结果不属于这个工具交付物。验证时请把它们留在独立私有分析目录，不加入可公开分发的实验代码包。
