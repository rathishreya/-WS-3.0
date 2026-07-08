# WS 3.0 — Product Requirements (PRD / BRS)

**Audience:** Joy, Bhavya, product & engineering. **Companions:** [`architecture.md`](./architecture.md) (how it's built) · [`05-zero-cut-design.md`](./05-zero-cut-design.md) (field-level design). This document is the **product requirements**: what the product does, every workflow with its **base case and edge cases**, the business rules, and testable acceptance criteria.

> **Product in one line:** WS 3.0 is a generic, multi-tenant platform that takes an organization from **onboarding through to delivering an assignment** — composing the plan with AI and asking a human to ratify twice. EZ is the first tenant, configured through the same product as everyone else.

**Conventions**
- **FR-x.y** = a functional requirement (testable). **MUST / SHOULD** carry their usual force.
- **Base case** = the happy path. **Edge cases** = every branch, failure, and exception the product must handle.
- `(EZ: …)` = illustrative config only — never product behaviour. `[J]` = awaiting Joy. **⚠️ Bhavya** = architecture-owned.
- **AC** = acceptance criteria.

**Reading order:** §1 goals → §2 personas → §3 product surfaces (what it looks like) → §4 domain model → **§5 the 15 workflow epics (base + edge cases)** → §6 cross-cutting → §7 non-functional → §8 phasing → §9 open items → §10 glossary.

---

## 1. Product goals & non-goals

### 1.1 Goals
- **G1** One organization can go from *nothing* to *delivering work* on bare-minimum information, with the product filling the rest just-in-time.
- **G2** The whole delivery lifecycle runs with **exactly two human touchpoints** (ratify the plan, confirm the verify); everything else is AI-composed or system-derived.
- **G3** The product is **generic** — a translation agency, a design studio, and a research firm each run on it unchanged. Every organization-specific value is config.
- **G4** Multiple legal entities within one org, and work *across* organizations, are first-class — with confidentiality guaranteed by construction.
- **G5** All commercial/financial operations (invoicing, wallet, payout, payroll) are absorbed and **improved**, never ported as-is; no shadow spreadsheets, no sync jobs, no drift.

### 1.2 Non-goals (this release)
- Not a commercial/pricing marketplace or live-market product (parked — option value).
- Not a general no-code scripting canvas — configuration is declarative + defaulted + archetype-seeded, not a programming surface.
- Not a content store — the product holds the *graph* of work and file *pointers*, never raw content as system of record.

### 1.3 Success metrics
- Time-to-first-delivery for a new workspace (onboarding → first verified assignment).
- Human touchpoints per assignment (target: 2).
- % of plan composed by AI and accepted without edit.
- Reporting accuracy (target: zero state/status drift — structurally, not by cleanup).

---

## 2. Personas & actors

| Actor | Level | What they do | Primary surface |
|---|---|---|---|
| **Platform Operator** | L0 | Provisions workspaces, sets tier + module availability, assigns the admin. No access to tenant content. | Operator console |
| **Workspace Admin** | L1 | Configures the whole operating model declaratively; ratifies AI-seeded config. | Admin/Setup console |
| **Module Admin** (optional) | L1 | Delegated admin for one module or one entity (can be entity-scoped/blinded). | Admin console (scoped) |
| **Owner** | L2 | Ratifies the AI plan for a request; signs off at the trust boundary. | Work console |
| **Performer** | L2 | Accepts an activity and produces the output. May be a human, an AI agent, or a human+tool. | One-tap channel (chat/WhatsApp/SMS); app optional |
| **Reviewer** | L2 | Passes/fails an activity where QA policy requires a human. | Work console |
| **Verifier** | L2 | One-tap confirms the reconciliation — the billing gate. | Work console |
| **Requester** | external/L2 | Submits brief + files + deadline; receives status + deliverable. | Any channel (form/email/client tool) |

**Roles are product primitives; their names are config.** (EZ maps owner/performer/reviewer/verifier onto SWAT/QA/SME/pool — a relabel, not new behaviour.)

---

## 3. What the product looks like (surfaces / IA)

The product is a set of **role-scoped surfaces** over one work graph. Each surface shows only what the actor's role and `(workspace_id, operating_entity_id)` scope permit (POV-scoping).

1. **Operator Console (L0)** — workspace list, provisioning wizard, tier/module toggles, oversight dashboards. No tenant content.
2. **Setup / Admin Console (L1)** — the **readiness dashboard** ("you can deliver once these are set"), config editors (entities, catalog, skills, pricing, teams/roles, policies, channels, modules), archetype picker, people directory, relationships (clients/vendors).
3. **Work Console (L2)** — request inbox, the **plan-ratification screen** (the AI draft, editable inline), the live work tree (parallel branches, status roll-up), the **verify screen** (pre-computed reconciliation, one-tap confirm), delivery view.
4. **Performer surface** — primarily **channel-native**: a chat/WhatsApp/SMS message with a one-tap Accept and an output upload. The full app is optional; most performers never open it.
5. **Requester surface** — submit a request (or it's auto-created from email/tool), a status roll-up, the delivered output, and approve-if-required.
6. **Money surfaces** — invoicing (if billing on), wallet/credits (if prepaid), payout (if paying through WS) — each appears **only** when its capability is turned on.

**Ambient AI, not a chatbot panel:** AI appears *inline* as suggestions the human approves (compose the plan, propose the performer, pre-compute the reconciliation), never as a separate assistant to converse with.

---

## 4. Domain model (recap)

- **Party + Relationship.** A Party (Org/Person) with typed Relationship edges (`employment / client / vendor / tenant`). Tenant/client/vendor are relationship *types*, not separate systems. A cross-org link is one edge, "vendor" from one side and "client" from the other.
- **Work graph (BAT).** `Request` → `Assignment` (one offering; Deliver is the mandatory last activity) → `Activity` (input(s) → one performer → one skill → output(s)). A Request is a **tree**: independent branches run in parallel, dependent ones gate on their input.
- **Config axes.** `delivery_model` ∈ {deliverable, retainer, outcome} × `billing_model` ∈ {unit×price, flat_retainer, retainer+usage, outcome}.
- **Two isolation keys.** `workspace_id` (crypto) · `operating_entity_id` (policy).

*Field-level detail for every record is in [`05-zero-cut-design.md`](./05-zero-cut-design.md); the schema is in [`architecture.md`](./architecture.md) §4.*

---

## 5. The workflows — functional requirements, base cases & edge cases

Fifteen epics. Each: **base-case flow → business rules → edge cases → FRs → acceptance criteria.**

---

### E1 · Workspace provisioning (L0)

**Base case**
1. Operator opens the provisioning wizard.
2. Enters **org name · deployment tier · admin email** (3 fields).
3. If tier = regional/sovereign, sets BYOK keys.
4. System creates the workspace, sets module availability, invites the admin.
5. Admin receives an invite → lands on the Setup home.

**Business rules**
- Provisioning MUST NOT ask for anything beyond the 3 fields (+ keys if sovereign). Everything else is deferred to config/JIT.
- EZ is provisioned through this same wizard — **no back-door** (FR-1.5).

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Duplicate `org_code`/name | Reject with a clear conflict; suggest an available code. |
| Sovereign tier chosen but no BYOK keys provided | Block activation until keys are set; workspace stays in `provisioning`. |
| Admin invite email bounces | Operator sees a delivery-failure flag; can re-issue to a corrected address. |
| Operator tries to view tenant content | Denied — L0 has provisioning/oversight scope only, never content. |

**FRs** — FR-1.1 3-field provisioning · FR-1.2 tier drives isolation (shared/regional/sovereign) · FR-1.3 BYOK required before a sovereign workspace activates · FR-1.4 module availability set at provisioning, tunable later · FR-1.5 **no back-door**: every tenant incl. EZ onboards via this flow.

**AC** — A workspace is created with ≤3 inputs; a sovereign workspace cannot reach `active` without BYOK; the operator can never open a tenant's briefs/deliverables.

---

### E2 · Workspace configuration & readiness (L1)

**Base case**
1. Admin picks an **industry archetype** (translation / creative / research / generic).
2. AI builds a **starter workspace**: catalog + capabilities, common skills, default roles, SLA + pricing bands, notification defaults.
3. The **readiness dashboard** shows "you can deliver once these are set" and lists only the gaps.
4. Admin **ratifies** each seeded item (entities, teams/roles, catalog, skills+pricing), edits as needed.
5. Admin sets up the first client relationship and activates the modules needed (Delivery always; others as required).
6. When the minimum chain is satisfied, the workspace flips to **Operational**.

**Business rules**
- The admin **edits AI proposals; never authors from a blank form** (FR-2.2).
- "Onboarded = can deliver" — readiness is defined as the minimum chain: `entity · offering + skills + Delivery-skill · team · people · client/requester` (+ `pricing/wallet` **only if billing on**).
- Only fields a **turned-on capability** needs are asked; the rest surface JIT at first use (FR-2.4).
- Archetypes carry **generic industry knowledge only** — never EZ's proprietary templates (FR-2.6).

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Admin picks "Generic" archetype | Near-empty starter; admin authors more manually; product still works. |
| Readiness never satisfied (a gap left open) | Workspace stays `configuring`; cannot publish a request; dashboard shows exactly what's missing. |
| Billing turned off | Pricing/wallet/tax fields are **not** asked; readiness ignores them. |
| Activity-template dependency forms a cycle | Config validation rejects the catalog until the cycle is broken. |
| Currency/tax missing while billing on | Readiness flags it as a blocking gap. |
| Admin edits a seeded offering after go-live | Catalog is **versioned**; in-flight work keeps its snapshot; new work uses the new version. |

**FRs** — FR-2.1 archetype seeds a full starter · FR-2.2 ratify-not-author · FR-2.3 readiness engine computes gaps live · FR-2.4 capability-gated + JIT fields · FR-2.5 workspace flips Operational only when the min chain is met · FR-2.6 archetypes generic · FR-2.7 catalog versioned; in-flight work uses its snapshot · FR-2.8 everything declarative — no hardcoded org rules.

**AC** — A fresh workspace reaches Operational without ever seeing a field its capabilities don't need; disabling billing removes all money fields; editing the catalog never mutates in-flight assignments.

---

### E3 · People & identity (L1 → self-onboard)

**Base case**
1. Admin bulk-invites / connects a directory (SSO-ready).
2. Per person, AI pre-fills the profile from their portable identity/history.
3. Person **ratifies** the profile and declares skills.
4. Auto-approve by policy → active; else admin approves.

**Business rules**
- People onboard themselves; the admin handles exceptions only (FR-3.1).
- `contract_type · operating_entity` asked only if on WS payroll; `skills` only if a performer; `cost/pay` (encrypted) only if paid through WS; `bank` JIT at first payout.
- Cost/pay/PII MUST be field-encrypted; salary data never stored in plaintext (FR-3.5).

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Skill declaration needs verification | Person is active for non-gated work; gated skills pending admin/reviewer approval. |
| Same person across two entities | One Party; entity-scoped relationships; no duplicate identity. |
| Contractor vs payroll | Payroll-only fields asked only for payroll contracts. |
| Person offboarded mid-assignment | Their in-flight activities flagged for reassignment (→ E13); no silent drop. |
| SSO account deprovisioned upstream | Access revoked on next auth; historical records retained (append-only). |

**FRs** — FR-3.1 self-onboard, admin-exceptions-only · FR-3.2 AI pre-fill from portable identity · FR-3.3 skill-gated approval policy · FR-3.4 one Party, many entity relationships · FR-3.5 encrypted cost/pay/PII · FR-3.6 offboarding triggers reassignment of in-flight work.

**AC** — A person can self-onboard and be active without admin touch when policy allows; salary is never returned in plaintext to any surface; offboarding never orphans live activities.

---

### E4 · Relationships — clients & vendors (L1)

**Base case (client)**
1. Admin adds a client: **company name · code · one requester (name+email)**.
2. Pricing/invoice-code/wallet asked **only if billing through WS**, JIT at first request.

**Base case (vendor / cross-org)**
1. Admin adds a vendor with **identity only** (`vendor_type` + contact, or a **WS-tenant link**).
2. `dispatchable_scope` defaults to *any* (JIT-narrowed); cost/rate captured at first dispatch; boundary review = mandatory; transparency = opaque (defaults).

**Business rules**
- Tenant/client/vendor are **relationship types on one model**, not separate flows (FR-4.1).
- A vendor may be an external party *or* another workspace (the cross-org edge — E14).
- Vendor onboarding MUST work even when the offering/skills aren't known yet (identity-only, then JIT).

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Client doesn't want money in/out via WS | No pricing/wallet/invoice fields asked; delivery still fully works. |
| Vendor's offering unknown at onboarding | Onboard on identity only; scope/cost captured at first dispatch. |
| Vendor is another workspace | Establish the cross-org edge (E14); B must accept before dispatch. |
| Requester email later belongs to a different client | Requests route by the mapped relationship; ambiguous senders flagged (→ E5). |

**FRs** — FR-4.1 one relationship model, typed · FR-4.2 client billing fields gated + JIT · FR-4.3 vendor identity-only onboarding · FR-4.4 vendor defaults (opaque, mandatory boundary review) · FR-4.5 vendor-as-workspace establishes a cross-org edge.

**AC** — A client with billing off is created with 3 inputs and can receive delivery; a vendor can be onboarded before its skills are known.

---

### E5 · Request intake

**Base case**
1. A requester submits **brief + files + deadline** via any channel (form, email, client tool, manual).
2. The product creates a **Request** with a `source_channel`, mapped to the client relationship + entity.

**Business rules**
- Channels: manual · Phrase adapter (1 Project = 1 Job = 1 Request) · email auto-create (1 thread ↔ 1 request) · ambient AI brief. All converge on one Request record.

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Duplicate email thread / re-send | Deduped to the existing Request (1 thread ↔ 1 request); appended, not duplicated. |
| Brief with no files | Request created; the composer raises clarifying questions if files are required for scoping. |
| Deadline in the past / missing | Flagged at intake; owner asked to confirm/repair before compose. |
| Requester not mapped to a client | Held in an "unmapped intake" queue; admin maps or rejects. |
| File unreadable / too large | Intake accepts the pointer; the composer flags it and requests a re-upload. |
| Ambiguous sender (matches 2 clients) | Routed to a disambiguation queue, not silently assigned. |

**FRs** — FR-5.1 multi-channel intake → one Request model · FR-5.2 email/tool dedupe (1 thread/project ↔ 1 request) · FR-5.3 unmapped/ambiguous intake queued, never dropped · FR-5.4 past/missing deadline flagged before compose.

**AC** — The same request arriving twice creates one Request; an unmapped sender never auto-attaches to the wrong client.

---

### E6 · AI plan composition

**Base case**
1. Composer (in the zero-retention enclave) reads brief + files **and this workspace's own config**.
2. Produces a **proposal**: offering + level · unit type/count · a **tree of activities** (skills, order, dependencies, Deliver last) · a proposed performer per activity · deadline · price (if billing on) · scope sheet · confidence · clarifying questions.

**Business rules**
- The composer **composes only from the tenant's own config** — it never invents structure (FR-6.1).
- It is **stateless, per-tenant scoped, zero-retention** — brief/file content is never persisted, never crosses tenants (FR-6.2).
- Output is a **proposal only**; nothing is real until the owner ratifies (FR-6.3).

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Vague/ambiguous brief | Low-confidence proposal + **clarifying questions**; never a silent guess. |
| Thin catalog (new tenant) | A thin plan proportional to config; archetypes mitigate; honest "as good as the config." |
| No matching offering | Composer flags "no offering matches"; owner maps manually or extends the catalog. |
| Mis-mapped offering/level | Owner edits inline (E7); the composer learns from edits **within the tenant only**. |
| File content can't be read | Flagged; scoping falls back to owner input or a re-upload request. |
| Cross-org request | Each side composes within its **own** workspace; the composer never reaches across the boundary. |

**FRs** — FR-6.1 compose from tenant config only · FR-6.2 stateless, per-tenant, zero-retention enclave · FR-6.3 suggest-not-act · FR-6.4 emit confidence + clarifying questions on low certainty · FR-6.5 provenance recorded (which config/templates were used) · FR-6.6 federated by the boundary.

**AC** — The composer never persists brief/file bytes; a vague brief yields questions, not a fabricated plan; no proposal becomes an assignment without ratification.

---

### E7 · Plan ratification (human touchpoint #1)

**Base case**
1. Owner opens the proposal.
2. **Approves in one click** → the Assignment + Activity tree are written in one transaction; the request goes LIVE; activities fan out in parallel.

**Business rules**
- Approval is one action, not a multi-screen wizard (FR-7.1).
- Editing is inline; an edit re-plans only the affected part (FR-7.2).

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Owner tweaks the plan | Inline edit; product re-derives dependent scoping/pricing; re-presents. |
| Owner rejects | Owner re-briefs/re-scopes → composer re-runs. |
| Owner unavailable past SLA | Escalates per policy (delegate/next owner); request doesn't stall silently. |
| Repeated reject loop | After N cycles, escalate to ops with the rejection reasons `[J: N]`. |
| Pricing/wallet check fails at publish | Auto-flag the owner to fix/fund before activities mobilize. |

**FRs** — FR-7.1 one-click approve · FR-7.2 inline edit re-plans only the delta · FR-7.3 reject → re-compose loop · FR-7.4 owner-unavailable escalation · FR-7.5 publish gated on pricing/wallet check when billing on.

**AC** — Approving publishes the whole tree atomically; an edit never forces a full re-author; an absent owner never freezes a request indefinitely.

---

### E8 · Allocation & mobilization

**Base case**
1. Per activity: **Pass 1** hard filters (skill+proficiency, availability, no conflict, tier-eligible) → **Pass 2** weighted score (`fit · quality_to_cost · committed_capacity_first · deadline_confidence · responsiveness`).
2. Product proposes the top performer (named) + alternates with reasons (at plan-ratify).
3. Mobilize via **WS-chat + push** (default); performer **one-tap accepts**.

**Business rules**
- **Committed-capacity-first:** saturate fixed-cost resources (salaried-to-quota, retainer teams, owned licenses; ~$0 marginal) before variable freelancers (FR-8.2).
- **No bidding** (removed per Bhavya) — propose → ratify → accept only (FR-8.3).
- Channels: WS-chat default (free); WhatsApp/SMS are **user-selectable paid fallbacks** behind one adapter; pay for costly channels only when the free one fails (FR-8.5).

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| No candidate passes hard filters (empty bench) | Fallback ladder: source externally (approved vendor/pool) **or** escalate to ops — per policy `[J]`. |
| Proposed performer declines | Auto-propose next-best; escalate by timezone/responsiveness. |
| All candidates exhausted | Fallback: external sourcing / curated open / escalate `[J]`. |
| No response within the window | Escalate channel: WS-chat → WhatsApp → SMS/call. |
| Performer accepts then goes silent | SLA monitor auto-escalates and surfaces a risk signal `[J: policy]`. |
| Conflict of interest (same party both sides) | Hard-filtered out in Pass 1. |
| Committed capacity saturated | Spill to next tier / variable resources per the objective. |
| Score tie | Deterministic tie-break (e.g. responsiveness, then cost) — no random assignment. |

**FRs** — FR-8.1 two-pass allocation (filter → score) · FR-8.2 committed-capacity-first · FR-8.3 propose→ratify→accept, no bidding · FR-8.4 fallback ladder on decline/exhaust · FR-8.5 channel-native, escalating, cost-aware mobilization · FR-8.6 SLA monitor auto-escalates at-risk work · FR-8.7 objective weights are tenant config.

**AC** — An empty bench never leaves an activity silently unassigned; a costly channel is used only after the free one fails; the same party can't sit on both sides of an activity.

---

### E9 · Execution — perform + QA

**Base case**
1. Performer type (set in the plan) runs: **human** works with progress auto-logged; **AI agent** runs a first pass; **human+tool** gets a JIT-brokered tool license.
2. QA policy per activity: **auto-QA** (agent-safe) or **human reviewer Pass/Fail**.
3. On pass → the activity is terminal.

**Business rules**
- One allocation engine for all performer types; an agent is allocated like a performer (~$0 marginal) but doesn't "accept" — it runs; first-pass → human QA (FR-9.2).
- The **license broker** assigns a pooled tool license JIT to the activity-session (a license = a committed resource) (FR-9.3).

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Agent first-pass fails | Fall back to a human performer automatically. |
| Interim/draft output | Auto-share the draft to the requester (border-safe); work continues. |
| Tool license unavailable | Broker queues for the next free license or escalates; activity waits, doesn't fail. |
| QA fails | Rework loop back to the performer. |
| Repeated rework (loop) | After N rounds, escalate to owner/ops `[J: N]` — no infinite loop. |
| Partial output | Activity stays non-terminal; dependent branches keep waiting on their input. |
| SLA breached mid-work | Auto-escalate + surface risk to the requester `[J]`. |

**FRs** — FR-9.1 progress auto-logged from the tool · FR-9.2 agent-as-performer with human-QA fallback · FR-9.3 JIT license broker · FR-9.4 QA policy per activity (auto vs human) · FR-9.5 rework loop with an escalation cap · FR-9.6 interim drafts auto-shared border-safe.

**AC** — A failed agent pass never blocks delivery (human takes over); QA rework can't loop forever; an unavailable license waits rather than dropping the activity.

---

### E10 · Delivery & verify (human touchpoint #2)

**Base case**
1. When all sibling activities + child assignments are terminal, the deliverable is **assembled**.
2. Owner gives **boundary sign-off** (mandatory review).
3. Deliver to the requester's store; the requester has had a status roll-up throughout.
4. AI **pre-computes reconciliation** (splits · fees · counts · exceptions).
5. Verifier **one-tap confirms** — the billing gate.

**Business rules**
- Deliver is the mandatory last activity of every assignment (FR-10.1).
- Verify is a **~10-second confirm**, not manual reconciliation (FR-10.4).
- Deliverables are **written to the recipient's store** (their property); the graph keeps the pointer + attribution (FR-10.3).

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Dependencies not yet terminal | Hold; other branches keep running; assemble only when all are terminal. |
| Boundary sign-off rejected | Route back to rework; nothing crosses the boundary. |
| Requester approval required and they reject | Rework loop back to the performer. |
| Recipient store unavailable at delivery | Retry with backoff; owner flagged; delivery not marked done until written. |
| Reconciliation mismatch at verify | Verifier sees the exception; can send back to fix before confirming. |
| Verifier unavailable | Escalate per policy; the gate doesn't silently auto-pass. |

**FRs** — FR-10.1 Deliver is the mandatory terminal activity · FR-10.2 assemble only when the whole tree is terminal · FR-10.3 deliverable written to recipient's store + attribution · FR-10.4 AI-precomputed reconciliation → one-tap verify · FR-10.5 verify is the sole billing gate · FR-10.6 auto-delivery shortcut where policy allows.

**AC** — Nothing bills without a verify confirm; a deliverable is never marked delivered until it's actually written to the recipient's store; a reconciliation mismatch is visible before money moves.

---

### E11 · Money — invoicing, wallet, payout

**Base case**
1. On verify, the product emits **one billable event**.
2. It fans out to two **independent, capability-gated** sides: **invoicing** (money in) and **payout** (money out).
3. Rolling — the moment verify clears; no batch pile-up.

**Business rules**
- A performer is paid off **verified work**, independent of whether the client has paid (FR-11.2).
- Invoicing destination is **pluggable**: WS module (generate) · external connector (push the event) · data-out (API/webhook) (FR-11.3).
- Wallet ledger is **append-only and the source of truth** — no spreadsheet mirror (FR-11.5).
- Grouping/tax/coins/quota are **config** (EZ: "1 invoice/entity/month", coins, quota×1.1).

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Billing turned off | No billable-money-in side; payout side still runs if paying through WS; no invoice generated. |
| Prepaid wallet insufficient at assignment-create | Publish blocked (E7 FR-7.5); owner asked to fund. |
| Assignment cancelled after wallet deduct | Refund the lot on cancel (ledger entry). |
| External connector down | Billable event is durable; push retried; no data lost. |
| Currency/tax mismatch | Resolved from the entity's `tax_profile`/currency; mismatch flagged, not guessed. |
| Client disputes an invoice | Dispute path (E13 F5); payout already settled off verified work is not clawed back. |
| Payout for an agent/tool | Agent/tool has ~$0 marginal cost; payout is for human/committed resources per config. |

**FRs** — FR-11.1 one billable event on verify · FR-11.2 invoicing & payout decoupled; payout off verified work · FR-11.3 pluggable invoicing destination · FR-11.4 wallet deduct-at-create → settle-at-verify → refund-on-cancel · FR-11.5 append-only ledger as source of truth · FR-11.6 grouping/tax/coins/quota all config · FR-11.7 typed-decimal, tested money math (no imports, no untested rules).

**AC** — Turning billing off removes all invoicing; a performer is paid on verify regardless of client payment; the wallet ledger reconciles to itself with no external mirror; a cancel always refunds correctly.

---

### E12 · Ongoing work — retainer & outcome (Type B)

**Base case**
1. An Engagement with `delivery_model = retainer | outcome` runs over **service periods**.
2. Retainer: "complete" = a period closes + verified → bill per period.
3. Outcome (BOT): "complete" = period closes + the outcome metric measured → bill per period from the metric.

**Business rules**
- Same lifecycle engine as deliverable work; the difference is *what "complete" means* and *how it rolls to a billable event* — both config, not new code (FR-12.1).

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Mid-period scope change | Applied to the current/next period per policy; pricing recomputed (E13 F1). |
| Outcome metric not measurable at close | Period held pending the metric; billing waits on the measurement `[J: formula]`. |
| Retainer + usage overage | Base retainer bills flat; overage bills as usage on top (billing_model = retainer+usage). |
| Period rollover | Next period auto-opens (recurring); no manual re-creation. |
| Engagement paused | Periods suspend; no billing while paused; resume cleanly. |

**FRs** — FR-12.1 one engine, delivery_model decides "complete" · FR-12.2 service-period state machine · FR-12.3 per-period billable events · FR-12.4 outcome billing from a measured metric `[J]` · FR-12.5 auto period rollover for recurring engagements.

**AC** — A retainer bills once per closed+verified period; an outcome engagement doesn't bill until its metric is measured; scope changes don't corrupt prior periods.

---

### E13 · Change & exceptions

**Base cases & rules**
- **F1 Scope change mid-flight** — edit-levels; pricing/scope recomputed; in-flight activities adjusted or re-planned (delta only).
- **F2 Reassignment** — expert unavailable → reassign; **fee-split** applies; **the workspace never funds the overrun** (EZ rule as config) (FR-13.2).
- **F3 Cancel / pause** — cancel refunds the wallet lot; pause suspends without billing.
- **F4 Goodwill revision post-completion** — a **new linked assignment, no claw-back** of the original (FR-13.4).
- **F5 Disputes** — a dispute path on invoices/deliverables; verified-work payouts aren't clawed back.
- **F6 Recurrence** — recurring requests re-open on cycle.

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Scope change after some activities are terminal | Only non-terminal parts re-plan; terminal outputs preserved. |
| Reassignment cost > original | Fee-split per policy; overrun not funded by the workspace. |
| Cancel after partial delivery | Refund per policy; delivered parts retained; ledger consistent. |
| Goodwill fix requested weeks later | New linked assignment; original billing untouched. |
| Dispute during payout | Payout of already-verified work stands; dispute handled on the invoice side. |

**FRs** — FR-13.1 scope change re-plans the delta only · FR-13.2 reassignment fee-split, workspace never funds overrun · FR-13.3 cancel refunds, pause suspends billing · FR-13.4 goodwill = new linked assignment, no claw-back · FR-13.5 dispute path decoupled from verified-work payout · FR-13.6 recurrence auto-reopen.

**AC** — A mid-flight scope change never discards completed work; a goodwill fix never reverses the original invoice; a cancel always leaves the ledger balanced.

---

### E14 · Cross-org / boundary (Phase 2)

**Base case**
1. WS-A onboards a vendor with `vendor_type = WS-tenant` → the handshake creates one Relationship edge; B accepts (sees an incoming **client**).
2. A dispatches a request → in A's graph the vendor is **one opaque boundary node**; in B's graph it's a **new Request** with A as client.
3. B runs its own lifecycle invisibly; returns a border-safe status roll-up + deliverable.

**Business rules**
- A never sees B's tree, performers, method, sub-vendors, or costs; B never sees A's other vendors/entities (FR-14.2).
- **Brokered files:** inputs stay in A's store (B gets a JIT scoped credential); deliverable written into A's store; provenance stripped per hop (FR-14.3).
- Transparency dial (config): default opaque; the vendor controls its own ceiling (FR-14.4).

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| B declines at the boundary | A's allocation treats it as a decline → fallback ladder (E8). |
| Chain A→B→C | Each hop re-encapsulates; **A never learns C exists**; provenance stripped per hop. |
| B raises transparency for A | Only up to B's own ceiling; A sees more milestones, still not internals. |
| Brokered credential expires mid-work | B re-requests a scoped credential; no standing access. |
| Deliverable write-back to A fails | Retry; not marked delivered until written; attribution logged. |
| Non-WS vendor (email/Phrase/API) | Client-system adapter — functional but bounded by that tool's surface. |

**FRs** — FR-14.1 one edge, two views (vendor/client) · FR-14.2 full encapsulation both directions · FR-14.3 brokered files, JIT scoped credentials, deliverable written to recipient's store · FR-14.4 transparency dial, vendor-controlled ceiling · FR-14.5 mandatory boundary sign-off + provenance stripping · FR-14.6 chains re-encapsulate per hop.

**AC** — A can never enumerate B's performers or sub-vendors; a chained C is invisible to A; a brokered credential is always scoped, expiring, and revocable.

---

### E15 · Multi-entity isolation

**Base case**
1. An org has multiple operating entities in one workspace.
2. Every relationship/work/wallet record carries `operating_entity_id`; access is scoped by `(workspace_id, operating_entity_id)`.
3. Default: sibling entities don't see each other's relationships or work.

**Business rules**
- **Default isolated** — Entity-1 does not learn Entity-2 is a vendor to Org B's Entity-3 (FR-15.1).
- The org admin sees across entities **unless** entity-delegated module-admins blind even the admin (FR-15.2).
- **Entity-vs-workspace is the client's choice** — entities-in-one-WS (policy isolation) vs a workspace-per-entity (crypto isolation); both interoperable and migratable (FR-15.4).

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| A user queries a sibling entity's work | Denied by RLS scoping; not visible. |
| Org admin should be blinded from an entity | Entity-delegated module-admin scope blinds even the org admin. |
| External Org B looks in | Sees only the entity it works with — never the org's other entities. |
| Client wants an entity fully walled off | Provision it as its own workspace (crypto isolation, own keys/tier). |
| Migrate an entity to its own workspace later | Supported as a **data-separation operation** (re-key + move) — heavier than a config toggle; flagged honestly. |
| `entity_isolation` flag flipped to shared | The org opts into cross-entity visibility deliberately. |

**FRs** — FR-15.1 entity-level default isolation via scoping · FR-15.2 entity-delegated admin can blind the org admin · FR-15.3 external orgs see only their counterpart entity · FR-15.4 entity-vs-workspace is the client's choice, interoperable + migratable · FR-15.5 separated entities still link back via the cross-org boundary.

**AC** — A sibling entity can't read another's relationships; an external org can't enumerate the org's other entities; an entity can be split to its own keyed workspace later.

---

## 6. Cross-cutting requirements

- **CC-1 Ambient AI** — AI is inline (suggest→approve), never a separate chatbot panel. Every AI output is a proposal a human can accept/edit.
- **CC-2 Channel-native notifications** — WS-chat default; WhatsApp/SMS/email selectable; one adapter interface; escalation is cost-aware.
- **CC-3 Reliable reporting** — one lifecycle engine; status derived in the write transaction; **no drift, no repair crons**. Reporting reads state; never computes it.
- **CC-4 Server-authoritative access** — RBAC + POV-scoping enforced server-side and config-driven (replaces frontend-JSON perms + email allowlists).
- **CC-5 Audit** — append-only, tenant-inspectable; every state change and money event logged.
- **CC-6 Files** — the graph holds pointers; bytes are processed in a zero-retention enclave; access flows to the tool, never a person.
- **CC-7 No shadow data** — no spreadsheet-as-database, no ERP↔WS sync anywhere.

---

## 7. Non-functional requirements

| # | Requirement |
|---|---|
| NFR-1 | **Isolation** — `workspace_id` crypto-isolated (BYOK for sovereign); `operating_entity_id` policy-isolated (RLS). Enforced server-side. |
| NFR-2 | **Confidentiality** — raw content never stored as system of record; zero-retention enclave; PII/salary field-encrypted. |
| NFR-3 | **Reliability** — state+status atomic; outbox for events; no dual-write drift. |
| NFR-4 | **Auditability** — append-only audit + money ledger; reconstructable history. |
| NFR-5 | **Scalability** — parallel activity branches; async workers for escalation/invoicing/payout; reporting off a read model. |
| NFR-6 | **Data residency** — regional/sovereign tiers pin data; enclave + file broker deploy per region. |
| NFR-7 | **Testability** — money and lifecycle rules covered by a parity-test catalog **before** the code that implements them. |
| NFR-8 | **Maintainability** — config-not-code; typed schema; no hand-run management-command surface. |

---

## 8. Phasing & scope

**Phase 1 (EZ as Tenant-Zero, intra-workspace):** E1–E13 + all cross-cutting + all absorbed ERP money/HR domains. Multi-tenant-*ready* by design.
**Phase 2 (cross-org):** E14 turned on; E15 entity-isolation is **built in Phase 1** (the primitive) so Phase 2 needs no rewrite. Portable identity/SSO (B2/B3) here.
**Parked:** commercial/pricing product, live-market moat.

---

## 9. Open items — awaiting Joy & Bhavya

**Joy `[J]`:** (1) allocation objective weights · (2) empty-bench fallback (external vs escalate) · (3) QA policy per activity · (4) SLA at-risk policy · (5) delivery-engine role definitions → owner/performer/reviewer/verifier · (6) BOT/outcome billing formula · (7) rework/reject escalation caps (the "N" values) · (+ delivery archetypes 02–06, statutory matrix).

**Bhavya (architecture.md §10):** core shape (modular-monolith vs microservices) · transactional vs event-sourced · GraphQL vs REST · isolation mechanism per tier · async infra · stack confirmation.

**None of these change a workflow or a requirement** — they fill parameters at marked holes.

---

## 10. Glossary

**Party** — an org or a person. **Relationship** — a typed edge (employment/client/vendor/tenant). **Request / Assignment / Activity** — the work-graph tree (BAT). **Deliver** — the mandatory last activity. **Billable event** — the single money-in/out trigger emitted at verify. **Committed capacity** — fixed-cost resources (salaried, retainer, owned licenses) with ~$0 marginal cost. **Archetype** — a generic industry starter kit that seeds config. **Readiness engine** — computes "can deliver" and asks only for gaps. **Boundary node** — the opaque representation of a vendor workspace in the client's graph. **Enclave** — the zero-retention sandbox where content is processed. **Operating entity** — a legal/billing unit inside one org (policy-isolated). **Workspace** — a tenant (crypto-isolated).

---

*The what is here; the how is in [`architecture.md`](./architecture.md); the field-level design is in [`05-zero-cut-design.md`](./05-zero-cut-design.md). Flag anything wrong or missing before approval — that's what this document is for.*
