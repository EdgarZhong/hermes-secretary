// @vitest-environment jsdom
import { beforeAll, expect, it, vi } from "vitest";
import { conversationExcerpt } from "./conversation-title";
let Controller: typeof import("./controller").Controller;
beforeAll(async () => {
  vi.stubGlobal("location", {href:"http://127.0.0.1:5173/new",origin:"http://127.0.0.1:5173",pathname:"/new",protocol:"http:"});
  vi.stubGlobal("localStorage", {getItem:()=>null,setItem:vi.fn(),removeItem:vi.fn()});
  vi.stubGlobal("history", {pushState:vi.fn(),replaceState:vi.fn()});
  vi.stubGlobal("window", {addEventListener:vi.fn()});
  Controller = (await import("./controller")).Controller;
});
it("ordinary reasoning notices obey the documented ten-second lifetime", () => {
  vi.useFakeTimers();
  try {
    const c = new Controller();
    c.notifyInfo("Thinking effort changed to", "High");
    vi.advanceTimersByTime(5000);
    expect(c.state.notifications).toHaveLength(1);
  } finally {vi.useRealTimers();}
});
it("a closed task without Snapshot evidence does not publish successful completion", () => {
  const c = new Controller();
  c.state = {...c.state,profile:"",route:{screen:"conversation",id:"A"},secretary:{profile_home:"/profile",conversation_ref:"conv-A"} as any};
  vi.spyOn(c,"readSecretary").mockResolvedValue({} as any);
  vi.spyOn(c,"readSchedules").mockResolvedValue({} as any);
  (c as any).event({type:"secretary.changed",payload:{profile_home:"/profile",conversation_ref:"conv-A",reason:"task_finished"}});
  expect(c.state.secretaryCompletion).toBeUndefined();
});
it("AI title input does not include hidden machinery as the users conversation", () => {
  const input = conversationExcerpt([{role:"user",content:"Plan a holiday"}, {role:"user",display_kind:"hidden",content:"Internal tool whitelist and maintenance routing"}] as any);
  expect(input).not.toContain("Internal tool whitelist");
});
