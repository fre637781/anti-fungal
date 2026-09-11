"""Chang 2024 Figure 1 rebuilt as involvement -> host -> severity.

See build/overrides.py for why this replaces the source file's species-first
opening chart on both Cryptococcus pages.
"""
from svgkit import (BRANCH, PAPER, STRAT, TIER, block, branch_box, elbow, esc,
                    label, line, rect, treatment_box, wrap)

SOURCE = "Chang 2024 Cryptococcosis | Figure 1 | PDF p2 (journal e496)"


# ------------------------------------------------------------------ the chart
# Ten leaves, left to right, in the order Figure 1 presents them.
LEAF_W, LEAF_GAP, GROUP_GAP, X0 = 158, 8, 24, 52
W, H = 1820, 1580


def leaf_x(i):
    """Leaf i, with wider gaps between the four involvement groups."""
    groups_before = sum(1 for boundary in (5, 6, 9) if i >= boundary)
    return X0 + i * (LEAF_W + LEAF_GAP) + groups_before * (GROUP_GAP - LEAF_GAP)


def build_svg(highlight=None):
    s = []
    s.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d __HEIGHT__">' % W)
    s.append('<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>')

    # header
    s.append(rect(X0, 28, W - 2 * X0, 100, "#f2f5f3", "#596861", rx=14, sw=3))
    s.append(label(X0 + 24, 68, "Cryptococcosis — first-line antifungal therapy by involvement, host and severity",
                   27, "800"))
    s.append(label(X0 + 24, 98,
                   "分層順序：involvement（感染部位）→ host（宿主）→ severity（嚴重度）。Species 只是修飾因子，不是第一層分支。",
                   14.5, "700", fill="#4a5a52"))
    s.append(label(W - X0 - 24, 98, "Chang 2024 · Figure 1", 13, "700", "end", "#66716b"))

    # entry
    ex, ew, ey, eh = 610, 600, 152, 58
    s.append(rect(ex, ey, ew, eh, "#ffffff", "#46617a", rx=12, sw=2.5))
    t, dy = block(ex, ey + 25, ew, "Confirmed cryptococcosis — define the syndrome and extent of disease",
                  14.5, "800", "middle", "#1d2a33")
    s.append(t)
    z, _ = block(ex, ey + 25 + dy + 3, ew, "先界定感染部位與播散範圍（CNS 檢查、血液 CrAg、影像）",
                 11.5, "700", "middle", "#5a6b76")
    s.append(z)

    # ---- level 1: involvement -------------------------------------------
    iy, ih = 248, 96
    groups = [
        (0, 5, "CNS cryptococcosis / cryptococcal meningitis", "CNS 侵犯"),
        (5, 1, "Disseminated (non-CNS, non-pulmonary)", "播散性"),
        (6, 3, "Isolated pulmonary cryptococcosis *", "單獨肺部"),
        (9, 1, "Direct skin inoculation", "直接皮膚接種"),
    ]
    bus = iy - 24
    s.append(line(ex + ew / 2, ey + eh, ex + ew / 2, bus))
    for start, span, en, zh in groups:
        gx = leaf_x(start)
        gw = leaf_x(start + span - 1) + LEAF_W - gx
        s.append(branch_box(gx, iy, gw, ih, en, zh, BRANCH, 15))
        s.append(elbow(ex + ew / 2, bus, gx + gw / 2, iy, bus))

    # ---- level 2: host / severity ---------------------------------------
    sy, sh = 378, 96
    strat = [
        (0, 1, "HIV", "PLHIV"),
        (1, 1, "SOT", "實體器官移植"),
        (2, 1, "Non-HIV / non-SOT", "其他宿主"),
        (3, 1, "Non-HIV + C. gattii", "species 修飾"),
        (4, 1, "CNS cryptococcoma", "腦部團塊"),
        (5, 1, "Treat as CNS disease", "cryptococcaemia 同 CNS"),
        (6, 2, "Severe", "多發 / ≥2 cm / 實變 / 空洞 / 多葉 / 低氧"),
        (8, 1, "† Mild (± cryptococcoma)", "無症狀或單一 <2 cm 結節"),
        (9, 1, "Primary cutaneous", "無播散證據"),
    ]
    bus2 = sy - 22
    for start, span, en, zh in strat:
        bx = leaf_x(start)
        bw = leaf_x(start + span - 1) + LEAF_W - bx
        hl = highlight == "gattii" and start == 3
        s.append(branch_box(bx, sy, bw, sh, en, zh, STRAT, 14))
        if hl:
            s.append(rect(bx - 6, sy - 6, bw + 12, sh + 12, "none", "#c58a00", rx=15, sw=3.5,
                          extra='stroke-dasharray="7 5"'))
        # connect from the owning involvement group
        for gstart, gspan, _, _ in groups:
            if gstart <= start < gstart + gspan:
                gx = leaf_x(gstart)
                gw = leaf_x(gstart + gspan - 1) + LEAF_W - gx
                s.append(elbow(gx + gw / 2, iy + ih, bx + bw / 2, sy, bus2))
                break

    # ---- level 3: pulmonary severe qualifier ----------------------------
    qy, qh = 496, 60
    bus3 = qy - 20
    px = leaf_x(6)
    pw = leaf_x(7) + LEAF_W - px
    for i, en in ((6, "Without cryptococcoma"), (7, "With cryptococcoma")):
        bx = leaf_x(i)
        s.append(rect(bx, qy, LEAF_W, qh, "#ffffff", "#697770", rx=10, sw=2))
        t, _ = block(bx, qy + 25, LEAF_W, en, 12.5, "750", "middle", "#2c3a33")
        s.append(t)
        s.append(elbow(px + pw / 2, sy + sh, bx + LEAF_W / 2, qy, bus3))

    # ---- level 4: induction ---------------------------------------------
    ty, th = 590, 172
    ind_x = leaf_x(0)
    ind_w = leaf_x(7) + LEAF_W - ind_x
    s.append(treatment_box(
        ind_x, ty, ind_w, th, "preferred",
        "Induction — polyene-based (all branches above)",
        "(AIIt) ‡ Liposomal amphotericin B 3–4 mg/kg daily + flucytosine 25 mg/kg four times a day — high-income settings", ))
    s.append(block(ind_x, ty + 92, ind_w,
                   "or (AI) § Liposomal amphotericin B 10 mg/kg single dose + flucytosine 25 mg/kg four times a day for 2 weeks + fluconazole 1200 mg daily — low-income settings",
                   13, "400", "middle", "#1c2a24")[0])
    s.append(block(ind_x, ty + 138, ind_w,
                   "‡ Strongly preferred for CNS disease in SOT and non-HIV/non-SOT, disseminated disease and severe pulmonary disease. ‡ and § have not been compared directly. § trialled only in cryptococcal meningitis.",
                   11.5, "400", "middle", "#4d5a53")[0])

    # fluconazole-only branches
    s.append(treatment_box(leaf_x(8), ty, LEAF_W, th, "alternative", "Fluconazole",
                           "400–800 mg daily", "Panel 6 states 400 mg daily"))
    s.append(treatment_box(leaf_x(9), ty, LEAF_W, th, "preferred", "Fluconazole",
                           "400 mg daily", "or until healed"))

    for i in range(10):
        top = qy + qh if i in (6, 7) else sy + sh
        s.append(line(leaf_x(i) + LEAF_W / 2, top, leaf_x(i) + LEAF_W / 2, ty))

    # ---- level 5: duration + grade ---------------------------------------
    dy_, dh = 796, 96
    durations = [
        ("2 weeks", "AI", "preferred"),
        ("≥2 weeks", "AIIt", "preferred"),
        ("≥2 weeks", "AIIt", "preferred"),
        ("4–6 weeks", "BIII", "alternative"),
        ("4–6 weeks", "BIII", "alternative"),
        ("2 weeks", "BIIu", "alternative"),
        ("2 weeks", "AIIu", "preferred"),
        ("4–6 weeks", "BIIu", "alternative"),
        ("¶ 6–12 months", "BIIu", "alternative"),
        ("3–6 months", "AIII", "preferred"),
    ]
    for i, (dur, grade, tier) in enumerate(durations):
        fill, stroke, ink = TIER[tier]
        bx = leaf_x(i)
        s.append(line(bx + LEAF_W / 2, ty + th, bx + LEAF_W / 2, dy_))
        s.append(rect(bx, dy_, LEAF_W, dh, fill, stroke, rx=10, sw=2))
        s.append(block(bx, dy_ + 22, LEAF_W, "Duration", 10.5, "800", "middle", "#5c6a62")[0])
        t, ddy = block(bx, dy_ + 46, LEAF_W, dur, 14.5, "800", "middle", ink)
        s.append(t)
        s.append(block(bx, dy_ + 46 + ddy + 6, LEAF_W, grade, 12.5, "800", "middle", ink)[0])

    # ---- level 6: consolidation / maintenance ----------------------------
    cy, ch = 936, 66
    my, mh = 1032, 86
    s.append(line(ind_x + ind_w / 2, dy_ + dh, ind_x + ind_w / 2, cy))
    s.append(treatment_box(ind_x, cy, ind_w, ch, "preferred", "Consolidation — 8 weeks",
                           "(AI) Fluconazole 400–800 mg daily (800 mg preferred in low-income settings)"))
    s.append(line(ind_x + ind_w / 2, cy + ch, ind_x + ind_w / 2, my))
    s.append(treatment_box(ind_x, my, ind_w, mh, "preferred", "Maintenance — 12 months",
                           "(AIIt) Fluconazole 200 mg daily, or until immune restoration"))
    s.append(block(ind_x, my + 68, ind_w,
                   "(BIIu) In people with HIV, cease after 12 months if aviraemic on ART with CD4 >100 cells per mm³; (AIII) restart if CD4 falls below 100.",
                   11.5, "400", "middle", "#4d5a53")[0])

    # the two fluconazole branches finish with their own course
    for i in (8, 9):
        bx = leaf_x(i)
        s.append(rect(bx, cy, LEAF_W, 54, "#f7f9f8", "#c9d3cd", rx=10, sw=1.5))
        s.append(block(bx, cy + 22, LEAF_W, "No separate consolidation / maintenance phase",
                       10.5, "700", "middle", "#5c6a62")[0])

    # ---- species modifier -------------------------------------------------
    ny, nh = 1152, 108
    s.append(rect(X0, ny, W - 2 * X0, nh, "#fffaf0", "#c58a00", rx=13, sw=2.5))
    s.append(label(X0 + 22, ny + 30, "Species is a modifier — not the first branch　種別只調整療程，不是第一層分支",
                   15.5, "800", fill="#765300"))
    s.append(label(X0 + 22, ny + 58,
                   "C. gattii CNS disease: (AIII) treat the same as C. neoformans CNS infection; (BIII) in non-HIV patients consider extending induction to 4–6 weeks; (AIII) early CSF shunting for obstructive chronic hydrocephalus.  — Panel 13",
                   12.5, "400", fill="#4a4030"))
    s.append(label(X0 + 22, ny + 82,
                   "Non-C. neoformans / non-C. gattii species (eg, Papiliotrema laurentii, Naganishia albida): (CIII) for CNS or disseminated disease, treat the same as C. neoformans CNS infection.  — Panel 15",
                   12.5, "400", fill="#4a4030"))

    # ---- footnotes --------------------------------------------------------
    fy = 1292
    notes = [
        "* Isolated pulmonary cryptococcosis (C. neoformans or C. gattii): mild = asymptomatic or mildly symptomatic, or a solitary small nodule (<2 cm); severe = multiple lesions, large lesions (≥2 cm), lobar consolidation, cavitation, multi-lobar involvement, or hypoxaemia.",
        "† If Cryptococcus spp in a respiratory specimen is judged to be airway colonisation after careful evaluation and no treatment is elected, (AIII) regular follow-up is recommended, especially before future immunosuppression.",
        "¶ A shorter duration (eg, 3 months) can be considered in immunocompetent individuals with mild isolated pulmonary cryptococcosis.",
        "Pulmonary disease with CNS involvement, cryptococcaemia, or a blood cryptococcal antigen titre >1:512 is treated as CNS disease (Panel 6). Cryptococcaemia: (AIIu) treat as CNS disease; all other non-CNS non-pulmonary disseminated disease: (BIIu) treat as CNS disease (Panel 7).",
        "Node colour encodes the recommendation grade: green = A (strongly recommended), amber = B (moderately recommended), blue = C (marginally recommended), red = D (recommended against). Grades and level of evidence are transcribed from the source figure.",
    ]
    rendered, ny2 = [], fy + 30
    for n in notes:
        t, dyy = block(X0 + 20, ny2, W - 2 * X0 - 40, n, 12.5, "400", "start", "#4a5a52", lh=17, pad=0)
        rendered.append(t)
        ny2 += dyy + 9
    s.append(rect(X0, fy, W - 2 * X0, ny2 - fy - 9 + 20, "#f7f9f8", "#c9d3cd", rx=13, sw=2))
    s.extend(rendered)

    height = int(ny2 - 9 + 20 + 28)
    s.append("</svg>")
    return "".join(s).replace("__HEIGHT__", str(height), 1)


def chart(highlight=None):
    return {
        "title": "Cryptococcosis treatment algorithm — involvement → host → severity (Figure 1)",
        "source": SOURCE,
        "kind": "GUIDELINE-DERIVED SUMMARY SVG — RESTRUCTURED TO THE SOURCE FIGURE'S OWN BRANCHING ORDER",
        "disclaimer": ("Reconstruction of Chang 2024 Figure 1. The branching order is the guideline's own: "
                       "syndrome / involvement first, then host (HIV, SOT, non-HIV/non-SOT), then severity; "
                       "species appears only as a modifier (Panel 13, Panel 15). Regimens, durations and "
                       "grades are transcribed from Figure 1 and the cited panels — use the original "
                       "Figure/Panel text for definitive wording."),
        "svg": build_svg(highlight),
        "visual_type": "guideline-derived-summary",
        "visual_fidelity": "summary-not-source-faithful-redraw",
        "source_has_original_figure": True,
        "source_figure": "Figure 1 (PDF p2, journal e496)",
    }
