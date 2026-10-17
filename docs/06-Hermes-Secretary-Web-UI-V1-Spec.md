# Hermes Secretary Web UI V1 — Product, Native Interface & Implementation Specification

> **改版阅读边界（2026-10-16）：** 本文保留现有Web UI与原生客户端架构基线。用户已确认第三轮自主实现聚焦Secretary改版与个人NM接入，界面修改整体后置；Memo控件、Orb／Idle倒计时、Notebook人类卡片、Settings及UI读取DTO的调整不作为本轮实施／验收条件。下方局部标识仅说明旧语义已被白板＋07替换或继续继承，不构成第三轮UI施工清单；后续界面改版另行安排。

> **历史冻结范围：** 下行“this round”“remain frozen”等只指第二轮，不约束第三轮已授权的改版。局部过时标识优先于对应旧正文；不修改第二轮验收历史。

> **Status:** Frozen normative specification for Round 2 (2026-10-12). This round MUST NOT revise its authoritative specifications; implementation and acceptance status belong to the root CLAUDE.md and round reports. **Authorized exceptions (2026-10-13):** §1.6 Composer keyboard binding (Enter submits content only; Escape carries the cancel-type primary actions), with §1.10 aligned; and §1.7 attachment budget (all attachments in the current draft together MUST NOT exceed 500 MB), explicitly confirmed by the user. Subsequent explicit user-confirmed amendments, including the 2026-10-14 corrections, are recorded in the Round 2 Snapshot Index. Unrelated clauses remain frozen.
> **Date:** 2026-10-12
> **Target:** `EdgarZhong/hermes-secretary` native Hermes/Secretary backend plus a separate browser-native Secretary UI repository.
> **Authority:** The user's final decisions in the two 2026-10-12 UI discussions and subsequent clarification take precedence over superseded UI proposals. For inherited Secretary Core semantics, effective `docs/02-noting-system-specification.md`, including its confirmed V1.6 revisions, takes precedence over corresponding older clauses in `docs/04-hermes-secretary-v1.5-implementation-spec.md`; retain 04's increments not superseded by current 02, then inherit applicable 01 requirements not covered by those increments. This specification is authoritative for its **expressly identified, user-approved Web UI increments**, which require compatible additive changes. Actual deployed behavior is established by source and tests, not by any historical design discussion.
> **Document organization:** Exactly six top-level numbered divisions at the `##` level, numbered **0–5**. Division 0 is the mandatory terminology/architecture preamble; divisions 1–5 are the five delivery sections. All subsidiary headings are `###` or `####`, with at most 20 sibling headings per parent.

**Normative vocabulary.** **MUST / MUST NOT** state non-negotiable V1 requirements; **SHOULD** is a strong implementation preference that may be varied only if the stronger architectural or functional invariant is still satisfied. **Existing** means grounded in the inspected fork; **Proposed additive** means a required outcome for which a new native interface may be necessary; **Verify** means the current implementation/DTO/transport or end-to-end guarantee is not yet established. A proposed name never silently becomes an existing API.

---

## 0. Terminology, Specification Authority & Architecture Invariants

### 0.1. Canonical terminology

> **第三轮适用性：** 表中Memo及Notebook-owned Schedule的术语已过时；Conversation／Session／Message Identity、原生客户端与真实消息载体继续继承。第三轮Scheduler与Notebook的定义以07术语表为准。

Use Hermes/Secretary's actual names first. UI-only terms are allowed only when they denote actual presentation behavior that has no corresponding native primitive.

| Term | Precise meaning | V1 implementation rule |
|---|---|---|
| **Hermes Desktop** | The existing Electron application, renderer, shared client code, and native API integration | Primary reference for feature coverage, session recovery, message projection, transport wiring, and API use; **not** an implementation to wholesale port. |
| **Dashboard REST** | Existing FastAPI HTTP routes, including `/api/sessions/*`, `/api/fs/*`, and `/api/files/*` | Frontend calls the relevant existing endpoints directly; no newly invented server-side UI adapter. |
| **TUI Gateway** | `tui_gateway/*`, with WebSocket JSON-RPC exposed at `/api/ws` | Hosts session-scoped runtime control, prompt submission, stream/event fanout and native attach methods. |
| **Messaging `gateway/`** | Hermes's messaging-channel integration layer | **Not** a synonym for TUI Gateway or Dashboard REST; no dependency on a messaging chat transport for primary browser chat. |
| **Agent Core** | Python Agent execution, tool calls, context/compaction, and runtime-owned state | Backend-owned; UI never instantiates, serializes, or owns Agent instances. |
| **Conversation** | One logically continuous user-facing path, including valid compression continuations; branches/new/reset are distinct | The view must preserve user continuity while correctly respecting native boundaries. |
| **`conversation_ref`** | Secretary's durable logical Conversation identity defined in 02 | Authoritative for Secretary Notebook/Noting/Memo ownership; the browser does not mint or duplicate the registry. |
| **Stored Session ID / `session_key`** | Durable Hermes Session locator (and its compression lineage) used for list, REST history, and resume | Used as the stable UI route/lookup address where supported; must not be confused with `conversation_ref`. |
| **Runtime Session ID / `session_id`** | Ephemeral TUI Gateway `_sessions` key used by session-scoped RPCs | Client keeps only a transient mapping from stored locator to this ID; invalidates/rebuilds after transport/backend changes. |
| **Message Identity** | `(conversation_ref, message_uid)` as specified in 02 | Must be respected whenever native UIDs exist; never substitute a physical DB row ID as a universally stable semantic identity. |
| **Timeline** | The chronological UI containing real stored messages, live projections, and visibly pending-but-not-yet-stored steer bubbles | Presentational surface, **not** a new authoritative transcript store. |
| **Turn** | One Hermes `run_conversation()` driving execution, possibly with multiple model/tool calls | Usage and controls must not equate one assistant bubble, model call, or tool call with one Turn. |
| **Steer / `session.steer`** | Native correction injection into a running Turn, not a new persisted user Turn at acceptance time | Browser text-only active-turn submission uses this existing mechanism. |
| **Pending Steer** | A server-accepted Steer not yet consumed at its legitimate native insertion point | May have separate temporary UI bubbles; exact withdraw/consume truth must come from backend. |
| **Withdraw** | Remove exactly one still-unconsumed pending Steer and recover its text | Not deletion of an already-persisted message; cannot succeed once consumed. |
| **Interrupt** | Stop the current Turn **and** atomically promote its remaining pending Steers into one follow-up Prompt | Different from plain Stop; never submits unsubmitted Composer content. |
| **Cancel Send** | Cancel one in-progress pre-acceptance send/upload transaction, restoring its captured local draft | Different from stopping an Agent Turn or canceling a Compaction. |
| **Rewind + Edit** | Frontend Reply action followed by confirmed native history truncation and resubmission | Not a threaded reply, filesystem rollback, or separate message-edit database. |
| **Compaction** | Hermes's actual context compression and possible physical Session rotation | Display true history content and true status; never insert a fabricated compression notice. |
| **Framework Message** | Secretary runtime-produced durable user-role message, typically `<framework-message>` | A real message in the Timeline with its own visual treatment. |
| **Instant Reminder** | Secretary active user-reminder delivery, typically `<instant-reminder>` | A real user-role message in the Timeline with a distinct reminder treatment. |
| **Deferred Reminder** | Secretary passive in-request reminder, typically `<deferred-reminder>` | Display where it is actually part of the durable/displayable native projection; never invent one merely from a pending schedule. |
| **Secretary Orb / Memo Stick** | Conversation-only, read-only UI projections of actual Noting state and current Memo | Not a secondary scheduler, task initiator, or Notebook editor. |
| **Full Foreground** | 02/04's logical audit view with Context Prelude, message nodes and Anchor/Snapshot annotations | **Deferred UI**; ordinary chat history is not to be mislabeled or implemented as Full Foreground. |

**Terminology retired from earlier discussions:** `Attach Notice` as a synthetic API object; `Photo Attach` as a universal backend operation; `PDF Attach` for ordinary file-PDF transfer; `Gateway` used ambiguously; `Reply` as a second thread; a separate `In-flight Queue` card/zone; speculative `/stash` name for the actual `/notebook` command; and a new “Conversation Web API” just to map stored IDs to runtime IDs. They MUST NOT appear as new domain types or backend requirements.

### 0.2. Relationship to 01/02/04 and historical 06

> **第三轮适用性：** 以下优先级描述的是第二轮。第三轮先白板＋07，再继承旧规格明确保留部分；旧规格中的Target不得反向覆盖新版。浏览器/notebook只读临时结果的差异仍保留。

| Source | Retained authority | Deliberate Web UI boundary/revision |
|---|---|---|
| `01-personal-hermes-v1-first-fork-iteration.md` | Hermes-first, additive-first, Conversation truth | The Web UI is a later, independently scoped delivery; it does not reopen the original first-fork implementation. |
| `02-noting-system-specification.md` | Current Core contract, including confirmed V1.6 revisions: `conversation_ref`, `message_uid`, Notebook, Noting, Reminder carriers, Compaction, Schedule | Current 02's confirmed revisions take precedence over corresponding older 04 clauses. UI displays these facts and uses existing backend owner resolution; it does not replicate Core rules. |
| `04-hermes-secretary-v1.5-implementation-spec.md` | V1.5 increments not superseded by current 02, including applicable Full Foreground and Core clauses | Inherit only still-effective increments, then applicable 01 requirements they do not cover. Full audit projection remains deferred as a UI feature. |
| Original `06-ui-read-api-discussion` | Early Web UI scope, read-only files, Orb/Memo, future audit requirements | A superseded discussion record, **not** an API schema, a current integration map, or authorization to implement. |
| `UI选型评估` and `恢复UI讨论` conversations | The user's later confirmed product interactions | Adopt the **latest user decision** when a conversation contradicts an earlier proposal, especially for Steer, Attach, Timeline, Slash, Compaction and Orb. |
| Subsequent architecture/UX decisions | Direct REST+WS, Desktop-first wiring, thin client, scoped engineering/design roles, Timeline timestamps, Files navigation | These are the final V1 decisions and override earlier assistant-imposed architectural constraints. |

For any inherited 02/04 reference below, apply the same precedence: current 02, including confirmed V1.6 revisions, then still-effective 04 increments, then inherited 01. This 06 supersedes the historical UI discussion for Web V1; its explicit Web increments remain authoritative.

**Explicit Core/UI conflict:** the inherited 02 text permits bare `/notebook` render output to participate in ordinary persisted transcript/context semantics. V1 now requires **human-only transient rendering without a durable message or model-context insertion**. This is a deliberate, limited new behavioral requirement; the implementing lead MUST locate the current command dispatch/persistence seam and provide a compatible, minimally invasive browser-facing path. It MUST NOT claim this behavior already exists or silently rewrite other CLI/TUI semantics.

### 0.3. Authoritative C/S architecture

```text
Browser-native Hermes Secretary UI
  React + assistant-ui + shadcn/ui + Tailwind
  UI rendering, bounded ephemeral state, transient stored-ID/runtime-ID mapping
        |                           |
        | HTTPS (existing REST)     | WSS (existing /api/ws, JSON-RPC + events)
        v                           v
  Hermes Dashboard REST         Hermes TUI Gateway
  SessionDB history, files      session.create/resume/activate,
  media, metadata, config       prompt.submit, steer, interrupt, stream
        \                           /
         \--- native Hermes/Secretary backend ---/
                     Agent Core + state.db + filesystem
```

The diagram is a **logical ownership** diagram, not a deployment promise that all browser cross-origin/auth scenarios already work. Browser authentication, URL resolution, hosting, WSS and file access MUST be validated against real routes and policies. A hosting reverse proxy required by deployment is infrastructure, **not** an invented BFF, alternate transcript API or Agent lifecycle owner.

Round 2 uses a separate **local frontend repository beside this backend workspace**, `hermes-secretary-web`. Necessary backend increments stay in this `hermes-secretary` workspace; all process plans, coordination records and acceptance evidence stay here as well. Subsequent user authorization enables automatic push after commits in both repositories. This code synchronization does not authorize cloud deployment or Memory Provider work.

### 0.4. Thin client and local-persistence allowlist

> **第三轮适用性：** 薄客户端与持久化边界保留；表中Memo实体退出，Schedule从Notebook中独立，权威owner仍在Secretary服务端。

| State | Authoritative owner | Browser treatment |
|---|---|---|
| Session list, stored transcript, titles, pinned/archived metadata, Lineage | Hermes SessionDB | Fetch on demand; no durable browser mirror or second repository. |
| `conversation_ref`, Notebook, Memo, Noting task/schedules | Secretary Core `state.db`/runtime | Read via native or minimally additive read interfaces; never client-derive truth. |
| Agent Turn lifecycle, Pending Steers, execution progress, usage, Compaction | TUI Gateway / Agent Core | Live in-memory projection from actual RPC/event/REST facts; refresh/reconnect resynchronizes. |
| Stored Session ID → Runtime ID map, event high-water marks, inflight render state | Browser working memory | Minimal transient Map/state; not persisted; recreated with existing `session.resume`/`session.activate`. |
| Unsubmitted text, selected photos/files and their Blobs, New Chat draft | Browser local persistence | Allowed, scoped by draft/Conversation and recoverable across same-browser reloads (IndexedDB for binary where appropriate). |
| Last route, Files return target, scroll position, explicitly chosen presentation preferences | Browser local persistence / URL history | Allowed, sparse and device-local; validation against server on restore. |
| Existing config such as `terminal.cwd`, actual active model/effort | Hermes native config/session | Display source of truth from native API; a *not-yet-applied user selection* may be local draft only. |

