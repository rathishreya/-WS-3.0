# WS 3.0 — Config Surface · Data Model · Cross-cutting

> What the WS-admin configures + the typed schema + AI/notifications/access/audit/integrations.

---

# WS 3.0 — The WS-Admin Config Surface

**What the workspace admin (L1) configures — every knob, declaratively.** This is the operational proof of "configure everything, hardcode nothing." Each config object lists its fields, defaults, and the **readiness rule** that unblocks delivery.

**Principle:** every object is *declarative* (chosen/tuned values, never logic), has *sane defaults*, and can be pre-seeded by an *archetype skeleton* + AI-assist. The admin ratifies, doesn't fill blank forms.

---

## The config object model (overview)

```
Workspace (L1)
├── Foundation
│   ├── Organization        (identity, brand, terminology)
│   ├── OperatingEntity[]    (legal/billing units — EZ Lab / AEZ / CASPR)
│   └── DeploymentTier       (shared/regional/sovereign + keys)
├── Operating Model
│   ├── Catalog: Division → Capability → Offering (+ delivery/billing model)
│   ├── Skill[] + RateList[] (+ the mandatory Delivery skill)
│   ├── Team[] + Role[]      (the delivery engine — SWAT/QA/SME/pool as config)
│   ├── SLAPolicy[]          (10:20:30-style, per tier/service)
│   ├── AllocationPolicy     (the weights)
│   ├── TransparencyDefault  (the opacity dial floor)
│   └── ModuleActivation[]   (which first-party modules are on)
├── Relationships
│   ├── ClientRelationship[] (per-client terms, per-relationship transparency)
│   ├── PricingRecord[]      (invoice codes, payment type)
│   └── QAReferenceData[]    (per-client knowledge)
└── Live Operations
    ├── Person[] + roleassignment (experts/SWAT/requesters)
    ├── Wallet[]             (prepaid funding)
    ├── Integration[]        (TR42, Phrase, email, payment gateway…)
    └── NotificationPolicy[] (channel-native rules)
```

---

## Foundation layer (rare — the admin, seldom changed)

