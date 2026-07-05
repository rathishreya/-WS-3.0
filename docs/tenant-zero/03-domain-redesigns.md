# WS 3.0 — Domain Redesigns & Efficiency

> The dissolved ERP, improved not ported: as-is to to-be + keep/kill/redesign per domain.

---

# EZ — Tenant-Zero: Workflow Reconstruction & Efficiency Redesign

**Status:** Draft v1 — reconstructed by Claude from the ERP code + module docs. For Joy/Bhavya/Shreyanshi red-line.
**Purpose:** Capture how EZ works *today* (as-is, from code — not invented) and how WS 3.0 should do it *better* (to-be), so the rebuild raises efficiency instead of just re-platforming the current pain.
**Scope note:** Per the decision to **dissolve the ERP**, every workflow below becomes a first-party WS 3.0 module. Everything absorbed comes in as **Tenant-Zero configuration**, never platform core.

## How to read this
Each workflow is written as:
- **As-Is** — the current flow, reconstructed from the code/docs.
- **Pain** — specific inefficiencies, with evidence.
- **WS 3.0** — the redesigned flow.
- **Win** — the concrete efficiency gain and who benefits.
- **⚠️ Joy** — tacit gaps only a human can confirm (code can't show these).

Anything marked ⚠️ is where I'm reconstructing and need validation.

---

## Part 0 — Cross-cutting efficiency principles (apply to *every* workflow)

These seven changes lift the whole system at once. Every workflow below inherits them, so they're stated once here.

| # | Principle | Replaces (evidence) | Efficiency gain |
|---|---|---|---|
| P1 | **One source of truth — kill the Sheets shadow-DB** | ~380 hardcoded Sheet IDs; `verify_wallet_sheet`, SOA drift crons; `load_*_from_sheet` importers | No manual sheet upkeep, no reconciliation firefighting, trustworthy dashboards |
| P2 | **Config-not-code** | `AHMED_SALEH_COST_PER_COIN`, translator cap `0.006`, night-shift `150.0`, `WALLET_BALANCE_THRESHOLD=5000`, `EXCULDE_PPR_ORG_COUNT` gmail list | Ops change rules in seconds via superadmin; no dev ticket, no deploy |
| P3 | **Event-driven, not polling/threads/crons** | 7 raw `threading.Thread` side-effects; AI-agent checkpoint polling; ~132 mgmt commands; batch crons | Reliable async (retry/audit), real-time updates, fewer silent failures |
| P4 | **Server-authoritative logic** | access-control JSON in frontend; side-effects coded client-side (WS 2.0 review) | Security + correctness; the client stops being able to lie |
| P5 | **Proper UI + validated APIs replace import scripts** | ~60 `load_*` / `update_*` / `fix_*` one-off commands | Dozens of hand-run scripts (and the people running them) disappear |
| P6 | **Ambient AI in the flow** | tribal knowledge to map briefs → services; manual scoping | Juniors/clients raise correct requests; senior people freed |
| P7 | **Rolling, not batch** | month-end/Friday reconciliation pile-ups | Work spread continuously; no end-of-cycle crunch |

---

## Part 1 — The client-delivery lifecycle (the core)

> Reconstructed from WS 2.0 Review §E + `WORKSPACE_SYNC` + wallet/accounts hooks. This is the least code-grounded part (Workspace internals not seen), so **⚠️ heaviest validation needed here.**

**As-Is**
1. Request arrives (WS-native, email/Gmail intake, or Phrase adapter — 1 thread ↔ 1 active request).
2. Request → Assignment(s) → Activity(ies); each activity = inputs → one performer (human / AI-agent / tool) → output.
3. Status/progress **derived asynchronously** in `task-scheduler` (separate from the mutation) → drifts → repair crons (`fix_*_conflicts`, `reset_critical_status`).
4. Allocation: SWAT proposes/assigns experts; mobilization by chasing (WhatsApp/call). ⚠️
5. Editor/TR42 auto-creates TR + PR + QA activities for translation.
6. Deliver (owner sign-off at org boundary) → Mark Completed (commercial trigger) → Verify & Save (V&S).
7. On assignment events, WS calls ERP wallet (deduct/refund) and sends invoice-item groups to `accounts`.

**Pain**
- State drift is *designed in* — status computed in a failable separate pipeline; dashboards admitted-inaccurate.
- Mobilization = humans chasing humans; SWAT is a chaser, not an exception-handler.
- Request-creation is fragile: malformed requests from feature-interaction edge cases → fixed by one-off scripts because the UI lacks controls (Bhavya).
- AI-agent completion = frontend polling; no push.

**WS 3.0**
- **One authoritative lifecycle engine**: state change + status derivation happen together (transactional or event-sourced — Bhavya's §9 call). No repair crons.
- **Robust, validated request-creation + admin controls in the UI** → the fix-script class disappears.
- **Ambient AI scope sheet**: enclave reads the file, emits counts/complexity/deadline estimate → allocation without "commit before seeing the file."
- **Intelligent mobilization**: channel-native one-tap accept + smart escalation → SWAT becomes exception-handler.
- **Event/push** for agent + status → real-time, no polling.

**Win** — Trustworthy real-time status; SWAT stops chasing; devs stop writing fix-scripts; clients/managers trust the numbers.

**⚠️ Joy** — SWAT/QA/SME/pool definition; the allocation judgment; per-archetype flow differences (translation vs BOT vs retainer); which validations in §E are load-bearing vs. accidental.

---

## Part 2 — Wallet / Credits (prepaid client money)

**As-Is** — Assignment txn (`created/updated/cancelled/deleted`) → price via `offering~src~tgt~unit` match against `InvoicePricingDetail.service` → **FIFO lot deduction** (`select_for_update`) → immutable `WalletLedger` row → balance check → 50%/25% low-balance email → **async Google-Sheet sync** (SOA/utilization). Top-up: lot (purchase/promo) → invoice → payment webhook → apply credit. Reconciliation crons detect DB-vs-Sheet drift.

**Pain** — The ledger is solid, but it's shadowed into Sheets (`sync_wallet_to_sheet`, `verify_wallet_sheet`) with **anomaly crons whose only job is to catch drift**; negative-balance carve-outs are hardcoded entity lists; notifications fire on raw threads.

**WS 3.0** — **Keep the ledger design as-is (it's good)**; drop the Sheet mirror entirely (P1) — the ledger *is* the SOA/utilization source, rendered live. Negative-balance policy → per-tenant config (P2). Notifications → event queue (P3).

**Win** — Removes the single most drift-prone subsystem; finance gets a live, always-correct SOA; no reconciliation crons.

**⚠️ Joy** — Is the SOA Google Sheet a client-facing deliverable, or purely internal reporting? (Decides whether we still *export* a sheet on demand.)

---

## Part 3 — Invoicing (V&S invoices + credit invoices)

**As-Is** — Workspace sends invoice items → grouped by `group_id` → validated against pricing JSON → currency-converted (rate snapshot at invoice time) → `Invoice`+`InvoiceItem` → status `draft→publish` (invoice number generated)`→payment` → PDF from static xlsx templates (`english/arabic/wht/dual_currency`, Arabic via external translate API) → `InvoiceAuditLog`. **1 Invoice Group = 1 invoice / Entity / month.**

**Pain** — Debug `print()` in `Invoice.save()`; v2 rewrite half-done (PATCH unroutable); dual currency + tax logic is dense but untested; PDF generation via LibreOffice/xlsx2pdf is fragile.

**WS 3.0** — Same invoice-group rule (load-bearing, keep). Move the invoice-item intake to the internal lifecycle (no cross-service hop once unified). Typed pricing + tax engine with **real tests** (this is money). Templated PDF as a service. Rate-snapshot behavior preserved.

**Win** — One-system invoicing (no WS↔ERP round-trip), tested tax/currency math, clean audit — fewer invoice corrections, faster close.

**⚠️ Joy** — Confirm the tax matrix (VAT/WHT/no-tax per entity/geo) and e-invoicing obligations (QR/e-invoice number) — legally critical.

---

## Part 4 — People / Onboarding

**As-Is** — Create person (validate per entity/type/contract) → create `auth_app.User` for email + official_email (**initial password = `name_id`+join-year** ⚠️ weak) → auto-create `LeaveBank` (sick by tenure, flexi by entity) → ITAM webhook (EZ/CASPR) → welcome email → Skill-Quota? delivery-support email → **sync to Workspace**. Effective-dated edits: `schedule_changes` writes `History` rows → **daily cron applies at effective_date**.

**Pain** — Weak default passwords; `People.team` has `on_delete=CASCADE` + hardcoded `default=62`; `salary_data`/`service_fee`/`discount` typing issues (money as CharField); onboarding data often arrives via `load_people*` spreadsheet imports.

**WS 3.0** — Proper identity + SSO/invite onboarding (no derived passwords). Effective-dated changes stay (good pattern) but applied via scheduled events, not a minute-cron. Typed money fields (Decimal). Team FK → `PROTECT`. UI-driven onboarding replaces `load_people*`.

**Win** — Secure onboarding, no spreadsheet imports, safer referential integrity.

**⚠️ Joy** — The onboarding archetype skeleton per entity (EZ Fulltime / AEZ PS / Freelance / CASPR) — what's mandatory vs JIT.

---

## Part 5 — Skills / Quota / Coins

**As-Is** — Skill (`name~proficiency~unit~src~tgt~country`) with USD + credit prices (`×10`). `RateList` = coins/unit. Assign `PeopleSkill` → recompute `cost_per_coin = payout ÷ total_coins` → propagate `cost_price_per_unit = coins_normal_unit × cost_per_coin` → sync to Workspace. Quota = committed monthly coins; base always paid, incentive at earnings ≥ quota×1.1.

**Pain** — Rate lists loaded from Google Sheet (`load_ratelist`, `Tab5_Coins Rate List`); credit recompute triggered by a currency-row `post_save` signal (implicit); `RateList.skill` denormalized as CharField.

**WS 3.0** — **Keep the coins normalization + quota/incentive model (genuinely good)**. Rate lists become first-class config (P1/P2 — no sheet). Explicit, tested recompute (no signal magic). Skill catalog as versioned config.

**Win** — Same clever economics, now editable by ops and testable — no sheet, no hidden signal.

**⚠️ Joy** — Confirm coins vs credits are independent scales; confirm quota×1.1 and incentive caps as config values.

---

## Part 6 — Payroll / Compensation

**As-Is** — Monthly crons (AEZ 7:00 PM / EZ 7:30 PM on the 1st) → per-entity calculators: pro-rate by payable days, **PPR bonus multiplier A/B/C/D = 1.25/1.0/0.75/0**, incentive (translator cap `USD 0.006`, **`Ahmed Saleh` fixed `0.002343022`**), night-shift `×150`, EZ statutory TDS/PF/ESI/LWF → approval `draft→approved→sent_to_accounts→on_hold` → `financial_data` **encrypted** → payslip (external microservice) → email. Unpaid leave/incentives imported from xlsx.

**Pain** — Per-person pay rules in config (Ahmed Saleh); caps hardcoded; unpaid-leave + incentive **imported by hand from spreadsheets** (`update_unpaid_leaves_from_xlsx`, `load_incentives_from_xlsx`); no tests on money math; statutory logic India-specific and buried.

**WS 3.0** — Payroll as a **Tenant-Zero module** (EZ's statutory rules are *EZ config*, not platform). Every cap/rate/per-person exception → config rows (P2). Unpaid-leave + incentives flow **automatically** from the (now-unified) leave + lifecycle data — no xlsx import. PPR multipliers, night-shift rate → config. **Tested** calculators (legally critical). Keep encryption.

**Win** — No monthly spreadsheet imports; comp runs on live data; one-person exceptions are config not deploys; auditable, tested payroll.

**⚠️ Joy** — Full statutory matrix per entity/geo (India PF/ESIC/LWF/TDS, UAE WPS); which exceptions are permanent policy vs legacy; the exact incentive rules per team (VG, Translation).

---

## Part 7 — Leave / Attendance / Shifts

**As-Is** — Leave request → validate (balance, conflicts→auto-reject overlaps, comp-off availability, flexi dates, WFH/Friday rules) → approve → **comp-off FIFO allocation** → attendance auto-regen (merge biometric + timesheet + leave) → month-end logs (4+ short leaves → unpaid). Shift assignment (monthly, week-off quotas, copy-prev-month). Entity-specific accrual (EZ/CASPR 7 sick days in Jan, AEZ 1/month; EL 1.5/month). Biometrics + leave-bank loaded from Google Sheets. Role (employee/manager/hr) **derived at runtime** by "who reports to you" + team-name = `"people"` = HR.

**Pain** — Biometric + leave-bank data via `load_biometric_manual` / `load_leave_bank_data` (Sheets); role derivation is string-fragile; much WFH-quota logic commented-out/dead; attendance is a cron-and-sheet dance.

**WS 3.0** — Biometric/attendance via **device/event integration** (P3), not sheet imports. Roles as **real assigned roles** (P4), not derived from reporting graph + team-name string. Leave/accrual rules → config per entity (P2). Attendance computed continuously (P7). Comp-off FIFO logic is fine — keep.

**Win** — No manual biometric/leave-bank imports; robust roles; real-time attendance; ops stop reconciling monthly.

**⚠️ Joy** — Confirm the accrual/short-leave/WFH-Friday rules that are *current policy* (vs the commented-out dead logic).

---

## Part 8 — PPR (quarterly performance review)

**As-Is** — Manager sets expectations → ratings → employee acknowledges (3 booleans; any "no" → status On-Hold + dispute email to managers + `hr@ez.works`) → HR publish (requires a rating) → grades A/B/C/D + E(probation) → **feeds compensation bonus**. Some fields are Postgres **generated columns**. Org grade counts exclude a hardcoded gmail list (`EXCULDE_PPR_ORG_COUNT`, incl. a junk entry, and the setting name is misspelled).

**Pain** — Exclude list hardcoded in settings; grade→bonus coupling implicit; CSV grade import via S3 subprocess.

**WS 3.0** — PPR as a module; exclude list + grade→multiplier map → config (P2). Direct, tested link PPR→comp (no implicit coupling). Keep the generated-column idea as computed fields.

**Win** — HR runs PPR + tunes the grade curve without a developer; clean, auditable bonus linkage.

**⚠️ Joy** — Confirm the grade→bonus mapping and who's legitimately excluded from org counts (and why).

---

## Part 9 — Offboarding

**As-Is** — LWD set → signal creates `Offboarding` (non-freelance) → **T-3** NOC emails (IT/Facilities/Accounts/manager) + formalities checklist → ITAM offboarding webhook → **T-1** exit-interview chatbot link → OpenAI summary → experience letter (per entity/contract, salary decrypted into a docx template → LibreOffice PDF → S3) → FNF. NOC/checklist state derived from checkboxes.

**Pain** — Emails via daily cron; Google-Form exit-interview path parallel to chatbot; experience-letter generation is a fragile docx→LibreOffice pipeline; PROD-gated email behavior is inconsistent.

**WS 3.0** — Offboarding as a workflow module: event-driven emails (P3), single exit-interview capture (drop the parallel Google-Form path), templated letter service. Keep the NOC checklist model.

**Win** — One exit path, reliable notifications, cleaner document generation.

**⚠️ Joy** — Confirm the NOC/experience-letter variations per entity (EZ/AEZ/CASPR/Trainee) and FNF rules.

---

## Part 10 — Sales / CRM

**As-Is** — Lead ingestion (bulk upload, per-platform dedup) → funnel (`contact_stage/status`) → daily follow-up crons → convert to `Client → Entity → Requester` → `InvoicePricingDetail` setup → **sync to Workspace** (signal-driven, rollback-by-delete on sync failure).

**Pain** — Every save of Client/Entity/Requester/Pricing triggers an outbound Workspace POST that can **delete the just-created row on failure** — a workspace outage blocks CRM writes; denormalized copies everywhere.

**WS 3.0** — Unified system → **no sync at all** (the whole rollback-by-delete class vanishes). CRM writes are local + transactional. Pricing lives once. Follow-ups event-scheduled.

**Win** — CRM no longer coupled to a second system's uptime; no denormalization drift; one pricing record.

**⚠️ Joy** — The real sales pipeline stages EZ uses (vs the generic ones in code).

---

## Part 11 — Timesheet

**As-Is** — Charge codes (`department_team_offering[_project]`) → log hours (24h/day cap, two-layer) → `upsert_timesheet_data` → feeds `leave.TimesheetData` for attendance. Pulled from Workspace **activity-logs** (Jira-style) daily. Access gated by `(entity, team)` allowlists + email allowlists in settings.

**Pain** — Charge codes loaded from Google Sheet; access via settings allowlists (config-in-code); timesheet ↔ attendance coupling depends on shift data being present or the write fails.

**WS 3.0** — Timesheet auto-derives from the unified lifecycle's **activity logs** (no separate Jira pull, no manual charge-code sheet). Access via real RBAC (P4). Charge codes as config.

**Win** — Timesheets fill themselves from actual work; no sheet, no separate Jira sync, no allowlist-in-code.

**⚠️ Joy** — Confirm whether timesheet stays a distinct concept post-unification or is subsumed by activity logs.

---

## Consolidated efficiency scorecard

| Lever | Workflows it improves | Human payoff |
|---|---|---|
| Kill Sheets shadow-DB (P1) | Wallet, Invoicing, Skills, Leave, Timesheet, PPR | Ops stop updating sheets; finance stops reconciling |
| Config-not-code (P2) | Payroll, PPR, Leave, Wallet, Skills | Ops change rules in seconds; devs stop deploying for policy tweaks |
| Unify → no sync (P3/unification) | CRM, Invoicing, Wallet, People, Skills | No drift, no rollback-by-delete, no double-entry |
| Robust request-creation + admin UI (P5) | Delivery lifecycle | Devs stop firefighting one-off scripts |
| Ambient AI + intelligent mobilization (P6) | Delivery lifecycle | Juniors raise correct requests; SWAT stops chasing |
| Rolling + real-time (P7/P3) | Verify, Attendance, Payroll, Status | No month-end/Friday crunch; trustworthy dashboards |

**Through-line:** today EZ's people do work the system should do — updating spreadsheets, importing xlsx, chasing experts, running fix-scripts, reconciling drift. Every redesign above moves that work **from people into the platform**.

---

## Open items for Joy (the tacit layer code can't show)
1. **SWAT / QA / SME / pool** — definition, hand-offs, TL sign-off points (modeled nowhere).
2. **Allocation judgment** — how work is actually assigned today.
3. **Per-archetype delivery flows** — translation vs BOT vs managed-service/retainer (they diverge structurally).
4. **Load-bearing vs accidental** — which validations/quirks must be preserved exactly.
5. **Cannot-interrupt windows** — which scheduled runs are legally critical (dates are in code; criticality is Joy's call).
6. **Policy vs legacy** — which hardcoded exceptions (Ahmed Saleh, caps, exclude lists) are current policy vs cruft to retire.
7. **Pilot capability + parity acceptance criteria** — the first cutover target.

---

# WS 3.0 — Domain Redesigns (the dissolved ERP, improved)

**Each absorbed ERP domain, redesigned — not ported.** Expands the keep/kill/redesign map (`09` §1) into target models + rules. Common to all: typed (no JSONB blobs), config-driven (no hardcodes), live-data-fed (no xlsx/Sheet imports), event-driven (no fire-and-forget threads), tested (esp. money).

---

## 1. Money — Wallet / Credits / Invoicing / Payout (one integrated domain)

**Why together:** in WS 2.0 these are split across apps + the ERP↔WS boundary. Unified, they're one money spine.

- **Wallet/Credits** — keep the FIFO immutable ledger + idempotent ops. Kill the Google-Sheet mirror, drift crons, hardcoded negative-balance entity lists. → **The ledger is the single SOA/utilization source, rendered live.** Negative-balance = per-tenant config. Credits = client prepaid; independent of expert coins.
- **Invoicing** — keep 1-group/entity/month, rate-snapshot-at-invoice, audit log. Kill the cross-service intake hop, debug prints, brittle xlsx→PDF. → Invoice fires as an **in-lifecycle event on Verify** (no hop, no auto-invoice-on-complete). Typed + tested tax/currency engine (VAT/WHT/dual-currency). PDF as a templated service.
- **Payout** — keep coins→cost and effective-dated rates. → Computed from verified periods/deliverables; paid via the payroll module. No claw-back on goodwill (new linked assignment instead).

**Key rules preserved:** ERP-was-source-of-truth becomes *the WS money module is the single truth*; rate changes apply only at cycle start; billing by `billing_model` (unit/retainer/outcome).

---

## 2. Catalog / Skills / Coins / Quota

- Keep: the offering primitive, coins normalization (`cost_per_coin = payout ÷ total_coins`), quota/incentive (base always paid, incentive ≥ quota×1.1).
- Kill: Sheet-loaded rate lists, the currency-signal magic recompute, denormalized `RateList.skill` CharField, the two-Team duplication.
- → **First-class config** rate lists + skills (versioned catalog, restructurable). Explicit, **tested** recompute (no post_save signal surprise). M2M offering↔capability with primary/secondary. Levels first-class (`⚠️ J10`).

---

## 3. People / Identity / Roles

- Keep: effective-dated `History` (schedule future changes), salary encryption.
- Kill: derived initial passwords (`name_id`+year), `CASCADE` on team FK + hardcoded `default=62`, money-as-`CharField`, `load_people*` spreadsheet imports, runtime role-by-string-match ("team == people" = HR).
- → **Proper identity** (invite now, SSO/portable-root ready), **real assigned roles** (RoleAssignment), typed money (Decimal), safe FKs (`PROTECT`/`SET_NULL`). UI-driven onboarding replaces imports.

---

## 4. Payroll / Compensation

- Keep: encryption, PPR-multiplier bonus, effective-dating, entity-specific calculators.
- Kill: xlsx imports (`update_unpaid_leaves_from_xlsx`, `load_incentives_from_xlsx`), per-person env-var rules (`AHMED_SALEH_*`), hardcoded caps (translator `0.006`, night-shift `150`), untested money math.
- → **Config-driven statutory engine** — India PF/ESIC/LWF/TDS, UAE WPS as **rule data per entity/geo**, not code (Tenant-Zero config). Per-person exceptions = config rows. Unpaid-leave + incentives flow **automatically from the unified leave + lifecycle data** (no import). Fully **tested** (legally critical). `❓ Joy J25:` the authoritative statutory matrix + per-team incentive rules.

---

## 5. Leave / Attendance / Shifts / Timesheet

- Keep: comp-off FIFO, entity-specific accruals, shift model.
- Kill: Sheet-loaded biometrics/leave-bank, dead commented WFH logic, string-derived roles, the separate Jira timesheet pull, manual charge-code sheets.
- → **Device/event attendance** (biometric integration, not sheet import). **Timesheet auto-derives from the unified activity logs** — it fills itself; charge-codes as config. Accrual/short-leave/WFH rules as **config per entity**. Real roles (not derived). `❓ Joy:` which accrual rules are current vs the dead logic.

---

## 6. PPR (performance review)

- Keep: quarterly cycle, generated-column computed fields, the ack/dispute/publish flow.
- Kill: hardcoded exclude-list (personal gmails in settings), the misspelled setting, implicit PPR→comp coupling.
- → **Config grade-curve** (A/B/C/D→multiplier as config), configurable exclusions, **explicit tested PPR→comp link**.

---

## 7. Offboarding

- Keep: the NOC/formalities checklist model, experience-letter templating.
- Kill: daily-cron email firing, the parallel Google-Form exit path, PROD-gating inconsistencies.
- → **Event-driven** (LWD triggers the timeline), **single exit-interview path**, templated-letter service.

---

## 8. Sales / CRM

- Keep: the lead funnel, pricing setup.
- Kill: the signal-driven workspace sync + **rollback-by-delete** (a workspace outage blocking CRM writes), denormalization drift.
- → **No sync at all** (one system). Local transactional writes. One pricing record (no denormalized copies). Event-scheduled follow-ups.

---

## 9. Reporting / Dashboards

- Kill: dashboards computed off drifting async state ("numbers don't match").
- → **Dedicated reporting store** fed by the **reliable single lifecycle engine** — accurate by construction. Real-time, trustworthy, no reconciliation.

---

## Cross-domain: what the redesign eliminates system-wide
- **The ERP↔WS boundary** — gone; one graph.
- **Google-Sheets-as-database** — gone; DB/ledger is the source.
- **~132 hand-run management commands** — replaced by UI + validated APIs + a **task queue** (retry/audit) instead of raw threads.
- **~380 hardcoded Sheet IDs, per-person rules, caps, allowlists** — all → config.

## Preserved primitives (the good bones we keep)
Coins normalization · immutable FIFO ledger · rate-at-cycle-start · effective-dated history · encryption · 1-invoice-group/entity/month · invoice-validation dependency graph · comp-off FIFO.
