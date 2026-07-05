# WS 3.0 — Open Questions

> Everything we still need from Joy (product/ops) and Bhavya (architecture).

---

# WS 3.0 — Questions for Joy

**Purpose:** The consolidated list of everything I need Joy (product owner + domain authority) to answer or look into, to finish the Tenant-Zero spec and the workflow mapping. Architecture questions (isolation, GraphQL, event-sourcing) go to Bhavya, not here.

**How to use:** Numbered so answers can reference them (e.g. "J1: …"). Each has a one-line **why** = what it unblocks. Ordered by how much it's blocking — **P0 = blocks the journey/architecture right now.**

---

## P0 — Blocking (needed to complete the journey + Architecture v2)

### J1 — The delivery engine: SWAT / QA / SME / pool  ⭐ biggest single gap
Define each layer: **what it does, how work hands off between them, who the TLs are, and how they map to real teams/designations.** It's referenced everywhere in the vision ("the SWAT TL signs off Verify") but **modeled nowhere in the ERP code.**
*Why:* it's the spine of allocation and the Verify sign-off; Part C(3) of the onboarding journey and the whole allocation design are blocked on it.

### J2 — Allocation mutation (❓A1 from `01-core-delivery`)
Where/how is the **pending expert access row created on an activity** — the "Allocate & Start" stage? Standard CRUD, or a dedicated allocate/publish mutation? It's currently invisible in the mapped mutations.
*Why:* it's the missing step between "assignment created" and "expert accepts"; the lifecycle engine can't be specified without it.

### J3 — Mobilization path (❓A2)
Channel-native push (WhatsApp/SMS/one-tap accept) appears **out-of-repo.** Where does it live today, and what's the **accept → access-write** path?
*Why:* mobilization is a headline WS 3.0 efficiency win (SWAT stops chasing); we need the real current path to redesign it.

### J4 — Verify & Save as the human gate (❓A6 / ⚠D4)  ⭐ most important reconciliation
Today the code **auto-invoices synchronously on mark-complete**, and a repair cron (`check_marked_complete_request_vs`) later fixes requests that skipped V&S. **Where is the Verify human gate today?** Is the immediate invoice a gap the repair cron compensates for? Confirm the WS 3.0 target: **TL signs off at Verify → *then* invoice + payout, run rolling.**
*Why:* this is the single most important lifecycle reconciliation — it decides whether "mark complete → invoice" gets split by an explicit gate.

### J5 — Feedback gate (❓A4)
What is `check_request_feedback` / **"feedback pending"** — who sets it, who clears it, and why does it block mark-complete?
*Why:* it short-circuits completion; the completion state machine is ambiguous without it.

### J6 — Who triggers delivery (❓A5)
`STDeliveryService.create_delivery` — invoked by whom (owner action / cron / editor callback)? Is it **idempotent** across interim + final?
*Why:* determines the trigger + safety model for the Deliver stage.

### J7 — Progress authority (❓A3)
Two progress implementations coexist (`progress_calculator.py` vs `status_manager.*_safe`). **Which runs in prod?**
*Why:* progress feeds status; the parity test needs the authoritative formula.

### J8 — Status enum: ordering + dead values (⚠D1)
`STATUS_PRIORITY` orders `slightly_delayed` as *worse* than `critical`, and several statuses (`very_late`, `require_attention_*`, `expert_delay_critical`) are **never produced**. Confirm the **intended ordering** and **which statuses are live vs dead** (so we prune them from the typed model).
*Why:* the status algorithm is load-bearing (dashboards, SLAs) and feeds the typed domain model.

---

## P1 — Operating model (needed to configure Tenant-Zero)

### J9 — "10:20:30" SLA
What do the three numbers mean, and is it **brand-wide, per-tier, or per-service**? (The catalogue implies speed is an EZ-wide promise.)
*Why:* SLA + quality tiers are a superadmin config knob and drive the deadline/at-risk logic.

### J10 — Service levels: first-class or descriptive?
Do levels (Machine/Lite/Assured/Transcreation; Basic/High-End; Templatized/Customized/Tailor-made) each carry their **own price / skills / QA / SLA**, or are they descriptive text inside a service?
*Why:* decides whether "level" is a priced, allocated, QA'd dimension of the catalog model.