**Organization** — `name`, `code` (immutable), `brand` (colors/logo tokens), `terminology_map` (org's own words → platform concepts), `default_currency`.
**OperatingEntity[]** — `name`, `code` (immutable), `billing_currency`, `tax_profile` (VAT/WHT/none + %), `invoice_prefix`, `allowed_currencies[]`. *One org → many.*
**DeploymentTier** — `tier` (shared|regional|sovereign, default **shared**), `keys` (BYOK at regional/sovereign).

*Readiness:* ≥1 OperatingEntity exists → invoicing/wallet can be configured.

---

## Operating-Model layer (the core — seeded, evolves)

**Catalog** — `Division[] → Capability[] → Offering[]` (many-to-many capability, primary/secondary).
- **Offering** fields: `name`, `capability[]` (primary+secondary), `levels[]`, `skills[]`, `type_of_unit`, `source/target_lang`, **`delivery_model`** (deliverable|retainer|outcome, default *deliverable*), **`billing_model`** (unit_x_price|flat_retainer|retainer_plus_usage|outcome), `cadence` (if recurring), `completion_rule`, `selling/min/optimal_price`, `est/researched_cost`, `description` (AI-generated if blank).
- **Level** (within offering): `name`, optional own `price` / `skills` / `QA_rule` / `SLA` — `⚠️ J10` first-class vs descriptive.

**Skill[]** — `name`, `proficiency`, `type_of_unit`, `src/tgt_lang`, `country`, `selling/cost_price`, `units_per_hour`, `incentive_pct`. Plus the **mandatory `Delivery` skill** (seeded, not invented).
**RateList[]** — `skill`, `coins_per_unit`, `incentive_pct`, `effective_date`. *(Config object — no more Google-Sheet loading.)*

**Team[] + Role[]** — the delivery engine as config. `Team` = `name`, `capability?`, `members[]`, `parent?`. `Role` = a *named instance* of a platform role-type (request/assignment/activity access) — e.g. EZ maps "SWAT" / "QA" / "SME" / "pool" onto the primitives here. `⚠️ J1` needs Joy's definition to seed EZ's set.
**SLAPolicy[]** — `name`, `tiers` (the 10:20:30 semantics `⚠️ J9`), `applies_to` (tier/service/level), `deadline_rules`.
**AllocationPolicy** — weights for `fit · quality_to_cost · committed_capacity_first · deadline_confidence · responsiveness` (defaults from vision §4.5; tunable). `⚠️ J12`.
**TransparencyDefault** — `floor` (opaque default), per-relationship override allowed.
**ModuleActivation[]** — which first-party modules are on (Delivery, Invoicing, Wallet, People, Payroll, Leave, Timesheet…), bounded by L0's availability.

*Readiness:* ≥1 Offering + its Skills + Delivery skill + a Team with an Expert → work can be created & allocated.

---

## Relationships layer (per-client — as formed)

**ClientRelationship[]** — `client`, `entity`, per-relationship `terminology_equivalences`, `transparency_level` (raises the floor), `sla_override`. **Entity-scoped isolation flag** (from the EY case) — controls whether sibling operating-entities can see this relationship (default **isolated**).
**PricingRecord[]** (invoice codes) — `entity`, `offering_pricing[]`, `currency`, `payment_type` (prepaid|postpaid), `valid_from/till`, auto-generated `invoice_code`.
**QAReferenceData[]** — per-client reference the in-scope AI retrieves (distinct from cross-tenant training).

*Readiness:* a PricingRecord whose invoice_code matches the assignment → assignment can be created & priced.

---

## Live-Operations layer (frequent — delegated module-admins)

**Person[]** — identity + `role_assignments[]` (which Team/Role, which capability) + `skill_assignments[]` (PeopleSkill: skill, quota_type, quota_data). *Manual create/invite now; SSO-ready.*
**Wallet[]** — `entity`, `requesters[]`, funded lots (prepaid). *Ledger-based, no sheet.*
**Integration[]** — `type` (TR42|Phrase|email|payment_gateway|…), `config`, `enabled`. Tier-gated (sovereign blocks egress tools).
**NotificationPolicy[]** — channel (WhatsApp/SMS/email/in-app), `recipient_rules` (role+role_type+status — configurable, *no more @mckinsey hardcode*), `template`, per-client overrides.

*Readiness:* a funded Wallet (if prepaid) + Experts with the offering's skills → the first assignment flows to delivery.

---

## The readiness engine (how "onboarded = can deliver" is enforced)

The system knows the dependency chain and computes a **live readiness state** per workspace:

```
can_create_request  ⟸ Person(requester) + permission
can_create_assignment ⟸ Offering + PricingRecord(matching invoice_code) + (Wallet if prepaid)
can_allocate         ⟸ Team + Expert with matching Skill
can_deliver          ⟸ Delivery skill + all above
can_invoice          ⟸ PricingRecord + billing_model
──────────────────────────────────────────────
WORKSPACE OPERATIONAL ⟺ all of the above satisfied for ≥1 offering
```

The admin UI surfaces exactly what's missing ("offerings ✓, experts ✓, **no funded wallet — prepaid delivery blocked**"). Deeper config (more offerings, SLAs, experts) is JIT-enriched after operational.

---

## Config change discipline
- **Versioned** — catalog restructuring (rename/merge/move offerings) is safe & reversible; history preserved.
- **Effective-dated** — rate/pricing changes apply at cycle boundaries, never mid-flight (carried from the good ERP primitive).
- **Delegated** — Foundation locked to the primary admin; Live-Ops delegable to module-admins (§9.2).
- **Audited** — every config change is tenant-inspectable.

---

# WS 3.0 — Typed Domain Model

**The schema the build stands on.** Replaces WS 2.0's loose JSONB `.get().get()` chains with typed entities. Grouped by area. Types are indicative (final types settle with Bhavya's DB-topology call).

**Conventions:** every entity is workspace-scoped (`workspace_id`) and most are entity-scopable (`operating_entity_id`) for the isolation model. Money is `Decimal`, never string. Timestamps + soft-delete (`is_disabled`) standard. IDs are typed.

---

## 1. Platform & tenancy

```
Workspace        { id, org_id, deployment_tier, status, created_at }
Organization     { id, name, code!, brand, terminology_map, default_currency }
OperatingEntity  { id, org_id→, name, code!, billing_currency, tax_profile{type,pct,reg_no},
                   invoice_prefix, allowed_currencies[], is_disabled }
```
`!` = immutable after create. **Isolation boundary = (workspace_id [, operating_entity_id])** — see §9.

## 2. Identity, roles, access

```
User        { id, email!, identity_ref (SSO-ready), status }
Person       { id, workspace_id→, user_id→, name, contract_type, operating_entity_id→,
               reporting_manager_id→self, employment_status, salary_data(encrypted) }
Role         { id, workspace_id→, name, role_type∈{request,assignment,activity,admin},
               capability_id?→ }              # named instance of a platform role-type
RoleAssignment { id, person_id→, role_id→, team_id?→, scope }
Access       { id, workspace_id→, subject(role|person), resource, action,
               entity_scope?, field_permissions{} }   # server-authoritative RBAC (replaces frontend JSON)
```
**Role-type = platform primitive; Role (name) = tenant config.** EZ's SWAT/QA/SME/pool are `Role` rows.

## 3. Catalog

