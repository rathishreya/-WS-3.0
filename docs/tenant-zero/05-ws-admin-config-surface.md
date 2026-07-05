# WS 3.0 — The WS-Admin Config Surface

**What the workspace admin (L1) configures — every knob, declaratively.** This is the operational proof of "configure everything, hardcode nothing." Each config object lists its fields, defaults, and the **readiness rule** that unblocks delivery.

**Principle:** every object is *declarative* (chosen/tuned values, never logic), has *sane defaults*, and can be pre-seeded by an *archetype skeleton* + AI-assist. The admin ratifies, doesn't fill blank forms.

---

## The config object model (overview)

```
Workspace (L1)
├── Foundation
│   ├── Organization        (identity, brand, terminology)
│   ├── OperatingEntity[]    (legal/billing units — EZ Lab / AEZ / CASPR)
│   └── DeploymentTier       (shared/regional/sovereign + keys)
├── Operating Model
│   ├── Catalog: Division → Capability → Offering (+ delivery/billing model)
│   ├── Skill[] + RateList[] (+ the mandatory Delivery skill)
│   ├── Team[] + Role[]      (the delivery engine — SWAT/QA/SME/pool as config)
│   ├── SLAPolicy[]          (10:20:30-style, per tier/service)
│   ├── AllocationPolicy     (the weights)
│   ├── TransparencyDefault  (the opacity dial floor)
│   └── ModuleActivation[]   (which first-party modules are on)
├── Relationships
│   ├── ClientRelationship[] (per-client terms, per-relationship transparency)
│   ├── PricingRecord[]      (invoice codes, payment type)
│   └── QAReferenceData[]    (per-client knowledge)
└── Live Operations
    ├── Person[] + roleassignment (experts/SWAT/requesters)
    ├── Wallet[]             (prepaid funding)
    ├── Integration[]        (TR42, Phrase, email, payment gateway…)
    └── NotificationPolicy[] (channel-native rules)
```

---

## Foundation layer (rare — the admin, seldom changed)

**Organization** — `name`, `code` (immutable), `brand` (colors/logo tokens), `terminology_map` (org's own words → platform concepts), `default_currency`.
**OperatingEntity[]** — `name`, `code` (immutable), `billing_currency`, `tax_profile` (VAT/WHT/none + %), `invoice_prefix`, `allowed_currencies[]`. *One org → many.*
**DeploymentTier** — `tier` (shared|regional|sovereign, default **shared**), `keys` (BYOK at regional/sovereign).

*Readiness:* ≥1 OperatingEntity exists → invoicing/wallet can be configured.

---

## Operating-Model layer (the core — seeded, evolves)

**Catalog** — `Division[] → Capability[] → Offering[]` (many-to-many capability, primary/secondary).
- **Offering** fields: `name`, `capability[]` (primary+secondary), `levels[]`, `skills[]`, `type_of_unit`, `source/target_lang`, **`delivery_model`** (deliverable|retainer|outcome, default *deliverable*), **`billing_model`** (unit_x_price|flat_retainer|retainer_plus_usage|outcome), `cadence` (if recurring), `completion_rule`, `selling/min/optimal_price`, `est/researched_cost`, `description` (AI-generated if blank).
- **Level** (within offering): `name`, optional own `price` / `skills` / `QA_rule` / `SLA` — `⚠️ J10` first-class vs descriptive.

**Skill[]** — `name`, `proficiency`, `type_of_unit`, `src/tgt_lang`, `country`, `selling/cost_price`, `units_per_hour`, `incentive_pct`. Plus the **mandatory `Delivery` skill** (seeded, not invented).
**RateList[]** — `skill`, `coins_per_unit`, `incentive_pct`, `effective_date`. *(Config object — no more Google-Sheet loading.)*

**Team[] + Role[]** — the delivery engine as config. `Team` = `name`, `capability?`, `members[]`, `parent?`. `Role` = a *named instance* of a platform role-type (request/assignment/activity access) — e.g. EZ maps "SWAT" / "QA" / "SME" / "pool" onto the primitives here. `⚠️ J1` needs Joy's definition to seed EZ's set.
**SLAPolicy[]** — `name`, `tiers` (the 10:20:30 semantics `⚠️ J9`), `applies_to` (tier/service/level), `deadline_rules`.
**AllocationPolicy** — weights for `fit · quality_to_cost · committed_capacity_first · deadline_confidence · responsiveness` (defaults from vision §4.5; tunable). `⚠️ J12`.
**TransparencyDefault** — `floor` (opaque default), per-relationship override allowed.
**ModuleActivation[]** — which first-party modules are on (Delivery, Invoicing, Wallet, People, Payroll, Leave, Timesheet…), bounded by L0's availability.

*Readiness:* ≥1 Offering + its Skills + Delivery skill + a Team with an Expert → work can be created & allocated.

---

## Relationships layer (per-client — as formed)

**ClientRelationship[]** — `client`, `entity`, per-relationship `terminology_equivalences`, `transparency_level` (raises the floor), `sla_override`. **Entity-scoped isolation flag** (from the EY case) — controls whether sibling operating-entities can see this relationship (default **isolated**).
**PricingRecord[]** (invoice codes) — `entity`, `offering_pricing[]`, `currency`, `payment_type` (prepaid|postpaid), `valid_from/till`, auto-generated `invoice_code`.
**QAReferenceData[]** — per-client reference the in-scope AI retrieves (distinct from cross-tenant training).

*Readiness:* a PricingRecord whose invoice_code matches the assignment → assignment can be created & priced.

---

## Live-Operations layer (frequent — delegated module-admins)

**Person[]** — identity + `role_assignments[]` (which Team/Role, which capability) + `skill_assignments[]` (PeopleSkill: skill, quota_type, quota_data). *Manual create/invite now; SSO-ready.*
**Wallet[]** — `entity`, `requesters[]`, funded lots (prepaid). *Ledger-based, no sheet.*
**Integration[]** — `type` (TR42|Phrase|email|payment_gateway|…), `config`, `enabled`. Tier-gated (sovereign blocks egress tools).
**NotificationPolicy[]** — channel (WhatsApp/SMS/email/in-app), `recipient_rules` (role+role_type+status — configurable, *no more @mckinsey hardcode*), `template`, per-client overrides.

*Readiness:* a funded Wallet (if prepaid) + Experts with the offering's skills → the first assignment flows to delivery.

---

## The readiness engine (how "onboarded = can deliver" is enforced)

The system knows the dependency chain and computes a **live readiness state** per workspace:

```
can_create_request  ⟸ Person(requester) + permission
can_create_assignment ⟸ Offering + PricingRecord(matching invoice_code) + (Wallet if prepaid)
can_allocate         ⟸ Team + Expert with matching Skill
can_deliver          ⟸ Delivery skill + all above
can_invoice          ⟸ PricingRecord + billing_model
──────────────────────────────────────────────
WORKSPACE OPERATIONAL ⟺ all of the above satisfied for ≥1 offering
```

The admin UI surfaces exactly what's missing ("offerings ✓, experts ✓, **no funded wallet — prepaid delivery blocked**"). Deeper config (more offerings, SLAs, experts) is JIT-enriched after operational.

---

## Config change discipline
- **Versioned** — catalog restructuring (rename/merge/move offerings) is safe & reversible; history preserved.
- **Effective-dated** — rate/pricing changes apply at cycle boundaries, never mid-flight (carried from the good ERP primitive).
- **Delegated** — Foundation locked to the primary admin; Live-Ops delegable to module-admins (§9.2).
- **Audited** — every config change is tenant-inspectable.
