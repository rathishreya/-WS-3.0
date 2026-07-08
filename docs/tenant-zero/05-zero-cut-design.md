# WS 3.0 — Zero-Cut Design: Onboarding · Work Lifecycle · Allocation

**The locked, field-level design** for the three core layers, from the layer-by-layer walkthrough. Platform-generic (no EZ baked); efficiency-first; capability-gated. `(EZ: …)` = illustrative config only. `[J]` = pending Joy's confirmation.

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

## Pending Joy `[J]`
1. The real `objective_weights` (allocation reality). 2. The empty-bench fallback (external vs escalate). 3. QA policy per activity. 4. SLA at-risk policy. 5. The delivery-engine role definitions (which map to `owner/performer/reviewer/verifier`). 6. BOT/outcome billing formula.

## Decisions locked here
- Party+Relationship model · capability-gated/JIT fields · archetypes generic · 2-touchpoint lifecycle · status in-engine · propose→ratify→accept · committed-capacity-first · **WS-chat default channel + WhatsApp/SMS opt-in via adapter** · **bidding removed** · pre-mobilization hooked-but-later.
