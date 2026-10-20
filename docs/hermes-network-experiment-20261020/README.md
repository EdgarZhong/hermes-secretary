# Hermes：今晚优化上线 + 精简网络实验（修订版）

版本：2026-10-20.2。依据：用户当晚确定的实施顺序。

**第一板块实施并上线 → 10–15 分钟网络实验 → 带回结果 → 再设计第二板块重构。**

目标：固定首尔源站、手机不依赖 VPN/代理 App，保持现有产品表现和交互。第一板块复用现有读取、持久受理、图片下载和认证机制；第二板块再评估新同步契约、持久缓存、SSE/WS 和恢复状态机。

## 交付状态

本包是本地 coding agent 的实施指导、已有 Noting 补丁、精简实验设施和离线分析器。已核对原始调查包、固定提交及官方资料；此环境没有手机 ADB 或首尔 SSH，**未修改应用源仓库、未部署生产、未执行新的手机网络实测**。

审计基线：后端 fcf5d08ac587b43c5aafd2f3e8656a6c5b147432；前端 83285d2be259f1ee9f7e24bba6dd4c70688831fe。执行前重新查实际 HEAD 和工作树。调查本地 ecc6695 相对该后端仅多一项文档提交。

## 文件导航

| 文件 | 用途 |
|---|---|
| HANDOFF.txt | 直接交给本地 Agent 的任务入口 |
| PHASE1-IMPLEMENTATION.md | 第一板块的完整实施、验证、上线和回退 |
| EXPERIMENT.md | 上线后的短实验，替换此前大矩阵 |
| PHASE2-SCOPE.md | 第二板块边界和选型依据，完整设计等待实验结果 |
| UX_ACCEPTANCE.md | 条件估算、两阶段目标和验收口径 |
| EVIDENCE.md | 已有数字、已证明缺陷和证据不足之处 |
| patches/noting-budget-local.patch | 原调查包中的现有补丁 |
| conditions.example.json | 可选完整条件模板；短实验只填必要字段 |
| probes/ | 固定字节下载探针，每文件 30 秒主动中止上限 |
| tools/ | CDP JSONL 离线分析器及字段说明 |
| SOURCES.md / VALIDATION.md | 来源与交付校验边界 |

用户已授权今晚在验证后上线，不必重复征求同一意图的确认。遵守实际仓库和环境访问控制；遇到实际审批阻断，提交具体 diff、风险和阻断理由，不绕过。

## 本地准备探针

在解压目录执行；只生成无个人内容的本地文件，不部署、不自动测量：

~~~bash
python3 probes/make_assets.py --out-dir ./generated-assets
cp probes/probe.html ./generated-assets/probe.html
~~~

Agent 可在第一板块的部署窗口准备临时受保护路径，避免额外 reload。默认只测 8 KiB + 64 KiB，不默认测 1 MiB。

原调查离线复核示例：

~~~bash
python3 tools/summarize_cdp.py \
  ../astra-investigation-20261020/evidence/phone-observe-20261020T222118.jsonl \
  ../astra-investigation-20261020/evidence/phone-observe-20261020T223500.jsonl \
  --target 2513 --label historical_mixed_network_capture \
  --out-dir ./baseline-analysis
~~~

2513 只适用于原调查；新采集重新发现前台 target。原文件含换网过程，不能按文件名认定整份属于某一种网络。

回交：实施项/commit/部署版本、同一 200 行窗口的新旧 bytes 与图片 fallback 数、定向验证原始结果、发布和回滚记录、手机逐样本时序及剩余问题。不能通过丢图、丢历史或删除一致性保护凑速度。
