# WS 3.0 — Cross-Cutting: Ambient AI · Notifications · Access · Audit

The concerns that touch every workflow. Kept in one place so they stay consistent.

---

## 1. Ambient AI (suggest → approve; never a chat panel)

**Principle (vision §2.4):** AI is a property of the surface, inline and dismissible, confidence-gated — never a persistent panel or popup. Runs in the enclave, per-tenant, stateless, inheriting the user's exact scope (AI POV = user POV).

**Touchpoints in the journey:**
| Where | AI does | Autonomy |
|---|---|---|
| Request intake | brief → proposes the right offering + level inline; asks "X or Y?" only if ambiguous | suggest→approve |
| Scope | reads the file in the enclave → non-confidential scope sheet (counts, complexity, per-expert deadline estimate) | suggest |
| Allocation | proposes a named allocation with reasons | owner ratifies |
| Onboarding/config | proposes catalog/skills/teams from the archetype skeleton | admin ratifies |
| Status | border-safe status roll-up + risk/exception propagation for the requester | surfaced |
| Verify | pre-computes the reconciliation for the TL | TL signs off |

**Metering:** AI priced in abstract credits, tenant-pooled, wallet overage with soft-stop (never kill mid-deliverable). (Commercial detail parked; the metering hook is designed in.)

---

## 2. Notifications (channel-native)

**Principle:** the edges are lightweight and external — mobilization, one-tap accept, approvals, status pings happen in WhatsApp/SMS/email; many users rarely open the app.

- **Config-driven recipient rules** — role + role_type + status, **configurable per client** (the `@mckinsey.com` silent-drop and exclude-lists become tenant config, not code).
- **Both switches** (template-allows AND user-setting-allows) preserved as config.
- **Event-driven delivery** via a task queue with retry/audit — not fire-and-forget threads. No more silent "client never got the notification."
- **Channels:** WhatsApp/SMS (mobilization, one-tap accept), email (intake/threading), in-app (deep work).

---

## 3. Access / RBAC (server-authoritative)

- **Server-authoritative** — the access decision lives on the server; the client computes optimistically for UX only (kills the WS 2.0 frontend access-JSON).
- **Need-to-know POV-scoping** — each user's surface is a projection of their scope; the UI shows only their slice.
- **Two isolation levels** — `workspace_id` and `operating_entity_id` (the EY case: sibling entities mutually invisible on the relationship dimension by default).
- **JIT least-privilege credentials** for any tenant-data pull (the enclave model); short-lived, per-grant.
- **Config-driven** — no hardcoded email allowlists (timesheet/payslip/leadership) → all become RBAC config.

---

## 4. Audit

- **Tenant-inspectable, tamper-evident** log of operator/admin actions ("don't-trust-us-verify").
- **Every config change** audited (who changed what knob, when).
- **Enclave governance** — no human sees tenant bytes; no content in logs; access flows to the tool, not the person.

---

## 5. Files & the enclave (brokered, zero-retention)

- **Inputs brokered** (read on-demand from the sender's store; instant revoke); **deliverables transferred** to the client's store as their property.
- **Content processing in a sealed, zero-retention enclave** — Splitter, counts, AI reading a brief pull bytes ephemerally, compute, retain nothing.
- **Attribution by WS identity** — the client's own logs show the WS user-id that accessed their files.

---

## 6. Integrations (the Connect surface)

- **Client-system adapters** (Phrase, memoQ, Trados…) at the intake/deliver boundary — directional-per-field (no two-way sync).
- **Tool integrations** (TR42, Canva, accounting, JIRA) at the module boundary — push-out + pull-reference, never two-way-sync a field.
- **License broker** — tool licenses as a pooled, JIT-assigned resource (cost moat); tier-gated (sovereign blocks egress tools).
- **AI-agent performers** (Flip/MT/OCR) — **push/event callback**, not the WS 2.0 checkpoint-polling.
