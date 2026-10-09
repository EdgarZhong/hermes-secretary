# Hermes Secretary V1 — Session Notebook / Noting System Implementation Specification

> **Status:** V1 inherited implementation contract, synchronized for V1.5
> **V1.5 precedence:** `04-hermes-secretary-v1.5-implementation-spec.md` is the highest-priority incremental revision for its explicitly changed scope; all unchanged V1 contracts below remain effective.
> **Scope:** Conversation Identity, History Search, Session Notebook, Noting, Notebook Schedule, and Reminder Delivery  
> **Related documents:**
> - `01-personal-hermes-v1-first-fork-iteration.md` — V1 goals, first-fork scope, and project boundary
> - `03-future-roadmap-memory-governance-rsi.md` — post-V1 Memory Governance / RSI roadmap
>
> This document is derived from the frozen Chinese semantic baseline and supersedes earlier Noting drafts, the earlier Noting configuration / Hermes interaction note, and the old Session Notebook implementation note. For unchanged V1 Notebook / Noting contracts, this document remains authoritative; explicit V1.5 revisions take precedence.

---

# 1. Terminology, Conversation Identity, and System Boundary

This specification reuses Hermes semantics wherever Hermes already has the relevant object or lifecycle. Secretary adds only the identity and state that Hermes does not natively provide but V1 Noting requires.

## 1.1 Core terminology

| Term | Meaning in this specification | Relationship to Hermes |
|---|---|---|
| **Session** | A physical execution and persistence scope with its own `session_id`, transcript rows, lifecycle, and runtime ownership. | Native Hermes concept. A Session is not equivalent to a complete user-semantic Conversation. |
| **Conversation** | One semantically continuous main-user conversation path. Ordinary continuation and compression continuation remain in the same Conversation. Branch/fork and reset/new boundaries create a new Conversation. | Hermes already has the relevant boundary behavior, but it does not expose one durable Secretary-owned primary key for the whole logical Conversation. |
| **Conversation Ref** | A Secretary-owned, durable, opaque, stable first-class identity for exactly one Conversation. | Secretary extension. It is independent of physical `session_id`, Gateway routing keys, and Channel identity. |
| **Conversation Locator / Alias** | A Hermes-derived locator that can prove which logical Conversation a physical Session belongs to. | Includes the compression-lineage fallback locator and, when available, the declared `(source, session_key, generation)` conversation identity / declared scope. A locator is not the Conversation Ref. |
| **Turn** | One complete `run_conversation()` execution initiated by one driving message. A Turn may contain several provider calls, tool calls/results, retries, and model iterations. | Native Hermes semantics. A Turn is not one LLM/API call. |
| **Message UID** | Hermes's durable logical-message UID, preserved across relevant persistence and compaction generations. | Native `message_uid`. A bare UID is not globally unique after branch/fork. |
| **Message Identity** | `(conversation_ref, message_uid)`, identifying one logical message in one logical Conversation. | Secretary composition of Conversation Ref and Hermes `message_uid`. |
| **Compression Continuation** | A new physical Session produced by rotating compaction while continuing the same logical Conversation. | Native Hermes compression-lineage behavior. |
| **Branch / Fork** | A new user-semantic Conversation created from an existing path. | Native Hermes boundary. History and `message_uid`s may be copied, but the branch does not share the parent's Conversation Ref. |
| **Active Foreground** | The Conversation context actually used for the current main-model request. | A Secretary view over the live Hermes runtime. |
| **History Foreground** | The authentic readable history of the current Conversation across valid continuation, with compaction scaffolding projected away and rewind/edit-superseded rows excluded. | Secretary view. It is the only source view used by History Search. |
| **Full Foreground** | The Noting provenance/audit view: logical messages plus compaction boundaries/messages and Noting Anchor/Snapshot annotations. | Secretary view used for Noting audit, Anchor resolution, and path validity. It is not the normal History Search view. |
| **Anchor** | The Message Identity to which a Notebook Snapshot is attached. | Not a second identity system. |
| **Notebook** | Structured working state for one Conversation. | Secretary extension. It is neither Session History nor long-term Memory. |
| **Notebook Snapshot** | A complete immutable Notebook state committed after successful Noting. | Secretary extension stored in the existing `state.db`. |
| **Noting Task** | One background, process-lifetime, one-shot Notebook maintenance task. | Secretary policy implemented on top of a persistent Hermes child Session/runtime. |
| **Noting Session** | The physical child Session used by one Noting Task. | Native Hermes Session. |
| **Runtime Profile** | Execution policy for a Noting Task. V1 has exactly `NOTING` and `NOTING_WITH_COMPACTION`. | Secretary extension. |
| **Schedule** | The Notebook-owned, in-Conversation scheduling capability. | Secretary extension. It is distinct from Hermes Cron. |
| **Hermes Cron / Hermes Cron Job** | Hermes's pre-existing scheduled-job subsystem. | Reused only where its schedule parsing / next-run utilities are useful. It is not the persistence or execution model for Notebook Schedule. |
| **System Reminder** | Passive synthetic input that does not start a main Turn; it is pulled into the next eligible main LLM request. | Secretary delivery semantics. |
| **User Reminder** | Active synthetic user input that attempts to re-enter the main Conversation through the existing Hermes ingress/admission path. | Secretary delivery semantics. |

Within this specification, **Schedule always means the Notebook-owned in-Conversation scheduling capability**. Hermes's existing scheduled-job subsystem is always named explicitly as **Hermes Cron** or **Hermes Cron Job**. These terms are not interchangeable.

## 1.2 Conversation / Session relationship

V1 relies on the following relationship already supported by Hermes's current lifecycle model:

```text
Conversation -> physical Session : one-to-many
physical Session -> Conversation : single-valued
```

A Conversation may span multiple physical Sessions because of rotating compression or host/runtime behavior. A given physical Session, however, belongs to only one logical Conversation. Explicit branch, reset/new, delegate/subagent, and tool-child boundaries are not folded back into the parent main Conversation.

This property lets Secretary derive or collect trusted Hermes locators from the current Session and resolve them to one durable Conversation Ref.

## 1.3 Conversation Ref as Secretary's base identity

Conversation Ref is not the compression-lineage root Session ID, and it is not a `gwk_*` declared prompt-cache scope. It is a Secretary-owned durable opaque ID, for example:

```text
conv_<opaque-id>
```

Implementation code must treat it as opaque and must not depend on its string format.

Conversation Ref is the ownership key for all Conversation-scoped Secretary state:

- current Notebook;
- Notebook Snapshots;
- Snapshot Anchors;
- Notebook Schedules;
- pending Reminder delivery;
- Conversation-local Noting enable state;
- Noting admission / same-Anchor deduplication;
- branch/rewind Notebook reconciliation.

These layers must not use `session_id`, `session_key`, transport identity, or Channel identity as their ownership key.

## 1.4 Conversation Identity Registry

Secretary adds a small Conversation Identity Registry to the existing `state.db`. Hermes's current Session identity model remains unchanged.

A conceptual schema is:

```text
secretary_conversations
- conversation_ref PRIMARY KEY
- created_at

secretary_conversation_aliases
- alias_kind
- alias_value
- conversation_ref
- created_at
- UNIQUE(alias_kind, alias_value)
```

Actual table and column names may follow repository conventions; the semantics are fixed.

### Locator A: compression-lineage fallback

When no declared stable session key is available, resolve through Hermes's verified compression lineage:

```text
current physical Session
-> Hermes compression-only lineage
-> lineage root / equivalent stable fallback locator
-> Conversation Identity Registry
```

The lineage walk must keep Hermes's current continuation boundary rules and exclude:

- explicit branch children;
- reset/new children;
- delegate/subagent children;
- tool Sessions.

### Locator B: declared Conversation locator

When the host / Gateway provides a stable session key, use Hermes's existing declared-conversation semantics:

```text
(source, session_key, conversation_generation)
```

`conversation_generation` comes from Hermes's existing durable `conversation_generations` mechanism. Compression does not advance it; a Conversation boundary does. The generation is not reconstructed from prunable Session history and therefore is not reused after old Session rows disappear.

The current `agent/prompt_cache_scope.py` logic — especially `declared_conversation_scope()` / `resolve_prompt_cache_scope()` — demonstrates the intended semantics for keeping one logical Conversation stable while physical Session IDs change. Secretary should reuse or extract that identity logic rather than reimplement Channel identity rules.

### Alias reconciliation

When resolving a Conversation Ref:

