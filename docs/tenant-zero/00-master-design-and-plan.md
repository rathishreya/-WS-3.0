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
