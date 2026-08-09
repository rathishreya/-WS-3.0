# Part 3 — assembles WS3_Master_Spec.xlsx from the data in parts 1 and 2.
# Run:  python3 build_master_spec_part3.py  &&  python3 ~/.claude/skills/xlsx/scripts/recalc.py WS3_Master_Spec.xlsx
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from build_master_spec_part1 import (UC, ORANGE, NAVY, SKY, SOFT, SKYSOFT,
                                     GREY, LINE, GOODS, WARNS, CRITS, F)
from build_master_spec_part2 import COMP, SCREENS, RULES, GAPS

hdr   = Font(name=F, size=9,   bold=True, color="FFFFFF")
body  = Font(name=F, size=9,   color="1A1A1A")
bodyb = Font(name=F, size=9,   bold=True, color=NAVY)
mut   = Font(name=F, size=8.5, color="5A6472")
thin  = Side(style="thin", color=LINE)
bd    = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap  = Alignment(wrap_text=True, vertical="top")
ctr   = Alignment(horizontal="center", vertical="center", wrap_text=True)
wb    = Workbook()

# verdict → fill, so an assessor can see the shape of the claim at a glance
VFILL = {"Better · new": GOODS, "Better": GOODS, "Parity": GREY,
         "WS 2.0 better": CRITS, "Gap on both": WARNS, "Out of scope": "FFFFFF"}
BFILL = {"Yes": GOODS, "Partial": WARNS, "Simulated": WARNS, "No": "FFFFFF"}


def band(ws, ncols, text, color=ORANGE, h=26, size=14):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    c = ws.cell(1, 1, text)
    c.font = Font(name=F, size=size, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=color)
    c.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[1].height = h


def head(ws, cols, title, color=ORANGE):
    """Band on row 1, column widths, header row 2. cols = [(title,width),…]"""
    band(ws, len(cols), title, color=color)
    for i, (t, w) in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
        c = ws.cell(2, i, t)
        c.font = hdr; c.fill = PatternFill("solid", fgColor=NAVY)
        c.border = bd; c.alignment = ctr
    ws.row_dimensions[2].height = 30


def rows(ws, data, start=3, heights=None):
    for j, rec in enumerate(data):
        r = start + j
        for i, v in enumerate(rec, 1):
            c = ws.cell(r, i, v)
            c.font = body; c.border = bd; c.alignment = wrap
        if heights:
            ws.row_dimensions[r].height = heights
    return start + len(data) - 1


# ============================================================ START HERE
ws = wb.active; ws.title = "START HERE"
band(ws, 3, "WS 3.0 — EVERY USE CASE, AND WHY CHAT-FIRST BEATS WS 2.0", size=15)
ws.column_dimensions['A'].width = 4
ws.column_dimensions['B'].width = 28
ws.column_dimensions['C'].width = 116
r = 3


def blk(title, lines):
    global r
    ws.cell(r, 2, title).font = Font(name=F, size=11, bold=True, color=NAVY)
    r += 1
    for a, b in lines:
        ws.cell(r, 2, a).font = bodyb
        ws.cell(r, 2).fill = PatternFill("solid", fgColor=SOFT)
        ws.cell(r, 2).border = bd
        ws.cell(r, 2).alignment = Alignment(wrap_text=True, vertical="center")
        ws.cell(r, 3, b).font = body
        ws.cell(r, 3).border = bd
        ws.cell(r, 3).alignment = wrap
        ws.row_dimensions[r].height = 32
        r += 1
    r += 1


