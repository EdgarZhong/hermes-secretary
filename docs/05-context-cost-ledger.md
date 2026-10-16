# 上下文开销记录（Context Cost Ledger）

记录产品改动对 LLM 上下文的开销影响。每次涉及 prompt 文本、工具 schema、消息载体的改动，在合并前按本文档的口径测量并追加一条记录。

## 测量口径

- Token 计数：`tiktoken` `o200k_base`（`uv run --with tiktoken`，无模型调用）。
- **完整 profile 基线** = 无 Secretary 的 root system prompt（实测 2,796）＋ Hermes 默认全量工具面（56 个工具 schema，实测 23,639）≈ **26,435 token**。
- 隔离测试 profile（仅 session_history + notebook_show 两个工具）不是基线，只用于取真实请求中的文本。
- Secretary 增量 = guidance 段＋Secretary 引入主会话的工具 schema（session_history、notebook_show、noting_memo）；不含 cron 提示词修订（描述文本级，增量可忽略）。
- Noting 追加 = task instruction＋`<noting-tools>` 控制消息（首条与每次 continuation 全量重发）；当前 Notebook 状态另计（随条目数变化）。

## 记录

### 2026-10-11 基线（V1.5 收口 / V1.6 施工前）

| 项目 | token | 占基线 |
|---|---|---|
| Secretary 主会话增量·现行（guidance 411 + session_history 317 + notebook_show 47） | 775 | 2.9% |
| Secretary 主会话增量·V1.6 目标（guidance 823 + 上列 schema + noting_memo 232） | 1,419 | 5.4% |
| Noting 首轮追加·现行（instruction 294 + `<noting-tools>` 2,239） | 2,533 | — |
| Noting 首轮追加·V1.6 目标（instruction 294 + `<noting-tools>` 3,237，三工具拆分后） | ≈3,531 | — |

分解备注：

- guidance 823 中身份段两例约占 300；三工具 schema（manage/edit/schedule + session_history + notebook_show + finish_noting）合计 ≈3,237，比单 `notebook_mutate` 版（2,239）多 ~1,000（entry_type 枚举与字段并集在三个 schema 中不可避免重复）；属已接受的拆分代价。
- History Search 截断预算：search 单行 content 超 ~800 字符就地截断并标记（全文唯一通道为 `read` + `message_uid`），20 条上限的 search 结果 ≈4–6k token，有界。

### 2026-10-15 Round Two Noting 成本模型（分析，非配置变更）

用户确认的分析口径：input 单价归一为 1，cache input 为 m，output 为 n；初始上下文 s=50K，每次 compact 后 r≈70K，w=256K，每次使用之间缓存完全失效，单次新增 d 分别为 30K／50K／80K。只统计基准方案在窗口内放得下的完整使用次数 H=floor((w-s)/d)，分别为 6／4／2 次，不计窗口满后的原生压缩。两边使用次数及新增内容相同。比较完全不开 Noting、每次使用后 Noting 并在达到 p 时 compact、仅达到 p 时 Noting+compact。触发判断在每次使用结束时进行。

基准冷启动历史 input 为 B=Hs+dH(H-1)/2，分别为 750K／500K／180K。令 x₁=s、yᵢ=xᵢ+d、bᵢ=1[yᵢ≥p]，xᵢ₊₁ 在 bᵢ=1 时为 r，否则为 yᵢ。每次 Noting 策略 aᵢ=1，仅阈值策略 aᵢ=bᵢ。Noting 成本 N(y)=U(y)+mV(y)+nO(y)，独立压缩成本 F(y) 同样按三个 bucket 计费。可识别的比较成本 C(p)=Σ[xᵢ+aᵢN(yᵢ)+bᵢF(yᵢ)]；省钱要求 C(p)<B。主会话内部其他 API 请求的缓存重放成本缺少使用次数及请求分布，未据此宣称完整总账或整账节约比例。数值表按策略计入末次使用结束触发的后台任务；若明确停止后台任务，应另算。

数据源：`.hermes-dev/round2-runtime/state.db` 的 `session_model_usage`（Noting 正常 loop 用 task=''，压缩单独用 task='compression'）与 `logs/agent.log` 的逐 API prompt/cache 记录。冻结前缀完整计费，Force 包含在 500 秒组。沿用此前样本截止 2026-10-15 17:51:33，2 秒组 19 个任务、500 秒组 5 个任务（4 Idle+1 Force）。均为 DeepSeek 运行量，不能称为 K3 实测。

