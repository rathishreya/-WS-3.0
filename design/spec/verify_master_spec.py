# Verifies WS3_Master_Spec.xlsx after recalculation: every computed cell on the
# summary tab is compared against the same count derived independently in Python
# from the source data. A green recalc only proves the formulas evaluate; this
# proves they evaluate to the right thing.
import sys
from collections import Counter
from openpyxl import load_workbook

from build_master_spec_part1 import UC
from build_master_spec_part2 import COMP, SCREENS, RULES, GAPS

PATH = sys.argv[1] if len(sys.argv) > 1 else "WS3_Master_Spec.xlsx"
vals = load_workbook(PATH, data_only=True)
forms = load_workbook(PATH, data_only=False)
ws = vals["6 · Summary"]
wf = forms["6 · Summary"]

by_actor = Counter(u[1] for u in UC)
by_verdict = Counter(u[9] for u in UC)
pairs_av = Counter((u[1], u[9]) for u in UC)
pairs_ab = Counter((u[1], u[10]) for u in UC)
pairs_sv = Counter((u[2], u[9]) for u in UC)

bad = []
checked = 0

# walk the three matrices: a header row is any row whose column B is blank but
# whose column C carries a label, with row labels beneath it in column B.
for r in range(1, ws.max_row + 1):
    label = ws.cell(r, 2).value
    if label != "" and label is not None:
        continue
    if not ws.cell(r, 3).value:
        continue
    cols = []
    c = 3
    while ws.cell(r, c).value not in (None, "", "Total"):
        cols.append(ws.cell(r, c).value)
        c += 1
    rr = r + 1
    while ws.cell(rr, 2).value not in (None, "", "Total"):
        rowlab = ws.cell(rr, 2).value
        for i, col in enumerate(cols):
            got = ws.cell(rr, 3 + i).value or 0
            if rowlab in by_actor:
                want = pairs_av.get((rowlab, col), 0) if col in by_verdict else pairs_ab.get((rowlab, col), 0)
            else:
                want = pairs_sv.get((rowlab, col), 0)
            checked += 1
            if got != want:
                bad.append("%s!%s%d  %s x %s: sheet=%s python=%s"
                           % (ws.title, chr(66 + i + 1), rr, rowlab, col, got, want))
        rr += 1

# headline block
HEAD = {
 "Use cases in the project": len(UC),
 "Built in a prototype today": sum(1 for u in UC if u[10] == "Yes"),
 "Where chat-first wins": by_verdict["Better · new"] + by_verdict["Better"],
 "Of which have no WS 2.0 equivalent at all": by_verdict["Better · new"],
 "Where WS 2.0 wins": by_verdict["WS 2.0 better"],
 "Where neither product serves it": by_verdict["Gap on both"],
 "Components compared side by side": len(COMP),
 "Of those, points WS 2.0 still wins": sum(1 for c in COMP if str(c[6]).strip() not in ("-", "")),
 "Screens mapped to B1-B6": len(SCREENS),
 "Invariants the UI must honour": len(RULES),
 "Gaps stated openly": len(GAPS),
}
for r in range(1, ws.max_row + 1):
    lab = ws.cell(r, 2).value
    if lab in HEAD:
        got = ws.cell(r, 3).value
        checked += 1
        if got != HEAD[lab]:
            bad.append("headline '%s': sheet=%s python=%s" % (lab, got, HEAD[lab]))

# every formula cell must have come back with a value
empty = 0
for name in forms.sheetnames:
    a, b = forms[name], vals[name]
    for row in a.iter_rows():
        for cell in row:
            if isinstance(cell.value, str) and cell.value.startswith("="):
                if b[cell.coordinate].value is None:
                    empty += 1
                    bad.append("%s!%s has a formula but no computed value" % (name, cell.coordinate))

print("cells checked:", checked, "| formula cells with no value:", empty)
if bad:
    print("MISMATCHES (%d):" % len(bad))
    for b_ in bad[:40]:
        print("  ", b_)
    sys.exit(1)
print("OK — every computed cell matches the Python-derived count.")