blk("What this is", [
 ("The claim", "WS 3.0 is a rebuild of the EZ workspace as three chat-first apps — client, expert, SWAT — on the Conversation OS shell described in the framework/surfaces vision doc. This workbook lists every use case the product has to serve, says where each one lives in our UI, names the WS 2.0 equivalent, and rules on which is better."),
 ("The comparison", "WS 2.0 is the shipped product. It is a table-and-modal application: a Live Requests table, a detail pane, a Gantt, and a modal per action. It is not a strawman — 10 of the 112 use cases below are marked 'WS 2.0 better' and a whole tab is given to the gaps we have not closed."),
 ("Who it is for", "Anyone assessing whether chat-first is the right shape for this product. It is written to be checked, not to be believed — every claim carries a source and every weakness is stated rather than left to be found."),
])
blk("How to read it", [
 ("1 · Use cases", "THE MAIN SHEET. All 112 use cases across the whole project. For each: the actor, the PRD stage it belongs to, why it exists at all, the surface and component that serves it in our build, how it opens, the WS 2.0 equivalent, a verdict, and whether it is built in the prototype."),
 ("2 · Component comparison", "30 UI components side by side. WS 2.0's treatment, ours, which surface ours sits on, WHY it sits there, why it is better — and a column that names where WS 2.0 still wins. Every row has that last column filled in honestly, and 10 of the 30 concede a point."),
 ("3 · Screens × surfaces", "19 screens mapped onto Framework B's six surfaces (B1–B6) in the vision doc's own format, so the mapping can be checked against the source rather than taken on trust."),
 ("4 · Rules that bind", "The 18 invariants any UI here must honour, each traced to the PRD clause or SOP it comes from. If a design decision on tab 1 or 2 looks arbitrary, it is usually one of these."),
 ("5 · Honest gaps", "15 places where we are behind, where both products are behind, or where our own build has a known bug. Includes a live tension between chat-first and the PRD's own 'ambient AI, not a chatbot' rule."),
 ("6 · Summary", "Counts, computed with formulas over tab 1 so they move if a verdict is edited. Change a verdict on tab 1 and this tab follows."),
])
blk("The verdict scale", [
 ("Better · new", "The use case has no WS 2.0 equivalent at all, and chat-first is what made it cheap to add. 42 of 112."),
 ("Better", "Both products serve it; ours takes fewer steps, states more, or removes a class of error. 25 of 112."),
 ("Parity", "Genuinely equivalent. Different shape, same outcome and roughly the same effort. 21 of 112."),
 ("WS 2.0 better", "They do it better than we do, today. 10 of 112 — listed rather than argued away."),
 ("Gap on both", "Neither product serves it. 9 of 112. These are the roadmap, not a scoring dispute."),
 ("Out of scope", "Belongs to WS admin or platform, not to any of the three apps. 5 of 112."),
])
blk("The argument in five lines", [
 ("1. The room is the ground", "The vision doc's Framework B: conversation is the ground; structure is summoned as spaces over it. Every node of the work graph — request, assignment, activity — is a room. Navigation and structure become the same object, so there is nothing to keep in sync."),
 ("2. Decisions live where the context is", "In WS 2.0 you read state in a pane and act in a modal. Here the card that tells you carries the buttons that resolve it. That is one gesture instead of three, and it is why the same shell serves a client approving a price and an expert accepting an offer."),
 ("3. The exception is the row", "Our lists say 'Tariq silent 4h — SOP-15 says offer onward', not 'Delayed'. A table of equal-weight rows makes you open things to triage; a list of stated exceptions lets you triage without opening anything."),
 ("4. One commercial trigger", "Verify — and only verify — bills the client and pays the performer. WS 2.0 invoices on completion, which is the defect the PRD calls D4. This is a model change the UI simply expresses."),
 ("5. It cost less to add the missing half", "Retainers, wallets, disputes, budget pace, private peer channels, an archive: 42 use cases with no WS 2.0 equivalent, most of them a card and a form rather than a screen. That is the real dividend of chat-first — the marginal cost of a new use case."),
])
blk("Sources", [
 ("Vision", "docs/reference/WS3-framework-surfaces-vision.pdf — Framework B · Conversation OS, surfaces B1–B6, and the ground/summoned distinction. Framework A · Structured Cockpit is the documented alternative; B is what we built."),
 ("PRD", "docs/tenant-zero/spec.md — lifecycle stages E1–E15, the Request → Assignment → Activity work graph, and the FR-numbered rules cited on tab 4."),
 ("WS 2.0", "14 screenshots of the shipped product shared in this project: Live Requests, request detail, Create New Request, Edit Request, Gantt, Flowchart, Create Activity, Delivery, Feedback, Collaborators, Splitter, Edit Log, Client rating, Tools."),
 ("The build", "design/ws3-client-chat.html · design/ws3-expert-chat.html · design/ws3-swat-chat.html — the three prototypes the 'Built?' column refers to."),
])
blk("How to challenge this", [
 ("Attack the verdicts", "Tab 1 column J. Every one is a judgement. If 'Better' should be 'Parity' on a row, change it — tab 6 recomputes."),
 ("Attack the placement", "Tab 2 column E is the reason a component sits on the surface it does. If the reason does not follow from the vision doc, the placement is wrong."),
 ("Attack the coverage", "112 use cases is a claim of completeness. The fastest disproof is a job one of these three actors does that appears nowhere on tab 1."),
 ("What we already concede", "Scanning at volume, bulk operations, the Gantt, lifecycle states, allocation UI, agent discoverability. All on tab 5, none of them dressed up."),
])