1. collect every Conversation locator that Hermes can currently prove;
2. look them up in the Identity Registry;
3. if all are unknown, mint one new Conversation Ref and bind all currently trusted aliases;
4. if one or more are known and every known alias points to the same Conversation Ref, return that Ref and bind newly discovered trusted aliases to it;
5. if trusted aliases already resolve to different Conversation Refs, fail closed. Do not auto-merge them.

A normal upgrade path is therefore:

```text
initial V1:
compression-lineage root S1 -> C1

later, after Channel/session_key support is enabled:
current Session is still provably in C1
and also yields (source, K, generation=7)
-> bind the new declared locator to C1
-> C1 remains unchanged
```

A reset/new boundary on the same Channel produces a new generation:

```text
(source, K, generation=7) -> C1
(source, K, generation=8) -> C2
```

`session_key` alone is never a valid Conversation locator.

## 1.5 Conversation identity and runtime routing are separate

Conversation Ref is ownership identity, not transport routing state.

When a background operation needs to reach the main Conversation runtime:

```text
conversation_ref
-> Identity Registry / trusted Hermes locator
-> current physical Session / SessionEntry
-> existing Hermes routing and admission path
```

At delivery time, the runtime may use the `session_id`, `session_key`, `source`, or other routing fields already held by Hermes. Those values are transient routing locators and do not become Notebook/Schedule ownership fields.

If an old Conversation stores `(session_key, generation=7)` but the Channel currently resolves to generation 8, the old Conversation's Reminder must not be delivered into the new Conversation. When ownership cannot be proven, resolution fails closed.

## 1.6 Message Identity

The canonical message identity is:

```text
Message Identity = (conversation_ref, message_uid)
```

Therefore:

- compression continuation does not change Message Identity;
- in-place compaction does not change Message Identity;
- branch/fork may copy a `message_uid`, but the new Conversation Ref makes the Message Identity different;
- Persistence Candidate provenance, Noting Anchors, and History Search provenance all use this canonical identity.

## 1.7 Goal and source of truth

Session Notebook is the structured **working-state layer** of a Conversation. It keeps important working state stable across long conversations and repeated Compaction, including:

- user commitments;
- user reminders;
- tasks accepted by the Assistant;
- watchpoints;
- decisions;
- open questions;
- developing insights;
- memory/rule/skill candidates awaiting later review.

The raw Hermes Conversation transcript remains the source of truth.

Notebook is asynchronously derived state, not the authoritative control path for the current Turn:

```text
new user intent
├─ immediate path -> main Conversation Foreground -> main Assistant follows it immediately
└─ persistence path -> later Noting -> reconcile it into Notebook
```

The main Assistant does not directly mutate Notebook. A short Noting delay does not mean the user's intent takes effect late.

## 1.8 Non-goals and Hermes-first design

V1 Noting is not:

- a replacement for Session History;
- a replacement for Compaction;
- a Conversation-summary repository;
- long-term Memory or a Knowledge Base;
- an external research agent;
- a replacement for Hermes Cron or a separate general-purpose job scheduler;
- a second transport/API stack;
- a resumable cross-process background workflow engine.

Where Hermes already owns the underlying mechanism, Secretary reuses it:

- physical execution/persistence -> Hermes Session;
- Turn execution -> `run_conversation()`;
- logical message identity -> `message_uid`;
- compression boundaries -> Hermes lineage;
- context usage -> Hermes's existing measurement paths;
- parent compaction -> Hermes native compaction lifecycle;
- Gateway busy/admission -> Hermes existing ingress path;
- time-expression parsing / next-run calculation -> Hermes Cron utilities where reusable;
- History Search -> the existing Secretary History Search capability, not a new Noting-specific implementation.

---

## 1.9 Runtime eligibility and general read tools

Notebook, Noting, Notebook Schedule, and their main-Assistant exposure belong only to a main Conversation that directly communicates with the user. Cron Tasks, Dreaming, Skill refinement, generic subagents/delegates, and other auxiliary/background runtimes do not participate, regardless of global Noting configuration. Their tool lists must never contain notebook_show; ordinary toolset inheritance or an explicit Notebook toolset must not grant it.

The dedicated Noting Runtime in §5 maintains an eligible Parent Conversation under its frozen ownership and narrow dispatch contract. It does not acquire a separate Notebook or enable Noting for its own child Session.

History Search is separate. V1.5 §2.2 and §3 supersede the former read_file-style configurable Main exposure: every eligible user Main receives session_history and the exact independent History Guidance, regardless of templates, toolsets, or Noting switches. Auxiliary runtimes receive no new Main injection and retain their existing lawful tool configuration. The dedicated Noting Worker retains its restricted Parent-history contract.

# 2. Foreground, History Search, and the Notebook Semantic Model

## 2.1 Active Foreground

Active Foreground is the Conversation context actually used for the current main-model request:

```text
root System Prompt
+ current compaction handoff / summary
+ surviving tail
+ live messages
```

When a Noting Task is spawned, it should freeze the Parent's actual live Active Context rather than reconstructing an approximation from storage merely for uniformity.

## 2.2 History Foreground

History Foreground is the authentic readable history of the current Conversation.

It:

- follows only valid continuation within the current Conversation;
- crosses rotating compression lineage;
- includes authentic active messages;
- includes `active=0, compacted=1` authentic source rows archived by compaction;
- excludes `active=0, compacted=0` rows superseded by rewind/undo/edit;
- deduplicates compaction generations according to Hermes logical-message identity;
- projects away the root prompt and compaction scaffold for ordinary history reading/search.

History Foreground is not Active Foreground and is not Full Foreground.

## 2.3 History Search Suite: a Secretary base capability, not a Noting capability

History Search is read-only and independent of Noting. V1.5 §2.2, §2.6 and §3 replace the former configurable Main exposure with mandatory eligible-Main session_history plus independent Stable Guidance. Auxiliary runtimes retain existing lawful tools without new Main injection. Search covers authentic current uncompacted and valid compressed history in the authorized Conversation.

History Search reads **History Foreground only**. Noting must reuse the same capability rather than introducing a second History Search implementation or placing History Search behind the Noting feature gate.

The existing `session_history` tool contract remains valid. V1 keeps at least the following operations.

### Search

```json
{
  "mode": "search",
  "query": "Rule + Reminder",
  "match": "keyword",
  "roles": ["user"],
  "limit": 20
}
```

- `match`: `keyword | regex`;
- no embedding / semantic search;
- optional role filtering;
- search scope is the current Conversation's History Foreground, not one physical Session.

Results expose at least:

```text
message_id
message_identity   # canonical provenance identity when projected by Secretary
message_uid
timestamp
role
content
```

Existing callers may continue to use `message_id`. Whenever a result is stored as durable provenance, Secretary normalizes it to canonical Message Identity.

### Read

```json
{
  "mode": "read",
  "message_id": 18342,
  "before": 2,
  "after": 3,
  "roles": ["user", "assistant"]
}
```

The existing bounded time-range/history read remains available as well.

The tool resolves compression continuation internally. The model does not need to reason about physical Session IDs.

History Search is read-only. It does not access Web, filesystem, Memory/NM, other Conversations, or Full Foreground's Noting/compaction audit annotations.

Both the main Assistant and the Noting Runtime use this same suite.

## 2.4 Full Foreground

V1.5 §1.3 and §2.5 replace the former loose Full audit structure. Full is ordered `[Context Prelude, Message Nodes…]`. The unique first Prelude has no Message Identity and projects the latest effective root System Prompt and Tool Schemas from actual Hermes execution/recovery sources, with source and validity recorded; missing sources are reported honestly. It does not retain a history of every Prompt/Tool version.

Ordinary nodes map one-to-one to `(conversation_ref, message_uid)`, never physical row IDs. The sole exception is a composite Compaction carrier: its Compaction and preserved real-user projections are adjacent nodes sharing the same original identity, distinguished by projection kind. Anchor and immutable Snapshot annotations attach to message nodes and are not new nodes. Full follows the current valid path through Compaction, resume, branch and rewrite; reads do not start Noting, Schedule or Turns. It is not Active request context or the History Search source.

## 2.5 Notebook sections and entry types

The Notebook exposes four semantic sections. Section is derived from `type`; there is no redundant independent section field.

```text
user
├── user_commitment
└── user_reminder

assistant
├── agent_task
└── watchpoint

consultation
├── decision
├── open_question
└── formulating_insight

persistence
├── memory_candidate
├── rule_candidate
└── skill_candidate
```