The implementation MUST NOT introduce a persisted API-response cache, client SessionDB replica, client-held Notebook records, client-managed turn ledger, independent unread watermarks, or background synchronization to make those local copies agree with the server. Small **in-memory** render buffers and pending UI state are inevitable; use no more than required. Optimize pagination and render performance before inventing more state layers. Losing browser storage may lose **unsubmitted** data and local presentation preferences, but MUST NOT destroy already accepted server data.

### 0.5. Additive compatibility and data provenance

1. All existing native REST/RPC methods MUST keep their names, required/optional input shapes, response shapes, errors and semantics. The V1 UI adapts to them; it does not standardize them by rewriting backend contracts.
2. Backend changes are restricted to concrete missing V1 atomic operations, source-truth read projections, or necessary event visibility at existing native seams. New behavior MUST be scoped and tested without side effects on unrelated clients.
3. UI-specific projection fields MUST NOT replace or rewrite real messages, `message_uid`, timestamps, attachments, `conversation_ref`, persisted Session lineage or model context.
4. An API call's *acknowledgment* and a Turn's *completion* are distinct. A websocket disconnect does not prove that a submitted Prompt was rejected.
5. Read-only navigation, Files browsing, Noting/Memo/Notebook inspection and route restoration MUST NOT start a new Turn, mutate Notebook/Memo or consume a Reminder.
6. A missing/uncertain backend fact is represented as loading/unknown/error, **never as guessed success, false idle, an inferred consumption, or a fabricated historical row**.

### 0.6. Engineering and delegation authority

> **第三轮适用性：** 本节角色与编排属于第二轮历史安排，第三轮以新计划与AGENTS为准；不据此指定旧Agent或扩大文档冻结。

**Main/Integration is GPT-6 Astra high**, accountable for technical direction, complete requirement coverage, delegation, review and integration. **Development is GPT-6.1 Sol high**, responsible for concrete frontend/backend implementation and relevant tests within assigned boundaries. Independent **Verification is Astra high**, independent **Validation is Astra medium**, and the independent **visual designer is Astra medium**. Technical accountability does not make the Main agent the sole code implementer. The visual designer is scoped to a cohesive design system, responsive visuals, tokens and styling, with **no authority to design new product interactions** or change button conditions, navigation, data semantics or Agent controls. See division 4 for boundaries and acceptance.

### 0.7. Confirmed deployment topology and dual-SPA routing (2026-10-17)

> **User-confirmed deployment shape.** One private hostname, one Cloudflare Access gate, one backend process serving both the Secretary SPA and the native Hermes Dashboard. This is a deployment decision, not a new API or a second product surface.

The following constraints are normative for the private cloud deployment:

1. **Single public entry.** The only public address is one private hostname protected by Cloudflare Access with an email allowlist. Cloudflare Tunnel reaches the backend host; a loopback-only reverse proxy rewrites the request `Host` to `127.0.0.1` and removes `Origin` before forwarding to Hermes. The Hermes backend and the reverse proxy MUST bind `127.0.0.1` only. No browser cross-origin configuration, second API hostname, or CORS policy is part of this deployment.
2. **Two SPAs, one origin.** `/` serves the Secretary SPA from `HERMES_WEB_DIST`. `/dashboard` serves the native Hermes Dashboard SPA from `HERMES_DASHBOARD_WEB_DIST` (prefix `HERMES_DASHBOARD_PREFIX`, default `/dashboard`). Both are same-origin with the API and MUST acquire the injected `window.__HERMES_SESSION_TOKEN__` from their own served `index.html`.
3. **One shared API and one backend process.** `/api/*` and `/api/ws` are shared by both SPAs. Requests under `/dashboard/api/*` MUST be rewritten to `/api/*` before routing, for both HTTP and WebSocket upgrades, so the native SPA can use `__HERMES_BASE_PATH__ = /dashboard` without a second API surface. Both SPAs MUST be mounted in the same Hermes process. A second backend process, multiple workers, or replicas are forbidden for this deployment: `_sessions` is process memory, and Scheduler/Noting background owners would duplicate or diverge.
4. **Authentication boundary.** Cloudflare Access is the only user-visible authentication layer. The backend session token remains an automatically injected machine credential, not a second interactive login. `dashboard.public_url` MUST NOT be configured for this deployment because it engages the dashboard OAuth gate; `--insecure` does not bypass authentication and MUST NOT be relied upon.
5. **Docker is allowed only with host identity.** If the backend runs in a container, the reverse proxy and the backend MUST share the host network namespace (or an equivalent arrangement) so WebSocket upgrades still present a `127.0.0.1` peer; a separate bridge network would be rejected by the loopback peer check.
6. **Stale runtime sessions are a normal reconnect case.** A backend restart, idle TTL, or eviction invalidates the in-memory runtime session. Session-scoped `config.set` for `model` / `reasoning` answers `4001`; the Web UI MUST resume the stored session and retry that operation once. Recovery is silent on success and surfaces the real error on failure. The backend stale-session guard MUST NOT be removed or weakened.
7. **No default change when the second SPA is absent.** When `HERMES_DASHBOARD_WEB_DIST` is unset, the server MUST behave exactly as before: no `/dashboard` mount and no path-rewrite middleware.

The stable operator entry points are `HERMES_WEB_DIST`, `HERMES_DASHBOARD_WEB_DIST`, and `HERMES_DASHBOARD_PREFIX`; their operator-facing summary lives in the repository README.

### 0.8. Development opt-out for model code-skew guards (user-confirmed 2026-10-17)

The user approved a configuration switch for the native model-operation code-skew protection (including RPC error `5098`). This is an implementation requirement, not a claim that the switch already exists.

- **Default compatibility.** The protection remains enabled by default. Existing installations without the new setting retain the original behavior and error handling.
- **Scope.** An explicit development opt-out bypasses only the model-operation skew guards. Keep raw revision detection, its cron consumers and backend retirement/watchdog behavior intact. Do not make `detect_code_skew()` return a fabricated no-skew result to implement the switch.
- **Configuration ownership.** Use the existing configuration system, not a new environment variable or frontend setting. The policy belongs to the backend process; requests or Sessions from different Profiles in that process must not change it. The implementation must document the chosen key and activation/restart behavior.
- **Preserved boundaries.** No database/schema, frontend protocol or Session ownership changes. Preserve the independent stale-runtime `4001` guard, authentication, model/provider validation and existing quality checks.
- **Actual limitation.** Opting out permits model operations despite revision drift; it does not hot-reload Python modules or guarantee compatibility between loaded and on-disk code. Genuine import/runtime failures still surface and may require a restart.

Implementation and evidence status remain in root `CLAUDE.md`. Tests must cover the default/enabled path, the explicit opt-out through the actual model ingress points, consistent process policy across Profiles, and unchanged raw detection/other consumers.

---

## 1. Product Design, User Interactions & V1 Boundaries

### 1.1. Experience, scope and visual authority

V1 is an English-language, responsive, chat-first Secretary, accessible from desktop and mobile browsers at a private deployment. It provides conversations, native execution visibility, attachments, session/turn control, a read-only Files viewer and restrained Secretary/Noting visibility. It is **not** a general-purpose assistant platform, an IDE, an Electron port, or a replacement for the existing administrative Dashboard.

- Use `assistant-ui` as the interaction/component foundation and `shadcn/ui` + Tailwind for the application design system. Browser-native semantics and accessibility take priority over bespoke render tricks.
- No speaker portraits/avatars in user/assistant message bubbles; preserve visual differentiation through layout and reusable tokens/components.
- The visual AI owns colors, fonts, radii, spacing, elevations, motion quality and responsive finish within the fixed product semantics. Do not name other libraries as required style dependencies or prescribe ornamental treatments not approved by the user.
- App identity/favicon/New Chat brand asset slots MUST use supplied project assets when available; absent assets receive a tasteful design-system placeholder without inventing new product branding or a hard dependency on an asset not yet provided.

### 1.2. Pages, navigation and browser history

Exactly **three main screen states** exist: **New Chat**, **Conversation**, **Files** (file list and preview are Files substates). The mobile sidebar/drawer exposes New Chat, Conversation list and Files; the **sidebar control remains at the mobile top-left** on every main screen.

| Screen | Mobile top-left | Navigation bar top-right | Main behavior |
|---|---|---|---|
| New Chat | Sidebar button | **No** `Back to Chat` | Welcome/initial composer; no backend Session merely from navigation. |
| Conversation | Sidebar button | **No** `Back to Chat` | Existing conversation, timeline, composer, conditional Secretary Orb. |
| Files list | Sidebar button | **`Back to Chat`** | Browse the configured default directory read-only. |
| Files preview | Sidebar button | **`Back to Chat`** | Read-only preview; Files internal path/breadcrumb navigation. |

- Desktop Files also puts `Back to Chat` **at the right of the Files navigation bar**, not the left; New Chat and Conversation never display it. The visual AI determines styling, not the location or conditions.
- **`Back to Chat` is a deliberate exit action, not `history.back()`**: it always returns directly to the chat state closest before entry into Files (existing Conversation or unsent New Chat), regardless of folder depth or preview depth. It restores the chat draft and reading position. With no valid preceding chat target (e.g. direct deep link), it opens New Chat. It must not create/resume/interrupt a Turn solely to navigate.
- Browser Back/Forward controls and platform-provided swipe-back gestures **must work natively** through real browser history. Files subroutes (directory and preview) participate in history; no application-level swipe gesture simulator or history-hijacking interception may replace system behavior.
- From Files, internal breadcrumbs/back-to-folder navigate the file hierarchy; they are **not** a substitute for the Files-level `Back to Chat`. Preserve native keyboard focus and standard link behavior.
- Refresh/revisit restores the last shown route (New Chat, Conversation, Files list, or Files preview), selected conversation, relevant preview path and reading position, plus local drafts. Verify the target still exists and is authorized; if not, fall back safely without changing backend state.

### 1.3. Session list, New Chat and chat selection

| Operation | Required behavior | Forbidden shortcut |
|---|---|---|
| Enter New Chat | Show clean unsent route and scoped draft; no backend Session | Creating an empty `session.create` on page mount. |
| First Send | Create exactly one backend Session via native RPC; then stage attachments and submit as prescribed | Eager create / duplicate create on concurrent button/Enter. |
| Open stored Conversation | Fetch authoritative history by stored locator; bind runtime only when needed for live actions/state | Reuse an unrelated runtime ID or force a new Conversation. |
| Switch conversations | Change selected route, hydrate destination; keep other running Turns owned by Hermes | Cancel previous Turn just because view changes. |
| Lineage/Compaction | Present one continuous user-semantic Conversation across valid compression edges, respecting branch/new boundaries | Treat every compression child as a separate new chat; merge branches. |
| Session with different historical cwd | Keep discoverable in the list according to native filters and real accessibility | Silently hide historical sessions to make the default-cwd story appear uniform. |

Conversation list, title, ordering, archival/pin affordances (only if included by the approved design and native capability) use actual REST results. Do not add management controls just because Desktop has them. Empty/loading/error and a lost/deleted session are explicit, recoverable UI states.

**User-confirmed sidebar restoration (2026-10-13, R2-C80):** Retain the approved Mock's Sidebar separators, including between Files and the theme controls. Organize real Sessions by their actual update time into mutually exclusive Today, Yesterday, previous 7 days, previous 30 days, and older groups. Restore the real-page presentation; do not substitute a single generic Conversations section for the approved grouping. Missing native timestamps must not be invented. Turn activation or completion must not cause whole-list flashing. Keep the list scrollable while hiding the visible scrollbar, and preserve the approved Mock separators and compact theme-control layout.

### 1.4. Timeline, streaming, message kinds and timestamps

**2026-10-15 用户确认底部留白：** Conversation Timeline 底部 padding 与 scroll-padding-bottom 统一为用户最终指定的 **64px**，避开 Secretary 悬浮球并保留正文间隙；替代此前试调的 52px，不改既有滚动跟随规则。

A Conversation has **one** Timeline. It includes the original ordered persisted messages, the live assistant stream and temporary pending-steer *visual* bubbles as a distinct non-persisted tail projection. No extra composer-level Queue card, separate In-flight panel or second transcript is permitted.

| Rendered source | Timeline semantics | Default rendering |
|---|---|---|
| Real ordinary User Message | One actual persisted user message with original content/metadata | User bubble, no avatar; native timestamp marker stripped only from UI presentation. |
| Real Assistant Message | Native persistent message / streaming continuation | Assistant content without avatar; rich text, code, accessible links. |
| Thinking | Model thinking stream, subject to actual available event segments | **Expanded while actively streaming**; auto-collapsed on completion; user can toggle. |
| Tool Call | Native tool call/arguments, activity and result | **Collapsed by default**, including during execution; show a visible working status, expandable parameters/results. |
| Framework Message | Genuine durable `<framework-message>` carrier | **Distinct message visual form within the Timeline**, not a toast, sidebar status or generic Assistant claim. |
| Process completion notification | Native `display_kind=process_complete`, excluding Noting Framework carriers | Independent notification card using the Framework Message theme; exact title **process complete**; collapsed by default, expandable to show the complete report. |
| Async delegation completion notification | Native `display_kind=async_delegation_complete` | Independent notification card using the Framework Message theme; exact title **async delegation complete**; collapsed by default, expandable to show the complete report. |
| Instant Reminder | Genuine `<instant-reminder>` user-role carrier | Distinct Reminder treatment, collapsed by default; not misattributed to a typed user message. |
| Deferred Reminder | Real native `<deferred-reminder>` message when actually projected in visible history | Collapsed by default, distinct from instant reminders; never fabricate one for a merely scheduled/pending occurrence. |
| Compaction | Real native summary/handoff carrier as projected by backend | In correct historical position, **collapsed by default**, full original available on expansion. |
| Pending Steer | Server-accepted, still-unconsumed correction | Separate provisional User-shaped bubbles at visual tail; no timestamp implying persistence. |
| Human-only `/notebook` result | Slash result intended for human viewing only | Temporary **Assistant-styled** result in the Conversation Timeline, anchored at the sequence boundary when the command is invoked; later messages follow it. Keep this display only in browser working memory; reload clears it. Until that memory is reset, preserve its invocation-time Timeline position across later messages and history updates; do not relocate it to the tail merely because an anchor was reconciled. Render the public human output as readable sections, entry states, fields and schedules; do not show internal Anchor metadata. No durable message identity or next-model-history insertion. |