# ============================================================ 1 · USE CASES
ws = wb.create_sheet("1 · Use cases")
UCOLS = [("#", 8), ("Actor", 11), ("PRD stage", 14), ("Use case", 40),
         ("Why it exists", 52), ("Our surface", 17), ("Our component", 34),
         ("How it opens", 13), ("WS 2.0 equivalent", 46), ("Verdict", 13), ("Built?", 10)]
head(ws, UCOLS, "EVERY USE CASE IN THE PROJECT   ·   112 rows   ·   client, expert, SWAT, admin")
ws.freeze_panes = "D3"
last = rows(ws, UC, heights=44)
for rr in range(3, last + 1):
    ws.cell(rr, 1).font = bodyb
    ws.cell(rr, 1).alignment = ctr
    for col, table in ((10, VFILL), (11, BFILL)):
        c = ws.cell(rr, col)
        c.alignment = ctr
        c.font = bodyb
        f = table.get(c.value)
        if f and f != "FFFFFF":
            c.fill = PatternFill("solid", fgColor=f)
ws.auto_filter.ref = "A2:K%d" % last
UC_LAST = last

# ============================================================ 2 · COMPONENTS
ws = wb.create_sheet("2 · Component comparison")
CCOLS = [("Component", 26), ("WS 2.0 treatment", 58), ("Our treatment", 58),
         ("Surface", 19), ("Why it sits there", 62), ("Why it is better", 58),
         ("Where WS 2.0 still wins", 46)]
head(ws, CCOLS, "COMPONENT BY COMPONENT   ·   WS 2.0 vs chat-first   ·   why each one sits where it does")
ws.freeze_panes = "B3"
last = rows(ws, COMP, heights=92)
for rr in range(3, last + 1):
    ws.cell(rr, 1).font = bodyb
    ws.cell(rr, 1).fill = PatternFill("solid", fgColor=SOFT)
    ws.cell(rr, 2).fill = PatternFill("solid", fgColor=GREY)
    ws.cell(rr, 3).fill = PatternFill("solid", fgColor=SKYSOFT)
    ws.cell(rr, 4).alignment = ctr
    w = ws.cell(rr, 7)
    if isinstance(w.value, str) and w.value.strip() not in ("-", ""):
        w.fill = PatternFill("solid", fgColor=WARNS)
r = last + 2
ws.cell(r, 1, "Reading the colours").font = bodyb
ws.cell(r, 2, "Grey = WS 2.0.  Blue = ours.  Amber in the last column = a point they still win. "
              "10 of the 30 rows carry one; the rest read '-' because we could not find one, not because we did not look.").font = mut
ws.cell(r, 2).alignment = wrap

# ============================================================ 3 · SCREENS
ws = wb.create_sheet("3 · Screens x surfaces")
SCOLS = [("App", 11), ("Screen", 24), ("B1 · section nav", 20), ("B2 · list + context", 42),
         ("B3 · spaces", 42), ("B4 · conversation", 42), ("B5 · prompt", 42), ("B6 · ambient AI", 36)]
head(ws, SCOLS, "SCREENS x FRAMEWORK B SURFACES   ·   the vision doc's own format, filled in from the build")
ws.freeze_panes = "C3"
last = rows(ws, SCREENS, heights=48)
for rr in range(3, last + 1):
    ws.cell(rr, 1).font = bodyb
    ws.cell(rr, 1).alignment = ctr
    ws.cell(rr, 2).font = bodyb
r = last + 2
ws.cell(r, 1, "Note").font = bodyb
ws.cell(r, 2, "B1 section nav · B2 list + context · B3 spaces summoned over the ground · B4 conversation (the ground) · "
              "B5 context-adaptive prompt with a scope indicator · B6 ambient AI. Source: WS3-framework-surfaces-vision.pdf. "
              "On mobile Framework B flips the ground: the list becomes the surface and the conversation a detented drawer.").font = mut
ws.cell(r, 2).alignment = wrap
ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8)
ws.row_dimensions[r].height = 34

