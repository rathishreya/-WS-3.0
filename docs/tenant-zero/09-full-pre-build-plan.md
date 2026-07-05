# WS 3.0 — Full Pre-Build Plan

**Everything I will design and decide BEFORE any code is written.** Complements the master design (`00`). No build until Shreyanshi says "build."

**Directive change locked in:** we **dissolve the ERP AND improve every domain** — not port it. Where the ERP has a good primitive we keep it; where it's structurally weak we redesign it. "As-is" is never the target.

---

## 0. The principles the whole plan serves
- **Config, not code** — every knob is declarative config; nothing hardcoded.
- **One source of truth** — no Google-Sheet shadow DB, no ERP↔WS sync, no drift.
- **One lifecycle engine** — state + status in one transaction/event; no repair crons.
- **One unified work model** — deliverable + ongoing (retainer/BOT) in one engine.
- **Move work from people into the platform** — kill import-scripts, chasing, reconciliation.
- **Improve, don't port** — rethink each domain; keep the proven, drop the fragile.
- **Test-first, parity-first, maintainable-by-the-team.**

---

## 1. Improve-don't-port: the domain redesign map

For each dissolved-ERP domain — what we **keep**, **kill**, and **redesign to**. This is the concrete "better way."

| Domain | Keep (proven) | Kill (fragile) | Redesign to |
|---|---|---|---|
| **Wallet / Credits** | FIFO immutable ledger, idempotent ops | Google-Sheet mirror + drift crons, hardcoded negative-balance lists | Ledger = the single live SOA/utilization source; negative-balance = per-tenant config |
| **Invoicing** | 1 group / entity / month, rate-snapshot, audit log | cross-service intake hop, debug prints, brittle xlsx→PDF | In-lifecycle invoice event (no hop); typed + **tested** tax/currency engine; templated PDF service |
| **Payroll / Comp** | encryption, PPR multiplier, effective-dating | xlsx imports, per-person env-var rules (Ahmed Saleh), untested money math | Config-driven statutory engine (rules as data); **fed by live data** (no imports); tested |
| **People / Identity** | effective-dated `History` | derived passwords, `CASCADE` team FK, money-as-`CharField` | Proper identity + invite/SSO-ready; typed money (Decimal); safe FKs |
| **Skills / Quota / Coins** | coins normalization, quota/incentive model | Sheet-loaded rate lists, signal-magic recompute | First-class config rate lists; explicit, tested recompute |
| **Leave / Attendance** | comp-off FIFO, entity accruals | Sheet-loaded biometrics, role-by-string-match, dead WFH code | Device/event attendance; **real assigned roles**; accruals as config |
| **Timesheet** | charge-code concept | manual charge-code sheets, separate Jira pull | **Auto-derived from the unified activity logs** — timesheets fill themselves |
| **PPR** | generated-column pattern | hardcoded exclude-list, implicit comp coupling | Config grade-curve; explicit tested PPR→comp link |
| **Offboarding** | NOC checklist model | daily-cron emails, parallel Google-Form path | Event-driven; single exit path; templated letters |
| **Sales / CRM** | funnel, pricing setup | signal-sync + rollback-by-delete, denormalization | **No sync** (one system); local transactional; one pricing record |
| **Reporting** | — | dashboards off drifting state | Dedicated reporting store off the reliable engine |

**Four structural rethinks above the domains** (the biggest wins):
1. **Kill the ERP↔WS boundary** — one system, one graph, zero sync (removes the whole drift/rollback-by-delete class).
2. **Kill Google-Sheets-as-database** — everywhere.
3. **Kill the ~132 hand-run management-command surface** — replace with UI + validated APIs + a real task queue (retry/audit), not fire-and-forget threads.
4. **One lifecycle engine + config-not-code** — the two changes that lift everything.

---

## 2. The complete design deliverable set (before build)

Grouped by workstream. ✅ = done · ▶ = next · ⏳ = needs Joy/Bhavya input.

### WS-1 — Platform & structure
- ✅ `00` master design (L0/L1/L2, use-cases, phases)
- ▶ Tenant **isolation model** — workspace + **operating-entity level** (the EY case) ⏳ Bhavya
- ▶ Access / RBAC model — server-authoritative, config-driven (replaces the frontend JSON + email allowlists)

### WS-2 — Onboarding & config surface
- ✅ `02` onboarding→delivery journey + config dependency chain
- ▶ `05` **WS-admin config surface** — every knob, declarative, with defaults + the readiness engine

### WS-3 — The work lifecycle
- ✅ `04` unified delivery model (deliverable + retainer/outcome)
- ✅ `01-core-delivery` (Joy — Type A draft)
- ⏳ `01`-style maps for the archetypes **02–06** (intake, agent-performer, nesting, change-paths, invoicing/V&S) — Joy-driven, I structure
- ▶ `07` **Type-B lifecycle detail** (retainer/outcome — service-period state machine)