**2026-10-15 用户确认完成回报的前端身份：** 上述两类通知按后端 `display_kind` 分类，前端使用独立通知 kind 和 system 角色，不能仅换皮后仍识别为 User Message；不使用用户气泡、用户消息动作栏、Reply／编辑入口或用户附件解析。原生 source 的 `role=user`、正文、UID 及数据库记录保持原样用于历史定位，不改变模型输入。Framework／Reminder 的既有包装优先识别，`display_metadata.noting_run_output=true` 不转换为进程完成通知，Noting Framework Message 的标题、主题及折叠行为保持不变。不以英文正文或 `display_text` 猜通知类型，固定标题不以任务摘要替代。

**2026-10-15 用户确认 `/notebook` 时间标签：** 前端临时 Notebook 卡片的时间标签使用 `Updated at`。时间值继续来自当前有效 Snapshot 在原生人类输出中的 `Created at`，仅调整界面文案，不修改后端响应字段、存储或时间语义。

**2026-10-15 用户确认 Thinking 展示保持现状：** 继续流式展示后端实际提供的推理文本或推理摘要，不因 GPT 等模型原始思维链不透明而隐藏其可见摘要或替换为「该模型思维链不可见」等固定文案。此前固定文案要求（前端 ISSUE-009）已由用户取消，不为该需求新增加密识别或接口。保留流式时展开、完成后自动折叠及用户手动展开的既有交互；内容仅以实际可用事件为准，不保证上游持续提供摘要。该取消不影响打断状态、缺段、状态闪烁等既有缺陷修复。

**2026-10-15 用户确认 GPT Subscription 路径与摘要分段：** GPT Subscription 指 Hermes 的 `openai-codex` Provider，使用 ChatGPT／Codex OAuth 订阅认证，经 `codex_responses` 模式调用 Responses API。摘要请求、接收、流式传输与段落分隔直接复用 Hermes：推理开启时请求 `summary: "auto"`，上游摘要增量经既有回调和 `reasoning.delta` 进入前端 Thinking；Responses 摘要的 `summary_index` 变化时由 Hermes 插入 `\n\n`。前端按收到的文本顺序拼接并正常渲染 Markdown，保留已有空行，无需额外补换行，不按每次回调强行分段（回调可能只是一个摘要段的文本碎片）。此结论限定上述 Responses 路径，不泛化至所有第三方兼容接口；源码依据见 [Provider 路由](../hermes_cli/runtime_provider.py)、[摘要请求](../agent/transports/codex.py)、[摘要流与分段](../agent/codex_runtime.py)。本次核对未发起真实订阅请求，不作为运行验收通过证据。

**Timeline time presentation contract:** Human-friendly date/time labels appear **only as Timeline reading aids** and **outside every message bubble**. They need not precede each message. The visual AI chooses ergonomic grouping, density, reveal timing, relative-vs-absolute style and placement; no per-message prefix rule is imposed. `<timestamp>ISO...</timestamp>` in ordinary native user-message content MUST be hidden from rendered text without modifying source data; grouped/merged Steers do not cause artificial timestamp rows. **2026-10-14 user clarification:** Reminder carriers remain collapsed by default; their inner timestamp is preserved on expansion, with no additional wrapper or timestamp-stripping treatment.

Message ordering, Compaction lineage, framework carriers, UIDs and stream insertion are backend facts. Do not infer message kind from English content text; identify authoritative native wrappers/projection metadata. Use event/source timestamps accurately, format locally, and avoid manufacturing message creation times for temporary UI nodes. Long histories initially load 200 backend messages and load 200 more per Show More History action, counting native tool-call/result rows; they remain scroll-anchored; a reader examining older messages MUST NOT be forcibly jumped to the bottom by new live content. Streaming content expands **before** the Pending Steer tail. Streaming presentation must follow real native progress without an artificial playback speed cap or a growing backlog of already-completed output. Reuse the mature interaction/rendering foundation while preserving the user-approved custom visual layer. With a live WebSocket connection, a materialized Instant Reminder must become visible at its native position promptly, without waiting for the resulting Turn to finish or allowing later Thinking to appear while that triggering row is still withheld.

### 1.5. Tool rendering, Markdown and errors

**视口信息不持久化（2026-10-15 用户确认）：** 滚动位置、手动控制状态和恢复计时只存在页面内存；不读写 localStorage 等持久存储。每次刷新页面回到 Timeline 底部并恢复默认跟随。

**2026-10-15 滚动补充澄清（覆盖此前恢复跟随的含糊描述）：** Timeline 默认随内容高度向下增长而被动跟随底部，持续显示最新内容；用户 Send 被接受后回底并开始被动跟随。任何用户主动 Timeline 滚动（向上或向下）立即退出跟随，之后流式追加不得推动视口，按用户选定的高度位置阅读；停止手动滚动控制 20 秒后，若当时 Turn 仍在流式输出，则自动回底恢复被动跟随；期间再次手动滚动重新计时，触摸拖动与惯性滚动结束后计时。若到期时 Turn 已结束则保留位置。只有用户 Send 被后端接受会立即回底；不得监听所有 Turn 启动统一回底，Reminder 等自动触发的新 Turn 不改变阅读位置。首次只加载 200 条后台消息；更早历史仅通过上方按钮每次加载 200 条，不做自动分页。向前加载完成后，补偿顶部新增高度并锚定原可见内容在视口中的位置，不能跳顶、跳底、闪动或错位。

**2026-10-15 用户录屏确认补充：** 每次真实工具调用在动态 Timeline 中只有一张卡，构建、运行和完成在同一卡片原位更新。**并行 N 次调用必须展示 N 张独立卡片，不得将整组并行调用合并成一张卡。识别到完整工具调用段时，全部调用卡即按后端真实顺序出现在 Timeline；各卡身份和位置顺序始终稳定，即使 start/complete 到达顺序不同，也仅及时更新各自的真实状态，不重排、不追加替代卡。** 每段 Thinking 和每次调用独立收尾，不以整个 Turn 结束作为统一纠正点。动态内容转为静态历史时，条目数量、顺序与内容保持连续，不得靠结束后的历史重渲染消除重复或补出此前漏显的段。处于底部跟随状态时，内容增长、卡片折叠及历史对账不得自行中断跟随；用户主动上滚阅读时保持其阅读位置。用户新 Send 被原生接受后回到底部、恢复跟随；手动滚动暂停与 20 秒恢复条件遵循上述最终澄清。

**2026-10-15 结束瞬间连续性补充：** Turn 从 active 转为完成及随后的后台历史刷新期间，当前内容与视口必须连续，不得短暂跳回旧 Turn 再恢复。历史消息的操作栏在 active/idle 切换时保持占位高度稳定；已有被动跟随与分页锚定不能因后台历史请求而暂停。仍遵守用户手动滚动所有权，不把 Turn 完成新增为强制回底触发。

- Assistant text supports Markdown and code blocks with normal text selection/copy. Render links safely; regular `http(s)` links may open, but assistant local paths/`file://` URLs remain plain text in V1, not automatically resolved into Files.
- Tool cards retain activity/identity while token deltas arrive, including incremental tool-call argument construction when native events expose them; secure sensitive payloads using existing redaction/authorization rules, not invented client heuristics.
- Tool state distinguishes constructing, running, complete, failed, interrupted, unknown and an explicit user-required approval/clarify request where native APIs expose it. A spinner alone is not evidence of a healthy model loop.
- Completion of one tool or assistant block is not completion of the whole Turn; controls reconcile with backend status and actual terminal events.
- A disconnected or stale feed displays a recoverable status; on reconnect, native replay plus REST history is reconciled instead of appending duplicated fragments.

**2026-10-15 流式速度联调修订：** 纯正文／推理增量及其原生身份配对投影（`message.output_delta` 的对应 `native_type`）必须共享同一按帧渲染合并策略，不能由每条身份事件打穿合并并造成已完成内容持续积压。仅合并中间画面，原生事件、文本、顺序、身份及控制状态仍逐条同步处理；interim 边界、控制与终态立即发布最新完整投影并取消过期待绘制帧。真实终态竞争仍由后端拒绝，前端明确说明本轮已结束、Steer 未被接受、草稿已保留，不自动转成普通 Prompt。

### 1.6. Composer contents, layout and keyboard

The Composer is a responsive, rounded multiline input with the approved controls: **Attach**, **Model**, **Reasoning**, and one state-dependent circular primary action (**Send / Steer / Stop / Interrupt / Cancel Send**). The visual AI may arrange the fixed controls ergonomically but may not remove, re-label semantically or replace their actions with unapproved flows.
- **Bottom anchor (user-reaffirmed 2026-10-14):** New Chat and Conversation share the same Composer bottom-edge anchor. Content growth expands upward; changing between these screens does not move the Composer. Desktop Composer and the two bottom capsules use the same bottom-spacing arrangement as mobile.

- **Enter submits content only (user-confirmed 2026-10-13).** Enter fires **Send** while idle, or **Steer** while a Turn is active with Composer content, and **nothing else**: with an empty Composer and no attachments, Enter performs **no** action and MUST NOT fire **Stop**, **Interrupt** or **Cancel Send**, and MUST NOT consume still-pending corrections. Shift+Enter inserts a newline; IME composition must never accidentally send. **Escape is the binding for cancel-type actions**: it triggers the correct cancellable action for the current state — **Cancel Send**, **Stop** or **Interrupt** — with sane modal priority and safeguards when a modal confirmation is active.
- Editor text can be undone via native Cmd/Ctrl+Z; ordinary text undo does **not** retract submitted messages, revert Rewind history, recover withdrawn Steers after consumption, undo attachments, or roll back filesystem actions.
- A draft belongs to an exact Conversation route or the independent current New Chat draft. Text and selected binary attachments must survive reload/revisit within the same browser where storage is available. Do not leak a draft across Conversations.
- A model/reasoning selector reflects backend-capable options and true current settings. A Composer pick not yet applied is local input state; an applied change must go through native Hermes configuration/session methods, never be hidden in localStorage as a competing active-model fact.
- During a send/upload transaction, prevent another Enter or Send while the transaction's acceptance is unresolved, regardless of additional typing; do not opportunistically submit those new characters.

### 1.7. Attach entry points and local selection

| Entry | UI contract | Native submit path |
|---|---|---|
| **Files** | Choose ordinary files, including ordinary PDF; show a small chip/icon and name | `file.attach` with bytes (`data_url`) → authoritative `ref_text` (`@file:...`) included in real submitted Prompt. |
| **Photos & Media** | Select images/media supported by native image routing; preview thumbnail | `image.attach_bytes` or verified equivalent native Image Attachment, bound to same runtime Session as Prompt. |
| **Take Photo** | Invoke mobile capture; one photo per capture, returning as an image attachment | Same image path as Photos & Media, not a fake ordinary-file `@file:` conversion. |
| Paste / drop | Add compatible selected content into Composer, preserve occurrence identity | Same type-specific native path when actually sending. |

**Transfer timing:** Selecting/pasting/dropping an attachment MUST NOT immediately upload to Hermes. Save it locally with the draft, check type/size at selection, and only transfer after the user issues Send. Duplicate visible filenames are allowed; distinct local occurrence IDs and the native server-generated paths/references distinguish them. Do not rename in the Composer or assume a filename is a unique identity. **User-confirmed attachment budget (2026-10-13): all attachments in the current draft together MUST NOT exceed 500 MB (500,000,000 bytes).** Selection, paste and drop MUST account for attachments already present, including duplicate-name occurrences; removing an attachment releases its contribution to that budget. Enforce the combined budget before admitting selected content into the draft. This is an aggregate limit, not a 500 MB allowance per file. Verify the complete actual upload and native submission path at this limit, including browser memory and websocket/API transport behavior; an ACK alone is not evidence of Agent readability. Do not retain the provisional 16 MiB per-file cap.

On historical messages: ordinary file attachments show only file type/name with an extension-derived icon; historical attachment chips are **not** click-to-preview, and no backend read-link reconstruction is required. Existing displayed image content may be restored only from real native history/projection, never from guessed local blob paths. PDF `pdf.attach` is not the default ordinary PDF mechanism (it renders pages into images, a different semantic action).

### 1.8. Primary action: normative decision table

Input assumptions: `draftText` is trimmed for meaningful send eligibility while preserving original edited content; `attachments` counts any selected file/photo; `pendingSteers` counts **server-authoritatively unconsumed** corrections; `turnActive` is based on actual live backend status, not merely a local spinner. “Send transaction” covers initial upload and unresolved submission admission.

