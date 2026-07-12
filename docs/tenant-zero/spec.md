# WS 3.0 — Product Requirements (PRD / BRS)

**The single product spec.** Everything a developer needs to build it, written so a client or stakeholder can also read it. **Companion:** [`architecture.md`](./architecture.md) — the technical *how it's built* for developers.

> **Product in one line:** WS 3.0 is a generic, multi-tenant platform that takes an organization from **onboarding through to delivering an assignment** — composing the plan with AI and asking a human to ratify twice. EZ is the first tenant, configured through the same product as everyone else.

### How to read this
- **Stakeholders / clients:** read the prose — goals (§1), personas (§2), what it looks like (§3), and the **base-case flow** of each workflow (§5). Skip the JSON.
- **Developers:** additionally read the **`▸ Data (JSON)`** blocks (click to expand), the edge-case tables, the numbered **FR-x.y** requirements, and the config surface (§6).
- **Conventions:** **FR-x.y** = testable requirement · **MUST/SHOULD** carry their usual force · **AC** = acceptance criteria · `(EZ: …)` = illustrative config only, never product behaviour · `[J]` = awaiting Joy · **⚠️ Bhavya** = architecture-owned.

**Contents:** §1 Goals · §2 Personas · §3 Surfaces · §4 Domain model & data-at-a-glance · **§5 The 15 workflows (base + edge cases + JSON + FRs)** · §6 Config surface (JSON) · §7 Cross-cutting · **§8 Data security, privacy & trust** · §9 Non-functional · §10 Phasing · §11 Open items · §12 Glossary · **Appendix A — worked example (row by row)**.

---

## 1. Goals & non-goals

**Goals**
- **G1** An org goes from *nothing* to *delivering* on bare-minimum info; the product fills the rest just-in-time.
- **G2** The delivery lifecycle runs with **exactly two human touchpoints** (ratify the plan, confirm the verify); the rest is AI-composed or system-derived.
- **G3** The product is **generic** — a translation agency, a design studio, and a research firm each run on it unchanged. Every org-specific value is config.
- **G4** Multiple legal entities within an org, and work *across* orgs, are first-class — with confidentiality guaranteed by construction.
- **G5** All commercial/financial ops (invoicing, wallet, payout, payroll) are absorbed and **improved**, never ported as-is — no shadow spreadsheets, no sync jobs, no drift.

**Non-goals (this release):** not a pricing marketplace; not a no-code scripting canvas (config is declarative + defaulted + archetype-seeded); not a content store (holds the *graph* + file *pointers*, never raw content).

**Success metrics:** time-to-first-delivery for a new workspace · human touchpoints per assignment (target 2) · % of plan accepted without edit · reporting drift (target: structurally zero).

---

## 2. Personas & actors

| Actor | Level | Does | Surface |
|---|---|---|---|
| **Platform Operator** | L0 | Provisions workspaces, sets tier + modules, assigns admin. No content access. | Operator console |
| **Workspace Admin** | L1 | Configures the operating model declaratively; ratifies AI-seeded config. | Setup/Admin console |
| **Module Admin** (optional) | L1 | Delegated admin for one module/entity (can be entity-scoped, blinding even the org admin). | Admin (scoped) |
| **Owner** | L2 | Ratifies the AI plan; signs off at the trust boundary. | Work console |
| **Performer** | L2 | Accepts an activity, produces the output. Human, AI agent, or human+tool. | One-tap channel; app optional |
| **Reviewer** | L2 | Pass/fail where QA policy needs a human. | Work console |
| **Verifier** | L2 | One-tap confirms the reconciliation — the billing gate. | Work console |
| **Requester** | ext/L2 | Submits brief+files+deadline; gets status + deliverable. | Any channel |

**Roles are product primitives; their names are config.** (EZ maps owner/performer/reviewer/verifier onto SWAT/QA/SME/pool — a relabel, not new behaviour.)

---

## 3. What the product looks like (surfaces / IA)

Role-scoped surfaces over **one work graph**. Each shows only what the actor's role and `(workspace_id, operating_entity_id)` scope permit.

1. **Operator Console (L0)** — workspace list, provisioning wizard, tier/module toggles, oversight. No tenant content.
2. **Setup / Admin Console (L1)** — the **readiness dashboard** ("you can deliver once these are set"), config editors, archetype picker, people directory, relationships.
3. **Work Console (L2)** — request inbox, the **plan-ratification screen** (AI draft, editable inline), the live work tree (parallel branches + status roll-up), the **verify screen** (pre-computed reconciliation, one-tap), delivery view.
4. **Performer surface** — mostly **channel-native**: a chat/WhatsApp/SMS message with one-tap Accept + output upload. App optional.
5. **Requester surface** — submit (or auto-created from email/tool), status roll-up, the deliverable, approve-if-required.
6. **Money surfaces** — invoicing / wallet / payout, each appearing **only when its capability is on**.

**Ambient AI, not a chatbot:** AI appears *inline* as suggestions a human approves — never a separate assistant to converse with.

---

## 4. Domain model & data at a glance

**Governing principles**
1. **Entity + Relationship** — an Entity (Org/Person) with typed Relationship edges (`employment/client/vendor/tenant`). Tenant/client/vendor are relationship *types*, not separate systems. A cross-org link is one edge — "vendor" from one side, "client" from the other.
2. **Capability-gated + JIT fields** — only fields a turned-on capability needs are asked; the rest surface at first use.
3. **Platform-generic** — roles, activities, money are generic; every EZ value is config.
4. **Efficiency-first** — AI composes, humans ratify; edges are channel-native.

**The work graph (BAT):** `Request` → `Assignment` (one offering; **Deliver is the mandatory last activity**) → `Activity` (input(s) → one performer → one skill → output(s)). A Request is a **tree**: independent branches run in parallel; dependent ones gate on their input (output→input).

**Config axes:** `delivery_model` ∈ {deliverable, retainer, outcome} × `billing_model` ∈ {unit×price, flat_retainer, retainer+usage, outcome}.

**Isolation keys:** `workspace_id` (crypto) · `operating_entity_id` (policy) — on every tenant record.

<details>
<summary>▸ Data (JSON): the entities at a glance</summary>

```jsonc
// Every tenant record carries these two keys — enforced by row-level security.
{ "workspace_id": "ws_uuid", "operating_entity_id": "oe_uuid" }

// The object graph (details per workflow below):
Workspace ─┬─ OperatingEntity[]
           ├─ Entity[] ──── Person | Org
           ├─ Relationship[]  // employment | client | vendor | tenant
           ├─ Offering[] ─── OfferingActivityTemplate[], Rate[]
           ├─ Skill[]
           ├─ Team[] / Role[]
           ├─ AllocationPolicy
           └─ Engagement[] ─ ServicePeriod[] (Type-B)
                 └─ Request[] ─ Proposal, Assignment[] ─ Activity[](tree)
                       Activity ─ ActivityIO[], Allocation, Mobilization, BoundaryNode?
                 Assignment ─ BillableEvent ─ InvoiceLine / PayoutLine
           Wallet ─ WalletLot[](FIFO), WalletLedger[](append-only)
           FileRef[] ─ AccessGrant[]     // pointers, never bytes
```
</details>

Field-level JSON for each record lives inline with its workflow below. The physical schema is in [`architecture.md`](./architecture.md) §4.

---

## 5. The workflows — base cases, edge cases, data & requirements

Fifteen epics. Each: **base-case flow → business rules → edge cases → Data (JSON) → FRs → acceptance criteria.**

---

### E1 · Workspace provisioning (L0)

**Base case**
1. Operator opens the provisioning wizard.
2. Enters **org name · deployment tier · admin email** (3 fields).
3. If tier = regional/sovereign, sets BYOK keys.
4. System creates the workspace, sets module availability, invites the admin.
5. Admin lands on the Setup home.

**Business rules** — provisioning MUST NOT ask beyond the 3 fields (+ keys if sovereign); everything else is deferred. EZ is provisioned through this same wizard — **no back-door**.

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Duplicate org code/name | Reject with a conflict; suggest an available code. |
| Sovereign tier, no BYOK keys | Block activation; workspace stays `provisioning`. |
| Admin invite bounces | Operator sees a delivery-failure flag; can re-issue. |
| Operator opens tenant content | Denied — L0 has provisioning/oversight scope only. |