```
Division    { id, workspace_id→, name }
Capability  { id, division_id→, name }
Offering    { id, workspace_id→, name, level_set_id?→,
              capabilities[]→ (primary + secondary),          # M2M
              type_of_unit, source_lang, target_lang, skills[]→,
              delivery_model∈{deliverable,retainer,outcome},
              billing_model∈{unit_x_price,flat_retainer,retainer_plus_usage,outcome},
              cadence?, completion_rule,
              selling_price, min_price, optimal_price, est_cost, researched_cost,  # Decimal
              description, is_disabled }
Level       { id, offering_id→, name, price?, skills[]?, qa_rule?, sla_id?→ }   # first-class ⚠️J10
```

## 4. Skills, coins, quota

```
Skill     { id, workspace_id→, name, proficiency, type_of_unit, source_lang, target_lang,
            country, selling_price, cost_price, units_per_hour, incentive_pct }   # Decimal
RateList  { id, workspace_id→, skill_ref, coins_per_unit, incentive_pct, effective_date }
PeopleSkill { id, person_id→, skill_id→, quota_type∈{unit,range,skill_quota,project,single_ctc},
              quota_data{ coins_normal_unit, total_coins, quota_per_month }, is_disabled }
```
Coins = expert-side normalizer (kept). Credits = client-side (§7). Independent scales.

## 5. The work graph (unchanged BAT, typed)

```
Engagement    { id, workspace_id→, operating_entity_id→, client_relationship_id→,
                delivery_model, billing_model, committed_resource_id?→, status }   # §04
ServicePeriod { id, engagement_id→, period_start, period_end, status,
                verified_by?→, invoice_id?→ }        # recurring models only
Request       { id, engagement_id→, workspace_id→, operating_entity_id→,
                stage, state∈{draft,live,delivered}, status, created_by→ }
Assignment    { id, request_id→, offering_id→, parent_id?→self,   # nesting
                invoice_code_ref, payment_type, unit_count, stage, status,
                assignment_delivery_at }
Activity      { id, assignment_id→, skill_id→, performer_type∈{human,agent,human_tool},
                sort_order, unit_count, stage, status, progress,
                outputs[]{file_ref,is_interim}, input_files[]{file_ref,dep_activity_id},
                start_by, deliver_by }
WRUA          { id, request_id→, subject_id→, role_type∈{request,assignment,activity},
                role_status∈{pending,accepted,rejected}, node_ref }   # access on the graph
```
- **Deliverable**: Engagement holds one Request. **Retainer/outcome**: Engagement spawns a ServicePeriod each cadence; the period is the billable unit.
- `stage/state/status` are typed enums (dead statuses pruned — `⚠️ D1` Joy).

## 6. State enums (typed, from Joy's `01-core-delivery`, pruned)

```
Stage(Request)    : request_created → assignment_created → assignment_published
                    → deliver_assignment → verified → marked_complete
                    (+ draft, paused, cancelled)
Stage(Assignment) : assignment_created → published → deliver → verified → marked_complete
Stage(Activity)   : activity_created → published → delivered
State             : draft → live → delivered
Status (derived)  : not_started, on_track, slightly_delayed, critical,
                    on_time_completed, slightly_delayed_completed, delayed_completed,
                    paused, cancelled     # roll-up = worst-of; ordering ⚠️D1 (Joy confirms)
```
**Key change vs WS 2.0:** status is derived **in the same transaction/event as the state change** (one engine) — not an async pipeline → no drift, no `fix_*_conflicts`.

## 7. Money (redesigned — one system, ledger-based)

```
Wallet       { id, operating_entity_id→, requesters[]→, total_balance,
               cost_per_credit, wallet_type∈{shared,personal} }
WalletLot    { id, wallet_id→, type∈{purchase,promotional}, total_credits, remaining_credits,
               cost_per_credit, valid_from, valid_to, status }
WalletLedger { id, wallet_id→, txn_type∈{add,deduct,refund,expire,transfer},
               credits, balance_after, assignment_ref, data }   # immutable, FIFO — the SOA source
Invoice      { id, operating_entity_id→, group_id, invoice_number?, invoice_cycle,
               status, billing_model, currency, rate_snapshot, totals{...}, verified_by→ }
InvoiceItem  { id, invoice_id→, offering_ref, unit_count, unit_price, discount, amount }
Payout       { id, person_id→, period, coins, amount, status }   # expert payment
```
- **1 Invoice Group = 1 invoice / entity / month** (kept).
- Invoice fires on **Verify** (explicit gate), not on mark-complete — resolves `⚠️ D4`.
- Ledger is the single utilization/SOA source — no Google-Sheet mirror.

## 8. Absorbed HR domains (typed, redesigned — see `10`)
`Payroll`, `Compensation`, `Leave`, `Attendance`, `Timesheet`, `PPR`, `Offboarding` — modeled as first-party modules, statutory rules as **config data** not code, live-data-fed (no xlsx imports). Detailed target models in `10-domain-redesigns`.