| Priority / condition | Main action label / icon semantics | Exact result |
|---|---|---|
| Sending/attaching/submitting, before confirmed admission | **Cancel Send** (`X` or cancellation affordance) | Abort remaining client-side transfer, do not start an unaccepted Prompt, restore captured text+attachments snapshot. |
| Idle + no meaningful text and no attachment | **Send disabled** | No RPC or navigation. |
| Idle + meaningful text or attachments | **Send** (up arrow) | Resolve/create proper runtime, stage all attachments, only then invoke `prompt.submit`. |
| Turn Active + nonempty **text only** | **Steer** (arrow pointing left into a vertical bar) | Call native `session.steer` and show accepted pending correction provisionally. Repeating is supported. |
| Turn Active + empty draft + no Pending | **Stop** (square) | Stop only current running Turn. |
| Turn Active + any attachment + no Pending | **Stop** (square) | Stop current Turn; leave unsubmitted text/files/photos staged in Composer. |
| Turn Active + empty draft + one or more Pending | **Interrupt** (square, semantic action changed) | Atomically stop Turn and promote exactly the remaining Pending corrections to one next Prompt. |
| Turn Active + any attachment + one or more Pending | **Interrupt** (square, semantic action changed) | Same pending-only atomic handoff; never submits Composer attachments or text. |

Buttons MUST be driven by this precedence so a user can prepare attachments during a running Turn without accidentally sending them as Steer. Attach is **never disabled solely because a Turn is active**. No implicit redirect, generic queued Prompt fallback or silent attachment drop is permitted. A text-only Steer rejection is represented as a rejection/recoverable draft, not silently converted into a new Turn or routed to a different Session.

### 1.9. Pending Steer visualization and consumption

**Accepted Steer:** move the corresponding text from Composer into a User-shaped provisional bubble at the Timeline tail; additional accepted Steers form separate provisional bubbles and gently push older pending items upward. These are **not yet persisted User Messages**, even though they share the visual form. New Thinking, Tool, and Assistant stream content is inserted ahead of that provisional tail; the pending bubbles stay at the bottom until there is an actual native insertion point.

**Withdraw:** each **still-unconsumed** pending occurrence exposes an undo/withdraw icon (not a generic delete `X`). Successful withdrawal removes exactly that occurrence and **overwrites** the Composer text with its text; if editing/Rewind presentation state is open, retire incompatible edit state as specified by the confirmed product behavior. If the backend says “already consumed” or cannot prove pending status, do not claim a successful withdrawal or locally erase an actual message.

**Consumption:** all corrections consumed at the **same native insertion point** produce one real persisted User Message, with the backend's combined text and original ordering. Remove the consumed provisional bubbles and render that **single** real message at the actual insertion point. Do not preserve one historical bubble per original Steer or construct multiple timestamps for the batch. If a Turn finishes before pending corrections were inserted, the native Finalizer must carry the remaining combined text into exactly one follow-up Prompt (subject to the authoritative backend state). That behavior must be proved and, if native semantics lack withdrawal/exact pending identity, minimally extended in the native backend.

**Race rules:** acceptance, withdrawal, insertion, interrupt, natural finish, refresh and disconnection may coincide. The client uses authoritative receipt/consumption state, not estimated tool-call boundaries. A rejected/error/no-response steer must not be optimistically shown as securely accepted forever. Recovered pending state must not be reconstructed from the mere presence of `inflight_turn.correction_offsets`: that value is not proof of which occurrences remain withdrawable.

### 1.10. Stop, Interrupt and Cancel Send are distinct

- **Stop** requests native Turn interruption with no pending correction handoff; unsubmitted Composer content remains untouched.
- **Interrupt** requests native Turn interruption **and** atomic consumption of exactly the still-pending corrections as **one new Prompt**; pending text does not become a local draft and is not combined with the Composer's unsent contents.
- **Cancel Send** is a pre-acceptance *client transaction* control, not `session.interrupt`. It cancels any remaining uploads and prevents a not-yet-admitted `prompt.submit`; on successful cancellation restores the original snapshot of both selected attachments and text, **overwriting even draft changes made since the send began**.
- Uploads may already have produced server-side paths when canceled; V1 does not guarantee cleanup of those residual staged bytes. Such residues must never be submitted as a Turn after cancellation.
- If `prompt.submit` may already have been accepted, cancellation cannot pretend to undo it. The UI must reconcile the real server outcome and show an unambiguous submitted/unknown/rejected state; never blind-resubmit or fire a new prompt as a compensation.
- Escape follows the available cancel-type current action (**Cancel Send**, **Stop** or **Interrupt**) with sane modal priority; while a Send transaction is in progress Enter is blocked, and while a user is composing an IME sequence Enter/Escape must respect IME conventions.

### 1.11. Rewind + Edit: user-visible transaction

1. Offer **Reply** on eligible **persisted User Message** bubbles only; it is a rewind/edit action, not threaded replies and not an “Edit message in place” feature.
2. On entry, save the current draft snapshot; temporarily hide the selected User Message **and all subsequent Timeline nodes** in the foreground display; prefill Composer with that User Message's editable text and recoverable existing attachment references. Overwrite the visible draft.
3. Show a Composer `X` exit affordance for this **temporary edit mode** (distinct from Pending Steer Withdraw and Cancel Send). Exit restores the entire original Timeline and the saved pre-Rewind draft without modifying the backend.
4. User-confirmed 2026-10-13: **Send opens one confirmation dialog with a red Rewind and send button**. The two deliberate actions are Send and confirming that single dialog; do not add a second confirmation stage or another confirmation dialog. Cancellation keeps the edit and its recoverable draft. After confirmation, issue the existing Hermes `prompt.submit` truncation/rewind parameters with the correct durable persisted target. Follow Desktop's native rewind submit and busy/interrupt handling; never treat a busy truncation as an ordinary queued/steered prompt.
5. After successful backend truncation, the new history becomes authoritative. On rejection, restore a safe recoverable state; never hide source rows permanently on the assumption that the cut happened.
6. Refresh while the Rewind transaction is uncommitted MUST **not** auto-run truncation; any surviving editor text becomes an ordinary draft without armed destructive metadata or concealed history.
7. Rewind changes the actual Hermes transcript path; it does **not** reverse filesystem side effects or reclaim earlier file uploads. Cmd/Ctrl+Z does not roll back a committed Rewind and only provides native text-editor undo.

### 1.12. Slash catalog, command dispatch and human-only `/notebook`

> **第三轮适用性：** 保留共享catalog与浏览器临时只读结果；新版四分区正文为work／situations／discussion／candidates，旧栏目不继承。/noting不再控制Scheduler或受Memo阻止；Proposal英文指令见07 §8.10。

| Class | Examples | Mandatory Web behavior |
|---|---|---|
| Navigation | `/new`, `/reset` where genuinely registered, `/sessions`, `/resume` | UI navigation/session selection, with the **actual** command's semantics validated. Never invoke terminal interactive selection inside the browser. |
| Session/user controls | `/model`, `/reasoning`, `/compact`/`/compress`, `/stop` where genuinely supported | Use established UI controls or dedicated native RPC; synchronize actual model/effort/compression state. Do not submit command text as ordinary Prompt by accident. |
| Session title | `/title`, `/title <name>` | Read or set the current Conversation title. A live Conversation writes through the native `session.title` RPC; a stored row falls back to `PATCH /api/sessions/{id}`. The native answer is the only adopted title; the existing `RenamingText` animation plays on the real change. `/title --ai` is not a mode; use `/ai-title`. |
| AI title (Web-local) | `/ai-title` | Web command-router command (no native registry entry) that asks the existing stateless `llm.oneshot` RPC to name the current transcript, then applies the result through the same `session.title`/PATCH write. It is advertised locally in Web completions, not by the native catalog. AI proposes; the command writes. Failure leaves the existing title untouched and surfaces the native error. |
| Human-facing results | `/help`, `/status`, `/usage`, `/notebook`, `/noting` where supported | Render native results appropriately; `/notebook` is a **transient read-only Assistant-style chat result** without new model context or durable transcript row. |
| Dynamic commands | Skills, Bundles, plugins from native completion/catalog | Discover native availability; expose only those executable via correct browser/native dispatch, not a hardcoded stale catalog. |
| Terminal-only / test-specific | `/mouse`, `/redraw`, `/density`, `/theme`, `/logs`, `/clear` or others **where proven TUI-only** | Exclude or intercept at the Web command router, without deleting commands from shared Hermes registry. |

**User-confirmed title split (2026-10-17).** `/title` remains the native read/set entry: `/title <name>` sets the given title and bare `/title` reads the current title. AI naming is a separate Web-local `/ai-title` command; it is not a `--ai` flag on `/title`, and it is not a native registry command. The Web command router advertises it locally, while official clients keep their native `/title` semantics. `/ai-title` makes one stateless `llm.oneshot` title-generation call from the current transcript and then applies it through the same native write. A failed generation or rejected write leaves the existing title untouched and surfaces the native error.

**User-confirmed slash completion (2026-10-13, R2-C76):** Composer supports Tab completion for slash commands. Each completion candidate presents the command and description in one text flow with unified wrapping, rather than separate text containers that wrap independently. Commands must not wrap prematurely while the candidate has sufficient available width.

Slash completions and execution are separate: a suggestion MUST NOT imply a command can execute in this UI when only a terminal handler exists. Typing a literal command, clicking a suggestion, selecting a model pill and using a matching keyboard shortcut must converge on one underlying action. `/notebook` is human read-only, shows the currently effective Snapshot/explicit “none” state and its proper timestamp **as required by 02** within the temporary result, but does not show Anchor/pointer IDs, create a Turn, consume Memo, mutate Notebook, or persist the human display as model-visible history. Other valid slash results follow their native result and persistence contracts, not an indiscriminate `/notebook` special-case extension.

### 1.13. Usage cards and context indicator

**User-confirmed compact pill (2026-10-14):** The collapsed pill shows only Total Tokens and Cache Hit Rate. Total includes trustworthy input, cache-read, cache-write and output consumption; absent required source fields remain unknown. Cache Hit Rate uses known input/cache-read counters independently of whether total is available. Remove the Information icon and its dedicated popup. Saved native Session counters may be shown while idle; do not invent missing completed Turn counts or Latest Turn receipts, and defer cold Context recovery if existing native APIs cannot provide a trustworthy occupancy. No new API is authorized.

Under/near the Composer, show a restrained usage component with two equal-size views, **Session Total** and **Latest Turn**, not badges on each assistant bubble or an aggressive cost dashboard. Switching views MUST NOT change the container's dimensions or jitter the chat input.

| Metric | Session Total | Latest Turn |
|---|---|---|
| Input tokens | Native trustworthy total | Native completed Turn result |
| Cache Read tokens | Native trustworthy total | Native completed Turn result |
| Output tokens | Native trustworthy total | Native completed Turn result |
| Cache Hit Rate | `cache_read / (input + cache_read)` **only if the source counters have that exact meaning**; otherwise native trustworthy ratio | Same constraint using Latest Turn counters |
| Turns | Real Session Turn count | Not an extra session count |
| Model Calls | Not a replacement for Turns | Number of provider/model calls in that actual Turn |
| Cache Write | Not displayed | Not displayed |

**User-confirmed visibility (2026-10-13, R2-C73):** Once usage data for the selected actual Session has been successfully fetched, show it regardless of whether a Turn is running or idle. Turn activity MUST NOT suppress successful Session usage data. Latest Turn retains its completed-Turn meaning; fields for which no valid value has been obtained remain unknown. New Chat remains excluded under R2-C16.

**User-confirmed incremental updates (2026-10-14):** For each field in both bottom capsules and their expanded views, update only when a new valid native value is obtained for the same Session and corresponding statistical view; zero is valid. Missing fields, unknown results, failed reads and Turn-state changes do not clear a previously valid in-memory value. Values never obtained remain unknown. Retention is memory-only, never frontend persistence, and must not leak across Sessions or incompatible views.

Session Total SHOULD refresh as real native model-call/turn usage updates are available; Latest Turn switches to the most recently **completed** Turn, not the latest arbitrary assistant text segment. Missing/incompatible counters with no previously valid value are shown as unavailable/unknown, **not** obtained by dubious subtraction of lifetime aggregates. Cost presentation should not direct attention away from the conversation.

The adjacent Context control is a compact percentage ring, with an expanded detailed numerical usage/max view. Do not invent a category breakdown bar when authoritative categories do not exist. Context and Session Total numbers refer to the backend's real state and source; no independent local token accounting is authoritative.

**Runtime presence is not product state (user-confirmed 2026-10-17).** Binding, cold start, runtime recycling and “no live agent yet” are implementation details, not states the Chat UI may expose. Consequences:

- No control may render a sentence derived from a missing binding — in particular the Reasoning panel MUST NOT show an “Effective on this route” line, and the Context/Usage capsules MUST NOT say “Unknown” or “no active runtime”.
- **User clarification (2026-10-17): previous readings are allowed as cold-start estimates.** After a cold start or a recycled runtime, restore usable Context and Session Total readouts from the same Session’s persisted native readings rather than requiring an exact live measurement. Reusing the previous value as an estimate is explicitly authorized: Context can use its persisted usage anchor, while Session Total can use the existing native persisted Session counters or the previous trustworthy value for that statistical view. These are usable estimates until superseded by valid live readings; do not reject them merely because no live runtime measurement exists. If there is no trustworthy previous value, omit the number rather than label it unknown. The expanded Context panel states, in one short sentence, that the value appears after the next model response (“Shows after the next model response.”) instead of printing placeholders. This clarification permits estimates; it does not relax Session/profile ownership or the following known-model-mismatch rules.
- Restoring validates the anchor before trusting it: a fingerprint mismatch (rewind, edit, compaction) or an anchor priced by a **different model** than the Session now uses makes it untrustworthy and the number is omitted. An anchor persisted before model identity was recorded has no opinion and is still restored. This is the accepted trade-off: a cold start followed by a model switch may briefly show the previous model’s occupancy until the next real call replaces it, but a *known* mismatch is never presented.
- Restoring must reuse an existing native read path. Do not add a dedicated API for this; if no existing read carries the persisted anchor, stop and escalate instead of inventing one.
- A value restored this way is replaced by live numbers as soon as a real runtime reports them; no frontend persistence and no cross-Session leakage.

