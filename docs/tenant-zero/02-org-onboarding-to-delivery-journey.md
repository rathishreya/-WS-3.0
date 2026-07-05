# WS 3.0 — Full Journey: Organization Onboarding → Assignment Delivery

**Status:** Draft v1 — design/workflow only, no code. For Shreyanshi/Joy/Bhavya review.
**Sources:** Foundational Vision (§2.2, §2.5, §3–4, §9, §13), Joy's `01-core-delivery.md`, the Workflow Mapping Brief, the dissolve-ERP decision.
**Legend:** `⚠️` = design decision I'm making (confirm/correct) · `❓` = open question routed to Joy/Bhavya.

---

## 0. Framing & locked decisions

- **1 organization = 1 workspace = 1 tenant**, holding **many operating-entities** (EZ = one WS with EZ Lab / ArabEasy / CASPR).
- **Three levels:** L0 Platform Operator → L1 Workspace Admin → L2 Operational roles.
- **"Onboarded" = the organization can take a request all the way to delivery + invoice.** Onboarding therefore *includes* the minimum-viable configuration (Part C).
- **Build fresh** to the WS 3.0 target (not WS 2.0 behavior); adopt Joy's mapped rules.
- **No back-door:** EZ (Tenant-Zero) is onboarded through this exact journey — it configures itself through the same surface every future org uses.
- **North-star config principle:** *every dimension is a first-class, declarative config object with smart defaults and an archetype skeleton, exposed through a guided admin surface — never a blank scripting canvas.* The WS admin controls **everything**, by tuning structured options, not by writing logic.

---

## Part A — The structural model (L0 / L1 / L2)

```
┌───────────────────────────────────────────────────────────────┐
│ L0  PLATFORM OPERATOR (the WS team)                            │
│  • provisions workspaces  • assigns each WS its admin          │
│  • sets deployment tier + which modules are available          │
│  • oversight — NOT the tenant's operating model                │
└───────────────┬───────────────────────────────────────────────┘
                │ provisions
        ┌───────▼───────────────────────────────────────────────┐
        │ L1  WORKSPACE  (= organization = tenant)               │
        │   Governed by the WORKSPACE ADMIN — the operating-     │
        │   model editor. Configures EVERYTHING (declaratively): │
        │   entities · catalog · skills · teams/roles · pricing  │
        │   · billing models · wallet · SLAs · allocation policy │
        │   · module activation · notifications · terminology    │
        │   (delegated module-admins sit under the admin, §9.2)  │
        └───────┬───────────────────────────────────────────────┘
                │ operates within
        ┌───────▼───────────────────────────────────────────────┐
        │ L2  OPERATIONAL ROLES (need-to-know scoped)            │
        │   SWAT/ops · Owner · Expert · QA · Requester/cc ·      │
        │   AI-agent — the delivery actors. Role *types* are     │
        │   platform primitives; the *named teams* are L1 config.│
        └───────────────────────────────────────────────────────┘
```

**Key layering (so nothing EZ-specific is hardcoded):**
- **Platform primitives** (fixed): the workspace boundary, the role *types* (request / assignment / activity access), the lifecycle state-machine shape, the config *object types*.
- **Tenant config** (L1 admin, per workspace): the *values* — EZ's SWAT/QA/SME/pool team names, its 15 capabilities / 79 offerings, its coin economy, its SLAs. All data, never code.

`⚠️` L0 scope is deliberately minimal for now (provision + module-availability + oversight); its full spec is parked until we know more.

---

## Part B — Organization Onboarding Journey (L0 → L1)

**Goal:** stand up a live-but-empty workspace with an admin, ready to be configured. Manual for now, designed to become AI-assisted.

| # | Actor | Action | Result |
|---|---|---|---|
| B1 | L0 Platform Operator | Create workspace for the organization | Workspace record exists (tenant boundary established) |
| B2 | L0 | Set **deployment tier** (Shared / Regional / Sovereign) + keys | Storage/processing posture set (Phase-1 EZ = Shared) |
| B3 | L0 | Set **module availability** (which first-party modules this WS may activate) | The WS admin's config palette is bounded |
| B4 | L0 | Assign the **Workspace Admin** (invite the first admin user) | L1 admin identity created; ownership handed off |
| B5 | L0 → L1 | **Handoff** | Workspace is *provisioned* — not yet *operational* |

**State at end of B:** an empty workspace with an admin and a bounded config palette. It **cannot deliver yet** — that's Part C.

`⚠️` People onboarding is **not** here — users/experts are added by the L1 admin *inside* the workspace (Part C). Portable identity + SSO federation (§2.2) is deferred to Phase 2; Phase 1 = admin creates/invites users directly.

---

## Part C — The Configuration Journey (L1 admin → "able to deliver")

