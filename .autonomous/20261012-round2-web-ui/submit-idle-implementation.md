# T3c Idle-only Submit 实施报告

R2-F08 的原子 idle-only 方法及显式图片归属仍是 Main 已登记于根 CLAUDE 的 **Agent 自主收敛／待用户追认**。Main 已 review 批准本阶段最小设计、DTO、R2-C10 单一判断点及图片薄传方案；此为 Development 完整交回，**不代表独立 Verification、Validation 或第二轮交付完成**。

## 1. 任务对应条款与授权

冻结文档 `37ad76f5dfac02d4774d5e0faea55911b5fb8de9`，产品基线 `edd031f5518955a10a2c68210e1c65477d6f0991`；当前 HEAD `8e7ba807f8f4f827f947e5e4184f46173d80cfd2`。已重读 executing-plans、根 AGENTS/CLAUDE、索引/基线、plan R2-F08/T3c、native-compatibility 末尾 Main 反例。

本阶段落实 06 §0.4–0.5（L85–105）事实归属/兼容、§1.8（L206–223）Idle Send 禁止隐式 busy fallback、§1.10（L233–241）Rewind、§2.9 新方法契约、§4.5–4.7（L585–618）准入/关闭/验收；继承 02 §1（L14–257）、§6.1–6.3（L2221–2261）、§6.6（L2287–2301）、§6.11–6.16（L2364–2451）、Final（L2514–2553）的真实 Message UID、owning profile、原生接线、未启用不变、Rewind/branch、不可变前缀。条款名与现行行数已核对。一级规格未修改；共享注册/生成由 Main 完成。

## 2. 实际变更与白名单

| 文件 | 实际职责 |
|---|---|
| `tui_gateway/methods_prompt.py` | 原生 `_lock_in_submit_turn` 临界区判断接缝；提取短 busy/claim 段；同锁统一写 running/inflight/source；导出实际 handler alias；请求线程捕获显式图片，薄传原 worker/compute-host |
| `tui_gateway/methods_submit_idle.py` | 新方法、finally-reset ContextVar 请求模式、单一 admission 决策/legacy 重查分派、图片输入验证；没有新 queue、gate、lease、账本或线程调度器 |
| `tui_gateway/contracts/submit_idle.py` | 独立 additive Params/Result；旧 PromptSubmit DTO 不变 |
| `tests/tui_gateway/test_submit_idle.py` | 真实生产 RPC/SessionDB/AIAgent Loop，受控外部 provider/构造/pipe 返回及时间屏障；当前 31 个参数化用例 |

其余产品文件没有由本阶段修改。特别未动已移交 Usage 的 `turn_context.py`、`turn_finalizer.py`、`prompt_turn.py`，也未动 session_lifecycle、compute-host、pending、正式 registry 或生成物。methods_prompt 相对产品基线净减 27 行（19 增/46 删）；新 sibling 144 行，测试 526 行。

## 3. 正式路径与结构性不变量

`server.handle_request` → 现有契约/retirement/RPC transport → 新 handler → bound `_native_prompt_submit_handler` → 原 sanitization/authorization/lease/preflight → 原 resume/reattach → `_lock_in_submit_turn` → 原 `_session_turn_admission` → 原 persist/build/worker/retirement/terminal。alias 经 methods_prompt.bind_module 绑定至 server globals 后读取；没有直接调用未绑定 module 函数。Main 已在 methods_prompt 后正式注册 methods_submit_idle，并导入 contracts；测试没有临时注册。

**唯一准入权威**仍是 `session_lifecycle._session_turn_admission`（L16），原 retirement.work + session.history_lock。新请求跳过外层 busy 观察，直接在原锁内通过 `_idle_submit_claim_error` 决定明确 busy 或继续原 truncation/claim；`_submit_commit_running_claim` 在同临界区同步写 running/inflight/source。ContextVar 仅表示请求模式并 finally reset；线程只接收已捕获的图片列表。没有外层持 history_lock 调整个 handler，resume/reattach 仍先完成，等待 provider/interrupt 仍在锁外。

source 布尔只是原 running claim 的来源注记：running=false 时它不阻止任何请求；下一次真正 legacy claim 同锁清除。未使用新入口时不存在该注记，原两 legacy 的 busy 观察/handle 和返回完全保留。legacy 已越过 idle 观察、却在原 claim 点碰到新 running claim时，由原锁返回私有 retry sentinel，回其原 queue/steer/interrupt政策；它不丢请求、不覆盖新 inflight。新请求永不进入 `_handle_busy_submit`。Web surface 元数据仅成功 claim 后写，legacy 保原 preflight 时点。旧 typed voice Stop 保原行为，新方法仅提交 Prompt。

