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