### 1.14. Compaction presence, cancellation and authentic history

During actual manual or automatic Compaction, the existing Context percentage ring **morphs in place** to a same-size animated loading ring; its normal percentage caption becomes **`Compacting`**. The expanded subview substitutes a **Cancel Compaction** action for the normal “used / limit” numbers while cancellation is meaningful. There is no extra Compaction status strip or second permanent control.

Cancel Compaction requests cancellation of **only** the active compression work, not the enclosing Turn, queued user actions, or the current legitimate transcript. If already committing or committed, the system reports that cancellation is no longer possible or complete; it must not leave a half-published context or fabricate a rollback. On actual completion/cancel/error, revert the Context indicator from reliable native state.

The post-compaction Timeline must display the **original native compaction summary/handoff** where it actually belongs, collapsed by default and expandable to its real content. On actual completion of manual, native automatic, or Noting-requested Parent compaction, reconcile the native Timeline and Context state promptly without requiring page reload or Turn completion. Noting task completion is not proof of Parent compaction completion; absent native textual handoff must not produce a synthetic summary. Native edge cases include a separate summary row, a composite carrier retaining real user text, Session rotation, no textual handoff and archived/compacted ancestors. The renderer follows the real projection; no synthetic “compression occurred” message, duplicated user identity or guessed marker is allowed. Full Foreground's audit node semantics from 02/04 do not become an excuse to build a V1 Full audit view.

### 1.15. Secretary Orb, Noting status and Memo Stick

> **第三轮适用性：** Memo计数、二级Memo面板和相关读取全部删除；Orb真实任务状态、失败提示与只读边界保留。下一次Idle展示须采用07新子开关及长度／时间资格，无资格不显示可执行倒计时。

**Visibility is governed by the GLOBAL Noting switch and route, not by conversation-local eligibility:** show Orb only on an **existing Conversation** page while the global switch is on. A conversation-local `/noting off` does **not** hide it. When global Noting is off, hide the Orb (rather than displaying a disabled orb). Never show it on New Chat or Files.

| View/state | Product behavior |
|---|---|
| Orb idle | Calm, unobtrusive, even when local Noting is off; no task-running claim. |
| Orb active | Lights only while a real Noting Task is executing; never from a mere countdown or “enabled” flag. |
| Orb finish | A short completion highlight then back to idle, from real task completion. |
| First-level Status | Compact, **read-only** actual status, available Idle Trigger estimate if any, Memo **count** and an expand affordance; **no Memo contents** in this level. |
| Memo second level | Replaces first-level Status body with a header and the full ordered **current effective Memo** plus collapse control; no Status-body remnants and no edit controls. |
| No valid next trigger | Show no invented countdown; a 0-second local clock never asserts Noting started. |
| Local `/noting off` | Preserve orb when global switch on, but render true local/not-running status; current Memo remains human-readable subject to authorized native reads. |

Use native status/task read with initial fetch on entry, refetch after Conversation change and reconnect, and existing owning Gateway event path for changes. An absolute authoritative next trigger time is preferred; the browser locally counts down rather than doing once-per-second HTTP polling. Orb, Status and Memo are entirely read-only: no Run Now, Stop, Noting toggle, Memo edit/delete, Notebook mutation or background control surface.

**User-confirmed system error notices (2026-10-14, R2-C106):** Consume the existing native `notification.show` / `notification.clear` events through the existing notice stack, retaining the actual owner, text, severity and keyed replacement/clear semantics. Noting failures use the Parent's native notice callback; they do not create a successful Finish Framework Message or completion highlight. Preserve real failure/commit/trigger behavior; error presentation is not a retry, Notebook repair or new API contract.

**User-confirmed notice lifetime (2026-10-17, replaces the 2026-10-14 ten-second value):** Error notices remain until manually dismissed. All ordinary notices automatically disappear after **5 seconds**, including native notices and local thinking-effort feedback, through the same notice lifetime owner. Notices can stack; native clear/replacement must not prematurely erase an earlier error occurrence. This uses the existing notice entry and adds no API.

### 1.16. Files viewer, scope and error states

Files is a read-only directory browser and previewer, rooted at the **default cwd returned by the Hermes backend**; no workspace switcher or project manager is in V1. Native `terminal.cwd` is configurable by Hermes, not by a new Secretary Files settings page. Directory listing, bounded text preview, supported media preview and download use existing authorized REST, with genuine response MIME/size/permission limits. The pane does not silently invoke editing, delete, write, rename or standalone “upload into folder.” Chat attachment staging remains independent and is an intentional existing *send* write operation.

Opening Files does not change the runtime Session cwd. Opening a historical Conversation with a different stored cwd does not automatically rewrite it or hide it; the backend's new/create/resume policies must be audited against the user requirement that **new** V1 sessions take the configured default cwd. If uniformity for a resumed historical session is desired, it requires explicit product authorization, not silent workspace mutation.

File list and preview have loading, empty, not found, permission denied, unsupported preview and oversized file states. Browser navigation/deep-link routes should not leak unauthorized host paths or credentials. Exiting via the Files top-right `Back to Chat` returns directly to prior chat/draft without breaking native browser history or resetting an unrelated active Turn.

---
## 2. V1-Only Additive API Contracts & Native Compatibility

### 2.1. Delta admission: no duplicate API layer

> **第三轮适用性：** N/F/A/D评估与原生复用保留；表中Memo能力删除，Notebook／Schedule按新owner和07接线，不额外保留旧读取入口。

**Every V1 requirement first receives one of four dispositions:** **N** = reuse existing native REST/RPC/Event unchanged; **F** = implement only in thin frontend UI/orchestration; **A** = add a minimal native method, read projection, or event at a proven missing seam; **D** = deferred and MUST NOT be implemented for V1. A user-visible action is not sufficient justification for a new backend method. The engineering team MUST record a file-level source audit and a failing invariant/test before creating any **A** item; Main/Integration reviews the evidence.

| Capability | Default disposition | Contract judgment |
|---|---|---|
| Session create/resume/activate and transient stored/runtime mapping | **N + F** | Existing Desktop pattern already implements this via RPC and in-memory mapping; **no new Conversation mapping API**. |
| Session list, stored history, lineage, basic files, default cwd, real model config | **N** | Call existing Dashboard REST and TUI Gateway directly. |
| Timeline grouping, bubble placement, human-friendly timestamps, sidebar/history, scroll/drafts | **F** | Presentation logic only; no new server storage. |
| Basic prompt, image and file attachments | **N + F** | Keep Hermes's distinct attachment calls and exact runtime binding. |
| Pending Steer independent identity, authoritative withdrawal/consumption | **A if existing implementation truly insufficient** | Current `session.steer` result alone does not establish independently withdrawable still-unconsumed occurrences. |
| Interrupt + exact remaining Pending as one next Prompt | **A if native path lacks atomic handoff** | Sequential `session.interrupt` then `prompt.submit` is not a safe approximation. |
| Cancel just Compaction, not Turn | **A if native cancellation hook not available at API boundary** | May require a small core cancellation probe/hook with generation checks. |
| Secretary Noting/Idle timer/current Memo and `/notebook` human read | **N where present, else smallest A** | Do not invent an entire Notebook REST hierarchy or dedicated second event socket. |
| Authentic compaction carrier, stable message kind, tool-argument visibility and trustworthy Latest Turn usage | **N where possible, else narrow projection A** | Add read/event fields only after proving the relevant existing projection cannot express the fact. |
| Full Foreground/Snapshot auditing, rich file-link preview, user-run Noting controls | **D** | No preemptive schema, endpoint or UI scaffolding. |

**Compatibility rule:** A proposed **A** method MUST have a new name rather than changing an existing method's parameters, response shape, acceptance semantics or errors. New event types/read-only projections may be added without changing existing fields. Exact implementation symbols for proposed deltas are **intentionally not asserted to exist**: the lead must publish the audited final method-name manifest before merging. The following sections freeze **semantics, schema obligations and atomicity**, not imaginary upstream method spellings.

### 2.2. Pending Steer: acceptance and authoritative identity

**Gap:** Native `session.steer` accepts text and may answer `{status:"queued",text}` for a running Agent, but this response does not itself prove that a specific, separately identifiable text occurrence remains withdrawable. `inflight_turn` correction offsets alone are not a pending inventory. The V1 UI requires exact occurrence-level withdrawal and a reliable ack/consume transition.

**Required native additive operation (logical name: `SteerSubmitPending`, method spelling finalized after source audit):**

| Contract item | Requirement |
|---|---|
| Input | Current **runtime** `session_id`, nonblank text, session/profile ownership through existing transport scope; optional client operation ID for retry deduplication only if the native backend can honor it atomically. |
| Admission | Reuse the actual native steer/correction queue and Turn fence; **do not** build a second correction queue or a parallel chat loop. |
| Accepted result | `{accepted:true, pending_id:<opaque>, state:"pending", ...}` or an equivalent explicit durable-enough authoritative receipt scoped to the live Session/Turn. The occurrence ID is stable until consumed/withdrawn/turn-retired; no browser-generated ID is an authority. |
| Rejected/non-steer result | Distinguish inactive Turn, compression-specific native queueing, invalid session, rejected payload, and terminal conflict. No silent redirect or ordinary Prompt fallback. |
| Consumption | Backend emits or exposes `pending_id` to insertion-point transition and the actual persisted User Message/row relationship (or exact consumed ID set), with **one** combined message for a shared insertion point. |
| Recovery | A read/snapshot path returns authoritative still-pending occurrences for the exact active runtime/Turn; reconnect must not infer their existence from stale client chips. |
| Lifetime | Pending identity need not become a new SessionDB entity; consumption persists through the **normal** Hermes message pathway, and no independent client persistence is needed. |

**Minimality choice:** The lead may implement one atomic enqueue-with-receipt handler and one pending snapshot rather than retrofit the existing `session.steer` response. The product does not require the illustrative `pending_id` field spelling, only its exact meaning and the absence of ambiguity. If the current Agent's correction queue is internally merged before it can retain occurrence boundaries, use the smallest in-core pending occurrence bookkeeping necessary **at that queue's real owner**, not client indexing of a concatenated string.

### 2.3. Pending Steer: Withdraw and consumption races

**Required native additive operation (logical name: `WithdrawPendingSteer`):**

| Situation | Atomic server result | UI consequence |
|---|---|---|
| Occurrence still pending | Remove that exact occurrence from the true pending buffer, return `withdrawn` with its original text | Delete only the provisional bubble; **overwrite** Composer text. |
| Already consumed | Report `already_consumed` (prefer actual persisted message/link if available) | Convert to/retain real history projection; **do not** restore Composer text. |
| Already withdrawn | Report idempotent already-withdrawn or a verifiable terminal rejection | Do not restore the same text twice. |
| Unknown/wrong Session/Turn | Explicit error, no mutation | Surface uncertainty; refresh pending snapshot. |
| Concurrent natural completion/Interrupt | Exactly one transition wins under the same authoritative queue/turn lock | No phantom withdrawn bubble and no duplicate follow-up Prompt. |

Consumption must remove the corresponding pending identifiers **as a single authoritative transition** at the actual insertion point. Temporary UI insertion occurs only after a successful acceptance receipt; provisional bubbles are cleared only by matching consumption/withdrawal/final handoff, not by elapsed time, a random event gap, or the user changing routes.

**Acceptance invariants:** `accepted_ids = pending_ids ∪ consumed_ids ∪ withdrawn_ids ∪ otherwise_terminally_rejected_ids` for a completed operation epoch, with each occurrence in exactly one terminal disposition; no acknowledged correction is silently lost; no consumed correction is still withdrawable; persisted combined text preserves the accepted order of all actually consumed occurrences.

### 2.4. Atomic Interrupt-and-submit of remaining Pending

**Required native operation (logical name: `InterruptAndSubmitPending`, not an alias for `session.interrupt`):**

1. Identify the exact live Session and active Turn under its existing owner/admission/turn lock; acquire an atomic barrier against native consumption, withdrawal, Finalizer queue drain and mid-Turn rotation.
2. Determine which accepted Pending Steers are **still unconsumed at that barrier**; do not read from the Composer, browser LocalStorage, speculative UI list or old correction offsets.
3. Interrupt/cancel the current Turn using its native shutdown semantics; ensure it cannot consume those selected corrections afterward.
4. Atomically reserve/consume those still-pending corrections **once**, in accepted order; admit exactly **one follow-up Prompt** using the existing native prompt admission/persistence/turn lifecycle (including the current stored-session tip after Compaction).
5. Return a machine-readable outcome that distinguishes `(interrupted, followup_accepted)`, `nothing_pending`, `already_transitioned`, `not_active`, `rejected` and genuine **indeterminate** acceptance. Return or make queryable the accepted new Turn/session identity. Do not emit success before actual backend admission.
6. On partial failure, preserve recoverable authoritative state or an explicit terminal error; prevent a second Finalizer or retry from dispatching the same text again. Native queue generation/lease changes must be accounted for.

It is **forbidden** to implement this as `await session.interrupt(...); await prompt.submit({text: locallyJoinedPending})`. That sequence loses atomic ownership of the buffer and races consumption, backend auto-continue, session rotation and other attached clients. A separate additive method is permitted because the required invariant genuinely crosses native atomic state boundaries.

### 2.5. Cancel Compaction without stopping the enclosing Turn

**Logical operation `CancelActiveCompaction` (method to be selected after inspecting existing native cancel hooks):**

