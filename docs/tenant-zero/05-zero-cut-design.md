# WS 3.0 — Zero-Cut Design (7 layers, field-level)

**The locked, field-level design** for the seven layers — Onboarding · Work Lifecycle · Allocation · Cross-Org · Multi-Entity · Money & Files · AI-Composes — from the layer-by-layer walkthrough. Platform-generic (no EZ baked); efficiency-first; capability-gated. `(EZ: …)` = illustrative config only. `[J]` = pending Joy's confirmation.

## Principles that govern all three layers
1. **Party + Relationship** — a Party (Org or Person) + a Relationship edge (employment / client / vendor / tenant). Tenant/client/vendor are *relationship types*, not separate systems.
2. **Capability-gated + JIT fields** — only fields a turned-on capability needs are asked; the rest surface at first use.
3. **Platform-generic** — roles, activities, tools, money are generic; EZ's values are config.
4. **Efficiency-first** — AI composes, humans ratify; edges are channel-native.

---

## Layer 1 — Onboarding

### The model
Onboard a **Party once**, attach a **Relationship** with its own config. Fields below are the *only* ones asked; everything else is a default, a ratification, or deferred (JIT).

### Fields by party (always-asked vs gated/JIT)
**Tenant (org + workspace) — platform operator (L0):** `org legal/display name` · `org_code` · `region` · `deployment_tier` · `admin_email`. *(BYOK keys only if regional/sovereign; modules_available.)*

**Operating entity — L1 admin:** always `legal_name · code · country`.
- Money switch **"Bill clients through WS?"** → if **Yes**: `billing_currency · tax_profile · invoice_prefix`. If **external**: connector only. If **No**: nothing.
- Money switch **"Pay performers through WS?"** → if Yes: payout/`bank_details` (JIT at first payout).

**Person — L1 invites → self-completes:** always `name · email · party_role`.
- `contract_type · operating_entity` → only if on WS payroll · `skills` → only if performer · `cost/pay` (encrypted) → only if paid through WS · `bank` → JIT at first payout.

**Client (deliver to) — L1:** always `company_name · code · one requester (name+email)`.
- `pricing / invoice_code / wallet` → **only if billing through WS**, JIT at first request.

**Vendor (dispatch to, cross-org) — L1:** always identity only — `vendor_type` (+ name/contact, or **WS-tenant link**).
- `dispatchable_scope` → **default "any," JIT-narrowed** · `cost/rate` → **at first dispatch** · `boundary_review = mandatory`, `transparency = opaque` (defaults).

### Archetypes (efficiency)
A generic **industry starter kit** (translation / creative / research / generic) that pre-seeds catalog + skills + roles + SLA/pricing bands → admin **ratifies**. Generic industry knowledge only — never EZ's proprietary templates. Optional ("Generic" = near-empty).

### Readiness engine
Computes "can deliver" live from the minimum chain and asks only for gaps: `entity · offering + skills + Delivery-skill · team · people · client/requester` (+ `pricing/wallet` *only if billing on*). Workspace flips to **Operational** when satisfied; deepens JIT after.

---

## Layer 2 — Work Lifecycle

### Primitives
`Request` (enters the workspace) → `Assignment` (group of activities for one offering; Deliver is the mandatory last activity) → `Activity` (input(s) → one performer → one skill → output(s)). A Request is a **tree**; independent branches run in parallel, dependent ones wait on their input.

### What a human types across the whole lifecycle
- **Requester:** `brief · files · deadline`
- **Owner:** *Approve* (or edit only to change the AI plan)
- **Performer:** *Accept* + the `output`
- **Reviewer:** *Pass/Fail* (only if human QA)
- **Verifier:** *Confirm*

Everything else is AI-composed or system-derived. **Net human touchpoints = 2** (ratify plan, confirm verify).

### Fields by record (source · when)
**Request:** `id · requester_id · entity_id` (system) · `brief · input_files[] · deadline` (**requester**, always) · `source_channel · engagement_id · stage/state/status` (system).