<details>
<summary>▸ Data (JSON): Workspace</summary>

```jsonc
{
  "id": "ws_uuid",
  "org_legal_name": "Acme Translations Ltd",   // L0-set
  "org_display_name": "Acme",
  "org_code": "ACME",                            // unique
  "region": "in",
  "deployment_tier": "shared",                   // shared | regional | sovereign
  "byok_key_ref": null,                          // required if regional/sovereign
  "admin_email": "admin@acme.com",
  "modules_available": ["delivery","invoicing","wallet","people"],
  "status": "provisioning"                        // provisioning | active | suspended
}
```
</details>

**FRs** — FR-1.1 3-field provisioning · FR-1.2 tier drives isolation · FR-1.3 BYOK required before a sovereign workspace activates · FR-1.4 module availability set here, tunable later · FR-1.5 **no back-door** (EZ included).
**AC** — a workspace is created with ≤3 inputs; a sovereign workspace can't reach `active` without BYOK; the operator can never open a tenant's briefs/deliverables.

---

### E2 · Configuration & readiness (L1)

**Base case**
1. Admin picks an **industry archetype** (translation / creative / research / generic).
2. AI builds a **starter workspace**: catalog + capabilities, common skills, default roles, SLA + pricing bands, notification defaults.
3. The **readiness dashboard** lists only the gaps.
4. Admin **ratifies** each seeded item (entities, teams/roles, catalog, skills+pricing), edits as needed.
5. Admin sets the first client relationship + activates needed modules (Delivery always; others as required).
6. Minimum chain met → workspace flips **Operational**.

**Business rules** — admin **edits AI proposals, never authors from blank**. "Onboarded = can deliver": min chain = `entity · offering + skills + Delivery-skill · team · people · client/requester` (+ `pricing/wallet` **only if billing on**). Capability-gated + JIT. Archetypes carry **generic industry knowledge only** — never EZ templates.

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| "Generic" archetype | Near-empty starter; author manually; product still works. |
| Readiness gap left open | Stays `configuring`; can't publish a request; dashboard shows what's missing. |
| Billing off | Pricing/wallet/tax not asked; readiness ignores them. |
| Activity-template dependency cycle | Config validation rejects the catalog. |
| Currency/tax missing while billing on | Flagged as a blocking gap. |
| Catalog edited after go-live | **Versioned**; in-flight work keeps its snapshot; new work uses the new version. |

Config JSON (entity, offering, skill, rate, policies, archetype) is in **§6 Config surface**.

**FRs** — FR-2.1 archetype seeds a full starter · FR-2.2 ratify-not-author · FR-2.3 readiness computes gaps live · FR-2.4 capability-gated + JIT · FR-2.5 Operational only when the min chain is met · FR-2.6 archetypes generic · FR-2.7 catalog versioned; in-flight uses its snapshot · FR-2.8 everything declarative, no hardcoded org rules.
**AC** — a fresh workspace reaches Operational without seeing a field its capabilities don't need; disabling billing removes all money fields; editing the catalog never mutates in-flight assignments.

---

### E3 · People & identity (L1 → self-onboard)

**Base case** — 1. Admin bulk-invites / connects a directory (SSO-ready). 2. AI pre-fills each profile from portable identity/history. 3. Person **ratifies** + declares skills. 4. Auto-approve by policy → active, else admin approves.

**Business rules** — people self-onboard; admin handles exceptions only. Payroll fields only if on WS payroll; `skills` only if a performer; `cost/pay` (encrypted) only if paid through WS; `bank` JIT at first payout. Cost/pay/PII MUST be field-encrypted; salary never in plaintext.

**Two-layer identity (one person, many workspaces).** One human = **one global root identity** (their login, personal workspace, portable reputation — lives *above* all workspaces) + **one workspace-scoped membership per workspace** they join (that workspace's role, skills, contract, cost, access). A workspace sees only its own membership; **it cannot learn the person is in another workspace** (the root→membership link is resolved at the identity layer, never in a tenant's graph). Auth once at the root; act per membership; revoke SSO/offboard ends *that* membership only. *(Portable identity is Phase 2 — modeled now so it needs no rewrite; in Phase 1 a person is in one workspace.)*

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| **One person in 2 workspaces** | One root identity + two isolated memberships; WS-A can't see the WS-B membership; leaving A doesn't touch B. Only portable reputation (metadata-only, governed) crosses. |
| Skill needs verification | Active for non-gated work; gated skills pending approval. |
| Same person, two entities | One Entity; entity-scoped relationships; no duplicate identity. |
| Contractor vs payroll | Payroll-only fields asked only for payroll contracts. |
| Offboarded mid-assignment | In-flight activities flagged for reassignment (→ E13); no silent drop. |
| SSO deprovisioned upstream | Access revoked on next auth; history retained (append-only). |

<details>
<summary>▸ Data (JSON): RootIdentity (global) + Person-membership (per workspace)</summary>

```jsonc
// ROOT IDENTITY — one per human, GLOBAL, above all workspaces. No workspace_id.
{
  "root_identity": {
    "id": "root_uuid",
    "owner_auth_ref": "<the human's own credential>",
    "personal_workspace_ref": "pws_uuid",     // invisible to any org (SEC-12)
    "portable_reputation": { "rating": 4.6, "jobs": 120 }  // metadata-only, crosses orgs
  }
}

// PERSON = a MEMBERSHIP, one per workspace, scoped. Same human → many of these.
{
  "id": "person_uuid",
  "workspace_id": "ws_uuid",            // this membership's workspace
  "entity_id": "ent_uuid",
  "root_identity_id": "root_uuid",      // links to the global identity (identity layer only)
  "name": "Sara Khan",                  // always
  "email": "sara@acme.com",             // always
  "entity_role": "performer",            // owner|performer|reviewer|verifier|admin
  "contract_type": "payroll",           // only if on WS payroll
  "operating_entity_id": "oe_uuid",    // only if on payroll
  "sso_federated": true,                // employee SSO; revoke → THIS membership ends
  "skills": [ { "skill_id": "skill_translate_ar_en", "proficiency": 4 } ],  // if performer
  "cost_encrypted": "<fernet>",         // only if paid through WS — never plaintext
  "bank_ref": null,                     // JIT at first payout
  "status": "active"                    // invited | active | offboarded
}
```
</details>

**FRs** — FR-3.1 self-onboard, admin-exceptions-only · FR-3.2 AI pre-fill · FR-3.3 skill-gated approval · FR-3.4 one Entity, many entity relationships · FR-3.5 encrypted cost/pay/PII · FR-3.6 offboarding reassigns in-flight work · FR-3.7 **two-layer identity: one global root identity + per-workspace memberships; workspaces can't see each other's membership; auth once, act per membership, revoke per membership** (Phase 2).
**AC** — a person self-onboards active without admin touch when policy allows; salary never returns in plaintext; offboarding never orphans live activities.

---

### E4 · Relationships — clients & vendors (L1)

**Base case (client)** — add a client with **company name · code · one requester (name+email)**; pricing/invoice-code/wallet asked **only if billing through WS**, JIT at first request.
**Base case (vendor / cross-org)** — add a vendor with **identity only** (`vendor_type` + contact, or a **WS-tenant link**); `dispatchable_scope` defaults *any* (JIT-narrowed); cost/rate at first dispatch; boundary review mandatory; transparency opaque (defaults).

**Business rules** — tenant/client/vendor are **types on one model**, not separate flows. A vendor may be external *or* another workspace (→ E14). Vendor onboarding MUST work before offering/skills are known.

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Client wants no money in/out via WS | No pricing/wallet/invoice fields; delivery still works. |
| Vendor offering unknown | Onboard identity-only; scope/cost at first dispatch. |
| Vendor is another workspace | Establish the cross-org edge (E14); B must accept first. |
| Requester email later maps elsewhere | Route by mapped relationship; ambiguous senders flagged (→ E5). |

<details>
<summary>▸ Data (JSON): Relationship (client) & Relationship (vendor)</summary>

