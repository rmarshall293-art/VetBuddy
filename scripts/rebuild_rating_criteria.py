#!/usr/bin/env python3
"""Rebuild damaged criteria in data/reference/rating_schedule.json from saved eCFR snapshots
of 38 CFR Part 4 (data/research/federal/ecfr_38cfr4_2026-08-27).

38 CFR 4.69 rates the dominant ("major") and non-dominant ("minor") upper extremity
separately. The 2020 PDF transcription had one percent column, so it kept the major
figure at the end of the text and the minor figure as the percent, lost some row
labels, and let page headers bleed in. This script reads the official tables and writes,
for each code with two rating columns: percent = major (dominant), percent_minor =
minor (non-dominant), and the row text as published. Rows with one rating keep
percent only. Table footnotes (special monthly compensation) are appended to the
row they mark.

The same parse also left PDF page headers ("[[PAGE 441]] ... —Continued Rating") and
bare numbers inside single-rating codes; those codes are rebuilt from the official table
too. A code whose official entry has no rated rows of its own keeps its text with only the
page header removed, except where the parse copied another code's rows onto it
(COPIED_ROWS). Superseded codes (digestive, revised 2024-05-19) are not rebuilt from the
current text, because their criteria changed. Every row stays UNVERIFIED until a named
reviewer checks it.

  python3 scripts/rebuild_rating_criteria.py           # rewrite the JSON
  python3 scripts/rebuild_rating_criteria.py --check   # fail if the JSON disagrees with the snapshots
"""
import argparse, json, re, sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SNAP_DIR = ROOT / "data/research/federal/ecfr_38cfr4_2026-08-27"
SNAPSHOT = "eCFR 38 CFR Part 4, amended through 2026-08-27"
DATASET = ROOT / "data/reference/rating_schedule.json"
NOTE = (f"Criteria re-transcribed from {SNAPSHOT}. Where the table has two columns, percent is the "
        "major (dominant) side and percent_minor the minor (non-dominant) side (38 CFR 4.69).")
NOTE_HEADER = f"2020 transcription with PDF page headers removed; checked against {SNAPSHOT}, which lists no rated rows under this code."
NOTE_COPIED = f"The 2020 transcription repeated another code's rows here; {SNAPSHOT} lists none under this code."
# The 2020 parse attached the next table's rows to a code that has none of its own.
COPIED_ROWS = {"8710": "8510 paralysis rows", "6091": "a rating instruction given a percent, and a 4.85 hearing-table row"}

# Signs of PDF-parse damage in a criteria row (also enforced by backend/tests/test_rating_schedule.py).
DAMAGE = re.compile(r"—\s*Continued|Major Minor|\[\[PAGE \d+\]\]|7–1–20 Edition|(?<!Stage)\s(?:0|[1-9]0|100)\s*$|^\s*\d{1,3}\s*$")
# One PDF page header. It must carry at least one sign of a page break (a page marker,
# the running head, or a "—Continued" table title) before the column heading "Rating",
# so "General Rating Formula" in regulation text is never touched.
_SEC = r"(?:§\s?4\.\d+[a-z]?\s*)?"
_RUNNING = r"(?:Department of Veterans Affairs|38 CFR Ch\. I \(7–1–20 Edition\))\s*"
_CONT = r"[A-Z][A-Z ,:]{3,}—\s*Continued\s*"
PAGE_HEADER = re.compile(
    r"\s*(?:\[\[PAGE \d+\]\]\s*)?(?:" + _RUNNING + _SEC + f"(?:{_CONT})?" + "|" + _SEC + _CONT +
    r"|(?<=\]\])\s*" + _SEC + r")Rating(?: Major Minor)?\s+(?=[A-Z(])")


def _text(el) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def _cell(td):
    """A rating cell -> (int, or the raw string when it is not a plain number, or None; [footnote marks])."""
    marks = [s.text.strip() for s in td.iter("sup") if (s.text or "").strip().isdigit()]
    rest = "".join(td.itertext())
    for m in marks:
        rest = rest.replace(m, "", 1)
    rest = rest.strip()
    if not rest:
        return None, marks
    if not re.fullmatch(r"\d{1,3}", rest):
        return rest, marks          # e.g. "*50" or "Total": refused below if it is in a rebuilt code
    return int(rest), marks


def _indent(td) -> int:
    m = re.search(r"indent-hanging-(\d+)", td.get("class", ""))
    return int(m.group(1)) if m else 0


