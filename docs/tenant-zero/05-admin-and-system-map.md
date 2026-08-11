# WS 3.0 — The Admin App & How the Whole System Works

> Where the dissolved ERP actually lands, and the model that ties the four apps into one product.
> Sources: `00-master.md` (L0/L1/L2, use-case catalog H1–H5, the keep/kill/redesign map), `03-domain-redesigns.md`
> (the nine domains), `02-config-and-model.md` (config surface, typed model, readiness engine),
> `01-onboarding-and-delivery.md` (seed → ratify → JIT), `spec.md` (E1–E15), the framework/surfaces vision doc.

---

## 0. The correction this document starts from

"Put the ERP things on admin" is right in intent and wrong if taken literally. The directive on record is
**dissolve the ERP and improve every domain — not port it** (`00-master.md` §0). If we move nine ERP
screens onto an admin app, we have ported it: same modules, same manual work, a nicer shell. The whole
reason the ERP hurt was that facts lived in one system and work lived in another, and the two were kept in
step by sync, sheets and crons.

So the question is not *which screens move* but **what kind of thing each domain is**. Every one of them is
exactly one of three:

| Kind | Definition | Who touches it | Where it lives |
|---|---|---|---|
| **Config** | A declared fact the lifecycle *reads*. Changing it changes future behaviour, never past records. | Admin sets it once, tunes it rarely. | **Admin app** |
| **Lifecycle event** | Emitted by work happening. Nobody authors it; authoring it by hand is the bug. | Nobody — the engine writes it. | **The three delivery apps** |
| **Cycle** | A calendar loop that opens, accumulates, closes and is signed. | Admin runs it, on a period. | **Admin app, as a run** |

That test routes all nine domains, and it is also the answer to "how the whole WS thing will work" — because
config, events and cycles are the only three ways anything in this product moves.

---

## 1. Where each ERP domain lands

| ERP domain | Kind | Admin owns | The apps own | Nobody owns (it derives) |
|---|---|---|---|---|
| **Wallet / Credits** | Config + event | Wallet setup, funding lots, cost-per-credit, negative-balance policy, low-balance thresholds | Client sees balance and tops up; SWAT sees the intake gate | The **ledger** — written only by deduct-at-create / settle-at-verify / refund-on-cancel |
| **Invoicing** | Config + event | Invoice codes, tax profile per entity, cycle, PDF template, payment terms | SWAT's **Verify** is the trigger; client pays in their thread | The **invoice** — it fires on Verify, it is never "created" |
| **Payout** | Config + event | Rate lists, coins-per-unit, quota and incentive rules, effective dates | Expert sees their lines and payout date | The **payout amount** — verified units × the rate snapshot |
| **People / Identity / Roles** | Config | Persons, invites, role assignments, teams, entity and reporting lines | Every app reads it for who-can-see-what | — |
| **Skills / Coins / Quota** | Config | Skill catalog, proficiency, units-per-hour, quota type and data per person | Allocation reads it as a hard filter and a score | — |
| **Payroll / Compensation** | **Cycle** (monthly) | The run: open → accumulate → review exceptions → sign → pay. Statutory rules as config rows per entity/geo | — | Unpaid leave, incentives and payout all **flow in from live data** — no xlsx import |
| **Leave / Attendance** | Config + cycle | Accrual rules per entity, holiday calendars, approvals | Expert declares time off; **allocation must read it** | Attendance from device events, not a sheet |
| **Timesheet** | **Derived — build nothing** | Charge codes as config | — | **Auto-derived from activity logs.** It fills itself. The only UI is an exception path when a person disputes a line |
| **PPR** | **Cycle** (quarterly) | The run: grade curve as config, ack/dispute/publish | — | Inputs come from delivered/verified work and QA outcomes |
| **Offboarding** | Event → cycle | The NOC checklist, letter templates | — | **LWD triggers the timeline** — no daily cron |
| **Sales / CRM** | Config (pre-lifecycle) | Lead funnel, pricing setup | A won deal *becomes* a ClientRelationship + PricingRecord | — |
| **Reporting** | Derived | Nothing to configure | Each app has its own slice | Fed by the dedicated reporting store off the one engine |

**Two things to notice.**

The "nobody owns it" column is where the win is. In the ERP those cells were people: someone imported the
leave xlsx, someone ran the invoice command, someone reconciled the timesheet against Jira. Every one of
them becomes a consequence of work that already happened.

And **Timesheet is the test case for the whole thesis.** If the admin app ships a timesheet screen, we have
rebuilt the ERP. Activities already carry performer, units, start and deliver times, and a charge code
inherited from the assignment's invoice code. The timesheet is a *query*. Building a form for it would mean
asking people to re-key facts the system already holds — which is the exact ERP failure mode.

---