### J11 — Billing models for v1
The catalogue proves ≥4 models: **unit×price, project/fixed, retainer/managed-service (Shared EA, BPO, HR Ops), and Build-Operate-Transfer (AI Transformation).** Which must the first EZ cut support, and which come later?
*Why:* the WS 2.0 invoice spine is unit-only; retainer/BOT break it. This is a foundational data-model decision.

### J12 — Allocation policy
How is work **actually assigned today** — the human judgment SWAT applies (fit, cost, capacity, deadline, responsiveness)? What weights/priorities?
*Why:* the allocation engine encodes this; we need the real policy, not the generic vision list.

### J13 — Trust tiers (Standard / Compliant / Private)
What does each **guarantee on data handling**, and roughly which clients demand which?
*Why:* maps to per-client storage/processing config (Relationships layer).

### J14 — Catalog authority
Is **`Finalised Services` (86 entries) the authoritative go-forward catalog**? After go-live, is the catalog edited continuously via the WS-admin, or a curated artifact?
*Why:* decides whether we seed a fixed catalog or build the catalog *editor* as a first-class surface.

---

## P2 — Workflow archetypes (the mapping beyond `01-core-delivery`)

### J15 — The remaining archetypes (02–06)
Per the Workflow Brief, map: **intake variations** (Phrase / email auto-create / manual), **agent-performed** (Flip/MT/OCR; agent→human-QA), **nested / sub-assignment + dependencies**, **change/edit paths** (scope change, reassignment, cancel — the edit-levels), **invoicing / Verify-and-Save detail** (the load-bearing validation chains).
*Why:* these complete the lifecycle spec + parity tests. `01-core-delivery` references them but doesn't expand them.

### J16 — The retainer / BOT divergence  ⭐
The **managed-service/retainer** and **BOT** archetypes have **no discrete deliverable and no unit count** — they don't fit the Request→Assignment→Activity→Deliver→unit-invoice model. How does EZ actually run and bill these (HR Ops, Contact Centre, AI Transformation)?
*Why:* it's the archetype most likely to break the core model; needs its own design before we commit the schema.

### J17 — Agent-as-performer (❓ in `01-core-delivery`)
Does the AI-agent path (Flip/MT/OCR) share the **exact same role machinery** as a human expert, or a distinct path?
*Why:* determines whether "performer" is one unified concept or two.

---

## P3 — Tacit rules & operations (what code + docs can't show)

### J18 — Live rules vs dead scripts
Of the ~132 management commands, **which `load_*` / `fix_*` / cron scripts encode *current business rules* vs. one-off history?**
*Why:* the live ones carry rules we must preserve; the dead ones we ignore.

### J19 — Manual edge-case interventions
What edge cases do ops handle **by hand** today (rush jobs, reassignment splits, goodwill revisions, disputes, negative-balance exceptions)? Each becomes a **feature or a config knob** in WS 3.0.
*Why:* if we miss these, work breaks — they're the "email → fix-script" gaps.

### J20 — Policy vs legacy hardcodes
Which hardcoded exceptions are **current policy vs cruft to retire** — e.g. `Ahmed Saleh` fixed cost-per-coin, the translator `0.006` cap, the `@mckinsey.com` silent-notification drop, the PPR exclude-list?
*Why:* policy ones become config; cruft gets dropped. We don't want to faithfully rebuild junk.

### J21 — Load-bearing vs accidental validations
Which validation chains (Request/Assignment/Activity creation, V&S) must be **preserved exactly** vs. which are accidental? (Bhavya flagged the V&S chains as intentional — confirm scope.)
*Why:* these become parity tests; we must not "simplify" a load-bearing rule.

### J22 — TR/PR sync edge cases
Confirm the commented `activity_service.py:506` TR/PR rule is a **Workspace↔Editor sync workaround, not a business rule** (so a clean Editor sync makes it vanish).
*Why:* avoids preserving a workaround as if it were a rule.

---

## P4 — Continuity & pilot (for the no-halt migration)

### J23 — Cannot-interrupt windows
The scheduled runs are in code (payroll 1st, offboarding daily, etc.). Which of these are **legally/financially critical** — the windows we must never cut over during?
*Why:* the strangler-fig migration schedule is built around these blackout windows.

### J24 — Pilot capability + parity acceptance criteria
Which **one capability** do we migrate first (Translation is the natural candidate — core, unit-based, full lifecycle), and what does **"works as well as WS 2.0"** mean for it (measurable acceptance criteria + pilot users + rollback)?
*Why:* strangler-fig proves the whole stack on one small surface before scaling; parity-first needs ops-defined acceptance.

