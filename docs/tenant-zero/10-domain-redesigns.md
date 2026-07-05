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
