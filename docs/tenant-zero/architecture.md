# WS 3.0 — Technical Architecture

**Audience:** Bhavya (architecture sign-off) & Joy (review). **Companion:** [`spec.md`](./spec.md) — the *what* (layers, fields, use-cases). This doc is the **engineering**: stack, service decomposition, data model + DB diagram, communications, events, security/isolation, deployment, and the open architecture calls.

> **System in one line:** a **multi-tenant control plane** that stores the *graph* of orchestrated work (never raw content), runs a single lifecycle engine, and composes plans with AI in a zero-retention enclave. EZ is the first tenant, configured through the same surface as everyone else.

**Conventions:** ✅ = locked in our design discussion · **⚠️ Bhavya** = an open architecture decision for sign-off · `(EZ: …)` = illustrative config only.

---

## 1. Design tenets that constrain the architecture

Everything below serves five non-negotiables we locked (see `spec.md` §11):

1. **One graph, one system, zero sync.** The single biggest lesson from the ERP: the ERP↔WS boundary + Google-Sheets-as-DB caused all the drift, rollback-by-delete, and repair-cron pain. **We do not rebuild that.** → a modular-monolith **core** with one transactional database, not a constellation of services that sync to each other.
2. **Status is derived in the same transaction as the state change.** No async projection to compute state. Events exist for *reporting and integration*, never for deriving truth. → no repair crons, no drift.
3. **Control plane, not content store.** The DB holds metadata + **file pointers**; raw bytes live in tenant storage and are processed in a **zero-retention enclave**. → the enclave and the byte-handling path are *physically separate* from the core.
4. **Config-not-code.** Every EZ-ism is a row, not a branch. → a first-class config schema + a readiness engine, not hardcoded rules.
5. **Two isolation levels.** `workspace_id` (crypto) and `operating_entity_id` (policy) on every record. → enforced at the data layer (RLS), server-authoritative.

---

## 2. Tech stack

| Concern | Choice | Rationale / note |
|---|---|---|
| **API style** | **GraphQL gateway + persisted queries** | one typed contract for a POV-scoped UI; persisted queries cap the attack/perf surface. **⚠️ Bhavya** to confirm GraphQL vs REST. |
| **Backend** | **Python 3.12 / FastAPI** | typed, async-native, fast. (ERP is Django today — **⚠️ Bhavya** confirms FastAPI vs staying Django.) |
| **Core data** | **PostgreSQL 16** | typed relational schema (replaces JSONB `.get().get()`), **row-level security** for `(workspace_id, operating_entity_id)`, strong transactional guarantees for the one-graph engine. |
| **Frontend** | **React + Apollo Client** | reuses WS 2.0 patterns incl. `chat-v2` (the default mobilization channel). |
| **Cache / queue** | **Redis** + a real task runner (**Celery / RQ / Temporal — ⚠️ Bhavya**) | replaces the ~132 fire-and-forget management commands with retryable, audited jobs. |
| **Event backbone** | **Postgres outbox → broker** (Redis Streams / Kafka / NATS — **⚠️ Bhavya**) | reliable event emission without dual-write drift (outbox pattern). |
| **Object storage** | **S3-compatible**, plus connected-cloud & own-infra tiers | the graph stores `file_ref` pointers only; bytes never touch the core DB. |
| **Enclave** | zero-retention compute sandbox (locked egress, ephemeral FS) | AI composer + agent performers run here; bytes in → result out → nothing retained. |
| **AuthN** | OIDC / SSO-ready; portable identity (Phase 2) | replaces derived-password + email-allowlist patterns from the ERP. |
| **Secrets / crypto** | per-workspace keys; **BYOK** for regional/sovereign; field-level encryption (Fernet-class) for cost/pay/PII | salary/PII never stored in plaintext. |
| **Observability** | structured logs + traces + tenant-inspectable audit log | one engine → reporting is reliable by construction. |
| **Infra** | containers + per-tier deployment (shared / regional / sovereign) | tier is a `Workspace` attribute; see §8. |

---

## 3. Service decomposition

**The honest call (⚠️ Bhavya to ratify): a modular-monolith *core*, not a microservice-per-domain.** Splitting config / lifecycle / allocation / money into separate networked services would force distributed transactions and cross-service sync to keep the work graph consistent — **exactly the ERP↔WS drift we are dissolving.** So those live as *modules inside one deployable core, sharing one DB and one transaction boundary.* We split out a service **only** where a genuine hard boundary exists: raw bytes, the enclave, external channels, or read/analytics load.

```mermaid
flowchart TB
  subgraph Client["Clients"]
    UI["React / Apollo UI"]
    CH["Channels: WS-chat · WhatsApp · SMS · email · Phrase"]
  end

  GW["API Gateway / BFF<br/>GraphQL · persisted queries · authN · POV-scoping"]

  subgraph Core["CORE ORCHESTRATION SERVICE  (modular monolith · one Postgres · one transaction)"]
    direction TB
    TEN["Tenancy & Identity<br/>Workspace · Operating-entity · Entity · Relationship · RBAC"]
    CFG["Config Engine<br/>catalog · skills · pricing · policies · readiness"]
    LC["Lifecycle Engine<br/>Request→Assignment→Activity · state+status in-txn"]
    ALL["Allocation<br/>hard filters · scored proposal · fallback ladder"]
    MON["Money<br/>billable event · invoicing · wallet ledger · payout"]
    BND["Boundary / Federation<br/>cross-org edge · encapsulation · provenance strip"]
  end

  subgraph Sep["Split-out services (hard boundaries only)"]
    CMP["AI Composer<br/>stateless · per-tenant · ZERO-RETENTION ENCLAVE"]
    FB["File Broker<br/>file_refs · access grants · byte I/O · enclave feed"]
    CG["Channel Gateway<br/>adapter interface · one-tap payloads · escalation"]
    RPT["Reporting / Read-Model<br/>projections off domain events"]
    WRK["Task Runtime<br/>retryable jobs: escalation · invoice · payout · period rollover"]
  end

  BUS["Domain Event Bus  (Postgres outbox → broker)"]

  UI --> GW
  CH --> CG
  GW --> Core
  Core -->|"compose (brief+files via scoped cred)"| CMP
  CMP -->|"bytes on demand"| FB
  Core <-->|"pointers · grants"| FB
  Core -->|"mobilize command"| CG
  CG -->|"one-tap callback (webhook)"| GW
  Core -->|"outbox"| BUS
  BUS --> RPT
  BUS --> WRK
  WRK --> Core
  Core <-->|"signed, encapsulated boundary API"| Core2["Another Workspace's Core<br/>(cross-org peer)"]
```

| Service | Owns | Why separate (or not) | Sync/async |
|---|---|---|---|
| **API Gateway / BFF** | GraphQL schema, persisted queries, authN, POV-scoping | thin edge; one contract for the UI | sync |
| **Core Orchestration** (modular monolith) | the **entire work graph + config + money events**, one Postgres, RLS | **deliberately not split** — one graph, one transaction, zero internal sync | sync (in-process modules) |
| ├ Tenancy & Identity | Workspace, Operating-entity, Entity, Relationship, Users, RBAC | module | in-txn |
| ├ Config Engine | catalog, skills, rates, teams, policies, readiness | module | in-txn |
| ├ Lifecycle Engine | Request/Assignment/Activity, state **+ status derived in-txn** | module | in-txn |
| ├ Allocation | hard filters → scored proposal → fallback ladder | module | in-txn |
| ├ Money | billable event, invoicing, wallet ledger, payout | module | in-txn |
| └ Boundary/Federation | cross-org edge, encapsulation, provenance strip | module with a **guarded external API** | sync + signed |
| **AI Composer** | brief→plan composition | **must** be isolated: zero-retention enclave, per-tenant, stateless | sync request/response |
| **File Broker** | `file_ref`s, access grants, enclave byte feed | **must** be isolated: it touches raw bytes | sync + short-lived creds |
| **Channel Gateway** | WS-chat/WhatsApp/SMS/email adapters, escalation | isolates external providers behind one adapter interface | async out, webhook in |
| **Reporting / Read-Model** | analytical projections | keeps read/analytics load off the transactional core (I3) | async (event-fed) |
| **Task Runtime** | escalation, invoice gen, payout runs, period rollovers, pre-mobilization | replaces the 132 hand-run commands with retry+audit | async (queue) |