**This is the crux of "onboarded = can deliver."** Below is the **minimum-viable config dependency chain**, derived directly from the *pre-conditions and steps* in Joy's `01-core-delivery.md`. It answers: *what must the WS admin configure before the very first assignment can flow to delivery + invoice?*

### C.1 The dependency chain (what unblocks what)

```
(1) FOUNDATION
    Organization identity + ≥1 Operating-Entity (legal/billing: currency, tax, invoice prefix)
        │  required by → invoicing, wallet, entity invoice codes
        ▼
(2) PEOPLE & ROLES
    ≥1 user per operational role: an Owner/SWAT, ≥1 Expert, a Requester
    + role permissions (e.g. requester.can_request_create)   [pre-cond: CreateRequest permission]
        │  required by → request creation, allocation (someone to assign)
        ▼
(3) TEAMS (the delivery engine, as config)
    SWAT / QA / SME / pool defined as configured teams; sign-off points
        │  required by → allocation routing, Verify sign-off
        ▼
(4) CATALOG
    ≥1 Offering the requester can request (offering ~ level ~ src ~ tgt ~ unit ~ capability)
        │  required by → assignment creation (pick offering)
        ▼
(5) SKILLS
    the skills the offering needs  +  the MANDATORY "Delivery" skill   [pre-cond: Delivery skill row]
    + rate list (coins/unit) for expert cost
        │  required by → activity creation (TR/PR/QA + Delivery), allocation match, payout
        ▼
(6) PRICING / INVOICE CODES
    an Entity with an invoice-pricing record whose invoice_code matches the assignment
    + payment type (prepaid / postpaid)                       [pre-cond: invoice_code_list match]
        │  required by → assignment creation, invoicing at delivery
        ▼
(7) WALLET  (only if payment type = prepaid)
    a funded wallet for the entity/requester                  [pre-cond: creditAssignment succeeds]
        │  required by → assignment creation (prepaid debits wallet)
        ▼
   ✅ MINIMUM-VIABLE WORKSPACE — the first assignment can now flow end-to-end.
```

### C.2 Mapped to the §9 config layers + the WS-admin surface

| Config layer (§9) | What the WS admin sets | Chain items |
|---|---|---|
| **Foundation** | Org identity, operating-entities, deployment tier, keys | (1) |
| **Operating Model** | Catalog (offerings/levels), skills + rate lists, teams/roles (the delivery engine), SLAs, allocation weights, billing models, terminology, transparency defaults | (3)(4)(5) |
| **Relationships** | Per-entity/-client pricing (invoice codes), per-client SLAs, QA reference data | (6) |
| **Live Operations** | People/experts + skill assignment, rate updates, module activation, wallet funding, integrations | (2)(5)(7) |

### C.3 Design notes
- **The "Delivery" skill is a platform primitive rendered as config** — every assignment auto-creates a mandatory Delivery activity (`sort_order=999`). The admin doesn't invent it; it's seeded, and the admin assigns performers to it.
- **Billing models are config, not code** — unit×price is the default, but *project / retainer / BOT* must be selectable per offering (per the catalogue; AI Transformation is BOT). `❓ Joy:` which billing models must the first EZ cut support?
- **"Smart onboarding" (later):** an **archetype skeleton** pre-seeds a plausible catalog/teams/skills for the org's industry, then **JIT enrichment** (never ask for a field until a feature needs it) + **AI-assisted** ratification. For now the admin fills it manually through the guided surface.

---

## Part D — The Delivery Journey (L2 — WS 3.0 target)

**Adopt Joy's `01-core-delivery` as the spine**, rendered as the WS 3.0 *target* (the fixes applied). The vision's 9 stages:

**Request → Create Assignment → Propose → Approve → Publish → Allocate & Start → Deliver → Mark Completed → Verify**

| Stage | What happens | Config it consumes (from Part C) | WS 3.0 fix vs today |
|---|---|---|---|
| **Request** | Requester submits a brief (manual / Phrase / email intake) | (2) permissions | Ambient AI maps brief → offering inline (§2.4) |
| **Create Assignment** | SWAT/owner picks offering; mandatory Delivery activity minted; payment type resolved | (4) catalog, (6) invoice code, (7) wallet | Robust validated creation → kills malformed-request scripts |
| **File split** | file → parts → activities (TR/PR/QA); unit-count split (remainder→first part) | (5) skills, unit types | AI scope-sheet (counts/complexity/deadline) before commit |
| **Propose / Allocate** | Propose performer(s); expert accepts/rejects | (2)(3)(5) experts+teams+skills, allocation policy | Intelligent channel-native mobilization (one-tap accept) → SWAT stops chasing |
| **Publish / Start** | On first expert accept, assignment/request go live | — | Push, not poll |
| **Work** | Expert works (TR42 or direct); interim/progress updates | (5), TR42 integration | Clean Editor sync → TR/PR workaround edge-cases vanish |
| **Deliver** | Activity/assignment delivers when all children terminal; auto-deliver cascade; owner boundary sign-off | (3) sign-off | **Mandatory boundary review = explicit Approve gate** (resolves ⚠D2) |
| **Mark Completed** | Commercial trigger | (6) pricing | **Decoupled from invoicing** — see Verify |
| **Verify (V&S)** | SWAT TL signs off; *then* invoice + payout, run rolling | (6)(5) rates/coins, invoicing module | **Explicit, server-authoritative Verify gate before the commercial trigger (resolves ⚠D4)** — no auto-invoice-on-complete, no repair crons |

