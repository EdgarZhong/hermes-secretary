# 云端 Embedding 与服务器降配估算

> 日期：2026-10-19 · 性质：**估算，未实施任何改动** · 数据来源：云服务器实测（`/proc/meminfo`、cgroup、llama.cpp 日志、systemd 记账）

## 1. 结论

1. **即使去掉 OpenClaw、embedding 全部上云，4G 仍是合理下限，2G 依旧不建议**；
2. 云 embedding 的真实收益是省约 **540 MiB 总足迹**、消除 2 秒召回超时、把 CPU 让给 Hermes/Ebbinghaus；
3. 月成本可忽略：按真实用量 0.3M tokens/月，放大 5 倍也只需 **¥0.5–¥1/月**。

## 2. 实测基线（8 GiB 机器）

| 指标 | 实测值 |
|---|---|
| MemTotal | 7.5 GiB |
| AnonPages | 2383 MiB |
| Slab（可回收/不可回收） | 709 / 119 MiB |
| Cached | 3646 MiB（可回收） |
| Swap | 4 GiB，已用 91 MiB |
| 30 天 OOM | 0 次 |

主要进程 RSS：nmem 1334 MiB、OpenClaw 708 MiB、hermes 490 MiB、journald 230 MiB、fwupd 191 MiB、Ebbinghaus 171 MiB、cloudflared 41 MiB、Caddy 35 MiB、mihomo 35 MiB。

## 3. NM 内存解剖

| 组成 | 占用 | 依据 |
|---|---|---|
| KuzuDB buffer pool | 512 MiB（下限） | 启动日志 `buffer_pool_mb=512 auto_floor_mb=512 auto_cap_mb=1024` |
| llama.cpp 计算缓冲 | 112 MiB | 日志 `CPU compute buffer size = 112.05 MiB` |
| KV cache / 上下文 | ~50 MiB | 估算 |
| 运行时、索引、其他 | ~130 MiB | 差值 |
| **匿名内存合计** | **~800 MiB** | 实测 `Pss_Anon = 802 MiB` |
| 模型文件（可回收） | 379 MiB | `Qwen3-Embedding-0.6B-Q4_K_M.gguf` |

云端 embedding 后：匿名约 **640 MiB**（−160），RSS 约 **950 MiB**（−379 文件页）。KuzuDB 的 512 MiB 与 embedding 无关，仍然存在。

## 4. 三场景对比（估算，±100–150 MiB）

| 组件 | A 现状 | B 去 OpenClaw | C 去 OpenClaw + 云 embedding |
|---|---|---|---|
| nmem | 800 | 800 | **640** |
| hermes | 550 | 550 | 550 |
| Ebbinghaus | 170 | 170 | 170 |
| OpenClaw | 690 | 0 | 0 |
| 系统 + daemon | 170 | 170 | 170 |
| 不可回收 slab/内核 | 170 | 170 | 170 |
| **匿名合计** | **~2.5 GiB** | **~1.85 GiB** | **~1.70 GiB** |
| 页缓存需求 | ~0.4 GiB | ~0.4 GiB | ~0.1 GiB |
| **实际驻留** | **~2.9 GiB** | **~2.25 GiB** | **~1.8 GiB** |

## 5. 2G / 4G 判定（按峰值，不按均值）

| 规格 | 场景 C 均值 | 峰值估算¹ | 余量 | 判断 |
|---|---|---|---|---|
| 2G | ~1.8 GiB | ~2.2 GiB | 峰值时为负 | ❌ 平时能跑，峰值必 swap |
| 4G | ~1.8 GiB | ~2.2 GiB | ~1.8 GiB | ✅ 舒适 |
| 8G（现状） | ~2.9 GiB | ~3.5 GiB | ~4.5 GiB | ✅ 最宽裕 |

¹ 峰值 = NM 触及 MemoryMax + Hermes 压缩峰值（cgroup 实测 1639 MiB）+ 其他服务。

