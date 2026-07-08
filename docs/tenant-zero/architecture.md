# WS 3.0 — Architecture

**Audience:** Joy & Bhavya (review). **Companion:** [`spec.md`](./spec.md) (the *what* and the field-level detail). This doc is the *how it's built*: the shape of the system, the layers, the isolation model, and the build path.

> **One line:** WS 3.0 is a **multi-tenant control plane** for orchestrated work. It holds the *graph* of work (who, what, when, how much) — never the raw content. EZ is simply the **first tenant** ("Tenant-Zero"), configured through the same surface as everyone else. No EZ logic is baked into the platform; every EZ-ism is config.

---

## 1. The core stance (read this first)

Three decisions shape everything below. If these are right, the rest follows.

1. **Platform-generic, EZ-as-config.** The platform ships primitives (Party, Relationship, Request, Assignment, Activity, roles, money events). EZ's model — SWAT/QA/SME/pool teams, coins, 10:20:30 SLA, the 86-service catalog — is **data in EZ's workspace**, not code in the platform. Litmus test we applied throughout: *could a translation agency, a design studio, and a research firm each run on this untouched?* If a feature only makes sense for EZ, it's config.

2. **Control plane, not system of record for content.** WS stores the **metadata graph** and **file pointers**. Raw bytes (briefs, deliverables, PII) live in the tenant's store and are processed ephemerally in a **sealed zero-retention enclave**. This is what makes multi-tenant confidentiality real rather than promised.

3. **AI composes → human ratifies.** The efficiency thesis. AI drafts the whole plan from a brief; humans touch the work exactly twice (ratify the plan, confirm the verify). Everything else is system-derived. This is a *product* stance with architectural consequences (an enclave, a composer, a suggest-not-act contract).

---

## 2. The structural model — L0 / L1 / L2

| Level | Who | Owns |
|---|---|---|
| **L0 — Platform Operator** | WS team | Provisions workspaces, sets deployment tier + module availability, assigns the L1 admin. Oversight only — **no back-door** into tenant data. |
| **L1 — Workspace = Organization = Tenant** | The workspace admin | Configures *everything* declaratively: entities, catalog, skills, teams/roles, pricing, billing/delivery models, wallet, SLAs, allocation policy, channels, terminology, module activation. |
| **L2 — Operational roles** | Inside a workspace | Run the work: owner · performer · reviewer · verifier · requester · AI-agent. (EZ maps these to SWAT/QA/SME/pool — a naming, not a new structure.) |

- **1 organization = 1 workspace, many operating-entities.** (EZ = one workspace holding EZ Lab / ArabEasy / CASPR.)
- **EZ onboards through the same flow as any tenant** — the strongest proof the platform is generic.

---

## 3. The six architectural layers

Everything — cross-org work, multi-entity isolation, EZ itself — falls out of the **same six layers + config**. Nothing is a special case.

```
┌─────────────────────────────────────────────────────────────┐
│ 6 · AI / Edges     composer (enclave) · channel adapters      │  suggest→approve
├─────────────────────────────────────────────────────────────┤
│ 5 · Money & Files  billable events · invoicing · payout ·     │  pluggable, gated
│                    wallet ledger · file pointers · enclave     │
├─────────────────────────────────────────────────────────────┤
│ 4 · Boundary       cross-org edge · encapsulation ·           │  one edge, two views
│                    brokered files · transparency dial          │
├─────────────────────────────────────────────────────────────┤
│ 3 · Lifecycle      Request→Assignment→Activity ·              │  one engine, status
│                    state+status in-engine · unified models     │  derived (no drift)
├─────────────────────────────────────────────────────────────┤
│ 2 · Config Engine  declarative knobs · readiness engine ·     │  config, not code
│                    archetypes · capability gating              │
├─────────────────────────────────────────────────────────────┤
│ 1 · Tenancy/Identity  workspace · operating-entity ·          │  two isolation levels
│                    Party + Relationship · RBAC                 │
└─────────────────────────────────────────────────────────────┘
```

**Why this matters:** a cross-org job is not a new subsystem — it's Layer 1's Relationship edge (a "vendor" from one side, a "client" from the other) viewed through Layer 4. Multi-entity isolation is just Layer 1's second scoping key. EZ is just a fully-populated Layer 2. **The primitives are few; the behaviours are config.**

---

## 4. Tenancy & isolation — the two levels

This is the part Bhavya must sign off. There are **two** isolation keys, deliberately:

| Key | Scope | Isolation mechanism | Use |
|---|---|---|---|
| **`workspace_id`** | Separate org / tenant | **Cryptographic** — separate tenant, BYOK for regional/sovereign tiers | Two different organizations (EZ vs a client) |
| **`operating_entity_id`** | A legal/billing unit *inside* one org | **Policy** — row-level scoping + need-to-know | EZ Lab vs ArabEasy inside EZ |

- Every relationship / work / wallet record carries **both** keys; access is scoped by `(workspace_id, operating_entity_id)`.
- **Default isolated at the entity level too:** sibling entities don't see each other's relationships or work. *(Entity-1 does not learn Entity-2 is a vendor to Org B — the confidentiality primitive the EY case needs, designed in from day one even though the flow is Phase 2.)*
- The org admin sees across entities **unless** entity-delegated module-admins blind even the admin (`module_admin_scope = entity`).
- **The mirror:** an external org sees only the entity it works with, never the org's other entities.

**Entity-vs-workspace is the client's choice** (both supported, interoperable, migratable): entities-in-one-WS (policy isolation, shared config) vs a workspace-per-entity (crypto isolation, own keys/tier). Splitting an entity into its own crypto-isolated workspace later is supported but is a **data-separation operation**, not a config toggle — flagged honestly.