### `user_commitment`

A commitment explicitly made by the user.

Required fields:

- `what`
- `intent`

Status transitions:

```text
pending -> in_progress -> done
pending/in_progress -> dropped
```

May carry a Schedule. When due, it produces a System Reminder and does not start a Turn.

### `user_reminder`

Something the user explicitly wants the system to remind them about later.

Required field:

- `message`

Status transitions:

```text
active -> delivered
active -> cancelled
```

May carry a Schedule. It is the only Notebook entry type that uses active User Reminder delivery.

### `agent_task`

A task the Assistant has accepted or must continue later.

Required fields:

- `task`
- `purpose`

Status transitions:

```text
pending -> running -> done
pending/running -> failed
pending/running -> dropped
```

May carry a Schedule. There is no separate semantic trigger type; a future prompt to revisit the task uses Schedule. Due delivery is a System Reminder only and never autonomously executes the task.

### `watchpoint`

Something that must remain visible until a future review horizon, then be checked again.

Required fields:

- `subject`
- `what_to_watch`
- `why`
- `until`

Status transitions:

```text
watching -> resolved
watching -> dropped
```

`until` is required and corresponds to a one-shot Schedule. Due delivery is a System Reminder.

### `decision`

Required fields:

- `decision`
- `rationale`

Status transitions:

```text
active -> superseded
active -> revoked
```

No Schedule.

### `open_question`

Required fields:

- `question`
- `why_it_matters`

Optional:

- `needed_information`

Status transitions:

```text
open -> resolved
open -> dropped
```

No Schedule.

### `formulating_insight`

Required fields:

- `insight`
- `basis`

Optional:

- `uncertainty`
- `what_would_confirm`
- `what_would_refute`

Status transitions:

```text
forming -> validated
forming -> rejected
forming -> superseded
```

No Schedule.

### Persistence Candidates

`memory_candidate`, `rule_candidate`, and `skill_candidate` are drafts for later main-Assistant review.

Suggested semantic fields:

```text
memory_candidate
- draft
- why_persist

rule_candidate
- draft_rule
- reason
- scope

skill_candidate
- capability
- workflow_draft
- why_reusable
```

Every candidate carries provenance using one or more canonical Message Identities:

```json
{
  "source_message_identities": [
    {
      "conversation_ref": "conv_...",
      "message_uid": "..."
    }
  ]
}
```

At least one valid source Message Identity is required.

V1.5 §6 and appendices A/C clarify that candidates are leads, not authority; /propose-persistence does not prefetch source text. The Main model retrieves source identities and surrounding/later evidence with session_history, proposes first, then executes only explicitly approved actions. Discussion/revision is not approval. Noting archives candidates only after confirmed execution, rejection or withdrawal, not proposal/approval alone.

Promotion is separate from Noting:

```text
candidate
-> main Assistant review
-> explicit user approval
-> external persistence action
```

The Noting child has no direct long-term Memory/Rule/Skill write permission.

## 2.6 Anchor and Snapshot position

An Anchor is the Message Identity used as the derivation point for one Noting result:

```text
Anchor = (conversation_ref, message_uid)
```

Rules:

- after a Trigger arrives, resolve the current Full Foreground head;
- freeze the Anchor before dispatching the child;
- the Anchor must be an ordinary logical Message;
- a Compaction Message cannot be an Anchor;
- at most one Noting Task may be admitted for the same Anchor;
- Parent messages arriving later do not move a frozen Anchor.

The Noting child also records the Parent's current physical Session for runtime/persistence lineage, but that Session is not the semantic Anchor identity.

## 2.7 Conversation path changes

### Compaction

Compaction does not create a new Conversation. Conversation Ref, Notebook ownership, and existing Message Identities remain attached to the same Conversation. V1 does not introduce a Notebook-level `compression_epoch` object.

### Rewind / Edit

Hermes rewrite semantics remain authoritative:

```text
persist rewrite
-> rebuild Full Foreground
-> reconcile current Notebook pointer
```

The current pointer becomes the latest committed Notebook Snapshot whose Anchor still exists on the current Full Foreground. If none remain valid, the pointer is null.

If Rewind/Edit occurs while a Noting Task is already running:

- do not force-cancel the task;
- let the child finish;
- revalidate the frozen Anchor immediately before commit;
- if the Anchor remains on the current Full Foreground, commit is allowed;
- if the Anchor has left the current path, abandon the result and do not move the pointer.

The child transcript may remain for audit.

### Branch / Fork

Branch/Fork creates a new Conversation Ref.

At the branch point, the new Conversation inherits:

- Full Foreground before the branch point;
- valid Noting Anchors on that path;
- the corresponding immutable Snapshot content;
- the current Notebook state at the branch point.

Inherited Anchors are rebound to branch-local Message Identity:

```text
parent: (conversation_ref_A, message_uid_X)
branch: (conversation_ref_B, message_uid_X)
```

Snapshot payloads may be shared/referenced internally, but payload sharing must not allow mutation to leak across Conversations.

---
# 3. Persistence, Notebook Control, and Schedule Runtime

## 3.1 Persistence principle: additive extension of `state.db` only

Secretary V1 does not modify the columns, primary keys, foreign keys, or existing semantics of Hermes core tables.

Secretary does not repurpose ownership in tables such as:

```text
sessions
messages
conversation_generations
gateway_routing
...
```

All durable Secretary state is added through new Secretary-owned tables in the same profile-scoped `state.db`.

Hermes already has centralized schema creation and schema-version migration. The implementation may bump the schema version and add new tables/indexes/migrations, but it should not add Secretary-specific columns to existing core tables.

Conceptually, V1 needs durable storage for at least:

```text
Conversation Identity Registry
Conversation-local Noting state
current Notebook pointer
immutable Notebook Snapshots
Notebook Schedule runtime state
durable pending Reminder delivery state
Noting admission / same-Anchor dedupe state, as needed
```

The exact table names may follow repository style. The ownership boundary above is part of the design.

## 3.2 Conversation-local Noting state

Conversation-local participation state is persisted by `conversation_ref`, for example:

```text
conversation_ref
noting_enabled
updated_at
```

`/noting on` and `/noting off` only change this local state. They do not duplicate global Noting policy and do not rewrite Hermes global configuration.

## 3.3 Immutable Notebook Snapshot

There is no long-lived mutable master Notebook row that is updated in place.

A successful Noting task follows this shape:

```text
read current Snapshot
-> compute complete next Notebook
-> INSERT immutable Snapshot
-> atomically move current pointer
```

A failed or abandoned task does not create a committed Snapshot and does not move the pointer.

All Conversations use one shared Snapshot table partitioned by `conversation_ref`; V1 does not create a table or file per Conversation.

Each Snapshot stores at least:

```text
snapshot_id
conversation_ref
anchor_message_uid
trigger_type = idle | force
runtime_profile = NOTING | NOTING_WITH_COMPACTION
payload_json        # complete Notebook state, not a diff
created_at
```

The complete Anchor identity is:

```text
(conversation_ref, anchor_message_uid)
```

`payload_json` contains the complete state of the four Notebook sections. Committed Snapshots are insert-only and are not mutated in place.

## 3.4 Current Notebook Pointer

Current state is represented separately:

```text
conversation_ref PRIMARY KEY
current_snapshot_id nullable
```

Snapshot insertion and pointer movement are one atomic transaction.

The Conversation Identity Registry does not store `current_snapshot_id`. Conversation identity and Notebook lifecycle remain separate layers.

## 3.5 Main Assistant Notebook Control

### `notebook_show`

When the runtime belongs to an eligible user-facing main Conversation (§1.9) and global noting.enabled=true, the main Assistant receives the read-only notebook_show capability:

```text
notebook_show
```

It returns the current Snapshot as the complete AI-facing structured JSON. It does not run the human `/notebook` renderer.

The main Assistant may inspect the current Notebook but does not receive Notebook create/edit/status/Schedule mutation tools and never mutates Notebook directly.

Conversation-local Noting on/off never adds or removes this tool, rewrites its schema, or prevents reading the last committed Snapshot. It is absent when global Noting is disabled. Generic auxiliary/background runtimes never receive it, even when global Noting is enabled. This read gate is separate from the effective background Noting gate.

History Search is unaffected by this gate.

## 3.6 Notebook inspection and Noting participation commands

In an eligible user-facing main Conversation with global noting.enabled=true, the following slash forms are available:

```text
/notebook
/noting on
/noting off
```

### Bare `/notebook`

