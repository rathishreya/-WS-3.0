# WS 3.0 — Master: Overview · Plan · Approval

> Consolidated: master design + use-cases + phases + pre-build plan + approval gate.

---

# WS 3.0 — Tenant-Zero: Master Design & Plan

**The single reference.** Ties together the structure, the work model, the use-cases, the product phases, and my work plan. Detailed specs live in `01`–`04` (and the `05`–`08` I'll add). No code until Shreyanshi says "build."

---

## 1. What we're building (one paragraph)

WS 3.0 is a **multi-workspace control plane**. A **platform operator (L0)** provisions **workspaces (L1)** — one per organization/tenant — each run by its own **workspace admin** who configures *everything* declaratively (no hardcoding). Inside a workspace, **operational roles (L2)** run the work: a request flows through one **unified lifecycle engine** that handles both **deliverable** work (translate a deck) and **ongoing** work (run a helpdesk / BOT), all the way to delivery + invoice. **EZ is Tenant-Zero** — the first workspace, onboarded through the same flow as everyone else (no back-door), which is how the platform proves itself.

---

## 2. The structural model (L0 / L1 / L2)

| Level | Who | Controls |
|---|---|---|
| **L0 — Platform Operator** | WS team | Provisions workspaces, assigns admins, sets deployment tier + module availability, oversight |
| **L1 — Workspace = Organization = Tenant** | The workspace admin | Configures the whole operating model *declaratively* — entities, catalog, skills, teams/roles, pricing, billing models, wallet, SLAs, allocation, notifications, terminology, module activation |
| **L2 — Operational roles** | Within a workspace | SWAT/ops · Owner · Expert · QA · Requester/cc · AI-agent — the delivery actors |

- **1 organization = 1 workspace, many operating-entities** (EZ = one WS holding EZ Lab / ArabEasy / CASPR).
- **Platform primitives are fixed; every EZ-ism is L1 config.** Role *types* are primitives; EZ's SWAT/QA/SME/pool are config.
- **Isolation is scopable to the operating-entity level, not just the workspace** (locked because of use-case UC-G4 below).

---

## 3. The unified work model (deliverable + ongoing, one engine)

Keep the BAT graph (Request → Assignment → Activity). Add a configurable **delivery model** that decides *how work rolls up to a billable event*:

| delivery_model | "Complete" = | Billing | Examples |
|---|---|---|---|
| `deliverable` | outputs delivered + verified (terminal) | once | Translation, Slide Design |
| `retainer` | a **service period** closes + verified | per period | Helpdesk, HR Ops, Shared EA |
| `outcome` (BOT) | period closes + outcome metric measured | per period, from the metric | AI Transformation |

`billing_model` (`unit×price` / `flat_retainer` / `retainer+usage` / `outcome`) is a **separate config axis**. A new commercial shape = a new config combination, never new code. (Detail in `04`.)

---

## 4. Use-case catalog (what I'm designing for)

`P1` = Phase 1 (EZ single-tenant) · `P2` = Phase 2 (multi-tenant/cross-org) · `X` = cross-cutting. This is the coverage map — everything the design must eventually hold.

### A. Platform & onboarding
- **A1** `P1` Platform operator provisions a workspace (L0).
- **A2** `P1` Admin configures org to "can deliver" (the 7-rung config chain).
- **A3** `P1` EZ onboarded as Tenant-Zero via the same flow — no back-door.
- **A4** `P1` One org, multiple operating-entities in one workspace (EZ's 3 entities).
- **A5** `X` Smart onboarding — archetype skeleton → JIT enrichment → AI-assist.

### B. Identity & roles
- **B1** `P1` Admin creates/invites users into roles (manual).
- **B2** `P2` Portable root identity + SSO federation.
- **B3** `P2` Freelancer authenticates against own identity, approved into orgs.
- **B4** `X` Need-to-know POV-scoping per role.
- **B5** `P1`* **Entity-level need-to-know within a workspace** (from UC-G4 — design the primitive now).

### C. Catalog & config (the "configure everything" surface)
- **C1** `P1` Offerings (deliverable/retainer/outcome × billing models).
- **C2** `P1` Skills + rate lists + the mandatory Delivery skill.
- **C3** `P1` Teams/roles = the delivery engine (SWAT/QA/SME/pool as config).
- **C4** `P1` Pricing / invoice codes / payment type.
- **C5** `P1` SLAs, allocation policy, transparency defaults, terminology.
- **C6** `P1` Module activation (People, Invoicing, Wallet… — the absorbed ERP modules).
- **C7** `X` Catalog restructuring — rename/merge/move services safely, versioned.

### D. Intake
- **D1** `P1` Manual request creation.
- **D2** `P1` Phrase adapter (1 Project = 1 Job = 1 Request).
- **D3** `P1` Email auto-create (dedicated Gmail, 1 thread ↔ 1 request).
- **D4** `X` Ambient AI brief → offering mapping.

### E. Delivery (the lifecycle)
- **E1** `P1` Deliverable flow (Type A) — the core (Joy's `01-core-delivery`).
- **E2** `P1` Retainer flow (Type B) — cyclic service periods.
- **E3** `P1` Outcome/BOT flow (Type B).
- **E4** `P1` File split → parts → activities (TR/PR/QA).
- **E5** `P1` Allocation & mobilization (propose→accept, channel-native one-tap).
- **E6** `P1` Agent-as-performer (Flip/MT/OCR; agent→human-QA).
- **E7** `P1` Human + mandated tool (TR42, Canva) via the license broker.
- **E8** `P1` Nested / sub-assignment + dependencies (output→input).
- **E9** `P1` Deliver → boundary review → **Verify (TL sign-off)** → invoice → payout.
- **E10** `P1` Auto-delivery (owner shortcut).

### F. Change & exceptions
- **F1** `P1` Scope change mid-flight (the edit-levels).
- **F2** `P1` Reassignment (expert unavailable; fee-split, EZ never funds overrun).
- **F3** `P1` Cancel / pause.
- **F4** `P1` Goodwill revisions post-completion (new linked assignment, no claw-back).
- **F5** `X` Disputes.
- **F6** `X` Recurrence.

### G. Cross-org (Phase 2 — your EY scenario lives here)
- **G1** `P2` A client orchestrates multiple vendors.
- **G2** `P2` **EZ as a vendor inside a client's tenant** (the Phase-2 acceptance test — EZ's method stays invisible).
- **G3** `P2` Per-relationship config + transparency dial (EY-3↔EZ ≠ EY-4↔EZ).
- **G4** `P2` **Confidentiality: EY-3 must not know EZ also works with EY-4.** → forces B5 (entity-level isolation) into P1 as a primitive.
- **G5** `P2` Encapsulation — a vendor is an opaque node across the boundary.
- **G6** `P2` Brokered inputs / transferred deliverables / attribution by WS identity.

### H. Commercial & financial (absorbed from the ERP — we're dissolving it)
- **H1** `P1` Wallet / credits (prepaid, FIFO ledger).
- **H2** `P1` Invoicing (1 invoice group / entity / month).
- **H3** `P1` Expert payout (coins / quota / incentive).
- **H4** `P1` Payroll — statutory (India PF/ESIC/TDS, UAE WPS) as Tenant-Zero config.
- **H5** `P1` People/HR, Leave, Timesheet, PPR, Offboarding (absorbed modules).

### I. Cross-cutting
- **I1** `X` Ambient inline AI (suggest→approve; no chat panel).
- **I2** `X` Channel-native notifications (WhatsApp/SMS/email).
- **I3** `X` Reliable reporting (one lifecycle engine → no drift, no repair crons).
- **I4** `X` Tenant-inspectable audit; server-authoritative access.

---

## 5. Product phases (the rollout)

**Phase 1 — EZ as Tenant-Zero (the internal backbone).** Single tenant, but **multi-tenant-ready by design**. In scope: onboarding + config surface, both work models (deliverable + retainer/outcome), the full delivery lifecycle, and the absorbed ERP modules (wallet, invoicing, payroll, HR…). Delivery is **intra-workspace**. This is where EZ actually runs.

**Phase 2 — Client orchestrating its agencies (the organization layer).** Multi-tenant, **cross-org** work: the EY scenario, EZ-as-vendor-inside-a-client, per-relationship transparency, encapsulation, entity-level confidentiality. Turned on *without a rewrite* because Phase 1 was built ready (that's why B5/entity-isolation is designed in now).

**Parked (option value, not now):** the commercial/pricing product, the live-market moat (Vision Part II).

---

## 6. My work plan (design → dependencies → build → cutover)

```
▶ Phase 0  DESIGN & SPEC  (now — no code)
    01 workflows+efficiency ✅   02 onboarding→delivery journey ✅
    03 questions-for-Joy ✅       04 unified delivery model ✅
    → 05 WS-admin config surface   06 typed domain model
    → 07 Type-B lifecycle detail   00 this master doc ✅

▶ Phase 1  DEPENDENCIES  (parallel)
    Joy answers 03 (delivery engine, A1–A6, BOT formula)
    Bhavya answers 08 (isolation incl. entity-level, event-vs-transactional, GraphQL)
    → folds into ARCHITECTURE v2 → sign-off gate

▶ Phase 2  BUILD  (only on your "go", after Arch v2)
    scaffolding → typed model → PARITY TESTS (first) → migration mapping
    → delivery engine + config surface + onboarding (Phase-1 features)

▶ Phase 3  CUTOVER  (strangler-fig)
    pilot capability (Translation) at parity → capability-by-capability
    → decommission ERP domain-by-domain (nothing halts)

▶ Phase 4  MULTI-TENANT / CROSS-ORG  (Phase-2 product, when triggered)
    turn on the organization layer (use-cases G1–G6)
```

**Gates:** Design (solo) → Joy + Bhavya → Arch v2 sign-off → **your "build"** → cutover.

---

## 7. Document set
- `00` this master design & plan
- `01` workflows + efficiency (ERP as-is → to-be)
- `02` onboarding → delivery journey (structure + config chain)
- `03` questions for Joy
- `04` unified delivery model (deliverable + ongoing)
- `05` *(next)* WS-admin config surface — every knob, declarative
- `06` *(next)* typed domain model
- `07` *(next)* Type-B lifecycle detail
- `08` *(next)* questions for Bhavya (architecture)

---

## 8. Open decisions & owners
| Decision | Owner | Status |
|---|---|---|
| Delivery engine (SWAT/QA/SME/pool) | Joy | open (P0 blocker) |
| Verify-gate + A1–A6 delivery details | Joy | open |
| Billing models for v1 + BOT formula | Joy | open |
| Tenant isolation model (incl. entity-level) | Bhavya | open |
| Transactional vs event-sourced engine | Bhavya | open |
| GraphQL gateway + persisted queries | Bhavya | open |
| `Engagement`/`ServicePeriod` naming + config matrix | Shreyanshi | confirm |
| Pull the EY cross-org case into P1? | Shreyanshi | you leaning P2 |

---

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

---

# WS 3.0 — Final Specification for Build Approval

**This is the document to approve.** It consolidates the full design. Approving it (together with the two flagged external inputs) is the green light to begin build.

**What "approve" means:** you agree the design direction, structure, work model, config surface, typed model, domain redesigns, and cross-cutting design are correct to build against. The **only** things still open are the clearly-listed Joy and Bhavya inputs — those slot into the marked holes without changing the design shape.

---

## 1. The design in one page

- **Multi-workspace control plane.** L0 platform operator provisions **workspaces** (one per org); each is run by its **workspace admin** who configures *everything declaratively*; **operational roles** run the work.
- **EZ is Tenant-Zero** — onboarded through the same flow (no back-door). 1 org = 1 workspace, many operating-entities.
- **One unified lifecycle engine** handles **deliverable** and **ongoing (retainer/BOT)** work — a configurable `delivery_model × billing_model` decides how work rolls up to a billable event.
- **The ERP is dissolved AND improved** — every domain redesigned (not ported): one graph, no sync, no Sheets, no hand-scripts, config-not-code, tested money.
- **"Onboarded = can deliver"** — a readiness engine enforces the config dependency chain.
- **Efficiency thesis:** move work from people into the platform (kill imports, chasing, reconciliation, drift).

## 2. The specification set (all pushed)

| Doc | Covers | Status |
|---|---|---|
| `00` | Master design — structure, use-cases (A–I), phases | ✅ |
| `01` | Workflows + efficiency (ERP as-is → to-be) | ✅ |
| `02` | Onboarding → delivery journey + config chain | ✅ |
| `04` | Unified delivery model (deliverable + ongoing) | ✅ |
| `05` | WS-admin config surface — every knob, declarative | ✅ |
| `06` | Typed domain model — the schema | ✅ |
| `07` | Type-B lifecycle (retainer/outcome) | ✅ |
| `10` | Domain redesigns (dissolved ERP, improved) | ✅ |
| `13` | Cross-cutting — AI, notifications, access, audit, files, integrations | ✅ |
| `01-core-delivery` (Joy) | Type-A delivery, from WS 2.0 code | ✅ draft |
| `03` | Questions for Joy | ✅ routed |
| `08` | Questions for Bhavya | ✅ routed |
| `09` | Full pre-build plan | ✅ |

## 3. What is design-complete (you approve these)

- [x] **Structure** — L0/L1/L2, org→workspace→entities, role-type primitives vs config roles
- [x] **Unified work model** — deliverable + retainer + outcome, one engine
- [x] **Onboarding + readiness engine** — "onboarded = can deliver"
- [x] **Config surface** — every knob declarative, defaulted, versioned (`05`)
- [x] **Typed domain model** — schema replacing JSONB (`06`)
- [x] **Type-B lifecycle** — service-period model (`07`)
- [x] **Domain redesigns** — all 9 ERP domains, keep/kill/redesign (`10`)
- [x] **Cross-cutting** — ambient AI, channel-native notifications, server-authoritative RBAC, entity-level isolation, audit, enclave, integrations (`13`)
- [x] **Efficiency design** — the 7 principles applied throughout
- [x] **Use-case coverage** — A–I catalog, phase-tagged (`00`)

## 4. The only open holes (external inputs — they slot in, don't reshape)

**From Joy** (`03`): delivery engine (SWAT/QA/SME/pool) · A1–A6 delivery details · Verify-gate confirmation · billing models for v1 + BOT formula · archetypes 02–06 · statutory matrix.
**From Bhavya** (`08`): tenant isolation (incl. entity-level) · transactional-vs-event-sourced engine · GraphQL/persisted-queries · async infra · stack confirmation.

These are marked `⚠️`/`❓` at their exact locations in the specs. **None changes the design shape** — they fill parameters (which roles, which formula, which isolation mechanism).

## 5. Scope boundaries (approve these too)

**In (Phase 1):** onboarding + config, both work models, full delivery lifecycle, all absorbed ERP domains, intra-workspace delivery, EZ as Tenant-Zero.
**Deferred (Phase 2):** cross-org orchestration, the EY confidentiality flow, portable identity/SSO, the flywheel, commercials/live-market moat. *(Entity-level isolation is designed into the primitives now so Phase 2 needs no rewrite.)*

## 6. What approval unlocks — the path to build

```
YOU APPROVE THIS SPEC
        │
        ├─ Joy answers 03  ─┐
        ├─ Bhavya answers 08 ┤→ fold into ARCHITECTURE v2 → Bhavya sign-off
        │                    │
        └────────────────────┘
                             ▼
   parity-test catalog (11) + migration mapping (12)  [I draft next]
                             ▼
              ┌──────────── BUILD (your "go") ────────────┐
              scaffold → typed model → parity tests FIRST →
              migration → Phase-1 features → strangler-fig cutover
```

## 7. Definition of "ready to build" (the gate)

- [ ] **This spec approved** by you ← *the action requested now*
- [ ] Joy's P0 answered (delivery engine + A1–A6)
- [ ] Bhavya's B1+B2 answered (isolation + engine)
- [ ] Parity-test catalog drafted (`11` — I do next)
- [ ] Migration mapping drafted (`12` — I do next)
- [ ] Architecture v2 signed off

## 8. The ask

**Approve this specification** to lock the design and let me proceed to the parity-test catalog + migration mapping (the last two solo pieces), while Joy and Bhavya answer their routed questions. Once those three land, Architecture v2 goes to Bhavya for sign-off — and then we build on your "go."

If anything in `00`–`13` is wrong or missing, flag it and I'll revise before you approve — that's exactly what this gate is for.