| Item | Contract |
|---|---|
| Target | Runtime `session_id`; identify the active compression operation/generation, if any. |
| Allowed phase | While cancellation can prevent publication of the compression result; do not promise undo after an irrevocable commit. |
| Effect | Request cooperative cancellation of **only** active compression; preserve enclosing Turn, unrelated Pending Steers, committed history and normal Agent operation. |
| Race | A successful commit and a cancellation cannot both be published for the same generation; any canceled output must be discarded rather than overwriting newer history. |
| Response | Explicit outcome: canceled / cancellation requested / already finished / too late to cancel / no active compaction / error. |
| Events | Status returns from `compressing` to a true backend state; actual Session/Context/Usage updates drive the ring. |

The lead first audits `session.compress`, native compression lock/commit fences, cancellation tokens and any isolated compute-host variant. It may add a small Core hook only if such a safe cancellation edge is absent. **Never** rewire or weaken `session.interrupt` to simulate this product operation. A button in the UI is insufficient proof the cancellation semantics work.

### 2.6. Secretary human-only read contracts

> **第三轮适用性：** CurrentMemoRead整项删除。HumanNotebookRead改为新版work／situations／discussion／candidates四区；NotingPresenceRead与NextIdleRead采用新开关、联合流程与双阈值。真实归属、只读、沿既有传输与禁止浏览器伪造倒计时继续保留。

Secretary read APIs MUST preserve 02's actual `conversation_ref` ownership. First inspect current Core tools/status data and identify only missing consumer-safe projections. No read may initiate a Turn, trigger Idle/Force Noting, mutate Snapshot pointers, consume Memo or acknowledge a Reminder.

| Logical read | Required source data | Minimum return/behavior |
|---|---|---|
| `NotingPresenceRead` | Effective global config, target Conversation's local Noting participation and real running-task ownership | Explicit global on/off and local participation, actual task state (including unknown), task identity/status where real, no inference from a stale DB `running` row. |
| `NotingNextIdleRead` | Native trigger scheduler and current eligibility | Absolute expected due time if meaningfully determined; explicit absent/unknown if not; optional server observation time for clock correction. Never fabricate a due date. |
| `CurrentMemoRead` | Current effective Memo in Secretary-owned state.db | Ordered current entries and count, including an explicit empty result; read-only even when local Noting is off, subject to authorized global behavior. |
| `HumanNotebookRead` | Current effective Notebook pointer and Snapshot | Read-only rendered four-section content (or true no-Snapshot result) and Snapshot `created_at`; no Anchor/pointer ID by default; never a normal persisted chat row. |
| `GlobalNotingConfigRead` | Existing native config read | Enough to decide Orb visibility without adding a duplicate browser-maintained setting. |
| `ScheduleTableRead` | Current Conversation's formal Scheduler Schedule Table (`secretary_schedule_registry`, projected by `schedule_public_conn`) | Read-only rows with id, content, expression, canonical schedule, timezone, delivery mode, state, next due, pending count and last delivery; an unbound Conversation returns explicit `unavailable` with an empty table. Never synthesize a due time or a scheduled occurrence client-side. |

The engineering team may expose these through the **existing** REST/read paths or new small TUI Gateway RPCs as technically appropriate; do not force every read through WS or wrap existing REST endpoints in redundant RPCs. All results use correct profile/Conversation owner resolution; fetching status for Conversation A must not paint B after a rapid route change. Changes SHOULD travel on existing owning WS transport as small events/invalidation hints, followed by refetch when necessary. Do **not** add a dedicated Noting WebSocket or fast periodic status polling merely for the countdown.

**Browser state boundary (user-confirmed 2026-10-17).** The Web UI is not a second store: session titles, pins and the Schedule Table are read from the backend and rendered from that answer. A rename is one native write — `session.title` for a live Conversation, `PATCH /api/sessions/{id}` for a stored row — and a pin is one native `PATCH /api/sessions/{id}`; the response is the only adopted value; no optimistic copy, browser mirror, replay queue or two-way sync layer exists. Pinned ordering is deterministic from backend fields (`sessions.pinned` boolean, then activity); the client keeps no pin-order table, so a custom drag order is out of scope. The Schedule Table is refetched on Conversation open, on Secretary invalidation hints and on panel expansion; schedule mutations emit no dedicated invalidation yet.

### 2.7. Special `/notebook` result contract and inherited Core behavior

> **第三轮适用性：** 临时人类结果、不持久化、不注入模型及客户端边界保留；four-section指07新四区，不指旧标签结构；不把后台Framework完整Snapshot注入误写为slash也要注入。

The new human view has a **different persistence intent** from the inherited 02 slash path. In a browser-client command invocation:

- Use one minimal read-only operation or a scoped native command execution mode whose output goes **only to the requesting UI**; no normal `message_uid`, transcript row, model-history injection, faux Assistant Turn, Snapshot mutation or Memo consumption.
- Present the response as a temporary Assistant-style chat result so it visually aligns with other command results; the display type is UI-only, with a local occurrence ID for rendering **not** a server Message Identity.
- Keep each ephemeral result only in browser working memory. Reload clears these results; do not persist or restore them through SessionDB or browser storage. The last real chat state comes from REST.
- Before that memory reset, preserve each result at the Timeline sequence boundary of its invocation, including after later messages, live/history reconciliation and compaction updates. Its relative position must remain correct; refreshing away a misplaced card is not a fix.
- Existing TUI/CLI semantics MUST remain compatible unless a separately approved Core-level change is absolutely necessary. The implementation review must identify the actual slash dispatch → output persistence path to enforce the difference, not hide a persisted row via CSS.
- The currently effective Snapshot's existence, four-section text and creation time remain grounded in 02/04; do not invent an empty Snapshot when no pointer exists.

### 2.8. Conditional display projections: strict evidence gate

These items are **not automatically additional API work**. Before making a change, prove the mismatch using the native server event/REST output and Desktop's already-working projection.

| Need | Prefer existing | Add only if proven missing |
|---|---|---|
| True Compaction message | REST `GET /api/sessions/{id}/messages?include_compacted=true`, existing display projector and compaction helper | Narrow server-side `display_*` projection for a real carrier, preserving message identity and full raw content. |
| Tool argument deltas | Existing TUI Gateway streamed `event` frames and Desktop event reducers | Correctly scoped incremental tool-call ID + argument delta if the backend cannot expose it, preserving sensitive content policy. |
| Message kind | Native `role`/display metadata and Secretary’s explicit `<framework-message>`, `<instant-reminder>`, `<deferred-reminder>` carrier semantics | Minimal safe kind projection if wrapper-based classification of actual messages is ambiguous or visually destructive. |
| Usage | `session.usage`, real turn/model-complete events and stored metadata | Read-only Latest Turn/source counters or model-call count where existing data is insufficient; **never** generate per-message estimates. |
| Real Noting presence | Existing Noting runtime metadata, config and true task events | Minimal read/event delta only for missing authority, not a UI polling database. |
| Default cwd vs live Session cwd | `/api/fs/default-cwd`, `session.info`, original cwd resolver | Fix only a demonstrated V1 behavior inconsistency at the correct native seam, not by falsifying UI paths. |

### 2.9. Additive interface correctness checklist

Every accepted delta requires a completed mini-contract before merge: **owner**, source file, reason native reuse fails, input constraints, stable IDs, response/terminal statuses, errors, timeout/unknown-acceptance rules, thread/lock ownership, native event projection, durable-vs-ephemeral boundary, existing-client compatibility, and tests. Use the source file's naming conventions when selecting method names. Existing RPC names and DTOs remain untouched. No other new backend features may be introduced under the label “V1 convenience.”

### 2.10. Model and reasoning-effort capability projection (decided 2026-10-17)

**一句话决策。** 思考强度的候选档位必须由后端解析后下发；前端只渲染后端给出的集合，拿不到就显示“未声明”，不再用固定常量冒充真实能力。

**为什么需要。** 现状有三处脱节：

- 前端把 `minimal … ultra` 七档写死（`apps/shared/src/reasoning-effort.ts` 与 Web 的 `src/core/reasoning.ts` 是同源复制）；后端从不告诉任何客户端“这条路由支持哪些档位”。
- 后端其实已经维护了十几张厂商档位表（ChatGPT 订阅、Kimi Code、xAI、TokenHub 等，见 `agent/reasoning_effort.py`），OpenRouter / Nous 的聚合目录里也有 `supported_efforts`。但这些表只在“构造请求”时被用掉，没有任何一处序列化给客户端。
- 结果是：`ultra` 在多数路由上必然被钳成 `max`；`none`（关闭思考）在自定义端点永远不出现；未设置时界面同时显示 `medium` 与 `Unknown`。

**增量内容。** 在既有 `model.options` 响应的 `providers[].capabilities[<model>]` 上增加两个字段，不新增 RPC：

| 字段 | 类型 | 含义 |
|---|---|---|
| `supported_efforts` | `list[str] \| None` | 该 `(provider, model)` 已声明的思考档位；`None` 表示没有上游声明 |
| `supported_efforts_source` | `"config" \| "provider" \| "catalog" \| None` | 上述集合的来源 |

**解析顺序（后端一个函数，按序回退）。**

1. 用户配置 `model_overrides.<provider>.<model>.supported_efforts`。自定义端点（DeepSeek 直连）走这条；`_default` 可给目录未知的模型兜底。
2. 厂商代码表（`codex_supported_efforts`、`kimi_supported_efforts` 等既有常量）。
3. 聚合器目录（OpenRouter / Nous 的 `supported_efforts`，仅缓存态）。
4. 都没有 → `None`。

**前端必须区分的三态。**

| 状态 | 渲染 |
|---|---|
| `supported_efforts` 有值 | 只显示这些档位 |
| `None` | 显示现有兼容全集，并标注“该路由未声明，厂商可能再收窄” |
| 字段缺失（旧后端） | 回退兼容全集，不报错 |

**明确不做。** 不改任何发送路径（`clamp_effort`、`route_supported_efforts`、`agent/transports/*` 全部不动），不改未设置时的实际发送值；不新增 RPC 方法；不改 `binding.info`；不改现有字段语义；不为任何厂商新增档位知识——集合只能来自配置、厂商代码或聚合器目录。

**兼容性红线。** `model.options` 的结果由 `contracts/registry.py` 依 `ModelCapabilities` 强校验（`extra="forbid"`）。新增字段必须同时进入契约模型并重新生成 `gateway-contract.generated.ts` / `.openrpc.json`；漏做会让 Desktop、TUI 与 Web **同时**收到校验失败。同步完成后新增字段是可选、只读的，不读它的客户端行为完全不变。

**已知边界。** Codex app-server 上的 `ultra` 可能少报一格，因为解析时拿不到会话的 `api_mode`；聚合器目录为缓存态，冷启动返回 `None`，界面落到兼容全集且不阻塞。

**验收。** 后端覆盖三种来源各一个用例与 `None` 回退，且契约生成物字节一致；前端三态各一个渲染用例，选择器只信任该字段或兼容全集；Desktop / TUI 的既有字段与数值零变化。

**实现落点（2026-10-17，已交付）。**

- `agent/models_dev.py`：`ModelCapabilities.supported_efforts` 字段；`declared_supported_efforts()` 读 `model_overrides`（显式优先，`_default` 仅在目录不认识该模型时兜底）；`model_overrides.supported_efforts` 进入 canonical key space。
- `agent/reasoning_effort.py`：`declared_provider_efforts(provider, model)`，覆盖 ChatGPT 订阅 / Codex、Kimi Coding、xAI 三家已声明的表；其余 provider 返回 `None`。
- `hermes_cli/inventory.py`：`_declared_efforts()` 按 `config > provider > catalog` 回退，`_apply_capabilities` 仅在确有声明时写入两个键。
- 契约与生成物：`ModelCapabilities` 加两字段，`scripts/gen_gateway_contracts.py` 已重跑。
- Web：`src/core/reasoning.ts` 三态返回（`source` / `undeclared`），`ReasoningSelector` 对未声明路由显示提示；其余客户端不读该字段，行为不变。
- 实测：`openai-codex` → `none/low/medium/high/xhigh/max`；`kimi-for-coding:k3` → `low/high/max`；`custom:deepseek-flash`（未声明）→ 不出现该字段；带 `model_overrides` 声明时来源标 `config`。`ModelOptionsResult` 与 `ModelOptionProvider` 均可通过校验。

---

### 2.11. New Chat Profile selection and Conversation icons (user-confirmed 2026-10-17)

This decision replaces the earlier proposal to place Profile entries inside the Model selector.

- **Placement and content.** Only the home / New Chat screen exposes a separate Profile dropdown. It is independent of the Model selector; each Profile option shows its name only, without a model, description, system prompt preview or other secondary metadata. Existing Conversation screens do not expose a control that pretends to change that Session's Profile in place.
- **Native ownership.** Read the available Profile roster through Hermes' existing native API. Selecting a Profile changes the New Chat environment before Session creation, including its model/provider defaults, SOUL/system instructions, memory, tools and native state ownership. The eventual `session.create` and all subsequent operations use that Profile. Existing Sessions remain owned by their original Profile; no transcript migration, copy of another Profile's prompt into the current Session, or second profile state store is introduced.
- **Draft and transition boundaries.** Preserve separate draft ownership per Profile with the existing draft mechanism. Profile-scoped model/effort choices and staged paths must not leak into another Profile's first send. A pending Send/session creation must not have its owner changed by the dropdown. Load native defaults/capabilities for the selected Profile, and do not publish a late response for the previous Profile into the new selection.
- **Workspace reuse.** Profiles may configure the same `terminal.cwd` to share project files; this does not merge their Session stores, memory or instructions.
- **Conversation row icons.** The icon to the left of each sidebar Conversation is determined by that row's owning Profile. Conversations of the same Profile use the same icon; the configured Profiles use distinguishable icons. Keep a centralized, hardcoded Profile-name-to-icon mapping in the frontend source, as the user requested. Do not add a config field, persistence layer or icon-setting UI. Render the Profile's icon using the existing icon system without adding text metadata to the Profile options.