**⚠️ Bhavya decision:** modular-monolith core (recommended) vs full microservice split. Recommendation stands on tenet #1 — but if the team wants independent scaling/deploy per domain, the trade is distributed-transaction complexity and a sync surface we've worked to eliminate.

---

## 4. Data model & DB diagram

One Postgres schema for the core. Every tenant-scoped table carries **`workspace_id`** and (where work/money/relationships live) **`operating_entity_id`** — both enforced by **row-level security**. Money is typed `Decimal`; cost/pay/PII are field-encrypted; the wallet ledger and audit log are **append-only**.

```mermaid
erDiagram
  WORKSPACE ||--o{ OPERATING_ENTITY : has
  WORKSPACE ||--o{ ENTITY : scopes
  WORKSPACE ||--o{ RELATIONSHIP : scopes
  WORKSPACE ||--o{ OFFERING : scopes
  WORKSPACE ||--o{ SKILL : scopes

  ENTITY ||--o| PERSON : "is-a (person)"
  ENTITY ||--o{ RELATIONSHIP : "from/to"
  ROOT_IDENTITY ||--o{ PERSON : "one human, many workspace memberships"
  PERSON ||--o{ ACCESS_GRANT_ROLE : holds
  PERSON ||--o{ PERSON_SKILL : "declares (expert skills)"
  SKILL ||--o{ PERSON_SKILL : "rated in"
  PERSON ||--o{ ACTIVITY : "performs (expert)"
  PERSON ||--o{ PAYOUT_LINE : "paid via"

  OPERATING_ENTITY ||--o{ RELATIONSHIP : scoped_to
  RELATIONSHIP ||--o{ ENGAGEMENT : governs

  OFFERING ||--o{ OFFERING_ACTIVITY_TEMPLATE : defines
  OFFERING ||--o{ RATE : priced_by
  SKILL ||--o{ OFFERING_ACTIVITY_TEMPLATE : used_in
  SKILL ||--o{ RATE : priced_by

  ENGAGEMENT ||--o{ SERVICE_PERIOD : "Type-B cycles"
  ENGAGEMENT ||--o{ REQUEST : contains

  REQUEST ||--o{ ASSIGNMENT : "AI-composed → ratified"
  REQUEST ||--o| PROPOSAL : "composer output"
  ASSIGNMENT ||--o{ ACTIVITY : "tree of"
  ACTIVITY ||--o{ ACTIVITY_IO : "inputs/outputs"
  ACTIVITY ||--o| ALLOCATION : proposes
  ACTIVITY ||--o| MOBILIZATION : notifies
  ACTIVITY ||--o| BOUNDARY_NODE : "if cross-org"

  FILE_REF ||--o{ ACTIVITY_IO : referenced_by
  FILE_REF ||--o{ ACCESS_GRANT : brokered_by

  ASSIGNMENT ||--o| BILLABLE_EVENT : "emits on verify"
  BILLABLE_EVENT ||--o| INVOICE_LINE : bills
  INVOICE ||--o{ INVOICE_LINE : groups
  BILLABLE_EVENT ||--o{ PAYOUT_LINE : pays
  RELATIONSHIP ||--o| WALLET : "prepaid (client)"
  WALLET ||--o{ WALLET_LOT : "FIFO lots"
  WALLET ||--o{ WALLET_LEDGER : "append-only truth"

  WORKSPACE {
    uuid id PK
    string org_code
    string region
    string deployment_tier
    string byok_key_ref
    jsonb modules_available
  }
  OPERATING_ENTITY {
    uuid id PK
    uuid workspace_id FK
    string code
    string country
    string billing_currency
    string tax_profile
    bool entity_isolation
  }
  ENTITY {
    uuid id PK
    uuid workspace_id FK
    string type "org|person"
    string display_name
  }
  PERSON {
    uuid id PK
    uuid workspace_id FK
    uuid entity_id FK
    uuid root_identity_id FK "global — links memberships across workspaces"
    string email
    string entity_role
    string contract_type
    uuid operating_entity_id FK
    bytes cost_encrypted
    bool sso_federated "employee SSO; revoke → this membership's access ends"
  }
  RELATIONSHIP {
    uuid id PK
    uuid workspace_id FK
    uuid from_entity FK
    uuid to_entity FK
    string type "employment|client|vendor|tenant"
    uuid operating_entity_id FK
    string invoice_code "per-client billing code (client rel; gated)"
    jsonb config
    string status
  }
  OFFERING {
    uuid id PK
    uuid workspace_id FK
    string name
    string delivery_model "deliverable|retainer|outcome"
    string billing_model
    jsonb levels
  }
  SKILL {
    uuid id PK
    uuid workspace_id FK
    string name
    jsonb proficiency_scale
  }
  ENGAGEMENT {
    uuid id PK
    uuid client_relationship_id FK
    string delivery_model
    string billing_model
  }
  SERVICE_PERIOD {
    uuid id PK
    uuid engagement_id FK
    string period
    string status
  }
  REQUEST {
    uuid id PK
    uuid workspace_id FK
    uuid operating_entity_id FK
    uuid requester_id FK
    uuid engagement_id FK
    text brief
    date deadline
    string source_channel
    string state
    string status "derived in-txn"
  }
  PROPOSAL {
    uuid id PK
    uuid request_id FK
    jsonb proposed_activities
    jsonb scope_sheet
    jsonb confidence
    jsonb clarifying_questions
    jsonb provenance
  }
  ASSIGNMENT {
    uuid id PK
    uuid request_id FK
    uuid offering_id FK
    string level
    string unit_type
    numeric unit_count
    uuid owner_id FK
    numeric price
    string state
    string status
  }
  ACTIVITY {
    uuid id PK
    uuid assignment_id FK
    uuid skill_id FK
    string performer_type "human|agent|human+tool"
    uuid performer_id FK
    uuid dependency_activity_id FK
    int sort_order
    string qa_policy
    string state
    string status "derived in-txn"
  }
  ACTIVITY_IO {
    uuid id PK
    uuid activity_id FK
    uuid file_ref_id FK
    string role "input|output"
  }
  FILE_REF {
    uuid id PK
    uuid workspace_id FK
    string store_location
    string key
    string checksum
    uuid owner_entity_id FK
  }
  ACCESS_GRANT {
    uuid id PK
    uuid file_ref_id FK
    string grantee
    jsonb scope
    timestamp expiry
    bool revocable
  }
  ALLOCATION {
    uuid id PK
    uuid activity_id FK
    jsonb candidates_scored
    uuid proposed_performer_id
    jsonb alternates
    jsonb reasons
  }
  MOBILIZATION {
    uuid id PK
    uuid activity_id FK
    string channel
    timestamp sent_at
    string response
    int escalation_step
  }
  BOUNDARY_NODE {
    uuid id PK
    uuid activity_id FK
    uuid linked_relationship_id FK
    string maps_to_request_ref
    string visible_status
    string opacity_level
  }
  BILLABLE_EVENT {
    uuid id PK
    uuid assignment_id FK
    uuid verified_by FK
    numeric unit_count
    numeric unit_price
    numeric amount
    string currency
    string billing_model
    uuid operating_entity_id FK
    uuid client_relationship_id FK
  }
  INVOICE {
    uuid id PK
    uuid operating_entity_id FK
    uuid client_relationship_id FK
    string invoice_number
    string invoice_code "per-client billing code (from the client relationship)"
    string grouping_rule
    jsonb tax
    string status
  }
  INVOICE_LINE {
    uuid id PK
    uuid invoice_id FK
    uuid billable_event_id FK
    jsonb rate_snapshot
  }
  PAYOUT_LINE {
    uuid id PK
    uuid billable_event_id FK
    uuid performer_id FK
    string period
    numeric amount
    string status
  }
  WALLET {
    uuid id PK
    uuid relationship_id FK
    numeric balance
    numeric cost_per_credit
  }
  WALLET_LOT {
    uuid id PK
    uuid wallet_id FK
    numeric credits
    numeric remaining
    date validity
  }
  WALLET_LEDGER {
    uuid id PK
    uuid wallet_id FK
    string op "deduct|settle|refund"
    numeric delta
    timestamp at
  }
  ROOT_IDENTITY {
    uuid id PK "GLOBAL — lives above every workspace; no workspace_id"
    string owner_auth_ref "the human's own credential"
    uuid personal_workspace_ref "invisible to any org (SEC-12)"
    jsonb portable_reputation "travels across orgs, metadata-only"
  }
  ACCESS_GRANT_ROLE {
    uuid id PK
    uuid person_id FK
    string scope
    string role_type
    string role_status
  }
  RATE {
    uuid id PK
    uuid workspace_id FK
    uuid skill_id FK
    uuid relationship_id FK
    string unit_type
    numeric rate
  }
  PERSON_SKILL {
    uuid id PK
    uuid workspace_id FK
    uuid person_id FK
    uuid skill_id FK
    int proficiency "1..5"
    string status "declared|verified"
  }
  OFFERING_ACTIVITY_TEMPLATE {
    uuid id PK
    uuid offering_id FK
    uuid skill_id FK
    int sort_order
    uuid dependency_template_id FK
    string qa_policy
  }
```

