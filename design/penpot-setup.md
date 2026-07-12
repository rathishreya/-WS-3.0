# WS 3.0 — Penpot design kit

**Goal:** design WS 3.0 in Penpot on a real, shared system — not from a blank canvas. This folder gives you the **design tokens** (colors, type, spacing, radius) and the **screen + component inventory** that map 1:1 to the working HTML prototype.

> **Why not a live Penpot from the AI session?** Penpot self-hosts as a multi-container stack (frontend, backend, exporter, Postgres, Redis) and needs a persistent host + URL. The build environment here is ephemeral with no public address, so a Penpot started there would vanish and be unreachable. Instead: **you run Penpot** (cloud or self-host, both below) and import this kit.

---

## 1. Get Penpot (pick one)

- **Fastest — cloud:** sign in at **penpot.app** (free, hosted). No setup.
- **Self-host (own data, on your infra — recommended for a real product):**
  ```bash
  # on your own machine/server, not the AI session
  wget https://raw.githubusercontent.com/penpot/penpot/main/docker/images/docker-compose.yaml
  docker compose -p penpot -f docker-compose.yaml up -d
  # → http://localhost:9001
  ```
  Follow the current official guide (versions change): https://help.penpot.app/technical-guide/getting-started/#self-host-with-docker

---

## 2. Import the design tokens

1. Open (or create) a Penpot file → open the **Tokens** tab (left panel).
2. **Import** → choose `design/ws3.tokens.json`.
3. You'll get three token sets — **core** (spacing, radius, type), **light**, **dark** — and two **themes** (Light / Dark). Switch themes to preview both.
4. Now every fill, text style, radius and spacing you apply pulls from a token — change `brand` once and the whole file updates.

*The values are the exact ones from the prototype (`design/ws3-ui-prototype.html`), so what you design will match what we build.*

---

## 3. The design language (so it stays one system)

| Aspect | Rule |
|---|---|
| **Accent discipline** | **Blue = action** (`brand`). **Violet = AI only** (`ai`) — never decorate with it; it means "the machine proposed this." Semantic green/amber/red = **status only**, not accent. |
| **Neutrals** | cool-biased grey (`muted`, `faint`) — chosen, not default. |
| **Type** | headings `type.h1/h2` (tight tracking, weight 740); body `type.body`; uppercase micro-labels `type.label` with letter-spacing; `mono` for IDs/data. |
| **Radius** | cards `radius.lg` (18), inputs/pills `radius.sm/md`, chips `radius.pill`. |
| **Spacing** | stick to the `space` scale (4→48); lay out with auto-layout + gap, not manual margins. |
| **Depth** | 1px `line` border + soft shadow; avoid heavy drop-shadows. |
| **Motion (for prototype)** | quick rise/fade on navigate; hover lift on cards. Respect reduced-motion. |
| **Icons** | line icons, ~1.7 stroke (match the prototype's SVG set). **No emoji in the product UI.** |
| **Signature** | the **work-graph** (nodes + connectors) is the product's motif — use it in empty states, the hero, the tree. |

---

## 4. Component library to build (in this order)

Build these as Penpot **components** first; screens then assemble from them.

1. **Buttons** — primary (brand) · secondary (outline) · ghost · AI (violet) · sizes sm/md.
2. **Inputs** — text · select · textarea · segmented control · toggle (knob) · switch-row.
3. **Status pill** — variants: on-track/verified (green) · slightly-delayed (amber) · critical (red) · queued (neutral) · **AI-proposed (violet)**.
4. **Card** — base + hover; padded + section header.
5. **List row** — avatar + title/subtitle + trailing (pill/button).
6. **Work-graph node** — number/check chip + title/subtitle + status; with connector spine (done / now / blocked states).
7. **AI suggestion block** — violet-tinted, uppercase "AI proposed" label, accept/edit affordance.
8. **KPI stat** · **Stepper** · **Readiness gauge** (conic) · **Inspector panel** · **Callout** · **Empty state** · **Phone/WhatsApp frame**.
9. **App chrome** — sidebar (workspace switcher + grouped nav) · top bar (role chip + ⌘K command + theme + avatar).

---

## 5. Screens to design (mirror the prototype)

Reference the interactive prototype for layout + copy: `design/ws3-ui-prototype.html`.

**Set up** — Readiness board (skippable) · Invite people · Operating-entity form · Add-client form (optional)
**Superadmin (L0)** — Workspaces · New workspace form
**Admin (L1)** — Admin home · Offering editor
**The work** — New request · **Ratify plan (touchpoint #1)** · Work tree (+ inspector) · **Verify (touchpoint #2)**
**Portals** — Client portal · Vendor portal (+ opaque running view) · Expert home (with the live accept→work→QA→deliver→paid flow)
**Explain it** — "All workflows" map (who acts · what's automatic · the 2 human gates)

**Frame sizes:** desktop 1440×1024 (12-col, 80px margins, 24px gutter) · optional mobile 390×844 for the expert/requester + WhatsApp edge.

---

## 6. Optional next step — a Penpot plugin that scaffolds frames

Penpot has a Plugin API (`penpot.createBoard`, `createText`, `createRectangle`, tokens access). I can write a plugin that **auto-generates the component library + key frames** from these tokens, so you start with the screens already laid out instead of drawing them. It needs to be loaded into *your* Penpot (a manifest URL), and I'd want to verify it against the current Plugin API version. Say the word and I'll build it.

---

## Files in this folder
- `ws3.tokens.json` — importable design tokens (light + dark, core scale). **Source of truth for color/type/space.**
- `penpot-setup.md` — this guide.

*The living visual reference remains the prototype (`design/ws3-ui-prototype.html`) and the IA/interaction rules in the vision (§13) + `spec.md` §3.*