### WS-4 — Domain redesigns (the ERP, improved)
- ▶ `10` **Domain redesign specs** — one section per domain from §1: money (wallet+invoicing+payout), skills/coins/quota, people/identity, payroll (statutory-as-config), leave/attendance/timesheet, PPR/offboarding, reporting. Each: keep/kill/redesign → target model + rules.

### WS-5 — Cross-cutting
- ▶ `13` Ambient-AI touchpoints + channel-native notifications + audit spec

### WS-6 — The build foundation
- ▶ `06` **Typed domain model** — the schema (Workspace→Entity→config→work graph + Engagement/ServicePeriod + the redesigned domains); replaces JSONB `.get().get()`
- ▶ `11` **Parity-test catalog** — the load-bearing rules (from code + Joy) as executable test specs
- ▶ `12` **Migration mapping** — ERP → new typed model, field by field (I design; you run)

### WS-7 — Questions out
- ✅ `03` questions for Joy
- ▶ `08` questions for Bhavya (isolation incl. entity-level, event-vs-transactional, GraphQL)

### WS-8 — The sign-off artifact
- ▶ **Architecture v2** — folds WS-1…WS-6 into the doc Bhavya signs off (the brief's gate before build)

---

## 3. Sequencing

```
Now (solo, no code, no waiting):
  05 config surface → 06 typed model → 07 Type-B detail → 10 domain redesigns → 13 cross-cutting
  (these need nobody — derivable from what we have)

Parallel (route out immediately):
  03 → Joy  (delivery engine, A1–A6, BOT formula, archetypes 02–06)
  08 → Bhavya (isolation incl. entity-level, engine model, GraphQL)

Converge (once answers land):
  11 parity-test catalog + 12 migration mapping (need rules pinned)
  → fold all into ARCHITECTURE v2 → sign-off

Then (your "go" only): BUILD
```

**Parallelism:** ~70% of the remaining design (05, 06, 07, 10, 13) I can do **now, solo**. Only 11/12 and Arch-v2 truly wait on Joy + Bhavya.

---

## 4. Dependencies & gates

| Gate | Needs | Blocks |
|---|---|---|
| Delivery lifecycle final | Joy: delivery engine + A1–A6 | `07`, parity tests, Arch v2 |
| Isolation + engine model | Bhavya: entity-level isolation, event-vs-transactional, GraphQL | typed model finalization, Arch v2 |
| Parity catalog | rules pinned from code + Joy | build (test-first) |
| **Architecture v2 sign-off** | all above | **BUILD** |

---

## 5. Definition of "design-complete → ready to build"

We are ready to build when **all** are true:
- [ ] Structure, isolation, access model specced (WS-1)
- [ ] Config surface + onboarding readiness specced (WS-2)
- [ ] All delivery archetypes + Type-B mapped (WS-3)
- [ ] Every ERP domain redesigned, not ported (WS-4)
- [ ] Cross-cutting (AI, notifications, audit) specced (WS-5)
- [ ] Typed domain model complete (WS-6)
- [ ] Parity-test catalog drafted (WS-6)
- [ ] Migration mapping drafted (WS-6)
- [ ] Joy P0 answered · Bhavya architecture decided
- [ ] **Architecture v2 signed off**

---

## 6. The build plan (after the gate — for reference, not now)

1. **Scaffold** the stack (FastAPI / Postgres / Redis / S3 + React/Apollo).
2. **Typed domain model** in code (from `06`).
3. **Parity tests first** (from `11`) — red before green.
4. **Migration scripts** (from `12`) — I design, you run against real data.
5. **Build Phase-1 features** — onboarding + config surface + unified lifecycle + redesigned domains.
6. **Strangler-fig cutover** — pilot capability (Translation) at parity → capability-by-capability → decommission ERP domain-by-domain (nothing halts).
7. **Phase 2** — turn on multi-tenant / cross-org (the EY use-cases).

---

## 7. Risks & how this plan mitigates them

| Risk | Mitigation in the plan |
|---|---|
| Rebuilding untested money logic wrong | Parity-test catalog (`11`) **before** any money code; redesign specs pin exact rules |
| "Configure everything" → too-customizable-to-use | Declarative + defaulted + archetype-skeleton config surface (`05`), never a scripting canvas |
| Scope blow-up (ERP + workspace) | Strangler-fig + pilot-first + domain-by-domain decommission; nothing big-bang |
| Halting live payroll/invoicing | Operational-calendar blackout windows (Joy J23); cut over into safe gaps |
| Recreating EZ-isms as new hardcodes | Every hardcode → config (§1); the no-back-door rule; EZ-isms register |
| Cross-org confidentiality retrofit | Entity-level isolation designed into the primitives now (WS-1), even though the flow is Phase 2 |

---

## TL;DR
- **Improve every ERP domain, don't port** — the keep/kill/redesign map is in §1.
- **~70% of remaining design I can do now, solo** (`05`, `06`, `07`, `10`, `13`).
- **The rest waits on Joy + Bhavya**, then folds into **Architecture v2** — the sign-off gate before build.
- **Recommended start:** `05` (config surface) → `06` (typed model) → `10` (domain redesigns).