**Notes on the model**
- **Entity + Relationship is the spine.** Tenant/client/vendor are `RELATIONSHIP.type` values, not tables. A cross-org link is one `RELATIONSHIP` row seen as `vendor` by A and `client` by B.
- **Two-layer identity (one person in N workspaces).** `ROOT_IDENTITY` is **global** — one per human, above all workspaces (their login, personal workspace, portable reputation). Each workspace they join gets its own **workspace-scoped `PERSON` membership** that references the root identity. A workspace's core sees only its own `PERSON` rows; **the root→membership mapping is resolved at the identity/gateway layer and never exposed into a tenant's graph** — so WS-A cannot learn the person is also in WS-B. Auth once at the root; act per membership; revoke SSO/offboard ends *that* membership only. The only deliberate cross-workspace signal is `portable_reputation` (metadata-only, superadmin-governed). *(Phase 2 — but modeled now so it needs no rewrite.)*
- **The work graph is a tree** via `ACTIVITY.dependency_activity_id`; independent branches run in parallel, dependent ones gate on their input.
- **`status` is a stored column written in the same transaction as `state`** — not a projection. Reporting reads it; it never computes it.
- **Money is append-only where it must be:** `WALLET_LEDGER` is the source of truth (no sheet mirror); `BILLABLE_EVENT` is immutable once emitted.
- **Files are pointers.** `FILE_REF` never holds bytes; `ACCESS_GRANT` issues the short-lived brokered credentials for the enclave and for cross-org.
- **The expert lives across several tables (not one "expert" table).** An expert is a `PERSON` (`entity_role=performer`) whose skills are `PERSON_SKILL` rows; allocation records the pick in `ALLOCATION.proposed_performer_id`; acceptance is an `ACCESS_GRANT_ROLE`; the person `performs` an `ACTIVITY` and writes outputs via `ACTIVITY_IO`; and is paid by `PAYOUT_LINE` off the `BILLABLE_EVENT`. (Traced end-to-end in `spec.md` Appendix A.)
- **Terminology — `ENTITY` vs `OPERATING_ENTITY` (two distinct things).** `ENTITY` is an **actor** — an org or a person (this is the old "Party"). `OPERATING_ENTITY` is a **legal/billing sub-unit inside one org**. An `ENTITY(org)` can contain several `OPERATING_ENTITY` rows (Acme → Acme Lab, ArabEasy). Rule to avoid confusion: the actor is always **Entity** (`entity_id`); the billing unit is always the fully-qualified **operating_entity** (`operating_entity_id`) — never write bare "entity" to mean the billing unit.
- **The client user is a `ENTITY(person)`.** A client company is `ENTITY(org)` (the `to_entity` of a `client` RELATIONSHIP); its requester is a `ENTITY(person)` under that org, referenced by `REQUEST.requester_id`. They only get a `ROOT_IDENTITY`/login if the client is itself on the platform (cross-org); otherwise they're a contact record you deliver to.
- **⚠️ Bhavya:** transactional (this model) vs event-sourced. Recommendation: transactional core with an **outbox** for events — gets reliability without the read-model-as-truth complexity.

---

## 5. Communications

**Principle:** *sync within a transaction boundary, async across one.* Core modules talk in-process (one transaction). Everything crossing the core — bytes, channels, reporting, other workspaces — is an explicit, guarded protocol.

| Path | Mechanism | Why |
|---|---|---|
| UI → Gateway | GraphQL / HTTPS, persisted queries | one typed, POV-scoped contract |
| Gateway → Core | sync call (in-proc or gRPC) | request/response for the graph |
| **Core module ↔ Core module** | **in-process, one DB transaction** | the one-graph rule — **no network sync between config/lifecycle/allocation/money** |
| Core → AI Composer | sync request/response, authenticated; brief/files handed as a **scoped credential**, not bytes | keeps content in the enclave, zero-retention |
| Composer / agents → File Broker | short-lived credential; bytes streamed into the enclave, nothing retained | control-plane discipline |
| Core → Channel Gateway | **async command** ("mobilize", payload) | external providers, ret/escalation |
| Channel → Gateway | **webhook callback** (one-tap accept/decline) | performer never opens the app |
| Core → Reporting / Workers | **domain events via outbox → broker** | reliable, drift-free (state already committed) |
| Worker → Core | authenticated API calls | escalation, invoicing, payouts, period rollover |
| **Core(A) ↔ Core(B)** cross-org | **signed, encapsulated Boundary API** + brokered file grants; provenance stripped per hop | A never sees B's internals; chains re-encapsulate so A never learns C exists |
| Non-WS entity | client-system **adapter** (email / Phrase / API) | bounded by that tool's surface |

### The outbox pattern (why no drift)
State + status commit in one transaction **together with** an `outbox` row. A relay publishes outbox rows to the broker. Consumers (reporting, workers) are eventually-consistent — but **truth is already committed in the core**, so a lost/late event never corrupts state. This is the structural fix for the ERP's sync/drift/repair-cron class of bugs.

### Domain events (illustrative)
`RequestCreated · PlanRatified · ActivityPublished · PerformerAccepted · OutputSubmitted · QAPassed · Delivered · BoundarySignedOff · Verified · BillableEventEmitted · InvoiceRaised · PayoutRaised · WalletDeducted/Settled/Refunded · PeriodClosed`. Events drive *reporting, notifications, and integrations* — never state derivation.

---

## 6. Key data-flow — brief → delivered → billed (the 2-touchpoint path, technically)

