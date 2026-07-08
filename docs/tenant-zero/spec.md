# WS 3.0 — Specification

**Audience:** Joy & Bhavya (review). **Companion:** [`architecture.md`](./architecture.md) (the *how it's built*). This is the *what*: every layer field-by-field, every use case and how it runs, the locked decisions, and the open items awaiting Joy and Bhavya.

> **What this is.** WS 3.0 is a generic, multi-tenant platform for orchestrated work — onboarding an organization all the way through to delivering an assignment, across entities and across organizations. EZ is the **first tenant** ("Tenant-Zero"), configured through the same surface as any other. Nothing in this spec is EZ-specific; `(EZ: …)` marks illustrative config values only. `[J]` marks an item awaiting Joy.

**How to read this:** §1 the model → §2–§8 the seven design layers, field-level → §9 the dissolved ERP → §10 the use-case catalog and how each works → §11 locked decisions → §12 open items → §13 the approval gate.

---

## 1. The model in one page

- **Party + Relationship.** A **Party** is an Org or a Person. A **Relationship** is a typed edge between parties — `employment` / `client` / `vendor` / `tenant`. *Tenant, client, and vendor are relationship types, not separate systems.* A cross-org link is one edge seen as "vendor" from one side and "client" from the other.
- **The work graph (BAT).** `Request` (enters the workspace) → `Assignment` (a group of activities for one offering; **Deliver is the mandatory last activity**) → `Activity` (input(s) → one performer → one skill → output(s)). A Request is a **tree**: independent branches run in parallel; dependent ones wait on their input (output→input gate).
- **Two isolation keys.** `workspace_id` (separate org, crypto-isolated) and `operating_entity_id` (unit inside an org, policy-isolated). Both on every record.
- **Delivery × billing as config axes.** `delivery_model` ∈ {deliverable, retainer, outcome} decides when work rolls up to a billable event; `billing_model` ∈ {unit×price, flat_retainer, retainer+usage, outcome} decides how it's priced. A new commercial shape = a new config combination, never new code.
- **Four governing principles.** Party+Relationship · capability-gated + JIT fields · platform-generic (EZ = config) · efficiency-first (AI composes, humans ratify; edges channel-native).

---

## 2. Layer 1 — Onboarding

**Model:** onboard a **Party once**, attach a **Relationship** with its own config. The fields below are the *only* ones asked; everything else is a default, a ratification, or deferred to first use (JIT).

### Fields by party — always-asked vs gated/JIT

**Tenant (org + workspace) — set by L0 operator:**
`org legal/display name` · `org_code` · `region` · `deployment_tier` · `admin_email`. *(BYOK keys only if regional/sovereign; `modules_available`.)*

**Operating entity — L1 admin:** always `legal_name · code · country`.
- **"Bill clients through WS?"** → **Yes:** `billing_currency · tax_profile · invoice_prefix`. **External:** connector only. **No:** nothing asked.
- **"Pay performers through WS?"** → **Yes:** payout / `bank_details` (JIT at first payout).

**Person — L1 invites → self-completes:** always `name · email · party_role`.
- `contract_type · operating_entity` → only if on WS payroll · `skills` → only if a performer · `cost/pay` (encrypted) → only if paid through WS · `bank` → JIT at first payout.

**Client (deliver to) — L1:** always `company_name · code · one requester (name+email)`.
- `pricing / invoice_code / wallet` → **only if billing through WS**, JIT at first request.

**Vendor (dispatch to, cross-org) — L1:** always identity only — `vendor_type` (+ name/contact, or a **WS-tenant link**).
- `dispatchable_scope` → **default "any," JIT-narrowed** · `cost/rate` → **at first dispatch** · `boundary_review = mandatory`, `transparency = opaque` (defaults).

### Archetypes (the efficiency move)
A generic **industry starter kit** — translation / creative / research / generic — pre-seeds catalog + skills + roles + SLA/pricing bands; the admin **ratifies** rather than authoring from blank. Generic industry knowledge only — **never EZ's proprietary templates**. Optional ("Generic" = near-empty).

### Readiness engine
Computes "can deliver" live and asks only for the gaps: `entity · offering + skills + Delivery-skill · team · people · client/requester` (+ `pricing/wallet` *only if billing on*). The workspace flips to **Operational** when the chain is satisfied, then deepens JIT.

---

## 3. Layer 2 — Work Lifecycle

### What a human actually types, across the whole lifecycle
- **Requester:** `brief · files · deadline`
- **Owner:** *Approve* (or edit, only to change the AI plan) — **touchpoint #1**
- **Performer:** *Accept* + the `output`
- **Reviewer:** *Pass / Fail* (only if human QA)
- **Verifier:** *Confirm* — **touchpoint #2**

Everything else is AI-composed or system-derived. **Net human touchpoints = 2.**

### Fields by record (source · when)
- **Request:** `id · requester_id · entity_id` (system) · `brief · input_files[] · deadline` (**requester**, always) · `source_channel · engagement_id · stage/state/status` (system).
- **Assignment (AI-composed → owner ratifies):** `offering_id · level` · `unit_type · unit_count` · `delivery_model · billing_model` (config) · `owner_id` · `price` (*gated*, JIT) · `invoice_code · payment_type` (*gated*) · `deadline` (AI→override) · `stage/status`.
- **Activity:** `skill_id · performer_type · performer_id` (AI→accept) · `input_files[] · dependency · unit_count · start_by/deliver_by` (AI) · `sort_order` (system, Delivery last) · `qa_policy` (config) · `outputs[]` (**performer**) · `progress` (auto) · `stage/status` (system, **derived in-engine — no drift**).
- **Delivery:** `deliverable` (system) · `boundary_signoff` (**owner**) · `delivered_to_store` (system).
- **Verify:** `reconciliation` (AI pre-computes) · `verified_by · confirm` (**verifier** — the gate) · `notes`.
- **Bill & Pay:** `billable_event` (system, on verify) · `payout[]` (rolling) · `invoice` (*only if billing through WS*) · `pushed_to_external` (connector).

### State machine
```
Request     : created → live → delivered → verified → billed   (+ paused, cancelled)
Assignment  : created → published → delivered → verified
Activity    : created → published → delivered
Status (derived in-engine): not_started · on_track · slightly_delayed · critical · … completed
             roll-up = worst-of over the tree
```
**Key change vs WS 2.0:** status is derived in the same transaction/event as the state change → no async drift, no repair crons.

---

## 4. Layer 3 — Allocation

### The engine (per activity)
- **Pass 1 — hard filters (platform):** required `skill + proficiency` (+ language/domain) · available · not conflicted · tier-eligible.
- **Pass 2 — weighted score (objective; weights = tenant config `[J]`):** `fit · quality_to_cost · committed_capacity_first · deadline_confidence · responsiveness` → propose top-1 (named) + alternates, with reasons.

### Committed-capacity-first (the economic rule)
Fixed-cost resources — salaried experts (to quota), retainer teams, owned tool licenses — have ~$0 marginal cost → **saturate them before variable freelancers.** Ties to the quota/coins model (config).

### Three agency gates
1. **AI proposes** the named performer (at plan-ratify).
2. **Owner ratifies** → accept · swap to an alternate. **(No bidding — removed per Bhavya.)**
3. **Performer accepts/rejects** — one tap.

### Mobilization (channel-native)
- **Default = WS-chat + push** (free, native one-tap, reuses WS 2.0 `chat-v2`).
- **User-selectable fallbacks = WhatsApp / SMS** (paid; tenant/user turns on).
- **One channel-adapter interface** — the platform emits "mobilize + one-tap payload"; adapters deliver. Routing: WS-chat → (no response) → WhatsApp → SMS/call. **Pay for costly channels only when the free one fails.**
- **Predictive pre-mobilization** — *hook designed now, shipped later* (needs demand history): a soft, non-binding availability ping ahead of known demand; feeds deadline-confidence/responsiveness. Not zero-cut.

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
- **Allocation Policy (config, once):** `objective_weights{…}` (defaults, tunable `[J]`) · `hard_filters` (platform) · `fallback_policy{on_exhaust: external | escalate}` · `escalation_window` · `channel_policy{default: ws_chat, optional:[whatsapp, sms]}`.
- **Per-activity:** `candidates_scored[] · proposed_performer_id · alternates[] · reasons` (AI) · access `{subject_id, role_type=activity, role_status(pending→accepted/rejected), reject_reason}` (**performer tap**) · `mobilization{channel, sent_at, response, escalation_step}` (system).

---

## 5. Layer 4 — Cross-Org / Boundary

**The insight:** a cross-WS connection is **one Relationship edge** — "vendor" from one side, "client" from the other. No separate cross-org machinery.

- **Handshake:** WS-A onboards a vendor with `vendor_type = WS-tenant` → `linked_org_ref` (B) · `dispatchable_scope` (default *any*) · `cost_terms` (JIT) · `transparency_granted` · `operating_entity` (A-side). B accepts → sees an incoming **client** (`pricing_to_A`, `SLA`, `transparency_ceiling`). `connection_type`: WS-native | adapter (email/Phrase/API).
- **Request crossing:** in A's graph the performer = **"WS-B", one opaque boundary node** (`boundary_node_id → maps_to: request_id in B`). In B's graph, a **new Request** with A as client; B runs its own lifecycle, invisible to A.
- **Visibility.** A→B crosses: brief · input files (brokered) · deadline. **Opaque to A:** B's tree, performers, method, sub-vendors, costs. B→A crosses: border-safe status roll-up · deliverable · action-items · risk. **Opaque to B:** A's other vendors/entities.
- **Brokered files:** inputs stay in A's store; B gets a **JIT scoped credential** (`access_grant{scope, grantee, expiry, revocable}`); deliverable **written into A's store**; attribution in A's logs.
- **Transparency dial (config):** default **opaque**; B may raise per relationship (`opaque → milestones → detailed`) — the vendor controls its ceiling.
- **Mandatory boundary review:** `boundary_signoff` (B's owner) + **provenance stripped** before crossing.
- **Chains (A→B→C):** each hop re-encapsulates — **A never learns C exists.**
- **Fields:** `relationship_id · {workspace_A, role=vendor} · {workspace_B, role=client} · linked_org_ref · operating_entity (A) · status` · A-cfg `{scope, cost, transparency_granted}` · B-cfg `{pricing, SLA, transparency_ceiling}` · `boundary_review_policy · connection_type`. Boundary node: `boundary_node_id · maps_to · visible_status · deliverable_ref · opacity_level`.

---

## 6. Layer 5 — Multi-Entity & the Entity-vs-Workspace choice

**The rule:** **Entity = a billing/legal unit inside one org, policy-isolated. Workspace = a separate org/tenant, crypto-isolated.** The client picks how many of each; the same engine runs under both.

- Every relationship/work/wallet record carries **`operating_entity_id`**; access scoped by `(workspace_id, operating_entity_id)`.
- **Default isolated:** sibling entities don't see each other's relationships or work. *(Entity-1 does not learn Entity-2 is a vendor to Org B's Entity-3.)*
- **Org admin sees all** across entities — unless entity-delegated module-admins (`module_admin_scope = entity`) blind even the admin. `entity_isolation` flag defaults to **isolated**; an org can flip it to share.
- **The mirror:** external Org B sees **only** the entity it works with — never the org's other entities.

| | Entities in one WS | Entity as its own WS |
|---|---|---|
| Isolation | policy (need-to-know + scoping) | **cryptographic** (separate tenant, BYOK) |
| Sibling can see? | no by default (admin can) | **no — can't** |
| Config/people/catalog | shared | fully separate |
| Tier/keys | same | can differ (e.g. sovereign) |

- Pick **one-WS** when entities share ops and policy-isolation suffices; **separate-WS** for a hard wall, own keys/tier, or a distinct operation.
- **Separate ≠ cut off** — a separated entity still links back via the cross-org boundary (Layer 4).
- **Migratable** — start entities-in-one-WS, split one later. *Honest note:* splitting into a crypto-isolated/BYOK workspace is a **data-separation operation**, heavier than a config toggle.

---

## 7. Layer 6 — Money & Files

**Control plane, not data plane:** WS orchestrates the **money events** and holds **file pointers**; money-custody and bytes can live elsewhere.

- **The decoupling:** at **Verify**, WS emits one **billable event** → fans out to two **independent, capability-gated** sides: client **invoicing** (money in) and performer **payout** (money out). A performer is paid off *verified work*, not off client payment.
- **Billable event (always):** `billable_event_id · assignment_ref · verified_by/at · unit_count · unit_price · amount · currency · billing_model · operating_entity_id · client_relationship_id`.
- **Client side — invoicing** *(gated: "bill through WS?")* — pluggable destination: **WS module** (generate) · **external connector** (push the event to their system) · **data-out** (API/webhook).
  - WS invoice: `invoice_number · grouping_rule` (config — per-entity-per-period / per-request; *EZ's "1/entity/month" is a value*) `· rate_snapshot · line_items[] · tax` (from entity `tax_profile`) `· status`.
  - External: `pushed_to_external{system, external_ref, status}` — no WS invoice.
- **Wallet / credits** *(gated: prepaid)* — `Wallet{balance, cost_per_credit}` · `WalletLot{credits, remaining, validity}` (FIFO) · **`WalletLedger` (immutable — the source of truth, no sheet mirror)**. Deduct at assignment-create → settle at verify → refund on cancel.
- **Expert side — payout** *(gated: "pay through WS?")* — `payout{performer_id, period, amount/coins, source=billable events, status}`. Value unit + quota/incentive = **config** *(EZ: coins, quota×1.1)*. If not via WS → export to their payroll.
- **Files:** the graph holds `file_ref{store_location, key, checksum, size, mime, owner_entity}` — a **pointer, not bytes**. Storage tiers (config): WS-managed · connected cloud · own infra (sovereign). **Enclave (zero-retention):** bytes pulled ephemerally → compute → return → retain nothing; access flows to the tool, never a person. **Brokered access** as in Layer 4.
- **Read:** auto-fires on verify (no extra touchpoint); rolling. All of grouping/billing/coins/quota/tax/destination/tier = config.

---

## 8. Layer 7 — AI-Composes (how a brief becomes a plan)

**The efficiency engine** — collapses ~6 manual steps (create · split · allocate · price) into one AI draft the owner ratifies. Sits between intake and the owner's single ratification; feeds Layer 3.

- **Principles:** composes from the tenant's **own** config (never invents structure) · per-tenant scoped, stateless, **zero-retention enclave** · **suggest → approve, never act** · federated by the boundary (each side composes within its own workspace) · declarative templates the admin can inspect/tune (not hardcoded logic).
- **The pass (one shot, in the enclave):**
  ```
  understand brief + files → map to offering + level (from THIS tenant's catalog)
    → scope (unit_type · unit_count from the files) → compose the activity TREE
    → propose a performer per activity → estimate deadline → price (if billing on)
    → assemble scope sheet + confidence + clarifying questions
  ```
- **Fields:** `proposed_offering_id · proposed_level` · `proposed_activities[]{skill_id, performer_type, proposed_performer_id, input_split, dependency, unit_count}` · `scope_sheet{unit_type, unit_count, assumptions[]}` · `proposed_deadline` · `proposed_price` (gated) · `confidence` (per section) · `clarifying_questions[]` · `provenance`.
- **Honest risks:** vague brief → low-confidence plan + clarifying questions (never a silent guess); thin-catalog cold start → a thin plan (archetypes mitigate; the floor is "as good as the config"); mis-mapping → always editable inline; the zero-retention discipline is non-negotiable.

---

## 9. The dissolved ERP — improve, don't port

The EZ ERP is **dissolved and improved**. Per-domain keep / kill / redesign (full detail in `03-domain-redesigns.md`):

| Domain | Keep | Kill | Redesign to |
|---|---|---|---|
| **Wallet / Credits** | FIFO immutable ledger, idempotent ops | Sheet mirror + drift crons, hardcoded lists | Ledger = the single live utilization source; negative-balance = config |
| **Invoicing** | 1 group / entity / month, rate-snapshot, audit | cross-service intake hop, brittle xlsx→PDF | In-lifecycle invoice event; tested tax/currency engine; templated PDF |
| **Payroll / Comp** | encryption, PPR multiplier, effective-dating | xlsx imports, per-person env rules, untested math | Config-driven statutory engine (rules as data); fed by live data; tested |
| **People / Identity** | effective-dated history | derived passwords, CASCADE team FK, money-as-CharField | Proper identity + invite/SSO-ready; typed money; safe FKs |
| **Skills / Quota / Coins** | coins normalization, quota/incentive | Sheet-loaded rates, signal-magic recompute | First-class config rate lists; explicit tested recompute |
| **Leave / Attendance** | comp-off FIFO, entity accruals | Sheet biometrics, role-by-string-match | Device/event attendance; real roles; accruals as config |
| **Timesheet** | charge-code concept | manual charge sheets, separate Jira pull | **Auto-derived from the unified activity logs** |
| **PPR** | generated-column pattern | hardcoded exclude-list | Config grade-curve; explicit tested PPR→comp link |
| **Offboarding** | NOC checklist | daily-cron emails, parallel Google-Form path | Event-driven; single exit path; templated letters |
| **Sales / CRM** | funnel, pricing setup | signal-sync + rollback-by-delete | No sync (one system); local transactional; one pricing record |

**Four structural rethinks above the domains:** kill the ERP↔WS boundary (one graph, zero sync) · kill Sheets-as-database · kill the ~132 hand-run commands (→ UI + validated APIs + real task queue) · one lifecycle engine + config-not-code.

---

## 10. Use-case catalog — and how each works

`P1` = Phase 1 (EZ single-tenant) · `P2` = Phase 2 (cross-org) · `X` = cross-cutting. This is the coverage map the design must hold, with a one-line "how it runs."

### A · Platform & onboarding
- **A1** `P1` L0 provisions a workspace — 3 fields (org name · tier · admin email) mint a tenant; BYOK only if sovereign. *(Layer 1)*
- **A2** `P1` Admin configures to "can deliver" — the readiness engine drives the config chain; JIT for the rest.
- **A3** `P1` EZ onboarded as Tenant-Zero **through the same flow — no back-door.**
- **A4** `P1` One org, many entities in one workspace (EZ's 3) — `operating_entity_id` scoping.
- **A5** `X` Smart onboarding — archetype skeleton → ratify → JIT gap-fill.

### B · Identity & roles
- **B1** `P1` Admin invites users into roles (manual for v1).
- **B2** `P2` Portable root identity + SSO federation.
- **B3** `P2` Freelancer authenticates against own identity, approved into orgs.
- **B4** `X` Need-to-know POV-scoping per role.
- **B5** `P1`* **Entity-level need-to-know within a workspace** — the primitive built now (forced by G4).

### C · Catalog & config
- **C1–C6** `P1` Offerings (delivery×billing) · skills + rates + mandatory Delivery skill · teams/roles (SWAT/QA/SME/pool as config) · pricing/invoice codes · SLAs/allocation/transparency/terminology · module activation. **C7** `X` versioned catalog restructuring.

### D · Intake
- **D1** `P1` Manual request. **D2** `P1` Phrase adapter (1 Project = 1 Job = 1 Request). **D3** `P1` Email auto-create (1 thread ↔ 1 request). **D4** `X` ambient AI brief → offering mapping. *All land as a `Request` with a `source_channel`.*

### E · Delivery (the lifecycle) — the core
- **E1** `P1` **Deliverable flow (Type A).** Brief+files → AI composes the plan → owner ratifies (touchpoint 1) → activities fan out → perform → policy QA → assemble → deliver → verifier confirms (touchpoint 2) → bill+pay.
- **E2/E3** `P1` **Retainer / Outcome (Type B).** Same engine; "complete" = a **service period** closes (retainer) or a period closes + outcome metric measured (BOT). Billed per period.
- **E4** `P1` File split → parts → activities (EZ: TR/PR/QA) — the composer's tree.
- **E5** `P1` Allocation & mobilization — propose→accept, one-tap, channel-native.
- **E6** `P1` Agent-as-performer (Flip/MT/OCR) — allocated like a performer; agent→human-QA.
- **E7** `P1` Human + mandated tool (TR42, Canva) — the license broker.
- **E8** `P1` Nested / sub-assignment + dependencies (output→input gate).
- **E9** `P1` Deliver → boundary review → **Verify (TL sign-off)** → invoice → payout.
- **E10** `P1` Auto-delivery (owner shortcut where policy allows).

### F · Change & exceptions
- **F1** scope change mid-flight (edit-levels) · **F2** reassignment (fee-split; EZ never funds overrun) · **F3** cancel/pause (wallet refund on cancel) · **F4** goodwill revision post-completion (**new linked assignment, no claw-back**) · **F5** disputes · **F6** recurrence.

### G · Cross-org (Phase 2 — the EY scenario)
- **G1** `P2` a client orchestrates multiple vendors · **G2** `P2` **EZ as a vendor inside a client's tenant** (method stays invisible) · **G3** `P2` per-relationship transparency dial (EY-3↔EZ ≠ EY-4↔EZ) · **G4** `P2` **EY-3 must not know EZ also works with EY-4** → forces B5 · **G5** `P2` encapsulation (opaque boundary node) · **G6** `P2` brokered inputs / transferred deliverables / attribution. *All = Layer 4 + Layer 5.*

### H · Commercial & financial (absorbed ERP)
- **H1** wallet/credits (FIFO ledger) · **H2** invoicing (1 group/entity/month) · **H3** expert payout (coins/quota/incentive) · **H4** payroll — statutory (India PF/ESIC/TDS, UAE WPS) as **config** · **H5** People/HR, Leave, Timesheet, PPR, Offboarding.

### I · Cross-cutting
- **I1** ambient inline AI (suggest→approve; no chat panel) · **I2** channel-native notifications · **I3** reliable reporting (one engine → no drift, no repair crons) · **I4** tenant-inspectable audit; server-authoritative access.

---

## 11. Locked decisions

Party+Relationship model · capability-gated + JIT fields · archetypes generic (never EZ templates) · **2-touchpoint lifecycle** (ratify plan, confirm verify) · status derived in-engine (no drift/crons) · propose→ratify→accept · committed-capacity-first · **WS-chat default channel + WhatsApp/SMS opt-in via one adapter** · **bidding removed** (per Bhavya) · pre-mobilization hooked-but-later · **AI composes from the tenant's own config, suggest→approve, zero-retention enclave** · pluggable invoicing destination (WS / external / data-out) · entity-vs-workspace is the client's choice, both interoperable & migratable · dissolve-and-improve the ERP (not port).

---

## 12. Open items — awaiting Joy & Bhavya

**Joy `[J]`:** (1) real `objective_weights` for allocation · (2) empty-bench fallback (external vs escalate) · (3) QA policy per activity · (4) SLA at-risk policy · (5) delivery-engine role definitions mapping to owner/performer/reviewer/verifier · (6) BOT/outcome billing formula · (+ delivery archetypes 02–06, statutory matrix).

**Bhavya:** tenant isolation mechanism (incl. entity-level) · transactional vs event-sourced engine · GraphQL gateway + persisted queries · async infra · stack confirmation.

**None of these reshape the design** — they fill parameters at marked holes.

---

## 13. The approval gate

Approving this spec + `architecture.md` means: the model, the seven layers, the isolation design, the use-case coverage, and the dissolve-and-improve ERP direction are correct to build against. The only open items are the Joy/Bhavya inputs in §12, which slot into marked holes.

```
APPROVE spec.md + architecture.md
      ├─ Joy answers [J] ──┐
      ├─ Bhavya answers ───┤→ ARCHITECTURE v2 → sign-off
      └─ parity-test catalog + migration mapping (last solo pieces)
                 ▼
        BUILD (on Shreyanshi's "go")
        scaffold → typed model → PARITY TESTS FIRST → migration →
        Phase-1 features → strangler-fig cutover → Phase 2 (cross-org)
```

**The ask:** review §1–§10; flag anything wrong or missing; approve to lock the design. Detailed prior specs live in `00`–`05` and the two `.mmd` flowcharts; this spec + `architecture.md` are the consolidated entry point for review.