```jsonc
// CLIENT
{
  "id": "rel_uuid", "workspace_id": "ws_uuid", "operating_entity_id": "oe_uuid",
  "type": "client",
  "from_entity": "ent_acme", "to_entity": "ent_client",
  "config": {
    "company_name": "Globex", "code": "GLBX",
    "requesters": [{ "name": "Ravi", "email": "ravi@globex.com" }],
    // gated — only if billing through WS, JIT at first request:
    "pricing": null, "invoice_code": null, "wallet_id": null
  },
  "status": "active"
}

// VENDOR (identity-only first; the rest JIT)
{
  "id": "rel_uuid2", "workspace_id": "ws_uuid", "operating_entity_id": "oe_uuid",
  "type": "vendor",
  "vendor_type": "external",           // external | ws_tenant
  "linked_org_ref": null,              // set if vendor_type = ws_tenant
  "config": {
    "name": "FreelanceCo", "contact": "ops@freelanceco.com",
    "dispatchable_scope": "any",       // default; JIT-narrowed
    "cost_terms": null,                // at first dispatch
    "boundary_review": "mandatory",    // default
    "transparency": "opaque"           // default
  },
  "status": "active"
}
```
</details>

**FRs** — FR-4.1 one typed relationship model · FR-4.2 client billing gated + JIT · FR-4.3 vendor identity-only onboarding · FR-4.4 vendor defaults (opaque, mandatory review) · FR-4.5 vendor-as-workspace → cross-org edge.
**AC** — a billing-off client is created with 3 inputs and can receive delivery; a vendor onboards before its skills are known.

---

### E5 · Request intake

**Base case** — a requester submits **brief + files + deadline** via any channel (form, email, client tool, manual); the product creates a **Request** with a `source_channel`, mapped to the client relationship + entity.

**Business rules** — channels: manual · Phrase adapter (1 Project = 1 Job = 1 Request) · email auto-create (1 thread ↔ 1 request) · ambient AI brief. All converge on one Request.

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Duplicate email thread / re-send | Deduped to the existing Request; appended, not duplicated. |
| Brief with no files | Created; composer raises clarifying questions if files are needed to scope. |
| Deadline past/missing | Flagged at intake; owner confirms/repairs before compose. |
| Requester not mapped to a client | Held in an "unmapped intake" queue; admin maps or rejects. |
| File unreadable/too large | Pointer accepted; composer flags it and requests re-upload. |
| Ambiguous sender (2 clients) | Disambiguation queue, not a silent assignment. |

<details>
<summary>▸ Data (JSON): Request</summary>

```jsonc
{
  "id": "req_uuid",
  "workspace_id": "ws_uuid", "operating_entity_id": "oe_uuid",   // system
  "requester_id": "ent_client",                                 // system (mapped)
  "engagement_id": "eng_uuid",                                    // system
  "brief": "Translate the attached 40-page report to Arabic",     // requester
  "input_files": ["file_ref_1", "file_ref_2"],                    // requester (pointers)
  "deadline": "2026-07-20",                                       // requester
  "source_channel": "email",                                      // system: manual|email|phrase|api
  "state": "created",                                             // created→live→delivered→verified→billed
  "status": "not_started"                                         // derived in-engine
}
```
</details>

**FRs** — FR-5.1 multi-channel intake → one Request model · FR-5.2 email/tool dedupe · FR-5.3 unmapped/ambiguous queued, never dropped · FR-5.4 past/missing deadline flagged before compose.
**AC** — the same request twice creates one Request; an unmapped sender never auto-attaches to the wrong client.

---

### E6 · AI plan composition

**Base case** — the composer (in the zero-retention enclave) reads brief + files **and this workspace's own config**, then produces a **proposal**: offering + level · unit type/count · a **tree of activities** (skills, order, dependencies, Deliver last) · a proposed performer per activity · deadline · price (if billing on) · scope sheet · confidence · clarifying questions.

**Business rules** — composes **only from the tenant's own config** (never invents structure); **stateless, per-tenant, zero-retention** (brief/file content never persisted, never crosses tenants); output is a **proposal only** — nothing is real until the owner ratifies.

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Vague/ambiguous brief | Low-confidence proposal + **clarifying questions**; never a silent guess. |
| Thin catalog (new tenant) | A thin plan; archetypes mitigate; honest "as good as the config." |
| No matching offering | Flags "no offering matches"; owner maps or extends the catalog. |
| Mis-mapped offering/level | Owner edits inline (E7); the composer learns **within the tenant only**. |
| File unreadable | Flagged; scoping falls back to owner input / re-upload. |
| Cross-org request | Each side composes within its **own** workspace; never across the boundary. |

<details>
<summary>▸ Data (JSON): Proposal</summary>

```jsonc
{
  "id": "prop_uuid", "request_id": "req_uuid",
  "proposed_offering_id": "off_translate", "proposed_level": "standard",
  "scope_sheet": { "unit_type": "page", "unit_count": 40, "assumptions": ["source is clean PDF"] },
  "proposed_activities": [
    { "seq": 1, "skill_id": "skill_ocr",        "performer_type": "agent",       "proposed_performer_id": "agent_ocr", "input_split": "pp.1-40", "dependency": null },
    { "seq": 2, "skill_id": "skill_translate",  "performer_type": "human",       "proposed_performer_id": "person_sara", "dependency": 1 },
    { "seq": 3, "skill_id": "skill_review",     "performer_type": "human",       "proposed_performer_id": "person_omar", "dependency": 2 },
    { "seq": 4, "skill_id": "skill_deliver",    "performer_type": "human+tool",  "proposed_performer_id": "person_omar", "dependency": 3 }
  ],
  "proposed_deadline": "2026-07-19",
  "proposed_price": { "amount": 800, "currency": "USD" },   // gated: only if billing on
  "confidence": { "offering": 0.95, "scope": 0.8, "performers": 0.9 },
  "clarifying_questions": [],                                // populated when a gap blocks composing
  "provenance": ["off_translate@v3", "rate_list@v2"]
}
```
</details>

**FRs** — FR-6.1 compose from tenant config only · FR-6.2 stateless, per-tenant, zero-retention · FR-6.3 suggest-not-act · FR-6.4 confidence + clarifying questions on low certainty · FR-6.5 provenance recorded · FR-6.6 federated by the boundary.
**AC** — the composer never persists brief/file bytes; a vague brief yields questions, not a fabricated plan; no proposal becomes an assignment without ratification.

---

### E7 · Plan ratification (human touchpoint #1)

**Base case** — owner opens the proposal → **approves in one click** → the Assignment + Activity tree are written in one transaction; the request goes LIVE; activities fan out in parallel.

**Business rules** — approval is one action, not a wizard. Editing is inline; an edit re-plans only the affected part.

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Owner tweaks the plan | Inline edit; product re-derives dependent scoping/pricing; re-presents. |
| Owner rejects | Re-briefs/re-scopes → composer re-runs. |
| Owner unavailable past SLA | Escalates per policy (delegate/next owner); no silent stall. |
| Repeated reject loop | After N cycles, escalate to ops with reasons `[J: N]`. |
| Pricing/wallet check fails at publish | Auto-flag the owner to fix/fund before activities mobilize. |

<details>
<summary>▸ Data (JSON): Assignment</summary>

```jsonc
{
  "id": "asg_uuid", "request_id": "req_uuid",
  "offering_id": "off_translate", "level": "standard",   // AI → ratify
  "unit_type": "page", "unit_count": 40,                  // AI
  "delivery_model": "deliverable", "billing_model": "unit_x_price",  // config
  "owner_id": "person_owner",                             // system
  "price": { "amount": 800, "currency": "USD" },          // AI, gated (billing on), JIT
  "invoice_code": "TRANS-STD", "payment_type": "prepaid", // config, gated
  "deadline": "2026-07-19",                               // AI → override
  "state": "published",                                   // created→published→delivered→verified
  "status": "on_track"                                    // derived in-engine
}
```
</details>

**FRs** — FR-7.1 one-click approve · FR-7.2 inline edit re-plans only the delta · FR-7.3 reject → re-compose · FR-7.4 owner-unavailable escalation · FR-7.5 publish gated on pricing/wallet check when billing on.
**AC** — approving publishes the whole tree atomically; an edit never forces a full re-author; an absent owner never freezes a request.