```
1. Intake      Channel/UI → Gateway → Core.Lifecycle: create REQUEST (source_channel, brief, files→FILE_REF via File Broker)
2. Compose     Core → AI Composer (enclave): reads THIS workspace's config; returns PROPOSAL
                 (offering, activity tree, performers, deadline, scope, price). Bytes stay in the enclave.
3. Ratify #1   Owner approves in UI → Core writes ASSIGNMENT + ACTIVITY tree in ONE txn; state+status set together
4. Mobilize    Core → Channel Gateway (async): one-tap payload per activity; WS-chat first, escalate to WhatsApp/SMS
                 Performer taps accept → webhook → Core sets ACCESS_GRANT_ROLE.role_status=accepted
5. Perform     Human/agent/tool produces output → ACTIVITY_IO(output) → FILE_REF; progress auto-logged
6. QA          qa_policy: auto (agent-safe) or human reviewer Pass/Fail
7. Assemble    When sibling activities + child assignments terminal → deliverable assembled; owner BOUNDARY_SIGNOFF
8. Deliver     Written to requester's store (their property); status roll-up already visible throughout
9. Verify #2   AI pre-computes reconciliation → verifier one-tap CONFIRM (the gate)
10. Money      Core.Money emits BILLABLE_EVENT (immutable) → fans out:
                 → Invoicing (if billing on): WS invoice / external connector / data-out
                 → Payout: PAYOUT_LINE off verified work (rolling), independent of client payment
                 → Wallet: settle the deduction; refund on cancel
11. Loop       ongoing → next period (Type-B SERVICE_PERIOD) · recurring → next cycle · one-off → done
```
Human touchpoints across all of this: **two** (step 3, step 9). Cross-org (Phase 2) inserts a `BOUNDARY_NODE` at step 4 — the performer *is* another workspace, which runs steps 1–11 internally and opaquely.

---

## 7. Security & isolation architecture

**The defensibility principle (vision §8):** *the operator cannot read a BYOK tenant's data — cryptographically, not by promise.* Every mechanism below serves it. This maps to the PRD's SEC-1…SEC-14. **The full security program** (data residency, threat model, bot/DDoS, AI-injection, monitoring, IR, compliance) is in **[`security.md`](./security.md)**.

| Control | Mechanism | PRD |
|---|---|---|
| **Workspace isolation (crypto)** | separate keys per workspace; **BYOK** for regional/sovereign; sovereign tenants can get schema-/DB-level separation (**⚠️ Bhavya:** RLS-pooled vs schema-per-tenant vs db-per-tenant). On BYOK, operator reads return ciphertext — **not decryptable, incl. the client list.** | SEC-8 |
| **Entity isolation (policy)** | **Postgres RLS** on `(workspace_id, operating_entity_id)`; default isolated; `entity_isolation` flag; entity-delegated module-admins can blind even the org admin | SEC-6 |
| **Control plane, not content** | the graph holds `file_ref` pointers only; **never custodies bytes** | SEC-1 |
| **Sealed zero-retention enclave** | bytes pulled ephemerally → compute → return → retain nothing; **locked egress, ephemeral FS**; access flows to the *tool*, never a person | SEC-3 |
| **Two processing modes by tier** | **Option B** (WS-controlled regional enclave) for shared/regional; **Option A** (in-environment runtime, **no egress**) required for sovereign — content-processing/AI runs inside the tenant's own environment. Phase 2+. | SEC-5 |
| **Two-layer need-to-know** | (1) **tool-pull scope** — what WS-the-tool may fetch from a tenant at all (the scoped credential); (2) **user-view scope** — POV-scoping per role. Both server-side. | SEC-6 |
| **Scoped tenant-API credential** | **JIT, least-privilege, short-lived per-grant tokens** minted by the File Broker; never a standing broad credential. A leak exposes **one file for minutes**. The crown-jewel surface. | SEC-7 |
| **No-human-bytes governance** | **no tenant content in logs**, no human debugging on raw data, stateless AI; enforced, not policy | SEC-4 |
| **Cross-org encapsulation** | opaque `BOUNDARY_NODE`; provenance stripped per hop; brokered file `ACCESS_GRANT` (scoped, expiring, revocable); deliverables written to the recipient's store | SEC-1, SEC-7 |
| **RBAC** | **server-authoritative**, config-driven (replaces frontend-JSON perms + email allowlists); persisted, POV-scoped GraphQL | SEC-6 |
| **Encryption at rest** | field-level (Fernet-class) for cost/pay/PII; salary never in plaintext | NFR-2 |
| **Tamper-evident audit** | append-only `AuditEvent`, **tenant-inspectable**, covers **operator/admin actions** ("don't-trust-us-verify") | SEC-9 |
| **Identity & revocation** | OIDC/SSO federation; **revoke SSO → live access ends**; freelancers on their own portable identity; personal workspace **unreachable from any org** (SEC-12). Phase 2. | SEC-10, SEC-12 |
| **No cross-tenant training** | composer/allocator per-tenant, stateless, zero-retention; cross-tenant training **prohibited**; any training consent-tiered, sovereignty excluded by design | SEC-13 |

---

## 8. Deployment topology

`Workspace.deployment_tier` selects the tier at provisioning. **The guarantee scales with the tier (vision §8):**

| Tier | Storage | Processing/AI | Keys | **Operator can read?** | Infra |
|---|---|---|---|---|---|
| **Shared** | WS multi-tenant (RLS) | WS enclave (Option B) | WS-managed | Yes (custodial) | shared cluster |
| **Regional** | WS, region-pinned | WS enclave, regional (Option B) | **BYOK** | **No (cryptographic)** | region-scoped cluster |
| **Sovereign** | Tenant infra, **no egress** | In-environment runtime (Option A) | **BYOK** | **No (cryptographic)** | isolated infra / own cloud |

- The enclave, File Broker, and Channel Gateway deploy **per region** so bytes and PII never leave residency.
- *(EZ resells these as its Standard/Compliant/Private tiers — a mapping, not a product distinction.)*
- Entity→separate-workspace migration (Layer 5) is a **data-separation operation** (re-key + move into a new keyed store) — supported, but heavier than a config toggle. Flagged honestly.

### 8.1 Provisioning & tier resolution (backend)

**The tier is a provisioning profile, not a label.** Choosing it at creation selects a recipe of *storage + keys + compute + network*, and it governs how **every** later request is routed. The isolation ladder itself is committed in `security.md` §2.2; this is the mechanism that runs it.

**The linchpin — a global tenant registry.** One small control-plane directory maps each workspace to its *placement*. It holds **no tenant content** — only routing metadata — and is consulted once per request.

```jsonc
tenant_registry = {
  "workspace_id":   "ws_ez",
  "org_code":       "EZ",
  "tier":           "shared",              // shared | regional | sovereign
  "region":         "in",
  "db_endpoint":    "pg-shared-in",        // which cluster/instance
  "schema_or_db":   "public",              // shared tables | tenant schema | dedicated db
  "key_ref":        "kms:platform/ez",     // platform KEK  OR  customer KMS ARN (BYOK)
  "store_endpoint": "s3://ws-in/ez/",      // WS store | tenant cloud | tenant infra
  "enclave_endpoint":"enclave-in",         // regional enclave | in-environment runtime
  "status":         "provisioning"         // provisioning → active → suspended
}
```

**Per-request resolution — the tier drives exactly three things: which DB · which key · which enclave.**
```
1. authN            → (workspace_id, operating_entity_id)
2. reg = registry[workspace_id]                       // one lookup
3. conn = connect(reg.db_endpoint, reg.schema_or_db)  // shared cluster | tenant schema | dedicated DB
4. SET app.workspace_id, app.operating_entity_id      // RLS session scope (shared/regional)
5. dek = KMS.unwrap(reg.key_ref, wrapped_data_key)    // envelope decrypt (BYOK ⇒ customer KMS)
6. content ops      → route to reg.enclave_endpoint   // regional | in-environment
```

