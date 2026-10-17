// @vitest-environment jsdom
import { beforeAll, expect, it, vi } from "vitest";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { SchedulePanel } from "/Users/edgar/code/hermes-secretary-web/src/design/indicators";
import { sessionGroups } from "/Users/edgar/code/hermes-secretary-web/src/core/session-groups";
import { conversationExcerpt } from "/Users/edgar/code/hermes-secretary-web/src/core/conversation-title";
import { RpcError } from "/Users/edgar/code/hermes-secretary-web/src/api/client";
let Controller: typeof import("/Users/edgar/code/hermes-secretary-web/src/core/controller").Controller;
beforeAll(async () => {
  vi.stubGlobal("location", {href:"http://127.0.0.1:5173/new", origin:"http://127.0.0.1:5173", pathname:"/new", protocol:"http:"});
  vi.stubGlobal("localStorage", {getItem:()=>null, setItem:vi.fn(), removeItem:vi.fn()});
  vi.stubGlobal("history", {pushState:vi.fn(), replaceState:vi.fn()});
  vi.stubGlobal("window", {addEventListener:vi.fn()});
  Controller = (await import("/Users/edgar/code/hermes-secretary-web/src/core/controller")).Controller;
});

it("schedule wall clock uses the named owning zone", () => {
  expect(Intl.DateTimeFormat().resolvedOptions().timeZone).toBe("UTC");
  const html = renderToStaticMarkup(<SchedulePanel status="Idle" state="idle" onCollapse={()=>{}} schedules={[{
    schedule_id:"s", content:"check", expression:"daily", canonical_schedule:{kind:"cron",expr:"0 10 * * *"},
    timezone:"Asia/Shanghai", delivery_mode:"instant", state:"active", next_due_at:"2026-10-18T10:00:00+08:00", pending_count:0, last_delivery:null
  }]} />);
  expect(html).toContain("10:00");
});

it("backend pinned rows precede newer unpinned rows", () => {
  const now = new Date("2026-10-17T12:00:00Z");
  const groups = sessionGroups([{id:"new",last_active:now.getTime()/1000,pinned:false}, {id:"pinned",last_active:1,pinned:true}], now);
  expect(groups.flatMap(group=>group.sessions)[0].id).toBe("pinned");
});

it("a stale config action on A never retries its write into B after navigation", async () => {
  const c = new Controller();
  c.state = {...c.state, route:{screen:"conversation",id:"A"}, profile:"", binding:{session_id:"runtime-A",stored_session_id:"A"}};
  let reject!: (error:unknown)=>void;
  const first = new Promise((_resolve, fail)=>{reject=fail});
  const writes:any[]=[];
  c.gateway.request = vi.fn(async (_method, params) => {writes.push(params); if(writes.length===1)return first; return {};}) as any;
  vi.spyOn(c,"ensureBinding").mockResolvedValue({session_id:"runtime-B",stored_session_id:"B"} as any);
  const pending = c.setSessionConfig("reasoning","high");
  c.state = {...c.state, route:{screen:"conversation",id:"B"}, binding:{session_id:"runtime-B",stored_session_id:"B"}};
  reject(new RpcError("Unknown session",4001));
  await pending.catch(()=>{});
  expect(writes.filter(item=>item.session_id==="runtime-B")).toEqual([]);
});

it("on-demand title excerpt includes the latest live conversation text", () => {
  const input = conversationExcerpt([{role:"user",content:"opening topic"}] as any,[{role:"user",text:"new task that dominates this conversation"}]);
  expect(input).toContain("new task that dominates this conversation");
});
