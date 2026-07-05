# WS 3.0 — Onboarding → Delivery: The Unified Design (deliverable + ongoing work)

**Status:** Draft v1 — design/workflow only, no code. Supersedes the delivery depth in `02`.
**Decision it implements:** the onboarding→delivery path must hold **both** Type A (deliverables) and Type B (ongoing/retainer/BOT) from the start.
**Sources:** Foundational Vision (§3 primitives, §4 lifecycle, §7 commercials, §9 config), Joy's `01-core-delivery`, the Finalised Services catalogue, the dissolve-ERP decision.
**Legend:** `⚠️` design decision (confirm) · `❓` open question for Joy/Bhavya.

---

## 0. The problem this solves

EZ sells two shapes of work:
- **Type A — deliverables:** "translate this deck," "design these slides." Finite: do it, hand it over, bill once.
- **Type B — ongoing services:** "run our helpdesk," "run our HR ops," AI Transformation (BOT). No single deliverable — it runs on a cadence and bills recurringly.

WS 2.0 only models Type A (unit×price, deliver-once). This design holds **both in one engine**, so nothing is a special case and nothing gets bolted on later.

---

## 1. The unifying abstraction: **the delivery model**

Keep the BAT primitives exactly (Vision §3): **Activity** (inputs → performer → skill → outputs) → **Assignment** (group of activities) → **Request** (crosses a boundary). The **work graph is identical for both types.**

Add one governing concept — the **Engagement** — carrying a **`delivery_model`** that decides *how activities roll up to a billable event*:

| delivery_model | Recurrence | "Completion" means | Billing trigger | EZ examples |
|---|---|---|---|---|
| **`deliverable`** (Type A) | one-shot | outputs delivered + verified → **terminal** | once, at Verify | Translation, Slide Design, Pitch Deck |
| **`retainer`** (Type B) | cyclic (e.g. monthly) | a **service period** closes → verified | per period | Shared EA, Contact Centre, HR Operations |
| **`outcome`** (Type B / BOT) | cyclic | a period closes + an **outcome metric** is measured | per period, computed from the metric | AI Transformation (YoY efficiency) |

**The one insight:** the difference between A and B is **not** the work — it's *what counts as the billable event* (a delivered output vs. a closed period) and *how it's priced*. Both are the same engine, differing only by config on the offering.

`⚠️` I'm introducing **Engagement** as the container above Request (a one-off engagement holds one request; a recurring engagement spawns a period each cycle). Confirm the naming — could also be "Service Agreement."

---

## 2. Billing model, decoupled from delivery model

Billing is a *separate* config axis, so any delivery model can use any compatible price rule:

| billing_model | How the invoice is computed | Pairs with |
|---|---|---|
| `unit_x_price` | `unit_count × price_per_unit` (the WS 2.0 spine) | deliverable, retainer-with-usage |
| `flat_retainer` | fixed fee per period | retainer |
| `retainer_plus_usage` | base fee + metered overage | retainer |
| `outcome` | computed from an efficiency/outcome metric vs. a baseline | outcome/BOT |

Decoupling delivery from billing is what keeps this **config, not code**: the WS admin picks `delivery_model` + `billing_model` per offering — no new engine per commercial shape.

---

## 3. Onboarding → config (unified for A and B)

The config-to-deliver dependency chain from `02` stands — with the delivery/billing model added to the catalog rung:

```
(1) Foundation → (2) People & Roles → (3) Teams (delivery engine) → (4) CATALOG*
    → (5) Skills (+ Delivery skill, rate list) → (6) Pricing/Invoice codes → (7) Wallet (if prepaid)
    ✅ can deliver — both types

* (4) CATALOG — each Offering now carries:
     delivery_model ∈ {deliverable, retainer, outcome}
     billing_model  ∈ {unit_x_price, flat_retainer, retainer_plus_usage, outcome}
     cadence        (only if recurring: monthly / weekly / custom)
     completion_rule (what closes a deliverable vs. a period)
```

So the **same admin surface** onboards both: a Translation offering (`deliverable` / `unit_x_price`) and a Helpdesk offering (`retainer` / `flat_retainer`, monthly) are configured identically — just different values. No hardcoding.

`⚠️` Retainers usually run on **committed capacity** (a dedicated EA/team) rather than per-activity allocation. That's already in the vision's allocation objective ("committed-capacity-first"), so the same allocation engine handles it — an engagement can bind a committed resource for its duration instead of allocating each activity fresh.

---

## 4. The delivery lifecycle (both models, shared stages)

The nine vision stages hold for both; the **delivery model flexes three of them**: completion, the Verify gate, and the billing trigger.