**Keys — envelope encryption is why "operator can't read" is a fact.** Each record/field is encrypted with a **data key (DEK)**; the DEK is wrapped by the tenant's **master key (KEK)** in KMS/HSM. Shared → KEK platform-managed (custodial). Regional/Sovereign → KEK in the **customer's KMS**; to read anything the platform must call *their* KMS to unwrap. **Revoke the key → the platform physically cannot decrypt** — the crypto-erase / off-switch.

**What each tier provisions & requires at creation:**
| Tier | Backend provisioning | Extra inputs required at creation |
|---|---|---|
| **Shared** | insert registry row + RLS scope; content → shared store, per-tenant prefix + DEK | none beyond the 3 fields (region defaulted) |
| **Regional** | create tenant **schema** (or region cluster); register **BYOK** key; store → tenant cloud / WS-region | **residency region** · **BYOK key ref** · optional connected-cloud config |
| **Sovereign** | provision **dedicated DB/instance** (their infra allowed) + wire **HSM**; deploy **in-environment enclave**; lock egress | **target environment** · **HSM/KMS details** · **network/VPC + no-egress** · compliance attestations |

**Provisioning state machine.** `provisioning → active`. Shared reaches `active` in seconds (row insert). **Regional/Sovereign cannot reach `active` without their BYOK key** (FR-1.3); sovereign involves IaC/ops orchestration. *Region and BYOK cannot be deferred* — you can't retrofit where bytes physically live or whose key encrypts them.

**Components this implies (to build):** the **tenant registry** service · a **provisioning orchestrator** (per-tier recipe; IaC for regional/sovereign) · a **data-source resolver** (routes the connection by tier) · **KMS integration with BYOK** (envelope encryption, per-tenant KEK, revoke) · **RLS session-scoping middleware** · an **enclave-endpoint resolver**. **Tier migration** (e.g. shared→sovereign) is a data-move + re-key operation, not a toggle. *(Bhavya QAs the RLS/KMS implementation; the mechanism is the committed §11.4 call.)*

---

## 9. Reliability & the ERP failure classes we design out

| ERP failure class | Structural fix here |
|---|---|
| ERP↔WS sync drift, rollback-by-delete | **one graph, one system, zero sync** (§1, §3) |
| Google-Sheets-as-database | typed Postgres; **ledger is the source of truth** |
| Status drift, repair crons | **status derived in the write transaction** (§4, §5) |
| ~132 fire-and-forget management commands | **Task Runtime** with retry + audit (§3) |
| Untested money math, xlsx imports | typed `Decimal`, **parity-test catalog before any money code**, live-fed (no imports) |
| Frontend-JSON permissions, email allowlists | server-authoritative, config-driven RBAC (§7) |

---

## 10. Engineering conventions — the efficient way to write the code

**The point of this section:** the ERP failed less on *choice of framework* than on *how the code was written* — sheets used as a database, tenant rules hardcoded, status recomputed by crons, money math untested. These conventions are what keep WS 3.0 from repeating that. **They are binding, not stylistic.**

| # | Convention | Rule | Never |
|---|---|---|---|
| **C1** | **Config, not code** | Behaviour is resolved from config rows at runtime. A new tenant/offering/rule is *data*. | `if tenant == "EZ"`; any org-specific branch |
| **C2** | **Status in the write txn** | Derive `status` in the same transaction that changes `state`; store it. | a cron/job that "recomputes" or "repairs" status |
| **C3** | **Outbox for events** | Emit domain events by writing an `outbox` row in the same txn; a relay publishes. | dual-writing to the DB and a broker separately |
| **C4** | **RLS by default** | Every query is scoped by `(workspace_id, operating_entity_id)` at the data layer. | ad-hoc `WHERE` scoping in app code; trusting the client |
| **C5** | **Typed, idempotent money** | `Decimal` + explicit currency; money ops carry an idempotency key; the ledger is append-only. | floats; mutable balances as source of truth; untested math |
| **C6** | **Capability gating** | A turned-off capability's fields/endpoints don't exist for that workspace. | collecting/validating data a capability doesn't need |
| **C7** | **Suggest, not act (AI)** | The composer/allocator return *proposals*; a human ratifies before anything is real. | auto-committing an AI plan or allocation |
| **C8** | **One graph, one txn** | Config/lifecycle/allocation/money mutate the graph in one transaction, in-process. | networked service-to-service sync to keep the graph consistent |
| **C9** | **Content stays in the enclave** | The core receives `file_ref`s + scoped credentials, never bytes; bytes live and die in the enclave. | passing raw content through the core or persisting it |
| **C10** | **Persisted, POV-scoped GraphQL** | Only allowlisted queries; resolvers enforce role + scope server-side. | arbitrary client queries; client-side permission checks |

### The patterns, concretely

**C1 — resolve from config (no tenant branches):**
```python
# GOOD — behaviour is data
offering = catalog.get(assignment.offering_id, version=assignment.offering_version)
tree     = offering.activity_templates                 # the plan shape is config
weights  = policy.objective_weights                    # allocation is config
# BAD — never do this
# if workspace.code == "EZ": tree = [...]              # hardcoded org rule
```

**C2 + C3 — status derived in-txn, event via outbox (kills drift):**
```python
with db.transaction():
    activity.state  = "delivered"
    activity.status = derive_status(activity)          # same txn, stored — not a cron
    assignment.status = rollup(assignment)             # worst-of over the tree, same txn
    outbox.append(Event("ActivityDelivered", activity.id))   # same txn
# a separate relay publishes committed outbox rows → reporting/workers
```

<details>
<summary>▸ JSON: a domain event (outbox → broker)</summary>

```jsonc
{
  "event_id": "evt_uuid",
  "type": "BillableEventEmitted",
  "workspace_id": "ws_uuid", "operating_entity_id": "oe_uuid",
  "occurred_at": "2026-07-17T10:00:00Z",
  "payload": { "billable_event_id": "be_uuid", "assignment_ref": "asg_uuid", "amount": 800, "currency": "USD" },
  "trace_id": "…"          // events drive reporting/notify/integration — never state derivation
}
```
</details>

<details>
<summary>▸ JSON: a persisted, POV-scoped GraphQL query (C10)</summary>

```jsonc
// Client sends an ID, not a query string — server has the allowlisted document.
{ "id": "q_workConsole_requestTree_v1",
  "variables": { "request_id": "req_uuid" } }
// Resolver enforces: actor role ∈ {owner,performer,…} AND row scope (workspace_id, operating_entity_id).
// A performer sees only their activities; a sibling entity sees nothing.
```
</details>

**C5 — money is typed, idempotent, append-only:**
```python
# deduct at assignment-create, settle at verify, refund on cancel — each idempotent
ledger.append(WalletEntry(op="deduct", delta=Money("-800", "USD"),
                          ref=assignment.id, idem_key=f"deduct:{assignment.id}"))
# balance is a projection of the ledger, never the source of truth
```

**Definition of done for any feature:** config-driven (C1) · state+status atomic (C2) · events via outbox (C3) · RLS-scoped (C4) · money typed+tested against the parity catalog (C5, NFR-7) · gated by capability (C6) · no content through the core (C9).

---

## 11. Open architecture decisions — ⚠️ Bhavya sign-off