## 2. What the admin app therefore is

**Not** nine modules. Four jobs, and a person doing each of them is in a different mood:

1. **Get the workspace to "can deliver"** — the readiness chain, once, at the start, and again whenever a
   rung breaks.
2. **Declare the operating model** — catalog, skills, rates, teams, roles, SLAs, allocation weights,
   transparency floor, module activation. Set rarely, read constantly.
3. **Hold the people facts** — who exists, what they can do, what they cost, when they are away.
4. **Run the cycles** — payroll month, PPR quarter, invoice close, an offboarding.

Job 4 is a different surface from jobs 1–3, in the same way SWAT's **Verify** is a different surface from
SWAT's rooms: it is a ledger you work down and sign, not a conversation. That is the strongest structural
carry-over from what we have already built — **a run is Verify's twin.**

### The rooms

| Section | Rooms | Kind |
|---|---|---|
| **Readiness** | The workspace itself — the five rungs, live | Home |
| **Catalog** | Divisions → capabilities → offerings → levels; skills; rate lists | Config rooms, tree in the list |
| **People** | One room per person; teams; roles; invites | Config rooms |
| **Clients** | One room per relationship — pricing record, invoice code, transparency, SLA override | Config rooms |
| **Money** | Wallets, invoice config, statutory rules | Config + a pane |
| **Runs** | Payroll · PPR · Invoice close · Offboarding | **Full-pane ledgers, signed** |
| **Modules** | Module activation, integrations, notification policy | Config rooms |
| **Audit** | Every config change, tenant-inspectable | Full-pane table |

### Why chat-first is the right shell for config — the argument that has to hold

This is the surface where "chat-first" is least obviously correct, so it needs a real answer rather than
consistency for its own sake. The answer is in `01-onboarding-and-delivery.md`: onboarding is
**seed → ratify → JIT gap-fill**, never blank forms. The admin *ratifies AI proposals and is told what is
missing next*. That is a stream of decision cards with the reasons attached — which is exactly the shape
every other app in this product already has.

Concretely:

- A proposed catalog arrives as a **ratify card** with what it inferred and from what, the same card SWAT
  gets for a plan.
- A broken rung arrives as a **scoped alert** on the room it belongs to — "no funded wallet, prepaid
  delivery blocked" sits on the wallet room, not on a dashboard.
- A config change is a **decision with a reason in the record**. The ERP's audit log answered *what
  changed*; the room answers *why*, which is what an auditor actually asks.
- Effective-dating becomes legible: "this rate applies from the next cycle, 1 Sep" is a sentence, and the
  card can say what it will and will not touch.

Where it is *not* right, and we should not pretend: **bulk editing a rate list, or a catalog restructure
across 200 offerings, wants a grid.** Those get a full pane, like Verify. The rule is the same one we
settled for SWAT — a conversation for decisions, a table for volume.

---

## 3. The readiness chain is the admin's home

From `02-config-and-model.md`, unchanged, because it is already right:

```
can_create_request    ⟸ Person(requester) + permission
can_create_assignment ⟸ Offering + PricingRecord(matching invoice_code) + (Wallet if prepaid)
can_allocate          ⟸ Team + Expert with matching Skill
can_deliver           ⟸ Delivery skill + all above
can_invoice           ⟸ PricingRecord + billing_model
──────────────────────────────────────────────────────
OPERATIONAL ⟺ all satisfied for ≥1 offering
```

The home room states which rung is broken and what it blocks, in that order. Not a percentage, not a
checklist of 40 settings — the same principle as our lists everywhere else: **state the exception, not the
inventory.**

---

## 4. How the whole WS thing works

### One graph, four projections, one console

There is one work graph — Request → Assignment → Activity, hung off an Engagement, with a ServicePeriod for
recurring models. There are not four systems. Each app is a **point-of-view projection** of that one graph,
and the projection is computed server-side from the roles a person holds per node (WRUA), never by the
front end.

| App | Sees | Cannot see |
|---|---|---|
| **Client** | Their requests, at milestone depth by default | Who inside EZ does the work; any sub-vendor; margin; the activity layer unless transparency is raised |
| **Expert** | The nodes they hold a role on, plus the request above them if they own an assignment | The client; other experts' rates; margin |
| **SWAT** | Everything inside the workspace boundary, both books | Another operating entity's relationships when isolation is on |
| **Admin** | Config, people, money rules, cycles — and *no work content* | The inside of a room; deliverable bytes |
| **Operator L0** | Workspaces, tiers, module availability, oversight | **Any tenant content, ever** |

The last two rows are the ones that are easy to get wrong. An admin who can read every room is a
data-protection problem and, worse, an admin nobody can hire — the whole point of the enclave model is that
holding the keys does not mean seeing the bytes.