Bare `/notebook` is the human-readable Notebook inspection command.

It:

1. resolves the current `conversation_ref`;
2. reads the current Notebook pointer;
3. if the pointer is non-null, loads that immutable Snapshot;
4. renders the Snapshot in a clear human-readable form;
5. displays the Snapshot's **`created_at` timestamp**.

It does **not** display the Anchor and does **not** display the pointer ID.

If the pointer is null, it returns an explicit “this Conversation has no Notebook Snapshot yet” style result. It does not fabricate an empty Snapshot.

Conversation-local `/noting off` does not disable bare `/notebook`. Therefore, with:

```text
global noting.enabled = true
conversation noting_enabled = false
```

the user can still inspect the most recently committed Snapshot.

The rendered `/notebook` result follows normal Hermes slash/message persistence and later-context behavior:

- no new `display_kind` is introduced;
- there is no special “UI-visible but model-hidden” transcript semantics;
- no new transcript role is introduced;
- the result remains visible to the AI through normal Hermes history/context behavior.

When Noting later sees a Notebook rendering in the transcript, it should treat it as a rendering of already-existing Notebook state rather than as fresh user evidence to duplicate into new entries.

### `/noting on|off`

`/noting on` and `/noting off` only change Conversation-local background Noting participation. They do not delete Snapshots, Schedule intent, or audit history, or change the main tool list, notebook_show read permission, or root System Prompt. They replace the former Notebook participation forms; /notebook remains the inspection command.

## 3.7 Notebook Mutation Control

Notebook mutation is exposed only to the Noting Runtime and uses semantic operations rather than raw JSON replacement or SQL.

The control surface supports at least:

- create / archive / restore;
- semantic field editing;
- legal status transitions;
- Schedule-intent create / update / cancel.

Each mutation returns the resulting complete AI-facing entry/state rather than a bare `OK`, so the Noting model can continue from the real state it just produced.

The model does not write Snapshot tables directly and cannot forge mutable Schedule runtime fields.

## 3.8 Schedule ownership model

Schedule is an adjunct of Noting/Notebook.

Only these Notebook entry types may carry a Schedule:

```text
user_commitment
user_reminder
agent_task
watchpoint
```

`watchpoint.until` corresponds to a one-shot Schedule.

These types have no Schedule:

```text
decision
open_question
formulating_insight
memory_candidate
rule_candidate
skill_candidate
```

Schedule intent belongs to the Notebook entry. Fast-changing operational state is stored separately from immutable Snapshot payloads.

Notebook Schedule does **not** create Hermes Cron Jobs, does not write Hermes Cron `jobs.json`, and does not enter Hermes Cron's isolated agent/script execution path.

V1.5 §5.2 and appendix B require the existing notebook_mutate expression schema to explain all five native time forms and bare-duration recurring versus explicit delayed once behavior; use configured Hermes timezone. No Cron job-control fields are added.

Stable Hermes Cron utilities may be reused for:

- schedule-expression parsing;
- canonical schedule representation;
- timezone handling;
- `compute_next_run()` or equivalent next-run calculation.

## 3.9 ConversationScheduleRegistry

Schedule registration and persistence are owned by a Secretary `ConversationScheduleRegistry`.

A conceptual runtime row contains:

```text
schedule_id
conversation_ref
notebook_entry_id
canonical_schedule
next_run_at
delivery_semantics   # system_reminder | user_reminder
enabled / terminal state
last_fired_at
claim / attempt fields only as needed for idempotent delivery
```

It does not store:

```text
platform
chat_id
thread_id
user_id
scope_id
assistant
character
channel
```

Routing information is resolved only at actual delivery time through Conversation Ref -> Hermes runtime resolution.

Notebook semantic mutation and Schedule runtime state stay synchronized through the Notebook service:

```text
entry schedule created or changed
-> register/update Schedule runtime row

entry completed/cancelled/dropped such that future delivery no longer makes sense
-> cancel/disable Schedule runtime row
```

The model is not responsible for remembering these side effects.

## 3.10 Schedule timer / due scanner

V1 does not build a second full Cron daemon.

Prefer a thin due scan attached to existing Hermes/Gateway periodic housekeeping/ticker infrastructure. If a particular host has no clean reusable seam, use a small Secretary-owned persisted scanner rather than cloning Hermes Cron's execution architecture.

Conceptually:

```text
periodic tick
-> scan Secretary Schedule rows
-> effective_noting_enabled(conversation_ref)?
-> next_run_at <= now ?
-> atomic/idempotent claim
-> dispatch according to delivery_semantics
-> advance or terminalize Schedule state
```

Requirements:

- operational state is durable and scanning resumes after process restart;
- a due occurrence cannot be successfully claimed twice by competing workers;
- delivery failure does not silently discard the occurrence;
- a successful one-shot is terminalized;
- recurring schedules use the shared schedule utility to compute the next run;
- V1 does not introduce a heavy distributed-scheduler abstraction unless Hermes deployment later makes one necessary.

When Conversation-local Noting is off:

- the Schedule row and Notebook intent remain stored;
- the scanner does not fire that Conversation's Schedule;
- `/noting on` makes it eligible again;
- an overdue one-shot is delivered at most once when eligibility returns;
- recurring schedules do not replay an unbounded backlog of missed occurrences; they advance according to the canonical schedule to a reasonable next execution point.

## 3.11 System Reminder delivery path

System Reminder is the passive delivery mechanism used by:

- `user_commitment` due;
- `agent_task` due;
- `watchpoint` due;
- the passive notice created by Force Noting admission;
- busy User Reminder fallback.

A due event or other source only creates a **durable pending System Reminder**. It does not start a Turn.

### Request-time pull

For each eligible main LLM request:

```text
durable Conversation messages
-> Hermes normal repair / request-context construction
-> provider-neutral api_messages
-> select/drain pending System Reminders for this Conversation
-> append standalone synthetic role=user carrier
-> request token/cache accounting
-> existing provider adapter
```

The injection point should be after ordinary transcript repair/merge where practical and before provider-specific adaptation. Provider adapters do not gain Secretary-specific semantic-role logic.

If a Reminder becomes due while one request is already in flight and the same Turn later makes another LLM request after a tool result, that next request may carry it. If the Turn makes no further model call, the first eligible request of the next natural Turn carries it.

### Delivery acknowledgement

Delivery is not acknowledged merely because the Reminder was inserted into a request.

- ACK after a successful provider/model response;
- request failure leaves the Reminder pending;
- a crash after successful response but before ACK may cause redelivery;
- the target is no-loss, at-least-once-safe semantics, not a heavyweight exactly-once protocol.

The carrier format is defined in §5.6.

## 3.12 User Reminder delivery path

A due `user_reminder` is an active invoke.

```text
conversation_ref
-> resolve current physical Session / SessionEntry
-> construct synthetic role=user MessageEvent
-> existing Hermes adapter.handle_message / session ingress
-> existing Hermes admission and busy gate
```

V1 does not add a second main-agent admission gate or a new busy lock around `run_conversation()`.

Reuse the existing Gateway/session admission path, including the semantics represented today by code such as:

- `_is_session_running(...)`;
- `_handle_active_session_busy_message(...)`;
- existing pending/admission handling.

### Main Conversation idle

When existing admission accepts the synthetic input:

```text
synthetic <user-reminder>...</user-reminder>
-> new main Conversation Turn
-> normal durable transcript
```

### Main Conversation busy

A busy User Reminder is **not** queued as a second Reminder Turn to run later.

Add only a narrow Secretary policy at the existing busy gate:

```text
busy synthetic user_reminder
-> convert to durable pending System Reminder
-> current Turn continues
```

The result then follows §3.11 request-time System Reminder delivery.

Do not implement a race-prone pre-check such as:

```text
if not busy:
    start_turn()
```

The real ingress/admission path makes the final busy/idle decision.

The User Reminder carrier format is defined in §5.6.

---

# 4. Noting Enablement, Triggering, and Admission Lifecycle

## 4.1 Global configuration

V1.5 §3.4–§3.5 adds the Main Pre-message Context boundary: read the latest owning-profile global configuration before capturing the active root Prompt and final Tool Schemas. Notebook Guidance, schema and dispatch change together on the next Main Turn, including warm cache and cold resume; local on/off never rebuilds Prompt/tools. Native cache mechanisms are reused, and deliberate global switching may lose prefix cache.

V1 global configuration:

