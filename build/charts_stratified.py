"""Turn a syndrome's treatment rows into a stratified pathway instead of a list.

The source file renders each syndrome as a flat vertical stack of treatment
nodes, which loses the axis the rows are already stratified along: the
"clinical setting" column, which carries the guideline's own severity / site /
phase distinctions (eg for coccidioidomycosis: primary pulmonary disease,
chronic pulmonary, extrapulmonary dissemination, severe or refractory disease,
mild coccidioidal meningitis, fluconazole-unresponsive CNS disease).

Nothing here is re-worded. Each option box is the row's own drug, dose,
duration and recommendation grade; the columns are the row's own clinical
setting. It is a re-arrangement of existing, source-located content.
"""
from svgkit import TIER, block, elbow, label, line, rect, wrap

W = 1820
X0 = 52
COND = ("#ffffff", "#697770")
STEP = ("#f2f5f3", "#596861")


def priority_class(priority):
    """Same classification the site uses for row shading (see assets/js/core.js)."""
    p = str(priority or "").lower()
    if any(k in p for k in ("avoid", "against", "not recommended", "discourag")):
        return "avoid"
    if "salvage" in p or "rescue" in p:
        return "salvage"
    if (p == "1" or p.startswith("1 ") or p.startswith("1—") or p.startswith("1 —")
            or "preferred" in p or "first-line" in p or "first line" in p
            or "strongly supported" in p):
        return "preferred"
    return "alternative"


LABEL = {"preferred": "PREFERRED", "alternative": "ALTERNATIVE",
         "salvage": "SALVAGE", "avoid": "AVOID"}


def _raw_priority(row):
    """The row's own priority wording, kept whenever it says more than the tier."""
    raw = str(row[0] or "").strip()
    return raw if raw.upper() != LABEL[priority_class(row[0])] else ""


def _option_height(row, w):
    lines = len(wrap(row[2], w - 22, 13.5))
    body = [t for t in (row[3], row[4]) if t and "not specified" not in t.lower()]
    extra = sum(len(wrap(t, w - 22, 11.5)) for t in body)
    raw = 15 * len(wrap(_raw_priority(row), w - 22, 11)) if _raw_priority(row) else 0
    return 30 + lines * 18 + extra * 15 + raw + (20 if row[6] else 0) + 12


def _option(x, y, w, row):
    tier = priority_class(row[0])
    fill, stroke, ink = TIER[tier]
    h = _option_height(row, w)
    out = [rect(x, y, w, h, fill, stroke, rx=10, sw=2.5)]
    ty = y + 20
    out.append(label(x + 11, ty, LABEL[tier], 10, "850", "start", ink))
    if row[1]:
        out.append(label(x + w - 11, ty, row[1], 10, "700", "end", "#5c6a62"))
    ty += 19
    raw = _raw_priority(row)
    if raw:
        for ln in wrap(raw, w - 22, 11):
            out.append(label(x + 11, ty - 3, "來源用語：" + ln, 11, "600", "start", "#5c6a62"))
            ty += 15
    for ln in wrap(row[2], w - 22, 13.5):
        out.append(label(x + 11, ty, ln, 13.5, "800", "start", "#18211d"))
        ty += 18
    for text, prefix in ((row[3], "Dose: "), (row[4], "Duration: ")):
        if not text or "not specified" in text.lower():
            continue
        for i, ln in enumerate(wrap(text, w - 22, 11.5)):
            out.append(label(x + 11, ty + 3, (prefix if i == 0 else "") + ln, 11.5, "400", "start", "#3f4b45"))
            ty += 15
    if row[6]:
        out.append(label(x + 11, ty + 14, "Recommendation / QoE: " + row[6], 11, "750", "start", ink))
    return "".join(out), y + h