### The three couplings that make it one product

Everything else is detail; these three are the load-bearing joins.

1. **Config → lifecycle, read-only, effective-dated.** The lifecycle never writes config. Config changes
   never rewrite history — a rate change applies at the next cycle boundary, and a delivered invoice keeps
   its rate snapshot. This is the ERP primitive worth keeping, and it is why "improve don't port" does not
   mean "throw everything away".

2. **Verify → money, once.** One tap emits **one** billable event, and the invoice and the payout both hang
   off it. This is the D4 fix, and it is the single most consequential difference from WS 2.0, which
   invoiced on mark-complete and then ran a repair cron. Because there is one event, there is nothing to
   reconcile.

3. **People facts ↔ allocation, both ways.** Skills, quota and **availability** are hard filters on
   allocation; delivered and verified work feeds PPR; PPR feeds the comp multiplier; leave feeds payroll.
   This loop is why HR cannot sit outside the product — the moment it does, allocation starts proposing
   people who are on leave, which is precisely what happens today.

### The four loops, by tempo

| Loop | Period | Opens | Closes | Who signs |
|---|---|---|---|---|
| **Request** | Hours to days | Intake maps a sender | Verify | SWAT (boundary), client (delivery) |
| **Service period** | Monthly | Cadence spawns it | Period close + verify | SWAT, then client |
| **Invoice** | Monthly per entity | First billable event of the cycle | Cycle close | Admin run |
| **Payroll** | Monthly per entity | Cycle opens | Sign and pay | Admin run |
| **PPR** | Quarterly | Cycle opens | Publish | Admin run, person acks |

The request loop is the only one a client ever sees. The other three are consequences of it.

### What the platform provides vs what EZ configures

Every EZ-ism is L1 config: SWAT, QA, SME and pool are `Role` rows; the 10:20:30 SLA is an `SLAPolicy`; the
allocation weights are numbers; coins and credits are two rate scales. The platform provides role *types*,
a lifecycle, a ledger and an allocator. **If a change to EZ's operating model needs a deploy, we have built
the ERP again.**

---

## 5. What admin must set before each app can do anything

| App | Blocked until admin has set |
|---|---|
| **Client** | An OperatingEntity, a ClientRelationship, a PricingRecord with an invoice code, a requester Person, and a funded Wallet if the relationship is prepaid |
| **SWAT** | An Offering with skills, a Team, the mandatory Delivery skill, an SLA policy and allocation weights |
| **Expert** | A Person with role assignments and PeopleSkill rows, and a RateList covering their skills |
| **Runs** | A tax profile per entity, statutory rule rows per entity/geo, a grade curve for PPR |

This table is the readiness chain seen from the other end, and it is the honest answer to "why can't I do
anything yet" — a question the ERP answered with a stack trace.

---

## 6. What this exposes that we do not have an answer to

Stated rather than left to be found, in the manner of the master spec's gaps tab.

1. **Expert availability is a hard filter with no UI anywhere** — already logged as EX-28 "Gap on both".
   Section 4's third coupling does not close without it. This is now the highest-value gap in the product,
   because allocation quality depends on it and neither product has it.
2. **Timesheet dispute path.** If timesheets derive, a person who disagrees needs somewhere to say so. That
   is one exception form, but it does not exist and it is not in any spec.
3. **The statutory matrix (`J25`).** India PF/ESIC/LWF/TDS and UAE WPS as rule data is the right design; the
   actual rules are Joy's to supply. The payroll run can be built against a schema of rule rows without
   them, and cannot be *correct* without them.
4. **Module activation sits on both sides of the L0/L1 line.** L0 sets availability, L1 activates within it
   (`00-master.md` C6). Two surfaces, one concept — a place where a UI can quietly lie about who is in
   control.
5. **Entity-level isolation in the admin app.** `B5` says isolation must reach operating-entity level. An
   admin console that lists all three EZ entities' relationships in one table breaks the same rule the
   delivery apps are careful about.
6. **"Admin sees no work content" needs enforcing in the design, not asserted.** The moment a payroll
   exception says "Mara, 3 unpaid days, Q3 report assignment", content has crossed. The run should reference
   nodes by id and cost, not by what the work was.

---

## 7. What gets built, in order

1. **Readiness home + the config rooms** — catalog, people, clients, wallets. This is what unblocks
   everything else and it is the seed→ratify→JIT flow.
2. **Runs as a full pane** — payroll first, since it is the cycle with real money and the clearest sign-off.
   It reuses the Verify shell we already built for SWAT.
3. **Audit as a full pane** — cheap, and it is the "don't trust us, verify" promise made visible.
4. **The L0 operator console** — a separate, deliberately small surface. Workspaces, tiers, module
   availability, and nothing else. Its most important property is how little it can see.
