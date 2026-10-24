# 后端 v1 恢复接口契约

当前已接正式 REST 和 `session.activate`，真实SQLite／正式handler输出固定于 `tests/tui_gateway/fixtures/recovery-view-v1.json`。文件包含 `rest`、`activate_request`、`activate_matched`、`activate_replaced`、`activate_unavailable`。生成脚本及原始库在 ignored `.hermes-dev/web-recovery-20261024/backend/`，无模型或外网。此为约定整包契约里程碑，后端仍继续补验证与收敛。

## REST

`GET /api/sessions/{stored_id}/messages?recovery_view=1` 默认最新200，`limit` 上限500。锚点请求使用恰好一个 `anchor_uid` 或 `anchor_row_id`，`before` 默认100、`after` 默认99，含anchor总数≤500；锚点请求不传limit。`before/after` 是行数，不是逻辑坐标。不能与旧 `offset/order/detail_row_ids` 混用；`view=cards`可选（本接口始终cards）。未知版本／冲突400，owner／locator／anchor找不到404。

响应保留 `session_id/profile/messages/projection/pagination`，新增 `selector` 和 `coverage`。selector精确为 `{kind:'latest',limit}` 或 `{kind:'anchor',anchor_uid?,anchor_row_id?,before,after}`。

`coverage={version:1,profile,requested_id,tip_id,lineage:string[],window,digest}`。

`window={first,last,predecessor,successor,is_start,is_end,start,end,returned,total}`。前四项是逻辑identity或null；identity=`{row_id,message_uid:string|null,logical_order:number,position:number}`。position为本事务逻辑代表集合的零基序号；logical_order为稳定首次顺序坐标。start/end为返回范围零基序号（空范围end=-1）。`is_start/is_end`证明真实首尾；predecessor/successor可核邻接。digest为完整cards的规范SHA256，不含折叠正文；每轮仍返回完整正文。

## activate

普通resume/activate响应宣告 `recovery_view_version:1`；收到能力后，activate新增可选参数：

```text
recovery_view={version:1,stored_id,profile,
 windows:[{selector,receipt:完整REST coverage}],
 details:[{row_id:正整数}]}
```

windows限1–2且至少一个latest（暖恢复再加anchor）；details限12行（兼容直接数字，但前端请传identity对象）。原有session_id仍是runtime binding ID。receipt owner/version必须相符，且必须由前端本轮真实REST取得。

成功 `result.recovery_view`：

```text
{version:1,complete:true,
 owner:{profile,stored_id,tip_id,runtime_id},epoch,
 windows:[{selector,coverage,matched,messages?:完整替换cards}],
 details:完整所需详情行[],detail_digest,
 state_snapshot:{events,seq,epoch,complete:true},
 stream_cut:{snapshot_seq,latest_seq,events,truncated:false},
 running,status,turn_started_at,inflight?,queued?}
```

matched仅在后端本次完整重读coverage与receipt完全一致时true，此时省略messages；false返回整个所选窗口。详情可能合法空，表示请求的physical row已不可展示；不能借旧详情补回。state_snapshot.seq是S，stream_cut.latest_seq是有限B，events为 `(S,B]` 同锁复制的连续后缀。B后已收到帧接正常处理，不能凭B跳未收到序号。epoch/runtime必须与本轮binding相同。外层state_snapshot同封套；外层messages为[]且messages_omitted=true。

可重试失败仍是RPC正常result，但 `recovery_view={version:1,complete:false,reason,owner:{profile,stored_id,runtime_id},epoch}`。原因包括 `history_busy`、`view_changed`、`coverage_gap`、`replay_gap`、`runtime_unavailable`、`read_failed`、`not_found`、`anchor_not_found`、`owner_mismatch`。仅complete=true可满足一致恢复。`not_found`应重新确认REST owner/locator并走失效路由；不能把失败的外层running/status作为ready。非法结构RPC -32602；不伪装成成功空窗口。

封套内部最多重做一次；前端按冻结要求最多两次立即重试，再普通退避。history_busy单次250ms。所有破坏变化校验依真实DB与完整snapshot证据，不依赖通知文件或缓存版本。

`session.events.since` 字段及语义不变；现在events/latest_seq/truncated/epoch由同一次原子cut取得，open_requests仍独立原生request snapshot。

## 已取得证据与剩余

最终新REST测试8项通过，封套测试24项通过：正式handler、旧activate、真实独立进程replace/rewind/compression/delete、外部append、当前Turn完整快照与有限suffix、ring缺口重试、外部lease／缺snapshot拒绝、250ms锁失败。原子cut并发、历史改写通知、UID退役／idle旧snapshot、详情边界及相关回归均已补齐；整包结论与既有catalog缺口见backend.md。