def build_svg(org_name, syndrome):
    rows = syndrome["rows"]
    strata = []
    for r in rows:
        if r[5] not in strata:
            strata.append(r[5])
    n = len(strata)
    gap = 12
    cw = (W - 2 * X0 - gap * (n - 1)) / n

    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d __HEIGHT__">' % W,
         '<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>']

    s.append(rect(X0, 28, W - 2 * X0, 100, "#f2f5f3", "#596861", rx=14, sw=3))
    s.append(label(X0 + 24, 66, org_name, 26, "800"))
    s.append(label(X0 + 24, 96, syndrome["title"], 15, "700", fill="#4a5a52"))
    s.append(label(W - X0 - 24, 96, "依 clinical setting 分層", 13, "700", "end", "#66716b"))

    # tier legend
    ly = 146
    s.append(rect(X0, ly, W - 2 * X0, 46, "#ffffff", "#c9d3cd", rx=11, sw=1.5))
    lx = X0 + 16
    for key in ("preferred", "alternative", "salvage", "avoid"):
        fill, stroke, ink = TIER[key]
        s.append(rect(lx, ly + 13, 20, 20, fill, stroke, rx=5, sw=2))
        s.append(label(lx + 27, ly + 28, LABEL[key], 12, "800", fill=ink))
        lx += 27 + len(LABEL[key]) * 8 + 30
    s.append(label(W - X0 - 16, ly + 28, "底色 = 治療建議層級；欄位 = 來源表格的 clinical setting 欄",
                   11.5, "700", "end", "#66716b"))

    # entry
    ey, eh = 212, 54
    s.append(rect(W / 2 - 320, ey, 640, eh, STEP[0], STEP[1], rx=11, sw=2.5))
    s.append(block(W / 2 - 320, ey + 32, 640,
                   "確立診斷後，先判斷屬於哪一個 clinical setting", 15, "800", "middle", "#2c3a33")[0])

    # strata columns
    cy = ey + eh + 48
    bus = cy - 24
    s.append(line(W / 2, ey + eh, W / 2, bus))
    bottoms = []
    for i, st in enumerate(strata):
        cx = X0 + i * (cw + gap)
        lines = wrap(st, cw - 20, 13)
        h = max(50, len(lines) * 17 + 24)
        s.append(rect(cx, cy, cw, h, COND[0], COND[1], rx=10, sw=2.5))
        ty = cy + (h - len(lines) * 17) / 2 + 13
        for ln in lines:
            s.append(label(cx + cw / 2, ty, ln, 13, "800", "middle", "#2c3a33"))
            ty += 17
        s.append(elbow(W / 2, bus, cx + cw / 2, cy, bus))

        oy = cy + h + 22
        s.append(line(cx + cw / 2, cy + h, cx + cw / 2, oy))
        for r in [r for r in rows if r[5] == st]:
            svg, oy = _option(cx, oy, cw, r)
            s.append(svg)
            oy += 9
        bottoms.append(oy - 9)

    # footnote
    ny = max(bottoms) + 36
    notes = [
        "欄位（白框）直接取自來源表格的 clinical setting 欄，不是重新歸納的分類；每張卡片的藥物、劑量、療程與 "
        "recommendation/QoE 皆為該列原文。逐列 exact locator 請在 Audit view 查看。",
        "底色為治療建議層級：綠=Preferred、黃=Alternative、藍=Salvage、紅=Avoid。",
    ]
    rendered, ty = [], ny + 28
    for nt in notes:
        t, dy = block(X0 + 20, ty, W - 2 * X0 - 40, nt, 12.5, "400", "start", "#4a5a52", lh=17, pad=0)
        rendered.append(t)
        ty += dy + 9
    s.append(rect(X0, ny, W - 2 * X0, ty - ny - 9 + 20, "#f7f9f8", "#c9d3cd", rx=13, sw=2))
    s.extend(rendered)

    height = int(ty - 9 + 20 + 28)
    s.append("</svg>")
    return "".join(s).replace("__HEIGHT__", str(height), 1)


def chart(org, syndrome, original):
    """Build a replacement chart, inheriting the original's provenance fields."""
    return {
        "title": syndrome["title"],
        "source": original.get("source", "See row-level exact source locators"),
        "kind": "GUIDELINE-DERIVED SUMMARY SVG — STRATIFIED BY THE SOURCE'S OWN CLINICAL-SETTING COLUMN",
        "disclaimer": ("Same treatment rows as the table on this page, arranged by the clinical "
                       "setting each row already carries (severity, site or phase) instead of a "
                       "single flat list. Wording, doses, durations and grades are unchanged; use "
                       "the cited original Figure/Table/text for definitive guidance."),
        "svg": build_svg(org["name"], syndrome),
        "visual_type": "guideline-derived-summary",
        "visual_fidelity": "summary-not-source-faithful-redraw",
        "source_has_original_figure": original.get("source_has_original_figure", False),
        "source_figure": original.get("source_figure", ""),
    }


def applies_to(syndrome):
    """Only worth redrawing when the rows really do span more than one setting."""
    seen = []
    for r in syndrome["rows"]:
        if r[5] not in seen:
            seen.append(r[5])
    return len(seen) >= 2