**图片归属**：新方法省略列表即明确 `[]`；不把图片放进 shared staging。所有项先于 alias/preflight/claim/truncate，用原 CLI resolver（引号、file://、~、环境变量、原 relative cwd）、原扩展名集合及实际文件读取验证，保留顺序/重复；不新增路径权限或推断。原 contracts.validate_params 只拒绝未知字段、把类型交给 handler，因此 list[str]/null 类型由同一图片验证点明确4000，未改全局validator。普通文件继续 file.attach 的 ref_text/@file。

已有 `prompt_turn._admit_prompt_turn` L144–148 对非 None 参数只读显式图片且不清 staging；已有 compute_host frame L51–57、成功派发 L302–304 同样支持。因此仅传参数，原 compute-host send_failed inline fallback 也收到同一列表。旧 submit 始终 None，继续原共享图片行为。原 `_write_submit_user_row` 不读 staging；图片 parts 构建后 `_adopt_submit_user_row` 使用既有 row ID/message_uid 更新同一 durable user row，未写另一套图片记录。

## 4. 有效证据、命令与适用版本

全部 pytest 经 canonical runner，工作区 `.venv`、isolated home/SQLite 在 ignored 证据目录；fixture 禁止 socket.connect/connect_ex，真实 AIAgent 和 Loop，外部 provider 返回受控。不调用真实模型、不启动 UI/后端、不重启53445。

| 日志 | 有效结果与版本 |
|---|---|
| `third.log` | 原设计（显式图片增量前）15 PASS /9.3s：new/new、new→legacy、legacy 已过 idle→new先claim，legacy queue/steer/redirect三模式，busy拒绝无mutations、锁序、finally reset、profile、lost ACK、Rewind双确认、真实SQLite、native失败与延迟build |
| `regression.log` | 图片增量前66旧native PASS：busy政策32、CompositeCarrier/Rewind17、failed build2、submit row target9、submit-time rows6；另生成一致性1PASS/catalog1FAIL，故整命令不是PASS |
| `images-first.log` | 11PASS/2FAIL保留：实际null在全局validator后进入handler、测试错用message_id键；产品补同点list[str]检查，测试改查真实message_uid后定向修复 |
| `images-final.log` | 最终图片产品代码17PASS /15.0s：上传、顺序重复、真实parts/唯一row、null/标量/非string/空path/不存在/扩展名/read失败、Rewind双确认、image-only、compute-host frame与send_failed真实inline fallback、旧submit None负对照；含既有storage失败1项 |
| `images-build.log` | 最终产品2PASS /2.5s：延迟build前非空文本真实accept row/UID，file://列表捕获后线程图片更新仍同UID；busy拒绝图片/draft文件/staging/当前row/inflight保留 |
| `images-ws.log` | 最终源码与测试2PASS /2.6s：两真实 WSTransport绑定，旧attach resolver屏障→旧transport.close→新detach false→旧append→新Send（省略或显式[]）均不夹图；新transport真正进入原native viewers/rebind。受控socket未联网，不冒称浏览器实际WS验收 |
| `voice-negative.log` | 最终产品旧typed Stop两个用例2PASS /1.3s，voice on仍原voice_stopped/结束event，voice off仍原Prompt路径；未跑645用例整文件 |
| `generated-final.log` | Main最新共享生成物（含image_paths）一致性1PASS /0.8s；不复跑已知catalog orphan来重复制造相同失败 |
| `owned-health-final.log` / `owned-health.json` | 原官方Measurer/compare/allows/阈值对任务4文件按产品基线ratchet，0blocking/0advisory；范围脚本在ignored目录，不改规则 |
| `ruff-final.log` | 官方 `scripts/check --only ruff` 1check PASS；`git diff --check -- methods_prompt.py` PASS |

当前31用例的覆盖证据是 **原设计中13个未变用例 + 最终图片19个不同用例，扣除重复storage1 = 31**；不是宣称执行过单条最终31PASS命令。原 staged-image 和 deferred-build 两测试已按新图片语义替换并取得最终证据；原 busy/claim/ContextVar/profile锁机制未因图片增量改变，复用15/66的适用部分，遵照Main不机械重跑。T3a109项未重跑。原设计 `first.log`/`second.log` 的测试预期/fixture失败也完整保留，见日志；没有抹掉首轮失败。

命令形态：`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh -j 1 <目标> --basetemp="$PWD/.hermes-dev/round2-evidence/submit-idle/<隔离目录>"`；原设计 test_submit_idle 全文件，regression为日志首段六个原生文件；图片分别 `-k image`、`-k 'images_deferred or images_busy'`、`-k late_legacy_attach`；生成一致性 `-k generated_files_are_current`；旧typed Stop只 `-k prompt_submit_typed_stop`。检查：`.venv/bin/python scripts/check --only ruff` 与 `.venv/bin/python .hermes-dev/round2-evidence/submit-idle/check_owned_health.py`。

