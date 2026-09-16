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
from svgkit import SVG_OPEN, TIER, block, elbow, label, line, rect, wrap

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


# Type scale. These charts are read on phones at the chart's own scale, so the
# smallest line has to survive that — 11.5px was legible on a desktop canvas
# and too small in the hand.
FS_TIER = 11.5      # PREFERRED / ALTERNATIVE …
FS_PHASE = 11.5     # the phase shown at the card's right edge
FS_RAW = 12         # the row's own priority wording
FS_DRUG = 14.5      # drug / regimen
FS_BODY = 12.5      # dose and duration
FS_GRADE = 12       # recommendation / QoE
FS_STRATUM = 14     # the clinical-setting label

LH_RAW, LH_DRUG, LH_BODY, LH_STRATUM = 16, 19, 16, 19


def _option_height(row, w):
    lines = len(wrap(row[2], w - 22, FS_DRUG))
    body = [t for t in (row[3], row[4]) if t and "not specified" not in t.lower()]
    extra = sum(len(wrap(t, w - 22, FS_BODY)) for t in body)
    raw = LH_RAW * len(wrap(_raw_priority(row), w - 22, FS_RAW)) if _raw_priority(row) else 0
    return 32 + lines * LH_DRUG + extra * LH_BODY + raw + (22 if row[6] else 0) + 12


def _option(x, y, w, row):
    tier = priority_class(row[0])
    fill, stroke, ink = TIER[tier]
    h = _option_height(row, w)
    out = [rect(x, y, w, h, fill, stroke, rx=10, sw=2.5)]
    ty = y + 21
    out.append(label(x + 11, ty, LABEL[tier], FS_TIER, "850", "start", ink))
    if row[1]:
        out.append(label(x + w - 11, ty, row[1], FS_PHASE, "700", "end", "#5c6a62"))
    ty += 20
    raw = _raw_priority(row)
    if raw:
        for ln in wrap(raw, w - 22, FS_RAW):
            out.append(label(x + 11, ty - 3, "來源用語：" + ln, FS_RAW, "600", "start", "#5c6a62"))
            ty += LH_RAW
    for ln in wrap(row[2], w - 22, FS_DRUG):
        out.append(label(x + 11, ty, ln, FS_DRUG, "800", "start", "#18211d"))
        ty += LH_DRUG
    for text, prefix in ((row[3], "Dose: "), (row[4], "Duration: ")):
        if not text or "not specified" in text.lower():
            continue
        for i, ln in enumerate(wrap(text, w - 22, FS_BODY)):
            out.append(label(x + 11, ty + 3, (prefix if i == 0 else "") + ln, FS_BODY, "400", "start", "#3f4b45"))
            ty += LH_BODY
    if row[6]:
        out.append(label(x + 11, ty + 15, "Recommendation / QoE: " + row[6], FS_GRADE, "750", "start", ink))
    return "".join(out), y + h


MAX_COLUMNS = 4          # beyond this, columns get too narrow to read
BAND_LABEL_W = 300
OPTION_MIN_W = 330


def _header(org_name, syndrome, subtitle):
    s = [rect(X0, 28, W - 2 * X0, 100, "#f2f5f3", "#596861", rx=14, sw=3),
         label(X0 + 24, 66, org_name, 26, "800"),
         label(X0 + 24, 96, syndrome["title"], 15, "700", fill="#4a5a52"),
         label(W - X0 - 24, 96, subtitle, 13, "700", "end", "#66716b")]
    ly = 146
    s.append(rect(X0, ly, W - 2 * X0, 46, "#ffffff", "#c9d3cd", rx=11, sw=1.5))
    lx = X0 + 16
    for key in ("preferred", "alternative", "salvage", "avoid"):
        fill, stroke, ink = TIER[key]
        s.append(rect(lx, ly + 13, 20, 20, fill, stroke, rx=5, sw=2))
        s.append(label(lx + 27, ly + 28, LABEL[key], 12, "800", fill=ink))
        lx += 27 + len(LABEL[key]) * 8 + 30
    s.append(label(W - X0 - 16, ly + 28,
                   "底色 = 建議層級；分層 = 來源表格 clinical setting 欄；逐列 locator 見 Audit view",
                   11.5, "700", "end", "#66716b"))
    return "".join(s)


def _footnote(s, ny):
    """Nothing to add below the chart — the legend row already carries the
    provenance line. Just leave a bottom margin."""
    return int(ny + 20)