**降级建议：2C4G，不碰 2C2G。** 降级前需把 NM `MemoryMax` 从 4G 调到 ≤2G、限制 journald、屏蔽 fwupd。

## 6. 云 Embedding 的收益与代价

**收益**
- 匿名内存 −160 MiB，页缓存 −379 MiB；
- 消除本地 2048-token 批量阻塞导致的 2 秒召回超时（近 24h 72 次）；
- CPU 从推理中释放，查询变成 30–80 ms 网络往返；
- 本地不再需要 379 MiB 模型文件与 112 MiB 计算缓冲。

**代价**
- 个人记忆内容出机器（隐私边界需用户确认）；
- 依赖网络与厂商可用性（保留 FTS 兜底）；
- 每次召回多一次 HTTPS 往返。

## 7. 月成本估算

真实用量基线：约 0.3M tokens/月（增量 0.12M + 查询 0.2M）。

| 用量 | Qwen v3（¥0.5/1M） | 3-small（$0.02/1M） | 3-large（$0.13/1M） |
|---|---|---|---|
| 1×（0.3M） | ¥0.15 | $0.006 | $0.04 |
| 3×（0.9M） | ¥0.45 | $0.018 | $0.12 |
| 5×（1.5M） | ¥0.75 | $0.03 | $0.20 |
| 10×（3M） | ¥1.5 | $0.06 | $0.39 |

全量重嵌入（470,876 tokens）一次性成本：Qwen ¥0.24 / 3-small $0.009 / 3-large $0.06。

> 对照：升级到 8C16G 约 +¥150–400/月，加 GPU 约 +¥1,500–2,500/月。API 成本低 2–3 个数量级。

## 8. 迁移清单（待批准后执行）

**前置**
1. 选定厂商并确认 API key（国内端点优先，规避 NAT 出口对 OpenAI 的不可达）；
2. 实测端点连通性与单次 embedding 延迟；
3. 确认 NM 0.10.101 的云端 embedding 配置方式（`NMEM_EMBED_*` / `remote_llm.json purposes.embedding`）；
4. 备份 `content.db`、`search_index`、`remote_llm.json`。

**执行**
1. 写入云端 embedding 配置；
2. 重启 NM 并确认不再加载本地 GGUF（日志无 `loading local embedding model`）；
3. 全量重嵌入 4,860 chunks，重建索引；
4. 抽样验证检索质量与延迟。

**验证点**
- 日志无 `query embedding timed out`；
- 召回 P95 延迟；
- Hermes 侧 `recall_timeout` 是否可维持 2s（云端通常更快）；
- 进程 RSS 与 cgroup 峰值。

**回退**
- 保留原 `remote_llm.json` 与本地模型文件；配置回滚 + 重启 NM 即恢复本地推理（索引需按原模型重建）。

## 9. 未决事项

- 厂商与 key 由用户确认；
- 是否保留本地模型作为离线兜底（保留则多占 379 MiB 页缓存）；
- 降级与 embedding 迁移的先后顺序（建议先迁移、观察峰值，再降配）。

## 10. 决定（2026-10-19 用户确认）

用户已确认部署转向，本估算作为该决定的依据记录在案：

- **目标**：腾讯云**首尔**地域轻量应用服务器，**2 vCPU / 4 GiB / 60 GiB SSD**；
- **迁移**：NM（Nowledge Mem，Hermes 侧使用）与 Ebbinghaus（爱宾豪斯）数据托管；**OpenClaw 不迁移**（新机上不再使用）；
- **Embedding**：NM 不再加载本地 GGUF，改用云端 embedding API；厂商与 Key 待定；
- **现北京服务器**：退出部署目标，其上服务保持现状作过渡运行，不再做降配/迁移/隧道改造；
- **规格一致性**：本报告结论「4G 为下限、2G 不可行」与所选 2C4G 一致；云 embedding 月成本按 5 倍用量估算 < ¥1；
- **状态**：首尔服务器已创建、访问私钥已下载；**尚未放置私钥、尚未配置 SSH、尚未迁移**；现网未改动。

