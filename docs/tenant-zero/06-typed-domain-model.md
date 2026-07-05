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