def parse_tables(paths):
    """Every diagnostic code in the snapshot tables -> its heading and rows (label, indent, ratings, notes)."""
    codes = {}
    for path in paths:
        for tbl in ET.parse(path).getroot().iter("TABLE"):
            foot = {}
            tf = tbl.find("TFOOT")
            if tf is not None:
                for td in tf.iter("TD"):
                    m = re.match(r"^(\d)\s+(.*)$", _text(td))
                    if m:
                        foot[m.group(1)] = m.group(2)
            body = tbl.find("TBODY")
            if body is None:
                continue
            cur = None
            for tr in body.findall("TR"):
                tds = tr.findall("TD")
                if not tds:
                    continue
                label = _text(tds[0])
                m = re.match(r"^(\d{4})\b\s*(.*)$", label)
                if m:
                    cur = codes[m.group(1)] = {"heading": m.group(2), "rows": []}
                    label = ""
                if cur is None:
                    continue
                cells = [_cell(td) for td in tds[1:]]
                marks = sorted({mk for _, mks in cells for mk in mks})
                cur["rows"].append({"label": label, "indent": _indent(tds[0]),
                                    "values": [v for v, _ in cells if isinstance(v, int)],
                                    "odd": [v for v, _ in cells if isinstance(v, str)],
                                    "notes": [foot[mk] for mk in marks if mk in foot]})
    return codes


def criteria_for(code):
    out, headings = [], []          # headings: [(indent, text)] that apply to the rows under them
    for r in code["rows"]:
        if r["odd"]:
            raise ValueError(f"rating cell this script does not understand: {r['odd']} in {code['heading'][:60]!r}")
        while headings and r["indent"] <= headings[-1][0]:
            headings.pop()
        if not r["values"]:
            if r["label"]:
                headings.append((r["indent"], r["label"]))
            continue
        if len(r["values"]) > 2:
            raise ValueError(f"more than two ratings in a row: {r}")
        text = " ".join([h for _, h in headings] + ([r["label"]] if r["label"] else [])) or code["heading"]
        for n in r["notes"]:
            text += f" (Table note: {n})"
        row = {"percent": r["values"][0], "text": text}
        if len(r["values"]) == 2:
            row["percent_minor"] = r["values"][1]
        out.append(row)
    return out


def damaged(code) -> bool:
    return any(DAMAGE.search(k["text"]) for k in code["criteria"])


# A bare page marker with only the running section number after it.
PAGE_MARK = re.compile(r"\s*\[\[PAGE \d+\]\]\s*(?:§\s?4\.\d+[a-z]?\s+)?")


def strip_headers(text: str) -> str:
    return re.sub(r"\s+", " ", PAGE_MARK.sub(" ", PAGE_HEADER.sub(" ", text))).strip()


def rebuilt(dataset, tables):
    """Rebuild every two-column code and every damaged code; everything else is untouched.
    Idempotent: a second run changes nothing (that is what --check tests)."""
    changed = []

    def put(c, crit, note):
        if crit != c["criteria"] or c.get("status_note") != note:
            changed.append(c["code"])
        c["criteria"], c["has_criteria"], c["status_note"] = crit, bool(crit), note

    for c in dataset["codes"]:
        t = tables.get(c["code"])
        rated = bool(t) and any(r["values"] for r in t["rows"])
        two_col = bool(t) and any(len(r["values"]) == 2 for r in t["rows"])
        if c.get("status") == "SUPERSEDED":
            if damaged(c):
                put(c, [{**k, "text": strip_headers(k["text"])} for k in c["criteria"]], c.get("status_note"))
        elif c["code"] in COPIED_ROWS or c.get("status_note") == NOTE_COPIED:
            if t is None or rated:
                raise ValueError(f"{c['code']}: expected an official entry with no rated rows")
            put(c, [], NOTE_COPIED)
        elif two_col or (rated and (damaged(c) or c.get("status_note") == NOTE)):
            put(c, criteria_for(t), NOTE)
        elif damaged(c) or c.get("status_note") == NOTE_HEADER:
            note = NOTE_HEADER if t is not None else c.get("status_note")
            put(c, [{**k, "text": strip_headers(k["text"])} for k in c["criteria"]], note)
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    tables = parse_tables(sorted(SNAP_DIR.glob("38cfr_*.xml")))
    data = json.loads(DATASET.read_text())
    changed = rebuilt(data, tables)
    if a.check:
        if changed:
            sys.exit(f"rating_schedule.json disagrees with the eCFR snapshot for {len(changed)} codes: {changed[:10]}")
        print("rating criteria match the eCFR snapshot")
        return
    DATASET.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(f"rebuilt {len(changed)} codes from {SNAPSHOT}")


if __name__ == "__main__":
    main()