---

### E8 · Allocation & mobilization

**Base case** — per activity: **Pass 1** hard filters (skill+proficiency, availability, no conflict, tier-eligible) → **Pass 2** weighted score (`fit · quality_to_cost · committed_capacity_first · deadline_confidence · responsiveness`) → propose top-1 (named) + alternates with reasons (at plan-ratify) → mobilize via **WS-chat + push** (default); performer **one-tap accepts**.

**Business rules** — **committed-capacity-first**: saturate fixed-cost resources (salaried-to-quota, retainer teams, owned licenses; ~$0 marginal) before variable freelancers. **No bidding** — propose → ratify → accept only. Channels: WS-chat default (free); WhatsApp/SMS user-selectable paid fallbacks behind one adapter; pay for costly channels only when the free one fails.

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Empty bench (no candidate passes) | Fallback ladder: source externally / escalate to ops — per policy `[J]`. |
| Proposed performer declines | Auto-propose next-best; escalate by timezone/responsiveness. |
| Candidates exhausted | External sourcing / curated open / escalate `[J]`. |
| No response in window | Escalate channel: WS-chat → WhatsApp → SMS/call. |
| Accepts then goes silent | SLA monitor auto-escalates + surfaces a risk signal `[J]`. |
| Conflict of interest | Hard-filtered in Pass 1. |
| Committed capacity saturated | Spill to next tier / variable per the objective. |
| Score tie | Deterministic tie-break (responsiveness → cost); no random assignment. |

<details>
<summary>▸ Data (JSON): Allocation & Mobilization (per activity)</summary>

```jsonc
{
  "allocation": {
    "activity_id": "act_uuid",
    "candidates_scored": [
      { "performer_id": "person_sara", "score": 0.91, "reasons": ["fit","committed_capacity"] },
      { "performer_id": "person_lee",  "score": 0.78, "reasons": ["fit"] }
    ],
    "proposed_performer_id": "person_sara",
    "alternates": ["person_lee"]
  },
  "access": {                                    // set by the performer's one tap
    "subject_id": "person_sara", "role_type": "activity",
    "role_status": "pending",                    // pending → accepted | rejected
    "reject_reason": null
  },
  "mobilization": {                              // system
    "channel": "ws_chat",                        // ws_chat | whatsapp | sms
    "sent_at": "2026-07-08T10:00:00Z",
    "response": null, "escalation_step": 0
  }
}
```
</details>

**FRs** — FR-8.1 two-pass allocation · FR-8.2 committed-capacity-first · FR-8.3 propose→ratify→accept, no bidding · FR-8.4 fallback ladder on decline/exhaust · FR-8.5 channel-native, escalating, cost-aware · FR-8.6 SLA monitor auto-escalates · FR-8.7 objective weights are tenant config.
**AC** — an empty bench never leaves an activity silently unassigned; a costly channel is used only after the free one fails; an entity can't sit on both sides of an activity.

---

### E9 · Execution — perform + QA

**Base case** — the performer type (set in the plan) runs: **human** works, progress auto-logged; **AI agent** runs a first pass; **human+tool** gets a JIT-brokered tool license. QA policy per activity: **auto-QA** (agent-safe) or **human reviewer Pass/Fail**. On pass → the activity is terminal.

**Business rules** — one allocation engine for all performer types; an agent is allocated like a performer (~$0 marginal) but doesn't "accept" — it runs; first-pass → human QA. The **license broker** assigns a pooled tool license JIT to the activity-session (a license = a committed resource).

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Agent first-pass fails | Fall back to a human performer automatically. |
| Interim/draft output | Auto-share the draft to the requester (border-safe); work continues. |
| Tool license unavailable | Broker queues for the next free license / escalates; activity waits, doesn't fail. |
| QA fails | Rework loop back to the performer. |
| Repeated rework | After N rounds, escalate to owner/ops `[J: N]` — no infinite loop. |
| Partial output | Activity stays non-terminal; dependents keep waiting on their input. |
| SLA breached mid-work | Auto-escalate + surface risk to the requester `[J]`. |

<details>
<summary>▸ Data (JSON): Activity</summary>

```jsonc
{
  "id": "act_uuid", "assignment_id": "asg_uuid",
  "skill_id": "skill_translate",           // AI
  "performer_type": "human",               // AI: human | agent | human+tool
  "performer_id": "person_sara",           // AI → accept
  "input_files": ["file_ref_ocr_out"],     // AI
  "dependency_activity_id": "act_ocr",     // AI (output→input gate)
  "unit_count": 40, "start_by": "2026-07-09", "deliver_by": "2026-07-17",  // AI
  "sort_order": 2,                         // system; Deliver = last
  "qa_policy": "human",                    // config: auto | human
  "outputs": [],                           // performer
  "progress": 0.0,                         // performer/tool, auto
  "state": "published",                    // created→published→delivered
  "status": "not_started"                  // derived in-engine
}
```
</details>

**FRs** — FR-9.1 progress auto-logged · FR-9.2 agent-as-performer with human-QA fallback · FR-9.3 JIT license broker · FR-9.4 QA policy per activity · FR-9.5 rework loop with an escalation cap · FR-9.6 interim drafts auto-shared border-safe.
**AC** — a failed agent pass never blocks delivery; QA rework can't loop forever; an unavailable license waits rather than dropping the activity.

---

### E10 · Delivery & verify (human touchpoint #2)

**Base case** — 1. When all sibling activities + child assignments are terminal, the deliverable is **assembled**. 2. Owner gives **boundary sign-off** (mandatory review). 3. Deliver to the requester's store; the requester has had a status roll-up throughout. 4. AI **pre-computes reconciliation** (splits · fees · counts · exceptions). 5. Verifier **one-tap confirms** — the billing gate.

**Business rules** — Deliver is the mandatory last activity. Verify is a ~10-second confirm, not manual reconciliation. Deliverables are **written to the recipient's store** (their property); the graph keeps the pointer + attribution.

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Dependencies not yet terminal | Hold; other branches keep running; assemble only when all are terminal. |
| Boundary sign-off rejected | Route back to rework; nothing crosses the boundary. |
| Requester approval required & they reject | Rework loop back to the performer. |
| Recipient store unavailable | Retry with backoff; owner flagged; not marked delivered until written. |
| Reconciliation mismatch at verify | Verifier sees the exception; can send back to fix before confirming. |
| Verifier unavailable | Escalate per policy; the gate never silently auto-passes. |

<details>
<summary>▸ Data (JSON): Delivery & Verify</summary>

```jsonc
{
  "delivery": {
    "deliverable_ref": "file_ref_final",     // system (assembled)
    "boundary_signoff": { "by": "person_owner", "at": "2026-07-17T09:00:00Z" },  // owner
    "delivered_to_store": "s3://client-globex/inbox/..."                         // system
  },
  "verify": {
    "reconciliation": {                       // AI pre-computed
      "unit_count": 40, "splits": [{ "performer": "person_sara", "units": 40 }],
      "fees": [], "exceptions": []
    },
    "verified_by": "person_verifier",         // the gate
    "confirm": true, "notes": null
  }
}
```
</details>

**FRs** — FR-10.1 Deliver is the mandatory terminal activity · FR-10.2 assemble only when the whole tree is terminal · FR-10.3 deliverable written to recipient's store + attribution · FR-10.4 AI-precomputed reconciliation → one-tap verify · FR-10.5 verify is the sole billing gate · FR-10.6 auto-delivery shortcut where policy allows.
**AC** — nothing bills without a verify confirm; a deliverable is never marked delivered until written to the recipient's store; a reconciliation mismatch is visible before money moves.

---

### E11 · Money — invoicing, wallet, payout & files

**Base case** — on verify, the product emits **one billable event** → fans out to two **independent, capability-gated** sides: **invoicing** (money in) and **payout** (money out). Rolling — the moment verify clears.