```yaml
noting:
  enabled: true
  idle_delay_seconds: 500

  auto_trigger_compaction_after_noting:
    enabled: false
    threshold_tokens: null

  auto_compact_after_force_noting_idle: false
```

| Field | Meaning |
|---|---|
| `noting.enabled` | Global Noting switch. |
| `noting.idle_delay_seconds` | How long the main Conversation must remain idle after a Turn finishes before an Idle Trigger is produced. Default: 500 seconds. |
| `noting.auto_trigger_compaction_after_noting.enabled` | After an Idle Trigger already exists, whether a user threshold may select `NOTING_WITH_COMPACTION`. |
| `noting.auto_trigger_compaction_after_noting.threshold_tokens` | Idle profile-selection threshold. It is not itself a Trigger. |
| `noting.auto_compact_after_force_noting_idle` | After successful Force Noting, whether a later Idle event may directly request Parent compaction. |

Conversation-local participation is controlled by:

```text
/noting on
/noting off
```

## 4.2 Effective enable state

```text
effective_noting_enabled(conversation)
=
global noting.enabled
AND
conversation-local noting_enabled
```

An eligible user-facing main Conversation participates by default when global Noting is enabled unless the user turns it off with /noting off. Non-eligible auxiliary/background runtimes never participate. This effective gate controls background behavior, not the main Notebook read surface.

Schedule is an adjunct of Noting and is governed by the same effective gate.

## 4.3 Disabled fallback invariant

When effective Noting is false for a Conversation:

- Idle Trigger handling is inert;
- Force Trigger handling is inert;
- Noting admission is inert;
- no Noting child/runtime is created;
- Notebook mutation does not occur;
- Notebook Schedule does not fire;
- no Noting-owned System/User Reminder is created;
- main Notebook reading is governed separately by user-facing main eligibility and global configuration, not this local background gate.

At the same time:

- **History Search remains independent and mandatory for eligible Main under V1.5**;
- the Secretary base timestamp contract remains active even when local Noting is off;
- in an eligible main Conversation with global noting.enabled=true, both /notebook and AI notebook_show can inspect an existing Snapshot;
- `/noting on|off` remains available to change local participation.

Apart from explicitly defined Secretary-wide configuration choices/conflicts, every Hermes execution seam touched by Noting returns directly to Hermes's existing behavior when the effective gate is false. Conversation-local off must not leave behind Noting-specific request assembly, busy admission, compaction, idle-timer, or background-work behavior.

## 4.4 Exactly two Noting Triggers

V1 has exactly:

1. **Idle Trigger**
2. **Force Trigger**

The following are not Noting Triggers:

- `auto_trigger_compaction_after_noting.threshold_tokens`;
- Hermes Auto Compaction;
- Notebook Schedule;
- Reminder delivery.

## 4.5 Idle Trigger

Idle is defined only from main Conversation Turn lifecycle:

```text
main Turn starts
-> main Turn ends
-> record turn_finished_at
-> wait idle_delay_seconds
-> if no new main Turn has started
-> Idle Trigger
```

Only main Turns affect this timer. Noting Turns, delegate/subagent Turns, background utility work, Schedule scanning, pending Reminder state, and side-agent activity do not reset it.

Foreground is consulted only after a Trigger exists, to resolve and freeze the Anchor.

## 4.6 Force Noting threshold

Force does not copy Hermes's Auto Compaction threshold calculator. It consumes two already-resolved Hermes values:

```text
ResolvedContextWindow
HermesResolvedAutoCompactionThreshold
```

Then derives:

```text
AutoCompactionReserve
= ResolvedContextWindow - HermesResolvedAutoCompactionThreshold

ForceNotingReserve
= max(AutoCompactionReserve * 1.20, 66K)

ForceNotingThreshold
= ResolvedContextWindow - ForceNotingReserve
```

The internal invariant is:

```text
ForceNotingThreshold < HermesResolvedAutoCompactionThreshold
```

### Exactly two capability failures

If:

```text
ForceNotingThreshold < 64K
```

Noting cannot be enabled for that configuration. The user-facing guidance is to increase the Context Window.

If:

```text
ForceNotingReserve > 128K
```

Noting cannot be enabled. The guidance is to reduce the Hermes Auto Compaction reserve / move the Hermes threshold later.

`128K` is not a clamp. Force-derived values are not fed back into Hermes threshold calculation.

## 4.7 Force token measurement and trigger wiring

Force reuses Hermes's request-context measurements rather than maintaining a second token counter.

The implementation attaches to the existing pressure/measurement seams corresponding to current code such as:

- `agent/usage_anchor.py::anchored_context_tokens(...)`;
- `agent/turn_context.py::_preflight_request_tokens(...)`;
- `agent/conversation_loop.py::_midturn_request_pressure_tokens(...)`;
- `agent/turn_preflight.py::compress_after_tool_results(...)`;
- the pre-provider-request path.

Conceptually:

```text
Hermes existing context-token measurement
├─ >= ForceNotingThreshold -> attempt Force admission
└─ >= Hermes AutoCompactionThreshold -> Hermes original compaction behavior
```

Force threshold comparison does not call `context_compressor.should_compress(tokens)` as a substitute for its own threshold.

Force Noting is asynchronous/background work. If the Parent reaches Hermes's compaction threshold while Noting is running, Hermes compacts normally without waiting for Noting.

## 4.8 Trigger admission and Anchor freeze

Idle and Force converge on one admission pipeline:

```text
Trigger arrives
-> resolve current Full Foreground head
-> derive and freeze Anchor Message Identity
-> record attempt
-> if head is a Compaction Message: skip
-> same-Anchor dedupe
-> trigger-specific gating / profile selection
-> atomic admission
-> spawn Noting Task
```

Different Anchors may have concurrent Noting Tasks. The same Anchor may have only one successful admission.

V1 does not add a heavyweight “only one Noting Task globally” lock.

## 4.9 Deriving Force Noting success state

V1 does not persist runtime flags such as:

```text
awaiting_compaction
force_noting_completed
compression_epoch
```

Whether Force Noting has already succeeded since the latest Compaction is derived from durable facts:

```text
latest Compaction boundary
+
committed Snapshot with trigger_type=force
+
Snapshot Anchor position
-> Force success state for the current pre-compaction segment
```

The resulting “normally only one successful Force Noting before the next Compaction” behavior is a consequence of these rules, not a separate stored flag.

## 4.10 Runtime Profile selection after Idle Trigger

When Idle fires, read current usage again.

### Usage below Force threshold

```text
auto_trigger_compaction_after_noting.enabled == false
-> NOTING

enabled == true and usage < configured threshold
-> NOTING

enabled == true and usage >= configured threshold
-> NOTING_WITH_COMPACTION
```

The user-defined Idle profile-selection threshold has no required ordering relationship with the Force or Hermes Auto Compaction thresholds.

### Usage at or above Force threshold

If the current pre-compaction segment already has a successful Force Snapshot:

```text
auto_compact_after_force_noting_idle == false
-> do nothing

auto_compact_after_force_noting_idle == true
-> request Parent compaction directly
-> do not spawn another Noting Task
```

If the segment does not yet have a successful Force Snapshot, the ordinary Idle path does not create a substitute ordinary Noting Task; the Force path owns that condition.

## 4.11 Force admission gating

Force admission requires all of:

```text
current measured usage >= ForceNotingThreshold
AND same Anchor has not already been admitted
AND no committed trigger_type=force Snapshot lies after the latest Compaction boundary
```

## 4.12 Relationship to Hermes Compaction

Hermes retains ownership of threshold-based Auto Compaction, including:

- configuration schema;
- per-model thresholds;
- context-window correction;
- reserve calculation;
- safety guards;
- retry/fallback/cooldown;
- in-place versus rotating mode.

Secretary Force only consumes Hermes's resolved result.

### Idle compaction conflict

When Noting is globally enabled and participates in runtime behavior, Hermes idle compaction must be disabled:

```yaml
compression:
  idle_compact_after_seconds: 0
```

Secretary idle lifecycle and Hermes idle compaction are conflicting mechanisms. This is a configuration conflict, not one of the two Force capability failures.

Conversation-local `/noting off` does not dynamically rewrite Hermes global config. It only makes Noting hooks inert for that Conversation.

## 4.13 Force admission Reminder side effect

A successful Force Noting admission also creates an internal passive System Reminder.

That Reminder does not get a separate delivery mechanism; it enters the unified pending System Reminder pipeline in §3.11.

---
# 5. Noting Runtime, Tool Surface, and Message/Timestamp Contract