## 5. 限制与保留失败

没有真实视觉模型/API理解验收、真实浏览器WS/REST旅程、host child执行或跨平台验收；compute-host证据只覆盖真正frame/dispatch接缝及inline fallback，不捏造child DB/Loop结果。scope目标是原生in-process；不替parent宣称child事实。

旧原生 `image.attach/detach` 的迟到append仍保持兼容行为，新Web显式列表使该shared staging不参与新请求。文件校验之后到worker读取之间仍是原文件生命周期/IO机制，之后失败按原terminal错误处理；没有新增持久attachment ownership或复制图片系统。

ACK streaming是真正native准入而不是Turn完成。没有新增op_id/持久去重：断线、超时、5xx/未知ACK不能当明确拒绝、安全重发或猜成功。需按既有activate/resume/history及真实user_row_id恢复事实。原生退休、build、存储、watch-child、Rewind错误保留；有些原native4009不携新busy data，不改写成新语义。catalog当时仍有Main已知 `review.summary` orphan；不把regression整体写成成功。当前服务仍旧进程，正式联调由Main集成快照/restart后进行。

## 6. 实际DTO与客户端影响

```ts
// 新方法 prompt.submit_idle；旧 prompt.submit 输入输出原样。
type SubmitIdleParams = {
  session_id: string; profile?: string | null; text?: string;
  image_paths?: string[]; // 省略 []，null/非list[str] 4000；顺序与重复保留
  title_preview?: string | null;
  truncate_before_user_ordinal?: number | null;
  truncate_before_row_id?: number | null;
  truncate_before_message_id?: string | null;
  confirm_truncate?: boolean | null; confirm_empty_truncate?: boolean | null;
  rebind_survivor_row_ids?: number[] | null;
};
type SubmitIdleResult = {
  status: 'streaming'; user_row_id?: number | null;
  survivor_user_row_ids?: (number | null)[] | null;
  survivor_row_id_map?: Record<string, number | null> | null;
  turn_isolation?: boolean | null;
};
// 真正原native running claim竞争的明确拒绝：
// {code:4009, message:'session busy', data:{accepted:false, reason:'session_busy'}}
```

实际入口 `methods_submit_idle.py:124`，同一个已绑定native handler；schema非法额外字段4000、runtime不存在4001、显式profile mismatch4003；图片空4015/notfound或extension4016/read5027；原其它错误透传。text默认空用于image-only；原native acceptance/terminal events、UID、history、provider/model/usage/profile ownership不重定义。没有新events/tables/缓存或客户端持久Turn账本。

前端普通Send与Rewind均用本方法；图片仅file.attach取得server path，显式发送本次图片列表，不调用image.attach/detach。成功沿真实streaming/user_row_id协调；明确busy保draft/图片；未知ACK恢复原生事实，禁止blind resend。旧客户端继续原prompt.submit/voice/typedStop/queue/steer/redirect/Image staging，不需变更。Web新请求不传queued、voice、internal hosted、browser conversation_ref为权限等字段。

## 7. 源码封存与完整交接

当前任务4文件SHA256如下；完整本地快照/符号hash/日志hash及report hash在 `source-manifest.json`，所有正式注册/生成物只是read-only记录Main拥有的集成版本。

- `tui_gateway/methods_prompt.py`：`77f9e6052fcd7776ceed76ed2b8f3e2bddbe240d7a532b110d89ce5c44d82772`
- `tui_gateway/methods_submit_idle.py`：`a811402327e201da86033c4ca496d3ffd22d67dc8f030e9173efbbcdd9653a50`
- `tui_gateway/contracts/submit_idle.py`：`df82bb57140c3a28c5cc0b7014c3707ae05f47e3775008d763d9e9b9b2ac2292`
- `tests/tui_gateway/test_submit_idle.py`：`804ce789b8a8096b44b3eff5e1e0a01d46893c3a5220aed97e4ea1e668191025`

Main集中review后，将4文件与正式server module order、contracts import、生成物纳入同一个集成快照，随后前端按上述真实DTO接线，并统一restart后做实际REST/WS/图片/模型验收及本轮两门禁。**本阶段全部白名单文件现已停止施工，可交给Main；Usage三个生命周期文件从T3a后始终未再占用或修改。** 后续review修复须另协调，不让历史证据覆盖新差异。不stage/commit，不操作用户真实profile或现有运行进程。
