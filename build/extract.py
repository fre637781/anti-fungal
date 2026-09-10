#!/usr/bin/env python3
"""
Extract the data embedded in the single-file V23 guideline HTML into static
JSON that both the desktop and the mobile build consume.

    python3 build/extract.py [source/Fungal_Treatment_Guideline_Interactive_v23.html]

Output (all paths relative to the repository root):
    data/meta.json          groups, bibliography, reference DBs, static prose, stats
    data/index.json         one lightweight summary per organism (landing + search)
    data/org/<id>.json      the full organism record
    data/charts/<id>.json   the organism's flowchart SVGs (loaded on demand)
"""
import hashlib
import json
import os
import re
import sys

import overrides

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SRC = os.path.join(ROOT, "source", "Fungal_Treatment_Guideline_Interactive_v23.html")

# The constants are emitted one-per-line by the generator of the source file.
CONST_RE = re.compile(r"^\s*const\s+([A-Z_]+)\s*=\s*(.+?);?\s*$")
WANTED = {
    "DATA",
    "SVG_CHARTS",
    "GROUP_META",
    "REFERENCE_LINKS",
    "REFERENCE_DATABASE",
    "PAGE_REFERENCE_DB",
}


def read_constants(src):
    found = {}
    with open(src, encoding="utf-8") as fh:
        for line in fh:
            m = CONST_RE.match(line)
            if not m or m.group(1) not in WANTED:
                continue
            found[m.group(1)] = json.loads(m.group(2))
    missing = WANTED - set(found)
    if missing:
        raise SystemExit("source file is missing: %s" % ", ".join(sorted(missing)))
    return found


BIB_ITEM_RE = re.compile(
    r'<div class="bib-item" id="ref-([a-z_]+)"><b>(.*?)</b><br>(.*?)<div class="ref-db-buttons">(.*?)</div></div>',
    re.S,
)
BIB_LINK_RE = re.compile(r'<a class="ref-db-btn (\w+)" href="([^"]+)"[^>]*>(.*?)\s*↗</a>')
BIB_CITE_RE = re.compile(r'data-citation="([^"]*)"')


def read_bibliography(src):
    """Parse the static bibliography block so both builds can re-render it natively."""
    html = open(src, encoding="utf-8").read()
    items = []
    for key, short, title, buttons in BIB_ITEM_RE.findall(html):
        cite = BIB_CITE_RE.search(buttons)
        items.append(
            {
                "key": key,
                "short": short.strip(),
                "title": title.strip(),
                "links": [
                    {"kind": kind, "href": href, "label": label.strip()}
                    for kind, href, label in BIB_LINK_RE.findall(buttons)
                ],
                "citation": cite.group(1).replace("&amp;", "&") if cite else "",
            }
        )
    if not items:
        raise SystemExit("could not parse the bibliography block")
    return items


# Row layout inside syndrome.rows — kept here so the front-end never guesses.
COL = {
    "priority": 0,
    "phase": 1,
    "drug": 2,
    "dose": 3,
    "duration": 4,
    "setting": 5,
    "recommendation": 6,
    "source": 7,
    "sequence": 8,
    "note": 9,
    "evidence_origin": 10,
    "recommendation_origin": 11,
    "dose_origin": 12,
    "duration_origin": 13,
}

# Fields that feed the landing-page search box. The original file searched the
# whole stringified record; this keeps the same reach without shipping it.
def search_blob(org):
    parts = [org["name"], org.get("aliases", ""), org["group"], org.get("evidence_scope", "")]
    parts += org.get("tags", [])
    parts += [org.get("category", ""), org.get("overview", ""), org.get("notes", "")]
    for syn in org.get("syndromes", []):
        parts.append(syn.get("title", ""))
        for row in syn.get("rows", []):
            parts += [
                row[COL["priority"]],
                row[COL["phase"]],
                row[COL["drug"]],
                row[COL["setting"]],
                row[COL["sequence"]],
            ]
    seen, words = set(), []
    for chunk in parts:
        for word in re.split(r"\s+", str(chunk or "").lower()):
            word = word.strip(" .,;:()[]/|—–")
            if len(word) > 1 and word not in seen:
                seen.add(word)
                words.append(word)
    return " ".join(words)


def write_json(rel_path, payload, compact=True):
    path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(
            payload,
            fh,
            ensure_ascii=False,
            separators=(",", ":") if compact else (", ", ": "),
            indent=None if compact else 1,
        )
    return os.path.getsize(path)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    if not os.path.exists(src):
        raise SystemExit("source file not found: %s" % src)

    const = read_constants(src)
    data, charts = const["DATA"], const["SVG_CHARTS"]
    groups = const["GROUP_META"]

    # Curated corrections layered on top of the untouched source document.
    overrides.apply(data, charts)

    # Drop any stale per-organism file so a shrinking source cannot leave orphans.
    for sub in ("org", "charts"):
        d = os.path.join(ROOT, "data", sub)
        if os.path.isdir(d):
            for name in os.listdir(d):
                if name.endswith(".json"):
                    os.remove(os.path.join(d, name))

    index, total_rows, total_charts, org_bytes, chart_bytes = [], 0, 0, 0, 0
    for org in data:
        bundle = charts.get(org["name"], {}) or {}
        chart_list = bundle.get("charts", []) or []
        rows = sum(len(s.get("rows", [])) for s in org.get("syndromes", []))
        total_rows += rows
        total_charts += len(chart_list)

        org_bytes += write_json("data/org/%s.json" % org["id"], org)
        if chart_list:
            chart_bytes += write_json("data/charts/%s.json" % org["id"], {"charts": chart_list})

        index.append(
            {
                "id": org["id"],
                "name": org["name"],
                "aliases": org.get("aliases", ""),
                "group": org["group"],
                "groupColor": org["groupColor"],
                "tags": org.get("tags", []),
                "evidence_scope": org.get("evidence_scope", ""),
                "evidence": org.get("evidence_availability", "other"),
                "syndromes": len(org.get("syndromes", [])),
                "rows": rows,
                "charts": len(chart_list),
                "q": search_blob(org),
            }
        )

    meta = {
        "version": "V23",
        "title": "Fungal Treatment Guideline",
        "subtitle": "Document-based clinical reference · V23 — per-page references",
        "source_file": os.path.basename(src),
        "source_sha256": hashlib.sha256(open(src, "rb").read()).hexdigest()[:16],
        "columns": COL,
        "groups": groups,
        "stats": {
            "organisms": len(data),
            "groups": len(groups),
            "rows": total_rows,
            "charts": total_charts,
        },
        "overrides": overrides.APPLIED,
        "bibliography": read_bibliography(src),
        "reference_links": const["REFERENCE_LINKS"],
        "reference_database": const["REFERENCE_DATABASE"],
        "page_reference_db": const["PAGE_REFERENCE_DB"],
    }
    meta_bytes = write_json("data/meta.json", meta)
    index_bytes = write_json("data/index.json", {"organisms": index})

    for note in overrides.APPLIED:
        print("override       %s" % note)
    print("organisms      %d" % len(data))
    print("syndrome rows  %d" % total_rows)
    print("flowcharts     %d" % total_charts)
    print("data/meta.json   %6.1f KB" % (meta_bytes / 1024))
    print("data/index.json  %6.1f KB" % (index_bytes / 1024))
    print("data/org/*       %6.1f KB total" % (org_bytes / 1024))
    print("data/charts/*    %6.1f KB total" % (chart_bytes / 1024))


if __name__ == "__main__":
    main()