## 9. Isolation model (feeds Bhavya `08`)
Every entity carries `workspace_id`; work + relationship entities also carry `operating_entity_id`. Isolation is enforceable at **both** levels — so two operating-entities in one workspace (the EY case) can be mutually invisible on the relationship dimension. `❓ Bhavya:` DB-shard-per-workspace vs RLS vs schema — but **the model exposes the entity-level key regardless**.

## 10. What this kills
- JSONB `data.get().get()` chains → typed fields.
- Money-as-`CharField` → `Decimal`.
- Two `Team` tables → one.
- Async status pipeline → in-engine derivation.
- ERP↔WS sync tables → one graph.
- Google-Sheet mirrors → the ledger/DB is the source.

---

# WS 3.0 — Cross-Cutting: Ambient AI · Notifications · Access · Audit

The concerns that touch every workflow. Kept in one place so they stay consistent.

---

## 1. Ambient AI (suggest → approve; never a chat panel)

**Principle (vision §2.4):** AI is a property of the surface, inline and dismissible, confidence-gated — never a persistent panel or popup. Runs in the enclave, per-tenant, stateless, inheriting the user's exact scope (AI POV = user POV).

**Touchpoints in the journey:**
| Where | AI does | Autonomy |
|---|---|---|
| Request intake | brief → proposes the right offering + level inline; asks "X or Y?" only if ambiguous | suggest→approve |
| Scope | reads the file in the enclave → non-confidential scope sheet (counts, complexity, per-expert deadline estimate) | suggest |
| Allocation | proposes a named allocation with reasons | owner ratifies |
| Onboarding/config | proposes catalog/skills/teams from the archetype skeleton | admin ratifies |
| Status | border-safe status roll-up + risk/exception propagation for the requester | surfaced |
| Verify | pre-computes the reconciliation for the TL | TL signs off |

**Metering:** AI priced in abstract credits, tenant-pooled, wallet overage with soft-stop (never kill mid-deliverable). (Commercial detail parked; the metering hook is designed in.)

---

## 2. Notifications (channel-native)

**Principle:** the edges are lightweight and external — mobilization, one-tap accept, approvals, status pings happen in WhatsApp/SMS/email; many users rarely open the app.

- **Config-driven recipient rules** — role + role_type + status, **configurable per client** (the `@mckinsey.com` silent-drop and exclude-lists become tenant config, not code).
- **Both switches** (template-allows AND user-setting-allows) preserved as config.
- **Event-driven delivery** via a task queue with retry/audit — not fire-and-forget threads. No more silent "client never got the notification."
- **Channels:** WhatsApp/SMS (mobilization, one-tap accept), email (intake/threading), in-app (deep work).

---

## 3. Access / RBAC (server-authoritative)

- **Server-authoritative** — the access decision lives on the server; the client computes optimistically for UX only (kills the WS 2.0 frontend access-JSON).
- **Need-to-know POV-scoping** — each user's surface is a projection of their scope; the UI shows only their slice.
- **Two isolation levels** — `workspace_id` and `operating_entity_id` (the EY case: sibling entities mutually invisible on the relationship dimension by default).
- **JIT least-privilege credentials** for any tenant-data pull (the enclave model); short-lived, per-grant.
- **Config-driven** — no hardcoded email allowlists (timesheet/payslip/leadership) → all become RBAC config.

---

## 4. Audit

- **Tenant-inspectable, tamper-evident** log of operator/admin actions ("don't-trust-us-verify").
- **Every config change** audited (who changed what knob, when).
- **Enclave governance** — no human sees tenant bytes; no content in logs; access flows to the tool, not the person.

---

## 5. Files & the enclave (brokered, zero-retention)

- **Inputs brokered** (read on-demand from the sender's store; instant revoke); **deliverables transferred** to the client's store as their property.
- **Content processing in a sealed, zero-retention enclave** — Splitter, counts, AI reading a brief pull bytes ephemerally, compute, retain nothing.
- **Attribution by WS identity** — the client's own logs show the WS user-id that accessed their files.

---

## 6. Integrations (the Connect surface)

- **Client-system adapters** (Phrase, memoQ, Trados…) at the intake/deliver boundary — directional-per-field (no two-way sync).
- **Tool integrations** (TR42, Canva, accounting, JIRA) at the module boundary — push-out + pull-reference, never two-way-sync a field.
- **License broker** — tool licenses as a pooled, JIT-assigned resource (cost moat); tier-gated (sovereign blocks egress tools).
- **AI-agent performers** (Flip/MT/OCR) — **push/event callback**, not the WS 2.0 checkpoint-polling.