**Business rules** — a performer is paid off **verified work**, independent of whether the client has paid. Invoicing destination is **pluggable**: WS module / external connector / data-out. Wallet ledger is **append-only and the source of truth** (no spreadsheet mirror). Grouping/tax/coins/quota are config. Files: the graph holds `file_ref` **pointers**; bytes are processed in a zero-retention **enclave**; brokered access via JIT scoped credentials.

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Billing off | No money-in side; payout still runs if paying through WS; no invoice. |
| Prepaid wallet insufficient at create | Publish blocked (FR-7.5); owner asked to fund. |
| Cancel after wallet deduct | Refund the lot on cancel (ledger entry). |
| External connector down | Billable event durable; push retried; nothing lost. |
| Currency/tax mismatch | Resolved from the entity's `tax_profile`/currency; mismatch flagged, not guessed. |
| Client disputes an invoice | Dispute path (E13 F5); verified-work payout not clawed back. |
| Agent/tool "payout" | ~$0 marginal; payout is for human/committed resources per config. |

<details>
<summary>▸ Data (JSON): BillableEvent, Invoice, Wallet, Payout, FileRef</summary>

```jsonc
// Emitted once, at verify — immutable
{
  "billable_event": {
    "id": "be_uuid", "assignment_ref": "asg_uuid",
    "verified_by": "person_verifier", "verified_at": "2026-07-17T10:00:00Z",
    "unit_count": 40, "unit_price": 20, "amount": 800, "currency": "USD",
    "billing_model": "unit_x_price",
    "operating_entity_id": "oe_uuid", "client_relationship_id": "rel_uuid"
  }
}

// Invoicing — gated ("bill through WS?"); one of:
{ "invoice": {                                  // WS module
    "invoice_number": "ACME-2026-07-001",
    "grouping_rule": "per_entity_per_period",    // config (EZ: 1/entity/month)
    "rate_snapshot": { "page": 20 },
    "line_items": [{ "billable_event_id": "be_uuid", "amount": 800 }],
    "tax": { "profile": "IN-GST", "amount": 144 }, "status": "raised" } }
{ "pushed_to_external": { "system": "netsuite", "external_ref": "INV-9",
    "status": "sent" } }                         // external connector — no WS invoice

// Wallet — gated (prepaid); ledger is the source of truth (append-only)
{ "wallet": { "id": "wal_uuid", "balance": 1200, "cost_per_credit": 1 },
  "wallet_lots": [{ "id": "lot_1", "credits": 2000, "remaining": 1200, "validity": "2026-12-31" }],
  "wallet_ledger": [
    { "op": "deduct",  "delta": -800, "ref": "asg_uuid", "at": "2026-07-08T..." },
    { "op": "settle",  "delta": 0,    "ref": "be_uuid",  "at": "2026-07-17T..." }
  ] }

// Payout — gated ("pay through WS?"); off verified work
{ "payout": { "performer_id": "person_sara", "period": "2026-07",
    "amount": 400, "unit": "coins", "source": ["be_uuid"], "status": "accrued" } }

// Files are pointers, never bytes
{ "file_ref": { "id": "file_ref_1", "store_location": "s3://acme/in/report.pdf",
    "key": "report.pdf", "checksum": "sha256:...", "size": 82113, "mime": "application/pdf",
    "owner_entity_id": "oe_uuid" },
  "access_grant": { "grantee": "ws_b_identity", "scope": ["read:file_ref_1"],
    "expiry": "2026-07-20T00:00:00Z", "revocable": true } }
```
</details>

**FRs** — FR-11.1 one billable event on verify · FR-11.2 invoicing & payout decoupled; payout off verified work · FR-11.3 pluggable invoicing destination · FR-11.4 wallet deduct-at-create → settle-at-verify → refund-on-cancel · FR-11.5 append-only ledger as source of truth · FR-11.6 grouping/tax/coins/quota all config · FR-11.7 typed-decimal, tested money math · FR-11.8 files are pointers; bytes in the zero-retention enclave; brokered JIT credentials.
**AC** — turning billing off removes all invoicing; a performer is paid on verify regardless of client payment; the ledger reconciles to itself with no external mirror; a cancel always refunds correctly.

---

### E12 · Ongoing work — retainer & outcome (Type B)

**Base case** — an Engagement with `delivery_model = retainer | outcome` runs over **service periods**. Retainer: "complete" = a period closes + verified → bill per period. Outcome (BOT): "complete" = period closes + the outcome metric measured → bill per period from the metric.

**Business rules** — same lifecycle engine; the difference is *what "complete" means* and *how it rolls to a billable event* — both config, not new code.

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Mid-period scope change | Applied to current/next period per policy; pricing recomputed (E13 F1). |
| Outcome metric not measurable at close | Period held pending the metric; billing waits `[J: formula]`. |
| Retainer + usage overage | Base bills flat; overage bills as usage on top. |
| Period rollover | Next period auto-opens (recurring); no manual re-creation. |
| Engagement paused | Periods suspend; no billing while paused; resume cleanly. |

<details>
<summary>▸ Data (JSON): Engagement & ServicePeriod</summary>

```jsonc
{
  "engagement": {
    "id": "eng_uuid", "client_relationship_id": "rel_uuid",
    "delivery_model": "retainer", "billing_model": "retainer_plus_usage"
  },
  "service_period": {
    "id": "sp_uuid", "engagement_id": "eng_uuid",
    "period": "2026-07", "status": "open",     // open → closed → verified → billed
    "outcome_metric": null                      // set for delivery_model = outcome
  }
}
```
</details>

**FRs** — FR-12.1 one engine, delivery_model decides "complete" · FR-12.2 service-period state machine · FR-12.3 per-period billable events · FR-12.4 outcome billing from a measured metric `[J]` · FR-12.5 auto period rollover.
**AC** — a retainer bills once per closed+verified period; an outcome engagement doesn't bill until its metric is measured; scope changes don't corrupt prior periods.

---

### E13 · Change & exceptions

**Base cases & rules**
- **F1 Scope change mid-flight** — edit-levels; pricing/scope recomputed; only the **delta** re-plans; terminal outputs preserved.
- **F2 Reassignment** — expert unavailable → reassign; **fee-split** applies; **the workspace never funds the overrun** (an EZ rule expressed as config).
- **F3 Cancel / pause** — cancel refunds the wallet lot; pause suspends without billing.
- **F4 Goodwill revision post-completion** — a **new linked assignment, no claw-back** of the original.
- **F5 Disputes** — a dispute path on invoices/deliverables; verified-work payouts aren't clawed back.
- **F6 Recurrence** — recurring requests re-open on cycle.

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| Scope change after some activities terminal | Only non-terminal parts re-plan; terminal outputs preserved. |
| Reassignment cost > original | Fee-split per policy; overrun not funded by the workspace. |
| Cancel after partial delivery | Refund per policy; delivered parts retained; ledger consistent. |
| Goodwill fix weeks later | New linked assignment; original billing untouched. |
| Dispute during payout | Verified-work payout stands; dispute handled on the invoice side. |

**FRs** — FR-13.1 scope change re-plans the delta only · FR-13.2 reassignment fee-split, workspace never funds overrun · FR-13.3 cancel refunds, pause suspends billing · FR-13.4 goodwill = new linked assignment, no claw-back · FR-13.5 dispute decoupled from verified-work payout · FR-13.6 recurrence auto-reopen.
**AC** — a mid-flight scope change never discards completed work; a goodwill fix never reverses the original invoice; a cancel always leaves the ledger balanced.

---

### E14 · Cross-org / boundary (Phase 2)

**Base case** — 1. WS-A onboards a vendor with `vendor_type = ws_tenant` → the handshake creates one Relationship edge; B accepts (sees an incoming **client**). 2. A dispatches a request → in A's graph the vendor is **one opaque boundary node**; in B's graph it's a **new Request** with A as client. 3. B runs its own lifecycle invisibly; returns a border-safe status roll-up + deliverable.

**Business rules** — A never sees B's tree/performers/method/sub-vendors/costs; B never sees A's other vendors/entities. **Brokered files:** inputs stay in A's store (B gets a JIT scoped credential); deliverable written into A's store; provenance stripped per hop. Transparency dial (config): default opaque; the vendor controls its own ceiling.

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| B declines at the boundary | A treats it as a decline → fallback ladder (E8). |
| Chain A→B→C | Each hop re-encapsulates; **A never learns C exists**; provenance stripped per hop. |
| B raises transparency for A | Only up to B's own ceiling; A sees more milestones, not internals. |
| Brokered credential expires mid-work | B re-requests a scoped credential; no standing access. |
| Deliverable write-back to A fails | Retry; not marked delivered until written; attribution logged. |
| Non-WS vendor (email/Phrase/API) | Client-system adapter — functional but bounded by that tool's surface. |