## 5.1 Noting replaces the old Background Self-Improvement Review product role

Secretary Noting takes over the product-level role previously served by Hermes Background Self-Improvement Review: observing the current Conversation outside the foreground Turn and performing structured maintenance.

In the Secretary fork:

- the old automatic Background Self-Improvement Review no longer runs as an independent product feature;
- if no other upstream dependency needs that independent path, it may be disabled or removed;
- the useful cache-parity machinery from that implementation is retained and generalized.

This is a fork-wide product decision. Conversation-local `/noting off` does not dynamically restore the old Background Review behavior.

## 5.2 Runtime composition

> Pending specification question, not a finalized contract: when Hermes wraps an external Agent runtime that owns the whole Main Turn, the availability and fidelity of the complete Parent request prefix and its cache inheritance are not yet defined. See V1.5 §4.5 D01. The user will re-evaluate this boundary; no fallback, new model route, support exclusion or external-runtime integration is authorized by this note. Existing prefix and dispatch requirements remain in force.

```text
Noting Runtime
=
persistent delegate-style child Session lifecycle
+
cache-parity inherited Parent prefix/runtime
+
thin NotingTaskRunner policy
```

### Reuse delegate-style lifecycle

- independent child `AIAgent`;
- independent child `session_id`;
- dedicated SessionDB handle;
- `parent_session_id`;
- normal child transcript persistence;
- explicit terminal `child.close()`.

### Reuse/generalize cache parity

- Parent `_cached_system_prompt`;
- Parent `session_start` where required;
- `_inherited_cache_scope`;
- necessary cached conversation root;
- the frozen Parent root and message prefix remain in every Noting request;
- the Parent's frozen tool definitions remain unchanged in the inherited prefix; the Noting task and subsequent new system-instruction/control messages append the current permitted tool list and complete schemas, explicitly making that list authoritative;
- actual Noting dispatch is restricted to History Search and Notebook tools, plus `compact_parent` only for the special profile;
- Parent model/provider/reasoning/runtime parity;
- MCP refresh parity/freeze;
- provider-specific fork tag where needed.

## 5.3 Extract a pure cache-parity helper

Do not turn the existing `build_cache_parity_fork()` into a universal constructor with persistence/lifecycle flags.

Extract a helper along the lines of:

```python
apply_cache_parity_from_parent(child, parent, *, fork_tag="noting")
```

Its responsibility is limited to prompt/cache/runtime parity. It does not:

- change `child.session_id`;
- detach `child._session_db`;
- disable persistence;
- rewrite `parent_session_id`;
- own task lifecycle or finalization.

## 5.4 Persistent Noting child, ownership, and one-shot lifecycle

Each Noting Task creates a real durable child Session.

Example:

```text
Parent current physical Session = S17
Anchor = (C42, M42)

Noting child:
session_id = N31
parent_session_id = S17
source/internal marker = noting
trigger_type = idle | force
runtime_profile = ...
```

Do not call `_persist_branch_seed()` and do not copy the Parent transcript into the child.

An active child is strongly owned for the lifetime of the process by a dedicated registry, for example:

```python
_active_noting_tasks[noting_session_id] = runner
```

This prevents normal Gateway soft eviction/LRU behavior from discarding an in-flight Noting child as though it were an ordinary detached child.

On process crash/restart:

- never resume the Noting Task;
- do not reconstruct it;
- do not create a recovery manifest for it;
- an incomplete task does not commit a Notebook Snapshot;
- any already-persisted child transcript remains audit-only.

## 5.5 Runtime prefix and durable suffix

The model-facing context has this shape:

```text
Parent inherited root System Prompt / frozen message prefix
Parent frozen tool definitions / schemas (unchanged)
Parent frozen Active Foreground through Anchor
------------------------------------------------
Noting task transition/control message: authoritative Noting tool list + complete schemas
Subsequent new system-instruction/control messages: repeat the authoritative list + schemas
Noting assistant/tool/continuation suffix
```

Every request in the same task, including tool-loop iterations and continuation Turns, retains the same complete frozen Parent prefix, including root, tool definitions and Active messages through Anchor, and appends only the Noting-owned suffix. Later Parent activity never refreshes that snapshot. Do not rewrite the inherited top-level tools/schema or root to implement the task's tool transition. The task and subsequent new system-instruction/control messages carry the permitted list and full schemas and state that they supersede the Parent's earlier tool-availability instructions. These instructions use the existing Hermes control-message mechanism (§5.6); they do not introduce a new root prompt or redesign provider roles.

This is a Hermes intermediate-layer context reuse contract. Model inheritance, API/provider resolution, serialization and inference use Hermes native mechanisms; do not introduce a Secretary-specific model route, provider adapter or App Server task executor for this requirement.

Only the Noting-owned suffix is persisted to the child Session. The inherited Parent prefix is not copied into the Noting transcript.

## 5.6 Unified message wrappers and timestamp contract

Secretary V1 does not introduce a new mid-conversation semantic role.

All three Secretary synthetic control/reminder carriers use:

```text
role = user
```

Their meaning comes from a complete XML-like wrapper. V1 does not add `_secretary_kind`, a special `display_kind`, or a new provider role for these carriers.

### Real user-message timestamp

Every genuine user input exposed to the model begins with one timestamp marker line, without wrapping the whole user message:

```xml
<timestamp>2026-10-07T21:34:18+08:00</timestamp>
Actual user content...
```

The timestamp:

- is exact ISO 8601 with a UTC offset;
- is visible to the model;
- may be stripped/hidden by normal UI presentation;
- is preserved in durable content so history/replay can recover it;
- should reuse Hermes's existing message timestamp source rather than create a second clock/source of truth.

### Noting Task transition/control message

The first Noting-owned durable transcript row is:

```json
{
  "role": "user",
  "content": "<noting-task>\n<timestamp>...</timestamp>\n...task instruction...\n</noting-task>"
}
```

The opening and closing tags are both present, and the timestamp is the first line inside the wrapper.

There is no Secretary `role=system` Noting transition row and no second root System Prompt. The inherited Parent root prompt remains the root prompt.

### System Reminder

System Reminder is a request-only synthetic carrier:

```json
{
  "role": "user",
  "content": "<system-reminder>\n<timestamp>...</timestamp>\n...reminder content...\n</system-reminder>"
}
```

The timestamp is the first line inside the wrapper.

The carrier itself is not persisted as an ordinary durable main-Conversation transcript row. The durable source is Secretary pending Reminder state. Delivery/retry preserves the original source-event timestamp rather than minting a new timestamp on every attempt.

### User Reminder

User Reminder is an active synthetic conversational input:

```json
{
  "role": "user",
  "content": "<user-reminder>\n<timestamp>...</timestamp>\n...reminder content...\n</user-reminder>"
}
```

The timestamp is the first line inside the wrapper.

When idle admission succeeds, the User Reminder becomes a normal durable user row in the main Conversation. When the main Conversation is busy, it is not first persisted as a future User Reminder Turn; the busy gate converts it into pending System Reminder delivery instead.

Retry or route resolution does not change the original Reminder timestamp.

### Timestamp source semantics

The timestamp represents the **source occurrence time** of the real or synthetic message:

- real user message -> user-message arrival/persistence time;
- Noting Task -> Noting transition/admission creation time;
- scheduled Reminder -> due/fire event time;
- Force internal Reminder -> Force admission event time.

Replay, retry, and request-time injection do not regenerate the source timestamp.

## 5.7 Tool surface

### Main Conversation

The main Conversation always has:

- History Search suite.

When Main eligibility is proven and global noting.enabled=true, it additionally has (independent of the local background switch):

- `notebook_show`, read-only, returning the complete AI-facing Notebook JSON.

The main Assistant never receives Notebook mutation tools.

### Noting Runtime

Both profiles may use:

**Read**
- current Notebook read/show;
- the existing History Search suite.

**Write**
- semantic Notebook create/edit/archive/restore/status/Schedule-intent mutation.

The Noting Runtime does not have access to:

- filesystem;
- terminal;
- Web/browser;
- Memory/NM;
- Skills persistence;
- raw Hermes Cron control;
- delegation;
- messaging;
- connectors/external data.

`NOTING_WITH_COMPACTION` additionally exposes:

- `compact_parent`.

