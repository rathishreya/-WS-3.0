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