<details>
<summary>▸ Data (JSON): cross-org edge & BoundaryNode</summary>

```jsonc
{
  "relationship": {                              // ONE edge, two views
    "id": "rel_xorg", "linked_org_ref": "ws_b",
    "workspace_A": { "id": "ws_a", "role": "vendor", "operating_entity_id": "oe_a2" },
    "workspace_B": { "id": "ws_b", "role": "client" },
    "A_cfg": { "dispatchable_scope": "translation", "cost_terms": "…", "transparency_granted": "milestones" },
    "B_cfg": { "pricing_to_A": "…", "sla": "…", "transparency_ceiling": "milestones" },
    "boundary_review_policy": "mandatory", "connection_type": "ws_native", "status": "active"
  },
  "boundary_node": {                             // how B appears inside A's graph
    "id": "bn_uuid", "activity_id": "act_in_A",
    "maps_to_request_ref": "req_in_B",           // opaque to A
    "visible_status": "in_progress", "deliverable_ref": null, "opacity_level": "opaque"
  }
}
```
</details>

**FRs** — FR-14.1 one edge, two views · FR-14.2 full encapsulation both directions · FR-14.3 brokered files, JIT scoped credentials, deliverable to recipient's store · FR-14.4 transparency dial, vendor-controlled ceiling · FR-14.5 mandatory boundary sign-off + provenance stripping · FR-14.6 chains re-encapsulate per hop.
**AC** — A can never enumerate B's performers or sub-vendors; a chained C is invisible to A; a brokered credential is always scoped, expiring, revocable.

---

### E15 · Multi-entity isolation

**Base case** — an org has multiple operating entities in one workspace; every relationship/work/wallet record carries `operating_entity_id`; access is scoped by `(workspace_id, operating_entity_id)`; **default: sibling entities don't see each other's** relationships or work.

**Business rules** — default isolated (Entity-1 doesn't learn Entity-2 is a vendor to Org B's Entity-3). The org admin sees across entities **unless** an entity-delegated module-admin blinds even the admin. **Entity-vs-workspace is the client's choice** — entities-in-one-WS (policy isolation) vs a workspace-per-entity (crypto isolation); both interoperable and migratable.

**Edge cases**
| Scenario | Expected behaviour |
|---|---|
| User queries a sibling entity's work | Denied by RLS scoping; not visible. |
| Org admin should be blinded from an entity | Entity-delegated module-admin scope blinds even the org admin. |
| External Org B looks in | Sees only the entity it works with — never the org's other entities. |
| Client wants an entity fully walled off | Provision it as its own workspace (crypto isolation, own keys/tier). |
| Migrate an entity to its own workspace later | Supported as a **data-separation operation** (re-key + move) — heavier than a config toggle; flagged honestly. |
| `entity_isolation` flipped to shared | The org opts into cross-entity visibility deliberately. |

<details>
<summary>▸ Data (JSON): entity scoping</summary>

```jsonc
{
  "operating_entity": {
    "id": "oe_uuid", "workspace_id": "ws_uuid",
    "legal_name": "Acme Lab", "code": "LAB", "country": "IN",
    "billing_currency": "INR", "tax_profile": "IN-GST", "invoice_prefix": "LAB",
    "entity_isolation": true,                 // default isolated
    "module_admin_scope": "entity"            // can blind even the org admin
  }
}
```
</details>

**FRs** — FR-15.1 entity-level default isolation via scoping · FR-15.2 entity-delegated admin can blind the org admin · FR-15.3 external orgs see only their counterpart entity · FR-15.4 entity-vs-workspace is the client's choice, interoperable + migratable · FR-15.5 separated entities still link back via the cross-org boundary.
**AC** — a sibling entity can't read another's relationships; an external org can't enumerate the org's other entities; an entity can be split to its own keyed workspace later.

---

## 6. Config surface (the declarative knobs)

Everything the workspace admin configures — **declarative, defaulted, versioned; nothing hardcoded.** The readiness engine (E2) computes which of these are required from the turned-on capabilities.

<details>
<summary>▸ Data (JSON): Offering · Skill · Rate · Team/Role · AllocationPolicy · Archetype</summary>

```jsonc
// OFFERING (delivery × billing axes; levels)
{
  "id": "off_translate", "version": 3, "name": "Document Translation",
  "delivery_model": "deliverable", "billing_model": "unit_x_price",
  "levels": ["economy","standard","premium"],
  "activity_templates": [                       // the tree the composer instantiates
    { "seq": 1, "skill_id": "skill_ocr",       "qa_policy": "auto",  "dependency": null },
    { "seq": 2, "skill_id": "skill_translate", "qa_policy": "human", "dependency": 1 },
    { "seq": 3, "skill_id": "skill_review",    "qa_policy": "human", "dependency": 2 },
    { "seq": 4, "skill_id": "skill_deliver",   "qa_policy": "auto",  "dependency": 3 }  // mandatory last
  ]
}

// SKILL + RATE
{ "skill": { "id": "skill_translate", "name": "Translate AR→EN",
    "proficiency_scale": [1,2,3,4,5] } }
{ "rate": { "id": "rate_uuid", "skill_id": "skill_translate", "unit_type": "page",
    "rate": 20, "currency": "USD", "relationship_id": null } }   // per-client override if set

// TEAM / ROLE  (EZ: SWAT/QA/SME/pool are just names here)
{ "team": { "id": "team_delivery", "name": "Delivery", "roles": ["owner","performer","reviewer","verifier"] } }

// ALLOCATION POLICY (weights, fallback, channels)
{
  "objective_weights": { "fit": 0.35, "quality_to_cost": 0.2,
    "committed_capacity_first": 0.25, "deadline_confidence": 0.1, "responsiveness": 0.1 },  // [J] real values
  "hard_filters": ["skill_proficiency","availability","no_conflict","tier_eligible"],
  "fallback_policy": { "on_exhaust": "escalate" },     // external | escalate  [J]
  "escalation_window": "PT2H",
  "channel_policy": { "default": "ws_chat", "optional": ["whatsapp","sms"] }
}

// ARCHETYPE (a generic starter kit — never EZ templates)
{ "archetype": { "id": "arch_translation", "seeds": ["offerings","skills","roles","sla_bands","pricing_bands"] } }
```
</details>

**Config rules** — FR-6cfg.1 every knob declarative + defaulted · FR-6cfg.2 catalog/offerings versioned; in-flight work uses its snapshot · FR-6cfg.3 rates support per-client overrides · FR-6cfg.4 role/skill/offering **names** are config, behaviour is not · FR-6cfg.5 the readiness engine derives required config from turned-on capabilities.

---

## 7. Cross-cutting requirements

- **CC-1 Ambient AI** — inline (suggest→approve), never a chatbot panel; every AI output is an editable proposal.
- **CC-2 Channel-native notifications** — WS-chat default; WhatsApp/SMS/email selectable; one adapter; escalation cost-aware.
- **CC-3 Reliable reporting** — one lifecycle engine; status derived in the write transaction; **no drift, no repair crons**. Reporting reads state, never computes it.
- **CC-4 Server-authoritative access** — RBAC + POV-scoping enforced server-side and config-driven (replaces frontend-JSON perms + email allowlists).
- **CC-5 Audit** — append-only, tenant-inspectable; every state change and money event logged.
- **CC-6 Files** — the graph holds pointers; bytes processed in a zero-retention enclave; access flows to the tool, never a person.
- **CC-7 No shadow data** — no spreadsheet-as-database, no ERP↔WS sync anywhere.

---

## 8. Data security, privacy & trust  (SEC-x)

**The trust model, straight from the vision (§2.1, §2.2, §8).** The whole platform's defensibility rests on this: *the operator can't read a tenant's data — cryptographically, not by promise.* These are hard product requirements, not aspirations. `[V§n]` cites the vision section. **The full information-security program** — data residency/storage, threat model, bot/DDoS defense, AI/prompt-injection controls, monitoring, IR, and the certification-readiness map — is in **[`security.md`](./security.md)**.