**Assignment (AI-composed → owner ratifies):** `offering_id · level` (AI→ratify) · `unit_type · unit_count` (AI) · `delivery_model · billing_model` (config) · `owner_id` (system) · `price` (AI, *only if billing on*, JIT) · `invoice_code · payment_type` (config, *only if billing on*) · `deadline` (AI→override) · `stage/status` (system).

**Activity:** `skill_id · performer_type · performer_id` (AI→accept) · `input_files[] · dependency(dep_activity_id) · unit_count · start_by/deliver_by` (AI) · `sort_order` (system, Delivery=last) · `qa_policy` (config) · `outputs[]` (**performer**) · `progress` (performer/tool, auto) · `stage/status` (system, derived in-engine — no drift).

**Delivery:** `deliverable` (system, on cascade) · `boundary_signoff` (**owner**) · `delivered_to_store` (system).

**Verify:** `reconciliation` (AI pre-computes) · `verified_by · confirm` (**verifier**, the gate) · `notes` (optional).

**Bill & Pay:** `billable_event` (system, on verify) · `payout[]` (system, always, rolling) · `invoice` (system, *only if billing through WS*) · `pushed_to_external` (connector, if billing external).

### State machine
```
Request     : created → live → delivered → verified → billed  (+ paused, cancelled)
Assignment  : created → published → delivered → verified
Activity    : created → published → delivered
Status (derived, in-engine): not_started · on_track · slightly_delayed · critical · …completed
             roll-up = worst-of over the tree
```
Key change vs WS 2.0: **status derived in the same transaction/event as the state change** → no async drift, no repair crons.

---

## Layer 3 — Allocation

### The engine (per activity)
**Pass 1 — hard filters (platform):** required `skill+proficiency` (+ language/domain) · available · not conflicted · tier-eligible.
**Pass 2 — weighted score (objective; weights = tenant config `[J]`):** `fit · quality_to_cost · committed_capacity_first · deadline_confidence · responsiveness` → propose top-1 (named) + alternates, with reasons.

### Committed-capacity-first (the economic rule)
Fixed-cost resources — salaried experts (to quota), retainer teams, owned tool licenses — have ~$0 marginal cost → **saturate them before variable freelancers.** Ties to the quota/coins model (config).

### Three agency gates
1. **AI proposes** the named performer (at plan-ratify).
2. **Owner ratifies** → *accept · swap to an alternate.* **(No bidding — removed per Bhavya.)**
3. **Performer accepts/rejects** — one tap.

### Mobilization (channel-native)
- **Default channel = WS-chat + push** (free, native one-tap, reuses WS 2.0 `chat-v2`).
- **User-selectable fallbacks = WhatsApp / SMS** (paid; the tenant/user turns these on).
- **Behind one channel-adapter interface** — the platform emits "mobilize + one-tap payload"; adapters deliver it. Channel set + routing = tenant config.
- **Routing/escalation:** WS-chat push → (no response in window) → WhatsApp → SMS/call. **Pay for costly channels only when the free one fails.**
- **Predictive pre-mobilization** — *hook designed now, shipped later* (needs demand history): warm likely performers ahead of known demand (recurring periods, in-flight requests, historical patterns) via a **soft, non-binding** availability ping; feeds deadline-confidence/responsiveness. Not zero-cut.

### Fallback ladder (no bidding)
```
proposed declines / times out → next-best (auto)
   → candidates exhausted → source externally (approved vendor/pool)  |  escalate to ops
```

### Performer types — one engine
- **Human** — proposed → accepts → works.
- **AI agent** (EZ: Flip/MT/OCR) — allocated like a performer (~$0 marginal, high speed, quality profile); no "accept," it just runs; first-pass → human QA.
- **Human + tool** — the **license broker** assigns a pooled tool license (EZ: TR42/Canva) JIT to the activity-session (a license = a committed resource; same utilization logic).

