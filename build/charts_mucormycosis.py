"""Cornely 2019 Figure 5 rebuilt as the decision pathway it actually is.

The figure has three panels, one per drug-availability scenario, and each panel
is a pathway: an emergency framing, surgical debridement alongside immediate
treatment initiation, a first-line row whose columns are conditional on brain
involvement / SOT / renal compromise, a response assessment, and separate
progressive-disease and toxicity branches.

Recommendation strengths below were read off the source figure's own fill
colours rather than inferred from the wording:

    #ddedde green  strongly recommended     -> preferred   (site green)
    #fff9d7 yellow moderately recommended   -> alternative (site amber)
    #feebed rose   marginally recommended   -> salvage     (site blue)
    #f7dfdf salmon recommended against      -> avoid       (site red)
"""
from svgkit import TIER, block, esc, elbow, label, line, rect, wrap

W = 1820
X0 = 52

# guideline strength -> the site's four-tier palette
STRENGTH = {
    "strong": ("preferred", "Strongly recommended"),
    "moderate": ("alternative", "Moderately recommended"),
    "marginal": ("salvage", "Marginally recommended"),
    "against": ("avoid", "Recommended against"),
}

COND = ("#ffffff", "#697770")      # "If brain involvement" etc — a condition, not a recommendation
STEP = ("#f2f5f3", "#596861")      # pathway steps — deliberately neutral, never a tier colour


def _stack_height(items, w, pad=12):
    """Height a column of tier-coloured option boxes will need."""
    h = 0
    for text, _ in items:
        lines = wrap(text, w - 22, 12.5)
        h += max(46, len(lines) * 17 + 20) + 7
    return h - 7 + pad * 0


def _stack(x, y, w, items):
    """Draw a column of option boxes, each shaded by its recommendation strength."""
    out, cy = [], y
    for text, strength in items:
        tier, _ = STRENGTH[strength]
        fill, stroke, ink = TIER[tier]
        lines = wrap(text, w - 22, 12.5)
        h = max(46, len(lines) * 17 + 20)
        out.append(rect(x, cy, w, h, fill, stroke, rx=9, sw=2))
        ty = cy + (h - len(lines) * 17) / 2 + 12
        for ln in lines:
            out.append(label(x + 11, ty, ln, 12.5, "600", "start", ink))
            ty += 17
        cy += h + 7
    return "".join(out), cy - 7


def _column(x, y, w, cond, items):
    """One first-line column: an optional white condition box, then the options."""
    out = []
    cy = y
    if cond:
        lines = wrap(cond, w - 22, 12.5)
        h = max(38, len(lines) * 16 + 18)
        out.append(rect(x, cy, w, h, COND[0], COND[1], rx=9, sw=2))
        ty = cy + (h - len(lines) * 16) / 2 + 12
        for ln in lines:
            out.append(label(x + 11, ty, ln, 12.5, "750", "start", "#2c3a33"))
            ty += 16
        out.append(line(x + w / 2, cy + h, x + w / 2, cy + h + 14))
        cy += h + 14
    s, bottom = _stack(x, cy, w, items)
    out.append(s)
    return "".join(out), bottom