The native Profile roster, Session ownership and existing APIs remain authoritative. The frontend mapping is presentation data, not a replacement Profile registry. A newly configured Profile needs an entry in that source mapping to receive its own icon; an unmapped name uses a generic fallback. Implementation and evidence status remain in root `CLAUDE.md`.

## 3. Native Integration — Verified Wiring & Implementation Handoff

**Purpose and limit.** This division records the native behavior and code seams **actually investigated** in the fork, and the product obligations they support. It is **not** a substitute for the implementation lead's current-commit audit or a prescriptive reimplementation of Hermes Desktop. GPT-6 Astra owns subsequent code-level design, exact DTO validation, module boundaries, and implementation choices. If an interface named here behaves differently at implementation time, test the deployed code and record the discrepancy; do not silently rewrite the user-facing contract of divisions 1–2.

### 3.1. Verified transport and authority map

| Concern | Verified native entrance | Reference implementation / backend source | Boundary to preserve |
|---|---|---|---|
| Gateway transport | WebSocket `/api/ws`, JSON-RPC requests plus `event` notifications | `hermes_cli/web_routers/chat_ws.py` → `tui_gateway/ws.py` → `tui_gateway/server.py`; Desktop `apps/desktop/src/api/client.ts` | Browser is a **client**; Gateway owns runtime objects and dispatch. Deployment must prove browser-compatible auth, origin, WSS and REST access. |
| Stored session list/detail/history | Dashboard HTTP `/api/sessions`, `/api/sessions/{id}`, `/api/sessions/{id}/messages` | `hermes_cli/web_routers/sessions.py`; Desktop `apps/desktop/src/api/sessions.ts` | REST/SessionDB is the durable display-history source; it is not replaced by a second client repository. |
| New/recovered/live runtime | `session.create`, `session.resume`, `session.activate`, `session.active_list` | `tui_gateway/methods_session.py`; Desktop `apps/desktop/src/app/session/hooks/use-session-actions/index.ts` | Native lifecycle is server-owned; short-lived runtime addressing and UI route identity are different. |
| Prompt and control | `prompt.submit`, `session.steer`, `session.interrupt`, `session.compress` | `tui_gateway/methods_prompt.py`, `tui_gateway/methods_session_interrupt.py`, `tui_gateway/methods_session.py` | Existing signatures/semantics stay intact; only division 2's **proven** atomic gaps warrant additions. |
| Usage/context | `session.usage`, `session.context_breakdown` | `tui_gateway/methods_session.py`; actual model-call/turn events where available | Counters must retain their source meaning; no reconstructed false per-turn precision. |
| Slash and completion | `complete.slash`, native command-dispatch/Slash handlers | `tui_gateway/methods_complete.py`, `tui_gateway/methods_slash.py`, `tui_gateway/methods_secretary.py`, Gateway registered dispatch | Use the actual command registry/availability and Web-specific routing; never assume all terminal commands work in a browser. |
| Files/default cwd | `/api/fs/default-cwd`, `/api/fs/list`, `/api/fs/read-text`, `/api/fs/read-data-url`, `/api/fs/download` | `hermes_cli/web_routers/files.py`; Desktop `apps/desktop/src/lib/desktop-fs.ts` | Read-only Files is not a file-write tool; backend path policy and active terminal backend matter. |
| Other managed/media files | Existing `/api/files/*`, `/api/media*` routes | `hermes_cli/web_routers/files.py`; Desktop `apps/desktop/src/lib/media.ts` | Distinct native security/transfer semantics; do not blanket-substitute for `/api/fs/*` or attachments. |
| Attachments | `file.attach`, `image.attach_bytes`, `image.detach`; `pdf.attach` is a separate page-rendering operation | `tui_gateway/methods_prompt.py` | Type-specific semantics and the exact runtime `session_id` must be respected. |
| Event replay | `session.events.since`, Gateway event sequence and epoch | `tui_gateway/methods_session.py`, `tui_gateway/event_replay.py` | Replay is **bounded**; a truncated replay requires authoritative history/state resynchronization. |

The file paths identify the checked **2026-10-12 fork snapshot**, not a perpetual guarantee of identical line numbers or contracts. This table is the source-backed **reuse inventory**; it is intentionally not duplicated in division 2 as newly proposed API schemas.

### 3.2. Session continuity: Desktop's actual client/server pattern

- Desktop invokes `session.create`, `session.resume`, and `session.activate` through Gateway API requests; its renderer does **not** directly call the Python Agent Core. `session.create` yields both `session_id` (runtime) and `stored_session_id` (durable locator). `session.resume` accepts a stored locator and can reattach a live session or establish a fresh runtime ID.
- Desktop maintains **stored → runtime mapping in memory**; it intentionally does not trust persisted runtime IDs. It persists some presentation/connection hints, but Secretary V1 **does not inherit** the broad Desktop persistence system. References: `apps/desktop/src/app/session/hooks/use-session-actions/index.ts`, `apps/desktop/src/store/session-states.ts`, `apps/desktop/src/store/session.ts`.
- `session.activate` is a live-session rebinding point; on missing, recycled or mismatched runtime identity, the client falls back to verified stored-session resume. A single-flight approach for the same stored target is a proven Desktop pattern, not grounds to create a server Conversation API.
- The Secretary Core `conversation_ref` defined by 02 remains the owner of Notebook/Noting state; it is **not** the ephemeral Gateway runtime ID or a license to implement another browser-side Conversation Identity Registry. Correct lineage after compression must be resolved from Hermes's actual persisted facts.
- Merely opening a route may fetch REST history without creating a runtime; when actual execution/status binding is required, use existing native lifecycle RPCs. Never cancel another Conversation's turn on a route switch or re-submit a Prompt merely because the websocket reconnected.

### 3.3. History, live stream and reconciliation

| Input | Confirmed behavior | V1 use / constraint |
|---|---|---|
| `GET /api/sessions/{id}/messages` | Resolves the session's resumable tip; reads compression ancestors, supports `limit`, `offset`, `order`, `include_compacted`; returns a paginated display projection. | Authoritative old content, native message position, real Compaction; pages must preserve stable chronology and scroll anchoring. |
| `session.resume` / `session.activate` | Bind or rebind runtime, report session status and available live/in-flight information; Desktop can request omitted/deferred transcript. | Live control attachment, **not** an alternative permanent history store. |
| WebSocket `event` stream | Native session-scoped deltas/status; events include the runtime identity. | Paint live output and controls for the correct Conversation; keep the pending-steer visual tail separate from durable rows. |
| `session.events.since` | Bounded replay, `truncated` signal and a process `epoch`. | On reconnect, replay safely when possible; after truncation/restart refetch REST history and true runtime status. |

Desktop's existing REST-prefetch-plus-resume and transcript reconciliation is the main **behavioral reference**. GPT-6 Astra may simplify its implementation for a single backend, but MUST preserve the ordering, identity, no-double-send and no-false-completion invariants. Do not convert the browser into a second persisted transcript mirror.

### 3.4. Native action composition and established gaps

| Product action | Native building block already confirmed | Necessary boundary / gap |
|---|---|---|
| First Send | `session.create` → staged attachment RPCs if any → `prompt.submit` | Create once on first send, not on page entry; `prompt.submit` acceptance and Turn completion are separate. |
| Active-turn pure-text Steer | `session.steer` | Existing acceptance alone does not prove independently withdrawable pending occurrences or their exact later consumption; division 2 sets the **required outcome** without dictating an internal patch. |
| Stop with no pending | `session.interrupt` | Avoid submitting unsent Composer content. |
| Interrupt with pending | Native interrupt/turn machinery | Requires one authoritative interrupt-and-promote transition; **not** two client RPCs joined by local text. |
| Rewind + Edit | `prompt.submit` native truncation parameters and Desktop's prior rewind pattern | Verify the durable target and explicit user consent; do not substitute UI-only history deletion. |
| Manual Compaction | `session.compress`; backend status/rotation | Canceling compression **alone** is not equivalent to `session.interrupt`; the safe cancellation edge must be audited. |
| Native Slash | Verified completion and dispatch surfaces | Browser routes navigation/UI actions locally, uses proper native control for core commands, and filters only genuinely incompatible commands. |
| Human-only `/notebook` | Secretary notebook command/result path | **Approved behavior change:** current `tui_gateway/methods_secretary.py` persists `/notebook` feedback; V1 must instead return a transient human-only result with no persisted/message-context side effect, while preserving unaffected existing clients. |

These are implementation **handoff facts and requirements**, not a command to invent a particular API name, lock layout, worker abstraction, or frontend state-library architecture. The lead may use verified equivalent native calls where appropriate, with a recorded reason.

### 3.5. Attachments, filesystem and cwd facts

- `file.attach` accepts a gateway-visible path or `data_url` and returns `ref_text` with an `@file:` reference; the ordinary PDF path is the same. `image.attach_bytes` accepts base64 image data and registers an image on the correct runtime session. The actual prompt/agent perception must be tested, not inferred from a successful upload ACK.
- Native `pdf.attach` renders selected PDF pages as images; it is **not** the ordinary PDF attachment contract. `image.detach` exists, but cleanup semantics for canceled multi-file uploads must be proven; do not promise remote deletion where the native API does not provide it.
- `/api/fs/*` and `/api/files/*` are distinct REST families with their own path/security and transfer semantics. A read-only Files viewer uses authorized native read endpoints, not an unrestricted filesystem proxy. Any existing write endpoints remain outside this UI's Files surface.
- `terminal.cwd` is Hermes's configured default workspace. `GET /api/fs/default-cwd` exposes a Files-side default, while Gateway's session create/resume cwd resolution has additional session/profile/backend rules (`tui_gateway/session_workdir.py`, `tui_gateway/server.py`). **New** Secretary sessions must use the effective backend default; existing different-cwd history remains discoverable and must not be silently migrated.
- Browser binary uploads must respect the actual implementation's websocket framing, raw-size and memory limits. An unverified aspirational number is not a V1 compatibility guarantee.

### 3.6. Secretary and display facts that require care

- Existing Core authority: Notebook/Noting/Memo and `conversation_ref` follow current 02, including confirmed V1.6 revisions, then still-effective 04 increments under §0.2. This Web UI reads and presents them; it does not manufacture a second registry, mutable Notebook document, Trigger scanner or Reminder scheduler.
- Framework Messages, Instant Reminders and Deferred Reminders follow their **actual carrier and history** semantics. The UI renders each genuine surfaced message in the Timeline with a distinct treatment; it must not convert a due-but-unmaterialized schedule into a synthetic historical bubble.
- Original `/notebook` feedback persistence was found in `tui_gateway/methods_secretary.py`; this is the **source-proven conflict** with the approved browser-only temporary viewer. The remedy is intentionally left for GPT-6 Astra to design within division 2's compatibility rules.
- Tool deltas, Latest Turn usage, Compaction read projection and Noting status/events were discussed and partially inspected, but their **complete end-to-end consumer contracts were not proven** at the time of this specification. GPT-6 Astra MUST verify each against the current fork; do not treat a logical proposal in division 2 as an existing DTO or hardcode imaginary fields.

### 3.7. Audit and handoff ledger

For each V1 feature, the implementation lead records only the following compact ledger; a detailed per-function implementation plan is **not** part of this specification:

| Field | Meaning |
|---|---|
| **Native source** | Verified file and actual REST path / RPC / event, or `none` if genuinely absent. |
| **Classification** | Reuse unchanged **N** / frontend-only **F** / justified additive **A** / deferred **D**. |
| **User-visible invariant** | Reference to the normative clause in division 1 and, if applicable, division 2. |
| **Evidence** | Integration test, source proof, or counterexample explaining a required additive delta. |
| **Owner and status** | GPT-6 Astra owns technical closure; visual AI owns styling-only work. Track unverified items as such. |

The ledger is the handoff artifact for coding. It is **not** a second design document authorizing new product interactions or a reason to turn every backend method into a new wrapper.

---

## 4. Implementation Ownership, Design-System Engineering & Acceptance

### 4.1. Technical accountability, development and independent review

> **第三轮适用性：** 第二轮角色安排保留作历史记录，不作为第三轮人员／模型指定；第三轮以新编排为准。

Current-round user-authorized model assignments and gate order are recorded in the Snapshot Index; they do not waive either final gate.

**GPT-6 Astra high is Main/Integration and the accountable technical lead across frontend and backend; GPT-6.1 Sol high performs concrete Development.** Astra owns coverage, architecture decisions, delegation, review, integration and final defect closure; Sol implements assigned features, native integrations and tests, returning complete stage evidence for review. The specification does not prescribe their internal code structure, concurrency primitives or file-by-file patch sequence. Independent Verification uses **Astra high**; independent Validation uses **Astra medium**.

The independent **visual designer, Astra medium**, owns visual art direction, design-system specification and implementation, typography, color, spacing, composition, iconography, motion and responsive visual polish **within the frozen interactions**. It may build reusable styled/presentational components, but MUST NOT independently implement or revise Agent controls, network clients, Session state machines, event semantics or navigation behavior.