### 4a. Deliverable path (Type A) — one-shot
```
Request → Create Assignment → Allocate & Start → Work → Deliver
        → Verify (TL sign-off) → Invoice(once) → Payout
        → ENGAGEMENT COMPLETE (terminal)
```
This is Joy's `01-core-delivery`, with the WS 3.0 fix: **explicit Verify gate before the commercial trigger** (no auto-invoice-on-complete).

### 4b. Retainer path (Type B) — cyclic
```
Create Engagement (bind committed team/resource, set cadence)
   └─► [ each period, automatically ]
        Open Period → work accrues (activities logged against the period)
                    → Period Close (on cadence)
                    → Verify (TL confirms service/SLA met for the period)
                    → Invoice (flat_retainer or retainer_plus_usage) → Payout
                    → next Open Period …
   (continues until the engagement is terminated)
```
The **service period is the billable unit** — it plays the exact role "Deliver" plays for Type A. Same Verify gate, same rolling-invoice discipline.

### 4c. Outcome / BOT path (Type B)
Same as retainer, but:
- an **outcome baseline** is captured at engagement start (the process's current cost/efficiency),
- each period's **Verify** confirms the outcome metric,
- **Invoice** is computed from the metric (the YoY-efficiency commitment), not a flat fee.

`❓ Joy:` how is the BOT efficiency metric actually measured and billed today (or intended)? This is the one place I have shape but not the formula.

### 4d. What's shared across all three (the efficiency core)
- **One lifecycle engine** — state + status derived in the same transaction → no drift, no repair crons (applies to periods too).
- **Explicit, rolling Verify gate** → nothing bills until a human TL signs off; kills the batch crunch.
- **Push/event-driven** — periods auto-open/close on cadence; no manual monthly kickoff.

---

## 5. Worked examples

**A — Translation (deliverable / unit_x_price)**
Requester submits "translate 20-page deck EN→AR" → AI maps to *Translation · EZ Assured · EN→AR* → assignment, split, TR/PR/QA activities → allocate expert (one-tap accept) → work in TR42 → deliver → **TL verifies → invoice once (units × rate) → expert paid** → complete.

**B1 — Helpdesk (retainer / flat_retainer, monthly)**
Client signs a helpdesk engagement → committed support team bound → **October period opens** → tickets handled as activities all month → **period closes Oct 31** → **TL verifies SLA met** → **invoice October's flat fee** → November period opens automatically. Runs until terminated.

**B2 — AI Transformation (outcome / outcome, monthly)**
Client hands over a process → **baseline efficiency captured** → EZ runs it with AI + committed team → each month: period closes → **TL verifies the efficiency metric** → **invoice computed from the committed YoY gain** → repeat.

Same engine, same stages, same Verify discipline — only the config differs.

---

## 6. Typed domain-model implications (feeds Shreyanshi + Bhavya)

- **New:** `Engagement { delivery_model, billing_model, cadence, completion_rule, committed_resource? }`, and `ServicePeriod { engagement, period_start, period_end, status }` for recurring models.
- **Unchanged:** the work graph — Request → Assignment → Activity + role/role_type/role_status.
- **Billing** reads `billing_model` off the engagement/offering; the "mark complete → invoice" coupling is replaced by an explicit **Verify → billable-event** step that fires per-delivery (A) or per-period-close (B).
- Kills the assumption baked through WS 2.0 that "every billable thing has a unit_count and a deliverable."

---

## 7. Open items

**For Joy:** the BOT outcome formula (§4c); whether "committed capacity" binding for retainers matches how EZ staffs them; the period-close + SLA-verify rules for retainers; + the P0 items in `03-questions-for-joy` (delivery engine, A1–A6) still apply to Type A.

**For Bhavya:** does modeling `Engagement`/`ServicePeriod` above the work graph fit the lifecycle-engine choice (transactional vs event-sourced)? Recurring periods lean toward an event/scheduler-driven model.

**Confirm with Shreyanshi:** the `Engagement` container name, and that `deliverable/retainer/outcome` × `unit_x_price/flat_retainer/retainer_plus_usage/outcome` is the right config matrix (not too many, not too few).

---

## Why this is the efficient design
- **One engine, not two** — no separate retainer system to build or maintain.
- **Recurrence is automatic** — periods open/close on cadence; no manual monthly setup (removes a whole class of ops work).
- **Everything is config** — a new commercial shape is a new `delivery_model`×`billing_model` combination, not new code.
- **The Verify gate + rolling billing** apply uniformly — no batch reconciliation, for deliverables *or* periods.