### Fields
**Allocation Policy (config, once):** `objective_weights{fit,quality_to_cost,committed_capacity_first,deadline_confidence,responsiveness}` (defaults; tunable `[J]`) · `hard_filters` (platform) · `fallback_policy{on_exhaust: external | escalate}` · `escalation_window` · `channel_policy{default: ws_chat, optional: [whatsapp, sms]}`.
**Per-activity (engine + access):** `candidates_scored[]·proposed_performer_id·alternates[]·reasons` (AI) · access `{subject_id, role_type=activity, role_status(pending→accepted/rejected), reject_reason}` (**performer tap**) · `mobilization{channel, sent_at, response, escalation_step}` (system).

---

## Layer 4 — Cross-Org / Boundary  *(in the zero cut)*

**The insight:** a cross-WS connection is **one Relationship edge** that is *"vendor"* from one side and *"client"* from the other. No separate cross-org machinery — the Party+Relationship model viewed from both ends.

### Establishing the link (handshake)
WS-A onboards a vendor with `vendor_type = WS-tenant` → `linked_org_ref` (B) · `dispatchable_scope` (default *any*) · `cost_terms` (JIT) · `transparency_granted` · **`operating_entity` (A-side — entity-scoped)**. B accepts → sees it as an incoming **client** (`pricing_to_A`, `SLA`, `transparency_ceiling`). `connection_type`: WS-native | adapter (email/Phrase/API).

### Request crossing
- **In A's graph:** the assignment's performer = **"WS-B" — one opaque boundary node**. `boundary_node_id → maps_to: request_id (in B)`.
- **In B's graph:** a **new Request** with **A as requester/client**; B runs its own internal lifecycle, invisible to A.

### Visibility (both directions)
- **A→B crosses:** brief · input files (brokered) · deadline. **Opaque to A:** B's tree, performers, method, sub-vendors, costs.
- **B→A crosses:** border-safe status roll-up · deliverable · action-items · risk. **Opaque to B:** A's other vendors/entities.