def build_svg(panel):
    cols = panel["first_line"]
    n = len(cols)
    gap = 12
    cw = (W - 2 * X0 - gap * (n - 1)) / n

    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d __HEIGHT__">' % W,
         '<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>']

    # header
    s.append(rect(X0, 28, W - 2 * X0, 100, "#f2f5f3", "#596861", rx=14, sw=3))
    s.append(label(X0 + 24, 66, "Mucormycosis — treatment pathway (%s)" % panel["panel"], 26, "800"))
    s.append(label(X0 + 24, 96, panel["subtitle"], 14.5, "700", fill="#4a5a52"))
    s.append(label(W - X0 - 24, 96, "Cornely 2019 · Figure 5", 13, "700", "end", "#66716b"))

    # legend — the guideline's own four strengths
    ly = 146
    s.append(rect(X0, ly, W - 2 * X0, 46, "#ffffff", "#c9d3cd", rx=11, sw=1.5))
    lx = X0 + 16
    for key in ("strong", "moderate", "marginal", "against"):
        tier, text = STRENGTH[key]
        fill, stroke, ink = TIER[tier]
        s.append(rect(lx, ly + 13, 20, 20, fill, stroke, rx=5, sw=2))
        s.append(label(lx + 27, ly + 28, text, 12.5, "750", fill="#3f4b45"))
        lx += 27 + len(text) * 7.2 + 34
    s.append(label(W - X0 - 16, ly + 28, "顏色 = guideline 自身的推薦強度（取自原圖填色）", 11.5,
                   "700", "end", "#66716b"))

    # emergency + surgery
    ey, eh = 212, 50
    s.append(rect(X0 + 240, ey, W - 2 * X0 - 480, eh, TIER["preferred"][0], TIER["preferred"][1], rx=11, sw=2.5))
    s.append(block(X0 + 240, ey + 30, W - 2 * X0 - 480,
                   "Suspected and confirmed mucormycosis are emergencies and require rapid action",
                   15, "800", "middle", TIER["preferred"][2])[0])

    sy, sh = 292, 92
    s.append(line(W / 2, ey + eh, W / 2, sy))
    s.append(rect(X0 + 240, sy, W - 2 * X0 - 480, sh, TIER["preferred"][0], TIER["preferred"][1], rx=11, sw=2.5))
    s.append(block(X0 + 240, sy + 26, W - 2 * X0 - 480,
                   "Surgical debridement with clean margins — for three purposes: (1) disease control, "
                   "(2) histopathology, (3) microbiological diagnostics",
                   13.5, "800", "middle", TIER["preferred"][2])[0])
    s.append(block(X0 + 240, sy + 68, W - 2 * X0 - 480,
                   "PLUS immediate treatment initiation", 13.5, "800", "middle", TIER["preferred"][2])[0])

    # first-line row
    fy = sy + sh + 46
    bus = fy - 24
    s.append(line(W / 2, sy + sh, W / 2, bus))
    bottom, col_bottoms = fy, []
    for i, col in enumerate(cols):
        cx = X0 + i * (cw + gap)
        svg, b = _column(cx, fy, cw, col.get("cond"), col["items"])
        s.append(svg)
        s.append(elbow(W / 2, bus, cx + cw / 2, fy, bus))
        col_bottoms.append(b)
        bottom = max(bottom, b)

    # response assessment
    ry, rh = bottom + 72, 62
    s.append(rect(W / 2 - 190, ry, 380, rh, STEP[0], STEP[1], rx=11, sw=2.5))
    s.append(block(W / 2 - 190, ry + 26, 380, "Response assessment", 15, "800", "middle", "#1d2a33")[0])
    s.append(block(W / 2 - 190, ry + 46, 380, "eg, weekly imaging", 12, "600", "middle", "#5a6b76")[0])
    join = bottom + 26
    for i, b in enumerate(col_bottoms):
        cx = X0 + i * (cw + gap)
        s.append(line(cx + cw / 2, b, cx + cw / 2, join))
    s.append(line(X0 + cw / 2, join, X0 + (len(cols) - 1) * (cw + gap) + cw / 2, join))
    s.append(line(W / 2, join, W / 2, ry))

    # outcome branches
    oy = ry + rh + 46
    obus = oy - 24
    branches = panel["branches"]
    bw = (W - 2 * X0 - gap * (len(branches) - 1)) / len(branches)
    obottom = oy
    for i, br in enumerate(branches):
        bx = X0 + i * (bw + gap)
        s.append(rect(bx, oy, bw, 46, COND[0], COND[1], rx=10, sw=2.5))
        s.append(block(bx, oy + 29, bw, br["title"], 14.5, "800", "middle", "#2c3a33")[0])
        s.append(elbow(W / 2, obus, bx + bw / 2, oy, obus))

        inner = br["columns"]
        iw = (bw - gap * (len(inner) - 1)) / len(inner)
        ibus = oy + 46 + 22
        for j, items in enumerate(inner):
            ix = bx + j * (iw + gap)
            svg, b = _stack(ix, oy + 46 + 44, iw, items)
            s.append(svg)
            s.append(elbow(bx + bw / 2, oy + 46, ix + iw / 2, oy + 46 + 44, ibus))
            obottom = max(obottom, b)
    s.append(line(W / 2, ry + rh, W / 2, obus))

    # footnote
    ny = obottom + 40
    notes = panel["notes"] + [
        "節點底色為 guideline 原圖的推薦強度，對應本站色階：綠=Strongly / 黃=Moderately / 藍=Marginally / 紅=Recommended against。"
        "白色方塊是分支條件，不是推薦等級。",
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


ISA_IV = "Isavuconazole IV 3 × 200 mg day 1–2, then 1 × 200 mg per day from day 3"
PCZ_IV = "Posaconazole IV 2 × 300 mg day 1, then 1 × 300 mg per day from day 2"
ISA_PCZ_IV = ISA_IV + "   ·   " + PCZ_IV
PCZ_SUSP = "Posaconazole oral suspension 4 × 200 mg per day"
AZOLE_SALVAGE = (ISA_IV + "   ·   or Posaconazole IV or DR tablets 2 × 300 mg day 1, "
                 "then 1 × 300 mg per day from day 2")
ABLC_OR_LAMB = "Amphotericin B lipid complex or liposomal amphotericin B 5 mg/kg per day from day 1"
NO_SLOW = "Avoid slow escalation of doses"

PANELS = [
    {
        "panel": "A — all treatment modalities and antifungal drugs available",
        "subtitle": "外科清創與立即開始抗黴菌治療並行；分支條件為腦部侵犯、SOT、腎功能不全，之後依反應評估決定後續。",
        "figure": "Figure 5A (PDF p7)",
        "first_line": [
            {"items": [(NO_SLOW, "against"),
                       ("Liposomal amphotericin B 5–10 mg/kg per day from day 1", "strong")]},
            {"cond": "If brain involvement",
             "items": [(NO_SLOW, "against"),
                       ("Liposomal amphotericin B 10 mg/kg per day from day 1", "strong")]},
            {"cond": "If SOT",
             "items": [(NO_SLOW, "against"),
                       ("Liposomal amphotericin B or amphotericin B lipid complex 10 mg/kg per day from day 1", "strong")]},
            {"cond": "If pre-existing renal compromise", "items": [(ISA_PCZ_IV, "strong")]},
            {"items": [(ISA_PCZ_IV, "moderate")]},
            {"items": [(PCZ_SUSP, "marginal")]},
            {"items": [("Liposomal amphotericin B < 5 mg/kg per day", "marginal")]},
            {"items": [("Avoid amphotericin B deoxycholate — any dose", "against")]},
        ],
        "branches": [
            {"title": "Stable disease or partial response", "columns": [
                [("Continuation of first-line treatment, or change to oral treatment: Isavuconazole PO "
                  "3 × 200 mg day 1–2, then 1 × 200 mg per day from day 3; or Posaconazole DR tablets "
                  "2 × 300 mg day 1, then 1 × 300 mg per day from day 2", "moderate")]]},
            {"title": "Progressive disease", "columns": [
                [(AZOLE_SALVAGE, "strong"), (PCZ_SUSP, "marginal")],
                [("Liposomal amphotericin B 10 mg/kg per day from day 1", "strong"),
                 (ABLC_OR_LAMB, "moderate"),
                 ("Combination with posaconazole", "marginal")]]},
            {"title": "Toxicity", "columns": [
                [(AZOLE_SALVAGE, "strong"), (PCZ_SUSP, "marginal")],
                [(ABLC_OR_LAMB, "moderate")]]},
        ],
        "notes": [
            "「Avoid slow escalation of doses」在原圖是 recommended against 的節點：意思是不要慢慢加量，第 1 天就給足劑量。",
            "腦部侵犯與 SOT 兩個分支都把 liposomal amphotericin B 提高到 10 mg/kg per day（SOT 可用 L-AmB 或 ABLC）。",
        ],
    },
    {
        "panel": "B — amphotericin B lipid formulations are not available",
        "subtitle": "沒有 lipid formulation 時改以 IV azole 為主；amphotericin B deoxycholate 任何劑量都是 recommended against。",
        "figure": "Figure 5B (PDF p8)",
        "first_line": [
            {"cond": "If pre-existing renal compromise", "items": [(ISA_PCZ_IV, "strong")]},
            {"items": [(ISA_PCZ_IV, "moderate")]},
            {"items": [(PCZ_SUSP, "marginal")]},
            {"items": [("Avoid amphotericin B deoxycholate — any dose", "against")]},
        ],
        "branches": [
            {"title": "Stable disease or partial response", "columns": [
                [("Continuation of first-line treatment, or change to oral treatment: Isavuconazole PO "
                  "3 × 200 mg day 1–2, then 1 × 200 mg per day from day 3; or Posaconazole DR tablets "
                  "2 × 300 mg day 1, then 1 × 300 mg per day from day 2", "moderate")]]},
            {"title": "Progressive disease", "columns": [
                [("Isavuconazole IV or PO 3 × 200 mg day 1–2, then 1 × 200 mg per day from day 3; "
                  "or Posaconazole IV or DR tablets 2 × 300 mg day 1, then 1 × 300 mg per day from day 2", "strong"),
                 (PCZ_SUSP, "marginal")]]},
            {"title": "Toxicity", "columns": [
                [("Isavuconazole IV or PO 3 × 200 mg day 1–2, then 1 × 200 mg per day from day 3; "
                  "or Posaconazole IV or DR tablets 2 × 300 mg day 1, then 1 × 300 mg per day from day 2", "strong"),
                 (PCZ_SUSP, "marginal")]]},
        ],
        "notes": [
            "此情境下 amphotericin B deoxycholate 仍不是替代品——原圖明確列為 recommended against（任何劑量）。",
        ],
    },
    {
        "panel": "C — isavuconazole and posaconazole IV / DR tablets are not available",
        "subtitle": "只剩 polyene 與 posaconazole 口服懸液；原圖在此情境未列出 stable disease 分支。",
        "figure": "Figure 5C (PDF p9)",
        "first_line": [
            {"items": [(NO_SLOW, "against"),
                       ("Liposomal amphotericin B 5–10 mg/kg per day from day 1", "strong")]},
            {"cond": "If brain involvement",
             "items": [(NO_SLOW, "against"),
                       ("Liposomal amphotericin B 10 mg/kg per day from day 1", "strong")]},
            {"cond": "If SOT",
             "items": [(NO_SLOW, "against"),
                       ("Liposomal amphotericin B or amphotericin B lipid complex 10 mg/kg per day from day 1", "strong")]},
            {"items": [(PCZ_SUSP, "marginal")]},
            {"items": [("Liposomal amphotericin B < 5 mg/kg per day", "marginal")]},
            {"items": [("Avoid amphotericin B deoxycholate — any dose", "against")]},
        ],
        "branches": [
            {"title": "Progressive disease", "columns": [
                [(PCZ_SUSP, "marginal")],
                [("Liposomal amphotericin B 10 mg/kg per day from day 1", "strong"),
                 (ABLC_OR_LAMB, "moderate"),
                 ("Combination with posaconazole", "marginal")]]},
            {"title": "Toxicity", "columns": [
                [(PCZ_SUSP, "marginal")],
                [(ABLC_OR_LAMB, "moderate")]]},
        ],
        "notes": [
            "原圖的 C 分頁只畫出 progressive disease 與 toxicity 兩個後續分支，沒有 stable disease 欄；此處照原圖呈現，不自行補上。",
        ],
    },
]

DISCLAIMER = ("Reconstruction of Cornely 2019 Figure 5. Node shading is the guideline's own "
              "recommendation strength, read from the source figure's fill colours. Surgery and "
              "immediate antifungal initiation are a single first step, and the response assessment "
              "loop drives the progressive-disease and toxicity branches — use the original figure "
              "and text for definitive wording.")


def charts():
    out = []
    for p in PANELS:
        out.append({
            "title": "Mucormycosis treatment pathway — %s" % p["panel"],
            "source": "Cornely 2019 Mucormycosis | %s" % p["figure"],
            "kind": "GUIDELINE-DERIVED SUMMARY SVG — REBUILT AS THE SOURCE FIGURE'S DECISION PATHWAY",
            "disclaimer": DISCLAIMER,
            "svg": build_svg(p),
            "visual_type": "guideline-derived-summary",
            "visual_fidelity": "summary-not-source-faithful-redraw",
            "source_has_original_figure": True,
            "source_figure": p["figure"],
        })
    return out