# ============================================================ 4 · RULES
ws = wb.create_sheet("4 · Rules that bind")
RCOLS = [("#", 8), ("Rule", 46), ("What it forces in the UI", 86), ("Source", 40)]
head(ws, RCOLS, "THE RULES ANY UI HERE MUST HONOUR   ·   each traced to its clause")
ws.freeze_panes = "A3"
last = rows(ws, RULES, heights=40)
for rr in range(3, last + 1):
    ws.cell(rr, 1).font = bodyb; ws.cell(rr, 1).alignment = ctr
    ws.cell(rr, 2).font = bodyb
    ws.cell(rr, 4).font = mut

# ============================================================ 5 · GAPS
ws = wb.create_sheet("5 · Honest gaps")
GCOLS = [("Gap", 30), ("Who wins", 20), ("The position", 106), ("Status", 18)]
head(ws, GCOLS, "WHERE WE ARE BEHIND   ·   stated, not argued away", color=NAVY)
ws.freeze_panes = "A3"
last = rows(ws, GAPS, heights=48)
for rr in range(3, last + 1):
    ws.cell(rr, 1).font = bodyb
    ws.cell(rr, 2).alignment = ctr
    v = ws.cell(rr, 2).value
    fill = CRITS if isinstance(v, str) and "WS 2.0" in v else WARNS
    ws.cell(rr, 2).fill = PatternFill("solid", fgColor=fill)
    ws.cell(rr, 4).alignment = ctr
    ws.cell(rr, 4).font = mut
r = last + 2
ws.cell(r, 1, "Why this tab exists").font = bodyb
ws.cell(r, 2, "A comparison with no losses in it is marketing. Six of these are places WS 2.0 is simply better today, "
              "two are our own bugs reproduced on 9 Aug, and one is a conflict between chat-first and the PRD's own "
              "'ambient AI, not a chatbot' rule that needs a decision rather than a defence.").font = mut
ws.cell(r, 2).alignment = wrap
ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
ws.row_dimensions[r].height = 44

# ============================================================ 6 · SUMMARY
ws = wb.create_sheet("6 · Summary")
band(ws, 9, "SUMMARY   ·   every number here is a formula over tab 1, not a typed count")
for i, w in enumerate([4, 26, 13, 13, 13, 13, 13, 13, 13], 1):
    ws.column_dimensions[get_column_letter(i)].width = w

UCS = "'1 · Use cases'"
A = "%s!$B$3:$B$%d" % (UCS, UC_LAST)   # actor
S = "%s!$C$3:$C$%d" % (UCS, UC_LAST)   # stage
V = "%s!$J$3:$J$%d" % (UCS, UC_LAST)   # verdict
B = "%s!$K$3:$K$%d" % (UCS, UC_LAST)   # built

ACTORS = ["Client", "Expert", "SWAT", "WS Admin", "Operator L0"]
VERDICTS = ["Better · new", "Better", "Parity", "WS 2.0 better", "Gap on both", "Out of scope"]
STAGES = sorted(set(u[2] for u in UC))
BUILTS = ["Yes", "Partial", "Simulated", "No"]


def grid(r0, title, row_labels, row_range, col_labels, col_range, note=None):
    """A COUNTIFS matrix: row_labels down the side, col_labels across, totals both ways."""
    ws.cell(r0, 2, title).font = Font(name=F, size=11, bold=True, color=NAVY)
    r0 += 1
    hr = r0
    ws.cell(hr, 2, "").fill = PatternFill("solid", fgColor=NAVY)
    ws.cell(hr, 2).border = bd
    for i, cl in enumerate(col_labels):
        c = ws.cell(hr, 3 + i, cl)
        c.font = hdr; c.fill = PatternFill("solid", fgColor=NAVY)
        c.border = bd; c.alignment = ctr
    tot = ws.cell(hr, 3 + len(col_labels), "Total")
    tot.font = hdr; tot.fill = PatternFill("solid", fgColor=NAVY)
    tot.border = bd; tot.alignment = ctr
    ws.row_dimensions[hr] = ws.row_dimensions[hr]
    ws.row_dimensions[hr].height = 30
    for j, rl in enumerate(row_labels):
        rr = hr + 1 + j
        c = ws.cell(rr, 2, rl)
        c.font = bodyb; c.fill = PatternFill("solid", fgColor=SOFT)
        c.border = bd; c.alignment = Alignment(wrap_text=True, vertical="center")
        for i, cl in enumerate(col_labels):
            cc = ws.cell(rr, 3 + i,
                         '=COUNTIFS(%s,$B%d,%s,%s$%d)' % (row_range, rr, col_range, get_column_letter(3 + i), hr))
            cc.font = body; cc.border = bd; cc.alignment = ctr
        e = get_column_letter(3 + len(col_labels) - 1)
        t = ws.cell(rr, 3 + len(col_labels), '=SUM(C%d:%s%d)' % (rr, e, rr))
        t.font = bodyb; t.border = bd; t.alignment = ctr
        t.fill = PatternFill("solid", fgColor=GREY)
    fr = hr + 1
    lr = hr + len(row_labels)
    rr = lr + 1
    c = ws.cell(rr, 2, "Total")
    c.font = bodyb; c.fill = PatternFill("solid", fgColor=GREY); c.border = bd; c.alignment = ctr
    for i in range(len(col_labels) + 1):
        L = get_column_letter(3 + i)
        t = ws.cell(rr, 3 + i, '=SUM(%s%d:%s%d)' % (L, fr, L, lr))
        t.font = bodyb; t.border = bd; t.alignment = ctr
        t.fill = PatternFill("solid", fgColor=GREY)
    if note:
        ws.cell(rr + 1, 2, note).font = mut
        ws.cell(rr + 1, 2).alignment = wrap
        return rr + 3
    return rr + 2