### Mechanics
- **Brokered files:** input files stay in A's store; B gets a **JIT scoped credential** (`file_ref` · `access_grant{scope, grantee=B's WS-identity, expiry, revocable}`); deliverable **written into A's store**; **attribution** in A's own logs.
- **Transparency dial (config):** default **opaque**; B may raise per relationship (`transparency_level ∈ {opaque→milestones→detailed}`) — vendor controls its ceiling.
- **Mandatory boundary review:** `boundary_signoff` (B's owner) + **provenance stripped** before crossing.
- **Allocation:** the boundary node is just `performer_type = vendor-workspace` in A's allocation engine (scored like any performer); the "accept" is by **B's owner**; B then allocates internally.
- **2–3 WS chain:** A→B→C — each hop re-encapsulates; **A never learns C exists**; provenance stripped per hop.
- **Non-WS party:** client-system adapter (email/Phrase/API) — functional but bounded by that tool's API.

### Fields
`relationship_id` · `{workspace_A, role=vendor}` · `{workspace_B, role=client}` · `linked_org_ref` · `operating_entity` (A-side) · `status` · A-cfg `{scope, cost, transparency_granted}` · B-cfg `{pricing, SLA, transparency_ceiling}` · `boundary_review_policy` · `connection_type`. Boundary node: `boundary_node_id · maps_to · visible_status · deliverable_ref · opacity_level`.

---

## Layer 5 — Multi-Entity & the Entity-vs-Workspace choice  *(in the zero cut)*

**The rule:** **Entity = a billing/legal unit inside one org, policy-isolated. Workspace = a separate org/tenant, crypto-isolated.** The client picks how many of each; the same engine runs under both.

### Multi-entity isolation (within one workspace)
- Every relationship/work/wallet record carries **`operating_entity_id`**; access scoped by `(workspace_id, operating_entity_id)` (RLS + need-to-know).
- **Default isolated:** sibling entities don't see each other's relationships/work. *(Ex: Entity-1 does not learn that Entity-2 is a vendor to Org B's Entity-3.)*
- **Org admin sees all** across entities — unless **entity-delegated module-admins** (`module_admin_scope = entity`) blind even the admin.
- `entity_isolation` flag (default **isolated**) — an org can flip it to share visibility across its entities.
- **The mirror:** an external Org B sees **only** the entity it works with — never the org's other entities (cross-org encapsulation).

### The client's choice (both supported, interoperable, migratable)
| | Entities in one WS | Entity as its own WS |
|---|---|---|
| Isolation | policy (need-to-know + scoping) | **cryptographic** (separate tenant, BYOK) |
| Sibling can see? | no by default (admin can) | **no — can't** |
| Config/people/catalog | shared | fully separate |
| Tier/keys | same | can differ (e.g. sovereign) |

- Pick **one-WS** when entities share ops and policy-isolation suffices; **separate-WS** when a hard wall, own keys/tier, or a distinct operation is needed.
- **Separate ≠ cut off:** a separated entity still links back via the **cross-org boundary** (Layer 4).
- **Migratable:** start entities-in-one-WS, split one into its own WS later. *Honest note:* splitting into a crypto-isolated/BYOK workspace involves **separating that entity's data** into its own keyed store — supported, but heavier than a config toggle.
- **Expressed at provisioning:** "one workspace with entities" vs "a workspace per entity" — a Foundation-layer decision the admin/operator sets.

---

## Layer 6 — Money & Files  *(in the zero cut)*

**Control plane, not data plane:** WS orchestrates the **money events** and holds **file pointers**; money-custody and bytes can live elsewhere.

### The decoupling
At **Verify**, WS emits one **billable event** → fans out to two **independent, capability-gated** sides: client **invoicing** (money in) and performer **payout** (money out). A performer is paid off *verified work*, not off client payment.

**Billable event (always):** `billable_event_id · assignment_ref · verified_by/at · unit_count · unit_price · amount · currency · billing_model · operating_entity_id · client_relationship_id`.

### Client side — invoicing *(gated: "bill through WS?")*
Pluggable destination: **WS module** (generate) · **external connector** (push billable event to their system) · **data-out** (API/webhook).
- **WS invoice:** `invoice_number` · **`grouping_rule` (config** — per-entity-per-period / per-request; *EZ's "1/entity/month" is a value*) · `rate_snapshot` · `line_items[]` · `tax` (from entity `tax_profile`) · `status`.
- **External:** `pushed_to_external{system, external_ref, status}` — no WS invoice.

### Wallet / credits *(gated: prepaid)*
`Wallet{balance, cost_per_credit}` · `WalletLot{credits, remaining, validity}` (FIFO) · **`WalletLedger` (immutable — the source of truth, no sheet mirror)**. Deduct at assignment-create → settle at verify → refund on cancel.

### Expert side — payout *(gated: "pay through WS?")*
`payout{performer_id, period, amount/coins, source=billable events, status}`. Value unit + quota/incentive = **config** *(EZ: coins, quota×1.1)*. If not via WS → export to their payroll.

### Files
- **Graph holds `file_ref{store_location, key, checksum, size, mime, owner_entity}` — a pointer, not bytes.**
- **Storage tiers (config):** WS-managed · connected cloud · own infra (sovereign).
- **Enclave (zero-retention):** bytes pulled ephemerally → compute → return → retain nothing; access flows to the tool, never a person.
- **Brokered access:** inputs read on-demand via JIT `access_grant{grantee, scope, expiry, revocable}`; deliverables **written to the recipient's store** (their property); attribution in the origin's logs.

### Read
Auto-fires on verify (no extra human touchpoint); rolling. All of grouping/billing/coins/quota/tax/destination/tier = config. Zero-cut: all in; only the broad external-connector catalogue is incremental.

---

## Layer 7 — AI-Composes (how a brief becomes a plan)  *(in the zero cut)*

**The efficiency engine.** This is the step that collapses ~6 manual steps (create · split · allocate · price) into one AI draft the owner ratifies. It sits between Request-intake and the owner's single ratification (Layer 2), and it feeds Layer 3's allocation.

### Principles
1. **Composes from the tenant's OWN config** — offerings, skills, levels, pricing, teams. It never invents structure; it selects and arranges what the workspace already declared. A new tenant with a thin catalog gets a thin plan; nothing EZ-specific is assumed.
2. **Per-tenant scoped · stateless · zero-retention enclave** — brief + files are read ephemerally in the sealed enclave (Layer 6); nothing is retained; the model sees only this tenant's config, never another tenant's data.
3. **Suggest → approve, never act** — the output is a *proposal*; the owner's ratification is the only thing that makes it real (vision's "AI composes → human ratifies").
4. **Federated by the boundary** — across a cross-org edge (Layer 4), each side composes within its own workspace; the composer never reaches across the boundary.
5. **Declarative templates, not hardcoded logic** — mapping rules (brief-signal → offering, complexity → level, tree shape per offering) are config/templates the admin can inspect and tune, not baked code.

### The pass (one shot, in the enclave)
```
understand brief + files
  → map to an offering + level (from THIS tenant's catalog)
  → scope: unit_type · unit_count (page/word/hour counts from the files)
  → compose the activity TREE (skills, order, dependencies, Deliver last)
  → propose a performer per activity (hands to Layer 3's engine)
  → estimate deadline (from scope + capacity + SLA bands)
  → price (only if billing on — from rate lists)
  → assemble the scope sheet + confidence + any clarifying questions
```

### Fields (AI-composed → owner ratifies)
`proposed_offering_id · proposed_level` · `proposed_activities[]{skill_id, performer_type, proposed_performer_id, input_split, dependency, unit_count}` · `scope_sheet{unit_type, unit_count, assumptions[]}` · `proposed_deadline` · `proposed_price` (gated) · `confidence` (per section) · `clarifying_questions[]` (only when a gap blocks composing) · `provenance` (which config/templates it drew from).

### Honest risk notes
- **Garbage-in** — a vague brief yields a low-confidence plan; the composer surfaces `clarifying_questions[]` rather than guessing silently. Owner ratification is the backstop.
- **Thin-catalog cold start** — a brand-new tenant with little config gets little composition; archetypes (Layer 1) mitigate by pre-seeding, but the honest floor is "as good as the config."
- **Mis-mapping** — the proposal is always editable inline (Layer 2's "Tweak"); the composer learns from edits *within the tenant* (not across tenants).
- **Not zero-retention-negotiable** — the enclave discipline is non-optional; the composer must never persist brief/file content.

---

## Zero-cut scope
**Everything in Layers 1–5 is in the zero cut** — a full-fledged generic WS that onboards on bare-min info and delivers, across entities and across workspaces. The only genuinely *constrained* items (not scoping choices): **predictive pre-mobilization** (the hook is in; prediction only works once demand history exists) and **entity→separate-WS migration tooling** (the models are in; the smooth data-separation tooling is heavier). Everything else is zero-cut.

---

## Pending Joy `[J]`
1. The real `objective_weights` (allocation reality). 2. The empty-bench fallback (external vs escalate). 3. QA policy per activity. 4. SLA at-risk policy. 5. The delivery-engine role definitions (which map to `owner/performer/reviewer/verifier`). 6. BOT/outcome billing formula.

## Decisions locked here
- Party+Relationship model · capability-gated/JIT fields · archetypes generic · 2-touchpoint lifecycle · status in-engine · propose→ratify→accept · committed-capacity-first · **WS-chat default channel + WhatsApp/SMS opt-in via adapter** · **bidding removed** · pre-mobilization hooked-but-later · **AI composes from the tenant's own config, suggest→approve, zero-retention enclave.**
