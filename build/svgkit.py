"""Shared SVG primitives for the guideline flowcharts built in build/charts_*.py.

Text is measured rather than assumed so boxes can shrink-to-fit, which keeps
long transcribed guideline wording inside its node instead of spilling out.
"""
# ---------------------------------------------------------------- SVG helpers
CJK = lambda ch: ord(ch) > 0x2E7F


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def text_width(s, size):
    """Rough advance width; CJK glyphs are full-width, Latin about 0.53em."""
    return sum((1.0 if CJK(c) else 0.53) * size for c in s)


def wrap(s, max_px, size):
    words, lines, cur = s.split(" "), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if cur and text_width(trial, size) > max_px:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def rect(x, y, w, h, fill, stroke, rx=11, sw=2, extra=""):
    return ('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" '
            'stroke="%s" stroke-width="%g"%s/>' % (x, y, w, h, rx, fill, stroke, sw,
                                                   (" " + extra) if extra else ""))


# The font family is set once on the <svg> root (see SVG_OPEN) instead of on
# every text node — these charts carry thousands of them.
SVG_OPEN = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" '
            'font-family="Arial,Helvetica,sans-serif">')


def label(x, y, s, size=14, weight="400", anchor="start", fill="#18211d", extra=""):
    attrs = '<text x="%g" y="%g" font-size="%g"' % (x, y, size)
    if weight != "400":
        attrs += ' font-weight="%s"' % weight
    if anchor != "start":
        attrs += ' text-anchor="%s"' % anchor
    attrs += ' fill="%s"' % fill
    if extra:
        attrs += " " + extra
    return attrs + ">%s</text>" % esc(s)


def block(x, y, w, s, size=13, weight="400", anchor="middle", fill="#18211d", lh=None, pad=10):
    """Centred, wrapped run of text. Returns (svg, height consumed)."""
    lh = lh or size + 4
    lines = wrap(s, w - 2 * pad, size)
    tx = x + w / 2 if anchor == "middle" else x + pad
    out = "".join(label(tx, y + i * lh, ln, size, weight, anchor, fill) for i, ln in enumerate(lines))
    return out, len(lines) * lh


def line(x1, y1, x2, y2, stroke="#6d7a73", sw=2):
    return ('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="%g" '
            'stroke-linecap="round"/>' % (x1, y1, x2, y2, stroke, sw))


def elbow(x1, y1, x2, y2, bus, stroke="#6d7a73", sw=2):
    """Vertical drop to a horizontal bus, across, then down into the target."""
    return ('<path d="M %g %g V %g H %g V %g" fill="none" stroke="%s" stroke-width="%g" '
            'stroke-linecap="round" stroke-linejoin="round"/>' % (x1, y1, bus, x2, y2, stroke, sw))


# tier colours — identical to the treatment-table row shading used site-wide
TIER = {
    "preferred":   ("#d8f0df", "#23824b", "#155b35"),
    "alternative": ("#fff0bd", "#c58a00", "#765300"),
    "salvage":     ("#d9eaff", "#3478bd", "#245787"),
    "avoid":       ("#f9d6d6", "#c53b3b", "#8d2525"),
}
BRANCH = ("#e9eff3", "#4a6b86")   # involvement — structural, never a tier colour
STRAT = ("#f2f5f3", "#697770")    # host / severity
PAPER = ("#ffffff", "#c9d3cd")


def treatment_box(x, y, w, h, tier, title, body, note=""):
    fill, stroke, ink = TIER[tier]
    out = [rect(x, y, w, h, fill, stroke, sw=2.5)]
    ty = y + 26
    t, dy = block(x, ty, w, title, 15, "800", "middle", ink)
    out.append(t)
    ty += dy + 6
    b, dy = block(x, ty, w, body, 13, "400", "middle", "#1c2a24")
    out.append(b)
    if note:
        ty += dy + 6
        n, _ = block(x, ty, w, note, 11.5, "400", "middle", "#4d5a53")
        out.append(n)
    return "".join(out)


def branch_box(x, y, w, h, en, zh, palette=BRANCH, size=14):
    """Text is shrunk until it fits the box, then centred vertically, so a long
    label such as 'Disseminated (non-CNS, non-pulmonary)' cannot spill out."""
    fill, stroke = palette
    zh_size = 11.5
    while True:
        en_lines = wrap(en, w - 14, size)
        en_h = len(en_lines) * (size + 4)
        zh_h = (zh_size + 4) + 4 if zh else 0
        if en_h + zh_h <= h - 18 or size <= 10.5:
            break
        size -= 0.5
        zh_size = min(zh_size, size - 1.5)

    out = [rect(x, y, w, h, fill, stroke, sw=2)]
    ty = y + (h - (en_h + zh_h)) / 2 + size
    for ln in en_lines:
        out.append(label(x + w / 2, ty, ln, size, "800", "middle", "#1d2a33"))
        ty += size + 4
    if zh:
        out.append(label(x + w / 2, ty + 4, zh, zh_size, "700", "middle", "#5a6b76"))
    return "".join(out)