1. **Core shape** — modular-monolith core (recommended, tenet #1) vs full microservices.
2. **Engine model** — transactional + outbox (recommended) vs event-sourced.
3. **API** — GraphQL + persisted queries (assumed) vs REST.
4. **Isolation mechanism** — **decided** (`security.md` §2.2): **RLS-pooled for Shared; dedicated DB + BYOK for Regional/Sovereign** (never table-per-tenant). Bhavya to QA the RLS/KMS implementation.
5. **Async infra** — task runner (Celery / RQ / Temporal) and broker (Redis Streams / Kafka / NATS).
6. **Stack confirmation** — FastAPI (proposed) vs staying on Django; Postgres version; deployment substrate.
7. **Repository layout** — how many repos we build. Recommendation: **~2** — one **product monorepo** (core + frontend + File Broker/Channel Gateway/Reporting/Task Runtime as internal services) plus a **separate AI Composer / enclave repo**. The enclave is proposed as its own repo because it deploys into the sealed, zero-retention, sometimes in-tenant / no-egress environment and should stay minimal and independently auditable — **this specific split is for Bhavya to confirm.** The fork: if Bhavya prefers a classic backend/frontend split, it becomes **3** (backend + frontend + enclave). Everything else stays a module, not a repo, to avoid cross-repo sync.

**None of these reshape the data model or the layer design** — they select mechanisms at the marked points.

---

## 12. Build path (gates, not a sprint)

```
DESIGN (now, no code)
   spec.md ✅  (PRD/BRS, field-level)   ·   architecture.md ✅  (this doc)
        ├─ Joy answers the [J] items ──┐
        ├─ Bhavya answers §11 ─────────┤→ ARCHITECTURE v2 → sign-off
        └─ parity-test catalog + migration mapping (last solo pieces)
                 ▼
   BUILD (only on Shreyanshi's "go")
   scaffold → typed model (§4) → PARITY TESTS FIRST → migration →
   Phase-1 features → strangler-fig cutover (capability-by-capability)
                 ▼
   PHASE 2 — cross-org / multi-tenant (boundary + entity-isolation already in; no rewrite)
```

**Gates:** Design (solo) → Joy + Bhavya inputs → **Architecture v2 sign-off (Bhavya)** → Shreyanshi's "build" → strangler-fig cutover.

---

## 13. What to review here

- **§3** — the modular-monolith-core call (decision #1). This is the most consequential architecture choice; it's deliberately conservative to avoid rebuilding the ERP's sync pain.
- **§4** — the data model / DB diagram. Is the Entity+Relationship spine and the work-graph tree right?
- **§5** — communications + the outbox pattern (how we kill drift for good).
- **§7–§8** — isolation and deployment tiers.
- **§10** — the engineering conventions (the binding "how to write the code" rules).
- **§11** — the six open decisions that need your sign-off.

The *what* (layers, fields, use-cases, how each scenario runs) is in **[`spec.md`](./spec.md)**.

---

## Appendix A — Formal JSON Schema (the interface contract)

**This is the machine-validatable contract** (JSON Schema Draft 2020-12) for the core entities — types, `required`, `enum`s, and constraints. Unlike the illustrative JSON in `spec.md`, a build's payloads can be **validated against this**, so "does it match the spec?" becomes a mechanical check. Enums are the locked value sets; `[J]` weights and Bhavya's mechanism choices don't appear here (they're config/values, not shape). `additionalProperties:false` on records means **no undeclared fields** — undeclared config lives in the explicit `config`/`jsonb` objects only.

> Scope: the load-bearing entities. Config records (Offering/Skill/Rate/AllocationPolicy) are summarized; their full schema follows the same pattern. This appendix is the source of truth for field shape; the ER (§4) is the source of truth for relationships.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ws3/schema/core.json",
  "title": "WS 3.0 — Core Entities",
  "$defs": {
    "uuid":      { "type": "string", "format": "uuid" },
    "ts":        { "type": "string", "format": "date-time" },
    "date":      { "type": "string", "format": "date" },
    "currency":  { "type": "string", "minLength": 3, "maxLength": 3 },
    "money": {
      "type": "object", "additionalProperties": false,
      "properties": { "amount": { "type": "number", "minimum": 0 }, "currency": { "$ref": "#/$defs/currency" } },
      "required": ["amount", "currency"]
    },
    "derivedStatus": { "type": "string", "enum": ["not_started","on_track","slightly_delayed","critical","completed"] },

    "Workspace": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "org_legal_name": { "type": "string" },
        "org_display_name": { "type": "string" },
        "org_code": { "type": "string", "pattern": "^[A-Z0-9_-]+$" },
        "region": { "type": "string" },
        "deployment_tier": { "type": "string", "enum": ["shared","regional","sovereign"] },
        "byok_key_ref": { "type": ["string","null"] },
        "admin_email": { "type": "string", "format": "email" },
        "modules_available": { "type": "array", "items": { "type": "string" } },
        "status": { "type": "string", "enum": ["provisioning","active","suspended"] }
      },
      "required": ["id","org_legal_name","org_code","deployment_tier","admin_email","status"],
      "allOf": [
        { "if": { "properties": { "deployment_tier": { "enum": ["regional","sovereign"] } } },
          "then": { "properties": { "byok_key_ref": { "type": "string" } }, "required": ["byok_key_ref"] } }
      ]
    },

    "OperatingEntity": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "workspace_id": { "$ref": "#/$defs/uuid" },
        "legal_name": { "type": "string" },
        "code": { "type": "string" },
        "country": { "type": "string", "minLength": 2, "maxLength": 2 },
        "billing_currency": { "$ref": "#/$defs/currency" },
        "tax_profile": { "type": ["string","null"] },
        "invoice_prefix": { "type": ["string","null"] },
        "entity_isolation": { "type": "boolean", "default": true },
        "module_admin_scope": { "type": "string", "enum": ["workspace","entity"], "default": "workspace" }
      },
      "required": ["id","workspace_id","legal_name","code","country"]
    },

    "RootIdentity": {
      "type": "object", "additionalProperties": false,
      "description": "GLOBAL — no workspace_id. One per human.",
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "owner_auth_ref": { "type": "string" },
        "personal_workspace_ref": { "type": ["string","null"] },
        "portable_reputation": { "type": "object" }
      },
      "required": ["id","owner_auth_ref"]
    },

    "Entity": {
      "type": "object", "additionalProperties": false,
      "description": "The actor (org or person). Formerly 'Party'.",
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "workspace_id": { "$ref": "#/$defs/uuid" },
        "type": { "type": "string", "enum": ["org","person"] },
        "display_name": { "type": "string" }
      },
      "required": ["id","workspace_id","type","display_name"]
    },

    "Person": {
      "type": "object", "additionalProperties": false,
      "description": "A membership — one per (human, workspace).",
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "workspace_id": { "$ref": "#/$defs/uuid" },
        "entity_id": { "$ref": "#/$defs/uuid" },
        "root_identity_id": { "$ref": "#/$defs/uuid" },
        "email": { "type": "string", "format": "email" },
        "entity_role": { "type": "string", "enum": ["owner","performer","reviewer","verifier","admin","requester"] },
        "contract_type": { "type": ["string","null"], "enum": ["payroll","contractor",null] },
        "operating_entity_id": { "oneOf": [ { "$ref": "#/$defs/uuid" }, { "type": "null" } ] },
        "sso_federated": { "type": "boolean", "default": false },
        "cost_encrypted": { "type": ["string","null"] },
        "bank_ref": { "type": ["string","null"] },
        "status": { "type": "string", "enum": ["invited","active","offboarded"] }
      },
      "required": ["id","workspace_id","entity_id","root_identity_id","email","entity_role","status"]
    },

    "PersonSkill": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "workspace_id": { "$ref": "#/$defs/uuid" },
        "person_id": { "$ref": "#/$defs/uuid" },
        "skill_id": { "$ref": "#/$defs/uuid" },
        "proficiency": { "type": "integer", "minimum": 1, "maximum": 5 },
        "status": { "type": "string", "enum": ["declared","verified"] }
      },
      "required": ["id","workspace_id","person_id","skill_id","proficiency","status"]
    },

    "Relationship": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "workspace_id": { "$ref": "#/$defs/uuid" },
        "operating_entity_id": { "$ref": "#/$defs/uuid" },
        "type": { "type": "string", "enum": ["employment","client","vendor","tenant"] },
        "from_entity": { "$ref": "#/$defs/uuid" },
        "to_entity": { "$ref": "#/$defs/uuid" },
        "vendor_type": { "type": ["string","null"], "enum": ["external","ws_tenant",null] },
        "linked_org_ref": { "type": ["string","null"] },
        "invoice_code": { "type": ["string","null"] },
        "config": { "type": "object" },
        "status": { "type": "string", "enum": ["pending","active","suspended","ended"] }
      },
      "required": ["id","workspace_id","operating_entity_id","type","from_entity","to_entity","status"],
      "allOf": [
        { "if": { "properties": { "type": { "const": "vendor" }, "vendor_type": { "const": "ws_tenant" } } },
          "then": { "required": ["linked_org_ref"] } }
      ]
    },

    "Offering": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "workspace_id": { "$ref": "#/$defs/uuid" },
        "name": { "type": "string" },
        "version": { "type": "integer", "minimum": 1 },
        "delivery_model": { "type": "string", "enum": ["deliverable","retainer","outcome"] },
        "billing_model": { "type": "string", "enum": ["unit_x_price","flat_retainer","retainer_plus_usage","outcome"] },
        "levels": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["id","workspace_id","name","version","delivery_model","billing_model"]
    },

    "Engagement": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "workspace_id": { "$ref": "#/$defs/uuid" },
        "client_relationship_id": { "$ref": "#/$defs/uuid" },
        "delivery_model": { "type": "string", "enum": ["deliverable","retainer","outcome"] },
        "billing_model": { "type": "string", "enum": ["unit_x_price","flat_retainer","retainer_plus_usage","outcome"] }
      },
      "required": ["id","workspace_id","client_relationship_id","delivery_model","billing_model"]
    },

    "ServicePeriod": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "engagement_id": { "$ref": "#/$defs/uuid" },
        "period": { "type": "string" },
        "status": { "type": "string", "enum": ["open","closed","verified","billed"] },
        "outcome_metric": { "type": ["number","null"] }
      },
      "required": ["id","engagement_id","period","status"]
    },

    "Request": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "workspace_id": { "$ref": "#/$defs/uuid" },
        "operating_entity_id": { "$ref": "#/$defs/uuid" },
        "requester_id": { "$ref": "#/$defs/uuid" },
        "engagement_id": { "oneOf": [ { "$ref": "#/$defs/uuid" }, { "type": "null" } ] },
        "brief": { "type": "string" },
        "input_files": { "type": "array", "items": { "$ref": "#/$defs/uuid" } },
        "deadline": { "$ref": "#/$defs/date" },
        "source_channel": { "type": "string", "enum": ["manual","email","phrase","api"] },
        "state": { "type": "string", "enum": ["created","live","delivered","verified","billed","paused","cancelled"] },
        "status": { "$ref": "#/$defs/derivedStatus" }
      },
      "required": ["id","workspace_id","operating_entity_id","requester_id","brief","deadline","source_channel","state","status"]
    },

    "Proposal": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "request_id": { "$ref": "#/$defs/uuid" },
        "proposed_offering_id": { "$ref": "#/$defs/uuid" },
        "proposed_level": { "type": "string" },
        "scope_sheet": {
          "type": "object", "additionalProperties": false,
          "properties": {
            "unit_type": { "type": "string" },
            "unit_count": { "type": "number", "minimum": 0 },
            "assumptions": { "type": "array", "items": { "type": "string" } }
          },
          "required": ["unit_type","unit_count"]
        },
        "proposed_activities": { "type": "array", "items": { "type": "object" } },
        "proposed_deadline": { "$ref": "#/$defs/date" },
        "proposed_price": { "oneOf": [ { "$ref": "#/$defs/money" }, { "type": "null" } ] },
        "confidence": { "type": "object", "additionalProperties": { "type": "number", "minimum": 0, "maximum": 1 } },
        "clarifying_questions": { "type": "array", "items": { "type": "string" } },
        "provenance": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["id","request_id","proposed_offering_id","scope_sheet","confidence"]
    },

    "Assignment": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "request_id": { "$ref": "#/$defs/uuid" },
        "workspace_id": { "$ref": "#/$defs/uuid" },
        "operating_entity_id": { "$ref": "#/$defs/uuid" },
        "offering_id": { "$ref": "#/$defs/uuid" },
        "offering_version": { "type": "integer", "minimum": 1 },
        "level": { "type": "string" },
        "unit_type": { "type": "string" },
        "unit_count": { "type": "number", "minimum": 0 },
        "delivery_model": { "type": "string", "enum": ["deliverable","retainer","outcome"] },
        "billing_model": { "type": "string", "enum": ["unit_x_price","flat_retainer","retainer_plus_usage","outcome"] },
        "owner_id": { "$ref": "#/$defs/uuid" },
        "price": { "oneOf": [ { "$ref": "#/$defs/money" }, { "type": "null" } ] },
        "invoice_code": { "type": ["string","null"] },
        "payment_type": { "type": ["string","null"], "enum": ["prepaid","postpaid",null] },
        "deadline": { "$ref": "#/$defs/date" },
        "state": { "type": "string", "enum": ["created","published","delivered","verified"] },
        "status": { "$ref": "#/$defs/derivedStatus" }
      },
      "required": ["id","request_id","workspace_id","operating_entity_id","offering_id","unit_type","unit_count","delivery_model","billing_model","owner_id","state","status"]
    },

    "Activity": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "assignment_id": { "$ref": "#/$defs/uuid" },
        "workspace_id": { "$ref": "#/$defs/uuid" },
        "operating_entity_id": { "$ref": "#/$defs/uuid" },
        "skill_id": { "$ref": "#/$defs/uuid" },
        "performer_type": { "type": "string", "enum": ["human","agent","human_tool"] },
        "performer_id": { "oneOf": [ { "$ref": "#/$defs/uuid" }, { "type": "null" } ] },
        "dependency_activity_id": { "oneOf": [ { "$ref": "#/$defs/uuid" }, { "type": "null" } ] },
        "unit_count": { "type": "number", "minimum": 0 },
        "start_by": { "$ref": "#/$defs/date" },
        "deliver_by": { "$ref": "#/$defs/date" },
        "sort_order": { "type": "integer", "minimum": 1 },
        "qa_policy": { "type": "string", "enum": ["auto","human"] },
        "outputs": { "type": "array", "items": { "$ref": "#/$defs/uuid" } },
        "progress": { "type": "number", "minimum": 0, "maximum": 1 },
        "state": { "type": "string", "enum": ["created","published","delivered"] },
        "status": { "$ref": "#/$defs/derivedStatus" }
      },
      "required": ["id","assignment_id","workspace_id","operating_entity_id","skill_id","performer_type","sort_order","qa_policy","state","status"]
    },

    "Allocation": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "activity_id": { "$ref": "#/$defs/uuid" },
        "candidates_scored": {
          "type": "array",
          "items": {
            "type": "object", "additionalProperties": false,
            "properties": {
              "performer_id": { "$ref": "#/$defs/uuid" },
              "score": { "type": "number", "minimum": 0, "maximum": 1 },
              "reasons": { "type": "array", "items": { "type": "string" } }
            },
            "required": ["performer_id","score"]
          }
        },
        "proposed_performer_id": { "$ref": "#/$defs/uuid" },
        "alternates": { "type": "array", "items": { "$ref": "#/$defs/uuid" } }
      },
      "required": ["id","activity_id","proposed_performer_id"]
    },

    "Mobilization": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "activity_id": { "$ref": "#/$defs/uuid" },
        "channel": { "type": "string", "enum": ["ws_chat","whatsapp","sms","email"] },
        "sent_at": { "$ref": "#/$defs/ts" },
        "response": { "type": ["string","null"], "enum": ["accepted","declined",null] },
        "escalation_step": { "type": "integer", "minimum": 0 }
      },
      "required": ["id","activity_id","channel","escalation_step"]
    },

    "AccessGrantRole": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "person_id": { "$ref": "#/$defs/uuid" },
        "scope": { "type": "string" },
        "role_type": { "type": "string", "enum": ["activity","assignment","workspace"] },
        "role_status": { "type": "string", "enum": ["pending","accepted","rejected"] },
        "reject_reason": { "type": ["string","null"] }
      },
      "required": ["id","person_id","scope","role_type","role_status"]
    },

    "FileRef": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "workspace_id": { "$ref": "#/$defs/uuid" },
        "store_location": { "type": "string" },
        "storage_tier": { "type": "string", "enum": ["ws_managed","connected_cloud","own_infra"] },
        "key": { "type": "string" },
        "checksum": { "type": "string" },
        "size": { "type": "integer", "minimum": 0 },
        "mime": { "type": "string" },
        "owner_entity_id": { "$ref": "#/$defs/uuid" }
      },
      "required": ["id","workspace_id","store_location","key","owner_entity_id"]
    },

    "AccessGrant": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "file_ref_id": { "$ref": "#/$defs/uuid" },
        "grantee": { "type": "string" },
        "scope": { "type": "array", "items": { "type": "string" } },
        "expiry": { "$ref": "#/$defs/ts" },
        "revocable": { "type": "boolean" }
      },
      "required": ["id","file_ref_id","grantee","scope","expiry","revocable"]
    },

    "BillableEvent": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "assignment_ref": { "$ref": "#/$defs/uuid" },
        "workspace_id": { "$ref": "#/$defs/uuid" },
        "operating_entity_id": { "$ref": "#/$defs/uuid" },
        "client_relationship_id": { "$ref": "#/$defs/uuid" },
        "verified_by": { "$ref": "#/$defs/uuid" },
        "verified_at": { "$ref": "#/$defs/ts" },
        "unit_count": { "type": "number", "minimum": 0 },
        "unit_price": { "type": "number", "minimum": 0 },
        "amount": { "type": "number", "minimum": 0 },
        "currency": { "$ref": "#/$defs/currency" },
        "billing_model": { "type": "string", "enum": ["unit_x_price","flat_retainer","retainer_plus_usage","outcome"] }
      },
      "required": ["id","assignment_ref","workspace_id","operating_entity_id","client_relationship_id","verified_by","verified_at","amount","currency","billing_model"]
    },

    "Invoice": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "operating_entity_id": { "$ref": "#/$defs/uuid" },
        "client_relationship_id": { "$ref": "#/$defs/uuid" },
        "invoice_number": { "type": "string" },
        "invoice_code": { "type": ["string","null"] },
        "grouping_rule": { "type": "string", "enum": ["per_entity_per_period","per_request"] },
        "line_items": { "type": "array", "items": { "$ref": "#/$defs/InvoiceLine" } },
        "tax": { "type": "object" },
        "status": { "type": "string", "enum": ["draft","raised","sent","paid","disputed"] }
      },
      "required": ["id","operating_entity_id","client_relationship_id","invoice_number","grouping_rule","status"]
    },
    "InvoiceLine": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "invoice_id": { "$ref": "#/$defs/uuid" },
        "billable_event_id": { "$ref": "#/$defs/uuid" },
        "rate_snapshot": { "type": "object" }
      },
      "required": ["id","invoice_id","billable_event_id"]
    },

    "Wallet": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "relationship_id": { "$ref": "#/$defs/uuid" },
        "denomination": { "type": "string", "default": "credits" },
        "balance": { "type": "number" },
        "cost_per_credit": { "type": "number", "minimum": 0 },
        "consumption_policy": { "type": "string", "enum": ["none","fifo","lifo"], "default": "fifo" },
        "expiry_enabled": { "type": "boolean", "default": false },
        "negative_balance_allowed": { "type": "boolean", "default": false }
      },
      "required": ["id","relationship_id","denomination","balance"]
    },
    "WalletLot": {
      "type": "object", "additionalProperties": false,
      "description": "Materializes only when expiry_enabled or lotting is on.",
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "wallet_id": { "$ref": "#/$defs/uuid" },
        "credits": { "type": "number", "minimum": 0 },
        "remaining": { "type": "number", "minimum": 0 },
        "validity": { "oneOf": [ { "$ref": "#/$defs/date" }, { "type": "null" } ] }
      },
      "required": ["id","wallet_id","credits","remaining"]
    },
    "WalletLedger": {
      "type": "object", "additionalProperties": false,
      "description": "Append-only. The source of truth. Balance is a projection.",
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "wallet_id": { "$ref": "#/$defs/uuid" },
        "op": { "type": "string", "enum": ["deduct","settle","refund"] },
        "delta": { "type": "number" },
        "ref": { "type": "string" },
        "idem_key": { "type": "string" },
        "at": { "$ref": "#/$defs/ts" }
      },
      "required": ["id","wallet_id","op","delta","idem_key","at"]
    },

    "PayoutLine": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "billable_event_id": { "$ref": "#/$defs/uuid" },
        "performer_id": { "$ref": "#/$defs/uuid" },
        "period": { "type": "string" },
        "unit": { "type": "string", "default": "currency" },
        "amount": { "type": "number", "minimum": 0 },
        "status": { "type": "string", "enum": ["accrued","paid","exported"] }
      },
      "required": ["id","billable_event_id","performer_id","period","amount","status"]
    },

    "BoundaryNode": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "id": { "$ref": "#/$defs/uuid" },
        "activity_id": { "$ref": "#/$defs/uuid" },
        "linked_relationship_id": { "$ref": "#/$defs/uuid" },
        "maps_to_request_ref": { "type": "string" },
        "visible_status": { "$ref": "#/$defs/derivedStatus" },
        "deliverable_ref": { "oneOf": [ { "$ref": "#/$defs/uuid" }, { "type": "null" } ] },
        "opacity_level": { "type": "string", "enum": ["opaque","milestones","detailed"] }
      },
      "required": ["id","activity_id","linked_relationship_id","maps_to_request_ref","opacity_level"]
    },

    "DomainEvent": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "event_id": { "$ref": "#/$defs/uuid" },
        "type": { "type": "string" },
        "workspace_id": { "$ref": "#/$defs/uuid" },
        "operating_entity_id": { "$ref": "#/$defs/uuid" },
        "occurred_at": { "$ref": "#/$defs/ts" },
        "payload": { "type": "object" },
        "trace_id": { "type": "string" }
      },
      "required": ["event_id","type","workspace_id","occurred_at","payload"]
    }
  }
}
```

**How to use it as a gate:** every API payload and DB row for a core entity MUST validate against its `$defs` schema. The enums above are the **locked value sets** — a build that introduces, say, a `billing_model` outside `{unit_x_price, flat_retainer, retainer_plus_usage, outcome}` fails validation. The two isolation keys (`workspace_id`, `operating_entity_id`) are `required` on every tenant-scoped entity, so a row that forgets them can't validate — which is how the schema enforces isolation-by-construction. `[J]`/Bhavya items are deliberately absent (they're values/mechanisms, not shape), so filling them later doesn't change this contract.