阈值扫描采用可解释的前缀重放近似：每个样本首 API 的完整 prompt P 作为长度代理，逐调用以 min(cache_read,P,prompt) 分配缓存前缀，剩余分配为未缓存前缀；其余 token 作为本次任务附加量。把前缀长度缩放至 y，再取同组平均；保留组内实测调用次数、附加输入和输出分布。它仅模拟前缀长度变化，未证明任务复杂度、输出和调用次数随新增长度的真实函数，更不是非线性拟合。因 P 也含任务追加文本，y 作为父上下文长度时存在代理误差。

估计系数（token 单位，近似值）：

| 样本 | U(y) | V(y) | O(y) |
|---|---|---|---|
| 2 秒，19 任务 | 26584.11+0.105025y | 85521.53+5.263396y | 7963.11 |
| 500 秒，5 任务，含 Force | 76466.60+0.311297y | 262364.00+6.288649y | 14982.00 |

Noting 子会话中两次独立 compression 请求的暂用均值 F≈13213.5+6661n（cache=0）；样本少、长度小，不能保证大上下文压缩也达到该成本。

官方 Kimi K3 国际站价格参考为 input $3/M、cache hit $0.3/M、output $15/M，即 m=0.1、n=5（[官方入口](https://platform.kimi.ai/)、[缓存及写入计费](https://platform.kimi.ai/docs/guide/context-caching)）。默认 5min cache write 单价与 input 相同；互斥 bucket 不重复相加。1h 写入更贵，需增加独立写入系数。这里按用户要求把应用窗口设为 256K。数值只换单价并沿用实测缓存分布：真实 K3 默认 5min TTL 下，500 秒 idle 后首个 Noting 可能丢失父缓存，实际费用会更高。

500 秒组在上述价格下 N(y)≈177613+0.940162y，F≈46518.5。p=120K 的比较成本如下（单位为 K 个原价 input 的等价费用，非整账 token 总数）：

| 单次新增 | 次数 | 不开 Noting | 每次 Noting | 仅阈值 Noting |
|---|---|---|---|---|
| 30K | 6 | 750.0 | 2259.2 | 1182.1 |
| 50K | 4 | 500.0 | 1600.7 | 1329.1 |
| 80K | 2 | 180.0 | 831.5 | 831.5 |

扫描 70K<p≤256K 后，在该估计模型下两种策略均无严格省钱阈值。仅阈值策略不触发任务时与基准持平（分别为 p>230K／250K／210K）。强制至少触发一次时，30K 情况最便宜 p∈(140K,170K]，成本 933.96K，仍贵 183.96K；50K 最便宜 p∈(150K,200K]，成本 782.16K，仍贵 282.16K；80K 在末次才触发没有区间内收益。

作为敏感性对照，2 秒组代入同一 K3 价格、同样计入独立压缩时也无省钱 p，但 30K 的仅阈值策略 p∈(140K,170K] 接近盈亏平衡，成本 778.80K。该区间的费用不等式为 980298.84m+14624.105n<142348.129；固定 n=5 需要 m<0.070619，固定 m=0.1 需要 n<3.03049。500 秒组同一区间为 1331434.316m+21643n<57399.430；n=5 时即便 m=0 也不满足。结论只适用于用户指定的有限使用区间、当前统计估计和末次任务口径，不外推为持续使用的长期结论。

后续定性讨论的用户明确前提：Noting 应在父缓存仍热时执行，idle delay 的设计目的包括保证这一点；父缓存过期不是期望运行条件。上述沿用实测缓存分布的费用表保留为历史估算，不能作为未来热缓存联合触发方案的定论。Notebook 是否收缩、是否与 compact 联合触发仍在讨论，尚未批准实现或配置变更。成本评价还应增加“只改进原生 compact／热缓存时机、不维护 Notebook”的基准，不能把压缩本身的收益全部归给 Notebook。

用户随后进一步明确 Notebook 的独立目的：作为跨 Compaction 的工作信息索引，指导 Main 查阅既有事项，再通过现有 History Search 回查原文并恢复多轮摘要遗漏的细节。该可靠性价值与热缓存提前压缩的费用收益分别评价；不能因原生摘要已有任务／决策字段便判定索引重复。费用比较的基准仍应包含“同样时机的提前 compact，无 Notebook”；质量比较则需要同时具备原文检索能力的基准，观察索引对历史事项发现、原文定位与细节恢复的实际增益。设计目的已同步 02 §1.7；维护频率、联合触发与强制查阅规则未据此变更。

### 记录模板

```text
### YYYY-MM-DD <改动标识>
改动内容：…
测量对象与口径：…
改动前 / 改动后（token 与占基线 %）：…
结论与取舍：…
```