r = 3
r = grid(r, "Verdict by actor", ACTORS, A, VERDICTS, V,
         "Green verdicts are ours to defend; 'WS 2.0 better' and 'Gap on both' are on tab 5.")
r = grid(r, "Build state by actor", ACTORS, A, BUILTS, B,
         "'Simulated' means the path exists in the prototype but is stubbed. 'No' rows are mostly the tab 5 gaps.")
r = grid(r, "Verdict by PRD stage", STAGES, S, VERDICTS, V,
         "Stages are the PRD's own lifecycle (docs/tenant-zero/spec.md, E1-E15). 'Cross' is anything that is not stage-bound.")

# headline counts
ws.cell(r, 2, "Headline").font = Font(name=F, size=11, bold=True, color=NAVY)
r += 1
HEAD = [
 ("Use cases in the project", '=COUNTA(%s!$A$3:$A$%d)' % (UCS, UC_LAST)),
 ("Built in a prototype today", '=COUNTIF(%s,"Yes")' % B),
 ("Where chat-first wins", '=COUNTIF(%s,"Better · new")+COUNTIF(%s,"Better")' % (V, V)),
 ("Of which have no WS 2.0 equivalent at all", '=COUNTIF(%s,"Better · new")' % V),
 ("Where WS 2.0 wins", '=COUNTIF(%s,"WS 2.0 better")' % V),
 ("Where neither product serves it", '=COUNTIF(%s,"Gap on both")' % V),
 ("Win rate, excluding out-of-scope and mutual gaps",
  '=IFERROR((COUNTIF(%s,"Better · new")+COUNTIF(%s,"Better"))/(COUNTA(%s!$A$3:$A$%d)-COUNTIF(%s,"Out of scope")-COUNTIF(%s,"Gap on both")),"")'
  % (V, V, UCS, UC_LAST, V, V)),
 ("Components compared side by side", len(COMP)),
 ("Of those, points WS 2.0 still wins", sum(1 for c in COMP if str(c[6]).strip() not in ("-", ""))),
 ("Screens mapped to B1-B6", len(SCREENS)),
 ("Invariants the UI must honour", len(RULES)),
 ("Gaps stated openly", len(GAPS)),
]
for label, val in HEAD:
    c = ws.cell(r, 2, label)
    c.font = bodyb; c.fill = PatternFill("solid", fgColor=SOFT)
    c.border = bd; c.alignment = Alignment(wrap_text=True, vertical="center")
    v = ws.cell(r, 3, val)
    v.font = bodyb; v.border = bd; v.alignment = ctr
    if "rate" in label:
        v.number_format = "0%"
    ws.row_dimensions[r].height = 22
    r += 1
r += 1
ws.cell(r, 2, "The last five numbers are counts of rows on tabs 2, 3, 4 and 5 as written by the build script; "
              "everything above them is a live COUNTIF over tab 1. Edit a verdict there and this tab moves.").font = mut
ws.cell(r, 2).alignment = wrap
ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8)
ws.row_dimensions[r].height = 30

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "WS3_Master_Spec.xlsx")
wb.save(out)
print("wrote", out, "| use-case rows 3..%d" % UC_LAST)
