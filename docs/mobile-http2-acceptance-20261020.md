# 手机端网络恢复与历史分层加载 · 修复验收（2026-10-20）

部署后由本机 DSH 执行的真实手机 Chrome + 桌面 Chrome 双端复测，验收 A1–A7。
任务书：[mobile-http2-retest-task.md](mobile-http2-retest-task.md)；判定口径：[next-round-acceptance.md](../.hermes-dev/mobile-http2-retest-20261019/next-round-acceptance.md)。

**2026-10-20后续收尾口径：** 用户确认手机首触Send目前未发现问题、会话列表挂账关闭、分层总流量不构成问题；以下保留当时版本实测，不再自动作为当前待办。侧栏源码复核表明手机下桌面副本为`display:none`，抽屉使用Radix modal；当时脚本误选隐藏节点只证明自动化定位失败，原汇总声称读屏／键盘“均受影响”证据不足，现予纠正，不能当作已实证用户缺陷。当前状态与追加调查见[CLAUDE](../CLAUDE.md)和[运维记录](operations-log.md)。

## 被测版本

| 项 | 值 |
|---|---|
| 后端 | `9a0c479`（HEAD `474e4939`，部署文档提交），00:17:17 重启，PID 208810 |
| 前端 | `index-CRPV46M2.js`（456 文件） |
| 协议 | HTTP/3 仍暂停（`protocols h1 h2`，UDP/443 无监听）；全程 h2 |
| 客户端 | PHZ110/Android 16 手机 Chrome；桌面 Chrome「Edgar」隐藏标签 |
| 模型 | 两端 `deepseek-flash` |

部署后 HEAD 前进触发 stale-module 防护（模型选择 503），核对 `session_turn_leases=0` 后重启一次后端解除；本次未改代码、DB、索引、分页。

## 执行

| 轮 | 发起 | 任务 | 结果 |
|---|---|---|---|
| R1 | 桌面 | 5×30s 串行 terminal | 5 tool 完成，`message.complete` 00:23:56.663 |
| R2 | 手机 | 2×30s | 2 tool，`message.complete` 00:27:15.017 |
| R3 | 手机 | 5×30s + 关标签重开 + 旧会话 | 5 tool，`message.complete` 00:30:47.698 |

测试对话：`20261020_002114_4cd698`。

## 判定

| # | 目标 | 判定 | 本轮 | 上一轮基线 |
|---|---|---|---|---|
| A1 | 本端已接受输入即时可见 | 已修复 | 提交→气泡 1.36s / 0.34s（回执后 0.67s / 0.02s） | 13.49s / 9.31s |
| A2 | 跨端 user 实时补齐 | 已修复 | 桌面行在 `message.start` 后 0.22s / 0.06s | 68.63s，晚于 complete |
| A3 | 标题不依赖大列表 | 已修复（擦线） | 标题在侧栏 0 条时出现：4.0s / 5.28s / 0.51s | 90s 仍 `Conversation` |
| A4 | 列表合并/取消/限流 | **未达成** | 291s 内 72→137 次，5.00→4.28MB，峰值 3→3 | — |
| A5 | 历史分层加载 | 已实现 | `view=cards` + `detail_row_ids` 分批；重载 5.2s 出正文 | 无分层 |
| A6 | 旧会话 274KB | 首屏已修复 | 标题 4.0s、首文 5.74s；总字节 479KB | 完成 30.55s，363KB |
| A7 | 一致性/无回归 | 通过 | 5/2/5 tool、三次 complete、全 h2、无 QUIC 错误 | — |

### 关键证据

- **A1/A2**：`prompt.submit_idle` 回执（`00:26:10.404` / `00:28:05.990`）后气泡即现；桌面 user 行由 WS `message.user_committed`/`message.start` 驱动，不再等 history 回读。
- **A3**：关标签重开 5.28s、旧会话 4.0s 时 `visible links = 0`，标题来自会话详情而非列表；侧栏切回 0.51s。
- **A4**：`summary=true` 把单次 alex 列表 590KB→93KB，但每周期固定拉 3 个 profile，请求数翻倍；未观察到取消。
- **A5/A6**：服务端实际收到 `view=cards` 首屏 + 多批 `detail_row_ids`；旧会话详情 8 批共 259KB，最后一批约 14.4s 发起。

## 仍未修复

1. 手机**首次触摸 Send 不提交**（R2/R3 各一次，10s 后第二次触摸成功），与上一轮 R3 同类。
2. **A4 列表**：次数上升、字节持平、无取消。
3. **分层不省流量**：旧会话 479KB vs 363KB（+32%），后台补水仍整页排队。
4. 移动端**侧栏双份 DOM**：当时自动化查询误选隐藏的桌面副本并取得零尺寸坐标，未证实用户触摸／键盘／读屏受影响；原“均受影响”汇总已按后续源码复核纠正。
5. 部署卫生：HEAD 前进未重启会触发 stale-module 503，挡住模型切换（本次已重启解除）。

## 边界

- 本轮手机路径明显好于上一轮（无 100s 级写出卡顿），延迟类改善不能全归因代码；载荷下降、事件驱动渲染、标题脱离列表可归因代码。
- 桌面窗口中的 581KB 非 summary 列表来自部署前已打开、仍跑旧 bundle 的用户标签，不计入新代码。
- 不据日志推算丢包率；未恢复 HTTP/3。

## 证据

原始证据在 `.hermes-dev/mobile-http2-retest-20261019/runs/20261020T001037+0800/`（ignored，不入库）：

- `report.md` 完整报告、`acceptance.json` 逐条判定、`metrics.json` 可复算指标
- `manifest.json`：118 文件 / 18,083,408 B，SHA256 `ecf2764e6fe585162e75f9b62eea993b236abd615df9018823f53ee18d7d4de0`
- 固定副本 `preserved-20261020T0045+0800/`，逐文件校验通过
- 复算：`.venv/bin/python final_analysis.py`
