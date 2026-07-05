# WS 3.0 — Type-B Lifecycle (Retainer / Outcome)

**The ongoing-work lifecycle in `01-core-delivery` depth.** Type A (deliverable) is Joy's `01`; this is the Type-B counterpart. Same engine, the **ServicePeriod** replaces the one-shot Deliver as the billable unit.

---

## Trigger
A client engages EZ for an **ongoing service** (helpdesk, HR ops, EA, BOT) — not a one-off deliverable. An `Engagement` is created with `delivery_model ∈ {retainer, outcome}`.

## Actors / roles
Same L2 roles. Difference: a retainer usually binds a **committed resource/team** (an EA, a helpdesk team) to the engagement for its duration, rather than allocating each activity fresh (vision's committed-capacity-first).

## Pre-conditions
- An Offering with `delivery_model = retainer|outcome` + a recurring `billing_model` + `cadence`.
- A ClientRelationship + PricingRecord (the retainer fee or the outcome terms).
- A committed resource/team available for binding.
- For `outcome`: a captured **baseline** (the process's current cost/efficiency).

## Steps (end to end)

| # | Actor | Action | System behavior | State |
|---|---|---|---|---|
| 1 | SWAT/owner | Create Engagement | binds committed resource; sets cadence; (outcome) captures baseline | Engagement `active` |
| 2 | System | **Open period** (on cadence) | creates `ServicePeriod(open)` for the cycle | Period `open` |
| 3 | Expert/team | Do the ongoing work | activities logged **against the open period** (tickets handled, tasks done) | work accrues |
| 4 | System | Interim visibility | period accrues effort/usage; status derived (SLA on track?) | period live |
| 5 | System | **Close period** (cadence end) | `ServicePeriod → closed`; no new activities attach | Period `closed` |
| 6 | SWAT TL | **Verify period** | TL confirms service/SLA met for the period (retainer) or the **outcome metric** (outcome) | Period `verified` |
| 7 | System | **Invoice** | `flat_retainer` / `retainer_plus_usage` / `outcome` billing computed → invoice raised; payout computed | Period `invoiced` |
| 8 | System | **Next period opens** | loops to step 2 until the engagement is terminated | Engagement continues |
| — | Owner | Terminate | ends the engagement after the final period settles | Engagement `terminated` |

## State machine

```
Engagement : active → terminated   (never "complete" — it runs)
ServicePeriod : open → closed → verified → invoiced   (repeats each cadence)
```
- The **ServicePeriod plays the exact role "Deliver" plays for Type A** — it's the thing that gets verified and billed.
- Same **one-engine** rule: period state + status derived together, no drift.
- Same **explicit Verify gate**: nothing bills until the TL signs off.

## Business rules
1. **Period is the billable unit.** One period per cadence per engagement.
2. **Committed-capacity binding.** A retainer reserves a resource/team; utilization is tracked against the commitment (ties to the coin/quota model — fixed-cost resources saturate first).
3. **Billing by model:** `flat_retainer` = fixed fee/period; `retainer_plus_usage` = base + metered overage; `outcome` = computed from the metric vs baseline. `❓ Joy:` the exact BOT/outcome formula.
4. **Rolling verify** — periods verify + invoice as they close, not batched.
5. **SLA per period** — the period's status reflects whether the service SLA was met across the cycle.

## Edge cases
- **Mid-period scope/team change** → handled as an edit within the open period (the §5 edit-levels apply); no new engagement.
- **Missed SLA in a period** → flagged at Verify; affects the period's status + (config) any SLA credit on the invoice.
- **Usage spike (retainer_plus_usage)** → overage metered into the period's invoice.
- **Termination mid-period** → final period pro-rated + settled at Verify.
- **Outcome not met** → the outcome billing computes accordingly; `❓ Joy:` floor/penalty rules.

## Variations
- **`retainer` vs `outcome`** differ only in step 6 (verify service-met vs verify-metric) and step 7 (fee vs metric-computed).
- A retainer **can still spawn deliverables** — e.g. an HR-ops retainer that also produces a one-off report → that report is a normal Type-A Assignment *inside* the period. The models compose.

## WS 3.0 notes
- The recurring/period model **leans event/scheduler-driven** — periods auto-open/close on cadence (`❓ Bhavya:` reinforces event-sourced consideration).
- No manual monthly kickoff/close — automation removes a whole class of ops work.
- `Engagement` + `ServicePeriod` sit above the unchanged work graph (see `06`).

## Open items
- `❓ Joy`: the outcome/BOT billing formula; how committed-capacity binding maps to EZ's real staffing; the period-close SLA-verify criteria.
- `❓ Bhavya`: period scheduling in the transactional-vs-event-sourced choice.