**The single most important WS 3.0 change (from Joy's ⚠D4):** today the code auto-invoices *synchronously* on mark-complete, and a repair cron (`check_marked_complete_request_vs`) later fixes requests that skipped V&S. **WS 3.0 makes Verify an explicit human gate** — nothing flows to invoicing/payout until the TL signs off — so the drift, and the repair cron, cease to exist.

**Status/state, unified:** one lifecycle engine computes state-change **and** status in the same transaction/replayable event — no async drift, no `fix_*_conflicts` crons (the seam Joy identified).

---

## Part E — The stitched end-to-end journey (one narrative)

*Example: onboarding "Acme Localization" — the same path EZ walks as Tenant-Zero.*

1. **L0** creates Acme's workspace, sets tier = Shared, activates the Delivery + Invoicing + Wallet + People modules, invites Acme's admin. *(Part B)*
2. **Acme's WS admin** configures the minimum-viable set — one operating-entity, a Translation offering with its levels, the required skills + Delivery skill + rate list, a SWAT team + one expert + a requester, an invoice-pricing record (postpaid), done. *(Part C)* → **workspace is now "onboarded."**
3. A **requester** submits "translate this 20-page deck, EN→AR." **Ambient AI** proposes *Translation · EZ Assured · EN→AR* inline; requester approves. *(Request)*
4. **SWAT** creates the assignment, the file splits into parts → TR/PR/QA activities, AI emits a scope sheet. *(Create Assignment / split)*
5. SWAT proposes an expert; the expert gets a **one-tap WhatsApp accept**. *(Allocate / mobilize)*
6. Expert works in TR42 → interim updates → delivers. Auto-deliver cascades; owner signs off at the boundary. *(Work / Deliver)*
7. **SWAT TL verifies (V&S)** → *only now* the invoice + expert payout are generated, rolling. *(Verify → commercial trigger)*
8. Result: deliverable in the client's store, invoice raised, expert paid — **no drift, no repair cron, no spreadsheet.**

**The dependency truth:** step 3 is impossible without step 2's config, and step 2 is impossible without step 1's provisioning. That chain *is* "onboarded = can deliver."

---

## Part F — Open items & architecture implications

**For Joy** (from `01-core-delivery`, they gate the delivery detail):
- ❓A1 Allocation mutation (how the pending expert access row is created) · ❓A2 Mobilization path · ❓A3 Progress authority · ❓A4 "Feedback pending" gate · ❓A5 Who triggers delivery · ❓A6/⚠D4 Verify as the human gate.
- ❓ Which **billing models** the first EZ cut must support (unit / project / retainer / BOT).
- ❓ The **delivery engine** definition (SWAT/QA/SME/pool) — still needed to finalize Part C(3).

**For Bhavya** (architecture v2):
- The **tenant-isolation boundary** — how L1 workspaces are isolated (DB-shard / RLS / schema-per-tenant) now that all modules (incl. payroll/invoicing) are multi-tenant.
- **Transactional vs event-sourced** lifecycle engine (the Part D unification).
- GraphQL gateway exposure + persisted-queries.

**Typed domain model (feeds Shreyanshi):** Workspace → Operating-Entity → {Users/Roles, Catalog(Offering/Level), Skills/RateList, Teams, Pricing/InvoiceCode, Wallet} → Work graph (Request → Assignment → Activity + role/role_type/role_status). Replace the WS 2.0 `data` JSONB `.get().get()` chains with typed schemas.

---

## Part G — Deferred to Phase 2 (designed-for, not built now)
- **Cross-org boundary work** — encapsulation, the transparency dial, inter-org requests (§4.1). Phase-1 journey is intra-workspace.
- **Portable root identity + SSO federation** (§2.2).
- **Flywheel onboarding** — client-invites-vendor, self-serve signup.
- **Commercial layer + live-market moat** (Part II of the vision) — parked.

---

## What I need to close Part C(3) and Part D
The delivery-engine definition (SWAT/QA/SME/pool) and the ❓A1–A6 answers are the only things standing between this journey and a fully-specified Tenant-Zero. Everything else here is derivable from what we have.