### 8.1 Data handling — control plane, tiers, sealed enclave

| # | Requirement |
|---|---|
| **SEC-1** | **Control plane only** — WS holds the metadata graph (who/what/when/which skill/status/access grants) and **file pointers**; it **never custodies file content**. `[V§2.1]` |
| **SEC-2** | **Tiered storage (tenant-configurable)** — WS-managed (convenience default) · connected cloud / SharePoint/Drive/S3 (regional/residency) · own infra, on-prem or cloud (sovereign). Sovereignty available to all, mandatory for none. *(EZ resells these as Standard/Compliant/Private — a mapping, not a product distinction.)* `[V§2.1,§8]` |
| **SEC-3** | **Sealed zero-retention enclave** — when a feature needs bytes (split, page/word count, AI reading a brief) WS pulls them into an ephemeral enclave, computes, returns the result, **retains nothing**. `[V§2.1]` |
| **SEC-4** | **Access flows to the tool, never a person** — no human at WS/operator/EZ ever sees tenant bytes; **no content in logs, no human debugging on raw data**; AI is stateless. `[V§2.1]` |
| **SEC-5** | **Two processing modes by tier** — **Option B** (WS-controlled regional enclave) for shared/regional tenants; **Option A** (in-environment runtime, **no egress**) is **required** for sovereign tenants (government/PIF/financial) who mandate "nothing leaves our environment." Phase 2+. `[V§2.1,§8]` |

### 8.2 Access, credentials & keys

| # | Requirement |
|---|---|
| **SEC-6** | **Two layers of need-to-know** — (1) what WS-the-tool may pull from a tenant *at all*; (2) what a given user may see *within* that. Both enforced server-side. `[V§2.1]` |
| **SEC-7** | **Scoped tenant-API credential = the crown jewel** — JIT, least-privilege, **short-lived per-grant tokens**, never a standing broad credential. A leaked token exposes **one file for minutes**. `[V§8]` |
| **SEC-8** | **Per-tenant keys; BYOK at Regional/Sovereign** — the operator is **cryptographically unable** to read a tenant's data or client list — *can't, not "promises not to."* A competing agency can adopt on the sovereign tier with its own keys. `[V§8]` |
| **SEC-9** | **Tenant-inspectable, tamper-evident audit** of operator/admin actions ("don't-trust-us-verify" applied to the operator) + the enclave's no-human-bytes governance. `[V§8]` |

### 8.3 Identity, offboarding & the personal/corporate wall

| # | Requirement |
|---|---|
| **SEC-10** | **Portable root identity + SSO federation** — org access via SSO; **revoke SSO → live access ends**. Freelancers authenticate against their **own** identity, never forced into one org's SSO. Phase 2. `[V§2.2]` |
| **SEC-11** | **Offboarding = metadata-only snapshot** — WS projects an org-permitted **shadow log** (project names, volumes, roles, feedback — **no files, no confidential content**) into the person's personal workspace; the org superadmin governs how much. `[V§2.2]` |
| **SEC-12** | **Personal/corporate separation by construction** — a person's personal workspace is **invisible to any org**; WS guarantees it, doesn't merely promise it. `[V§2.2]` |

### 8.4 AI & data-use boundaries

| # | Requirement |
|---|---|
| **SEC-13** | **No cross-tenant training** — the composer/allocator run **per-tenant, stateless, zero-retention**; cross-tenant training is **prohibited**. Any future training is consent-tiered and sovereignty-sensitive tenants are excluded **by design**. `[V§2.4,§6]` |
| **SEC-14** | **Confidentiality governs the metadata** — even when file bytes are sovereign, the graph WS holds (names, volumes, turnaround) is confidential-by-scoping, not open. `[V§10]` |

### 8.5 Trust tiers (what a tenant/client actually buys)

| | Shared | Regional | Sovereign |
|---|---|---|---|
| **Storage** | WS multi-tenant | WS, region-pinned | Tenant infra, no egress |
| **Processing/AI** | WS enclave (Option B) | WS enclave, regional | In-environment runtime (Option A) |
| **Keys** | WS-managed | Customer-managed (BYOK) | Customer-managed (BYOK) |
| **Operator can read?** | Yes (custodial) | **No (cryptographic)** | **No (cryptographic)** |

**AC** — on a BYOK tier, an operator query for a tenant's briefs/deliverables/client list returns nothing decryptable; a leaked tenant-API token grants at most one file for minutes; no tenant bytes ever appear in a log or reach a human; a person's personal workspace is unreachable from any org.

---

## 9. Non-functional requirements

| # | Requirement |
|---|---|
| NFR-1 | **Isolation** — `workspace_id` crypto (BYOK for sovereign); `operating_entity_id` policy (RLS). Server-side. |
| NFR-2 | **Confidentiality** — raw content never system-of-record; zero-retention enclave; PII/salary field-encrypted. |
| NFR-3 | **Reliability** — state+status atomic; outbox for events; no dual-write drift. |
| NFR-4 | **Auditability** — append-only audit + money ledger; reconstructable history. |
| NFR-5 | **Scalability** — parallel activity branches; async workers for escalation/invoicing/payout; reporting off a read model. |
| NFR-6 | **Data residency** — regional/sovereign tiers pin data; enclave + file broker deploy per region. |
| NFR-7 | **Testability** — money & lifecycle rules covered by a parity-test catalog **before** the code implementing them. |
| NFR-8 | **Maintainability** — config-not-code; typed schema; no hand-run management-command surface. |

---

## 10. Phasing & scope

**Phase 1 (EZ as Tenant-Zero, intra-workspace):** E1–E13 + all cross-cutting + absorbed ERP money/HR domains. Multi-tenant-*ready* by design.
**Phase 2 (cross-org):** E14 turned on; E15 entity-isolation is **built in Phase 1** (the primitive) so Phase 2 needs no rewrite. Portable identity/SSO here.
**Parked:** commercial/pricing product, live-market moat.

---

## 11. Open items — awaiting Joy & Bhavya

**Joy `[J]`:** (1) allocation objective weights · (2) empty-bench fallback (external vs escalate) · (3) QA policy per activity · (4) SLA at-risk policy · (5) delivery-engine role definitions → owner/performer/reviewer/verifier · (6) BOT/outcome billing formula · (7) rework/reject escalation caps (the "N" values) · (+ delivery archetypes 02–06, statutory matrix).
**Bhavya (architecture.md §11):** core shape (modular-monolith vs microservices) · transactional vs event-sourced · GraphQL vs REST · isolation mechanism per tier · async infra · stack confirmation · **repository layout** (the ~2-repo recommendation — confirm the separate AI Composer / enclave repo).

**None of these change a workflow or a requirement** — they fill parameters at marked holes.

---

## 12. Glossary

**Entity** — an **actor**: an org or a person (replaces the old term "Party"); distinct from *operating entity* below. **Relationship** — a typed edge (employment/client/vendor/tenant). **Request / Assignment / Activity** — the work-graph tree (BAT). **Deliver** — the mandatory last activity. **Billable event** — the single money-in/out trigger emitted at verify. **Committed capacity** — fixed-cost resources (~$0 marginal). **Archetype** — a generic industry starter kit that seeds config. **Readiness engine** — computes "can deliver" and asks only for gaps. **Boundary node** — the opaque representation of a vendor workspace in the client's graph. **Enclave** — the zero-retention sandbox where content is processed. **Operating entity** — a legal/billing unit inside one org (policy-isolated). **Workspace** — a tenant (crypto-isolated).

---

## Appendix A — Worked example: one use case, row by row

**The scenario (answers "show how data entry is done"):** *Acme* (a translation agency) runs on WS. It onboards, adds a client *Globex*, receives a 40-page document to translate into Arabic, delivers it, invoices Globex, and pays the translator *Sara*. Below is **every row created**, in order. IDs are illustrative. This also traces the **expert (Sara)** end-to-end and shows **where `invoice_code`, `person_skill`, and the client user sit**.

**Step 1 — L0 provisions the workspace** (E1)
```jsonc
workspace         { "id":"ws_acme", "org_code":"ACME", "deployment_tier":"shared", "admin_email":"admin@acme.com", "status":"active" }
```