From the `<noting-task>` transition, the current permitted list and complete schemas are appended in task/control instructions, and repeated in subsequent new system-instruction/control messages, with an explicit instruction to use this list as authoritative. They permit only History Search/Notebook and special-profile `compact_parent`. The inherited Parent root, tool definitions and message prefix remain unchanged throughout the task; do not replace the top-level tools/schema to express the transition. Actual dispatch independently enforces the Noting whitelist, including rejection of forbidden Parent tools. Reuse Hermes native model/API/provider mechanisms without deeper routing changes. Observe cache reuse through Hermes request/response evidence; do not redesign the provider cache.

## 5.8 Runtime Profiles

### `NOTING`

```text
continuation = false
terminal_action = null
```

Behavior:

- exactly one complete Turn;
- child auto-compaction disabled;
- after Notebook work completes, run the commit gate;
- commit the Snapshot;
- close the child.

### `NOTING_WITH_COMPACTION`

```text
continuation = true
terminal_action = parent_compaction_admitted_or_already_done
```

Behavior:

- the same child may execute multiple complete Turns;
- child auto-compaction remains disabled;
- after each Turn, check the terminal action;
- if unsatisfied, the runtime injects a mandatory continuation driving message;
- continuation is bounded;
- reaching the explicit terminal-failure boundary ends the task without committing an incomplete result.

Generic delegate behavior remains one-Turn. V1 does not change generic delegate semantics merely to support this special profile.

## 5.9 `compact_parent`

`compact_parent` does not wait synchronously for the Parent's complete compaction lifecycle to finish.

Its contract is:

> The Parent either no longer requires compaction at the relevant threshold, or a compaction request has been successfully admitted into the native Hermes compaction lifecycle.

Conceptually:

```text
re-read Parent usage
-> already below relevant threshold? SUCCESS
-> otherwise request native compaction
-> compressed / pending / already in-flight / admitted? SUCCESS
-> still required and not admitted? FAILURE
```

It reuses Hermes native compaction routing, locks, fences, retries, fallback, late-ack handling, and in-place-versus-rotating semantics.

The special-profile commit order is:

```text
Notebook work
-> compact_parent SUCCESS
-> commit-time Anchor validity check
-> commit immutable Snapshot
-> close task
```

Notebook commit does not wait for ultimate compaction completion. If Hermes later retries, falls back, or ultimately fails that compaction, an already valid committed Notebook Snapshot is not rolled back.

## 5.10 Parent concurrent activity and commit gate

After admission, Noting is decoupled from later Parent foreground activity:

- the Parent may continue receiving Turns;
- the Parent may Auto Compact independently;
- renewed Parent activity does not cancel Noting;
- the Noting child continues against its frozen Prefix and Anchor.

The final safety gate is Anchor validity:

```text
frozen Anchor still belongs to current Full Foreground
-> commit allowed

Anchor no longer belongs to current path
-> abandon result
```

## 5.11 Prompt-cache divergence

Every same-model Noting request retains the complete frozen Parent prefix, including root, tool definitions and messages through Anchor, to reuse the Parent's available cache. The authoritative Noting tool list and schemas are appended only in the child-owned task/control suffix. Secretary must guarantee this prefix reuse at the Hermes intermediate layer; native Hermes model/API/provider behavior is reused without additional routing or caching layers.

On server-slot-style cache routes, later Noting suffix divergence may reuse the Background Review fork-tag pattern so the divergent child stream does not evict the Parent's cache slot.

The design target is:

1. every tool-loop and continuation request retains the same complete frozen Parent prefix, including tools/schema;
2. task and subsequent new system-instruction/control messages repeat the authoritative permitted list and full schemas; actual dispatch remains restricted from task start;
3. available Parent/task cache reuse is measured from Hermes actual provider requests/responses, not inferred from shared bytes;
4. later Noting traffic does not gratuitously rebuild the Parent context or overwrite its cache scope.

The exact provider-specific tag string is an implementation detail.

---

# 6. Hermes Integration Wiring, Acceptance, and Open Frontend/API Work

This chapter is the implementation backstop. Mechanisms already defined in the functional chapters are not redesigned here, but every agreed Hermes integration seam that is easy to omit during implementation is called out explicitly.

## 6.1 Additive persistence wiring

- all durable Secretary state lives in the existing profile-scoped `state.db`;
- add only Secretary-owned tables/indexes/migrations;
- do not add Secretary columns to `sessions`, `messages`, `conversation_generations`, `gateway_routing`, or other core tables;
- follow Hermes's existing DB connection and transaction discipline;
- Snapshot INSERT and current-pointer movement are one transaction;
- same-Anchor admission uses a DB-backed unique/atomic admission mechanism rather than only a process-local check;
- Schedule due claims and Reminder delivery/ACK state are durable so restart does not lose them.

## 6.2 Conversation Identity wiring

Prefer reuse/extraction of current Hermes mechanisms including:

- `SessionDB.get_compression_lineage(session_id)`;
- compression-continuation and explicit-fork detection;
- `conversation_generations`;
- the `(source, session_key, generation)` semantics in `agent/prompt_cache_scope.py::declared_conversation_scope(...)`;
- the branch/reset isolation already encoded by `resolve_prompt_cache_scope()` and related helpers.

Secretary adds a separate `resolve_conversation_ref(...)` layer. The prompt-cache scope string itself is not used as the durable Conversation Ref.

When Channel/session-key support is introduced later, the newly available locator is attached as an alias to the existing Conversation Ref. Existing Notebook/Snapshot/Schedule ownership is not migrated to a different key.

## 6.3 Runtime route-resolution wiring

When a background action must reach a Conversation:

1. resolve trusted locators from `conversation_ref` through the Identity Registry;
2. for compression lineage, resolve the current Hermes tip through `SessionDB.get_compression_tip()` or its current equivalent;
3. for Gateway runtime, use existing SessionStore lookup / route healing;
4. verify that any declared generation still belongs to the target Conversation;
5. if route ownership cannot be proven, fail closed.

Current mechanisms that can be reused include equivalents of:

- `SessionStore.lookup_by_session_id()`;
- `SessionStore.lookup_by_session_key()`;
- compression-tip-aware route healing;
- compression-tip ownership checks already used by heartbeat acceptance.

## 6.4 History Search wiring

V1.5 §2.2 and §3 supersede configurable Main exposure: the existing registry/schema/handler is reused, but every eligible Main must receive session_history and its independent Guidance. It is not gated by Noting. Auxiliary Agents receive no new Main injection and retain existing lawful configuration; the Noting child reuses its restricted Parent-history path.

It continues to:

- read History Foreground;
- search current uncompacted history and valid compression continuation;
- exclude rewind/edit-superseded rows;
- preserve the existing `session_history search/read` contract;
- normalize an old `message_id` result to canonical Message Identity when durable provenance is needed.

The Noting child simply reuses this capability.

## 6.5 User timestamp wiring

Prefer Hermes's existing message timestamp support, including current mechanisms such as:

- `agent.message_metadata::stamp_message_timestamp`;
- Gateway/history timestamp projection.

The goal is not to add another DB timestamp column. The model-visible content uses the §5.6 marker while normal UI presentation may avoid showing that marker redundantly.

Conversation-local Noting off does not disable the real-user-message timestamp contract.

## 6.6 Noting Trigger / Turn-lifecycle wiring

Idle timing attaches to main Turn start/end boundaries, not generic background activity.

Force attaches to Hermes's existing request-context measurement seams. The new hooks return immediately when Noting is effectively disabled.

Conceptually, every Noting-specific hook at a shared Hermes seam follows:

```text
if not effective_noting_enabled(conversation_ref):
    return existing Hermes behavior unchanged
```

Force/Idle integration does not take ownership of the global agent loop.

## 6.7 Cache-parity child wiring

Extract the pure cache-parity helper from the old Background Review path. Construct the durable Noting child through delegate-style lifecycle code.

The Noting child has:

- dedicated DB handle;
- independent `session_id`;
- `parent_session_id` pointing to the Parent physical Session at spawn time;
- no Parent transcript seed;
- first child-owned durable row = `role=user` `<noting-task>...`;
- strong ownership in the active-Noting registry;
- no restart resume.

## 6.8 System Reminder request-injection wiring

System Reminder injection happens at the provider-neutral request-construction layer:

```text
Hermes durable history
-> normal transcript repair/context construction
-> pending Reminder pull
-> synthetic role=user carrier
-> request accounting
-> existing provider adapter
```

Do not teach OpenAI/Responses/Anthropic or other provider adapters new Secretary semantic roles.

If a provider later merges adjacent user rows, that is acceptable as long as the wrapper content remains intact.

Reminder ACK is tied to successful provider/model response, not to request assembly.