def _build_bands(org_name, syndrome, strata, rows):
    """One full-width band per stratum: label on the left, options to the right.

    Used when there are too many strata for readable columns — Aspergillus
    chronic pulmonary aspergillosis alone has nine.
    """
    s = [SVG_OPEN % (W, "__HEIGHT__"),
         '<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>',
         _header(org_name, syndrome, "依 clinical setting 分層（%d 層）" % len(strata))]

    ey, eh = 212, 54
    s.append(rect(X0, ey, 640, eh, STEP[0], STEP[1], rx=11, sw=2.5))
    s.append(block(X0, ey + 32, 640, "確立診斷後，先判斷屬於哪一個 clinical setting",
                   15, "800", "middle", "#2c3a33")[0])

    spine = X0 + 26
    ox = X0 + 30 + BAND_LABEL_W + 18
    avail = W - X0 - ox
    y = ey + eh + 30
    centres = []
    for st in strata:
        opts = [r for r in rows if r[5] == st]
        per_row = max(1, int(avail // OPTION_MIN_W))
        # A band with fewer options than fit gets wider cards rather than a
        # half-empty row, but not so wide that the bands look ragged.
        used = min(len(opts), per_row)
        ow = min((avail - (used - 1) * 12) / used, OPTION_MIN_W * 2)
        per_row = used

        lab_lines = wrap(st, BAND_LABEL_W - 24, FS_STRATUM)
        lab_h = max(54, len(lab_lines) * LH_STRATUM + 26)

        # lay the options out in a wrapped grid, tracking each grid row's height
        oy, row_h, placed = y, 0, []
        for i, r in enumerate(opts):
            col = i % per_row
            if col == 0 and i:
                oy += row_h + 9
                row_h = 0
            placed.append((X0 + 30 + BAND_LABEL_W + 18 + col * (ow + 12), oy, r))
            row_h = max(row_h, _option_height(r, ow))
        band_h = max(lab_h, (oy + row_h) - y)

        s.append(rect(X0 + 30, y, BAND_LABEL_W, band_h, COND[0], COND[1], rx=10, sw=2.5))
        ty = y + (band_h - len(lab_lines) * LH_STRATUM) / 2 + FS_STRATUM
        for ln in lab_lines:
            s.append(label(X0 + 30 + BAND_LABEL_W / 2, ty, ln, FS_STRATUM, "800", "middle", "#2c3a33"))
            ty += LH_STRATUM
        for ox_, oy_, r in placed:
            s.append(_option(ox_, oy_, ow, r)[0])

        cy = y + band_h / 2
        centres.append(cy)
        s.append(line(spine, cy, X0 + 30, cy))
        y += band_h + 16

    s.append(line(spine, ey + eh, spine, centres[-1]))
    height = _footnote(s, y + 20)
    s.append("</svg>")
    return "".join(s).replace("__HEIGHT__", str(height), 1)


def build_svg(org_name, syndrome):
    rows = syndrome["rows"]
    strata = []
    for r in rows:
        if r[5] not in strata:
            strata.append(r[5])
    if len(strata) > MAX_COLUMNS:
        return _build_bands(org_name, syndrome, strata, rows)
    n = len(strata)
    gap = 12
    cw = (W - 2 * X0 - gap * (n - 1)) / n

    s = [SVG_OPEN % (W, "__HEIGHT__"),
         '<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>']

    s.append(_header(org_name, syndrome, "依 clinical setting 分層（%d 層）" % n))

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
        lines = wrap(st, cw - 20, FS_STRATUM)
        h = max(52, len(lines) * LH_STRATUM + 24)
        s.append(rect(cx, cy, cw, h, COND[0], COND[1], rx=10, sw=2.5))
        ty = cy + (h - len(lines) * LH_STRATUM) / 2 + FS_STRATUM
        for ln in lines:
            s.append(label(cx + cw / 2, ty, ln, FS_STRATUM, "800", "middle", "#2c3a33"))
            ty += LH_STRATUM
        s.append(elbow(W / 2, bus, cx + cw / 2, cy, bus))

        oy = cy + h + 22
        s.append(line(cx + cw / 2, cy + h, cx + cw / 2, oy))
        for r in [r for r in rows if r[5] == st]:
            svg, oy = _option(cx, oy, cw, r)
            s.append(svg)
            oy += 9
        bottoms.append(oy - 9)

    height = _footnote(s, max(bottoms) + 36)
    s.append("</svg>")
    return "".join(s).replace("__HEIGHT__", str(height), 1)


def chart(org, syndrome, original):
    """Build a replacement chart, inheriting the original's provenance fields."""
    return {
        "title": syndrome["title"],
        "source": original.get("source", "See row-level exact source locators"),
        "kind": "GUIDELINE-DERIVED SUMMARY SVG — STRATIFIED BY THE SOURCE'S OWN CLINICAL-SETTING COLUMN",
        "disclaimer": "重建摘要圖：正式分支、措辭與分級以所引用的原始 Figure / Table / text 為準。",
        "rebuilt": "stratified",
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