**Open for Bhavya:** transactional vs event-sourced lifecycle engine; the exact RLS/tenant-isolation mechanism; GraphQL gateway + persisted queries; async infra; stack confirmation. These fill *parameters* — they don't reshape the layers.

---

## 5. The boundary — how workspaces connect (Layer 4)

A cross-org connection is **one Relationship edge**, "vendor" from A's side and "client" from B's side. There is no separate cross-org machinery.

- **In A's graph:** the vendor is **one opaque boundary node** (`boundary_node_id → maps_to: request_id in B`). A never sees B's tree, performers, method, sub-vendors, or costs.
- **In B's graph:** a **new Request** with A as the client. B runs its own lifecycle, invisible to A.
- **Brokered files:** inputs stay in A's store; B gets a **JIT scoped credential**; deliverables are **written back into A's store**; provenance is stripped at each hop.
- **Chains (A→B→C):** each hop re-encapsulates — **A never learns C exists.**
- **Transparency dial (config):** default opaque; the vendor may raise its own ceiling per relationship.
- **Non-WS parties:** reached via a client-system adapter (email / Phrase / API), bounded by that tool's surface.

Everything crosses through **one channel-adapter interface** and **one boundary contract** — so a second or third workspace is not new code, it's another edge.

---

## 6. Efficiency architecture — why it's 2 touchpoints, not 6

The lifecycle is built around **AI composes → owner ratifies**:

```
brief + files ─▶ [AI composer, in the enclave] ─▶ proposed plan
                     (offering · file split · activity tree ·
                      performers · deadline · scope · price)
                                  │
                          ┌───────┴────────┐
                    OWNER RATIFIES  ◀── human touchpoint #1
                          │
                 activities fan out in parallel
                 (channel-native one-tap mobilization; most
                  performers never open the app)
                          │
                 perform → policy-driven QA → assemble → deliver
                          │
                 AI pre-computes reconciliation
                          │
                 VERIFIER CONFIRMS  ◀── human touchpoint #2
                          │
                 billable event → invoicing + payout (rolling)
```

- **The composer** reads only the tenant's own config, is stateless and per-tenant scoped, and **suggests — never acts**. Its output is always editable inline.
- **Status is derived in the same transaction/event as the state change** — the single biggest reliability fix vs WS 2.0 (no async drift, no repair crons, no Google-Sheet shadow DB).
- **Mobilization is channel-native:** WS-chat by default (reuses WS 2.0 `chat-v2`), WhatsApp/SMS as user-selectable paid fallbacks, all behind one adapter. **No bidding** (removed per Bhavya).

---

## 7. What we are dissolving (the ERP) and the discipline for it

The EZ ERP is **dissolved and improved** — not ported. One graph, no ERP↔WS sync, no Sheets-as-database, no ~132 hand-run management commands. Each domain gets a keep / kill / redesign pass (full table in `spec.md` §9 and `03-domain-redesigns.md`):

- **Kill the ERP↔WS boundary** → one system, zero sync (removes the whole drift/rollback class).
- **Kill Google-Sheets-as-database** → the ledger *is* the source of truth.
- **Kill fire-and-forget scripts** → UI + validated APIs + a real task queue (retry/audit).
- **Config-not-code + one lifecycle engine** → the two changes that lift everything.
- **Tested money math** → parity-test catalog before any money code is written.

---

## 8. Stack (proposed — Bhavya to confirm)

| Layer | Choice | Note |
|---|---|---|
| Backend | **Python / FastAPI** | typed, async-ready |
| Frontend | **React / Apollo** | reuses WS 2.0 patterns incl. `chat-v2` |
| Data | **Postgres** | typed schema, RLS for entity scoping (replaces JSONB `.get().get()`) |
| Cache/queue | **Redis** + a real task queue | retry + audit, not fire-and-forget threads |
| Files | **S3-compatible** + connected-cloud + own-infra tiers | graph holds pointers only |
| Enclave | zero-retention compute | bytes ephemeral; access flows to the tool, never a person |

*(Today's ERP is Django; the redesign proposes FastAPI. Bhavya confirms.)*

---

## 9. The build path (gates, not a sprint)

```
DESIGN (now, no code)
   7-layer zero-cut design ✅  ·  architecture.md + spec.md ✅
        │
        ├─ Joy answers the [J] items ──┐
        ├─ Bhavya answers architecture ┤→ ARCHITECTURE v2 → Bhavya sign-off
        │                              │
   parity-test catalog + migration mapping (last solo pieces)
        ▼
   BUILD (only on Shreyanshi's "go")
   scaffold → typed model → PARITY TESTS FIRST → migration →
   Phase-1 features → strangler-fig cutover (capability-by-capability)
        ▼
   PHASE 2 — turn on cross-org / multi-tenant (no rewrite; designed in)
```

**Phase 1** = EZ as Tenant-Zero, intra-workspace, all absorbed ERP domains — multi-tenant-*ready* by design. **Phase 2** = cross-org orchestration (the EY case), turned on without a rewrite because the boundary and entity-isolation primitives are already in.

**Gates:** Design (solo) → Joy + Bhavya inputs → Architecture v2 sign-off → **Shreyanshi's "build"** → strangler-fig cutover.

---

## 10. What to review here

- **§1** — do you agree with the three-part stance (generic-not-EZ, control-plane, AI-composes)?
- **§4** — Bhavya: the two-level isolation model and the open architecture calls.
- **§5** — the boundary/encapsulation contract for connecting workspaces.
- **§9** — the gates and where your sign-off sits.

Field-level detail, use-cases, and how each scenario runs are in **[`spec.md`](./spec.md)**.