**Step 2 — Admin configures (seeded from the translation archetype, then ratified)** (E2, §6)
```jsonc
operating_entity  { "id":"oe_acme", "workspace_id":"ws_acme", "legal_name":"Acme Lab", "code":"LAB", "billing_currency":"USD", "tax_profile":"—", "invoice_prefix":"LAB" }
offering          { "id":"off_tr", "workspace_id":"ws_acme", "name":"Document Translation", "delivery_model":"deliverable", "billing_model":"unit_x_price", "version":1 }
skill             { "id":"sk_ocr",   "workspace_id":"ws_acme", "name":"OCR" }
skill             { "id":"sk_tr",    "workspace_id":"ws_acme", "name":"Translate EN→AR" }
skill             { "id":"sk_rev",   "workspace_id":"ws_acme", "name":"Review" }
skill             { "id":"sk_del",   "workspace_id":"ws_acme", "name":"Deliver" }        // mandatory last
offering_activity_template  { "offering_id":"off_tr", "seq":1, "skill_id":"sk_ocr", "qa_policy":"auto",  "dependency":null }
offering_activity_template  { "offering_id":"off_tr", "seq":2, "skill_id":"sk_tr",  "qa_policy":"human", "dependency":1 }
offering_activity_template  { "offering_id":"off_tr", "seq":3, "skill_id":"sk_rev", "qa_policy":"human", "dependency":2 }
offering_activity_template  { "offering_id":"off_tr", "seq":4, "skill_id":"sk_del", "qa_policy":"auto",  "dependency":3 }
rate              { "id":"rt_1", "workspace_id":"ws_acme", "skill_id":"sk_tr", "unit_type":"page", "rate":20, "relationship_id":null }
allocation_policy { "workspace_id":"ws_acme", "objective_weights":{...}, "channel_policy":{"default":"ws_chat"} }
```

**Step 3 — Add the expert Sara** (E3) — *this is the "where is people-skill / where is the expert" answer*
```jsonc
root_identity     { "id":"root_sara", "owner_auth_ref":"oidc|sara", "personal_workspace_ref":"pws_sara" }   // GLOBAL
entity             { "id":"ent_sara", "workspace_id":"ws_acme", "type":"person", "display_name":"Sara Khan" }
person            { "id":"per_sara", "workspace_id":"ws_acme", "entity_id":"ent_sara", "root_identity_id":"root_sara",
                    "entity_role":"performer", "contract_type":"payroll", "operating_entity_id":"oe_acme", "cost_encrypted":"<fernet>" }
person_skill      { "id":"ps_1", "workspace_id":"ws_acme", "person_id":"per_sara", "skill_id":"sk_tr", "proficiency":4, "status":"verified" }
```

**Step 4 — Add the client Globex + its user (requester)** (E4) — *this is "where the client user sits"*
```jsonc
entity             { "id":"ent_globex", "workspace_id":"ws_acme", "type":"org", "display_name":"Globex" }        // client COMPANY
relationship      { "id":"rel_globex", "workspace_id":"ws_acme", "operating_entity_id":"oe_acme",
                    "type":"client", "from_entity":"oe_acme", "to_entity":"ent_globex",
                    "invoice_code":"GLBX-01",                    // ← invoice_code lives here (per client)
                    "config":{ "code":"GLBX" }, "status":"active" }
entity             { "id":"ent_ravi", "workspace_id":"ws_acme", "type":"person", "display_name":"Ravi (Globex)" } // client USER
```

**Step 5 — Request comes in** (E5)
```jsonc
request           { "id":"req_1", "workspace_id":"ws_acme", "operating_entity_id":"oe_acme",
                    "requester_id":"ent_ravi", "brief":"Translate to Arabic", "input_files":["fr_src"], "deadline":"2026-07-20",
                    "source_channel":"email", "state":"created", "status":"not_started" }
file_ref          { "id":"fr_src", "workspace_id":"ws_acme", "store_location":"s3://acme/in/report.pdf", "owner_entity_id":"oe_acme" }
```

**Step 6 — AI composes → owner ratifies** (E6/E7)
```jsonc
proposal          { "id":"prop_1", "request_id":"req_1", "proposed_offering_id":"off_tr", "scope_sheet":{"unit_type":"page","unit_count":40}, "confidence":{...} }
assignment        { "id":"asg_1", "request_id":"req_1", "offering_id":"off_tr", "level":"standard", "unit_type":"page", "unit_count":40,
                    "owner_id":"per_owner", "price":{"amount":800,"currency":"USD"}, "invoice_code":"GLBX-01", "state":"published", "status":"on_track" }
activity          { "id":"act_ocr", "assignment_id":"asg_1", "skill_id":"sk_ocr", "performer_type":"agent", "sort_order":1, "state":"published" }
activity          { "id":"act_tr",  "assignment_id":"asg_1", "skill_id":"sk_tr",  "performer_type":"human", "dependency_activity_id":"act_ocr", "sort_order":2, "qa_policy":"human", "state":"published" }
activity          { "id":"act_rev", "assignment_id":"asg_1", "skill_id":"sk_rev", "performer_type":"human", "dependency_activity_id":"act_tr", "sort_order":3, "state":"published" }
activity          { "id":"act_del", "assignment_id":"asg_1", "skill_id":"sk_del", "performer_type":"human", "dependency_activity_id":"act_rev", "sort_order":4, "state":"published" }
```

**Step 7 — Allocate + mobilize + Sara accepts** (E8) — *the expert gets the work*
```jsonc
allocation        { "activity_id":"act_tr", "proposed_performer_id":"per_sara", "candidates_scored":[{"performer_id":"per_sara","score":0.91}] }
mobilization      { "activity_id":"act_tr", "channel":"ws_chat", "sent_at":"...", "escalation_step":0 }
access_grant_role { "id":"agr_1", "person_id":"per_sara", "scope":"act_tr", "role_type":"activity", "role_status":"accepted" }
activity (update) { "id":"act_tr", "performer_id":"per_sara" }
```

**Step 8 — Perform + QA + deliver + verify** (E9/E10) — *the expert delivers*
```jsonc
activity_io       { "activity_id":"act_tr", "file_ref_id":"fr_tr_out", "role":"output" }
file_ref          { "id":"fr_tr_out", "workspace_id":"ws_acme", "store_location":"enclave→acme store", "owner_entity_id":"oe_acme" }
activity (update) { "id":"act_del", "state":"delivered" }                          // deliverable assembled + written to Globex store
verify            { "assignment_id":"asg_1", "reconciliation":{"unit_count":40,"splits":[{"performer":"per_sara","units":40}]}, "verified_by":"per_verifier", "confirm":true }
```

**Step 9 — Money: bill Globex, pay Sara** (E11) — *the expert gets paid*
```jsonc
billable_event    { "id":"be_1", "assignment_ref":"asg_1", "verified_by":"per_verifier", "unit_count":40, "unit_price":20, "amount":800,
                    "currency":"USD", "billing_model":"unit_x_price", "operating_entity_id":"oe_acme", "client_relationship_id":"rel_globex" }
invoice           { "id":"inv_1", "operating_entity_id":"oe_acme", "client_relationship_id":"rel_globex",
                    "invoice_number":"LAB-2026-07-001", "invoice_code":"GLBX-01", "grouping_rule":"per_entity_per_period", "status":"raised" }
invoice_line      { "invoice_id":"inv_1", "billable_event_id":"be_1", "rate_snapshot":{"page":20} }
payout_line       { "billable_event_id":"be_1", "performer_id":"per_sara", "period":"2026-07", "amount":400, "status":"accrued" }   // ← Sara paid
```

**The expert path, isolated (Bhavya's Q7):** `per_sara` → `person_skill` (what she can do) → `allocation.proposed_performer_id` (picked) → `access_grant_role` (accepted) → `activity.performer_id` + `activity_io` (did the work) → `payout_line.performer_id` (got paid). No standalone "expert" table — the expert *is* a Person with a role, which is why the same human can be a performer here and a client's requester elsewhere.

---

*The what is here; the how is in [`architecture.md`](./architecture.md). Flag anything wrong or missing before approval — that's what this document is for.*