## 6.9 User Reminder Gateway wiring

Active User Reminder delivery does not use the Hermes Cron execution path and does not create an isolated `cron_<job>_<timestamp>` Session.

Reuse Hermes's existing synthetic/internal ingress behavior, including current patterns such as:

- `gateway/wake.py::deliver_wake()`;
- heartbeat / synthetic `MessageEvent` delivery;
- `adapter.handle_message()`;
- `gateway/run_busy.py::_handle_active_session_busy_message(...)`.

Only the existing busy gate receives the narrow policy “Secretary User Reminder while busy -> pending System Reminder.”

Do not add a second main-agent busy/admission gate.

## 6.10 Schedule scanner wiring

The ConversationScheduleRegistry timer reuses Hermes/Gateway periodic process infrastructure where practical. Notebook Schedule is not registered in the Hermes Cron Registry.

The scanner is:

- backed by durable `state.db` state;
- resumed on startup;
- skipped for effective-disabled Conversations;
- atomically claimed per due occurrence;
- allowed to reuse Hermes Cron parsing/next-run utilities;
- connected to §3.11 or §3.12 according to delivery semantics;
- reconciled with Notebook intent/status by the Notebook service.

## 6.11 Rewind/Edit/Branch wiring

Secretary reconciliation happens after Hermes successfully performs its own mutation:

- Rewind/Edit: rebuild Full Foreground, then reconcile the current Notebook pointer;
- an in-flight Noting Task is not cancelled; its Anchor is revalidated at commit;
- Branch: mint a new Conversation Ref, inherit the branch-point Notebook state/valid Snapshot history, and rebind inherited Anchors to branch-local Message Identity;
- Secretary hooks do not alter Hermes's native rewrite/branch semantics.

## 6.12 Noting-disabled / Hermes-native acceptance

Test at least:

```text
global noting.enabled = true
conversation /noting off
```

Expected behavior:

- Eligible Main History Search remains present with its independent Guidance regardless of Noting;
- bare `/notebook` can still read the latest Snapshot;
- main Assistant notebook_show remains present and can read the latest committed Snapshot;
- Noting Trigger / child / Schedule / Reminder behavior is inert;
- request, compaction, and admission paths show no Noting-specific behavior beyond Secretary-wide base capabilities.

Also test global noting.enabled=false: all Noting-specific runtime hooks are no-ops and the main Notebook read tool is absent. With either global value, Cron, Dreaming, Skill-refinement, and generic subagent runtimes have no notebook_show and do not start Noting. The dedicated Noting Runtime retains only its explicit Parent maintenance contract.

## 6.13 Identity / persistence acceptance

Cover at least:

- Conversation Ref remains stable across rotating compression;
- Conversation Ref remains stable across in-place compaction;
- branch/reset/new receives a new Conversation Ref;
- one physical Session never resolves to two Conversations;
- fallback locator first creates C1;
- later enabling a session_key/Channel locator still binds to C1;
- generation change creates a new Conversation;
- alias conflict fails closed;
- Notebook/Snapshot/Schedule ownership uses Conversation Ref only;
- Snapshot is immutable;
- pointer movement is atomic;
- failed/incomplete Noting does not move the pointer.

## 6.14 Foreground / History Search acceptance

- Active, History, and Full Foreground are not conflated;
- History Search remains available with Noting off;
- History Search crosses compression continuation;
- rewind/edit-superseded rows are excluded;
- Full Foreground can audit compaction boundary + Anchor + Snapshot;
- a historical `/notebook` rendering is not treated by Noting as new user evidence.

## 6.15 Trigger / Force / race acceptance

- only main Turns reset Idle;
- Force formula matches the specification exactly;
- there are exactly two Force capability failures;
- token measurement reuses Hermes;
- under valid configuration the Force threshold is earlier than Hermes Auto Compaction threshold;
- two attempts on the same Anchor admit only one task;
- different Anchors may run concurrently;
- Force success state is derived from Snapshot + Compaction boundary rather than a stored flag.

## 6.16 Runtime / tool-isolation acceptance

- the child is a persistent Hermes Session;
- Parent prefix is not copied into the child transcript;
- the first child-owned row is `role=user` `<noting-task>`;
- child transcript is auditable;
- process crash does not resume the task;
- incomplete task does not commit;
- the task and subsequent new system-instruction/control messages append the complete authoritative History Search/Notebook tool list and schemas, plus special-profile `compact_parent`; dispatch denies filesystem/Web/Memory/Skills/delegation tools;
- every tool-loop and continuation request retains the same complete frozen Parent root/tools/message prefix; no tool transition rewrites its head; actual cache-read counters are recorded from Hermes/provider responses;
- model inheritance and API/provider execution reuse native Hermes; no Secretary-specific model route or App Server executor is added;
- the main Assistant never mutates Notebook;
- Special-profile continuation always reuses the same child;
- child auto-compaction is disabled.

## 6.17 Schedule / Reminder / timestamp acceptance

- due `user_commitment`, `agent_task`, and `watchpoint` do not start a Turn;
- idle `user_reminder` can start a new Turn through existing admission;
- busy `user_reminder` becomes pending System Reminder rather than a second queued Turn;
- pending System Reminder enters the next eligible main LLM request;
- a failed provider request does not lose the Reminder;
- restart does not lose pending delivery;
- Schedule off/on does not delete Schedule intent;
- real user message uses a standalone `<timestamp>...</timestamp>` prefix line;
- `<noting-task>`, `<system-reminder>`, and `<user-reminder>` place the timestamp as the first line inside the wrapper;
- all three synthetic carriers use `role=user`;
- there is no Secretary mid-conversation `role=system` carrier;
- retry/replay does not rewrite the source occurrence timestamp.

## 6.18 `/notebook` acceptance

- `/noting on|off` persists Conversation-local participation correctly;
- local off still allows bare `/notebook` to read an existing Snapshot;
- a null pointer produces an explicit no-Snapshot result;
- the human view displays Snapshot `created_at`;
- it does not display Anchor;
- it does not display the pointer ID;
- it does not introduce a new `display_kind`;
- it follows normal Hermes persistence/context behavior;
- AI notebook_show returns complete structured JSON rather than the human renderer;
- local Noting on/off preserves the complete main tool-schema bytes and read access, including after cold reconstruction;
- non-user-facing auxiliary runtimes never receive notebook_show, including through composite/inherited toolsets;
- Eligible Main receives History Search independently of read configuration/templates and Noting; authentic current and cross-Compaction history remains searchable.

## 6.19 Open issue: additive Frontend / API contract

Core V1 implementation does not depend on designing a new API hierarchy first.

Frontend/API remains open under this principle:

```text
inspect official Hermes Gateway / tui_gateway / shared contracts
-> identify real Notebook/Noting UI gaps
-> add the minimum RPC/event/DTO extensions
```

Likely areas include:

- current Notebook projection;
- Snapshot/audit history;
- Noting activity/status;
- Full Foreground audit;
- config/status presentation.

Method names, event names, and DTO schemas are intentionally not frozen in this iteration and do not block the first Noting implementation.

---

# Final implementation invariants

```text
Hermes Conversation transcript is the source of truth.

Secretary Conversation Ref is the stable ownership identity.
Hermes Session / lineage / declared scopes are locators, not ownership IDs.

History Search is a general first-class read-only capability over authorized History Foreground.
Eligible Main exposure is mandatory independently of templates/configuration and Noting under V1.5; auxiliary runtimes retain existing lawful tools without new Main injection.
It searches current uncompacted and valid compressed history.

Notebook is one eligible user-facing main Conversation's derived working state.
Generic auxiliary/background runtimes never acquire Notebook or Noting.
Each successful Noting commits a complete immutable Snapshot.

Noting is gated by global config AND Conversation-local state.
Schedule is an adjunct of Noting/Notebook and is inert when Noting is effectively off.

Eligible main Assistant Notebook reading is gated only by global configuration,
independently of Conversation-local background Noting participation.
The main Assistant never mutates Notebook directly.
User intent takes effect immediately through the Conversation foreground;
Noting later reconciles that intent into Notebook.

Noting Runtime = persistent Hermes child Session
+ Parent cache-parity prefix
+ History Search
+ Notebook-only writes.

Secretary synthetic control/reminder messages use role=user + explicit wrappers.
No new mid-conversation provider role is introduced.

V1 does not create:
- a second Memory system,
- a second Conversation transcript store,
- a second Cron job system,
- a second main-agent admission gate,
- or a parallel API hierarchy.
```