| Decision or work product | Accountable AI | Specialist role / limits |
|---|---|---|
| Source/code audit and implementation architecture | **Astra high Main/Integration** | Sol high performs scoped audits/development; visual designer receives stable component requirements. |
| REST/WS and Hermes Session/Core integration | **Astra high Main/Integration** | Sol high implements; visual designer does not touch API contracts. |
| Composer/Steer/Interrupt/Rewind/Slash state machines | **Astra high Main/Integration** | Sol high implements; visual designer styles specified states without new transitions. |
| Design tokens, reusable visual components and responsive polish | **Astra medium visual designer** for delivery; **Astra high Main/Integration** for integration/review | Visual permissions remain limited to 06's frozen interactions and accessibility requirements. |
| Automated tests, race/failure cases, native compatibility | **Sol high Development**, reviewed by **Astra high Main/Integration** | Visual designer may provide appearance fixtures; technical closure remains with Main. |
| Independent specification Verification | **Astra high independent reviewer** | Establish requirements from the frozen specifications, then review implementation and evidence. |
| Independent user Validation | **Astra medium independent validator** | Validate actual user input-to-output paths after Verification passes. |
| Final integration, defect triage and delivery evidence | **Astra high Main/Integration** | Review complete stage returns; Sol and visual designer fix defects within assigned scope. |

### 4.2. Design system as a production engineering deliverable

> **第三轮适用性：** 设计系统与组件治理保留；Memo相关组件退出，新版不因为本节列过Memo而继续实现。

The design system is **mandatory**, not a mood board or an optional last-mile styling pass. The visual AI establishes a coherent, reusable foundation using the approved React/assistant-ui/shadcn/Tailwind stack.

| System layer | Required discipline |
|---|---|
| **Tokens** | Central, semantic definitions for colors, typography, spacing, radii, shadows, elevation, motion and responsive rules; prefer semantic tokens over page-specific magic numbers. |
| **Components** | Shared primitives and composed visuals for top nav, sidebar, composer, action button, message kinds, tool/thinking disclosure, usage/context, popover, files list/preview and Secretary Orb/Memo. |
| **States** | Consistent hover, focus-visible, selected, active, pending, busy, disabled, unknown, error and reduced-motion variants without hiding required status. |
| **Responsive** | Desktop and mobile share a design language; keyboard insets, touch targets, safe-area handling and reading width are considered in visual delivery. |
| **Governance** | Any reused style change is made in the relevant token/component layer, with visual regression checks; no scattered literal colors, arbitrary one-off CSS overrides, duplicate design token values or page-local invented components where reusable semantics exist. |

Local implementation exceptions are permissible only when they represent a genuinely unique visual need, follow the token system, and are documented; they MUST NOT become an escape hatch to scatter unreviewed styling across screens. The system must remain maintainable after a different AI or human picks up the code.

### 4.3. Fixed product interactions; visual freedom only inside those bounds

- Division 1 controls **what an element does, when it exists, where behaviorally fixed controls appear, which action is enabled, and what errors mean**. The visual AI controls **how those facts are legible and aesthetically expressed**.
- The visual AI may decide Timeline time-label density, visual grouping and motion within the precise contract that times appear only outside bubbles. It may choose colors/typography for Framework Messages and both Reminder kinds, but MUST NOT reclassify, suppress, invent or relocate their real Timeline messages.
- The mobile Sidebar button remains **top-left** across New Chat/Conversation/Files; `Back to Chat` appears only on Files navigation bar **top-right** and has the fixed one-step return-to-chat semantic. This is not an optional visual rearrangement.
- One fixed Composer primary action follows the exact matrix in §1.8. The visual AI cannot add a secondary “Send Anyway,” a floating Queue, a separate Reminder inbox, an Orb `Run Now`, or a different Rewind flow.
- Questions about undefined styling can be resolved by the visual AI. Questions that would change interaction/product scope require explicit user approval, not an AI's unrecorded preference.

### 4.4. Sequencing without prescribing code architecture

> **第三轮适用性：** 本节是第二轮里程碑，不是第三轮实施计划；Memo相关里程碑退出，新切片见07 §9。

Implementation order is a **dependency guide**, not a file-by-file plan imposed on Astra:

| Milestone | Outcome and exit evidence |
|---|---|
| Native compatibility baseline | Proven REST/WS connectivity, identity map and current API status, plus a classified N/F/A/D ledger. |
| Foundational UI/design system | Shared tokens and components, three main routes and draft restoration without backend side effects. |
| Authentic conversation | Paginated history + live events + status reconstruction; true message kinds, times, Thinking/Tool presentation and Compaction history. |
| Submission/control | New Chat Send, type-specific attachments, Steer/Withdraw, Stop/Interrupt, Cancel Send, Rewind with real backend invariants. |
| Secretary/Files and utilities | Native Slash, Context/Usage, Orb/Memo, human-only Notebook, read-only Files and return navigation. |
| Hardening and final acceptance | Localhost in-app browser acceptance at all four required viewports (§4.6), reconnection/race and security/accessibility checks, relevant regression evidence; real-device keyboard/camera/system swipe-back checks remain later dedicated validation. |

Astra may reorder independent work and choose its preferred frontend engineering approach so long as every product and interface contract is met. Do not build future product infrastructure as a prerequisite to V1.

### 4.5. Normative acceptance matrix

A feature is not accepted because its button is present or its RPC returned 200. Use the backend's actual messages, persisted rows, usage and live state as validation evidence.

| Test focus | Required observable proof |
|---|---|
| Drafts and pages | New Chat navigation does not create a Session; same-browser text/binary drafts survive reload; Files right-top `Back to Chat` returns directly to previous chat; browser Back/Forward works naturally. Native system swipe-back remains required product behavior with real-device proof deferred under §4.6. |
| Identity and continuity | Stored→runtime mappings are memory-only and safely rebound; existing history loads by REST; true compression lineage appears as one Conversation; no cross-session stream bleed. |
| Streaming and history | True Thinking/tool parameter events appear as available; replay truncation refetches history; pending bubbles do not corrupt message ordering; no duplicated persisted assistant/user content. |
| Timeline semantics | Human-readable time appears only outside message bubbles; no per-message mandatory prefix; real Framework/Instant/Deferred Reminder carriers are distinct Timeline messages; no invented reminders or synthetic compaction markers. |
| Attachment success | Selected items remain local until Send; a real image is actually understood by the configured DeepSeek model (user confirms current V4.1Flash supports vision); verify actual configuration and request, without replacing the native provider or adding model routing. Ordinary file/PDF `@file:` is actually readable by Agent; duplicate filenames remain independent. Real-device camera invocation proof is deferred under §4.6, while Take Photo remains implemented. |
| Cancel Send | Before acceptance, cancellation restores the pre-send local text/binary snapshot; no duplicate turn; uncertain acceptance is reported rather than treated as a definite cancel. |
| Steer and Withdraw | Multiple pure-text steers accepted during an active turn; independent pending occurrences; consumed corrections cannot be withdrawn; successful withdrawal overwrites Composer; merged real user row in correct native position. |
| Stop and Interrupt | Stop has no unintended next prompt; with pending, Interrupt cuts the Turn and admits exactly one follow-up of **only** unconsumed pending content; attachments/unsent draft are not included. |
| Rewind | Two explicit confirmations, correct truncation target and replay, cancellation restores prior view; reload does not silently execute stale rewind; filesystem side effects remain untouched. |
| Usage and Compaction | Truthful Session Total/Latest Turn and Context data; Context ring becomes Compacting in place; cancel affects only compression; real handoff/summary displays correctly, including no-text and combined-carrier cases. |
| Secretary and Slash | `/notebook` human view is temporary and not present in DB/model context; current Memo is read-only and ordered; Orb visibility follows **global** switch; real running state and due time never guessed. |
| Read-only Files | Real backend default cwd, authorized list/preview/download, accurate errors; no unauthorized write/edit/renaming control; nondefault historical sessions are not arbitrarily hidden. |
| Security/robustness | Auth, origin, sensitive data, file read boundaries, Markdown rendering, browser IME/focus/keyboard, accessibility, large transcripts, native regression and compatibility pass within the declared local coverage. Four-viewports retain complete layouts and operations; real-device soft-keyboard checks are recorded separately under §4.6. |

### 4.6. Test layers and compatibility gate

> **第三轮适用性：** 第二轮证据与判定按原版本保留，不能替代第三轮两个独立门禁；新范围与证据由第三轮索引确定。

- **Unit/contract tests** confirm product state machines, visual component props, identity rules, slash routing, draft isolation, message-kind projections and mandatory API outcomes.
- **Gateway/Core regression tests** exercise only genuine additive behavior and prove unchanged clients can still call all existing methods with their original semantics; include crash, simultaneous correction consumption/withdraw, interrupt races and Compaction cancel/commit races where relevant.
- **Browser integration tests** use real REST+WS against the target fork, not UI mocks alone; include REST history paging, authentic message kind preservation, attachment-to-Agent readability, reconnection and uncertain Submit outcomes.
- **Required browser/visual acceptance** runs on local localhost through the in-app browser at desktop **1440×900** and **1024×768**, and mobile **390×844** and **320×568**. Every viewport MUST retain complete, usable layouts and operations, including the sidebar, Files return, Composer, Timeline, dialogs and Secretary views; small-screen usability is mandatory. The visual designer may own appearance fixtures; Main/Integration owns final behavior proof.
- **Later dedicated real-device validation** covers actual mobile soft keyboard, camera invocation and native system swipe-back. Their product capabilities remain required and implemented; browser viewport evidence MUST NOT be presented as proof of these device behaviors, nor does the deferred proof remove the features.
- **V1.6 handoff** is included in Round 2 acceptance: reuse valid historical evidence, supplement only transferred gaps and impacts of actual new changes, and do not repeat V1.6's own full Verification. Round 2 still requires its complete independent Verification and Validation gates.
- **No false green:** unavailable/unproven APIs are reported as blocked or incomplete; tests cannot pass by inventing DTOs, hardcoding counters, hiding legitimate messages or silently downgrading product rules.

### 4.7. Delivery checklist and change control

> **第三轮适用性：** 保留如实报告、兼容和薄客户端原则；Astra/Sol固定分工仅属第二轮，本轮角色按新计划。

The final implementation report MUST contain: (a) current source revision and changed files; (b) native-reuse versus additive-delta list with why each addition was needed; (c) verified client/backend contract results and existing-client compatibility; (d) test matrix with real evidence and known limitations; (e) design-system token/component governance checks; (f) proof of no new backend service, client business database or durable API history cache; and (g) a concise list of unresolved items, if any, without declaring them complete.

**Change control:** no engineering, review or visual role may reinterpret a V1 product behavior, add an unrequested page/interaction, alter an existing native API or expand future scope without explicit user authorization. Astra leads technical decisions and Sol implements within assigned scope; neither may silently replace approved UX with a weaker behavior.

---

## 5. Planned Future Product Capabilities — Explicitly Out of V1

### 5.1. Full Foreground and provenance audit

The future UI is a **human-readable audit projection**, not a different chat history implementation. Retain 02/04's precise `Full Foreground` semantics: unique `Context Prelude`, ordered logical message nodes, authentic Compaction projection, and Anchor/Snapshot attachments. Message Identity is `(conversation_ref, message_uid)`; composite compaction may project adjacent logical nodes without inventing a second identity. The future viewer may expose source/version validity and audit anchors, but **none of its endpoints, database tables, message-node UI or navigation scaffolding is required in V1**.

### 5.2. Historical Notebook/Snapshot and advanced Memo views

> **第三轮适用性：** 旧Memo未来能力已取消，不再保留。Notebook历史审计仅为过去记录的未来设想，本次不实现已退出内容的短期检索通道。

Future screens may browse immutable Notebook Snapshot history, Anchor chronology, item lifecycle audit, archived Memo batches and richer human provenance. V1 has only the current effective Memo Stick and temporary human-readable `/notebook` result. Future read access may remain valid when Background Noting is disabled, subject to Hermes's authorized global policy; current V1 must not introduce editable Notebook surfaces or pretend archived data is an active Memo.

### 5.3. Rich Framework/Reminder and scheduler presentation

Future richer message cards may show provenance, delivery kind, timing, pending/consumed state and detailed schedule linkage. V1 already requires **distinct, real Framework Message / Instant Reminder / Deferred Reminder nodes in the ordinary Conversation Timeline**, not a generic notification overlay. Any future enhancements must preserve 02/04's actual carrier semantics and must not reconstruct due deliveries from guessed UI clocks.

### 5.4. Expanded workspace and file interactions

Future phases may add workspace switching, multi-root views, authenticated historical attachment preview/download, file editing, deliberate uploads into a selected folder, or richer artifact preview. These are **not** included in V1 Files; chat attachments use the separate native send pipeline. No unrequested filesystem write/management UI or workspace database is to be introduced prematurely.

### 5.5. Broader surfaces and advanced interactions

Native desktop/mobile applications, live voice/video interactions, advanced Dashboard controls, comprehensive branch-tree navigation, extended usage analytics and deeper multimodal presentation are future candidates, **not V1 prerequisites**. Browser camera attachment and mobile-responsive chat are already V1; they should not be confused with live camera/video streaming.

### 5.6. Future-scope change gate

Future goals remain recorded so omitting them from V1 is **not** a cancellation. However, V1 is complete only against the explicit requirements in divisions 0–4. No future-scope API method, audit storage, speculative DTO, hidden tab, preview scaffold or unused cross-client sync layer may be added “for later” without separate scope approval.

---

> **第三轮适用性：** 下文薄客户端、原生复用与真实交互原则保留；末句固定Astra／视觉AI职责是第二轮历史编排，第三轮按新计划，不由此指定人员／模型。

**Final normative invariant:** *The browser is a thin, reconstructible API client. Hermes/Secretary owns all committed conversation and runtime truth. The Web UI follows the confirmed user interactions exactly; source-grounded native reuse is preferred; exceptional backend changes are minimal and additive; the design system is centralized; GPT-6 Astra is responsible for integration and correctness, and the visual AI is responsible for styling without inventing product behavior.*
