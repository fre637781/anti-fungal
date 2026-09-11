"""Curated corrections applied on top of the source document's own data.

The single-file HTML in source/ is left byte-for-byte as delivered, so every
deviation from it is declared here and can be reviewed on its own. extract.py
applies these while building data/, and records the applied list in meta.json.

Current overrides
-----------------
dose-typo-dayay
    The source file carries "mg/kg/dayay" throughout — the residue of a bad
    "d" -> "day" substitution when the doses were normalised. These are dose
    strings a clinician reads, so they are corrected to "/day" in both the
    treatment rows and the flowchart SVGs that bake the same text in.

cryptococcosis-algorithm
    The source file's Cryptococcus flowcharts open species-first. The guideline
    does not stratify that way: Chang 2024 Figure 1 branches involvement ->
    host -> severity, and species enters only as a modifier (Panel 13 treats
    C. gattii CNS disease the same as C. neoformans, with induction possibly
    extended to 4-6 weeks in non-HIV patients; Panel 15 says the same for the
    rare non-neoformans/non-gattii species).

stratified-charts
    The source file draws every syndrome as one flat stack of treatment nodes,
    which hides the axis the rows are already stratified along: their own
    clinical-setting column (severity, site or phase). 91 of 152 syndromes span
    more than one setting, so those are redrawn as branches — as columns, or as
    full-width bands once there are more than four settings (Aspergillus
    chronic pulmonary aspergillosis has nine). Nothing is re-worded: each card
    carries the row's own drug, dose, duration, grade and priority wording.
    Charts a dedicated builder already rebuilt are left alone.

mucormycosis-pathway
    The source file renders Cornely 2019 Figure 5 as a flat list of three
    treatment rows, which drops the parts of the figure that carry the
    decisions: the emergency framing, surgery as a co-equal first step, the
    brain-involvement / SOT / renal-compromise modifiers, the response
    assessment loop, and the separate progressive-disease and toxicity
    branches — along with every "recommended against" node. Each of the three
    drug-availability panels is rebuilt as the pathway it actually is.
    Recommendation strengths were read off the source figure's own fill
    colours (strong #ddedde, moderate #fff9d7, marginal #feebed,
    against #f7dfdf), not inferred from wording.
"""
import charts_cryptococcosis
import charts_mucormycosis
import charts_stratified

TYPOS = [("/dayay", "/day")]

APPLIED = []


def fix_typos(data, charts):
    """Repair text corruption carried in from the source document."""
    n = 0

    def fix(s):
        nonlocal n
        out = s
        for bad, good in TYPOS:
            if bad in out:
                n += out.count(bad)
                out = out.replace(bad, good)
        return out

    for org in data:
        for syn in org.get("syndromes", []):
            for row in syn.get("rows", []):
                for i, cell in enumerate(row):
                    if isinstance(cell, str):
                        row[i] = fix(cell)
    for bundle in charts.values():
        for c in bundle.get("charts", []):
            c["svg"] = fix(c["svg"])
    return n


def _bundle(charts, name):
    bundle = charts.get(name)
    if not bundle:
        raise SystemExit("override target missing from source: %s" % name)
    return bundle


def apply(data, charts):
    """Mutates the extracted DATA / SVG_CHARTS in place."""
    del APPLIED[:]

    fixed = fix_typos(data, charts)
    if fixed:
        APPLIED.append("dose-typo-dayay — %d corrupted dose strings repaired to '/day'" % fixed)

    # --- cryptococcosis: involvement -> host -> severity ---------------------
    for name, hl in (("Cryptococcus neoformans species complex", None),
                     ("Cryptococcus gattii species complex", "gattii")):
        _bundle(charts, name)["charts"].insert(0, charts_cryptococcosis.chart(hl))
    APPLIED.append("cryptococcosis-algorithm — Chang 2024 Figure 1 restructured as "
                   "involvement → host → severity")

    for org in data:
        if org["name"].startswith("Cryptococcus ") and "species complex" in org["name"]:
            org["source_note"] = (
                "治療分層依 Chang 2024 Figure 1：involvement → host → severity；species 僅為修飾因子"
                "（C. gattii CNS 依 Panel 13 與 C. neoformans 相同，non-HIV 可考慮 induction 延長至 4–6 週）。 "
            ) + org.get("source_note", "")

    # --- mucormycosis: restore Figure 5's actual pathway ---------------------
    bundle = _bundle(charts, "Mucorales spp. — mucormycosis")
    rebuilt = charts_mucormycosis.charts()
    # Replace the three flattened availability charts, keep anything else
    # (eg the paediatric supplement chart) after them.
    kept = [c for c in bundle["charts"] if "Figure 5" not in c["title"]]
    bundle["charts"] = rebuilt + kept
    APPLIED.append("mucormycosis-pathway — Cornely 2019 Figure 5A/5B/5C rebuilt as decision "
                   "pathways with response assessment and recommended-against nodes")

    # --- show the stratification the rows already carry, site-wide ------------
    n = 0
    for org in data:
        bundle = charts.get(org["name"])
        if not bundle:
            continue
        by_title = {c["title"]: c for c in bundle["charts"]}
        for syn in org["syndromes"]:
            original = by_title.get(syn["title"])
            if original is None or original.get("rebuilt"):
                continue          # a dedicated builder already owns this chart
            if not charts_stratified.applies_to(syn):
                continue          # a single clinical setting stays a plain list
            bundle["charts"][bundle["charts"].index(original)] = \
                charts_stratified.chart(org, syn, original)
            n += 1
    APPLIED.append("stratified-charts — %d charts redrawn as severity / site / phase pathways "
                   "from the rows' own clinical-setting column" % n)