---

## P5 — Statutory / finance (route to finance if not yours)

### J25 — Statutory payroll matrix
Since we're dissolving the ERP, WS 3.0 owns payroll. The **full statutory matrix per entity/geo** (India PF/ESIC/LWF/TDS/Form 16, UAE WPS) + the **incentive rules per team** (e.g. VG, Translation).
*Why:* legally critical, zero-tolerance; must be rebuilt as *Tenant-Zero config*, not platform core — and needs the authoritative rules.

---

## Suggested session order
Start with **J1** (delivery engine) and **J2–J8** (the core delivery ❓/⚠️) in one working session — that unblocks the journey and the architecture. Then J9–J14 (operating model), then map the archetypes J15–J17. J18–J25 can be captured as we go.

---

# WS 3.0 — Questions for Bhavya (Architecture)

The architecture decisions that gate the build. Numbered `B1…` for reference. Each has a **why** and my **lean** (a starting position, not a decision).

---

### B1 — Tenant isolation model  ⭐
How are workspaces isolated: **DB-shard-per-workspace** (the team's stated plan), **RLS**, or **schema-per-tenant**? And critically — the model must support **operating-entity-level isolation *within* a workspace** (the EY case: EY-3 mustn't see EY-4's vendor relationship).
*Why:* the review calls isolation the weakest, hardest-to-retrofit part; the typed model already exposes `workspace_id` + `operating_entity_id`, but the enforcement mechanism is yours.
*Lean:* logical isolation (RLS + entity-scoped policies) for Phase-1 EZ single-tenant, shard-ready — full physical sharding when Phase-2 multi-tenant lands.

### B2 — Lifecycle engine: transactional vs event-sourced  ⭐
The core WS 3.0 fix folds status derivation into the state change (no async drift). Do we do this **transactionally** (state+status in one DB transaction) or **event-sourced** (replayable event log)?
*Why:* it's the §9 open decision from your brief, and the recurring **ServicePeriod** model (retainer/BOT) leans event/scheduler-driven.
*Lean:* event-sourced for the lifecycle (natural fit for periods, audit, replay, and killing the repair crons); transactional writes underneath.

### B3 — GraphQL gateway exposure
PostGraphile-thin gateway vs code-first GraphQL? And are **persisted queries + Apollo caching** a hard constraint to preserve (you flagged them "most critical")?
*Why:* the other §9 open decision; shapes the whole API layer + the frontend data strategy.
*Lean:* preserve persisted-queries (security) + Apollo caching (perf) as constraints; gateway choice yours.

### B4 — ERP↔WS integration → gone
We're **dissolving the ERP**, so the bidirectional REST sync + rollback-by-delete disappears — one graph, one system. Confirm this is consistent with your architecture direction (it reverses the earlier "ERP stays external" framing).
*Why:* it's the single biggest scope + architecture change; everything downstream assumes one system.

### B5 — Async / eventing infrastructure
Replace the WS 2.0 pattern (raw `threading.Thread` side-effects + `django-crontab` + AI-agent polling) with what — Celery, a broker, an event bus?
*Why:* notifications, period scheduling, agent callbacks, invoicing all need reliable async (retry/audit); "fire-and-forget threads" is a named tech-debt.
*Lean:* a proper task queue + event bus; push/event for agent callbacks (not polling).

### B6 — Stack confirmation
The brief proposes Python/FastAPI + React/Apollo + Postgres + Redis + S3. Confirm — and any change given the dissolve-ERP scope expansion (the ERP is Django today; do we keep Django ORM, move to FastAPI, or …?).
*Why:* the scaffolding depends on it; the ERP being Django is a real input.

### B7 — Multi-tenancy readiness scope for Phase 1
Phase 1 = EZ single tenant, built multi-tenant-ready. How much of the isolation/tenancy machinery do we build now vs defer — without painting into a corner?
*Why:* balances "don't over-engineer Phase-1" against "don't retrofit isolation later."

---

## What unblocks on your answers
- **B1 + B2** → finalize the typed domain model (`06`) + the lifecycle engine spec → **Architecture v2**.
- **B3 + B6** → the API layer + scaffolding.
- **B5** → notifications, period scheduling, agent callbacks.

## Suggested: B1 + B2 first — they're the two that gate Architecture v2 sign-off.
